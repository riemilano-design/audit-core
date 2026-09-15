// STEP JSON v0(docs/STEP_JSON-V0_PLAN_2026-09-15.md)・STEP JSON v0.2(docs/STEP_JSON-V0.2_PLAN_2026-09-15.md)。
// Failure Event の 1 行の版と、版つきの行を作る関数、スキーマの読み込み、出どころ(provenance)の組み立て。
//
// 【値は変えない】D1 の lib が作る FailureEvent の先頭に schemaVersion を、末尾に provenance を足すだけ(v0 計画 J-2・v0.2 計画 2.1)。
// 【置き場所】v0 計画 6.1 は lib/failureEvent.ts に置く予定だった。D3 が同じファイルを触っていたので、衝突を避けて
// このファイルに分けた(計画書 §10.1 に書いた)。
// 【版を上げるとき】スキーマのファイルを版ごとに 1 つ増やし、古い版のファイルは消さない(v0 計画 3.2)。
// 【出どころは推測しない】評価関数の識別は人が渡した文(`--evaluator`)をそのまま写す。`enginePath` から推測しない(P-43・K-4)。
// 【絶対パスは書かない】パスはリポジトリの根からの相対にする(v0.2 計画 K-2)。ホームディレクトリのユーザー名を行に出さない。
// 【記録の meta の 7 欄】STEP JSON V0.3-META(docs/STEP_JSON-V0.3-META_PLAN_2026-09-15.md)。そろえの組・打ち切りの組を、スキーマ v0.3 の 7 変種と同じ規則で読んで写す。
// 無い欄はキーを出さず、記録していなければ unrecordedKeys に名前を並べる(false を書かない ― 計画 D-1・K-1)。どの変種にも合わない meta は写さずに例外(K-3)。
// 【実戦の続きと読み筋】STEP D2(docs/STEP_D2_PLAN_2026-09-15.md)。スキーマ v0.4 で、FailureEvent の `counterfactual` をそのまま行に入れる
// (consequences の後。v0.3 に欄を足しただけ = MINOR。スキーマのファイルは v0.3 から道具で作り、v0.1〜v0.3 のファイルは変えていない)。
// 【玉の区域の数と形勢の状態】STEP D2.5(docs/STEP_D2.5_PLAN_2026-09-15.md)。スキーマ v0.5 で trigger.positionFacts・branch.standingPair・counterfactual の positionFactsEnd と差・
// 出どころの規則(standing・positionFacts)を足した(欄を足しただけ = MINOR。スキーマのファイルは v0.4 から道具で作り、v0.1〜v0.4 のファイルは変えていない)。

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import type { MetaLine } from "../invariants/types.js";
import { validate, type JsonSchema } from "./eventSchema.js";
import type { DiagnosisRule, FailureEvent } from "./failureEvent.js";
import type { PositionFactsRules } from "./positionFacts.js";
import type { StandingBounds } from "./standing.js";
import { readDirtyState, type DirtyState, type GitState } from "./gitState.js";
import type { ScreenMeta } from "./rescreen.js";
// 版の文字列とスキーマのファイルがある版の並びは lib/schemaVersions.ts の 1 か所に置く(STEP D-SCREEN-2。司令塔 e3 の決定)
import { FAILURE_EVENT_SCHEMA_VERSION, KNOWN_SCHEMA_VERSIONS } from "./schemaVersions.js";

export { FAILURE_EVENT_SCHEMA_VERSION, KNOWN_SCHEMA_VERSIONS };
export type SchemaVersion = (typeof KNOWN_SCHEMA_VERSIONS)[number];

/** 出どころに写す meta の欄(v0.2)。meta に無かった欄は `null` にし、`unrecordedKeys` に名前を並べる(v0.2 計画 K-3) */
export const PROVENANCE_META_KEYS = ["gitHead", "dirty", "enginePath", "searchMode", "nodes", "threads"] as const;
/**
 * STEP JSON V0.3-META で足した、記録の meta の 7 欄(計画 2.1。並びは K-4)。**無い欄はキーを出さない(`null` も `false` も書かない ― D-1)**。
 * 名前を `unrecordedKeys` に並べるのは「meta に無く、門の欄が `false` でない」とき(K-1)。門は `mirrored`(従う欄は `originalUserSide`・`plyOffset`・`startSfen`)と
 * `trailingMoveTruncated`(従う欄は `truncatedTrailingMove`)。`sideAlignmentChecked` は門を持たない。
 */
export const SIDE_AND_TRUNCATION_META_KEYS = ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked", "trailingMoveTruncated", "truncatedTrailingMove"] as const;
/** スキーマ v0.3 の `startSfen` の pattern と同じ文字列(計画 K-5: 空白で区切った 4 つの部分。盤の正しさは見ない)。試験でスキーマと突き合わせる */
export const START_SFEN_PATTERN = "^\\S+ [bw] \\S+ [1-9][0-9]*$";
/** スキーマ v0.3 の `truncatedTrailingMove` の pattern と同じ文字列(計画 K-5: 盤上の手か打つ手。lib/usiRotation.ts と同じ形)。試験でスキーマと突き合わせる */
export const USI_MOVE_PATTERN = "^([1-9][a-i][1-9][a-i]\\+?|[PLNSGBR]\\*[1-9][a-i])$";

export interface ProvenanceMetaBase {
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
}

/** そろえの組(計画 2.3): 無い / 回していない / 回した */
export type ProvenanceSideFields =
  | { mirrored?: never; originalUserSide?: never; plyOffset?: never; startSfen?: never; sideAlignmentChecked?: never }
  | { mirrored: false; sideAlignmentChecked: false; originalUserSide?: never; plyOffset?: never; startSfen?: never }
  | { mirrored: true; originalUserSide: "gote"; plyOffset: 1; startSfen: string; sideAlignmentChecked: boolean };
/** 打ち切りの組(計画 2.3): 無い / 落としていない / 落とした。**そろえの組があるなら、打ち切りの組が無いことは無い**(K-7。lib が止める) */
export type ProvenanceTruncationFields =
  | { trailingMoveTruncated?: never; truncatedTrailingMove?: never }
  | { trailingMoveTruncated: false; truncatedTrailingMove?: never }
  | { trailingMoveTruncated: true; truncatedTrailingMove: string };
/**
 * STEP D-SCREEN-2(計画 §3)。段 2 の記録の meta の screen の写し(deepPlies・measuredOrder は写さない)。**screen の無い記録はキーを出さない**
 * (unrecordedKeys にも入れない。screen が無いのは「記録していない」ではなく「段 2 の記録でない」)。deepRun.enginePath は根からの相対、dirty は DirtyState の 4 値
 */
export interface ProvenanceScreen {
  lightNodes: number;
  deepNodes: number;
  rule: { dropCp: number; advantageCp: number; advantageDropCp: number; before: number; after: number };
  sourceSha256: string;
  deepRun: { gitHead: string | null; dirty: DirtyState; enginePath: string; threads: number; startedAt: string; order: "plyAscending" };
}
export type ProvenanceMeta = ProvenanceMetaBase & ProvenanceSideFields & ProvenanceTruncationFields & { screen?: ProvenanceScreen } & { unrecordedKeys: string[] };

/** 記録の meta が、出どころに写せる形(STEP JSON V0.3-META 計画 2.3 の 7 変種)に合わない(計画 K-3)。文に記録の kifuId と、食い違った欄の名前(`欄 <名前>:`)を書く */
export class InvalidProvenanceMetaError extends Error {
  override name = "InvalidProvenanceMetaError";
}

export interface Provenance {
  record: { path: string; sha256: string; meta: ProvenanceMeta | null };
  /** 人が渡した評価関数の識別。**確かめていない自己申告**。null = 渡されていない */
  evaluator: { declared: string | null };
  /** Failure Event を組み立てたとき(diagnose.ts を回したとき)のコードと規則の値 */
  analysis: {
    gitHead: string | null;
    dirty: DirtyState;
    rule: { advantageCp: number; dropCp: number; windowPlies: number; focusDropCp: number; notEvaluationCp: number; standing: StandingBounds; positionFacts: PositionFactsRules };
  };
}

/** `--events` の 1 行(版つき)。版の欄は先頭、出どころは末尾に置く。STEP D2 の `counterfactual` は v0.4 から行に入る(consequences の後) */
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

const START_SFEN = new RegExp(START_SFEN_PATTERN);
const USI_MOVE = new RegExp(USI_MOVE_PATTERN);
const SIDE_FOLLOWERS = ["originalUserSide", "plyOffset", "startSfen"] as const;

/**
 * STEP JSON V0.3-META。meta のそろえの組と打ち切りの組を、スキーマ v0.3 の 7 変種と同じ規則で読む(計画 2.1〜2.3・K-1・K-3・K-5・K-7)。
 * 合わない形は写さず、食い違いを全部集めてから InvalidProvenanceMetaError を投げる(黙って写すと、スキーマを通らない行を書く)。
 */
function sideAndTruncationOf(raw: Record<string, unknown>): { fields: ProvenanceSideFields & ProvenanceTruncationFields; unrecorded: ReadonlySet<string> } {
  const has = (key: string): boolean => Object.hasOwn(raw, key);
  const problems: string[] = [];
  const problem = (key: string, text: string): void => {
    problems.push(`欄 ${key}: ${text}`);
  };
  const unrecorded = new Set<string>();

  let side: ProvenanceSideFields = {};
  if (!has("mirrored") && !has("sideAlignmentChecked")) {
    for (const key of SIDE_FOLLOWERS) if (has(key)) problem(key, "mirrored が無いのにある");
    for (const key of ["mirrored", ...SIDE_FOLLOWERS, "sideAlignmentChecked"]) unrecorded.add(key);
  } else if (!has("mirrored")) {
    problem("mirrored", "sideAlignmentChecked があるのに無い");
  } else if (!has("sideAlignmentChecked")) {
    problem("sideAlignmentChecked", "mirrored があるのに無い");
  } else if (raw.mirrored === false) {
    for (const key of SIDE_FOLLOWERS) if (has(key)) problem(key, "mirrored が false なのにある");
    if (raw.sideAlignmentChecked !== false) problem("sideAlignmentChecked", "mirrored が false なのに false でない");
    side = { mirrored: false, sideAlignmentChecked: false };
  } else if (raw.mirrored === true) {
    if (raw.originalUserSide !== "gote") problem("originalUserSide", `"gote" でない(${JSON.stringify(raw.originalUserSide)})`);
    if (raw.plyOffset !== 1) problem("plyOffset", `1 でない(${JSON.stringify(raw.plyOffset)})`);
    if (typeof raw.startSfen !== "string" || !START_SFEN.test(raw.startSfen)) problem("startSfen", "空白で区切った 4 つの部分の SFEN でない");
    if (typeof raw.sideAlignmentChecked !== "boolean") problem("sideAlignmentChecked", "boolean でない");
    side = { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: String(raw.startSfen), sideAlignmentChecked: raw.sideAlignmentChecked === true };
  } else {
    problem("mirrored", "boolean でない");
  }

  let truncation: ProvenanceTruncationFields = {};
  if (!has("trailingMoveTruncated")) {
    if (has("truncatedTrailingMove")) problem("truncatedTrailingMove", "trailingMoveTruncated が無いのにある");
    if (has("mirrored") || has("sideAlignmentChecked")) problem("trailingMoveTruncated", "そろえの組があるのに無い(どの replay.ts も書かない形 ― K-7)");
    unrecorded.add("trailingMoveTruncated");
    unrecorded.add("truncatedTrailingMove");
  } else if (raw.trailingMoveTruncated === false) {
    if (has("truncatedTrailingMove")) problem("truncatedTrailingMove", "trailingMoveTruncated が false なのにある");
    truncation = { trailingMoveTruncated: false };
  } else if (raw.trailingMoveTruncated === true) {
    if (typeof raw.truncatedTrailingMove !== "string" || !USI_MOVE.test(raw.truncatedTrailingMove)) problem("truncatedTrailingMove", "USI の手でない");
    truncation = { trailingMoveTruncated: true, truncatedTrailingMove: String(raw.truncatedTrailingMove) };
  } else {
    problem("trailingMoveTruncated", "boolean でない");
  }

  if (problems.length > 0) {
    throw new InvalidProvenanceMetaError(`記録 ${String(raw.kifuId)} の meta が、出どころに写せる形(STEP JSON V0.3-META 計画 2.3 の 7 変種)に合いません: ${problems.join(" / ")}`);
  }
  return { fields: Object.assign({}, side, truncation) as ProvenanceSideFields & ProvenanceTruncationFields, unrecorded };
}

/** STEP D-SCREEN-2。screen の写し(形は diagnose の不変条件 lib/screenDiagnosis.ts の screenOfRecord で確かめ済み)。無ければキーを出さない */
function screenProvenanceOf(raw: Record<string, unknown>, repoRoot: string): { screen?: ProvenanceScreen } {
  const screen = raw.screen as ScreenMeta | undefined;
  if (screen === undefined) return {};
  return {
    screen: {
      lightNodes: screen.lightNodes,
      deepNodes: screen.deepNodes,
      rule: { dropCp: screen.rule.dropCp, advantageCp: screen.rule.advantageCp, advantageDropCp: screen.rule.advantageDropCp, before: screen.rule.before, after: screen.rule.after },
      sourceSha256: screen.sourceSha256,
      deepRun: {
        gitHead: screen.deepRun.gitHead,
        dirty: readDirtyState({ dirty: screen.deepRun.dirty }),
        enginePath: pathForProvenance(screen.deepRun.enginePath, repoRoot),
        threads: screen.deepRun.threads,
        startedAt: screen.deepRun.startedAt,
        order: screen.deepRun.order,
      },
    },
  };
}

export function provenanceMetaOf(meta: MetaLine | undefined, repoRoot: string): ProvenanceMeta | null {
  if (meta === undefined) return null;
  const raw = meta as unknown as Record<string, unknown>;
  const stringOf = (key: string): string | null => (typeof raw[key] === "string" ? (raw[key] as string) : null);
  const integerOf = (key: string): number | null => (typeof raw[key] === "number" ? (raw[key] as number) : null);
  const enginePath = stringOf("enginePath");
  // STEP JSON V0.3-META: 7 欄が出どころに写せる形でなければ、ここで例外(K-3)
  const { fields, unrecorded } = sideAndTruncationOf(raw);
  return {
    gitHead: stringOf("gitHead"),
    dirty: readDirtyState(meta),
    enginePath: enginePath === null ? null : pathForProvenance(enginePath, repoRoot),
    searchMode: stringOf("searchMode"),
    nodes: integerOf("nodes"),
    threads: integerOf("threads"),
    ...fields,
    ...screenProvenanceOf(raw, repoRoot),
    unrecordedKeys: [...PROVENANCE_META_KEYS.filter((key) => !Object.hasOwn(raw, key)), ...SIDE_AND_TRUNCATION_META_KEYS.filter((key) => unrecorded.has(key))],
  } as ProvenanceMeta;
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
  /** STEP D2.5: 形勢の状態の境(lib/failureEvent.ts の STANDING_BOUNDS) */
  standingBounds: StandingBounds;
  /** STEP D2.5: 玉の区域の数え方(lib/counterfactual.ts の POSITION_FACTS_RULES) */
  positionFactsRules: PositionFactsRules;
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
        standing: { aheadCp: input.standingBounds.aheadCp, behindCp: input.standingBounds.behindCp },
        positionFacts: { zone: input.positionFactsRules.zone, reach: input.positionFactsRules.reach, control: input.positionFactsRules.control },
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
