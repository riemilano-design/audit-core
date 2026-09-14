// STEP U6-O: 材料から文を組み立てる純粋関数のテスト。
//
// 【このテストが確かめないこと(先に書く。docs/STEP_U6-O_PLAN_2026-09-13.md 6.2)】
// - **「文が自然か」は測れない。** 日本語として読めるか、初心者に伝わるか、
//   コーパスの語り口に似ているかは、ここでは一切確かめていない。
// - **「材料の組み合わせが将棋として意味のある区別か」も測れない。**
// - **したがって、このテストが緑であることは「文が良いこと」を意味しない。**
//   「禁止したものが出ていない」「3種類の無いを混ぜていない」「材料が決めたスロットに出る」だけである。

import { describe, expect, it } from "vitest";
import type { Role } from "shogiops/types";

import { roleToJapanese } from "./pieceMapping.js";
import { computePvMaterials, type PvMaterialRules, type PvMaterials, type PvMaterialsResult } from "./pvMaterials.js";
import { buildPvSentences, type PvSentenceResult, type SentenceRules } from "./pvSentence.js";

/** 文にする材料をすべて使う規則。**既定値が無いので、テスト側が必ず全部書く。** */
const ALL: SentenceRules = {
  initiative: "first_capture",
  minPliesForAbsence: 4,
  use: {
    slot1: ["firstCapture", "firstContactPly"],
    slot2: ["firstCheck", "firstPromotion", "bishopExchangePly", "firstDrop", "kingMovePlies"],
    slot3: ["capturedRoles", "kingNeighborDelta", "advanceRetreat", "slidingReachDelta"],
  },
};

function emptyMaterials(): PvMaterials {
  return {
    firstCapture: null,
    firstContactPly: null,
    capturedRoles: { us: new Map<Role, number>(), opponent: new Map<Role, number>() },
    handDelta: { us: new Map<Role, number>(), opponent: new Map<Role, number>() },
    kingNeighborDelta: { us: 0, opponent: 0 },
    firstCheck: null,
    firstPromotion: null,
    bishopExchangePly: null,
    firstDrop: null,
    kingMovePlies: { us: [], opponent: [] },
    advanceRetreat: { us: { up: 0, down: 0, side: 0 }, opponent: { up: 0, down: 0, side: 0 } },
    slidingReachDelta: { us: 0, opponent: 0 },
  };
}

function measured(overrides: Partial<PvMaterials>, opts?: { usablePlies?: number; truncatedAtPly?: number | null }): PvMaterialsResult {
  return {
    kind: "measured",
    pvLength: 12,
    usablePlies: opts?.usablePlies ?? 12,
    truncatedAtPly: opts?.truncatedAtPly ?? null,
    materials: { ...emptyMaterials(), ...overrides },
  };
}

function textOf(r: PvSentenceResult): string {
  return r.kind === "text" ? r.sentences.join("") : "";
}

describe("buildPvSentences ― 3種類の「無い」を分ける(規則11.6)", () => {
  it("読み筋が短くて測れなかった行は not_measured(「起きなかった」ではない)", () => {
    const r = buildPvSentences({ kind: "insufficient", pvLength: 1, usablePlies: 1, reason: "pv_too_short" }, ALL);
    expect(r).toEqual({ kind: "not_measured", reason: "pv_too_short" });
  });

  it("測って無かった(手数は十分)なら「ぶつからない」と言ってよい", () => {
    const r = buildPvSentences(measured({}, { usablePlies: 12 }), ALL);
    expect(r.kind).toBe("text");
    expect(textOf(r)).toContain("しばらく駒はぶつからない");
  });

  // ここが本題。同じ null でも、手数が足りなければ「無かった」と言ってはいけない。
  it("材料が null でも再生手数が足りなければ not_measured(同じ値でも意味が違う)", () => {
    const r = buildPvSentences(measured({}, { usablePlies: 2 }), ALL);
    expect(r).toEqual({ kind: "not_measured", reason: "too_few_plies_for_absence" });
  });

  it("接触はあっても再生手数が足りなければ「取り合いにはならない」とは言わない(否定の文)", () => {
    expect(buildPvSentences(measured({ firstContactPly: 1 }, { usablePlies: 3 }), ALL)).toEqual({
      kind: "not_measured",
      reason: "too_few_plies_for_absence",
    });
  });

  it("firstContactPly が 0(rootで既にぶつかっている)を null と同じに扱わない", () => {
    const r = buildPvSentences(measured({ firstContactPly: 0 }), ALL);
    expect(textOf(r)).toContain("駒はぶつかります");
    expect(textOf(r)).not.toContain("ぶつからない");
  });

  it("text のときの sentences は必ず1つ以上(空配列を「無い」に使わない)", () => {
    const r = buildPvSentences(measured({ firstCheck: { ply: 3, byUs: false } }), ALL);
    expect(r.kind).toBe("text");
    if (r.kind === "text") expect(r.sentences.length).toBeGreaterThan(0);
  });
});

// 【中心(独立監査 2 回目の必須 C。規則 11.8)】
// この STEP の中心は「どの材料を、どのスロットの文に出すか」である。当初の試験は
// 「文が変わる」「禁止語が出ない」だけを見ており、**材料11 をスロット3→2、材料6 を 2→3、
// 材料5 をガードごと 3→2 へ移しても、すべて緑のままだった。** そこで材料ごとに、
// 期待するスロットの文(「途中で、」か「そのあと、」か、どちらでもないか)に現れることを見る。
describe("buildPvSentences ― 材料ごとに、決めたスロットの文に出る(中心)", () => {
  /** 文の書き出しでスロットを見分ける。スロット2 は「途中で、」、3 は「そのあと、」、1 はどちらでもない。 */
  function slotOf(sentence: string): 1 | 2 | 3 {
    if (sentence.startsWith("途中で、")) return 2;
    if (sentence.startsWith("そのあと、")) return 3;
    return 1;
  }

  const cases: Array<{ material: string; input: PvMaterialsResult; fragment: string; slot: 1 | 2 | 3 }> = [
    { material: "1 firstCapture", input: measured({ firstCapture: { ply: 1, byUs: true, role: "pawn" } }), fragment: "こちらから仕掛けていく", slot: 1 },
    { material: "2 firstContactPly", input: measured({ firstContactPly: 3 }), fragment: "駒はぶつかりますが", slot: 1 },
    { material: "1・2 が null(無かった)", input: measured({}), fragment: "しばらく駒はぶつからない", slot: 1 },
    { material: "3 capturedRoles", input: measured({ capturedRoles: { us: new Map<Role, number>([["pawn", 1]]), opponent: new Map<Role, number>() } }), fragment: "こちらが歩を取る", slot: 3 },
    { material: "5 kingNeighborDelta", input: measured({ kingNeighborDelta: { us: -1, opponent: 0 } }), fragment: "玉の周りの駒が1枚減る", slot: 3 },
    { material: "6 firstCheck", input: measured({ firstCheck: { ply: 2, byUs: true } }), fragment: "王手がかかる", slot: 2 },
    { material: "7 firstPromotion", input: measured({ firstPromotion: { ply: 4, byUs: true, role: "pawn" } }), fragment: "歩が成る", slot: 2 },
    { material: "8 bishopExchangePly", input: measured({ bishopExchangePly: 2 }), fragment: "角を交換する", slot: 2 },
    { material: "9 firstDrop", input: measured({ firstDrop: { ply: 5, byUs: false, role: "pawn" } }), fragment: "歩を打つ", slot: 2 },
    { material: "10 kingMovePlies", input: measured({ kingMovePlies: { us: [3], opponent: [] } }), fragment: "玉が動く", slot: 2 },
    { material: "11 advanceRetreat", input: measured({ advanceRetreat: { us: { up: 2, down: 0, side: 0 }, opponent: { up: 0, down: 0, side: 0 } } }), fragment: "こちらの駒が前に出る", slot: 3 },
    { material: "12 slidingReachDelta", input: measured({ slidingReachDelta: { us: 5, opponent: 0 } }), fragment: "こちらの駒の動ける範囲が広がる", slot: 3 },
  ];

  it("材料ごとに、その節が期待するスロットの文にちょうど1回だけ現れる", () => {
    const wrong: string[] = [];
    for (const c of cases) {
      const r = buildPvSentences(c.input, ALL);
      const hits = r.kind === "text" ? r.sentences.filter((s) => s.includes(c.fragment)) : [];
      if (hits.length !== 1 || slotOf(hits[0] ?? "") !== c.slot) {
        wrong.push(`${c.material}: 期待 ${c.slot} / 実際 ${hits.map(slotOf).join(",") || "出ない"}`);
      }
    }
    // 11.5: 目当ての数字だけでなく、試した総数と外れた一覧も出す。
    expect({ 試した材料: cases.length, 期待と違った: wrong }).toEqual({ 試した材料: 12, 期待と違った: [] });
  });

  it("文は必ずスロット1→2→3 の順に並ぶ", () => {
    const r = buildPvSentences(
      measured({
        firstCapture: { ply: 1, byUs: false, role: "pawn" },
        firstCheck: { ply: 2, byUs: true },
        capturedRoles: { us: new Map<Role, number>(), opponent: new Map<Role, number>([["pawn", 1]]) },
      }),
      ALL,
    );
    expect(r.kind === "text" ? r.sentences.map(slotOf) : []).toEqual([1, 2, 3]);
  });
});

describe("buildPvSentences ― 打ち切り: 残りの手で覆りうる材料を外す(基準は「単調かどうか」)", () => {
  // 単調: 起きたことを言う肯定の文(1・6〜10・3。起きたことは起きたまま、枚数は増えるだけ)。
  // 覆りうる: 5・12(root と末端の差)・11(比較)・**不在を言う否定の文**(スロット1 の 2 文。計画書 18.)。
  // 材料3 の片側の言い方も覆りうる(不在の判定で言い方を選ぶ。計画書 18.7.1)。「○の取り合いになる」は残す。
  const truncatedInput = measured(
    {
      firstCapture: { ply: 1, byUs: true, role: "pawn" },
      firstCheck: { ply: 3, byUs: false },
      capturedRoles: { us: new Map<Role, number>([["pawn", 1]]), opponent: new Map<Role, number>([["pawn", 1]]) },
      handDelta: { us: new Map<Role, number>([["pawn", 1]]), opponent: new Map<Role, number>() },
      advanceRetreat: { us: { up: 3, down: 0, side: 0 }, opponent: { up: 0, down: 0, side: 0 } },
      kingNeighborDelta: { us: -2, opponent: 0 },
      slidingReachDelta: { us: 6, opponent: 0 },
    },
    { truncatedAtPly: 5 },
  );

  // 【期待値を変えた(2026-09-13)】この試験は以前、打ち切りでも材料11(「前に出る」)を
  // 使うと固定していた。独立監査 2 回目の実測で材料11 は覆りうると分かり(1,817 件中 68 件)、
  // **決定が変わったので期待値を変えた。試験に合わせて実装を直したのではない**(計画書 17.1)。
  it("単調な材料(1・6・3)は使い、覆りうる材料(5・11・12)は外す", () => {
    const text = textOf(buildPvSentences(truncatedInput, ALL));
    expect(text).toContain("こちらから仕掛けて"); // 材料1(スロット1)
    expect(text).toContain("王手がかかる"); // 材料6(スロット2)
    expect(text).toContain("歩の取り合いになる"); // 材料3(単調)
    expect(text).not.toContain("前に出る"); // 材料11(比較は覆る)
    expect(text).not.toContain("玉の周りの駒"); // 材料5(root と末端の差)
    expect(text).not.toContain("動ける範囲"); // 材料12(root と末端の差)
  });

  // 打ち切られた集計は「少なくともそれだけ」であって「それで全部」ではない。
  // 数を出すと1枚で終わったと読める(CLAUDE.md ルール6)。
  it("打ち切りのとき、文に数字が1つも出ない", () => {
    expect(textOf(buildPvSentences(truncatedInput, ALL))).not.toMatch(/[0-90-9]/);
  });

  // 上の 2 件が**当たり前に通っているのではない**ことを示す。
  // 同じ材料で打ち切りが無ければ、外した 5・11・12 が出て、材料5 が数字を出す。
  it("同じ材料でも打ち切りが無ければ、外した 5・11・12 が出る(上の試験が空振りでないことの校正)", () => {
    const notTruncated = { ...truncatedInput, truncatedAtPly: null } as typeof truncatedInput;
    const text = textOf(buildPvSentences(notTruncated, ALL));
    expect(text).toMatch(/[0-90-9]/);
    expect(text).toContain("こちらの駒が前に出る");
    expect(text).toContain("玉の周りの駒");
    expect(text).toContain("動ける範囲");
  });

  // 【期待値を変えた(2026-09-13)】この試験は以前「しばらくぶつからない は打ち切りでも使う」と固定していた。
  // 司令塔が「単調なので残す」という自分の決定を訂正したため、**決定が変わったので期待値を変えた。
  // 試験に合わせて実装を直したのではない**(計画書 18.)。否定の文は、範囲が読む人に見えない限り覆る。
  it("打ち切りのとき、不在を言う否定の文(「しばらく駒はぶつからない」「取り合いにはならない」)は出ない", () => {
    const cut = { usablePlies: 6, truncatedAtPly: 7 };
    expect(textOf(buildPvSentences(measured({}, cut), ALL))).not.toContain("ぶつからない");
    expect(textOf(buildPvSentences(measured({ firstContactPly: 2 }, cut), ALL))).not.toContain("取り合いにはならない");
    // 校正: 同じ材料で打ち切りが無ければ、どちらも出る(上の 2 行が空振りでないこと)。
    expect(textOf(buildPvSentences(measured({}, { usablePlies: 6 }), ALL))).toContain("しばらく駒はぶつからない");
    expect(textOf(buildPvSentences(measured({ firstContactPly: 2 }, { usablePlies: 6 }), ALL))).toContain("取り合いにはならない");
  });

  it("打ち切りで文が 1 つも立たなければ not_measured(pv_truncated)。no_material(言うことが無い)とは言わない", () => {
    expect(buildPvSentences(measured({}, { usablePlies: 6, truncatedAtPly: 7 }), ALL)).toEqual({
      kind: "not_measured",
      reason: "pv_truncated",
    });
    // 手数不足とは別の理由になる(同じ値に 2 種類の「無い」を背負わせない。規則 11.6)。
    expect(buildPvSentences(measured({}, { usablePlies: 2 }), ALL)).toEqual({
      kind: "not_measured",
      reason: "too_few_plies_for_absence",
    });
  });

  // 文字列リテラルを全部拾うと、否定の形はスロット1 の 2 文だけだった(計画書 18.)。
  // 母数(allInputs)は出力の枝を網羅している(下の網羅の試験)ので、枝を足せばここにも効く。
  it("打ち切りのとき、母数のどの入力からも否定の形(ない・ません 等)を含む文が出ない", () => {
    const NEG = /ない|ません|ぬ|ず[、。]|無い|無く|なし|なく/;
    const cut = allInputs().map((i) => (i.kind === "measured" ? { ...i, usablePlies: 6, truncatedAtPly: 7 } : i));
    expect(cut.map((i) => textOf(buildPvSentences(i, ALL))).filter((t) => NEG.test(t))).toEqual([]);
    // 校正: 打ち切りが無ければ、母数には否定の形を含む文がある(検査が空振りでないこと)。
    expect(allOutputs().filter((t) => NEG.test(t)).length).toBeGreaterThan(0);
  });

  // 【2026-09-13 に足した(計画書 18.7.1)】片側の言い方(「こちらが○を取る」「相手が○を取る」)は、
  // 相手側がその駒を取っていないという**不在の判定**で選ぶ。文字列は肯定でも、打ち切りでは覆りうる
  // (模擬で 2,738 回中 563 回、読み筋全体では相手側も同じ駒を取っていた)。「取り合い」は肯定の事実なので残す。
  it("打ち切りのとき、片側の言い方は出さず、「○の取り合いになる」は残す", () => {
    const captured = {
      capturedRoles: {
        us: new Map<Role, number>([["pawn", 1], ["silver", 1]]),
        opponent: new Map<Role, number>([["pawn", 1], ["gold", 1]]),
      },
    };
    const cut = textOf(buildPvSentences(measured(captured, { usablePlies: 6, truncatedAtPly: 7 }), ALL));
    expect(cut).toContain("歩の取り合いになる");
    expect(cut).not.toContain("銀を取る");
    expect(cut).not.toContain("金を取る");
    // 校正: 同じ材料で打ち切りが無ければ、片側の言い方も出る(上が空振りでないこと)。
    const notCut = textOf(buildPvSentences(measured(captured, { usablePlies: 6 }), ALL));
    expect(notCut).toContain("こちらが銀を取る");
    expect(notCut).toContain("相手が金を取る");
  });

  it("打ち切りのとき、母数のどの入力からも片側の言い方が出ない", () => {
    const ONE_SIDED = /(こちらが|相手が)[^、。]+を取る/;
    const cut = allInputs().map((i) => (i.kind === "measured" ? { ...i, usablePlies: 6, truncatedAtPly: 7 } : i));
    expect(cut.map((i) => textOf(buildPvSentences(i, ALL))).filter((t) => ONE_SIDED.test(t))).toEqual([]);
    // 校正: 打ち切りが無ければ、母数には片側の言い方がある。
    expect(allOutputs().filter((t) => ONE_SIDED.test(t)).length).toBeGreaterThan(0);
  });

  // 【固定例(2026-09-13 に期待値を変えた。計画書 18.)】
  // 実物の読み筋を前から k 手で打ち切り(k+1 手目に非合法手を置く)、同じ k 手を打ち切らずに
  // 再生した場合と比べる。この読み筋は 7 手目でぶつかり、8 手目で取る。
  // - 打ち切らない k 手の読み筋は、k = 4〜6 で「しばらく駒はぶつからない」、k = 7 で「取り合いにはならない」と言う
  // - **読み筋の全体では、どちらも覆る**(7 手目で接触、8 手目で捕獲)
  // - したがって、読めなかった続きがあると分かっている打ち切りのときは、どちらも言わない
  // 以前この試験は「打ち切りでも k = 4〜6 で『しばらく』と言い、k 手以内には接触が無い」ことを固定していた。
  // 範囲付きの主張としては正しかったが、文は範囲を読む人に示していない。**決定が変わったので期待値を変えた。**
  it("固定例: 打ち切りでは、読み筋の全体で覆る否定の文を言わない(打ち切らなければ言う)", () => {
    const START = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
    const RULES: PvMaterialRules = {
      contact: "capture_available",
      kingNeighborhood: "eight_neighbors",
      advance: "rank_delta",
      reach: "sliding_attack_count",
    };
    const fullPv = ["2g2f", "8c8d", "2f2e", "8d8e", "6i7h", "4a3b", "2e2d", "2c2d"];
    const full = computePvMaterials(START, fullPv, RULES, 3);
    if (full.kind !== "measured") throw new Error("固定例の読み筋が再生できない");
    // 残りの手でぶつかり・取りが起きる例であること(空振りでないことの校正)。
    expect([full.materials.firstContactPly, full.materials.firstCapture?.ply]).toEqual([7, 8]);

    const negatives = ["しばらく駒はぶつからない", "取り合いにはならない"];
    const saidWhenCut: string[] = [];
    const saidWhenNotCut: string[] = [];
    for (let k = 3; k < fullPv.length; k++) {
      const cut = computePvMaterials(START, [...fullPv.slice(0, k), "9a9i"], RULES, 3);
      const notCut = computePvMaterials(START, fullPv.slice(0, k), RULES, 3);
      if (cut.kind !== "measured" || notCut.kind !== "measured") continue;
      expect([cut.truncatedAtPly, notCut.truncatedAtPly]).toEqual([k + 1, null]); // 本当に打ち切り / 打ち切りでない
      for (const s of negatives) {
        if (textOf(buildPvSentences(cut, ALL)).includes(s)) saidWhenCut.push(`${k}:${s}`);
        if (textOf(buildPvSentences(notCut, ALL)).includes(s)) saidWhenNotCut.push(`${k}:${s}`);
      }
    }
    // 11.5: 打ち切らない側で言った一覧も出す(打ち切りの側が 0 件なのは、言う場面が無いからではないこと)。
    expect({ 打ち切りで言った: saidWhenCut, 打ち切らずに言った: saidWhenNotCut }).toEqual({
      打ち切りで言った: [],
      打ち切らずに言った: ["4:しばらく駒はぶつからない", "5:しばらく駒はぶつからない", "6:しばらく駒はぶつからない", "7:取り合いにはならない"],
    });
  });
});

describe("buildPvSentences ― 材料4(持ち駒の増減)は文にしない", () => {
  // 決定(2026-09-13): 材料4 は「末端の持ち駒 − root の持ち駒」で、captureSummary.ts の
  // 人間承認済みの理由(持ち駒の枚数は取った事実の集約にならない)に当たる。数えること(U6-M)は変えない。
  it("打ち切りの有無にかかわらず、持ち駒の増減だけを変えても文が変わらない", () => {
    const hand = { handDelta: { us: new Map<Role, number>([["pawn", 1]]), opponent: new Map<Role, number>([["bishop", -1]]) } };
    expect(textOf(buildPvSentences(measured(hand), ALL))).toBe(textOf(buildPvSentences(measured({}), ALL)));
    // 打ち切りの側は否定の文が出ないため、材料が無いと空になる。空どうしの比較で通らないよう、王手を足す。
    const check = { firstCheck: { ply: 2, byUs: true } };
    const cutText = textOf(buildPvSentences(measured({ ...hand, ...check }, { usablePlies: 6, truncatedAtPly: 7 }), ALL));
    expect(cutText).toContain("王手がかかる");
    expect(cutText).toBe(textOf(buildPvSentences(measured(check, { usablePlies: 6, truncatedAtPly: 7 }), ALL)));
  });

  it("母数のどの文にも「持ち駒」が出ない(母数には持ち駒の増減がある入力を含む)", () => {
    for (const text of allOutputs()) expect(text).not.toContain("持ち駒");
  });

  it("use.slot3 に handDelta を書くと型で止まる", () => {
    const slot3: SentenceRules["use"]["slot3"] = [
      // @ts-expect-error 材料4 は文にしないので、Slot3Material から外してある
      "handDelta",
    ];
    expect(slot3).toHaveLength(1);
  });
});

describe("buildPvSentences ― 駒種の日本語名が無いとき(pieceMapping.ts の義務)", () => {
  it("対応表に無い駒種の節は出さず、英語の駒種名を文に出さない", () => {
    const text = textOf(
      buildPvSentences(
        measured({
          firstCheck: { ply: 1, byUs: true },
          firstPromotion: { ply: 2, byUs: true, role: "tokin" },
          firstDrop: { ply: 3, byUs: false, role: "horse" },
          capturedRoles: { us: new Map<Role, number>([["dragon", 1]]), opponent: new Map<Role, number>() },
        }),
        ALL,
      ),
    );
    expect(text).toContain("王手がかかる"); // 同じ文の他の節は出る(空振りでないこと)
    expect(text).not.toMatch(/[A-Za-z]/);
    expect(text).not.toContain("が成る");
    expect(text).not.toContain("を打つ");
    expect(text).not.toContain("を取る");
  });

  // いま材料が渡してくる駒種は成っていない駒種だけ(捕獲は元の駒種に正規化・成りは成る前の
  // 駒種・打つ駒は持ち駒。pvMaterials.test.ts の材料3・7・9)。そのすべてに日本語名がある。
  it("材料が渡しうる駒種(成っていない駒種)は、すべて日本語名を持つ(null に到達しない)", () => {
    const roles: Role[] = ["king", "rook", "bishop", "gold", "silver", "knight", "lance", "pawn"];
    expect(roles.filter((role) => roleToJapanese(role) === null)).toEqual([]);
  });
});

describe("buildPvSentences ― 決定的(T-1)と、材料が効くこと(T-2)", () => {
  it("同じ入力からは常に同じ文が出る", () => {
    const input = measured({ firstCapture: { ply: 2, byUs: false, role: "silver" } });
    expect(buildPvSentences(input, ALL)).toEqual(buildPvSentences(input, ALL));
  });

  it("文にする材料を変えると文が変わる(効いていない材料を静かに持たない)", () => {
    const base = buildPvSentences(measured({}), ALL);
    const cases: Array<[string, PvMaterialsResult]> = [
      ["firstCapture", measured({ firstCapture: { ply: 1, byUs: true, role: "pawn" } })],
      ["firstContactPly", measured({ firstContactPly: 3 })],
      ["firstCheck", measured({ firstCheck: { ply: 2, byUs: true } })],
      ["firstPromotion", measured({ firstPromotion: { ply: 4, byUs: true, role: "pawn" } })],
      ["bishopExchangePly", measured({ bishopExchangePly: 2 })],
      ["firstDrop", measured({ firstDrop: { ply: 5, byUs: false, role: "pawn" } })],
      ["kingMovePlies", measured({ kingMovePlies: { us: [3], opponent: [] } })],
      ["advanceRetreat", measured({ advanceRetreat: { us: { up: 2, down: 0, side: 0 }, opponent: { up: 0, down: 0, side: 0 } } })],
      ["capturedRoles", measured({ capturedRoles: { us: new Map<Role, number>([["pawn", 1]]), opponent: new Map<Role, number>() } })],
      ["kingNeighborDelta", measured({ kingNeighborDelta: { us: -1, opponent: 0 } })],
      ["slidingReachDelta", measured({ slidingReachDelta: { us: 5, opponent: 0 } })],
    ];
    const unchanged = cases.filter(([, input]) => textOf(buildPvSentences(input, ALL)) === textOf(base)).map(([name]) => name);
    // 11.5: 目当ての数字だけでなく、試した総数と変わらなかった一覧も出す。
    // 材料4(handDelta)は文にしないと決めたので、ここには入れない(上の describe で「変わらない」ことを固定)。
    expect({ 試した材料: cases.length, 変わらなかった材料: unchanged }).toEqual({ 試した材料: 11, 変わらなかった材料: [] });
  });

  it("use に入れていない材料は文に出ない(取捨は規則が決める)", () => {
    const rules: SentenceRules = { ...ALL, use: { slot1: ["firstCapture"], slot2: [], slot3: [] } };
    const r = buildPvSentences(measured({ firstCheck: { ply: 2, byUs: true }, kingNeighborDelta: { us: -1, opponent: 0 } }), rules);
    expect(textOf(r)).not.toContain("王手");
    expect(textOf(r)).not.toContain("玉の周り");
  });
});

/** 出力に現れうる全パターンの入力を1か所に集める(禁止語・場所・否定の文の検査の母数)。 */
function allInputs(): PvMaterialsResult[] {
  return [
    measured({ firstCapture: { ply: 1, byUs: true, role: "pawn" } }),
    measured({ firstCapture: { ply: 1, byUs: false, role: "bishop" } }),
    measured({ firstContactPly: 0 }),
    measured({}),
    measured({
      firstCheck: { ply: 2, byUs: true },
      firstPromotion: { ply: 4, byUs: true, role: "pawn" },
      bishopExchangePly: 2,
      firstDrop: { ply: 5, byUs: false, role: "silver" },
      kingMovePlies: { us: [3], opponent: [6] },
      advanceRetreat: { us: { up: 3, down: 1, side: 0 }, opponent: { up: 0, down: 0, side: 0 } },
    }),
    measured({ advanceRetreat: { us: { up: 0, down: 2, side: 0 }, opponent: { up: 0, down: 0, side: 0 } } }),
    measured({
      capturedRoles: { us: new Map<Role, number>([["pawn", 1]]), opponent: new Map<Role, number>([["pawn", 1], ["silver", 1]]) },
      // 材料4 は文にしない。**「持ち駒」が出ないことの検査が空振りしないよう、母数には値を入れておく。**
      handDelta: { us: new Map<Role, number>([["pawn", 1]]), opponent: new Map<Role, number>([["silver", 1]]) },
      kingNeighborDelta: { us: -2, opponent: 1 },
      slidingReachDelta: { us: 7, opponent: 2 },
    }),
    measured({ kingNeighborDelta: { us: 1, opponent: 0 }, slidingReachDelta: { us: 0, opponent: 4 } }),
    // 「こちらが○を取る」の枝(片側だけが取った駒)。当初の母数から漏れていた(計画書 15.)。
    measured({
      capturedRoles: { us: new Map<Role, number>([["silver", 1]]), opponent: new Map<Role, number>([["pawn", 1]]) },
    }),
  ];
}

function allOutputs(): string[] {
  return allInputs().map((i) => textOf(buildPvSentences(i, ALL))).filter((t) => t.length > 0);
}

describe("buildPvSentences ― 禁止したもの(T-3・T-4・T-5)", () => {
  // captureSummary.ts 冒頭の人間承認済みの制約と同じ。
  it("「得」「損」「有利」「不利」「互角」が1つも出ない", () => {
    const banned = ["得", "損", "有利", "不利", "互角"];
    for (const text of allOutputs()) for (const w of banned) expect(text).not.toContain(w);
  });

  // 【この検査が捕まえないもの(規則11.1。リストと一緒に書く)】
  // - マスの符号と主要な区域表現しか見ていない。「相手の陣地の奥」のような
  //   言い換えは捕まらない。**これが通ったことを「場所を言っていない」の証拠にしない。**
  // - 「玉の周り」は**わざと禁止していない**。設計書5.3 の例文がこの表現を使っており
  //   (駒基準の相対位置)、禁止すると設計が認めた文まで弾く。
  it("場所の表現(マスの符号・主要な区域表現)が出ない", () => {
    const files = "123456789１２３４５６７８９";
    const ranks = "一二三四五六七八九";
    const areas = ["玉頭", "自陣", "敵陣", "中央", "筋", "段"];
    for (const text of allOutputs()) {
      for (const f of files) for (const r of ranks) expect(text).not.toContain(`${f}${r}`);
      for (const a of areas) expect(text).not.toContain(a);
    }
  });

  it("未来の記述が必ず仮定の形になっている(「そうです」で終わる)", () => {
    for (const text of allOutputs()) {
      for (const sentence of text.split("。").filter((s) => s.length > 0)) {
        expect(sentence.endsWith("そうです")).toBe(true);
      }
    }
  });
});

// 【母数の穴を塞ぐ(2026-09-13)】
// 禁止語・場所の検査は allOutputs() を母数にしている。**母数が出力の枝を
// 網羅していなければ、検査は通って当然である。**そこで、実装が出しうる
// 文の断片をここに列挙し、**すべてが allOutputs() に現れること**を確かめる。
// 枝を足したらこの一覧も足すことになり、母数が自動的に追随する。
describe("buildPvSentences ― 禁止語・場所の検査の母数(allOutputs の網羅)", () => {
  const fragments = [
    // スロット1(4通り)
    "こちらから仕掛けていく",
    "相手から攻めてくる",
    "駒はぶつかりますが、取り合いにはならない",
    "しばらく駒はぶつからない",
    // スロット2(5通り)
    "王手がかかる",
    "が成る",
    "角を交換する",
    "を打つ",
    "玉が動く",
    // スロット3(材料3の3通り・5の2通り・11の2通り・12の2通り。材料4 は文にしない)
    "の取り合いになる",
    "こちらが",
    "相手が",
    "玉の周りの駒が",
    "枚減る",
    "枚増える",
    "こちらの駒が前に出る",
    "こちらの駒が引く",
    "こちらの駒の動ける範囲が広がる",
    "相手の駒の動ける範囲が広がる",
  ];

  it("実装が出しうる文の断片が、すべて母数(allOutputs)に現れる", () => {
    const all = allOutputs().join("\n");
    const missing = fragments.filter((f) => !all.includes(f));
    // 11.5: 目当ての数字だけでなく、母数の大きさも一緒に出す。
    expect({ 母数の文字列数: allOutputs().length, 網羅できていない断片: missing }).toEqual({
      母数の文字列数: allOutputs().length,
      網羅できていない断片: [],
    });
  });
});
