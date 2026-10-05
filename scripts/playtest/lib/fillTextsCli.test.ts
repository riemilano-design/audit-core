// 言い換えの束の CLI(`scripts/playtest/fillTexts.ts`)の配線の試験 ― 人間の GO(2026-10-05・最後の 1 回)の修正条件 1〜3。
//
// 【陽性対照 = 2026-10-05 に落ちた手】repo の根から**相対の道**で打った(cwd と python の cwd が違う)。
// 顧客の道(out/<顧客>/…)は試験に書けないので、合成の材料を一時フォルダに置き、**同じ旗の並び・同じ相対の道の形**で打つ。
// 直す前はこの試験が落ちた手と同じ理由(「言い換えの文(fill_texts)が無い」)で赤、直した後は緑(記録 LANE §87)。
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

const REPO_ROOT = path.resolve(new URL("../../..", import.meta.url).pathname);
const REPORT_PDF_DIR = path.join(REPO_ROOT, "scripts", "playtest", "report-pdf");
const TSX_CLI = path.join(REPO_ROOT, "node_modules", "tsx", "dist", "cli.mjs");

/** 落ちた手の字そのもの(2026-10-05 23:03。顧客フォルダ名は c5 のまま ― 顧客の実名ではない)。試験はこの旗の並びを変えずに道だけ合成に置き換える。 */
export const FAILED_COMMAND_2026_10_05 = "SEAT_COST_CAP_USD=1 npx tsx scripts/playtest/fillTexts.ts --selection scripts/playtest/out/c5/exit/answer_selection.json --seats-dir scripts/playtest/out/c5/llm-seats --out-dir scripts/playtest/out/c5/exit";

interface Run { status: number | null; stdout: string; stderr: string; outDir: string; args: string[] }

/** 合成の材料は python の試験の fixture(exit_fill_test.selection2 / integration)から作る ― 写しを持たない。 */
function fixtureFromPython(): { selection: Record<string, unknown>; integration: Record<string, unknown> } {
  const out = execFileSync("python3", ["-X", "utf8", "-c", "import json, exit_fill_test as T; print(json.dumps({'selection': T.selection2(), 'integration': T.integration()}, ensure_ascii=False))"], { cwd: REPORT_PDF_DIR, encoding: "utf-8" });
  return JSON.parse(out) as { selection: Record<string, unknown>; integration: Record<string, unknown> };
}

/**
 * `cwdMode: "repo"` = 落ちた手と同じ(cwd = repo の根、道は repo 相対)。
 * `cwdMode: "material"` = cwd を**材料のフォルダ**にし、道は `exit/answer_selection.json` のような下向きの相対(`..` を含まない)。
 * repo の外の一時フォルダは `..` が根で飽和するので、「repo の根から解く」誤りと「cwd から解く」正解が同じ道に落ちて見分けられない ―
 * 変異 M12(2026-10-05)が緑で通ったので、下向きの相対で見分ける。
 */
function runDryRunWithRelativePaths(cwdMode: "repo" | "material" = "repo"): Run {
  const base = mkdtempSync(path.join(tmpdir(), "fill-texts-cli-"));
  const fx = fixtureFromPython();
  const exitDir = path.join(base, "exit");
  const seatsDir = path.join(base, "llm-seats");
  mkdirSync(path.join(seatsDir, String(fx.selection.runId)), { recursive: true });
  mkdirSync(exitDir, { recursive: true });
  writeFileSync(path.join(exitDir, "answer_selection.json"), JSON.stringify(fx.selection), "utf-8");
  writeFileSync(path.join(seatsDir, String(fx.selection.runId), "integration.json"), JSON.stringify(fx.integration), "utf-8");
  // 落ちた手と同じ: 道は**打った場所(cwd)からの相対**。
  const cwd = cwdMode === "repo" ? REPO_ROOT : base;
  const rel = (p: string): string => path.relative(cwd, p);
  const script = path.join(REPO_ROOT, "scripts", "playtest", "fillTexts.ts");
  const args = [cwdMode === "repo" ? rel(script) : script, "--selection", rel(path.join(exitDir, "answer_selection.json")), "--seats-dir", rel(seatsDir), "--out-dir", rel(exitDir)];
  for (const a of args.slice(1)) expect(path.isAbsolute(a)).toBe(false);
  if (cwdMode === "material") for (const a of args.slice(1).filter((_, i) => i % 2 === 1)) expect(a.startsWith("..")).toBe(false);
  const r = spawnSync(process.execPath, [TSX_CLI, ...args, "--env", rel(path.join(base, "no.env")), "--dry-run"], { cwd, encoding: "utf-8", env: { ...process.env, SEAT_COST_CAP_USD: "1" }, timeout: 120_000 });
  return { status: r.status, stdout: r.stdout ?? "", stderr: r.stderr ?? "", outDir: exitDir, args };
}

describe("CLI の配線 ― 落ちた手(repo の根・相対の道)で下見が通り、下見が照合を本番の経路で 1 回呼ぶ", () => {
  let run: Run;
  let runElsewhere: Run;
  beforeAll(() => { run = runDryRunWithRelativePaths("repo"); runElsewhere = runDryRunWithRelativePaths("material"); }, 180_000);
  afterAll(() => { for (const r of [run, runElsewhere]) if (r !== undefined) rmSync(path.dirname(r.outDir), { recursive: true, force: true }); });

  it("c1 旗の並びは落ちた手の字そのもの(道だけ合成)", () => {
    const failed = FAILED_COMMAND_2026_10_05.split(" ");
    expect(failed.slice(0, 3)).toEqual(["SEAT_COST_CAP_USD=1", "npx", "tsx"]);
    const failedFlags = failed.slice(3).filter((_, i) => i === 0 || i % 2 === 1); // script と旗だけ
    const ownFlags = run.args.filter((_, i) => i === 0 || i % 2 === 1);
    expect(ownFlags).toEqual(failedFlags);
    expect(failed.slice(3).filter((_, i) => i > 0 && i % 2 === 0).every((p) => !path.isAbsolute(p))).toBe(true);
  });
  it("c2 修正条件 1: 相対の道で打って通る(rc 0・下見の JSON が在る)", () => {
    expect(run.stderr, run.stderr).not.toContain("JSON を返さなかった");
    expect(run.status, `${run.stdout}\n${run.stderr}`).toBe(0);
    expect(existsSync(path.join(run.outDir, "fill_texts.dryrun.json"))).toBe(true);
    expect(run.stdout).toContain("有効な上限 SEAT_COST_CAP_USD = 1");
    expect(run.stdout).toContain("下見だけ(送っていない)");
  });
  it("c3 修正条件 2: 下見が --verify-texts を本番の経路で 1 回呼ぶ(空の文 4 本 → python の JSON が返る)。API は呼ばない・attempts/ は作らない", () => {
    const dry = JSON.parse(readFileSync(path.join(run.outDir, "fill_texts.dryrun.json"), "utf-8")) as Record<string, unknown>;
    const wiring = dry.verifyWiring as Record<string, unknown>;
    expect(wiring.calls).toBe(1);
    expect(wiring.checked).toEqual(["lead", "p1.1", "p1.2", "p1.3"]);
    expect(wiring.problemCounts).toEqual({ lead: 1, "p1.1": 1, "p1.2": 1, "p1.3": 1 });
    expect(wiring.f5).toEqual({ lead: false, "p1.1": false, "p1.2": false, "p1.3": false });
    expect(wiring.maxChars).toBe(200);
    const input = JSON.parse(readFileSync(String(wiring.inputPath), "utf-8")) as Record<string, string>;
    expect(input).toEqual({ lead: "", "p1.1": "", "p1.2": "", "p1.3": "" });
    expect(run.stdout).toContain("照合の配線: exit_fill.py --verify-texts を 1 回呼んだ");
    expect(existsSync(path.join(run.outDir, "attempts"))).toBe(false);
    expect(existsSync(path.join(run.outDir, "fill_texts.report.json"))).toBe(false);
  });
  it("c4 修正条件 1: 解き方は実行位置に依存しない ― repo の外の材料のフォルダを cwd にして、下向きの相対の道で打っても通る(repo の根から解くと無い道になる)", () => {
    expect(runElsewhere.args.slice(1).filter((_, i) => i % 2 === 1)).toEqual(["exit/answer_selection.json", "llm-seats", "exit"]);
    expect(path.isAbsolute(runElsewhere.args[0]!)).toBe(true);
    expect(runElsewhere.status, `${runElsewhere.stdout}\n${runElsewhere.stderr}`).toBe(0);
    const dry = JSON.parse(readFileSync(path.join(runElsewhere.outDir, "fill_texts.dryrun.json"), "utf-8")) as Record<string, unknown>;
    expect((dry.verifyWiring as Record<string, unknown>).calls).toBe(1);
    expect((dry.verifyWiring as Record<string, unknown>).checked).toEqual(["lead", "p1.1", "p1.2", "p1.3"]);
  });
});
