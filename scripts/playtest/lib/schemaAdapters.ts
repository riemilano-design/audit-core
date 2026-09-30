// 束 R4 ― 正本の schema(seat-output.llm.v0.1・integration.llm.v0.1)を各社の構造化出力の制約に写す(計画 §1「構造化の掛け方」)。
//
// 【写しは「席がこの形で書きやすくする」ため】判定は正本の検証器(lib/eventSchema.ts で正本に掛ける)だけ。写しが受理集合を広げても狭めても、最後は正本で落ちる・通る。
// 【OpenAI strict】全欄 required・任意の欄は anyOf [T, null]・additionalProperties false・oneOf → anyOf・受け付けない語(pattern/minItems/minimum/maximum/const)は外す(const は enum に)。
// 【Gemini responseSchema】additionalProperties 無し・const → enum・oneOf → anyOf・pattern/minimum/maximum 無し。任意の欄はそのまま任意。
// 【Anthropic input_schema】正本のまま($schema/$id/title/description だけ外す)。
// 【null の後始末】strict の写しは任意の欄を null で返しうる。正本が null を許さない欄の null は落としてから正本に掛ける(dropNullsNotAllowed)。

type Rec = Record<string, unknown>;
function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

const ANNOTATIONS = new Set(["$schema", "$id", "title", "description", "$comment"]);

/**
 * **自由形の節**(2026-09-30 の初回の実行で 3 社の 400 から分かった):
 * - `{type: "array"}` に `items` が無いと **Gemini は 400**(`any_of[5].items: missing field`)。
 *   **OpenAI strict も** items を要る。→ 中身を「数・字・真偽・無し」にする(束の値の配列は名前や印の列なので収まる)。
 * - `{type: "object"}` に `properties` が無いと **OpenAI strict は 400**(`additionalProperties is required to be supplied and to be false`)。
 *   strict では「何でも入る object」を書けないので、**枝が他にあれば落とす**(落とすほうが、空の object しか許さない偽の枝より正直)。
 *   Gemini は自由形の object を受け付けた(400 の指摘に出ていない)ので触らない。
 * 正本は変えないので、返ってきた JSON は今までどおり正本で受理・却下される。
 */
const SCALAR_BRANCHES = [{ type: "number" }, { type: "string" }, { type: "boolean" }, { type: "null" }];
function isFreeFormObject(node: unknown): boolean {
  return isRecord(node) && node.type === "object" && node.properties === undefined;
}
function isFreeFormArray(node: unknown): boolean {
  return isRecord(node) && node.type === "array" && node.items === undefined;
}
function withScalarItems(node: Rec): Rec {
  return { ...node, items: { anyOf: SCALAR_BRANCHES.map((b) => ({ ...b })) } };
}

/**
 * 自由形の始末を **3 社で同じにする**(司令塔の条件 2026-09-30)。
 * 社ごとに写しの狭さが違うと、**席の間で「書ける形」が変わり、一致・不一致を実力差として読めなくなる**
 * (「一致を証拠にしない」と同じ家族の、逆向きの穴)。だから **いちばん狭い社に全社をそろえる**:
 * `value` の形は「数・字・真偽・無し・その配列」。観測の値に自由形の object が要る場面は無い。
 */
function normalizeFreeForm(node: Rec): Rec {
  const out = isFreeFormArray(node) ? withScalarItems(node) : node;
  for (const key of ["anyOf", "oneOf"]) {
    if (!Array.isArray(out[key])) continue;
    const kept = (out[key] as unknown[]).filter((branch) => !isFreeFormObject(branch));
    out[key] = kept.length > 0 ? kept : [{ type: "string" }];
  }
  return out;
}

/** その社の写しで `observations[].value` に書ける形(記録に残して 3 席で比べる) */
export function effectiveValueShape(provider: "openai" | "gemini" | "anthropic", canonical: Rec): string[] {
  const adapted = adaptSchema(provider, canonical) as Rec;
  const items = ((adapted.properties as Rec | undefined)?.items as Rec | undefined);
  const row = (items?.items as Rec | undefined);
  const value = (((row?.properties as Rec | undefined)?.observations as Rec | undefined)?.items as Rec | undefined);
  const node = ((value?.properties as Rec | undefined)?.value) as Rec | undefined;
  const branches = (node?.anyOf ?? node?.oneOf) as Rec[] | undefined;
  if (branches === undefined) return node?.type === undefined ? [] : [String(node.type)];
  return branches.map((b) => String(b.type ?? (b.nullable === true ? "null" : "?"))).sort();
}

function stripAnnotations(schema: Rec): Rec {
  const out: Rec = {};
  for (const [k, v] of Object.entries(schema)) if (!ANNOTATIONS.has(k)) out[k] = v;
  return out;
}

function mapSchema(schema: unknown, fn: (node: Rec, isOptionalProperty: boolean) => Rec, isOptionalProperty = false): unknown {
  if (!isRecord(schema)) return schema;
  const node: Rec = { ...schema };
  if (isRecord(node.properties)) {
    const required = new Set(Array.isArray(node.required) ? (node.required as string[]) : []);
    const props: Rec = {};
    for (const [k, v] of Object.entries(node.properties)) props[k] = mapSchema(v, fn, !required.has(k));
    node.properties = props;
  }
  if (isRecord(node.items)) node.items = mapSchema(node.items, fn, false);
  for (const key of ["oneOf", "anyOf"]) if (Array.isArray(node[key])) node[key] = (node[key] as unknown[]).map((s) => mapSchema(s, fn, false));
  return fn(node, isOptionalProperty);
}

/** OpenAI strict モード向け */
export function toOpenAIStrict(canonical: Rec): Rec {
  const mapped = mapSchema(stripAnnotations(canonical), (node, optional) => {
    const out: Rec = {};
    for (const [k, v] of Object.entries(node)) {
      if (ANNOTATIONS.has(k) || k === "pattern" || k === "minItems" || k === "minimum" || k === "maximum") continue;
      if (k === "const") { out.enum = [v]; continue; }
      if (k === "oneOf") { out.anyOf = v; continue; }
      out[k] = v;
    }
    if (isRecord(out.properties)) {
      out.required = Object.keys(out.properties);
      out.additionalProperties = false;
    }
    const normalized = normalizeFreeForm(out);
    for (const key of Object.keys(normalized)) out[key] = normalized[key];
    if (isFreeFormArray(out)) return withScalarItems(out);
    if (optional) {
      // 任意の欄は「その形 か null」にする(strict は全欄 required なので null で「無い」を表す)
      return { anyOf: [out, { type: "null" }] };
    }
    return out;
  }) as Rec;
  return mapped;
}

/** Gemini responseSchema 向け */
export function toGemini(canonical: Rec): Rec {
  return mapSchema(stripAnnotations(canonical), (node) => {
    const out: Rec = {};
    for (const [k, v] of Object.entries(node)) {
      if (ANNOTATIONS.has(k) || k === "additionalProperties" || k === "pattern" || k === "minimum" || k === "maximum") continue;
      if (k === "const") { out.enum = [v]; out.type = typeof v === "boolean" ? "boolean" : "string"; continue; }
      if (k === "oneOf") { out.anyOf = v; continue; }
      out[k] = v;
    }
    if (Array.isArray(out.type)) {
      // ["string", "null"] → string + nullable
      const types = (out.type as string[]).filter((t) => t !== "null");
      out.type = types[0] ?? "string";
      if ((node.type as string[]).includes("null")) out.nullable = true;
    }
    return normalizeFreeForm(out);
  }) as Rec;
}

/** Anthropic tool の input_schema 向け(注記を外し、**自由形は 3 社と同じに狭める**) */
export function toAnthropic(canonical: Rec): Rec {
  return mapSchema(stripAnnotations(canonical), (node) => {
    const out: Rec = {};
    for (const [k, v] of Object.entries(node)) if (!ANNOTATIONS.has(k)) out[k] = v;
    return normalizeFreeForm(out);
  }) as Rec;
}

export function adaptSchema(provider: "openai" | "gemini" | "anthropic", canonical: Rec): Rec {
  switch (provider) {
    case "openai": return toOpenAIStrict(canonical);
    case "gemini": return toGemini(canonical);
    case "anthropic": return toAnthropic(canonical);
  }
}

function allowsNull(schema: unknown): boolean {
  if (!isRecord(schema)) return false;
  if (schema.const === null) return true;
  if (schema.type === "null") return true;
  if (Array.isArray(schema.type) && (schema.type as string[]).includes("null")) return true;
  for (const key of ["oneOf", "anyOf"]) if (Array.isArray(schema[key]) && (schema[key] as unknown[]).some(allowsNull)) return true;
  return false;
}

/**
 * 正本が null を許さない欄に入った null を落とす(strict の写しの「無い」の表し方を、正本の「欄が無い」に戻す)。
 * 正本が null を許す欄(observations[].value・menuMatch)の null はそのまま。
 */
export function dropNullsNotAllowed(json: unknown, canonical: unknown): unknown {
  if (Array.isArray(json)) {
    const itemSchema = isRecord(canonical) ? canonical.items : undefined;
    return json.map((item) => dropNullsNotAllowed(item, itemSchema));
  }
  if (!isRecord(json)) return json;
  const props = isRecord(canonical) && isRecord(canonical.properties) ? canonical.properties : {};
  const out: Rec = {};
  for (const [k, v] of Object.entries(json)) {
    const sub = props[k];
    if (v === null && !allowsNull(sub)) continue;
    out[k] = dropNullsNotAllowed(v, sub);
  }
  return out;
}

/** 写しの中に残ってはいけない語(試験が見る) */
export function forbiddenKeywords(provider: "openai" | "gemini" | "anthropic", schema: unknown): string[] {
  const found = new Set<string>();
  const banned = provider === "openai" ? ["oneOf", "pattern", "minItems", "minimum", "maximum", "const"] : provider === "gemini" ? ["oneOf", "additionalProperties", "const", "pattern"] : ["$schema", "$id"];
  const walk = (x: unknown): void => {
    if (Array.isArray(x)) { x.forEach(walk); return; }
    if (!isRecord(x)) return;
    for (const [k, v] of Object.entries(x)) {
      if (banned.includes(k)) found.add(k);
      if (k === "properties" && isRecord(v)) { for (const p of Object.values(v)) walk(p); continue; }
      walk(v);
    }
  };
  walk(schema);
  return [...found].sort();
}
