// STEP OBS-2(docs/LANE_DIAG_LOG_2026-09.md §12.2)。契約 hypothesis v0.1 のスキーマと機械検査 H-1〜H-8
// (lib/hypothesis.ts)を見る。**エンジンは起動しない。**
//
// 【構成】H-1〜H-8 × 通る 1・落ちる 1(16)+ スキーマ 4(通る・知らない欄・版違い・value の oneOf)+
// 登録簿 2(111 本・obs.timeSearch.col.* 30 本)+ パリティ 1(lib が読んだ一覧 = report-pdf/check_answer.py の BANNED_WORDS)+
// CLI 1(hypothesisCheck.ts を子プロセスで回し exit code を見る)= 24 本。
// STEP EXPO-1(§12.9)で版 0.2(expired)の 3 本を足して 27 本。
// STEP 契約の仮説 v0.3(2026-09-26)で版 0.3(lane に reply・fork)の 4 本を足して 31 本。
// 【落ちる入力】§12.2「落ちる入力(H ごとに 1 つ、試験に固定)」をそのまま使う。
// 【基準の例】§12.2 の設計案 §7.1 の例を実物のパス・欄名に直した fixture
// (__fixtures__/hypothesis.v0.1.example.json)。today 2026-09-25 で 9/9 通る。writtenAt を 2026-09-26 にすると
// H-4 だけ落ちる。

import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { validate } from "./eventSchema.js";
import { checkResultLines, loadHypothesisBannedWords, loadHypothesisSchema, loadObsRegistry, validateHypothesisLine, type CheckResult, type HypothesisCheckName } from "./hypothesis.js";

type Json = Record<string, unknown>;

const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const OBS_ITEMS_PATH = fileURLToPath(new URL("../../../docs/OBSERVATION_ITEMS.md", import.meta.url));
const CHECK_ANSWER_PY = fileURLToPath(new URL("../report-pdf/check_answer.py", import.meta.url));
const HYPOTHESIS_CHECK_TS = fileURLToPath(new URL("../hypothesisCheck.ts", import.meta.url));
const FIXTURE_PATH = fileURLToPath(new URL("./__fixtures__/hypothesis.v0.1.example.json", import.meta.url));

const TODAY = "2026-09-25";
const schema = loadHypothesisSchema();
const registry = loadObsRegistry(OBS_ITEMS_PATH);
const BASE_LINE = JSON.parse(readFileSync(FIXTURE_PATH, "utf-8")) as Json;

const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

function checksOf(line: unknown, today: string = TODAY): CheckResult[] {
  return validateHypothesisLine(line, { today, registry, schema });
}

function resultOf(line: unknown, check: HypothesisCheckName, today: string = TODAY): CheckResult {
  const result = checksOf(line, today).find((r) => r.check === check);
  if (result === undefined) throw new Error(`検査 ${check} の結果が無い`);
  return result;
}

// 基準の例(設計案 §7.1 を実物のパス・欄名に直したもの、§12.2)の 2 本を、そのまま
// H-4(予測は数で、測る前に書く)の通る/落ちるに使う(司令塔の指示)。

describe("H-1 数の実在", () => {
  it("通る: 基準の例(小数・整数・割合〈derived〉のすべてが observations に実在する)", () => {
    expect(resultOf(BASE_LINE, "H-1").ok).toBe(true);
  });

  it("落ちる: 『崩れ 31 回』(観測は 30)・『56%』(derived 無し)", () => {
    const line = clone(BASE_LINE);
    line.statement = "崩れは 31 回で、長考の割合は 56%でした。という読みです。";
    const result = resultOf(line, "H-1");
    expect(result.ok).toBe(false);
    expect(result.messages.some((m) => m.includes("31"))).toBe(true);
    expect(result.messages.some((m) => m.includes("56"))).toBe(true);
  });
});

describe("H-2 ID の登録", () => {
  it("通る: 基準の例の obsId はすべて登録簿にある", () => {
    expect(resultOf(BASE_LINE, "H-2").ok).toBe(true);
  });

  it('落ちる: obsId "obs.time.phaseSpentMedian"(未登録)', () => {
    const line = clone(BASE_LINE);
    (line.observations as Json[])[0]!.obsId = "obs.time.phaseSpentMedian";
    const result = resultOf(line, "H-2");
    expect(result.ok).toBe(false);
    expect(result.messages.join(" ")).toContain("obs.time.phaseSpentMedian");
  });
});

describe("H-3 反証を試みたことの記録", () => {
  it("通る: items があり result が none_found でない", () => {
    expect(resultOf(BASE_LINE, "H-3").ok).toBe(true);
  });

  it('落ちる: attempted true, items: [], result: "weakened"', () => {
    const line = clone(BASE_LINE);
    (line.counterEvidence as Json).items = [];
    (line.counterEvidence as Json).result = "weakened";
    const result = resultOf(line, "H-3");
    expect(result.ok).toBe(false);
  });
});

describe("H-4 予測は数で、測る前に書く", () => {
  it("通る: today 2026-09-25 で基準の例は 11/11 通る(writtenAt(2026-09-25) <= today)", () => {
    const results = checksOf(BASE_LINE);
    // **検査の本数は 11**(schema + H-1〜H-10)。H-9(packet の照合)と H-10(名前の照合)は
    // 2026-09-30 に足した ― packet を渡していないのでどちらも `skipped` の印が付く
    // (**ok だが緑ではない**)
    expect(results).toHaveLength(11);
    for (const result of results) expect(result, `${result.check}: ${result.messages.join(" / ")}`).toMatchObject({ ok: true });
    for (const check of ["H-9", "H-10"] as const) {
      const result = results.find((candidate) => candidate.check === check)!;
      expect(result.skipped, `${check}: packet を渡していないのに未照合の印が無い`).toBe(true);
    }
  });

  it("落ちる: writtenAt を 2026-09-26 にすると H-4 だけ落ちる(他 8 は通る)", () => {
    const line = clone(BASE_LINE);
    (line.prediction as Json).writtenAt = "2026-09-26";
    const results = checksOf(line);
    for (const result of results) {
      if (result.check === "H-4") expect(result.ok).toBe(false);
      else expect(result, `${result.check}: ${result.messages.join(" / ")}`).toMatchObject({ ok: true });
    }
  });
});

describe("H-5 禁止語・断定しない形", () => {
  it("通る: 禁止語が無く、statement が「という読みです」の形", () => {
    expect(resultOf(BASE_LINE, "H-5").ok).toBe(true);
  });

  it("落ちる: 渡した一覧の語を含む statement(一覧は差し替え口から渡す)", () => {
    // STEP H5-SYNC(§12.9): 一覧は check_answer.py が持つ(空になりうる)ので、
    // 「語があれば落ちる」ことは自前の一覧を渡して見る(python 側の増減で壊れない)。
    const line = clone(BASE_LINE);
    line.statement = "崩れの原因を調べています。という読みです。";
    const bannedWords = ["原因"];
    const result = validateHypothesisLine(line, { today: TODAY, registry, schema, bannedWords }).find(
      (r) => r.check === "H-5",
    )!;
    expect(result.ok).toBe(false);
    expect(result.messages.join(" ")).toContain("原因");
    // 一覧が空でも H-5 は消えない ―「という読みです / 可能性があります」の形は残る。
    const empty = validateHypothesisLine(line, { today: TODAY, registry, schema, bannedWords: [] }).find(
      (r) => r.check === "H-5",
    )!;
    expect(empty.ok).toBe(true);
    const assertive = clone(BASE_LINE);
    assertive.statement = "崩れは 30 回でした。";
    const assertiveResult = validateHypothesisLine(assertive, { today: TODAY, registry, schema, bannedWords: [] }).find(
      (r) => r.check === "H-5",
    )!;
    expect(assertiveResult.ok).toBe(false);
    expect(assertiveResult.messages.join(" ")).toContain("という読みです");
  });
});

describe("H-6 盲検", () => {
  it("通る: counterEvidence.provenance.inputs が provenance.inputs の部分集合で、本人の言葉を含まない", () => {
    expect(resultOf(BASE_LINE, "H-6").ok).toBe(true);
  });

  it("落ちる: counterEvidence.provenance.inputs に 00-本人の言葉.md", () => {
    const line = clone(BASE_LINE);
    (line.counterEvidence as Json).provenance = { inputs: ["out/p4/00-本人の言葉.md"] };
    const result = resultOf(line, "H-6");
    expect(result.ok).toBe(false);
    expect(result.messages.join(" ")).toContain("本人の言葉");
  });
});

describe("H-7 昇格は human_reviewed 以上だけ", () => {
  it("通る: scope this_user(昇格の条件を問わない)", () => {
    expect(resultOf(BASE_LINE, "H-7").ok).toBe(true);
  });

  it("落ちる: scope beginners_general + knowledge.reviewStatus draft", () => {
    const line = clone(BASE_LINE);
    line.scope = "beginners_general";
    (line.knowledge as Json).range = "beginners_general";
    const result = resultOf(line, "H-7");
    expect(result.ok).toBe(false);
  });
});

describe("H-8 名前と絶対パスを持たない", () => {
  it("通る: 相対パスのみ", () => {
    expect(resultOf(BASE_LINE, "H-8").ok).toBe(true);
  });

  it("落ちる: provenance.inputs[0] が絶対パス", () => {
    const line = clone(BASE_LINE);
    const absolute = "/tmp/out/p4/pipe-3min/report/time_cause.json";
    (line.provenance as Json).inputs = [absolute];
    (line.counterEvidence as Json).provenance = { inputs: [absolute] };
    const result = resultOf(line, "H-8");
    expect(result.ok).toBe(false);
    expect(result.messages.join(" ")).toContain(absolute);
  });
});

describe("スキーマ(契約の欄)", () => {
  it("通る: 基準の例", () => {
    expect(validate(BASE_LINE, schema)).toEqual([]);
  });

  it("落ちる: 知らない欄", () => {
    const line = clone(BASE_LINE);
    (line as Json).extra = true;
    const errors = validate(line, schema);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors.some((e) => e.includes("知らない欄") && e.includes("extra"))).toBe(true);
  });

  it("落ちる: 版違い", () => {
    const line = clone(BASE_LINE);
    line.schemaVersion = "0.2";
    const errors = validate(line, schema);
    expect(errors.length).toBeGreaterThan(0);
  });

  it("落ちる: value の oneOf(どの型にも合わない値)", () => {
    const line = clone(BASE_LINE) as unknown as { observations: Array<Record<string, unknown>> };
    line.observations[0]!.value = Number.NaN;
    const errors = validate(line, schema);
    expect(errors.some((e) => e.includes("oneOf"))).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// STEP EXPO-1(docs/LANE_DIAG_LOG_2026-09.md §12.9): 版 0.2(knowledge.reviewStatus に expired)。
// 照合する版は行の schemaVersion が決める(opts.schema を渡さない呼び方)。
// ---------------------------------------------------------------------------

/** 版を固定せず、行の schemaVersion から選ばせる(CLI と同じ呼び方)。 */
function checksByVersion(line: unknown, today: string = TODAY): CheckResult[] {
  return validateHypothesisLine(line, { today, registry });
}

const V02_FIXTURE_PATH = fileURLToPath(new URL("./__fixtures__/hypothesis.v0.2.example.json", import.meta.url));
const V02_LINE = JSON.parse(readFileSync(V02_FIXTURE_PATH, "utf-8")) as Json;

/** 既存の記録(obs-3/p4-min3)。02 は H-3 が NG、04・05 は 9 検査すべて ok。 */
const RECORDS_DIR = fileURLToPath(new URL("../records/obs-3/p4-min3/", import.meta.url));
const RECORD_FILES: Array<{ file: string; ngChecks: HypothesisCheckName[] }> = [
  ...["001", "002", "003"].map((n) => ({ file: `02-H-p4-min3-${n}.json`, ngChecks: ["H-3" as HypothesisCheckName] })),
  ...["001", "002", "003"].map((n) => ({ file: `04-H-p4-min3-${n}.json`, ngChecks: [] })),
  ...["001", "002", "003"].map((n) => ({ file: `05-H-p4-min3-${n}.json`, ngChecks: [] })),
];

describe("版 0.2(expired)", () => {
  it("通る: v0.2 の例(reviewStatus expired)は schema ok。同じ行を v0.1 として照合すると落ちる", () => {
    const results = checksByVersion(V02_LINE);
    const schemaResult = results.find((r) => r.check === "schema")!;
    expect(schemaResult.ok, schemaResult.messages.join(" / ")).toBe(true);
    // H-1〜H-8 も基準の例と同じく全部通る(版を上げただけで検査は変わらない)。
    expect(results.filter((r) => !r.ok)).toEqual([]);
    expect((V02_LINE.knowledge as Json).reviewStatus).toBe("expired");

    // v0.1 のスキーマを明示して渡すと、const "0.1" と enum の両方で落ちる。
    const asV01 = validateHypothesisLine(V02_LINE, { today: TODAY, registry, schema });
    expect(asV01.find((r) => r.check === "schema")!.ok).toBe(false);

    // 版の一覧に無い schemaVersion は「照合の相手が決まらない」として schema NG。
    const unknownVersion = clone(V02_LINE);
    unknownVersion.schemaVersion = "9.9";
    const unknownResult = checksByVersion(unknownVersion).find((r) => r.check === "schema")!;
    expect(unknownResult.ok).toBe(false);
    expect(unknownResult.messages.join(" ")).toContain("9.9");
  });

  it("既存の記録(obs-3/p4-min3 の 9 本)は v0.1 として今までどおりの結果になる", () => {
    for (const { file, ngChecks } of RECORD_FILES) {
      const line = JSON.parse(readFileSync(join(RECORDS_DIR, file), "utf-8")) as Json;
      expect(line.schemaVersion, file).toBe("0.1");
      const results = checksByVersion(line);
      expect(results, file).toHaveLength(11); // H-9・H-10 を足した(2026-09-30)
      expect(
        results.filter((r) => !r.ok).map((r) => r.check),
        `${file} の NG の並び`,
      ).toEqual(ngChecks);
    }
    expect(RECORD_FILES).toHaveLength(9);
  });

  it("落ちる: v0.2 で reviewStatus expired かつ scope beginners_general は H-7 が止める", () => {
    const line = clone(V02_LINE);
    line.scope = "beginners_general";
    (line.knowledge as Json).range = "beginners_general";
    // schema そのものは通る(expired は v0.2 の enum にある)。
    expect(checksByVersion(line).find((r) => r.check === "schema")!.ok).toBe(true);
    const h7 = checksByVersion(line).find((r) => r.check === "H-7")!;
    expect(h7.ok).toBe(false);
    expect(h7.messages.join(" ")).toContain("human_reviewed");

    // human_reviewed に上げれば H-7 は通る(止めているのは expired であること)。
    const promoted = clone(line);
    (promoted.knowledge as Json).reviewStatus = "human_reviewed";
    expect(checksByVersion(promoted).find((r) => r.check === "H-7")!.ok).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// STEP 契約の仮説 v0.3(2026-09-26、司令塔の設計判断): lane の enum に reply・fork を足した版。
// v0.1・v0.2 の既存の記録が今までどおり通ることを確かめたうえで、v0.3 で reply・fork が通ることを見る。
// ---------------------------------------------------------------------------

/** v0.1 の既存の記録 3 本(obs-3/p4-min3、02 段階)。読むだけで使う(書き換えない)。 */
const V01_EXISTING_RECORDS_DIR = fileURLToPath(new URL("../records/obs-3/p4-min3/", import.meta.url));
const V01_EXISTING_FILES = ["02-H-p4-min3-001.json", "02-H-p4-min3-002.json", "02-H-p4-min3-003.json"];

/** v0.2 の既存の記録 6 本(obs-3/p4-min3-r2、lane side・time、既に v0.2 の enum にある側)。読むだけで使う。 */
const V02_EXISTING_RECORDS_DIR = fileURLToPath(new URL("../records/obs-3/p4-min3-r2/", import.meta.url));
const V02_EXISTING_FILES = [
  "02-H-side-001.json",
  "02-H-side-002.json",
  "02-H-side-003.json",
  "02-H-time-001.json",
  "02-H-time-002.json",
  "02-H-time-003.json",
];

describe("版 0.3(lane に reply・fork)", () => {
  it("通る: v0.1 の既存の記録 3 本(obs-3/p4-min3)は v0.3 を足しても schema ok のまま", () => {
    for (const file of V01_EXISTING_FILES) {
      const line = JSON.parse(readFileSync(join(V01_EXISTING_RECORDS_DIR, file), "utf-8")) as Json;
      expect(line.schemaVersion, file).toBe("0.1");
      const schemaResult = checksByVersion(line).find((r) => r.check === "schema")!;
      expect(schemaResult.ok, `${file}: ${schemaResult.messages.join(" / ")}`).toBe(true);
    }
    expect(V01_EXISTING_FILES).toHaveLength(3);
  });

  it("通る: v0.2 の既存の記録 6 本(obs-3/p4-min3-r2、lane side・time)は v0.3 を足しても schema ok のまま", () => {
    for (const file of V02_EXISTING_FILES) {
      const line = JSON.parse(readFileSync(join(V02_EXISTING_RECORDS_DIR, file), "utf-8")) as Json;
      expect(line.schemaVersion, file).toBe("0.2");
      const schemaResult = checksByVersion(line).find((r) => r.check === "schema")!;
      expect(schemaResult.ok, `${file}: ${schemaResult.messages.join(" / ")}`).toBe(true);
    }
    expect(V02_EXISTING_FILES).toHaveLength(6);
  });

  it("通る: v0.3 で lane reply・fork が通る(同じ行を v0.2 のまま照合すると enum に無く落ちる)", () => {
    const replyLine = clone(V02_LINE);
    replyLine.lane = "reply";
    const asV02Reply = checksByVersion(replyLine).find((r) => r.check === "schema")!;
    expect(asV02Reply.ok, "lane reply は v0.2 の enum に無いので落ちるはず").toBe(false);

    replyLine.schemaVersion = "0.3";
    const asV03Reply = checksByVersion(replyLine).find((r) => r.check === "schema")!;
    expect(asV03Reply.ok, asV03Reply.messages.join(" / ")).toBe(true);

    const forkLine = clone(V02_LINE);
    forkLine.schemaVersion = "0.3";
    forkLine.lane = "fork";
    const asV03Fork = checksByVersion(forkLine).find((r) => r.check === "schema")!;
    expect(asV03Fork.ok, asV03Fork.messages.join(" / ")).toBe(true);
  });

  it("落ちる: v0.3 でも知らない lane(例 unknown)は落ちる", () => {
    const line = clone(V02_LINE);
    line.schemaVersion = "0.3";
    line.lane = "unknown";
    const result = checksByVersion(line).find((r) => r.check === "schema")!;
    expect(result.ok).toBe(false);
    expect(result.messages.join(" ")).toContain("lane");
    expect(result.messages.join(" ")).toContain("unknown");
  });
});

describe("登録簿(docs/OBSERVATION_ITEMS.md §1)", () => {
  // STEP OBS-5'(docs/LANE_DIAG_LOG_2026-09.md §12.6): obs_extra.json の 3 本を §1.6 に足したので 108→111。
  // STEP OBS-5(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A)): obs_geo.json の 4 本(moveCombination・
  // replyToCapture・replyToCheck・decisionContext)を §1 に足したので 111→115。
  // STEP OBS-5c(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A2)): recognition_measure.json の 4 本
  // (obs.vocab.shapeStatus・intentStatus・openingStatus・exposure)を §1.16 に足したので 115→119。
  // STEP OBS-5e(§12.10 (A4))で obs.vocab.shapeMissingSummary・shapeMovedRequiredSummary を
  // 同じ §1.16 に足したので 119→121。
  // STEP OBS-5d(§12.10 (A3))で obs.fork.sideCrossTable を §1.8 に足したので 121→122。
  // STEP OBS-5f(§12.10 (A5))で obs.vocab.shapeOneAwayDetail・shapeClosestPerGame を
  // 同じ §1.16 に足したので 122→124。
  // STEP OBS-5g(§12.10 (H))で obs.vocab.shapeMovedRequiredPerGame を同じ §1.16 に足したので 124→125。
  // STEP OBS-5h(§12.14)で obs.fork.sideCrossByGame を §1.8 に足したので 125→126。
  // **この試験は、登録簿に行を足したときに必ず落ちる門**(足したことを記録に残させるためにある)。
  // 落ちたら、まず「足した行は意図したものか」を確かめてから数を直す。
  it("existing の大きさは 126", () => {
    expect(registry.size).toBe(126);
  });

  it("obs.timeSearch.col.* は 30 本", () => {
    const columns = [...registry].filter((id) => id.startsWith("obs.timeSearch.col."));
    expect(columns).toHaveLength(30);
  });
});

describe("パリティ(検査 3・禁止語)", () => {
  it("lib が読んだ一覧は report-pdf/check_answer.py の BANNED_WORDS と並びまで一致する(空でも通る)", () => {
    // STEP H5-SYNC(§12.9): lib は一覧の写しを持たず、python の実物を読む。
    // 人間の決定(f715da2)で語が空になっても、この試験は通る(一致を見るだけ)。
    const source = readFileSync(CHECK_ANSWER_PY, "utf-8");
    const match = /BANNED_WORDS\s*=\s*\[([\s\S]*?)\]/.exec(source);
    expect(match, "check_answer.py に BANNED_WORDS が見つからない").not.toBeNull();
    const words = Array.from(match![1]!.matchAll(/"([^"]*)"/g)).map((m) => m[1]!);
    expect([...loadHypothesisBannedWords()]).toEqual(words);
    // 読めないときは黙って空にせず例外(「0 件だった」と「検査していない」を混ぜない)。
    expect(() => loadHypothesisBannedWords(join(REPO_ROOT, "この名前のファイルは無い.py"))).toThrow();
  });
});

describe("CLI(hypothesisCheck.ts)", () => {
  it(
    "子プロセス: 基準の例は exit 0、H-1 が落ちる入力は exit 1",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "hypothesis-check-"));
      try {
        const okPath = join(dir, "ok.json");
        writeFileSync(okPath, JSON.stringify(BASE_LINE), "utf-8");
        const stdout = execFileSync("npx", ["tsx", HYPOTHESIS_CHECK_TS, okPath, "--today", TODAY], {
          cwd: REPO_ROOT,
          encoding: "utf-8",
        });
        expect(stdout).toContain("schema ok");
        expect(stdout).not.toContain("NG");
        // **CLI が表示の 1 か所(`checkResultLines`)を通っていること。**
        // packet を渡していないので H-9 は `skip` ― ここが `H-9 ok` に戻ると、
        // 記録(02-check.txt)を読む人が「照合して通った」と読む(独立監査の指摘。2026-09-30)。
        expect(stdout).toContain("H-9 skip");
        expect(stdout).not.toContain("H-9 ok");

        const badLine = clone(BASE_LINE);
        badLine.statement = "崩れは 31 回で、長考の割合は 56%でした。という読みです。";
        const badPath = join(dir, "bad.json");
        writeFileSync(badPath, JSON.stringify(badLine), "utf-8");
        let failure: { status: number | null; stdout: string } | undefined;
        try {
          execFileSync("npx", ["tsx", HYPOTHESIS_CHECK_TS, badPath, "--today", TODAY], { cwd: REPO_ROOT, encoding: "utf-8" });
        } catch (error) {
          failure = error as { status: number | null; stdout: string };
        }
        expect(failure, "落ちる入力で exit 0 のまま止まらなかった").toBeDefined();
        expect(failure!.status).toBe(1);
        expect(String(failure!.stdout)).toContain("H-1 NG");
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );
});

describe("検査 1 件を人が読む行にする(状態の語は 1 か所)", () => {
  it("n1 packet を渡していない H-9 は skip と書く(ok と書かない)", () => {
    const lines = checkResultLines({
      check: "H-9",
      ok: true,
      skipped: true,
      messages: ["未照合: packet が渡されていないので packetRef を照合していない(参照 2 件)"],
    });
    expect(lines).toHaveLength(1);
    expect(lines[0]!.startsWith("H-9 skip ")).toBe(true);
    // **「ok」と読めないこと**(記録に残って人が読む行なので、ここが本題)
    expect(lines[0]!).not.toContain(" ok ");
    expect(lines[0]!).toContain("未照合");
  });

  it("n2 通った検査は ok、落ちた検査は NG(緩めていないことの裏)", () => {
    expect(checkResultLines({ check: "H-9", ok: true, messages: [] })).toEqual(["H-9 ok"]);
    expect(checkResultLines({ check: "H-1", ok: false, messages: ["あ", "い"] })).toEqual(["H-1 NG あ / い"]);
  });

  it("n3 報告(notes)を落とさない ― 状態の行とは別の行で出す", () => {
    const lines = checkResultLines({
      check: "H-9",
      ok: true,
      messages: [],
      notes: ["observations[0]: この行は数え直せない"],
    });
    expect(lines).toEqual(["H-9 ok", "  (報告) observations[0]: この行は数え直せない"]);
  });
});
