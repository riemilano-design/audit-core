// STEP FILL 作業 X(docs/STEP_FILL_PLAN_2026-09-22.md §2)。measureCheckBaseline(現局面だけの参考評価)の
// 単体試験。**エンジンは起動しない**(偽の LowPriorityEngine)。
//
// 王手中・非王手中の sfen は apps/server/src/rules/gameStatus.test.ts と同じ構成の局面を使う
// (isInCheck(sfen, "sente") が真になることを、この試験自身で確かめる ― 前提を暗黙にしない)。

import { describe, expect, it } from "vitest";
import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { GoOptions, MultiPvGoResult } from "../../../apps/server/src/engine/usiEngine.js";
import { isGameOver, isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import { measureCheckBaseline } from "./checkBaseline.js";

const STARTPOS_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
/** 5七の後手の飛車が、5九の先手玉に王手をかけている局面(王手中・非終局)。apps/server/src/rules/gameStatus.test.ts と同じ構成。 */
const SENTE_IN_CHECK_SFEN = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";
/** 先手が詰まされた終局(王手中かつ終局)。apps/server/src/api/stateResponse.test.ts の selfCheckmateSfen と同じ構成。 */
const SENTE_CHECKMATED_SFEN = "KPs6/1g7/r8/9/9/9/9/9/9 b - 1";

describe("前提(sfen の性質。この試験自身で確かめる)", () => {
  it("SENTE_IN_CHECK_SFEN は王手中で終局でない", () => {
    expect(isInCheck(SENTE_IN_CHECK_SFEN, "sente")).toBe(true);
    expect(isGameOver(SENTE_IN_CHECK_SFEN)).toBe(false);
  });
  it("SENTE_CHECKMATED_SFEN は王手中かつ終局", () => {
    expect(isInCheck(SENTE_CHECKMATED_SFEN, "sente")).toBe(true);
    expect(isGameOver(SENTE_CHECKMATED_SFEN)).toBe(true);
  });
  it("STARTPOS_SFEN は王手中でない", () => {
    expect(isInCheck(STARTPOS_SFEN, "sente")).toBe(false);
  });
});

interface Call {
  multiPv: number[];
  positions: string[];
  goOptions: GoOptions[];
}

/** goMultiPv が常に同じ1本を返すだけのエンジン。呼び出しの引数を calls に記録する。 */
function stubEngine(pv: string[], calls: Call): LowPriorityEngine {
  const result: MultiPvGoResult = {
    bestmove: pv[0],
    ponder: undefined,
    lines: [{ multipv: 1, score: { type: "cp", value: 77 }, pv, lowerbound: false, upperbound: false }],
    infoLines: [],
  };
  return {
    position: (sfen: string) => calls.positions.push(sfen),
    setMultiPv: (n: number) => calls.multiPv.push(n),
    goMultiPv: async (options: GoOptions = {}) => {
      calls.goOptions.push(options);
      return result;
    },
  };
}

function throwingEngine(): LowPriorityEngine {
  return {
    position: () => {},
    setMultiPv: () => {},
    goMultiPv: async () => {
      throw new Error("エンジンの例外");
    },
  };
}

describe("measureCheckBaseline", () => {
  it("王手中(終局でない)の局面は、MultiPV 1・nodes 固定で現局面だけを読み、scoreCp/mate/bestmove/nodes を返す", async () => {
    const calls: Call = { multiPv: [], positions: [], goOptions: [] };
    const engine = stubEngine(["5i5h"], calls);
    const result = await measureCheckBaseline(SENTE_IN_CHECK_SFEN, engine, 12345);
    expect(result).toEqual({ scoreCp: 77, mate: null, bestmove: "5i5h", nodes: 12345 });
    // afterPass(手番を入れ替えた局面)は読まない ― 呼び出しは1回だけ
    expect(calls.positions).toEqual([SENTE_IN_CHECK_SFEN]);
    expect(calls.multiPv).toEqual([1]);
    expect(calls.goOptions).toEqual([{ nodes: 12345 }]);
  });

  it("王手中でない局面は、エンジンを呼ばずに null", async () => {
    const calls: Call = { multiPv: [], positions: [], goOptions: [] };
    const engine = stubEngine(["7g7f"], calls);
    const result = await measureCheckBaseline(STARTPOS_SFEN, engine, 12345);
    expect(result).toBeNull();
    expect(calls.positions).toEqual([]);
  });

  it("終局(王手中かつ詰み)は、エンジンを呼ばずに null(終局を先に見る)", async () => {
    const calls: Call = { multiPv: [], positions: [], goOptions: [] };
    const engine = stubEngine(["1a1b"], calls);
    const result = await measureCheckBaseline(SENTE_CHECKMATED_SFEN, engine, 12345);
    expect(result).toBeNull();
    expect(calls.positions).toEqual([]);
  });

  it("エンジンの例外は握りつぶして null(測れなかった。推測しない)", async () => {
    const result = await measureCheckBaseline(SENTE_IN_CHECK_SFEN, throwingEngine(), 12345);
    expect(result).toBeNull();
  });

  it("mate で返った場合は mate を、bestmove が無ければ null を運ぶ", async () => {
    const engine: LowPriorityEngine = {
      position: () => {},
      setMultiPv: () => {},
      goMultiPv: async () => ({
        bestmove: undefined,
        ponder: undefined,
        lines: [{ multipv: 1, score: { type: "mate", value: 3 }, pv: [], lowerbound: false, upperbound: false }],
        infoLines: [],
      }),
    };
    const result = await measureCheckBaseline(SENTE_IN_CHECK_SFEN, engine, 1);
    expect(result).toEqual({ scoreCp: null, mate: 3, bestmove: null, nodes: 1 });
  });
});
