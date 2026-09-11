// STEP T-5(T5-B: 分母の報告)。docs/STEP_T-5_PLAN_2026-09-11.md 2. T5-B、
// docs/COVERAGE_AND_OUTCOME_PROPOSAL.md 4.2 の列をそのまま使う。
//
// 【このファイルがやること】
// - phase:"ready"のrecord行を、既存フィールドの機械的な読み取りだけで6列に数える
//   純粋関数(countDenominators)。
// - 複数入力(kifuId単位)の集計に加え、探索の記録(meta.mode === "explore")が
//   あればmeta.profileごとの小計もあわせて返す(buildDenominatorReport)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・新しい閾値・文言。数える基準はいずれも既存のstatus/フィールド値
//   そのままで、このファイルでは新しい判定を作らない。
// - 「異常」の判定。ここで数えるのは観測の集計であり、不変条件ではない
//   (docs/AGENT_PROTOCOL.md 11.、STEP T-5計画書 T5-B)。

import type { RecordLine } from "../invariants/types.js";

/** 「認識あり」とみなすCoachExplanation.statusの集合(提案書「forming以上」)。 */
const RECOGNIZED_STATUSES = new Set(["forming", "matched", "completed"]);

const EXCLUDED_REASON = "excluded_by_reference_evaluation";

export interface DenominatorCounts {
  /** 全手数(phase:"ready"の行数)。 */
  totalPlies: number;
  /** 認識あり: coachにstatusがforming/matched/completedの要素が1件以上ある。 */
  hasRecognition: number;
  /** 道のりあり: plan.candidateMoveLabelsが空でない。 */
  hasRoute: number;
  /** 候補手あり: candidateMoveState === "ready" && candidateMove?.status === "ready"。 */
  hasCandidateMove: number;
  /** 候補手が全件除外: candidateMoveState === "ready" && candidateMove.status ===
   * "not_ready" && notReadyReason === "excluded_by_reference_evaluation"。 */
  candidateExcluded: number;
  /** いずれも無し(沈黙): 認識あり・道のりあり・候補手あり のいずれにも該当しない。 */
  silent: number;
}

function emptyCounts(): DenominatorCounts {
  return {
    totalPlies: 0,
    hasRecognition: 0,
    hasRoute: 0,
    hasCandidateMove: 0,
    candidateExcluded: 0,
    silent: 0,
  };
}

/** phase:"ready"のrecord行を6列で数える(定義はSTEP T-5計画書2. T5-Bの表のとおり)。
 * phase:"immediate"の行はここで無視するため、呼び出し側で事前にフィルタしなくてよい。
 * coachがundefinedの行は認識なしとして数える(STEP T-5計画書 T5-B)。 */
export function countDenominators(records: RecordLine[]): DenominatorCounts {
  const counts = emptyCounts();

  for (const record of records) {
    if (record.phase !== "ready") continue;
    counts.totalPlies += 1;

    const { response } = record;
    const coach = response.coach;
    const hasRecognition = coach !== undefined && coach.some((c) => RECOGNIZED_STATUSES.has(c.status));
    if (hasRecognition) counts.hasRecognition += 1;

    const { plan } = response;
    const hasRoute = Object.keys(plan.candidateMoveLabels).length > 0;
    if (hasRoute) counts.hasRoute += 1;

    const hasCandidateMove = plan.candidateMoveState === "ready" && plan.candidateMove?.status === "ready";
    if (hasCandidateMove) counts.hasCandidateMove += 1;

    const candidateExcluded =
      plan.candidateMoveState === "ready" &&
      plan.candidateMove?.status === "not_ready" &&
      plan.candidateMove.notReadyReason === EXCLUDED_REASON;
    if (candidateExcluded) counts.candidateExcluded += 1;

    if (!hasRecognition && !hasRoute && !hasCandidateMove) counts.silent += 1;
  }

  return counts;
}

/** 入力1件(1本のJSONLファイル由来)の集計に必要な最小限の情報。 */
export interface DenominatorInput {
  kifuId: string;
  mode: string | undefined;
  profile: string | undefined;
  records: RecordLine[];
}

/** 表の1行分(入力ごと、またはプロファイルごと)。 */
export interface DenominatorRow {
  label: string;
  counts: DenominatorCounts;
}

export interface DenominatorReport {
  perInput: DenominatorRow[];
  /** 探索の記録(mode: "explore")が1件も無ければundefined。 */
  perProfile: DenominatorRow[] | undefined;
}

/** 入力ごとの集計に加え、探索の記録(meta.mode === "explore")があれば
 * meta.profileごとの小計もあわせて返す(STEP T-5計画書2. T5-B)。
 * profileが無い探索の記録は"unknown"として集計する。 */
export function buildDenominatorReport(inputs: DenominatorInput[]): DenominatorReport {
  const perInput: DenominatorRow[] = inputs.map((input) => ({
    label: input.kifuId,
    counts: countDenominators(input.records),
  }));

  const exploreInputs = inputs.filter((input) => input.mode === "explore");
  if (exploreInputs.length === 0) {
    return { perInput, perProfile: undefined };
  }

  const byProfile = new Map<string, RecordLine[]>();
  for (const input of exploreInputs) {
    const profile = input.profile ?? "unknown";
    const list = byProfile.get(profile) ?? [];
    list.push(...input.records);
    byProfile.set(profile, list);
  }

  const perProfile: DenominatorRow[] = Array.from(byProfile.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([profile, records]) => ({ label: profile, counts: countDenominators(records) }));

  return { perInput, perProfile };
}
