// STEP D0-SIDE 段 2(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の F-S1〜F-S6・F-S10・F-S11・Q-3)。
// **期待値は試験を回す前に手で書いた**(規則 11.1)。F-S10 の局面は監査 A と 1e がそれぞれ手で導いた値(計画 11.5)。
//
// F-S6 の検算(盤全体の回転)は、**マスの変換(rotateSquare)を使わず**、行と駒の単位の反転で書く(変換器と写し方を共有しないため。計画 4. の (c))。
// 比べ方は SFEN の文字列ではなく、shogiops の正規化を通した盤・手番・持ち駒の 3 欄(計画 4. の (b))。

import { pathToFileURL } from "node:url";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";
import { makeSfen } from "shogiops/sfen";
import { describe, expect, it } from "vitest";

import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { GOTE_TO_MOVE_INITIAL_SFEN } from "./sideAlignment.js";
import { rotateSquare, rotateUsiMove, UsiRotationError } from "./usiRotation.js";

const LIB_DIR = dirname(fileURLToPath(import.meta.url));
const KIFU_10MOVES: string[] = JSON.parse(readFileSync(join(LIB_DIR, "..", "kifu", "2026-09-10-claude-10moves.json"), "utf8")).moves;

const ALL_SQUARES = [1, 2, 3, 4, 5, 6, 7, 8, 9].flatMap((file) => [..."abcdefghi"].map((rank) => `${file}${rank}`));

/** 盤全体を 180 度回す検算。段の順を逆にし、各段を駒の単位で左右反転し、大文字・小文字を入れ替え、持ち駒の先後を入れ替え、手番を入れ替える。 */
function rotateSfenByBoard(sfen: string): string {
  const [board, turn, hands] = sfen.split(" ");
  const swapCase = (text: string) => text.replace(/[A-Za-z]/g, (c) => (c === c.toUpperCase() ? c.toLowerCase() : c.toUpperCase()));
  const ranks = board!.split("/").map((rank) => {
    const cells: (string | null)[] = [];
    for (const token of rank.match(/\+?[A-Za-z]|\d/g) ?? []) {
      if (/^\d$/.test(token)) for (let i = 0; i < Number(token); i++) cells.push(null);
      else cells.push(token);
    }
    if (cells.length !== 9) throw new Error(`段の長さが 9 でない: ${rank}`);
    return cells;
  });
  const rotatedBoard = [...ranks]
    .reverse()
    .map((cells) => {
      let text = "";
      let empty = 0;
      for (const cell of [...cells].reverse()) {
        if (cell === null) {
          empty += 1;
          continue;
        }
        if (empty > 0) text += String(empty);
        empty = 0;
        text += swapCase(cell);
      }
      return empty > 0 ? text + String(empty) : text;
    })
    .join("/");
  return `${rotatedBoard} ${turn === "b" ? "w" : "b"} ${hands === "-" ? "-" : swapCase(hands!)} 1`;
}

/** 盤・手番・持ち駒の 3 欄(shogiops の正規化を通す。手数の欄は比べない) */
const positionFields = (sfen: string) => makeSfen(parsePosition(sfen)).split(" ").slice(0, 3);

const playAll = (start: string, moves: readonly string[]) => moves.reduce((sfen, move) => applyMove(sfen, move), start);

describe("rotateUsiMove(F-S1〜F-S4)", () => {
  it("F-S1: 7g7f → 3c3d(7→3、g→c、f→d)", () => {
    expect(rotateUsiMove("7g7f")).toBe("3c3d");
  });

  it("F-S2: 8h2b+ → 2b8h+(成りの + はそのまま)", () => {
    expect(rotateUsiMove("8h2b+")).toBe("2b8h+");
  });

  it("F-S3: P*5e → P*5e(中央は動かない)", () => {
    expect(rotateUsiMove("P*5e")).toBe("P*5e");
  });

  it("F-S4: P*2d → P*8f(打つマスを回す。駒の文字はそのまま)", () => {
    expect(rotateUsiMove("P*2d")).toBe("P*8f");
  });

  it("マス: 7g → 3c、2d → 8f、5e → 5e、1a → 9i、9i → 1a", () => {
    expect(["7g", "2d", "5e", "1a", "9i"].map(rotateSquare)).toStrictEqual(["3c", "8f", "5e", "9i", "1a"]);
  });

  it("読めない手・マスは推測せずに例外を投げる", () => {
    for (const bad of ["", "7g7", "0a1b", "7j7f", "p*5e", "K*5e", "7g7f=", "resign"]) {
      expect(() => rotateUsiMove(bad), bad).toThrow(UsiRotationError);
    }
    expect(() => rotateSquare("10a")).toThrow(UsiRotationError);
  });
});

describe("回転は自分自身の逆(F-S5)", () => {
  it("81 マスすべてで、2 回回すと元に戻り、1 回では(5e を除き)元と違う", () => {
    expect(ALL_SQUARES).toHaveLength(81);
    for (const square of ALL_SQUARES) {
      expect(rotateSquare(rotateSquare(square)), square).toBe(square);
      if (square !== "5e") expect(rotateSquare(square), square).not.toBe(square);
    }
  });

  it("F-S1〜F-S4 の手は 2 回回すと元に戻る", () => {
    for (const move of ["7g7f", "8h2b+", "P*5e", "P*2d"]) expect(rotateUsiMove(rotateUsiMove(move)), move).toBe(move);
  });
});

describe("usi-coordinates.mjs の rotateSquare180 と突き合わせる(Q-3。.mjs の試験は vitest で走らない ― P-27)", () => {
  it("81 マスすべてで結果が同じ", async () => {
    const moduleUrl = pathToFileURL(join(LIB_DIR, "..", "..", "lib", "usi-coordinates.mjs")).href;
    const { rotateSquare180 } = (await import(moduleUrl)) as { rotateSquare180: (square: string) => string };
    for (const square of ALL_SQUARES) expect(rotateSquare(square), square).toBe(rotateSquare180(square));
  });
});

describe("固定棋譜 2026-09-10-claude-10moves を回す(F-S6・F-S10・F-S11)", () => {
  const rotated = KIFU_10MOVES.map(rotateUsiMove);
  const originalFinal = playAll(DEFAULT_INITIAL_SFEN, KIFU_10MOVES);

  it("前提: 平手・後手番の初期局面は、手番の欄だけが w の平手", () => {
    expect(GOTE_TO_MOVE_INITIAL_SFEN).toBe("lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1");
  });

  it("前提: 元の最後の局面は、計画 11.5 で手で確かめた値(成り駒と両方の持ち駒を含む)", () => {
    expect(KIFU_10MOVES).toHaveLength(20);
    expect(originalFinal).toBe("lnsgk1snl/1r7/pppppp1pp/6pg1/9/7P1/PP1PPPP1P/3RG1SK1/+b1S2G1NL b Bnlp 21");
  });

  it("F-S6 (a): 回した 20 手は、平手・後手番の初期局面から applyMove ですべて合法に並ぶ", () => {
    expect(() => playAll(GOTE_TO_MOVE_INITIAL_SFEN, rotated)).not.toThrow();
  });

  it("F-S6 (b): 手を回して並べた最後の局面と、元の最後の局面を盤ごと回した局面が、盤・手番・持ち駒の 3 欄とも一致する", () => {
    expect(positionFields(playAll(GOTE_TO_MOVE_INITIAL_SFEN, rotated))).toStrictEqual(positionFields(rotateSfenByBoard(originalFinal)));
  });

  it("F-S10: 回した最後の局面は、手で導いた値と文字列まで一致する(変換器も検算も通さない正解)", () => {
    expect(playAll(GOTE_TO_MOVE_INITIAL_SFEN, rotated)).toBe("ln1g2s1+B/1ks1gr3/p1pppp1pp/1p7/9/1GP6/PP1PPPPPP/7R1/LNS1KGSNL w NLPb 21");
  });

  it("F-S11: 元の最後の局面と回した最後の局面は一致しない(対称な局面で回転の誤りが見えなくならないことの前提)", () => {
    expect(positionFields(playAll(GOTE_TO_MOVE_INITIAL_SFEN, rotated))).not.toStrictEqual(positionFields(originalFinal));
  });

  it("検算そのものの確かめ: 盤ごと回す関数を 2 回当てると、元の局面の 3 欄に戻る", () => {
    expect(positionFields(rotateSfenByBoard(rotateSfenByBoard(originalFinal)))).toStrictEqual(positionFields(originalFinal));
  });
});
