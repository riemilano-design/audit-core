// 束 R4 の試験(計画 §6「schemaAdapters」)。**写しは判定しない** ― 判定は正本の検証器だけなので、この試験が見るのは 2 つ。
//
// 【1】各社の制約に本当に写っているか(OpenAI strict = 全欄 required + additionalProperties false + 受け付けない語が残っていない、Gemini = additionalProperties と pattern が無い、Anthropic = 正本のまま)。
// 【2】写しの形で返った JSON が、null の後始末を通せば**正本を通る**こと(受理集合を狭めていない)。往復は seat-output と integration の両方で見る。
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { validateIntegrationLlm } from "./integration.js";
import { adaptSchema, dropNullsNotAllowed, effectiveValueShape, forbiddenKeywords, toAnthropic, toGemini, toOpenAIStrict } from "./schemaAdapters.js";
import { validateSeatOutputLlm } from "./seatOutput.js";

type Rec = Record<string, unknown>;
function loadSchema(name: string): Rec {
  return JSON.parse(readFileSync(new URL(`../schemas/${name}`, import.meta.url), "utf-8")) as Rec;
}
const SEAT_SCHEMA = loadSchema("seat-output.llm.v0.1.schema.json");
const INTEG_SCHEMA = loadSchema("integration.llm.v0.1.schema.json");

function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}
/** OpenAI strict の席が返しうる形を作る: 正本で任意かつ書かなかった欄を null で埋める */
function fillNullsForOptional(json: unknown, schema: unknown): unknown {
  if (Array.isArray(json)) return json.map((item) => fillNullsForOptional(item, isRecord(schema) ? schema.items : undefined));
  if (!isRecord(json)) return json;
  const props = isRecord(schema) && isRecord(schema.properties) ? schema.properties : {};
  const required = new Set(Array.isArray((schema as Rec).required) ? ((schema as Rec).required as string[]) : []);
  const out: Rec = {};
  for (const [k, v] of Object.entries(json)) out[k] = fillNullsForOptional(v, props[k]);
  for (const k of Object.keys(props)) if (!(k in out) && !required.has(k)) out[k] = null;
  return out;
}
/**
 * **自由形の節**を探す(2026-09-30 の初回の実行で 3 社が 400 を返した形)。
 * `{type:"array"}` に items が無い → Gemini も OpenAI も 400 / `{type:"object"}` に properties が無い → OpenAI strict が 400。
 */
function freeFormNodes(schema: unknown, path = "$"): string[] {
  const found: string[] = [];
  if (Array.isArray(schema)) { schema.forEach((s, i) => found.push(...freeFormNodes(s, `${path}[${i}]`))); return found; }
  if (!isRecord(schema)) return found;
  if (schema.type === "array" && schema.items === undefined) found.push(`${path}: array に items が無い`);
  if (schema.type === "object" && schema.properties === undefined) found.push(`${path}: object に properties が無い`);
  for (const [k, v] of Object.entries(schema)) if (k !== "enum" && k !== "required") found.push(...freeFormNodes(v, `${path}.${k}`));
  return found;
}

/** 節を歩いて、objects に required と additionalProperties が揃っているかを見る(OpenAI strict の条件) */
function strictProblems(schema: unknown, path = "$"): string[] {
  const problems: string[] = [];
  if (Array.isArray(schema)) { schema.forEach((s, i) => problems.push(...strictProblems(s, `${path}[${i}]`))); return problems; }
  if (!isRecord(schema)) return problems;
  if (isRecord(schema.properties)) {
    const keys = Object.keys(schema.properties);
    const required = Array.isArray(schema.required) ? (schema.required as string[]) : [];
    if (keys.length !== required.length || keys.some((k) => !required.includes(k))) problems.push(`${path}: required が全欄でない`);
    if (schema.additionalProperties !== false) problems.push(`${path}: additionalProperties が false でない`);
    for (const [k, v] of Object.entries(schema.properties)) problems.push(...strictProblems(v, `${path}.${k}`));
    return problems;
  }
  for (const [k, v] of Object.entries(schema)) if (k !== "enum" && k !== "required") problems.push(...strictProblems(v, `${path}.${k}`));
  return problems;
}

// ---- 正本を通る fixture(最小) ----
function seatLlm(): Rec {
  return {
    reach: { passphrase: "run20260", sections: [{ section: "A", lastKey: "q1 普段指さない", seal: "a1b2c3" }, { section: "2", lastKey: "aggregates.branches.total.value", seal: "d4e5f6" }] },
    items: [
      {
        itemId: "S-001", kind: "finding", factOrHypothesis: "fact", lane: "side",
        statement: "第一候補が攻めだった分かれ道のうち、実戦も攻めだった局面は 65 だった。",
        observations: [{ path: "aggregates.sideMatch.attack.numerator", value: 65, unit: "件", packetRef: { path: "aggregates.sideMatch.attack.numerator" } }],
        counterEvidence: { attempted: true, items: [], result: "none_found" },
      },
      {
        itemId: "S-002", kind: "hypothesis", factOrHypothesis: "hypothesis", lane: "time",
        statement: "長く考えた局面で崩れが増えている可能性があります。",
        observations: [{ path: "facts.time[3].spentSec", value: null, packetRef: { path: "facts.time[3].spentSec" } }],
        counterEvidence: { attempted: true, items: [{ kind: "denominator", text: "分母を見た", observations: [{ value: 25, packetRef: { path: "aggregates.groups.core.games.value" } }] }], result: "stands" },
        prediction: { window: "次の 20 局", metric: "崩れの件数", comparator: "<=", value: 10, alsoRequires: [] },
        requestRef: { questionId: "q1" },
        internal: { reasoning: "この手は自玉側を固める狙いだったかもしれない(内部だけ)" },
      },
    ],
    answers: [{ questionId: "q1", status: "partial", itemIds: ["S-001", "S-002"], reason: "束に戦型の認識が 25 行しかない", missing: [{ what: "普段指す戦型の組", howToMeasure: "同じ人の別の組で同じ認識を回す" }] }],
    selfComputedNumbers: [],
    omissions: [],
  };
}
function integLlm(): Rec {
  return {
    clusters: [{
      clusterId: "C-001", packetRefs: ["aggregates.sideMatch.attack.numerator"],
      itemRefs: [{ seatIndex: 0, hypothesisId: "I-0-001" }, { seatIndex: 1, hypothesisId: "I-1-003" }],
      representative: { kind: "finding", factOrHypothesis: "fact", lane: "side", statement: "攻めの側が合った局面は 65 だった。", observations: [{ path: "aggregates.sideMatch.attack.numerator", value: 65, packetRef: { path: "aggregates.sideMatch.attack.numerator" } }], counterEvidence: { attempted: true, items: [], result: "none_found" } },
    }],
    contradictions: [], dropped: [], heldBack: [], forVerification: ["C-001"], answerNotes: [{ questionId: "q1", text: "束に無いので答えられない節がある" }],
  };
}

describe("fixture は正本を通る(往復の出発点)", () => {
  it("seat-output と integration の最小 fixture", () => {
    expect(validateSeatOutputLlm(seatLlm())).toEqual([]);
    expect(validateIntegrationLlm(integLlm())).toEqual([]);
  });
});

describe("OpenAI strict の写し", () => {
  it("全欄 required・additionalProperties false・受け付けない語が残っていない", () => {
    for (const [name, schema] of [["seat", SEAT_SCHEMA], ["integ", INTEG_SCHEMA]] as const) {
      const adapted = toOpenAIStrict(schema as Rec);
      expect(strictProblems(adapted), name).toEqual([]);
      expect(forbiddenKeywords("openai", adapted), name).toEqual([]);
    }
  });
  it("自由形の節が残っていない(初回の実行の 400 の回帰): array に items・object の枝は落とす", () => {
    for (const [name, schema] of [["seat", SEAT_SCHEMA], ["integ", INTEG_SCHEMA]] as const) {
      expect(freeFormNodes(toOpenAIStrict(schema as Rec)), name).toEqual([]);
    }
    // 正本には自由形が在る(だから写しで始末する必要がある)= この試験が本当に何かを測っている証拠
    expect(freeFormNodes(SEAT_SCHEMA).length).toBeGreaterThan(0);
  });
  it("value の枝は「数・字・真偽・無し・数や字の配列」になる(object の枝は落ちる)", () => {
    const value = (toOpenAIStrict(SEAT_SCHEMA) as any).properties.items.items.properties.observations.items.properties.value;
    const types = (value.anyOf as Record<string, unknown>[]).map((b) => b.type);
    expect(types).toEqual(["number", "string", "boolean", "null", "array"]);
    const array = (value.anyOf as Record<string, any>[]).find((b) => b.type === "array");
    expect((array!.items.anyOf as Record<string, unknown>[]).map((b) => b.type)).toEqual(["number", "string", "boolean", "null"]);
  });
  it("任意の欄は「その形 か null」になる(strict は全欄 required なので null で「無い」を表す)", () => {
    const adapted = toOpenAIStrict(SEAT_SCHEMA) as any;
    const item = adapted.properties.items.items;
    expect(Array.isArray(item.properties.prediction.anyOf)).toBe(true);
    expect(item.properties.prediction.anyOf[1]).toEqual({ type: "null" });
    // 必須の欄は包まない
    expect(item.properties.statement).toEqual({ type: "string" });
  });
  it("正本が oneOf で許した null は写しでも許される(observations[].value)", () => {
    const adapted = toOpenAIStrict(SEAT_SCHEMA) as any;
    const value = adapted.properties.items.items.properties.observations.items.properties.value;
    expect(value.anyOf).toContainEqual({ type: "null" });
  });
});

describe("Gemini の写し", () => {
  it("additionalProperties・pattern・const が残っていない", () => {
    for (const [name, schema] of [["seat", SEAT_SCHEMA], ["integ", INTEG_SCHEMA]] as const) {
      const adapted = toGemini(schema as Rec);
      expect(forbiddenKeywords("gemini", adapted), name).toEqual([]);
      expect(JSON.stringify(adapted), name).not.toContain("additionalProperties");
    }
  });
  it("自由形の array に items を足す(Gemini は items の無い array を 400 で返す。2026-09-30 の実測)", () => {
    for (const [name, schema] of [["seat", SEAT_SCHEMA], ["integ", INTEG_SCHEMA]] as const) {
      const found = freeFormNodes(toGemini(schema as Rec)).filter((line) => line.includes("array"));
      expect(found, name).toEqual([]);
    }
  });
  it("任意の欄はそのまま任意(required を足さない)", () => {
    const adapted = toGemini(SEAT_SCHEMA) as any;
    expect(adapted.properties.items.items.required).toEqual(SEAT_SCHEMA.properties && (SEAT_SCHEMA as any).properties.items.items.required);
    expect(adapted.properties.items.items.properties.prediction.anyOf).toBeUndefined();
  });
  it("type が配列の欄は nullable に写す", () => {
    const adapted = toGemini({ type: "object", properties: { x: { type: ["string", "null"] } }, required: ["x"] }) as any;
    expect(adapted.properties.x).toEqual({ type: "string", nullable: true });
  });
  it("const は enum + type に写す", () => {
    const adapted = toGemini({ type: "object", properties: { c: { const: "seat-output" } }, required: ["c"] }) as any;
    expect(adapted.properties.c).toEqual({ enum: ["seat-output"], type: "string" });
  });
});

describe("Anthropic の写し", () => {
  it("正本のまま(注記だけ外す。pattern・minItems は残す)", () => {
    const adapted = toAnthropic(SEAT_SCHEMA) as any;
    expect(forbiddenKeywords("anthropic", adapted)).toEqual([]);
    expect(adapted.$schema).toBeUndefined();
    expect(adapted.title).toBeUndefined();
    expect(adapted.properties.items.items.properties.itemId.pattern).toBe("^S-[0-9]{3}$");
    expect(adapted.properties.items.items.properties.observations.minItems).toBe(1);
  });
  it("adaptSchema は社ごとに同じものを返す", () => {
    expect(adaptSchema("openai", SEAT_SCHEMA)).toEqual(toOpenAIStrict(SEAT_SCHEMA));
    expect(adaptSchema("gemini", SEAT_SCHEMA)).toEqual(toGemini(SEAT_SCHEMA));
    expect(adaptSchema("anthropic", SEAT_SCHEMA)).toEqual(toAnthropic(SEAT_SCHEMA));
  });
});

describe("3 社の有効な形をそろえる(司令塔の条件 2026-09-30 ― 席をまたいで比べるため)", () => {
  // 社ごとに狭さが違うと、**席の間で「書ける形」が変わり、一致・不一致を実力差として読めなくなる**。
  // いちばん狭い形(数・字・真偽・無し・その配列)に 3 社そろえる。
  it("observations[].value の形が 3 社で同じ", () => {
    const shapes = (["openai", "gemini", "anthropic"] as const).map((p) => effectiveValueShape(p, SEAT_SCHEMA));
    expect(shapes[0]).toEqual(["array", "boolean", "null", "number", "string"]);
    expect(shapes[1], "gemini").toEqual(shapes[0]);
    expect(shapes[2], "anthropic").toEqual(shapes[0]);
    // 正本は object も許す(だから写しでそろえる必要が在る)= この試験が何かを測っている証拠
    const canonical = ((SEAT_SCHEMA as any).properties.items.items.properties.observations.items.properties.value.oneOf as Record<string, unknown>[]).map((b) => b.type).sort();
    expect(canonical).toContain("object");
  });
  it("枝が全部自由形の object なら、字の枝を残す(空の anyOf にしない。独立監査の変異 L)", () => {
    // 空の anyOf は「何も受け付けない」形になり、社の入口で落ちる。受け皿を残す。
    const canonical = { type: "object", properties: { x: { oneOf: [{ type: "object" }, { type: "object" }] } }, required: ["x"], additionalProperties: false };
    for (const provider of ["openai", "gemini", "anthropic"] as const) {
      const adapted = adaptSchema(provider, canonical) as any;
      const node = provider === "openai" ? adapted.properties.x : adapted.properties.x;
      const branches = (node.anyOf ?? node.oneOf) as Record<string, unknown>[];
      expect(branches, provider).toEqual([{ type: "string" }]);
    }
  });
  it("自由形の節は 3 社とも残らない", () => {
    for (const provider of ["openai", "gemini", "anthropic"] as const) {
      for (const schema of [SEAT_SCHEMA, INTEG_SCHEMA]) expect(freeFormNodes(adaptSchema(provider, schema)), provider).toEqual([]);
    }
  });
});

describe("写しの形で返った JSON は、null の後始末を通せば正本を通る(受理集合を狭めていない)", () => {
  it("seat-output: 任意の欄を全部 null で埋めて返っても通る", () => {
    const withNulls = fillNullsForOptional(seatLlm(), SEAT_SCHEMA);
    // null を落とす前は正本で落ちる(= この試験が後始末を本当に測っている)
    expect(validateSeatOutputLlm(withNulls).length).toBeGreaterThan(0);
    const cleaned = dropNullsNotAllowed(withNulls, SEAT_SCHEMA);
    expect(validateSeatOutputLlm(cleaned)).toEqual([]);
    expect(cleaned).toEqual(seatLlm());
  });
  it("integration: 同じ往復", () => {
    const withNulls = fillNullsForOptional(integLlm(), INTEG_SCHEMA);
    expect(validateIntegrationLlm(withNulls).length).toBeGreaterThan(0);
    const cleaned = dropNullsNotAllowed(withNulls, INTEG_SCHEMA);
    expect(validateIntegrationLlm(cleaned)).toEqual([]);
    expect(cleaned).toEqual(integLlm());
  });
  it("正本が null を許す欄の null は残す(observations[].value の null を消さない)", () => {
    const json = seatLlm();
    const cleaned = dropNullsNotAllowed(json, SEAT_SCHEMA) as any;
    expect(cleaned.items[1].observations[0].value).toBeNull();
    expect("value" in cleaned.items[1].observations[0]).toBe(true);
  });
  it("後始末は配列の中の object も見る", () => {
    const cleaned = dropNullsNotAllowed({ items: [{ itemId: "S-001", prediction: null }] }, SEAT_SCHEMA) as any;
    expect("prediction" in cleaned.items[0]).toBe(false);
    expect(cleaned.items[0].itemId).toBe("S-001");
  });
});

// ---------------------------------------------------------------------------
// STEP S-4(2026-10-06、audit-core/docs/CORE_CONNECTION_S4_PLAN_2026-10-06.md §2.1(b)):
// seat-output.llm.v0.2・integration.llm.v0.2 は v0.1 の複製 + observations の minItems を外した**だけ**
// (構造で比べる)。写し(adaptSchema/forbiddenKeywords)は版が上がっても今までどおり緑であることを見る
// ― 2 つの契約は別々の node に minItems が在るので、まとめて 1 つの describe にする。
// ---------------------------------------------------------------------------
const SEAT_SCHEMA_V02 = loadSchema("seat-output.llm.v0.2.schema.json");
const INTEG_SCHEMA_V02 = loadSchema("integration.llm.v0.2.schema.json");

describe("版 0.2(observations の minItems を外す。STEP S-4)", () => {
  it("seat-output.llm.v0.2 は v0.1 の複製 + observations.minItems を外した**だけ**(構造で比べる)", () => {
    const restored = JSON.parse(JSON.stringify(SEAT_SCHEMA_V02)) as any;
    restored.properties.items.items.properties.observations.minItems = 1;
    expect(restored).toEqual(SEAT_SCHEMA);
    expect(SEAT_SCHEMA_V02).not.toEqual(SEAT_SCHEMA);
  });
  it("integration.llm.v0.2 は v0.1 の複製 + clusters[].representative.observations.minItems を外した**だけ**(構造で比べる。他の minItems は手を付けていない)", () => {
    const restored = JSON.parse(JSON.stringify(INTEG_SCHEMA_V02)) as any;
    restored.properties.clusters.items.properties.representative.properties.observations.minItems = 1;
    expect(restored).toEqual(INTEG_SCHEMA);
    expect(INTEG_SCHEMA_V02).not.toEqual(INTEG_SCHEMA);
    // 観測以外の minItems(packetRefs・itemRefs・contradictions)は 0.1 と同じ値のまま
    expect((INTEG_SCHEMA_V02 as any).properties.clusters.items.properties.packetRefs.minItems).toBe(1);
    expect((INTEG_SCHEMA_V02 as any).properties.clusters.items.properties.itemRefs.minItems).toBe(1);
    expect((INTEG_SCHEMA_V02 as any).properties.contradictions.items.properties.itemRefs.minItems).toBe(2);
    expect((INTEG_SCHEMA_V02 as any).properties.contradictions.items.properties.packetRefs.minItems).toBe(1);
  });
  it("写し(forbiddenKeywords・自由形の節)は v0.2 でも緑のまま", () => {
    for (const provider of ["openai", "gemini", "anthropic"] as const) {
      for (const schema of [SEAT_SCHEMA_V02, INTEG_SCHEMA_V02]) {
        const adapted = adaptSchema(provider, schema);
        expect(forbiddenKeywords(provider, adapted), provider).toEqual([]);
        expect(freeFormNodes(adapted), provider).toEqual([]);
      }
    }
  });
  it("items[].observations が 0 件の封筒は v0.2 の schema を通る(v0.1 では minItems で落ちるはず)", () => {
    const zeroObs = seatLlm();
    (zeroObs.items as Rec[])[0]!.observations = [];
    expect(validateSeatOutputLlm(zeroObs, SEAT_SCHEMA_V02 as any)).toEqual([]);
    const v01Problems = validateSeatOutputLlm(zeroObs, SEAT_SCHEMA as any);
    expect(v01Problems.length).toBeGreaterThan(0);
    expect(v01Problems.join(" / ")).toContain("足りない");
  });
});
