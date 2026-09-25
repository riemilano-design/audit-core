// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §3)。Failure Event と diagnosis-moment の「今の版」と、スキーマのファイルがある版の並びを
// **この 1 か所**に置く(司令塔 e3 の決定)。
//
// 【版の番号の決め方】先にスキーマをコミットした STEP が次の番号を取り、後の STEP はその次を取る(D2.5 計画 Q-3)。
// 載せ替えで番号が変わるときは、このファイルと、スキーマを作る道具の引数だけを替える。**コミットのときは並びを連番にする**(抜けたままコミットしない)。
// 【古い版】スキーマのファイルは版ごとに 1 つ増やし、古い版のファイルは消さない(JSON v0 計画 3.2)。

export const FAILURE_EVENT_SCHEMA_VERSION = "0.7" as const;
/** Failure Event のスキーマのファイルがある版(古い版のファイルは消さない) */
export const KNOWN_SCHEMA_VERSIONS = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7"] as const;

export const DIAGNOSIS_MOMENT_SCHEMA_VERSION = "0.4" as const;
/** diagnosis-moment のスキーマのファイルがある版 */
export const KNOWN_DIAGNOSIS_MOMENT_SCHEMA_VERSIONS = ["0.1", "0.2", "0.3", "0.4"] as const;

/**
 * STEP D-SCREEN-2 の欄(branch.evaluationSource・counterfactual.pvSource・provenance.record.meta.screen)を足す前の版。
 * 今の版が「この版 + D-SCREEN の欄」であることを試験が見る(scratchpad の道具 dscreen2-schema-gen.py の基の版の引数と同じ値)。
 */
export const FAILURE_EVENT_SCREEN_BASE_VERSION = "0.5" as const;
export const DIAGNOSIS_MOMENT_SCREEN_BASE_VERSION = "0.2" as const;

/**
 * STEP D2.6(docs/STEP_D2.6_PLAN_2026-09-17.md §4)。D-SCREEN の欄が入った版(= D2.6 の userMoveFacts を足す前の版)。
 * 今の版が「この版 + counterfactual.{actual,pv}.userMoveFacts」であることを試験が見る。D-SCREEN の欄の試験もこの版を読む
 */
export const FAILURE_EVENT_MOVE_FACTS_BASE_VERSION = "0.6" as const;
export const DIAGNOSIS_MOMENT_MOVE_FACTS_BASE_VERSION = "0.3" as const;

/** STEP D4(docs/STEP_D4_PLAN_2026-09-15.md §7)。契約 diagnosis-gate の今の版と、スキーマのファイルがある版(ほかの契約の定数とは独立に末尾に置く) */
export const DIAGNOSIS_GATE_SCHEMA_VERSION = "0.1" as const;
export const KNOWN_DIAGNOSIS_GATE_SCHEMA_VERSIONS = ["0.1"] as const;

/** STEP D3-COND(docs/STEP_D3-COND_PLAN_2026-09-15.md §6)。--events-cond の行の契約 diagnosis-condition の版 */
export const DIAGNOSIS_CONDITION_SCHEMA_VERSION = "0.1" as const;
/** diagnosis-condition のスキーマのファイルがある版 */
export const KNOWN_DIAGNOSIS_CONDITION_SCHEMA_VERSIONS = ["0.1"] as const;
/** --cond-summary の契約 diagnosis-condition-summary の版(スキーマのファイルは置いていない。試験が欄を見る) */
export const DIAGNOSIS_CONDITION_SUMMARY_SCHEMA_VERSION = "0.1" as const;

/** STEP D6(docs/STEP_D6_PLAN_2026-09-16.md §6)。契約 diagnosis-report の今の版と、スキーマのファイルがある版(ほかの契約の定数とは独立に末尾に置く) */
export const DIAGNOSIS_REPORT_SCHEMA_VERSION = "0.1" as const;
export const KNOWN_DIAGNOSIS_REPORT_SCHEMA_VERSIONS = ["0.1"] as const;

/** STEP OBS-2(docs/LANE_DIAG_LOG_2026-09.md §12.2)。契約 hypothesis(仮説台帳の 1 行)の今の版と、スキーマのファイルがある版(末尾に独立して置く) */
export const HYPOTHESIS_SCHEMA_VERSION = "0.1" as const;
export const KNOWN_HYPOTHESIS_SCHEMA_VERSIONS = ["0.1"] as const;
