// STEP D-SCREEN-1(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §1・§2・§11 の段 2)。段 1(全行を軽いノード数で測った記録)から、
// 急落の候補の組の前後の ready 行だけを選び、深いノード数で測り直した値を**別の欄**に足した段 2 の記録を組み立てる。
//
// 【このファイルがやること】
// - 候補の組を選ぶ(§2 の (a)〜(d)。閾値は draft の DRAFT_SCREEN_RULE_1 を 1 か所に置く)
// - 読み直す行を決める(候補の組ごとに行 i−1・i・i+1・i+2。端は切り、重なりは 1 回、ply の昇順)
// - 引数で受けた `measure` を ply の昇順に呼び、行に `engineReferenceDeep`・`searchPvsDeep`(同じ呼び出しの戻り値)を、
//   meta に `screen` を足す。deepRun の gitHead・dirty は**このファイルが自分で読む**(渡された値を使わない ― 計画 R-3)
//
// 【このファイルが絶対にやらないこと】
// - エンジンを起こすこと(`measure` は呼び出し側が渡す。試験は偽の `measure` を渡す)
// - 段 1 の値を書き換えること: `engineReference`(軽い値)・`searchPvs`(③の探索の読み筋)・読み直していない行・meta の既存の欄は
//   **段 1 のバイト列のまま**出す(足した行だけを JSON に組み直し、欄は後ろに足す)
// - 深い値の使い方を決めること(`diagnose.ts` の規則・版は D-SCREEN-2)

import type { EngineReferenceMeasurement } from "../../../apps/server/src/analysis/engineReference.js";
import { isGameOver, isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import type { CheckBaseline } from "./checkBaseline.js";
import { pairEvaluations, readEvaluations } from "./failureEvent.js";
import { recordSha256 } from "./failureEventSchema.js";
import { readGitState, type GitRunner } from "./gitState.js";

// ---- 候補の組(計画 §2)----

/** 候補の組の規則。**判断的知識の仮置き(draft)**。校正で取りこぼしが出たら、候補を広げる向き(絶対値を小さくする)にだけ動かす */
export interface ScreenRule {
  /** (a) 比べた組で差がこれ以下 */
  dropCp: number;
  /** (b) 直前の scoreCp がこれ以上で… */
  advantageCp: number;
  /** (b) …差がこれ以下 */
  advantageDropCp: number;
  /** 読み直す行: 組の直前の行から前へ何行 */
  before: number;
  /** 読み直す行: 組の直前の行から後ろへ何行(組の直後の行を含む) */
  after: number;
}

export const DRAFT_SCREEN_RULE_1: ScreenRule = { dropCp: -300, advantageCp: 300, advantageDropCp: -200, before: 1, after: 2 };

/** 組が候補になった理由(1 つの組に複数付きうる) */
export type ScreenReason = "drop" | "advantageDrop" | "mateAfter" | "matedIfPass" | "notEvaluation" | "notMeasurable";

export interface ScreenCandidate {
  fromPly: number;
  toPly: number;
  reasons: ScreenReason[];
}

/**
 * 段 1 の値だけで候補の組を選ぶ。組は `pairEvaluations` と同じ(連続する ready 行)。
 * (d) の理由は `pairEvaluations` の reason をそのまま使う(直前の行が王手中なら、直後が notMeasurable でも王手中の組になり、候補にしない)。
 */
export function screenCandidatesOf(records: readonly RecordLine[], rule: ScreenRule): ScreenCandidate[] {
  const rows = readEvaluations(records);
  const candidates: ScreenCandidate[] = [];
  pairEvaluations(rows).forEach((pair, index) => {
    const from = rows[index]!;
    const to = rows[index + 1]!;
    const reasons: ScreenReason[] = [];
    if (pair.kind === "compared" && pair.diffCp <= rule.dropCp) reasons.push("drop");
    if (
      pair.kind === "compared" &&
      from.evaluation.state === "measured" &&
      from.evaluation.scoreCp !== null &&
      from.evaluation.scoreCp >= rule.advantageCp &&
      pair.diffCp <= rule.advantageDropCp
    ) {
      reasons.push("advantageDrop");
    }
    if (pair.kind === "mateAfter" && pair.mateAfter < 0) reasons.push("mateAfter");
    if (to.evaluation.state === "measured" && to.evaluation.afterPassMate !== null && to.evaluation.afterPassMate > 0) reasons.push("matedIfPass");
    if (pair.kind === "notCompared" && (pair.reason === "notEvaluation" || pair.reason === "notMeasurable")) reasons.push(pair.reason);
    if (reasons.length > 0) candidates.push({ fromPly: pair.fromPly, toPly: pair.toPly, reasons });
  });
  return candidates;
}

/** 読み直す ready 行の ply(昇順・重なりなし)。候補の組の直前の行を i として i − before 〜 i + after、端は切る */
export function deepPliesOf(records: readonly RecordLine[], rule: ScreenRule): number[] {
  const plies = readEvaluations(records).map((row) => row.ply);
  const chosen = new Set<number>();
  for (const candidate of screenCandidatesOf(records, rule)) {
    const index = plies.indexOf(candidate.fromPly);
    for (let offset = -rule.before; offset <= rule.after; offset++) {
      const ply = plies[index + offset];
      if (ply !== undefined) chosen.add(ply);
    }
  }
  return [...chosen].sort((a, b) => a - b);
}

// ---- 段 2 の記録(計画 §2・§11)----

/** 1 行を深く測る関数。CLI は `measureEngineReference(sfen, engine, deepNodes)` を渡す */
export type ScreenMeasure = (sfen: string) => Promise<EngineReferenceMeasurement>;

/** STEP FILL 作業 X(計画 §2)。1 行(王手中)を深く測る関数。CLI は `measureCheckBaseline(sfen, engine, deepNodes)` を渡す */
export type CheckBaselineMeasure = (sfen: string) => Promise<CheckBaseline | null>;

export interface DeepRunInput {
  deepNodes: number;
  /** 深い回で使ったエンジン */
  enginePath: string;
  threads: number;
  startedAt: string;
  /** git の状態を読む場所(このファイルが自分で読む) */
  repoRoot: string;
  /** 試験専用。本番の呼び出し側は渡さない */
  runGit?: GitRunner;
  /** STEP FILL 作業 X(計画 §2)。渡すと、読み直す行のうち先手が王手中(終局でない)の行にだけ追加で呼び、`checkBaselineDeep` を足す。
   * 渡さなければ(既存の呼び出し)今までどおり `checkBaselineDeep` は書かない。 */
  checkMeasure?: CheckBaselineMeasure;
}

export interface ScreenMeta {
  lightNodes: number;
  deepNodes: number;
  rule: ScreenRule;
  /** 校正の床(`allPlies`)だけ true。候補を選ばず全 ready 行を読み直した(rule は写すが、選び方には使っていない)。本番の段 2 はキーを出さない(監査 N-6)。出どころには写さない */
  allPlies?: true;
  /** 読み直した ready 行の ply(昇順) */
  deepPlies: number[];
  /** 段 1 のファイルのバイト列の sha256 */
  sourceSha256: string;
  deepRun: {
    gitHead: string | null;
    dirty: boolean | null;
    enginePath: string;
    threads: number;
    startedAt: string;
    order: "plyAscending";
    /** 実際に `measure` を呼んだ ply の並び */
    measuredOrder: number[];
  };
}

/** 段 1 として受け付けない入力(書く前に止める) */
export class RescreenInputError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RescreenInputError";
  }
}

interface ParsedSource {
  rawLines: string[];
  parsed: Array<{ kind?: unknown } | null>;
  metaIndex: number;
  meta: MetaLine & { referenceNodes?: unknown; screen?: unknown };
  records: RecordLine[];
  lightNodes: number;
}

function parseSource(source: Uint8Array): ParsedSource {
  const rawLines = Buffer.from(source).toString("utf-8").split("\n");
  const parsed = rawLines.map((line) => (line.trim().length > 0 ? (JSON.parse(line) as { kind?: unknown }) : null));
  const metaIndexes = parsed.flatMap((line, index) => (line?.kind === "meta" ? [index] : []));
  if (metaIndexes.length !== 1) throw new RescreenInputError(`meta 行がちょうど 1 つではない(${metaIndexes.length} 行)`);
  const metaIndex = metaIndexes[0]!;
  const meta = parsed[metaIndex] as ParsedSource["meta"];
  if (meta.screen !== undefined) throw new RescreenInputError("meta に screen がある(段 2 の記録は段 1 として受け付けない)");
  const lightNodes = meta.referenceNodes;
  if (typeof lightNodes !== "number" || !Number.isInteger(lightNodes) || lightNodes <= 0) {
    throw new RescreenInputError(`meta の referenceNodes が正の整数でない(${JSON.stringify(lightNodes)})`);
  }
  const records = parsed.filter((line): line is RecordLine => line?.kind === "record") as RecordLine[];
  const readyPlies = records.filter((record) => record.phase === "ready").map((record) => record.ply);
  if (new Set(readyPlies).size !== readyPlies.length) throw new RescreenInputError("同じ ply の ready 行が 2 つ以上ある");
  return { rawLines, parsed, metaIndex, meta, records, lightNodes };
}

/**
 * 読み直す行の選び方(STEP D-SCREEN-2)。`allPlies` は**校正の床(計画 §5 の 0.)だけ**で使う: 候補を選ばず、全 ready 行を読み直す。
 * `rule` はそのまま写し、`deepPlies` が全 ready 行になる。選び方が meta から読めるように、screen の `rule` の直後に `allPlies: true` を書く(監査 N-6)。
 */
export interface RescreenOptions {
  allPlies?: boolean;
}

function chooseDeepPlies(records: readonly RecordLine[], rule: ScreenRule, options: RescreenOptions): number[] {
  return options.allPlies ? readEvaluations(records).map((row) => row.ply) : deepPliesOf(records, rule);
}

/** 書く前の確かめ(CLI がエンジンを起こす前に呼ぶ)。読み直す行を返す */
export function planRescreen(source: Uint8Array, rule: ScreenRule, options: RescreenOptions = {}): { deepPlies: number[]; lightNodes: number } {
  const { records, lightNodes } = parseSource(source);
  return { deepPlies: chooseDeepPlies(records, rule, options), lightNodes };
}

/**
 * 段 2 の記録の全文を返す(改行の並びは段 1 のまま)。`measure` は読み直す行ごとに 1 回、ply の昇順で呼ぶ。
 * 読み直した行には `engineReferenceDeep`(= 戻り値の reference。測らない・測れなかったは null)と `searchPvsDeep`(= **同じ呼び出しの** searchPvs)を足す。
 *
 * STEP FILL 作業 X(計画 §2): `run.checkMeasure` を渡すと、読み直す行のうち先手が王手中(終局でない)の行にだけ、同じ ply の順で追加に呼び、
 * `checkBaselineDeep` を足す(`measure` は王手中の局面では呼び出し側の測る関数 = `measureEngineReference` が engine を呼ばずに null を返すため、
 * `measuredOrder`(段 1 の軽いノード数と揃える主役の記録)には数えない)。`run.checkMeasure` を渡さない呼び出し(既存のテスト等)は今までどおり
 * `checkBaselineDeep` を書かない。
 */
export async function rescreenRecords(
  source: Uint8Array,
  rule: ScreenRule,
  measure: ScreenMeasure,
  run: DeepRunInput,
  options: RescreenOptions = {},
): Promise<string> {
  const { rawLines, parsed, metaIndex, meta, records, lightNodes } = parseSource(source);
  const deepPlies = chooseDeepPlies(records, rule, options);
  const readyByPly = new Map(records.filter((record) => record.phase === "ready").map((record) => [record.ply, record]));
  const measureCheck = run.checkMeasure;

  const measuredOrder: number[] = [];
  const measured = new Map<number, EngineReferenceMeasurement>();
  const checkMeasured = new Map<number, CheckBaseline | null>();
  for (const ply of deepPlies) {
    const sfen = readyByPly.get(ply)!.sfen;
    const measurement = await measure(sfen);
    measuredOrder.push(ply);
    measured.set(ply, measurement);
    if (measureCheck !== undefined && !isGameOver(sfen) && isInCheck(sfen, "sente")) {
      checkMeasured.set(ply, await measureCheck(sfen));
    }
  }

  const gitState = readGitState(run.repoRoot, run.runGit);
  const screen: ScreenMeta = {
    lightNodes,
    deepNodes: run.deepNodes,
    rule,
    ...(options.allPlies ? { allPlies: true as const } : {}),
    deepPlies,
    sourceSha256: recordSha256(source),
    deepRun: {
      gitHead: gitState.gitHead,
      dirty: gitState.dirty,
      enginePath: run.enginePath,
      threads: run.threads,
      startedAt: run.startedAt,
      order: "plyAscending",
      measuredOrder,
    },
  };

  return rawLines
    .map((rawLine, index) => {
      const line = parsed[index];
      if (index === metaIndex) return JSON.stringify({ ...meta, screen });
      if (line?.kind !== "record") return rawLine;
      const record = line as RecordLine;
      const measurement = record.phase === "ready" ? measured.get(record.ply) : undefined;
      if (measurement === undefined) return rawLine;
      // STEP FILL 作業 X: checkMeasured に無い(王手中でない・measureCheck 無し)行は checkBaselineDeep の欄を出さない
      return checkMeasured.has(record.ply)
        ? JSON.stringify({ ...record, engineReferenceDeep: measurement.reference, searchPvsDeep: measurement.searchPvs, checkBaselineDeep: checkMeasured.get(record.ply) })
        : JSON.stringify({ ...record, engineReferenceDeep: measurement.reference, searchPvsDeep: measurement.searchPvs });
    })
    .join("\n");
}
