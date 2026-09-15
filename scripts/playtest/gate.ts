// STEP D4(docs/STEP_D4_PLAN_2026-09-15.md §7)。全ての手の組を対照群にして、条件式 1 本ごとに崩れ率を比べ、Gate で「満たす / 根拠不足」を出す道具。
//
// 使い方: npx tsx scripts/playtest/gate.ts --person <pN> --test-person <pN> --material <a.jsonl …> --test-sente <…> [--test-gote <…>]
//           --conditions <dir> --out <gate.jsonl> [--records-append]
//
// - 標準出力に Markdown(全ての組の崩れの基準値・条件式ごとの Gate)。`--out` に契約 diagnosis-gate v0.1 の行(定義 1 本につき 1 行、0 本なら空のファイル)
// - `--records-append` は、行を scripts/playtest/records/gate/<person>.jsonl に追記する(pair を含まない定義の行は追記しない)
// - 止める(行を書かずに exit 1): 人のラベルが記号でない・材料と試す側が同じラベル・同じ記録の重なり・referenceNodes がそろわない・error 行・
//   試す側の先手 / 後手の食い違い・段 2 の記録の不変条件の破れ・`--test-gote` で draft の定義がある(N-5・T-7)・行がスキーマに合わない
//
// 【このファイルがやること】入力を読み、lib/diagnosisMoment.ts の allPairsOf(軽い値)・lib/gate.ts の集計と判定・lib/gateOutput.ts の行と Markdown をつなぐ
// 【このファイルが絶対にやらないこと】エンジンを回すこと。深い値を使うこと(Q-2)。diagnose.ts の出力を変えること(Q-9)。条件式の中身を置くこと

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { MetaLine, RecordLine } from "./invariants/types.js";
import type { LoadedCondition } from "./lib/condition.js";
import { allPairsOf } from "./lib/diagnosisMoment.js";
import { diagnoseRecords, DRAFT_RULE_1 } from "./lib/failureEvent.js";
import { recordSha256 } from "./lib/failureEventSchema.js";
import { appliesToPairs, baselineTallyOf, GATE_VALUES, gateOf, gateTallyOf, judgePairs, type GatePairsGame } from "./lib/gate.js";
import {
  appendGateRecords,
  GateInputError,
  gateInputProblems,
  gateLineOf,
  gateRecordsSummary,
  loadConditionsDir,
  renderGateMarkdown,
  testGoteProblems,
  testSetOf,
  validateDiagnosisGateLine,
  type GateInputEntry,
  type GateLine,
  type GateRunContext,
} from "./lib/gateOutput.js";
import { readGitState } from "./lib/gitState.js";
import { screenOfRecord } from "./lib/screenDiagnosis.js";
import { initialSfenOf } from "./lib/sideAlignment.js";

/** このファイルがあるリポジトリ(作業ツリー)の根。入力のパスはここからの相対で書く */
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const RECORDS_DIR = path.join(REPO_ROOT, "scripts", "playtest", "records", "gate");
const USAGE =
  "使い方: npx tsx scripts/playtest/gate.ts --person <pN> --test-person <pN> --material <a.jsonl …> --test-sente <…> [--test-gote <…>] --conditions <dir> --out <gate.jsonl> [--records-append]";

interface GateArgs {
  person: string;
  testPerson: string;
  material: string[];
  testSente: string[];
  testGote: string[];
  conditions: string;
  out: string;
  recordsAppend: boolean;
}

const SINGLE = ["--person", "--test-person", "--conditions", "--out"] as const;
const MULTI = ["--material", "--test-sente", "--test-gote"] as const;

function parseArgs(argv: readonly string[]): GateArgs {
  const single = new Map<string, string>();
  const multi = new Map<string, string[]>(MULTI.map((flag) => [flag, []]));
  let recordsAppend = false;
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index]!;
    if (flag === "--records-append") {
      recordsAppend = true;
    } else if ((SINGLE as readonly string[]).includes(flag)) {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new GateInputError([`${flag} に値が無い`]);
      if (single.has(flag)) throw new GateInputError([`${flag} が 2 回ある`]);
      single.set(flag, value);
      index += 1;
    } else if ((MULTI as readonly string[]).includes(flag)) {
      while (argv[index + 1] !== undefined && !argv[index + 1]!.startsWith("--")) {
        multi.get(flag)!.push(argv[index + 1]!);
        index += 1;
      }
    } else {
      throw new GateInputError([`知らない引数: ${flag}`]);
    }
  }
  const missing = SINGLE.filter((flag) => !single.has(flag));
  if (missing.length > 0) throw new GateInputError([`${missing.join("・")} が無い`]);
  return {
    person: single.get("--person")!,
    testPerson: single.get("--test-person")!,
    material: multi.get("--material")!,
    testSente: multi.get("--test-sente")!,
    testGote: multi.get("--test-gote")!,
    conditions: single.get("--conditions")!,
    out: single.get("--out")!,
    recordsAppend,
  };
}

interface ReadInput {
  entry: GateInputEntry;
  file: { path: string; sha256: string };
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
    file: { path: relative, sha256 },
    meta,
    records,
  };
}

/** 1 局の全ての組(軽い値)。段 2 の記録は不変条件だけ確かめる(T-2) */
function pairsGameOf(input: ReadInput): GatePairsGame {
  const { kifuId } = input.entry;
  screenOfRecord(kifuId, input.meta, input.records);
  const initialSfen = initialSfenOf(input.meta);
  const { events } = diagnoseRecords(kifuId, input.records, DRAFT_RULE_1, initialSfen);
  return { kifuId, ...allPairsOf(kifuId, input.records, DRAFT_RULE_1, initialSfen, events, { source: "light" }) };
}

async function main(): Promise<void> {
  const argv = process.argv.slice(2);
  if (argv.length === 0) {
    console.error(USAGE);
    return;
  }
  const args = parseArgs(argv);
  const material = args.material.map(readInput);
  const testSente = args.testSente.map(readInput);
  const testGote = args.testGote.map(readInput);
  const { problems, referenceNodes } = gateInputProblems({
    person: args.person,
    testPerson: args.testPerson,
    material: material.map((input) => input.entry),
    testSente: testSente.map((input) => input.entry),
    testGote: testGote.map((input) => input.entry),
  });
  const conditions: LoadedCondition[] = await loadConditionsDir(path.resolve(args.conditions));
  problems.push(...testGoteProblems(testGote.length, conditions));
  if (problems.length > 0 || referenceNodes === null) throw new GateInputError(problems);

  const materialGames = material.map(pairsGameOf);
  const testGames = [...testSente, ...testGote].map(pairsGameOf);
  const applied = conditions.filter((loaded) => appliesToPairs(loaded.definition));
  const git = readGitState(REPO_ROOT);
  const context: GateRunContext = {
    person: args.person,
    testPerson: args.testPerson,
    referenceNodes,
    materialInputs: material.map((input) => input.file),
    test: { ...testSetOf(testSente.length, testGote.length), inputs: [...testSente, ...testGote].map((input) => input.file) },
    gateValues: GATE_VALUES,
    conditionsInRun: applied.length,
    provenance: { gitHead: git.gitHead, dirty: git.dirty },
  };

  const lines: GateLine[] = conditions.map((loaded) => {
    if (!appliesToPairs(loaded.definition)) return gateLineOf(context, loaded, null);
    const tallyOf = (games: readonly GatePairsGame[]) => gateTallyOf(games, games.map((game) => judgePairs(loaded, game.pairs)));
    const materialTally = tallyOf(materialGames);
    const testTally = tallyOf(testGames);
    return gateLineOf(context, loaded, { material: materialTally, test: testTally, gate: gateOf(loaded.definition.status, materialTally, testTally, GATE_VALUES) });
  });
  // すべての行をスキーマに照らしてから書く(1 行でも合わなければ何も書かない)
  const invalid = lines.flatMap((line) => validateDiagnosisGateLine(JSON.parse(JSON.stringify(line))).map((error) => `${line.condition.id}: ${error}`));
  if (invalid.length > 0) throw new Error(`契約 diagnosis-gate の行がスキーマに合わない: ${invalid.join(" / ")}`);

  const recordsBefore = gateRecordsSummary(RECORDS_DIR, args.person);
  console.log(
    renderGateMarkdown({
      person: args.person,
      testPerson: args.testPerson,
      referenceNodes,
      material: { files: material.length, baseline: baselineTallyOf(materialGames) },
      test: { ...context.test, files: testGames.length, baseline: baselineTallyOf(testGames) },
      lines,
      recordsBefore,
    }).join("\n"),
  );
  writeFileSync(path.resolve(args.out), lines.map((line) => `${JSON.stringify(line)}\n`).join(""), "utf-8");
  if (args.recordsAppend) {
    const appended = appendGateRecords(RECORDS_DIR, args.person, lines);
    console.error(`棄却の記録に ${appended} 行を追記した(${path.relative(REPO_ROOT, path.join(RECORDS_DIR, `${args.person}.jsonl`))})`);
  }
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
  process.exitCode = 1;
});
