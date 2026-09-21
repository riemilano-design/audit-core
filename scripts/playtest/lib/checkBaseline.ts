// STEP FILL 作業 X(docs/STEP_FILL_PLAN_2026-09-22.md §1 の H1・H2、§2)。
//
// 【背景】本番の measureEngineReference(apps/server/src/analysis/engineReference.ts)は、
// 本人(先手)が王手中の局面では「パスが成立しない」という理由で reference を null にし、
// エンジンを一切呼ばない。そのため、王手中が続く局面には評価が一切付かず、優勢から
// 自玉の詰みへ変わる過程がグラフ・組・場面の集計から丸ごと抜ける(計画 §1 の H1・H2)。
//
// 【このファイルがやること】ハーネスの観測として、**現局面だけ**(手番を入れ替えたパスの
// 局面は読まない。王手中はパスが成立しないため)を MultiPV 1・固定ノード数で読む。
// **本番の measureEngineReference は変えない**(呼び出し側が別に呼ぶだけ)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・評価・閾値・文言
// - エンジンの探索アルゴリズムの複製(MultiPV の先頭行を読むだけの薄い変換のみ。
//   apps/server/src/analysis/engineReference.ts の sideFromMultiPv と同じ形だが、
//   private のため export されておらず、ここで同じ形を薄く保つ)

import { isGameOver, isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { MultiPvGoResult } from "../../../apps/server/src/engine/usiEngine.js";

/** 王手中の現局面だけを MultiPV 1 で読んだ結果。afterPass は無い(パスが成立しないため)。 */
export interface CheckBaseline {
  scoreCp: number | null;
  mate: number | null;
  bestmove: string | null;
  nodes: number;
}

function topLineOf(result: MultiPvGoResult): { scoreCp: number | null; mate: number | null; bestmove: string | null } {
  const top = result.lines[0];
  const score = top?.score;
  return {
    scoreCp: score?.type === "cp" ? score.value : null,
    mate: score?.type === "mate" ? score.value : null,
    bestmove: result.bestmove ?? null,
  };
}

/**
 * sfen(先手番の局面)が、終局でなく先手が王手中のときだけ、現局面を MultiPV 1・nodes 固定で読む。
 * それ以外(終局・王手中でない)は呼び出し側の条件と重ねてここでも確かめ、エンジンを呼ばずに null を返す。
 * エンジンの例外はここで握りつぶす(measureEngineReference と同じ ― 測れなかった、推測しない)。
 */
export async function measureCheckBaseline(
  sfen: string,
  engine: LowPriorityEngine,
  nodes: number,
): Promise<CheckBaseline | null> {
  if (isGameOver(sfen)) return null;
  if (!isInCheck(sfen, "sente")) return null;
  try {
    engine.setMultiPv(1);
    engine.position(sfen);
    const result = await engine.goMultiPv({ nodes });
    return { ...topLineOf(result), nodes };
  } catch {
    return null;
  }
}
