// STEP D4(docs/STEP_D4_PLAN_2026-09-15.md §7・§8・§13.6)。gate.ts を実際に回す(npx tsx)。
// 記録は gateFixtures/ の固定の記録(GAME01 の手順に評価を植えたもの。中身は gateFixtures/specs.ts の出力とバイト一致)。定義と --out は OS の一時ディレクトリ。
// **エンジンは起動しない。試験の実行中は作業ツリーにファイルを作らない**(子プロセスの前後で git status を比べるほかの試験が並行で走る)。
// **棄却の記録(records/gate/)には書かない**(--records-append は定義 0 本の実行でだけ渡す)。
//
// 【静かにスキップしない】npx・tsx が無ければ spawnSync の status が 0 でなく赤になる。

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, describe, expect, it } from "vitest";
import { GATE_FIXTURES, gateFixtureText } from "./gateFixtures/specs.js";
import { GATE_VALUES, gateVerdictOf } from "./lib/gate.js";
import { validateDiagnosisGateLine } from "./lib/gateOutput.js";

const REPO_ROOT = fileURLToPath(new URL("../../", import.meta.url));
const GATE_TS = fileURLToPath(new URL("./gate.ts", import.meta.url));
const FIXTURES = fileURLToPath(new URL("./gateFixtures/", import.meta.url));
const RECORDS_GATE_DIR = join(REPO_ROOT, "scripts", "playtest", "records", "gate");
/** 根の外(定義・--out・根の外の記録を置く) */
const WORK = mkdtempSync(join(tmpdir(), "gate-cli-"));
afterAll(() => rmSync(WORK, { recursive: true, force: true }));

const fixture = (name: string): string => join(FIXTURES, name);

const DEFINITION = (id: string, appliesTo: string, uses: string, status = "draft", evaluate = "(view) => view !== null") => `export default {
  id: ${JSON.stringify(id)},
  label: "試験だけの定義(仮)",
  status: ${JSON.stringify(status)},
  definitionText: "試験だけ",
${status === "approved" ? '  readableText: "試験だけの条件の文",\n' : ""}  uses: [${JSON.stringify(uses)}],
  thresholds: {},
  appliesTo: [${JSON.stringify(appliesTo)}],
  approval: ${status === "approved" ? '{ approvedBy: "test", date: "2026-09-16", record: "test" }' : "null"},
  evaluate: ${evaluate},
};
`;

function conditionsDir(name: string, files: Record<string, string>): string {
  const dir = join(WORK, name);
  mkdirSync(dir, { recursive: true });
  for (const [file, content] of Object.entries(files)) writeFileSync(join(dir, file), content, "utf-8");
  return dir;
}

function run(args: string[]) {
  const result = spawnSync("npx", ["tsx", GATE_TS, ...args], { cwd: REPO_ROOT, encoding: "utf-8" });
  return { status: result.status, stdout: result.stdout, stderr: result.stderr };
}

const M1 = fixture("m1.jsonl");
const M2 = fixture("m2.jsonl");
const S1 = fixture("s1.jsonl");
const base = (out: string, conditions: string) => ["--person", "p2", "--test-person", "p1", "--material", M1, M2, "--test-sente", S1, "--conditions", conditions, "--out", out];

/** records/gate/ の中身(無ければ null)。実行の前後で比べる */
const recordsState = (): string | null => (existsSync(RECORDS_GATE_DIR) ? readdirSync(RECORDS_GATE_DIR).map((name) => `${name}:${statSync(join(RECORDS_GATE_DIR, name)).size}`).join(",") : null);

describe("gate.ts(計画 §7)", () => {
  it("固定の記録は gateFixtures/specs.ts の出力とバイト一致(並びも GATE_FIXTURES と同じ)", () => {
    const names = readdirSync(FIXTURES).filter((name) => name.endsWith(".jsonl")).sort();
    expect(names).toEqual(Object.keys(GATE_FIXTURES).sort());
    for (const name of names) expect(readFileSync(fixture(name), "utf-8") === gateFixtureText(name), name).toBe(true);
  });

  it("T-6・I-8 定義 0 本: exit 0、--out は 0 行、Markdown に基準値の表(材料 2 本・組)、--records-append でも records/gate/ は変わらない", () => {
    const out = join(WORK, "zero.jsonl");
    const before = recordsState();
    const result = run([...base(out, conditionsDir("zero", {})), "--records-append"]);
    expect(result.status, result.stderr).toBe(0);
    expect(readFileSync(out, "utf-8")).toBe("");
    expect(result.stdout).toContain("## 全ての組の崩れ(条件式なし)");
    expect(result.stdout).toMatch(/材料: 記録 2 本/);
    expect(result.stdout).toMatch(/\| 材料 \| \d+ \| 2 \/ \d+/);
    expect(result.stdout).toMatch(/Gate に当てた条件式が無い/);
    expect(recordsState()).toBe(before);
  }, 60_000);

  it("T-3 pair の定義(draft)と failureEvent だけの定義: 2 行ともスキーマに合い、前者は集計つき notJudged draft、後者は pairNotApplied。conditionsInRun は 1", () => {
    const out = join(WORK, "two.jsonl");
    const dir = conditionsDir("two", {
      "a_pair.ts": DEFINITION("test_only_cli_pair", "pair", "standingPair.before"),
      "b_event.ts": DEFINITION("test_only_cli_event", "failureEvent", "trigger.focus.state"),
    });
    const result = run(base(out, dir));
    expect(result.status, result.stderr).toBe(0);
    const lines = readFileSync(out, "utf-8").trim().split("\n").map((line) => JSON.parse(line) as Record<string, any>);
    expect(lines.map((line) => validateDiagnosisGateLine(line))).toEqual([[], []]);
    expect(lines.map((line) => [line.condition.id, line.gate, line.conditionsInRun])).toEqual([
      ["test_only_cli_pair", { notJudged: "draft" }, 1],
      ["test_only_cli_event", { notJudged: "pairNotApplied" }, 1],
    ]);
    expect(lines[0]!.material.tally.all.collapsed).toBe(2);
    expect(lines[0]!.material.tally.all.transitions.aheadToLevel).toBe(2);
    expect(lines[0]!.material.inputs.map((input: { path: string }) => input.path)).toEqual(["scripts/playtest/gateFixtures/m1.jsonl", "scripts/playtest/gateFixtures/m2.jsonl"]);
    expect(lines[0]!.test).toMatchObject({ set: "sente1", provisional: true });
    expect(lines[0]!.source).toEqual({ referenceNodes: 4_000_000, evaluation: "light" });
    expect(result.stdout).toContain("- test_only_cli_event(draft)");
  }, 60_000);

  it("R-2 approved の定義を道具で回す: 行の gateValues は人間の確定値、gate は gateVerdictOf(GATE_VALUES) と一致。材料は G-1 の境(tn 10・3 局)で、minTruePairs を 11 にすると結果が変わる", () => {
    const dir = conditionsDir("r2", { "a.ts": DEFINITION("test_only_cli_approved", "pair", "trigger.evaluationBefore.scoreCp", "approved", "(view) => view.trigger.evaluationBefore.scoreCp >= 300") });
    const out = join(WORK, "r2.jsonl");
    const result = run(["--person", "p2", "--test-person", "p1", "--material", fixture("r2-m1.jsonl"), fixture("r2-m2.jsonl"), fixture("r2-m3.jsonl"), "--test-sente", fixture("r2-s1.jsonl"), "--conditions", dir, "--out", out]);
    expect(result.status, result.stderr).toBe(0);
    const lines = readFileSync(out, "utf-8").trim().split("\n").map((line) => JSON.parse(line) as Record<string, any>);
    expect(lines).toHaveLength(1);
    const line = lines[0]!;
    expect(validateDiagnosisGateLine(line)).toEqual([]);
    expect(line.gateValues).toEqual({ minTruePairs: 10, minGames: 3, minRateRatio: 2, minRateDiffPoints: 10, maxPvToActualRatio: 0.5, minTestTruePairs: 3 });
    const truePairs = line.material.tally.truePairs;
    expect([truePairs.denominator, truePairs.collapsed, truePairs.gamesWithDenominator]).toEqual([10, 9, 3]);
    expect(line.gate).toEqual(gateVerdictOf(line.material.tally, line.test.tally, GATE_VALUES));
    expect(line.gate.items[0]).toMatchObject({ item: "G-1", result: "met", threshold: { minTruePairs: 10, minGames: 3 } });
    expect(gateVerdictOf(line.material.tally, line.test.tally, { ...GATE_VALUES, minTruePairs: 11 }).items[0]!.result).toBe("notMet");
  }, 60_000);

  it.each([
    ["G-F8 referenceNodes がそろわない", () => [...base(join(WORK, "x1.jsonl"), conditionsDir("x1", {})).slice(0, 7), fixture("s-nodes.jsonl"), "--conditions", conditionsDir("x1b", {}), "--out", join(WORK, "x1.jsonl")], /referenceNodes がそろわない/],
    ["材料と試す側が同じラベル", () => ["--person", "p1", ...base(join(WORK, "x2.jsonl"), conditionsDir("x2", {})).slice(2)], /同じ人のラベル/],
    ["材料と試す側に同じ記録", () => [...base(join(WORK, "x3.jsonl"), conditionsDir("x3", {})).slice(0, 7), M1, "--conditions", conditionsDir("x3b", {}), "--out", join(WORK, "x3.jsonl")], /同じ name/],
    ["T-7 --test-gote で draft の定義", () => [...base(join(WORK, "x4.jsonl"), conditionsDir("x4", { "a.ts": DEFINITION("test_only_cli_draft", "pair", "standingPair.before") })), "--test-gote", fixture("g1.jsonl")], /draft: test_only_cli_draft/],
    ["知らない引数", () => [...base(join(WORK, "x5.jsonl"), conditionsDir("x5", {})), "--deep"], /知らない引数/],
    [
      "R-1 根の外の記録",
      () => {
        const outside = join(WORK, "outside-g1.jsonl");
        writeFileSync(outside, gateFixtureText("g1.jsonl"), "utf-8");
        return [...base(join(WORK, "x6.jsonl"), conditionsDir("x6", {})), "--test-gote", outside];
      },
      /根の外/,
    ],
    ["S-1 --test-person が記号の形でない", () => ["--person", "p2", "--test-person", "someone", ...base(join(WORK, "x7.jsonl"), conditionsDir("x7", {})).slice(4)], /--test-person は p1・p2 の形/],
  ])("止める(exit 1、--out を書かない): %s", (_label, argsOf, message) => {
    const args = argsOf();
    const out = args[args.indexOf("--out") + 1]!;
    const result = run(args);
    expect(result.status).toBe(1);
    expect(result.stderr).toMatch(message);
    expect(result.stdout).toBe(""); // 止めた実行は Markdown(ラベル・記録の数)を出さない
    expect(existsSync(out)).toBe(false);
  }, 60_000);

  it("I-9 gate.ts・lib/gate.ts・lib/gateOutput.ts はエンジンを import しない", () => {
    for (const file of ["./gate.ts", "./lib/gate.ts", "./lib/gateOutput.ts"]) {
      const imports = readFileSync(new URL(file, import.meta.url), "utf-8")
        .split("\n")
        .filter((line) => /^import /.test(line));
      expect(imports.filter((line) => /engine|usi|child_process/i.test(line)), file).toEqual([]);
    }
  });
});
