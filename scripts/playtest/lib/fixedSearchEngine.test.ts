// STEP T-6(A-2)のテスト。docs/STEP_T-6_PLAN_2026-09-11.md 2. A-2「テストは
// 偽のLowPriorityEngineで『nodesが付与される』『0なら素通し』を確認」に従う。

import { describe, expect, it } from "vitest";
import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { GoOptions, MultiPvGoResult } from "../../../apps/server/src/engine/usiEngine.js";
import { withFixedSearch } from "./fixedSearchEngine.js";

function makeFakeResult(): MultiPvGoResult {
  return { bestmove: "7g7f", ponder: undefined, lines: [], infoLines: [] };
}

function makeFakeEngine(): {
  engine: LowPriorityEngine;
  calls: { position: Array<{ sfen: string; moves: string[] }>; setMultiPv: number[]; goMultiPv: (GoOptions | undefined)[] };
} {
  const calls: {
    position: Array<{ sfen: string; moves: string[] }>;
    setMultiPv: number[];
    goMultiPv: (GoOptions | undefined)[];
  } = { position: [], setMultiPv: [], goMultiPv: [] };

  const engine: LowPriorityEngine = {
    position: (sfen: string, moves: string[] = []) => {
      calls.position.push({ sfen, moves });
    },
    setMultiPv: (multiPv: number) => {
      calls.setMultiPv.push(multiPv);
    },
    goMultiPv: async (options?: GoOptions): Promise<MultiPvGoResult> => {
      calls.goMultiPv.push(options);
      return makeFakeResult();
    },
  };

  return { engine, calls };
}

describe("withFixedSearch", () => {
  it("nodesが正の値のとき、goMultiPvの呼び出しにnodesを付与して下のengineへ渡す", async () => {
    const { engine, calls } = makeFakeEngine();
    const wrapped = withFixedSearch(engine, 4_000_000);

    await wrapped.goMultiPv({ movetimeMs: 2000 });

    expect(calls.goMultiPv).toEqual([{ movetimeMs: 2000, nodes: 4_000_000 }]);
  });

  it("nodesが正の値のとき、optionsが未指定でもnodesだけを付与する", async () => {
    const { engine, calls } = makeFakeEngine();
    const wrapped = withFixedSearch(engine, 100);

    await wrapped.goMultiPv();

    expect(calls.goMultiPv).toEqual([{ nodes: 100 }]);
  });

  it("nodesが正の値のとき、position・setMultiPvは素通しする", () => {
    const { engine, calls } = makeFakeEngine();
    const wrapped = withFixedSearch(engine, 100);

    wrapped.position("startpos", ["7g7f"]);
    wrapped.setMultiPv(3);

    expect(calls.position).toEqual([{ sfen: "startpos", moves: ["7g7f"] }]);
    expect(calls.setMultiPv).toEqual([3]);
  });

  it("nodesが0のとき、包まず元のengineをそのまま返す", () => {
    const { engine } = makeFakeEngine();
    const wrapped = withFixedSearch(engine, 0);

    expect(wrapped).toBe(engine);
  });
});
