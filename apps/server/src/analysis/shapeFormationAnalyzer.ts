// Shape判定(shapeDetector.ts, Unit1)に、指し手履歴から見た「実際にその形へ向かう
// 駒の動きが観測されているか」という証拠を組み合わせ、プロダクト向けのstatusを算出する。
//
// 【解決したい問題(Unit4のブラウザ実地確認で判明)】
// shapeDetector.tsのstatus="forming"は、盤面が静的にどれだけrequired_piecesと
// 一致しているかだけを見ており、次の2つを区別できない:
//   (a) たまたま初期配置の駒が必須マスと一致しているだけ
//       (例: 初期局面で本美濃囲いの6九金が、一度も動いていないのに一致している)
//   (b) 実際にその形に向かって駒が動いている
// (a)なのに「本美濃囲いを作ろうとしている可能性があります」と表示するのは、
// 「対局中、将棋の意味をリアルタイムで通訳してくれるコーチ」というCLAUDE.mdの
// 最重要コンセプトに反する誤った通訳になる。
//
// 【解決方法・将棋知識について】
// 新しい将棋知識は一切追加しない。data/shapes/*.jsonのrequired_pieces(既存データ)
// と、実際の指し手履歴だけから機械的に導出できる情報のみを使う。
// 具体的には、Unit2(intentDetector.ts)が intents.recognition_pattern の判定に
// 使っているのと全く同じ仕組み(「駒種+移動先が指し手履歴に存在するか」)を
// signatureEvidence.ts経由で再利用し、shapes.required_piecesの各マスについても
// 同じ判定を行う(重複ロジックを作らない、というdocs/ROLES.mdの方針に対応)。
//
// 【Unit1(shapeDetector.ts)との関係】
// shapeDetector.ts / detectShapes() / ShapeDetectionResult は変更していない。
// 引き続き「盤面の静的な一致(shape_match)」だけを見る純粋関数として存在する
// (Phase2の shape graph ランキング等、静的な一致度だけで十分な用途に使える)。
// 本モジュールはその上に「指し手履歴も見た、プロダクト向けのstatus」を追加する
// レイヤーであり、ShapeFormationResult.status は ShapeDetectionResult.status とは
// 別の意味(静的一致のみ vs 形成過程の証拠つき)を持つ点に注意
// (詳細はPhase1 Unit5の報告を参照。混同しやすいため、呼び出し元は本モジュールの
// analyzeShapeFormation()をUI/説明生成向けの入口として使うことを推奨する)。

import { DEFAULT_INITIAL_SFEN, replayMoveHistory, type MoveEvent } from "./moveHistory.js";
import { japaneseToRole } from "./pieceMapping.js";
import { detectShapes, type ShapeDetectionResult, type ShapeStatus } from "./shapeDetector.js";
import { getShapes, type ShapeDefinition } from "./shapeRepository.js";
import { findMoveEvidence, type SignatureEvidence } from "./signatureEvidence.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";
export { IllegalMoveError, MoveHistoryError } from "./moveHistory.js";

export interface ShapeFormationEvidenceEntry {
  /** required_pieces.square (USI形式) */
  square: string;
  /** required_pieces.piece (日本語駒名、既存データそのまま) */
  piece: string;
  /** この駒がこのマスへ動いたことを示す、指し手履歴上の根拠 */
  evidence: SignatureEvidence;
}

export interface ShapeFormationResult extends ShapeDetectionResult {
  /**
   * shape_formation_evidence: matchedSquaresのうち、指し手履歴上「実際にその駒が
   * そのマスへ動いた」ことが確認できたものの一覧。初期配置からずっと動いていない駒は
   * (required_pieces上のマスとたまたま一致していても)ここには含まれない。
   */
  formationEvidence: ShapeFormationEvidenceEntry[];
  /**
   * shape_status: shape_match(静的な一致)とshape_formation_evidence(動的な証拠)を
   * 組み合わせたプロダクト向けの状態。ShapeDetectionResult.statusを上書きする。
   * - completed: missingSquaresが0件(shape_matchと同じ基準。物理的に形が完成していれば
   *   経緯を問わず完成として良いため、証拠の有無では判定しない)
   * - forming: 1件以上matchedかつ1件以上missing、かつformationEvidenceが1件以上ある
   *   (=偶然の一致ではなく、実際にその形へ向かう動きが観測されている)
   * - none: 上記以外。matchedSquaresはあるがformationEvidenceが無い「偶然の一致」も
   *   ここに含まれる(=断定を避け、何も申告しない)。
   */
  status: ShapeStatus;
}

export class ShapeFormationAnalysisError extends Error {}

export interface AnalyzeShapeFormationOptions {
  shapes?: ShapeDefinition[];
  /** 対局の初期局面。MVPでは常にstartposのため通常は指定不要(テスト用の差し替え口)。 */
  initialSfen?: string;
}

function buildFormationEvidence(
  shapeMatch: ShapeDetectionResult,
  shapeDef: ShapeDefinition,
  events: MoveEvent[],
): ShapeFormationEvidenceEntry[] {
  const evidence: ShapeFormationEvidenceEntry[] = [];
  for (const square of shapeMatch.matchedSquares) {
    const requiredPiece = shapeDef.required_pieces.find((p) => p.square === square && !p.optional);
    if (!requiredPiece) continue; // 理論上到達しない(matchedSquaresはrequired_pieces由来)が、型上の安全のため
    const role = japaneseToRole(requiredPiece.piece);
    const found = findMoveEvidence(events, shapeMatch.perspectiveColor, role, square);
    if (found) evidence.push({ square, piece: requiredPiece.piece, evidence: found });
  }
  return evidence;
}

function resolveStatus(shapeMatch: ShapeDetectionResult, formationEvidence: ShapeFormationEvidenceEntry[]): ShapeStatus {
  if (shapeMatch.matchedSquares.length > 0 && shapeMatch.missingSquares.length === 0) {
    return "completed";
  }
  if (shapeMatch.matchedSquares.length > 0 && formationEvidence.length > 0) {
    return "forming";
  }
  return "none";
}

/**
 * SFEN + 指し手履歴から、Shape判定(shape_match、Unit1のdetectShapes)と、
 * その形へ向かう実際の駒の動きの証拠(shape_formation_evidence)をあわせて算出する。
 * sfenはmoveHistoryをinitialSfenから再生した結果と一致するはずという前提を検証する
 * (intentDetector.tsと同じ安全策。局面と履歴の取り違えを防ぐ)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 */
export function analyzeShapeFormation(
  sfen: string,
  moveHistory: string[],
  options: AnalyzeShapeFormationOptions = {},
): ShapeFormationResult[] {
  const shapes = options.shapes ?? getShapes();
  // sfen自体の妥当性はdetectShapes内部のparsePosition経由でInvalidSfenErrorとして検証される。
  const shapeMatches = detectShapes(sfen, shapes);

  const initialSfen = options.initialSfen ?? DEFAULT_INITIAL_SFEN;
  const { events, finalSfen } = replayMoveHistory(moveHistory, initialSfen);

  if (finalSfen !== sfen) {
    throw new ShapeFormationAnalysisError(
      `sfenとmoveHistoryの再生結果が一致しません(局面と履歴の組み合わせが不正です)。` +
        `expected="${finalSfen}" actual="${sfen}"`,
    );
  }

  return analyzeShapeFormationFromEvents(sfen, events, { shapes });
}

/**
 * Phase 7 Unit 2(認識の時系列): 既に再生済みのMoveEventを受け取る版。
 *
 * analyzeShapeFormationとの違いは**入力の受け取り方だけ**で、判定
 * (resolveStatus / buildFormationEvidence)は同一のものを呼ぶ。新しい判定方式・
 * 閾値は一切足していない。
 *
 * 【なぜ必要か】認識の時系列は、各plyについて履歴の先頭からの部分列で判定する。
 * analyzeShapeFormationをplyごとに呼ぶと、そのたびに履歴を頭から再生し直すため
 * O(n^2)になる(120手で実測2,037ms)。再生を1回に共有するための入り口である。
 *
 * 【呼び出し側の責務】この関数は**sfenとeventsの整合を検証しない**
 * (analyzeShapeFormationが行っているfinalSfenとの突き合わせを持たない)。
 * 整合は、1回の再生から得たsfensとeventsを組で渡す呼び出し側が担保すること。
 * 不整合な組を渡すと、局面と履歴が食い違ったまま判定される。
 */
export function analyzeShapeFormationFromEvents(
  sfen: string,
  events: MoveEvent[],
  options: AnalyzeShapeFormationOptions = {},
): ShapeFormationResult[] {
  const shapes = options.shapes ?? getShapes();
  const shapeMatches = detectShapes(sfen, shapes);

  return shapeMatches.map((shapeMatch) => {
    const shapeDef = shapes.find((s) => s.id === shapeMatch.shapeId);
    const formationEvidence = shapeDef ? buildFormationEvidence(shapeMatch, shapeDef, events) : [];
    const status = resolveStatus(shapeMatch, formationEvidence);

    return { ...shapeMatch, formationEvidence, status };
  });
}
