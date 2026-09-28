// STEP ANSWER 追加作業 ANSWER-DIRECT(docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2)。「浅い読みで見えた分かれ道」
// (§9.1 の 2.)を測る段の純粋関数。**測る段だけ**(PDF は report-pdf/render_direct.py)。
//
// 【追記(司令塔 e3、監査前の仕様追記 2 点。docs §9 にも同じ内容)】
// 1. 「局」の番号が組(3 分の組・10 分の組)をまたいで重なる(1〜10 が両方にある)ため、`group`(組のラベル。
//    CLI が `--group`/`--patient`+`--time-limit-sec` から決める。無ければ組の順の番号)を 1 局ぶんの結合の
//    引数・出力の両方に足した。
// 2. 「評価の差」を `topGapCp`(第 1 候補と第 2 候補の差)から、**実戦の手が第 1 候補からどれだけ下がったか**
//    (whatif-v2 の `loss`。第 1 候補の評価 − 実戦の手の評価)に変えた(`actualGapCp`)。実戦の手が候補 5 つに
//    無いとき(`loss.isLowerBound`)は「少なくともこれだけ」という下限の値であり、実戦の手そのものの正確な
//    差ではないため、`actualGapCp` は null にする(表には「—」)。並び順もこれの大きい順(null は最後)に
//    変えた。`topGapCp` は出力の JSON には残す(表には出さない)。
//
// 【このファイルがやること】
// - whatif-v2 の position 行(`scenes.fork` が true のもの)と、read.ts の分かれ道の行を `ply` で結合する
//   (`lib/type.ts` の生成モードと**同じやり方**。type.ts と同じく、read 側の行は fork 行だけが渡される
//   前提 ― read.ts の出力そのもの)
// - `firstVisibleNodes` が null でなく `TYPE_VALUES.nodeShallowMaxNodes`(1 万)以下の分かれ道だけを選ぶ
//   (1 万ちょうどは含む)
// - 局をまたいだ一覧(実戦との差=`actualGapCp` の大きい順。null は最後)と、印の数(第 1 候補の tags(READ の印:
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

/** whatif-v2 の `loss`(第 1 候補の評価 − 実戦の手の評価)のうち、この段が使う分だけ。 */
export interface DirectAnswersLossInput {
  /** cp 同士のときだけの実際の cp 差(詰みが絡めば null)。 */
  cpValue: number | null;
  /** 実戦の手が候補(K 個)に無く、最後の候補との差を下限として使ったか。 */
  isLowerBound: boolean;
}

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
  /** 実戦の手が第 1 候補からどれだけ下がったか(whatif-v2 の `loss`)。候補が無い等で測れなければ null。 */
  loss: DirectAnswersLossInput | null;
  /** whatif-v2 の `scenes.fork`。 */
  fork: boolean;
}

/**
 * 表に出す「実戦との差」(司令塔の仕様追記 2.)。実戦の手が候補 5 つに無いとき(`isLowerBound`)は
 * 「少なくともこれだけ」という下限の値であり、実戦の手そのものの正確な差ではないため null にする。
 * 詰みが絡む等で `cpValue` が無いときも null。
 */
export function actualGapCpOf(loss: DirectAnswersLossInput | null): number | null {
  if (loss === null) return null;
  if (loss.isLowerBound) return null;
  return loss.cpValue;
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
  /** 組のラベル(「3 分」「10 分」等。CLI が決める。司令塔の仕様追記 1.)。 */
  group: string;
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
  /** 第 1 候補と第 2 候補の差(表には出さない。JSON には残す ― 司令塔の仕様追記 2.)。 */
  topGapCp: number | null;
  /** 表に出す「実戦との差」(`actualGapCpOf` で `loss` から作る)。 */
  actualGapCp: number | null;
  firstVisibleNodes: number;
}

export interface DirectAnswersGameJoinResult {
  answers: DirectAnswer[];
  /** この局の分かれ道の総数(read の分かれ道の行のうち、whatif-v2 と結合できた数。1 万以下の選別をする前)。 */
  forkCount: number;
}

/**
 * 1 局ぶんの whatif-v2・read の行を `ply` で結合し、浅い読み(`firstVisibleNodes` が null でなく
 * `values.nodeShallowMaxNodes` 以下)の分かれ道だけを選ぶ(計画 §9.2)。`group` は組のラベル(CLI が決める。
 * 司令塔の仕様追記 1.)。
 * `lib/type.ts` の生成モードと同じやり方: read 側に無い行(read.ts 側で候補 0 件等の理由で除外された、
 * 計画に無い理論上の状態)は数えずに読み飛ばす。
 */
export function joinDirectAnswersGame(
  kifuId: string,
  gameNo: number,
  group: string,
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
      group,
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
      actualGapCp: actualGapCpOf(position.loss),
      firstVisibleNodes: readPosition.firstVisibleNodes,
    });
  }
  return { answers, forkCount };
}

// ---- 局をまたいだ並び順 ----

/** 実戦との差(`actualGapCp`)の大きい順(司令塔の仕様追記 2.)。null(実戦の手が候補 5 つに無い・詰みが絡む等)は最後に置く。 */
export function sortDirectAnswers(answers: readonly DirectAnswer[]): DirectAnswer[] {
  return [...answers].sort((a, b) => {
    if (a.actualGapCp === null && b.actualGapCp === null) return 0;
    if (a.actualGapCp === null) return 1;
    if (b.actualGapCp === null) return -1;
    return b.actualGapCp - a.actualGapCp;
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

/**
 * 組のラベル(`report-pdf/check_answer.py` の `tag_of_time_limit_sec` と**同じ対応**。
 * 司令塔の仕様追記 1、2026-09-24)。`direct_answers.json` の `answers[].group` に入る値。
 *
 * **2026-09-29 に `scripts/playtest/directAnswers.ts` からここへ移した。**段 `exit-render` の表紙
 * (`exit_cover.py --group`)が同じラベルを要るため ― CLI に置いたままだと `lib/deliver.ts` が
 * 写しを持つことになる(`Board` が 4 実装に散った P-111 と同じ病気)。
 */
export function groupLabelOfTimeLimitSec(sec: number): string {
  if (sec === 180) return "3 分";
  if (sec === 600) return "10 分";
  throw new Error(`--time-limit-sec は 180 か 600 です(${sec})`);
}
