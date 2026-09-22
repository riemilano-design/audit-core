// STEP TIME 作業 3(docs/STEP_TIME_PLAN_2026-09-22.md §6.7 の 1)。
// `lib/findingTexts.ts` の固定文が docs §5.2・§5.3 の文字列と一致することを確かめる(**文の正本は docs**。
// 合わなければこの試験を赤のまま報告する ― docs は書き換えない)。
//
// 【切り方(このファイルの中だけの約束。docs の書式に依存する)】
// - 発見ごとの節は、docs の見出し行(例:「**T1 `timeSpent`: 崩れは、時間をかけた手に多い**」)から始まる
// - 「考えられること」の行は `- 考えられること(...): (a) … (b) … (c) …` または `- 考えられること: (a) … (b) … (c) …`。
//   `(a)`/`(b)`/`(c)` の直前で分割する(`\s(?=\([abc]\))`。本文中の他の丸括弧(例: 「(時間のせいではない)」)は
//   `(a)`〜`(c)` の 1 文字パターンに一致しないので割れない)
// - 「次の 20 局で見分けがつくこと」「試せること」の行は 1 行まるごと(配列にしない)
// - §5.3 の 3 通り・評価の揺れの注記は「見出し: 「文」」の `「」` の中身をそのまま取る

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { CONSIDERATIONS_LEAD, EVAL_JITTER_NOTE, FINDING_TEXTS, FORBIDDEN_FINDING_TEXT_WORDS, PREVIOUS_TEXTS } from "./findingTexts.js";
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

  it("phase(T5): 3 つとも null(§5.2 T5「考えられること・試せることは付けない」)", () => {
    expect(FINDING_TEXTS.phase).toStrictEqual({ title: FINDING_TEXTS.phase.title, considerations: null, distinguish: null, tryable: null });
  });

  it("docs の T1 のかっこ書きが CONSIDERATIONS_LEAD と一致する(§5.1 の頭の 1 文)", () => {
    const section = sectionAfter(HEADERS.timeSpent);
    expect(section).toContain(`考えられること(${CONSIDERATIONS_LEAD}): `);
  });
});

describe("PREVIOUS_TEXTS・EVAL_JITTER_NOTE は docs §5.3 と文字列として一致する", () => {
  function quotedTextAfter(label: string): string {
    const lineMatch = DOCS_TEXT.match(new RegExp(`^- ${label}: 「(.*)」$`, "m"));
    if (!lineMatch) throw new Error(`docs に見つからない行: ${label}`);
    return lineMatch[1]!;
  }

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

describe("禁止語 0(§5.1: BANNED 18 語 + 「すべき」「した方がよい」)", () => {
  const allTexts: string[] = [
    CONSIDERATIONS_LEAD,
    ...Object.values(FINDING_TEXTS).flatMap((set) => [set.title, ...(set.considerations ?? []), set.distinguish ?? "", set.tryable ?? ""]),
    PREVIOUS_TEXTS.both,
    PREVIOUS_TEXTS.beforeOnly,
    PREVIOUS_TEXTS.nowOnly,
    EVAL_JITTER_NOTE,
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
