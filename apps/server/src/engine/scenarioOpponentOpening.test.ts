import { describe, expect, it } from "vitest";
import { isLegalMove } from "../rules/legalMoves.js";
import { applyMove } from "../rules/applyMove.js";
import { DEFAULT_INITIAL_SFEN } from "../analysis/moveHistory.js";
import { detectIntents } from "../analysis/intentDetector.js";
import { isScenarioId, pickScenarioMove, type ScenarioId } from "./scenarioOpponentOpening.js";

// gameSession.playOpponentMove相当の最小再現(人間側の手は無関係の合法手で埋める)。
// 実際のgameSession/applyMoveをそのまま使い、指し手選択(pickScenarioMove)以外の
// ロジックを重複実装しないことを確認する。
const SENTE_FILLERS = ["1g1f", "2g2f", "3g3f", "4g4f", "5g5f", "6g6f", "9g9f", "8g8f"];

function playScenarioToCompletion(scenario: ScenarioId) {
  let sfen = DEFAULT_INITIAL_SFEN;
  const moveHistory: string[] = [];
  let stepIndex = 0;
  const intentSnapshots: { moveHistoryLength: number; matchStatus: string; matchScore: number }[] = [];

  // 十分な回数だけ「人間の適当な一手 -> シナリオの一手」を繰り返す。
  for (let i = 0; i < SENTE_FILLERS.length; i++) {
    const senteMove = SENTE_FILLERS[i]!;
    expect(isLegalMove(sfen, senteMove)).toBe(true);
    sfen = applyMove(sfen, senteMove);
    moveHistory.push(senteMove);

    const scenarioMove = pickScenarioMove(sfen, stepIndex, scenario);
    if (!scenarioMove) break; // シナリオが尽きた

    expect(isLegalMove(sfen, scenarioMove)).toBe(true);
    sfen = applyMove(sfen, scenarioMove);
    moveHistory.push(scenarioMove);
    stepIndex += 1;

    const [intentResult] = detectIntents(sfen, moveHistory).filter((r) => r.intentId === scenario);
    intentSnapshots.push({
      moveHistoryLength: moveHistory.length,
      matchStatus: intentResult!.matchStatus,
      matchScore: intentResult!.matchScore,
    });
  }

  return { sfen, moveHistory, intentSnapshots };
}

describe("isScenarioId", () => {
  it("既知のシナリオidのみを受け入れる", () => {
    expect(isScenarioId("boh_gin")).toBe(true);
    expect(isScenarioId("hayajikake")).toBe(true);
    expect(isScenarioId("funa_gakoi")).toBe(false);
    expect(isScenarioId(null)).toBe(false);
    expect(isScenarioId(undefined)).toBe(false);
  });
});

describe("pickScenarioMove", () => {
  it("棒銀シナリオの各指し手はすべて、指された時点の局面で合法である", () => {
    const { intentSnapshots } = playScenarioToCompletion("boh_gin");
    expect(intentSnapshots.length).toBeGreaterThan(0);
  });

  it("早仕掛けシナリオの各指し手はすべて、指された時点の局面で合法である", () => {
    const { intentSnapshots } = playScenarioToCompletion("hayajikake");
    expect(intentSnapshots.length).toBeGreaterThan(0);
  });

  it("棒銀シナリオを進めると、Intent判定がnone→forming→matchedと遷移する", () => {
    const { intentSnapshots } = playScenarioToCompletion("boh_gin");
    const statuses = intentSnapshots.map((s) => s.matchStatus);

    // 最初は(まだ何も一致していないので)none、最後はmatchedになっているはず。
    expect(statuses[0]).not.toBe("matched");
    expect(statuses.at(-1)).toBe("matched");
    // 途中でformingを経由していること(いきなりmatchedにならないこと)。
    expect(statuses).toContain("forming");

    // matchScoreが単調に増加(少なくとも減少はしない)していること。
    for (let i = 1; i < intentSnapshots.length; i++) {
      expect(intentSnapshots[i]!.matchScore).toBeGreaterThanOrEqual(intentSnapshots[i - 1]!.matchScore);
    }
  });

  it("早仕掛けシナリオを進めると、Intent判定がforming→matchedと遷移する", () => {
    const { intentSnapshots } = playScenarioToCompletion("hayajikake");
    const statuses = intentSnapshots.map((s) => s.matchStatus);

    expect(statuses[0]).toBe("forming");
    expect(statuses.at(-1)).toBe("matched");
  });

  it("シナリオの手を使い切るとundefinedを返す(通常のエンジンへフォールバックできる)", () => {
    // hayajikakeは2手しかないため、2手目以降はundefinedになるはず。
    let sfen = DEFAULT_INITIAL_SFEN;
    sfen = applyMove(sfen, "1g1f");
    const move0 = pickScenarioMove(sfen, 0, "hayajikake")!;
    sfen = applyMove(sfen, move0);
    sfen = applyMove(sfen, "2g2f");
    const move1 = pickScenarioMove(sfen, 1, "hayajikake")!;
    sfen = applyMove(sfen, move1);
    sfen = applyMove(sfen, "3g3f");

    expect(pickScenarioMove(sfen, 2, "hayajikake")).toBeUndefined();
  });

  it("人間の手でシナリオの想定局面が崩れ、次の手が非合法になった場合はundefinedを返す", () => {
    // hayajikakeの2手目(6d6e)は、6dに歩が既に無ければ非合法になる。
    // ここでは1手目を適用せずに2手目のstepIndexを渡すことで、その状況を再現する。
    expect(pickScenarioMove(DEFAULT_INITIAL_SFEN, 1, "hayajikake")).toBeUndefined();
  });
});
