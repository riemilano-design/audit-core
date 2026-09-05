// 「ユーザーが着手する直前の局面」と「相手の応手まで終えた現在の局面」を突き合わせ、
// 直前の一手で何が変わったかを機械的な事実として列挙する(Phase6 Unit2)。
//
// 【このモジュールがやること】
// routePlanner.ts(Unit1)とshapeFormationAnalyzer.tsが既に出している結果を、
// 着手の前後で比較するだけ。新しい将棋知識・ヒューリスティック・重み・閾値は
// 一切持たない。エンジンにもLLMにも依存しない決定的な純粋関数。
//
// 【このモジュールが絶対にやらないこと】
// 「良い手だった」「悪手だった」「形勢が良くなった」といった評価は一切行わない。
// エンジンの評価値には触れない(触れられる引数すら受け取らない)。
// 相手の狙いの推定もしない(それは既存のintentDetector.tsの責務)。
//
// 【原因の帰属について(重要・承認済みの3ルール)】
// beforeとafterの間には「ユーザーの着手」と「相手の着手」の2手が入るため、
// 変化の原因を安易に相手のせいにしない。原因(cause)を付けてよいのは次だけ:
//   1. ユーザーの着手そのものから直接確認できる変化(駒がその手で目標マスへ入った等)
//   2. 既存のplanChangeReason.tsが確定分類した理由(捕獲・王手放置・ピン)
//   3. それ以外は cause: null(原因を断定せず、変化した事実だけを述べる)
// "unknown"は「分類できなかった」という既存の値なので、causeとしては採用しない
// (=nullに倒す)。
//
// 【実測で判明した、素朴な差分では誤る3点(いずれも本モジュールで対策済み)】
//  a. 目標形が変わった手では、形・経路の差分を出してはいけない。matchedSquares/
//     missingSquaresは形ごとに定義が違うため、比較しても「崩れた」等の誤った事実になる。
//     → targetShapeIdが変わった場合はtarget_shape_changedのみを返す。
//  b. 「担当の駒が変わった」の誤検知。経路上を同じ駒が1歩進んだだけでも
//     fromSquareは変わる。→ 指した手の移動元・移動先と一致する場合は進行として扱う。
//  c. 「経路が消えた」には完成と喪失の2種類がある。
//     → matchedSquaresに増分があれば完成(route_completed)、無ければ喪失(route_lost)。

import { isDrop, makeSquareName, parseUsi } from "shogiops/util";
import type { PlanChangeReason } from "./planChangeReason.js";
import type { RouteCandidateMove, ShapeSquareRoute } from "./routePlanner.js";

export type MoveOutcomeFactKind =
  /** 目標形そのものが変わった(この場合、形・経路の差分は一切出さない) */
  | "target_shape_changed"
  /** 指した手が、直前に表示していた候補手に含まれていた */
  | "played_candidate"
  /** 指した手が、直前に表示していた候補手には含まれていなかった */
  | "played_non_candidate"
  /** 目標マスが埋まった(対応する経路が無かった場合のみ。経路があればroute_completed) */
  | "square_completed"
  /** 既に成立していた目標マスの駒がいなくなった */
  | "square_lost"
  /** 目標マスまでの残り手数が減った */
  | "route_advanced"
  /** 目標マスに駒が入り、その道のりが終わった */
  | "route_completed"
  /** 道のり自体が今の局面では成立しなくなった */
  | "route_lost"
  /** 残り手数が増えた */
  | "route_lengthened"
  /** 道のりの1手目が、今の局面では指せなくなった */
  | "route_first_move_unavailable"
  /** 道のりの1手目が、指せるようになった */
  | "route_first_move_available"
  /** 目標マス・経路を自分の駒が塞ぐようになり、準備手が必要になった */
  | "preparation_required"
  /** 塞いでいた自分の駒がどき、準備手が不要になった */
  | "preparation_resolved"
  /** 目標マスへ向かう担当の駒が別の駒に変わった(同じ駒の前進は含まない) */
  | "route_assignee_changed";

export interface MoveOutcomeFact {
  kind: MoveOutcomeFactKind;
  /** 対象の目標マス(USI形式)。目標マスに紐づかない事実ではnull。 */
  targetSquare: string | null;
  /** 目標マスに置く駒種(日本語表記)。分からない場合はnull。 */
  targetPiece: string | null;
  remainingStepsBefore: number | null;
  remainingStepsAfter: number | null;
  /** 経路を塞いでいる(いた)自分の駒のマス(USI形式)。 */
  blockingSquare: string | null;
  /** kind: "played_candidate"の場合の候補手の種類。それ以外はnull。 */
  candidateKind: RouteCandidateMove["kind"] | null;
  /**
   * 原因。planChangeReason.tsが確定分類した場合のみ値を持つ("unknown"は採用しない)。
   * 断定できない場合は必ずnull(ファイル冒頭の3ルール参照)。
   */
  cause: PlanChangeReason | null;
}

/** 比較に使う、ある局面時点のスナップショット(いずれも既存モジュールの出力そのまま)。 */
export interface MoveOutcomeSnapshot {
  /** 実際に採用されていた目標形のshapeId(採用が無ければundefined)。 */
  targetShapeId: string | undefined;
  /** shapeFormationAnalyzer.tsのmatchedSquares(targetShapeIdの形についてのもの)。 */
  matchedSquares: string[];
  /** routePlanner.tsのroutes。 */
  routes: ShapeSquareRoute[];
  /** routePlanner.tsのcandidateMoves。 */
  candidateMoves: RouteCandidateMove[];
}

export interface MoveOutcome {
  playedMoveUsi: string;
  /** 相手が応手していない場合(終局等)はnull。 */
  opponentMoveUsi: string | null;
  /** 空配列は「特筆すべき変化なし」を意味する(呼び出し側がその旨を表示する)。 */
  facts: MoveOutcomeFact[];
}

function makeFact(kind: MoveOutcomeFactKind, overrides: Partial<MoveOutcomeFact> = {}): MoveOutcomeFact {
  return {
    kind,
    targetSquare: overrides.targetSquare ?? null,
    targetPiece: overrides.targetPiece ?? null,
    remainingStepsBefore: overrides.remainingStepsBefore ?? null,
    remainingStepsAfter: overrides.remainingStepsAfter ?? null,
    blockingSquare: overrides.blockingSquare ?? null,
    candidateKind: overrides.candidateKind ?? null,
    cause: overrides.cause ?? null,
  };
}

/** "unknown"は「分類できなかった」という値なので、原因としては採用しない(nullに倒す)。 */
function toCause(planChangeReason: PlanChangeReason | null): PlanChangeReason | null {
  if (planChangeReason === null || planChangeReason === "unknown") return null;
  return planChangeReason;
}

interface PlayedMoveSquares {
  from: string | null;
  to: string | null;
}

/** 指した手の移動元・移動先をUSI形式のマス名で得る(ドロップは移動元を持たない)。 */
function playedMoveSquares(playedMoveUsi: string): PlayedMoveSquares {
  const move = parseUsi(playedMoveUsi);
  if (!move) return { from: null, to: null };
  return {
    from: isDrop(move) ? null : makeSquareName(move.from),
    to: makeSquareName(move.to),
  };
}

/**
 * 担当の駒が「別の駒に変わった」のか「同じ駒が経路上を進んだ」のかを区別する。
 * 指した手の移動元がbefore側の担当マス、移動先がafter側の担当マスなら、
 * それは同じ駒が進んだだけであり、担当が変わったわけではない。
 */
function isSamePieceAdvanced(before: ShapeSquareRoute, after: ShapeSquareRoute, played: PlayedMoveSquares): boolean {
  return played.from !== null && before.fromSquare === played.from && after.fromSquare === played.to;
}

function diffRoute(
  before: ShapeSquareRoute,
  after: ShapeSquareRoute,
  played: PlayedMoveSquares,
  cause: PlanChangeReason | null,
): MoveOutcomeFact[] {
  const facts: MoveOutcomeFact[] = [];
  const base = { targetSquare: before.targetSquare, targetPiece: before.targetPiece };

  if (after.remainingSteps < before.remainingSteps) {
    facts.push(
      makeFact("route_advanced", {
        ...base,
        remainingStepsBefore: before.remainingSteps,
        remainingStepsAfter: after.remainingSteps,
      }),
    );
  } else if (after.remainingSteps > before.remainingSteps) {
    facts.push(
      makeFact("route_lengthened", {
        ...base,
        remainingStepsBefore: before.remainingSteps,
        remainingStepsAfter: after.remainingSteps,
      }),
    );
  }

  if (after.fromSquare !== before.fromSquare && !isSamePieceAdvanced(before, after, played)) {
    facts.push(makeFact("route_assignee_changed", base));
  }

  const hadFirstMove = before.firstMoveUsis.length > 0;
  const hasFirstMove = after.firstMoveUsis.length > 0;
  if (hadFirstMove && !hasFirstMove) {
    facts.push(makeFact("route_first_move_unavailable", { ...base, cause }));
  } else if (!hadFirstMove && hasFirstMove) {
    facts.push(makeFact("route_first_move_available", base));
  }

  if (!before.blockedReason && after.blockedReason) {
    facts.push(makeFact("preparation_required", { ...base, blockingSquare: after.blockingSquare }));
  } else if (before.blockedReason && !after.blockedReason) {
    facts.push(makeFact("preparation_resolved", { ...base, blockingSquare: before.blockingSquare }));
  }

  return facts;
}

/**
 * 着手前後のスナップショットから、直前の一手で変わった事実を列挙する。
 *
 * planChangeReasonは既存のplanChangeReason.tsが確定分類した値をそのまま受け取る
 * (本モジュールは理由の判定を自前では行わない)。null・"unknown"の場合、
 * 原因は付けずに事実だけを返す。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 */
export function detectMoveOutcome(
  before: MoveOutcomeSnapshot,
  after: MoveOutcomeSnapshot,
  playedMoveUsi: string,
  opponentMoveUsi: string | null,
  planChangeReason: PlanChangeReason | null = null,
): MoveOutcome {
  const facts: MoveOutcomeFact[] = [];

  // 目標形が変わった場合、形・経路は別物なので差分を取らない(実測で判明した誤りへの対策)。
  if (before.targetShapeId !== after.targetShapeId) {
    return {
      playedMoveUsi,
      opponentMoveUsi,
      facts: [makeFact("target_shape_changed")],
    };
  }

  const cause = toCause(planChangeReason);
  const played = playedMoveSquares(playedMoveUsi);

  // 直前に候補手を1件も表示していなかった場合は、候補手だったかどうかに言及しない
  // (「表示していた候補手ではありません」は、候補が存在した場合にのみ意味を持つ)。
  if (before.candidateMoves.length > 0) {
    const playedCandidate = before.candidateMoves.find((c) => c.moveUsi === playedMoveUsi);
    facts.push(
      playedCandidate
        ? makeFact("played_candidate", {
            targetSquare: playedCandidate.targetSquare,
            targetPiece: playedCandidate.targetPiece,
            candidateKind: playedCandidate.kind,
          })
        : makeFact("played_non_candidate"),
    );
  }

  const beforeMatched = new Set(before.matchedSquares);
  const afterMatched = new Set(after.matchedSquares);
  const newlyMatched = after.matchedSquares.filter((square) => !beforeMatched.has(square));
  const lostMatched = before.matchedSquares.filter((square) => !afterMatched.has(square));

  // 経路があった目標マスの完成はroute_completedとして扱い、二重に報告しない。
  const beforeRouteTargets = new Set(before.routes.map((r) => r.targetSquare));
  for (const square of newlyMatched) {
    if (beforeRouteTargets.has(square)) continue;
    facts.push(makeFact("square_completed", { targetSquare: square }));
  }
  for (const square of lostMatched) {
    facts.push(makeFact("square_lost", { targetSquare: square }));
  }

  const newlyMatchedSet = new Set(newlyMatched);
  for (const beforeRoute of before.routes) {
    const afterRoute = after.routes.find((r) => r.targetSquare === beforeRoute.targetSquare);
    if (afterRoute) {
      facts.push(...diffRoute(beforeRoute, afterRoute, played, cause));
      continue;
    }
    // 経路が消えた場合、完成と喪失を混同しない(実測で判明した誤りへの対策)。
    if (newlyMatchedSet.has(beforeRoute.targetSquare)) {
      facts.push(
        makeFact("route_completed", {
          targetSquare: beforeRoute.targetSquare,
          targetPiece: beforeRoute.targetPiece,
          remainingStepsBefore: beforeRoute.remainingSteps,
          remainingStepsAfter: 0,
        }),
      );
    } else {
      facts.push(
        makeFact("route_lost", {
          targetSquare: beforeRoute.targetSquare,
          targetPiece: beforeRoute.targetPiece,
          remainingStepsBefore: beforeRoute.remainingSteps,
          cause,
        }),
      );
    }
  }

  return { playedMoveUsi, opponentMoveUsi, facts };
}
