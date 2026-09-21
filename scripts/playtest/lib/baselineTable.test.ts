// STEP BASE(docs/STEP_BASE_PLAN_2026-09-21.md §1・§2)。枠の振り分け(A・B の境・C の重なり・「どれでもない」)、外れの 3 条件それぞれ
// (1 つだけ欠けたら false)、pool からその人を除くこと(同じラベルで止まる)、判定できない組の扱い、GATE_VALUES を読んでいること、
// lower の向き、分母 0 を、**合成の組**で見張る。エンジンは起動しない。
//
// 【正解の置き方】枠の分母・崩れ・候補の真偽は、植えた組から手で数えた値(実装の出力から写さない)。

import { describe, expect, it } from "vitest";
import {
  baselineInputProblems,
  baselineReportOf,
  FRAMES,
  renderBaselineMarkdown,
  type BaselineGame,
  type BaselineInputEntry,
  type BaselineInputGroup,
  type BaselinePerson,
  type BaselineReport,
} from "./baselineTable.js";
import type { PairRow } from "./condition.js";
import { GATE_VALUES, type GateValues } from "./gate.js";
import type { Standing } from "./standing.js";

// ---- 組の行(gate.test.ts の stub と同じ考え方。崩れ・軸の振り分けが読む欄だけ持つ) ----

interface MoveFactsPatch {
  drop?: boolean;
  capturedRole?: string | null;
  promotion?: boolean;
  kingMove?: boolean;
  toInOwnKingZone?: boolean | null;
  toInOpponentKingZone?: boolean | null;
}

const NONE_FACTS: Required<MoveFactsPatch> = { drop: false, capturedRole: null, promotion: false, kingMove: false, toInOwnKingZone: false, toInOpponentKingZone: false };

/** 崩れ・軸 A・B・C が読む欄だけの組の行。`compared=false` なら counterfactual.state を noPv 相当にして C を判定不能にする */
function pair(opts: { kifuId: string; branchPly: number; before: Standing; after?: Standing; compared?: boolean; facts?: MoveFactsPatch }): PairRow {
  const { kifuId, branchPly, before, after = before, compared = true, facts = {} } = opts;
  return {
    kifuId,
    pairKind: "compared",
    branchPly,
    fromReadyPly: branchPly - 1,
    toReadyPly: branchPly + 1,
    standingPair: { before, after },
    counterfactual: compared ? { state: "compared", actual: { userMoveFacts: { ...NONE_FACTS, ...facts } } } : { state: "unrecorded" },
  } as unknown as PairRow;
}

function gameOf(kifuId: string, pairs: PairRow[], totalMoves: number | null = 300): BaselineGame {
  return { kifuId, pairs, movesMissing: 0, rowStandings: [], totalMoves };
}

function personOf(label: string, games: BaselineGame[]): BaselinePerson {
  return { label, games };
}

const frame = (report: BaselineReport, id: string) => report.frames.find((entry) => entry.id === id)!;

// ---- A・B・C の振り分け ----

describe("枠の振り分け(計画 §1.1)", () => {
  it("FRAMES は 24 で固定(A 2・B 3・AxB 6・C 7・AxC 6)", () => {
    expect(FRAMES.length).toBe(24);
    const byAxis = (axis: string) => FRAMES.filter((entry) => entry.axis === axis).length;
    expect([byAxis("A"), byAxis("B"), byAxis("AxB"), byAxis("C"), byAxis("AxC")]).toEqual([2, 3, 6, 7, 6]);
  });

  it("軸 A: ahead → A_ahead、level → A_level、behind・未定は判定できない(不変。件数を別に出す)", () => {
    const games = [
      gameOf("g1", [pair({ kifuId: "g1", branchPly: 1, before: "ahead" }), pair({ kifuId: "g1", branchPly: 3, before: "level" }), pair({ kifuId: "g1", branchPly: 5, before: "behind" })]),
    ];
    const report = baselineReportOf(personOf("p1", games), [personOf("p2", [gameOf("h1", [])])]);
    expect(frame(report, "A_ahead").subject.denominator).toBe(1);
    expect(frame(report, "A_level").subject.denominator).toBe(1);
    expect(report.unclassified.A.subjectPairs).toBe(1);
  });

  it("軸 B: phaseOf と同じ境(< 1/3 早い・< 2/3 中・それ以外遅い)。総手数が無ければ判定できない", () => {
    const total = 300;
    const games = [
      gameOf(
        "g1",
        [
          pair({ kifuId: "g1", branchPly: 99, before: "ahead" }), // 99/300 < 1/3 → early
          pair({ kifuId: "g1", branchPly: 100, before: "ahead" }), // 100/300 = 1/3 ちょうど → mid(境を含む)
          pair({ kifuId: "g1", branchPly: 199, before: "ahead" }), // < 2/3 → mid
          pair({ kifuId: "g1", branchPly: 200, before: "ahead" }), // = 2/3 ちょうど → late
        ],
        total,
      ),
      gameOf("g2", [pair({ kifuId: "g2", branchPly: 10, before: "ahead" })], null),
    ];
    const report = baselineReportOf(personOf("p1", games), [personOf("p2", [gameOf("h1", [])])]);
    expect(frame(report, "B_early").subject.denominator).toBe(1);
    expect(frame(report, "B_mid").subject.denominator).toBe(2);
    expect(frame(report, "B_late").subject.denominator).toBe(1);
    expect(report.unclassified.B.subjectPairs).toBe(1);
    expect(report.unclassified.B.subjectGames).toBe(1);
  });

  it("軸 C: 1 手で複数の枠に重なってよい(打つ手 かつ 自玉のそば)。6 つとも偽なら「どれでもない手」だけ", () => {
    const games = [
      gameOf("g1", [
        pair({ kifuId: "g1", branchPly: 1, before: "ahead", facts: { drop: true, toInOwnKingZone: true } }),
        pair({ kifuId: "g1", branchPly: 3, before: "ahead" }), // 6 つとも偽 → none
      ]),
    ];
    const report = baselineReportOf(personOf("p1", games), [personOf("p2", [gameOf("h1", [])])]);
    expect(frame(report, "C_drop").subject.denominator).toBe(1);
    expect(frame(report, "C_ownZone").subject.denominator).toBe(1);
    expect(frame(report, "C_capture").subject.denominator).toBe(0);
    expect(frame(report, "C_none").subject.denominator).toBe(1);
  });

  it("軸 C: counterfactual.state が compared でない、または zone の欄が null なら軸 C 全体が判定できない", () => {
    const games = [
      gameOf("g1", [
        pair({ kifuId: "g1", branchPly: 1, before: "ahead", compared: false }),
        pair({ kifuId: "g1", branchPly: 3, before: "ahead", facts: { toInOwnKingZone: null } }),
      ]),
    ];
    const report = baselineReportOf(personOf("p1", games), [personOf("p2", [gameOf("h1", [])])]);
    for (const key of ["C_drop", "C_capture", "C_promotion", "C_kingMove", "C_ownZone", "C_oppZone", "C_none"]) {
      expect(frame(report, key).subject.denominator).toBe(0);
    }
    expect(report.unclassified.C.subjectPairs).toBe(2);
  });

  it("軸 C: toInOwnKingZone が非 null でも toInOpponentKingZone が null なら、軸 C の 7 枠すべてが判定できない(片方だけでは判定しない)", () => {
    const games = [gameOf("g1", [pair({ kifuId: "g1", branchPly: 1, before: "ahead", facts: { toInOwnKingZone: true, toInOpponentKingZone: null } })])];
    const report = baselineReportOf(personOf("p1", games), [personOf("p2", [gameOf("h1", [])])]);
    for (const key of ["C_drop", "C_capture", "C_promotion", "C_kingMove", "C_ownZone", "C_oppZone", "C_none"]) {
      expect(frame(report, key).subject.denominator).toBe(0);
    }
    expect(report.unclassified.C.subjectPairs).toBe(1);
  });

  it("AxB は A・B の両方が in のときだけ in。AxC(優勢 側)は「どれでもない」を含まない", () => {
    expect(FRAMES.some((entry) => entry.id === "AxC_ahead_none")).toBe(false);
    const games = [gameOf("g1", [pair({ kifuId: "g1", branchPly: 100, before: "ahead", facts: { drop: true } })], 300)];
    const report = baselineReportOf(personOf("p1", games), [personOf("p2", [gameOf("h1", [])])]);
    expect(frame(report, "AxB_ahead_mid").subject.denominator).toBe(1);
    expect(frame(report, "AxB_level_mid").subject.denominator).toBe(0);
    expect(frame(report, "AxC_ahead_drop").subject.denominator).toBe(1);
  });
});

// ---- 崩れの数え方は lib/gate.ts をそのまま使う ----

describe("崩れは lib/gate.ts の collapseOf と同じ(ahead→level は崩れ、ahead→ahead は崩れでない)", () => {
  it("A_ahead の崩れ・分母", () => {
    const games = [
      gameOf("g1", [
        pair({ kifuId: "g1", branchPly: 1, before: "ahead", after: "level" }),
        pair({ kifuId: "g1", branchPly: 3, before: "ahead", after: "ahead" }),
      ]),
    ];
    const report = baselineReportOf(personOf("p1", games), [personOf("p2", [gameOf("h1", [])])]);
    expect(frame(report, "A_ahead")).toMatchObject({ subject: { collapsed: 1, denominator: 2, gamesWithCollapse: 1 } });
  });
});

// ---- 外れの 3 条件(計画 §2)----

/** 分母 n・崩れ c 組を 1 枠(A_ahead)に、games 局(1 局に上限なく)配る。局ごとに 1 組以上の崩れを持たせて gamesWithCollapse を積む */
function bucketGames(label: string, n: number, c: number, games: number): BaselineGame[] {
  const perGame: PairRow[][] = Array.from({ length: games }, () => []);
  for (let index = 0; index < n; index += 1) {
    const g = index % games;
    perGame[g]!.push(pair({ kifuId: `${label}${g}`, branchPly: perGame[g]!.length * 100 + 1, before: "ahead", after: index < c ? "level" : "ahead" }));
  }
  return perGame.map((pairs, g) => gameOf(`${label}${g}`, pairs));
}

describe("外れの印(candidate・lower)の 3 条件。1 つだけ欠けたら false", () => {
  // 基準: subject 20 組・崩れ 10(50%・3 局)/ pool(1 人)200 組・崩れ 20(10%) → 比 5・差 40 → 3 条件とも満たす
  const POOL_OK = () => [personOf("p2", bucketGames("f", 200, 20, 5))];

  it("3 条件とも満たす → candidate true・reasons 空", () => {
    const report = baselineReportOf(personOf("p1", bucketGames("t", 20, 10, 3)), POOL_OK());
    const f = frame(report, "A_ahead");
    expect(f.candidate).toBe(true);
    expect(f.reasonsCandidateNotMet).toEqual([]);
  });

  it("条件 1(分母)だけ欠ける: subject 9 組・崩れ 9(3 局) → subjectDenominatorBelowMin", () => {
    const report = baselineReportOf(personOf("p1", bucketGames("t", 9, 9, 3)), POOL_OK());
    expect(frame(report, "A_ahead").reasonsCandidateNotMet).toContain("subjectDenominatorBelowMin");
  });

  it("条件 1(崩れのある局)だけ欠ける: subject 20 組・崩れ 10 だが 2 局に集める → subjectGamesWithCollapseBelowMin", () => {
    const report = baselineReportOf(personOf("p1", bucketGames("t", 20, 10, 2)), POOL_OK());
    expect(frame(report, "A_ahead").reasonsCandidateNotMet).toContain("subjectGamesWithCollapseBelowMin");
  });

  it("条件 2(比・差)だけ欠ける: subject 20 組・崩れ 3(15%)・分母は十分 → ratioNotMet・diffNotMet", () => {
    const report = baselineReportOf(personOf("p1", bucketGames("t", 20, 3, 3)), POOL_OK());
    const reasons = frame(report, "A_ahead").reasonsCandidateNotMet;
    expect(reasons).toContain("ratioNotMet");
  });

  it("条件 3(pool の誰と比べても高い)だけ欠ける: pool に subject と同じ率の人を混ぜる → poolMemberEqualOrHigher", () => {
    const pool = [personOf("p2", bucketGames("f", 200, 20, 5)), personOf("p3", bucketGames("s", 20, 10, 3))];
    const report = baselineReportOf(personOf("p1", bucketGames("t", 20, 10, 3)), pool);
    expect(frame(report, "A_ahead").reasonsCandidateNotMet).toContain("poolMemberEqualOrHigher");
  });

  it("分母 0 の pool の人は条件 3 の比べから外す(その人がいても candidate は変わらない)", () => {
    const withZero = [personOf("p2", bucketGames("f", 200, 20, 5)), personOf("p3", [gameOf("z1", [])])];
    const report = baselineReportOf(personOf("p1", bucketGames("t", 20, 10, 3)), withZero);
    expect(frame(report, "A_ahead").candidate).toBe(true);
    expect(frame(report, "A_ahead").poolByPerson.find((m) => m.label === "p3")).toEqual({ label: "p3", collapsed: 0, denominator: 0, ratePercent: null });
  });

  it("lower は向きが逆(基準値 ÷ その人 ≥ 比・差)。subject の率が低いほうの例で lower true・candidate false", () => {
    // subject 200 組・崩れ 20(10%)、pool 20 組・崩れ 10(50%、3 局)
    const report = baselineReportOf(personOf("p1", bucketGames("t", 200, 20, 5)), [personOf("p2", bucketGames("f", 20, 10, 3))]);
    const f = frame(report, "A_ahead");
    expect(f.candidate).toBe(false);
    expect(f.lower).toBe(true);
    expect(f.reasonsLowerNotMet).toEqual([]);
  });

  it("subject の崩れが 0(率 0)でも、G-2 と同じ特別扱い(基準値の崩れ ≥ 1 なら比の条件を満たす)で lower を判定する", () => {
    // subject 200 組・崩れ 0(3 局には崩れが無いので条件 1(崩れのある局)は満たさない → lower は false になる。
    // ここでは分母だけ十分(minTruePairs)にして cond1(分母) は満たし、cond1(崩れのある局)は自然に 0 のため false のまま。
    // rateRatioMet(baseline, subject) は subject.collapsed === 0 → baseline.collapsed>=1 で true になることだけを確かめる。
    const subject = [gameOf("t0", Array.from({ length: 20 }, (_, index) => pair({ kifuId: "t0", branchPly: index * 100 + 1, before: "ahead", after: "ahead" })))];
    const report = baselineReportOf(personOf("p1", subject), [personOf("p2", bucketGames("f", 20, 10, 3))]);
    const f = frame(report, "A_ahead");
    expect(f.reasonsLowerNotMet).not.toContain("ratioNotMet");
    expect(f.reasonsLowerNotMet).not.toContain("diffNotMet");
    expect(f.reasonsLowerNotMet).toContain("subjectGamesWithCollapseBelowMin");
  });

  it("GATE_VALUES を読んでいる: minTruePairs を 5 に下げると、9 組でも条件 1(分母)を満たす", () => {
    const values: GateValues = { ...GATE_VALUES, minTruePairs: 5 };
    const report = baselineReportOf(personOf("p1", bucketGames("t", 9, 9, 3)), POOL_OK(), values);
    expect(frame(report, "A_ahead").reasonsCandidateNotMet).not.toContain("subjectDenominatorBelowMin");
    expect(report.gateValues).toEqual(values);
  });
});

// ---- 入力の確かめ(pool からその人を除くこと・判定できない組)----

describe("baselineReportOf・baselineInputProblems の不変条件", () => {
  it("pool に person と同じラベルがあれば止まる", () => {
    expect(() => baselineReportOf(personOf("p1", [gameOf("g1", [])]), [personOf("p1", [gameOf("h1", [])])])).toThrow(/同じラベル/);
  });

  it("pool の中で同じラベルが 2 回あれば止まる", () => {
    expect(() => baselineReportOf(personOf("p1", [gameOf("g1", [])]), [personOf("p2", [gameOf("h1", [])]), personOf("p2", [gameOf("h2", [])])])).toThrow(/pool に同じラベルが 2 回/);
  });

  it("person と pool に同じ kifuId の記録があれば止まる", () => {
    expect(() => baselineReportOf(personOf("p1", [gameOf("dup", [])]), [personOf("p2", [gameOf("dup", [])])])).toThrow(/同じ kifuId/);
  });

  it("baselineInputProblems: --pool のラベルが --person と同じ・同じ sha256 の記録は止める", () => {
    const entry = (over: Partial<BaselineInputEntry>): BaselineInputEntry => ({
      name: "a", path: "a.jsonl", kifuId: "k1", sha256: "s1", meta: { kind: "meta", kifuId: "k1", startedAt: "", gitHead: null, enginePath: "", referenceNodes: 400000 } as never, errorLines: 0, ...over,
    });
    const person: BaselineInputGroup = { label: "p1", entries: [entry({})] };
    const samePool: BaselineInputGroup[] = [{ label: "p1", entries: [entry({ name: "b", path: "b.jsonl", kifuId: "k2", sha256: "s2" })] }];
    expect(baselineInputProblems(person, samePool).problems.some((p) => p.includes("同じラベル"))).toBe(true);

    const overlapPool: BaselineInputGroup[] = [{ label: "p2", entries: [entry({ name: "b", path: "b.jsonl" })] }];
    expect(baselineInputProblems(person, overlapPool).problems.some((p) => p.includes("sha256"))).toBe(true);
  });

  it("baselineInputProblems: referenceNodes がそろえば返し、そろわなければ null で問題を出す", () => {
    const entry = (kifuId: string, referenceNodes: number): BaselineInputEntry => ({
      name: kifuId, path: `${kifuId}.jsonl`, kifuId, sha256: kifuId, meta: { kind: "meta", kifuId, startedAt: "", gitHead: null, enginePath: "", referenceNodes } as never, errorLines: 0,
    });
    const person: BaselineInputGroup = { label: "p1", entries: [entry("a", 400000)] };
    const okPool: BaselineInputGroup[] = [{ label: "p2", entries: [entry("b", 400000)] }];
    expect(baselineInputProblems(person, okPool)).toEqual({ problems: [], referenceNodes: 400000 });

    const badPool: BaselineInputGroup[] = [{ label: "p2", entries: [entry("c", 100000)] }];
    const result = baselineInputProblems(person, badPool);
    expect(result.referenceNodes).toBeNull();
    expect(result.problems.some((p) => p.includes("referenceNodes がそろわない"))).toBe(true);
  });
});

describe("renderBaselineMarkdown", () => {
  it("名前・手・局面を含まない Markdown を返す(枠の数だけ行がある)", () => {
    const report = baselineReportOf(personOf("p1", [gameOf("g1", [pair({ kifuId: "g1", branchPly: 1, before: "ahead" })])]), [personOf("p2", [gameOf("h1", [])])]);
    const md = renderBaselineMarkdown(report).join("\n");
    expect(md).toContain("優勢"); // 枠のラベルは日本語(枠の id そのものは列に出さない)
    for (const forbidden of ["sfen", "SFEN", "2g2f", "kifuId"]) expect(md).not.toContain(forbidden);
  });
});
