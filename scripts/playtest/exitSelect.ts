// ⑤ Answer selection の道具(計画 docs/PLAN_EXIT_SELECT_2026-10-01.md の S-2・S-9)。
//
// 2 つの顔がある。
//   `--draft`  : **候補の一覧**を書く(`out/<顧客>/exit/answer_selection.draft.json`)。
//                **採用の印は空のまま。**
//   (既定)    : 段 `exit-select` の**門**。選択を読んで 3 つを見る ―
//                在る / 契約に合う / `adoptedBy` が埋まっている。**書き換えない。**
//
// 【採用は機械がしない】この道具は候補を並べるだけで、採用の印を付けるのは司令塔か人間
// (正本 ⑤ の行)。**門は `adoptedBy` を埋める道を持たない。**
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import { ANSWER_MENU } from "./lib/answerMenu.js";
import {
  aggregateIdsOf,
  questionIdsOf,
  selectionProblems,
  statementByItemRefOf,
  validateAnswerSelection,
} from "./lib/answerSelection.js";
import { buildSelectionDraft, selectionGateProblems } from "./lib/exitSelect.js";
import { loadObsRegistry } from "./lib/hypothesis.js";

class ExitSelectError extends Error {
  override name = "ExitSelectError";
}

function readJson(filePath: string): unknown {
  try {
    return JSON.parse(readFileSync(filePath, "utf-8")) as unknown;
  } catch (error) {
    throw new ExitSelectError(`読めない JSON: ${filePath}(${String(error)})`);
  }
}

interface Args {
  readonly draft: boolean;
  readonly selection?: string;
  readonly out?: string;
  readonly packet?: string;
  readonly integration?: string;
  readonly request?: string;
  readonly obsRegistry?: string;
  readonly today: string;
}

export function parseArgs(argv: readonly string[]): Args {
  const flags: Record<string, string> = {};
  const positional: string[] = [];
  let draft = false;
  let i = 0;
  while (i < argv.length) {
    const token = argv[i]!;
    if (token === "--draft") {
      draft = true;
      i += 1;
      continue;
    }
    if (token.startsWith("--")) {
      const value = argv[i + 1];
      if (value === undefined || value.startsWith("--")) throw new ExitSelectError(`${token} に値が無い`);
      flags[token.slice(2)] = value;
      i += 2;
      continue;
    }
    positional.push(token);
    i += 1;
  }
  const args: Args = {
    draft,
    ...(positional[0] !== undefined ? { selection: positional[0] } : {}),
    ...(flags["out"] !== undefined ? { out: flags["out"] } : {}),
    ...(flags["packet"] !== undefined ? { packet: flags["packet"] } : {}),
    ...(flags["integration"] !== undefined ? { integration: flags["integration"] } : {}),
    ...(flags["request"] !== undefined ? { request: flags["request"] } : {}),
    ...(flags["obs-registry"] !== undefined ? { obsRegistry: flags["obs-registry"] } : {}),
    today: flags["today"] ?? new Date().toISOString().slice(0, 10),
  };
  if (draft) {
    for (const required of ["packet", "integration", "request", "out"] as const) {
      if (args[required] === undefined) throw new ExitSelectError(`--draft には --${required} が要る`);
    }
  } else if (args.selection === undefined) {
    throw new ExitSelectError("選択の道を渡してください(例: out/c5/exit/answer_selection.json)");
  }
  return args;
}

function runDraft(args: Args): number {
  const draft = buildSelectionDraft({
    packet: readJson(args.packet!),
    integration: readJson(args.integration!),
    request: readJson(args.request!),
    registry: args.obsRegistry !== undefined ? loadObsRegistry(args.obsRegistry) : new Set<string>(),
    today: args.today,
    menuIds: ANSWER_MENU.map((item) => item.id as string),
  });
  mkdirSync(path.dirname(args.out!), { recursive: true });
  writeFileSync(args.out!, `${JSON.stringify(draft, null, 2)}\n`, "utf-8");
  console.log(
    `書いた: ${args.out}(通った候補 ${draft.items.length} 件・落ちた候補 ${draft.rejected.length} 件・` +
      `問い ${draft.questions.length} 件・行動の表 ${draft.menuIds.length} 件)`,
  );
  console.log("採用の印(adoptedBy)は空のままです ― 採用は司令塔か人間が付けます。");
  return 0;
}

function runGate(args: Args): number {
  const selection = readJson(args.selection!);
  const materialsGiven = args.packet !== undefined && args.integration !== undefined && args.request !== undefined;
  const { problems, notes } = selectionGateProblems(selection, {
    validateContract: (value) => validateAnswerSelection(value),
    ...(materialsGiven
      ? {
          crossCheck: (value) =>
            selectionProblems(value, {
              aggregateIds: aggregateIdsOf(readJson(args.packet!)),
              statementByItemRef: statementByItemRefOf(readJson(args.integration!)),
              questionIds: questionIdsOf(readJson(args.request!)),
              menuIds: new Set(ANSWER_MENU.map((item) => item.id as string)),
            }),
        }
      : {}),
  });
  for (const note of notes) console.log(note);
  if (problems.length > 0) {
    console.error(`落ちた項目 ${problems.length} 件:`);
    for (const problem of problems) console.error(`- ${problem}`);
    return 1;
  }
  console.log(`通過(${args.selection})`);
  return 0;
}

export function main(argv: readonly string[]): number {
  const args = parseArgs(argv);
  return args.draft ? runDraft(args) : runGate(args);
}

if (process.argv[1] !== undefined && import.meta.url.endsWith(path.basename(process.argv[1]))) {
  try {
    process.exit(main(process.argv.slice(2)));
  } catch (error) {
    console.error(error instanceof ExitSelectError ? error.message : String(error));
    process.exit(1);
  }
}
