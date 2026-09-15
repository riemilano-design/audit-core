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
// - STEP D2(監査 1e の R-1)… 64KB を超える Markdown を子プロセスからパイプで受けても末尾まで届くこと(process.exit で終わると黙って切れる)。
// - STEP D2(監査 1e の任意 N-1)… 表の後に K-3 で止まる入力を置いても、パイプで表の末尾まで届いてから exit 1 で止まること(捕まえない例外で止まると切れる)。
// - STEP D1b … --events-rise・--events-maxdrop を付けても --events と表が変わらないこと(G-9)、K-3 で 3 つのファイルのどれも書き換えないこと(G-16)、
//   旗を 1 つだけ渡しても、そのファイルは 2 つを一緒に渡した回と同じこと(監査 A の S-1)。
// - STEP D-SCREEN-2 … 段 2 の記録とその段 1 を一緒に渡すと表を書かずに exit 1(S-14)、段 2 の記録だけなら行に出どころの欄が出ること。
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
import { POSITION_FACTS_RULES } from "./lib/counterfactual.js";
import { renderDiagnosisTotals } from "./lib/diagnosisTotals.js";
import { diagnosisMomentsOf, loadDiagnosisMomentSchema, toMomentLine } from "./lib/diagnosisMoment.js";
import { validate } from "./lib/eventSchema.js";
import { buildDiagnosisReport, DRAFT_RULE_1, NOT_EVALUATION_CP, renderDiagnosisReport, STANDING_BOUNDS, type DiagnosisInput } from "./lib/failureEvent.js";
import { engineRef, FOLD_MOVES, FOLD_START, GAME01_MOVES, plantedRecords } from "./lib/failureEventFixtures.js";
import { buildProvenance, FAILURE_EVENT_SCHEMA_VERSION, loadFailureEventSchema, toEventLine, validateFailureEventLine } from "./lib/failureEventSchema.js";
import { readGitState } from "./lib/gitState.js";
import { initialSfenOf } from "./lib/sideAlignment.js";

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
    expect(source).toContain("rule: DRAFT_RULE_1, notEvaluationCp: NOT_EVALUATION_CP, standingBounds: STANDING_BOUNDS, positionFactsRules: POSITION_FACTS_RULES, repoRoot: REPO_ROOT,");
    // STEP D2(監査 1e の R-1): 終わるときに process.exit を呼ばない(パイプの標準出力が書き終わる前に切れる。子プロセスの試験 R-1 でも見る)
    expect(source).not.toContain("process.exit(");
    // STEP D1b: 上がりと最大の下がりを同じ記録・規則・開始局面・出どころで組み立て、3 つのファイルは全部の行を作ってから書く
    expect(source).toContain("        const moments = diagnosisMomentsOf(entry.input.kifuId, entry.input.records, DRAFT_RULE_1, initialSfenOf(entry.input.meta), row.result.events, screen);");
    // STEP D-SCREEN-2(計画 §3・S-14): 表を書く前に段 2 とその段 1 の組を確かめ、moment にも Failure Event と同じ screen を渡す
    expect(source).toContain("  const conflicts = screenInputConflicts(entries.map((entry) => ({ name: entry.filePath, kifuId: entry.input.kifuId, sha256: entry.sha256, meta: entry.input.meta })));\n");
    expect(source).toContain('  if (conflicts.length > 0) throw new ScreenInputConflictError(conflicts.join(" / "));\n');
    expect(source.indexOf("screenInputConflicts(entries")).toBeLessThan(source.indexOf("buildDiagnosisReport(inputs"));
    expect(source).toContain("        const screen = screenOfRecord(entry.input.kifuId, entry.input.meta, entry.input.records);\n");
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
                    standingBounds: STANDING_BOUNDS,
                    positionFactsRules: POSITION_FACTS_RULES,
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
          expect(provenance.analysis.rule).toEqual({
            advantageCp: 300,
            dropCp: -400,
            windowPlies: 5,
            focusDropCp: 300,
            notEvaluationCp: 30000,
            standing: { aheadCp: 300, behindCp: -300 },
            positionFacts: { zone: "king_and_eight_neighbors", reach: "non_king_pieces", control: "squares" },
          });
        }
        // T-6(STEP JSON v0 計画 6.2): toEqual は欄の順を見ないので、先頭であることは別に見る。
        // 版は 1 か所の定数(lib/schemaVersions.ts。STEP D-SCREEN-2)で見る。定数の値の誤りは、今の版のスキーマの schemaVersion の const で落ちる
        const schema = loadFailureEventSchema();
        for (const line of writtenEvents) {
          expect(Object.keys(line)[0]).toBe("schemaVersion");
          expect(line.schemaVersion).toBe(FAILURE_EVENT_SCHEMA_VERSION);
          expect(validateFailureEventLine(line, schema)).toEqual([]);
        }
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );

  // STEP D2(監査 1e の R-1)。D2 の節で Markdown が 64KB を超えるようになった(records/d3-nnue で約 112KB)。process.exit で終わると、
  // パイプで受けた標準出力が書き終わる前にプロセスが止まり、exit 0 のまま末尾が消える。execFileSync の標準出力はパイプである
  it(
    "子プロセス(R-1): 64KB を超える Markdown をパイプで受けても末尾まで届き、同じ記録を lib に掛けて描いたものと全文一致する(exit 0)",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d2-diagnose-pipe-"));
      try {
        const records = plantedRecords(GAME01_MOVES, { 48: engineRef(500, { afterPassMate: 3, dropCp: 350 }), 50: engineRef(-300) });
        // 1 本あたり約 760 バイト(B が数えた)。200 本で 64KB の 2 倍を超える(下で確かめる)
        const inputs: DiagnosisInput[] = Array.from({ length: 200 }, (_, index) => {
          const kifuId = `d2-pipe-${String(index).padStart(3, "0")}`;
          return { kifuId, meta: { kind: "meta", kifuId, startedAt: "t", gitHead: null, enginePath: ENGINE_PATH } as MetaLine, records, errorLines: [] };
        });
        const paths = inputs.map((input) => {
          const filePath = join(dir, `${input.kifuId}.jsonl`);
          writeFileSync(filePath, `${[input.meta, ...input.records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
          return filePath;
        });
        const before = gitStatus();
        const stdout = execFileSync("npx", ["tsx", DIAGNOSE_TS, ...paths], { cwd: REPO_ROOT, encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
        expect(gitStatus()).toBe(before);
        const report = buildDiagnosisReport(inputs.map((input) => JSON.parse(JSON.stringify(input)) as DiagnosisInput), DRAFT_RULE_1);
        const expected = `${[...renderDiagnosisReport(report), ...renderDiagnosisTotals(report)].join("\n")}\n`;
        expect(Buffer.byteLength(expected, "utf-8")).toBeGreaterThan(2 * 65536);
        // 切れたときに何バイト・何行届いたかが読めるよう、全文の比べの前にバイト数と行数を見る
        expect(Buffer.byteLength(stdout, "utf-8")).toBe(Buffer.byteLength(expected, "utf-8"));
        expect(stdout.split("\n").length).toBe(expected.split("\n").length);
        expect(stdout).toBe(expected);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    120_000,
  );

  // STEP D2(監査 1e の任意 N-1、司令塔の決定 (b))。R-1 と同じ原因で、例外で止まる経路(K-3 の meta)も、捕まえない例外で止まると
  // パイプの標準出力が 64KB で切れた(0 でない終了のまま)。表の後に K-3 で止まる入力を置き、表の末尾まで届いてから exit 1 で止まることを見る
  it(
    "子プロセス(N-1): 64KB を超える表の後に K-3 で止まる入力を置いても、パイプで表の末尾まで届き、exit 1 で名前つきの文を標準エラーに書き、--events を書かない",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d2-diagnose-pipe-k3-"));
      try {
        const records = plantedRecords(GAME01_MOVES, { 48: engineRef(500, { afterPassMate: 3, dropCp: 350 }), 50: engineRef(-300) });
        const inputs: DiagnosisInput[] = Array.from({ length: 200 }, (_, index) => {
          const kifuId = `d2-pipe-k3-${String(index).padStart(3, "0")}`;
          return { kifuId, meta: { kind: "meta", kifuId, startedAt: "t", gitHead: null, enginePath: ENGINE_PATH } as MetaLine, records, errorLines: [] };
        });
        // 最後の 1 本は K-3(回した局に plyOffset が無い)。表には並ぶが、--events の出どころを組み立てるところで止まる
        const brokenMeta = {
          kind: "meta",
          kifuId: "d2-pipe-k3-broken",
          startedAt: "t",
          gitHead: null,
          enginePath: ENGINE_PATH,
          mirrored: true,
          originalUserSide: "gote",
          startSfen: FOLD_START,
          sideAlignmentChecked: true,
          trailingMoveTruncated: false,
        };
        inputs.push({
          kifuId: "d2-pipe-k3-broken",
          meta: brokenMeta as unknown as MetaLine,
          records: plantedRecords(FOLD_MOVES, { 0: engineRef(500), 2: engineRef(-500) }, {}, FOLD_START),
          errorLines: [],
        });
        const paths = inputs.map((input) => {
          const filePath = join(dir, `${input.kifuId}.jsonl`);
          writeFileSync(filePath, `${[input.meta, ...input.records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
          return filePath;
        });
        const eventsPath = join(dir, "events.jsonl");
        const before = gitStatus();
        let failure: { status: number | null; stdout: string; stderr: string } | undefined;
        try {
          execFileSync("npx", ["tsx", DIAGNOSE_TS, ...paths, "--events", eventsPath], { cwd: REPO_ROOT, encoding: "utf-8", stdio: "pipe", maxBuffer: 64 * 1024 * 1024 });
        } catch (error) {
          failure = error as { status: number | null; stdout: string; stderr: string };
        }
        expect(gitStatus()).toBe(before);
        expect(failure, "止まらなかった").toBeDefined();
        expect(failure!.status).toBe(1);
        const report = buildDiagnosisReport(inputs.map((input) => JSON.parse(JSON.stringify(input)) as DiagnosisInput), DRAFT_RULE_1);
        const expected = `${[...renderDiagnosisReport(report), ...renderDiagnosisTotals(report)].join("\n")}\n`;
        expect(Buffer.byteLength(expected, "utf-8")).toBeGreaterThan(2 * 65536);
        // 切れたときに何バイト・何行届いたかが読めるよう、全文の比べの前にバイト数と行数を見る
        const stdout = String(failure!.stdout);
        expect(Buffer.byteLength(stdout, "utf-8")).toBe(Buffer.byteLength(expected, "utf-8"));
        expect(stdout.split("\n").length).toBe(expected.split("\n").length);
        expect(stdout).toBe(expected);
        // 止めた文は、例外の名前と実行時の値(記録の kifuId・食い違った欄の名前)で見る
        expect(String(failure!.stderr)).toContain("InvalidProvenanceMetaError: 記録 d2-pipe-k3-broken の meta が");
        expect(String(failure!.stderr)).toContain("欄 plyOffset:");
        expect(existsSync(eventsPath)).toBe(false);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    120_000,
  );

  // STEP D1b(docs/STEP_D1b_PLAN_2026-09-15.md G-9)。--events-rise・--events-maxdrop を付けても、--events の行と標準出力の表は旗なしと同じ。
  // 上がりと最大の下がりの行は、同じ記録を lib に掛けて組み立てた行と一致し、契約 diagnosis-moment v0.2 のスキーマを通る
  it(
    "子プロセス(D1b の G-9): 上がり・最大の下がりの旗を付けても --events と表は旗なしとバイト一致で、2 つのファイルは lib の行と一致しスキーマを通る",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d1b-diagnose-"));
      try {
        const inputs: DiagnosisInput[] = [
          {
            kifuId: "d1b-rise",
            meta: { kind: "meta", kifuId: "d1b-rise", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH } as MetaLine,
            records: plantedRecords(GAME01_MOVES, { 20: engineRef(100, { bestmove: "3g2h" }), 22: engineRef(600) }),
            errorLines: [],
          },
          {
            kifuId: "d1b-quiet",
            meta: { kind: "meta", kifuId: "d1b-quiet", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH } as MetaLine,
            records: plantedRecords(GAME01_MOVES.slice(0, 6), { 0: engineRef(0), 2: engineRef(10), 4: engineRef(20), 6: engineRef(30) }),
            errorLines: [],
          },
        ];
        const paths = inputs.map((input) => {
          const filePath = join(dir, `${input.kifuId}.jsonl`);
          writeFileSync(filePath, `${[input.meta, ...input.records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
          return filePath;
        });
        const plainEvents = join(dir, "plain-events.jsonl");
        const events = join(dir, "events.jsonl");
        const rise = join(dir, "rise.jsonl");
        const maxDrop = join(dir, "maxdrop.jsonl");
        const before = gitStatus();
        const plainStdout = execFileSync("npx", ["tsx", DIAGNOSE_TS, ...paths, "--events", plainEvents], { cwd: REPO_ROOT, encoding: "utf-8" });
        const stdout = execFileSync("npx", ["tsx", DIAGNOSE_TS, ...paths, "--events", events, "--events-rise", rise, "--events-maxdrop", maxDrop], { cwd: REPO_ROOT, encoding: "utf-8" });
        expect(gitStatus()).toBe(before);
        expect(stdout).toBe(plainStdout);
        expect(readFileSync(events)).toEqual(readFileSync(plainEvents));

        const reread = inputs.map((input) => JSON.parse(JSON.stringify(input)) as DiagnosisInput);
        const report = buildDiagnosisReport(reread, DRAFT_RULE_1);
        const analysisGit = readGitState(REPO_ROOT);
        const expectedRise: unknown[] = [];
        const expectedMaxDrop: unknown[] = [];
        report.forEach((row, index) => {
          if (row.result.kind !== "counted") throw new Error(`${row.kifuId} が数えられなかった`);
          const provenance = buildProvenance({
            recordPath: paths[index]!,
            recordSha256: createHash("sha256").update(readFileSync(paths[index]!)).digest("hex"),
            meta: reread[index]!.meta,
            evaluator: null,
            analysisGit,
            rule: DRAFT_RULE_1,
            notEvaluationCp: NOT_EVALUATION_CP,
            standingBounds: STANDING_BOUNDS,
            positionFactsRules: POSITION_FACTS_RULES,
            repoRoot: REPO_ROOT,
          });
          const moments = diagnosisMomentsOf(reread[index]!.kifuId, reread[index]!.records, DRAFT_RULE_1, initialSfenOf(reread[index]!.meta), row.result.events);
          expectedRise.push(...moments.rises.map((moment) => toMomentLine(moment, provenance)));
          expectedMaxDrop.push(toMomentLine(moments.maxDrop, provenance));
        });
        const readLines = (file: string) => readFileSync(file, "utf-8").split("\n").filter((line) => line.length > 0).map((line) => JSON.parse(line) as Record<string, unknown>);
        const riseLines = readLines(rise);
        const maxDropLines = readLines(maxDrop);
        // 1 本目は上がり 1 件、2 本目は 0 件。最大の下がりは入力 1 本につき 1 行(1 本目は組の行、2 本目は noDrop)
        expect(riseLines.map((line) => [line.kifuId, line.branchPly])).toEqual([["d1b-rise", 21]]);
        expect(maxDropLines.map((line) => [line.kifuId, line.state ?? line.branchPly])).toEqual([
          ["d1b-rise", 23],
          ["d1b-quiet", "noDrop"],
        ]);
        expect(riseLines).toEqual(JSON.parse(JSON.stringify(expectedRise)));
        expect(maxDropLines).toEqual(JSON.parse(JSON.stringify(expectedMaxDrop)));
        const momentSchema = loadDiagnosisMomentSchema();
        for (const line of [...riseLines, ...maxDropLines]) expect(validate(line, momentSchema)).toEqual([]);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    120_000,
  );

  // STEP D1b(監査 A の推奨 S-1)。新しい旗を 1 つだけ渡した回でも、そのファイルは 2 つを一緒に渡した回とバイト一致し、渡していないファイルは作らない
  it(
    "子プロセス(D1b の S-1): --events-rise だけ・--events-maxdrop だけを渡しても、それぞれのファイルは 2 つを一緒に渡した回とバイト一致し、渡していないファイルは作らない",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d1b-diagnose-single-"));
      try {
        const meta = { kind: "meta", kifuId: "d1b-single", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH };
        const records = plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(600) });
        const recordPath = join(dir, "d1b-single.jsonl");
        writeFileSync(recordPath, `${[meta, ...records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
        const out = (name: string) => join(dir, name);
        const run = (args: string[]) => execFileSync("npx", ["tsx", DIAGNOSE_TS, recordPath, ...args], { cwd: REPO_ROOT, encoding: "utf-8" });
        const before = gitStatus();
        run(["--events-rise", out("both-rise.jsonl"), "--events-maxdrop", out("both-maxdrop.jsonl")]);
        run(["--events-rise", out("rise-only.jsonl")]);
        run(["--events-maxdrop", out("maxdrop-only.jsonl")]);
        expect(gitStatus()).toBe(before);
        expect(readdirSync(dir).sort()).toEqual(["both-maxdrop.jsonl", "both-rise.jsonl", "d1b-single.jsonl", "maxdrop-only.jsonl", "rise-only.jsonl"]);
        // 上がり 1 件(20→22)・最大の下がり 1 行(22→24)。空のファイル同士の一致で通らないよう、行の数を先に見る
        expect(readFileSync(out("both-rise.jsonl"), "utf-8").trim().split("\n")).toHaveLength(1);
        expect(readFileSync(out("both-maxdrop.jsonl"), "utf-8").trim().split("\n")).toHaveLength(1);
        expect(readFileSync(out("rise-only.jsonl"))).toEqual(readFileSync(out("both-rise.jsonl")));
        expect(readFileSync(out("maxdrop-only.jsonl"))).toEqual(readFileSync(out("both-maxdrop.jsonl")));
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    120_000,
  );

  // STEP D1b(計画 G-16・S-8)。2 本目の記録の meta が K-3 に当たると、3 つのファイルのどれも書かず、前もって置いたファイルのバイト列が変わらない
  it(
    "子プロセス(D1b の G-16): 2 本目の meta が K-3 に当たると exit 1 で、--events・--events-rise・--events-maxdrop のどれも書き換えない",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d1b-diagnose-k3-"));
      try {
        const good = { kind: "meta", kifuId: "d1b-good", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH };
        const broken = {
          kind: "meta",
          kifuId: "d1b-broken",
          startedAt: "t",
          gitHead: null,
          enginePath: ENGINE_PATH,
          mirrored: true,
          originalUserSide: "gote",
          startSfen: FOLD_START,
          sideAlignmentChecked: true,
          trailingMoveTruncated: false,
        };
        const files: Array<[string, object, unknown[]]> = [
          ["d1b-good", good, plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(600) })],
          ["d1b-broken", broken, plantedRecords(FOLD_MOVES, { 0: engineRef(500), 2: engineRef(-500) }, {}, FOLD_START)],
        ];
        const paths = files.map(([name, meta, records]) => {
          const filePath = join(dir, `${name}.jsonl`);
          writeFileSync(filePath, `${[meta, ...records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
          return filePath;
        });
        const outputs = ["events", "rise", "maxdrop"].map((name) => join(dir, `${name}.jsonl`));
        outputs.forEach((file, index) => writeFileSync(file, `前の回の行 ${index}\n`, "utf-8"));
        const previous = outputs.map((file) => readFileSync(file));
        let failure: { status: number | null; stderr: string } | undefined;
        try {
          execFileSync("npx", ["tsx", DIAGNOSE_TS, ...paths, "--events", outputs[0]!, "--events-rise", outputs[1]!, "--events-maxdrop", outputs[2]!], {
            cwd: REPO_ROOT,
            encoding: "utf-8",
            stdio: "pipe",
          });
        } catch (error) {
          failure = error as { status: number | null; stderr: string };
        }
        expect(failure, "止まらなかった").toBeDefined();
        expect(failure!.status).toBe(1);
        expect(String(failure!.stderr)).toContain("InvalidProvenanceMetaError: 記録 d1b-broken の meta が");
        outputs.forEach((file, index) => expect(readFileSync(file), file).toEqual(previous[index]));
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
          expect(line.schemaVersion).toBe(FAILURE_EVENT_SCHEMA_VERSION);
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
          expect(line.schemaVersion).toBe(FAILURE_EVENT_SCHEMA_VERSION);
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
  // STEP D-SCREEN-2(計画 §3・S-14)。段 2 の記録とその段 1 を一緒に渡したら、表を書かずに名前を並べて止める。段 2 の記録だけなら通り、行に出どころの欄が出る
  it(
    "子プロセス(D-SCREEN-2 の S-14): 段 2 の記録とその段 1 を一緒に渡すと、表も --events も書かずに名前を並べて exit 1。段 2 の記録だけなら exit 0 で、Event の行に evaluationSource・pvSource・出どころの screen がある",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d-screen-2-s14-"));
      try {
        const records = plantedRecords(GAME01_MOVES, { 20: engineRef(0), 22: engineRef(-500) }).map((record) =>
          record.engineReference ? { ...record, engineReference: { ...record.engineReference, nodes: 400_000 } } : record,
        );
        const meta1 = { kind: "meta", kifuId: "d-screen-2", startedAt: "t", gitHead: null, enginePath: ENGINE_PATH, searchMode: "nodes", nodes: 400_000, threads: 1, referenceNodes: 400_000 };
        const stage1 = join(dir, "stage1.jsonl");
        writeFileSync(stage1, `${[meta1, ...records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
        const sha1 = createHash("sha256").update(readFileSync(stage1)).digest("hex");
        const screen = {
          lightNodes: 400_000,
          deepNodes: 4_000_000,
          rule: { dropCp: -300, advantageCp: 300, advantageDropCp: -200, before: 1, after: 2 },
          deepPlies: [],
          sourceSha256: sha1,
          deepRun: { gitHead: null, dirty: null, enginePath: ENGINE_PATH, threads: 1, startedAt: "t2", order: "plyAscending", measuredOrder: [] },
        };
        const stage2 = join(dir, "stage2.jsonl");
        writeFileSync(stage2, `${[{ ...meta1, screen }, ...records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
        const eventsOut = join(dir, "events.jsonl");
        const before = gitStatus();

        let failure: { status: number | null; stdout: string; stderr: string } | undefined;
        try {
          execFileSync("npx", ["tsx", DIAGNOSE_TS, stage1, stage2, "--events", eventsOut], { cwd: REPO_ROOT, encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] });
        } catch (error) {
          failure = error as { status: number | null; stdout: string; stderr: string };
        }
        expect(failure?.status).toBe(1);
        expect(String(failure!.stderr)).toContain(`ScreenInputConflictError: 段 2 の記録 ${stage2} と、その段 1 の記録 ${stage1} を一緒に渡している(screen.sourceSha256 が一致)`);
        expect(String(failure!.stderr)).toContain(`同じ kifuId d-screen-2 に、screen のある記録(${stage2})と無い記録(${stage1})を一緒に渡している`);
        expect(String(failure!.stdout)).toBe("");
        expect(existsSync(eventsOut)).toBe(false);

        const stdout = execFileSync("npx", ["tsx", DIAGNOSE_TS, stage2, "--events", eventsOut], { cwd: REPO_ROOT, encoding: "utf-8" });
        expect(stdout).toContain("## 読み直し(STEP D-SCREEN。meta に screen のある記録だけ)");
        const lines = readFileSync(eventsOut, "utf-8")
          .trim()
          .split("\n")
          .map((line) => JSON.parse(line) as { branchPly: number; branch: { evaluationSource?: string }; counterfactual: { pvSource?: string }; provenance: { record: { meta: { screen?: { sourceSha256: string } } } } });
        expect(lines.map((line) => [line.branchPly, line.branch.evaluationSource, line.counterfactual.pvSource])).toEqual([[21, "light", "light"]]);
        expect(lines[0]!.provenance.record.meta.screen?.sourceSha256).toBe(sha1);
        expect(validateFailureEventLine(lines[0], loadFailureEventSchema())).toEqual([]);
        expect(gitStatus()).toBe(before);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    120_000,
  );
});
