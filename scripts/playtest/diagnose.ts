// STEP D1(docs/STEP_D1_PLAN_2026-09-14.md 3.2)。replay.ts の JSONL を読み、Failure Event を
// Markdown の表で標準出力へ書く。**エンジンは回さない**(check.ts と同じ形)。
//
// 使い方: npx tsx scripts/playtest/diagnose.ts <a.jsonl> [<b.jsonl> ...] [--events <out.jsonl>] [--events-rise <out.jsonl>] [--events-maxdrop <out.jsonl>] [--evaluator "<評価関数の識別>"] [--conditions <dir> --person <p1> [--events-cond <out.jsonl>] [--cond-summary <out.json>] [--kifu-dir <dir>] [--listed-results <file.json>]]
//
// 【このファイルは薄くしてある】判定・集計・表の組み立てはすべて lib/failureEvent.ts(合計は lib/diagnosisTotals.ts)にあり、そちらに試験がある。
// ここでやるのは、記録を読む・lib を呼ぶ・書き出す、だけである。
// `--events` の 1 行は lib/failureEventSchema.ts の toEventLine で、版の欄 schemaVersion を先頭に付けて書く
// (STEP JSON v0.2・V0.3-META・STEP D2 の v0.4・STEP D2.5 の v0.5。スキーマは scripts/playtest/schemas/failure-event.v0.5.schema.json)。行の末尾に出どころ(provenance)を付ける:
// 記録のファイル(根からの相対)と sha256・記録の meta の写し・`--evaluator` の文(**確かめていない自己申告**。渡されなければ null。
// enginePath から推測しない ― P-43)・このコマンドを回したときの gitHead と汚れ・規則の値(docs/STEP_JSON-V0.2_PLAN_2026-09-15.md 2.1)。
//
// `--events-rise`・`--events-maxdrop`(STEP D1b。docs/STEP_D1b_PLAN_2026-09-15.md)は、上がりの組と局ごとの最大の下がりを、別の契約 diagnosis-moment v0.2
// (scripts/playtest/schemas/diagnosis-moment.v0.2.schema.json)の行で書く。組み立ては lib/diagnosisMoment.ts。**`--events` の行と表は変えない**。
// **3 つのファイルは、すべての行を作ってから書く**(出どころの例外で一部のファイルだけが書かれる形を避ける ― 計画 S-8)。
//
// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §3・§11)。meta に screen のある段 2 の記録(rescreen.ts)は、組ごとに深い値か軽い値かを選ぶ
// (判断は lib/screenDiagnosis.ts)。**段 2 の記録とその段 1 を一緒に渡したら、表を書く前に名前を並べて exit 1**(二重に数えない ― S-14)。
// screen の無い記録の表と行は変えない(--events の版の欄のほか)。
//
// STEP D3-COND(docs/STEP_D3-COND_PLAN_2026-09-15.md §3・§6)。`--conditions <dir>`(条件式の定義。1 件 1 ファイル)と `--person <p1 の形の記号>` を渡すと、
// Failure Event・上がり・最大の下がりの組に条件式を当て、表の後に条件式の節を足す。`--events-cond` は 1 行 =(入力 1 件 × 定義 1 件)の判定を契約 diagnosis-condition v0.1
// (scripts/playtest/schemas/diagnosis-condition.v0.1.schema.json)で、`--cond-summary` は 1 人ぶんの集計を契約 diagnosis-condition-summary で書く。§7.2 の「落としたか」の材料は
// `--kifu-dir <固定棋譜 JSON のディレクトリ>`(id で ending を引く)と `--listed-results <kifuId → win・loss の JSON>` から読む(渡さなければ「記録に無い」「載っていない」)。
// 判定と集計は lib/condition.ts、行・節・読み込みは lib/conditionReport.ts。**--conditions を渡さなければ、表と 3 つのファイルは変えない。**
// 定義は動的 import で読むので main は非同期(末尾で main() の Promise の失敗を捕まえる)。
//
// 【exit code】lib の例外は外へ出さず「数えられなかった」行にして exit 0。**入力が読めないとき(ENOENT・壊れた JSONL)・引数が誤りのときは exit 1**
// (計画 D-1 の読み替え ― 2026-09-15、監査 B の非必須 d)。**記録の meta が出どころに写せる形でない(STEP JSON V0.3-META 計画 K-3)ときも、--events を書かずに exit 1**
// (表は標準出力に書き終えてから止まる。前の回に同じパスへ書いた --events のファイルは消さない ― 計画 L-4)。
// **終わるときに process.exit を呼ばず、例外も外へ投げない**(STEP D2 の監査 1e の R-1・任意 N-1、司令塔の決定 (b))。標準出力がパイプだと書き込みは非同期で、
// exit も捕まえない例外もその完了を待たずにプロセスを止めるので、64KB を超える表が、exit 0 のまま黙って(例外なら 0 でない終了のまま)切れる。
// 例外はファイルの末尾の main の呼び出しで捕まえて、名前と文を標準エラーに書き、終了コードは process.exitCode に置いて、書き終わるのを待って自然に終わる。
//
// 【このファイルが絶対にやらないこと】
// - 死因のタグを approved にすること・閾値を確定すること
// - **この件数を診断に使うこと**(評価関数の種類は記録に残っていない。今の記録は入力の行の enginePath で見分けられる ― P-43。計画 0.)

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { MetaLine, RecordLine } from "./invariants/types.js";
import { conditionTallyOf, type ConditionGameInput } from "./lib/condition.js";
import {
  assertPersonLabel,
  conditionGameOf,
  conditionInputsOf,
  conditionLinesOf,
  conditionSummaryOf,
  loadConditionsFromDir,
  readKifuEndings,
  readListedResults,
  renderConditionSection,
} from "./lib/conditionReport.js";
import { POSITION_FACTS_RULES } from "./lib/counterfactual.js";
import { diagnosisMomentsOf, toMomentLine } from "./lib/diagnosisMoment.js";
import { renderDiagnosisTotals } from "./lib/diagnosisTotals.js";
import { buildDiagnosisReport, DRAFT_RULE_1, NOT_EVALUATION_CP, renderDiagnosisReport, STANDING_BOUNDS, type DiagnosisInput } from "./lib/failureEvent.js";
import { buildProvenance, pathForProvenance, recordSha256, toEventLine } from "./lib/failureEventSchema.js";
import { readGitState } from "./lib/gitState.js";
import { screenInputConflicts, ScreenInputConflictError, screenOfRecord } from "./lib/screenDiagnosis.js";
import { initialSfenOf } from "./lib/sideAlignment.js";

/** このファイルがあるリポジトリ(作業ツリー)の根。出どころのパスはここからの相対にする */
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

interface ConditionArgs {
  conditionsDir: string | undefined;
  person: string | undefined;
  eventsCondOut: string | undefined;
  condSummaryOut: string | undefined;
  kifuDir: string | undefined;
  listedResultsPath: string | undefined;
}

function parseArgs(argv: string[]): { files: string[]; eventsOut: string | undefined; eventsRiseOut: string | undefined; eventsMaxDropOut: string | undefined; evaluator: string | null } & ConditionArgs {
  const taken = new Set<number>();
  const valueOf = (flag: string): string | undefined => {
    const index = argv.indexOf(flag);
    if (index === -1) return undefined;
    taken.add(index);
    taken.add(index + 1);
    return argv[index + 1];
  };
  const eventsOut = valueOf("--events");
  const eventsRiseOut = valueOf("--events-rise");
  const eventsMaxDropOut = valueOf("--events-maxdrop");
  const evaluator = valueOf("--evaluator");
  // 自己申告の文を空で埋めない(「無い」は null = --evaluator を渡さないこと。渡したのに値が無い・空・次の旗なら誤りとして止める)
  if (argv.includes("--evaluator") && (evaluator === undefined || evaluator.trim().length === 0 || evaluator.startsWith("--"))) throw new Error("--evaluator に評価関数の識別の文を渡してください(空は受け付けない)");
  // STEP D3-COND: 条件式の旗は値を必ず取り、組で使う(黙って無視しない)。--person は名前でない記号だけ
  const conditionFlag = (flag: string): string | undefined => {
    const value = valueOf(flag);
    if (argv.includes(flag) && (value === undefined || value.trim().length === 0 || value.startsWith("--"))) throw new Error(`${flag} に値を渡してください`);
    return value;
  };
  const conditionsDir = conditionFlag("--conditions");
  const person = conditionFlag("--person");
  const eventsCondOut = conditionFlag("--events-cond");
  const condSummaryOut = conditionFlag("--cond-summary");
  const kifuDir = conditionFlag("--kifu-dir");
  const listedResultsPath = conditionFlag("--listed-results");
  if (conditionsDir === undefined && [person, eventsCondOut, condSummaryOut, kifuDir, listedResultsPath].some((value) => value !== undefined)) {
    throw new Error("--person・--events-cond・--cond-summary・--kifu-dir・--listed-results は --conditions と一緒に渡してください");
  }
  if (conditionsDir !== undefined && person === undefined) throw new Error("--conditions には --person(名前でない記号)が要ります");
  if (person !== undefined) assertPersonLabel(person);
  const files = argv.filter((arg, index) => !taken.has(index) && arg.length > 0);
  return { files, eventsOut, eventsRiseOut, eventsMaxDropOut, evaluator: evaluator ?? null, conditionsDir, person, eventsCondOut, condSummaryOut, kifuDir, listedResultsPath };
}

interface InputEntry {
  input: DiagnosisInput;
  filePath: string;
  sha256: string;
}

function readInput(filePath: string): InputEntry {
  const bytes = readFileSync(path.resolve(filePath));
  const lines = bytes
    .toString("utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as { kind: string });
  const meta = lines.find((line) => line.kind === "meta") as MetaLine | undefined;
  const records = lines.filter((line): line is RecordLine => line.kind === "record");
  // STEP D0-SIDE 段 1(R-9): error 行(replay.ts が途中で止まった印)を集めて渡す。1 つでもあれば lib がその記録を数えない。
  const errorLines = lines.filter((line) => line.kind === "error").map((line) => ({ reason: String((line as { reason?: unknown }).reason) }));
  return { input: { kifuId: meta?.kifuId ?? path.basename(filePath), meta, records, errorLines }, filePath, sha256: recordSha256(bytes) };
}

async function main(): Promise<void> {
  const { files, eventsOut, eventsRiseOut, eventsMaxDropOut, evaluator, conditionsDir, person, eventsCondOut, condSummaryOut, kifuDir, listedResultsPath } = parseArgs(process.argv.slice(2));
  if (files.length === 0) {
    console.error("使い方: npx tsx scripts/playtest/diagnose.ts <a.jsonl> [<b.jsonl> ...] [--events <out.jsonl>] [--events-rise <out.jsonl>] [--events-maxdrop <out.jsonl>] [--evaluator \"<評価関数の識別>\"] [--conditions <dir> --person <p1> [--events-cond <out.jsonl>] [--cond-summary <out.json>] [--kifu-dir <dir>] [--listed-results <file.json>]]");
    process.exitCode = 0;
    return;
  }

  const entries = files.map(readInput);
  // STEP D-SCREEN-2(計画 §3・S-14): 段 2 の記録とその段 1 を一緒に渡したら、表を書く前に止める
  const conflicts = screenInputConflicts(entries.map((entry) => ({ name: entry.filePath, kifuId: entry.input.kifuId, sha256: entry.sha256, meta: entry.input.meta })));
  if (conflicts.length > 0) throw new ScreenInputConflictError(conflicts.join(" / "));
  // STEP D3-COND: 定義と §7.2 の材料は、表を書く前に読む(読めなければ表を書かずに止める)
  const conditions = conditionsDir === undefined ? undefined : await loadConditionsFromDir(conditionsDir);
  const endings = kifuDir === undefined ? undefined : readKifuEndings(kifuDir);
  const listedResults = listedResultsPath === undefined ? undefined : readListedResults(listedResultsPath);
  const inputs = entries.map((entry) => entry.input);
  const report = buildDiagnosisReport(inputs, DRAFT_RULE_1);
  // STEP D3(計画 Q-5): 入力が 2 本以上なら、入力ごとの表の後に群の合計の節を足す(1 本なら何も足さない)。
  console.log([...renderDiagnosisReport(report), ...renderDiagnosisTotals(report)].join("\n"));

  if (eventsOut || eventsRiseOut || eventsMaxDropOut || conditions) {
    const analysisGit = readGitState(REPO_ROOT);
    const riseLines: string[] = [];
    const maxDropLines: string[] = [];
    // STEP D3-COND: 条件式の行と、1 人ぶんの集計の入力
    const conditionLines: string[] = [];
    const conditionGames: ConditionGameInput[] = [];
    // buildDiagnosisReport は入力 1 本につき 1 行を同じ順で返す(lib/failureEvent.ts)
    const eventLines = report.flatMap((row, index) => {
      if (row.result.kind !== "counted") return [];
      const entry = entries[index]!;
      const provenance = buildProvenance({
        recordPath: entry.filePath,
        recordSha256: entry.sha256,
        meta: entry.input.meta,
        evaluator,
        analysisGit,
        rule: DRAFT_RULE_1, notEvaluationCp: NOT_EVALUATION_CP, standingBounds: STANDING_BOUNDS, positionFactsRules: POSITION_FACTS_RULES, repoRoot: REPO_ROOT,
      });
      // STEP D1b: 上がりと最大の下がり(同じ記録・同じ規則・同じ開始局面・同じ出どころ)。頼まれたときだけ組み立てる
      if (eventsRiseOut || eventsMaxDropOut || conditions) {
        // STEP D-SCREEN-2: 段 2 の記録は Failure Event と同じ screen を渡す(数えた記録なので不変条件は確かめ済み)
        const screen = screenOfRecord(entry.input.kifuId, entry.input.meta, entry.input.records);
        const moments = diagnosisMomentsOf(entry.input.kifuId, entry.input.records, DRAFT_RULE_1, initialSfenOf(entry.input.meta), row.result.events, screen);
        riseLines.push(...moments.rises.map((moment) => JSON.stringify(toMomentLine(moment, provenance))));
        maxDropLines.push(JSON.stringify(toMomentLine(moments.maxDrop, provenance)));
        // STEP D3-COND: 同じ Failure Event と moment の行に条件式を当てる(判定しない行は書かない)
        if (conditions) {
          conditionLines.push(...conditionLinesOf(conditionInputsOf(row.result.events, moments), conditions, provenance).map((line) => JSON.stringify(line)));
          conditionGames.push(conditionGameOf({ kifuId: entry.input.kifuId, meta: entry.input.meta, events: row.result.events, moments, endings, listedResults }));
        }
      }
      return row.result.events.map((event) => JSON.stringify(toEventLine(event, provenance)));
    });
    // STEP D3-COND: 1 人ぶんの集計(同じ kifuId が 2 本なら止める)。節は表の後に書き、2 つのファイルもほかのファイルと一緒に全部を作ってから書く
    let conditionSummary: string | undefined;
    if (conditions && person !== undefined) {
      const tallies = conditions.map((loaded) => conditionTallyOf(person, conditionGames, loaded));
      const sources = { kifuDir: kifuDir === undefined ? null : pathForProvenance(kifuDir, REPO_ROOT), listedResults: listedResultsPath === undefined ? null : pathForProvenance(listedResultsPath, REPO_ROOT) };
      const summaryInputs = entries.map((entry, index) => ({ path: pathForProvenance(entry.filePath, REPO_ROOT), sha256: entry.sha256, kifuId: entry.input.kifuId, counted: report[index]!.result.kind === "counted" }));
      conditionSummary = `${JSON.stringify(conditionSummaryOf({ person, inputs: summaryInputs, sources, analysisGit, tallies }), null, 2)}\n`;
      console.log(renderConditionSection(person, tallies, sources).join("\n"));
    }
    // STEP D1b(計画 S-8): 3 つのファイルは、すべての行を作ってから書く
    const jsonl = (lines: string[]): string => (lines.length > 0 ? `${lines.join("\n")}\n` : "");
    if (eventsOut) writeFileSync(path.resolve(eventsOut), jsonl(eventLines), "utf-8");
    if (eventsRiseOut) writeFileSync(path.resolve(eventsRiseOut), jsonl(riseLines), "utf-8");
    if (eventsMaxDropOut) writeFileSync(path.resolve(eventsMaxDropOut), jsonl(maxDropLines), "utf-8");
    if (eventsCondOut) writeFileSync(path.resolve(eventsCondOut), jsonl(conditionLines), "utf-8");
    if (condSummaryOut && conditionSummary !== undefined) writeFileSync(path.resolve(condSummaryOut), conditionSummary, "utf-8");
  }

  process.exitCode = 0;
}

main().catch((error: unknown) => {
  // 名前と文を先に 1 行で書く(試験は `<名前>: <文>` で止めた理由を見る)。続けてスタックの残りを書く
  if (error instanceof Error) {
    console.error(`${error.name}: ${error.message}`);
    const frames = (error.stack ?? "").split("\n").slice(1).join("\n");
    if (frames.length > 0) console.error(frames);
  } else {
    console.error(String(error));
  }
  process.exitCode = 1;
});
