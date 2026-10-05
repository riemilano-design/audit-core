// 言い換えの束 ― **1 回限りの境界測定実験**(人間の GO 2026-10-05。司令塔の中継。計画 docs/PLAN_FILL_TEXTS_2026-10-05.md §7)。
//
// 使い方(下見。鍵を使わない・送らない。**照合の配線は本番と同じ経路で 1 回通す** ― 人間の GO 条件 2):
//   npx tsx scripts/playtest/fillTexts.ts --selection <out/<顧客>/exit/answer_selection.json> --seats-dir <out/<顧客>/llm-seats> \
//     --out-dir <out/<顧客>/exit> [--env .env] --dry-run
// 本番(**司令塔の合図の後に 1 回だけ**。同じ out-dir に report が在れば回さない = 2 回目を回さない):
//   SEAT_COST_CAP_USD=1 npx tsx scripts/playtest/fillTexts.ts … (同じ引数で --dry-run を外す)
//   【上限 1 の置き方(司令塔 2026-10-05)】.env は書き換えない(鍵と同じファイル)。回すその 1 回のコマンドの環境変数で渡す ―
//   `loadDotEnv` は既に在る環境変数を上書きしないので、下見で「有効な上限 SEAT_COST_CAP_USD = 1」が印字されることを先に確かめる。
//   【道の引数は打った場所(cwd)から絶対に解く】(人間の GO 条件 1。2026-10-05 の 1 回限りの実行は、相対の道を python(cwd = report-pdf)に
//   そのまま渡して lead 1 回の呼び出しの後に落ちた。陽性対照 = `lib/fillTextsCli.test.ts`)
//
// 【段にしない】deliver.ts に足さない(条件 6)。出力は out/ にだけ: fill_texts.json(採用可能の文だけ)・fill_texts.problems.json・
//   fill_texts.report.json(スロットごとに 試行数 / F-5 通過数 / 採用可能数 / 失敗理由 / 実費 / 最大費用。**F-5 通過と採用可能は別項目** ― 条件 11)・
//   attempts/<runId>/(試行の記録 `attempt_<slot>_<n>.json` を**呼び出しの前に作り、後に同じファイルへ**成功/失敗と usage・実費を書く ― 条件 4。原文・指摘も)。
// 【生成結果は監査済みの事実ではない】採用は司令塔、送付は人間(条件 4)。
// 【照合は python の 1 か所】`exit_fill.py --verify-texts`(F-5 + 禁止語 + 長さ。`f5` の欄で F-5 そのものを別に返す)。用語と禁止語も `exit_fill.py --print-terms` から参照で受ける(写さない)。
import { execFileSync, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { ENV_NAMES, loadDotEnv, readEnv, readEnvNumber, redactSecrets } from "./lib/env.js";
import { EXPERIMENT, FillTextsError, instructionText, maxCostBefore, runFillTexts, slotJobsOf, userTextOf, type TermLine, type VerifyVerdict } from "./lib/fillTexts.js";
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
/**
 * 道の引数は**打った場所(cwd)から絶対の道に解いて**から使う(人間の GO 条件 1・2026-10-05)。
 * python(`exit_fill.py`)は cwd = report-pdf で起こすので、相対の道をそのまま渡すと report-pdf 相対で探して「無い」になる
 * ― 2026-10-05 の 1 回限りの実行が lead 1 回の呼び出しの後にここで落ちた(陽性対照 `lib/fillTextsCli.test.ts`)。
 */
function requiredPath(name: string): string {
  return path.resolve(process.cwd(), requiredArg(name));
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

/** python の `--verify-texts` の出力(problems・f5)→ スロット → 判定。 */
function verdictsOf(out: Record<string, unknown>): Record<string, VerifyVerdict> {
  const problems = (out.problems ?? {}) as Record<string, string[]>;
  const f5 = (out.f5 ?? {}) as Record<string, boolean>;
  const verdicts: Record<string, VerifyVerdict> = {};
  for (const [slot, list] of Object.entries(problems)) verdicts[slot] = { problems: list, f5Passed: f5[slot] === true };
  return verdicts;
}

/**
 * 照合(F-5 + 禁止語 + 長さ)。**本番と下見の 1 か所**(人間の GO 条件 2: 下見も python の起動・道の解決・JSON の往復を本番と同じ経路で通す)。
 * 文を `inputPath` に書き、python に `--verify-texts` で読ませる。
 */
function verifyTexts(texts: Record<string, string>, inputPath: string, selectionPath: string, seatsDir: string): { verdicts: Record<string, VerifyVerdict>; raw: Record<string, unknown> } {
  writeFileSync(inputPath, `${JSON.stringify(texts, null, 1)}\n`, "utf-8");
  const raw = pyJson(["--verify-texts", inputPath, "--selection", selectionPath, "--seats-dir", seatsDir, "--max-chars", String(EXPERIMENT.maxChars)]);
  return { verdicts: verdictsOf(raw), raw };
}

async function main(): Promise<void> {
  const envArg = argOf("env");
  const envPath = envArg === undefined ? path.join(REPO_ROOT, ".env") : path.resolve(process.cwd(), envArg);
  if (existsSync(envPath)) loadDotEnv(envPath);
  const selectionPath = requiredPath("selection");
  const seatsDir = requiredPath("seats-dir");
  const outDir = requiredPath("out-dir");
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
    // 条件 2: API 呼び出しだけを省き、照合の配線(python の起動・道の解決・JSON の往復)は本番と同じ関数で通す ― 文を空にした入力。
    // (2026-10-05 の 1 回限りの実行は、下見が照合を呼ばなかったので、相対の道の不具合が本番で初めて出た。)
    const wiringInput = path.join(outDir, "fill_texts.dryrun.verify_input.json");
    const wiring = verifyTexts(Object.fromEntries(jobs.map((j) => [j.slot, ""])), wiringInput, selectionPath, seatsDir);
    const problemCounts = Object.fromEntries(Object.entries(wiring.verdicts).map(([slot, v]) => [slot, v.problems.length]));
    const verifyWiring = { calls: 1, inputPath: wiringInput, checked: wiring.raw.checked, problemCounts, f5: Object.fromEntries(Object.entries(wiring.verdicts).map(([slot, v]) => [slot, v.f5Passed])), maxChars: wiring.raw.maxChars };
    writeFileSync(path.join(outDir, "fill_texts.dryrun.json"), `${JSON.stringify({ slots: jobs.map((j) => ({ slot: j.slot, kind: j.kind, statementChars: j.statement.length })), maxCostUsdBefore: before, fixed: EXPERIMENT, model: model ?? null, verifyWiring }, null, 1)}\n`, "utf-8");
    console.log(`照合の配線: exit_fill.py --verify-texts を 1 回呼んだ(空の文 ${String(jobs.length)} 本 → JSON が返った・問題 ${String(Object.values(problemCounts).reduce((a, b) => a + b, 0))} 件)`);
    console.log("下見だけ(送っていない)");
    return;
  }
  const reportPath = path.join(outDir, "fill_texts.report.json");
  if (existsSync(reportPath)) throw new FillTextsError(`${reportPath} が既に在る ― この実験は 1 回だけ(条件 7)。2 回目は回さない`);
  const attemptRunId = `${randomBytes(4).toString("hex")}-${today().replace(/-/g, "")}`;
  // 試行の記録は attempts/<attemptRunId>/ の下(前の実行の記録を上書きしない ― 2026-10-05 に落ちた実行の attempts/verify_input_1.json を残す)。
  const attemptsDir = path.join(outDir, "attempts", attemptRunId);
  mkdirSync(attemptsDir, { recursive: true });
  const secrets = [apiKey];
  let verifyCount = 0;
  const result = await runFillTexts(
    { jobs, instruction, ...(model === undefined ? {} : { model }), ...(apiKey === undefined ? {} : { apiKey }), prices, capUsdFromEnv, runId: attemptRunId, today: today(), gitHead: gitHead() },
    {
      call: (req, key) => callStructured(req, { fetch, apiKey: key }),
      verify: async (texts) => {
        verifyCount += 1;
        return verifyTexts(texts, path.join(attemptsDir, `verify_input_${String(verifyCount)}.json`), selectionPath, seatsDir).verdicts;
      },
      // 条件 4: 試行の記録(呼び出しの前・後・照合の後)と原文を**その場で**書く。落ちても消えない。
      persist: (file) => { writeFileSync(path.join(attemptsDir, file.name), redactSecrets(file.content, secrets), "utf-8"); },
    },
  );
  writeFileSync(path.join(outDir, "fill_texts.json"), `${JSON.stringify(result.texts, null, 1)}\n`, "utf-8");
  writeFileSync(path.join(outDir, "fill_texts.problems.json"), `${JSON.stringify(result.problems, null, 1)}\n`, "utf-8");
  writeFileSync(reportPath, `${redactSecrets(JSON.stringify(result.report, null, 1), secrets)}\n`, "utf-8");
  const totals = result.report.totals as Record<string, unknown>;
  for (const s of result.report.slots as Record<string, unknown>[]) {
    console.log(`  ${String(s.slot).padEnd(6)} 試行 ${String(s.attempts)} / F-5 通過 ${String(s.f5Passed)} / 採用可能 ${String(s.adoptable)} / 実費 ${Number(s.actualCostUsd).toFixed(4)} / 最大 ${Number(s.maxCostUsdBefore).toFixed(4)}${s.notAttempted === undefined ? "" : ` / 回していない(${String(s.notAttempted)})`}`);
  }
  console.log(`呼び出し ${String(totals.calls)} / 実費 ${Number(totals.actualCostUsd).toFixed(4)} USD / 最大費用(実行前) ${Number(totals.maxCostUsdBefore).toFixed(4)} USD${totals.stopReason === null ? "" : ` / 止めた: ${String(totals.stopReason)}`}`);
  console.log(`書いた: ${outDir}(fill_texts.json・fill_texts.problems.json・fill_texts.report.json・attempts/${attemptRunId}/)― 生成結果は監査済みの事実ではない。ここで停止`);
}

await main();
