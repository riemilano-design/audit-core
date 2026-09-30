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
import { aggregateAgreementProblems, type AggregateRow } from "./observationAggregates.js";
import { packetRefPathProblems } from "./packetRef.js";

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
 * **持ち時間が 25 局で 1 つか**(P-3。設計セッションの提案 → 束 C で受けた)。
 * 局ごとに違う持ち時間の材料を混ぜると、時間の数(長考・速い手)が**比べられない数の寄せ集め**になる。
 * 混ざっているなら、それを言う(勝手に代表値を選ばない)。
 */
export function timeLimitProblems(facts: unknown): string[] {
  const games = ((facts as { games?: unknown })?.games ?? []) as { gameId?: unknown; timeLimitSec?: unknown }[];
  if (!Array.isArray(games) || games.length === 0) return [];
  const missing = games.filter((game) => typeof game.timeLimitSec !== "number").map((game) => String(game.gameId));
  const problems: string[] = [];
  if (missing.length > 0) problems.push(`持ち時間: ${missing.length} 局に持ち時間が無い(例 ${missing.slice(0, 3).join("・")})`);
  const limits = new Set(games.filter((game) => typeof game.timeLimitSec === "number").map((game) => game.timeLimitSec as number));
  if (limits.size > 1) problems.push(`持ち時間: 局によって違う(${[...limits].sort((a, b) => a - b).join(" / ")} 秒) ― 時間の数を 1 つの母集団として出せない`);
  return problems;
}

/** 25 局に共通の持ち時間(1 つでなければ undefined) */
export function commonTimeLimitSec(facts: unknown): number | undefined {
  const games = ((facts as { games?: unknown })?.games ?? []) as { timeLimitSec?: unknown }[];
  const limits = new Set(games.filter((game) => typeof game.timeLimitSec === "number").map((game) => game.timeLimitSec as number));
  return limits.size === 1 ? [...limits][0] : undefined;
}

/**
 * **packet と request が同じ範囲を指しているか**(R-1・P-3。設計セッションの提案 → 束 C で受けた)。
 * **packet は request を参照しない**(向きは一方通行)ので、突き合わせはこの外の関数でやる。
 */
export function requestAgreementProblems(packet: unknown, request: unknown): string[] {
  const problems: string[] = [];
  const facts = (packet as { facts?: unknown })?.facts;
  const games = ((facts as { games?: unknown })?.games ?? []) as unknown[];
  const scope = (request as { requestedScope?: { games?: unknown; timeLimitSec?: unknown } })?.requestedScope;
  if (scope === undefined) return ["範囲: request に requestedScope が無い"];
  if (scope.games !== games.length) problems.push(`範囲: request の局数が ${String(scope.games)}(packet は ${games.length} 局)`);
  const limit = commonTimeLimitSec(facts);
  if (limit === undefined) problems.push("範囲: packet の持ち時間が 1 つに決まらないので request と突き合わせられない");
  else if (scope.timeLimitSec !== limit) problems.push(`範囲: request の持ち時間が ${String(scope.timeLimitSec)} 秒(packet の局は ${limit} 秒)`);
  const packetRef = (packet as { customerRef?: unknown })?.customerRef;
  const requestRef = (request as { customerRef?: unknown })?.customerRef;
  if (packetRef !== requestRef) problems.push(`範囲: 顧客の符号が違う(packet ${String(packetRef)} / request ${String(requestRef)})`);
  return problems;
}

/**
 * packet の検査の入口(後の束・検証器はここを呼ぶ)。**schema の形 + 集計の行の形 + 集計の筋 + 持ち時間 + 封の符号**を
 * 1 つに束ねる。空なら通った。
 */
export function observationPacketProblems(packet: unknown, schema: JsonSchema = loadObservationPacketSchema()): string[] {
  const problems = validateObservationPacket(packet, schema);
  if (packet !== null && typeof packet === "object") {
    const record = packet as { aggregates?: unknown; facts?: unknown; packetId?: unknown };
    problems.push(...aggregateFormProblems(record.aggregates));
    if (Array.isArray(record.aggregates) && record.facts !== null && typeof record.facts === "object") {
      problems.push(...aggregateAgreementProblems(record.aggregates as AggregateRow[], record.facts as Record<string, unknown>));
    }
    problems.push(...timeLimitProblems(record.facts));
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

// ==================== packet の中の場所を引く(束 V-a。検証器の H-9 のため) ====================
//
// 【なぜここか】packet を読むのは自動化レーンの仕事(司令塔の境界。2026-09-30)。
//   **path の文法(正規表現)は実験席の `lib/packetRef.ts`** が持つ ― ここでは**引き当てだけ**をやる。
//   文法と引き当ての 2 つを同じ場所に置くと、**同じ規則が 2 か所に増える**(P-185 の型)。
// 【観測は 1 つの数を指す】司令塔の決定(2026-09-30): 集計の行を指す path は
//   `.numerator` / `.denominator` / `.value` の**どれかまで必ず書く**。
//   `aggregates.<id>` 単独は**引き当てない**(どの数を指しているか決まらない)。
//   **本編の印 `<!-- agg: id -->` は別** ― あちらは行を指すので id 単独でよい。
// 【黙って通さない】引き当てられない path は理由を返す(`undefined` を「値が無い」と混ぜない)。
// 【2026-09-30 の寄せ】文法の判定を自分でも書いていた(単独形を落とす・packet の外を落とす・形が読めない)。
//   R2 が `lib/packetRef.ts` に文法を 1 か所で置いたので、**`packetRefPathProblems` を呼ぶだけにした** ―
//   自分の側に残すと、文法を直したとき**こちらだけ古い判定で黙る**(P-185 の 2 か所の型)。

export type ResolvedPacketPath = { readonly ok: true; readonly value: unknown } | { readonly ok: false; readonly reason: string };

/** `facts.moves[3].usi` の形を鍵と添字の列にする(`[` `]` と `.` だけを見る。文法の判定はしない) */
function pathSteps(path: string): (string | number)[] | undefined {
  const steps: (string | number)[] = [];
  for (const part of path.split(".")) {
    if (part === "") return undefined;
    const match = /^([A-Za-z0-9_]+)((?:\[\d+\])*)$/.exec(part);
    if (match === null) return undefined;
    steps.push(match[1]!);
    for (const index of match[2]!.matchAll(/\[(\d+)\]/g)) steps.push(Number(index[1]));
  }
  return steps;
}

/**
 * packet の中の場所を引く。**集計の行は数の欄まで書かせる**(上のコメントの決定)。
 * 事実の行は `facts.<列>[n].<欄>`(`facts.recognition.rows[n].<欄>` も同じ形で引ける)。
 */
export function resolvePacketPath(packet: unknown, path: string): ResolvedPacketPath {
  if (packet === null || typeof packet !== "object") return { ok: false, reason: "packet が無い" };
  const record = packet as Record<string, unknown>;
  // 文法は実験席の 1 か所(単独形・packet の外・読めない形はここで落ちる)
  const grammar = packetRefPathProblems(path);
  if (grammar.length > 0) return { ok: false, reason: grammar[0]! };
  const steps = pathSteps(path);
  if (steps === undefined) return { ok: false, reason: `path の形が読めない: ${path}` };
  const head = steps[0];

  if (head === "aggregates") {
    const last = steps[steps.length - 1] as string;
    const id = steps.slice(1, -1).join(".");
    const rows = record.aggregates;
    if (!Array.isArray(rows)) return { ok: false, reason: "packet に aggregates が無い" };
    const row = (rows as Record<string, unknown>[]).find((candidate) => candidate.id === id);
    if (row === undefined) return { ok: false, reason: `集計に ${id} の行が無い` };
    if (!Object.hasOwn(row, last)) return { ok: false, reason: `集計の ${id} に ${last} が無い(分数の行と単独の数の行を取り違えていないか)` };
    return { ok: true, value: row[last] };
  }

  let current: unknown = record;
  const walked: string[] = [];
  for (const step of steps) {
    walked.push(String(step));
    if (typeof step === "number") {
      if (!Array.isArray(current)) return { ok: false, reason: `${walked.join(".")} は列でない` };
      if (step >= current.length) return { ok: false, reason: `${walked.join(".")} は列の外(長さ ${current.length})` };
      current = current[step];
      continue;
    }
    if (current === null || typeof current !== "object" || Array.isArray(current)) {
      return { ok: false, reason: `${walked.join(".")} を引けない` };
    }
    if (!Object.hasOwn(current as Record<string, unknown>, step)) {
      return { ok: false, reason: `${walked.join(".")} が packet に無い` };
    }
    current = (current as Record<string, unknown>)[step];
  }
  return { ok: true, value: current };
}
