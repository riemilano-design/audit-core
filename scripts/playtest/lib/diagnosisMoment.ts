// STEP D1b(docs/STEP_D1b_PLAN_2026-09-15.md)。急落が無い局・勝った局にも、事実だけの 2 つの出力を足す。
// - 上がり(`rise`): 急落と同じ窓(本人の手 → 相手の手)で、本人視点の評価が `−dropCp` 以上上がった組、または直後に本人が詰ませる読み(`mateAfter > 0`)の組
// - 最大の下がり(`maxDrop`): 局ごとに、差を取れた組(`compared`)のうち `diffCp` が最も小さい 1 件(閾値未満でも出す。同じ値なら早い組)。
//   出せない局も黙って落とさず、状態の行(`noDrop`・`noComparedPair`)にする(規則 11.6)
// 行の契約は `diagnosis-moment` v0.1(Failure Event とは別。計画 Q-1)。スキーマは scripts/playtest/schemas/diagnosis-moment.v0.1.schema.json。
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
  triggerOf,
  type Continuation,
  type DiagnosisRule,
  type Evaluation,
  type FailureEvent,
  type Trigger,
} from "./failureEvent.js";
import type { Provenance } from "./failureEventSchema.js";

export const DIAGNOSIS_MOMENT_CONTRACT = "diagnosis-moment" as const;
export const DIAGNOSIS_MOMENT_SCHEMA_VERSION = "0.1" as const;

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
): DiagnosisMoments {
  const rows = readEvaluations(records);
  const pairs = pairEvaluations(rows);
  const moves = fullMovesOf(rows);
  const eventPlies = new Set(events.map((event) => event.branchPly));

  const pairFields = (index: number): MomentPairFields => {
    const from = rows[index]!;
    const to = rows[index + 1]!;
    const branchPly = from.ply + 1;
    const userMove = moves[branchPly - 1];
    const opponentMove = moves[branchPly];
    if (userMove === undefined || opponentMove === undefined) {
      throw new Error(`記録 ${kifuId} の組 ${from.ply}→${to.ply} の窓の 2 手が棋譜に無い(手数 ${moves.length})`);
    }
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
      failureEventBranchPly: eventPlies.has(branchPly) ? branchPly : null,
      consequences: actualContinuation(moves, branchPly, rule.windowPlies, initialSfen),
      counterfactual: counterfactualOf({ record: from.record, moves, branchPly, windowPlies: rule.windowPlies, initialSfen, bestmoveAtBefore: userBestmoveAtBefore }),
    };
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
  const excludedPairs: ExcludedPairs = {
    mateDrop: pairs.filter((pair) => pair.kind === "mateAfter" && pair.mateAfter < 0).length,
    mateRise: pairs.filter((pair) => pair.kind === "mateAfter" && pair.mateAfter > 0).length,
    notCompared: pairs.filter((pair) => pair.kind === "notCompared").length,
  };
  let minIndex: number | undefined;
  let minDiffCp = 0;
  pairs.forEach((pair, index) => {
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
    maxDrop = { ...momentOrder("maxDrop", kifuId, pairFields(minIndex), { kind: "cp", diffCp: minDiffCp }), excludedPairs };
  }
  return { rises, maxDrop };
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

export function loadDiagnosisMomentSchema(): JsonSchema {
  return JSON.parse(readFileSync(new URL(`../schemas/diagnosis-moment.v${DIAGNOSIS_MOMENT_SCHEMA_VERSION}.schema.json`, import.meta.url), "utf-8")) as JsonSchema;
}

/** 1 行(JSON.parse した値)を契約のスキーマに照らす。誤りを 1 件 1 行で返す(空なら通った) */
export function validateDiagnosisMomentLine(line: unknown, schema: JsonSchema = loadDiagnosisMomentSchema()): string[] {
  return validate(line, schema);
}
