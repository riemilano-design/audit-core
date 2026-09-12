// detectEscapeSquareThreats(STEP 5-E)のテスト。
// 「移動先が届くか」の計算そのものはapplyMove(rules)とisSquareAttacked(rules)の
// 責務であるため、ここで確認するのは「配線が正しいこと」(現在の手番の合法手すべてに
// ついて、指した後の移動先へ相手の駒が届くかどうかを正しく判定して返すこと)。

import { describe, expect, it } from "vitest";
import {
  InvalidSfenError,
  detectEscapeSquareThreats,
  summarizeEscapeSquareThreatsForSquare,
} from "./escapeSquareThreat.js";

describe("detectEscapeSquareThreats", () => {
  it("移動先に相手の駒が届く手・届かない手の両方を正しく判定する", () => {
    // 後手の飛車が1eにあり、5筋の金(5f)が動ける先のうち、5e・4e・6e(同じ e段)は
    // 飛車の横の利きが届く。4f・6f・5g(f段・g段)は届かない。
    const sfen = "k8/9/9/9/8r/4G4/9/9/K8 b - 1";

    const result = detectEscapeSquareThreats(sfen);
    const byMove = new Map(result.map((r) => [r.move, r]));

    expect(byMove.get("5f5e")).toEqual({ move: "5f5e", toSquare: "5e", attacked: true });
    expect(byMove.get("5f4e")).toEqual({ move: "5f4e", toSquare: "4e", attacked: true });
    expect(byMove.get("5f6e")).toEqual({ move: "5f6e", toSquare: "6e", attacked: true });

    expect(byMove.get("5f4f")).toEqual({ move: "5f4f", toSquare: "4f", attacked: false });
    expect(byMove.get("5f6f")).toEqual({ move: "5f6f", toSquare: "6f", attacked: false });
    expect(byMove.get("5f5g")).toEqual({ move: "5f5g", toSquare: "5g", attacked: false });
  });

  it("玉の移動先も判定する(listAttackedPiecesは玉を除外するが、これは除外しない)", () => {
    const sfen = "k8/9/9/9/8r/4G4/9/9/K8 b - 1";

    const result = detectEscapeSquareThreats(sfen);
    const kingMoves = result.filter((r) => r.move.startsWith("9i"));

    expect(kingMoves.length).toBeGreaterThan(0);
    expect(kingMoves.every((r) => r.attacked === false)).toBe(true);
  });

  it("打つ手(ドロップ)も対象に含める", () => {
    // 同じ局面に先手の持ち駒の歩を1枚加える。8eは飛車のいる段(e段)上なので届き、
    // 8gは届かない。
    const sfen = "k8/9/9/9/8r/4G4/9/9/K8 b P 1";

    const result = detectEscapeSquareThreats(sfen);
    const byMove = new Map(result.map((r) => [r.move, r]));

    expect(byMove.get("P*8e")).toEqual({ move: "P*8e", toSquare: "8e", attacked: true });
    expect(byMove.get("P*8g")).toEqual({ move: "P*8g", toSquare: "8g", attacked: false });
  });

  it("STEP_5-E計画 1.1 と同じ局面で、実際にshogiopsのsquareAttackersへ委ねた結果を返す", () => {
    // 計画書1.1の表は「どちらも届かない」としているが、shogiopsに実際に問い合わせると、
    // 7hの金が7gへ移動した後・8iの桂が7gへ移動した後は、8hに残る後手の馬(横行かつ斜め
    // 1マスに利きが届く駒)の斜めの利きが7gへ届くため、squareAttackersはtrueを返す
    // (直接squareAttackersを呼んで確認済み。8hの馬そのものを取る7h8hと、
    // 銀が8hへ移動する7i8hは、当てる側の馬がいなくなるためfalse)。
    // この関数は判定をshogiopsへ委ねるだけであり、この結果を独自に補正しない。
    const sfen = "lns1k1sn1/1r2g1g1l/1ppppp1pp/p5p2/7P1/2P6/PP1PPPP1P/1+bGK1S1R1/LNS2G1NL b b 13";

    const result = detectEscapeSquareThreats(sfen);
    const byMove = new Map(result.map((r) => [r.move, r]));

    expect(byMove.get("7h7g")?.attacked).toBe(true);
    expect(byMove.get("7h8h")?.attacked).toBe(false);
    expect(byMove.get("7i8h")?.attacked).toBe(false);
    expect(byMove.get("8i7g")?.attacked).toBe(true);
  });

  it("現在の手番に合法手が1つも無い局面(詰み)では空配列を返す", () => {
    const sfen = "8k/7G1/6S1R/9/9/9/9/9/8K w - 1";

    expect(detectEscapeSquareThreats(sfen)).toEqual([]);
  });

  it("成り・不成りの2手がある場合、移動先が同じなら判定結果も同じになる", () => {
    // 先手の銀が成れるマス(5c・4c・6c)へ動ける局面。成り・不成りのどちらでも
    // 移動先は同じマスであり、利きは盤の占有だけで決まるため、結果は一致するはず。
    const sfen = "8k/9/9/4S4/9/9/9/9/K8 b - 1";

    const result = detectEscapeSquareThreats(sfen);
    const promotable = result.filter((r) => r.move.endsWith("+"));

    for (const promoted of promotable) {
      const plain = result.find((r) => r.move === promoted.move.slice(0, -1));
      if (plain) {
        expect(plain.attacked).toBe(promoted.attacked);
      }
    }
    // この局面に成り・不成りの両方が合法な手が実際に含まれていることを確認する
    // (比較が意味のある形で行われたことの確認)。
    expect(promotable.length).toBeGreaterThan(0);
  });

  it("不正なSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => detectEscapeSquareThreats("not-a-valid-sfen")).toThrow(InvalidSfenError);
  });
});

describe("summarizeEscapeSquareThreatsForSquare", () => {
  it("その駒の合法手が1つも無い場合、hasNoLegalMovesはtrue", () => {
    const result = summarizeEscapeSquareThreatsForSquare([], "5e");

    expect(result).toEqual({ hasNoLegalMoves: true, allDestinationsAttacked: false });
  });

  it("合法手はあるが一部しか届かない場合、allDestinationsAttackedはfalse", () => {
    const threats = [
      { move: "5e5d", toSquare: "5d", attacked: true },
      { move: "5e5f", toSquare: "5f", attacked: false },
    ];

    const result = summarizeEscapeSquareThreatsForSquare(threats, "5e");

    expect(result).toEqual({ hasNoLegalMoves: false, allDestinationsAttacked: false });
  });

  it("合法手すべての移動先に相手の駒が届く場合、allDestinationsAttackedはtrue", () => {
    const threats = [
      { move: "5e5d", toSquare: "5d", attacked: true },
      { move: "5e4e", toSquare: "4e", attacked: true },
    ];

    const result = summarizeEscapeSquareThreatsForSquare(threats, "5e");

    expect(result).toEqual({ hasNoLegalMoves: false, allDestinationsAttacked: true });
  });

  it("他のマスの指し手は数えない(移動元でだけ絞り込む)", () => {
    const threats = [
      { move: "5e5d", toSquare: "5d", attacked: false },
      { move: "3c3d", toSquare: "3d", attacked: true },
    ];

    const result = summarizeEscapeSquareThreatsForSquare(threats, "5e");

    expect(result).toEqual({ hasNoLegalMoves: false, allDestinationsAttacked: false });
  });

  it("打つ手(ドロップ)は移動元マスを持たないため、どの駒の集計にも数えない", () => {
    const threats = [{ move: "P*5e", toSquare: "5e", attacked: true }];

    const result = summarizeEscapeSquareThreatsForSquare(threats, "5e");

    // "5e"を移動元として持つ通常の指し手は無いため、ドロップの有無に関わらず
    // hasNoLegalMoves: trueになる(打つ手は「5eにある駒の合法手」ではないため)。
    expect(result).toEqual({ hasNoLegalMoves: true, allDestinationsAttacked: false });
  });

  it("実戦に近い局面: detectEscapeSquareThreatsの結果と組み合わせて、合法手すべてが届く駒を判定する", () => {
    // 1i の金は 1h・2h・2i の3マスにしか動けず、file1・file2を後手の飛車2枚が
    // それぞれ制圧しているため、どの移動先にも利きが届く。9i の玉は無関係で安全。
    const sfen = "4k2rr/9/9/9/9/9/9/9/K7G b - 1";

    const threats = detectEscapeSquareThreats(sfen);

    expect(summarizeEscapeSquareThreatsForSquare(threats, "1i")).toEqual({
      hasNoLegalMoves: false,
      allDestinationsAttacked: true,
    });
    expect(summarizeEscapeSquareThreatsForSquare(threats, "9i")).toEqual({
      hasNoLegalMoves: false,
      allDestinationsAttacked: false,
    });
  });
});
