// STEP TIME 作業 1(docs/STEP_TIME_PLAN_2026-09-22.md §6.1 の 1)。既存の固定棋譜 JSON に、元の KIF から読んだ
// 消費時間(moveSeconds)を後から足す小さな道具。開発補助であり本番導線には含めない(新しい数は出さない。既知の正解
// との校正は司令塔が手で行う)。
//
// 使い方:
//   npx tsx scripts/playtest/kifu-times.ts <fixed.json> <元の KIF>
//
// 【このファイルがやること】
// - 元の KIF を lib/kifuImport.ts の importKif で読み直す(CSA は対象外。「元の KIF」だけを読む)
// - 読み直した USI の手順(result.moves)を、既存の固定棋譜の「本人の手順」(originalMoves があればそれ、
//   無ければ moves。lib/reportData.ts の originalMovesOf と同じ)と突き合わせる。**1 つでも食い違えば書かない**
// - 一致すれば、読み直した moveSeconds(元の手順の順のまま。toFixedKifu と同じ形)を固定棋譜に足して書き直す
//   (1 手も秒を読めていなければ、欄を足さずに「秒が無い」と出す)
// - **書き換えても mtime を変えない**(pipeline.ts の段の「済み」判定は内容だけを見るので必須ではないが、
//   念のため常に元の mtime へ戻す。計画書 §6.1 の 1)
//
// 【このファイルが絶対にやらないこと】
// - moves が食い違うのに書くこと(黙って一部だけ足さない)。エンジンを回すこと。CSA を読むこと

import { readFileSync, statSync, utimesSync, writeFileSync } from "node:fs";

import { decodeKifuBytes, importKif } from "./lib/kifuImport.js";
import { originalMovesOf, type FixedKifu } from "./lib/reportData.js";

const [fixedPath, kifPath] = process.argv.slice(2);
if (fixedPath === undefined || kifPath === undefined) {
  console.error("使い方: npx tsx scripts/playtest/kifu-times.ts <fixed.json> <元の KIF>");
  process.exit(2);
}

const fixedRaw = readFileSync(fixedPath, "utf-8");
const fixed = JSON.parse(fixedRaw) as FixedKifu & Record<string, unknown>;
const original = originalMovesOf(fixed);

const { text } = decodeKifuBytes(readFileSync(kifPath));
const result = importKif(text);
if (result.kind !== "imported") {
  console.error(`読めなかった(${result.reason}): ${result.detail}`);
  process.exit(1);
}

if (result.moves.length !== original.length || result.moves.some((usi, i) => usi !== original[i])) {
  console.error(
    `moves が食い違うので書かない(固定棋譜 ${original.length} 手 / 読み直した KIF ${result.moves.length} 手)`,
  );
  process.exit(1);
}

const moveSeconds = result.lines.moves.map((m) => m.time);
if (!moveSeconds.some((t) => t !== null)) {
  console.log(`${fixedPath}: 秒を読めた手が 1 つも無いので、moveSeconds は足さない`);
  process.exit(0);
}

const written = { ...fixed, moveSeconds };
const stat = statSync(fixedPath);
writeFileSync(fixedPath, `${JSON.stringify(written, null, 2)}\n`, "utf-8");
// STEP TIME §6.1 の 1: pipeline.ts の段の「済み」判定は内容だけを見るが、念のため mtime は変えない。
utimesSync(fixedPath, stat.atime, stat.mtime);

const withTime = moveSeconds.filter((t) => t !== null).length;
console.log(`${fixedPath}: moveSeconds を足した(${withTime} / ${moveSeconds.length} 手に秒あり)`);
