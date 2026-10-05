// Audit Core T-2(docs/AUDIT_CORE_EXTRACTION_PLAN.md §7 Phase 1 の I-1)。Core 候補が将棋側を import しないことの
// 静的走査。**既に在る逆依存は KNOWN_EXCEPTIONS に名指しで記録し、新しい逆依存だけを落とす。**
//
// 【検出するもの】Core 候補のファイルから出る辺のうち、
//   - TS: `shogiops`・`apps/server` への import、または Core 候補の外の module で**そこから先(Core 候補を通らずに)
//     `shogiops`/`apps/server` に届く**ものへの import(静的 import・`export … from`・`import type`・
//     文字列リテラルの `import()`・`require()`)。AST で読む(typescript 7 の `unstable/sync` が返す実 AST)。
//   - TS: `report-pdf/` を指す文字列リテラル(Python のソースを字面で読む依存。§3.2)。
//   - Python: report-pdf の組版・盤・指し手の module(SHOGI_PY_MODULES)への `import`/`from … import`(関数内も含む)。
//     AST(python3 の `ast`)で読む。
// 【例外の意味】「安全だから許す」ではない。**今ある技術的負債を名指しする**ため。T-3 以降で 1 本外すたびに
//   ここから消す ― 消し忘れは「例外が実物に無い」として赤になる(両向き)。
// 【このファイルが絶対にやらないこと】逆依存を解消すること。Core 候補の中身を変えること。実物(`out/`)を読むこと。

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as ast from "typescript/unstable/ast";
import { API, type Snapshot } from "typescript/unstable/sync";
import { afterAll, describe, expect, it } from "vitest";

const PLAYTEST = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const REPO_ROOT = path.resolve(PLAYTEST, "..", "..");
const APPS_SERVER = path.join(REPO_ROOT, "apps", "server");
const PLAYTEST_TSCONFIG = path.join(PLAYTEST, "tsconfig.json");

/** Core 候補(計画 §3 結論の TS 8 本 = 将棋依存なし)。相対パスは scripts/playtest から。 */
export const CORE_TS_PURE = [
  "lib/eventSchema.ts", "lib/packetRef.ts", "lib/prng.ts", "lib/env.ts",
  "lib/tokenBudget.ts", "lib/schemaAdapters.ts", "lib/llmClient.ts", "lib/gitState.ts",
] as const;

/** Core 候補 [A′](計画 §2.1.1・§2.2。機構は汎用だが将棋依存が残る)。 */
export const CORE_TS_A_PRIME = [
  "lib/observationPacket.ts", "lib/observationAggregates.ts", "lib/observationProvenance.ts", "lib/hypothesis.ts",
  "lib/seatOutput.ts", "lib/integration.ts", "lib/seatRun.ts", "lib/exitSelect.ts", "lib/answerSelection.ts",
  "hypothesisCheck.ts", "seatOutputCheck.ts", "integrationCheck.ts", "runSeats.ts",
] as const;

/** Core 候補(Python)。計画 §3 結論の 3 本と、§2.3 の [A′] 5 本。 */
export const CORE_PY_PURE = ["compare_render.py", "check_fonts_embedded.py", "rename_list.py"] as const;
export const CORE_PY_A_PRIME = ["check_answer.py", "exit_gate.py", "check_structure.py", "check_delivery.py", "exit_index.py"] as const;

/** report-pdf の将棋側(組版・盤・指し手・冊子の材料。計画 §2.3 の [B])。 */
export const SHOGI_PY_MODULES = [
  "board_draw", "board_spec", "move_text", "fig1",
  "render_answer", "render_appendix", "render_direct", "render_front", "render_main", "render_time_cause", "render_whatif",
  "exit_fill", "exit_body", "exit_cover", "exit_render", "exit_groups", "exit_candidates", "answer_facts",
  "_app", "_app_head", "_head", "_mid", "_tail", "_util", "dump_booklet_numbers",
] as const;

export type EdgeKind = "runtime" | "type" | "dynamic" | "require" | "text";

export interface BoundaryViolation {
  /** Core 候補(scripts/playtest からの相対パス) */
  file: string;
  /** 候補の中に書かれている import 指定子(文字列リテラルの場合はその字) */
  specifier: string;
  kind: EdgeKind;
  /** 何に届くか(`shogiops` / `apps/server` / `report-pdf` / Python の module 名)。経由があれば `(via …)` */
  reaches: string;
}

export interface KnownException extends BoundaryViolation {
  reason: string;
}

/**
 * 現在すでに在る逆依存(計画 §3.1・§3.2 の表と 1 対 1)。**増やすときは計画に根拠を書く。減るのは T-3 以降。**
 */
export const KNOWN_EXCEPTIONS: readonly KnownException[] = [
  { file: "lib/hypothesis.ts", specifier: "./timeSearch.js", kind: "runtime", reaches: "apps/server (via invariants/types.ts)",
    reason: "§3.1: `SEARCH_COLUMNS` を `loadObsRegistry` の 30 本の id のためだけに引く。timeSearch → reportData → apps/server + shogiops。T-3(I-2)で引数注入に替える" },
  { file: "lib/hypothesis.ts", specifier: "../report-pdf/check_answer.py", kind: "text", reaches: "report-pdf",
    reason: "§3.2: `BANNED_WORDS` を Python のソースから正規表現で抜く(言語をまたぐ字面依存)。T-3(I-2)で JSON 化" },
  { file: "lib/observationProvenance.ts", specifier: "./observationFacts.js", kind: "runtime", reaches: "shogiops (via lib/observationFacts.ts)",
    reason: "§3.1: `AHEAD_CP` を閾値の表 `toolThresholds()` のために引く。I-3 で `ThresholdRow[]` の引数に" },
  { file: "lib/observationProvenance.ts", specifier: "./reportData.js", kind: "runtime", reaches: "apps/server (via invariants/types.ts)",
    reason: "§3.1: `TIME_VALUES` を閾値の表のために引く。I-3 で引数に" },
  { file: "lib/observationAggregates.ts", specifier: "./observationFacts.js", kind: "type", reaches: "shogiops (via lib/observationFacts.ts)",
    reason: "§3.1: `FactsMaterials` の型だけ(実行時依存なし)。I-4 で generic に" },
  { file: "lib/gitState.ts", specifier: "../invariants/types.js", kind: "type", reaches: "apps/server (via invariants/types.ts)",
    reason: "§3.1: `MetaLine` の型だけ。`invariants/types.ts` が apps/server の型を import する。`Pick<MetaLine,\"dirty\">` を局所型に置き換えれば切れる" },
  { file: "report-pdf/exit_gate.py", specifier: "exit_candidates", kind: "runtime", reaches: "exit_candidates",
    reason: "§3.1: 門が候補の一覧(⑤ の材料)の module を読む。走査層の分離(I-8)の後に見直す" },
  { file: "report-pdf/exit_gate.py", specifier: "exit_fill", kind: "runtime", reaches: "exit_fill",
    reason: "§3.1: 検査 (xi) の型の再構成のため関数内で `exit_fill` を import(循環を避けて関数内)。⑥ = 将棋" },
];

// ==================== TS の走査(typescript 7 の実 AST) ====================

interface Edge { specifier: string; kind: EdgeKind }

/** `report-pdf/` 配下の Python ファイルへの**パス**だけ(出どころの名札「… exit_groups.py AHEAD_CP」のような説明の字は拾わない)。 */
const REPORT_PDF_PY_RE = /(^|\/)report-pdf\/[\w.-]+\.py$/;

let api: API | undefined;
let snapshot: Snapshot | undefined;
const tempDirs: string[] = [];

function tsApi(): API {
  api ??= new API({ cwd: REPO_ROOT });
  return api;
}

/** scripts/playtest の project から実ファイルの AST を取る(project に無いファイルは例外 = 黙って通さない)。 */
function sourceFileOf(absFile: string): ast.SourceFile {
  snapshot ??= tsApi().updateSnapshot({ openProjects: [PLAYTEST_TSCONFIG] });
  const project = snapshot.getProject(PLAYTEST_TSCONFIG);
  const sf = project?.program.getSourceFile(absFile);
  if (sf === undefined) throw new Error(`project に無いファイル(走査できない): ${absFile}`);
  return sf;
}

/** 合成したソースの AST(陽性対照用)。一時フォルダに tsconfig と 1 ファイルを置いて別 project として読む。 */
export function parseSynthetic(sourceText: string): ast.SourceFile {
  const dir = mkdtempSync(path.join(tmpdir(), "core-boundary-"));
  tempDirs.push(dir);
  const tsconfig = path.join(dir, "tsconfig.json");
  const file = path.join(dir, "probe.ts");
  writeFileSync(tsconfig, JSON.stringify({ compilerOptions: { target: "ES2022", module: "ESNext", moduleResolution: "Bundler", noEmit: true }, include: ["probe.ts"] }));
  writeFileSync(file, sourceText);
  const snap = tsApi().updateSnapshot({ openProjects: [tsconfig] });
  const sf = snap.getProject(tsconfig)?.program.getSourceFile(file);
  if (sf === undefined) throw new Error("合成ソースを読めなかった");
  return sf;
}

afterAll(() => {
  snapshot?.dispose();
  api?.close();
  for (const dir of tempDirs) rmSync(dir, { recursive: true, force: true });
});

function literalText(node: ast.Node | undefined): string | undefined {
  return node !== undefined && (ast.isStringLiteral(node) || ast.isNoSubstitutionTemplateLiteral(node)) ? node.text : undefined;
}

/** 1 ファイルの import の辺を AST から取る(文字列リテラルの `report-pdf/` 参照も `text` として拾う)。 */
export function tsEdgesOf(sf: ast.SourceFile): Edge[] {
  const edges: Edge[] = [];
  const visit = (node: ast.Node): void => {
    if (ast.isImportDeclaration(node)) {
      const clause = node.importClause;
      const named = clause?.namedBindings;
      const allTypeSpecifiers = named !== undefined && ast.isNamedImports(named) && named.elements.length > 0 && named.elements.every((e) => e.isTypeOnly);
      const typeOnly = clause?.phaseModifier === ast.SyntaxKind.TypeKeyword || (allTypeSpecifiers && clause?.name === undefined);
      edges.push({ specifier: literalText(node.moduleSpecifier) ?? "<non-literal import>", kind: typeOnly ? "type" : "runtime" });
    } else if (ast.isExportDeclaration(node) && node.moduleSpecifier !== undefined) {
      edges.push({ specifier: literalText(node.moduleSpecifier) ?? "<non-literal export>", kind: node.isTypeOnly ? "type" : "runtime" });
    } else if (ast.isImportEqualsDeclaration(node) && ast.isExternalModuleReference(node.moduleReference)) {
      edges.push({ specifier: literalText(node.moduleReference.expression) ?? "<non-literal import=>", kind: node.isTypeOnly ? "type" : "runtime" });
    } else if (ast.isCallExpression(node)) {
      const arg = literalText(node.arguments[0]);
      if (node.expression.kind === ast.SyntaxKind.ImportKeyword) edges.push({ specifier: arg ?? "<non-literal import()>", kind: "dynamic" });
      else if (ast.isIdentifier(node.expression) && node.expression.text === "require") edges.push({ specifier: arg ?? "<non-literal require()>", kind: "require" });
    }
    const text = literalText(node);
    if (text !== undefined && REPORT_PDF_PY_RE.test(text)) {
      const parent = node.parent;
      const isSpecifier = ast.isImportDeclaration(parent) || ast.isExportDeclaration(parent);
      if (!isSpecifier) edges.push({ specifier: text, kind: "text" });
    }
    node.forEachChild(visit);
  };
  visit(sf);
  return edges;
}

/** 相対指定子を実ファイルに直す(`.js` → `.ts`、フォルダは `index.ts`)。解決できなければ undefined。 */
function resolveRelative(fromFile: string, specifier: string): string | undefined {
  const base = path.resolve(path.dirname(fromFile), specifier);
  const candidates = [base, base.replace(/\.js$/, ".ts"), base.replace(/\.js$/, ".tsx"), `${base}.ts`, path.join(base, "index.ts")];
  for (const c of candidates) if (existsSync(c) && statSync(c).isFile()) return c;
  return undefined;
}

function isShogiTarget(specifier: string, resolved: string | undefined): string | undefined {
  if (specifier === "shogiops" || specifier.startsWith("shogiops/")) return "shogiops";
  if (resolved !== undefined && (resolved === APPS_SERVER || resolved.startsWith(`${APPS_SERVER}${path.sep}`))) return "apps/server";
  return undefined;
}

/**
 * Core 候補の外の module から、**Core 候補を通らずに**将棋側へ届くか(届く先の名前。届かなければ undefined)。
 * 候補を通る経路は候補自身の辺として別に数える(二重に数えない)。
 */
export function reachesShogi(absFile: string, coreSet: ReadonlySet<string>, memo: Map<string, string | undefined>, stack: Set<string> = new Set()): string | undefined {
  if (memo.has(absFile)) return memo.get(absFile);
  if (stack.has(absFile)) return undefined;
  stack.add(absFile);
  let found: string | undefined;
  for (const edge of tsEdgesOf(sourceFileOf(absFile))) {
    if (edge.kind === "text" || edge.specifier.startsWith("<")) continue;
    const resolved = edge.specifier.startsWith(".") ? resolveRelative(absFile, edge.specifier) : undefined;
    const direct = isShogiTarget(edge.specifier, resolved);
    if (direct !== undefined) { found = `${direct} (via ${path.relative(PLAYTEST, absFile)})`; break; }
    if (resolved === undefined || coreSet.has(resolved)) continue;
    const deeper = reachesShogi(resolved, coreSet, memo, stack);
    if (deeper !== undefined) { found = deeper; break; }
  }
  stack.delete(absFile);
  memo.set(absFile, found);
  return found;
}

export function tsViolationsOf(relFile: string, edges: readonly Edge[], coreSet: ReadonlySet<string>, memo: Map<string, string | undefined>): BoundaryViolation[] {
  const absFile = path.join(PLAYTEST, relFile);
  const out: BoundaryViolation[] = [];
  for (const edge of edges) {
    if (edge.kind === "text") { out.push({ file: relFile, specifier: edge.specifier, kind: edge.kind, reaches: "report-pdf" }); continue; }
    if (edge.specifier.startsWith("<")) { out.push({ file: relFile, specifier: edge.specifier, kind: edge.kind, reaches: "unknown" }); continue; }
    if (edge.specifier.startsWith("node:")) continue;
    const resolved = edge.specifier.startsWith(".") ? resolveRelative(absFile, edge.specifier) : undefined;
    const direct = isShogiTarget(edge.specifier, resolved);
    if (direct !== undefined) { out.push({ file: relFile, specifier: edge.specifier, kind: edge.kind, reaches: direct }); continue; }
    if (resolved === undefined || coreSet.has(resolved)) continue;
    const deeper = reachesShogi(resolved, coreSet, memo);
    if (deeper !== undefined) out.push({ file: relFile, specifier: edge.specifier, kind: edge.kind, reaches: deeper });
  }
  return out;
}

// ==================== Python の走査 ====================

const PY_AST_SCRIPT = `
import ast, json, sys
out = {}
for f in sys.argv[1:]:
    rows = []
    tree = ast.parse(open(f, encoding="utf-8").read(), f)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names: rows.append({"module": a.name, "line": n.lineno})
        elif isinstance(n, ast.ImportFrom):
            rows.append({"module": ("." * n.level) + (n.module or ""), "line": n.lineno})
    out[f] = rows
print(json.dumps(out))
`;

export function pyImportsOf(absFiles: readonly string[]): Record<string, { module: string; line: number }[]> {
  const result = spawnSync("python3", ["-X", "utf8", "-c", PY_AST_SCRIPT, ...absFiles], { encoding: "utf-8" });
  if (result.status !== 0) throw new Error(`python3 の ast 走査が落ちた: ${result.stderr}`);
  return JSON.parse(result.stdout) as Record<string, { module: string; line: number }[]>;
}

export function pyViolationsOf(relFile: string, imports: readonly { module: string }[]): BoundaryViolation[] {
  const shogi = new Set<string>(SHOGI_PY_MODULES);
  const out: BoundaryViolation[] = [];
  const seen = new Set<string>();
  for (const imp of imports) {
    const top = imp.module.replace(/^\.+/, "").split(".")[0] ?? "";
    if (!shogi.has(top) || seen.has(top)) continue;
    seen.add(top);
    out.push({ file: `report-pdf/${relFile}`, specifier: top, kind: "runtime", reaches: top });
  }
  return out;
}

// ==================== 実物の走査 ====================

const CORE_TS_ALL: readonly string[] = [...CORE_TS_PURE, ...CORE_TS_A_PRIME];
const CORE_SET: ReadonlySet<string> = new Set(CORE_TS_ALL.map((f) => path.join(PLAYTEST, f)));
const CORE_PY_ALL: readonly string[] = [...CORE_PY_PURE, ...CORE_PY_A_PRIME];

function keyOf(v: BoundaryViolation): string {
  return `${v.file} → ${v.specifier} [${v.kind}]`;
}

function measureAll(): BoundaryViolation[] {
  const memo = new Map<string, string | undefined>();
  const found: BoundaryViolation[] = [];
  for (const relFile of CORE_TS_ALL) found.push(...tsViolationsOf(relFile, tsEdgesOf(sourceFileOf(path.join(PLAYTEST, relFile))), CORE_SET, memo));
  const pyAbs = CORE_PY_ALL.map((f) => path.join(PLAYTEST, "report-pdf", f));
  const pyImports = pyImportsOf(pyAbs);
  for (const relFile of CORE_PY_ALL) found.push(...pyViolationsOf(relFile, pyImports[path.join(PLAYTEST, "report-pdf", relFile)] ?? []));
  return found;
}

describe("Core 境界(Core 候補 → 将棋側の逆依存)", () => {
  it("Core 候補のファイルは全部在る(名前が変わったら気づく)", () => {
    for (const f of CORE_TS_ALL) expect(existsSync(path.join(PLAYTEST, f)), f).toBe(true);
    for (const f of CORE_PY_ALL) expect(existsSync(path.join(PLAYTEST, "report-pdf", f)), f).toBe(true);
    for (const m of SHOGI_PY_MODULES) expect(existsSync(path.join(PLAYTEST, "report-pdf", `${m}.py`)), m).toBe(true);
  });

  it("将棋依存なしと分類した候補(PURE)からは、例外に無い逆依存が 0 本", () => {
    const measured = measureAll();
    const pure = new Set<string>([...CORE_TS_PURE, ...CORE_PY_PURE.map((f) => `report-pdf/${f}`)]);
    const known = new Set(KNOWN_EXCEPTIONS.map(keyOf));
    expect(measured.filter((v) => pure.has(v.file) && !known.has(keyOf(v))).map(keyOf)).toEqual([]);
  });

  it("新しい逆依存は 0 本(既知の例外に無い辺は落ちる)", () => {
    const known = new Set(KNOWN_EXCEPTIONS.map(keyOf));
    const fresh = measureAll().filter((v) => !known.has(keyOf(v)));
    expect(fresh.map((v) => `${keyOf(v)} → ${v.reaches}`)).toEqual([]);
  });

  it("既知の例外は全部まだ実物に在り、届く先も同じ(外したら例外から消す ― 消し忘れが赤になる向き)", () => {
    const measured = new Map(measureAll().map((v) => [keyOf(v), v] as const));
    expect(KNOWN_EXCEPTIONS.filter((e) => !measured.has(keyOf(e))).map(keyOf)).toEqual([]);
    const moved = KNOWN_EXCEPTIONS.filter((e) => measured.get(keyOf(e))?.reaches !== e.reaches).map((e) => `${keyOf(e)}: 例外 ${e.reaches} / 実測 ${String(measured.get(keyOf(e))?.reaches)}`);
    expect(moved).toEqual([]);
  });

  it("例外は 1 件ずつ理由がある・重複が無い・候補のファイルを指す", () => {
    const keys = KNOWN_EXCEPTIONS.map(keyOf);
    expect(new Set(keys).size).toBe(keys.length);
    const files = new Set<string>([...CORE_TS_ALL, ...CORE_PY_ALL.map((f) => `report-pdf/${f}`)]);
    for (const e of KNOWN_EXCEPTIONS) {
      expect(e.reason.length, keyOf(e)).toBeGreaterThan(0);
      expect(files.has(e.file), keyOf(e)).toBe(true);
    }
  });
});

describe("走査器の陽性対照(検出器が効いていることを、ファイルを変えずに確かめる)", () => {
  const memo = new Map<string, string | undefined>();
  const probe = "lib/__boundary_probe__.ts";
  const violations = (src: string): BoundaryViolation[] => tsViolationsOf(probe, tsEdgesOf(parseSynthetic(src)), CORE_SET, memo);

  it("`shogiops` の静的 import は runtime として捕まる", () => {
    const v = violations('import { parseSfen } from "shogiops/sfen.js";\n');
    expect(v.map(keyOf)).toEqual([`${probe} → shogiops/sfen.js [runtime]`]);
    expect(v[0]?.reaches).toBe("shogiops");
  });

  it("`apps/server` への相対 import(型だけ)は type として捕まる", () => {
    const v = violations('import type { StateResponse } from "../../../apps/server/src/api/stateResponse.js";\n');
    expect(v.map(keyOf)).toEqual([`${probe} → ../../../apps/server/src/api/stateResponse.js [type]`]);
    expect(v[0]?.reaches).toBe("apps/server");
  });

  it("指定子ごとに `type` だけの import も type として捕まる(`import { type X }`)", () => {
    const v = violations('import { type MetaLine } from "../invariants/types.js";\n');
    expect(v.map(keyOf)).toEqual([`${probe} → ../invariants/types.js [type]`]);
  });

  it("Core 候補の外を経由して将棋に届く import も捕まる(`./reportData.js`)", () => {
    const v = violations('import { TIME_VALUES } from "./reportData.js";\n');
    expect(v.map(keyOf)).toEqual([`${probe} → ./reportData.js [runtime]`]);
    expect(v[0]?.reaches).toBe("apps/server (via invariants/types.ts)");
  });

  it("`export … from`・`import()`・`require()`・`report-pdf/` の文字列も捕まる", () => {
    const src = 'export { TIME_VALUES } from "./reportData.js";\nconst a = await import("shogiops");\nconst b = require("./reportData.js");\nconst c = new URL("../report-pdf/check_answer.py", import.meta.url);\n';
    expect(violations(src).map(keyOf)).toEqual([
      `${probe} → ./reportData.js [runtime]`,
      `${probe} → shogiops [dynamic]`,
      `${probe} → ./reportData.js [require]`,
      `${probe} → ../report-pdf/check_answer.py [text]`,
    ]);
  });

  it("文字列でない `import()` は unknown として捕まる(黙って通さない)", () => {
    const v = violations('const m = "./x.js";\nconst a = await import(m);\n');
    expect(v.map((x) => `${keyOf(x)} → ${x.reaches}`)).toEqual([`${probe} → <non-literal import()> [dynamic] → unknown`]);
  });

  it("Core 候補どうし・node:・外部ライブラリ・コメント中の語・出どころの名札は 0 本(陰性対照)", () => {
    const src = '// report-pdf/check_answer.py を読む、と書いたコメント\nconst label = "scripts/playtest/report-pdf/exit_groups.py AHEAD_CP";\nimport { readFileSync } from "node:fs";\nimport { validate } from "./eventSchema.js";\nimport { Prng } from "./prng.js";\nimport * as ast from "typescript/unstable/ast";\n';
    expect(violations(src)).toEqual([]);
  });

  it("Python: 将棋側の module の import は捕まり(同じ module は 1 回)、候補どうし・標準ライブラリは 0 本", () => {
    expect(pyViolationsOf("x.py", [{ module: "json" }, { module: "check_answer" }, { module: "fitz" }])).toEqual([]);
    expect(pyViolationsOf("x.py", [{ module: "exit_fill" }, { module: "exit_fill" }, { module: "board_draw" }]).map(keyOf))
      .toEqual(["report-pdf/x.py → exit_fill [runtime]", "report-pdf/x.py → board_draw [runtime]"]);
  });

  it("Python: 関数内の import も ast で拾える(exit_gate.py の `exit_fill` が実物の陽性対照)", () => {
    const file = path.join(PLAYTEST, "report-pdf", "exit_gate.py");
    const rows = pyImportsOf([file])[file] ?? [];
    expect(rows.filter((r) => r.module === "exit_fill").length).toBeGreaterThan(0);
  });
});
