import { describe, expect, it } from "vitest";
import { getPlanChangeReasonMessage, type PlanChangeReason } from "./gameApi.js";

describe("getPlanChangeReasonMessage", () => {
  it("planChanged=falseの場合、reasonがnullでも理由文言を表示しない", () => {
    expect(getPlanChangeReasonMessage({ planChanged: false, planChangeReason: null })).toBeNull();
  });

  it("planChanged=falseの場合、reasonに値があっても理由文言を表示しない(planChangedとの組み合わせを優先)", () => {
    // 通常この組み合わせは起こらない(サーバー側の契約上)が、万一reasonだけを見て
    // 判定しないことを確認するための防御的テスト。
    expect(
      getPlanChangeReasonMessage({ planChanged: false, planChangeReason: "candidate_piece_captured" }),
    ).toBeNull();
  });

  it("planChanged=true, candidate_piece_capturedの場合、捕獲理由が表示される", () => {
    const message = getPlanChangeReasonMessage({ planChanged: true, planChangeReason: "candidate_piece_captured" });
    expect(message).toBe("予定していた駒が、相手の手によって取られました。");
  });

  it("planChanged=true, candidate_move_illegal_due_to_checkの場合、玉の移動不能理由が表示される", () => {
    const message = getPlanChangeReasonMessage({
      planChanged: true,
      planChangeReason: "candidate_move_illegal_due_to_check",
    });
    expect(message).toBe("相手の手によって、予定していた玉の移動ができなくなりました。");
  });

  it("planChanged=true, candidate_piece_pinnedの場合、駒が動かせなくなった理由が表示される", () => {
    const message = getPlanChangeReasonMessage({ planChanged: true, planChangeReason: "candidate_piece_pinned" });
    expect(message).toBe("相手の手によって、予定していた駒が動かせなくなりました。");
  });

  it("planChanged=true, unknownの場合、理由固有の文言は表示しない(nullを返す)", () => {
    expect(getPlanChangeReasonMessage({ planChanged: true, planChangeReason: "unknown" })).toBeNull();
  });

  it("planChanged=true, nullの場合も理由固有の文言は表示しない", () => {
    expect(getPlanChangeReasonMessage({ planChanged: true, planChangeReason: null })).toBeNull();
  });

  it("planChanged=true, サーバー側が将来追加しうる未知のreason値の場合も、断定せず表示しない(安全側)", () => {
    // TypeScriptの型では表現できない、実行時にのみ起こりうる未知の文字列を
    // 意図的にキャストして、安全側のフォールバック(default節)を検証する。
    const unknownReason = "some_future_reason_not_yet_known" as PlanChangeReason;
    expect(getPlanChangeReasonMessage({ planChanged: true, planChangeReason: unknownReason })).toBeNull();
  });
});
