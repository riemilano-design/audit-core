// STEP JSON v0(docs/STEP_JSON-V0_PLAN_2026-09-15.md)・STEP JSON v0.2(docs/STEP_JSON-V0.2_PLAN_2026-09-15.md)。
// Failure Event の 1 行の版と、版つきの行を作る関数、スキーマの読み込み、出どころ(provenance)の組み立て。
//
// 【値は変えない】D1 の lib が作る FailureEvent の先頭に schemaVersion を、末尾に provenance を足すだけ(v0 計画 J-2・v0.2 計画 2.1)。
// 【置き場所】v0 計画 6.1 は lib/failureEvent.ts に置く予定だった。D3 が同じファイルを触っていたので、衝突を避けて
// このファイルに分けた(計画書 §10.1 に書いた)。
// 【版を上げるとき】スキーマのファイルを版ごとに 1 つ増やし、古い版のファイルは消さない(v0 計画 3.2)。
// 【出どころは推測しない】評価関数の識別は人が渡した文(`--evaluator`)をそのまま写す。`enginePath` から推測しない(P-43・K-4)。
// 【絶対パスは書かない】パスはリポジトリの根からの相対にする(v0.2 計画 K-2)。ホームディレクトリのユーザー名を行に出さない。

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import type { MetaLine } from "../invariants/types.js";
import { validate, type JsonSchema } from "./eventSchema.js";
import type { DiagnosisRule, FailureEvent } from "./failureEvent.js";
import { readDirtyState, type DirtyState, type GitState } from "./gitState.js";

export const FAILURE_EVENT_SCHEMA_VERSION = "0.2" as const;
/** スキーマのファイルがある版(古い版のファイルは消さない) */
export const KNOWN_SCHEMA_VERSIONS = ["0.1", "0.2"] as const;
export type SchemaVersion = (typeof KNOWN_SCHEMA_VERSIONS)[number];

/** 出どころに写す meta の欄。meta に無かった欄は `unrecordedKeys` に名前を並べる(v0.2 計画 K-3) */
export const PROVENANCE_META_KEYS = ["gitHead", "dirty", "enginePath", "searchMode", "nodes", "threads"] as const;

export interface ProvenanceMeta {
  /** 記録を取ったときのコード。null = 取れなかった、または meta に欄が無い(`unrecordedKeys` で分かる) */
  gitHead: string | null;
  /** 記録を取ったときの汚れ(DirtyState の 4 値) */
  dirty: DirtyState;
  /** 評価(再生)に使ったエンジン。根からの相対に直す */
  enginePath: string | null;
  searchMode: string | null;
  /** 0 = 時間で打ち切る探索(`searchMode` が `"movetime"`。replay.ts `--nodes 0`)。null にしない ― `searchMode` と組で読む */
  nodes: number | null;
  threads: number | null;
  unrecordedKeys: string[];
}

export interface Provenance {
  record: { path: string; sha256: string; meta: ProvenanceMeta | null };
  /** 人が渡した評価関数の識別。**確かめていない自己申告**。null = 渡されていない */
  evaluator: { declared: string | null };
  /** Failure Event を組み立てたとき(diagnose.ts を回したとき)のコードと規則の値 */
  analysis: {
    gitHead: string | null;
    dirty: DirtyState;
    rule: { advantageCp: number; dropCp: number; windowPlies: number; focusDropCp: number; notEvaluationCp: number };
  };
}

/** `--events` の 1 行(版つき)。版の欄は先頭、出どころは末尾に置く */
export type FailureEventLine = { schemaVersion: typeof FAILURE_EVENT_SCHEMA_VERSION } & FailureEvent & { provenance: Provenance };

/** 記録のファイルのバイト列の sha256(小文字 64 桁)。diagnose.ts と試験が同じ関数を使う */
export function recordSha256(bytes: Uint8Array): string {
  return createHash("sha256").update(bytes).digest("hex");
}

export function toEventLine(event: FailureEvent, provenance: Provenance): FailureEventLine {
  return { schemaVersion: FAILURE_EVENT_SCHEMA_VERSION, ...event, provenance };
}

/**
 * 出どころに書くパス。**`repoRoot` の中なら根からの相対(区切りは /)**。
 * 外なら、パスの中の `apps/server/engine/` から後ろ(エンジンの置き場所。別の作業ツリーで記録したエンジンでも `nnue/` の区別を残す)、
 * それも無ければファイル名だけ。**絶対パスは返さない**(v0.2 計画 K-2)。
 */
export function pathForProvenance(filePath: string, repoRoot: string): string {
  const absolute = path.resolve(filePath);
  const relative = path.relative(path.resolve(repoRoot), absolute);
  const outside = relative === "" || relative === ".." || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative);
  if (!outside) return relative.split(path.sep).join("/");
  const posix = absolute.split(path.sep).join("/");
  const engineAt = posix.lastIndexOf("/apps/server/engine/");
  if (engineAt !== -1) return posix.slice(engineAt + 1);
  return path.basename(absolute);
}

export function provenanceMetaOf(meta: MetaLine | undefined, repoRoot: string): ProvenanceMeta | null {
  if (meta === undefined) return null;
  const raw = meta as unknown as Record<string, unknown>;
  const stringOf = (key: string): string | null => (typeof raw[key] === "string" ? (raw[key] as string) : null);
  const integerOf = (key: string): number | null => (typeof raw[key] === "number" ? (raw[key] as number) : null);
  const enginePath = stringOf("enginePath");
  return {
    gitHead: stringOf("gitHead"),
    dirty: readDirtyState(meta),
    enginePath: enginePath === null ? null : pathForProvenance(enginePath, repoRoot),
    searchMode: stringOf("searchMode"),
    nodes: integerOf("nodes"),
    threads: integerOf("threads"),
    unrecordedKeys: PROVENANCE_META_KEYS.filter((key) => !Object.hasOwn(raw, key)),
  };
}

export interface ProvenanceInput {
  recordPath: string;
  recordSha256: string;
  meta: MetaLine | undefined;
  /** `--evaluator` の文。渡されなければ null(推測しない) */
  evaluator: string | null;
  analysisGit: Pick<GitState, "gitHead" | "dirty">;
  rule: DiagnosisRule;
  notEvaluationCp: number;
  repoRoot: string;
}

export function buildProvenance(input: ProvenanceInput): Provenance {
  return {
    record: {
      path: pathForProvenance(input.recordPath, input.repoRoot),
      sha256: input.recordSha256,
      meta: provenanceMetaOf(input.meta, input.repoRoot),
    },
    evaluator: { declared: input.evaluator },
    analysis: {
      gitHead: input.analysisGit.gitHead,
      dirty: readDirtyState({ dirty: input.analysisGit.dirty }),
      rule: {
        advantageCp: input.rule.advantageCp,
        dropCp: input.rule.dropCp,
        windowPlies: input.rule.windowPlies,
        focusDropCp: input.rule.focusDropCp,
        notEvaluationCp: input.notEvaluationCp,
      },
    },
  };
}

/** 版のスキーマのファイル(scripts/playtest/schemas/failure-event.v<版>.schema.json) */
export function failureEventSchemaUrl(version: SchemaVersion = FAILURE_EVENT_SCHEMA_VERSION): URL {
  return new URL(`../schemas/failure-event.v${version}.schema.json`, import.meta.url);
}

export function loadFailureEventSchema(version: SchemaVersion = FAILURE_EVENT_SCHEMA_VERSION): JsonSchema {
  return JSON.parse(readFileSync(failureEventSchemaUrl(version), "utf-8")) as JsonSchema;
}

/**
 * 1 行(JSON.parse した値)をスキーマに照らす。誤りを 1 件 1 行で返す(空なら通った)。
 * スキーマを渡さなければ、今の版のスキーマで見る(行の schemaVersion で選ばない ― 違う版の行は落ちるのが正しい)。
 */
export function validateFailureEventLine(line: unknown, schema: JsonSchema = loadFailureEventSchema()): string[] {
  return validate(line, schema);
}
