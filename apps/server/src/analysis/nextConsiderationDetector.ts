// 現在の局面について既に確定している事実だけを整理する(Phase6 Unit4)。
//
// 【このモジュールがやること】
// Unit 1(routePlanner.ts)と形判定が既に確定させた結果と、将棋のルール上の事実
// (王手を受けているか・対局が終わっているか)を受け取り、「今の局面で分かっていること」を
// 決定的な規則で選び・並べるだけ。新しい判定は一切行わない。
//
// 【このモジュールが絶対にやらないこと】
// - 「良い手/悪い手」「最善」「おすすめ」「危険」といった評価・推奨は一切しない
//   (評価に必要な情報を引数として受け取ってすらいない)。
// - エンジンの評価値には一切触れない。LLMも使わない。
// - 相手の意図・狙いには触れない(Phase1のcoachブロックの責務)。
// - 複数手先の予測はしない。
// - 着手前の局面・lastMoveOutcome・lastBoardEvents は使わない(差分ではなく、
//   現在局面の静的な状態だけを扱う。Unit 2・Unit 3との責務境界)。
//
// 【並び順について】
// 並び順は「残り手数の少ない順」という機械的な規則だけで決める。これは将棋としての
// 良し悪しの順ではない(その旨は説明側の文言で明示する)。同じ残り手数の場合は
// Unit 1 が既に確定させた routes の順序(typical_build_order順)をそのまま保つ。
//
// 【重複回避について】
// Unit 1 が既に画面に出している「残り手数」「マスの状態」「一手目が指せる/指せない」
// 「経路が計算できなかったこと」「準備手」は、ここでは扱わない(再掲しない)。
// route_first_move_playable は、既に表示されている候補手が「どの目標マスへ向かう
// 経路の一手なのか」という対応を示すためだけのもの。

import type { RouteCandidateMove, ShapeSquareRoute } from "./routePlanner.js";
import type { ReviewStatus } from "./nameExposure.js";

export type NextConsiderationKind =
  /** 自玉に王手がかかっている(将棋のルール上の制約であり、評価ではない) */
  | "in_check"
  /** 現在指せる候補手が、どの目標マスへ向かう経路の一手目なのか */
  | "route_first_move_playable"
  /** 経路はあるが、経路そのものの一手目が現在1つも指せない(準備手しか無い場合を含む) */
  | "no_playable_route_first_move"
  /** 選択中の形に必要なマスがすべて埋まっている */
  | "shape_completed";

export interface NextConsiderationFact {
  kind: NextConsiderationKind;
  /** kind: "route_first_move_playable" の場合の指し手(USI形式)。それ以外はnull。 */
  moveUsi: string | null;
  /** その手が向かっている目標マス(USI形式)。紐づかない事実ではnull。 */
  targetSquare: string | null;
  /** 目標マスに置く駒種(日本語表記、data/shapes/*.jsonそのまま)。紐づかない事実ではnull。 */
  targetPiece: string | null;
  /** kind: "shape_completed" の場合の形の名前。それ以外はnull。 */
  shapeName: string | null;
  /** kind: "shape_completed" の場合の、その形のreview_status。それ以外(shapeNameがnullの場合)はnull。
   * 名前を出してよいかの判断はanalysis/nameExposure.tsに集約し、このモジュールでは判断しない。 */
  shapeReviewStatus: ReviewStatus | null;
}

/**
 * 判定の材料。いずれも既存モジュールが確定させた値をそのまま受け取るだけで、
 * このモジュールは局面(SFEN)を自分で解釈しない(将棋のルール判定を複製しない)。
 */
export interface NextConsiderationInput {
  /** 実際に採用された目標形のshapeId。採用が無ければundefined。 */
  targetShapeId: string | undefined;
  /** 選択中の形の名前(shapeFormationAnalyzer.tsのname)。分からない場合はnull。 */
  shapeName: string | null;
  /** 選択中の形のreview_status(shapeFormationAnalyzer.tsのreviewStatus)。shapeNameが
   * nullの場合はnull。 */
  shapeReviewStatus: ReviewStatus | null;
  /** 選択中の形の未達成マス(shapeFormationAnalyzer.tsのmissingSquares)。 */
  missingSquares: string[];
  /** routePlanner.tsのroutes。 */
  routes: ShapeSquareRoute[];
  /** routePlanner.tsのcandidateMoves(実際にユーザーへ提示されている候補手)。 */
  candidateMoves: RouteCandidateMove[];
  /** 対局が終了しているか(rules/gameStatus.tsの判定結果)。 */
  isGameEnd: boolean;
  /** 自分(ユーザー)の玉に王手がかかっているか(rules層の判定結果)。 */
  inCheck: boolean;
}

function makeFact(
  kind: NextConsiderationKind,
  overrides: Partial<Omit<NextConsiderationFact, "kind">> = {},
): NextConsiderationFact {
  return {
    kind,
    moveUsi: overrides.moveUsi ?? null,
    targetSquare: overrides.targetSquare ?? null,
    targetPiece: overrides.targetPiece ?? null,
    shapeName: overrides.shapeName ?? null,
    shapeReviewStatus: overrides.shapeReviewStatus ?? null,
  };
}

/**
 * 残り手数の少ない順に並べる。同じ残り手数の場合は元の順序(routePlanner.tsが
 * typical_build_order順で確定させた順序)をそのまま保つ(Array.prototype.sortは安定)。
 * remainingStepsAfterはkind==="route_step"では常に数値だが、万一nullだった場合は
 * 順序を推測せず末尾へ送る(並び順を勝手に決めない)。
 */
function sortByRemainingSteps(candidates: RouteCandidateMove[]): RouteCandidateMove[] {
  return [...candidates].sort(
    (a, b) =>
      (a.remainingStepsAfter ?? Number.MAX_SAFE_INTEGER) - (b.remainingStepsAfter ?? Number.MAX_SAFE_INTEGER),
  );
}

/**
 * 現在局面について分かっている事実を、表示順に並べて返す。
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 *
 * 空配列は「表示すべき事実が無い」ことを意味する(呼び出し側はブロックごと描画しない)。
 */
export function detectNextConsiderations(input: NextConsiderationInput): NextConsiderationFact[] {
  // 目標形が決まっていない・対局が終わっている局面では、何も述べない。
  if (input.targetShapeId === undefined) return [];
  if (input.isGameEnd) return [];

  // 形が完成している場合は、それだけを単独で述べる(他の事実は併記しない)。
  if (input.missingSquares.length === 0) {
    // 形の名前が分からない場合は文言を組み立てられないため、推測せず何も述べない。
    if (input.shapeName === null) return [];
    return [
      makeFact("shape_completed", {
        shapeName: input.shapeName,
        shapeReviewStatus: input.shapeReviewStatus,
      }),
    ];
  }

  const facts: NextConsiderationFact[] = [];

  if (input.inCheck) facts.push(makeFact("in_check"));

  // 準備手(kind: "preparation")は扱わない。準備手を「道のりの一手目」と述べるのは
  // 事実として誤りであり、準備手の存在自体はUnit 1の経路ブロックが既に示している。
  const routeSteps = input.candidateMoves.filter((candidate) => candidate.kind === "route_step");

  if (routeSteps.length > 0) {
    for (const candidate of sortByRemainingSteps(routeSteps)) {
      facts.push(
        makeFact("route_first_move_playable", {
          moveUsi: candidate.moveUsi,
          targetSquare: candidate.targetSquare,
          targetPiece: candidate.targetPiece,
        }),
      );
    }
  } else if (input.routes.length > 0) {
    // 経路はあるが、経路そのものの一手目が1つも候補手になっていない
    // (準備手しか指せない場合を含む)。経路自体が1件も無い場合(経路を計算できなかった
    // 場合)は、Unit 1の経路ブロックが既にその旨を表示しているため、ここでは述べない。
    facts.push(makeFact("no_playable_route_first_move"));
  }

  return facts;
}
