// USI形式のマス目表記(例: "8h")を、ユーザー向けの日本語表記(例: "８八")へ変換する。
// docs/DATA_MODEL.md「座標表記の規約」が定める
// 「内部データはUSI形式を正規形式とし、ユーザー向け画面には変換関数を通してから表示する」
// の変換関数にあたる。表記の変換のみを行い、将棋の判断は一切しない。
//
// 段の対応(docs/DATA_MODEL.mdの表そのまま):
//   a=一 b=二 c=三 d=四 e=五 f=六 g=七 h=八 i=九
// 筋は全角数字(１〜９)にする(将棋の慣例的な表記に合わせるための字形の変換のみ)。

const FILE_TO_JAPANESE: Record<string, string> = {
  "1": "１",
  "2": "２",
  "3": "３",
  "4": "４",
  "5": "５",
  "6": "６",
  "7": "７",
  "8": "８",
  "9": "９",
};

const RANK_TO_JAPANESE: Record<string, string> = {
  a: "一",
  b: "二",
  c: "三",
  d: "四",
  e: "五",
  f: "六",
  g: "七",
  h: "八",
  i: "九",
};

/**
 * USI形式のマス目(例: "8h")を日本語表記(例: "８八")に変換する。
 *
 * 解釈できない文字列が来た場合は例外を投げず、入力をそのまま返す
 * (表記の変換だけのために対局・説明表示を止めないための安全側の既定動作。
 * analysis/api層のsafe*ラッパーと同じ考え方)。
 */
export function toJapaneseSquare(usiSquare: string): string {
  if (usiSquare.length !== 2) return usiSquare;
  const file = FILE_TO_JAPANESE[usiSquare[0]!];
  const rank = RANK_TO_JAPANESE[usiSquare[1]!];
  if (!file || !rank) return usiSquare;
  return `${file}${rank}`;
}

/**
 * マス目の並び(経路)を "５九→６八→７八→８八" のような1つの文字列にする。
 * 個々のマスの変換はtoJapaneseSquareに委ねる(同じ変換規則を重複させない)。
 */
export function toJapaneseSquarePath(usiSquares: string[]): string {
  return usiSquares.map((square) => toJapaneseSquare(square)).join("→");
}

/**
 * USI形式の指し手(例: "5i6h")を、移動元と移動先のマス目表記
 * (例: "５九→６八")に変換する。
 *
 * 駒の種類や成り・不成りは表現しない(この関数はマス目の表記変換だけを担当する。
 * 駒を含む正式な棋譜表記はnotation/japaneseMoveHistory.tsの責務)。
 * ドロップ(例: "P*5e")や解釈できない文字列は、例外を投げず入力をそのまま返す。
 */
export function toJapaneseMoveSquares(moveUsi: string): string {
  const withoutPromotion = moveUsi.endsWith("+") ? moveUsi.slice(0, -1) : moveUsi;
  if (withoutPromotion.length !== 4 || withoutPromotion.includes("*")) return moveUsi;

  const from = toJapaneseSquare(withoutPromotion.slice(0, 2));
  const to = toJapaneseSquare(withoutPromotion.slice(2, 4));
  if (from === withoutPromotion.slice(0, 2) || to === withoutPromotion.slice(2, 4)) return moveUsi;

  return `${from}→${to}`;
}
