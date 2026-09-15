// STEP D3-COND の骨組み(docs/STEP_D3-COND_PLAN_2026-09-15.md §7 の K-1〜K-10)と、D4 計画 §3 の改訂(docs/STEP_D4_PLAN_2026-09-15.md §8 の K-12〜K-14)。
// 監査 C の GO の条件 C-1(appliesTo が 2 種類以上の定義)・C-2(表の null の意味と門の一覧)も足した(計画 §12.5)。
// **エンジンは起動しない。**
//
// 【正解の置き方】行は型どおりに手で書いた架空の値(記録から写さない)。定義は試験だけの架空の定義 `test_only_*` で、将棋の判断を含めない。
// 期待は計画書の表と、この行から手で数えた値(実装の出力から写さない)。
// 【この試験が確かめないこと】全ての手の組を作る関数 allPairsOf(K-11)・Gate(D4 本体)。出力の契約 diagnosis-condition v0.1 と diagnose.ts の口(D-SCREEN-2 の後)。

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  checkCondition,
  CONDITION_ROW_KINDS,
  ConditionLoadError,
  conditionTallyOf,
  judgeCondition,
  judgeConditionPvSide,
  loadCondition,
  lostByEndingOf,
  READABLE_FIELDS,
  testSideTallyOf,
  userSideOf,
  type ConditionDefinition,
  type ConditionGameInput,
  type ConditionInput,
  type ConditionLoadProblem,
  type ConditionRowKind,
  type ConditionView,
  type LoadedCondition,
  type PairRow,
} from "./condition.js";
import type { CounterfactualComparison, SequenceFacts } from "./counterfactual.js";
import type { MaxDropMoment, MomentPairFields, RiseMoment } from "./diagnosisMoment.js";
import type { BranchKind, Evaluation, FailureEvent, Trigger } from "./failureEvent.js";
import type { PositionFacts } from "./positionFacts.js";

// ---- 手で書いた行 ----

const measured = (scoreCp: number | null, mate: number | null = null): Evaluation => ({
  state: "measured",
  scoreCp,
  mate,
  bestmove: "2g2f",
  afterPassScoreCp: 100,
  afterPassMate: null,
  dropCp: 50,
});
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
/** 実戦の逃げ道 1・読み筋の逃げ道 3・根 2 */
const comparison = (): CounterfactualComparison => ({
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
  kingEscapesRoot: { state: "counted", count: 2 },
  actual: sequence(1),
  pv: sequence(3),
  pvMinusActual: {
    capturedRoles: { us: {}, opponent: {} },
    kingSurroundingsOwn: 0,
    positionFacts: { zonePieces: { ownKingZone: counts(0, 0), opponentKingZone: counts(0, 0) }, zoneControl: { ownKingZone: counts(0, 0), opponentKingZone: counts(0, 0) } },
    kingEscapes: 2,
  },
  kingEscapesChangeFromRoot: { actual: -1, pv: 1 },
});
/** 直前の評価 +500 */
const trigger = (): Trigger => ({
  evaluationBefore: measured(500),
  opponentIntent: { classification: { column: "noCandidate" }, refersToIntentId: null },
  shape: { state: "recorded", status: "forming", refersToShapeId: null },
  focus: { state: "nothingToSay" },
  kingSurroundings: { squares: 5, own: 3 },
  positionFacts: positionFacts(),
});
const consequences = () => ({ checks: [] as number[], mate: null as number | null, windowPlies: 5, windowShort: false });

function event(kifuId: string, branchPly: number, kinds: BranchKind[] = ["cpDrop"]): FailureEvent {
  return {
    kifuId,
    branchPly,
    fromReadyPly: branchPly - 1,
    toReadyPly: branchPly + 1,
    trigger: trigger(),
    action: { playedMove: "7g7f", bestmoveAtBefore: "2g2f" },
    branch: { kinds, diffCp: -500, mateAfter: null, matedIfPassAfter: false, evaluationAfter: measured(0), standingPair: { before: "ahead", after: "level" } },
    consequences: consequences(),
    counterfactual: comparison(),
    candidateModes: [],
  };
}
function pairFields(branchPly: number): MomentPairFields {
  return {
    branchPly,
    fromReadyPly: branchPly - 1,
    toReadyPly: branchPly + 1,
    trigger: trigger(),
    moves: { userMove: "7g7f", opponentMove: "3c3d" },
    userBestmoveAtBefore: "2g2f",
    opponentBestmove: { state: "notInRecord" },
    evaluationAfter: measured(0),
    standingPair: { before: "ahead", after: "level" },
    failureEventBranchPly: null,
    consequences: consequences(),
    counterfactual: comparison(),
  };
}
const EXCLUDED = { mateDrop: 0, mateRise: 0, notCompared: 0 };
const rise = (kifuId: string, branchPly: number): RiseMoment => ({ eventClass: "rise", kifuId, ...pairFields(branchPly), change: { kind: "cp", diffCp: 500 } });
const maxDropPair = (kifuId: string, branchPly: number): MaxDropMoment => ({ eventClass: "maxDrop", kifuId, ...pairFields(branchPly), change: { kind: "cp", diffCp: -200 }, excludedPairs: EXCLUDED });
const maxDropState = (kifuId: string): MaxDropMoment => ({ eventClass: "maxDrop", kifuId, state: "noDrop", minDiffCp: 10, excludedPairs: EXCLUDED });
const pairRow = (kifuId: string, branchPly: number): PairRow => ({ kifuId, pairKind: "compared", ...pairFields(branchPly) });

function inputOf(kind: ConditionRowKind): ConditionInput {
  switch (kind) {
    case "failureEvent":
      return { kind, row: event("k", 11) };
    case "rise":
      return { kind, row: rise("k", 11) };
    case "maxDropPair":
      return { kind: "maxDrop", row: maxDropPair("k", 11) };
    case "pair":
      return { kind, row: pairRow("k", 11) };
  }
}

// ---- 試験だけの架空の定義 ----

const definition = (patch: Partial<ConditionDefinition> = {}): ConditionDefinition => ({
  id: "test_only_a",
  label: "試験だけの定義(仮)",
  status: "draft",
  definitionText: "試験だけ",
  uses: [],
  thresholds: {},
  appliesTo: ["failureEvent"],
  approval: null,
  evaluate: () => true,
  ...patch,
});
const loaded = (d: ConditionDefinition): LoadedCondition => checkCondition(d, new TextEncoder().encode(d.id));
/** view のパスを辿る(無ければ undefined) */
const at = (view: ConditionView, path: string): unknown => path.split(".").reduce<unknown>((current, key) => (current as Record<string, unknown> | undefined)?.[key], view);
const problemsOf = (d: unknown, bytes = new Uint8Array([0])): readonly ConditionLoadProblem[] => {
  try {
    checkCondition(d, bytes);
    return [];
  } catch (error) {
    if (error instanceof ConditionLoadError) return error.problems;
    throw error;
  }
};

describe("READABLE_FIELDS(計画 §2 の表・D4 §3 の種類の列)", () => {
  it("表の各行は、持つ行の種類の列に書いた種類の行でだけ読める(ほかの種類の行ではパスが無い)", () => {
    const readableKinds = Object.fromEntries(
      READABLE_FIELDS.map((entry) => [
        entry.path,
        CONDITION_ROW_KINDS.filter((kind) => {
          try {
            judgeCondition(definition({ uses: [entry.path], appliesTo: [kind] }), inputOf(kind));
            return true;
          } catch {
            return false;
          }
        }),
      ]),
    );
    expect(readableKinds).toStrictEqual(Object.fromEntries(READABLE_FIELDS.map((entry) => [entry.path, [...entry.kinds]])));
    expect(new Set(READABLE_FIELDS.map((entry) => entry.path)).size).toBe(READABLE_FIELDS.length);
  });

  it("D4 §3 (i) 直後の行の評価から作られる欄と (ii) 実戦の事実のまま読まれる欄の印は、計画の列挙どおり", () => {
    const evaluationLeaves = (base: string) => ["scoreCp", "mate", "bestmove", "afterPassScoreCp", "afterPassMate", "dropCp"].map((name) => `${base}.${name}`);
    expect(READABLE_FIELDS.filter((entry) => entry.afterRow).map((entry) => entry.path).sort()).toStrictEqual(
      [
        "branch.kinds",
        "branch.diffCp",
        "branch.mateAfter",
        "branch.matedIfPassAfter",
        ...evaluationLeaves("branch.evaluationAfter"),
        "branch.standingPair.after",
        ...evaluationLeaves("evaluationAfter"),
        "standingPair.after",
        "failureEventBranchPly",
        "change.kind",
        "change.diffCp",
        "change.mateAfter",
      ].sort(),
    );
    const zone = ["zonePieces", "zoneControl"].flatMap((group) => ["ownKingZone", "opponentKingZone"].flatMap((z) => ["bySente", "byGote"].map((s) => `counterfactual.pvMinusActual.positionFacts.${group}.${z}.${s}`)));
    expect(READABLE_FIELDS.filter((entry) => entry.actualKept).map((entry) => entry.path).sort()).toStrictEqual(
      [
        "consequences.checks",
        "consequences.mate",
        "counterfactual.pvMinusActual.capturedRoles.us",
        "counterfactual.pvMinusActual.capturedRoles.opponent",
        "counterfactual.pvMinusActual.kingSurroundingsOwn",
        "counterfactual.pvMinusActual.kingEscapes",
        ...zone,
        "counterfactual.kingEscapesChangeFromRoot.actual",
      ].sort(),
    );
  });
  it("C-2 null の意味: 計画 §2 の表の「null の意味」列(値 / 判定不能)と、型が null を持たない欄(notNullable)を、パスの一覧で固定する", () => {
    const evaluationLeaves = (base: string) => ["scoreCp", "mate", "bestmove", "afterPassScoreCp", "afterPassMate", "dropCp"].map((name) => `${base}.${name}`);
    const zoneLeaves = (base: string, withSquares: boolean) => [
      ...(withSquares ? ["ownKingZone", "opponentKingZone"].map((zone) => `${base}.zoneSquares.${zone}`) : []),
      ...["zonePieces", "zoneControl"].flatMap((group) => ["ownKingZone", "opponentKingZone"].flatMap((zone) => ["bySente", "byGote"].map((side) => `${base}.${group}.${zone}.${side}`))),
    ];
    const bothSides = (leaves: string[]) => ["actual", "pv"].flatMap((side) => leaves.map((leaf) => `counterfactual.${side}.${leaf}`));
    const byNullMeans = (nullMeans: string) => READABLE_FIELDS.filter((entry) => entry.nullMeans === nullMeans).map((entry) => entry.path).sort();
    expect(byNullMeans("value")).toStrictEqual(
      [
        ...evaluationLeaves("trigger.evaluationBefore"),
        "trigger.kingSurroundings.squares",
        "trigger.kingSurroundings.own",
        "action.playedMove",
        "action.bestmoveAtBefore",
        ...evaluationLeaves("branch.evaluationAfter"),
        "userBestmoveAtBefore",
        ...evaluationLeaves("evaluationAfter"),
        "failureEventBranchPly",
        "consequences.mate",
        "counterfactual.pvTruncatedAtPly",
        ...bothSides(["mate", "gameEnd", "kingSurroundingsEnd.squares", "kingSurroundingsEnd.own"]),
      ].sort(),
    );
    expect(byNullMeans("undecidable")).toStrictEqual(
      [
        ...zoneLeaves("trigger.positionFacts", true),
        "branch.diffCp",
        "branch.mateAfter",
        ...bothSides(zoneLeaves("positionFactsEnd", true)),
        "counterfactual.pvMinusActual.capturedRoles.us",
        "counterfactual.pvMinusActual.capturedRoles.opponent",
        "counterfactual.pvMinusActual.kingSurroundingsOwn",
        "counterfactual.pvMinusActual.kingEscapes",
        ...zoneLeaves("counterfactual.pvMinusActual.positionFacts", false),
        "counterfactual.kingEscapesChangeFromRoot.actual",
        "counterfactual.kingEscapesChangeFromRoot.pv",
      ].sort(),
    );
    expect(byNullMeans("notNullable")).toStrictEqual(
      [
        "trigger.focus.state",
        "trigger.shape.status",
        "trigger.opponentIntent.classification",
        "branch.kinds",
        "branch.matedIfPassAfter",
        "branch.standingPair.before",
        "branch.standingPair.after",
        "moves.userMove",
        "moves.opponentMove",
        "standingPair.before",
        "standingPair.after",
        "change.kind",
        "change.diffCp",
        "change.mateAfter",
        "consequences.checks",
        "counterfactual.state",
        "counterfactual.comparedPlies",
        "counterfactual.windowPlies",
        "counterfactual.actualPlies",
        "counterfactual.pvLength",
        "counterfactual.pvUsablePlies",
        "counterfactual.pvBounded.lowerbound",
        "counterfactual.pvBounded.upperbound",
        "counterfactual.pvFirstMove",
        "counterfactual.pvFirstMoveIsBestmoveAtBefore",
        "counterfactual.pvFirstMoveIsPlayedMove",
        "counterfactual.kingEscapesRoot.count",
        ...bothSides(["capturedRoles.us", "capturedRoles.opponent", "checks.byUs", "checks.byOpponent", "kingEscapesEnd.count"]),
      ].sort(),
    );
  });

  it("C-2 門: 計画 §2 の表の「門」列を、門の並び(祖先から順)ごとのパスの一覧で固定する", () => {
    const evaluationLeaves = (base: string) => ["scoreCp", "mate", "bestmove", "afterPassScoreCp", "afterPassMate", "dropCp"].map((name) => `${base}.${name}`);
    const zoneLeaves = (base: string, withSquares: boolean) => [
      ...(withSquares ? ["ownKingZone", "opponentKingZone"].map((zone) => `${base}.zoneSquares.${zone}`) : []),
      ...["zonePieces", "zoneControl"].flatMap((group) => ["ownKingZone", "opponentKingZone"].flatMap((zone) => ["bySente", "byGote"].map((side) => `${base}.${group}.${zone}.${side}`))),
    ];
    const sequenceLeaves = (side: string) =>
      ["capturedRoles.us", "capturedRoles.opponent", "checks.byUs", "checks.byOpponent", "mate", "gameEnd", "kingSurroundingsEnd.squares", "kingSurroundingsEnd.own", ...zoneLeaves("positionFactsEnd", true)].map((leaf) => `counterfactual.${side}.${leaf}`);
    const grouped: Record<string, string[]> = {};
    for (const entry of READABLE_FIELDS) (grouped[entry.gates.map((gate) => `${gate.path}∈${gate.passes.join("|")}`).join(" → ")] ??= []).push(entry.path);
    for (const paths of Object.values(grouped)) paths.sort();
    const compared = "counterfactual.state∈compared";
    expect(grouped).toStrictEqual({
      "": [
        "trigger.opponentIntent.classification",
        "trigger.kingSurroundings.squares",
        "trigger.kingSurroundings.own",
        ...zoneLeaves("trigger.positionFacts", true),
        "action.playedMove",
        "action.bestmoveAtBefore",
        "branch.kinds",
        "branch.diffCp",
        "branch.mateAfter",
        "branch.matedIfPassAfter",
        "branch.standingPair.before",
        "branch.standingPair.after",
        "moves.userMove",
        "moves.opponentMove",
        "userBestmoveAtBefore",
        "standingPair.before",
        "standingPair.after",
        "failureEventBranchPly",
        "change.kind",
        "counterfactual.state",
      ].sort(),
      "trigger.evaluationBefore.state∈measured": evaluationLeaves("trigger.evaluationBefore").sort(),
      "trigger.focus.state∈stated|nothingToSay": ["trigger.focus.state"],
      "trigger.shape.state∈recorded": ["trigger.shape.status"],
      "branch.evaluationAfter.state∈measured": evaluationLeaves("branch.evaluationAfter").sort(),
      "evaluationAfter.state∈measured": evaluationLeaves("evaluationAfter").sort(),
      "change.kind∈cp": ["change.diffCp"],
      "change.kind∈mateAfter": ["change.mateAfter"],
      "consequences.windowShort∈false": ["consequences.checks", "consequences.mate"],
      [compared]: [
        "counterfactual.comparedPlies",
        "counterfactual.windowPlies",
        "counterfactual.actualPlies",
        "counterfactual.pvLength",
        "counterfactual.pvUsablePlies",
        "counterfactual.pvTruncatedAtPly",
        "counterfactual.pvBounded.lowerbound",
        "counterfactual.pvBounded.upperbound",
        "counterfactual.pvFirstMove",
        "counterfactual.pvFirstMoveIsBestmoveAtBefore",
        "counterfactual.pvFirstMoveIsPlayedMove",
        ...sequenceLeaves("actual"),
        ...sequenceLeaves("pv"),
        "counterfactual.pvMinusActual.capturedRoles.us",
        "counterfactual.pvMinusActual.capturedRoles.opponent",
        "counterfactual.pvMinusActual.kingSurroundingsOwn",
        "counterfactual.pvMinusActual.kingEscapes",
        ...zoneLeaves("counterfactual.pvMinusActual.positionFacts", false),
        "counterfactual.kingEscapesChangeFromRoot.actual",
        "counterfactual.kingEscapesChangeFromRoot.pv",
      ].sort(),
      [`${compared} → counterfactual.kingEscapesRoot.state∈counted`]: ["counterfactual.kingEscapesRoot.count"],
      [`${compared} → counterfactual.actual.kingEscapesEnd.state∈counted`]: ["counterfactual.actual.kingEscapesEnd.count"],
      [`${compared} → counterfactual.pv.kingEscapesEnd.state∈counted`]: ["counterfactual.pv.kingEscapesEnd.count"],
    });
  });

});

describe("judgeCondition(計画 §2)", () => {
  const scoreAtLeast300 = definition({ uses: ["trigger.evaluationBefore.scoreCp", "consequences.mate"], evaluate: (v) => (at(v, "trigger.evaluationBefore.scoreCp") as number) >= 300 });

  it("K-1 読める入力は match / noMatch、usedValues は uses のパスだけ", () => {
    const high = event("k", 11);
    const low = event("k", 21);
    low.trigger.evaluationBefore = measured(100);
    expect(judgeCondition(scoreAtLeast300, { kind: "failureEvent", row: high })).toStrictEqual({ state: "match", usedValues: { trigger: { evaluationBefore: { scoreCp: 500 } }, consequences: { mate: null } } });
    expect(judgeCondition(scoreAtLeast300, { kind: "failureEvent", row: low })).toStrictEqual({ state: "noMatch", usedValues: { trigger: { evaluationBefore: { scoreCp: 100 } }, consequences: { mate: null } } });
  });

  it("K-2 evaluationBefore が notMeasurable → 判定不能(理由 = 門の実際の状態)。measured で scoreCp が null(詰みの読み)は値", () => {
    const row = event("k", 11);
    row.trigger.evaluationBefore = { state: "notMeasurable" };
    expect(judgeCondition(definition({ uses: ["trigger.evaluationBefore.scoreCp"] }), { kind: "failureEvent", row })).toStrictEqual({
      state: "undecidable",
      missing: [{ path: "trigger.evaluationBefore.scoreCp", reason: { kind: "gate", gatePath: "trigger.evaluationBefore.state", actual: "notMeasurable" } }],
    });
    const mateRow = event("k", 21);
    mateRow.trigger.evaluationBefore = measured(null, 3);
    expect(judgeCondition(definition({ uses: ["trigger.evaluationBefore.scoreCp"], evaluate: (v) => at(v, "trigger.evaluationBefore.scoreCp") === null }), { kind: "failureEvent", row: mateRow })).toStrictEqual({
      state: "match",
      usedValues: { trigger: { evaluationBefore: { scoreCp: null } } },
    });
  });

  it("K-2 focus が nothingToSay → 値として読める / pending → 判定不能", () => {
    const d = definition({ uses: ["trigger.focus.state"], evaluate: (v) => at(v, "trigger.focus.state") === "nothingToSay" });
    expect(judgeCondition(d, { kind: "failureEvent", row: event("k", 11) })).toStrictEqual({ state: "match", usedValues: { trigger: { focus: { state: "nothingToSay" } } } });
    const pending = event("k", 21);
    pending.trigger.focus = { state: "pending" };
    expect(judgeCondition(d, { kind: "failureEvent", row: pending })).toStrictEqual({
      state: "undecidable",
      missing: [{ path: "trigger.focus.state", reason: { kind: "gate", gatePath: "trigger.focus.state", actual: "pending" } }],
    });
  });

  it("K-2 consequences.mate が null で windowShort が false → 値 / windowShort が true → checks も mate も判定不能", () => {
    const d = definition({ uses: ["consequences.checks", "consequences.mate"], evaluate: (v) => at(v, "consequences.mate") === null });
    expect(judgeCondition(d, { kind: "failureEvent", row: event("k", 11) })).toStrictEqual({ state: "match", usedValues: { consequences: { checks: [], mate: null } } });
    const short = event("k", 21);
    short.consequences.windowShort = true;
    const gate = { kind: "gate", gatePath: "consequences.windowShort", actual: true };
    expect(judgeCondition(d, { kind: "failureEvent", row: short })).toStrictEqual({
      state: "undecidable",
      missing: [
        { path: "consequences.checks", reason: gate },
        { path: "consequences.mate", reason: gate },
      ],
    });
  });

  it("K-2 failureEventBranchPly が null → 値(上がりの行)", () => {
    const d = definition({ uses: ["failureEventBranchPly"], appliesTo: ["rise"], evaluate: (v) => at(v, "failureEventBranchPly") === null });
    expect(judgeCondition(d, { kind: "rise", row: rise("k", 11) })).toStrictEqual({ state: "match", usedValues: { failureEventBranchPly: null } });
  });

  it("K-2 kingEscapesEnd が noKing で .count を使う → 判定不能 / counterfactual が compared でない → 判定不能", () => {
    const d = definition({ uses: ["counterfactual.actual.kingEscapesEnd.count"] });
    const noKing = event("k", 11);
    (noKing.counterfactual as CounterfactualComparison).actual.kingEscapesEnd = { state: "noKing" };
    expect(judgeCondition(d, { kind: "failureEvent", row: noKing })).toStrictEqual({
      state: "undecidable",
      missing: [{ path: "counterfactual.actual.kingEscapesEnd.count", reason: { kind: "gate", gatePath: "counterfactual.actual.kingEscapesEnd.state", actual: "noKing" } }],
    });
    const unrecorded = event("k", 21);
    unrecorded.counterfactual = { state: "unrecorded" };
    expect(judgeCondition(d, { kind: "failureEvent", row: unrecorded })).toStrictEqual({
      state: "undecidable",
      missing: [{ path: "counterfactual.actual.kingEscapesEnd.count", reason: { kind: "gate", gatePath: "counterfactual.state", actual: "unrecorded" } }],
    });
  });

  it("K-2 pvMinusActual.kingEscapes が null → 判定不能 / branch.diffCp が null → 判定不能", () => {
    const row = event("k", 11, ["mateDrop"]);
    (row.counterfactual as CounterfactualComparison).pvMinusActual.kingEscapes = null;
    row.branch.diffCp = null;
    expect(judgeCondition(definition({ uses: ["counterfactual.pvMinusActual.kingEscapes", "branch.diffCp"] }), { kind: "failureEvent", row })).toStrictEqual({
      state: "undecidable",
      missing: [
        { path: "counterfactual.pvMinusActual.kingEscapes", reason: { kind: "null" } },
        { path: "branch.diffCp", reason: { kind: "null" } },
      ],
    });
  });

  it("K-2 trigger.kingSurroundings が null(玉が無い)→ .own は値の null", () => {
    const row = event("k", 11);
    row.trigger.kingSurroundings = null;
    expect(judgeCondition(definition({ uses: ["trigger.kingSurroundings.own"], evaluate: (v) => at(v, "trigger.kingSurroundings.own") === null }), { kind: "failureEvent", row })).toStrictEqual({
      state: "match",
      usedValues: { trigger: { kingSurroundings: { own: null } } },
    });
  });

  it("D4 §3 の D2.5 の行: 玉の無い側の positionFacts は判定不能 / standingPair.before の undetermined は判定不能 / branch.standingPair.before の ahead は値", () => {
    const noKing = event("k", 11);
    noKing.trigger.positionFacts.zonePieces.ownKingZone = null;
    expect(judgeCondition(definition({ uses: ["trigger.positionFacts.zonePieces.ownKingZone.bySente"] }), { kind: "failureEvent", row: noKing })).toStrictEqual({
      state: "undecidable",
      missing: [{ path: "trigger.positionFacts.zonePieces.ownKingZone.bySente", reason: { kind: "null" } }],
    });
    const undetermined = rise("k", 21);
    undetermined.standingPair = { before: { undetermined: "unrecorded" }, after: "level" };
    expect(judgeCondition(definition({ uses: ["standingPair.before"], appliesTo: ["rise"] }), { kind: "rise", row: undetermined })).toStrictEqual({
      state: "undecidable",
      missing: [{ path: "standingPair.before", reason: { kind: "undetermined", undetermined: "unrecorded" } }],
    });
    expect(judgeCondition(definition({ uses: ["branch.standingPair.before"], evaluate: (v) => at(v, "branch.standingPair.before") === "ahead" }), { kind: "failureEvent", row: event("k", 31) })).toStrictEqual({
      state: "match",
      usedValues: { branch: { standingPair: { before: "ahead" } } },
    });
  });

  it("K-4 appliesTo に無い種類の行・最大の下がりの状態の行 → 判定しない", () => {
    const d = definition({ uses: ["counterfactual.state"], appliesTo: ["failureEvent", "maxDropPair"] });
    expect(judgeCondition(d, { kind: "rise", row: rise("k", 11) })).toStrictEqual({ state: "notJudged", reason: "kindNotApplied" });
    expect(judgeCondition(d, { kind: "maxDrop", row: maxDropState("k") })).toStrictEqual({ state: "notJudged", reason: "maxDropState" });
    expect(judgeCondition(d, { kind: "maxDrop", row: maxDropPair("k", 11) })).toStrictEqual({ state: "match", usedValues: { counterfactual: { state: "compared" } } });
    expect(judgeCondition(definition({ uses: ["counterfactual.state"], appliesTo: ["failureEvent"] }), { kind: "maxDrop", row: maxDropState("k") })).toStrictEqual({ state: "notJudged", reason: "kindNotApplied" });
  });

  it("K-7 evaluate には uses のパスだけの写しを渡す(外の欄が undefined なら真を返す架空の定義 → match)", () => {
    const d = definition({ uses: ["counterfactual.state"], evaluate: (v) => at(v, "trigger") === undefined && at(v, "kifuId") === undefined && at(v, "counterfactual.actual") === undefined });
    expect(judgeCondition(d, { kind: "failureEvent", row: event("k", 11) })).toStrictEqual({ state: "match", usedValues: { counterfactual: { state: "compared" } } });
  });
});

describe("checkCondition・loadCondition(計画 §2 の R-4・D4 §3)", () => {
  it("K-5 読み込みで止める: approved で approval null / draft で approval あり / label に(仮)が無い / uses が表に無い / appliesTo が空", () => {
    const approval = { approvedBy: "試験", date: "2026-09-16", record: "試験" };
    expect(problemsOf(definition({ status: "approved", approval: null }))).toStrictEqual([{ code: "approvedWithoutApproval" }]);
    expect(problemsOf(definition({ status: "draft", approval }))).toStrictEqual([{ code: "draftWithApproval" }]);
    expect(problemsOf(definition({ label: "試験だけの定義" }))).toStrictEqual([{ code: "labelWithoutProvisional" }]);
    expect(problemsOf(definition({ uses: ["trigger.evaluationBefore.state"] }))).toStrictEqual([{ code: "unknownPath", path: "trigger.evaluationBefore.state" }]);
    expect(problemsOf(definition({ appliesTo: [] }))).toStrictEqual([{ code: "emptyAppliesTo" }]);
    expect(problemsOf(definition({ status: "approved", approval, uses: ["trigger.evaluationBefore.scoreCp"] }))).toStrictEqual([]);
  });

  it("K-5 形の崩れた定義(evaluate が無い)は malformed だけを出して止める", () => {
    const { evaluate: _evaluate, ...withoutEvaluate } = definition();
    expect(problemsOf(withoutEvaluate)).toStrictEqual([{ code: "malformed", detail: "evaluate が関数でない" }]);
  });

  it("K-8 definitionSha256 は定義のファイルのバイト列の sha256(1 バイト変えると変わる。同じ id でも変わる)", () => {
    const d = definition();
    expect(checkCondition(d, new TextEncoder().encode("a")).definitionSha256).toBe("ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb");
    expect(checkCondition(d, new TextEncoder().encode("b")).definitionSha256).toBe("3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d");
  });

  it("K-8 loadCondition は定義のファイルを読み込み、そのバイト列の sha256 を持つ", async () => {
    const path = fileURLToPath(new URL("./conditionFixtures/test_only_loadable.ts", import.meta.url));
    const result = await loadCondition(path);
    expect(result.definition.id).toBe("test_only_loadable");
    expect(result.definitionSha256).toBe(createHash("sha256").update(readFileSync(path)).digest("hex"));
    expect(judgeCondition(result.definition, { kind: "failureEvent", row: event("k", 11) })).toStrictEqual({ state: "match", usedValues: { counterfactual: { state: "compared" } } });
  });

  it("K-12a pair を含む定義に、表にあるが failureEvent だけが持つ branch.standingPair.before → 種類の確かめで止まる(表に無いパスでは止まらない)", () => {
    expect(problemsOf(definition({ uses: ["branch.standingPair.before"], appliesTo: ["pair"] }))).toStrictEqual([{ code: "pathNotInKind", path: "branch.standingPair.before", kind: "pair" }]);
  });

  it("K-12b pair を含む定義に evaluationAfter.scoreCp(組にある)→ 結果の欄の確かめで止まる。rise だけの定義なら通る", () => {
    expect(problemsOf(definition({ uses: ["evaluationAfter.scoreCp"], appliesTo: ["pair"] }))).toStrictEqual([{ code: "afterRowFieldWithPair", path: "evaluationAfter.scoreCp" }]);
    expect(problemsOf(definition({ uses: ["evaluationAfter.scoreCp"], appliesTo: ["rise"] }))).toStrictEqual([]);
  });

  it("K-13 pair を含む定義に failureEventBranchPly / consequences.checks / counterfactual.pvMinusActual.kingEscapes → 3 つとも止まる(pair を含まなければ通る)", () => {
    expect(problemsOf(definition({ uses: ["failureEventBranchPly"], appliesTo: ["pair"] }))).toStrictEqual([{ code: "afterRowFieldWithPair", path: "failureEventBranchPly" }]);
    expect(problemsOf(definition({ uses: ["consequences.checks"], appliesTo: ["pair"] }))).toStrictEqual([{ code: "actualKeptFieldWithPair", path: "consequences.checks" }]);
    expect(problemsOf(definition({ uses: ["counterfactual.pvMinusActual.kingEscapes"], appliesTo: ["pair"] }))).toStrictEqual([{ code: "actualKeptFieldWithPair", path: "counterfactual.pvMinusActual.kingEscapes" }]);
    expect(problemsOf(definition({ uses: ["failureEventBranchPly", "consequences.checks", "counterfactual.pvMinusActual.kingEscapes"], appliesTo: ["rise", "maxDropPair"] }))).toStrictEqual([]);
  });
  it("C-1 appliesTo が 2 種類以上の定義: [failureEvent, pair] + branch.standingPair.before → 種類の確かめは pair だけで止まる / [rise, pair] + evaluationAfter.scoreCp → 結果の欄の確かめで止まる", () => {
    expect(problemsOf(definition({ uses: ["branch.standingPair.before"], appliesTo: ["failureEvent", "pair"] }))).toStrictEqual([{ code: "pathNotInKind", path: "branch.standingPair.before", kind: "pair" }]);
    expect(problemsOf(definition({ uses: ["evaluationAfter.scoreCp"], appliesTo: ["rise", "pair"] }))).toStrictEqual([{ code: "afterRowFieldWithPair", path: "evaluationAfter.scoreCp" }]);
  });

});

describe("judgeConditionPvSide(D4 §3 の Q-4)", () => {
  const escapes = definition({
    uses: ["counterfactual.actual.kingEscapesEnd.count", "trigger.kingSurroundings.own"],
    appliesTo: ["pair"],
    evaluate: (v) => (at(v, "counterfactual.actual.kingEscapesEnd.count") as number) >= 2,
  });

  it("K-14 読み筋の側の view は pv.kingEscapesEnd.count(3)と同じ trigger を、元のパスの名前で読む。実戦の側は actual(1)", () => {
    const input: ConditionInput = { kind: "pair", row: pairRow("k", 11) };
    expect(judgeCondition(escapes, input)).toStrictEqual({ state: "noMatch", usedValues: { counterfactual: { actual: { kingEscapesEnd: { count: 1 } } }, trigger: { kingSurroundings: { own: 3 } } } });
    expect(judgeConditionPvSide(escapes, input)).toStrictEqual({ state: "match", usedValues: { counterfactual: { actual: { kingEscapesEnd: { count: 3 } } }, trigger: { kingSurroundings: { own: 3 } } } });
  });

  it("K-14 読み筋の側の門も読み筋の側で見る(pv の玉が無い → 判定不能。欄の名前は元のパス)", () => {
    const row = pairRow("k", 11);
    (row.counterfactual as CounterfactualComparison).pv.kingEscapesEnd = { state: "noKing" };
    expect(judgeConditionPvSide(escapes, { kind: "pair", row })).toStrictEqual({
      state: "undecidable",
      missing: [{ path: "counterfactual.actual.kingEscapesEnd.count", reason: { kind: "gate", gatePath: "counterfactual.pv.kingEscapesEnd.state", actual: "noKing" } }],
    });
  });

  it("K-14 counterfactual.pvFirstMoveIsPlayedMove だけの定義 → 当てられない(actual.* が無い・置き換えの表に無い)", () => {
    const d = definition({ uses: ["counterfactual.pvFirstMoveIsPlayedMove"], appliesTo: ["pair"] });
    expect(judgeConditionPvSide(d, { kind: "pair", row: pairRow("k", 11) })).toStrictEqual({
      state: "notApplicable",
      reasons: [{ reason: "noActualPath" }, { reason: "pathNotReplaceable", paths: ["counterfactual.pvFirstMoveIsPlayedMove"] }],
    });
  });

  it("K-14(D4 §11 の L-6)actual.* があっても、置き換えの表に無い counterfactual の欄を使えば当てられない", () => {
    const d = definition({ uses: ["counterfactual.actual.kingEscapesEnd.count", "counterfactual.pvFirstMoveIsPlayedMove"], appliesTo: ["pair"] });
    expect(judgeConditionPvSide(d, { kind: "pair", row: pairRow("k", 11) })).toStrictEqual({
      state: "notApplicable",
      reasons: [{ reason: "pathNotReplaceable", paths: ["counterfactual.pvFirstMoveIsPlayedMove"] }],
    });
  });

  it("K-14 そのまま読む欄(standingPair.before・moves.*・userBestmoveAtBefore・counterfactual.state・comparedPlies・kingEscapesRoot.count)は読み筋の側でも同じ値", () => {
    const d = definition({
      uses: ["counterfactual.actual.checks.byOpponent", "standingPair.before", "moves.userMove", "userBestmoveAtBefore", "counterfactual.state", "counterfactual.comparedPlies", "counterfactual.kingEscapesRoot.count"],
      appliesTo: ["pair"],
    });
    const row = pairRow("k", 11);
    (row.counterfactual as CounterfactualComparison).pv.checks.byOpponent = [14];
    expect(judgeConditionPvSide(d, { kind: "pair", row })).toStrictEqual({
      state: "match",
      usedValues: {
        counterfactual: { actual: { checks: { byOpponent: [14] } }, state: "compared", comparedPlies: 6, kingEscapesRoot: { count: 2 } },
        standingPair: { before: "ahead" },
        moves: { userMove: "7g7f" },
        userBestmoveAtBefore: "2g2f",
      },
    });
  });
});

// ---- 集計(計画 §3)----

const game = (kifuId: string, patch: Partial<ConditionGameInput> = {}): ConditionGameInput => ({
  kifuId,
  userSide: "sente",
  ending: { kind: "resign", ply: 91 },
  listedResult: "loss",
  events: [],
  rises: [],
  maxDrop: maxDropState(kifuId),
  ...patch,
});
const withBefore = (row: FailureEvent, evaluation: Evaluation): FailureEvent => {
  row.trigger.evaluationBefore = evaluation;
  return row;
};
const always = loaded(definition({ uses: ["counterfactual.state"], appliesTo: ["failureEvent", "rise", "maxDropPair"] }));

describe("conditionTallyOf(計画 §3)", () => {
  it("K-3 該当 2・非該当 1・判定不能 4 → 分母 3、判定不能の理由の内訳、該当の一覧と局の数", () => {
    const d = loaded(definition({ uses: ["trigger.evaluationBefore.scoreCp"], evaluate: (v) => (at(v, "trigger.evaluationBefore.scoreCp") as number) >= 300 }));
    const games = [
      game("kifu-a", {
        events: [
          event("kifu-a", 11),
          withBefore(event("kifu-a", 21), measured(100)),
          withBefore(event("kifu-a", 31), { state: "notMeasurable" }),
          withBefore(event("kifu-a", 41), { state: "notMeasuredInCheck" }),
        ],
      }),
      game("kifu-b", { events: [withBefore(event("kifu-b", 11), measured(400)), withBefore(event("kifu-b", 21), { state: "unrecorded" }), withBefore(event("kifu-b", 31), { state: "notMeasurable" })] }),
    ];
    const tally = conditionTallyOf("p9", games, d);
    const gate = "trigger.evaluationBefore.state";
    expect(tally.overall).toStrictEqual({
      match: 2,
      noMatch: 1,
      denominator: 3,
      undecidable: 4,
      undecidableReasons: [
        { path: "trigger.evaluationBefore.scoreCp", reason: `${gate}=notMeasurable`, rows: 2 },
        { path: "trigger.evaluationBefore.scoreCp", reason: `${gate}=notMeasuredInCheck`, rows: 1 },
        { path: "trigger.evaluationBefore.scoreCp", reason: `${gate}=unrecorded`, rows: 1 },
      ],
      notJudged: { kindNotApplied: 2, maxDropState: 0 },
      duplicatePairsSkipped: 0,
      matches: [
        { kifuId: "kifu-a", rowKind: "failureEvent", branchPly: 11 },
        { kifuId: "kifu-b", rowKind: "failureEvent", branchPly: 11 },
      ],
      gamesWithMatch: 2,
    });
    expect([tally.person, tally.condition, tally.games, tally.countedRowKinds]).toStrictEqual([
      "p9",
      { id: "test_only_a", label: "試験だけの定義(仮)", status: "draft", definitionSha256: d.definitionSha256 },
      { total: 2, sente: 2, gote: 0 },
      ["failureEvent"],
    ]);
  });

  it("K-4 集計: appliesTo に無い種類の行と最大の下がりの状態の行は、判定せず数だけ", () => {
    const d = loaded(definition({ uses: ["counterfactual.state"], appliesTo: ["maxDropPair"] }));
    const tally = conditionTallyOf("p9", [game("kifu-a", { events: [event("kifu-a", 11)], rises: [rise("kifu-a", 21)] })], d);
    expect([tally.overall.notJudged, tally.overall.match, tally.overall.denominator, tally.countedRowKinds]).toStrictEqual([{ kindNotApplied: 2, maxDropState: 1 }, 0, 0, ["maxDropPair"]]);
  });

  it("K-6 同じ人の入力に同じ kifuId が 2 本 → 止める", () => {
    expect(() => conditionTallyOf("p9", [game("kifu-a"), game("kifu-b"), game("kifu-a")], always)).toThrow("同じ kifuId が 2 本");
  });

  it("K-9 §7.2 用の列は急落の Failure Event だけ(matedIfPass だけの Event・上がりは入らない)。同じ組 (kifuId, branchPly) は 1 回だけ数える", () => {
    const pairAt11 = maxDropPair("kifu-a", 11);
    (pairAt11 as { failureEventBranchPly: number | null }).failureEventBranchPly = 11;
    const riseAt21 = rise("kifu-a", 21);
    riseAt21.failureEventBranchPly = 21;
    const tally = conditionTallyOf(
      "p9",
      [
        game("kifu-a", {
          events: [event("kifu-a", 11, ["cpDrop"]), event("kifu-a", 21, ["matedIfPass"]), event("kifu-a", 31, ["mateDrop", "matedIfPass"])],
          maxDrop: pairAt11,
          rises: [riseAt21, rise("kifu-a", 51)],
        }),
      ],
      always,
    );
    expect([tally.overall.match, tally.overall.duplicatePairsSkipped, tally.overall.matches]).toStrictEqual([
      4,
      2,
      [
        { kifuId: "kifu-a", rowKind: "failureEvent", branchPly: 11 },
        { kifuId: "kifu-a", rowKind: "failureEvent", branchPly: 21 },
        { kifuId: "kifu-a", rowKind: "failureEvent", branchPly: 31 },
        { kifuId: "kifu-a", rowKind: "rise", branchPly: 51 },
      ],
    ]);
    expect(tally.section72).toStrictEqual({
      failureEventApplied: true,
      match: 2,
      noMatch: 0,
      undecidable: 0,
      matches: [
        { kifuId: "kifu-a", branchPly: 11, kinds: ["cpDrop"], within5: "absent", lostByEnding: "lost", listedResult: "loss", agreement: "agree" },
        { kifuId: "kifu-a", branchPly: 31, kinds: ["mateDrop", "matedIfPass"], within5: "absent", lostByEnding: "lost", listedResult: "loss", agreement: "agree" },
      ],
      gamesWithMatch: 1,
    });
  });

  it("K-9 落としたか: resign・ply 奇数・先手の局 → 落とした / ply 偶数・先手 → 落としていない / 後手の局は偶数で落とした / abort・読めない → 決まらない / ending 無し → 記録に無い", () => {
    expect([
      lostByEndingOf({ kind: "resign", ply: 91 }, "sente"),
      lostByEndingOf({ kind: "resign", ply: 92 }, "sente"),
      lostByEndingOf({ kind: "timeUp", ply: 92 }, "gote"),
      lostByEndingOf({ kind: "mate", ply: 91 }, "gote"),
      lostByEndingOf({ kind: "abort", ply: 50 }, "sente"),
      lostByEndingOf({ kind: "unreadable", reason: "ply_mismatch", ply: null }, "sente"),
      lostByEndingOf(undefined, "sente"),
      lostByEndingOf(null, "sente"),
    ]).toStrictEqual(["lost", "notLost", "lost", "notLost", "undetermined", "undetermined", "notInRecord", "notInRecord"]);
  });

  it("K-9 README の表と食い違えば「食い違い」、どちらかが決まらなければ並べるだけ", () => {
    const one = (kifuId: string) => [event(kifuId, 11)];
    const tally = conditionTallyOf(
      "p9",
      [
        game("kifu-a", { ending: { kind: "resign", ply: 92 }, listedResult: "loss", events: one("kifu-a") }),
        game("kifu-b", { ending: { kind: "resign", ply: 92 }, listedResult: "win", events: one("kifu-b") }),
        game("kifu-c", { ending: { kind: "abort", ply: 40 }, listedResult: "win", events: one("kifu-c") }),
        game("kifu-d", { ending: { kind: "resign", ply: 91 }, listedResult: null, events: one("kifu-d") }),
        game("kifu-e", { ending: undefined, listedResult: "loss", events: one("kifu-e") }),
      ],
      always,
    );
    expect(tally.section72.matches.map((m) => [m.kifuId, m.lostByEnding, m.listedResult, m.agreement])).toStrictEqual([
      ["kifu-a", "notLost", "loss", "mismatch"],
      ["kifu-b", "notLost", "win", "agree"],
      ["kifu-c", "undetermined", "win", "notComparable"],
      ["kifu-d", "lost", "notListed", "notComparable"],
      ["kifu-e", "notInRecord", "loss", "notComparable"],
    ]);
  });

  it("K-9 5 手以内の王手・詰み: 王手か詰みがあれば「あり」、無くて窓が足りなければ「窓が足りない」、無ければ「なし」", () => {
    const withConsequences = (branchPly: number, checks: number[], mate: number | null, windowShort: boolean) => {
      const row = event("kifu-a", branchPly);
      row.consequences = { checks, mate, windowPlies: 5, windowShort };
      return row;
    };
    const tally = conditionTallyOf(
      "p9",
      [game("kifu-a", { events: [withConsequences(11, [14], null, true), withConsequences(21, [], null, true), withConsequences(31, [], null, false), withConsequences(41, [], 46, false)] })],
      always,
    );
    expect(tally.section72.matches.map((m) => [m.branchPly, m.within5])).toStrictEqual([
      [11, "present"],
      [21, "windowShort"],
      [31, "absent"],
      [41, "present"],
    ]);
  });
});

describe("testSideTallyOf・userSideOf(計画 §4 の 2)", () => {
  it("K-10 試す側は先手の局と後手の局を別の列に出す(混ぜた合計にしない)", () => {
    const result = testSideTallyOf(
      "p1",
      {
        sente: [game("s-1", { events: [event("s-1", 11)] }), game("s-2", { events: [event("s-2", 11)] })],
        gote: [game("g-1", { userSide: "gote", events: [event("g-1", 11), event("g-1", 21), event("g-1", 31)] })],
      },
      always,
    );
    expect([result.sente.overall.match, result.sente.games, result.gote.overall.match, result.gote.games]).toStrictEqual([2, { total: 2, sente: 2, gote: 0 }, 3, { total: 1, sente: 0, gote: 1 }]);
  });

  it("K-10 列と本人の側が食い違う局・両方の列にある kifuId → 止める", () => {
    expect(() => testSideTallyOf("p1", { sente: [game("g-1", { userSide: "gote" })], gote: [] }, always)).toThrow("本人が gote の局");
    expect(() => testSideTallyOf("p1", { sente: [game("x-1")], gote: [game("x-1", { userSide: "gote" })] }, always)).toThrow("両方にある");
  });

  it("本人の側は meta の mirrored と originalUserSide から(無ければ先手。食い違えば止める)", () => {
    expect([userSideOf(undefined), userSideOf({ mirrored: false }), userSideOf({ mirrored: true, originalUserSide: "gote" })]).toStrictEqual(["sente", "sente", "gote"]);
    expect(() => userSideOf({ mirrored: true })).toThrow("originalUserSide が gote でない");
    expect(() => userSideOf({ originalUserSide: "gote" })).toThrow("originalUserSide がある");
  });
});
