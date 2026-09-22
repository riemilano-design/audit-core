// STEP TIME 作業 1(docs/STEP_TIME_PLAN_2026-09-22.md §6.1 の 1)。kifu-times.ts(子プロセス)の試験。
// **期待値は試験を回す前に手で書いた**(規則 11.1)。
// 【一時ディレクトリ以外に書かない】走らせる前と後で git status(node_modules だけを除く)が同じであることを確かめる。

import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, statSync, utimesSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const TOOL_TS = join(PLAYTEST_DIR, "kifu-times.ts");

const KIF_WITH_TIME = [
  "先手：Ｘ",
  "後手：Ｙ",
  "手合割：平手",
  "手数----指手---------消費時間--",
  "   1 ７六歩(77)   ( 0:01/00:00:01)",
  "   2 ３四歩(33)   ( 0:00/00:00:00)",
  "   3 ２六歩(27)   ( 0:02/00:00:03)",
  "   4 投了",
  "まで3手で先手の勝ち",
  "",
].join("\n");

const KIF_WITHOUT_TIME = [
  "先手：Ｘ",
  "後手：Ｙ",
  "手合割：平手",
  "手数----指手---------消費時間--",
  "   1 ７六歩(77)",
  "   2 ３四歩(33)",
  "   3 ２六歩(27)",
  "   4 投了",
  "まで3手で先手の勝ち",
  "",
].join("\n");

const MOVES = ["7g7f", "3c3d", "2g2f"];
const EXPECTED_SECONDS = [
  { spentSec: 1, totalSec: 1 },
  { spentSec: 0, totalSec: 0 },
  { spentSec: 2, totalSec: 3 },
];

const gitStatus = (): string =>
  execFileSync(
    "git",
    ["status", "--porcelain", "-z", "--untracked-files=all", "--ignored", "--", ".", ":(exclude,glob)**/node_modules", ":(exclude,glob)**/node_modules/**"],
    { cwd: REPO_ROOT },
  ).toString();

function withTempDir<T>(f: (dir: string) => T): T {
  const dir = mkdtempSync(join(tmpdir(), "step-time-kifu-times-"));
  try {
    return f(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function run(args: string[]): { status: number | null; stdout: string; stderr: string } {
  try {
    const stdout = execFileSync("npx", ["tsx", TOOL_TS, ...args], { cwd: REPO_ROOT, encoding: "utf-8", stdio: "pipe" });
    return { status: 0, stdout, stderr: "" };
  } catch (error) {
    const failure = error as { status: number | null; stdout: string; stderr: string };
    return { status: failure.status, stdout: String(failure.stdout), stderr: String(failure.stderr) };
  }
}

describe("kifu-times.ts(既存の固定棋譜に moveSeconds を後から足す)", () => {
  it(
    "moves が一致すれば moveSeconds を足す。mtime は変えない",
    () => {
      const before = gitStatus();
      withTempDir((dir) => {
        const fixedPath = join(dir, "g.fixed.json");
        const kifPath = join(dir, "g.kif");
        writeFileSync(fixedPath, `${JSON.stringify({ id: "k1", source: "test", ending: { kind: "resign", ply: 4 }, moves: MOVES }, null, 2)}\n`, "utf-8");
        writeFileSync(kifPath, KIF_WITH_TIME, "utf-8");
        const oldTime = new Date("2020-01-01T00:00:00Z");
        utimesSync(fixedPath, oldTime, oldTime);

        const result = run([fixedPath, kifPath]);
        expect(result.status, result.stderr).toBe(0);
        expect(result.stdout).toContain("moveSeconds を足した(3 / 3 手に秒あり)");

        const written = JSON.parse(readFileSync(fixedPath, "utf-8")) as Record<string, unknown>;
        expect(written["moveSeconds"]).toStrictEqual(EXPECTED_SECONDS);
        expect(written["moves"]).toStrictEqual(MOVES); // 他の欄は変えない
        expect(written["id"]).toBe("k1");

        const stat = statSync(fixedPath);
        expect(stat.mtime.getTime()).toBe(oldTime.getTime()); // mtime を元に戻す
      });
      expect(gitStatus()).toBe(before);
    },
    60_000,
  );

  it(
    "moves が食い違えば書かない(exit 1、ファイルは変わらない)",
    () => {
      withTempDir((dir) => {
        const fixedPath = join(dir, "g.fixed.json");
        const kifPath = join(dir, "g.kif");
        const original = `${JSON.stringify({ id: "k1", source: "test", ending: { kind: "resign", ply: 4 }, moves: ["7g7f", "3c3d", "2g2f", "8h2b+"] }, null, 2)}\n`;
        writeFileSync(fixedPath, original, "utf-8");
        writeFileSync(kifPath, KIF_WITH_TIME, "utf-8"); // 3 手だけの KIF(固定棋譜は 4 手)

        const result = run([fixedPath, kifPath]);
        expect(result.status).toBe(1);
        expect(result.stderr).toContain("moves が食い違うので書かない");
        expect(readFileSync(fixedPath, "utf-8")).toBe(original);
      });
    },
    60_000,
  );

  it(
    "秒を読めた手が 1 つも無ければ moveSeconds を足さない(exit 0、ファイルは変わらない)",
    () => {
      withTempDir((dir) => {
        const fixedPath = join(dir, "g.fixed.json");
        const kifPath = join(dir, "g.kif");
        const original = `${JSON.stringify({ id: "k1", source: "test", ending: { kind: "resign", ply: 4 }, moves: MOVES }, null, 2)}\n`;
        writeFileSync(fixedPath, original, "utf-8");
        writeFileSync(kifPath, KIF_WITHOUT_TIME, "utf-8");

        const result = run([fixedPath, kifPath]);
        expect(result.status, result.stderr).toBe(0);
        expect(result.stdout).toContain("moveSeconds は足さない");
        expect(readFileSync(fixedPath, "utf-8")).toBe(original);
      });
    },
    60_000,
  );

  it(
    "originalMoves を持つ固定棋譜(後手を回した局)は、originalMoves と突き合わせる",
    () => {
      withTempDir((dir) => {
        const fixedPath = join(dir, "g.fixed.json");
        const kifPath = join(dir, "g.kif");
        // mirrored な固定棋譜: moves は回して畳んだ側(比べない)、originalMoves が本人の元の手順(比べる側)
        writeFileSync(
          fixedPath,
          `${JSON.stringify(
            { id: "k1", source: "test", mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: "dummy", ending: { kind: "resign", ply: 4 }, moves: ["dummy"], originalMoves: MOVES },
            null,
            2,
          )}\n`,
          "utf-8",
        );
        writeFileSync(kifPath, KIF_WITH_TIME, "utf-8");

        const result = run([fixedPath, kifPath]);
        expect(result.status, result.stderr).toBe(0);
        const written = JSON.parse(readFileSync(fixedPath, "utf-8")) as Record<string, unknown>;
        expect(written["moveSeconds"]).toStrictEqual(EXPECTED_SECONDS);
        expect(written["moves"]).toStrictEqual(["dummy"]); // moves(畳んだ側)は変えない
      });
    },
    60_000,
  );
});
