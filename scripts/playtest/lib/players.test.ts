import { describe, expect, it } from "vitest";
import { makeSfen, parseSfen } from "shogiops/sfen";
import type { HighPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { Prng } from "./prng.js";
import {
  buildKifuJsonText,
  parseProfileOption,
  pickByEProfile,
  pickByRProfile,
  pickByS1Rule,
  pickByS2Rule,
  pickByS3Rule,
  pickMove,
  pickMoveWithTier,
  profileForGame,
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

// ---- STEP D3(docs/STEP_D3_PLAN_2026-09-14.md 4.1・8.1)。期待値は試験を回す前に手で書いた ----

/** 呼ばれたら落ちるエンジン。B・B2 と、S1 の規則②で決まる局面では呼ばれないはず。 */
function throwingEngine(): HighPriorityEngine {
  return {
    position: () => {
      throw new Error("エンジンを呼んだ");
    },
    go: async () => {
      throw new Error("エンジンを呼んだ");
    },
  };
}

const F_B6_SFEN = "8k/9/9/9/9/9/4G3P/9/4K4 b - 1";

describe("F-B13 parseProfileOption・profileForGame(--profile の選び方)", () => {
  it("--profile B なら 1〜12 局目がすべて B、B2 なら全部 B2", () => {
    for (let game = 1; game <= 12; game++) {
      expect(profileForGame(game, parseProfileOption(["--games", "12", "--profile", "B"]))).toBe("B");
      expect(profileForGame(game, parseProfileOption(["--profile", "B2", "--games", "12"]))).toBe("B2");
    }
  });

  it("無指定なら既定の10局構成を繰り返す(1 局目 S1・3 局目 S2・7 局目 E・10 局目 R・11 局目 S1)", () => {
    const profile = parseProfileOption(["--games", "12"]);
    expect(profile).toBeUndefined();
    expect(profileForGame(1, profile)).toBe("S1");
    expect(profileForGame(3, profile)).toBe("S2");
    expect(profileForGame(7, profile)).toBe("E");
    expect(profileForGame(10, profile)).toBe("R");
    expect(profileForGame(11, profile)).toBe("S1");
  });

  it("分からない値・値の無い --profile はエラーで止める(黙って既定の並びにしない)", () => {
    expect(() => parseProfileOption(["--profile", "X"])).toThrow(/--profile の値が分からない/);
    expect(() => parseProfileOption(["--games", "3", "--profile"])).toThrow(/--profile の値が分からない/);
  });
});

describe("F-B14 pickMoveWithTier(プロファイル → 決め方の振り分け)", () => {
  const context = () => ({ prng: new Prng(1), randomRate: 0.3, engine: throwingEngine(), s3: { cursor: 0 } });

  it("B は F-B6 の局面で 5g5h・5-iii、B2 は 1g1f・5-iv-b(エンジンを呼ばない)", async () => {
    expect(await pickMoveWithTier("B", F_B6_SFEN, baseResponse(F_B6_SFEN), context())).toEqual({ move: "5g5h", tier: "5-iii" });
    expect(await pickMoveWithTier("B2", F_B6_SFEN, baseResponse(F_B6_SFEN), context())).toEqual({ move: "1g1f", tier: "5-iv-b" });
  });

  it("S1 は既存の pickMove のまま(規則②で 3i3h)で、段を持たない", async () => {
    const response = baseResponse(INITIAL_SFEN, {
      candidateMoveState: "pending",
      candidateMove: undefined,
      candidateMoveLabels: { "3i3h": "銀を３八へ", "2h6h": "飛車を６八へ" },
    });
    expect(await pickMoveWithTier("S1", INITIAL_SFEN, response, context())).toEqual({ move: "3i3h", tier: null });
  });
});

describe("F-B14b pickMove は B・B2 を扱わない(計画 8.8 の A8)", () => {
  it("F-B14b pickMove に B・B2 を渡すと例外で止まる(振り分けは pickMoveWithTier の 1 か所だけ)", async () => {
    const context = { prng: new Prng(1), randomRate: 0.3, engine: throwingEngine(), s3: { cursor: 0 } };
    await expect(pickMove("B", F_B6_SFEN, baseResponse(F_B6_SFEN), context)).rejects.toThrow(/pickMoveWithTier を使う/);
    await expect(pickMove("B2", F_B6_SFEN, baseResponse(F_B6_SFEN), context)).rejects.toThrow(/pickMoveWithTier を使う/);
  });
});

describe("F-B15 buildKifuJsonText(棋譜 JSON の組み立て)", () => {
  it("B・B2 は tiers を持ち、欄の並びは id・source・profile・seed・moves・tiers", () => {
    const text = buildKifuJsonText({ id: "k1", profile: "B", seed: 3, moves: ["5g5h", "3c3d"], tiers: ["5-iii"] });
    expect(text.endsWith("}\n")).toBe(true);
    const parsed = JSON.parse(text);
    expect(parsed).toEqual({ id: "k1", source: "explore", profile: "B", seed: 3, moves: ["5g5h", "3c3d"], tiers: ["5-iii"] });
    expect(Object.keys(parsed)).toEqual(["id", "source", "profile", "seed", "moves", "tiers"]);
    expect(JSON.parse(buildKifuJsonText({ id: "k2", profile: "B2", seed: 4, moves: ["1g1f"], tiers: ["5-iv-b"] })).tiers).toEqual(["5-iv-b"]);
  });

  it("S1〜R は tiers の欄を持たない(既存の形のまま)", () => {
    const parsed = JSON.parse(buildKifuJsonText({ id: "k3", profile: "S1", seed: 2, moves: ["7g7f"], tiers: [null] }));
    expect(Object.keys(parsed)).toEqual(["id", "source", "profile", "seed", "moves"]);
  });
});
