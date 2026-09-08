import { describe, expect, it } from "vitest";
import { exposeName } from "./nameExposure.js";

describe("exposeName", () => {
  it("draftの場合、siteに応じた注記(pendingNote)を返す", () => {
    expect(exposeName("銀冠", "draft", "shape").pendingNote).toBe("内容を確認中の形");
    expect(exposeName("銀冠", "draft", "squares").pendingNote).toBe("内容を確認中");
    expect(exposeName("銀冠", "draft", "section").pendingNote).toBe(
      "この形の説明は内容を確認中のため、参考程度に見てください。",
    );
  });

  it("human_reviewedの場合、pendingNoteは常にnull", () => {
    expect(exposeName("本美濃囲い", "human_reviewed", "shape").pendingNote).toBeNull();
    expect(exposeName("本美濃囲い", "human_reviewed", "squares").pendingNote).toBeNull();
    expect(exposeName("本美濃囲い", "human_reviewed", "section").pendingNote).toBeNull();
  });

  it("expert_verifiedの場合、pendingNoteは常にnull(human_reviewedと区別しない)", () => {
    expect(exposeName("本美濃囲い", "expert_verified", "shape").pendingNote).toBeNull();
    expect(exposeName("本美濃囲い", "expert_verified", "squares").pendingNote).toBeNull();
    expect(exposeName("本美濃囲い", "expert_verified", "section").pendingNote).toBeNull();
  });

  it("nameはそのまま返す(内容を書き換えない)", () => {
    expect(exposeName("銀冠", "draft", "shape").name).toBe("銀冠");
    expect(exposeName("本美濃囲い", "human_reviewed", "shape").name).toBe("本美濃囲い");
  });
});
