// recorder.ts の toCachedPlan が、本番関数の戻り値を取りこぼさずに詰め替えるか。
//
// 【なぜこのテストが要るか(STEP 5-F の A-4 独立監査の指摘。必須 1)】
// CachedReachablePlan.plan.focusText は apps/server/src/api/stateResponse.ts で
// **optional**(`focusText?: string | null`)である。そのため toCachedPlan の
// `focusText: result.focusText,` の **1 行を消しても tsc は通り、既存のテストも
// 落ちず、記録だけが null になる。**
//
// これは 2026-09-12 に実際に踏んだ穴である(計画書 14.13)。focusEngine を渡す
// 配線(入口)だけを直し、受け取った結果を詰め替える側(出口)を数えていなかった。
// 型検査もテストも緑のまま、固定棋譜 43 行すべてで focusText が null になった。
// 既知事項 P-24 の型。
//
// **コメントで「気をつけろ」と書くのではなく、気をつけなくても済む手順にする**
// (計画書 13.11 の一般則)。だからコメントではなくテストを置く。
//
// このテストは将棋の判断をしない。本番関数の戻り値の欄が、記録へ渡る器
// (CachedReachablePlan)に入っているかどうかだけを見る。

import { describe, expect, it } from "vitest";
import { buildReadyRecord, toCachedPlan } from "./recorder.js";
import type { GameState } from "../../../apps/server/src/game/gameSession.js";
import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { MultiPvGoResult } from "../../../apps/server/src/engine/usiEngine.js";

const SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

/** safeComputeReachablePlan の戻り値の形(必要な欄だけ)。 */
function planResult(overrides: Record<string, unknown> = {}) {
  return {
    reachableShapes: [],
    candidateMove: undefined,
    targetShapeId: undefined,
    searchPvs: [],
    ...overrides,
  } as Awaited<ReturnType<typeof import("../../../apps/server/src/api/stateResponse.js").safeComputeReachablePlan>>;
}

describe("toCachedPlan", () => {
  // ここが本題。この 1 件が、詰め替え漏れを見張る。
  it("focusText を詰め替える(文がある場合)", () => {
    const text = "このまま何もしないと、あなたの８七の歩が取られる可能性があります。";
    const cached = toCachedPlan(SFEN, planResult({ focusText: text }));
    expect(cached?.plan.focusText).toBe(text);
  });

  it("focusText が null(出さないと決めた場合)もそのまま運ぶ", () => {
    const cached = toCachedPlan(SFEN, planResult({ focusText: null }));
    expect(cached?.plan.focusText).toBeNull();
  });

  it("focusText が undefined(③を計算していない場合)もそのまま運ぶ", () => {
    const cached = toCachedPlan(SFEN, planResult({ focusText: undefined }));
    expect(cached?.plan.focusText).toBeUndefined();
  });

  // 【欄を増やしたときに、この見張りごと増やしてもらうための 1 件】
  // 本番の戻り値に欄が増えたら、ここも増やす。optional な欄は詰め替えを
  // 忘れても型が通るため、tsc は教えてくれない。
  it("本番の戻り値のうち、記録へ運ぶと決めた欄がすべて入っている", () => {
    const text = "このまま何もしないと、あなたの８七の歩が取られる可能性があります。";
    const cached = toCachedPlan(
      SFEN,
      planResult({ reachableShapes: [], candidateMove: undefined, targetShapeId: "honmino", focusText: text }),
    );
    expect(cached).toEqual({
      sfen: SFEN,
      targetShapeId: "honmino",
      plan: { reachableShapes: [], candidateMove: undefined, focusText: text },
    });
  });

  it("本番関数が失敗(undefined)を返したら undefined のまま", () => {
    expect(toCachedPlan(SFEN, undefined)).toBeUndefined();
  });
});

// --- STEP U6-L(docs/STEP_U6-L_PLAN_2026-09-13.md 5. B-1)。読み筋の「出口」の見張り。 ---
//
// 【なぜ要るか】
// searchPvs は本番の戻り値では必須欄なので、**本番側で埋め忘れれば tsc が止める。**
// しかし**ハーネスが受け取った結果を記録行へ詰め替える 1 行**を消しても、tsc は
// 通ってしまう(buildRecordLine へ渡す値が減るだけ)。A-4 で踏んだのはまさにここで、
// 入口だけ直して出口を数えなかった。だから出口にテストを置く。
//
// 本番関数(safeComputeReachablePlan)は実際に呼ぶ。エンジンだけを差し替える
// (将棋の判断・探索の中身は本番のまま。ここでは複製しない)。

const STARTPOS_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

/** goMultiPv が常に同じ1本を返すだけのエンジン。実際のプロセスは起動しない。 */
function stubEngine(pv: string[], opts: { lowerbound?: boolean } = {}): LowPriorityEngine {
  const result: MultiPvGoResult = {
    bestmove: pv[0],
    ponder: undefined,
    lines: [
      {
        multipv: 1,
        score: { type: "cp", value: 42 },
        pv,
        lowerbound: opts.lowerbound ?? false,
        upperbound: false,
      },
    ],
    infoLines: [],
  };
  return {
    position: () => {},
    setMultiPv: () => {},
    goMultiPv: async () => result,
  };
}

function startState(): GameState {
  return { sfen: STARTPOS_SFEN, moveHistory: [], forcedPliesUsed: 0 };
}

describe("buildReadyRecord の searchPvs(STEP U6-L)", () => {
  it("本番が③を作るのに使った探索の読み筋が、ready 行の JSON に載る", async () => {
    const { line } = await buildReadyRecord(
      startState(),
      2,
      "7g7f",
      "3c3d",
      stubEngine(["7g7f"]),
      false,
      null,
      null,
      [],
      stubEngine(["7g7f"]),
      0, // referenceNodes=0: ハーネス側の engineReference は測らない
      stubEngine(["8h2b", "3a2b", "2g2f"]), // focusEngine
    );

    const parsed = JSON.parse(line) as { searchPvs?: Array<Record<string, unknown>> };
    expect(parsed.searchPvs).toBeDefined();
    // ③は baseline と afterPass の2本を探索する。
    expect(parsed.searchPvs?.map((o) => o.source)).toEqual(["focus_baseline", "focus_after_pass"]);
    expect(parsed.searchPvs?.[0]?.pv).toEqual(["8h2b", "3a2b", "2g2f"]);
    expect(parsed.searchPvs?.[0]?.multipv).toBe(1);
  });

  it("lowerbound が立った読み筋も、立ったまま記録へ運ぶ", async () => {
    const { line } = await buildReadyRecord(
      startState(),
      2,
      "7g7f",
      "3c3d",
      stubEngine(["7g7f"]),
      false,
      null,
      null,
      [],
      stubEngine(["7g7f"]),
      0,
      stubEngine(["8h2b"], { lowerbound: true }),
    );

    const parsed = JSON.parse(line) as { searchPvs?: Array<Record<string, unknown>> };
    expect(parsed.searchPvs?.every((o) => o.lowerbound === true)).toBe(true);
  });

  it("長さ1の読み筋も捨てずに記録する(記録側に長さの門番を置かない)", async () => {
    const { line } = await buildReadyRecord(
      startState(),
      2,
      "7g7f",
      "3c3d",
      stubEngine(["7g7f"]),
      false,
      null,
      null,
      [],
      stubEngine(["7g7f"]),
      0,
      stubEngine(["8h2b"]),
    );

    const parsed = JSON.parse(line) as { searchPvs?: Array<Record<string, unknown>> };
    expect(parsed.searchPvs?.map((o) => (o.pv as string[]).length)).toEqual([1, 1]);
  });

  it("immediate 行には searchPvs のキー自体が出ない(既存のJSONLの形を変えない)", async () => {
    const { buildImmediateRecord } = await import("./recorder.js");
    const { line } = buildImmediateRecord(startState(), 1, "7g7f", null, false, null, null, []);
    expect(Object.keys(JSON.parse(line) as object)).not.toContain("searchPvs");
  });

});