import { describe, expect, it, vi } from "vitest";
import { checkCandidateMovesSafety, type SafetyCheckEngine } from "./candidateMoveSafetyCheck.js";
import type { MultiPvGoResult } from "../engine/usiEngine.js";
import { planPathToShape, type PathPlanCandidateMove } from "./pathPlanner.js";
import { analyzeShapeFormation } from "./shapeFormationAnalyzer.js";
import { DEFAULT_INITIAL_SFEN } from "./moveHistory.js";
import { IllegalMoveError } from "../rules/applyMove.js";

const INITIAL_SFEN = DEFAULT_INITIAL_SFEN;

function multiPvResult(lines: MultiPvGoResult["lines"], bestmove = "7g7f"): MultiPvGoResult {
  return { bestmove, ponder: undefined, lines, infoLines: [] };
}

/** テスト用のモックエンジン。position()呼び出し順に対応するgoMultiPv結果をキューから返す。 */
function makeMockEngine(responses: MultiPvGoResult[]): SafetyCheckEngine & { positions: string[] } {
  const positions: string[] = [];
  let call = 0;
  return {
    positions,
    position: vi.fn((sfen: string) => {
      positions.push(sfen);
    }),
    setMultiPv: vi.fn(),
    goMultiPv: vi.fn(async () => {
      const result = responses[call];
      call += 1;
      if (!result) throw new Error("モックエンジンへの想定外の呼び出し(レスポンス不足)");
      return result;
    }),
  };
}

describe("checkCandidateMovesSafety", () => {
  it("baseline局面と各候補手の遷移後局面を、それぞれエンジンに解析させて対応付ける", async () => {
    const candidateMoves: PathPlanCandidateMove[] = [{ moveUsi: "7g7f" }, { moveUsi: "2g2f" }];
    const engine = makeMockEngine([
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 20 }, pv: ["3c3d"], lowerbound: false, upperbound: false }]),
      multiPvResult([{ multipv: 1, score: { type: "cp", value: -400 }, pv: ["8c8d"], lowerbound: false, upperbound: false }]),
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 15 }, pv: ["3c3d"], lowerbound: false, upperbound: false }]),
    ]);

    const result = await checkCandidateMovesSafety(INITIAL_SFEN, candidateMoves, engine);

    expect(result.baselineSfen).toBe(INITIAL_SFEN);
    expect(result.baselineMultiPv).toEqual([{ multipv: 1, score: { type: "cp", value: 20 }, pv: ["3c3d"], lowerbound: false, upperbound: false }]);
    expect(result.evaluations).toHaveLength(2);
    expect(result.evaluations[0]!.moveUsi).toBe("7g7f");
    expect(result.evaluations[0]!.multiPv).toEqual([{ multipv: 1, score: { type: "cp", value: -400 }, pv: ["8c8d"], lowerbound: false, upperbound: false }]);
    expect(result.evaluations[1]!.moveUsi).toBe("2g2f");
    expect(result.evaluations[0]!.resultingSfen).not.toBe(INITIAL_SFEN);
    expect(engine.positions).toEqual([
      INITIAL_SFEN,
      result.evaluations[0]!.resultingSfen,
      result.evaluations[1]!.resultingSfen,
    ]);
  });

  it("engineReferenceAvailableは正常終了時は常にtrueだが、これは安全判定ではないため除外・最善手決定は一切行わない", async () => {
    const candidateMoves: PathPlanCandidateMove[] = [{ moveUsi: "7g7f" }];
    // わざと「明らかに悪そうな」評価値(大きなマイナス)を返しても、結果からは除外されない
    // ことを確認する(このモジュールが閾値判定を一切行わないことの直接的な検証)。
    const engine = makeMockEngine([
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 0 }, pv: [], lowerbound: false, upperbound: false }]),
      multiPvResult([{ multipv: 1, score: { type: "mate", value: -1 }, pv: [], lowerbound: false, upperbound: false }]),
    ]);

    const result = await checkCandidateMovesSafety(INITIAL_SFEN, candidateMoves, engine);

    // engineReferenceAvailable: true は「参考評価を取得し対応付けできた」という
    // 機械的事実であり、「安全」を意味しない(ファイル冒頭コメント参照)。
    expect(result.engineReferenceAvailable).toBe(true);
    expect(result.evaluations).toHaveLength(1); // 除外されていない
  });

  it("multiPvオプションを指定した場合、事前にengine.setMultiPvを呼ぶ", async () => {
    const engine = makeMockEngine([multiPvResult([])]);
    await checkCandidateMovesSafety(INITIAL_SFEN, [], engine, { multiPv: 3 });
    expect(engine.setMultiPv).toHaveBeenCalledWith(3);
  });

  it("multiPvオプションを指定しない場合、engine.setMultiPvを呼ばない", async () => {
    const engine = makeMockEngine([multiPvResult([])]);
    await checkCandidateMovesSafety(INITIAL_SFEN, [], engine);
    expect(engine.setMultiPv).not.toHaveBeenCalled();
  });

  it("candidateMovesが空配列の場合、baselineのみ解析し安全にevaluations: []を返す", async () => {
    const engine = makeMockEngine([multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [], lowerbound: false, upperbound: false }])]);
    const result = await checkCandidateMovesSafety(INITIAL_SFEN, [], engine);

    expect(result.evaluations).toEqual([]);
    expect(result.baselineMultiPv).toEqual([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [], lowerbound: false, upperbound: false }]);
  });

  it("非合法な候補手が渡された場合、独自エラーに置き換えずIllegalMoveErrorを伝播する", async () => {
    const engine = makeMockEngine([multiPvResult([])]);
    await expect(
      checkCandidateMovesSafety(INITIAL_SFEN, [{ moveUsi: "1a1a" }], engine),
    ).rejects.toThrow(IllegalMoveError);
  });

  it("9. pathPlannerが返したcandidateMovesを、変換なしでそのまま入力として利用できる", async () => {
    const shapeResults = analyzeShapeFormation(DEFAULT_INITIAL_SFEN, []);
    const planResult = planPathToShape(DEFAULT_INITIAL_SFEN, shapeResults, "mino_takamino");
    // typical_build_orderの次のマス自体は動かせても、実際に合法手が0件になる場合があるため、
    // ここでは「型としてそのまま渡せること」自体を検証する(候補が0件でも呼び出しは成立する)。
    const engine = makeMockEngine(
      planResult.candidateMoves.length > 0
        ? [multiPvResult([]), ...planResult.candidateMoves.map(() => multiPvResult([]))]
        : [multiPvResult([])],
    );

    await expect(
      checkCandidateMovesSafety(DEFAULT_INITIAL_SFEN, planResult.candidateMoves, engine),
    ).resolves.toBeDefined();
  });

  it("10. 同一入力に対して常に同じ結果になる(決定的)", async () => {
    const candidateMoves: PathPlanCandidateMove[] = [{ moveUsi: "7g7f" }];
    const makeResponses = () => [
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 20 }, pv: [], lowerbound: false, upperbound: false }]),
      multiPvResult([{ multipv: 1, score: { type: "cp", value: -10 }, pv: [], lowerbound: false, upperbound: false }]),
    ];

    const resultA = await checkCandidateMovesSafety(INITIAL_SFEN, candidateMoves, makeMockEngine(makeResponses()));
    const resultB = await checkCandidateMovesSafety(INITIAL_SFEN, candidateMoves, makeMockEngine(makeResponses()));

    expect(resultA).toEqual(resultB);
  });
});
