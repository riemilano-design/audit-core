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
  buildFindings,
  buildGames,
  buildPatientGames,
  buildPatientReportData,
  buildPatientTime,
  buildPrevious,
  displayScoreOf,
  endingTextOf,
  FINDING_VALUES,
  formatPlayedMove,
  gameFactsOf,
  featuredGamesOf,
  leftBucketIndexOf,
  moveCheckFromGateLines,
  originalMovesOf,
  phaseOf,
  plyOffsetOf,
  ReportDataError,
  resultOf,
  sideOf,
  spentBucketIndexOf,
  testGamesCountOf,
  type Finding,
  type FixedKifu,
  type GameSource,
  type PatientGame,
  type PatientOverview,
  type PatientReportData,
  type PatientTime,
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
    // STEP TIME: PatientReportData に time が必須になったので、この試験(禁止語の検査)には関係の無い空の形を足す。
    time: { available: false, perMove: null, bySpent: null, afterLongThink: null, byLeft: null, phaseSpent: null, timeUpLosses: null },
    // STEP TIME 作業 2: findings・previous も必須になったので、同じく関係の無い空の形を足す。
    findings: [],
    previous: null,
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

// ---- STEP TIME(docs/STEP_TIME_PLAN_2026-09-22.md §6.1)。消費時間の事実(PatientTime) ----

describe("spentBucketIndexOf・leftBucketIndexOf(4 段・3 段の境目)", () => {
  it("spentBucketIndexOf: 1/2、4/5、9/10 の境目(0〜1・2〜4・5〜9・10 以上)", () => {
    expect([1, 2, 4, 5, 9, 10].map(spentBucketIndexOf)).toEqual([0, 1, 1, 2, 2, 3]);
  });
  it("leftBucketIndexOf: 59/60、119/120 の境目(60 未満・60〜119・120 以上)。負の残りも 60 未満の段", () => {
    expect([-10, 0, 59, 60, 119, 120, 1000].map(leftBucketIndexOf)).toEqual([0, 0, 0, 1, 1, 2, 2]);
  });
});

describe("buildPatientTime: available(1 局でも moveSeconds が無ければ false)", () => {
  const withTime = GAME01_MOVES.slice(0, 4);
  const recordsWithTime: RecordLine[] = plantedRecords(withTime, {});
  const meta = { kind: "meta", kifuId: "time-a", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine;
  const sourceWithTime: GameSource = {
    kifuId: "time-a",
    meta,
    records: recordsWithTime,
    fixed: { id: "time-a", ending: { kind: "resign", ply: 5 }, moves: withTime, moveSeconds: withTime.map(() => ({ spentSec: 1, totalSec: 1 })) },
  };
  const meta2 = { kind: "meta", kifuId: "time-b", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine;
  const sourceWithoutTime: GameSource = {
    kifuId: "time-b",
    meta: meta2,
    records: plantedRecords(withTime, {}),
    fixed: { id: "time-b", ending: { kind: "resign", ply: 5 }, moves: withTime }, // moveSeconds を持たない
  };

  it("全局が moveSeconds を持てば available: true", () => {
    const games = buildGames([sourceWithTime]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.available).toBe(true);
  });

  it("1 局でも moveSeconds が無ければ available: false で他の欄はすべて null(一部だけ出さない)", () => {
    const games = buildGames([sourceWithTime, sourceWithoutTime]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time).toStrictEqual({ available: false, perMove: null, bySpent: null, afterLongThink: null, byLeft: null, phaseSpent: null, timeUpLosses: null });
  });
});

describe("buildPatientTime: perMove(後手の局の添字合わせ。合成の 10 手・手で計算した期待値)", () => {
  // originalMoves(元の手順)の偶数番目(2, 4, 6, 8, 10 手目)が本人(後手)の手。moveSeconds は元の手順の順のまま。
  const originalMoves = GAME01_MOVES.slice(0, 10);
  const aligned = alignMovesToSente(originalMoves, "gote");
  const startSfen = aligned.alignment.mirrored ? aligned.alignment.startSfen : DEFAULT_INITIAL_SFEN;
  const records: RecordLine[] = plantedRecords(aligned.moves, {}, {}, startSfen);
  const meta = {
    kind: "meta",
    kifuId: "time-gote-10",
    startedAt: "",
    gitHead: null,
    enginePath: "",
    mirrored: true,
    startSfen,
    plyOffset: 1,
    originalUserSide: "gote",
  } as unknown as MetaLine;
  // 本人(後手・偶数手目)の秒: 5, 12, 0, 30, 8(手で中央値・平均・割合を計算した。相手(奇数手目)の秒は集計に入らないので何でもよい)
  const moveSeconds = [
    { spentSec: 3, totalSec: 3 }, // 1 手目(相手)
    { spentSec: 5, totalSec: 5 }, // 2 手目(本人)
    { spentSec: 2, totalSec: 5 }, // 3 手目(相手)
    { spentSec: 12, totalSec: 17 }, // 4 手目(本人)
    { spentSec: 1, totalSec: 6 }, // 5 手目(相手)
    { spentSec: 0, totalSec: 17 }, // 6 手目(本人)
    { spentSec: 4, totalSec: 10 }, // 7 手目(相手)
    { spentSec: 30, totalSec: 47 }, // 8 手目(本人)
    { spentSec: 6, totalSec: 16 }, // 9 手目(相手)
    { spentSec: 8, totalSec: 55 }, // 10 手目(本人)
  ];
  const source: GameSource = {
    kifuId: "time-gote-10",
    meta,
    records,
    fixed: { id: "time-gote-10", ending: { kind: "resign", ply: originalMoves.length + 1 }, moves: aligned.moves, originalMoves, mirrored: true, moveSeconds },
  };

  it("perMove: 本人(後手)の 5 手だけを数える([0,5,8,12,30] の中央値 8・平均 11・10 秒以上 40%・30 秒以上 20%・0〜1 秒 20%・1 局の合計 55)", () => {
    const games = buildGames([source]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.available).toBe(true);
    expect(time.perMove).toStrictEqual({ moves: 5, median: 8, mean: 11, ge10: 40, ge30: 20, le1: 20, gameMedian: 55 });
  });
});

describe("buildPatientTime: afterLongThink は「直前の自分の手」= 2 手前(1 手前の相手の手ではない)", () => {
  // GAME01_MOVES(先手)。分岐点 49(ahead 500 → behind -300、崩れる 1 組)を使う(先手の作り物と同じ植え方)。
  const records: RecordLine[] = plantedRecords(GAME01_MOVES, { 48: engineRef(500, { bestmove: "2h2g" }), 50: engineRef(-300) });
  const meta = { kind: "meta", kifuId: "time-along", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine;

  function timeArrayWith(overrides: Record<number, { spentSec: number; totalSec: number }>): Array<{ spentSec: number; totalSec: number } | null> {
    return GAME01_MOVES.map((_, i) => overrides[i + 1] ?? null); // キーは KIF の手数(1 始まり)
  }

  it("正: 49 手目の 2 手前(47 手目、本人)が 10 秒以上なら afterLongThinkAny に数える(1 手前の 48 手目は無関係)", () => {
    const moveSeconds = timeArrayWith({ 47: { spentSec: 15, totalSec: 900 }, 49: { spentSec: 3, totalSec: 5 } });
    const source: GameSource = { kifuId: "time-along", meta, records, fixed: { id: "time-along", ending: { kind: "mate", ply: 56 }, moves: GAME01_MOVES, moveSeconds } };
    const games = buildGames([source]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.afterLongThink).toStrictEqual({
      quickAfterLongThink: { n: 1, collapsed: 1 }, // 49 手目(この手)も 4 秒以下(3 秒)
      afterLongThinkAny: { n: 1, collapsed: 1 },
    });
  });

  it("負(off-by-one の見張り): 49 手目の 1 手前(48 手目、相手)だけが 10 秒以上でも数えない(47 手目は 10 秒未満)", () => {
    const moveSeconds = timeArrayWith({ 47: { spentSec: 2, totalSec: 100 }, 48: { spentSec: 20, totalSec: 900 } });
    const source: GameSource = { kifuId: "time-along", meta, records, fixed: { id: "time-along", ending: { kind: "mate", ply: 56 }, moves: GAME01_MOVES, moveSeconds } };
    const games = buildGames([source]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.afterLongThink).toStrictEqual({ quickAfterLongThink: { n: 0, collapsed: 0 }, afterLongThinkAny: { n: 0, collapsed: 0 } });
  });

  // STEP TIME §6.2 の監査の指摘(2026-09-23): 変異 `<` → `<=` が既存の単体試験を通過した。10 秒ちょうどの境界を確かめる。
  it("正(境界。10 秒ちょうどは longThinkSec 以上に数える): 47 手目がちょうど 10 秒なら afterLongThinkAny に数える", () => {
    const moveSeconds = timeArrayWith({ 47: { spentSec: 10, totalSec: 900 } });
    const source: GameSource = { kifuId: "time-along", meta, records, fixed: { id: "time-along", ending: { kind: "mate", ply: 56 }, moves: GAME01_MOVES, moveSeconds } };
    const games = buildGames([source]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.afterLongThink!.afterLongThinkAny.n).toBe(1);
  });

  it("負(境界): 47 手目が 9 秒(10 秒未満)なら afterLongThinkAny に数えない", () => {
    const moveSeconds = timeArrayWith({ 47: { spentSec: 9, totalSec: 900 } });
    const source: GameSource = { kifuId: "time-along", meta, records, fixed: { id: "time-along", ending: { kind: "mate", ply: 56 }, moves: GAME01_MOVES, moveSeconds } };
    const games = buildGames([source]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.afterLongThink!.afterLongThinkAny.n).toBe(0);
  });
});

describe("buildPatientTime: byLeft(負の残りも 60 未満の段に入る)", () => {
  const records: RecordLine[] = plantedRecords(GAME01_MOVES, { 48: engineRef(500, { bestmove: "2h2g" }), 50: engineRef(-300) });
  const meta = { kind: "meta", kifuId: "time-left", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine;
  // 本人(先手・奇数手目)の秒を 47 手目まで大きくし(累計がすぐ持ち時間を超える)、他は null。
  const moveSeconds = GAME01_MOVES.map((_, i) => (i + 1 === 1 ? { spentSec: 500, totalSec: 500 } : null));
  const source: GameSource = { kifuId: "time-left", meta, records, fixed: { id: "time-left", ending: { kind: "mate", ply: 56 }, moves: GAME01_MOVES, moveSeconds } };

  it("持ち時間 180 秒に対し 1 手目で 500 秒使うと、49 手目の組(崩れた組)の残りは負で「60 未満」の段に入る", () => {
    const games = buildGames([source]);
    const time = buildPatientTime(games, buildPatientGames(games), 180);
    // 1 手目そのものの組(branchPly 1)だけは「この手より前の消費」が 0 なので残り 180(120 以上の段)。
    // それ以外の本人の組は、1 手目の 500 秒がずっと積まれたまま(他の手の秒は null で増えない)なので、残りは負のまま「60 未満」の段。
    // 崩れる組は 49 手目の 1 件だけ(先手の作り物と同じ植え方)。
    expect(time.byLeft).toStrictEqual([
      { n: 19, collapsed: 1 },
      { n: 0, collapsed: 0 },
      { n: 1, collapsed: 0 },
    ]);
  });

  it("--time-limit-sec を渡さなければ byLeft は null", () => {
    const games = buildGames([source]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.byLeft).toBeNull();
  });
});

describe("buildPatientTime: timeUpLosses・phaseSpent.timeUpLoss は「本人が時間で負けた局」だけ(司令塔の指示、2026-09-23)", () => {
  // 手数 4(偶数)・timeUp: 最後の手(4 手目)は後手が指した = 先手(本人)が指せずに時間切れ負け
  const lossMoves = GAME01_MOVES.slice(0, 4);
  const lossRecords: RecordLine[] = plantedRecords(lossMoves, {});
  const lossMeta = { kind: "meta", kifuId: "time-loss", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine;
  const lossMoveSeconds = lossMoves.map((_, i) => ({ spentSec: i + 1, totalSec: i + 1 })); // 1,2,3,4 秒(値そのものは検証しない)
  const lossSource: GameSource = {
    kifuId: "time-loss",
    meta: lossMeta,
    records: lossRecords,
    fixed: { id: "time-loss", ending: { kind: "timeUp", ply: 5 }, moves: lossMoves, moveSeconds: lossMoveSeconds },
  };

  // 手数 3(奇数)・timeUp: 最後の手(3 手目)は先手(本人)が指した = 後手(相手)が指せずに時間切れ負け(本人の勝ち)
  const winMoves = GAME01_MOVES.slice(0, 3);
  const winRecords: RecordLine[] = plantedRecords(winMoves, {});
  const winMeta = { kind: "meta", kifuId: "time-win", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine;
  const winMoveSeconds = winMoves.map((_, i) => ({ spentSec: i + 1, totalSec: i + 1 }));
  const winSource: GameSource = {
    kifuId: "time-win",
    meta: winMeta,
    records: winRecords,
    fixed: { id: "time-win", ending: { kind: "timeUp", ply: 4 }, moves: winMoves, moveSeconds: winMoveSeconds },
  };

  it("本人が時間で負けた局(lossSource)だけが result: 負け になる(前提の確認)", () => {
    const games = buildGames([lossSource, winSource]);
    const patientGames = buildPatientGames(games);
    expect(patientGames.map((g) => [g.id, g.result])).toEqual([
      ["time-loss", "負け"],
      ["time-win", "勝ち"],
    ]);
  });

  it("timeUpLosses には本人が負けた局だけが入り、相手が切れ負けた(本人が勝った)局は入らない", () => {
    const games = buildGames([lossSource, winSource]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.timeUpLosses).toHaveLength(1);
    expect(time.timeUpLosses![0]!.gameNo).toBe(1); // kifuId 昇順で time-loss が 1 局目
  });

  it("phaseSpent.timeUpLoss は 1 局、otherGames は勝った局を含めて数える(0 局にはならない)", () => {
    const games = buildGames([lossSource, winSource]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.phaseSpent!.timeUpLoss.games).toBe(1);
    expect(time.phaseSpent!.otherGames.games).toBe(1);
  });
});

// STEP TIME §6.2 の監査の指摘(2026-09-23): 変異(`phaseSpentOfGame` の `- game.plyOffset` を落とす)が既存の単体試験を
// 通過した(後手の局の試験が無かった)。plyOffset を引いた recordPly を使うことを、手で計算した期待値で確かめる。
describe("buildPatientTime: phaseSpent は後手の局で plyOffset を引いた recordPly を使う(監査の指摘、2026-09-23)", () => {
  const originalMoves = GAME01_MOVES.slice(0, 6);
  const aligned = alignMovesToSente(originalMoves, "gote");
  const startSfen = aligned.alignment.mirrored ? aligned.alignment.startSfen : DEFAULT_INITIAL_SFEN;
  const records: RecordLine[] = plantedRecords(aligned.moves, {}, {}, startSfen);
  const meta = {
    kind: "meta",
    kifuId: "time-phase-gote",
    startedAt: "",
    gitHead: null,
    enginePath: "",
    mirrored: true,
    startSfen,
    plyOffset: 1,
    originalUserSide: "gote",
  } as unknown as MetaLine;
  // 本人(後手・偶数手目)の秒: 2 手目 10 秒・4 手目 20 秒・6 手目 30 秒。total は 6。
  // recordPly = kifPly − plyOffset(1) なので、2→1(1/6 < 1/3 → early)、4→3(3/6 < 2/3 → mid)、6→5(5/6 ≥ 2/3 → late)。
  // plyOffset を引かずに kifPly をそのまま使うと、2→2(2/6 = 1/3 ちょうど → mid)、4→4(4/6 = 2/3 ちょうど → late)とずれる
  // (手で計算した境界が変わる。off-by-one の見張り)。
  const moveSeconds = [
    { spentSec: 1, totalSec: 1 }, // 1 手目(相手)
    { spentSec: 10, totalSec: 10 }, // 2 手目(本人)
    { spentSec: 1, totalSec: 2 }, // 3 手目(相手)
    { spentSec: 20, totalSec: 30 }, // 4 手目(本人)
    { spentSec: 1, totalSec: 3 }, // 5 手目(相手)
    { spentSec: 30, totalSec: 60 }, // 6 手目(本人)
  ];
  const source: GameSource = {
    kifuId: "time-phase-gote",
    meta,
    records,
    fixed: { id: "time-phase-gote", ending: { kind: "resign", ply: originalMoves.length + 1 }, moves: aligned.moves, originalMoves, mirrored: true, moveSeconds },
  };

  it("otherGames(投了。時間で負けた局ではない)が 1 局・序盤 10・中盤 20・終盤 30", () => {
    const games = buildGames([source]);
    const time = buildPatientTime(games, buildPatientGames(games), undefined);
    expect(time.phaseSpent).toStrictEqual({
      timeUpLoss: { games: 0, early: 0, mid: 0, late: 0 },
      otherGames: { games: 1, early: 10, mid: 20, late: 30 },
    });
  });
});

// ---- STEP TIME 作業 2(docs/STEP_TIME_PLAN_2026-09-22.md §6.4)。findings の判定・previous の比較 ----

const EMPTY_TIME: PatientTime = { available: false, perMove: null, bySpent: null, afterLongThink: null, byLeft: null, phaseSpent: null, timeUpLosses: null };
const EMPTY_OVERVIEW: PatientOverview = { fell: 0, early: 0, mid: 0, late: 0, fromAhead: 0, fromAheadLoss: 0, moveCheck: null };

function timeWithBySpent(le1: { n: number; collapsed: number }, ge10: { n: number; collapsed: number }): PatientTime {
  return { ...EMPTY_TIME, available: true, bySpent: [le1, { n: 0, collapsed: 0 }, { n: 0, collapsed: 0 }, ge10] };
}

/** aheadLoss を発火させない(scores が 300 未満のまま)、局数だけが要る試験用のダミーの局。 */
function emptyGames(n: number): PatientGame[] {
  return Array.from({ length: n }, (_, i) => ({ no: i + 1, id: `g${i + 1}`, side: "先手" as const, total: 1, result: "勝ち" as const, ending: null, events: 0, scores: [0], plies: [1], marks: [] }));
}

function gameOf(no: number, result: "勝ち" | "負け", scores: Array<number | null>): PatientGame {
  return { no, id: `g${no}`, side: "先手", total: scores.length, result, ending: null, events: 0, scores, plies: scores.map((_, i) => i + 1), marks: [] };
}

describe("buildFindings: timeSpent(minPairs・ratio の境界)", () => {
  it("minPairs 未満(19)なら、比率の条件を満たしていても出さない", () => {
    const time = timeWithBySpent({ n: 100, collapsed: 10 }, { n: 19, collapsed: 4 }); // 4/19 ≈ 21.05%(le1 の 10% の 2 倍以上)
    const [timeSpent] = buildFindings(EMPTY_OVERVIEW, time, emptyGames(20));
    expect(timeSpent).toMatchObject({ kind: "timeSpent", shown: false });
  });
  it("minPairs ちょうど(20)で比率もちょうど 2 倍なら出す", () => {
    const time = timeWithBySpent({ n: 100, collapsed: 10 }, { n: 20, collapsed: 4 }); // 4/20 = 20%、le1 は 10% ちょうど 2 倍
    const [timeSpent] = buildFindings(EMPTY_OVERVIEW, time, emptyGames(20));
    expect(timeSpent).toMatchObject({ kind: "timeSpent", shown: true, numbers: { a: 4, b: 20, p: 20, c: 10, d: 100, q: 10 } });
  });
  it("比率が 2 倍にわずかに届かなければ出さない(3/20 = 15% < 20%)", () => {
    const time = timeWithBySpent({ n: 100, collapsed: 10 }, { n: 20, collapsed: 3 });
    const [timeSpent] = buildFindings(EMPTY_OVERVIEW, time, emptyGames(20));
    expect(timeSpent).toMatchObject({ kind: "timeSpent", shown: false });
  });
  it("0〜1 秒の分母が 0 なら比べられないので出さない", () => {
    const time = timeWithBySpent({ n: 0, collapsed: 0 }, { n: 100, collapsed: 100 });
    const [timeSpent] = buildFindings(EMPTY_OVERVIEW, time, emptyGames(20));
    expect(timeSpent).toMatchObject({ kind: "timeSpent", shown: false });
  });
  it("time.available が false なら、数はすべて null で出さない", () => {
    const [timeSpent] = buildFindings(EMPTY_OVERVIEW, EMPTY_TIME, emptyGames(20));
    expect(timeSpent).toMatchObject({ kind: "timeSpent", shown: false, numbers: { a: null, b: null, p: null, c: null, d: null, q: null } });
  });
  it("FINDING_VALUES は計画の値(minPairs 20・ratio 2)のまま", () => {
    expect(FINDING_VALUES).toStrictEqual({ minPairs: 20, ratio: 2 });
  });
});

describe("buildFindings: timeUpLoss(finalScore の詰みの扱い)", () => {
  it("finalScore が +300 以上・詰み(±3000 の正)は m に数え、null・300 未満は数えない", () => {
    const time: PatientTime = {
      ...EMPTY_TIME,
      available: true,
      bySpent: [
        { n: 0, collapsed: 0 },
        { n: 0, collapsed: 0 },
        { n: 0, collapsed: 0 },
        { n: 0, collapsed: 0 },
      ],
      timeUpLosses: [
        { gameNo: 1, total: 10, usedSec: 100, finalScore: 300 }, // ちょうど 300(数える)
        { gameNo: 2, total: 10, usedSec: 100, finalScore: 3000 }, // 詰み(数える)
        { gameNo: 3, total: 10, usedSec: 100, finalScore: 299 }, // 300 未満(数えない)
        { gameNo: 4, total: 10, usedSec: 100, finalScore: null }, // 読めていない(数えない)
      ],
    };
    const [, timeUpLoss] = buildFindings(EMPTY_OVERVIEW, time, emptyGames(20));
    expect(timeUpLoss).toMatchObject({ kind: "timeUpLoss", shown: true, numbers: { n: 4, m: 2 } });
  });
  it("timeUpLosses が 0 局なら出さない", () => {
    const time: PatientTime = { ...EMPTY_TIME, available: true, bySpent: [{ n: 0, collapsed: 0 }, { n: 0, collapsed: 0 }, { n: 0, collapsed: 0 }, { n: 0, collapsed: 0 }], timeUpLosses: [] };
    const [, timeUpLoss] = buildFindings(EMPTY_OVERVIEW, time, emptyGames(20));
    expect(timeUpLoss).toMatchObject({ kind: "timeUpLoss", shown: false, numbers: { n: 0, m: 0 } });
  });
});

// 司令塔の直し(2026-09-23、監査の前): aheadLoss は overview.fromAhead・fromAheadLoss(組の延べ)ではなく、
// 凍結の _head.py の game_facts と同じ決め方(局の scores が一度でも +300 以上・その局の result)で**局の数**を数える。
describe("buildFindings: aheadLoss(局の数。scores が一度でも +300 以上になった局・その局の result)", () => {
  it("+300 以上になり、かつ負けた局を aheadLossGames、+300 以上になった局を aheadGames に数える", () => {
    const games = [
      gameOf(1, "負け", [100, 300, 200]), // 300 以上になり、負け → aheadGames・aheadLossGames の両方
      gameOf(2, "勝ち", [100, 400, 450]), // 300 以上になったが勝ち → aheadGames のみ
      gameOf(3, "負け", [100, 200, 250]), // 300 未満のまま負け → どちらにも入らない
    ];
    const [, , aheadLoss] = buildFindings(EMPTY_OVERVIEW, EMPTY_TIME, games);
    expect(aheadLoss).toMatchObject({ kind: "aheadLoss", shown: true, numbers: { aheadGames: 2, aheadLossGames: 1 } });
  });
  it("境界: ちょうど 300 は優勢に入る(299 は入らない)", () => {
    const games = [gameOf(1, "負け", [300]), gameOf(2, "負け", [299])];
    const [, , aheadLoss] = buildFindings(EMPTY_OVERVIEW, EMPTY_TIME, games);
    expect(aheadLoss).toMatchObject({ kind: "aheadLoss", shown: true, numbers: { aheadGames: 1, aheadLossGames: 1 } });
  });
  it("優勢になった局が無ければ出さない(aheadGames 0)", () => {
    const games = [gameOf(1, "負け", [100, 200])];
    const [, , aheadLoss] = buildFindings(EMPTY_OVERVIEW, EMPTY_TIME, games);
    expect(aheadLoss).toMatchObject({ kind: "aheadLoss", shown: false, numbers: { aheadGames: 0, aheadLossGames: 0 } });
  });
  it("優勢になった局がすべて勝ちなら出さない(aheadGames > 0・aheadLossGames 0)", () => {
    const games = [gameOf(1, "勝ち", [400])];
    const [, , aheadLoss] = buildFindings(EMPTY_OVERVIEW, EMPTY_TIME, games);
    expect(aheadLoss).toMatchObject({ kind: "aheadLoss", shown: false, numbers: { aheadGames: 1, aheadLossGames: 0 } });
  });
  it("null の評価は無視する(未測定の手を優勢と数えない)", () => {
    const games = [gameOf(1, "負け", [null, null])];
    const [, , aheadLoss] = buildFindings(EMPTY_OVERVIEW, EMPTY_TIME, games);
    expect(aheadLoss).toMatchObject({ kind: "aheadLoss", shown: false, numbers: { aheadGames: 0, aheadLossGames: 0 } });
  });
});

describe("buildFindings: phase・none", () => {
  it("phase はつねに出す(崩れ 0 回でも判定なし)", () => {
    const [, , , phase] = buildFindings(EMPTY_OVERVIEW, EMPTY_TIME, emptyGames(20));
    expect(phase).toMatchObject({ kind: "phase", shown: true, numbers: { fell: 0, early: 0, mid: 0, late: 0 } });
  });
  it("none は timeSpent・timeUpLoss・aheadLoss が 1 つも出ないときだけ出す", () => {
    const [, , , , none] = buildFindings(EMPTY_OVERVIEW, EMPTY_TIME, emptyGames(20));
    expect(none).toMatchObject({ kind: "none", shown: true, numbers: { games: 20 } });
  });
  it("none は 3 つのどれか 1 つでも出ていれば出さない(aheadLoss だけが出る場合)", () => {
    const games = [gameOf(1, "負け", [300])];
    const [, , , , none] = buildFindings(EMPTY_OVERVIEW, EMPTY_TIME, games);
    expect(none).toMatchObject({ kind: "none", shown: false });
  });
});

describe("buildPrevious: 前回との比較(3 通り)", () => {
  function findingOf(kind: Finding["kind"], shown: boolean): Finding {
    return { kind, shown, numbers: { x: shown ? 1 : 0 }, text: "t" };
  }
  it("null を渡せば previous も null", () => {
    expect(buildPrevious(null, [findingOf("phase", true)])).toBeNull();
  });
  it("前回出た・今回も出た / 前回出た・今回は出ない / 前回出ない・今回出た の 3 通り", () => {
    const previous = {
      summary: { games: 14 },
      findings: [findingOf("timeSpent", true), findingOf("timeUpLoss", true), findingOf("aheadLoss", false)],
    };
    const current = [findingOf("timeSpent", true), findingOf("timeUpLoss", false), findingOf("aheadLoss", true)];
    const result = buildPrevious(previous, current);
    expect(result).toStrictEqual({
      games: 14,
      findings: [
        { kind: "timeSpent", shownBefore: true, shownNow: true, numbersBefore: { x: 1 }, numbersNow: { x: 1 } },
        { kind: "timeUpLoss", shownBefore: true, shownNow: false, numbersBefore: { x: 1 }, numbersNow: { x: 0 } },
        { kind: "aheadLoss", shownBefore: false, shownNow: true, numbersBefore: { x: 0 }, numbersNow: { x: 1 } },
      ],
    });
  });
  it("前回の findings に今回の種類が無ければ例外(道具のバージョン違いを黙って無視しない)", () => {
    const previous = { summary: { games: 14 }, findings: [findingOf("timeSpent", true)] };
    expect(() => buildPrevious(previous, [findingOf("timeSpent", true), findingOf("phase", true)])).toThrow(ReportDataError);
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
