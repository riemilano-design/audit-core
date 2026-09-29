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
// 【出口】問題が 1 件でもあれば終了コード 1(数が合わない・辿れない・材料が差し替わった、を黙って通さない)。
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { readFileSync } from "node:fs";
import path from "node:path";
import {
  aggregateCoverageProblems, aggregatesOf, bookletAgreementProblems, bookletMissingNotes, type AggregateRow, type BookletNumbers,
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

function bookletOf(comparePath: string, patient: unknown, direct: unknown): BookletNumbers {
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
  };
}

function numbersOf(row: AggregateRow): string {
  if (typeof row.value === "number") return String(row.value);
  return `${String(row.numerator)} / ${String(row.denominator)}`;
}

function main(): void {
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
  problems.push(...traceProblems(packet, { repoRoot: REPO_ROOT }));

  const requestPath = argOf("request");
  if (requestPath !== undefined) {
    const request = JSON.parse(readFileSync(requestPath, "utf-8")) as unknown;
    problems.push(...validateObservationRequest(request).map((line) => `request: ${line}`));
    problems.push(...requestAgreementProblems(packet, request));
  }
  const comparePath = argOf("compare");
  if (comparePath !== undefined) {
    problems.push(...bookletAgreementProblems(aggregates, bookletOf(comparePath, materials.patient, { counts: (JSON.parse(readFileSync(paths.direct, "utf-8")) as { counts?: unknown }).counts })));
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
  if (comparePath !== undefined) {
    console.log("照合の相手が材料に無い数(問題ではないが、黙って外さない):");
    for (const note of bookletMissingNotes(aggregates)) console.log(`  - ${note}`);
  }

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
