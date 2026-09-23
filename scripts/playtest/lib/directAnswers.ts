// STEP ANSWER 追加作業 ANSWER-DIRECT(docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2)。「浅い読みで見えた分かれ道」
// (§9.1 の 2.)を測る段の純粋関数。**測る段だけ**(PDF は report-pdf/render_direct.py)。
//
// 【このファイルがやること】
// - whatif-v2 の position 行(`scenes.fork` が true のもの)と、read.ts の分かれ道の行を `ply` で結合する
//   (`lib/type.ts` の生成モードと**同じやり方**。type.ts と同じく、read 側の行は fork 行だけが渡される
//   前提 ― read.ts の出力そのもの)
// - `firstVisibleNodes` が null でなく `TYPE_VALUES.nodeShallowMaxNodes`(1 万)以下の分かれ道だけを選ぶ
//   (1 万ちょうどは含む)
// - 局をまたいだ一覧(評価の差=`topGapCp` の大きい順。null は最後)と、印の数(第 1 候補の tags(READ の印:
//   取る/打つ/王手/捨て駒/引く 等)ごとの n・第 1 候補の side ごとの n・実戦の tags ごとの n・局数・総数・
//   分かれ道の総数)を組む
//
// 【「性質(tags)」の出どころについての判断(実装担当の判断)】
// docs §9.1 は「第 1 候補の性質(READ の印: 取る/打つ/王手/捨て駒/引く、と whatif-v2 の側)」と書く。
// この 5 つの語(取る/打つ/王手/捨て駒/引く)は read.ts の `ReadMoveMarks`(capture/drop/givesCheck/
// sacrifice/retreat)と 1 対 1 で対応する一方、whatif-v2 自身の `WhatifMoveTags` には打つ・捨て駒・引くに
// 当たる印が無い。§9.2 の「作るもの」の文は read の fork 行から `firstVisibleNodes` だけを挙げているが、
// §9.1 の内容(READ の印)を出すには read の `top1Tags`・`actualTags` も要る。そのため、このファイルでは
// **`tags` = read.ts の `top1Tags`/`actualTags`、`side` = whatif-v2 の `top1Side`/`actualSide`** として
// 結合する(§9.1 の「(READ の印...、と whatif-v2 の側)」という書き分けと一致する解釈)。
//
// 【このファイルが絶対にやらないこと】
// - エンジンを起動すること・ファイルの読み書き(CLI(scripts/playtest/directAnswers.ts)の役目)
// - 将棋の判断・評価・閾値・文言。名前を付けること(印は key のまま扱う ― lib/type.ts と同じ考え方)
// - 新しい閾値を置くこと(`TYPE_VALUES.nodeShallowMaxNodes` を import して使うだけ)

import { READ_TAG_NAMES, type ReadMoveMarks, type ReadTagName } from "./read.js";
import { TYPE_VALUES, type TypeValues, type WhatifSideRaw } from "./type.js";

export class DirectAnswersError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DirectAnswersError";
  }
}

// ---- 1 局ぶんの結合の入力 ----

/** whatif-v2 の position 行から、この段が使う分だけ(計画「作るもの」1.)。 */
export interface DirectAnswersWhatifPositionInput {
  ply: number;
  displayPly: number;
  sfen: string;
  top1Move: string;
  pv: readonly string[];
  top1Side: WhatifSideRaw;
  actualMove: string;
  actualSide: WhatifSideRaw;
  topGapCp: number | null;
  /** whatif-v2 の `scenes.fork`。 */
  fork: boolean;
}

/** read.ts の分かれ道の行から、この段が使う分だけ。read.ts の出力は fork 行だけなので、渡された行はすべて
 * 分かれ道である前提(`lib/type.ts` の生成モードと同じ前提)。 */
export interface DirectAnswersReadPositionInput {
  ply: number;
  firstVisibleNodes: number | null;
  top1Tags: ReadMoveMarks;
  actualTags: ReadMoveMarks;
}

// ---- 1 件の「直接の答え」 ----

export interface DirectAnswer {
  kifuId: string;
  gameNo: number;
  displayPly: number;
  sfen: string;
  actualMove: string;
  top1Move: string;
  pv: readonly string[];
  top1Tags: ReadMoveMarks;
  top1Side: WhatifSideRaw;
  actualTags: ReadMoveMarks;
  actualSide: WhatifSideRaw;
  topGapCp: number | null;
  firstVisibleNodes: number;
}

export interface DirectAnswersGameJoinResult {
  answers: DirectAnswer[];
  /** この局の分かれ道の総数(read の分かれ道の行のうち、whatif-v2 と結合できた数。1 万以下の選別をする前)。 */
  forkCount: number;
}

/**
 * 1 局ぶんの whatif-v2・read の行を `ply` で結合し、浅い読み(`firstVisibleNodes` が null でなく
 * `values.nodeShallowMaxNodes` 以下)の分かれ道だけを選ぶ(計画 §9.2)。
 * `lib/type.ts` の生成モードと同じやり方: read 側に無い行(read.ts 側で候補 0 件等の理由で除外された、
 * 計画に無い理論上の状態)は数えずに読み飛ばす。
 */
export function joinDirectAnswersGame(
  kifuId: string,
  gameNo: number,
  whatifPositions: readonly DirectAnswersWhatifPositionInput[],
  readPositions: readonly DirectAnswersReadPositionInput[],
  values: TypeValues = TYPE_VALUES,
): DirectAnswersGameJoinResult {
  const readByPly = new Map<number, DirectAnswersReadPositionInput>();
  for (const position of readPositions) readByPly.set(position.ply, position);

  const answers: DirectAnswer[] = [];
  let forkCount = 0;
  for (const position of whatifPositions) {
    if (!position.fork) continue;
    const readPosition = readByPly.get(position.ply);
    if (readPosition === undefined) continue; // read.ts 側で除外された分かれ道(既知の限界。lib/type.ts と同じ)
    forkCount++;
    if (readPosition.firstVisibleNodes === null) continue;
    if (readPosition.firstVisibleNodes > values.nodeShallowMaxNodes) continue;
    answers.push({
      kifuId,
      gameNo,
      displayPly: position.displayPly,
      sfen: position.sfen,
      actualMove: position.actualMove,
      top1Move: position.top1Move,
      pv: position.pv,
      top1Tags: readPosition.top1Tags,
      top1Side: position.top1Side,
      actualTags: readPosition.actualTags,
      actualSide: position.actualSide,
      topGapCp: position.topGapCp,
      firstVisibleNodes: readPosition.firstVisibleNodes,
    });
  }
  return { answers, forkCount };
}

// ---- 局をまたいだ並び順 ----

/** 評価の差(`topGapCp`)の大きい順(計画「出力」)。null(第 1・第 2 候補のどちらかが詰み等)は最後に置く。 */
export function sortDirectAnswers(answers: readonly DirectAnswer[]): DirectAnswer[] {
  return [...answers].sort((a, b) => {
    if (a.topGapCp === null && b.topGapCp === null) return 0;
    if (a.topGapCp === null) return 1;
    if (b.topGapCp === null) return -1;
    return b.topGapCp - a.topGapCp;
  });
}

// ---- 印の数 ----

const WHATIF_SIDE_VALUES: readonly WhatifSideRaw[] = ["attack", "defense", "both", "none"];

export interface DirectAnswersCounts {
  /** 第 1 候補の tags(READ の印)ごとの n。 */
  top1TagCounts: Record<ReadTagName, number>;
  /** 第 1 候補の side ごとの n。 */
  top1SideCounts: Record<WhatifSideRaw, number>;
  /** 実戦の tags(READ の印)ごとの n。 */
  actualTagCounts: Record<ReadTagName, number>;
  /** 選ばれた分かれ道が 1 つ以上ある局の数。 */
  gamesCount: number;
  /** 選ばれた分かれ道の総数(= answers.length)。 */
  totalCount: number;
  /** 局をまたいだ分かれ道の総数(選別をする前。whatif-v2・read が結合できた数の合計)。 */
  totalForkCount: number;
}

/** 選ばれた一覧(`answers`)から印の数を数える(計画「出力」)。 */
export function directAnswersCountsOf(games: readonly { forkCount: number }[], answers: readonly DirectAnswer[]): DirectAnswersCounts {
  const top1TagCounts = {} as Record<ReadTagName, number>;
  const actualTagCounts = {} as Record<ReadTagName, number>;
  for (const tag of READ_TAG_NAMES) {
    top1TagCounts[tag] = 0;
    actualTagCounts[tag] = 0;
  }
  const top1SideCounts = {} as Record<WhatifSideRaw, number>;
  for (const side of WHATIF_SIDE_VALUES) top1SideCounts[side] = 0;

  const gameIds = new Set<string>();
  for (const answer of answers) {
    for (const tag of READ_TAG_NAMES) {
      if (answer.top1Tags[tag]) top1TagCounts[tag]++;
      if (answer.actualTags[tag]) actualTagCounts[tag]++;
    }
    top1SideCounts[answer.top1Side]++;
    gameIds.add(answer.kifuId);
  }

  return {
    top1TagCounts,
    top1SideCounts,
    actualTagCounts,
    gamesCount: gameIds.size,
    totalCount: answers.length,
    totalForkCount: games.reduce((sum, game) => sum + game.forkCount, 0),
  };
}

// ---- 局をまたいだファイル全体 ----

export interface DirectAnswersFile {
  values: TypeValues;
  answers: DirectAnswer[];
  counts: DirectAnswersCounts;
}

/** 局ごとの結合結果(`joinDirectAnswersGame` の出力の列)から、`direct_answers.json` の中身を組む。 */
export function buildDirectAnswersFile(games: readonly DirectAnswersGameJoinResult[], values: TypeValues = TYPE_VALUES): DirectAnswersFile {
  const answers = sortDirectAnswers(games.flatMap((game) => game.answers));
  const counts = directAnswersCountsOf(games, answers);
  return { values, answers, counts };
}
