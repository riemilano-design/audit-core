// STEP WHATIF 作業 1(docs/STEP_WHATIF_PLAN_2026-09-22.md §2.1・§2.2・§2.4・§2.5)。
// 「重要な局面の分かれ道」を測る段の純粋関数。**測る段だけ**(見せる段(PDF・Web、計画 §2.3)は別の作業。ここでは作らない)。
//
// 【追記(STEP WHATIF 作業 4、計画 §9)】攻めの側の決め方の v2(§9.3)を足した。v1(相手玉から sideZoneRadius
// マス以内 または 王手)に加え、v2(既定の sideVersion)は「相手の駒を取る」「動かした駒が相手玉のそば
// (hitsDefenderRadius マス以内)の相手の駒(玉以外)に当たる」「行き先が相手玉から attackZoneRadius マス以内」を
// 足す(いずれか 1 つでも真なら攻めの側)。守りの側は変えない(本人の指摘は攻めの側だけ ― §9.1)。
// `WHATIF_VALUES.sideVersion` の既定は 2(v2)。`sideVersion: 1` を渡せば v1 と同じ結果になる。
//
// 【このファイルがやること】
// - 1 局面(本人の手番、根は先手番。記録は「本人 = 先手」にそろえてある ― lib/sideAlignment.ts)について、
//   エンジンの MultiPV 結果(呼び出し側が渡す。ここではエンジンを呼ばない)と実戦の手から、候補・実戦の手の順位・
//   第 1 と第 2 候補の差を組み立てる
// - 候補・実戦の手に、行き先だけで決まる印(oppKingZone / ownKingZone / givesCheck / kingMove)を付ける。
//   王手になるかどうか・玉を動かす手かどうかは既存の関数(lib/moveFacts.ts の moveFactsOf・apps/server の isInCheck)を
//   呼ぶだけ。玉のそばかどうかは **この段だけの決め方**(玉から `sideZoneRadius` マス以内。§2.5)で、
//   `moveFactsOf`・`POSITION_FACTS_RULES`(Gate・基準値が使う 8 マスの決め方)は変えない
// - 拾う場面 3 種類(fork・narrowHeld・chanceHeld、計画 §2.2)と、1 局に 1 つのいちばん大きな分かれ道(§2.4-1)を出す
// - **場面の局面だけ**(fork・narrowHeld・chanceHeld のどれか、または biggestFork)、合法手を全部出して攻めの側・
//   守りの側に分け、側ごとに(その側の手だけを渡す reader を通して)読んだ最上位を組む(§2.5。2 巡目)
// - 本人の手番の局面の一覧(userTurnsOf)と、startPly・終局を外す絞り込み(evaluableTurns)。**エンジンを呼ばない**
//   ので、CLI(whatif.ts)側のループの「どの局面を読むか」を、エンジンを起こさずに試験できる
//
// 【手数の表し方について(監査 REVISE、2026-09-22)】`ply` は**畳んだ後の記録の手数**である(本人が後手の局は
// lib/sideAlignment.ts で 180 度回して 1 手目を開始局面に畳んであるため、回した局では元の棋譜の手数と 1 ずれる)。
// **人に見せる・報告する手数は `displayPly`(= ply + plyOffset)を使うこと。** `withDisplayPly` が
// `lib/reportData.ts` の `displayPlyOf`(既存・確定済み)をそのまま呼んで足す(二重に実装しない)。
//
// 【このファイルが絶対にやらないこと】
// - エンジンを起動すること・子プロセスを起こすこと(CLI(scripts/playtest/whatif.ts)の役目。
//   側ごとの読みも `WhatifSideReader` を呼ぶだけで、ここでは USI を話さない)
// - 「攻め・守り」の役割を局面の意味から判定すること(印は行き先だけで決まる。計画 §2.1・§2.5)
// - 手のねらい・わけ・良し悪しの文を作ること。第 1 候補を「正解」と呼ぶこと(計画 5.)
// - ファイルの読み書き
//
// 【判断的知識】WHATIF_VALUES(multiPv・nodes・startPly・minLossCp・narrowGapCp・riseCp・pvMoves・
// sideZoneRadius・sideNodes・sideVersion・hitsDefenderRadius・attackZoneRadius)は計画の仮置きの値であり、
// 将棋一般の閾値ではない(2026-09-22、司令塔 e3。計画 §2.1・§2.2・§2.5・§9.3)。承認前の draft 相当。
// **この値を顧客の文に数として出さないこと。**(2026-09-26。司令塔の申し送り。冊子の ② の母集団の説明に
// `minLossCp` の 600 を「第一候補より 600 点以上下がった場面」と書きかけて止めた ― 承認前の draft 相当の値が
// 将棋一般の基準のように読める。母集団は「候補 5 つの中に無かった、または第一候補より大きく下がった場面」の
// ように語で書く。数で書くなら「この診断では 600 点以上を『大きく』としています」と添える。
// 経緯は docs/LANE_DIAG_LOG_2026-09.md §12.13。)
// `sideZoneRadius` = 2 は §2.4-3 の実測(候補 5 つの中に攻め・守りの両方が見つかった局面が 4/85)を受けて、
// 8 マス(1 マス以内)から広げた値(§2.5)。`sideVersion` = 2(既定)・`hitsDefenderRadius` = 2・
// `attackZoneRadius` = 3 は §9.2 の下見(第 1 候補の 53% が v1 で「なし」だった)を受けた決め方 v2(§9.3)。

import { attacks } from "shogiops/attacks";
import type { Color, Square } from "shogiops/types";
import { opposite, parseUsi, squareDist } from "shogiops/util";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { isGameOver, isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import { getLegalMoves } from "../../../apps/server/src/rules/legalMoves.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { POSITION_FACTS_RULES } from "./counterfactual.js";
import { moveFactsOf } from "./moveFacts.js";
import { displayPlyOf } from "./reportData.js";

/** 判断的知識の仮置き(計画 §2.1・§2.2・§2.4・§2.5)。ここに 1 か所だけ置き、出力の出どころ(meta 行)へそのまま写す。 */
export const WHATIF_VALUES = {
  /** MultiPV の本数(K) */
  multiPv: 5,
  /** 1 局面あたりの探索ノード数(候補 K 個の読み) */
  nodes: 1_000_000,
  /** この手数(本人の手番、1 手目から数えて)から読む。序盤は飛ばす */
  startPly: 17,
  /** 分かれ道(下がった側)。実戦の手が第 1 候補よりこれ以上低ければ拾う */
  minLossCp: 600,
  /** 指せる手が少なかった局面。第 1 候補と第 2 候補の差がこれ以上なら拾う */
  narrowGapCp: 400,
  /** 相手の手の後の機会。直前の本人の手番からの第 1 候補の評価の上がりがこれ以上なら拾う */
  riseCp: 400,
  /** 読み筋を出す手数(先頭から) */
  pvMoves: 7,
  /** 攻め・守りの「玉のそば」の広さ(玉から何マス以内か。縦横斜めの大きいほうで数える ― shogiops の squareDist)。
   * §2.4-3 の実測(8 マスでは両方が見つかる局面が 4/85)を受けて 2 に広げた(§2.5)。 */
  sideZoneRadius: 2,
  /** 場面ごとの側の読み(searchmoves で絞った読み)のノード数 */
  sideNodes: 1_000_000,
  /** 攻め・守りの決め方のバージョン(1 = 従来、2 = 取る・守り駒に当てる・3 マス以内を足す。計画 §9.3)。既定は 2。 */
  sideVersion: 2,
  /** v2: 「動かした駒が相手の駒に当たる」を数える半径(相手玉から何マス以内の相手の駒か。玉自身は含まない)。 */
  hitsDefenderRadius: 2,
  /** v2: 行き先が相手玉から何マス以内なら攻めの側に入れるか(v1 の sideZoneRadius より広い)。 */
  attackZoneRadius: 3,
} as const;

export type WhatifValues = { readonly [K in keyof typeof WHATIF_VALUES]: number };

/**
 * Gate(`lib/gate.ts`)・基準値(`baselineTable.ts` の軸 C)が使う「玉のそば」の広さ(玉の升 + 8 近傍 = 1 マス以内。
 * `lib/positionFacts.ts`・`lib/moveFacts.ts` の `king_and_eight_neighbors`、D2.5 の人間承認 2026-09-15)。
 * **この段では判定に使わない**(値を写すだけ。出力の出どころに「この段と Gate・基準値では広さが違う」ことを残すため。§2.5 の 3.)。
 */
export const GATE_AND_BASELINE_KING_ZONE_RADIUS = 1;

// ---- 印(行き先だけで決まる) ----

export interface WhatifMoveTags {
  /** 相手玉から sideZoneRadius マス以内へ動かす手 */
  oppKingZone: boolean;
  /** 自玉から sideZoneRadius マス以内へ動かす手。玉自身の手は含まない */
  ownKingZone: boolean;
  /** 指した後、相手が王手を受ける手か */
  givesCheck: boolean;
  /** 玉を動かす手か */
  kingMove: boolean;
  /** v2(§9.3): 相手の駒を取る手か */
  captures: boolean;
  /** v2: 指した後、動かした駒が相手玉から hitsDefenderRadius マス以内の相手の駒(玉以外)に当たるか
   * (shogiops の `attacks(piece, to, occupied)` で数える)。 */
  hitsOppKingZonePiece: boolean;
  /** v2: 行き先が相手玉から attackZoneRadius マス以内か(v1 の oppKingZone より広い決め方)。 */
  oppKingZone3: boolean;
}

export type WhatifSide = "attack" | "defense" | "both" | "none";

/**
 * 攻めの側・守りの側(計画 §2.1・§2.5・§9.3)。守りの側は v1 のまま(ownKingZone または kingMove)。
 * 攻めの側は `values.sideVersion` で切り替える:
 * - v1: oppKingZone または givesCheck
 * - v2(既定): v1 ∪ captures ∪ hitsOppKingZonePiece ∪ oppKingZone3
 * 両方に当たれば both。
 */
export function sideOf(tags: WhatifMoveTags, values: WhatifValues = WHATIF_VALUES): WhatifSide {
  const attackV1 = tags.oppKingZone || tags.givesCheck;
  const attack = values.sideVersion === 2 ? attackV1 || tags.captures || tags.hitsOppKingZonePiece || tags.oppKingZone3 : attackV1;
  const defense = tags.ownKingZone || tags.kingMove;
  if (attack && defense) return "both";
  if (attack) return "attack";
  if (defense) return "defense";
  return "none";
}

/**
 * v2(§9.3): 指した後の盤で、動かした駒(`movedTo` の升の駒)が、相手玉(`oppKing`)から `radius` マス以内の
 * 相手の駒(玉自身は含まない)のどれかに当たるか。shogiops の `attacks(piece, square, occupied)` で、動かした駒
 * 1 枚の利きを求め、区域内の相手の駒と重なるかを見る(`lib/moveFacts.ts` の `reachInZone` と同じ考え方)。
 */
function hitsOppKingZonePieceOf(afterSfen: string, opp: Color, oppKing: Square, movedTo: Square, radius: number): boolean {
  const after = parsePosition(afterSfen);
  const movedPiece = after.board.get(movedTo);
  if (movedPiece === undefined) return false; // 起こらない想定(指した後の升に駒が無いことはない)
  const attacked = attacks(movedPiece, movedTo, after.board.occupied);
  for (const square of after.board.color(opp)) {
    if (square === oppKing) continue;
    if (squareDist(square, oppKing) > radius) continue;
    if (attacked.has(square)) return true;
  }
  return false;
}

/**
 * `sfen` の局面(本人の手番)で `moveUsi` を指したときの印(計画 §2.5 の 2.・§9.3)。
 * - 玉を動かす手か・合法性の確認は `lib/moveFacts.ts` の `moveFactsOf`(D2.6 で確定済み)をそのまま呼ぶ
 *   (`kingMove` は区域の規則に依らない欄なので、8 マスの `POSITION_FACTS_RULES` を渡しても値は変わらない)
 * - 玉のそばかどうかは、この段だけの決め方(`squareDist` ≤ `values.sideZoneRadius`/`values.attackZoneRadius`)。
 *   既存の 1 マスの関数(`moveFactsOf` の `toInOwnKingZone`/`toInOpponentKingZone`)には引数を足さず、ここで別に計算する
 * - 王手になるかどうかは `isInCheck` を薄く重ねる(moveFactsOf は持たない欄)
 * - v2 の印(captures・hitsOppKingZonePiece・oppKingZone3)は `sideVersion` に関わらず常に計算する(`sideOf` 側で
 *   使うかどうかを分ける。値がずれていても印そのものは事実として一定にするため)
 * 合法でない手・読めない手は moveFactsOf / applyMove が例外を投げる。
 */
export function tagsOf(sfen: string, moveUsi: string, values: WhatifValues = WHATIF_VALUES): WhatifMoveTags {
  const facts = moveFactsOf(sfen, moveUsi, POSITION_FACTS_RULES);
  const move = parseUsi(moveUsi)!; // moveFactsOf が合法性・読めることを確かめ済み(例外で先に止まる)
  const pos = parsePosition(sfen);
  const own = pos.turn;
  const opp = opposite(own);
  const ownKing = pos.board.pieces(own, "king").first();
  const oppKing = pos.board.pieces(opp, "king").first();
  const oppNear = oppKing !== undefined && squareDist(move.to, oppKing) <= values.sideZoneRadius;
  const ownNear = ownKing !== undefined && squareDist(move.to, ownKing) <= values.sideZoneRadius;
  const after = applyMove(sfen, moveUsi);
  return {
    oppKingZone: oppNear,
    ownKingZone: ownNear && !facts.kingMove,
    givesCheck: isInCheck(after, opp),
    kingMove: facts.kingMove,
    captures: facts.capturedRole !== null,
    hitsOppKingZonePiece: oppKing !== undefined && hitsOppKingZonePieceOf(after, opp, oppKing, move.to, values.hitsDefenderRadius),
    oppKingZone3: oppKing !== undefined && squareDist(move.to, oppKing) <= values.attackZoneRadius,
  };
}

// ---- 候補・局面 ----

/** エンジンの MultiPV の 1 本を、この段が読む分だけに絞った形(CLI が MultiPvLine から作る)。 */
export interface WhatifEngineLine {
  scoreCp: number | null;
  mate: number | null;
  /** 読み筋(USI の手の列)。先頭が候補の手。 */
  pv: readonly string[];
}

export interface WhatifCandidate {
  move: string;
  scoreCp: number | null;
  mate: number | null;
  /** 読み筋の先頭 `pvMoves` 手 */
  pv: string[];
  tags: WhatifMoveTags;
  side: WhatifSide;
}

/**
 * 評価を 1 本の数直線に乗せる(cp と mate を比べるため)。cp はそのまま。mate は
 * cp の取り得る範囲の外側の値にして、勝ちの詰みはどんな cp よりも高く・負けの詰みは
 * どんな cp よりも低くする(詰みまでの手数が短いほど、勝ちはより高く・負けはより低い ―
 * エンジンの通常の並び順と同じ)。**表示用の値ではない**(呼び出し側には出さない。
 * 場面を拾う・biggestFork を選ぶための内部の比べ方だけに使う)。
 */
const MATE_SENTINEL = 1_000_000;
export function evalValueOf(candidate: { scoreCp: number | null; mate: number | null }): number | null {
  if (candidate.scoreCp !== null) return candidate.scoreCp;
  if (candidate.mate !== null) return candidate.mate > 0 ? MATE_SENTINEL - candidate.mate : -MATE_SENTINEL - candidate.mate;
  return null;
}

/** `lines` から候補を作る(読み筋の先頭が無い行は除く)。順序はそのまま(呼び出し側が MultiPV の順で渡す)。 */
export function candidatesOf(sfen: string, lines: readonly WhatifEngineLine[], values: WhatifValues = WHATIF_VALUES): WhatifCandidate[] {
  const candidates: WhatifCandidate[] = [];
  for (const line of lines) {
    const move = line.pv[0];
    if (move === undefined) continue;
    const tags = tagsOf(sfen, move, values);
    candidates.push({ move, scoreCp: line.scoreCp, mate: line.mate, pv: line.pv.slice(0, values.pvMoves), tags, side: sideOf(tags, values) });
  }
  return candidates;
}

/** 実戦の手が候補の中で何番目か(1 始まり)。無ければ null。 */
export function actualRankOf(candidates: readonly WhatifCandidate[], actualMove: string): number | null {
  const index = candidates.findIndex((c) => c.move === actualMove);
  return index === -1 ? null : index + 1;
}

/** 第 1 候補と第 2 候補の差。どちらかが詰み・候補が 2 未満なら null(計画 §2.1「1 局面の出力」)。 */
export function topGapCpOf(candidates: readonly WhatifCandidate[]): number | null {
  const c0 = candidates[0];
  const c1 = candidates[1];
  if (c0 === undefined || c1 === undefined) return null;
  if (c0.mate !== null || c1.mate !== null) return null;
  if (c0.scoreCp === null || c1.scoreCp === null) return null;
  return c0.scoreCp - c1.scoreCp;
}

export interface WhatifLoss {
  /** 比べる内部の値(evalValueOf の差。cp 同士ならそのまま cp の差、詰みが絡めば大きな値)。場面を拾う・biggestFork の比べに使う */
  value: number;
  /** cp 同士のときだけの実際の cp 差(詰みが絡めば null。冊子に出せるのはこちらの意味の値)。 */
  cpValue: number | null;
  /** 実戦の手が候補 K に無く、「第 K 候補との差」を下限として使ったか(計画 §2.4-1) */
  isLowerBound: boolean;
}

/**
 * 第 1 候補と、実戦の手(見つかればその順位、見つからなければ最後の候補=第 K 候補)との差。
 * 実戦の手が候補に無いときの差は「第 K 候補との差以上」として扱う(計画 §2.4-1)。候補が無ければ null。
 */
export function lossOf(candidates: readonly WhatifCandidate[], actualRank: number | null): WhatifLoss | null {
  const c0 = candidates[0];
  if (c0 === undefined) return null;
  const v0 = evalValueOf(c0);
  if (v0 === null) return null;
  const compareTo = actualRank !== null ? candidates[actualRank - 1] : candidates[candidates.length - 1];
  if (compareTo === undefined) return null;
  const vCompare = evalValueOf(compareTo);
  if (vCompare === null) return null;
  const bothCp = c0.scoreCp !== null && compareTo.scoreCp !== null;
  return {
    value: v0 - vCompare,
    cpValue: bothCp ? c0.scoreCp! - compareTo.scoreCp! : null,
    isLowerBound: actualRank === null,
  };
}

/** 分かれ道(下がった側、計画 §2.2 の表 1 行目)。実戦の手が候補に無い、または詰みも含めた比べ方で minLossCp 以上低い。 */
function isFork(loss: WhatifLoss | null, actualRank: number | null, values: WhatifValues): boolean {
  if (actualRank === null) return true;
  if (loss === null) return false;
  return loss.value >= values.minLossCp;
}

/** 指せる手が少なかった局面(計画 §2.2 の表 2 行目)。実戦の手 = 第 1 候補、かつ第 1 と第 2 の差(どちらも詰みでない)が narrowGapCp 以上。 */
function isNarrowHeld(candidates: readonly WhatifCandidate[], actualRank: number | null, values: WhatifValues): boolean {
  if (actualRank !== 1) return false;
  const gap = topGapCpOf(candidates);
  return gap !== null && gap >= values.narrowGapCp;
}

/**
 * 相手の手の後の機会(計画 §2.2 の表 3 行目)。直前の本人の手番からの第 1 候補の評価の上がりが riseCp 以上、
 * かつ実戦の手 = 第 1 候補。`previousCandidate0Value` が無い(この局面より前に読んだ本人の手番が無い)ときは false。
 */
function isChanceHeld(candidates: readonly WhatifCandidate[], actualRank: number | null, previousCandidate0Value: number | null, values: WhatifValues): boolean {
  if (actualRank !== 1) return false;
  if (previousCandidate0Value === null) return false;
  const c0 = candidates[0];
  if (c0 === undefined) return false;
  const v0 = evalValueOf(c0);
  if (v0 === null) return false;
  return v0 - previousCandidate0Value >= values.riseCp;
}

export interface WhatifPositionInput {
  ply: number;
  sfen: string;
  actualMove: string;
  lines: readonly WhatifEngineLine[];
  /** 直前に読んだ本人の手番の局面の第 1 候補の評価(evalValueOf)。無ければ null(chanceHeld は常に false になる)。 */
  previousCandidate0Value: number | null;
}

export interface WhatifPosition {
  ply: number;
  sfen: string;
  candidates: WhatifCandidate[];
  actualMove: string;
  actualTags: WhatifMoveTags;
  actualSide: WhatifSide;
  actualRank: number | null;
  topGapCp: number | null;
  loss: WhatifLoss | null;
  scenes: { fork: boolean; narrowHeld: boolean; chanceHeld: boolean };
  /** 次の局面の previousCandidate0Value に渡す値(候補が無ければ null)。 */
  candidate0Value: number | null;
}

/**
 * 1 局面ぶんの記録を組む(計画 §2.1・§2.2・§2.4)。エンジンは呼ばない(呼び出し側が MultiPV の結果を渡す)。
 * **攻めの側・守りの側の最上位はここでは出さない**(候補 K の中から拾うやり方は §2.4-3 の実測で成り立たないと
 * 分かったため、§2.5 のとおり場面の局面だけ・合法手全部から側ごとに読む形へ変えた。`whatifSceneOf` 参照)。
 */
export function whatifPositionOf(input: WhatifPositionInput, values: WhatifValues = WHATIF_VALUES): WhatifPosition {
  const candidates = candidatesOf(input.sfen, input.lines, values);
  const actualTags = tagsOf(input.sfen, input.actualMove, values);
  const actualSide = sideOf(actualTags, values);
  const actualRank = actualRankOf(candidates, input.actualMove);
  const loss = lossOf(candidates, actualRank);
  const topGapCp = topGapCpOf(candidates);
  const c0 = candidates[0];
  const candidate0Value = c0 !== undefined ? evalValueOf(c0) : null;
  return {
    ply: input.ply,
    sfen: input.sfen,
    candidates,
    actualMove: input.actualMove,
    actualTags,
    actualSide,
    actualRank,
    topGapCp,
    loss,
    scenes: {
      fork: isFork(loss, actualRank, values),
      narrowHeld: isNarrowHeld(candidates, actualRank, values),
      chanceHeld: isChanceHeld(candidates, actualRank, input.previousCandidate0Value, values),
    },
    candidate0Value,
  };
}

// ---- 1 局ごとのまとめ(計画 §2.2 の最後・§2.4-1) ----

export interface WhatifBiggestFork {
  ply: number;
  lossValue: number;
  lossCp: number | null;
  lossIsLowerBound: boolean;
}

export interface WhatifGameSummary {
  /** 読んだ(本人の手番の)局面の数 */
  positionsRead: number;
  /** 実戦の手が第 1 候補と同じだった数 */
  matchesTop1: number;
  /** 実戦の手が候補 K 位以内だった数 */
  withinMultiPv: number;
  /** 1 局に 1 つ、差が最大の手(§2.4-1)。読んだ局面が 0 なら null */
  biggestFork: WhatifBiggestFork | null;
  /** 拾った場面(§2.2)の手数の一覧。1 つの局面が複数の種類に当たることがある(それぞれの配列に入る)。 */
  scenes: {
    fork: number[];
    narrowHeld: number[];
    chanceHeld: number[];
  };
}

/** 1 局ぶんの `WhatifPosition` の列から、まとめを作る(計画 §2.2 の最後・§2.4-1)。 */
export function whatifGameSummaryOf(positions: readonly WhatifPosition[]): WhatifGameSummary {
  let biggestFork: WhatifBiggestFork | null = null;
  for (const p of positions) {
    if (p.loss === null) continue;
    if (biggestFork === null || p.loss.value > biggestFork.lossValue) {
      biggestFork = { ply: p.ply, lossValue: p.loss.value, lossCp: p.loss.cpValue, lossIsLowerBound: p.loss.isLowerBound };
    }
  }

  return {
    positionsRead: positions.length,
    matchesTop1: positions.filter((p) => p.actualRank === 1).length,
    withinMultiPv: positions.filter((p) => p.actualRank !== null).length,
    biggestFork,
    scenes: {
      fork: positions.filter((p) => p.scenes.fork).map((p) => p.ply),
      narrowHeld: positions.filter((p) => p.scenes.narrowHeld).map((p) => p.ply),
      chanceHeld: positions.filter((p) => p.scenes.chanceHeld).map((p) => p.ply),
    },
  };
}

// ---- 場面ごとの側の読み(計画 §2.5。1 巡目(候補 K・biggestFork)が終わってから、2 巡目として回す) ----

/** その局面の合法手すべてを、攻めの側・守りの側に分ける(`sideOf` と同じ決め方。両方に当たる手は両方に入る)。 */
export function sideMovesOf(sfen: string, values: WhatifValues = WHATIF_VALUES): { attack: string[]; defense: string[] } {
  const attack: string[] = [];
  const defense: string[] = [];
  for (const move of getLegalMoves(sfen)) {
    const side = sideOf(tagsOf(sfen, move, values), values);
    if (side === "attack" || side === "both") attack.push(move);
    if (side === "defense" || side === "both") defense.push(move);
  }
  return { attack, defense };
}

export interface WhatifSideReadResult {
  move: string;
  scoreCp: number | null;
  mate: number | null;
  pv: string[];
}

/**
 * `moves`(その側の合法手だけ)に絞って読む関数。CLI(scripts/playtest/whatif.ts)が
 * `go nodes <nodes> searchmoves <moves…>`(MultiPV 1)を話す本物のエンジンで実装する。
 * ここでは呼ぶだけで、エンジンは起こさない(試験は差し替える)。`moves` が空のときは呼ばない
 * (`sideReadOf` が先に `noLegalMove` を返す)。読めなかった(例外・タイムアウト)場合は null。
 */
export type WhatifSideReader = (sfen: string, moves: readonly string[], nodes: number) => Promise<WhatifSideReadResult | null>;

export type WhatifSideRead =
  | { state: "found"; result: WhatifSideReadResult }
  /** その側に合法手が無い(§2.5) */
  | { state: "noLegalMove" }
  /** 合法手はあったが、reader が測れなかった(エンジンの例外・タイムアウト。計画に無い状態だが、
   * 「測れなかった」を「無い」と混ぜない ― lib/checkBaseline.ts 等と同じ考え方) */
  | { state: "notMeasured" };

async function sideReadOf(sfen: string, moves: readonly string[], reader: WhatifSideReader, nodes: number): Promise<WhatifSideRead> {
  if (moves.length === 0) return { state: "noLegalMove" };
  const result = await reader(sfen, moves, nodes);
  if (result === null) return { state: "notMeasured" };
  return { state: "found", result };
}

export interface WhatifScene {
  ply: number;
  attack: WhatifSideRead;
  defense: WhatifSideRead;
  /** attack − defense(両方 found・cp のときだけ。計画 §2.4-2・§2.5) */
  sideGapCp: number | null;
}

/**
 * 場面(fork・narrowHeld・chanceHeld のどれか、または biggestFork)の局面の手数だけ、昇順・重複なしで返す。
 * biggestFork は 1 巡目(候補 K の読み)がすべて終わってから決まるため、`summary` を受け取って足す(§2.5 の 3.)。
 */
export function sceneReadPlies(positions: readonly WhatifPosition[], summary: WhatifGameSummary): number[] {
  const plies = new Set<number>();
  for (const p of positions) {
    if (p.scenes.fork || p.scenes.narrowHeld || p.scenes.chanceHeld) plies.add(p.ply);
  }
  if (summary.biggestFork !== null) plies.add(summary.biggestFork.ply);
  return [...plies].sort((a, b) => a - b);
}

/** 1 場面ぶんの、側ごとの読みを組む(計画 §2.5)。エンジンは `reader` を通して呼ぶ(ここでは起こさない)。 */
export async function whatifSceneOf(ply: number, sfen: string, reader: WhatifSideReader, values: WhatifValues = WHATIF_VALUES): Promise<WhatifScene> {
  const { attack: attackMoves, defense: defenseMoves } = sideMovesOf(sfen, values);
  const attack = await sideReadOf(sfen, attackMoves, reader, values.sideNodes);
  const defense = await sideReadOf(sfen, defenseMoves, reader, values.sideNodes);
  const sideGapCp =
    attack.state === "found" && defense.state === "found" && attack.result.scoreCp !== null && defense.result.scoreCp !== null
      ? attack.result.scoreCp - defense.result.scoreCp
      : null;
  return { ply, attack, defense, sideGapCp };
}

export interface WhatifSceneReadSummary {
  /** 場面(2 巡目で読んだ局面)の数 */
  scenesRead: number;
  /** 攻めの側に合法手が無かった場面の数 */
  attackNoLegalMoveCount: number;
  /** 守りの側に合法手が無かった場面の数 */
  defenseNoLegalMoveCount: number;
  /** 攻め・守りの両方が読めた(found)場面の数(計画 §2.4-3・§2.5) */
  bothFoundCount: number;
}

/** 場面ごとの側の読みの列から、まとめを作る(計画 §2.5 の 4.・3.)。 */
export function whatifSceneReadSummaryOf(scenes: readonly WhatifScene[]): WhatifSceneReadSummary {
  return {
    scenesRead: scenes.length,
    attackNoLegalMoveCount: scenes.filter((s) => s.attack.state === "noLegalMove").length,
    defenseNoLegalMoveCount: scenes.filter((s) => s.defense.state === "noLegalMove").length,
    bothFoundCount: scenes.filter((s) => s.attack.state === "found" && s.defense.state === "found").length,
  };
}

// ---- 本人の手番の局面の一覧(CLI のループを、エンジンを起こさずに試験するため) ----

export interface WhatifTurn {
  ply: number;
  sfen: string;
  move: string;
}

/**
 * `startSfen` から `moves` をすべて再生し、本人の手番(そろえた記録は先手番。1, 3, 5, … 手目)の局面を一覧にする。
 * startPly の絞り込み・終局の除外はしない(`evaluableTurns` で分ける)。
 */
export function userTurnsOf(startSfen: string, moves: readonly string[]): WhatifTurn[] {
  const turns: WhatifTurn[] = [];
  let sfen = startSfen;
  for (let i = 0; i < moves.length; i++) {
    const move = moves[i]!;
    if (i % 2 === 0) turns.push({ ply: i + 1, sfen, move });
    sfen = applyMove(sfen, move);
  }
  return turns;
}

/** `userTurnsOf` の一覧から、実際に読む局面(startPly 以上・終局でない)だけを残す。 */
export function evaluableTurns(turns: readonly WhatifTurn[], values: WhatifValues = WHATIF_VALUES): WhatifTurn[] {
  return turns.filter((turn) => turn.ply >= values.startPly && !isGameOver(turn.sfen));
}

// ---- 手数の表し方(監査 REVISE、2026-09-22。ファイル冒頭コメント参照) ----

/**
 * `ply`(畳んだ後の記録の手数)を持つ値に `displayPly`(= ply + plyOffset。人に見せる・報告する手数)を足す。
 * `lib/reportData.ts` の `displayPlyOf`(既存・確定済み)をそのまま呼ぶ(二重に実装しない)。
 * `position`・`scene` の行、`summary.biggestFork` のどれにも同じ形で使う(CLI(whatif.ts)が呼ぶ)。
 */
export function withDisplayPly<T extends { ply: number }>(item: T, plyOffset: number): T & { displayPly: number } {
  return { ...item, displayPly: displayPlyOf(item.ply, plyOffset) };
}
