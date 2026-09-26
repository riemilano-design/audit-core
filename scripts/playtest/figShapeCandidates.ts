// STEP FIG-2 (a) の薄い入口(CLI)。**材料を読んで JSON を書くだけで、判定を 1 つも持たない。**
// 判定・順位・名前の出し方はすべて fig/shapeCandidates.ts(純関数の層)が行う。
//
// 【使い方】
//   npx tsx scripts/playtest/figShapeCandidates.ts \
//     --answers <direct_answers.json> \
//     --kifu-dir "<group>:<dir>" [--kifu-dir ...] \
//     --out <出力の JSON> [--summary <出力の md>]
//
// `--kifu-dir` は `direct_answers.json` の `group` の値と、その組の `*.fixed.json` が置かれた
// ディレクトリの対応。**組とディレクトリの対応をこのファイルに書かない**(材料の置き場所は
// 呼ぶ側が指定する。納品の経路・顧客の名前をコードに入れないため)。
//
// 【開始局面(計画 §8.6 の決定 (B))】
// 固定棋譜が回した局(`mirrored: true`)かどうかは、既存の `lib/sideAlignment.ts` の
// `readSideAlignment` で読む(二重に実装しない)。回した局は `startSfen`、そうでなければ平手を
// 純関数へ渡す。**進める手数の式は純関数側**(`displayPly -(開始局面の SFEN の手数欄)`)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判定・順位・閾値。名前の出し方。**候補を間引くこと**(切れ目は見せ方 (b) の判断)。
// - 例外を握りつぶして別の局面を評価すること。**落ちた局面は `failures` に記録して数える**
//   (校正 = 何件一致したかを数えるため。黙って飛ばさない)。
// - エンジンの起動。顧客の名前・相手の名前の出力。

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import { DEFAULT_INITIAL_SFEN } from "../../apps/server/src/analysis/moveHistory.js";
import type { NameExposureRule } from "../../apps/server/src/analysis/nameExposure.js";
import { findShapeCandidates, loadAllShapes, type ShapeCandidatesResult } from "./fig/shapeCandidates.js";
import { readSideAlignment } from "./lib/sideAlignment.js";

class FigCliError extends Error {}

interface Args {
  answers: string;
  kifuDirs: Map<string, string>;
  out: string;
  summary: string | null;
}

function parseArgs(argv: readonly string[]): Args {
  let answers: string | null = null;
  let out: string | null = null;
  let summary: string | null = null;
  const kifuDirs = new Map<string, string>();
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    const value = argv[i + 1];
    if (value === undefined) throw new FigCliError(`${flag} に値がありません`);
    if (flag === "--answers") answers = value;
    else if (flag === "--out") out = value;
    else if (flag === "--summary") summary = value;
    else if (flag === "--kifu-dir") {
      const at = value.indexOf(":");
      if (at <= 0) throw new FigCliError(`--kifu-dir は "<group>:<dir>" の形です: "${value}"`);
      kifuDirs.set(value.slice(0, at), value.slice(at + 1));
    } else throw new FigCliError(`知らない引数です: "${flag}"`);
    i += 1;
  }
  if (answers === null || out === null) throw new FigCliError("--answers と --out は必須です");
  if (kifuDirs.size === 0) throw new FigCliError("--kifu-dir を 1 つ以上渡してください");
  return { answers, kifuDirs, out, summary };
}

interface AnswerRow {
  group: string;
  kifuId: string;
  displayPly: number;
  sfen: string;
}

function readAnswers(file: string): AnswerRow[] {
  const parsed = JSON.parse(readFileSync(file, "utf-8")) as { answers?: unknown };
  if (!Array.isArray(parsed.answers)) throw new FigCliError(`answers[] がありません: "${file}"`);
  return parsed.answers.map((row, index) => {
    const r = row as Partial<AnswerRow>;
    if (typeof r.group !== "string" || typeof r.kifuId !== "string" || typeof r.displayPly !== "number" || typeof r.sfen !== "string") {
      throw new FigCliError(`answers[${index}] に group・kifuId・displayPly・sfen が揃っていません`);
    }
    return { group: r.group, kifuId: r.kifuId, displayPly: r.displayPly, sfen: r.sfen };
  });
}

interface Kifu {
  moves: string[];
  initialSfen: string;
  mirrored: boolean;
}

function readKifu(dirs: Map<string, string>, group: string, kifuId: string, cache: Map<string, Kifu>): Kifu {
  const key = `${group}/${kifuId}`;
  const hit = cache.get(key);
  if (hit !== undefined) return hit;
  const dir = dirs.get(group);
  if (dir === undefined) throw new FigCliError(`組 "${group}" の --kifu-dir が渡されていません`);
  const parsed = JSON.parse(readFileSync(path.join(dir, `${kifuId}.fixed.json`), "utf-8")) as Record<string, unknown>;
  const { alignment } = readSideAlignment(parsed);
  if (!Array.isArray(parsed.moves)) throw new FigCliError(`moves[] がありません: "${key}"`);
  const kifu: Kifu = {
    moves: parsed.moves as string[],
    initialSfen: alignment.mirrored ? alignment.startSfen : DEFAULT_INITIAL_SFEN,
    mirrored: alignment.mirrored,
  };
  cache.set(key, kifu);
  return kifu;
}

interface Failure {
  kifuId: string;
  displayPly: number;
  mirrored: boolean;
  error: string;
}

interface RunOutput {
  kind: "fig2a_shape_candidates";
  /** 校正の数(計画 §8.6): 何局面を読み、何件が一致したか。 */
  calibration: { answers: number; matched: number; failed: number; mirroredAnswers: number; mirroredMatched: number };
  shapes: { total: number; draft: number; reviewed: number };
  positions: ShapeCandidatesResult[];
  failures: Failure[];
}

function quantiles(sorted: readonly number[]): Array<{ q: number; value: number }> {
  // 10 分位。**最近傍順位法**(index = ceil(q * n) - 1、q=0 は先頭)。新しい閾値ではなく、並べて位置を読むだけ。
  if (sorted.length === 0) return [];
  return [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1].map((q) => {
    const index = q === 0 ? 0 : Math.ceil(q * sorted.length) - 1;
    return { q, value: sorted[index]! };
  });
}

function median(sorted: readonly number[]): number | null {
  if (sorted.length === 0) return null;
  const half = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? sorted[half]! : (sorted[half - 1]! + sorted[half]!) / 2;
}

function summarize(run: RunOutput): string {
  const lines: string[] = [];
  const positions = run.positions;
  const candidateCounts = positions.map((p) => p.candidates.length).sort((a, b) => a - b);
  const matchScores = positions.flatMap((p) => p.candidates.map((c) => c.matchScore)).sort((a, b) => a - b);
  const figureTrue = positions.filter((p) => p.figure).length;
  const figureFalse = positions.filter((p) => !p.figure);
  const hedgedPerPosition = positions.map((p) => p.internal.exposureCounts.hedged).sort((a, b) => a - b);
  const totals = { named: 0, hedged: 0, none: 0 };
  const byRule = new Map<NameExposureRule, number>();
  for (const p of positions) {
    totals.named += p.internal.exposureCounts.named;
    totals.hedged += p.internal.exposureCounts.hedged;
    totals.none += p.internal.exposureCounts.none;
    for (const [rule, count] of Object.entries(p.internal.countsByRule)) {
      byRule.set(rule as NameExposureRule, (byRule.get(rule as NameExposureRule) ?? 0) + count);
    }
  }

  lines.push("# STEP FIG-2 (a) 実測の要約(道具が出した数だけ。判断は書かない)", "");
  lines.push("## 校正(計画 §8.6)", "");
  lines.push(`- 局面: ${run.calibration.answers} 件 / 一致: **${run.calibration.matched}**  / 落ちた: ${run.calibration.failed}`);
  lines.push(`- うち回した局(mirrored): ${run.calibration.mirroredAnswers} 件 / 一致: **${run.calibration.mirroredMatched}**`);
  lines.push(`- 形: ${run.shapes.total}(下書き ${run.shapes.draft} / レビュー済み ${run.shapes.reviewed})`, "");
  for (const failure of run.failures) {
    lines.push(`- 落ちた局面: ${failure.kifuId} ply ${failure.displayPly} mirrored=${failure.mirrored} ${failure.error}`);
  }
  lines.push("## 図を出すか(P1)", "");
  lines.push(`- \`figure: true\`: **${figureTrue} / ${positions.length}**`);
  lines.push(`- \`figure: false\`: ${figureFalse.length} 件${figureFalse.length === 0 ? "(**この材料ではこの出口が一度も使われなかった**)" : ""}`);
  for (const p of figureFalse) lines.push(`  - ${p.kifuId} ply ${p.displayPly}`);
  lines.push("");
  lines.push("## 1 局面あたりの候補数(P2)", "");
  lines.push(`- 最小 ${candidateCounts[0] ?? 0} / 中央値 ${median(candidateCounts) ?? 0} / 最大 ${candidateCounts[candidateCounts.length - 1] ?? 0}`);
  lines.push(`- 延べ候補数 ${matchScores.length}`, "");
  lines.push("## matchScore の分布(全候補ぶん。10 分位・最近傍順位法)", "");
  lines.push("| 分位 | 値 |");
  lines.push("|---|---|");
  for (const { q, value } of quantiles(matchScores)) lines.push(`| ${(q * 100).toFixed(0)}% | ${value.toFixed(4)} |`);
  lines.push(`| 最小 | ${(matchScores[0] ?? 0).toFixed(4)} |`);
  lines.push(`| 中央値 | ${(median(matchScores) ?? 0).toFixed(4)} |`);
  lines.push(`| 最大 | ${(matchScores[matchScores.length - 1] ?? 0).toFixed(4)} |`);
  lines.push("");
  lines.push("## 名前の見せ方の内訳(延べ。候補は捨てていない)", "");
  lines.push(`- \`named\`: **${totals.named}** / \`hedged\`: ${totals.hedged} / \`none\`(盤だけ): ${totals.none}`);
  lines.push(`- \`hedged\` が 1 件以上ある局面: ${positions.filter((p) => p.internal.exposureCounts.hedged > 0).length} / ${positions.length}`);
  // `figure` は到達できる候補が 0 件かどうかで、図を載せるかどうかではない(STEP P-100)。
  // 紙面の側が見る数をここに並べて出すだけ。**選別はしない。**
  lines.push(`- \`hedged\` が 0 件の局面: ${positions.filter((p) => p.internal.exposureCounts.hedged === 0).length} / ${positions.length}`);
  lines.push(`- 1 局面あたりの \`hedged\`: 最小 ${hedgedPerPosition[0] ?? 0} / 中央値 ${median(hedgedPerPosition) ?? 0} / 最大 ${hedgedPerPosition[hedgedPerPosition.length - 1] ?? 0}`, "");
  lines.push("## 規則ごとの件数(延べ)", "");
  lines.push("| 規則 | 件数 |");
  lines.push("|---|---|");
  for (const [rule, count] of [...byRule.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    lines.push(`| ${rule} | ${count} |`);
  }
  lines.push("");
  lines.push("## 注(出力の notes。全局面に入っている)", "");
  for (const note of positions[0]?.notes ?? []) lines.push(`- ${note}`);
  return `${lines.join("\n")}\n`;
}

function main(): void {
  const args = parseArgs(process.argv.slice(2));
  const shapes = loadAllShapes();
  const answers = readAnswers(args.answers);
  const cache = new Map<string, Kifu>();

  const positions: ShapeCandidatesResult[] = [];
  const failures: Failure[] = [];
  let mirroredAnswers = 0;
  let mirroredMatched = 0;

  for (const answer of answers) {
    const kifu = readKifu(args.kifuDirs, answer.group, answer.kifuId, cache);
    if (kifu.mirrored) mirroredAnswers += 1;
    try {
      positions.push(
        findShapeCandidates(
          {
            kifuId: answer.kifuId,
            displayPly: answer.displayPly,
            sfen: answer.sfen,
            moves: kifu.moves,
            initialSfen: kifu.initialSfen,
          },
          { shapes },
        ),
      );
      if (kifu.mirrored) mirroredMatched += 1;
    } catch (error) {
      failures.push({
        kifuId: answer.kifuId,
        displayPly: answer.displayPly,
        mirrored: kifu.mirrored,
        error: error instanceof Error ? `${error.constructor.name}: ${error.message}` : String(error),
      });
    }
  }

  const run: RunOutput = {
    kind: "fig2a_shape_candidates",
    calibration: {
      answers: answers.length,
      matched: positions.length,
      failed: failures.length,
      mirroredAnswers,
      mirroredMatched,
    },
    shapes: {
      total: shapes.length,
      draft: shapes.filter((s) => s.review_status === "draft" || s.review_status === "expired").length,
      reviewed: shapes.filter((s) => s.review_status === "human_reviewed" || s.review_status === "expert_verified").length,
    },
    positions,
    failures,
  };

  mkdirSync(path.dirname(args.out), { recursive: true });
  writeFileSync(args.out, `${JSON.stringify(run, null, 2)}\n`, "utf-8");
  if (args.summary !== null) {
    mkdirSync(path.dirname(args.summary), { recursive: true });
    writeFileSync(args.summary, summarize(run), "utf-8");
  }
  console.log(
    `局面 ${run.calibration.answers} 件 / 一致 ${run.calibration.matched} / 落ちた ${run.calibration.failed}` +
      ` | figure: true ${positions.filter((p) => p.figure).length} | 形 ${run.shapes.total}`,
  );
}

main();
