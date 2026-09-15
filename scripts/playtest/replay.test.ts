// STEP D0-SIDE 段 1(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の R-8・R-3・Q-9)と段 2(R-1〜R-4・Q-9 の (b)(c))。replay.ts の配線を見張る。
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

/** F-S8 の開始局面(平手・後手番の初期局面に、回した 1 手目 3c3d を当てた局面。手で導いた値。計画 11.5) */
const FS8_START = "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2";

/** meta に再生の手順や判定の欄が漏れていない(監査 A の任意 2。子プロセスは見る欄を個別に読むので、漏れを別に見る) */
function expectNoPlanFieldsInMeta(meta: Record<string, unknown>): void {
  for (const key of ["moves", "reason", "originalMoves", "alignment"]) expect(Object.hasOwn(meta, key), key).toBe(false);
}

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

  it("段 2(R-1〜R-4): そろえの欄を meta より前に読み、同じ開始局面の文字列を GameState と解析の initialSfen に渡し、meta に mirrored の欄を書く", () => {
    const readAt = source.indexOf("  const { alignment: sideAlignment, sideAlignmentChecked } = readSideAlignment(kifu);");
    expect(readAt).toBeGreaterThan(-1);
    expect(readAt).toBeLessThan(source.indexOf("    buildMetaLine({"));
    expect(source).toContain("  const replayStartSfen = sideAlignment.mirrored ? sideAlignment.startSfen : undefined;");
    expect(source).toContain("      : { directionRule, suppressTargetShapeProgress, initialSfen: replayStartSfen };");
    expect(source).toContain("    let state: GameState = replayStartSfen === undefined ? initialState : { ...initialState, sfen: replayStartSfen };");
    expect(source).toContain("        ...sideMetaFields(sideAlignment),");
    expect(source).toContain("        sideAlignmentChecked,");
    expect(source).not.toContain("createInitialGameState(undefined, { variants: getApprovedScenarioVariants() }).sfen");
  });
});

/** 一時ディレクトリに固定棋譜を書き、存在しないエンジンのパスで replay.ts を回す。書いた記録の行(書かれなければ null)を返す。 */
function runReplayWithoutEngine(kifuFields: Record<string, unknown>): { status: number | null; lines: Record<string, unknown>[] | null; stderr: string } {
  const dir = mkdtempSync(join(tmpdir(), "d0side-replay-"));
  try {
    const kifuPath = join(dir, "kifu.json");
    const outPath = join(dir, "out.jsonl");
    writeFileSync(kifuPath, JSON.stringify({ id: "d0side-no-moves", source: "試験の固定棋譜", ...kifuFields }), "utf-8");
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
      const result = runReplayWithoutEngine({ moves: ["7g7f"] });
      expect(gitStatus()).toBe(before);
      expect(result.status, result.stderr).toBe(1);
      expect(result.lines, "記録が書かれていない").not.toBeNull();
      const lines = result.lines!;
      expect(lines.map((line) => line.kind)).toStrictEqual(["meta", "error"]);
      const meta = lines[0]!;
      expect(meta.trailingMoveTruncated).toBe(true);
      expect(meta.truncatedTrailingMove).toBe("7g7f");
      // 段 2: 回していない局は mirrored: false だけで、startSfen・plyOffset・originalUserSide の欄は無い
      expect(meta.mirrored).toBe(false);
      for (const key of ["startSfen", "plyOffset", "originalUserSide"]) expect(Object.hasOwn(meta, key), key).toBe(false);
      expect(meta.sideAlignmentChecked).toBe(false);
      expectNoPlanFieldsInMeta(meta);
      expect(lines[1]!.reason).toBe("no_moves_to_replay");
    },
    60_000,
  );

  it(
    "手数 0 の棋譜: exit 1、meta は trailingMoveTruncated: false で truncatedTrailingMove の欄そのものが無い(null も書かない)、error 行の理由 no_moves_to_replay、record 行 0 本",
    () => {
      const result = runReplayWithoutEngine({ moves: [] });
      expect(result.status, result.stderr).toBe(1);
      expect(result.lines, "記録が書かれていない").not.toBeNull();
      const lines = result.lines!;
      expect(lines.map((line) => line.kind)).toStrictEqual(["meta", "error"]);
      const meta = lines[0]!;
      expect(meta.trailingMoveTruncated).toBe(false);
      expect(Object.hasOwn(meta, "truncatedTrailingMove")).toBe(false);
      expect(meta.mirrored).toBe(false);
      for (const key of ["startSfen", "plyOffset", "originalUserSide"]) expect(Object.hasOwn(meta, key), key).toBe(false);
      expect(meta.sideAlignmentChecked).toBe(false);
      expectNoPlanFieldsInMeta(meta);
      expect(lines[1]!.reason).toBe("no_moves_to_replay");
    },
    60_000,
  );

  it(
    "F-S9a (iv-b): 本人が後手・元 2 手を回して畳んだ棋譜(手順 1 手): exit 1、meta に mirrored: true・originalUserSide・plyOffset・startSfen と落とした手、error 行の理由 no_moves_to_replay",
    () => {
      const result = runReplayWithoutEngine({
        mirrored: true,
        originalUserSide: "gote",
        plyOffset: 1,
        startSfen: FS8_START,
        moves: ["7g7f"],
        originalMoves: ["7g7f", "3c3d"],
      });
      expect(result.status, result.stderr).toBe(1);
      expect(result.lines, "記録が書かれていない").not.toBeNull();
      const lines = result.lines!;
      expect(lines.map((line) => line.kind)).toStrictEqual(["meta", "error"]);
      const meta = lines[0]!;
      expect(meta.mirrored).toBe(true);
      expect(meta.originalUserSide).toBe("gote");
      expect(meta.plyOffset).toBe(1);
      expect(meta.startSfen).toBe(FS8_START);
      expect(meta.sideAlignmentChecked).toBe(true);
      expect(meta.trailingMoveTruncated).toBe(true);
      expect(meta.truncatedTrailingMove).toBe("7g7f");
      expectNoPlanFieldsInMeta(meta);
      expect(lines[1]!.reason).toBe("no_moves_to_replay");
    },
    60_000,
  );

  it(
    "F-S9a (iv-c): 本人が後手・元 1 手を回して畳んだ棋譜(手順 0 手): exit 1、meta に mirrored: true と開始局面、trailingMoveTruncated: false(落とした手の欄は無い)、error 行の理由 no_moves_to_replay",
    () => {
      const result = runReplayWithoutEngine({ mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START, moves: [], originalMoves: ["7g7f"] });
      expect(result.status, result.stderr).toBe(1);
      expect(result.lines, "記録が書かれていない").not.toBeNull();
      const lines = result.lines!;
      expect(lines.map((line) => line.kind)).toStrictEqual(["meta", "error"]);
      const meta = lines[0]!;
      expect(meta.mirrored).toBe(true);
      expect(meta.startSfen).toBe(FS8_START);
      expect(meta.plyOffset).toBe(1);
      expect(meta.sideAlignmentChecked).toBe(true);
      expect(meta.trailingMoveTruncated).toBe(false);
      expect(Object.hasOwn(meta, "truncatedTrailingMove")).toBe(false);
      expectNoPlanFieldsInMeta(meta);
      expect(lines[1]!.reason).toBe("no_moves_to_replay");
    },
    60_000,
  );

  it(
    "そろえの欄の形が食い違う棋譜(mirrored: true なのに startSfen が無い): 記録を書かずに exit 1 で止まり、理由を標準エラーに出す(平手として黙って再生しない)",
    () => {
      const result = runReplayWithoutEngine({ mirrored: true, moves: ["7g7f", "3c3d"] });
      expect(result.status).toBe(1);
      expect(result.lines).toBeNull();
      expect(result.stderr).toContain("mirrored が true の棋譜には");
    },
    60_000,
  );

  it(
    "originalMoves の無い回した棋譜(手順 0 手): 照合せずに再生の判定へ進み、meta に mirrored: true と sideAlignmentChecked: false を書く(照合せずに通したことが記録に残る)",
    () => {
      const result = runReplayWithoutEngine({ mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START, moves: [] });
      expect(result.status, result.stderr).toBe(1);
      expect(result.lines, "記録が書かれていない").not.toBeNull();
      const meta = result.lines![0]!;
      expect(meta.mirrored).toBe(true);
      expect(meta.sideAlignmentChecked).toBe(false);
      expect(result.lines![1]!.reason).toBe("no_moves_to_replay");
    },
    60_000,
  );

  it(
    "moves を 1 手変えた回した棋譜(originalMoves との照合が食い違う): 記録を書かずに exit 1 で止まり、理由を標準エラーに出す",
    () => {
      const result = runReplayWithoutEngine({ mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START, moves: ["7g7e"], originalMoves: ["7g7f", "3c3d"] });
      expect(result.status).toBe(1);
      expect(result.lines).toBeNull();
      expect(result.stderr).toContain("一致しません");
    },
    60_000,
  );
});
