// STEP PIPE 作業 B(docs/STEP_PIPE_PLAN_2026-09-21.md §2.2)。S5「記録 → 本人向けの事実」を組む純粋関数。
//
// 【このファイルがやること】
// - 段 2 の記録(replay.ts → rescreen.ts の JSONL)と固定棋譜(kifu-import-check.ts --fixed の JSON)から、
//   凍結した第 6 版テンプレート(scripts/playtest/out/report-template-v6、gitignore・読むだけ)が読む
//   `patient_report_data.json`・`audit_metrics.json` と同じ形の事実だけを組み立てる
// - 既存の lib(lib/failureEvent.ts・lib/diagnosisMoment.ts・lib/standing.ts・lib/gate.ts・lib/condition.ts・
//   lib/sideAlignment.ts・lib/usiRotation.ts・lib/kifuImport.ts)の関数を呼ぶだけで、判定・閾値を新しく置かない
// - 後手の局は、記録が「本人 = 先手に回した」向きになっているので、USI は 180 度回して本人が指した向きへ戻す
//   (lib/usiRotation.ts の rotateUsiMove。固定棋譜の originalMoves と突き合わせて確かめる)
//
// 【このファイルが絶対にやらないこと】
// - ファイルの読み書き(道具 reportData.ts の役目)。エンジンを回すこと
// - 判定的知識(閾値・Gate の値)を新しく置くこと。既存の定数(STANDING_BOUNDS・GATE_VALUES 等)を読むだけ
// - 将棋の判断・断定的な戦法名の表示

import type { MetaLine, RecordLine } from "../invariants/types.js";
import { collapseOf, type CollapseTally } from "./gate.js";
import { baselineTallyOf, type GatePairsGame } from "./gate.js";
import { allPairsOf, type AllPairs } from "./diagnosisMoment.js";
import { DRAFT_RULE_1, diagnoseRecords, STANDING_BOUNDS, readEvaluations, type Evaluation, type FailureEvent } from "./failureEvent.js";
import { totalDiagnosisCounts, type DiagnosisTotals } from "./diagnosisTotals.js";
import { initialSfenOf } from "./sideAlignment.js";
import { rotateUsiMove } from "./usiRotation.js";
import { ENDING_KIF_WORDS, type EndingKind, type FixedKifuEnding, type MoveTime } from "./kifuImport.js";
import { judgeCondition, type ConditionDefinition, type PairRow } from "./condition.js";
import type { GateLine } from "./gateOutput.js";
import { toJapaneseMove } from "../../../apps/server/src/notation/japaneseMove.js";
import { toJapaneseMoveHistory } from "../../../apps/server/src/notation/japaneseMoveHistory.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import { roleToKanji, makeJapaneseSquare } from "shogiops/notation/util";
import { parseUsi, isDrop } from "shogiops/util";
import type { Role } from "shogiops/types";

// ---- 入力の形 ----

/** 固定棋譜(kifu-import-check.ts --fixed の JSON)を読むのに必要な欄だけ。ending が無い固定棋譜もある(古い版・読めなかった等)。 */
export interface FixedKifu {
  id: string;
  ending?: FixedKifuEnding | null;
  moves: readonly string[];
  originalMoves?: readonly string[];
  mirrored?: boolean;
  /**
   * STEP TIME: 元の手順(`originalMovesOf` と同じ並び。KIF の手数 = 添字 + 1)の消費時間。
   * 欄が無い固定棋譜もある(時間を読めなかった KIF・CSA・このステップより前の記録)。
   */
  moveSeconds?: readonly (MoveTime | null)[];
}

export interface GameSource {
  kifuId: string;
  meta: MetaLine;
  records: readonly RecordLine[];
  fixed: FixedKifu;
}

export class ReportDataError extends Error {}

/** 固定棋譜の本人の手順(originalMoves があればそれ、無ければ moves)。 */
export function originalMovesOf(fixed: FixedKifu): readonly string[] {
  return fixed.originalMoves ?? fixed.moves;
}

/** 本人の側(先手・後手)。meta.mirrored が true なら後手(D0-SIDE 段 2)。 */
export function sideOf(meta: Pick<MetaLine, "mirrored">): "先手" | "後手" {
  return meta.mirrored === true ? "後手" : "先手";
}

/** 記録の ply を「本人が指した向き」の手数へ戻す差(mirrored なら plyOffset、無ければ 0)。 */
export function plyOffsetOf(meta: Pick<MetaLine, "mirrored" | "plyOffset">): number {
  return meta.mirrored === true ? (meta.plyOffset ?? 1) : 0;
}

/**
 * 勝ち負け(構造的な事実。将棋の判断ではない)。終局の種類(`ending.kind`)ごとに決め方が違うので、
 * 終局の種類を見ずに手数の偶奇だけで決めない(独立監査 REVISE、2026-09-21)。
 *
 * - **resign・mate・timeUp**(2 人目 20 局の実物にある 3 種。金の標本と突き合わせて確かめた):
 *   最後の手を指した側(手数が奇数なら先手・偶数なら後手)が勝ち。手番の側が「指せず終わった」種類
 *   (投了・詰み・切れ負けはどれも、次に指すはずだった側が指せずに終わる)。
 * - **illegalWin・illegalLoss**: `ending.ply`(= 本人が指した向きの総手数 + 1、次に指すはずだった手の番号)の
 *   手番の側を、語の意味どおりに読む(`illegalWin` ならその側の勝ち、`illegalLoss` ならその側の負け。
 *   推測ではなく `lib/kifuImport.ts` の `ENDING_KIF_WORDS` の語(反則勝ち・反則負け)をそのまま読む)。
 * - **それ以外**(repetition・impasse・abort・defaultWin・defaultLoss・enteringKingWin・noMate・unlisted・
 *   unreadable・ending が無い): この規則(手数の偶奇・ending.ply の手番)では勝敗を決められないので、
 *   黙って偶奇で決めずに例外を投げる。
 */
export function resultOf(side: "先手" | "後手", total: number, ending: FixedKifuEnding | null | undefined, kifuId: string): "勝ち" | "負け" {
  const moverOf = (ply: number): "先手" | "後手" => (ply % 2 === 1 ? "先手" : "後手");
  if (ending === null || ending === undefined) {
    throw new ReportDataError(`${kifuId} に終局の記録(ending)が無いので、勝ち負けを決められない`);
  }
  if (ending.kind === "resign" || ending.kind === "mate" || ending.kind === "timeUp") {
    return moverOf(total) === side ? "勝ち" : "負け";
  }
  if (ending.kind === "illegalWin" || ending.kind === "illegalLoss") {
    const mover = moverOf(ending.ply);
    const winner = ending.kind === "illegalWin" ? mover : mover === "先手" ? "後手" : "先手";
    return winner === side ? "勝ち" : "負け";
  }
  throw new ReportDataError(`${kifuId} の終局の種類(${ending.kind})からは、この規則で勝ち負けを決められない`);
}

/** 終局の種類の日本語(lib/kifuImport.ts の ENDING_KIF_WORDS をそのまま引く。新しい語を作らない)。 */
export function endingTextOf(ending: FixedKifuEnding | null | undefined): string | null {
  if (ending === null || ending === undefined || ending.kind === "unlisted" || ending.kind === "unreadable") return null;
  return ENDING_KIF_WORDS[ending.kind as EndingKind];
}

/**
 * 評価値の表示(金の標本と突き合わせて割り出した規則): measured で scoreCp があればそれ、
 * mate があれば ±3000(符号は mate の符号)。それ以外(未測定・mate 0 など)は null。
 * **3000 は判定に使う値ではなく、折れ線を描くための表示専用の値**(mate 側は 20 局中すべて正で確認、
 * 負の側は実物に無く未確認 ― 報告に明記する)。
 */
export const MATE_DISPLAY_SCORE = 3000;
export function displayScoreOf(evaluation: Evaluation): number | null {
  if (evaluation.state !== "measured") return null;
  if (evaluation.scoreCp !== null) return evaluation.scoreCp;
  if (evaluation.mate !== null && evaluation.mate !== 0) return Math.sign(evaluation.mate) * MATE_DISPLAY_SCORE;
  return null;
}

// ---- games ----

export interface PatientGame {
  no: number;
  id: string;
  side: "先手" | "後手";
  total: number;
  result: "勝ち" | "負け";
  ending: string | null;
  /** その局の Failure Event(急落候補・matedIfPass)の数。 */
  events: number;
  scores: Array<number | null>;
  plies: number[];
  marks: number[];
}

interface BuiltGame {
  source: GameSource;
  initialSfen: string;
  plyOffset: number;
  side: "先手" | "後手";
  originalMoves: readonly string[];
  events: readonly FailureEvent[];
  allPairs: AllPairs;
}

/** 段 2 の記録・固定棋譜から、局ごとに必要な材料を作る(順序は kifuId の昇順に揃える)。 */
export function buildGames(sources: readonly GameSource[]): BuiltGame[] {
  const sorted = [...sources].sort((a, b) => a.kifuId.localeCompare(b.kifuId));
  return sorted.map((source) => {
    if (source.kifuId !== source.fixed.id) {
      throw new ReportDataError(`記録の kifuId(${source.kifuId})と固定棋譜の id(${source.fixed.id})が違う`);
    }
    const initialSfen = initialSfenOf(source.meta);
    const plyOffset = plyOffsetOf(source.meta);
    const side = sideOf(source.meta);
    const originalMoves = originalMovesOf(source.fixed);
    const diag = diagnoseRecords(source.kifuId, source.records, DRAFT_RULE_1, initialSfen);
    const allPairs = allPairsOf(source.kifuId, source.records, DRAFT_RULE_1, initialSfen, diag.events, { source: "light" });
    return { source, initialSfen, plyOffset, side, originalMoves, events: diag.events, allPairs };
  });
}

/** displayPly(本人が指した向きの手数) = 記録の branchPly + plyOffset。 */
export function displayPlyOf(branchPly: number, plyOffset: number): number {
  return branchPly + plyOffset;
}

export function buildPatientGames(games: readonly BuiltGame[]): PatientGame[] {
  return games.map((game, index) => {
    const total = game.originalMoves.length;
    const rows = readEvaluations(game.source.records);
    const scores = rows.map((row) => displayScoreOf(row.evaluation));
    const plies = rows.map((row) => row.ply);
    const dropEvents = game.events.filter((event) => event.branch.kinds.some((kind) => kind !== "matedIfPass"));
    const marks = dropEvents.map((event) => event.fromReadyPly / 2);
    return {
      no: index + 1,
      id: game.source.kifuId,
      side: game.side,
      total,
      result: resultOf(game.side, total, game.source.fixed.ending, game.source.kifuId),
      ending: endingTextOf(game.source.fixed.ending),
      // 「drop」種(急落候補。matedIfPass だけで当たった Failure Event は数えない)の件数。marks と同じ数え方
      events: dropEvents.length,
      scores,
      plies,
      marks,
    };
  });
}

// ---- 指し手の日本語表記(played。best は既存の toJapaneseMove をそのまま使う)----

/**
 * D0-KIFU2 が読みをそろえた短縮形(竜・全・圭・杏)に、書くときも合わせる上書き。
 * shogiops の既定(roleToKanji)は長い形(成香など)と「龍」なので、この 4 つだけ差し替える。
 */
const SHORT_PROMOTED_KANJI: Partial<Record<Role, string>> = {
  promotedlance: "杏",
  promotedknight: "圭",
  promotedsilver: "全",
  dragon: "竜",
  dragonpromoted: "竜",
};

function pieceKanjiOf(role: Role): string {
  return SHORT_PROMOTED_KANJI[role] ?? roleToKanji("standard")(role);
}

/**
 * 「指した手」の日本語表記(本人が指した向き、金の標本と突き合わせて割り出した形)。
 * shogiops の makeJapaneseMoveOrDrop はそのまま使わず(あいまいさの表記 上・引・直 等を出さない代わりに、
 * 盤面の升番号を必ず添える)。同じ升に指した直前の手の升と一致すれば「同」。打つ手は常に「打」を添える。
 */
export function formatPlayedMove(sfenBeforeOriginal: string, moveUsiOriginal: string, previousDestUsi: string | null): string | null {
  const move = parseUsi(moveUsiOriginal);
  if (!move) return null;
  if (isDrop(move)) {
    return `${makeJapaneseSquare(move.to)}${pieceKanjiOf(move.role)}打`;
  }
  const piece = parsePosition(sfenBeforeOriginal).board.get(move.from);
  if (!piece) return null;
  const sameSquare = previousDestUsi !== null && previousDestUsi === moveUsiOriginal.slice(2, 4);
  const destStr = sameSquare ? "同" : makeJapaneseSquare(move.to);
  const promStr = move.promotion ? "成" : "";
  const from = moveUsiOriginal.slice(0, 2);
  const fileDigit = from[0];
  const rankDigit = String(from.charCodeAt(1) - "a".charCodeAt(0) + 1);
  return `${destStr}${pieceKanjiOf(piece.role)}${promStr}(${fileDigit}${rankDigit})`;
}

/** 後手の局の USI(記録は本人 = 先手に回した向き)を、本人が指した向き(原局面)へ戻す。 */
export function toOriginalUsi(fixedUsi: string, mirrored: boolean): string {
  return mirrored ? rotateUsiMove(fixedUsi) : fixedUsi;
}

// ---- events ----

export interface PatientEvent {
  gameNo: number;
  kind: "drop" | "matedIfPass";
  ply: number;
  before: number | null;
  after: number | null;
  played: string | null;
  best: string;
  sameBest: boolean;
  after5: string;
  afterPassMate: number | null;
  playedUsi: string;
  bestUsi: string | null;
}

function after5TextOf(checks: readonly number[], plyOffset: number, windowShort: boolean): string {
  let text: string;
  if (checks.length > 0) {
    text = `${checks.map((ply) => `${ply + plyOffset} 手目`).join("・")}に王手を受けています`;
  } else {
    text = "5 手以内に王手はありませんでした";
  }
  if (windowShort) text += "(棋譜の終わりが近く、5 手ぶんは見られていません)";
  return text;
}

export function buildPatientEvents(games: readonly BuiltGame[]): PatientEvent[] {
  const events: PatientEvent[] = [];
  games.forEach((game, index) => {
    // 本人が指した向きの SFEN 列(全手の直前局面。日本語表記に使う)
    const sfensBefore: string[] = [DEFAULT_INITIAL_SFEN];
    let sfen = DEFAULT_INITIAL_SFEN;
    for (const move of game.originalMoves) sfensBefore.push((sfen = applyMove(sfen, move)));

    for (const event of game.events) {
      const displayPly = displayPlyOf(event.branchPly, game.plyOffset);
      const isDropKind = event.branch.kinds.some((kind) => kind !== "matedIfPass");
      const playedUsiOriginal = game.originalMoves[displayPly - 1];
      if (playedUsiOriginal === undefined) throw new ReportDataError(`${game.source.kifuId} の ${displayPly} 手目が本人の手順に無い`);
      const sfenBeforePlayed = sfensBefore[displayPly - 1]!;
      const previousDest = displayPly - 2 >= 0 ? (game.originalMoves[displayPly - 2]?.slice(2, 4) ?? null) : null;
      const played = formatPlayedMove(sfenBeforePlayed, playedUsiOriginal, previousDest);

      const bestFixedUsi = event.action.bestmoveAtBefore;
      const bestUsiOriginal = bestFixedUsi === null ? null : toOriginalUsi(bestFixedUsi, game.side === "後手");
      const best = bestUsiOriginal === null ? "—" : (toJapaneseMove(sfenBeforePlayed, bestUsiOriginal) ?? "—");
      const sameBest = bestUsiOriginal !== null && bestUsiOriginal === playedUsiOriginal;

      const checks = event.consequences.checks;
      const afterPassMate = event.branch.matedIfPassAfter && event.branch.evaluationAfter.state === "measured" ? event.branch.evaluationAfter.afterPassMate : null;

      events.push({
        gameNo: index + 1,
        kind: isDropKind ? "drop" : "matedIfPass",
        ply: displayPly,
        before: displayScoreOf(event.trigger.evaluationBefore),
        after: displayScoreOf(event.branch.evaluationAfter),
        played,
        best,
        sameBest,
        after5: after5TextOf(checks, game.plyOffset, event.consequences.windowShort),
        afterPassMate,
        playedUsi: playedUsiOriginal,
        bestUsi: bestUsiOriginal,
      });
    }
  });
  return events;
}

// ---- escapeScenes(候補「逃げ道が減る」king_escapes_decrease_v1 の、該当かつ崩れた組)----

function kingEscapesCountOf(escapes: { state: string; count?: number }): number {
  if (escapes.state !== "counted" || escapes.count === undefined) {
    throw new ReportDataError("king_escapes_decrease_v1 が該当したのに逃げ道の数を数えられない局面だった");
  }
  return escapes.count;
}

export interface EscapeScene {
  gameNo: number;
  displayPly: number;
  userMove: string | null;
  opponentMove: string | null;
  before: number | null;
  after: number | null;
  escRoot: number;
  escEnd: number;
  pvEscEnd: number;
}

export function buildEscapeScenes(games: readonly BuiltGame[], kingEscapesDefinition: ConditionDefinition): EscapeScene[] {
  const scenes: EscapeScene[] = [];
  games.forEach((game, index) => {
    // 指し手の履歴としての日本語表記(直前の手の升と同じなら「同」。金の標本と突き合わせて割り出した形で、
    // 「played」(events)の升番号つきの表記とは別 ― _mid.py の disp_move も履歴の表記をそのまま使う)
    const japaneseHistory = toJapaneseMoveHistory([...game.originalMoves], DEFAULT_INITIAL_SFEN);
    for (const pair of game.allPairs.pairs) {
      const judged = judgeCondition(kingEscapesDefinition, { kind: "pair", row: pair });
      if (judged.state !== "match") continue;
      const collapse = collapseOf(pair.standingPair);
      if (!(collapse.counted && collapse.transition !== null)) continue;
      if (pair.counterfactual.state !== "compared") {
        // king_escapes_decrease_v1 は counterfactual.actual.* を使うので、match ならここに来ないはず(念のための歯止め)
        throw new ReportDataError(`${game.source.kifuId} の組 ${pair.branchPly} が該当したのに counterfactual が compared でない`);
      }
      const displayPly = displayPlyOf(pair.branchPly, game.plyOffset);
      scenes.push({
        gameNo: index + 1,
        displayPly,
        userMove: japaneseHistory[displayPly - 1] ?? null,
        opponentMove: japaneseHistory[displayPly] ?? null,
        before: displayScoreOf(pair.trigger.evaluationBefore),
        after: displayScoreOf(pair.evaluationAfter),
        escRoot: kingEscapesCountOf(pair.counterfactual.kingEscapesRoot),
        escEnd: kingEscapesCountOf(pair.counterfactual.actual.kingEscapesEnd),
        pvEscEnd: kingEscapesCountOf(pair.counterfactual.pv.kingEscapesEnd),
      });
    }
  });
  return scenes;
}

// ---- overview ----

export interface MoveCheckOverview {
  n: number;
  fell: number;
  games: number;
  otherN: number;
  otherFell: number;
}

export interface PatientOverview {
  fell: number;
  early: number;
  mid: number;
  late: number;
  fromAhead: number;
  fromAheadLoss: number;
  moveCheck: MoveCheckOverview | null;
}

/**
 * 崩れた組(前が ahead・level、直後に区分が 1 段下がった)を、局ごとの「1/3・2/3」で早い・中・遅いに分ける
 * (`_head.py` の phase() と同じ考え方。ここでは組の `branchPly`(本人の向きへ戻す前の値)を、
 * 本人が指した向きの総手数と比べる ― 金の標本に一致する式として割り出した。報告に割り出しの根拠を書く)。
 */
export function phaseOf(branchPlyNoOffset: number, total: number): "early" | "mid" | "late" {
  const fraction = branchPlyNoOffset / total;
  if (fraction < 1 / 3) return "early";
  if (fraction < 2 / 3) return "mid";
  return "late";
}

interface FellPair {
  gameNo: number;
  before: "ahead" | "level";
  win: boolean;
}

function fellPairsOf(games: readonly BuiltGame[], patientGames: readonly PatientGame[]): FellPair[] {
  const rows: FellPair[] = [];
  games.forEach((game, index) => {
    const patientGame = patientGames[index]!;
    for (const pair of game.allPairs.pairs) {
      const collapse = collapseOf(pair.standingPair);
      if (collapse.counted && collapse.transition !== null) {
        rows.push({ gameNo: index + 1, before: collapse.before, win: patientGame.result === "勝ち" });
      }
    }
  });
  return rows;
}

export function buildOverview(games: readonly BuiltGame[], patientGames: readonly PatientGame[], moveCheck: MoveCheckOverview | null): PatientOverview {
  const fell = fellPairsOf(games, patientGames);
  let early = 0;
  let mid = 0;
  let late = 0;
  games.forEach((game, index) => {
    const total = patientGames[index]!.total;
    for (const pair of game.allPairs.pairs) {
      const collapse = collapseOf(pair.standingPair);
      if (!(collapse.counted && collapse.transition !== null)) continue;
      const phase = phaseOf(pair.branchPly, total);
      if (phase === "early") early += 1;
      else if (phase === "mid") mid += 1;
      else late += 1;
    }
  });
  const fromAhead = fell.filter((row) => row.before === "ahead");
  const fromAheadLoss = fromAhead.filter((row) => !row.win).length;
  return { fell: fell.length, early, mid, late, fromAhead: fromAhead.length, fromAheadLoss, moveCheck };
}

/** gate.jsonl の 1 行(condition.id が一致するもの)から overview.moveCheck を組む(G-1・G-2・G-4 の値。CLAUDE.md 4 番: 判定・閾値は読むだけ)。 */
export function moveCheckFromGateLines(gateLines: readonly GateLine[], conditionId: string): MoveCheckOverview | null {
  const line = gateLines.find((entry) => entry.condition.id === conditionId);
  if (line === undefined || !("items" in line.gate)) return null;
  const g1 = line.gate.items.find((item) => item.item === "G-1");
  const g2 = line.gate.items.find((item) => item.item === "G-2");
  const g4 = line.gate.items.find((item) => item.item === "G-4");
  if (g1 === undefined || g2 === undefined || g4 === undefined) return null;
  return {
    n: g2.values["trueDenominator"] as number,
    fell: g2.values["trueCollapsed"] as number,
    games: g1.values["gamesWithTrueDenominator"] as number,
    otherN: g4.values["testTruePairsDenominator"] as number,
    otherFell: g4.values["testTrueCollapsed"] as number,
  };
}

// ---- time(STEP TIME 作業 1。docs/STEP_TIME_PLAN_2026-09-22.md §6.1 の 2。消費時間の事実だけを組む) ----
//
// - `fixed.moveSeconds`(元の手順の順。KIF の手数 = 添字 + 1)を、既存の `game.allPairs.pairs`(collapseOf で数える
//   「組」と同じ分母)・`originalMovesOf` と突き合わせる。新しい判定的知識(閾値)は置かず、`TIME_VALUES` の 1 か所にまとめる
//   (値は docs/STEP_TIME_PLAN_2026-09-22.md §4 の校正の表と同じ)。
// - 1 局でも `moveSeconds` が無ければ(比較対象の棋譜など)、`available: false` にして他の欄を全部 null にする
//   (一部だけ出して比べられるように見せない)。

/** 判定的な値は 1 か所に(CLAUDE.md 4 番)。値は docs/STEP_TIME_PLAN_2026-09-22.md §4 の校正の表と同じ。 */
export const TIME_VALUES = {
  /** 0〜1 / 2〜4 / 5〜9 / 10 以上(4 段)の境目。 */
  spentBucketsSec: [1, 4, 9] as const,
  /** 60 未満 / 60〜119 / 120 以上(3 段)の境目。 */
  leftBucketsSec: [60, 120] as const,
  /** 「直前の自分の手」が長考だったとみなす下限(以上)。 */
  longThinkSec: 10,
  /** 長考の直後の手が「速い」とみなす上限(以下)。 */
  quickSec: 4,
} as const;

export function spentBucketIndexOf(spentSec: number): number {
  const [b0, b1, b2] = TIME_VALUES.spentBucketsSec;
  if (spentSec <= b0) return 0;
  if (spentSec <= b1) return 1;
  if (spentSec <= b2) return 2;
  return 3;
}

export function leftBucketIndexOf(leftSec: number): number {
  const [b0, b1] = TIME_VALUES.leftBucketsSec;
  if (leftSec < b0) return 0;
  if (leftSec < b1) return 1;
  return 2;
}

/** 小数第 1 位までの四捨五入(collect.py の round(x, 1) と同じ丸め方の意図。負の値は扱わない)。 */
function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

/** 中央値(件数が偶数なら中央 2 件の平均。Python の statistics.median と同じ)。空配列は呼ばない。 */
function medianOf(values: readonly number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1]! + sorted[mid]!) / 2 : sorted[mid]!;
}

/**
 * `fixed.moveSeconds` を読む(無ければ null)。`originalMovesOf` と長さが違えば例外(黙って一部だけ読まない)。
 */
export function moveSecondsOf(fixed: FixedKifu): readonly (MoveTime | null)[] | null {
  if (fixed.moveSeconds === undefined) return null;
  const originalMoves = originalMovesOf(fixed);
  if (fixed.moveSeconds.length !== originalMoves.length) {
    throw new ReportDataError(`${fixed.id} の moveSeconds の長さ(${fixed.moveSeconds.length})が moves(${originalMoves.length})と違う`);
  }
  return fixed.moveSeconds;
}

/** 本人が指した側の手番(KIF の手数の偶奇。先手なら奇数、後手なら偶数)。 */
function ownParityOf(side: "先手" | "後手"): 0 | 1 {
  return side === "先手" ? 1 : 0;
}

/** 本人が指した手の消費時間だけを、KIF の手数の昇順で並べる(秒が無い手は含めない)。 */
function ownMoveTimesOf(game: BuiltGame, seconds: readonly (MoveTime | null)[]): Array<{ kifPly: number; time: MoveTime }> {
  const parity = ownParityOf(game.side);
  const out: Array<{ kifPly: number; time: MoveTime }> = [];
  seconds.forEach((time, index) => {
    const kifPly = index + 1;
    if (kifPly % 2 !== parity || time === null) return;
    out.push({ kifPly, time });
  });
  return out;
}

export interface TimeBucket {
  /** その段に当てはまる組の数(分母は既存の崩れの組 counted と同じ)。 */
  n: number;
  /** そのうち崩れた組の数。 */
  collapsed: number;
}

function emptyBucket(): TimeBucket {
  return { n: 0, collapsed: 0 };
}

/** `game.allPairs.pairs` のうち「組(counted)」だけを、崩れたかどうかと一緒に返す(fellPairsOf と同じ数え方)。 */
function countedPairsOf(game: BuiltGame): Array<{ pair: PairRow; collapsed: boolean }> {
  const out: Array<{ pair: PairRow; collapsed: boolean }> = [];
  for (const pair of game.allPairs.pairs) {
    const collapse = collapseOf(pair.standingPair);
    if (collapse.counted) out.push({ pair, collapsed: collapse.transition !== null });
  }
  return out;
}

export interface PerMoveTimeStats {
  /** 本人の手の総数(件数)。 */
  moves: number;
  median: number;
  mean: number;
  /** 10 秒以上の割合(%、小数第 1 位)。 */
  ge10: number;
  /** 30 秒以上の割合(%、小数第 1 位)。 */
  ge30: number;
  /** 0〜1 秒の割合(%、小数第 1 位)。 */
  le1: number;
  /** 1 局あたりの消費(本人の手の合計)の中央値。 */
  gameMedian: number;
}

function buildPerMoveTimeStats(games: readonly BuiltGame[], secondsByGame: ReadonlyMap<string, readonly (MoveTime | null)[]>): PerMoveTimeStats {
  const perGameTotals: number[] = [];
  const allSpent: number[] = [];
  for (const game of games) {
    const own = ownMoveTimesOf(game, secondsByGame.get(game.source.kifuId)!);
    perGameTotals.push(own.reduce((sum, m) => sum + m.time.spentSec, 0));
    for (const m of own) allSpent.push(m.time.spentSec);
  }
  const n = allSpent.length;
  return {
    moves: n,
    median: medianOf(allSpent),
    mean: round1(allSpent.reduce((a, b) => a + b, 0) / n),
    ge10: round1((100 * allSpent.filter((s) => s >= 10).length) / n),
    ge30: round1((100 * allSpent.filter((s) => s >= 30).length) / n),
    le1: round1((100 * allSpent.filter((s) => s <= 1).length) / n),
    gameMedian: medianOf(perGameTotals),
  };
}

/** 4 段(spentBucketIndexOf)× {組の数, 崩れ}。その手(組の branchPly)にかけた時間で振り分ける。 */
function buildBySpent(games: readonly BuiltGame[], secondsByGame: ReadonlyMap<string, readonly (MoveTime | null)[]>): TimeBucket[] {
  const buckets: TimeBucket[] = [emptyBucket(), emptyBucket(), emptyBucket(), emptyBucket()];
  for (const game of games) {
    const seconds = secondsByGame.get(game.source.kifuId)!;
    for (const { pair, collapsed } of countedPairsOf(game)) {
      const displayPly = displayPlyOf(pair.branchPly, game.plyOffset);
      const time = seconds[displayPly - 1];
      if (time === undefined || time === null) continue;
      const bucket = buckets[spentBucketIndexOf(time.spentSec)]!;
      bucket.n += 1;
      if (collapsed) bucket.collapsed += 1;
    }
  }
  return buckets;
}

export interface PatientAfterLongThink {
  /** 「直前の自分の手が longThinkSec 秒以上で、この手は quickSec 秒以下」× {組の数, 崩れ}。 */
  quickAfterLongThink: TimeBucket;
  /** 「直前の自分の手が longThinkSec 秒以上」(この手の時間は問わない)× {組の数, 崩れ}。 */
  afterLongThinkAny: TimeBucket;
}

/** 「直前の自分の手」= 2 手前(本人の前の手番。KIF の手数で displayPly − 2)。 */
function buildAfterLongThink(games: readonly BuiltGame[], secondsByGame: ReadonlyMap<string, readonly (MoveTime | null)[]>): PatientAfterLongThink {
  const quickAfterLongThink = emptyBucket();
  const afterLongThinkAny = emptyBucket();
  for (const game of games) {
    const seconds = secondsByGame.get(game.source.kifuId)!;
    for (const { pair, collapsed } of countedPairsOf(game)) {
      const displayPly = displayPlyOf(pair.branchPly, game.plyOffset);
      const prevOwnKifPly = displayPly - 2;
      if (prevOwnKifPly < 1) continue; // 直前の自分の手が無い(本人の最初の手)
      const prevOwn = seconds[prevOwnKifPly - 1];
      if (prevOwn === undefined || prevOwn === null || prevOwn.spentSec < TIME_VALUES.longThinkSec) continue;
      afterLongThinkAny.n += 1;
      if (collapsed) afterLongThinkAny.collapsed += 1;
      const thisTime = seconds[displayPly - 1];
      if (thisTime === undefined || thisTime === null || thisTime.spentSec > TIME_VALUES.quickSec) continue;
      quickAfterLongThink.n += 1;
      if (collapsed) quickAfterLongThink.collapsed += 1;
    }
  }
  return { quickAfterLongThink, afterLongThinkAny };
}

/** 3 段(leftBucketIndexOf)× {組の数, 崩れ}。残り = 持ち時間 − それまでの本人の消費の合計(この手より前、spentSec の和)。 */
function buildByLeft(games: readonly BuiltGame[], secondsByGame: ReadonlyMap<string, readonly (MoveTime | null)[]>, timeLimitSec: number): TimeBucket[] {
  const buckets: TimeBucket[] = [emptyBucket(), emptyBucket(), emptyBucket()];
  for (const game of games) {
    const seconds = secondsByGame.get(game.source.kifuId)!;
    const parity = ownParityOf(game.side);
    // KIF の手数 → それより前の本人の消費の合計(累積和。この手そのものは含めない)。
    const usedBefore = new Map<number, number>();
    let cumulative = 0;
    for (let kifPly = parity === 1 ? 1 : 2; kifPly <= seconds.length; kifPly += 2) {
      usedBefore.set(kifPly, cumulative);
      const time = seconds[kifPly - 1];
      if (time !== null && time !== undefined) cumulative += time.spentSec;
    }
    for (const { pair, collapsed } of countedPairsOf(game)) {
      const displayPly = displayPlyOf(pair.branchPly, game.plyOffset);
      const used = usedBefore.get(displayPly);
      if (used === undefined) continue; // この組の手が本人の手でない(起きないはずだが念のため)
      const left = timeLimitSec - used;
      const bucket = buckets[leftBucketIndexOf(left)]!;
      bucket.n += 1;
      if (collapsed) bucket.collapsed += 1;
    }
  }
  return buckets;
}

/** 序盤・中盤・終盤(phaseOf)ごとの、本人の消費(spentSec)の合計。 */
function phaseSpentOfGame(game: BuiltGame, seconds: readonly (MoveTime | null)[], total: number): { early: number; mid: number; late: number } {
  const parity = ownParityOf(game.side);
  const sums = { early: 0, mid: 0, late: 0 };
  for (let kifPly = parity === 1 ? 1 : 2; kifPly <= seconds.length; kifPly += 2) {
    const time = seconds[kifPly - 1];
    if (time === null || time === undefined) continue;
    const recordPly = kifPly - game.plyOffset;
    sums[phaseOf(recordPly, total)] += time.spentSec;
  }
  return sums;
}

export interface PhaseSpentGroup {
  /** この組に入る局の数。0 局なら中央値は 0(局が無いという事実のまま。CLAUDE.md 4 番: 新しい閾値は置かない)。 */
  games: number;
  early: number;
  mid: number;
  late: number;
}

export interface PatientPhaseSpent {
  /** 本人が時間で負けた局(ending.kind === "timeUp" かつ本人の結果が「負け」。相手が切れ負けた勝ちの局は otherGames)。 */
  timeUpLoss: PhaseSpentGroup;
  /** それ以外の局。 */
  otherGames: PhaseSpentGroup;
}

function phaseSpentGroupOf(rows: ReadonlyArray<{ early: number; mid: number; late: number }>): PhaseSpentGroup {
  if (rows.length === 0) return { games: 0, early: 0, mid: 0, late: 0 };
  return {
    games: rows.length,
    early: medianOf(rows.map((r) => r.early)),
    mid: medianOf(rows.map((r) => r.mid)),
    late: medianOf(rows.map((r) => r.late)),
  };
}

/**
 * 本人が時間で負けた局か(ending.kind === "timeUp" かつ本人の結果が「負け」。既存の resultOf・buildPatientGames と
 * 同じ判定を使い回す。司令塔の指示、2026-09-23: 「使い切った」は本人が負けた側の意味)。
 * 相手が切れ負けた(本人が勝った)局は含めない。
 */
function isTimeUpLoss(fixedEnding: FixedKifuEnding | null | undefined, result: "勝ち" | "負け"): boolean {
  return fixedEnding?.kind === "timeUp" && result === "負け";
}

function buildPhaseSpent(
  games: readonly BuiltGame[],
  patientGames: readonly PatientGame[],
  secondsByGame: ReadonlyMap<string, readonly (MoveTime | null)[]>,
): PatientPhaseSpent {
  const timeUpLossRows: Array<{ early: number; mid: number; late: number }> = [];
  const otherRows: Array<{ early: number; mid: number; late: number }> = [];
  games.forEach((game, index) => {
    const total = patientGames[index]!.total;
    const sums = phaseSpentOfGame(game, secondsByGame.get(game.source.kifuId)!, total);
    (isTimeUpLoss(game.source.fixed.ending, patientGames[index]!.result) ? timeUpLossRows : otherRows).push(sums);
  });
  return { timeUpLoss: phaseSpentGroupOf(timeUpLossRows), otherGames: phaseSpentGroupOf(otherRows) };
}

export interface TimeUpGame {
  gameNo: number;
  total: number;
  /** 本人の消費の合計(その局で読めた最後の本人の手の totalSec。累積の時計の値であり、spentSec の和ではない)。 */
  usedSec: number;
  /** 最後に読んだ局面の評価(displayScoreOf。読めていなければ null)。 */
  finalScore: number | null;
}

/** 本人が時間で負けた局(isTimeUpLoss)だけを対象にする(司令塔の指示、2026-09-23)。 */
function buildTimeUpLosses(
  games: readonly BuiltGame[],
  patientGames: readonly PatientGame[],
  secondsByGame: ReadonlyMap<string, readonly (MoveTime | null)[]>,
): TimeUpGame[] {
  const out: TimeUpGame[] = [];
  games.forEach((game, index) => {
    if (!isTimeUpLoss(game.source.fixed.ending, patientGames[index]!.result)) return;
    const own = ownMoveTimesOf(game, secondsByGame.get(game.source.kifuId)!);
    const usedSec = own.reduce((max, m) => Math.max(max, m.time.totalSec), 0);
    const measured = readEvaluations(game.source.records).filter((row) => row.evaluation.state === "measured");
    const last = measured[measured.length - 1];
    out.push({ gameNo: patientGames[index]!.no, total: patientGames[index]!.total, usedSec, finalScore: last === undefined ? null : displayScoreOf(last.evaluation) });
  });
  return out;
}

export interface PatientTime {
  /** 1 局でも消費時間を読めていなければ false(このときは他の欄を全部 null にする。比較対象の棋譜など)。 */
  available: boolean;
  perMove: PerMoveTimeStats | null;
  bySpent: TimeBucket[] | null;
  afterLongThink: PatientAfterLongThink | null;
  /** `--time-limit-sec` が渡されなければ null(持ち時間が分からないと「残り」を出せない)。 */
  byLeft: TimeBucket[] | null;
  phaseSpent: PatientPhaseSpent | null;
  /** 本人が時間で負けた局(ending.kind === "timeUp" かつ本人の結果が「負け」)だけ。相手が切れ負けた勝ちの局は入らない。 */
  timeUpLosses: TimeUpGame[] | null;
}

const EMPTY_PATIENT_TIME: PatientTime = { available: false, perMove: null, bySpent: null, afterLongThink: null, byLeft: null, phaseSpent: null, timeUpLosses: null };

export function buildPatientTime(games: readonly BuiltGame[], patientGames: readonly PatientGame[], timeLimitSec: number | undefined): PatientTime {
  const secondsByGame = new Map<string, readonly (MoveTime | null)[]>();
  for (const game of games) {
    const seconds = moveSecondsOf(game.source.fixed);
    if (seconds === null) return EMPTY_PATIENT_TIME;
    secondsByGame.set(game.source.kifuId, seconds);
  }
  return {
    available: true,
    perMove: buildPerMoveTimeStats(games, secondsByGame),
    bySpent: buildBySpent(games, secondsByGame),
    afterLongThink: buildAfterLongThink(games, secondsByGame),
    byLeft: timeLimitSec === undefined ? null : buildByLeft(games, secondsByGame, timeLimitSec),
    phaseSpent: buildPhaseSpent(games, patientGames, secondsByGame),
    timeUpLosses: buildTimeUpLosses(games, patientGames, secondsByGame),
  };
}

// ---- findings(STEP TIME 作業 2。docs/STEP_TIME_PLAN_2026-09-22.md §6.4 の 1)。
// 発見の判定はここ(TypeScript・試験できる側)で行う。python(report-pdf/render_front.py)は描くだけ。
// 「考えられること」「次の 20 局で見分けがつくこと」の固定文(§5)は作業 3(人間の承認の後)なので、ここでは数の文だけを作る。

/** 種類は固定の一覧(数える前に書く。増やすのは計画 → 監査。docs/STEP_TIME_PLAN_2026-09-22.md §6.4 の 1 の表の順)。 */
export type FindingKind = "timeSpent" | "timeUpLoss" | "aheadLoss" | "phase" | "none";

/** 発見 1 件。`shown: false` の発見も JSON には書く(数つき。前回との比較に使う)。文の中の数はすべて `numbers` から作る。 */
export interface Finding {
  kind: FindingKind;
  shown: boolean;
  numbers: Record<string, number | null>;
  text: string;
}

/** 判定的な値は 1 か所に(CLAUDE.md 4 番)。値は docs/STEP_TIME_PLAN_2026-09-22.md §6.4 の 1 の表のとおり。 */
export const FINDING_VALUES = {
  /** timeSpent(T1): 10 秒以上の組がこの数以上でなければ出さない。 */
  minPairs: 20,
  /** timeSpent(T1): 10 秒以上の崩れ率が、0〜1 秒の崩れ率のこの倍以上でなければ出さない。 */
  ratio: 2,
} as const;

function timeSpentFinding(time: PatientTime): Finding {
  const kind: FindingKind = "timeSpent";
  if (!time.available || time.bySpent === null) {
    return {
      kind,
      shown: false,
      numbers: { a: null, b: null, p: null, c: null, d: null, q: null },
      text: "10 秒以上かけた手は — / —(—%)が崩れ、0〜1 秒の手は — / —(—%)でした",
    };
  }
  const ge10 = time.bySpent[3]!;
  const le1 = time.bySpent[0]!;
  const p = ge10.n === 0 ? null : percentOf(ge10.collapsed, ge10.n);
  const q = le1.n === 0 ? null : percentOf(le1.collapsed, le1.n);
  // 分数の比較は掛け算で行う(浮動小数点の丸め誤差を避ける)。0〜1 秒の分母が 0 なら比べる相手が無いので出さない。
  const shown = ge10.n >= FINDING_VALUES.minPairs && le1.n > 0 && ge10.collapsed * le1.n >= le1.collapsed * FINDING_VALUES.ratio * ge10.n;
  const text = `10 秒以上かけた手は ${ge10.collapsed} / ${ge10.n}(${p ?? "—"}%)が崩れ、0〜1 秒の手は ${le1.collapsed} / ${le1.n}(${q ?? "—"}%)でした`;
  return { kind, shown, numbers: { a: ge10.collapsed, b: ge10.n, p, c: le1.collapsed, d: le1.n, q }, text };
}

function timeUpLossFinding(time: PatientTime): Finding {
  const kind: FindingKind = "timeUpLoss";
  if (!time.available || time.timeUpLosses === null) {
    return { kind, shown: false, numbers: { n: null, m: null }, text: "持ち時間を使い切って負けた — 局のうち、最後の局面の評価が +300 以上だったのは — 局でした" };
  }
  const n = time.timeUpLosses.length;
  // m: 最後に読んだ局面の評価が +300 以上(displayScoreOf は詰みを ±3000 で表すので、本人側の詰みもここへ自動的に入る)。
  const m = time.timeUpLosses.filter((game) => game.finalScore !== null && game.finalScore >= 300).length;
  const text = `持ち時間を使い切って負けた ${n} 局のうち、最後の局面の評価が +300 以上だったのは ${m} 局でした`;
  return { kind, shown: n >= 1, numbers: { n, m }, text };
}

function aheadLossFinding(overview: PatientOverview): Finding {
  const kind: FindingKind = "aheadLoss";
  const n = overview.fromAheadLoss;
  const k = overview.fromAhead;
  const text = `一度は優勢(+300 以上)になった後に負けた対局が ${n} 局ありました(優勢になった対局は ${k} 局)`;
  return { kind, shown: n >= 1, numbers: { n, k }, text };
}

function phaseFinding(overview: PatientOverview): Finding {
  const kind: FindingKind = "phase";
  const { fell, early, mid, late } = overview;
  const text = `崩れ ${fell} 回のうち、序盤 ${early}・中盤 ${mid}・終盤 ${late} でした`;
  // 計画の文どおり「つねに出す。判定なし」(崩れ 0 回でも出す。docs/STEP_TIME_PLAN_2026-09-22.md §6.4 の 1 の表)。
  return { kind, shown: true, numbers: { fell, early, mid, late }, text };
}

function noneFinding(gamesCount: number, othersShown: boolean): Finding {
  const kind: FindingKind = "none";
  const text = `時間と形勢の動きについて、この ${gamesCount} 局では上に書ける数はありませんでした`;
  return { kind, shown: !othersShown, numbers: { games: gamesCount }, text };
}

/** 発見の判定(本編 4 ページの材料)。種類の順は固定(上の表の順のまま)。 */
export function buildFindings(overview: PatientOverview, time: PatientTime, gamesCount: number): Finding[] {
  const timeSpent = timeSpentFinding(time);
  const timeUpLoss = timeUpLossFinding(time);
  const aheadLoss = aheadLossFinding(overview);
  const phase = phaseFinding(overview);
  const none = noneFinding(gamesCount, timeSpent.shown || timeUpLoss.shown || aheadLoss.shown);
  return [timeSpent, timeUpLoss, aheadLoss, phase, none];
}

// ---- previous(前回との比較。docs/STEP_TIME_PLAN_2026-09-22.md §6.4 の 2。`--previous <前回の patient_report_data.json>`) ----

export interface PreviousFindingComparison {
  kind: FindingKind;
  shownBefore: boolean;
  shownNow: boolean;
  numbersBefore: Record<string, number | null>;
  numbersNow: Record<string, number | null>;
}

export interface PatientPrevious {
  games: number;
  findings: PreviousFindingComparison[];
}

/** `--previous` を渡したときだけ組む(無ければ null。python は「初回のため、前回との比較はありません」を出す)。 */
export function buildPrevious(previous: Pick<PatientReportData, "summary" | "findings"> | null, currentFindings: readonly Finding[]): PatientPrevious | null {
  if (previous === null) return null;
  const byKind = new Map(previous.findings.map((finding) => [finding.kind, finding]));
  const findings = currentFindings.map((now) => {
    const before = byKind.get(now.kind);
    if (before === undefined) throw new ReportDataError(`--previous の findings に ${now.kind} が無い(道具のバージョンが違う可能性がある)`);
    return { kind: now.kind, shownBefore: before.shown, shownNow: now.shown, numbersBefore: before.numbers, numbersNow: now.numbers };
  });
  return { games: previous.summary.games, findings };
}

// ---- patient_report_data.json ----

export interface PatientReportData {
  title: string;
  person: string;
  today: string;
  summary: { games: number };
  games: PatientGame[];
  events: PatientEvent[];
  overview: PatientOverview;
  escapeScenes: EscapeScene[];
  time: PatientTime;
  /** STEP TIME 作業 2(§6.4 の 1)。 */
  findings: Finding[];
  /** STEP TIME 作業 2(§6.4 の 2)。`--previous` を渡さなければ null。 */
  previous: PatientPrevious | null;
}

/** 本人向けの側に出してはならない開発用の語(split_data.py の見張りと同じ)。 */
const FORBIDDEN_PATIENT_WORDS = ["G-1", "G-2", "G-3", "G-4", "gate", "sha", "nodes", "gitHead", "definition"] as const;

export function assertNoForbiddenWords(patient: PatientReportData): void {
  const blob = JSON.stringify(patient);
  for (const word of FORBIDDEN_PATIENT_WORDS) {
    if (blob.includes(word)) throw new ReportDataError(`本人向けのデータに開発用の語が入っている: ${word}`);
  }
}

export interface BuildPatientReportDataOptions {
  title: string;
  person: string;
  today: string;
  kingEscapesConditionId: string;
  moveCheckConditionId: string;
  /** STEP TIME: `byLeft`(残り時間)を出すための持ち時間(秒)。渡さなければ `time.byLeft` は null。 */
  timeLimitSec?: number;
  /** STEP TIME 作業 2(§6.4 の 2)。前回の `patient_report_data.json`(`summary`・`findings` だけ読む)。渡さなければ `previous` は null。 */
  previous?: Pick<PatientReportData, "summary" | "findings"> | null;
}

export function buildPatientReportData(
  sources: readonly GameSource[],
  gateLines: readonly GateLine[],
  kingEscapesDefinition: ConditionDefinition,
  options: BuildPatientReportDataOptions,
): PatientReportData {
  const games = buildGames(sources);
  const patientGames = buildPatientGames(games);
  const events = buildPatientEvents(games);
  const escapeScenes = buildEscapeScenes(games, kingEscapesDefinition);
  const moveCheck = moveCheckFromGateLines(gateLines, options.moveCheckConditionId);
  const overview = buildOverview(games, patientGames, moveCheck);
  const time = buildPatientTime(games, patientGames, options.timeLimitSec);
  const findings = buildFindings(overview, time, patientGames.length);
  const previous = buildPrevious(options.previous ?? null, findings);
  const patient: PatientReportData = {
    title: options.title,
    person: options.person,
    today: options.today,
    summary: { games: patientGames.length },
    games: patientGames,
    events,
    overview,
    escapeScenes,
    time,
    findings,
    previous,
  };
  assertNoForbiddenWords(patient);
  return patient;
}

// ---- audit_metrics.json(技術資料の側。別冊の道具 _app.py・_tail.py が読む欄を満たす。best effort) ----

export interface AuditSummary {
  games: number;
  events: number;
  matedIfPassOnly: number;
  fromAdvantage: number;
  withChecks: number;
  cause1: number;
}

/** lib/diagnosisTotals.ts の合計から、audit_metrics.json の summary の欄を埋める。 */
export function auditSummaryFromTotals(totals: DiagnosisTotals, games: number, events: readonly PatientEvent[]): AuditSummary {
  const drop = events.filter((event) => event.kind === "drop");
  const matedIfPassOnly = events.length - drop.length;
  const counts = totals.counts;
  return {
    games,
    events: drop.length,
    matedIfPassOnly,
    fromAdvantage: counts?.fromAdvantage ?? 0,
    withChecks: counts?.withCheck ?? 0,
    cause1: counts?.cause1Draft ?? 0,
  };
}

export interface AuditPairs {
  total: number;
  fell: number;
  den: number;
  aheadToLevel: number;
  levelToBehind: number;
  aheadToBehind: number;
  behindExcluded: number;
  beforeUndet: number;
  afterUndet: number;
  fromAhead: [number, number];
  fromLevel: [number, number];
  win5: [number, number];
  windowShort: number;
  gamesWithFall: number;
  games: number;
  gateCode: string | null;
  conditions: number;
}

/** `_app.py` が読む欄の名前(`pr[...]`)に合わせて、lib/gate.ts の CollapseTally を並べ替える(値は baselineTallyOf のまま。新しい集計はしない)。 */
export function buildAuditPairs(games: readonly BuiltGame[], gitHead: string | null, conditionsInDir: number): AuditPairs {
  const gatePairsGames: GatePairsGame[] = games.map((game) => ({
    kifuId: game.source.kifuId,
    pairs: game.allPairs.pairs,
    movesMissing: game.allPairs.movesMissing,
    rowStandings: game.allPairs.rowStandings,
  }));
  const baseline = baselineTallyOf(gatePairsGames);
  const all = baseline.all;
  return {
    total: all.pairs,
    fell: all.collapsed,
    den: all.denominator,
    aheadToLevel: all.transitions.aheadToLevel,
    levelToBehind: all.transitions.levelToBehind,
    aheadToBehind: all.transitions.aheadToBehind,
    behindExcluded: all.excluded.cannotFall,
    beforeUndet: all.excluded.beforeUndetermined,
    afterUndet: all.excluded.afterUndetermined,
    fromAhead: [all.byBefore.ahead.collapsed, all.byBefore.ahead.denominator],
    fromLevel: [all.byBefore.level.collapsed, all.byBefore.level.denominator],
    win5: [all.within5.dropped, all.within5.denominator],
    windowShort: all.within5.excluded.windowShort,
    gamesWithFall: all.gamesWithCollapse,
    games: baseline.games,
    gateCode: gitHead === null ? null : gitHead.slice(0, 7),
    conditions: conditionsInDir,
  };
}

export function totalDiagnosisCountsOf(games: readonly BuiltGame[]): DiagnosisTotals {
  const rows = games.map((game) => {
    const diag = diagnoseRecords(game.source.kifuId, game.source.records, DRAFT_RULE_1, game.initialSfen);
    return { kifuId: game.source.kifuId, meta: game.source.meta, result: { kind: "counted" as const, counts: diag.counts, events: diag.events } };
  });
  return totalDiagnosisCounts(rows);
}

// ---- audit_metrics.json の candidate(別冊 _app.py が読む欄。gate.jsonl と条件式の定義から組む。best effort) ----

export interface AuditCandidatePhase {
  early: number;
  mid: number;
  late: number;
  fromAhead: number;
  fromAheadLoss: number;
  dropEarly: number;
  dropMid: number;
  dropLate: number;
}

export interface AuditCandidate {
  id: string;
  label: string;
  readableText: string | undefined;
  definitionText: string;
  verdict: string;
  meets: boolean;
  tn: number;
  tc: number;
  tnGames: number;
  tTotal: number;
  fn: number;
  fc: number;
  und: number;
  tPct: number;
  fPct: number;
  byBefore: CollapseTally["byBefore"];
  fByBefore: CollapseTally["byBefore"];
  pv: unknown;
  test: { games: number; tn: number; tc: number; fn: number; fc: number };
  gate: Array<{ id: string; name: string; value: string; threshold: string; met: boolean; reason: string }>;
  reps: EscapeScene[];
  sha: string;
  phase: AuditCandidatePhase;
}

/**
 * `_app.py` と同じ丸め方(四捨五入を整数演算で。負の数は使わない集計なのでこの式で足りる)。
 * STEP TIME 作業 2(§6.4)の `timeSpentFinding` も、新しい丸め方を作らずこれを使い回す(呼び出し側で `denominator === 0` は
 * 別に判定して `null` にする ― ここでの `0` 返しは「分母 0 は 0%」という既存の意味のまま変えない)。
 */
export function percentOf(collapsed: number, denominator: number): number {
  if (denominator === 0) return 0;
  return Math.floor((200 * collapsed + denominator) / (2 * denominator));
}

const GATE_ITEM_NAMES: Record<string, string> = {
  "G-1": "当てはまる組が十分にあるか",
  "G-2": "当てはまる組の方が下がりやすいか",
  "G-3": "エンジンの読み筋では起きにくいか",
  "G-4": "別の棋譜でも同じ向きか",
};

/**
 * 別冊(付録)の候補の欄(`_app.py` の `c`)を、gate.jsonl の 1 行(材料の側。同じ条件式で `test` も入っている行)と
 * 条件式の定義から組む。Gate の判定・数値そのものは gate.jsonl を読むだけで、ここでは新しく判定しない。
 * 表示用の「value・threshold・reason」の文は、凍結した第 6 版の文面に合わせた定型文(既出の言い換え。CLAUDE.md ルール 5 の範囲)。
 */
/**
 * Gate の項目が満たさなかった理由(英字の記号)を日本語の短い文にする表。凍結した第 6 版の文面から割り出した既出の言い換え
 * (CLAUDE.md ルール 5)。表に無い記号は、記号のまま出す(推測で文を作らない)。
 */
const GATE_REASON_TEXT: Record<string, string> = {
  ratioNotMet: "割合の比が 2 倍に届かない",
  diffNotMet: "割合の差が 10 ポイントに届かない",
  pvTooHigh: "読み筋の側でも半分より多く起きている",
  signDiffers: "別の棋譜では向きが逆",
  testSignZero: "別の棋譜では変化が無い",
  materialSignZero: "材料の側で変化が無い",
  truePairsBelowMin: "当てはまる組が足りない",
  gamesBelowMin: "当てはまる組のある局が足りない",
  testTruePairsBelowMin: "別の棋譜で当てはまる組が足りない",
  pvSetEmpty: "読み筋の側と比べられる組が無い",
  pvSideNotApplicable: "読み筋の側を当てられない",
};

function gateReasonTextOf(reasons: readonly string[]): string {
  return reasons.map((reason) => GATE_REASON_TEXT[reason] ?? reason).join("・");
}

/** 試す側の局数(`test.set` の "sente<n>+gote<m>" / "sente<n>" から。新しい判断はしない、文字列の読み替えだけ)。 */
export function testGamesCountOf(testSet: string): number {
  const matches = [...testSet.matchAll(/(?:sente|gote)(\d+)/g)];
  return matches.reduce((sum, match) => sum + Number(match[1]), 0);
}

export function buildAuditCandidate(gateLine: GateLine, definition: ConditionDefinition, definitionSha256: string, reps: readonly EscapeScene[], phase: AuditCandidatePhase): AuditCandidate | null {
  if (!("items" in gateLine.gate) || !("tally" in gateLine.material) || !("tally" in gateLine.test)) return null;
  const material = gateLine.material.tally;
  const test = gateLine.test.tally;
  const t = material.truePairs;
  const f = material.falsePairs;
  const pv = material.pvSide;
  const testGames = testGamesCountOf(gateLine.test.set);
  const gateItems = gateLine.gate.items.map((item) => {
    let value = "";
    let threshold = "";
    if (item.item === "G-1") {
      value = `当てはまる組 ${item.values["truePairsDenominator"]} 組・${item.values["gamesWithTrueDenominator"]} 局`;
      threshold = `${gateLine.gateValues.minTruePairs} 組以上・${gateLine.gateValues.minGames} 局以上`;
    } else if (item.item === "G-2") {
      value = `当てはまる組 ${percentOf(t.collapsed, t.denominator)}%・当てはまらない組 ${percentOf(f.collapsed, f.denominator)}%`;
      threshold = `${gateLine.gateValues.minRateRatio} 倍以上、かつ ${gateLine.gateValues.minRateDiffPoints} ポイント以上の差`;
    } else if (item.item === "G-3") {
      value = pv.state === "applicable" ? `実戦の側 ${pv.actualTrue} 組・読み筋の側 ${pv.pvTrue} 組` : "読み筋の側を当てられない";
      threshold = gateLine.gateValues.maxPvToActualRatio === 0.5 ? "読み筋の側が実戦の側の半分以下" : `読み筋の側が実戦の側の ${gateLine.gateValues.maxPvToActualRatio} 以下`;
    } else if (item.item === "G-4") {
      const tt = test.truePairs;
      const tf = test.falsePairs;
      value = `別の ${testGames} 局で当てはまる組 ${tt.denominator} 組、下がった ${tt.collapsed} 組(当てはまらない組は ${tf.collapsed} / ${tf.denominator})`;
      threshold = `${gateLine.gateValues.minTestTruePairs} 組以上、かつ同じ向き`;
    }
    return { id: item.item, name: GATE_ITEM_NAMES[item.item] ?? item.item, value, threshold, met: item.result === "met", reason: gateReasonTextOf(item.reasons) };
  });
  return {
    id: definition.id,
    label: definition.label,
    readableText: definition.readableText,
    definitionText: definition.definitionText,
    verdict: `この条件は、${gateLine.gate.text}${gateLine.gate.verdict === "meets" ? "です" : "しています"}。`,
    meets: gateLine.gate.verdict === "meets",
    tn: t.denominator,
    tc: t.collapsed,
    tnGames: t.gamesWithDenominator,
    tTotal: t.pairs,
    fn: f.denominator,
    fc: f.collapsed,
    und: gateLine.material.tally.judgements.undecidable,
    tPct: percentOf(t.collapsed, t.denominator),
    fPct: percentOf(f.collapsed, f.denominator),
    byBefore: t.byBefore,
    fByBefore: f.byBefore,
    pv,
    test: { games: testGames, tn: test.truePairs.denominator, tc: test.truePairs.collapsed, fn: test.falsePairs.denominator, fc: test.falsePairs.collapsed },
    gate: gateItems,
    reps: [...reps],
    sha: definitionSha256.slice(0, 8),
    phase,
  };
}

/** `candidate.phase` の dropEarly/dropMid/dropLate(29 件の「drop」種の Failure Event を、表示 ply をそのまま使って早い・中・遅いに分ける。金の標本に一致する式として割り出した)。 */
export function buildAuditCandidatePhase(overview: PatientOverview, events: readonly PatientEvent[], patientGames: readonly PatientGame[]): AuditCandidatePhase {
  const dropEvents = events.filter((event) => event.kind === "drop");
  let dropEarly = 0;
  let dropMid = 0;
  let dropLate = 0;
  const totalByNo = new Map(patientGames.map((game) => [game.no, game.total]));
  for (const event of dropEvents) {
    const total = totalByNo.get(event.gameNo)!;
    const phase = phaseOf(event.ply, total);
    if (phase === "early") dropEarly += 1;
    else if (phase === "mid") dropMid += 1;
    else dropLate += 1;
  }
  return { early: overview.early, mid: overview.mid, late: overview.late, fromAhead: overview.fromAhead, fromAheadLoss: overview.fromAheadLoss, dropEarly, dropMid, dropLate };
}

// ---- sfens.json(各手の局面。本人が指した向き。inputs/sfens.ts と同じ出力) ----

export interface GameSfens {
  side: "sente" | "gote";
  sfens: string[];
  moves: string[];
}

/** `kifuId → { side, sfens, moves }`(本人が指した向きの SFEN 列。開始局面 + 各手の後、moves.length + 1 個)。 */
export function buildSfens(games: readonly BuiltGame[]): Record<string, GameSfens> {
  const out: Record<string, GameSfens> = {};
  for (const game of games) {
    const sfens: string[] = [DEFAULT_INITIAL_SFEN];
    let sfen = DEFAULT_INITIAL_SFEN;
    for (const move of game.originalMoves) sfens.push((sfen = applyMove(sfen, move)));
    out[game.source.kifuId] = { side: game.side === "後手" ? "gote" : "sente", sfens, moves: [...game.originalMoves] };
  }
  return out;
}

// ---- prose-request.md の材料(S6) ----

export interface GameTransition {
  ply: number;
  from: "ahead" | "level" | "behind";
  to: "ahead" | "level" | "behind";
}

export interface GameFacts {
  no: number;
  points: Array<{ ply: number; score: number }>;
  transitions: GameTransition[];
  maxPly: number;
  maxScore: number;
  minPly: number;
  minScore: number;
  everAhead: boolean;
  everBehind: boolean;
  finalScore: number;
  timeLoss: boolean;
}

function rankOf(score: number): "ahead" | "level" | "behind" {
  if (score >= STANDING_BOUNDS.aheadCp) return "ahead";
  if (score <= STANDING_BOUNDS.behindCp) return "behind";
  return "level";
}

export function gameFactsOf(game: PatientGame): GameFacts {
  const points = game.plies
    .map((ply, index) => ({ ply: ply + (game.side === "後手" ? 1 : 0), score: game.scores[index] }))
    .filter((point): point is { ply: number; score: number } => point.score !== null);
  const transitions: GameTransition[] = [];
  let current: "ahead" | "level" | "behind" = "level";
  for (const point of points) {
    const rank = rankOf(point.score);
    if (rank !== current) {
      transitions.push({ ply: point.ply, from: current, to: rank });
      current = rank;
    }
  }
  const maxPoint = points.reduce((best, point) => (point.score > best.score ? point : best), points[0]!);
  const minPoint = points.reduce((best, point) => (point.score < best.score ? point : best), points[0]!);
  const everAhead = maxPoint.score >= STANDING_BOUNDS.aheadCp;
  const everBehind = minPoint.score <= STANDING_BOUNDS.behindCp;
  const timeLoss = game.result === "負け" && (game.ending ?? "").includes("切れ負け");
  return {
    no: game.no,
    points,
    transitions,
    maxPly: maxPoint.ply,
    maxScore: maxPoint.score,
    minPly: minPoint.ply,
    minScore: minPoint.score,
    everAhead,
    everBehind,
    finalScore: points[points.length - 1]!.score,
    timeLoss,
  };
}

export interface FeaturedGames {
  /** 優勢から負けた局(全部。最大値の大きい順)。 */
  lossesFromAhead: PatientGame[];
  /** 劣勢から勝った局のうち、最も悪かった値の小さい順に 3 局まで。 */
  winsFromBehindTop3: PatientGame[];
}

/** 1 局ずつ載せる局の選び方(凍結した `_mid.py` の `la`・`wb` と同じ考え方。3 局までは司令塔の計画の指示)。 */
export function featuredGamesOf(games: readonly PatientGame[], facts: ReadonlyMap<number, GameFacts>): FeaturedGames {
  const losses = games.filter((game) => game.result === "負け");
  const wins = games.filter((game) => game.result === "勝ち");
  const lossesFromAhead = losses
    .filter((game) => facts.get(game.no)!.everAhead)
    .slice()
    .sort((a, b) => facts.get(b.no)!.maxScore - facts.get(a.no)!.maxScore);
  const winsFromBehind = wins
    .filter((game) => facts.get(game.no)!.everBehind)
    .slice()
    .sort((a, b) => facts.get(a.no)!.minScore - facts.get(b.no)!.minScore);
  return { lossesFromAhead, winsFromBehindTop3: winsFromBehind.slice(0, 3) };
}

/**
 * 言い換え(prose.json)の文に出してよい数の一覧(`_mid.py` の `allowed_numbers` と同じ考え方。
 * 照合の規則そのもの(BANNED 語・数の確認)は `_mid.py` に残したまま変えない。ここは材料を渡すだけ)。
 */
export function allowedNumbersOf(
  game: PatientGame,
  facts: GameFacts,
  events: readonly PatientEvent[],
  escapeScenes: readonly EscapeScene[],
  context: { total20: number; lossesCount: number; winsCount: number; lossesFromAheadCount: number; winsFromBehindCount: number },
): number[] {
  const numbers = new Set<number>([game.total, game.no, context.total20, 300, context.lossesFromAheadCount, context.winsFromBehindCount, context.winsCount, context.lossesCount]);
  for (const point of facts.points) {
    numbers.add(point.ply);
    numbers.add(Math.abs(point.score));
  }
  for (const transition of facts.transitions) numbers.add(transition.ply);
  const gameEvents = events.filter((event) => event.gameNo === game.no);
  for (const event of gameEvents) {
    numbers.add(event.ply);
    if (event.before !== null) numbers.add(Math.abs(event.before));
    if (event.after !== null) numbers.add(Math.abs(event.after));
    for (const match of event.after5.matchAll(/\d+/g)) numbers.add(Number(match[0]));
  }
  const gameScenes = escapeScenes.filter((scene) => scene.gameNo === game.no);
  for (const scene of gameScenes) {
    numbers.add(scene.displayPly);
    numbers.add(scene.escRoot);
    numbers.add(scene.escEnd);
    numbers.add(scene.pvEscEnd);
  }
  numbers.add(facts.transitions.filter((transition) => transition.to === "ahead").length);
  numbers.add(facts.transitions.filter((transition) => transition.to === "behind").length);
  return [...numbers].sort((a, b) => a - b);
}

/** prose-request.md(Markdown)。人(または LLM。CLAUDE.md ルール 5 の「言い換え」)が読んで prose.json を書くための、事実の一覧。 */
export function buildProseRequestMarkdown(
  patient: PatientReportData,
  featured: FeaturedGames,
  factsByNo: ReadonlyMap<number, GameFacts>,
): string {
  const lines: string[] = [];
  lines.push(`# 言い換えの材料(prose-request.md、${patient.person})`);
  lines.push("");
  lines.push("prose.json が無いため、ここで止まっています。1 局ずつ載せる局の事実だけを並べます。");
  lines.push("言い換えは人(または LLM。確定した判断を自然な言い回しに整えるだけ)が書き、prose.json に保存してください。");
  lines.push(`照合の規則(使ってよい数・禁止語)は凍結した _mid.py のものを変えずに使います。`);
  lines.push("");
  const losses = patient.games.filter((game) => game.result === "負け");
  const wins = patient.games.filter((game) => game.result === "勝ち");
  const context = {
    total20: patient.games.length,
    lossesCount: losses.length,
    winsCount: wins.length,
    lossesFromAheadCount: featured.lossesFromAhead.length,
    winsFromBehindCount: featured.winsFromBehindTop3.length,
  };
  const allFeatured = [...featured.lossesFromAhead, ...featured.winsFromBehindTop3];
  for (const game of allFeatured) {
    const facts = factsByNo.get(game.no)!;
    lines.push(`## 第 ${game.no} 局(${game.id}・${game.side}・${game.result}・${facts.timeLoss ? "持ち時間切れ" : (game.ending ?? "終局")})`);
    lines.push("");
    lines.push(`- 総手数: ${game.total}`);
    lines.push(`- 最も良かった: ${facts.maxPly} 手目 ${facts.maxScore >= 0 ? "+" : ""}${facts.maxScore}`);
    lines.push(`- 最も悪かった: ${facts.minPly} 手目 ${facts.minScore >= 0 ? "+" : ""}${facts.minScore}`);
    lines.push(`- 最終評価: ${facts.finalScore >= 0 ? "+" : ""}${facts.finalScore}`);
    if (facts.transitions.length > 0) {
      lines.push("- 区分の変化:");
      for (const transition of facts.transitions) {
        lines.push(`  - ${transition.ply} 手目: ${transition.from} → ${transition.to}`);
      }
    } else {
      lines.push("- 区分の変化: 最後まで互角の範囲(−300〜+300)にとどまりました");
    }
    const gameEvents = patient.events.filter((event) => event.gameNo === game.no);
    if (gameEvents.length > 0) {
      lines.push("- 場面(急落・詰めろ相当):");
      for (const event of gameEvents) {
        lines.push(`  - ${event.ply} 手目 ${event.played ?? event.playedUsi}(${event.before ?? "—"} → ${event.after ?? "—"})。${event.after5}`);
      }
    }
    const gameScenes = patient.escapeScenes.filter((scene) => scene.gameNo === game.no);
    if (gameScenes.length > 0) {
      lines.push("- 玉の逃げ道が減った場面:");
      for (const scene of gameScenes) {
        lines.push(`  - ${scene.displayPly} 手目 ${scene.userMove ?? "?"} → ${scene.opponentMove ?? "?"}(逃げ道 ${scene.escRoot} → ${scene.escEnd}、読み筋なら ${scene.pvEscEnd}）`);
      }
    }
    const allowed = allowedNumbersOf(game, facts, patient.events, patient.escapeScenes, context);
    lines.push(`- 文に使ってよい数(_mid.py の allowed_numbers と同じ集め方): ${allowed.join("、")}`);
    lines.push("");
  }
  return lines.join("\n");
}
