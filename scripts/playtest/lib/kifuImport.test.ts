// STEP D0-KIFU(仮番号): 外部の棋譜(KIF / CSA)を固定棋譜の JSON に変換する試作の試験。
//
// 【正解の置き方(規則 11.1: 校正は既知の正解と突き合わせる)】
// 自作の KIF・CSA は、固定棋譜 2026-09-10-claude-10moves(再生で確かめ済みの USI 手順)を**手で**書き直したもの。
// 変換器と shogiops が同じ誤りを持っていても、この JSON とは一致しない。
//
// 【この試験が確かめないこと】
// - 外部サービス(81Dojo・ぴよ将棋・将棋ウォーズ)が実際に書き出す棋譜を読めるか(計画書 7. で実物を使う)
// - 外部サービスが書き出すファイルのバイト列(Shift_JIS の読み分けは、リテラルのバイト列で確かめる。実物のファイルでは確かめない)
// - kifu-import-check.ts(確認スクリプト。試験は無い)

import { readFileSync } from "node:fs";
import { kifMoveRegex, parseKifMoveOrDrop } from "shogiops/notation/kif";
import { describe, expect, it } from "vitest";

import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import {
  decodeKifuBytes,
  ENDING_KIF_WORDS,
  importCsa,
  importKif,
  KIF_ENDINGS,
  STANDARD_START_SFEN,
  toFixedKifu,
  type KifuImportResult,
  type PieceNameAlignment,
} from "./kifuImport.js";

const FIXED = JSON.parse(readFileSync(new URL("../kifu/2026-09-10-claude-10moves.json", import.meta.url), "utf-8")) as {
  id: string;
  moves: string[];
};

const KIF_MOVES = [
  "７六歩(77)", "３二金(41)", "２六歩(27)", "３四歩(33)", "７七角(88)",
  "３三金(32)", "６八飛(28)", "２四金(33)", "４八玉(59)", "７七角成(22)",
  "同　桂(89)", "２七角打", "３八銀(39)", "５四角成(27)", "３九玉(48)",
  "７六馬(54)", "２八玉(39)", "７七馬(76)", "５八金(69)", "９九馬(77)",
];

function kifText(opts: { handicap?: string; extraHeader?: string[]; moves?: string[]; tail?: string[] } = {}): string {
  const moves = opts.moves ?? KIF_MOVES;
  return [
    "# ---- Kifu for Windows V7 棋譜ファイル ----",
    "開始日時：2026/09/10 10:00:00",
    `手合割：${opts.handicap ?? "平手"}　　`,
    "先手：先手の人",
    "後手：後手の人",
    ...(opts.extraHeader ?? []),
    "手数----指手---------消費時間--",
    ...moves.map((m, i) => `${String(i + 1).padStart(4)} ${m.padEnd(10, "　")}   ( 0:01/00:00:${String(i + 1).padStart(2, "0")})`),
    ...(opts.tail ?? [`${String(moves.length + 1).padStart(4)} 投了   ( 0:01/00:00:30)`, `まで${moves.length}手で後手の勝ち`]),
  ].join("\r\n");
}

const CSA_MOVES = [
  "+7776FU", "-4132KI", "+2726FU", "-3334FU", "+8877KA", "-3233KI", "+2868HI", "-3324KI", "+5948OU", "-2277UM",
  "+8977KE", "-0027KA", "+3938GI", "-2754UM", "+4839OU", "-5476UM", "+3928OU", "-7677UM", "+6958KI", "-7799UM",
];

function csaText(opts: { board?: string[]; moves?: string[]; commaTime?: boolean; ending?: string } = {}): string {
  const moves = opts.moves ?? CSA_MOVES;
  return [
    "V2.2",
    "N+先手の人",
    "N-後手の人",
    "$START_TIME:2026/09/10 10:00:00",
    ...(opts.board ?? ["PI", "+"]),
    ...moves.flatMap((m) => (opts.commaTime ? [`${m},T1`] : [m, "T1"])),
    opts.ending ?? "%TORYO",
  ].join("\n");
}

function imported(r: KifuImportResult): Extract<KifuImportResult, { kind: "imported" }> {
  if (r.kind !== "imported") throw new Error(`取り込めなかった: ${r.reason} ${r.detail}`);
  return r;
}

function finalSfenOf(moves: string[]): string {
  return moves.reduce((sfen, usi) => applyMove(sfen, usi), STANDARD_START_SFEN);
}

describe("importKif ― 既知の正解(固定棋譜)と突き合わせる", () => {
  it("手で書き直した KIF が、固定棋譜の USI 20 手と一致する", () => {
    const r = imported(importKif(kifText()));
    expect(FIXED.moves).toHaveLength(20); // 正解そのものが空でないこと
    expect(r.moves).toEqual(FIXED.moves);
    expect(r.finalSfen).toBe(finalSfenOf(FIXED.moves));
  });

  it("往復: shogiops だけで進めた終局局面と一致し、指し手表記の作り直しも全手一致する", () => {
    const r = imported(importKif(kifText()));
    expect(r.roundTrip.finalPositionMatches).toBe(true);
    expect(r.roundTrip.notationMismatches).toEqual([]);
  });

  it("行を 3 つに分ける: 採った 20 / 読んだが使わない(種類つき) / 読めなかった 0", () => {
    const r = imported(importKif(kifText()));
    const kinds = r.lines.unused.map((l) => l.kind);
    expect({
      採った: r.lines.moves.length,
      ヘッダ: kinds.filter((k) => k === "header").length,
      コメント: kinds.filter((k) => k === "comment").length,
      列見出し: kinds.filter((k) => k === "column_header").length,
      終局: kinds.filter((k) => k === "ending").length,
      まとめ: kinds.filter((k) => k === "summary").length,
      読めなかった: r.lines.unread.length,
    }).toEqual({ 採った: 20, ヘッダ: 4, コメント: 1, 列見出し: 1, 終局: 1, まとめ: 1, 読めなかった: 0 });
    expect(r.lines.moves.every((m) => m.timeDropped)).toBe(true); // 消費時間は読んで捨てたと記録する
    expect(r.ending?.text).toContain("投了");
  });

  it("知らない形の行は、取り込めても「読めなかった」に残る(黙って捨てない)", () => {
    const r = imported(importKif(kifText({ extraHeader: ["謎の行です"] })));
    expect(r.moves).toEqual(FIXED.moves);
    expect(r.lines.unread.map((l) => [l.text, l.why])).toEqual([["謎の行です", "知らない形の行"]]);
  });

  it("変化(分岐)の行は本譜に混ぜず、「読んだが使わない」に数える", () => {
    const r = imported(
      importKif(
        kifText({
          tail: ["  21 投了", "まで20手で後手の勝ち", "", "変化：12手", "  12 ５五角打", "  13 ３八銀(39)"],
        }),
      ),
    );
    expect(r.moves).toEqual(FIXED.moves);
    expect(r.lines.unused.filter((l) => l.kind === "variation")).toHaveLength(3);
  });

  it("終局の後にある指し手行は「読めなかった」に入れる", () => {
    const r = imported(importKif(kifText({ tail: ["  21 投了", "  22 ５八金(69)"] })));
    expect(r.moves).toHaveLength(20);
    expect(r.lines.unread.map((l) => l.why)).toEqual(["終局の行の後にある指し手行"]);
  });

  // 往復の「表記が食い違った」を記録する枝の試験。これが無いと、食い違いを記録しない変異が沈黙する。
  // 「同」を使わず移動先を明示する書き方(読める・手順は同じ)は、作り直すと「同　桂」になる。
  it("同じ手を別の書き方で書いた行は、手順は一致したまま「表記の食い違い」として記録される", () => {
    const moves = [...KIF_MOVES];
    moves[10] = "７七桂(89)";
    const r = imported(importKif(kifText({ moves })));
    expect(r.moves).toEqual(FIXED.moves);
    expect(r.roundTrip.notationMismatches).toEqual([{ ply: 11, original: "７七桂(89)", remade: "同　桂(89)" }]);
  });

  it("終局の行が無ければ ending は null(書かれていなかった)", () => {
    const r = imported(importKif(kifText({ tail: [] })));
    expect(r.ending).toBeNull();
  });
});

describe("importKif ― 取り込めないものは理由を分けて返す", () => {
  it("手合割が平手以外なら unsupported_start(手合割の行番号を返す)", () => {
    const r = importKif(kifText({ handicap: "香落ち", moves: ["３四歩(33)"] }));
    expect(r.kind).toBe("not_imported");
    if (r.kind === "not_imported") {
      expect(r.reason).toBe("unsupported_start");
      expect(r.lineNo).toBe(3);
    }
  });

  it("指し手の表記として読めない行があれば unparsable_move(行番号つき)", () => {
    const r = importKif(kifText({ moves: ["▲７六歩"] }));
    expect(r.kind === "not_imported" ? [r.reason, r.lineNo] : r.kind).toEqual(["unparsable_move", 7]);
  });

  it("非合法な手があれば illegal_move", () => {
    const r = importKif(kifText({ moves: ["７五歩(77)"] }));
    expect(r.kind === "not_imported" ? r.reason : r.kind).toBe("illegal_move");
  });

  it("手数が飛んでいれば unparsable_move", () => {
    const text = kifText().replace("   2 ３二金(41)", "   3 ３二金(41)");
    const r = importKif(text);
    expect(r.kind === "not_imported" ? r.reason : r.kind).toBe("unparsable_move");
  });

  it("指し手の行が 1 つも無ければ no_move_lines(0 手の対局とは言わない)", () => {
    const r = importKif(kifText({ moves: [], tail: [] }));
    expect(r.kind === "not_imported" ? r.reason : r.kind).toBe("no_move_lines");
  });
});

describe("importCsa ― 既知の正解と突き合わせる", () => {
  it("手で書き直した CSA が、固定棋譜の USI 20 手と一致し、往復も一致する", () => {
    const r = imported(importCsa(csaText()));
    expect(r.moves).toEqual(FIXED.moves);
    expect(r.finalSfen).toBe(finalSfenOf(FIXED.moves));
    expect(r.roundTrip.finalPositionMatches).toBe(true);
    expect(r.roundTrip.notationMismatches).toEqual([]);
    expect(r.ending?.text).toBe("%TORYO");
    expect(r.lines.unread).toEqual([]);
    expect(r.lines.moves.every((m) => m.pieceNameAligned === null)).toBe(true); // CSA は揃えの対象外(STEP D0-KIFU2 の T-6(d))
  });

  it("カンマ区切り(+7776FU,T1)でも同じ手順になり、消費時間は「読んだが使わない」に入る", () => {
    const r = imported(importCsa(csaText({ commaTime: true })));
    expect(r.moves).toEqual(FIXED.moves);
    expect(r.lines.unused.filter((l) => l.kind === "time")).toHaveLength(20);
  });

  it("駒落ち(PI11KY)なら unsupported_start", () => {
    const r = importCsa(csaText({ board: ["PI11KY", "-"], moves: ["-3334FU"] }));
    expect(r.kind === "not_imported" ? r.reason : r.kind).toBe("unsupported_start");
  });

  it("手番の符号が合わなければ unparsable_move", () => {
    const r = importCsa(csaText({ moves: ["-3334FU"] }));
    expect(r.kind === "not_imported" ? r.reason : r.kind).toBe("unparsable_move");
  });

  it("知らない形の行は「読めなかった」に残る", () => {
    const r = imported(importCsa(csaText().replace("V2.2", "V2.2\nZZZ")));
    expect(r.lines.unread.map((l) => l.text)).toEqual(["ZZZ"]);
  });
});

describe("形式をまたいで", () => {
  it("同じ対局の KIF と CSA は同じ USI 手順になる", () => {
    expect(imported(importKif(kifText())).moves).toEqual(imported(importCsa(csaText())).moves);
  });

  it("固定棋譜の JSON の形(replay.ts がそのまま読める形)にできる", () => {
    const fixed = toFixedKifu(imported(importKif(kifText())), "x", "自作の KIF");
    expect(Object.keys(fixed)).toEqual(["id", "source", "ending", "moves"]);
    expect(fixed.moves).toEqual(FIXED.moves);
  });
});

// 以下は監査(f2)の変異 M1・M2・M7・M9・M10・M11 で沈黙した枝の試験。どれも、変換器が存在する理由
// (標準でない書き方を黙って取り込まない / 平手以外を取り込まない / 文字コードを読み分ける)に当たる。

describe("importKif ― 中将棋の読み方へ落とさない", () => {
  it("移動元を全角で書いた「７六歩(７七)」は、shogiops 単体なら手として読むが、変換器は unparsable_move で止めて「読めなかった」に残す", () => {
    // 前提: parseKifMoveOrDrop は通常の指し手・打ちの正規表現に合わない行を中将棋の読み方で読む(kif.js:279)。
    // この前提が崩れたら、変換器の前処理が要るかを見直す。
    expect(parseKifMoveOrDrop("７六歩(７七)")).toBeDefined();
    const r = importKif(kifText({ moves: ["７六歩(７七)"] }));
    expect(r.kind).toBe("not_imported");
    if (r.kind === "not_imported") {
      expect([r.reason, r.lineNo, r.detail]).toEqual(["unparsable_move", 7, "７六歩(７七)"]);
      expect(r.lines.moves).toEqual([]);
      expect(r.lines.unread.map((l) => [l.lineNo, l.why])).toEqual([[7, "指し手の表記として読めない"]]);
    }
  });
});

describe("開始局面 ― 持駒だけ平手と違っても平手とは言わない", () => {
  const board = [
    "後手の持駒：なし",
    "  ９ ８ ７ ６ ５ ４ ３ ２ １",
    "+---------------------------+",
    "|v香v桂v銀v金v玉v金v銀v桂v香|一",
    "| ・v飛 ・ ・ ・ ・ ・v角 ・|二",
    "|v歩v歩v歩v歩v歩v歩v歩v歩v歩|三",
    "| ・ ・ ・ ・ ・ ・ ・ ・ ・|四",
    "| ・ ・ ・ ・ ・ ・ ・ ・ ・|五",
    "| ・ ・ ・ ・ ・ ・ ・ ・ ・|六",
    "| 歩 歩 歩 歩 歩 歩 歩 歩 歩|七",
    "| ・ 角 ・ ・ ・ ・ ・ 飛 ・|八",
    "| 香 桂 銀 金 玉 金 銀 桂 香|九",
    "+---------------------------+",
  ];
  const withBoard = (senteHand: string) =>
    [...board, `先手の持駒：${senteHand}`, "手数----指手---------消費時間--", "   1 ７六歩(77)", "   2 投了"].join("\r\n");

  it("KIF: 平手と同じ局面図は取り込めるが、先手の持駒に角を足すと unsupported_start", () => {
    const same = imported(importKif(withBoard("なし")));
    expect(same.moves).toEqual(["7g7f"]); // 対照(局面図の経路でも読める)
    const r = importKif(withBoard("角"));
    expect(r.kind === "not_imported" ? r.reason : r.kind).toBe("unsupported_start");
  });

  it("CSA: PI に P+00KA を足すと unsupported_start", () => {
    const r = importCsa(csaText({ board: ["PI", "P+00KA", "+"], moves: ["+7776FU"] }));
    expect(r.kind === "not_imported" ? r.reason : r.kind).toBe("unsupported_start");
  });
});

describe("importKif ― 半角の「:」", () => {
  it("半角「:」で書いたヘッダと変化の行も、ヘッダ・変化に分ける(読めなかった 0)", () => {
    const text = [
      "開始日時:2026/09/10 10:00:00",
      "手合割:平手",
      "先手:先手の人",
      "後手:後手の人",
      "手数----指手---------消費時間--",
      "   1 ７六歩(77)   ( 0:01/00:00:01)",
      "   2 投了",
      "",
      "変化:1手",
      "   1 ２六歩(27)",
    ].join("\n");
    const r = imported(importKif(text));
    expect(r.moves).toEqual(["7g7f"]);
    const kinds = r.lines.unused.map((l) => l.kind);
    expect({
      ヘッダ: kinds.filter((k) => k === "header").length,
      変化: kinds.filter((k) => k === "variation").length,
      読めなかった: r.lines.unread.length,
    }).toEqual({ ヘッダ: 4, 変化: 2, 読めなかった: 0 });
  });
});

describe("importCsa ― KIF 側の試験と対になるもの", () => {
  it("%TORYO の後にある指し手行は「読めなかった」に入れる", () => {
    const r = imported(importCsa(`${csaText({ moves: ["+7776FU"] })}\n-3334FU`));
    expect(r.moves).toEqual(["7g7f"]);
    expect(r.ending?.text).toBe("%TORYO");
    expect(r.lines.unread.map((l) => [l.text, l.why])).toEqual([["-3334FU", "終局の行の後にある指し手行"]]);
  });

  it("同じ手を別の駒名で書いた行(角が成る手を -2277RY)は、手順は一致したまま「表記の食い違い」として記録される", () => {
    const moves = [...CSA_MOVES];
    moves[9] = "-2277RY";
    const r = imported(importCsa(csaText({ moves })));
    expect(r.moves).toEqual(FIXED.moves);
    expect(r.roundTrip.notationMismatches).toEqual([{ ply: 10, original: "-2277RY", remade: "2277UM" }]);
  });
});

describe("decodeKifuBytes ― 文字コードを読み分け、どちらで読んだかを返す", () => {
  it("Shift_JIS のバイト列は shift_jis、UTF-8 は utf-8 として読み、UTF-8 の BOM は除く", () => {
    // 「手合割：平手」の Shift_JIS のバイト列(リテラル)
    const sjis = new Uint8Array([0x8e, 0xe8, 0x8d, 0x87, 0x8a, 0x84, 0x81, 0x46, 0x95, 0xbd, 0x8e, 0xe8]);
    const utf8 = new TextEncoder().encode("手合割：平手");
    const bom = new Uint8Array([0xef, 0xbb, 0xbf, ...utf8]);
    expect([decodeKifuBytes(sjis), decodeKifuBytes(utf8), decodeKifuBytes(bom)]).toEqual([
      { text: "手合割：平手", encoding: "shift_jis" },
      { text: "手合割：平手", encoding: "utf-8" },
      { text: "手合割：平手", encoding: "utf-8" },
    ]);
  });
});

// ---------------------------------------------------------------- STEP D0-KIFU2
// 1 文字の成り駒(竜・全・圭・杏)を、指し手の行の駒の欄だけ 龍・成銀・成桂・成香 に揃えて読む(docs/STEP_D0-KIFU2_PLAN_2026-09-15.md)。
//
// 【正解の置き方】棋譜は架空の最小のもの。期待する USI と揃えは、計画書 3. に試験を回す前に手で書いた表のまま(変換器の出力から写さない)。
// 【この試験が確かめないこと】実物の棋譜(1e が実棋譜 20 局で測る。計画書 5. の予-A5)。kifu-import-check.ts の「揃えた手」の列(試験なし)。

type Fixture = Array<[kif: string, usi: string, aligned: PieceNameAlignment | null]>;

const RYU: PieceNameAlignment = { written: "竜", readAs: "龍" };
const ZEN: PieceNameAlignment = { written: "全", readAs: "成銀" };
const KEI: PieceNameAlignment = { written: "圭", readAs: "成桂" };
const KYO: PieceNameAlignment = { written: "杏", readAs: "成香" };

// T-2 竜(と の対照を含む)
const T2: Fixture = [
  ["２六歩(27)", "2g2f", null], ["８四歩(83)", "8c8d", null], ["２五歩(26)", "2f2e", null], ["８五歩(84)", "8d8e", null],
  ["２四歩(25)", "2e2d", null], ["同　歩(23)", "2c2d", null], ["同　飛(28)", "2h2d", null], ["８六歩(85)", "8e8f", null],
  ["２三飛成(24)", "2d2c+", null], ["８七歩成(86)", "8f8g+", null], ["２二竜(23)", "2c2b", RYU], ["８八と(87)", "8g8h", null],
];
// T-3 杏
const T3: Fixture = [
  ["１六歩(17)", "1g1f", null], ["１四歩(13)", "1c1d", null], ["１五歩(16)", "1f1e", null], ["同　歩(14)", "1d1e", null],
  ["同　香(19)", "1i1e", null], ["８四歩(83)", "8c8d", null], ["１三香成(15)", "1e1c+", null], ["８五歩(84)", "8d8e", null],
  ["１二杏(13)", "1c1b", KYO],
];
// T-4 圭
const T4: Fixture = [
  ["３六歩(37)", "3g3f", null], ["８四歩(83)", "8c8d", null], ["３七桂(29)", "2i3g", null], ["８五歩(84)", "8d8e", null],
  ["４五桂(37)", "3g4e", null], ["８六歩(85)", "8e8f", null], ["３三桂成(45)", "4e3c+", null], ["８七歩成(86)", "8f8g+", null],
  ["３二圭(33)", "3c3b", KEI],
];
// T-5 全(「同　全」を含む)
const T5: Fixture = [
  ["２六歩(27)", "2g2f", null], ["８四歩(83)", "8c8d", null], ["２五歩(26)", "2f2e", null], ["８五歩(84)", "8d8e", null],
  ["３八銀(39)", "3i3h", null], ["９四歩(93)", "9c9d", null], ["２七銀(38)", "3h2g", null], ["９五歩(94)", "9d9e", null],
  ["２六銀(27)", "2g2f", null], ["１四歩(13)", "1c1d", null], ["２四歩(25)", "2e2d", null], ["同　歩(23)", "2c2d", null],
  ["２五銀(26)", "2f2e", null], ["７四歩(73)", "7c7d", null], ["２四銀(25)", "2e2d", null], ["７五歩(74)", "7d7e", null],
  ["２三銀成(24)", "2d2c+", null], ["３二銀(31)", "3a3b", null], ["同　全(23)", "2c3b", ZEN], ["７六歩(75)", "7e7f", null],
  ["２二全(32)", "3b2b", ZEN],
];

/** 1 文字の成り駒の手を長い書き方で書いた棋譜(揃えは要らない)。 */
function longForm(f: Fixture): Fixture {
  return f.map(([kif, usi, aligned]) => [aligned === null ? kif : kif.replace(aligned.written, aligned.readAs), usi, null]);
}

/** 取り込めて、手順・往復・揃えがすべて表のとおりであること。 */
function expectFixture(f: Fixture, opts: Parameters<typeof kifText>[0] = {}): Extract<KifuImportResult, { kind: "imported" }> {
  const r = imported(importKif(kifText({ ...opts, moves: f.map(([kif]) => kif) })));
  expect(r.moves).toEqual(f.map(([, usi]) => usi));
  expect(r.finalSfen).toBe(finalSfenOf(f.map(([, usi]) => usi)));
  expect(r.roundTrip.finalPositionMatches).toBe(true);
  expect(r.roundTrip.notationMismatches).toEqual([]);
  expect(r.lines.moves.map((m) => m.pieceNameAligned)).toEqual(f.map(([, , aligned]) => aligned));
  return r;
}

describe("importKif ― 1 文字の成り駒(竜・全・圭・杏)を揃えて読む(STEP D0-KIFU2)", () => {
  it("前提(T-1): shogiops の kifMoveRegex は 1 文字の成り駒を読まず、長い書き方と と・馬 は読む", () => {
    // この前提が崩れたら(shogiops が 1 文字の形を読むようになったら)、揃えが要るかを見直す。
    expect(["２二竜(23)", "同 全(23)", "３二圭(33)", "１二杏(13)"].map((t) => kifMoveRegex.test(t))).toEqual([false, false, false, false]);
    expect(["２二龍(23)", "同 成銀(23)", "３二成桂(33)", "１二成香(13)", "８八と(87)", "７六馬(54)"].map((t) => kifMoveRegex.test(t))).toEqual([
      true, true, true, true, true, true,
    ]);
  });

  it("T-2 竜: ２二竜(23) を 龍 に揃えて読み、手の行の text は元の行のまま(「竜」)", () => {
    const r = expectFixture(T2);
    const input = kifText({ moves: T2.map(([kif]) => kif) }).split("\r\n");
    expect(r.lines.moves[10]?.lineNo).toBe(17);
    expect(r.lines.moves[10]?.text).toBe(input[16]);
    expect(r.lines.moves[10]?.text).toContain("２二竜(23)");
  });

  it("T-3 杏: １二杏(13) を 成香 に揃えて読む", () => {
    expectFixture(T3);
  });

  it("T-4 圭: ３二圭(33) を 成桂 に揃えて読む", () => {
    expectFixture(T4);
  });

  it("T-5 全: 「同　全(23)」と「２二全(32)」を 成銀 に揃えて読み、作り直した表記(同　成銀・２二成銀)と食い違わない", () => {
    expectFixture(T5);
  });

  it("T-6 対照: 長い書き方(龍・成銀・成桂・成香)と既存の固定棋譜の KIF は、同じ手順のまま何も揃えない", () => {
    for (const f of [T2, T3, T4, T5]) expectFixture(longForm(f));
    const r = imported(importKif(kifText()));
    expect(r.moves).toEqual(FIXED.moves);
    expect(r.lines.moves.map((m) => m.pieceNameAligned)).toEqual(Array(20).fill(null));
  });

  it("T-7 ヘッダ・コメント・変化・まとめの行の 竜・全・圭・杏 は書き換えない(text は入力の行とバイト一致)", () => {
    const opts = {
      extraHeader: ["棋戦：竜王戦・全日本"],
      tail: ["*圭と杏と竜と全", "  22 投了", "まで21手で先手の勝ち", "", "変化：21手", "  21 ２二竜(23)", "  22 同　全(31)"],
    };
    const r = expectFixture(T5, opts);
    const input = kifText({ ...opts, moves: T5.map(([kif]) => kif) }).split("\r\n");
    expect(r.lines.unused.map((l) => l.text)).toEqual(r.lines.unused.map((l) => input[l.lineNo - 1]));
    expect(r.lines.unused.map((l) => [l.kind, l.text]).filter(([, t]) => /[竜全圭杏]/.test(t ?? ""))).toEqual([
      ["header", "棋戦：竜王戦・全日本"],
      ["comment", "*圭と杏と竜と全"],
      ["variation", "  21 ２二竜(23)"],
      ["variation", "  22 同　全(31)"],
    ]);
    expect(r.lines.unread).toEqual([]);
  });

  // 監査 f2 の変異 A-3(食い違いの original を揃える前の文字列に戻す)が沈黙した枝の試験(計画書 10.8・10.9)。
  it("T-9 揃えた手に本当の書き方の違いがあれば、食い違いの original は揃えた後の表記(「３二全(23)」→ 同　成銀 と比べた ３二成銀(23))", () => {
    const moves = T5.map(([kif]) => kif);
    moves[18] = "３二全(23)"; // 直前の手の移動先が 3 二なので、作り直すと「同」になる(手は同じ 2c3b)
    const r = imported(importKif(kifText({ moves })));
    expect(r.moves).toEqual(T5.map(([, usi]) => usi));
    expect(r.lines.moves.map((m) => m.pieceNameAligned)).toEqual(T5.map(([, , aligned]) => aligned));
    expect(r.roundTrip.finalPositionMatches).toBe(true);
    expect(r.roundTrip.notationMismatches).toEqual([{ ply: 19, original: "３二成銀(23)", remade: "同　成銀(23)" }]);
  });

  it("T-8 揃えた手が非合法なら illegal_move で止め、detail には元の表記(竜)を出す", () => {
    const r = importKif(kifText({ moves: ["２二竜(23)"] }));
    expect(r.kind).toBe("not_imported");
    if (r.kind === "not_imported") {
      expect([r.reason, r.lineNo, r.detail]).toEqual(["illegal_move", 7, "1 手目 ２二竜(23)(2c2b)"]);
      expect(r.lines.unread.map((l) => [l.lineNo, l.why])).toEqual([[7, "非合法な指し手"]]);
    }
  });
});

// ---------------------------------------------------------------- STEP D0-KIFU3
// 終局の行を、固定棋譜 JSON の `ending`({ kind, ply })に残す(docs/STEP_D0-KIFU3_PLAN_2026-09-15.md)。
//
// 【正解の置き方】期待は計画書 3. の表のまま、試験を回す前に手で書いた(変換器の出力から写さない)。棋譜と文は架空。
// CSA の語の表の期待は、コンピュータ将棋協会「CSA標準棋譜ファイル形式」第7版 V3.0(2024年5月14日)の語と意味から手で書いた。
// 【この試験が確かめないこと】実物の棋譜(1e が手元の 30 局で測る。計画書 5. の P-1)。alignedFixedKifu の欄の並び(sideAlignment.test.ts の T-8・T-9)。

/** 20 手の KIF の終局の行だけを替える(行頭の数は 21 が正しい。行は 27 行目) */
const withEnding = (line: string): string => kifText({ tail: [line] });

describe("importKif・importCsa ― 終局の種類と手数を ending に残す(STEP D0-KIFU3)", () => {
  it("T-1: 既定の KIF(20 手 + 21 投了)は { kind: resign, ply: 21 }。固定棋譜は id・source・ending・moves", () => {
    const r = imported(importKif(kifText()));
    expect(r.endingFact).toStrictEqual({ kind: "resign", ply: 21 });
    expect(toFixedKifu(r, "x", "自作の KIF")).toStrictEqual({ id: "x", source: "自作の KIF", ending: { kind: "resign", ply: 21 }, moves: FIXED.moves });
  });

  it("T-2: 終局の語を 切れ負け・詰み に替えると timeUp・mate(ply 21)", () => {
    expect(imported(importKif(withEnding("  21 切れ負け   ( 0:01/00:00:30)"))).endingFact).toStrictEqual({ kind: "timeUp", ply: 21 });
    expect(imported(importKif(withEnding("  21 詰み"))).endingFact).toStrictEqual({ kind: "mate", ply: 21 });
  });

  it("T-3: KIF の 12 語を 1 本ずつ読むと 12 の英名がすべて出て重ならない。語の表と判定の語は同じ集合", () => {
    const table: Array<[word: string, kind: string]> = [
      ["投了", "resign"], ["中断", "abort"], ["千日手", "repetition"], ["持将棋", "impasse"], ["詰み", "mate"], ["不詰", "noMate"],
      ["切れ負け", "timeUp"], ["反則勝ち", "illegalWin"], ["反則負け", "illegalLoss"], ["入玉勝ち", "enteringKingWin"], ["不戦勝", "defaultWin"], ["不戦敗", "defaultLoss"],
    ];
    const read = table.map(([word]) => imported(importKif(withEnding(`  21 ${word}`))).endingFact);
    expect(read).toStrictEqual(table.map(([, kind]) => ({ kind, ply: 21 })));
    expect(new Set(read.map((ending) => ending?.kind)).size).toBe(12);
    expect(Object.entries(ENDING_KIF_WORDS).map(([kind, word]) => [word, kind])).toStrictEqual(table);
    expect(new Set(KIF_ENDINGS)).toStrictEqual(new Set(table.map(([word]) => word)));
  });

  it("T-4: 終局の行が無い KIF は endingFact が null。固定棋譜は ending: null のキーを持つ", () => {
    const r = imported(importKif(kifText({ tail: [] })));
    expect(r.endingFact).toBeNull();
    const fixed = toFixedKifu(r, "x", "自作の KIF");
    expect(Object.keys(fixed)).toStrictEqual(["id", "source", "ending", "moves"]);
    expect(fixed.ending).toBeNull();
  });

  it("T-5(R-1): 20 手の後の終局の行の手数が 25 なら unreadable。行は読めなかった行だけに入り、結果の ending は null、取り込みは続く", () => {
    const r = importKif(withEnding("  25 投了"));
    expect(r.kind).toBe("imported");
    const ok = imported(r);
    expect(toFixedKifu(ok, "x", "自作の KIF")).toStrictEqual({
      id: "x",
      source: "自作の KIF",
      ending: { kind: "unreadable", reason: "ply_mismatch", ply: null },
      moves: FIXED.moves,
    });
    expect(ok.lines.unread.map((l) => [l.lineNo, l.why])).toStrictEqual([[27, "ending_ply_mismatch"]]);
    expect(ok.ending).toBeNull();
    expect(ok.lines.unused.filter((l) => l.kind === "ending")).toHaveLength(0);
    // 食い違った行の後の指し手行は、今までどおり「終局の行の後」として読まない(手数の合う 21 投了 でも)
    const after = imported(importKif(kifText({ tail: ["  25 投了", "  21 投了"] })));
    expect(after.endingFact).toStrictEqual({ kind: "unreadable", reason: "ply_mismatch", ply: null });
    expect(after.lines.unread.map((l) => l.why)).toStrictEqual(["ending_ply_mismatch", "終局の行の後にある指し手行"]);
  });

  it("T-6(R-4): 語の後に文が続く終局の行でも { kind: resign, ply: 21 } だけで、文は写らない", () => {
    const fixed = toFixedKifu(imported(importKif(withEnding("  21 投了 〇〇〇〇"))), "x", "自作の KIF");
    expect(fixed.ending).toStrictEqual({ kind: "resign", ply: 21 });
    expect(JSON.stringify(fixed)).not.toContain("〇〇〇〇");
  });

  it("T-7(S-3): CSA の %TORYO は resign、表に無い語と符号つきの語は unlisted(語は写さない)。ply は指し手数 + 1", () => {
    expect(imported(importCsa(csaText())).endingFact).toStrictEqual({ kind: "resign", ply: 21 });
    expect(imported(importCsa(csaText({ ending: "%NANIKA_NO_OWARI" }))).endingFact).toStrictEqual({ kind: "unlisted", ply: 21 });
    expect(imported(importCsa(csaText({ ending: "%+ILLEGAL_ACTION" }))).endingFact).toStrictEqual({ kind: "unlisted", ply: 21 });
    expect(imported(importCsa(csaText({ moves: ["+7776FU"] }))).endingFact).toStrictEqual({ kind: "resign", ply: 2 });
  });

  it("T-7 の続き: CSA の語の表は、V3.0 の文書で意味が KIF の語と同じ 8 語だけ。文書にあって表に入れない語は unlisted", () => {
    const table: Array<[word: string, kind: string]> = [
      ["%TORYO", "resign"], ["%CHUDAN", "abort"], ["%SENNICHITE", "repetition"], ["%TIME_UP", "timeUp"],
      ["%ILLEGAL_MOVE", "illegalLoss"], ["%JISHOGI", "impasse"], ["%TSUMI", "mate"], ["%FUZUMI", "noMate"],
      ["%+ILLEGAL_ACTION", "unlisted"], ["%-ILLEGAL_ACTION", "unlisted"], ["%KACHI", "unlisted"], ["%HIKIWAKE", "unlisted"],
      ["%MAX_MOVES", "unlisted"], ["%MATTA", "unlisted"], ["%ERROR", "unlisted"],
    ];
    expect(table.map(([word]) => imported(importCsa(csaText({ ending: word }))).endingFact)).toStrictEqual(table.map(([, kind]) => ({ kind, ply: 21 })));
  });

  it("T-12(S-1 の限界): KIF の表に無い語の終局の行は、今までどおり取り込み全体が unparsable_move で止まる", () => {
    const r = importKif(withEnding("  21 勝ち宣言"));
    expect(r.kind === "not_imported" ? [r.reason, r.lineNo] : r.kind).toStrictEqual(["unparsable_move", 27]);
  });
});
