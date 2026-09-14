// STEP U6-T((あ′)。docs/STEP_U6-T_PLAN_2026-09-13.md)の CLI。
// 回帰の局面に MultiPV 1 と 5 の探索を当て、読み筋の本数・長さ・標識の分布を JSONL に書く。
//
// 使い方(エンジンを使う。**回す前に宣言すること**):
//   npx tsx scripts/playtest/multipv-survey.ts --stage A --records <out/u6l のディレクトリ> --out <file.jsonl>
//   npx tsx scripts/playtest/multipv-survey.ts --stage B --records <…> --out <…>   (規則 12 番。枠を取ってから)
// エンジンを使わずに入力だけ確かめる:
//   npx tsx scripts/playtest/multipv-survey.ts --list-roots --records <…>
//
// 【この CLI は薄くしてある】
// 走らせる部品・門番・集計・校正はすべて lib/multiPvSurvey.ts にあり、そちらに試験がある。
// ここでやるのは、記録を読む・エンジンを起動する・行を書く、だけである。
//
// 【本番の挙動を変えない。apps/ のファイルを 1 行も変えない】(司令塔の決定。計画 §8)

import { appendFileSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { loadavg } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { resolveEnginePath } from "../../apps/server/src/engine/enginePath.js";
import { PrioritizedEngine } from "../../apps/server/src/engine/prioritizedEngine.js";
import { UsiEngine } from "../../apps/server/src/engine/usiEngine.js";
import { CALIBRATION_BASELINE, CALIBRATION_BOUND_RATE_TOLERANCE } from "./lib/calibrationBaseline.js";
import { buildMetaLine } from "./lib/recorder.js";
import {
  buildSurveyReport,
  calibrationGate,
  checkCalibration,
  conditionKey,
  controlRowsOf,
  dedupeRoots,
  runSurvey,
  type CalibrationExpectation,
  type SurveyCondition,
} from "./lib/multiPvSurvey.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(__dirname, "..", "..");

// 判断的知識の値。**すべて計画 §3・§9.1 で承認された値**であり、ハーネスの引数である(本番の閾値ではない)。
const REPORT_PARAMS = {
  d1MinLength: 3, // D-1: 標識付きなのに usablePlies が 3 以上の本を数える
  tolerance: 0.05, // D-2: 落ちる標識なしの本が 5% を超えたら値を確定させない
  // D-3 は判定を出さない(分布と 0 本・1 本の局面の数だけ。2026-09-14 の司令塔の決定。計画 §3 D-3)
  lossThresholds: [2, 3, 4, 5, 6], // S-4: 控えの候補
} as const;

// 段 A の校正に使う既知の値と幅は lib/calibrationBaseline.ts にある(U6-T2)。**ここで書き換えない**
// (値は凍結してあり、記録から数え直した値との一致を lib/calibrationBaseline.test.ts が見る)。

const STAGES = {
  A: {
    conditions: [
      { multiPv: 1, mode: "nodes", nodes: 4_000_000 },
      { multiPv: 5, mode: "nodes", nodes: 4_000_000 },
    ] as const satisfies readonly [SurveyCondition, SurveyCondition],
    threads: 1, // 回帰と同じ(replay.ts:188)
  },
  B: {
    conditions: [
      { multiPv: 1, mode: "movetime", movetimeMs: 2000 },
      { multiPv: 5, mode: "movetime", movetimeMs: 2000 },
    ] as const satisfies readonly [SurveyCondition, SurveyCondition],
    threads: null, // 本番と同じく設定しない(計画 §1.2)。既定値がいくつかは推測で書かない
  },
} as const;

function argValue(args: string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

/** 記録のディレクトリから ready 行の局面を読む。ファイル名の順(決定的)。 */
function readRecordRows(dir: string): Array<{ kifuId: string; ply: number; sfen: string }> {
  const rows: Array<{ kifuId: string; ply: number; sfen: string }> = [];
  for (const file of readdirSync(dir).filter((name) => name.endsWith(".jsonl")).sort()) {
    let kifuId = file.replace(/\.jsonl$/, "");
    for (const line of readFileSync(path.join(dir, file), "utf-8").split("\n")) {
      if (!line.trim()) continue;
      const parsed = JSON.parse(line) as { kind?: string; kifuId?: string; phase?: string; ply?: number; sfen?: string };
      if (parsed.kind === "meta" && typeof parsed.kifuId === "string") kifuId = parsed.kifuId;
      if (parsed.kind === "record" && parsed.phase === "ready" && typeof parsed.sfen === "string") {
        rows.push({ kifuId, ply: parsed.ply ?? -1, sfen: parsed.sfen });
      }
    }
  }
  return rows;
}

/**
 * エンジンの本数を数える。`ps -A -o pid=,comm=` を取り、**一致はシェルの外(ここ)で、末尾一致で行う**
 * (文字列を grep の引数に入れると自分を数える / macOS の comm はフルパスで -x が一致しない)。
 */
function countEngineProcesses(enginePath: string): number {
  const name = path.basename(enginePath);
  const out = execFileSync("ps", ["-A", "-o", "pid=,comm="]).toString();
  return out
    .split("\n")
    .map((line) => line.trim().split(/\s+/).slice(1).join(" "))
    .filter((command) => command === name || command.endsWith(`/${name}`)).length;
}

async function main(): Promise<number> {
  const args = process.argv.slice(2);
  const recordsDir = argValue(args, "--records");
  if (!recordsDir) {
    console.error("--records <記録のディレクトリ> を指定してください(既定値は置かない)");
    return 1;
  }
  const sourceRows = readRecordRows(recordsDir);
  const roots = dedupeRoots(sourceRows);

  if (args.includes("--list-roots")) {
    console.log(`ready 行 ${sourceRows.length} / 畳んだ局面 ${roots.length}`);
    for (const [index, root] of roots.entries()) {
      if (root.origins.length > 1) console.log(`  局面 ${index}: ${root.origins.length} 回(${root.origins.map((o) => `${o.kifuId}#${o.ply}`).join(", ")})`);
    }
    return 0;
  }

  const stageName = argValue(args, "--stage");
  if (stageName !== "A" && stageName !== "B") {
    console.error("--stage A または --stage B を指定してください");
    return 1;
  }
  const outPath = argValue(args, "--out");
  if (!outPath) {
    console.error("--out <file.jsonl> を指定してください");
    return 1;
  }
  const stage = STAGES[stageName];

  // 段 A は、校正の値の出どころが書かれていなければ始めない。**エンジンを起動する前・出力を作る前に止める。**
  let calibrationExpectation: CalibrationExpectation | null = null;
  if (stageName === "A") {
    const gate = calibrationGate(CALIBRATION_BASELINE, CALIBRATION_BOUND_RATE_TOLERANCE);
    if (gate.kind === "missing_source") {
      console.error(gate.reason);
      return 3;
    }
    calibrationExpectation = gate.expectation;
  }

  const enginePath = resolveEnginePath();
  const startedAt = new Date().toISOString();
  const engineProcessesBeforeStart = countEngineProcesses(enginePath);

  // 段 B は時間に依存する計測(規則 12 番)。他のエンジンが 1 本でも走っていたら始めない。
  if (stageName === "B" && engineProcessesBeforeStart !== 0) {
    console.error(`エンジンが ${engineProcessesBeforeStart} 本走っています。段 B は他のエンジンを止めてから行います(規則 12 番)。`);
    return 2;
  }

  writeFileSync(outPath, "");
  const appendLine = (line: string): void => appendFileSync(outPath, `${line}\n`);
  // STEP U6-R: git の状態は渡さない。buildMetaLine が repoRoot から自分で読む(値を偽れないように)。
  // **この後で文字列を書き換えない**(U6-R 計画 §7 の Y10 と同じ限界を持つため)。
  appendLine(
    buildMetaLine({
      kifuId: `multipv-survey-${stageName}`,
      startedAt,
      repoRoot: REPO_ROOT,
      enginePath,
      extra: {
        mode: "multipv-survey",
        stage: stageName,
        conditions: stage.conditions.map(conditionKey),
        threads: stage.threads === null ? "not_set" : stage.threads,
        recordsDir,
        sourceRows: sourceRows.length,
        roots: roots.length,
        engineProcessesBeforeStart,
        loadavgAtStart: loadavg(),
      },
    }),
  );

  const rawEngine = new UsiEngine(enginePath);
  rawEngine.start();
  try {
    await rawEngine.usiHandshake();
    await rawEngine.isReady();
    if (stage.threads !== null) rawEngine.setThreads(stage.threads);
    const engine = new PrioritizedEngine(rawEngine);

    const { rows, stoppedAfterFailure } = await runSurvey({
      roots,
      conditions: stage.conditions,
      // 条件ごとに別のハンドル(runSurvey が条件ごとに 1 回だけ呼ぶ)
      engineFor: () => engine.asLowPriority(),
      onRow: (row) => appendLine(JSON.stringify(row)),
      clock: () => Date.now(),
    });

    const report = buildSurveyReport(rows, REPORT_PARAMS);
    // 対照(MultiPV 1)を選ぶのは lib の controlRowsOf(条件の並びに依存しない。試験は lib 側)。
    // **ここで行を選び直さない**(multiPvSurvey.test.ts の照合が、この 1 行を見張る)。
    const calibration =
      calibrationExpectation !== null
        ? checkCalibration(controlRowsOf(rows, stage.conditions), REPORT_PARAMS.tolerance, calibrationExpectation)
        : null;
    appendLine(
      JSON.stringify({ kind: "survey_summary", stoppedAfterFailure, loadavgAtEnd: loadavg(), report, calibration }),
    );

    console.log(`段 ${stageName}: 探索 ${rows.length} 本 / 失敗で止まった: ${stoppedAfterFailure}`);
    for (const r of report) {
      console.log(`  ${r.condition}: 失敗 ${r.summary.failed} / 本数の不一致 ${r.summary.requestedMismatch} / D-1 ${r.d1BoundedLongLines} / D-2 ${JSON.stringify(r.d2)}`);
      console.log(`    D-3 ${JSON.stringify(r.d3)}`);
    }
    if (calibration) console.log(`  校正(MultiPV 1 の対照): ${calibration.passed ? "合格" : "**不合格** ― 段 A の結果を使わずに止めて報告する"}`);
    return stoppedAfterFailure ? 1 : 0;
  } finally {
    rawEngine.quit();
    rawEngine.close();
  }
}

main().then(
  (code) => process.exit(code),
  (err: unknown) => {
    console.error(err);
    process.exit(1);
  },
);
