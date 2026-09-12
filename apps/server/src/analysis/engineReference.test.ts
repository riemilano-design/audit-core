// 元はSTEP T-7(A-1)のテスト(scripts/playtest/lib/engineReference.test.ts)。
// STEP 5-F(docs/STEP_5-F_PLAN_2026-09-12.md 4. A-1)で本番へ移設した
// engineReference.tsのテストとして、本番側(apps/server/src/analysis/)へ移す。
// テストの内容・件数は変えていない(import元だけをこのファイルからの相対パスに
// 変更した)。

import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import type { Role } from "shogiops/types";
import { describe, expect, it } from "vitest";
import type { LowPriorityEngine } from "../engine/prioritizedEngine.js";
import type { GoOptions, MultiPvGoResult } from "../engine/usiEngine.js";
import { captureSquareOf, measureEngineReference, passSfen } from "./engineReference.js";

const INITIAL_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

/** apps/server/src/api/stateResponse.test.ts の selfCheckmateSfen と同じ組み立て
 * (人間指定テスト1、STEP 4-5)。 */
function customSfen(pieces: Array<{ square: string; color: "sente" | "gote"; role: Role }>): string {
  let board = Board.empty();
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

function selfCheckmateSfen(): string {
  return customSfen([
    { square: "9a", color: "sente", role: "king" },
    { square: "8a", color: "sente", role: "pawn" },
    { square: "9c", color: "gote", role: "rook" },
    { square: "8b", color: "gote", role: "gold" },
    { square: "7a", color: "gote", role: "silver" },
  ]);
}

// gameStatus.test.tsのisInCheckのテストで使われている局面(5七の後手の飛車が
// 5九の先手玉に王手をかけている)。
const SENTE_IN_CHECK_SFEN = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";

function makeFakeEngine(
  results: MultiPvGoResult[],
): { engine: LowPriorityEngine; positions: string[]; goOptions: (GoOptions | undefined)[] } {
  const positions: string[] = [];
  const goOptions: (GoOptions | undefined)[] = [];
  let callIndex = 0;

  const engine: LowPriorityEngine = {
    position: (sfen: string) => {
      positions.push(sfen);
    },
    setMultiPv: () => {
      // 呼ばれたことは position/goMultiPv の順序で十分検証できるため記録しない。
    },
    goMultiPv: async (options?: GoOptions): Promise<MultiPvGoResult> => {
      goOptions.push(options);
      const result = results[callIndex];
      callIndex += 1;
      if (!result) throw new Error("unexpected extra goMultiPv call");
      return result;
    },
  };

  return { engine, positions, goOptions };
}

describe("passSfen", () => {
  it("手番bをwへ入れ替える", () => {
    expect(passSfen(INITIAL_SFEN)).toBe(
      "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1",
    );
  });

  it("手番wをbへ入れ替える", () => {
    const wSfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1";
    expect(passSfen(wSfen)).toBe(INITIAL_SFEN);
  });
});

describe("captureSquareOf", () => {
  it("移動先に先手の駒がある場合、そのマスを返す", () => {
    // 初期局面、8八の角(先手)を取る手(相手が指したと仮定)。
    expect(captureSquareOf(INITIAL_SFEN, "2b8h")).toBe("8h");
  });

  it("移動先に先手の駒が無い場合、nullを返す", () => {
    expect(captureSquareOf(INITIAL_SFEN, "7g7f")).toBeNull();
  });

  it("移動先の駒が先手ではなく後手の場合、nullを返す", () => {
    // 8八の角(先手)ではなく2二の角(後手)を移動先に指定する。
    expect(captureSquareOf(INITIAL_SFEN, "8h2b")).toBeNull();
  });

  it("打つ手(ドロップ)でも移動先だけを見て判定する", () => {
    expect(captureSquareOf(INITIAL_SFEN, "P*8h")).toBe("8h");
  });

  it("moveUsiがnullならnullを返す", () => {
    expect(captureSquareOf(INITIAL_SFEN, null)).toBeNull();
  });
});

describe("measureEngineReference", () => {
  it("baseline・afterPass・dropCp・captureSquareを組み立てる(両方cpのとき)", async () => {
    const { engine, positions, goOptions } = makeFakeEngine([
      {
        bestmove: "6i7h",
        ponder: undefined,
        lines: [{ multipv: 1, score: { type: "cp", value: -324 }, pv: ["6i7h"], lowerbound: false, upperbound: false }],
        infoLines: [],
      },
      {
        bestmove: "2b8h",
        ponder: undefined,
        lines: [{ multipv: 1, score: { type: "cp", value: 1410 }, pv: ["2b8h"], lowerbound: false, upperbound: false }],
        infoLines: [],
      },
    ]);

    const result = await measureEngineReference(INITIAL_SFEN, engine, 4_000_000);

    expect(result.reference).toEqual({
      baseline: { scoreCp: -324, mate: null, bestmove: "6i7h" },
      afterPass: { scoreCp: 1410, mate: null, bestmove: "2b8h", captureSquare: "8h" },
      dropCp: -324 - -1410,
      nodes: 4_000_000,
    });
    expect(positions).toEqual([INITIAL_SFEN, passSfen(INITIAL_SFEN)]);
    expect(goOptions).toEqual([{ nodes: 4_000_000 }, { nodes: 4_000_000 }]);
  });

  it("mateのときはscoreCpをnullにし、dropCpもnullにする", async () => {
    const { engine } = makeFakeEngine([
      { bestmove: "6i7h", ponder: undefined, lines: [{ multipv: 1, score: { type: "mate", value: 3 }, pv: [], lowerbound: false, upperbound: false }], infoLines: [] },
      { bestmove: "8h2b", ponder: undefined, lines: [{ multipv: 1, score: { type: "cp", value: 1410 }, pv: [], lowerbound: false, upperbound: false }], infoLines: [] },
    ]);

    const result = await measureEngineReference(INITIAL_SFEN, engine, 4_000_000);

    expect(result.reference?.baseline).toEqual({ scoreCp: null, mate: 3, bestmove: "6i7h" });
    expect(result.reference?.dropCp).toBeNull();
  });

  it("afterPass.bestmoveの移動先に先手の駒が無ければcaptureSquareはnull", async () => {
    const { engine } = makeFakeEngine([
      { bestmove: "6i7h", ponder: undefined, lines: [{ multipv: 1, score: { type: "cp", value: 0 }, pv: [], lowerbound: false, upperbound: false }], infoLines: [] },
      { bestmove: "3c3d", ponder: undefined, lines: [{ multipv: 1, score: { type: "cp", value: 0 }, pv: [], lowerbound: false, upperbound: false }], infoLines: [] },
    ]);

    const result = await measureEngineReference(INITIAL_SFEN, engine, 4_000_000);

    expect(result.reference?.afterPass.captureSquare).toBeNull();
  });

  it("終局していれば測らずnullを返す", async () => {
    const { engine, goOptions } = makeFakeEngine([]);

    const result = await measureEngineReference(selfCheckmateSfen(), engine, 4_000_000);

    expect(result.reference).toBeNull();
    expect(result.searchPvs).toEqual([]);
    expect(goOptions).toEqual([]);
  });

  it("先手が王手中なら測らずnullを返す", async () => {
    const { engine, goOptions } = makeFakeEngine([]);

    const result = await measureEngineReference(SENTE_IN_CHECK_SFEN, engine, 4_000_000);

    expect(result.reference).toBeNull();
    expect(result.searchPvs).toEqual([]);
    expect(goOptions).toEqual([]);
  });

  it("エンジンが例外を投げた場合はnullを返す(推測しない)", async () => {
    const engine: LowPriorityEngine = {
      position: () => {},
      setMultiPv: () => {},
      goMultiPv: async () => {
        throw new Error("engine timeout");
      },
    };

    const result = await measureEngineReference(INITIAL_SFEN, engine, 4_000_000);

    expect(result.reference).toBeNull();
    // 1本目から例外なので、測れた読み筋も無い。
    expect(result.searchPvs).toEqual([]);
  });

  // --- STEP U6-L(docs/STEP_U6-L_PLAN_2026-09-13.md)。読み筋の持ち回り。 ---

  it("STEP U6-L: ③が使うのと同じ探索結果から、読み筋を2本ぶん返す", async () => {
    const { engine } = makeFakeEngine([
      {
        bestmove: "6i7h",
        ponder: undefined,
        lines: [
          { multipv: 1, score: { type: "cp", value: -324 }, pv: ["6i7h", "3c3d"], lowerbound: false, upperbound: false },
        ],
        infoLines: [],
      },
      {
        bestmove: "2b8h",
        ponder: undefined,
        lines: [{ multipv: 1, score: { type: "cp", value: 1410 }, pv: ["2b8h"], lowerbound: true, upperbound: false }],
        infoLines: [],
      },
    ]);

    const result = await measureEngineReference(INITIAL_SFEN, engine, 4_000_000);

    expect(result.searchPvs).toEqual([
      {
        source: "focus_baseline",
        sfen: INITIAL_SFEN,
        moveUsi: null,
        multipv: 1,
        scoreCp: -324,
        mate: null,
        pv: ["6i7h", "3c3d"],
        lowerbound: false,
        upperbound: false,
      },
      {
        source: "focus_after_pass",
        sfen: passSfen(INITIAL_SFEN),
        moveUsi: null,
        multipv: 1,
        scoreCp: 1410,
        mate: null,
        pv: ["2b8h"],
        lowerbound: true,
        upperbound: false,
      },
    ]);
  });

  it("STEP U6-L: 長さ0・長さ1の読み筋も捨てずに記録する(記録側で長さの門番を持たない)", async () => {
    const { engine } = makeFakeEngine([
      { bestmove: "6i7h", ponder: undefined, lines: [{ multipv: 1, score: { type: "cp", value: 0 }, pv: [], lowerbound: false, upperbound: false }], infoLines: [] },
      { bestmove: "3c3d", ponder: undefined, lines: [{ multipv: 1, score: { type: "cp", value: 0 }, pv: ["3c3d"], lowerbound: false, upperbound: false }], infoLines: [] },
    ]);

    const result = await measureEngineReference(INITIAL_SFEN, engine, 4_000_000);

    expect(result.searchPvs.map((o) => o.pv)).toEqual([[], ["3c3d"]]);
  });

  it("STEP U6-L: 2本目で例外になっても、測れた1本目の読み筋は返す", async () => {
    let calls = 0;
    const engine: LowPriorityEngine = {
      position: () => {},
      setMultiPv: () => {},
      goMultiPv: async () => {
        calls += 1;
        if (calls === 1) {
          return {
            bestmove: "6i7h",
            ponder: undefined,
            lines: [{ multipv: 1, score: { type: "cp", value: 12 }, pv: ["6i7h"], lowerbound: false, upperbound: false }],
            infoLines: [],
          };
        }
        throw new Error("engine timeout");
      },
    };

    const result = await measureEngineReference(INITIAL_SFEN, engine, 4_000_000);

    expect(result.reference).toBeNull();
    expect(result.searchPvs).toHaveLength(1);
    expect(result.searchPvs[0]?.source).toBe("focus_baseline");
  });
});
