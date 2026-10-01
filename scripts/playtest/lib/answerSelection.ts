// ⑤ Answer selection の契約の入口(計画 docs/PLAN_EXIT_SELECT_2026-10-01.md の S-1)。
//
// 【採用は機械がしない】この道具は「検証を通った候補」を id で並べ、**採用の印は空のまま**にする。
// 印を付けるのは司令塔か人間(正本 ⑤ の行)。段 `exit-select` は印が埋まるまで止まる。
//
// 【機械の読みを捨てない】`answers[].machineSummary` に ④ の `summary` をそのまま写す。
// 2026-10-01 に **機械は `partial`・人間は `unanswerable`** で食い違った実物がある ―
// 両方が並んで見えたから見つかった。`status` に写してはいけない(S-5a)が、捨ててもいけない(S-5b)。
//
// 【schema で書けないものはここで見る】検証器(`lib/eventSchema.ts`)は JSON Schema の部分集合で
// **`maxItems` を扱わない**ので、「ちょうど 3 本」「ちょうど 2 つ」はこの道具が数える。
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { type JsonSchema, validate } from "./eventSchema.js";

export const ANSWER_SELECTION_CONTRACT = "answer-selection";
export const ANSWER_SELECTION_SCHEMA_VERSION = "0.1";

/**
 * 正本の数。**人が決めた数なので、試験は字で留める**(2026-10-01 の教訓 ―
 * 定数から土台を作る試験は、その定数を動かす変異で赤くならない)。
 */
export const P1_COUNT = 3;
export const BOARD_COUNT = 2;

/** `status` の 3 語(採用の側)。④ の `summary` は 5 語で、**写し方の規則は作らない**(司令塔 2026-10-01)。 */
export const ADOPTED_STATUSES = ["answered", "partial", "unanswerable"] as const;
export type AdoptedStatus = (typeof ADOPTED_STATUSES)[number];

/** `neededObservation` が要る `status`(S-8)。 */
export const STATUSES_NEEDING_OBSERVATION: readonly AdoptedStatus[] = ["partial", "unanswerable"];

const HERE = path.dirname(fileURLToPath(import.meta.url));

export function answerSelectionSchemaPath(): string {
  return path.join(HERE, "..", "schemas", `answer-selection.v${ANSWER_SELECTION_SCHEMA_VERSION}.schema.json`);
}

export function loadAnswerSelectionSchema(): JsonSchema {
  return JSON.parse(readFileSync(answerSelectionSchemaPath(), "utf-8")) as JsonSchema;
}

export function validateAnswerSelection(
  selection: unknown,
  schema: JsonSchema = loadAnswerSelectionSchema(),
): string[] {
  return validate(selection, schema);
}

// ==================== 道具が見るもの(schema で書けないもの)====================
//
// 【なぜ schema に書かないか】検証器は **`maxItems` を扱わない**ので「ちょうど 3 本」が書けない。
// 承認済みの行動の表(M1〜M9)は**写すと表が変わったとき黙ってずれる**ので、実在はここで照合する。
// 統合と packet の中の実在も、別のファイルを読む話なので schema では書けない。

/** 照合に使う材料(**id の集合だけ**。数は持たない)。 */
export interface SelectionContext {
  /** packet の `aggregates[].id`(S-3) */
  readonly aggregateIds: ReadonlySet<string>;
  /** 統合の `itemRef` → その束の代表の `statement`(S-4・S-7)。statement が無い束は空文字 */
  readonly statementByItemRef: ReadonlyMap<string, string>;
  /** request の `customerQuestions[].id`(S-5。**並びも意味を持つ**ので配列) */
  readonly questionIds: readonly string[];
  /** 承認済みの行動の表の id(S-6) */
  readonly menuIds: ReadonlySet<string>;
}

/** `itemRef` の鍵。**場所ではなく中身**で引く(席の番号と仮説の id の組)。 */
export function itemRefKey(ref: { seatIndex: number; hypothesisId: string }): string {
  return `${ref.seatIndex}/${ref.hypothesisId}`;
}

/** 統合の実物から照合の材料を作る。`clusters[].itemRefs[]` → その束の `representative.statement`。 */
export function statementByItemRefOf(integration: unknown): Map<string, string> {
  const out = new Map<string, string>();
  const clusters = (integration as { clusters?: unknown[] })?.clusters;
  if (!Array.isArray(clusters)) return out;
  for (const cluster of clusters) {
    const node = cluster as {
      itemRefs?: { seatIndex?: unknown; hypothesisId?: unknown }[];
      representative?: { statement?: unknown };
    };
    const statement = typeof node.representative?.statement === "string" ? node.representative.statement : "";
    for (const ref of node.itemRefs ?? []) {
      if (typeof ref.seatIndex !== "number" || typeof ref.hypothesisId !== "string") continue;
      out.set(itemRefKey({ seatIndex: ref.seatIndex, hypothesisId: ref.hypothesisId }), statement);
    }
  }
  return out;
}

/** packet の実物から `aggregates[].id` の集合を作る。 */
export function aggregateIdsOf(packet: unknown): Set<string> {
  const rows = (packet as { aggregates?: { id?: unknown }[] })?.aggregates;
  const out = new Set<string>();
  for (const row of Array.isArray(rows) ? rows : []) {
    if (typeof row.id === "string") out.add(row.id);
  }
  return out;
}

/** request の実物から問いの id を**並びのまま**取る。 */
export function questionIdsOf(request: unknown): string[] {
  const questions = (request as { customerQuestions?: { id?: unknown }[] })?.customerQuestions;
  const out: string[] = [];
  for (const question of Array.isArray(questions) ? questions : []) {
    if (typeof question.id === "string") out.push(question.id);
  }
  return out;
}

/** 文に数が入っていないか(S-8)。**半角・全角の数字**を見る。 */
const DIGITS_RE = /[0-9０-９]/;

type Selection = {
  lead: { itemRef: { seatIndex: number; hypothesisId: string } };
  p1: { slot: string; aggregateIds: string[]; itemRef: { seatIndex: number; hypothesisId: string }; readingRequired: boolean }[];
  answers: {
    questionId: string;
    status: string;
    itemRefs: { seatIndex: number; hypothesisId: string }[];
    aggregateIds: string[];
    neededObservation?: { what: string; howToMeasure: string };
  }[];
  boards: unknown[];
  actions: { slot: string; menuId: string; itemRef: { seatIndex: number; hypothesisId: string } }[];
  humanQueue: { itemRef: { seatIndex: number; hypothesisId: string } }[];
};

/**
 * 契約に合った選択を、**材料と突き合わせる**(S-3〜S-8)。
 * 契約そのものの形は `validateAnswerSelection` が見る ― **ここは二重に言わない。**
 */
export function selectionProblems(selection: unknown, ctx: SelectionContext): string[] {
  const problems: string[] = [];
  const sel = selection as Selection;

  // ---- S-3: aggregateIds が packet に実在する ----
  const checkAggregates = (ids: readonly string[], where: string) => {
    for (const id of ids) {
      if (!ctx.aggregateIds.has(id)) problems.push(`S-3 ${where}: packet の aggregates に無い id「${id}」`);
    }
  };
  // ---- S-4: itemRef が統合に実在する ----
  const checkItemRef = (ref: { seatIndex: number; hypothesisId: string }, where: string) => {
    if (!ctx.statementByItemRef.has(itemRefKey(ref))) {
      problems.push(`S-4 ${where}: 統合に無い itemRef「${itemRefKey(ref)}」`);
    }
  };

  checkItemRef(sel.lead.itemRef, "lead.itemRef");

  // ---- p1: ちょうど 3 本(schema は下限だけ見る)----
  if (sel.p1.length !== P1_COUNT) {
    problems.push(`S-2 p1 が ${sel.p1.length} 本(ちょうど ${P1_COUNT} 本が要る)`);
  }
  const p1Slots = sel.p1.map((row) => row.slot);
  if (new Set(p1Slots).size !== p1Slots.length) {
    problems.push(`S-2 p1 の slot が重なっている(${p1Slots.join(", ")})`);
  }
  sel.p1.forEach((row, index) => {
    checkAggregates(row.aggregateIds, `p1[${index}](${row.slot})`);
    checkItemRef(row.itemRef, `p1[${index}](${row.slot}).itemRef`);
    // ---- S-7: 読みが要る行は statement を持つ ----
    if (row.readingRequired) {
      const statement = ctx.statementByItemRef.get(itemRefKey(row.itemRef));
      if (statement !== undefined && statement.trim() === "") {
        problems.push(`S-7 p1[${index}](${row.slot}): readingRequired だが統合の代表に statement が無い`);
      }
    }
  });

  // ---- boards: ちょうど 2 つ ----
  if (sel.boards.length !== BOARD_COUNT) {
    problems.push(`S-2 boards が ${sel.boards.length} つ(ちょうど ${BOARD_COUNT} つが要る)`);
  }

  // ---- S-5: request の問いごとにちょうど 1 行 ----
  const answered = sel.answers.map((row) => row.questionId);
  for (const questionId of ctx.questionIds) {
    const n = answered.filter((id) => id === questionId).length;
    if (n !== 1) problems.push(`S-5 問い ${questionId} の行が ${n} 件(ちょうど 1 件が要る)`);
  }
  for (const questionId of answered) {
    if (!ctx.questionIds.includes(questionId)) {
      problems.push(`S-5 request に無い問い「${questionId}」の行が在る`);
    }
  }

  sel.answers.forEach((row, index) => {
    checkAggregates(row.aggregateIds, `answers[${index}](${row.questionId})`);
    row.itemRefs.forEach((ref, refIndex) => {
      checkItemRef(ref, `answers[${index}](${row.questionId}).itemRefs[${refIndex}]`);
    });
    // ---- S-8: partial / unanswerable は neededObservation を持ち、数を含まない ----
    const needs = (STATUSES_NEEDING_OBSERVATION as readonly string[]).includes(row.status);
    if (needs && row.neededObservation === undefined) {
      problems.push(`S-8 answers[${index}](${row.questionId}): status が ${row.status} だが neededObservation が無い`);
    }
    if (!needs && row.neededObservation !== undefined) {
      problems.push(`S-8 answers[${index}](${row.questionId}): status が ${row.status} なのに neededObservation が在る`);
    }
    for (const [field, text] of Object.entries(row.neededObservation ?? {})) {
      if (DIGITS_RE.test(text)) {
        problems.push(`S-8 answers[${index}](${row.questionId}).neededObservation.${field}: 数が入っている「${text}」`);
      }
    }
  });

  // ---- S-6: menuId が承認済みの表に実在する / 表に無いものは humanQueue へ ----
  const actionSlots = sel.actions.map((row) => row.slot);
  if (new Set(actionSlots).size !== actionSlots.length) {
    problems.push(`S-6 actions の slot が重なっている(${actionSlots.join(", ")})`);
  }
  sel.actions.forEach((row, index) => {
    if (!ctx.menuIds.has(row.menuId)) {
      problems.push(`S-6 actions[${index}](${row.slot}): 承認済みの表に無い menuId「${row.menuId}」(冊子に出せない ― humanQueue へ)`);
    }
    checkItemRef(row.itemRef, `actions[${index}](${row.slot}).itemRef`);
  });
  sel.humanQueue.forEach((row, index) => {
    checkItemRef(row.itemRef, `humanQueue[${index}].itemRef`);
  });

  return problems;
}
