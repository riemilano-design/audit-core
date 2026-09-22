// STEP WHATIF 作業 2(docs/STEP_WHATIF_PLAN_2026-09-22.md §2.3・§7.3)。lib/whatifReport.ts の単体試験。
// **エンジンは起動しない**(whatif.jsonl は合成データを直接組み立てる)。

import { describe, expect, it } from "vitest";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import {
  afterCandidateOf,
  buildGameReport,
  buildRepresentative,
  buildSummary,
  buildWhatifReportData,
  parseWhatifJsonl,
  pickRepresentativePly,
  WhatifReportError,
  type PatientGameLike,
  type WhatifCandidateOut,
  type WhatifPositionRow,
  type WhatifSceneRow,
  type WhatifSummaryRow,
} from "./whatifReport.js";
import type { WhatifCandidate, WhatifMoveTags } from "./whatif.js";

const INIT = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
const NO_TAGS: WhatifMoveTags = { oppKingZone: false, ownKingZone: false, givesCheck: false, kingMove: false };

function candidate(move: string, scoreCp: number | null, pv: readonly string[] = [move], mate: number | null = null): WhatifCandidate {
  return { move, scoreCp, mate, pv: [...pv], tags: NO_TAGS, side: "none" };
}

/** 最小の position 行(このファイルの試験が使う欄だけ正しく埋める)。 */
function positionRow(overrides: Partial<WhatifPositionRow> & { ply: number }): WhatifPositionRow {
  return {
    kind: "position",
    ply: overrides.ply,
    displayPly: overrides.displayPly ?? overrides.ply,
    sfen: overrides.sfen ?? INIT,
    candidates: overrides.candidates ?? [candidate("7g7f", 50)],
    actualMove: overrides.actualMove ?? "7g7f",
    actualTags: NO_TAGS,
    actualSide: "none",
    actualRank: overrides.actualRank ?? 1,
    topGapCp: overrides.topGapCp ?? null,
    loss: overrides.loss ?? null,
    scenes: overrides.scenes ?? { fork: false, narrowHeld: false, chanceHeld: false },
    candidate0Value: overrides.candidate0Value ?? 50,
  };
}

function summaryRow(overrides: Partial<WhatifSummaryRow> = {}): WhatifSummaryRow {
  return {
    kind: "summary",
    positionsRead: overrides.positionsRead ?? 0,
    matchesTop1: overrides.matchesTop1 ?? 0,
    withinMultiPv: overrides.withinMultiPv ?? 0,
    biggestFork: overrides.biggestFork ?? null,
    scenes: overrides.scenes ?? { fork: [], narrowHeld: [], chanceHeld: [] },
    sceneReads: overrides.sceneReads ?? { scenesRead: 0, attackNoLegalMoveCount: 0, defenseNoLegalMoveCount: 0, bothFoundCount: 0 },
    timingMs: overrides.timingMs ?? { pass1: 0, pass2: 0 },
  };
}

// ---- pickRepresentativePly(4 つの分岐) ----

describe("pickRepresentativePly", () => {
  it("負けた局: summary.biggestFork の局面(kind=fork)", () => {
    const summary = summaryRow({ biggestFork: { ply: 41, displayPly: 41, lossValue: 300, lossCp: 300, lossIsLowerBound: false } });
    expect(pickRepresentativePly("負け", [], summary)).toStrictEqual({ kind: "fork", ply: 41 });
  });

  it("負けた局: biggestFork が無ければ null(載せる局面なし)", () => {
    expect(pickRepresentativePly("負け", [], summaryRow())).toBeNull();
  });

  it("勝った局: narrowHeld があれば topGapCp が最大の局面(同点は早い手数)", () => {
    const positions = [
      positionRow({ ply: 21, topGapCp: 400, scenes: { fork: false, narrowHeld: true, chanceHeld: false } }),
      positionRow({ ply: 25, topGapCp: 600, scenes: { fork: false, narrowHeld: true, chanceHeld: false } }),
      positionRow({ ply: 29, topGapCp: 600, scenes: { fork: false, narrowHeld: true, chanceHeld: false } }), // 同点 → 早い手数(25)のまま変わらない
    ];
    expect(pickRepresentativePly("勝ち", positions, summaryRow())).toStrictEqual({ kind: "narrowHeld", ply: 25 });
  });

  it("勝った局: narrowHeld が無く chanceHeld があれば最初(最も早い手数)", () => {
    const positions = [
      positionRow({ ply: 31, scenes: { fork: false, narrowHeld: false, chanceHeld: true } }),
      positionRow({ ply: 35, scenes: { fork: false, narrowHeld: false, chanceHeld: true } }),
    ];
    expect(pickRepresentativePly("勝ち", positions, summaryRow())).toStrictEqual({ kind: "chanceHeld", ply: 31 });
  });

  it("勝った局: narrowHeld も chanceHeld も無ければ biggestFork(fork の最大)", () => {
    const summary = summaryRow({ biggestFork: { ply: 55, displayPly: 55, lossValue: 200, lossCp: 200, lossIsLowerBound: false } });
    expect(pickRepresentativePly("勝ち", [], summary)).toStrictEqual({ kind: "fork", ply: 55 });
  });

  it("勝った局: narrowHeld・chanceHeld・biggestFork のどれも無ければ null(載せる局面なし)", () => {
    expect(pickRepresentativePly("勝ち", [], summaryRow())).toBeNull();
  });
});

// ---- afterCandidateOf・buildRepresentative(5 手進めた局面。実際に applyMove する) ----

describe("afterCandidateOf", () => {
  const pv = ["7g7f", "3c3d", "2g2f", "8c8d", "2f2e", "8d8e"]; // 6 手(5 手だけ適用する)

  it("実戦が第 1 候補と違う: 第 1 候補(index 0)の pv を 5 手適用する", () => {
    const position = positionRow({ ply: 17, candidates: [candidate("7g7f", 60, pv), candidate("2g2f", 40)], actualMove: "2g2f" });
    const after = afterCandidateOf(position);
    expect(after).not.toBeNull();
    expect(after!.candidateIndex).toBe(0);
    expect(after!.movesApplied).toBe(5);
    expect(after!.lastMoveUsi).toBe("2f2e");
    let expected = INIT;
    for (const usi of pv.slice(0, 5)) expected = applyMove(expected, usi);
    expect(after!.sfenAfter).toBe(expected);
  });

  it("実戦 = 第 1 候補: 第 2 候補(index 1)の pv を使う", () => {
    const pv2 = ["2g2f", "8c8d", "2f2e", "8d8e", "2e2d", "8e8f"]; // 第 1 候補と別の、それ自体で合法な手順
    const position = positionRow({ ply: 17, candidates: [candidate("7g7f", 60, ["7g7f"]), candidate("2g2f", 40, pv2)], actualMove: "7g7f" });
    const after = afterCandidateOf(position);
    expect(after).not.toBeNull();
    expect(after!.candidateIndex).toBe(1);
    expect(after!.move).toBe("2g2f");
  });

  it("実戦 = 第 1 候補で、第 2 候補が無ければ null", () => {
    const position = positionRow({ ply: 17, candidates: [candidate("7g7f", 60)], actualMove: "7g7f" });
    expect(afterCandidateOf(position)).toBeNull();
  });

  it("候補の pv が空なら null", () => {
    const position = positionRow({ ply: 17, candidates: [candidate("7g7f", 60, []), candidate("2g2f", 40)], actualMove: "2g2f" });
    expect(afterCandidateOf(position)).toBeNull();
  });
});

describe("buildRepresentative", () => {
  it("scene が無いプレイでも組める(scene: null)", () => {
    const position = positionRow({ ply: 17, candidates: [candidate("7g7f", 60, ["7g7f", "3c3d"]), candidate("2g2f", 40)], actualMove: "2g2f", actualRank: 2 });
    const rep = buildRepresentative({ kind: "fork", ply: 17 }, [position], new Map());
    expect(rep.scene).toBeNull();
    expect(rep.actual).toStrictEqual({ found: true, scoreCp: 40, mate: null });
    expect(rep.candidates).toHaveLength(2);
  });

  it("実戦の手が候補に無ければ actual.found=false", () => {
    const position = positionRow({ ply: 17, candidates: [candidate("7g7f", 60)], actualMove: "9g9f", actualRank: null });
    const rep = buildRepresentative({ kind: "fork", ply: 17 }, [position], new Map());
    expect(rep.actual).toStrictEqual({ found: false, scoreCp: null, mate: null });
  });

  it("scene がある場面は attack/defense/sideGapCp をそのまま渡す", () => {
    const position = positionRow({ ply: 23 });
    const scene: WhatifSceneRow = {
      kind: "scene",
      ply: 23,
      displayPly: 23,
      attack: { state: "found", result: { move: "5e5d", scoreCp: 100, mate: null, pv: ["5e5d"] } },
      defense: { state: "noLegalMove" },
      sideGapCp: null,
    };
    const rep = buildRepresentative({ kind: "fork", ply: 23 }, [position], new Map([[23, scene]]));
    expect(rep.scene).toStrictEqual({
      attack: { state: "found", move: "5e5d", scoreCp: 100, mate: null, pv: ["5e5d"] },
      defense: { state: "noLegalMove" },
      sideGapCp: null,
    });
  });

  it("pick の ply の局面が無ければ止める", () => {
    expect(() => buildRepresentative({ kind: "fork", ply: 999 }, [], new Map())).toThrow(WhatifReportError);
  });

  it("候補は上位 3 つに切り詰める", () => {
    const position = positionRow({
      ply: 17,
      candidates: [candidate("a", 1, []), candidate("b", 2, []), candidate("c", 3, []), candidate("d", 4, []), candidate("e", 5, [])],
      actualMove: "a",
    });
    const rep = buildRepresentative({ kind: "fork", ply: 17 }, [position], new Map());
    expect(rep.candidates.map((c: WhatifCandidateOut) => c.move)).toStrictEqual(["a", "b", "c"]);
  });
});

// ---- buildSummary(延べ・重なりを除いた数・lossesWithNarrowHeld) ----

describe("buildSummary", () => {
  it("延べ数と重なりを除いた数(1 局面が複数種類に当たる場合を二重に数えない)", () => {
    const games = [
      buildGameReportForSummaryTest("負け"),
      buildGameReportForSummaryTest("負け"),
    ];
    const summaries = [
      summaryRow({ positionsRead: 10, matchesTop1: 4, withinMultiPv: 8, scenes: { fork: [21, 25], narrowHeld: [25], chanceHeld: [] } }), // 21,25 の集合={21,25} → distinct 2
      summaryRow({ positionsRead: 5, matchesTop1: 2, withinMultiPv: 3, scenes: { fork: [31], narrowHeld: [], chanceHeld: [31] } }), // {31} → distinct 1
    ];
    const summary = buildSummary(games, summaries);
    expect(summary.positionsRead).toBe(15);
    expect(summary.matchesTop1).toBe(6);
    expect(summary.withinMultiPv).toBe(11);
    expect(summary.scenes).toStrictEqual({ fork: 3, narrowHeld: 1, chanceHeld: 1, rawTotal: 5, distinctTotal: 3 });
  });

  it("sideCompare は sceneReads をそのまま足す", () => {
    const games = [buildGameReportForSummaryTest("勝ち")];
    const summaries = [summaryRow({ sceneReads: { scenesRead: 4, attackNoLegalMoveCount: 1, defenseNoLegalMoveCount: 0, bothFoundCount: 3 } })];
    expect(buildSummary(games, summaries).sideCompare).toStrictEqual({ scenesRead: 4, bothFound: 3, attackNoLegalMove: 1, defenseNoLegalMove: 0 });
  });

  it("lossesWithNarrowHeld: 負けた局のうち narrowHeld が 1 件以上ある局の数 / 負けた局の総数", () => {
    const games = [buildGameReportForSummaryTest("負け"), buildGameReportForSummaryTest("負け"), buildGameReportForSummaryTest("勝ち")];
    const summaries = [
      summaryRow({ scenes: { fork: [], narrowHeld: [21], chanceHeld: [] } }), // 負け・narrowHeld あり
      summaryRow({ scenes: { fork: [], narrowHeld: [], chanceHeld: [] } }), // 負け・narrowHeld なし
      summaryRow({ scenes: { fork: [], narrowHeld: [31], chanceHeld: [] } }), // 勝ち(数えない)
    ];
    expect(buildSummary(games, summaries).lossesWithNarrowHeld).toStrictEqual({ withNarrow: 1, lossesTotal: 2 });
  });

  it("games と summaries の数が違えば止める", () => {
    expect(() => buildSummary([buildGameReportForSummaryTest("勝ち")], [])).toThrow(WhatifReportError);
  });
});

function buildGameReportForSummaryTest(result: "勝ち" | "負け") {
  return { gameNo: 1, id: "g", side: "先手" as const, result, total: 10, ending: null, plyOffset: 0, scores: [], plies: [], positionsRead: 0, matchesTop1: 0, withinMultiPv: 0, representative: null };
}

// ---- parseWhatifJsonl・buildGameReport・buildWhatifReportData(結合、mirrored の手数・名前/パスなし) ----

const DEFAULT_META_VALUES = { multiPv: 5, nodes: 1_000_000, sideZoneRadius: 2, startPly: 17, minLossCp: 600, narrowGapCp: 400, riseCp: 400 };
/** buildWhatifReportData が出す values(WhatifReportValues)の欄だけ(DEFAULT_META_VALUES から multiPv・nodes を除いたもの)。 */
const DEFAULT_META_VALUES_SUBSET = { sideZoneRadius: 2, startPly: 17, minLossCp: 600, narrowGapCp: 400, riseCp: 400 };

function metaLine(kifuId: string, valuesOverrides: Record<string, number> = {}, extra: Record<string, unknown> = {}): string {
  return JSON.stringify({ kind: "meta", kifuId, values: { ...DEFAULT_META_VALUES, ...valuesOverrides }, threads: 1, ...extra });
}

function makeJsonl(
  kifuId: string,
  positions: WhatifPositionRow[],
  scenes: WhatifSceneRow[],
  summary: WhatifSummaryRow,
  valuesOverrides: Record<string, number> = {},
  extra: Record<string, unknown> = {},
): string {
  const lines = [metaLine(kifuId, valuesOverrides, extra), ...positions.map((p) => JSON.stringify(p)), ...scenes.map((s) => JSON.stringify(s)), JSON.stringify(summary)];
  return `${lines.join("\n")}\n`;
}

describe("parseWhatifJsonl", () => {
  it("meta・position・scene・summary をそれぞれ振り分ける", () => {
    const jsonl = makeJsonl("g1", [positionRow({ ply: 17 })], [], summaryRow({ positionsRead: 1 }));
    const parsed = parseWhatifJsonl(jsonl);
    expect(parsed.meta.kifuId).toBe("g1");
    expect(parsed.positions).toHaveLength(1);
    expect(parsed.summary.positionsRead).toBe(1);
  });

  it("meta 行が無ければ止める", () => {
    expect(() => parseWhatifJsonl(`${JSON.stringify(summaryRow())}\n`)).toThrow(WhatifReportError);
  });

  it("summary 行が無ければ止める", () => {
    expect(() => parseWhatifJsonl(`${metaLine("g1")}\n`)).toThrow(WhatifReportError);
  });
});

/** buildGameReport は meta.values の中身を読まない(buildWhatifReportData だけが読む)ので、試験用の最小の meta。 */
function metaFor(kifuId: string): { kind: "meta"; kifuId: string; values: typeof DEFAULT_META_VALUES } {
  return { kind: "meta", kifuId, values: DEFAULT_META_VALUES };
}

describe("buildGameReport: mirrored の局の手数(displayPly)", () => {
  it("後手の局(plyOffset=1)は plies に +1 しない(scores/plies は patient から渡されたまま。plyOffset だけ持つ)", () => {
    const patient: PatientGameLike = { id: "g1", side: "後手", total: 40, result: "勝ち", ending: "投了", scores: [10, -20], plies: [1, 3] };
    const parsed = { meta: metaFor("g1"), positions: [], scenes: [], summary: summaryRow() };
    const game = buildGameReport(1, patient, parsed);
    expect(game.plyOffset).toBe(1);
    expect(game.plies).toStrictEqual([1, 3]);
  });

  it("先手の局は plyOffset=0", () => {
    const patient: PatientGameLike = { id: "g1", side: "先手", total: 40, result: "勝ち", ending: "投了", scores: [], plies: [] };
    const parsed = { meta: metaFor("g1"), positions: [], scenes: [], summary: summaryRow() };
    expect(buildGameReport(1, patient, parsed).plyOffset).toBe(0);
  });

  it("representative の displayPly は position 行の displayPly をそのまま使う(このファイルは回し直さない)", () => {
    const position = positionRow({ ply: 79, displayPly: 80, candidates: [candidate("7g7f", 60)], actualMove: "7g7f" });
    const summary = summaryRow({ biggestFork: { ply: 79, displayPly: 80, lossValue: 300, lossCp: 300, lossIsLowerBound: false } });
    const patient: PatientGameLike = { id: "g1", side: "後手", total: 100, result: "負け", ending: "投了", scores: [], plies: [] };
    const parsed = { meta: metaFor("g1"), positions: [position], scenes: [], summary };
    const game = buildGameReport(1, patient, parsed);
    expect(game.representative!.ply).toBe(79);
    expect(game.representative!.displayPly).toBe(80);
  });

  it("patient.id と meta.kifuId が違えば止める", () => {
    const patient: PatientGameLike = { id: "g1", side: "先手", total: 1, result: "勝ち", ending: null, scores: [], plies: [] };
    const parsed = { meta: metaFor("g2"), positions: [], scenes: [], summary: summaryRow() };
    expect(() => buildGameReport(1, patient, parsed)).toThrow(WhatifReportError);
  });
});

describe("buildWhatifReportData: 名前・パスを含まない", () => {
  it("JSON 化した結果に /Users/ を含まない", () => {
    const jsonl = makeJsonl("g1", [], [], summaryRow({ positionsRead: 1, matchesTop1: 1, withinMultiPv: 1 }));
    const patient: PatientGameLike = { id: "g1", side: "先手", total: 10, result: "勝ち", ending: "投了", scores: [1], plies: [1] };
    const report = buildWhatifReportData([{ id: "g1", jsonl, patient }]);
    const blob = JSON.stringify(report);
    expect(blob).not.toContain("/Users/");
    expect(report.values).toStrictEqual(DEFAULT_META_VALUES_SUBSET);
    expect(report.gamesCount).toBe(1);
  });

  it("局は kifuId の昇順に並ぶ", () => {
    const jsonlB = makeJsonl("gB", [], [], summaryRow());
    const jsonlA = makeJsonl("gA", [], [], summaryRow());
    const patientA: PatientGameLike = { id: "gA", side: "先手", total: 1, result: "勝ち", ending: null, scores: [], plies: [] };
    const patientB: PatientGameLike = { id: "gB", side: "先手", total: 1, result: "勝ち", ending: null, scores: [], plies: [] };
    const report = buildWhatifReportData([
      { id: "gB", jsonl: jsonlB, patient: patientB },
      { id: "gA", jsonl: jsonlA, patient: patientA },
    ]);
    expect(report.games.map((g) => g.id)).toStrictEqual(["gA", "gB"]);
    expect(report.games.map((g) => g.gameNo)).toStrictEqual([1, 2]);
  });

  it("sideZoneRadius が局によって違えば止める", () => {
    const jsonlA = makeJsonl("gA", [], [], summaryRow());
    const jsonlB = makeJsonl("gB", [], [], summaryRow(), { sideZoneRadius: 3 });
    const patientA: PatientGameLike = { id: "gA", side: "先手", total: 1, result: "勝ち", ending: null, scores: [], plies: [] };
    const patientB: PatientGameLike = { id: "gB", side: "先手", total: 1, result: "勝ち", ending: null, scores: [], plies: [] };
    expect(() =>
      buildWhatifReportData([
        { id: "gA", jsonl: jsonlA, patient: patientA },
        { id: "gB", jsonl: jsonlB, patient: patientB },
      ]),
    ).toThrow(WhatifReportError);
  });

  it("startPly・minLossCp・narrowGapCp・riseCp のどれかが局によって違っても止める", () => {
    const jsonlA = makeJsonl("gA", [], [], summaryRow());
    const jsonlB = makeJsonl("gB", [], [], summaryRow(), { riseCp: 300 });
    const patientA: PatientGameLike = { id: "gA", side: "先手", total: 1, result: "勝ち", ending: null, scores: [], plies: [] };
    const patientB: PatientGameLike = { id: "gB", side: "先手", total: 1, result: "勝ち", ending: null, scores: [], plies: [] };
    expect(() =>
      buildWhatifReportData([
        { id: "gA", jsonl: jsonlA, patient: patientA },
        { id: "gB", jsonl: jsonlB, patient: patientB },
      ]),
    ).toThrow(WhatifReportError);
  });

  it("入力が 0 局なら止める", () => {
    expect(() => buildWhatifReportData([])).toThrow(WhatifReportError);
  });
});
