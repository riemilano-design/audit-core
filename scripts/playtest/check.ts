// STEP T-2(不変条件 I-1〜I-5・draftと集約報告)。STEP T-5(T5-B・T5-C)で
// 分母(観測の集計)の追加と表記の更新を行った。
// docs/PLAYTEST_LOOP_PROPOSAL.md 4.3・4.4・4.5・6. の T-2、
// docs/STEP_T-5_PLAN_2026-09-11.md 2. T5-B・T5-C に従う。
//
// T-1(replay.ts)が保存したJSONLに対して、不変条件(draft・approved)を適用し、
// 検出を「型 × 発生条件」で束ねてMarkdown報告を標準出力へ書く。
//
// 使い方: npx tsx scripts/playtest/check.ts <a.jsonl> [<b.jsonl> ...] [--json <out.json>]
//
// 【このファイルが絶対にやらないこと】
// - 検出を理由に仕様・閾値・文言を変えること、既知事項の表に載せること、不変条件を
//   approvedにすること(4.5 規則1・2)。
// - 将棋の判断・評価。
// - exit code を 0 以外にすること(STEP T-5では変えない。exit codeの扱い自体は
//   人間承認事項。docs/STEP_T-5_PLAN_2026-09-11.md 5.)。
// - T5-Bの分母集計を理由に仕様・閾値・文言を変えること(分母は観測の集計であり、
//   不変条件ではない。docs/AGENT_PROTOCOL.md 11.)。

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import { invariants } from "./invariants/index.js";
import type { Finding, InvariantType, MetaLine, RecordLine } from "./invariants/types.js";
import { buildDenominatorReport, type DenominatorInput, type DenominatorReport, type DenominatorRow } from "./lib/denominators.js";

const ALL_TYPES: InvariantType[] = ["沈黙", "矛盾", "断定", "未説明用語", "盤との不一致", "陳腐化"];

const DISCLAIMER =
  "不変条件(approved と draft)による検出であり、仕様・既知事項・異常の有無を確定するものではない。approved の検出は STEP の完了条件に関わる(docs/AGENT_PROTOCOL.md 11.)。0件は『有効な不変条件が捉える範囲では検出されない』を意味する。";

const DENOMINATOR_NOTE = "観測の集計であり、不変条件ではない。何も異常と呼ばない。";

interface InputFileResult {
  filePath: string;
  kifuId: string;
  gitHead: string | null;
  mode: string | undefined;
  profile: string | undefined;
  records: RecordLine[];
  findings: Finding[];
}

interface Group {
  invariantId: string;
  condition: string;
  count: number;
  /** kifuId#ply の形式で発生箇所を列挙したもの(既存識別子の連結。新しい語は作らない)。 */
  plies: string[];
  examples: Finding[];
}

function parseArgs(argv: string[]): { files: string[]; jsonOut: string | undefined } {
  const jsonIndex = argv.indexOf("--json");
  const jsonOut = jsonIndex !== -1 ? argv[jsonIndex + 1] : undefined;
  const files = (jsonIndex !== -1 ? argv.slice(0, jsonIndex) : argv).filter((a) => a.length > 0);
  return { files, jsonOut };
}

function readInputFile(filePath: string): InputFileResult {
  const raw = readFileSync(path.resolve(filePath), "utf-8");
  const lines = raw
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0)
    .map((l) => JSON.parse(l) as { kind: string });

  const meta = lines.find((l) => l.kind === "meta") as MetaLine | undefined;
  const kifuId = meta?.kifuId ?? path.basename(filePath);
  const gitHead = meta?.gitHead ?? null;
  const mode = meta?.mode;
  const profile = meta?.profile;

  const records = lines.filter((l): l is RecordLine => l.kind === "record");

  const findings: Finding[] = [];
  for (const invariant of invariants) {
    for (const finding of invariant.check(records)) {
      findings.push({ ...finding, kifuId });
    }
  }

  return { filePath, kifuId, gitHead, mode, profile, records, findings };
}

function groupFindings(allFindings: Finding[]): Group[] {
  const map = new Map<string, Finding[]>();
  for (const finding of allFindings) {
    const key = `${finding.invariantId}\u0000${finding.condition}`;
    const list = map.get(key) ?? [];
    list.push(finding);
    map.set(key, list);
  }

  const groups: Group[] = [];
  for (const [key, findings] of map) {
    const [invariantId, condition] = key.split("\u0000");
    groups.push({
      invariantId: invariantId ?? "",
      condition: condition ?? "",
      count: findings.length,
      plies: findings.map((f) => `${f.kifuId}#${f.ply}`),
      examples: findings.slice(0, 3),
    });
  }

  groups.sort((a, b) => (a.invariantId === b.invariantId ? a.condition.localeCompare(b.condition) : a.invariantId.localeCompare(b.invariantId)));
  return groups;
}

function typeCounts(allFindings: Finding[]): Record<InvariantType, number> {
  const invariantTypeById = new Map(invariants.map((inv) => [inv.id, inv.type]));
  const counts: Record<InvariantType, number> = { 沈黙: 0, 矛盾: 0, 断定: 0, 未説明用語: 0, 盤との不一致: 0, 陳腐化: 0 };
  for (const finding of allFindings) {
    const type = invariantTypeById.get(finding.invariantId);
    if (type) counts[type] += 1;
  }
  return counts;
}

/** 表1件分(入力ごと、またはプロファイルごと)をMarkdownのテーブル行として並べる。
 * T5-B(分母の報告)の6列をそのまま出す(観測の集計であり、判断はしない)。 */
function renderDenominatorTable(rows: DenominatorRow[]): string[] {
  const lines: string[] = [];
  lines.push("| 対象 | 全手数 | 認識あり | 道のりあり | 候補手あり | 候補手が全件除外 | いずれも無し(沈黙) |");
  lines.push("|---|---|---|---|---|---|---|");
  for (const row of rows) {
    const c = row.counts;
    lines.push(
      `| ${row.label} | ${c.totalPlies} | ${c.hasRecognition} | ${c.hasRoute} | ${c.hasCandidateMove} | ${c.candidateExcluded} | ${c.silent} |`,
    );
  }
  return lines;
}

function renderMarkdown(
  inputs: InputFileResult[],
  allFindings: Finding[],
  groups: Group[],
  denominatorReport: DenominatorReport,
): string {
  const lines: string[] = [];

  lines.push("# 対局記録の不変条件チェック");
  lines.push("");
  lines.push("## 入力");
  for (const input of inputs) {
    lines.push(`- ${input.filePath}(kifuId: ${input.kifuId}, gitHead: ${input.gitHead ?? "不明"}, 検出 ${input.findings.length} 件)`);
  }
  const distinctGitHeads = new Set(inputs.map((input) => input.gitHead ?? "不明"));
  if (distinctGitHeads.size >= 2) {
    lines.push(
      `- 注意: 入力の gitHead が混在しています(${Array.from(distinctGitHeads).join(", ")})。`,
    );
  }
  lines.push("");

  lines.push("## 分母(観測の集計)");
  lines.push("");
  lines.push(DENOMINATOR_NOTE);
  lines.push("");
  lines.push(...renderDenominatorTable(denominatorReport.perInput));
  lines.push("");
  if (denominatorReport.perProfile) {
    lines.push("### プロファイルごとの小計(探索モードのみ)");
    lines.push("");
    lines.push(...renderDenominatorTable(denominatorReport.perProfile));
    lines.push("");
  }

  lines.push("## 型ごとの件数");
  lines.push("");
  lines.push("| 型 | 件数 |");
  lines.push("|---|---|");
  const counts = typeCounts(allFindings);
  for (const type of ALL_TYPES) {
    lines.push(`| ${type} | ${counts[type]} |`);
  }
  lines.push("");

  lines.push("## 束(不変条件 × 発生条件)ごとの詳細");
  lines.push("");
  if (groups.length === 0) {
    lines.push("検出はありません。");
  } else {
    for (const group of groups) {
      const invariant = invariants.find((inv) => inv.id === group.invariantId);
      lines.push(`### ${group.invariantId}(${invariant?.title ?? ""}) / condition: \`${group.condition}\``);
      lines.push("");
      lines.push(`- 型: ${invariant?.type ?? "不明"} / status: ${invariant?.status ?? "不明"} / source: ${invariant?.source ?? "不明"}`);
      lines.push(`- 件数: ${group.count}`);
      lines.push(`- 発生箇所(kifuId#ply): ${group.plies.join(", ")}`);
      lines.push(`- 代表例(最大3件):`);
      for (const example of group.examples) {
        lines.push(
          `  - kifuId: ${example.kifuId} / ply: ${example.ply} / senteMove: ${example.senteMove ?? "null"} / goteMove: ${example.goteMove ?? "null"} / sfen: ${example.sfen}`,
        );
        lines.push(`    detail: ${example.detail}`);
      }
      lines.push("");
    }
  }

  lines.push("---");
  lines.push("");
  lines.push(DISCLAIMER);
  lines.push("");

  return lines.join("\n");
}

function main(): void {
  const { files, jsonOut } = parseArgs(process.argv.slice(2));
  if (files.length === 0) {
    console.error(
      "使い方: npx tsx scripts/playtest/check.ts <a.jsonl> [<b.jsonl> ...] [--json <out.json>]",
    );
    process.exit(0);
    return;
  }

  const inputs = files.map(readInputFile);
  const allFindings = inputs.flatMap((i) => i.findings);
  const groups = groupFindings(allFindings);

  const denominatorInputs: DenominatorInput[] = inputs.map((i) => ({
    kifuId: i.kifuId,
    mode: i.mode,
    profile: i.profile,
    records: i.records,
  }));
  const denominatorReport = buildDenominatorReport(denominatorInputs);

  console.log(renderMarkdown(inputs, allFindings, groups, denominatorReport));

  if (jsonOut) {
    const json = {
      inputs: inputs.map((i) => ({ path: i.filePath, kifuId: i.kifuId, gitHead: i.gitHead })),
      invariants: invariants.map((inv) => ({ id: inv.id, type: inv.type, status: inv.status })),
      findings: allFindings,
      groups: groups.map((g) => ({ ...g, examples: g.examples })),
      denominators: denominatorReport,
    };
    writeFileSync(path.resolve(jsonOut), `${JSON.stringify(json, null, 2)}\n`, "utf-8");
  }

  process.exit(0);
}

main();
