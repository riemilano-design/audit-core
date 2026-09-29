// 3 席 LLM API の束 R1 ― CLI: packet + request + 指示文 → seat_input.md + seat_input.meta.json
// (計画 docs/STEP_LLM_SEATS_R1_RENDER_2026-09-30.md。lib は lib/seatInput.ts)。
//
// 【顧客の PDF にどう出るか】今は何も変わらない。3 席の LLM に渡す入力を作るだけで、LLM は呼ばない(鍵はまだ無い)。
// 【使い方】
//   npx tsx scripts/playtest/seatInput.ts --packet <packet.json> --request <observation-request.json> \
//     --instruction docs/LLM_SEATS_INSTRUCTION_v1_2026-09-30.md --run-id <半角英数 8 桁以上> --out-dir <dir> \
//     [--forbid-file <1 行 1 語。値に混ざれば止める。語はログに出さない>] [--instruction-sha <sha256>]
// 【出口】止まる条件(lib)に当たれば書かずに終了コード 1。書いた後、ファイルから読み直して抽出の証拠(数の包含)を
//   もう一度見る(render の中の検査と別の口)。合わなければ終了コード 1。
// 【鍵】この道具は API の鍵を読まない・書かない。
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { SeatInputError, dataLinesOf, numberInclusionProblems, renderSeatInput } from "./lib/seatInput.js";

function argOf(name: string): string | undefined {
  const index = process.argv.indexOf(`--${name}`);
  if (index < 0) return undefined;
  const value = process.argv[index + 1];
  return value === undefined || value.startsWith("--") ? undefined : value;
}
function requiredArg(name: string): string {
  const value = argOf(name);
  if (value === undefined) throw new Error(`--${name} が要る`);
  return value;
}

function main(): void {
  const packet = JSON.parse(readFileSync(requiredArg("packet"), "utf-8")) as unknown;
  const request = JSON.parse(readFileSync(requiredArg("request"), "utf-8")) as unknown;
  const instruction = readFileSync(requiredArg("instruction"));
  const runId = requiredArg("run-id");
  const outDir = requiredArg("out-dir");
  const forbidFile = argOf("forbid-file");
  const forbid = forbidFile === undefined ? [] : readFileSync(forbidFile, "utf-8").split("\n").map((w) => w.trim()).filter((w) => w.length > 0);
  const instructionSha256 = argOf("instruction-sha");

  let rendered: ReturnType<typeof renderSeatInput>;
  try {
    rendered = renderSeatInput({ packet, request, instruction, runId, forbid, ...(instructionSha256 === undefined ? {} : { instructionSha256 }) });
  } catch (err) {
    if (err instanceof SeatInputError) {
      console.log(err.message);
      process.exitCode = 1;
      return;
    }
    throw err;
  }
  mkdirSync(outDir, { recursive: true });
  const textPath = path.join(outDir, "seat_input.md");
  const metaPath = path.join(outDir, "seat_input.meta.json");
  writeFileSync(textPath, rendered.text, "utf-8");
  writeFileSync(metaPath, `${JSON.stringify(rendered.meta, null, 1)}\n`, "utf-8");

  // 書いたファイルから読み直して、抽出の証拠をもう一度(別の口)
  const written = readFileSync(textPath, "utf-8");
  const problems = numberInclusionProblems(dataLinesOf(written, instruction.toString("utf-8")), packet, request);
  const { meta } = rendered;
  console.log(`書いた: ${textPath}`);
  console.log(`  sha256 ${meta.seatInputSha256}  ${meta.bytes} バイト  ${meta.chars} 字  概算 ${meta.tokenEstimate.value} トークン(${meta.tokenEstimate.method})`);
  console.log(`  packetId ${meta.packetId}  符号 ${meta.customerRef}  持ち時間 ${meta.timeLimitSec} 秒  ${meta.games} 局  合言葉 ${meta.passphrase}`);
  console.log("  節:");
  for (const s of meta.sections) console.log(`    ${s.section.padEnd(4)} ${s.title.slice(0, 24).padEnd(24)} ${String(s.rows).padStart(5)} 行  最後 ${s.lastKey}  (${s.packetPath})`);
  if (problems.length > 0) {
    console.log(`\n抽出の証拠(ファイルから読み直し)に問題 ${problems.length} 件:`);
    for (const p of problems) console.log(`  - ${p}`);
    process.exitCode = 1;
    return;
  }
  console.log("\n問題なし(契約・線の組・指示文の sha・識別子・抽出の証拠を 2 つの口で)");
}

main();
