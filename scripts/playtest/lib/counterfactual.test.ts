// STEP D2(docs/STEP_D2_PLAN_2026-09-15.md 3.)の lib の試験。**エンジンは起動しない。**
//
// 【正解の置き方(規則 11.1)】固定例 F-1〜F-16 の手順と期待は、計画書 3. に試験を回す前に手で書いた表のまま(実装の出力から写さない)。
// F-1・F-2・F-3・F-6・F-16 の手順は、計画の段階で B と事前読み A が本番の規則の関数に通して合法と期待を確かめている(計画 3.・11.)。
// 【この試験が確かめないこと】20 局版の記録(盲検の条件 ― 計画 5.3)。v0.4 のスキーマの変種と境目(lib/failureEventSchema.test.ts が見る。ここでは F-11 の 1 行が通ることだけ)。

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import { applyMove, IllegalMoveError } from "../../../apps/server/src/rules/applyMove.js";
import type { RecordLine } from "../invariants/types.js";
import {
  counterfactualLines,
  counterfactualOf,
  kingEscapesOf,
  type Counterfactual,
  type CounterfactualComparison,
  type CounterfactualInput,
  POSITION_FACTS_RULES,
  type CounterfactualDiff,
  type SequenceFacts,
} from "./counterfactual.js";
import { actualContinuation, buildDiagnosisReport, diagnoseRecords, DRAFT_RULE_1, NOT_EVALUATION_CP, renderDiagnosisReport, STANDING_BOUNDS } from "./failureEvent.js";
import { positionFactsDiff, positionFactsOf } from "./positionFacts.js";
import { engineRef, GAME01_MOVES, plantedRecords } from "./failureEventFixtures.js";
import { buildProvenance, FAILURE_EVENT_SCHEMA_VERSION, loadFailureEventSchema, toEventLine, validateFailureEventLine } from "./failureEventSchema.js";
import { alignMovesToSente } from "./sideAlignment.js";

const INIT = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
const WINDOW = DRAFT_RULE_1.windowPlies;

const F1_ACTUAL = ["7g7f", "3c3d", "8h2b+", "3a2b", "B*4e"];
const F1_PV = ["7g7f", "3c3d", "2g2f", "4a3b", "2f2e"];
const F2_ACTUAL = ["7g7f", "3c3d", "8h3c+", "4a4b", "3c4b"];
const ROOK_ROOT = "4k4/9/9/9/9/9/9/9/4K4 b Rr 1";
const MATE_ROOT = "4k4/9/4P4/9/9/9/9/9/4K4 b G 1";
const STALEMATE_ROOT = "k8/2G6/9/1G7/9/9/9/9/4K4 b - 1";
/** 監査 1e の S-2: 後手の歩 5g が 5h を守り、後手が金を持つ。先手が 1g1f なら G*5h で詰む */
const GOTE_MATE_ROOT = "4k4/9/9/9/9/9/4p3P/9/4K4 b g 1";
/** 監査 1e の S-3: 先手の金 5h。4g へ行けば玉の周りから外れ、4h へ行けば周りに残る */
const GOLD_ROOT = "4k4/9/9/9/9/9/9/4G4/4K4 b - 1";
const F12_PREFIX = ["1g1f", "1c1d", "9g9f", "9c9d", "1f1e", "8c8d", "9f9e", "2c2d", "4g4f", "7c7d"];
const F12_ROOT = "lnsgkgsnl/1r5b1/3pppp2/ppp4pp/P7P/5P3/1PPPP1PP1/1B5R1/LNSGKGSNL b - 11";

function focusBaseline(sfen: string, pv: string[], extra: Partial<SearchPvObservation> = {}): SearchPvObservation {
  return { source: "focus_baseline", sfen, moveUsi: null, multipv: 1, scoreCp: 0, mate: null, pv, lowerbound: false, upperbound: false, ...extra };
}

/** 根から実戦と読み筋を並べる入力(前置きがあれば INIT から、無ければ根を開始局面にする) */
function input(
  root: string,
  actual: string[],
  pv: string[] | { searchPvs: SearchPvObservation[] | null | undefined },
  options: { prefix?: string[]; bestmoveAtBefore?: string | null; pvExtra?: Partial<SearchPvObservation>; windowPlies?: number } = {},
): CounterfactualInput {
  const prefix = options.prefix ?? [];
  const searchPvs = Array.isArray(pv) ? [focusBaseline(root, pv, options.pvExtra)] : pv.searchPvs;
  const record: Pick<RecordLine, "sfen" | "searchPvs"> = { sfen: root };
  if (searchPvs !== undefined) record.searchPvs = searchPvs;
  return {
    record,
    moves: [...prefix, ...actual],
    branchPly: prefix.length + 1,
    windowPlies: options.windowPlies ?? WINDOW,
    initialSfen: prefix.length > 0 ? INIT : root,
    bestmoveAtBefore: options.bestmoveAtBefore ?? null,
  };
}

function compared(counterfactual: Counterfactual): CounterfactualComparison {
  expect(counterfactual.state).toBe("compared");
  if (counterfactual.state !== "compared") throw new Error(`compared でない: ${counterfactual.state}`);
  return counterfactual;
}

const NO_CHECKS = { byUs: [], byOpponent: [] };

/** STEP D2.5 の欄(positionFactsEnd・pvMinusActual.positionFacts)は D2 の期待に入れず、別の試験(このファイルの末尾・lib/positionFacts.test.ts)で見る */
const d2Facts = (facts: SequenceFacts) => {
  // STEP D2.6 の userMoveFacts も D2 の固定例の外(lib/moveFacts.test.ts が見る)
  const { positionFactsEnd: _positionFactsEnd, userMoveFacts: _userMoveFacts, ...rest } = facts;
  return rest;
};
const d2Diff = (diff: CounterfactualDiff) => {
  const { positionFacts: _positionFacts, ...rest } = diff;
  return rest;
};

describe("前提", () => {
  it("INIT は本番の平手の初期局面と同じ文字列", () => {
    expect(DEFAULT_INITIAL_SFEN).toBe(INIT);
  });
});

describe("STEP D2 の固定例(計画 3.)", () => {
  it("F-1 取った駒が違う: N = 5、実戦 us 角 1 / opponent 角 1、読み筋 空、差 us 角 −1・opponent 角 −1、玉の周り 5 / 2、逃げ道 3", () => {
    const c = compared(counterfactualOf(input(INIT, F1_ACTUAL, F1_PV)));
    expect([c.comparedPlies, c.actualPlies, c.pvLength, c.pvUsablePlies, c.pvTruncatedAtPly]).toEqual([5, 5, 5, 5, null]);
    expect(d2Facts(c.actual)).toEqual({
      capturedRoles: { us: { bishop: 1 }, opponent: { bishop: 1 } },
      checks: NO_CHECKS,
      mate: null,
      gameEnd: null,
      kingSurroundingsEnd: { squares: 5, own: 2 },
      kingEscapesEnd: { state: "counted", count: 3 },
    });
    expect(d2Facts(c.pv)).toEqual({
      capturedRoles: { us: {}, opponent: {} },
      checks: NO_CHECKS,
      mate: null,
      gameEnd: null,
      kingSurroundingsEnd: { squares: 5, own: 2 },
      kingEscapesEnd: { state: "counted", count: 3 },
    });
    expect(d2Diff(c.pvMinusActual)).toEqual({ capturedRoles: { us: { bishop: -1 }, opponent: { bishop: -1 } }, kingSurroundingsOwn: 0, kingEscapes: 0 });
    expect(c.kingEscapesRoot).toEqual({ state: "counted", count: 3 });
    expect(c.kingEscapesChangeFromRoot).toEqual({ actual: 0, pv: 0 });
  });

  it("F-2 王手がある: 実戦 byUs [3, 5]・us 金 1、終わりは後手玉に王手で逃げ道は数えられない(差 null)", () => {
    const c = compared(counterfactualOf(input(INIT, F2_ACTUAL, F1_PV)));
    expect(c.comparedPlies).toBe(5);
    expect(c.actual.checks).toEqual({ byUs: [3, 5], byOpponent: [] });
    expect(c.actual.capturedRoles).toEqual({ us: { gold: 1 }, opponent: {} });
    expect(c.actual.kingEscapesEnd).toEqual({ state: "opponentInCheck" });
    expect(c.actual.kingSurroundingsEnd).toEqual({ squares: 5, own: 2 });
    expect(c.pv.checks).toEqual(NO_CHECKS);
    expect(c.pv.capturedRoles).toEqual({ us: {}, opponent: {} });
    expect(c.pv.kingEscapesEnd).toEqual({ state: "counted", count: 3 });
    expect(d2Diff(c.pvMinusActual)).toEqual({ capturedRoles: { us: { gold: -1 }, opponent: {} }, kingSurroundingsOwn: 0, kingEscapes: null });
    expect(c.kingEscapesChangeFromRoot).toEqual({ actual: null, pv: 0 });
  });

  it("F-3 逃げ道が違う: N = 2、逃げ道 実戦 5・読み筋 6(差 +1)、読み筋 byOpponent [2]、玉の周り 8 / 0、根の逃げ道 5", () => {
    const c = compared(counterfactualOf(input(ROOK_ROOT, ["5i5h", "R*4c"], ["5i5h", "R*5c"])));
    expect(c.comparedPlies).toBe(2);
    expect(c.actual.kingEscapesEnd).toEqual({ state: "counted", count: 5 });
    expect(c.pv.kingEscapesEnd).toEqual({ state: "counted", count: 6 });
    expect(c.pvMinusActual.kingEscapes).toBe(1);
    expect(c.pv.checks).toEqual({ byUs: [], byOpponent: [2] });
    expect(c.actual.checks).toEqual(NO_CHECKS);
    expect([c.actual.kingSurroundingsEnd, c.pv.kingSurroundingsEnd]).toEqual([
      { squares: 8, own: 0 },
      { squares: 8, own: 0 },
    ]);
    expect(c.kingEscapesRoot).toEqual({ state: "counted", count: 5 });
    expect(c.kingEscapesChangeFromRoot).toEqual({ actual: 0, pv: 1 });
  });

  it("F-4 読み筋の無い行: 欄なし・null・focus_baseline なし・0 手を 4 つの状態に分ける", () => {
    expect(counterfactualOf(input(INIT, F1_ACTUAL, { searchPvs: undefined })).state).toBe("unrecorded");
    expect(counterfactualOf(input(INIT, F1_ACTUAL, { searchPvs: null })).state).toBe("notMeasurable");
    expect(counterfactualOf(input(INIT, F1_ACTUAL, { searchPvs: [focusBaseline(INIT, F1_PV, { source: "focus_after_pass" })] })).state).toBe(
      "noFocusBaseline",
    );
    expect(counterfactualOf(input(INIT, F1_ACTUAL, { searchPvs: [focusBaseline(INIT, [])] })).state).toBe("emptyPv");
  });

  it("F-4 Event は D2 の欄が無くても今までどおり出る(searchPvs を植えない記録は unrecorded)", () => {
    const records = plantedRecords(GAME01_MOVES, { 48: engineRef(500, { bestmove: "2h2g" }), 50: engineRef(-300) });
    const event = diagnoseRecords("game-01", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN).events.find((e) => e.branchPly === 49);
    expect(event).toBeDefined();
    expect(event!.counterfactual).toEqual({ state: "unrecorded" });
  });

  it("F-5 読み筋が窓より短い: N = 2、標識 lowerbound を残し、実戦も 2 手で切る(3 手目の角の取り合いを数えない)", () => {
    const c = compared(counterfactualOf(input(INIT, F1_ACTUAL, ["7g7f", "3c3d"], { pvExtra: { lowerbound: true } })));
    expect([c.comparedPlies, c.windowPlies, c.pvLength, c.pvUsablePlies, c.actualPlies]).toEqual([2, 5, 2, 2, 5]);
    expect(c.pvBounded).toEqual({ lowerbound: true, upperbound: false });
    expect(c.actual.capturedRoles).toEqual({ us: {}, opponent: {} });
    expect(c.pv.capturedRoles).toEqual({ us: {}, opponent: {} });
  });

  it("F-6 読み筋が詰みで終わる: N = 1、読み筋 詰み 1 手目(先手の勝ち)・王手 [1]・逃げ道は数えられない、実戦 詰みなし・逃げ道 8・玉の周り 8 / 0", () => {
    const c = compared(counterfactualOf(input(MATE_ROOT, ["5i4h", "5a4a"], ["G*5b"])));
    expect([c.comparedPlies, c.actualPlies, c.pvUsablePlies]).toEqual([1, 2, 1]);
    expect(c.pv.mate).toEqual({ ply: 1, winner: "sente" });
    expect(c.pv.gameEnd).toBeNull();
    expect(c.pv.checks).toEqual({ byUs: [1], byOpponent: [] });
    expect(c.pv.kingEscapesEnd).toEqual({ state: "opponentInCheck" });
    expect(c.pv.kingSurroundingsEnd).toEqual({ squares: 5, own: 0 });
    expect(c.actual.mate).toBeNull();
    expect(c.actual.checks).toEqual(NO_CHECKS);
    expect(c.actual.kingEscapesEnd).toEqual({ state: "counted", count: 8 });
    expect(c.actual.kingSurroundingsEnd).toEqual({ squares: 8, own: 0 });
  });

  it("F-7 根の局面が違う読み筋は rootMismatch", () => {
    const other = "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2";
    expect(counterfactualOf(input(INIT, F1_ACTUAL, { searchPvs: [focusBaseline(other, F1_PV)] })).state).toBe("rootMismatch");
  });

  it("F-8 1 手目の一致の欄: 成/不成だけ違う bestmove とは同じと言わない。読み筋 = 実戦なら実戦の手と同じで、差はすべて 0", () => {
    const differs = compared(counterfactualOf(input(INIT, F1_ACTUAL, F1_PV, { bestmoveAtBefore: "7g7f+" })));
    expect(differs.pvFirstMoveIsBestmoveAtBefore).toBe(false);
    const same = compared(counterfactualOf(input(INIT, F1_ACTUAL, [...F1_ACTUAL], { bestmoveAtBefore: "7g7f" })));
    expect([same.pvFirstMove, same.pvFirstMoveIsBestmoveAtBefore, same.pvFirstMoveIsPlayedMove]).toEqual(["7g7f", true, true]);
    expect(d2Diff(same.pvMinusActual)).toEqual({ capturedRoles: { us: {}, opponent: {} }, kingSurroundingsOwn: 0, kingEscapes: 0 });
  });

  it("F-9 読み筋に非合法手: 打ち切り 4・並べられた 3・N = 3", () => {
    const c = compared(counterfactualOf(input(INIT, F1_ACTUAL, ["7g7f", "3c3d", "7f7e", "7f7e"])));
    expect([c.pvLength, c.pvTruncatedAtPly, c.pvUsablePlies, c.comparedPlies]).toEqual([4, 4, 3, 3]);
  });

  it("F-12 分岐点が 1 手目でない: 王手の ply は記録の手数 [13, 15]。D1 の窓は足りない", () => {
    const c = compared(counterfactualOf(input(F12_ROOT, F2_ACTUAL, F1_PV, { prefix: F12_PREFIX })));
    expect(c.comparedPlies).toBe(5);
    expect(c.actual.checks).toEqual({ byUs: [13, 15], byOpponent: [] });
    expect(c.pvUsablePlies).toBe(5);
    expect(actualContinuation([...F12_PREFIX, ...F2_ACTUAL], 11, WINDOW, INIT)).toEqual({ checks: [], mate: null, windowPlies: 5, windowShort: true });
  });

  it("F-13 読み筋の 1 手目が根で非合法なら pvUnplayable(N = 0 の compared にしない)", () => {
    expect(counterfactualOf(input(INIT, F1_ACTUAL, ["7f7e"])).state).toBe("pvUnplayable");
  });

  it("F-15 窓の 6 手目に後手の王手: N = 6、実戦の byOpponent [6] は D1 の actualContinuation の checks [6] と一致する", () => {
    const moves = ["5i5h", "5a5b", "5h5i", "5b5a", "5i5h", "R*5c"];
    const c = compared(counterfactualOf(input(ROOK_ROOT, moves, [...moves])));
    expect(c.comparedPlies).toBe(6);
    expect(c.actual.checks.byOpponent).toEqual([6]);
    expect(actualContinuation(moves, 1, WINDOW, ROOK_ROOT).checks).toEqual([6]);
  });

  it("F-16 読み筋が詰みでない終局で終わる: N = 1、読み筋 詰み null・終局 1 手目 stalemate、実戦 どちらも null", () => {
    const c = compared(counterfactualOf(input(STALEMATE_ROOT, ["5i4h"], ["8d8c"])));
    expect(c.comparedPlies).toBe(1);
    expect([c.pv.mate, c.pv.gameEnd]).toEqual([null, { ply: 1, result: "stalemate" }]);
    expect([c.actual.mate, c.actual.gameEnd]).toEqual([null, null]);
  });

  it("S-1(監査 1e の任意): focus_baseline の multipv 2 が multipv 1 より前にあっても、multipv 1 の読み筋を使う", () => {
    const c = compared(counterfactualOf(input(INIT, F1_ACTUAL, { searchPvs: [focusBaseline(INIT, ["2g2f"], { multipv: 2 }), focusBaseline(INIT, F1_PV)] })));
    expect([c.pvFirstMove, c.pvLength, c.comparedPlies]).toEqual(["7g7f", 5, 5]);
  });

  it("S-2(監査 1e の任意): 後手の手で窓の中に詰む: N = 2、実戦 詰み 2 手目(後手の勝ち)・後手の手による王手 [2]・逃げ道 0、読み筋 詰みなし・逃げ道 2(差 +2)、根の逃げ道 4。D1 の consequences も同じ詰み", () => {
    const c = compared(counterfactualOf(input(GOTE_MATE_ROOT, ["1g1f", "G*5h"], ["5i4i", "G*5h"])));
    expect([c.comparedPlies, c.actualPlies, c.pvUsablePlies]).toEqual([2, 2, 2]);
    expect(d2Facts(c.actual)).toEqual({
      capturedRoles: { us: {}, opponent: {} },
      checks: { byUs: [], byOpponent: [2] },
      mate: { ply: 2, winner: "gote" },
      gameEnd: null,
      kingSurroundingsEnd: { squares: 5, own: 0 },
      kingEscapesEnd: { state: "counted", count: 0 },
    });
    expect(d2Facts(c.pv)).toEqual({
      capturedRoles: { us: {}, opponent: {} },
      checks: { byUs: [], byOpponent: [2] },
      mate: null,
      gameEnd: null,
      kingSurroundingsEnd: { squares: 5, own: 0 },
      kingEscapesEnd: { state: "counted", count: 2 },
    });
    expect(d2Diff(c.pvMinusActual)).toEqual({ capturedRoles: { us: {}, opponent: {} }, kingSurroundingsOwn: 0, kingEscapes: 2 });
    expect(c.kingEscapesRoot).toEqual({ state: "counted", count: 4 });
    expect(c.kingEscapesChangeFromRoot).toEqual({ actual: -4, pv: -2 });
    expect(actualContinuation(["1g1f", "G*5h"], 1, WINDOW, GOTE_MATE_ROOT)).toMatchObject({ checks: [2], mate: 2 });
  });

  it("S-3(監査 1e の任意): 玉の周りの差が 0 でない: N = 1、周り 実戦 0 / 5・読み筋 1 / 5(差 +1)、逃げ道 実戦 5・読み筋 4(差 −1)、1 手目は実戦の手と違う", () => {
    const c = compared(counterfactualOf(input(GOLD_ROOT, ["5h4g"], ["5h4h"])));
    expect(c.comparedPlies).toBe(1);
    expect([c.actual.kingSurroundingsEnd, c.pv.kingSurroundingsEnd]).toEqual([
      { squares: 5, own: 0 },
      { squares: 5, own: 1 },
    ]);
    expect([c.actual.kingEscapesEnd, c.pv.kingEscapesEnd]).toEqual([
      { state: "counted", count: 5 },
      { state: "counted", count: 4 },
    ]);
    expect(d2Diff(c.pvMinusActual)).toEqual({ capturedRoles: { us: {}, opponent: {} }, kingSurroundingsOwn: 1, kingEscapes: -1 });
    expect(c.kingEscapesRoot).toEqual({ state: "counted", count: 4 });
    expect(c.pvFirstMoveIsPlayedMove).toBe(false);
  });
});

describe("STEP D2 の境目", () => {
  it("上限は windowPlies + 1: 窓 4 なら F-15 の手順でも N = 5 で、6 手目の王手は数えない", () => {
    const moves = ["5i5h", "5a5b", "5h5i", "5b5a", "5i5h", "R*5c"];
    const c = compared(counterfactualOf(input(ROOK_ROOT, moves, [...moves], { windowPlies: 4 })));
    expect([c.comparedPlies, c.actualPlies]).toEqual([5, 5]);
    expect(c.actual.checks.byOpponent).toEqual([]);
  });

  it("先手玉の無い局面の逃げ道は noKing(0 にしない)", () => {
    expect(kingEscapesOf("4k4/9/9/9/9/9/9/9/9 b - 1")).toEqual({ state: "noKing" });
  });

  it("状態の判定の順: 実戦の根が合わない記録は、読み筋の欄が無くても actualRootMismatch", () => {
    const i = input(INIT, F1_ACTUAL, { searchPvs: undefined });
    expect(counterfactualOf({ ...i, record: { sfen: F12_ROOT } }).state).toBe("actualRootMismatch");
  });
});

// ---- 記録から(F-10・F-11・F-14)----

function rotatedKifu(id: string): { moves: string[]; startSfen: string } {
  const moves = (JSON.parse(readFileSync(new URL(`../kifu/${id}.json`, import.meta.url), "utf-8")) as { moves: string[] }).moves;
  const aligned = alignMovesToSente(moves, "gote");
  const startSfen = (aligned.alignment as { startSfen?: string }).startSfen;
  if (startSfen === undefined) throw new Error(`回した記録に startSfen が無い: ${id}`);
  return { moves: aligned.moves, startSfen };
}

/** ply 10 → 12 に −500 の急落を植え、ply 10 の行に実戦と同じ 6 手の読み筋を植える(分岐点 11) */
function droppedRotatedRecords(moves: string[], startSfen: string): RecordLine[] {
  const records = plantedRecords(moves, { 10: engineRef(500), 12: engineRef(0) }, {}, startSfen);
  const row = records.find((record) => record.ply === 10)!;
  row.searchPvs = [focusBaseline(row.sfen, moves.slice(10, 16))];
  return records;
}

describe("STEP D2 の固定例(記録から。計画 3.)", () => {
  it("F-10 回した記録(claude-2): 開始局面から並べると actualRootMismatch にならず比べる。平手から並べると D1 が IllegalMoveError(D1 の今の振る舞い)", () => {
    const { moves, startSfen } = rotatedKifu("2026-09-12-live-30moves-claude-2");
    const records = droppedRotatedRecords(moves, startSfen);
    const event = diagnoseRecords("f-10", records, DRAFT_RULE_1, startSfen).events.find((e) => e.branchPly === 11);
    expect(event).toBeDefined();
    const c = compared(event!.counterfactual);
    expect([c.comparedPlies, c.pvFirstMoveIsPlayedMove]).toEqual([6, true]);
    expect(() => diagnoseRecords("f-10", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN)).toThrow(IllegalMoveError);
  });

  it("F-11 端から端まで: GAME01 の分岐点 49 に counterfactual が付き、N = 6 で実戦の byOpponent は D1 の consequences.checks と一致し、1 行は今の版のスキーマを通り、Markdown に 2 行", () => {
    const records = plantedRecords(GAME01_MOVES, {
      48: engineRef(500, { afterPassMate: 3, dropCp: 350, bestmove: "2h2g" }),
      50: engineRef(-300),
    });
    const row = records.find((record) => record.ply === 48)!;
    row.searchPvs = [focusBaseline(row.sfen, GAME01_MOVES.slice(48, 54))];
    const { events } = diagnoseRecords("game-01", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN);
    const event = events.find((e) => e.branchPly === 49)!;
    const c = compared(event.counterfactual);
    expect(c.comparedPlies).toBe(6);
    expect(c.actual.checks.byOpponent).toEqual(event.consequences.checks);
    expect(event.consequences.checks).toEqual([52, 54]);

    // F-11 の v0.4(STEP D2.5 で版は 0.5、STEP D-SCREEN-2 から版は定数で見る): toEventLine の 1 行(ファイルと同じ形)は counterfactual を consequences の後に持ち、今の版のスキーマを通る
    const provenance = buildProvenance({
      recordPath: "game-01.jsonl",
      recordSha256: "0".repeat(64),
      meta: undefined,
      evaluator: null,
      analysisGit: { gitHead: null, dirty: null },
      rule: DRAFT_RULE_1,
      notEvaluationCp: NOT_EVALUATION_CP,
      standingBounds: STANDING_BOUNDS,
      positionFactsRules: POSITION_FACTS_RULES,
      repoRoot: "/nonexistent-repo-root",
    });
    const line = JSON.parse(JSON.stringify(toEventLine(event, provenance))) as Record<string, unknown>;
    expect(line.schemaVersion).toBe(FAILURE_EVENT_SCHEMA_VERSION);
    expect(Object.keys(line).indexOf("counterfactual")).toBe(Object.keys(line).indexOf("consequences") + 1);
    expect(line.counterfactual).toEqual(JSON.parse(JSON.stringify(event.counterfactual)));
    expect(validateFailureEventLine(line, loadFailureEventSchema())).toEqual([]);

    const report = renderDiagnosisReport(buildDiagnosisReport([{ kifuId: "game-01", meta: undefined, records, errorLines: [] }], DRAFT_RULE_1));
    const lines = report.filter((line) => line.startsWith("- game-01 分岐点 49 "));
    expect(lines).toEqual(counterfactualLines("game-01", 49, event.counterfactual));
    expect(lines).toHaveLength(2);
    expect(lines[0]).toContain("実戦の続き(6 手 = 分岐の手 + 5 手)");
    expect(lines[1]).toContain("読み筋(③の探索・6 手 = 分岐の手 + 5 手・標識なし・1 手目は直前の bestmove と違う)");
  });

  it("F-14 実戦の根が合わない(claude-3 を回した記録を平手として読む): D1 は例外にならず、D2 は actualRootMismatch", () => {
    const { moves, startSfen } = rotatedKifu("2026-09-12-live-30moves-claude-3");
    const records = droppedRotatedRecords(moves, startSfen);
    const event = diagnoseRecords("f-14", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN).events.find((e) => e.branchPly === 11);
    expect(event).toBeDefined();
    expect(event!.counterfactual).toEqual({ state: "actualRootMismatch" });
  });
});

describe("STEP D2 の Markdown(計画 2.5)", () => {
  it("compared でない状態は 1 行で状態を書く", () => {
    expect(counterfactualLines("k", 7, { state: "unrecorded" })).toEqual(["- k 分岐点 7 読み筋: 記録に読み筋が無い(測っていない)"]);
  });

  it("S-4(監査 1e の任意): renderDiagnosisReport でも、compared でない Event(読み筋を植えない GAME01 の分岐点 49 = unrecorded)は節の中に 1 行", () => {
    const records = plantedRecords(GAME01_MOVES, { 48: engineRef(500, { afterPassMate: 3, dropCp: 350, bestmove: "2h2g" }), 50: engineRef(-300) });
    const report = renderDiagnosisReport(buildDiagnosisReport([{ kifuId: "game-01", meta: undefined, records, errorLines: [] }], DRAFT_RULE_1));
    const heading = report.indexOf("## 実戦の続きと読み筋(STEP D2。事実の並びだけ。読み筋は③の探索で、急落を見つけた評価とは別の探索)");
    expect(heading).toBeGreaterThan(-1);
    const expected = "- game-01 分岐点 49 読み筋: 記録に読み筋が無い(測っていない)";
    expect(report.filter((line) => line.startsWith("- game-01 分岐点 49 "))).toEqual([expected]);
    expect(report.indexOf(expected)).toBeGreaterThan(heading);
  });

  it("評価語を使わない(正解・悪手・最善・損・得・有利・不利・攻め急ぎ が行に出ない)", () => {
    const lines = [
      ...counterfactualLines("k", 1, counterfactualOf(input(INIT, F2_ACTUAL, F1_PV))),
      ...counterfactualLines("k", 1, counterfactualOf(input(MATE_ROOT, ["5i4h", "5a4a"], ["G*5b"]))),
    ];
    expect(lines).toHaveLength(4);
    for (const word of ["正解", "悪手", "最善", "損", "得", "有利", "不利", "攻め急ぎ"]) {
      expect(lines.join("\n")).not.toContain(word);
    }
  });
});

// ---- STEP D2.5(docs/STEP_D2.5_PLAN_2026-09-15.md §2・§4 の P-11・W-12)----
describe("STEP D2.5 の positionFactsEnd", () => {
  it("P-11: 実戦が 2 手で終わる記録(N = 2、読み筋は 3 手)では、actual・pv の positionFactsEnd は根から 2 手目の後の局面の値で、読み筋の最後(3 手目の後)ではない。差は手で数えた値", () => {
    // 根は先手の金 5h・先手玉 5i・後手玉 5a。実戦 5h4g 5a4a、読み筋 5h4h 5a4a 4h3g
    const c = compared(counterfactualOf(input(GOLD_ROOT, ["5h4g", "5a4a"], ["5h4h", "5a4a", "4h3g"])));
    expect([c.comparedPlies, c.actualPlies, c.pvUsablePlies]).toEqual([2, 2, 3]);
    const after = (moves: string[]) => moves.reduce((sfen, move) => applyMove(sfen, move), GOLD_ROOT);
    // 前提: 読み筋の 3 手目の後(金 3g)は、2 手目の後(金 4h)と値が違う(同じだと、切り損ねを見分けられない)
    expect(positionFactsOf(after(["5h4h", "5a4a", "4h3g"]), POSITION_FACTS_RULES)).not.toEqual(positionFactsOf(after(["5h4h", "5a4a"]), POSITION_FACTS_RULES));
    expect(c.actual.positionFactsEnd).toEqual(positionFactsOf(after(["5h4g", "5a4a"]), POSITION_FACTS_RULES));
    expect(c.pv.positionFactsEnd).toEqual(positionFactsOf(after(["5h4h", "5a4a"]), POSITION_FACTS_RULES));
    // 手で数えた値: 先手玉 5i の区域(4h・5h・6h・4i・5i・6i)に、実戦の金 4g は 4h だけ(駒 1・升 1)、読み筋の金 4h は 5h・4i(駒 1・升 2)。
    // 後手玉 4a の区域には、どちらの金も届かない。後手の駒は玉だけ
    expect(c.actual.positionFactsEnd.zoneControl.ownKingZone).toEqual({ bySente: 1, byGote: 0 });
    expect(c.pv.positionFactsEnd.zoneControl.ownKingZone).toEqual({ bySente: 2, byGote: 0 });
    expect(c.pvMinusActual.positionFacts).toEqual({
      zonePieces: { ownKingZone: { bySente: 0, byGote: 0 }, opponentKingZone: { bySente: 0, byGote: 0 } },
      zoneControl: { ownKingZone: { bySente: 1, byGote: 0 }, opponentKingZone: { bySente: 0, byGote: 0 } },
    });
    expect(c.pvMinusActual.positionFacts).toEqual(positionFactsDiff(c.pv.positionFactsEnd, c.actual.positionFactsEnd));
  });
});
