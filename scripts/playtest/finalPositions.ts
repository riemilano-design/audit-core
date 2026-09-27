// STEP ANSWER 追加作業 ANSWER-DIRECT(docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2)。「盤上はこう勝てた」
// (§9.1 の 1.)のための、終局の局面をエンジンで読む CLI。
//
// 使い方(2 通り。どちらか一方):
//   npx tsx scripts/playtest/finalPositions.ts --kifu <固定棋譜 JSON …> --game-nos <n,n,…> [--group <ラベル>|--time-limit-sec <秒>] --out <final_positions.json>
//   npx tsx scripts/playtest/finalPositions.ts --kifu <固定棋譜 JSON …> --patient <patient_report_data.json> [--group <ラベル>|--time-limit-sec <秒>] --out <final_positions.json>
//
// 【入力】`--kifu` に渡した固定棋譜(`*.fixed.json`)のうち、
//   - `--game-nos`(カンマ区切り)を渡したときは、`--kifu` に渡した順とその番号を対応させる(数が食い違えば止める)
//   - `--patient` を渡したときは、その `time.timeUpLosses[*].gameNo` の集合と `games[].no`/`games[].id` から
//     対象の kifuId を決め、`--kifu` の中からその id を持つファイルだけを選ぶ(選ばれなかった --kifu は無視する)
//
// 【この CLI がやること】選んだ局ごとに、固定棋譍を `lib/finalPosition.ts` の `finalPositionOf`(純粋関数)で
// 最後の局面まで進め、その SFEN をエンジン 1 本(素の UsiEngine。read.ts の `readEval` と同じ形)で
// `go nodes <READ_VALUES.nodeLadder の最大値> `(MultiPV 1)読む。
//
// 【group(組のラベル)の決め方(司令塔の仕様追記 1、2026-09-24。実装担当の判断)】「局」の番号が組(3 分の組・
// 10 分の組)をまたいで重なるため、直接 `directAnswers.ts` と同じ考え方でラベルを持たせる。**この CLI は
// 1 回の実行で 1 つの組しか扱わない**ため(`--patient` は 1 本、`--game-nos` も 1 組ぶん)、`--group`/
// `--time-limit-sec` は 1 個だけ渡す(`directAnswers.ts` のような「ペアの数だけ渡す」繰り返しではない):
// - `--group <ラベル>` を渡せば、そのままラベルにする。
// - `--time-limit-sec <秒>` を渡せば、`report-pdf/check_answer.py` の `tag_of_time_limit_sec` と同じ対応
//   (180 → 3 分の組、600 → 10 分の組)でラベルにする。
// - どちらも渡さなければ、`"1"`(1 回の実行に 1 つの組しか無いため、複数回の実行にまたがる「順の番号」は
//   この CLI 単体では決められない。`directAnswers.ts` の「組の順の番号」に相当する既定値として固定した)。
//
// 【このファイルが絶対にやらないこと】将棋の判断・評価・閾値・文言。新しい値を置くこと(ノード数は
// READ_VALUES.nodeLadder の最大値をそのまま使う。180/600 は check_answer.py と同じ値の再利用)。
// 名前・/Users/ を含む絶対パスを出力へ書くこと。

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { resolveEnginePath } from "../../apps/server/src/engine/enginePath.js";
import { UsiEngine } from "../../apps/server/src/engine/usiEngine.js";
import { parseInfoLine, type UsiScore } from "../../apps/server/src/engine/usiInfoParser.js";
import { finalPositionOf, type FinalPositionKifu } from "./lib/finalPosition.js";
import { readGitState } from "./lib/gitState.js";
import type { FixedKifuEnding } from "./lib/kifuImport.js";
import { READ_VALUES } from "./lib/read.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE = [
  "使い方:",
  "  npx tsx scripts/playtest/finalPositions.ts --kifu <固定棋譜 JSON …> --game-nos <n,n,…> --out <final_positions.json>",
  "  npx tsx scripts/playtest/finalPositions.ts --kifu <固定棋譜 JSON …> --patient <patient_report_data.json> --out <final_positions.json>",
].join("\n");

// read.ts の DEFAULT_THREADS・READ_TIMEOUT_MS と同じ値(既存の既定。新しい値は置かない)。
const DEFAULT_THREADS = 1;
const NODES_TIMEOUT_MS = 60_000;
const NODES = Math.max(...READ_VALUES.nodeLadder);

function collectUntilFlag(args: readonly string[], startIndex: number): string[] {
  const values: string[] = [];
  let i = startIndex;
  while (i < args.length && !args[i]!.startsWith("--")) {
    values.push(args[i]!);
    i++;
  }
  return values;
}

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

/** `report-pdf/check_answer.py` の `tag_of_time_limit_sec` と同じ対応(司令塔の仕様追記 1)。 */
function groupLabelOfTimeLimitSec(sec: number): string {
  if (sec === 180) return "3 分";
  if (sec === 600) return "10 分";
  throw new Error(`--time-limit-sec は 180 か 600 です(${sec})`);
}

/** この CLI は 1 回の実行で 1 つの組しか扱わないので、`--group`/`--time-limit-sec` は 1 個だけ(ファイル冒頭コメント参照)。 */
function groupLabelOf(args: readonly string[]): string {
  const groupArg = argValue(args, "--group");
  const timeLimitArg = argValue(args, "--time-limit-sec");
  if (groupArg !== undefined && timeLimitArg !== undefined) {
    throw new Error("--group と --time-limit-sec は同時に指定できません");
  }
  if (groupArg !== undefined) return groupArg;
  if (timeLimitArg !== undefined) return groupLabelOfTimeLimitSec(Number(timeLimitArg));
  return "1";
}

interface FixedKifuFile extends FinalPositionKifu {
  id: string;
  /** STEP ENDING_CLOCK §4 の 15(計画の直し、7a40122)。`via`(印)を運ぶために読むだけ。判定はしない。 */
  ending?: FixedKifuEnding | null;
}

interface PatientGameLike {
  no: number;
  id: string;
}

interface PatientLike {
  games: PatientGameLike[];
  time: { timeUpLosses: { gameNo: number }[] | null };
}

/** `--kifu` に渡したファイルから、対象(kifuId・gameNo)を選ぶ。 */
function selectTargets(kifuPaths: readonly string[], gameNosArg: string | undefined, patientArg: string | undefined): { path: string; kifu: FixedKifuFile; gameNo: number }[] {
  const loaded = kifuPaths.map((p) => ({ path: path.resolve(p), kifu: JSON.parse(readFileSync(path.resolve(p), "utf-8")) as FixedKifuFile }));

  if (gameNosArg !== undefined) {
    const gameNos = gameNosArg.split(",").map((s) => Number(s.trim()));
    if (gameNos.length !== loaded.length) {
      throw new Error(`--game-nos(${gameNos.length} 個)と --kifu(${loaded.length} 個)の数が対応していません`);
    }
    if (gameNos.some((n) => !Number.isInteger(n) || n <= 0)) {
      throw new Error(`--game-nos は正の整数のカンマ区切りです(${gameNosArg})`);
    }
    return loaded.map((entry, index) => ({ ...entry, gameNo: gameNos[index]! }));
  }

  if (patientArg !== undefined) {
    const patient = JSON.parse(readFileSync(path.resolve(patientArg), "utf-8")) as PatientLike;
    const targetGameNos = new Set((patient.time.timeUpLosses ?? []).map((loss) => loss.gameNo));
    const gameNoById = new Map(patient.games.map((g) => [g.id, g.no]));
    const targets: { path: string; kifu: FixedKifuFile; gameNo: number }[] = [];
    for (const entry of loaded) {
      const gameNo = gameNoById.get(entry.kifu.id);
      if (gameNo === undefined) continue; // --patient の games に無い局(この組の対象外)。無視する
      if (!targetGameNos.has(gameNo)) continue; // 時間切れ負けではない局
      targets.push({ ...entry, gameNo });
    }
    return targets;
  }

  throw new Error("--game-nos か --patient のどちらかが要ります");
}

/** `sfen` を `nodes` ノードだけ読む(MultiPV 1)。read.ts の `readEval` と同じ形(重複だが、CLI はそれぞれ
 * 自分の分だけ持つ ― whatif.ts の makeSideReader・read.ts の readEval と同じ流儀)。 */
async function readTop1(engine: UsiEngine, sfen: string, nodes: number): Promise<{ scoreCp: number | null; mate: number | null; pv: string[] } | null> {
  try {
    engine.setMultiPv(1);
    engine.position(sfen);
    engine.send(`go nodes ${nodes}`);
    const { collected } = await engine.waitForLine((line) => line.startsWith("bestmove"), { timeoutMs: NODES_TIMEOUT_MS });

    let best: { score: UsiScore | undefined; pv: string[] } | undefined;
    for (const raw of collected) {
      const parsed = parseInfoLine(raw);
      if (parsed !== undefined && parsed.multipv === 1) best = { score: parsed.score, pv: parsed.pv };
    }
    const bestmoveMatch = collected.find((line) => line.startsWith("bestmove"))?.match(/^bestmove (\S+)/);
    const move = best?.pv[0] ?? bestmoveMatch?.[1];
    if (move === undefined) return null;
    return {
      scoreCp: best?.score?.type === "cp" ? best.score.value : null,
      mate: best?.score?.type === "mate" ? best.score.value : null,
      pv: best !== undefined && best.pv.length > 0 ? best.pv : [move],
    };
  } catch {
    return null;
  }
}

async function main(): Promise<number> {
  const args = process.argv.slice(2);
  const kifuIndex = args.indexOf("--kifu");
  if (kifuIndex === -1) {
    console.error(USAGE);
    return 1;
  }
  const kifuPaths = collectUntilFlag(args, kifuIndex + 1);
  const gameNosArg = argValue(args, "--game-nos");
  const patientArg = argValue(args, "--patient");
  const outArg = argValue(args, "--out");
  if (kifuPaths.length === 0 || outArg === undefined || (gameNosArg === undefined) === (patientArg === undefined)) {
    // --game-nos と --patient はどちらか一方だけ(両方無し・両方ありはどちらも使い方の誤り)
    console.error(USAGE);
    return 1;
  }

  const targets = selectTargets(kifuPaths, gameNosArg, patientArg);
  if (targets.length === 0) {
    console.error("対象の局が 0 件です(--kifu と --game-nos / --patient を確かめてください)");
    return 1;
  }
  const group = groupLabelOf(args);

  const enginePath = resolveEnginePath();
  const engine = new UsiEngine(enginePath);
  engine.start();
  try {
    await engine.usiHandshake();
    await engine.isReady();
    engine.setThreads(DEFAULT_THREADS);

    const startedAt = new Date().toISOString();
    const gitState = readGitState(REPO_ROOT);

    const entries: {
      group: string;
      kifuId: string;
      gameNo: number;
      moves: number;
      sfen: string;
      mirrored: boolean;
      top1Move: string | null;
      pv: string[];
      scoreCp: number | null;
      mate: number | null;
      /** STEP ENDING_CLOCK §4 の 15(計画の直し、7a40122)。どう選ばれたかを運ぶ印(印を運ぶだけ・ここで判定しない)。
       * `lib/reportData.ts` の `buildTimeUpLosses` と同じ対応(語 `切れ負け` = "word"・それ以外(`投了` の時計一致) = "clock")。 */
      via: "word" | "clock";
    }[] = [];

    for (const target of targets) {
      const final = finalPositionOf(target.kifu);
      const mirrored = target.kifu.mirrored === true;
      const top1 = await readTop1(engine, final.sfen, NODES);
      const via: "word" | "clock" = target.kifu.ending?.kind === "timeUp" ? "word" : "clock";
      entries.push({
        group,
        kifuId: target.kifu.id,
        gameNo: target.gameNo,
        moves: final.moves,
        sfen: final.sfen,
        mirrored,
        top1Move: top1?.pv[0] ?? null,
        pv: top1?.pv ?? [],
        scoreCp: top1?.scoreCp ?? null,
        mate: top1?.mate ?? null,
        via,
      });
    }

    const out = {
      kind: "final_positions",
      startedAt,
      gitHead: gitState.gitHead,
      dirty: gitState.dirty,
      nodes: NODES,
      threads: DEFAULT_THREADS,
      entries,
    };

    const outPath = path.resolve(outArg);
    mkdirSync(path.dirname(outPath), { recursive: true });
    writeFileSync(outPath, `${JSON.stringify(out, null, 2)}\n`, "utf-8");
    console.log(`書き込み: ${outPath}(${entries.length} 局)`);
    return 0;
  } finally {
    engine.quit();
    engine.close();
  }
}

main().then(
  (code) => process.exit(code),
  (err: unknown) => {
    console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
    process.exit(1);
  },
);
