// STEP OBS-3a(docs/LANE_DIAG_LOG_2026-09.md §12.4、設計案 docs/DESIGN_OBSERVATION_LAYER_2026-09.md §14 の段取り 3)。
// 観測の写し(obs_snapshot.json)を、道具の出力から機械で作る。
//
// 【このファイルがやること】
// - `SNAPSHOT_ITEMS`: obsId → 取り出し方の白いリスト(docs/OBSERVATION_ITEMS.md §1 に登録済みの ID だけを使う)。
//   要素ごとに `extraEnumKeys`(その obsId だけ追加で許す列挙のキー。値の形を絞りたいときは `pattern` を付ける)
//   を持てる(2026-09-25 の司令塔の REVISE。`obs.menu.item` の `id` が M1〜M9 のときだけ残るのに使う)。
// - `numbersOnly(value, allowedEnumKeys)`: 値の中の文字列を、許された列挙のキーの直下にあるもの以外すべて捨てる。
// - `buildObsSnapshot(inputs, opts)`: 道具の出力をそのまま写して obs_snapshot.json の中身を組む。
//
// 【このファイルが絶対にやらないこと】
// - fs・エンジンの起動・子プロセス(CLI 側〈../obsSnapshot.ts〉が読んで渡す。ここは純粋関数だけ)。
// - 合計・割合・新しい数の計算(道具が既に出した数をそのまま写すだけ)。
// - 将棋の判断。
// - `person`・`title`・`id`・`kifuId`・`sfen`・`moves`・`pv`・`actualMove`・`played`・`best`・`text`・`labels`・
//   `oneLine`・`actionCore`・`evidenceName`・`verifyName` の値を出力へ残すこと(`numbersOnly` が、許された
//   列挙のキー以外の文字列をすべて落とすことで防ぐ ― 個々のキー名を特別扱いしない一般規則)。
// - STEP OBS-5f(§12.10 (A5))で `shapeId`(`data/` の形の id)・`square`・`piece`(幾何の事実。欠けていた
//   マスとそこに要る駒)の 2 種類だけ、`extraEnumKeys` で例外的に文字列を通す。**固定棋譜の id(`g01` 等)は
//   直接は通さず**、`--patient` の `games[].id`↔`no` で局番号(数)に変換してから使う(2 種類のまま保つため)。

// ---- numbersOnly(値の中の文字列を落とす) ----

/**
 * 許すキーの 1 件。プレーンな文字列なら「そのキーなら値を問わず残す」(既定の列挙のキーと同じ)。
 * `{ key, pattern }` は「そのキーで、かつ値が `pattern` に一致するときだけ残す」
 * (`obs.menu.item` の `id` が M1〜M9〈`^M[0-9]+$`〉のときだけ残るのに使う。2026-09-25 の司令塔の REVISE)。
 */
export type EnumKeyAllow = string | { key: string; pattern: RegExp };

/** `numbersOnly` が値を残す例外(列挙のキー)。docs/LANE_DIAG_LOG_2026-09.md §12.4 の白いリスト。 */
export const OBS_SNAPSHOT_ENUM_KEYS: readonly EnumKeyAllow[] = ["kind", "state", "group", "result", "ending", "side", "stage", "top1Side", "actualSide"];

function keyAllows(allow: EnumKeyAllow, key: string, value: string): boolean {
  if (typeof allow === "string") return allow === key;
  return allow.key === key && allow.pattern.test(value);
}

function stripStringsAt(value: unknown, key: string | null, allowedEnumKeys: readonly EnumKeyAllow[]): unknown {
  if (value === null) return null;
  if (typeof value === "number" || typeof value === "boolean") return value;
  if (typeof value === "string") return key !== null && allowedEnumKeys.some((allow) => keyAllows(allow, key, value)) ? value : undefined;
  if (Array.isArray(value)) {
    return value.map((item) => stripStringsAt(item, null, allowedEnumKeys)).filter((item) => item !== undefined);
  }
  if (typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      const stripped = stripStringsAt(v, k, allowedEnumKeys);
      if (stripped !== undefined) out[k] = stripped;
    }
    return out;
  }
  return undefined; // undefined・function・symbol(JSON には出ないはずだが念のため)
}

/**
 * 値の中の「文字列」を再帰的に見て、直下のキーが `allowedEnumKeys` にあるもの以外はすべて落とす
 * (数・真偽・null はそのまま残す)。個々のキー名〈person・title・id・sfen…〉を特別扱いしない
 * ― 一般規則(「文字列は許された列挙のキーの直下だけ」)がそれらを自動的に落とす。
 */
export function numbersOnly(value: unknown, allowedEnumKeys: readonly EnumKeyAllow[] = OBS_SNAPSHOT_ENUM_KEYS): unknown {
  return stripStringsAt(value, null, allowedEnumKeys);
}

// ---- 入出力の形 ----

export class ObsSnapshotError extends Error {}

export interface ObsSnapshotInputFile {
  /** 元のファイル名(basename だけ。絶対パスは持たない ― CLI 側が path.basename で作る)。 */
  name: string;
  sha256: string;
  data: unknown;
}

export interface ObsSnapshotInputs {
  /** patient_report_data.json(必須)。 */
  patient: ObsSnapshotInputFile;
  /** time_cause.json(必須。`kind: "time_cause"` を確かめる)。 */
  timeCause: ObsSnapshotInputFile;
  /** whatif_report_data.json(任意)。 */
  whatifData?: ObsSnapshotInputFile;
  /** direct_answers.json(任意)。 */
  direct?: ObsSnapshotInputFile;
  /** final_positions.json(任意。渡せば `kind: "final_positions"` を確かめる)。 */
  finalPositions?: ObsSnapshotInputFile;
  /** answer_menu.json(任意)。 */
  menu?: ObsSnapshotInputFile;
  /** obs_extra.json(任意。STEP OBS-5'。渡せば `kind: "obs_extra"` を確かめる)。 */
  extra?: ObsSnapshotInputFile;
  /** obs_geo.json(任意。STEP OBS-5〈docs/LANE_DIAG_LOG_2026-09.md §12.10 (A)〉。渡せば `kind: "obs_geo"` を確かめる)。 */
  geo?: ObsSnapshotInputFile;
  /**
   * recognition_measure.json(任意。STEP OBS-5c〈docs/LANE_DIAG_LOG_2026-09.md §12.10 (A2)〉。
   * `scripts/playtest/recognitionMeasure.ts` の出力をそのまま渡す。渡せば `kind: "recognition_measure"` を確かめる。
   */
  recognition?: ObsSnapshotInputFile;
}

export interface ObsSnapshotOptions {
  customer: string;
  group: string;
  /** `loadObsRegistry`(lib/hypothesis.ts)の集合。`SNAPSHOT_ITEMS` の全 obsId がここに無ければ例外。 */
  registry: Set<string>;
  gitHead: string | null;
  dirty: boolean | null;
}

export interface ObsSnapshotItem {
  obsId: string;
  path: string;
  value: unknown;
}

export interface ObsSnapshot {
  kind: "obs_snapshot";
  schemaVersion: "0.1";
  customer: string;
  group: string;
  gitHead: string | null;
  dirty: boolean | null;
  inputs: Array<{ name: string; sha256: string }>;
  items: ObsSnapshotItem[];
}

// ---- 道具の出力の形(この段が読む欄だけ。`unknown` として受け取った JSON をここでだけ型づける) ----

interface PatientLike {
  games: Array<{ no: number; id: string; total: number; result: string; ending: string | null; events: number; scores: Array<number | null>; plies: number[] }>;
  overview: unknown;
  findings: Array<{ kind: string; shown: boolean; numbers: Record<string, number | null> }>;
  events: unknown[];
  escapeScenes: unknown[];
  time: { bySpent: unknown; byLeft: unknown; afterLongThink: unknown; perMove: unknown; phaseSpent: unknown; timeUpLosses: unknown };
}

interface TimeCauseGameLike {
  group: string;
  gameNo: number;
  phaseSpentSec: unknown;
  longThinkCountByPhase: unknown;
  longThinkTotal: number;
  longestMove: unknown;
  longThinkStreakCount: number;
  midThinkByPhase: unknown;
  midThinkTotal: unknown;
  forkAmongLongThink: unknown;
  oppositeSideAmongForkLongThink: unknown;
  rookMark: unknown;
  remainingSec: unknown;
  timeUpLoss: unknown;
  timeLimitSec: unknown;
  midMoveSeconds: unknown;
}

interface TimeCauseGroupLike {
  group: string;
  timeUpLoss: unknown;
  other: unknown;
  rookMarkBreakdown: unknown;
  c10Table: unknown;
}

interface TimeCauseFileLike {
  kind?: unknown;
  games: TimeCauseGameLike[];
  groups: TimeCauseGroupLike[];
}

interface WhatifRepresentativeLike {
  kind: string;
  ply: number;
  displayPly: number;
  actualRank: number | null;
  actual: unknown;
  topGapCp: number | null;
  scene: unknown;
}

interface WhatifGameLike {
  gameNo: number;
  total: number;
  result: string;
  ending: string | null;
  positionsRead: number;
  matchesTop1: number;
  withinMultiPv: number;
  representative: WhatifRepresentativeLike | null;
}

interface WhatifDataLike {
  values: unknown;
  summary: unknown;
  games: WhatifGameLike[];
}

interface DirectAnswerLike {
  group: string;
  gameNo: number;
  displayPly: number;
  topGapCp: number | null;
  actualGapCp: number | null;
  firstVisibleNodes: number;
  top1Side: string;
  actualSide: string;
  top1Tags: unknown;
  actualTags: unknown;
}

interface DirectAnswersFileLike {
  answers: DirectAnswerLike[];
  counts: unknown;
}

interface FinalPositionEntryLike {
  group: string;
  gameNo: number;
  scoreCp: number | null;
  mate: number | null;
  mirrored: boolean;
}

interface FinalPositionsFileLike {
  kind?: unknown;
  entries: FinalPositionEntryLike[];
}

interface AnswerMenuItemLike {
  id: string;
  stage: string;
  minN: number;
  verifyGate: unknown;
  foundInSameData: boolean;
}

interface AnswerMenuFileLike {
  items: AnswerMenuItemLike[];
}

// STEP OBS-5'(docs/LANE_DIAG_LOG_2026-09.md §12.6)。obs_extra.json(この段が読む欄だけ)。
interface ObsExtraPairLike {
  gameNo: number;
  branchPly: number;
  displayPly: number;
  phase: string;
  spentSec: number | null;
  spentBucket: number | null;
  collapsed: boolean;
}

interface ObsExtraPhaseMovesLike {
  gameNo: number;
  timeUpLoss: boolean;
  early: unknown;
  mid: unknown;
  late: unknown;
}

interface ObsExtraFileLike {
  kind?: unknown;
  pairs: ObsExtraPairLike[];
  phaseMoves: ObsExtraPhaseMovesLike[];
  phaseSecPerMoveMedians: unknown;
}

// STEP OBS-5(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A))。obs_geo.json(この段が読む欄だけ)。
interface ObsGeoMoveLike {
  gameNo: number;
  kifPly: number;
  side: string;
  facts: unknown;
  combination: string;
  replyToCapture: string;
  replyToCheck: string;
}

interface ObsGeoDecisionContextLike {
  gameNo: number;
  kifPly: number;
  spentBucket: string;
  collapse: boolean | null;
  fork: boolean | null;
  inCheck: boolean | null;
  oppPrevCapture: boolean | null;
  oppPrevDrop: boolean | null;
  oppPrevGivesCheck: boolean | null;
  oppPrevPromotion: boolean | null;
  phase: string;
  evalBand: string | null;
}

// STEP OBS-5d(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A3))。obs_geo.json の `sideCrossTable[]`(この段が読む欄だけ)。
interface ObsGeoSideCrossCellLike {
  top1Side: string;
  actualSide: string;
  count: number;
}

interface ObsGeoFileLike {
  kind?: unknown;
  moves: ObsGeoMoveLike[];
  decisionContext: ObsGeoDecisionContextLike[];
  sideCrossTable: ObsGeoSideCrossCellLike[];
}

// STEP OBS-5c(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A2))。recognition_measure.json(この段が読む欄だけ)。
// `scripts/playtest/lib/recognitionMeasure.ts` の `StatusCountsByKind`・`ExposureTotals` の該当部分と
// 同じ形(`byGroup[group]` から `statusCounts`・`exposure` だけを読む。`rows` は読まない)。
interface RecognitionStateCountsLike {
  none: number;
  forming: number;
  completed: number;
  matched: number;
}

interface RecognitionStatusCountsBySideLike {
  self: RecognitionStateCountsLike;
  opponent: RecognitionStateCountsLike;
}

interface RecognitionStatusCountsByKindLike {
  shape: RecognitionStatusCountsBySideLike;
  intent: RecognitionStatusCountsBySideLike;
  opening: RecognitionStatusCountsBySideLike;
}

// 実際の出力には hiddenCompletedNoEvidence・weakClaims・weakClaimsShown・pickedByR5p・droppedByR6・
// droppedByR6ById(id → 数の対)も入っているが、この段が読むのは named/hedged/hidden の 3 つだけ
// (id の一覧・id → 数の対は写さない。docs/LANE_DIAG_LOG_2026-09.md §12.10 (A2) の指示)。
interface RecognitionExposureCountsLike {
  named: number;
  hedged: number;
  hidden: number;
}

interface RecognitionExposureBySideLike {
  self: RecognitionExposureCountsLike;
  opponent: RecognitionExposureCountsLike;
}

interface RecognitionExposureByKindLike {
  shape: RecognitionExposureBySideLike;
  intent: RecognitionExposureBySideLike;
  opening: RecognitionExposureBySideLike;
}

interface RecognitionGroupTotalsLike {
  statusCounts: RecognitionStatusCountsByKindLike;
  /** 値の組(A・B・C・D・D'・D'')ごとの露出。この段が読むのは `EXPOSURE_SET_FOR_VOCAB`(D'')だけ。 */
  exposure: Record<string, RecognitionExposureByKindLike>;
  // STEP OBS-5e(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A4))。「あと 1 枚」の中身。件数だけ
  // (id → 数の対・id の一覧はここでは読まない ― `lib/recognitionMeasure.ts` 側にはあるが写さない)。
  /** 欠けたマス・駒の延べ件数(forming だった局面だけ) */
  shapeMissingTotal: number;
  /** 自分側の「最も近づいた形」の欠けがちょうど 1 枚だった局の数 */
  selfClosestOneAwayGames: number;
  /** 「初期位置でない必要駒」だけで数え直した到達率が 1.0 に達した局数の延べ(id をまたいだ合計) */
  shapeMovedRequiredCompleteTotal: number;
}

// STEP OBS-5f(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A5))。「止まる場所」(局ごとの「あと 1 枚」の
// 内訳・「最も近づいた形」)。材料は rows[].closestSelfShape・rows[].shapeBest・rows[].shapeMovedRequiredBest
// (recognitionMeasure.ts の既存の出力。新しい計算は足していない)。
interface RecognitionMissingPieceLike {
  square: string;
  piece: string;
}

interface RecognitionClosestSelfShapeLike {
  shapeId: string;
  matchScore: number;
  missing: RecognitionMissingPieceLike[];
}

interface RecognitionRowLike {
  group: string;
  /** 固定棋譜の id(`lib/recognitionMeasure.ts` の `GameRow.id`)。ファイル名・人の名前ではない
   * (設計の時点でそう決められている)が、ここでは直接は写さず、`--patient` の `games[].id` と
   * 突き合わせて数の `no`(局番号)に変換してから使う(§12.10 (A5) の「文字列の穴」を 2 種類だけに限るため)。 */
  id: string;
  closestSelfShape: RecognitionClosestSelfShapeLike | null;
  shapeBest: Record<string, number>;
  shapeMovedRequiredBest: Record<string, number>;
}

interface RecognitionMeasureFileLike {
  kind?: unknown;
  byGroup: Record<string, RecognitionGroupTotalsLike>;
  /** STEP OBS-5e。「初期位置でない必要駒」が 0 の形の件数(自分側・相手側。id の一覧は読まない)。 */
  movedRequiredZeroShapeCounts: { self: number; opponent: number };
  /** STEP OBS-5f。局ごとの数(§1.16 参照)。 */
  rows: RecognitionRowLike[];
}

/** `obs.vocab.exposure` が読む値の組。統括の追加指示(2026-09-25)で D'' に決まっている。 */
const EXPOSURE_SET_FOR_VOCAB = "D''";

function recognitionOf(inputs: ObsSnapshotInputs): RecognitionMeasureFileLike {
  return inputs.recognition!.data as RecognitionMeasureFileLike;
}

/** `--recognition` を渡したのに byGroup に組が無ければ例外(黙って空を出さない)。 */
function recognitionGroupOf(inputs: ObsSnapshotInputs, group: string): RecognitionGroupTotalsLike {
  const found = recognitionOf(inputs).byGroup[group];
  if (found === undefined) {
    throw new ObsSnapshotError(`--recognition の byGroup に組 "${group}" が無い`);
  }
  return found;
}

/** 状態の件数の 4 つだけを選んで写す(件数だけ。他の欄が増えても影響しない)。 */
function stateCountsOf(c: RecognitionStateCountsLike): RecognitionStateCountsLike {
  return { none: c.none, forming: c.forming, completed: c.completed, matched: c.matched };
}

function statusCountsBySideOf(bySide: RecognitionStatusCountsBySideLike): RecognitionStatusCountsBySideLike {
  return { self: stateCountsOf(bySide.self), opponent: stateCountsOf(bySide.opponent) };
}

/** 露出の named/hedged/hidden の 3 つだけを選んで写す(hiddenCompletedNoEvidence 等・droppedByR6ById は写さない)。 */
function exposureCountsOf(c: RecognitionExposureCountsLike): { named: number; hedged: number; hidden: number } {
  return { named: c.named, hedged: c.hedged, hidden: c.hidden };
}

function exposureBySideOf(bySide: RecognitionExposureBySideLike): {
  self: { named: number; hedged: number; hidden: number };
  opponent: { named: number; hedged: number; hidden: number };
} {
  return { self: exposureCountsOf(bySide.self), opponent: exposureCountsOf(bySide.opponent) };
}

function patientOf(inputs: ObsSnapshotInputs): PatientLike {
  return inputs.patient.data as PatientLike;
}

// STEP OBS-5f。固定棋譜の id(`recognition rows[].id`)→ 局番号(`patient games[].no`)。
// `--patient` は必須入力で組ごとのファイルなので、同じ組の局なら id は揃っているはず。
// 揃わない行(--patient の games に無い id)は、その組の対象外として無視する
// (`scripts/playtest/finalPositions.ts` の `selectTargets` と同じ考え方)。
function patientGameNoById(inputs: ObsSnapshotInputs): Map<string, number> {
  return new Map(patientOf(inputs).games.map((g) => [g.id, g.no]));
}

function recognitionRowsForGroup(inputs: ObsSnapshotInputs, group: string): RecognitionRowLike[] {
  return recognitionOf(inputs).rows.filter((r) => r.group === group);
}

function timeCauseOf(inputs: ObsSnapshotInputs): TimeCauseFileLike {
  return inputs.timeCause.data as TimeCauseFileLike;
}

function timeCauseGamesForGroup(inputs: ObsSnapshotInputs, group: string): TimeCauseGameLike[] {
  return timeCauseOf(inputs).games.filter((g) => g.group === group);
}

function timeCauseGroupsForGroup(inputs: ObsSnapshotInputs, group: string): TimeCauseGroupLike[] {
  return timeCauseOf(inputs).groups.filter((g) => g.group === group);
}

// ---- SNAPSHOT_ITEMS(obsId → 取り出し方の白いリスト) ----

/** 任意入力が渡されていないとき、その obsId を丸ごと出さない印(「無い」を空で埋めない)。 */
const SKIP: unique symbol = Symbol("obsSnapshot.skip");

export interface SnapshotItemDefinition {
  obsId: string;
  /** 出どころの説明(ドキュメント用の文字列。実際の値の取り出しは `pick` が行う)。 */
  path: string;
  pick: (inputs: ObsSnapshotInputs, opts: ObsSnapshotOptions) => unknown;
  /** この obsId だけ追加で許す列挙のキー(既定の `OBS_SNAPSHOT_ENUM_KEYS` に無いもの)。2026-09-25 の司令塔の REVISE。 */
  extraEnumKeys?: readonly EnumKeyAllow[];
}

/** `obs.menu.item` の `id` を残す条件(M1〜M9)。docs/OBSERVATION_ITEMS.md の `AnswerMenuId`(`lib/answerMenu.ts`)と同じ形。 */
const MENU_ITEM_ID_PATTERN = /^M[0-9]+$/;

export const SNAPSHOT_ITEMS: readonly SnapshotItemDefinition[] = [
  // ---- patient_report_data.json(必須。--group では絞らない ― 組ごとのファイルなのでそのまま) ----
  { obsId: "obs.report.overview", path: "overview", pick: (inputs) => patientOf(inputs).overview },
  {
    obsId: "obs.report.finding",
    path: "findings[].{kind,shown,numbers}",
    pick: (inputs) => patientOf(inputs).findings.map((f) => ({ kind: f.kind, shown: f.shown, numbers: f.numbers })),
  },
  // 「数と kind」(計画 §12.4): events[] をそのまま渡し、numbersOnly が played・best・after5・playedUsi・
  // bestUsi(文字列)を落として gameNo・kind・ply・before・after・sameBest・afterPassMate だけを残す。
  { obsId: "obs.report.event", path: "events[]", pick: (inputs) => patientOf(inputs).events },
  { obsId: "obs.report.escapeScene", path: "escapeScenes[]", pick: (inputs) => patientOf(inputs).escapeScenes },
  {
    obsId: "obs.eval.game",
    path: "games[].{no,total,result,ending,events}",
    pick: (inputs) => patientOf(inputs).games.map((g) => ({ no: g.no, total: g.total, result: g.result, ending: g.ending, events: g.events })),
  },
  {
    obsId: "obs.eval.score",
    path: "games[].{no,scores,plies}",
    pick: (inputs) => patientOf(inputs).games.map((g) => ({ no: g.no, scores: g.scores, plies: g.plies })),
  },
  { obsId: "obs.time.bySpent", path: "time.bySpent", pick: (inputs) => patientOf(inputs).time.bySpent },
  { obsId: "obs.time.byLeft", path: "time.byLeft", pick: (inputs) => patientOf(inputs).time.byLeft },
  { obsId: "obs.time.afterLongThink", path: "time.afterLongThink", pick: (inputs) => patientOf(inputs).time.afterLongThink },
  { obsId: "obs.time.perMove", path: "time.perMove", pick: (inputs) => patientOf(inputs).time.perMove },
  { obsId: "obs.time.phaseSpentPatient", path: "time.phaseSpent", pick: (inputs) => patientOf(inputs).time.phaseSpent },
  { obsId: "obs.time.timeUpLosses", path: "time.timeUpLosses", pick: (inputs) => patientOf(inputs).time.timeUpLosses },

  // ---- time_cause.json の局(11 本。必須。games[] は --group に一致するものだけ) ----
  {
    obsId: "obs.time.phaseSpentSec",
    path: "time_cause games[].phaseSpentSec",
    pick: (inputs, opts) => timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, phaseSpentSec: g.phaseSpentSec })),
  },
  {
    obsId: "obs.time.longThinkCountByPhase",
    path: "time_cause games[].longThinkCountByPhase",
    pick: (inputs, opts) => timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, longThinkCountByPhase: g.longThinkCountByPhase })),
  },
  {
    obsId: "obs.time.longThinkTotal",
    path: "time_cause games[].longThinkTotal",
    pick: (inputs, opts) => timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, longThinkTotal: g.longThinkTotal })),
  },
  {
    obsId: "obs.time.longestMove",
    path: "time_cause games[].longestMove",
    pick: (inputs, opts) => timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, longestMove: g.longestMove })),
  },
  {
    obsId: "obs.time.longThinkStreakCount",
    path: "time_cause games[].longThinkStreakCount",
    pick: (inputs, opts) => timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, longThinkStreakCount: g.longThinkStreakCount })),
  },
  {
    obsId: "obs.time.midThinkByPhase",
    path: "time_cause games[].{midThinkByPhase,midThinkTotal}",
    pick: (inputs, opts) =>
      timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, midThinkByPhase: g.midThinkByPhase, midThinkTotal: g.midThinkTotal })),
  },
  {
    obsId: "obs.time.forkAmongLongThink",
    path: "time_cause games[].forkAmongLongThink",
    pick: (inputs, opts) => timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, forkAmongLongThink: g.forkAmongLongThink })),
  },
  {
    obsId: "obs.time.oppositeSideAmongForkLongThink",
    path: "time_cause games[].oppositeSideAmongForkLongThink",
    pick: (inputs, opts) =>
      timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, oppositeSideAmongForkLongThink: g.oppositeSideAmongForkLongThink })),
  },
  {
    obsId: "obs.time.rookMark",
    path: "time_cause games[].rookMark",
    pick: (inputs, opts) => timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, rookMark: g.rookMark })),
  },
  {
    obsId: "obs.time.remainingSec",
    path: "time_cause games[].{remainingSec,timeUpLoss,timeLimitSec}",
    pick: (inputs, opts) =>
      timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, remainingSec: g.remainingSec, timeUpLoss: g.timeUpLoss, timeLimitSec: g.timeLimitSec })),
  },
  {
    obsId: "obs.time.midMoveSeconds",
    path: "time_cause games[].midMoveSeconds",
    pick: (inputs, opts) => timeCauseGamesForGroup(inputs, opts.group).map((g) => ({ gameNo: g.gameNo, midMoveSeconds: g.midMoveSeconds })),
  },

  // ---- time_cause.json の組(3 本。必須。groups[] は --group に一致するものだけ) ----
  {
    obsId: "obs.time.groupMedians",
    path: "time_cause groups[].{timeUpLoss,other}",
    pick: (inputs, opts) => timeCauseGroupsForGroup(inputs, opts.group).map((g) => ({ group: g.group, timeUpLoss: g.timeUpLoss, other: g.other })),
  },
  {
    obsId: "obs.time.rookMarkBreakdown",
    path: "time_cause groups[].rookMarkBreakdown",
    pick: (inputs, opts) => timeCauseGroupsForGroup(inputs, opts.group).map((g) => ({ group: g.group, rookMarkBreakdown: g.rookMarkBreakdown })),
  },
  {
    obsId: "obs.time.c10Table",
    path: "time_cause groups[].c10Table",
    pick: (inputs, opts) => timeCauseGroupsForGroup(inputs, opts.group).map((g) => ({ group: g.group, c10Table: g.c10Table })),
  },

  // ---- whatif_report_data.json(任意。--group では絞らない ― 組ごとのファイル) ----
  { obsId: "obs.fork.values", path: "values", pick: (inputs) => (inputs.whatifData === undefined ? SKIP : (inputs.whatifData.data as WhatifDataLike).values) },
  {
    obsId: "obs.fork.game",
    path: "games[].{gameNo,total,result,ending,positionsRead,matchesTop1,withinMultiPv}",
    pick: (inputs) => {
      if (inputs.whatifData === undefined) return SKIP;
      const whatif = inputs.whatifData.data as WhatifDataLike;
      return whatif.games.map((g) => ({
        gameNo: g.gameNo,
        total: g.total,
        result: g.result,
        ending: g.ending,
        positionsRead: g.positionsRead,
        matchesTop1: g.matchesTop1,
        withinMultiPv: g.withinMultiPv,
      }));
    },
  },
  {
    obsId: "obs.fork.representative",
    path: "games[].representative.{kind,ply,displayPly,actualRank,actual,topGapCp}",
    pick: (inputs) => {
      if (inputs.whatifData === undefined) return SKIP;
      const whatif = inputs.whatifData.data as WhatifDataLike;
      return whatif.games.map((g) => ({
        gameNo: g.gameNo,
        representative:
          g.representative === null
            ? null
            : {
                kind: g.representative.kind,
                ply: g.representative.ply,
                displayPly: g.representative.displayPly,
                actualRank: g.representative.actualRank,
                actual: g.representative.actual,
                topGapCp: g.representative.topGapCp,
              },
      }));
    },
  },
  {
    obsId: "obs.fork.scene",
    path: "games[].representative.scene",
    pick: (inputs) => {
      if (inputs.whatifData === undefined) return SKIP;
      const whatif = inputs.whatifData.data as WhatifDataLike;
      return whatif.games.map((g) => ({ gameNo: g.gameNo, scene: g.representative === null ? null : g.representative.scene }));
    },
  },
  { obsId: "obs.fork.summary", path: "summary", pick: (inputs) => (inputs.whatifData === undefined ? SKIP : (inputs.whatifData.data as WhatifDataLike).summary) },

  // ---- direct_answers.json(任意。answers[] は --group に一致するものだけ) ----
  {
    obsId: "obs.direct.answer",
    path: "answers[].{gameNo,displayPly,topGapCp,actualGapCp,firstVisibleNodes,top1Side,actualSide,top1Tags,actualTags}",
    pick: (inputs, opts) => {
      if (inputs.direct === undefined) return SKIP;
      const direct = inputs.direct.data as DirectAnswersFileLike;
      return direct.answers
        .filter((a) => a.group === opts.group)
        .map((a) => ({
          gameNo: a.gameNo,
          displayPly: a.displayPly,
          topGapCp: a.topGapCp,
          actualGapCp: a.actualGapCp,
          firstVisibleNodes: a.firstVisibleNodes,
          top1Side: a.top1Side,
          actualSide: a.actualSide,
          top1Tags: a.top1Tags,
          actualTags: a.actualTags,
        }));
    },
  },
  { obsId: "obs.direct.counts", path: "counts", pick: (inputs) => (inputs.direct === undefined ? SKIP : (inputs.direct.data as DirectAnswersFileLike).counts) },

  // ---- final_positions.json(任意。entries[] は --group に一致するものだけ) ----
  {
    obsId: "obs.direct.finalPosition",
    path: "entries[].{gameNo,scoreCp,mate,mirrored}",
    pick: (inputs, opts) => {
      if (inputs.finalPositions === undefined) return SKIP;
      const finalPositions = inputs.finalPositions.data as FinalPositionsFileLike;
      return finalPositions.entries.filter((e) => e.group === opts.group).map((e) => ({ gameNo: e.gameNo, scoreCp: e.scoreCp, mate: e.mate, mirrored: e.mirrored }));
    },
  },

  // ---- answer_menu.json(任意。--group では絞らない) ----
  {
    obsId: "obs.menu.item",
    path: "items[].{id,stage,minN,verifyGate,foundInSameData}",
    pick: (inputs) => {
      if (inputs.menu === undefined) return SKIP;
      const menu = inputs.menu.data as AnswerMenuFileLike;
      return menu.items.map((i) => ({ id: i.id, stage: i.stage, minN: i.minN, verifyGate: i.verifyGate, foundInSameData: i.foundInSameData }));
    },
    // `id`(M1〜M9)だけ追加で許す(2026-09-25 の司令塔の REVISE: 1 周で行動の表を引くのに必須)。
    // M パターンでない `id`(他の obsId の `id` フィールド)は、この extraEnumKeys がその obsId のときしか
    // 効かないので、今までどおり落ちる。
    extraEnumKeys: [{ key: "id", pattern: MENU_ITEM_ID_PATTERN }],
  },

  // ---- obs_extra.json(任意。STEP OBS-5'。--group では絞らない ― 既に 1 組ぶんのファイル) ----
  {
    obsId: "obs.time.pairSpent",
    path: "obs_extra pairs[]",
    pick: (inputs) => (inputs.extra === undefined ? SKIP : (inputs.extra.data as ObsExtraFileLike).pairs),
    // `phase`(early/mid/late)は列挙のキーとして残す(計画 §12.6: 「組と局・手の対応」に段が要る)。
    extraEnumKeys: ["phase"],
  },
  {
    obsId: "obs.time.phaseMoves",
    path: "obs_extra phaseMoves[]",
    pick: (inputs) => (inputs.extra === undefined ? SKIP : (inputs.extra.data as ObsExtraFileLike).phaseMoves),
  },
  {
    obsId: "obs.time.phaseSecPerMoveMedians",
    path: "obs_extra phaseSecPerMoveMedians",
    pick: (inputs) => (inputs.extra === undefined ? SKIP : (inputs.extra.data as ObsExtraFileLike).phaseSecPerMoveMedians),
  },

  // ---- obs_geo.json(任意。STEP OBS-5〈docs/LANE_DIAG_LOG_2026-09.md §12.10 (A)〉。--group では絞らない) ----
  {
    obsId: "obs.geo.moveCombination",
    path: "obs_geo moves[].{gameNo,kifPly,side,facts,combination}",
    pick: (inputs) => {
      if (inputs.geo === undefined) return SKIP;
      const geo = inputs.geo.data as ObsGeoFileLike;
      return geo.moves.map((m) => ({ gameNo: m.gameNo, kifPly: m.kifPly, side: m.side, facts: m.facts, combination: m.combination }));
    },
    // `combination` は幾何の組み合わせの名前(将棋の語彙を含まない。lib/obsGeo.ts 参照)。`side` は既に base の許可に含まれる。
    extraEnumKeys: ["combination"],
  },
  {
    obsId: "obs.geo.replyToCapture",
    path: "obs_geo moves[].{gameNo,kifPly,replyToCapture}",
    pick: (inputs) => {
      if (inputs.geo === undefined) return SKIP;
      const geo = inputs.geo.data as ObsGeoFileLike;
      return geo.moves.map((m) => ({ gameNo: m.gameNo, kifPly: m.kifPly, replyToCapture: m.replyToCapture }));
    },
    extraEnumKeys: ["replyToCapture"],
  },
  {
    obsId: "obs.geo.replyToCheck",
    path: "obs_geo moves[].{gameNo,kifPly,replyToCheck}",
    pick: (inputs) => {
      if (inputs.geo === undefined) return SKIP;
      const geo = inputs.geo.data as ObsGeoFileLike;
      return geo.moves.map((m) => ({ gameNo: m.gameNo, kifPly: m.kifPly, replyToCheck: m.replyToCheck }));
    },
    extraEnumKeys: ["replyToCheck"],
  },
  {
    obsId: "obs.time.decisionContext",
    path: "obs_geo decisionContext[]",
    pick: (inputs) => (inputs.geo === undefined ? SKIP : (inputs.geo.data as ObsGeoFileLike).decisionContext),
    // `spentBucket`("≤9"/">9")・`phase`・`evalBand` は列挙のキーとして残す(統括経由の追加指示、2026-09-25)。
    extraEnumKeys: ["spentBucket", "phase", "evalBand"],
  },
  // STEP OBS-5d(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A3))。出どころは obs_geo.json だが、側の一致の
  // 交差表という中身にならい obsId の列は `fork` にした(実装担当の判断。理由は報告に書く)。
  // `top1Side`・`actualSide` は既に `OBS_SNAPSHOT_ENUM_KEYS` にあるので extraEnumKeys は不要。
  {
    obsId: "obs.fork.sideCrossTable",
    path: "obs_geo sideCrossTable[]",
    pick: (inputs) => (inputs.geo === undefined ? SKIP : (inputs.geo.data as ObsGeoFileLike).sideCrossTable),
  },

  // ---- recognition_measure.json(任意。STEP OBS-5c〈docs/LANE_DIAG_LOG_2026-09.md §12.10 (A2)〉。
  //      --group に一致する byGroup[group] だけ。値は件数だけ〈id の一覧・droppedByR6ById は写さない〉) ----
  {
    obsId: "obs.vocab.shapeStatus",
    path: "recognition byGroup[group].statusCounts.shape.{self,opponent}.{none,forming,completed,matched}",
    pick: (inputs, opts) => (inputs.recognition === undefined ? SKIP : statusCountsBySideOf(recognitionGroupOf(inputs, opts.group).statusCounts.shape)),
  },
  {
    obsId: "obs.vocab.intentStatus",
    path: "recognition byGroup[group].statusCounts.intent.{self,opponent}.{none,forming,completed,matched}",
    pick: (inputs, opts) => (inputs.recognition === undefined ? SKIP : statusCountsBySideOf(recognitionGroupOf(inputs, opts.group).statusCounts.intent)),
  },
  {
    obsId: "obs.vocab.openingStatus",
    path: "recognition byGroup[group].statusCounts.opening.{self,opponent}.{none,forming,completed,matched}",
    pick: (inputs, opts) => (inputs.recognition === undefined ? SKIP : statusCountsBySideOf(recognitionGroupOf(inputs, opts.group).statusCounts.opening)),
  },
  {
    obsId: "obs.vocab.exposure",
    path: "recognition byGroup[group].exposure[\"D''\"].{shape,intent,opening}.{self,opponent}.{named,hedged,hidden}",
    pick: (inputs, opts) => {
      if (inputs.recognition === undefined) return SKIP;
      const group = recognitionGroupOf(inputs, opts.group);
      const set = group.exposure[EXPOSURE_SET_FOR_VOCAB];
      if (set === undefined) {
        throw new ObsSnapshotError(`--recognition の byGroup["${opts.group}"].exposure に値の組 "${EXPOSURE_SET_FOR_VOCAB}" が無い`);
      }
      return { shape: exposureBySideOf(set.shape), intent: exposureBySideOf(set.intent), opening: exposureBySideOf(set.opening) };
    },
  },

  // ---- recognition_measure.json(STEP OBS-5e〈docs/LANE_DIAG_LOG_2026-09.md §12.10 (A4)〉。
  //      「あと 1 枚」の中身。件数だけ ― id の一覧・id → 数の対は写さない) ----
  {
    obsId: "obs.vocab.shapeMissingSummary",
    path: "recognition byGroup[group].{shapeMissingTotal,selfClosestOneAwayGames}",
    pick: (inputs, opts) => {
      if (inputs.recognition === undefined) return SKIP;
      const group = recognitionGroupOf(inputs, opts.group);
      return { shapeMissingTotal: group.shapeMissingTotal, selfClosestOneAwayGames: group.selfClosestOneAwayGames };
    },
  },
  {
    obsId: "obs.vocab.shapeMovedRequiredSummary",
    path: "recognition byGroup[group].shapeMovedRequiredCompleteTotal, recognition movedRequiredZeroShapeCounts.{self,opponent}",
    pick: (inputs, opts) => {
      if (inputs.recognition === undefined) return SKIP;
      const group = recognitionGroupOf(inputs, opts.group);
      const zero = recognitionOf(inputs).movedRequiredZeroShapeCounts;
      return { completeTotal: group.shapeMovedRequiredCompleteTotal, zeroCount: { self: zero.self, opponent: zero.opponent } };
    },
  },

  // ---- recognition_measure.json(STEP OBS-5f〈docs/LANE_DIAG_LOG_2026-09.md §12.10 (A5)〉。
  //      「止まる場所」。局ごとの内訳(id ではなく patient から引いた局番号 `gameNo` で示す)。
  //      **ここで初めて「形の id」と「マス + 駒」の文字列を通す**(白いリストの穴。他の文字列は
  //      いままでどおり `numbersOnly` が落とす)。--patient の games に無い id(組の対象外)は無視する。 ----
  {
    obsId: "obs.vocab.shapeOneAwayDetail",
    path: "recognition rows[].closestSelfShape(missing が 1 件の行) → {gameNo,shapeId,square,piece}",
    pick: (inputs, opts) => {
      if (inputs.recognition === undefined) return SKIP;
      const gameNoById = patientGameNoById(inputs);
      const out: Array<{ gameNo: number; shapeId: string; square: string; piece: string }> = [];
      for (const row of recognitionRowsForGroup(inputs, opts.group)) {
        const closest = row.closestSelfShape;
        if (closest === null || closest.missing.length !== 1) continue;
        const gameNo = gameNoById.get(row.id);
        if (gameNo === undefined) continue; // --patient の games に無い局(組の対象外)。無視する
        const missing = closest.missing[0]!;
        out.push({ gameNo, shapeId: closest.shapeId, square: missing.square, piece: missing.piece });
      }
      return out;
    },
    // `shapeId` は `data/` の形の認識(review_status を経たもの)。`square`・`piece` は幾何の事実
    // (欠けていたマスとそこに要る駒)。この 2 種類だけを通す(§12.10 (A5) の条件)。
    extraEnumKeys: ["shapeId", "square", "piece"],
  },
  {
    obsId: "obs.vocab.shapeClosestPerGame",
    path: "recognition rows[].{closestSelfShape.shapeId,shapeBest,shapeMovedRequiredBest} → {gameNo,shapeId,rawBest,movedRequiredBest}",
    pick: (inputs, opts) => {
      if (inputs.recognition === undefined) return SKIP;
      const gameNoById = patientGameNoById(inputs);
      const out: Array<{ gameNo: number; shapeId: string; rawBest: number | null; movedRequiredBest: number | null }> = [];
      for (const row of recognitionRowsForGroup(inputs, opts.group)) {
        const closest = row.closestSelfShape;
        if (closest === null) continue;
        const gameNo = gameNoById.get(row.id);
        if (gameNo === undefined) continue; // --patient の games に無い局(組の対象外)。無視する
        out.push({
          gameNo,
          shapeId: closest.shapeId,
          rawBest: row.shapeBest[closest.shapeId] ?? null,
          // 分母 0(初期位置でない必要駒が 0)の形は shapeMovedRequiredBest に入らない = 数え直せない → null
          movedRequiredBest: row.shapeMovedRequiredBest[closest.shapeId] ?? null,
        });
      }
      return out;
    },
    extraEnumKeys: ["shapeId"],
  },
];

// ---- 組み立て ----

/**
 * `SNAPSHOT_ITEMS` を差し替えられる版(試験専用。「登録簿に無い obsId を足すと例外」を確かめるため)。
 * `buildObsSnapshot` はこれを既定の `SNAPSHOT_ITEMS` で呼ぶだけ。
 */
export function buildObsSnapshotFromItems(items: readonly SnapshotItemDefinition[], inputs: ObsSnapshotInputs, opts: ObsSnapshotOptions): ObsSnapshot {
  const timeCause = timeCauseOf(inputs);
  if (timeCause.kind !== "time_cause") {
    throw new ObsSnapshotError(`--time-cause の kind が "time_cause" でない(${JSON.stringify(timeCause.kind)})`);
  }
  if (inputs.finalPositions !== undefined) {
    const finalPositions = inputs.finalPositions.data as FinalPositionsFileLike;
    if (finalPositions.kind !== "final_positions") {
      throw new ObsSnapshotError(`--final-positions の kind が "final_positions" でない(${JSON.stringify(finalPositions.kind)})`);
    }
  }
  if (inputs.extra !== undefined) {
    const extra = inputs.extra.data as ObsExtraFileLike;
    if (extra.kind !== "obs_extra") {
      throw new ObsSnapshotError(`--extra の kind が "obs_extra" でない(${JSON.stringify(extra.kind)})`);
    }
  }
  if (inputs.geo !== undefined) {
    const geo = inputs.geo.data as ObsGeoFileLike;
    if (geo.kind !== "obs_geo") {
      throw new ObsSnapshotError(`--geo の kind が "obs_geo" でない(${JSON.stringify(geo.kind)})`);
    }
  }
  if (inputs.recognition !== undefined) {
    const recognition = recognitionOf(inputs);
    if (recognition.kind !== "recognition_measure") {
      throw new ObsSnapshotError(`--recognition の kind が "recognition_measure" でない(${JSON.stringify(recognition.kind)})`);
    }
  }

  const inputFiles: ObsSnapshotInputFile[] = [
    inputs.patient,
    inputs.timeCause,
    inputs.whatifData,
    inputs.direct,
    inputs.finalPositions,
    inputs.menu,
    inputs.extra,
    inputs.geo,
    inputs.recognition,
  ].filter((f): f is ObsSnapshotInputFile => f !== undefined);

  const items_: ObsSnapshotItem[] = [];
  for (const def of items) {
    if (!opts.registry.has(def.obsId)) {
      throw new ObsSnapshotError(`SNAPSHOT_ITEMS の obsId「${def.obsId}」が登録簿(loadObsRegistry)に無い`);
    }
    const raw = def.pick(inputs, opts);
    if (raw === SKIP) continue;
    const allowedEnumKeys = def.extraEnumKeys === undefined ? OBS_SNAPSHOT_ENUM_KEYS : [...OBS_SNAPSHOT_ENUM_KEYS, ...def.extraEnumKeys];
    items_.push({ obsId: def.obsId, path: def.path, value: numbersOnly(raw, allowedEnumKeys) });
  }

  return {
    kind: "obs_snapshot",
    schemaVersion: "0.1",
    customer: opts.customer,
    group: opts.group,
    gitHead: opts.gitHead,
    dirty: opts.dirty,
    inputs: inputFiles.map((f) => ({ name: f.name, sha256: f.sha256 })),
    items: items_,
  };
}

/** 道具の出力(`inputs`)から `obs_snapshot.json` の中身を組む(`SNAPSHOT_ITEMS` を使う既定の呼び方)。 */
export function buildObsSnapshot(inputs: ObsSnapshotInputs, opts: ObsSnapshotOptions): ObsSnapshot {
  return buildObsSnapshotFromItems(SNAPSHOT_ITEMS, inputs, opts);
}
