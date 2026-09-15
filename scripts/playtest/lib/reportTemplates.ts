// STEP D6(docs/STEP_D6_PLAN_2026-09-16.md §3・§4)。言い換えの契約の表を **この 1 か所**に置く:
// 文の型・差し込み口の固定の欄・禁止語・文の種類ごとの終わり・許す直書き・用語・形勢の区分の境の承認日。
//
// 【判断的知識】§4.2 の禁止語と §4.3 の文の終わりは司令塔の承認済み(計画 10.4)。文の型の語を変えるときは、計画を直してから変える。
// 【このファイルが絶対にやらないこと】数を数えること・判定すること(lib/diagnosisReport.ts)。LLM・エンジン。

/** 形勢の区分の境(lib/failureEvent.ts の STANDING_BOUNDS)を人間が承認した日(計画 3.0。文に直書きしない ― R-3) */
export const STANDING_BOUNDS_APPROVED_ON = "2026-09-15" as const;

/** 出力の文の種類(計画 §6 の `kind`) */
export type SentenceKind = "heading" | "F-1" | "F-2" | "F-2b" | "F-3" | "F-4" | "F-5" | "F-6" | "verdict" | "none" | "N-1" | "N-2" | "N-3";

/** 文の型(計画 3.1〜3.4)。`{name}` は差し込み口(3.0)。**語を変えない** */
export const TEMPLATES = {
  headingWithText: { kind: "heading", text: "条件 {id}: {readableText}" },
  headingIdOnly: { kind: "heading", text: "条件 {id}" },
  "F-1": {
    kind: "F-1",
    text: "この条件に当てはまり、直後の形勢の区分の変化を確かめられた手の組は {tn} 組({tnGames} 局)でした。そのうち直後に形勢の区分が 1 段以上下がった組は {tc} 組({tcPct})でした。",
  },
  "F-2": { kind: "F-2", text: "当てはまらなかった手の組では、{fn} 組のうち {fc} 組({fcPct})でした。" },
  "F-2b": { kind: "F-2b", text: "直前の形勢の区分を揃えて比べてはいません。" },
  "F-3": { kind: "F-3", text: "同じ手の組でエンジンの読み筋を進めた側では、この条件に当てはまった組は {p} 組で、実戦の側の {a} 組と比べました(比べられた組 {n} 組)。" },
  "F-3-notEvaluable": { kind: "F-3", text: "読み筋の側では、この条件を比べられませんでした。" },
  "F-4": { kind: "F-4", text: "条件を作った棋譜とは別の {testGames} 局では、当てはまる組が {testTn} 組あり、下がった組の割合は当てはまらない組より{direction}向きでした。" },
  "F-5": { kind: "F-5", text: "この {testGames} 局は先手の対局だけで、確認は途中です。" },
  "F-6": { kind: "F-6", text: "この条件に当てはまる手の組は、{tnGames} 局にわたって繰り返し確認されました。" },
  meets: {
    kind: "verdict",
    text: "以上から、この条件は「追加検証する価値のある個人パターン候補」です。現時点では個人の固定的な傾向と断定する段階ではなく、追加の棋譜で同じ傾向が見られるかを確かめる価値があります。",
  },
  insufficient: { kind: "verdict", text: "この条件は、現データでは個人パターンとして採用する根拠が不足しています。" },
  draft: { kind: "verdict", text: "この条件は承認前(draft)のため、判定していません。" },
  pairNotApplied: { kind: "verdict", text: "この条件は手の組に当てない条件のため、判定していません。" },
  none: { kind: "none", text: "この実行で、追加検証する価値のある個人パターン候補は見つかりませんでした。" },
  "N-1": {
    kind: "N-1",
    text: "形勢の区分(優勢・互角・劣勢)は、人間が承認した境(評価値 {aheadCp} 以上を優勢、{behindCp} 以下を劣勢、その間を互角。{approvedOn})による仮の区分で、区分そのものが診断の結論ではありません。直前か直後の区分を決められない組(王手中・終局・評価値として読めない値など)と、直前が劣勢の組(それより下がらない)は、割合の数に入れていません。",
  },
  "N-2": { kind: "N-2", text: "この報告は {games} 局からの候補選びで、同じ対局の中の手の組は互いに独立ではありません。この実行で調べた条件は {conditionsInRun} 本です。" },
} as const satisfies Record<string, { kind: SentenceKind; text: string }>;
export type TemplateKey = keyof typeof TEMPLATES;

/** 差し込み口ごとに取ってよい欄(計画 3.0 と 13.1 の対応表。**これ以外の欄から取らない** ― R-4) */
export const SLOT_FIELDS = {
  id: "condition.id",
  readableText: "definition.readableText",
  tn: "material.tally.truePairs.denominator",
  tc: "material.tally.truePairs.collapsed",
  fn: "material.tally.falsePairs.denominator",
  fc: "material.tally.falsePairs.collapsed",
  tnGames: "material.tally.truePairs.gamesWithDenominator",
  tcPct: "material.tally.truePairs.collapsed,material.tally.truePairs.denominator",
  fcPct: "material.tally.falsePairs.collapsed,material.tally.falsePairs.denominator",
  n: "material.tally.pvSide.n",
  a: "material.tally.pvSide.actualTrue",
  p: "material.tally.pvSide.pvTrue",
  testGames: "test.inputs",
  testTn: "test.tally.truePairs.denominator",
  direction: "test.tally.truePairs.collapsed,test.tally.truePairs.denominator,test.tally.falsePairs.collapsed,test.tally.falsePairs.denominator",
  games: "material.inputs",
  conditionsInRun: "conditionsInRun",
  aheadCp: "STANDING_BOUNDS.aheadCp",
  behindCp: "STANDING_BOUNDS.behindCp",
  approvedOn: "STANDING_BOUNDS_APPROVED_ON",
} as const;
export type SlotName = keyof typeof SLOT_FIELDS;

/** 差し込み口の値の作り方(計画 3.0 の `derivedBy`) */
export const SLOT_DERIVED_BY: Partial<Record<SlotName, "pct" | "sign" | "count" | "signedCp">> = {
  tcPct: "pct",
  fcPct: "pct",
  direction: "sign",
  testGames: "count",
  games: "count",
  aheadCp: "signedCp",
  behindCp: "signedCp",
};

/** 禁止語(計画 4.2。**承認済み**)。位置を限る語(`繰り返し`・`傾向`)は固定文の外に出たら止める */
export const FORBIDDEN_WORDS = [
  // 評価・推奨
  "良い手", "悪手", "悪い", "最善", "正解", "間違", "おすすめ", "べき", "有利", "不利", "損",
  // 性格・固定
  "弱点", "癖", "型", "性格", "苦手", "得意", "下手", "上手", "才能", "傾向",
  // 失敗・因果
  "失敗", "ミス", "見落とし", "原因", "せいで", "敗因", "招い", "崩壊",
  // 断定
  "必ず", "確実", "明らか", "間違いなく", "確定", "証明",
  // 練習(D7 の領分)
  "練習", "課題", "克服", "改善", "直す", "直し",
  // 人に向ける語・頻度(監査 93 の S-2。司令塔が 5 語を決めた。「ため」「から」は誤検出が多いので足さない)
  "くせ", "あなた", "ご自身", "いつも", "がち",
  // 位置を限る語(F-6 と 3.3 の固定文の中だけ)
  "繰り返し",
] as const;

/**
 * 文の種類ごとの終わり(計画 4.3。**位置の検査**)。配列の i 番目は、その文の i 番目の文(「。」で区切った単位)の終わり。
 * F-3 の比べた文は差し込み口の値を含むので、終わりの形を正規表現で持つ。
 */
export const ENDINGS: Record<TemplateKey, readonly (string | RegExp)[] | null> = {
  headingWithText: null,
  headingIdOnly: null,
  "F-1": ["でした。", "でした。"],
  "F-2": ["でした。"],
  "F-2b": ["いません。"],
  "F-3": [/比べました\(比べられた組 [0-9]+ 組\)。$/],
  "F-3-notEvaluable": ["比べられませんでした。"],
  "F-4": ["でした。"],
  "F-5": ["確認は途中です。"],
  "F-6": ["確認されました。"],
  meets: ["です。", "価値があります。"],
  insufficient: ["不足しています。"],
  draft: ["判定していません。"],
  pairNotApplied: ["判定していません。"],
  none: ["見つかりませんでした。"],
  "N-1": ["ありません。", "いません。"],
  "N-2": ["ありません。", "です。"],
};

/** 固定文(計画 5.2 の 1。型とバイト一致で確かめてから取り除く)。N-3 の用語の並びも固定の並びとして扱う */
export const FIXED_TEMPLATES: readonly TemplateKey[] = ["F-6", "meets", "insufficient", "draft", "pairNotApplied", "none", "N-1", "N-2"];

/** 文の本文で許す直書きの数字(計画 4.1。F-1 の「1 段」の 1 だけ) */
export const ALLOWED_LITERAL_DIGITS: Partial<Record<TemplateKey, readonly string[]>> = { "F-1": ["1"] };

/** 数の検査(4.1)の範囲の型。見出しと N-3 は対象外(C-1) */
export const NUMBER_CHECKED_TEMPLATES: readonly TemplateKey[] = ["F-1", "F-2", "F-2b", "F-3", "F-3-notEvaluable", "F-4", "F-5", "F-6", "meets", "insufficient", "draft", "pairNotApplied", "none", "N-1", "N-2"];

/** 用語(計画 3.4 の N-3。CLAUDE.md 2 番)。報告の文に初めて出た語だけを並べる */
export const TERMS = [
  { term: "手の組", text: "手の組 = 自分の手 1 つと相手の手 1 つ" },
  { term: "読み筋", text: "読み筋 = エンジンがその局面から先を読んだ手順" },
  { term: "評価値", text: "評価値 = エンジンが局面につけた点数(棋譜の本人の側から見た値)" },
] as const;
export const TERMS_PREFIX = "用語: ";
export const TERMS_SEPARATOR = " / ";

/** 項目の説明(計画 §6。dev の表だけに出す ― R-7) */
export const ITEM_DESCRIPTIONS = {
  "G-1": "当てはまる組の数と局の数",
  "G-2": "下がった組の割合の比と差",
  "G-3": "読み筋の側との比べ",
  "G-4": "別の棋譜での確かめ",
} as const;

/** 百分率の表示(計画 4.1。整数の四捨五入 `floor((200·c + n) / (2·n))`。分母 0 は「分母 0」) */
export function rateText(collapsed: number, denominator: number): string {
  if (denominator === 0) return "分母 0";
  const pct = Math.floor((200 * collapsed + denominator) / (2 * denominator));
  return `${collapsed}/${denominator}・${pct}%`;
}

/** 境の値の表示(`+300`・`−300`。負の記号は U+2212) */
export function signedCpText(cp: number): string {
  return cp >= 0 ? `+${cp}` : `−${Math.abs(cp)}`;
}
