// 次世代パイプライン Phase A の束 C(計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §4・§5b の D)。
// **provenance(出どころ・材料の封・閾値)の組み立てと、追跡性の検査。**
//
// 【顧客の PDF にどう出るか】今は何も変わらない。変わるのは、冊子の数から材料の実物まで
//   **機械で辿れる**ようになることだけ(人間の指示の試験 D)。
// 【参照方式】値ごとに出どころを埋め込むと provenance だけで約 3.6 MB(実測の行数から計算)。
//   行は符号(`src`)だけを持ち、符号 → 出どころ → 材料のパスと `sha256` をここで結ぶ(計画 §4)。
// 【閾値は「確かめた写し」】packet を読む側に閾値を推測させない(P-1)。
//   値は道具の定数から取る(`AHEAD_CP`・`TIME_VALUES`)が、**この層は将棋側の定数を読まない**(Audit Core T-4/I-3)。
//   表 `ThresholdRow[]` は packet の生産者(将棋側 `lib/observationFacts.ts` の `toolThresholds()`)が組み、
//   `provenanceOf` の `toolThresholds` で渡す。**写しが python 側・TS 側の定数と合っていることは将棋側の試験が突き合わせる。**
//   材料から読めるもの(エンジンの `minLossCp` など)は**写しではなく読んだ値**を入れる。
// 【D は「辿れた」で止めない】`sha256` を引いて**材料のファイルを実際に読み直し、同じ値になること**まで見る ―
//   参照が生きているだけでは、差し替わった材料を指していても緑になる(私から足した 1 点)。
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";

export class ObservationProvenanceError extends Error {
  override name = "ObservationProvenanceError";
}

export type ThresholdRow = { readonly id: string; readonly value: number; readonly unit: string; readonly from: string };
export type SourceRow = Record<string, unknown> & { readonly id: string; readonly type: string; readonly inputPaths: readonly string[] };
export type InputRow = { readonly path: string; readonly sha256: string; readonly bytes: number };

/**
 * jsonl の meta 行から 1 つの値を取る。**行ごとに違っていたら例外**(25 局が同じ設定で作られたことを確かめる) ―
 * 違う設定の材料を混ぜたまま「この閾値で作った」と書けば、それは嘘になる。
 */
export function metaValue(metaRows: readonly Record<string, unknown>[], keys: readonly string[], label: string): unknown {
  const seen = new Set<string>();
  let value: unknown;
  for (const row of metaRows) {
    let current: unknown = row;
    for (const key of keys) {
      if (current === null || typeof current !== "object") { current = undefined; break; }
      current = (current as Record<string, unknown>)[key];
    }
    if (current === undefined) continue;
    seen.add(JSON.stringify(current));
    value = current;
  }
  if (seen.size > 1) {
    throw new ObservationProvenanceError(`${label} が材料の中で ${seen.size} 通りある(${[...seen].slice(0, 3).join(" / ")}) ― 違う設定で作った材料が混ざっている`);
  }
  return value;
}

export type SourcesInput = {
  readonly inputsBySource: Readonly<Record<string, readonly string[]>>;
  readonly meta: { readonly read: readonly Record<string, unknown>[]; readonly whatif: readonly Record<string, unknown>[] };
  readonly sources: { readonly material: string; readonly engine: string; readonly engineShallow: string; readonly direct: string; readonly recognition: string };
  /** 認識の定義の下書き・レビュー状況(材料から読んだ値。ここで決めない) */
  readonly recognitionReviewStatus?: string;
};

/** 出どころの一覧(符号 → 何を読んだか)。**パスは読み手が組んだものをそのまま使う** */
export function sourcesOf(input: SourcesInput): SourceRow[] {
  const pathsOf = (id: string): readonly string[] => {
    const list = input.inputsBySource[id];
    if (list === undefined || list.length === 0) throw new ObservationProvenanceError(`出どころ ${id} で読んだ材料が無い`);
    return list;
  };
  const rows: SourceRow[] = [];
  rows.push({
    id: input.sources.material, type: "material",
    kind: "patient_report_data・sfens・time_cause(対局後診断の報告の材料)",
    inputPaths: pathsOf(input.sources.material),
  });
  rows.push({
    id: input.sources.direct, type: "material",
    kind: "direct_answers(浅い読みで差が見えた局面)",
    inputPaths: pathsOf(input.sources.direct),
  });
  const engineRow: Record<string, unknown> = {
    id: input.sources.engine, type: "engine", kind: "whatif-v2(分かれ道の候補と側)",
    inputPaths: pathsOf(input.sources.engine),
  };
  const whatifHead = metaValue(input.meta.whatif, ["gitHead"], "whatif-v2 の gitHead");
  const whatifNodes = metaValue(input.meta.whatif, ["values", "nodes"], "whatif-v2 の nodes");
  const whatifMultiPv = metaValue(input.meta.whatif, ["values", "multiPv"], "whatif-v2 の multiPv");
  if (typeof whatifHead === "string") engineRow.gitHead = whatifHead;
  if (typeof whatifNodes === "number") engineRow.nodesLimit = whatifNodes;
  if (typeof whatifMultiPv === "number") engineRow.multipv = whatifMultiPv;
  rows.push(engineRow as SourceRow);

  const shallowRow: Record<string, unknown> = {
    id: input.sources.engineShallow, type: "engine", kind: "read(浅い読み。分かれ道の見え方)",
    inputPaths: pathsOf(input.sources.engineShallow),
  };
  const readHead = metaValue(input.meta.read, ["gitHead"], "read の gitHead");
  const ladder = metaValue(input.meta.read, ["values", "nodeLadder"], "read の nodeLadder");
  if (typeof readHead === "string") shallowRow.gitHead = readHead;
  if (Array.isArray(ladder) && ladder.length > 0 && typeof ladder[ladder.length - 1] === "number") {
    shallowRow.nodesLimit = ladder[ladder.length - 1] as number;
  }
  rows.push(shallowRow as SourceRow);

  const recognitionRow: Record<string, unknown> = {
    id: input.sources.recognition, type: "recognition",
    kind: "opening_recognition と data/ の形の定義(機械認識)",
    inputPaths: pathsOf(input.sources.recognition),
  };
  if (input.recognitionReviewStatus !== undefined) recognitionRow.reviewStatus = input.recognitionReviewStatus;
  rows.push(recognitionRow as SourceRow);
  return rows;
}

/** 材料から読んだ閾値(写しではない)。read / whatif-v2 の meta にある値 */
export function materialThresholds(meta: SourcesInput["meta"]): ThresholdRow[] {
  const rows: ThresholdRow[] = [];
  const minLoss = metaValue(meta.whatif, ["values", "minLossCp"], "whatif-v2 の minLossCp");
  if (typeof minLoss === "number") {
    rows.push({ id: "branch_min_loss_cp", value: minLoss, unit: "centipawns", from: "材料 whatif-v2 の meta の values.minLossCp(読んだ値)" });
  }
  const ladder = metaValue(meta.read, ["values", "nodeLadder"], "read の nodeLadder");
  if (Array.isArray(ladder) && typeof ladder[0] === "number") {
    rows.push({ id: "shallow_first_nodes", value: ladder[0] as number, unit: "nodes", from: "材料 read の meta の values.nodeLadder[0](読んだ値)" });
  }
  return rows;
}

export type ProvenanceInput = SourcesInput & {
  readonly pipelineVersion: string;
  readonly generatedAt: string;
  readonly inputs: readonly InputRow[];
  /**
   * 道具の定数の写し(閾値の表)。**この層は作らない** ― packet の生産者(将棋側)が組んで渡す(Audit Core T-4/I-3)。
   * 既定値を持たない(渡し忘れは型検査で落ちる)。`materialThresholds` の前に、渡した順のまま並ぶ。
   */
  readonly toolThresholds: readonly ThresholdRow[];
};

export function provenanceOf(input: ProvenanceInput): Record<string, unknown> {
  return {
    pipelineVersion: input.pipelineVersion,
    generatedAt: input.generatedAt,
    sources: sourcesOf(input),
    inputs: input.inputs,
    thresholds: [...input.toolThresholds, ...materialThresholds(input.meta)],
  };
}

// ==================== 追跡性(人間の指示の試験 D) ====================

type PacketLike = {
  readonly facts?: Record<string, unknown>;
  readonly aggregates?: readonly Record<string, unknown>[];
  readonly provenance?: { readonly sources?: readonly Record<string, unknown>[]; readonly inputs?: readonly InputRow[] };
};

export type TraceOptions = {
  /** 材料を読み直す根(リポジトリの根)。渡さないとファイルを読み直さない(**その場合は「読み直していない」と言う**) */
  readonly repoRoot?: string;
  /** 読み直しを差し替えるための入口(試験用)。既定はファイルを読む */
  readonly readBytes?: (absolutePath: string) => Buffer;
};

/**
 * **冊子の数 → 集計の行 → derivedFrom の局 → 事実の行 → provenance.sources → 材料の `sha256`** を実際に辿る。
 * 空なら通った。`repoRoot` を渡すと**材料のファイルを読み直して `sha256` を突き合わせる**。
 */
export function traceProblems(packet: PacketLike, options: TraceOptions = {}): string[] {
  const problems: string[] = [];
  const facts = packet.facts ?? {};
  const aggregates = packet.aggregates ?? [];
  const sources = packet.provenance?.sources ?? [];
  const inputs = packet.provenance?.inputs ?? [];
  if (aggregates.length === 0) problems.push("D 追跡性: 集計の行が 0 件");

  const sourceById = new Map<string, Record<string, unknown>>();
  for (const source of sources) sourceById.set(String(source.id), source);
  const inputByPath = new Map<string, InputRow>();
  for (const input of inputs) inputByPath.set(input.path, input);

  // (1) 材料のどのファイルも、いずれかの出どころが名指ししている(名指しの無いファイルは辿れない)
  const claimed = new Set<string>();
  for (const source of sources) {
    const list = source.inputPaths;
    if (!Array.isArray(list)) {
      problems.push(`D 追跡性: 出どころ ${String(source.id)} に inputPaths が無い`);
      continue;
    }
    for (const value of list) {
      const filePath = String(value);
      claimed.add(filePath);
      if (!inputByPath.has(filePath)) problems.push(`D 追跡性: 出どころ ${String(source.id)} が名指しした ${filePath} が provenance.inputs に無い`);
    }
  }
  for (const input of inputs) {
    if (!claimed.has(input.path)) problems.push(`D 追跡性: 材料 ${input.path} をどの出どころも名指ししていない`);
  }

  // (2) 局の集合(derivedFrom の相手)
  const gameIds = new Set(((facts.games ?? []) as { gameId?: unknown }[]).map((row) => String(row.gameId)));

  // (2b) **事実の行の符号も出どころに着くこと。**
  // 集計 → 事実の行 → 材料、の途中が切れるのは行の側でも起きる(行ごとに `src`・`srcTop1Side` などを持つ)。
  // **見ていないと、行が知らない符号を指していても緑になる。**
  const factSources = new Set<string>();
  const rowGroups: Record<string, unknown>[][] = [];
  for (const key of ["games", "moves", "engine", "time", "branches", "collapse"]) {
    const rows = facts[key];
    if (Array.isArray(rows)) rowGroups.push(rows as Record<string, unknown>[]);
  }
  const recognitionPart = (facts.recognition ?? {}) as { rows?: Record<string, unknown>[]; definitions?: Record<string, unknown>[] };
  if (Array.isArray(recognitionPart.rows)) rowGroups.push(recognitionPart.rows);
  if (Array.isArray(recognitionPart.definitions)) rowGroups.push(recognitionPart.definitions);
  for (const rows of rowGroups) {
    for (const row of rows) {
      for (const [key, value] of Object.entries(row)) {
        if (!key.startsWith("src") || typeof value !== "string") continue;
        factSources.add(value);
      }
    }
  }
  for (const id of [...factSources].sort()) {
    if (!sourceById.has(id)) problems.push(`D 追跡性: 事実の行の符号「${id}」が provenance.sources に無い`);
  }

  // (3) 集計の行ごとに辿る
  const usedSources = new Set<string>();
  for (const row of aggregates) {
    const id = String(row.id ?? "id なし");
    const src = row.src === undefined ? undefined : String(row.src);
    if (src === undefined || !sourceById.has(src)) {
      problems.push(`D 追跡性: ${id} の src「${String(row.src)}」が provenance.sources に無い`);
    } else {
      usedSources.add(src);
    }
    for (const value of (row.srcExtra ?? []) as unknown[]) {
      const extra = String(value);
      if (!sourceById.has(extra)) problems.push(`D 追跡性: ${id} の srcExtra「${extra}」が provenance.sources に無い`);
      else usedSources.add(extra);
    }
    const derivedFrom = (row.derivedFrom ?? []) as unknown[];
    // **数が 0 の行は空でよい**(0 件の集合に局は無い)。0 でないのに空なら、どの局から出た数か辿れない
    const amount = typeof row.value === "number" ? row.value : typeof row.denominator === "number" ? row.denominator : undefined;
    if (derivedFrom.length === 0 && amount !== 0) {
      problems.push(`D 追跡性: ${id} に derivedFrom が無い(数は ${String(amount)} ― どの局から出た数か辿れない)`);
    }
    for (const value of derivedFrom) {
      if (!gameIds.has(String(value))) problems.push(`D 追跡性: ${id} の derivedFrom の局 ${String(value)} が facts.games に無い`);
    }
    // 事実の行まで降りる: その局の行が母集団の側に実在するか
    const population = row.population as { from?: unknown } | undefined;
    const from = population?.from === undefined ? undefined : String(population.from);
    if (from !== undefined) {
      const rows = from === "recognition"
        ? (((facts.recognition ?? {}) as { rows?: { gameId?: unknown }[] }).rows ?? [])
        : ((facts[from] ?? []) as { gameId?: unknown }[]);
      const inPopulation = new Set(rows.map((factRow) => String(factRow.gameId)));
      const missing = derivedFrom.map(String).filter((gameId) => !inPopulation.has(gameId));
      if (missing.length > 0) {
        problems.push(`D 追跡性: ${id} の局 ${missing.slice(0, 3).join("・")} の行が facts.${from} に無い`);
      }
    }
    // 出どころ → 材料のファイル(名指しが 1 本でも無ければ、材料まで降りられない)
    const source = src === undefined ? undefined : sourceById.get(src);
    const sourcePaths = (source?.inputPaths ?? []) as unknown[];
    if (source !== undefined && sourcePaths.length === 0) {
      problems.push(`D 追跡性: ${id} の出どころ ${String(src)} が材料のファイルを名指ししていない`);
    }
  }
  for (const source of sources) {
    // 事実の行が使っている符号も「使っている」に数える(集計の行だけが使い手ではない)
    if (factSources.has(String(source.id))) continue;
    if (!usedSources.has(String(source.id))) {
      problems.push(`D 追跡性: 出どころ ${String(source.id)} をどの集計の行も使っていない(要らない出どころか、src の付け忘れ)`);
    }
  }

  // (4) 材料の実物を読み直して `sha256` を突き合わせる(「辿れた」で止めない)
  if (options.repoRoot === undefined) {
    problems.push("D 追跡性: 材料を読み直していない(repoRoot が渡されていない) ― 参照が生きているだけでは、差し替わった材料を指していても気づけない");
  } else {
    const read = options.readBytes ?? ((absolutePath: string) => readFileSync(absolutePath));
    for (const input of inputs) {
      let bytes: Buffer;
      try {
        bytes = read(path.join(options.repoRoot, input.path));
      } catch (error) {
        problems.push(`D 追跡性: 材料 ${input.path} を読み直せない(${error instanceof Error ? error.message : String(error)})`);
        continue;
      }
      if (bytes.length !== input.bytes) {
        problems.push(`D 追跡性: 材料 ${input.path} の大きさが ${bytes.length}(封は ${input.bytes})`);
      }
      const sha256 = createHash("sha256").update(bytes).digest("hex");
      if (sha256 !== input.sha256) {
        problems.push(`D 追跡性: 材料 ${input.path} の指紋が変わっている(いま ${sha256.slice(0, 12)}… / 封 ${String(input.sha256).slice(0, 12)}…)`);
      }
    }
  }
  return problems;
}
