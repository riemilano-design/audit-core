// STEP OBS-5'(docs/LANE_DIAG_LOG_2026-09.md §12.6)。1 周(OBS-3b)で不足した観測項目 2 つ
// (「組と局・手の対応」「段ごとの手数あたり」)を、既存の材料の写しで作る純粋関数。
//
// 【このファイルがやること】
// - `buildObsExtra(sources, gitHead, dirty)`: `lib/reportData.ts` の `buildGames`・`buildPatientGames`・
//   `countedPairsOf`・`ownMoveTimesOf`・`isTimeUpLoss`・`phaseOf`・`displayPlyOf`・`spentBucketIndexOf`・
//   `moveSecondsOf`(すべて既存。ここでは新しい判定を作らない)を組み合わせ、`obs_extra.json` の中身を作る。
// - 中央値(`phaseSecPerMoveMedians`)だけは計算あり。算法は `lib/timeCause.ts` の `medianOf` をそのまま使う
//   (新しい算法を作らない)。
//
// 【このファイルが絶対にやらないこと】
// - ファイルの読み書き・エンジンの起動(道具 `obsExtra.ts` の役目)。
// - 新しい判定的知識(閾値)を置くこと。`TIME_VALUES`・`spentBucketIndexOf`・`phaseOf` をそのまま使うだけ。
// - `patient_report_data.json`・`time_cause.json` の形を変えること(この道具の出力は別ファイル `obs_extra.json`)。

import {
  buildGames,
  buildPatientGames,
  countedPairsOf,
  displayPlyOf,
  isTimeUpLoss,
  moveSecondsOf,
  ownMoveTimesOf,
  phaseOf,
  spentBucketIndexOf,
  type GameSource,
  type PatientGame,
} from "./reportData.js";
import { medianOf } from "./timeCause.js";

export class ObsExtraError extends Error {}

/** `buildGames` の戻り値の要素の型(型自体は reportData.ts で export していないので、戻り値から取り出す)。 */
type BuiltGame = ReturnType<typeof buildGames>[number];

// ---- pairs(組と局・手の対応) ----

export interface ObsExtraPair {
  gameNo: number;
  branchPly: number;
  displayPly: number;
  phase: "early" | "mid" | "late";
  /** `buildBySpent` と同じ取り方(`seconds[displayPly - 1]`)。取れない組は `null`(落とさない)。 */
  spentSec: number | null;
  /** `spentBucketIndexOf(spentSec)`。`spentSec` が `null` なら `null`。 */
  spentBucket: 0 | 1 | 2 | 3 | null;
  collapsed: boolean;
}

function pairsOf(games: readonly BuiltGame[], patientGames: readonly PatientGame[]): ObsExtraPair[] {
  const out: ObsExtraPair[] = [];
  games.forEach((game, index) => {
    const patientGame = patientGames[index]!;
    // 1 局でも moveSeconds が無い(fixed.moveSeconds が undefined)固定棋譜は、この局の全ての組が spentSec: null になる
    // (moveSecondsOf は undefined を null で返す。落とさず、時間の欄だけ埋まらない扱い)。
    const seconds = moveSecondsOf(game.source.fixed) ?? [];
    for (const { pair, collapsed } of countedPairsOf(game)) {
      const displayPly = displayPlyOf(pair.branchPly, game.plyOffset);
      const phase = phaseOf(pair.branchPly, patientGame.total);
      const time = seconds[displayPly - 1];
      const spentSec = time === undefined || time === null ? null : time.spentSec;
      const spentBucket = spentSec === null ? null : (spentBucketIndexOf(spentSec) as 0 | 1 | 2 | 3);
      out.push({ gameNo: patientGame.no, branchPly: pair.branchPly, displayPly, phase, spentSec, spentBucket, collapsed });
    }
  });
  return out;
}

// ---- phaseMoves(局ごとの段別の手数と消費) ----

export interface ObsExtraPhaseCell {
  moves: number;
  sec: number;
}

export interface ObsExtraPhaseMoves {
  gameNo: number;
  timeUpLoss: boolean;
  early: ObsExtraPhaseCell;
  mid: ObsExtraPhaseCell;
  late: ObsExtraPhaseCell;
}

function emptyPhaseCell(): ObsExtraPhaseCell {
  return { moves: 0, sec: 0 };
}

/**
 * `phaseSpentOfGame`(lib/reportData.ts)と同じ数え方(本人が指した手・秒が取れたものだけ)で、
 * 段ごとの手数もあわせて数える。`ownMoveTimesOf` が返す手の集合は `phaseSpentOfGame` の走査と同じ
 * (parity が合い、秒が null でない手だけ)なので、`sec` の合計は `phaseSpentOfGame` と一致する。
 */
function phaseMovesOf(games: readonly BuiltGame[], patientGames: readonly PatientGame[]): ObsExtraPhaseMoves[] {
  return games.map((game, index) => {
    const patientGame = patientGames[index]!;
    const seconds = moveSecondsOf(game.source.fixed) ?? [];
    const cells = { early: emptyPhaseCell(), mid: emptyPhaseCell(), late: emptyPhaseCell() };
    for (const { kifPly, time } of ownMoveTimesOf(game, seconds)) {
      const recordPly = kifPly - game.plyOffset;
      const phase = phaseOf(recordPly, patientGame.total);
      cells[phase].moves += 1;
      cells[phase].sec += time.spentSec;
    }
    return {
      gameNo: patientGame.no,
      timeUpLoss: isTimeUpLoss(game.source.fixed.ending, patientGame.result),
      early: cells.early,
      mid: cells.mid,
      late: cells.late,
    };
  });
}

// ---- phaseSecPerMoveMedians(段ごとの手数あたり秒の中央値。計算あり) ----

export interface ObsExtraMedianGroup {
  /**
   * この組(timeUpLoss / other)に入る局の総数(`moves` が 0 の局を除いた「その段だけの分母」ではなく、
   * `lib/timeCause.ts` の `TimeCauseSubgroupSummary.games` と同じ「組全体の局数」。計画 §12.6 の
   * 「`moves` が 0 の局は `games` に数えない」は、`games` が組に 1 つで除外が段ごとに変わるため字義どおりには
   * 置けない。実装担当がこの形を選び、レーン長が採った(§12.6 の実測に記録)。中央値(`early/mid/late`)側は、
   * 段ごとに `moves` が 0 の局をその段の列から除いてから取る)。
   */
  games: number;
  early: number | null;
  mid: number | null;
  late: number | null;
}

export interface ObsExtraPhaseSecPerMoveMedians {
  timeUpLoss: ObsExtraMedianGroup;
  other: ObsExtraMedianGroup;
}

function medianGroupOf(rows: readonly ObsExtraPhaseMoves[]): ObsExtraMedianGroup {
  const rateOf = (cell: ObsExtraPhaseCell): number | null => (cell.moves === 0 ? null : cell.sec / cell.moves);
  const ratesOf = (pick: (row: ObsExtraPhaseMoves) => ObsExtraPhaseCell): readonly number[] =>
    rows.map((row) => rateOf(pick(row))).filter((rate): rate is number => rate !== null);
  return {
    games: rows.length,
    early: medianOf(ratesOf((row) => row.early)),
    mid: medianOf(ratesOf((row) => row.mid)),
    late: medianOf(ratesOf((row) => row.late)),
  };
}

function phaseSecPerMoveMediansOf(phaseMoves: readonly ObsExtraPhaseMoves[]): ObsExtraPhaseSecPerMoveMedians {
  return {
    timeUpLoss: medianGroupOf(phaseMoves.filter((row) => row.timeUpLoss)),
    other: medianGroupOf(phaseMoves.filter((row) => !row.timeUpLoss)),
  };
}

// ---- ファイル全体 ----

export interface ObsExtra {
  kind: "obs_extra";
  schemaVersion: "0.1";
  gitHead: string | null;
  dirty: boolean | null;
  pairs: ObsExtraPair[];
  phaseMoves: ObsExtraPhaseMoves[];
  phaseSecPerMoveMedians: ObsExtraPhaseSecPerMoveMedians;
}

export function buildObsExtra(sources: readonly GameSource[], gitHead: string | null, dirty: boolean | null): ObsExtra {
  const games = buildGames(sources);
  const patientGames = buildPatientGames(games);
  const phaseMoves = phaseMovesOf(games, patientGames);
  return {
    kind: "obs_extra",
    schemaVersion: "0.1",
    gitHead,
    dirty,
    pairs: pairsOf(games, patientGames),
    phaseMoves,
    phaseSecPerMoveMedians: phaseSecPerMoveMediansOf(phaseMoves),
  };
}
