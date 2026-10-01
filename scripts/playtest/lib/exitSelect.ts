// ⑤ Answer selection の**候補の一覧**(計画 docs/PLAN_EXIT_SELECT_2026-10-01.md の S-2)。
//
// 【採用は機械がしない】この道具は **検証(③)を通った候補を id で並べるだけ**で、
// **採用の印は空のまま**にする。印を付けるのは司令塔か人間(正本 ⑤ の行)。
// **`adoptedBy` は常に `null`。**ここが緩むと、機械が選んだものが段 `exit-select` を素通りする。
//
// 【下書きは契約ではない】出すものは `answer-selection.v0.1` に**合わない**(合ったら、
// 機械が採用を済ませたのと同じになる)。**合わないことを試験で留める。**
//
// 【落ちた候補も捨てない】検証に落ちたものは `rejected` に理由つきで並べる ―
// 「黙って消える」より「並んで見える」(2026-10-01 の食い違いは、並んで見えたから見つかった)。
import { AGGREGATE_REF_RE, FACTS_REF_RE } from "./packetRef.js";
import { type CheckResult, validateHypothesisLine } from "./hypothesis.js";

export const SELECTION_DRAFT_NOTE =
  "これは候補の一覧であって採用ではない。採用の印(adoptedBy)は司令塔か人間が付ける。";

export interface DraftItem {
  readonly itemRef: { readonly seatIndex: number; readonly hypothesisId: string };
  readonly statement: string;
  /** その候補の観測が指す集計の行の id(`aggregates.<id>.<part>` から id を取る) */
  readonly aggregateIds: readonly string[];
  /** その候補の観測が指す局面(`facts.engine[...]`)。**盤に選べるのはここだけ** */
  readonly boardRefs: readonly string[];
}

export interface RejectedItem {
  readonly itemRef: { readonly seatIndex: number; readonly hypothesisId: string };
  /** 落ちた検査の名前(`H-9` など)。**理由を書かずに消さない** */
  readonly failedChecks: readonly string[];
}

export interface DraftQuestion {
  readonly questionId: string;
  readonly text: string;
  /** ④ の `summary` を**そのまま**。**`status` は入れない**(採用の判断なので人が書く) */
  readonly machineSummary: string;
}

export interface SelectionDraft {
  readonly note: string;
  readonly customerRef: string;
  readonly packetId: string;
  readonly runId: string;
  readonly items: readonly DraftItem[];
  readonly rejected: readonly RejectedItem[];
  readonly questions: readonly DraftQuestion[];
  readonly menuIds: readonly string[];
  /** **常に `null`。**機械は採用しない */
  readonly adoptedBy: null;
}

/** `aggregates.<id>.<part>` から集計の行の id を取る。形に合わなければ `undefined`。 */
export function aggregateIdOfRef(path: string): string | undefined {
  if (!AGGREGATE_REF_RE.test(path)) return undefined;
  const parts = path.split(".");
  // 先頭の `aggregates` と末尾の `numerator` / `denominator` / `value` を外した真ん中が id。
  return parts.slice(1, -1).join(".");
}

/** `facts.engine[...]` を指す参照かどうか(**盤に選べる局面**)。 */
export function isBoardRef(path: string): boolean {
  return FACTS_REF_RE.test(path) && path.startsWith("facts.engine[");
}

function refsOf(line: unknown): string[] {
  const observations = (line as { observations?: { packetRef?: { path?: unknown } }[] })?.observations;
  const out: string[] = [];
  for (const observation of Array.isArray(observations) ? observations : []) {
    const path = observation?.packetRef?.path;
    if (typeof path === "string") out.push(path);
  }
  return out;
}

/** 落ちた検査の名前(`ok` でないもの)。`schema` も 1 つの検査として数える。 */
export function failedCheckNames(results: readonly CheckResult[]): string[] {
  return results.filter((result) => !result.ok).map((result) => result.check);
}

export interface DraftMaterials {
  readonly packet: unknown;
  readonly integration: unknown;
  readonly request: unknown;
  readonly registry: Set<string>;
  readonly today: string;
  readonly menuIds: readonly string[];
  /**
   * 検証(③)。**既定は本物の `validateHypothesisLine`。**
   *
   * 【なぜ差し替えられるようにするか】試験で「通る候補」を作るには
   * `hypothesis.v0.4` の行を H-1〜H-11 すべてに通る形で組む必要があり、
   * **土台を組むこと自体が別の仕事**になる。ここで測りたいのは
   * **「通ったものは `items`・落ちたものは `rejected`」の振り分け**なので、検証は差し替える。
   * **既定が本物であること**は別の試験が留める(差し替えを忘れても、既定が偽物にならない)。
   */
  readonly validate?: (line: unknown) => readonly CheckResult[];
}

/**
 * 候補の一覧を組む。**検証を通った候補だけ `items` に入り、落ちたものは `rejected` に理由つきで残る。**
 * **`adoptedBy` は `null` のまま**(機械は採用しない)。
 */
export function buildSelectionDraft(materials: DraftMaterials): SelectionDraft {
  const integration = materials.integration as {
    runId?: unknown;
    clusters?: {
      itemRefs?: { seatIndex?: unknown; hypothesisId?: unknown }[];
      representative?: unknown;
    }[];
    answersByQuestion?: { questionId?: unknown; summary?: unknown }[];
  };
  const items: DraftItem[] = [];
  const rejected: RejectedItem[] = [];

  for (const cluster of integration.clusters ?? []) {
    const representative = cluster.representative;
    const results = (materials.validate ?? ((line: unknown) =>
      validateHypothesisLine(line, {
        today: materials.today,
        registry: materials.registry,
        packet: materials.packet,
      })))(representative);
    const failedChecks = failedCheckNames(results);
    const statement = typeof (representative as { statement?: unknown })?.statement === "string"
      ? ((representative as { statement: string }).statement)
      : "";
    const paths = refsOf(representative);
    const aggregateIds = [...new Set(paths.map(aggregateIdOfRef).filter((id): id is string => id !== undefined))];
    const boardRefs = [...new Set(paths.filter(isBoardRef))];
    for (const ref of cluster.itemRefs ?? []) {
      if (typeof ref.seatIndex !== "number" || typeof ref.hypothesisId !== "string") continue;
      const itemRef = { seatIndex: ref.seatIndex, hypothesisId: ref.hypothesisId };
      if (failedChecks.length > 0) {
        rejected.push({ itemRef, failedChecks });
      } else {
        items.push({ itemRef, statement, aggregateIds, boardRefs });
      }
    }
  }

  const questionText = new Map<string, string>();
  for (const question of ((materials.request as { customerQuestions?: { id?: unknown; text?: unknown }[] })
    ?.customerQuestions) ?? []) {
    if (typeof question.id === "string") {
      questionText.set(question.id, typeof question.text === "string" ? question.text : "");
    }
  }
  const questions: DraftQuestion[] = [];
  for (const row of integration.answersByQuestion ?? []) {
    if (typeof row.questionId !== "string") continue;
    questions.push({
      questionId: row.questionId,
      text: questionText.get(row.questionId) ?? "",
      machineSummary: typeof row.summary === "string" ? row.summary : "",
    });
  }

  return {
    note: SELECTION_DRAFT_NOTE,
    customerRef: String((materials.packet as { customerRef?: unknown })?.customerRef ?? ""),
    packetId: String((materials.packet as { packetId?: unknown })?.packetId ?? ""),
    runId: String(integration.runId ?? ""),
    items,
    rejected,
    questions,
    menuIds: [...materials.menuIds],
    // **機械は採用しない。**ここに値を入れると ⑤ が意味を失う。
    adoptedBy: null,
  };
}

// ==================== S-9 の門の判定(2026-10-01)====================
//
// 【門は読むだけ】この関数は**渡されたものを一切書き換えない**(`adoptedBy` を埋めない)。
// 埋められる門を書いてしまうと ⑤ が消える(司令塔 2026-10-01)。
// **書き換えていないことは試験が実物で見る**(呼ぶ前と後で深く等しいか)。
// 【fs を持たない】この関数はファイルを読まない・書かない。読むのは CLI の仕事。

/** `adoptedBy` が**埋まっている**とはどういうことか(空白だけは埋まっていない)。 */
export function adoptedByProblems(selection: unknown): string[] {
  const adoptedBy = (selection as { adoptedBy?: unknown })?.adoptedBy;
  if (adoptedBy === null || adoptedBy === undefined) {
    return ["S-9 adoptedBy が無い(採用の印は人が付ける ― 機械は埋めない)"];
  }
  if (typeof adoptedBy !== "object") return [`S-9 adoptedBy の形が違う(${typeof adoptedBy})`];
  const problems: string[] = [];
  const row = adoptedBy as Record<string, unknown>;
  for (const field of ["who", "at", "basis"] as const) {
    const value = row[field];
    if (typeof value !== "string" || value.trim() === "") {
      problems.push(`S-9 adoptedBy.${field} が空(何を見て採ったかを書く ― 委任の条件 2)`);
    }
  }
  return problems;
}

/**
 * 段 `exit-select` の判定。**契約に合うか・`adoptedBy` が埋まっているか**を見る。
 * 材料が渡されれば突き合わせ(S-3〜S-8)も見る。渡されなければ**飛ばして声に出す**
 * (⑧ の `--request` と同じ扱い ― 黙らない)。
 *
 * **渡された `selection` を書き換えない。**
 */
export function selectionGateProblems(
  selection: unknown,
  deps: {
    readonly validateContract: (selection: unknown) => string[];
    readonly crossCheck?: (selection: unknown) => string[];
  },
): { problems: string[]; notes: string[] } {
  const problems = [...deps.validateContract(selection)];
  problems.push(...adoptedByProblems(selection));
  const notes: string[] = [];
  if (deps.crossCheck === undefined) {
    notes.push("注記: 材料が渡されていないので突き合わせ(S-3〜S-8)は飛ばした");
  } else if (problems.length === 0) {
    // **契約に合わないものを突き合わせない**(誤りの文が二重になるだけで、場所が分からなくなる)。
    problems.push(...deps.crossCheck(selection));
  } else {
    notes.push("注記: 契約に合わないので突き合わせ(S-3〜S-8)は回していない");
  }
  return { problems, notes };
}
