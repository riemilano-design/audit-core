// scripts/ 配下の型検査を、2 つの tsconfig の両方について「必ず」走らせる。
//
// 【なぜこのファイルが要るか(2026-09-12 の実測)】
// 以前の package.json は次のように && でつないでいた。
//
//   "typecheck:scripts": "tsc --noEmit -p scripts/tsconfig.json && tsc --noEmit -p scripts/playtest/tsconfig.json"
//
// && は左が失敗すると右を実行しない。そして 1 つ目の scripts/tsconfig.json は
// include に ../apps/server/src を含むため、**apps/server に型エラーが 1 件でもあると、
// ハーネス(scripts/playtest/**)の型検査は一度も走らない**。走らなかったこと自体は
// 出力に現れないので、「エラーは 1 件だけ」に見える。
//
// 実測(2026-09-12): scripts/verify-shapes.ts(1 つ目の対象)と
// scripts/playtest/lib/prng.ts(2 つ目の対象)へ同時に型エラーを仕込むと、
// 出力に出たのは verify-shapes.ts の 1 件だけだった。playtest 側の誤りは
// 存在ごと消えていた。仕込みは両方戻してある。
//
// 【このファイルがやること】
// - 2 つの tsconfig について tsc --noEmit を順に、**どちらが失敗しても両方**実行する。
// - 終了コードを合算する(どちらかが 0 以外なら 0 以外で終わる)。
//
// 【このファイルが絶対にやらないこと】
// - エラーの握りつぶし・件数の要約・出力の加工。tsc の出力はそのまま流す。
// - tsconfig の include の書き換え(それは別の判断)。

import { spawnSync } from "node:child_process";

/** 検査する tsconfig。増やすときはここに足す(&& でつながないこと)。 */
const PROJECTS = ["scripts/tsconfig.json", "scripts/playtest/tsconfig.json"];

let failed = 0;

for (const project of PROJECTS) {
  const result = spawnSync("npx", ["tsc", "--noEmit", "-p", project], { stdio: "inherit" });
  const code = result.status ?? 1;
  if (code !== 0) failed = code;
}

process.exit(failed);
