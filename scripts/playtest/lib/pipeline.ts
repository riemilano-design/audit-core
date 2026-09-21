// STEP PIPE 作業 A(docs/STEP_PIPE_PLAN_2026-09-21.md §2.1)。scripts/playtest/pipeline.ts の純粋な部分。
//
// 【このファイルがやること】
// - 局の一覧づくり(--kifu-dir の中の .kif 等から、--me かファイル名の末尾 -sente/-gote で先後を決める)
// - 段ごとの「済み」の判定(段 1 は最後の行が summary、段 2 は空でない、fixed は id と moves がある、diagnose は 4 つの出力がすべてある、gate は出力がある)
// - 既存の道具(kifu-import-check.ts・replay.ts・rescreen.ts・diagnose.ts・gate.ts)へ渡す引数の組み立て(docs/STEP_PIPE_PLAN_2026-09-21.md §1 の表の値に固定)
// - 上限つきの並行実行(runWithLimit)と、失敗を止めずに集める実行(runPipeline)
// - --dry-run 用の読み取り専用のプレビュー(planPipeline。何も書かず・何も実行しない)
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・評価・閾値・文言。エンジン・子プロセスを直接起こすこと(fs・run は呼び出し側が注入する)。
// - records/ へ書くこと。--records-append を足すこと(gateCommand は常に付けない)。
// - 既存の道具(kifu-import-check.ts・replay.ts・rescreen.ts・diagnose.ts・gate.ts)の中身の複製・改変。

import path from "node:path";
import { fileURLToPath } from "node:url";

import type { MetaLine } from "../invariants/types.js";
import { userSideOf, type UserSide } from "./condition.js";

// ---- 段の一覧(司令塔が後で足せる形。--until の値もここから出す) ----

export type Stage = "import" | "evaluate" | "diagnose" | "gate";
export const STAGES: readonly Stage[] = ["import", "evaluate", "diagnose", "gate"];

// ---- 引数の解釈 ----

export class PipelineArgError extends Error {}

export interface PipelineArgs {
  person: string;
  kifuDir: string;
  work: string;
  me: string | undefined;
  parallel: number;
  compareDirs: string[];
  comparePerson: string | undefined;
  until: Stage;
  evaluator: string | undefined;
  dryRun: boolean;
}

const SINGLE_FLAGS = ["--person", "--kifu-dir", "--work", "--me", "--parallel", "--compare-person", "--until", "--evaluator"] as const;
type SingleFlag = (typeof SINGLE_FLAGS)[number];

const DEFAULT_PARALLEL = 5;

/**
 * `--compare-dir` は繰り返し可(値を連続していくつでも取る)。**役割(司令塔 e3 の直し、2026-09-21)**:
 * `--person`・`--kifu-dir` の局(このお客さん)が **gate.ts の材料の側**(`--person`・`--material`)、
 * `--compare-dir` の記録が **gate.ts の試す側**(`--test-person`・`--test-sente`/`--test-gote`)。
 * 2 人目 20 局(材料)を 1 人目 10 局(試す側)で確かめた C-1・C-5 の正式な実行と同じ向き
 * (docs/STEP_D3-COND_PLAN_2026-09-15.md §14・§15.2)。
 * 計画 §2.1 の CLI にある「試す側の人のラベル」は表に無いため、`--compare-person`(p1・p2 の形の記号。
 * gate.ts 自身が形を確かめる)を新設した。`--compare-dir` と `--compare-person` は必ず一緒に渡す
 * (片方だけは止める)。この判断は計画に書かれていないため、報告でその旨を明記する。
 */
export function parsePipelineArgs(argv: readonly string[]): PipelineArgs {
  const single = new Map<SingleFlag, string>();
  const compareDirs: string[] = [];
  let dryRun = false;

  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i]!;
    if (flag === "--dry-run") {
      dryRun = true;
      continue;
    }
    if (flag === "--compare-dir") {
      i += 1;
      let took = 0;
      while (i < argv.length && !argv[i]!.startsWith("--")) {
        compareDirs.push(argv[i]!);
        took += 1;
        i += 1;
      }
      if (took === 0) throw new PipelineArgError("--compare-dir に値が無い");
      i -= 1;
      continue;
    }
    if ((SINGLE_FLAGS as readonly string[]).includes(flag)) {
      const value = argv[i + 1];
      if (value === undefined || value.startsWith("--")) throw new PipelineArgError(`${flag} に値が無い`);
      if (single.has(flag as SingleFlag)) throw new PipelineArgError(`${flag} が 2 回ある`);
      single.set(flag as SingleFlag, value);
      i += 1;
      continue;
    }
    throw new PipelineArgError(`知らない引数: ${flag}`);
  }

  const person = single.get("--person");
  const kifuDir = single.get("--kifu-dir");
  const work = single.get("--work");
  if (person === undefined || kifuDir === undefined || work === undefined) {
    throw new PipelineArgError("--person・--kifu-dir・--work は必須");
  }

  const parallelRaw = single.get("--parallel") ?? String(DEFAULT_PARALLEL);
  const parallel = Number(parallelRaw);
  if (!Number.isInteger(parallel) || parallel <= 0) throw new PipelineArgError(`--parallel は正の整数: ${parallelRaw}`);

  const untilRaw = single.get("--until") ?? STAGES[STAGES.length - 1]!;
  if (!(STAGES as readonly string[]).includes(untilRaw)) throw new PipelineArgError(`--until は ${STAGES.join("|")} のいずれか: ${untilRaw}`);

  const comparePerson = single.get("--compare-person");
  if (compareDirs.length > 0 && comparePerson === undefined) throw new PipelineArgError("--compare-dir を渡すときは --compare-person も渡す");
  if (compareDirs.length === 0 && comparePerson !== undefined) throw new PipelineArgError("--compare-person は --compare-dir と一緒に渡す");

  return {
    person,
    kifuDir,
    work,
    me: single.get("--me"),
    parallel,
    compareDirs,
    comparePerson,
    until: untilRaw as Stage,
    evaluator: single.get("--evaluator"),
    dryRun,
  };
}

// ---- 局の一覧づくり(先後: --me か、ファイル名の末尾 -sente/-gote。どちらも無ければ止まる) ----

export const KIF_EXTENSIONS = [".kif", ".kifu", ".csa", ".ki2"] as const;

export class PipelineConfigError extends Error {}

export type SideMode = { kind: "me"; me: string } | { kind: "filenameSuffix"; side: "sente" | "gote" };

export interface GameJob {
  id: string;
  /** 道具の第一引数に渡す実ファイルパス(`--kifu-dir` を含む)。 */
  kifPath: string;
  /** `--kifu-dir` からの相対パス(このファイルはフラットな一覧なのでファイル名そのもの)。`--source` に使う
   * (司令塔 e3 の直し、2026-09-21: 固定棋譜に /Users/ を含む絶対パスを残さないため)。 */
  kifName: string;
  sideMode: SideMode;
}

const FILENAME_SIDE_SUFFIX = /^(.+)-(sente|gote)$/;

/** `--kifu-dir` 直下のファイル名の一覧(`fs.listFiles` の結果)から局の一覧を作る。局の並びは id の昇順。 */
export function listGames(kifuDir: string, fileNames: readonly string[], me: string | undefined): GameJob[] {
  const kifFiles = fileNames
    .filter((name) => (KIF_EXTENSIONS as readonly string[]).includes(path.extname(name).toLowerCase()))
    .slice()
    .sort();

  const jobs = kifFiles.map((name): GameJob => {
    const base = name.slice(0, name.length - path.extname(name).length);
    const kifPath = path.join(kifuDir, name);
    if (me !== undefined) return { id: base, kifPath, kifName: name, sideMode: { kind: "me", me } };
    const match = FILENAME_SIDE_SUFFIX.exec(base);
    if (match === null) {
      throw new PipelineConfigError(`${name}: --me が無く、ファイル名の末尾が -sente / -gote でもない(先後を推測しない)`);
    }
    return { id: match[1]!, kifPath, kifName: name, sideMode: { kind: "filenameSuffix", side: match[2] as "sente" | "gote" } };
  });

  return jobs.slice().sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}

// ---- 出力先のパス(--work の下。作業ディレクトリの構成) ----

export function personWorkDir(work: string, person: string): string {
  return path.join(work, person);
}

export interface GamePaths {
  fixedKifuPath: string;
  stage1Path: string;
  stage2Path: string;
}

export function gamePaths(personDir: string, id: string): GamePaths {
  return {
    fixedKifuPath: path.join(personDir, "kifu", `${id}.fixed.json`),
    stage1Path: path.join(personDir, "stage1", `${id}.jsonl`),
    stage2Path: path.join(personDir, "stage2", `${id}.jsonl`),
  };
}

export interface DiagnosePaths {
  events: string;
  rise: string;
  maxdrop: string;
  md: string;
}

export function diagnoseDir(personDir: string): string {
  return path.join(personDir, "diagnose");
}

export function diagnosePaths(personDir: string): DiagnosePaths {
  const dir = diagnoseDir(personDir);
  return {
    events: path.join(dir, "events.jsonl"),
    rise: path.join(dir, "rise.jsonl"),
    maxdrop: path.join(dir, "maxdrop.jsonl"),
    md: path.join(dir, "diagnose.md"),
  };
}

export function gateOutPath(personDir: string): string {
  return path.join(personDir, "gate.jsonl");
}

export function timingPath(work: string): string {
  return path.join(work, "timing.jsonl");
}

/** `--conditions`(表の値 `lib/conditions`)。このファイルからの相対で固定する(scripts/playtest/lib/conditions)。 */
const LIB_DIR = path.dirname(fileURLToPath(import.meta.url));
export const CONDITIONS_DIR = path.join(LIB_DIR, "conditions");

// ---- 既存の道具へ渡す引数(計画 §1 の表の値に固定。表と違う値を渡す旗は作らない) ----

export const STAGE1_NODES = 400_000;
export const STAGE1_REFERENCE_NODES = 400_000;
export const STAGE1_THREADS = 1;
export const STAGE1_DIRECTION_RULE = "current";
export const STAGE2_DEEP_NODES = 4_000_000;

export type ToolName = "kifu-import-check" | "replay" | "rescreen" | "diagnose" | "gate";

/** `--source` は `--kifu-dir` からの相対パス(ファイル名)。計画は自由記述としか書いておらず、値を新しく作らないための
 * 判断だが、絶対パス(`job.kifPath`)をそのまま使うと /Users/ を含むパスが固定棋譜に残るため、相対の名前にした
 * (司令塔 e3 の直し、2026-09-21)。第一引数(実ファイルの位置)は道具が読む必要があるので絶対 / 指定どおりのパスのまま。 */
export function importCommand(job: GameJob, fixedOutPath: string): string[] {
  const base = [job.kifPath, "--fixed", fixedOutPath, "--id", job.id, "--source", job.kifName];
  return job.sideMode.kind === "me" ? [...base, "--me", job.sideMode.me] : [...base, "--as", job.sideMode.side];
}

export function replayCommand(fixedKifuPath: string, stage1OutPath: string): string[] {
  return [
    fixedKifuPath,
    "--nodes",
    String(STAGE1_NODES),
    "--reference-nodes",
    String(STAGE1_REFERENCE_NODES),
    "--threads",
    String(STAGE1_THREADS),
    "--direction-rule",
    STAGE1_DIRECTION_RULE,
    "--out",
    stage1OutPath,
  ];
}

export function rescreenCommand(stage1Path: string, stage2OutPath: string): string[] {
  return [stage1Path, "--out", stage2OutPath, "--deep-nodes", String(STAGE2_DEEP_NODES)];
}

export function diagnoseCommand(stage2Paths: readonly string[], eventsOut: string, riseOut: string, maxdropOut: string, evaluator: string | undefined): string[] {
  const args = [...stage2Paths, "--events", eventsOut, "--events-rise", riseOut, "--events-maxdrop", maxdropOut];
  if (evaluator !== undefined) args.push("--evaluator", evaluator);
  return args;
}

/** `--records-append` は決して足さない(棄却の記録へ書くのは、予測を先にコミットした正式な実行だけ。司令塔が手で回す)。 */
export function gateCommand(
  materialPerson: string,
  testPerson: string,
  materialFiles: readonly string[],
  testSenteFiles: readonly string[],
  testGoteFiles: readonly string[],
  conditionsDir: string,
  out: string,
): string[] {
  const args = ["--person", materialPerson, "--test-person", testPerson, "--material", ...materialFiles, "--test-sente", ...testSenteFiles];
  if (testGoteFiles.length > 0) args.push("--test-gote", ...testGoteFiles);
  args.push("--conditions", conditionsDir, "--out", out);
  return args;
}

// ---- 段ごとの「済み」の判定(Lishogi の run-game.sh と同じ判定) ----

export function fixedKifuDone(content: string | undefined, expectedId: string): boolean {
  if (content === undefined) return false;
  let parsed: unknown;
  try {
    parsed = JSON.parse(content);
  } catch {
    return false;
  }
  if (typeof parsed !== "object" || parsed === null) return false;
  const obj = parsed as { id?: unknown; moves?: unknown };
  return obj.id === expectedId && Array.isArray(obj.moves);
}

/** 段 1: 最後の行が summary であること(run-game.sh の `tail -1 | grep '"kind":"summary"'` と同じ判定)。 */
export function stage1Done(content: string | undefined): boolean {
  if (content === undefined) return false;
  const lines = content
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
  const last = lines[lines.length - 1];
  if (last === undefined) return false;
  try {
    const parsed = JSON.parse(last) as { kind?: unknown };
    return parsed.kind === "summary";
  } catch {
    return false;
  }
}

/** 段 2: 空でないこと(run-game.sh の `[ ! -s "$s2" ]` の否定と同じ判定)。 */
export function stage2Done(content: string | undefined): boolean {
  return content !== undefined && content.trim().length > 0;
}

/** S3: 3 つの JSONL と Markdown がすべてある(diagnose.ts は 3 つのファイルを揃えて書く。S-8 参照)。 */
export function diagnoseDone(events: string | undefined, rise: string | undefined, maxdrop: string | undefined, md: string | undefined): boolean {
  return [events, rise, maxdrop, md].every((content) => content !== undefined && content.trim().length > 0);
}

/** S4: gate.jsonl がある(0 本の定義でも空のファイルとして書かれるため、存在だけを見る)。 */
export function gateDone(exists: boolean): boolean {
  return exists;
}

// ---- meta 行を読む(段 1・段 2 の JSONL の 1 行目。gate の先手 / 後手の振り分けに使う) ----

export function readMetaLine(content: string): MetaLine | undefined {
  for (const raw of content.split("\n")) {
    const line = raw.trim();
    if (line.length === 0) continue;
    let parsed: unknown;
    try {
      parsed = JSON.parse(line);
    } catch {
      continue;
    }
    if (typeof parsed === "object" && parsed !== null && (parsed as { kind?: unknown }).kind === "meta") return parsed as MetaLine;
    // meta 行は先頭にあるはずだが、無ければ次の行も見る(壊れた記録を誤って meta とみなさないため kind を確かめる)
  }
  return undefined;
}

/** 段 2 の meta から本人の側を読む(condition.ts の userSideOf をそのまま使う。判定ロジックは複製しない)。読めなければ null。 */
export function sideOfStage2(content: string): UserSide | null {
  const meta = readMetaLine(content);
  try {
    return userSideOf(meta);
  } catch {
    return null;
  }
}

// ---- 上限つきの並行実行(1 局の失敗で他が止まらず、順序を保って結果を返す) ----

export interface JobResult<T> {
  job: T;
  ok: boolean;
  error: unknown;
}

export async function runWithLimit<T>(jobs: readonly T[], limit: number, worker: (job: T) => Promise<void>): Promise<JobResult<T>[]> {
  const results: JobResult<T>[] = new Array(jobs.length);
  let next = 0;
  const lane = async (): Promise<void> => {
    for (;;) {
      const index = next;
      next += 1;
      if (index >= jobs.length) return;
      const job = jobs[index]!;
      try {
        await worker(job);
        results[index] = { job, ok: true, error: undefined };
      } catch (error) {
        results[index] = { job, ok: false, error };
      }
    }
  };
  const laneCount = Math.min(limit, jobs.length);
  await Promise.all(Array.from({ length: laneCount }, () => lane()));
  return results;
}

// ---- 所要の記録(work/timing.jsonl) ----

export interface TimingEntry {
  gameId: string;
  startedAt: string;
  finishedAt: string;
  rc: number | "skip";
}

export function timingLineOf(entry: TimingEntry): string {
  return `${JSON.stringify(entry)}\n`;
}

// ---- 呼び出し側が注入する副作用(fs・道具の実行) ----

export interface PipelineFs {
  /** ファイルが無ければ undefined(存在と内容を同時に見る。symptom-not-yet-verified: 成果物そのもので確かめる) */
  readText(filePath: string): string | undefined;
  writeText(filePath: string, content: string): void;
  appendText(filePath: string, content: string): void;
  ensureDir(dirPath: string): void;
  /** ディレクトリ直下のファイル名の一覧(非再帰)。無ければ空配列。 */
  listFiles(dirPath: string): string[];
}

export interface ToolResult {
  code: number;
  stdout: string;
  stderr: string;
}

export type ToolRunner = (tool: ToolName, args: readonly string[]) => Promise<ToolResult>;

export interface PipelineFailure {
  gameId: string;
  stage: string;
  message: string;
}

export interface PipelineResult {
  failures: PipelineFailure[];
  timingLines: string[];
  exitCode: number;
}

interface GameOutcome {
  ok: boolean;
  stage2Path: string;
}

/**
 * 実行する(fs へ書き、run を呼ぶ)。1 局の失敗で他を止めない。最後に失敗の一覧と、
 * 失敗が 1 件でもあれば 0 でない exitCode を返す。**--records-append は付けない・records/ へは書かない**
 * (gateCommand 自体が付けないので、ここでも新しい引数を足さない)。
 */
export async function runPipeline(args: PipelineArgs, games: readonly GameJob[], fs: PipelineFs, run: ToolRunner, clock: () => string = () => new Date().toISOString()): Promise<PipelineResult> {
  const personDir = personWorkDir(args.work, args.person);
  fs.ensureDir(args.work);
  fs.ensureDir(path.join(personDir, "kifu"));
  const untilRank = STAGES.indexOf(args.until);

  const failures: PipelineFailure[] = [];
  const timingLines: string[] = [];
  const outcomes = new Map<string, GameOutcome>();
  const tPath = timingPath(args.work);

  async function processGame(job: GameJob): Promise<void> {
    const startedAt = clock();
    const gp = gamePaths(personDir, job.id);
    let ok = true;
    let rc: number | "skip" = "skip";

    const fixedExisting = fs.readText(gp.fixedKifuPath);
    if (!fixedKifuDone(fixedExisting, job.id)) {
      fs.ensureDir(path.join(personDir, "kifu"));
      const result = await run("kifu-import-check", importCommand(job, gp.fixedKifuPath));
      rc = result.code;
      if (!fixedKifuDone(fs.readText(gp.fixedKifuPath), job.id)) {
        ok = false;
        failures.push({ gameId: job.id, stage: "import", message: `kifu-import-check.ts rc=${result.code}: fixed 棋譜が出来ていない` });
      }
    }

    if (ok && untilRank >= STAGES.indexOf("evaluate")) {
      const s1Existing = fs.readText(gp.stage1Path);
      if (!stage1Done(s1Existing)) {
        const result = await run("replay", replayCommand(gp.fixedKifuPath, gp.stage1Path));
        rc = result.code;
        if (!stage1Done(fs.readText(gp.stage1Path))) {
          ok = false;
          failures.push({ gameId: job.id, stage: "evaluate-replay", message: `replay.ts rc=${result.code}: 段 1 の記録が出来ていない` });
        }
      }
    }

    if (ok && untilRank >= STAGES.indexOf("evaluate")) {
      const s2Existing = fs.readText(gp.stage2Path);
      if (!stage2Done(s2Existing)) {
        fs.ensureDir(path.join(personDir, "stage2"));
        const result = await run("rescreen", rescreenCommand(gp.stage1Path, gp.stage2Path));
        rc = result.code;
        if (!stage2Done(fs.readText(gp.stage2Path))) {
          ok = false;
          failures.push({ gameId: job.id, stage: "evaluate-rescreen", message: `rescreen.ts rc=${result.code}: 段 2 の記録が出来ていない` });
        }
      }
    }

    const finishedAt = clock();
    const line = timingLineOf({ gameId: job.id, startedAt, finishedAt, rc });
    timingLines.push(line);
    fs.appendText(tPath, line);

    if (ok && untilRank >= STAGES.indexOf("evaluate")) {
      outcomes.set(job.id, { ok: true, stage2Path: gp.stage2Path });
    } else {
      outcomes.set(job.id, { ok: false, stage2Path: gp.stage2Path });
    }
  }

  fs.ensureDir(path.join(personDir, "stage1"));
  if (untilRank >= STAGES.indexOf("evaluate")) fs.ensureDir(path.join(personDir, "stage2"));

  const jobResults = await runWithLimit(games, args.parallel, processGame);
  for (const result of jobResults) {
    if (!result.ok && result.error !== undefined) {
      failures.push({ gameId: result.job.id, stage: "unexpected", message: result.error instanceof Error ? result.error.message : String(result.error) });
    }
  }

  if (untilRank >= STAGES.indexOf("diagnose")) {
    const successGames = games.filter((job) => outcomes.get(job.id)?.ok === true);
    const stage2Paths = successGames.map((job) => outcomes.get(job.id)!.stage2Path);
    const dp = diagnosePaths(personDir);
    const already = diagnoseDone(fs.readText(dp.events), fs.readText(dp.rise), fs.readText(dp.maxdrop), fs.readText(dp.md));
    if (!already) {
      if (stage2Paths.length === 0) {
        failures.push({ gameId: "*", stage: "diagnose", message: "段 2 まで済んだ局が 0 なので診断できない" });
      } else {
        fs.ensureDir(diagnoseDir(personDir));
        const result = await run("diagnose", diagnoseCommand(stage2Paths, dp.events, dp.rise, dp.maxdrop, args.evaluator));
        fs.writeText(dp.md, result.stdout);
        if (!diagnoseDone(fs.readText(dp.events), fs.readText(dp.rise), fs.readText(dp.maxdrop), fs.readText(dp.md))) {
          failures.push({ gameId: "*", stage: "diagnose", message: `diagnose.ts rc=${result.code}: 出力が揃っていない` });
        }
      }
    }
  }

  if (untilRank >= STAGES.indexOf("gate") && args.compareDirs.length > 0) {
    const gOut = gateOutPath(personDir);
    const already = gateDone(fs.readText(gOut) !== undefined);
    if (!already) {
      // 材料の側 = このお客さん(--person・--kifu-dir)の段 2(先手・後手を分けない、gate.ts の --material はそのまま渡す)
      const materialFiles = games.filter((job) => outcomes.get(job.id)?.ok === true).map((job) => outcomes.get(job.id)!.stage2Path);
      // 試す側 = --compare-dir の記録(先後は各記録の meta 行から読む。ファイル名には頼らない。決められない記録があれば推測せず失敗にする)
      const compareFiles = args.compareDirs.flatMap((dir) =>
        fs
          .listFiles(dir)
          .filter((name) => name.endsWith(".jsonl"))
          .sort()
          .map((name) => path.join(dir, name)),
      );
      const testSente: string[] = [];
      const testGote: string[] = [];
      const undetermined: string[] = [];
      for (const file of compareFiles) {
        const content = fs.readText(file);
        const side = content === undefined ? null : sideOfStage2(content);
        if (side === "sente") testSente.push(file);
        else if (side === "gote") testGote.push(file);
        else undetermined.push(file);
      }
      if (undetermined.length > 0) {
        failures.push({ gameId: "*", stage: "gate", message: `--compare-dir の記録の本人の側が meta から決められない(推測しない): ${undetermined.join(", ")}` });
      } else if (materialFiles.length === 0) {
        failures.push({ gameId: "*", stage: "gate", message: "材料(このお客さんの段 2)が 0 局なので gate できない" });
      } else if (testSente.length === 0 && testGote.length === 0) {
        failures.push({ gameId: "*", stage: "gate", message: "--compare-dir に *.jsonl が無い" });
      } else {
        const result = await run("gate", gateCommand(args.person, args.comparePerson!, materialFiles, testSente, testGote, CONDITIONS_DIR, gOut));
        if (!gateDone(fs.readText(gOut) !== undefined)) {
          failures.push({ gameId: "*", stage: "gate", message: `gate.ts rc=${result.code}: 出力が出来ていない` });
        }
      }
    }
  }

  return { failures, timingLines, exitCode: failures.length > 0 ? 1 : 0 };
}

// ---- --dry-run 用のプレビュー(何も書かず・何も実行しない) ----

export interface PlannedStep {
  gameId: string;
  stage: "import" | "evaluate-replay" | "evaluate-rescreen" | "diagnose" | "gate";
  tool: ToolName;
  args: string[];
  action: "run" | "skip";
  reason: string;
}

/**
 * 読み取り専用のプレビュー。**fs.readText / fs.listFiles しか呼ばない**(writeText・appendText・ensureDir・run は呼ばない)。
 * diagnose・gate の対象は「現時点ですでに段 2 まで済んでいる局」だけ(これから実行して済むはずの局は、実行するまで成否が分からないため含めない)。
 */
export function planPipeline(args: PipelineArgs, games: readonly GameJob[], fs: PipelineFs): PlannedStep[] {
  const personDir = personWorkDir(args.work, args.person);
  const untilRank = STAGES.indexOf(args.until);
  const steps: PlannedStep[] = [];
  const doneStage2: string[] = [];

  for (const job of games) {
    const gp = gamePaths(personDir, job.id);
    const fixedContent = fs.readText(gp.fixedKifuPath);
    const importOk = fixedKifuDone(fixedContent, job.id);
    steps.push({
      gameId: job.id,
      stage: "import",
      tool: "kifu-import-check",
      args: importCommand(job, gp.fixedKifuPath),
      action: importOk ? "skip" : "run",
      reason: importOk ? "fixed 済み" : "fixed 未作成",
    });
    if (untilRank < STAGES.indexOf("evaluate")) continue;

    const s1Content = fs.readText(gp.stage1Path);
    const s1Ok = stage1Done(s1Content);
    steps.push({
      gameId: job.id,
      stage: "evaluate-replay",
      tool: "replay",
      args: replayCommand(gp.fixedKifuPath, gp.stage1Path),
      action: s1Ok ? "skip" : "run",
      reason: s1Ok ? "段 1 済み" : "段 1 未実施",
    });

    const s2Content = fs.readText(gp.stage2Path);
    const s2Ok = stage2Done(s2Content);
    steps.push({
      gameId: job.id,
      stage: "evaluate-rescreen",
      tool: "rescreen",
      args: rescreenCommand(gp.stage1Path, gp.stage2Path),
      action: s2Ok ? "skip" : "run",
      reason: s2Ok ? "段 2 済み" : "段 2 未実施",
    });

    if (s2Ok) doneStage2.push(gp.stage2Path);
  }

  if (untilRank >= STAGES.indexOf("diagnose")) {
    const dp = diagnosePaths(personDir);
    const already = diagnoseDone(fs.readText(dp.events), fs.readText(dp.rise), fs.readText(dp.maxdrop), fs.readText(dp.md));
    const notReady = games.length - doneStage2.length;
    steps.push({
      gameId: "*",
      stage: "diagnose",
      tool: "diagnose",
      args: diagnoseCommand(doneStage2, dp.events, dp.rise, dp.maxdrop, args.evaluator),
      action: already ? "skip" : "run",
      reason: already ? "診断済み" : `段 2 済みの ${doneStage2.length} 局を対象にする見込み(${notReady} 局はまだ段 2 が済んでいない)`,
    });
  }

  if (untilRank >= STAGES.indexOf("gate") && args.compareDirs.length > 0) {
    const gOut = gateOutPath(personDir);
    const already = gateDone(fs.readText(gOut) !== undefined);
    // 試す側 = --compare-dir の記録。先後は各記録の meta 行から読む(ファイル名には頼らない)
    const compareFiles = args.compareDirs.flatMap((dir) =>
      fs
        .listFiles(dir)
        .filter((name) => name.endsWith(".jsonl"))
        .sort()
        .map((name) => path.join(dir, name)),
    );
    const testSente: string[] = [];
    const testGote: string[] = [];
    let undeterminedCount = 0;
    for (const file of compareFiles) {
      const content = fs.readText(file);
      const side = content === undefined ? null : sideOfStage2(content);
      if (side === "sente") testSente.push(file);
      else if (side === "gote") testGote.push(file);
      else undeterminedCount += 1;
    }
    steps.push({
      gameId: "*",
      stage: "gate",
      tool: "gate",
      // 材料の側 = このお客さん(doneStage2。今すでに段 2 が済んでいる局だけ)
      args: gateCommand(args.person, args.comparePerson ?? "", doneStage2, testSente, testGote, CONDITIONS_DIR, gOut),
      action: already ? "skip" : "run",
      reason: already
        ? "gate 済み"
        : `材料(このお客さん)${doneStage2.length} 局・試す側(--compare-dir)先手 ${testSente.length} 局・後手 ${testGote.length} 局を対象にする見込み${undeterminedCount > 0 ? `(本人の側が読めない記録 ${undeterminedCount} 件があり、実行時はこの段が失敗になる)` : ""}`,
    });
  }

  return steps;
}
