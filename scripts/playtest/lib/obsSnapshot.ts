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
  games: Array<{ no: number; total: number; result: string; ending: string | null; events: number; scores: Array<number | null>; plies: number[] }>;
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

function patientOf(inputs: ObsSnapshotInputs): PatientLike {
  return inputs.patient.data as PatientLike;
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

  const inputFiles: ObsSnapshotInputFile[] = [inputs.patient, inputs.timeCause, inputs.whatifData, inputs.direct, inputs.finalPositions, inputs.menu].filter(
    (f): f is ObsSnapshotInputFile => f !== undefined,
  );

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
