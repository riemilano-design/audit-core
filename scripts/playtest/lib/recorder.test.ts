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
import { toCachedPlan } from "./recorder.js";

const SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

/** safeComputeReachablePlan の戻り値の形(必要な欄だけ)。 */
function planResult(overrides: Record<string, unknown> = {}) {
  return {
    reachableShapes: [],
    candidateMove: undefined,
    targetShapeId: undefined,
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
