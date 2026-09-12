// STEP 5-F(docs/STEP_5-F_PLAN_2026-09-12.md 4. A-2、9.10)。③(相手の次の狙い)を
// エンジンの参考評価(analysis/engineReference.ts の EngineReference)から作る、
// 決定的な純粋関数。エンジンもLLMもここでは呼ばない(EngineReferenceは引数で受け取る)。
//
// 【規則(人間承認済み。2026-09-12の9.10改定を反映。計画書 9.10 まで1つも変えないこと)】
// 「出さない」(null)は次の2つだけ。それ以外はすべて文を返す。
// 1. mateが絡む → 出さない(H-2)。dropCpは両方がcpのときだけ算出されるため、
//    mateが絡む局面はdropCp===nullになる。「出さないと決めた」ことは計画書6.の
//    宿題として記録済み(mateが出る局面を含む記録が取れた時点で再提示する)。
// 2. (A) 帯が1件だけで、その1件がcaptureSquareと同じマス → 出さない
//    (同じ画面に同じ事実が二度出るのを避ける。STEP 4-6で消した型)。
//    ただし(A)の判定は、dropCpが閾値以上でcaptureSquareが解決している
//    「③が出る局面」の中でだけ行う(計画書2.1の実測A=10・B=8・C=2は、この
//    母集団の中で数えた値のため、母集団をそろえないと10件からずれる)。
//
// 上記の2つに当てはまらない場合は、すべて次のいずれかの文を返す(nullにしない)。
// - (B) captureSquareが帯に含まれ、帯が2件以上 →
//   「いま注意する駒のうち、このまま何もしないと、あなたの{マス}の{駒名}が
//   取られる可能性があります。」
// - (C) captureSquareが帯に含まれない →
//   「このまま何もしないと、あなたの{マス}の{駒名}が取られる可能性があります。」
// - それ以外すべて(EngineReferenceが無い・dropCpがnullまたは閾値未満・
//   captureSquareが無い・駒名が解決できない)→
//   「いまのところ、急いで対応することはありません。」
//
// 【9.10の理由(人間の言葉)】
// 枝を刈って焦点を渡すのがこのアプリの中心だとすれば、「いま急ぐことは無い」は
// 省略できるおまけではなく、焦点を渡すことの半分。攻めたがる初心者は、まさに
// 急ぐ必要が無い局面で急いで間違えている。閾値未満・駒名不明などで③が消えると、
// 「何も言われなかった」のか「急がなくてよいと判定された」のかが初心者には
// 区別できない。「いまのところ、急いで対応することはありません。」を出すことで、
// 後者であることを明示する。
//
// 【文言について】
// 一字も変えないこと。「なかでも」「上に挙げた」は人間が明示的に避けた表現
// (計画書 3. H-3a。「なかでも」は順位づけの含みが出るため、「上に挙げた」は
// 配置が変わると事実と合わなくなるため)。評価語(最善・危険・損・べき)は使わず、
// cpの数字も指す手も文には出さない(CLAUDE.md「絶対に守るルール」3番・6番)。
//
// 【閾値300cpの出どころ(H-2)】
// I-7(scripts/playtest/invariants/i7-urgent-but-other-talk.ts の
// I7_DROP_THRESHOLD_CP)と同じdraftの初期値であり、将棋一般の閾値ではない。
// candidateMoveReferenceFilter.tsの候補手除外の300cpとも別物。
// 比較はdropCp>=300を採用側とする(I-7がdropCp<I7_DROP_THRESHOLD_CPで除外する
// 実装と一致させるため)。
//
// 【駒名】
// captureSquareにある自分の駒の名前。pieceThreatExplanation.tsのpieceName
// (基本駒8種はroleToJapanese、成駒6種はPROMOTED_ROLE_TO_JAPANESEの対応表)を
// そのままexportして共有し、同じ対応表を2つ作らない。名前が解決できない場合は
// 出さない(推測して名前を付けない)。
//
// 【帯との突き合わせ】
// 「帯が名指ししているマスの一覧」は、呼び出し側がurgentMessagesのうち
// kind==="piece_attacked"のsquareを取り出して渡す(このモジュール自身は
// urgentMessagesの形を知らない)。

import { parseSquareName } from "shogiops/util";
import { parsePosition } from "../rules/sfenPosition.js";
import { toJapaneseSquare } from "../notation/japaneseSquare.js";
import { pieceName } from "./pieceThreatExplanation.js";
import type { EngineReference } from "./engineReference.js";

/**
 * 300cp閾値の出どころ(H-2): I-7と同じdraftの初期値であり、将棋一般の閾値
 * ではない。候補手除外の300cp(candidateMoveReferenceFilter.ts)とも別物。
 */
const DROP_THRESHOLD_CP = 300;

export interface PieceThreatFocusInput {
  /** パス局面の探索結果(analysis/engineReference.ts)。無ければnull。 */
  engineReference: EngineReference | null;
  /**
   * 帯(urgentMessagesのうちkind==="piece_attacked")が名指ししているマスの
   * 一覧(USI形式)。呼び出し側がPieceThreatMessage[]から取り出して渡す。
   */
  bandSquares: readonly string[];
  /** captureSquareにある駒の名前を読むためのSFEN(現局面)。 */
  sfen: string;
}

/**
 * SFENのsquare(USI形式)にある駒の日本語名を返す。駒が無い、またはpieceName
 * (pieceThreatExplanation.ts)が対応表に無い役職の場合はnull。
 */
function pieceNameAt(sfen: string, usiSquare: string): string | null {
  const square = parseSquareName(usiSquare);
  if (square === undefined) return null;
  const piece = parsePosition(sfen).board.get(square);
  if (!piece) return null;
  return pieceName(piece.role);
}

/**
 * 閾値未満・captureSquareが無い・駒名が解決できないなど、③を「出さない」の
 * ではなく「急ぐ話が無い」ことを伝える既定文(9.10。人間承認済み。一字も
 * 変えないこと)。
 */
const NO_RUSH_TEXT = "いまのところ、急いで対応することはありません。";

/**
 * ③(相手の次の狙い)の文を組み立てる。上記の規則に従い、null(「出さない」)を
 * 返すのはmateが絡む場合と(A)の場合のみ。それ以外はすべて文を返す。
 */
export function explainPieceThreatFocus(input: PieceThreatFocusInput): string | null {
  const { engineReference, bandSquares, sfen } = input;

  // EngineReferenceが無い → 急ぐ話にならない
  if (engineReference === null) return NO_RUSH_TEXT;

  // 1. mateが絡む → 出さない(H-2)。baseline/afterPassのどちらかにmateが
  //    立っている場合はここで止める。
  if (engineReference.baseline.mate !== null || engineReference.afterPass.mate !== null) return null;

  // dropCpが無い、または閾値未満 → 急ぐ話にならない
  const { dropCp } = engineReference;
  if (dropCp === null || dropCp < DROP_THRESHOLD_CP) return NO_RUSH_TEXT;

  // captureSquareが無い → 急ぐ話にならない
  const captureSquare = engineReference.afterPass.captureSquare;
  if (captureSquare === null) return NO_RUSH_TEXT;

  const inBand = bandSquares.includes(captureSquare);

  // 2. (A) 帯が1件だけで、その1件がcaptureSquareと同じマス → 出さない
  //    (閾値を超え、captureSquareも解決している「③が出る局面」の中でだけ判定する。
  //    計画書2.1の実測がこの母集団の中でA/B/Cを数えているため、母集団をそろえる)
  if (inBand && bandSquares.length === 1) return null;

  const name = pieceNameAt(sfen, captureSquare);
  if (name === null) return NO_RUSH_TEXT; // 駒名が解決できない → 急ぐ話にならない

  const squareText = toJapaneseSquare(captureSquare);

  // (B) captureSquareが帯に含まれ、帯が2件以上
  if (inBand) {
    return `いま注意する駒のうち、このまま何もしないと、あなたの${squareText}の${name}が取られる可能性があります。`;
  }

  // (C) captureSquareが帯に含まれない
  return `このまま何もしないと、あなたの${squareText}の${name}が取られる可能性があります。`;
}
