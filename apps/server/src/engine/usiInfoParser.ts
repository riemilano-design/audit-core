// USIエンジンが`go`中に返す`info`行のうち、MultiPV安全確認(Phase2 Unit3)が必要とする
// multipv番号・score(cp/mate)・pv(読み筋)だけを取り出す、純粋なパーサー。
//
// 既存のusiEngine.ts の go() は、`score cp` を正規表現1本で(multipvを区別せず、
// 最後に見つかった値を採用するだけの)簡易的な方法で読み取っている。これは
// 単一bestmove APIとしては十分だが、MultiPV(複数の候補読み筋)を扱うには
// 「どのinfo行がどのmultipv番号のものか」を区別できる必要があるため、
// 本ファイルを新設して責務を分離する(既存のgo()自体は変更しない。
// 「既存の単一bestmove APIを壊さない」という制約に対応)。
//
// 【scoreの意味(perspective)について】
// USIプロトコル(UCIも同様)の慣例として、`score cp <x>` / `score mate <x>` は
// その`go`を実行した局面(=直前の`position`コマンドで設定した局面)における
// 「手番側から見た」評価値であり、xが正であれば手番側が優勢であることを意味する。
// これはUSIプロトコル自体の定義であり、本実装が独自に定めたものではない。
// 本パーサーはこの値を一切加工・符号反転せず、エンジンが出力したそのままの値を
// 保持するだけに責務を限定する(手番が変わった局面の評価値との比較・正規化は、
// 本Unitでは行わない。呼び出し側が局面ごとの手番を踏まえて解釈すること)。
//
// 【安全性判定について】
// このファイルはinfo行のパース(構造化)のみを行う。「この評価値は良い/悪い」
// といった評価・判定は一切行わない(CLAUDE.mdルール3番・6番、および
// candidateMoveSafetyCheck.tsのファイル冒頭コメントを参照)。

export type UsiScoreType = "cp" | "mate";

export interface UsiScore {
  type: UsiScoreType;
  /**
   * cpならセンチポーン値、mateなら詰みまでの手数。
   * 符号はUSIプロトコルの慣例どおり「その局面の手番側から見た」値であり、
   * 本パーサーはこれを反転・正規化しない(ファイル冒頭コメント参照)。
   */
  value: number;
}

export interface UsiInfoLine {
  /**
   * info行のmultipv番号。省略されている場合は1として扱う
   * (USI/UCIの慣例上、multipv未指定はMultiPV=1相当の単一読み筋を意味するため)。
   */
  multipv: number;
  /** scoreが含まれていない(または解析できない)info行の場合はundefined。 */
  score: UsiScore | undefined;
  /** pv(読み筋)のUSI形式指し手列。含まれていない場合は空配列。 */
  pv: string[];
  /** 元のinfo行全文(デバッグ・トレーサビリティ用)。 */
  raw: string;
}

const MULTIPV_PATTERN = /\bmultipv\s+(\d+)\b/;
const SCORE_PATTERN = /\bscore\s+(cp|mate)\s+(-?\d+)\b/;
const PV_PATTERN = /\bpv\s+(.+)$/;

/**
 * 1行のUSI出力を解析する。"info"で始まらない行(bestmove行・usiok等)はinfo行では
 * ないためundefinedを返す。"info"で始まるが個々のフィールド(multipv/score/pv)を
 * 解析できない場合は、そのフィールドだけ既定値(multipv:1 / score:undefined / pv:[])
 * にフォールバックし、例外は投げない(想定外のエンジン出力で対局・解析全体を
 * 止めないため)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 */
export function parseInfoLine(line: string): UsiInfoLine | undefined {
  const trimmed = line.trim();
  if (!trimmed.startsWith("info")) return undefined;

  const multipvMatch = trimmed.match(MULTIPV_PATTERN);
  const multipv = multipvMatch ? Number(multipvMatch[1]) : 1;

  const scoreMatch = trimmed.match(SCORE_PATTERN);
  const score: UsiScore | undefined = scoreMatch
    ? { type: scoreMatch[1] as UsiScoreType, value: Number(scoreMatch[2]) }
    : undefined;

  const pvMatch = trimmed.match(PV_PATTERN);
  const pv = pvMatch ? pvMatch[1]!.trim().split(/\s+/).filter((s) => s.length > 0) : [];

  return { multipv, score, pv, raw: line };
}
