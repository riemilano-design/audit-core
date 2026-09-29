// 次世代パイプライン Phase A の束 B(計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §3・§8)。
// **既存の出力から `packet.facts` の 7 欄を組むだけ。新しい判定を作らない。**
//
// 【この束がやらないこと】`aggregates`(冊子に出る数)と provenance の組み立ては束 C。
// 【材料は「読んだ値」で受け取る】この層はパスを読まない(引数は JSON を読んだ値)。
//   **試験が小さな合成材料で回せる**ようにするため(実データは gitignore の out/ にあり、門では読まない)。
//   実データで測るのは道具の側(`--check`)と、記録に残す実測。
// 【局の鍵】材料はどれも `g01` の形を持つ(実測: patient の `id`・direct と time_cause の `kifuId`・
//   `sfens.json` の鍵・`opening_recognition.json` の rows の鍵・jsonl の meta の `kifuId`)。**これを `gameId` にする。**
// 【駒種の語彙】`lib/moveFacts.ts` の `STANDARD_ROLES`(`userMoveFacts.role` と同じ 14 語)。
//   **`moveFactsOf` は呼ばない** ― あちらは玉の区域の広さ(閾値 = 判断的知識)を引数に要り、8 つ余分な事実も作る。
//   ここが要るのは「動かした駒は何か」だけなので、**同じ 2 行の引き当て**(打つ手は USI の 1 文字目、
//   盤の手は指す前の局面の元の升)を持つ。**語彙は写さずに import する。**
import { parseSquareName } from "shogiops/util";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { STANDARD_ROLES, type StandardRole } from "./moveFacts.js";

export class ObservationFactsError extends Error {
  override name = "ObservationFactsError";
}

/** USI の 1 文字目(打つ手の駒)→ 駒種。**成り駒は打てない**ので成りの語は出てこない */
const DROP_ROLE: Record<string, StandardRole> = {
  k: "king", r: "rook", b: "bishop", g: "gold", s: "silver", n: "knight", l: "lance", p: "pawn",
};

export type MoveRole = { readonly piece: StandardRole; readonly drop: boolean };

/**
 * その手が動かした(打った)駒の駒種。`sfenBefore` は**指す前**の局面。
 * 盤の手で元の升に駒が無ければ例外(材料の向きが食い違っている合図なので、黙って進めない)。
 */
export function moveRoleOf(sfenBefore: string, usi: string): MoveRole {
  if (usi.length < 4) throw new ObservationFactsError(`USI が短い: ${usi}`);
  if (usi[1] === "*") {
    const role = DROP_ROLE[(usi[0] ?? "").toLowerCase()];
    if (role === undefined) throw new ObservationFactsError(`打つ手の駒の字が読めない: ${usi}`);
    return { piece: role, drop: true };
  }
  const from = usi.slice(0, 2);
  const board = parsePosition(sfenBefore).board;
  const piece = pieceAtSquare(board, from);
  if (piece === undefined) throw new ObservationFactsError(`元の升 ${from} に駒が無い(局面と手が合っていない): ${usi}`);
  if (!(STANDARD_ROLES as readonly string[]).includes(piece)) throw new ObservationFactsError(`本将棋の駒種でない: ${piece}`);
  return { piece: piece as StandardRole, drop: false };
}

/**
 * 升の名前 → 盤の駒の駒種。**升の番号の計算は自分で書かない** ―
 * `shogiops/util` の `parseSquareName` を使う(既存の `lib/beginnerProfile.ts` と同じ)。
 * **自分で番号を組んだら実物で落ちた**(2026-09-30。`4f3g` の元の升に駒が無いと言われた)。
 */
function pieceAtSquare(board: { get(square: number): { role: string } | undefined }, square: string): string | undefined {
  const index = parseSquareName(square);
  if (index === undefined) return undefined;
  return board.get(index)?.role;
}

// ==================== 材料の形(読んだ値。読み方は呼ぶ側) ====================

export type PatientGame = {
  readonly id: string;
  readonly no: number;
  readonly side: string;
  readonly result: string;
  readonly ending?: string;
  readonly plies: readonly number[];
  readonly total: number;
  readonly scores?: readonly (number | null)[];
};
export type PatientEvent = {
  readonly gameNo: number;
  readonly kind?: string;
  readonly ply?: number;
  readonly before?: number | null;
  readonly after?: number | null;
};
export type PatientData = { readonly games: readonly PatientGame[]; readonly events?: readonly PatientEvent[] };
export type SfensData = Record<string, { readonly sfens: readonly string[]; readonly moves: readonly string[]; readonly side?: string }>;
export type TimeCauseGame = Record<string, unknown> & { readonly kifuId: string };
export type TimeCauseData = { readonly games: readonly TimeCauseGame[]; readonly groups?: readonly Record<string, unknown>[] };
/**
 * read / whatif-v2 の position 行。**`kifuId` は行に無い**(実測: jsonl の `meta` 行にしか無い)ので、
 * **読み手がファイル名の語幹を `kifuId` として付けて渡す**(既存の `check_answer.side_match_of` と同じやり方 ―
 * あちらも `os.path.basename` の語幹を使っている。判定ではなく写し)。
 */
export type ReadPosition = Record<string, unknown> & { readonly kifuId: string; readonly kind?: string };
export type WhatifPosition = Record<string, unknown> & { readonly kifuId: string; readonly kind?: string };
export type DirectAnswer = Record<string, unknown> & { readonly kifuId: string; readonly displayPly: number };
export type RecognitionData = {
  readonly rows: Record<string, Record<string, unknown>>;
  readonly definitions?: Record<string, unknown>;
};
export type DefinitionRecord = Record<string, unknown> & { readonly id: string };

export type FactsSources = {
  /** patient_report_data・time_cause など「材料の JSON」を指す符号 */
  readonly material: string;
  /** whatif-v2(エンジンの読み)を指す符号 */
  readonly engine: string;
  /** read(浅い読み)を指す符号 ― 分かれ道の `firstVisibleNodes` の出どころ */
  readonly engineShallow: string;
  /** direct_answers.json(浅い読みで差が見えた 103 局面)を指す符号 */
  readonly direct: string;
  /** 認識の定義を指す符号 */
  readonly recognition: string;
};

export type FactsMaterials = {
  readonly patient: PatientData;
  readonly sfens: SfensData;
  readonly timeCause: TimeCauseData;
  readonly readPositions: readonly ReadPosition[];
  readonly whatifPositions: readonly WhatifPosition[];
  readonly directAnswers: readonly DirectAnswer[];
  readonly recognition: RecognitionData;
  readonly definitions: readonly DefinitionRecord[];
  readonly sources: FactsSources;
  /** 局の持ち時間(秒)。材料が持たないので呼ぶ側が渡す(組の設定。ここで推測しない) */
  readonly timeLimitSec?: number;
};

// ==================== facts の 7 欄 ====================

export function gameRowsOf(materials: FactsMaterials): Record<string, unknown>[] {
  // 持ち時間は材料(`time_cause.json` の局ごとの `timeLimitSec`)から。**呼ぶ側に推測させない**
  const timeLimitByGame = new Map<string, number>();
  for (const game of materials.timeCause.games) {
    if (typeof game.timeLimitSec === "number") timeLimitByGame.set(game.kifuId, game.timeLimitSec);
  }
  return materials.patient.games.map((game) => {
    const row: Record<string, unknown> = {
      gameId: game.id,
      no: game.no,
      side: game.side,
      result: game.result,
      ownPlyCount: game.plies.length,
      totalPlyCount: game.total,
      src: materials.sources.material,
    };
    if (game.ending) row.ending = game.ending;
    const limit = timeLimitByGame.get(game.id) ?? materials.timeLimitSec;
    if (typeof limit === "number") row.timeLimitSec = limit;
    const record = materials.sfens[game.id];
    if (record?.side !== undefined) row.mirrored = record.side === "gote";
    return row;
  });
}

/** 本人の手(v0.1)。`side` の欄は最初から持つ(相手の手を足すときに契約を変えない) */
export function moveRowsOf(materials: FactsMaterials): Record<string, unknown>[] {
  // **分かれ道の印の鍵は `ply`**(`displayPly` ではない)。**実測で決めた**(2026-09-30):
  // 分かれ道 404 行の `(kifuId, ply)` は本人の手と **404 / 404 一致**、`displayPly` は **141 / 404 しか一致しない**
  // (263 行で 2 つの値が違う)。最初 `displayPly` を使って印が 141 しか立たず、**数を見て気づいた**。
  // **whatif-v2 との結合は `displayPly`**(既存の `check_answer.side_match_of` と同じ鍵)なので、**2 つの鍵は用途で使い分ける。**
  const forks = new Set(materials.readPositions.map((row) => `${String(row.kifuId)}/${String(row.ply ?? row.displayPly)}`));
  const spent = spentSecByGamePly(materials.timeCause);
  const rows: Record<string, unknown>[] = [];
  for (const game of materials.patient.games) {
    const record = materials.sfens[game.id];
    if (record === undefined) throw new ObservationFactsError(`${game.id} の局面が材料に無い(sfens.json)`);
    for (const ply of game.plies) {
      const usi = record.moves[ply];
      const sfenBefore = record.sfens[ply];
      const row: Record<string, unknown> = { gameId: game.id, ply: ply + 1, side: "own", src: materials.sources.material };
      if (usi !== undefined) {
        row.usi = usi;
        if (sfenBefore !== undefined) {
          const role = moveRoleOf(sfenBefore, usi);
          row.piece = role.piece;
          row.drop = role.drop;
        }
      }
      const seconds = spent.get(`${game.id}/${ply + 1}`);
      if (seconds !== undefined) row.spentSec = seconds;
      row.isFork = forks.has(`${game.id}/${ply + 1}`);
      rows.push(row);
    }
  }
  return rows;
}

/**
 * 手ごとの秒(材料 `time_cause.json` の `midMoveSeconds` から)。
 * **中盤の手だけ**を材料が持つので、無い手には欄を出さない(0 を書かない ― 「測っていない」と「0 秒」は別)。
 */
function spentSecByGamePly(timeCause: TimeCauseData): Map<string, number> {
  const out = new Map<string, number>();
  for (const game of timeCause.games) {
    const list = game.midMoveSeconds;
    if (!Array.isArray(list)) continue;
    for (const entry of list) {
      if (entry === null || typeof entry !== "object") continue;
      // **鍵は `kifPly`**(実測。`ply` ではない)、秒は `sec`
      const ply = (entry as { kifPly?: unknown }).kifPly;
      const seconds = (entry as { sec?: unknown }).sec;
      if (typeof ply === "number" && typeof seconds === "number") out.set(`${game.kifuId}/${ply}`, seconds);
    }
  }
  return out;
}

export function engineRowsOf(materials: FactsMaterials): Record<string, unknown>[] {
  return materials.whatifPositions.map((position) => {
    const gameId = String(position.kifuId);
    const ply = Number(position.displayPly ?? position.ply);
    const row: Record<string, unknown> = { gameId, ply, sfen: String(position.sfen), src: materials.sources.engine };
    const candidates = position.candidates;
    if (Array.isArray(candidates)) {
      const list = candidates
        .filter((candidate): candidate is Record<string, unknown> => candidate !== null && typeof candidate === "object")
        .map((candidate) => {
          const out: Record<string, unknown> = { usi: String(candidate.move ?? candidate.usi) };
          const score = candidate.value ?? candidate.scoreCp;
          if (typeof score === "number") out.scoreCp = Math.trunc(score);
          if (Array.isArray(candidate.pv)) out.pv = candidate.pv.map((move) => String(move));
          return out;
        });
      if (list.length > 0) {
        row.candidates = list;
        const top = list[0];
        if (top?.usi !== undefined) row.top1Usi = top.usi;
        if (typeof top?.scoreCp === "number") row.scoreCp = top.scoreCp;
      }
    }
    if (position.actualMove !== undefined) row.actualUsi = String(position.actualMove);
    return row;
  });
}

/**
 * 分かれ道。**行の骨は read(404 件)**で、側(`*Side`)は whatif-v2、浅い読みで差が見えた印は direct_answers から足す。
 * **出どころが違う欄には `src*` を置く**(provenance の参照方式。計画 §4)。
 */
export function branchRowsOf(materials: FactsMaterials): Record<string, unknown>[] {
  const whatif = new Map<string, WhatifPosition>();
  for (const position of materials.whatifPositions) {
    whatif.set(`${String(position.kifuId)}/${String(position.displayPly ?? position.ply)}`, position);
  }
  // **浅い読みで差が見えた 103 局面**は direct_answers が持つ(`actualGapCp` もあちらの値を写す ―
  // whatif-v2 の `loss` は `{value, cpValue, isLowerBound}` の組で、**下限のときに数として書けない**)
  const shallowRows = new Map<string, DirectAnswer>();
  for (const answer of materials.directAnswers) shallowRows.set(`${answer.kifuId}/${answer.displayPly}`, answer);
  return materials.readPositions.map((position) => {
    const gameId = String(position.kifuId);
    const displayPly = Number(position.displayPly ?? position.ply);
    const key = `${gameId}/${displayPly}`;
    const row: Record<string, unknown> = {
      gameId,
      ply: Number(position.ply ?? displayPly),
      displayPly,
      src: materials.sources.engineShallow,
    };
    if (position.top1Move !== undefined) row.top1Usi = String(position.top1Move);
    if (position.actualMove !== undefined) row.actualUsi = String(position.actualMove);
    if (Array.isArray(position.top1Tags)) row.top1Tags = position.top1Tags.map((tag) => String(tag));
    if (Array.isArray(position.actualTags)) row.actualTags = position.actualTags.map((tag) => String(tag));
    if (typeof position.firstVisibleNodes === "number") row.firstVisibleNodes = position.firstVisibleNodes;
    const engine = whatif.get(key);
    if (engine !== undefined) {
      // **第 1 候補の側は `candidates[0].side`**(実測。行の直下には無い ―
      // 既存の `check_answer.side_match_of` も同じ場所から引いている)
      const candidates = engine.candidates;
      if (Array.isArray(candidates) && candidates.length > 0) {
        const top = candidates[0] as Record<string, unknown>;
        if (typeof top.side === "string") {
          row.top1Side = top.side;
          row.srcTop1Side = materials.sources.engine;
        }
      }
      if (typeof engine.actualSide === "string") row.actualSide = engine.actualSide;
      if (typeof engine.topGapCp === "number") {
        row.topGapCp = Math.trunc(engine.topGapCp);
        row.srcTopGapCp = materials.sources.engine;
      }
    }
    const shallowRow = shallowRows.get(key);
    row.shallowVisible = shallowRow !== undefined;
    if (shallowRow !== undefined && typeof shallowRow.actualGapCp === "number") {
      row.actualGapCp = Math.trunc(shallowRow.actualGapCp);
      row.srcActualGapCp = materials.sources.direct;
    }
    return row;
  });
}

export function collapseRowsOf(materials: FactsMaterials): Record<string, unknown>[] {
  const gameIdByNo = new Map(materials.patient.games.map((game) => [game.no, game.id] as const));
  const rows: Record<string, unknown>[] = [];
  for (const event of materials.patient.events ?? []) {
    const gameId = gameIdByNo.get(event.gameNo);
    if (gameId === undefined) throw new ObservationFactsError(`崩れの行の局番号 ${event.gameNo} が games に無い`);
    const row: Record<string, unknown> = { gameId, ply: Number(event.ply ?? 0), src: materials.sources.material };
    if (typeof event.before === "number") row.beforeCp = Math.trunc(event.before);
    if (typeof event.after === "number") row.afterCp = Math.trunc(event.after);
    if (event.kind !== undefined) row.kind = String(event.kind);
    rows.push(row);
  }
  return rows;
}

export function timeRowsOf(materials: FactsMaterials): Record<string, unknown>[] {
  return materials.timeCause.games.map((game) => {
    const row: Record<string, unknown> = { gameId: game.kifuId, src: materials.sources.material };
    const phases = game.phaseSpentSec;
    if (phases !== null && typeof phases === "object") {
      const table = phases as Record<string, unknown>;
      if (typeof table.early === "number") row.earlySpentSec = table.early;
      if (typeof table.mid === "number") row.midSpentSec = table.mid;
      if (typeof table.late === "number") row.lateSpentSec = table.late;
    }
    if (typeof game.longThinkTotal === "number") row.longThinkCount = game.longThinkTotal;
    const fork = game.forkAmongLongThink;
    if (fork !== null && typeof fork === "object") {
      const table = fork as Record<string, unknown>;
      if (typeof table.numerator === "number") row.longThinkForkCount = table.numerator;
    }
    const opposite = game.oppositeSideAmongForkLongThink;
    if (opposite !== null && typeof opposite === "object") {
      const table = opposite as Record<string, unknown>;
      if (typeof table.numerator === "number") row.longThinkOppositeCount = table.numerator;
    }
    if (typeof game.remainingSec === "number") row.remainingSec = game.remainingSec;
    if (typeof game.timeUpLoss === "boolean") row.timeUpLoss = game.timeUpLoss;
    return row;
  });
}

/** 材料の snake_case を camelCase に直す(**束 A の試験 c1・c2 と同じ直し方**) */
export function camelKey(key: string): string {
  return key.replace(/_([a-z])/g, (_all, letter: string) => (letter as string).toUpperCase());
}

/** 定義から packet に写さない欄(束 A の試験 c2 の表と同じ) */
const DEFINITION_NOT_COPIED = new Set(["scenario", "source"]);

export function recognitionOf(materials: FactsMaterials): { rows: Record<string, unknown>[]; definitions: Record<string, unknown>[] } {
  const rows = Object.entries(materials.recognition.rows).map(([gameId, row]) => {
    const out: Record<string, unknown> = { gameId, src: materials.sources.recognition };
    if (Array.isArray(row.proposalSignature)) out.selfSignature = row.proposalSignature.map((id) => String(id));
    if (Array.isArray(row.proposalSignatureNames)) out.names = row.proposalSignatureNames.map((name) => String(name));
    if (row.proposalSignatureClass !== undefined) out.signatureClass = String(row.proposalSignatureClass);
    const self = row.self as Record<string, unknown> | undefined;
    const opponent = row.opponent as Record<string, unknown> | undefined;
    if (typeof self?.recognized === "boolean") out.selfRecognized = self.recognized;
    if (typeof self?.strongRecognized === "boolean") out.selfStrongRecognized = self.strongRecognized;
    if (typeof opponent?.recognized === "boolean") out.opponentRecognized = opponent.recognized;
    if (typeof opponent?.strongRecognized === "boolean") out.opponentStrongRecognized = opponent.strongRecognized;
    if (Array.isArray(opponent?.reached)) {
      const ids = opponent.reached
        .filter((entry): entry is Record<string, unknown> => entry !== null && typeof entry === "object")
        .map((entry) => String(entry.openingId));
      if (ids.length > 0) out.opponentSignature = ids;
    }
    return out;
  });
  const definitions = materials.definitions.map((definition) => {
    const out: Record<string, unknown> = { src: materials.sources.recognition };
    for (const [key, value] of Object.entries(definition)) {
      if (DEFINITION_NOT_COPIED.has(key)) continue;
      if (key === "recognition_pattern" && Array.isArray(value)) {
        out.recognitionPattern = value
          .filter((element): element is Record<string, unknown> => element !== null && typeof element === "object")
          .map((element) => Object.fromEntries(Object.entries(element).map(([k, v]) => [camelKey(k), v])));
        continue;
      }
      out[camelKey(key)] = value;
    }
    return out;
  });
  return { rows, definitions };
}

export function factsOf(materials: FactsMaterials): Record<string, unknown> {
  return {
    games: gameRowsOf(materials),
    moves: moveRowsOf(materials),
    engine: engineRowsOf(materials),
    time: timeRowsOf(materials),
    branches: branchRowsOf(materials),
    collapse: collapseRowsOf(materials),
    recognition: recognitionOf(materials),
  };
}

// ==================== 完全性(B)と粒度(C)の検査 ====================
//
// **人間の指示(2026-09-30・伝聞)の 5 本立ての B と C。**
// 試験の中だけでなく**道具が毎回自分で測る** ― 次の顧客の材料でも同じ検査が走る。

export function completenessProblems(facts: Record<string, unknown>, materials: FactsMaterials): string[] {
  const problems: string[] = [];
  const games = (facts.games ?? []) as { gameId: string }[];
  const packetIds = new Set(games.map((game) => game.gameId));
  const materialIds = new Set(materials.patient.games.map((game) => game.id));
  for (const id of materialIds) if (!packetIds.has(id)) problems.push(`B 完全性: 材料の局 ${id} が packet に無い`);
  for (const id of packetIds) if (!materialIds.has(id)) problems.push(`B 完全性: packet の局 ${id} が材料に無い`);
  if (packetIds.size !== games.length) problems.push(`B 完全性: packet の局に同じ id が 2 回ある(行 ${games.length} / id ${packetIds.size})`);

  const recognition = (facts.recognition ?? {}) as { rows?: { gameId: string }[] };
  const recognitionIds = new Set((recognition.rows ?? []).map((row) => row.gameId));
  for (const id of Object.keys(materials.recognition.rows)) {
    if (!recognitionIds.has(id)) problems.push(`B 完全性: 認識の行 ${id} が packet に無い`);
  }

  const branches = (facts.branches ?? []) as unknown[];
  if (branches.length !== materials.readPositions.length) {
    problems.push(`B 完全性: 分かれ道の行が ${branches.length}(材料の read は ${materials.readPositions.length})`);
  }
  const engine = (facts.engine ?? []) as unknown[];
  if (engine.length !== materials.whatifPositions.length) {
    problems.push(`B 完全性: エンジンの行が ${engine.length}(材料の whatif-v2 は ${materials.whatifPositions.length})`);
  }

  // **分かれ道の局面が、本人の手として在るか**(2026-09-30 に踏んだ取り違えを機械で捕まえる)。
  // 鍵を `displayPly` にすると 404 のうち 141 しか一致しない ― **数が合わないことを検査で言わせる。**
  const moveKeys = new Set(((facts.moves ?? []) as { gameId: string; ply: number }[]).map((move) => `${move.gameId}/${move.ply}`));
  const orphans = (branches as { gameId: string; ply: number }[]).filter((branch) => !moveKeys.has(`${branch.gameId}/${branch.ply}`));
  if (orphans.length > 0) {
    problems.push(`B 完全性: 分かれ道 ${orphans.length} 件の (局, 手) が本人の手に無い(例 ${orphans.slice(0, 3).map((row) => `${row.gameId}/${row.ply}`).join("・")})`);
  }
  const forkFlags = ((facts.moves ?? []) as { isFork?: boolean }[]).filter((move) => move.isFork === true).length;
  if (forkFlags !== branches.length) {
    problems.push(`B 完全性: 分かれ道の印が付いた手が ${forkFlags}(分かれ道の行は ${branches.length})`);
  }

  // **残る 3 欄の件数と重複**(2026-09-30 の独立監査の REVISE 1)。
  // 監査は**行が増える方向**で 2 通り作って通した ― 同じ定義のフォルダを 2 回渡すと定義が 114 → 117 になり、
  // 崩れ・時間の材料の 1 行を複製すると 155 → 156・25 → 26 になるのに、**検査は 0 件だった**。
  // 「道具が毎回自分で測る」と書いておきながら、**7 欄のうち 3 欄で測っていなかった。**
  const collapse = (facts.collapse ?? []) as unknown[];
  const events = materials.patient.events ?? [];
  if (collapse.length !== events.length) {
    problems.push(`B 完全性: 崩れの行が ${collapse.length}(材料の events は ${events.length})`);
  }
  const time = (facts.time ?? []) as { gameId: string }[];
  if (time.length !== materials.timeCause.games.length) {
    problems.push(`B 完全性: 時間の行が ${time.length}(材料の time_cause は ${materials.timeCause.games.length})`);
  }
  const timeIds = new Set(time.map((row) => row.gameId));
  if (timeIds.size !== time.length) {
    problems.push(`B 完全性: 時間の行に同じ局が 2 回ある(行 ${time.length} / 局 ${timeIds.size})`);
  }
  const definitions = ((facts.recognition ?? {}) as { definitions?: { id?: string }[] }).definitions ?? [];
  if (definitions.length !== materials.definitions.length) {
    problems.push(`B 完全性: 認識の定義が ${definitions.length}(材料は ${materials.definitions.length})`);
  }
  const definitionIds = new Set(definitions.map((row) => String(row.id)));
  if (definitionIds.size !== definitions.length) {
    problems.push(`B 完全性: 認識の定義に同じ id が 2 回ある(行 ${definitions.length} / id ${definitionIds.size})`);
  }
  return problems;
}

export function granularityProblems(facts: Record<string, unknown>, materials: FactsMaterials): string[] {
  const problems: string[] = [];
  const moves = (facts.moves ?? []) as { gameId: string; ply: number }[];
  const countByGame = new Map<string, number>();
  for (const move of moves) countByGame.set(move.gameId, (countByGame.get(move.gameId) ?? 0) + 1);
  let expectedTotal = 0;
  for (const game of materials.patient.games) {
    expectedTotal += game.plies.length;
    const got = countByGame.get(game.id) ?? 0;
    if (got !== game.plies.length) {
      problems.push(`C 粒度: ${game.id} の本人の手が ${got}(材料は ${game.plies.length})`);
    }
  }
  if (moves.length !== expectedTotal) problems.push(`C 粒度: 本人の手の合計が ${moves.length}(材料は ${expectedTotal})`);
  const duplicated = new Set<string>();
  const seen = new Set<string>();
  for (const move of moves) {
    const key = `${move.gameId}/${move.ply}`;
    if (seen.has(key)) duplicated.add(key);
    seen.add(key);
  }
  if (duplicated.size > 0) problems.push(`C 粒度: 同じ手が 2 回ある(${[...duplicated].slice(0, 5).join("・")})`);
  return problems;
}

export function factsProblems(facts: Record<string, unknown>, materials: FactsMaterials): string[] {
  return [...completenessProblems(facts, materials), ...granularityProblems(facts, materials)];
}
