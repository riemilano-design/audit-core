// STEP P-26(2026-09-13、司令塔承認済み): GET /api/game がバックグラウンド解析を
// 起動してよいかを決める純粋関数。
//
// 【なぜ切り出すか】
// server.tsには直接のテストが1つも無い(2026-09-13の独立監査で確認)。
// 起動条件をserver.tsのif文に直接書くと、検証手段が実機だけになる。
// 「型が通るのに壊れる」経路にはテストを置く(docs/STEP_5-F_PLAN_2026-09-12.md
// 13.11の一般則。toCachedPlanのときと同じ考え)。
//
// 【この関数がやらないこと】
// 将棋の判断はしない。サーバーが組み立てた状態(2つのstate)とキーの一致だけで決める。

import type { CandidateMoveState, FocusTextState } from "./stateResponse.js";

/**
 * GET /api/game でバックグラウンド解析を起動してよいか。
 *
 * 【なぜfocusTextStateも見るか(P-26)】
 * 候補手が0件の局面ではhasCandidateMoves(stateResponse.ts:1593)が
 * **キャッシュを見ずに同期的に**falseになり、candidateMoveStateは
 * キャッシュ無しのまま"unavailable"で確定する。一方focusTextStateは
 * 現局面に一致するcachedPlanがあるかだけで決まるため"pending"のまま残る。
 * candidateMoveStateだけを見ていると、この組み合わせで誰も解析を始めず、
 * ③が「急ぐことがないか、いま確かめています。」のまま止まる
 * (2026-09-13に実機で再現。30秒経っても変わらず、エンジンは0本だった)。
 *
 * 【なぜfailedPlanKeyで止めるか(P-26の(i)、司令塔承認済み)】
 * runBackgroundPlanAnalysisはキャッシュを**成功経路でしか書かない**。
 * 失敗するとfocusTextStateは"pending"のまま固定されるため、この条件だけでは
 * GETのたびに解析が起動し直し、失敗し続ける局面で再試行が止まらない
 * (エンジンを掴む処理なので、対局そのものの応答に影響しうる)。
 * 失敗したキーを1つ覚えて、同じキーでは起動しない。局面か目標形が変われば
 * キーが変わるので自然に解ける。
 *
 * **この歯止めはP-23を偶発的から確定的に変える**(一度失敗したらその局面では
 * 二度と③が出ない)。**したがってweb側が「まだ分かりません」を必ず出すことが
 * 前提である**(計画書4.2)。
 *
 * 【POST経路には掛けない】
 * この関数はGETからの自動起動にだけ使う。POST(着手・新規対局・目標形の選択)は
 * ユーザーの操作であり、黙って起動を止めると「押したのに何も起きない」になる。
 */
export function shouldStartBackgroundAnalysisOnGet(
  plan: { candidateMoveState: CandidateMoveState; focusTextState: FocusTextState },
  planKey: string,
  failedPlanKey: string | undefined,
): boolean {
  // 同じキーで一度失敗している → 起動しない(再試行が止まらなくなるため)。
  if (failedPlanKey !== undefined && planKey === failedPlanKey) return false;
  return plan.candidateMoveState === "pending" || plan.focusTextState === "pending";
}
