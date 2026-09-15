// STEP D6(docs/STEP_D6_PLAN_2026-09-16.md §7)。Gate の行を文にする lib を見張る。**エンジン・LLM は使わない。**
// 行は試験だけの架空の Gate の行(`test_only_*`)。欄の名前は D4 の実装に合わせた(計画 13.1)。固定例の数は互いに違う値にする(R-4)。

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { validate, type JsonSchema } from "./eventSchema.js";
import {
  buildDiagnosisReport,
  chooseRows,
  outputProblems,
  recomputeItemResults,
  ReportInputError,
  ReportOutputError,
  slotText,
  splitSentences,
  type GateItemId,
  type GateItemResult,
  type NumberedGateLine,
  type ReportConditionLine,
  type ReportContext,
  type ReportDefinition,
  type ReportLine,
  type ReportOptions,
  type ReportSentence,
} from "./diagnosisReport.js";
import { STANDING_BOUNDS } from "./failureEvent.js";
import { GATE_TEXT, GATE_VALUES, gateVerdictOf, type CollapseTally, type GateTally } from "./gate.js";
import { validateDiagnosisGateLine } from "./gateOutput.js";
import { rateText, SLOT_FIELDS, STANDING_BOUNDS_APPROVED_ON, TEMPLATES, TERMS, type TemplateKey } from "./reportTemplates.js";

const SHA_A = "a".repeat(64);
const SHA_B = "b".repeat(64);
const SHA_D = "d".repeat(64);
const SHA_OLD = "e".repeat(64);
const LABEL_A = "試験だけの定義(仮)";
const TEXT_A = "試験だけの条件の文";

const DEF_A: ReportDefinition = { id: "test_only_a", label: LABEL_A, status: "approved", readableText: TEXT_A, definitionSha256: SHA_A };
const DEF_B: ReportDefinition = { id: "test_only_b", label: "試験だけの二つめ(仮)", status: "approved", readableText: "二つめの条件を見る文", definitionSha256: SHA_B };
const DEF_D: ReportDefinition = { id: "test_only_d", label: "試験だけの下書き(仮)", status: "draft", definitionSha256: SHA_D };

const CONTEXT: ReportContext = {
  definitions: [DEF_A, DEF_B, DEF_D],
  standingBounds: STANDING_BOUNDS,
  input: { path: "scripts/playtest/records/gate/test_only.jsonl", sha256: "c".repeat(64) },
  provenance: { gitHead: "head", dirty: false },
};

/** 崩れの集計(D4 の CollapseTally の全部の欄。T-26 で契約のスキーマを通す)。`aheadDenominator` は直前が優勢の組の数(崩れは先に優勢の組に数える) */
function collapseTally(denominator: number, collapsed: number, games: number, aheadDenominator: number): CollapseTally {
  const aheadCollapsed = Math.min(collapsed, aheadDenominator);
  const byGame = Array.from({ length: games }, (_, index) => ({ kifuId: `g${index}`, pairs: Math.floor(denominator / games) + (index < denominator % games ? 1 : 0) })).filter((entry) => entry.pairs > 0);
  return {
    pairs: denominator + 8,
    collapsed,
    denominator,
    excluded: { beforeUndetermined: 2, afterUndetermined: 3, cannotFall: 3 },
    transitions: { aheadToLevel: aheadCollapsed, levelToBehind: collapsed - aheadCollapsed, aheadToBehind: 0 },
    byBefore: { ahead: { collapsed: aheadCollapsed, denominator: aheadDenominator }, level: { collapsed: collapsed - aheadCollapsed, denominator: denominator - aheadDenominator } },
    gamesWithDenominator: games,
    denominatorByGame: byGame,
    gamesWithPairs: games,
    gamesWithCollapse: Math.min(games, collapsed),
    within5: { dropped: collapsed, denominator, excluded: { beforeUndetermined: 1, cannotFall: 1, windowShort: 0 }, distinctDrops: collapsed, distinctDropsByGame: [] },
  };
}

/** D4 の GateTally の形にそろえる(判定の数・全ての組・表示用の率) */
function gateTally(games: number, truePairs: CollapseTally, falsePairs: CollapseTally, pvSide: GateTally["pvSide"]): GateTally {
  const all = collapseTally(truePairs.denominator + falsePairs.denominator, truePairs.collapsed + falsePairs.collapsed, games, truePairs.byBefore.ahead.denominator + falsePairs.byBefore.ahead.denominator);
  return {
    games,
    judgements: { match: truePairs.pairs, noMatch: falsePairs.pairs, undecidable: 0, undecidableReasons: [], movesMissing: 0 },
    all,
    truePairs,
    falsePairs,
    rates: { truePercent: null, falsePercent: null, ratio: null, diffPoints: null },
    pvSide,
  };
}

type Sign = "pos" | "neg" | "zero" | "fn0";

/** 材料の側。`pos` は tn 23・真の総数 31・局 7・tc 11・fn 341・fc 29・n 19・a 13・p 5(T-1 の値) */
function materialTally(options: { sign?: "pos" | "neg"; f2b?: boolean; g3?: boolean; tn?: number; tc?: number; tnGames?: number; ahead?: number; games?: number } = {}): GateTally {
  const negative = options.sign === "neg";
  return gateTally(
    options.games ?? 20,
    collapseTally(options.tn ?? 23, options.tc ?? (negative ? 1 : 11), options.tnGames ?? 7, options.ahead ?? (options.f2b ? 12 : Math.min(8, options.tn ?? 23))),
    collapseTally(341, negative ? 100 : 29, 20, 120),
    options.g3 === false ? { state: "applicable", n: 0, actualTrue: 0, pvTrue: 0 } : { state: "applicable", n: 19, actualTrue: 13, pvTrue: 5 },
  );
}

/** 試す側。tn 4・fn 90。符号は tc·fn − fc·tn: pos 112 / neg −70 / zero 0 / fn0 は偽の分母 0 */
function testTally(sign: Sign, games: number): GateTally {
  const falseCollapsed = { pos: 17, neg: 40, zero: 45, fn0: 0 }[sign];
  return gateTally(games, collapseTally(4, sign === "neg" ? 1 : 2, 3, 2), sign === "fn0" ? collapseTally(0, 0, 0, 0) : collapseTally(90, falseCollapsed, 6, 30), { state: "applicable", n: 7, actualTrue: 3, pvTrue: 1 });
}

const inputsOf = (count: number, prefix: string) =>
  Array.from({ length: count }, (_, index) => ({ path: `scripts/playtest/records/test_only/${prefix}${index}.jsonl`, sha256: (index + 1).toString(16).padStart(64, "0") }));

const ALL_MET: Record<GateItemId, GateItemResult> = { "G-1": "met", "G-2": "met", "G-3": "met", "G-4": "met" };

interface LineOptions {
  id?: string;
  sha?: string;
  label?: string;
  status?: "draft" | "approved";
  kind?: "judged" | "draft" | "pairNotApplied";
  material?: GateTally;
  test?: GateTally;
  set?: string;
  provisional?: boolean;
  items?: Record<GateItemId, GateItemResult>;
  conditionsInRun?: number;
}

/** D4 の形の Gate の行(JSON.parse した値と同じ形)。項目は D4 の gateVerdictOf から作り、`items` を渡したときだけ結果を差し替える(食い違いの固定例) */
function gateLine(options: LineOptions = {}): Record<string, unknown> {
  const set = options.set ?? "sente6";
  const material = options.material ?? materialTally();
  const test = options.test ?? testTally("pos", set.includes("+gote") ? 10 : 6);
  const kind = options.kind ?? "judged";
  const computed = gateVerdictOf(material, test).items;
  const gateItems = computed.map((item) => (options.items === undefined || options.items[item.item] === item.result ? item : { ...item, result: options.items[item.item], reasons: ["test_only"] }));
  const verdict = gateItems.every((item) => item.result === "met") ? "meets" : "insufficient";
  const base = {
    contract: "diagnosis-gate",
    schemaVersion: "0.1",
    person: "p2",
    testPerson: "p1",
    condition: { id: options.id ?? "test_only_a", label: options.label ?? LABEL_A, status: options.status ?? (kind === "draft" ? "draft" : "approved"), definitionSha256: options.sha ?? SHA_A },
    source: { referenceNodes: 4000000, evaluation: "light" },
  };
  const tail = { gateValues: { ...GATE_VALUES }, conditionsInRun: options.conditionsInRun ?? 3, provenance: { gitHead: "g", dirty: false } };
  const testSet = { set, provisional: options.provisional ?? !set.includes("+gote"), inputs: inputsOf(test.games, "t") };
  if (kind === "pairNotApplied") return { ...base, material: { inputs: inputsOf(material.games, "m") }, test: testSet, gate: { notJudged: "pairNotApplied" }, ...tail };
  const gate =
    kind === "draft"
      ? { notJudged: "draft" }
      : {
          items: gateItems,
          verdict,
          text: verdict === "meets" ? GATE_TEXT.meets : GATE_TEXT.insufficient,
        };
  return { ...base, material: { inputs: inputsOf(material.games, "m"), tally: material }, test: { ...testSet, tally: test }, gate, ...tail };
}

const entriesOf = (lines: readonly unknown[]) => lines.map((value, index) => ({ line: index + 1, value }));
const report = (lines: readonly unknown[], options: ReportOptions, context: ReportContext = CONTEXT) => buildDiagnosisReport(entriesOf(lines), context, options);
const conditionLines = (lines: readonly ReportLine[]) => lines.filter((line): line is ReportConditionLine => line.lineKind === "condition");
const texts = (sentences: readonly ReportSentence[]) => sentences.map((sentence) => sentence.text);
const summaryOf = (lines: readonly ReportLine[]) => lines.find((line) => line.lineKind === "summary")!;
const inputProblems = (run: () => unknown): string[] => {
  try {
    run();
  } catch (error) {
    if (error instanceof ReportInputError || error instanceof ReportOutputError) return [...error.problems];
    throw error;
  }
  return [];
};

const MEETS_TEXT = TEMPLATES.meets.text;
const N1_TEXT = "形勢の区分(優勢・互角・劣勢)は、人間が承認した境(評価値 +300 以上を優勢、−300 以下を劣勢、その間を互角。2026-09-15)による仮の区分で、区分そのものが診断の結論ではありません。直前か直後の区分を決められない組(王手中・終局・評価値として読めない値など)と、直前が劣勢の組(それより下がらない)は、割合の数に入れていません。";
const N2_TEXT = "この報告は 20 局からの候補選びで、同じ対局の中の手の組は互いに独立ではありません。この実行で調べた条件は 3 本です。";
const N3_ALL = `用語: ${TERMS.map(({ text }) => text).join(" / ")}`;

describe("STEP D6: 文の組み立て(計画 §3・§7 の T-1〜T-8・T-11)", () => {
  it("T-1: meets・sente6・readableText あり → person に見出し・F-1〜F-6(F-2b なし)・meets の固定文・N-1〜N-3。数はすべて入力の欄の値で、label は出ない", () => {
    const { lines } = report([gateLine()], { audience: "person" });
    const [condition] = conditionLines(lines);
    expect(texts(condition!.sentences)).toStrictEqual([
      `条件 test_only_a: ${TEXT_A}`,
      "この条件に当てはまり、直後の形勢の区分の変化を確かめられた手の組は 23 組(7 局)でした。そのうち直後に形勢の区分が 1 段以上下がった組は 11 組(11/23・48%)でした。",
      "当てはまらなかった手の組では、341 組のうち 29 組(29/341・9%)でした。",
      "同じ手の組でエンジンの読み筋を進めた側では、この条件に当てはまった組は 5 組で、実戦の側の 13 組と比べました(比べられた組 19 組)。",
      "条件を作った棋譜とは別の 6 局では、当てはまる組が 4 組あり、下がった組の割合は当てはまらない組より高い向きでした。",
      "この 6 局は先手の対局だけで、確認は途中です。",
      "この条件に当てはまる手の組は、7 局にわたって繰り返し確認されました。",
      MEETS_TEXT,
    ]);
    expect(texts(summaryOf(lines).sentences)).toStrictEqual([N1_TEXT, N2_TEXT, N3_ALL]);
    expect(JSON.stringify(lines)).not.toContain("試験だけの定義");
    expect(condition!.dev).toBeUndefined();
  });

  it("T-2: insufficient(G-1 notMet・G-3 notEvaluable)→ person は条件式の行なし / dev は根拠不足の固定文、項目は満たさなかった・測れなかったに分かれ、F-6 が無い", () => {
    const material = materialTally({ tn: 9, tc: 4, g3: false, ahead: 3 });
    const items: Record<GateItemId, GateItemResult> = { "G-1": "notMet", "G-2": "met", "G-3": "notEvaluable", "G-4": "met" };
    expect(conditionLines(report([gateLine({ material, items })], { audience: "person" }).lines)).toStrictEqual([]);
    const dev = report([gateLine({ material, items })], { audience: "dev" });
    const [condition] = conditionLines(dev.lines);
    expect(condition!.sentences.map((sentence) => sentence.template)).toStrictEqual(["headingWithText", "F-1", "F-2", "F-3-notEvaluable", "F-4", "F-5", "insufficient"]);
    expect(condition!.dev!.items.map((item) => [item.item, item.result])).toStrictEqual([["G-1", "notMet"], ["G-2", "met"], ["G-3", "notEvaluable"], ["G-4", "met"]]);
    expect(condition!.dev!.omittedForPerson).toBe("insufficient");
    expect(dev.markdown.join("\n")).toContain("| G-1 | 当てはまる組の数と局の数 |");
    expect(dev.markdown.join("\n")).toContain("満たさなかった");
    expect(dev.markdown.join("\n")).toContain("測れなかった");
  });

  it("T-3: T-2 を --include-insufficient で person → 見出しと根拠不足の固定文だけ。項目名・G- の記号・数が出ない", () => {
    const material = materialTally({ tn: 9, tc: 4, g3: false, ahead: 3 });
    const items: Record<GateItemId, GateItemResult> = { "G-1": "notMet", "G-2": "met", "G-3": "notEvaluable", "G-4": "met" };
    const [condition] = conditionLines(report([gateLine({ material, items })], { audience: "person", includeInsufficient: true }).lines);
    expect(texts(condition!.sentences)).toStrictEqual([`条件 test_only_a: ${TEXT_A}`, TEMPLATES.insufficient.text]);
    expect(condition!.sentences.map((sentence) => sentence.text).join("")).not.toMatch(/G-|[0-9]/);
  });

  it("T-4: notJudged draft・readableText 無し → person は行も数もなし / dev は見出し「条件 test_only_d」と「判定していません」", () => {
    const line = gateLine({ id: "test_only_d", sha: SHA_D, label: DEF_D.label, kind: "draft" });
    expect(conditionLines(report([line], { audience: "person" }).lines)).toStrictEqual([]);
    const [condition] = conditionLines(report([line], { audience: "dev" }).lines);
    expect(texts(condition!.sentences)).toStrictEqual(["条件 test_only_d", TEMPLATES.draft.text]);
    expect(condition!.notJudged).toBe("draft");
  });

  it("T-5: approved の定義に readableText が無い → 止まる(書かない)", () => {
    const context = { ...CONTEXT, definitions: [{ ...DEF_A, readableText: undefined }] };
    expect(inputProblems(() => report([gateLine()], { audience: "person" }, context))).toStrictEqual(["行 1: approved の定義に readableText が無い"]);
  });

  it("T-7: 百分率は整数の四捨五入(29/200 は 15%。浮動小数の Math.round(29/200*100) は 14)。分母 0 は「分母 0」", () => {
    expect([rateText(1, 3), rateText(2, 3), rateText(29, 200), rateText(0, 5), rateText(0, 0)]).toStrictEqual(["1/3・33%", "2/3・67%", "29/200・15%", "0/5・0%", "分母 0"]);
  });

  it("T-8: 「繰り返し」は G-1 met の F-6 だけ(G-1 notMet の dev の行には無い)", () => {
    const insufficient = report([gateLine({ material: materialTally({ tn: 9, tc: 4, g3: false, ahead: 3 }), items: { "G-1": "notMet", "G-2": "met", "G-3": "notEvaluable", "G-4": "met" } })], { audience: "dev" });
    expect(JSON.stringify(texts(conditionLines(insufficient.lines)[0]!.sentences))).not.toContain("繰り返し");
    expect(JSON.stringify(texts(conditionLines(report([gateLine()], { audience: "dev" }).lines)[0]!.sentences))).toContain("繰り返し");
  });

  it("T-11: test.set sente6+gote4・provisional false → F-5 が無い", () => {
    const [condition] = conditionLines(report([gateLine({ set: "sente6+gote4" })], { audience: "person" }).lines);
    expect(condition!.sentences.some((sentence) => sentence.template === "F-5")).toBe(false);
    expect(condition!.sentences.find((sentence) => sentence.template === "F-4")!.text).toContain("別の 10 局");
  });
});

describe("STEP D6: 入力の確かめ(計画 5.1 の T-6・T-20・T-23・T-25)", () => {
  const withTally = (patch: (line: Record<string, any>) => void, base: Record<string, unknown> = gateLine()) => {
    const line = JSON.parse(JSON.stringify(base)) as Record<string, any>;
    patch(line);
    return line;
  };
  const cases: Array<[string, () => unknown, string]> = [
    ["版", () => report([withTally((l) => (l.schemaVersion = "0.2"))], { audience: "dev" }), "schemaVersion が知っている版でない"],
    ["person の記号", () => report([withTally((l) => (l.person = "someone"))], { audience: "dev" }), "person が p と数字の記号でない"],
    ["path が絶対パス", () => report([withTally((l) => (l.material.inputs[0].path = "/Users/x/a.jsonl"))], { audience: "dev" }), "material.inputs[0].path が絶対パスか根の外"],
    ["path が根の外", () => report([withTally((l) => (l.test.inputs[0].path = "../../outside/a.jsonl"))], { audience: "dev" }), "test.inputs[0].path が絶対パスか根の外"],
    ["入力の path が絶対パス", () => report([gateLine()], { audience: "dev" }, { ...CONTEXT, input: { ...CONTEXT.input, path: "/Users/x/gate.jsonl" } }), "入力の path が絶対パス"],
    ["入力の path が根の外", () => report([gateLine()], { audience: "dev" }, { ...CONTEXT, input: { ...CONTEXT.input, path: "../outside/gate.jsonl" } }), "入力の path が絶対パスか根の外"],
    ["verdict と items", () => report([withTally((l) => (l.gate.items[1].result = "notMet"))], { audience: "dev" }), "verdict が meets なのに met でない項目がある"],
    ["approved で notJudged draft", () => report([withTally((l) => (l.gate = { notJudged: "draft" }))], { audience: "dev" }), "approved の定義なのに notJudged: draft"],
    ["件数 tc > tn", () => report([withTally((l) => (l.material.tally.truePairs.collapsed = 30))], { audience: "dev" }), "material.tally.truePairs.collapsed が denominator より大きい"],
    ["gateValues の違い", () => report([withTally((l) => (l.gateValues.minGames = 2))], { audience: "dev" }), "gateValues が人間の確定値(GATE_VALUES)と違う"],
    ["G-1 met なのに tn 4", () => report([gateLine({ material: materialTally({ tn: 4, tc: 2 }), items: ALL_MET })], { audience: "dev" }), "G-1 の結果 met が、tally と gateValues から計算し直した notMet と違う"],
    ["G-3 の再計算の食い違い", () => report([withTally((l) => (l.material.tally.pvSide.pvTrue = 7))], { audience: "dev" }), "G-3 の結果 met が、tally と gateValues から計算し直した notMet と違う"],
    ["G-4 の再計算の食い違い", () => report([gateLine({ test: testTally("neg", 6), items: ALL_MET })], { audience: "dev" }), "G-4 の結果 met が、tally と gateValues から計算し直した notMet と違う"],
    ["sente6 で provisional false", () => report([gateLine({ provisional: false })], { audience: "dev" }), "test.provisional が test.set と食い違う"],
    ["定義の sha の違い", () => report([gateLine({ sha: SHA_OLD })], { audience: "dev" }), "definitionSha256 の定義のファイルが無い"],
  ];
  for (const [name, run, message] of cases) {
    it(`T-6 ${name}: 止まり、書かない`, () => {
      const problems = inputProblems(run);
      expect(problems.length).toBeGreaterThan(0);
      expect(problems.join("\n")).toContain(message);
    });
  }

  it("T-20: 採った行どうしで conditionsInRun(3 と 4)か material.inputs の本数(20 と 19)が違えば止まる(C-2)", () => {
    const b = { id: "test_only_b", sha: SHA_B, label: DEF_B.label };
    expect(inputProblems(() => report([gateLine(), gateLine({ ...b, conditionsInRun: 4 })], { audience: "dev" })).join("\n")).toContain("採った行どうしで conditionsInRun が違う");
    const fewer = materialTally({ games: 19 });
    expect(inputProblems(() => report([gateLine(), gateLine({ ...b, material: fewer })], { audience: "dev" })).join("\n")).toContain("採った行どうしで material.inputs の本数が違う");
  });

  it("T-23: test.set が既知の 2 つ以外 / fc 0・tc 0 なのに G-2 met / 材料の側の fn 0 なのに G-4 met → 止まる", () => {
    expect(inputProblems(() => report([gateLine({ set: "gote4" })], { audience: "dev" })).join("\n")).toContain("test.set が sente6・sente6+gote4 のどれでもない");
    const zeroCollapse: GateTally = { ...materialTally(), truePairs: collapseTally(23, 0, 7, 8), falsePairs: collapseTally(341, 0, 20, 120) };
    expect(inputProblems(() => report([gateLine({ material: zeroCollapse, items: { "G-1": "met", "G-2": "met", "G-3": "met", "G-4": "notEvaluable" } })], { audience: "dev" })).join("\n")).toContain(
      "G-2 の結果 met が、tally と gateValues から計算し直した notMet と違う",
    );
    const noFalse: GateTally = { ...materialTally(), falsePairs: collapseTally(0, 0, 0, 0) };
    expect(inputProblems(() => report([gateLine({ material: noFalse, items: { "G-1": "met", "G-2": "notEvaluable", "G-3": "met", "G-4": "met" } })], { audience: "dev" })).join("\n")).toContain(
      "G-4 の結果 met が、tally と gateValues から計算し直した notEvaluable と違う",
    );
  });

  it("T-25: material.tally.games 20 と material.inputs 19 本 / test.tally.games と test.inputs の違い → 止まる", () => {
    expect(inputProblems(() => report([withTally((l) => l.material.inputs.pop())], { audience: "dev" })).join("\n")).toContain("material.tally.games と material.inputs の本数が違う");
    expect(inputProblems(() => report([withTally((l) => l.test.inputs.pop())], { audience: "dev" })).join("\n")).toContain("test.tally.games と test.inputs の本数が違う");
  });

  // ---- 監査 93 の C-1: 再計算の式の項と境(試験だけ)----
  it("C-1 F-2b の境: 直前が優勢の組の割合の差がちょうど 10 ポイント(100·|5·10 − 4·10| = 1000 = 10·10·10)なら出す", () => {
    const material = gateTally(20, collapseTally(10, 5, 3, 5), collapseTally(10, 1, 3, 4), { state: "applicable", n: 19, actualTrue: 13, pvTrue: 5 });
    const [condition] = conditionLines(report([gateLine({ material })], { audience: "dev" }).lines);
    expect(condition!.sentences.some((sentence) => sentence.template === "F-2b")).toBe(true);
  });

  it("C-1 G-2 の差の境: 100·(tc·fn − fc·tn) がちょうど 10·tn·fn(真 2/10・偽 10/100。比も 2·100 = 2·10·10 でちょうど)なら met", () => {
    const material = gateTally(20, collapseTally(10, 2, 3, 5), collapseTally(100, 10, 20, 50), { state: "applicable", n: 19, actualTrue: 13, pvTrue: 5 });
    expect(recomputeItemResults(material, testTally("pos", 6), GATE_VALUES)["G-2"]).toBe("met");
  });

  it("C-1 G-3 の境: 2·pvTrue がちょうど actualTrue(pvTrue 3・actualTrue 6)なら met", () => {
    const material = { ...materialTally(), pvSide: { state: "applicable", n: 10, actualTrue: 6, pvTrue: 3 } } as GateTally;
    expect(recomputeItemResults(material, testTally("pos", 6), GATE_VALUES)["G-3"]).toBe("met");
  });

  it("C-1 G-1 の局の数: tn 23 でも tn の組のある局が 2(材料の局は 20)なら notMet(局は gamesWithDenominator で数える)", () => {
    expect(recomputeItemResults(materialTally({ tnGames: 2 }), testTally("pos", 6), GATE_VALUES)["G-1"]).toBe("notMet");
  });

  it("C-1 G-4 の試す側の最小数: 試す側の tn が 2(向きは同じ正)なら notMet", () => {
    const test = gateTally(6, collapseTally(2, 1, 2, 1), collapseTally(90, 17, 6, 30), { state: "applicable", n: 7, actualTrue: 3, pvTrue: 1 });
    expect(recomputeItemResults(materialTally(), test, GATE_VALUES)["G-4"]).toBe("notMet");
  });

  it("C-1 notEvaluable と偽る行: 再計算では met の G-3 を、行が notEvaluable と書いていれば止まる", () => {
    const problems = inputProblems(() => report([gateLine({ items: { ...ALL_MET, "G-3": "notEvaluable" } })], { audience: "dev" }));
    expect(problems.join("\n")).toContain("G-3 の結果 notEvaluable が、tally と gateValues から計算し直した met と違う");
  });

  it("recomputeItemResults: G-2 は偽の崩れが 0 なら真の崩れ ≥ 1 で比の条件を満たす(D4 の実装の式 ― 13.2 の決定 2)", () => {
    const test = testTally("pos", 6);
    const withOneCollapse: GateTally = { ...materialTally(), truePairs: collapseTally(23, 3, 7, 8), falsePairs: collapseTally(341, 0, 20, 120) };
    expect(recomputeItemResults(withOneCollapse, test, GATE_VALUES)["G-2"]).toBe("met");
    const noCollapse: GateTally = { ...withOneCollapse, truePairs: collapseTally(23, 0, 7, 8) };
    expect(recomputeItemResults(noCollapse, test, GATE_VALUES)["G-2"]).toBe("notMet");
  });
});

describe("STEP D6: 向き・採る行・注記(計画 T-14〜T-16・T-18・T-21・T-24)", () => {
  it("T-14: F-4 の向きは試す側の符号から: 正 → 高い / 負(dev の insufficient、材料の側も負で G-4 met)→ 低い / 0 → 文なし・差なし / fn 0 → 文なし・比べられない", () => {
    const f4 = (line: Record<string, unknown>) => {
      const [condition] = conditionLines(report([line], { audience: "dev" }).lines);
      return [condition!.sentences.find((sentence) => sentence.template === "F-4")?.text ?? null, condition!.dev!.testDirection];
    };
    expect(f4(gateLine())[0]).toContain("より高い向きでした。");
    const negative = { material: materialTally({ sign: "neg" }), test: testTally("neg", 6), items: { "G-1": "met", "G-2": "notMet", "G-3": "met", "G-4": "met" } as Record<GateItemId, GateItemResult> };
    expect(f4(gateLine(negative))[0]).toContain("より低い向きでした。");
    expect(f4(gateLine({ test: testTally("zero", 6), items: { ...ALL_MET, "G-4": "notMet" } }))).toStrictEqual([null, "noDifference"]);
    expect(f4(gateLine({ test: testTally("fn0", 6), items: { ...ALL_MET, "G-4": "notEvaluable" } }))).toStrictEqual([null, "notComparable"]);
  });

  it("T-15: 同じ条件 id が sente6・sente6+gote4・後から再実行した sente6 の順 → person は sente6+gote4 の行(2 行目)だけ。dev は採らなかった行 2", () => {
    const lines = [gateLine({ sha: SHA_OLD }), gateLine({ set: "sente6+gote4" }), gateLine({ sha: "f".repeat(64) })];
    const taken = chooseRows(entriesOf(lines) as unknown as NumberedGateLine[]);
    expect(taken.map((entry) => [entry.row.line, entry.rowsNotTaken])).toStrictEqual([[2, 2]]);
    const [person] = conditionLines(report(lines, { audience: "person" }).lines);
    expect(person!.input.line).toBe(2);
    expect(conditionLines(report(lines, { audience: "dev" }).lines)[0]!.dev!.rowsNotTaken).toBe(2);
  });

  it("T-16: F-2b は直前が優勢の組の割合の差が 10 ポイント以上のとき(真 12/23・偽 120/341 は出す、真 8/23・偽 120/341 は出さない)", () => {
    const has = (f2b: boolean) => conditionLines(report([gateLine({ material: materialTally({ f2b }) })], { audience: "person" }).lines)[0]!.sentences.some((sentence) => sentence.template === "F-2b");
    expect([has(true), has(false)]).toStrictEqual([true, false]);
  });

  it("T-18: STANDING_BOUNDS を { aheadCp: 400, behindCp: -200 } に差し替えると、N-1 が +400・−200 になり sources に同じ値", () => {
    const { lines } = report([gateLine()], { audience: "person" }, { ...CONTEXT, standingBounds: { aheadCp: 400, behindCp: -200 } });
    const n1 = summaryOf(lines).sentences.find((sentence) => sentence.template === "N-1")!;
    expect(n1.text).toContain("評価値 +400 以上を優勢、−200 以下を劣勢");
    expect(n1.sources.map((source) => [source.slot, source.value])).toStrictEqual([["aheadCp", 400], ["behindCp", -200], ["approvedOn", STANDING_BOUNDS_APPROVED_ON]]);
  });

  it("T-21: person に出す条件式が 0 本(insufficient と draft だけ)→ person は 0 件の固定文・N-2・N-3(手の組)だけで N-1 が無い / dev は N-1〜N-3", () => {
    const lines = [gateLine({ material: materialTally({ tn: 9, tc: 4, g3: false, ahead: 3 }), items: { "G-1": "notMet", "G-2": "met", "G-3": "notEvaluable", "G-4": "met" } }), gateLine({ id: "test_only_d", sha: SHA_D, label: DEF_D.label, kind: "draft" })];
    const person = report(lines, { audience: "person" });
    expect(conditionLines(person.lines)).toStrictEqual([]);
    expect(texts(summaryOf(person.lines).sentences)).toStrictEqual([TEMPLATES.none.text, N2_TEXT, `用語: ${TERMS[0].text}`]);
    const dev = report(lines, { audience: "dev" });
    expect(summaryOf(dev.lines).sentences.map((sentence) => sentence.kind)).toStrictEqual(["N-1", "N-2", "N-3"]);
  });

  it("L-2: person の報告の条件式は id の昇順(入力が test_only_b・test_only_a の順でも a から)", () => {
    const lines = [gateLine({ id: "test_only_b", sha: SHA_B, label: DEF_B.label }), gateLine()];
    expect(conditionLines(report(lines, { audience: "person" }).lines).map((line) => line.condition.id)).toStrictEqual(["test_only_a", "test_only_b"]);
  });

  it("T-24: approved の定義の pairNotApplied の行(tally なし)と、別の条件式の meets の行 → 止まらない。dev に「手の組に当てない条件のため」、person には出ない。採る行の比べに入らない", () => {
    const lines = [gateLine({ id: "test_only_b", sha: SHA_B, label: DEF_B.label, kind: "pairNotApplied" }), gateLine()];
    const person = report(lines, { audience: "person" });
    expect(conditionLines(person.lines).map((line) => line.condition.id)).toStrictEqual(["test_only_a"]);
    const dev = conditionLines(report(lines, { audience: "dev" }).lines);
    expect(texts(dev.find((line) => line.condition.id === "test_only_b")!.sentences)).toStrictEqual(["条件 test_only_b: 二つめの条件を見る文", TEMPLATES.pairNotApplied.text]);
    const sameId = [gateLine({ kind: "pairNotApplied" }), gateLine({ sha: SHA_A })];
    expect(chooseRows(entriesOf([...sameId].reverse()) as unknown as NumberedGateLine[]).map((entry) => entry.row.line)).toStrictEqual([1]);
  });
});

// ---- 出力の全パターン(T-9・T-10・T-13)----

interface Combination {
  lines: Record<string, unknown>[];
  options: ReportOptions;
  context: ReportContext;
}

function allCombinations(): Combination[] {
  const combos: Combination[] = [];
  for (const set of ["sente6", "sente6+gote4"]) {
    const games = set.includes("+gote") ? 10 : 6;
    for (const audience of ["dev", "person"] as const) {
      for (const includeInsufficient of [false, true]) {
        for (const sign of ["pos", "neg"] as const) {
          for (const f2b of [false, true]) {
            for (const g3 of [true, false]) {
              for (const testSign of ["pos", "neg", "zero", "fn0"] as const) {
                const material = materialTally({ sign, f2b, g3 });
                const test = testTally(testSign, games);
                combos.push({ lines: [gateLine({ material, test, set })], options: { audience, includeInsufficient }, context: CONTEXT });
              }
            }
          }
        }
      }
      for (const withText of [true, false]) {
        const context = withText ? { ...CONTEXT, definitions: [DEF_A, DEF_B, { ...DEF_D, readableText: "下書きの条件を見る文" }] } : CONTEXT;
        combos.push({ lines: [gateLine({ id: "test_only_d", sha: SHA_D, label: DEF_D.label, kind: "draft", set })], options: { audience }, context });
      }
      combos.push({ lines: [gateLine({ id: "test_only_b", sha: SHA_B, label: DEF_B.label, kind: "pairNotApplied", set })], options: { audience }, context: CONTEXT });
    }
  }
  return combos;
}

/** 入力の行の欄の値(差し込み口の field を辿る) */
function valueAt(line: Record<string, any>, field: string, context: ReportContext): unknown {
  if (field === "definition.readableText") return context.definitions.find((definition) => definition.definitionSha256 === line.condition.definitionSha256)?.readableText;
  if (field === "STANDING_BOUNDS.aheadCp") return context.standingBounds.aheadCp;
  if (field === "STANDING_BOUNDS.behindCp") return context.standingBounds.behindCp;
  if (field === "STANDING_BOUNDS_APPROVED_ON") return STANDING_BOUNDS_APPROVED_ON;
  if (field === "material.inputs" || field === "test.inputs") return field.split(".").reduce((current, key) => current[key], line).length;
  return field.split(".").reduce((current: any, key) => current?.[key], line);
}

describe("STEP D6: 出力の全パターン(T-9・T-10・T-13)と契約のスキーマ", () => {
  const combos = allCombinations();
  let cache: Array<{ combo: Combination; report: ReturnType<typeof buildDiagnosisReport> }> | undefined;
  /** 組み立ては試験の中で(投げたときにファイルの読み込みで落ちず、使う試験が落ちる) */
  const builtAll = () => (cache ??= combos.map((combo) => ({ combo, report: buildDiagnosisReport(entriesOf(combo.lines), combo.context, combo.options) })));
  const schema = JSON.parse(readFileSync(new URL("../schemas/diagnosis-report.v0.1.schema.json", import.meta.url), "utf-8")) as JsonSchema;

  it("T-9: 全パターン(組み合わせ 268 通り)で報告を組めて(5.2 の確かめで止まらない)、出した文に 5.2 の確かめを当て直しても当たり 0", () => {
    expect(combos).toHaveLength(268);
    for (const { combo, report: result } of builtAll()) {
      const sentences = result.lines.flatMap((line) => line.sentences);
      expect(outputProblems(sentences, combo.lines.map((line) => (line.condition as { label: string }).label))).toStrictEqual([]);
    }
  });

  it("T-10: 全パターンの文で、差し込み口の field は 3.0 の固定の欄だけ、値はその欄の値(作った値は作り方どおり)、本文の数字は差し込み口の値か「1 段」の 1 だけ", () => {
    for (const { combo, report: result } of builtAll()) {
      const line = combo.lines[0] as Record<string, any>;
      for (const sentence of result.lines.flatMap((reportLine) => reportLine.sentences)) {
        for (const source of sentence.sources) {
          expect(source.field, `${sentence.template} {${source.slot}}`).toBe(SLOT_FIELDS[source.slot]);
          if (source.derivedBy === "pct") {
            const [collapsedField, denominatorField] = source.field.split(",");
            expect(source.value).toBe(rateText(valueAt(line, collapsedField!, combo.context) as number, valueAt(line, denominatorField!, combo.context) as number));
          } else if (source.derivedBy === "sign") {
            const [tc, tn, fc, fn] = source.field.split(",").map((field) => valueAt(line, field, combo.context) as number);
            expect(source.value).toBe(tc! * fn! - fc! * tn! > 0 ? "高い" : "低い");
          } else {
            expect(source.value, `${sentence.template} {${source.slot}}`).toBe(valueAt(line, source.field, combo.context));
          }
        }
        if (sentence.kind === "heading" || sentence.kind === "N-3") continue;
        const pool = [...sentence.sources.flatMap((source) => slotText(source).match(/[0-9]+/g) ?? []), ...(sentence.template === "F-1" ? ["1"] : [])];
        for (const digits of sentence.text.match(/[0-9]+/g) ?? []) {
          const index = pool.indexOf(digits);
          expect(index, `${sentence.template}: ${digits}`).toBeGreaterThan(-1);
          pool.splice(index, 1);
        }
      }
    }
  });

  it("T-13: 母数の網羅: 全部の文の型・F-4 の 2 つの向き・F-4 の 4 つの扱い・0 件の文が母数に現れる", () => {
    const sentences = builtAll().flatMap(({ report: result }) => result.lines.flatMap((line) => line.sentences));
    const templates = new Set(sentences.map((sentence) => sentence.template));
    for (const key of Object.keys(TEMPLATES) as TemplateKey[]) expect(templates.has(key), key).toBe(true);
    expect(templates.has("terms")).toBe(true);
    const f4 = sentences.filter((sentence) => sentence.template === "F-4").map((sentence) => sentence.text);
    expect([f4.some((text) => text.includes("高い向き")), f4.some((text) => text.includes("低い向き"))]).toStrictEqual([true, true]);
    const directions = new Set(builtAll().flatMap(({ report: result }) => conditionLines(result.lines).map((line) => line.dev?.testDirection)).filter((value) => value !== undefined));
    expect([...directions].sort()).toStrictEqual(["noDifference", "notApplicable", "notComparable", "shown"]);
  });

  it("契約のスキーマ: 全パターンの出力の行(dev・person、条件式の行と注記の行)が diagnosis-report v0.1 を通る", () => {
    for (const { report: result } of builtAll()) for (const line of result.lines) expect(validate(JSON.parse(JSON.stringify(line)), schema)).toStrictEqual([]);
  });

  it("T-26: D6 の固定例の Gate の行(全パターン・draft・pairNotApplied)が D4 の契約のスキーマ(diagnosis-gate v0.1)を通る", () => {
    for (const combo of combos) for (const line of combo.lines) expect(validateDiagnosisGateLine(JSON.parse(JSON.stringify(line)))).toStrictEqual([]);
    expect(validateDiagnosisGateLine(JSON.parse(JSON.stringify(gateLine())))).toStrictEqual([]);
  });

  it("T-12: 同じ入力を 2 回組むと、行と Markdown がバイト一致", () => {
    const again = combos.slice(0, 20).map((combo) => buildDiagnosisReport(entriesOf(combo.lines), combo.context, combo.options));
    expect(JSON.stringify(again)).toBe(JSON.stringify(builtAll().slice(0, 20).map(({ report: result }) => result)));
  });
});

describe("STEP D6: 出力の確かめ(計画 5.2 の T-17・T-19・T-22)", () => {
  it("T-17: approved の readableText に「弱点」/「傾向」/ label の文字列 /「繰り返し」→ 止まる。固定文の中の「傾向」「繰り返し」では止まらない。固定文の型を変えると止まる", () => {
    for (const readableText of ["弱点を見る文", "傾向を見る文", "試験だけの定義を見る文", "繰り返しを見る文"]) {
      const context = { ...CONTEXT, definitions: [{ ...DEF_A, readableText }] };
      expect(inputProblems(() => report([gateLine()], { audience: "person" }, context)).join("\n"), readableText).toMatch(/文 0\(headingWithText\): 「(弱点|傾向|試験だけの定義|繰り返し)」を含む/);
    }
    const meets: ReportSentence = { kind: "verdict", template: "meets", text: MEETS_TEXT, sources: [] };
    expect(outputProblems([meets], [LABEL_A])).toStrictEqual([]);
    expect(outputProblems([{ ...meets, text: MEETS_TEXT.replace("価値があります", "価値がありますね") }], [LABEL_A])).toContain("文 0(meets): 固定文が型と違う");
  });

  it("T-17b(S-1): 空白・ゼロ幅文字で割った語、半角の語、label を割った語も、NFKC で揃えて空白を除いてから照合して止める", () => {
    for (const readableText of ["弱 点を見る文", "弱\u200B点を見る文", "ﾐｽを見る文", "試験だけの 定義を見る文"]) {
      const context = { ...CONTEXT, definitions: [{ ...DEF_A, readableText }] };
      expect(inputProblems(() => report([gateLine()], { audience: "person" }, context)).join("\n"), JSON.stringify(readableText)).toMatch(/文 0\(headingWithText\): 「(弱点|ミス|試験だけの定義)」を含む/);
    }
  });

  it("T-17c(S-2): 「くせ」「あなた」「ご自身」「いつも」「がち」も止まる。一覧に無い「ため」は止まらない(誤検出を避けるため足していない)", () => {
    for (const word of ["くせ", "あなた", "ご自身", "いつも", "がち"]) {
      const context = { ...CONTEXT, definitions: [{ ...DEF_A, readableText: `${word}を見る文` }] };
      expect(inputProblems(() => report([gateLine()], { audience: "person" }, context)).join("\n"), word).toContain(`「${word}」を含む`);
    }
    const context = { ...CONTEXT, definitions: [{ ...DEF_A, readableText: "確かめるための条件の文" }] };
    expect(inputProblems(() => report([gateLine()], { audience: "person" }, context))).toStrictEqual([]);
  });

  it("T-19: 終わりの検査は位置で見る(F-1 の種類で「です。」で終わる文は止まる)", () => {
    const f1: ReportSentence = { kind: "F-1", template: "F-1", text: "テストの文でした。テストの文です。", sources: [] };
    expect(outputProblems([f1], [])).toContain("文 0(F-1): 文の終わりが型の位置と違う");
    expect(splitSentences(TEMPLATES["N-1"].text)).toHaveLength(2);
  });

  it("T-22: N-3 の用語の並び「自分の手 1 つと相手の手 1 つ」は数の検査の対象外(止まらない ― C-1)", () => {
    expect(outputProblems([{ kind: "N-3", template: "terms", text: N3_ALL, sources: [] }], [])).toStrictEqual([]);
  });
});
