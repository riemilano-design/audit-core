// STEP D3(docs/STEP_D3_PLAN_2026-09-14.md 2.2・2.3・8.4)。縛った初心者(docs/PLAYTEST_PERSONA_BEGINNER.md
// 4. の 5.「⑤が無い、または押せないとき自分で決める順」)を写したプロファイル B と B2(文書では B′)。
//
// 【このファイルが受け取るもの・読むもの(型とソース照合で縛る。計画 8.4 の決定 12・13)】
// - 引数は sfen と variant だけ。対局のエンジンも、画面の応答も受け取らない
// - モジュールは次の許す一覧だけを読む: shogiops/*・apps/server/src/rules/*・apps/server/src/analysis/pieceThreatDetector.js。
//   それ以外(エンジン・画面の応答・API・game/・lib の他のファイル)を読むと beginnerProfile.test.ts の F-B16 が落ちる
//   (許す一覧は試験の isAllowedSpecifier と同じ。計画 8.8 の A3)
//
// 【このファイルが絶対にやらないこと】
// - 将棋の良し悪しを書くこと。規則は人物設定の写しであり、試験の入力(演じ方)であって本番の判断ではない
// - 乱数・時刻に頼ること。同じ sfen と variant なら同じ手・同じ段を返す(決定的)
//
// 本番関数(apps/server/src 配下)は import して呼ぶだけで、複製・改変はしない。

import type { Color, Role } from "shogiops/types";
import { parseSquareName } from "shogiops/util";
import { detectPieceThreats } from "../../../apps/server/src/analysis/pieceThreatDetector.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { listAttackedPieces } from "../../../apps/server/src/rules/attackedPieces.js";
import { getLegalMoves } from "../../../apps/server/src/rules/legalMoves.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { isSquareAttacked } from "../../../apps/server/src/rules/squareAttack.js";

/** B は 5-i〜5-v をすべて使う。B2(B′)は 5-iii(金か銀を玉の隣へ)を一度も使わない(計画 2.3)。 */
export type BeginnerVariant = "B" | "B2";

/** どの段で決めたか(計画 2.2)。棋譜 JSON の tiers に書く(Q-4)。 */
export type BeginnerTier = "5-i" | "5-ii" | "5-iii" | "5-iv-a" | "5-iv-b" | "5-v";

export interface BeginnerPick {
  move: string;
  tier: BeginnerTier;
}

const FILES = "123456789";
const RANKS = "abcdefghi";

/** 端の筋(計画 2.2 の注記 4 (i))。 */
const EDGE_FILES: ReadonlySet<number> = new Set([1, 9]);

/** 先手の飛車(龍)が盤に無いときに「飛車の筋」の代わりに使う筋(初期位置。注記 4 (iii))。 */
const SUBSTITUTE_ROOK_FILE = 2;

interface BoardPiece {
  /** USI 形式のマス(例 "5g")。 */
  square: string;
  file: number;
  /** a=0 … i=8。先手の「前」は数字が小さくなる方向。 */
  rankIndex: number;
  color: Color;
  role: Role;
}

function squareName(file: number, rankIndex: number): string {
  return `${file}${RANKS[rankIndex]}`;
}

function fileOf(square: string): number {
  return Number(square[0]);
}

function rankIndexOf(square: string): number {
  return RANKS.indexOf(square[1] ?? "");
}

/** 盤上の駒を USI のマスの名前で並べる(並びの順は使わない。見つけるためだけ)。 */
function piecesOf(sfen: string): BoardPiece[] {
  const board = parsePosition(sfen).board;
  const pieces: BoardPiece[] = [];
  for (const file of FILES) {
    for (const rank of RANKS) {
      const square = parseSquareName(`${file}${rank}`);
      if (square === undefined) continue;
      const piece = board.get(square);
      if (!piece) continue;
      pieces.push({ square: `${file}${rank}`, file: Number(file), rankIndex: RANKS.indexOf(rank), color: piece.color, role: piece.role });
    }
  }
  return pieces;
}

function pieceAt(pieces: readonly BoardPiece[], square: string): BoardPiece | undefined {
  return pieces.find((piece) => piece.square === square);
}

function isDrop(move: string): boolean {
  return move[1] === "*";
}

function fromOf(move: string): string {
  return move.slice(0, 2);
}

function toOf(move: string): string {
  return move.slice(2, 4);
}

function isAdjacent(a: string, b: string): boolean {
  return Math.max(Math.abs(fileOf(a) - fileOf(b)), Math.abs(rankIndexOf(a) - rankIndexOf(b))) === 1;
}

/**
 * 5-i「相手の駒を取れるなら取る(取り返されるかを 1 手だけ確かめ、取り返されるなら取らない)」。
 * 移動先に後手の駒がある手(打つ手は含まない)のうち、指した後の局面で移動先に後手の利きが届いていない手を、
 * 合法手の順で最初に 1 つ。成り・不成が両方合法なら、合法手の順で先の不成になる(注記 1)。
 */
function pickCapture(sfen: string, legalMoves: readonly string[], pieces: readonly BoardPiece[]): string | undefined {
  for (const move of legalMoves) {
    if (isDrop(move)) continue;
    const destination = toOf(move);
    const target = pieceAt(pieces, destination);
    if (!target || target.color !== "gote") continue;
    if (!isSquareAttacked(applyMove(sfen, move), destination, "gote")) return move;
  }
  return undefined;
}

/**
 * 5-ii「帯の駒を逃がす(取られない場所へ)」。帯と同じ事実(detectPieceThreats(listAttackedPieces))の先頭の駒について、
 * その駒の手のうち、指した後の移動先に後手の利きが届いていない手を、合法手の順で最初に 1 つ。画面の応答は読まない。
 */
function pickEscape(sfen: string, legalMoves: readonly string[]): string | undefined {
  const target = detectPieceThreats(listAttackedPieces(sfen, "sente"))[0];
  if (!target) return undefined;
  for (const move of legalMoves) {
    if (isDrop(move) || fromOf(move) !== target.square) continue;
    if (!isSquareAttacked(applyMove(sfen, move), toOf(move), "gote")) return move;
  }
  return undefined;
}

/**
 * 5-iii「金か銀を玉の隣へ一つ寄せる(すでに玉の隣にある駒は動かさない)」。
 * 先手の金・銀(成っていない。成銀・と金・成香・成桂は含まない)の、打つ手でない手のうち、
 * 移動元が先手玉の隣でなく、移動先が隣である手を、合法手の順で最初に 1 つ(注記 5)。
 */
function pickGuard(legalMoves: readonly string[], pieces: readonly BoardPiece[]): string | undefined {
  const king = pieces.find((piece) => piece.color === "sente" && piece.role === "king");
  if (!king) return undefined;
  for (const move of legalMoves) {
    if (isDrop(move)) continue;
    const mover = pieceAt(pieces, fromOf(move));
    if (!mover || mover.color !== "sente") continue;
    if (mover.role !== "gold" && mover.role !== "silver") continue;
    if (isAdjacent(mover.square, king.square)) continue;
    if (isAdjacent(toOf(move), king.square)) return move;
  }
  return undefined;
}

/** 歩を 1 マス前へ進める合法手。不成を選び、成りしか合法でなければ成り(計画 2.2 の 5-iv)。無ければ undefined。 */
function pawnStep(legalMoves: readonly string[], pawn: BoardPiece): string | undefined {
  if (pawn.rankIndex === 0) return undefined;
  const plain = `${pawn.square}${squareName(pawn.file, pawn.rankIndex - 1)}`;
  if (legalMoves.includes(plain)) return plain;
  if (legalMoves.includes(`${plain}+`)) return `${plain}+`;
  return undefined;
}

/**
 * 飛車(角)から敵陣側へ見て最初に当たる駒が先手の歩なら、その歩。
 * 歩でない駒(自分のでも相手のでも)が先にあれば undefined(その先の歩は探さない。注記 3)。
 */
function frontPawnOf(pieces: readonly BoardPiece[], piece: BoardPiece): BoardPiece | undefined {
  for (let rankIndex = piece.rankIndex - 1; rankIndex >= 0; rankIndex--) {
    const found = pieceAt(pieces, squareName(piece.file, rankIndex));
    if (!found) continue;
    return found.color === "sente" && found.role === "pawn" ? found : undefined;
  }
  return undefined;
}

function senteRooks(pieces: readonly BoardPiece[]): BoardPiece[] {
  return pieces.filter((piece) => piece.color === "sente" && (piece.role === "rook" || piece.role === "dragon")).sort((a, b) => a.file - b.file);
}

function senteBishops(pieces: readonly BoardPiece[]): BoardPiece[] {
  return pieces.filter((piece) => piece.color === "sente" && (piece.role === "bishop" || piece.role === "horse")).sort((a, b) => a.file - b.file);
}

/**
 * 5-iv-a「飛車か角の前の歩を一つ前に出す」。飛車(龍を含む)を先、角(馬を含む)を後に見る。
 * 対象の歩の 1 マス前が合法でなければ、次の飛車・角へ落ちる(注記 2)。同じ種類が 2 枚あれば筋の数字が小さい方から見る
 * (飛車 2 枚の順は計画 8.8 の A2 で確定)。
 */
function pickFrontPawn(legalMoves: readonly string[], pieces: readonly BoardPiece[]): string | undefined {
  for (const piece of [...senteRooks(pieces), ...senteBishops(pieces)]) {
    const pawn = frontPawnOf(pieces, piece);
    if (!pawn) continue;
    const move = pawnStep(legalMoves, pawn);
    if (move) return move;
  }
  return undefined;
}

/**
 * 5-iv-b「(飛車・角の前の歩が無いときは)他の歩を一つ前に出す」。合法手の順は使わない(注記 4)。
 * (i) 端(1 筋・9 筋)を除いた進められる歩のうち、飛車の筋に最も近い筋の歩 /
 * (ii) 同じ距離なら筋の数字が小さい方 / (iii) 飛車が無ければ 2 筋で代え、2 枚なら筋の数字が小さい方 /
 * (iv) 端以外に進められる歩が無ければ、端の歩を同じ順で。
 */
function pickOtherPawn(legalMoves: readonly string[], pieces: readonly BoardPiece[]): string | undefined {
  const rooks = senteRooks(pieces);
  const referenceFile = rooks[0]?.file ?? SUBSTITUTE_ROOK_FILE;
  const steps = pieces
    .filter((piece) => piece.color === "sente" && piece.role === "pawn")
    .map((pawn) => ({ pawn, move: pawnStep(legalMoves, pawn) }))
    .filter((step): step is { pawn: BoardPiece; move: string } => step.move !== undefined);
  const inner = steps.filter((step) => !EDGE_FILES.has(step.pawn.file));
  const pool = inner.length > 0 ? inner : steps;
  const ordered = [...pool].sort(
    (a, b) => Math.abs(a.pawn.file - referenceFile) - Math.abs(b.pawn.file - referenceFile) || a.pawn.file - b.pawn.file,
  );
  return ordered[0]?.move;
}

/**
 * 先手番の sfen について、B(または B2)の決め方で 1 手と段を返す(計画 2.2)。上から順に試し、当たったらそこで決める。
 * 合法手が 0(詰み)なら undefined。**先手番でない sfen は受け付けない**(演じるのは先手だけ)。
 */
export function pickByBeginnerProfile(sfen: string, variant: BeginnerVariant): BeginnerPick | undefined {
  if (parsePosition(sfen).turn !== "sente") {
    throw new Error(`B は先手番の局面だけを受け付ける: ${sfen}`);
  }
  const legalMoves = getLegalMoves(sfen);
  const firstLegalMove = legalMoves[0];
  if (firstLegalMove === undefined) return undefined;
  const pieces = piecesOf(sfen);

  const capture = pickCapture(sfen, legalMoves, pieces);
  if (capture) return { move: capture, tier: "5-i" };

  const escape = pickEscape(sfen, legalMoves);
  if (escape) return { move: escape, tier: "5-ii" };

  if (variant === "B") {
    const guard = pickGuard(legalMoves, pieces);
    if (guard) return { move: guard, tier: "5-iii" };
  }

  const frontPawn = pickFrontPawn(legalMoves, pieces);
  if (frontPawn) return { move: frontPawn, tier: "5-iv-a" };

  const otherPawn = pickOtherPawn(legalMoves, pieces);
  if (otherPawn) return { move: otherPawn, tier: "5-iv-b" };

  return { move: firstLegalMove, tier: "5-v" };
}
