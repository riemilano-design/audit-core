// candidateMoveSafetyCheck.ts(基準局面・候補手後の局面のMultiPV参考評価を取得し、
// candidateMovesと対応付けるだけの機械的なモジュール)の結果から、
// 「安全確認を経た候補手」(CLAUDE.mdルール3番)かどうかを実際に判定する、決定的な純粋関数。
//
// 【人間承認の記録(2026-09-10。docs/PHASES.md Unit 4 再設計案 STEP 4-2)】
// ルール3番の解釈(決定1): 「安全確認を経た候補手」= ①基準局面との評価値低下が閾値未満、
// かつ ②候補手を指した後に相手視点で詰みにならない手。評価値を取得できない手の扱いは
// 既存(hasUsableEvaluation、candidateMoveExplanation.ts)のまま変えない。
//
// 判定はこのファイルだけで行う。エンジンとの通信・USI出力のパースはengine/へ、
// MultiPV結果の取得・candidateMovesとの対応付けはcandidateMoveSafetyCheck.tsへ、
// それぞれ責務を残したままにする(責務境界は変えない)。エンジン・LLMには依存しない
// (入力はCandidateMoveSafetyCheckResultの値のみ)。
//
// 【閾値について(決定2。重要な但し書き)】
// REFERENCE_DROP_THRESHOLD_CP = 300 は、2026-09-10 に人間が承認した値である。
// 根拠は、本番エンジン(YANEURAOU_ENGINE_MATERIAL / MaterialLv1、駒割りのみの評価)・
// 思考時間2秒・MultiPV1という条件のもとで実測した次の値である(docs/PHASES.md
// Unit 4 再設計案 STEP 4-2 の実測表): P-1局の通常の駒組み6局面・9候補の低下が
// -22〜+76cp、P-2で観測された駒損候補(C局28手目 金５八→４七)の低下が655〜878cp、
// 別の駒損候補(C局26手目 歩４七→４六)の低下が470〜478cp。
//
// この300という値は「将棋一般として客観的に安全とみなせる閾値」では**ない**。
// あくまで、このアプリが候補手をユーザーに見せるかどうかを機械的に決めるための
// **本アプリ内の候補手除外基準**である。エンジンの種類・思考時間・MultiPVの設定等の
// 条件を変える場合、この値をそのまま正当化してはならない(条件が変われば人間の
// 再検討が必要)。150cp・500cpなど他の値との比較で「これが最適な閾値である」と
// 断定する根拠もない(実測はP-1・P-2という限られた局面・候補手数にとどまる)。
//
// 【方式(i)の限界(同STEPの実測で確認済み)】
// このフィルタが除外できるのは、駒割りのみの評価で2秒の探索によって低下が現れる
// 「駒損が読める手」に限られる。位置的な問題(C局16手目)や、エンジンの最善手として
// 現れる受けの手(C局30手目)は、この方式では捕捉できない。
//
// 【決定3(詰み)】候補手後に相手視点で詰みあり(mateかつvalue>0)→ 除外。
// 基準局面自体が詰み評価(baselineがmate)→ 評価値の低下比較は行わない
// (詰みの手数を比較対象にしない)。ただし詰み条件は基準局面の状態に関わらず
// 独立に判定する(詰み判定と評価値低下判定を混同しない)。
//
// 【決定5(基準局面の評価値が取得できない場合。2026-09-10人間承認「除外で」)】
// 基準局面のMultiPV結果が空、または先頭行にscoreが無い場合、低下量を検証できない。
// 候補手側のscore無しを個別除外している既存挙動(hasUsableEvaluation)と対称に、
// この場合は候補手を全件除外する(呼び出し側でnot_ready + baseline_evaluation_unavailable
// として扱う)。

import type { CandidateMoveSafetyCheckResult } from "./candidateMoveSafetyCheck.js";
import type { UsiScore } from "../engine/usiInfoParser.js";

/**
 * 2026-09-10人間承認の閾値(cp)。ファイル冒頭コメントの但し書きを参照。
 * 本アプリ内の候補手除外基準であり、将棋一般の客観的な安全閾値ではない。
 */
export const REFERENCE_DROP_THRESHOLD_CP = 300;

export interface CandidateMoveReferenceFilterResult {
  /**
   * 基準局面の評価値(自分視点)が取得できず、低下量を検証できない状態か
   * (決定5)。trueの場合、excludedは常にすべてtrue(候補手を全件除外する)。
   */
  baselineUnavailable: boolean;
  /** safetyCheck.evaluations(=candidateMovesと同じ順序)ごとの除外判定。 */
  excluded: boolean[];
}

/** 候補手後(相手視点)の評価が「自分が詰まされる」ことを示すか。
 * 基準局面の状態(mateかどうか)に関わらず独立に判定する(決定3)。 */
function isOpponentMateForSelf(candidateScore: UsiScore | undefined): boolean {
  return candidateScore !== undefined && candidateScore.type === "mate" && candidateScore.value > 0;
}

/**
 * 基準・候補手後のいずれもcpのとき、評価値の低下が閾値以上かどうか。
 * 低下 = 基準(自分視点)−候補手後(自分視点)。候補手後の評価はエンジン出力(相手視点)を
 * そのまま使うため、自分視点への反転(符号を変える)は加算(baseline + candidate)と同じになる
 * (baseline − (−candidate) = baseline + candidate)。
 */
function isDropBeyondThreshold(baseline: UsiScore, candidateScore: UsiScore | undefined): boolean {
  if (baseline.type !== "cp" || candidateScore === undefined || candidateScore.type !== "cp") {
    return false;
  }
  return baseline.value + candidateScore.value >= REFERENCE_DROP_THRESHOLD_CP;
}

/**
 * candidateMoveSafetyCheck.tsが取得したMultiPV参考評価から、候補手ごとに
 * 「安全確認を経た候補手」(決定1〜3・決定5)かどうかを判定する。
 *
 * この関数自身は将棋の知識・エンジン・LLMに依存しない、入力のみで決まる純粋関数
 * (同じ入力に対して常に同じ結果を返す)。
 */
export function filterCandidateMovesByReferenceEvaluation(
  safetyCheck: Pick<CandidateMoveSafetyCheckResult, "baselineMultiPv" | "evaluations">,
): CandidateMoveReferenceFilterResult {
  const baseline = safetyCheck.baselineMultiPv[0]?.score;

  if (baseline === undefined) {
    return {
      baselineUnavailable: true,
      excluded: safetyCheck.evaluations.map(() => true),
    };
  }

  const excluded = safetyCheck.evaluations.map((evaluation) => {
    const candidateScore = evaluation.multiPv[0]?.score;
    if (isOpponentMateForSelf(candidateScore)) return true;
    if (baseline.type === "mate") return false; // 決定3: 基準局面が詰みなら低下比較を行わない
    return isDropBeyondThreshold(baseline, candidateScore);
  });

  return { baselineUnavailable: false, excluded };
}
