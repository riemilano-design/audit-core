// STEP ANSWER 作業(docs/STEP_ANSWER_PLAN_2026-09-23.md §2.3)。行動のメニュー(`lib/answerMenu.ts` の
// `ANSWER_MENU`)を `answer_menu.json` に書く道具。
//
// 使い方: npx tsx scripts/playtest/answerMenu.ts --out <answer_menu.json>
//
// 組み立ては純粋関数(lib/answerMenu.ts)に任せ、ここは読み書きと配線だけ。
//
// 【この CLI が絶対にやらないこと】メニューの中身(条件・行動・minN)を決めること(それは lib/answerMenu.ts の
// `ANSWER_MENU`。文言の正本は docs §3)。エンジンを回すこと。

import { writeFileSync } from "node:fs";
import { buildAnswerMenuFile } from "./lib/answerMenu.js";

const USAGE = "使い方: npx tsx scripts/playtest/answerMenu.ts --out <answer_menu.json>";

export class AnswerMenuCliError extends Error {}

interface CliArgs {
  out: string;
}

export function parseArgs(argv: readonly string[]): CliArgs {
  let out: string | undefined;
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index]!;
    if (flag === "--out") {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new AnswerMenuCliError(`--out に値が無い。${USAGE}`);
      out = value;
      index += 1;
    } else {
      throw new AnswerMenuCliError(`知らない引数: ${flag}。${USAGE}`);
    }
  }
  if (out === undefined) throw new AnswerMenuCliError(`--out が無い。${USAGE}`);
  return { out };
}

function main(argv: readonly string[]): void {
  const args = parseArgs(argv);
  writeFileSync(args.out, JSON.stringify(buildAnswerMenuFile(), null, 2) + "\n", "utf-8");
  console.log(`wrote ${args.out}`);
}

const isMain = process.argv[1] !== undefined && import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}
