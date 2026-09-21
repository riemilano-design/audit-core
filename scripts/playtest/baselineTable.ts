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
// 【このファイルがやること】入力を読み、lib/diagnosisMoment.ts の allPairsOf(軽い値)で組を作り、lib/baselineTable.ts の
// 集計(baselineReportOf)・入力の確かめ(baselineInputProblems)・Markdown(renderBaselineMarkdown)をつなぐ。
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

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE = "使い方: npx tsx scripts/playtest/baselineTable.ts --person <pN> --material <a.jsonl …> --pool <pM>=<a.jsonl …> [--pool <pK>=<…> …] --out <baseline.json>";

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
}

function parseArgs(argv: readonly string[]): Args {
  let person: string | undefined;
  let out: string | undefined;
  const material: string[] = [];
  const pools: PoolSpec[] = [];
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
    } else if (flag === "--material") {
      index += 1;
      while (index < argv.length && !argv[index]!.startsWith("--")) {
        material.push(argv[index]!);
        index += 1;
      }
    } else if (flag === "--pool") {
      index += 1;
      const first = argv[index];
      if (first === undefined || first.startsWith("--")) throw new BaselineInputError(["--pool に値が無い"]);
      const eq = first.indexOf("=");
      if (eq < 0) throw new BaselineInputError([`--pool の値は <ラベル>=<記録> の形: ${first}`]);
      const label = first.slice(0, eq);
      const firstFile = first.slice(eq + 1);
      const files = firstFile.length > 0 ? [firstFile] : [];
      index += 1;
      while (index < argv.length && !argv[index]!.startsWith("--")) {
        files.push(argv[index]!);
        index += 1;
      }
      pools.push({ label, files });
    } else {
      throw new BaselineInputError([`知らない引数: ${flag}`]);
    }
  }
  const missing = [...(person === undefined ? ["--person"] : []), ...(out === undefined ? ["--out"] : [])];
  if (missing.length > 0) throw new BaselineInputError([`${missing.join("・")} が無い`]);
  if (material.length === 0) throw new BaselineInputError(["--material の記録が無い"]);
  if (pools.length === 0) throw new BaselineInputError(["--pool が無い"]);
  return { person: person!, material, pools, out: out! };
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
  console.log(renderBaselineMarkdown(report).join("\n"));
  writeFileSync(path.resolve(args.out), `${JSON.stringify(report, null, 2)}\n`, "utf-8");
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
  process.exitCode = 1;
});
