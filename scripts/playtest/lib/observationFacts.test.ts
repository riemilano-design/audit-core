// 束 B の試験(計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §5b の B・C)。
//
// 【材料は合成】実データは gitignore の `out/` にあるので門では読まない。**実データでの実測は道具の側で測り、記録に残す**
// (§5e の下に実測を書いた)。合成材料は**実物の形をそのまま小さくしたもの** ―
// 実物で確かめた形(`kifuId` は行に無い・`top1Side` は `candidates[0].side`・`midMoveSeconds` は `kifPly`)を使う。
// 【B と C は道具が自分で測る】`completenessProblems`・`granularityProblems` は試験の中だけでなく道具が毎回呼ぶ。
//   だから**壊した材料で落ちること**を 1 本ずつ校正する。
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { aggregatesOf } from "./observationAggregates.js";
import { provenanceOf, traceProblems } from "./observationProvenance.js";
import {
  ObservationFactsError,
  toolThresholds,
  branchRowsOf,
  aheadAtAnyPointOf,
  bandOf,
  calibrationProblems,
  collapseMarkIndexes,
  isOppositeSide,
  tagListOf,
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
  type PatientFinding,
} from "./observationFacts.js";
import { observationPacketProblems, packetIdOf } from "./observationPacket.js";

const INITIAL = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
/** 1 手目 7g7f(歩)を指した後 */
const AFTER_7G7F = "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2";

function materials(): FactsMaterials {
  return {
    patient: {
      games: [
        // **評価の列は本人の手と 1 対 1**(実物で 1242 / 1242)。g01 は 1 手目 320(優勢)→ 2 手目 −140(劣勢)で**崩れが 1 回**
        { id: "g01", no: 1, side: "先手", result: "負け", ending: "投了", plies: [0, 2], total: 3, scores: [320, -140] },
        { id: "g02", no: 2, side: "後手", result: "勝ち", plies: [1], total: 2, scores: [null] },
      ],
      events: [{ gameNo: 1, kind: "drop", ply: 3, before: 320, after: -140 }],
      // **材料が既に持っている合計**(校正の相手)。写した規則から組んだ数がここと違えば止める
      findings: [
        { kind: "phase", numbers: { fell: 1, early: 0, mid: 1, late: 0 } },
        { kind: "aheadLoss", numbers: { aheadGames: 1, aheadLossGames: 1 } },
      ],
      time: { afterLongThink: { quickAfterLongThink: { n: 7, collapsed: 2 } }, bySpent: [{ n: 40, collapsed: 5 }] },
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
        // 長考の欄は**全局が持つ**(材料の time_cause は 0 でも欄を出す)。足す行に欄が無ければ集計が例外になる
        { kifuId: "g02", timeLimitSec: 180, timeUpLoss: true, longThinkTotal: 0, forkAmongLongThink: { numerator: 0, denominator: 0 }, oppositeSideAmongForkLongThink: { numerator: 0, denominator: 0 } },
      ],
    },
    // read の position 行(`kifuId` は読み手が足したもの)。
    // **`ply` と `displayPly` をわざと違う値にする** ― 実物では 404 行のうち 263 行で違い、
    // **`ply` が本人の手と 404 / 404 一致、`displayPly` は 141 しか一致しない**(2026-09-30 の実測)。
    // 同じ値にすると、鍵の取り違えを試験が見逃す(最初その状態だった)。
    readPositions: [
      // **印は真偽の組**(実物の形。2026-09-30 の実測)。**配列にすると、組を捨てる取り違えを試験が見逃す** ―
      // 束 B は `Array.isArray` で見て 404 行すべての印を落としており、合成材料が配列だったので緑のままだった。
      { kifuId: "g01", kind: "position", ply: 3, displayPly: 7, top1Move: "8g8f", actualMove: "P*4d", top1Tags: { drop: false, capture: true, retreat: false, declinesPromotion: false, sacrifice: false, kingMove: false, givesCheck: false }, actualTags: { drop: true, capture: false, retreat: false, declinesPromotion: false, sacrifice: true, kingMove: false, givesCheck: false }, firstVisibleNodes: 2000 },
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
        // **群の名前は実物の 3 つだけ**(多数の核・それ以外・署名なし)。表に無い名前を書くと、群の合計の番人が落ちる
        g02: { proposalSignature: [], proposalSignatureNames: [], proposalSignatureClass: "署名なし", self: { recognized: false, strongRecognized: false }, opponent: { recognized: false, strongRecognized: false } },
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
    expect(rows[0]).toEqual({ gameId: "g01", no: 1, side: "先手", result: "負け", ending: "投了", ownPlyCount: 2, totalPlyCount: 3, timeLimitSec: 180, mirrored: false, aheadAtAnyPoint: true, src: "m1" });
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
    // 評価の列は 2 つしか無いので 3 手目には `scoreCp` が出ない(「無い」と「0」を混ぜない)
    expect(rows[2]).toEqual({ gameId: "g01", ply: 4, side: "own", isFork: false, collapsed: false, src: "m1" });
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
      top1Tags: ["capture"], actualTags: ["drop", "sacrifice"], firstVisibleNodes: 2000,
      top1Side: "attack", srcTop1Side: "e1", actualSide: "defense", oppositeSide: true, topGapCp: 80, srcTopGapCp: "e1",
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
    expect(rows[1]).toEqual({ gameId: "g02", longThinkCount: 0, longThinkForkCount: 0, longThinkOppositeCount: 0, timeUpLoss: true, src: "m1" });
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
  it("g1 合成材料から組んだ packet(facts + aggregates + provenance)が契約に通る", () => {
    // **集計も provenance も道具に組ませる**(手で並べた 1 行では、束 C で足した検査を通り抜けてしまう)。
    const data = materials();
    const facts = factsOf(data);
    const aggregates = aggregatesOf(facts, data);
    const inputs = [
      { path: "scripts/playtest/out/c5/patient.json", sha256: "a".repeat(64), bytes: 1 },
      { path: "scripts/playtest/out/c5/direct.json", sha256: "b".repeat(64), bytes: 2 },
      { path: "scripts/playtest/out/c5/whatif/g01.jsonl", sha256: "c".repeat(64), bytes: 3 },
      { path: "scripts/playtest/out/c5/read/g01.jsonl", sha256: "d".repeat(64), bytes: 4 },
      { path: "data/openings/onikoroshi.json", sha256: "e".repeat(64), bytes: 5 },
    ];
    const provenance = provenanceOf({
      pipelineVersion: "0000000",
      generatedAt: "2026-09-30T00:00:00Z",
      inputs,
      inputsBySource: {
        m1: ["scripts/playtest/out/c5/patient.json"],
        d1: ["scripts/playtest/out/c5/direct.json"],
        e1: ["scripts/playtest/out/c5/whatif/g01.jsonl"],
        e2: ["scripts/playtest/out/c5/read/g01.jsonl"],
        r1: ["data/openings/onikoroshi.json"],
      },
      meta: { read: [{ gitHead: "abc", values: { nodeLadder: [2000, 1000000] } }], whatif: [{ gitHead: "abc", values: { nodes: 1000000, multiPv: 5, minLossCp: 600 } }] },
      sources: data.sources,
      toolThresholds: toolThresholds(),
      recognitionReviewStatus: "draft",
    });
    const packet = {
      contract: "observation-packet",
      schemaVersion: "0.1",
      packetId: packetIdOf(facts, aggregates),
      customerRef: "c5",
      facts,
      aggregates,
      provenance,
    };
    expect(factsProblems(facts, data)).toEqual([]);
    expect(observationPacketProblems(packet)).toEqual([]);
    // **材料を読み直す口を差し替えて**追跡性まで見る(門では実ファイルを読まない)
    const bytesByPath = new Map(inputs.map((input) => [input.path, input] as const));
    const problems = traceProblems(packet, {
      repoRoot: "/(合成)",
      readBytes: (absolutePath) => {
        const found = [...bytesByPath].find(([key]) => absolutePath.endsWith(key));
        if (found === undefined) throw new Error(`知らないパス: ${absolutePath}`);
        // 指紋が合う中身を作れないので、**封の値をそのまま返す作り**にはできない ―
        // ここでは「読み直しが呼ばれた」ことと、**合わなければ落ちる**ことを下の g2 で見る
        return Buffer.alloc(found[1].bytes);
      },
    });
    // 合成の中身では指紋が合わないので、出る問題は**指紋の 5 件だけ**(辿る道そのものは通っている)
    expect(problems.filter((line) => !line.includes("指紋が変わっている"))).toEqual([]);
    expect(problems).toHaveLength(inputs.length);
  });

  it("g2 追跡性は壊すと落ちる(符号・局・名指し・読み直し)", () => {
    const data = materials();
    const facts = factsOf(data);
    const aggregates = aggregatesOf(facts, data);
    const inputs = [{ path: "x.json", sha256: "a".repeat(64), bytes: 3 }];
    const base = {
      facts,
      aggregates,
      provenance: {
        pipelineVersion: "0", generatedAt: "2026-09-30T00:00:00Z", inputs,
        sources: [
          { id: "m1", type: "material", inputPaths: ["x.json"] },
          { id: "d1", type: "material", inputPaths: ["x.json"] },
          { id: "e1", type: "engine", inputPaths: ["x.json"] },
          { id: "e2", type: "engine", inputPaths: ["x.json"] },
          { id: "r1", type: "recognition", inputPaths: ["x.json"] },
        ],
        thresholds: [{ id: "ahead_cp", value: 300, unit: "centipawns", from: "x" }],
      },
    };
    const readBytes = (): Buffer => Buffer.from("abc", "utf-8");
    const sha = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    // 指紋が合う材料を渡せば、辿る道は通る
    const good = { ...base, provenance: { ...base.provenance, inputs: [{ path: "x.json", sha256: sha, bytes: 3 }] } };
    expect(traceProblems(good, { repoRoot: "/(合成)", readBytes })).toEqual([]);
    // (1) 材料が差し替わった(指紋が違う)
    expect(traceProblems(base, { repoRoot: "/(合成)", readBytes }).join("\n")).toContain("指紋が変わっている");
    // (2) 読み直していない
    expect(traceProblems(good).join("\n")).toContain("材料を読み直していない");
    // (3) 知らない符号
    const badSrc = { ...good, aggregates: good.aggregates.map((row, index) => (index === 0 ? { ...row, src: "zz" } : row)) };
    expect(traceProblems(badSrc, { repoRoot: "/(合成)", readBytes }).join("\n")).toContain("src「zz」が provenance.sources に無い");
    // (4) derivedFrom に facts に無い局
    const badGame = { ...good, aggregates: good.aggregates.map((row, index) => (index === 0 ? { ...row, derivedFrom: ["g99"] } : row)) };
    expect(traceProblems(badGame, { repoRoot: "/(合成)", readBytes }).join("\n")).toContain("derivedFrom の局 g99 が facts.games に無い");
    // (5) どの出どころも名指ししていない材料
    const orphanInput = { ...good, provenance: { ...good.provenance, inputs: [...good.provenance.inputs, { path: "y.json", sha256: "f".repeat(64), bytes: 1 }] } };
    expect(traceProblems(orphanInput, { repoRoot: "/(合成)", readBytes }).join("\n")).toContain("y.json をどの出どころも名指ししていない");
    // (6) 数が 0 でないのに derivedFrom が空
    const emptyDerived = { ...good, aggregates: good.aggregates.map((row) => (row.id === "collapse.total" ? { ...row, derivedFrom: [] } : row)) };
    expect(traceProblems(emptyDerived, { repoRoot: "/(合成)", readBytes }).join("\n")).toContain("collapse.total に derivedFrom が無い");
  });

  it("g3 校正は写しがずれれば落ちる(崩れの合計・優勢の局)", () => {
    const data = materials();
    const facts = factsOf(data);
    expect(calibrationProblems(facts, data)).toEqual([]);
    // 材料の合計を 1 ずらす(= 写した規則がずれた状態と同じ形)
    const findingsOf = (fell: number, aheadGames: number, aheadLossGames: number): PatientFinding[] =>
      [{ kind: "phase", numbers: { fell } }, { kind: "aheadLoss", numbers: { aheadGames, aheadLossGames } }];
    const shifted = { ...data, patient: { ...data.patient, findings: findingsOf(2, 1, 1) } };
    expect(calibrationProblems(facts, shifted).join("\n")).toContain("崩れの印が 1(材料の合計は 2)");
    const shiftedAhead = { ...data, patient: { ...data.patient, findings: findingsOf(1, 2, 1) } };
    expect(calibrationProblems(facts, shiftedAhead).join("\n")).toContain("優勢になった局が 1(材料は 2)");
    // 材料に合計が無ければ「校正できていない」と言う(黙らない)
    const noFindings = { ...data, patient: { ...data.patient, findings: [] } };
    expect(calibrationProblems(facts, noFindings)).toHaveLength(2);
    // 評価の列の長さが本人の手と違えば言う
    const badScores = { ...data, patient: { ...data.patient, games: [{ ...data.patient.games[0]!, scores: [10] }, data.patient.games[1]!] } };
    expect(calibrationProblems(facts, badScores).join("\n")).toContain("評価の列が 1(本人の手は 2)");
  });

  it("g4 評価の列と崩れの印は材料の写し(null の手には欄を出さない)", () => {
    const rows = moveRowsOf(materials());
    expect(rows.map((row) => row.scoreCp)).toEqual([320, -140, undefined]);
    expect(rows.map((row) => row.collapsed)).toEqual([false, true, false]);
    const games = gameRowsOf(materials());
    expect(games.map((game) => game.aheadAtAnyPoint)).toEqual([true, false]);
  });

  it("g5 印は真偽の組から立っている名前の列にする(表に無い印は例外)", () => {
    const branches = branchRowsOf(materials());
    expect(branches[0]!.top1Tags).toEqual(["capture"]);
    expect(branches[0]!.actualTags).toEqual(["drop", "sacrifice"]);
    expect(tagListOf(["capture"], "x")).toEqual(["capture"]);
    expect(tagListOf(undefined, "x")).toBeUndefined();
    expect(() => tagListOf({ drop: true, odd: true }, "x")).toThrow(ObservationFactsError);
    // **false は落とす**(欄が在るだけでは印は立っていない ― 束 B の取り違えの中身)
    expect(tagListOf({ drop: false, capture: false }, "x")).toEqual([]);
  });

  it("g7 崩れの印と区分の規則(2026-09-30 の校正で足した ― 合成材料だけでは変異が黙った)", () => {
    // **合成材料の 25 局分の代わりにならない**: 材料側の局は評価が 2 つしか無く、
    // 「下がった」を「下がった または 同じ」に変えても**印の数が変わらなかった**(変異が黙った)。
    // 規則そのものを列で確かめる ― **境目**と**値が無い組**と**同じ区分**を 1 本ずつ。
    expect(bandOf(300)).toBe(2);
    expect(bandOf(299)).toBe(1);
    expect(bandOf(-300)).toBe(0);
    expect(bandOf(-299)).toBe(1);
    expect(bandOf(null)).toBeNull();
    expect(bandOf(undefined)).toBeNull();
    // 同じ区分のままは印にしない(ここが「下がった」の意味)
    expect([...collapseMarkIndexes([100, 100, 50])]).toEqual([]);
    expect([...collapseMarkIndexes([320, 100])]).toEqual([1]);
    expect([...collapseMarkIndexes([320, -400])]).toEqual([1]);
    expect([...collapseMarkIndexes([100, -400, -500])]).toEqual([1]);
    // 前が劣勢のときは印にしない(下がりようが無い)
    expect([...collapseMarkIndexes([-400, -500])]).toEqual([]);
    // 境目は「300 以上が優勢」
    expect([...collapseMarkIndexes([300, 299])]).toEqual([1]);
    expect([...collapseMarkIndexes([299, 298])]).toEqual([]);
    // 値が無い組は飛ばす(「無い」を「下がった」にしない)
    expect([...collapseMarkIndexes([320, null, 0])]).toEqual([]);
    expect([...collapseMarkIndexes([null, 320, 0])]).toEqual([2]);
    // 一度でも優勢(閾値以上)になったか
    expect(aheadAtAnyPointOf([0, 299])).toBe(false);
    expect(aheadAtAnyPointOf([0, 300])).toBe(true);
    expect(aheadAtAnyPointOf([null])).toBe(false);
    expect(aheadAtAnyPointOf([])).toBe(false);
  });

  it("g6 側が逆の印は 2 組の表どおり(両方・どちらでもないは逆にならない)", () => {
    expect(isOppositeSide("attack", "defense")).toBe(true);
    expect(isOppositeSide("defense", "attack")).toBe(true);
    for (const pair of [["attack", "attack"], ["attack", "both"], ["both", "defense"], ["none", "attack"], ["defense", "none"]] as const) {
      expect(isOppositeSide(pair[0], pair[1]), pair.join("→")).toBe(false);
    }
    expect(branchRowsOf(materials())[0]!.oppositeSide).toBe(true); // 第 1 候補 attack・実戦 defense
  });
});

// ==================== 閾値は確かめた写し(P-1) ====================
// Audit Core T-4/I-3 で `observationProvenance.test.ts`(束 C)から**表を組む側と一緒に**移した。
// packet に「+300 で優勢」と書いておきながら道具が別の値で数えていたら、読む側は**気づけないまま**その数を使う。
// だから `from` に書いた場所を**実際に読んで**突き合わせる(j1・j2)。j0 は人が決めた数を**字で**留める(定数から組まない)。
const REPO_ROOT = new URL("../../../", import.meta.url);

describe("閾値は確かめた写し(P-1。表は将棋側が組む)", () => {
  it("j0 表は 4 行で、値・単位・在り処は c5 の packet に出ているものと字で同じ(300・10・4・1)", () => {
    expect(toolThresholds()).toEqual([
      { id: "ahead_cp", value: 300, unit: "centipawns", from: "scripts/playtest/report-pdf/exit_groups.py AHEAD_CP" },
      { id: "long_think_sec", value: 10, unit: "seconds", from: "scripts/playtest/lib/reportData.ts TIME_VALUES.longThinkSec" },
      { id: "quick_sec", value: 4, unit: "seconds", from: "scripts/playtest/lib/reportData.ts TIME_VALUES.quickSec" },
      { id: "spent_band_1_sec", value: 1, unit: "seconds", from: "scripts/playtest/lib/reportData.ts TIME_VALUES.spentBucketsSec[0]" },
    ]);
  });

  it("j1 `from` に書いた場所を実際に読み、その値が在ることを確かめる", () => {
    const thresholds = toolThresholds();
    expect(thresholds.length).toBeGreaterThan(3);
    for (const threshold of thresholds) {
      const parts = threshold.from.split(" ");
      expect(parts, `${threshold.id} の from が「パス 定数名」の形でない`).toHaveLength(2);
      const source = readFileSync(new URL(parts[0]!, REPO_ROOT), "utf-8");
      // 定数名の最後の部分(`TIME_VALUES.spentBucketsSec[0]` → `spentBucketsSec`)
      const name = parts[1]!.split(".").pop()!.replace(/\[\d+\]$/, "");
      const lines = source.split("\n").filter((line) => line.includes(name) && !line.trimStart().startsWith("//") && !line.trimStart().startsWith("*"));
      expect(lines.length, `${parts[0]} に ${name} の行が無い`).toBeGreaterThan(0);
      const withValue = lines.filter((line) => new RegExp(`(^|[^0-9])${threshold.value}([^0-9]|$)`).test(line));
      expect(withValue.length, `${parts[0]} の ${name} の行に ${threshold.value} が無い(写しがずれている)`).toBeGreaterThan(0);
    }
  });

  it("j2 優勢の閾値は python 側(exit_groups.py)の定数と同じ値", () => {
    // **写した先が python なので、型検査では結べない** ― ここで実物を読んで突き合わせる
    const source = readFileSync(new URL("scripts/playtest/report-pdf/exit_groups.py", REPO_ROOT), "utf-8");
    const found = /^AHEAD_CP = (\d+)$/m.exec(source);
    expect(found, "exit_groups.py に AHEAD_CP の行が無い").not.toBeNull();
    const ahead = toolThresholds().find((row) => row.id === "ahead_cp")!;
    expect(ahead.value).toBe(Number(found![1]));
    expect(ahead.unit).toBe("centipawns");
  });
});
