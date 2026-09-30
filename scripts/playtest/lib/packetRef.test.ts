// 束 R2 ― packetRef の文法(1 か所)。計画 docs/STEP_LLM_SEATS_R2_CONTRACT_2026-09-30.md §3。
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { AGGREGATE_REF_RE, FACTS_REF_RE, aggregateRef, isPacketObsId, packetObsIdOf, packetRefPathProblems } from "./packetRef.js";

describe("packetRef.path の文法", () => {
  it("集計と事実の参照は通る", () => {
    for (const p of ["aggregates.sideMatch.attack.numerator", "aggregates.sideMatch.attack.denominator", "aggregates.groups.core.games.value", "aggregates.collapse_total.value", "facts.branches[12].topGapCp", "facts.games[0].result", "facts.recognition.rows[3].selfSignature", "facts.engine[1032].candidates[4].scoreCp"]) {
      expect(packetRefPathProblems(p), p).toEqual([]);
    }
  });
  it("集計の単独形・節の見出しの書き方・無い列・別の根は落ちる(実在は見ない = 文法だけ)", () => {
    for (const p of ["aggregates.sideMatch.attack", "aggregates.sideMatch.attack.num", "facts.games[]", "facts.time.bySpent[3].collapsed", "facts.time[3]", "time.bySpent[3]", "aggregates[0]", "aggregates.", "facts.branches", "facts.recognition[0].rows", "packet.aggregates.x", "", 12, undefined]) {
      expect(packetRefPathProblems(p).length, String(p)).toBe(1);
    }
  });
  it("aggregateRef と packetObsIdOf は文法どおりの字を返す", () => {
    expect(aggregateRef("sideMatch.attack", "numerator")).toBe("aggregates.sideMatch.attack.numerator");
    expect(AGGREGATE_REF_RE.test(aggregateRef("sideMatch.attack", "denominator"))).toBe(true);
    expect(AGGREGATE_REF_RE.test(aggregateRef("branches.total", "value"))).toBe(true);
    expect(AGGREGATE_REF_RE.test("aggregates.sideMatch.attack")).toBe(false); // 単独形は受けない(司令塔の決定 2026-09-30)
    expect(FACTS_REF_RE.test("facts.moves[3].usi")).toBe(true);
    expect(packetObsIdOf("facts.moves[3].usi")).toBe("packet.facts.moves[3].usi");
    expect(isPacketObsId("packet.facts.moves[3].usi")).toBe(true);
    expect(isPacketObsId("obs.time.bySpent")).toBe(false);
  });
  it("この module は packet を読まない(observationPacket を import しない)", () => {
    const src = readFileSync(new URL("./packetRef.ts", import.meta.url), "utf-8");
    expect(src).not.toMatch(/from "\.\/observationPacket/);
    expect(src).not.toMatch(/readFileSync/);
  });
});
