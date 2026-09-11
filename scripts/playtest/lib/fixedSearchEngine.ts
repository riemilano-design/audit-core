// STEP T-6(A-2)。docs/STEP_T-6_PLAN_2026-09-11.md 2. A-2に従う。
//
// 回帰モード(replay.ts)のエンジン条件(設問1(b)、人間承認済み)を固定するための
// 薄いアダプタ。LowPriorityEngine(apps/server/src/engine/prioritizedEngine.ts)を
// そのまま包み、goMultiPv(options)を呼ぶときに、呼び出し側が指定した固定ノード数
// (nodes)を options へ追加して下(元のengine)へそのまま渡すだけで、position・
// setMultiPvは素通しする。本番関数の複製・改変はしない。
//
// nodesが0のときは包まず、渡されたengineをそのまま返す(本番条件movetimeへの
// 逃げ道。STEP T-6計画書 A-3の`--nodes 0`)。

import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { GoOptions, MultiPvGoResult } from "../../../apps/server/src/engine/usiEngine.js";

/**
 * `engine.goMultiPv(options)`を`{ ...options, nodes }`で下のengineへ渡すアダプタを返す。
 * `nodes`が0の場合は`engine`をそのまま返す(包まない)。
 */
export function withFixedSearch(engine: LowPriorityEngine, nodes: number): LowPriorityEngine {
  if (nodes === 0) return engine;

  return {
    position: (sfen: string, moves: string[] = []) => engine.position(sfen, moves),
    setMultiPv: (multiPv: number) => engine.setMultiPv(multiPv),
    goMultiPv: (options?: GoOptions): Promise<MultiPvGoResult> => engine.goMultiPv({ ...options, nodes }),
  };
}
