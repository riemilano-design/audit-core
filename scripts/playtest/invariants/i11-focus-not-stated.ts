// I-11(沈黙、draft): 「本番が③を出すと決めた局面で、③がその駒を名指していない」を
// 検出する(STEP 5-F の A-4。docs/STEP_5-F_PLAN_2026-09-12.md 14.)。
//
// 出典: docs/STEP_5-F_PLAN_2026-09-12.md 5.(i)・14.4(2026-09-12 人間決定 H-18)。
//
// 【この不変条件が言わないこと(必ず読むこと)】
// - **300cp という閾値が初心者にとって適切かは判定しない。** 本番が③を出すと
//   決めた局面で③が出ているか、だけを見る。
// - 閾値を本番(apps/server/src/analysis/pieceThreatFocusExplanation.ts の
//   DROP_THRESHOLD_CP)から import しているため、**I-11 は「閾値が正しいか」を
//   検証できない。** 見るのは**「閾値と画面が整合しているか」**だけである。
// - これは docs/AGENT_PROTOCOL.md 11 の「**不変条件は仕様の写しであって仕様の
//   源ではない**」に照らして正しい形である。import は、その写しをそのまま実装して
//   いる。**自前で 300 を持たない理由はここにある** ―― 写経すると、本番の閾値を
//   変えたときに I-11 だけ古い値で残り、**本番が黙ると決めた行で鳴く**。
// - これは「最善手を言え」ではない。候補手そのものの良し悪しは判断しない。
//
// 【この不変条件の位置づけ(H-20、人間決定)】
// - ③(focusText)は STEP 5-F の A-2b・A-2c・A-3 で**既に本番へ入っている**。
//   したがって **I-11 は最初から 0 件を返す。改善の証拠ではなく、壊れたら鳴る
//   見張りである。**
// - 見張りが生きていることは、recorder.ts の focusEngine を外して I-11 を回し、
//   finding が出ることで確かめる(計画書 14.5 の 2)。
// - 一般則(計画書 14.11): **後から入る指標には前の値が無い。改善の証拠は作れない
//   ので、見張りが鳴ることを人工的に確かめる方へ切り替える。**
//
// 判定(記録の1行から読むものだけで決める。新しい将棋の判断をしない):
// 1. 緊急事態(エンジンの事実): engineReference があり、dropCp !== null かつ
//    dropCp >= DROP_THRESHOLD_CP、かつ afterPass.captureSquare !== null。
//    **I-7 と同じ読み方**(i7-urgent-but-other-talk.ts)。
// 2. (A) ではない: 帯(plan.urgentMessages の kind: "piece_attacked")が
//    **ちょうど1件で、そのマスが captureSquare と同じ**なら対象外。本番が
//    explainPieceThreatFocus の (A) で「帯が既に同じ駒を名指しているので③は
//    重ねて言わない」と決めた局面であり、③が黙るのが正しい。
// 3. ③がその事実を述べていない: plan.focusText が null / 欄なし、または
//    toJapaneseSquare(captureSquare) を含まない。
//
// 検出しない: engineReference が null(測っていない)、終局、
//   focusTextState が "pending"(まだ計算していない。記録のready行では起きない
//   はずだが、起きたら「言っていない」ではなく「まだ言っていない」なので分ける)。
//
// 表記(toJapaneseSquare)は本番の文言生成(pieceThreatFocusExplanation.ts)と
// 同じ関数を使う。表記を二重に持たない。

import { DROP_THRESHOLD_CP } from "../../../apps/server/src/analysis/pieceThreatFocusExplanation.js";
import type { PieceThreatMessage } from "../../../apps/server/src/analysis/pieceThreatExplanation.js";
import { toJapaneseSquare } from "../../../apps/server/src/notation/japaneseSquare.js";
import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-11";

/**
 * 帯([0])のうち「当たり」の事実を取り出す。
 *
 * 【squareが応答の型に無いことについて(実測して確かめた)】
 * ReachablePlanBody.urgentMessages の宣言は `{ kind: string; text: string }[]` で、
 * squareは型に現れない。しかし実体はPieceThreatMessage(analysis/
 * pieceThreatExplanation.ts)であり、JSONにはsquare・attackerSquaresが載る。
 * 2026-09-12に記録44ファイルを走査したところ、piece_attacked 718件のうち
 * **510件がsquareを持ち、欠けている208件は2026-09-10〜11の13ファイル**
 * (run1/run2/yure-01〜10/run-equivalence-check)だけだった。squareが足される
 * 前の世代の記録であり、現行世代(u6f-*・u6a-*)は全件持っている。
 *
 * 型に無いものを当てにしないため、**欄が無い場合を「情報が無い」として明示的に
 * 扱う**(I-10と同じ扱い。docs/STEP_5-E_PLAN_2026-09-12.md)。squareが1件でも
 * 欠けていると(A)の判定(帯1件・同じマス)が確かめられないため、**除外しない**
 * ＝判定を続ける。黙って(A)扱いにして見逃すより、鳴って人が見る方を選ぶ。
 */
function bandAttacked(record: RecordLine): { count: number; squares: string[]; complete: boolean } {
  const attacked = record.response.plan.urgentMessages.filter((m) => m.kind === "piece_attacked");
  const squares = attacked
    .map((m) => (m as Partial<PieceThreatMessage>).square)
    .filter((sq): sq is string => typeof sq === "string");
  return { count: attacked.length, squares, complete: squares.length === attacked.length };
}

export const i11FocusNotStated: Invariant = {
  id: ID,
  title:
    "パスすると評価が大きく落ち相手の最善が捕獲を含む局面で、③(なぜそれが重要か)がその駒のマスを名指していない",
  type: "沈黙",
  status: "draft",
  source: "docs/STEP_5-F_PLAN_2026-09-12.md 5.(i)・14.4(閾値は本番のDROP_THRESHOLD_CPをimportする。2026-09-12人間決定H-18)",
  check(records: RecordLine[]): Finding[] {
    const findings: Finding[] = [];

    for (const record of records) {
      if (record.phase !== "ready") continue;
      if (record.response.status.isEnd) continue;

      // 1. 緊急事態か(エンジンの事実)。
      const engineReference = record.engineReference;
      if (!engineReference) continue;
      const { dropCp, afterPass } = engineReference;
      if (dropCp === null || dropCp < DROP_THRESHOLD_CP) continue;
      const captureSquare = afterPass.captureSquare;
      if (captureSquare === null) continue;

      // まだ計算していない行は「言っていない」ではない(13.1の状況1)。
      if (record.response.plan.focusTextState === "pending") continue;

      // 2. (A)か(帯が1件で同じマス)。本番が③を黙ると決めた局面。
      // squareが欠けている古い世代の記録では(A)を確かめられないので除外しない
      // (bandAttackedのコメント参照)。
      const band = bandAttacked(record);
      if (band.complete && band.count === 1 && band.squares[0] === captureSquare) continue;

      // 3. ③がそのマスを名指しているか。
      const focusText = record.response.plan.focusText ?? null;
      const squareText = toJapaneseSquare(captureSquare);
      if (focusText !== null && focusText.includes(squareText)) continue;

      const condition = focusText === null ? "focus_absent" : "focus_other_square";
      const bandNote = band.complete ? "" : "(帯のマス情報が欠けている古い世代の記録です)";
      const conditionText =
        focusText === null
          ? "③に文がありません。"
          : `③が別のことを述べています(「${focusText}」)。`;

      findings.push({
        invariantId: ID,
        kifuId: "",
        ply: record.ply,
        phase: record.phase,
        condition,
        detail: `パスすると先手視点で約 ${dropCp}cp 落ち、相手の最善 ${afterPass.bestmove ?? "不明"} が ${captureSquare}(${squareText})の駒を取る局面で、帯は ${band.count} 件${bandNote}、${conditionText}`,
        sfen: record.sfen,
        senteMove: record.senteMove,
        goteMove: record.goteMove,
      });
    }

    return findings;
  },
};
