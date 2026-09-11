// pieceThreatExplanation.ts(Phase 7 Unit 4 STEP 4-3)のテスト。
// 人間承認済みの文言(C-1)・成駒の表記(H-1)への変換だけを確認する
// (並び順そのものはpieceThreatDetector.test.tsの責務。ここでは既に並び済みの
// factsを渡して、文言化だけを確認する)。

import { describe, expect, it } from "vitest";
import type { PieceThreatFact } from "./pieceThreatDetector.js";
import { explainPieceThreats } from "./pieceThreatExplanation.js";

describe("explainPieceThreats", () => {
  it("C-1: 1駒・1攻め駒の文言", () => {
    const facts: PieceThreatFact[] = [
      { square: "8h", role: "bishop", attackers: [{ square: "8g", role: "gold" }] },
    ];

    expect(explainPieceThreats(facts)).toEqual([
      {
        kind: "piece_attacked",
        text: "あなたの８八の角に、相手の８七の金が当たっています(次の相手の手で取られる可能性があります)。",
        square: "8h",
        attackerSquares: ["8g"],
      },
    ]);
  });

  it("複数の攻め駒は「と」で連結する(並び順は渡されたfactsの順のまま。例: 金の次に歩)", () => {
    const facts: PieceThreatFact[] = [
      {
        square: "5e",
        role: "gold",
        attackers: [
          { square: "5d", role: "gold" },
          { square: "5f", role: "pawn" },
        ],
      },
    ];

    expect(explainPieceThreats(facts)).toEqual([
      {
        kind: "piece_attacked",
        text: "あなたの５五の金に、相手の５四の金と５六の歩が当たっています(次の相手の手で取られる可能性があります)。",
        square: "5e",
        attackerSquares: ["5d", "5f"],
      },
    ]);
  });

  it("H-1: 成駒6種(龍・馬・と金・成銀・成桂・成香)の名前をそのまま表記する", () => {
    const facts: PieceThreatFact[] = [
      { square: "3e", role: "dragon", attackers: [{ square: "5c", role: "bishop" }] },
      { square: "4e", role: "horse", attackers: [{ square: "5c", role: "bishop" }] },
      { square: "5e", role: "silver", attackers: [{ square: "8h", role: "tokin" }] },
      { square: "6e", role: "gold", attackers: [{ square: "8h", role: "promotedsilver" }] },
      { square: "7e", role: "gold", attackers: [{ square: "8h", role: "promotedknight" }] },
      { square: "8e", role: "gold", attackers: [{ square: "8h", role: "promotedlance" }] },
    ];

    const messages = explainPieceThreats(facts);
    expect(messages.map((m) => m.text)).toEqual([
      "あなたの３五の龍に、相手の５三の角が当たっています(次の相手の手で取られる可能性があります)。",
      "あなたの４五の馬に、相手の５三の角が当たっています(次の相手の手で取られる可能性があります)。",
      "あなたの５五の銀に、相手の８八のと金が当たっています(次の相手の手で取られる可能性があります)。",
      "あなたの６五の金に、相手の８八の成銀が当たっています(次の相手の手で取られる可能性があります)。",
      "あなたの７五の金に、相手の８八の成桂が当たっています(次の相手の手で取られる可能性があります)。",
      "あなたの８五の金に、相手の８八の成香が当たっています(次の相手の手で取られる可能性があります)。",
    ]);
  });

  it("自分の駒の名前が解決できない役職(標準将棋に無い役職)は行を出さない", () => {
    const facts: PieceThreatFact[] = [
      { square: "5e", role: "lion", attackers: [{ square: "5f", role: "rook" }] },
    ];

    expect(explainPieceThreats(facts)).toEqual([]);
  });

  it("攻め駒の名前が解決できない場合、その攻め駒は連結から除かれる。全滅すれば行自体を出さない", () => {
    const oneUnresolvable: PieceThreatFact[] = [
      {
        square: "5e",
        role: "gold",
        attackers: [
          { square: "5f", role: "rook" },
          { square: "6f", role: "lion" },
        ],
      },
    ];
    expect(explainPieceThreats(oneUnresolvable)).toEqual([
      {
        kind: "piece_attacked",
        text: "あなたの５五の金に、相手の５六の飛が当たっています(次の相手の手で取られる可能性があります)。",
        square: "5e",
        // 名前が解決できない攻め駒(6f・lion)はtoNamedAttackersの結果に合わせて除かれる。
        attackerSquares: ["5f"],
      },
    ]);

    const allUnresolvable: PieceThreatFact[] = [
      { square: "5e", role: "gold", attackers: [{ square: "6f", role: "lion" }] },
    ];
    expect(explainPieceThreats(allUnresolvable)).toEqual([]);
  });
});
