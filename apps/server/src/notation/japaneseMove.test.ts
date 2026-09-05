// japaneseMove.ts のテスト。棋譜表記の生成そのものはshogiopsの責務のため、
// ここで確認するのは「配線が正しいこと」と「変換できない場合に推測しないこと」。

import { makeSfen, parseSfen } from "shogiops/sfen";
import { describe, expect, it } from "vitest";
import { toJapaneseMove } from "./japaneseMove.js";
import { applyMove } from "../rules/applyMove.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

describe("toJapaneseMove", () => {
  it("移動の手を日本語の棋譜表記へ変換する", () => {
    expect(toJapaneseMove(INITIAL_SFEN, "7i7h")).toBe("７八銀");
    expect(toJapaneseMove(INITIAL_SFEN, "5i6h")).toBe("６八玉");
    expect(toJapaneseMove(INITIAL_SFEN, "7g7f")).toBe("７六歩");
  });

  it("同じマスへ行ける駒が複数ある場合の区別(右/左等)もshogiopsに委ねる", () => {
    expect(toJapaneseMove(INITIAL_SFEN, "4i5h")).toBe("５八金右");
    expect(toJapaneseMove(INITIAL_SFEN, "6i5h")).toBe("５八金左");
  });

  it("直前の手の移動先に関わらず「同」表記にはしない(単独で読める表記にする)", () => {
    // 先手7六歩 → 後手3四歩 → 先手2六歩 と進めた局面で、後手が3三の駒を3四へ動かす等の
    // 「同」が出得る状況ではなく、ここでは直前の手の移動先と同じマスへ指す手を確認する。
    const afterP7f = applyMove(INITIAL_SFEN, "7g7f");
    const afterP3d = applyMove(afterP7f, "3c3d");
    // 直前の手(3c3d)の移動先3dへ、先手の角が動く手。lastDestを渡していないため
    // 「同角」ではなくマス目を明示した表記になる。
    expect(toJapaneseMove(afterP3d, "8h3c+")).not.toContain("同");
  });

  it("USIとして解釈できない文字列はnullを返す(表記を推測しない)", () => {
    expect(toJapaneseMove(INITIAL_SFEN, "")).toBeNull();
    expect(toJapaneseMove(INITIAL_SFEN, "zzzz")).toBeNull();
  });

  it("合法性の判定は行わない(合法手だけを渡すのは呼び出し側の責務)", () => {
    // shogiopsのmakeJapaneseMoveOrDropは合法性を検証せず、USIとして解釈できれば
    // 表記を返す。本モジュールもそれに倣い、合法手判定を独自に持たない
    // (Unit 4がここへ渡すのは、routePlanner.tsが合法手から作った候補手のみ)。
    expect(toJapaneseMove(INITIAL_SFEN, "9i2b")).toBe("２二香不成");
  });
});
