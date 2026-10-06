// STEP S-1(audit-core/docs/CORE_CONNECTION_S1_PLAN_2026-10-06.md §2)。`hypothesisCheck.ts`(CLI)の
// 任意引数 `--packet <path>` を実際に回す(npx tsx)。**合成材料のみ。実物の c5・実物の packet では回さない。**
//
// 【見るのはこれだけ】`--packet` が無ければ今までどおり H-9 が `skip`(未照合)、`--packet` が在れば
// 値が一致すれば `H-9 ok`・値がずれていれば `H-9 NG` になること。H-9 の判定そのもの(lib/hypothesis.ts)は見ない。

import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, describe, expect, it } from "vitest";

const REPO_ROOT = fileURLToPath(new URL("../../", import.meta.url));
const CLI_TS = fileURLToPath(new URL("./hypothesisCheck.ts", import.meta.url));
const WORK = mkdtempSync(join(tmpdir(), "hypothesis-check-cli-"));
afterAll(() => rmSync(WORK, { recursive: true, force: true }));

/** 数え直し(recountRowProblems)が通る、observationPacketRef.test.ts の packet() と同じ形の packet。 */
function packet(): Record<string, unknown> {
  return {
    contract: "observation-packet",
    schemaVersion: "0.1",
    packetId: "0".repeat(16),
    customerRef: "c5",
    facts: {
      games: [{ gameId: "g01", no: 1, side: "先手", result: "負け", ownPlyCount: 1, totalPlyCount: 2, timeLimitSec: 180, aheadAtAnyPoint: true, src: "m1" }],
      moves: [{ gameId: "g01", ply: 1, side: "own", usi: "7g7f", collapsed: true, spentSec: 1, src: "m1" }],
      engine: [{ gameId: "g01", ply: 1, sfen: "(合成)", src: "e1" }],
      time: [{ gameId: "g01", longThinkCount: 5, src: "m1" }],
      branches: [
        { gameId: "g01", ply: 1, displayPly: 1, top1Side: "attack", actualSide: "attack", topGapCp: 120, src: "e2" },
        { gameId: "g01", ply: 1, displayPly: 3, top1Side: "attack", actualSide: "defense", topGapCp: 80, src: "e2" },
      ],
      collapse: [{ gameId: "g01", ply: 1, src: "m1" }],
      recognition: { rows: [{ gameId: "g01", signatureClass: "多数の核", names: ["鬼殺し"] , src: "r1" }], definitions: [{ id: "onikoroshi", name: "鬼殺し", src: "r1" }] },
    },
    aggregates: [
      {
        id: "sideMatch.attack", name: "第 1 候補の側が攻めだった分かれ道のうち、実戦も攻めの側だった局面",
        unit: "positions", population: { from: "branches", where: [{ field: "top1Side", op: "==", value: "attack" }], unit: "positions" },
        numeratorWhere: [{ field: "actualSide", op: "in", value: ["attack", "both"] }],
        numerator: 1, denominator: 2, derivedFrom: ["g01"], src: "e1", recountable: true, timeDependent: false,
      },
    ],
    provenance: {
      pipelineVersion: "0", generatedAt: "2026-09-30T00:00:00Z",
      sources: [{ id: "m1", type: "material", inputPaths: ["x.json"] }],
      inputs: [{ path: "x.json", sha256: "a".repeat(64), bytes: 1 }],
      thresholds: [{ id: "ahead_cp", value: 300, unit: "centipawns", from: "x" }],
    },
  };
}

/** H-9 が見る `observations` だけを持つ行(スキーマの他の欄は見ないので最小限)。 */
function line(value: number): Record<string, unknown> {
  return {
    schemaVersion: "0.4",
    hypothesisId: "H-s1-test-001",
    subject: { customer: "c5", groups: ["3 分"], gamesCount: 25 },
    scope: "this_user",
    lane: "side",
    statement: "試験だけの文(数「2」を含む)",
    observations: [
      { obsId: "packet.aggregates.sideMatch.attack.numerator", value, packetRef: { path: "aggregates.sideMatch.attack.numerator" } },
    ],
    counterEvidence: { attempted: true, items: [], result: "none_found", provenance: { inputs: [] } },
    prediction: { writtenAt: "2026-09-30", window: "次の 25 局", metric: "sideMatch.attack", comparator: ">=", value: 1, alsoRequires: [] },
    status: "proposed",
    knowledge: { kind: "discovered", reviewStatus: "draft", origin: { kifu: "c5", lane: "side" }, range: "this_user" },
    provenance: { gitHead: null, inputs: [], excludedInputs: [] },
  };
}

function run(args: string[]) {
  const result = spawnSync("npx", ["tsx", CLI_TS, ...args], { cwd: REPO_ROOT, encoding: "utf-8" });
  return { status: result.status, stdout: result.stdout, stderr: result.stderr };
}

describe("hypothesisCheck.ts の --packet(任意引数)", () => {
  const lineGoodPath = join(WORK, "line_good.json");
  const lineWrongPath = join(WORK, "line_wrong.json");
  const packetPath = join(WORK, "packet.json");
  writeFileSync(lineGoodPath, JSON.stringify(line(1)), "utf-8");
  writeFileSync(lineWrongPath, JSON.stringify(line(65)), "utf-8");
  writeFileSync(packetPath, JSON.stringify(packet()), "utf-8");

  it("s1-1 --packet が無ければ H-9 は今までどおり skip のまま", () => {
    const r = run([lineGoodPath, "--today", "2026-09-30"]);
    expect(r.stdout).toContain("H-9 skip");
    expect(r.stdout).not.toContain("H-9 ok");
    expect(r.stdout).not.toContain("H-9 NG");
  });

  it("s1-2 --packet を渡すと H-9 が照合する(値が一致すれば ok、ずれれば NG)", () => {
    const good = run([lineGoodPath, "--today", "2026-09-30", "--packet", packetPath]);
    expect(good.stdout).toContain("H-9 ok");
    expect(good.stdout).not.toContain("H-9 skip");

    const wrong = run([lineWrongPath, "--today", "2026-09-30", "--packet", packetPath]);
    expect(wrong.stdout).toContain("H-9 NG");
    expect(wrong.stdout).toContain("value が packet と違う");
  });
});
