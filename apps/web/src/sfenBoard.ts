// SFEN文字列の盤面部分を、表示用の駒配置に変換する純粋関数。
// apps/webはこのためだけにshogiops全体を持ち込まず、必要最小限の文字列解析のみ行う
// (合法手判定はapps/server側の責任であり、ここでは表示にしか使わない)。

export interface BoardPiece {
  // 成りを含む駒種を大文字1文字(成りは先頭に"+")で表す。例: "P", "+P", "K"
  piece: string;
  color: "sente" | "gote";
}

export type BoardSquare = BoardPiece | null;

const FILES = 9;
const RANKS = 9;

export function parseSfenBoardPart(sfen: string): BoardSquare[][] {
  const boardPart = sfen.split(" ")[0] ?? "";
  const rankStrings = boardPart.split("/");
  if (rankStrings.length !== RANKS) {
    throw new Error(`SFENの段数が9ではありません: "${sfen}"`);
  }
  return rankStrings.map(parseRank);
}

function parseRank(rankStr: string): BoardSquare[] {
  const squares: BoardSquare[] = [];
  let i = 0;
  while (i < rankStr.length) {
    const ch = rankStr[i];
    if (ch === undefined) break;
    if (ch >= "1" && ch <= "9") {
      const emptyCount = Number(ch);
      for (let j = 0; j < emptyCount; j += 1) squares.push(null);
      i += 1;
      continue;
    }
    if (ch === "+") {
      const next = rankStr[i + 1];
      if (next === undefined) throw new Error(`不正なSFEN段表記です: "${rankStr}"`);
      squares.push(toPiece(`+${next}`));
      i += 2;
      continue;
    }
    squares.push(toPiece(ch));
    i += 1;
  }
  if (squares.length !== FILES) {
    throw new Error(`SFENの筋数が9ではありません: "${rankStr}"`);
  }
  return squares;
}

function toPiece(token: string): BoardPiece {
  const letter = token.replace("+", "");
  const color: BoardPiece["color"] = letter === letter.toLowerCase() ? "gote" : "sente";
  const piece = (token.startsWith("+") ? "+" : "") + letter.toUpperCase();
  return { piece, color };
}

// 手番(b=先手/w=後手)をSFENから取り出す。
export function parseSfenTurn(sfen: string): "sente" | "gote" {
  const turn = sfen.split(" ")[1];
  return turn === "w" ? "gote" : "sente";
}

// 持ち駒部分(例: "S2Pb"、無ければ"-")を { 駒種: 枚数 } の一覧に分解する。
export function parseSfenHands(sfen: string): { sente: Record<string, number>; gote: Record<string, number> } {
  const handsPart = sfen.split(" ")[2] ?? "-";
  const sente: Record<string, number> = {};
  const gote: Record<string, number> = {};
  if (handsPart === "-") return { sente, gote };

  let i = 0;
  while (i < handsPart.length) {
    let countStr = "";
    while (handsPart[i] !== undefined && handsPart[i]! >= "0" && handsPart[i]! <= "9") {
      countStr += handsPart[i];
      i += 1;
    }
    const letter = handsPart[i];
    if (letter === undefined) break;
    i += 1;
    const count = countStr === "" ? 1 : Number(countStr);
    const target = letter === letter.toLowerCase() ? gote : sente;
    target[letter.toUpperCase()] = (target[letter.toUpperCase()] ?? 0) + count;
  }
  return { sente, gote };
}
