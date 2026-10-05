// 束 C の試験(provenance と閾値の写し。計画 §4・P-1)。
//
// 【いちばん大事な 1 本は将棋側へ移した】**閾値の写しが、写し元の実物と合っていること**(j0〜j2)は、
// Audit Core T-4/I-3 で表を組む側(`lib/observationFacts.ts` の `toolThresholds()`)と一緒に
// `observationFacts.test.ts` へ移した。ここ(Core)は**渡された表をそのまま・材料の閾値の前に**載せることだけを見る(j7)。
// 【追跡性そのもの】辿る道の試験は束 B の試験ファイル側(g2)に置いた ―
// あちらは合成材料から組んだ packet を持っているので、同じものを 2 つ作らない。
import { describe, expect, it } from "vitest";
import { ObservationProvenanceError, materialThresholds, metaValue, provenanceOf, sourcesOf, type ThresholdRow } from "./observationProvenance.js";

const META = {
  read: [{ gitHead: "abc123", values: { nodeLadder: [2000, 1000000], minLossCp: 600 } }],
  whatif: [{ gitHead: "abc123", values: { nodes: 1000000, multiPv: 5, minLossCp: 600 } }],
};
const SOURCES = { material: "m1", engine: "e1", engineShallow: "e2", direct: "d1", recognition: "r1" };
const BY_SOURCE = { m1: ["a.json"], d1: ["b.json"], e1: ["c.jsonl"], e2: ["d.jsonl"], r1: ["e.json"] };
/** 将棋側が組んで渡す閾値の表の**合成**(Core の試験は将棋側の定数を読まない。写しの正しさは observationFacts.test.ts の j0〜j2) */
const TOOL: readonly ThresholdRow[] = [
  { id: "ahead_cp", value: 300, unit: "centipawns", from: "x.py AHEAD_CP" },
  { id: "long_think_sec", value: 10, unit: "seconds", from: "y.ts T.longThinkSec" },
];

describe("閾値は確かめた写し(P-1)", () => {
  it("j3 材料から読める閾値は写さず読む(読めなければ載せない)", () => {
    const rows = materialThresholds(META);
    expect(rows.map((row) => row.id)).toEqual(["branch_min_loss_cp", "shallow_first_nodes"]);
    expect(rows[0]!.value).toBe(600);
    expect(rows[1]!.value).toBe(2000);
    expect(materialThresholds({ read: [], whatif: [] })).toEqual([]);
  });
});

describe("出どころの一覧", () => {
  it("j4 符号ごとに、読んだ材料のパスとエンジンの設定が付く", () => {
    const rows = sourcesOf({ inputsBySource: BY_SOURCE, meta: META, sources: SOURCES, recognitionReviewStatus: "draft" });
    expect(rows.map((row) => row.id)).toEqual(["m1", "d1", "e1", "e2", "r1"]);
    const engine = rows.find((row) => row.id === "e1")!;
    expect(engine).toMatchObject({ type: "engine", gitHead: "abc123", nodesLimit: 1000000, multipv: 5, inputPaths: ["c.jsonl"] });
    const shallow = rows.find((row) => row.id === "e2")!;
    // 浅い読みの上限は**梯子の最後**(材料の値)
    expect(shallow.nodesLimit).toBe(1000000);
    expect(rows.find((row) => row.id === "r1")!.reviewStatus).toBe("draft");
  });

  it("j5 材料を 1 つも読んでいない出どころは例外(空の符号を作らない)", () => {
    expect(() => sourcesOf({ inputsBySource: { ...BY_SOURCE, r1: [] }, meta: META, sources: SOURCES })).toThrow(ObservationProvenanceError);
  });

  it("j6 設定が材料の中で 2 通りあれば例外(違う設定の材料を混ぜたまま名乗らない)", () => {
    const mixed = { ...META, whatif: [META.whatif[0]!, { gitHead: "abc123", values: { nodes: 500000, multiPv: 5, minLossCp: 600 } }] };
    expect(() => sourcesOf({ inputsBySource: BY_SOURCE, meta: mixed, sources: SOURCES })).toThrow(ObservationProvenanceError);
    expect(metaValue(META.whatif, ["values", "nodes"], "x")).toBe(1000000);
    // 欄が無い行は数えない(「無い」と「違う」を混ぜない)
    expect(metaValue([{ values: {} }, ...META.whatif], ["values", "nodes"], "x")).toBe(1000000);
  });

  it("j7 provenance は出どころ・材料・閾値を 1 つに束ねる(渡された道具の閾値が**そのまま・その順で**先、材料の閾値が後)", () => {
    const provenance = provenanceOf({
      pipelineVersion: "0000000", generatedAt: "2026-09-30T00:00:00Z",
      inputs: [{ path: "a.json", sha256: "a".repeat(64), bytes: 1 }],
      inputsBySource: BY_SOURCE, meta: META, sources: SOURCES, toolThresholds: TOOL,
    });
    expect(Object.keys(provenance).sort()).toEqual(["generatedAt", "inputs", "pipelineVersion", "sources", "thresholds"]);
    expect(provenance.thresholds).toEqual([...TOOL, ...materialThresholds(META)]);
  });
});
