// STEP U6-L(docs/STEP_U6-L_PLAN_2026-09-13.md 3.1)。
// 本番が既に行った探索の読み筋(pv)を、記録のためだけに持ち回るための観測の型。
//
// 【このモジュールがやること】
// - MultiPvGoResult(engine/usiEngine.ts)から、探索1回ぶんの観測を組み立てる
//   純粋関数。エンジンもLLMもここでは呼ばない。
//
// 【このモジュールが絶対にやらないこと】
// - 将棋の判断・評価・閾値・文言。読み筋が「良い読み筋か」は判定しない。
// - 新しい探索。運ぶのは呼び出し側が既に持っている MultiPvGoResult だけである。
//
// 【なぜ本番側に置くのか(ハーネス側ではなく)】
// ③(focusText)と⑤(candidateMove)を作ったのと**同一の探索結果**を運ぶため。
// 別のところで測り直すと、同じ局面・同じ条件でも別の結果になりうる
// (2026-09-12に実測で3行踏んでいる。`claude-3` ply 22 では afterPass の最善手
// そのものが別の手だった。docs/STEP_5-F_PLAN_2026-09-12.md)。
// 「同じ設定で呼べば同じ結果」を前提にせず、**同じオブジェクトから値をコピーする**
// ことで構造的に同一性を保証する(計画書 1.1 決定1)。
//
// 【画面にも応答にも出さない】
// この観測は api/stateResponse.ts の ReachablePlanBody(HTTPの応答本体)には
// 入れない。server.ts も backgroundPlan へ写さない。記録(JSONL)へ運ぶのは
// ハーネス(scripts/playtest/lib/recorder.ts)だけである。

import type { MultiPvLine } from "../engine/usiEngine.js";

/** どの探索の読み筋か。③の2本と、候補手の安全確認のbaseline・各候補手。 */
export type SearchPvSource =
  /** ③: 現局面(analysis/engineReference.ts の baseline)。 */
  | "focus_baseline"
  /** ③: 手番を入れ替えた局面(同 afterPass)。 */
  | "focus_after_pass"
  /** ⑤: 候補手を指す前の局面(analysis/candidateMoveSafetyCheck.ts の baselineMultiPv)。 */
  | "candidate_baseline"
  /** ⑤: 候補手を1つ指した後の局面(同 evaluations[].multiPv)。 */
  | "candidate_after_move";

/** 探索1回・MultiPV1本ぶんの観測。 */
export interface SearchPvObservation {
  source: SearchPvSource;
  /** 実際に探索した局面(SFEN)。後から同じ局面を再現できるようにするため。 */
  sfen: string;
  /** source === "candidate_after_move" のときだけ、その候補手(USI)。他はnull。 */
  moveUsi: string | null;
  /** MultiPV番号。本STEPの時点では常に1のはず(計画書 2.1・予測P3)。 */
  multipv: number;
  scoreCp: number | null;
  mate: number | null;
  /**
   * 読み筋(USI形式の指し手列)。**長さで捨てない**(0手・1手もそのまま記録する)。
   * 記録の時点で捨てると、捨てた件数が分布から消えるため(計画書 1.2(a))。
   * 「何手未満を読み筋として使わないか」は使う側(U6-M)が決める門番であって、
   * 記録側の判断ではない。
   */
  pv: string[];
  /** 採用したinfo行に付いていた標識(engine/usiInfoParser.ts)。 */
  lowerbound: boolean;
  upperbound: boolean;
}

/**
 * 探索1回ぶんの MultiPvLine[] を観測の配列へ写す(1本につき1件)。
 * linesが空(info行が1つも解析できなかった)なら空配列を返す。
 * 値の加工・符号反転は一切行わない(usiInfoParser.tsの方針と同じ)。
 *
 * 引数に MultiPvGoResult 全体ではなく lines を取るのは、呼び出し側によっては
 * 手元にあるのが lines だけ(candidateMoveSafetyCheck.tsのbaselineMultiPv等)で
 * あり、**無い値をここで作らないため**である(bestmoveを空で埋めたりしない)。
 */
export function toSearchPvObservations(
  source: SearchPvSource,
  sfen: string,
  moveUsi: string | null,
  lines: readonly MultiPvLine[],
): SearchPvObservation[] {
  return lines.map((line) => ({
    source,
    sfen,
    moveUsi,
    multipv: line.multipv,
    scoreCp: line.score?.type === "cp" ? line.score.value : null,
    mate: line.score?.type === "mate" ? line.score.value : null,
    pv: line.pv,
    lowerbound: line.lowerbound,
    upperbound: line.upperbound,
  }));
}
