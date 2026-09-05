import { describe, expect, it } from "vitest";
import { explainBoardEvent, explainBoardEvents } from "./boardEventExplanation.js";
import type { BoardEvent, BoardEventKind } from "./boardEventDetector.js";

function makeEvent(kind: BoardEventKind, overrides: Partial<BoardEvent> = {}): BoardEvent {
  return { kind, piece: overrides.piece ?? null, square: overrides.square ?? null };
}

const ALL_KINDS: BoardEventKind[] = [
  "captured_by_you",
  "captured_by_opponent",
  "check_given",
  "check_received",
  "promoted_by_you",
  "promoted_by_opponent",
];

describe("explainBoardEvent", () => {
  it("1. 自分が取った/取られた事実を、マス・駒種つきで述べる", () => {
    expect(explainBoardEvent(makeEvent("captured_by_you", { piece: "歩", square: "5d" })).text).toBe(
      "この手で、相手の５四の歩を取りました。",
    );
    expect(explainBoardEvent(makeEvent("captured_by_opponent", { piece: "銀", square: "7h" })).text).toBe(
      "相手の手で、あなたの７八の銀が取られました。",
    );
  });

  it("2. 王手はどちらの手で起きたかを述べる", () => {
    expect(explainBoardEvent(makeEvent("check_given")).text).toBe("この手で、相手の玉に王手がかかりました。");
    expect(explainBoardEvent(makeEvent("check_received")).text).toBe(
      "相手の手で、あなたの玉に王手がかかっています。",
    );
  });

  it("3. 成りは実際に成った事実だけを述べる", () => {
    expect(explainBoardEvent(makeEvent("promoted_by_you", { piece: "歩", square: "5c" })).text).toBe(
      "この手で、歩が５三で成りました。",
    );
    expect(explainBoardEvent(makeEvent("promoted_by_opponent", { piece: "歩", square: "5g" })).text).toBe(
      "相手の手で、歩が５七で成りました。",
    );
  });

  it("4. 駒種が確定していない場合は、駒名を推測せず述べない", () => {
    const { text } = explainBoardEvent(makeEvent("captured_by_you", { piece: null, square: "5d" }));

    expect(text).toBe("この手で、相手の５四にあった駒を取りました。");
  });

  it("5. どの種類の説明も、評価・推奨・損得の表現を含まない", () => {
    const forbidden = [
      "良い手", "悪手", "損", "危険", "警戒", "取り返", "おすすめ", "最善", "形勢", "有利", "不利", "べき",
    ];

    for (const kind of ALL_KINDS) {
      const { text } = explainBoardEvent(makeEvent(kind, { piece: "歩", square: "5d" }));
      expect(text.length, kind).toBeGreaterThan(0);
      for (const word of forbidden) {
        expect(text, `${kind} / ${word}`).not.toContain(word);
      }
    }
  });

  it("6. 同じ入力に対しては常に同じ結果を返す(決定的)", () => {
    const event = makeEvent("captured_by_opponent", { piece: "歩", square: "1g" });

    expect(explainBoardEvent(event)).toEqual(explainBoardEvent(event));
  });
});

describe("explainBoardEvents", () => {
  it("7. 出来事が無ければ空配列を返す(何も無かったことをここでは言葉にしない)", () => {
    expect(explainBoardEvents([])).toEqual([]);
  });

  it("8. 出来事の順序をそのまま保つ", () => {
    const events = [
      makeEvent("captured_by_you", { piece: "銀", square: "5c" }),
      makeEvent("promoted_by_you", { piece: "歩", square: "5c" }),
    ];

    expect(explainBoardEvents(events).map((m) => m.kind)).toEqual(["captured_by_you", "promoted_by_you"]);
  });
});
