// STEP READ(docs/STEP_READ_PLAN_2026-09-22.md §2・§3)。「読みの間違い」を人を介さずに分解する段の純粋関数。
// **測る段だけ**(見せる段は今回作らない。計画 5.)。対象は STEP WHATIF 作業 4 の v2 jsonl(`whatif-v2/`)の
// うち、`scenes.fork` が true の position 行(分かれ道)だけ(計画「作るもの」冒頭)。
//
// 【このファイルがやること】
// - 2.1 浅い探索でも分かる崩れか: node ラダー(`READ_VALUES.nodeLadder`)の各段について、
//   (a) 第 1 候補の評価(searchmoves 無し)・(b) 実戦の手だけを読ませた評価(searchmoves 実戦の手)の差が
//   `minLossCp` 以上になる最小の段(`firstVisibleNodes`)。エンジンの生の読み(`ReadLadderLevelInput`)を
//   受け取って組む(呼び出し側(CLI)がエンジンを呼ぶ。ここでは呼ばない)。
//   あわせて、いちばん深い段の (b) の読み筋の 2 手目(相手の返し)が、次に相手が実際に指した手と同じか
//   (`opponentReplyMatchesPv`)
// - 2.2 手の性質: 第 1 候補・実戦の手それぞれに、行き先と駒だけで決まる印(`ReadMoveMarks`)を付ける。
//   玉を動かす手か・王手か・取ったかは既存の関数(`lib/moveFacts.ts` の `moveFactsOf`・
//   `apps/server` の `isInCheck`)をそのまま呼ぶ(二重に実装しない)
// - 2.3 見た目: 指した直後の駒の損得(`materialLookOf`)。第 1 候補・実戦の手それぞれについて
// - 1 局ぶんのまとめ(`readGameSummaryOf`): `firstVisibleNodes` の区分・`opponentReplyMatchesPv` の件数・
//   印の種類 × 種類の表・2.3 の 3 件数
//
// 【このファイルが絶対にやらないこと】
// - エンジンを起動すること・子プロセスを起こすこと(CLI(scripts/playtest/read.ts)の役目)
// - 「読みが浅い」「感覚が偏っている」のような断定の文を作ること。分類と件数だけを出す(計画 1.)
// - ファイルの読み書き
//
// 【判断的知識】READ_VALUES(nodeLadder・minLossCp・pieceValues)は計画の仮置きの値であり、
// 将棋一般の閾値ではない(2026-09-22。計画 §2.1・§2.2・§2.3)。承認前の draft 相当。
// `minLossCp` は WHATIF_VALUES.minLossCp と同じ値を参照する(計画「作るもの」1.)。

import { attacks } from "shogiops/attacks";
import type { Color, MoveOrDrop, Square } from "shogiops/types";
import { isDrop, opposite, parseUsi, squareRank } from "shogiops/util";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import { isLegalMove } from "../../../apps/server/src/rules/legalMoves.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { POSITION_FACTS_RULES } from "./counterfactual.js";
import { moveFactsOf, type UserMoveFacts } from "./moveFacts.js";
import { evalValueOf, WHATIF_VALUES } from "./whatif.js";

/** 判断的知識の仮置き(計画 §2.1・§2.2・§2.3)。ここに 1 か所だけ置き、meta 行へそのまま写す。 */
export const READ_VALUES = {
  /** 2.1: 浅い探索から深い探索まで、順に読む段(ノード数)。 */
  nodeLadder: [2_000, 10_000, 50_000, 200_000, 1_000_000] as const,
  /** 2.1: 「分かれ道が見える」とみなす差。WHATIF_VALUES.minLossCp(= 600)と同じ値(計画「作るもの」1.)。 */
  minLossCp: WHATIF_VALUES.minLossCp,
  /** 2.2・2.3: 駒の価値の仮置き(計画「作るもの」2.・3.)。成駒は元の駒 + 1、玉は 0。 */
  pieceValues: {
    pawn: 1,
    lance: 3,
    knight: 4,
    silver: 5,
    gold: 6,
    bishop: 8,
    rook: 10,
    tokin: 2,
    promotedlance: 4,
    promotedknight: 5,
    promotedsilver: 6,
    horse: 9,
    dragon: 11,
    king: 0,
  } as const,
} as const;

export type ReadValues = typeof READ_VALUES;

export class ReadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ReadError";
  }
}

function pieceValueOf(role: string, values: ReadValues): number {
  const value = (values.pieceValues as Record<string, number>)[role];
  if (value === undefined) throw new ReadError(`価値表に無い駒種: ${role}`);
  return value;
}

/** `afterSfen`(指した後の局面)で、`opp` 側の駒のどれかが `target` の升に利いているか(取り返せるか)。 */
function isSquareAttackedByOpponent(afterSfen: string, opp: Color, target: Square): boolean {
  const after = parsePosition(afterSfen);
  for (const square of after.board.color(opp)) {
    const piece = after.board.get(square);
    if (piece === undefined) continue;
    if (attacks(piece, square, after.board.occupied).has(target)) return true;
  }
  return false;
}

interface MoveMaterialContext {
  facts: UserMoveFacts;
  move: MoveOrDrop;
  afterSfen: string;
  opp: Color;
  /** 指した後、動かした先が相手の利きにあるか(取り返せるか) */
  attacked: boolean;
  /** 取った駒の価値(取っていなければ 0) */
  capturedValue: number;
  /** 動かした駒の、指した後の升での価値(成っていれば成った後の価値) */
  movedValue: number;
}

/** `moveMarksOf`・`materialLookOf` が共有する下ごしらえ(moveFactsOf・applyMove・利きの判定)。 */
function moveMaterialContextOf(sfen: string, moveUsi: string, values: ReadValues): MoveMaterialContext {
  const facts = moveFactsOf(sfen, moveUsi, POSITION_FACTS_RULES);
  const move = parseUsi(moveUsi);
  if (move === undefined) throw new ReadError(`USI の手として読めない: ${moveUsi}`);
  const before = parsePosition(sfen);
  const opp = opposite(before.turn);
  const afterSfen = applyMove(sfen, moveUsi);
  const after = parsePosition(afterSfen);
  const movedPiece = after.board.get(move.to);
  if (movedPiece === undefined) throw new ReadError(`指した後の升に駒が無い: ${moveUsi}`);
  const attacked = isSquareAttackedByOpponent(afterSfen, opp, move.to);
  const capturedValue = facts.capturedRole !== null ? pieceValueOf(facts.capturedRole, values) : 0;
  const movedValue = pieceValueOf(movedPiece.role, values);
  return { facts, move, afterSfen, opp, attacked, capturedValue, movedValue };
}

// ---- 2.2 手の性質(行き先と駒だけで決まる) ----

export interface ReadMoveMarks {
  /** 持ち駒を打つ手か */
  drop: boolean;
  /** 相手の駒を取る手か */
  capture: boolean;
  /** 自陣の側へ動く手か(本人 = 先手にそろえた記録なので、段が大きくなる方向。打つ手は false) */
  retreat: boolean;
  /** 成れるのに成らない手か(打つ手・すでに成った手は false) */
  declinesPromotion: boolean;
  /** 捨て駒か: 動かした先が相手の利きにあり、その升での駒の損得(取った駒の価値 − 動かした駒の価値)が負
   * (取り返しの有無を問わない ― 相手の利きにあるという事実だけで判定する) */
  sacrifice: boolean;
  /** 玉を動かす手か */
  kingMove: boolean;
  /** 指した後、相手が王手を受けるか */
  givesCheck: boolean;
}

/**
 * `ReadMoveMarks` の欄の名前を**実行時に使える語彙**にしたもの(2026-09-30。Observation Packet の束 C)。
 * **写しではなく、型と機械で結んである** ― 下の `_ReadMoveMarkKeysComplete` が、
 * 欄が増えてこの並びに無いときに**型検査で落ちる**(語彙が 2 か所でずれる道を塞ぐ)。
 */
export const READ_MOVE_MARK_KEYS = ["drop", "capture", "retreat", "declinesPromotion", "sacrifice", "kingMove", "givesCheck"] as const;
type AssertNever<T extends never> = T;
export type _ReadMoveMarkKeysComplete = AssertNever<Exclude<keyof ReadMoveMarks, (typeof READ_MOVE_MARK_KEYS)[number]>>;

/** `sfen` の局面(本人の手番)で `moveUsi` を指したときの印(計画「作るもの」2.)。合法でない手・読めない手は例外。 */
export function moveMarksOf(sfen: string, moveUsi: string, values: ReadValues = READ_VALUES): ReadMoveMarks {
  const ctx = moveMaterialContextOf(sfen, moveUsi, values);
  const retreat = !isDrop(ctx.move) && squareRank(ctx.move.to) > squareRank(ctx.move.from);
  const declinesPromotion = !isDrop(ctx.move) && !ctx.facts.promotion && isLegalMove(sfen, `${moveUsi}+`);
  const sacrifice = ctx.attacked && ctx.capturedValue - ctx.movedValue < 0;
  return {
    drop: ctx.facts.drop,
    capture: ctx.facts.capturedRole !== null,
    retreat,
    declinesPromotion,
    sacrifice,
    kingMove: ctx.facts.kingMove,
    givesCheck: isInCheck(ctx.afterSfen, ctx.opp),
  };
}

// ---- 2.3 見た目と評価の食い違い ----

/**
 * 指した直後(相手の返しの前)の見た目の損得(計画「作るもの」3.)。
 * 取った駒の価値 − (動かした先が相手の利きにあるなら動かした駒の価値、なければ 0)。
 */
export function materialLookOf(sfen: string, moveUsi: string, values: ReadValues = READ_VALUES): number {
  const ctx = moveMaterialContextOf(sfen, moveUsi, values);
  return ctx.capturedValue - (ctx.attacked ? ctx.movedValue : 0);
}

// ---- 2.1 浅い探索でも分かる崩れか ----

/** 1 段ぶんの、呼び出し側(CLI)が読んだ生の値。測れなかった(エンジンの例外・タイムアウト)ときは null。 */
export interface ReadLadderLevelInput {
  nodes: number;
  /** (a) 第 1 候補の評価(searchmoves 無し) */
  top: { scoreCp: number | null; mate: number | null } | null;
  /** (b) 実戦の手だけを読ませた評価(searchmoves 実戦の手) */
  actual: { scoreCp: number | null; mate: number | null; pv: readonly string[] } | null;
}

export interface ReadLadderLevel {
  nodes: number;
  topScoreCp: number | null;
  topMate: number | null;
  actualScoreCp: number | null;
  actualMate: number | null;
  /** evalValueOf(top) − evalValueOf(actual)。どちらかが測れなければ null(計画「作るもの」1.) */
  diffValue: number | null;
}

/** `evalValueOf`(lib/whatif.ts。mate を数直線に乗せる、既存の関数)で 1 段の差を組む。 */
export function ladderLevelOf(input: ReadLadderLevelInput): ReadLadderLevel {
  const topValue = input.top !== null ? evalValueOf(input.top) : null;
  const actualValue = input.actual !== null ? evalValueOf(input.actual) : null;
  return {
    nodes: input.nodes,
    topScoreCp: input.top?.scoreCp ?? null,
    topMate: input.top?.mate ?? null,
    actualScoreCp: input.actual?.scoreCp ?? null,
    actualMate: input.actual?.mate ?? null,
    diffValue: topValue !== null && actualValue !== null ? topValue - actualValue : null,
  };
}

/** 差が `minLossCp` 以上になる最小のノード数(`levels` は昇順を前提とする)。どの段でも出なければ null。 */
export function firstVisibleNodesOf(levels: readonly ReadLadderLevel[], minLossCp: number): number | null {
  for (const level of levels) {
    if (level.diffValue !== null && level.diffValue >= minLossCp) return level.nodes;
  }
  return null;
}

/**
 * いちばん深い段の (b) の読み筋の 2 手目(相手の返し)が、次に相手が実際に指した手と同じか。
 * `pvAtMaxNodes` が無い(測れなかった、または pv が 1 手しかない)・`nextActualMove` が無い(この分かれ道が
 * 対局の最後の手だった)ときは、比べられないので null。
 */
export function opponentReplyMatchesPvOf(pvAtMaxNodes: readonly string[] | null, nextActualMove: string | null): boolean | null {
  if (pvAtMaxNodes === null || nextActualMove === null) return null;
  const reply = pvAtMaxNodes[1];
  if (reply === undefined) return null;
  return reply === nextActualMove;
}

// ---- 1 局面ぶんの組み立て ----

export interface ReadForkPositionInput {
  ply: number;
  displayPly: number;
  sfen: string;
  actualMove: string;
  /** whatif-v2 の候補 1 番(第 1 候補)の手 */
  top1Move: string;
  /** 次に相手が実際に指した手(固定棋譜から)。対局の最後の手なら null */
  nextActualMove: string | null;
  /** `READ_VALUES.nodeLadder` と同じ順(昇順)の、各段の生の読み */
  ladderLevels: readonly ReadLadderLevelInput[];
}

export interface ReadForkPosition {
  ply: number;
  displayPly: number;
  sfen: string;
  actualMove: string;
  top1Move: string;
  ladder: ReadLadderLevel[];
  firstVisibleNodes: number | null;
  opponentReplyMatchesPv: boolean | null;
  top1Tags: ReadMoveMarks;
  actualTags: ReadMoveMarks;
  top1MaterialLook: number;
  actualMaterialLook: number;
}

/** 1 つの分かれ道の記録を組む(計画「作るもの」1.〜3.)。エンジンは呼ばない。 */
export function readForkPositionOf(input: ReadForkPositionInput, values: ReadValues = READ_VALUES): ReadForkPosition {
  const ladder = input.ladderLevels.map(ladderLevelOf);
  const firstVisibleNodes = firstVisibleNodesOf(ladder, values.minLossCp);
  const maxNodes = Math.max(...input.ladderLevels.map((level) => level.nodes));
  const maxLevelInput = input.ladderLevels.find((level) => level.nodes === maxNodes);
  const pvAtMaxNodes = maxLevelInput?.actual?.pv ?? null;
  const opponentReplyMatchesPv = opponentReplyMatchesPvOf(pvAtMaxNodes, input.nextActualMove);
  return {
    ply: input.ply,
    displayPly: input.displayPly,
    sfen: input.sfen,
    actualMove: input.actualMove,
    top1Move: input.top1Move,
    ladder,
    firstVisibleNodes,
    opponentReplyMatchesPv,
    top1Tags: moveMarksOf(input.sfen, input.top1Move, values),
    actualTags: moveMarksOf(input.sfen, input.actualMove, values),
    top1MaterialLook: materialLookOf(input.sfen, input.top1Move, values),
    actualMaterialLook: materialLookOf(input.sfen, input.actualMove, values),
  };
}

// ---- 1 局ぶんのまとめ ----

export const READ_TAG_NAMES = ["drop", "capture", "retreat", "declinesPromotion", "sacrifice", "kingMove", "givesCheck"] as const;
export type ReadTagName = (typeof READ_TAG_NAMES)[number];

/** `firstVisibleNodes` の区分の件数(`values.nodeLadder` の各段 + "出ない"(none))。 */
export function firstVisibleNodesBucketsOf(positions: readonly { firstVisibleNodes: number | null }[], nodeLadder: readonly number[] = READ_VALUES.nodeLadder): Record<string, number> {
  const buckets: Record<string, number> = {};
  for (const nodes of nodeLadder) buckets[String(nodes)] = 0;
  buckets.none = 0;
  for (const position of positions) {
    const key = position.firstVisibleNodes === null ? "none" : String(position.firstVisibleNodes);
    buckets[key] = (buckets[key] ?? 0) + 1;
  }
  return buckets;
}

/** `opponentReplyMatchesPv` の件数(matched = 一致・measured = 比べられた件数。null は measured に含めない)。 */
export function opponentReplyMatchesPvCountOf(positions: readonly { opponentReplyMatchesPv: boolean | null }[]): { matched: number; measured: number } {
  let matched = 0;
  let measured = 0;
  for (const position of positions) {
    if (position.opponentReplyMatchesPv === null) continue;
    measured++;
    if (position.opponentReplyMatchesPv) matched++;
  }
  return { matched, measured };
}

/** 第 1 候補の種類ごとに、実戦の手の種類の件数(7 × 7。複数の印に当たってよいので、独立に数える)。 */
export function tagCrossTableOf(positions: readonly { top1Tags: ReadMoveMarks; actualTags: ReadMoveMarks }[]): Record<ReadTagName, Record<ReadTagName, number>> {
  const table = {} as Record<ReadTagName, Record<ReadTagName, number>>;
  for (const top1Tag of READ_TAG_NAMES) {
    table[top1Tag] = {} as Record<ReadTagName, number>;
    for (const actualTag of READ_TAG_NAMES) table[top1Tag][actualTag] = 0;
  }
  for (const position of positions) {
    for (const top1Tag of READ_TAG_NAMES) {
      if (!position.top1Tags[top1Tag]) continue;
      for (const actualTag of READ_TAG_NAMES) {
        if (position.actualTags[actualTag]) table[top1Tag][actualTag]++;
      }
    }
  }
  return table;
}

export interface ReadMaterialLookSummary {
  /** 実戦の手が駒得に見える(materialLook > 0)局面の数(分かれ道 = 評価は下がった局面のうちの数) */
  actualPositiveCount: number;
  /** 第 1 候補が駒損に見える(materialLook < 0)局面の数 */
  top1NegativeCount: number;
  /** 両方に当たる局面の数 */
  bothCount: number;
}

export function materialLookSummaryOf(positions: readonly { actualMaterialLook: number; top1MaterialLook: number }[]): ReadMaterialLookSummary {
  let actualPositiveCount = 0;
  let top1NegativeCount = 0;
  let bothCount = 0;
  for (const position of positions) {
    const actualPositive = position.actualMaterialLook > 0;
    const top1Negative = position.top1MaterialLook < 0;
    if (actualPositive) actualPositiveCount++;
    if (top1Negative) top1NegativeCount++;
    if (actualPositive && top1Negative) bothCount++;
  }
  return { actualPositiveCount, top1NegativeCount, bothCount };
}

export interface ReadGameSummary {
  /** 読んだ分かれ道の数 */
  forkPositionsRead: number;
  firstVisibleNodesBuckets: Record<string, number>;
  opponentReplyMatchesPv: { matched: number; measured: number };
  tagCrossTable: Record<ReadTagName, Record<ReadTagName, number>>;
  materialLook: ReadMaterialLookSummary;
}

/** 1 局ぶんの `ReadForkPosition` の列から、まとめを作る(計画「作るもの」4.)。手・評価値・SFEN は含まない。 */
export function readGameSummaryOf(positions: readonly ReadForkPosition[], values: ReadValues = READ_VALUES): ReadGameSummary {
  return {
    forkPositionsRead: positions.length,
    firstVisibleNodesBuckets: firstVisibleNodesBucketsOf(positions, values.nodeLadder),
    opponentReplyMatchesPv: opponentReplyMatchesPvCountOf(positions),
    tagCrossTable: tagCrossTableOf(positions),
    materialLook: materialLookSummaryOf(positions),
  };
}
