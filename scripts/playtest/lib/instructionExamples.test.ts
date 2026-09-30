// 束 R4 ― 指示文に書いた**場所の例**の検め(司令塔の F-2・F-3。2026-09-30)。
//
// 【何を固定するか】(1) 例を拾う規則(穴・空の添字は例でない)。(2) **門の 2 段**: 書き方の誤りは止め、材料の薄さは警告にとどめる
//   ― これを混ぜると、**局数の少ない組では正しい packet なのに送れなくなる**(司令塔の F-3)。(3) 指示文 v1.1 の例が全部文法を通ること。
// 【実物の packet は使わない】実物は gitignore なので、ここは合成した packet で**分かれ方**を固定する。
//   実物への当ては CLI(runSeats)の送る前の門で毎回走る(記録は LOG §10)。
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { checkInstructionExample, instructionExamplePaths, instructionExampleReport } from "./instructionExamples.js";
import { packetRefPathProblems } from "./packetRef.js";

function packet(over: { timeRows?: unknown[]; names?: unknown; aggregates?: unknown[] } = {}): Record<string, unknown> {
  return {
    facts: {
      games: [{ gameId: "g01" }],
      time: over.timeRows ?? [{ gameId: "g01", longThinkCount: 5, remainingSec: 0 }],
      branches: [{ gameId: "g01", topGapCp: -46 }],
      recognition: { rows: [{ gameId: "g01", names: over.names ?? ["同型矢倉"] }], definitions: [{ id: "onikoroshi" }] },
    },
    aggregates: over.aggregates ?? [
      { id: "sideMatch.attack", numerator: 65, denominator: 107 },
      { id: "branches.total", value: 404 },
      { id: "empty.row", value: null },
    ],
  };
}

describe("例を拾う規則", () => {
  it("バッククォートの中の facts. / aggregates. を拾い、穴と空の添字は拾わない", () => {
    const text = "場所は `aggregates.<id>.numerator` の形。例: `aggregates.branches.total.value`・`facts.time[0].longThinkCount`。欄は `facts.recognition.rows[].names`。`obs.time.bySpent` は別。";
    expect(instructionExamplePaths(text).sort()).toEqual(["aggregates.branches.total.value", "facts.time[0].longThinkCount"]);
  });
});

describe("門の 2 段 ― 書き方の誤りは止める", () => {
  it("集計の id が実物と違う(camelCase を snake_case で書いた)", () => {
    const check = checkInstructionExample("aggregates.side_match.attack.numerator", packet());
    expect(check.level).toBe("error");
    expect(check.reason).toContain("side_match.attack の行が無い");
  });
  it("分数の行と単独の数の行の取り違え", () => {
    expect(checkInstructionExample("aggregates.branches.total.numerator", packet()).level).toBe("error");
    expect(checkInstructionExample("aggregates.sideMatch.attack.value", packet()).level).toBe("error");
  });
  it("表の名前が実物と違う", () => {
    const check = checkInstructionExample("facts.timeline[0].spentSec", packet());
    expect(check.level).toBe("error");
    expect(check.reason).toContain("facts.timeline");
  });
  it("欄名が実物と違う(行は在るが欄が無い)", () => {
    const check = checkInstructionExample("facts.time[0].spentSec", packet());
    expect(check.level).toBe("error");
    expect(check.reason).toContain("spentSec の欄が無い");
  });
  it("文法が違う(行番号が表の名前の後ろに無い・集計の単独形)", () => {
    // **理由まで見る**: 文法の判定を外しても別の理由(欄が無い・id が無い)で error になるので、
    // level だけ見る試験は文法の判定を消す変異で黙る(独立監査の変異 F。2026-09-30)
    for (const path of ["facts.time.bySpent[0].collapsed", "aggregates.branches.total", "packet.facts.time[0].longThinkCount", "facts.games[].result"]) {
      const check = checkInstructionExample(path, packet());
      expect(check.level, path).toBe("error");
      expect(check.reason, path).toContain("文法");
    }
  });
});

describe("門の 2 段 ― 材料の薄さは警告にとどめて続ける(司令塔の F-3)", () => {
  it("表が空でも止めない(少ない組・新しい顧客で正しい packet を弾かない)", () => {
    const check = checkInstructionExample("facts.time[0].longThinkCount", packet({ timeRows: [] }));
    expect(check.level).toBe("warn");
    expect(check.reason).toContain("空");
  });
  it("行番号が表の外でも止めない", () => {
    const check = checkInstructionExample("facts.time[3].longThinkCount", packet());
    expect(check.level).toBe("warn");
    expect(check.reason).toContain("表の外");
  });
  it("値が空(null・空の列)でも止めない", () => {
    expect(checkInstructionExample("facts.recognition.rows[0].names", packet({ names: [] })).level).toBe("warn");
    expect(checkInstructionExample("aggregates.empty.row.value", packet()).level).toBe("warn");
  });
  it("値が 0 は「空」ではない(0 を空として扱うと、0 の観測が警告になる)", () => {
    // 境界(独立監査の変異 G。2026-09-30): fixture に 0 の例が無いと `isEmptyValue` が 0 を空にする変異で黙る
    expect(checkInstructionExample("facts.time[0].remainingSec", packet())).toEqual({ path: "facts.time[0].remainingSec", level: "ok", value: 0 });
  });
  it("引けて値が入っていれば ok(値も返す)", () => {
    expect(checkInstructionExample("facts.time[0].longThinkCount", packet())).toEqual({ path: "facts.time[0].longThinkCount", level: "ok", value: 5 });
    expect(checkInstructionExample("aggregates.sideMatch.attack.numerator", packet())).toEqual({ path: "aggregates.sideMatch.attack.numerator", level: "ok", value: 65 });
    expect(checkInstructionExample("facts.recognition.rows[0].names", packet()).level).toBe("ok");
  });
});

describe("指示文 1 本の検め", () => {
  const text = "例: `aggregates.sideMatch.attack.numerator`・`facts.time[0].longThinkCount`・`facts.recognition.rows[0].names`";
  it("全部引ければ errors も warnings も空", () => {
    const report = instructionExampleReport(text, packet(), { label: "席の指示文", minExamples: 3 });
    expect(report.errors).toEqual([]);
    expect(report.warnings).toEqual([]);
    expect(report.checks.length).toBe(3);
  });
  it("例が足りないのは誤り(例が消えた指示文を黙って配らない)", () => {
    const report = instructionExampleReport("例: `facts.time[0].longThinkCount`", packet(), { label: "席の指示文", minExamples: 3 });
    expect(report.errors.length).toBe(1);
    expect(report.errors[0]).toContain("1 本しか無い");
  });
  it("例がちょうど min - 1 本なら誤り / ちょうど min 本なら通る(境界。独立監査の変異 I)", () => {
    const two = "例: `facts.time[0].longThinkCount`・`facts.branches[0].topGapCp`";
    const three = `${two}・\`facts.recognition.rows[0].names\``;
    expect(instructionExampleReport(two, packet(), { label: "席の指示文", minExamples: 3 }).errors.length).toBe(1);
    expect(instructionExampleReport(three, packet(), { label: "席の指示文", minExamples: 3 }).errors).toEqual([]);
  });
  it("薄い材料では warnings だけが出る(errors は空 = 送れる)", () => {
    const report = instructionExampleReport(text, packet({ timeRows: [], names: [] }), { label: "席の指示文", minExamples: 3 });
    expect(report.errors).toEqual([]);
    expect(report.warnings.length).toBe(2);
  });
});

describe("指示文 v1.1 の実文", () => {
  const examples = instructionExamplePaths(readFileSync(new URL("../../../docs/LLM_SEATS_INSTRUCTION_v1.1_2026-09-30.md", import.meta.url), "utf-8"));
  it("例が 3 つ以上あり、全部が文法を通る", () => {
    expect(examples.length).toBeGreaterThanOrEqual(3);
    for (const path of examples) expect(packetRefPathProblems(path), path).toEqual([]);
  });
  it("集計の例は分子・分母・単独の値のどれかを指している(単独形を例に出さない)", () => {
    const aggregates = examples.filter((p) => p.startsWith("aggregates."));
    expect(aggregates.length).toBeGreaterThan(0);
    for (const path of aggregates) expect(path, path).toMatch(/\.(numerator|denominator|value)$/);
  });
  it("事実の例の行番号は 0(少ない組でも引ける。司令塔の F-3)", () => {
    const facts = examples.filter((p) => p.startsWith("facts."));
    expect(facts.length).toBeGreaterThan(0);
    for (const path of facts) expect(path, path).toContain("[0]");
  });
  it("v1 の例は文法を通らない(v1.1 で直した理由。ここが緑に戻ったら v1 を見直す合図)", () => {
    expect(packetRefPathProblems("facts.time.bySpent[3].collapsed").length).toBe(1);
  });
});
