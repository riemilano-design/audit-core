// STEP D3(計画 Q-5)の試験。群ごとの合計が、入力ごとの分母の行を欄ごとに足したものになるかを見る。
// **期待値は手で計算した**(A の各欄を 1〜20、B をその 10 倍にして、合計は 11 倍)。

import { describe, expect, it } from "vitest";
import { renderDiagnosisTotals, totalDiagnosisCounts } from "./diagnosisTotals.js";
import type { DiagnosisCounts, DiagnosisRow } from "./failureEvent.js";

const A = {
  readyRows: 1,
  measured: 2,
  notMeasuredGameEnd: 3,
  notMeasuredInCheck: 4,
  notMeasurable: 5,
  unrecorded: 6,
  notEvaluation: 7,
  comparedPairs: 8,
  mateAfterPairs: 9,
  notComparedPairs: 10,
  dropCandidates: 11,
  matedIfPassPairs: 12,
  events: 13,
  fromAdvantage: 14,
  withCheck: 15,
  withMate: 16,
  windowShort: 17,
  beforeAfterPassMate: 18,
  beforeDropCpAtLeast: 19,
  cause1Draft: 20,
} satisfies DiagnosisCounts;

const B = {
  readyRows: 10,
  measured: 20,
  notMeasuredGameEnd: 30,
  notMeasuredInCheck: 40,
  notMeasurable: 50,
  unrecorded: 60,
  notEvaluation: 70,
  comparedPairs: 80,
  mateAfterPairs: 90,
  notComparedPairs: 100,
  dropCandidates: 110,
  matedIfPassPairs: 120,
  events: 130,
  fromAdvantage: 140,
  withCheck: 150,
  withMate: 160,
  windowShort: 170,
  beforeAfterPassMate: 180,
  beforeDropCpAtLeast: 190,
  cause1Draft: 200,
} satisfies DiagnosisCounts;

/** A + B を手で書いたもの。 */
const A_PLUS_B = {
  readyRows: 11,
  measured: 22,
  notMeasuredGameEnd: 33,
  notMeasuredInCheck: 44,
  notMeasurable: 55,
  unrecorded: 66,
  notEvaluation: 77,
  comparedPairs: 88,
  mateAfterPairs: 99,
  notComparedPairs: 110,
  dropCandidates: 121,
  matedIfPassPairs: 132,
  events: 143,
  fromAdvantage: 154,
  withCheck: 165,
  withMate: 176,
  windowShort: 187,
  beforeAfterPassMate: 198,
  beforeDropCpAtLeast: 209,
  cause1Draft: 220,
} satisfies DiagnosisCounts;

/** 比べた組が 1 つも無い入力(測っていない行だけ)。 */
const NO_PAIRS = {
  readyRows: 1,
  measured: 0,
  notMeasuredGameEnd: 0,
  notMeasuredInCheck: 0,
  notMeasurable: 0,
  unrecorded: 1,
  notEvaluation: 0,
  comparedPairs: 0,
  mateAfterPairs: 0,
  notComparedPairs: 0,
  dropCandidates: 0,
  matedIfPassPairs: 0,
  events: 0,
  fromAdvantage: 0,
  withCheck: 0,
  withMate: 0,
  windowShort: 0,
  beforeAfterPassMate: 0,
  beforeDropCpAtLeast: 0,
  cause1Draft: 0,
} satisfies DiagnosisCounts;

function counted(kifuId: string, counts: DiagnosisCounts): DiagnosisRow {
  return { kifuId, meta: undefined, result: { kind: "counted", counts, events: [] } };
}

function notCounted(kifuId: string): DiagnosisRow {
  return { kifuId, meta: undefined, result: { kind: "notCounted", errorName: "Error", message: "壊れた記録" } };
}

describe("totalDiagnosisCounts・renderDiagnosisTotals(計画 Q-5)", () => {
  it("F-Q1 数えた 2 本の件数を、20 の欄すべてについて足す(入力の件数は書き換えない)", () => {
    const totals = totalDiagnosisCounts([counted("a", A), counted("b", B)]);
    expect(totals).toEqual({ counted: ["a", "b"], notCounted: [], counts: A_PLUS_B });
    expect(A.readyRows).toBe(1);

    const lines = renderDiagnosisTotals([counted("a", A), counted("b", B)]);
    expect(lines[0]).toBe("## 合計(入力 2 本。数えた 2 本・数えられなかった 0 本)");
    expect(lines).toContain("| 11 | 22 | 33 | 44 | 55 | 66 | 77 | 88 | 99 | 110 |");
    expect(lines).toContain("| 121 | 154 | 165 | 176 | 187 | 198 | 209 | 132 | 143 | 220 |");
  });

  it("F-Q2 数えられなかった入力は合計に混ぜず、名前で並べる", () => {
    const rows = [notCounted("x"), counted("a", A)];
    expect(totalDiagnosisCounts(rows)).toEqual({ counted: ["a"], notCounted: ["x"], counts: A });

    const lines = renderDiagnosisTotals(rows);
    expect(lines[0]).toBe("## 合計(入力 2 本。数えた 1 本・数えられなかった 1 本)");
    expect(lines).toContain("- 合計に入れなかった入力(数えられなかった): x");
  });

  it("F-Q3 合計で比べた組が 0 なら、急落候補の欄は 0 ではなく「比べる組が無い」", () => {
    const lines = renderDiagnosisTotals([counted("a", NO_PAIRS), counted("b", NO_PAIRS)]);
    expect(lines).toContain("| 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |");
    expect(lines).toContain(
      "| 比べる組が無い | 比べる組が無い | 比べる組が無い | 比べる組が無い | 比べる組が無い | 比べる組が無い | 比べる組が無い | 0 | 0 | 0 |",
    );
  });

  it("F-Q4 入力が 1 本なら合計の節を出さない。数えた入力が 0 本なら counts は null で「数えた入力が無い」", () => {
    expect(renderDiagnosisTotals([counted("a", A)])).toEqual([]);

    const rows = [notCounted("x"), notCounted("y")];
    expect(totalDiagnosisCounts(rows)).toEqual({ counted: [], notCounted: ["x", "y"], counts: null });
    expect(renderDiagnosisTotals(rows)).toContain("- 数えた入力が無い");
  });
});
