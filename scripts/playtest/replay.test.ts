// STEP D0-SIDE 段 1(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の R-8・R-3・Q-9)。replay.ts の配線を見張る。
//
// - ソース照合 … 呼び出しの 1 行を消す・別の手順を渡す、を捕まえる
// - 子プロセス(Q-9 の分岐だけ。監査 A の推奨、司令塔の決定)… 再生する手が無い局は、エンジンを起こす前に止まる。そこで
//   `SHOGI_ENGINE_PATH` に存在しないパスを渡して replay.ts を実際に回し、exit code・書いた記録の meta・error 行・record 行の本数を見る。
//   分岐がエンジンの起動より前で止まらなければ、存在しないエンジンの起動で落ちて記録も書かれない(P-30)ので、赤で見分けられる
//   (`resolveEnginePath` はパスを返すだけでファイルを開かない ― apps/server/src/engine/enginePath.ts)。
// 【限界】手を再生する経路(ready 行の本数 (n−1)/2 + 1 と meta の値)はエンジンを起こすので試験の中で走らせない。段 R の記録で確かめる。
// 【静かにスキップしない】npx・tsx・git が無ければ execFileSync が例外を投げて赤になる(status が 1 でないので)。
// 【一時ディレクトリ以外に書かない】走らせる前と後で git status(node_modules だけを除く)が同じであることを確かめる。

import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const REPLAY_TS = join(PLAYTEST_DIR, "replay.ts");

const gitStatus = (): string =>
  execFileSync(
    "git",
    ["status", "--porcelain", "-z", "--untracked-files=all", "--ignored", "--", ".", ":(exclude,glob)**/node_modules", ":(exclude,glob)**/node_modules/**"],
    { cwd: REPO_ROOT },
  ).toString();

describe("replay.ts の配線(R-8・R-3・Q-9。ソース照合)", () => {
  const source = readFileSync(REPLAY_TS, "utf8");

  it("棋譜の手順をそのまま使わず、planReplayMoves が決めた手順を 2 手ずつ読む", () => {
    expect(source).toContain("  const replayPlan = planReplayMoves(kifu.moves);");
    expect(source).toContain("  const moves = replayPlan.moves;");
    expect(source).not.toContain("const moves = kifu.moves;");
    expect(source).toContain("    for (let i = 0; i < moves.length; i += 2) {");
  });

  it("meta に trailingMoveTruncated を常に書き、落としたときだけ落とした手を書く(truncationMetaFields を通す)", () => {
    expect(source).toContain('import { planReplayMoves, truncationMetaFields } from "./lib/replayPlan.js";');
    expect(source).toContain("        ...truncationMetaFields(replayPlan),");
    expect(source).not.toContain("truncatedTrailingMove: replayPlan");
  });

  it("再生する手が無い局は、エンジンを起こす前に理由の error 行を書いて止める", () => {
    const branch = source.indexOf('  if (replayPlan.kind === "noMovesToReplay") {');
    const engineStart = source.indexOf("  const rawEngine = new UsiEngine(enginePath);");
    expect(branch).toBeGreaterThan(-1);
    expect(engineStart).toBeGreaterThan(branch);
    expect(source).toContain("    lines.push(buildErrorLine({ reason: replayPlan.reason, message: NO_MOVES_TO_REPLAY_MESSAGE }));");
  });
});

/** 一時ディレクトリに固定棋譜を書き、存在しないエンジンのパスで replay.ts を回す。書いた記録の行(書かれなければ null)を返す。 */
function runReplayWithoutEngine(moves: string[]): { status: number | null; lines: Record<string, unknown>[] | null; stderr: string } {
  const dir = mkdtempSync(join(tmpdir(), "d0side-replay-"));
  try {
    const kifuPath = join(dir, "kifu.json");
    const outPath = join(dir, "out.jsonl");
    writeFileSync(kifuPath, JSON.stringify({ id: "d0side-no-moves", source: "試験の固定棋譜", moves }), "utf-8");
    let status: number | null = 0;
    let stderr = "";
    try {
      execFileSync("npx", ["tsx", REPLAY_TS, kifuPath, "--out", outPath], {
        cwd: REPO_ROOT,
        encoding: "utf-8",
        stdio: "pipe",
        env: { ...process.env, SHOGI_ENGINE_PATH: join(dir, "no-such-engine") },
      });
    } catch (error) {
      const failure = error as { status: number | null; stderr: string };
      status = failure.status;
      stderr = String(failure.stderr);
    }
    const lines = existsSync(outPath)
      ? readFileSync(outPath, "utf-8").trim().split("\n").map((line) => JSON.parse(line) as Record<string, unknown>)
      : null;
    return { status, lines, stderr };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

describe("replay.ts の Q-9 の分岐(子プロセス。エンジンは起こさない)", () => {
  it(
    "元が 1 手の棋譜: exit 1、meta に trailingMoveTruncated: true と落とした手、error 行の理由 no_moves_to_replay、record 行 0 本、リポジトリに書かない",
    () => {
      const before = gitStatus();
      const result = runReplayWithoutEngine(["7g7f"]);
      expect(gitStatus()).toBe(before);
      expect(result.status, result.stderr).toBe(1);
      expect(result.lines, "記録が書かれていない").not.toBeNull();
      const lines = result.lines!;
      expect(lines.map((line) => line.kind)).toStrictEqual(["meta", "error"]);
      const meta = lines[0]!;
      expect(meta.trailingMoveTruncated).toBe(true);
      expect(meta.truncatedTrailingMove).toBe("7g7f");
      expect(lines[1]!.reason).toBe("no_moves_to_replay");
    },
    60_000,
  );

  it(
    "手数 0 の棋譜: exit 1、meta は trailingMoveTruncated: false で truncatedTrailingMove の欄そのものが無い(null も書かない)、error 行の理由 no_moves_to_replay、record 行 0 本",
    () => {
      const result = runReplayWithoutEngine([]);
      expect(result.status, result.stderr).toBe(1);
      expect(result.lines, "記録が書かれていない").not.toBeNull();
      const lines = result.lines!;
      expect(lines.map((line) => line.kind)).toStrictEqual(["meta", "error"]);
      const meta = lines[0]!;
      expect(meta.trailingMoveTruncated).toBe(false);
      expect(Object.hasOwn(meta, "truncatedTrailingMove")).toBe(false);
      expect(lines[1]!.reason).toBe("no_moves_to_replay");
    },
    60_000,
  );
});
