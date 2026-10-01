// ⑤ の候補の一覧の試験(計画 docs/PLAN_EXIT_SELECT_2026-10-01.md の S-2)。
//
// 【この束の肝】**採用の印は空のまま**。ここが緩むと、機械が選んだものが段 `exit-select` を素通りし、
// 2026-10-01 に見つけた食い違い(④ の `summary` = `partial` / 人間の採用 = `unanswerable`)が
// **自動で通る**。だから `adoptedBy` が埋まる変異・下書きが契約に合ってしまう変異を当てる。
import path from "node:path";

import { describe, expect, it } from "vitest";

import { FACTS_REF_RE } from "./packetRef.js";

import { validateAnswerSelection } from "./answerSelection.js";
import {
  DELIVER_EXIT_DIR,
  DELIVER_EXIT_NAMES,
  DELIVER_STAGES,
  DeliverArgError,
  customerDirOf,
  exitSelectPaths,
} from "./deliver.js";
import type { CheckResult } from "./hypothesis.js";
import {
  SELECTION_DRAFT_NOTE,
  adoptedByProblems,
  aggregateIdOfRef,
  buildSelectionDraft,
  failedCheckNames,
  isBoardRef,
  selectionGateProblems,
  type DraftMaterials,
} from "./exitSelect.js";

/** 代表の行(検証は差し替えるので、ここは形だけ) */
function representative(hypothesisId: string, statement: string, paths: readonly string[]) {
  return {
    schemaVersion: "0.4",
    hypothesisId,
    statement,
    observations: paths.map((path) => ({ packetRef: { path } })),
  };
}

const OK: CheckResult[] = [{ check: "schema", ok: true, messages: [] }];
const NG: CheckResult[] = [
  { check: "schema", ok: true, messages: [] },
  { check: "H-9", ok: false, messages: ["packet に無い"] },
  { check: "H-10", ok: false, messages: ["語彙に無い"] },
];

function materials(over: Partial<DraftMaterials> = {}): DraftMaterials {
  return {
    packet: { customerRef: "c5", packetId: "22aee8fe696d0262", aggregates: [{ id: "groups.core.games" }] },
    integration: {
      runId: "558b8a81-20261001-2",
      clusters: [
        {
          itemRefs: [{ seatIndex: 1, hypothesisId: "I-1-001" }],
          representative: representative("I-1-001", "通る候補の読み", [
            "aggregates.groups.core.games.value",
            "facts.engine[12].scoreCp",
          ]),
        },
        {
          itemRefs: [{ seatIndex: 2, hypothesisId: "I-2-001" }],
          representative: representative("I-2-001", "落ちる候補の読み", ["aggregates.branches.total.value"]),
        },
      ],
      answersByQuestion: [{ questionId: "q1", summary: "partial" }],
    },
    request: { customerQuestions: [{ id: "q1", text: "普段指さない戦型のとき、どこで崩れているか" }] },
    registry: new Set<string>(),
    today: "2026-10-01",
    menuIds: ["M1", "M4", "M9"],
    // **通る候補と落ちる候補を 1 つずつ**(振り分けの両側を測る)。
    validate: (line) => ((line as { hypothesisId?: string })?.hypothesisId === "I-1-001" ? OK : NG),
    ...over,
  };
}

describe("⑤ 候補の一覧(S-2)", () => {
  it("u1 **採用の印は空のまま**(機械は採用しない)", () => {
    expect(buildSelectionDraft(materials()).adoptedBy).toBeNull();
    // 材料がどうであれ `null`(「材料が揃えば入れる」形になっていない)。
    expect(buildSelectionDraft(materials({ menuIds: [] })).adoptedBy).toBeNull();
    expect(buildSelectionDraft(materials({ integration: { clusters: [] } })).adoptedBy).toBeNull();
  });

  it("u2 **下書きは契約に合わない**(⑥ に間違って渡せない)", () => {
    // 合ってしまったら、機械が採用を済ませたのと同じになる。**合わないことを留める。**
    const problems = validateAnswerSelection(buildSelectionDraft(materials()));
    expect(problems.length).toBeGreaterThan(0);
    expect(problems.join("\n")).toContain("contract");
  });

  it("u3 検証を通ったものは items・落ちたものは rejected(**両側**)", () => {
    const draft = buildSelectionDraft(materials());
    expect(draft.items.map((item) => item.itemRef.hypothesisId)).toEqual(["I-1-001"]);
    expect(draft.rejected.map((item) => item.itemRef.hypothesisId)).toEqual(["I-2-001"]);
    // **落ちた理由を書かずに消さない。**
    expect(draft.rejected[0]!.failedChecks).toEqual(["H-9", "H-10"]);
    // **数がそろっていない**ので、片方だけ数える取り違えが黙らない。
    expect(draft.items).toHaveLength(1);
    expect(draft.rejected).toHaveLength(1);
    expect(draft.items.length + draft.rejected.length).toBe(2);
  });

  it("u4 全部落ちれば items は空(通った数を「全部」にしない)", () => {
    const draft = buildSelectionDraft(materials({ validate: () => NG }));
    expect(draft.items).toEqual([]);
    expect(draft.rejected).toHaveLength(2);
    // 逆側: 全部通れば rejected が空。
    const allOk = buildSelectionDraft(materials({ validate: () => OK }));
    expect(allOk.items).toHaveLength(2);
    expect(allOk.rejected).toEqual([]);
  });

  it("u5 候補は観測の指す先だけを持つ(集計の id と盤の局面)", () => {
    const item = buildSelectionDraft(materials()).items[0]!;
    expect(item.aggregateIds).toEqual(["groups.core.games"]);
    expect(item.boardRefs).toEqual(["facts.engine[12].scoreCp"]);
    expect(item.statement).toBe("通る候補の読み");
  });

  it("u5b 観測の `path` が文字列でないものは拾わない(型の守りを留める)", () => {
    // 【なぜ要るか】独立監査が当てた変異 ― `typeof path === "string"` の守りを
    // `as string` で迂回しても **2277 本すべて緑・型検査も 0 件**だった。
    // 土台に文字列でない `path` が 1 件も無かったため。
    const broken = {
      schemaVersion: "0.4",
      hypothesisId: "I-1-001",
      statement: "読み",
      observations: [
        { packetRef: { path: "aggregates.groups.core.games.value" } },
        { packetRef: { path: 42 } },
        { packetRef: { path: null } },
        { packetRef: {} },
        { packetRef: { path: ["facts.engine[0].scoreCp"] } },
        { packetRef: { path: "facts.engine[7].scoreCp" } },
      ],
    };
    const draft = buildSelectionDraft(
      materials({
        validate: () => OK,
        integration: {
          runId: "r1",
          clusters: [{ itemRefs: [{ seatIndex: 1, hypothesisId: "I-1-001" }], representative: broken }],
          answersByQuestion: [],
        },
      }),
    );
    const item = draft.items[0]!;
    // **文字列の 2 件だけ**が通る(数・null・無い欄・配列は落ちる)。
    expect(item.aggregateIds).toEqual(["groups.core.games"]);
    expect(item.boardRefs).toEqual(["facts.engine[7].scoreCp"]);
    // **件数で留める**(拾い過ぎたら増える)。
    expect(item.aggregateIds.length + item.boardRefs.length).toBe(2);
    // 文字列でないものが**どの形でも混ざっていない**。
    expect(JSON.stringify(item)).not.toContain("42");
    expect(JSON.stringify(item)).not.toContain("null");
  });

  it("u6 問いは ④ の summary をそのまま持ち、**status は持たない**", () => {
    const draft = buildSelectionDraft(materials());
    expect(draft.questions).toHaveLength(1);
    expect(draft.questions[0]!.questionId).toBe("q1");
    expect(draft.questions[0]!.machineSummary).toBe("partial");
    expect(draft.questions[0]!.text).toContain("普段指さない");
    // **採用の語を下書きに入れない**(人が書くもの)。
    expect(Object.keys(draft.questions[0]!).sort()).toEqual(["machineSummary", "questionId", "text"]);
    expect(JSON.stringify(draft.questions[0])).not.toContain("status");
  });

  it("u7 下書きに「採用ではない」と書いてある", () => {
    const draft = buildSelectionDraft(materials());
    expect(draft.note).toBe(SELECTION_DRAFT_NOTE);
    expect(draft.note).toContain("採用ではない");
    expect(draft.note).toContain("adoptedBy");
  });

  it("u8 行動の表はそのまま写す(縮めない)", () => {
    expect(buildSelectionDraft(materials()).menuIds).toEqual(["M1", "M4", "M9"]);
    expect(buildSelectionDraft(materials({ menuIds: ["M1"] })).menuIds).toEqual(["M1"]);
  });

  it("u9 封の符号と周を材料から取る(新しい数を作らない)", () => {
    const draft = buildSelectionDraft(materials());
    expect(draft.packetId).toBe("22aee8fe696d0262");
    expect(draft.runId).toBe("558b8a81-20261001-2");
    expect(draft.customerRef).toBe("c5");
  });

  it("u10 集計の参照から id を取る(**形に合わないものは取らない**)", () => {
    expect(aggregateIdOfRef("aggregates.groups.core.games.value")).toBe("groups.core.games");
    expect(aggregateIdOfRef("aggregates.side_match.attack.numerator")).toBe("side_match.attack");
    expect(aggregateIdOfRef("aggregates.a.denominator")).toBe("a");
    // 形に合わないもの(末尾の語が無い・列が違う・退化した字)。
    for (const bad of [
      "aggregates.groups.core.games",
      "facts.engine[0].scoreCp",
      "aggregates..value",
      "aggregates.a.b.total",
      "",
      "aggregates",
    ]) {
      expect(aggregateIdOfRef(bad), bad).toBeUndefined();
    }
  });

  it("u11 盤に選べるのは `facts.engine[...]` だけ", () => {
    expect(isBoardRef("facts.engine[0].scoreCp")).toBe(true);
    expect(isBoardRef("facts.engine[12].candidates[0].usi")).toBe(true);
    for (const bad of [
      "facts.time[3].midSpentSec",
      "facts.branches[0].topGapCp",
      "aggregates.groups.core.games.value",
      "facts.engine.scoreCp",
      "facts.engineering[0].x",
      "",
      // **文字として `engine` を含むが、`engine` の列ではない**(独立監査が当てた変異。2026-10-01)。
      // `startsWith("facts.engine[")` を `includes("engine")` に緩める変異が、
      // **2277 本すべてを緑で通った** ― 既存の bad の字はどれも `engine` を含まないため。
      // **この 2 つは `FACTS_REF_RE` を通る**(自分で正規表現に当てて確かめた)ので、
      // 文法の側では落ちず、**列の見分けだけがこれを落としている**。
      "facts.collapse[0].enginePresenceFlag",
      "facts.time[3].engineNote",
    ]) {
      expect(isBoardRef(bad), bad).toBe(false);
    }
  });

  it("u11b 盤の見分けは**列**で決まる(字に `engine` が在るかではない)", () => {
    // 上の bad の 2 つが「文法で落ちている」のではないことを、**文法を通ることで**示す。
    // こうしておくと、`isBoardRef` の緩みと `FACTS_REF_RE` の緩みが混ざらない。
    expect(FACTS_REF_RE.test("facts.collapse[0].enginePresenceFlag")).toBe(true);
    expect(FACTS_REF_RE.test("facts.time[3].engineNote")).toBe(true);
    expect(isBoardRef("facts.collapse[0].enginePresenceFlag")).toBe(false);
    expect(isBoardRef("facts.time[3].engineNote")).toBe(false);
    // 逆側: `engine` の列は通る。
    expect(FACTS_REF_RE.test("facts.engine[0].scoreCp")).toBe(true);
    expect(isBoardRef("facts.engine[0].scoreCp")).toBe(true);
  });

  it("u12 落ちた検査の名前は `ok` でないものだけ", () => {
    expect(failedCheckNames(OK)).toEqual([]);
    expect(failedCheckNames(NG)).toEqual(["H-9", "H-10"]);
    // `schema` も 1 つの検査として数える(落ちたら名前が出る)。
    expect(failedCheckNames([{ check: "schema", ok: false, messages: ["形が違う"] }])).toEqual(["schema"]);
  });

  it("u13 **既定の検証は本物**(差し替えを忘れても偽物にならない)", () => {
    // `validate` を渡さない = 本物の `validateHypothesisLine`。
    // 明らかに形の違う行(`{}`)は落ちるので、**全部 `rejected` に行く**。
    const draft = buildSelectionDraft({
      ...materials(),
      validate: undefined,
      integration: {
        runId: "r1",
        clusters: [{ itemRefs: [{ seatIndex: 1, hypothesisId: "I-1-001" }], representative: {} }],
        answersByQuestion: [],
      },
    });
    expect(draft.items).toEqual([]);
    expect(draft.rejected).toHaveLength(1);
    // **本物の検査の名前が出る**(偽物の検証なら H- の名前は出ない)。
    expect(draft.rejected[0]!.failedChecks.some((name) => name.startsWith("H-"))).toBe(true);
    expect(draft.rejected[0]!.failedChecks).toContain("schema");
  });

  it("u14 材料が空でも落ちない(**空のものを空のまま返す** ― 黙って作らない)", () => {
    const draft = buildSelectionDraft({
      packet: {},
      integration: {},
      request: {},
      registry: new Set<string>(),
      today: "2026-10-01",
      menuIds: [],
    });
    expect(draft.items).toEqual([]);
    expect(draft.rejected).toEqual([]);
    expect(draft.questions).toEqual([]);
    expect(draft.adoptedBy).toBeNull();
    expect(draft.packetId).toBe("");
  });
});

describe("⑤ の門(S-9)", () => {
  /** 契約に合い、`adoptedBy` も埋まっている選択(形だけ ― 契約の検査は差し替える) */
  function filled() {
    return {
      contract: "answer-selection",
      adoptedBy: { who: "commander", at: "2026-10-01T00:00:00Z", basis: "検証を通り、問いに合う候補を採った" },
    };
  }
  const noContractProblems = () => [];

  it("g1 `adoptedBy` が無い・空だと落ちる(**機械が埋める欄ではない**)", () => {
    expect(adoptedByProblems({ adoptedBy: null }).join("\n")).toContain("adoptedBy が無い");
    expect(adoptedByProblems({}).join("\n")).toContain("adoptedBy が無い");
    expect(adoptedByProblems({ adoptedBy: "済み" }).join("\n")).toContain("形が違う");
    // **3 つの欄を 1 つずつ**(片方だけ見る変異が黙らない)。
    for (const field of ["who", "at", "basis"] as const) {
      const row = filled();
      (row.adoptedBy as Record<string, string>)[field] = "";
      const problems = adoptedByProblems(row);
      expect(problems, field).toHaveLength(1);
      expect(problems[0], field).toContain(`adoptedBy.${field}`);
    }
    // **空白だけも「埋まっていない」**(字が在るかを見ている)。
    const blank = filled();
    blank.adoptedBy.basis = "   　 ";
    expect(adoptedByProblems(blank).join("\n")).toContain("adoptedBy.basis");
    // 埋まっていれば問題なし。
    expect(adoptedByProblems(filled())).toEqual([]);
  });

  it("g2 門は契約の誤りと `adoptedBy` の誤りの**両方**を言う", () => {
    const { problems } = selectionGateProblems(
      { adoptedBy: null },
      { validateContract: () => ["契約: contract が無い"] },
    );
    expect(problems.join("\n")).toContain("契約: contract が無い");
    expect(problems.join("\n")).toContain("adoptedBy が無い");
  });

  it("g3 **門は渡されたものを書き換えない**(`adoptedBy` を埋める道が無い)", () => {
    // 【なぜこの試験か】埋められる門を書いてしまうと ⑤ が消える(司令塔 2026-10-01)。
    // **呼ぶ前と後で深く等しい**ことを見る ― 門が「足りないから入れておく」をしない。
    const empty = { contract: "answer-selection", adoptedBy: null };
    const before = JSON.parse(JSON.stringify(empty)) as typeof empty;
    const { problems } = selectionGateProblems(empty, { validateContract: noContractProblems });
    expect(problems.length).toBeGreaterThan(0);
    expect(empty).toEqual(before);
    expect(empty.adoptedBy).toBeNull();
    // 埋まっている側でも書き換えない。
    const ok = filled();
    const okBefore = JSON.parse(JSON.stringify(ok)) as typeof ok;
    selectionGateProblems(ok, { validateContract: noContractProblems, crossCheck: () => [] });
    expect(ok).toEqual(okBefore);
  });

  it("g4 材料が渡されなければ**飛ばして声に出す**(黙らない)", () => {
    const { problems, notes } = selectionGateProblems(filled(), { validateContract: noContractProblems });
    expect(problems).toEqual([]);
    expect(notes).toHaveLength(1);
    expect(notes[0]).toContain("材料が渡されていない");
    expect(notes[0]).toContain("S-3〜S-8");
  });

  it("g5 契約に合わないときは突き合わせを回さない(**回していないと言う**)", () => {
    const { problems, notes } = selectionGateProblems(
      { adoptedBy: null },
      { validateContract: () => ["契約: 形が違う"], crossCheck: () => ["ここは回ってはいけない"] },
    );
    expect(problems.join("\n")).not.toContain("ここは回ってはいけない");
    expect(notes.join("\n")).toContain("回していない");
  });

  it("g6 全部そろえば通る(通る側も留める)", () => {
    const { problems, notes } = selectionGateProblems(filled(), {
      validateContract: noContractProblems,
      crossCheck: () => [],
    });
    expect(problems).toEqual([]);
    expect(notes).toEqual([]);
  });

  it("g7 突き合わせの誤りはそのまま出る(門が飲み込まない)", () => {
    const { problems } = selectionGateProblems(filled(), {
      validateContract: noContractProblems,
      crossCheck: () => ["S-3 p1[0](p1.1): packet の aggregates に無い id「x」"],
    });
    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain("S-3");
  });
});

describe("⑤ の選択の置き場(S-9 の道)", () => {
  it("g8 選択は **work の兄弟**(`out/<顧客>/exit/`)に置く", () => {
    const paths = exitSelectPaths("/w/out/c5");
    expect(paths.dir).toBe("/w/out/c5/exit");
    expect(paths.answerSelection).toBe("/w/out/c5/exit/answer_selection.json");
    expect(paths.selectionDraft).toBe("/w/out/c5/exit/answer_selection.draft.json");
    // **名前は 1 か所の表から**(写しを作らない)。
    expect(DELIVER_EXIT_NAMES.answerSelection).toBe("answer_selection.json");
    expect(DELIVER_EXIT_DIR).toBe("exit");
    // **下書きと本物を同じ名前にしない**(取り違えると採用を上書きする)。
    expect(paths.answerSelection).not.toBe(paths.selectionDraft);
  });

  it("g9 顧客のフォルダは**仮定にせず組の一覧で確かめる**", () => {
    expect(customerDirOf([{ work: "/w/out/c5/deliver1" }, { work: "/w/out/c5/pipe-3min" }])).toBe("/w/out/c5");
    // 親が 2 通りなら落ちる(「work の親が顧客」が崩れた形で黙って動かない)。
    expect(() => customerDirOf([{ work: "/w/out/c5/deliver1" }, { work: "/w/out/c9/deliver1" }])).toThrow(
      DeliverArgError,
    );
    expect(() => customerDirOf([])).toThrow(DeliverArgError);
    // 1 組だけでも通る。
    expect(customerDirOf([{ work: "/w/out/c5/deliver1" }])).toBe("/w/out/c5");
  });

  it("g9b **同じ顧客を違う字で渡しても 1 つに揃う**(`path.resolve` が利いている)", () => {
    // 【なぜ要るか】独立監査が当てた変異 ― `path.resolve` を外しても
    // **2277 本すべて緑**だった。g9 の材料が最初から絶対パスだけだったため。
    // **実際の運用は相対パスを渡している**(`--work out/c5/pipe-3min` の形)ので、
    // ここが緩むと**同じ顧客が 2 通りに見えて落ちる**。
    const absolute = path.join(process.cwd(), "out/c5/pipe-3min");
    expect(customerDirOf([{ work: "out/c5/deliver1" }, { work: absolute }])).toBe(
      path.join(process.cwd(), "out/c5"),
    );
    // 相対だけ・絶対だけでも同じ答え(片方だけ正規化する変異が黙らない)。
    expect(customerDirOf([{ work: "out/c5/deliver1" }])).toBe(path.join(process.cwd(), "out/c5"));
    expect(customerDirOf([{ work: absolute }])).toBe(path.join(process.cwd(), "out/c5"));
    // **違う顧客は揃わない**(正規化が「全部同じ」にしてしまわない)。
    expect(() => customerDirOf([{ work: "out/c5/deliver1" }, { work: "out/c9/deliver1" }])).toThrow(
      DeliverArgError,
    );
  });

  it("g10 段 `exit-select` は `exit-candidates` の**直前**で、人の確認点", () => {
    // **並びは字で留める**(「どこかに在る」では位置が留まらない)。
    const stages = [...DELIVER_STAGES];
    expect(stages[stages.indexOf("exit-candidates") - 1]).toBe("exit-select");
    expect(stages.indexOf("exit-select")).toBeGreaterThan(stages.indexOf("answer-pdf"));
    expect(stages.filter((stage) => stage === "exit-select")).toHaveLength(1);
  });
});
