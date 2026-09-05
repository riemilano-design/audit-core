// SFEN + 指し手履歴 -> Intent候補 の本実装。
// docs/DATA_MODEL.md の教育用データパイプライン③(相手の意図)のうち、
// 「相手が今、代表的なパターン(棒銀・斜め棒銀・早仕掛けなど)のどれに
// 近づいているように見えるか」を判定する。
//
// 将棋知識(この手順が何を意味するか)は一切ここで判断せず、data/intents/*.json
// (intentRepository.ts経由)に確定したrecognition_patternと、実際の指し手履歴を
// 機械的に突き合わせるだけに責務を限定する(shapeDetector.tsと同じ設計方針)。
//
// 重要な前提(docs/DATA_MODEL.md「相手の意図」節・intents.schema.jsonより):
// recognition_patternは「順不同でも良い断片的なシグネチャ」であり、厳密な手順の
// 一致を要求するものではない。そのため本実装も、各シグネチャ(駒種+移動先)が
// 指し手履歴のどこかで(順序を問わず)観測されたかどうかだけを判定する。
// これにより、シグネチャが一部しか観測されない「まだ断定できない」状態(forming)を
// 自然に表現できる([../../../../CLAUDE.md](../../../../CLAUDE.md) ルール6番:
// 断定できないことは断定しない、に対応する)。
//
// 座標視点は docs/DATA_MODEL.md のMVP確定仕様に従い、intentsのrecognition_patternは
// 常にopponent(居飛車)=後手(gote)の絶対座標として記録されているため、
// 判定対象の指し手も常にgote側の手に限定する。

import type { Color } from "shogiops/types";
import { parsePosition } from "../rules/sfenPosition.js";
import {
  DEFAULT_INITIAL_SFEN,
  replayMoveHistory,
  type MoveEvent,
} from "./moveHistory.js";
import { japaneseToRole } from "./pieceMapping.js";
import { findMoveEvidence } from "./signatureEvidence.js";
import {
  getIntents,
  type AffectsTargetShape,
  type IntentDefinition,
  type RecognitionPatternEntry,
} from "./intentRepository.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";
export { IllegalMoveError, MoveHistoryError } from "./moveHistory.js";

// docs/DATA_MODEL.md: MVPでは role=opponent(居飛車)=gote固定。
const OPPONENT_COLOR: Color = "gote";

export type IntentMatchStatus = "none" | "forming" | "matched";

export interface MatchedSignature {
  piece: string;
  to: string;
  orderHint?: number;
  /** このシグネチャが観測された根拠(指し手履歴上の位置) */
  evidence: { ply: number; moveUsi: string };
}

export interface IntentDetectionResult {
  intentId: string;
  name: string;
  openingId: string;
  /** data/intents/*.json 側の「この知識データ自体への自信度」(検知の確信度とは別概念) */
  dataConfidenceLevel: IntentDefinition["confidence_level"];
  /** シグネチャが1つも観測されない/一部観測/全て観測、の3段階。断定を避けるための土台。 */
  matchStatus: IntentMatchStatus;
  /** 観測されたシグネチャの割合。0〜1。決定的な値(同じ入力なら常に同じ値)。 */
  matchScore: number;
  matchedSignatures: MatchedSignature[];
  unmatchedSignatures: RecognitionPatternEntry[];
  /** 後続(説明生成)処理がそのまま使えるよう、intent定義からそのまま引き継ぐ */
  currentAimExplanation: string;
  nextAimExplanation: string;
  affectsTargetShapes?: AffectsTargetShape[];
}

export class IntentDetectorError extends Error {}

function evaluateIntent(opponentEvents: MoveEvent[], intent: IntentDefinition): IntentDetectionResult {
  const matchedSignatures: MatchedSignature[] = [];
  const unmatchedSignatures: RecognitionPatternEntry[] = [];

  for (const signature of intent.recognition_pattern) {
    const expectedRole = japaneseToRole(signature.piece);
    const evidence = findMoveEvidence(opponentEvents, OPPONENT_COLOR, expectedRole, signature.to);

    if (evidence) {
      matchedSignatures.push({
        piece: signature.piece,
        to: signature.to,
        orderHint: signature.order_hint,
        evidence,
      });
    } else {
      unmatchedSignatures.push(signature);
    }
  }

  const total = intent.recognition_pattern.length;
  const matchScore = total === 0 ? 0 : matchedSignatures.length / total;

  let matchStatus: IntentMatchStatus;
  if (matchedSignatures.length === 0) {
    matchStatus = "none";
  } else if (unmatchedSignatures.length === 0) {
    matchStatus = "matched";
  } else {
    matchStatus = "forming";
  }

  return {
    intentId: intent.id,
    name: intent.name,
    openingId: intent.opening_id,
    dataConfidenceLevel: intent.confidence_level,
    matchStatus,
    matchScore,
    matchedSignatures,
    unmatchedSignatures,
    currentAimExplanation: intent.current_aim_explanation,
    nextAimExplanation: intent.next_aim_explanation,
    affectsTargetShapes: intent.affects_target_shapes,
  };
}

export interface DetectIntentsOptions {
  intents?: IntentDefinition[];
  /** 対局の初期局面。MVPでは常にstartposのため通常は指定不要(テスト用の差し替え口)。 */
  initialSfen?: string;
}

/**
 * 現在のSFENと、そこに至るまでの指し手履歴(USI形式、初手から順に)から、
 * data/intents/ にある各Intentについて「どの程度そのパターンに近づいているか」を判定する。
 *
 * sfenは「moveHistoryをinitialSfenから再生した結果と一致するはず」という前提を
 * 内部で検証する(呼び出し側の局面と履歴の取り違えを防ぐ最低限の防御)。
 * 一致しない場合はIntentDetectorErrorを投げる。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 */
export function detectIntents(
  sfen: string,
  moveHistory: string[],
  options: DetectIntentsOptions = {},
): IntentDetectionResult[] {
  // sfen自体がshogiopsで解釈可能かをまず確認する(不正なSFENに対してInvalidSfenErrorを投げる)。
  parsePosition(sfen);

  const initialSfen = options.initialSfen ?? DEFAULT_INITIAL_SFEN;
  const { events, finalSfen } = replayMoveHistory(moveHistory, initialSfen);

  if (finalSfen !== sfen) {
    throw new IntentDetectorError(
      `sfenとmoveHistoryの再生結果が一致しません(局面と履歴の組み合わせが不正です)。` +
        `expected="${finalSfen}" actual="${sfen}"`,
    );
  }

  const opponentEvents = events.filter((event) => event.color === OPPONENT_COLOR);
  const intents = options.intents ?? getIntents();

  const results = intents.map((intent) => evaluateIntent(opponentEvents, intent));

  // 呼び出し側(将来の説明生成)が扱いやすいよう、一致度が高い順・同点ならintentId昇順で安定ソートする。
  return results.sort((a, b) => b.matchScore - a.matchScore || a.intentId.localeCompare(b.intentId));
}

/**
 * 指定したidのIntent1件だけを判定する。将来の説明生成などで
 * 「特定の意図についてだけ知りたい」場合に使う想定。
 */
export function detectIntent(
  sfen: string,
  moveHistory: string[],
  intentId: string,
  options: DetectIntentsOptions = {},
): IntentDetectionResult | undefined {
  const intents = options.intents ?? getIntents();
  const intent = intents.find((i) => i.id === intentId);
  if (!intent) return undefined;
  return detectIntents(sfen, moveHistory, { ...options, intents: [intent] })[0];
}
