// Audit Core T-1(docs/AUDIT_CORE_EXTRACTION_PLAN.md §5・§7 Phase 0)。Golden Master の期待値を実物から測り、
// `docs/golden_master/<name>_expectation.json` と比べる(または書く)。
//
// 使い方:
//   npx tsx scripts/playtest/goldenMasterCheck.ts --expect docs/golden_master/c5_expectation.json [--write] [--customer-dir <dir>]
//
// - `inputs` の節は人が書く(どの実物を測るか)。それ以外の節(`identity`・`packet`・`g9`・`g8`)は機械が書く。
// - `--write` が無ければ測った値と期待値を比べ、違いを 1 行 1 件で出して rc=1。一致なら rc=0。
// - 実物(`scripts/playtest/out/`)は git に無い。ここに書くのは sha256・判定・3 つの数だけ。
//
// 【このファイルが絶対にやらないこと】門の判定・閾値・文言を新しく作ること。実物(PDF・md・packet)を書き換えること。
// 門の引数を自分で組むこと(`lib/deliver.ts` の組み立てをそのまま使う ― 本番と同じ引数で測る)。

import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  type DeliverProbe,
  answerMaterialFlags,
  checkStructureCommand,
  customerDirOf,
  deliverOutPaths,
  exitGateCommand,
  groupListOf,
  groupPaths,
  materialPlanOf,
  parseDeliverArgs,
} from "./lib/deliver.js";
import { checkResultLines, loadObsRegistry, validateHypothesisLine } from "./lib/hypothesis.js";
import { integrationProblems } from "./lib/integration.js";
import { canonicalJson, observationPacketProblems, packetIdOf } from "./lib/observationPacket.js";
import { seatOutputProblems } from "./lib/seatOutput.js";
import type { SeatInputMeta } from "./lib/seatInput.js";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const REPORT_PDF = path.join("scripts", "playtest", "report-pdf");
const USAGE = "使い方: npx tsx scripts/playtest/goldenMasterCheck.ts --expect <expectation.json> [--write] [--customer-dir <dir>]";

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
type Rec = Record<string, Json>;

interface Inputs {
  customer_dir: string;
  packet: string;
  request: string;
  answer_selection: string;
  deliver_dir: string;
  work_dir: string;
  kifu_dir: string;
  person: string;
  time_limit_sec: number;
  today: string;
  group_label: string;
  sent_pdf_dir: string;
  sent_pdfs: string[];
  seat_runs_dir: string;
  obs_items: string;
}

interface GateRecord {
  status: "pass" | "fail" | "error";
  return_code: number;
  errors: string[];
  warnings: string[];
  stdout: string[];
}

function sha256Of(buffer: Buffer): string {
  return createHash("sha256").update(buffer).digest("hex");
}

function fileIdentity(absPath: string): { sha256: string; bytes: number } {
  const buffer = readFileSync(absPath);
  return { sha256: sha256Of(buffer), bytes: buffer.length };
}

function rel(absPath: string): string {
  return path.relative(REPO_ROOT, absPath).split(path.sep).join("/");
}

function normalize(text: string): string {
  return text.split(REPO_ROOT).join("<repo>");
}

function lines(text: string): string[] {
  return normalize(text).split("\n").filter((line) => line.length > 0);
}

function statusOf(rc: number): GateRecord["status"] {
  return rc === 0 ? "pass" : rc === 1 ? "fail" : "error";
}

const WARNING_RE = /^(\(報告\)|注記:)/;

function runPythonGate(script: string, args: readonly string[]): GateRecord {
  const result = spawnSync("python3", ["-X", "utf8", path.join(REPORT_PDF, script), ...args], {
    cwd: REPO_ROOT,
    env: process.env,
    encoding: "utf-8",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  const rc = result.status ?? -1;
  const stderr = lines(result.stderr);
  return {
    status: statusOf(rc),
    return_code: rc,
    errors: stderr.filter((line) => !WARNING_RE.test(line)),
    warnings: stderr.filter((line) => WARNING_RE.test(line)),
    stdout: lines(result.stdout),
  };
}

const probe: DeliverProbe = {
  exists: (filePath) => existsSync(filePath),
  hasJsonl: (dirPath) => existsSync(dirPath) && readdirSync(dirPath).some((name) => name.endsWith(".jsonl")),
  fixedKifuFiles: (dirPath) =>
    existsSync(dirPath) ? readdirSync(dirPath).filter((name) => name.endsWith(".fixed.json")).sort().map((name) => path.join(dirPath, name)) : [],
  timeUpLossCount: () => 0,
  mtimeMs: (filePath) => (existsSync(filePath) ? statSync(filePath).mtimeMs : undefined),
};

function readJson(absPath: string): unknown {
  return JSON.parse(readFileSync(absPath, "utf-8"));
}

function measure(inputs: Inputs, customerDirOverride: string | undefined): Rec {
  const customerDir = path.resolve(REPO_ROOT, customerDirOverride ?? inputs.customer_dir);
  const packetPath = path.join(customerDir, inputs.packet);
  const requestPath = path.join(customerDir, inputs.request);
  const deliverDir = path.join(customerDir, inputs.deliver_dir);
  const workDir = path.join(customerDir, inputs.work_dir);
  const kifuDir = path.join(customerDir, inputs.kifu_dir);
  const obsItems = path.resolve(REPO_ROOT, inputs.obs_items);

  // ---- 門の引数は lib/deliver.ts に組ませる(本番の deliver.ts と同じ 1 か所) ----
  // `--name`・`--title` は 30p 形のどの冊子にも届かない(lib/deliver.ts の納品ログの注記)。ここでは伏せ字。
  const args = parseDeliverArgs([
    "--person", inputs.person, "--kifu-dir", kifuDir, "--work", workDir, "--time-limit-sec", String(inputs.time_limit_sec),
    "--name", "-", "--title", "-", "--today", inputs.today, "--out", deliverDir, "--group-label", inputs.group_label,
  ]);
  const groups = groupListOf(args);
  const thisGroup = groupPaths({ work: args.work, timeLimitSec: args.timeLimitSec }, args.person);
  const out = deliverOutPaths(args.out);
  const plan = materialPlanOf(args);
  const derivedCustomerDir = customerDirOf(groups);
  if (derivedCustomerDir !== customerDir) throw new Error(`work の親が customer_dir と違う: ${derivedCustomerDir} / ${customerDir}`);

  const exitGateArgs = exitGateCommand(groups, probe, out, plan, customerDir);
  const checkAnswerArgs = [out.honbunMd, ...answerMaterialFlags(groups, probe, out, plan)];
  const checkStructureArgs = checkStructureCommand(groups, probe, out, plan, thisGroup, args.out, customerDir);

  // ---- 入力の同一性(門に渡した実物ファイルの sha256) ----
  const identity: Record<string, Json> = {};
  const addIdentity = (absPath: string): void => {
    if (existsSync(absPath) && statSync(absPath).isFile()) identity[rel(absPath)] = fileIdentity(absPath);
  };
  for (const arg of [...exitGateArgs, ...checkAnswerArgs, ...checkStructureArgs]) if (path.isAbsolute(arg)) addIdentity(arg);
  addIdentity(obsItems);

  // ---- G-2 packet ----
  const packet = readJson(packetPath) as { packetId?: unknown; facts?: unknown; aggregates?: unknown };
  const canonical = canonicalJson({ aggregates: packet.aggregates, facts: packet.facts });
  const canonicalSha = sha256Of(Buffer.from(canonical, "utf-8"));
  const packetId = packetIdOf(packet.facts, packet.aggregates);
  if (!canonicalSha.startsWith(packetId)) throw new Error("packetIdOf が canonical の sha256 の先頭と一致しない(道具の前提が崩れた)");
  const packetRecord: Rec = {
    packet_id: String(packet.packetId),
    packet_id_recomputed: packetId,
    canonical_sha256: canonicalSha,
    canonical_bytes: Buffer.byteLength(canonical, "utf-8"),
    file_sha256: fileIdentity(packetPath).sha256,
    file_bytes: fileIdentity(packetPath).bytes,
    problems: observationPacketProblems(packet).map(normalize),
  };

  // ---- G-9 Python の門 3 つ ----
  const g9: Rec = {};
  g9.exit_gate = runPythonGate("exit_gate.py", exitGateArgs) as unknown as Rec;
  g9.check_answer = runPythonGate("check_answer.py", checkAnswerArgs) as unknown as Rec;
  g9.check_structure = runPythonGate("check_structure.py", checkStructureArgs) as unknown as Rec;

  // ---- G-5/G-9 TS の門 3 つ(CLI と同じ材料・同じ関数) ----
  const registry = loadObsRegistry(obsItems);
  const request = readJson(requestPath);
  const seatsDir = path.join(customerDir, inputs.seat_runs_dir);
  const hypothesisCheck: Rec = {};
  const seatOutputCheck: Rec = {};
  const integrationCheck: Rec = {};
  const seatRuns: Json[] = [];
  const runIds = existsSync(seatsDir)
    ? readdirSync(seatsDir).filter((name) => statSync(path.join(seatsDir, name)).isDirectory()).sort()
    : [];
  for (const runId of runIds) {
    const runDir = path.join(seatsDir, runId);
    const summaryPath = path.join(runDir, "run_summary.json");
    if (!existsSync(summaryPath)) continue;
    const summary = readJson(summaryPath) as { today?: unknown };
    const today = String(summary.today);
    const metaPath = path.join(runDir, "seat_input.meta.json");
    const seatFiles = readdirSync(runDir).filter((name) => /^seat_(gpt|gemini|claude)\.json$/.test(name)).sort();
    const hasIntegration = existsSync(path.join(runDir, "integration.json"));
    seatRuns.push({ run_id: runId, today, seat_files: seatFiles, integration: hasIntegration });
    addIdentity(metaPath);
    const meta = readJson(metaPath) as SeatInputMeta;
    for (const seatFile of seatFiles) {
      const seatPath = path.join(runDir, seatFile);
      addIdentity(seatPath);
      const envelope = readJson(seatPath) as { items?: unknown[] };
      const key = `${runId}/${seatFile}`;

      const problems = seatOutputProblems(envelope, { meta, request, today, packet }).map(normalize);
      seatOutputCheck[key] = { status: statusOf(problems.length > 0 ? 1 : 0), return_code: problems.length > 0 ? 1 : 0, problems };

      const items = Array.isArray(envelope.items) ? envelope.items : [];
      let anyFailed = false;
      const perItem: Json[] = items.map((line) => {
        const results = validateHypothesisLine(line, { today, registry, packet });
        if (results.some((r) => !r.ok)) anyFailed = true;
        const id = (line as { hypothesisId?: unknown } | null)?.hypothesisId;
        return { hypothesis_id: String(id), lines: results.flatMap((r) => checkResultLines(r)).map(normalize) };
      });
      hypothesisCheck[key] = { status: statusOf(anyFailed ? 1 : 0), return_code: anyFailed ? 1 : 0, items: perItem };
    }
    if (hasIntegration) {
      const integrationPath = path.join(runDir, "integration.json");
      const inputPath = path.join(runDir, "integration_input.json");
      addIdentity(integrationPath);
      addIdentity(inputPath);
      const problems = integrationProblems(readJson(integrationPath), readJson(inputPath), { today, packet }).map(normalize);
      integrationCheck[runId] = { status: statusOf(problems.length > 0 ? 1 : 0), return_code: problems.length > 0 ? 1 : 0, problems };
    }
  }
  g9.hypothesisCheck = hypothesisCheck;
  g9.seatOutputCheck = seatOutputCheck;
  g9.integrationCheck = integrationCheck;

  // ---- G-8 PDF の封(compare_render.py --seal の 3 つの数) ----
  const sentDir = path.join(customerDir, inputs.sent_pdf_dir);
  const pdfPaths = inputs.sent_pdfs.map((name) => path.join(sentDir, name));
  for (const p of pdfPaths) addIdentity(p);
  const sealPath = path.join(mkdtempSync(path.join(tmpdir(), "golden-master-seal-")), "seal.json");
  const seal = spawnSync("python3", ["-X", "utf8", path.join(REPORT_PDF, "compare_render.py"), "--seal", sealPath, ...pdfPaths], {
    cwd: REPO_ROOT, env: process.env, encoding: "utf-8",
  });
  if (seal.status !== 0) throw new Error(`compare_render.py --seal が落ちた(rc=${String(seal.status)}): ${seal.stderr}`);
  const books = (readJson(sealPath) as { books: Record<string, Json> }).books;
  const g8: Rec = {};
  for (const [relKey, book] of Object.entries(books)) g8[path.basename(relKey)] = book;

  return {
    identity: Object.fromEntries(Object.entries(identity).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))),
    packet: packetRecord,
    seat_runs: seatRuns,
    g9,
    g8,
  };
}

function diff(expected: Json | undefined, actual: Json | undefined, at: string, out: string[]): void {
  if (out.length >= 200) return;
  const isObj = (x: unknown): x is Rec => x !== null && typeof x === "object" && !Array.isArray(x);
  if (Array.isArray(expected) && Array.isArray(actual)) {
    if (expected.length !== actual.length) out.push(`${at}: 長さ 期待 ${expected.length} / 実測 ${actual.length}`);
    for (let i = 0; i < Math.min(expected.length, actual.length); i += 1) diff(expected[i], actual[i], `${at}[${i}]`, out);
    return;
  }
  if (isObj(expected) && isObj(actual)) {
    for (const key of new Set([...Object.keys(expected), ...Object.keys(actual)])) {
      if (!(key in expected)) out.push(`${at}.${key}: 期待に無い`);
      else if (!(key in actual)) out.push(`${at}.${key}: 実測に無い`);
      else diff(expected[key], actual[key], `${at}.${key}`, out);
    }
    return;
  }
  if (JSON.stringify(expected) !== JSON.stringify(actual)) out.push(`${at}: 期待 ${JSON.stringify(expected)} / 実測 ${JSON.stringify(actual)}`);
}

const MEASURED_KEYS = ["identity", "packet", "seat_runs", "g9", "g8"] as const;

function main(): number {
  const argv = process.argv.slice(2);
  const argOf = (name: string): string | undefined => {
    const index = argv.indexOf(name);
    return index >= 0 ? argv[index + 1] : undefined;
  };
  const expectPath = argOf("--expect");
  if (expectPath === undefined) {
    console.error(USAGE);
    return 2;
  }
  const write = argv.includes("--write");
  const absExpect = path.resolve(REPO_ROOT, expectPath);
  const expectation = readJson(absExpect) as Rec;
  const inputs = expectation.inputs as unknown as Inputs;
  const measured = measure(inputs, argOf("--customer-dir"));

  if (write) {
    const next: Rec = {};
    for (const [key, value] of Object.entries(expectation)) if (!(MEASURED_KEYS as readonly string[]).includes(key)) next[key] = value;
    for (const key of MEASURED_KEYS) next[key] = measured[key]!;
    writeFileSync(absExpect, `${JSON.stringify(next, null, 1)}\n`, "utf-8");
    console.log(`wrote ${rel(absExpect)}`);
    return 0;
  }
  const differences: string[] = [];
  for (const key of MEASURED_KEYS) diff(expectation[key], measured[key], key, differences);
  if (differences.length > 0) {
    console.error(`★期待値と違う(${differences.length} 件${differences.length >= 200 ? "以上" : ""}):`);
    for (const d of differences) console.error(`- ${d}`);
    return 1;
  }
  const g9 = measured.g9 as Rec;
  console.log(`期待値のとおり(${rel(absExpect)})`);
  console.log(`  packet ${String((measured.packet as Rec).packet_id)}・門 ${Object.keys(g9).length} 種・冊子 ${Object.keys(measured.g8 as Rec).length} 冊・入力 ${Object.keys(measured.identity as Rec).length} ファイル`);
  return 0;
}

process.exitCode = main();
