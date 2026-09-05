// pathPlanner.ts(⑦候補手)のスナップショットを、着手の前後で突き合わせるための
// Phase3 Unit1(検知のみ)のロジック。docs/PHASES.md Phase3の成果物のうち、
// 「計画済みの道筋が相手の手によって崩れたことを検知するロジック」の最小部分を実装する。
//
// 【今回のUnit1が扱わないこと(重要)】
// 再計画・変更理由の生成・エンジン評価による判定は一切行わない(いずれもUnit1の
// 承認範囲外。別Unitとして改めて計画・承認を経る)。
//
// 【判定条件(人間承認済み)】
// 「ユーザーが着手する直前に保存したPlanSnapshotのcandidateMoveUsisのうち、
// 今回ユーザーが実際に指した手、および同じ移動先マス(targetSquare)を持つ
// 兄弟候補を除いたものについて、現在局面で合法な手が1つも残っていない場合」を
// planChanged=trueとする。
// - targetShapeIdが前回と現在で一致しない場合(目標形の選択変更・フォールバック
//   変化を含む)は判定対象外(false)とする。ユーザー自身の操作による変化を
//   「相手の手による崩れ」と混同しないため。
// - 除外後に比較対象の候補手が0件になった場合(=ユーザーが唯一の候補手を
//   そのまま指した場合、または複数候補のうち1つを指して兄弟候補も含めて
//   除外された場合を含む)は、「計画が崩れた」とは断定せずfalseとする
//   (承認事項3: 比較対象が無いことと、相手による崩れは別事象として扱う)。
// - 上記以外(targetPieceの消失・typical_build_orderの変化・より良い別ルートの
//   発見・エンジン評価値等)は、今回のUnit1では判定条件に一切含めない。
//
// 【兄弟候補の除外について(Unit1の既知課題を修正、人間承認済み)】
// pathPlanner.tsの設計上、1回のPathPlanResultが返すcandidateMovesは常に同じ
// targetSquare(移動先マス)を共有する。そのため、ユーザーが複数候補のうち
// 1つを実際に指すと、targetSquareが自分の駒で埋まり、残りの兄弟候補は
// 「自分の駒がある場所には動けない」という基本ルールにより、相手の着手とは
// 無関係に非合法化される。これは相手による計画崩壊ではなく、計画を正常に
// 実行した結果であるため、実際に指した手と同じ移動先マスを持つ候補も
// remainingから除外する。USI文字列のパースにはshogiops/utilの既存
// parseUsi(pathPlanner.ts等が既に使っている手法)を再利用し、新しい将棋知識・
// 評価値・利き判定・エンジン・LLMは一切導入しない。
// パースに失敗した場合(型上ほぼ起こらないが安全側の設計として)は、
// 誤って除外しない(=remainingに残す。falseに倒すよりtrue側に残す)。

// 【Phase6 Unit1で追加した兄弟候補の判定基準(移動元が同じ場合)】
// routePlanner.tsは「経路を塞いでいる自分の駒をどかす準備手」を候補にすることがある。
// 準備手は「同じ駒(同じ移動元)を、別々の移動先へ動かす」候補の集まりであるため、
// ユーザーがそのうち1つを実際に指すと、その駒は移動元から居なくなり、残りの準備手は
// 相手の着手とは無関係に非合法化する。これは計画を正常に実行した結果であって
// 相手による計画崩壊ではないため、移動先が同じ場合(既存基準)に加えて、
// 移動元が同じ場合も兄弟候補として除外する。
// なお従来のpathPlanner.tsの候補は常に移動先が同一だったため、移動元が同じ候補は
// 必ず移動先も同じであり既に除外されていた。したがってこの追加は、
// 既存(Phase3)の判定結果を変えない(テストで固定している)。

import { isDrop, parseUsi } from "shogiops/util";

export interface PlanSnapshot {
  /** ⑥で実際に採用されたshapeId(resolvedTargetShapeId)。 */
  targetShapeId: string;
  /** ⑦(pathPlanner.ts)が返したcandidateMovesのUSI文字列一覧。 */
  candidateMoveUsis: string[];
}

/**
 * candidateUsiが、playedMoveUsiと同じ移動先マス(to)、または同じ移動元マス(from)を持つ
 * 「兄弟候補」かどうかを判定する(移動元による判定を加えた理由はファイル冒頭のコメント参照)。
 * いずれかのパースに失敗した場合は、安全側に倒し兄弟候補とは
 * 判定しない(=falseを返し、remainingに残す)。
 * ドロップ(打つ手)は移動元を持たないため、移動元による判定の対象外とする。
 */
function isSiblingCandidate(candidateUsi: string, playedMoveUsi: string): boolean {
  const playedMove = parseUsi(playedMoveUsi);
  if (!playedMove) return false;
  const candidateMove = parseUsi(candidateUsi);
  if (!candidateMove) return false;
  if (candidateMove.to === playedMove.to) return true;
  if (isDrop(candidateMove) || isDrop(playedMove)) return false;
  return candidateMove.from === playedMove.from;
}

/**
 * 前回のPlanSnapshot・今回ユーザーが実際に指した手・現在の目標形・現在の合法手一覧から、
 * 「相手の手によって前回計画の前提が崩れたか」を機械的に判定する。
 *
 * エンジン・LLMには一切依存しない純粋関数(決定的)。
 */
export function detectPlanChange(
  previous: PlanSnapshot | undefined,
  playedMoveUsi: string,
  currentTargetShapeId: string | undefined,
  currentLegalMoveUsis: string[],
): boolean {
  if (!previous) return false;
  if (previous.targetShapeId !== currentTargetShapeId) return false;

  const remaining = previous.candidateMoveUsis.filter(
    (usi) => usi !== playedMoveUsi && !isSiblingCandidate(usi, playedMoveUsi),
  );
  if (remaining.length === 0) return false;

  const legalSet = new Set(currentLegalMoveUsis);
  return !remaining.some((usi) => legalSet.has(usi));
}
