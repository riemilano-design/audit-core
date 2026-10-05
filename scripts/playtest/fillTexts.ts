// 言い換えの束 ― **1 回限りの境界測定実験**(人間の GO 2026-10-05。司令塔の中継。計画 docs/PLAN_FILL_TEXTS_2026-10-05.md §7)。
//
// 使い方(下見。鍵を使わない・送らない):
//   npx tsx scripts/playtest/fillTexts.ts --selection <out/<顧客>/exit/answer_selection.json> --seats-dir <out/<顧客>/llm-seats> \
//     --out-dir <out/<顧客>/exit> [--env .env] --dry-run
// 本番(**司令塔の合図の後に 1 回だけ**。同じ out-dir に report が在れば回さない = 2 回目を回さない):
//   SEAT_COST_CAP_USD=1 npx tsx scripts/playtest/fillTexts.ts … (同じ引数で --dry-run を外す)
//   【上限 1 の置き方(司令塔 2026-10-05)】.env は書き換えない(鍵と同じファイル)。回すその 1 回のコマンドの環境変数で渡す ―
//   `loadDotEnv` は既に在る環境変数を上書きしないので、下見で「有効な上限 SEAT_COST_CAP_USD = 1」が印字されることを先に確かめる。
//
// 【段にしない】deliver.ts に足さない(条件 6)。出力は out/ にだけ: fill_texts.json(F-5 を通った文だけ)・fill_texts.problems.json・
//   fill_texts.report.json(スロットごとに 試行数 / F-5 通過数 / 採用可能数 / 失敗理由 / 実費 / 最大費用)・attempts/(原文)。
// 【生成結果は監査済みの事実ではない】採用は司令塔、送付は人間(条件 4)。
// 【照合は python の 1 か所】`exit_fill.py --verify-texts`(F-5 + 長さ)。用語と禁止語も `exit_fill.py --print-terms` から参照で受ける(写さない)。
import { execFileSync, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { ENV_NAMES, loadDotEnv, readEnv, readEnvNumber, redactSecrets } from "./lib/env.js";
import { EXPERIMENT, FillTextsError, instructionText, maxCostBefore, runFillTexts, slotJobsOf, userTextOf, type TermLine } from "./lib/fillTexts.js";
import { callStructured } from "./lib/llmClient.js";
import { estimateTokensByChars } from "./lib/tokenBudget.js";

const REPO_ROOT = path.resolve(new URL("../..", import.meta.url).pathname);
const REPORT_PDF_DIR = path.join(REPO_ROOT, "scripts", "playtest", "report-pdf");

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
  if (value === undefined) throw new FillTextsError(`--${name} が要る`);
  return value;
}
function gitHead(): string | null {
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], { cwd: REPO_ROOT, encoding: "utf-8" }).trim();
  } catch {
    return null;
  }
}
function today(): string {
  return new Date().toISOString().slice(0, 10);
}
function readJson(p: string): Record<string, unknown> {
  return JSON.parse(readFileSync(p, "utf-8")) as Record<string, unknown>;
}

/** python の 1 か所(`exit_fill.py`)を呼ぶ。rc≠0 でも stdout の JSON を読む(--verify-texts は問題が在れば rc 1 で JSON を出す)。 */
function pyJson(args: readonly string[]): Record<string, unknown> {
  const r = spawnSync("python3", ["-X", "utf8", "exit_fill.py", ...args], { cwd: REPORT_PDF_DIR, encoding: "utf-8" });
  if (r.error !== undefined) throw new FillTextsError(`exit_fill.py を起動できない: ${r.error.message}`);
  const text = (r.stdout ?? "").trim();
  if (text.length === 0) throw new FillTextsError(`exit_fill.py ${args[0] ?? ""} が JSON を返さなかった(rc ${String(r.status)}): ${(r.stderr ?? "").slice(0, 300)}`);
  return JSON.parse(text) as Record<string, unknown>;
}

async function main(): Promise<void> {
  const envPath = argOf("env") ?? path.join(REPO_ROOT, ".env");
  if (existsSync(envPath)) loadDotEnv(envPath);
  const selectionPath = requiredArg("selection");
  const seatsDir = requiredArg("seats-dir");
  const outDir = requiredArg("out-dir");
  const selection = readJson(selectionPath);
  const runId = String(selection.runId ?? "");
  if (runId.length === 0) throw new FillTextsError("⑤ の runId が空 ― 統合の周を引けない");
  const integration = readJson(path.join(seatsDir, runId, "integration.json"));
  const jobs = slotJobsOf(selection, integration);

  const terms = pyJson(["--print-terms"]);
  const instruction = instructionText(terms.termLines as TermLine[], terms.forbiddenWords as string[], EXPERIMENT.maxChars);

  const [inName, outName] = ENV_NAMES.prices.claude;
  const prices = { inPerMillion: readEnvNumber(inName) ?? 0, outPerMillion: readEnvNumber(outName) ?? 0 };
  const apiKey = readEnv(ENV_NAMES.keys.anthropic);
  const model = readEnv(ENV_NAMES.models.claude);
  const capUsdFromEnv = readEnvNumber(ENV_NAMES.costCap);
  const before = maxCostBefore(jobs, instruction, prices);

  console.log(`スロット ${String(jobs.length)}: ${jobs.map((j) => `${j.slot}(${String(j.statement.length)} 字)`).join(" / ")}`);
  for (const j of jobs) console.log(`  ${j.slot.padEnd(6)} 入力 ≒ ${String(estimateTokensByChars(`${instruction}\n\n${userTextOf(j)}`).inputTokens)} トークン・最大 ${String(EXPERIMENT.maxAttemptsPerSlot)} 呼び出し ≒ ${(before.perSlot[j.slot] ?? 0).toFixed(4)} USD`);
  console.log(`最大費用(実行前・${String(EXPERIMENT.maxCalls)} 呼び出し × 入力の実測 + 取り置き ${String(EXPERIMENT.reserveOutputTokens)}) ≒ ${before.total.toFixed(4)} USD / この実験の上限 ${String(EXPERIMENT.capUsd)} USD / 有効な上限 ${ENV_NAMES.costCap} = ${String(capUsdFromEnv)}(環境変数が .env より先。1 でなければ回らない)`);

  mkdirSync(outDir, { recursive: true });
  if (flag("dry-run")) {
    writeFileSync(path.join(outDir, "fill_texts.dryrun.json"), `${JSON.stringify({ slots: jobs.map((j) => ({ slot: j.slot, kind: j.kind, statementChars: j.statement.length })), maxCostUsdBefore: before, fixed: EXPERIMENT, model: model ?? null }, null, 1)}\n`, "utf-8");
    console.log("下見だけ(送っていない)");
    return;
  }
  const reportPath = path.join(outDir, "fill_texts.report.json");
  if (existsSync(reportPath)) throw new FillTextsError(`${reportPath} が既に在る ― この実験は 1 回だけ(条件 7)。2 回目は回さない`);
  const attemptsDir = path.join(outDir, "attempts");
  mkdirSync(attemptsDir, { recursive: true });
  let verifyCount = 0;
  const result = await runFillTexts(
    { jobs, instruction, ...(model === undefined ? {} : { model }), ...(apiKey === undefined ? {} : { apiKey }), prices, capUsdFromEnv, runId: `${randomBytes(4).toString("hex")}-${today().replace(/-/g, "")}`, today: today(), gitHead: gitHead() },
    {
      call: (req, key) => callStructured(req, { fetch, apiKey: key }),
      verify: async (texts) => {
        verifyCount += 1;
        const input = path.join(attemptsDir, `verify_input_${String(verifyCount)}.json`);
        writeFileSync(input, `${JSON.stringify(texts, null, 1)}\n`, "utf-8");
        const out = pyJson(["--verify-texts", input, "--selection", selectionPath, "--seats-dir", seatsDir, "--max-chars", String(EXPERIMENT.maxChars)]);
        return (out.problems ?? {}) as Record<string, string[]>;
      },
    },
  );
  const secrets = [apiKey];
  for (const file of result.files) writeFileSync(path.join(attemptsDir, file.name), redactSecrets(file.content, secrets), "utf-8");
  writeFileSync(path.join(outDir, "fill_texts.json"), `${JSON.stringify(result.texts, null, 1)}\n`, "utf-8");
  writeFileSync(path.join(outDir, "fill_texts.problems.json"), `${JSON.stringify(result.problems, null, 1)}\n`, "utf-8");
  writeFileSync(reportPath, `${redactSecrets(JSON.stringify(result.report, null, 1), secrets)}\n`, "utf-8");
  const totals = result.report.totals as Record<string, unknown>;
  for (const s of result.report.slots as Record<string, unknown>[]) {
    console.log(`  ${String(s.slot).padEnd(6)} 試行 ${String(s.attempts)} / F-5 通過 ${String(s.f5Passed)} / 採用可能 ${String(s.adoptable)} / 実費 ${Number(s.actualCostUsd).toFixed(4)} / 最大 ${Number(s.maxCostUsdBefore).toFixed(4)}${s.notAttempted === undefined ? "" : ` / 回していない(${String(s.notAttempted)})`}`);
  }
  console.log(`呼び出し ${String(totals.calls)} / 実費 ${Number(totals.actualCostUsd).toFixed(4)} USD / 最大費用(実行前) ${Number(totals.maxCostUsdBefore).toFixed(4)} USD${totals.stopReason === null ? "" : ` / 止めた: ${String(totals.stopReason)}`}`);
  console.log(`書いた: ${outDir}(fill_texts.json・fill_texts.problems.json・fill_texts.report.json・attempts/)― 生成結果は監査済みの事実ではない。ここで停止`);
}

await main();
