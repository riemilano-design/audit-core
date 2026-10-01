// ⑤ の契約の試験(計画 docs/PLAN_EXIT_SELECT_2026-10-01.md の S-1)。
//
// 【「読めた」を証拠にしない】`eventSchema` は知らないキーワードで例外を投げるので「読めた」は言える。
// しかし**何を落とすか**は別に測る ― 壊した選択が落ちることを 1 本ずつ書く。
// 【人が決めたものは字で留める】欄の名前の一覧・正本の数(3 本・2 つ)・語の一覧を字で置く。
// 2026-10-01 に ⑧ で、定数から土台を作った試験が**その定数を動かす変異で 1 本も赤くならなかった**
// (レーン記録 §79)。同じ型を先に塞ぐ。
import { describe, expect, it } from "vitest";

import { SchemaKeywordError } from "./eventSchema.js";
import { ANSWER_MENU } from "./answerMenu.js";
import {
  ADOPTED_STATUSES,
  ANSWER_SELECTION_CONTRACT,
  ANSWER_SELECTION_SCHEMA_VERSION,
  BOARD_COUNT,
  P1_COUNT,
  STATUSES_NEEDING_OBSERVATION,
  type SelectionContext,
  aggregateIdsOf,
  itemRefKey,
  loadAnswerSelectionSchema,
  questionIdsOf,
  selectionProblems,
  statementByItemRefOf,
  validateAnswerSelection,
} from "./answerSelection.js";

/** 契約に合う最小の選択(5 人目の形。問い 1 件・`unanswerable`)。 */
function minimalSelection() {
  // **使い回さない。**最初は 1 つの object を 4 か所で共有していたため、
  // `s.lead.itemRef.hypothesisId = "I1"` が **4 か所を同時に書き換え**、
  // 「lead の守りを外す」変異が**他の場所の誤りで緑になった**(その場で当てた変異 U16・U17)。
  // 場所ごとに別の object を作り、**場所ごとの変異が場所ごとに赤くなる**ようにする。
  const itemRef = () => ({ seatIndex: 1, hypothesisId: "I-1-001" });
  return {
    contract: ANSWER_SELECTION_CONTRACT,
    schemaVersion: ANSWER_SELECTION_SCHEMA_VERSION,
    customerRef: "c5",
    packetId: "22aee8fe696d0262",
    runId: "558b8a81-20261001-2",
    runChoiceReason: "2 席が同じ周で立った唯一の周で、統合が実際に 2 席を見ている(司令塔の判断 2026-10-01)",
    lead: { itemRef: itemRef(), statementSource: "integration.representative" },
    p1: [
      { slot: "p1.1", aggregateIds: ["groups.core.games"], itemRef: itemRef(), readingRequired: true },
      { slot: "p1.2", aggregateIds: ["branches.total"], itemRef: itemRef(), readingRequired: true },
      { slot: "p1.3", aggregateIds: ["collapse.total"], itemRef: itemRef(), readingRequired: false },
    ],
    answers: [
      {
        questionId: "q1",
        // **人間の決定**(2026-10-01)。④ の `summary` は `partial` だった ― 写してはいけない。
        status: "unanswerable",
        machineSummary: "partial",
        itemRefs: [itemRef()],
        aggregateIds: ["groups.core.games"],
        neededObservation: {
          what: "普段の戦略を判定するための過去の対局集合",
          howToMeasure: "今回とは別の過去棋譜と同じ手順で型を取り、群の分かれ方を比べる",
        },
      },
    ],
    boards: [
      { slot: "p2.1", gameId: "g01", ply: 48, packetRef: "facts.engine[0]" },
      { slot: "p2.2", gameId: "g07", ply: 62, packetRef: "facts.engine[31]" },
    ],
    actions: [{ slot: "act.1", menuId: "M4", itemRef: itemRef() }],
    // **空の配列に型を書く。**書かないと `never[]` に推論され、
    // 後の試験が `humanQueue` に行を入れるところで `tsc` が落ちる(**門の 1 本が壊れる**)。
    // vitest は通るので、**型検査を回さないと気づかない**(独立監査が実測。2026-10-01)。
    humanQueue: [] as { itemRef: { seatIndex: number; hypothesisId: string }; actionCandidateText: string; why: string }[],
    adoptedBy: { who: "commander", at: "2026-10-01T00:00:00Z", basis: "検証を通り、問いに合う候補を採った" },
  };
}

/** schema の木を歩いて、object の節と property の名前を集める。 */
function walkSchema(node: unknown, out: { objects: Record<string, unknown>[]; names: string[]; keys: string[] }) {
  if (node === null || typeof node !== "object" || Array.isArray(node)) return;
  const map = node as Record<string, unknown>;
  for (const key of Object.keys(map)) out.keys.push(key);
  if (map["type"] === "object") out.objects.push(map);
  const props = map["properties"];
  if (props && typeof props === "object") {
    for (const [name, child] of Object.entries(props as Record<string, unknown>)) {
      out.names.push(name);
      walkSchema(child, out);
    }
  }
  const items = map["items"];
  if (items) walkSchema(items, out);
}

function schemaWalk() {
  const out: { objects: Record<string, unknown>[]; names: string[]; keys: string[] } = {
    objects: [],
    names: [],
    keys: [],
  };
  walkSchema(loadAnswerSelectionSchema(), out);
  return out;
}

describe("answer-selection.v0.1 の契約(S-1)", () => {
  it("s1 スキーマが読める(知らないキーワードで例外にならない)", () => {
    expect(() => loadAnswerSelectionSchema()).not.toThrow();
    expect(() => validateAnswerSelection(minimalSelection())).not.toThrow();
  });

  it("s2 最小の選択は通る(5 人目の形。問い 1 件・unanswerable)", () => {
    expect(validateAnswerSelection(minimalSelection())).toEqual([]);
  });

  it("s3 **欄の名前の一覧を字で留める**(足しても減らしても赤)", () => {
    // **人が決めた表面**なので字で置く。`additionalProperties: false` は「知らない欄を通さない」だけで、
    // **欄が増えたこと・減ったこと自体**は見ない ― そこをここで留める。
    expect([...new Set(schemaWalk().names)].sort()).toEqual(
      [
        "actionCandidateText",
        "actions",
        "adoptedBy",
        "aggregateIds",
        "answers",
        "at",
        "basis",
        "boards",
        "contract",
        "customerRef",
        "gameId",
        "howToMeasure",
        "humanQueue",
        "hypothesisId",
        "itemRef",
        "itemRefs",
        "lead",
        "machineSummary",
        "menuId",
        "neededObservation",
        "p1",
        "packetId",
        "packetRef",
        "ply",
        "questionId",
        "readingRequired",
        "runChoiceReason",
        "runId",
        "schemaVersion",
        "seatIndex",
        "slot",
        "statementSource",
        "status",
        "what",
        "who",
        "why",
      ].sort(),
    );
  });

  it("s4 **`internal` の欄がどこにも無い**(規則 8 の (3)。⑥ の入口にも掛ける)", () => {
    expect(schemaWalk().names).not.toContain("internal");
    // 綴りを変えた抜け道も見る(`internalNotes` のような名前)。
    expect(schemaWalk().names.filter((n) => n.toLowerCase().includes("internal"))).toEqual([]);
    expect(schemaWalk().names.filter((n) => n.toLowerCase().includes("reasoning"))).toEqual([]);
  });

  it("s5 **席の数の欄が無い**(一致を証拠にしない。規則 8 の (2))", () => {
    const names = schemaWalk().names;
    // `seatIndex` は席の**番号**なので在ってよい。**数える欄**が無いことを見る。
    expect(names).not.toContain("seatCount");
    expect(names.filter((n) => /count$/i.test(n))).toEqual([]);
    expect(names).toContain("seatIndex");
  });

  it("s6 **object の節はすべて `additionalProperties: false`**(知らない欄を通さない)", () => {
    const objects = schemaWalk().objects;
    expect(objects.length).toBeGreaterThanOrEqual(8);
    for (const node of objects) {
      expect(node["additionalProperties"], JSON.stringify(Object.keys(node["properties"] ?? {}))).toBe(false);
    }
  });

  it("s7 **数の欄は席の番号と手数だけ**(集計の数を契約に書かない)", () => {
    // 数を書くと「途中の編集で数字が変わった」の道ができる。**数は ⑥ が packet から引く。**
    const numeric: string[] = [];
    const walk = (node: unknown, name: string) => {
      if (node === null || typeof node !== "object" || Array.isArray(node)) return;
      const map = node as Record<string, unknown>;
      if (map["type"] === "integer" || map["type"] === "number") numeric.push(name);
      for (const [childName, child] of Object.entries((map["properties"] ?? {}) as Record<string, unknown>)) {
        walk(child, childName);
      }
      if (map["items"]) walk(map["items"], name);
    };
    walk(loadAnswerSelectionSchema(), "(根)");
    expect([...new Set(numeric)].sort()).toEqual(["ply", "seatIndex"]);
  });

  it("s8 契約の名前と版が違う選択は落ちる", () => {
    const wrongName = { ...minimalSelection(), contract: "answer-selection-v2" };
    expect(validateAnswerSelection(wrongName).join("\n")).toContain("answer-selection-v2");
    const wrongVersion = { ...minimalSelection(), schemaVersion: "0.2" };
    expect(validateAnswerSelection(wrongVersion).join("\n")).toContain("0.2");
  });

  it("s9 知らない欄を足すと落ちる(`internal` も含む)", () => {
    const withInternal = { ...minimalSelection(), internal: { reasoning: "席の内部推論" } };
    expect(validateAnswerSelection(withInternal).join("\n")).toContain("internal");
    const withSeatCount = { ...minimalSelection(), seatCount: 2 };
    expect(validateAnswerSelection(withSeatCount).join("\n")).toContain("seatCount");
  });

  it("s10 **`status` は 3 語・`machineSummary` は 5 語**(語を字で留める)", () => {
    expect([...ADOPTED_STATUSES]).toEqual(["answered", "partial", "unanswerable"]);
    const schema = loadAnswerSelectionSchema() as {
      properties: { answers: { items: { properties: Record<string, { enum?: string[] }> } } };
    };
    const answerProps = schema.properties.answers.items.properties;
    expect(answerProps["status"]?.enum).toEqual(["answered", "partial", "unanswerable"]);
    expect(answerProps["machineSummary"]?.enum).toEqual([
      "answered",
      "partial",
      "unanswerable",
      "mixed",
      "no_seat",
    ]);
    // **5 語を 3 語に落としてはいけない**(機械の読みを捨てない。S-5b)。
    expect(answerProps["machineSummary"]?.enum).toContain("mixed");
    expect(answerProps["machineSummary"]?.enum).toContain("no_seat");
    expect(answerProps["status"]?.enum).not.toContain("mixed");
  });

  it("s11 `status` に 5 語の方の語を入れると落ちる(`mixed`・`no_seat`)", () => {
    for (const bad of ["mixed", "no_seat"]) {
      const selection = minimalSelection();
      selection.answers[0]!.status = bad;
      expect(validateAnswerSelection(selection).join("\n")).toContain(bad);
    }
  });

  it("s12 **機械の読みは残す** ― `machineSummary` が無ければ落ちる", () => {
    const selection = minimalSelection() as unknown as { answers: Record<string, unknown>[] };
    delete selection.answers[0]!.machineSummary;
    expect(validateAnswerSelection(selection).join("\n")).toContain("machineSummary");
  });

  it("s13 slot の字が語彙の外だと落ちる(`p1.4`・`p2.3`・`act.0`)", () => {
    const bad: [string, (s: ReturnType<typeof minimalSelection>) => void][] = [
      ["p1.4", (s) => { s.p1[0]!.slot = "p1.4"; }],
      ["p1.lead", (s) => { s.p1[0]!.slot = "p1.lead"; }],
      ["p2.3", (s) => { s.boards[0]!.slot = "p2.3"; }],
      ["act.0", (s) => { s.actions[0]!.slot = "act.0"; }],
    ];
    for (const [label, mutate] of bad) {
      const selection = minimalSelection();
      mutate(selection);
      expect(validateAnswerSelection(selection).join("\n"), label).toContain(label);
    }
  });

  it("s14 退化した文字が落ちる ― **欄ごとに両側で、場所を名指しして**(2026-10-01 に 2 度踏んだ型)", () => {
    // 【両側で校正する】最初は `customerRef` に `"::"` だけを当てていた ― **2 文字で英数字が無い**ので
    // `pattern` が先に捕まえ、**`minLength` を外す変異が黙った**(変異 U8)。
    // だから守りのある欄ごとに、**`minLength` だけが効く値**と **`pattern` だけが効く値**を並べる。
    // 【場所を名指しする】値だけを照合すると、**別の欄の誤りで緑になる** ―
    // 土台の `itemRef` を 1 つ使い回していたとき、`lead` の守りを外す変異が他の場所の誤りで黙った(変異 U16)。
    const cases: [string, string, (s: ReturnType<typeof minimalSelection>) => void][] = [
      // [落ちるはずの字, 誤りに出るはずの場所, 当てる]
      ["c", ".customerRef", (s) => { s.customerRef = "c"; }],
      ["::", ".customerRef", (s) => { s.customerRef = "::"; }],
      ["ab", ".runId", (s) => { s.runId = "ab"; }],
      ["::::", ".runId", (s) => { s.runId = "::::"; }],
      ["xy", ".p1[0].aggregateIds[0]", (s) => { s.p1[0]!.aggregateIds = ["xy"]; }],
      [";;;;", ".p1[0].aggregateIds[0]", (s) => { s.p1[0]!.aggregateIds = [";;;;"]; }],
      ["g", ".boards[0].gameId", (s) => { s.boards[0]!.gameId = "g"; }],
      ["--", ".boards[0].gameId", (s) => { s.boards[0]!.gameId = "--"; }],
      ["I1", ".lead.itemRef.hypothesisId", (s) => { s.lead.itemRef.hypothesisId = "I1"; }],
      ["-/-", ".lead.itemRef.hypothesisId", (s) => { s.lead.itemRef.hypothesisId = "-/-"; }],
      // **4 か所の `itemRef` を 1 つずつ当てる**(写しが 4 つあるので、1 つだけ守りを外す変異が黙らない)。
      ["P1", ".p1[0].itemRef.hypothesisId", (s) => { s.p1[0]!.itemRef.hypothesisId = "P1"; }],
      ["A1", ".answers[0].itemRefs[0].hypothesisId", (s) => { s.answers[0]!.itemRefs[0]!.hypothesisId = "A1"; }],
      ["C1", ".actions[0].itemRef.hypothesisId", (s) => { s.actions[0]!.itemRef.hypothesisId = "C1"; }],
      // 長さだけの守り(pattern を持たない欄)。
      ["短い", ".runChoiceReason", (s) => { s.runChoiceReason = "短い"; }],
      ["あ", ".answers[0].neededObservation.what", (s) => { s.answers[0]!.neededObservation!.what = "あ"; }],
    ];
    for (const [label, where, mutate] of cases) {
      const selection = minimalSelection();
      mutate(selection);
      const problems = validateAnswerSelection(selection);
      // **ちょうど 1 件**(場所を 1 つだけ壊したので、2 件以上なら土台が使い回されている)。
      expect(problems, `${label} @ ${where}`).toHaveLength(1);
      expect(problems[0], `${label} @ ${where}`).toContain(where);
      expect(problems[0], `${label} @ ${where}`).toContain(label);
    }
    // **通る側**も留める: 守りの境目(`minLength` ちょうど)は通る。
    const atLimit = minimalSelection();
    atLimit.customerRef = "c5";            // 2 文字(customerRef の下限)
    atLimit.p1[0]!.aggregateIds = ["abc"]; // 3 文字(下限)
    expect(validateAnswerSelection(atLimit)).toEqual([]);
  });

  it("s21 **4 か所の `itemRef` の形がそろっている**($ref が無いので展開してある)", () => {
    // 検証器は `$ref` を扱わないので `itemRef` の形が **4 か所に写してある**。
    // 写しが増えても減っても**形が食い違ったら赤**にする(1 か所だけ緩める変異を、場所を当てずに捕まえる)。
    const schema = loadAnswerSelectionSchema() as Record<string, never>;
    const found: [string, unknown][] = [];
    const walk = (node: unknown, path: string) => {
      if (node === null || typeof node !== "object" || Array.isArray(node)) return;
      const map = node as Record<string, unknown>;
      for (const [name, child] of Object.entries((map["properties"] ?? {}) as Record<string, unknown>)) {
        if (name === "itemRef" || name === "itemRefs") {
          const shape = name === "itemRefs" ? (child as Record<string, unknown>)["items"] : child;
          found.push([`${path}.${name}`, shape]);
        } else {
          walk(child, `${path}.${name}`);
        }
      }
      if (map["items"]) walk(map["items"], `${path}[]`);
    };
    walk(schema, "");
    // **4 か所**(lead・p1・answers・actions)+ humanQueue = 5 か所。字で留める。
    expect(found.map(([p]) => p).sort()).toEqual(
      [
        ".actions[].itemRef",
        ".answers[].itemRefs",
        ".humanQueue[].itemRef",
        ".lead.itemRef",
        ".p1[].itemRef",
      ].sort(),
    );
    const first = JSON.stringify(found[0]![1]);
    for (const [where, shape] of found) {
      expect(JSON.stringify(shape), where).toBe(first);
    }
  });

  it("s15 `packetId` が 16 桁の 16 進でないと落ちる(封の符号)", () => {
    const selection = minimalSelection();
    selection.packetId = "22aee8fe";
    expect(validateAnswerSelection(selection).join("\n")).toContain("22aee8fe");
  });

  it("s16 `adoptedBy` が無い・空だと落ちる(機械が埋めない欄)", () => {
    const missing = minimalSelection() as unknown as Record<string, unknown>;
    delete missing.adoptedBy;
    expect(validateAnswerSelection(missing).join("\n")).toContain("adoptedBy");
    const emptyBasis = minimalSelection();
    emptyBasis.adoptedBy.basis = "";
    expect(validateAnswerSelection(emptyBasis).join("\n")).toContain("basis");
    const wrongWho = minimalSelection();
    emptyBasis.adoptedBy.basis = "ある";
    wrongWho.adoptedBy.who = "llm";
    expect(validateAnswerSelection(wrongWho).join("\n")).toContain("llm");
  });

  it("s17 `menuId` の形が M1〜M9 の形でないと落ちる(実在の照合は道具の S-6)", () => {
    const selection = minimalSelection();
    selection.actions[0]!.menuId = "M99";
    expect(validateAnswerSelection(selection).join("\n")).toContain("M99");
    // **9 件の一覧を schema に写していないこと**(写すと表が変わったとき黙ってずれる)。
    const schema = loadAnswerSelectionSchema() as {
      properties: { actions: { items: { properties: { menuId: Record<string, unknown> } } } };
    };
    expect(schema.properties.actions.items.properties.menuId["enum"]).toBeUndefined();
    expect(schema.properties.actions.items.properties.menuId["pattern"]).toBe("^M[1-9]$");
  });

  it("s18 **正本の数を字で留める**(p1 は 3 本・盤は 2 つ)", () => {
    expect(P1_COUNT).toBe(3);
    expect(BOARD_COUNT).toBe(2);
    // **近くの数と同じにしない**(取り違えを落とす)。
    expect(P1_COUNT).not.toBe(BOARD_COUNT);
    for (const near of [1, 4, 5, 9, 25]) {
      expect(P1_COUNT).not.toBe(near);
      expect(BOARD_COUNT).not.toBe(near);
    }
    // schema の下限もこの数(**上限は検証器に maxItems が無いので道具が数える**)。
    const schema = loadAnswerSelectionSchema() as {
      properties: { p1: Record<string, unknown>; boards: Record<string, unknown> };
    };
    expect(schema.properties.p1["minItems"]).toBe(3);
    expect(schema.properties.boards["minItems"]).toBe(2);
  });

  it("s19 `neededObservation` が要る status を字で留める", () => {
    expect([...STATUSES_NEEDING_OBSERVATION]).toEqual(["partial", "unanswerable"]);
    expect([...STATUSES_NEEDING_OBSERVATION]).not.toContain("answered");
  });

  it("s20 検証器が扱わないキーワードを schema に書いていない($ref・maxItems・anyOf)", () => {
    // 書くと `SchemaKeywordError` で**例外**になる(黙って無視されない)が、
    // **読めることだけを見る試験は、例外の道を通らない**ので、キーワードの字も見る。
    const keys = new Set(schemaWalk().keys);
    for (const unsupported of ["$ref", "$defs", "maxItems", "anyOf", "allOf", "not", "multipleOf"]) {
      expect(keys.has(unsupported), unsupported).toBe(false);
    }
    expect(() => validateAnswerSelection({}, loadAnswerSelectionSchema())).not.toThrow(SchemaKeywordError);
  });
});

describe("⑤ 材料との突き合わせ(S-3〜S-8)", () => {
  // 【合成の材料】`out/` の実データは gitignore なので試験では読まない
  //(`check_structure_test.py` と同じ流儀)。**実物での測りは別に回して記録に書く。**
  const AGG = ["groups.core.games", "branches.total", "collapse.total", "side_match.attack"];
  const ITEM_REFS: [number, string][] = [
    [1, "I-1-001"],
    [1, "I-1-002"],
    [2, "I-2-001"],
    [2, "I-2-009"], // statement が空の束(S-7 を当てるため)
  ];

  function contextOf(over: Partial<SelectionContext> = {}): SelectionContext {
    const statements = new Map<string, string>();
    for (const [seatIndex, hypothesisId] of ITEM_REFS) {
      statements.set(
        itemRefKey({ seatIndex, hypothesisId }),
        hypothesisId === "I-2-009" ? "" : `${hypothesisId} の読み`,
      );
    }
    return {
      aggregateIds: new Set(AGG),
      statementByItemRef: statements,
      questionIds: ["q1"],
      menuIds: new Set(["M1", "M4", "M9"]),
      ...over,
    };
  }

  /** 契約にも通る選択(突き合わせも通る)。 */
  function okSelection() {
    const selection = minimalSelection();
    selection.answers[0]!.aggregateIds = ["groups.core.games"];
    return selection;
  }

  it("t1 材料に合う選択は問題なし(**まず通る側を留める**)", () => {
    expect(validateAnswerSelection(okSelection())).toEqual([]);
    expect(selectionProblems(okSelection(), contextOf())).toEqual([]);
  });

  it("t2 S-3 packet に無い aggregateId は落ちる(**場所を名指しする**)", () => {
    const selection = okSelection();
    selection.p1[1]!.aggregateIds = ["groups.core.games", "time.midOver"];
    const problems = selectionProblems(selection, contextOf());
    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain("S-3");
    expect(problems[0]).toContain("p1[1](p1.2)");
    expect(problems[0]).toContain("time.midOver");
    // **答えの側でも別に落ちる**(片方だけ見る変異が黙らない)。
    const inAnswer = okSelection();
    inAnswer.answers[0]!.aggregateIds = ["time.midOver"];
    const answerProblems = selectionProblems(inAnswer, contextOf());
    expect(answerProblems).toHaveLength(1);
    expect(answerProblems[0]).toContain("answers[0](q1)");
  });

  it("t3 S-4 統合に無い itemRef は落ちる ― **5 か所を 1 つずつ**", () => {
    const places: [string, (s: ReturnType<typeof okSelection>) => void][] = [
      ["lead.itemRef", (s) => { s.lead.itemRef.hypothesisId = "I-9-999"; }],
      ["p1[0](p1.1).itemRef", (s) => { s.p1[0]!.itemRef.hypothesisId = "I-9-999"; }],
      ["answers[0](q1).itemRefs[0]", (s) => { s.answers[0]!.itemRefs[0]!.hypothesisId = "I-9-999"; }],
      ["actions[0](act.1).itemRef", (s) => { s.actions[0]!.itemRef.hypothesisId = "I-9-999"; }],
    ];
    for (const [where, mutate] of places) {
      const selection = okSelection();
      mutate(selection);
      const problems = selectionProblems(selection, contextOf());
      expect(problems, where).toHaveLength(1);
      expect(problems[0], where).toContain("S-4");
      expect(problems[0], where).toContain(where);
    }
    // humanQueue も見る(**冊子に出ないが、指している先は在るはず**)。
    const withQueue = okSelection();
    withQueue.humanQueue = [
      { itemRef: { seatIndex: 9, hypothesisId: "I-9-999" }, actionCandidateText: "ある候補の文", why: "menuMatch: null" },
    ];
    const queueProblems = selectionProblems(withQueue, contextOf());
    expect(queueProblems).toHaveLength(1);
    expect(queueProblems[0]).toContain("humanQueue[0].itemRef");
  });

  it("t4 S-4 **席の番号だけが違う itemRef も落ちる**(鍵は組で引く)", () => {
    const selection = okSelection();
    selection.lead.itemRef.seatIndex = 2; // 2/I-1-001 は統合に無い(1/I-1-001 は在る)
    const problems = selectionProblems(selection, contextOf());
    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain("2/I-1-001");
  });

  it("t5 p1 は**ちょうど 3 本**(多くても少なくても落ちる)", () => {
    const few = okSelection();
    few.p1 = few.p1.slice(0, 2);
    expect(selectionProblems(few, contextOf()).join("\n")).toContain("p1 が 2 本");
    const many = okSelection();
    many.p1 = [...many.p1, { slot: "p1.1", aggregateIds: ["branches.total"], itemRef: { seatIndex: 1, hypothesisId: "I-1-002" }, readingRequired: false }];
    const manyProblems = selectionProblems(many, contextOf()).join("\n");
    expect(manyProblems).toContain("p1 が 4 本");
    // **slot の重なりも別に言う**(本数だけ見る変異が黙らない)。
    expect(manyProblems).toContain("重なっている");
  });

  it("t6 boards は**ちょうど 2 つ**", () => {
    const one = okSelection();
    one.boards = one.boards.slice(0, 1);
    expect(selectionProblems(one, contextOf()).join("\n")).toContain("boards が 1 つ");
    const three = okSelection();
    three.boards = [...three.boards, { slot: "p2.1", gameId: "g09", ply: 30, packetRef: "facts.engine[9]" }];
    expect(selectionProblems(three, contextOf()).join("\n")).toContain("boards が 3 つ");
  });

  it("t7 S-5 問いごとにちょうど 1 行(0 行・2 行・request に無い問い)", () => {
    const none = okSelection();
    none.answers = [];
    expect(selectionProblems(none, contextOf()).join("\n")).toContain("問い q1 の行が 0 件");
    const twice = okSelection();
    twice.answers = [twice.answers[0]!, { ...twice.answers[0]!, itemRefs: [{ seatIndex: 1, hypothesisId: "I-1-001" }] }];
    expect(selectionProblems(twice, contextOf()).join("\n")).toContain("問い q1 の行が 2 件");
    const unknown = okSelection();
    unknown.answers[0]!.questionId = "q7";
    const unknownProblems = selectionProblems(unknown, contextOf()).join("\n");
    expect(unknownProblems).toContain("問い q1 の行が 0 件");
    expect(unknownProblems).toContain("request に無い問い「q7」");
  });

  it("t8 S-5 問いが 2 件の顧客では 2 行要る(1 件の形に固めない)", () => {
    const ctx = contextOf({ questionIds: ["q1", "q2"] });
    const selection = okSelection();
    expect(selectionProblems(selection, ctx).join("\n")).toContain("問い q2 の行が 0 件");
    selection.answers = [
      selection.answers[0]!,
      { ...selection.answers[0]!, questionId: "q2", itemRefs: [{ seatIndex: 2, hypothesisId: "I-2-001" }] },
    ];
    expect(selectionProblems(selection, ctx)).toEqual([]);
  });

  it("t9 S-6 承認済みの表に無い menuId は落ちる(**表は道具が持つ**)", () => {
    const selection = okSelection();
    selection.actions[0]!.menuId = "M5"; // 合成の表には無い
    const problems = selectionProblems(selection, contextOf());
    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain("S-6");
    expect(problems[0]).toContain("M5");
    expect(problems[0]).toContain("humanQueue");
    // 表に在るものは通る。
    const ok = okSelection();
    ok.actions[0]!.menuId = "M9";
    expect(selectionProblems(ok, contextOf())).toEqual([]);
  });

  it("t10 S-6 **本物の表(M1〜M9)の 9 件を字で留める**(表が縮んでも気づく)", () => {
    expect(ANSWER_MENU.map((item) => item.id)).toEqual(["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"]);
    expect(ANSWER_MENU).toHaveLength(9);
  });

  it("t11 S-7 readingRequired なのに代表の statement が空だと落ちる", () => {
    const selection = okSelection();
    selection.p1[0]!.itemRef = { seatIndex: 2, hypothesisId: "I-2-009" }; // statement が空の束
    selection.p1[0]!.readingRequired = true;
    const problems = selectionProblems(selection, contextOf());
    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain("S-7");
    expect(problems[0]).toContain("p1[0](p1.1)");
    // **readingRequired が false なら通る**(数だけの行を禁じているのではない)。
    const notRequired = okSelection();
    notRequired.p1[0]!.itemRef = { seatIndex: 2, hypothesisId: "I-2-009" };
    notRequired.p1[0]!.readingRequired = false;
    expect(selectionProblems(notRequired, contextOf())).toEqual([]);
  });

  it("t12 S-8 partial / unanswerable は neededObservation が要る", () => {
    for (const status of ["partial", "unanswerable"]) {
      const selection = okSelection() as unknown as { answers: Record<string, unknown>[] };
      selection.answers[0]!.status = status;
      delete selection.answers[0]!.neededObservation;
      const problems = selectionProblems(selection, contextOf());
      expect(problems, status).toHaveLength(1);
      expect(problems[0], status).toContain("neededObservation が無い");
      expect(problems[0], status).toContain(status);
    }
  });

  it("t13 S-8 answered なのに neededObservation が在ると落ちる(余った向き)", () => {
    const selection = okSelection();
    selection.answers[0]!.status = "answered";
    const problems = selectionProblems(selection, contextOf());
    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain("なのに neededObservation が在る");
  });

  it("t14 S-8 neededObservation に数が入ると落ちる(半角・全角の両方)", () => {
    for (const text of ["25 局の比較", "２５局の比較", "過去 1 年の棋譜"]) {
      const selection = okSelection();
      selection.answers[0]!.neededObservation = { what: text, howToMeasure: "別の棋譜で同じ手順を回す" };
      const problems = selectionProblems(selection, contextOf());
      expect(problems, text).toHaveLength(1);
      expect(problems[0], text).toContain("数が入っている");
      expect(problems[0], text).toContain(".what");
    }
    // **howToMeasure の側も別に見る**(片方だけ見る変異が黙らない)。
    const other = okSelection();
    other.answers[0]!.neededObservation = { what: "過去の対局集合", howToMeasure: "直近 50 局で比べる" };
    const problems = selectionProblems(other, contextOf());
    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain(".howToMeasure");
  });

  it("t15 **人間が書いた 5 人目の答えが通る**(数を含まない文で書けること)", () => {
    // 人間の文は「今回とは別の過去棋譜との比較が必要です」で**数を持たない**。
    const selection = okSelection();
    selection.answers[0]!.status = "unanswerable";
    selection.answers[0]!.neededObservation = {
      what: "普段の戦略を判定するための過去の対局集合",
      howToMeasure: "今回とは別の過去棋譜と同じ手順で型を取り、群の分かれ方を比べる",
    };
    expect(validateAnswerSelection(selection)).toEqual([]);
    expect(selectionProblems(selection, contextOf())).toEqual([]);
    // **機械の読みは `partial` のまま残っている**(採用と並べて記録する)。
    expect(selection.answers[0]!.machineSummary).toBe("partial");
    expect(selection.answers[0]!.status).not.toBe(selection.answers[0]!.machineSummary);
  });

  it("t17 S-5 **既知の id を前方に含む問い**は「request に無い」で落ちる(前方一致に緩めない)", () => {
    // 【なぜ要るか】独立監査が当てた変異 ― `questionIds.includes(questionId)` を
    // `some((known) => questionId.startsWith(known))` に緩めても **37 本が緑のまま**だった。
    // schema の `questionId` は `^q[1-9][0-9]*$` で **2 桁以上を許す**ので、
    // `q1` を持つ顧客の選択に `q11` の行が混ざっても、前方一致なら通ってしまう。
    // (同じ型を 2026-10-01 に席の鍵の照合でも踏んでいる ― 前方一致は閉じる。)
    const selection = okSelection();
    selection.answers[0]!.questionId = "q11";
    const problems = selectionProblems(selection, contextOf({ questionIds: ["q1"] }));
    expect(problems.join("\n")).toContain("request に無い問い「q11」");
    // **逆側**も留める: `q11` の顧客に `q1` の行が来ても落ちる(前方一致の向きを両方塞ぐ)。
    const other = okSelection();
    other.answers[0]!.questionId = "q1";
    expect(selectionProblems(other, contextOf({ questionIds: ["q11"] })).join("\n")).toContain(
      "request に無い問い「q1」",
    );
  });

  it("t18 S-7 **空白だけの statement** も「読みが無い」で落ちる(`trim` を留める)", () => {
    // 【なぜ要るか】独立監査が当てた変異 ― `statement.trim() === ""` の `trim` を外しても
    // **37 本が緑のまま**だった。空文字の束しか土台に無かったため。
    const statements = new Map(contextOf().statementByItemRef);
    statements.set(itemRefKey({ seatIndex: 2, hypothesisId: "I-2-009" }), "   \u3000\n  ");
    const selection = okSelection();
    selection.p1[0]!.itemRef = { seatIndex: 2, hypothesisId: "I-2-009" };
    selection.p1[0]!.readingRequired = true;
    const problems = selectionProblems(selection, contextOf({ statementByItemRef: statements }));
    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain("S-7");
    expect(problems[0]).toContain("p1[0](p1.1)");
    // **通る側**: 1 文字でも字が在れば通る(「空白だけ」を落としているのであって、短さではない)。
    const short = new Map(statements);
    short.set(itemRefKey({ seatIndex: 2, hypothesisId: "I-2-009" }), " あ ");
    expect(selectionProblems(selection, contextOf({ statementByItemRef: short }))).toEqual([]);
  });

  it("t16 材料の作り方(実物の形から id を取る)", () => {
    expect([...aggregateIdsOf({ aggregates: [{ id: "a.b" }, { id: "c.d" }, { noId: 1 }] })]).toEqual(["a.b", "c.d"]);
    expect(questionIdsOf({ customerQuestions: [{ id: "q1" }, { id: "q2" }] })).toEqual(["q1", "q2"]);
    const statements = statementByItemRefOf({
      clusters: [
        { itemRefs: [{ seatIndex: 1, hypothesisId: "I-1-001" }], representative: { statement: "ある読み" } },
        { itemRefs: [{ seatIndex: 2, hypothesisId: "I-2-001" }], representative: {} },
      ],
    });
    expect(statements.get("1/I-1-001")).toBe("ある読み");
    expect(statements.get("2/I-2-001")).toBe("");
    expect(statements.has("3/I-3-001")).toBe(false);
    // **欄が無い・形が違う材料で黙って空にならない**(空の材料なら照合は全部落ちる側へ行く)。
    expect(aggregateIdsOf({}).size).toBe(0);
    expect(questionIdsOf({})).toEqual([]);
    expect(statementByItemRefOf({}).size).toBe(0);
  });
});
