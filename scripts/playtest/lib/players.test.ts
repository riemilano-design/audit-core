import { describe, expect, it } from "vitest";
import { makeSfen, parseSfen } from "shogiops/sfen";
import type { HighPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { Prng } from "./prng.js";
import {
  pickByEProfile,
  pickByRProfile,
  pickByS1Rule,
  pickByS2Rule,
  pickByS3Rule,
  pickMove,
} from "./players.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

function basePlan(): ReachablePlanBody {
  return {
    reachableShapes: [],
    routes: [],
    targetShapeProgress: null,
    candidateMoveLabels: {},
    lastMoveOutcome: null,
    nextConsiderations: [],
    candidateMoveState: "unavailable",
    // STEP 5-F(A-3): ③の背景解析の状態。この土台は③について何も言わないため
    // "pending"(まだ計算していない)を既定にする。
    focusTextState: "pending",
    candidateMove: undefined,
    pendingReviewNote: null,
    resolvedTargetShapeId: null,
    shapeWeakness: null,
    urgentMessages: [],
    referenceShapes: [],
    directionNote: null,
    planChanged: false,
    planChangeReason: null,
  };
}

function baseResponse(sfen: string, planOverrides: Partial<ReachablePlanBody> = {}): StateResponseBodyWithPlan {
  return {
    sfen,
    moveHistory: [],
    status: { isEnd: false, outcome: undefined },
    coach: undefined,
    legalMoves: [],
    // STEP 5-E(S-2): StateResponseBodyWithPlan に必須で足された欄。
    // 判定には使わないため、この土台では空配列にする。
    escapeSquareThreats: [],
    moveHistoryJapanese: [],
    plan: { ...basePlan(), ...planOverrides },
  };
}

describe("pickByS1Rule", () => {
  it("① candidateMove.status===readyならexplanations[0].moveを返す", () => {
    const response = baseResponse(INITIAL_SFEN, {
      candidateMoveState: "ready",
      candidateMove: {
        status: "ready",
        notReadyReason: null,
        explanations: [
          {
            id: "e1",
            stage: "candidate_move",
            purpose: "",
            move: "7g7f",
            reason: "",
            refers_to_shape_id: null,
            refers_to_intent_id: null,
            confidence_level: "low",
            glossary_terms: [],
            template_id: "t",
          },
        ],
        sharedNotes: [],
      },
      candidateMoveLabels: { "2h6h": "飛車を６八へ" },
    });

    expect(pickByS1Rule(response)).toBe("7g7f");
  });

  it("② readyでなくても、candidateMoveLabelsに手があれば最初のUSIを返す", () => {
    const response = baseResponse(INITIAL_SFEN, {
      candidateMoveState: "pending",
      candidateMove: undefined,
      candidateMoveLabels: { "3i3h": "銀を３八へ", "2h6h": "飛車を６八へ" },
    });

    expect(pickByS1Rule(response)).toBe("3i3h");
  });

  it("③ どちらも無ければundefinedを返す(呼び出し側で浅い読みへ)", () => {
    const response = baseResponse(INITIAL_SFEN, {
      candidateMoveState: "unavailable",
      candidateMove: undefined,
      candidateMoveLabels: {},
    });

    expect(pickByS1Rule(response)).toBeUndefined();
  });
});

describe("pickByS2Rule", () => {
  it("① 当たっている駒について、移動先に利きが無い手をgetLegalMovesの順で最初に選ぶ", () => {
    // 実戦局面(C局30手目・３六歩打の直後)。桂３七が歩３六から当たっており、
    // ３七二五への移動(3g2e)は利きが無く、３七四五(3g4e)には利きが残る
    // (apps/server/src/rules/attackedPieces.test.tsと同じ局面)。
    const sfen = "lnsgk2nl/4r2b1/pp1p2gpp/2p2s3/4p1P2/2PP1pp2/PP1SPPNPP/1B1RG1SK1/LN3G2L b - 31";
    const response = baseResponse(sfen, {
      urgentMessages: [{ kind: "piece_attacked", text: "桂が当たっています。" }],
    });

    expect(pickByS2Rule(sfen, response)).toBe("3g2e");
  });

  it("① 移動先すべてに利きが残る場合はundefinedを返す(呼び出し側でS1へ)", () => {
    // 自作の最小局面: 先手桂5eが後手香5aから当たっており、桂の合法な移動先
    // (4c・6c)はいずれも後手歩(4b・6b)の利きが残る。
    const sfen = "4l3k/3p1p3/9/9/4N4/9/9/9/8K b - 1";
    const response = baseResponse(sfen, {
      urgentMessages: [{ kind: "piece_attacked", text: "桂が当たっています。" }],
    });

    expect(pickByS2Rule(sfen, response)).toBeUndefined();
  });

  it("urgentMessagesにpiece_attackedが無ければundefinedを返す(呼び出し側でS1へ)", () => {
    const response = baseResponse(INITIAL_SFEN, { urgentMessages: [] });

    expect(pickByS2Rule(INITIAL_SFEN, response)).toBeUndefined();
  });
});

describe("pickByS3Rule", () => {
  it("cursor=0では定型列の先頭(7g7f)を返し、nextCursorを1にする", () => {
    const result = pickByS3Rule(INITIAL_SFEN, 0);
    expect(result).toEqual({ move: "7g7f", nextCursor: 1 });
  });

  it("非合法な手は消費せず読み飛ばし、次に合法な手を返す", () => {
    // 7g7f・3c3d の2手を指した後(先手番に戻る)、cursor=0の"7g7f"は既に非合法だが
    // "6g6f"はまだ合法。読み飛ばしてnextCursorを2にする。
    let sfen = applyMove(INITIAL_SFEN, "7g7f");
    sfen = applyMove(sfen, "3c3d");

    const result = pickByS3Rule(sfen, 0);
    expect(result).toEqual({ move: "6g6f", nextCursor: 2 });
  });

  it("末尾まで合法な手が無ければundefinedを返す(呼び出し側でS1へ)", () => {
    expect(pickByS3Rule(INITIAL_SFEN, 8)).toBeUndefined();
  });
});

/** テスト用の固定応手エンジン(実プロセスを起動しない)。 */
function fakeEngine(bestmove: string | undefined): HighPriorityEngine {
  return {
    position: () => {},
    go: async () => ({ bestmove, ponder: undefined, scoreCp: undefined, infoLines: [] }),
  };
}

describe("pickByEProfile", () => {
  it("bestmoveをそのまま返す", async () => {
    expect(await pickByEProfile(INITIAL_SFEN, fakeEngine("7g7f"))).toBe("7g7f");
  });

  it("bestmoveが無い/resign/winならundefinedを返す", async () => {
    expect(await pickByEProfile(INITIAL_SFEN, fakeEngine(undefined))).toBeUndefined();
    expect(await pickByEProfile(INITIAL_SFEN, fakeEngine("resign"))).toBeUndefined();
    expect(await pickByEProfile(INITIAL_SFEN, fakeEngine("win"))).toBeUndefined();
  });
});

describe("pickByRProfile(乱択混合)", () => {
  it("種を固定すると、乱択に落ちる手番/しない手番を含め毎回同じ結果を返す(決定性)", async () => {
    const run = () =>
      pickByRProfile(INITIAL_SFEN, new Prng(123), 0.3, fakeEngine("7g7f"));

    const a = await run();
    const b = await run();
    expect(a).toBe(b);
  });

  it("randomRate=1なら常にgetLegalMovesから選ぶ(エンジンを呼ばない)", async () => {
    let engineCalled = false;
    const engine: HighPriorityEngine = {
      position: () => {
        engineCalled = true;
      },
      go: async () => ({ bestmove: "7g7f", ponder: undefined, scoreCp: undefined, infoLines: [] }),
    };

    const move = await pickByRProfile(INITIAL_SFEN, new Prng(1), 1, engine);
    expect(move).toBeDefined();
    expect(engineCalled).toBe(false);
  });

  it("randomRate=0なら常にE(エンジン)へ委ねる", async () => {
    const move = await pickByRProfile(INITIAL_SFEN, new Prng(1), 0, fakeEngine("2g2f"));
    expect(move).toBe("2g2f");
  });
});

describe("pickMove(プロファイルの分岐)", () => {
  it("S1: ①②が無ければEへフォールバックする", async () => {
    const response = baseResponse(INITIAL_SFEN, {
      candidateMoveState: "unavailable",
      candidateMove: undefined,
      candidateMoveLabels: {},
    });
    const move = await pickMove("S1", INITIAL_SFEN, response, {
      prng: new Prng(1),
      randomRate: 0.3,
      engine: fakeEngine("9g9f"),
      s3: { cursor: 0 },
    });
    expect(move).toBe("9g9f");
  });

  it("S3: 定型列を使い切ったらS1経由でEへフォールバックする", async () => {
    const response = baseResponse(INITIAL_SFEN, {
      candidateMoveState: "unavailable",
      candidateMove: undefined,
      candidateMoveLabels: {},
    });
    const s3 = { cursor: 8 };
    const move = await pickMove("S3", INITIAL_SFEN, response, {
      prng: new Prng(1),
      randomRate: 0.3,
      engine: fakeEngine("1g1f"),
      s3,
    });
    expect(move).toBe("1g1f");
    expect(s3.cursor).toBe(8);
  });
});
