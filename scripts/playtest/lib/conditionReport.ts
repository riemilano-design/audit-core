// STEP D3-COND(docs/STEP_D3-COND_PLAN_2026-09-15.md §3・§6)。条件式の判定を、diagnose.ts の出力の形にする。
// - `--events-cond` の 1 行(契約 diagnosis-condition v0.1。1 行 =(入力 1 件 × 定義 1 件)の判定。判定しない行は書かない)
// - `--cond-summary`(契約 diagnosis-condition-summary。1 人ぶんの集計)と、標準出力の条件式の節(条件ごとに status と「(仮)」を出す ― S-3)
// - 定義のディレクトリの読み込み・§7.2 の「落としたか」の材料(固定棋譜 JSON の ending・README の表を写した JSON)の読み込み(計画 §9 の N-4)
//
// 【このファイルがやること】判定と集計は lib/condition.ts を呼ぶだけ。ここは並べ方・ファイルの読み方・契約の欄を持つ
// 【このファイルが絶対にやらないこと】評価語・「3 件以上か」「20 局以上か」の判定語。全ての手の組の行を書くこと(D4 の Q-1)。人の名前を受けること(--person は記号だけ)

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import type { MetaLine } from "../invariants/types.js";
import {
  judgeCondition,
  loadCondition,
  userSideOf,
  type ConditionGameInput,
  type ConditionInput,
  type ConditionJudgement,
  type ConditionRowKind,
  type ConditionTally,
  type LoadedCondition,
  type LostByEnding,
  type Section72Match,
  type Within5,
} from "./condition.js";
import type { DiagnosisMoments } from "./diagnosisMoment.js";
import { validate, type JsonSchema } from "./eventSchema.js";
import type { FailureEvent } from "./failureEvent.js";
import type { Provenance } from "./failureEventSchema.js";
import { readDirtyState, type DirtyState, type GitState } from "./gitState.js";
import type { FixedKifuEnding } from "./kifuImport.js";
// 版の文字列は lib/schemaVersions.ts の 1 か所に置く(STEP D-SCREEN-2 の作法)
import { DIAGNOSIS_CONDITION_SCHEMA_VERSION, DIAGNOSIS_CONDITION_SUMMARY_SCHEMA_VERSION, KNOWN_DIAGNOSIS_CONDITION_SCHEMA_VERSIONS } from "./schemaVersions.js";

export const DIAGNOSIS_CONDITION_CONTRACT = "diagnosis-condition" as const;
export const DIAGNOSIS_CONDITION_SUMMARY_CONTRACT = "diagnosis-condition-summary" as const;
export type DiagnosisConditionSchemaVersion = (typeof KNOWN_DIAGNOSIS_CONDITION_SCHEMA_VERSIONS)[number];

/** 行の入力の種類(diagnosis-moment の eventClass に Failure Event を足した名前。全ての手の組は書かない) */
export type ConditionEventClass = "failureEvent" | "rise" | "maxDrop";

export type JudgedCondition = Exclude<ConditionJudgement, { state: "notJudged" }>;

/** `--events-cond` の 1 行。契約と版を先頭に、出どころ(Failure Event と同じ)を末尾に置く */
export interface DiagnosisConditionLine {
  contract: typeof DIAGNOSIS_CONDITION_CONTRACT;
  schemaVersion: typeof DIAGNOSIS_CONDITION_SCHEMA_VERSION;
  kifuId: string;
  eventClass: ConditionEventClass;
  branchPly: number;
  condition: ConditionTally["condition"];
  result: JudgedCondition;
  provenance: Provenance;
}

/** 1 局の判定の入力。並びは --events・--events-rise・--events-maxdrop のファイルの順(Failure Event → 上がり → 最大の下がり) */
export function conditionInputsOf(events: readonly FailureEvent[], moments: DiagnosisMoments): ConditionInput[] {
  return [
    ...events.map((row): ConditionInput => ({ kind: "failureEvent", row })),
    ...moments.rises.map((row): ConditionInput => ({ kind: "rise", row })),
    { kind: "maxDrop", row: moments.maxDrop },
  ];
}

function eventClassOf(input: ConditionInput): ConditionEventClass {
  if (input.kind === "pair") throw new Error("全ての手の組の行は --events-cond に書かない(D4 計画 Q-1)");
  return input.kind;
}

/** 入力 1 件ごとに、定義を並びの順に当てる。判定しない行(appliesTo の外・最大の下がりの状態の行)は書かない(計画 §2) */
export function conditionLinesOf(inputs: readonly ConditionInput[], conditions: readonly LoadedCondition[], provenance: Provenance): DiagnosisConditionLine[] {
  const lines: DiagnosisConditionLine[] = [];
  for (const input of inputs) {
    for (const loaded of conditions) {
      const result = judgeCondition(loaded.definition, input);
      if (result.state === "notJudged") continue;
      const { definition } = loaded;
      lines.push({
        contract: DIAGNOSIS_CONDITION_CONTRACT,
        schemaVersion: DIAGNOSIS_CONDITION_SCHEMA_VERSION,
        kifuId: input.row.kifuId,
        eventClass: eventClassOf(input),
        branchPly: (input.row as { branchPly: number }).branchPly,
        condition: { id: definition.id, label: definition.label, status: definition.status, definitionSha256: loaded.definitionSha256 },
        result,
        provenance,
      });
    }
  }
  return lines;
}

/** 1 局ぶんの集計の入力。本人の側は meta から、§7.2 の材料は読み込んだ表から kifuId で引く(無ければ「記録に無い」「載っていない」) */
export function conditionGameOf(input: {
  kifuId: string;
  meta: MetaLine | undefined;
  events: readonly FailureEvent[];
  moments: DiagnosisMoments;
  endings: ReadonlyMap<string, FixedKifuEnding | null | undefined> | undefined;
  listedResults: ReadonlyMap<string, "win" | "loss"> | undefined;
}): ConditionGameInput {
  return {
    kifuId: input.kifuId,
    userSide: userSideOf(input.meta),
    ending: input.endings?.get(input.kifuId),
    listedResult: input.listedResults?.get(input.kifuId) ?? null,
    events: input.events,
    rises: input.moments.rises,
    maxDrop: input.moments.maxDrop,
  };
}

// ---- 読み込み ----

/** 定義のディレクトリの `*.ts`(`*.test.ts`・`*.d.ts` を除く)をファイル名の順に読む。1 つも無い・同じ id が 2 つあれば止める */
export async function loadConditionsFromDir(dir: string): Promise<LoadedCondition[]> {
  const files = readdirSync(dir)
    .filter((name) => name.endsWith(".ts") && !name.endsWith(".test.ts") && !name.endsWith(".d.ts"))
    .sort();
  if (files.length === 0) throw new Error(`--conditions のディレクトリに定義のファイル(*.ts)が無い: ${dir}`);
  const loaded: LoadedCondition[] = [];
  for (const file of files) loaded.push(await loadCondition(path.join(dir, file)));
  assertDistinctConditionIds(loaded);
  return loaded;
}

export function assertDistinctConditionIds(conditions: readonly LoadedCondition[]): void {
  const seen = new Set<string>();
  for (const { definition } of conditions) {
    if (seen.has(definition.id)) throw new Error(`同じ id の条件式の定義が 2 つある: ${definition.id}`);
    seen.add(definition.id);
  }
}

function isEnding(value: unknown): value is FixedKifuEnding | null {
  if (value === null) return true;
  if (typeof value !== "object") return false;
  const ending = value as { kind?: unknown; ply?: unknown };
  return typeof ending.kind === "string" && (typeof ending.ply === "number" || (ending.kind === "unreadable" && ending.ply === null));
}

/**
 * 固定棋譜 JSON のディレクトリ(`*.json`)から、id → ending を読む(計画 §9 の N-4)。`ending` のキーが無い棋譜は undefined(どちらも「記録に無い」)。
 * **手(moves)は読まない。**id が無い・同じ id が 2 つ・ending の形が違えば止める
 */
export function readKifuEndings(dir: string): Map<string, FixedKifuEnding | null | undefined> {
  const endings = new Map<string, FixedKifuEnding | null | undefined>();
  for (const file of readdirSync(dir).filter((name) => name.endsWith(".json")).sort()) {
    const data = JSON.parse(readFileSync(path.join(dir, file), "utf-8")) as Record<string, unknown>;
    if (typeof data.id !== "string" || data.id.length === 0) throw new Error(`--kifu-dir の ${file} に id が無い`);
    if (endings.has(data.id)) throw new Error(`--kifu-dir に同じ id の棋譜が 2 つある: ${data.id}`);
    if (!Object.hasOwn(data, "ending")) {
      endings.set(data.id, undefined);
      continue;
    }
    if (!isEnding(data.ending)) throw new Error(`--kifu-dir の ${file} の ending が固定棋譜 JSON の形でない`);
    endings.set(data.id, data.ending);
  }
  return endings;
}

/** README の勝ち負けの表を写した JSON(`{ "<kifuId>": "win" | "loss" }`)を読む。ほかの値があれば止める */
export function readListedResults(filePath: string): Map<string, "win" | "loss"> {
  const data = JSON.parse(readFileSync(filePath, "utf-8")) as unknown;
  if (typeof data !== "object" || data === null || Array.isArray(data)) throw new Error("--listed-results は { kifuId: \"win\" | \"loss\" } の JSON にしてください");
  const results = new Map<string, "win" | "loss">();
  for (const [kifuId, value] of Object.entries(data)) {
    if (value !== "win" && value !== "loss") throw new Error(`--listed-results の ${kifuId} の値が win・loss でない`);
    results.set(kifuId, value);
  }
  return results;
}

/** `--person` は名前でない記号だけを受ける(D4 計画 S-8 の `p1`・`p2` の形。人の名前を出力に書かない) */
export const PERSON_LABEL_PATTERN = /^p[0-9]+$/;
export function assertPersonLabel(label: string): void {
  if (!PERSON_LABEL_PATTERN.test(label)) throw new Error("--person は名前でない記号(p1・p2 の形)にしてください");
}

// ---- 集計の JSON ----

export interface DiagnosisConditionSummary {
  contract: typeof DIAGNOSIS_CONDITION_SUMMARY_CONTRACT;
  schemaVersion: typeof DIAGNOSIS_CONDITION_SUMMARY_SCHEMA_VERSION;
  person: string;
  /** 渡した記録(根からの相対)。`counted` が false の記録は集計に入れていない(error 行・例外) */
  inputs: Array<{ path: string; sha256: string; kifuId: string; counted: boolean }>;
  /** §7.2 の材料の出どころ(根からの相対)。渡されていなければ null */
  sources: { kifuDir: string | null; listedResults: string | null };
  analysis: { gitHead: string | null; dirty: DirtyState };
  conditions: ConditionTally[];
}

export function conditionSummaryOf(input: {
  person: string;
  inputs: DiagnosisConditionSummary["inputs"];
  sources: DiagnosisConditionSummary["sources"];
  analysisGit: Pick<GitState, "gitHead" | "dirty">;
  tallies: readonly ConditionTally[];
}): DiagnosisConditionSummary {
  return {
    contract: DIAGNOSIS_CONDITION_SUMMARY_CONTRACT,
    schemaVersion: DIAGNOSIS_CONDITION_SUMMARY_SCHEMA_VERSION,
    person: input.person,
    inputs: input.inputs,
    sources: input.sources,
    analysis: { gitHead: input.analysisGit.gitHead, dirty: readDirtyState({ dirty: input.analysisGit.dirty }) },
    conditions: [...input.tallies],
  };
}

// ---- 標準出力の節 ----

const KIND_LABELS: Record<ConditionRowKind, string> = { failureEvent: "Failure Event", rise: "上がり", maxDropPair: "最大の下がりの組", pair: "全ての手の組" };
const WITHIN5_LABELS: Record<Within5, string> = { present: "あり", absent: "なし", windowShort: "窓が足りない" };
const LOST_LABELS: Record<LostByEnding, string> = { lost: "落とした", notLost: "落としていない", undetermined: "決まらない(終局の種類)", notInRecord: "記録に無い" };
const LISTED_LABELS: Record<Section72Match["listedResult"], string> = { win: "勝ち", loss: "負け", notListed: "載っていない" };
const AGREEMENT_LABELS: Record<Section72Match["agreement"], string> = { agree: "一致", mismatch: "食い違い", notComparable: "比べない" };

/** 条件式の節。**条件ごとに label(必ず「(仮)」を含む)と status を見出しに出す**(計画 S-3)。評価語・判定語を足さない */
export function renderConditionSection(person: string, tallies: readonly ConditionTally[], sources: DiagnosisConditionSummary["sources"]): string[] {
  const lines: string[] = [];
  lines.push("## 条件式の判定(STEP D3-COND。該当・非該当・判定不能の数だけ)");
  lines.push("");
  lines.push("- **条件式の定義は判断的知識。status が draft の定義は人間の承認の前の仮置きで、名前に必ず「(仮)」を付ける。**「3 件以上か」「20 局以上か」は数を並べるだけで、判定しない");
  lines.push("- 分母は該当 + 非該当。判定不能は分母に入れず、欄と理由を並べる。同じ組 (kifuId, branchPly) は 1 回だけ数える(Failure Event → 最大の下がりの組 → 上がりの順に先に見た行)");
  const games = tallies[0]?.games ?? { total: 0, sente: 0, gote: 0 };
  lines.push(`- 人: ${person}(--person の記号)。数えた局: ${games.total}(先手 ${games.sente}・後手 ${games.gote})。error 行の記録・数えられなかった記録は入れていない`);
  lines.push(`- 終局の出どころ: ${sources.kifuDir ?? "渡されていない(すべて「記録に無い」)"}。README の表の出どころ: ${sources.listedResults ?? "渡されていない(すべて「載っていない」)"}`);
  lines.push("");
  for (const tally of tallies) {
    const { condition, overall, section72 } = tally;
    lines.push(`### ${condition.label}(id: ${condition.id}・status: ${condition.status}・definitionSha256: ${condition.definitionSha256.slice(0, 12)})`);
    lines.push("");
    lines.push("| 数えた入力の種類 | 該当 | 非該当 | 分母(該当 + 非該当) | 判定不能 | 判定しない行(対象外の種類) | 判定しない行(最大の下がりの状態の行) | 同じ組で数えなかった行 | 該当があった局 |");
    lines.push("|---|---|---|---|---|---|---|---|---|");
    lines.push(
      `| ${tally.countedRowKinds.map((kind) => KIND_LABELS[kind]).join("・") || "無し"} | ${overall.match} | ${overall.noMatch} | ${overall.denominator} | ${overall.undecidable} | ${overall.notJudged.kindNotApplied} | ${overall.notJudged.maxDropState} | ${overall.duplicatePairsSkipped} | ${overall.gamesWithMatch} |`,
    );
    lines.push("");
    lines.push(`- 判定不能の内訳: ${overall.undecidableReasons.length === 0 ? "無し" : overall.undecidableReasons.map((entry) => `${entry.path}(${entry.reason})${entry.rows} 行`).join("、")}`);
    lines.push(`- 該当: ${overall.matches.length === 0 ? "無し" : overall.matches.map((match) => `${match.kifuId} 分岐点 ${match.branchPly}(${KIND_LABELS[match.rowKind]})`).join("、")}`);
    if (!section72.failureEventApplied) {
      lines.push("- §7.2 用の列: この定義は Failure Event に当てない");
      lines.push("");
      continue;
    }
    lines.push(`- §7.2 用の列(kinds に cpDrop か mateDrop がある Failure Event だけ): 該当 ${section72.match}・非該当 ${section72.noMatch}・判定不能 ${section72.undecidable}・該当があった局 ${section72.gamesWithMatch}`);
    if (section72.matches.length > 0) {
      lines.push("");
      lines.push("| 対象 | 分岐点 | 当たり方 | 5 手以内の王手・詰み | 終局から | README の表 | 並べた結果 |");
      lines.push("|---|---|---|---|---|---|---|");
      for (const match of section72.matches) {
        lines.push(
          `| ${match.kifuId} | ${match.branchPly} | ${match.kinds.join("+")} | ${WITHIN5_LABELS[match.within5]} | ${LOST_LABELS[match.lostByEnding]} | ${LISTED_LABELS[match.listedResult]} | ${AGREEMENT_LABELS[match.agreement]} |`,
        );
      }
    }
    lines.push("");
  }
  return lines;
}

// ---- スキーマ ----

export function loadDiagnosisConditionSchema(version: DiagnosisConditionSchemaVersion = DIAGNOSIS_CONDITION_SCHEMA_VERSION): JsonSchema {
  return JSON.parse(readFileSync(new URL(`../schemas/diagnosis-condition.v${version}.schema.json`, import.meta.url), "utf-8")) as JsonSchema;
}

/** 1 行(JSON.parse した値)を契約のスキーマに照らす。誤りを 1 件 1 行で返す(空なら通った) */
export function validateDiagnosisConditionLine(line: unknown, schema: JsonSchema = loadDiagnosisConditionSchema()): string[] {
  return validate(line, schema);
}
