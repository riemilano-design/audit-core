import { describe, expect, it } from "vitest";
import {
  getPlanChangeReasonMessage,
  shouldRetryPlanRefresh,
  shouldShowNextConsiderations,
  shouldShowPlanChangedNotice,
  PLAN_REFRESH_MAX_ATTEMPTS,
  type LastMoveOutcomeBody,
  type NextConsiderationMessage,
  type PlanChangeReason,
} from "./gameApi.js";

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

// Phase6 Unit3 ⑦: Phase3の「前回の計画が使えなくなりました。」と、Unit2の
// route_lostメッセージが同じ事象を二重に述べるのを防ぐ表示判断。
describe("shouldShowPlanChangedNotice", () => {
  function outcome(kinds: string[]): LastMoveOutcomeBody {
    return {
      playedMoveLabel: "７八銀",
      opponentMoveLabel: "１四歩",
      messages: kinds.map((kind) => ({ kind, text: "" })),
    };
  }

  it("planChanged=falseなら表示しない", () => {
    expect(shouldShowPlanChangedNotice({ planChanged: false, lastMoveOutcome: null })).toBe(false);
  });

  it("planChanged=trueで、route_lostの説明が無ければ表示する(従来どおり)", () => {
    expect(shouldShowPlanChangedNotice({ planChanged: true, lastMoveOutcome: null })).toBe(true);
    expect(
      shouldShowPlanChangedNotice({ planChanged: true, lastMoveOutcome: outcome(["played_non_candidate"]) }),
    ).toBe(true);
  });

  it("planChanged=trueでも、route_lostの説明があれば重複するため表示しない", () => {
    expect(
      shouldShowPlanChangedNotice({
        planChanged: true,
        lastMoveOutcome: outcome(["played_non_candidate", "route_lost"]),
      }),
    ).toBe(false);
  });
});

// Phase6 Unit4: 「今の局面で分かっていること」の表示可否。
// web側が持ってよいのは「サーバーが返した件数が0かどうか」の判定だけで、
// 文言生成・文言の加工・並び替え・フィルタ・将棋の判断は一切持たない。
describe("shouldShowNextConsiderations", () => {
  function messages(kinds: string[]): NextConsiderationMessage[] {
    return kinds.map((kind) => ({ kind, text: `${kind}のテキスト` }));
  }

  it("空配列なら表示しない(ブロックごと描画しない)", () => {
    expect(shouldShowNextConsiderations({ nextConsiderations: [] })).toBe(false);
  });

  it("1件でもあれば表示する", () => {
    expect(shouldShowNextConsiderations({ nextConsiderations: messages(["in_check"]) })).toBe(true);
  });

  it("メッセージの種類によって表示可否を変えない(サーバーの判断をweb側で覆さない)", () => {
    const kinds = [
      "in_check",
      "route_first_move_playable",
      "no_playable_route_first_move",
      "shape_completed",
      "ordering_note",
    ];
    for (const kind of kinds) {
      expect(shouldShowNextConsiderations({ nextConsiderations: messages([kind]) })).toBe(true);
    }
  });

  it("サーバーが返した並び・内容を変更しない(判定に使うのは件数だけ)", () => {
    const nextConsiderations = messages(["route_first_move_playable", "ordering_note"]);
    const before = nextConsiderations.map((m) => `${m.kind}:${m.text}`);

    shouldShowNextConsiderations({ nextConsiderations });

    expect(nextConsiderations.map((m) => `${m.kind}:${m.text}`)).toEqual(before);
  });
});

// ⑧(MultiPV参考評価)の再取得を続けてよいかの判定。
// Phase6の通し確認で、1回だけの再取得ではエンジンの解析(実測で約8秒)に間に合わず、
// サーバーが"ready"なのに画面が「計算中」のまま止まることが判明したため、上限付きの
// リトライへ変更した。web側が持つのは「状態」と「試行回数」による判定だけで、
// 将棋の判断は一切持たない。
describe("shouldRetryPlanRefresh", () => {
  it('"pending"の間はリトライする', () => {
    expect(shouldRetryPlanRefresh({ candidateMoveState: "pending" }, 1)).toBe(true);
  });

  it('"ready"になったらリトライしない', () => {
    expect(shouldRetryPlanRefresh({ candidateMoveState: "ready" }, 1)).toBe(false);
  });

  it('"unavailable"(そもそも候補手が無い)ならリトライしない', () => {
    expect(shouldRetryPlanRefresh({ candidateMoveState: "unavailable" }, 1)).toBe(false);
  });

  it("上限回数に達したら、まだpendingでもリトライしない(無限に回さない)", () => {
    expect(
      shouldRetryPlanRefresh({ candidateMoveState: "pending" }, PLAN_REFRESH_MAX_ATTEMPTS - 1),
    ).toBe(true);
    expect(shouldRetryPlanRefresh({ candidateMoveState: "pending" }, PLAN_REFRESH_MAX_ATTEMPTS)).toBe(
      false,
    );
    expect(
      shouldRetryPlanRefresh({ candidateMoveState: "pending" }, PLAN_REFRESH_MAX_ATTEMPTS + 1),
    ).toBe(false);
  });

  it("上限は有限で、実測の解析時間(18〜19秒)を1.5秒間隔でカバーできる", () => {
    expect(Number.isInteger(PLAN_REFRESH_MAX_ATTEMPTS)).toBe(true);
    expect(PLAN_REFRESH_MAX_ATTEMPTS).toBeGreaterThanOrEqual(14);
    expect(PLAN_REFRESH_MAX_ATTEMPTS).toBeLessThanOrEqual(40);
  });
});
