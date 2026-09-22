// STEP TIME 作業 3(docs/STEP_TIME_PLAN_2026-09-22.md §6.7 の 1)。「じゃあどうしたらいい?」に人を介さずに答える
// 3 段(考えられること・次の 20 局で見分けがつくこと・試せること)の固定文。
// STEP TIME 作業 4「伝わる形」(§6.10 の 1)。読んで分かる順と言葉にするための固定文(読み方・ひとことで・
// 試せることのまとめ・言葉の意味)を足した。判定・数は変えない。
// STEP TIME 作業 4b(§6.12。文だけの直し)。「試せること」3 本(T1・T4・T3)を単独で読める文に、「同じ物差し」→
// 「同じ数え方」。読み方を 5 段に(「4 ページ目」→「最後のページ」)、`phase` の数の文の下に付ける 1 文
// (`PHASE_NOTE`)を新設、言葉の意味に「秒読み」を足して 5 項目に。判定・数は変えない。
//
// 【このファイルがやること】
// - docs/STEP_TIME_PLAN_2026-09-22.md §5.2・§5.3・§5.5 の固定文を、そのまま写しただけの純粋データとして持つ
//   (発見の種類 `FindingKind` ごとの `title`・`considerations`・`distinguish`・`tryable`・`oneLine`・
//   `oneLineVariants`、前回比較の 3 通りの文、評価の揺れの注記、読み方の枠、`phase` の下の 1 文(`PHASE_NOTE`)、
//   試せることのまとめの見出し・末尾の文、言葉の意味の 5 項目)
// - **文の正本は docs §5**。ここは写しであり、試験(findingTexts.test.ts)が両者の文字列一致を確かめる。
//   文を変えるときは docs → コードの順(§5.1)
//
// 【このファイルが絶対にやらないこと】
// - 新しい文言を作ること(局ごとの言い換え・助言・予測)。ここにある文字列は docs §5 の引用のみ
// - 発見の判定(何を出すか)・「ひとことで」の**選び方**(3 通りのどれを選ぶか)。文字列そのものはここに置くが、
//   `numbers` から選ぶロジックは `reportData.ts`(判定は TypeScript・試験できる側、の原則に合わせる)
//
// 【title について(§6.7 の 1 は `title: string` を型に含むが、docs §5.2・§5.3 の一致試験の対象には含めていない)】
// docs §5 の各発見の見出し行(例: 「T1 `timeSpent`: 崩れは、時間をかけた手に多い」)は、内部の整理用の見出しであり、
// §5.1 の「答えの形」(3 段)には含まれない。1 ページ目の見出しは `report-pdf/render_front.py` の `TITLE_JP`
// (作業 2 で実装担当が決めた、事実だけの題)がすでに担っており、この STEP はそれを変える指示を受けていない
// (§6.7 の 2 は 3 段の差し込みだけを指示しており、見出しの変更は書かれていない)。
// そのため `title` は **新しい文言を作らず、`render_front.py` の既存の `TITLE_JP` と同じ文字列をそのまま移した**
// (実装担当の判断。docs との一致試験の対象にはしない ― 試験は §5.2・§5.3 の 3 段・3 通りの文だけを見る)。
//
// 【oneLine・oneLineVariants について(§6.10 の 1。実装担当の判断)】
// `timeSpent`・`aheadLoss`・`none` は 1 通りの固定文なので `oneLine: string`(`oneLineVariants: null`)。
// `timeUpLoss`・`phase` は §5.5 が「3 通り」と書くとおり `oneLine: null`・`oneLineVariants: Record<string, string>`
// に、docs の引用符の中の文字列をそのままキーごとに持たせた(`phase` はプレースホルダ `{序盤|中盤|終盤}`・
// `{X}と{Y}` を含む docs のテンプレートの文字列そのまま ― 埋め込みは `reportData.ts` の役目)。
// **`numbers`(`m`・`n`・`fell`・`early`・`mid`・`late`)からどの文字列を選ぶかは、ここでは決めない**
// (判定は `reportData.ts`。CLAUDE.md 5 番: 判断はコードで、文言はここで、を分ける)。

import type { FindingKind } from "./reportData.js";

/** 発見の種類ごとの固定文(docs §5.2・§5.5 の写し)。`phase` の `considerations`・`distinguish`・`tryable` は
 * 3 つとも null(§5.2 T5: 数の文だけ)。`oneLine`・`oneLineVariants` は §5.5(作業 4)を参照。 */
export interface FindingTextSet {
  /** report-pdf/render_front.py の既存 TITLE_JP と同じ文字列(§6.7 の 1 の型に合わせた欄。docs 一致試験の対象外)。 */
  title: string;
  /** (a)(b)(c) を、各要素にラベルを含めたまま並べたもの(docs の「(a) … (b) … (c) …」の各項目)。 */
  considerations: readonly string[] | null;
  /** 「次の 20 局で見分けがつくこと」の文(docs の 1 行まるごと)。 */
  distinguish: string | null;
  /** 「試せること」の文(docs の 1 行まるごと)。 */
  tryable: string | null;
  /** 「ひとことで」(§5.5)。1 通りの種類だけ(`timeSpent`・`aheadLoss`・`none`)。3 通りの種類は null(`oneLineVariants` を見る)。 */
  oneLine: string | null;
  /** 「ひとことで」の 3 通り(§5.5。`timeUpLoss`・`phase` だけ)。他の種類は null。どのキーを選ぶかは `reportData.ts`。 */
  oneLineVariants: Readonly<Record<string, string>> | null;
}

/** `timeUpLoss` の `oneLineVariants` のキー(§5.5。`numbers.m` と `numbers.n` で選ぶのは reportData.ts 側)。 */
export type TimeUpLossOneLineKey = "mEqualsN" | "partial" | "mZero";

/** `phase` の `oneLineVariants` のキー(§5.5)。`single` は docs のプレースホルダ `{序盤|中盤|終盤}` を含んだまま、
 * `tie` はプレースホルダ `{X}と{Y}` を含んだまま(埋め込みは reportData.ts の役目)。`tieAllPhases` は
 * 「3 つ同数なら」の置き換え文字列(末尾の「で」を含む。docs の引用符のまま)。`zero` は「崩れ 0」。 */
export type PhaseOneLineKey = "single" | "tie" | "tieAllPhases" | "zero";

/** 「考えられること」の頭に付ける 1 文(docs §5.1・§5.2 T1 に書かれた文言。全種類の考えられることに共通)。 */
export const CONSIDERATIONS_LEAD = "どれかは分からない。どれでもないこともある";

/** docs/STEP_TIME_PLAN_2026-09-22.md §5.2 の固定文(発見の種類ごと)。 */
export const FINDING_TEXTS: Record<FindingKind, FindingTextSet> = {
  timeSpent: {
    title: "時間をかけた手と、崩れの割合",
    considerations: [
      "(a) むずかしい局面ほど時間を使い、むずかしい局面ほど崩れる(時間のせいではない)",
      "(b) 時間をかけて選んだ手が、候補の中で低いほうだった",
      "(c) 残り時間を気にして、読み切る前に指した",
    ],
    distinguish: "(a) は 10 秒以上かけた手の局面で第 1 候補と第 2 候補の差が小さいか、(b) は時間をかけた手が上位 5 つの中の何番目か、(c) は残り 60 秒未満の手の崩れの割合",
    tryable: "持ち時間の長い対局(10 分 + 30 秒など)を 5 局ほど混ぜて同じ数え方で数えると、『残り時間を気にして指した』が残るかどうかが分かれます",
    oneLine: "長く考えた手のほうが、短く指した手より、崩れる割合が高い",
    oneLineVariants: null,
  },
  timeUpLoss: {
    title: "持ち時間を使い切って負けた局の、最後の局面の評価",
    considerations: ["(a) 中盤で 1 手ずつが長かった", "(b) 候補が並ぶ局面が続いた", "(c) 序盤で使いすぎた"],
    distinguish: "中盤の 1 手あたりの秒(4 秒の線)、候補の差、序盤の消費",
    tryable: "秒読みのある持ち時間(10 分 + 30 秒など)で 5 局ほど指すと、時間で終わる局が消えるか、それでも盤上で下がるかが分かれます",
    oneLine: null,
    oneLineVariants: {
      mEqualsN: "持ち時間を使い切って負けた局は、どれも盤の上では互角以上だった",
      partial: "持ち時間を使い切って負けた局のうち、盤の上では互角以上だった局があった",
      mZero: "持ち時間を使い切って負けた局は、盤の上でも下がっていた",
    } satisfies Record<TimeUpLossOneLineKey, string>,
  },
  aheadLoss: {
    title: "優勢になった後に負けた対局",
    considerations: [
      "(a) 優勢の局面で候補が並び、どれを選んでも差が縮んだ",
      "(b) 優勢になった後の手に、使える時間が残っていなかった",
      "(c) 優勢の局面で 1 手の差が大きい手(分かれ道)が続いた",
    ],
    distinguish: "優勢の局面での第 1 候補と第 2 候補の差、優勢になった後の残り時間、優勢の局面での分かれ道の数",
    tryable: "持ち時間の長い対局を混ぜると、『使える時間が残っていなかった』かどうかが分かれます。ほかの 2 つは、次の 20 局を同じ数え方で数えると分かれます",
    oneLine: "一度は優勢になった対局のうち、負けに終わった対局があった",
    oneLineVariants: null,
  },
  phase: {
    title: "崩れの時期(序盤・中盤・終盤)",
    considerations: null,
    distinguish: null,
    tryable: null,
    oneLine: null,
    oneLineVariants: {
      single: "崩れは{序盤|中盤|終盤}に多かった",
      tie: "崩れの時期は、{X}と{Y}で同じくらいだった",
      tieAllPhases: "序盤と中盤と終盤で",
      zero: "崩れは無かった",
    } satisfies Record<PhaseOneLineKey, string>,
  },
  none: {
    title: "時間と形勢の動きについて",
    considerations: ["(a) 本当に無い", "(b) 20 局では少なすぎて見えない", "(c) 比較対象が同じ棋力帯・同じ持ち時間でない"],
    distinguish: "40 局を合わせて同じ枠を数える。(c) は比較対象を持ち時間でそろえてから",
    tryable: "同じ持ち時間で次の 20 局を指すと、『20 局では少なすぎて見えない』かどうかが分かれます",
    oneLine: "時間と形勢の動きに、目立った数は出なかった",
    oneLineVariants: null,
  },
};

/** 前回との比較(2 ページ目)に付ける固定文(docs §5.3。3 通り)。 */
export interface PreviousTexts {
  /** 前回も今回も出た。 */
  both: string;
  /** 前回出て今回出ない。 */
  beforeOnly: string;
  /** 前回出ず今回出た。 */
  nowOnly: string;
}

export const PREVIOUS_TEXTS: PreviousTexts = {
  both: "同じ数が 2 回続けて出ています。上の『考えられること』のどれかは、次の 20 局で分かれます",
  beforeOnly: "今回は出ていません。20 局では出たり出なかったりする数です。次の 20 局でもう一度数えます",
  nowOnly: "今回初めて出ています。次の 20 局でも出るかを見ます",
};

/** 評価の揺れの注記(4 ページ目。docs §5.3)。 */
export const EVAL_JITTER_NOTE = "同じ棋譜でもエンジンの評価は回すたびに少し揺れます。『優勢になった局』の数は、境目の局で 1 局ぶん動くことがあります";

// ---- STEP TIME 作業 4「伝わる形」(§6.10。docs §5.5 の写し) ----

/** 読み方(1 ページ目の冒頭の枠。docs §5.5。2026-09-23 作業 4b で 5 段に直し、「4 ページ目」→「最後のページ」に)。 */
export const READING_GUIDE =
  "この冊子の読み方: 太字の 1 行は、棋譜から数えた事実をひとことで言ったものです。その下に数があります。囲みの中は「考えられること」で、どれが当たっているかは分かりません。「次の 20 局で見分けがつくこと」は、次の冊子でどの数を見るかです。「試せること」は、次の 20 局までにできることです。言葉の意味と数え方は最後のページにあります。";

/** 崩れの時期(`phase`)の数の文の下に付ける 1 文(考えられること・試せることの代わり。docs §5.5。2026-09-23 作業 4b で新設)。 */
export const PHASE_NOTE = "この項は、序盤・中盤・終盤で局面の数が違うため、回数だけを並べています。";

/** 次の 20 局までに試せること(まとめ)の見出し(1 ページ目の末尾。docs §5.5)。 */
export const TRYABLE_SUMMARY_HEADING = "次の 20 局までに試せること(まとめ)";

/** 次の 20 局までに試せること(まとめ)の末尾の 1 文(docs §5.5)。 */
export const TRYABLE_SUMMARY_TAIL = "どれもやらなくて大丈夫です。やったものがあれば、次の冊子でその前と後を並べます。";

/** 言葉の意味(4 ページ目の頭。docs §5.5)の 1 項目。 */
export interface GlossaryItem {
  term: string;
  text: string;
}

/** 言葉の意味(最後のページの頭。「数え方」の前。docs §5.5)。5 項目、docs の順のまま(2026-09-23 作業 4b で「秒読み」を追加)。 */
export const GLOSSARY: readonly GlossaryItem[] = [
  { term: "崩れ", text: "本人の 1 手で、形勢の段(優勢・互角・劣勢)が 1 段以上下がったこと。+300 以上を優勢、−300 以下を劣勢、その間を互角としています" },
  { term: "第 1 候補", text: "エンジンが最も良いとした手。第 2 候補はその次です。2 つの差が小さいほど、『候補が並ぶ』局面です" },
  { term: "分かれ道", text: "本人が指した手が、エンジンの候補 5 つに入らなかった、または第 1 候補より 600 以上低かった局面" },
  { term: "評価", text: "エンジンが計算した形勢の数。プラスは本人が良い側です" },
  { term: "秒読み", text: "持ち時間を使い切った後も、1 手ごとに決まった秒(30 秒など)で指し続けられる決まり。『10 分 + 30 秒』は持ち時間 10 分、秒読み 30 秒の意味です" },
];

/**
 * `finding_texts.json` の形(§6.7 の 1: 「python にも文を写す必要があるので、`reportData.ts` の CLI が
 * `finding_texts.json` を `patient_report_data.json` の隣に書く(TS の定数から生成。python は手写ししない)」)。
 * このオブジェクトをそのまま JSON にする(`reportData.ts` の役目。ここは形を作るだけ)。
 * STEP TIME 作業 4(§6.10 の 1): `readingGuide`・`tryableSummaryHeading`・`tryableSummaryTail`・`glossary` を足した
 * (`findings[].oneLine` は個々の発見ごとに解決済みの値を `reportData.ts` の `Finding.oneLine` が持つので、
 * ここ(種類に依らない固定文の置き場)には含めない)。
 * STEP TIME 作業 4b(§6.12): `phaseNote`(`phase` の数の文の下に付ける 1 文)を足した。
 */
export interface FindingTextsFile {
  considerationsLead: string;
  findings: Record<FindingKind, FindingTextSet>;
  previous: PreviousTexts;
  evalJitterNote: string;
  readingGuide: string;
  tryableSummaryHeading: string;
  tryableSummaryTail: string;
  glossary: readonly GlossaryItem[];
  phaseNote: string;
}

export function buildFindingTextsFile(): FindingTextsFile {
  return {
    considerationsLead: CONSIDERATIONS_LEAD,
    findings: FINDING_TEXTS,
    previous: PREVIOUS_TEXTS,
    evalJitterNote: EVAL_JITTER_NOTE,
    readingGuide: READING_GUIDE,
    tryableSummaryHeading: TRYABLE_SUMMARY_HEADING,
    tryableSummaryTail: TRYABLE_SUMMARY_TAIL,
    glossary: GLOSSARY,
    phaseNote: PHASE_NOTE,
  };
}

/**
 * 禁止語(docs §5.1: BANNED の 18 語 + 「すべき」「した方がよい」)。render_front.py の BANNED と揃える
 * (python 側は手写ししたまま。ここは TS 側の固定文を見張る試験専用)。
 */
export const FORBIDDEN_FINDING_TEXT_WORDS = [
  "悪手",
  "弱点",
  "癖",
  "型",
  "傾向",
  "原因",
  "ミス",
  "見落とし",
  "改善",
  "練習",
  "必ず",
  "明らか",
  "あなた",
  "ご自身",
  "いつも",
  "がち",
  "クセ",
  "パターン",
  "すべき",
  "した方がよい",
] as const;
