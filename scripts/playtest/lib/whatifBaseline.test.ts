// STEP WHATIF 作業 3(docs/STEP_WHATIF_PLAN_2026-09-22.md §8.1-2)。baselineTable.ts に足す whatif の 6 行を、
// **合成の summary の数**で見張る(エンジン・ファイルの読み書きは無い純粋関数)。
//
// 【正解の置き方】分子・分母は植えた数から手で数えた値(実装の出力から写さない)。

import { describe, expect, it } from "vitest";
import {
  whatifInputProblems,
  whatifRateRowsOf,
  renderWhatifRateMarkdown,
  type WhatifFileEntry,
  type WhatifInputGroup,
  type WhatifSummaryCounts,
} from "./whatifBaseline.js";

const VALUES = { multiPv: 5, nodes: 1_000_000, startPly: 17 };

function summary(over: Partial<WhatifSummaryCounts> = {}): WhatifSummaryCounts {
  return {
    positionsRead: 10,
    matchesTop1: 4,
    withinMultiPv: 8,
    forkCount: 2,
    narrowHeldCount: 1,
    chanceHeldCount: 1,
    scenesRead: 3,
    attackNoLegalMoveCount: 1,
    ...over,
  };
}

function entry(over: Partial<WhatifFileEntry> = {}): WhatifFileEntry {
  return {
    name: "a.jsonl",
    path: "a.jsonl",
    kifuId: "k1",
    sha256: "sha-a",
    values: VALUES,
    summary: summary(),
    ...over,
  };
}

function group(label: string, entries: WhatifFileEntry[]): WhatifInputGroup {
  return { label, entries };
}

describe("whatifInputProblems(計画 §8.1-2)", () => {
  it("material が空なら問題を出す", () => {
    const problems = whatifInputProblems([], [group("p3", [entry()])], ["p3"]);
    expect(problems.some((p) => p.includes("--whatif-material の記録が無い"))).toBe(true);
  });

  it("--whatif-pool のラベルの記録が空なら問題を出す", () => {
    const problems = whatifInputProblems([entry()], [group("p3", [])], ["p3"]);
    expect(problems.some((p) => p.includes("--whatif-pool p3 の記録が無い"))).toBe(true);
  });

  it("--whatif-pool に同じラベルが 2 回あれば問題を出す", () => {
    const problems = whatifInputProblems(
      [entry()],
      [group("p3", [entry({ name: "b", path: "b", kifuId: "k2", sha256: "sha-b" })]), group("p3", [entry({ name: "c", path: "c", kifuId: "k3", sha256: "sha-c" })])],
      ["p3"],
    );
    expect(problems.some((p) => p.includes("--whatif-pool に同じラベルが 2 回ある"))).toBe(true);
  });

  it("--whatif-pool のラベルが --pool に無ければ問題を出す(逆向きも)", () => {
    const onlyWhatifExtra = whatifInputProblems([entry()], [group("p4", [entry({ name: "b", path: "b", kifuId: "k2", sha256: "sha-b" })])], ["p3"]);
    expect(onlyWhatifExtra.some((p) => p.includes("--whatif-pool のラベルが --pool に無い: p4"))).toBe(true);

    const onlyPoolExtra = whatifInputProblems([entry()], [group("p3", [entry({ name: "b", path: "b", kifuId: "k2", sha256: "sha-b" })])], ["p3", "p4"]);
    expect(onlyPoolExtra.some((p) => p.includes("--pool のラベルに対応する --whatif-pool が無い: p4"))).toBe(true);
  });

  it("最後の行が summary でない記録は問題を出す", () => {
    const problems = whatifInputProblems([entry({ summary: undefined })], [group("p3", [entry({ name: "b", path: "b", kifuId: "k2", sha256: "sha-b" })])], ["p3"]);
    expect(problems.some((p) => p.includes("最後の行が summary でない"))).toBe(true);
  });

  it("同じ kifuId・sha256・name が material と pool の間で重なれば問題を出す", () => {
    const dupKifuId = whatifInputProblems([entry({ kifuId: "same" })], [group("p3", [entry({ name: "b", path: "b", kifuId: "same", sha256: "sha-b" })])], ["p3"]);
    expect(dupKifuId.some((p) => p.includes("同じ kifuId の whatif 記録"))).toBe(true);
  });

  it("values が記録の間でそろわなければ問題を出す", () => {
    const problems = whatifInputProblems(
      [entry({ values: { ...VALUES, startPly: 17 } })],
      [group("p3", [entry({ name: "b", path: "b", kifuId: "k2", sha256: "sha-b", values: { ...VALUES, startPly: 20 } })])],
      ["p3"],
    );
    expect(problems.some((p) => p.includes("values が記録の間でそろわない"))).toBe(true);
  });

  it("そろっていれば問題無し", () => {
    const problems = whatifInputProblems([entry()], [group("p3", [entry({ name: "b", path: "b", kifuId: "k2", sha256: "sha-b" })])], ["p3"]);
    expect(problems).toEqual([]);
  });
});

describe("whatifRateRowsOf(計画 §8.1-2)", () => {
  it("6 行を、id の順で、正しい分子・分母で組む", () => {
    const material: WhatifFileEntry[] = [entry({ summary: summary({ positionsRead: 10, matchesTop1: 4, withinMultiPv: 8, forkCount: 2, narrowHeldCount: 1, chanceHeldCount: 1, scenesRead: 3, attackNoLegalMoveCount: 1 }) })];
    const pool: WhatifInputGroup[] = [
      group("p3", [entry({ name: "b", kifuId: "k2", sha256: "sha-b", summary: summary({ positionsRead: 20, matchesTop1: 6, withinMultiPv: 16, forkCount: 5, narrowHeldCount: 3, chanceHeldCount: 2, scenesRead: 7, attackNoLegalMoveCount: 2 }) })]),
      group("p4", [entry({ name: "c", kifuId: "k3", sha256: "sha-c", summary: summary({ positionsRead: 30, matchesTop1: 15, withinMultiPv: 25, forkCount: 4, narrowHeldCount: 5, chanceHeldCount: 4, scenesRead: 9, attackNoLegalMoveCount: 3 }) })]),
    ];

    const rows = whatifRateRowsOf(material, pool);
    expect(rows.map((r) => r.id)).toEqual(["whatif_matchesTop1", "whatif_withinMultiPv", "whatif_fork", "whatif_narrowHeld", "whatif_chanceHeld", "whatif_attackNoLegalMove"]);

    const top1 = rows.find((r) => r.id === "whatif_matchesTop1")!;
    expect(top1.subject).toEqual({ collapsed: 4, denominator: 10, ratePercent: 40 });
    // pool 合計: (6+15) / (20+30) = 21/50 = 42%
    expect(top1.poolTotal).toEqual({ collapsed: 21, denominator: 50, ratePercent: 42 });
    // 人ごと: p3 = 6/20 = 30%、p4 = 15/30 = 50%
    expect(top1.poolRange).toEqual({ minPercent: 30, maxPercent: 50 });

    const attackNoLegal = rows.find((r) => r.id === "whatif_attackNoLegalMove")!;
    // 分母は scenesRead(positionsRead ではない)
    expect(attackNoLegal.subject).toEqual({ collapsed: 1, denominator: 3, ratePercent: (100 * 1) / 3 });
    expect(attackNoLegal.poolTotal).toEqual({ collapsed: 5, denominator: 16, ratePercent: (100 * 5) / 16 });
  });

  it("分母 0 の人は poolRange の比べから除く(分母の取り違えを見張る変異の的)", () => {
    const material: WhatifFileEntry[] = [entry()];
    const pool: WhatifInputGroup[] = [
      group("p3", [entry({ name: "b", kifuId: "k2", sha256: "sha-b", summary: summary({ positionsRead: 0, matchesTop1: 0 }) })]),
      group("p4", [entry({ name: "c", kifuId: "k3", sha256: "sha-c", summary: summary({ positionsRead: 10, matchesTop1: 3 }) })]),
    ];
    const rows = whatifRateRowsOf(material, pool);
    const top1 = rows.find((r) => r.id === "whatif_matchesTop1")!;
    // p3 は分母 0 なので比べから除く。残るのは p4 の 30% だけ
    expect(top1.poolRange).toEqual({ minPercent: 30, maxPercent: 30 });
  });

  it("分母が 0(pool が空)なら ratePercent は null", () => {
    const material: WhatifFileEntry[] = [entry({ summary: summary({ positionsRead: 0, matchesTop1: 0, withinMultiPv: 0, scenesRead: 0, attackNoLegalMoveCount: 0 }) })];
    const pool: WhatifInputGroup[] = [group("p3", [entry({ name: "b", kifuId: "k2", sha256: "sha-b", summary: summary({ positionsRead: 0, matchesTop1: 0, scenesRead: 0 }) })])];
    const rows = whatifRateRowsOf(material, pool);
    const top1 = rows.find((r) => r.id === "whatif_matchesTop1")!;
    expect(top1.subject).toEqual({ collapsed: 0, denominator: 0, ratePercent: null });
    expect(top1.poolTotal).toEqual({ collapsed: 0, denominator: 0, ratePercent: null });
    expect(top1.poolRange).toEqual({ minPercent: null, maxPercent: null });
  });
});

describe("renderWhatifRateMarkdown", () => {
  it("名前・手・局面・kifuId を含まない Markdown を返す(6 行 + 見出し)", () => {
    const material: WhatifFileEntry[] = [entry()];
    const pool: WhatifInputGroup[] = [group("p3", [entry({ name: "b", kifuId: "k2", sha256: "sha-b" })])];
    const rows = whatifRateRowsOf(material, pool);
    const md = renderWhatifRateMarkdown(rows).join("\n");
    expect(md).toContain("candidate/lower の判定は付けない");
    expect(md).toContain("第 1 候補と同じ");
    for (const forbidden of ["sfen", "SFEN", "2g2f", "kifuId", "k1", "k2"]) expect(md).not.toContain(forbidden);
    // 6 行(見出し行を除く)
    const rowLines = renderWhatifRateMarkdown(rows).filter((line) => line.startsWith("| ") && !line.includes("その人"));
    expect(rowLines.length).toBe(6);
  });
});
