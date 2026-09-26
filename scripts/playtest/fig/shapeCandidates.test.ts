// STEP FIG-2 (a) の試験(計画 §5 を §8.2 の直しに合わせて読み替えたもの + 司令塔の追加指示)。
//
// 【材料】合成の形と合成の局面だけを使う(実データを読まない)。**例外は最後の 1 本**で、
// そこだけ `data/` を読む ― 注 3 の「未レビューの下書き 80 件を含む 82 形」の数が
// データと合っているかの校正で、数が動いたら注が嘘になるため(その 1 本だけと明記する)。
//
// 【計画 §5 からの読み替え(§8.2)】
// - §5 の 2「`hidden` の候補が落ちる」は**作らない** ― 露出では候補を捨てないため。
//   代わりに「名前は出ないが候補には残る」を固定する(試験 2)。
// - §5 の 4・5(`named` になる条件)は、**`named` が構造上返らないこと**の試験に置き換える
//   (司令塔の追加指示 1(a))。D'' の肝は R5(証拠 2 件の下限)と R5' で固定する(試験 4・5)。

import { describe, expect, it } from "vitest";

import { EXPOSURE_VALUE_SETS } from "../lib/recognitionMeasure.js";
import type { ShapeDefinition } from "../../../apps/server/src/analysis/shapeRepository.js";
import {
  FIG2A_EXPOSURE_VALUES,
  FIG2A_NOTES,
  ShapeCandidatesError,
  STANDARD_PIECE_COUNTS,
  findShapeCandidates,
  loadAllShapes,
  type ShapeCandidatesResult,
} from "./shapeCandidates.js";

// ---------------------------------------------------------------------------
// 合成の材料
// ---------------------------------------------------------------------------

/** 平手から 4 手(先手が 6九金 → 6八・4九金 → 4八)進めた局面。手数欄は 5。 */
const POSITION_MOVES = ["6i6h", "8c8d", "4i4h", "8d8e"] as const;
const POSITION_SFEN = "lnsgkgsnl/1r5b1/p1ppppppp/9/1p7/9/PPPPPPPPP/1B1G1G1R1/LNS1K1SNL b - 5";
const POSITION_PLY = 5;

/** 回した局(`mirrored: true`)の開始局面に見立てたもの(後手番の平手に 1 手当てた先手番の局面。手数欄は 2)。 */
const MIRRORED_START_SFEN = "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2";
const MIRRORED_SFEN = "lnsgkgsnl/1r5b1/p1pppp1pp/6p2/1p7/9/PPPPPPPPP/1B1G1G1R1/LNS1K1SNL b - 6";
const MIRRORED_PLY = 6;

function shape(
  id: string,
  reviewStatus: ShapeDefinition["review_status"],
  squares: ReadonlyArray<[piece: string, square: string]>,
  side: ShapeDefinition["side"] = "self",
): ShapeDefinition {
  return {
    id,
    name: `形${id}`,
    name_kana: "かた",
    side,
    family: "試験",
    parent_shape_id: null,
    required_pieces: squares.map(([piece, square]) => ({ piece, square, optional: false })),
    characteristics: "試験のための形です。",
    confidence_level: "medium",
    review_status: reviewStatus,
  };
}

/** completed(欠け 0)になる形。証拠 2 件・動くべき駒 2 枚なので、R6 でも落ちず R4(named)に届く。 */
const T1_COMPLETED = shape("t1_completed", "human_reviewed", [["金", "6h"], ["金", "4h"]]);
/** forming・証拠 2 件・欠け 2 件 → R5 で hedged(matchScore 0.5)。draft なので注記が付く。 */
const T2_HEDGED = shape("t2_hedged", "draft", [["金", "6h"], ["金", "4h"], ["玉", "5h"], ["銀", "7h"]]);
/** forming・証拠 1 件・欠け 2 件 → R5 で名前を出さない(matchScore 1/3)。D'' の肝その 1。 */
const T3_NONE = shape("t3_none", "draft", [["金", "6h"], ["玉", "5h"], ["銀", "7h"]]);
/** forming・証拠 1 件・欠け 1 件 → R5' で hedged(matchScore 0.5)。D'' の肝その 2。 */
const T4_R5P = shape("t4_r5p", "draft", [["金", "6h"], ["玉", "5h"]]);
/** 相手側の形(初期配置のままなので相手視点では completed)。候補に入ってはいけない。 */
const T5_OPPONENT = shape("t5_opponent", "draft", [["金", "6a"], ["金", "4a"]], "opponent");
/** 何も一致しない形 → status none(R0)。**名前は出ないが候補には残る。** */
const T6_ZERO = shape("t6_zero", "draft", [["飛", "5e"], ["角", "5f"]]);

const ALL_TEST_SHAPES = [T1_COMPLETED, T2_HEDGED, T3_NONE, T4_R5P, T5_OPPONENT, T6_ZERO];

function run(shapes: ShapeDefinition[] = ALL_TEST_SHAPES): ShapeCandidatesResult {
  return findShapeCandidates(
    { kifuId: "t", displayPly: POSITION_PLY, sfen: POSITION_SFEN, moves: [...POSITION_MOVES] },
    { shapes },
  );
}

function candidate(result: ShapeCandidatesResult, shapeId: string) {
  const found = result.candidates.find((c) => c.shapeId === shapeId);
  if (found === undefined) throw new Error(`候補に ${shapeId} がありません`);
  return found;
}

// ---------------------------------------------------------------------------

describe("findShapeCandidates", () => {
  it("1. 候補が 0 件なら figure: false・candidates: [](0 個は正常な出口)", () => {
    const result = run([]);
    expect(result.figure).toBe(false);
    expect(result.candidates).toStrictEqual([]);
    // 0 件でも注は全部入る。
    expect(result.notes).toStrictEqual([...FIG2A_NOTES]);
  });

  it("2. 名前が出ない候補も捨てない(証拠 1 件・欠け 2 件 → 名前は出ないが候補には残る)", () => {
    const result = run();
    const t3 = candidate(result, "t3_none");
    expect(t3.label).toStrictEqual({ level: "none", text: null });
    expect(t3.exposureRule).toBe("R5");
    expect(t3.status).toBe("forming");
    expect(t3.evidence).toStrictEqual({ evidenceCount: 1, missingCount: 2, requiredCount: 3, movedRequiredCount: 3 });
    // status が none(何も一致していない)の形も候補に残る ― 序盤で図が空にならないため(§8.2)。
    const t6 = candidate(result, "t6_zero");
    expect(t6.status).toBe("none");
    expect(t6.exposureRule).toBe("R0");
    expect(t6.label.level).toBe("none");
    expect(t6.matchScore).toBe(0);
  });

  it("3. hedged は「〜のような形」で、下書きには注記が付く", () => {
    const t2 = candidate(run(), "t2_hedged");
    expect(t2.label).toStrictEqual({ level: "hedged", text: "形t2_hedgedのような形" });
    expect(t2.exposureRule).toBe("R5");
    expect(t2.pendingNote).toBe("内容を確認中の形");
    expect(t2.evidence).toStrictEqual({ evidenceCount: 2, missingCount: 2, requiredCount: 4, movedRequiredCount: 4 });
  });

  it("4. R5'(証拠 1 件・欠け 1 件)で hedged になる(D'' の hedgeOneEvidenceIfMissingLe1)", () => {
    const t4 = candidate(run(), "t4_r5p");
    expect(t4.exposureRule).toBe("R5p");
    expect(t4.label).toStrictEqual({ level: "hedged", text: "形t4_r5pのような形" });
    expect(t4.evidence).toStrictEqual({ evidenceCount: 1, missingCount: 1, requiredCount: 2, movedRequiredCount: 2 });
  });

  it("5. named は構造上返らない(completed になる形を含む局面でも、その形は候補に入らない)", () => {
    const result = run();
    // 前提の校正: T1 は確かに completed になる形で、reviewed・証拠 2 件・動くべき駒 2 枚 =
    // 露出の規則だけなら R4(named)に届く。それでも候補に入らない。
    expect(result.candidates.map((c) => c.shapeId)).not.toContain("t1_completed");
    expect(result.candidates.map((c) => c.status)).not.toContain("completed");
    expect(result.candidates.map((c) => c.label.level)).not.toContain("named");
    expect(result.internal.exposureCounts.named).toBe(0);
    expect(result.internal.countsByRule.R4).toBe(0);
  });

  it("5b. named は「どんな入力でも」返らない(候補になりうる全ての形を総当たりしても 0 件)", () => {
    // 合成の形を 1 件ずつ単独で渡しても、組で渡しても named は出ない。
    for (const one of ALL_TEST_SHAPES) {
      expect(run([one]).candidates.map((c) => c.label.level)).not.toContain("named");
    }
    // 開始局面を渡す経路(回した局)でも同じ。
    const mirrored = findShapeCandidates(
      { kifuId: "t", displayPly: MIRRORED_PLY, sfen: MIRRORED_SFEN, moves: [...POSITION_MOVES], initialSfen: MIRRORED_START_SFEN },
      { shapes: ALL_TEST_SHAPES },
    );
    expect(mirrored.candidates.map((c) => c.label.level)).not.toContain("named");
    expect(mirrored.internal.exposureCounts.named).toBe(0);
  });

  it("6. 並びは matchScore 降順 → shapeId 昇順で決定的(同じ入力で 2 回呼んで同一)", () => {
    const first = run();
    const second = run();
    expect(first.candidates.map((c) => c.shapeId)).toStrictEqual(["t2_hedged", "t4_r5p", "t3_none", "t6_zero"]);
    expect(first.candidates.map((c) => c.rank)).toStrictEqual([1, 2, 3, 4]);
    // t2 と t4 は matchScore が同じ 0.5 で、shapeId 昇順で決まっている(同点のタイブレーク)。
    expect(candidate(first, "t2_hedged").matchScore).toBe(candidate(first, "t4_r5p").matchScore);
    expect(JSON.stringify(second)).toBe(JSON.stringify(first));
  });

  it("7. notes に 3 つの注が必ず入る(狙いで絞っていない・経路を見ていない・下書きを含めた)", () => {
    const result = run();
    expect(result.notes).toHaveLength(3);
    expect(result.notes).toStrictEqual([
      "狙い(⑤)で絞っていません。目的で選んだ結果ではありません。",
      "経路の判定をしていません。そこへ行く手順があるかは見ていません。",
      "未レビューの下書き 80 件を含む 82 形から探しました。下書きの名前は断定せず、最大でも「〜のような形」までにとどめます。",
    ]);
  });

  it("8. 切り出しが合わないときは例外が伝わる(黙って別の局面を評価しない)", () => {
    // displayPly が 1 つずれると、再生結果が sfen と一致しないので判定側が例外を投げる。
    expect(() =>
      findShapeCandidates(
        { kifuId: "t", displayPly: POSITION_PLY - 1, sfen: POSITION_SFEN, moves: [...POSITION_MOVES] },
        { shapes: ALL_TEST_SHAPES },
      ),
    ).toThrow(/再生結果が一致しません/);
    // 手数が範囲の外(手より先の ply)なら、切り出しの段で止まる。
    expect(() =>
      findShapeCandidates(
        { kifuId: "t", displayPly: 99, sfen: POSITION_SFEN, moves: [...POSITION_MOVES] },
        { shapes: ALL_TEST_SHAPES },
      ),
    ).toThrow(ShapeCandidatesError);
    // 開始局面の手数欄が読めないものも止める。
    expect(() =>
      findShapeCandidates(
        { kifuId: "t", displayPly: 5, sfen: POSITION_SFEN, moves: [...POSITION_MOVES], initialSfen: "lnsgkgsnl b -" },
        { shapes: ALL_TEST_SHAPES },
      ),
    ).toThrow(ShapeCandidatesError);
  });

  it("9. internal に customerVisible: false の印が付く(顧客版に出さない欄)", () => {
    const result = run();
    expect(result.internal.customerVisible).toBe(false);
    expect(result.internal.exposureCounts).toStrictEqual({ named: 0, hedged: 2, none: 2 });
    expect(result.internal.countsByRule).toStrictEqual({ R0: 1, R1: 0, R2: 0, R3: 0, R4: 0, R5: 2, R5p: 1, R6: 0 });
  });

  it("10. 開始局面を渡すと displayPly -(開始局面の SFEN の手数欄)で切る(計画 §8.6 の (B))", () => {
    // 回した局の開始局面(手数欄 2)から 4 手 → displayPly 6。平手の式(displayPly - 1)では合わない。
    const result = findShapeCandidates(
      { kifuId: "t", displayPly: MIRRORED_PLY, sfen: MIRRORED_SFEN, moves: [...POSITION_MOVES], initialSfen: MIRRORED_START_SFEN },
      { shapes: ALL_TEST_SHAPES },
    );
    expect(result.figure).toBe(true);
    expect(result.candidates.map((c) => c.shapeId)).toStrictEqual(["t2_hedged", "t4_r5p", "t3_none", "t6_zero"]);
    // 開始局面を渡さないと(= 平手として読むと)同じ局面には行けない。
    expect(() =>
      findShapeCandidates(
        { kifuId: "t", displayPly: MIRRORED_PLY, sfen: MIRRORED_SFEN, moves: [...POSITION_MOVES] },
        { shapes: ALL_TEST_SHAPES },
      ),
    ).toThrow();
  });

  it("11. side: opponent の形は候補に入らない(相手側の完成形も出ない)", () => {
    const result = run();
    expect(result.candidates.map((c) => c.shapeId)).not.toContain("t5_opponent");
    // 相手側の形だけを渡せば候補は 0 件になる(= 図を出さない)。
    const onlyOpponent = run([T5_OPPONENT]);
    expect(onlyOpponent.figure).toBe(false);
    expect(onlyOpponent.candidates).toStrictEqual([]);
  });
});

describe("駒数の検査(2026-09-26 に追加)", () => {
  it("14. 駒数が平手の総数と合わない sfen は例外(正しい sfen は通る)", () => {
    // 期待する表は平手から引いたもの。玉 2・飛 2・角 2・金 4・銀 4・桂 4・香 4・歩 18。
    expect(
      Object.fromEntries([...STANDARD_PIECE_COUNTS.entries()].sort(([a], [b]) => a.localeCompare(b))),
    ).toStrictEqual({ bishop: 2, gold: 4, king: 2, knight: 4, lance: 4, pawn: 18, rook: 2, silver: 4 });

    // 正しい局面は通る(この試験の校正)。
    expect(() => run()).not.toThrow();

    // 歩を 1 枚抜いた局面(9c の歩を消した)。**`parseSfen` はこれを通してしまう**ので、この検査が要る。
    const missingPawn = "lnsgkgsnl/1r5b1/1ppppppp1/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
    expect(() =>
      findShapeCandidates({ kifuId: "t", displayPly: 1, sfen: missingPawn, moves: [] }, { shapes: ALL_TEST_SHAPES }),
    ).toThrow(ShapeCandidatesError);
    expect(() =>
      findShapeCandidates({ kifuId: "t", displayPly: 1, sfen: missingPawn, moves: [] }, { shapes: ALL_TEST_SHAPES }),
    ).toThrow(/駒数が平手の総数と合いません/);

    // 持ち駒で歩を 2 枚増やした局面も止まる(持ち駒を数に含めていることの確認)。
    const extraPawns = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b 2P 1";
    expect(() =>
      findShapeCandidates({ kifuId: "t", displayPly: 1, sfen: extraPawns, moves: [] }, { shapes: ALL_TEST_SHAPES }),
    ).toThrow(/pawn: 20/);
  });

  it("14b. 成駒と持ち駒を含めて数える(取って打ち直した結果、片方に角が 2 枚ある局面は通る)", () => {
    // 司令塔が「成立しない」と止めた型の局面(先手の盤上に角 2 枚。片方は成った角)。
    // 相手の角を取って打ち直した結果で、**駒の総数は合っている**ので通らなければならない。
    const twoBishops = "lnsg1gsnl/9/ppp1k1+B1p/7p1/3Rp1p2/1PP2B1P1/P1SPPPP1P/5R3/LN1GKGSNL b 2P 27";
    // 駒数の検査は切り出しより先に走るので、**切り出しの例外が出た = 駒数の検査は通った**ということ。
    expect(() =>
      findShapeCandidates({ kifuId: "t", displayPly: 27, sfen: twoBishops, moves: [] }, { shapes: ALL_TEST_SHAPES }),
    ).toThrow(/切り出す手数が範囲の外です/);
    expect(() =>
      findShapeCandidates({ kifuId: "t", displayPly: 27, sfen: twoBishops, moves: [] }, { shapes: ALL_TEST_SHAPES }),
    ).not.toThrow(/駒数が平手の総数と合いません/);
  });
});

describe("露出の値と形の件数", () => {
  it("12. FIG2A_EXPOSURE_VALUES は EXPOSURE_VALUE_SETS[\"D''\"] と同値(5 つの値を明示して照合する)", () => {
    expect(FIG2A_EXPOSURE_VALUES).toStrictEqual({
      minRequiredForName: 1,
      minEvidenceForHedged: 2,
      hideCompletedWithoutEvidence: true,
      hedgeOneEvidenceIfMissingLe1: true,
      minEvidenceForCompleted: "movedRequired",
    });
    // 測る側の組が変わったら気づけるようにする(import 先の一覧が動いたら落ちる)。
    expect(FIG2A_EXPOSURE_VALUES).toStrictEqual(EXPOSURE_VALUE_SETS["D''"]);
  });

  it("13. loadAllShapes は 82 形(未レビューの下書き 80・レビュー済み 2)を返す ― 注 3 の数の校正。**この 1 本だけ data/ を読む**", () => {
    const shapes = loadAllShapes();
    const draft = shapes.filter((s) => s.review_status === "draft" || s.review_status === "expired");
    const reviewed = shapes.filter((s) => s.review_status === "human_reviewed" || s.review_status === "expert_verified");
    expect(shapes).toHaveLength(82);
    expect(draft).toHaveLength(80);
    expect(reviewed).toHaveLength(2);
    // id 昇順で決定的。
    expect(shapes.map((s) => s.id)).toStrictEqual([...shapes.map((s) => s.id)].sort((a, b) => a.localeCompare(b)));
    // 注 3 の文に出る数が、上で数えた数と合っていること。
    expect(FIG2A_NOTES[2]).toContain(`下書き ${draft.length} 件を含む ${shapes.length} 形`);
  });
});
