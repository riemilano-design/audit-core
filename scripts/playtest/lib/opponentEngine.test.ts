// STEP D3b の試験(docs/STEP_D3b_PLAN_2026-09-15.md 5.1・10.4)。**エンジンは呼ばない。** go に渡った options を記録するだけの偽のエンジンを使う。
// 期待値は試験を回す前に手で書いた。

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { HighPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { GoOptions } from "../../../apps/server/src/engine/usiEngine.js";
import { buildHighPriorityHandles, parseOpponentNodesOption, withOpponentNodes } from "./opponentEngine.js";

const EXPLORE_TS = join(dirname(fileURLToPath(import.meta.url)), "..", "explore.ts");

/** position と go の引数を記録するだけの偽のエンジン。 */
function recordingEngine(): { engine: HighPriorityEngine; positions: unknown[][]; goOptions: (GoOptions | undefined)[] } {
  const positions: unknown[][] = [];
  const goOptions: (GoOptions | undefined)[] = [];
  const engine: HighPriorityEngine = {
    position: (...args) => {
      positions.push(args);
    },
    go: async (options) => {
      goOptions.push(options);
      return { bestmove: "7g7f", ponder: undefined, scoreCp: undefined, infoLines: [] };
    },
  };
  return { engine, positions, goOptions };
}

/** asHighPriority() を呼ぶたびに新しい偽のエンジンを作り、作ったものを順に残す偽の PrioritizedEngine。 */
function recordingPrioritizedEngine() {
  const created: ReturnType<typeof recordingEngine>[] = [];
  return {
    created,
    asHighPriority: (): HighPriorityEngine => {
      const recording = recordingEngine();
      created.push(recording);
      return recording.engine;
    },
  };
}

/**
 * TypeScript のソースからコメントを除く(行コメント `// …` とブロックコメント `/* … *\/`)。
 * **ソース照合はコードだけに当てる**(f2 の事前読み: コメントに書いた文字列で、否定の照合が赤になったり、肯定の照合が
 * コメントで通って沈黙したりするのを防ぐ ― 計画 10.4)。文字列リテラルの中の `//` は explore.ts の照合対象の行に無い。
 */
function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");
}

describe("withOpponentNodes(計画 5.1)", () => {
  it("F-O1 nodes 2000 を渡すと、go の options に nodes が足され、position と go の結果はそのまま通る", async () => {
    const fake = recordingEngine();
    const wrapped = withOpponentNodes(fake.engine, 2000);
    wrapped.position("startpos", ["7g7f"]);
    const result = await wrapped.go({ movetimeMs: 1000 });
    expect(fake.goOptions).toEqual([{ movetimeMs: 1000, nodes: 2000 }]);
    expect(fake.positions).toEqual([["startpos", ["7g7f"]]]);
    expect(result.bestmove).toBe("7g7f");
  });

  it("F-O2 nodes が undefined なら、同じエンジンをそのまま返し、options に nodes の欄が無い", async () => {
    const fake = recordingEngine();
    const wrapped = withOpponentNodes(fake.engine, undefined);
    expect(wrapped).toBe(fake.engine);
    await wrapped.go({ movetimeMs: 1000 });
    expect(fake.goOptions).toEqual([{ movetimeMs: 1000 }]);
    expect(Object.keys(fake.goOptions[0] ?? {})).toEqual(["movetimeMs"]);
  });

  it("F-O7 包みは go と position しか持たない(goMultiPv を持たないので LowPriorityEngine の代わりにならない)", () => {
    const wrapped = withOpponentNodes(recordingEngine().engine, 5);
    expect(Object.keys(wrapped).sort()).toEqual(["go", "position"]);
    expect("goMultiPv" in wrapped).toBe(false);
  });
});

describe("buildHighPriorityHandles(計画 5.1)", () => {
  it("F-O3 相手のハンドルだけに nodes 20000 が渡り、先手(E 読み)のハンドルには渡らない。ハンドルは別々に 2 つ作る", async () => {
    const prioritized = recordingPrioritizedEngine();
    const handles = buildHighPriorityHandles(prioritized, 20000);
    expect(prioritized.created).toHaveLength(2);
    expect(handles.opponent).not.toBe(handles.sente);

    await handles.opponent.go({ movetimeMs: 1000 });
    await handles.sente.go({ movetimeMs: 100 });

    const allOptions = prioritized.created.flatMap((recording) => recording.goOptions);
    expect(allOptions).toHaveLength(2);
    expect(allOptions).toContainEqual({ movetimeMs: 1000, nodes: 20000 });
    const senteOptions = allOptions.find((options) => options?.movetimeMs === 100);
    expect(senteOptions).toEqual({ movetimeMs: 100 });
    expect(Object.keys(senteOptions ?? {})).toEqual(["movetimeMs"]);
    // 相手の go と先手の go は、別々の偽のエンジンに届く
    expect(prioritized.created.map((recording) => recording.goOptions.length)).toEqual([1, 1]);
  });

  it("F-O4 opponentNodes が undefined なら、相手・先手とも options はそのまま", async () => {
    const prioritized = recordingPrioritizedEngine();
    const handles = buildHighPriorityHandles(prioritized, undefined);
    await handles.opponent.go({ movetimeMs: 1000 });
    await handles.sente.go({ movetimeMs: 100 });
    const allOptions = prioritized.created.flatMap((recording) => recording.goOptions);
    expect(allOptions).toEqual(expect.arrayContaining([{ movetimeMs: 1000 }, { movetimeMs: 100 }]));
    expect(allOptions.every((options) => !("nodes" in (options ?? {})))).toBe(true);
    expect(prioritized.created.map((recording) => recording.engine)).toContain(handles.opponent);
  });

  it("F-O8 相手の go に nodes を付けて渡した回数だけを数える(先手の go は数えない。opponentNodes が undefined なら 0)", async () => {
    const withNodes = buildHighPriorityHandles(recordingPrioritizedEngine(), 2000);
    expect(withNodes.opponentNodesGoCalls()).toBe(0);
    await withNodes.opponent.go({ movetimeMs: 1000 });
    await withNodes.opponent.go({ movetimeMs: 1000 });
    await withNodes.opponent.go({ movetimeMs: 1000 });
    await withNodes.sente.go({ movetimeMs: 100 });
    await withNodes.sente.go({ movetimeMs: 100 });
    expect(withNodes.opponentNodesGoCalls()).toBe(3);

    const withoutNodes = buildHighPriorityHandles(recordingPrioritizedEngine(), undefined);
    await withoutNodes.opponent.go({ movetimeMs: 1000 });
    await withoutNodes.opponent.go({ movetimeMs: 1000 });
    expect(withoutNodes.opponentNodesGoCalls()).toBe(0);
  });
});

describe("parseOpponentNodesOption(計画 5.1・10.4)", () => {
  it("F-O5 無ければ undefined、正の整数ならその数、0・負・小数・指数・符号・空白・先頭 0・文字・値なしはエラー", () => {
    expect(parseOpponentNodesOption(["--games", "10"])).toBeUndefined();
    expect(parseOpponentNodesOption(["--opponent-nodes", "2000", "--games", "10"])).toBe(2000);
    for (const bad of ["0", "-5", "1.5", "2e3", "+2000", " 2000", "2000 ", "abc", "02000", ""]) {
      expect(() => parseOpponentNodesOption(["--opponent-nodes", bad])).toThrow(/--opponent-nodes の値は正の整数/);
    }
    expect(() => parseOpponentNodesOption(["--games", "10", "--opponent-nodes"])).toThrow(/値が無い/);
  });
});

describe("F-O6 explore.ts の配線(コメントを除いたソースの照合。一方向の見張り ― P-32)", () => {
  it("コメントを除く関数は、行コメント・ブロックコメントの中の照合文字列を消し、コードの行は残す(先に校正する)", () => {
    const sample = [
      "// playOpponentMove(state, engine.asHighPriority(), getApprovedScenarioVariants())",
      "/* engine: handles.sente, */",
      "      state = await playOpponentMove(state, handles.opponent, getApprovedScenarioVariants()); // 相手",
    ].join("\n");
    const code = stripComments(sample);
    expect(code).not.toContain("engine.asHighPriority()");
    expect(code).not.toContain("engine: handles.sente,");
    expect(code).toContain("playOpponentMove(state, handles.opponent, getApprovedScenarioVariants());");
  });

  it("相手には handles.opponent、先手には handles.sente を渡し、asHighPriority を直接渡さない。asLowPriority の 6 か所は変わらない", () => {
    const code = stripComments(readFileSync(EXPLORE_TS, "utf-8"));
    expect(code).toContain("playOpponentMove(state, handles.opponent, getApprovedScenarioVariants())");
    expect(code).not.toContain("playOpponentMove(state, handles.sente");
    expect(code).not.toContain("playOpponentMove(state, engine.asHighPriority()");
    expect(code).toContain("engine: handles.sente,");
    expect(code).toContain("const handles = buildHighPriorityHandles(engine, opponentNodes);");
    expect(code.split("engine.asHighPriority()").length - 1).toBe(0);
    expect(code.split("engine.asLowPriority()").length - 1).toBe(6);
    expect(code).toContain("opponentNodes: parseOpponentNodesOption(argv)");
    expect(code).toContain("opponentNodes: opponentNodes ?? null,");
    expect(code).toContain("opponentNodesGoCalls: handles.opponentNodesGoCalls(),");
    expect(code).toContain("相手の go(nodes 付き)=${result.opponentNodesGoCalls}");
  });
});
