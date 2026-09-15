// STEP D-SCREEN-1(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §1)。rescreen.ts の配線を見張る(scan-compare.test.ts と同じ形)。
//
// - ソース照合 … 書く前の確かめをエンジンを起こす前に行い、measureEngineReference を深いノード数で measure として渡し、
//   Threads 1 で、規則は DRAFT_SCREEN_RULE_1、書き出しは lib の全文、であることを見る(照合は片側にしか壊れない)
// - 子プロセス … **エンジンを起こさずに止まる経路だけ**を走らせる(引数の誤り・段 2 を入力・--out が入力と同じ)。深く測る経路は
//   エンジンが要るので試験しない(lib/rescreen.test.ts が偽の measure で見る)
//
// 【静かにスキップしない】npx・tsx・git が無ければ execFileSync が例外を投げて赤になる。
// 【一時ディレクトリ以外に書かない】走らせる前と後で git status(node_modules だけを除く)が同じ。

import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const RESCREEN_TS = join(PLAYTEST_DIR, "rescreen.ts");

const gitStatus = (): string =>
  execFileSync(
    "git",
    ["status", "--porcelain", "-z", "--untracked-files=all", "--ignored", "--", ".", ":(exclude,glob)**/node_modules", ":(exclude,glob)**/node_modules/**"],
    { cwd: REPO_ROOT },
  ).toString();

function runRescreen(args: string[]): { status: number; stderr: string } {
  try {
    execFileSync("npx", ["tsx", RESCREEN_TS, ...args], { cwd: REPO_ROOT, encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] });
    return { status: 0, stderr: "" };
  } catch (error) {
    const failure = error as { status: number | null; stderr: string };
    return { status: failure.status ?? -1, stderr: String(failure.stderr) };
  }
}

const META = { kind: "meta", kifuId: "rescreen-cli", startedAt: "t", gitHead: null, enginePath: "/e", searchMode: "nodes", nodes: 400000, threads: 1, referenceNodes: 400000 };

describe("rescreen.ts(計画 §1)", () => {
  it("ソース照合: エンジンを起こす前に段 1 を確かめ、measureEngineReference を深いノード数で measure にし、Threads 1 で、lib の全文を書く", () => {
    const source = readFileSync(RESCREEN_TS, "utf8");
    expect(source).toContain("  const { deepPlies } = planRescreen(source, DRAFT_SCREEN_RULE_1, options);\n");
    // STEP D-SCREEN-2: --all-plies は確かめと測りの両方に同じ options で渡す
    expect(source).toContain('  const options = { allPlies: args.includes("--all-plies") };\n');
    expect(source).toContain("    }, options);\n");
    expect(source).toContain(
      "    const text = await rescreenRecords(source, DRAFT_SCREEN_RULE_1, (sfen) => measureEngineReference(sfen, engine, deepNodes), {\n",
    );
    expect(source).toContain("      threads: DEEP_THREADS,\n");
    expect(source).toContain("    rawEngine.setThreads(DEEP_THREADS);\n");
    expect(source).toContain("const DEEP_THREADS = 1;\n");
    expect(source).toContain('    writeFileSync(outPath, text, "utf-8");\n');
    expect(source).toContain("  if (inputPath === outPath) throw new Error(");
    expect(source.indexOf("planRescreen(source, DRAFT_SCREEN_RULE_1, options)")).toBeLessThan(source.indexOf("rawEngine.start();"));
  });

  it(
    "子プロセス: 引数の誤り・段 2 の記録を入力・--out が入力と同じ、はどれもエンジンを起こさずに exit 1 で止まり、書かない",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d-screen-1-cli-"));
      try {
        const before = gitStatus();

        const noArgs = runRescreen([]);
        expect(noArgs.status).toBe(1);
        expect(noArgs.stderr).toContain("使い方: npx tsx scripts/playtest/rescreen.ts <段1.jsonl> --out <段2.jsonl> --deep-nodes <N> [--all-plies]");

        const noNodes = runRescreen([join(dir, "a.jsonl"), "--out", join(dir, "b.jsonl")]);
        expect(noNodes.status).toBe(1);
        expect(noNodes.stderr).toContain("使い方:");

        const stage2 = join(dir, "stage2.jsonl");
        writeFileSync(stage2, `${JSON.stringify({ ...META, screen: { deepPlies: [] } })}\n`, "utf-8");
        const stage2Out = join(dir, "stage2-out.jsonl");
        const rejected = runRescreen([stage2, "--out", stage2Out, "--deep-nodes", "4000000"]);
        expect(rejected.status).toBe(1);
        expect(rejected.stderr).toContain("RescreenInputError: meta に screen がある");
        expect(rejected.stderr).not.toContain("読み直す行");
        expect(existsSync(stage2Out)).toBe(false);

        const stage1 = join(dir, "stage1.jsonl");
        const stage1Text = `${JSON.stringify(META)}\n`;
        writeFileSync(stage1, stage1Text, "utf-8");
        const same = runRescreen([stage1, "--out", stage1, "--deep-nodes", "4000000"]);
        expect(same.status).toBe(1);
        expect(same.stderr).toContain("Error: --out が入力と同じパス(段 1 のファイルは変えない)");
        expect(readFileSync(stage1, "utf-8")).toBe(stage1Text);

        expect(gitStatus()).toBe(before);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    120_000,
  );
});
