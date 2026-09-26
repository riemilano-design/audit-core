// STEP OBS-5(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A))。幾何の写し `obs_geo.json` を組む純粋関数。
// 作りは STEP OBS-5'(§12.6、lib/obsExtra.ts)に揃える。
// STEP OBS-5d(§12.10 (A3))で `sideCrossTable`(側の一致の交差表)を追加した(下記)。
//
// 【このファイルがやること】
// - `buildObsGeo(sources, whatifPositionsByKifuId, gitHead, dirty)`: 段 2 の記録・固定棋譜から、
//   本人の手 1 つごとの幾何の事実・側・組み合わせの名前(`moves[]`)と、5〜9 秒(`spentBucket "≤9"`)・
//   10 秒以上(`spentBucket ">9"`。今までの `longThink === true` と同じ集合)の帯に絞った
//   決断の文脈(`decisionContext[]`)、`whatif-v2` の `kind:"position"` かつ `scenes.fork` が真の行を
//   第 1 候補の側 × 実戦の側で数えた交差表(`sideCrossTable[]`。STEP OBS-5d、§12.10 (A3))を組む
//   (統括経由の追加指示、2026-09-25/2026-09-26。**判定はしない ― 写す・数えるだけ**)。
//   **新しい盤の計算はしない**(`lib/moveFacts.ts` の
//   `moveFactsOf`・`lib/read.ts` の `moveMarksOf`・`lib/whatif.ts` の `tagsOf`/`sideOf`・
//   `lib/timeFeatures.ts` の `buildGameMoveFeatureRows` を呼ぶだけ)。`sideCrossTable` は
//   `whatifPositionsByKifuId`(既に `top1Side`/`actualSide`/`fork` を持つ `MoveFeatureWhatifPosition[]`)を
//   数えるだけで、新しい判定は一切しない。
// - 局面の再生は `apps/server/src/analysis/moveHistory.ts` の `DEFAULT_INITIAL_SFEN`・`replayMoveHistory`
//   をそのまま使う(`applyMove` は `replayMoveHistory` の内部が呼ぶ)。**`lib/sideAlignment.ts` の
//   「本人 = 先手にそろえる」変換は使わない** ― `moveFactsOf`・`moveMarksOf`・`tagsOf` はどれも
//   `position.turn`(局面の手番)から「own/opp」を決める向き非依存の関数なので、本人が後手の局でも
//   元の手順(`originalMovesOf` = 回す前の手順)を `DEFAULT_INITIAL_SFEN` からそのまま再生すれば、
//   本人の手番の局面で正しく own/opp が決まる(実装担当の判断。§12.10 (A) が名指しした 3 つの道具の
//   組み合わせから導いた)。
// - 名前の表(`GEO_FACT_LABELS`・`GEO_SIDE_LABELS`)は、この 1 か所だけに置く。**将棋の語彙(戦法・囲い・
//   狙いの名前)を 1 語も入れない**(幾何の語だけ)。`capture`・`drop`・`givesCheck` の語は
//   `report-pdf/render_direct.py` の `TAG_JP` と同じ(「取る」「打つ」「王手」)、`side` の
//   `attack`/`defense` の語は §12.10 (A) の例(「相手玉側」)と `docs/OBSERVATION_ITEMS.md` §2 の
//   `obs.geo.moveCombination` の例をそのまま使う(二重の訳語を増やさず、この STEP の計画・設計案が
//   名指しした語をそのまま採る ― 実装担当の判断)。
//
// 【このファイルが絶対にやらないこと】
// - ファイルの読み書き・エンジンの起動(道具 `obsGeo.ts` の役目)。
// - 「合駒」の判定(§12.10 (A) が明記した逸脱: `replyToCheck` は「玉を動かす/取る/それ以外/王手ではない」の
//   4 値で、「合駒」は入れない。合駒を数えるには利きの線を新しく計算する必要があり、この段の
//   「既存の道具を呼ぶだけ」という制約を越えるため)。
// - 新しい判定的知識(閾値)を置くこと。5〜9 秒・10 秒以上の帯は既存の `TIME_VALUES.spentBucketsSec [1,4,9]`
//   (`lib/reportData.ts`)の区切りを `buildGameMoveFeatureRows` 経由でそのまま使う(新しい閾値は置かない)。
// - `sideCrossTable`・`sideCrossByGame` で「一致」「不一致」という合計を作ること(統括の決定、2026-09-26)。`both` を
//   他のマスへ足し込まない。16 マスの件数をそのまま出すだけで、読む側が必要な足し算をする。
// - STEP OBS-5h(§12.14)で `sideCrossByGame`(16 マスを「何局に散っているか」でも写す)を足した。
//   `sideCrossTable` と同じ `whatifPositionsByKifuId` を数えるだけ(新しい盤の計算・新しい閾値は無し)。
//   `sideCrossTable` は残す(置き換えない ― 既存の読みと冊子が引いている)。

import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../../../apps/server/src/analysis/moveHistory.js";
import { POSITION_FACTS_RULES } from "./counterfactual.js";
import { moveFactsOf } from "./moveFacts.js";
import { moveMarksOf } from "./read.js";
import { buildGames, buildPatientGames, ownParityOf, type GameSource, type PatientGame } from "./reportData.js";
import { buildGameMoveFeatureRows, type MoveFeatureWhatifPosition } from "./timeFeatures.js";
import { sideOf as whatifSideOf, tagsOf, type WhatifSide } from "./whatif.js";

export class ObsGeoError extends Error {}

/** `buildGames` の戻り値の要素の型(reportData.ts は型を export していないので、戻り値から取り出す。obsExtra.ts と同じ手)。 */
type BuiltGame = ReturnType<typeof buildGames>[number];

// ---- moves(本人の手 1 つごとの幾何の事実・側・組み合わせの名前) ----

export interface ObsGeoMoveFacts {
  /** 相手の駒を取る手か(`moveFactsOf` の `capturedRole !== null`)。 */
  capture: boolean;
  /** 持ち駒を打つ手か。 */
  drop: boolean;
  /** 指した後、相手が王手を受けるか(`moveMarksOf` の `givesCheck`)。 */
  givesCheck: boolean;
  /** 玉を動かす手か。 */
  kingMove: boolean;
}

export type ObsGeoReplyToCapture = "取り返し" | "取らない" | "相手は取っていない";
export type ObsGeoReplyToCheck = "玉を動かす" | "取る" | "それ以外" | "王手ではない";

export interface ObsGeoMove {
  gameNo: number;
  /** KIF の手数(本人が指した向き = 回す前の手順の添字 + 1。`lib/timeCause.ts` の `ownMoveTimesOf` の `kifPly` と同じ数え方)。 */
  kifPly: number;
  side: WhatifSide;
  facts: ObsGeoMoveFacts;
  /** `facts` × `side` から作った幾何の組み合わせの名前(決-B)。 */
  combination: string;
  replyToCapture: ObsGeoReplyToCapture;
  replyToCheck: ObsGeoReplyToCheck;
}

// ---- decisionContext(5〜9 秒・10 秒以上の帯に絞った、既存 30 列のうち 8 本の写し + 帯・崩れの旗) ----

/** `MoveFeatureRow.spentBucket`(4 段)のうち、この段が対象にする 2 段(統括経由の追加指示、2026-09-25)。 */
export type ObsGeoDecisionBucket = "≤9" | ">9";

export interface ObsGeoDecisionContext {
  gameNo: number;
  kifPly: number;
  /** `MoveFeatureRow.spentBucket` をそのまま写す(`"≤9"` = 5〜9 秒、`">9"` = 10 秒以上。新しい閾値ではない)。 */
  spentBucket: ObsGeoDecisionBucket;
  /** `MoveFeatureRow.collapse` をそのまま写す(既存の崩れの旗)。 */
  collapse: boolean | null;
  fork: boolean | null;
  inCheck: boolean | null;
  oppPrevCapture: boolean | null;
  oppPrevDrop: boolean | null;
  oppPrevGivesCheck: boolean | null;
  oppPrevPromotion: boolean | null;
  phase: "early" | "mid" | "late";
  evalBand: "ahead" | "level" | "behind" | null;
}

// ---- sideCrossTable(STEP OBS-5d、§12.10 (A3))。fork が真の行を第 1 候補の側 × 実戦の側で数えた交差表 ----

/** 側の 4 値(`lib/whatif.ts` の `WhatifSide` と同じ集合)。表の行・列の並びを固定する順。 */
const SIDE_VALUES: readonly WhatifSide[] = ["attack", "defense", "both", "none"];

export interface ObsGeoSideCrossCell {
  /** 第 1 候補(`candidates[0]`)の側。 */
  top1Side: WhatifSide;
  /** 実戦の手の側。 */
  actualSide: WhatifSide;
  /** この組み合わせだった、`kind:"position"` かつ `scenes.fork` が真の行の件数。 */
  count: number;
}

/**
 * `whatifPositionsByKifuId` の全局・全行(`--whatif-v2-dir` を渡した分すべて。§12.10 (A3) は「組ごとに」
 * 求めると書いているが、この関数自身は組を知らない ― `obsGeo.ts` の 1 回の呼び出しが 1 組ぶんの
 * `--records`/`--kifu`/`--whatif-v2-dir` を受け取る既存の作り〈`obs_geo.json` は既に「1 組ぶんのファイル」、
 * `docs/OBSERVATION_ITEMS.md` の `obs.geo.*`・`obs.time.decisionContext` と同じ〉のまま「組ごとに」を満たす。
 * 実装担当の判断)のうち、`fork` が真の行だけを、第 1 候補の側 × 実戦の側で数える(決-A3)。
 * **新しい盤の計算はしない**(`MoveFeatureWhatifPosition.top1Side`/`actualSide`/`fork` を数えるだけ)。
 * 16 マス(4×4)を常に返す(件数 0 のマスも省かない ― 合計が fork の行数と一致することを機械で確かめやすくする)。
 * `both` は他のマスへ足し込まない(統括の決定、2026-09-26。「一致」「不一致」という合計はこの関数が作らない)。
 * `whatifPositionsByKifuId` が `null`(`--whatif-v2-dir` 無し)なら全マス 0。
 */
function sideCrossTableOf(whatifPositionsByKifuId: ReadonlyMap<string, readonly MoveFeatureWhatifPosition[]> | null): ObsGeoSideCrossCell[] {
  const counts = new Map<string, number>();
  for (const top1Side of SIDE_VALUES) {
    for (const actualSide of SIDE_VALUES) counts.set(`${top1Side}|${actualSide}`, 0);
  }
  if (whatifPositionsByKifuId !== null) {
    for (const positions of whatifPositionsByKifuId.values()) {
      for (const position of positions) {
        if (!position.fork) continue;
        const key = `${position.top1Side}|${position.actualSide}`;
        counts.set(key, (counts.get(key) ?? 0) + 1);
      }
    }
  }
  const out: ObsGeoSideCrossCell[] = [];
  for (const top1Side of SIDE_VALUES) {
    for (const actualSide of SIDE_VALUES) out.push({ top1Side, actualSide, count: counts.get(`${top1Side}|${actualSide}`)! });
  }
  return out;
}

// ---- sideCrossByGame(STEP OBS-5h、§12.14)。sideCrossTable の 16 マスを「何局に散っているか」でも数える ----

export interface ObsGeoSideCrossByGameCell {
  /** 第 1 候補(`candidates[0]`)の側。 */
  top1Side: WhatifSide;
  /** 実戦の手の側。 */
  actualSide: WhatifSide;
  /** この組み合わせだった、`kind:"position"` かつ `scenes.fork` が真の行の件数(= `sideCrossTable` の同じマスの `count`)。 */
  positions: number;
  /** この組み合わせが 1 局面以上あった局の数。 */
  gamesWithAtLeastOne: number;
  /** 1 局の中でのこの組み合わせの最大数。 */
  maxPositionsInOneGame: number;
}

export interface ObsGeoSideCrossByGame {
  /** 分母(= `whatifPositionsByKifuId` の Map のキーの数。`--whatif-v2-dir` が無ければ 0)。 */
  gamesTotal: number;
  cells: ObsGeoSideCrossByGameCell[];
}

/**
 * `sideCrossTableOf` と同じ入力(`whatifPositionsByKifuId`)を、`fork` が真の行について
 * 第 1 候補の側 × 実戦の側で数えるが、**局(Map のキー)ごとに数えてから 16 マスへ集計する**(決-A3 の延長、§12.14)。
 * **新しい盤の計算・新しい閾値はしない**(`sideCrossTableOf` と同じ値〈`top1Side`/`actualSide`/`fork`〉を
 * 局ごとに数えるだけ)。16 マス(4×4)を常に返す(件数 0 のマスも省かない)。
 * `both` は他のマスへ足し込まない(統括の決定、2026-09-26。`sideCrossTableOf` と同じ)。
 * `whatifPositionsByKifuId` が `null`(`--whatif-v2-dir` 無し)なら `gamesTotal` は 0、全マス 0。
 */
function sideCrossByGameOf(whatifPositionsByKifuId: ReadonlyMap<string, readonly MoveFeatureWhatifPosition[]> | null): ObsGeoSideCrossByGame {
  const gamesTotal = whatifPositionsByKifuId?.size ?? 0;
  // マスのキーごとに、局ごとの件数を積む(1 局に付き 1 エントリ。0 件の局も含む)。
  const perGameCountsByCell = new Map<string, number[]>();
  for (const top1Side of SIDE_VALUES) {
    for (const actualSide of SIDE_VALUES) perGameCountsByCell.set(`${top1Side}|${actualSide}`, []);
  }
  if (whatifPositionsByKifuId !== null) {
    for (const positions of whatifPositionsByKifuId.values()) {
      const countsInGame = new Map<string, number>();
      for (const top1Side of SIDE_VALUES) {
        for (const actualSide of SIDE_VALUES) countsInGame.set(`${top1Side}|${actualSide}`, 0);
      }
      for (const position of positions) {
        if (!position.fork) continue;
        const key = `${position.top1Side}|${position.actualSide}`;
        countsInGame.set(key, (countsInGame.get(key) ?? 0) + 1);
      }
      for (const [key, count] of countsInGame) perGameCountsByCell.get(key)!.push(count);
    }
  }
  const cells: ObsGeoSideCrossByGameCell[] = [];
  for (const top1Side of SIDE_VALUES) {
    for (const actualSide of SIDE_VALUES) {
      const perGameCounts = perGameCountsByCell.get(`${top1Side}|${actualSide}`)!;
      const positions = perGameCounts.reduce((sum, count) => sum + count, 0);
      const gamesWithAtLeastOne = perGameCounts.filter((count) => count > 0).length;
      const maxPositionsInOneGame = perGameCounts.reduce((max, count) => Math.max(max, count), 0);
      cells.push({ top1Side, actualSide, positions, gamesWithAtLeastOne, maxPositionsInOneGame });
    }
  }
  return { gamesTotal, cells };
}

export interface ObsGeo {
  kind: "obs_geo";
  schemaVersion: "0.1";
  gitHead: string | null;
  dirty: boolean | null;
  moves: ObsGeoMove[];
  decisionContext: ObsGeoDecisionContext[];
  sideCrossTable: ObsGeoSideCrossCell[];
  sideCrossByGame: ObsGeoSideCrossByGame;
}

// ---- 名前の表(幾何だけ。将棋の語彙を含まない。§12.10 (A) の 1.) ----

/**
 * `report-pdf/render_direct.py` の `TAG_JP`(取る・打つ・王手・捨て駒・引く)と同じ語のうち、この段が使う
 * 3 つ(取る・打つ・王手)をそのまま使い、`kingMove` だけ計画 §12.10 (A) 自身の語(「玉を動かす」。
 * `replyToCheck` の値そのもの)を当てた。
 */
const GEO_FACT_LABELS: ReadonlyArray<readonly [key: keyof ObsGeoMoveFacts, label: string]> = [
  ["capture", "取る"],
  ["drop", "打つ"],
  ["givesCheck", "王手"],
  ["kingMove", "玉を動かす"],
];

/**
 * `WhatifSide` の訳。attack/defense は §12.10 (A) の例(「取る・相手玉側」)と
 * `docs/OBSERVATION_ITEMS.md` §2 の `obs.geo.moveCombination` の例をそのまま使う
 * (`report-pdf` の `SIDE_JP`「攻め/守り」とは別の訳 ― この STEP の計画・設計案が名指しした語を優先した)。
 */
const GEO_SIDE_LABELS: Record<WhatifSide, string> = {
  attack: "相手玉側",
  defense: "自玉側",
  both: "両方",
  none: "どちらでもない",
};

/** `facts` が 1 つも真でないときの語(`render_direct.py` の `tags_text_of` の「特になし」と同じ語)。 */
const GEO_NO_FACTS_LABEL = "特になし";

/** この表(`GEO_FACT_LABELS`・`GEO_SIDE_LABELS`・`GEO_NO_FACTS_LABEL`)と `replyToCapture`/`replyToCheck` の
 * 値がすべて含む語(試験専用。将棋の語彙を含まないことを機械で確かめるのに使う)。 */
export const GEO_VOCABULARY_WORDS: readonly string[] = [
  ...GEO_FACT_LABELS.map(([, label]) => label),
  ...Object.values(GEO_SIDE_LABELS),
  GEO_NO_FACTS_LABEL,
  "取り返し",
  "取らない",
  "相手は取っていない",
  "それ以外",
  "王手ではない",
];

/** `facts` × `side` から幾何の組み合わせの名前を作る(決-B)。 */
export function combinationNameOf(facts: ObsGeoMoveFacts, side: WhatifSide): string {
  const factNames = GEO_FACT_LABELS.filter(([key]) => facts[key]).map(([, label]) => label);
  const parts = factNames.length > 0 ? factNames : [GEO_NO_FACTS_LABEL];
  return [...parts, GEO_SIDE_LABELS[side]].join("・");
}

export function replyToCaptureOf(ownFacts: ObsGeoMoveFacts, oppCaptured: boolean): ObsGeoReplyToCapture {
  if (!oppCaptured) return "相手は取っていない";
  return ownFacts.capture ? "取り返し" : "取らない";
}

/**
 * 王手への応じ方の名前。**当てる順は「玉を動かす」→「取る」で、入れ替えてはいけない**
 * (玉で王手駒を取る手は両方に当たる。基準の入力〈`<p4>` 3 分の組 18 局〉に実例が 10 件ある)。
 * この順を固定する試験が無かったため、独立監査の変異 2 が沈黙した(2026-09-25 の REVISE。
 * 試験は `obsGeo.test.ts` の「(b2) 王手への応じ方の当てる順」)。`export` はその試験のため。
 */
export function replyToCheckOf(ownFacts: ObsGeoMoveFacts, oppGivesCheck: boolean): ObsGeoReplyToCheck {
  if (!oppGivesCheck) return "王手ではない";
  if (ownFacts.kingMove) return "玉を動かす";
  if (ownFacts.capture) return "取る";
  return "それ以外";
}

function moveFactsGeoOf(sfen: string, moveUsi: string): ObsGeoMoveFacts {
  const facts = moveFactsOf(sfen, moveUsi, POSITION_FACTS_RULES);
  return {
    capture: facts.capturedRole !== null,
    drop: facts.drop,
    givesCheck: moveMarksOf(sfen, moveUsi).givesCheck,
    kingMove: facts.kingMove,
  };
}

/** 1 局ぶんの `moves[]`(本人の手だけ、KIF の手数の昇順)。 */
function movesOfGame(game: BuiltGame, gameNo: number): ObsGeoMove[] {
  const originalMoves = game.originalMoves;
  const parity = ownParityOf(game.side);
  const { sfens } = replayMoveHistory([...originalMoves], DEFAULT_INITIAL_SFEN);

  const out: ObsGeoMove[] = [];
  for (let kifPly = 1; kifPly <= originalMoves.length; kifPly++) {
    if (kifPly % 2 !== parity) continue; // 相手の手
    const sfenBefore = sfens[kifPly - 1]!;
    const moveUsi = originalMoves[kifPly - 1]!;
    const facts = moveFactsGeoOf(sfenBefore, moveUsi);
    const side = whatifSideOf(tagsOf(sfenBefore, moveUsi));
    const combination = combinationNameOf(facts, side);

    // 「初手(相手の直前の手が無い)は「相手は取っていない」「王手ではない」」(§12.10 (A))。
    // kifPly === 1 の本人の手は先手のときだけ起こる(後手の本人の初手は kifPly === 2 で、
    // その 1 手前〈kifPly === 1〉が相手の手として存在する)。
    let replyToCapture: ObsGeoReplyToCapture = "相手は取っていない";
    let replyToCheck: ObsGeoReplyToCheck = "王手ではない";
    if (kifPly >= 2) {
      const oppSfenBefore = sfens[kifPly - 2]!;
      const oppMoveUsi = originalMoves[kifPly - 2]!;
      const oppFacts = moveFactsGeoOf(oppSfenBefore, oppMoveUsi);
      replyToCapture = replyToCaptureOf(facts, oppFacts.capture);
      replyToCheck = replyToCheckOf(facts, oppFacts.givesCheck);
    }

    out.push({ gameNo, kifPly, side, facts, combination, replyToCapture, replyToCheck });
  }
  return out;
}

function movesOf(games: readonly BuiltGame[], patientGames: readonly PatientGame[]): ObsGeoMove[] {
  const out: ObsGeoMove[] = [];
  games.forEach((game, index) => out.push(...movesOfGame(game, patientGames[index]!.no)));
  return out;
}

function decisionContextOf(
  games: readonly BuiltGame[],
  patientGames: readonly PatientGame[],
  whatifPositionsByKifuId: ReadonlyMap<string, readonly MoveFeatureWhatifPosition[]> | null,
): ObsGeoDecisionContext[] {
  const out: ObsGeoDecisionContext[] = [];
  games.forEach((game, index) => {
    const patientGame = patientGames[index]!;
    const whatifPositions = whatifPositionsByKifuId?.get(game.source.kifuId) ?? null;
    // group・timeLimitSec はこの段の出力に出ない(fork・inCheck・oppPrev*・phase・evalBand の 8 本だけを写す)ので、
    // 意味のある値は要らない(実装担当の判断)。
    const rows = buildGameMoveFeatureRows(game.source.fixed, patientGame.no, "obsGeo", undefined, game.source.records, whatifPositions);
    for (const row of rows) {
      // 統括経由の追加指示(2026-09-25): 10 秒以上(旧 longThink)だけでなく 5〜9 秒の帯も対象にする。
      // 新しい閾値は置かない ― `TIME_VALUES.spentBucketsSec` の既存の区切りが決めた `spentBucket` を見るだけ。
      if (row.spentBucket !== "≤9" && row.spentBucket !== ">9") continue;
      out.push({
        gameNo: row.gameNo,
        kifPly: row.kifPly,
        spentBucket: row.spentBucket,
        collapse: row.collapse,
        fork: row.fork,
        inCheck: row.inCheck,
        oppPrevCapture: row.oppPrevCapture,
        oppPrevDrop: row.oppPrevDrop,
        oppPrevGivesCheck: row.oppPrevGivesCheck,
        oppPrevPromotion: row.oppPrevPromotion,
        phase: row.phase,
        evalBand: row.evalBand,
      });
    }
  });
  return out;
}

export function buildObsGeo(
  sources: readonly GameSource[],
  whatifPositionsByKifuId: ReadonlyMap<string, readonly MoveFeatureWhatifPosition[]> | null,
  gitHead: string | null,
  dirty: boolean | null,
): ObsGeo {
  const games = buildGames(sources);
  const patientGames = buildPatientGames(games);
  return {
    kind: "obs_geo",
    schemaVersion: "0.1",
    gitHead,
    dirty,
    moves: movesOf(games, patientGames),
    decisionContext: decisionContextOf(games, patientGames, whatifPositionsByKifuId),
    sideCrossTable: sideCrossTableOf(whatifPositionsByKifuId),
    sideCrossByGame: sideCrossByGameOf(whatifPositionsByKifuId),
  };
}
