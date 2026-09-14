// STEP U6-T2 の試験。段 A の校正の既知の値が、書かれた出どころ(コミット済みの記録)から本当に出ることを見る。
// **エンジンは起動しない**(記録を読むだけ)。git が無ければ execFileSync が例外を投げて赤になる(skip は書かない)。

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { CALIBRATION_BASELINE, CALIBRATION_BOUND_RATE_TOLERANCE, CALIBRATION_KIFU_IDS } from "./calibrationBaseline.js";
import { calibrationGate, observeCalibrationBaseline, type CalibrationRecordRow } from "./multiPvSurvey.js";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const RECORDS_DIR = join(REPO_ROOT, CALIBRATION_BASELINE.source.recordsDir);

type Line = { kind: string; kifuId?: string; gitHead?: string | null; dirty?: boolean; phase?: string; ply?: number; sfen?: string; searchPvs?: CalibrationRecordRow["searchPvs"] };

function readRecord(kifuId: string): { meta: Line | undefined; rows: CalibrationRecordRow[] } {
  const lines = readFileSync(join(RECORDS_DIR, `${kifuId}.jsonl`), "utf-8")
    .split("\n")
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line) as Line);
  const meta = lines.find((line) => line.kind === "meta");
  const rows = lines
    .filter((line) => line.kind === "record" && line.phase === "ready")
    .map((line) => ({ kifuId, ply: line.ply!, sfen: line.sfen!, searchPvs: line.searchPvs }));
  return { meta, rows };
}

describe("段 A の校正の既知の値(U6-T2)", () => {
  it("書かれた記録から数え直すと、既知の値(25 / 56・標識付きの長さ 2・D-2 の値 3)と一致する", () => {
    // 並びは CLI の readRecordRows と同じくファイル名の順(代表の行の選び方を揃える)
    const rows = [...CALIBRATION_KIFU_IDS].sort().flatMap((kifuId) => readRecord(kifuId).rows);
    const observed = observeCalibrationBaseline(rows, 0.05);
    expect(observed.withoutFocusBaseline).toBe(0);
    expect({
      marked: observed.marked,
      total: observed.total,
      maxBoundedPvLength: observed.maxBoundedPvLength,
      minPlies: observed.minPlies.kind === "value" ? observed.minPlies.value : observed.minPlies.kind,
    }).toEqual({
      marked: CALIBRATION_BASELINE.marked,
      total: CALIBRATION_BASELINE.total,
      maxBoundedPvLength: CALIBRATION_BASELINE.maxBoundedPvLength,
      minPlies: CALIBRATION_BASELINE.minPlies,
    });
  });

  it("記録は書かれた gitHead で取られ(dirty false)、SHA256SUMS と一致し、書かれた recordsCommit に同じバイト列で入っている", () => {
    const sums = new Map(
      readFileSync(join(RECORDS_DIR, "SHA256SUMS"), "utf-8")
        .trim()
        .split("\n")
        .map((line) => {
          const [hash, name] = line.trim().split(/\s+/);
          return [name!, hash!] as const;
        }),
    );
    for (const kifuId of CALIBRATION_KIFU_IDS) {
      const { meta } = readRecord(kifuId);
      expect(meta, kifuId).toMatchObject({ kifuId, gitHead: CALIBRATION_BASELINE.source.gitHead, dirty: false });
      const bytes = readFileSync(join(RECORDS_DIR, `${kifuId}.jsonl`));
      expect(createHash("sha256").update(bytes).digest("hex"), kifuId).toBe(sums.get(`${kifuId}.jsonl`));
      const committed = execFileSync(
        "git",
        ["show", `${CALIBRATION_BASELINE.source.recordsCommit}:${CALIBRATION_BASELINE.source.recordsDir}/${kifuId}.jsonl`],
        { cwd: REPO_ROOT, maxBuffer: 64 * 1024 * 1024 },
      );
      expect(Buffer.compare(committed, bytes), kifuId).toBe(0);
    }
  });

  it("出どころは 4 つの欄がすべて埋まっていて、門を通ると 25 / 56 を中心に ± 15 ポイントの既知の値になる", () => {
    for (const value of Object.values(CALIBRATION_BASELINE.source)) expect(value.length).toBeGreaterThan(0);
    expect(CALIBRATION_BASELINE.source.evaluator).toContain("768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76");
    expect(calibrationGate(CALIBRATION_BASELINE, CALIBRATION_BOUND_RATE_TOLERANCE)).toEqual({
      kind: "ready",
      source: CALIBRATION_BASELINE.source,
      expectation: { boundRate: 25 / 56, boundRateTolerance: 0.15, maxBoundedPvLength: 2, minPlies: 3 },
    });
  });

  it("値と出どころは凍結してあり、後から書き換えられない(A の G-5)", () => {
    expect(Object.isFrozen(CALIBRATION_BASELINE)).toBe(true);
    expect(Object.isFrozen(CALIBRATION_BASELINE.source)).toBe(true);
    expect(Object.isFrozen(CALIBRATION_KIFU_IDS)).toBe(true);
  });
});
