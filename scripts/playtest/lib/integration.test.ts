// 束 R3 の試験(計画 docs/STEP_LLM_SEATS_R3_INTEGRATION_2026-09-30.md §5)。
//
// 【要点】席の項目は黙って消えない・一致は証拠でない・席名は出ない・internal は器に入らない、を変異 1 本ずつで見る。
// 【packet を読まない】integration.ts が observationPacket* を import しないことを試験が見る。packetDigest は呼び出し側が渡す packet の写し。
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  answersByQuestionOf, buildIntegrationInput, canonicalJson, completeIntegration, copySeatItem, integrationProblems, seatPermutation, validateIntegrationInput, validateIntegrationLlm,
} from "./integration.js";
import type { SeatInputMeta } from "./seatInput.js";
import { completeSeatOutput } from "./seatOutput.js";

const TODAY = "2026-09-30";
const RUN = "run20260930abc";
const SHA = (c: string) => c.repeat(64);

function meta(): SeatInputMeta {
  return {
    schemaVersion: "0.1", runId: RUN, passphrase: "run20260", packetId: "22aee8fe696d0262", customerRef: "c5", timeLimitSec: 180, games: 25,
    instructionSha256: SHA("3"), seatInputSha256: SHA("9"), bytes: 1, chars: 1, tokenEstimate: { value: 1, method: "chars/3" },
    sections: [{ section: "2", title: "集計", packetPath: "aggregates.<id>.numerator|denominator|value", rows: 3, lastKey: "aggregates.branches.total.value 値" }],
    omitted: [], notIncluded: [],
  };
}
function packet() {
  return {
    packetId: "22aee8fe696d0262", customerRef: "c5",
    facts: { games: [{ gameId: "g01", side: "先手", result: "勝ち", totalPlyCount: 123 }, { gameId: "g02", side: "後手", result: "負け", totalPlyCount: 88 }] },
    aggregates: [
      { id: "sideMatch.attack", numerator: 65, denominator: 107, unit: "positions", name: "第一候補が攻めの分かれ道のうち実戦も攻め" },
      { id: "branches.total", value: 404, unit: "positions", name: "分かれ道の総数" },
    ],
    provenance: { thresholds: [{ id: "ahead_cp", value: 300, unit: "centipawns", from: "x.py AHEAD_CP" }] },
  };
}
function request() {
  return { contract: "observation-request", schemaVersion: "0.1", customerRef: "c5", customerQuestions: [{ id: "q1", text: "普段指さない戦型の影響", via: "relayed" }], requestedScope: { games: 25, timeLimitSec: 180 } };
}
const NUM = () => ({ path: "aggregates.sideMatch.attack.numerator" });
const DEN = () => ({ path: "aggregates.sideMatch.attack.denominator" });
const TOTAL = () => ({ path: "aggregates.branches.total.value" });

/** 席が書いた形(seat-output.llm)。席ごとに少し変える */
function seatLlm(variant: "a" | "b" | "c") {
  const hyp = {
    itemId: "S-001", kind: "hypothesis", factOrHypothesis: "hypothesis", lane: "side",
    statement: variant === "c" ? "攻めの側は選ばれにくい(65 / 107)という読みです。" : "分かれ道で攻めの側が選ばれやすい(65 / 107)という読みです。",
    observations: [{ value: 65, unit: "positions", packetRef: NUM() }, { value: 107, unit: "positions", packetRef: DEN() }],
    counterEvidence: { attempted: true, items: [], result: "none_found" },
    prediction: { window: "次の 25 局", metric: "packet.aggregates.sideMatch.attack.numerator / packet.aggregates.sideMatch.attack.denominator", comparator: ">=", value: 0.6, alsoRequires: [] },
    internal: { reasoning: "0.61 は自分で割った", namesOutsideVocabulary: [] },
  };
  const finding = {
    itemId: "S-002", kind: "finding", factOrHypothesis: "fact", lane: "fork", statement: "分かれ道の総数は 404 だった。",
    observations: [{ value: 404, unit: "positions", packetRef: TOTAL() }], counterEvidence: { attempted: true, items: [], result: "none_found" },
  };
  const un = {
    itemId: "S-003", kind: "unanswerable", factOrHypothesis: "fact", lane: "shape", requestRef: { questionId: "q1" },
    statement: "局ごとの型の承認済みの判定が束に無いため、この問いには答えられない。",
    observations: [{ value: 404, unit: "positions", packetRef: TOTAL() }], counterEvidence: { attempted: true, items: [], result: "none_found" },
    neededObservation: { what: "局ごとの型の判定", whyNotInPacket: "定義が下書き", howToMeasure: "承認済みの定義で判定し直す" },
  };
  return {
    reach: { passphrase: "run20260", sections: [{ section: "2", lastKey: "aggregates.branches.total.value" }] },
    items: variant === "b" ? [hyp, finding] : [hyp, finding, un],
    answers: [variant === "b"
      ? { questionId: "q1", status: "answered", itemIds: ["S-001"], missing: [] }
      : { questionId: "q1", status: "unanswerable", itemIds: ["S-003"], missing: [{ what: "局ごとの型の判定", howToMeasure: "承認済みの定義で判定し直す" }] }],
    selfComputedNumbers: variant === "a" ? [{ value: 0.61, how: "65 / 107", fromPaths: ["aggregates.sideMatch.attack.numerator"] }] : [],
    omissions: [],
  };
}
function envelopeOf(seat: "gpt" | "gemini" | "claude", variant: "a" | "b" | "c") {
  return completeSeatOutput(seatLlm(variant), { runId: RUN, seat, model: `${seat}-test`, meta: meta(), today: TODAY, gitHead: "0000000", usage: { inputTokens: 1, outputTokens: 1 }, finishReason: "stop", attempts: 1, requestedAt: "2026-09-30T00:00:00Z" });
}
function build(runId = RUN) {
  return buildIntegrationInput(
    [{ seat: "gpt", envelope: envelopeOf("gpt", "a") }, { seat: "gemini", absentReason: "reach_failed" }, { seat: "claude", envelope: envelopeOf("claude", "c") }],
    { runId, packet: packet(), request: request(), seatOrderRef: "seat_order.json" },
  );
}
type Seat = { seatIndex: number; present: boolean; items?: { hypothesisId: string }[] };
/** 入力から、整理役が書く形の最小(束 2・dropped 1・矛盾 1・heldBack 1) */
function llmOf(input: Record<string, unknown>) {
  const seats = (input.seats as Seat[]).filter((s) => s.present);
  const [s1, s2] = seats as [Seat, Seat];
  const id = (s: Seat, n: number) => ({ seatIndex: s.seatIndex, hypothesisId: s.items![n]!.hypothesisId });
  return {
    clusters: [
      { clusterId: "C-001", packetRefs: ["aggregates.sideMatch.attack.numerator", "aggregates.sideMatch.attack.denominator"], itemRefs: [id(s1, 0), id(s2, 0)],
        representative: { kind: "hypothesis", factOrHypothesis: "hypothesis", lane: "side", statement: "分かれ道で攻めの側が選ばれる割合(65 / 107)について、席の読みが分かれている、という読みです。",
          observations: [{ value: 65, unit: "positions", packetRef: NUM() }, { value: 107, unit: "positions", packetRef: DEN() }], counterEvidence: { attempted: true, items: [], result: "none_found" },
          prediction: { window: "次の 25 局", metric: "packet.aggregates.sideMatch.attack.numerator / packet.aggregates.sideMatch.attack.denominator", comparator: ">=", value: 0.6, alsoRequires: [] } } },
      { clusterId: "C-002", packetRefs: ["aggregates.branches.total.value"], itemRefs: [id(s1, 1), id(s2, 1)],
        representative: { kind: "finding", factOrHypothesis: "fact", lane: "fork", statement: "分かれ道の総数は 404 だった。", observations: [{ value: 404, unit: "positions", packetRef: TOTAL() }], counterEvidence: { attempted: true, items: [], result: "none_found" } } },
    ],
    contradictions: [{ clusterIds: ["C-001"], itemRefs: [id(s1, 0), id(s2, 0)], packetRefs: ["aggregates.sideMatch.attack.numerator"], text: "同じ分子と分母から、選ばれやすい・選ばれにくいの逆の読み。" }],
    dropped: [{ itemRef: id(s1, 2), reason: "問いへの答えの行。束にせず answersByQuestion に残す" }, { itemRef: id(s2, 2), reason: "同上" }],
    heldBack: [{ clusterId: "C-002", reason: "総数の写しで、次の対局群で動く数の予測を持たない" }],
    forVerification: ["C-001"],
    answerNotes: [{ questionId: "q1", text: "両席とも束に判定が無いと答えた。" }],
  };
}
function ctxOf(input: Record<string, unknown>) {
  return { input, customerRef: "c5", timeLimitSec: 180, games: 25, today: TODAY, gitHead: "0000000", model: "integrator-test", usage: { inputTokens: 1, outputTokens: 1 }, finishReason: "stop", attempts: 1, requestedAt: "2026-09-30T00:00:00Z" };
}
function full() {
  const { input } = build();
  const output = completeIntegration(llmOf(input), ctxOf(input));
  return { input, output };
}
function problems(output: unknown, input: unknown) {
  return integrationProblems(output, input, { today: TODAY, registry: new Set<string>() });
}

describe("入力の器(校正 1・3)", () => {
  it("封筒 3 つ(1 つは空席)から器を組み、schema を通り、internal はどこにも無い", () => {
    const { input, seatOrder } = build();
    expect(validateIntegrationInput(input)).toEqual([]);
    expect(JSON.stringify(input)).not.toContain("internal");
    expect(JSON.stringify(input)).not.toMatch(/gpt|gemini|claude/);
    expect(seatOrder.map((s) => s.seat).sort()).toEqual(["claude", "gemini", "gpt"]);
    const { itemMap } = build();
    expect(itemMap).toHaveLength(6);
    expect(itemMap.every((m) => /^I-[0-9]+-[0-9]{3}$/.test(m.anonId) && /^H-c5-/.test(m.hypothesisId))).toBe(true);
    const present = (input.seats as { present: boolean; items?: { hypothesisId: string }[]; answers?: { itemIds: string[] }[] }[]).filter((s) => s.present);
    expect(present.every((s) => s.items!.every((it) => it.hypothesisId.startsWith("I-")))).toBe(true);
    expect(present[0]!.answers![0]!.itemIds[0]).toMatch(/^I-/); // answers の参照も匿名 id に
    const absent = (input.seats as { present: boolean; reason?: string }[]).find((s) => !s.present);
    expect(absent?.reason).toBe("reach_failed");
    expect((input.packetDigest as { aggregates: unknown[] }).aggregates).toHaveLength(3);
  });
  it("席の行の写しは許した欄だけ(internal・origin.seat・subject・provenance は落ちる)", () => {
    const item = { hypothesisId: "H-c5-x-001", kind: "finding", lane: "fork", statement: "x", observations: [{ obsId: "packet.a.value", path: "a.value", value: 1, packetRef: { path: "a.value" }, extra: 1 }], counterEvidence: { attempted: true, items: [], result: "none_found", provenance: { inputs: ["x"] } }, internal: { reasoning: "秘" }, origin: { seat: "gpt", itemId: "S-001" }, subject: {}, provenance: {}, status: "proposed" };
    const copy = copySeatItem(item);
    expect(Object.keys(copy).sort()).toEqual(["counterEvidence", "hypothesisId", "kind", "lane", "observations", "origin", "statement"]);
    expect(copy.origin).toEqual({ itemId: "S-001" });
    expect(Object.keys((copy.observations as Record<string, unknown>[])[0]!)).not.toContain("extra");
    expect(Object.keys(copy.counterEvidence as Record<string, unknown>)).not.toContain("provenance");
  });
  it("席の順は runId から決定的(同じ runId なら同じ、違う runId で違う例が在る)", () => {
    expect(seatPermutation(RUN, 3)).toEqual(seatPermutation(RUN, 3));
    const a = build().seatOrder.map((s) => s.seat).join(",");
    const others = ["xyz1", "xyz2", "xyz3", "xyz4", "xyz5", "xyz6"].map((r) => build(`${r}20260930`).seatOrder.map((s) => s.seat).join(","));
    expect(others.some((o) => o !== a)).toBe(true);
    expect(canonicalJson({ b: 1, a: [2, { d: 1, c: 2 }] })).toBe('{"a":[2,{"c":2,"d":1}],"b":1}');
  });
  it("入力に internal を入れると器の schema で落ちる(構造で拒む)", () => {
    const { input } = build();
    ((input.seats as Record<string, unknown>[])[0]!.items as Record<string, unknown>[]);
    const seat = (input.seats as { present: boolean; items?: Record<string, unknown>[] }[]).find((s) => s.present)!;
    seat.items![0]!.internal = { reasoning: "x" };
    expect(validateIntegrationInput(input).some((p) => p.includes("internal"))).toBe(true);
  });
});

describe("出力の器(校正 2)", () => {
  it("整理役が書く形を通り、道具が seatCount・answersByQuestion・run を埋め、I-1〜I-8 を通る", () => {
    const { input, output } = full();
    expect(validateIntegrationLlm(llmOf(input))).toEqual([]);
    expect(problems(output, input)).toEqual([]);
    const clusters = output.clusters as { seatCount: { value: number; evidence: boolean }; representative: { hypothesisId: string; origin: { seat: string } } }[];
    expect(clusters[0]!.seatCount).toEqual({ value: 2, evidence: false });
    expect(clusters[0]!.representative.hypothesisId).toBe("H-c5-integrun2-001");
    expect(clusters[0]!.representative.origin).toEqual({ seat: "integrator" });
    const abq = output.answersByQuestion as { summary: string; bySeat: unknown[]; note?: string }[];
    expect(abq[0]!.summary).toBe("unanswerable");
    expect(abq[0]!.bySeat).toHaveLength(2);
    expect(abq[0]!.note).toBe("両席とも束に判定が無いと答えた。");
    expect((output.selfComputedNumbers as unknown[]).length).toBe(1);
  });
  it("summary は機械で決まる: 1 席でも違えば mixed(多数決で unanswerable を消さない)", () => {
    const { input } = buildIntegrationInput(
      [{ seat: "gpt", envelope: envelopeOf("gpt", "a") }, { seat: "gemini", envelope: envelopeOf("gemini", "b") }, { seat: "claude", envelope: envelopeOf("claude", "c") }],
      { runId: RUN, packet: packet(), request: request(), seatOrderRef: "seat_order.json" },
    );
    const rows = answersByQuestionOf(input) as { summary: string; bySeat: { status: string }[] }[];
    expect(rows[0]!.bySeat.map((b) => b.status).sort()).toEqual(["answered", "unanswerable", "unanswerable"]);
    expect(rows[0]!.summary).toBe("mixed");
  });
  it("同じ入力で 2 回 → 同じ出力", () => {
    const { input } = build();
    expect(completeIntegration(llmOf(input), ctxOf(input))).toEqual(completeIntegration(llmOf(input), ctxOf(input)));
  });
});

describe("変異(それぞれ 1 件だけ赤くなる)", () => {
  type Out = { clusters: Record<string, unknown>[]; dropped: Record<string, unknown>[]; heldBack: Record<string, unknown>[]; forVerification: string[]; contradictions: Record<string, unknown>[]; answersByQuestion: Record<string, unknown>[]; run: Record<string, unknown> };
  it("項目を clusters からも dropped からも落とす → I-1", () => {
    const { input, output } = full();
    (output as Out).dropped.pop();
    const out = problems(output, input);
    expect(out).toHaveLength(1);
    expect(out[0]).toMatch(/^I-1: 入力の項目「.*」が clusters にも dropped にも無い/);
  });
  it("根拠の場所を共有しない項目を束に → I-2(+ その項目が 2 回現れる I-1)", () => {
    const { input, output } = full();
    const c = (output as Out).clusters;
    (c[1]!.itemRefs as unknown[]).push((c[0]!.itemRefs as unknown[])[0]);
    const out = problems(output, input);
    expect(out.filter((p) => p.startsWith("I-2"))).toHaveLength(1);
    expect(out.filter((p) => p.startsWith("I-1"))).toHaveLength(1); // 同じ項目が 2 回
    expect(out.filter((p) => p.startsWith("I-8"))).toHaveLength(1); // 代表の出どころ(成員の列)と itemRefs が食い違う
    expect(out.filter((p) => p.startsWith("I-3"))).toHaveLength(0); // 足したのは同じ席の項目なので seatCount は変わらない(予測はここを外していた ― 記録)
    expect(out).toHaveLength(3);
  });
  it("evidence: true → schema", () => {
    const { input, output } = full();
    ((output as Out).clusters[0]!.seatCount as { evidence: boolean }).evidence = true;
    const out = problems(output, input);
    expect(out).toHaveLength(1);
    expect(out[0]).toMatch(/^schema: .*evidence/);
  });
  it("seatCount.value を +1 → I-3", () => {
    const { input, output } = full();
    ((output as Out).clusters[0]!.seatCount as { value: number }).value = 3;
    expect(problems(output, input)).toEqual(["I-3: C-001 の seatCount.value が 3(成員の席は 2)"]);
  });
  it("束を forVerification から外して heldBack にも置かない → I-3。理由が一致の数を参照 → I-3", () => {
    const { input, output } = full();
    (output as Out).forVerification = [];
    expect(problems(output, input)).toEqual(["I-3: C-001 が forVerification と heldBack のどちらにも無い(外すなら理由つきで heldBack へ)"]);
    (output as Out).heldBack.push({ clusterId: "C-001", reason: "2 席しか一致していない" });
    expect(problems(output, input)).toEqual(["I-3: heldBack[1] の理由が一致の数を参照している(seatCount は理由にしない)"]);
  });
  it("代表の statement に成員に無い数 → I-4(H-1)。代表の観測に成員に無い場所 → I-4", () => {
    const { input, output } = full();
    const rep = (output as Out).clusters[0]!.representative as { statement: string; observations: { packetRef: { path: string }; obsId: string; path: string }[] };
    rep.statement = "割合は 0.7(65 / 107)という読みです。";
    expect(problems(output, input)).toEqual(["I-4: C-001 の representative H-1: statement: 数「0.7」が observations の値に無い"]);
    rep.statement = "分かれ道で攻めの側(65 / 107)という読みです。";
    rep.observations.push({ obsId: "packet.aggregates.branches.total.value", path: "aggregates.branches.total.value", packetRef: { path: "aggregates.branches.total.value" }, ...({ value: 404 } as object) } as never);
    const out = problems(output, input);
    expect(out).toEqual(["I-4: C-001 の representative の観測「aggregates.branches.total.value」が成員の観測に無い(整理役が根拠を足した)"]);
  });
  it("1 席 unanswerable なのに summary を answered → I-5", () => {
    const { input, output } = full();
    ((output as Out).answersByQuestion[0] as { summary: string }).summary = "answered";
    expect(problems(output, input)).toEqual(["I-5: answersByQuestion が席の answers から機械で決まる内訳・summary と違う(多数決で答えを変えない)"]);
  });
  it("隔離欄の数を矛盾の text に → I-6", () => {
    const { input, output } = full();
    ((output as Out).contradictions[0] as { text: string }).text = "率 0.61 で逆の読み。";
    expect(problems(output, input)).toEqual(["I-6: selfComputedNumbers[0] の値「0.61」が代表の文・矛盾・注に出ている"]);
  });
  it("代表に origin.seat: gpt → I-7(席名も鳴る)", () => {
    const { input, output } = full();
    ((output as Out).clusters[0]!.representative as { origin: { seat: string } }).origin.seat = "gpt";
    const out = problems(output, input);
    expect(out.filter((p) => p.startsWith("I-7"))).toHaveLength(2);
    expect(out).toHaveLength(2);
  });
  it("run.inputSha256 を変える → I-8", () => {
    const { input, output } = full();
    (output as Out).run.inputSha256 = "8".repeat(64);
    expect(problems(output, input)).toEqual(["I-8: run.inputSha256 が入力の器の sha と違う(別の入力で得た出力)"]);
  });
  it("整理役が seatCount や answersByQuestion を書いたら整理役が書く形で落ちる", () => {
    const { input } = build();
    const bad = llmOf(input) as Record<string, unknown>;
    bad.answersByQuestion = [];
    expect(validateIntegrationLlm(bad).length).toBeGreaterThan(0);
    expect(() => completeIntegration(bad, ctxOf(input))).toThrow(/整理役が書く形/);
  });
});

describe("packet を読まない(校正 4)", () => {
  it("integration.ts は observationPacket* を import せず、packet のファイルを開かない", () => {
    const src = readFileSync(new URL("./integration.ts", import.meta.url), "utf-8");
    expect(src).not.toMatch(/from "\.\/observation(Packet|Aggregates|Facts|Materials|Provenance)/);
    expect(src).not.toMatch(/readFileSync\([^)]*packet/i);
  });
});
