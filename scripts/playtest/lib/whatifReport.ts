// STEP WHATIF 作業 2(docs/STEP_WHATIF_PLAN_2026-09-22.md §2.3・§7.3)。「見せる段」の材料(付録 2)を組む純粋関数。
//
// 【このファイルがやること】
// - 局ごとの whatif.jsonl(scripts/playtest/whatif.ts、STEP WHATIF 作業 1 の出力)と、patient_report_data.json の
//   games の欄(id・side・total・result・ending・scores・plies)から、付録 2(分かれ道)の材料 whatif_report_data.json を組む
// - 1 ページ目の集計(§7.3): 読んだ局面・第 1 候補と同じ・上位 5 つ・fork/narrowHeld/chanceHeld の延べ数と
//   重なりを除いた数・両方の側が出た数/場面の数・攻めの側に合法手なし・負けた局のうち narrowHeld があった局の数
//   (**消費時間の表はここでは作らない**。§7.3 末尾。入力に消費時間が無い)
// - 局ごとの代表の場面 1 つ(§2.3・§7.3): 負けた局は summary.biggestFork の局面、勝った局は narrowHeld のうち
//   topGapCp が最大の局面(無ければ chanceHeld の最初、それも無ければ fork の最大(= biggestFork)、
//   それも無ければ「載せる局面なし」= null)。選び方は `pickRepresentativePly` の 1 か所にまとめ、試験する
// - 場面の材料: displayPly・種類・position の候補 3 つ(手・評価・読み筋)・実戦の手と順位・scene の attack/defense・
//   sideGapCp・5 手進めた局面のための pv(第 1 候補。実戦が第 1 候補なら第 2 候補)を、apps/server の `applyMove` で
//   実際に SFEN へ適用してから渡す(python 側で盤のルールを二重に実装しない。手は USI のまま出す ― 日本語表記・
//   盤面図は report-pdf/render_whatif.py の役目)
//
// 【mirrored の扱い】whatif.jsonl の sfen・USI は「本人 = 先手」にそろえた向き(lib/whatif.ts のコメント参照)。
// このファイルはその向きのまま SFEN・USI を出力へ渡す(回し直さない)。表示の向き(本人が後手なら盤を反転する等)は、
// reportData.ts・report-pdf が後手の局をどう表しているか(`side`・`plyOffset` を見て python 側が判断する)と
// 同じ流儀にそろえる ― 回し方を新しく決めない(依頼の指示どおり)。
//
// 【このファイルが絶対にやらないこと】
// - ファイルの読み書き・エンジンの起動・子プロセスの起動(呼び出し側(scripts/playtest/whatifReport.ts)の役目)
// - 手のねらい・わけ・良し悪しの文を作ること。第 1 候補を「正解」と呼ぶこと
// - 名前・/Users/ を含む絶対パスを出力へ含めること

import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import type { WhatifBiggestFork, WhatifCandidate, WhatifGameSummary, WhatifPosition, WhatifScene, WhatifSceneReadSummary, WhatifSideRead } from "./whatif.js";

export class WhatifReportError extends Error {}

// ---- whatif.jsonl の行の形(scripts/playtest/whatif.ts が書くとおり) ----

export interface WhatifMetaRow {
  kind: "meta";
  kifuId: string;
  values: { sideZoneRadius: number; startPly: number; minLossCp: number; narrowGapCp: number; riseCp: number; [key: string]: number };
  [key: string]: unknown;
}

export interface WhatifPositionRow extends WhatifPosition {
  kind: "position";
  displayPly: number;
}

export interface WhatifSceneRow extends WhatifScene {
  kind: "scene";
  displayPly: number;
}

export interface WhatifSummaryRow extends Omit<WhatifGameSummary, "biggestFork"> {
  kind: "summary";
  biggestFork: (WhatifBiggestFork & { displayPly: number }) | null;
  sceneReads: WhatifSceneReadSummary;
  timingMs: { pass1: number; pass2: number };
}

export interface ParsedWhatifJsonl {
  meta: WhatifMetaRow;
  positions: WhatifPositionRow[];
  scenes: WhatifSceneRow[];
  summary: WhatifSummaryRow;
}

/** `whatif.jsonl` の中身(文字列)を読む。meta・summary が無ければ止める(推測しない)。 */
export function parseWhatifJsonl(content: string): ParsedWhatifJsonl {
  const lines = content
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
  let meta: WhatifMetaRow | undefined;
  const positions: WhatifPositionRow[] = [];
  const scenes: WhatifSceneRow[] = [];
  let summary: WhatifSummaryRow | undefined;
  for (const raw of lines) {
    const parsed = JSON.parse(raw) as { kind?: unknown };
    if (parsed.kind === "meta") meta = parsed as unknown as WhatifMetaRow;
    else if (parsed.kind === "position") positions.push(parsed as unknown as WhatifPositionRow);
    else if (parsed.kind === "scene") scenes.push(parsed as unknown as WhatifSceneRow);
    else if (parsed.kind === "summary") summary = parsed as unknown as WhatifSummaryRow;
  }
  if (meta === undefined) throw new WhatifReportError("whatif.jsonl に meta 行が無い");
  if (summary === undefined) throw new WhatifReportError("whatif.jsonl に summary 行が無い");
  return { meta, positions, scenes, summary };
}

// ---- 代表の場面の選び方(§2.3・§7.3。4 つの分岐) ----

export type WhatifSceneKind = "fork" | "narrowHeld" | "chanceHeld";

export interface RepresentativePick {
  kind: WhatifSceneKind;
  ply: number;
}

/**
 * 局ごとの代表の場面 1 つを選ぶ(4 つの分岐、依頼の指示のとおり)。
 * 1. 負けた局: summary.biggestFork の局面(無ければ null)
 * 2. 勝った局・narrowHeld がある: topGapCp が最大の局面(同点は早い手数。既に ply 昇順の配列なので `>` で判定する)
 * 3. 勝った局・narrowHeld が無く chanceHeld がある: 最初(最も早い手数)の局面
 * 4. 勝った局・どちらも無い: summary.biggestFork の局面(無ければ null = 「載せる局面なし」)
 */
export function pickRepresentativePly(result: "勝ち" | "負け", positions: readonly WhatifPositionRow[], summary: WhatifSummaryRow): RepresentativePick | null {
  if (result === "負け") {
    return summary.biggestFork === null ? null : { kind: "fork", ply: summary.biggestFork.ply };
  }
  const narrowHeldPositions = positions.filter((p) => p.scenes.narrowHeld);
  if (narrowHeldPositions.length > 0) {
    let best = narrowHeldPositions[0]!;
    for (const p of narrowHeldPositions.slice(1)) {
      if (p.topGapCp! > best.topGapCp!) best = p;
    }
    return { kind: "narrowHeld", ply: best.ply };
  }
  const chanceHeldPositions = positions.filter((p) => p.scenes.chanceHeld);
  if (chanceHeldPositions.length > 0) {
    return { kind: "chanceHeld", ply: chanceHeldPositions[0]!.ply };
  }
  return summary.biggestFork === null ? null : { kind: "fork", ply: summary.biggestFork.ply };
}

// ---- 場面の材料(候補・attack/defense・5 手進めた局面) ----

export interface WhatifCandidateOut {
  move: string;
  scoreCp: number | null;
  mate: number | null;
  pv: string[];
}

function candidateOut(candidate: WhatifCandidate): WhatifCandidateOut {
  return { move: candidate.move, scoreCp: candidate.scoreCp, mate: candidate.mate, pv: candidate.pv.slice(0, 5) };
}

export interface WhatifSideReadOut {
  state: "found" | "noLegalMove" | "notMeasured";
  move?: string;
  scoreCp?: number | null;
  mate?: number | null;
  pv?: string[];
}

function sideReadOut(read: WhatifSideRead): WhatifSideReadOut {
  if (read.state !== "found") return { state: read.state };
  return { state: "found", move: read.result.move, scoreCp: read.result.scoreCp, mate: read.result.mate, pv: read.result.pv.slice(0, 5) };
}

export interface WhatifAfterCandidateOut {
  /** どの候補を使ったか(0 始まり。実戦が第 1 候補(0)なら第 2 候補(1)を使う)。 */
  candidateIndex: number;
  move: string;
  scoreCp: number | null;
  mate: number | null;
  /** その候補の読み筋どおりに(最大 5 手)進めた局面の SFEN。 */
  sfenAfter: string;
  /** `sfenAfter` を作った最後の手(盤面のハイライトに使う)。 */
  lastMoveUsi: string;
  movesApplied: number;
}

/**
 * 「第 1 候補(実戦が第 1 候補なら第 2 候補)の pv」を、5 手ぶん実際に SFEN へ適用する(計画 §2.3)。
 * その候補が無ければ(実戦 = 第 1 候補で、候補が 1 つしか無い局面)null。pv が空でも null。
 */
export function afterCandidateOf(position: WhatifPositionRow): WhatifAfterCandidateOut | null {
  const c0 = position.candidates[0];
  const candidateIndex = c0 !== undefined && c0.move === position.actualMove ? 1 : 0;
  const candidate = position.candidates[candidateIndex];
  if (candidate === undefined) return null;
  const movesToApply = candidate.pv.slice(0, 5);
  if (movesToApply.length === 0) return null;
  let sfen = position.sfen;
  for (const usi of movesToApply) sfen = applyMove(sfen, usi);
  return {
    candidateIndex,
    move: candidate.move,
    scoreCp: candidate.scoreCp,
    mate: candidate.mate,
    sfenAfter: sfen,
    lastMoveUsi: movesToApply[movesToApply.length - 1]!,
    movesApplied: movesToApply.length,
  };
}

export interface WhatifRepresentativeOut {
  kind: WhatifSceneKind;
  ply: number;
  displayPly: number;
  sfen: string;
  actualMove: string;
  actualRank: number | null;
  /** 実戦の手が候補の中に見つかっていれば、その評価(見つからなければ null。候補には無いことを表す)。 */
  actual: { found: boolean; scoreCp: number | null; mate: number | null };
  topGapCp: number | null;
  candidates: WhatifCandidateOut[];
  scene: { attack: WhatifSideReadOut; defense: WhatifSideReadOut; sideGapCp: number | null } | null;
  afterCandidate: WhatifAfterCandidateOut | null;
}

export function buildRepresentative(pick: RepresentativePick, positions: readonly WhatifPositionRow[], scenesByPly: ReadonlyMap<number, WhatifSceneRow>): WhatifRepresentativeOut {
  const position = positions.find((p) => p.ply === pick.ply);
  if (position === undefined) throw new WhatifReportError(`ply ${pick.ply} の局面が positions に見つからない`);
  const sceneRow = scenesByPly.get(pick.ply) ?? null;
  const actualCandidate = position.candidates.find((c) => c.move === position.actualMove);
  return {
    kind: pick.kind,
    ply: position.ply,
    displayPly: position.displayPly,
    sfen: position.sfen,
    actualMove: position.actualMove,
    actualRank: position.actualRank,
    actual: { found: actualCandidate !== undefined, scoreCp: actualCandidate?.scoreCp ?? null, mate: actualCandidate?.mate ?? null },
    topGapCp: position.topGapCp,
    candidates: position.candidates.slice(0, 3).map(candidateOut),
    scene: sceneRow === null ? null : { attack: sideReadOut(sceneRow.attack), defense: sideReadOut(sceneRow.defense), sideGapCp: sceneRow.sideGapCp },
    afterCandidate: afterCandidateOf(position),
  };
}

// ---- 局ごとの材料 ----

/** patient_report_data.json の games の欄のうち、この段が読む欄だけ(局の一覧・勝敗・side・total・scores/plies)。 */
export interface PatientGameLike {
  id: string;
  side: "先手" | "後手";
  total: number;
  result: "勝ち" | "負け";
  ending: string | null;
  scores: Array<number | null>;
  plies: number[];
}

export interface WhatifReportGameOut {
  gameNo: number;
  id: string;
  side: "先手" | "後手";
  result: "勝ち" | "負け";
  total: number;
  ending: string | null;
  /** scores/plies を人に見せる手数へ直す差(後手の局は 1)。render2.py の `off` と同じ考え方。 */
  plyOffset: number;
  scores: Array<number | null>;
  plies: number[];
  positionsRead: number;
  matchesTop1: number;
  withinMultiPv: number;
  representative: WhatifRepresentativeOut | null;
}

export function buildGameReport(gameNo: number, patient: PatientGameLike, parsed: ParsedWhatifJsonl): WhatifReportGameOut {
  if (patient.id !== parsed.meta.kifuId) throw new WhatifReportError(`patient の id(${patient.id})と whatif.jsonl の kifuId(${parsed.meta.kifuId})が違う`);
  const pick = pickRepresentativePly(patient.result, parsed.positions, parsed.summary);
  const scenesByPly = new Map(parsed.scenes.map((s) => [s.ply, s]));
  const representative = pick === null ? null : buildRepresentative(pick, parsed.positions, scenesByPly);
  return {
    gameNo,
    id: patient.id,
    side: patient.side,
    result: patient.result,
    total: patient.total,
    ending: patient.ending,
    plyOffset: patient.side === "後手" ? 1 : 0,
    scores: patient.scores,
    plies: patient.plies,
    positionsRead: parsed.summary.positionsRead,
    matchesTop1: parsed.summary.matchesTop1,
    withinMultiPv: parsed.summary.withinMultiPv,
    representative,
  };
}

// ---- 1 ページ目の集計(§7.3。消費時間の表はここでは作らない) ----

export interface WhatifReportSummaryOut {
  positionsRead: number;
  matchesTop1: number;
  withinMultiPv: number;
  scenes: {
    fork: number;
    narrowHeld: number;
    chanceHeld: number;
    /** fork + narrowHeld + chanceHeld の延べ数(1 局面が複数種類に当たれば二重に数える)。 */
    rawTotal: number;
    /** 局ごとに fork ∪ narrowHeld ∪ chanceHeld の手数の集合を取り、重なりを除いた数を局をまたいで足したもの。 */
    distinctTotal: number;
  };
  sideCompare: { scenesRead: number; bothFound: number; attackNoLegalMove: number; defenseNoLegalMove: number };
  /** 負けた局のうち、narrowHeld が 1 つ以上あった局の数 / 負けた局の総数。 */
  lossesWithNarrowHeld: { withNarrow: number; lossesTotal: number };
}

export function buildSummary(games: readonly WhatifReportGameOut[], summaries: readonly WhatifSummaryRow[]): WhatifReportSummaryOut {
  if (games.length !== summaries.length) throw new WhatifReportError("games と summaries の数が違う(呼び出し側のバグ)");
  let positionsRead = 0;
  let matchesTop1 = 0;
  let withinMultiPv = 0;
  let fork = 0;
  let narrowHeld = 0;
  let chanceHeld = 0;
  let distinctTotal = 0;
  let scenesRead = 0;
  let bothFound = 0;
  let attackNoLegalMove = 0;
  let defenseNoLegalMove = 0;
  let lossesTotal = 0;
  let withNarrow = 0;
  summaries.forEach((s, index) => {
    positionsRead += s.positionsRead;
    matchesTop1 += s.matchesTop1;
    withinMultiPv += s.withinMultiPv;
    fork += s.scenes.fork.length;
    narrowHeld += s.scenes.narrowHeld.length;
    chanceHeld += s.scenes.chanceHeld.length;
    distinctTotal += new Set([...s.scenes.fork, ...s.scenes.narrowHeld, ...s.scenes.chanceHeld]).size;
    scenesRead += s.sceneReads.scenesRead;
    bothFound += s.sceneReads.bothFoundCount;
    attackNoLegalMove += s.sceneReads.attackNoLegalMoveCount;
    defenseNoLegalMove += s.sceneReads.defenseNoLegalMoveCount;
    const game = games[index]!;
    if (game.result === "負け") {
      lossesTotal += 1;
      if (s.scenes.narrowHeld.length > 0) withNarrow += 1;
    }
  });
  return {
    positionsRead,
    matchesTop1,
    withinMultiPv,
    scenes: { fork, narrowHeld, chanceHeld, rawTotal: fork + narrowHeld + chanceHeld, distinctTotal },
    sideCompare: { scenesRead, bothFound, attackNoLegalMove, defenseNoLegalMove },
    lossesWithNarrowHeld: { withNarrow, lossesTotal },
  };
}

// ---- 全体の組み立て ----

export interface WhatifReportInput {
  id: string;
  /** whatif.jsonl の中身(文字列)。 */
  jsonl: string;
  patient: PatientGameLike;
}

/**
 * 冊子の文(用語の説明・「17 手目より後」等)に出す、判断的知識の値(計画 §2.1 の WHATIF_VALUES の一部)。
 * **固定で書かない**(python 側の文言に埋め込む数は、必ずここ経由でデータから読む)。全局で同じはずなので、
 * 違えば止める(`buildWhatifReportData` が確かめる)。
 */
export interface WhatifReportValues {
  /** 攻め・守りの「玉のそば」の広さ(玉から何マス以内か)。 */
  sideZoneRadius: number;
  /** この手数(1 手目から数えて)から読む。 */
  startPly: number;
  /** 分かれ道(下がった側)を拾う閾値。 */
  minLossCp: number;
  /** 選択肢が限られた局面を拾う閾値(第 1 候補と第 2 候補の差)。 */
  narrowGapCp: number;
  /** 相手の手の後の機会を拾う閾値(評価の上がり)。 */
  riseCp: number;
}

const REPORT_VALUE_KEYS: readonly (keyof WhatifReportValues)[] = ["sideZoneRadius", "startPly", "minLossCp", "narrowGapCp", "riseCp"];

function reportValuesOf(metaList: readonly WhatifMetaRow[]): WhatifReportValues {
  const picked = REPORT_VALUE_KEYS.map((key) => {
    const values = new Set(metaList.map((meta) => meta.values[key]));
    if (values.size !== 1) throw new WhatifReportError(`${key} が局によって違う: ${[...values].join("・")}`);
    return [key, [...values][0]!] as const;
  });
  return Object.fromEntries(picked) as unknown as WhatifReportValues;
}

export interface WhatifReportData {
  gamesCount: number;
  values: WhatifReportValues;
  summary: WhatifReportSummaryOut;
  games: WhatifReportGameOut[];
}

/** 局の一覧(kifuId の昇順)から whatif_report_data.json の中身を組む。 */
export function buildWhatifReportData(inputs: readonly WhatifReportInput[]): WhatifReportData {
  if (inputs.length === 0) throw new WhatifReportError("入力が 0 局");
  const sorted = [...inputs].sort((a, b) => a.id.localeCompare(b.id));
  const parsedList = sorted.map((input) => parseWhatifJsonl(input.jsonl));
  const values = reportValuesOf(parsedList.map((p) => p.meta));
  const games = sorted.map((input, index) => buildGameReport(index + 1, input.patient, parsedList[index]!));
  const summary = buildSummary(games, parsedList.map((p) => p.summary));
  return { gamesCount: games.length, values, summary, games };
}
