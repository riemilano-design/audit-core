// 束 R4 の試験 ― 1 席と 1 回の実行(計画 docs/STEP_LLM_SEATS_R4_CALLSEAT_2026-09-30.md §6)。**網に出ない**(fetch は全部差し替え)。
//
// 【要点 1】止まる条件(no_key / no_model / cost_cap / input_limit / reach_failed / schema_failed / http_failed)がそれぞれ**空席**になり、
//   **他の席で埋まらない**(器の席は 3 つのまま・present false・その席の項目は 0 件)。
// 【要点 2】cost_cap は**残りの席も送らない**(生成の入口が 1 度も叩かれない)。上限を越えた費用は発生しない。
// 【要点 3】再試行は計画 §4 のとおり(schema 2 回・途中切れ 1 回で取り置き 1.5 倍・合言葉不一致は再試行しない)。
//   schema の再依頼は**会話にしない** ― 前回の出力を渡さず、落ちた理由だけを足した新しい 1 通。
// 【要点 4】保存物・run_summary に鍵が 1 字も無い。
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { OBSERVATION_PACKET_CONTRACT, OBSERVATION_PACKET_SCHEMA_VERSION, OBSERVATION_REQUEST_CONTRACT, packetIdOf } from "./observationPacket.js";
import { renderSeatInput, type SeatInputMeta } from "./seatInput.js";
import { FIXED_INSTRUCTION_SHA256, RETRY_UNCHANGED_FIELDS_NOTICE, fixedShaProblems, parseHoldBack, runAll, retryUserText, seatsMissingPrices, type RunAllConfig, type SeatConfig } from "./seatRun.js";

const INSTRUCTION = readFileSync(new URL("../../../docs/LLM_SEATS_INSTRUCTION_v1_2026-09-30.md", import.meta.url));
const INTEGRATOR_INSTRUCTION = "あなたは整理役です。席の名前は知りません。";
const RUN_ID = "run20260930abc";
const TODAY = "2026-09-30";
const KEYS = { openai: "sk-test-OPENAIKEYVALUE0000", gemini: "AIza-test-GEMINIKEYVALUE0", anthropic: "sk-ant-test-CLAUDEKEYVAL" };
const PRICES = { gpt: { inPerMillion: 5, outPerMillion: 30 }, gemini: { inPerMillion: 2, outPerMillion: 12, tiers: [{ aboveInputTokens: 200_000, inPerMillion: 4, outPerMillion: 18 }] }, claude: { inPerMillion: 5, outPerMillion: 25 } };

type Rec = Record<string, unknown>;

// ---- 最小の packet / request(隣の束の試験と同じ形) ----
function minimalFacts(): Rec {
  return {
    games: [{ gameId: "g01", no: 1, side: "先手", result: "負け", ending: "投了", ownPlyCount: 62, totalPlyCount: 123, timeLimitSec: 180, mirrored: false, src: "m1" }],
    moves: [{ gameId: "g01", ply: 48, side: "own", usi: "P*4d", piece: "pawn", drop: true, spentSec: 12.5, phase: "mid", isFork: true, tags: ["drop"], collapsed: false, src: "m1" }],
    engine: [{ gameId: "g01", ply: 48, sfen: "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1", scoreCp: 120, top1Usi: "8g8f", actualUsi: "P*4d", candidates: [{ usi: "8g8f", scoreCp: 120, pv: ["8g8f", "3c3d"] }], nodes: 2000, multipv: 5, src: "e1" }],
    time: [{ gameId: "g01", earlySpentSec: 30, midSpentSec: 90, lateSpentSec: 40, longThinkCount: 3, longThinkForkCount: 2, longThinkOppositeCount: 1, remainingSec: 0, timeUpLoss: false, src: "m1" }],
    branches: [{ gameId: "g01", ply: 48, displayPly: 48, top1Usi: "8g8f", actualUsi: "P*4d", top1Side: "attack", actualSide: "defense", top1Tags: ["capture"], actualTags: ["drop"], topGapCp: 80, firstVisibleNodes: 2000, shallowVisible: true, src: "e1", srcFirstVisibleNodes: "e2" }],
    collapse: [{ gameId: "g01", ply: 50, beforeCp: 320, afterCp: -140, bandBefore: "ahead", bandAfter: "level", kind: "drop", src: "m1" }],
    recognition: {
      rows: [{ gameId: "g01", selfSignature: ["onikoroshi"], opponentSignature: ["sansan_kaku_senpo"], signatureClass: "多数の核", names: ["鬼殺し"], selfRecognized: true, opponentRecognized: true, selfStrongRecognized: true, opponentStrongRecognized: false, reviewStatus: "draft", src: "r1" }],
      definitions: [{ id: "onikoroshi", name: "鬼殺し", side: "self", reviewStatus: "draft", recognitionPattern: [{ orderHint: 1, piece: "桂", to: "77" }], src: "r1" }],
    },
  };
}
function minimalAggregates(): Rec[] {
  return [
    // S-3 (e): numeratorWhere を立てる(無いと数え直しが「値の行」として読み、常に合わない。packet が渡って H-9 が
    // 数え直しを回すようになって実測で分かった)。空配列 = 分母と同じ条件(数え直すと分子・分母ともに 1)。
    { id: "side_match.attack", numerator: 1, denominator: 1, unit: "positions", name: "第 1 候補が攻めの手だった分かれ道のうち、実戦も攻めの手だった局面", population: { from: "branches", where: [{ field: "top1Side", op: "==", value: "attack" }], unit: "positions" }, numeratorWhere: [], derivedFrom: ["g01"], src: "e1", recountable: true, timeDependent: false },
    { id: "branches.total", value: 1, unit: "positions", name: "分かれ道の総数", population: { from: "branches", where: [], unit: "positions" }, derivedFrom: ["g01"], src: "e1", recountable: true, timeDependent: false },
  ];
}
function packet(): Rec {
  const facts = minimalFacts();
  const aggregates = minimalAggregates();
  return {
    contract: OBSERVATION_PACKET_CONTRACT, schemaVersion: OBSERVATION_PACKET_SCHEMA_VERSION, packetId: packetIdOf(facts, aggregates), customerRef: "c5", facts, aggregates,
    provenance: {
      pipelineVersion: "0000000", generatedAt: "2026-09-30T00:00:00Z",
      sources: [
        { id: "e1", type: "engine", engineVersion: "(仮)", nodesLimit: 2000, multipv: 5, generatedAt: "2026-09-30T00:00:00Z", inputPaths: ["scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json"] },
        { id: "m1", type: "material", kind: "patient-report-data", gitHead: "0000000", inputPaths: ["scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json"] },
        { id: "r1", type: "recognition", definitionsDirs: ["data/openings"], reviewStatus: "draft", inputPaths: ["scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json"] },
      ],
      inputs: [{ path: "scripts/playtest/out/c5/pipe-3min/report/patient_report_data.json", sha256: "a".repeat(64), bytes: 104857 }],
      thresholds: [{ id: "ahead_cp", value: 300, unit: "centipawns", from: "scripts/playtest/report-pdf/exit_groups.py AHEAD_CP" }],
    },
  };
}
function request(): Rec {
  return { contract: OBSERVATION_REQUEST_CONTRACT, schemaVersion: "0.1", customerRef: "c5", customerQuestions: [{ id: "q1", text: "普段指さない戦型のときに何が変わるか", askedAt: "2026-09-29", via: "relayed" }], requestedScope: { games: 1, timeLimitSec: 180, note: "3 分切れ負け" } };
}
function metaOf(): SeatInputMeta {
  return renderSeatInput({ packet: packet(), request: request(), instruction: INSTRUCTION, runId: RUN_ID }).meta;
}

// ---- 席・整理役が返す形(正本を通る最小) ----
function seatLlm(meta: SeatInputMeta, over: { passphrase?: string } = {}): Rec {
  return {
    reach: { passphrase: over.passphrase ?? meta.passphrase, sections: meta.sections.map((s) => ({ section: s.section, lastKey: s.lastKey, seal: s.seal })) },
    items: [
      {
        itemId: "S-001", kind: "finding", factOrHypothesis: "fact", lane: "side",
        // S-3 (e): seatRun.ts が packet を H-9 へ渡すようになったので、合成の値は packet の実際の値(numerator: 1)に合わせる
        // (packet が無かった頃は H-9 が skip していたため「65」でも緑だった)。
        statement: "第一候補が攻めだった分かれ道のうち、実戦も攻めだった局面は 1 だった。",
        observations: [{ path: "aggregates.side_match.attack.numerator", value: 1, unit: "件", packetRef: { path: "aggregates.side_match.attack.numerator" } }],
        counterEvidence: { attempted: true, items: [], result: "none_found" },
      },
      {
        itemId: "S-002", kind: "hypothesis", factOrHypothesis: "hypothesis", lane: "time",
        statement: "長く考えた局面で崩れが増えている可能性があります。",
        observations: [{ path: "facts.time[0].longThinkCount", value: 3, packetRef: { path: "facts.time[0].longThinkCount" } }],
        counterEvidence: { attempted: true, items: [{ kind: "denominator", text: "分かれ道の総数を分母に見た", observations: [{ value: 1, packetRef: { path: "aggregates.branches.total.value" } }] }], result: "stands" },
        prediction: { window: "次の 20 局", metric: "崩れの件数", comparator: "<=", value: 10, alsoRequires: [] },
        requestRef: { questionId: "q1" },
        internal: { reasoning: "この手は自玉側を固める狙いだったかもしれない(内部だけ)" },
      },
    ],
    answers: [{ questionId: "q1", status: "partial", itemIds: ["S-001", "S-002"], reason: "束に在るのは 1 局の組だけ", missing: [{ what: "普段指す戦型の組", howToMeasure: "同じ人の別の組で同じ認識を回す" }] }],
    selfComputedNumbers: [],
    omissions: [],
  };
}
/**
 * 整理役が返す形。**器の行をそのまま写せない** ― 器の観測は obsId を持ち、代表の観測は packetRef を持つ形(整理役向けの正本)。
 * 整理役の指示文はこの写し替えを明示する(R4 で実測した落ち方: obsId・writtenAt が「知らない欄」で落ちる)。
 */
function representativeObs(obs: Rec): Rec {
  const path = String(obs.path ?? (obs.packetRef as Rec | undefined)?.path ?? "");
  return { path, value: obs.value, ...(obs.unit === undefined ? {} : { unit: obs.unit }), packetRef: { path } };
}
/** 同じ文の行を 1 つの束にする(在る席の全部の項目を拾う ― I-1 は黙って落とすことを許さない) */
function integratorLlm(input: Rec): Rec {
  const seats = (input.seats as Rec[]).filter((s) => s.present === true);
  const groups = new Map<string, Array<{ seatIndex: number; item: Rec }>>();
  for (const seat of seats) {
    for (const item of (seat.items as Rec[]) ?? []) {
      const key = String(item.statement);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push({ seatIndex: Number(seat.seatIndex), item });
    }
  }
  const clusters = [...groups.values()].map((members, i) => {
    const item = members[0]!.item;
    const observations = (item.observations as Rec[]).map(representativeObs);
    const ce = item.counterEvidence as Rec;
    const prediction = item.prediction as Rec | undefined;
    return {
      clusterId: `C-${String(i + 1).padStart(3, "0")}`,
      packetRefs: [String((observations[0]!.packetRef as Rec).path)],
      itemRefs: members.map((m) => ({ seatIndex: m.seatIndex, hypothesisId: String(m.item.hypothesisId) })),
      representative: {
        kind: item.kind, factOrHypothesis: item.factOrHypothesis, lane: item.lane, statement: item.statement, observations,
        counterEvidence: { attempted: ce.attempted, items: (ce.items as Rec[]).map((ci) => ({ kind: ci.kind, text: ci.text, observations: (ci.observations as Rec[]).map(representativeObs) })), result: ce.result },
        ...(prediction === undefined ? {} : { prediction: { window: prediction.window, metric: prediction.metric, comparator: prediction.comparator, value: prediction.value, alsoRequires: prediction.alsoRequires } }),
        ...(item.requestRef === undefined ? {} : { requestRef: item.requestRef }),
      },
    };
  });
  return {
    clusters, contradictions: [], dropped: [], heldBack: [], forVerification: clusters.map((c) => c.clusterId),
    answerNotes: [{ questionId: "q1", text: "束に在るのは短い組だけなので答えられる幅が狭い" }],
  };
}

// ---- 差し替えた fetch(3 社の入口を 1 本で受ける) ----
interface Reply { status: number; body: unknown }
interface CallLog { url: string; body: Rec; role: string }
interface Api {
  fetch: typeof fetch;
  calls: CallLog[];
  urls: string[];
  bodies: Rec[];
  /** 生成の入口(数えの入口を除く)を叩いた回数。role を渡せばその席だけ */
  generateCalls: (role?: string) => number;
  /** その役へ送った user の本文(生成の入口だけ) */
  usersOf: (role: string) => string[];
}
function userTextOf(body: Rec): string {
  if (Array.isArray(body.input)) return String((body.input[1] as Rec | undefined)?.content ?? "");
  if (Array.isArray(body.messages)) return String((body.messages[0] as Rec | undefined)?.content ?? "");
  if (Array.isArray(body.contents)) return String(((body.contents[0] as Rec | undefined)?.parts as Rec[] | undefined)?.[0]?.text ?? "");
  return "";
}
function roleOf(url: string, body: Rec): string {
  if (url.includes("count_tokens") || url.includes(":countTokens")) return "count";
  if (userTextOf(body).includes(`"contract": "integration-input"`)) return "integrator";
  if (url.includes("generativelanguage")) return "gemini";
  return String(body.model ?? "").startsWith("claude") ? "claude" : "gpt";
}
function fakeApi(replies: Record<string, Reply[]>, countTokens = 70_000): Api {
  const calls: CallLog[] = [];
  const urls: string[] = [];
  const bodies: Rec[] = [];
  const used: Record<string, number> = {};
  const fetchImpl = (async (url: string, init: RequestInit) => {
    const body = JSON.parse(String(init.body)) as Rec;
    urls.push(String(url));
    bodies.push(body);
    const role = roleOf(String(url), body);
    calls.push({ url: String(url), body, role });
    if (role === "count") {
      const reply = String(url).includes("count_tokens") ? { input_tokens: countTokens } : { totalTokens: countTokens };
      return { status: 200, ok: true, text: async () => JSON.stringify(reply) } as unknown as Response;
    }
    const queue = replies[role] ?? [];
    const i = used[role] ?? 0;
    used[role] = i + 1;
    const r = queue[Math.min(i, queue.length - 1)] ?? { status: 500, body: { error: `試験に ${role} の返答が無い` } };
    return { status: r.status, ok: r.status < 400, text: async () => JSON.stringify(r.body) } as unknown as Response;
  }) as unknown as typeof fetch;
  return {
    fetch: fetchImpl, calls, urls, bodies,
    generateCalls: (role?: string) => calls.filter((c) => c.role !== "count" && (role === undefined || c.role === role)).length,
    usersOf: (role: string) => calls.filter((c) => c.role === role).map((c) => userTextOf(c.body)),
  };
}
/** tool の名前は強制した名前と同じでなければ取り出さない(違えば JSON 無しとして扱われる) ― 既定は席の名前 */
function anthropicOk(json: unknown, over: Rec = {}, toolName = "submit_seat_output"): Reply {
  return { status: 200, body: { id: "msg_1", model: "claude-opus-5-2026", stop_reason: "tool_use", content: [{ type: "tool_use", name: toolName, input: json }], usage: { input_tokens: 70_000, output_tokens: 5_000 }, ...over } };
}
function integratorOk(json: unknown, over: Rec = {}): Reply {
  return anthropicOk(json, over, "submit_integration");
}
const EMPTY_INTEGRATION = { clusters: [], contradictions: [], dropped: [], heldBack: [], forVerification: [], answerNotes: [] };
function openaiOk(json: unknown, over: Rec = {}): Reply {
  return { status: 200, body: { id: "resp_1", model: "gpt-5.5-2026", status: "completed", output: [{ type: "message", content: [{ type: "output_text", text: JSON.stringify(json) }] }], usage: { input_tokens: 70_000, output_tokens: 5_000 }, ...over } };
}
function geminiOk(json: unknown, over: Rec = {}): Reply {
  return { status: 200, body: { candidates: [{ content: { parts: [{ text: JSON.stringify(json) }] }, finishReason: "STOP" }], usageMetadata: { promptTokenCount: 70_000, candidatesTokenCount: 5_000 }, modelVersion: "gemini-3.1-pro-preview", ...over } };
}

function seats(over: Partial<Record<"gpt" | "gemini" | "claude", Partial<SeatConfig>>> = {}): SeatConfig[] {
  return [
    { seat: "gpt", provider: "openai", model: "gpt-5.5", apiKey: KEYS.openai, prices: PRICES.gpt, reserveOutputTokens: 30_000, temperature: 0, ...over.gpt },
    { seat: "gemini", provider: "gemini", model: "gemini-3.1-pro-preview", apiKey: KEYS.gemini, prices: PRICES.gemini, reserveOutputTokens: 30_000, temperature: 0, ...over.gemini },
    { seat: "claude", provider: "anthropic", model: "claude-opus-5", apiKey: KEYS.anthropic, prices: PRICES.claude, reserveOutputTokens: 30_000, temperature: 0, ...over.claude },
  ];
}
function config(over: Partial<RunAllConfig> = {}): RunAllConfig {
  return {
    runId: RUN_ID, packet: packet(), request: request(), instruction: INSTRUCTION, today: TODAY, gitHead: "0".repeat(40),
    seats: seats(), capUsd: 10,
    integrator: { provider: "anthropic", model: "claude-opus-5", apiKey: KEYS.anthropic, prices: PRICES.claude, reserveOutputTokens: 20_000, temperature: 0, instruction: INTEGRATOR_INSTRUCTION },
    secrets: Object.values(KEYS),
    ...over,
  };
}
const DEPS = { sleep: async () => {}, now: () => new Date("2026-09-30T01:00:00Z") };

async function run(cfg: Partial<RunAllConfig> = {}, replies?: Record<string, Reply[]>): Promise<{ result: Awaited<ReturnType<typeof runAll>>; api: Api }> {
  const meta = metaOf();
  const api = fakeApi(replies ?? {
    gpt: [openaiOk(seatLlm(meta))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))],
    integrator: [integratorOk(EMPTY_INTEGRATION)],
  });
  const result = await runAll(config(cfg), { fetch: api.fetch, ...DEPS });
  return { result, api };
}

describe("1 回の実行が通る(3 席 + 整理役)", () => {
  it("3 席の封筒ができ、契約の検査が 0 件で、器と統合まで進む", async () => {
    const meta = metaOf();
    const api = fakeApi({ gpt: [openaiOk(seatLlm(meta))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))], integrator: [] });
    // 整理役の返答は器の中身から作るので、1 回目の実行で器を得てから組み直す(2 段)
    const first = await runAll(config({ integrator: undefined }), { fetch: api.fetch, ...DEPS });
    expect(first.seats.map((s) => s.present)).toEqual([true, true, true]);
    expect(first.checks.seats.map((c) => c.problems), JSON.stringify(first.checks.seats)).toEqual([[], [], []]);
    const input = first.integrationInput!;
    const api2 = fakeApi({ gpt: [openaiOk(seatLlm(meta))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))], integrator: [integratorOk(integratorLlm(input))] });
    const result = await runAll(config(), { fetch: api2.fetch, ...DEPS });
    expect(result.integration).toBeDefined();
    expect(result.checks.integration?.problems, JSON.stringify(result.checks.integration)).toEqual([]);
    expect((result.integration!.clusters as unknown[]).length).toBe(2);
  });
  it("保存物の名前(計画 §5)", async () => {
    const { result } = await run();
    const names = result.files.map((f) => f.name);
    for (const expected of ["seat_input.md", "seat_input.meta.json", "seat_gpt_attempt_1_raw.json", "seat_gpt.json", "seat_gemini.json", "seat_claude.json", "integration_input.json", "seat_order.json", "checks.json", "run_summary.json"]) {
      expect(names, expected).toContain(expected);
    }
  });
  it("run_summary の形(席ごとの状態・usage・費用・所要・sha)", async () => {
    const { result } = await run();
    const s = result.summary as any;
    expect(s.contract).toBe("llm-seats-run-summary");
    expect(s.runId).toBe(RUN_ID);
    expect(s.seatInput.sha256).toBe(result.meta.seatInputSha256);
    expect(s.seatInput.instructionSha256).toBe(result.meta.instructionSha256);
    expect(s.seats.map((x: any) => x.seat)).toEqual(["gpt", "gemini", "claude"]);
    expect(s.seats[0].usage).toEqual({ inputTokens: 70_000, outputTokens: 5_000 });
    // 5 ドル/100 万 × 7 万 + 30 ドル/100 万 × 5 千 = 0.35 + 0.15
    expect(s.seats[0].actualCostUsd).toBeCloseTo(0.5, 6);
    expect(s.seats[0].items).toBe(2);
    expect(s.totals.seatsPresent).toBe(3);
    expect(s.totals.capReached).toBe(false);
    expect(s.integration.inputSha256).toMatch(/^[0-9a-f]{64}$/);
  });
  it("run_summary は「温度を送ったか」を席ごとに持つ(Anthropic には送らないので false)", async () => {
    const { result } = await run();
    const s = result.summary as any;
    // 3 社とも温度を送らない(gpt-5.5 も claude-opus-5 も受け付けない。Gemini だけに送ると非対称)
    expect(s.seats.map((x: any) => [x.seat, x.temperatureSent])).toEqual([["gpt", false], ["gemini", false], ["claude", false]]);
    expect(s.integration.temperatureSent).toBe(false);
  });
  it("run_summary は席ごとの「有効な形」と、3 席でそろっているかを持つ", async () => {
    const { result } = await run();
    const s = result.summary as any;
    for (const seat of s.seats) expect(seat.valueShape, seat.seat).toEqual(["array", "boolean", "null", "number", "string"]);
    expect(s.totals.valueShapeSame).toBe(true);
  });
  it("席には 1 通だけ送る(会話にしない・他席の出力を渡さない)", async () => {
    const { api } = await run();
    const seatBodies = api.calls.filter((c) => c.role !== "count" && c.role !== "integrator").map((c) => c.body);
    for (const body of seatBodies) {
      if (Array.isArray(body.messages)) expect(body.messages.length).toBe(1);
      if (Array.isArray(body.input)) expect(body.input.length).toBe(2); // system + user
      if (Array.isArray(body.contents)) expect(body.contents.length).toBe(1);
    }
    // 席の入力に他席の出力(封筒の hypothesisId)が混ざっていない
    const seatUsers = seatBodies.map(userTextOf);
    expect(seatUsers.length).toBe(3);
    for (const text of seatUsers) expect(text).toContain("束はここまで");
    for (const text of seatUsers) expect(text).not.toMatch(/H-c5-/);
  });
  it("整理役に送る schema は integration.llm.v0.2(observations の minItems が無い。STEP S-4 §2.1(b))", async () => {
    // 【なぜここで見るか】`loadIntegrationLlmSchema`(seatRun.ts)は非公開の関数で、観測できる場所は
    // 実際に整理役(anthropic)へ送る request body の `tools[0].input_schema` だけ ― Anthropic の写しは
    // 「正本のまま($schema/$id/title/description だけ外す)」なので、minItems の有無がそのまま出る。
    const { api } = await run();
    const integratorBody = api.calls.find((c) => c.role === "integrator")!.body as any;
    const observationsNode = integratorBody.tools[0].input_schema.properties.clusters.items.properties.representative.properties.observations;
    expect(observationsNode.minItems, JSON.stringify(observationsNode)).toBeUndefined();
    expect(observationsNode.type).toBe("array"); // 外した先がそもそも違う欄になっていない
  });
});

describe("空席(止まる条件)は他の席で埋めない", () => {
  it("鍵が無い席は no_key で、生成の入口を叩かない。他の席は回る", async () => {
    const { result, api } = await run({ seats: seats({ gemini: { apiKey: undefined } }) });
    expect(result.seats.map((s) => s.absentReason)).toEqual([undefined, "no_key", undefined]);
    expect(api.urls.some((u) => u.includes("generativelanguage"))).toBe(false);
    expect(api.generateCalls("gemini")).toBe(0);
    expect(result.seats.filter((s) => s.present).length).toBe(2);
  });
  it("鍵が空の字でも no_key(.env の空欄をそのまま渡しても送らない。独立監査の変異 E)", async () => {
    const { result, api } = await run({ seats: seats({ claude: { apiKey: "" } }) });
    expect(result.seats[2]!.absentReason).toBe("no_key");
    expect(api.generateCalls("claude")).toBe(0);
  });
  it("モデル名が無い席は no_model", async () => {
    const { result } = await run({ seats: seats({ gpt: { model: "" } }) });
    expect(result.seats[0]!.absentReason).toBe("no_model");
    expect(result.seats[0]!.present).toBe(false);
  });
  it("器には 3 席が残り、空席は present false・項目 0 件(他席の項目が入らない)", async () => {
    const { result } = await run({ seats: seats({ gemini: { apiKey: undefined }, claude: { model: "" } }) });
    const seatsInInput = result.integrationInput!.seats as Rec[];
    expect(seatsInInput.length).toBe(3);
    expect(seatsInInput.filter((s) => s.present === true).length).toBe(1);
    for (const s of seatsInInput) {
      if (s.present === true) expect((s.items as unknown[]).length).toBe(2);
      else expect(((s.items as unknown[] | undefined) ?? []).length).toBe(0);
    }
    // 対応表は在る席の分だけ(空席の匿名 id を作らない)
    expect(new Set(result.itemMap!.map((r) => r.seatIndex)).size).toBe(1);
  });
  it("合言葉が違えば reach_failed ― 再試行しない(送信は 1 回)", async () => {
    const meta = metaOf();
    const { result, api } = await run({}, {
      gpt: [openaiOk(seatLlm(meta, { passphrase: "ちがう" }))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))],
      integrator: [integratorOk(EMPTY_INTEGRATION)],
    });
    expect(result.seats[0]!.absentReason).toBe("reach_failed");
    expect(result.seats[0]!.attempts.length).toBe(1);
    expect(api.generateCalls("gpt")).toBe(1);
  });
  it("形が 3 回とも合わなければ schema_failed(再依頼は 2 回。前回の出力は渡さず理由だけ足す)", async () => {
    const meta = metaOf();
    const bad = { reach: { passphrase: meta.passphrase, sections: [] }, items: [{ itemId: "わるい形" }], answers: [], selfComputedNumbers: [], omissions: [] };
    const { result, api } = await run({}, {
      gpt: [openaiOk(bad)], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))],
      integrator: [integratorOk(EMPTY_INTEGRATION)],
    });
    expect(result.seats[0]!.absentReason).toBe("schema_failed");
    expect(result.seats[0]!.attempts.map((a) => a.kind)).toEqual(["first", "schema_retry", "schema_retry"]);
    const users = api.usersOf("gpt");
    expect(users.length).toBe(3);
    expect(users[1]).toContain("前回の返答は次の欄で形が合わず受け取れませんでした");
    // 会話にしない = 前回の返答そのもの(JSON)を渡さない。検査が落とした欄と理由だけを足す
    expect(users[1]).not.toContain('"reach"');
    expect(users[1]).not.toContain(JSON.stringify(bad));
    expect(users[2]).toContain("前回の返答は次の欄で");
  });
  it("2 回目で形が合えば席は在る(attempts 2)", async () => {
    const meta = metaOf();
    const bad = { reach: { passphrase: meta.passphrase, sections: [] }, items: [{ itemId: "S-1" }], answers: [], selfComputedNumbers: [], omissions: [] };
    const { result } = await run({}, {
      gpt: [openaiOk(bad), openaiOk(seatLlm(meta))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))],
      integrator: [integratorOk(EMPTY_INTEGRATION)],
    });
    expect(result.seats[0]!.present).toBe(true);
    expect(result.seats[0]!.attempts.length).toBe(2);
    expect((result.summary as any).seats[0].attempts[1].kind).toBe("schema_retry");
  });
  it("途中で切れたら取り置きを 1.5 倍にして 1 回だけ送り直す", async () => {
    const meta = metaOf();
    const cut = openaiOk(seatLlm(meta), { status: "incomplete", incomplete_details: { reason: "max_output_tokens" } });
    const { result, api } = await run({}, {
      gpt: [cut, openaiOk(seatLlm(meta))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))],
      integrator: [integratorOk(EMPTY_INTEGRATION)],
    });
    expect(result.seats[0]!.attempts.map((a) => a.reserveOutputTokens)).toEqual([30_000, 45_000]);
    expect(result.seats[0]!.attempts[1]!.kind).toBe("length_retry");
    expect(result.seats[0]!.present).toBe(true);
    const reserves = api.bodies.filter((b) => Array.isArray(b.input)).map((b) => b.max_output_tokens);
    expect(reserves).toEqual([30_000, 45_000]);
  });
  it("HTTP が続けて失敗すれば http_failed(原文の代わりに理由を残す)", async () => {
    const meta = metaOf();
    const { result } = await run({}, {
      gpt: [{ status: 503, body: { error: "unavailable" } }], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))],
      integrator: [integratorOk(EMPTY_INTEGRATION)],
    });
    expect(result.seats[0]!.absentReason).toBe("http_failed");
    expect(result.seats[0]!.attempts[0]!.httpAttempts).toBe(4);
    expect(result.files.some((f) => f.name === "seat_gpt_attempt_1_error.txt")).toBe(true);
  });
});

describe("費用の上限(送る前に止める。上限は実行単位)", () => {
  it("1 席目で越える見込みなら送らず、残りの席も送らない(2 席目は単体なら収まる額でも送らない)", async () => {
    // 上限 0.6 ドル: gpt の見込み 1.25 / gemini 0.5 / claude 1.1(概算入力 7 万 + 取り置き 3 万)。
    // **gemini は単体なら収まる** ― それでも送らないのが「上限は実行単位」。0.01 のような極端な額では、
    // 席ごとに落ちるだけで「残りも送らない」を測れない(2026-09-30 の変異 M6 が沈黙して分かった)。
    const { result, api } = await run({ capUsd: 0.6 });
    expect(result.seats.map((s) => s.absentReason)).toEqual(["cost_cap", "cost_cap", "cost_cap"]);
    expect(api.generateCalls()).toBe(0);
    expect((result.summary as any).totals.capReached).toBe(true);
    expect((result.summary as any).totals.cumulativeCostUsd).toBe(0);
  });
  it("2 席目までで累計が越えたら 3 席目は送らない(1・2 席目の封筒は残る)", async () => {
    // 1 席 0.5 + 0.26 = 0.76 ドル。上限 1.2 ドルなら 3 席目(0.5)で越える
    const { result, api } = await run({ capUsd: 1.2 });
    expect(result.seats.map((s) => s.present)).toEqual([true, true, false]);
    expect(result.seats[2]!.absentReason).toBe("cost_cap");
    expect(api.generateCalls("claude")).toBe(0);
    expect(result.integrationInput!.seats).toHaveLength(3);
  });
  it("入力上限を越える席は input_limit で送らない(他の席は回る)", async () => {
    const { result, api } = await run({ seats: seats({ claude: { inputLimit: 80_000 } }) });
    expect(result.seats[2]!.absentReason).toBe("input_limit");
    expect(api.generateCalls("claude")).toBe(0);
    expect(result.seats.filter((s) => s.present).length).toBe(2);
  });
  it("Gemini の段: 概算入力が 200k を超える組では高い単価で見積もる(司令塔 2026-09-30)", async () => {
    const meta = metaOf();
    const api = fakeApi({ gpt: [openaiOk(seatLlm(meta))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))] }, 250_000);
    const result = await runAll(config({ integrator: undefined, capUsd: 1.2, seats: [seats()[1]!] }), { fetch: api.fetch, ...DEPS });
    // 高い段 4/18 なら 1.0 + 0.54 = 1.54 ドルで上限 1.2 を越える。下の段 2/12 なら 0.5 + 0.36 = 0.86 で通ってしまう
    expect(result.seats[0]!.absentReason).toBe("cost_cap");
    expect(result.seats[0]!.estimate).toEqual({ inputTokens: 250_000, method: "api" });
    expect(api.generateCalls()).toBe(0);
  });
});

describe("揺れの床の 2 回目(人間の決定 2026-09-30: 上限は実行の累計に掛ける)", () => {
  it("2 回目は 1 回目の累計を引き継ぎ、越える見込みなら 1 通も送らない", async () => {
    // 1 回目で 10 ドル近くまで使った後の 2 回目
    const { result, api } = await run({ capUsd: 10, cumulativeCostUsdBefore: 9.9 });
    expect(result.seats.map((s) => s.absentReason)).toEqual(["cost_cap", "cost_cap", "cost_cap"]);
    expect(api.generateCalls()).toBe(0);
    expect((result.summary as any).cumulativeCostUsdBefore).toBe(9.9);
  });
  it("余裕があれば 2 回目も回り、累計は 1 回目の分を足して記録する", async () => {
    const { result } = await run({ capUsd: 10, cumulativeCostUsdBefore: 2 });
    expect(result.seats.map((s) => s.present)).toEqual([true, true, true]);
    // 1 回目の 2 ドル + この回の 3 席(0.5 + 0.2 + 0.475)+ 整理役(0.475)
    expect((result.summary as any).totals.cumulativeCostUsd).toBeGreaterThan(2);
    expect((result.summary as any).totals.cumulativeCostUsd).toBeLessThan(10);
  });
});

describe("整理役", () => {
  it("整理役が失敗しても席の封筒・器・run_summary は残る(統合は後から回し直せる)", async () => {
    const meta = metaOf();
    const { result } = await run({}, {
      gpt: [openaiOk(seatLlm(meta))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))],
      integrator: [{ status: 500, body: { error: "boom" } }],
    });
    expect(result.integration).toBeUndefined();
    expect(result.integrator!.absentReason).toBe("http_failed");
    expect(result.seats.filter((s) => s.present).length).toBe(3);
    expect(result.files.map((f) => f.name)).toContain("integration_input.json");
    expect(result.files.map((f) => f.name)).toContain("run_summary.json");
    expect((result.summary as any).integration.present).toBe(false);
  });
  it("整理役に渡すのは器だけ(席の名前を渡さない)", async () => {
    const { api } = await run();
    const integratorUser = api.usersOf("integrator")[0];
    expect(integratorUser).toBeDefined();
    expect(integratorUser).not.toMatch(/\bgpt\b|gemini|claude|openai|anthropic/i);
  });
});

describe("鍵が保存物に出ない", () => {
  it("応答が鍵を echo しても、保存物・run_summary・器のどこにも出ない", async () => {
    const meta = metaOf();
    const { result } = await run({}, {
      gpt: [{ status: 401, body: { error: { message: `bad key ${KEYS.openai}` } } }],
      gemini: [geminiOk(seatLlm(meta), { note: `x ${KEYS.gemini}` })],
      claude: [anthropicOk(seatLlm(meta))],
      integrator: [integratorOk(EMPTY_INTEGRATION)],
    });
    const all = result.files.map((f) => f.content).join("\n");
    for (const key of Object.values(KEYS)) expect(all).not.toContain(key);
    expect(all).toContain("[redacted]");
    expect(JSON.stringify(result.summary)).not.toContain(KEYS.openai);
  });
});

describe("再依頼の文", () => {
  it("落ちた理由だけを足し、前回の出力は入れない", () => {
    const text = retryUserText("束の本文", ["items[0]: itemId が形と違う", "answers が空"]);
    expect(text.startsWith("束の本文")).toBe(true);
    expect(text).toContain("- items[0]: itemId が形と違う");
    expect(text).toContain("前回の返答そのものは渡していません");
  });
  it("r1(STEP S-4 §2.1(c2)): 落ちた欄以外は変えないでほしい、の固定の 1 文が、累積した理由の一覧の前に入る", () => {
    const text = retryUserText("束の本文", ["items[0]: itemId が形と違う", "answers が空"]);
    expect(text).toContain(RETRY_UNCHANGED_FIELDS_NOTICE);
    // **一覧の前**(理由の 1 件目より前に出る)
    expect(text.indexOf(RETRY_UNCHANGED_FIELDS_NOTICE)).toBeLessThan(text.indexOf("- items[0]: itemId が形と違う"));
    // 字で固定(1 字変われば赤くなる)
    expect(RETRY_UNCHANGED_FIELDS_NOTICE).toBe(
      "落ちた欄以外は形が合っていました。直すのはここに挙げた欄だけで、他の欄の形・鍵の名前・配列の形は変えないでください。余計な鍵を足さない・配列を文字列にしない。",
    );
  });
});

describe("固定した指示文の sha(司令塔 2026-09-30)", () => {
  // 【なぜ試験にするか】「同じ版名で中身を差し替えない」は約束では守れない。**1 バイト変えたらここが赤くなる**ことで守る。
  it("表の sha が実物のファイルと一致する", () => {
    for (const [basename, sha] of Object.entries(FIXED_INSTRUCTION_SHA256)) {
      const content = readFileSync(new URL(`../../../docs/${basename}`, import.meta.url));
      expect(fixedShaProblems(basename, content), `${basename} → ${sha.slice(0, 8)}`).toEqual([]);
    }
  });
  it("1 バイト変えれば落ちる(版名を上げる合図)", () => {
    const basename = "LLM_SEATS_INSTRUCTION_v1.1_2026-09-30.md";
    const content = readFileSync(new URL(`../../../docs/${basename}`, import.meta.url), "utf-8");
    const problems = fixedShaProblems(basename, `${content} `);
    expect(problems.length).toBe(1);
    expect(problems[0]).toContain("版名を上げる");
  });
  it("表に無い指示文は配らない(固定していない文で席に聞かない)", () => {
    const problems = fixedShaProblems("LLM_SEATS_INSTRUCTION_v9_2027-01-01.md", "なんでも");
    expect(problems.length).toBe(1);
    expect(problems[0]).toContain("固定されていない");
  });
  it("7 本(席 v1・v1.1・v1.2・v1.3・v1.4・**v1.5**・整理役 v1)が表に在る", () => {
    expect(Object.keys(FIXED_INSTRUCTION_SHA256).length).toBe(7);
    // 古い版を消さない ― v1.1 で回した 3 周と比べられるようにする(版名を上げても前の sha は残す)
    expect(Object.keys(FIXED_INSTRUCTION_SHA256)).toContain("LLM_SEATS_INSTRUCTION_v1.1_2026-09-30.md");
    expect(Object.keys(FIXED_INSTRUCTION_SHA256)).toContain("LLM_SEATS_INSTRUCTION_v1.2_2026-10-01.md");
    // S-3(2026-10-06): 埋め草禁止・配列はそのまま配列で写す の 2 文を足した v1.3
    expect(Object.keys(FIXED_INSTRUCTION_SHA256)).toContain("LLM_SEATS_INSTRUCTION_v1.3_2026-10-06.md");
    // S-4(2026-10-06 §2.1(c1)): observations 0 件の書き方・itemId の形・最上位の鍵は 5 つだけ の 4 ブロックを変えた v1.4
    expect(Object.keys(FIXED_INSTRUCTION_SHA256)).toContain("LLM_SEATS_INSTRUCTION_v1.4_2026-10-06.md");
    // S-6(2026-10-07 (c)): 局を符号で呼ぶときは gameId を観測に引く、の 1 ブロックを足した v1.5
    expect(Object.keys(FIXED_INSTRUCTION_SHA256)).toContain("LLM_SEATS_INSTRUCTION_v1.5_2026-10-07.md");
  });
  it("v1.4 は v1.3 と 4 ブロックだけ違う(STEP S-4 §2.1(c1)。それ以外は 1 バイトも変えていない)", () => {
    const v13 = readFileSync(new URL("../../../docs/LLM_SEATS_INSTRUCTION_v1.3_2026-10-06.md", import.meta.url), "utf-8").split("\n");
    const v14 = readFileSync(new URL("../../../docs/LLM_SEATS_INSTRUCTION_v1.4_2026-10-06.md", import.meta.url), "utf-8").split("\n");
    // 同じ行数(足したのは既存行の後ろへの挿入。削った行は無い)
    expect(v14.length).toBe(v13.length + 2);
    // (1) 版名の行(1 行目)
    expect(v13[0]).toContain("指示文 v1.3");
    expect(v14[0]).toContain("指示文 v1.4");
    expect(v14[0]).toBe(v13[0]!.replace("v1.3", "v1.4"));
    // (2) 21 行目(埋め草禁止の行)の末尾の文を置き換えた
    expect(v13[20]).toContain("根拠が束に無い項目は `kind` を `unanswerable` にして `neededObservation` を書く。");
    expect(v14[20]).toContain("根拠が束に無い項目は `kind` を `unanswerable` か `needed_observation` にし");
    expect(v14[20]).toContain("それ以外の `kind` の項目は `observations` を 1 件以上写す。");
    // (3)(4) 22 行目(配列の行)はそのまま、その後ろに 2 行足した
    expect(v14[21]).toBe(v13[21]);
    expect(v14[22]).toContain("itemId");
    expect(v14[22]).toContain("S-001");
    expect(v14[23]).toContain("items2");
    expect(v14[23]).toContain("5 つだけ");
    // 以降(24 行目〜末尾)は v1.3 の 22 行目〜末尾とそのまま同じ(新しい行の後ろで 1 バイトもずれていない)
    expect(v14.slice(24)).toEqual(v13.slice(22));
    // 冒頭(1〜22 行目)は、版名の行(0)と置き換えた行(20)以外は全部一致
    // (21 行目(index 21)は既に上で比べた。22 行目より後ろは挿入で位置がずれるので、上の slice 比較に任せる)
    const changedLines = new Set([0, 20]);
    for (let i = 0; i < 22; i += 1) {
      if (changedLines.has(i)) continue;
      expect(v14[i], `行 ${i + 1}`).toBe(v13[i]);
    }
  });
  it("v1.5 は v1.4 と版名の行 + 1 ブロックだけ違う(STEP S-6 (c)。それ以外は 1 バイトも変えていない)", () => {
    const v14 = readFileSync(new URL("../../../docs/LLM_SEATS_INSTRUCTION_v1.4_2026-10-06.md", import.meta.url), "utf-8").split("\n");
    const v15 = readFileSync(new URL("../../../docs/LLM_SEATS_INSTRUCTION_v1.5_2026-10-07.md", import.meta.url), "utf-8").split("\n");
    // 足したのは既存行の後ろへの挿入 1 行だけ(削った行は無い)
    expect(v15.length).toBe(v14.length + 1);
    // (1) 版名の行(1 行目)
    expect(v14[0]).toContain("指示文 v1.4");
    expect(v15[0]).toContain("指示文 v1.5");
    expect(v15[0]).toBe(v14[0]!.replace("v1.4", "v1.5"));
    // (2) 22 行目(index 21)に新しいブロックを挿入した(局の符号を観測に引く)
    expect(v15[21]).toContain("facts.recognition.rows[n].gameId");
    expect(v15[21]).toContain("H-1");
    expect(v15[21]).toContain("埋め草を写さない");
    // (3) 以降(23 行目〜末尾、index 22〜)は v1.4 の 22 行目〜末尾(index 21〜)とそのまま同じ(新しい行の後ろで 1 バイトもずれていない)
    expect(v15.slice(22)).toEqual(v14.slice(21));
    // 冒頭(1〜21 行目、index 0〜20)は版名の行(index 0)以外は全部一致
    for (let i = 1; i < 21; i += 1) {
      expect(v15[i], `行 ${i + 1}`).toBe(v14[i]);
    }
  });
});

// 人の判断で**送らなかった席**(2026-10-01 の人間の決定: Gemini は無料枠のままなので回さない)。
// 「断られた空席」と同じ語にすると、席が立たなかった理由が読めなくなる ― 語と数の両方で分ける。
describe("送っていない席(人の判断。断られた空席と区別する)", () => {
  const HOLD = { reason: "無料枠・人間の判断で保留" };
  it("held_back の席はその社の入口を叩かず、実費 0・試行 0・理由が記録に残る(他の席は回る)", async () => {
    const { result, api } = await run({ seats: seats({ gemini: { holdBack: HOLD } }) });
    expect(result.seats.map((s) => s.absentReason)).toEqual([undefined, "held_back", undefined]);
    expect(api.urls.some((u) => u.includes("generativelanguage"))).toBe(false);
    expect(api.generateCalls("gemini")).toBe(0);
    const held = result.seats[1]!;
    expect(held.present).toBe(false);
    expect(held.attempts).toEqual([]);
    expect(held.actualCostUsd).toBe(0);
    expect(held.estimatedCostUsd).toBe(0);
    expect(held.absentNote).toContain("無料枠・人間の判断で保留");
    expect(result.seats.filter((s) => s.present).length).toBe(2);
  });
  it("同じ実行の中で「送っていない」と「断られた」が別の語になる", async () => {
    const meta = metaOf();
    const { result } = await run({ seats: seats({ gemini: { holdBack: HOLD } }) }, {
      gpt: [{ status: 500, body: { error: "こちらの都合で落ちた" } }],
      claude: [anthropicOk(seatLlm(meta))], integrator: [integratorOk(EMPTY_INTEGRATION)],
    });
    expect(result.seats[0]!.absentReason).toBe("http_failed");
    expect(result.seats[1]!.absentReason).toBe("held_back");
    expect(result.seats[0]!.absentReason).not.toBe(result.seats[1]!.absentReason);
    // 断られた席は試行が残る / 送っていない席は残らない(数でも分かる)
    expect(result.seats[0]!.attempts.length).toBeGreaterThan(0);
    expect(result.seats[1]!.attempts.length).toBe(0);
  });
  it("到達の比較の分母は送った席だけ(seatsSent 2・seatsHeldBack に名前)", async () => {
    const { result } = await run({ seats: seats({ gemini: { holdBack: HOLD } }) });
    const totals = (result.summary as any).totals;
    expect(totals.seatsSent).toBe(2);
    expect(totals.seatsHeldBack).toEqual(["gemini"]);
    expect(totals.seatsPresent).toBe(2);
    // 席の数(3)とは別の数であること ― 3 のままなら分母が送っていない席を含んでいる
    expect(totals.seatsSent).not.toBe(result.seats.length);
    expect(totals.valueShapeSame).toBe(true);
  });
  it("送った席が 1 つなら valueShapeSame は null(1 席で「形がそろっている」と読ませない)", async () => {
    const { result } = await run({ seats: seats({ gemini: { holdBack: HOLD }, claude: { holdBack: HOLD } }) });
    const totals = (result.summary as any).totals;
    expect(totals.valueShapeSame).toBe(null);
    expect(totals.seatsSent).toBe(1);
    expect(totals.seatsHeldBack).toEqual(["gemini", "claude"]);
  });
  it("全席を保留にしたら送った席 0・valueShapeSame は null(独立監査の指摘の境界)", async () => {
    const { result, api } = await run({ integrator: undefined, seats: seats({ gpt: { holdBack: HOLD }, gemini: { holdBack: HOLD }, claude: { holdBack: HOLD } }) });
    expect(api.generateCalls()).toBe(0);
    const totals = (result.summary as any).totals;
    expect(totals.seatsSent).toBe(0);
    expect(totals.seatsPresent).toBe(0);
    expect(totals.valueShapeSame).toBe(null);
    expect(totals.capReached).toBe(false);
    expect(result.seats.map((s) => s.absentReason)).toEqual(["held_back", "held_back", "held_back"]);
  });
  it("上限の判定より前に処理する ― 上限に当たった実行でも held_back は cost_cap にならない", async () => {
    const { result, api } = await run({ capUsd: 0.6, seats: seats({ gemini: { holdBack: HOLD } }) });
    expect(result.seats.map((s) => s.absentReason)).toEqual(["cost_cap", "held_back", "cost_cap"]);
    expect(api.generateCalls()).toBe(0);
    expect((result.summary as any).totals.capReached).toBe(true);
  });
  it("器に残る理由も held_back(整理役が「送っていない席」と読める)", async () => {
    const { result } = await run({ seats: seats({ gemini: { holdBack: HOLD } }) });
    const inInput = (result.integrationInput!.seats as Rec[]);
    expect(inInput.length).toBe(3);
    const absent = inInput.filter((s) => s.present !== true);
    expect(absent.length).toBe(1);
    expect(String(absent[0]!.reason)).toContain("held_back");
    expect(String(absent[0]!.reason)).toContain("無料枠・人間の判断で保留");
  });
});

describe("--hold-back-seat の読み方(parseHoldBack)", () => {
  const NAMES = ["gpt", "gemini", "claude"];
  it("名前と理由が揃えばその席だけを保留にする", () => {
    const held = parseHoldBack(["node", "x", "--hold-back-seat", "gemini", "--hold-back-reason", "無料枠・人間の判断で保留"], NAMES);
    expect([...held.keys()]).toEqual(["gemini"]);
    expect(held.get("gemini")).toEqual({ reason: "無料枠・人間の判断で保留" });
  });
  it("2 席でもカンマで読める", () => {
    const held = parseHoldBack(["--hold-back-seat", "gemini,gpt", "--hold-back-reason", "理由"], NAMES);
    expect([...held.keys()]).toEqual(["gemini", "gpt"]);
  });
  it("指定が無ければ空(既定は全席に送る)", () => {
    expect(parseHoldBack(["node", "x"], NAMES).size).toBe(0);
  });
  it("知らない名前は投げる ― 綴り違いで「送らないはずの席」に送らせない", () => {
    expect(() => parseHoldBack(["--hold-back-seat", "gemni", "--hold-back-reason", "理由"], NAMES)).toThrow(/知らない席の名前/);
    // 片方だけ合っていても投げる(合っている方だけ保留にして進めない)
    expect(() => parseHoldBack(["--hold-back-seat", "gemini,claud", "--hold-back-reason", "理由"], NAMES)).toThrow(/claud/);
  });
  it("理由が無い・空ならば投げる(理由の無い「送っていない」は記録として読めない)", () => {
    expect(() => parseHoldBack(["--hold-back-seat", "gemini"], NAMES)).toThrow(/--hold-back-reason/);
    expect(() => parseHoldBack(["--hold-back-seat", "gemini", "--hold-back-reason", "   "], NAMES)).toThrow(/--hold-back-reason/);
    // 次の旗を理由と読み違えない
    expect(() => parseHoldBack(["--hold-back-seat", "gemini", "--hold-back-reason", "--runs"], NAMES)).toThrow(/--hold-back-reason/);
  });
});

describe("単価が無い席の洗い出し(seatsMissingPrices)", () => {
  const ok = { inPerMillion: 5, outPerMillion: 30 };
  const none = { inPerMillion: 0, outPerMillion: 0 };
  it("送る席の単価が無ければ名前を返す(費用が 0 に見えて上限が効かない)", () => {
    expect(seatsMissingPrices([{ seat: "gpt", prices: ok }, { seat: "claude", prices: none }])).toEqual(["claude"]);
    // 片側だけ欠けていても返す
    expect(seatsMissingPrices([{ seat: "gpt", prices: { inPerMillion: 5, outPerMillion: 0 } }])).toEqual(["gpt"]);
  });
  it("**送らない席**の単価が無くても返さない(保留の指定が「実行できない」に化けない)", () => {
    expect(seatsMissingPrices([{ seat: "gemini", prices: none, holdBack: { reason: "無料枠・人間の判断で保留" } }, { seat: "gpt", prices: ok }])).toEqual([]);
  });
});

// 2026-10-01 の実測: 形が 3 回とも合わず **2.77 ドル**を使った席は、毎回**違う**理由で落ちていた
//(必須の欄が無い → 知らない欄を作った → また必須の欄が無い)。再依頼が**直前の理由だけ**を渡していたため、
// 席は「言われた所を直し、前に言われた所を壊す」往復をした。
describe("再依頼は理由をためて渡す(前回の出力は渡さない)", () => {
  function brokenThen(meta: SeatInputMeta): Reply[] {
    const first = seatLlm(meta); delete (first as Rec).answers;                       // 1 回目: answers が無い
    const second = seatLlm(meta); (second as Rec).items2 = [];                        // 2 回目: 知らない欄
    return [anthropicOk(first), anthropicOk(second), anthropicOk(seatLlm(meta))];     // 3 回目: 通る
  }
  it("2 回目の再依頼の文に、1 回目の理由も残っている", async () => {
    const meta = metaOf();
    const { result, api } = await run({ seats: [seats()[2]!], integrator: undefined }, { claude: brokenThen(meta) });
    expect(result.seats[0]!.present).toBe(true);
    const users = api.usersOf("claude");
    expect(users.length).toBe(3);
    // **理由の所だけを見る。** 束の本文には指示文が入っていて「answers」も「必須」も出てくるので、
    // 送った字の全体で探すと、理由を渡していなくても緑になる(2026-10-01 に変異 S7 が黙って分かった)。
    const reasonsOf = (text: string): string => {
      const at = text.indexOf("前回の返答は次の欄で形が合わず");
      return at < 0 ? "" : text.slice(at);
    };
    expect(reasonsOf(users[0]!)).toBe("");                       // 1 回目は理由が無い
    expect(reasonsOf(users[1]!)).toContain("「answers」");          // 2 回目は 1 回目の理由
    expect(reasonsOf(users[1]!)).not.toContain("items2");
    // **3 回目は 1 回目と 2 回目の理由を両方持つ**(ここが直した所)
    expect(reasonsOf(users[2]!)).toContain("「answers」");
    expect(reasonsOf(users[2]!)).toContain("items2");
    // 前回の出力そのものは渡さない(席が自分の誤りを土台にすると周の独立が壊れる)
    expect(users[2]!).toContain("前回の返答そのものは渡していません");
    expect(users[2]!).not.toContain("S-001");
  });
  it("落ちた試行の**指摘の本文**が成果物に残る(件数だけで終わらない)", async () => {
    const meta = metaOf();
    const { result } = await run({ seats: [seats()[2]!], integrator: undefined }, { claude: brokenThen(meta) });
    const names = result.files.map((f) => f.name);
    expect(names).toContain("seat_claude_attempt_1_problems.txt");
    expect(names).toContain("seat_claude_attempt_2_problems.txt");
    // 通った試行には指摘のファイルが無い
    expect(names).not.toContain("seat_claude_attempt_3_problems.txt");
    const first = result.files.find((f) => f.name === "seat_claude_attempt_1_problems.txt")!.content;
    expect(first).toContain("answers");
    const second = result.files.find((f) => f.name === "seat_claude_attempt_2_problems.txt")!.content;
    expect(second).toContain("items2");
    // **どの試行で何が落ちたかが読める** ― 1 回目のファイルに 2 回目の理由は無く、
    // 2 回目のファイルに 1 回目の理由も混ざらない(ためた理由を全部書くと、どこで何が起きたか読めなくなる)
    expect(first).not.toContain("items2");
    expect(second).not.toContain("「answers」");
    expect(first).toContain("「answers」");
  });
});

// ---- S-3 (e): runAll が seatOutputProblems・integrationProblems に cfg.packet を渡すようになった ----
//
// 【何を見るか】packet を渡す前は H-9(packetRef の実在と値の一致)が `packet が渡されていない` で skip され、
// 緑のまま黙っていた(観測の値が packet と違っても検査に出なかった)。この試験は、その配線が効いていることを
// **checks.json(E-3・I-4)に H-9 の行が出ること**で見る(合成の封筒・合成 packet。LLM は fake)。
describe("S-3 (e): packet を H-9 へ渡す", () => {
  it("観測の値が packet と違う席だけ、checks.seats の E-3 に H-9 の行が出る(他の席は出ない)", async () => {
    const meta = metaOf();
    const bad = seatLlm(meta);
    // S-001 の観測をわざと packet の実際の値(1)と違う値にする(VM = value mismatch)
    (bad.items as Rec[])[0]!.observations = [
      { path: "aggregates.side_match.attack.numerator", value: 999, unit: "件", packetRef: { path: "aggregates.side_match.attack.numerator" } },
    ];
    const api = fakeApi({
      gpt: [openaiOk(bad)], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))],
      integrator: [],
    });
    const result = await runAll(config({ integrator: undefined }), { fetch: api.fetch, ...DEPS });
    const gptProblems = result.checks.seats.find((c) => c.seat === "gpt")!.problems;
    expect(gptProblems.some((p) => p.includes("H-9")), JSON.stringify(gptProblems)).toBe(true);
    // packet と合っている席は H-9 で落ちない
    expect(result.checks.seats.find((c) => c.seat === "gemini")!.problems).toEqual([]);
    expect(result.checks.seats.find((c) => c.seat === "claude")!.problems).toEqual([]);
  });

  it("I-4(統合)にも packet が渡り、代表の観測が packet と違えば H-9 の行が出る", async () => {
    const meta = metaOf();
    const api1 = fakeApi({ gpt: [openaiOk(seatLlm(meta))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))], integrator: [] });
    const first = await runAll(config({ integrator: undefined }), { fetch: api1.fetch, ...DEPS });
    const input = first.integrationInput!;
    // 整理役の代表の観測をわざと packet と違う値にする(クラスタ 1 件目の最初の観測)
    const integration = integratorLlm(input);
    const rep = (integration.clusters as Rec[])[0]!.representative as Rec;
    (rep.observations as Rec[])[0]!.value = 999;
    const api2 = fakeApi({ gpt: [openaiOk(seatLlm(meta))], gemini: [geminiOk(seatLlm(meta))], claude: [anthropicOk(seatLlm(meta))], integrator: [integratorOk(integration)] });
    const result = await runAll(config(), { fetch: api2.fetch, ...DEPS });
    const problems = result.checks.integration?.problems ?? [];
    expect(problems.some((p) => p.includes("H-9")), JSON.stringify(problems)).toBe(true);
  });
});
