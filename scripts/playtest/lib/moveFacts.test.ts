// STEP D2.6(docs/STEP_D2.6_PLAN_2026-09-17.md §6)。本人の手そのものの事実(U-1〜U-9)の固定例 F-1〜F-12b と、スキーマ v0.7・v0.4 の形。
// **エンジンは起動しない。**
//
// 【正解の置き方】期待は計画書 §6 の表のまま(盤の図から手で導いた。実装の出力から写さない)。
// 【この試験が確かめないこと】F-13(旧版の出力とのバイト一致)は実装の記録(計画 §10)に、道具の実行で残す。

import { describe, expect, it } from "vitest";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import { checkCondition, judgeCondition, judgeConditionPvSide, type ConditionDefinition, type PairRow } from "./condition.js";
import { counterfactualOf, POSITION_FACTS_RULES, sequenceFacts, type CounterfactualComparison } from "./counterfactual.js";
import { loadDiagnosisMomentSchema } from "./diagnosisMoment.js";
import { loadFailureEventSchema } from "./failureEventSchema.js";
import { moveFactsOf, STANDARD_ROLES, type UserMoveFacts } from "./moveFacts.js";
import { DIAGNOSIS_MOMENT_MOVE_FACTS_BASE_VERSION, DIAGNOSIS_MOMENT_SCHEMA_VERSION, FAILURE_EVENT_MOVE_FACTS_BASE_VERSION, FAILURE_EVENT_SCHEMA_VERSION } from "./schemaVersions.js";

type Json = Record<string, any>;
const INIT = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
const facts = (sfen: string, move: string): UserMoveFacts => moveFactsOf(sfen, move, POSITION_FACTS_RULES);
/** U-1〜U-9 を計画 §6 の表の並びで */
const row = (f: UserMoveFacts) => [f.role, f.drop, f.capturedRole, f.promotion, f.kingMove, f.fromInOwnKingZone, f.toInOwnKingZone, f.toInOpponentKingZone, f.ownKingZoneReachBeforeMinusAfter];

describe("moveFactsOf(計画 §1・§6)", () => {
  it("F-1 平手 7g7f: 歩・区域の外・利きの差 0", () => {
    expect(row(facts(INIT, "7g7f"))).toEqual(["pawn", false, null, false, false, false, false, false, 0]);
  });

  it("F-2 平手 6i7h: 金が区域の中(6i)から外(7h)へ、自玉の区域に届く升 3 → 1 で +2", () => {
    expect(row(facts(INIT, "6i7h"))).toEqual(["gold", false, null, false, false, true, false, false, 2]);
  });

  it("F-3 平手 5i4h: 玉の手。U-6・U-7 は true、U-9 は null", () => {
    expect(row(facts(INIT, "5i4h"))).toEqual(["king", false, null, false, true, true, true, false, null]);
  });

  it("F-4 金を 4h に打つ: 打つ手。U-6 は null、U-9 は 0 − 2 = −2", () => {
    expect(row(facts("4k4/9/9/9/9/9/9/9/4K4 b G 1", "G*4h"))).toEqual(["gold", true, null, false, false, null, true, false, -2]);
  });

  it("F-5 角が銀を取って成る(2h8b+): role は成る前、取った駒は銀、相手玉 7a の区域に入る", () => {
    expect(row(facts("2k6/1s7/9/9/9/9/9/7B1/4K4 b - 1", "2h8b+"))).toEqual(["bishop", false, "silver", true, false, false, false, true, 0]);
  });

  it("F-6 先手玉の無い局面で飛が竜を取る: 取った駒は竜のまま、自玉に依る欄は null", () => {
    expect(row(facts("4k2+r1/9/9/9/9/9/9/9/7R1 b - 1", "2i2a"))).toEqual(["rook", false, "dragon", false, false, null, null, false, null]);
  });

  it("F-7 歩が 5c に成る / 成らない", () => {
    expect(row(facts("4k4/9/9/4P4/9/9/9/9/4K4 b - 1", "5d5c+"))).toEqual(["pawn", false, null, true, false, false, false, false, 0]);
    expect(row(facts("4k4/9/9/4P4/9/9/9/9/4K4 b - 1", "5d5c"))).toEqual(["pawn", false, null, false, false, false, false, false, 0]);
  });

  it("F-8 飛が 5e から 3e へ: 前は 5h・5i(玉で止まり 5i を含む)の 2、後は 0 で +2", () => {
    expect(row(facts("3k5/9/9/9/4R4/9/9/9/4K4 b - 1", "5e3e"))).toEqual(["rook", false, null, false, false, false, false, false, 2]);
  });

  it("F-9 飛が 5e から 5c へ: 後の利きは空いた 5e を通って 5h・5i に届くので 2 − 2 = 0", () => {
    expect(row(facts("3k5/9/9/9/4R4/9/9/9/4K4 b - 1", "5e5c"))).toEqual(["rook", false, null, false, false, false, false, false, 0]);
  });

  it("F-14 飛が 5e から 5g へ(監査 f2 の N-1): 前は 5h・5i の 2、後も 5h・5i の 2 で 0。指す前の利きを指した後の占有で数えると、5g の自分で止まって前が 0 になり −2", () => {
    expect(facts("3k5/9/9/9/4R4/9/9/9/4K4 b - 1", "5e5g").ownKingZoneReachBeforeMinusAfter).toBe(0);
  });

  it("読めない手・合法でない手・扱わない規則は例外", () => {
    expect(() => facts(INIT, "zz")).toThrow(/読めない/);
    expect(() => facts(INIT, "5i5g")).toThrow(/合法でない/);
    expect(() => moveFactsOf(INIT, "7g7f", { ...POSITION_FACTS_RULES, control: "pieces" as never })).toThrow(/扱わない規則/);
  });

  it("駒種の並びは本将棋の 14 種", () => {
    expect(STANDARD_ROLES).toHaveLength(14);
  });
});

// ---- 反事実の組(F-10・F-10b)と条件式(F-11・F-12・F-12b)----

const ROOT = "4k4/9/9/9/9/9/4P4/9/4K4 b G 1";
function focus(sfen: string, pv: readonly string[]): SearchPvObservation {
  return { source: "focus_baseline", sfen, moveUsi: null, multipv: 1, scoreCp: 0, mate: null, pv: [...pv], lowerbound: false, upperbound: false };
}
function compared(actual: string[], pv: string[]): CounterfactualComparison {
  const counterfactual = counterfactualOf({ record: { sfen: ROOT, searchPvs: [focus(ROOT, pv)] }, moves: actual, branchPly: 1, windowPlies: 5, initialSfen: ROOT, bestmoveAtBefore: null });
  if (counterfactual.state !== "compared") throw new Error(`compared でない: ${counterfactual.state}`);
  return counterfactual;
}
const pairRow = (counterfactual: CounterfactualComparison): PairRow => ({ kifuId: "d26", pairKind: "compared", counterfactual }) as unknown as PairRow;
const definition = (uses: string, evaluate: ConditionDefinition["evaluate"]) =>
  checkCondition(
    { id: "test_only_move_facts", label: "試験だけの定義(仮)", status: "draft", definitionText: "試験だけ", uses: [uses], thresholds: {}, appliesTo: ["pair"], approval: null, evaluate } satisfies ConditionDefinition,
    new TextEncoder().encode(uses),
  ).definition;
const DROP = "counterfactual.actual.userMoveFacts.drop";
const FROM = "counterfactual.actual.userMoveFacts.fromInOwnKingZone";
const REACH = "counterfactual.actual.userMoveFacts.ownKingZoneReachBeforeMinusAfter";
const dropDef = definition(DROP, (view) => (view as Json).counterfactual.actual.userMoveFacts.drop === true);
const fromDef = definition(FROM, (view) => (view as Json).counterfactual.actual.userMoveFacts.fromInOwnKingZone === true);
const reachDef = definition(REACH, (view) => (view as Json).counterfactual.actual.userMoveFacts.ownKingZoneReachBeforeMinusAfter > 0);
/** 判定の形(B の N-1: gatePath の文字列は両側で違うので、状態・理由の種類・欄の名前で比べる) */
const shape = (judgement: Json) => (judgement.state === "undecidable" ? { state: judgement.state, missing: judgement.missing.map((m: Json) => ({ path: m.path, kind: m.reason.kind })) } : { state: judgement.state });

describe("反事実の両側(計画 §2・§3)", () => {
  it("F-10 実戦は盤上の手(5g5f)、読み筋は打つ手(G*4h): 両側に同じ関数の値", () => {
    const c = compared(["5g5f", "5a5b"], ["G*4h", "5a5b"]);
    expect(c.pvFirstMoveIsPlayedMove).toBe(false);
    expect(c.actual.userMoveFacts).toEqual(facts(ROOT, "5g5f"));
    expect(c.pv.userMoveFacts).toEqual(facts(ROOT, "G*4h"));
    expect([c.actual.userMoveFacts.drop, c.pv.userMoveFacts.drop]).toEqual([false, true]);
  });

  it("F-10b 読み筋の 1 手目 = 実戦の手: 両側の事実が深く等しく、条件式の判定の形も同じ", () => {
    const c = compared(["5g5f", "5a5b"], ["5g5f", "5a5b"]);
    expect(c.pvFirstMoveIsPlayedMove).toBe(true);
    expect(c.pv.userMoveFacts).toStrictEqual(c.actual.userMoveFacts);
    for (const def of [dropDef, fromDef, reachDef]) {
      expect(shape(judgeConditionPvSide(def, { kind: "pair", row: pairRow(c) }) as Json)).toEqual(shape(judgeCondition(def, { kind: "pair", row: pairRow(c) }) as Json));
    }
  });

  it("F-11 drop を読む条件式: 実戦の側 noMatch、読み筋の側 match(view は元のパスの名前で pv の値)", () => {
    const row = pairRow(compared(["5g5f", "5a5b"], ["G*4h", "5a5b"]));
    expect(judgeCondition(dropDef, { kind: "pair", row })).toEqual({ state: "noMatch", usedValues: { counterfactual: { actual: { userMoveFacts: { drop: false } } } } });
    expect(judgeConditionPvSide(dropDef, { kind: "pair", row })).toEqual({ state: "match", usedValues: { counterfactual: { actual: { userMoveFacts: { drop: true } } } } });
  });

  it("F-12 fromInOwnKingZone を読む条件式: 実戦の側は判定できる、読み筋の側(打つ手)は判定不能で理由の種類は gate", () => {
    const row = pairRow(compared(["5g5f", "5a5b"], ["G*4h", "5a5b"]));
    expect(judgeCondition(fromDef, { kind: "pair", row }).state).toBe("noMatch");
    expect(judgeConditionPvSide(fromDef, { kind: "pair", row })).toEqual({
      state: "undecidable",
      missing: [{ path: FROM, reason: { kind: "gate", gatePath: "counterfactual.pv.userMoveFacts.drop", actual: true } }],
    });
  });

  it("F-12b U-9 を読む条件式: 実戦の手が玉の手なら実戦の側は判定不能で理由の種類は gate、読み筋の側(歩)は判定できる", () => {
    const row = pairRow(compared(["5i4i", "5a5b"], ["5g5f", "5a5b"]));
    expect(judgeCondition(reachDef, { kind: "pair", row })).toEqual({
      state: "undecidable",
      missing: [{ path: REACH, reason: { kind: "gate", gatePath: "counterfactual.actual.userMoveFacts.kingMove", actual: true } }],
    });
    expect(judgeConditionPvSide(reachDef, { kind: "pair", row }).state).toBe("noMatch");
  });

  it("sequenceFacts は空の手順を受けない", () => {
    expect(() => sequenceFacts(ROOT, [], 1)).toThrow(/手順が空/);
  });
});

// ---- スキーマ(計画 §4)----

const clone = (value: unknown): Json => JSON.parse(JSON.stringify(value)) as Json;
function withoutUserMoveFacts(counterfactual: Json): void {
  for (const variant of counterfactual.oneOf as Json[]) {
    if (variant.properties.state?.const !== "compared") continue;
    for (const side of ["actual", "pv"]) {
      const sequence = variant.properties[side];
      delete sequence.properties.userMoveFacts;
      sequence.required = (sequence.required as string[]).filter((key) => key !== "userMoveFacts");
    }
  }
}

describe("スキーマ v0.7・v0.4(計画 §4、監査 f2 の W-1)", () => {
  it("今の版は 0.7・0.4", () => {
    expect([FAILURE_EVENT_SCHEMA_VERSION, DIAGNOSIS_MOMENT_SCHEMA_VERSION]).toEqual(["0.7", "0.4"]);
  });

  it("Failure Event 0.7 = 0.6 + counterfactual(compared)の actual・pv の userMoveFacts(版の値・$id・title・description のほかは同じ)", () => {
    const current = clone(loadFailureEventSchema());
    const base = clone(loadFailureEventSchema(FAILURE_EVENT_MOVE_FACTS_BASE_VERSION));
    withoutUserMoveFacts(current.properties.counterfactual);
    current.properties.schemaVersion = base.properties.schemaVersion;
    for (const key of ["$id", "title", "description"]) current[key] = base[key];
    expect(current).toEqual(base);
  });

  it("diagnosis-moment 0.4 = 0.3 + 組の行の counterfactual の userMoveFacts", () => {
    const current = clone(loadDiagnosisMomentSchema());
    const base = clone(loadDiagnosisMomentSchema(DIAGNOSIS_MOMENT_MOVE_FACTS_BASE_VERSION));
    let withCounterfactual = 0;
    for (const variant of current.oneOf as Json[]) {
      variant.properties.schemaVersion.const = DIAGNOSIS_MOMENT_MOVE_FACTS_BASE_VERSION;
      if (variant.properties.counterfactual) {
        withoutUserMoveFacts(variant.properties.counterfactual);
        withCounterfactual += 1;
      }
    }
    for (const key of ["$id", "title", "description"]) current[key] = base[key];
    expect(withCounterfactual).toBe(3);
    expect(current).toEqual(base);
  });

  it("userMoveFacts の欄の型: 駒種の列挙は 14 種(取っていないは null)、U-6〜U-9 は null を通す", () => {
    const compared = (loadFailureEventSchema() as Json).properties.counterfactual.oneOf.find((v: Json) => v.properties.state?.const === "compared");
    const umf = compared.properties.actual.properties.userMoveFacts;
    expect(umf.properties.role.enum).toEqual([...STANDARD_ROLES]);
    expect(umf.properties.capturedRole.enum).toEqual([...STANDARD_ROLES, null]);
    expect(umf.properties.ownKingZoneReachBeforeMinusAfter.type).toEqual(["integer", "null"]);
    expect(compared.properties.pv.properties.userMoveFacts).toEqual(umf);
  });
});
