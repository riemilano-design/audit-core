// STEP U6-I4(②を見る指標)。docs/STEP_U6-I3_PLAN_2026-09-12.md 19.
//
// 【このファイルがやること】
// - phase:"ready" の record 行を、②(opponent_intent)が「候補が無い / 候補があるのに黙った /
//   喋った(最も新しい根拠 / より古い根拠)/ 判定できない(理由 U-1〜U-8)」のどれかに分ける。
// - 純粋関数(classifyIntentStatementRow)と、detectIntents を呼ぶ薄い呼び出し
//   (summarizeIntentStatements)に分けている(19.4.0)。固定例は純粋関数に検出結果を直接渡し、
//   呼び出しの 1 行は試験 T-1・F-11 が見張る(P-32)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断。「根拠が新しい」は「正しい」ではない(19.5。CLAUDE.md ルール5)。
// - 本番の判定の複製。候補の集め方は本番の canSpeakAtIntentStage をそのまま呼ぶ(19.2 の 2)。
// - 黙って飛ばすこと。呼び直しの例外も、どの列にも当たらない行も「判定できない」に数える
//   (19.3。I-9 の `catch { continue; }` と `if (!matched) continue;` の形にしない ― P-22)。
// - 合否の判定。観測の集計であり、異常とは呼ばない(docs/AGENT_PROTOCOL.md 11.)。
//
// 【件数は照合時の data/intents/ に依存する】記録を取った後に data/intents/ が変わると、
// 同じ記録でも件数が変わる(P-22 と同じ性質。19.3)。

import {
  canSpeakAtIntentStage,
  type CoachExplanation,
} from "../../../apps/server/src/analysis/explanationGenerator.js";
import { detectIntents, type IntentDetectionResult } from "../../../apps/server/src/analysis/intentDetector.js";
import type { RecordLine } from "../invariants/types.js";

/** 薄い呼び出しから純粋関数へ渡す検出結果。例外は `{ ok: false }` にする(U-2)。 */
export type IntentDetection = { ok: true; results: IntentDetectionResult[] } | { ok: false };

/**
 * 「判定できない」の理由(19.3)。**上から順に判定し、最初に当たった理由を採る**(1 行に理由は 1 つ)。
 * U-1〜U-4 は全行に、U-5〜U-8 は「喋った」に当たった行にだけ判定する。
 */
export const UNDETERMINED_REASONS = {
  "U-1": "coach に [2] または [3] が無い",
  "U-2": "detectIntents が例外を投げた",
  "U-3": "列の判定が 2 つ以上当たった",
  "U-4": "列の判定がどれにも当たらない",
  "U-5": "名指しした intentId が呼び直した結果に無い",
  "U-6": "名指しした狙いの matchedSignatures が空",
  "U-7": "名指しした狙いが、比べる候補の集合に入らない",
  "U-8": "名指しした狙いの根拠が、候補どうしの最大より新しい",
} as const;

export type UndeterminedReason = keyof typeof UNDETERMINED_REASONS;

export type IntentStatementClass =
  | { column: "noCandidate" }
  | { column: "muted" }
  | { column: "spokeLatest" }
  | { column: "spokeOlder" }
  | { column: "undetermined"; reason: UndeterminedReason };

export interface IntentStatementCounts {
  /** 全手数(phase:"ready" の行数)。列とは**別に**数える(列の和と突き合わせるため)。 */
  totalPlies: number;
  /** 候補が 1 件も無い: [3] の status が "none"。 */
  noCandidate: number;
  /** 候補があるのに黙った: [3] が "none" でなく、[2] の template_id が opponent_intent_unclassified で始まる。 */
  muted: number;
  /** 喋った(判定できた分)のうち、最も新しい根拠に基づく。 */
  spokeLatest: number;
  /** 喋った(判定できた分)のうち、より古い根拠に基づく。 */
  spokeOlder: number;
  /** 判定できない、理由別。0 件の理由も必ず持つ(規則 11.5)。 */
  undetermined: Record<UndeterminedReason, number>;
}

const MUTED_TEMPLATE_PREFIX = "opponent_intent_unclassified";

/**
 * 指標自身の「根拠の新しさ」の定義: その狙いの署名の ply の最大(19.2 の 3 の (i))。
 * 本番の表示用の pickLatestMatchedSignature とは ply の値が一致するが、**そこから借りない**
 * (新しさは本番の選び方の条件ではなく、物差しの側の定義。2026-09-13 の司令塔の決定)。
 */
function latestEvidencePly(result: IntentDetectionResult): number {
  return Math.max(...result.matchedSignatures.map((signature) => signature.evidence.ply));
}

function undetermined(reason: UndeterminedReason): IntentStatementClass {
  return { column: "undetermined", reason };
}

/** 記録 1 行と検出結果から、列を 1 つ決める(純粋関数。19.1・19.2・19.3)。 */
export function classifyIntentStatementRow(record: RecordLine, detection: IntentDetection): IntentStatementClass {
  const coach: CoachExplanation[] | undefined = record.response.coach;
  const intentStage = coach?.find((c) => c.stage === "opponent_intent");
  const nextAimStage = coach?.find((c) => c.stage === "opponent_next_aim");
  if (intentStage === undefined || nextAimStage === undefined) return undetermined("U-1");
  if (!detection.ok) return undetermined("U-2");

  // 列の判定は互いに独立に行い、当たった数で U-3・U-4 を決める(先に当たった列を採らない)。
  const isNoCandidate = nextAimStage.status === "none";
  const isMuted = nextAimStage.status !== "none" && intentStage.template_id.startsWith(MUTED_TEMPLATE_PREFIX);
  const namedIntentId = intentStage.refers_to_intent_id;
  const isSpoke = namedIntentId !== null;

  const hitCount = [isNoCandidate, isMuted, isSpoke].filter(Boolean).length;
  if (hitCount >= 2) return undetermined("U-3");
  if (hitCount === 0) return undetermined("U-4");
  if (isNoCandidate) return { column: "noCandidate" };
  if (isMuted) return { column: "muted" };

  const named = detection.results.find((r) => r.intentId === namedIntentId);
  if (named === undefined) return undetermined("U-5");
  if (named.matchedSignatures.length === 0) return undetermined("U-6");

  // 比べる相手は、本番で [2] に選ばれうる集合と一致させる(19.2 の 2)。
  const comparable = detection.results.filter((r) => r.matchScore > 0 && canSpeakAtIntentStage(r));
  if (!comparable.includes(named)) return undetermined("U-7");

  const namedLatest = latestEvidencePly(named); // (i)
  const newestAmongComparable = Math.max(...comparable.map(latestEvidencePly)); // (ii)
  if (namedLatest === newestAmongComparable) return { column: "spokeLatest" };
  if (namedLatest < newestAmongComparable) return { column: "spokeOlder" };
  return undetermined("U-8");
}

function emptyCounts(): IntentStatementCounts {
  const undeterminedCounts = Object.fromEntries(
    Object.keys(UNDETERMINED_REASONS).map((reason) => [reason, 0]),
  ) as Record<UndeterminedReason, number>;
  return { totalPlies: 0, noCandidate: 0, muted: 0, spokeLatest: 0, spokeOlder: 0, undetermined: undeterminedCounts };
}

/** 判定できない行の合計(理由別の和)。 */
export function countUndetermined(counts: IntentStatementCounts): number {
  return Object.values(counts.undetermined).reduce((sum, n) => sum + n, 0);
}

export class IntentStatementCountMismatchError extends Error {}

/**
 * 記録の配列を数える(薄い呼び出し。19.4.0)。
 *
 * 【この関数の 3 行が守るもの ― 純粋関数の固定例では守られない(P-32)】
 * - `totalPlies` は検出の**前に**数える。例外のときに行ごと消えると、下の assert が鳴る
 * - `detectIntents` には記録行の `sfen` と `response.moveHistory` をそのまま渡す(T-1 が見張る)
 * - 例外は `{ ok: false }` にして純粋関数へ渡す。**`continue` しない**(F-11 が見張る)
 *
 * 【assert】表を出す前に「候補なし + 黙った + 喋った(判定できた分)+ 判定できない = 全手数」を
 * 確かめ、合わなければ例外を投げる。「判定できない = U-1 + … + U-8」「喋った(判定できた分)=
 * 最新 + 古い」は、この実装では**数え方そのものが定義**になっている(別々の数を突き合わせる形に
 * していない)。どこにも数えられずに行が消えたとき(M-6・C-3)に鳴るのは 1 本目である。
 */
export function summarizeIntentStatements(records: RecordLine[]): IntentStatementCounts {
  const counts = emptyCounts();

  for (const record of records) {
    if (record.phase !== "ready") continue;
    counts.totalPlies += 1;

    let detection: IntentDetection;
    try {
      detection = { ok: true, results: detectIntents(record.sfen, record.response.moveHistory) };
    } catch {
      detection = { ok: false };
    }

    const classified = classifyIntentStatementRow(record, detection);
    if (classified.column === "undetermined") {
      counts.undetermined[classified.reason] += 1;
    } else {
      counts[classified.column] += 1;
    }
  }

  const columnSum =
    counts.noCandidate + counts.muted + counts.spokeLatest + counts.spokeOlder + countUndetermined(counts);
  if (columnSum !== counts.totalPlies) {
    throw new IntentStatementCountMismatchError(
      `②の列の和(${columnSum})が全手数(${counts.totalPlies})と一致しません。どこにも数えられずに消えた行があります。`,
    );
  }

  return counts;
}
