import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "./moveHistory.js";
import {
  analyzeOpeningFormationFromEvents,
  loadOpeningsFromDir,
  openingToShapeDefinition,
  type OpeningDefinition,
  type OpeningFormationResult,
} from "./openingDetector.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// apps/server/src/analysis -> apps/server/src -> apps/server -> apps -> リポジトリルート
const DRAFT_OPENINGS_DIR = path.join(
  __dirname,
  "..",
  "..",
  "..",
  "..",
  "data",
  "drafts",
  "2026-09-25-knowledge",
  "openings",
);

/** テスト用の opening(data/ の実データではない。将棋知識を足さないよう、駒とマスは既存の初期配置・定跡と無関係な素の対だけを使う)。 */
function makeOpening(
  id: string,
  side: OpeningDefinition["side"],
  pattern: Array<{ piece: string; to: string; order_hint?: number }> | undefined,
): OpeningDefinition {
  const base: OpeningDefinition = {
    id,
    name: `テスト戦型_${id}`,
    name_kana: `てすとせんけい_${id}`,
    side,
    family: "テスト",
    leads_to_shape_ids: [],
    scenario: null,
    source: "テスト用のダミー(将棋知識ではない)",
    confidence_level: "low",
    review_status: "draft",
  };
  return pattern === undefined ? base : { ...base, recognition_pattern: pattern };
}

function findResult(results: OpeningFormationResult[], openingId: string): OpeningFormationResult {
  const found = results.find((r) => r.openingId === openingId);
  if (!found) throw new Error(`opening not found in results: ${openingId}`);
  return found;
}

function analyzeAfter(moveHistory: string[], openings: OpeningDefinition[]): OpeningFormationResult[] {
  const { events, finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
  return analyzeOpeningFormationFromEvents(finalSfen, events, openings);
}

describe("openingToShapeDefinition", () => {
  it("recognition_pattern の {piece, to} を required_pieces の {piece, square, optional:false} へ写す", () => {
    const opening = makeOpening("t_map", "self", [
      { piece: "銀", to: "3h", order_hint: 1 },
      { piece: "金", to: "5h", order_hint: 2 },
    ]);

    const shape = openingToShapeDefinition(opening);

    expect(shape).not.toBeNull();
    expect(shape?.required_pieces).toEqual([
      { piece: "銀", square: "3h", optional: false },
      { piece: "金", square: "5h", optional: false },
    ]);
    // 形の判定に要る欄をそのまま写し、無い欄は発明しない。
    expect(shape?.id).toBe("t_map");
    expect(shape?.name).toBe(opening.name);
    expect(shape?.name_kana).toBe(opening.name_kana);
    expect(shape?.side).toBe("self");
    expect(shape?.family).toBe("テスト");
    expect(shape?.parent_shape_id).toBeNull();
    expect(shape?.characteristics).toBe("");
    expect(shape?.confidence_level).toBe("low");
    expect(shape?.review_status).toBe("draft");
    // order_hint は読まない(写し先にも現れない)。
    expect(JSON.stringify(shape)).not.toContain("order_hint");
  });

  it("recognition_pattern が無い・空の opening は認識の候補にならない(null)", () => {
    expect(openingToShapeDefinition(makeOpening("t_none", "self", undefined))).toBeNull();
    expect(openingToShapeDefinition(makeOpening("t_empty", "self", []))).toBeNull();
  });
});

describe("analyzeOpeningFormationFromEvents", () => {
  it("side=self は先手(sente)の駒だけ・side=opponent は後手(gote)の駒だけを数える", () => {
    // 先手が銀を3八へ、後手が銀を3二へ動かした局面。
    const results = analyzeAfter(
      ["3i3h", "3a3b"],
      [
        makeOpening("t_self_3h", "self", [{ piece: "銀", to: "3h" }]),
        makeOpening("t_opp_3h", "opponent", [{ piece: "銀", to: "3h" }]),
        makeOpening("t_self_3b", "self", [{ piece: "銀", to: "3b" }]),
        makeOpening("t_opp_3b", "opponent", [{ piece: "銀", to: "3b" }]),
      ],
    );

    // 3八の銀は先手の駒なので self 側だけが数える。
    expect(findResult(results, "t_self_3h").matchedSquares).toEqual(["3h"]);
    expect(findResult(results, "t_self_3h").status).toBe("completed");
    expect(findResult(results, "t_opp_3h").matchedSquares).toEqual([]);
    expect(findResult(results, "t_opp_3h").status).toBe("none");

    // 3二の銀は後手の駒なので opponent 側だけが数える。
    expect(findResult(results, "t_opp_3b").matchedSquares).toEqual(["3b"]);
    expect(findResult(results, "t_opp_3b").status).toBe("completed");
    expect(findResult(results, "t_self_3b").matchedSquares).toEqual([]);
    expect(findResult(results, "t_self_3b").status).toBe("none");

    expect(findResult(results, "t_self_3h").perspectiveColor).toBe("sente");
    expect(findResult(results, "t_opp_3b").perspectiveColor).toBe("gote");
  });

  it("全ての対が盤にあり、動いた証拠もある局面は completed", () => {
    const results = analyzeAfter(
      ["3i3h", "3a3b", "6i5h"],
      [
        makeOpening("t_two", "self", [
          { piece: "銀", to: "3h" },
          { piece: "金", to: "5h" },
        ]),
      ],
    );
    const result = findResult(results, "t_two");

    expect(result.matchedSquares.sort()).toEqual(["3h", "5h"]);
    expect(result.missingSquares).toEqual([]);
    expect(result.formationEvidence.map((e) => e.square).sort()).toEqual(["3h", "5h"]);
    expect(result.matchScore).toBe(1);
    expect(result.status).toBe("completed");
  });

  it("1つの対だけが盤にあり、その駒が動いた証拠がある局面は forming", () => {
    const results = analyzeAfter(
      ["3i3h", "3a3b"],
      [
        makeOpening("t_two", "self", [
          { piece: "銀", to: "3h" },
          { piece: "金", to: "5h" },
        ]),
      ],
    );
    const result = findResult(results, "t_two");

    expect(result.matchedSquares).toEqual(["3h"]);
    expect(result.missingSquares).toEqual(["5h"]);
    expect(result.formationEvidence).toHaveLength(1);
    expect(result.formationEvidence[0]?.square).toBe("3h");
    expect(result.formationEvidence[0]?.evidence.moveUsi).toBe("3i3h");
    expect(result.status).toBe("forming");
  });

  it("盤には一致しているが動いた証拠が無い(初期配置のままの駒)場合は none", () => {
    // 1手も指していない初期局面。4九の金は初期配置のまま一致するが、動いた証拠は無い。
    const results = analyzeOpeningFormationFromEvents(DEFAULT_INITIAL_SFEN, [], [
      makeOpening("t_initial", "self", [
        { piece: "金", to: "4i" },
        { piece: "銀", to: "3h" },
      ]),
    ]);
    const result = findResult(results, "t_initial");

    expect(result.matchedSquares).toEqual(["4i"]);
    expect(result.missingSquares).toEqual(["3h"]);
    expect(result.formationEvidence).toEqual([]);
    expect(result.status).toBe("none");
  });

  it("「証拠1件以下かつ欠け2件以上」が出力の欄だけから計算できる(I-9 相当)", () => {
    const results = analyzeAfter(
      ["3i3h"],
      [
        makeOpening("t_four", "self", [
          { piece: "金", to: "4i" },
          { piece: "銀", to: "3h" },
          { piece: "玉", to: "2h" },
          { piece: "飛", to: "6h" },
        ]),
      ],
    );
    const result = findResult(results, "t_four");

    expect(result.matchedSquares.sort()).toEqual(["3h", "4i"]);
    expect(result.missingSquares.sort()).toEqual(["2h", "6h"]);
    expect(result.formationEvidence).toHaveLength(1);
    // 判定そのものはこのモジュールに無く、呼び出し側が欄から数えられることだけを確かめる。
    const i9Like = result.missingSquares.length >= 2 && result.formationEvidence.length <= 1;
    expect(i9Like).toBe(true);
  });

  it("結果は matchScore 降順・同点なら id 昇順で返る(委譲先の並び順のまま)", () => {
    const results = analyzeOpeningFormationFromEvents(DEFAULT_INITIAL_SFEN, [], [
      makeOpening("t_b_full", "self", [{ piece: "金", to: "6i" }]),
      makeOpening("t_c_half", "self", [
        { piece: "金", to: "4i" },
        { piece: "銀", to: "3h" },
      ]),
      makeOpening("t_a_full", "self", [{ piece: "金", to: "4i" }]),
    ]);

    expect(results.map((r) => r.openingId)).toEqual(["t_a_full", "t_b_full", "t_c_half"]);
    expect(results.map((r) => r.matchScore)).toEqual([1, 1, 0.5]);
  });

  it("下書きの openings(実ファイル)を読み込むと、recognition_pattern を持つものだけが候補になる", () => {
    const openings = loadOpeningsFromDir(DRAFT_OPENINGS_DIR);
    expect(openings).toHaveLength(111);

    let candidates = 0;
    let skipped = 0;
    for (const opening of openings) {
      // ファイル名・戦型名はメッセージに出さない(件数だけで確かめる)。
      const shape = openingToShapeDefinition(opening);
      if (shape === null) skipped += 1;
      else candidates += 1;
    }
    expect(candidates).toBe(108);
    expect(skipped).toBe(3);

    // 例外なく最後まで判定できる(駒名・マス表記が既存の変換で扱える)。
    const results = analyzeOpeningFormationFromEvents(DEFAULT_INITIAL_SFEN, [], openings);
    expect(results).toHaveLength(108);
  });
});
