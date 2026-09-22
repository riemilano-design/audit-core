// STEP READ(docs/STEP_READ_PLAN_2026-09-22.md)。「読みの間違い」を人を介さずに分解する段の CLI。
// **測る段だけ**(見せる段は今回作らない。計画 5.)。
//
// 使い方: npx tsx scripts/playtest/read.ts --whatif <whatif-v2.jsonl> --kifu <固定棋譜 JSON> --out <read.jsonl>
//           [--threads <N>]
//
// 【入力】`whatif.ts`(STEP WHATIF 作業 4。攻めの側の決め方 v2)の出力(jsonl)と、同じ局の固定棋譜 JSON
// (`kifu-import-check.ts --fixed` の形)。**対象は `scenes.fork` が true の position 行(分かれ道)だけ**
// (計画「作るもの」冒頭)。`whatif` の meta 行から `kifuId` を読む(この CLI 自身は棋譜 ID を引数に取らない)。
//
// 【この CLI は薄くしてある】場面の組み立て・印・見た目の損得は lib/read.ts にあり、そちらに試験がある。
// ここでやるのは、whatif-v2・固定棋譜を読む・エンジンを起こす(素の UsiEngine。scripts/playtest/whatif.ts の
// 2 巡目(側ごとの読み)と同じ「ハーネスの観測として足す」流儀。lib/checkBaseline.ts 参照)・
// 分かれ道の局面ごとに node ラダーを読む・行を書く、だけである。
//
// 【このファイルが絶対にやらないこと】将棋の判断・評価・閾値・文言。records/ への書き込み。
// 名前・/Users/ を含む絶対パスを出力へ書くこと(enginePath はここでは書かない)。「読みが浅い」
// 「感覚が偏っている」のような断定の文を作ること(分類と件数だけを出す)。

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { resolveEnginePath } from "../../apps/server/src/engine/enginePath.js";
import { UsiEngine } from "../../apps/server/src/engine/usiEngine.js";
import { parseInfoLine, type UsiScore } from "../../apps/server/src/engine/usiInfoParser.js";
import { readGitState } from "./lib/gitState.js";
import {
  READ_VALUES,
  readForkPositionOf,
  readGameSummaryOf,
  type ReadForkPosition,
  type ReadLadderLevelInput,
} from "./lib/read.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE = "使い方: npx tsx scripts/playtest/read.ts --whatif <whatif-v2.jsonl> --kifu <固定棋譜 JSON> --out <read.jsonl> [--threads <N>]";
const DEFAULT_THREADS = 1;
// go nodes の待ち(usiEngine.ts の NODES_GO_TIMEOUT_MS・scripts/playtest/whatif.ts の SIDE_READ_TIMEOUT_MS と同じ考え方)。
const READ_TIMEOUT_MS = 60_000;

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

interface WhatifCandidateRow {
  move: string;
}

interface WhatifPositionRow {
  kind: "position";
  ply: number;
  displayPly: number;
  sfen: string;
  candidates: WhatifCandidateRow[];
  actualMove: string;
  scenes: { fork: boolean; narrowHeld: boolean; chanceHeld: boolean };
}

interface WhatifMetaRow {
  kind: "meta";
  kifuId: string;
}

interface FixedKifu {
  id: string;
  moves: string[];
  [field: string]: unknown;
}

/** whatif-v2 jsonl を読み、meta の `kifuId` と、分かれ道(`scenes.fork` が true)の position 行だけを返す。 */
function readWhatifForkPositions(whatifPath: string): { kifuId: string; positions: WhatifPositionRow[] } {
  const text = readFileSync(whatifPath, "utf-8");
  const rows = text
    .split("\n")
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
  const meta = rows.find((row) => row.kind === "meta") as unknown as WhatifMetaRow | undefined;
  if (meta === undefined) throw new Error(`whatif の記録に meta 行がありません: ${whatifPath}`);
  const positions = rows.filter((row) => row.kind === "position" && (row as unknown as WhatifPositionRow).scenes.fork === true) as unknown as WhatifPositionRow[];
  return { kifuId: meta.kifuId, positions };
}

/**
 * `sfen` を `nodes` ノードだけ読む(`searchmoves` を渡せばその手だけに絞る。MultiPV 1)。
 * 素の `UsiEngine` を直に使う(scripts/playtest/whatif.ts の `makeSideReader` と同じ形)。
 * エンジンの例外・タイムアウトはここで握りつぶし null を返す(測れなかった、推測しない)。
 */
async function readEval(engine: UsiEngine, sfen: string, nodes: number, searchmoves?: readonly string[]): Promise<{ scoreCp: number | null; mate: number | null; pv: string[] } | null> {
  try {
    engine.setMultiPv(1);
    engine.position(sfen);
    const command = searchmoves !== undefined ? `go nodes ${nodes} searchmoves ${searchmoves.join(" ")}` : `go nodes ${nodes}`;
    engine.send(command);
    const { collected } = await engine.waitForLine((line) => line.startsWith("bestmove"), { timeoutMs: READ_TIMEOUT_MS });

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
  const whatifArg = argValue(args, "--whatif");
  const kifuArg = argValue(args, "--kifu");
  const outArg = argValue(args, "--out");
  if (whatifArg === undefined || kifuArg === undefined || outArg === undefined) {
    console.error(USAGE);
    return 1;
  }
  const threadsArg = argValue(args, "--threads");
  const threads = threadsArg !== undefined ? Number(threadsArg) : DEFAULT_THREADS;
  if (!Number.isInteger(threads) || threads <= 0) {
    console.error(`--threads は正の整数です(threads=${threadsArg})`);
    return 1;
  }

  const whatifPath = path.resolve(whatifArg);
  const { kifuId, positions } = readWhatifForkPositions(whatifPath);

  const kifuPath = path.resolve(kifuArg);
  const kifu = JSON.parse(readFileSync(kifuPath, "utf-8")) as FixedKifu;
  if (kifu.id !== kifuId) {
    console.error(`--whatif(kifuId=${kifuId})と --kifu(id=${kifu.id})が対応していません`);
    return 1;
  }

  const enginePath = resolveEnginePath();
  const engine = new UsiEngine(enginePath);
  engine.start();
  try {
    await engine.usiHandshake();
    await engine.isReady();
    engine.setThreads(threads);

    const startedAt = new Date().toISOString();
    // 名前・/Users/ を含む絶対パスは書かない(enginePath はここに含めない)。
    const gitState = readGitState(REPO_ROOT);
    const lines: string[] = [
      JSON.stringify({
        kind: "meta",
        kifuId,
        startedAt,
        gitHead: gitState.gitHead,
        dirty: gitState.dirty,
        values: READ_VALUES,
        threads,
      }),
    ];

    const startedMs = Date.now();
    const readPositions: ReadForkPosition[] = [];
    let skippedForkCount = 0;
    for (const position of positions) {
      const top1 = position.candidates[0];
      if (top1 === undefined) {
        // 計画に無い、理論上の状態(候補が 0 件の局面。scripts/playtest/whatif.ts の既知の限界と同じ)。
        // 測れないので、このファイルの summary の外で件数だけ数える(局面の一覧には含めない)。
        skippedForkCount++;
        continue;
      }
      if (kifu.moves[position.ply - 1] !== position.actualMove) {
        throw new Error(`固定棋譜と whatif の記録の手数が対応していません(ply=${position.ply}, kifu=${kifuId})`);
      }
      const nextActualMove = position.ply < kifu.moves.length ? kifu.moves[position.ply]! : null;

      const ladderLevels: ReadLadderLevelInput[] = [];
      for (const nodes of READ_VALUES.nodeLadder) {
        const top = await readEval(engine, position.sfen, nodes);
        const actual = await readEval(engine, position.sfen, nodes, [position.actualMove]);
        ladderLevels.push({
          nodes,
          top: top !== null ? { scoreCp: top.scoreCp, mate: top.mate } : null,
          actual: actual !== null ? { scoreCp: actual.scoreCp, mate: actual.mate, pv: actual.pv } : null,
        });
      }

      const readPosition = readForkPositionOf({
        ply: position.ply,
        displayPly: position.displayPly,
        sfen: position.sfen,
        actualMove: position.actualMove,
        top1Move: top1.move,
        nextActualMove,
        ladderLevels,
      });
      readPositions.push(readPosition);
      lines.push(JSON.stringify({ kind: "position", ...readPosition }));
    }
    const timingMs = Date.now() - startedMs;

    const summary = readGameSummaryOf(readPositions);
    lines.push(JSON.stringify({ kind: "summary", ...summary, skippedForkCount, timingMs }));

    const outPath = path.resolve(outArg);
    mkdirSync(path.dirname(outPath), { recursive: true });
    writeFileSync(outPath, `${lines.join("\n")}\n`, "utf-8");
    console.log(`書き込み: ${outPath}(分かれ道 ${readPositions.length} / 除外 ${skippedForkCount} / ${timingMs}ms)`);
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
