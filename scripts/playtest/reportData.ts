// STEP PIPE 作業 B(docs/STEP_PIPE_PLAN_2026-09-21.md §2.2)。S5「記録 → 本人向けの事実」の道具。
//
// 使い方:
//   npx tsx scripts/playtest/reportData.ts --person <id> --name <表示名> --title <タイトル> --today <YYYY-MM-DD>
//     --records <段 2 の JSONL …> --kifu <固定棋譜 JSON …> --gate <gate.jsonl>
//     --out-patient <patient_report_data.json> --out-audit <audit_metrics.json>
//     [--conditions <dir>] [--king-escapes-condition <id>] [--move-check-condition <id>] [--out-prose-request <prose-request.md>]
//
// - `--conditions` の既定は `scripts/playtest/lib/conditions`。`--king-escapes-condition`/`--move-check-condition` の既定は
//   金の標本(第 6 版)に合わせた `king_escapes_decrease_v1`・`ahead_move_into_own_king_zone_v1`(докs/STEP_D3-COND_PLAN 済みの承認済み定義)
// - 組み立ては純粋関数(lib/reportData.ts)に任せ、ここは読み書きと配線だけ
// - `--out-prose-request` を渡すと、1 局ずつ載せる局の事実の一覧(prose-request.md)も書く(S6 の材料。言い換えそのものはしない)
//
// 【このファイルが絶対にやらないこと】エンジンを回すこと・records/ へ書くこと・judgment を新しく作ること

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { MetaLine, RecordLine } from "./invariants/types.js";
import { loadConditionsFromDir } from "./lib/conditionReport.js";
import { readGitState } from "./lib/gitState.js";
import type { GateLine } from "./lib/gateOutput.js";
import {
  auditSummaryFromTotals,
  buildAuditCandidate,
  buildAuditCandidatePhase,
  buildAuditPairs,
  buildEscapeScenes,
  buildGames,
  buildPatientEvents,
  buildPatientGames,
  buildPatientReportData,
  buildProseRequestMarkdown,
  buildSfens,
  featuredGamesOf,
  gameFactsOf,
  totalDiagnosisCountsOf,
  type GameFacts,
  type GameSource,
} from "./lib/reportData.js";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const DEFAULT_CONDITIONS_DIR = path.join(REPO_ROOT, "scripts", "playtest", "lib", "conditions");
const DEFAULT_KING_ESCAPES_CONDITION = "king_escapes_decrease_v1";
const DEFAULT_MOVE_CHECK_CONDITION = "ahead_move_into_own_king_zone_v1";

const USAGE =
  "使い方: npx tsx scripts/playtest/reportData.ts --person <id> --name <表示名> --title <タイトル> --today <YYYY-MM-DD> --records <段 2 の JSONL …> --kifu <固定棋譜 JSON …> --gate <gate.jsonl> --out-patient <patient_report_data.json> --out-audit <audit_metrics.json> [--conditions <dir>] [--king-escapes-condition <id>] [--move-check-condition <id>] [--out-prose-request <prose-request.md>]";

export class ReportDataCliError extends Error {}

interface CliArgs {
  person: string;
  name: string;
  title: string;
  today: string;
  records: string[];
  kifu: string[];
  gate: string;
  outPatient: string;
  outAudit: string;
  conditionsDir: string;
  kingEscapesConditionId: string;
  moveCheckConditionId: string;
  outProseRequest: string | undefined;
  outSfens: string | undefined;
}

const SINGLE = [
  "--person",
  "--name",
  "--title",
  "--today",
  "--gate",
  "--out-patient",
  "--out-audit",
  "--conditions",
  "--king-escapes-condition",
  "--move-check-condition",
  "--out-prose-request",
  "--out-sfens",
] as const;
const MULTI = ["--records", "--kifu"] as const;

export function parseArgs(argv: readonly string[]): CliArgs {
  const single = new Map<string, string>();
  const multi = new Map<string, string[]>(MULTI.map((flag) => [flag, []]));
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index]!;
    if ((SINGLE as readonly string[]).includes(flag)) {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new ReportDataCliError(`${flag} に値が無い`);
      if (single.has(flag)) throw new ReportDataCliError(`${flag} が 2 回ある`);
      single.set(flag, value);
      index += 1;
    } else if ((MULTI as readonly string[]).includes(flag)) {
      while (argv[index + 1] !== undefined && !argv[index + 1]!.startsWith("--")) {
        multi.get(flag)!.push(argv[index + 1]!);
        index += 1;
      }
    } else {
      throw new ReportDataCliError(`知らない引数: ${flag}`);
    }
  }
  const required = ["--person", "--name", "--title", "--today", "--gate", "--out-patient", "--out-audit"] as const;
  const missing = required.filter((flag) => !single.has(flag));
  if (missing.length > 0) throw new ReportDataCliError(`${missing.join("・")} が無い。${USAGE}`);
  if (multi.get("--records")!.length === 0) throw new ReportDataCliError(`--records が無い。${USAGE}`);
  if (multi.get("--kifu")!.length === 0) throw new ReportDataCliError(`--kifu が無い。${USAGE}`);
  return {
    person: single.get("--person")!,
    name: single.get("--name")!,
    title: single.get("--title")!,
    today: single.get("--today")!,
    records: multi.get("--records")!,
    kifu: multi.get("--kifu")!,
    gate: single.get("--gate")!,
    outPatient: single.get("--out-patient")!,
    outAudit: single.get("--out-audit")!,
    conditionsDir: single.get("--conditions") ?? DEFAULT_CONDITIONS_DIR,
    kingEscapesConditionId: single.get("--king-escapes-condition") ?? DEFAULT_KING_ESCAPES_CONDITION,
    moveCheckConditionId: single.get("--move-check-condition") ?? DEFAULT_MOVE_CHECK_CONDITION,
    outProseRequest: single.get("--out-prose-request"),
    outSfens: single.get("--out-sfens"),
  };
}

function readJsonlLines(filePath: string): Array<Record<string, unknown>> {
  return readFileSync(filePath, "utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
}

function readGameSource(recordsPath: string, kifuFiles: readonly string[]): GameSource {
  const lines = readJsonlLines(recordsPath);
  const meta = lines.find((line) => line["kind"] === "meta") as unknown as MetaLine | undefined;
  if (meta === undefined) throw new ReportDataCliError(`${recordsPath} に meta 行が無い`);
  const records = lines.filter((line) => line["kind"] === "record") as unknown as RecordLine[];
  const kifuPath = kifuFiles.find((file) => path.basename(file) === `${meta.kifuId}.fixed.json` || path.basename(file, ".fixed.json") === meta.kifuId);
  if (kifuPath === undefined) throw new ReportDataCliError(`${meta.kifuId} の固定棋譜(--kifu)が見つからない`);
  const fixed = JSON.parse(readFileSync(kifuPath, "utf-8")) as GameSource["fixed"];
  return { kifuId: meta.kifuId, meta, records, fixed };
}

function readGateLines(gatePath: string): GateLine[] {
  return readJsonlLines(gatePath) as unknown as GateLine[];
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const sources = args.records.map((recordsPath) => readGameSource(recordsPath, args.kifu));
  const gateLines = readGateLines(args.gate);
  const conditions = await loadConditionsFromDir(args.conditionsDir);
  const kingEscapes = conditions.find((loaded) => loaded.definition.id === args.kingEscapesConditionId);
  if (kingEscapes === undefined) throw new ReportDataCliError(`${args.conditionsDir} に条件式 ${args.kingEscapesConditionId} が無い`);

  const patient = buildPatientReportData(sources, gateLines, kingEscapes.definition, {
    title: args.title,
    person: args.name,
    today: args.today,
    kingEscapesConditionId: args.kingEscapesConditionId,
    moveCheckConditionId: args.moveCheckConditionId,
  });

  writeFileSync(path.resolve(args.outPatient), `${JSON.stringify(patient, null, 2)}\n`, "utf-8");

  // ---- audit_metrics.json(技術資料の側。best effort。別冊の道具 _app.py・_tail.py が読む欄を満たす) ----
  const builtGames = buildGames(sources);
  const patientGamesForAudit = buildPatientGames(builtGames);
  const eventsForAudit = buildPatientEvents(builtGames);
  const escapeScenesForAudit = buildEscapeScenes(builtGames, kingEscapes.definition);
  const totals = totalDiagnosisCountsOf(builtGames);
  const analysisGit = readGitState(REPO_ROOT);
  const pairs = buildAuditPairs(builtGames, analysisGit.gitHead, conditions.length);
  const auditCandidatePhase = buildAuditCandidatePhase(patient.overview, eventsForAudit, patientGamesForAudit);
  const moveCheckGateLine = gateLines.find((line) => line.condition.id === args.kingEscapesConditionId);
  const candidate =
    moveCheckGateLine === undefined ? null : buildAuditCandidate(moveCheckGateLine, kingEscapes.definition, kingEscapes.definitionSha256, escapeScenesForAudit, auditCandidatePhase);

  const audit = {
    title: args.title,
    person: args.name,
    today: args.today,
    summary: auditSummaryFromTotals(totals, patientGamesForAudit.length, eventsForAudit),
    games: patientGamesForAudit,
    events: eventsForAudit,
    pairs,
    candidate,
  };
  writeFileSync(path.resolve(args.outAudit), `${JSON.stringify(audit, null, 2)}\n`, "utf-8");

  if (args.outSfens !== undefined) {
    const sfens = buildSfens(builtGames);
    writeFileSync(path.resolve(args.outSfens), JSON.stringify(sfens), "utf-8");
  }

  if (args.outProseRequest !== undefined) {
    const factsByNo = new Map<number, GameFacts>(patient.games.map((game) => [game.no, gameFactsOf(game)]));
    const featured = featuredGamesOf(patient.games, factsByNo);
    const markdown = buildProseRequestMarkdown(patient, featured, factsByNo);
    writeFileSync(path.resolve(args.outProseRequest), markdown, "utf-8");
  }

  console.log(`patient: ${patient.games.length} 局・events ${patient.events.length} 件・escapeScenes ${patient.escapeScenes.length} 件`);
  process.exitCode = 0;
}

main().catch((error: unknown) => {
  if (error instanceof Error) {
    console.error(`${error.name}: ${error.message}`);
  } else {
    console.error(String(error));
  }
  process.exitCode = 1;
});
