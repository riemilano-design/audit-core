#!/usr/bin/env node
// docs/ ・ CLAUDE.md ・ .claude/ 配下の文書について、機械的に確認できる範囲だけを
// チェックする補助ツール。外部ライブラリに依存しない(Node.js標準機能のみ。
// scripts/validate-data.mjs と同じ方針。理由は docs/TESTING_STRATEGY.md を参照)。
//
// 位置づけ(STEP γ): 3役制の監査(独立性)を代替するものではない。
// docs/AGENT_PROTOCOL.md 10. の Tier B は「監査担当が行う確認そのもの」は省略せず、
// 報告の分量だけを圧縮する設計であり、このスクリプトはその確認作業のうち
// 機械的に済ませられる部分を肩代わりするだけの道具である。
//
// 使い方: node scripts/check-docs.mjs
// 常に exit 0 で終わる(このスクリプト自体が何かをブロックすることはない)。
// hookには接続しない(触ってよいファイルは docs/AGENT_PROTOCOL.md が定める)。

import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";

const ROOT = fileURLToPath(new URL("..", import.meta.url));

// ディレクトリ探索から除外するもの(依存モジュール・ビルド成果物・VCS内部)。
const EXCLUDED_DIRS = new Set(["node_modules", ".git", "dist", "build", "coverage"]);

function walkMarkdownFiles(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    if (EXCLUDED_DIRS.has(entry)) continue;
    const full = join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      walkMarkdownFiles(full, out);
    } else if (entry.endsWith(".md")) {
      out.push(full);
    }
  }
  return out;
}

function readText(path) {
  return readFileSync(path, "utf-8");
}

// ============================================================
// 1. 陳腐化パターンの検出
// ============================================================
//
// 【なぜ「禁止語」ではなくこの限定リストなのか】
// STEP γ の独立監査で、禁止語(最善・おすすめ・悪手・危険・有利・不利・形勢など)を
// リポジトリ全体からgrepする方式は、docs/PHASES.mdやstep-auditor.md自身が
// 「これらの語を使わない」というルールを説明するために、その語を列挙している箇所を
// 確実に誤検知することが実測で確認された。禁止語チェックはこのスクリプトに実装せず、
// .claude/agents/step-auditor.md の確認項目7(監査担当による人的確認)に委ねる
// (docs/AGENT_PROTOCOL.md 10. 参照)。
//
// 一方、ここに列挙する陳腐化パターンは「特定の事実が既に確定した後も、
// 確定前の表現が残っている」という、文脈非依存で機械的に判定できる種類の誤りに限る。
// 新しいパターンに気づいたら、判断根拠のコメントとともにここへ追加すること。
// 「Phase N 以降」のような一般形を正規表現で拾わないこと
// (例: "Phase 7以降の構造は未定" のような、まだ何も確定していない正当な将来言及を
// 誤検知するため。docs/ARCHITECTURE.md に実例がある)。
const STALE_PATTERNS = [
  {
    text: "Phase4以降",
    note: "Phase 4 は完了済み(docs/PHASES.md の Phase 4 節に記録)。「これから着手する」という意味の表現は陳腐化している。",
  },
  {
    text: "Phase 4以降",
    note: "同上。",
  },
  {
    text: "Phase 4 以降",
    note: "同上。",
  },
  {
    text: "apps/ はまだ存在しない",
    note: "apps/ は Phase 0 で作成済み。",
  },
  {
    text: "apps/が作られるまでは着手できない",
    note: "apps/ は既に作成済み。.claude/agents/*.md の説明文にこの記述が残っている場合、STEP 0d 相当の対応対象(未着手)。",
  },
];

function checkStalePatterns(files) {
  const findings = [];
  for (const file of files) {
    const text = readText(file);
    for (const { text: pattern, note } of STALE_PATTERNS) {
      if (text.includes(pattern)) {
        const line = text.slice(0, text.indexOf(pattern)).split("\n").length;
        findings.push({ file: relative(ROOT, file), line, pattern, note });
      }
    }
  }
  return findings;
}

// ============================================================
// 2. Markdown相対リンクの実在確認
// ============================================================
//
// [text](path) 形式のうち、http(s)://・mailto:・# のみのアンカー・空リンクは対象外。
// パスにアンカー(#...)が付いている場合は、ファイルの実在だけを確認する
// (アンカー先の見出しが実在するかまでは確認しない)。
const LINK_PATTERN = /\[[^\]]*\]\(([^)]+)\)/g;

function checkBrokenLinks(files) {
  const findings = [];
  for (const file of files) {
    const text = readText(file);
    const dir = dirname(file);
    let match;
    LINK_PATTERN.lastIndex = 0;
    while ((match = LINK_PATTERN.exec(text)) !== null) {
      const rawTarget = match[1].trim();
      if (
        rawTarget === "" ||
        rawTarget.startsWith("#") ||
        /^[a-z]+:\/\//i.test(rawTarget) ||
        rawTarget.startsWith("mailto:")
      ) {
        continue;
      }
      const targetPath = rawTarget.split("#")[0];
      if (targetPath === "") continue; // 同一ファイル内アンカーのみ
      const resolved = resolve(dir, targetPath);
      try {
        statSync(resolved);
      } catch {
        const line = text.slice(0, match.index).split("\n").length;
        findings.push({ file: relative(ROOT, file), line, target: rawTarget });
      }
    }
  }
  return findings;
}

// ============================================================
// 3. docs/PHASES.md の既知事項の件数チェック(意図しない増減の検知)
// ============================================================
//
// ここでのベースラインは、STEP γ 実装時点(2026年)の docs/PHASES.md の件数。
// 数が変わったこと自体は悪いことではない(既知事項の解消・追加は当然起きる)。
// このチェックは「気づかないうちに増減していないか」を機械的に知らせるだけで、
// 増減の是非を判断するのは人間である。
// 【重要】各セクションの開始・終了は個別に指定する(共有の停止マーカー方式は、
// 「Unit 4」セクションが次の「Phase 6 完了時点」セクションまで飲み込んでしまう
// バグを一度実際に起こしている。開始行のすぐ次に来る、その区切りに固有の
// マーカーを終了点として明示すること)。
// なお実装時に実測した結果、「既知事項(Unit 4、未対応)」は4件であり、
// 開発中の会話で3件と説明していたのは誤りだった(この誤りはSTEP γの
// 設計判断そのものには影響していない。件数ベースの除外方式を採らず
// マーカー方式にしたため)。
const KNOWN_ISSUE_SECTIONS = [
  {
    label: "既知事項(Unit 1〜3、未対応。Unit 4 では修正しない)",
    start: "**既知事項(Unit 1〜3、未対応。Unit 4 では修正しない)**",
    end: "**既知事項(Unit 4、未対応)**",
    expected: 4,
  },
  {
    label: "既知事項(Unit 4、未対応)",
    start: "**既知事項(Unit 4、未対応)**",
    end: "**Phase 6 完了前の修正",
    expected: 4,
  },
  {
    label: "既知事項(Phase 6 完了時点、未解決。修正には着手しない)",
    start: "**既知事項(Phase 6 完了時点、未解決。修正には着手しない)**",
    end: "**触ってよい主なディレクトリ**",
    expected: 9,
  },
];

function countBulletsBetween(text, startMarker, endMarker) {
  const start = text.indexOf(startMarker);
  if (start === -1) return null;
  const searchFrom = start + startMarker.length;
  const end = endMarker ? text.indexOf(endMarker, searchFrom) : text.length;
  const section = text.slice(searchFrom, end === -1 ? text.length : end);
  return section.split("\n").filter((l) => l.trimStart().startsWith("- ")).length;
}

function checkKnownIssueCounts(phasesPath) {
  const text = readText(phasesPath);
  const results = [];
  for (const { label, start, end, expected } of KNOWN_ISSUE_SECTIONS) {
    const actual = countBulletsBetween(text, start, end);
    results.push({ header: label, expected, actual });
  }
  // 実機点検テーブル(N-1, N-2, ... 形式の表)の行数。
  const tableRowMatches = text.match(/^\| N-\d+ \|/gm) ?? [];
  results.push({ header: "実機点検テーブル(N-*)の行数", expected: 5, actual: tableRowMatches.length });
  return results;
}

// ============================================================
// 4. apps/ ・ data/ の意図しない変更の検出(情報提示のみ)
// ============================================================
//
// このSTEPが文書のみを対象にしている場合、apps/ data/ に差分が出ていないかを
// 確認する材料を提供する。判定(意図した変更かどうか)は人間・監査担当が行う。
function checkAppsDataDiff() {
  try {
    const trackedDiff = execSync("git diff --name-only HEAD", { cwd: ROOT, encoding: "utf-8" });
    const untracked = execSync("git status --porcelain", { cwd: ROOT, encoding: "utf-8" })
      .split("\n")
      .filter((l) => l.startsWith("??"))
      .map((l) => l.slice(3));
    const changed = [...trackedDiff.split("\n").filter(Boolean), ...untracked];
    const relevant = changed.filter((f) => f.startsWith("apps/") || f.startsWith("data/"));
    return relevant;
  } catch {
    return null; // gitが使えない環境では情報提示を諦める(ブロックしない)
  }
}

// ============================================================
// 5. 未処遇の「ユーザーに見える = はい」既知事項の一覧(docs/AGENT_PROTOCOL.md 10.)
// ============================================================
//
// 【マーカー方式による既存分の除外について】
// 本STEP開始時点で docs/PHASES.md に記録済みの既知事項(実機点検の N-1〜N-5 表を含む、
// すべてのセクション)は、この一覧の対象にしない。件数(例:「16件」)で除外するのではなく、
// 追跡対象とする表の直前に <!-- check-docs: track-visibility --> という
// HTMLコメントマーカーを置くという運用にする。既存の表にはこのマーカーが無いため、
// 件数がいくつであっても自動的に対象外になる(数え間違いによる取りこぼしが起きない)。
// 本STEP以降、新しく既知事項の表を作るときに、このマーカーを付けて初めて
// この一覧の対象になる。
//
// 表の書式: マーカーの直後の表に、「見えるか」を含む見出しセルと、
// 「状態」または「処遇」を含む見出しセルを持つこと。各行の「見えるか」列に
// 「はい」を含み、「状態」列が「未処遇」であるか空欄の行を、未処遇として拾う。
// (「はい」の判定に迷った場合は「はい」とする。docs/AGENT_PROTOCOL.md 10.)
const TRACK_MARKER = "<!-- check-docs: track-visibility -->";

function parseMarkdownTable(lines) {
  // lines: ヘッダ行・区切り行・データ行の配列(先頭2行がヘッダ・区切り)。
  const splitRow = (line) =>
    line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((c) => c.trim());
  const header = splitRow(lines[0]);
  const rows = lines.slice(2).map(splitRow);
  return { header, rows };
}

function findUnresolvedVisibleIssues(phasesPath) {
  const text = readText(phasesPath);
  const findings = [];
  let searchFrom = 0;
  while (true) {
    const markerIdx = text.indexOf(TRACK_MARKER, searchFrom);
    if (markerIdx === -1) break;
    searchFrom = markerIdx + TRACK_MARKER.length;
    // マーカー直後の最初の表ブロックを探す。
    const after = text.slice(searchFrom);
    const tableMatch = after.match(/(\|[^\n]*\|\n\|[-:| ]+\|\n(?:\|[^\n]*\|\n?)*)/);
    if (!tableMatch) continue;
    const tableLines = tableMatch[1].trim().split("\n");
    const { header, rows } = parseMarkdownTable(tableLines);
    const visibleColIdx = header.findIndex((h) => h.includes("見えるか"));
    const statusColIdx = header.findIndex((h) => h.includes("状態") || h.includes("処遇"));
    if (visibleColIdx === -1 || statusColIdx === -1) continue;
    for (const row of rows) {
      const visible = row[visibleColIdx] ?? "";
      const status = row[statusColIdx] ?? "";
      const isVisible = visible.includes("はい");
      const isUnresolved = status.trim() === "" || status.includes("未処遇");
      if (isVisible && isUnresolved) {
        findings.push({ row });
      }
    }
  }
  return findings;
}

// ============================================================
// 実行
// ============================================================

function main() {
  const files = walkMarkdownFiles(ROOT);
  const phasesPath = join(ROOT, "docs", "PHASES.md");

  console.log("=== 1. 陳腐化パターンの検出 ===");
  const stale = checkStalePatterns(files);
  if (stale.length === 0) {
    console.log("該当なし。");
  } else {
    for (const f of stale) {
      console.log(`  ${f.file}:${f.line}  "${f.pattern}"  — ${f.note}`);
    }
  }

  console.log("\n=== 2. Markdown相対リンクの実在確認 ===");
  const broken = checkBrokenLinks(files);
  if (broken.length === 0) {
    console.log("リンク切れなし。");
  } else {
    for (const b of broken) {
      console.log(`  ${b.file}:${b.line}  リンク先が見つからない: ${b.target}`);
    }
  }

  console.log("\n=== 3. docs/PHASES.md 既知事項の件数チェック ===");
  try {
    const counts = checkKnownIssueCounts(phasesPath);
    for (const c of counts) {
      const mark = c.actual === c.expected ? "OK" : "!! 変化あり";
      console.log(`  [${mark}] ${c.header}: 期待 ${c.expected} 件 / 実際 ${c.actual ?? "不明(セクション未検出)"} 件`);
    }
  } catch (err) {
    console.log(`  docs/PHASES.md を読めなかった: ${err.message}`);
  }

  console.log("\n=== 4. apps/ ・ data/ の変更(情報提示。判定は人間・監査担当が行う) ===");
  const appsDataDiff = checkAppsDataDiff();
  if (appsDataDiff === null) {
    console.log("  git を使えなかったため確認できなかった。");
  } else if (appsDataDiff.length === 0) {
    console.log("  apps/ ・ data/ に差分なし。");
  } else {
    for (const f of appsDataDiff) console.log(`  変更あり: ${f}`);
  }

  console.log("\n=== 5. 未処遇の「ユーザーに見える = はい」既知事項(司令塔が提案に併記するもの) ===");
  try {
    const unresolved = findUnresolvedVisibleIssues(phasesPath);
    if (unresolved.length === 0) {
      console.log("  対象なし(マーカー付きの表が無いか、未処遇の項目が無い)。");
    } else {
      for (const u of unresolved) {
        console.log(`  未処遇: ${u.row.join(" | ")}`);
      }
    }
  } catch (err) {
    console.log(`  docs/PHASES.md を読めなかった: ${err.message}`);
  }

  // このスクリプトは監査・判断を代替しない。常にexit 0で終える。
  process.exit(0);
}

main();
