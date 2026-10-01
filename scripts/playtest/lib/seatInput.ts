// 3 席 LLM API の束 R1 ― render: packet + request → seat_input.md(計画 docs/STEP_LLM_SEATS_R1_RENDER_2026-09-30.md)。
//
// 【顧客の PDF にどう出るか】今は何も変わらない。作るのは 3 席の LLM に渡す**同一バイトの入力 1 本**と、その目次・sha・省いたものの一覧。
// 【この道具は抽出だけ】値は JSON.stringify の写し。再計算・丸め直し・欠損の補完をしない。
//   その証拠として、本文の数値トークンの多重集合が packet + request の数値トークンの多重集合に含まれることを、
//   render の中(`dataLines`)と、書いたファイルから(`numberInclusionProblems`)の 2 か所で見る。
// 【黙って送らない】packet / request が契約を通らない・線の組が無い・指示文の sha が固定値と違う・
//   符号以外の識別子(@ / http / 絶対パス / ~ / 禁止の語)が値に混ざる・runId が短い、のどれかなら例外(SeatInputError)。
// 【外へ出る入力】席は外部 API。実名は packet に元から無い(customerRef は符号)。符号 c5 と path の中の c5 は載せてよい(計画 §1.1 の監査の条件)。
import { createHash } from "node:crypto";
import { observationPacketProblems, requestAgreementProblems, validateObservationRequest } from "./observationPacket.js";
import { aggregateRef } from "./packetRef.js";

export const SEAT_INPUT_META_SCHEMA_VERSION = "0.1" as const;
/** 指示文 v1(docs/LLM_SEATS_INSTRUCTION_v1_2026-09-30.md)の sha256。司令塔が文面を承認した版。変えるときは版を上げる */
export const INSTRUCTION_V1_SHA256 = "3b09bec22b7ea95c1a7e7a3cce1087b1c3c9f54ad2583d35f2d00e46242b2f88";
export const PASSPHRASE_LENGTH = 8;

export class SeatInputError extends Error {
  readonly problems: readonly string[];
  constructor(problems: readonly string[]) {
    super(`seat_input を作れない(${problems.length} 件):\n${problems.map((p) => `  - ${p}`).join("\n")}`);
    this.name = "SeatInputError";
    this.problems = problems;
  }
}

export interface SeatInputSection {
  section: string;
  title: string;
  /** その節の行が packet のどこか(席が packetRef.path に写す文法の根) */
  packetPath: string;
  rows: number;
  /** 最後の data 行の先頭 2 トークン(先頭 60 字まで。到達検査が席の reach.sections と前方一致で照合する) */
  lastKey: string;
}

export interface SeatInputMeta {
  schemaVersion: typeof SEAT_INPUT_META_SCHEMA_VERSION;
  runId: string;
  passphrase: string;
  packetId: string;
  customerRef: string;
  timeLimitSec: number;
  games: number;
  instructionSha256: string;
  seatInputSha256: string;
  bytes: number;
  chars: number;
  tokenEstimate: { value: number; method: "chars/3" };
  sections: SeatInputSection[];
  /**
   * **本文に見出しだけが在る節**(データの行を持たない。例: 0 読み方・0.1 省いたもの・0.2 線の組)。
   * 席はこれらも「読んだ節」として挙げるので、**meta が持っていないと到達の検査が正直な席を落とす**
   * (2026-09-30 の初回の実行で実測。司令塔の決定は「meta に載せ、無い節名は従来どおり落とす」)。
   */
  headingSections: string[];
  /** packet にはあるが本文に写さなかったもの */
  omitted: string[];
  /** 意図して含めていないもの(現行ルートの出力) */
  notIncluded: string[];
}

export interface RenderSeatInputArgs {
  packet: unknown;
  request: unknown;
  /** 指示文のバイト列そのまま */
  instruction: Buffer;
  /** 指示文の固定 sha(既定は v1)。違えば止まる */
  instructionSha256?: string;
  runId: string;
  /** 値に混ざっていれば止める語(実名など)。**語そのものはメッセージに出さない** */
  forbid?: readonly string[];
}

export const OMITTED: readonly string[] = [
  "facts.engine[].candidates[].pv(読み筋。席は読み筋を根拠にしない)",
  "facts.engine[].sfen(局面は gameId + ply で packet に戻れる)",
  "facts.engine[].nodes・multipv(provenance.sources のエンジン設定に同じ値)",
  "provenance.inputs[].sha256・bytes(path だけ写した)",
  "facts.*[].src・src*(出どころの符号。provenance.sources を §0.3 に写した)",
  "provenance.sources[].inputPaths(§0.3 の inputs の一覧と同じ)",
];

export const NOT_INCLUDED: readonly string[] = [
  "現行の納品レーンの出力(承認済みの行動の表・本編の冊子・候補一覧)。席はそれらを見ずに分析する",
  "実験 1 の束に在って packet v0.1 に無いもの(Failure Event の詳細・escapeScenes・時間の 4 段全部・read の ladder・scene 行・tagCrossTable・final_positions)。packet が唯一の事実入力なので足さない",
];

/**
 * 読み方の固定文。**data 行ではない**(数の包含の検査から除く。欄名 `top1Side` や「第 1 候補」の数字は値ではない)。
 * 閾値の値は書かず、線の組の id で指す(値は 1 行目に packet から写してある)。試験は、固定文の全行が data 行から除かれることを見る。
 */
export const READING_GUIDE: readonly string[] = [
  "- 数はすべて packet からそのまま写した。再計算・丸め直し・欠損の補完はしていない。小数は元の桁のまま。`null` は packet でも null(測れなかった・該当なし)。",
  "- 列挙(印・条件)は `+` または `;` 区切り。空は `-`。",
  "- 手は USI 表記(筋の数字 + 段の英字で「元のマス」「行き先のマス」を並べる。`*` の前が駒の英字なら打つ手、末尾 `+` は成る)。局面は `gameId` と `ply`(記録の手数。本人=先手にそろえた後の手数で、本人が後手の局〈mirrored = true〉は元の棋譜の手数と一つずれる。`displayPly` が元の棋譜の手数)で指す。",
  "- 評価 `scoreCp`・`beforeCp`・`afterCp` はエンジンの評価(centipawn)で、本人から見て正が本人有利。線の組 `ahead_cp` 以上を優勢、その負を劣勢、間を互角とする(この線は道具の仮置きの値であり、将棋一般の基準ではない)。",
  "- 崩れ(collapse)は、本人の手の前と次の本人の手番の前とで、段(優勢・互角・劣勢)が下がった組。`kind` は道具の分類。",
  "- 側 `top1Side`・`actualSide`(attack / defense / both / none)は手の行き先だけで決まる印で、手の意味の判定ではない。`oppositeSide` = 第 1 候補と実戦の側が逆。",
  "- 分かれ道(branches)は、第 1 候補と実戦の手の差が線の組 `branch_min_loss_cp` 以上の本人の局面。`shallowVisible` = 浅い読み(線の組 `shallow_first_nodes` のノード数)で既に差が見えた局面。`firstVisibleNodes` = 差が見えた最小のノード数。",
  "- 時間: `spentSec` は棋譜に書かれた秒。長考は線の組 `long_think_sec` 以上、早指しは `quick_sec` 以下(集計の行の名前と population に定義がある)。",
  "- 集計(aggregates)は数ごとに 1 行。分数は分子の行と分母の行に分かれ、名前・母集団(population: どの facts から、どの条件で)・分子の条件・時間に依るか・facts から数え直せるか・出どころの局は分子の行にだけ書いてある。根拠に引くときは、その行の 1 列目(packetRef)と値をそのまま写す。**分母は population に書かれたとおりで、行の名前を読み替えない。**",
  "- 戦型の機械認識(recognition)は**すべて下書き(draft)の定義**による。`rows` は局ごとの署名(定義の id の列)と群の分類、`definitions` は判定に使った定義の写し(id・名前・側・型)。名前は定義にあるものだけ。",
  "- 第 1 候補は鍵名が top1 なだけで「正解」ではない。実戦が第 1 候補と違うことから、見落とし・苦手・知らないを読まない。",
];

// ---- 値の写し ----

function v(x: unknown): string {
  if (x === undefined) return "null";
  if (typeof x === "string") return x;
  return JSON.stringify(x) ?? "null";
}

function list(x: unknown, sep = "+"): string {
  if (!Array.isArray(x) || x.length === 0) return "-";
  return x.map((item) => v(item)).join(sep);
}

function where(x: unknown): string {
  if (!Array.isArray(x) || x.length === 0) return "-";
  return x.map((item) => {
    const r = item as { field?: unknown; op?: unknown; value?: unknown };
    return `${v(r.field)} ${v(r.op)} ${JSON.stringify(r.value) ?? "null"}`;
  }).join("; ");
}

function isRecord(x: unknown): x is Record<string, unknown> {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

// ---- 数値トークン(抽出の証拠) ----

const NUMBER_RE = /-?\d+(?:\.\d+)?/g;

export function numberTokens(text: string): Map<string, number> {
  const out = new Map<string, number>();
  for (const m of text.matchAll(NUMBER_RE)) out.set(m[0], (out.get(m[0]) ?? 0) + 1);
  return out;
}

/**
 * 本文の data 行の数値トークンの多重集合が、packet + request(JSON の字面)の多重集合に含まれるか。
 * 含まれない(回数が多い・無い)トークンを 1 件 1 行で返す。空なら通った。
 * **これは校正の道具**なので、わざとずらした写しで捕まることを試験で見る。
 */
export function numberInclusionProblems(dataText: string, packet: unknown, request: unknown): string[] {
  const allowed = numberTokens(`${JSON.stringify(packet)}\n${JSON.stringify(request)}`);
  const problems: string[] = [];
  for (const [token, count] of numberTokens(dataText)) {
    const have = allowed.get(token) ?? 0;
    if (count > have) problems.push(`数「${token}」が本文に ${count} 回、packet + request には ${have} 回`);
  }
  return problems;
}

/**
 * seat_input.md の本文から、包含の検査に掛ける行(data 行)だけを抜く。見出し・固定文・指示文・末尾の合言葉は除く。
 * **1 行目(符号・持ち時間・局数・線の組の値)は data 行**なので含める ― 2026-09-30 の独立監査が、(A) から後ろだけを
 * 切り出していて 1 行目が検査から落ちている(1 行目の 180 を書き換えても緑)ことを実物で示した。render の内側の検査(`e.data`)と同じ集合を見る。
 */
export function dataLinesOf(text: string, instruction: string): string {
  const firstLine = text.split("\n")[0] ?? "";
  const body = text.slice(text.indexOf("\n# (A) ") + 1);
  const fixed = new Set<string>([...READING_GUIDE, ...FIXED_PROSE, ...OMITTED.map((l) => `- ${l}`), ...NOT_INCLUDED.map((l) => `- ${l}`), ...instruction.split("\n")]);
  return [firstLine, ...body.split("\n")]
    .filter((line) => line.length > 0 && !line.startsWith("#") && !line.startsWith(SENTINEL_HEAD) && !fixed.has(line))
    .join("\n");
}

// ---- 符号以外の識別子(欄の型で見る: すべての文字列の値を歩く) ----

export function identifierProblems(value: unknown, path: string, forbid: readonly string[] = []): string[] {
  const problems: string[] = [];
  const walk = (x: unknown, p: string): void => {
    if (typeof x === "string") {
      if (x.startsWith("/")) problems.push(`${p} が絶対パス`);
      if (x.includes("@")) problems.push(`${p} にメールの記号を含む`);
      if (/https?:\/\//.test(x)) problems.push(`${p} に URL を含む`);
      if (x.includes("~")) problems.push(`${p} に「~」を含む`);
      for (const word of forbid) if (word.length > 0 && x.includes(word)) problems.push(`${p} に禁止の語を含む`);
      return;
    }
    if (Array.isArray(x)) x.forEach((item, i) => walk(item, `${p}[${i}]`));
    else if (isRecord(x)) for (const [k, item] of Object.entries(x)) walk(item, `${p}.${k}`);
  };
  walk(value, path);
  return problems;
}

// ---- 本文 ----

const SENTINEL_HEAD = "(束はここまで。合言葉: ";
const FIXED_PROSE: readonly string[] = [
  "この問いに合わせて事実の作り方を変えていない(packet は request を参照しない。問いは分析の条件であり、事実の入力ではない)。",
  "省いたもの(packet にはある):",
  "含めていないもの(意図して):",
];

interface Emitter {
  lines: string[];
  data: string[];
  sections: SeatInputSection[];
}

function heading(e: Emitter, line: string): void {
  e.lines.push(line);
}
function prose(e: Emitter, line: string): void {
  e.lines.push(line);
}
function data(e: Emitter, line: string): void {
  e.lines.push(line);
  e.data.push(line);
}
/**
 * 本文の見出しから節の番号を拾い、**`section()` で正式に登録された節を除く**。残るのが「見出しだけの節」。
 * 字面を手で並べないので、見出しを増やしても meta が付いてくる。
 * **注意**: ここが見ているのは「正式に登録されたか」だけで、`data()` を呼んでいるかは見ていない ―
 * **データの行を持つ節を登録し忘れると、この関数はそれを「見出しだけ」と見なし、E-1 の lastKey の照合が外れる**
 * (2026-09-30 の独立監査が 0.2 でこれを見つけた。データの行を書く節は必ず `section()` で登録する)。
 */
export function headingSectionsOf(lines: readonly string[], dataSections: readonly string[]): string[] {
  const found: string[] = [];
  const have = new Set(dataSections);
  for (const line of lines) {
    const match = /^#{2,4} ([0-9]+(?:\.[0-9]+)*)[.、 ]/.exec(line);
    if (match === null) continue;
    const label = match[1]!;
    if (have.has(label) || found.includes(label)) continue;
    found.push(label);
  }
  return found;
}

export const LAST_KEY_MAX_CHARS = 60;
/** data 行の先頭 2 トークン(表なら先頭 2 セル)。長い文は先頭 60 字で切る(到達検査は前方一致で見る) */
/**
 * 鍵の正規化。**箇条書きの印は鍵ではない** ― 行頭の `- `(`*`・`•` も)と末尾の `:` を外す。
 *
 * 【なぜ要るか】2026-10-01 の実行で、席は「shallow_first_nodes」と正しく書いたのに
 * meta が「- shallow_first_nodes:」を持っていたため、**正直に読んだ席が E-1 で落ちた**(§0.2・§0.3 の 2 件)。
 * 司令塔の決定: meta は鍵だけを持ち、照合は**両側に同じ正規化**を掛ける。
 * **鍵そのものが違えば落ちることは変えない**(正規化で穴を開けない)。
 */
export function normalizeLastKey(key: string): string {
  // 内側の空白は 1 つに詰める(表記のゆれで正直な席を落とさない。実物では数が変わらないことを測った)
  return key.trim().replace(/^[-*•]\s+/, "").replace(/[:：]\s*$/, "").trim().replace(/\s+/g, " ");
}
function keyOf(line: string): string {
  const cells = line.startsWith("|") ? line.split("|").slice(1).map((c) => c.trim()) : line.split(/\s+/);
  // 正規化は**ここ 1 か所**(箇条書きの行は「- 鍵:」の 2 セルになるので、切った後に印を外せば鍵だけが残る)
  return normalizeLastKey([...cells.filter((c) => c.length > 0).slice(0, 2).join(" ")].slice(0, LAST_KEY_MAX_CHARS).join(""));
}
function section(e: Emitter, section: string, title: string, packetPath: string, rows: unknown[], body: () => void): void {
  heading(e, "");
  heading(e, `## ${section}. ${title}(${packetPath}、${rows.length} 行)`);
  const before = e.data.length;
  body();
  const written = e.data.slice(before);
  e.sections.push({ section, title, packetPath, rows: rows.length, lastKey: written.length > 0 ? keyOf(written[written.length - 1]!) : "-" });
}
function table(e: Emitter, header: string[], rows: string[][]): void {
  heading(e, `| ${header.join(" | ")} |`);
  heading(e, `|${header.map(() => "---").join("|")}|`);
  for (const row of rows) data(e, `| ${row.join(" | ")} |`);
}

type Row = Record<string, unknown>;

function factsOf(packet: Record<string, unknown>): Record<string, unknown> {
  return packet.facts as Record<string, unknown>;
}

export function renderSeatInput(args: RenderSeatInputArgs): { text: string; meta: SeatInputMeta } {
  const problems: string[] = [];
  const { packet, request, instruction, runId } = args;
  const expectedSha = args.instructionSha256 ?? INSTRUCTION_V1_SHA256;
  const instructionSha = createHash("sha256").update(instruction).digest("hex");
  if (instructionSha !== expectedSha) problems.push(`指示文の sha256 が固定値と違う(${instructionSha.slice(0, 8)}… / 固定 ${expectedSha.slice(0, 8)}…)。文面を変えたなら版を上げる`);
  if (typeof runId !== "string" || !/^[a-z0-9-]{8,}$/i.test(runId)) problems.push("runId が無いか短い(半角英数 8 桁以上)― 合言葉が作れない");
  problems.push(...observationPacketProblems(packet).map((p) => `packet: ${p}`));
  problems.push(...validateObservationRequest(request).map((p) => `request: ${p}`));
  if (problems.length > 0) throw new SeatInputError(problems);
  problems.push(...requestAgreementProblems(packet, request));
  const pk = packet as Record<string, unknown>;
  const rq = request as Record<string, unknown>;
  const provenance = pk.provenance as Record<string, unknown>;
  const thresholds = provenance.thresholds as Row[];
  if (!Array.isArray(thresholds) || thresholds.length === 0) problems.push("provenance.thresholds が空 ― どの線で数えたかを席に渡せない");
  problems.push(...identifierProblems(packet, "packet", args.forbid));
  problems.push(...identifierProblems(request, "request", args.forbid));
  if (problems.length > 0) throw new SeatInputError(problems);

  const facts = factsOf(pk);
  const games = facts.games as Row[];
  const scope = rq.requestedScope as Row;
  const questions = rq.customerQuestions as Row[];
  const passphrase = runId.slice(0, PASSPHRASE_LENGTH);
  const e: Emitter = { lines: [], data: [], sections: [] };

  // 1 行目(S-2: 線の組と持ち時間。無ければ上で止まっている)
  data(e, `対象: 〇〇さん(符号 ${v(pk.customerRef)})。持ち時間 ${v(scope.timeLimitSec)} 秒の組・${v(scope.games)} 局。線の組: ${thresholds.map((t) => `${v(t.id)}=${v(t.value)} ${v(t.unit)}`).join("; ")}`);
  heading(e, "");
  // 指示文(バイト列そのまま)
  e.lines.push(instruction.toString("utf-8").replace(/\n$/, ""));

  heading(e, "");
  heading(e, "# (A) 依頼主の問いと範囲(request)");
  heading(e, "");
  section(e, "A", "顧客の問い", "request.customerQuestions[]", questions, () => {
    table(e, ["id", "問い(原文の写し)", "askedAt", "via"], questions.map((q) => [v(q.id), v(q.text), v(q.askedAt), v(q.via)]));
  });
  heading(e, "");
  data(e, `requestedScope: games と timeLimitSec は 1 行目に写した。note ${v(scope.note)}`);
  prose(e, FIXED_PROSE[0]!);

  heading(e, "");
  heading(e, `# (B) 材料の束(packet の写し。packetId ${v(pk.packetId)}・schemaVersion ${v(pk.schemaVersion)}・pipelineVersion ${v(provenance.pipelineVersion)}・generatedAt ${v(provenance.generatedAt)})`);
  heading(e, "");
  heading(e, "## 0. 読み方(先に読んでください)");
  for (const line of READING_GUIDE) prose(e, line);
  heading(e, "");
  heading(e, "### 0.1 省いたもの・含めていないもの");
  prose(e, FIXED_PROSE[1]!);
  for (const line of OMITTED) prose(e, `- ${line}`);
  prose(e, FIXED_PROSE[2]!);
  for (const line of NOT_INCLUDED) prose(e, `- ${line}`);
  heading(e, "");
  // 0.2 は**データの行を持つ節**なので、0.3 と同じく正式に登録する(2026-09-30 の独立監査の指摘)。
  // 登録しないと headingSections(= 正式な節に無いもの)に混ざり、**この節だけ lastKey の照合が外れる**。
  section(e, "0.2", "線の組(値は 1 行目に写した。ここは id と在り処)", "provenance.thresholds", thresholds, () => {
    for (const t of thresholds) data(e, `- ${v(t.id)}: ${v(t.from)}`);
  });
  heading(e, "");
  const sources = provenance.sources as Row[];
  const inputs = provenance.inputs as Row[];
  // inputs の一覧は §0.3 の**中**に置く(節の最後の行が meta の lastKey と同じになるように。
  // 2026-09-30: 節の外に置いていたため、席が見た最後の行と meta が食い違い、到達の検査が落ちた)
  section(e, "0.3", "出どころ", "provenance.sources[] と provenance.inputs[].path", [...sources, ...inputs], () => {
    table(e, ["id", "type", "kind", "engineVersion", "nodesLimit", "multipv", "reviewStatus", "definitionsDirs"], sources.map((s) => [v(s.id), v(s.type), v(s.kind), v(s.engineVersion), v(s.nodesLimit), v(s.multipv), v(s.reviewStatus), list(s.definitionsDirs, "; ")]));
    heading(e, "");
    heading(e, `#### inputs(provenance.inputs[].path、${inputs.length} 本)`);
    for (const input of inputs) data(e, `- ${v(input.path)}`);
  });

  section(e, "1", "局", "facts.games[]", games, () => {
    table(e, ["gameId", "no", "side", "result", "ending", "ownPlyCount", "totalPlyCount", "timeLimitSec", "mirrored", "aheadAtAnyPoint"],
      games.map((g) => [v(g.gameId), v(g.no), v(g.side), v(g.result), v(g.ending), v(g.ownPlyCount), v(g.totalPlyCount), v(g.timeLimitSec), v(g.mirrored), v(g.aheadAtAnyPoint)]));
  });

  // 集計は**数ごとに 1 行**(司令塔の決定 2026-09-30): 分数は .numerator と .denominator の 2 行、単独の数は .value の 1 行。
  // 席は 1 列目をそのまま packetRef.path に写す。名前・母集団・出どころの局は最初の行にだけ書く(同じ値を 2 度写さない ― 抽出の証拠を守る)。
  const aggregates = pk.aggregates as Row[];
  const aggregateRows: string[][] = [];
  for (const a of aggregates) {
    const pop = a.population as Row;
    const id = v(a.id);
    const head = [v(a.name), v(a.unit), `${v(pop.from)} / ${where(pop.where)} / ${v(pop.unit)}`, where(a.numeratorWhere), v(a.sumField), v(a.timeDependent), v(a.recountable), v(a.recountNote), list(a.derivedFrom)];
    const rest = ["-", v(a.unit), "-", "-", "-", "-", "-", "-", "-"];
    if (typeof a.value === "number") aggregateRows.push([aggregateRef(id, "value"), "値", v(a.value), ...head]);
    else {
      aggregateRows.push([aggregateRef(id, "numerator"), "分子", v(a.numerator), ...head]);
      aggregateRows.push([aggregateRef(id, "denominator"), "分母", v(a.denominator), ...rest]);
    }
  }
  section(e, "2", "集計(数ごとに 1 行。分数は分子・分母の 2 行)", "aggregates.<id>.numerator|denominator|value", aggregateRows, () => {
    table(e, ["packetRef", "どの数", "値", "名前", "unit", "population(from / where / unit)", "numeratorWhere", "sumField", "timeDependent", "recountable", "recountNote", "derivedFrom"], aggregateRows);
  });

  const time = facts.time as Row[];
  section(e, "3", "時間(局ごと)", "facts.time[]", time, () => {
    table(e, ["gameId", "earlySpentSec", "midSpentSec", "lateSpentSec", "longThinkCount", "longThinkForkCount", "longThinkOppositeCount", "remainingSec", "timeUpLoss"],
      time.map((t) => [v(t.gameId), v(t.earlySpentSec), v(t.midSpentSec), v(t.lateSpentSec), v(t.longThinkCount), v(t.longThinkForkCount), v(t.longThinkOppositeCount), v(t.remainingSec), v(t.timeUpLoss)]));
  });

  const collapse = facts.collapse as Row[];
  section(e, "4", "崩れ", "facts.collapse[]", collapse, () => {
    table(e, ["gameId", "ply", "beforeCp", "afterCp", "bandBefore", "bandAfter", "kind"],
      collapse.map((c) => [v(c.gameId), v(c.ply), v(c.beforeCp), v(c.afterCp), v(c.bandBefore), v(c.bandAfter), v(c.kind)]));
  });

  const branches = facts.branches as Row[];
  section(e, "5", "分かれ道", "facts.branches[]", branches, () => {
    table(e, ["gameId", "ply", "displayPly", "top1Usi", "actualUsi", "top1Side", "actualSide", "oppositeSide", "top1Tags", "actualTags", "topGapCp", "actualGapCp", "firstVisibleNodes", "shallowVisible"],
      branches.map((b) => [v(b.gameId), v(b.ply), v(b.displayPly), v(b.top1Usi), v(b.actualUsi), v(b.top1Side), v(b.actualSide), v(b.oppositeSide), list(b.top1Tags), list(b.actualTags), v(b.topGapCp), v(b.actualGapCp), v(b.firstVisibleNodes), v(b.shallowVisible)]));
  });

  const recognition = facts.recognition as Row;
  const rows = recognition.rows as Row[];
  const definitions = recognition.definitions as Row[];
  section(e, "6", "戦型の機械認識(局ごと。すべて draft)", "facts.recognition.rows[]", rows, () => {
    table(e, ["gameId", "selfSignature", "opponentSignature", "signatureClass", "names", "selfRecognized", "selfStrongRecognized", "opponentRecognized", "opponentStrongRecognized", "reviewStatus"],
      rows.map((r) => [v(r.gameId), list(r.selfSignature), list(r.opponentSignature), v(r.signatureClass), list(r.names), v(r.selfRecognized), v(r.selfStrongRecognized), v(r.opponentRecognized), v(r.opponentStrongRecognized), v(r.reviewStatus)]));
  });
  section(e, "6.1", "戦型の定義(判定に使ったもの。recognitionPattern は `orderHint:piece→to` の列。無い定義は `-`)", "facts.recognition.definitions[]", definitions, () => {
    table(e, ["id", "name", "nameKana", "side", "family", "reviewStatus", "confidenceLevel", "leadsToShapeIds", "recognitionPattern"],
      definitions.map((d) => {
        const pattern = Array.isArray(d.recognitionPattern) && d.recognitionPattern.length > 0
          ? (d.recognitionPattern as Row[]).map((p) => `${v(p.orderHint)}:${v(p.piece)}→${v(p.to)}`).join("; ")
          : "-";
        return [v(d.id), v(d.name), v(d.nameKana), v(d.side), v(d.family), v(d.reviewStatus), v(d.confidenceLevel), list(d.leadsToShapeIds), pattern];
      }));
  });

  const moves = facts.moves as Row[];
  const byGame = new Map<string, Row[]>();
  for (const m of moves) {
    const id = v(m.gameId);
    byGame.set(id, [...(byGame.get(id) ?? []), m]);
  }
  section(e, "7", "本人の手(局ごとに 1 行。各手は `ply:usi piece spentSec scoreCp phase 印` で、印は F = 分かれ道(isFork)・C = 崩れ(collapsed)・D = 打つ手(drop)、無ければ -)", "facts.moves[](gameId + ply で 1 手)", moves, () => {
    for (const [id, ms] of byGame) {
      data(e, `${id}: ${ms.map((m) => {
        const marks = [m.isFork ? "F" : "", m.collapsed ? "C" : "", m.drop ? "D" : ""].filter((x) => x.length > 0).join("");
        return `${v(m.ply)}:${v(m.usi)} ${v(m.piece)} ${v(m.spentSec)} ${v(m.scoreCp)} ${v(m.phase)} ${marks.length > 0 ? marks : "-"}`;
      }).join("; ")}`);
    }
  });

  const engine = facts.engine as Row[];
  section(e, "8", "候補(本人の手番の局面ごとに 1 行。`gameId ply top1Usi actualUsi scoreCp | usi scoreCp; …`(候補は元の順)。読み筋と sfen は省いた)", "facts.engine[](gameId + ply で 1 局面)", engine, () => {
    for (const p of engine) {
      const cands = Array.isArray(p.candidates) ? (p.candidates as Row[]).map((c) => `${v(c.usi)} ${v(c.scoreCp)}`).join("; ") : "-";
      data(e, `${v(p.gameId)} ${v(p.ply)} ${v(p.top1Usi)} ${v(p.actualUsi)} ${v(p.scoreCp)} | ${cands}`);
    }
  });

  heading(e, "");
  e.lines.push(`${SENTINEL_HEAD}${passphrase})`);
  const text = `${e.lines.join("\n")}\n`;

  // 抽出の証拠(render の中でも見る)
  const inclusion = numberInclusionProblems(e.data.join("\n"), packet, request);
  if (inclusion.length > 0) throw new SeatInputError(inclusion.map((p) => `抽出の証拠: ${p}`));

  const bytes = Buffer.byteLength(text, "utf-8");
  const meta: SeatInputMeta = {
    schemaVersion: SEAT_INPUT_META_SCHEMA_VERSION,
    runId,
    passphrase,
    packetId: v(pk.packetId),
    customerRef: v(pk.customerRef),
    timeLimitSec: scope.timeLimitSec as number,
    games: games.length,
    instructionSha256: instructionSha,
    seatInputSha256: createHash("sha256").update(text, "utf-8").digest("hex"),
    bytes,
    chars: [...text].length,
    tokenEstimate: { value: Math.ceil([...text].length / 3), method: "chars/3" },
    sections: e.sections,
    headingSections: headingSectionsOf(e.lines, e.sections.map((section) => section.section)),
    omitted: [...OMITTED],
    notIncluded: [...NOT_INCLUDED],
  };
  return { text, meta };
}
