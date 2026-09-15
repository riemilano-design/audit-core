// STEP D1。diagnose.ts の配線を見張る(docs/STEP_D1_PLAN_2026-09-14.md 5.2。U6-I4(2) の check.test.ts と同じ形)。
//
// - ソース照合 … 呼び出しの 1 行を消す・渡す records を変える、を捕まえる(照合は片側にしか壊れない)
// - 子プロセス … diagnose.ts を実際に走らせ、標準出力が、同じ記録をこの試験のプロセスで lib に掛けて
//   描いたものと全文一致すること、--events の JSONL が同じ Failure Event を持つことを確かめる。
//   期待値は data から切り離してある(同じ lib で描き直して比べる。件数を固定しない ― P-20)。
// - T-6(STEP JSON v0 計画 6.2)… 子プロセスの --events の各行が、版の欄 schemaVersion を先頭に持ち、
//   今の版のスキーマを通ることを、同じ子プロセスの試験で確かめる。
// - STEP JSON v0.2 … 各行の末尾の provenance が、渡した記録のファイル(根の外なのでファイル名だけ)・そのバイトの sha256・
//   --evaluator の文・このリポジトリの HEAD・規則の値を持つことを、lib の組み立ての関数を通さずに見る(組み立ての誤りを両側で揃えないため)。
// - STEP JSON V0.3-META … 平手の記録と回した記録を並べ、各行の provenance.record.meta に自分の記録の meta の 7 欄が写ることと、
//   写せない meta(K-3)では --events を書かずに 0 でなく止まり、前の回のファイルが残ることを、組み立ての関数を通さずに見る。
//
// 【静かにスキップしない】npx・tsx・git が無ければ execFileSync が例外を投げて赤になる。
// 【一時ディレクトリ以外に書かない】走らせる前と後で git status(無視されるファイルも 1 本ずつ。
// node_modules だけを除く ― U6-I4(2) の計画書 9.4.1)が同じであることを確かめる。

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { MetaLine } from "./invariants/types.js";
import { renderDiagnosisTotals } from "./lib/diagnosisTotals.js";
import { buildDiagnosisReport, DRAFT_RULE_1, NOT_EVALUATION_CP, renderDiagnosisReport, type DiagnosisInput } from "./lib/failureEvent.js";
import { engineRef, FOLD_MOVES, FOLD_START, GAME01_MOVES, plantedRecords } from "./lib/failureEventFixtures.js";
import { buildProvenance, loadFailureEventSchema, toEventLine, validateFailureEventLine } from "./lib/failureEventSchema.js";
import { readGitState } from "./lib/gitState.js";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const DIAGNOSE_TS = join(PLAYTEST_DIR, "diagnose.ts");
// 固定例の meta の enginePath。相対の文字列だと、試験のプロセスと子プロセスで cwd を基準に違うパスへ直るので、根からの絶対パスにする
// (scripts/playtest から回しても根から回しても同じ結果。出どころには根からの相対 apps/server/engine/YaneuraOu-by-gcc が書かれる)
const ENGINE_PATH = join(REPO_ROOT, "apps", "server", "engine", "YaneuraOu-by-gcc");

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
    expect(source).toContain("  const entries = files.map(readInput);");
    expect(source).toContain("  const inputs = entries.map((entry) => entry.input);");
    // STEP D0-SIDE 段 1(R-9): error 行を集めて lib に渡している
    expect(source).toContain('  const errorLines = lines.filter((line) => line.kind === "error").map((line) => ({ reason: String((line as { reason?: unknown }).reason) }));');
    expect(source).toContain("meta, records, errorLines },");
    expect(source).toContain("  const report = buildDiagnosisReport(inputs, DRAFT_RULE_1);");
    // STEP D3(計画 Q-5): 入力ごとの表の後に群の合計の節を足した。合計の呼び出しもこの 1 行で見張る。
    expect(source).toContain('  console.log([...renderDiagnosisReport(report), ...renderDiagnosisTotals(report)].join("\\n"));');
    expect(source).toContain("row.result.events.map((event) => JSON.stringify(toEventLine(event, provenance)))");
    expect(source).toContain("rule: DRAFT_RULE_1, notEvaluationCp: NOT_EVALUATION_CP, repoRoot: REPO_ROOT,");
  });

  it(
    "子プロセス: 2 入力の JSONL に diagnose.ts を掛けると exit 0 で、出力と --events が、同じ記録を lib に掛けた結果と一致する(T-6: 各行は版の欄を先頭に持ち、スキーマを通る)",
    () => {
      const inputs: DiagnosisInput[] = [
        {
          kifuId: "d1-planted",
          meta: { kind: "meta", kifuId: "d1-planted", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH } as MetaLine,
          records: plantedRecords(GAME01_MOVES, { 48: engineRef(500, { afterPassMate: 3, dropCp: 350 }), 50: engineRef(-300) }),
          errorLines: [],
        },
        {
          kifuId: "d1-quiet",
          meta: { kind: "meta", kifuId: "d1-quiet", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH } as MetaLine,
          records: plantedRecords(GAME01_MOVES.slice(0, 20), { 10: engineRef(100), 12: engineRef(-600) }),
          errorLines: [],
        },
        // STEP D0-SIDE 段 1(R-9): error 行を持つ記録。数えずに「error 行のため使わない」行になり、Failure Event を書き出さない
        {
          kifuId: "d1-halted",
          meta: { kind: "meta", kifuId: "d1-halted", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH } as MetaLine,
          records: plantedRecords(GAME01_MOVES, { 48: engineRef(500, { afterPassMate: 3, dropCp: 350 }), 50: engineRef(-300) }),
          // STEP D0-SIDE 段 2(監査 A の任意 1): 理由を odd_move_count 以外にする。diagnose.ts が理由で error 行を絞る誤り(odd_move_count だけを集める等)を、
          // ソース照合の文字列一致だけでなく、この子プロセスでも捕まえるため
          errorLines: [{ reason: "human_move_error" }],
        },
      ];
      const dir = mkdtempSync(join(tmpdir(), "d1-diagnose-"));
      try {
        const paths = inputs.map((input) => {
          const filePath = join(dir, `${input.kifuId}.jsonl`);
          const errorLines = input.errorLines.map((line) => ({ kind: "error", reason: line.reason, message: "試験の error 行" }));
          writeFileSync(filePath, `${[input.meta, ...input.records, ...errorLines].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
          return filePath;
        });
        const eventsPath = join(dir, "events.jsonl");

        const before = gitStatus();
        // exit code が 0 以外なら execFileSync が例外を投げる(=赤)。npx・tsx が無くても例外で赤。
        const evaluator = "試験の評価関数(自己申告)";
        const stdout = execFileSync("npx", ["tsx", DIAGNOSE_TS, ...paths, "--events", eventsPath, "--evaluator", evaluator], { cwd: REPO_ROOT, encoding: "utf-8" });
        const after = gitStatus();
        expect(after).toBe(before);
        expect(readdirSync(dir).sort()).toEqual(["d1-halted.jsonl", "d1-planted.jsonl", "d1-quiet.jsonl", "events.jsonl"]);

        // 同じ記録を、ファイルを経由した形(JSON に書いて読み直した形)でこのプロセスの lib に掛ける
        const reread = inputs.map((input) => JSON.parse(JSON.stringify(input)) as DiagnosisInput);
        const report = buildDiagnosisReport(reread, DRAFT_RULE_1);
        // R-9: 3 本目は数えない。植えた死因①は 1 本目と同じなので、数えていれば Failure Event が出るはずの記録である
        expect(report.map((row) => row.result.kind)).toEqual(["counted", "counted", "excluded"]);
        // STEP D3(計画 Q-5): 2 入力なので合計の節が付く。節が空なら、この比べは合計の配線を見ていないことになる。
        expect(renderDiagnosisTotals(report).length).toBeGreaterThan(0);
        expect(stdout).toBe(`${[...renderDiagnosisReport(report), ...renderDiagnosisTotals(report)].join("\n")}\n`);

        const expectedEvents = report.flatMap((row) => (row.result.kind === "counted" ? row.result.events : []));
        expect(expectedEvents.length).toBeGreaterThan(0);
        const writtenEvents = readFileSync(eventsPath, "utf-8").trim().split("\n").map((line) => JSON.parse(line) as Record<string, unknown>);
        const analysisGit = readGitState(REPO_ROOT);
        const expectedLines = report.flatMap((row, index) =>
          row.result.kind === "counted"
            ? row.result.events.map((event) =>
                toEventLine(
                  event,
                  buildProvenance({
                    recordPath: paths[index]!,
                    recordSha256: createHash("sha256").update(readFileSync(paths[index]!)).digest("hex"),
                    meta: reread[index]!.meta,
                    evaluator,
                    analysisGit,
                    rule: DRAFT_RULE_1,
                    notEvaluationCp: NOT_EVALUATION_CP,
                    repoRoot: REPO_ROOT,
                  }),
                ),
              )
            : [],
        );
        expect(writtenEvents).toEqual(JSON.parse(JSON.stringify(expectedLines)));
        // STEP JSON v0.2: 出どころを、組み立ての関数を通さずに見る(記録は根の外の一時ディレクトリなのでファイル名だけ)
        const head = execFileSync("git", ["rev-parse", "HEAD"], { cwd: REPO_ROOT, encoding: "utf-8" }).trim();
        for (const line of writtenEvents) {
          const provenance = line.provenance as { record: { path: string; sha256: string }; evaluator: { declared: string | null }; analysis: { gitHead: string | null; rule: Record<string, number> } };
          const fileName = `${line.kifuId as string}.jsonl`;
          expect(provenance.record.path).toBe(fileName);
          expect(provenance.record.sha256).toBe(createHash("sha256").update(readFileSync(join(dir, fileName))).digest("hex"));
          expect(provenance.evaluator.declared).toBe(evaluator);
          expect(provenance.analysis.gitHead).toBe(head);
          expect(provenance.analysis.rule).toEqual({ advantageCp: 300, dropCp: -400, windowPlies: 5, focusDropCp: 300, notEvaluationCp: 30000 });
        }
        // T-6(STEP JSON v0 計画 6.2): toEqual は欄の順を見ないので、先頭であることは別に見る。版は定数でなく値で見る
        const schema = loadFailureEventSchema();
        for (const line of writtenEvents) {
          expect(Object.keys(line)[0]).toBe("schemaVersion");
          expect(line.schemaVersion).toBe("0.3");
          expect(validateFailureEventLine(line, schema)).toEqual([]);
        }
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );

  it(
    "--evaluator を値なし(末尾)・空の文・空白だけ・次の旗(--evaluator --events)で渡すと、exit 0 以外で止まり、--events を書かない",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d1-diagnose-evaluator-"));
      try {
        const recordPath = join(dir, "d1-quiet.jsonl");
        const meta = { kind: "meta", kifuId: "d1-quiet", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH };
        const records = plantedRecords(GAME01_MOVES.slice(0, 20), { 10: engineRef(100), 12: engineRef(-600) });
        writeFileSync(recordPath, `${[meta, ...records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
        const eventsPath = join(dir, "events.jsonl");
        const cases: [string, string[]][] = [
          ["末尾の --evaluator", [recordPath, "--events", eventsPath, "--evaluator"]],
          ["空の文", [recordPath, "--events", eventsPath, "--evaluator", ""]],
          ["空白だけ", [recordPath, "--events", eventsPath, "--evaluator", "  "]],
          ["次の旗", [recordPath, "--evaluator", "--events", eventsPath]],
        ];
        for (const [name, args] of cases) {
          let failure: { status: number | null; stderr: string } | undefined;
          try {
            execFileSync("npx", ["tsx", DIAGNOSE_TS, ...args], { cwd: REPO_ROOT, encoding: "utf-8", stdio: "pipe" });
          } catch (error) {
            failure = error as { status: number | null; stderr: string };
          }
          expect(failure, `${name}: 止まらなかった`).toBeDefined();
          expect(failure!.status, name).not.toBe(0);
          // 別の理由(tsx が無い・TypeError 等)で落ちたのを「止めた」と読まないよう、例外の名前つきの止めた文で確かめる。
          // 文だけだと、tsx が標準エラーに出す code frame(`throw new Error("--evaluator …` のソースの行)にも一致してしまう(B の変異 Z-1)
          expect(String(failure!.stderr), name).toContain("Error: --evaluator に評価関数の識別の文を渡してください");
          expect(existsSync(eventsPath), name).toBe(false);
        }
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );

  // STEP JSON V0.3-META(計画 6.2)。1 本目は平手の記録、2 本目は回した記録(1 本目の meta を全部の行に付ける誤り M-13 を捕まえる)
  it(
    "V0.3-META 子プロセス: 平手の記録と回した記録を並べて --events を書くと、各行の provenance.record.meta に自分の記録の meta の 7 欄が写る(組み立ての関数を通さずに見る)",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "json03-diagnose-"));
      try {
        const plainMeta = { kind: "meta", kifuId: "json03-plain", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH };
        const foldMeta = {
          kind: "meta",
          kifuId: "json03-fold",
          startedAt: "t",
          gitHead: null,
          enginePath: ENGINE_PATH,
          mirrored: true,
          originalUserSide: "gote",
          plyOffset: 1,
          startSfen: FOLD_START,
          sideAlignmentChecked: true,
          trailingMoveTruncated: true,
          truncatedTrailingMove: "2g2f",
        };
        const inputs: Array<[string, object, unknown[]]> = [
          ["json03-plain", plainMeta, plantedRecords(GAME01_MOVES, { 48: engineRef(500, { afterPassMate: 3, dropCp: 350 }), 50: engineRef(-300) })],
          ["json03-fold", foldMeta, plantedRecords(FOLD_MOVES, { 0: engineRef(500), 2: engineRef(-500) }, {}, FOLD_START)],
        ];
        const paths = inputs.map(([name, meta, records]) => {
          const filePath = join(dir, `${name}.jsonl`);
          writeFileSync(filePath, `${[meta, ...records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
          return filePath;
        });
        const eventsPath = join(dir, "events.jsonl");
        const before = gitStatus();
        execFileSync("npx", ["tsx", DIAGNOSE_TS, ...paths, "--events", eventsPath], { cwd: REPO_ROOT, encoding: "utf-8" });
        expect(gitStatus()).toBe(before);

        const lines = readFileSync(eventsPath, "utf-8").trim().split("\n").map((line) => JSON.parse(line) as Record<string, unknown>);
        const metaOf = (line: Record<string, unknown>): Record<string, unknown> => (line.provenance as { record: { meta: Record<string, unknown> } }).record.meta;
        const seven = ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked", "trailingMoveTruncated", "truncatedTrailingMove"];
        const plainLines = lines.filter((line) => line.kifuId === "json03-plain");
        const foldLines = lines.filter((line) => line.kifuId === "json03-fold");
        expect(plainLines.length).toBeGreaterThan(0);
        expect(foldLines.length).toBeGreaterThan(0);
        const schema = loadFailureEventSchema();
        for (const line of plainLines) {
          const meta = metaOf(line);
          expect(seven.filter((key) => Object.hasOwn(meta, key))).toEqual([]);
          expect(meta.unrecordedKeys).toEqual(["dirty", "searchMode", "nodes", "threads", ...seven]);
          expect(line.schemaVersion).toBe("0.3");
          expect(validateFailureEventLine(line, schema)).toEqual([]);
        }
        for (const line of foldLines) {
          const meta = metaOf(line);
          expect(Object.fromEntries(seven.filter((key) => Object.hasOwn(meta, key)).map((key) => [key, meta[key]]))).toEqual({
            mirrored: true,
            originalUserSide: "gote",
            plyOffset: 1,
            startSfen: "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2",
            sideAlignmentChecked: true,
            trailingMoveTruncated: true,
            truncatedTrailingMove: "2g2f",
          });
          expect(meta.unrecordedKeys).toEqual(["dirty", "searchMode", "nodes", "threads"]);
          expect(line.schemaVersion).toBe("0.3");
          expect(validateFailureEventLine(line, schema)).toEqual([]);
        }
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );

  it(
    "V0.3-META 子プロセス(K-3): 出どころに写せない meta(回した局に plyOffset が無い)の記録では、exit 0 以外で止まり、--events を書かない(前の回のファイルはそのまま残る)",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "json03-diagnose-k3-"));
      try {
        const meta = {
          kind: "meta",
          kifuId: "json03-broken",
          startedAt: "t",
          gitHead: null,
          enginePath: ENGINE_PATH,
          mirrored: true,
          originalUserSide: "gote",
          startSfen: FOLD_START,
          sideAlignmentChecked: true,
          trailingMoveTruncated: false,
        };
        const records = plantedRecords(FOLD_MOVES, { 0: engineRef(500), 2: engineRef(-500) }, {}, FOLD_START);
        const recordPath = join(dir, "json03-broken.jsonl");
        writeFileSync(recordPath, `${[meta, ...records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
        const eventsPath = join(dir, "events.jsonl");
        const previous = "前の回の行\n";
        writeFileSync(eventsPath, previous, "utf-8");
        let failure: { status: number | null; stderr: string } | undefined;
        try {
          execFileSync("npx", ["tsx", DIAGNOSE_TS, recordPath, "--events", eventsPath], { cwd: REPO_ROOT, encoding: "utf-8", stdio: "pipe" });
        } catch (error) {
          failure = error as { status: number | null; stderr: string };
        }
        expect(failure, "止まらなかった").toBeDefined();
        expect(failure!.status).not.toBe(0);
        // 止めた文は、実行時の値(記録の kifuId と、食い違った欄の名前)で見る。ソースの code frame にはこの 2 つが値の形で出ない(v0.2 の Z-1 の教訓)
        expect(String(failure!.stderr)).toContain("記録 json03-broken の meta が");
        expect(String(failure!.stderr)).toContain("欄 plyOffset:");
        expect(readFileSync(eventsPath, "utf-8")).toBe(previous);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );
});
