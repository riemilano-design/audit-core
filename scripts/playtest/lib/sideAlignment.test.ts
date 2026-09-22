// STEP D0-SIDE 段 2(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の F-S8・F-S9a (iii)(iv-b)(iv-c)・R-3・R-4・Q-4・Q-7)。
// **期待値は試験を回す前に手で書いた**(規則 11.1)。F-S8 の startSfen は監査 A と 1e がそれぞれ手で導いた値(計画 11.5)。
// meta・固定棋譜の形(司令塔の決定): `mirrored` を常に持ち、`startSfen`・`plyOffset`・`originalUserSide` は true のときだけ持つ。null は使わない。
// **欄が無いことと undefined の欄を区別するため、toStrictEqual と Object.keys で比べる**。

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import type { FixedKifuEnding } from "./kifuImport.js";
import { planReplayMoves } from "./replayPlan.js";
import {
  alignedFixedKifu,
  alignMovesToSente,
  GOTE_TO_MOVE_INITIAL_SFEN,
  initialSfenOf,
  InvalidSideAlignmentError,
  readSideAlignment,
  sideMetaFields,
} from "./sideAlignment.js";

const LIB_DIR = dirname(fileURLToPath(import.meta.url));
const KIFU_10MOVES: string[] = JSON.parse(readFileSync(join(LIB_DIR, "..", "kifu", "2026-09-10-claude-10moves.json"), "utf8")).moves;

/** F-S8 の開始局面(平手・後手番の初期局面に、回した 1 手目 3c3d を当てた局面。手数の欄は 2) */
const FS8_START = "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2";

/** STEP D0-KIFU3: 20 手の棋譜の後の投了(ply は元の手順の指し手数 + 1) */
const ENDING: FixedKifuEnding = { kind: "resign", ply: 21 };

describe("alignMovesToSente(案 1: 回して 1 手目を開始局面に畳む)", () => {
  it("本人が先手なら何も変えず、mirrored: false だけ", () => {
    const aligned = alignMovesToSente(KIFU_10MOVES, "sente");
    expect(aligned).toStrictEqual({ alignment: { mirrored: false }, moves: KIFU_10MOVES });
    expect(aligned.moves).not.toBe(KIFU_10MOVES);
  });

  it("F-S8: 本人が後手なら、startSfen は手で導いた値と文字列まで一致し、moves は回した 2 手目以降の 19 手、plyOffset: 1", () => {
    const aligned = alignMovesToSente(KIFU_10MOVES, "gote");
    expect(aligned.alignment).toStrictEqual({ mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START });
    expect(aligned.moves).toHaveLength(19);
    // 回した 2 手目は元の 2 手目 4a3b を回したもの、最後は元の 20 手目 7g9i を回したもの(手で回した)
    expect(aligned.moves[0]).toBe("6i7h");
    expect(aligned.moves[18]).toBe("3c1a");
  });

  it("F-S8: startSfen は先手番で、畳んだ手順は startSfen から合法に並ぶ(本人の手が 1 手目に来る)", () => {
    const aligned = alignMovesToSente(KIFU_10MOVES, "gote");
    if (!aligned.alignment.mirrored) throw new Error("回っていない");
    expect(aligned.alignment.startSfen.split(" ")[1]).toBe("b");
    expect(() => aligned.moves.reduce((sfen, move) => applyMove(sfen, move), aligned.alignment.mirrored ? aligned.alignment.startSfen : "")).not.toThrow();
  });

  it("入力の配列を書き換えない", () => {
    const moves = ["7g7f", "3c3d"];
    alignMovesToSente(moves, "gote");
    expect(moves).toStrictEqual(["7g7f", "3c3d"]);
  });

  it("手順が 0 手の後手の局はそろえられない(畳む 1 手目が無い。kifuImport は 0 手の棋譜を no_move_lines にする)", () => {
    expect(() => alignMovesToSente([], "gote")).toThrow(InvalidSideAlignmentError);
  });
});

describe("畳む → 落とす の順(R-8 と重ねる。F-S9a (iii)・Q-9 (b)(c))", () => {
  it("F-S9a (iii): 元 20 手(偶数)の後手の局は、畳んで 19 手 → 落として 18 手。plyOffset: 1 と、落とした手(回した座標)が両方残る", () => {
    const aligned = alignMovesToSente(KIFU_10MOVES, "gote");
    const plan = planReplayMoves(aligned.moves);
    expect(aligned.alignment).toMatchObject({ mirrored: true, plyOffset: 1 });
    expect(plan).toMatchObject({ kind: "replay", trailingMoveTruncated: true, truncatedTrailingMove: "3c1a" });
    if (plan.kind === "replay") expect(plan.moves).toHaveLength(18);
  });

  it("F-S9a (iv-b): 本人が後手・元 2 手 → 畳んで 1 手 → 落として 0 手で、no_moves_to_replay(落とした手は残す)", () => {
    const aligned = alignMovesToSente(["7g7f", "3c3d"], "gote");
    expect(aligned).toStrictEqual({ alignment: { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START }, moves: ["7g7f"] });
    expect(planReplayMoves(aligned.moves)).toStrictEqual({
      kind: "noMovesToReplay",
      reason: "no_moves_to_replay",
      trailingMoveTruncated: true,
      truncatedTrailingMove: "7g7f",
    });
  });

  it("F-S9a (iv-c): 本人が後手・元 1 手 → 畳んで 0 手(奇数でないので落とさない)で、no_moves_to_replay", () => {
    const aligned = alignMovesToSente(["7g7f"], "gote");
    expect(aligned).toStrictEqual({ alignment: { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START }, moves: [] });
    expect(planReplayMoves(aligned.moves)).toStrictEqual({ kind: "noMovesToReplay", reason: "no_moves_to_replay", trailingMoveTruncated: false });
  });
});

describe("readSideAlignment(R-4。固定棋譜 JSON の欄の形を確かめる)", () => {
  it("欄が無い・mirrored: false は先手の局", () => {
    expect(readSideAlignment({ id: "k", moves: [] })).toStrictEqual({ alignment: { mirrored: false }, sideAlignmentChecked: false });
    expect(readSideAlignment({ id: "k", moves: [], mirrored: false })).toStrictEqual({ alignment: { mirrored: false }, sideAlignmentChecked: false });
  });

  // 元 2 手(7g7f・3c3d)の後手の局を回して畳んだ固定棋譜(F-S9a (iv-b) と同じ。手で導いた値)
  const MIRRORED_2 = { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START, moves: ["7g7f"], originalMoves: ["7g7f", "3c3d"] };
  const MIRRORED_2_ALIGNMENT = { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START };

  it("mirrored: true で originalMoves があれば、回して畳み直した値と照合し、一致すれば sideAlignmentChecked: true", () => {
    expect(readSideAlignment(MIRRORED_2)).toStrictEqual({ alignment: MIRRORED_2_ALIGNMENT, sideAlignmentChecked: true });
  });

  it("mirrored: true で originalMoves が無ければ照合せず、sideAlignmentChecked: false(照合せずに通したことが記録に残る)", () => {
    const { originalMoves: _omitted, ...withoutOriginal } = MIRRORED_2;
    expect(readSideAlignment(withoutOriginal)).toStrictEqual({ alignment: MIRRORED_2_ALIGNMENT, sideAlignmentChecked: false });
  });

  it("moves を 1 手変えた固定棋譜は、照合で止まる(理由に moves の欄を出す)", () => {
    expect(() => readSideAlignment({ ...MIRRORED_2, moves: ["7g7e"] })).toThrow(InvalidSideAlignmentError);
    expect(() => readSideAlignment({ ...MIRRORED_2, moves: ["7g7e"] })).toThrow(/moves.*一致しません/);
  });

  it("startSfen を変えた固定棋譜は、照合で止まる(理由に startSfen の欄を出す)", () => {
    expect(() => readSideAlignment({ ...MIRRORED_2, startSfen: GOTE_TO_MOVE_INITIAL_SFEN })).toThrow(InvalidSideAlignmentError);
    expect(() => readSideAlignment({ ...MIRRORED_2, startSfen: GOTE_TO_MOVE_INITIAL_SFEN })).toThrow(/startSfen.*一致しません/);
  });

  it("originalMoves が手の配列でない・空・読めない手や非合法な 1 手目を含むなら止まる", () => {
    for (const originalMoves of ["7g7f", [], [1], ["zz", "3c3d"], ["3c3d", "7g7f"]]) {
      expect(() => readSideAlignment({ ...MIRRORED_2, originalMoves }), JSON.stringify(originalMoves)).toThrow(InvalidSideAlignmentError);
    }
  });

  it("形が食い違えば例外を投げる(黙って平手として読まない)", () => {
    const bad: Record<string, unknown>[] = [
      { mirrored: "true", originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START },
      { mirrored: true },
      { mirrored: true, originalUserSide: "sente", plyOffset: 1, startSfen: FS8_START },
      { mirrored: true, originalUserSide: "gote", plyOffset: 0, startSfen: FS8_START },
      { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: "" },
      { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: null },
      { startSfen: FS8_START },
      { mirrored: false, plyOffset: 1 },
      { mirrored: false, originalUserSide: "gote" },
      { mirrored: null },
      { mirrored: false, originalMoves: ["7g7f"] },
    ];
    for (const kifu of bad) expect(() => readSideAlignment(kifu), JSON.stringify(kifu)).toThrow(InvalidSideAlignmentError);
  });
});

describe("sideMetaFields(R-3。meta に書く欄)", () => {
  it("回さなかったときは mirrored: false の欄だけを持つ(startSfen などの欄も null も作らない)", () => {
    const fields = sideMetaFields(alignMovesToSente(KIFU_10MOVES, "sente").alignment);
    expect(fields).toStrictEqual({ mirrored: false });
    expect(Object.keys(fields)).toStrictEqual(["mirrored"]);
    expect(JSON.stringify(fields)).toBe('{"mirrored":false}');
  });

  it("回したときは mirrored: true・originalUserSide・plyOffset・startSfen の 4 欄だけを持つ", () => {
    const fields = sideMetaFields(alignMovesToSente(KIFU_10MOVES, "gote").alignment);
    expect(Object.keys(fields)).toStrictEqual(["mirrored", "originalUserSide", "plyOffset", "startSfen"]);
    expect(JSON.stringify(fields)).toBe(`{"mirrored":true,"originalUserSide":"gote","plyOffset":1,"startSfen":"${FS8_START}"}`);
  });
});

describe("initialSfenOf(R-5〜R-7 に渡す開始局面。3 つに分けて読む)", () => {
  it("meta が無い・mirrored の欄が無い(D0-SIDE 段 2 より前)・mirrored: false は平手", () => {
    expect(initialSfenOf(undefined)).toBe(DEFAULT_INITIAL_SFEN);
    expect(initialSfenOf({})).toBe(DEFAULT_INITIAL_SFEN);
    expect(initialSfenOf({ mirrored: false })).toBe(DEFAULT_INITIAL_SFEN);
  });

  it("mirrored: true は meta の startSfen", () => {
    expect(initialSfenOf({ mirrored: true, startSfen: FS8_START })).toBe(FS8_START);
  });

  it("mirrored: true なのに startSfen が無い・空なら例外(平手として読まない)", () => {
    expect(() => initialSfenOf({ mirrored: true })).toThrow(InvalidSideAlignmentError);
    expect(() => initialSfenOf({ mirrored: true, startSfen: "" })).toThrow(InvalidSideAlignmentError);
  });

  it("前提: F-S8 の開始局面は平手と違う(同じだと、渡し忘れを見分けられない)", () => {
    expect(FS8_START).not.toBe(DEFAULT_INITIAL_SFEN);
    expect(GOTE_TO_MOVE_INITIAL_SFEN).not.toBe(DEFAULT_INITIAL_SFEN);
  });
});

describe("alignedFixedKifu(kifu-import-check.ts の --fixed。Q-4)", () => {
  const fixed = { id: "k", source: "試験の固定棋譜", ending: ENDING, moves: KIFU_10MOVES };

  it("本人が先手: id・source・mirrored: false・ending・moves の 5 欄(手順はそのまま。D0-KIFU3 の欄の位置 (ii))", () => {
    const written = alignedFixedKifu(fixed, "sente");
    expect(Object.keys(written)).toStrictEqual(["id", "source", "mirrored", "ending", "moves"]);
    expect(written).toStrictEqual({ id: "k", source: "試験の固定棋譜", mirrored: false, ending: { kind: "resign", ply: 21 }, moves: KIFU_10MOVES });
  });

  it("本人が後手: そろえの 4 欄・畳んだ moves と、回す前の手順 originalMoves を残す。replay.ts の readSideAlignment がそのまま読める", () => {
    const written = alignedFixedKifu(fixed, "gote");
    expect(Object.keys(written)).toStrictEqual(["id", "source", "mirrored", "originalUserSide", "plyOffset", "startSfen", "ending", "moves", "originalMoves"]);
    expect(written.startSfen).toBe(FS8_START);
    expect(written.originalMoves).toStrictEqual(KIFU_10MOVES);
    expect((written.moves as string[]).length).toBe(19);
    expect(readSideAlignment(JSON.parse(JSON.stringify(written)) as Record<string, unknown>)).toStrictEqual({
      alignment: { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FS8_START },
      sideAlignmentChecked: true,
    });
  });

  it("T-8(S-C): 入力に ending のキーが無ければ出力にも無い(キーが無い = 終局の行を見ていない)。null なら null のまま写す", () => {
    const withoutEnding = { id: fixed.id, source: fixed.source, moves: fixed.moves };
    const written = alignedFixedKifu(withoutEnding, "sente");
    expect(written).toStrictEqual({ id: "k", source: "試験の固定棋譜", mirrored: false, moves: KIFU_10MOVES });
    expect(Object.hasOwn(written, "ending")).toBe(false);
    expect(Object.hasOwn(alignedFixedKifu(withoutEnding, "gote"), "ending")).toBe(false);
    expect(alignedFixedKifu({ ...withoutEnding, ending: null }, "sente")).toStrictEqual({ id: "k", source: "試験の固定棋譜", mirrored: false, ending: null, moves: KIFU_10MOVES });
  });

  it("T-9: 本人が後手でも ending は元の手順で数えたまま: ply = originalMoves の手数 + 1、ply − plyOffset = moves の手数 + 1", () => {
    const written = alignedFixedKifu(fixed, "gote");
    expect(written.ending).toStrictEqual({ kind: "resign", ply: 21 });
    const ply = (written.ending as { ply: number }).ply;
    expect(ply).toBe((written.originalMoves as string[]).length + 1);
    expect(ply - (written.plyOffset as number)).toBe((written.moves as string[]).length + 1);
  });

  it("T-11(P-3): ending を持つ固定棋譜も readSideAlignment・planReplayMoves は止めず、ending の無いときと同じ結果", () => {
    const withoutEnding = { id: fixed.id, source: fixed.source, moves: fixed.moves };
    for (const side of ["sente", "gote"] as const) {
      const withIt = JSON.parse(JSON.stringify(alignedFixedKifu(fixed, side))) as Record<string, unknown>;
      const without = JSON.parse(JSON.stringify(alignedFixedKifu(withoutEnding, side))) as Record<string, unknown>;
      expect(Object.hasOwn(withIt, "ending")).toBe(true);
      expect(readSideAlignment(withIt)).toStrictEqual(readSideAlignment(without));
      expect(planReplayMoves(withIt.moves as string[])).toStrictEqual(planReplayMoves(without.moves as string[]));
    }
    // 側を決めない形 (i)(mirrored の欄が無い)も
    expect(readSideAlignment({ id: "k", source: "試験の固定棋譜", ending: ENDING, moves: KIFU_10MOVES })).toStrictEqual({
      alignment: { mirrored: false },
      sideAlignmentChecked: false,
    });
  });

  // STEP TIME(docs/STEP_TIME_PLAN_2026-09-22.md §6.1 の 1): moveSeconds は通すだけ(回さず・詰めず)。
  const MOVE_SECONDS_10 = KIFU_10MOVES.map((_, i) => ({ spentSec: i + 1, totalSec: (i + 1) * 10 }));

  it("STEP TIME: 本人が先手なら moveSeconds はそのまま(ending の後ろ・moves の前)", () => {
    const written = alignedFixedKifu({ ...fixed, moveSeconds: MOVE_SECONDS_10 }, "sente");
    expect(Object.keys(written)).toStrictEqual(["id", "source", "mirrored", "ending", "moveSeconds", "moves"]);
    expect(written.moveSeconds).toStrictEqual(MOVE_SECONDS_10);
  });

  it("STEP TIME: 本人が後手でも moveSeconds は回さない・詰めない(10 件のまま。originalMoves と同じ並び・同じ長さ)", () => {
    const written = alignedFixedKifu({ ...fixed, moveSeconds: MOVE_SECONDS_10 }, "gote");
    expect(written.moveSeconds).toStrictEqual(MOVE_SECONDS_10); // moves は 19 件に畳まれるが moveSeconds は 10 件のまま
    expect((written.moveSeconds as unknown[]).length).toBe((written.originalMoves as string[]).length);
    expect((written.moves as string[]).length).not.toBe((written.moveSeconds as unknown[]).length);
  });

  it("STEP TIME: 入力に moveSeconds のキーが無ければ出力にも無い(先手・後手のどちらでも)", () => {
    expect(Object.hasOwn(alignedFixedKifu(fixed, "sente"), "moveSeconds")).toBe(false);
    expect(Object.hasOwn(alignedFixedKifu(fixed, "gote"), "moveSeconds")).toBe(false);
  });
});
