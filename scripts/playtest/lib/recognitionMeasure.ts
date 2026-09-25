// STEP OPEN-2(docs/LANE_DIAG_LOG_2026-09.md §12.8)。
// 固定棋譜の並びについて「形・狙い・戦型の認識が立った局面の数」を数える純粋関数。
//
// 【これは何か】
// 知識レーンが scratchpad の使い捨て台本(measure.ts / openmeasure.ts)で測っていた
// 数え方を、追跡されるファイルへ写したもの。写したのは**数え方だけ**で、判定は
// apps/server の本番関数(analyzeShapeFormationFromEvents / detectIntentsFromEvents /
// analyzeOpeningFormationFromEvents)をそのまま呼ぶ。
//
// 【このファイルが絶対にやらないこと】
// - 新しい判定・新しい閾値を書くこと。I-9 相当の「証拠 1 件以下・欠け 2 件以上」は
//   invariants/i9-shape-claim-without-evidence.ts の定数を import する(ここで数を書かない)。
// - 形・戦型・狙いの良し悪しを言うこと。数えるのは「その状態の局面がいくつあったか」だけ。
// - 局の中身(玉・飛の位置、手、局面)を出すこと。使い捨て台本にあった `snap`(玉・飛の
//   位置の文字列)は**写していない**。出るのは数と、固定棋譜の id だけ。
// - ファイルを読む・書く(入出力は CLI 側 scripts/playtest/recognitionMeasure.ts の責務)。
//
// 【数え方(使い捨て台本と同じ。ここを変えると二本立ての校正が成り立たない)】
// - 分母 = 先手番の局面 ply 0, 2, 4, … ≤ min(maxPly, 手数)。`maxPly` 0 は「全手」。
//   docs/BASELINE_2026-09-12.md §2 の「全手数」と同じ数え方(初期局面を含む)。
// - 「立つ」= status が forming か completed(狙いは matchStatus が forming か matched)。
// - 「強い」= completed(狙いは matched)か、証拠が 2 件以上。
// - 沈黙 = 強いものが 1 つも無い局面(自分側・相手側・全体をそれぞれ数える)。
// - I-9 相当 = 立った行のうち 証拠 ≤ I9_MAX_EVIDENCE かつ 欠け ≥ I9_MIN_MISSING。
//   形は forming/completed の両方に当て、戦型は forming の行だけに当てる
//   (開発・診断レーン §12.7 の訂正。openmeasure.ts と同じ)。
// - **局数の欄(STEP OPEN-2b)は「延べ局面」ではなく「局の数」**。1 局の中で同じ id が
//   何局面で立っても 1 と数える(rows に id の集合を持ち、byGroup でその集合を足し上げる)。

import { makeSquareName } from "shogiops/util";

import { analyzeShapeFormationFromEvents } from "../../../apps/server/src/analysis/shapeFormationAnalyzer.js";
import { detectIntentsFromEvents } from "../../../apps/server/src/analysis/intentDetector.js";
import {
  analyzeOpeningFormationFromEvents,
  type OpeningDefinition,
} from "../../../apps/server/src/analysis/openingDetector.js";
import { replayMoveHistory } from "../../../apps/server/src/analysis/moveHistory.js";
import type { IntentDefinition } from "../../../apps/server/src/analysis/intentRepository.js";
import type { ShapeDefinition } from "../../../apps/server/src/analysis/shapeRepository.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { I9_MAX_EVIDENCE, I9_MIN_MISSING } from "../invariants/i9-shape-claim-without-evidence.js";

export class RecognitionMeasureError extends Error {}

/** 測る対象の 1 局(固定棋譜の中身)。棋譜ファイルの読み込みは呼び出し側が行う。 */
export interface MeasuredGame {
  /** 集計の組(例: 人ごと)。byGroup のキーになる */
  group: string;
  /** 固定棋譜の id。rows に出るのはこれだけで、ファイル名・人の名前は出さない */
  id: string;
  moves: string[];
  startSfen?: string;
}

export interface MeasureRecognitionOptions {
  shapes: ShapeDefinition[];
  intents: IntentDefinition[];
  /** 戦型。渡さないときは空(= open* の欄は「戦型を 1 件も読んでいない」ときの数になる) */
  openings?: OpeningDefinition[];
  /** 0 は全手。正の数は「その ply まで」 */
  maxPly: number;
}

/** 1 局分の数。欄の意味は冒頭の「数え方」を参照。 */
export interface GameRow {
  group: string;
  id: string;
  /** 手数(棋譜の moves の数) */
  plies: number;
  /** 分母。ply 0, 2, … の局面の数 */
  positions: number;

  // --- 形(data/shapes) ---
  /** 形が 1 つでも立った局面 */
  recShape: number;
  /** 強い形(completed か証拠 2 件以上)が 1 つでもあった局面 */
  recShapeEvid2: number;
  /** 強い形のうち自分側(side !== "opponent")があった局面 */
  recEvid2Self: number;
  /** 強い形のうち相手側(side === "opponent")があった局面 */
  recEvid2Opp: number;
  /** 強い形が 1 つも無かった局面(形の沈黙) */
  silentEvid2: number;
  /** 形の沈黙のうち、先手玉が 5i(初期位置)にあった局面 */
  silentEvid2King5i: number;

  // --- 狙い(data/intents) ---
  /** 狙いが 1 つでも立った局面 */
  recIntent: number;
  /** 強い狙い(matched か証拠 2 件以上)が 1 つでもあった局面 */
  recIntent2: number;

  // --- 形と狙いを合わせて ---
  /** 形か狙いが 1 つでも立った局面 */
  recAny: number;
  /** 形も狙いも 1 つも立たなかった局面 */
  silent: number;

  // --- I-9 相当(形) ---
  /** 立った形のうち I-9 相当だった件数(局面ではなく件数) */
  i9type: number;
  /** そのうち相手側 */
  i9Opp: number;

  // --- 内訳 ---
  /** 形 id ごとの「立った局面」の件数 */
  shapeHits: Record<string, number>;
  /** 形 id ごとの「completed だった局面」の件数(byGroup の gamesCompleted のもと) */
  shapeCompleted: Record<string, number>;
  /** 形 id ごとの matchScore の最大値(byGroup の gamesBest75 のもと) */
  shapeBest: Record<string, number>;
  /** 狙い id ごとの「立った局面」の件数 */
  intentHits: Record<string, number>;

  // --- この局で立った / 完成した id の集合(STEP OPEN-2b。byGroup の局数のもと) ---
  // 局面の数ではなく「この局に 1 局面でもあったか」だけを持つ。並びは id の昇順。
  /** この局で 1 局面でも forming か completed だった形の id */
  shapeOnIds: string[];
  /** この局で 1 局面でも completed だった形の id */
  shapeCompIds: string[];
  /** この局で 1 局面でも forming か matched だった狙いの id */
  intentOnIds: string[];
  /** この局で 1 局面でも matched だった狙いの id */
  intentCompIds: string[];
  /** この局で 1 局面でも forming か completed だった戦型の id */
  openOnIds: string[];
  /** この局で 1 局面でも completed だった戦型の id */
  openCompIds: string[];

  // --- 戦型(openings) ---
  /** 強い戦型が自分側に無かった局面 */
  openSilentSelf: number;
  /** 強い戦型が相手側に無かった局面 */
  openSilentOpp: number;
  /** 強い戦型がどちらにも無かった局面 */
  openSilentAny: number;
  /** forming の戦型のうち I-9 相当だった件数(自分側) */
  openI9Self: number;
  /** 同(相手側) */
  openI9Opp: number;
  /** completed だった戦型の件数 */
  openCompleted: number;
  /** そのうち証拠 0 件だったもの(P-86 の型) */
  openCompletedNoEvidence: number;
  /** forming だった戦型の件数 */
  openForming: number;
  /** 証拠 0 の completed を戦型 id ごとに数えたもの */
  openCompNoEvidById: Record<string, number>;
}

/**
 * 組ごとの合計。rows の数をそのまま足した欄と、**局数**で数える欄(`gamesCompleted`・
 * `gamesBest75` と、STEP OPEN-2b で足した `*OnGames`・`*CompGames` の 6 欄)からなる。
 */
export interface GroupTotals {
  games: number;
  plies: number;
  positions: number;
  recShape: number;
  recShapeEvid2: number;
  recEvid2Self: number;
  recEvid2Opp: number;
  silentEvid2: number;
  silentEvid2King5i: number;
  recIntent: number;
  recIntent2: number;
  recAny: number;
  silent: number;
  i9type: number;
  i9Opp: number;
  shapeHits: Record<string, number>;
  /** 形 id ごとの「completed が 1 局面でもあった局数」(局面数ではない) */
  gamesCompleted: Record<string, number>;
  /** 形 id ごとの「matchScore の最大が 0.75 以上だった局数」 */
  gamesBest75: Record<string, number>;
  intentHits: Record<string, number>;

  // --- レコード 1 件ごとの局数(STEP OPEN-2b)。id → その組で「立った / 完成した」局の数 ---
  // 延べ局面ではない(同じ局の何局面で立っても 1)。`shapeCompGames` は `gamesCompleted` と同じ値になる。
  /** 形 id ごとの「forming か completed が 1 局面でもあった局数」 */
  shapeOnGames: Record<string, number>;
  /** 形 id ごとの「completed が 1 局面でもあった局数」 */
  shapeCompGames: Record<string, number>;
  /** 狙い id ごとの「forming か matched が 1 局面でもあった局数」 */
  intentOnGames: Record<string, number>;
  /** 狙い id ごとの「matched が 1 局面でもあった局数」 */
  intentCompGames: Record<string, number>;
  /** 戦型 id ごとの「forming か completed が 1 局面でもあった局数」 */
  openOnGames: Record<string, number>;
  /** 戦型 id ごとの「completed が 1 局面でもあった局数」 */
  openCompGames: Record<string, number>;

  openSilentSelf: number;
  openSilentOpp: number;
  openSilentAny: number;
  openI9Self: number;
  openI9Opp: number;
  openCompleted: number;
  openCompletedNoEvidence: number;
  openForming: number;
  openCompNoEvidById: Record<string, number>;
}

export interface RecognitionMeasureResult {
  byGroup: Record<string, GroupTotals>;
  rows: GameRow[];
}

/** byGroup の gamesBest75 の境目。使い捨て台本の 0.75 をそのまま写したもので、新しい閾値ではない。 */
const BEST_SCORE_THRESHOLD = 0.75;

/** 先手玉が初期位置かを見るためのマス(silentEvid2King5i)。将棋の判断ではなく位置の照合。 */
const SENTE_KING_INITIAL_SQUARE = "5i";

function emptyRow(group: string, id: string, plies: number): GameRow {
  return {
    group,
    id,
    plies,
    positions: 0,
    recShape: 0,
    recShapeEvid2: 0,
    recEvid2Self: 0,
    recEvid2Opp: 0,
    silentEvid2: 0,
    silentEvid2King5i: 0,
    recIntent: 0,
    recIntent2: 0,
    recAny: 0,
    silent: 0,
    i9type: 0,
    i9Opp: 0,
    shapeHits: {},
    shapeCompleted: {},
    shapeBest: {},
    intentHits: {},
    shapeOnIds: [],
    shapeCompIds: [],
    intentOnIds: [],
    intentCompIds: [],
    openOnIds: [],
    openCompIds: [],
    openSilentSelf: 0,
    openSilentOpp: 0,
    openSilentAny: 0,
    openI9Self: 0,
    openI9Opp: 0,
    openCompleted: 0,
    openCompletedNoEvidence: 0,
    openForming: 0,
    openCompNoEvidById: {},
  };
}

function emptyTotals(): GroupTotals {
  return {
    games: 0,
    plies: 0,
    positions: 0,
    recShape: 0,
    recShapeEvid2: 0,
    recEvid2Self: 0,
    recEvid2Opp: 0,
    silentEvid2: 0,
    silentEvid2King5i: 0,
    recIntent: 0,
    recIntent2: 0,
    recAny: 0,
    silent: 0,
    i9type: 0,
    i9Opp: 0,
    shapeHits: {},
    gamesCompleted: {},
    gamesBest75: {},
    intentHits: {},
    shapeOnGames: {},
    shapeCompGames: {},
    intentOnGames: {},
    intentCompGames: {},
    openOnGames: {},
    openCompGames: {},
    openSilentSelf: 0,
    openSilentOpp: 0,
    openSilentAny: 0,
    openI9Self: 0,
    openI9Opp: 0,
    openCompleted: 0,
    openCompletedNoEvidence: 0,
    openForming: 0,
    openCompNoEvidById: {},
  };
}

/**
 * 分母になる ply の並び(0, 2, 4, … ≤ min(maxPly, plies))。
 * `maxPly` が 0(または負)のときは全手。手数が奇数でも最後は「先手番の局面」で止まる。
 */
export function plyStepsOf(plies: number, maxPly: number): number[] {
  const last = maxPly > 0 ? Math.min(maxPly, plies) : plies;
  const steps: number[] = [];
  for (let ply = 0; ply <= last; ply += 2) steps.push(ply);
  return steps;
}

/** 先手玉のマス(見つからなければ "-")。局面の中身は出さず、5i かどうかの照合にだけ使う。 */
function senteKingSquare(sfen: string): string {
  const pos = parsePosition(sfen);
  const squares = [...pos.board.pieces("sente", "king")];
  const square = squares[0];
  // マス名への変換は shogiops の makeSquareName に任せる(自前で座標を計算しない)。
  return square === undefined ? "-" : makeSquareName(square);
}

function bump(counter: Record<string, number>, key: string): void {
  counter[key] = (counter[key] ?? 0) + 1;
}

/**
 * 固定棋譜の並びについて、形・狙い・戦型の認識を数える。
 *
 * **判定は本番関数がすべて行う。** この関数は「どの局面で呼ぶか」と「何を数えるか」だけを持つ。
 */
export function measureRecognition(
  games: readonly MeasuredGame[],
  options: MeasureRecognitionOptions,
): RecognitionMeasureResult {
  const { shapes, intents, maxPly } = options;
  const openings = options.openings ?? [];

  const rows: GameRow[] = [];

  for (const game of games) {
    const { events, sfens } = replayMoveHistory(game.moves, game.startSfen);
    const row = emptyRow(game.group, game.id, game.moves.length);
    // 局数の欄のもと。局面ごとに足すのではなく、この局に 1 度でも出た id を集合で持つ。
    const shapeOnSet = new Set<string>();
    const shapeCompSet = new Set<string>();
    const intentOnSet = new Set<string>();
    const intentCompSet = new Set<string>();
    const openOnSet = new Set<string>();
    const openCompSet = new Set<string>();

    for (const ply of plyStepsOf(game.moves.length, maxPly)) {
      const sfen = sfens[ply];
      if (sfen === undefined) {
        throw new RecognitionMeasureError(`再生した局面が足りません(id="${game.id}" ply=${ply})`);
      }
      const prefix = events.slice(0, ply);
      row.positions += 1;

      // --- 形 ---
      const shapeResults = analyzeShapeFormationFromEvents(sfen, prefix, { shapes });
      const shapeOn = shapeResults.filter((r) => r.status === "forming" || r.status === "completed");
      const shapeStrong = (r: (typeof shapeResults)[number]): boolean =>
        r.status === "completed" || r.formationEvidence.length >= 2;

      if (shapeOn.some((r) => r.side !== "opponent" && shapeStrong(r))) row.recEvid2Self += 1;
      if (shapeOn.some((r) => r.side === "opponent" && shapeStrong(r))) row.recEvid2Opp += 1;
      if (shapeOn.length > 0) row.recShape += 1;
      if (shapeOn.some(shapeStrong)) {
        row.recShapeEvid2 += 1;
      } else {
        row.silentEvid2 += 1;
        if (senteKingSquare(sfen) === SENTE_KING_INITIAL_SQUARE) row.silentEvid2King5i += 1;
      }

      for (const r of shapeResults) {
        if (r.matchScore > (row.shapeBest[r.shapeId] ?? 0)) row.shapeBest[r.shapeId] = r.matchScore;
        if (r.status === "completed") {
          bump(row.shapeCompleted, r.shapeId);
          shapeCompSet.add(r.shapeId);
        }
      }
      for (const r of shapeOn) {
        bump(row.shapeHits, r.shapeId);
        shapeOnSet.add(r.shapeId);
        if (r.formationEvidence.length <= I9_MAX_EVIDENCE && r.missingSquares.length >= I9_MIN_MISSING) {
          row.i9type += 1;
          if (r.side === "opponent") row.i9Opp += 1;
        }
      }

      // --- 狙い ---
      const intentResults = detectIntentsFromEvents(prefix, { intents });
      const intentOn = intentResults.filter(
        (r) => r.matchStatus === "forming" || r.matchStatus === "matched",
      );
      if (intentOn.some((r) => r.matchStatus === "matched" || r.matchedSignatures.length >= 2)) {
        row.recIntent2 += 1;
      }
      for (const r of intentOn) {
        bump(row.intentHits, r.intentId);
        intentOnSet.add(r.intentId);
        if (r.matchStatus === "matched") intentCompSet.add(r.intentId);
      }
      if (intentOn.length > 0) row.recIntent += 1;

      if (shapeOn.length > 0 || intentOn.length > 0) row.recAny += 1;
      else row.silent += 1;

      // --- 戦型 ---
      const openingResults = analyzeOpeningFormationFromEvents(sfen, prefix, openings);
      const openingOn = openingResults.filter(
        (r) => r.status === "forming" || r.status === "completed",
      );
      const openingStrong = (r: (typeof openingResults)[number]): boolean =>
        r.status === "completed" || r.formationEvidence.length >= 2;

      if (!openingOn.some((r) => r.side !== "opponent" && openingStrong(r))) row.openSilentSelf += 1;
      if (!openingOn.some((r) => r.side === "opponent" && openingStrong(r))) row.openSilentOpp += 1;
      if (!openingOn.some(openingStrong)) row.openSilentAny += 1;

      for (const r of openingOn) {
        openOnSet.add(r.openingId);
        if (r.status === "completed") {
          openCompSet.add(r.openingId);
          row.openCompleted += 1;
          if (r.formationEvidence.length === 0) {
            row.openCompletedNoEvidence += 1;
            bump(row.openCompNoEvidById, r.openingId);
          }
        } else {
          row.openForming += 1;
          // I-9 相当は「申告している行(forming)」に当てる(§12.7 の訂正)。
          if (r.formationEvidence.length <= I9_MAX_EVIDENCE && r.missingSquares.length >= I9_MIN_MISSING) {
            if (r.side === "opponent") row.openI9Opp += 1;
            else row.openI9Self += 1;
          }
        }
      }
    }

    const sorted = (ids: Set<string>): string[] => [...ids].sort();
    row.shapeOnIds = sorted(shapeOnSet);
    row.shapeCompIds = sorted(shapeCompSet);
    row.intentOnIds = sorted(intentOnSet);
    row.intentCompIds = sorted(intentCompSet);
    row.openOnIds = sorted(openOnSet);
    row.openCompIds = sorted(openCompSet);

    rows.push(row);
  }

  const byGroup: Record<string, GroupTotals> = {};
  for (const row of rows) {
    const totals = (byGroup[row.group] ??= emptyTotals());
    totals.games += 1;
    totals.plies += row.plies;
    totals.positions += row.positions;
    totals.recShape += row.recShape;
    totals.recShapeEvid2 += row.recShapeEvid2;
    totals.recEvid2Self += row.recEvid2Self;
    totals.recEvid2Opp += row.recEvid2Opp;
    totals.silentEvid2 += row.silentEvid2;
    totals.silentEvid2King5i += row.silentEvid2King5i;
    totals.recIntent += row.recIntent;
    totals.recIntent2 += row.recIntent2;
    totals.recAny += row.recAny;
    totals.silent += row.silent;
    totals.i9type += row.i9type;
    totals.i9Opp += row.i9Opp;
    totals.openSilentSelf += row.openSilentSelf;
    totals.openSilentOpp += row.openSilentOpp;
    totals.openSilentAny += row.openSilentAny;
    totals.openI9Self += row.openI9Self;
    totals.openI9Opp += row.openI9Opp;
    totals.openCompleted += row.openCompleted;
    totals.openCompletedNoEvidence += row.openCompletedNoEvidence;
    totals.openForming += row.openForming;

    for (const [id, count] of Object.entries(row.shapeHits)) {
      totals.shapeHits[id] = (totals.shapeHits[id] ?? 0) + count;
    }
    for (const [id, count] of Object.entries(row.intentHits)) {
      totals.intentHits[id] = (totals.intentHits[id] ?? 0) + count;
    }
    for (const [id, count] of Object.entries(row.openCompNoEvidById)) {
      totals.openCompNoEvidById[id] = (totals.openCompNoEvidById[id] ?? 0) + count;
    }
    // ここから下は「局数」で数える(局面の数ではない)。1 局につき 1 しか足さない。
    for (const id of Object.keys(row.shapeCompleted)) bump(totals.gamesCompleted, id);
    for (const [id, best] of Object.entries(row.shapeBest)) {
      if (best >= BEST_SCORE_THRESHOLD) bump(totals.gamesBest75, id);
    }
    for (const id of row.shapeOnIds) bump(totals.shapeOnGames, id);
    for (const id of row.shapeCompIds) bump(totals.shapeCompGames, id);
    for (const id of row.intentOnIds) bump(totals.intentOnGames, id);
    for (const id of row.intentCompIds) bump(totals.intentCompGames, id);
    for (const id of row.openOnIds) bump(totals.openOnGames, id);
    for (const id of row.openCompIds) bump(totals.openCompGames, id);
  }

  return { byGroup, rows };
}
