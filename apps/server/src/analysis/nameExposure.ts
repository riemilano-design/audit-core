// 戦法・陣形の名前を、ユーザーへ断定的に見せてよいかどうかを判断する唯一のモジュール。
// docs/DATA_MODEL.md の review_status(draft / human_reviewed / expert_verified)は
// 「知識を追加してよいか」と「ユーザーへ見せてよいか」を分離する運用区分であり、
// CLAUDE.md ルール4番(未レビューの知識を、戦法・陣形・狙いの名前としてユーザーへ
// 断定的に見せない)への対応として、その「見せてよいか」の判断だけをここに集約する。
//
// 【このモジュールがやること】
// review_statusが"draft"の場合にだけ、呼び出し元が画面に添えるべき注記文
// (pendingNote)を返す。それ以外(human_reviewed/expert_verified)はnull。
//
// 【このモジュールが絶対にやらないこと】
// - 将棋の判断(この形が何か・相手の意図が何か)は一切しない。
// - review_statusの値そのものを判断・変更しない(data/側で確定済みの値をそのまま使う)。
// - 新しい閾値・分類を作らない(draft/human_reviewed/expert_verifiedの3値のみを扱い、
//   human_reviewedとexpert_verifiedを区別する新しい判定も導入しない。両者とも
//   「見せてよい」として同じに扱う)。
//
// site(呼び出し場所の種類)ごとに注記文が異なる理由: 画面上の表示形式
// (見出しへの括弧書き/マスの説明への括弧書き/セクションの独立した注意書き)が
// 異なるため、文言も表示形式に合わせて変える(STEP ζ-5で人間承認済みの文言)。
// 新しいsiteをこのモジュールの実装担当の判断で増やさないこと。

export type ReviewStatus = "draft" | "human_reviewed" | "expert_verified";

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
 * draft の場合のみ pendingNote が入る(site に応じた文言)。
 * human_reviewed / expert_verified の場合、pendingNote は常に null
 * (両者を区別する判定はしない)。
 *
 * name 自体は判断を加えず素通しする(この関数は「出してよいか」だけを判断し、
 * 名前の内容そのものは書き換えない)。
 */
export function exposeName(name: string, reviewStatus: ReviewStatus, site: NameExposureSite): ExposedName {
  return {
    name,
    pendingNote: reviewStatus === "draft" ? PENDING_NOTE_BY_SITE[site] : null,
  };
}
