// STEP FILL 作業 X(docs/STEP_FILL_PLAN_2026-09-22.md §2)。buildReadyRecord が ready 行へ
// checkBaseline を書く配線を見張る。**エンジンは起動しない**(偽の LowPriorityEngine)。
//
// recorder.test.ts のスタブ(position/setMultiPv/goMultiPv)と同じ形。GameState は
// 王手中の局面(SENTE_IN_CHECK_SFEN)・非王手中の局面(STARTPOS_SFEN)を使う。

import { describe, expect, it } from "vitest";
import { buildReadyRecord } from "./recorder.js";
import type { GameState } from "../../../apps/server/src/game/gameSession.js";
import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { MultiPvGoResult } from "../../../apps/server/src/engine/usiEngine.js";

const STARTPOS_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
/** 5七の後手の飛車が、5九の先手玉に王手をかけている局面(王手中・非終局)。apps/server/src/rules/gameStatus.test.ts と同じ構成。 */
const SENTE_IN_CHECK_SFEN = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";
/** 先手が詰まされた終局(王手中かつ終局)。apps/server/src/api/stateResponse.test.ts の selfCheckmateSfen と同じ構成。 */
const SENTE_CHECKMATED_SFEN = "KPs6/1g7/r8/9/9/9/9/9/9 b - 1";

function stateAt(sfen: string): GameState {
  return { sfen, moveHistory: [], forcedPliesUsed: 0 };
}

/** goMultiPv が常に同じ1本を返すだけのエンジン(候補手計算用。呼ばれても構わないが中身は使わない)。 */
function planEngine(): LowPriorityEngine {
  const result: MultiPvGoResult = {
    bestmove: "7g7f",
    ponder: undefined,
    lines: [{ multipv: 1, score: { type: "cp", value: 42 }, pv: ["7g7f"], lowerbound: false, upperbound: false }],
    infoLines: [],
  };
  return { position: () => {}, setMultiPv: () => {}, goMultiPv: async () => result };
}

/** engineReference・checkBaseline を測る側のスタブ。常に同じ1本を返す。 */
function referenceEngine(scoreCp: number): { engine: LowPriorityEngine } {
  const result: MultiPvGoResult = {
    bestmove: "5i5h",
    ponder: undefined,
    lines: [{ multipv: 1, score: { type: "cp", value: scoreCp }, pv: ["5i5h"], lowerbound: false, upperbound: false }],
    infoLines: [],
  };
  const engine: LowPriorityEngine = { position: () => {}, setMultiPv: () => {}, goMultiPv: async () => result };
  return { engine };
}

async function callBuildReadyRecord(sfen: string, referenceNodes: number, refEngine: LowPriorityEngine) {
  return buildReadyRecord(
    stateAt(sfen),
    2,
    "7g7f",
    "3c3d",
    planEngine(),
    false,
    null,
    null,
    [],
    refEngine,
    referenceNodes,
    planEngine(),
  );
}

describe("buildReadyRecord: checkBaseline(STEP FILL 作業 X)", () => {
  it("王手中(終局でない)・referenceNodes > 0 の行は checkBaseline を書く(engineReference は null のまま)", async () => {
    const { engine } = referenceEngine(-500);
    const { line } = await callBuildReadyRecord(SENTE_IN_CHECK_SFEN, 4_000_000, engine);
    const parsed = JSON.parse(line) as { engineReference: unknown; checkBaseline?: unknown };
    expect(parsed.engineReference).toBeNull();
    expect(parsed.checkBaseline).toEqual({ scoreCp: -500, mate: null, bestmove: "5i5h", nodes: 4_000_000 });
  });

  it("王手中でない行は checkBaseline の欄自体が無い", async () => {
    const { engine } = referenceEngine(0);
    const { line } = await callBuildReadyRecord(STARTPOS_SFEN, 4_000_000, engine);
    const parsed = JSON.parse(line) as Record<string, unknown>;
    expect(Object.keys(parsed)).not.toContain("checkBaseline");
  });

  it("終局(王手中かつ詰み)の行は checkBaseline の欄自体が無い", async () => {
    const { engine } = referenceEngine(0);
    const { line } = await callBuildReadyRecord(SENTE_CHECKMATED_SFEN, 4_000_000, engine);
    const parsed = JSON.parse(line) as Record<string, unknown>;
    expect(Object.keys(parsed)).not.toContain("checkBaseline");
  });

  it("referenceNodes が 0(測らない設定)の行は、王手中でも checkBaseline の欄自体が無い", async () => {
    const { engine } = referenceEngine(-500);
    const { line } = await callBuildReadyRecord(SENTE_IN_CHECK_SFEN, 0, engine);
    const parsed = JSON.parse(line) as Record<string, unknown>;
    expect(parsed.engineReference).toBeNull();
    expect(Object.keys(parsed)).not.toContain("checkBaseline");
  });

  it("immediate 行には checkBaseline のキー自体が出ない(既存の JSONL の形を変えない)", async () => {
    const { buildImmediateRecord } = await import("./recorder.js");
    const { line } = buildImmediateRecord(stateAt(SENTE_IN_CHECK_SFEN), 1, "7g7f", null, false, null, null, []);
    expect(Object.keys(JSON.parse(line) as object)).not.toContain("checkBaseline");
  });
});
