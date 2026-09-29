// 束 B の試験(計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §5b の B・C)。
//
// 【材料は合成】実データは gitignore の `out/` にあるので門では読まない。**実データでの実測は道具の側で測り、記録に残す**
// (§5e の下に実測を書いた)。合成材料は**実物の形をそのまま小さくしたもの** ―
// 実物で確かめた形(`kifuId` は行に無い・`top1Side` は `candidates[0].side`・`midMoveSeconds` は `kifPly`)を使う。
// 【B と C は道具が自分で測る】`completenessProblems`・`granularityProblems` は試験の中だけでなく道具が毎回呼ぶ。
//   だから**壊した材料で落ちること**を 1 本ずつ校正する。
import { describe, expect, it } from "vitest";
import {
  ObservationFactsError,
  branchRowsOf,
  collapseRowsOf,
  completenessProblems,
  engineRowsOf,
  factsOf,
  factsProblems,
  gameRowsOf,
  granularityProblems,
  moveRoleOf,
  moveRowsOf,
  recognitionOf,
  timeRowsOf,
  type FactsMaterials,
} from "./observationFacts.js";
import { observationPacketProblems, packetIdOf } from "./observationPacket.js";

const INITIAL = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
/** 1 手目 7g7f(歩)を指した後 */
const AFTER_7G7F = "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2";

function materials(): FactsMaterials {
  return {
    patient: {
      games: [
        { id: "g01", no: 1, side: "先手", result: "負け", ending: "投了", plies: [0, 2], total: 3 },
        { id: "g02", no: 2, side: "後手", result: "勝ち", plies: [1], total: 2 },
      ],
      events: [{ gameNo: 1, kind: "drop", ply: 3, before: 320, after: -140 }],
    },
    sfens: {
      g01: { sfens: [INITIAL, AFTER_7G7F, INITIAL, AFTER_7G7F], moves: ["7g7f", "3c3d", "P*4d"], side: "sente" },
      g02: { sfens: [INITIAL, AFTER_7G7F, INITIAL], moves: ["7g7f", "8h3c"], side: "gote" },
    },
    timeCause: {
      games: [
        {
          kifuId: "g01", timeLimitSec: 180, timeUpLoss: false, remainingSec: 14, longThinkTotal: 5,
          phaseSpentSec: { early: 16, mid: 92, late: 58 },
          forkAmongLongThink: { numerator: 1, denominator: 5 },
          oppositeSideAmongForkLongThink: { numerator: 0, denominator: 1 },
          midMoveSeconds: [{ kifPly: 3, sec: 22, fork: true }],
        },
        { kifuId: "g02", timeLimitSec: 180, timeUpLoss: true },
      ],
    },
    // read の position 行(`kifuId` は読み手が足したもの)。
    // **`ply` と `displayPly` をわざと違う値にする** ― 実物では 404 行のうち 263 行で違い、
    // **`ply` が本人の手と 404 / 404 一致、`displayPly` は 141 しか一致しない**(2026-09-30 の実測)。
    // 同じ値にすると、鍵の取り違えを試験が見逃す(最初その状態だった)。
    readPositions: [
      { kifuId: "g01", kind: "position", ply: 3, displayPly: 7, top1Move: "8g8f", actualMove: "P*4d", top1Tags: ["capture"], actualTags: ["drop"], firstVisibleNodes: 2000 },
    ],
    whatifPositions: [
      {
        kifuId: "g01", kind: "position", ply: 3, displayPly: 7, sfen: INITIAL, actualMove: "P*4d", actualSide: "defense",
        topGapCp: 80, loss: { value: -6, cpValue: -6, isLowerBound: true },
        candidates: [{ move: "8g8f", scoreCp: 120, side: "attack", pv: ["8g8f", "3c3d"] }, { move: "1g1f", scoreCp: 40, side: "none" }],
      },
    ],
    directAnswers: [{ kifuId: "g01", displayPly: 7, actualGapCp: 126 }],
    recognition: {
      rows: {
        g01: {
          proposalSignature: ["onikoroshi"], proposalSignatureNames: ["鬼殺し"], proposalSignatureClass: "多数の核",
          self: { recognized: true, strongRecognized: true }, opponent: { recognized: true, strongRecognized: false, reached: [{ openingId: "sansan_kaku_senpo" }] },
        },
        g02: { proposalSignature: [], proposalSignatureNames: [], proposalSignatureClass: "核なし", self: { recognized: false, strongRecognized: false }, opponent: { recognized: false, strongRecognized: false } },
      },
    },
    definitions: [
      { id: "onikoroshi", name: "鬼殺し", name_kana: "おにころし", side: "self", family: "kakugawari", review_status: "draft", confidence_level: "low", scenario: "(写さない欄)", source: "(写さない欄)", leads_to_shape_ids: ["mino"], recognition_pattern: [{ order_hint: 1, piece: "桂", to: "77" }] },
    ],
    sources: { material: "m1", engine: "e1", engineShallow: "e2", direct: "d1", recognition: "r1" },
  };
}

describe("駒種の引き当て(moveRoleOf)", () => {
  it("d1 打つ手は USI の 1 文字目から(成り駒は打てない)", () => {
    expect(moveRoleOf(INITIAL, "P*4d")).toEqual({ piece: "pawn", drop: true });
    expect(moveRoleOf(INITIAL, "B*8e")).toEqual({ piece: "bishop", drop: true });
  });

  it("d2 盤の手は指す前の局面の元の升から(USI に駒種は無い)", () => {
    expect(moveRoleOf(INITIAL, "7g7f")).toEqual({ piece: "pawn", drop: false });
    expect(moveRoleOf(INITIAL, "8h7g")).toEqual({ piece: "bishop", drop: false });
    expect(moveRoleOf(INITIAL, "2h2f")).toEqual({ piece: "rook", drop: false });
    expect(moveRoleOf(INITIAL, "5i5h")).toEqual({ piece: "king", drop: false });
  });

  it("d3 元の升に駒が無ければ例外(黙って進めない)", () => {
    expect(() => moveRoleOf(INITIAL, "5e5d")).toThrow(ObservationFactsError);
  });

  it("d4 短い USI は例外", () => {
    expect(() => moveRoleOf(INITIAL, "7g")).toThrow(ObservationFactsError);
  });
});

describe("facts の 7 欄", () => {
  it("e1 局の行は材料の値を写す(持ち時間は time_cause から・向きは sfens から)", () => {
    const rows = gameRowsOf(materials());
    expect(rows).toHaveLength(2);
    expect(rows[0]).toEqual({ gameId: "g01", no: 1, side: "先手", result: "負け", ending: "投了", ownPlyCount: 2, totalPlyCount: 3, timeLimitSec: 180, mirrored: false, src: "m1" });
    expect(rows[1]!.mirrored).toBe(true);
    expect(rows[1]!.ending).toBeUndefined();
  });

  it("e2 手の行は本人の手だけ・ply は材料の添字 + 1・駒種と打つ手の区別が付く", () => {
    const rows = moveRowsOf(materials());
    expect(rows.map((row) => `${String(row.gameId)}/${String(row.ply)}`)).toEqual(["g01/1", "g01/3", "g02/2"]);
    expect(rows[0]).toMatchObject({ side: "own", usi: "7g7f", piece: "pawn", drop: false, isFork: false });
    expect(rows[1]).toMatchObject({ usi: "P*4d", piece: "pawn", drop: true, isFork: true, spentSec: 22 });
    // **秒は中盤の手だけ材料が持つ** ― 無い手に 0 を書かない(「測っていない」と「0 秒」は別)
    expect(rows[0]!.spentSec).toBeUndefined();
  });

  it("e2b 材料に手が無い本人の手(投了の分)は usi も駒種も出さない", () => {
    const data = materials();
    const patched = { ...data, patient: { ...data.patient, games: [{ ...data.patient.games[0]!, plies: [0, 2, 3] }] } };
    const rows = moveRowsOf(patched);
    expect(rows).toHaveLength(3);
    expect(rows[2]).toEqual({ gameId: "g01", ply: 4, side: "own", isFork: false, src: "m1" });
  });

  it("e3 エンジンの行は候補を写し、第 1 候補と評価を先頭から取る", () => {
    const rows = engineRowsOf(materials());
    expect(rows).toHaveLength(1);
    // **エンジンの行の ply は `displayPly`**(whatif との結合に使う鍵。既存の check_answer と同じ)
    expect(rows[0]).toMatchObject({ gameId: "g01", ply: 7, sfen: INITIAL, top1Usi: "8g8f", scoreCp: 120, actualUsi: "P*4d", src: "e1" });
    expect(rows[0]!.candidates).toEqual([
      { usi: "8g8f", scoreCp: 120, pv: ["8g8f", "3c3d"] },
      { usi: "1g1f", scoreCp: 40 },
    ]);
  });

  it("e4 分かれ道は read が骨・側は whatif の candidates[0].side・差は direct から(出どころの符号つき)", () => {
    const rows = branchRowsOf(materials());
    expect(rows).toHaveLength(1);
    expect(rows[0]).toEqual({
      gameId: "g01", ply: 3, displayPly: 7, top1Usi: "8g8f", actualUsi: "P*4d",
      top1Tags: ["capture"], actualTags: ["drop"], firstVisibleNodes: 2000,
      top1Side: "attack", srcTop1Side: "e1", actualSide: "defense", topGapCp: 80, srcTopGapCp: "e1",
      shallowVisible: true, actualGapCp: 126, srcActualGapCp: "d1", src: "e2",
    });
  });

  it("e4b whatif の loss(下限つきの組)は数として写さない", () => {
    const rows = branchRowsOf(materials());
    // **`loss` は {value, cpValue, isLowerBound} の組**で、下限のことがある ― 差は direct の値だけを使う
    expect(rows[0]!.actualGapCp).toBe(126);
  });

  it("e5 崩れの行は局番号を局 id に直す", () => {
    expect(collapseRowsOf(materials())).toEqual([{ gameId: "g01", ply: 3, beforeCp: 320, afterCp: -140, kind: "drop", src: "m1" }]);
  });

  it("e6 時間の行は分数の分子だけを数として取る", () => {
    const rows = timeRowsOf(materials());
    expect(rows[0]).toEqual({ gameId: "g01", earlySpentSec: 16, midSpentSec: 92, lateSpentSec: 58, longThinkCount: 5, longThinkForkCount: 1, longThinkOppositeCount: 0, remainingSec: 14, timeUpLoss: false, src: "m1" });
    expect(rows[1]).toEqual({ gameId: "g02", timeUpLoss: true, src: "m1" });
  });

  it("e7 認識は rows と definitions。写さない欄(scenario・source)は出さない", () => {
    const got = recognitionOf(materials());
    expect(got.rows[0]).toEqual({
      gameId: "g01", selfSignature: ["onikoroshi"], names: ["鬼殺し"], signatureClass: "多数の核",
      selfRecognized: true, selfStrongRecognized: true, opponentRecognized: true, opponentStrongRecognized: false,
      opponentSignature: ["sansan_kaku_senpo"], src: "r1",
    });
    expect(got.definitions[0]).toEqual({
      id: "onikoroshi", name: "鬼殺し", nameKana: "おにころし", side: "self", family: "kakugawari",
      reviewStatus: "draft", confidenceLevel: "low", leadsToShapeIds: ["mino"],
      recognitionPattern: [{ orderHint: 1, piece: "桂", to: "77" }], src: "r1",
    });
    expect(Object.keys(got.definitions[0]!)).not.toContain("scenario");
    expect(Object.keys(got.definitions[0]!)).not.toContain("source");
  });
});

describe("B 完全性・C 粒度(道具が毎回自分で測る)", () => {
  it("f1 そろった材料では問題が出ない", () => {
    const data = materials();
    expect(factsProblems(factsOf(data), data)).toEqual([]);
  });

  it("f2 局が欠ければ B が言う", () => {
    const data = materials();
    const facts = factsOf(data);
    (facts.games as unknown[]).pop();
    expect(completenessProblems(facts, data).join("\n")).toContain("材料の局 g02 が packet に無い");
  });

  it("f3 局が増えれば B が言う", () => {
    const data = materials();
    const facts = factsOf(data);
    (facts.games as Record<string, unknown>[]).push({ gameId: "g99", no: 99, side: "先手", result: "勝ち", ownPlyCount: 0, totalPlyCount: 0, src: "m1" });
    expect(completenessProblems(facts, data).join("\n")).toContain("packet の局 g99 が材料に無い");
  });

  it("f4 手の数が合わなければ C が言う(局ごとと合計の両方)", () => {
    const data = materials();
    const facts = factsOf(data);
    (facts.moves as unknown[]).pop();
    const problems = granularityProblems(facts, data);
    expect(problems.join("\n")).toContain("g02 の本人の手が 0(材料は 1)");
    expect(problems.join("\n")).toContain("本人の手の合計が 2(材料は 3)");
  });

  it("f5 同じ手が 2 回あれば C が言う", () => {
    const data = materials();
    const facts = factsOf(data);
    const moves = facts.moves as Record<string, unknown>[];
    moves.push({ ...moves[0]! });
    expect(granularityProblems(facts, data).join("\n")).toContain("同じ手が 2 回ある");
  });

  it("f6 分かれ道が本人の手に無い手を指していれば B が言う(鍵の取り違えを捕まえる)", () => {
    const data = materials();
    const facts = factsOf(data);
    (facts.branches as Record<string, unknown>[])[0]!.ply = 2;
    const problems = completenessProblems(facts, data);
    expect(problems.join("\n")).toContain("分かれ道 1 件の (局, 手) が本人の手に無い");
  });

  it("f7 分かれ道の印の数が行の数と合わなければ B が言う", () => {
    const data = materials();
    const facts = factsOf(data);
    (facts.moves as Record<string, unknown>[])[1]!.isFork = false;
    expect(completenessProblems(facts, data).join("\n")).toContain("分かれ道の印が付いた手が 0");
  });

  it("f7b 行が増える方向の壊れも B が言う(**監査が見つけた穴**。崩れ・時間・定義の 3 欄)", () => {
    // 2026-09-30 の独立監査が、実データで 2 通り作って**検査 0 件**を通した ―
    // 同じ定義のフォルダを 2 回渡す / 材料の 1 行を複製する。**7 欄のうち 3 欄で測っていなかった。**
    const data = materials();
    const collapseDoubled = factsOf(data);
    (collapseDoubled.collapse as Record<string, unknown>[]).push({ ...(collapseDoubled.collapse as Record<string, unknown>[])[0]! });
    expect(completenessProblems(collapseDoubled, data).join("\n")).toContain("崩れの行が 2(材料の events は 1)");

    const timeDoubled = factsOf(data);
    (timeDoubled.time as Record<string, unknown>[]).push({ ...(timeDoubled.time as Record<string, unknown>[])[0]! });
    const timeProblems = completenessProblems(timeDoubled, data).join("\n");
    expect(timeProblems).toContain("時間の行が 3(材料の time_cause は 2)");
    expect(timeProblems).toContain("時間の行に同じ局が 2 回ある");

    const definitionsDoubled = factsOf(data);
    const definitionRows = (definitionsDoubled.recognition as { definitions: Record<string, unknown>[] }).definitions;
    definitionRows.push({ ...definitionRows[0]! });
    const definitionProblems = completenessProblems(definitionsDoubled, data).join("\n");
    expect(definitionProblems).toContain("認識の定義が 2(材料は 1)");
    expect(definitionProblems).toContain("認識の定義に同じ id が 2 回ある");
  });

  it("f8 認識の行が欠ければ B が言う", () => {
    const data = materials();
    const facts = factsOf(data);
    (facts.recognition as { rows: unknown[] }).rows.pop();
    expect(completenessProblems(facts, data).join("\n")).toContain("認識の行 g02 が packet に無い");
  });
});

describe("束 A の契約との突き合わせ", () => {
  it("g1 合成材料から組んだ facts が packet の契約に通る(器と中身が食い違っていない)", () => {
    const facts = factsOf(materials());
    const aggregates = [
      {
        id: "branches.total", value: 1, unit: "positions", name: "分かれ道の総数",
        population: { from: "branches", where: [], unit: "positions" }, derivedFrom: ["g01"], src: "e2",
      },
    ];
    const packet = {
      contract: "observation-packet",
      schemaVersion: "0.1",
      packetId: packetIdOf(facts, aggregates),
      customerRef: "c5",
      facts,
      aggregates,
      provenance: {
        pipelineVersion: "0000000",
        generatedAt: "2026-09-30T00:00:00Z",
        sources: [
          { id: "m1", type: "material", path: "scripts/playtest/out/c5/x.json", sha256: "a".repeat(64) },
          { id: "e1", type: "engine", engineVersion: "(仮)" },
          { id: "e2", type: "engine", engineVersion: "(仮)" },
          { id: "d1", type: "material", path: "scripts/playtest/out/c5/y.json", sha256: "b".repeat(64) },
          { id: "r1", type: "recognition", definitionsDirs: ["data/openings"] },
        ],
        inputs: [{ path: "scripts/playtest/out/c5/x.json", sha256: "a".repeat(64), bytes: 1 }],
      },
    };
    expect(observationPacketProblems(packet)).toEqual([]);
  });
});
