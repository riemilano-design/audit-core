// pieceThreatFocusExplanation.ts(STEP 5-F、docs/STEP_5-F_PLAN_2026-09-12.md A-2a)のテスト。
//
// 【校正について】
// 実装前に、固定棋譜4局の記録(scripts/playtest/out/baseline-2026-09-12/*.jsonl。
// .gitignore配下のためテストからは参照しない)にこの関数を実際に掛け、計画書2.1の
// 実測(A=10件・B=8件・C=2件、engineReferenceのあるready行59件)と一致することを
// 確かめた(2026-09-12。手元で1回実行して確認する方式=計画書「測り方(i)」)。
// 以下のテストのSFEN・マス・駒名は、その校正で実際に出た組み合わせをそのまま
// 使っている(初期局面の9i=香・7i=銀・6i=金・8i=桂は標準の初期配置そのもの)。

import { describe, expect, it } from "vitest";
import type { EngineReference } from "./engineReference.js";
import { explainPieceThreatFocus } from "./pieceThreatFocusExplanation.js";

const INITIAL_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

function reference(overrides: Partial<EngineReference> = {}): EngineReference {
  return {
    baseline: { scoreCp: 0, mate: null, bestmove: "2h5h" },
    afterPass: { scoreCp: -300, mate: null, bestmove: "9i9h", captureSquare: "9i" },
    dropCp: 300,
    nodes: 4_000_000,
    ...overrides,
  };
}

describe("explainPieceThreatFocus", () => {
  it("EngineReferenceがnullなら出さない", () => {
    expect(
      explainPieceThreatFocus({ engineReference: null, bandSquares: [], sfen: INITIAL_SFEN }),
    ).toBeNull();
  });

  it("閾値(300cp)未満なら出さない", () => {
    const engineReference = reference({ dropCp: 299 });
    expect(
      explainPieceThreatFocus({ engineReference, bandSquares: [], sfen: INITIAL_SFEN }),
    ).toBeNull();
  });

  it("mateが絡む(H-2)なら出さない", () => {
    const engineReference = reference({
      baseline: { scoreCp: null, mate: 3, bestmove: "2h5h" },
      dropCp: 500, // dropCpの値によらず、mateが絡む時点で止まることを確かめる
    });
    expect(
      explainPieceThreatFocus({ engineReference, bandSquares: [], sfen: INITIAL_SFEN }),
    ).toBeNull();
  });

  it("captureSquareが無ければ出さない", () => {
    const engineReference = reference({
      afterPass: { scoreCp: -300, mate: null, bestmove: "9i9h", captureSquare: null },
    });
    expect(
      explainPieceThreatFocus({ engineReference, bandSquares: [], sfen: INITIAL_SFEN }),
    ).toBeNull();
  });

  it("(A) 帯が1件だけで、その1件がcaptureSquareと同じマスなら出さない", () => {
    const engineReference = reference(); // captureSquare: "9i"
    expect(
      explainPieceThreatFocus({ engineReference, bandSquares: ["9i"], sfen: INITIAL_SFEN }),
    ).toBeNull();
  });

  it("(B) captureSquareが帯に含まれ、帯が2件以上なら「いま注意する駒のうち、」から始まる文", () => {
    const engineReference = reference(); // captureSquare: "9i"(香)
    expect(
      explainPieceThreatFocus({ engineReference, bandSquares: ["6h", "9i"], sfen: INITIAL_SFEN }),
    ).toBe("いま注意する駒のうち、このまま何もしないと、あなたの９九の香が取られる可能性があります。");
  });

  it("(C) captureSquareが帯に含まれないなら、その句が付かない文", () => {
    const engineReference = reference({
      afterPass: { scoreCp: -300, mate: null, bestmove: "7i7h", captureSquare: "7i" },
    });
    expect(
      explainPieceThreatFocus({ engineReference, bandSquares: [], sfen: INITIAL_SFEN }),
    ).toBe("このまま何もしないと、あなたの７九の銀が取られる可能性があります。");
  });

  it("駒名が解決できない(captureSquareに駒が無い)場合は出さない", () => {
    const engineReference = reference({
      afterPass: { scoreCp: -300, mate: null, bestmove: "5f5e", captureSquare: "5e" },
    });
    // 初期局面の5eは空マス(pieceThreatFocusExplanationは推測して名前を付けない)。
    expect(
      explainPieceThreatFocus({ engineReference, bandSquares: [], sfen: INITIAL_SFEN }),
    ).toBeNull();
  });
});
