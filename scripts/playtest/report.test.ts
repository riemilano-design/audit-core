// STEP D6(docs/STEP_D6_PLAN_2026-09-16.md §6)。report.ts の CLI を見張る。**エンジン・LLM は使わない。**
// 数・文・確かめは lib/diagnosisReport.test.ts が見る。ここは、読む・定義を読み込む・lib を呼ぶ・書く・止まる、だけを見る。

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { GATE_VALUES } from "./lib/gate.js";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const REPORT_TS = join(PLAYTEST_DIR, "report.ts");

const gitStatus = (): string =>
  execFileSync(
    "git",
    ["status", "--porcelain", "-z", "--untracked-files=all", "--ignored", "--", ".", ":(exclude,glob)**/node_modules", ":(exclude,glob)**/node_modules/**"],
    { cwd: REPO_ROOT },
  ).toString();

function run(args: string[]): { status: number; stdout: string; stderr: string } {
  try {
    const stdout = execFileSync("npx", ["tsx", REPORT_TS, ...args], { cwd: REPO_ROOT, encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] });
    return { status: 0, stdout, stderr: "" };
  } catch (error) {
    const failure = error as { status: number | null; stdout: string; stderr: string };
    return { status: failure.status ?? -1, stdout: String(failure.stdout), stderr: String(failure.stderr) };
  }
}

const DEFINITION_SOURCE = `export default {
  id: "test_only_cli",
  label: "試験だけの定義(仮)",
  status: "approved",
  definitionText: "試験だけ",
  readableText: "試験だけの条件の文",
  uses: [],
  thresholds: {},
  appliesTo: ["pair"],
  approval: { approvedBy: "試験", date: "2026-09-16", record: "試験" },
  evaluate: () => true,
};
`;

function collapse(denominator: number, collapsed: number, games: number, ahead: number) {
  const aheadCollapsed = Math.min(collapsed, ahead);
  return {
    pairs: denominator + 8,
    collapsed,
    denominator,
    excluded: { beforeUndetermined: 1, afterUndetermined: 1, cannotFall: 1 },
    transitions: { aheadToLevel: aheadCollapsed, levelToBehind: collapsed - aheadCollapsed, aheadToBehind: 0 },
    byBefore: { ahead: { collapsed: aheadCollapsed, denominator: ahead }, level: { collapsed: collapsed - aheadCollapsed, denominator: denominator - ahead } },
    gamesWithDenominator: games,
    within5: { dropped: collapsed, denominator },
  };
}

const inputs = (count: number, prefix: string) => Array.from({ length: count }, (_, index) => ({ path: `records/test_only/${prefix}${index}.jsonl`, sha256: (index + 1).toString(16).padStart(64, "0") }));

function gateLineFor(definitionSha256: string): Record<string, unknown> {
  return {
    contract: "diagnosis-gate",
    schemaVersion: "0.1",
    person: "p2",
    testPerson: "p1",
    condition: { id: "test_only_cli", label: "試験だけの定義(仮)", status: "approved", definitionSha256 },
    source: { referenceNodes: 4000000, evaluation: "light" },
    material: { inputs: inputs(20, "m"), tally: { games: 20, truePairs: collapse(23, 11, 7, 8), falsePairs: collapse(341, 29, 20, 120), pvSide: { state: "applicable", n: 19, actualTrue: 13, pvTrue: 5 } } },
    test: { set: "sente6", provisional: true, inputs: inputs(6, "t"), tally: { games: 6, truePairs: collapse(4, 2, 3, 2), falsePairs: collapse(90, 17, 6, 30), pvSide: { state: "applicable", n: 7, actualTrue: 3, pvTrue: 1 } } },
    gate: { items: (["G-1", "G-2", "G-3", "G-4"] as const).map((item) => ({ item, values: {}, threshold: {}, result: "met", reasons: [] })), verdict: "meets", text: "追加検証する価値のある個人パターン候補" },
    gateValues: { ...GATE_VALUES },
    conditionsInRun: 1,
    provenance: { gitHead: "g", dirty: false },
  };
}

describe("report.ts(計画 §6)", () => {
  it("ソース照合: report.ts は定義を loadCondition で読み、lib の buildDiagnosisReport に渡し、行と Markdown の両方を書く。lib の確かめに当たれば書かずに exit 1", () => {
    const source = readFileSync(REPORT_TS, "utf8");
    expect(source).toContain("    const loaded = await loadCondition(path.join(conditionsArg, name));\n");
    expect(source).toContain("  const report = buildDiagnosisReport(\n");
    expect(source).toContain('  writeFileSync(outPath, `${report.lines.map((line) => JSON.stringify(line)).join("\\n")}\\n`, "utf-8");\n');
    expect(source).toContain('  writeFileSync(mdPath, `${report.markdown.join("\\n")}\\n`, "utf-8");\n');
    expect(source).toContain("  if (error instanceof ReportInputError || error instanceof ReportOutputError) {\n");
    expect(source.indexOf("buildDiagnosisReport(\n")).toBeLessThan(source.indexOf("writeFileSync(outPath"));
  });

  it(
    "子プロセス: 定義のファイルと Gate の行から person の報告を書く。入力の確かめに当たれば exit 1 で何も書かない。引数が足りなければ exit 1",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d6-report-"));
      try {
        const before = gitStatus();
        const conditions = join(dir, "conditions");
        mkdirSync(conditions);
        writeFileSync(join(conditions, "test_only_cli.ts"), DEFINITION_SOURCE, "utf-8");
        const sha = createHash("sha256").update(DEFINITION_SOURCE).digest("hex");
        const gate = join(dir, "gate.jsonl");
        writeFileSync(gate, `${JSON.stringify(gateLineFor(sha))}\n`, "utf-8");
        const out = join(dir, "report.jsonl");
        const md = join(dir, "report.md");

        const ok = run(["--gate", gate, "--conditions", conditions, "--audience", "person", "--out", out, "--md", md]);
        expect(ok.status, ok.stderr).toBe(0);
        const lines = readFileSync(out, "utf-8").trim().split("\n").map((text) => JSON.parse(text) as { lineKind: string; sentences: Array<{ text: string }>; input: { path: string } });
        expect(lines.map((line) => line.lineKind)).toStrictEqual(["condition", "summary"]);
        expect(lines[0]!.sentences[0]!.text).toBe("条件 test_only_cli: 試験だけの条件の文");
        expect(lines[0]!.input.path).toBe("gate.jsonl");
        expect(readFileSync(md, "utf-8")).toContain("## 条件 test_only_cli: 試験だけの条件の文");

        const brokenOut = join(dir, "broken.jsonl");
        const brokenMd = join(dir, "broken.md");
        writeFileSync(gate, `${JSON.stringify(gateLineFor("0".repeat(64)))}\n`, "utf-8");
        const broken = run(["--gate", gate, "--conditions", conditions, "--audience", "person", "--out", brokenOut, "--md", brokenMd]);
        expect(broken.status).toBe(1);
        expect(broken.stderr).toContain("ReportInputError");
        expect(broken.stderr).toContain("definitionSha256 の定義のファイルが無い");
        expect([existsSync(brokenOut), existsSync(brokenMd)]).toStrictEqual([false, false]);

        const usage = run(["--gate", gate, "--audience", "person"]);
        expect(usage.status).toBe(1);
        expect(usage.stderr).toContain("使い方: npx tsx scripts/playtest/report.ts --gate <gate.jsonl>");
        expect(gitStatus()).toBe(before);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    120_000,
  );
});
