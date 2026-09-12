// STEP U6-S(docs/PHASES.md で採番)。実際に盤上に存在する81マスの集合。
//
// 【なぜこの集合が要るのか】
// shogiopsの attacks() は、盤の内部表現(1段=16マス幅)の都合上、**盤の外にあたる
// マスを含んだ利きを返すことがある。**Position の合法手生成は内部でこれを盤の範囲へ
// 絞っているが、attacks() を直接呼ぶモジュールは自分で盤の外を除外する必要がある。
//
// 除外しないと、たとえば次のことが起きる。
// - 経路探索(analysis/routePlanner.ts): 5iの銀の「後ろ斜め」として九段目より下の
//   6j・4j が返り、「３九→４八→５九→6j→７九→７八」のように**存在しないマスを
//   通り抜ける経路**が作られ、手数も実際より短く出る。
// - 利きの升数(analysis/pvMaterials.ts): 9九の角は素の size() が 29(実際は8)、
//   5五の飛は 23(実際は16)。**線で利く駒だけが静かに過大になる。**
//
// 【なぜここ(rules/)に置くのか】
// これは「盤とはどこか」という盤そのものの事実であり、解析の都合ではない。
// 2026-09-13 までは analysis/routePlanner.ts と analysis/pvMaterials.ts が
// **同じ集合を別々に持っていた**(後者の冒頭コメントは「共通化は既存ファイルに
// 触るので別STEPの判断とする」と明記していた)。**同じものが2か所にあると、
// 片方だけ直る状態を作る。**U6-S で1か所へまとめた。
//
// 盤の範囲は docs/DATA_MODEL.md の座標表記の規約(筋1〜9・段a〜i)そのままで
// 組み立てる。**段の内部的な幅などの実装詳細には依存しない。**

import { SquareSet } from "shogiops/square-set";
import { parseSquareName } from "shogiops/util";

export const BOARD_SQUARES: SquareSet = (() => {
  let squares = SquareSet.empty();
  for (const file of "123456789") {
    for (const rank of "abcdefghi") {
      const square = parseSquareName(`${file}${rank}`);
      if (square !== undefined) squares = squares.with(square);
    }
  }
  return squares;
})();
