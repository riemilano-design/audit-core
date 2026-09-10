// STEP T-3。docs/PLAYTEST_LOOP_PROPOSAL.md 4.2・STEP T-3計画書
// 「対局者(自分側)の5プロファイル」で要求される「決定的(同じ局面・同じ乱数状態で
// 同じ手)」を満たすための、種つき決定的乱数生成器(xorshift32)。
//
// 依存追加なし。将棋の判断は一切行わない、汎用の乱数ユーティリティ。

/** xorshift32による決定的な擬似乱数生成器。同じ種からは常に同じ列を返す。 */
export class Prng {
  private state: number;

  constructor(seed: number) {
    // xorshift32の内部状態は0であってはならない(0のままだと以後ずっと0を返す)。
    // 0が渡された場合は固定の非ゼロ値へ振り替える(値自体に将棋的な意味は無い)。
    const normalized = seed | 0;
    this.state = normalized === 0 ? 0x9e3779b9 : normalized;
  }

  /** [0, 1) の範囲の浮動小数点数を返す(決定的)。 */
  next(): number {
    let x = this.state;
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    this.state = x;
    return (x >>> 0) / 0x100000000;
  }

  /** [0, max) の整数を返す(max は正の整数が前提。決定的)。 */
  nextInt(max: number): number {
    return Math.floor(this.next() * max);
  }
}
