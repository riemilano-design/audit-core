// 3 席 LLM API の実行(束 R4。計画 docs/STEP_LLM_SEATS_R4_CALLSEAT_2026-09-30.md §5・§7)。
//
// 【顧客の PDF にどう出るか】今は何も変わらない。ここで得るのは検証(H-9・H-10)と採用(司令塔・人間)の前の材料で、顧客の文には 1 字も出ない。
// 【使い方】鍵・モデル名・単価・上限額は `.env`(gitignore。人間が置く)。**この道具は鍵を出力しない**。
//   下見(鍵を使わず、束と概算と上限だけ見る):
//     npx tsx scripts/playtest/runSeats.ts --packet <packet.json> --request <request.json> --out-dir <dir> --dry-run
//   本番(既定で 2 回。人間の決定 2026-09-30 = 揺れの床を初回に含める。**上限は 2 回の累計に掛かる**):
//     npx tsx scripts/playtest/runSeats.ts --packet <packet.json> --request <request.json> --out-dir <dir> \
//       --instruction docs/LLM_SEATS_INSTRUCTION_v1.1_2026-09-30.md --instruction-sha <固定 sha> \
//       --integrator-instruction docs/LLM_SEATS_INTEGRATOR_INSTRUCTION_v1_2026-09-30.md [--runs 2] [--env .env]
//   人の判断で席を**送らない**(断られた空席と区別して記録に残る。送らない席には鍵も単価も要らない):
//     … --hold-back-seat gemini --hold-back-reason "無料枠・人間の判断で保留"
// 【出口】1 回の中で席が 1 つも立たなければ終了コード 1(黙って「0 席の実行」を成功にしない)。
import { execFileSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { ENV_NAMES, loadDotEnv, readEnv, readEnvNumber, redactSecrets } from "./lib/env.js";
import { instructionExampleReport } from "./lib/instructionExamples.js";
import { renderSeatInput } from "./lib/seatInput.js";
import { FIXED_INSTRUCTION_SHA256, INTEGRATOR_RESERVE_OUTPUT_TOKENS, SEAT_RESERVE_OUTPUT_TOKENS, fixedShaProblems, parseHoldBack, runAll, seatsMissingPrices, type IntegratorConfig, type RunAllResult, type SeatConfig } from "./lib/seatRun.js";
import type { Seat } from "./lib/seatOutput.js";
import { budgetDecision, estimateTokensByChars, type Prices } from "./lib/tokenBudget.js";
import type { Provider } from "./lib/llmClient.js";

const REPO_ROOT = path.resolve(new URL("../..", import.meta.url).pathname);
const DEFAULT_INSTRUCTION = path.join(REPO_ROOT, "docs/LLM_SEATS_INSTRUCTION_v1_2026-09-30.md");

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
/** 2 回の実行の合言葉が同じにならないように、**先頭 8 桁を乱数にする**(合言葉は runId の先頭 8 桁。R1 で踏んだ) */
function newRunId(index: number): string {
  return `${randomBytes(4).toString("hex")}-${today().replace(/-/g, "")}-${index + 1}`;
}

const SEATS: Array<{ seat: Seat; provider: Provider; modelName: string; keyName: string; priceNames: readonly [string, string]; limitName: string }> = [
  { seat: "gpt", provider: "openai", modelName: ENV_NAMES.models.gpt, keyName: ENV_NAMES.keys.openai, priceNames: ENV_NAMES.prices.gpt, limitName: ENV_NAMES.inputLimits.gpt },
  { seat: "gemini", provider: "gemini", modelName: ENV_NAMES.models.gemini, keyName: ENV_NAMES.keys.gemini, priceNames: ENV_NAMES.prices.gemini, limitName: ENV_NAMES.inputLimits.gemini },
  { seat: "claude", provider: "anthropic", modelName: ENV_NAMES.models.claude, keyName: ENV_NAMES.keys.anthropic, priceNames: ENV_NAMES.prices.claude, limitName: ENV_NAMES.inputLimits.claude },
];

/** 単価。Gemini のように入力が大きいと上がる段があれば 3 つ揃って初めて段として扱う(欠けていたら段なし = 安い方に倒さないため警告) */
function pricesOf(seat: Seat, names: readonly [string, string], warnings: string[]): Prices {
  const inPerMillion = readEnvNumber(names[0]) ?? 0;
  const outPerMillion = readEnvNumber(names[1]) ?? 0;
  if (inPerMillion === 0 || outPerMillion === 0) warnings.push(`${seat}: 単価(${names.join(" / ")})が .env に無い ― 費用を 0 と見なして進めない`);
  const tierNames = seat === "gemini" ? ENV_NAMES.priceTiers.gemini : undefined;
  if (tierNames === undefined) return { inPerMillion, outPerMillion };
  const above = readEnvNumber(tierNames[0]);
  const tierIn = readEnvNumber(tierNames[1]);
  const tierOut = readEnvNumber(tierNames[2]);
  if (above === undefined || tierIn === undefined || tierOut === undefined) {
    warnings.push(`${seat}: 段の単価(${tierNames.join(" / ")})が揃っていない ― 段なしとして見積もる(大きい入力で安く見える)`);
    return { inPerMillion, outPerMillion };
  }
  return { inPerMillion, outPerMillion, tiers: [{ aboveInputTokens: above, inPerMillion: tierIn, outPerMillion: tierOut }] };
}

function seatConfigs(warnings: string[]): SeatConfig[] {
  // 人の判断で**送らない**席(読み方は lib/seatRun.ts の parseHoldBack。知らない名前・理由の空は投げる)
  const heldBack = parseHoldBack(process.argv, SEATS.map((s) => s.seat));
  return SEATS.map((s) => {
    const limit = readEnvNumber(s.limitName);
    const apiKey = readEnv(s.keyName);
    const model = readEnv(s.modelName);
    return {
      seat: s.seat, provider: s.provider, ...(model === undefined ? {} : { model }), ...(apiKey === undefined ? {} : { apiKey }),
      prices: pricesOf(s.seat, s.priceNames, heldBack.has(s.seat) ? [] : warnings), ...(limit === undefined ? {} : { inputLimit: limit }),
      reserveOutputTokens: SEAT_RESERVE_OUTPUT_TOKENS, temperature: 0,
      ...(heldBack.has(s.seat) ? { holdBack: heldBack.get(s.seat)! } : {}),
    };
  });
}

function integratorConfig(instructionPath: string | undefined, warnings: string[]): IntegratorConfig | undefined {
  const provider = readEnv(ENV_NAMES.integrator.provider) as Provider | undefined;
  const model = readEnv(ENV_NAMES.integrator.model);
  if (provider === undefined || model === undefined || instructionPath === undefined) {
    warnings.push(`整理役: ${ENV_NAMES.integrator.provider} / ${ENV_NAMES.integrator.model} / --integrator-instruction のどれかが無い ― 統合は行わない(席の封筒と器は残る)`);
    return undefined;
  }
  const keyName = provider === "openai" ? ENV_NAMES.keys.openai : provider === "gemini" ? ENV_NAMES.keys.gemini : ENV_NAMES.keys.anthropic;
  const priceNames = provider === "openai" ? ENV_NAMES.prices.gpt : provider === "gemini" ? ENV_NAMES.prices.gemini : ENV_NAMES.prices.claude;
  const seatOfProvider: Seat = provider === "openai" ? "gpt" : provider === "gemini" ? "gemini" : "claude";
  const apiKey = readEnv(keyName);
  return {
    provider, model, ...(apiKey === undefined ? {} : { apiKey }), prices: pricesOf(seatOfProvider, priceNames, warnings),
    reserveOutputTokens: INTEGRATOR_RESERVE_OUTPUT_TOKENS, temperature: 0, instruction: readFileSync(instructionPath, "utf-8"),
  };
}

function writeFiles(dir: string, result: RunAllResult, secrets: readonly (string | undefined)[]): void {
  mkdirSync(dir, { recursive: true });
  for (const file of result.files) writeFileSync(path.join(dir, file.name), redactSecrets(file.content, secrets), "utf-8");
}

function printRun(runId: string, result: RunAllResult): void {
  const summary = result.summary as Record<string, any>;
  console.log(`\n== ${runId}(packetId ${result.meta.packetId}・束 ${result.meta.bytes} B・概算 ${result.meta.tokenEstimate.value} トークン)`);
  for (const seat of summary.seats as Record<string, any>[]) {
    const state = seat.present === true ? `項目 ${String(seat.items)} 件・検査の指摘 ${String(seat.checkProblems)} 件`
      : seat.absentReason === "held_back" ? `送っていない(${String(seat.absentNote).replace(/^seat_[a-z]+: /, "")})` : `空席(${String(seat.absentReason)})`;
    console.log(`  ${String(seat.seat).padEnd(7)} ${String(seat.model ?? "-").padEnd(26)} ${state} / 実費 ${String(seat.actualCostUsd)} ドル・${String(seat.elapsedMs)} ms`);
  }
  const integ = summary.integration as Record<string, any> | null;
  if (integ !== null) console.log(`  整理役  ${String(integ.model ?? "-").padEnd(26)} ${integ.present === true ? `束 ${String(integ.clusters)} 件・検査の指摘 ${String(integ.checkProblems)} 件` : `無し(${String(integ.absentReason)})`} / 実費 ${String(integ.actualCostUsd)} ドル`);
  console.log(`  累計の実費 ${String(summary.totals.cumulativeCostUsd)} ドル(上限 ${String(summary.capUsd)} ドル・上限に達した: ${String(summary.totals.capReached)})`);
}

async function main(): Promise<void> {
  const envPath = argOf("env") ?? path.join(REPO_ROOT, ".env");
  const loaded = loadDotEnv(envPath);
  console.log(`.env: ${existsSync(envPath) ? `${envPath} から ${loaded.length} 個の名前を読んだ(値は出さない)` : `${envPath} が無い`}`);

  const packet = JSON.parse(readFileSync(requiredArg("packet"), "utf-8")) as Record<string, unknown>;
  const request = JSON.parse(readFileSync(requiredArg("request"), "utf-8")) as Record<string, unknown>;
  const outDir = requiredArg("out-dir");
  const instructionPath = argOf("instruction") ?? DEFAULT_INSTRUCTION;
  const instruction = readFileSync(instructionPath);
  // 席の指示文の sha は**表の固定値**を既定にする(手で打たせない ― 打った値は下の門で固定値と照合する)
  const instructionShaArg = argOf("instruction-sha");
  const instructionSha = instructionShaArg ?? FIXED_INSTRUCTION_SHA256[path.basename(argOf("instruction") ?? DEFAULT_INSTRUCTION)];
  const forbidFile = argOf("forbid-file");
  const forbid = forbidFile === undefined ? undefined : readFileSync(forbidFile, "utf-8").split("\n").map((l) => l.trim()).filter((l) => l.length > 0);
  const runs = Number(argOf("runs") ?? "2");
  const capUsd = readEnvNumber(ENV_NAMES.costCap);
  const warnings: string[] = [];
  const seats = seatConfigs(warnings);
  const integrator = integratorConfig(argOf("integrator-instruction"), warnings);
  const secrets = [readEnv(ENV_NAMES.keys.openai), readEnv(ENV_NAMES.keys.gemini), readEnv(ENV_NAMES.keys.anthropic)];
  for (const line of warnings) console.log(`  注意: ${line}`);

  // 送る前の門 1: 指示文の sha を固定値と照合する(司令塔が 2026-09-30 に 2 本を固定)。
  // 席の指示文は render も照合するが、**整理役の指示文は render を通らない**のでここだけが見る。
  // `--instruction-sha` を渡した場合は固定値と一致することも見る(手で打った値で固定値を上書きさせない)。
  const shaProblems = [
    ...fixedShaProblems(path.basename(instructionPath), instruction),
    ...(integrator === undefined ? [] : fixedShaProblems(path.basename(argOf("integrator-instruction") ?? ""), integrator.instruction)),
  ];
  const fixedSeatSha = FIXED_INSTRUCTION_SHA256[path.basename(instructionPath)];
  if (instructionShaArg !== undefined && fixedSeatSha !== undefined && instructionShaArg !== fixedSeatSha) {
    shaProblems.push(`--instruction-sha が固定値と違う(${instructionShaArg.slice(0, 8)}… / 固定 ${fixedSeatSha.slice(0, 8)}…)`);
  }
  if (shaProblems.length > 0) throw new Error(`指示文の sha が固定値と合わない(${shaProblems.length} 件):\n${shaProblems.map((l) => `  - ${l}`).join("\n")}`);

  // 送る前の門 2(司令塔の F-2・F-3): 指示文の**場所の例**を実物の packet に当てる。
  // **書き方の誤り(欄名・集計の id・表の名前・文法)は止める / 材料の薄さ(表が空・行番号が表の外・値が空)は警告で続ける。**
  // 席は例をまねるので、引けない例を配ると席が引けない数を書いて H-9 で落ちる ― 配った側の誤りを実行の前に落とす。
  const exampleReports = [
    instructionExampleReport(instruction.toString("utf-8"), packet, { label: `席の指示文(${path.basename(instructionPath)})`, minExamples: 3 }),
    ...(integrator === undefined ? [] : [instructionExampleReport(integrator.instruction, packet, { label: "整理役の指示文" })]),
  ];
  for (const report of exampleReports) {
    for (const line of report.warnings) console.log(`  注意: ${line}`);
    const ok = report.checks.filter((c) => c.level === "ok").length;
    if (report.checks.length > 0) console.log(`  指示文の例: ${String(report.checks.length)} 本中 ${String(ok)} 本が引けて値も入っている`);
  }
  const exampleErrors = exampleReports.flatMap((r) => r.errors);
  if (exampleErrors.length > 0) throw new Error(`指示文の例が実物の packet で引けない(${exampleErrors.length} 件)― 席は例をまねるので送らない:\n${exampleErrors.map((l) => `  - ${l}`).join("\n")}`);

  if (flag("dry-run")) {
    // 鍵を使わない下見: 束を組み、概算と上限の判定だけ見せる(送らない)
    const { text, meta } = renderSeatInput({ packet, request, instruction, runId: newRunId(0), ...(instructionSha === undefined ? {} : { instructionSha256: instructionSha }), ...(forbid === undefined ? {} : { forbid }) });
    mkdirSync(outDir, { recursive: true });
    writeFileSync(path.join(outDir, "seat_input.md"), text, "utf-8");
    writeFileSync(path.join(outDir, "seat_input.meta.json"), `${JSON.stringify(meta, null, 1)}\n`, "utf-8");
    console.log(`下見: 束 ${meta.bytes} B・${meta.chars} 字・概算 ${meta.tokenEstimate.value} トークン(${meta.tokenEstimate.method})・sha ${meta.seatInputSha256.slice(0, 12)}…`);
    const estimate = estimateTokensByChars(text).inputTokens;
    let cumulative = 0;
    for (const seat of [...seats, ...(integrator === undefined ? [] : [{ seat: "integrator" as const, ...integrator }])]) {
      if ("holdBack" in seat && seat.holdBack !== undefined) {
        // 送らない席は**見積もりにも入れない**(入れると「2 回でいくら」が送らない分だけ高く見える)
        console.log(`  ${String(seat.seat).padEnd(10)} ${(seat.model ?? "(モデル名が無い)").padEnd(26)} 送っていない(${seat.holdBack.reason})`);
        continue;
      }
      const decision = budgetDecision({ inputTokens: estimate, reserveOutputTokens: seat.reserveOutputTokens, prices: seat.prices, capUsd: capUsd ?? 0, cumulativeCostUsd: cumulative, ...(("inputLimit" in seat && seat.inputLimit !== undefined) ? { inputLimit: seat.inputLimit } : {}) });
      if (decision.ok) cumulative = decision.cumulativeCostUsd;
      console.log(`  ${String(seat.seat).padEnd(10)} ${(seat.model ?? "(モデル名が無い)").padEnd(26)} 見込み ${decision.estimatedCostUsd.toFixed(4)} ドル / 累計 ${cumulative.toFixed(4)} ドル ${decision.ok ? "" : `→ 送らない(${String(decision.reason)})`}`);
    }
    console.log(`  ${String(runs)} 回の見込み 約 ${(cumulative * runs).toFixed(2)} ドル(上限 ${String(capUsd ?? "未設定")} ドル)`);
    return;
  }

  if (capUsd === undefined) throw new Error(`${ENV_NAMES.costCap} が .env に無い ― 上限の無い実行はしない`);
  // **単価が無ければ費用が 0 に見え、上限が効かない** ― 送る前に止める(司令塔の先決め 1 の裏側)
  const noPrice = seatsMissingPrices([...seats, ...(integrator === undefined ? [] : [{ seat: "integrator", prices: integrator.prices }])]);
  if (noPrice.length > 0) throw new Error(`単価が .env に無い席(${noPrice.join(" / ")})― 費用が 0 に見えて上限が効かないので送らない`);
  const runIds: string[] = [];
  const pair: Record<string, unknown>[] = [];
  let cumulative = 0;
  for (let i = 0; i < runs; i += 1) {
    const runId = argOf(`run-id-${i + 1}`) ?? newRunId(i);
    runIds.push(runId);
    const result = await runAll({
      runId, packet, request, instruction, ...(instructionSha === undefined ? {} : { instructionSha256: instructionSha }),
      today: today(), gitHead: gitHead(), seats, ...(integrator === undefined ? {} : { integrator }), capUsd,
      cumulativeCostUsdBefore: cumulative, ...(forbid === undefined ? {} : { forbid }), secrets,
    }, { fetch });
    writeFiles(path.join(outDir, runId), result, secrets);
    printRun(runId, result);
    const summary = result.summary as Record<string, any>;
    cumulative = Number(summary.totals.cumulativeCostUsd);
    pair.push({
      runId, seatsPresent: summary.totals.seatsPresent, seatsSent: summary.totals.seatsSent, seatsHeldBack: summary.totals.seatsHeldBack,
      valueShapeSame: summary.totals.valueShapeSame, capReached: summary.totals.capReached, cumulativeCostUsd: cumulative,
      seats: (summary.seats as Record<string, any>[]).map((s) => ({ seat: s.seat, present: s.present, absentReason: s.absentReason ?? null, items: s.items, checkProblems: s.checkProblems })),
      integration: summary.integration === null ? null : { present: (summary.integration as Record<string, any>).present, clusters: (summary.integration as Record<string, any>).clusters },
    });
    // ここで止める 2 つ(司令塔 2026-09-30): 席が 1 つも立たない / **上限に当たって送らなかった席が出た**。
    // 上限に当たったら残りを無理に埋めない・上限を上げない ― 止めて人間に聞く。
    const stopReason = summary.totals.seatsPresent === 0 ? "席が 1 つも立たなかった"
      : summary.totals.capReached === true ? "費用の上限に当たって送らなかった席が出た(上限を上げない・残りを埋めない)" : undefined;
    if (stopReason !== undefined) {
      writeFileSync(path.join(outDir, "pair_summary.json"), `${JSON.stringify({ runIds, runs: pair, stoppedAt: runId, stopReason }, null, 1)}\n`, "utf-8");
      console.log(`\n${runId}: ${stopReason} ― ここで止める`);
      process.exitCode = 1;
      return;
    }
  }
  writeFileSync(path.join(outDir, "pair_summary.json"), `${JSON.stringify({ runIds, runs: pair }, null, 1)}\n`, "utf-8");
  console.log(`\n書いた: ${outDir}(${runIds.join(" / ")})・累計 ${cumulative.toFixed(4)} ドル`);
}

await main();
