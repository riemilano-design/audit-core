// STEP D3-COND 計画 §5 の 5(§13 の選択肢 (a)。人間の承認 2026-09-17)。lib/conditions/ に置いた承認済みの条件式の定義を読み込み、形・文・固定例を確かめる。
// **エンジンは起動しない。記録は読まない。**
//
// 【正解の置き方】C-1 の固定例は定義の文(「実戦と読み筋を比べられた手数(最大 6 手)の後の逃げ道の数が、自分の手の前より少ない」)から手で書いた。組の行は lib/condition.test.ts と同じ形で手で書いた架空の値。
// 禁止語と label の照合は、D6 の出力の検査(lib/diagnosisReport.ts)と同じ normalizeForMatch でそろえる。
// 【この試験が確かめないこと】材料の側・試す側での件数(§11 の予測と gate.ts の実行)。判定と読み込みの骨組み(lib/condition.test.ts)。

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { judgeCondition, type ConditionView, type PairRow } from "./condition.js";
import { loadConditionsFromDir } from "./conditionReport.js";
import type { CounterfactualComparison, SequenceFacts } from "./counterfactual.js";
import type { MomentPairFields } from "./diagnosisMoment.js";
import { normalizeForMatch } from "./diagnosisReport.js";
import type { Evaluation, Trigger } from "./failureEvent.js";
import type { PositionFacts } from "./positionFacts.js";
import { FORBIDDEN_WORDS } from "./reportTemplates.js";

const CONDITIONS_DIR = fileURLToPath(new URL("./conditions/", import.meta.url));
const C1_ID = "king_escapes_decrease_v1";
const C1_FILE = fileURLToPath(new URL(`./conditions/${C1_ID}.ts`, import.meta.url));
/** 承認のときのファイルのバイト列の sha256(§11 の予測と結びつける値。定義を変えるときは v2 の別ファイルにする) */
const C1_SHA256 = "ec31899a5b67ae1d0e5642a40e623def04dd39374a197961e0e50f5511ae9e78";
const PROVISIONAL = "(仮)";

async function c1() {
  const found = (await loadConditionsFromDir(CONDITIONS_DIR)).find((entry) => entry.definition.id === C1_ID);
  if (found === undefined) throw new Error(`${C1_ID} が lib/conditions/ に無い`);
  return found;
}

// ---- 手で書いた組の行(lib/condition.test.ts と同じ形)----

const measured = (scoreCp: number): Evaluation => ({ state: "measured", scoreCp, mate: null, bestmove: "2g2f", afterPassScoreCp: 100, afterPassMate: null, dropCp: 50 });
const counts = (bySente: number, byGote: number) => ({ bySente, byGote });
const positionFacts = (): PositionFacts => ({
  zoneSquares: { ownKingZone: 6, opponentKingZone: 6 },
  zonePieces: { ownKingZone: counts(5, 0), opponentKingZone: counts(0, 5) },
  zoneControl: { ownKingZone: counts(4, 0), opponentKingZone: counts(0, 4) },
});
const sequence = (kingEscapes: number): SequenceFacts => ({
  capturedRoles: { us: {}, opponent: {} },
  checks: { byUs: [], byOpponent: [] },
  mate: null,
  gameEnd: null,
  kingSurroundingsEnd: { squares: 5, own: 3 },
  positionFactsEnd: positionFacts(),
  kingEscapesEnd: { state: "counted", count: kingEscapes },
});
/** 根の逃げ道 `root`・実戦の後 `actualEnd`・読み筋の後 3 */
const comparison = (root: number, actualEnd: number): CounterfactualComparison => ({
  state: "compared",
  comparedPlies: 6,
  windowPlies: 5,
  actualPlies: 6,
  pvLength: 8,
  pvUsablePlies: 8,
  pvTruncatedAtPly: null,
  pvBounded: { lowerbound: false, upperbound: false },
  pvFirstMove: "2g2f",
  pvFirstMoveIsBestmoveAtBefore: true,
  pvFirstMoveIsPlayedMove: false,
  kingEscapesRoot: { state: "counted", count: root },
  actual: sequence(actualEnd),
  pv: sequence(3),
  pvMinusActual: {
    capturedRoles: { us: {}, opponent: {} },
    kingSurroundingsOwn: 0,
    positionFacts: { zonePieces: { ownKingZone: counts(0, 0), opponentKingZone: counts(0, 0) }, zoneControl: { ownKingZone: counts(0, 0), opponentKingZone: counts(0, 0) } },
    kingEscapes: 3 - actualEnd,
  },
  kingEscapesChangeFromRoot: { actual: actualEnd - root, pv: 3 - root },
});
const trigger = (): Trigger => ({
  evaluationBefore: measured(500),
  opponentIntent: { classification: { column: "noCandidate" }, refersToIntentId: null },
  shape: { state: "recorded", status: "forming", refersToShapeId: null },
  focus: { state: "nothingToSay" },
  kingSurroundings: { squares: 5, own: 3 },
  positionFacts: positionFacts(),
});
function pairRow(root: number, actualEnd: number): PairRow {
  const fields: MomentPairFields = {
    branchPly: 11,
    fromReadyPly: 10,
    toReadyPly: 12,
    trigger: trigger(),
    moves: { userMove: "7g7f", opponentMove: "3c3d" },
    userBestmoveAtBefore: "2g2f",
    opponentBestmove: { state: "notInRecord" },
    evaluationAfter: measured(0),
    standingPair: { before: "ahead", after: "level" },
    failureEventBranchPly: null,
    consequences: { checks: [], mate: null, windowPlies: 5, windowShort: false },
    counterfactual: comparison(root, actualEnd),
  };
  return { kifuId: "k", pairKind: "compared", ...fields };
}

describe("lib/conditions/ の承認済みの定義(D3-COND 計画 §5 の 5・§13)", () => {
  it("(a) lib/conditions/ の定義はすべてエラーなく読め、id が重複しない。今あるのは C-1 の 1 本", async () => {
    const ids = (await loadConditionsFromDir(CONDITIONS_DIR)).map((entry) => entry.definition.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids).toStrictEqual([C1_ID]);
  });

  it("(a) C-1 のファイルは承認したバイト列のまま(definitionSha256 = 読み込んだファイルの sha256 = 承認のときの値)", async () => {
    const { definitionSha256, definition } = await c1();
    expect([definitionSha256, createHash("sha256").update(readFileSync(C1_FILE)).digest("hex"), definition.status]).toStrictEqual([C1_SHA256, C1_SHA256, "approved"]);
  });

  it("(b) approved の定義は approval があり、readableText が空でなく「(仮)」を含まない", async () => {
    const approved = (await loadConditionsFromDir(CONDITIONS_DIR)).filter((entry) => entry.definition.status === "approved");
    expect(approved.map((entry) => entry.definition.id)).toContain(C1_ID);
    for (const { definition } of approved) {
      expect(definition.approval, definition.id).not.toBeNull();
      expect(typeof definition.readableText === "string" && definition.readableText.length > 0, definition.id).toBe(true);
      expect(definition.readableText!.includes(PROVISIONAL), definition.id).toBe(false);
    }
  });

  it("(c) readableText に禁止語(reportTemplates の FORBIDDEN_WORDS)と label の語(「(仮)」を除いた語も)を含まない。照合は normalizeForMatch でそろえる", async () => {
    const hitsOf = (text: string, label: string) =>
      [...FORBIDDEN_WORDS, label, label.split(PROVISIONAL).join("")].filter((word) => word.length > 0 && normalizeForMatch(text).includes(normalizeForMatch(word)));
    // 照合そのものが働くこと(空白で割った禁止語・label の語を捕まえる)
    expect(hitsOf("弱 点を見ます。逃げ道 が減る", "逃げ道が減る(仮)")).toStrictEqual(["弱点", "逃げ道が減る"]);
    for (const { definition } of await loadConditionsFromDir(CONDITIONS_DIR)) {
      if (definition.readableText === undefined) continue;
      expect(hitsOf(definition.readableText, definition.label), definition.id).toStrictEqual([]);
    }
  });

  it("(d) C-1 の evaluate: 根 5・後 4 → 真 / 根 4・後 4 → 偽 / 根 3・後 5 → 偽", async () => {
    const { definition } = await c1();
    const view = (root: number, actualEnd: number): ConditionView => ({ counterfactual: { kingEscapesRoot: { count: root }, actual: { kingEscapesEnd: { count: actualEnd } } } });
    expect([definition.evaluate(view(5, 4)), definition.evaluate(view(4, 4)), definition.evaluate(view(3, 5))]).toStrictEqual([true, false, false]);
  });

  it("(e) C-1 を全ての手の組の行に当てる: 根の逃げ道が noKing → 判定不能(門の実際の値)/ 根 2・後 1 → 該当(読んだのは uses の 2 つだけ)", async () => {
    const { definition } = await c1();
    const noKing = pairRow(2, 1);
    (noKing.counterfactual as CounterfactualComparison).kingEscapesRoot = { state: "noKing" };
    expect(judgeCondition(definition, { kind: "pair", row: noKing })).toStrictEqual({
      state: "undecidable",
      missing: [{ path: "counterfactual.kingEscapesRoot.count", reason: { kind: "gate", gatePath: "counterfactual.kingEscapesRoot.state", actual: "noKing" } }],
    });
    expect(judgeCondition(definition, { kind: "pair", row: pairRow(2, 1) })).toStrictEqual({
      state: "match",
      usedValues: { counterfactual: { kingEscapesRoot: { count: 2 }, actual: { kingEscapesEnd: { count: 1 } } } },
    });
  });
});
