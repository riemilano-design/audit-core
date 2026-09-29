// 束 C の試験(provenance と閾値の写し。計画 §4・P-1)。
//
// 【いちばん大事な 1 本】**閾値の写しが、写し元の実物と合っていること**(i 系ではなく j1)。
// packet に「+300 で優勢」と書いておきながら道具が別の値で数えていたら、
// 読む側は**気づけないまま**その数を使う。だから `from` に書いた場所を**実際に読んで**突き合わせる。
// 【追跡性そのもの】辿る道の試験は束 B の試験ファイル側(g2)に置いた ―
// あちらは合成材料から組んだ packet を持っているので、同じものを 2 つ作らない。
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { ObservationProvenanceError, materialThresholds, metaValue, provenanceOf, sourcesOf, toolThresholds } from "./observationProvenance.js";

const REPO_ROOT = new URL("../../../", import.meta.url);

const META = {
  read: [{ gitHead: "abc123", values: { nodeLadder: [2000, 1000000], minLossCp: 600 } }],
  whatif: [{ gitHead: "abc123", values: { nodes: 1000000, multiPv: 5, minLossCp: 600 } }],
};
const SOURCES = { material: "m1", engine: "e1", engineShallow: "e2", direct: "d1", recognition: "r1" };
const BY_SOURCE = { m1: ["a.json"], d1: ["b.json"], e1: ["c.jsonl"], e2: ["d.jsonl"], r1: ["e.json"] };

describe("閾値は確かめた写し(P-1)", () => {
  it("j1 `from` に書いた場所を実際に読み、その値が在ることを確かめる", () => {
    const thresholds = toolThresholds();
    expect(thresholds.length).toBeGreaterThan(3);
    for (const threshold of thresholds) {
      const parts = threshold.from.split(" ");
      expect(parts, `${threshold.id} の from が「パス 定数名」の形でない`).toHaveLength(2);
      const source = readFileSync(new URL(parts[0]!, REPO_ROOT), "utf-8");
      // 定数名の最後の部分(`TIME_VALUES.spentBucketsSec[0]` → `spentBucketsSec`)
      const name = parts[1]!.split(".").pop()!.replace(/\[\d+\]$/, "");
      const lines = source.split("\n").filter((line) => line.includes(name) && !line.trimStart().startsWith("//") && !line.trimStart().startsWith("*"));
      expect(lines.length, `${parts[0]} に ${name} の行が無い`).toBeGreaterThan(0);
      const withValue = lines.filter((line) => new RegExp(`(^|[^0-9])${threshold.value}([^0-9]|$)`).test(line));
      expect(withValue.length, `${parts[0]} の ${name} の行に ${threshold.value} が無い(写しがずれている)`).toBeGreaterThan(0);
    }
  });

  it("j2 優勢の閾値は python 側(exit_groups.py)の定数と同じ値", () => {
    // **写した先が python なので、型検査では結べない** ― ここで実物を読んで突き合わせる
    const source = readFileSync(new URL("scripts/playtest/report-pdf/exit_groups.py", REPO_ROOT), "utf-8");
    const found = /^AHEAD_CP = (\d+)$/m.exec(source);
    expect(found, "exit_groups.py に AHEAD_CP の行が無い").not.toBeNull();
    const ahead = toolThresholds().find((row) => row.id === "ahead_cp")!;
    expect(ahead.value).toBe(Number(found![1]));
    expect(ahead.unit).toBe("centipawns");
  });

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

  it("j7 provenance は出どころ・材料・閾値を 1 つに束ねる", () => {
    const provenance = provenanceOf({
      pipelineVersion: "0000000", generatedAt: "2026-09-30T00:00:00Z",
      inputs: [{ path: "a.json", sha256: "a".repeat(64), bytes: 1 }],
      inputsBySource: BY_SOURCE, meta: META, sources: SOURCES,
    });
    expect(Object.keys(provenance).sort()).toEqual(["generatedAt", "inputs", "pipelineVersion", "sources", "thresholds"]);
    expect((provenance.thresholds as unknown[]).length).toBe(toolThresholds().length + materialThresholds(META).length);
  });
});
