// STEP U6-L(2026-09-13 の独立監査の指摘、必須3)。
// **本番の解析が失敗した行で、searchPvs が null になる**ことを見張る。
//
// 【なぜ別ファイルなのか】
// 失敗の経路(safeComputeReachablePlan が undefined を返す)を自然な入力で作るのは
// 難しい ― ③の計算は自前の try/catch を持ち、候補手の探索は候補手が0件の局面では
// そもそも呼ばれないためである。そこでこのファイルだけモジュールをモックする。
// モックはファイル単位で効くので、他のテスト(recorder.test.ts)へは波及させない。
//
// 【何を見張っているのか】
// 「測れなかった(null)」と「測ったが0本だった([])」を、**同じ値にしない**こと。
// 当初の実装は `result?.searchPvs ?? []` で、両方が `[]` になっていた
// (一つの値に二つの意味。既知事項 P-23 と同じ型)。

import { describe, expect, it, vi } from "vitest";
import type { GameState } from "../../../apps/server/src/game/gameSession.js";
import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";

vi.mock("../../../apps/server/src/api/stateResponse.js", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../../apps/server/src/api/stateResponse.js")>();
  return {
    ...actual,
    // 本番が失敗した(内部で例外を握りつぶして undefined を返した)状況だけを作る。
    // buildStateResponseWithPlan は本物のまま(記録行の組み立ては本番どおり)。
    safeComputeReachablePlan: async () => undefined,
  };
});

const { buildReadyRecord } = await import("./recorder.js");

const STARTPOS_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

function startState(): GameState {
  return { sfen: STARTPOS_SFEN, moveHistory: [], forcedPliesUsed: 0 };
}

function unusedEngine(): LowPriorityEngine {
  return {
    position: () => {},
    setMultiPv: () => {},
    goMultiPv: () => {
      throw new Error("呼ばれないはず(safeComputeReachablePlan をモックしているため)");
    },
  };
}

describe("buildReadyRecord: 本番の解析が失敗した行", () => {
  it("searchPvs は null になる(空配列にしない)", async () => {
    const { line } = await buildReadyRecord(
      startState(),
      2,
      "7g7f",
      "3c3d",
      unusedEngine(),
      false,
      null,
      null,
      [],
      unusedEngine(),
      0, // referenceNodes=0: ハーネス側の engineReference も測らない
      unusedEngine(),
    );

    const parsed = JSON.parse(line) as { searchPvs?: unknown };
    expect(parsed.searchPvs).toBeNull();
    // 欄そのものは出す(「欄が無い」= 古い記録 とも混ぜない)。
    expect(Object.keys(JSON.parse(line) as object)).toContain("searchPvs");
  });
});
