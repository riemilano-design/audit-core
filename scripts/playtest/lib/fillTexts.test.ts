// 言い換えの束(1 回限りの境界測定実験)の純粋部の試験。計画 docs/PLAN_FILL_TEXTS_2026-10-05.md §5・§7。
import { describe, expect, it } from "vitest";
import {
  EXPERIMENT, FillTextsError, RULES_LINES, RULES_SHA256, capProblems, instructionText, itemRefKey, maxCostBefore, rulesSha256, runFillTexts,
  slotJobsOf, statementsOf, userTextOf, type FillTextsDeps, type SlotJob, type VerifyVerdict,
} from "./fillTexts.js";
import type { StructuredRequest, StructuredResponse } from "./llmClient.js";

const TERMS = [["第 1 候補", "この局面でエンジンが 1 番に挙げた手。"], ["分かれ道", "差が大きかった局面。"], ["自玉側", "自分の玉のまわりを固める手。"], ["一致率", "同じ側だった割合。"]] as const;
const FORBIDDEN = ["普段"];
const PRICES = { inPerMillion: 5, outPerMillion: 25 };
const STATEMENT_LEAD = "攻めも自玉側も第 1 候補と違う側が残り(65 / 107、76 / 132)、長考の直後の 1 手は 9 / 37 で崩れた";
const STATEMENT_H1 = "一致率は 0.7 を下回り、65 / 107 と 76 / 132 で両方の側に残った";
const STATEMENT_H2 = "0〜1 秒の 531 手で崩れは 22 手、長考直後は 9 / 37";
const STATEMENT_H3 = "一度優勢になった 18 局のうち 6 局を落とした";

function ref(seat: number, hid: string): Record<string, unknown> { return { seatIndex: seat, hypothesisId: hid }; }
function integration(): Record<string, unknown> {
  const cluster = (seat: number, hid: string, statement: string) => ({ itemRefs: [ref(seat, hid)], representative: { statement, internal: { reasoning: "普段と違う型(内部)" } } });
  return { clusters: [cluster(0, "lead", STATEMENT_LEAD), cluster(0, "h1", STATEMENT_H1), cluster(1, "h2", STATEMENT_H2), cluster(2, "h3", STATEMENT_H3), cluster(0, "q1", "問いの読み(合成)")] };
}
function selection(): Record<string, unknown> {
  return {
    runId: "558b8a81-20261001-2",
    lead: { itemRef: ref(0, "lead"), statementSource: "integration.representative" },
    p1: [{ slot: "p1.1", aggregateIds: ["sideMatch.attack"], itemRef: ref(0, "h1"), readingRequired: true },
         { slot: "p1.2", aggregateIds: ["time.quickAfterLongThink"], itemRef: ref(1, "h2"), readingRequired: true },
         { slot: "p1.3", aggregateIds: ["aheadThenLost"], itemRef: ref(2, "h3"), readingRequired: true }],
    answers: [{ questionId: "q1", status: "answered", itemRefs: [ref(0, "q1")], aggregateIds: [] }],
  };
}
function jobs(): SlotJob[] { return slotJobsOf(selection(), integration()); }
const INSTRUCTION = instructionText(TERMS, FORBIDDEN, EXPERIMENT.maxChars);

function response(text: string | undefined, opts: { finish?: "stop" | "length"; json?: unknown; usage?: { inputTokens: number; outputTokens: number } } = {}): StructuredResponse {
  const json = opts.json !== undefined ? opts.json : text === undefined ? undefined : { text };
  return { text: JSON.stringify(json ?? null), json, raw: { ok: true }, usage: opts.usage ?? { inputTokens: 600, outputTokens: 40 }, finishReason: opts.finish ?? "stop", finishReasonRaw: "end_turn", httpStatus: 200, attempts: 1 };
}
/** 偽の席: スロットごとに返答の列。偽の照合: 文 → 問題の一覧(既定は「99」が入っていれば落とす・それ以外は通す)。
 *  F-5 そのものの判定は「数の字」「指し手」の問題が無いこと(禁止語・長さの問題だけなら F-5 は通る ― 条件 11) */
function fakeDeps(answers: Record<string, (string | undefined)[]>, verifyRule?: (slot: string, text: string) => string[]): FillTextsDeps & { calls: StructuredRequest[]; verified: Record<string, string>[] } {
  const calls: StructuredRequest[] = [];
  const verified: Record<string, string>[] = [];
  const counters: Record<string, number> = {};
  return {
    calls, verified,
    call: async (req) => {
      calls.push(req);
      const slot = /スロット: ([^(]+)\(/.exec(req.user)?.[1] ?? "?";
      const n = counters[slot] ?? 0;
      counters[slot] = n + 1;
      const list = answers[slot] ?? [];
      return response(list[Math.min(n, list.length - 1)]);
    },
    verify: async (texts) => {
      verified.push(texts);
      const out: Record<string, VerifyVerdict> = {};
      for (const [slot, text] of Object.entries(texts)) {
        const problems = verifyRule ? verifyRule(slot, text) : (text.includes("99") ? [`スロット ${slot}: 数の字「99」が statement に無い`] : []);
        out[slot] = { problems, f5Passed: !problems.some((p) => p.includes("数の字") || p.includes("指し手")) };
      }
      return out;
    },
    now: () => new Date("2026-10-05T12:00:00Z"),
  };
}
function cfg(over: Record<string, unknown> = {}) {
  return { jobs: jobs(), instruction: INSTRUCTION, model: "claude-opus-5", apiKey: "sk-ant-test-KEY", prices: PRICES, capUsdFromEnv: 1, runId: "r1", today: "2026-10-05", gitHead: "abc", ...over };
}

describe("言い換えの束 ― 人間の GO の条件は字で留まっている", () => {
  it("t1 固定値(1 席 Claude・4 スロット・3 試行・12 呼び出し・1,000 トークン・1 USD・200 字・答えの文は作らない)", () => {
    expect(EXPERIMENT).toEqual({ seat: "claude", provider: "anthropic", maxSlots: 4, maxAttemptsPerSlot: 3, maxCalls: 12, reserveOutputTokens: 1000, capUsd: 1, maxChars: 200, generateAnswers: false, temperature: 0 });
    expect(EXPERIMENT.maxAttemptsPerSlot * EXPERIMENT.maxSlots).toBe(EXPERIMENT.maxCalls);
  });
  it("t2 指示文は固定(RULES_LINES の sha が留まり、用語と禁止語と上限が入る)", () => {
    expect(rulesSha256()).toBe(RULES_SHA256);
    expect(RULES_LINES).toHaveLength(7);
    expect(INSTRUCTION).toContain("「普段」");
    expect(INSTRUCTION).toContain("200 字以内");
    for (const [term, meaning] of TERMS) expect(INSTRUCTION).toContain(`- ${term}: ${meaning}`);
    expect(INSTRUCTION).toContain("1 字も変えない");
    expect(INSTRUCTION).toContain("因果関係を変えない");
    expect(() => instructionText([], FORBIDDEN, 200)).toThrow(FillTextsError);
    expect(() => instructionText(TERMS, [], 200)).toThrow(FillTextsError);
  });
  it("t3 .env の上限が 1 でなければ回さない", () => {
    expect(capProblems(1)).toEqual([]);
    expect(capProblems(undefined)[0]).toContain("SEAT_COST_CAP_USD");
    expect(capProblems(10)[0]).toContain("この実験の上限は 1 USD");
    expect(capProblems(0.5)).toHaveLength(1);
  });
});

describe("スロット = lead + 読み(true)だけ。答えの文は作らない", () => {
  it("t4 4 スロット・statement は統合の代表・internal は読まない", () => {
    const js = jobs();
    expect(js.map((j) => j.slot)).toEqual(["lead", "p1.1", "p1.2", "p1.3"]);
    expect(js[0]!.kind).toBe("lead");
    expect(js[1]!.statement).toBe(STATEMENT_H1);
    expect(js.some((j) => j.slot.startsWith("ans."))).toBe(false);
    for (const j of js) expect(j.statement).not.toContain("内部");
    expect(itemRefKey(ref(3, "I-3-007"))).toBe("3:I-3-007");
    expect(() => itemRefKey({ seatIndex: "3", hypothesisId: "x" })).toThrow(FillTextsError);
    expect(statementsOf(integration()).get("1:h2")).toBe(STATEMENT_H2);
  });
  it("t5 readingRequired が false の行は作らない・statement が無ければ止まる・5 スロット目は止まる", () => {
    const s = selection();
    (s.p1 as Record<string, unknown>[])[2]!.readingRequired = false;
    expect(slotJobsOf(s, integration()).map((j) => j.slot)).toEqual(["lead", "p1.1", "p1.2"]);
    const s2 = selection();
    (s2.p1 as Record<string, unknown>[])[0]!.itemRef = ref(9, "none");
    expect(() => slotJobsOf(s2, integration())).toThrow(/統合の clusters に無い/);
    const s3 = selection();
    (s3.p1 as Record<string, unknown>[]).push({ slot: "p1.4", itemRef: ref(2, "h3"), readingRequired: true });
    expect(() => slotJobsOf(s3, integration())).toThrow(/4 まで/);
  });
  it("t6 user の本文は statement だけ(packet の数・問いの原文・候補は渡さない)", () => {
    const u = userTextOf(jobs()[1]!);
    expect(u).toContain(STATEMENT_H1);
    expect(u).toContain("スロット: p1.1(");
    expect(u).not.toContain("packet");
    expect(u).not.toContain("404");
    expect(userTextOf(jobs()[0]!)).toContain("太字の 1 文");
  });
});

describe("実行 ― 1 試行 = 1 呼び出し・F-5 を通った文だけ・落ちたら止まる", () => {
  it("t7 全部 1 回で通る: 4 呼び出し・4 文・採用可能 4・実費は単価どおり", async () => {
    const deps = fakeDeps({ lead: ["A"], "p1.1": ["B"], "p1.2": ["C"], "p1.3": ["D"] });
    const r = await runFillTexts(cfg(), deps);
    expect(r.texts).toEqual({ lead: "A", "p1.1": "B", "p1.2": "C", "p1.3": "D" });
    expect(deps.calls).toHaveLength(4);
    expect(deps.verified).toHaveLength(4);
    const totals = r.report.totals as Record<string, unknown>;
    expect(totals.calls).toBe(4);
    expect(totals.adoptable).toBe(4);
    expect(totals.actualCostUsd).toBeCloseTo(4 * (600 * 5 + 40 * 25) / 1_000_000, 10);
    expect(totals.stopReason).toBeNull();
    // 呼び出しの形: Claude・取り置き 1,000・温度 0・system は固定の指示文。
    for (const c of deps.calls) {
      expect(c.provider).toBe("anthropic");
      expect(c.maxOutputTokens).toBe(1000);
      expect(c.temperature).toBe(0);
      expect(c.system).toBe(INSTRUCTION);
    }
  });
  it("t8 落ちたら累積の指摘で再試行(前の出力は渡さない)・3 回とも落ちれば書かない", async () => {
    const deps = fakeDeps({ lead: ["99 が入っている", "まだ 99", "通る文"], "p1.1": ["99", "99", "99"], "p1.2": ["C"], "p1.3": ["D"] });
    const r = await runFillTexts(cfg(), deps);
    expect(r.texts).toEqual({ lead: "通る文", "p1.2": "C", "p1.3": "D" });
    expect("p1.1" in r.texts).toBe(false);
    const slots = r.report.slots as Record<string, unknown>[];
    expect(slots[0]).toMatchObject({ slot: "lead", attempts: 3, f5Passed: 1, adoptable: 1 });
    expect(slots[1]).toMatchObject({ slot: "p1.1", attempts: 3, f5Passed: 0, adoptable: 0 });
    expect((slots[1]!.failureReasons as string[])).toHaveLength(3);
    // 3 回目の user は 1 回目と 2 回目の理由を両方持ち、前の出力の文は持たない。
    const leadCalls = deps.calls.filter((c) => c.user.includes("スロット: lead("));
    expect(leadCalls[2]!.user).toContain("数の字「99」");
    expect(leadCalls[2]!.user).not.toContain("99 が入っている");
    expect(leadCalls[0]!.user).not.toContain("前回の返答");
    expect(r.problems["p1.1"]).toHaveLength(3);
    expect((r.report.totals as Record<string, unknown>).calls).toBe(3 + 3 + 1 + 1);
  });
  it("t9 形が合わない返答は 1 試行として数え、理由を累積する", async () => {
    const deps = fakeDeps({ lead: ["A"], "p1.1": ["B"], "p1.2": ["C"], "p1.3": ["D"] });
    let first = true;
    const call = deps.call;
    deps.call = async (req, key) => {
      if (first && req.user.includes("スロット: lead(")) { first = false; return response(undefined, { json: { answer: "別の欄" } }); }
      return call(req, key);
    };
    const r = await runFillTexts(cfg(), deps);
    expect(r.texts.lead).toBe("A");
    const lead = (r.report.slots as Record<string, unknown>[])[0]!;
    expect(lead.attempts).toBe(2);
    expect((lead.failureReasons as string[])[0]).toContain("形:");
    expect(deps.verified).toHaveLength(4); // 形が合わない返答は照合に送らない
  });
  it("t10 費用の上限に当たったら送らず、残りのスロットも回さない(別の席で埋めない)", async () => {
    const deps = fakeDeps({ lead: ["A"], "p1.1": ["B"], "p1.2": ["C"], "p1.3": ["D"] });
    // 単価を上げて 1 呼び出しで上限 1 USD を越える見込みにする。
    const r = await runFillTexts(cfg({ prices: { inPerMillion: 500_000, outPerMillion: 500_000 } }), deps);
    expect(deps.calls).toHaveLength(0);
    expect(r.texts).toEqual({});
    const slots = r.report.slots as Record<string, unknown>[];
    expect(String((slots[0]!.failureReasons as string[])[0])).toContain("費用の上限 1 USD");
    expect(slots[1]!.notAttempted).toContain("費用の上限");
    expect((r.report.totals as Record<string, unknown>).stopReason).toContain("残りも回さない");
  });
  it("t11 呼び出しは 12 まで(13 本目は送らない)", async () => {
    const deps = fakeDeps({ lead: ["99", "99", "99"], "p1.1": ["99", "99", "99"], "p1.2": ["99", "99", "99"], "p1.3": ["99", "99", "99"] });
    const r = await runFillTexts(cfg(), deps);
    expect(deps.calls).toHaveLength(12);
    expect(r.texts).toEqual({});
    // 5 本目のスロットが来ても 13 本目は出ない(合成: jobs を 5 にする ― slotJobsOf は 4 で止めるので直接渡す)。
    const five = [...jobs(), { slot: "p1.9", kind: "reading" as const, itemRef: { seatIndex: 2, hypothesisId: "h3" }, statement: STATEMENT_H3 }];
    const deps2 = fakeDeps({ lead: ["99", "99", "99"], "p1.1": ["99", "99", "99"], "p1.2": ["99", "99", "99"], "p1.3": ["99", "99", "99"], "p1.9": ["X"] });
    const r2 = await runFillTexts(cfg({ jobs: five }), deps2);
    expect(deps2.calls).toHaveLength(12);
    const last = (r2.report.slots as Record<string, unknown>[])[4]!;
    expect(String((last.failureReasons as string[])[0])).toContain("呼び出しの上限 12");
  });
  it("t12 送れなかった(HTTP)ときは再試行しない・鍵や単価や上限が無ければ回さない", async () => {
    const deps = fakeDeps({ lead: ["A"], "p1.1": ["B"], "p1.2": ["C"], "p1.3": ["D"] });
    const call = deps.call;
    deps.call = async (req, key) => { if (req.user.includes("スロット: p1.2(")) throw new Error("HTTP 500: boom"); return call(req, key); };
    const r = await runFillTexts(cfg(), deps);
    expect(r.texts).toEqual({ lead: "A", "p1.1": "B", "p1.3": "D" });
    expect((r.report.slots as Record<string, unknown>[])[2]).toMatchObject({ slot: "p1.2", attempts: 1, adoptable: 0 });
    await expect(runFillTexts(cfg({ apiKey: undefined }), deps)).rejects.toThrow(/鍵/);
    await expect(runFillTexts(cfg({ prices: { inPerMillion: 0, outPerMillion: 25 } }), deps)).rejects.toThrow(/単価/);
    await expect(runFillTexts(cfg({ capUsdFromEnv: 10 }), deps)).rejects.toThrow(/上限は 1 USD/);
  });
  it("t13 report は条件 5 の欄(試行数・F-5 通過数・採用可能数・失敗理由・実費・最大費用)と、測ったもの / 測っていないものの欄を持つ", async () => {
    const deps = fakeDeps({ lead: ["A"], "p1.1": ["99", "B"], "p1.2": ["C"], "p1.3": ["D"] });
    const r = await runFillTexts(cfg(), deps);
    const slots = r.report.slots as Record<string, unknown>[];
    for (const s of slots) for (const key of ["slot", "attempts", "f5Passed", "adoptable", "failureReasons", "actualCostUsd", "maxCostUsdBefore"]) expect(s).toHaveProperty(key);
    const before = maxCostBefore(jobs(), INSTRUCTION, PRICES);
    expect((r.report.totals as Record<string, unknown>).maxCostUsdBefore).toBeCloseTo(before.total, 12);
    expect(slots[1]!.maxCostUsdBefore).toBeCloseTo(before.perSlot["p1.1"]!, 12);
    // 最大費用は実行の前の数(実費と別)。**3 呼び出し × (入力の実測 + 取り置き 1,000)** ― 字で数え直す(関数と同じ表で比べない)。
    const inputTokens = Math.ceil([...`${INSTRUCTION}\n\n${userTextOf(jobs()[1]!)}`].length / 3);
    expect(before.perSlot["p1.1"]).toBeCloseTo(3 * (inputTokens * 5 + 1000 * 25) / 1_000_000, 12);
    expect(before.total).toBeGreaterThan((r.report.totals as Record<string, unknown>).actualCostUsd as number);
    const measured = r.report.measured as Record<string, unknown>;
    expect((measured.byMachine as string[]).join(" ")).toContain("F-5");
    expect((measured.notMeasured as string[]).join(" ")).toContain("因果");
    expect((measured.notMeasured as string[]).join(" ")).toContain("人間が読む");
    expect(String(measured.note)).toContain("監査済みの事実ではない");
    const fixed = r.report.fixed as Record<string, unknown>;
    expect(fixed.rulesSha256).toBe(RULES_SHA256);
    expect(fixed.capUsd).toBe(1);
    expect(r.files.some((f) => f.name === "p1.1_attempt_1_problems.txt")).toBe(true);
  });
  it("t15 上限は実行の単位 ― スロットが変わっても累計は戻らない", async () => {
    // 1 呼び出しの実費を 0.75 USD にする(入力 150,000 トークン × 5 USD/M)。見込みは小さいので 1 本目は送れる。
    // 2 本目は累計 0.75 + 見込みで 1 USD の内 → 送る。3 本目は累計 1.5 > 1 → 送らず、残りも回さない。
    const big = { inputTokens: 150_000, outputTokens: 0 };
    const deps = fakeDeps({ lead: ["A"], "p1.1": ["B"], "p1.2": ["C"], "p1.3": ["D"] });
    const call = deps.call;
    deps.call = async (req, key) => ({ ...(await call(req, key)), usage: big });
    const r = await runFillTexts(cfg(), deps);
    expect(deps.calls).toHaveLength(2);
    expect(Object.keys(r.texts)).toEqual(["lead", "p1.1"]);
    const slots = r.report.slots as Record<string, unknown>[];
    expect(String((slots[2]!.failureReasons as string[])[0])).toContain("費用の上限 1 USD");
    expect(slots[3]!.notAttempted).toContain("費用の上限");
    expect((r.report.totals as Record<string, unknown>).actualCostUsd).toBeCloseTo(1.5, 6);
  });
  it("t14 長さの判定は照合側(python)の仕事 ― 照合が返した理由をそのまま失敗理由にする。F-5 通過と採用可能は別項目(条件 11)", async () => {
    const deps = fakeDeps({ lead: ["A"], "p1.1": ["長い", "短い"], "p1.2": ["C"], "p1.3": ["D"] }, (slot, text) => (text === "長い" ? [`スロット ${slot}: 201 字 ― 上限 200 字を越えている`] : []));
    const r = await runFillTexts(cfg(), deps);
    expect(r.texts["p1.1"]).toBe("短い");
    const p11 = (r.report.slots as Record<string, unknown>[])[1]!;
    expect((p11.failureReasons as string[])[0]).toContain("上限 200 字");
    // 長さで落ちた 1 回目も F-5 は通っている → F-5 通過 2・採用可能 1(同じ数にならない)。
    expect(p11).toMatchObject({ attempts: 2, f5Passed: 2, adoptable: 1 });
    expect((r.report.totals as Record<string, unknown>).f5Passed).toBe(5);
    expect((r.report.totals as Record<string, unknown>).adoptable).toBe(4);
    const rows = p11.attemptRows as Record<string, unknown>[];
    expect(rows.map((a) => a.status)).toEqual(["rejected", "adoptable"]);
    expect(rows.map((a) => a.f5Passed)).toEqual([true, true]);
    expect(String((r.report.columns as Record<string, string>).adoptable)).toContain("採用そのもの");
    // 数の字で落ちた試行は F-5 も落ちる。
    const deps2 = fakeDeps({ lead: ["99", "A"], "p1.1": ["B"], "p1.2": ["C"], "p1.3": ["D"] });
    const r2 = await runFillTexts(cfg(), deps2);
    expect((r2.report.slots as Record<string, unknown>[])[0]).toMatchObject({ attempts: 2, f5Passed: 1, adoptable: 1 });
  });
});

describe("試行の記録は呼び出しの前に作り、後に同じファイルへ書き足す(人間の GO 条件 4・2026-10-05 の実行で usage が消えた)", () => {
  it("t16 照合が落ちても attempt_<slot>_<n>.json に usage と実費が残る・前の記録は欄が空・persist が無くても files に 1 本ずつ", async () => {
    const deps = fakeDeps({ lead: ["A"], "p1.1": ["B"], "p1.2": ["C"], "p1.3": ["D"] });
    const persisted: { name: string; content: string }[] = [];
    deps.verify = async () => { throw new Error("exit_fill.py --verify-texts が JSON を返さなかった(合成)"); };
    deps.persist = (f) => { persisted.push(f); };
    await expect(runFillTexts(cfg({ runId: "r1" }), deps)).rejects.toThrow(/JSON を返さなかった/);
    expect(persisted.map((f) => f.name)).toEqual(["attempt_lead_1.json", "attempt_lead_1.json", "lead_attempt_1_raw.json"]);
    const before = JSON.parse(persisted[0]!.content) as Record<string, unknown>;
    expect(before).toMatchObject({ attemptId: "r1:lead:1", slot: "lead", attempt: 1, status: "requested", usage: null, costUsd: null, cumulativeCostUsd: null, f5Passed: null, problems: [] });
    expect(typeof before.requestedAt).toBe("string");
    const after = JSON.parse(persisted[1]!.content) as Record<string, unknown>;
    expect(after).toMatchObject({ attemptId: "r1:lead:1", status: "responded", usage: { inputTokens: 600, outputTokens: 40 }, finishReason: "stop", f5Passed: null });
    expect(after.costUsd).toBeCloseTo((600 * 5 + 40 * 25) / 1_000_000, 12);
    expect(after.cumulativeCostUsd).toBeCloseTo((600 * 5 + 40 * 25) / 1_000_000, 12);
    // 送れなかったときも同じファイルに send_failed が残る。
    const deps3 = fakeDeps({ lead: ["A"], "p1.1": ["B"], "p1.2": ["C"], "p1.3": ["D"] });
    const names3: string[] = [];
    deps3.call = async () => { throw new Error("HTTP 500: boom"); };
    deps3.persist = (f) => { names3.push(`${f.name}:${String((JSON.parse(f.content.startsWith("{") ? f.content : "{}") as Record<string, unknown>).status ?? "-")}`); };
    await runFillTexts(cfg(), deps3);
    expect(names3.slice(0, 2)).toEqual(["attempt_lead_1.json:requested", "attempt_lead_1.json:send_failed"]);
    // persist が無くても files に試行の記録が 1 本ずつ(同じ name は上書き)、最後の状態で返る。
    const deps2 = fakeDeps({ lead: ["A"], "p1.1": ["99", "B"], "p1.2": ["C"], "p1.3": ["D"] });
    const r = await runFillTexts(cfg(), deps2);
    const attemptFiles = r.files.filter((f) => f.name.startsWith("attempt_"));
    expect(attemptFiles.map((f) => f.name)).toEqual(["attempt_lead_1.json", "attempt_p1.1_1.json", "attempt_p1.1_2.json", "attempt_p1.2_1.json", "attempt_p1.3_1.json"]);
    expect((JSON.parse(attemptFiles[1]!.content) as Record<string, unknown>).status).toBe("rejected");
    expect((JSON.parse(attemptFiles[2]!.content) as Record<string, unknown>).status).toBe("adoptable");
    expect(new Set(r.files.map((f) => f.name)).size).toBe(r.files.length);
  });
});
