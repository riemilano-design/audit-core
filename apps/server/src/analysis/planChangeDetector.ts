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
// 今回ユーザーが実際に指した手を除いたものについて、現在局面で合法な手が
// 1つも残っていない場合」をplanChanged=trueとする。
// - targetShapeIdが前回と現在で一致しない場合(目標形の選択変更・フォールバック
//   変化を含む)は判定対象外(false)とする。ユーザー自身の操作による変化を
//   「相手の手による崩れ」と混同しないため。
// - 除外後に比較対象の候補手が0件になった場合(=ユーザーが唯一の候補手を
//   そのまま指した場合を含む)は、「計画が崩れた」とは断定せずfalseとする
//   (承認事項3: 比較対象が無いことと、相手による崩れは別事象として扱う)。
// - 上記以外(targetPieceの消失・typical_build_orderの変化・より良い別ルートの
//   発見・エンジン評価値等)は、今回のUnit1では判定条件に一切含めない。

export interface PlanSnapshot {
  /** ⑥で実際に採用されたshapeId(resolvedTargetShapeId)。 */
  targetShapeId: string;
  /** ⑦(pathPlanner.ts)が返したcandidateMovesのUSI文字列一覧。 */
  candidateMoveUsis: string[];
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

  const remaining = previous.candidateMoveUsis.filter((usi) => usi !== playedMoveUsi);
  if (remaining.length === 0) return false;

  const legalSet = new Set(currentLegalMoveUsis);
  return !remaining.some((usi) => legalSet.has(usi));
}
