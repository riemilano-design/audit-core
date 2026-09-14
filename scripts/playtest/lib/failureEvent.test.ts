// STEP D1 の lib の試験(docs/STEP_D1_PLAN_2026-09-14.md 5.1)。**エンジンは起動しない。**
// 固定例は、探索モード game-01 の実際の指し手に合成の評価を植えた記録を使う(lib/failureEventFixtures.ts)。
// ②③は本番の explainPositionWithStatus で作る。②の分類の期待値は、同じ記録を分類し直して比べる
// (件数や狙いの id を固定しない ― data/intents/ を増やすたびに落ちるため。P-20)。

import { describe, expect, it } from "vitest";
import { detectIntents } from "../../../apps/server/src/analysis/intentDetector.js";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import {
  actualContinuation,
  buildDiagnosisReport,
  diagnoseRecords,
  DRAFT_RULE_1,
  evaluationOf,
  focusStateOf,
  pairEvaluations,
  readEvaluations,
  renderDiagnosisReport,
} from "./failureEvent.js";
import { baseRowsOf, engineRef, GAME01_MOVES, plantedRecords } from "./failureEventFixtures.js";
import { classifyIntentStatementRow } from "./intentStatement.js";

const eventAt = (events: ReturnType<typeof diagnoseRecords>["events"], branchPly: number) => events.find((e) => e.branchPly === branchPly);
/** 仮置きの規則(DRAFT_RULE_1)で数える。**規則は呼び出し側が渡す**(lib に既定値を置かない。監査 B の必須 2) */
const diagnoseDraft = (kifuId: string, records: readonly RecordLine[]) => diagnoseRecords(kifuId, records, DRAFT_RULE_1);

describe("F-1: 植えた死因①(優勢 → 急落 → 窓の中に自玉への王手)", () => {
  // ply 48: +500・afterPass.mate 3・dropCp 350 / ply 50: −300。後手の手の後に王手中なのは 52・54・56(56 で詰み)。
  const records = plantedRecords(GAME01_MOVES, {
    48: engineRef(500, { afterPassMate: 3, dropCp: 350, bestmove: "2h2g" }),
    50: engineRef(-300),
  });
  const { events, counts } = diagnoseDraft("game-01", records);

  it("分岐点 49 に死因①が 1 件、draft で出る。窓(50〜54)の王手は 52・54、詰み(56)は窓の外", () => {
    const event = eventAt(events, 49);
    expect(event).toBeDefined();
    expect(event!.branch).toEqual({ kinds: ["cpDrop"], diffCp: -800, mateAfter: null, matedIfPassAfter: false });
    expect(event!.consequences).toEqual({ checks: [52, 54], mate: null, windowPlies: 5, windowShort: false });
    expect(event!.candidateModes).toEqual([{ mode: "mate_threat", status: "draft", matchedBy: ["cpDrop"] }]);
    expect(counts.cause1Draft).toBe(1);
  });

  it("実際の手は分岐点(49 手目)の手、直前の bestmove は直前の行の baseline.bestmove", () => {
    const event = eventAt(events, 49)!;
    expect(event.action).toEqual({ playedMove: GAME01_MOVES[48], bestmoveAtBefore: "2h2g" });
    expect(event.action.playedMove).toBe("5h5c+");
    expect([event.fromReadyPly, event.toReadyPly]).toEqual([48, 50]);
  });

  it("発症条件に直前の行の afterPass.mate と dropCp が状態つきで写る(計画 9.1)", () => {
    const before = eventAt(events, 49)!.trigger.evaluationBefore;
    expect(before).toMatchObject({ state: "measured", scoreCp: 500, afterPassMate: 3, dropCp: 350 });
    expect(counts.beforeAfterPassMate).toBe(1);
    expect(counts.beforeDropCpAtLeast).toBe(1);
  });

  it("直前の行の afterPass.mate は、1 つ前の組(46→48)から見ると「直後にパスすると詰まされる読み」であり、急落とは別に数える", () => {
    const event = eventAt(events, 47);
    expect(event?.branch).toEqual({ kinds: ["matedIfPass"], diffCp: 500, mateAfter: null, matedIfPassAfter: true });
    expect(event?.candidateModes).toEqual([]); // 直前(46)は 0 で優勢ではない
    // 分岐点 47 の窓(48〜52)にも、後手の 52 手目の王手が入る(期待値を最初 1 と書いた読み違い。窓の中身を辿っていなかった)
    expect(event?.consequences).toEqual({ checks: [52], mate: null, windowPlies: 5, windowShort: false });
    // 「うち」は急落候補の内訳(計画 9.1・D-3): 窓に王手のある Failure Event は 47・49 の 2 件だが、急落候補は 49 だけなので 1
    expect(counts).toMatchObject({ dropCandidates: 1, matedIfPassPairs: 1, events: 2, fromAdvantage: 1, withCheck: 1, withMate: 0 });
  });

  it("王手中・終局の行は評価を持たず、その行に掛かる組は比べない", () => {
    expect(counts).toMatchObject({ readyRows: 29, notMeasuredInCheck: 6, notMeasuredGameEnd: 1, notMeasurable: 0, unrecorded: 0 });
    expect(counts.measured).toBe(22);
    expect(counts.comparedPairs + counts.mateAfterPairs + counts.notComparedPairs).toBe(28);
  });
});

describe("F-2・F-3: 当たらない形", () => {
  it("F-2: 急落だが直前が優勢でなければ、急落候補 1・死因① 0", () => {
    const { events, counts } = diagnoseDraft("f2", plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(-500) }));
    expect(eventAt(events, 21)?.branch.kinds).toEqual(["cpDrop"]);
    expect(counts).toMatchObject({ dropCandidates: 1, fromAdvantage: 0, cause1Draft: 0 });
  });

  it("F-3: 優勢から急落しても、窓の中に王手も詰みも無ければ死因① 0", () => {
    const { events, counts } = diagnoseDraft("f3", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(-300) }));
    expect(eventAt(events, 21)?.consequences).toEqual({ checks: [], mate: null, windowPlies: 5, windowShort: false });
    expect(counts).toMatchObject({ dropCandidates: 1, fromAdvantage: 1, cause1Draft: 0 });
  });
});

describe("F-4: 窓が足りない", () => {
  it("分岐点の後、窓の途中で記録が終わり終局もしていなければ「窓が足りない」(起きなかったにしない)", () => {
    const moves = GAME01_MOVES.slice(0, 30);
    const { events, counts } = diagnoseDraft("f4", plantedRecords(moves, { 26: engineRef(500), 28: engineRef(-300) }));
    expect(eventAt(events, 27)?.consequences).toEqual({ checks: [], mate: null, windowPlies: 5, windowShort: true });
    expect(counts.windowShort).toBe(1);
  });

  it("窓の終わりちょうどで記録が終わるなら「足りない」にしない(境目。32 手で切ると分岐点 27 の窓 28〜32 は全部ある。監査 B の必須 1)", () => {
    const moves = GAME01_MOVES.slice(0, 32);
    const { events } = diagnoseDraft("f4-edge", plantedRecords(moves, { 26: engineRef(500), 28: engineRef(-300) }));
    expect(eventAt(events, 27)?.consequences).toEqual({ checks: [], mate: null, windowPlies: 5, windowShort: false });
  });

  it("先手が詰ませて終わる窓は、窓は閉じるが「窓の中に詰み」にしない(数えるのは後手の勝ちの詰みだけ。監査 B の非必須 c)", () => {
    // 後手玉 5 一・先手の歩 5 三・先手の持ち駒 金 → G*5b で頭金の詰み
    const sfen = "4k4/9/4P4/9/9/9/9/9/4K4 b G 1";
    expect(actualContinuation(["G*5b"], 1, 5, sfen)).toEqual({ checks: [], mate: null, windowPlies: 5, windowShort: false });
  });

  it("終局で終わる棋譜は、終局の手で窓が閉じるので「足りない」にしない", () => {
    const continuation = actualContinuation(GAME01_MOVES, 53, 5);
    expect(continuation).toEqual({ checks: [54, 56], mate: 56, windowPlies: 5, windowShort: false });
  });
});

describe("F-5: 評価の状態(計画 2.)", () => {
  const rows = baseRowsOf(GAME01_MOVES);
  const recordAt = (ply: number, engineReference: RecordLine["engineReference"] | "absent"): RecordLine => {
    const [record] = plantedRecords(GAME01_MOVES, { [ply]: engineReference === undefined ? "absent" : engineReference }).filter((r) => r.ply === ply);
    return record!;
  };

  it("null + 終局 / null + 王手中 / null + どちらでもない / 欄なし / 値が 1 つも無い、を 5 つに分ける", () => {
    expect(rows.find((r) => r.ply === 56)).toBeDefined();
    expect(evaluationOf(recordAt(56, null))).toEqual({ state: "notMeasuredGameEnd" });
    expect(evaluationOf(recordAt(34, null))).toEqual({ state: "notMeasuredInCheck" });
    expect(evaluationOf(recordAt(20, null))).toEqual({ state: "notMeasurable" });
    expect(evaluationOf(recordAt(20, "absent"))).toEqual({ state: "unrecorded" });
    expect(evaluationOf(recordAt(20, engineRef(null)))).toEqual({ state: "notMeasurable" });
    expect(evaluationOf(recordAt(20, engineRef(120)))).toMatchObject({ state: "measured", scoreCp: 120 });
  });

  it("比べられなかった組は、どちら側のどの状態かを理由として持つ", () => {
    const records = plantedRecords(GAME01_MOVES, { 32: engineRef(10), 34: null, 36: "absent" });
    const pairs = pairEvaluations(readEvaluations(records));
    expect(pairs.find((p) => p.fromPly === 32)).toEqual({ kind: "notCompared", fromPly: 32, toPly: 34, reason: "notMeasuredInCheck", side: "to" });
    expect(pairs.find((p) => p.fromPly === 34)).toEqual({ kind: "notCompared", fromPly: 34, toPly: 36, reason: "notMeasuredInCheck", side: "from" });
    expect(pairs.find((p) => p.fromPly === 36)).toEqual({ kind: "notCompared", fromPly: 36, toPly: 38, reason: "unrecorded", side: "from" });
  });

  it("評価が 1 つも無い記録は、急落候補も死因①も 0 で、全行「測っていない」", () => {
    const plant = Object.fromEntries(baseRowsOf(GAME01_MOVES).map((row) => [row.ply, "absent" as const]));
    const { counts } = diagnoseDraft("unrecorded", plantedRecords(GAME01_MOVES, plant));
    expect(counts).toMatchObject({ readyRows: 29, unrecorded: 29, measured: 0, comparedPairs: 0, notComparedPairs: 28, dropCandidates: 0, cause1Draft: 0 });
  });
});

describe("F-6: mate が絡む組(計画 D-3)", () => {
  it("(i) 直前 +500・直後 baseline.mate = −3 は mateDrop(差は取らない)", () => {
    const { events } = diagnoseDraft("f6i", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(null, { mate: -3 }) }));
    expect(eventAt(events, 21)?.branch).toEqual({ kinds: ["mateDrop"], diffCp: null, mateAfter: -3, matedIfPassAfter: false });
  });

  it("(ii) 直後の行の afterPass.mate > 0 は「パスすると詰まされる読み」(急落とは呼ばない)。< 0 は当たらない", () => {
    // 22 は 350: 植え方の既定で次の行(24)は 0 なので、400 にすると 22→24 の差が −400 で急落に当たってしまう(最初の読み違い)
    const hit = diagnoseDraft("f6ii", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(350, { afterPassMate: 5 }) }));
    expect(eventAt(hit.events, 21)?.branch).toEqual({ kinds: ["matedIfPass"], diffCp: -150, mateAfter: null, matedIfPassAfter: true });
    // 直前(20)は +500 だが、急落候補ではないので「うち直前が優勢」に入れない(計画 9.1・D-3)
    expect(hit.counts).toMatchObject({ dropCandidates: 0, matedIfPassPairs: 1, events: 1, fromAdvantage: 0 });

    const miss = diagnoseDraft("f6ii-neg", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(350, { afterPassMate: -5 }) }));
    expect(eventAt(miss.events, 21)).toBeUndefined();
  });
});

describe("F-7: 発症条件の写し(②・形・③。計画 3.1・9.2)", () => {
  it("③は 4 つの状態に分け、文はそのまま写す(文の中身では分けない)", () => {
    const records = plantedRecords(GAME01_MOVES, {}, {
      2: { focusTextState: "ready", focusText: "いまのところ、急いで対応することはありません。" },
      4: { focusTextState: "ready", focusText: null },
      6: { focusTextState: "pending", focusText: null },
      8: "absent",
    });
    const at = (ply: number) => records.find((r) => r.ply === ply)!;
    expect(focusStateOf(at(2))).toEqual({ state: "stated", text: "いまのところ、急いで対応することはありません。" });
    expect(focusStateOf(at(4))).toEqual({ state: "nothingToSay" });
    expect(focusStateOf(at(6))).toEqual({ state: "pending" });
    expect(focusStateOf(at(8))).toEqual({ state: "unrecorded" });
  });

  it("直前の行の②の分類・形・③が、Failure Event の trigger にそのまま入る", () => {
    const records = plantedRecords(
      GAME01_MOVES,
      { 20: engineRef(500), 22: engineRef(-300) },
      { 20: { focusTextState: "ready", focusText: "テストの文" } },
    );
    const before = records.find((r) => r.ply === 20)!;
    const { events } = diagnoseDraft("f7", records);
    const trigger = eventAt(events, 21)!.trigger;
    const expectedClass = classifyIntentStatementRow(before, { ok: true, results: detectIntents(before.sfen, before.response.moveHistory) });
    expect(trigger.opponentIntent.classification).toEqual(expectedClass);
    const intentStage = before.response.coach!.find((c) => c.stage === "opponent_intent")!;
    expect(trigger.opponentIntent.refersToIntentId).toBe(intentStage.refers_to_intent_id);
    const shapeStage = before.response.coach!.find((c) => c.stage === "current_shape")!;
    expect(trigger.shape).toEqual({ state: "recorded", status: shapeStage.status, refersToShapeId: shapeStage.refers_to_shape_id });
    expect(trigger.focus).toEqual({ state: "stated", text: "テストの文" });
  });
});

describe("報告(計画 3.2・D-1)", () => {
  it("例外は外へ出さず、種類と message を持った「数えられなかった」行にする", () => {
    const report = buildDiagnosisReport([{ kifuId: "bad", meta: undefined, records: [] }], DRAFT_RULE_1, () => {
      throw new RangeError("壊れた");
    });
    expect(report[0]?.result).toEqual({ kind: "notCounted", errorName: "RangeError", message: "壊れた" });
    expect(renderDiagnosisReport(report)).toContain("- 数えられなかった入力: bad(RangeError: 壊れた)");
  });

  it("注記(診断に使わない・draft・「測っていない」は「急落なし」ではない)を出し、0 件の列も出す", () => {
    const records = plantedRecords(GAME01_MOVES, {});
    const text = renderDiagnosisReport(buildDiagnosisReport([{ kifuId: "g", meta: undefined, records }], DRAFT_RULE_1)).join("\n");
    expect(text).toContain("この件数は診断に使わない。");
    expect(text).toContain("死因①のタグは draft。");
    expect(text).toContain("「測っていない」「測れなかった」は「急落なし」ではない。");
    expect(text).toContain("| g | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |");
  });

  it("注記(評価関数の見分け方・cp の絶対値が 30000 以上は評価値ではない)を出す(STEP D1-FIX。D1 計画 §10.10 の宿題 2 件)", () => {
    const records = plantedRecords(GAME01_MOVES, {});
    const text = renderDiagnosisReport(buildDiagnosisReport([{ kifuId: "g", meta: undefined, records }], DRAFT_RULE_1)).join("\n");
    expect(text).toContain("今の記録は入力の行の `enginePath` で見分けられる(`engine/` と `engine/nnue/`。`nn.bin` だけ差し替えると見分けられない ― P-43)");
    expect(text).not.toContain("今ある記録は駒得だけの評価で取られている");
    expect(text).toContain("cp の絶対値が 30000 以上の値は評価値ではない。");
  });

  it("比べた組が 1 つも無い記録(全行 engineReference の欄なし。game-01 と同じ形)は、急落候補とその内訳を 0 ではなく「比べる組が無い」と出す", () => {
    const records = plantedRecords(GAME01_MOVES.slice(0, 4), { 0: "absent", 2: "absent", 4: "absent" });
    const report = buildDiagnosisReport([{ kifuId: "u0", meta: undefined, records }], DRAFT_RULE_1);
    expect(report[0]?.result).toMatchObject({
      kind: "counted",
      counts: { readyRows: 3, unrecorded: 3, comparedPairs: 0, mateAfterPairs: 0, dropCandidates: 0 },
    });
    const text = renderDiagnosisReport(report).join("\n");
    expect(text).toContain("| u0 | 比べる組が無い | 比べる組が無い | 比べる組が無い | 比べる組が無い | 比べる組が無い | 比べる組が無い | 比べる組が無い | 0 | 0 | 0 |");
  });

  it("初期局面だけの記録でも落ちない(組が無い)", () => {
    const records = plantedRecords([], { 0: engineRef(0) });
    expect(records[0]?.sfen).toBe(DEFAULT_INITIAL_SFEN);
    expect(diagnoseDraft("empty", records).counts).toMatchObject({ readyRows: 1, comparedPairs: 0, events: 0 });
  });
});

describe("規則は呼び出し側が渡す(windowPlies を 5 に決め打ちしない。監査 B の必須 2)", () => {
  const records = plantedRecords(GAME01_MOVES, {
    48: engineRef(500, { afterPassMate: 3, dropCp: 350, bestmove: "2h2g" }),
    50: engineRef(-300),
  });
  const rule3 = { ...DRAFT_RULE_1, windowPlies: 3 };

  it("windowPlies 3 なら分岐点 49 の窓(50〜52)の王手は [52]、5 なら [52, 54]", () => {
    expect(eventAt(diagnoseRecords("w3", records, rule3).events, 49)?.consequences).toEqual({
      checks: [52],
      mate: null,
      windowPlies: 3,
      windowShort: false,
    });
    expect(eventAt(diagnoseRecords("w5", records, DRAFT_RULE_1).events, 49)?.consequences.checks).toEqual([52, 54]);
  });

  it("buildDiagnosisReport も渡された規則で数える", () => {
    const [row] = buildDiagnosisReport([{ kifuId: "w3", meta: undefined, records }], rule3);
    expect(row?.result.kind === "counted" ? eventAt(row.result.events, 49)?.consequences.checks : "数えられなかった").toEqual([52]);
  });
});

describe("境目(計画の「以上」「以下」。監査 B の非必須 b)", () => {
  it("直前がちょうど +300 は「うち直前が優勢」に入る", () => {
    const { counts } = diagnoseDraft("edge-adv", plantedRecords(GAME01_MOVES, { 20: engineRef(300), 22: engineRef(-100) }));
    expect(counts).toMatchObject({ dropCandidates: 1, fromAdvantage: 1 });
  });

  it("直前がちょうど +300 で窓に王手があれば、死因①(draft)の候補が付く(candidateModes の優勢の境目)", () => {
    // F-1 と同じ窓(50〜54 に 52・54 の王手)。直前 48 をちょうど +300 にする
    const { events, counts } = diagnoseDraft("edge-adv-mode", plantedRecords(GAME01_MOVES, { 48: engineRef(300), 50: engineRef(-500) }));
    expect(eventAt(events, 49)?.candidateModes).toEqual([{ mode: "mate_threat", status: "draft", matchedBy: ["cpDrop"] }]);
    expect(counts.cause1Draft).toBe(1);
  });

  it("差がちょうど −400 は急落候補に入る", () => {
    const { counts } = diagnoseDraft("edge-drop", plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(-300) }));
    expect(counts.dropCandidates).toBe(1);
  });

  it("直前の dropCp がちょうど 300 は「うち直前 dropCp ≥ 300」に入る", () => {
    const { counts } = diagnoseDraft("edge-dropcp", plantedRecords(GAME01_MOVES, { 20: engineRef(100, { dropCp: 300 }), 22: engineRef(-400) }));
    expect(counts).toMatchObject({ dropCandidates: 1, beforeDropCpAtLeast: 1 });
  });
});

describe("比べた組が 0 でも直後が mate の組がある記録(監査 B の非必須 c)", () => {
  it("急落候補は数で出す(「比べる組が無い」にしない)", () => {
    const records = plantedRecords(GAME01_MOVES.slice(0, 4), { 0: "absent", 2: engineRef(500), 4: engineRef(null, { mate: -3 }) });
    const report = buildDiagnosisReport([{ kifuId: "m1", meta: undefined, records }], DRAFT_RULE_1);
    expect(report[0]?.result).toMatchObject({ kind: "counted", counts: { comparedPairs: 0, mateAfterPairs: 1, dropCandidates: 1 } });
    expect(renderDiagnosisReport(report).join("\n")).toContain("| m1 | 1 | 1 | ");
  });
});

describe("評価値でない特別値(cp の絶対値 ≥ 30000。P-45・計画 D-6)", () => {
  // 22 は NNUE 版 claude-3-round2 ply 30 と同じ形(baseline は普通の値、afterPass が 35281、dropCp が 30457)。26 は baseline がちょうど −30000
  const records = plantedRecords(GAME01_MOVES, {
    20: engineRef(100),
    22: engineRef(-4824, { afterPassScoreCp: 35281, dropCp: 30457 }),
    24: engineRef(100),
    26: engineRef(-30000),
    28: engineRef(100),
  });

  it("baseline でも afterPass でも、特別値の行は「評価値でない」として組から外し、急落候補に入れない", () => {
    expect(evaluationOf(records.find((record) => record.ply === 22)!)).toEqual({ state: "notEvaluation" });
    expect(evaluationOf(records.find((record) => record.ply === 26)!)).toEqual({ state: "notEvaluation" });
    const pairs = pairEvaluations(readEvaluations(records));
    expect(pairs.find((pair) => pair.fromPly === 20)).toEqual({ kind: "notCompared", fromPly: 20, toPly: 22, reason: "notEvaluation", side: "to" });
    const { counts, events } = diagnoseDraft("special", records);
    expect(counts).toMatchObject({ notEvaluation: 2, dropCandidates: 0 });
    expect(events).toEqual([]);
  });

  it("状態の表に「評価値でない」の欄を別に出す", () => {
    const text = renderDiagnosisReport(buildDiagnosisReport([{ kifuId: "special", meta: undefined, records }], DRAFT_RULE_1)).join("\n");
    expect(text).toContain("| 測っていない | 評価値でない(cp の絶対値 ≥ 30000) | 比べた組 |");
    expect(text).toContain("| special | 29 | 20 | 1 | 6 | 0 | 0 | 2 | ");
  });
});

describe("入力の行(評価関数の取り違えを防ぐ。P-43)", () => {
  it("入力の行に meta の gitHead・汚れ・enginePath・nodes を出す(計算は変えない)", () => {
    const meta = {
      kind: "meta",
      kifuId: "m",
      startedAt: "t",
      gitHead: "abc123",
      enginePath: "/e/nnue/YaneuraOu-by-gcc",
      nodes: 4_000_000,
      dirty: false,
      dirtyPaths: [],
      dirtyCount: 0,
    } as MetaLine;
    const text = renderDiagnosisReport(buildDiagnosisReport([{ kifuId: "m", meta, records: plantedRecords([], { 0: engineRef(0) }) }], DRAFT_RULE_1)).join("\n");
    expect(text).toMatch(/^- m\(gitHead: abc123, .+, enginePath: \/e\/nnue\/YaneuraOu-by-gcc, nodes: 4000000\)$/m);
    const noNodes = renderDiagnosisReport(buildDiagnosisReport([{ kifuId: "m", meta: { ...meta, nodes: undefined }, records: plantedRecords([], { 0: engineRef(0) }) }], DRAFT_RULE_1)).join("\n");
    expect(noNodes).toContain("nodes: 記録していない)");
  });
});
