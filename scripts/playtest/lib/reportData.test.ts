// STEP PIPE 作業 B(docs/STEP_PIPE_PLAN_2026-09-21.md §2.2)。lib/reportData.ts の試験。
// 小さな作り物(GAME01_MOVES・alignMovesToSente)と、記録があるときだけ走る回帰(records/real-02・real-03)。
// 実棋譜の記録の中身(手・値・ply)は書かない(既知の集計値だけを比べる)。

import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { engineRef, GAME01_MOVES, plantedRecords } from "./failureEventFixtures.js";
import type { GateLine } from "./gateOutput.js";
import { loadConditionsFromDir } from "./conditionReport.js";
import { alignMovesToSente } from "./sideAlignment.js";
import { rotateUsiMove } from "./usiRotation.js";
import kingEscapesDefinition from "./conditions/king_escapes_decrease_v1.js";
import {
  assertNoForbiddenWords,
  buildAuditCandidatePhase,
  buildAuditPairs,
  buildPatientReportData,
  displayScoreOf,
  endingTextOf,
  formatPlayedMove,
  gameFactsOf,
  featuredGamesOf,
  moveCheckFromGateLines,
  originalMovesOf,
  phaseOf,
  plyOffsetOf,
  ReportDataError,
  resultOf,
  sideOf,
  testGamesCountOf,
  type FixedKifu,
  type GameSource,
  type PatientReportData,
} from "./reportData.js";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const CONDITIONS_DIR = path.join(ROOT, "scripts", "playtest", "lib", "conditions");

// ---- 小さな純粋関数 ----

describe("sideOf・plyOffsetOf", () => {
  it("mirrored が無い(先手のまま)なら先手・plyOffset 0", () => {
    expect(sideOf({ mirrored: undefined })).toBe("先手");
    expect(plyOffsetOf({ mirrored: undefined, plyOffset: undefined })).toBe(0);
  });
  it("mirrored が true(後手を回した)なら後手・plyOffset は meta の値(既定 1)", () => {
    expect(sideOf({ mirrored: true })).toBe("後手");
    expect(plyOffsetOf({ mirrored: true, plyOffset: 1 })).toBe(1);
    expect(plyOffsetOf({ mirrored: true, plyOffset: undefined })).toBe(1);
  });
});

describe("resultOf(構造的な事実。ending.kind ごとに決め方を変える)", () => {
  it("resign・mate・timeUp は、先手・奇数手 → 勝ち、先手・偶数手 → 負け", () => {
    expect(resultOf("先手", 41, { kind: "resign", ply: 42 }, "t")).toBe("勝ち");
    expect(resultOf("先手", 66, { kind: "mate", ply: 67 }, "t")).toBe("負け");
    expect(resultOf("先手", 41, { kind: "timeUp", ply: 42 }, "t")).toBe("勝ち");
  });
  it("resign・mate・timeUp は、後手・偶数手 → 勝ち、後手・奇数手 → 負け", () => {
    expect(resultOf("後手", 68, { kind: "resign", ply: 69 }, "t")).toBe("勝ち");
    expect(resultOf("後手", 65, { kind: "mate", ply: 66 }, "t")).toBe("負け");
  });
  it("illegalWin: ending.ply の手番の側の勝ち(語の意味どおり)", () => {
    // total=41(奇数) なら ending.ply=42(偶数、後手番)。illegalWin は後手の勝ち
    expect(resultOf("後手", 41, { kind: "illegalWin", ply: 42 }, "t")).toBe("勝ち");
    expect(resultOf("先手", 41, { kind: "illegalWin", ply: 42 }, "t")).toBe("負け");
  });
  it("illegalLoss: ending.ply の手番の側の負け(語の意味どおり)", () => {
    expect(resultOf("後手", 41, { kind: "illegalLoss", ply: 42 }, "t")).toBe("負け");
    expect(resultOf("先手", 41, { kind: "illegalLoss", ply: 42 }, "t")).toBe("勝ち");
  });
  it("この規則で決められない終局の種類は例外(偶奇で決めない)", () => {
    for (const kind of ["repetition", "impasse", "abort", "defaultWin", "defaultLoss", "enteringKingWin", "noMate", "unlisted"] as const) {
      expect(() => resultOf("先手", 41, { kind, ply: 42 }, "t")).toThrow(ReportDataError);
    }
    expect(() => resultOf("先手", 41, { kind: "unreadable", reason: "ply_mismatch", ply: null }, "t")).toThrow(ReportDataError);
  });
  it("ending が無い(null・undefined)固定棋譜は例外", () => {
    expect(() => resultOf("先手", 41, null, "t")).toThrow(ReportDataError);
    expect(() => resultOf("先手", 41, undefined, "t")).toThrow(ReportDataError);
  });
});

describe("endingTextOf", () => {
  it("ENDING_KIF_WORDS の語をそのまま返す", () => {
    expect(endingTextOf({ kind: "resign", ply: 10 })).toBe("投了");
    expect(endingTextOf({ kind: "timeUp", ply: 10 })).toBe("切れ負け");
    expect(endingTextOf({ kind: "mate", ply: 10 })).toBe("詰み");
  });
  it("unlisted・unreadable は null", () => {
    expect(endingTextOf({ kind: "unlisted", ply: 10 })).toBeNull();
    expect(endingTextOf({ kind: "unreadable", reason: "ply_mismatch", ply: null })).toBeNull();
  });
});

describe("displayScoreOf", () => {
  it("measured で scoreCp があればそれ", () => {
    expect(displayScoreOf({ state: "measured", scoreCp: 123, mate: null, bestmove: null, afterPassScoreCp: null, afterPassMate: null, dropCp: null })).toBe(123);
  });
  it("measured で scoreCp が無く mate があれば ±3000(mate の符号)", () => {
    expect(displayScoreOf({ state: "measured", scoreCp: null, mate: 5, bestmove: null, afterPassScoreCp: null, afterPassMate: null, dropCp: null })).toBe(3000);
    expect(displayScoreOf({ state: "measured", scoreCp: null, mate: -3, bestmove: null, afterPassScoreCp: null, afterPassMate: null, dropCp: null })).toBe(-3000);
  });
  it("measured でない・mate 0 は null", () => {
    expect(displayScoreOf({ state: "notMeasuredGameEnd" })).toBeNull();
    expect(displayScoreOf({ state: "measured", scoreCp: null, mate: 0, bestmove: null, afterPassScoreCp: null, afterPassMate: null, dropCp: null })).toBeNull();
  });
});

describe("phaseOf(局ごとの 1/3・2/3。境は late 側に含む)", () => {
  it("1/3 未満は early", () => {
    expect(phaseOf(10, 100)).toBe("early");
    expect(phaseOf(33, 100)).toBe("early"); // 33/100 = 0.33 < 1/3(0.333…)
  });
  it("1/3 以上・2/3 未満は mid", () => {
    expect(phaseOf(34, 100)).toBe("mid"); // 34/100 = 0.34 ≥ 1/3
    expect(phaseOf(65, 99)).toBe("mid"); // 65/99 = 0.6566… < 2/3
  });
  it("2/3 以上(ちょうども含む)は late", () => {
    expect(phaseOf(67, 100)).toBe("late"); // 67/100 = 0.67 ≥ 2/3
    expect(phaseOf(66, 99)).toBe("late"); // 66/99 = 2/3 ちょうど(境を含む)
  });
});

describe("testGamesCountOf", () => {
  it("sente<n>+gote<m> は n+m", () => expect(testGamesCountOf("sente6+gote4")).toBe(10));
  it("sente<n> だけなら n", () => expect(testGamesCountOf("sente6")).toBe(6));
});

describe("assertNoForbiddenWords", () => {
  const base: PatientReportData = {
    title: "t",
    person: "p",
    today: "2026-01-01",
    summary: { games: 1 },
    games: [],
    events: [],
    overview: { fell: 0, early: 0, mid: 0, late: 0, fromAhead: 0, fromAheadLoss: 0, moveCheck: null },
    escapeScenes: [],
  };
  it("開発用の語が無ければ通る", () => expect(() => assertNoForbiddenWords(base)).not.toThrow());
  it("開発用の語(例: sha)が入っていれば止まる", () => {
    expect(() => assertNoForbiddenWords({ ...base, title: "sha 付き" })).toThrow(ReportDataError);
  });
});

describe("moveCheckFromGateLines", () => {
  const gateLine = {
    condition: { id: "ahead_move_into_own_king_zone_v1" },
    gate: {
      items: [
        { item: "G-1", values: { gamesWithTrueDenominator: 6 }, threshold: {}, result: "met", reasons: [] },
        { item: "G-2", values: { trueDenominator: 10, trueCollapsed: 4 }, threshold: {}, result: "notMet", reasons: [] },
        { item: "G-4", values: { testTruePairsDenominator: 8, testTrueCollapsed: 0 }, threshold: {}, result: "notMet", reasons: [] },
      ],
    },
  } as unknown as GateLine;
  it("G-1・G-2・G-4 の値を n・fell・games・otherN・otherFell に写す", () => {
    expect(moveCheckFromGateLines([gateLine], "ahead_move_into_own_king_zone_v1")).toEqual({ n: 10, fell: 4, games: 6, otherN: 8, otherFell: 0 });
  });
  it("id が無ければ null", () => expect(moveCheckFromGateLines([gateLine], "no_such_id")).toBeNull());
  it("draft(items が無い gate)なら null", () => {
    const draftLine = { condition: { id: "x" }, gate: { notJudged: "draft" } } as unknown as GateLine;
    expect(moveCheckFromGateLines([draftLine], "x")).toBeNull();
  });
});

describe("formatPlayedMove(指した手の日本語表記。升番号つき)", () => {
  it("打つ手は常に「打」を添える", () => {
    expect(formatPlayedMove(DEFAULT_INITIAL_SFEN, "P*5e", null)).toBe("５五歩打");
  });
  it("盤上の手は升番号を必ず添える(あいまいさの表記は出さない)", () => {
    // 7g7f: 初形の 7 筋の歩を 1 つ進める
    expect(formatPlayedMove(DEFAULT_INITIAL_SFEN, "7g7f", null)).toBe("７六歩(77)");
  });
  it("直前の手と同じ升なら「同」", () => {
    expect(formatPlayedMove(DEFAULT_INITIAL_SFEN, "7g7f", "7f")).toBe("同歩(77)");
  });
});

// ---- 小さな作り物での組み立て(GAME01_MOVES。先手) ----

function fixedKifuOf(id: string, ending: FixedKifu["ending"], moves: readonly string[]): FixedKifu {
  return { id, ending, moves };
}

describe("buildPatientReportData(先手の作り物。GAME01_MOVES 56 手・56 手目で後手の勝ちの詰み)", () => {
  // lib/failureEvent.test.ts の F-1 と同じ植え方: 分岐点 49 に急落 1 件
  const records: RecordLine[] = plantedRecords(GAME01_MOVES, {
    48: engineRef(500, { afterPassMate: 3, dropCp: 350, bestmove: "2h2g" }),
    50: engineRef(-300),
  });
  const meta = { kind: "meta", kifuId: "test-01", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine;
  const source: GameSource = { kifuId: "test-01", meta, records, fixed: fixedKifuOf("test-01", { kind: "mate", ply: 56 }, GAME01_MOVES) };

  it("originalMovesOf は moves をそのまま返す(originalMoves が無い先手の局)", () => {
    expect(originalMovesOf(source.fixed)).toBe(GAME01_MOVES);
  });

  const patient = buildPatientReportData([source], [], kingEscapesDefinition, {
    title: "t",
    person: "p",
    today: "2026-01-01",
    kingEscapesConditionId: "king_escapes_decrease_v1",
    moveCheckConditionId: "ahead_move_into_own_king_zone_v1",
  });

  it("games: 1 局・先手・56 手・後手の勝ち(先手負け)・詰み", () => {
    expect(patient.games).toHaveLength(1);
    expect(patient.games[0]).toMatchObject({ no: 1, id: "test-01", side: "先手", total: 56, result: "負け", ending: "詰み" });
  });

  it("events: 分岐点 49(ply)に drop 種が 1 件、実際の手(playedUsi)は GAME01_MOVES[48]", () => {
    // 56 手目が後手の勝ちの詰みなので、49 の drop のほかに終盤の matedIfPass 種が出ることがある(件数は決め打ちしない)
    const at49 = patient.events.find((event) => event.ply === 49);
    expect(at49).toMatchObject({ gameNo: 1, kind: "drop", before: 500, after: -300, playedUsi: GAME01_MOVES[48], bestUsi: "2h2g", sameBest: false });
    expect(at49!.played).not.toBeNull();
  });

  it("本人向けの側に開発用の語が無い(assertNoForbiddenWords が通る)", () => {
    expect(() => assertNoForbiddenWords(patient)).not.toThrow();
  });
});

// ---- 小さな作り物での組み立て(後手。alignMovesToSente で回した局) ----

describe("buildPatientReportData(後手の作り物。180 度回した組を本人が指した向きへ戻す)", () => {
  const originalMoves = GAME01_MOVES.slice(0, 10);
  const aligned = alignMovesToSente(originalMoves, "gote");
  const rotatedMoves = aligned.moves;
  const startSfen = aligned.alignment.mirrored ? aligned.alignment.startSfen : DEFAULT_INITIAL_SFEN;
  // 分岐点(fixed の branchPly 1)に急落を 1 件植える。displayPly = 1 + plyOffset(1) = 2
  const records: RecordLine[] = plantedRecords(rotatedMoves, { 0: engineRef(500, { bestmove: "2h2g" }), 2: engineRef(-300) }, {}, startSfen);
  const meta = {
    kind: "meta",
    kifuId: "test-02",
    startedAt: "",
    gitHead: null,
    enginePath: "",
    mirrored: true,
    startSfen,
    plyOffset: 1,
    originalUserSide: "gote",
  } as unknown as MetaLine;
  const source: GameSource = {
    kifuId: "test-02",
    meta,
    records,
    fixed: { id: "test-02", ending: { kind: "resign", ply: originalMoves.length + 1 }, moves: rotatedMoves, originalMoves, mirrored: true },
  };

  it("originalMovesOf は originalMoves を返す(moves ではなく)", () => {
    expect(originalMovesOf(source.fixed)).toBe(originalMoves);
  });

  const patient = buildPatientReportData([source], [], kingEscapesDefinition, {
    title: "t",
    person: "p",
    today: "2026-01-01",
    kingEscapesConditionId: "king_escapes_decrease_v1",
    moveCheckConditionId: "ahead_move_into_own_king_zone_v1",
  });

  it("side は後手、total は本人が指した向きの手数(originalMoves.length)", () => {
    expect(patient.games[0]).toMatchObject({ side: "後手", total: originalMoves.length });
  });

  it("events の playedUsi・bestUsi は、記録の向き(本人 = 先手に回した)から本人が指した向きへ 180 度戻した USI", () => {
    const event = patient.events.find((candidate) => candidate.ply === 2);
    expect(event).toBeDefined();
    // 実際に指した手(本人が指した向き)は originalMoves[1](displayPly 2 の 1 つ前のインデックス)そのもの
    expect(event!.playedUsi).toBe(originalMoves[1]);
    // bestmove は記録の向き(先手に回した)の "2h2g" を植えたので、本人が指した向きへ戻すと 180 度回した値になる
    expect(event!.bestUsi).toBe(rotateUsiMove("2h2g"));
  });
});

// ---- 記録があるときだけ走る回帰(2 人目 20 局。既知の集計値だけを比べる。手・値・ply は書かない) ----

const REAL02_DIR = path.join(ROOT, "scripts", "playtest", "records", "real-02");
const REAL03_DIR = path.join(ROOT, "scripts", "playtest", "records", "real-03");
const GATE_PATH = path.join(ROOT, "scripts", "playtest", "records", "gate", "p2.jsonl");
const hasRealRecords = existsSync(REAL02_DIR) && existsSync(REAL03_DIR) && existsSync(GATE_PATH);

function readJsonl(filePath: string): Array<Record<string, unknown>> {
  return readFileSync(filePath, "utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
}

function readRealSource(recordsPath: string, kifuDir: string): GameSource {
  const lines = readJsonl(recordsPath);
  const meta = lines.find((line) => line["kind"] === "meta") as unknown as MetaLine;
  const recs = lines.filter((line) => line["kind"] === "record") as unknown as RecordLine[];
  const fixed = JSON.parse(readFileSync(path.join(kifuDir, `${meta.kifuId}.fixed.json`), "utf-8")) as FixedKifu;
  return { kifuId: meta.kifuId, meta, records: recs, fixed };
}

describe.runIf(hasRealRecords)("回帰: 2 人目 20 局(既知の集計値。STEP PIPE 作業 B の報告と同じ値)", () => {
  it(
    "patient_report_data.json と audit の pairs が、金の標本と突き合わせて確かめた値と一致する",
    async () => {
      const p2Ids02 = ["01", "04", "09", "11", "15", "16", "17", "18", "20"].map((n) => `kifu2-${n}`);
      const p2Ids03 = ["02", "03", "05", "06", "07", "08", "10", "12", "13", "14", "19"].map((n) => `kifu2-${n}`);
      const sources = [
        ...p2Ids02.map((id) => readRealSource(path.join(REAL02_DIR, `${id}.jsonl`), path.join(REAL02_DIR, "kifu"))),
        ...p2Ids03.map((id) => readRealSource(path.join(REAL03_DIR, `${id}.jsonl`), path.join(REAL03_DIR, "kifu"))),
      ];
      const gateLines = readJsonl(GATE_PATH) as unknown as GateLine[];
      const conditions = await loadConditionsFromDir(CONDITIONS_DIR);
      const kingEscapes = conditions.find((loaded) => loaded.definition.id === "king_escapes_decrease_v1")!;

      const patient = buildPatientReportData(sources, gateLines, kingEscapes.definition, {
        title: "t",
        person: "p",
        today: "2026-01-01",
        kingEscapesConditionId: "king_escapes_decrease_v1",
        moveCheckConditionId: "ahead_move_into_own_king_zone_v1",
      });

      expect(patient.games).toHaveLength(20);
      expect(patient.events).toHaveLength(39);
      expect(patient.escapeScenes).toHaveLength(8);
      expect(patient.overview).toMatchObject({ fell: 32, early: 2, mid: 14, late: 16, fromAhead: 14, fromAheadLoss: 10 });
      expect(patient.overview.moveCheck).toEqual({ n: 10, fell: 4, games: 6, otherN: 8, otherFell: 0 });
      // games[].events・marks(drop 種だけを数える。matedIfPass だけで当たった Failure Event は入れない)
      const kifu2_08 = patient.games.find((game) => game.id === "kifu2-08")!;
      expect(kifu2_08.events).toBe(6);
      expect(kifu2_08.marks).toEqual([30, 31, 37, 41, 42, 44]);
      const totalMarks = patient.games.reduce((sum, game) => sum + game.marks.length, 0);
      expect(totalMarks).toBe(29);
      const { buildGames } = await import("./reportData.js");
      const built = buildGames(sources);
      const pairs = buildAuditPairs(built, null, conditions.length);
      expect(pairs).toMatchObject({ total: 734, fell: 32, den: 604, aheadToLevel: 11, levelToBehind: 18, aheadToBehind: 3, behindExcluded: 77, beforeUndet: 30, afterUndet: 23, gamesWithFall: 17, games: 20 });
      expect(pairs.fromAhead).toEqual([14, 170]);
      expect(pairs.fromLevel).toEqual([18, 434]);
      expect(pairs.win5).toEqual([69, 597]);

      const phase = buildAuditCandidatePhase(patient.overview, patient.events, patient.games);
      expect(phase).toEqual({ early: 2, mid: 14, late: 16, fromAhead: 14, fromAheadLoss: 10, dropEarly: 0, dropMid: 9, dropLate: 20 });

      // S6: 1 局ずつ載せる局の選び方(la = 優勢から負けた局、wb = 劣勢から勝った局のうち下がり幅の大きい順に 3 局)
      const factsByNo = new Map(patient.games.map((game) => [game.no, gameFactsOf(game)]));
      const featured = featuredGamesOf(patient.games, factsByNo);
      expect(featured.winsFromBehindTop3.length).toBeLessThanOrEqual(3);
      expect(featured.lossesFromAhead.every((game) => game.result === "負け")).toBe(true);
      expect(featured.winsFromBehindTop3.every((game) => game.result === "勝ち")).toBe(true);
    },
    120_000,
  );
});
