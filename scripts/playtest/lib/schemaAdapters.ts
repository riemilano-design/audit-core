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
    return out;
  }) as Rec;
}

/** Anthropic tool の input_schema 向け(正本のまま。注記だけ外す) */
export function toAnthropic(canonical: Rec): Rec {
  return mapSchema(stripAnnotations(canonical), (node) => {
    const out: Rec = {};
    for (const [k, v] of Object.entries(node)) if (!ANNOTATIONS.has(k)) out[k] = v;
    return out;
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
