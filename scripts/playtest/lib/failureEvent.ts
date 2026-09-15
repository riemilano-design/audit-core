// STEP D1(docs/STEP_D1_PLAN_2026-09-14.md)。1 局の記録(replay.ts の JSONL)から、評価の推移・
// 急落の候補・実戦の続きの王手/詰み・発症条件の写しを取り出し、Failure Event を組み立てる。
//
// 【このファイルがやること】
// - ready 行ごとの評価を「状態 + 値」で読む(計画 2.)。null を行の sfen に本番の関数を当て直して分ける
// - 連続する ready 行の組を作り、比べられない組は理由つきで数える(黙って飛ばさない ― P-22)
// - 急落の候補の後、実戦の手を窓の分だけ進め、後手の手による自玉への王手と自玉の詰みを集める
// - 発症条件(直前の行の評価・②の分類・形・③の状態)を A 層の値のまま写す(計画 3.1・9.1・9.2)
// - 死因①のタグを draft で付ける
// - STEP D2.5(docs/STEP_D2.5_PLAN_2026-09-15.md): 直前の行の局面の玉の区域に届く駒と升の数(trigger.positionFacts)と、組の前後の形勢の状態(branch.standingPair)を足す
//
// 【このファイルが絶対にやらないこと】
// - エンジンを回すこと。記録を読むだけ(check.ts と同じ形)
// - 将棋の判断。閾値(DRAFT_RULE_1)は判断的知識の仮置きであり、正本 5.3 の値を写しただけ(CLAUDE.md ルール 4)
// - 「無い」を 0 や false で埋めること(計画 2.。AGENT_PROTOCOL 11.6)
// - ③の文を読んで「急ぐと言った / 言わなかった」に分けること(計画 9.2)
// - 例外を外へ出すこと(diagnose.ts の exit code は常に 0。計画 D-1)
//
// 【この件数は診断に使わない】評価関数の種類は記録に残っていない(計画 0.・E-f)。今の記録は入力の行の enginePath で
// 見分けられる(engine/ と engine/nnue/。nn.bin だけ差し替えると見分けられない ― P-43)。

import { detectBoardEvents } from "../../../apps/server/src/analysis/boardEventDetector.js";
import { detectIntents } from "../../../apps/server/src/analysis/intentDetector.js";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { getGameOutcome, isGameOver, isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { displayDirty, readDirtyState } from "./gitState.js";
import { counterfactualLines, counterfactualOf, POSITION_FACTS_RULES, type Counterfactual } from "./counterfactual.js";
import { classifyIntentStatementRow, type IntentDetection, type IntentStatementClass } from "./intentStatement.js";
import { kingSurroundingsOf, type KingSurroundings } from "./kingSurroundings.js";
import { positionFactsOf, type PositionFacts } from "./positionFacts.js";
import { initialSfenOf } from "./sideAlignment.js";
import { standingPairOf, type StandingBounds, type StandingPair } from "./standing.js";

// ---- 仮の規則(判断的知識。1 か所にまとめる)----

export interface DiagnosisRule {
  /** 直前が優勢: 直前の行の baseline.scoreCp がこれ以上 */
  advantageCp: number;
  /** 分岐点で急落: 次の ready 行との差がこれ以下(負の値) */
  dropCp: number;
  /** 実戦の続きの窓: 分岐点の手の後、この手数(ply) */
  windowPlies: number;
  /** 分母の列「直前の dropCp がこれ以上」(③の承認済みの 300cp の借用) */
  focusDropCp: number;
}

/**
 * **【判断的知識・仮置き・人間の判断事項・draft】** 正本 5.3 の値(+300 / −400 / 3〜5 手)と、
 * ③の承認済みの 300cp の借用。窓は ply で 5 手(後手の手が 3 回入る。計画 D-2)。
 */
export const DRAFT_RULE_1: DiagnosisRule = { advantageCp: 300, dropCp: -400, windowPlies: 5, focusDropCp: 300 };

/**
 * **【判断的知識・人間の承認済み(2026-09-15、2fe81c3)】** STEP D2.5 の形勢の状態の境(docs/STEP_D2.5_PLAN_2026-09-15.md §1 の M-5・Q-5)。
 * +300 は正本 5.3(advantageCp)の借用、−300 は新しい値。境を含む。Failure Event の branch.standingPair と diagnosis-moment の standingPair に使い、出どころに写す。
 */
export const STANDING_BOUNDS: StandingBounds = { aheadCp: 300, behindCp: -300 };

/**
 * これ以上の |scoreCp| は評価値として扱わない(P-45。NNUE 版の記録で afterPass.scoreCp が 35281 = VALUE_MAX_EVAL を cp に直した値になり、
 * dropCp が 30457 になった)。**判断的知識の仮置き**(計画 D-6)。
 */
export const NOT_EVALUATION_CP = 30000;
const isNotEvaluation = (scoreCp: number | null): boolean => scoreCp !== null && Math.abs(scoreCp) >= NOT_EVALUATION_CP;

// ---- 評価の状態(計画 2.)----

export type Evaluation =
  | {
      state: "measured";
      scoreCp: number | null;
      mate: number | null;
      bestmove: string | null;
      afterPassScoreCp: number | null;
      /** > 0 なら、先手がパスすると後手が詰ませる読み(後手視点の値。計画 E-c) */
      afterPassMate: number | null;
      /** null は「両方 cp ではなかった」(0 ではない) */
      dropCp: number | null;
    }
  /** 測らないと決めた(終局) */
  | { state: "notMeasuredGameEnd" }
  /** 測らないと決めた(先手が王手中) */
  | { state: "notMeasuredInCheck" }
  /** 測れなかった(例外・時間切れ。記録からは区別できない)/ 値が 1 つも無い */
  | { state: "notMeasurable" }
  /** 測っていない(この記録は評価を持たない) */
  | { state: "unrecorded" }
  /**
   * 評価値でない(baseline か afterPass の |scoreCp| が NOT_EVALUATION_CP 以上)。やねうら王の特別値(VALUE_MAX_EVAL 付近)を
   * cp に直したもので、評価値として比べられない(P-45。測れなかった・測っていない・組が無い、とも別の「無い」)
   */
  | { state: "notEvaluation" };

export type EvaluationState = Evaluation["state"];

/** 1 行の評価の状態。`null` は行の sfen に本番の isGameOver / isInCheck を当て直して分ける(計画 E-b)。 */
export function evaluationOf(record: RecordLine): Evaluation {
  const reference = record.engineReference;
  if (reference === undefined) return { state: "unrecorded" };
  if (reference === null) {
    if (isGameOver(record.sfen)) return { state: "notMeasuredGameEnd" };
    if (isInCheck(record.sfen, "sente")) return { state: "notMeasuredInCheck" };
    return { state: "notMeasurable" };
  }
  if (reference.baseline.scoreCp === null && reference.baseline.mate === null) return { state: "notMeasurable" };
  if (isNotEvaluation(reference.baseline.scoreCp) || isNotEvaluation(reference.afterPass.scoreCp)) return { state: "notEvaluation" };
  return {
    state: "measured",
    scoreCp: reference.baseline.scoreCp,
    mate: reference.baseline.mate,
    bestmove: reference.baseline.bestmove,
    afterPassScoreCp: reference.afterPass.scoreCp,
    afterPassMate: reference.afterPass.mate,
    dropCp: reference.dropCp,
  };
}

export interface EvaluatedRow {
  ply: number;
  record: RecordLine;
  evaluation: Evaluation;
}

export function readEvaluations(records: readonly RecordLine[]): EvaluatedRow[] {
  return records
    .filter((record) => record.phase === "ready")
    .slice()
    .sort((a, b) => a.ply - b.ply)
    .map((record) => ({ ply: record.ply, record, evaluation: evaluationOf(record) }));
}

// ---- 連続する組(計画 2.)----

export type NotComparedReason = Exclude<EvaluationState, "measured"> | "mateBefore";

export type EvaluationPair =
  | { kind: "compared"; fromPly: number; toPly: number; diffCp: number }
  /** 直前が cp・直後が mate。差は取らない(計画 D-3) */
  | { kind: "mateAfter"; fromPly: number; toPly: number; scoreCpBefore: number; mateAfter: number }
  | { kind: "notCompared"; fromPly: number; toPly: number; reason: NotComparedReason; side: "from" | "to" };

export function pairEvaluations(rows: readonly EvaluatedRow[]): EvaluationPair[] {
  const pairs: EvaluationPair[] = [];
  for (let index = 0; index + 1 < rows.length; index++) {
    const from = rows[index]!;
    const to = rows[index + 1]!;
    const span = { fromPly: from.ply, toPly: to.ply };
    if (from.evaluation.state !== "measured") {
      pairs.push({ ...span, kind: "notCompared", reason: from.evaluation.state, side: "from" });
      continue;
    }
    if (to.evaluation.state !== "measured") {
      pairs.push({ ...span, kind: "notCompared", reason: to.evaluation.state, side: "to" });
      continue;
    }
    if (from.evaluation.scoreCp === null) {
      pairs.push({ ...span, kind: "notCompared", reason: "mateBefore", side: "from" });
      continue;
    }
    if (to.evaluation.scoreCp !== null) {
      pairs.push({ ...span, kind: "compared", diffCp: to.evaluation.scoreCp - from.evaluation.scoreCp });
    } else {
      // measured なので scoreCp と mate の少なくとも一方がある
      pairs.push({ ...span, kind: "mateAfter", scoreCpBefore: from.evaluation.scoreCp, mateAfter: to.evaluation.mate! });
    }
  }
  return pairs;
}

// ---- 実戦の続き(計画 3.1・D-2)----

/** 相手の手で自玉に王手がかかった(boardEventDetector の kind) */
const OPPONENT_CHECK = "check_received";

export interface Continuation {
  /** 窓の中で、後手の手の後に自玉が王手を受けた ply */
  checks: number[];
  /** 窓の中で自玉が詰んだ ply(後手の勝ちの詰み)。無ければ null */
  mate: number | null;
  windowPlies: number;
  /** 窓が棋譜の終わりを越え、終局もしていない(「起きなかった」ではない) */
  windowShort: boolean;
}

/**
 * 分岐点の手(branchPly 手目。先手の手)から、実戦の手を窓の終わり(branchPly + windowPlies)まで進める。
 * **読み筋ではなく実戦の続き**を見る。王手は detectBoardEvents の check_received、詰みは getGameOutcome。
 */
export function actualContinuation(
  moves: readonly string[],
  branchPly: number,
  windowPlies: number,
  initialSfen: string,
): Continuation {
  let sfen = initialSfen;
  for (let index = 0; index < branchPly - 1; index++) sfen = applyMove(sfen, moves[index]!);

  const lastPly = branchPly + windowPlies;
  const checks: number[] = [];
  let mate: number | null = null;
  let reachedPly = branchPly - 1;
  let ended = false;

  for (let sentePly = branchPly; sentePly <= lastPly && !ended; sentePly += 2) {
    const senteMove = moves[sentePly - 1];
    if (senteMove === undefined) break;
    const gotePly = sentePly + 1;
    const goteMove = gotePly <= lastPly ? (moves[gotePly - 1] ?? null) : null;

    const events = detectBoardEvents(sfen, senteMove, goteMove);
    if (events.some((event) => event.kind === OPPONENT_CHECK)) checks.push(gotePly);

    const afterSente = applyMove(sfen, senteMove);
    reachedPly = sentePly;
    if (isGameOver(afterSente)) {
      ended = true;
      break;
    }
    if (goteMove === null) break;
    sfen = applyMove(afterSente, goteMove);
    reachedPly = gotePly;
    const outcome = getGameOutcome(sfen);
    if (outcome !== undefined) {
      ended = true;
      if (outcome.winner === "gote") mate = gotePly;
    }
  }

  return { checks, mate, windowPlies, windowShort: !ended && reachedPly < lastPly };
}

// ---- 発症条件の写し(計画 3.1・9.1・9.2)----

/** ③が実際に何と言ったか。**文の中身では分けない**(計画 9.2) */
export type FocusState =
  | { state: "stated"; text: string }
  | { state: "nothingToSay" }
  | { state: "pending" }
  | { state: "unrecorded" };

export function focusStateOf(record: RecordLine): FocusState {
  const plan = record.response.plan as { focusTextState?: string; focusText?: string | null } | undefined;
  if (plan?.focusTextState === undefined) return { state: "unrecorded" };
  if (plan.focusTextState === "pending") return { state: "pending" };
  return typeof plan.focusText === "string" ? { state: "stated", text: plan.focusText } : { state: "nothingToSay" };
}

export type ShapeState = { state: "recorded"; status: string; refersToShapeId: string | null } | { state: "unrecorded" };

// STEP D2: 先手玉の周りを数える関数は lib/kingSurroundings.ts へ移した(lib/counterfactual.ts からも使うため。中身は変えていない)。
export { kingSurroundingsOf, type KingSurroundings } from "./kingSurroundings.js";

export interface Trigger {
  /** 直前の行の評価(状態 + 値。afterPass.mate と dropCp を含む ― 計画 9.1) */
  evaluationBefore: Evaluation;
  /** 直前の行の②(U6-I4 の分類をそのまま) */
  opponentIntent: { classification: IntentStatementClass; refersToIntentId: string | null };
  /** 直前の行の形(coach の current_shape) */
  shape: ShapeState;
  /** 直前の行の③ */
  focus: FocusState;
  /** 直前の行の局面の、先手玉の周り(STEP JSON v0.2。数えるだけ) */
  kingSurroundings: KingSurroundings | null;
  /** 直前の行の局面の、両方の玉の区域に利きが届く駒と升の数(STEP D2.5。数えるだけ) */
  positionFacts: PositionFacts;
}

/** `initialSfen` は記録の開始局面(STEP D0-SIDE 段 2 の R-5。回して畳んだ記録は平手から並べ直せない)。 */
export function triggerOf(row: EvaluatedRow, initialSfen: string): Trigger {
  const record = row.record;
  let detection: IntentDetection;
  try {
    detection = { ok: true, results: detectIntents(record.sfen, record.response.moveHistory, { initialSfen }) };
  } catch {
    detection = { ok: false };
  }
  const coach = record.response.coach;
  const intentStage = coach?.find((c) => c.stage === "opponent_intent");
  const shapeStage = coach?.find((c) => c.stage === "current_shape");
  return {
    evaluationBefore: row.evaluation,
    opponentIntent: {
      classification: classifyIntentStatementRow(record, detection),
      refersToIntentId: intentStage?.refers_to_intent_id ?? null,
    },
    shape:
      shapeStage === undefined
        ? { state: "unrecorded" }
        : { state: "recorded", status: shapeStage.status, refersToShapeId: shapeStage.refers_to_shape_id },
    focus: focusStateOf(record),
    kingSurroundings: kingSurroundingsOf(record.sfen),
    positionFacts: positionFactsOf(record.sfen, POSITION_FACTS_RULES),
  };
}

// ---- Failure Event(計画 3.1。正本 5.2 の形。counterfactual は STEP D2)----

/** 分岐点で何に当たったか。**matedIfPass は「急落」と呼ばない**(計画 D-3 の司令塔の条件) */
export type BranchKind = "cpDrop" | "mateDrop" | "matedIfPass";

export interface FailureEvent {
  kifuId: string;
  /** 分岐点の手(先手の手)の ply */
  branchPly: number;
  fromReadyPly: number;
  toReadyPly: number;
  trigger: Trigger;
  action: { playedMove: string | null; bestmoveAtBefore: string | null };
  branch: {
    kinds: BranchKind[];
    diffCp: number | null;
    mateAfter: number | null;
    /** 直後の行で、パスすると詰まされる読み(詰めろ相当)があった */
    matedIfPassAfter: boolean;
    /** 直後の行の評価(状態 + 値。evaluationBefore と同じ形 ― STEP JSON v0.2 の 2.2・K-5) */
    evaluationAfter: Evaluation;
    /** 直前の行と直後の行の評価の形勢の状態を並べただけ(STEP D2.5。判定語は持たない) */
    standingPair: StandingPair;
  };
  consequences: Continuation;
  /**
   * STEP D2(docs/STEP_D2_PLAN_2026-09-15.md)。分岐点の局面から、実戦の続きとエンジンの読み筋(直前の行の focus_baseline)を
   * 同じ手数だけ並べた事実。**死因の規則(candidateModes)には使わない。**Failure Event JSON にはスキーマ v0.4 で出す(consequences の後)
   */
  counterfactual: Counterfactual;
  candidateModes: Array<{ mode: "mate_threat"; status: "draft"; matchedBy: BranchKind[] }>;
}

export interface DiagnosisCounts {
  readyRows: number;
  measured: number;
  notMeasuredGameEnd: number;
  notMeasuredInCheck: number;
  notMeasurable: number;
  unrecorded: number;
  notEvaluation: number;
  comparedPairs: number;
  mateAfterPairs: number;
  notComparedPairs: number;
  /** 急落候補(cpDrop か mateDrop) */
  dropCandidates: number;
  /** 直後の行でパスすると詰まされる読みがあった組(急落とは別に数える) */
  matedIfPassPairs: number;
  /** Failure Event(急落候補 か matedIfPass で当たった組) */
  events: number;
  /** 以下 6 つは**急落候補のうち**(計画 9.1。matedIfPass だけで当たった Failure Event は数えない ― D-3 で数え分けるため) */
  fromAdvantage: number;
  withCheck: number;
  withMate: number;
  windowShort: number;
  beforeAfterPassMate: number;
  beforeDropCpAtLeast: number;
  /** Failure Event のうち、死因①(draft)の候補が付いたもの */
  cause1Draft: number;
}

/** 最も長い moveHistory(最後の ready 行は棋譜の全手を持つ。計画 E-d)。STEP D1b の lib/diagnosisMoment.ts も同じ手順を使う */
export function fullMovesOf(rows: readonly EvaluatedRow[]): string[] {
  return rows.reduce<string[]>(
    (longest, row) => (row.record.response.moveHistory.length > longest.length ? row.record.response.moveHistory : longest),
    [],
  );
}

/** `initialSfen` は記録の開始局面(STEP D0-SIDE 段 2 の R-5。`buildDiagnosisReport` が meta から読んで渡す)。 */
export function diagnoseRecords(
  kifuId: string,
  records: readonly RecordLine[],
  rule: DiagnosisRule,
  initialSfen: string,
): { counts: DiagnosisCounts; events: FailureEvent[] } {
  const rows = readEvaluations(records);
  const pairs = pairEvaluations(rows);
  const moves = fullMovesOf(rows);
  const events: FailureEvent[] = [];
  let dropCandidates = 0;
  let matedIfPassPairs = 0;

  pairs.forEach((pair, index) => {
    const from = rows[index]!;
    const to = rows[index + 1]!;
    const kinds: BranchKind[] = [];
    if (pair.kind === "compared" && pair.diffCp <= rule.dropCp) kinds.push("cpDrop");
    if (pair.kind === "mateAfter" && pair.mateAfter < 0) kinds.push("mateDrop");
    if (kinds.length > 0) dropCandidates += 1;
    const matedIfPassAfter =
      to.evaluation.state === "measured" && to.evaluation.afterPassMate !== null && to.evaluation.afterPassMate > 0;
    if (matedIfPassAfter) {
      kinds.push("matedIfPass");
      matedIfPassPairs += 1;
    }
    if (kinds.length === 0) return;

    const branchPly = from.ply + 1;
    const consequences = actualContinuation(moves, branchPly, rule.windowPlies, initialSfen);
    const advantage =
      from.evaluation.state === "measured" && from.evaluation.scoreCp !== null && from.evaluation.scoreCp >= rule.advantageCp;
    const danger = consequences.checks.length > 0 || consequences.mate !== null;
    const bestmoveAtBefore = from.evaluation.state === "measured" ? from.evaluation.bestmove : null;
    // STEP D2: D1 の実戦の続き(consequences)の後に数える。D1 の経路と値は変えない(計画 4. の限界・予-D2)
    const counterfactual = counterfactualOf({ record: from.record, moves, branchPly, windowPlies: rule.windowPlies, initialSfen, bestmoveAtBefore });
    events.push({
      kifuId,
      branchPly,
      fromReadyPly: from.ply,
      toReadyPly: to.ply,
      trigger: triggerOf(from, initialSfen),
      action: {
        playedMove: moves[branchPly - 1] ?? null,
        bestmoveAtBefore,
      },
      branch: {
        kinds,
        diffCp: pair.kind === "compared" ? pair.diffCp : null,
        mateAfter: pair.kind === "mateAfter" ? pair.mateAfter : null,
        matedIfPassAfter,
        evaluationAfter: to.evaluation,
        standingPair: standingPairOf(from.evaluation, to.evaluation, STANDING_BOUNDS),
      },
      consequences,
      counterfactual,
      candidateModes: advantage && danger ? [{ mode: "mate_threat", status: "draft", matchedBy: kinds }] : [],
    });
  });

  const stateCount = (state: EvaluationState) => rows.filter((row) => row.evaluation.state === state).length;
  const countEvents = (predicate: (event: FailureEvent) => boolean) => events.filter(predicate).length;
  // 「うち」の列は急落候補の内訳(計画 9.1・D-3)。matedIfPass だけで当たった Failure Event は入れない
  const dropEvents = events.filter((event) => event.branch.kinds.some((kind) => kind !== "matedIfPass"));
  const countDrops = (predicate: (event: FailureEvent) => boolean) => dropEvents.filter(predicate).length;
  const before = (event: FailureEvent) => event.trigger.evaluationBefore;

  return {
    events,
    counts: {
      readyRows: rows.length,
      measured: stateCount("measured"),
      notMeasuredGameEnd: stateCount("notMeasuredGameEnd"),
      notMeasuredInCheck: stateCount("notMeasuredInCheck"),
      notMeasurable: stateCount("notMeasurable"),
      unrecorded: stateCount("unrecorded"),
      notEvaluation: stateCount("notEvaluation"),
      comparedPairs: pairs.filter((pair) => pair.kind === "compared").length,
      mateAfterPairs: pairs.filter((pair) => pair.kind === "mateAfter").length,
      notComparedPairs: pairs.filter((pair) => pair.kind === "notCompared").length,
      dropCandidates,
      matedIfPassPairs,
      events: events.length,
      fromAdvantage: countDrops((event) => {
        const evaluation = before(event);
        return evaluation.state === "measured" && evaluation.scoreCp !== null && evaluation.scoreCp >= rule.advantageCp;
      }),
      withCheck: countDrops((event) => event.consequences.checks.length > 0),
      withMate: countDrops((event) => event.consequences.mate !== null),
      windowShort: countDrops((event) => event.consequences.windowShort),
      beforeAfterPassMate: countDrops((event) => {
        const evaluation = before(event);
        return evaluation.state === "measured" && evaluation.afterPassMate !== null && evaluation.afterPassMate > 0;
      }),
      beforeDropCpAtLeast: countDrops((event) => {
        const evaluation = before(event);
        return evaluation.state === "measured" && evaluation.dropCp !== null && evaluation.dropCp >= rule.focusDropCp;
      }),
      cause1Draft: countEvents((event) => event.candidateModes.length > 0),
    },
  };
}

// ---- 報告(計画 3.2。diagnose.ts は積むだけにする)----

export interface DiagnosisInput {
  kifuId: string;
  meta: MetaLine | undefined;
  records: RecordLine[];
  /**
   * STEP D0-SIDE 段 1(R-9)。記録の error 行(replay.ts が途中で止まった印)の理由。**1 つでもあれば、その記録は数えない**
   * (最後の組を欠いた局を黙って 1 局と数えない)。**必須にしてある**(渡し忘れを型検査で止める)。
   */
  errorLines: readonly { reason: string }[];
}

export type DiagnosisResult =
  | { kind: "counted"; counts: DiagnosisCounts; events: FailureEvent[] }
  | { kind: "notCounted"; errorName: string; message: string }
  /** STEP D0-SIDE 段 1(R-9)。error 行を持つ記録なので数えなかった(例外で数えられなかった notCounted とは別) */
  | { kind: "excluded"; errorReasons: string[] };

export interface DiagnosisRow {
  kifuId: string;
  meta: MetaLine | undefined;
  result: DiagnosisResult;
}

type Diagnose = (kifuId: string, records: readonly RecordLine[], rule: DiagnosisRule, initialSfen: string) => { counts: DiagnosisCounts; events: FailureEvent[] };

/** 入力ごとに診断する。**例外を外へ出さない**(計画 D-1)。`diagnose` は試験専用。 */
export function buildDiagnosisReport(
  inputs: readonly DiagnosisInput[],
  rule: DiagnosisRule,
  diagnose: Diagnose = diagnoseRecords,
): DiagnosisRow[] {
  return inputs.map((input) => {
    // STEP D0-SIDE 段 1(R-9): error 行を持つ記録は、診断の関数を呼ばずに外す
    if (input.errorLines.length > 0) {
      return { kifuId: input.kifuId, meta: input.meta, result: { kind: "excluded", errorReasons: input.errorLines.map((line) => line.reason) } };
    }
    try {
      // STEP D0-SIDE 段 2(R-5): 開始局面は meta から読む(形の食い違う meta は例外になり、下の catch で「数えられなかった」になる)
      const { counts, events } = diagnose(input.kifuId, input.records, rule, initialSfenOf(input.meta));
      return { kifuId: input.kifuId, meta: input.meta, result: { kind: "counted", counts, events } };
    } catch (error) {
      return {
        kifuId: input.kifuId,
        meta: input.meta,
        result: {
          kind: "notCounted",
          errorName: error instanceof Error ? error.constructor.name : typeof error,
          message: error instanceof Error ? error.message : String(error),
        },
      };
    }
  });
}

const EVALUATION_LABELS: Record<Exclude<EvaluationState, "measured">, string> = {
  notMeasuredGameEnd: "測らない(終局)",
  notMeasuredInCheck: "測らない(王手中)",
  notMeasurable: "測れなかった",
  unrecorded: "測っていない",
  notEvaluation: "評価値でない",
};

function evaluationCell(evaluation: Evaluation): string {
  if (evaluation.state !== "measured") return EVALUATION_LABELS[evaluation.state];
  return evaluation.scoreCp !== null ? String(evaluation.scoreCp) : `mate ${evaluation.mate}`;
}

function focusCell(focus: FocusState): string {
  switch (focus.state) {
    case "stated":
      return `文あり「${focus.text}」`;
    case "nothingToSay":
      return "言うことが無い";
    case "pending":
      return "計算していない";
    case "unrecorded":
      return "記録していない";
  }
}

function intentCell(intent: Trigger["opponentIntent"]): string {
  const c = intent.classification;
  const column = c.column === "undetermined" ? `判定できない(${c.reason})` : c.column;
  return intent.refersToIntentId === null ? column : `${column} / ${intent.refersToIntentId}`;
}

const NOTES = [
  "- **この件数は診断に使わない。** 評価関数の種類は記録に残っていない(MATERIAL と NNUE で `meta.enginePath` は同じになりうる)。今の記録は入力の行の `enginePath` で見分けられる(`engine/` と `engine/nnue/`。`nn.bin` だけ差し替えると見分けられない ― P-43)",
  "- **死因①のタグは draft。** 閾値(直前 +300 / 差 −400 / 窓 5 手 / 直前の dropCp 300)は判断的知識の仮置きである",
  "- 発症条件の②と形は、照合時の `data/intents/`・`data/shapes/` に依存する(記録時の ②③ と混ざる)",
  "- **「測っていない」「測れなかった」は「急落なし」ではない。** 窓が棋譜の終わりを越えたものは「窓が足りない」であり、「起きなかった」ではない",
  "- **cp の絶対値が 30000 以上の値は評価値ではない。** やねうら王の特別値(VALUE_MAX_EVAL 付近)を cp に直したもので、その行は「評価値でない」として組から外す(P-45。30000 は仮置き ― 計画 D-6)",
  "- 観測の集計であり、異常とは呼ばない。自分の手で落ちたのか相手の応手で落ちたのかは分けていない(連続する ready 行の差は 2 手分)",
];

/**
 * 急落候補とその内訳の欄。比べた組(差を取った組・直後が mate の組)が 1 つも無ければ、0 ではなく「比べる組が無い」と出す
 * (計画 4.2・規則 11.6。「無い」を「急落なし」にしない)。**表示の分岐はここだけ。**
 * 組が無い理由(測れなかった・測っていない・評価値でない・行が 1 つ)は畳んでいるので、区別は隣の「評価の状態と組」の表が担う。
 * STEP D3: lib/diagnosisTotals.ts の合計の表も同じ分岐を使うため export した(分岐を 2 か所に持たない)。
 */
/** 数えなかった入力の欄の文。error 行のため使わなかった記録と、例外で数えられなかった記録を分ける(STEP D0-SIDE 段 1。R-9) */
function uncountedCell(result: Exclude<DiagnosisResult, { kind: "counted" }>): string {
  return result.kind === "excluded" ? "error 行のため使わない" : "数えられなかった";
}

export function dropCountCell(counts: DiagnosisCounts, value: number): string {
  return counts.comparedPairs + counts.mateAfterPairs === 0 ? "比べる組が無い" : String(value);
}

export function renderDiagnosisReport(rows: readonly DiagnosisRow[]): string[] {
  const lines: string[] = [];
  lines.push("# 負け方の診断(STEP D1。道具の確認用)");
  lines.push("");
  lines.push(...NOTES);
  lines.push("");

  lines.push("## 入力");
  for (const row of rows) {
    const meta = row.meta;
    lines.push(
      `- ${row.kifuId}(gitHead: ${meta?.gitHead ?? "不明"}, ${displayDirty(readDirtyState(meta), meta?.dirtyCount ?? meta?.dirtyPaths?.length)}, enginePath: ${meta?.enginePath ?? "不明"}, nodes: ${meta === undefined ? "不明" : (meta.nodes ?? "記録していない")})`,
    );
  }
  for (const row of rows) {
    if (row.result.kind === "notCounted") {
      lines.push(`- 数えられなかった入力: ${row.kifuId}(${row.result.errorName}: ${row.result.message})`);
    } else if (row.result.kind === "excluded") {
      lines.push(`- error 行のため使わなかった入力: ${row.kifuId}(error 行の理由: ${row.result.errorReasons.join("、")})`);
    }
  }
  lines.push("");

  lines.push("## 評価の状態と組");
  lines.push("");
  lines.push("| 対象 | ready 行 | 測った | 測らない(終局) | 測らない(王手中) | 測れなかった | 測っていない | 評価値でない(cp の絶対値 ≥ 30000) | 比べた組 | 直後が mate の組 | 比べられなかった組 |");
  lines.push("|---|---|---|---|---|---|---|---|---|---|---|");
  for (const row of rows) {
    if (row.result.kind !== "counted") {
      lines.push(`| ${row.kifuId} | ${uncountedCell(row.result)} | - | - | - | - | - | - | - | - | - |`);
      continue;
    }
    const c = row.result.counts;
    lines.push(
      `| ${row.kifuId} | ${c.readyRows} | ${c.measured} | ${c.notMeasuredGameEnd} | ${c.notMeasuredInCheck} | ${c.notMeasurable} | ${c.unrecorded} | ${c.notEvaluation} | ${c.comparedPairs} | ${c.mateAfterPairs} | ${c.notComparedPairs} |`,
    );
  }
  lines.push("");

  lines.push("## Failure Event の数(0 件も出す)");
  lines.push("");
  lines.push(
    "| 対象 | 急落候補 | うち直前が優勢 | うち窓の中に王手 | うち窓の中に詰み | うち窓が足りない | うち直前 afterPass.mate > 0 | うち直前 dropCp ≥ 300 | 直後にパスすると詰まされる読み | Failure Event | 死因①(draft) |",
  );
  lines.push("|---|---|---|---|---|---|---|---|---|---|---|");
  for (const row of rows) {
    if (row.result.kind !== "counted") {
      lines.push(`| ${row.kifuId} | ${uncountedCell(row.result)} | - | - | - | - | - | - | - | - | - |`);
      continue;
    }
    const c = row.result.counts;
    const drop = (value: number) => dropCountCell(c, value);
    lines.push(
      `| ${row.kifuId} | ${drop(c.dropCandidates)} | ${drop(c.fromAdvantage)} | ${drop(c.withCheck)} | ${drop(c.withMate)} | ${drop(c.windowShort)} | ${drop(c.beforeAfterPassMate)} | ${drop(c.beforeDropCpAtLeast)} | ${c.matedIfPassPairs} | ${c.events} | ${c.cause1Draft} |`,
    );
  }
  lines.push("");

  lines.push("## Failure Event(1 件 1 行)");
  lines.push("");
  lines.push(
    "| 対象 | 分岐点 | 当たり方 | 直前の評価 | 差 | 直後 mate | 直前 afterPass.mate | 直前 dropCp | ②(直前) | 形(直前) | ③(直前) | 実際の手 | 直前の bestmove | 窓の王手 | 窓の詰み | 窓が足りない | 死因①(draft) |",
  );
  lines.push("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");
  for (const row of rows) {
    if (row.result.kind !== "counted") continue;
    for (const event of row.result.events) {
      const before = event.trigger.evaluationBefore;
      const measured = before.state === "measured" ? before : null;
      lines.push(
        `| ${event.kifuId} | ${event.branchPly} | ${event.branch.kinds.join("+")} | ${evaluationCell(before)} | ${event.branch.diffCp ?? "-"} | ${event.branch.mateAfter ?? "-"} | ${measured ? (measured.afterPassMate ?? "無し") : EVALUATION_LABELS[before.state as Exclude<EvaluationState, "measured">]} | ${measured ? (measured.dropCp ?? "両方 cp ではない") : "-"} | ${intentCell(event.trigger.opponentIntent)} | ${event.trigger.shape.state === "recorded" ? event.trigger.shape.status : "記録していない"} | ${focusCell(event.trigger.focus)} | ${event.action.playedMove ?? "-"} | ${event.action.bestmoveAtBefore ?? "-"} | ${event.consequences.checks.join(",") || "無し"} | ${event.consequences.mate ?? "無し"} | ${event.consequences.windowShort ? "足りない" : "-"} | ${event.candidateModes.length > 0 ? "mate_threat" : "-"} |`,
      );
    }
  }
  lines.push("");

  // STEP D2(計画 2.5): Event 1 件につき、実戦の続きと読み筋の 2 行(比べない状態は 1 行)。表の中に行を挟まないよう、表の後に置く
  lines.push("## 実戦の続きと読み筋(STEP D2。事実の並びだけ。読み筋は③の探索で、急落を見つけた評価とは別の探索)");
  lines.push("");
  let counterfactualCount = 0;
  for (const row of rows) {
    if (row.result.kind !== "counted") continue;
    for (const event of row.result.events) {
      lines.push(...counterfactualLines(event.kifuId, event.branchPly, event.counterfactual));
      counterfactualCount += 1;
    }
  }
  if (counterfactualCount === 0) lines.push("- Failure Event が無い");
  lines.push("");
  return lines;
}
