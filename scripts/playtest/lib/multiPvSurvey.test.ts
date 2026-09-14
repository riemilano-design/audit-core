// STEP U6-T の部品の試験。計画 §6 の K-1〜K-6 をここで見張る。
// **エンジンは起動しない**(偽のエンジンを差し込む)。将棋の判断もしない。

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { GoOptions, MultiPvGoResult, MultiPvLine } from "../../../apps/server/src/engine/usiEngine.js";
import {
  boundedLongLines,
  classifyLine,
  conditionOrder,
  controlRowsOf,
  decideMinPlies,
  dedupeRoots,
  goOptionsFor,
  median,
  runSurvey,
  summarizeAnomalies,
  summarizeConditions,
  summarizeUsableCounts,
  toSurveyLines,
  unboundedLossByThreshold,
  buildSurveyReport,
  calibrationGate,
  checkCalibration,
  type SurveyCondition,
  type SurveyLine,
  type SurveySearchRow,
} from "./multiPvSurvey.js";

const STARTPOS = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
const AFTER_7G7F = "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2";
/** 先手の初手として合法で、互いに重ならない 5 手 */
const FIRST_MOVES = ["7g7f", "2g2f", "6g6f", "5g5f", "1g1f"];

const MP1: SurveyCondition = { multiPv: 1, mode: "nodes", nodes: 111 };
const MP5: SurveyCondition = { multiPv: 5, mode: "nodes", nodes: 555 };

type EngineEvent =
  | { kind: "setMultiPv"; value: number }
  | { kind: "position"; sfen: string }
  | { kind: "go"; options: GoOptions | undefined };

/** ハンドルをまたいだ go の順序を 1 本の列に積む(ハンドルごとの events では順序が見えない) */
type SharedGoLog = Array<{ root: string; handle: string }>;

/**
 * 偽のエンジン。**MultiPV の初期値は 1**(本番の `prioritizedEngine.ts:140` と同じ)。
 * 呼び出し側が setMultiPv を忘れると 1 本しか返らない。
 * `shared` を渡すと、go のたびに { 直前の position の局面, ハンドルの名前 } を共通の列に積む。
 */
function fakeEngine(
  fail: (goCount: number) => boolean = () => false,
  shared?: { log: SharedGoLog; handle: string },
): {
  engine: LowPriorityEngine;
  events: EngineEvent[];
} {
  const events: EngineEvent[] = [];
  let multiPv = 1;
  let goCount = 0;
  let root = "";
  const engine: LowPriorityEngine = {
    position: (sfen: string) => {
      root = sfen;
      events.push({ kind: "position", sfen });
    },
    setMultiPv: (value: number) => {
      multiPv = value;
      events.push({ kind: "setMultiPv", value });
    },
    goMultiPv: async (options?: GoOptions): Promise<MultiPvGoResult> => {
      events.push({ kind: "go", options });
      shared?.log.push({ root, handle: shared.handle });
      goCount += 1;
      if (fail(goCount)) throw new Error("時間切れ(偽)");
      const lines: MultiPvLine[] = FIRST_MOVES.slice(0, multiPv).map((move, index) => ({
        multipv: index + 1,
        score: { type: "cp", value: 0 },
        pv: [move, "3c3d"],
        lowerbound: false,
        upperbound: false,
      }));
      return { bestmove: lines[0]?.pv[0], ponder: undefined, lines, infoLines: [] };
    },
  };
  return { engine, events };
}

function line(overrides: Partial<SurveyLine> & { usablePlies: number }): SurveyLine {
  return {
    multipv: 1,
    scoreCp: 0,
    mate: null,
    pv: [],
    lowerbound: false,
    upperbound: false,
    truncatedAtPly: null,
    ...overrides,
  };
}

function okRow(lines: SurveyLine[], rootIndex = 0, condition: SurveyCondition = MP5): SurveySearchRow {
  return { kind: "search", rootIndex, rootSfen: STARTPOS, origins: [], condition, order: 0, elapsedMs: 0, status: "ok", lines };
}

/** 呼ぶたびに step ずつ進む偽の時計(本物の時計に依存しない) */
function tick(step = 10): () => number {
  let now = 0;
  return () => (now += step);
}

const ROOTS = [
  { sfen: STARTPOS, origins: [{ kifuId: "a", ply: 0 }] },
  { sfen: AFTER_7G7F, origins: [{ kifuId: "a", ply: 1 }] },
];

describe("局面を畳む(計画 §1.5)", () => {
  it("手数欄だけが違う sfen は同じ局面として 1 つに畳み、元の行は全部残す", () => {
    const roots = dedupeRoots([
      { kifuId: "a", ply: 0, sfen: STARTPOS },
      { kifuId: "b", ply: 0, sfen: STARTPOS.replace(/ 1$/, " 5") },
      { kifuId: "a", ply: 1, sfen: AFTER_7G7F },
    ]);
    expect(roots).toHaveLength(2);
    expect(roots[0]?.sfen).toBe(STARTPOS); // 代表は最初に現れた行の sfen(後の行で上書きしない)
    expect(roots[0]?.origins).toEqual([
      { kifuId: "a", ply: 0 },
      { kifuId: "b", ply: 0 },
    ]);
  });
});

describe("局面を畳む: 手番・持ち駒は局面の一部(計画 §1.5。独立監査 A の非必須 a)", () => {
  it("盤が同じでも、手番だけ・持ち駒だけが違う sfen は別の局面として残す", () => {
    const board = STARTPOS.split(" ")[0];
    const roots = dedupeRoots([
      { kifuId: "a", ply: 0, sfen: `${board} b - 1` },
      { kifuId: "a", ply: 1, sfen: `${board} w - 1` },
      { kifuId: "a", ply: 2, sfen: `${board} b P 1` },
    ]);
    expect(roots.map((root) => root.sfen)).toEqual([`${board} b - 1`, `${board} w - 1`, `${board} b P 1`]);
  });
});

describe("条件の順序を交互にする(計画 §4)", () => {
  it("偶数番目は [a, b]、奇数番目は [b, a]", () => {
    expect([0, 1, 2].map((i) => conditionOrder(i, ["a", "b"] as const))).toEqual([
      ["a", "b"],
      ["b", "a"],
      ["a", "b"],
    ]);
  });
});

describe("K-1: MultiPV 5 と書いた探索が、本当に MultiPV 5 で走った", () => {
  it("各 go の直前に、その条件の MultiPV が送られ、その本数が返る", async () => {
    const fakes = new Map<SurveyCondition, ReturnType<typeof fakeEngine>>([
      [MP1, fakeEngine()],
      [MP5, fakeEngine()],
    ]);
    const { rows } = await runSurvey({ clock: tick(),
      roots: ROOTS,
      conditions: [MP1, MP5],
      engineFor: (condition) => fakes.get(condition)!.engine,
    });

    for (const [condition, fake] of fakes) {
      let lastMultiPv: number | null = null;
      let goes = 0;
      for (const event of fake.events) {
        if (event.kind === "setMultiPv") lastMultiPv = event.value;
        if (event.kind === "go") {
          goes += 1;
          expect(lastMultiPv).toBe(condition.multiPv);
        }
      }
      expect(goes).toBe(ROOTS.length);
    }
    for (const row of rows) {
      expect(row.status).toBe("ok");
      if (row.status === "ok") expect(row.lines).toHaveLength(row.condition.multiPv);
    }
    expect(summarizeConditions(rows).map((s) => s.requestedMismatch)).toEqual([0, 0]);
  });
});

describe("K-2: 行に書いた条件と、実際に走った条件が一致する", () => {
  it("各条件のハンドルが受け取った go の引数は、その条件から作ったものだけ", async () => {
    const fakes = new Map<SurveyCondition, ReturnType<typeof fakeEngine>>([
      [MP1, fakeEngine()],
      [MP5, fakeEngine()],
    ]);
    const { rows } = await runSurvey({ clock: tick(),
      roots: ROOTS,
      conditions: [MP1, MP5],
      engineFor: (condition) => fakes.get(condition)!.engine,
    });

    for (const [condition, fake] of fakes) {
      const goOptions = fake.events.flatMap((event) => (event.kind === "go" ? [event.options] : []));
      expect(goOptions).toEqual(ROOTS.map(() => goOptionsFor(condition)));
    }
    // 行の条件と返った本数が食い違わない(ハンドルを入れ替えるとここが割れる)
    for (const row of rows) {
      if (row.status === "ok") expect(row.lines.length).toBe(row.condition.multiPv);
    }
  });

  it("movetime の条件は movetimeMs だけを渡す", () => {
    expect(goOptionsFor({ multiPv: 5, mode: "movetime", movetimeMs: 2000 })).toEqual({ movetimeMs: 2000 });
  });
});

// 【独立監査 A の必須 1(Z-1)】順序の交互を、関数(conditionOrder)ではなく呼び出し側で壊すと
// (runSurvey が常に conditionOrder(0, …) を呼ぶ)、K-1・K-2 はハンドルごとの出来事しか見ないので沈黙した。
// **ハンドルをまたいだ探索の順序**を、2 つの偽のエンジンが共通の 1 本の列に積んで確かめる。
describe("局面ごとに条件の順序が交互になる(runSurvey の呼び出しとして。計画 §4)", () => {
  it("局面 0 は MultiPV 1 → 5、局面 1 は MultiPV 5 → 1 の順に go が届く", async () => {
    const log: SharedGoLog = [];
    const fakes = new Map<SurveyCondition, ReturnType<typeof fakeEngine>>([
      [MP1, fakeEngine(undefined, { log, handle: "MP1" })],
      [MP5, fakeEngine(undefined, { log, handle: "MP5" })],
    ]);
    const { rows } = await runSurvey({
      clock: tick(),
      roots: ROOTS,
      conditions: [MP1, MP5],
      engineFor: (condition) => fakes.get(condition)!.engine,
    });
    expect(log).toEqual([
      { root: STARTPOS, handle: "MP1" },
      { root: STARTPOS, handle: "MP5" },
      { root: AFTER_7G7F, handle: "MP5" },
      { root: AFTER_7G7F, handle: "MP1" },
    ]);
    // 行に書いた order も、実際に届いた順と同じ
    expect(rows.map((row) => [row.rootIndex, row.condition.multiPv, row.order])).toEqual([
      [0, 1, 0],
      [0, 5, 1],
      [1, 5, 0],
      [1, 1, 1],
    ]);
  });
});

describe("K-3: 門番は「標識が先、長さが後」", () => {
  it("標識付きは長くても落とし、標識なしは長さで判定する", () => {
    expect(classifyLine({ lowerbound: true, upperbound: false, usablePlies: 20 }, 3)).toBe("rejected_bound");
    expect(classifyLine({ lowerbound: false, upperbound: true, usablePlies: 20 }, 3)).toBe("rejected_bound");
    expect(classifyLine({ lowerbound: false, upperbound: false, usablePlies: 2 }, 3)).toBe("rejected_length");
    expect(classifyLine({ lowerbound: false, upperbound: false, usablePlies: 3 }, 3)).toBe("usable");
  });
});

describe("K-4: 長さの決定は usablePlies で行う(pv.length ではない)", () => {
  // 打ち切りが無いと usablePlies と pv.length は一致して見分けがつかない。
  // 3 手目が非合法(7g の歩はもう動いている)な読み筋を使う。
  it("途中で非合法になる読み筋は、再生できた手数で門番に掛かる", () => {
    const [surveyLine] = toSurveyLines(STARTPOS, {
      bestmove: "7g7f",
      ponder: undefined,
      lines: [{ multipv: 1, score: { type: "cp", value: 0 }, pv: ["7g7f", "3c3d", "7g7f"], lowerbound: false, upperbound: false }],
      infoLines: [],
    });
    expect(surveyLine?.pv).toHaveLength(3);
    expect(surveyLine?.usablePlies).toBe(2);
    expect(surveyLine?.truncatedAtPly).toBe(3);
    expect(classifyLine(surveyLine!, 3)).toBe("rejected_length");
  });

  it("source・sfen・moveUsi は行に残さない(1 つの欄に 2 つの意味を持たせない)", () => {
    const [surveyLine] = toSurveyLines(STARTPOS, {
      bestmove: "7g7f",
      ponder: undefined,
      lines: [{ multipv: 1, score: { type: "cp", value: 0 }, pv: ["7g7f"], lowerbound: false, upperbound: false }],
      infoLines: [],
    });
    expect(Object.keys(surveyLine!)).not.toContain("source");
    expect(Object.keys(surveyLine!)).not.toContain("sfen");
    expect(Object.keys(surveyLine!)).not.toContain("moveUsi");
  });
});

describe("K-5: D-2 の式(標識付きの usablePlies の最大値 + 1)", () => {
  it("U6-L 型の固定例: 標識付きがすべて 2・標識なしが 3 以上なら 3、落ちる本は 0", () => {
    const lines = [
      line({ usablePlies: 2, lowerbound: true }),
      line({ usablePlies: 2, upperbound: true }),
      line({ usablePlies: 2, lowerbound: true }),
      line({ usablePlies: 3 }),
      line({ usablePlies: 10 }),
      line({ usablePlies: 17 }),
      line({ usablePlies: 20 }),
    ];
    expect(decideMinPlies(lines, 0.05)).toEqual({
      kind: "value",
      value: 3,
      boundedMaxUsablePlies: 2,
      unboundedLost: 0,
      unboundedTotal: 4,
      lossRatio: 0,
    });
  });

  it("落ちる標識なしの本が許容を超えたら、値を確定させない", () => {
    const lines = [line({ usablePlies: 4, lowerbound: true }), line({ usablePlies: 3 }), line({ usablePlies: 4 }), line({ usablePlies: 10 })];
    const decision = decideMinPlies(lines, 0.05);
    expect(decision.kind).toBe("loss_exceeds_tolerance");
    if (decision.kind === "loss_exceeds_tolerance") {
      expect(decision.value).toBe(5);
      expect(decision.unboundedLost).toBe(2);
    }
  });

  it("標識付きが 1 本も無ければ、式は値を出さない(0 や 1 に化けさせない)", () => {
    expect(decideMinPlies([line({ usablePlies: 5 })], 0.05)).toEqual({ kind: "no_bounded_lines", unboundedTotal: 1 });
  });

  it("D-1: 標識付きなのに長い本を数える", () => {
    const lines = [line({ usablePlies: 2, lowerbound: true }), line({ usablePlies: 3, upperbound: true }), line({ usablePlies: 9 })];
    expect(boundedLongLines(lines, 3)).toBe(1);
  });
});

describe("K-6: 失敗(時間切れ)が出たら、その後の探索をしない", () => {
  it("1 回目の go が失敗したら、失敗の行 1 行だけを残して止まる", async () => {
    const shared = fakeEngine((goCount) => goCount === 1);
    const other = fakeEngine();
    const { rows, stoppedAfterFailure } = await runSurvey({ clock: tick(),
      roots: ROOTS,
      conditions: [MP1, MP5],
      engineFor: (condition) => (condition === MP1 ? shared.engine : other.engine),
    });

    expect(stoppedAfterFailure).toBe(true);
    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({ status: "failed", lines: null });
    const goes = [...shared.events, ...other.events].filter((event) => event.kind === "go");
    expect(goes).toHaveLength(1);
  });
});

describe("「無い」の 3 種類(規則 11.6)", () => {
  it("探索して読み筋が返らなかった行は lines: []、失敗した行は lines: null", async () => {
    const empty: LowPriorityEngine = {
      position: () => {},
      setMultiPv: () => {},
      goMultiPv: async () => ({ bestmove: undefined, ponder: undefined, lines: [], infoLines: [] }),
    };
    const { rows } = await runSurvey({ clock: tick(), roots: ROOTS.slice(0, 1), conditions: [MP1, MP5], engineFor: () => ({ ...empty }) });
    expect(rows.map((row) => [row.status, row.lines])).toEqual([
      ["ok", []],
      ["ok", []],
    ]);
  });
});

describe("集計(判断はしない)", () => {
  it("S-4: 控えの候補ごとに、落ちる標識なしの本を数える", () => {
    const lines = [line({ usablePlies: 2, lowerbound: true }), line({ usablePlies: 3 }), line({ usablePlies: 5 })];
    expect(unboundedLossByThreshold(lines, [2, 3, 4, 6])).toEqual([
      { threshold: 2, lost: 0, unboundedTotal: 2 },
      { threshold: 3, lost: 0, unboundedTotal: 2 },
      { threshold: 4, lost: 1, unboundedTotal: 2 },
      { threshold: 6, lost: 2, unboundedTotal: 2 },
    ]);
  });

  it("S-6: 打ち切り・空の読み筋・先頭の手の重複を数える", () => {
    const rows = [
      okRow([
        line({ usablePlies: 2, pv: ["7g7f", "3c3d"] }),
        line({ usablePlies: 1, pv: ["7g7f", "x"], truncatedAtPly: 2 }),
        line({ usablePlies: 0, pv: [] }),
      ]),
    ];
    expect(summarizeAnomalies(rows)).toEqual({ truncated: 1, emptyPv: 1, duplicateFirstMoves: 1 });
  });

  it("中央値は偶数個なら真ん中 2 つの平均", () => {
    expect(median([3, 2])).toBe(2.5);
    expect(median([1, 3, 2])).toBe(2);
    expect(median([])).toBeNull();
  });
});

describe("D-3: 判定は出さない。分布と 0 本・1 本の局面の数を必ず並べる(2026-09-14 の司令塔の決定)", () => {
  const usable = line({ usablePlies: 5 });
  const bounded = line({ usablePlies: 2, lowerbound: true });

  it("分布・中央値・0 本・1 本だけを返し、判定の欄(holds など)を持たない", () => {
    const rows = [okRow([usable, usable, bounded]), okRow([usable, usable, usable])];
    // toEqual は余分な欄があっても割れる。判定の欄を戻すとここが鳴る
    expect(summarizeUsableCounts(rows, 3)).toEqual({
      roots: 2,
      histogram: { 2: 1, 3: 1 },
      median: 2.5,
      zero: 0,
      one: 0,
    });
  });

  it("0 本・1 本の局面の数を出す", () => {
    const rows = [okRow([bounded]), okRow([usable]), okRow([usable, usable, usable])];
    const summary = summarizeUsableCounts(rows, 3);
    expect(summary.zero).toBe(1);
    expect(summary.one).toBe(1);
  });

  it("行が 1 つも無ければ median は null(測っていないことを 0 本にしない)", () => {
    expect(summarizeUsableCounts([], 3)).toEqual({ roots: 0, histogram: {}, median: null, zero: 0, one: 0 });
  });
});

// 【変異で沈黙した 2 件を塞ぐ(規則 11.3・11.8)】
// P-6: 実物の S-1「要求本数と返った本数が違った探索」は K-1 の ② の観測だが、
//      **不一致が 0 でない場合を試験していなかった**ので、数えるのをやめても鳴らなかった。
// P-10: 許容の比較は「超えたら」(>)。**境目ちょうどの試験が無かった**ので、>= に変えても鳴らなかった。
describe("変異で沈黙した 2 件の見張り", () => {
  it("P-6: MultiPV 5 の探索で 3 本しか返らなければ、不一致を 1 と数える", () => {
    const three = [line({ usablePlies: 5 }), line({ usablePlies: 5, multipv: 2 }), line({ usablePlies: 5, multipv: 3 })];
    const [summary] = summarizeConditions([okRow(three, 0, MP5)]);
    expect(summary).toMatchObject({ requestedMismatch: 1, linesReturned: { 3: 1 } });
  });

  it("P-10: 落ちる割合が許容とちょうど同じなら、超えていないので値を出す", () => {
    const lines = [
      line({ usablePlies: 2, lowerbound: true }),
      line({ usablePlies: 2 }), // 標識なしで 3 未満 → 20 本中 1 本 = 0.05
      ...Array.from({ length: 19 }, () => line({ usablePlies: 10 })),
    ];
    const decision = decideMinPlies(lines, 0.05);
    expect(decision).toMatchObject({ kind: "value", value: 3, unboundedLost: 1, unboundedTotal: 20, lossRatio: 0.05 });
  });
});

describe("所要時間(段 B で CPU の取り合いを見る。計画 §4)", () => {
  it("go の前後で測った時間を行に書き、失敗の行にも書く", async () => {
    const readings = [100, 2100, 2200, 4300];
    let index = 0;
    const clock = () => readings[index++]!;
    const ok = fakeEngine();
    const failing = fakeEngine((goCount) => goCount === 1);
    const { rows } = await runSurvey({
      clock,
      roots: ROOTS.slice(0, 1),
      conditions: [MP1, MP5],
      engineFor: (condition) => (condition === MP1 ? ok.engine : failing.engine),
    });
    expect(rows.map((row) => [row.status, row.elapsedMs])).toEqual([
      ["ok", 2000],
      ["failed", 2100],
    ]);
  });
});

describe("報告の組み立て(buildSurveyReport)", () => {
  const PARAMS = { d1MinLength: 3, tolerance: 0.05, lossThresholds: [2, 3, 4, 5, 6] };
  const MT5: SurveyCondition = { multiPv: 5, mode: "movetime", movetimeMs: 2000 };

  it("D-2 が値を出せば、その値を門番にして D-3 を数える", () => {
    const rows = [
      okRow([line({ usablePlies: 2, lowerbound: true }), line({ usablePlies: 12 }), line({ usablePlies: 15 })], 0),
      okRow([line({ usablePlies: 9 }), line({ usablePlies: 11 }), line({ usablePlies: 14 })], 1),
    ];
    const [report] = buildSurveyReport(rows, PARAMS);
    expect(report?.d2).toMatchObject({ kind: "value", value: 3 });
    expect(report?.d3).toMatchObject({ kind: "computed", minPlies: 3, counts: { median: 2.5 } });
    expect(report?.d1BoundedLongLines).toBe(0);
    expect(report?.elapsedMs).toBeNull(); // nodes の条件では所要時間を出さない
  });

  it("D-3 の門番は D-2 が出した値を使う(3 と決め打ちしない)", () => {
    // 標識付きの最大が 4 → 値は 5。標識なし 23 本のうち 5 未満は 1 本(4.3%)で許容の内
    const rows = [
      okRow([line({ usablePlies: 4, lowerbound: true }), line({ usablePlies: 4 }), line({ usablePlies: 12 }), line({ usablePlies: 13 })], 0),
      okRow(Array.from({ length: 20 }, () => line({ usablePlies: 12 })), 1),
    ];
    const [report] = buildSurveyReport(rows, PARAMS);
    expect(report?.d2).toMatchObject({ kind: "value", value: 5 });
    expect(report?.d3).toMatchObject({ kind: "computed", minPlies: 5 });
    // 門番 5 では局面 0 の「標識なし 4 手」が落ちるので 2 本、局面 1 は 20 本
    if (report?.d3.kind === "computed") expect(report.d3.counts.histogram).toEqual({ 2: 1, 20: 1 });
  });

  it("D-2 が値を出さなければ、D-3 は計算せず理由を書く(「成り立たない」にしない)", () => {
    const [report] = buildSurveyReport([okRow([line({ usablePlies: 12 })])], PARAMS);
    expect(report?.d3).toEqual({ kind: "not_computed", reason: "no_bounded_lines" });
  });

  it("movetime の条件だけ所要時間の分布を出し、条件は行に現れた順に分ける", () => {
    const rows: SurveySearchRow[] = [
      { ...okRow([line({ usablePlies: 12 })], 0, MT5), elapsedMs: 2000 },
      { ...okRow([line({ usablePlies: 12 })], 0, MP1), elapsedMs: 1 },
      { ...okRow([line({ usablePlies: 12 })], 1, MT5), elapsedMs: 2600 },
    ];
    const reports = buildSurveyReport(rows, PARAMS);
    expect(reports.map((r) => r.condition)).toEqual(["MultiPV5/movetime2000", "MultiPV1/nodes111"]);
    expect(reports[0]?.elapsedMs).toEqual({ min: 2000, median: 2300, max: 2600 });
    expect(reports[1]?.elapsedMs).toBeNull();
  });
});

describe("段 A の校正(checkCalibration。規則 11.7)", () => {
  const EXPECTED = { boundRate: 28 / 56, boundRateTolerance: 0.15, maxBoundedPvLength: 2, minPlies: 3 };
  const bounded = () => line({ usablePlies: 2, pv: ["7g7f", "3c3d"], upperbound: true });
  const settled = () => line({ usablePlies: 12, pv: new Array(12).fill("7g7f") });

  it("既知の値の幅に入り、標識付きが 2 手以下で、式が 3 を出せば合格", () => {
    const rows = [okRow([bounded()]), okRow([settled()])];
    const result = checkCalibration(rows, 0.05, EXPECTED);
    expect(result).toMatchObject({ boundRate: { observed: 0.5, ok: true }, boundedPvLength: { observedMax: 2, ok: true }, minPlies: { ok: true }, passed: true });
  });

  it("標識付きの割合が幅を外れたら不合格(80% は 50% ± 15 の外)", () => {
    const rows = [okRow([bounded()]), okRow([bounded()]), okRow([bounded()]), okRow([bounded()]), okRow([settled()])];
    const result = checkCalibration(rows, 0.05, EXPECTED);
    expect(result.boundRate).toEqual({ observed: 0.8, ok: false });
    expect(result.passed).toBe(false);
  });

  it("標識付きの本が長ければ不合格", () => {
    const rows = [okRow([line({ usablePlies: 3, pv: ["7g7f", "3c3d", "2g2f"], lowerbound: true })]), okRow([settled()])];
    expect(checkCalibration(rows, 0.05, EXPECTED).boundedPvLength).toEqual({ observedMax: 3, ok: false });
  });

  it("行が無ければ observed も ok も null で、合格にしない", () => {
    const result = checkCalibration([], 0.05, EXPECTED);
    expect(result.boundRate).toEqual({ observed: null, ok: null });
    expect(result.passed).toBe(false);
  });
});

// 【独立監査 A の必須 2(Z-6)】CLI の中で対照を conditions[0] として選んでいたので、
// conditions[1](MultiPV 5)に変えても何も鳴らなかった。選ぶ処理を lib に出し、ここで見張る。
describe("段 A の校正の対照を選ぶ(controlRowsOf)", () => {
  const rows = [okRow([], 0, MP5), okRow([], 0, MP1), okRow([], 1, MP1), okRow([], 1, MP5)];

  it("MultiPV 1 の条件の行だけを返す(条件の並びに依存しない)", () => {
    for (const conditions of [[MP1, MP5], [MP5, MP1]]) {
      expect(controlRowsOf(rows, conditions).map((row) => [row.rootIndex, row.condition.multiPv])).toEqual([
        [0, 1],
        [1, 1],
      ]);
    }
  });

  it("MultiPV 1 の条件がちょうど 1 つでなければ例外(黙ってどちらかを選ばない)", () => {
    expect(() => controlRowsOf(rows, [MP5, { multiPv: 5, mode: "nodes", nodes: 1 }])).toThrow("ちょうど 1 つ");
    expect(() => controlRowsOf(rows, [MP1, { multiPv: 1, mode: "nodes", nodes: 1 }])).toThrow("ちょうど 1 つ");
  });

  it("行が 0 本なら空を返す(例外にしない。測っていないことは checkCalibration が null で表す)", () => {
    expect(controlRowsOf([], [MP1, MP5])).toEqual([]);
  });

  // 呼び出し側の照合(recorder.test.ts の meta 行の照合と同じ型)。**照合は片側にしか壊れない**
  // (整形を変えると緑でも落ちる。文字列を残して意味を変える書き換え ― 例えば rows を別の配列で
  // 覆い隠す ― は捕まらない)。
  it("CLI は checkCalibration に controlRowsOf の結果だけを渡し、自分で行を選ばない", () => {
    const source = readFileSync(new URL("../multipv-survey.ts", import.meta.url), "utf8");
    expect(source).toContain(
      "        ? checkCalibration(controlRowsOf(rows, stage.conditions), REPORT_PARAMS.tolerance, calibrationExpectation)\n",
    );
    expect(source.split("checkCalibration(").length - 1).toBe(1);
    expect(source).not.toMatch(/conditions\[\d\]/);
  });
});

// 【2026-09-14 の司令塔の決定】段 A は、校正の値の出どころが明示されていなければ始めない。
// コメントだけでは、取り直しを忘れた日に誰も止めない(規則 11.2 の型)。
describe("段 A の校正の出どころ(calibrationGate)", () => {
  const baseline = { marked: 28, total: 56, maxBoundedPvLength: 2, minPlies: 3 };
  const source = { recordsDir: "out/d0-nnue", gitHead: "abc123", evaluator: "sha256:0f" };

  it("source が null か欄が空なら始めない。3 つとも書けば既知の値を組み立てる", () => {
    expect(calibrationGate({ ...baseline, source: null }, 0.15)).toMatchObject({ kind: "missing_source" });
    for (const empty of [{ recordsDir: "" }, { gitHead: "" }, { evaluator: "" }]) {
      expect(calibrationGate({ ...baseline, source: { ...source, ...empty } }, 0.15).kind).toBe("missing_source");
    }
    expect(calibrationGate({ ...baseline, source }, 0.15)).toEqual({
      kind: "ready",
      source,
      expectation: { boundRate: 0.5, boundRateTolerance: 0.15, maxBoundedPvLength: 2, minPlies: 3 },
    });
  });

  // 呼び出し側の照合。**エンジンを起動する前に、実際の CALIBRATION_BASELINE で門を通し、止まったら非 0 で返す。**
  // 子プロセスで CLI を走らせる試験にはしない(門を外す変異が入ると、共有ツリーではエンジンが起動する ― P-29)。
  // 照合は片側にしか壊れない(文字列を残して意味を変える書き換えは捕まらない)。
  it("CLI は段 A でエンジンより先に門を通し、止まったら非 0 で返す。source は今は null", () => {
    const cli = readFileSync(new URL("../multipv-survey.ts", import.meta.url), "utf8");
    const gateCall = "    const gate = calibrationGate(CALIBRATION_BASELINE, CALIBRATION_BOUND_RATE_TOLERANCE);\n";
    const stop = '    if (gate.kind === "missing_source") {\n      console.error(gate.reason);\n      return 3;\n    }\n';
    expect(cli).toContain(gateCall);
    expect(cli).toContain(stop);
    expect(cli.split("calibrationGate(").length - 1).toBe(1);
    expect(cli.indexOf(gateCall)).toBeLessThan(cli.indexOf("resolveEnginePath()"));
    expect(cli.indexOf(gateCall)).toBeLessThan(cli.indexOf("new UsiEngine("));
    // 取り直すまでは埋まっていないこと(埋まっていたら、この試験を書き換えて出どころを確かめる)
    expect(cli).toContain("  source: null,\n");
  });
});

describe("条件ごとに別のハンドル(H-9)", () => {
  it("engineFor が 2 つの条件に同じハンドルを返したら、探索を 1 本もせずに止める", async () => {
    const shared = fakeEngine();
    await expect(
      runSurvey({ clock: tick(), roots: ROOTS, conditions: [MP1, MP5], engineFor: () => shared.engine }),
    ).rejects.toThrow("同じハンドル");
    expect(shared.events.filter((event) => event.kind === "go")).toHaveLength(0);
  });
});

