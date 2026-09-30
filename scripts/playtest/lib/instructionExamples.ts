// 束 R4 ― 指示文に書いた**場所の例**を、実物の packet に当てて確かめる(司令塔の F-2・F-3。2026-09-30)。
//
// 【なぜ要るか】指示文は機械が読まない文書なので、例が間違っていても誰も落とさない。**席は例をまねる**ので、
//   引けない例を配ると席が引けない数を書き、H-9(実在の照合)で落ちる ― 席の失敗ではなく配った側の失敗になる。
//   実測(2026-09-30): 目で読んだ司令塔が見つけた誤りは 1 本、機械で当てたら 3 本だった。
// 【門は 2 段(司令塔の F-3)】**書き方の誤りは止める / 材料の薄さは警告にとどめる。**
//   例の欄名・集計の id・文法が違うのは配った側の誤りなので送らない。表が空・行番号が表の外・値が空なのは
//   その顧客の材料が薄いだけなので、警告にして続ける(**局数の少ない組で正しい packet が送れなくなるのを防ぐ**)。
// 【ここだけが packet を読む】席の出力の契約検査(seatOutput・integration)は packet を読まない ― 実在の照合は H-9(自動化レーン)。
//   この module は「配る前に指示文を検める」ためのもので、CLI(runSeats)からだけ呼ぶ。
import { resolvePacketPath } from "./observationPacket.js";
import { packetRefPathProblems } from "./packetRef.js";

type Rec = Record<string, unknown>;
function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

/** 指示文の中の「場所の例」= バッククォートで囲まれ `facts.` / `aggregates.` で始まり、穴(`<…>`)も空の添字(`[]`)も無いもの */
export function instructionExamplePaths(text: string): string[] {
  const found = new Set<string>();
  for (const match of text.matchAll(/`([^`]+)`/g)) {
    const token = match[1]!;
    if (!/^(facts|aggregates)\./.test(token)) continue;
    if (token.includes("<") || token.includes(" ") || token.includes("[]")) continue;
    found.add(token);
  }
  return [...found];
}

export type ExampleLevel = "ok" | "warn" | "error";
export interface ExampleCheck {
  path: string;
  level: ExampleLevel;
  reason?: string;
  value?: unknown;
}

/** `facts.…` の例が指す表(`facts.recognition.rows` は 2 段)。無ければ undefined */
function factsTableOf(packet: Rec, path: string): { name: string; rows: unknown } | undefined {
  const facts = isRecord(packet.facts) ? packet.facts : {};
  const parts = path.split(".");
  if (parts[1] === "recognition") {
    const recognition = isRecord(facts.recognition) ? facts.recognition : {};
    const key = (parts[2] ?? "").replace(/\[\d+\].*$/, "");
    return { name: `facts.recognition.${key}`, rows: recognition[key] };
  }
  const key = (parts[1] ?? "").replace(/\[\d+\].*$/, "");
  return { name: `facts.${key}`, rows: facts[key] };
}
function indexOf(path: string): number | undefined {
  const match = /\[(\d+)\]/.exec(path);
  return match === null ? undefined : Number(match[1]);
}
/** 値が「在るが空」か(材料の薄さ。止めずに警告) */
function isEmptyValue(value: unknown): boolean {
  return value === null || (Array.isArray(value) && value.length === 0) || value === "";
}

/**
 * 例 1 本を当てる。**level の分かれ方が門の規則そのもの**:
 * `error` = 書き方(文法・表の名前・集計の id・欄名)の誤り / `warn` = 材料の薄さ(表が空・行番号が表の外・値が空)。
 */
export function checkInstructionExample(path: string, packet: unknown): ExampleCheck {
  const grammar = packetRefPathProblems(path);
  if (grammar.length > 0) return { path, level: "error", reason: grammar[0]! };
  if (!isRecord(packet)) return { path, level: "error", reason: "packet が無い" };

  if (path.startsWith("aggregates.")) {
    const parts = path.split(".");
    const part = parts[parts.length - 1]!;
    const id = parts.slice(1, -1).join(".");
    const rows = Array.isArray(packet.aggregates) ? (packet.aggregates as Rec[]) : undefined;
    if (rows === undefined) return { path, level: "error", reason: "packet に aggregates が無い" };
    const row = rows.find((candidate) => candidate.id === id);
    if (row === undefined) return { path, level: "error", reason: `集計に ${id} の行が無い(例の id が実物と違う)` };
    if (!Object.hasOwn(row, part)) return { path, level: "error", reason: `集計の ${id} に ${part} が無い(分数の行と単独の数の行の取り違え)` };
    const value = row[part];
    if (isEmptyValue(value)) return { path, level: "warn", reason: `集計の ${id}.${part} は空(材料が薄い)`, value };
    return { path, level: "ok", value };
  }

  const table = factsTableOf(packet, path);
  if (table === undefined || !Array.isArray(table.rows)) {
    return { path, level: "error", reason: `${table?.name ?? path} という表が packet に無い(例の表の名前が実物と違う)` };
  }
  const rows = table.rows;
  if (rows.length === 0) return { path, level: "warn", reason: `${table.name} が空(この顧客の材料が薄い)` };
  const index = indexOf(path) ?? 0;
  if (index >= rows.length) return { path, level: "warn", reason: `${table.name} は ${rows.length} 行で、例の行番号 ${index} は表の外(少ない組)` };
  // 欄名の誤りと値の空を分ける: 同じ表の**在る行**で欄を引き直す(行番号が在る限り欄の有無は行から分かる)
  const resolved = resolvePacketPath(packet, path);
  const column = path.split(".").pop()!;
  const row = rows[index];
  if (!isRecord(row) || !Object.hasOwn(row, column)) {
    return { path, level: "error", reason: `${table.name} の行に ${column} の欄が無い(例の欄名が実物と違う)` };
  }
  if (!resolved.ok) return { path, level: "error", reason: resolved.reason };
  if (isEmptyValue(resolved.value)) return { path, level: "warn", reason: `${path} は空(材料が薄い)`, value: resolved.value };
  return { path, level: "ok", value: resolved.value };
}

export interface InstructionExampleReport {
  checks: ExampleCheck[];
  errors: string[];
  warnings: string[];
}

/**
 * 指示文 1 本を検める。`minExamples` を満たさないのは**誤り**(例が消えた指示文を黙って配らない)。
 * 返す `errors` が空でなければ CLI は送らない。`warnings` は出して続ける。
 */
export function instructionExampleReport(text: string, packet: unknown, opts: { label: string; minExamples?: number }): InstructionExampleReport {
  const paths = instructionExamplePaths(text);
  const checks = paths.map((path) => checkInstructionExample(path, packet));
  const errors = checks.filter((c) => c.level === "error").map((c) => `${opts.label}: 例「${c.path}」が引けない ― ${c.reason ?? ""}`);
  const warnings = checks.filter((c) => c.level === "warn").map((c) => `${opts.label}: 例「${c.path}」― ${c.reason ?? ""}`);
  const min = opts.minExamples ?? 0;
  if (paths.length < min) errors.push(`${opts.label}: 場所の例が ${paths.length} 本しか無い(${min} 本以上を書く)`);
  return { checks, errors, warnings };
}
