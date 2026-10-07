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

/**
 * STEP OBS-2(docs/LANE_DIAG_LOG_2026-09.md §12.2)。契約 hypothesis(仮説台帳の 1 行)の今の版と、スキーマのファイルがある版(末尾に独立して置く)。
 * **`HYPOTHESIS_SCHEMA_VERSION` は据え置き**(STEP EXPO-1 §12.9)。0.2 は `knowledge.reviewStatus` に `expired` を足した版で、
 * 書く側の既定は変えない ― 既存の記録はすべて 0.1 であり、検査は `KNOWN_HYPOTHESIS_SCHEMA_VERSIONS` の両方を受ける(行の `schemaVersion` で選ぶ)。
 * 0.3 は `lane` の enum に `reply`・`fork` を足した版(STEP 契約の仮説 v0.3、2026-09-26。司令塔の設計判断)。
 * こちらも書く側の既定は変えない ― 行の `schemaVersion` が版を選ぶ仕組みはそのまま。
 */
export const HYPOTHESIS_SCHEMA_VERSION = "0.1" as const;
/**
 * 0.4 は STEP R2(docs/STEP_LLM_SEATS_R2_CONTRACT_2026-09-30.md): 席の出力の欄(kind・packetRef・internal …)を足した版。既定は据え置き。
 * 0.5 は STEP S-4(audit-core/docs/CORE_CONNECTION_S4_PLAN_2026-10-06.md §2.1(b)): `observations` の `minItems` を外した版
 * (`kind` が `unanswerable`・`needed_observation` の行は観測 0 件でよい ― H-12 が kind で見る)。既定は据え置き。
 */
export const KNOWN_HYPOTHESIS_SCHEMA_VERSIONS = ["0.1", "0.2", "0.3", "0.4", "0.5"] as const;

/**
 * 席(`lib/seatOutput.ts`)と整理役(`lib/integration.ts`)が書く hypothesis 行の `schemaVersion` は
 * **この 1 つの定数**を読む(S-6 計画 `audit-core/docs/CORE_CONNECTION_S6_PLAN_2026-10-07.md` (b)。
 * S-5 の結果 §10.4 発見 (A): S-4 で契約を 0.5 に上げたのに整理役側だけ 0.4 を直書きしていて、
 * 観測 0 件の代表が schema で落ちていた)。`lib/seatOutput.ts` はこの値を再輸出する ― 定義は 2 か所に置かない。
 */
export const SEAT_HYPOTHESIS_SCHEMA_VERSION = "0.5" as const;

/**
 * STEP S-7(audit-core/docs/CORE_CONNECTION_S7_PLAN_2026-10-07.md (e))。契約 integration(整理役の出力。道具が保存する形)の
 * 今の版と、スキーマのファイルがある版(末尾に独立して置く)。0.2 は `clusters[].packetRefs` の `minItems` を外した版
 * (観測 0 件だけの成員で束んだとき、整理役が根を作らずに済むようにする)。**保存済みの記録はすべて `schemaVersion: "0.1"` で、
 * `validateIntegration` は記録自身の `schemaVersion` で版を解決するため、既存の記録は 1 行も動かない。**
 */
export const INTEGRATION_SCHEMA_VERSION = "0.2" as const;
/** integration のスキーマのファイルがある版(古い版のファイルは消さない) */
export const KNOWN_INTEGRATION_SCHEMA_VERSIONS = ["0.1", "0.2"] as const;
