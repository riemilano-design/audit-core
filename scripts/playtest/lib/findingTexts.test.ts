// STEP TIME 作業 3(docs/STEP_TIME_PLAN_2026-09-22.md §6.7 の 1)。
// `lib/findingTexts.ts` の固定文が docs §5.2・§5.3 の文字列と一致することを確かめる(**文の正本は docs**。
// 合わなければこの試験を赤のまま報告する ― docs は書き換えない)。
// STEP TIME 作業 4(§6.10)。§5.5(読み方・ひとことで・試せることのまとめ・言葉の意味)の一致試験を足した。
// STEP TIME 作業 4b(§6.12)。「試せること」3 本の直し(既存の一致試験がそのまま検知)・読み方の 5 段への直し
// (既存の一致試験がそのまま検知)・`PHASE_NOTE`(新設)の一致試験・`GLOSSARY` 5 項目(秒読み追加)の一致試験を足した。
//
// 【切り方(このファイルの中だけの約束。docs の書式に依存する)】
// - 発見ごとの節は、docs の見出し行(例:「**T1 `timeSpent`: 崩れは、時間をかけた手に多い**」)から始まる
// - 「考えられること」の行は `- 考えられること(...): (a) … (b) … (c) …` または `- 考えられること: (a) … (b) … (c) …`。
//   `(a)`/`(b)`/`(c)` の直前で分割する(`\s(?=\([abc]\))`。本文中の他の丸括弧(例: 「(時間のせいではない)」)は
//   `(a)`〜`(c)` の 1 文字パターンに一致しないので割れない)
// - 「次の 20 局で見分けがつくこと」「試せること」の行は 1 行まるごと(配列にしない)
// - §5.3 の 3 通り・評価の揺れの注記は「見出し: 「文」」の `「」` の中身をそのまま取る
// - §5.5「ひとことで」の各行は、行の中の「」で囲まれた箇所をすべて `matchAll(/「(.*?)」/g)` で順に取り出す
//   (`timeSpent`・`aheadLoss`・`none` は 1 個、`timeUpLoss`・`phase` は複数。`phase` のプレースホルダ
//   `{序盤|中盤|終盤}`・`{X}と{Y}` はそのまま文字列に含まれる ― 埋め込みは reportData.ts 側の責務で、
//   ここでは「docs の引用符の中の文字列そのもの」が一致することだけを見る)
// - §5.5「読み方」「試せることのまとめ」「崩れの時期に付ける 1 文」は、それぞれの見出し行の `「(.*)」` を取る
//   (見出しの後ろにコロン + quote が 1 個の場合は greedy)。「試せることのまとめ」は 1 行に「見出し「…」」
//   「末尾の 1 文「…」」の 2 か所あるため、ラベルの直後から次の `」` までを非 greedy で取る
// - §5.5「言葉の意味」の 5 項目(秒読みを含む)は `- {用語}: 「(.*)」` の形(既存の quotedTextAfter と同じ切り方。
//   「秒読み」の行は `秒読み(2026-09-23 作業 4b で追加)` がラベルなので、その丸括弧を含めて渡す)

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  CONSIDERATIONS_LEAD,
  EVAL_JITTER_NOTE,
  FINDING_TEXTS,
  FORBIDDEN_FINDING_TEXT_WORDS,
  GLOSSARY,
  PHASE_NOTE,
  PREVIOUS_TEXTS,
  READING_GUIDE,
  TRYABLE_SUMMARY_HEADING,
  TRYABLE_SUMMARY_TAIL,
} from "./findingTexts.js";
import type { FindingKind } from "./reportData.js";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const DOCS_PATH = path.join(REPO_ROOT, "docs", "STEP_TIME_PLAN_2026-09-22.md");
const DOCS_TEXT = readFileSync(DOCS_PATH, "utf-8");

/** 見出し行から、次の見出し(`\n\n**T` または `\n\n### `)の手前までを切り出す。 */
function sectionAfter(header: string): string {
  const idx = DOCS_TEXT.indexOf(header);
  if (idx === -1) throw new Error(`docs にこの見出しが無い: ${header}`);
  const rest = DOCS_TEXT.slice(idx + header.length);
  const nextT = rest.indexOf("\n\n**T");
  const nextH3 = rest.indexOf("\n\n### ");
  const candidates = [nextT, nextH3].filter((n) => n !== -1);
  const end = candidates.length === 0 ? rest.length : Math.min(...candidates);
  return rest.slice(0, end);
}

const CONSIDERATIONS_LINE = /^- 考えられること(?:\([^)]*\))?: (.*)$/m;
const DISTINGUISH_LINE = /^- 次の 20 局で見分けがつくこと: (.*)$/m;
const TRYABLE_LINE = /^- 試せること: (.*)$/m;

/** 「(a) … (b) … (c) …」を、各項目にラベルを含めたまま 3 つに割る。 */
function splitConsiderations(raw: string): string[] {
  return raw.split(/\s(?=\([abc]\))/);
}

interface DocsFindingSection {
  considerations: string[] | null;
  distinguish: string | null;
  tryable: string | null;
}

/** docs §5.2 のうち、指定した見出しの節から 3 段を取り出す(見つからない行は null)。 */
function docsFindingTextsOf(header: string): DocsFindingSection {
  const section = sectionAfter(header);
  const considerationsMatch = section.match(CONSIDERATIONS_LINE);
  const distinguishMatch = section.match(DISTINGUISH_LINE);
  const tryableMatch = section.match(TRYABLE_LINE);
  return {
    considerations: considerationsMatch ? splitConsiderations(considerationsMatch[1]!) : null,
    distinguish: distinguishMatch ? distinguishMatch[1]! : null,
    tryable: tryableMatch ? tryableMatch[1]! : null,
  };
}

/** `- {label}: 「(.*)」` の形の行から、引用符の中身を取り出す(§5.3・§5.5「言葉の意味」で使う。greedy なので
 * ネストした『』も含めて行末までを取る)。 */
function quotedTextAfter(label: string): string {
  const lineMatch = DOCS_TEXT.match(new RegExp(`^- ${label}: 「(.*)」$`, "m"));
  if (!lineMatch) throw new Error(`docs に見つからない行: ${label}`);
  return lineMatch[1]!;
}

function escapeRegExp(raw: string): string {
  return raw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** prefix で始まる 1 行を探し、その行の中の「」で囲まれた箇所を出現順にすべて取り出す(§5.5「ひとことで」)。 */
function quotedSegmentsOfLineStartingWith(prefix: string): string[] {
  const lineMatch = DOCS_TEXT.match(new RegExp(`^${escapeRegExp(prefix)}.*$`, "m"));
  if (!lineMatch) throw new Error(`docs に見つからない行(先頭一致): ${prefix}`);
  return [...lineMatch[0].matchAll(/「(.*?)」/g)].map((m) => m[1]!);
}

const HEADERS: Record<Exclude<FindingKind, "phase">, string> = {
  timeSpent: "**T1 `timeSpent`: 崩れは、時間をかけた手に多い**",
  timeUpLoss: "**T2 `timeUpLoss`: 使い切って負けた局は、盤上は互角以上だった**",
  aheadLoss: "**T4 `aheadLoss`: 優勢になった後に負けた対局があった**",
  none: "**T3 `none`: 探したが、上に書ける数は無かった**",
};

describe("FINDING_TEXTS は docs §5.2 と文字列として一致する", () => {
  for (const kind of Object.keys(HEADERS) as Array<Exclude<FindingKind, "phase">>) {
    it(`${kind}: 考えられること・次の 20 局で見分けがつくこと・試せること`, () => {
      const docsSection = docsFindingTextsOf(HEADERS[kind]);
      const code = FINDING_TEXTS[kind];
      expect(code.considerations).toStrictEqual(docsSection.considerations);
      expect(code.distinguish).toBe(docsSection.distinguish);
      expect(code.tryable).toBe(docsSection.tryable);
    });
  }

  it("phase(T5): considerations・distinguish・tryable は 3 つとも null(§5.2 T5「考えられること・試せることは付けない」)。oneLine は null で oneLineVariants を使う(§5.5・作業 4)", () => {
    expect(FINDING_TEXTS.phase.considerations).toBeNull();
    expect(FINDING_TEXTS.phase.distinguish).toBeNull();
    expect(FINDING_TEXTS.phase.tryable).toBeNull();
    expect(FINDING_TEXTS.phase.oneLine).toBeNull();
    expect(FINDING_TEXTS.phase.oneLineVariants).not.toBeNull();
  });

  it("docs の T1 のかっこ書きが CONSIDERATIONS_LEAD と一致する(§5.1 の頭の 1 文)", () => {
    const section = sectionAfter(HEADERS.timeSpent);
    expect(section).toContain(`考えられること(${CONSIDERATIONS_LEAD}): `);
  });
});

describe("PREVIOUS_TEXTS・EVAL_JITTER_NOTE は docs §5.3 と文字列として一致する", () => {
  it("前回も今回も出た", () => {
    expect(PREVIOUS_TEXTS.both).toBe(quotedTextAfter("前回も今回も出た"));
  });

  it("前回出て今回出ない", () => {
    expect(PREVIOUS_TEXTS.beforeOnly).toBe(quotedTextAfter("前回出て今回出ない"));
  });

  it("前回出ず今回出た", () => {
    expect(PREVIOUS_TEXTS.nowOnly).toBe(quotedTextAfter("前回出ず今回出た"));
  });

  it("評価の揺れの注記(4 ページ目)", () => {
    expect(EVAL_JITTER_NOTE).toBe(quotedTextAfter("評価の揺れの注記\\(4 ページ目\\)"));
  });
});

// STEP TIME 作業 4(§6.10 の 1・§5.5)。「ひとことで」の固定文が docs と文字列として一致することを確かめる。
// `numbers` からどの文字列を選ぶか(境界)は lib/reportData.test.ts 側で確かめる(ここは文字列そのものだけ)。
describe("「ひとことで」(§5.5)は docs と文字列として一致する(STEP TIME 作業 4)", () => {
  it("timeSpent(1 通り)", () => {
    const [expected] = quotedSegmentsOfLineStartingWith("- `timeSpent`: ");
    expect(expected).toBeDefined();
    expect(FINDING_TEXTS.timeSpent.oneLine).toBe(expected);
  });

  it("aheadLoss(1 通り)", () => {
    const [expected] = quotedSegmentsOfLineStartingWith("- `aheadLoss`: ");
    expect(expected).toBeDefined();
    expect(FINDING_TEXTS.aheadLoss.oneLine).toBe(expected);
  });

  it("none(1 通り)", () => {
    const [expected] = quotedSegmentsOfLineStartingWith("- `none`: ");
    expect(expected).toBeDefined();
    expect(FINDING_TEXTS.none.oneLine).toBe(expected);
  });

  it("timeUpLoss: m = n / 0 < m < n / m = 0 の 3 通り(docs の出現順 = mEqualsN・partial・mZero)", () => {
    const [mEqualsN, partial, mZero] = quotedSegmentsOfLineStartingWith("- `timeUpLoss`(3 通り");
    expect(FINDING_TEXTS.timeUpLoss.oneLineVariants).toStrictEqual({ mEqualsN, partial, mZero });
  });

  it("phase: 最大 1 つ / 最大 2 つ以上 / 3 つ同数の置き換え / 崩れ 0 の 4 か所(docs の出現順 = single・tie・tieAllPhases・zero)", () => {
    const [single, tie, tieAllPhases, zero] = quotedSegmentsOfLineStartingWith("- `phase`(3 通り");
    expect(FINDING_TEXTS.phase.oneLineVariants).toStrictEqual({ single, tie, tieAllPhases, zero });
  });
});

// STEP TIME 作業 4(§6.10 の 1・§5.5)。読み方の枠・試せることのまとめ(見出し・末尾の文)・言葉の意味(5 項目)。
// STEP TIME 作業 4b(§6.12)で「読み方」の行の末尾に注記(丸かっこ)が付いたため、READING_GUIDE の抽出は
// 「」の直後に `(` が続く箇所(注記の開始)までを greedy に取る(本文中の「」はすべて対になっているので、
// 最後に現れる「」( の直前までが本文、その後ろが注記)。
describe("読み方・試せることのまとめ・言葉の意味(§5.5)は docs と文字列として一致する(STEP TIME 作業 4)", () => {
  it("READING_GUIDE(1 ページ目冒頭の枠)", () => {
    const lineMatch = DOCS_TEXT.match(/^\*\*読み方\(1 ページ目の冒頭の枠\)\*\*: 「(.*)」\(/m);
    if (!lineMatch) throw new Error("docs に読み方の行が無い");
    expect(READING_GUIDE).toBe(lineMatch[1]);
  });

  it("TRYABLE_SUMMARY_HEADING・TRYABLE_SUMMARY_TAIL(1 ページ目末尾のまとめ)", () => {
    const lineMatch = DOCS_TEXT.match(/^\*\*次の 20 局までに試せること\(まとめ。1 ページ目の末尾\)\*\*:.*$/m);
    if (!lineMatch) throw new Error("docs に試せることのまとめの行が無い");
    const line = lineMatch[0];
    const headingMatch = line.match(/見出し「(.*?)」/);
    const tailMatch = line.match(/末尾の 1 文「(.*)」$/);
    if (!headingMatch || !tailMatch) throw new Error("docs の試せることのまとめの行から見出し・末尾の文を取れない");
    expect(TRYABLE_SUMMARY_HEADING).toBe(headingMatch[1]);
    expect(TRYABLE_SUMMARY_TAIL).toBe(tailMatch[1]);
  });

  it("GLOSSARY(言葉の意味、5 項目。docs の順のまま。2026-09-23 作業 4b で「秒読み」を追加)", () => {
    expect(GLOSSARY).toStrictEqual([
      { term: "崩れ", text: quotedTextAfter("崩れ") },
      { term: "第 1 候補", text: quotedTextAfter("第 1 候補") },
      { term: "分かれ道", text: quotedTextAfter("分かれ道") },
      { term: "評価", text: quotedTextAfter("評価") },
      { term: "秒読み", text: quotedTextAfter("秒読み\\(2026-09-23 作業 4b で追加\\)") },
    ]);
  });

  it("PHASE_NOTE(崩れの時期に付ける 1 文。`phase` の数の文の下。2026-09-23 作業 4b で新設)", () => {
    const lineMatch = DOCS_TEXT.match(/^\*\*崩れの時期に付ける 1 文\(`phase` の数の文の下。考えられること・試せることの代わり\)\*\*: 「(.*)」$/m);
    if (!lineMatch) throw new Error("docs に崩れの時期に付ける 1 文の行が無い");
    expect(PHASE_NOTE).toBe(lineMatch[1]);
  });
});

describe("禁止語 0(§5.1: BANNED 18 語 + 「すべき」「した方がよい」)", () => {
  const allTexts: string[] = [
    CONSIDERATIONS_LEAD,
    ...Object.values(FINDING_TEXTS).flatMap((set) => [
      set.title,
      ...(set.considerations ?? []),
      set.distinguish ?? "",
      set.tryable ?? "",
      set.oneLine ?? "",
      ...(set.oneLineVariants ? Object.values(set.oneLineVariants) : []),
    ]),
    PREVIOUS_TEXTS.both,
    PREVIOUS_TEXTS.beforeOnly,
    PREVIOUS_TEXTS.nowOnly,
    EVAL_JITTER_NOTE,
    READING_GUIDE,
    TRYABLE_SUMMARY_HEADING,
    TRYABLE_SUMMARY_TAIL,
    PHASE_NOTE,
    ...GLOSSARY.flatMap((item) => [item.term, item.text]),
  ];

  it("固定文のどれにも禁止語が入っていない", () => {
    for (const text of allTexts) {
      for (const word of FORBIDDEN_FINDING_TEXT_WORDS) {
        expect(text.includes(word), `「${word}」が含まれている: ${text}`).toBe(false);
      }
    }
  });

  it("FORBIDDEN_FINDING_TEXT_WORDS は §5.1 の一覧のまま(20 語)", () => {
    expect(FORBIDDEN_FINDING_TEXT_WORDS).toHaveLength(20);
    expect(FORBIDDEN_FINDING_TEXT_WORDS).toContain("すべき");
    expect(FORBIDDEN_FINDING_TEXT_WORDS).toContain("した方がよい");
  });
});
