// STEP ANSWER 作業(docs/STEP_ANSWER_PLAN_2026-09-23.md §2.3・§3)。
// `lib/answerMenu.ts` の `ANSWER_MENU` が docs §3 の表と一致することを確かめる
// (findingTexts.test.ts と同じ形。文の正本は docs §3、合わなければこの試験を赤のまま報告する)。
//
// 【司令塔の事前監査 REVISE(2026-09-23)による範囲の縮小】
// docs §3 の表は司令塔がこの REVISE(M1・M8 の minN 変更ほか)に合わせて書き直す途中のため、
// **この試験の docs 一致は id・段階・minN だけ**にした(行動の文の芯は比べない。司令塔の指示)。
// さらに M8 の minN は、書き直された docs にまだ合わせられないため docs から取らず、
// このファイル(実装)の値をそのまま確かめる単独の試験にしてある(**未照合**。docs 側の確定後に司令塔が
// このテストを docs 由来へ戻すことを想定)。
// 【ANSWER-M1(2026-09-24)】M1 は docs §3 の「この版では出さない」の記述を消したため、docs 一致試験に戻した
// (docs §7.2)。
//
// 【ANSWER-MENU2(2026-09-24、docs §8)】答え合わせの下限(verifyGate。§8.1)と M9(§8.2)を追加。
// docs §3 の表には M9 が無く(§8.2 の表にある)、docs 一致試験は §3・§8.2 の両方の表から読む。
//
// `menuConditionHoldsOf`・`menuVerifyGateHoldsOf` の境界(各 id の「出す条件」・「答え合わせの下限」が
// ちょうど成り立つ/成り立たない材料)も確かめる。

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  ANSWER_MENU,
  answerMenuDenominatorOf,
  menuConditionHoldsOf,
  menuVerifyGateHoldsOf,
  type AnswerMenuId,
  type AnswerMenuMaterials,
  type AnswerMenuPatientGroup,
} from "./answerMenu.js";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const DOCS_PATH = path.join(REPO_ROOT, "docs", "STEP_ANSWER_PLAN_2026-09-23.md");
const DOCS_TEXT = readFileSync(DOCS_PATH, "utf-8");

interface DocsMenuRow {
  id: string;
  stage: string;
  minN: number;
}

/**
 * §3(M1〜M8)・§8.2(M9)の表(パイプテーブル)を 1 行ずつ読む。先頭列が `M` で始まる行だけ拾う
 * (見出し・区切り行は無視)。§3・§8.2 とも id・段階・minN の列位置(0・1・5)は同じ形なので、
 * どちらの表の行かを区別せずにまとめて読める。
 */
function docsMenuRows(): DocsMenuRow[] {
  const lines = DOCS_TEXT.split("\n").filter((line) => /^\|\s*M\d/.test(line));
  return lines.map((line) => {
    // `| M1 | 時間 | ... | 行動 | 根拠の数 | minN | 答え合わせの数 |` → split("|") の要素は
    // ["", " M1 ", " 時間 ", ..., ""] の形(先頭・末尾が空)。中身だけを使う。
    const parts = line
      .split("|")
      .slice(1, -1)
      .map((cell) => cell.trim());
    const [id, stage, , , , minNCell] = parts;
    if (id === undefined || stage === undefined || minNCell === undefined) {
      throw new Error(`docs の表の行から列を取れない: ${line}`);
    }
    const numbers = minNCell.match(/\d+/g);
    if (numbers === null) throw new Error(`docs の表の minN 列に数が無い: ${minNCell}`);
    const minN = Number(numbers[numbers.length - 1]);
    return { id, stage, minN };
  });
}

const M8_UNMATCHED_TO_DOCS: ReadonlySet<string> = new Set(["M8"]);

describe("ANSWER_MENU は docs §3・§8.2 の表と一致する(id・段階・minN。行動の文の芯は今回は比べない)", () => {
  const rows = docsMenuRows();

  it("docs の行数と ANSWER_MENU の件数が一致する(§3 の 8 件 + §8.2 の M9 = 9 件)", () => {
    expect(rows).toHaveLength(9);
    expect(ANSWER_MENU).toHaveLength(9);
  });

  it.each(rows.filter((row) => !M8_UNMATCHED_TO_DOCS.has(row.id)))("$id(docs 由来)", (row) => {
    const item = ANSWER_MENU.find((entry) => entry.id === row.id);
    expect(item, `ANSWER_MENU に ${row.id} が無い`).toBeDefined();
    expect(item!.stage).toBe(row.stage);
    expect(item!.minN).toBe(row.minN);
  });

  it("M8 の段階は docs と一致する(minN は未照合。docs が書き直され次第、司令塔が戻す)", () => {
    for (const row of rows.filter((r) => M8_UNMATCHED_TO_DOCS.has(r.id))) {
      const item = ANSWER_MENU.find((entry) => entry.id === row.id);
      expect(item, `ANSWER_MENU に ${row.id} が無い`).toBeDefined();
      expect(item!.stage).toBe(row.stage);
    }
  });

  it("M8 の minN は、司令塔の指示(2026-09-23 REVISE 3)どおりの値(未照合。docs との一致は取っていない)", () => {
    expect(ANSWER_MENU.find((entry) => entry.id === "M8")!.minN).toBe(2);
  });
});

// ==================== menuConditionHoldsOf の境界 ====================

function group(overrides: Partial<AnswerMenuPatientGroup> & { group: AnswerMenuPatientGroup["group"] }): AnswerMenuPatientGroup {
  return {
    group: overrides.group,
    games: overrides.games ?? 10,
    timeUpLosses: overrides.timeUpLosses ?? null,
    bySpentTotal: overrides.bySpentTotal ?? null,
    bySpentZeroToOne: overrides.bySpentZeroToOne ?? null,
    overviewFell: overrides.overviewFell ?? null,
    overviewEarly: overrides.overviewEarly ?? null,
    phaseSpentOtherEarlyMedian: overrides.phaseSpentOtherEarlyMedian ?? null,
    phaseSpentOtherMidMedian: overrides.phaseSpentOtherMidMedian ?? null,
    afterLongThinkAny: overrides.afterLongThinkAny ?? null,
    afterLongThinkQuick: overrides.afterLongThinkQuick ?? null,
    midOverGames: overrides.midOverGames ?? null,
    midOverOver: overrides.midOverOver ?? null,
    midOverOverAndTimeUpLoss: overrides.midOverOverAndTimeUpLoss ?? null,
    timeUpLossMidSecs: overrides.timeUpLossMidSecs ?? [],
    otherGamesMidMedian: overrides.otherGamesMidMedian ?? null,
  };
}

function materialsOf(...groups: AnswerMenuPatientGroup[]): AnswerMenuMaterials {
  return { patientGroups: groups, readCombined: null, sideMatch: null };
}

describe("menuConditionHoldsOf の境界", () => {
  it("M1(ANSWER-M1、§7.2): 時間負け 2・4 秒超 5 → 成立、分母(4 秒超の局数)は 5", () => {
    const materials = materialsOf(group({ group: "min3", timeUpLosses: { n: 2, allAtLeast300: true }, midOverOver: 5 }));
    expect(menuConditionHoldsOf("M1", materials)).toBe(true);
    expect(answerMenuDenominatorOf("M1", materials)).toBe(5);
  });

  it("M1: 時間負けが 1(2 未満)→ 4 秒超が 5 以上でも不成立", () => {
    const materials = materialsOf(group({ group: "min3", timeUpLosses: { n: 1, allAtLeast300: true }, midOverOver: 5 }));
    expect(menuConditionHoldsOf("M1", materials)).toBe(false);
  });

  it("M1: 4 秒超の局が 4(5 未満)→ 時間負けが 2 以上でも不成立", () => {
    const materials = materialsOf(group({ group: "min3", timeUpLosses: { n: 2, allAtLeast300: true }, midOverOver: 4 }));
    expect(menuConditionHoldsOf("M1", materials)).toBe(false);
  });

  it("M1: min3 の組が無い、または midOverOver が測れなければ不成立・分母 null", () => {
    const materials = materialsOf(group({ group: "min10", timeUpLosses: { n: 2, allAtLeast300: true }, midOverOver: 5 }));
    expect(menuConditionHoldsOf("M1", materials)).toBe(false);
    expect(answerMenuDenominatorOf("M1", materials)).toBeNull();
  });

  it("M2: 3 分の崩れ率が 10 分の崩れ率のちょうど 1.5 倍 → 不成立、わずかに超える → 成立", () => {
    const min10 = group({ group: "min10", bySpentTotal: { collapsed: 10, n: 100 } }); // rate 0.10
    const exact = materialsOf(group({ group: "min3", bySpentTotal: { collapsed: 15, n: 100 } }), min10); // rate 0.15 = 0.10*1.5
    const over = materialsOf(group({ group: "min3", bySpentTotal: { collapsed: 16, n: 100 } }), min10); // rate 0.16 > 0.15
    expect(menuConditionHoldsOf("M2", exact)).toBe(false);
    expect(menuConditionHoldsOf("M2", over)).toBe(true);
    expect(answerMenuDenominatorOf("M2", over)).toBe(10);
  });

  it("M2: timeUpLosses.n >= 1(3 分の組)だけでも成立(10 分の組が無くても)", () => {
    const materials = materialsOf(group({ group: "min3", timeUpLosses: { n: 1, allAtLeast300: true } }));
    expect(menuConditionHoldsOf("M2", materials)).toBe(true);
  });

  it("M3: 序盤の崩れ割合がちょうど 15% → 成立、序盤の消費が中盤以上 → 不成立", () => {
    const okShare = group({
      group: "min3",
      overviewFell: 100,
      overviewEarly: 15,
      phaseSpentOtherEarlyMedian: 10,
      phaseSpentOtherMidMedian: 50,
    });
    expect(menuConditionHoldsOf("M3", materialsOf(okShare))).toBe(true);
    const spentNotLess = group({
      group: "min3",
      overviewFell: 100,
      overviewEarly: 15,
      phaseSpentOtherEarlyMedian: 50,
      phaseSpentOtherMidMedian: 50,
    });
    expect(menuConditionHoldsOf("M3", materialsOf(spentNotLess))).toBe(false);
  });

  it("M3: 序盤の崩れ割合が 15% を超える → 不成立", () => {
    const overShare = group({
      group: "min3",
      overviewFell: 100,
      overviewEarly: 16,
      phaseSpentOtherEarlyMedian: 10,
      phaseSpentOtherMidMedian: 50,
    });
    expect(menuConditionHoldsOf("M3", materialsOf(overShare))).toBe(false);
  });

  it("M4(司令塔の指示 2026-09-23 REVISE 2): 両方の分数が 70% ちょうど → 不成立、わずかに下回る → 成立", () => {
    const materialsAt70 = { patientGroups: [], readCombined: null, sideMatch: { attack: { collapsed: 70, n: 100 }, defense: { collapsed: 70, n: 100 }, forkTotal: 200 } };
    const materialsUnder70 = { patientGroups: [], readCombined: null, sideMatch: { attack: { collapsed: 69, n: 100 }, defense: { collapsed: 69, n: 100 }, forkTotal: 200 } };
    expect(menuConditionHoldsOf("M4", materialsAt70)).toBe(false);
    expect(menuConditionHoldsOf("M4", materialsUnder70)).toBe(true);
    expect(answerMenuDenominatorOf("M4", materialsUnder70)).toBe(200);
  });

  it("M4: 片方だけ 70% 未満(もう片方はちょうど 70%)→ 不成立(AND。実装担当の判断)", () => {
    const materials = {
      patientGroups: [],
      readCombined: null,
      sideMatch: { attack: { collapsed: 69, n: 100 }, defense: { collapsed: 70, n: 100 }, forkTotal: 200 },
    };
    expect(menuConditionHoldsOf("M4", materials)).toBe(false);
  });

  it("M4: sideMatch が無ければ不成立・分母 null", () => {
    const materials = materialsOf(group({ group: "min3" }));
    expect(menuConditionHoldsOf("M4", materials)).toBe(false);
    expect(answerMenuDenominatorOf("M4", materials)).toBeNull();
  });

  it("M5(≥、境界を含む): 長考の次の崩れ率がちょうど 2 倍 → 成立、わずかに届かない → 不成立", () => {
    const exact = group({
      group: "min3",
      bySpentZeroToOne: { collapsed: 10, n: 100 }, // rate 0.10
      afterLongThinkQuick: { collapsed: 6, n: 30 }, // rate 0.20 = 0.10*2
    });
    const under = group({
      group: "min3",
      bySpentZeroToOne: { collapsed: 10, n: 100 },
      afterLongThinkQuick: { collapsed: 5, n: 30 }, // rate ≈0.167 < 0.20
    });
    expect(menuConditionHoldsOf("M5", materialsOf(exact))).toBe(true);
    expect(menuConditionHoldsOf("M5", materialsOf(under))).toBe(false);
    expect(answerMenuDenominatorOf("M5", materialsOf(exact))).toBe(30);
  });

  it("M6(B v3 2026-09-24 の実例で確認): 分母 20 未満 → 不成立、20 以上で割合ちょうど 40% → 不成立、わずかに下回る → 成立", () => {
    const tooFew = { patientGroups: [], readCombined: { forkPositionsRead: 0, firstVisibleNodesNoneCount: 0, sacrificeRowTotal: 19, sacrificeDiagonal: 7 }, sideMatch: null };
    const at40 = { patientGroups: [], readCombined: { forkPositionsRead: 0, firstVisibleNodesNoneCount: 0, sacrificeRowTotal: 20, sacrificeDiagonal: 8 }, sideMatch: null }; // 8/20 = 40%
    const under40 = { patientGroups: [], readCombined: { forkPositionsRead: 0, firstVisibleNodesNoneCount: 0, sacrificeRowTotal: 57, sacrificeDiagonal: 17 }, sideMatch: null }; // B v3 の実例
    expect(menuConditionHoldsOf("M6", tooFew)).toBe(false);
    expect(menuConditionHoldsOf("M6", at40)).toBe(false);
    expect(menuConditionHoldsOf("M6", under40)).toBe(true);
    expect(answerMenuDenominatorOf("M6", under40)).toBe(57);
  });

  it("M7: 600 以上の分かれ道がちょうど 40% → 成立、40% を超える → 不成立", () => {
    const at40 = { patientGroups: [], readCombined: { forkPositionsRead: 100, firstVisibleNodesNoneCount: 60, sacrificeRowTotal: 0, sacrificeDiagonal: 0 }, sideMatch: null }; // 40 が 600 以上
    const over40 = { patientGroups: [], readCombined: { forkPositionsRead: 100, firstVisibleNodesNoneCount: 59, sacrificeRowTotal: 0, sacrificeDiagonal: 0 }, sideMatch: null }; // 41 が 600 以上
    expect(menuConditionHoldsOf("M7", at40)).toBe(true);
    expect(menuConditionHoldsOf("M7", over40)).toBe(false);
    expect(answerMenuDenominatorOf("M7", at40)).toBe(100);
  });

  it("M8: timeUpLosses の m = n(すべて +300 以上)→ 成立、1 局でも届かない → 不成立", () => {
    const allOk = materialsOf(group({ group: "min3", timeUpLosses: { n: 3, allAtLeast300: true } }));
    const notAll = materialsOf(group({ group: "min3", timeUpLosses: { n: 3, allAtLeast300: false } }));
    expect(menuConditionHoldsOf("M8", allOk)).toBe(true);
    expect(menuConditionHoldsOf("M8", notAll)).toBe(false);
    expect(answerMenuDenominatorOf("M8", allOk)).toBe(3);
  });

  it("M9(docs §8.2、ANSWER-MENU2): 時間負け 2・両方とも中央値超え → 成立", () => {
    const materials = materialsOf(
      group({ group: "min3", timeUpLosses: { n: 2, allAtLeast300: true }, timeUpLossMidSecs: [84, 77], otherGamesMidMedian: 40 }),
    );
    expect(menuConditionHoldsOf("M9", materials)).toBe(true);
    expect(answerMenuDenominatorOf("M9", materials)).toBe(2);
  });

  it("M9: 時間負け 2 局のうち 1 局だけ中央値を下回る → 不成立(すべてが条件、実装担当の判断)", () => {
    const materials = materialsOf(
      group({ group: "min3", timeUpLosses: { n: 2, allAtLeast300: true }, timeUpLossMidSecs: [84, 30], otherGamesMidMedian: 40 }),
    );
    expect(menuConditionHoldsOf("M9", materials)).toBe(false);
  });

  it("M9: 時間負けが 1(2 未満)→ 中央値をすべて超えていても不成立", () => {
    const materials = materialsOf(
      group({ group: "min3", timeUpLosses: { n: 1, allAtLeast300: true }, timeUpLossMidSecs: [84], otherGamesMidMedian: 40 }),
    );
    expect(menuConditionHoldsOf("M9", materials)).toBe(false);
  });

  it("M9: min3 の組が無い、または otherGamesMidMedian・timeUpLossMidSecs が測れなければ不成立・分母 null", () => {
    const materials = materialsOf(group({ group: "min10", timeUpLosses: { n: 2, allAtLeast300: true }, timeUpLossMidSecs: [84, 77], otherGamesMidMedian: 40 }));
    expect(menuConditionHoldsOf("M9", materials)).toBe(false);
    expect(answerMenuDenominatorOf("M9", materials)).toBeNull();
  });

  it("知らない id は例外(M9 は ANSWER-MENU2 で追加済みのため、知らない id は M10 で確かめる)", () => {
    expect(() => menuConditionHoldsOf("M10" as AnswerMenuId, materialsOf())).toThrow();
    expect(() => menuVerifyGateHoldsOf("M10" as AnswerMenuId, materialsOf())).toThrow();
  });
});

// ==================== menuVerifyGateHoldsOf の境界(docs §8.1、ANSWER-MENU2) ====================

describe("menuVerifyGateHoldsOf の境界", () => {
  it("M1: overAndTimeUpLoss / over がちょうど 1/2 → 成立、わずかに下回る → 不成立", () => {
    const exact = materialsOf(group({ group: "min3", midOverOver: 8, midOverOverAndTimeUpLoss: 4 })); // 4/8 = 0.5
    const under = materialsOf(group({ group: "min3", midOverOver: 8, midOverOverAndTimeUpLoss: 3 })); // 3/8 < 0.5
    expect(menuVerifyGateHoldsOf("M1", exact)).toBe(true);
    expect(menuVerifyGateHoldsOf("M1", under)).toBe(false);
  });

  it("M1: 実データに近い比率(1/7)→ 不成立(§7.6 の司令塔の判断を機械が再現する)", () => {
    const materials = materialsOf(group({ group: "min3", midOverOver: 7, midOverOverAndTimeUpLoss: 1 }));
    expect(menuVerifyGateHoldsOf("M1", materials)).toBe(false);
  });

  it("M1: min3 の組が無い、または over・overAndTimeUpLoss が測れなければ不成立", () => {
    const materials = materialsOf(group({ group: "min10", midOverOver: 8, midOverOverAndTimeUpLoss: 4 }));
    expect(menuVerifyGateHoldsOf("M1", materials)).toBe(false);
  });

  it("verifyGate が null の項目は常に true(M2〜M9。M9 で確認)", () => {
    expect(menuVerifyGateHoldsOf("M9", materialsOf())).toBe(true);
    expect(menuVerifyGateHoldsOf("M2", materialsOf())).toBe(true);
    expect(menuVerifyGateHoldsOf("M8", materialsOf())).toBe(true);
  });
});
