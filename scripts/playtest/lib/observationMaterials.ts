// 束 B の読み手(計画 docs/PLAN_OBSERVATION_PACKET_2026-09-30.md §3)。
// **既存の材料のファイルを読んで `FactsMaterials` にするだけ。**判定も集計もしない。
//
// 【なぜ読み手を分けるか】`lib/observationFacts.ts` は**読んだ値**を受け取る(試験が合成材料で回せる)。
//   パスと `sha256` を扱うのはこの層だけにする。
// 【provenance の材料の一覧】読んだファイルの `path`(リポジトリの根からの相対)・`sha256`・`bytes` を返す。
//   **絶対パスとホームのユーザー名を出さない**(既存の契約と同じ規則。監査が束 B の条件として挙げた点)。
// 【jsonl の `kifuId`】position 行は `kifuId` を持たない(実測)。**ファイル名の語幹を付ける** ―
//   既存の `check_answer.side_match_of` と同じやり方(判定ではなく写し)。
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import type { DefinitionRecord, DirectAnswer, FactsMaterials, FactsSources, PatientData, ReadPosition, RecognitionData, SfensData, TimeCauseData, WhatifPosition } from "./observationFacts.js";

export class ObservationMaterialsError extends Error {
  override name = "ObservationMaterialsError";
}

export type MaterialInput = { readonly path: string; readonly sha256: string; readonly bytes: number };

export type MaterialPaths = {
  readonly patient: string;
  readonly sfens: string;
  readonly timeCause: string;
  readonly direct: string;
  readonly recognition: string;
  readonly readDirs: readonly string[];
  readonly whatifDirs: readonly string[];
  readonly definitionDirs: readonly string[];
};

/** 既定の出どころの符号(provenance.sources の id と対で使う) */
export const DEFAULT_SOURCES: FactsSources = {
  material: "m1",
  engine: "e1",
  engineShallow: "e2",
  direct: "d1",
  recognition: "r1",
};

function repoRelative(filePath: string, repoRoot: string): string {
  const resolved = path.resolve(filePath);
  const relative = path.relative(path.resolve(repoRoot), resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new ObservationMaterialsError(`リポジトリの外のファイルは材料にしない: ${filePath}`);
  }
  return relative.split(path.sep).join("/");
}

function readWithInput(filePath: string, repoRoot: string, inputs: MaterialInput[]): unknown {
  const bytes = readFileSync(filePath);
  inputs.push({ path: repoRelative(filePath, repoRoot), sha256: createHash("sha256").update(bytes).digest("hex"), bytes: bytes.length });
  return JSON.parse(bytes.toString("utf-8"));
}

/**
 * フォルダの `*.jsonl` の position 行を、ファイル名の語幹を `kifuId` として付けて並べる。
 * **meta 行も別に集める**(束 C。provenance の出どころに「どのエンジンの設定で作ったか」を入れるため ―
 * 実物の meta 行は `gitHead`・`values.nodes`・`values.multiPv`・`values.minLossCp` を持つ)。
 */
function readPositionRows(dirs: readonly string[], repoRoot: string, inputs: MaterialInput[], metaRows: Record<string, unknown>[]): Record<string, unknown>[] {
  const rows: Record<string, unknown>[] = [];
  for (const dir of dirs) {
    for (const name of readdirSync(dir).sort()) {
      if (!name.endsWith(".jsonl")) continue;
      const filePath = path.join(dir, name);
      const bytes = readFileSync(filePath);
      inputs.push({ path: repoRelative(filePath, repoRoot), sha256: createHash("sha256").update(bytes).digest("hex"), bytes: bytes.length });
      const kifuId = name.replace(/\.jsonl$/, "");
      for (const line of bytes.toString("utf-8").split("\n")) {
        const trimmed = line.trim();
        if (trimmed === "") continue;
        const row = JSON.parse(trimmed) as Record<string, unknown>;
        if (row.kind === "meta") {
          metaRows.push({ ...row, kifuId });
          continue;
        }
        if (row.kind !== "position") continue;
        rows.push({ ...row, kifuId });
      }
    }
  }
  return rows;
}

function readDefinitions(dirs: readonly string[], repoRoot: string, inputs: MaterialInput[]): DefinitionRecord[] {
  const records: DefinitionRecord[] = [];
  for (const dir of dirs) {
    for (const name of readdirSync(dir).sort()) {
      if (!name.endsWith(".json")) continue;
      const filePath = path.join(dir, name);
      if (!statSync(filePath).isFile()) continue;
      records.push(readWithInput(filePath, repoRoot, inputs) as DefinitionRecord);
    }
  }
  return records;
}

export type ReadMaterialsResult = {
  readonly materials: FactsMaterials;
  readonly inputs: readonly MaterialInput[];
  /**
   * 出どころの符号 → その出どころで読んだファイルのパス(束 C)。
   * **provenance の sources[].inputPaths になる** ― 集計の行の `src` から材料の `sha256` まで
   * 機械で辿れるようにするため(人間の指示の試験 D)。**読みながら組む**(後から順番で復元しない)。
   */
  readonly inputsBySource: Readonly<Record<string, readonly string[]>>;
  /** jsonl の meta 行(read / whatif-v2)。**provenance の出どころの欄に使う。facts には入れない** */
  readonly meta: { readonly read: readonly Record<string, unknown>[]; readonly whatif: readonly Record<string, unknown>[] };
};

export function readFactsMaterials(paths: MaterialPaths, repoRoot: string, sources: FactsSources = DEFAULT_SOURCES): ReadMaterialsResult {
  const inputs: MaterialInput[] = [];
  const bySource: Record<string, string[]> = {};
  /** 読んだ分のパスを、その出どころの符号に付ける(読みながら組む) */
  const under = <T,>(sourceId: string, read: () => T): T => {
    const before = inputs.length;
    const value = read();
    const list = bySource[sourceId] ?? [];
    for (const input of inputs.slice(before)) list.push(input.path);
    bySource[sourceId] = list;
    return value;
  };
  const patient = under(sources.material, () => readWithInput(paths.patient, repoRoot, inputs)) as PatientData;
  const sfens = under(sources.material, () => readWithInput(paths.sfens, repoRoot, inputs)) as SfensData;
  const timeCause = under(sources.material, () => readWithInput(paths.timeCause, repoRoot, inputs)) as TimeCauseData;
  const directFile = under(sources.direct, () => readWithInput(paths.direct, repoRoot, inputs)) as { answers?: DirectAnswer[] };
  const recognition = under(sources.recognition, () => readWithInput(paths.recognition, repoRoot, inputs)) as RecognitionData;
  const readMeta: Record<string, unknown>[] = [];
  const whatifMeta: Record<string, unknown>[] = [];
  const readPositions = under(sources.engineShallow, () => readPositionRows(paths.readDirs, repoRoot, inputs, readMeta)) as unknown as ReadPosition[];
  const whatifPositions = under(sources.engine, () => readPositionRows(paths.whatifDirs, repoRoot, inputs, whatifMeta)) as unknown as WhatifPosition[];
  const definitions = under(sources.recognition, () => readDefinitions(paths.definitionDirs, repoRoot, inputs));
  if (!Array.isArray(patient.games) || patient.games.length === 0) throw new ObservationMaterialsError("patient_report_data に games が無い");
  if (!Array.isArray(directFile.answers)) throw new ObservationMaterialsError("direct_answers に answers が無い");
  const materials: FactsMaterials = {
    patient,
    sfens,
    timeCause,
    readPositions,
    whatifPositions,
    directAnswers: directFile.answers,
    recognition,
    definitions,
    sources,
  };
  return { materials, inputs, inputsBySource: bySource, meta: { read: readMeta, whatif: whatifMeta } };
}
