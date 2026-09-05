// pathPlanner.tsが列挙した候補手(PathPlanCandidateMove[])を、USIエンジンのMultiPV結果と
// 突き合わせるための基盤。docs/PHASES.md Phase2の成果物「候補手とエンジンのMultiPV結果を
// 突き合わせ、安全確認(悪手排除)を行うロジック」のうち、MultiPV解析結果の取得と
// candidateMovesとの対応付けまでを実装する。
//
// 【このモジュールが絶対にしないこと(重要)】
// 「この手が最善」「この手を指すべき」「この手は悪手」「この手が安全」
// 「候補Aより候補Bが優れている」といった評価・判定・除外は一切行わない。
//
// 理由: CLAUDE.md/docs/PHASES.md/docs/ROLES.mdのいずれにも、「エンジン評価値の差が
// 何cp(またはmate手数がどう)であれば"明らかな悪手"とみなすか」という具体的な閾値の
// 定義が存在しない。根拠のない閾値を勝手に発明することは、CLAUDE.mdルール4番
// (将棋の知識を人間のレビューなしに確定しない)・ルール6番(断定できないことは
// 断定しない)の精神に反する。そのため本モジュールは、
//   1. 現在局面のMultiPV評価を取得する
//   2. 各候補手を指した後の局面のMultiPV評価を取得する
//   3. candidateMovesとMultiPV結果を対応付ける
// までを行い、「安全かどうかの判定(safety verdict)」は今後も実装しない。
// 具体的な閾値の設計は、人間の承認を経て別途行う(現時点で予定はない)。
//
// 【engineReferenceAvailableについて(重要・命名の経緯)】
// このフィールドは元々safetyVerdictAvailableという名前で、常にfalse(literal型)
// だった。「安全と判定できたか」という意味に読めてしまい、CLAUDE.mdルール3・6と
// 衝突しかねないため、「エンジンによる参考評価を取得でき、candidateMovesとの
// 対応付けが確認できた」という機械的事実だけを表すengineReferenceAvailableへ
// 改名した。これは安全の判定結果では一切ない。現状の実装では、この関数が例外を
// 投げずに完了した場合は常にtrueになる(baseline・各候補の解析が1:1で揃って
// 得られたことを意味するだけで、その中身の値が良いか悪いかは問わない)。
// booleanのままにしているのは、将来checkCandidateMovesSafetyが部分失敗を
// 内部で扱うようになった場合に備え、呼び出し側(candidateMoveExplanation.ts)の
// 分岐を無駄にしないため。
//
// 【局面遷移について】
// 候補手を指した後の局面は、既存のrules/applyMove.ts(合法性確認込みの唯一の
// 局面遷移API)を使う。独自の局面遷移ロジックは複製しない。
//
// 【エンジンとの通信について】
// エンジンプロセスの起動・USI通信そのものはengine/usiEngine.ts(UsiEngine)の
// 責務であり、本モジュールは呼び出し側から注入されたエンジン(SafetyCheckEngine、
// gameSession.tsのOpponentEngineと同じ「必要なメソッドだけをPickする」設計)を
// 通じてのみ利用する。エンジンの生成・ハンドシェイクはserver.ts/gameSession.ts側の
// 責務であり、本Unitでは行わない(API/UI統合は対象外)。

import { applyMove } from "../rules/applyMove.js";
import type { GoOptions, MultiPvLine, UsiEngine } from "../engine/usiEngine.js";
import type { PathPlanCandidateMove } from "./pathPlanner.js";

export { IllegalMoveError } from "../rules/applyMove.js";
export { InvalidSfenError } from "../rules/sfenPosition.js";

/** UsiEngineのうち、本モジュールが実際に使うメソッドのみを要求する。
 * gameSession.tsのOpponentEngine(Pick<UsiEngine, "position" | "go">)と同じ設計方針。 */
export type SafetyCheckEngine = Pick<UsiEngine, "position" | "setMultiPv" | "goMultiPv">;

export interface CandidateMoveEvaluation {
  /** pathPlannerが返したUSI形式の指し手(そのまま)。 */
  moveUsi: string;
  /** この手を指した後の局面のSFEN(rules/applyMove.tsで遷移させたもの)。 */
  resultingSfen: string;
  /**
   * 遷移後の局面をエンジンにMultiPV解析させた生の結果(multipv番号昇順)。
   * scoreの符号はUSIプロトコルの慣例どおり「遷移後の局面の手番側(=相手)から見た」値であり、
   * ここでは反転・正規化しない(usiInfoParser.tsのファイル冒頭コメント参照)。
   * この値をどう解釈するか(有利/不利の判定)は本モジュールの責務外。
   */
  multiPv: MultiPvLine[];
}

export interface CandidateMoveSafetyCheckResult {
  /** 安全確認の対象となった、候補手を指す前の局面。 */
  baselineSfen: string;
  /** baselineSfenをエンジンにMultiPV解析させた生の結果(multipv番号昇順)。 */
  baselineMultiPv: MultiPvLine[];
  /** candidateMoves各手に対応するMultiPV解析結果(candidateMovesと同じ順序)。 */
  evaluations: CandidateMoveEvaluation[];
  /**
   * エンジンによる参考評価を取得でき、candidateMovesとの対応付けが確認できたか
   * という機械的事実。「安全」「悪手ではない」という判定を意味しない
   * (ファイル冒頭コメント参照)。呼び出し側は、この値の真偽に関わらず、
   * evaluationsの内容だけを根拠に「安全」「推奨」といった表示をしてはならない
   * (CLAUDE.mdルール3番)。falseの場合、evaluationsが不完全である可能性がある
   * ことを示す(現状の実装では、この関数は例外を投げないかぎり常にtrueを返す)。
   */
  engineReferenceAvailable: boolean;
}

export interface CheckCandidateMovesSafetyOptions {
  /** エンジンの思考時間(ミリ秒)。省略時はUsiEngine.goMultiPvの既定値に従う。 */
  movetimeMs?: GoOptions["movetimeMs"];
  /**
   * 指定した場合、解析前に engine.setMultiPv(multiPv) を呼ぶ。
   * 省略した場合はsetMultiPvを呼ばない(エンジン側の現在の設定をそのまま使う)。
   */
  multiPv?: number;
}

/**
 * pathPlanner.tsが返したcandidateMovesを、USIエンジンのMultiPV結果と対応付ける。
 *
 * 【処理内容】
 * 1. baselineSfen(候補手を指す前の局面)をエンジンに解析させる
 * 2. candidateMoves各手について、rules/applyMove.tsで局面を遷移させたうえで
 *    エンジンに解析させる(独自の局面遷移・合法性判定は行わない)
 * 3. 結果をcandidateMovesと同じ順序で対応付けて返す
 *
 * 【行わないこと】
 * 「どの候補が良いか」の判定・除外は行わない(ファイル冒頭コメント参照)。
 *
 * candidateMovesが空配列の場合、baselineの解析のみ行いevaluationsは空配列を返す
 * (安全なフォールバック。例外は投げない)。
 *
 * candidateMovesの中に、baselineSfenにおいて非合法な手が含まれていた場合は
 * IllegalMoveErrorを伝播させる(pathPlanner.tsは合法手のみを返す設計だが、
 * 独自の合法性判定を行わずrules層にそのまま委ねるため)。
 */
export async function checkCandidateMovesSafety(
  baselineSfen: string,
  candidateMoves: PathPlanCandidateMove[],
  engine: SafetyCheckEngine,
  options: CheckCandidateMovesSafetyOptions = {},
): Promise<CandidateMoveSafetyCheckResult> {
  const { movetimeMs, multiPv } = options;

  if (multiPv !== undefined) {
    engine.setMultiPv(multiPv);
  }

  engine.position(baselineSfen);
  const baseline = await engine.goMultiPv({ movetimeMs });

  const evaluations: CandidateMoveEvaluation[] = [];
  for (const candidate of candidateMoves) {
    const resultingSfen = applyMove(baselineSfen, candidate.moveUsi);
    engine.position(resultingSfen);
    const analyzed = await engine.goMultiPv({ movetimeMs });
    evaluations.push({ moveUsi: candidate.moveUsi, resultingSfen, multiPv: analyzed.lines });
  }

  return {
    baselineSfen,
    baselineMultiPv: baseline.lines,
    evaluations,
    engineReferenceAvailable: true,
  };
}
