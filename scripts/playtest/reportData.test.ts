// STEP TIME 作業 1(docs/STEP_TIME_PLAN_2026-09-22.md §6.1)。reportData.ts(CLI)の --time-limit-sec の配線だけを見る。
// 組み立て(buildPatientReportData 等)そのものの試験は lib/reportData.test.ts。

import { describe, expect, it } from "vitest";
import { parseArgs, ReportDataCliError } from "./reportData.js";

const REQUIRED = [
  "--person", "p", "--name", "n", "--title", "t", "--today", "2026-01-01",
  "--records", "r.jsonl", "--kifu", "k.fixed.json", "--gate", "g.jsonl",
  "--out-patient", "op.json", "--out-audit", "oa.json",
];

describe("parseArgs ― --time-limit-sec(STEP TIME)", () => {
  it("渡さなければ undefined(byLeft は null のまま出す側の既定)", () => {
    expect(parseArgs(REQUIRED).timeLimitSec).toBeUndefined();
  });

  it("正の数を渡せばその数(秒)になる", () => {
    expect(parseArgs([...REQUIRED, "--time-limit-sec", "180"]).timeLimitSec).toBe(180);
  });

  it("0 以下・数でなければ止める(黙って undefined にしない)", () => {
    for (const bad of ["0", "-1", "abc", ""]) {
      expect(() => parseArgs([...REQUIRED, "--time-limit-sec", bad])).toThrow(ReportDataCliError);
    }
  });
});
