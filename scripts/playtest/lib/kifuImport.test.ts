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
import { parseKifMoveOrDrop } from "shogiops/notation/kif";
import { describe, expect, it } from "vitest";

import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { decodeKifuBytes, importCsa, importKif, STANDARD_START_SFEN, toFixedKifu, type KifuImportResult } from "./kifuImport.js";

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

function csaText(opts: { board?: string[]; moves?: string[]; commaTime?: boolean } = {}): string {
  const moves = opts.moves ?? CSA_MOVES;
  return [
    "V2.2",
    "N+先手の人",
    "N-後手の人",
    "$START_TIME:2026/09/10 10:00:00",
    ...(opts.board ?? ["PI", "+"]),
    ...moves.flatMap((m) => (opts.commaTime ? [`${m},T1`] : [m, "T1"])),
    "%TORYO",
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
    expect(Object.keys(fixed)).toEqual(["id", "source", "moves"]);
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
