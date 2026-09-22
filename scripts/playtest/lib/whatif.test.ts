// STEP WHATIF 作業 1(docs/STEP_WHATIF_PLAN_2026-09-22.md)。lib/whatif.ts の単体試験。
// **エンジンは起動しない**(MultiPV の結果は WhatifEngineLine の読みを差し替えて渡す)。
//
// 【正解の置き方】盤の図・区域の決め方から手で導く(実装の出力から写さない)。既存の moveFactsOf の試験
// (lib/moveFacts.test.ts)・isInCheck の試験(apps/server/src/rules/gameStatus.test.ts)と同じ構成の局面を使う。

import { describe, expect, it } from "vitest";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { isGameOver, isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import { POSITION_FACTS_RULES } from "./counterfactual.js";
import { moveFactsOf } from "./moveFacts.js";
import {
  WHATIF_VALUES,
  actualRankOf,
  candidatesOf,
  evalValueOf,
  evaluableTurns,
  lossOf,
  sceneReadPlies,
  sideMovesOf,
  sideOf,
  tagsOf,
  topGapCpOf,
  userTurnsOf,
  whatifGameSummaryOf,
  whatifPositionOf,
  whatifSceneOf,
  whatifSceneReadSummaryOf,
  withDisplayPly,
  type WhatifEngineLine,
  type WhatifPosition,
  type WhatifSideReader,
  type WhatifSideReadResult,
  type WhatifValues,
} from "./whatif.js";

const INIT = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
/** 5七の後手の飛車が、5九の先手玉に王手をかけている局面(王手中・非終局)。gameStatus.test.ts と同じ構成。 */
const SENTE_IN_CHECK_SFEN = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";
/** 先手が詰まされた終局(王手中かつ終局)。checkBaseline.test.ts と同じ構成。 */
const SENTE_CHECKMATED_SFEN = "KPs6/1g7/r8/9/9/9/9/9/9 b - 1";

// ---- WHATIF_VALUES(判断的知識の仮置き。値そのものを直接確かめる) ----

describe("WHATIF_VALUES", () => {
  it("計画の仮置きの値(2026-09-22、STEP WHATIF 作業 4 で sideVersion・hitsDefenderRadius・attackZoneRadius を追記)", () => {
    expect(WHATIF_VALUES).toStrictEqual({
      multiPv: 5,
      nodes: 1_000_000,
      startPly: 17,
      minLossCp: 600,
      narrowGapCp: 400,
      riseCp: 400,
      pvMoves: 7,
      sideZoneRadius: 2,
      sideNodes: 1_000_000,
      sideVersion: 2,
      hitsDefenderRadius: 2,
      attackZoneRadius: 3,
    });
  });
});

// ---- 印(行き先だけで決まる。既存の moveFactsOf をそのまま呼ぶ) ----
//
// 【STEP WHATIF 作業 4(計画 §9.3)で足した 3 つの印(captures・hitsOppKingZonePiece・oppKingZone3)について】
// `tagsOf` の戻り値の形が増えたので、既存の `toEqual`(完全一致)の期待値にも 3 つの欄を足す(盤の図から手で
// 導いた値。実装の出力からは写さない)。この 5 件の局面はどれも駒を取らず・相手玉のそばの駒に当たらないので
// captures・hitsOppKingZonePiece は常に false。oppKingZone3(相手玉から 3 マス以内)だけは、
// 「attack(oppKingZone のみ)」の局面(4a は相手玉 5a から 1 マス)で true になる(距離 1 ≤ 3。oppKingZone
// (距離 ≤ 2)がすでに true のこの局面では、side の結果(v1/v2 とも "attack")は変わらない)。
describe("tagsOf・sideOf(計画 §2.1・§9.3)", () => {
  it("none: 平手 7g7f はどの印も立たない", () => {
    expect(tagsOf(INIT, "7g7f")).toEqual({
      oppKingZone: false,
      ownKingZone: false,
      givesCheck: false,
      kingMove: false,
      captures: false,
      hitsOppKingZonePiece: false,
      oppKingZone3: false,
    });
    expect(sideOf(tagsOf(INIT, "7g7f"))).toBe("none");
  });

  it("kingMove: 玉を動かす手は kingMove=true・ownKingZone=false(toInOwnKingZone 自体は true でも除く)、side は defense", () => {
    const sfen = "4k4/9/9/9/9/9/9/9/4K4 b G 1";
    // 前提: moveFactsOf の toInOwnKingZone は true(玉の手なので新しい位置がそのまま自玉の区域に入る)
    expect(moveFactsOf(sfen, "5i4h", POSITION_FACTS_RULES).toInOwnKingZone).toBe(true);
    const tags = tagsOf(sfen, "5i4h");
    expect(tags).toEqual({
      oppKingZone: false,
      ownKingZone: false,
      givesCheck: false,
      kingMove: true,
      captures: false,
      hitsOppKingZonePiece: false,
      oppKingZone3: false,
    });
    expect(sideOf(tags)).toBe("defense");
  });

  it("defense(ownKingZone): 金が自玉(5i)のそばへ動く。玉の手ではない", () => {
    const sfen = "4k4/9/9/9/9/9/4G4/9/4K4 b - 1";
    expect(moveFactsOf(sfen, "5g5h", POSITION_FACTS_RULES).toInOwnKingZone).toBe(true);
    const tags = tagsOf(sfen, "5g5h");
    expect(tags).toEqual({
      oppKingZone: false,
      ownKingZone: true,
      givesCheck: false,
      kingMove: false,
      captures: false,
      hitsOppKingZonePiece: false,
      oppKingZone3: false,
    });
    expect(sideOf(tags)).toBe("defense");
  });

  it("attack(oppKingZone のみ、王手にならない): 銀が相手玉(5a)の区域(4a、玉と同じ段=横の関係)へ動く。銀は横に利かないので王手にならない", () => {
    const sfen = "4k4/6S2/9/9/9/9/9/9/4K4 b - 1";
    expect(isInCheck(applyMove(sfen, "3b4a"), "gote")).toBe(false);
    // 区域に入ることの前提確認(moveFactsOf で直接)
    expect(moveFactsOf(sfen, "3b4a", POSITION_FACTS_RULES).toInOpponentKingZone).toBe(true);
    const tags = tagsOf(sfen, "3b4a");
    expect(tags).toEqual({
      oppKingZone: true,
      ownKingZone: false,
      givesCheck: false,
      kingMove: false,
      captures: false,
      hitsOppKingZonePiece: false,
      // 4a は相手玉 5a から 1 マス(≤ attackZoneRadius(3))。oppKingZone(≤ 2)もすでに true なので、
      // side の結果は v1/v2 とも "attack" のまま(下の sideOf の期待は変わらない)。
      oppKingZone3: true,
    });
    expect(sideOf(tags)).toBe("attack");
  });

  it("sideZoneRadius の境(既定 2): ちょうど 2 マス(相手玉 5a から 5c)は入り、1 マス以内では入らない。王手にもならない", () => {
    const sfen = "4k4/9/9/4S4/9/9/9/9/4K4 b - 1";
    expect(isInCheck(applyMove(sfen, "5d5c"), "gote")).toBe(false);
    expect(tagsOf(sfen, "5d5c").oppKingZone).toBe(true); // 既定(sideZoneRadius: 2)
    const radius1: WhatifValues = { ...WHATIF_VALUES, sideZoneRadius: 1 };
    expect(tagsOf(sfen, "5d5c", radius1).oppKingZone).toBe(false);
  });

  it("attack(givesCheck のみ、区域の外): 飛が遠くから王手をかける(5e は相手玉 5a の区域の外。attackZoneRadius(3)の外でもある ― 距離 4)", () => {
    const sfen = "4k4/9/9/9/8R/9/9/9/4K4 b - 1";
    const after = applyMove(sfen, "1e5e");
    expect(isInCheck(after, "gote")).toBe(true);
    // 区域の外であることの前提確認(moveFactsOf で直接)
    expect(moveFactsOf(sfen, "1e5e", POSITION_FACTS_RULES).toInOpponentKingZone).toBe(false);
    const tags = tagsOf(sfen, "1e5e");
    expect(tags).toEqual({
      oppKingZone: false,
      ownKingZone: false,
      givesCheck: true,
      kingMove: false,
      captures: false,
      hitsOppKingZonePiece: false,
      oppKingZone3: false,
    });
    expect(sideOf(tags)).toBe("attack");
  });

  it("both: 銀が両方の玉の区域が重なる升(5e)へ動く(自玉 5f・相手玉 5d)", () => {
    const sfen = "9/9/9/4k4/9/3SK4/9/9/9 b - 1";
    const tags = tagsOf(sfen, "6f5e");
    expect(tags.ownKingZone).toBe(true);
    expect(tags.oppKingZone).toBe(true);
    expect(sideOf(tags)).toBe("both");
  });
});

// ---- v2 の印(captures・hitsOppKingZonePiece・oppKingZone3。計画 §9.3・§9.4) ----
//
// この一群は、v1 では none(攻めの側でない)だが v2 では attack になる局面を、3 つの印それぞれについて
// 1 つずつ切り分ける(盤の図・区域の決め方から手で導いた正解。実装の出力からは写さない)。

describe("v2 の印(計画 §9.3・§9.4)", () => {
  it("captures: 相手玉から遠い手でも、相手の駒を取れば v2 は attack(v1 は none)", () => {
    // 銀 5f が、相手玉 5a から 4 マス(区域の外)の 5e にいる相手の歩を取る。ほかに相手の駒は無い。
    const sfen = "4k4/9/9/9/4p4/4S4/9/9/4K4 b - 1";
    const tags = tagsOf(sfen, "5f5e");
    expect(tags).toEqual({
      oppKingZone: false,
      ownKingZone: false,
      givesCheck: false,
      kingMove: false,
      captures: true,
      hitsOppKingZonePiece: false,
      oppKingZone3: false,
    });
    expect(sideOf(tags, { ...WHATIF_VALUES, sideVersion: 1 })).toBe("none");
    expect(sideOf(tags)).toBe("attack"); // 既定(v2)
  });

  it("hitsOppKingZonePiece: 行き先は相手玉から遠くても、動かした駒(飛)が相手玉のそば(2 マス以内)の相手の歩に当たれば v2 は attack(v1 は none)", () => {
    // 飛 9f が 5f まで横に動く(捕る駒は無い)。5f から縦に利きが伸び、5c の相手の歩(相手玉 5a から 2 マス)に当たる
    // (5c で止まるので、その先の 5b・5a には利かない ― 線の駒は止めた升を含む決め方)。
    const sfen = "4k4/9/4p4/9/9/R8/9/9/4K4 b - 1";
    const tags = tagsOf(sfen, "9f5f");
    expect(tags).toEqual({
      oppKingZone: false,
      ownKingZone: false,
      givesCheck: false,
      kingMove: false,
      captures: false,
      hitsOppKingZonePiece: true,
      oppKingZone3: false,
    });
    expect(sideOf(tags, { ...WHATIF_VALUES, sideVersion: 1 })).toBe("none");
    expect(sideOf(tags)).toBe("attack"); // 既定(v2)
  });

  it("oppKingZone3: 相手玉からちょうど 3 マス(sideZoneRadius(2)の外・attackZoneRadius(3)の内)は v2 だけ attack", () => {
    const sfen = "4k4/9/9/9/4S4/9/9/9/4K4 b - 1"; // 銀 5e が 5d(相手玉 5a から 3 マス)へ進む
    const tags = tagsOf(sfen, "5e5d");
    expect(tags).toEqual({
      oppKingZone: false,
      ownKingZone: false,
      givesCheck: false,
      kingMove: false,
      captures: false,
      hitsOppKingZonePiece: false,
      oppKingZone3: true,
    });
    expect(sideOf(tags, { ...WHATIF_VALUES, sideVersion: 1 })).toBe("none");
    expect(sideOf(tags)).toBe("attack"); // 既定(v2)
  });

  it("成りの有無: captures・oppKingZone3 は行き先だけで決まるので変わらないが、hitsOppKingZonePiece は駒の利きが変わるため変わりうる", () => {
    // 銀 4c → 4b(どちらも敵陣。成り・不成りのどちらも合法)。行き先 4b のそばに相手の駒は無いが、
    // 4b から見て真横(sideways)の 3b に相手の歩がいる(相手玉 5a から 2 マス)。
    // 銀は真横に利かないので当たらない。成銀(金と同じ利き)は真横に利くので当たる。
    const sfen = "4k4/6p2/5S3/9/9/9/9/9/4K4 b - 1";

    const notPromoted = tagsOf(sfen, "4c4b");
    expect(notPromoted.captures).toBe(false);
    expect(notPromoted.oppKingZone3).toBe(true); // 4b は相手玉 5a から 1 マス
    expect(notPromoted.hitsOppKingZonePiece).toBe(false); // 銀は真横に利かない

    const promoted = tagsOf(sfen, "4c4b+");
    expect(promoted.captures).toBe(false); // 変わらない(行き先は同じ・取っていない)
    expect(promoted.oppKingZone3).toBe(true); // 変わらない(行き先は同じ)
    expect(promoted.hitsOppKingZonePiece).toBe(true); // 変わる(成銀は金と同じ利きで真横にも利く)
  });
});

// ---- 評価を 1 本の数直線に乗せる(mate と cp を比べるため) ----

describe("evalValueOf", () => {
  it("cp はそのまま", () => {
    expect(evalValueOf({ scoreCp: 123, mate: null })).toBe(123);
    expect(evalValueOf({ scoreCp: -50, mate: null })).toBe(-50);
  });

  it("勝ちの詰みはどんな cp よりも高く、詰みまでが短いほど高い", () => {
    const mate1 = evalValueOf({ scoreCp: null, mate: 1 })!;
    const mate3 = evalValueOf({ scoreCp: null, mate: 3 })!;
    expect(mate1).toBeGreaterThan(mate3);
    expect(mate3).toBeGreaterThan(30000);
  });

  it("負けの詰みはどんな cp よりも低く、詰みまでが長いほど(まだ時間があるほど)高い(=ましな方)", () => {
    const mateMinus1 = evalValueOf({ scoreCp: null, mate: -1 })!;
    const mateMinus10 = evalValueOf({ scoreCp: null, mate: -10 })!;
    expect(mateMinus10).toBeGreaterThan(mateMinus1);
    expect(mateMinus1).toBeLessThan(-30000);
  });

  it("cp も mate も無ければ null", () => {
    expect(evalValueOf({ scoreCp: null, mate: null })).toBeNull();
  });
});

// ---- 候補の一覧 ----

function line(move: string, scoreCp: number | null, mate: number | null = null, pv?: readonly string[]): WhatifEngineLine {
  return { scoreCp, mate, pv: pv ?? [move] };
}

describe("candidatesOf", () => {
  it("読み筋の先頭が無い行(空の pv)は除く", () => {
    const candidates = candidatesOf(INIT, [line("7g7f", 100), { scoreCp: 50, mate: null, pv: [] }]);
    expect(candidates).toHaveLength(1);
    expect(candidates[0]!.move).toBe("7g7f");
  });

  it("読み筋は先頭 pvMoves(既定 7)手だけを持つ", () => {
    const pv = ["7g7f", "a", "b", "c", "d", "e", "f", "g", "h"];
    const [candidate] = candidatesOf(INIT, [line("7g7f", 100, null, pv)]);
    expect(candidate!.pv).toEqual(["7g7f", "a", "b", "c", "d", "e", "f"]);
  });

  it("pvMoves を変えると、そのぶんだけ読み筋が変わる(値を WHATIF_VALUES から読んでいることの確認)", () => {
    const pv = ["7g7f", "a", "b", "c"];
    const values: WhatifValues = { ...WHATIF_VALUES, pvMoves: 2 };
    const [candidate] = candidatesOf(INIT, [line("7g7f", 100, null, pv)], values);
    expect(candidate!.pv).toEqual(["7g7f", "a"]);
  });

  it("side・tags は tagsOf と同じ(平手 7g7f は none)", () => {
    const [candidate] = candidatesOf(INIT, [line("7g7f", 100)]);
    expect(candidate!.tags).toEqual(tagsOf(INIT, "7g7f"));
    expect(candidate!.side).toBe("none");
  });
});

describe("actualRankOf", () => {
  const candidates = candidatesOf(INIT, [line("7g7f", 100), line("2g2f", 80), line("3g3f", 60)]);
  it("見つかれば 1 始まりの順位", () => {
    expect(actualRankOf(candidates, "7g7f")).toBe(1);
    expect(actualRankOf(candidates, "3g3f")).toBe(3);
  });
  it("見つからなければ null", () => {
    expect(actualRankOf(candidates, "5g5f")).toBeNull();
  });
});

// ---- 第 1 候補と第 2 候補の差 ----

describe("topGapCpOf", () => {
  it("cp 同士なら差", () => {
    const candidates = candidatesOf(INIT, [line("7g7f", 1000), line("2g2f", 400)]);
    expect(topGapCpOf(candidates)).toBe(600);
  });
  it("どちらかが詰みなら null", () => {
    const candidates = candidatesOf(INIT, [line("7g7f", 1000), line("2g2f", null, 3)]);
    expect(topGapCpOf(candidates)).toBeNull();
  });
  it("候補が 2 未満なら null", () => {
    expect(topGapCpOf(candidatesOf(INIT, [line("7g7f", 1000)]))).toBeNull();
  });
});

// ---- 分かれ道の差(loss) ----

describe("lossOf", () => {
  it("実戦の手が見つかれば、第 1 候補との cp 差(下限ではない)", () => {
    const candidates = candidatesOf(INIT, [line("7g7f", 1000), line("2g2f", 400)]);
    const loss = lossOf(candidates, 2);
    expect(loss).toEqual({ value: 600, cpValue: 600, isLowerBound: false });
  });

  it("実戦の手が候補に無ければ、第 K 候補(最後)との差を下限として使う", () => {
    const candidates = candidatesOf(INIT, [line("7g7f", 1000), line("2g2f", 400), line("3g3f", 100)]);
    const loss = lossOf(candidates, null);
    expect(loss).toEqual({ value: 900, cpValue: 900, isLowerBound: true });
  });

  it("第 1 候補が勝ちの詰みで、実戦の手が cp: 数直線の値で大きな差になり、cpValue は null(cp では書けない)", () => {
    const candidates = candidatesOf(INIT, [line("7g7f", null, 5), line("2g2f", 200)]);
    const loss = lossOf(candidates, 2)!;
    expect(loss.cpValue).toBeNull();
    expect(loss.value).toBeGreaterThan(WHATIF_VALUES.minLossCp);
  });

  it("実戦の手の続きが自玉の詰み(mate 負): 数直線で大きな差になる", () => {
    const candidates = candidatesOf(INIT, [line("7g7f", 50), line("2g2f", null, -3)]);
    const loss = lossOf(candidates, 2)!;
    expect(loss.value).toBeGreaterThan(WHATIF_VALUES.minLossCp);
  });

  it("候補が無ければ null", () => {
    expect(lossOf([], null)).toBeNull();
  });
});

// ---- 1 局面の記録(whatifPositionOf) ----

/** INIT から 1 手ずつの平手の合法手(タグはすべて none)。境を跨ぐ試験用に scoreCp だけ差し替える。 */
function initPosition(
  candidateScores: readonly (number | { mate: number })[],
  actualMove: string,
  previousCandidate0Value: number | null = null,
  extra: Partial<{ ply: number }> = {},
): WhatifPosition {
  const moves = ["7g7f", "2g2f", "3g3f", "5g5f", "6g6f"];
  const lines = candidateScores.map((score, i) => (typeof score === "number" ? line(moves[i]!, score) : line(moves[i]!, null, score.mate)));
  return whatifPositionOf({ ply: extra.ply ?? WHATIF_VALUES.startPly, sfen: INIT, actualMove, lines, previousCandidate0Value });
}

describe("whatifPositionOf: 場面の境(計画 §2.2)", () => {
  it("fork: 差がちょうど minLossCp(600)なら拾う", () => {
    const p = initPosition([1000, 400], "2g2f");
    expect(p.actualRank).toBe(2);
    expect(p.loss?.value).toBe(600);
    expect(p.scenes.fork).toBe(true);
  });
  it("fork: 差が minLossCp − 1(599)なら拾わない", () => {
    const p = initPosition([1000, 401], "2g2f");
    expect(p.loss?.value).toBe(599);
    expect(p.scenes.fork).toBe(false);
  });
  it("fork: 実戦の手が候補に無ければ、差の大小によらず拾う", () => {
    const p = initPosition([1000, 999], "1g1f");
    expect(p.actualRank).toBeNull();
    expect(p.loss?.isLowerBound).toBe(true);
    expect(p.scenes.fork).toBe(true);
  });

  it("narrowHeld: 実戦 = 第 1 候補、差がちょうど narrowGapCp(400)なら拾う", () => {
    const p = initPosition([1000, 600], "7g7f");
    expect(p.actualRank).toBe(1);
    expect(p.topGapCp).toBe(400);
    expect(p.scenes.narrowHeld).toBe(true);
  });
  it("narrowHeld: 差が narrowGapCp − 1(399)なら拾わない", () => {
    const p = initPosition([1000, 601], "7g7f");
    expect(p.topGapCp).toBe(399);
    expect(p.scenes.narrowHeld).toBe(false);
  });
  it("narrowHeld: 実戦 = 第 1 候補でも、第 2 候補が詰みなら拾わない(どちらも詰みでないことが要る)", () => {
    const p = initPosition([1000, { mate: 2 }], "7g7f");
    expect(p.scenes.narrowHeld).toBe(false);
  });
  it("narrowHeld: 実戦の手が第 1 候補でなければ拾わない", () => {
    const p = initPosition([1000, 600], "2g2f");
    expect(p.scenes.narrowHeld).toBe(false);
  });

  it("chanceHeld: 直前からの上がりがちょうど riseCp(400)、実戦 = 第 1 候補なら拾う", () => {
    const p = initPosition([1400], "7g7f", 1000);
    expect(p.scenes.chanceHeld).toBe(true);
  });
  it("chanceHeld: 上がりが riseCp − 1(399)なら拾わない", () => {
    const p = initPosition([1399], "7g7f", 1000);
    expect(p.scenes.chanceHeld).toBe(false);
  });
  it("chanceHeld: 直前の値が無ければ(この局面より前に読んでいない)拾わない", () => {
    const p = initPosition([1400], "7g7f", null);
    expect(p.scenes.chanceHeld).toBe(false);
  });
  it("chanceHeld: 実戦の手が第 1 候補でなければ拾わない", () => {
    const p = initPosition([1400, 1000], "2g2f", 1000);
    expect(p.scenes.chanceHeld).toBe(false);
  });
});

// ---- 1 局ごとのまとめ ----

describe("whatifGameSummaryOf", () => {
  it("読んだ局面の数・第 1 候補と同じ数・multiPv 位以内の数", () => {
    const positions = [initPosition([1000, 400], "7g7f"), initPosition([1000, 400], "2g2f"), initPosition([1000, 999], "1g1f")];
    const summary = whatifGameSummaryOf(positions);
    expect(summary.positionsRead).toBe(3);
    expect(summary.matchesTop1).toBe(1);
    expect(summary.withinMultiPv).toBe(2);
  });

  it("biggestFork: 差が最大の 1 手を選ぶ(minLossCp に届かなくても出す)", () => {
    const small = initPosition([1000, 999], "2g2f", null, { ply: 17 }); // 差 1
    const big = initPosition([1000, 400], "2g2f", null, { ply: 19 }); // 差 600
    const summary = whatifGameSummaryOf([small, big]);
    expect(summary.biggestFork).toEqual({ ply: 19, lossValue: 600, lossCp: 600, lossIsLowerBound: false });
  });

  it("biggestFork: 実戦の手が候補に無いときは lossIsLowerBound: true", () => {
    const p = initPosition([1000, 900], "1g1f", null, { ply: 17 });
    const summary = whatifGameSummaryOf([p]);
    expect(summary.biggestFork?.lossIsLowerBound).toBe(true);
  });

  it("biggestFork: 読んだ局面が 0 なら null", () => {
    expect(whatifGameSummaryOf([]).biggestFork).toBeNull();
  });

  it("scenes は拾った場面の手数の一覧(1 つの局面が複数の種類に当たれば、それぞれの配列に入る)", () => {
    // narrowHeld かつ chanceHeld になる局面(実戦 = 第 1 候補、差 400 以上、直前からの上がりも 400 以上)
    const p = initPosition([1000, 600], "7g7f", 500, { ply: 17 });
    expect(p.scenes).toEqual({ fork: false, narrowHeld: true, chanceHeld: true });
    const summary = whatifGameSummaryOf([p]);
    expect(summary.scenes).toEqual({ fork: [], narrowHeld: [17], chanceHeld: [17] });
  });
});

// ---- 場面ごとの側の読み(計画 §2.5) ----

describe("sideMovesOf(合法手を攻め・守りに分ける。sideOf と同じ決め方)", () => {
  it("攻め(桂 5d4b+)と守り(金 5g5h)がどちらも入る", () => {
    const sfen = "4k4/9/9/4N4/9/9/4G4/9/4K4 b - 1";
    const { attack, defense } = sideMovesOf(sfen);
    expect(attack).toContain("5d4b+");
    expect(defense).toContain("5g5h");
    expect(attack).not.toContain("5g5h");
    expect(defense).not.toContain("5d4b+");
  });

  it("both の手(銀 6f5e)は両方に入る", () => {
    const sfen = "9/9/9/4k4/9/3SK4/9/9/9 b - 1";
    const { attack, defense } = sideMovesOf(sfen);
    expect(attack).toContain("6f5e");
    expect(defense).toContain("6f5e");
  });

  it("sideZoneRadius を変えると分け方が変わる(値を WHATIF_VALUES から読んでいることの確認、v1 の決め方): 王手にならない銀の手(3b4a)は、半径 0 では攻めから消える", () => {
    const sfen = "4k4/6S2/9/9/9/9/9/9/4K4 b - 1";
    expect(sideMovesOf(sfen).attack).toContain("3b4a"); // 既定(半径 2・v2)では入る(tagsOf の attack(oppKingZone のみ)の試験と同じ局面)
    // STEP WHATIF 作業 4: sideZoneRadius だけを 0 にしても、既定(v2)では 3b4a は oppKingZone3(相手玉から 3
    // マス以内。attackZoneRadius は固定 3 のまま変わらない)で依然 attack に入ってしまう。この試験は
    // 「sideZoneRadius だけで攻めが決まる v1 の決め方」を確かめる試験なので、sideVersion: 1 を明示して読む。
    const values: WhatifValues = { ...WHATIF_VALUES, sideZoneRadius: 0, sideVersion: 1 };
    expect(sideMovesOf(sfen, values).attack).not.toContain("3b4a");
  });

  it("平手初形(7g7f 等)は、王手にも玉のそばにもならないのでどちらの側にも入らない", () => {
    const { attack, defense } = sideMovesOf(INIT);
    expect(attack).not.toContain("7g7f");
    expect(defense).not.toContain("7g7f");
  });
});

describe("whatifSceneOf・sceneReadPlies・whatifSceneReadSummaryOf", () => {
  const sfen = "4k4/9/9/4N4/9/9/4G4/9/4K4 b - 1";
  const fakeReaderOf = (calls: Array<{ sfen: string; moves: readonly string[]; nodes: number }>, resultFor: (moves: readonly string[]) => WhatifSideReadResult | null): WhatifSideReader => {
    return async (s, moves, nodes) => {
      calls.push({ sfen: s, moves, nodes });
      return resultFor(moves);
    };
  };

  it("側ごとに、その側の手だけを reader に渡す(moves が側の手のみ)", async () => {
    const calls: Array<{ sfen: string; moves: readonly string[]; nodes: number }> = [];
    const reader = fakeReaderOf(calls, (moves) => ({ move: moves[0]!, scoreCp: 10, mate: null, pv: [moves[0]!] }));
    await whatifSceneOf(17, sfen, reader);
    expect(calls).toHaveLength(2);
    const { attack, defense } = sideMovesOf(sfen);
    expect(new Set(calls[0]!.moves)).toEqual(new Set(attack));
    expect(new Set(calls[1]!.moves)).toEqual(new Set(defense));
    expect(calls.every((c) => c.nodes === WHATIF_VALUES.sideNodes)).toBe(true);
  });

  it("nodes は WHATIF_VALUES.sideNodes から読む(値を変える変異で赤くなることの確認)", async () => {
    const calls: Array<{ sfen: string; moves: readonly string[]; nodes: number }> = [];
    const reader = fakeReaderOf(calls, (moves) => ({ move: moves[0]!, scoreCp: 10, mate: null, pv: [moves[0]!] }));
    const values: WhatifValues = { ...WHATIF_VALUES, sideNodes: 12345 };
    await whatifSceneOf(17, sfen, reader, values);
    expect(calls.every((c) => c.nodes === 12345)).toBe(true);
  });

  it("両方の側に合法手があり、reader が両方とも見つければ found・found、sideGapCp は差", async () => {
    const reader: WhatifSideReader = async (_s, moves) =>
      moves.includes("5d4b+") ? { move: "5d4b+", scoreCp: 300, mate: null, pv: ["5d4b+"] } : { move: "5g5h", scoreCp: 100, mate: null, pv: ["5g5h"] };
    const scene = await whatifSceneOf(17, sfen, reader);
    expect(scene.attack).toEqual({ state: "found", result: { move: "5d4b+", scoreCp: 300, mate: null, pv: ["5d4b+"] } });
    expect(scene.defense).toEqual({ state: "found", result: { move: "5g5h", scoreCp: 100, mate: null, pv: ["5g5h"] } });
    expect(scene.sideGapCp).toBe(200);
  });

  it("その側に合法手が無ければ、reader を呼ばずに noLegalMove(呼ばれた回数は守りの側の 1 回だけ)", async () => {
    // 玉と金だけ(攻めの側になる手が無い局面)
    const noAttackSfen = "4k4/9/9/9/9/9/4G4/9/4K4 b - 1";
    const { attack: attackMoves } = sideMovesOf(noAttackSfen);
    expect(attackMoves).toEqual([]); // この局面の前提(攻めの側の合法手が無いこと)を、この試験自身で確かめる
    let readerCalls = 0;
    const reader: WhatifSideReader = async (_s, moves) => {
      readerCalls += 1;
      return { move: moves[0]!, scoreCp: 0, mate: null, pv: [moves[0]!] };
    };
    const scene = await whatifSceneOf(17, noAttackSfen, reader);
    expect(scene.attack).toEqual({ state: "noLegalMove" });
    expect(scene.defense.state).toBe("found");
    expect(readerCalls).toBe(1); // 守りの側の 1 回だけ(攻めの側では呼ばれない)
  });

  it("reader が null を返せば notMeasured(合法手はあった)", async () => {
    const reader: WhatifSideReader = async () => null;
    const scene = await whatifSceneOf(17, sfen, reader);
    expect(scene.attack).toEqual({ state: "notMeasured" });
    expect(scene.defense).toEqual({ state: "notMeasured" });
    expect(scene.sideGapCp).toBeNull();
  });

  it("sceneReadPlies: fork・narrowHeld・chanceHeld のいずれか、または biggestFork の手数(重複なし・昇順)", () => {
    const forkOnly = initPosition([1000, 400], "2g2f", null, { ply: 17 }); // fork(差 600)
    const narrowOnly = initPosition([1000, 600], "7g7f", null, { ply: 19 }); // narrowHeld
    const neither = initPosition([1000, 999], "7g7f", null, { ply: 21 }); // どれでもない
    const summary = whatifGameSummaryOf([forkOnly, narrowOnly, neither]);
    // biggestFork は差が最大の forkOnly(600)になるはず(neither の差は 1)
    expect(summary.biggestFork?.ply).toBe(17);
    expect(sceneReadPlies([forkOnly, narrowOnly, neither], summary)).toEqual([17, 19]);
  });

  it("sceneReadPlies: biggestFork が fork・narrowHeld・chanceHeld のどれでもない場合でも足す", () => {
    // 実戦の手(2g2f)は候補にあり、差 1(fork の閾値 600 未満)。1 局面だけの対局:
    // biggestFork には出るが、fork/narrowHeld(第 1 候補でない)/chanceHeld(第 1 候補でない)のどれでもない。
    const p = initPosition([1000, 999], "2g2f", null, { ply: 17 });
    expect(p.actualRank).toBe(2);
    const summary = whatifGameSummaryOf([p]);
    expect(summary.scenes).toEqual({ fork: [], narrowHeld: [], chanceHeld: [] });
    expect(summary.biggestFork?.ply).toBe(17);
    expect(sceneReadPlies([p], summary)).toEqual([17]);
  });

  it("whatifSceneReadSummaryOf: 場面の数・側ごとに合法手が無かった数・両方が見つかった数", async () => {
    const foundReader: WhatifSideReader = async (_s, moves) => ({ move: moves[0]!, scoreCp: 0, mate: null, pv: [moves[0]!] });
    const bothFound = await whatifSceneOf(17, sfen, foundReader); // 攻め・守りとも合法手あり → 両方 found
    const noAttackSfen = "4k4/9/9/9/9/9/4G4/9/4K4 b - 1";
    const attackMissing = await whatifSceneOf(19, noAttackSfen, foundReader); // 攻めの側は noLegalMove
    const summary = whatifSceneReadSummaryOf([bothFound, attackMissing]);
    expect(summary).toEqual({ scenesRead: 2, attackNoLegalMoveCount: 1, defenseNoLegalMoveCount: 0, bothFoundCount: 1 });
  });
});

// ---- 本人の手番の局面の一覧(CLI のループを、エンジンを起こさずに試験するため) ----

describe("userTurnsOf", () => {
  it("1, 3, 5, … 手目(本人の手番)だけを、指す前の sfen とともに拾う", () => {
    const moves = ["7g7f", "3c3d", "2g2f", "8c8d"];
    const afterTwo = applyMove(applyMove(INIT, "7g7f"), "3c3d");
    expect(userTurnsOf(INIT, moves)).toEqual([
      { ply: 1, sfen: INIT, move: "7g7f" },
      { ply: 3, sfen: afterTwo, move: "2g2f" },
    ]);
  });

  it("手数が 1(本人の手で終わる棋譜)でも、その 1 手を拾う", () => {
    expect(userTurnsOf(INIT, ["7g7f"])).toEqual([{ ply: 1, sfen: INIT, move: "7g7f" }]);
  });

  it("手が無ければ空", () => {
    expect(userTurnsOf(INIT, [])).toEqual([]);
  });
});

describe("evaluableTurns", () => {
  it("startPly より前は読まない(既定 17)", () => {
    const turns = [
      { ply: WHATIF_VALUES.startPly - 1, sfen: INIT, move: "7g7f" },
      { ply: WHATIF_VALUES.startPly, sfen: INIT, move: "7g7f" },
    ];
    expect(evaluableTurns(turns).map((t) => t.ply)).toEqual([WHATIF_VALUES.startPly]);
  });

  it("startPly を変えると境も変わる(値を WHATIF_VALUES から読んでいることの確認)", () => {
    const turns = [
      { ply: 5, sfen: INIT, move: "7g7f" },
      { ply: 7, sfen: INIT, move: "7g7f" },
    ];
    const values: WhatifValues = { ...WHATIF_VALUES, startPly: 7 };
    expect(evaluableTurns(turns, values).map((t) => t.ply)).toEqual([7]);
  });

  it("終局の局面は読まない", () => {
    expect(isGameOver(SENTE_CHECKMATED_SFEN)).toBe(true);
    const turns = [{ ply: WHATIF_VALUES.startPly, sfen: SENTE_CHECKMATED_SFEN, move: "7g7f" }];
    expect(evaluableTurns(turns)).toEqual([]);
  });

  it("王手中(終局でない)の局面は読む", () => {
    expect(isInCheck(SENTE_IN_CHECK_SFEN, "sente")).toBe(true);
    expect(isGameOver(SENTE_IN_CHECK_SFEN)).toBe(false);
    const turns = [{ ply: WHATIF_VALUES.startPly, sfen: SENTE_IN_CHECK_SFEN, move: "5i4h" }];
    expect(evaluableTurns(turns)).toEqual(turns);
  });
});

// ---- 手数の表し方(監査 REVISE、2026-09-22) ----

describe("withDisplayPly", () => {
  it("先手の局(plyOffset 0): displayPly = ply", () => {
    expect(withDisplayPly({ ply: 17 }, 0)).toEqual({ ply: 17, displayPly: 17 });
  });

  it("mirrored の局(plyOffset 1): displayPly = ply + 1", () => {
    expect(withDisplayPly({ ply: 17 }, 1)).toEqual({ ply: 17, displayPly: 18 });
  });

  it("ply 以外の欄はそのまま残る(position・scene・biggestFork のどれにも使える形)", () => {
    expect(withDisplayPly({ ply: 79, lossValue: 568, lossCp: 568, lossIsLowerBound: false }, 1)).toEqual({
      ply: 79,
      lossValue: 568,
      lossCp: 568,
      lossIsLowerBound: false,
      displayPly: 80,
    });
  });
});
