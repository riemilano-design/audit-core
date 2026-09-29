// 束 B の読み手の試験(2026-09-30 の独立監査の REVISE 2)。
//
// 【なぜ要るか】`lib/observationMaterials.ts` は **パスと `sha256`、そしてリポジトリの外を拒む門**を持つ唯一の層なのに、
// 試験が無かった。監査は手で「外のパスは例外になる」ことを確かめたが、**自動の網が無いと、
// この門が静かに壊れても vitest は気づけない**(束 A の §5e で「絶対パスとホームのユーザー名を出さない」を
// 束 B の条件として受けたので、閉じたなら試験も要る)。
//
// 【材料は一時フォルダに作る】実データ(`out/`)は gitignore なので門では読まない。**リポジトリにも書かない。**
// `readFactsMaterials` は `repoRoot` を引数で取るので、**一時フォルダを「根」として渡せば**
// 相対パスの規則も外を拒む門も、実ファイルで確かめられる。
import { createHash } from "node:crypto";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { ObservationMaterialsError, readFactsMaterials, type MaterialPaths } from "./observationMaterials.js";

const INITIAL = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

/** 実物の形をそのまま小さくした材料を、一時フォルダに書く(この「根」からの相対パスが返るはず) */
function makeMaterials(): { root: string; paths: MaterialPaths } {
  const root = mkdtempSync(path.join(tmpdir(), "obs-materials-"));
  const report = path.join(root, "report");
  const readDir = path.join(root, "read");
  const whatifDir = path.join(root, "whatif-v2");
  const definitionDir = path.join(root, "definitions");
  for (const dir of [report, readDir, whatifDir, definitionDir]) mkdirSync(dir, { recursive: true });

  const write = (file: string, value: unknown) => writeFileSync(file, JSON.stringify(value), "utf-8");
  write(path.join(report, "patient_report_data.json"), {
    person: "(実名のような値。packet には出ない)",
    games: [{ id: "g01", no: 1, side: "先手", result: "負け", plies: [0], total: 1 }],
    events: [],
  });
  write(path.join(report, "sfens.json"), { g01: { sfens: [INITIAL], moves: ["7g7f"], side: "sente" } });
  write(path.join(report, "time_cause.json"), { games: [{ kifuId: "g01", timeLimitSec: 180 }] });
  write(path.join(report, "direct_answers.json"), { answers: [{ kifuId: "g01", displayPly: 1 }] });
  write(path.join(report, "opening_recognition.json"), { rows: { g01: {} } });
  writeFileSync(path.join(readDir, "g01.jsonl"), [
    JSON.stringify({ kind: "meta", kifuId: "g01" }),
    JSON.stringify({ kind: "position", ply: 1, displayPly: 1, top1Move: "8g8f" }),
    "",
  ].join("\n"), "utf-8");
  writeFileSync(path.join(whatifDir, "g01.jsonl"), [
    JSON.stringify({ kind: "meta", kifuId: "g01" }),
    JSON.stringify({ kind: "position", ply: 1, displayPly: 1, sfen: INITIAL, candidates: [{ move: "8g8f", side: "attack" }] }),
    "",
  ].join("\n"), "utf-8");
  write(path.join(definitionDir, "onikoroshi.json"), { id: "onikoroshi", name: "鬼殺し", side: "self", review_status: "draft" });

  return {
    root,
    paths: {
      patient: path.join(report, "patient_report_data.json"),
      sfens: path.join(report, "sfens.json"),
      timeCause: path.join(report, "time_cause.json"),
      direct: path.join(report, "direct_answers.json"),
      recognition: path.join(report, "opening_recognition.json"),
      readDirs: [readDir],
      whatifDirs: [whatifDir],
      definitionDirs: [definitionDir],
    },
  };
}

describe("材料の読み手(パス・指紋・外を拒む門)", () => {
  it("h1 読めた材料が揃い、jsonl の position 行にファイル名の語幹が付く", () => {
    const { root, paths } = makeMaterials();
    const { materials } = readFactsMaterials(paths, root);
    expect(materials.patient.games).toHaveLength(1);
    expect(materials.readPositions).toHaveLength(1);
    expect(materials.readPositions[0]!.kifuId).toBe("g01");
    expect(materials.whatifPositions[0]!.kifuId).toBe("g01");
    // **meta 行は入らない**(position だけ)
    expect(materials.readPositions.every((row) => row.kind === "position")).toBe(true);
    expect(materials.definitions).toHaveLength(1);
  });

  it("h2 返すパスは必ず根からの相対(先頭が / でない・.. を含まない)", () => {
    const { root, paths } = makeMaterials();
    const { inputs } = readFactsMaterials(paths, root);
    expect(inputs.length).toBeGreaterThan(5);
    for (const input of inputs) {
      expect(input.path.startsWith("/"), `絶対パスが入っている: ${input.path}`).toBe(false);
      expect(input.path.includes(".."), `根の外を指している: ${input.path}`).toBe(false);
      expect(input.path.includes(path.sep === "/" ? "\\" : "/")).toBe(false);
    }
  });

  it("h3 根の外のファイルは例外(絶対パスとホームのユーザー名が載る経路を塞ぐ)", () => {
    const { root, paths } = makeMaterials();
    const other = makeMaterials();
    // **実在するが根の外**のファイルを渡す(存在しないファイルの例外と区別するため、実在させる)
    expect(() => readFactsMaterials({ ...paths, patient: other.paths.patient }, root)).toThrow(ObservationMaterialsError);
  });

  it("h4 指紋と大きさが実ファイルと合う", () => {
    const { root, paths } = makeMaterials();
    const { inputs } = readFactsMaterials(paths, root);
    for (const input of inputs) {
      const bytes = readFileSync(path.join(root, input.path));
      expect(input.bytes, input.path).toBe(bytes.length);
      expect(input.sha256, input.path).toBe(createHash("sha256").update(bytes).digest("hex"));
    }
  });

  it("h5 材料が壊れていれば読み手が言う(黙って空を返さない)", () => {
    const { root, paths } = makeMaterials();
    writeFileSync(path.join(root, "report", "patient_report_data.json"), JSON.stringify({ games: [] }), "utf-8");
    expect(() => readFactsMaterials(paths, root)).toThrow(ObservationMaterialsError);
    const { root: root2, paths: paths2 } = makeMaterials();
    writeFileSync(path.join(root2, "report", "direct_answers.json"), JSON.stringify({}), "utf-8");
    expect(() => readFactsMaterials(paths2, root2)).toThrow(ObservationMaterialsError);
  });

  it("h6 同じフォルダを 2 回渡すと材料が増える(**読み手は防がない** ― 増えたことは B の検査が言う)", () => {
    const { root, paths } = makeMaterials();
    const doubled = readFactsMaterials({ ...paths, definitionDirs: [paths.definitionDirs[0]!, paths.definitionDirs[0]!] }, root);
    expect(doubled.materials.definitions).toHaveLength(2);
    // ここで止めるのではなく、`completenessProblems` が「材料と数が違う」と言う側で捕まえる
    // (読み手は写すだけ・検査は 1 か所、という線を崩さない)
  });
});
