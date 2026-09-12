// STEP P-26: GET /api/game の起動条件(純粋関数)。
// server.tsには直接のテストが無いため、判定はここで確かめる。

import { describe, expect, it } from "vitest";

import { shouldStartBackgroundAnalysisOnGet } from "./backgroundAnalysisTrigger.js";

const KEY = "sfen-a|shape-a";
const OTHER_KEY = "sfen-b|shape-a";

describe("shouldStartBackgroundAnalysisOnGet", () => {
  // ここがP-26の本体。この組み合わせで誰も解析を始めなかった。
  it("候補手がunavailableでも、③がpendingなら起動する(P-26)", () => {
    expect(
      shouldStartBackgroundAnalysisOnGet(
        { candidateMoveState: "unavailable", focusTextState: "pending" },
        KEY,
        undefined,
      ),
    ).toBe(true);
  });

  it("候補手がpendingなら従来どおり起動する", () => {
    expect(
      shouldStartBackgroundAnalysisOnGet({ candidateMoveState: "pending", focusTextState: "pending" }, KEY, undefined),
    ).toBe(true);
  });

  it("両方とも待っていないなら起動しない", () => {
    expect(
      shouldStartBackgroundAnalysisOnGet({ candidateMoveState: "unavailable", focusTextState: "ready" }, KEY, undefined),
    ).toBe(false);
    expect(
      shouldStartBackgroundAnalysisOnGet({ candidateMoveState: "ready", focusTextState: "ready" }, KEY, undefined),
    ).toBe(false);
  });

  // (i) の歯止め。これが無いと、失敗し続ける局面でGETのたびに起動し直す。
  it("同じキーで一度失敗していたら起動しない", () => {
    expect(
      shouldStartBackgroundAnalysisOnGet({ candidateMoveState: "unavailable", focusTextState: "pending" }, KEY, KEY),
    ).toBe(false);
    expect(
      shouldStartBackgroundAnalysisOnGet({ candidateMoveState: "pending", focusTextState: "pending" }, KEY, KEY),
    ).toBe(false);
  });

  it("別のキー(局面か目標形が変わった)なら、失敗の記憶は効かない", () => {
    expect(
      shouldStartBackgroundAnalysisOnGet(
        { candidateMoveState: "unavailable", focusTextState: "pending" },
        OTHER_KEY,
        KEY,
      ),
    ).toBe(true);
  });

  it("failedPlanKeyがundefinedのときは歯止めが掛からない", () => {
    expect(
      shouldStartBackgroundAnalysisOnGet(
        { candidateMoveState: "unavailable", focusTextState: "pending" },
        KEY,
        undefined,
      ),
    ).toBe(true);
  });
});
