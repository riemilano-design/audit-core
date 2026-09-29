// Observation Packet を組む道具(束 C。計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §8)。
//
// 【顧客の PDF にどう出るか】今は何も変わらない。冊子は今のままの数で出る。
//   この道具が足すのは、**その数がどの材料のどの行から出たかを機械で辿れる 1 つのファイル**である。
// 【この道具は判定をしない】読む・数える・突き合わせる・書く。**数を手で書き写す場所が 1 つも無い。**
// 【使い方】
//   npx tsx scripts/playtest/observationPacket.ts --customer-ref c5 \
//     --patient <patient_report_data.json> --sfens <sfens.json> --time-cause <time_cause.json> \
//     --direct <direct_answers.json> --recognition <opening_recognition.json> \
//     --read <read のフォルダ> --whatif <whatif-v2 のフォルダ> --definitions <定義のフォルダ,…> \
//     [--out <書き出す packet.json>] [--request <request.json>] [--compare <exit_candidates.json>]
//   組まずに**既に在る packet を検証する**とき(材料を持たない側と同じ立場):
//     npx tsx scripts/playtest/observationPacket.ts --verify <packet.json>
// 【出口】問題が 1 件でもあれば終了コード 1(数が合わない・辿れない・材料が差し替わった、を黙って通さない)。
import { execFileSync, spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { readFileSync } from "node:fs";
import path from "node:path";
import {
  aggregateCoverageProblems, aggregatesOf, bookletAgreementProblems, recountProblems, type AggregateRow, type BookletNumbers, type BookletPythonNumbers,
} from "./lib/observationAggregates.js";
import { factsOf, factsProblems } from "./lib/observationFacts.js";
import { DEFAULT_SOURCES, readFactsMaterials, type MaterialPaths } from "./lib/observationMaterials.js";
import {
  OBSERVATION_PACKET_CONTRACT, OBSERVATION_PACKET_SCHEMA_VERSION, observationPacketProblems,
  packetIdOf, requestAgreementProblems, validateObservationRequest,
} from "./lib/observationPacket.js";
import { provenanceOf, traceProblems } from "./lib/observationProvenance.js";

const REPO_ROOT = path.resolve(new URL("../..", import.meta.url).pathname);

function argOf(name: string): string | undefined {
  const index = process.argv.indexOf(`--${name}`);
  if (index < 0) return undefined;
  return process.argv[index + 1];
}

function requiredArg(name: string): string {
  const value = argOf(name);
  if (value === undefined || value.startsWith("--")) throw new Error(`--${name} が要る`);
  return value;
}

function gitHead(): string {
  return execFileSync("git", ["rev-parse", "HEAD"], { cwd: REPO_ROOT, encoding: "utf-8" }).trim();
}

/**
 * **冊子の道具(python)に数えさせる**(束 D)。`check_answer.side_match_of`・`long_think_fork_of` の値を取る。
 * 冊子の JSON に残っていない 2 つの数(側が逆の分子・長考のうち側が逆)の突き合わせ相手になる。
 * **静かにあきらめない** ― 呼べなければ理由を問題として返す(照合の相手が消えるのを黙って通さない)。
 */
function pythonNumbersOf(paths: MaterialPaths, timeCause: unknown, problems: string[]): BookletPythonNumbers | undefined {
  const games = ((timeCause as { games?: { group?: unknown }[] }).games ?? []);
  const groups = [...new Set(games.map((game) => String(game.group)))];
  if (groups.length !== 1) {
    problems.push(`python の照合: time_cause の組が ${groups.length} 通り(${groups.join(" / ")}) ― どの組で数えるか決められない`);
    return undefined;
  }
  const script = path.join(REPO_ROOT, "scripts/playtest/report-pdf/dump_booklet_numbers.py");
  const result = spawnSync("python3", [
    "-X", "utf8", script,
    "--time-cause", path.resolve(paths.timeCause),
    "--group", groups[0]!,
    "--whatif", ...paths.whatifDirs.map((dir) => path.resolve(dir)),
  ], { encoding: "utf-8" });
  if (result.status !== 0) {
    problems.push(`python の照合: dump_booklet_numbers.py が落ちた(status=${String(result.status)} ${result.stderr?.trim() ?? ""})`);
    return undefined;
  }
  return JSON.parse(result.stdout) as BookletPythonNumbers;
}

function bookletOf(comparePath: string, patient: unknown, direct: unknown, python: BookletPythonNumbers | undefined): BookletNumbers {
  const exit = JSON.parse(readFileSync(comparePath, "utf-8")) as {
    actionFractions?: BookletNumbers["actionFractions"];
    denominators?: BookletNumbers["denominators"];
    repro?: { rows?: BookletNumbers["repro"] };
    openingGroups?: BookletNumbers["openingGroups"];
  };
  return {
    actionFractions: exit.actionFractions,
    denominators: exit.denominators,
    repro: exit.repro?.rows,
    openingGroups: exit.openingGroups,
    findings: (patient as { findings?: BookletNumbers["findings"] }).findings,
    directCounts: (direct as { counts?: Record<string, number> }).counts,
    python,
  };
}

function numbersOf(row: AggregateRow): string {
  if (typeof row.value === "number") return String(row.value);
  return `${String(row.numerator)} / ${String(row.denominator)}`;
}

/**
 * **既に在る packet を検証する**(束 D)。材料を読まない ― 受け取る側(3 席・検証器・組版)と同じ立場で、
 * 契約・集計の筋・行の揃い・**数え直し**・追跡性を見る。材料の指紋の照合だけはファイルを読む。
 */
function verify(packetPath: string): void {
  const packet = JSON.parse(readFileSync(packetPath, "utf-8")) as { facts?: Record<string, unknown>; aggregates?: Record<string, unknown>[]; packetId?: unknown; provenance?: { sources?: Record<string, unknown>[]; inputs?: { path: string; sha256: string; bytes: number }[] } };
  const problems = [
    ...observationPacketProblems(packet),
    ...aggregateCoverageProblems((packet.aggregates ?? []) as AggregateRow[]),
    ...recountProblems(packet),
    ...traceProblems(packet, { repoRoot: REPO_ROOT }),
  ];
  console.log(`検証: ${packetPath}(packetId ${String(packet.packetId)})`);
  if (problems.length > 0) {
    console.log(`問題 ${problems.length} 件:`);
    for (const line of problems) console.log(`  - ${line}`);
    process.exitCode = 1;
    return;
  }
  console.log("問題なし(契約・集計の筋・行の揃い・数え直し・追跡性)");
}

function main(): void {
  const verifyPath = argOf("verify");
  if (verifyPath !== undefined) {
    verify(verifyPath);
    return;
  }
  const customerRef = requiredArg("customer-ref");
  const paths: MaterialPaths = {
    patient: requiredArg("patient"),
    sfens: requiredArg("sfens"),
    timeCause: requiredArg("time-cause"),
    direct: requiredArg("direct"),
    recognition: requiredArg("recognition"),
    readDirs: requiredArg("read").split(","),
    whatifDirs: requiredArg("whatif").split(","),
    definitionDirs: requiredArg("definitions").split(","),
  };
  const { materials, inputs, inputsBySource, meta } = readFactsMaterials(paths, REPO_ROOT);
  const facts = factsOf(materials);
  const problems = factsProblems(facts, materials);
  const aggregates = aggregatesOf(facts, materials);
  const provenance = provenanceOf({
    pipelineVersion: gitHead(),
    generatedAt: new Date().toISOString(),
    inputs,
    inputsBySource,
    meta,
    sources: DEFAULT_SOURCES,
    recognitionReviewStatus: "draft",
  });
  const packet = {
    contract: OBSERVATION_PACKET_CONTRACT,
    schemaVersion: OBSERVATION_PACKET_SCHEMA_VERSION,
    packetId: packetIdOf(facts, aggregates),
    customerRef,
    facts,
    aggregates,
    provenance,
  };
  problems.push(...aggregateCoverageProblems(aggregates));
  problems.push(...observationPacketProblems(packet));
  problems.push(...recountProblems(packet));
  problems.push(...traceProblems(packet, { repoRoot: REPO_ROOT }));

  const requestPath = argOf("request");
  if (requestPath !== undefined) {
    const request = JSON.parse(readFileSync(requestPath, "utf-8")) as unknown;
    problems.push(...validateObservationRequest(request).map((line) => `request: ${line}`));
    problems.push(...requestAgreementProblems(packet, request));
  }
  const comparePath = argOf("compare");
  if (comparePath !== undefined) {
    const python = pythonNumbersOf(paths, materials.timeCause, problems);
    const direct = { counts: (JSON.parse(readFileSync(paths.direct, "utf-8")) as { counts?: unknown }).counts };
    problems.push(...bookletAgreementProblems(aggregates, bookletOf(comparePath, materials.patient, direct, python)));
  }

  const counts = Object.entries(facts).map(([key, value]) => {
    if (Array.isArray(value)) return `${key} ${value.length}`;
    const recognition = value as { rows?: unknown[]; definitions?: unknown[] };
    return `${key} rows ${recognition.rows?.length ?? 0} / definitions ${recognition.definitions?.length ?? 0}`;
  });
  console.log(`packetId ${packet.packetId}  材料 ${inputs.length} 本  行数: ${counts.join(" / ")}`);
  console.log("集計の行:");
  for (const row of aggregates) {
    const mark = row.recountable ? " " : "*";
    console.log(`  ${mark} ${row.id.padEnd(32)} ${numbersOf(row).padStart(11)} ${row.unit.padEnd(9)} ${row.timeDependent ? "時間に依る" : ""}`);
  }
  console.log("(* = 数え直せない行。理由は recountNote)");

  const outPath = argOf("out");
  if (outPath !== undefined) {
    writeFileSync(outPath, `${JSON.stringify(packet, null, 1)}\n`, "utf-8");
    console.log(`書いた: ${outPath}`);
  }
  if (problems.length > 0) {
    console.log(`\n問題 ${problems.length} 件:`);
    for (const line of problems) console.log(`  - ${line}`);
    process.exitCode = 1;
    return;
  }
  console.log("\n問題なし(schema・集計の筋・持ち時間・封・追跡性、そして渡された照合すべて)");
}

main();
