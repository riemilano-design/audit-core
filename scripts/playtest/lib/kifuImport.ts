// 外部の棋譜(KIF / CSA)を、固定棋譜の JSON({ id, source, moves: [USI...] })へ変換する試作。
// STEP D0-KIFU(仮番号。docs/STEP_D0-KIFU_PLAN_2026-09-14.md)。
//
// 【このファイルがやること】
// - KIF(柿木形式)と CSA を行ごとに読み、本譜の指し手を USI に直す
// - 1 手ずつ apps/server の rules/applyMove で適用する(非合法ならそこで止めて not_imported)
// - 往復の確認を返す: shogiops の Position.play で進めた終局局面との一致、指し手表記の作り直しとの一致
// - **行を 3 つに分けて全部返す**(規則 11.6): 採った / 読んだが使わない(種類つき) / 読めなかった
//
// 【このファイルが絶対にやらないこと】
// - 平手以外の開始局面の変換(unsupported_start として返す。本番の対局は初期局面から始まる)
// - 変化(分岐)の取り込み(本譜だけを読む。変化の行は「読んだが使わない」に数える)
// - 読めない行を黙って捨てること
// - 将棋の判断・評価(形式の変換だけを行う)

import { makeCsaMoveOrDrop, parseCsaHeader, parseCsaMoveOrDrop } from "shogiops/notation/csa";
import { kifDropRegex, kifMoveRegex, makeKifMoveOrDrop, parseKifHeader, parseKifMoveOrDrop } from "shogiops/notation/kif";
import { makeSfen } from "shogiops/sfen";
import type { Square } from "shogiops/types";
import { makeUsi } from "shogiops/util";
import type { Position } from "shogiops/variant/position";

import { applyMove, IllegalMoveError } from "../../../apps/server/src/rules/applyMove.js";

/** 本番の対局が始まる局面(平手の初期局面)。 */
export const STANDARD_START_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

export type KifuFormat = "kif" | "csa";

/** 「読んだが使わない行」の種類。 */
export type UnusedKind = "header" | "column_header" | "board" | "time" | "comment" | "ending" | "variation" | "summary";

export interface SourceLine {
  /** 元の棋譜の何行目か(1 始まり。CSA でカンマ区切りの場合は同じ行番号が続く) */
  lineNo: number;
  /** 元の行(CSA のカンマ区切りでは、その片) */
  text: string;
}

export interface ClassifiedLines {
  /** 指し手として採った行 */
  moves: Array<SourceLine & { ply: number; usi: string; timeDropped: boolean }>;
  /** 読んだが使わない行 */
  unused: Array<SourceLine & { kind: UnusedKind }>;
  /** 読めなかった行(知らない形・終局の後の指し手)。黙って捨てない */
  unread: Array<SourceLine & { why: string }>;
}

export interface RoundTrip {
  /** 棋譜の指し手を shogiops の Position.play でそのまま進めた終局局面 */
  libraryFinalSfen: string;
  /** applyMove で進めた終局局面と、盤・手番・持ち駒が一致したか */
  finalPositionMatches: boolean;
  /** 指し手表記を作り直して、元の表記と一致しなかった手 */
  notationMismatches: Array<{ ply: number; original: string; remade: string | null }>;
}

export type NotImportedReason =
  | "header_unreadable"
  | "unsupported_start"
  | "unparsable_move"
  | "illegal_move"
  | "no_move_lines";

export type KifuImportResult =
  | {
      kind: "imported";
      format: KifuFormat;
      moves: string[];
      finalSfen: string;
      /** 終局の行(投了・千日手・%TORYO など)。無ければ null(棋譜に書かれていなかった) */
      ending: SourceLine | null;
      lines: ClassifiedLines;
      roundTrip: RoundTrip;
    }
  | {
      kind: "not_imported";
      format: KifuFormat;
      reason: NotImportedReason;
      detail: string;
      /** 原因の行。開始局面のように行に帰せないときは null */
      lineNo: number | null;
      lines: ClassifiedLines;
    };

/** 盤・手番・持ち駒(SFEN の先頭 3 欄)。手数の欄は形式ごとに数え方が違うので比べない。 */
function positionPart(sfen: string): string {
  return sfen.split(" ").slice(0, 3).join(" ");
}

function emptyLines(): ClassifiedLines {
  return { moves: [], unused: [], unread: [] };
}

// ---------------------------------------------------------------- KIF

const KIF_ENDINGS = ["投了", "中断", "千日手", "持将棋", "詰み", "不詰", "切れ負け", "反則勝ち", "反則負け", "入玉勝ち", "不戦勝", "不戦敗"];
// 行の正規化で「:」は全角の「：」に置き換わる(shogiops の normalizedKifLines と同じ)。消費時間はその後の形で探す。
const KIF_TIME = /\s*\(\s*\d+[:：]\d+\s*\/\s*\d+[:：]\d+[:：]\d+\s*\)\s*$/;
const KIF_MOVE_LINE = /^(\d+)\s+(\S.*)$/;
const KIF_BOARD_PREFIXES = ["|", "+---", "先手の持駒", "後手の持駒", "下手の持駒", "上手の持駒", "先手番", "後手番", "上手番", "下手番"];

/** shogiops の normalizedKifLines と同じ正規化を 1 行ずつ行う(行番号を保つため)。 */
function normalizeKifLine(line: string): string {
  return line.replace(/:/g, "：").replace(/　/g, " ").trim();
}

export function importKif(raw: string): KifuImportResult {
  const lines = emptyLines();
  const header = parseKifHeader(raw);
  if (header.isErr) {
    return { kind: "not_imported", format: "kif", reason: "header_unreadable", detail: String(header.error), lineNo: null, lines };
  }
  const libPos: Position = header.value;
  const startSfen = makeSfen(libPos);
  const rawLines = raw.split(/\r?\n/);
  if (positionPart(startSfen) !== positionPart(STANDARD_START_SFEN)) {
    const tag = rawLines.findIndex((l) => normalizeKifLine(l).startsWith("手合割："));
    return {
      kind: "not_imported",
      format: "kif",
      reason: "unsupported_start",
      detail: `開始局面が平手の初期局面ではない: ${startSfen}`,
      lineNo: tag >= 0 ? tag + 1 : null,
      lines,
    };
  }

  let sfen = STANDARD_START_SFEN;
  let lastDest: Square | undefined;
  let ending: SourceLine | null = null;
  let inVariation = false;

  for (const [index, original] of rawLines.entries()) {
    const lineNo = index + 1;
    const text = normalizeKifLine(original);
    if (text.length === 0) continue; // 空行は何も運ばない
    const src = { lineNo, text: original };

    if (inVariation || text.startsWith("変化：")) {
      inVariation = true;
      lines.unused.push({ ...src, kind: "variation" });
      continue;
    }
    if (text.startsWith("#") || text.startsWith("*") || text.startsWith("&")) {
      lines.unused.push({ ...src, kind: "comment" });
      continue;
    }
    if (text.startsWith("手数")) {
      lines.unused.push({ ...src, kind: "column_header" });
      continue;
    }
    if (/^まで\d+手/.test(text)) {
      lines.unused.push({ ...src, kind: "summary" });
      continue;
    }
    if (KIF_BOARD_PREFIXES.some((p) => text.startsWith(p)) || /^[１２３４５６７８９ ]+$/.test(text)) {
      lines.unused.push({ ...src, kind: "board" });
      continue;
    }

    const moveLine = text.match(KIF_MOVE_LINE);
    if (moveLine) {
      const plyNo = Number(moveLine[1]);
      const rest = moveLine[2] ?? "";
      const moveText = rest.replace(KIF_TIME, "").trim();
      const timeDropped = moveText !== rest.trim();

      if (ending !== null) {
        lines.unread.push({ ...src, why: "終局の行の後にある指し手行" });
        continue;
      }
      if (KIF_ENDINGS.some((w) => moveText.startsWith(w))) {
        ending = src;
        lines.unused.push({ ...src, kind: "ending" });
        continue;
      }
      const expected = lines.moves.length + 1;
      if (plyNo !== expected) {
        lines.unread.push({ ...src, why: `手数が続いていない(期待 ${expected})` });
        return { kind: "not_imported", format: "kif", reason: "unparsable_move", detail: `手数 ${plyNo}(期待 ${expected})`, lineNo, lines };
      }
      if (!kifMoveRegex.test(moveText) && !kifDropRegex.test(moveText)) {
        lines.unread.push({ ...src, why: "指し手の表記として読めない" });
        return { kind: "not_imported", format: "kif", reason: "unparsable_move", detail: moveText, lineNo, lines };
      }
      const md = parseKifMoveOrDrop(moveText, lastDest);
      if (md === undefined) {
        lines.unread.push({ ...src, why: "指し手の表記として読めない" });
        return { kind: "not_imported", format: "kif", reason: "unparsable_move", detail: moveText, lineNo, lines };
      }
      const usi = makeUsi(md);
      try {
        sfen = applyMove(sfen, usi);
      } catch (e) {
        if (!(e instanceof IllegalMoveError)) throw e;
        lines.unread.push({ ...src, why: "非合法な指し手" });
        return { kind: "not_imported", format: "kif", reason: "illegal_move", detail: `${expected} 手目 ${moveText}(${usi})`, lineNo, lines };
      }
      lines.moves.push({ ...src, ply: expected, usi, timeDropped });
      lastDest = md.to;
      continue;
    }

    if (/^[^\s：]+：/.test(text)) {
      lines.unused.push({ ...src, kind: "header" });
      continue;
    }
    lines.unread.push({ ...src, why: "知らない形の行" });
  }

  if (lines.moves.length === 0) {
    return { kind: "not_imported", format: "kif", reason: "no_move_lines", detail: "指し手の行が 1 つも無い", lineNo: null, lines };
  }

  // 往復: 同じ表記を shogiops だけで進め、指し手表記も作り直す。
  const notationMismatches: RoundTrip["notationMismatches"] = [];
  let dest: Square | undefined;
  for (const m of lines.moves) {
    const moveText = normalizeKifLine(m.text).match(KIF_MOVE_LINE)?.[2]?.replace(KIF_TIME, "").trim() ?? "";
    const md = parseKifMoveOrDrop(moveText, dest);
    if (md === undefined) {
      notationMismatches.push({ ply: m.ply, original: moveText, remade: null });
      break;
    }
    const remade = makeKifMoveOrDrop(libPos, md, dest);
    if (remade === undefined || normalizeKifLine(remade) !== moveText) {
      notationMismatches.push({ ply: m.ply, original: moveText, remade: remade ?? null });
    }
    libPos.play(md);
    dest = md.to;
  }
  const libraryFinalSfen = makeSfen(libPos);

  return {
    kind: "imported",
    format: "kif",
    moves: lines.moves.map((m) => m.usi),
    finalSfen: sfen,
    ending,
    lines,
    roundTrip: {
      libraryFinalSfen,
      finalPositionMatches: positionPart(libraryFinalSfen) === positionPart(sfen),
      notationMismatches,
    },
  };
}

// ---------------------------------------------------------------- CSA

const CSA_MOVE = /^[+-]\d{4}[A-Z]{2}$/;

export function importCsa(raw: string): KifuImportResult {
  const lines = emptyLines();
  const header = parseCsaHeader(raw);
  if (header.isErr) {
    return { kind: "not_imported", format: "csa", reason: "header_unreadable", detail: String(header.error), lineNo: null, lines };
  }
  const libPos = header.value;
  const startSfen = makeSfen(libPos);
  if (positionPart(startSfen) !== positionPart(STANDARD_START_SFEN)) {
    return {
      kind: "not_imported",
      format: "csa",
      reason: "unsupported_start",
      detail: `開始局面が平手の初期局面ではない: ${startSfen}`,
      lineNo: null,
      lines,
    };
  }

  // CSA はカンマで 1 行に複数の文を書ける。行番号を保ったまま片に割る。
  const pieces: SourceLine[] = [];
  for (const [index, original] of raw.split(/\r?\n/).entries()) {
    for (const part of original.split(",")) {
      const text = part.trim();
      if (text.length > 0) pieces.push({ lineNo: index + 1, text });
    }
  }

  let sfen = STANDARD_START_SFEN;
  let ending: SourceLine | null = null;
  const notationMismatches: RoundTrip["notationMismatches"] = [];

  for (const src of pieces) {
    const { text, lineNo } = src;
    if (/^V\d/.test(text) || /^N[+-]/.test(text) || text.startsWith("$")) {
      lines.unused.push({ ...src, kind: "header" });
      continue;
    }
    if (text.startsWith("'")) {
      lines.unused.push({ ...src, kind: "comment" });
      continue;
    }
    if (/^P[I1-9+-]/.test(text) || text === "+" || text === "-") {
      lines.unused.push({ ...src, kind: "board" });
      continue;
    }
    if (/^T\d+$/.test(text)) {
      lines.unused.push({ ...src, kind: "time" });
      continue;
    }
    if (text.startsWith("%")) {
      if (ending === null) {
        ending = src;
        lines.unused.push({ ...src, kind: "ending" });
      } else {
        lines.unread.push({ ...src, why: "2 つ目の終局の行" });
      }
      continue;
    }
    if (CSA_MOVE.test(text)) {
      if (ending !== null) {
        lines.unread.push({ ...src, why: "終局の行の後にある指し手行" });
        continue;
      }
      const ply = lines.moves.length + 1;
      const sign = libPos.turn === "sente" ? "+" : "-";
      if (!text.startsWith(sign)) {
        lines.unread.push({ ...src, why: `手番の符号が合わない(期待 ${sign})` });
        return { kind: "not_imported", format: "csa", reason: "unparsable_move", detail: `${ply} 手目 ${text}`, lineNo, lines };
      }
      const md = parseCsaMoveOrDrop(libPos, text);
      if (md === undefined) {
        lines.unread.push({ ...src, why: "指し手の表記として読めない" });
        return { kind: "not_imported", format: "csa", reason: "unparsable_move", detail: text, lineNo, lines };
      }
      const usi = makeUsi(md);
      try {
        sfen = applyMove(sfen, usi);
      } catch (e) {
        if (!(e instanceof IllegalMoveError)) throw e;
        lines.unread.push({ ...src, why: "非合法な指し手" });
        return { kind: "not_imported", format: "csa", reason: "illegal_move", detail: `${ply} 手目 ${text}(${usi})`, lineNo, lines };
      }
      const remade = makeCsaMoveOrDrop(libPos, md);
      if (remade === undefined || remade !== text.slice(1)) {
        notationMismatches.push({ ply, original: text, remade: remade ?? null });
      }
      libPos.play(md);
      lines.moves.push({ ...src, ply, usi, timeDropped: false });
      continue;
    }
    lines.unread.push({ ...src, why: "知らない形の行" });
  }

  if (lines.moves.length === 0) {
    return { kind: "not_imported", format: "csa", reason: "no_move_lines", detail: "指し手の行が 1 つも無い", lineNo: null, lines };
  }
  const libraryFinalSfen = makeSfen(libPos);
  return {
    kind: "imported",
    format: "csa",
    moves: lines.moves.map((m) => m.usi),
    finalSfen: sfen,
    ending,
    lines,
    roundTrip: {
      libraryFinalSfen,
      finalPositionMatches: positionPart(libraryFinalSfen) === positionPart(sfen),
      notationMismatches,
    },
  };
}

// ---------------------------------------------------------------- 共通

/** 取り込めた棋譜を、固定棋譜の JSON の形にする(replay.ts がそのまま読める形)。 */
export function toFixedKifu(
  result: Extract<KifuImportResult, { kind: "imported" }>,
  id: string,
  source: string,
): { id: string; source: string; moves: string[] } {
  return { id, source, moves: [...result.moves] };
}

/**
 * 棋譜ファイルのバイト列を文字列にする。KIF は Shift_JIS のことが多い(.kif)。
 * UTF-8 として読んで置換文字(U+FFFD)が出たら Shift_JIS として読み直し、**どちらで読んだかを返す**。
 */
export function decodeKifuBytes(bytes: Uint8Array): { text: string; encoding: "utf-8" | "shift_jis" } {
  const utf8 = new TextDecoder("utf-8").decode(bytes);
  if (!utf8.includes("�")) return { text: utf8.replace(/^﻿/, ""), encoding: "utf-8" };
  return { text: new TextDecoder("shift_jis").decode(bytes), encoding: "shift_jis" };
}
