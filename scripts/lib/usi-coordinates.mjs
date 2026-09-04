// USI形式のマス目表記(例: "3b")を扱う汎用ユーティリティ。
// shapes/openings/intents のどのスキーマの座標フィールドにも使える想定で、
// shapes固有のロジック(required_piecesの構造など)には依存しない。
//
// 座標形式・視点の規約は docs/DATA_MODEL.md の「座標表記の規約」を参照。

const FILE_MIN = 1;
const FILE_MAX = 9;
const RANKS = "abcdefghi"; // a=一 ... i=九

export class InvalidUsiSquareError extends Error {
  constructor(square) {
    super(`不正なUSIマス目表記です: "${square}"`);
    this.name = "InvalidUsiSquareError";
    this.square = square;
  }
}

function parseUsiSquare(square) {
  const match = /^([1-9])([a-i])$/.exec(square);
  if (!match) throw new InvalidUsiSquareError(square);
  return { file: Number(match[1]), rank: match[2] };
}

/**
 * 盤面を180度回転した先のマス目を返す(筋 n -> 10-n、段は a<->i の対称変換)。
 * 先手絶対座標<->後手絶対座標の相互変換、およびその逆に使う。
 * 詳細: docs/DATA_MODEL.md の「座標表記の規約」。
 */
export function rotateSquare180(square) {
  const { file, rank } = parseUsiSquare(square);
  const rotatedFile = FILE_MIN + FILE_MAX - file;
  const rotatedRank = RANKS[RANKS.length - 1 - RANKS.indexOf(rank)];
  return `${rotatedFile}${rotatedRank}`;
}
