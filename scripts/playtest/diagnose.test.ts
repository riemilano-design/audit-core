// STEP D1。diagnose.ts の配線を見張る(docs/STEP_D1_PLAN_2026-09-14.md 5.2。U6-I4(2) の check.test.ts と同じ形)。
//
// - ソース照合 … 呼び出しの 1 行を消す・渡す records を変える、を捕まえる(照合は片側にしか壊れない)
// - 子プロセス … diagnose.ts を実際に走らせ、標準出力が、同じ記録をこの試験のプロセスで lib に掛けて
//   描いたものと全文一致すること、--events の JSONL が同じ Failure Event を持つことを確かめる。
//   期待値は data から切り離してある(同じ lib で描き直して比べる。件数を固定しない ― P-20)。
//
// 【静かにスキップしない】npx・tsx・git が無ければ execFileSync が例外を投げて赤になる。
// 【一時ディレクトリ以外に書かない】走らせる前と後で git status(無視されるファイルも 1 本ずつ。
// node_modules だけを除く ― U6-I4(2) の計画書 9.4.1)が同じであることを確かめる。

import { execFileSync } from "node:child_process";
import { mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { MetaLine } from "./invariants/types.js";
import { renderDiagnosisTotals } from "./lib/diagnosisTotals.js";
import { buildDiagnosisReport, DRAFT_RULE_1, renderDiagnosisReport, type DiagnosisInput } from "./lib/failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords } from "./lib/failureEventFixtures.js";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const DIAGNOSE_TS = join(PLAYTEST_DIR, "diagnose.ts");

const gitStatus = (): string =>
  execFileSync(
    "git",
    [
      "status",
      "--porcelain",
      "-z",
      "--untracked-files=all",
      "--ignored",
      "--",
      ".",
      ":(exclude,glob)**/node_modules",
      ":(exclude,glob)**/node_modules/**",
    ],
    { cwd: REPO_ROOT },
  ).toString();

describe("diagnose.ts(計画 5.2)", () => {
  it("ソース照合: 読んだ記録をそのまま渡して組み立て、描いた行を出し、Failure Event を書き出している", () => {
    const source = readFileSync(DIAGNOSE_TS, "utf8");
    expect(source).toContain("  const inputs = files.map(readInput);");
    expect(source).toContain("  const report = buildDiagnosisReport(inputs, DRAFT_RULE_1);");
    // STEP D3(計画 Q-5): 入力ごとの表の後に群の合計の節を足した。合計の呼び出しもこの 1 行で見張る。
    expect(source).toContain('  console.log([...renderDiagnosisReport(report), ...renderDiagnosisTotals(report)].join("\\n"));');
    expect(source).toContain("row.result.events.map((event) => JSON.stringify(event))");
  });

  it(
    "子プロセス: 2 入力の JSONL に diagnose.ts を掛けると exit 0 で、出力と --events が、同じ記録を lib に掛けた結果と一致する",
    () => {
      const inputs: DiagnosisInput[] = [
        {
          kifuId: "d1-planted",
          meta: { kind: "meta", kifuId: "d1-planted", startedAt: "t", gitHead: null, enginePath: "-" } as MetaLine,
          records: plantedRecords(GAME01_MOVES, { 48: engineRef(500, { afterPassMate: 3, dropCp: 350 }), 50: engineRef(-300) }),
        },
        {
          kifuId: "d1-quiet",
          meta: { kind: "meta", kifuId: "d1-quiet", startedAt: "t", gitHead: null, enginePath: "-" } as MetaLine,
          records: plantedRecords(GAME01_MOVES.slice(0, 20), { 10: engineRef(100), 12: engineRef(-600) }),
        },
      ];
      const dir = mkdtempSync(join(tmpdir(), "d1-diagnose-"));
      try {
        const paths = inputs.map((input) => {
          const filePath = join(dir, `${input.kifuId}.jsonl`);
          writeFileSync(filePath, `${[input.meta, ...input.records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
          return filePath;
        });
        const eventsPath = join(dir, "events.jsonl");

        const before = gitStatus();
        // exit code が 0 以外なら execFileSync が例外を投げる(=赤)。npx・tsx が無くても例外で赤。
        const stdout = execFileSync("npx", ["tsx", DIAGNOSE_TS, ...paths, "--events", eventsPath], { cwd: REPO_ROOT, encoding: "utf-8" });
        const after = gitStatus();
        expect(after).toBe(before);
        expect(readdirSync(dir).sort()).toEqual(["d1-planted.jsonl", "d1-quiet.jsonl", "events.jsonl"]);

        // 同じ記録を、ファイルを経由した形(JSON に書いて読み直した形)でこのプロセスの lib に掛ける
        const reread = inputs.map((input) => JSON.parse(JSON.stringify(input)) as DiagnosisInput);
        const report = buildDiagnosisReport(reread, DRAFT_RULE_1);
        // STEP D3(計画 Q-5): 2 入力なので合計の節が付く。節が空なら、この比べは合計の配線を見ていないことになる。
        expect(renderDiagnosisTotals(report).length).toBeGreaterThan(0);
        expect(stdout).toBe(`${[...renderDiagnosisReport(report), ...renderDiagnosisTotals(report)].join("\n")}\n`);

        const expectedEvents = report.flatMap((row) => (row.result.kind === "counted" ? row.result.events : []));
        expect(expectedEvents.length).toBeGreaterThan(0);
        const writtenEvents = readFileSync(eventsPath, "utf-8").trim().split("\n").map((line) => JSON.parse(line));
        expect(writtenEvents).toEqual(JSON.parse(JSON.stringify(expectedEvents)));
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );
});
