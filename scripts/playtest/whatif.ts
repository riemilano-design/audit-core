// STEP WHATIF 作業 1(docs/STEP_WHATIF_PLAN_2026-09-22.md §2.1・§2.5)。「重要な局面の分かれ道」を測る段の CLI。
// **測る段だけ**(見せる段(PDF・Web)は別の作業。ここでは作らない)。
//
// 使い方: npx tsx scripts/playtest/whatif.ts --kifu <固定棋譜 JSON> --out <whatif.jsonl>
//           [--nodes <N>] [--multipv <K>] [--threads <N>]
//
// 【この CLI は薄くしてある】場面の拾い方・候補の組み立て・側ごとの分け方は lib/whatif.ts にあり、
// そちらに試験がある。ここでやるのは、固定棋譜を読む・エンジンを起こす(replay.ts・rescreen.ts と同じ
// LowPriorityEngine と resolveEnginePath())・本人の手番の局面ごとに MultiPV を呼ぶ(1 巡目)・場面の局面だけ
// 側ごとに searchmoves で読む(2 巡目、§2.5)・行を書く、だけである。
//
// 【2 巡目(側ごとの読み)について】`LowPriorityEngine`(apps/server が公開する型)には searchmoves を渡す口が
// 無いため、apps/ は変えず、ハーネスの側(このファイル)で素の `UsiEngine`(`send`・`waitForLine`)を直に使って
// `go nodes N searchmoves <その側の手…>` を組み立てる(lib/checkBaseline.ts と同じ「ハーネスの観測として足す」
// 流儀)。1 巡目の `PrioritizedEngine.asLowPriority()` とは別に、素のエンジンを使うだけで、`apps/` 側のコードは
// 1 行も変えていない。この CLI は 1 巡目・2 巡目とも直列(await で待ってから次へ)なので、
// 素のエンジンへ直接コマンドを送っても、PrioritizedEngine 経由の呼び出しと衝突しない。
//
// 【このファイルが絶対にやらないこと】将棋の判断・評価・閾値・文言。records/ への書き込み。
// 名前・/Users/ を含む絶対パスを出力へ書くこと(enginePath はここでは書かない)。
//
// 【手数の表し方(監査 REVISE、2026-09-22)】`ply` は畳んだ後の記録の手数。人に見せる手数は
// `displayPly`(= ply + plyOffset)。meta 行に `mirrored`・`plyOffset`・`startSfen`(mirrored のときだけ、
// replay.ts の段の meta と同じ形。lib/sideAlignment.ts の `sideMetaFields`)を足し、position・scene の行と
// summary の biggestFork には `lib/whatif.ts` の `withDisplayPly`(`lib/reportData.ts` の `displayPlyOf` を呼ぶ)
// で `displayPly` を足す。詳しくは lib/whatif.ts のファイル冒頭コメント参照。

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { DEFAULT_INITIAL_SFEN } from "../../apps/server/src/analysis/moveHistory.js";
import { resolveEnginePath } from "../../apps/server/src/engine/enginePath.js";
import { PrioritizedEngine } from "../../apps/server/src/engine/prioritizedEngine.js";
import { UsiEngine, type MultiPvLine } from "../../apps/server/src/engine/usiEngine.js";
import { parseInfoLine, type UsiScore } from "../../apps/server/src/engine/usiInfoParser.js";
import { readGitState } from "./lib/gitState.js";
import { plyOffsetOf } from "./lib/reportData.js";
import { readSideAlignment, sideMetaFields } from "./lib/sideAlignment.js";
import {
  GATE_AND_BASELINE_KING_ZONE_RADIUS,
  WHATIF_VALUES,
  evaluableTurns,
  sceneReadPlies,
  userTurnsOf,
  whatifGameSummaryOf,
  whatifPositionOf,
  whatifSceneOf,
  whatifSceneReadSummaryOf,
  withDisplayPly,
  type WhatifEngineLine,
  type WhatifPosition,
  type WhatifScene,
  type WhatifSideReader,
  type WhatifValues,
} from "./lib/whatif.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE = "使い方: npx tsx scripts/playtest/whatif.ts --kifu <固定棋譜 JSON> --out <whatif.jsonl> [--nodes <N>] [--multipv <K>] [--threads <N>]";
const DEFAULT_THREADS = 1;
// go nodes の待ち(usiEngine.ts の NODES_GO_TIMEOUT_MS と同じ考え方。side の探索量も候補と同じ桁のため揃える)。
const SIDE_READ_TIMEOUT_MS = 60_000;

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

interface FixedKifu {
  id: string;
  moves: string[];
  [field: string]: unknown;
}

/** `MultiPvGoResult.lines`(usiEngine.ts の型)から、lib/whatif.ts が読む最小限の形へ。 */
function toEngineLine(line: MultiPvLine): WhatifEngineLine {
  return {
    scoreCp: line.score?.type === "cp" ? line.score.value : null,
    mate: line.score?.type === "mate" ? line.score.value : null,
    pv: line.pv,
  };
}

/**
 * 側ごとの読み(計画 §2.5)。`moves`(その側の合法手だけ)に絞って `go nodes N searchmoves <moves…>` を
 * MultiPV 1 で読む。**素の `UsiEngine` を直に使う**(`LowPriorityEngine` は searchmoves を渡す口を持たないため。
 * ファイル冒頭コメント参照)。エンジンの例外・タイムアウトはここで握りつぶし null を返す
 * (measureEngineReference・measureCheckBaseline と同じ「測れなかった、推測しない」)。
 */
function makeSideReader(rawEngine: UsiEngine): WhatifSideReader {
  return async (sfen, moves, nodes) => {
    try {
      rawEngine.setMultiPv(1);
      rawEngine.position(sfen);
      rawEngine.send(`go nodes ${nodes} searchmoves ${moves.join(" ")}`);
      const { collected } = await rawEngine.waitForLine((line) => line.startsWith("bestmove"), { timeoutMs: SIDE_READ_TIMEOUT_MS });

      let best: { score: UsiScore | undefined; pv: string[] } | undefined;
      for (const raw of collected) {
        const parsed = parseInfoLine(raw);
        if (parsed !== undefined && parsed.multipv === 1) best = { score: parsed.score, pv: parsed.pv };
      }
      const bestmoveMatch = collected.find((l) => l.startsWith("bestmove"))?.match(/^bestmove (\S+)/);
      const move = best?.pv[0] ?? bestmoveMatch?.[1];
      if (move === undefined) return null;
      return {
        move,
        scoreCp: best?.score?.type === "cp" ? best.score.value : null,
        mate: best?.score?.type === "mate" ? best.score.value : null,
        pv: best !== undefined && best.pv.length > 0 ? best.pv : [move],
      };
    } catch {
      return null;
    }
  };
}

async function main(): Promise<number> {
  const args = process.argv.slice(2);
  const kifuArg = argValue(args, "--kifu");
  const outArg = argValue(args, "--out");
  if (kifuArg === undefined || outArg === undefined) {
    console.error(USAGE);
    return 1;
  }

  const nodesArg = argValue(args, "--nodes");
  const nodes = nodesArg !== undefined ? Number(nodesArg) : WHATIF_VALUES.nodes;
  const multiPvArg = argValue(args, "--multipv");
  const multiPv = multiPvArg !== undefined ? Number(multiPvArg) : WHATIF_VALUES.multiPv;
  const threadsArg = argValue(args, "--threads");
  const threads = threadsArg !== undefined ? Number(threadsArg) : DEFAULT_THREADS;
  if (!Number.isInteger(nodes) || nodes <= 0 || !Number.isInteger(multiPv) || multiPv <= 0 || !Number.isInteger(threads) || threads <= 0) {
    console.error(`--nodes・--multipv・--threads は正の整数です(nodes=${nodesArg} multipv=${multiPvArg} threads=${threadsArg})`);
    return 1;
  }
  // startPly・minLossCp・narrowGapCp・riseCp・pvMoves・sideZoneRadius・sideNodes は判断的知識の仮置きのまま
  // (CLI からは変えない。--nodes/--multipv は候補 K 個の読みの探索量だけを上書きする)。
  const values: WhatifValues = { ...WHATIF_VALUES, nodes, multiPv };

  const kifuPath = path.resolve(kifuArg);
  const kifu = JSON.parse(readFileSync(kifuPath, "utf-8")) as FixedKifu;
  const { alignment } = readSideAlignment(kifu);
  const startSfen = alignment.mirrored ? alignment.startSfen : DEFAULT_INITIAL_SFEN;
  // 手数の表し方(監査 REVISE): replay.ts の段の meta と同じ形(lib/sideAlignment.ts の sideMetaFields)。
  // mirrored なら plyOffset・startSfen も持つ。plyOffsetOf(lib/reportData.ts、既存)で displayPly の差を読む。
  const sideFields = sideMetaFields(alignment);
  const plyOffset = plyOffsetOf(sideFields);

  const allTurns = userTurnsOf(startSfen, kifu.moves);
  const turns = evaluableTurns(allTurns, values);

  const enginePath = resolveEnginePath();
  const rawEngine = new UsiEngine(enginePath);
  rawEngine.start();
  try {
    await rawEngine.usiHandshake();
    await rawEngine.isReady();
    rawEngine.setThreads(threads);
    const engine = new PrioritizedEngine(rawEngine).asLowPriority();

    const startedAt = new Date().toISOString();
    // 名前・/Users/ を含む絶対パスは書かない(enginePath はここに含めない)。
    const gitState = readGitState(REPO_ROOT);
    const lines: string[] = [
      JSON.stringify({
        kind: "meta",
        kifuId: kifu.id,
        startedAt,
        gitHead: gitState.gitHead,
        dirty: gitState.dirty,
        values,
        threads,
        // 出どころ(計画 §2.5 の 3.): この段の「玉のそば」は values.sideZoneRadius マス以内、
        // Gate・基準値(baselineTable.ts の軸 C)の「玉のそば」は gateAndBaseline マス以内(値を写すだけ)。
        kingZoneRadius: { thisStage: values.sideZoneRadius, gateAndBaseline: GATE_AND_BASELINE_KING_ZONE_RADIUS },
        // 手数の表し方(監査 REVISE): mirrored・plyOffset・startSfen(mirrored のときだけ)。replay.ts と同じ形。
        ...sideFields,
      }),
    ];

    // ---- 1 巡目: 本人の手番の局面ごとに、候補 K 個を MultiPV で読む ----
    const pass1StartedAt = Date.now();
    const positions: WhatifPosition[] = [];
    let previousCandidate0Value: number | null = null;
    for (const turn of turns) {
      engine.setMultiPv(multiPv);
      engine.position(turn.sfen);
      const result = await engine.goMultiPv({ nodes });
      const engineLines = result.lines.map(toEngineLine);
      const position = whatifPositionOf({ ply: turn.ply, sfen: turn.sfen, actualMove: turn.move, lines: engineLines, previousCandidate0Value }, values);
      positions.push(position);
      previousCandidate0Value = position.candidate0Value;
      lines.push(JSON.stringify({ kind: "position", ...withDisplayPly(position, plyOffset) }));
    }
    const pass1Ms = Date.now() - pass1StartedAt;

    const summary = whatifGameSummaryOf(positions);

    // ---- 2 巡目: 場面(fork・narrowHeld・chanceHeld・biggestFork)の局面だけ、側ごとに searchmoves で読む(計画 §2.5) ----
    const pass2StartedAt = Date.now();
    const sideReader = makeSideReader(rawEngine);
    const scenePlies = sceneReadPlies(positions, summary);
    const scenes: WhatifScene[] = [];
    for (const ply of scenePlies) {
      const position = positions.find((p) => p.ply === ply);
      if (position === undefined) continue; // 起こらない想定(scenePlies は positions から作る)が、念のため
      const scene = await whatifSceneOf(ply, position.sfen, sideReader, values);
      scenes.push(scene);
      lines.push(JSON.stringify({ kind: "scene", ...withDisplayPly(scene, plyOffset) }));
    }
    const pass2Ms = Date.now() - pass2StartedAt;
    const sceneReads = whatifSceneReadSummaryOf(scenes);

    const biggestFork = summary.biggestFork === null ? null : withDisplayPly(summary.biggestFork, plyOffset);
    lines.push(JSON.stringify({ kind: "summary", ...summary, biggestFork, sceneReads, timingMs: { pass1: pass1Ms, pass2: pass2Ms } }));

    const outPath = path.resolve(outArg);
    mkdirSync(path.dirname(outPath), { recursive: true });
    writeFileSync(outPath, `${lines.join("\n")}\n`, "utf-8");
    console.log(
      `書き込み: ${outPath}(局面 ${positions.length} / 読んだ本人の手番 ${allTurns.length} / 場面 ${scenes.length} / 1 巡目 ${pass1Ms}ms / 2 巡目 ${pass2Ms}ms)`,
    );
    return 0;
  } finally {
    rawEngine.quit();
    rawEngine.close();
  }
}

main().then(
  (code) => process.exit(code),
  (err: unknown) => {
    console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
    process.exit(1);
  },
);
