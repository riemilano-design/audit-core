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
// - **露出の欄(STEP EXPO-1、§12.9)は「延べ」**。局面 × レコードの行(`none` は含めない)
//   1 つずつに `decideNameExposure` を当て、hidden / hedged / named の数を数える。
//   **判定も閾値もここには書かない** ― 関数と値の組(`NAME_EXPOSURE_VALUES`)を
//   apps/server から import するだけで、この道具は「どの行に当てるか」と「何を数えるか」しか持たない。
// - **STEP EXPO-1b で値の組が 6 つ(A・B・C・D・D'・D'')になった。** D 系が使う
//   `movedRequiredCount`(必要な駒のうち「平手の初期位置と違うマスにある駒」の数)は、
//   **定義を読む側 = この道具**が作って渡す(規則は apps/server、定義の読み取りはここ、という線)。
//   初期位置の表は書かず、平手の初期局面(`DEFAULT_INITIAL_SFEN`)を 1 回読んで引く
//   (新しい将棋知識を書かない)。

import type { Color } from "shogiops/types";
import { makeSquareName, parseSquareName } from "shogiops/util";

import { analyzeShapeFormationFromEvents } from "../../../apps/server/src/analysis/shapeFormationAnalyzer.js";
import { detectIntentsFromEvents } from "../../../apps/server/src/analysis/intentDetector.js";
import {
  analyzeOpeningFormationFromEvents,
  type OpeningDefinition,
} from "../../../apps/server/src/analysis/openingDetector.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../../../apps/server/src/analysis/moveHistory.js";
import { japaneseToRole } from "../../../apps/server/src/analysis/pieceMapping.js";
import type { IntentDefinition } from "../../../apps/server/src/analysis/intentRepository.js";
import {
  decideNameExposure,
  NAME_EXPOSURE_VALUES,
  type NameExposureInput,
  type NameExposureValues,
} from "../../../apps/server/src/analysis/nameExposure.js";
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

// ---------------------------------------------------------------------------
// 露出の欄(STEP EXPO-1、docs/LANE_DIAG_LOG_2026-09.md §12.9)
// ---------------------------------------------------------------------------

/**
 * 値の組の名前。A = 今日の規則、B = 案、C = 案(forming の証拠の下限だけ 2)、
 * D / D' / D'' = 中間案(STEP EXPO-1b)。
 */
export type ExposureValueSetName = "A" | "B" | "C" | "D" | "D'" | "D''";

/**
 * 比べる 6 つの値の組。**この道具が閾値を決めるのではない** ―
 * B は `apps/server` の `NAME_EXPOSURE_VALUES`(統括の承認待ちの案)**そのもの**、
 * C はその `minEvidenceForHedged` だけを 2 にしたもの、
 * A は「今日の規則」を `decideNameExposure` の値で表したもの
 * (`minRequiredForName: 0` で R3 が当たらず、`minEvidenceForHedged: Infinity` で R5 が hedged にならず、
 * `hideCompletedWithoutEvidence: false` で R2 が当たらない = completed/matched だけが出る今の見え方)。
 * **A・B・C は STEP EXPO-1b で足した 2 欄を既定値で持つ**(= EXPO-1 と同じ決定。試験で固定)。
 *
 * D 系は中間案(§12.9 の追記)で、C を基本に R5'(証拠 1 件でも欠け ≤ 1 なら hedged)を足し、
 * completed / matched に要求する証拠の下限だけを変えたもの:
 * - **D** … `"all"`(必要な駒の数)。**統括の判断で採用候補から外れた**(必要な駒に初期位置の駒を
 *   含む形は永久に named にならないため)。**比較のためだけに測る。**
 * - **D'** … `2`
 * - **D''** … `"movedRequired"`(必要な駒のうち初期位置と違うマスにある駒の数。0 件なら名前を出さない)
 * 値の選択は統括が行う(この欄は前後を並べて渡すためのもの)。
 */
export const EXPOSURE_VALUE_SETS: Record<ExposureValueSetName, NameExposureValues> = {
  A: {
    minRequiredForName: 0,
    minEvidenceForHedged: Number.POSITIVE_INFINITY,
    hideCompletedWithoutEvidence: false,
    hedgeOneEvidenceIfMissingLe1: false,
    minEvidenceForCompleted: 0,
  },
  B: { ...NAME_EXPOSURE_VALUES },
  C: { ...NAME_EXPOSURE_VALUES, minEvidenceForHedged: 2 },
  D: {
    ...NAME_EXPOSURE_VALUES,
    minEvidenceForHedged: 2,
    hedgeOneEvidenceIfMissingLe1: true,
    minEvidenceForCompleted: "all",
  },
  "D'": {
    ...NAME_EXPOSURE_VALUES,
    minEvidenceForHedged: 2,
    hedgeOneEvidenceIfMissingLe1: true,
    minEvidenceForCompleted: 2,
  },
  "D''": {
    ...NAME_EXPOSURE_VALUES,
    minEvidenceForHedged: 2,
    hedgeOneEvidenceIfMissingLe1: true,
    minEvidenceForCompleted: "movedRequired",
  },
};

/** 露出の数(延べ。局面 × レコードの行を数える)。 */
export interface ExposureCounts {
  /** 名前を言える行 */
  named: number;
  /** 控えめに言う行 */
  hedged: number;
  /** 出さない行(下の hiddenCompletedNoEvidence もここに含む) */
  hidden: number;
  /** そのうち「証拠 0 件の completed / matched」を規則 R2 で落とした行(P-85・P-86 の物差し) */
  hiddenCompletedNoEvidence: number;
  /** 証拠が 1 件以下だった行(値の組によらない。分母) */
  weakClaims: number;
  /** そのうち named か hedged になった行(分子) */
  weakClaimsShown: number;
  /** 規則 R5'(証拠 1 件・欠け ≤ 1)で hedged になった行(STEP EXPO-1b) */
  pickedByR5p: number;
  /** 規則 R6(completed / matched の証拠が下限に足りない)で hidden にした行。**上の hidden にも入る** */
  droppedByR6: number;
  /** R6 で落ちた行を、レコードの id ごとに数えたもの */
  droppedByR6ById: Record<string, number>;
}

/** 自分側・相手側。形と戦型は定義の side、狙いは常に相手側。 */
export interface ExposureBySide {
  self: ExposureCounts;
  opponent: ExposureCounts;
}

export interface ExposureByKind {
  shape: ExposureBySide;
  intent: ExposureBySide;
  opening: ExposureBySide;
}

/** 値の組 3 つ分の露出の数。 */
export type ExposureTotals = Record<ExposureValueSetName, ExposureByKind>;

const EXPOSURE_SET_NAMES: ExposureValueSetName[] = ["A", "B", "C", "D", "D'", "D''"];
const EXPOSURE_KINDS: Array<NameExposureInput["kind"]> = ["shape", "intent", "opening"];

/** 「証拠が少ない主張」の境目。I-9 の定数(invariants 側)をそのまま使い、ここで数を書かない。 */
const WEAK_CLAIM_MAX_EVIDENCE = I9_MAX_EVIDENCE;

function emptyExposureCounts(): ExposureCounts {
  return {
    named: 0,
    hedged: 0,
    hidden: 0,
    hiddenCompletedNoEvidence: 0,
    weakClaims: 0,
    weakClaimsShown: 0,
    pickedByR5p: 0,
    droppedByR6: 0,
    droppedByR6ById: {},
  };
}

function emptyExposureTotals(): ExposureTotals {
  const byKind = (): ExposureByKind => ({
    shape: { self: emptyExposureCounts(), opponent: emptyExposureCounts() },
    intent: { self: emptyExposureCounts(), opponent: emptyExposureCounts() },
    opening: { self: emptyExposureCounts(), opponent: emptyExposureCounts() },
  });
  return { A: byKind(), B: byKind(), C: byKind(), D: byKind(), "D'": byKind(), "D''": byKind() };
}

function addExposureCounts(into: ExposureCounts, from: ExposureCounts): void {
  into.named += from.named;
  into.hedged += from.hedged;
  into.hidden += from.hidden;
  into.hiddenCompletedNoEvidence += from.hiddenCompletedNoEvidence;
  into.weakClaims += from.weakClaims;
  into.weakClaimsShown += from.weakClaimsShown;
  into.pickedByR5p += from.pickedByR5p;
  into.droppedByR6 += from.droppedByR6;
  for (const [id, count] of Object.entries(from.droppedByR6ById)) {
    into.droppedByR6ById[id] = (into.droppedByR6ById[id] ?? 0) + count;
  }
}

function addExposureTotals(into: ExposureTotals, from: ExposureTotals): void {
  for (const set of EXPOSURE_SET_NAMES) {
    for (const kind of EXPOSURE_KINDS) {
      addExposureCounts(into[set][kind].self, from[set][kind].self);
      addExposureCounts(into[set][kind].opponent, from[set][kind].opponent);
    }
  }
}

/**
 * 立っている行(`none` でない 1 レコード × 1 局面)を 6 つの値の組に当てて数える。
 * 判定は `decideNameExposure` がすべて行う。ここは入力を組み立てて数えるだけ。
 * `id` は `droppedByR6ById`(どのレコードが R6 で落ちたか)のためだけに使う。
 */
function countExposure(
  totals: ExposureTotals,
  kind: NameExposureInput["kind"],
  side: "self" | "opponent",
  id: string,
  input: Omit<NameExposureInput, "kind">,
): void {
  const weak = input.evidenceCount <= WEAK_CLAIM_MAX_EVIDENCE;
  for (const set of EXPOSURE_SET_NAMES) {
    const decision = decideNameExposure({ kind, ...input }, EXPOSURE_VALUE_SETS[set]);
    const counts = totals[set][kind][side];
    counts[decision.level] += 1;
    if (decision.rule === "R2") counts.hiddenCompletedNoEvidence += 1;
    if (decision.rule === "R5p") counts.pickedByR5p += 1;
    if (decision.rule === "R6") {
      counts.droppedByR6 += 1;
      bump(counts.droppedByR6ById, id);
    }
    if (weak) {
      counts.weakClaims += 1;
      if (decision.level !== "hidden") counts.weakClaimsShown += 1;
    }
  }
}

/** 平手の初期局面(`DEFAULT_INITIAL_SFEN`)。初期位置の表を書かず、ここから引く。 */
const INITIAL_POSITION = parsePosition(DEFAULT_INITIAL_SFEN);

/**
 * 必要な駒(非 optional)のうち、**平手の初期局面でその色・その駒種が置かれていないマス**の一覧
 * (STEP EXPO-1b の R6 `"movedRequired"` が使う `movedRequiredCount` の元。STEP OBS-5e で
 * 「どの駒が動くべき駒か」を到達率の数え直しにも使うため、件数だけでなく一覧を返す版を切り出した)。
 *
 * 将棋の判断はしない ― 「そのマスに、その色のその駒種が初期局面から在るか」の照合だけである。
 * 初期位置のまま一致する駒は、動いた証拠(`formationEvidence`)を持ちようがないので、
 * 「証拠を求めてよい駒」から外すために数える。
 */
export function movedRequiredPiecesOf(
  pieces: ReadonlyArray<{ piece: string; square: string }>,
  perspectiveColor: Color,
): Array<{ piece: string; square: string }> {
  const moved: Array<{ piece: string; square: string }> = [];
  for (const required of pieces) {
    const square = parseSquareName(required.square);
    if (square === undefined) {
      throw new RecognitionMeasureError(`マス目の表記が不正です: "${required.square}"`);
    }
    const initial = INITIAL_POSITION.board.get(square);
    const sameAsInitial =
      initial !== undefined && initial.color === perspectiveColor && initial.role === japaneseToRole(required.piece);
    if (!sameAsInitial) moved.push(required);
  }
  return moved;
}

/** `movedRequiredPiecesOf` の件数だけを返す版(STEP EXPO-1b までの呼び出し口をそのまま残す)。 */
export function movedRequiredCountOf(
  pieces: ReadonlyArray<{ piece: string; square: string }>,
  perspectiveColor: Color,
): number {
  return movedRequiredPiecesOf(pieces, perspectiveColor).length;
}

// ---------------------------------------------------------------------------
// 状態の件数(STEP OBS-5c。docs/LANE_DIAG_LOG_2026-09.md §12.10 (A2)「計画の直し」2026-09-26)。
//
// 露出の欄(countExposure)は `status !== "none"` に絞った行にしか当たらず、`none` は集計の前に
// 捨てられている。写し(obsSnapshot)は「道具が既に出した数をそのまま写すだけ」という不変条件を
// 持つため、`completed` の件数(`named + hedged` の足し算)も `none` の件数(どこにも無い)も
// 写し側では作れない。ここに「既に計算済みの `status`(または `matchStatus`)と `side` を数えるだけ」
// の欄を 1 つ足し、`none` を含む 4 状態の件数を持たせる。**新しい盤の計算でも新しい閾値でもない**
// ― `status`/`matchStatus`/`side` はどれも analyzeShapeFormationFromEvents・detectIntentsFromEvents・
// analyzeOpeningFormationFromEvents が既に計算済みの値で、ここでは数えるだけ。
// ---------------------------------------------------------------------------

/** 認識の状態。形・戦型は none/forming/completed、狙いは none/forming/matched(completed は使わない)。 */
export type RecognitionState = "none" | "forming" | "completed" | "matched";

const RECOGNITION_STATES: readonly RecognitionState[] = ["none", "forming", "completed", "matched"];

/** 状態ごとの件数(側 1 つぶん)。 */
export type StatusCountsByState = Record<RecognitionState, number>;

/** 自分側・相手側の状態の件数。狙いは常に相手側にしか数えない(self は 0 のまま)。 */
export interface StatusCountsBySide {
  self: StatusCountsByState;
  opponent: StatusCountsByState;
}

/** 種類(形・狙い・戦型)ごとの状態の件数。 */
export interface StatusCountsByKind {
  shape: StatusCountsBySide;
  intent: StatusCountsBySide;
  opening: StatusCountsBySide;
}

function emptyStatusCountsByState(): StatusCountsByState {
  return { none: 0, forming: 0, completed: 0, matched: 0 };
}

function emptyStatusCountsBySide(): StatusCountsBySide {
  return { self: emptyStatusCountsByState(), opponent: emptyStatusCountsByState() };
}

function emptyStatusCountsByKind(): StatusCountsByKind {
  return { shape: emptyStatusCountsBySide(), intent: emptyStatusCountsBySide(), opening: emptyStatusCountsBySide() };
}

function addStatusCountsByState(into: StatusCountsByState, from: StatusCountsByState): void {
  for (const state of RECOGNITION_STATES) into[state] += from[state];
}

function addStatusCountsByKind(into: StatusCountsByKind, from: StatusCountsByKind): void {
  addStatusCountsByState(into.shape.self, from.shape.self);
  addStatusCountsByState(into.shape.opponent, from.shape.opponent);
  addStatusCountsByState(into.intent.self, from.intent.self);
  addStatusCountsByState(into.intent.opponent, from.intent.opponent);
  addStatusCountsByState(into.opening.self, from.opening.self);
  addStatusCountsByState(into.opening.opponent, from.opening.opponent);
}

/**
 * `status`(または `matchStatus`)と `side` から `statusCounts` の 1 件を数える(bump)。
 * `side` は既存の露出の数え方(`countExposure` の呼び出し)と同じ規則で self/opponent に丸める
 * (`side === "opponent"` だけを opponent、それ以外〈"self"・"both"〉は self)。判定は一切しない。
 */
function bumpStatusCount(counts: StatusCountsBySide, side: "self" | "opponent", state: RecognitionState): void {
  counts[side][state] += 1;
}

// ---------------------------------------------------------------------------
// 「あと 1 枚」の中身(STEP OBS-5e。docs/LANE_DIAG_LOG_2026-09.md §12.10 (A4))。
//
// レーン長が測った事実: 18 局で最も完成に近づいた自分側の形の多くが `mutekigakoi`
// (12 局で到達率 0.80)だったが、必要な駒 5 枚のうち 3 枚(玉・金・金)は先手の初期配置その
// ものだった。「あと 1 枚」の大部分は「玉と金を動かしていない」の言い換えで、居玉 91% と
// 同じ事実を別の側から見た数になっている。ここに足すのは次の 2 つ(**新しい盤の計算・新しい
// 閾値は置かない**。既存の `missingSquares`・`matchedSquares`・`movedRequiredPiecesOf` の
// 突き合わせだけ):
// 1. 欠けたマスと駒の内訳(形 id ごとの件数、局ごとに最も近づいた自分側の形とその欠け)。
// 2. 到達率を「初期位置でない必要駒」だけで数え直した版(D'' の考え方を到達率にも当てる)。
// ---------------------------------------------------------------------------

/** 欠けていた 1 マス・1 駒(`missingSquares` の 1 件を定義の `required_pieces` へ突き合わせたもの)。 */
export interface MissingPiece {
  square: string;
  piece: string;
}

/** 局の中で最も近づいた自分側の形(matchScore が最大のもの)と、そのとき欠けていた駒。 */
export interface ClosestSelfShape {
  shapeId: string;
  matchScore: number;
  missing: MissingPiece[];
}

/** 形の定義の `required_pieces`(非 optional)から、`missingSquares` に対応する駒名を引く。 */
function missingPiecesOf(shapeDef: ShapeDefinition, missingSquares: readonly string[]): MissingPiece[] {
  return missingSquares.map((square) => {
    const required = shapeDef.required_pieces.find((p) => p.square === square && !p.optional);
    if (required === undefined) {
      throw new RecognitionMeasureError(`missingSquares のマスが required_pieces に無い(id="${shapeDef.id}" square="${square}")`);
    }
    return { square, piece: required.piece };
  });
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

  // --- 露出(STEP EXPO-1)。値の組 A / B / C × 形・狙い・戦型 × 自分側・相手側 ---
  // byGroup の同じ欄は、この局ごとの数をそのまま足し上げたもの(局数ではなく延べ)。
  exposure: ExposureTotals;

  // --- 状態の件数(STEP OBS-5c)。種類 × 自分側/相手側 × none/forming/completed/matched の件数 ---
  // 露出と違い `none` も数える(捨てない)。byGroup の同じ欄は、この局ごとの数をそのまま足し上げたもの。
  statusCounts: StatusCountsByKind;

  // --- 「あと 1 枚」の中身(STEP OBS-5e) ---
  /**
   * 形の id・欠けたマス・駒(`"${shapeId}:${square}:${piece}"`)ごとの件数。
   * **forming だった局面だけ**を数える(completed は `missingSquares` が必ず 0 件なので数えても増えない)。
   */
  shapeMissingCounts: Record<string, number>;
  /** shapeMissingCounts の値をそのまま足した合計(この局分。forming の行の欠けの総数と一致するはず)。 */
  shapeMissingTotal: number;
  /** 局の中で最も近づいた自分側の形(side !== "opponent" のうち matchScore が最大)と、そのとき欠けていた駒。無ければ null。 */
  closestSelfShape: ClosestSelfShape | null;
  /**
   * 形 id ごとの「初期位置でない必要駒」だけで数え直した到達率(`movedRequiredPiecesOf` の一致数 /
   * `movedRequiredPiecesOf` の総数)の、この局での最大値。**分母が 0(movedRequiredZeroShapeIds に
   * 含まれる形)は入らない**(数え直せない = 到達率を持たない)。自分側・相手側の両方を持つ
   * (id が既に側を確定しているので、この欄では側で分けない)。
   */
  shapeMovedRequiredBest: Record<string, number>;
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

  /** 露出(STEP EXPO-1)。rows の同じ欄を足し上げた延べの数(局数ではない) */
  exposure: ExposureTotals;

  /** 状態の件数(STEP OBS-5c)。rows の同じ欄を足し上げた延べの数(none を含む。局数ではない) */
  statusCounts: StatusCountsByKind;

  // --- 「あと 1 枚」の中身(STEP OBS-5e)。rows の同じ欄を足し上げたもの ---
  /** 形の id・欠けたマス・駒ごとの件数(延べ。forming だった局面だけ)。rows の shapeMissingCounts の合計 */
  shapeMissingCounts: Record<string, number>;
  /** shapeMissingCounts の値の合計(延べ) */
  shapeMissingTotal: number;
  /**
   * 自分側の closestSelfShape の欠けがちょうど 1 枚だった局の数。**駒の種類を問わない**(銀でも玉でも金でも数える)。
   * **「あと 1 枚で完成」と読まないこと**(既知事項 P-90): 欠けが 1 枚でも、その 1 枚が初期配置のマスの駒なら
   * 「まだ来ていない」ではなく「離れた」であり、完成に近いことを意味しない。
   * **銀だけを数えた局数はこの値ではない**(既知事項 P-97。`<p4>` の 3 分 18 局では、この値が 13 で
   * そのうち駒が銀だったのは 10。**13 と 10 を混ぜない**)。
   */
  selfClosestOneAwayGames: number;
  /** 形 id ごとの「数え直した到達率(shapeMovedRequiredBest)が 1 局面でも 1.0 に達した局数」 */
  gamesMovedRequiredComplete: Record<string, number>;
  /** gamesMovedRequiredComplete の値の合計(延べ。id をまたいで数える) */
  shapeMovedRequiredCompleteTotal: number;
}

export interface RecognitionMeasureResult {
  byGroup: Record<string, GroupTotals>;
  rows: GameRow[];
  /**
   * 「初期位置でない必要駒」が 0 の形の id(STEP OBS-5e)。**到達率を数え直せない形**
   * (必要な駒が全部、平手の初期配置と一致している = 動いた証拠を持ちようがない)。
   * 局・組に依らない、形の定義から決まる値(自分側・相手側)。
   */
  movedRequiredZeroShapeIds: { self: string[]; opponent: string[] };
  /** movedRequiredZeroShapeIds の件数だけを持つ版(obsSnapshot が写す用。id の一覧は白いリストの門に掛かるため件数だけ渡す)。 */
  movedRequiredZeroShapeCounts: { self: number; opponent: number };
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
    exposure: emptyExposureTotals(),
    statusCounts: emptyStatusCountsByKind(),
    shapeMissingCounts: {},
    shapeMissingTotal: 0,
    closestSelfShape: null,
    shapeMovedRequiredBest: {},
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
    exposure: emptyExposureTotals(),
    statusCounts: emptyStatusCountsByKind(),
    shapeMissingCounts: {},
    shapeMissingTotal: 0,
    selfClosestOneAwayGames: 0,
    gamesMovedRequiredComplete: {},
    shapeMovedRequiredCompleteTotal: 0,
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

  // R6 の "movedRequired" に渡す数(と、STEP OBS-5e が使う一覧)。定義 × 視点で決まるので
  // 1 回だけ数えて使い回す(局面ごとに数え直しても同じ値になる ― 定義も初期局面も動かないため)。
  const shapeById = new Map(shapes.map((shape) => [shape.id, shape]));
  const openingById = new Map(openings.map((opening) => [opening.id, opening]));
  const movedRequiredPiecesCache = new Map<string, MissingPiece[]>();
  const movedRequiredPiecesOfId = (kind: "shape" | "opening", id: string, color: Color): MissingPiece[] => {
    const key = `${kind}:${id}:${color}`;
    const cached = movedRequiredPiecesCache.get(key);
    if (cached !== undefined) return cached;
    let pieces: Array<{ piece: string; square: string }>;
    if (kind === "shape") {
      const shape = shapeById.get(id);
      if (shape === undefined) throw new RecognitionMeasureError(`形の定義が見つかりません(id="${id}")`);
      pieces = shape.required_pieces.filter((p) => !p.optional).map((p) => ({ piece: p.piece, square: p.square }));
    } else {
      const opening = openingById.get(id);
      if (opening === undefined) throw new RecognitionMeasureError(`戦型の定義が見つかりません(id="${id}")`);
      // openingDetector.ts が recognition_pattern を「非 optional の required_pieces」へ写すのと同じ対応。
      pieces = (opening.recognition_pattern ?? []).map((entry) => ({ piece: entry.piece, square: entry.to }));
    }
    const moved = movedRequiredPiecesOf(pieces, color);
    movedRequiredPiecesCache.set(key, moved);
    return moved;
  };
  const movedRequiredOf = (kind: "shape" | "opening", id: string, color: Color): number =>
    movedRequiredPiecesOfId(kind, id, color).length;

  // STEP OBS-5e: 「初期位置でない必要駒」が 0 の形の id(自分側・相手側)。局・組に依らない
  // (形の定義から決まる)ので、games のループの外で 1 つの集合として持つ。
  const movedRequiredZeroSelfIds = new Set<string>();
  const movedRequiredZeroOpponentIds = new Set<string>();

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
      // 状態の件数(STEP OBS-5c)。`none` を含む全件(shapeOn で絞る前)を数える。
      for (const r of shapeResults) {
        bumpStatusCount(row.statusCounts.shape, r.side === "opponent" ? "opponent" : "self", r.status);
      }
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

        const shapeDef = shapeById.get(r.shapeId);
        if (shapeDef !== undefined) {
          // STEP OBS-5e (1a): 欠けたマスと駒の内訳(forming だった局面だけ。completed は欠け 0 件なので
          // 数えても増えない)。
          if (r.status === "forming") {
            for (const missing of missingPiecesOf(shapeDef, r.missingSquares)) {
              bump(row.shapeMissingCounts, `${r.shapeId}:${missing.square}:${missing.piece}`);
              row.shapeMissingTotal += 1;
            }
          }

          // STEP OBS-5e (1b): 局の中で最も近づいた自分側の形(matchScore が最大。shapeBest と同じ
          // 基準〈status を問わない〉。同点は先に見つかったほうを残す)。
          if (r.side !== "opponent" && (row.closestSelfShape === null || r.matchScore > row.closestSelfShape.matchScore)) {
            row.closestSelfShape = {
              shapeId: r.shapeId,
              matchScore: r.matchScore,
              missing: missingPiecesOf(shapeDef, r.missingSquares),
            };
          }

          // STEP OBS-5e (2): 到達率を「初期位置でない必要駒」だけで数え直す(shapeBest と同じく
          // status を問わず、この局で一番高かった値を持つ)。分母が 0(movedRequired が無い形)は
          // 「数え直せない」ので shapeMovedRequiredBest に入れず、id だけ別の集合へ記録する。
          const movedPieces = movedRequiredPiecesOfId("shape", r.shapeId, r.perspectiveColor);
          if (movedPieces.length === 0) {
            (r.side === "opponent" ? movedRequiredZeroOpponentIds : movedRequiredZeroSelfIds).add(r.shapeId);
          } else {
            const movedMatched = movedPieces.filter((p) => r.matchedSquares.includes(p.square)).length;
            const recounted = movedMatched / movedPieces.length;
            if (recounted > (row.shapeMovedRequiredBest[r.shapeId] ?? -1)) {
              row.shapeMovedRequiredBest[r.shapeId] = recounted;
            }
          }
        }
      }
      for (const r of shapeOn) {
        bump(row.shapeHits, r.shapeId);
        shapeOnSet.add(r.shapeId);
        if (r.formationEvidence.length <= I9_MAX_EVIDENCE && r.missingSquares.length >= I9_MIN_MISSING) {
          row.i9type += 1;
          if (r.side === "opponent") row.i9Opp += 1;
        }
        // 露出(STEP EXPO-1)。必要な数 = optional でない required_pieces の数
        // (一致したマス + 欠けたマス。shapeDetector.ts が両方 required_pieces の非 optional から作る)。
        countExposure(row.exposure, "shape", r.side === "opponent" ? "opponent" : "self", r.shapeId, {
          status: r.status,
          evidenceCount: r.formationEvidence.length,
          missingCount: r.missingSquares.length,
          requiredCount: r.matchedSquares.length + r.missingSquares.length,
          // 視点は判定が採った側(side="both" の形は一致度の高い側が入る)をそのまま使う。
          movedRequiredCount: movedRequiredOf("shape", r.shapeId, r.perspectiveColor),
          reviewStatus: r.reviewStatus,
        });
      }

      // --- 狙い ---
      const intentResults = detectIntentsFromEvents(prefix, { intents });
      const intentOn = intentResults.filter(
        (r) => r.matchStatus === "forming" || r.matchStatus === "matched",
      );
      // 状態の件数(STEP OBS-5c)。狙いは常に相手側だけに数える(self は 0 のまま)。
      for (const r of intentResults) {
        bumpStatusCount(row.statusCounts.intent, "opponent", r.matchStatus);
      }
      if (intentOn.some((r) => r.matchStatus === "matched" || r.matchedSignatures.length >= 2)) {
        row.recIntent2 += 1;
      }
      for (const r of intentOn) {
        bump(row.intentHits, r.intentId);
        intentOnSet.add(r.intentId);
        if (r.matchStatus === "matched") intentCompSet.add(r.intentId);
        // 露出(STEP EXPO-1)。狙いの side は常に相手側(data/intents に side の欄が無く、
        // intentDetector.ts が後手の指し手だけを見る。docs/DATA_MODEL.md の MVP 確定仕様)。
        // 必要な数 = recognition_pattern の長さ(= 一致した署名 + 未一致の署名)。
        // 狙いの署名は「指し手」そのもの(駒 × 移動先)なので、初期配置のまま一致することがない
        // = 動くべき数は必要な数と同じ(R6 の "movedRequired" は形・戦型と同じ意味になる)。
        countExposure(row.exposure, "intent", "opponent", r.intentId, {
          status: r.matchStatus,
          evidenceCount: r.matchedSignatures.length,
          missingCount: r.unmatchedSignatures.length,
          requiredCount: r.matchedSignatures.length + r.unmatchedSignatures.length,
          movedRequiredCount: r.matchedSignatures.length + r.unmatchedSignatures.length,
          reviewStatus: r.reviewStatus,
        });
      }
      if (intentOn.length > 0) row.recIntent += 1;

      if (shapeOn.length > 0 || intentOn.length > 0) row.recAny += 1;
      else row.silent += 1;

      // --- 戦型 ---
      const openingResults = analyzeOpeningFormationFromEvents(sfen, prefix, openings);
      const openingOn = openingResults.filter(
        (r) => r.status === "forming" || r.status === "completed",
      );
      // 状態の件数(STEP OBS-5c)。`none` を含む全件(openingOn で絞る前)を数える。
      for (const r of openingResults) {
        bumpStatusCount(row.statusCounts.opening, r.side === "opponent" ? "opponent" : "self", r.status);
      }
      const openingStrong = (r: (typeof openingResults)[number]): boolean =>
        r.status === "completed" || r.formationEvidence.length >= 2;

      if (!openingOn.some((r) => r.side !== "opponent" && openingStrong(r))) row.openSilentSelf += 1;
      if (!openingOn.some((r) => r.side === "opponent" && openingStrong(r))) row.openSilentOpp += 1;
      if (!openingOn.some(openingStrong)) row.openSilentAny += 1;

      for (const r of openingOn) {
        openOnSet.add(r.openingId);
        // 露出(STEP EXPO-1)。必要な数 = recognition_pattern の長さ
        // (openingDetector.ts が recognition_pattern を optional でない required_pieces へ写す)。
        countExposure(row.exposure, "opening", r.side === "opponent" ? "opponent" : "self", r.openingId, {
          status: r.status,
          evidenceCount: r.formationEvidence.length,
          missingCount: r.missingSquares.length,
          requiredCount: r.matchedSquares.length + r.missingSquares.length,
          movedRequiredCount: movedRequiredOf("opening", r.openingId, r.perspectiveColor),
          reviewStatus: r.reviewStatus,
        });
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
    addExposureTotals(totals.exposure, row.exposure);
    addStatusCountsByKind(totals.statusCounts, row.statusCounts);
    totals.shapeMissingTotal += row.shapeMissingTotal;
    if (row.closestSelfShape !== null && row.closestSelfShape.missing.length === 1) {
      totals.selfClosestOneAwayGames += 1;
    }

    for (const [id, count] of Object.entries(row.shapeHits)) {
      totals.shapeHits[id] = (totals.shapeHits[id] ?? 0) + count;
    }
    for (const [id, count] of Object.entries(row.intentHits)) {
      totals.intentHits[id] = (totals.intentHits[id] ?? 0) + count;
    }
    for (const [id, count] of Object.entries(row.openCompNoEvidById)) {
      totals.openCompNoEvidById[id] = (totals.openCompNoEvidById[id] ?? 0) + count;
    }
    for (const [key, count] of Object.entries(row.shapeMissingCounts)) {
      totals.shapeMissingCounts[key] = (totals.shapeMissingCounts[key] ?? 0) + count;
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
    for (const [id, best] of Object.entries(row.shapeMovedRequiredBest)) {
      if (best >= 1) {
        bump(totals.gamesMovedRequiredComplete, id);
        totals.shapeMovedRequiredCompleteTotal += 1;
      }
    }
  }

  const sortedIds = (ids: Set<string>): string[] => [...ids].sort();
  return {
    byGroup,
    rows,
    movedRequiredZeroShapeIds: { self: sortedIds(movedRequiredZeroSelfIds), opponent: sortedIds(movedRequiredZeroOpponentIds) },
    movedRequiredZeroShapeCounts: { self: movedRequiredZeroSelfIds.size, opponent: movedRequiredZeroOpponentIds.size },
  };
}
