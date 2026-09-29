// 次世代パイプライン Phase A の束 A(計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §8。正本 NEXTGEN_PIPELINE_BRIEF_2026-09-29.md)。
// Observation Packet と Observation Request の**契約の読み込み・検証・封の符号**だけを持つ。
//
// 【この束では中身を組まない】materials から facts・aggregates を作るのは束 B・C。ここは器の検査だけ。
// 【外部ライブラリを使わない】検証は lib/eventSchema.ts(JSON Schema の小さな部分集合)。
//   そのため schema は **辞書ではなく配列 + id** で書く($ref・patternProperties・additionalProperties にスキーマ、を使わない)。
// 【顧客の実名を packet に入れない】`customerRef` は出力フォルダの符号だけ(schema の pattern が半角小文字に縛る)。
//   理由: packet は 3 席の LLM(外部 API)への入力になる ― 実名が外へ出る経路を入口で閉じる(計画 §2.5)。
// 【封】`packetId` は facts + aggregates を**鍵の順にそろえて**取った sha256 の先頭 16。
//   鍵の並びが変わっても同じ値になり、**中身が 1 つ変われば変わる**(試験で固定)。材料の sha256 は provenance.inputs。
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { validate, type JsonSchema } from "./eventSchema.js";

export const OBSERVATION_PACKET_CONTRACT = "observation-packet" as const;
export const OBSERVATION_REQUEST_CONTRACT = "observation-request" as const;
/** 契約の版。**版を上げるときはファイルを 1 つ増やし、古い版のファイルは消さない**(既存の契約と同じ流儀) */
export const OBSERVATION_PACKET_SCHEMA_VERSION = "0.1" as const;
export const OBSERVATION_REQUEST_SCHEMA_VERSION = "0.1" as const;

export function observationPacketSchemaUrl(version: string = OBSERVATION_PACKET_SCHEMA_VERSION): URL {
  return new URL(`../schemas/observation-packet.v${version}.schema.json`, import.meta.url);
}

export function observationRequestSchemaUrl(version: string = OBSERVATION_REQUEST_SCHEMA_VERSION): URL {
  return new URL(`../schemas/observation-request.v${version}.schema.json`, import.meta.url);
}

export function loadObservationPacketSchema(version: string = OBSERVATION_PACKET_SCHEMA_VERSION): JsonSchema {
  return JSON.parse(readFileSync(observationPacketSchemaUrl(version), "utf-8")) as JsonSchema;
}

export function loadObservationRequestSchema(version: string = OBSERVATION_REQUEST_SCHEMA_VERSION): JsonSchema {
  return JSON.parse(readFileSync(observationRequestSchemaUrl(version), "utf-8")) as JsonSchema;
}

/**
 * packet をスキーマに照らす。誤りを 1 件 1 行で返す(空なら通った)。
 * **スキーマを渡さなければ今の版で見る**(packet の schemaVersion で選ばない ― 違う版の packet は落ちるのが正しい)。
 */
export function validateObservationPacket(packet: unknown, schema: JsonSchema = loadObservationPacketSchema()): string[] {
  return validate(packet, schema);
}

export function validateObservationRequest(request: unknown, schema: JsonSchema = loadObservationRequestSchema()): string[] {
  return validate(request, schema);
}

/**
 * 集計の行の**形**の検査(分数か単独の数か、ちょうど 1 つ)。
 *
 * 【なぜ schema でなく道具で見るか】最初は `oneOf` の 2 変種で書いたが、**誤りの文が
 * 「oneOf の 0 個に合った」だけになり、行の中のどこが悪いのかが出ない**。
 * そうすると試験が「意図と別の理由で落ちても緑」になる(2026-09-30 に校正で見つけた)。
 * schema は平らにして欄を名指しさせ、**形だけをここで見る**。
 */
export function aggregateFormProblems(aggregates: unknown): string[] {
  if (!Array.isArray(aggregates)) return ["aggregates が配列でない"];
  const problems: string[] = [];
  aggregates.forEach((row, index) => {
    if (row === null || typeof row !== "object") {
      problems.push(`aggregates[${index}]: 行がオブジェクトでない`);
      return;
    }
    const at = `aggregates[${index}](${String((row as { id?: unknown }).id ?? "id なし")})`;
    const hasNumerator = Object.hasOwn(row, "numerator");
    const hasDenominator = Object.hasOwn(row, "denominator");
    const hasValue = Object.hasOwn(row, "value");
    const isFraction = hasNumerator || hasDenominator;
    if (isFraction && hasValue) problems.push(`${at}: 分数(numerator・denominator)と単独の数(value)が同じ行に在る`);
    if (!isFraction && !hasValue) problems.push(`${at}: 数が無い(numerator + denominator か value のどちらかが要る)`);
    if (hasNumerator !== hasDenominator) problems.push(`${at}: 分数の片方だけが在る(numerator ${hasNumerator ? "在り" : "無し"} / denominator ${hasDenominator ? "在り" : "無し"})`);
  });
  return problems;
}

/**
 * packet の検査の入口(後の束・検証器はここを呼ぶ)。**schema の形 + 集計の行の形 + 封の符号**を 1 つに束ねる。
 * 空なら通った。
 */
export function observationPacketProblems(packet: unknown, schema: JsonSchema = loadObservationPacketSchema()): string[] {
  const problems = validateObservationPacket(packet, schema);
  if (packet !== null && typeof packet === "object") {
    const record = packet as { aggregates?: unknown; facts?: unknown; packetId?: unknown };
    problems.push(...aggregateFormProblems(record.aggregates));
    problems.push(...packetIdProblems(record));
  }
  return problems;
}

/**
 * 鍵の順にそろえた JSON(封の符号を取るための正規形)。
 * **配列の順は変えない** ― 行の並びは事実の一部(局の順・手の順)なので、並べ替えたら別の packet。
 */
export function canonicalJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value !== null && typeof value === "object") {
    const entries = Object.keys(value as Record<string, unknown>)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson((value as Record<string, unknown>)[key])}`);
    return `{${entries.join(",")}}`;
  }
  return JSON.stringify(value) ?? "null";
}

/**
 * 封の符号。**facts と aggregates だけ**から取る(provenance の `generatedAt` を入れると、
 * 同じ事実から組んでも毎回変わって「材料が差し替わった」を見分けられなくなる)。
 */
export function packetIdOf(facts: unknown, aggregates: unknown): string {
  const canonical = canonicalJson({ aggregates, facts });
  return createHash("sha256").update(canonical, "utf-8").digest("hex").slice(0, 16);
}

/** packet の `packetId` が中身と合っているか(合っていれば空、違えば 1 行) */
export function packetIdProblems(packet: { packetId?: unknown; facts?: unknown; aggregates?: unknown }): string[] {
  const expected = packetIdOf(packet.facts, packet.aggregates);
  if (packet.packetId === expected) return [];
  return [`packetId が中身と合わない(封: ${String(packet.packetId)} / 中身から取った値: ${expected})`];
}
