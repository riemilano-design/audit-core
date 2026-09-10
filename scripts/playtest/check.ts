// STEP T-2(不変条件 I-1〜I-5・draftと集約報告)。
// docs/PLAYTEST_LOOP_PROPOSAL.md 4.3・4.4・4.5・6. の T-2 に従う。
//
// T-1(replay.ts)が保存したJSONLに対して、不変条件(すべてdraft)を適用し、
// 検出を「型 × 発生条件」で束ねてMarkdown報告を標準出力へ書く。
//
// 使い方: npx tsx scripts/playtest/check.ts <a.jsonl> [<b.jsonl> ...] [--json <out.json>]
//
// 【このファイルが絶対にやらないこと】
// - 検出を理由に仕様・閾値・文言を変えること、既知事項の表に載せること、不変条件を
//   approvedにすること(4.5 規則1・2)。
// - 将棋の判断・評価。
// - exit code を 0 以外にすること(draftの不変条件は何もブロックしない。4.5)。

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import { invariants } from "./invariants/index.js";
import type { Finding, InvariantType, MetaLine, RecordLine } from "./invariants/types.js";

const ALL_TYPES: InvariantType[] = ["沈黙", "矛盾", "断定", "未説明用語", "盤との不一致", "陳腐化"];

const DISCLAIMER =
  "draft の不変条件による検出であり、仕様・既知事項・異常の有無を確定するものではない。0件は『有効な不変条件が捉える範囲では検出されない』を意味する。";

interface InputFileResult {
  filePath: string;
  kifuId: string;
  gitHead: string | null;
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

  const records = lines.filter((l): l is RecordLine => l.kind === "record");

  const findings: Finding[] = [];
  for (const invariant of invariants) {
    for (const finding of invariant.check(records)) {
      findings.push({ ...finding, kifuId });
    }
  }

  return { filePath, kifuId, gitHead, findings };
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

function renderMarkdown(inputs: InputFileResult[], allFindings: Finding[], groups: Group[]): string {
  const lines: string[] = [];

  lines.push("# 対局記録の不変条件チェック(draft)");
  lines.push("");
  lines.push("## 入力");
  for (const input of inputs) {
    lines.push(`- ${input.filePath}(kifuId: ${input.kifuId}, gitHead: ${input.gitHead ?? "不明"}, 検出 ${input.findings.length} 件)`);
  }
  lines.push("");

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

  console.log(renderMarkdown(inputs, allFindings, groups));

  if (jsonOut) {
    const json = {
      inputs: inputs.map((i) => ({ path: i.filePath, kifuId: i.kifuId, gitHead: i.gitHead })),
      invariants: invariants.map((inv) => ({ id: inv.id, type: inv.type, status: inv.status })),
      findings: allFindings,
      groups: groups.map((g) => ({ ...g, examples: g.examples })),
    };
    writeFileSync(path.resolve(jsonOut), `${JSON.stringify(json, null, 2)}\n`, "utf-8");
  }

  process.exit(0);
}

main();
