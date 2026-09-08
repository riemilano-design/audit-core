import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { DEFAULT_OPENINGS_DIR, loadApprovedScenarioVariants, ScenarioRepositoryError } from "./scenarioRepository.js";

function writeOpeningFixture(dir: string, fileName: string, content: unknown): void {
  writeFileSync(path.join(dir, fileName), JSON.stringify(content), "utf-8");
}

describe("scenarioRepository", () => {
  it("実際のdata/openings/(scenarioがnull)に対しては0件を返す", () => {
    expect(loadApprovedScenarioVariants(DEFAULT_OPENINGS_DIR)).toEqual([]);
  });

  it("存在しないディレクトリに対してScenarioRepositoryErrorを投げる", () => {
    expect(() => loadApprovedScenarioVariants(`${DEFAULT_OPENINGS_DIR}-does-not-exist`)).toThrow(
      ScenarioRepositoryError,
    );
  });

  describe("verification_statusによる除外(実運用ゲート)", () => {
    let dir: string;

    afterEach(() => {
      if (dir) rmSync(dir, { recursive: true, force: true });
    });

    it("human_approved以外(unverified / ai_verified)のvariantは候補から除外される", () => {
      dir = mkdtempSync(path.join(tmpdir(), "scenario-repo-test-"));
      writeOpeningFixture(dir, "fixture.json", {
        id: "fixture_opening",
        scenario: {
          variants: [
            { id: "v_unverified", target_intent_id: "hayajikake", moves: ["6c6d"], verification_status: "unverified" },
            { id: "v_ai", target_intent_id: "hayajikake", moves: ["6c6d"], verification_status: "ai_verified" },
          ],
        },
      });

      expect(loadApprovedScenarioVariants(dir)).toEqual([]);
    });

    it("human_approvedのvariantだけが返る", () => {
      dir = mkdtempSync(path.join(tmpdir(), "scenario-repo-test-"));
      writeOpeningFixture(dir, "fixture.json", {
        id: "fixture_opening",
        scenario: {
          variants: [
            { id: "v_unverified", target_intent_id: "hayajikake", moves: ["6c6d"], verification_status: "unverified" },
            {
              id: "v_approved",
              target_intent_id: "hayajikake",
              moves: ["6c6d", "6d6e"],
              verification_status: "human_approved",
            },
          ],
        },
      });

      const result = loadApprovedScenarioVariants(dir);
      expect(result).toEqual([
        {
          openingId: "fixture_opening",
          variantId: "v_approved",
          targetIntentId: "hayajikake",
          moves: ["6c6d", "6d6e"],
        },
      ]);
    });

    it("scenarioがnull/undefinedのopeningは候補ゼロとして扱う", () => {
      dir = mkdtempSync(path.join(tmpdir(), "scenario-repo-test-"));
      writeOpeningFixture(dir, "a.json", { id: "opening_a", scenario: null });
      writeOpeningFixture(dir, "b.json", { id: "opening_b" });

      expect(loadApprovedScenarioVariants(dir)).toEqual([]);
    });
  });
});
