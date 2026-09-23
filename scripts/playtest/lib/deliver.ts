// STEP DELIVER-1(docs/STEP_DELIVER1_PLAN_2026-09-25.md §3 の 3)。scripts/playtest/deliver.ts の純粋な部分。
//
// 【このファイルがやること】
// - 引数の解釈(parseDeliverArgs)
// - 組の一覧づくり(groupListOf。付録 3・付録 4・B の検査で組をまたいで合算する組の、順序つきの一覧)
// - 段ごとのコマンドの組み立て(既存の道具へ渡す引数の並び。手で組んでいた 4 本の .sh を機械で再現するもの)
// - 段ごとの「済み」の判定(出力が既にあれば飛ばす。lib/pipeline.ts と同じ流儀)
// - 納品ログの行(deliverLogLineOf)と、--out の安全装置(unexpectedOutFiles)
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・評価・閾値・文言。新しい分析指標・新しい集計。子プロセスの起動・fs(呼び出し側が注入する)。
// - 既存の道具(reportData.ts・read.ts・directAnswers.ts・finalPositions.ts・timeCause.ts・timeSearch.ts・
//   answerMenu.ts・report-pdf/ の python)の中身の複製・改変。**呼び方だけ**を決める。

import path from "node:path";

// ---- 段の一覧(計画 §3 の 3 の順。司令塔の指示書 §3.3 の表) ----

export type DeliverStage =
  | "pipeline-data"
  | "prose-gate"
  | "pipeline-pdf"
  | "deliverables-pdf"
  | "appendix3-answers"
  | "appendix3-final"
  | "appendix3-pdf"
  | "appendix4-cause"
  | "appendix4-search"
  | "appendix4-pdf"
  | "answer-menu"
  | "answer-draft"
  | "answer-gate"
  | "answer-check"
  | "answer-pdf"
  | "check-delivery";

export const DELIVER_STAGES: readonly DeliverStage[] = [
  "pipeline-data",
  "prose-gate",
  "pipeline-pdf",
  "deliverables-pdf",
  "appendix3-answers",
  "appendix3-final",
  "appendix3-pdf",
  "appendix4-cause",
  "appendix4-search",
  "appendix4-pdf",
  "answer-menu",
  "answer-draft",
  "answer-gate",
  "answer-check",
  "answer-pdf",
  "check-delivery",
];

/** 段ごとに起こす道具(呼び出し側が実際の実行ファイルへ対応させる)。`copy` と `gate` は子プロセスを起こさない。 */
export type DeliverTool =
  | "pipeline"
  | "direct-answers"
  | "final-positions"
  | "time-cause"
  | "time-search"
  | "answer-menu"
  | "render-direct"
  | "render-time-cause"
  | "answer-facts"
  | "check-answer"
  | "render-answer"
  | "check-delivery"
  | "copy"
  | "gate";

// ---- 顧客フォルダの中の名前(司令塔が決めた固定の名前。判断を持たない) ----

export const DELIVER_OUT_NAMES = {
  front: "1_まとめ.pdf",
  main: "2_付録1_形勢が動いた対局.pdf",
  whatif: "3_付録2_分かれ道.pdf",
  appendix3: "5_付録3_直接の答え.pdf",
  appendix4: "6_付録4_時間の使い方.pdf",
  answerDraft: "8_B_どうしたら_下書き.md",
  answerPdf: "8_B_どうしたら.pdf",
  directDir: "direct",
  log: "deliver_log.jsonl",
} as const;

export const DELIVER_DIRECT_NAMES = {
  directAnswers: "direct_answers.json",
  finalPositions: "final_positions.json",
  timeCause: "time_cause.json",
  timeSearch: "time_cause_search.json",
  answerMenu: "answer_menu.json",
} as const;

/** B の下書きで「読み」を人が埋める場所の印(計画 §3 の 4)。`answer-gate` はこの印が残っていれば止まる。 */
export const TODO_MARK = "<!-- TODO: 読み -->";

export interface DeliverOutPaths {
  front: string;
  main: string;
  whatif: string;
  appendix3: string;
  appendix4: string;
  answerDraft: string;
  answerPdf: string;
  directDir: string;
  log: string;
  directAnswers: string;
  finalPositions: string;
  timeCause: string;
  timeSearch: string;
  answerMenu: string;
}

export function deliverOutPaths(out: string): DeliverOutPaths {
  const directDir = path.join(out, DELIVER_OUT_NAMES.directDir);
  return {
    front: path.join(out, DELIVER_OUT_NAMES.front),
    main: path.join(out, DELIVER_OUT_NAMES.main),
    whatif: path.join(out, DELIVER_OUT_NAMES.whatif),
    appendix3: path.join(out, DELIVER_OUT_NAMES.appendix3),
    appendix4: path.join(out, DELIVER_OUT_NAMES.appendix4),
    answerDraft: path.join(out, DELIVER_OUT_NAMES.answerDraft),
    answerPdf: path.join(out, DELIVER_OUT_NAMES.answerPdf),
    directDir,
    log: path.join(out, DELIVER_OUT_NAMES.log),
    directAnswers: path.join(directDir, DELIVER_DIRECT_NAMES.directAnswers),
    finalPositions: path.join(directDir, DELIVER_DIRECT_NAMES.finalPositions),
    timeCause: path.join(directDir, DELIVER_DIRECT_NAMES.timeCause),
    timeSearch: path.join(directDir, DELIVER_DIRECT_NAMES.timeSearch),
    answerMenu: path.join(directDir, DELIVER_DIRECT_NAMES.answerMenu),
  };
}

/** 組ごとの `final_positions_<i>.json`(i は組の順の 1 始まり。連結前の中間ファイル)。 */
export function finalPositionsPartPath(out: string, groupIndex: number): string {
  return path.join(out, DELIVER_OUT_NAMES.directDir, `final_positions_${groupIndex + 1}.json`);
}

const FINAL_POSITIONS_PART_RE = /^final_positions_\d+\.json$/;

/**
 * `--out` の安全装置(司令塔の判断。指示書 §3.3)。`deliver.ts` 自身が書く名前**以外**のファイル名を返す。
 * 空でなければ呼び出し側は何もせず止まる(既存の顧客フォルダを取り違えて上書きしないため)。
 * `outNames`・`directNames` は、それぞれ `<out>` 直下・`<out>/direct/` 直下の実際のファイル名の一覧。
 */
export function unexpectedOutFiles(outNames: readonly string[], directNames: readonly string[]): string[] {
  const allowedTop = new Set<string>(Object.values(DELIVER_OUT_NAMES));
  const allowedDirect = new Set<string>(Object.values(DELIVER_DIRECT_NAMES));
  const unexpected: string[] = [];
  for (const name of outNames) {
    if (!allowedTop.has(name)) unexpected.push(name);
  }
  for (const name of directNames) {
    if (allowedDirect.has(name) || FINAL_POSITIONS_PART_RE.test(name)) continue;
    unexpected.push(path.join(DELIVER_OUT_NAMES.directDir, name));
  }
  return unexpected;
}

// ---- 引数の解釈 ----

export class DeliverArgError extends Error {}

/** 組 1 つ = 1 つの `--work` と、その組の持ち時間(秒)。順序が付録 3・付録 4・検査の引数の並びを決める。 */
export interface DeliverGroup {
  work: string;
  timeLimitSec: number;
}

export interface DeliverArgs {
  person: string;
  kifuDir: string;
  work: string;
  timeLimitSec: number;
  name: string;
  title: string;
  today: string;
  out: string;
  /** 渡されたときだけキーが付く(`lib/pipeline.ts` の任意のキーと同じ流儀)。 */
  previousWork?: string;
  parallel?: number;
  from?: DeliverStage;
  /** 組の一覧(順序つき。必ず 1 つ以上で、`work` をちょうど 1 回含む)。 */
  groups: DeliverGroup[];
  forbid: string[];
  dryRun: boolean;
}

const SINGLE_FLAGS = ["--person", "--kifu-dir", "--work", "--time-limit-sec", "--name", "--title", "--today", "--out", "--previous-work", "--parallel", "--from"] as const;
type SingleFlag = (typeof SINGLE_FLAGS)[number];

function positiveIntOf(flag: string, raw: string): number {
  const value = Number(raw);
  if (!Number.isInteger(value) || value <= 0) throw new DeliverArgError(`${flag} は正の整数: ${raw}`);
  return value;
}

/**
 * `--group-work <work> --group-time-limit-sec <秒>` は**対で同じ回数**並べる(司令塔の判断。指示書 §3.3)。
 * 渡さないときの既定 = `[--previous-work(あれば、秒は --time-limit-sec), --work]` の順。
 * 渡したときは `--work` が一覧にちょうど 1 回含まれていること・`--previous-work` も(渡したなら)含まれていることを確かめる。
 */
export function parseDeliverArgs(argv: readonly string[]): DeliverArgs {
  const single = new Map<SingleFlag, string>();
  const groupWorks: string[] = [];
  const groupSecs: string[] = [];
  const forbid: string[] = [];
  let dryRun = false;

  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i]!;
    if (flag === "--dry-run") {
      dryRun = true;
      continue;
    }
    const value = argv[i + 1];
    if (flag === "--group-work" || flag === "--group-time-limit-sec" || flag === "--forbid") {
      if (value === undefined || value.startsWith("--")) throw new DeliverArgError(`${flag} に値が無い`);
      if (flag === "--group-work") groupWorks.push(value);
      else if (flag === "--group-time-limit-sec") groupSecs.push(value);
      else forbid.push(value);
      i += 1;
      continue;
    }
    if ((SINGLE_FLAGS as readonly string[]).includes(flag)) {
      if (value === undefined || value.startsWith("--")) throw new DeliverArgError(`${flag} に値が無い`);
      if (single.has(flag as SingleFlag)) throw new DeliverArgError(`${flag} が 2 回ある`);
      single.set(flag as SingleFlag, value);
      i += 1;
      continue;
    }
    throw new DeliverArgError(`知らない引数: ${flag}`);
  }

  const person = single.get("--person");
  const kifuDirRaw = single.get("--kifu-dir");
  const workRaw = single.get("--work");
  const timeLimitRaw = single.get("--time-limit-sec");
  const name = single.get("--name");
  const title = single.get("--title");
  const today = single.get("--today");
  const outRaw = single.get("--out");
  if (person === undefined || kifuDirRaw === undefined || workRaw === undefined || timeLimitRaw === undefined || name === undefined || title === undefined || today === undefined || outRaw === undefined) {
    throw new DeliverArgError("--person・--kifu-dir・--work・--time-limit-sec・--name・--title・--today・--out は必須");
  }

  // `--work` と同じ理由で、パスは受け取った時点で絶対パスにする(lib/pipeline.ts の parsePipelineArgs と同じ)。
  const kifuDir = path.resolve(kifuDirRaw);
  const work = path.resolve(workRaw);
  const out = path.resolve(outRaw);
  const timeLimitSec = positiveIntOf("--time-limit-sec", timeLimitRaw);
  const previousWorkRaw = single.get("--previous-work");
  const previousWork = previousWorkRaw === undefined ? undefined : path.resolve(previousWorkRaw);
  const parallelRaw = single.get("--parallel");
  const parallel = parallelRaw === undefined ? undefined : positiveIntOf("--parallel", parallelRaw);

  const fromRaw = single.get("--from");
  if (fromRaw !== undefined && !(DELIVER_STAGES as readonly string[]).includes(fromRaw)) {
    throw new DeliverArgError(`--from は ${DELIVER_STAGES.join("|")} のいずれか: ${fromRaw}`);
  }
  const from = fromRaw as DeliverStage | undefined;

  if (groupWorks.length !== groupSecs.length) {
    throw new DeliverArgError(`--group-work(${groupWorks.length} 個)と --group-time-limit-sec(${groupSecs.length} 個)は対で同じ回数`);
  }

  let groups: DeliverGroup[];
  if (groupWorks.length === 0) {
    // 既定 = [前回(あれば), 今回] の順。前回の秒は --time-limit-sec と同じとみなす(通常の 2 回目のお客さん)。
    groups = previousWork === undefined ? [{ work, timeLimitSec }] : [{ work: previousWork, timeLimitSec }, { work, timeLimitSec }];
  } else {
    groups = groupWorks.map((w, index) => ({ work: path.resolve(w), timeLimitSec: positiveIntOf("--group-time-limit-sec", groupSecs[index]!) }));
    const workCount = groups.filter((g) => g.work === work).length;
    if (workCount !== 1) throw new DeliverArgError(`--group-work の一覧に --work がちょうど 1 回含まれていない(${workCount} 回)`);
    if (previousWork !== undefined && !groups.some((g) => g.work === previousWork)) {
      throw new DeliverArgError("--group-work の一覧に --previous-work が含まれていない");
    }
  }

  return {
    person,
    kifuDir,
    work,
    timeLimitSec,
    name,
    title,
    today,
    out,
    ...(previousWork !== undefined ? { previousWork } : {}),
    ...(parallel !== undefined ? { parallel } : {}),
    ...(from !== undefined ? { from } : {}),
    groups,
    forbid,
    dryRun,
  };
}

// ---- 組ごとのパス(`--work` の下の構成。lib/pipeline.ts の personWorkDir・reportPaths と同じ場所) ----

export interface GroupPaths {
  work: string;
  timeLimitSec: number;
  personDir: string;
  fixedKifuDir: string;
  stage2Dir: string;
  whatifV2Dir: string;
  readDir: string;
  typeSummary: string;
  reportDir: string;
  patient: string;
  whatifData: string;
  whatifPdf: string;
  frontPdf: string;
  mainPdf: string;
  prose: string;
  proseRequest: string;
}

export function groupPaths(group: DeliverGroup, person: string): GroupPaths {
  const personDir = path.join(group.work, person);
  const reportDir = path.join(group.work, "report");
  return {
    work: group.work,
    timeLimitSec: group.timeLimitSec,
    personDir,
    fixedKifuDir: path.join(personDir, "kifu"),
    stage2Dir: path.join(personDir, "stage2"),
    whatifV2Dir: path.join(personDir, "whatif-v2"),
    readDir: path.join(personDir, "read"),
    typeSummary: path.join(personDir, "type-summary.json"),
    reportDir,
    patient: path.join(reportDir, "patient_report_data.json"),
    whatifData: path.join(reportDir, "whatif_report_data.json"),
    whatifPdf: path.join(reportDir, "whatif.pdf"),
    frontPdf: path.join(reportDir, "front.pdf"),
    mainPdf: path.join(reportDir, "main.pdf"),
    prose: path.join(reportDir, "prose.json"),
    proseRequest: path.join(reportDir, "prose-request.md"),
  };
}

export function groupListOf(args: DeliverArgs): GroupPaths[] {
  return args.groups.map((g) => groupPaths(g, args.person));
}

/** 呼び出し側が注入する「見えているもの」(fs の読み取りだけ。書き込み・実行はしない)。 */
export interface DeliverProbe {
  exists(filePath: string): boolean;
  /** そのフォルダに `*.jsonl` が 1 つ以上あるか(無いフォルダは false)。 */
  hasJsonl(dirPath: string): boolean;
  /** そのフォルダの `*.fixed.json` の一覧(絶対パス。名前の昇順)。無ければ空配列。 */
  fixedKifuFiles(dirPath: string): string[];
  /**
   * `patient_report_data.json` の `time.timeUpLosses` の件数(読めなければ 0)。
   * `finalPositions.ts` は対象 0 件で rc=1 になるため、0 件の組はこの段を飛ばす(実装担当の判断。報告に明記)。
   */
  timeUpLossCount(patientPath: string): number;
}

// ---- 段ごとのコマンドの組み立て ----

/** `pipeline.ts` へ渡す引数(段 1・段 3。`--until` だけが違う)。 */
export function pipelineCommand(args: DeliverArgs, until: "report-data" | "pdf"): string[] {
  const out = ["--person", args.person, "--kifu-dir", args.kifuDir, "--work", args.work];
  if (args.parallel !== undefined) out.push("--parallel", String(args.parallel));
  out.push("--whatif", "--until", until, "--name", args.name, "--title", args.title, "--today", args.today, "--time-limit-sec", String(args.timeLimitSec));
  if (args.previousWork !== undefined) {
    out.push("--previous", path.join(args.previousWork, "report", "patient_report_data.json"));
  }
  return out;
}

/** 組のうち `read/` がある組だけ(順序は組の順)。`--whatif-v2-dir`・`--read-dir` の対はこの一覧で決まる。 */
export function groupsWithRead(groups: readonly GroupPaths[], probe: DeliverProbe): GroupPaths[] {
  return groups.filter((g) => probe.hasJsonl(g.readDir));
}

/**
 * 段 5(`directAnswers.ts`)。`read/` がある組だけ、組の順に `--whatif-v2-dir`・`--read-dir` の対を並べ、
 * そのあとに同じ順で `--time-limit-sec` を並べる(`make_direct.sh` と同じ並び)。
 */
export function directAnswersCommand(groups: readonly GroupPaths[], outPath: string): string[] {
  const out: string[] = [];
  for (const g of groups) out.push("--whatif-v2-dir", g.whatifV2Dir, "--read-dir", g.readDir);
  for (const g of groups) out.push("--time-limit-sec", String(g.timeLimitSec));
  out.push("--out", outPath);
  return out;
}

/** 段 6(`finalPositions.ts`)。1 回の実行で 1 つの組(`make_direct.sh` と同じ)。 */
export function finalPositionsCommand(group: GroupPaths, kifuFiles: readonly string[], outPath: string): string[] {
  return ["--kifu", ...kifuFiles, "--patient", group.patient, "--time-limit-sec", String(group.timeLimitSec), "--out", outPath];
}

/**
 * 段 6 の連結。**先頭のファイルのメタ + `entries` を順に連結**する(司令塔が既存の `final_positions.json` と
 * 突き合わせて確認済み。指示書 §2)。数は 1 つも作らない ― 並べ替えもしない。
 */
export function mergeFinalPositions(parts: readonly Record<string, unknown>[]): Record<string, unknown> {
  if (parts.length === 0) throw new DeliverArgError("連結する final_positions が 0 件");
  const entries: unknown[] = [];
  for (const part of parts) {
    const rows = part["entries"];
    if (!Array.isArray(rows)) throw new DeliverArgError("final_positions に entries が無い");
    entries.push(...rows);
  }
  return { ...parts[0]!, entries };
}

/** 段 7(`render_direct.py`)の `REPORT_DATA_DIR`(組の report を**組の順**でカンマ区切り)。 */
export function reportDataDirEnv(groups: readonly GroupPaths[]): string {
  return groups.map((g) => g.reportDir).join(",");
}

export function renderDirectCommand(directAnswersPath: string, finalPositionsPath: string, outPdf: string): string[] {
  return [directAnswersPath, finalPositionsPath, outPdf];
}

/**
 * 段 8(`timeCause.ts`)。全組を組の順に。`--kifu-dir` が出るたびに新しい組が始まる形式(`timeCause.ts` の
 * 引数の読み方どおり)。`--whatif-v2-dir` は **`whatif-v2/` がある組だけ**に付ける。
 */
export function timeCauseCommand(groups: readonly GroupPaths[], probe: DeliverProbe, outPath: string): string[] {
  const out: string[] = [];
  for (const g of groups) {
    out.push("--kifu-dir", g.fixedKifuDir, "--patient", g.patient, "--time-limit-sec", String(g.timeLimitSec));
    if (probe.hasJsonl(g.whatifV2Dir)) out.push("--whatif-v2-dir", g.whatifV2Dir);
  }
  out.push("--out", outPath);
  return out;
}

/**
 * 段 9(`timeSearch.ts`)。`--role discover` = 前回の組、`--role validate` = 今回の組。
 * `--outcomes` は渡さない(既定 = 3 つ全部。指示書 §2)。
 */
export function timeSearchCommand(discover: GroupPaths, validate: GroupPaths, probe: DeliverProbe, outPath: string): string[] {
  const out: string[] = [];
  for (const [role, g] of [
    ["discover", discover],
    ["validate", validate],
  ] as const) {
    out.push("--role", role, "--kifu-dir", g.fixedKifuDir, "--records-dir", g.stage2Dir, "--time-limit-sec", String(g.timeLimitSec));
    if (probe.hasJsonl(g.whatifV2Dir)) out.push("--whatif-v2-dir", g.whatifV2Dir);
  }
  out.push("--out", outPath);
  return out;
}

/** 段 10(`render_time_cause.py`)。`--search` は探索の出力があるときだけ(`render_time_cause.py` の任意の旗)。 */
export function renderTimeCauseCommand(timeCausePath: string, outPdf: string, timeSearchPath: string | undefined): string[] {
  const out = [timeCausePath, outPdf];
  if (timeSearchPath !== undefined) out.push("--search", timeSearchPath);
  return out;
}

/**
 * 材料の旗を決めるための「この実行で何が出来るか」(**存在だけで決めない**ための情報)。
 * `--whatif-data`・`--whatif-pdf` は今回の組(`--work`)では段 3 が作るので、まだファイルが無くても渡す。
 * `--time-search` は段 9 が回るとき(= `--previous-work` があるとき)だけ渡す。
 * こうしないと `--dry-run` と実行時で引数が変わってしまう(照合できない)。
 */
export interface MaterialPlan {
  currentWork: string;
  hasSearch: boolean;
}

export function materialPlanOf(args: DeliverArgs): MaterialPlan {
  return { currentWork: args.work, hasSearch: args.previousWork !== undefined };
}

/** その組の `whatif_report_data.json` / `whatif.pdf` が、この実行の終わりまでに在るか。 */
function willHaveWhatif(group: GroupPaths, probe: DeliverProbe, plan: MaterialPlan, kind: "data" | "pdf"): boolean {
  if (group.work === plan.currentWork) return true; // 段 3(pipeline --until pdf)が作る
  return probe.exists(kind === "data" ? group.whatifData : group.whatifPdf);
}

/**
 * `check_answer.py`・`render_answer.py` に共通の材料の旗(指示書 §2 の「引数 20 個の内訳」= `run_check.sh` の並び)。
 * 並びは `run_check.sh` のとおり: patient(組の順)→ whatif-data → whatif-v2-dir → read-dir → type-summary →
 * whatif-pdf(各組 + 付録 3)→ direct ×2 → time-cause → time-search → menu。
 */
export function answerMaterialFlags(groups: readonly GroupPaths[], probe: DeliverProbe, out: DeliverOutPaths, plan: MaterialPlan): string[] {
  const withRead = groupsWithRead(groups, probe);
  const flags: string[] = [];
  for (const g of groups) flags.push("--patient", g.patient, "--time-limit-sec", String(g.timeLimitSec));
  for (const g of groups) {
    if (willHaveWhatif(g, probe, plan, "data")) flags.push("--whatif-data", g.whatifData);
  }
  // `--whatif-v2-dir`・`--read-dir` は **`read/` がある組だけ**(指示書 §2: `whatif-v2` があっても `read/` が
  // 無い組は渡さない ― ここを間違えると M4 の数が変わる)。
  for (const g of withRead) flags.push("--whatif-v2-dir", g.whatifV2Dir);
  for (const g of withRead) flags.push("--read-dir", g.readDir);
  for (const g of groups) {
    if (probe.exists(g.typeSummary)) flags.push("--type-summary", g.typeSummary);
  }
  for (const g of groups) {
    if (willHaveWhatif(g, probe, plan, "pdf")) flags.push("--whatif-pdf", g.whatifPdf);
  }
  // 付録 3 の PDF も `--whatif-pdf` に渡す(B の読み筋の手を検査 2 で照合するため。計画 §5)。
  flags.push("--whatif-pdf", out.appendix3);
  flags.push("--direct", out.directAnswers, "--direct", out.finalPositions);
  flags.push("--time-cause", out.timeCause);
  if (plan.hasSearch) flags.push("--time-search", out.timeSearch);
  flags.push("--menu", out.answerMenu);
  return flags;
}

export function checkAnswerCommand(groups: readonly GroupPaths[], probe: DeliverProbe, out: DeliverOutPaths, plan: MaterialPlan): string[] {
  return [out.answerDraft, ...answerMaterialFlags(groups, probe, out, plan)];
}

export function renderAnswerCommand(groups: readonly GroupPaths[], probe: DeliverProbe, out: DeliverOutPaths, plan: MaterialPlan): string[] {
  return [out.answerDraft, out.answerPdf, ...answerMaterialFlags(groups, probe, out, plan)];
}

/**
 * 段 12(`answer_facts.py`)。数の材料だけを渡す(`--menu`・`--whatif-pdf` は要らない ― 文の照合はしない)。
 * `--whatif-v2-dir`・`--read-dir` は `read/` がある組だけ(`answerMaterialFlags` と同じ規則)。
 */
export function answerFactsCommand(groups: readonly GroupPaths[], probe: DeliverProbe, out: DeliverOutPaths, displayName: string, plan: MaterialPlan): string[] {
  const withRead = groupsWithRead(groups, probe);
  // 表示名は `--name` で渡す(`answer_facts.py` が名前を自分の中に持たないため)。
  const flags: string[] = ["--name", displayName];
  for (const g of groups) flags.push("--patient", g.patient, "--time-limit-sec", String(g.timeLimitSec));
  for (const g of withRead) flags.push("--whatif-v2-dir", g.whatifV2Dir);
  for (const g of withRead) flags.push("--read-dir", g.readDir);
  flags.push("--direct", out.directAnswers, "--direct", out.finalPositions);
  flags.push("--time-cause", out.timeCause);
  if (plan.hasSearch) flags.push("--time-search", out.timeSearch);
  flags.push("--out", out.answerDraft);
  return flags;
}

export function checkDeliveryCommand(outDir: string, forbid: readonly string[]): string[] {
  const flags = [outDir];
  for (const word of forbid) flags.push("--forbid", word);
  return flags;
}

// ---- 納品ログ(計画 §3 の 5) ----

export interface DeliverLogEntry {
  stage: DeliverStage;
  startedAt: string;
  finishedAt: string;
  rc: number | "skip";
  humanGate: boolean;
}

export function deliverLogLineOf(entry: DeliverLogEntry): string {
  return `${JSON.stringify(entry)}\n`;
}

// ---- --dry-run 用のプレビュー(何も書かず・何も実行しない) ----

export interface PlannedDeliverStep {
  stage: DeliverStage;
  tool: DeliverTool;
  cmd: string;
  args: string[];
  action: "run" | "skip" | "gate";
  reason: string;
  /** `render_direct.py` の `REPORT_DATA_DIR` のように、環境変数で渡すもの(無ければキー自体を付けない)。 */
  env?: Record<string, string>;
}

/** `--from` が指定されていたら、その段より前を飛ばす(司令塔の判断。人間の確認点で止まった後の再開用)。 */
export function stagesFrom(from: DeliverStage | undefined): DeliverStage[] {
  if (from === undefined) return [...DELIVER_STAGES];
  const index = DELIVER_STAGES.indexOf(from);
  return DELIVER_STAGES.slice(index);
}

/**
 * 段ごとのコマンドと「済み」の判定を、**実行せずに**組み立てる。`deliver.ts`(CLI)は実行時もこの一覧を使い、
 * `--dry-run` のときは JSON にして出すだけ(引数の組み立てが 1 か所にしか無いようにするため)。
 * `cmdOf` は道具名を実際のコマンド名へ直す(呼び出し側が注入 ― このファイルはパスを知らない)。
 */
export function planDeliver(args: DeliverArgs, probe: DeliverProbe, cmdOf: (tool: DeliverTool) => string): PlannedDeliverStep[] {
  const out = deliverOutPaths(args.out);
  const groups = groupListOf(args);
  const thisGroup = groupPaths({ work: args.work, timeLimitSec: args.timeLimitSec }, args.person);
  const plan = materialPlanOf(args);
  const steps: PlannedDeliverStep[] = [];
  const wanted = new Set(stagesFrom(args.from));

  const push = (step: PlannedDeliverStep): void => {
    if (wanted.has(step.stage)) steps.push(step);
  };

  push({
    stage: "pipeline-data",
    tool: "pipeline",
    cmd: cmdOf("pipeline"),
    args: pipelineCommand(args, "report-data"),
    action: "run",
    reason: "S1〜S4 + whatif + READ + S5(局ごとの済みの判定は pipeline.ts 自身が持つ)",
  });

  const proseOk = probe.exists(thisGroup.prose);
  push({
    stage: "prose-gate",
    tool: "gate",
    cmd: cmdOf("gate"),
    args: [thisGroup.prose],
    action: proseOk ? "skip" : "gate",
    reason: proseOk ? "prose.json がある" : `言い換えが要る: ${thisGroup.proseRequest} を基に ${thisGroup.prose} を書く`,
  });

  push({
    stage: "pipeline-pdf",
    tool: "pipeline",
    cmd: cmdOf("pipeline"),
    args: pipelineCommand(args, "pdf"),
    action: "run",
    reason: "S7 本編 + 付録 1 + 付録 2(PDF の済みの判定は pipeline.ts 自身が持つ)",
  });

  const copies: [string, string][] = [
    [thisGroup.frontPdf, out.front],
    [thisGroup.mainPdf, out.main],
    [thisGroup.whatifPdf, out.whatif],
  ];
  const copyDone = copies.every(([, dst]) => probe.exists(dst));
  push({
    stage: "deliverables-pdf",
    tool: "copy",
    cmd: cmdOf("copy"),
    args: copies.flat(),
    action: copyDone ? "skip" : "run",
    reason: copyDone ? "3 冊とも複製済み" : "本編・付録 1・付録 2 を顧客フォルダへ複製する",
  });

  const withRead = groupsWithRead(groups, probe);
  const answersDone = probe.exists(out.directAnswers);
  push({
    stage: "appendix3-answers",
    tool: "direct-answers",
    cmd: cmdOf("direct-answers"),
    args: directAnswersCommand(withRead, out.directAnswers),
    action: answersDone ? "skip" : "run",
    reason: answersDone ? "direct_answers.json がある" : `read/ がある ${withRead.length} 組を組の順で合算する`,
  });

  // 段 6 は組ごとに 1 回ずつ + 連結。**全組ぶんの引数をここで組む**が、`finalPositions.ts` は対象 0 件で
  // rc=1 になるので、**時間切れ負けが 0 局の組は実行時に飛ばす**(実装担当の判断)。判定を実行時に置くのは、
  // 今回の組の `patient_report_data.json` は段 1 が作るため ― ここ(計画を組む時点)ではまだ無いことがある。
  const finalDone = probe.exists(out.finalPositions);
  const finalArgs: string[] = [];
  groups.forEach((g, index) => {
    finalArgs.push(...finalPositionsCommand(g, probe.fixedKifuFiles(g.fixedKifuDir), finalPositionsPartPath(args.out, index)));
  });
  push({
    stage: "appendix3-final",
    tool: "final-positions",
    cmd: cmdOf("final-positions"),
    args: finalArgs,
    action: finalDone ? "skip" : "run",
    reason: finalDone
      ? "final_positions.json がある"
      : `${groups.length} 組を組の順に(エンジン 1 本。時間切れ負けが 0 局の組は実行時に飛ばす ― 道具が対象 0 件で rc=1 になるため)`,
  });

  const a3PdfDone = probe.exists(out.appendix3);
  push({
    stage: "appendix3-pdf",
    tool: "render-direct",
    cmd: cmdOf("render-direct"),
    args: renderDirectCommand(out.directAnswers, out.finalPositions, out.appendix3),
    action: a3PdfDone ? "skip" : "run",
    reason: a3PdfDone ? "付録 3 の PDF がある" : "付録 3 の PDF を作る",
    env: { REPORT_DATA_DIR: reportDataDirEnv(groups) },
  });

  const causeDone = probe.exists(out.timeCause);
  push({
    stage: "appendix4-cause",
    tool: "time-cause",
    cmd: cmdOf("time-cause"),
    args: timeCauseCommand(groups, probe, out.timeCause),
    action: causeDone ? "skip" : "run",
    reason: causeDone ? "time_cause.json がある" : `全 ${groups.length} 組を組の順で合算する`,
  });

  const previous = args.previousWork === undefined ? undefined : groups.find((g) => g.work === args.previousWork);
  const searchDone = probe.exists(out.timeSearch);
  if (previous !== undefined) {
    const validate = groups.find((g) => g.work === args.work)!;
    push({
      stage: "appendix4-search",
      tool: "time-search",
      cmd: cmdOf("time-search"),
      args: timeSearchCommand(previous, validate, probe, out.timeSearch),
      action: searchDone ? "skip" : "run",
      reason: searchDone ? "time_cause_search.json がある" : "発見用 = 前回の組・検証用 = 今回の組",
    });
  } else {
    push({
      stage: "appendix4-search",
      tool: "time-search",
      cmd: cmdOf("time-search"),
      args: [],
      action: "skip",
      reason: "--previous-work が無いので探索は回さない",
    });
  }

  const a4PdfDone = probe.exists(out.appendix4);
  push({
    stage: "appendix4-pdf",
    tool: "render-time-cause",
    cmd: cmdOf("render-time-cause"),
    args: renderTimeCauseCommand(out.timeCause, out.appendix4, plan.hasSearch ? out.timeSearch : undefined),
    action: a4PdfDone ? "skip" : "run",
    reason: a4PdfDone ? "付録 4 の PDF がある" : "付録 4 の PDF を作る",
  });

  const menuDone = probe.exists(out.answerMenu);
  push({
    stage: "answer-menu",
    tool: "answer-menu",
    cmd: cmdOf("answer-menu"),
    args: ["--out", out.answerMenu],
    action: menuDone ? "skip" : "run",
    reason: menuDone ? "answer_menu.json がある" : "行動のメニューの表を書き出す",
  });

  const draftDone = probe.exists(out.answerDraft);
  push({
    stage: "answer-draft",
    tool: "answer-facts",
    cmd: cmdOf("answer-facts"),
    args: answerFactsCommand(groups, probe, out, args.name, plan),
    action: draftDone ? "skip" : "run",
    reason: draftDone ? "下書きがある(上書きしない)" : "B の「分かっている事実」を材料から組む",
  });

  push({
    stage: "answer-gate",
    tool: "gate",
    cmd: cmdOf("gate"),
    args: [out.answerDraft],
    action: "gate",
    reason: `下書きに ${TODO_MARK} が残っていれば止まる(「読み」を人が埋める)`,
  });

  push({
    stage: "answer-check",
    tool: "check-answer",
    cmd: cmdOf("check-answer"),
    args: checkAnswerCommand(groups, probe, out, plan),
    action: "run",
    reason: "B の検査(禁止語・数・指し手の照合)",
  });

  const answerPdfDone = probe.exists(out.answerPdf);
  push({
    stage: "answer-pdf",
    tool: "render-answer",
    cmd: cmdOf("render-answer"),
    args: renderAnswerCommand(groups, probe, out, plan),
    action: answerPdfDone ? "skip" : "run",
    reason: answerPdfDone ? "B の PDF がある" : "B の PDF を作る",
  });

  push({
    stage: "check-delivery",
    tool: "check-delivery",
    cmd: cmdOf("check-delivery"),
    args: checkDeliveryCommand(args.out, args.forbid),
    action: "run",
    reason: "伏せ字・個人情報・禁止語の検査(PDF 全冊と md)",
  });

  return steps;
}
