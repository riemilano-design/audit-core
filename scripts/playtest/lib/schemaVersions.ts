// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §3)。Failure Event と diagnosis-moment の「今の版」と、スキーマのファイルがある版の並びを
// **この 1 か所**に置く(司令塔 e3 の決定)。
//
// 【版の番号の決め方】先にスキーマをコミットした STEP が次の番号を取り、後の STEP はその次を取る(D2.5 計画 Q-3)。
// 載せ替えで番号が変わるときは、このファイルと、スキーマを作る道具の引数だけを替える。**コミットのときは並びを連番にする**(抜けたままコミットしない)。
// 【古い版】スキーマのファイルは版ごとに 1 つ増やし、古い版のファイルは消さない(JSON v0 計画 3.2)。

export const FAILURE_EVENT_SCHEMA_VERSION = "0.6" as const;
/** Failure Event のスキーマのファイルがある版(古い版のファイルは消さない) */
export const KNOWN_SCHEMA_VERSIONS = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6"] as const;

export const DIAGNOSIS_MOMENT_SCHEMA_VERSION = "0.3" as const;
/** diagnosis-moment のスキーマのファイルがある版 */
export const KNOWN_DIAGNOSIS_MOMENT_SCHEMA_VERSIONS = ["0.1", "0.2", "0.3"] as const;

/**
 * STEP D-SCREEN-2 の欄(branch.evaluationSource・counterfactual.pvSource・provenance.record.meta.screen)を足す前の版。
 * 今の版が「この版 + D-SCREEN の欄」であることを試験が見る(scratchpad の道具 dscreen2-schema-gen.py の基の版の引数と同じ値)。
 */
export const FAILURE_EVENT_SCREEN_BASE_VERSION = "0.5" as const;
export const DIAGNOSIS_MOMENT_SCREEN_BASE_VERSION = "0.2" as const;
