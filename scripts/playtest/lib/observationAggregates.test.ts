// 束 C の試験(計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §5・§5b の A)。
//
// 【何を固定するか】(1) 数えるしくみ(条件・単位・局の数え方)、(2) 冊子の 20 の数の**組み立て方**、
// (3) **合わなければ止まる**番人、(4) 契約(schema)と道具の語彙が食い違っていないこと。
// 【期待値を書き写さない】数は**試験の中で別の道から作って**突き合わせる ―
// 期待値を書き写すと、材料が変わったときに試験だけが古くなる(5 人目で踏んだ型)。
// **ただし 1 件だけ数を直接書く**(`branches.total`)― 全部を「両方作って比べる」にすると、
// **両方が同じ間違いをしたときに緑になる**(P-159 の家族)。
// 【実データは読まない】実物の 25 局での照合は道具の `--compare` で測り、記録に残す(門は合成だけ)。
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  BOOKLET_MISSING, ObservationAggregatesError, ROW_DEFINITIONS, aggregateAgreementProblems, aggregatesOf,
  bookletAgreementProblems, bookletMissingNotes, countOf, factsIndexOf, fieldValueOf, matches, sumOf,
  timeDependentOf, type AggregateRow, type BookletNumbers,
} from "./observationAggregates.js";
import type { FactsMaterials } from "./observationFacts.js";
import { DEFAULT_SOURCES } from "./observationMaterials.js";
import { loadObservationPacketSchema } from "./observationPacket.js";

/**
 * 集計だけを見るための `facts`(**材料からではなく、行を直に置く**)。
 * 実物の形は束 B の試験が見ているので、ここでは**数え方が効いているか**だけを見る。
 * 群は 2 つに分かれ(多数の核 2 局・署名なし 1 局)、**それ以外は 0 局**(0 の行が出る形も見る)。
 */
function facts(): Record<string, unknown> {
  return {
    games: [
      { gameId: "g01", no: 1, side: "先手", result: "負け", ownPlyCount: 3, totalPlyCount: 6, timeLimitSec: 180, aheadAtAnyPoint: true, src: "m1" },
      { gameId: "g02", no: 2, side: "先手", result: "勝ち", ownPlyCount: 2, totalPlyCount: 4, timeLimitSec: 180, aheadAtAnyPoint: true, src: "m1" },
      { gameId: "g03", no: 3, side: "先手", result: "負け", ownPlyCount: 1, totalPlyCount: 2, timeLimitSec: 180, aheadAtAnyPoint: false, src: "m1" },
    ],
    moves: [
      { gameId: "g01", ply: 1, side: "own", scoreCp: 320, collapsed: false, isFork: true, src: "m1" },
      { gameId: "g01", ply: 3, side: "own", scoreCp: -140, collapsed: true, isFork: false, spentSec: 1, src: "m1" },
      { gameId: "g01", ply: 5, side: "own", scoreCp: -600, collapsed: true, isFork: false, spentSec: 3, src: "m1" },
      { gameId: "g02", ply: 1, side: "own", scoreCp: 400, collapsed: false, isFork: true, src: "m1" },
      { gameId: "g02", ply: 3, side: "own", scoreCp: 100, collapsed: true, isFork: false, src: "m1" },
      { gameId: "g03", ply: 1, side: "own", scoreCp: 0, collapsed: false, isFork: false, src: "m1" },
    ],
    engine: [{ gameId: "g01", ply: 1, sfen: "(合成)", src: "e1" }],
    time: [
      { gameId: "g01", longThinkCount: 5, longThinkForkCount: 2, longThinkOppositeCount: 1, timeUpLoss: false, src: "m1" },
      { gameId: "g02", longThinkCount: 3, longThinkForkCount: 1, longThinkOppositeCount: 0, timeUpLoss: false, src: "m1" },
      { gameId: "g03", longThinkCount: 0, longThinkForkCount: 0, longThinkOppositeCount: 0, timeUpLoss: true, src: "m1" },
    ],
    branches: [
      { gameId: "g01", ply: 1, displayPly: 1, top1Side: "attack", actualSide: "attack", oppositeSide: false, top1Tags: ["drop"], shallowVisible: true, src: "e2" },
      { gameId: "g01", ply: 1, displayPly: 3, top1Side: "attack", actualSide: "defense", oppositeSide: true, top1Tags: ["drop", "capture"], shallowVisible: true, src: "e2" },
      { gameId: "g01", ply: 1, displayPly: 5, top1Side: "defense", actualSide: "both", oppositeSide: false, top1Tags: [], shallowVisible: false, src: "e2" },
      { gameId: "g02", ply: 1, displayPly: 1, top1Side: "defense", actualSide: "attack", oppositeSide: true, top1Tags: ["drop"], shallowVisible: true, src: "e2" },
      { gameId: "g02", ply: 3, displayPly: 3, top1Side: "both", actualSide: "attack", oppositeSide: false, top1Tags: ["capture"], shallowVisible: true, src: "e2" },
      { gameId: "g03", ply: 1, displayPly: 1, top1Side: "none", actualSide: "none", oppositeSide: false, top1Tags: [], shallowVisible: false, src: "e2" },
    ],
    collapse: [{ gameId: "g01", ply: 3, beforeCp: 320, afterCp: -140, src: "m1" }],
    recognition: {
      rows: [
        { gameId: "g01", signatureClass: "多数の核", src: "r1" },
        { gameId: "g02", signatureClass: "多数の核", src: "r1" },
        { gameId: "g03", signatureClass: "署名なし", src: "r1" },
      ],
      definitions: [{ id: "onikoroshi", reviewStatus: "draft", src: "r1" }],
    },
  };
}

/**
 * 材料の代わり。`aggregatesOf` が材料を見るのは**写す 2 行の数だけ**なので、
 * そこだけを持つ最小の値にする(他の欄を作ると、見ていない欄を見ているように読める)。
 */
const materialsStub = {
  patient: { games: [], time: { afterLongThink: { quickAfterLongThink: { n: 37, collapsed: 9 } }, bySpent: [{ n: 531, collapsed: 22 }] } },
} as unknown as FactsMaterials;

function rowsById(aggregates: readonly AggregateRow[]): Map<string, AggregateRow> {
  return new Map(aggregates.map((row) => [row.id, row] as const));
}

describe("数え方のしくみ", () => {
  it("i1 条件の当たり方(値が無い行はどの演算子でも当たらない)", () => {
    expect(matches("attack", { field: "top1Side", op: "==", value: "attack" })).toBe(true);
    expect(matches("attack", { field: "top1Side", op: "!=", value: "defense" })).toBe(true);
    expect(matches("both", { field: "actualSide", op: "in", value: ["attack", "both"] })).toBe(true);
    expect(matches("none", { field: "actualSide", op: "in", value: ["attack", "both"] })).toBe(false);
    expect(matches(["drop", "capture"], { field: "top1Tags", op: "includes", value: "drop" })).toBe(true);
    expect(matches([], { field: "top1Tags", op: "includes", value: "drop" })).toBe(false);
    expect(matches(3, { field: "spentSec", op: "<=", value: 4 })).toBe(true);
    expect(matches(5, { field: "spentSec", op: "<=", value: 4 })).toBe(false);
    // **測っていない行を拾わない** ― `!=` でも当たらない(ここを緩めると分母が静かに膨らむ)
    expect(matches(undefined, { field: "spentSec", op: "<=", value: 4 })).toBe(false);
    expect(matches(undefined, { field: "spentSec", op: "!=", value: 9 })).toBe(false);
    expect(matches(null, { field: "collapsed", op: "==", value: true })).toBe(false);
    expect(() => matches(1, { field: "x", op: "≒" as never, value: 1 })).toThrow(ObservationAggregatesError);
  });

  it("i2 行に無い欄は局の行・認識の行から引く(群の条件を手の行に当てられる)", () => {
    const index = factsIndexOf(facts());
    const move = (facts().moves as Record<string, unknown>[])[0]!;
    expect(fieldValueOf(index, move, "collapsed")).toBe(false);
    expect(fieldValueOf(index, move, "result")).toBe("負け");
    expect(fieldValueOf(index, move, "signatureClass")).toBe("多数の核");
    expect(fieldValueOf(index, move, "shallowVisible")).toBeUndefined();
  });

  it("i3 単位が「局」なら局を数える(同じ局を重ねて数えない)", () => {
    const index = factsIndexOf(facts());
    const where = [{ field: "top1Tags", op: "includes" as const, value: "drop" }];
    expect(countOf(index, { from: "branches", where, unit: "positions" })).toBe(3);
    expect(countOf(index, { from: "branches", where, unit: "games" })).toBe(2);
  });

  it("i4 足す行に欄が無ければ例外(黙って 0 として足さない)", () => {
    const index = factsIndexOf(facts());
    expect(sumOf(index, { from: "time", where: [], unit: "moves" }, "longThinkCount")).toBe(8);
    expect(() => sumOf(index, { from: "time", where: [], unit: "moves" }, "spentSec")).toThrow(ObservationAggregatesError);
  });

  it("i5 時間に依る行は条件の欄から決まる(手で立てない)", () => {
    expect(timeDependentOf({ from: "time", where: [], unit: "moves" })).toBe(true);
    expect(timeDependentOf({ from: "moves", where: [{ field: "spentSec", op: "<=", value: 4 }], unit: "moves" })).toBe(true);
    expect(timeDependentOf({ from: "moves", where: [], unit: "moves" }, [{ field: "timeUpLoss", op: "==", value: true }])).toBe(true);
    expect(timeDependentOf({ from: "moves", where: [], unit: "moves" }, [], "longThinkCount")).toBe(true);
    expect(timeDependentOf({ from: "moves", where: [{ field: "collapsed", op: "==", value: true }], unit: "moves" })).toBe(false);
  });
});

describe("冊子の数の組み立て", () => {
  it("i6 数は facts から数えた値になる(別の道で作った値と突き合わせる)", () => {
    const data = facts();
    const aggregates = aggregatesOf(data, materialsStub);
    const byId = rowsById(aggregates);
    const branches = data.branches as Record<string, unknown>[];
    const moves = data.moves as Record<string, unknown>[];
    const games = data.games as Record<string, unknown>[];
    const times = data.time as Record<string, unknown>[];
    const recognition = (data.recognition as { rows: Record<string, unknown>[] }).rows;

    // **1 件だけ数を直接書く**(両方が同じ間違いをしたときに緑にならないように)
    expect(byId.get("branches.total")!.value).toBe(6);

    const attack = branches.filter((row) => row.top1Side === "attack");
    expect(byId.get("sideMatch.attack")!.denominator).toBe(attack.length);
    expect(byId.get("sideMatch.attack")!.numerator).toBe(attack.filter((row) => row.actualSide === "attack" || row.actualSide === "both").length);
    const defense = branches.filter((row) => row.top1Side === "defense");
    expect(byId.get("sideMatch.defense")!.denominator).toBe(defense.length);
    expect(byId.get("sideMatch.defense")!.numerator).toBe(defense.filter((row) => row.actualSide === "defense" || row.actualSide === "both").length);
    expect(byId.get("sideMatch.oppositeAll")!.denominator).toBe(attack.length + defense.length);
    expect(byId.get("sideMatch.oppositeAll")!.numerator).toBe(branches.filter((row) => row.oppositeSide === true).length);

    expect(byId.get("branches.shallowVisible")!.value).toBe(branches.filter((row) => row.shallowVisible === true).length);
    expect(byId.get("branches.shallowVisibleGames")!.value).toBe(new Set(branches.filter((row) => row.shallowVisible === true).map((row) => row.gameId)).size);
    const drops = branches.filter((row) => row.shallowVisible === true && (row.top1Tags as string[]).includes("drop"));
    expect(byId.get("repro.top1Drop.positions")!.value).toBe(drops.length);
    expect(byId.get("repro.top1Drop.games")!.value).toBe(new Set(drops.map((row) => row.gameId)).size);

    expect(byId.get("collapse.total")!.value).toBe(moves.filter((row) => row.collapsed === true).length);
    const ahead = games.filter((row) => row.aheadAtAnyPoint === true);
    expect(byId.get("aheadThenLost")!.denominator).toBe(ahead.length);
    expect(byId.get("aheadThenLost")!.numerator).toBe(ahead.filter((row) => row.result === "負け").length);

    expect(byId.get("longThink.total")!.value).toBe(times.reduce((total, row) => total + (row.longThinkCount as number), 0));
    expect(byId.get("longThink.fork")!.value).toBe(times.reduce((total, row) => total + (row.longThinkForkCount as number), 0));
    expect(byId.get("longThink.opposite")!.value).toBe(times.reduce((total, row) => total + (row.longThinkOppositeCount as number), 0));

    const core = recognition.filter((row) => row.signatureClass === "多数の核").map((row) => row.gameId);
    expect(byId.get("groups.core.games")!.value).toBe(core.length);
    expect(byId.get("groups.core.collapses")!.value).toBe(moves.filter((row) => row.collapsed === true && core.includes(row.gameId)).length);
    // **0 の群も行が出る**(局が 1 つも無い群を黙って落とさない)
    expect(byId.get("groups.other.games")!.value).toBe(0);
    expect(byId.get("groups.other.games")!.derivedFrom).toEqual([]);
  });

  it("i7 写した 2 行は数え直せない印と理由を持ち、局は全局(母集団の where は定義の一部)", () => {
    const data = facts();
    const byId = rowsById(aggregatesOf(data, materialsStub));
    const quick = byId.get("time.quickAfterLongThink")!;
    expect(quick.recountable).toBe(false);
    expect(quick.numerator).toBe(9);
    expect(quick.denominator).toBe(37);
    expect(quick.recountNote).toContain("中盤の手だけ");
    expect(quick.derivedFrom).toEqual(["g01", "g02", "g03"]);
    const band = byId.get("time.bySpent0to1")!;
    expect(band.recountable).toBe(false);
    expect([band.numerator, band.denominator]).toEqual([22, 531]);
    // **数え直せる行には理由を付けない**(印と理由が食い違う道を塞ぐ)
    expect(byId.get("collapse.total")!.recountNote).toBeUndefined();
    expect(byId.get("collapse.total")!.recountable).toBe(true);
    // 材料に数が無ければ例外(黙って 0 を書かない)
    expect(() => aggregatesOf(data, { patient: { games: [] } } as unknown as FactsMaterials)).toThrow(ObservationAggregatesError);
  });

  it("i8 合わなければ止まる(5 通りに壊して、それぞれ言わせる)", () => {
    const data = facts();
    const aggregates = aggregatesOf(data, materialsStub);
    expect(aggregateAgreementProblems(aggregates, data)).toEqual([]);
    const shift = (id: string, change: Partial<AggregateRow>): AggregateRow[] =>
      aggregates.map((row) => (row.id === id ? { ...row, ...change } : row));

    // (a) 分子を 1 ずらす(別の道で数えた 2 行の和と合わなくなる)
    expect(aggregateAgreementProblems(shift("sideMatch.oppositeAll", { numerator: 1 }), data).join("\n")).toContain("側が逆の局面が 1");
    // (b) 群の数を 1 ずらす(群の合計が局の数と合わなくなる)
    expect(aggregateAgreementProblems(shift("groups.core.games", { value: 1 }), data).join("\n")).toContain("群の局数の合計が 2");
    // (c) 群の崩れを 1 ずらす(全体の崩れと合わなくなる)
    expect(aggregateAgreementProblems(shift("groups.core.collapses", { value: 1 }), data).join("\n")).toContain("群ごとの崩れの合計が");
    // (d) 単位を入れ替える(局が局面より多くなる)
    expect(aggregateAgreementProblems(shift("repro.top1Drop.games", { value: 99 }), data).join("\n")).toContain("単位が入れ替わっている");
    // (e) 数え直せない印の理由を外す / timeDependent を手で立てる
    expect(aggregateAgreementProblems(shift("time.bySpent0to1", { recountNote: undefined }), data).join("\n")).toContain("理由が書かれていない");
    expect(aggregateAgreementProblems(shift("collapse.total", { timeDependent: true }), data).join("\n")).toContain("timeDependent が条件の欄と合わない");
    // (f) 分子が分母を超える
    expect(aggregateAgreementProblems(shift("sideMatch.attack", { numerator: 99 }), data).join("\n")).toContain("分子 99 が分母");
  });
});

describe("冊子との照合(試験 A)", () => {
  /** 合成の集計から、そのまま「冊子の側の数」を作る(数が合っている状態の相手) */
  function bookletOf(aggregates: readonly AggregateRow[]): BookletNumbers {
    const byId = rowsById(aggregates);
    const value = (id: string): number => byId.get(id)!.value!;
    const group = (key: string) => ({
      key,
      games: value(`groups.${key}.games`),
      collapses: value(`groups.${key}.collapses`),
      aheadGames: byId.get(`groups.${key}.aheadThenLost`)!.denominator!,
      aheadLossGames: byId.get(`groups.${key}.aheadThenLost`)!.numerator!,
    });
    return {
      actionFractions: [
        { id: "M4", label: "攻め", numerator: byId.get("sideMatch.attack")!.numerator, denominator: byId.get("sideMatch.attack")!.denominator, unit: "局面" },
        { id: "M4", label: "自玉側", numerator: byId.get("sideMatch.defense")!.numerator, denominator: byId.get("sideMatch.defense")!.denominator, unit: "局面" },
        { id: "M5", label: "", numerator: byId.get("time.quickAfterLongThink")!.numerator, denominator: byId.get("time.quickAfterLongThink")!.denominator, unit: "手" },
      ],
      denominators: [
        { number: byId.get("sideMatch.oppositeAll")!.denominator, unit: "局面", from: "第 1 候補の側が 1 つだった分かれ道(長考で絞らない)" },
        { number: byId.get("time.bySpent0to1")!.denominator, unit: "手", from: "「0〜1 秒で指した手のうち崩れた手」の分母" },
        { number: value("longThink.total"), unit: "手", from: "10 秒以上考えた手(全部)" },
        { number: value("longThink.fork"), unit: "手", from: "10 秒以上考えた手のうち、分かれ道だった手" },
      ],
      repro: [{ phrase: "第 1 候補が駒を打つ手", positions: value("repro.top1Drop.positions"), games: value("repro.top1Drop.games") }],
      openingGroups: [group("core"), group("other"), group("noSignature")],
      findings: [
        { kind: "phase", numbers: { fell: value("collapse.total") } },
        { kind: "aheadLoss", numbers: { aheadGames: byId.get("aheadThenLost")!.denominator!, aheadLossGames: byId.get("aheadThenLost")!.numerator! } },
      ],
      directCounts: {
        totalForkCount: value("branches.total"),
        totalCount: value("branches.shallowVisible"),
        gamesCount: value("branches.shallowVisibleGames"),
      },
    };
  }

  it("i9 数が合っていれば 0 件・1 つずらせばその行を名指しする", () => {
    const aggregates = aggregatesOf(facts(), materialsStub);
    const booklet = bookletOf(aggregates);
    expect(bookletAgreementProblems(aggregates, booklet)).toEqual([]);
    const shifted = aggregates.map((row) => (row.id === "sideMatch.attack" ? { ...row, numerator: (row.numerator ?? 0) + 1 } : row));
    const problems = bookletAgreementProblems(shifted, booklet);
    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain("sideMatch.attack の numerator");
  });

  it("i10 照合の相手が材料に無ければ言う(黙って対象から外さない)", () => {
    const aggregates = aggregatesOf(facts(), materialsStub);
    const booklet = bookletOf(aggregates);
    const withoutCounts = { ...booklet, directCounts: {} };
    expect(bookletAgreementProblems(aggregates, withoutCounts).join("\n")).toContain("照合する相手(direct_answers の totalForkCount)が材料に無い");
    // 同じ言葉の行が 2 つあると引き当てられない(どちらを採ってもよいことにしない)
    const doubled = { ...booklet, denominators: [...booklet.denominators!, ...booklet.denominators!] };
    expect(bookletAgreementProblems(aggregates, doubled).join("\n")).toContain("照合する相手(数の出どころ");
    // 相手が原理的に無い 2 つは、問題ではなく**報告**に出る
    const notes = bookletMissingNotes(aggregates);
    expect(notes).toHaveLength(BOOKLET_MISSING.length);
    expect(notes.join("\n")).toContain("JSON に残っていない");
  });

  it("i11 照合の表に載せた id は、必ず集計の行として在る", () => {
    const ids = new Set(ROW_DEFINITIONS.map((row) => row.id));
    for (const missing of BOOKLET_MISSING) expect(ids.has(missing.id), missing.id).toBe(true);
    expect(ids.size).toBe(ROW_DEFINITIONS.length); // id が重なっていない
  });
});

describe("契約(schema)と道具の語彙が合っているか", () => {
  it("i12 母集団の欄名・単位・出どころの符号が、すべて契約に在るもの", () => {
    const schema = loadObservationPacketSchema() as unknown as {
      properties: { aggregates: { items: { properties: {
        unit: { enum: string[] };
        sumField: { enum: string[] };
        population: { required: string[]; properties: { from: { enum: string[] }; where: { items: { properties: { field: { enum: string[] }; op: { enum: string[] } } } }; unit: { enum: string[] } } };
      } } } };
    };
    const items = schema.properties.aggregates.items.properties;
    const fields = new Set(items.population.properties.where.items.properties.field.enum);
    const ops = new Set(items.population.properties.where.items.properties.op.enum);
    const froms = new Set(items.population.properties.from.enum);
    const units = new Set(items.unit.enum);
    const sources = new Set(Object.values(DEFAULT_SOURCES));
    for (const row of ROW_DEFINITIONS) {
      expect(froms.has(row.population.from), `${row.id} の from`).toBe(true);
      expect(units.has(row.population.unit), `${row.id} の母集団の単位`).toBe(true);
      expect(units.has(row.unit), `${row.id} の単位`).toBe(true);
      expect(sources.has(row.src), `${row.id} の src`).toBe(true);
      for (const extra of row.srcExtra ?? []) expect(sources.has(extra), `${row.id} の srcExtra`).toBe(true);
      for (const condition of [...row.population.where, ...(row.numeratorWhere ?? [])]) {
        expect(fields.has(condition.field), `${row.id} の欄 ${condition.field}`).toBe(true);
        expect(ops.has(condition.op), `${row.id} の演算子 ${condition.op}`).toBe(true);
      }
      if (row.sumField !== undefined) expect(items.sumField.enum.includes(row.sumField), `${row.id} の sumField`).toBe(true);
    }
  });

  it("i13 手の印の語彙は、道具の定数と契約で同じ", () => {
    // `lib/read.ts` の `READ_MOVE_MARK_KEYS` は型と機械で結んである(欄が増えれば型検査が落ちる)。
    // **契約の側も同じ並びであること**をここで固定する(2 か所でずれる道を塞ぐ)。
    const source = readFileSync(new URL("./read.ts", import.meta.url), "utf-8");
    const found = /export const READ_MOVE_MARK_KEYS = \[([^\]]+)\]/.exec(source);
    expect(found, "READ_MOVE_MARK_KEYS が lib/read.ts に無い").not.toBeNull();
    const keys = [...found![1]!.matchAll(/"([a-zA-Z]+)"/g)].map((match) => match[1]);
    const schema = loadObservationPacketSchema() as unknown as {
      properties: { facts: { properties: { branches: { items: { properties: { top1Tags: { items: { enum: string[] } }; actualTags: { items: { enum: string[] } } } } } } } };
    };
    const branches = schema.properties.facts.properties.branches.items.properties;
    expect(branches.top1Tags.items.enum).toEqual(keys);
    expect(branches.actualTags.items.enum).toEqual(keys);
  });
});
