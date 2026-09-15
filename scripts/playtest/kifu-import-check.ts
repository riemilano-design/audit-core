// 外部の棋譜ファイル(KIF / CSA)を kifuImport で読み、何が読めて何が読めなかったかを表で出す。
// STEP D0-KIFU(仮番号。docs/STEP_D0-KIFU_PLAN_2026-09-14.md)。開発補助であり本番導線には含めない。
//
// 使い方:
//   npx tsx scripts/playtest/kifu-import-check.ts <フォルダ>            … 中の .kif / .kifu / .csa / .ki2 をすべて読み、表で出す
//   npx tsx scripts/playtest/kifu-import-check.ts <ファイル> [--format kif|csa] [--fixed <out.json> --id <id> --source <text>]
//
// 【このファイルがやること】ファイルのバイト列を読み(UTF-8 か Shift_JIS か、どちらで読んだかを出す)、
// 取り込みの結果・往復の確認・揃えた手(1 文字の成り駒。STEP D0-KIFU2)・行の 3 分類(採った / 読んだが使わない / 読めなかった)を標準出力へ書く。
// 【やらないこと】ネットワークへのアクセス。棋譜の取得。ファイルの書き換え(--fixed の出力先を除く)。

import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import { decodeKifuBytes, importCsa, importKif, toFixedKifu, type KifuFormat, type KifuImportResult } from "./lib/kifuImport.js";

const EXTENSIONS = [".kif", ".kifu", ".csa", ".ki2"];

function flag(name: string): string | undefined {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

interface Checked {
  file: string;
  bytes: number;
  encoding: string;
  format: KifuFormat | "ki2";
  result: KifuImportResult | null;
}

function check(file: string, formatOverride?: string): Checked {
  const raw = readFileSync(file);
  const { text, encoding } = decodeKifuBytes(raw);
  const ext = path.extname(file).toLowerCase();
  if (formatOverride === undefined && ext === ".ki2") {
    // KI2 は移動元を書かない形式で、shogiops の kifMoveRegex(移動元の "(77)" を要る)では読めない。読んだふりをしない。
    return { file, bytes: raw.length, encoding, format: "ki2", result: null };
  }
  const format: KifuFormat = formatOverride === "csa" || formatOverride === "kif" ? formatOverride : ext === ".csa" ? "csa" : "kif";
  return { file, bytes: raw.length, encoding, format, result: format === "csa" ? importCsa(text) : importKif(text) };
}

function cell(s: string): string {
  return s.replace(/\|/g, "\\|").replace(/\n/g, " ");
}

function row(c: Checked): string {
  const name = path.basename(c.file);
  const r = c.result;
  if (r === null) return `| ${cell(name)} | ${c.bytes} | ${c.encoding} | ki2 | 読めなかった | KI2 形式は非対応 | - | - | - | - | - | - |`;
  const kinds = new Map<string, number>();
  for (const l of r.lines.unused) kinds.set(l.kind, (kinds.get(l.kind) ?? 0) + 1);
  const unused = [...kinds].map(([k, n]) => `${k} ${n}`).join("、") || "0";
  const aligned = r.lines.moves.filter((m) => m.pieceNameAligned !== null).length;
  if (r.kind === "not_imported") {
    return `| ${cell(name)} | ${c.bytes} | ${c.encoding} | ${c.format} | 読めなかった | ${r.reason}(行 ${r.lineNo ?? "-"}): ${cell(r.detail)} | ${r.lines.moves.length}(途中まで) | - | - | ${aligned}(途中まで) | ${unused} | ${r.lines.unread.length} |`;
  }
  const ending = r.ending ? cell(r.ending.text.trim()) : "無し";
  const rt = `局面 ${r.roundTrip.finalPositionMatches ? "一致" : "不一致"} / 表記の食い違い ${r.roundTrip.notationMismatches.length}`;
  return `| ${cell(name)} | ${c.bytes} | ${c.encoding} | ${c.format} | 読めた | - | ${r.moves.length} | ${ending} | ${rt} | ${aligned} | ${unused} | ${r.lines.unread.length} |`;
}

function details(c: Checked): string[] {
  const out: string[] = [];
  const r = c.result;
  if (r === null) return out;
  for (const m of r.lines.moves) {
    if (m.pieceNameAligned !== null) out.push(`- ${path.basename(c.file)} ${m.ply} 手目 揃えて読んだ: ${m.pieceNameAligned.written}→${m.pieceNameAligned.readAs}`);
  }
  for (const l of r.lines.unread) out.push(`- ${path.basename(c.file)} ${l.lineNo} 行目 読めなかった(${l.why}): \`${cell(l.text.trim())}\``);
  if (r.kind === "imported") {
    for (const m of r.roundTrip.notationMismatches.slice(0, 10)) {
      out.push(`- ${path.basename(c.file)} ${m.ply} 手目 表記の食い違い: 元「${m.original}」/ 作り直し「${m.remade ?? "作れない"}」`);
    }
  }
  return out;
}

const target = process.argv[2];
if (target === undefined || target.startsWith("--")) {
  console.error("使い方: npx tsx scripts/playtest/kifu-import-check.ts <フォルダまたはファイル> [--format kif|csa] [--fixed <out.json> --id <id> --source <text>]");
  process.exit(2);
}

const isDir = statSync(target).isDirectory();
const files = isDir
  ? readdirSync(target)
      .filter((f) => EXTENSIONS.includes(path.extname(f).toLowerCase()))
      .sort()
      .map((f) => path.join(target, f))
  : [target];
const skipped = isDir ? readdirSync(target).filter((f) => !EXTENSIONS.includes(path.extname(f).toLowerCase())) : [];
const checked = files.map((f) => check(f, isDir ? undefined : flag("--format")));

console.log(`# 棋譜の取り込み確認(${isDir ? `フォルダ ${target}` : `ファイル ${target}`})`);
console.log("");
console.log(`対象 ${checked.length} ファイル${skipped.length > 0 ? ` / 拡張子が対象外で読まなかったもの ${skipped.length}: ${skipped.join(", ")}` : ""}`);
console.log("");
console.log("| ファイル | バイト | 文字コード | 形式 | 結果 | 読めなかった理由 | 手数 | 終局の行 | 往復 | 揃えた手 | 読んだが使わない行 | 読めなかった行 |");
console.log("|---|---|---|---|---|---|---|---|---|---|---|---|");
for (const c of checked) console.log(row(c));
const notes = checked.flatMap(details);
if (notes.length > 0) {
  console.log("");
  console.log("## 揃えて読んだ手・読めなかった行・表記の食い違い");
  for (const n of notes) console.log(n);
}

const fixedOut = flag("--fixed");
if (!isDir && fixedOut !== undefined) {
  const r = checked[0]?.result;
  if (!r || r.kind !== "imported") {
    console.log("\n--fixed: 取り込めなかったので書かない");
  } else {
    writeFileSync(fixedOut, `${JSON.stringify(toFixedKifu(r, flag("--id") ?? path.basename(target), flag("--source") ?? target), null, 2)}\n`, "utf-8");
    console.log(`\n--fixed: ${fixedOut} に書いた`);
  }
}
