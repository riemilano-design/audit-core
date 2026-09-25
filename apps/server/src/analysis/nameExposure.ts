// 戦法・陣形の名前を、ユーザーへ断定的に見せてよいかどうかを判断する唯一のモジュール。
// docs/DATA_MODEL.md の review_status(draft / human_reviewed / expert_verified / expired)は
// 「知識を追加してよいか」と「ユーザーへ見せてよいか」を分離する運用区分であり、
// CLAUDE.md ルール4番(未レビューの知識を、戦法・陣形・狙いの名前としてユーザーへ
// 断定的に見せない)への対応として、その「見せてよいか」の判断だけをここに集約する。
//
// 【このモジュールがやること】
// 1. exposeName(): review_statusが"draft"(および"expired")の場合にだけ、呼び出し元が
//    画面に添えるべき注記文(pendingNote)を返す。それ以外(human_reviewed/
//    expert_verified)はnull。
// 2. decideNameExposure(): STEP EXPO-1(docs/LANE_DIAG_LOG_2026-09.md §12.9)。
//    「名前を出す経路はすべて1つの関数を通す」(docs/DATA_MODEL.md)の実装として、
//    認識の状態(none/forming/completed/matched)・証拠の数・必要な駒の数・review_status
//    から hidden / hedged / named の3段階を返す純粋関数。
//    **この STEP では、この関数はまだ本体(explanationGenerator.ts・stateResponse.ts・
//    apps/web)から呼ばれていない。** 呼ぶのは測る道具(scripts/playtest)だけで、
//    画面の見え方は変わらない。閾値の値(NAME_EXPOSURE_VALUES)は統括の承認待ちの案であり、
//    本体へつなぐのは値が選ばれた後の別 STEP(EXPO-2)。
//
// 【このモジュールが絶対にやらないこと】
// - 将棋の判断(この形が何か・相手の意図が何か)は一切しない。
// - review_statusの値そのものを判断・変更しない(data/側で確定済みの値をそのまま使う)。
// - human_reviewedとexpert_verifiedを区別する判定を導入しない(両者とも「見せてよい」)。
//   同じく draft と expired も区別しない(どちらも「断定的に見せない」。docs/DATA_MODEL.md
//   の運用区分の表、2026-09-25 の人間の決定)。
// - 閾値の値をこのファイルの外に散らかすこと(値は NAME_EXPOSURE_VALUES 1 か所だけ)。
//
// site(呼び出し場所の種類)ごとに注記文が異なる理由: 画面上の表示形式
// (見出しへの括弧書き/マスの説明への括弧書き/セクションの独立した注意書き)が
// 異なるため、文言も表示形式に合わせて変える(STEP ζ-5で人間承認済みの文言)。
// 新しいsiteをこのモジュールの実装担当の判断で増やさないこと。

/**
 * 運用区分(docs/DATA_MODEL.md「運用区分 review_status」)。
 * `expired` は 2026-09-25 の人間の決定で追加した4つ目の値で、**露出は `draft` と同じ**
 * (名前を断定的に見せない)。data/ 側の実在件数は 0 件。
 */
export type ReviewStatus = "draft" | "human_reviewed" | "expert_verified" | "expired";

/** 名前を断定的に見せてよくない運用区分(draft と expired。両者を区別しない)。 */
function isPending(reviewStatus: ReviewStatus): boolean {
  return reviewStatus === "draft" || reviewStatus === "expired";
}

export type NameExposureSite = "shape" | "squares" | "section";

export interface ExposedName {
  name: string;
  /** draft のときだけ入る注記。draft 以外は null */
  pendingNote: string | null;
}

/** site ごとの、draft のときの注記文(STEP ζ-5で人間承認済み。一字一句変更しない)。 */
const PENDING_NOTE_BY_SITE: Record<NameExposureSite, string> = {
  shape: "内容を確認中の形",
  squares: "内容を確認中",
  section: "この形の説明は内容を確認中のため、参考程度に見てください。",
};

/**
 * 名前(戦法・陣形の名称)と、その review_status・使用場所(site)から、
 * ユーザーに見せてよい名前と、必要な注記(pendingNote)を返す。
 *
 * draft / expired の場合のみ pendingNote が入る(site に応じた文言)。
 * human_reviewed / expert_verified の場合、pendingNote は常に null
 * (両者を区別する判定はしない)。
 *
 * expired を draft と同じに扱うのは docs/DATA_MODEL.md の運用区分の表(2026-09-25 の
 * 人間の決定)による。**実在するレコードに expired は 0 件のため、この1行で画面の
 * 見え方は変わらない**(STEP EXPO-1)。
 *
 * name 自体は判断を加えず素通しする(この関数は「出してよいか」だけを判断し、
 * 名前の内容そのものは書き換えない)。
 */
export function exposeName(name: string, reviewStatus: ReviewStatus, site: NameExposureSite): ExposedName {
  return {
    name,
    pendingNote: isPending(reviewStatus) ? PENDING_NOTE_BY_SITE[site] : null,
  };
}

// ---------------------------------------------------------------------------
// STEP EXPO-1: 控えめな露出の規則(decideNameExposure)
// ---------------------------------------------------------------------------

/** 名前を出す判断の対象になる「1つの認識」。data/ の1レコード × 1局面に対応する。 */
export interface NameExposureInput {
  /** 形(shapes)・狙い(intents)・戦型(openings)のどれか。規則は今のところ kind で分岐しない */
  kind: "shape" | "intent" | "opening";
  /** 認識の状態。狙いの matched は形の completed と同じ扱い */
  status: "none" | "forming" | "completed" | "matched";
  /** 証拠の数(形・戦型 = formationEvidence、狙い = matchedSignatures) */
  evidenceCount: number;
  /**
   * 欠けの数(形・戦型 = missingSquares、狙い = unmatchedSignatures)。
   * **今の規則 R0〜R5 はこの値を読まない。** 呼び出し側が必ず持っている量なので入力に置き、
   * 将来この値を使う規則を足すときに入口を増やさなくて済むようにしてある。
   */
  missingCount: number;
  /** 必要な数(形 = optional でない required_pieces、戦型・狙い = recognition_pattern の長さ) */
  requiredCount: number;
  reviewStatus: ReviewStatus;
}

/** 名前の見せ方の3段階。hidden=出さない / hedged=控えめに言う / named=名前を言う。 */
export type NameExposureLevel = "hidden" | "hedged" | "named";

/** どの規則で決まったか(下の decideNameExposure の R0〜R5)。測る側が内訳を数えるために返す。 */
export type NameExposureRule = "R0" | "R1" | "R2" | "R3" | "R4" | "R5";

export interface NameExposureDecision {
  level: NameExposureLevel;
  /** hedged/named かつ draft・expired のときだけ入る注記(exposeName の shape と同じ文言)。それ以外は null */
  pendingNote: string | null;
  rule: NameExposureRule;
}

/** 規則 R3・R5・R2 が使う値。**この3つ以外の閾値を作らない。** */
export interface NameExposureValues {
  /** 必要な数がこの値以下の認識は名前を出さない(R3)。「対1の形」を名前にしないための下限 */
  minRequiredForName: number;
  /** forming を hedged にしてよい証拠の下限(R5) */
  minEvidenceForHedged: number;
  /** 証拠0件の completed / matched を hidden にするか(R2) */
  hideCompletedWithoutEvidence: boolean;
}

/**
 * 閾値の値。**1か所にまとめる**(docs/LANE_DIAG_LOG_2026-09.md §12.9 の設計判断)。
 *
 * **この値は案であり、統括の承認を経ていない。** そのため本体(explanationGenerator.ts・
 * stateResponse.ts・apps/web)はまだ decideNameExposure を呼んでいない。
 * 値を決めるための測定は scripts/playtest/lib/recognitionMeasure.ts が
 * A(今日の規則)・B(この案)・C(minEvidenceForHedged だけ 2)の3組で行う。
 */
export const NAME_EXPOSURE_VALUES: NameExposureValues = {
  minRequiredForName: 1,
  minEvidenceForHedged: 1,
  hideCompletedWithoutEvidence: true,
};

/**
 * 認識1件について、名前をどう見せてよいかを返す純粋関数。
 *
 * 規則は上から順に当て、**先に当たったものが勝つ**:
 * - **R0** `status === "none"` → hidden(何も立っていない)。
 * - **R1** `reviewStatus` が draft / expired のときは **named にしない**(CLAUDE.md ルール4番)。
 *   下の R4 で named になるはずだったところを hedged に落とし、`rule` は "R1" と記録する。
 * - **R2** `hideCompletedWithoutEvidence` かつ completed / matched かつ証拠0件 → hidden
 *   (盤に偶然その形があるだけで、その形へ向かった手が1つも観測されていない場合)。
 * - **R3** `requiredCount <= minRequiredForName` → hidden(必要な数が少なすぎる認識は名前にしない)。
 * - **R4** completed / matched → reviewed なら named、draft / expired なら hedged(R1)。
 * - **R5** forming → 証拠が `minEvidenceForHedged` 以上なら hedged、足りなければ hidden。
 *
 * **「今日の規則」も同じ関数で表せる**(測る側が前後を比べるため):
 * `values = { minRequiredForName: 0, minEvidenceForHedged: Number.POSITIVE_INFINITY,
 * hideCompletedWithoutEvidence: false }` を渡すと、R2 は無効・R3 は `requiredCount <= 0` で
 * 当たらない・R5 は証拠がいくつあっても hedged にならないので、
 * 「completed / matched は reviewed なら named・draft なら hedged、forming は hidden」= 今日と同じになる。
 *
 * この関数は将棋の判断をしない。渡された数と区分だけを見る。
 */
export function decideNameExposure(
  input: NameExposureInput,
  values: NameExposureValues = NAME_EXPOSURE_VALUES,
): NameExposureDecision {
  const note = isPending(input.reviewStatus) ? PENDING_NOTE_BY_SITE.shape : null;
  const decide = (level: NameExposureLevel, rule: NameExposureRule): NameExposureDecision => ({
    level,
    pendingNote: level === "hidden" ? null : note,
    rule,
  });

  if (input.status === "none") return decide("hidden", "R0");

  const isComplete = input.status === "completed" || input.status === "matched";

  if (values.hideCompletedWithoutEvidence && isComplete && input.evidenceCount === 0) {
    return decide("hidden", "R2");
  }
  if (input.requiredCount <= values.minRequiredForName) {
    return decide("hidden", "R3");
  }
  if (isComplete) {
    // R1: draft / expired は named にしない(最大で hedged)。
    return isPending(input.reviewStatus) ? decide("hedged", "R1") : decide("named", "R4");
  }
  // 残るのは forming だけ。
  return decide(input.evidenceCount >= values.minEvidenceForHedged ? "hedged" : "hidden", "R5");
}
