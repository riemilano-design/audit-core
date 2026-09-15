// STEP D1b(docs/STEP_D1b_PLAN_2026-09-15.md)。急落が無い局・勝った局にも、事実だけの 2 つの出力を足す。
// - 上がり(`rise`): 急落と同じ窓(本人の手 → 相手の手)で、本人視点の評価が `−dropCp` 以上上がった組、または直後に本人が詰ませる読み(`mateAfter > 0`)の組
// - 最大の下がり(`maxDrop`): 局ごとに、差を取れた組(`compared`)のうち `diffCp` が最も小さい 1 件(閾値未満でも出す。同じ値なら早い組)。
//   出せない局も黙って落とさず、状態の行(`noDrop`・`noComparedPair`)にする(規則 11.6)
// 行の契約は `diagnosis-moment` v0.2(Failure Event とは別。計画 Q-1)。スキーマは scripts/playtest/schemas/diagnosis-moment.v0.2.schema.json。
// STEP D2.5(docs/STEP_D2.5_PLAN_2026-09-15.md §2)で、組の行に standingPair を足し、trigger・counterfactual に玉の区域の数が入った(v0.1 のファイルは変えていない)。
//
// 【このファイルがやること】`readEvaluations`・`pairEvaluations` の結果を読み、行を組み立てる純粋関数。窓の中の事実は Failure Event と同じ関数
// (`triggerOf`・`actualContinuation`・D2 の `counterfactualOf`)に同じ根で当てる(計画 2.・E-7・Q-4)。
//
// 【このファイルが絶対にやらないこと】
// - 理由の推定(相手が間違えた・本人がうまく指した)と評価語。**窓は 2 手を分けず、「相手の手で上がった」とは書かない**(計画 E-3)
// - `afterPass.bestmove` を相手の第一候補として出すこと(本人が指す前の盤で手番を相手にした探索の手。`opponentBestmove` は `notInRecord` 固定 ― E-4)
// - Failure Event の値・列挙・`--events` の行を変えること。死因のタグ(`candidateModes`)を付けること
// - 新しい閾値を置くこと(上がりの閾値は `DiagnosisRule.dropCp` の符号を変えて使う ― Q-2)。エンジンを回すこと

import { readFileSync } from "node:fs";
import type { RecordLine } from "../invariants/types.js";
import { counterfactualOf, type Counterfactual } from "./counterfactual.js";
import { validate, type JsonSchema } from "./eventSchema.js";
import {
  actualContinuation,
  fullMovesOf,
  pairEvaluations,
  readEvaluations,
  STANDING_BOUNDS,
  triggerOf,
  type Continuation,
  type DiagnosisRule,
  type EvaluatedRow,
  type Evaluation,
  type FailureEvent,
  type Trigger,
} from "./failureEvent.js";
import type { Provenance } from "./failureEventSchema.js";
import { standingOf, standingPairOf, type Standing, type StandingPair } from "./standing.js";
import type { PairRow } from "./condition.js";
import type { ScreenMeta } from "./rescreen.js";
// 版の文字列は lib/schemaVersions.ts の 1 か所に置く(STEP D-SCREEN-2)
import { DIAGNOSIS_MOMENT_SCHEMA_VERSION, KNOWN_DIAGNOSIS_MOMENT_SCHEMA_VERSIONS } from "./schemaVersions.js";
import { choosePairSources, withPvSource, type EvaluationSource } from "./screenDiagnosis.js";

export const DIAGNOSIS_MOMENT_CONTRACT = "diagnosis-moment" as const;
export { DIAGNOSIS_MOMENT_SCHEMA_VERSION, KNOWN_DIAGNOSIS_MOMENT_SCHEMA_VERSIONS };
export type DiagnosisMomentSchemaVersion = (typeof KNOWN_DIAGNOSIS_MOMENT_SCHEMA_VERSIONS)[number];

/** 組の行(`rise` と、`maxDrop` の組の行)が持つ欄(計画 2.) */
export interface MomentPairFields {
  /** 本人の手の ply(Failure Event の branchPly と同じ数え方) */
  branchPly: number;
  fromReadyPly: number;
  toReadyPly: number;
  /** 直前の行(`triggerOf` をそのまま) */
  trigger: Trigger;
  /** 窓の 2 手(記録の手数 `branchPly`・`branchPly + 1`)。**2 手を分けて「どちらの手で」とは言わない** */
  moves: { userMove: string; opponentMove: string };
  /** 直前の行の baseline.bestmove(Failure Event の action.bestmoveAtBefore と同じ値) */
  userBestmoveAtBefore: string | null;
  /** 記録に相手番の局面の評価が無い(計画 E-3・E-4) */
  opponentBestmove: { state: "notInRecord" };
  /** 直後の行の評価(Failure Event の branch.evaluationAfter と同じ形) */
  evaluationAfter: Evaluation;
  /** STEP D2.5: 直前の行と直後の行の評価の形勢の状態(Failure Event の branch.standingPair と同じ形) */
  standingPair: StandingPair;
  /** STEP D-SCREEN-2(計画 §3)。組の評価の出どころ。meta に screen のある記録だけに書く */
  evaluationSource?: EvaluationSource;
  /** 同じ組の Failure Event があればその branchPly、無ければ null(計画 E-8・Q-5) */
  failureEventBranchPly: number | null;
  /** `actualContinuation` をそのまま */
  consequences: Continuation;
  /** D2 の `counterfactualOf` を Failure Event と同じ根で当てた値 */
  counterfactual: Counterfactual;
}

/** 最大の下がりの候補にしなかった組の数(計画 2.・S-5) */
export interface ExcludedPairs {
  /** 直前が cp・直後が本人の詰まされる読み(mateAfter < 0) */
  mateDrop: number;
  /** 直前が cp・直後が本人の詰ませる読み(mateAfter > 0) */
  mateRise: number;
  /** どちらかの行が測られていない・評価値でない・直前が mate */
  notCompared: number;
}

export type RiseMoment = { eventClass: "rise"; kifuId: string } & MomentPairFields & { change: { kind: "cp"; diffCp: number } | { kind: "mateAfter"; mateAfter: number } };

export type MaxDropMoment =
  | ({ eventClass: "maxDrop"; kifuId: string } & MomentPairFields & { change: { kind: "cp"; diffCp: number }; excludedPairs: ExcludedPairs })
  /** 差を取れた組の最小の diffCp が 0 以上(0 もここ。−1 は組の行 ― S-4) */
  | { eventClass: "maxDrop"; kifuId: string; state: "noDrop"; minDiffCp: number; excludedPairs: ExcludedPairs }
  /** 差を取れた組が 1 つも無い */
  | { eventClass: "maxDrop"; kifuId: string; state: "noComparedPair"; excludedPairs: ExcludedPairs };

export type DiagnosisMoment = RiseMoment | MaxDropMoment;

export interface DiagnosisMoments {
  rises: RiseMoment[];
  maxDrop: MaxDropMoment;
}

/**
 * 1 局の上がりと最大の下がり。`events` は同じ記録・同じ規則・同じ開始局面の `diagnoseRecords` の Failure Event
 * (`failureEventBranchPly` を引くためだけに読む。値は変えない)。
 */
export function diagnosisMomentsOf(
  kifuId: string,
  records: readonly RecordLine[],
  rule: DiagnosisRule,
  initialSfen: string,
  events: readonly FailureEvent[],
  /** STEP D-SCREEN-2。不変条件を確かめた段 2 の記録の screen。無ければ今のまま */
  screen?: ScreenMeta,
): DiagnosisMoments {
  const rows = readEvaluations(records);
  // STEP D-SCREEN-2(計画 §3): 段 2 の記録は、組ごとに 2 行とも深い値か 2 行とも軽い値かを選ぶ(Failure Event と同じ決め方)
  const chosen = screen === undefined ? undefined : choosePairSources(rows);
  const pairs = chosen === undefined ? pairEvaluations(rows) : chosen.map((pair) => pair.pair);
  const context: PairFieldsContext = { kifuId, moves: fullMovesOf(rows), eventPlies: new Set(events.map((event) => event.branchPly)), rule, initialSfen };

  // `lightOnly`: 最大の下がりで出どころが混ざる局は、全部の組を軽い値で作る(S-13)
  const pairFields = (index: number, lightOnly = false): MomentPairFields => {
    const pick = chosen === undefined || lightOnly ? undefined : chosen[index]!;
    const from = pick === undefined ? rows[index]! : pick.from;
    const to = pick === undefined ? rows[index + 1]! : pick.to;
    const source: EvaluationSource | undefined = chosen === undefined ? undefined : lightOnly ? "light" : pick!.source;
    return pairFieldsOf(context, from, to, source);
  };

  // 上がり: 急落の閾値の符号を変える(計画 Q-2。新しい定数を置かない)
  const riseCp = -rule.dropCp;
  const rises: RiseMoment[] = [];
  pairs.forEach((pair, index) => {
    if (pair.kind === "compared" && pair.diffCp >= riseCp) {
      rises.push(momentOrder("rise", kifuId, pairFields(index), { kind: "cp", diffCp: pair.diffCp }));
    } else if (pair.kind === "mateAfter" && pair.mateAfter > 0) {
      rises.push(momentOrder("rise", kifuId, pairFields(index), { kind: "mateAfter", mateAfter: pair.mateAfter }));
    }
  });

  // 最大の下がり: compared の組だけから選ぶ。同じ値なら早い組(`<` で置き換える)
  // STEP D-SCREEN-2(計画 §3・S-13): 比べた組の出どころが混ざる局は、全部の組を軽い値で作り直して選ぶ(局の中の比べでもノード数を混ぜない)
  const lightOnly = new Set((chosen ?? []).filter((pair) => pair.pair.kind === "compared").map((pair) => pair.source)).size > 1;
  const dropPairs = lightOnly ? pairEvaluations(rows) : pairs;
  const excludedPairs: ExcludedPairs = {
    mateDrop: dropPairs.filter((pair) => pair.kind === "mateAfter" && pair.mateAfter < 0).length,
    mateRise: dropPairs.filter((pair) => pair.kind === "mateAfter" && pair.mateAfter > 0).length,
    notCompared: dropPairs.filter((pair) => pair.kind === "notCompared").length,
  };
  let minIndex: number | undefined;
  let minDiffCp = 0;
  dropPairs.forEach((pair, index) => {
    if (pair.kind !== "compared") return;
    if (minIndex === undefined || pair.diffCp < minDiffCp) {
      minIndex = index;
      minDiffCp = pair.diffCp;
    }
  });
  let maxDrop: MaxDropMoment;
  if (minIndex === undefined) {
    maxDrop = { eventClass: "maxDrop", kifuId, state: "noComparedPair", excludedPairs };
  } else if (minDiffCp >= 0) {
    maxDrop = { eventClass: "maxDrop", kifuId, state: "noDrop", minDiffCp, excludedPairs };
  } else {
    maxDrop = { ...momentOrder("maxDrop", kifuId, pairFields(minIndex, lightOnly), { kind: "cp", diffCp: minDiffCp }), excludedPairs };
  }
  return { rises, maxDrop };
}

/** 組の行の欄を作る材料(1 局ぶん)。`diagnosisMomentsOf` と `allPairsOf` が同じ関数で作る(STEP D4 計画 §2) */
interface PairFieldsContext {
  kifuId: string;
  moves: string[];
  eventPlies: ReadonlySet<number>;
  rule: DiagnosisRule;
  initialSfen: string;
}

/** 窓の 2 手(記録の手数 `branchPly`・`branchPly + 1`)。棋譜に無ければ null */
function windowMovesOf(moves: readonly string[], from: EvaluatedRow): { userMove: string; opponentMove: string } | null {
  const userMove = moves[from.ply];
  const opponentMove = moves[from.ply + 1];
  return userMove === undefined || opponentMove === undefined ? null : { userMove, opponentMove };
}

/** 組 1 つの欄。`source` は D-SCREEN-2 の出どころ(screen の無い記録と allPairsOf は undefined でキーを出さない)。窓の 2 手が棋譜に無ければ例外 */
function pairFieldsOf(context: PairFieldsContext, from: EvaluatedRow, to: EvaluatedRow, source: EvaluationSource | undefined): MomentPairFields {
  const { kifuId, moves, eventPlies, rule, initialSfen } = context;
  const branchPly = from.ply + 1;
  const window = windowMovesOf(moves, from);
  if (window === null) {
    throw new Error(`記録 ${kifuId} の組 ${from.ply}→${to.ply} の窓の 2 手が棋譜に無い(手数 ${moves.length})`);
  }
  const { userMove, opponentMove } = window;
  const userBestmoveAtBefore = from.evaluation.state === "measured" ? from.evaluation.bestmove : null;
  return {
    branchPly,
    fromReadyPly: from.ply,
    toReadyPly: to.ply,
    trigger: triggerOf(from, initialSfen),
    moves: { userMove, opponentMove },
    userBestmoveAtBefore,
    opponentBestmove: { state: "notInRecord" },
    evaluationAfter: to.evaluation,
    standingPair: standingPairOf(from.evaluation, to.evaluation, STANDING_BOUNDS),
    ...(source === undefined ? {} : { evaluationSource: source }),
    failureEventBranchPly: eventPlies.has(branchPly) ? branchPly : null,
    consequences: actualContinuation(moves, branchPly, rule.windowPlies, initialSfen),
    counterfactual: (() => {
      const counterfactual = counterfactualOf({ record: from.record, moves, branchPly, windowPlies: rule.windowPlies, initialSfen, bestmoveAtBefore: userBestmoveAtBefore });
      return source === undefined ? counterfactual : withPvSource(counterfactual, source);
    })(),
  };
}

/** STEP D4(計画 §2)。1 局の全ての手の組 */
export interface AllPairs {
  /** 窓の 2 手が棋譜にある組だけ(ply の昇順) */
  pairs: PairRow[];
  /** 窓の 2 手が棋譜に無く、`pairs` に入れなかった組の数(分母に入れない) */
  movesMissing: number;
  /**
   * ready 行すべての形勢の状態(軽い値、ply の昇順)。5 手以内(参考)が読む。
   * **計画 §2 の型に無い欄**(司令塔の決定 T-1、計画 §13 に記録)。movesMissing の組の行も含む
   */
  rowStandings: Array<{ ply: number; standing: Standing }>;
}

/**
 * STEP D4(計画 §2)。1 局の全ての手の組を、`diagnosisMomentsOf` と同じ欄の作り方で並べる。
 * **出どころは軽い値だけ**(Q-2・R-6): 記録に `engineReferenceDeep`・`searchPvsDeep` があっても `engineReference`・`searchPvs` を読み、
 * 組の行に `evaluationSource`・`counterfactual.pvSource` を書かない(出どころは集計に 1 回だけ ― 司令塔の決定 T-2)。
 * `events` は `failureEventBranchPly` を引くためだけに読む。軽い値にそろえるため、screen を渡さない `diagnoseRecords` の Event を渡す。
 */
export function allPairsOf(
  kifuId: string,
  records: readonly RecordLine[],
  rule: DiagnosisRule,
  initialSfen: string,
  events: readonly FailureEvent[],
  options: { source: "light" },
): AllPairs {
  if (options.source !== "light") throw new Error(`allPairsOf の出どころは light だけ(${String(options.source)})`);
  const rows = readEvaluations(records);
  const context: PairFieldsContext = { kifuId, moves: fullMovesOf(rows), eventPlies: new Set(events.map((event) => event.branchPly)), rule, initialSfen };
  const pairs: PairRow[] = [];
  let movesMissing = 0;
  pairEvaluations(rows).forEach((pair, index) => {
    const from = rows[index]!;
    if (windowMovesOf(context.moves, from) === null) {
      movesMissing += 1;
      return;
    }
    pairs.push({ kifuId, pairKind: pair.kind, ...pairFieldsOf(context, from, rows[index + 1]!, undefined) });
  });
  return { pairs, movesMissing, rowStandings: rows.map((row) => ({ ply: row.ply, standing: standingOf(row.evaluation, STANDING_BOUNDS) })) };
}

/** 行の欄の順(スキーマの properties と同じ順) */
function momentOrder<C extends "rise" | "maxDrop", Change>(eventClass: C, kifuId: string, fields: MomentPairFields, change: Change) {
  return {
    eventClass,
    kifuId,
    branchPly: fields.branchPly,
    fromReadyPly: fields.fromReadyPly,
    toReadyPly: fields.toReadyPly,
    trigger: fields.trigger,
    change,
    moves: fields.moves,
    userBestmoveAtBefore: fields.userBestmoveAtBefore,
    opponentBestmove: fields.opponentBestmove,
    evaluationAfter: fields.evaluationAfter,
    standingPair: fields.standingPair,
    ...(fields.evaluationSource === undefined ? {} : { evaluationSource: fields.evaluationSource }),
    failureEventBranchPly: fields.failureEventBranchPly,
    consequences: fields.consequences,
    counterfactual: fields.counterfactual,
  };
}

/** `--events-rise`・`--events-maxdrop` の 1 行。契約と版の欄を先頭に、出どころを末尾に置く(Failure Event の `schemaVersion` と取り違えないよう `contract` を必須にする) */
export type DiagnosisMomentLine = { contract: typeof DIAGNOSIS_MOMENT_CONTRACT; schemaVersion: typeof DIAGNOSIS_MOMENT_SCHEMA_VERSION } & DiagnosisMoment & { provenance: Provenance };

export function toMomentLine(moment: DiagnosisMoment, provenance: Provenance): DiagnosisMomentLine {
  return { contract: DIAGNOSIS_MOMENT_CONTRACT, schemaVersion: DIAGNOSIS_MOMENT_SCHEMA_VERSION, ...moment, provenance };
}

export function loadDiagnosisMomentSchema(version: DiagnosisMomentSchemaVersion = DIAGNOSIS_MOMENT_SCHEMA_VERSION): JsonSchema {
  return JSON.parse(readFileSync(new URL(`../schemas/diagnosis-moment.v${version}.schema.json`, import.meta.url), "utf-8")) as JsonSchema;
}

/** 1 行(JSON.parse した値)を契約のスキーマに照らす。誤りを 1 件 1 行で返す(空なら通った) */
export function validateDiagnosisMomentLine(line: unknown, schema: JsonSchema = loadDiagnosisMomentSchema()): string[] {
  return validate(line, schema);
}
