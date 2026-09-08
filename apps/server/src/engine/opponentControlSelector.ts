// 相手AIが毎局どのvariantを指すかを、承認済み候補から均等・決定的に選ぶための純粋関数群。
// docs/PHASES.md Phase 7 Unit 1 / docs/SCENARIOS.md により、選択は「毎局seed付きランダムで、
// 承認済みvariantから均等に1件を選ぶ」ことが確定している(人間承認済み)。
// 重み付けは行わない(スキーマも拡張しない)。
//
// seedおよび選択結果はAPIレスポンスへ公開しない(docs/ARCHITECTURE.md 6.の公開境界)。

/**
 * 決定的な擬似乱数生成器(mulberry32相当)。
 * 出典: https://gist.github.com/tommyettinger/46a874533244883189143505d203312c
 * (Tommy Ettingerによる公開アルゴリズムの説明に基づく、数行の最小実装。外部依存を増やさない)。
 * 同じseedを与えると常に同じ数列を返す(決定性)。
 */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * 相手AI制御の選択に使うseedを生成する。Date.now()ベース(テストからは
 * 固定値を注入して呼べるよう、この関数自体を差し替え可能にしている)。
 */
export function generateOpponentControlSeed(now: () => number = Date.now): number {
  return now() >>> 0;
}

/**
 * 候補(variants)から、seedに基づいて均等に1件を選ぶ決定的な純粋関数。
 * 同じseedと同じ候補列(順序を含む)であれば常に同じ結果を返す。
 * 候補が0件ならundefinedを返す。
 */
export function selectVariant<T>(variants: readonly T[], seed: number): T | undefined {
  if (variants.length === 0) return undefined;
  const random = mulberry32(seed);
  const index = Math.floor(random() * variants.length);
  // 浮動小数点誤差でindexがvariants.lengthに達した場合の安全策。
  return variants[Math.min(index, variants.length - 1)];
}
