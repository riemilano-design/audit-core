// STEP D1(docs/STEP_D1_PLAN_2026-09-14.md 3.2)。replay.ts の JSONL を読み、Failure Event を
// Markdown の表で標準出力へ書く。**エンジンは回さない**(check.ts と同じ形)。
//
// 使い方: npx tsx scripts/playtest/diagnose.ts <a.jsonl> [<b.jsonl> ...] [--events <out.jsonl>] [--events-rise <out.jsonl>] [--events-maxdrop <out.jsonl>] [--evaluator "<評価関数の識別>"]
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
import { POSITION_FACTS_RULES } from "./lib/counterfactual.js";
import { diagnosisMomentsOf, toMomentLine } from "./lib/diagnosisMoment.js";
import { renderDiagnosisTotals } from "./lib/diagnosisTotals.js";
import { buildDiagnosisReport, DRAFT_RULE_1, NOT_EVALUATION_CP, renderDiagnosisReport, STANDING_BOUNDS, type DiagnosisInput } from "./lib/failureEvent.js";
import { buildProvenance, recordSha256, toEventLine } from "./lib/failureEventSchema.js";
import { readGitState } from "./lib/gitState.js";
import { screenInputConflicts, ScreenInputConflictError, screenOfRecord } from "./lib/screenDiagnosis.js";
import { initialSfenOf } from "./lib/sideAlignment.js";

/** このファイルがあるリポジトリ(作業ツリー)の根。出どころのパスはここからの相対にする */
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

function parseArgs(argv: string[]): { files: string[]; eventsOut: string | undefined; eventsRiseOut: string | undefined; eventsMaxDropOut: string | undefined; evaluator: string | null } {
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
  const files = argv.filter((arg, index) => !taken.has(index) && arg.length > 0);
  return { files, eventsOut, eventsRiseOut, eventsMaxDropOut, evaluator: evaluator ?? null };
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

function main(): void {
  const { files, eventsOut, eventsRiseOut, eventsMaxDropOut, evaluator } = parseArgs(process.argv.slice(2));
  if (files.length === 0) {
    console.error("使い方: npx tsx scripts/playtest/diagnose.ts <a.jsonl> [<b.jsonl> ...] [--events <out.jsonl>] [--events-rise <out.jsonl>] [--events-maxdrop <out.jsonl>] [--evaluator \"<評価関数の識別>\"]");
    process.exitCode = 0;
    return;
  }

  const entries = files.map(readInput);
  // STEP D-SCREEN-2(計画 §3・S-14): 段 2 の記録とその段 1 を一緒に渡したら、表を書く前に止める
  const conflicts = screenInputConflicts(entries.map((entry) => ({ name: entry.filePath, kifuId: entry.input.kifuId, sha256: entry.sha256, meta: entry.input.meta })));
  if (conflicts.length > 0) throw new ScreenInputConflictError(conflicts.join(" / "));
  const inputs = entries.map((entry) => entry.input);
  const report = buildDiagnosisReport(inputs, DRAFT_RULE_1);
  // STEP D3(計画 Q-5): 入力が 2 本以上なら、入力ごとの表の後に群の合計の節を足す(1 本なら何も足さない)。
  console.log([...renderDiagnosisReport(report), ...renderDiagnosisTotals(report)].join("\n"));

  if (eventsOut || eventsRiseOut || eventsMaxDropOut) {
    const analysisGit = readGitState(REPO_ROOT);
    const riseLines: string[] = [];
    const maxDropLines: string[] = [];
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
      if (eventsRiseOut || eventsMaxDropOut) {
        // STEP D-SCREEN-2: 段 2 の記録は Failure Event と同じ screen を渡す(数えた記録なので不変条件は確かめ済み)
        const screen = screenOfRecord(entry.input.kifuId, entry.input.meta, entry.input.records);
        const moments = diagnosisMomentsOf(entry.input.kifuId, entry.input.records, DRAFT_RULE_1, initialSfenOf(entry.input.meta), row.result.events, screen);
        riseLines.push(...moments.rises.map((moment) => JSON.stringify(toMomentLine(moment, provenance))));
        maxDropLines.push(JSON.stringify(toMomentLine(moments.maxDrop, provenance)));
      }
      return row.result.events.map((event) => JSON.stringify(toEventLine(event, provenance)));
    });
    // STEP D1b(計画 S-8): 3 つのファイルは、すべての行を作ってから書く
    const jsonl = (lines: string[]): string => (lines.length > 0 ? `${lines.join("\n")}\n` : "");
    if (eventsOut) writeFileSync(path.resolve(eventsOut), jsonl(eventLines), "utf-8");
    if (eventsRiseOut) writeFileSync(path.resolve(eventsRiseOut), jsonl(riseLines), "utf-8");
    if (eventsMaxDropOut) writeFileSync(path.resolve(eventsMaxDropOut), jsonl(maxDropLines), "utf-8");
  }

  process.exitCode = 0;
}

try {
  main();
} catch (error) {
  // 名前と文を先に 1 行で書く(試験は `<名前>: <文>` で止めた理由を見る)。続けてスタックの残りを書く
  if (error instanceof Error) {
    console.error(`${error.name}: ${error.message}`);
    const frames = (error.stack ?? "").split("\n").slice(1).join("\n");
    if (frames.length > 0) console.error(frames);
  } else {
    console.error(String(error));
  }
  process.exitCode = 1;
}
