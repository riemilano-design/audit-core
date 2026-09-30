// 束 R2 の試験(計画 docs/STEP_LLM_SEATS_R2_CONTRACT_2026-09-30.md §6)。
//
// 【要点】「通った」は証拠にならない ― 変異 9 本がそれぞれ 1 件だけ赤くなることを見る。**packet を読まない**(import の一覧を試験が見る)。
// 【契約 v0.4 の分岐】H-2(packet. は文法)・H-4(kind で予測の要否)・H-5(fact は読みの語を混ぜない)を、席の行で見る。
import { readFileSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { validateHypothesisLine } from "./hypothesis.js";
import type { SeatInputMeta } from "./seatInput.js";
import { SEAT_INPUT_PROVENANCE_PREFIX, completeSeatOutput, seatOutputProblems, validateSeatOutputEnvelope, validateSeatOutputLlm } from "./seatOutput.js";

const SHA_IN = "9".repeat(64);
const SHA_INS = "3".repeat(64);
const TODAY = "2026-09-30";
const REGISTRY = new Set<string>(["obs.time.bySpent"]);

function meta(): SeatInputMeta {
  return {
    schemaVersion: "0.1", runId: "run20260930abc", passphrase: "run20260", packetId: "22aee8fe696d0262", customerRef: "c5", timeLimitSec: 180, games: 25,
    instructionSha256: SHA_INS, seatInputSha256: SHA_IN, bytes: 10, chars: 10, tokenEstimate: { value: 4, method: "chars/3" },
    sections: [
      { section: "A", title: "顧客の問い", packetPath: "request.customerQuestions[]", rows: 1, lastKey: "q1 普段指さない" },
      { section: "1", title: "局", packetPath: "facts.games[]", rows: 25, lastKey: "g25 25" },
      { section: "2", title: "集計", packetPath: "aggregates.<id>.numerator|denominator|value", rows: 37, lastKey: "aggregates.branches.total.value 値" },
    ],
    headingSections: ["0", "0.1", "0.2"], omitted: [], notIncluded: [],
  };
}
function request() {
  return { contract: "observation-request", schemaVersion: "0.1", customerRef: "c5", customerQuestions: [{ id: "q1", text: "普段指さない戦型の影響", via: "relayed" }], requestedScope: { games: 25, timeLimitSec: 180 } };
}
/** 毎回新しい object(共有すると変異の試験が互いに漏れる ― 2026-09-30 に踏んだ) */
const NUM = (): { path: string } => ({ path: "aggregates.sideMatch.attack.numerator" });
const DEN = (): { path: string } => ({ path: "aggregates.sideMatch.attack.denominator" });
function llm() {
  return {
    reach: { passphrase: "run20260", sections: [{ section: "A", lastKey: "q1" }, { section: "1", lastKey: "g25 25" }, { section: "2", lastKey: "aggregates.branches.total.value" }] },
    items: [
      {
        itemId: "S-001", kind: "finding", factOrHypothesis: "fact", lane: "side",
        statement: "第一候補が攻めだった分かれ道 107 のうち、実戦も攻めだった局面は 65 だった。",
        observations: [{ value: 65, unit: "positions", packetRef: NUM() }, { value: 107, unit: "positions", packetRef: DEN() }],
        counterEvidence: { attempted: true, items: [], result: "none_found" },
        internal: { reasoning: "攻めの側に固定されているかは 0.61 では言えない(自分で割った)", namesOutsideVocabulary: [] },
      },
      {
        itemId: "S-002", kind: "hypothesis", factOrHypothesis: "hypothesis", lane: "side",
        statement: "分かれ道で攻めの側が選ばれやすい(65 / 107)という読みです。",
        observations: [{ value: 65, unit: "positions", packetRef: NUM(), derived: { kind: "percent", numerator: { path: "aggregates.sideMatch.attack.numerator", value: 65 }, denominator: { path: "aggregates.sideMatch.attack.denominator", value: 107 } } }, { value: 107, unit: "positions", packetRef: DEN() }],
        counterEvidence: { attempted: true, items: [{ kind: "denominator", text: "分母 107 は第一候補が攻めの局面だけで、自玉側の分かれ道は含まない。", observations: [{ value: 107, packetRef: DEN() }] }], result: "weakened" },
        prediction: { window: "次の 25 局", metric: "packet.aggregates.sideMatch.attack.numerator / packet.aggregates.sideMatch.attack.denominator", comparator: ">=", value: 0.6, alsoRequires: [] },
      },
      {
        itemId: "S-003", kind: "unanswerable", factOrHypothesis: "fact", lane: "shape", requestRef: { questionId: "q1" },
        statement: "局ごとの型を分ける承認済みの判定が束に無いため、この問いには答えられない。",
        observations: [{ value: "draft", packetRef: { path: "facts.recognition.rows[0].reviewStatus" } }],
        counterEvidence: { attempted: true, items: [], result: "none_found" },
        neededObservation: { what: "局ごとの型の判定(承認済み)", whyNotInPacket: "定義が下書き", howToMeasure: "定義を承認してから局ごとに判定し直す" },
      },
    ],
    answers: [{ questionId: "q1", status: "unanswerable", itemIds: ["S-003"], reason: "束に判定が無い", missing: [{ what: "局ごとの型の判定", howToMeasure: "承認済みの定義で判定し直す" }] }],
    selfComputedNumbers: [{ value: 0.61, how: "65 / 107 を割った", fromPaths: ["aggregates.sideMatch.attack.numerator", "aggregates.sideMatch.attack.denominator"] }],
    omissions: [],
  };
}
function ctx() {
  return { runId: "run20260930abc", seat: "gpt" as const, model: "gpt-test", meta: meta(), today: TODAY, gitHead: "0000000", usage: { inputTokens: 1, outputTokens: 1 }, finishReason: "stop", attempts: 1, requestedAt: "2026-09-30T00:00:00Z" };
}
function envelope() {
  return completeSeatOutput(llm(), ctx());
}
function problems(env: unknown) {
  return seatOutputProblems(env, { meta: meta(), request: request(), today: TODAY, registry: REGISTRY });
}

describe("席が書く形 → 封筒(completeSeatOutput は決定的で数を作らない)", () => {
  it("席が書く形の schema を通り、封筒の schema も通る", () => {
    expect(validateSeatOutputLlm(llm())).toEqual([]);
    expect(validateSeatOutputEnvelope(envelope())).toEqual([]);
  });
  it("道具が埋める欄: id の写し替え・obsId・writtenAt・provenance・subject", () => {
    const env = envelope() as { items: Record<string, unknown>[]; answers: { itemIds: string[] }[] };
    expect(env.items.map((i) => i.hypothesisId)).toEqual(["H-c5-gptrun2-001", "H-c5-gptrun2-002", "H-c5-gptrun2-003"]);
    expect(env.answers[0]!.itemIds).toEqual(["H-c5-gptrun2-003"]);
    expect((env.items[0]!.origin as { itemId: string }).itemId).toBe("S-001");
    expect((env.items[0]!.observations as { obsId: string; path: string }[])[0]).toMatchObject({ obsId: "packet.aggregates.sideMatch.attack.numerator", path: "aggregates.sideMatch.attack.numerator" });
    expect((env.items[1]!.prediction as { writtenAt: string }).writtenAt).toBe(TODAY);
    expect((env.items[1]!.provenance as { inputs: string[] }).inputs).toEqual([`${SEAT_INPUT_PROVENANCE_PREFIX}${SHA_IN}`]);
    expect(env.items[0]!.subject).toEqual({ customer: "c5", groups: ["180 秒"], gamesCount: 25 });
    expect(env.items[0]!.schemaVersion).toBe("0.4");
  });
  it("同じ入力で 2 回 → 同じ封筒。封筒は席の object を参照で持たない", () => {
    expect(envelope()).toEqual(envelope());
    const input = llm();
    const env = completeSeatOutput(input, ctx()) as { items: { observations: { packetRef: { path: string } }[] }[] };
    env.items[0]!.observations[0]!.packetRef.path = "x";
    expect(input.items[0]!.observations[0]!.packetRef.path).toBe("aggregates.sideMatch.attack.numerator");
  });
  it("席が provenance を書いたら席が書く形で落ちる(道具の欄を LLM に書かせない)", () => {
    const bad = llm() as { items: Record<string, unknown>[] };
    bad.items[0]!.provenance = { gitHead: null, inputs: ["x"], excludedInputs: [] };
    expect(validateSeatOutputLlm(bad).length).toBeGreaterThan(0);
    expect(() => completeSeatOutput(bad, ctx())).toThrow(/席が書く形/);
  });
  it("itemId の重複は封筒にしない", () => {
    const bad = llm();
    bad.items[1]!.itemId = "S-001";
    expect(() => completeSeatOutput(bad, ctx())).toThrow(/重複/);
  });
});

describe("封筒の検査 E-1〜E-7(校正 2: 最小の封筒は通る)", () => {
  it("通る", () => expect(problems(envelope())).toEqual([]));
  it("契約 v0.4 の分岐: 各行が H-1〜H-8 を通る(packet. の obsId は文法、finding に予測は要らない、fact は読みの形を要らない)", () => {
    const env = envelope() as { items: unknown[] };
    for (const item of env.items) {
      const results = validateHypothesisLine(item, { today: TODAY, registry: REGISTRY });
      expect(results.filter((r) => !r.ok).map((r) => `${r.check}: ${r.messages.join(" / ")}`)).toEqual([]);
    }
  });
});

describe("変異(それぞれ 1 件だけ赤くなる)", () => {
  type Env = { reach: { passphrase: string }; items: Record<string, unknown>[]; answers: Record<string, unknown>[]; selfComputedNumbers: { value: number }[] };
  it("unanswerable の missing を空に → E-2", () => {
    const env = envelope() as Env;
    env.answers[0]!.missing = [];
    expect(problems(env)).toEqual(["E-2: answers[0](unanswerable)の missing が空 ― 何が無いかを空で埋めない"]);
  });
  it("partial の missing を空に → E-2(unanswerable と対称。監査の指摘 2026-09-30)", () => {
    const env = envelope() as Env;
    env.answers[0]!.status = "partial";
    env.answers[0]!.missing = [];
    expect(problems(env)).toEqual(["E-2: answers[0](partial)の missing が空 ― 何が無いかを空で埋めない"]);
  });
  it("packetRef.path を v0.1 の packet に無い列に → E-4(文法。実在の照合ではない)", () => {
    const env = envelope() as Env;
    (env.items[0]!.observations as { packetRef: { path: string }; obsId: string }[])[0]!.packetRef.path = "facts.time.bySpent[3].collapsed";
    (env.items[0]!.observations as { packetRef: { path: string }; obsId: string }[])[0]!.obsId = "packet.facts.time.bySpent[3].collapsed";
    const out = problems(env);
    expect(out.filter((p) => p.startsWith("E-4"))).toHaveLength(1);
    expect(out.filter((p) => p.startsWith("E-3"))).toHaveLength(1); // H-2 の分岐も同じ文法で落ちる(文法は 1 か所)
    expect(out).toHaveLength(2);
  });
  it("合言葉を 1 字変える → E-1", () => {
    const env = envelope() as Env;
    env.reach.passphrase = "run2026X";
    expect(problems(env)).toEqual(["E-1: 合言葉が違う(席「run2026X」/ meta「run20260」)― 届いていない"]);
  });
  it("隔離欄の数を statement に書く → E-5(H-1 も落ちる)", () => {
    const env = envelope() as Env;
    env.items[0]!.statement = "実戦も攻めだった局面は 65(率 0.61)だった。";
    const out = problems(env);
    expect(out.some((p) => p.startsWith("E-5"))).toBe(true);
    expect(out.some((p) => p.includes("H-1"))).toBe(true);
    expect(out).toHaveLength(2);
  });
  it("fact の statement に「という読みです」 → E-3(H-5 の分岐)", () => {
    const env = envelope() as Env;
    env.items[0]!.statement = "実戦も攻めだった局面は 65 だった、という読みです。";
    expect(problems(env)).toEqual(["E-3: items[0] H-5: 事実の行(fact / finding)の statement に読みの語「という読み」を含む"]);
  });
  it("hypothesis から prediction を外す → E-3(H-4)", () => {
    const env = envelope() as Env;
    delete env.items[1]!.prediction;
    expect(problems(env)).toEqual(["E-3: items[1] H-4: prediction が無い"]);
  });
  it("finding から prediction を外す(元から無い)→ 通る。付けても通る", () => {
    const env = envelope() as Env;
    expect(env.items[0]!.prediction).toBeUndefined();
    expect(problems(env)).toEqual([]);
    env.items[0]!.prediction = { writtenAt: TODAY, window: "次の 25 局", metric: "packet.aggregates.sideMatch.attack.numerator", comparator: ">=", value: 0.6, alsoRequires: [] };
    expect(problems(env)).toEqual([]);
  });
  it("answers の中に internal → E-6", () => {
    const env = envelope() as Env;
    env.answers[0]!.internal = { reasoning: "x" };
    const out = problems(env);
    expect(out).toHaveLength(1); // 封筒の schema(additionalProperties: false)が先に落とす。E-6 は schema をすり抜けた形(items の中の入れ子など)の備え
    expect(out[0]).toMatch(/^schema: .*internal/);
  });
  it("run.inputSha256 が meta と違う → E-7", () => {
    const env = envelope() as Env & { run: { inputSha256: string } };
    env.run.inputSha256 = "8".repeat(64);
    expect(problems(env)).toEqual(["E-7: run.inputSha256 が meta の seat_input の sha と違う(別の入力で得た出力)"]);
  });
  it("節を写さず omissions にも無い → E-1", () => {
    const env = envelope() as Env & { reach: { sections: unknown[] } };
    env.reach.sections = env.reach.sections.slice(0, 2);
    expect(problems(env)).toEqual(["E-1: 節「2」を席が reach.sections に写しておらず、omissions にも無い"]);
  });
});

describe("packet を読まない(校正 4)・足すだけ(校正 1)", () => {
  it("seatOutput.ts と packetRef.ts は observationPacket* を import しない・ファイルを開かない(schema と登録簿を除く)", () => {
    for (const file of ["seatOutput.ts", "packetRef.ts"]) {
      const src = readFileSync(new URL(`./${file}`, import.meta.url), "utf-8");
      expect(src, file).not.toMatch(/from "\.\/observation(Packet|Aggregates|Facts|Materials|Provenance)/);
      expect(src, file).not.toMatch(/readFileSync\([^)]*packet/i);
    }
  });
  it("実験 1 の契約の行(v0.3)は schemaVersion を 0.4 にすればそのまま通る(9 検査 ok)", () => {
    const dir = new URL("../records/experiment-llm-25/", import.meta.url);
    const files = readdirSync(dir).filter((f) => f.startsWith("E-") && f.endsWith(".json"));
    expect(files.length).toBe(6);
    const registry = new Set<string>();
    for (const f of files) {
      const line = JSON.parse(readFileSync(new URL(f, dir), "utf-8")) as Record<string, unknown>;
      for (const obs of line.observations as { obsId: string }[]) registry.add(obs.obsId);
      for (const ce of (line.counterEvidence as { items: { observations: { obsId: string }[] }[] }).items) for (const o of ce.observations) registry.add(o.obsId);
      line.schemaVersion = "0.4";
      const results = validateHypothesisLine(line, { today: TODAY, registry });
      expect(results.filter((r) => !r.ok).map((r) => `${f} ${r.check}: ${r.messages.join(" / ")}`)).toEqual([]);
    }
  });
});

describe("E-1 と見出しだけの節(2026-09-30 の初回の実行で実測。司令塔の決定 (iii))", () => {
  // 席は束の見出しどおり「0」「0.1」「0.2」(読み方・省いたもの・線の組)も読んだと書く。
  // **meta がそれを持っていないと、正直な席が落ちる**。持っていれば通り、束にも無い節名は落ちる。
  function withReachSections(sections: { section: string; lastKey: string }[]) {
    const src = llm();
    src.reach.sections = sections as typeof src.reach.sections;
    return completeSeatOutput(src, ctx());
  }
  const DATA = [{ section: "A", lastKey: "q1" }, { section: "1", lastKey: "g25 25" }, { section: "2", lastKey: "aggregates.branches.total.value" }];
  it("見出しだけの節を挙げても落ちない(lastKey は何でもよい ― データの行が無いので)", () => {
    const found = problems(withReachSections([...DATA, { section: "0", lastKey: "読み方" }, { section: "0.1", lastKey: "-" }]));
    expect(found).toEqual([]);
  });
  it("データの行を持つ節は、見出しに見えても lastKey を厳しく照合する(0.2 線の組。2026-09-30 の独立監査の指摘)", () => {
    // meta が 0.2 を**データの節**として持つとき、席の lastKey が違えば落ちる(見出しの枝に逃げない)
    const metaWith = { ...meta(), sections: [...meta().sections, { section: "0.2", title: "線の組", packetPath: "provenance.thresholds", rows: 1, lastKey: "- ahead_cp:" }], headingSections: ["0", "0.1"] };
    const check = (lastKey: string) => seatOutputProblems(withReachSections([...DATA, { section: "0.2", lastKey }]), { meta: metaWith, request: request(), today: TODAY, registry: REGISTRY });
    expect(check("- ahead_cp:")).toEqual([]);
    const wrong = check("それらしい鍵");
    expect(wrong.length).toBe(1);
    expect(wrong[0]).toContain("前方一致しない");
  });
  it("meta にも束の見出しにも無い節名は落ちる(捏造は通らない)", () => {
    const found = problems(withReachSections([...DATA, { section: "9.9", lastKey: "それらしい鍵" }]));
    expect(found.length).toBe(1);
    expect(found[0]).toContain("meta にも束の見出しにも無い節「9.9」");
  });
  it("データの行が在る節は今までどおり lastKey を照合する", () => {
    const found = problems(withReachSections([{ section: "A", lastKey: "q1" }, { section: "1", lastKey: "ちがう鍵" }, { section: "2", lastKey: "aggregates.branches.total.value" }]));
    expect(found.length).toBe(1);
    expect(found[0]).toContain("前方一致しない");
  });
});

describe("H-2 の歩く先(2026-09-30 に R4 で見つけた抜け。反証と分数の中の packet. の id)", () => {
  // 【なぜ在来の fixture で捕まらなかったか】反証・分数が使う path が item.observations と同じ字だったので、
  // 先に集めた packetIds に入っていて登録簿の側へ回らなかった。**別の path**にすると抜けが出る(集合の重なりで隠れる型)。
  const OTHER = "facts.collapse[3].afterCp";
  function withCounterOnlyPath(path: string) {
    const src = llm();
    src.items[0]!.counterEvidence = { attempted: true, items: [{ kind: "counterexample", text: "崩れた局面の側を見た。", observations: [{ value: -140, packetRef: { path } }] }], result: "weakened" };
    return completeSeatOutput(src, ctx());
  }
  function withDerivedOnlyPath(path: string) {
    const src = llm();
    src.items[0]!.observations = [{ value: 65, unit: "positions", packetRef: NUM(), derived: { kind: "ratio", numerator: { path, value: 65 }, denominator: { path: "aggregates.sideMatch.attack.denominator", value: 107 } } }, { value: 107, unit: "positions", packetRef: DEN() }];
    return completeSeatOutput(src, ctx());
  }
  it("反証だけが持つ path でも通る(登録簿の側へ回さない)", () => {
    expect(problems(withCounterOnlyPath(OTHER))).toEqual([]);
  });
  it("反証の path の文法が壊れていれば、その場所を名指しで落ちる", () => {
    const found = problems(withCounterOnlyPath("facts.collapse.afterCp"));
    expect(found.length).toBe(1);
    expect(found[0]).toContain("H-2");
    expect(found[0]).toContain("counterEvidence.items[0].observations[0]");
  });
  it("分数の分子だけが持つ path でも通る / 壊れていれば分子を名指しで落ちる", () => {
    expect(problems(withDerivedOnlyPath("aggregates.groups.core.games.value"))).toEqual([]);
    const found = problems(withDerivedOnlyPath("aggregates.groups.core.games"));
    expect(found.length).toBe(1);
    expect(found[0]).toContain("observations[0].derived.numerator");
  });
  it("登録簿の obs.* は今までどおり登録簿で見る(packet. の分岐が全部を通してしまわない)", () => {
    const env = envelope() as { items: Record<string, unknown>[] };
    (env.items[0]!.observations as Record<string, unknown>[])[0]!.obsId = "obs.notInRegistry";
    const found = problems(env);
    expect(found.some((p) => p.includes("H-2") && p.includes("obs.notInRegistry"))).toBe(true);
  });
});
