// STEP BASE(docs/STEP_BASE_PLAN_2026-09-21.md §1・§2)。1 人を person、その人を除いた 1 人以上を pool にして、
// pool を合わせた枠ごとの崩れ率を基準値にし、person がその基準値から外れている枠を候補(下見)として出す道具。
//
// 使い方: npx tsx scripts/playtest/baselineTable.ts --person <pN> --material <段 2 の記録 …>
//           --pool <pM>=<記録 …> [--pool <pK>=<…> …] --out <baseline.json>
//
// - `--material` は person の段 2 の記録(gate.ts の `--material` と同じ形式の JSONL)。
// - `--pool` は 1 つの pool の人を表す。最初のトークンは `<ラベル>=<1 本目の記録のパス>`(空でもよい)、続くトークンは同じ pool の記録を追加する。
//   複数の pool の人を集計に入れるときは `--pool` を人の数だけ繰り返す。
// - 標準出力に Markdown の表。`--out` に契約の無い JSON(計画 §2 の出力そのまま。名前・手・局面・SFEN は書かない)。
// - 止める(exit 1): `--person`・`--pool` のラベルが p1・p2 の形でない・`--pool` のラベルが `--person` と同じ・
//   `--pool` 同士で同じラベル・記録が無い・referenceNodes がそろわない・error 行がある・同じ記録が person・pool の間で重なる。
//
// - `--whatif-material`・`--whatif-pool`(STEP WHATIF 作業 3。docs/STEP_WHATIF_PLAN_2026-09-22.md §8.1-2。任意、渡すなら両方):
//   `whatif.ts` の出力(jsonl)を読み、5 つの率(第 1 候補と同じ・上位 5 つ・fork・narrowHeld・chanceHeld。分母は
//   positionsRead の合計)+ 攻めの側に合法手が無かった場面の率(分母は scenesRead の合計)の 6 行を Markdown・JSON に足す。
//   **candidate/lower の判定は付けない**(pool 合計の率と pool の人ごとの最小〜最大を添えるだけ)。渡さなければ出力は
//   1 バイトも変わらない。止める(exit 1): 片方だけ渡した・記録の最後の行が summary でない・values が記録の間でそろわない・
//   `--whatif-pool` のラベルの集合が `--pool` のラベルの集合と一致しない・同じ記録が重なる。
//
// 【このファイルがやること】入力を読み、lib/diagnosisMoment.ts の allPairsOf(軽い値)で組を作り、lib/baselineTable.ts の
// 集計(baselineReportOf)・入力の確かめ(baselineInputProblems)・Markdown(renderBaselineMarkdown)をつなぐ。
// whatif の入力・集計・Markdown は lib/whatifBaseline.ts につなぐ(閾値・判定語はどちらのファイルにも新しく置かない)。
// 【このファイルが絶対にやらないこと】エンジンを回すこと。records/ へ書くこと。閾値・判定語を新しく置くこと

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { MetaLine, RecordLine } from "./invariants/types.js";
import {
  baselineInputProblems,
  baselineReportOf,
  renderBaselineMarkdown,
  type BaselineGame,
  type BaselineInputEntry,
  type BaselineInputGroup,
  type BaselinePerson,
} from "./lib/baselineTable.js";
import { diagnoseRecords, DRAFT_RULE_1, fullMovesOf, readEvaluations } from "./lib/failureEvent.js";
import { recordSha256 } from "./lib/failureEventSchema.js";
import { allPairsOf } from "./lib/diagnosisMoment.js";
import { screenOfRecord } from "./lib/screenDiagnosis.js";
import { initialSfenOf } from "./lib/sideAlignment.js";
import {
  renderWhatifRateMarkdown,
  whatifInputProblems,
  whatifRateRowsOf,
  type WhatifFileEntry,
  type WhatifInputGroup,
  type WhatifRateRow,
  type WhatifSummaryCounts,
} from "./lib/whatifBaseline.js";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE =
  "使い方: npx tsx scripts/playtest/baselineTable.ts --person <pN> --material <a.jsonl …> --pool <pM>=<a.jsonl …> [--pool <pK>=<…> …] --out <baseline.json>\n" +
  "  [--whatif-material <whatif.jsonl …>] [--whatif-pool <pM>=<whatif.jsonl …> …](計画 §8.1-2。どちらも任意だが、渡すなら両方)";

class BaselineInputError extends Error {
  constructor(readonly problems: readonly string[]) {
    super(`baselineTable.ts の入力を受け付けない: ${problems.join(" / ")}`);
    this.name = "BaselineInputError";
  }
}

interface PoolSpec {
  label: string;
  files: string[];
}

interface Args {
  person: string;
  material: string[];
  pools: PoolSpec[];
  out: string;
  /** 計画 §8.1-2。渡さなければ 1 バイトも出力を変えない(whatif の行を出さない)。 */
  whatifMaterial: string[];
  whatifPools: PoolSpec[];
}

function parseArgs(argv: readonly string[]): Args {
  let person: string | undefined;
  let out: string | undefined;
  const material: string[] = [];
  const pools: PoolSpec[] = [];
  const whatifMaterial: string[] = [];
  const whatifPools: PoolSpec[] = [];
  let index = 0;
  while (index < argv.length) {
    const flag = argv[index]!;
    if (flag === "--person" || flag === "--out") {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new BaselineInputError([`${flag} に値が無い`]);
      if (flag === "--person") {
        if (person !== undefined) throw new BaselineInputError(["--person が 2 回ある"]);
        person = value;
      } else {
        if (out !== undefined) throw new BaselineInputError(["--out が 2 回ある"]);
        out = value;
      }
      index += 2;
    } else if (flag === "--material" || flag === "--whatif-material") {
      const list = flag === "--material" ? material : whatifMaterial;
      index += 1;
      while (index < argv.length && !argv[index]!.startsWith("--")) {
        list.push(argv[index]!);
        index += 1;
      }
    } else if (flag === "--pool" || flag === "--whatif-pool") {
      const list = flag === "--pool" ? pools : whatifPools;
      index += 1;
      const first = argv[index];
      if (first === undefined || first.startsWith("--")) throw new BaselineInputError([`${flag} に値が無い`]);
      const eq = first.indexOf("=");
      if (eq < 0) throw new BaselineInputError([`${flag} の値は <ラベル>=<記録> の形: ${first}`]);
      const label = first.slice(0, eq);
      const firstFile = first.slice(eq + 1);
      const files = firstFile.length > 0 ? [firstFile] : [];
      index += 1;
      while (index < argv.length && !argv[index]!.startsWith("--")) {
        files.push(argv[index]!);
        index += 1;
      }
      list.push({ label, files });
    } else {
      throw new BaselineInputError([`知らない引数: ${flag}`]);
    }
  }
  const missing = [...(person === undefined ? ["--person"] : []), ...(out === undefined ? ["--out"] : [])];
  if (missing.length > 0) throw new BaselineInputError([`${missing.join("・")} が無い`]);
  if (material.length === 0) throw new BaselineInputError(["--material の記録が無い"]);
  if (pools.length === 0) throw new BaselineInputError(["--pool が無い"]);
  if ((whatifMaterial.length > 0) !== (whatifPools.length > 0)) {
    throw new BaselineInputError(["--whatif-material と --whatif-pool は渡すなら両方(片方だけでは whatif の行を組み立てられない)"]);
  }
  return { person: person!, material, pools, out: out!, whatifMaterial, whatifPools };
}

interface ReadInput {
  entry: BaselineInputEntry;
  meta: MetaLine | undefined;
  records: RecordLine[];
}

function readInput(filePath: string): ReadInput {
  const absolute = path.resolve(filePath);
  const bytes = readFileSync(absolute);
  const lines = bytes
    .toString("utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as { kind: string });
  const meta = lines.find((line) => line.kind === "meta") as MetaLine | undefined;
  const records = lines.filter((line): line is RecordLine => line.kind === "record");
  const sha256 = recordSha256(bytes);
  const relative = path.relative(REPO_ROOT, absolute);
  return {
    entry: { name: filePath, path: relative, kifuId: meta?.kifuId ?? path.basename(filePath), sha256, meta, errorLines: lines.filter((line) => line.kind === "error").length },
    meta,
    records,
  };
}

interface RawWhatifSummary {
  positionsRead: number;
  matchesTop1: number;
  withinMultiPv: number;
  scenes: { fork: number[]; narrowHeld: number[]; chanceHeld: number[] };
  sceneReads: { attackNoLegalMoveCount: number; scenesRead: number };
}

/** whatif.ts の出力(jsonl)を読む(計画 §8.1-2)。段 2 の記録(readInput)とは形が違うので別に読む。 */
function readWhatifInput(filePath: string): WhatifFileEntry {
  const absolute = path.resolve(filePath);
  const bytes = readFileSync(absolute);
  const lines = bytes
    .toString("utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as { kind: string });
  const meta = lines.find((line) => line.kind === "meta") as ({ kifuId: string; values: unknown } & Record<string, unknown>) | undefined;
  const summaryLine = lines.filter((line) => line.kind === "summary").at(-1) as ({ kind: "summary" } & RawWhatifSummary) | undefined;
  const summary: WhatifSummaryCounts | undefined =
    summaryLine === undefined
      ? undefined
      : {
          positionsRead: summaryLine.positionsRead,
          matchesTop1: summaryLine.matchesTop1,
          withinMultiPv: summaryLine.withinMultiPv,
          forkCount: summaryLine.scenes.fork.length,
          narrowHeldCount: summaryLine.scenes.narrowHeld.length,
          chanceHeldCount: summaryLine.scenes.chanceHeld.length,
          scenesRead: summaryLine.sceneReads.scenesRead,
          attackNoLegalMoveCount: summaryLine.sceneReads.attackNoLegalMoveCount,
        };
  const sha256 = recordSha256(bytes);
  const relative = path.relative(REPO_ROOT, absolute);
  return { name: filePath, path: relative, kifuId: meta?.kifuId ?? path.basename(filePath), sha256, values: meta?.values, summary };
}

/** 段 2 の記録 1 本から 1 局ぶんの組(軽い値)と、軸 B が読む総手数を作る(gate.ts の pairsGameOf と同じ組の作り方)。 */
function baselineGameOf(input: ReadInput): BaselineGame {
  const kifuId = input.entry.kifuId;
  screenOfRecord(kifuId, input.meta, input.records);
  const initialSfen = initialSfenOf(input.meta);
  const { events } = diagnoseRecords(kifuId, input.records, DRAFT_RULE_1, initialSfen);
  const allPairs = allPairsOf(kifuId, input.records, DRAFT_RULE_1, initialSfen, events, { source: "light" });
  const totalMoves = fullMovesOf(readEvaluations(input.records)).length;
  return { kifuId, pairs: allPairs.pairs, movesMissing: allPairs.movesMissing, rowStandings: allPairs.rowStandings, totalMoves: totalMoves > 0 ? totalMoves : null };
}

async function main(): Promise<void> {
  const argv = process.argv.slice(2);
  if (argv.length === 0) {
    console.error(USAGE);
    return;
  }
  const args = parseArgs(argv);
  const materialInputs = args.material.map(readInput);
  const poolInputs = args.pools.map((pool) => ({ label: pool.label, inputs: pool.files.map(readInput) }));

  const personGroup: BaselineInputGroup = { label: args.person, entries: materialInputs.map((input) => input.entry) };
  const poolGroups: BaselineInputGroup[] = poolInputs.map((pool) => ({ label: pool.label, entries: pool.inputs.map((input) => input.entry) }));
  const { problems } = baselineInputProblems(personGroup, poolGroups);
  if (problems.length > 0) throw new BaselineInputError(problems);

  const person: BaselinePerson = { label: args.person, games: materialInputs.map(baselineGameOf) };
  const pool: BaselinePerson[] = poolInputs.map((poolInput) => ({ label: poolInput.label, games: poolInput.inputs.map(baselineGameOf) }));

  const report = baselineReportOf(person, pool);
  const markdownLines = renderBaselineMarkdown(report);

  // whatif の行(計画 §8.1-2)。--whatif-material/--whatif-pool を渡さなければ、ここには一切入らない
  // (出力は 1 バイトも変わらない ― parseArgs が「渡すなら両方」を強制しているので、この分岐は両方揃っているときだけ真になる)。
  let whatif: { material: { label: string; games: number }; pool: Array<{ label: string; games: number }>; rows: WhatifRateRow[] } | undefined;
  if (args.whatifMaterial.length > 0 && args.whatifPools.length > 0) {
    const whatifMaterialEntries = args.whatifMaterial.map(readWhatifInput);
    const whatifPoolGroups: WhatifInputGroup[] = args.whatifPools.map((pool) => ({ label: pool.label, entries: pool.files.map(readWhatifInput) }));
    const poolLabels = args.pools.map((pool) => pool.label);
    const whatifProblems = whatifInputProblems(whatifMaterialEntries, whatifPoolGroups, poolLabels);
    if (whatifProblems.length > 0) throw new BaselineInputError(whatifProblems);

    const rows = whatifRateRowsOf(whatifMaterialEntries, whatifPoolGroups);
    whatif = {
      material: { label: args.person, games: whatifMaterialEntries.length },
      pool: whatifPoolGroups.map((group) => ({ label: group.label, games: group.entries.length })),
      rows,
    };
    markdownLines.push(...renderWhatifRateMarkdown(rows));
  }

  console.log(markdownLines.join("\n"));
  const output = whatif === undefined ? report : { ...report, whatif };
  writeFileSync(path.resolve(args.out), `${JSON.stringify(output, null, 2)}\n`, "utf-8");
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
  process.exitCode = 1;
});
