// 次世代パイプライン Phase A の束 C(計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §2.3・§2.4・§8)。
// **冊子に出ている数を、`facts` から数えて `aggregates` にする。**
//
// 【顧客の PDF にどう出るか】**今は何も変わらない。** 冊子の数は今のまま同じ値で出る。
//   変わるのは「その数がどの行から出たか」を機械で辿れることだけ(人間の指示の試験 A・D)。
// 【新しい判定を作らない】数えるのに使う条件は `facts` に在る欄だけ(`where` の欄名は schema の enum が縛る)。
//   側・崩れ・優勢の規則は既存の道具の写しで、写しは `lib/observationFacts.ts` 側に置いて校正してある。
// 【数を書き写さない】**行の数は必ずこの層が `facts` から数える。**
//   例外は 2 行だけ(時間の 9 / 37 と 22 / 531)― 材料の秒が中盤の手だけなので数え直せない。
//   その 2 行は材料の値を写し、`recountable: false` と理由を付ける(P-4。人間の了承 2026-09-30)。
// 【合わなければ止まる】群に割った数の合計・側の 2 通りの数え方が食い違えば `aggregateAgreementProblems` が言う。
//   既存の `exit_groups.group_rows` と同じ形の番人(あちらは 133 ≠ 79 でずれを見つけた)。
import type { FactsMaterials } from "./observationFacts.js";

export class ObservationAggregatesError extends Error {
  override name = "ObservationAggregatesError";
}

export type ConditionOp = "==" | "!=" | ">=" | "<=" | ">" | "<" | "includes" | "in";
export type Condition = { readonly field: string; readonly op: ConditionOp; readonly value: unknown };
export type PopulationFrom = "games" | "moves" | "engine" | "time" | "branches" | "collapse" | "recognition";
export type AggregateUnit = "positions" | "games" | "moves" | "seconds" | "centipawns";
export type Population = { readonly from: PopulationFrom; readonly where: readonly Condition[]; readonly unit: AggregateUnit };

export type AggregateRow = {
  readonly id: string;
  readonly name: string;
  readonly unit: AggregateUnit;
  readonly population: Population;
  readonly numeratorWhere?: readonly Condition[];
  readonly sumField?: string;
  readonly numerator?: number;
  readonly denominator?: number;
  readonly value?: number;
  readonly derivedFrom: readonly string[];
  readonly src: string;
  readonly srcExtra?: readonly string[];
  readonly recountable: boolean;
  readonly recountNote?: string;
  readonly timeDependent: boolean;
};

/**
 * **時間に依る欄**(P-2。設計セッションの提案 → 束 C で受けた)。
 * `timeDependent` は手で立てず、`population` と `numeratorWhere` の欄名・`from` から機械で決める。
 */
export const TIME_FIELDS: ReadonlySet<string> = new Set([
  "spentSec", "longThinkCount", "longThinkForkCount", "longThinkOppositeCount", "timeUpLoss", "timeLimitSec",
]);

/** 行に無くても**局から引ける欄**(局の行に在る欄)。行の `gameId` で引く */
const GAME_LEVEL_FIELDS: ReadonlySet<string> = new Set([
  "side", "result", "timeLimitSec", "aheadAtAnyPoint", "ownPlyCount", "totalPlyCount", "no", "ending", "mirrored",
]);
/** 行に無くても**認識の行から引ける欄** */
const RECOGNITION_FIELDS: ReadonlySet<string> = new Set(["signatureClass", "reviewStatus"]);

type Row = Record<string, unknown>;

/** `facts` を引きやすくした索引(局の欄・認識の欄を、どの行からでも引けるようにする) */
export type FactsIndex = {
  readonly facts: Record<string, unknown>;
  readonly gameById: Map<string, Row>;
  readonly recognitionById: Map<string, Row>;
};

export function factsIndexOf(facts: Record<string, unknown>): FactsIndex {
  const gameById = new Map<string, Row>();
  for (const row of rowsOf(facts, "games")) gameById.set(String(row.gameId), row);
  const recognitionById = new Map<string, Row>();
  for (const row of rowsOf(facts, "recognition")) recognitionById.set(String(row.gameId), row);
  return { facts, gameById, recognitionById };
}

export function rowsOf(facts: Record<string, unknown>, from: PopulationFrom): Row[] {
  if (from === "recognition") {
    const recognition = (facts.recognition ?? {}) as { rows?: Row[] };
    return recognition.rows ?? [];
  }
  const rows = facts[from];
  if (!Array.isArray(rows)) throw new ObservationAggregatesError(`facts に ${from} が無い`);
  return rows as Row[];
}

/**
 * 行の欄の値。行に無ければ**局の行・認識の行**から引く(群の条件を手の行に当てられるようにするため)。
 * **`facts` に無い欄は `undefined`** ― 条件はどの演算子でも当たらない(下の `matches`)。
 */
export function fieldValueOf(index: FactsIndex, row: Row, field: string): unknown {
  if (Object.hasOwn(row, field)) return row[field];
  const gameId = row.gameId === undefined ? undefined : String(row.gameId);
  if (gameId !== undefined && GAME_LEVEL_FIELDS.has(field)) return index.gameById.get(gameId)?.[field];
  if (gameId !== undefined && RECOGNITION_FIELDS.has(field)) return index.recognitionById.get(gameId)?.[field];
  return undefined;
}

/**
 * 条件に当たるか。**値が無い行はどの演算子でも当たらない**(`!=` も当たらない) ―
 * 「測っていない」行を条件で拾うと、分母が静かに膨らむ(秒が中盤だけ、という実物の形で必ず踏む)。
 */
export function matches(value: unknown, condition: Condition): boolean {
  if (value === undefined || value === null) return false;
  switch (condition.op) {
    case "==": return value === condition.value;
    case "!=": return value !== condition.value;
    case ">=": case "<=": case ">": case "<": {
      if (typeof value !== "number" || typeof condition.value !== "number") return false;
      if (condition.op === ">=") return value >= condition.value;
      if (condition.op === "<=") return value <= condition.value;
      if (condition.op === ">") return value > condition.value;
      return value < condition.value;
    }
    case "includes": return Array.isArray(value) && value.includes(condition.value);
    case "in": return Array.isArray(condition.value) && condition.value.includes(value);
    default: throw new ObservationAggregatesError(`知らない演算子: ${String(condition.op)}`);
  }
}

export function selectRows(index: FactsIndex, population: Population, extra: readonly Condition[] = []): Row[] {
  const conditions = [...population.where, ...extra];
  return rowsOf(index.facts, population.from).filter((row) => conditions.every((condition) => matches(fieldValueOf(index, row, condition.field), condition)));
}

/**
 * 母集団の数。**単位が「局」で行が局でないときは、局の数を数える**(同じ局を重ねて数えない)。
 * これが「22 の 2 つの意味」(局面 54 と 局 22)を機械で分ける線である。
 */
export function countOf(index: FactsIndex, population: Population, extra: readonly Condition[] = []): number {
  const rows = selectRows(index, population, extra);
  if (population.unit === "games" && population.from !== "games") {
    return new Set(rows.map((row) => String(row.gameId))).size;
  }
  return rows.length;
}

export function gameIdsOf(rows: readonly Row[]): string[] {
  return [...new Set(rows.map((row) => String(row.gameId)))].sort();
}

/** 欄を足した数(行の数え上げではない行。長考の 3 行がこれ)。**欄が無い行があれば例外** */
export function sumOf(index: FactsIndex, population: Population, field: string): number {
  let total = 0;
  for (const row of selectRows(index, population)) {
    const value = fieldValueOf(index, row, field);
    if (typeof value !== "number") throw new ObservationAggregatesError(`${population.from} の行に ${field} が無い(${String(row.gameId)}) ― 足せない`);
    total += value;
  }
  return total;
}

export function timeDependentOf(population: Population, numeratorWhere: readonly Condition[] = [], sumField?: string): boolean {
  if (population.from === "time") return true;
  if (sumField !== undefined && TIME_FIELDS.has(sumField)) return true;
  return [...population.where, ...numeratorWhere].some((condition) => TIME_FIELDS.has(condition.field));
}

// ==================== 行の定義(冊子に出ている数。1 つ残らず) ====================
//
// **値はここに書かない。**書くのは「何を数えるか」だけで、数は `facts` から取る
// (数を書き写すと、材料が変わったときに packet だけが古くなる ― 5 人目で踏んだ型)。
// 例外の 2 行は `fromMaterial` を持ち、材料の値を写す(数え直せない理由つき)。

type MaterialNumbers = { readonly numerator: number; readonly denominator: number };

type RowDefinition = {
  readonly id: string;
  readonly name: string;
  readonly unit: AggregateUnit;
  readonly population: Population;
  readonly numeratorWhere?: readonly Condition[];
  readonly sumField?: string;
  readonly src: string;
  readonly srcExtra?: readonly string[];
  readonly recountNote?: string;
  readonly fromMaterial?: (materials: FactsMaterials) => MaterialNumbers | undefined;
};

const SIGNATURE_GROUPS = [
  { key: "core", signature: "多数の核" },
  { key: "other", signature: "それ以外" },
  { key: "noSignature", signature: "署名なし" },
] as const;

/** 群の鍵 → 集計の id の部分(`groups.core.games` など) */
function groupDefinitions(): RowDefinition[] {
  const rows: RowDefinition[] = [];
  for (const group of SIGNATURE_GROUPS) {
    rows.push({
      id: `groups.${group.key}.games`,
      name: `序盤の駒の動きの型で分けた群「${group.signature}」の局`,
      unit: "games",
      population: { from: "recognition", where: [{ field: "signatureClass", op: "==", value: group.signature }], unit: "games" },
      src: "r1",
    });
    rows.push({
      id: `groups.${group.key}.collapses`,
      name: `群「${group.signature}」の局で、評価の区分が下がった手`,
      unit: "moves",
      population: {
        from: "moves",
        where: [{ field: "signatureClass", op: "==", value: group.signature }, { field: "collapsed", op: "==", value: true }],
        unit: "moves",
      },
      src: "m1",
      srcExtra: ["r1"],
    });
    rows.push({
      id: `groups.${group.key}.aheadThenLost`,
      name: `群「${group.signature}」で一度は優勢になった局のうち、負けた局`,
      unit: "games",
      population: {
        from: "games",
        where: [{ field: "signatureClass", op: "==", value: group.signature }, { field: "aheadAtAnyPoint", op: "==", value: true }],
        unit: "games",
      },
      numeratorWhere: [{ field: "result", op: "==", value: "負け" }],
      src: "m1",
      srcExtra: ["r1"],
    });
  }
  return rows;
}

export const ROW_DEFINITIONS: readonly RowDefinition[] = [
  // ---- 分かれ道の側(冊子の 65 / 107・76 / 132・51 / 239) ----
  {
    id: "sideMatch.attack",
    name: "第 1 候補の側が攻めだった分かれ道のうち、実戦も攻めの側だった局面",
    unit: "positions",
    population: { from: "branches", where: [{ field: "top1Side", op: "==", value: "attack" }], unit: "positions" },
    numeratorWhere: [{ field: "actualSide", op: "in", value: ["attack", "both"] }],
    src: "e1",
  },
  {
    id: "sideMatch.defense",
    name: "第 1 候補の側が自玉側だった分かれ道のうち、実戦も自玉側だった局面",
    unit: "positions",
    population: { from: "branches", where: [{ field: "top1Side", op: "==", value: "defense" }], unit: "positions" },
    numeratorWhere: [{ field: "actualSide", op: "in", value: ["defense", "both"] }],
    src: "e1",
  },
  {
    id: "sideMatch.oppositeAll",
    name: "第 1 候補の側が攻め・自玉側のどちらか 1 つだった分かれ道のうち、実戦が逆の側だった局面",
    unit: "positions",
    population: { from: "branches", where: [{ field: "top1Side", op: "in", value: ["attack", "defense"] }], unit: "positions" },
    numeratorWhere: [{ field: "oppositeSide", op: "==", value: true }],
    src: "e1",
  },
  // **同じ数に別の道で着く 2 行**(印を使わず `==` だけで数える)。
  // 上の `oppositeAll` の分子と、この 2 行の分子の和が合うことを `aggregateAgreementProblems` が見る。
  {
    id: "sideMatch.attackToDefense",
    name: "第 1 候補の側が攻めで、実戦は自玉側だった局面",
    unit: "positions",
    population: { from: "branches", where: [{ field: "top1Side", op: "==", value: "attack" }], unit: "positions" },
    numeratorWhere: [{ field: "actualSide", op: "==", value: "defense" }],
    src: "e1",
  },
  {
    id: "sideMatch.defenseToAttack",
    name: "第 1 候補の側が自玉側で、実戦は攻めだった局面",
    unit: "positions",
    population: { from: "branches", where: [{ field: "top1Side", op: "==", value: "defense" }], unit: "positions" },
    numeratorWhere: [{ field: "actualSide", op: "==", value: "attack" }],
    src: "e1",
  },
  // ---- 時間(冊子の 9 / 37・22 / 531)。**数え直せない 2 行** ----
  {
    id: "time.quickAfterLongThink",
    name: "直前の自分の手が 10 秒以上で、この手は 4 秒以内だった手のうち、評価の区分が下がった手",
    unit: "moves",
    population: { from: "moves", where: [{ field: "spentSec", op: "<=", value: 4 }], unit: "moves" },
    numeratorWhere: [{ field: "collapsed", op: "==", value: true }],
    src: "m1",
    recountNote:
      "数え直せない理由は 2 つ。(1) 材料(time_cause.midMoveSeconds)が持つ秒は中盤の手だけで、facts で秒が付いた手は 1242 のうち 161 しか無い。" +
      "(2)「直前の自分の手が 10 秒以上」は前の手を見る条件で、where に書けない。この行の where は定義の一部しか書けていない(この手が 4 秒以内、まで)。" +
      "数は材料(patient_report_data.time.afterLongThink.quickAfterLongThink)の写し。全時期の秒を材料に出す別の束で数え直せるようにする",
    fromMaterial: (materials) => {
      const bucket = materials.patient.time?.afterLongThink?.quickAfterLongThink;
      return bucket === undefined ? undefined : { numerator: bucket.collapsed, denominator: bucket.n };
    },
  },
  {
    id: "time.bySpent0to1",
    name: "0〜1 秒で指した手のうち、評価の区分が下がった手",
    unit: "moves",
    population: { from: "moves", where: [{ field: "spentSec", op: "<=", value: 1 }], unit: "moves" },
    numeratorWhere: [{ field: "collapsed", op: "==", value: true }],
    src: "m1",
    recountNote:
      "材料(time_cause.midMoveSeconds)が持つ秒は中盤の手だけで、facts で秒が付いた手は 1242 のうち 161 しか無い。" +
      "数は材料(patient_report_data.time.bySpent の 1 段目)の写し。全時期の秒を材料に出す別の束で数え直せるようにする",
    fromMaterial: (materials) => {
      const bucket = (materials.patient.time?.bySpent ?? [])[0];
      return bucket === undefined ? undefined : { numerator: bucket.collapsed, denominator: bucket.n };
    },
  },
  // ---- 長考(冊子の 61・33・5)。**局ごとの欄を足した数** ----
  {
    id: "longThink.total",
    name: "10 秒以上考えた手",
    unit: "moves",
    population: { from: "time", where: [], unit: "moves" },
    sumField: "longThinkCount",
    src: "m1",
  },
  {
    id: "longThink.fork",
    name: "10 秒以上考えた手のうち、分かれ道だった手",
    unit: "moves",
    population: { from: "time", where: [], unit: "moves" },
    sumField: "longThinkForkCount",
    src: "m1",
  },
  {
    id: "longThink.opposite",
    name: "10 秒以上考えた分かれ道のうち、実戦が第 1 候補と逆の側だった手",
    unit: "moves",
    population: { from: "time", where: [], unit: "moves" },
    sumField: "longThinkOppositeCount",
    src: "m1",
  },
  // ---- 分かれ道の数(冊子の 404・103) ----
  {
    id: "branches.total",
    name: "分かれ道として読んだ局面",
    unit: "positions",
    population: { from: "branches", where: [], unit: "positions" },
    src: "e2",
  },
  {
    id: "branches.shallowVisible",
    name: "浅い読みで差が見えた分かれ道の局面(付録に並べた局面)",
    unit: "positions",
    population: { from: "branches", where: [{ field: "shallowVisible", op: "==", value: true }], unit: "positions" },
    src: "d1",
  },
  {
    id: "branches.shallowVisibleGames",
    name: "浅い読みで差が見えた分かれ道が出てきた局(同じ局を重ねて数えない)",
    unit: "games",
    population: { from: "branches", where: [{ field: "shallowVisible", op: "==", value: true }], unit: "games" },
    src: "d1",
  },
  // ---- 再現の表(冊子の 54 局面・22 局)。**同じ母集団を 2 つの単位で出す** ----
  {
    id: "repro.top1Drop.positions",
    name: "浅い読みで差が見えた分かれ道のうち、第 1 候補が駒を打つ手だった局面",
    unit: "positions",
    population: {
      from: "branches",
      where: [{ field: "shallowVisible", op: "==", value: true }, { field: "top1Tags", op: "includes", value: "drop" }],
      unit: "positions",
    },
    src: "e2",
    srcExtra: ["d1"],
  },
  {
    id: "repro.top1Drop.games",
    name: "その局面が出てきた局(同じ局を重ねて数えない)",
    unit: "games",
    population: {
      from: "branches",
      where: [{ field: "shallowVisible", op: "==", value: true }, { field: "top1Tags", op: "includes", value: "drop" }],
      unit: "games",
    },
    src: "e2",
    srcExtra: ["d1"],
  },
  // ---- 崩れと優勢(冊子の 79・18 / 6) ----
  {
    id: "collapse.total",
    name: "評価の区分が下がった手",
    unit: "moves",
    population: { from: "moves", where: [{ field: "collapsed", op: "==", value: true }], unit: "moves" },
    src: "m1",
  },
  {
    id: "aheadThenLost",
    name: "一度は優勢になった局のうち、負けた局",
    unit: "games",
    population: { from: "games", where: [{ field: "aheadAtAnyPoint", op: "==", value: true }], unit: "games" },
    numeratorWhere: [{ field: "result", op: "==", value: "負け" }],
    src: "m1",
  },
  ...groupDefinitions(),
];

/**
 * `facts` から `aggregates` を組む。**数はここで数える**(材料から写す 2 行を除く)。
 * `materials` は、その 2 行の値と、写した理由を取るためだけに使う。
 */
export function aggregatesOf(facts: Record<string, unknown>, materials: FactsMaterials): AggregateRow[] {
  const index = factsIndexOf(facts);
  return ROW_DEFINITIONS.map((definition) => {
    const rows = selectRows(index, definition.population);
    const base = {
      id: definition.id,
      name: definition.name,
      unit: definition.unit,
      population: definition.population,
      derivedFrom: gameIdsOf(rows),
      src: definition.src,
      timeDependent: timeDependentOf(definition.population, definition.numeratorWhere, definition.sumField),
    };
    const extra: Record<string, unknown> = {};
    if (definition.numeratorWhere !== undefined) extra.numeratorWhere = definition.numeratorWhere;
    if (definition.sumField !== undefined) extra.sumField = definition.sumField;
    if (definition.srcExtra !== undefined) extra.srcExtra = definition.srcExtra;

    if (definition.fromMaterial !== undefined) {
      const numbers = definition.fromMaterial(materials);
      if (numbers === undefined) throw new ObservationAggregatesError(`${definition.id} の数が材料に無い(材料の time が空)`);
      // **写した行の `derivedFrom` は「材料が数えた範囲」= 全局**にする。
      // 母集団の `where` は定義の一部しか書けていない(秒が中盤の手だけ)ので、
      // そこから出した局の列を載せると**数の出どころを取り違えて示す**ことになる
      // (合成材料では 4 秒以内の手が 0 件で、数が 7 なのに局が空になった ― 2026-09-30 の試験で出た)。
      return {
        ...base, ...extra,
        derivedFrom: gameIdsOf(rowsOf(facts, "games")),
        numerator: numbers.numerator,
        denominator: numbers.denominator,
        recountable: false,
        recountNote: definition.recountNote ?? "数え直せない(理由が書かれていない)",
      } as AggregateRow;
    }
    if (definition.sumField !== undefined) {
      return { ...base, ...extra, value: sumOf(index, definition.population, definition.sumField), recountable: true } as AggregateRow;
    }
    if (definition.numeratorWhere !== undefined) {
      return {
        ...base, ...extra,
        numerator: countOf(index, definition.population, definition.numeratorWhere),
        denominator: countOf(index, definition.population),
        recountable: true,
      } as AggregateRow;
    }
    return { ...base, ...extra, value: countOf(index, definition.population), recountable: true } as AggregateRow;
  });
}

// ==================== 合わなければ止まる(集計の側の番人) ====================

function rowById(aggregates: readonly AggregateRow[], id: string): AggregateRow | undefined {
  return aggregates.find((row) => row.id === id);
}

function numberOf(aggregates: readonly AggregateRow[], id: string, key: "numerator" | "denominator" | "value"): number | undefined {
  const row = rowById(aggregates, id);
  const value = row?.[key];
  return typeof value === "number" ? value : undefined;
}

/**
 * 集計どうしの筋が通っているか。**別の道で同じ数に着くこと**を確かめる(1 つの道だけなら、
 * その道が間違っていても緑になる ― P-159 の家族)。空なら通った。
 */
export function aggregateAgreementProblems(aggregates: readonly AggregateRow[], facts: Record<string, unknown>): string[] {
  const problems: string[] = [];
  // **在る行の間の関係だけを見る。**行が揃っているかは `aggregateCoverageProblems`(道具が呼ぶ)の仕事 ―
  // ここで「無い」を数えると、**小さな packet(一部の行だけ)を検査できなくなる**(2026-09-30 に試験で出た)。
  const known = new Set(aggregates.map((row) => row.id));
  const need = (id: string, key: "numerator" | "denominator" | "value"): number | undefined => {
    if (!known.has(id)) return undefined;
    const value = numberOf(aggregates, id, key);
    if (value === undefined) problems.push(`集計の筋: ${id} の ${key} が無い`);
    return value;
  };
  /** 関係を見るのは、参加する行が全部在るときだけ */
  const all = (...ids: string[]): boolean => ids.every((id) => known.has(id));

  // (1) 側が逆の分子は、印で数えた数と `==` だけで数えた 2 行の和が合うこと
  const opposite = need("sideMatch.oppositeAll", "numerator");
  const attackToDefense = need("sideMatch.attackToDefense", "numerator");
  const defenseToAttack = need("sideMatch.defenseToAttack", "numerator");
  if (opposite !== undefined && attackToDefense !== undefined && defenseToAttack !== undefined) {
    if (opposite !== attackToDefense + defenseToAttack) {
      problems.push(`集計の筋: 側が逆の局面が ${opposite}(攻め→自玉側 ${attackToDefense} + 自玉側→攻め ${defenseToAttack} = ${attackToDefense + defenseToAttack}) ― 印と条件のどちらかがずれている`);
    }
  }
  // (2) 側が逆の分母は、攻めの分母 + 自玉側の分母
  const oppositeDenominator = need("sideMatch.oppositeAll", "denominator");
  const attackDenominator = need("sideMatch.attack", "denominator");
  const defenseDenominator = need("sideMatch.defense", "denominator");
  if (oppositeDenominator !== undefined && attackDenominator !== undefined && defenseDenominator !== undefined) {
    if (oppositeDenominator !== attackDenominator + defenseDenominator) {
      problems.push(`集計の筋: 側が 1 つだった分かれ道が ${oppositeDenominator}(攻め ${attackDenominator} + 自玉側 ${defenseDenominator})`);
    }
  }
  // (3) 群の局数の合計 = packet の局の数(群は局を分ける ― 重なりも漏れも無い)
  const gameRows = (facts.games ?? []) as unknown[];
  const groupIds = SIGNATURE_GROUPS.flatMap((group) => [`groups.${group.key}.games`, `groups.${group.key}.collapses`, `groups.${group.key}.aheadThenLost`]);
  const hasGroups = all(...groupIds);
  let groupGames = 0;
  let groupCollapses = 0;
  let groupAheadDenominator = 0;
  let groupAheadNumerator = 0;
  for (const group of SIGNATURE_GROUPS) {
    groupGames += need(`groups.${group.key}.games`, "value") ?? 0;
    groupCollapses += need(`groups.${group.key}.collapses`, "value") ?? 0;
    groupAheadDenominator += need(`groups.${group.key}.aheadThenLost`, "denominator") ?? 0;
    groupAheadNumerator += need(`groups.${group.key}.aheadThenLost`, "numerator") ?? 0;
  }
  if (hasGroups && groupGames !== gameRows.length) problems.push(`集計の筋: 群の局数の合計が ${groupGames}(packet の局は ${gameRows.length})`);
  const collapseTotal = need("collapse.total", "value");
  if (hasGroups && collapseTotal !== undefined && groupCollapses !== collapseTotal) {
    problems.push(`集計の筋: 群ごとの崩れの合計が ${groupCollapses}(全体は ${collapseTotal})`);
  }
  const aheadDenominator = need("aheadThenLost", "denominator");
  const aheadNumerator = need("aheadThenLost", "numerator");
  if (hasGroups && aheadDenominator !== undefined && groupAheadDenominator !== aheadDenominator) {
    problems.push(`集計の筋: 群ごとの「優勢になった局」の合計が ${groupAheadDenominator}(全体は ${aheadDenominator})`);
  }
  if (hasGroups && aheadNumerator !== undefined && groupAheadNumerator !== aheadNumerator) {
    problems.push(`集計の筋: 群ごとの「優勢になって負けた局」の合計が ${groupAheadNumerator}(全体は ${aheadNumerator})`);
  }
  // (4) 局面の数と局の数を混ぜていないか(局 ≦ 局面)
  for (const pair of [["repro.top1Drop.positions", "repro.top1Drop.games"], ["branches.shallowVisible", "branches.shallowVisibleGames"]] as const) {
    const positions = need(pair[0], "value");
    const games = need(pair[1], "value");
    if (positions !== undefined && games !== undefined && games > positions) {
      problems.push(`集計の筋: ${pair[1]} が ${games} で ${pair[0]} の ${positions} より多い ― 単位が入れ替わっている`);
    }
  }
  // (5) 分子は分母を超えない・数え直せない行には理由が要る
  for (const row of aggregates) {
    if (typeof row.numerator === "number" && typeof row.denominator === "number" && row.numerator > row.denominator) {
      problems.push(`集計の筋: ${row.id} の分子 ${row.numerator} が分母 ${row.denominator} より大きい`);
    }
    if (row.recountable === false && (row.recountNote === undefined || row.recountNote.length < 20)) {
      problems.push(`集計の筋: ${row.id} は数え直せない行なのに理由が書かれていない`);
    }
    if (row.recountable === true && row.recountNote !== undefined) {
      problems.push(`集計の筋: ${row.id} は数え直せる行なのに数え直せない理由が付いている`);
    }
    if (row.timeDependent !== timeDependentOf(row.population, row.numeratorWhere, row.sumField)) {
      problems.push(`集計の筋: ${row.id} の timeDependent が条件の欄と合わない(手で立てた値になっている)`);
    }
  }
  return problems;
}

// ==================== 一致の固定(人間の指示の試験 A) ====================
//
// **いま冊子に出ている数と、packet から数えた数が 1 つ残らず一致するか。**
// 相手は**冊子が実際に使った成果物**(`exit_candidates.json`・`patient_report_data.findings`・
// `direct_answers.counts`)であり、私が書き写した期待値ではない ―
// 期待値を書き写すと、材料が変わったときに**試験だけが古くなる**(5 人目で踏んだ型)。
// 【相手が無い数は「無い」と言う】材料に照合の相手が無い数は、**黙って通さずに 1 行出す。**
//   実物では 2 つある(側が逆の分子 51 と、長考の側が逆 5)― どちらも既存の python の関数が
//   その場で数えているだけで、JSON に残っていない。

export type BookletActionFraction = { readonly id?: string; readonly label?: string; readonly numerator?: number; readonly denominator?: number; readonly unit?: string };
export type BookletDenominator = { readonly number?: number; readonly unit?: string; readonly from?: string };
export type BookletReproRow = { readonly phrase?: string; readonly positions?: number; readonly games?: number };
export type BookletGroup = { readonly key?: string; readonly games?: number; readonly collapses?: number; readonly aheadGames?: number; readonly aheadLossGames?: number };
/**
 * **冊子の道具(python)がその場で数える数**(束 D で足した)。
 * `report-pdf/dump_booklet_numbers.py` が `check_answer.side_match_of`・`long_think_fork_of` を呼んで出す。
 * **別の言語の別の実装**なので、書き写した期待値より強い相手になる。
 */
export type BookletPythonNumbers = {
  readonly longThink?: { readonly longThink?: number; readonly fork?: number; readonly oppositeSide?: number };
  readonly sideMatch?: {
    readonly attack?: { readonly n?: number; readonly collapsed?: number };
    readonly defense?: { readonly n?: number; readonly collapsed?: number };
    readonly forkTotal?: number;
    readonly opposite?: { readonly numerator?: number; readonly denominator?: number };
  };
};
export type BookletNumbers = {
  readonly actionFractions?: readonly BookletActionFraction[];
  readonly denominators?: readonly BookletDenominator[];
  readonly repro?: readonly BookletReproRow[];
  readonly openingGroups?: readonly BookletGroup[];
  readonly findings?: readonly { readonly kind?: string; readonly numbers?: Record<string, number> }[];
  readonly directCounts?: Record<string, number>;
  readonly python?: BookletPythonNumbers;
};

/** 冊子の側の数の引き当て(1 つでも見つからなければ、それを言う) */
type Expectation = { readonly label: string; readonly get: (booklet: BookletNumbers) => number | undefined };

function fractionOf(booklet: BookletNumbers, id: string, label: string, key: "numerator" | "denominator"): number | undefined {
  const row = (booklet.actionFractions ?? []).find((candidate) => candidate.id === id && (candidate.label ?? "") === label);
  return row?.[key];
}

function denominatorOf(booklet: BookletNumbers, unit: string, includes: string): number | undefined {
  const rows = (booklet.denominators ?? []).filter((row) => row.unit === unit && (row.from ?? "").includes(includes));
  if (rows.length !== 1) return undefined;
  return rows[0]?.number;
}

function reproOf(booklet: BookletNumbers, phrase: string, key: "positions" | "games"): number | undefined {
  return (booklet.repro ?? []).find((row) => row.phrase === phrase)?.[key];
}

function groupOf(booklet: BookletNumbers, key: string, field: keyof BookletGroup): number | undefined {
  const row = (booklet.openingGroups ?? []).find((candidate) => candidate.key === key);
  const value = row?.[field];
  return typeof value === "number" ? value : undefined;
}

function findingOf(booklet: BookletNumbers, kind: string, key: string): number | undefined {
  return (booklet.findings ?? []).find((row) => row.kind === kind)?.numbers?.[key];
}

/** 集計の id + どの数か → 冊子の側の引き当て。**照合の相手が無い数はここに載せない**(下の MISSING に書く) */
/**
 * 集計の id + どの数か → **冊子の側の引き当て(1 つの数に複数持てる)。**
 * 同じ数に 2 つの相手(冊子が使った JSON と、冊子の道具の python の実装)を置く ―
 * **別の道で同じ数に着くほど強い**(束 D で 7 つの数が 2 つの相手を持つようになった)。
 * 相手が 1 つも見つからない数は、`bookletAgreementProblems` が「相手が無い」と言う。
 */
const BOOKLET_EXPECTATIONS: Readonly<Record<string, Partial<Record<"numerator" | "denominator" | "value", readonly Expectation[]>>>> = {
  "sideMatch.attack": {
    numerator: [
      { label: "M4 攻めの分子", get: (b) => fractionOf(b, "M4", "攻め", "numerator") },
      { label: "python の side_match_of の attack.collapsed", get: (b) => b.python?.sideMatch?.attack?.collapsed },
    ],
    denominator: [
      { label: "M4 攻めの分母", get: (b) => fractionOf(b, "M4", "攻め", "denominator") },
      { label: "python の side_match_of の attack.n", get: (b) => b.python?.sideMatch?.attack?.n },
    ],
  },
  "sideMatch.defense": {
    numerator: [
      { label: "M4 自玉側の分子", get: (b) => fractionOf(b, "M4", "自玉側", "numerator") },
      { label: "python の side_match_of の defense.collapsed", get: (b) => b.python?.sideMatch?.defense?.collapsed },
    ],
    denominator: [
      { label: "M4 自玉側の分母", get: (b) => fractionOf(b, "M4", "自玉側", "denominator") },
      { label: "python の side_match_of の defense.n", get: (b) => b.python?.sideMatch?.defense?.n },
    ],
  },
  "sideMatch.oppositeAll": {
    // **分子は冊子が使った JSON に残っていない**(本文の 51)。束 D で python の実装を相手にして閉じた
    numerator: [{ label: "python の side_match_of の opposite.numerator", get: (b) => b.python?.sideMatch?.opposite?.numerator }],
    denominator: [
      { label: "数の出どころ「第 1 候補の側が 1 つだった分かれ道」", get: (b) => denominatorOf(b, "局面", "第 1 候補の側が 1 つだった") },
      { label: "python の side_match_of の opposite.denominator", get: (b) => b.python?.sideMatch?.opposite?.denominator },
    ],
  },
  "time.quickAfterLongThink": {
    numerator: [{ label: "M5 の分子", get: (b) => fractionOf(b, "M5", "", "numerator") }],
    denominator: [{ label: "M5 の分母", get: (b) => fractionOf(b, "M5", "", "denominator") }],
  },
  "time.bySpent0to1": {
    denominator: [{ label: "数の出どころ「0〜1 秒で指した手」", get: (b) => denominatorOf(b, "手", "0〜1 秒で指した手") }],
  },
  "longThink.total": {
    value: [
      { label: "数の出どころ「10 秒以上考えた手(全部)」", get: (b) => denominatorOf(b, "手", "10 秒以上考えた手(全部)") },
      { label: "python の long_think_fork_of の longThink", get: (b) => b.python?.longThink?.longThink },
    ],
  },
  "longThink.fork": {
    value: [
      { label: "数の出どころ「10 秒以上考えた手のうち、分かれ道」", get: (b) => denominatorOf(b, "手", "分かれ道だった手") },
      { label: "python の long_think_fork_of の fork", get: (b) => b.python?.longThink?.fork },
    ],
  },
  // **冊子が使った JSON に残っていない**(本文の 5)。束 D で python の実装を相手にして閉じた
  "longThink.opposite": { value: [{ label: "python の long_think_fork_of の oppositeSide", get: (b) => b.python?.longThink?.oppositeSide }] },
  "branches.total": {
    value: [
      { label: "direct_answers の totalForkCount", get: (b) => b.directCounts?.totalForkCount },
      { label: "python の side_match_of の forkTotal", get: (b) => b.python?.sideMatch?.forkTotal },
    ],
  },
  "branches.shallowVisible": { value: [{ label: "direct_answers の totalCount", get: (b) => b.directCounts?.totalCount }] },
  "branches.shallowVisibleGames": { value: [{ label: "direct_answers の gamesCount", get: (b) => b.directCounts?.gamesCount }] },
  "repro.top1Drop.positions": { value: [{ label: "再現の表「第 1 候補が駒を打つ手」の局面", get: (b) => reproOf(b, "第 1 候補が駒を打つ手", "positions") }] },
  "repro.top1Drop.games": { value: [{ label: "再現の表「第 1 候補が駒を打つ手」の局", get: (b) => reproOf(b, "第 1 候補が駒を打つ手", "games") }] },
  "collapse.total": { value: [{ label: "patient の findings phase.fell", get: (b) => findingOf(b, "phase", "fell") }] },
  aheadThenLost: {
    numerator: [{ label: "patient の findings aheadLoss.aheadLossGames", get: (b) => findingOf(b, "aheadLoss", "aheadLossGames") }],
    denominator: [{ label: "patient の findings aheadLoss.aheadGames", get: (b) => findingOf(b, "aheadLoss", "aheadGames") }],
  },
  "groups.core.games": { value: [{ label: "群 A の局数", get: (b) => groupOf(b, "core", "games") }] },
  "groups.other.games": { value: [{ label: "群 B の局数", get: (b) => groupOf(b, "other", "games") }] },
  "groups.noSignature.games": { value: [{ label: "群 C の局数", get: (b) => groupOf(b, "noSignature", "games") }] },
  "groups.core.collapses": { value: [{ label: "群 A の崩れ", get: (b) => groupOf(b, "core", "collapses") }] },
  "groups.other.collapses": { value: [{ label: "群 B の崩れ", get: (b) => groupOf(b, "other", "collapses") }] },
  "groups.noSignature.collapses": { value: [{ label: "群 C の崩れ", get: (b) => groupOf(b, "noSignature", "collapses") }] },
  "groups.core.aheadThenLost": {
    numerator: [{ label: "群 A の優勢→負け", get: (b) => groupOf(b, "core", "aheadLossGames") }],
    denominator: [{ label: "群 A の優勢になった局", get: (b) => groupOf(b, "core", "aheadGames") }],
  },
  "groups.other.aheadThenLost": {
    numerator: [{ label: "群 B の優勢→負け", get: (b) => groupOf(b, "other", "aheadLossGames") }],
    denominator: [{ label: "群 B の優勢になった局", get: (b) => groupOf(b, "other", "aheadGames") }],
  },
  "groups.noSignature.aheadThenLost": {
    numerator: [{ label: "群 C の優勢→負け", get: (b) => groupOf(b, "noSignature", "aheadLossGames") }],
    denominator: [{ label: "群 C の優勢になった局", get: (b) => groupOf(b, "noSignature", "aheadGames") }],
  },
};

// **「照合の相手が無い数」の表は束 D で消した。**
// 束 C では、側が逆の分子(冊子の本文の 51)と長考のうち側が逆(本文の 5)に突き合わせる相手が
// 冊子の JSON に無く、道具が毎回「相手が無い」と声に出していた。
// 束 D で**冊子の道具の python(`report-pdf/dump_booklet_numbers.py`)を相手として呼ぶ**ようにしたので、
// 2 つとも普通の照合になった。**相手が渡されなければ上の「相手が無い」の 1 行が出る**ので、黙って外れる道は無い。

/** 集計の行と冊子の数の突き合わせ。空なら 1 つ残らず一致 */
export function bookletAgreementProblems(aggregates: readonly AggregateRow[], booklet: BookletNumbers): string[] {
  const problems: string[] = [];
  const byId = new Map(aggregates.map((row) => [row.id, row] as const));
  for (const [id, expectations] of Object.entries(BOOKLET_EXPECTATIONS)) {
    const row = byId.get(id);
    if (row === undefined) {
      problems.push(`A 再現性: 集計に ${id} が無い`);
      continue;
    }
    for (const [key, list] of Object.entries(expectations) as [keyof AggregateRow & ("numerator" | "denominator" | "value"), readonly Expectation[]][]) {
      const mine = row[key];
      let found = 0;
      for (const expectation of list) {
        const theirs = expectation.get(booklet);
        // **渡されなかった相手は数えない。**同じ数に 2 つ置いてあり、片方(python)が無い回もある
        if (theirs === undefined) continue;
        found += 1;
        if (mine !== theirs) problems.push(`A 再現性: ${id} の ${key} が ${String(mine)}(冊子の ${expectation.label} は ${theirs})`);
      }
      // **相手が 1 つも無いときは言う**(黙って照合の対象から外さない)
      if (found === 0) problems.push(`A 再現性: ${id} の ${key} を照合する相手(${list.map((expectation) => expectation.label).join(" / ")})が材料に無い`);
    }
  }
  return problems;
}

/**
 * **行が揃っているか**(道具が呼ぶ)。冊子に出る数の表(`ROW_DEFINITIONS`)の id が、
 * 1 つ残らず在って重なっていないこと。**契約の検査とは別にする** ―
 * 契約は「この形か」を見るもので、「この顧客の 20 の数が全部在るか」は道具の仕事。
 */
export function aggregateCoverageProblems(aggregates: readonly AggregateRow[]): string[] {
  const problems: string[] = [];
  const counts = new Map<string, number>();
  for (const row of aggregates) counts.set(row.id, (counts.get(row.id) ?? 0) + 1);
  for (const definition of ROW_DEFINITIONS) {
    const count = counts.get(definition.id) ?? 0;
    if (count === 0) problems.push(`集計の揃い: ${definition.id} の行が無い`);
    if (count > 1) problems.push(`集計の揃い: ${definition.id} の行が ${count} 本ある`);
  }
  const known = new Set(ROW_DEFINITIONS.map((definition) => definition.id));
  for (const id of counts.keys()) if (!known.has(id)) problems.push(`集計の揃い: 表に無い行 ${id} が在る`);
  return problems;
}


/**
 * **packet だけを見て数え直す**(束 D。人間の指示の試験 E の相手)。
 *
 * 【誰のための検査か】packet を受け取る側(3 席の LLM・検証器・組版)は**材料を持たない。**
 * その立場で「この数は本当にこの母集団を数えた数か」を確かめられるようにする ―
 * `population`・`numeratorWhere`・`sumField` のとおりに `facts` を数え、行の数と突き合わせる。
 * 【数え直せない行は対象外】`recountable: false` の 2 行(材料の秒が中盤の手だけ)は飛ばす。
 * **理由が書かれていない `recountable: false` は `aggregateAgreementProblems` が落とす**ので、
 * ここで飛ばしても「黙って外れた行」は残らない。
 * 【これは同じ道か】数え方の仕組みは `aggregatesOf` と同じものを使う(別に書けば二重の実装になり、
 * どちらが正しいか決められない)。**この検査が捕まえるのは「packet の数が後から書き換わった」形** ―
 * 母集団の言葉と数が食い違う packet を、材料が無い側でも落とせる。
 */
export function recountProblems(packet: { facts?: unknown; aggregates?: unknown }): string[] {
  const facts = packet.facts;
  if (facts === null || typeof facts !== "object") return ["数え直し: facts が無い"];
  const aggregates = packet.aggregates;
  if (!Array.isArray(aggregates)) return ["数え直し: aggregates が無い"];
  const index = factsIndexOf(facts as Record<string, unknown>);
  const problems: string[] = [];
  for (const row of aggregates as AggregateRow[]) {
    if (row.recountable === false) continue;
    const population = row.population;
    if (population === undefined) {
      problems.push(`数え直し: ${row.id} に population が無い`);
      continue;
    }
    try {
      if (row.sumField !== undefined) {
        const total = sumOf(index, population, row.sumField);
        if (row.value !== total) problems.push(`数え直し: ${row.id} の数が ${String(row.value)}(${population.from} の ${row.sumField} を足すと ${total})`);
        continue;
      }
      if (row.numeratorWhere !== undefined) {
        const denominator = countOf(index, population);
        const numerator = countOf(index, population, row.numeratorWhere);
        if (row.denominator !== denominator) problems.push(`数え直し: ${row.id} の分母が ${String(row.denominator)}(数え直すと ${denominator})`);
        if (row.numerator !== numerator) problems.push(`数え直し: ${row.id} の分子が ${String(row.numerator)}(数え直すと ${numerator})`);
        continue;
      }
      const value = countOf(index, population);
      if (row.value !== value) problems.push(`数え直し: ${row.id} の数が ${String(row.value)}(数え直すと ${value})`);
    } catch (error) {
      problems.push(`数え直し: ${row.id} を数え直せない(${error instanceof Error ? error.message : String(error)})`);
    }
    // **局の列も数え直す**(数が合っていても、どの局から出たかが書き換わっていれば辿れない)
    const derivedFrom = gameIdsOf(selectRows(index, population));
    const written = [...(row.derivedFrom ?? [])].sort();
    if (written.length > 0 && derivedFrom.length > 0 && written.join(",") !== derivedFrom.join(",")) {
      problems.push(`数え直し: ${row.id} の derivedFrom が ${written.length} 局(数え直すと ${derivedFrom.length} 局)`);
    }
  }
  return problems;
}
