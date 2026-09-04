import { describe, expect, it } from "vitest";
import {
  detectIntents,
  InvalidSfenError,
  IntentDetectorError,
  type IntentDetectionResult,
} from "./intentDetector.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "./moveHistory.js";
import type { IntentDefinition } from "./intentRepository.js";

// 手番は先手(自分=四間飛車)から始まるため、gote(相手=居飛車)側の指し手をrecognition_pattern
// どおりに進めるには、間に合法な先手の手を挟む必要がある。ここでの先手の手は何でもよく、
// 判定結果に影響しない(無関係なファイルの歩を1マスずつ進めるだけ)。
const SENTE_FILLERS = ["1g1f", "2g2f", "3g3f", "4g4f", "5g5f", "6g6f", "9g9f", "8g8f"];

function interleaveWithSenteFillers(goteMoves: string[]): string[] {
  const moves: string[] = [];
  goteMoves.forEach((goteMove, i) => {
    const filler = SENTE_FILLERS[i];
    if (!filler) throw new Error("SENTE_FILLERSが不足しています(テストフィクスチャの調整が必要)");
    moves.push(filler, goteMove);
  });
  return moves;
}

function sfenAfter(moveHistory: string[]): string {
  return replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN).finalSfen;
}

function findResult(results: IntentDetectionResult[], intentId: string): IntentDetectionResult {
  const found = results.find((r) => r.intentId === intentId);
  if (!found) throw new Error(`intent not found in results: ${intentId}`);
  return found;
}

// data/intents/hayajikake.json の recognition_pattern: 歩 6d(1) -> 6e(2)。
// 居飛車(gote)の6筋の歩をそのまま2回まっすぐ突くだけで両シグネチャに到達できる、
// 最も手数の少ないケース。
const HAYAJIKAKE_GOTE_MOVES_FULL = ["6c6d", "6d6e"];

// data/intents/boh_gin.json の recognition_pattern: 銀 7c(1) -> 7d(2) -> 7e(3)。
// 銀が通る前に、同じ筋の歩(7c/7d/7e)を1マスずつ先に逃がしておく必要がある
// (7c/7dは初期配置で歩に占有されているため)。
const BOH_GIN_GOTE_MOVES_FULL = [
  "7c7d", // 歩を退避(7cを空ける)
  "7a7b", // 銀 前進
  "7b7c", // 銀 7c到達 -> シグネチャ1
  "7d7e", // 歩をさらに退避(7dを空ける)
  "7c7d", // 銀 7d到達 -> シグネチャ2
  "7e7f", // 歩をさらに退避(7eを空ける)
  "7d7e", // 銀 7e到達 -> シグネチャ3
];

// data/intents/naname_bogin.json の recognition_pattern: 銀 4b(1) -> 5c(2) -> 6d(3)。
// 3aの銀は斜め前進で4bへ直接到達できる(4bは初期配置で空)。5cは歩の退避が必要。
const NANAME_BOGIN_GOTE_MOVES_FULL = [
  "3a4b", // 銀 4b到達 -> シグネチャ1
  "5c5d", // 歩を退避(5cを空ける)
  "4b5c", // 銀 5c到達 -> シグネチャ2
  "5c6d", // 銀 6d到達 -> シグネチャ3
];

describe("detectIntents", () => {
  it("初期局面(履歴なし) -> どのintentもmatchStatus: none", () => {
    const results = detectIntents(DEFAULT_INITIAL_SFEN, []);
    expect(results.length).toBeGreaterThan(0);
    for (const result of results) {
      expect(result.matchStatus).toBe("none");
      expect(result.matchScore).toBe(0);
      expect(result.matchedSignatures).toEqual([]);
    }
  });

  it("早仕掛けのrecognition_patternに完全一致する局面 -> matchStatus: matched, matchScore: 1", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);
    const results = detectIntents(sfen, moveHistory);

    const hayajikake = findResult(results, "hayajikake");
    expect(hayajikake.matchStatus).toBe("matched");
    expect(hayajikake.matchScore).toBe(1);
    expect(hayajikake.unmatchedSignatures).toEqual([]);
    expect(hayajikake.matchedSignatures.map((s) => s.to)).toEqual(["6d", "6e"]);
    // 根拠(どの手で観測したか)が含まれていること
    expect(hayajikake.matchedSignatures[0]?.evidence.moveUsi).toBe("6c6d");
    expect(hayajikake.matchedSignatures[1]?.evidence.moveUsi).toBe("6d6e");
  });

  it("早仕掛けの途中段階(1手目のみ観測) -> matchStatus: forming, 0 < matchScore < 1", () => {
    const moveHistory = interleaveWithSenteFillers([HAYAJIKAKE_GOTE_MOVES_FULL[0]!]);
    const sfen = sfenAfter(moveHistory);
    const results = detectIntents(sfen, moveHistory);

    const hayajikake = findResult(results, "hayajikake");
    expect(hayajikake.matchStatus).toBe("forming");
    expect(hayajikake.matchScore).toBeCloseTo(0.5);
    expect(hayajikake.matchedSignatures).toHaveLength(1);
    expect(hayajikake.unmatchedSignatures).toHaveLength(1);
  });

  it("棒銀のrecognition_patternに完全一致する局面 -> matchStatus: matched", () => {
    const moveHistory = interleaveWithSenteFillers(BOH_GIN_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);
    const results = detectIntents(sfen, moveHistory);

    const bohGin = findResult(results, "boh_gin");
    expect(bohGin.matchStatus).toBe("matched");
    expect(bohGin.matchScore).toBe(1);
    expect(bohGin.matchedSignatures.map((s) => s.to).sort()).toEqual(["7c", "7d", "7e"]);
  });

  it("斜め棒銀のrecognition_patternに完全一致する局面 -> matchStatus: matched", () => {
    const moveHistory = interleaveWithSenteFillers(NANAME_BOGIN_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);
    const results = detectIntents(sfen, moveHistory);

    const nanameBogin = findResult(results, "naname_bogin");
    expect(nanameBogin.matchStatus).toBe("matched");
    expect(nanameBogin.matchScore).toBe(1);
    expect(nanameBogin.matchedSignatures.map((s) => s.to)).toEqual(["4b", "5c", "6d"]);

    // 棒銀・早仕掛けの手がかりは一切登場していないため、他のintentはnoneのまま
    // (=「相手が斜め棒銀をしている」からといって、他の意図を誤検知しない)。
    const bohGin = findResult(results, "boh_gin");
    const hayajikake = findResult(results, "hayajikake");
    expect(bohGin.matchStatus).toBe("none");
    expect(hayajikake.matchStatus).toBe("none");
  });

  it("どのintentのrecognition_patternにも該当しない局面 -> 全intentがmatchStatus: none", () => {
    const goteMoves = ["3c3d", "8c8d"];
    const moveHistory = interleaveWithSenteFillers(goteMoves);
    const sfen = sfenAfter(moveHistory);
    const results = detectIntents(sfen, moveHistory);

    for (const result of results) {
      expect(result.matchStatus).toBe("none");
      expect(result.matchScore).toBe(0);
    }
  });

  it("不正なSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => detectIntents("not-a-valid-sfen", [])).toThrow(InvalidSfenError);
  });

  it("sfenとmoveHistoryの組み合わせが矛盾している場合、IntentDetectorErrorを投げる", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    // わざと初期局面のSFENを渡す(実際にはmoveHistory分だけ進んでいるはず)。
    expect(() => detectIntents(DEFAULT_INITIAL_SFEN, moveHistory)).toThrow(IntentDetectorError);
  });

  it("同じ入力に対して常に同じ結果を返す(決定的)", () => {
    const moveHistory = interleaveWithSenteFillers(BOH_GIN_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);
    const first = detectIntents(sfen, moveHistory);
    const second = detectIntents(sfen, moveHistory);
    expect(second).toEqual(first);
  });

  it("特定のintentだけに絞り込んで判定できる(将来の呼び出し元向けオプション)", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);
    const onlyHayajikake: IntentDefinition = {
      id: "hayajikake",
      name: "早仕掛け",
      opening_id: "ibisha",
      recognition_pattern: [
        { piece: "歩", to: "6d", order_hint: 1 },
        { piece: "歩", to: "6e", order_hint: 2 },
      ],
      current_aim_explanation: "",
      next_aim_explanation: "",
      confidence_level: "medium",
    };
    const results = detectIntents(sfen, moveHistory, { intents: [onlyHayajikake] });
    expect(results).toHaveLength(1);
    expect(results[0]?.matchStatus).toBe("matched");
  });
});
