// STEP TYPE(docs/STEP_TYPE_PLAN_2026-09-23.md)。分かれ道の「タイプ」を、大きさ(A)×側(B)×性質(C)の
// 印の組み合わせで定義し、3 局以上に繰り返される組を数える段の純粋関数。**測る段だけ**(冊子に出す形は
// 別の作業)。
//
// 【このファイルがやること】
// - 分かれ道 1 つぶんの入力(whatif-v2 の position 行の側の印・read.ts の position 行の firstVisibleNodes・
//   手の性質の印・見た目の損得・その手にかけた秒)から、3 軸(size・side・nature)の組を付ける(`typeForkOf`)。
// - 複数局(`TypeGame` の列)から、組ごとの局数・回数(`typeGroupCountsOf`)、3 局以上の組
//   (`repeatedGroupsOf`)、側ごとの秒の中央値(T4 用、`medianSecondsBySideOf`)、実戦が retreat の
//   分かれ道が出る局数(T5 用、`retreatGameCountOf`)を集計する。
//
// 【このファイルが絶対にやらないこと】
// - エンジンを起動すること・ファイルの読み書き(CLI(scripts/playtest/type.ts)の役目)
// - タイプに名前(「攻め急ぎ」等)を付けること。組は印の組み合わせ(`key`)のまま扱う
//   (docs/STEP_TYPE_PLAN_2026-09-23.md 1.「決まりとの関係」)
// - 局面の意味からの判定。側・性質は whatif-v2・read.ts がすでに付けた印をそのまま読むだけ
//
// 【判断的知識】TYPE_VALUES(nodeShallowMaxNodes・nodeDeepMinNodes・repeatMinGames)は計画の仮置きの値であり、
// 将棋一般の閾値ではない(2026-09-23、計画 §3)。承認前の draft 相当。

/** 判断的知識の仮置き(計画 §3)。ここに 1 か所だけ置き、出力の出どころ(meta 行)へそのまま写す。 */
export const TYPE_VALUES = {
  /** 軸 A(大きさ): firstVisibleNodes がこの値以下なら「浅い(shallow)」(計画の 2000〜10000)。 */
  nodeShallowMaxNodes: 10_000,
  /** 軸 A: firstVisibleNodes がこの値以上なら「深い(deep)」(計画の 50000 以上)。 */
  nodeDeepMinNodes: 50_000,
  /** 「繰り返し」とみなす最小の局数(計画 §3「同じ (A, B, C) の組が 3 局以上に出ること」)。 */
  repeatMinGames: 3,
} as const;

/** 数値を widen する(`lib/whatif.ts` の `WhatifValues` と同じ考え方 ― 呼び出し側が別の数値で上書きできるように)。 */
export type TypeValues = { readonly [K in keyof typeof TYPE_VALUES]: number };

export class TypeStepError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TypeStepError";
  }
}

// ---- 軸 A: 大きさ(firstVisibleNodes) ----

export type TypeSizeBucket = "none" | "shallow" | "deep";

/**
 * `firstVisibleNodes`(read.ts の出力。null = 100 万ノードでも 600 未満)から軸 A を決める(計画 §3)。
 * `nodeShallowMaxNodes` と `nodeDeepMinNodes` の間(計画が定義していない区間)に落ちる値は、
 * 現在の `READ_VALUES.nodeLadder`(2000・10000・50000・200000・1000000)では起こらないが、
 * 黙って寄せずに例外を投げる(計画にない判断: 保守的側 ― 未定義の区分へ機械的に丸めない)。
 */
export function sizeBucketOf(firstVisibleNodes: number | null, values: TypeValues = TYPE_VALUES): TypeSizeBucket {
  if (firstVisibleNodes === null) return "none";
  if (firstVisibleNodes <= values.nodeShallowMaxNodes) return "shallow";
  if (firstVisibleNodes >= values.nodeDeepMinNodes) return "deep";
  throw new TypeStepError(
    `firstVisibleNodes(${firstVisibleNodes})が「浅い」(${values.nodeShallowMaxNodes} 以下)にも「深い」(${values.nodeDeepMinNodes} 以上)にも当たらない`,
  );
}

// ---- 軸 B: 側(whatif-v2 の side) ----

/** whatif-v2(lib/whatif.ts の `WhatifSide`)の側の印。ここでは値をそのまま読むだけで、再判定はしない。 */
export type WhatifSideRaw = "attack" | "defense" | "both" | "none";

export type TypeSideBucket = "top1AttackActualDefense" | "top1DefenseActualAttack" | "same" | "eitherNone";

interface SideMembership {
  attack: boolean;
  defense: boolean;
}

/** "both" を「攻めでも守りでもある」集合として扱う(司令塔の指示、計画にない判断: 「同じ側」は集合が交わるかどうかで見る)。 */
function sideMembershipOf(side: WhatifSideRaw): SideMembership {
  return { attack: side === "attack" || side === "both", defense: side === "defense" || side === "both" };
}

/**
 * 軸 B(側)を決める(計画 §3、計画にない判断: 「両方」の扱い)。
 * - 第 1 候補・実戦の手のどちらかが "none"(攻めでも守りでもない)なら `eitherNone`。
 * - どちらも "none" でなければ、それぞれを { attack, defense } の集合に開き(`both` は両方 true)、
 *   集合が交わっていれば `same`(片方が `both` でも、もう片方の側と重なれば同じ側として扱う)。
 * - 交わらなければ、第 1 候補が攻め側だけ・実戦が守り側だけ、またはその逆。
 */
export function sideBucketOf(top1Side: WhatifSideRaw, actualSide: WhatifSideRaw): TypeSideBucket {
  if (top1Side === "none" || actualSide === "none") return "eitherNone";
  const top1 = sideMembershipOf(top1Side);
  const actual = sideMembershipOf(actualSide);
  const intersects = (top1.attack && actual.attack) || (top1.defense && actual.defense);
  if (intersects) return "same";
  if (top1.attack && actual.defense) return "top1AttackActualDefense";
  if (top1.defense && actual.attack) return "top1DefenseActualAttack";
  // "attack"/"defense"/"both" の組み合わせでは、交わらない場合はここまでの2分岐で必ず尽くされる(9通り確認済み)。
  // 未知の値(将来 WhatifSideRaw が増える等)が来たときのための歯止め。
  throw new TypeStepError(`側の組み合わせを判定できない(top1Side=${top1Side}, actualSide=${actualSide})`);
}

// ---- 軸 C: 性質(実戦の手) ----

export type TypeNatureBucket = "retreat" | "materialGain" | "drop" | "other";

/** read.ts の `ReadMoveMarks` のうち、軸 C の判定に使う 3 つだけ。 */
export interface TypeNatureTags {
  retreat: boolean;
  drop: boolean;
  sacrifice: boolean;
}

/**
 * 軸 C(性質)を決める(計画 §3。優先順は commander の指示どおり retreat → 駒得の見た目 → drop → それ以外)。
 * 「駒得の見た目」= `actualMaterialLook > 0` かつ `sacrifice` でない(read.ts の `materialLookOf`・`sacrifice` と同じ値)。
 */
export function natureBucketOf(actualTags: TypeNatureTags, actualMaterialLook: number): TypeNatureBucket {
  if (actualTags.retreat) return "retreat";
  if (actualMaterialLook > 0 && !actualTags.sacrifice) return "materialGain";
  if (actualTags.drop) return "drop";
  return "other";
}

// ---- 組(A, B, C) ----

export interface TypeTriple {
  size: TypeSizeBucket;
  side: TypeSideBucket;
  nature: TypeNatureBucket;
}

/** 組を一意な文字列の key にする(名前を付けない ― 印の組み合わせのまま扱うための表現)。 */
export function typeKeyOf(triple: TypeTriple): string {
  return `${triple.size}|${triple.side}|${triple.nature}`;
}

function tripleOfKey(key: string): TypeTriple {
  const parts = key.split("|");
  if (parts.length !== 3) throw new TypeStepError(`key の形が不正: ${key}`);
  const [size, side, nature] = parts as [TypeSizeBucket, TypeSideBucket, TypeNatureBucket];
  return { size, side, nature };
}

// ---- 1 分かれ道ぶんの記録 ----

export interface TypeForkInput {
  ply: number;
  displayPly: number;
  /** read.ts の `firstVisibleNodes`(null = 100 万ノードでも 600 未満)。 */
  firstVisibleNodes: number | null;
  /** whatif-v2 の第 1 候補(candidates[0])の side。 */
  top1Side: WhatifSideRaw;
  /** whatif-v2 の実戦の手の side(actualSide)。 */
  actualSide: WhatifSideRaw;
  /** read.ts の実戦の手の印(actualTags)のうち軸 C に使う 3 つ。 */
  actualTags: TypeNatureTags;
  /** read.ts の実戦の手の見た目の損得(actualMaterialLook)。 */
  actualMaterialLook: number;
  /** その手にかけた秒(fixed 棋譜の moveSeconds から。読めなければ null)。 */
  spentSec: number | null;
}

/** 分かれ道 1 つぶんの記録。**手・SFEN・評価値は持たない**(計画「出力」)。 */
export interface TypeFork {
  ply: number;
  displayPly: number;
  size: TypeSizeBucket;
  side: TypeSideBucket;
  nature: TypeNatureBucket;
  key: string;
  spentSec: number | null;
}

export function typeForkOf(input: TypeForkInput, values: TypeValues = TYPE_VALUES): TypeFork {
  const size = sizeBucketOf(input.firstVisibleNodes, values);
  const side = sideBucketOf(input.top1Side, input.actualSide);
  const nature = natureBucketOf(input.actualTags, input.actualMaterialLook);
  const triple: TypeTriple = { size, side, nature };
  return { ply: input.ply, displayPly: input.displayPly, size, side, nature, key: typeKeyOf(triple), spentSec: input.spentSec };
}

// ---- moveSeconds から秒を引く(STEP TIME(lib/reportData.ts の buildBySpent 等)と同じ添字合わせ:
//       displayPly は「本人が指した向きの手数」= KIF の手数なので、moveSeconds[displayPly - 1] を読む) ----

export interface MoveSecondsLike {
  spentSec: number;
}

/** `moveSeconds` が無ければ(または欄の長さが足りなければ)null。将棋の判断ではなく単なる添字読み。 */
export function spentSecOfDisplayPly(moveSeconds: readonly (MoveSecondsLike | null)[] | null | undefined, displayPly: number): number | null {
  if (moveSeconds === null || moveSeconds === undefined) return null;
  const time = moveSeconds[displayPly - 1];
  return time === undefined || time === null ? null : time.spentSec;
}

// ---- 局ごとのまとめ ----

export interface TypeGame {
  id: string;
  forks: readonly TypeFork[];
}

// ---- 複数局の集計(計画「作るもの」) ----

export interface TypeGroupCount {
  key: string;
  triple: TypeTriple;
  /** その組が出た局の数(1 局 1 回で数える)。 */
  games: number;
  /** その組が出た延べ回数(1 局に複数回出ることがある)。 */
  occurrences: number;
}

/** 組ごとの局数・回数(計画「出力」)。key の昇順で返す(決定的な順序)。 */
export function typeGroupCountsOf(games: readonly TypeGame[]): TypeGroupCount[] {
  const occurrences = new Map<string, number>();
  const gamesByKey = new Map<string, Set<string>>();
  for (const game of games) {
    for (const fork of game.forks) {
      occurrences.set(fork.key, (occurrences.get(fork.key) ?? 0) + 1);
      const set = gamesByKey.get(fork.key) ?? new Set<string>();
      set.add(game.id);
      gamesByKey.set(fork.key, set);
    }
  }
  return [...occurrences.keys()]
    .sort()
    .map((key) => ({ key, triple: tripleOfKey(key), games: gamesByKey.get(key)!.size, occurrences: occurrences.get(key)! }));
}

/** `values.repeatMinGames` 局以上に出た組だけ(計画 §3「繰り返し」)。 */
export function repeatedGroupsOf(counts: readonly TypeGroupCount[], values: TypeValues = TYPE_VALUES): TypeGroupCount[] {
  return counts.filter((count) => count.games >= values.repeatMinGames);
}

// ---- T4: 側(軸 B)ごとの秒の中央値 ----

/** 中央値(件数が偶数なら中央2件の平均。`lib/reportData.ts` の非公開の `medianOf` と同じ考え方 ― export されていないため写す)。 */
function medianOf(values: readonly number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1]! + sorted[mid]!) / 2 : sorted[mid]!;
}

export interface TypeSideSecondsMedian {
  side: TypeSideBucket;
  /** 秒が読めた分かれ道の数(分母)。 */
  n: number;
  medianSec: number | null;
}

const SIDE_BUCKETS: readonly TypeSideBucket[] = ["top1AttackActualDefense", "top1DefenseActualAttack", "same", "eitherNone"];

/** T4 用(計画 §4)。側(軸 B)ごとに、秒が読めた分かれ道の中央値を出す。 */
export function medianSecondsBySideOf(games: readonly TypeGame[]): TypeSideSecondsMedian[] {
  return SIDE_BUCKETS.map((side) => {
    const seconds = games.flatMap((game) => game.forks.filter((fork) => fork.side === side && fork.spentSec !== null).map((fork) => fork.spentSec!));
    return { side, n: seconds.length, medianSec: medianOf(seconds) };
  });
}

// ---- T5: 実戦が retreat の分かれ道が出る局数 ----

/** T5 用(計画 §4)。実戦の手が retreat(軸 C)の分かれ道が 1 つでもある局の数。 */
export function retreatGameCountOf(games: readonly TypeGame[]): number {
  return games.filter((game) => game.forks.some((fork) => fork.nature === "retreat")).length;
}
