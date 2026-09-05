import { describe, expect, it } from "vitest";
import { parseInfoLine } from "./usiInfoParser.js";

describe("parseInfoLine", () => {
  it("1. multipv・score(cp)・pvを含むinfo行を正しくparseできる", () => {
    const result = parseInfoLine("info depth 10 seldepth 12 multipv 1 score cp 55 nodes 12345 pv 7g7f 3c3d");
    expect(result).toEqual({
      multipv: 1,
      score: { type: "cp", value: 55 },
      pv: ["7g7f", "3c3d"],
      raw: "info depth 10 seldepth 12 multipv 1 score cp 55 nodes 12345 pv 7g7f 3c3d",
    });
  });

  it("2. multipv番号を正しく保持する(1以外の値・省略時のデフォルト1)", () => {
    expect(parseInfoLine("info multipv 3 score cp 10 pv 2g2f")?.multipv).toBe(3);
    // multipv未指定はUSI/UCIの慣例上MultiPV=1相当として扱う。
    expect(parseInfoLine("info depth 5 score cp 10 pv 2g2f")?.multipv).toBe(1);
  });

  it("3. cp scoreを正しく保持する(正負とも)", () => {
    expect(parseInfoLine("info multipv 1 score cp 120 pv 7g7f")?.score).toEqual({ type: "cp", value: 120 });
    expect(parseInfoLine("info multipv 1 score cp -80 pv 7g7f")?.score).toEqual({ type: "cp", value: -80 });
  });

  it("4. mate scoreを正しく保持する(正負とも)", () => {
    expect(parseInfoLine("info multipv 1 score mate 3 pv 7g7f")?.score).toEqual({ type: "mate", value: 3 });
    expect(parseInfoLine("info multipv 1 score mate -2 pv 7g7f")?.score).toEqual({ type: "mate", value: -2 });
  });

  it("5. side-to-move perspectiveの値をそのまま保持し、符号を反転・正規化しない", () => {
    // USIプロトコルの慣例上「その局面の手番側から見た」値だが、本パーサーは
    // これを一切加工せず、エンジンが出力した符号のままvalueに格納する。
    const negative = parseInfoLine("info multipv 1 score cp -300 pv 7g7f");
    const positive = parseInfoLine("info multipv 1 score cp 300 pv 7g7f");
    expect(negative?.score?.value).toBe(-300);
    expect(positive?.score?.value).toBe(300);
  });

  it("7a. 'info'で始まらない行はinfo行として扱わずundefinedを返す", () => {
    expect(parseInfoLine("bestmove 7g7f ponder 3c3d")).toBeUndefined();
    expect(parseInfoLine("usiok")).toBeUndefined();
    expect(parseInfoLine("")).toBeUndefined();
  });

  it("7b. multipv/score/pvが解析できないinfo行でも例外を投げず既定値にフォールバックする", () => {
    expect(parseInfoLine("info depth 3 nodes 100")).toEqual({
      multipv: 1,
      score: undefined,
      pv: [],
      raw: "info depth 3 nodes 100",
    });
    expect(parseInfoLine("info multipv abc score cp xyz pv")).toEqual({
      multipv: 1,
      score: undefined,
      pv: [],
      raw: "info multipv abc score cp xyz pv",
    });
  });

  it("7c. pvの後に余分な空白があっても安全にtrimして配列化する", () => {
    expect(parseInfoLine("info multipv 1 score cp 0 pv   7g7f   3c3d  ")?.pv).toEqual(["7g7f", "3c3d"]);
  });

  it("10. 同一入力に対して常に同じ結果を返す(決定的)", () => {
    const line = "info depth 8 multipv 2 score cp 42 pv 2g2f 8c8d";
    expect(parseInfoLine(line)).toEqual(parseInfoLine(line));
  });
});
