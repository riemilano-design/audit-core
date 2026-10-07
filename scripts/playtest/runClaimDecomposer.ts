// D-2b(audit-core/docs/CLAIM_DECOMPOSITION_D2B_PLAN_2026-10-07.md §2)。分解器の CLI。
//
// 【配線】下見(--dry-run)と本番は、この同じファイルの同じコードを通る。唯一の違いは、どの
// `fetch` を `lib/seatRun.ts` の `runSlot` へ渡すか(下見はネットワークに出ない `buildDryRunFetch`、
// 本番は本物の `fetch`)。instruction の道の解決・gold fixture の読み込み・`decomposeOriginalText` の
// 呼び出し・`decompositionCompare` への接続・保存物の書き出しは枝分かれしない(実測の事故
// 「絶対の道だけで下見して、本番で LLM を 1 回呼んだ後に相対の道で落ちた」を避けるため)。
//
// 【下見は .env を読まない】下見は API 鍵を一切使わないので、`.env`(鍵が入っている)を読み込まず、
// 3 社分のダミーの設定(ダミーの鍵・モデル名・単価)だけで `runSlot` を走らせる ― 3 社それぞれの
// schema の写し(`schemaAdapters.ts`)と応答の読み(`llmClient.ts`)を下見で確かめるため、3 社とも回す。
// 【本番は 1 社だけ】`DECOMPOSE_PROVIDER`(gpt/gemini/claude のどれか 1 つ)・`DECOMPOSE_COST_CAP_USD`
// を `.env` から読む(無ければ投げる ― 上限の無い実行はしない)。
//
// 使い方(下見。鍵を使わない):
//   npx tsx scripts/playtest/runClaimDecomposer.ts --gold-dir scripts/playtest/fixtures/decomposition \
//     --out-dir <dir> --dry-run
// 使い方(本番。司令塔が 1 回だけ行う):
//   npx tsx scripts/playtest/runClaimDecomposer.ts --gold-dir scripts/playtest/fixtures/decomposition \
//     --out-dir <dir> [--env .env] [--instruction audit-core/docs/CLAIM_DECOMPOSER_INSTRUCTION_v1_2026-10-07.md]
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import {
  DECOMPOSER_INSTRUCTION_SHA256, assertPricesPresent, decomposerInstructionShaProblems, type DecomposeConfig,
} from "./lib/claimDecomposer.js";
import { buildDryRunFetch } from "./lib/claimDecomposerDryRun.js";
import { runDecomposerOverGold, sumDecompositionCompare, type GoldFixtureFile } from "./lib/claimDecomposerRun.js";
import { ENV_NAMES, loadDotEnv, readEnv, readEnvNumber, redactSecrets } from "./lib/env.js";
import type { Provider } from "./lib/llmClient.js";
import type { SlotDeps, SlotRunResult } from "./lib/seatRun.js";
import type { Prices } from "./lib/tokenBudget.js";

const REPO_ROOT = path.resolve(new URL("../..", import.meta.url).pathname);
const DEFAULT_INSTRUCTION = "audit-core/docs/CLAIM_DECOMPOSER_INSTRUCTION_v1_2026-10-07.md";
const DEFAULT_GOLD_DIR = "scripts/playtest/fixtures/decomposition";
const DECOMPOSE_PROVIDER_ENV = "DECOMPOSE_PROVIDER";
const DECOMPOSE_COST_CAP_ENV = "DECOMPOSE_COST_CAP_USD";

function argOf(name: string): string | undefined {
  const index = process.argv.indexOf(`--${name}`);
  if (index < 0) return undefined;
  const value = process.argv[index + 1];
  return value === undefined || value.startsWith("--") ? undefined : value;
}
function flag(name: string): boolean {
  return process.argv.includes(`--${name}`);
}
function requiredArg(name: string): string {
  const value = argOf(name);
  if (value === undefined) throw new Error(`--${name} が要る`);
  return value;
}
function resolveRepoPath(p: string): string {
  return path.isAbsolute(p) ? p : path.join(REPO_ROOT, p);
}

function loadGoldFixtures(dir: string): GoldFixtureFile[] {
  const files = readdirSync(dir).filter((f) => f.endsWith(".json")).sort();
  return files.map((f) => {
    const json = JSON.parse(readFileSync(path.join(dir, f), "utf-8")) as Record<string, unknown>;
    return { id: f.replace(/\.json$/, ""), ...json } as GoldFixtureFile;
  });
}

const PROVIDER_SEATS: Record<"gpt" | "gemini" | "claude", { provider: Provider; modelName: string; keyName: string; priceNames: readonly [string, string]; limitName: string }> = {
  gpt: { provider: "openai", modelName: ENV_NAMES.models.gpt, keyName: ENV_NAMES.keys.openai, priceNames: ENV_NAMES.prices.gpt, limitName: ENV_NAMES.inputLimits.gpt },
  gemini: { provider: "gemini", modelName: ENV_NAMES.models.gemini, keyName: ENV_NAMES.keys.gemini, priceNames: ENV_NAMES.prices.gemini, limitName: ENV_NAMES.inputLimits.gemini },
  claude: { provider: "anthropic", modelName: ENV_NAMES.models.claude, keyName: ENV_NAMES.keys.anthropic, priceNames: ENV_NAMES.prices.claude, limitName: ENV_NAMES.inputLimits.claude },
};

/** 本番: `.env` から 1 社分の設定を読む(`runSeats.ts` の `pricesOf`/`seatConfigs` と同じ考え方の小さい写し)。 */
function productionConfigOf(seatName: "gpt" | "gemini" | "claude", capUsd: number, warnings: string[]): DecomposeConfig {
  const seat = PROVIDER_SEATS[seatName];
  const apiKey = readEnv(seat.keyName) ?? "";
  const model = readEnv(seat.modelName) ?? "";
  const inPerMillion = readEnvNumber(seat.priceNames[0]) ?? 0;
  const outPerMillion = readEnvNumber(seat.priceNames[1]) ?? 0;
  if (inPerMillion === 0 || outPerMillion === 0) warnings.push(`${seatName}: 単価(${seat.priceNames.join(" / ")})が .env に無い ― 費用を 0 と見なして進めない`);
  const prices: Prices = { inPerMillion, outPerMillion };
  const limit = readEnvNumber(seat.limitName);
  return {
    provider: seat.provider, model, apiKey, prices, reserveOutputTokens: 4_000, temperature: 0, capUsd,
    ...(limit === undefined ? {} : { inputLimit: limit }),
  };
}

/** 下見: 3 社分のダミー設定(鍵を使わない。`.env` を読まない)。 */
function dryRunConfigsOf(capUsd: number): Array<{ seat: "gpt" | "gemini" | "claude"; cfg: DecomposeConfig }> {
  return (["gpt", "gemini", "claude"] as const).map((seat) => ({
    seat,
    cfg: {
      provider: PROVIDER_SEATS[seat].provider, model: "dry-run-model", apiKey: "dry-run-key",
      prices: { inPerMillion: 1, outPerMillion: 1 }, reserveOutputTokens: 4_000, temperature: 0, capUsd,
    },
  }));
}

function writeSlotFiles(dir: string, slot: SlotRunResult, secrets: readonly (string | undefined)[]): void {
  mkdirSync(dir, { recursive: true });
  for (const file of slot.files) writeFileSync(path.join(dir, file.name), redactSecrets(file.content, secrets), "utf-8");
}

function printTotals(label: string, totals: ReturnType<typeof sumDecompositionCompare>): void {
  console.log(`  ${label}: span 交わり ${totals.spanIntersection}・正解のみ ${totals.spanExpectedOnly}・実測のみ ${totals.spanActualOnly} / value 一致 ${totals.valueMatchCount} / form 一致 ${totals.formMatchCount} / uncovered 交わり ${totals.uncoveredIntersection}・正解のみ ${totals.uncoveredExpectedOnly}・実測のみ ${totals.uncoveredActualOnly}`);
}

async function runOneConfig(label: string, cfg: DecomposeConfig, instruction: string, golds: GoldFixtureFile[], deps: SlotDeps, outDir: string, secrets: readonly (string | undefined)[]): Promise<void> {
  const results = await runDecomposerOverGold(golds, instruction, cfg, deps);
  for (const r of results) {
    writeSlotFiles(path.join(outDir, label, r.goldId), r.slot, secrets);
    const state = r.slot.present ? `present(claims ${(r.slot.llm?.claims as unknown[] | undefined)?.length ?? 0} 件)` : `空席(${r.slot.absentReason})`;
    console.log(`  ${label} / ${r.goldId}: ${state} / 実費 ${r.slot.actualCostUsd.toFixed(4)} ドル・累計 ${r.slot.cumulativeCostUsd.toFixed(4)} ドル`);
    if (r.compare !== undefined) {
      writeFileSync(path.join(outDir, label, `${r.goldId}.compare.json`), `${JSON.stringify(r.compare, null, 1)}\n`, "utf-8");
    }
  }
  const compares = results.flatMap((r) => (r.compare === undefined ? [] : [r.compare]));
  const totals = sumDecompositionCompare(compares);
  writeFileSync(path.join(outDir, label, "totals.json"), `${JSON.stringify(totals, null, 1)}\n`, "utf-8");
  printTotals(`${label} 合計(${compares.length}/${golds.length} 本が照合まで進んだ)`, totals);
}

async function main(): Promise<void> {
  const goldDir = resolveRepoPath(argOf("gold-dir") ?? DEFAULT_GOLD_DIR);
  const instructionPath = resolveRepoPath(argOf("instruction") ?? DEFAULT_INSTRUCTION);
  const outDir = resolveRepoPath(requiredArg("out-dir"));
  const instruction = readFileSync(instructionPath, "utf-8");

  // 送る前の門: 指示文の sha を固定値と照合する(下見・本番どちらも通る ― 鍵を使わない門)。
  const shaProblems = decomposerInstructionShaProblems(path.basename(instructionPath), instruction);
  if (shaProblems.length > 0) throw new Error(`指示文の sha が固定値と合わない:\n${shaProblems.map((l) => `  - ${l}`).join("\n")}`);

  const golds = loadGoldFixtures(goldDir);
  console.log(`gold: ${goldDir} から ${golds.length} 本(${golds.map((g) => g.id).join(", ")})`);
  mkdirSync(outDir, { recursive: true });

  if (flag("dry-run")) {
    console.log(`下見: .env を読まない・鍵を使わない。指示文 ${path.basename(instructionPath)} の sha は固定値 ${DECOMPOSER_INSTRUCTION_SHA256[path.basename(instructionPath)]?.slice(0, 12)}… と一致。`);
    const { fetch: dryFetch, log } = buildDryRunFetch();
    const deps: SlotDeps = { fetch: dryFetch, sleep: async () => {} };
    for (const { seat, cfg } of dryRunConfigsOf(1000)) {
      await runOneConfig(seat, cfg, instruction, golds, deps, outDir, []);
    }
    console.log(`下見: 入口を叩いた回数 ${log.calls.length}(内訳 ${JSON.stringify(log.calls.reduce((acc: Record<string, number>, c) => { acc[`${c.provider}:${c.kind}`] = (acc[`${c.provider}:${c.kind}`] ?? 0) + 1; return acc; }, {}))})`);
    return;
  }

  const envPath = resolveRepoPath(argOf("env") ?? ".env");
  loadDotEnv(envPath);
  const seatName = readEnv(DECOMPOSE_PROVIDER_ENV) as "gpt" | "gemini" | "claude" | undefined;
  if (seatName === undefined || !(seatName in PROVIDER_SEATS)) {
    throw new Error(`${DECOMPOSE_PROVIDER_ENV} が .env に無い(gpt / gemini / claude のどれか)`);
  }
  const capUsd = readEnvNumber(DECOMPOSE_COST_CAP_ENV);
  if (capUsd === undefined) throw new Error(`${DECOMPOSE_COST_CAP_ENV} が .env に無い ― 上限の無い実行はしない`);
  const warnings: string[] = [];
  const cfg = productionConfigOf(seatName, capUsd, warnings);
  for (const w of warnings) console.log(`  注意: ${w}`);
  // 単価が無ければ費用が 0 に見え、上限が効かない ― 送る前に止める(`runSeats.ts` の `seatsMissingPrices` と同じ規律)
  assertPricesPresent(seatName, warnings);
  if (cfg.apiKey === "" || cfg.model === "") throw new Error(`${seatName}: 鍵かモデル名が .env に無い`);
  const secrets = [readEnv(ENV_NAMES.keys.openai), readEnv(ENV_NAMES.keys.gemini), readEnv(ENV_NAMES.keys.anthropic)];
  const deps: SlotDeps = { fetch };
  await runOneConfig(seatName, cfg, instruction, golds, deps, outDir, secrets);
}

await main();
