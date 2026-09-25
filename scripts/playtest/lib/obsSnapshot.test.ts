// STEP OBS-3a(docs/LANE_DIAG_LOG_2026-09.md §12.4)。lib/obsSnapshot.ts(SNAPSHOT_ITEMS・numbersOnly・
// buildObsSnapshot)と obsSnapshot.ts(CLI)を見る。**エンジンは起動しない。**
//
// 【構成】11 本(計画の「作るもの」3. + 2026-09-25 の司令塔の REVISE 1 点): 組の絞り込み/numbersOnly が
// person・title・id・sfen を落とす/白いリスト外の文字列が出力に無い(走査)/登録簿に無い obsId を
// SNAPSHOT_ITEMS に足すと例外/入力の kind 違いで例外/無い任意入力の obsId が出ない/inputs[].sha256 と
// basename/items の本数 = SNAPSHOT_ITEMS の本数(材料が揃った fixture)/CLI exit 0・引数不足で 2/合計や
// 割合を作っていない(fixture の数の集合 ⊇ 出力の数の集合)/obs.menu.item の id は M1〜M9 のときだけ残る
// (同じ規則でも M パターンでない id は落ちる)。
//
// fixture(架空の顧客 p9、`person`/`title` は架空の文字列 "X")は __fixtures__/obsSnapshot/ に置く。

import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { recordSha256 } from "./failureEventSchema.js";
import { loadObsRegistry } from "./hypothesis.js";
import {
  buildObsSnapshot,
  buildObsSnapshotFromItems,
  numbersOnly,
  OBS_SNAPSHOT_ENUM_KEYS,
  SNAPSHOT_ITEMS,
  type ObsSnapshotInputFile,
  type ObsSnapshotInputs,
  type ObsSnapshotOptions,
  type SnapshotItemDefinition,
} from "./obsSnapshot.js";

const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const OBS_ITEMS_PATH = fileURLToPath(new URL("../../../docs/OBSERVATION_ITEMS.md", import.meta.url));
const OBS_SNAPSHOT_CLI = fileURLToPath(new URL("../obsSnapshot.ts", import.meta.url));
const FIXTURES_DIR = fileURLToPath(new URL("./__fixtures__/obsSnapshot/", import.meta.url));

const registry = loadObsRegistry(OBS_ITEMS_PATH);

function loadInputFile(name: string): ObsSnapshotInputFile {
  const filePath = join(FIXTURES_DIR, name);
  const bytes = readFileSync(filePath);
  return { name, sha256: recordSha256(bytes), data: JSON.parse(bytes.toString("utf-8")) as unknown };
}

function fullInputs(): ObsSnapshotInputs {
  return {
    patient: loadInputFile("patient.json"),
    timeCause: loadInputFile("time_cause.json"),
    whatifData: loadInputFile("whatif_report_data.json"),
    direct: loadInputFile("direct_answers.json"),
    finalPositions: loadInputFile("final_positions.json"),
    menu: loadInputFile("answer_menu.json"),
    // STEP OBS-5'(docs/LANE_DIAG_LOG_2026-09.md §12.6)。obs_extra.json も任意入力の 1 つとして fullInputs に足した
    // (足さないと「材料が揃った fixture では items.length === SNAPSHOT_ITEMS.length」〈8.〉が壊れる。
    // 既存の他の任意入力〈whatifData・direct・finalPositions・menu〉と同じ扱い)。
    extra: loadInputFile("obs_extra.json"),
    // STEP OBS-5(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A))。obs_geo.json も同じ理由で足した。
    geo: loadInputFile("obs_geo.json"),
  };
}

function optionsOf(group: string): ObsSnapshotOptions {
  return { customer: "p9", group, registry, gitHead: "abc123", dirty: false };
}

function collectNumbers(value: unknown, out: Set<number>): void {
  if (typeof value === "number" && Number.isFinite(value)) out.add(value);
  else if (Array.isArray(value)) for (const item of value) collectNumbers(item, out);
  else if (value !== null && typeof value === "object") for (const v of Object.values(value as Record<string, unknown>)) collectNumbers(v, out);
}

// 1. 組の絞り込み(fixture に 3 分 2 局 + 10 分 1 局 → 2 局)
describe("組の絞り込み", () => {
  it("time_cause の games[]・groups[] は --group に一致するものだけ(3 分 2 局 + 10 分 1 局 → 2 局)", () => {
    const snapshot = buildObsSnapshot(fullInputs(), optionsOf("3 分"));
    const phaseSpentSec = snapshot.items.find((i) => i.obsId === "obs.time.phaseSpentSec");
    expect(phaseSpentSec, "obs.time.phaseSpentSec が出ていない").toBeDefined();
    const rows = phaseSpentSec!.value as Array<{ gameNo: number }>;
    expect(rows.length).toBe(2);
    expect(rows.map((r) => r.gameNo).sort()).toEqual([1, 2]);

    const groupMedians = snapshot.items.find((i) => i.obsId === "obs.time.groupMedians");
    expect((groupMedians!.value as unknown[]).length).toBe(1);
  });
});

// 2. numbersOnly が person・title・id・sfen 等を落とし、白いリストの値は残す
describe("numbersOnly", () => {
  it("許された列挙のキー以外の文字列を落とし、数・真偽・null・許された列挙の値は残す", () => {
    const input = {
      person: "本人の名前",
      title: "冊子の題",
      id: "kifu-a",
      sfen: "lnsgkgsnl/…",
      kifuId: "kifu-a",
      moves: ["7g7f"],
      pv: ["7g7f"],
      actualMove: "7g7f",
      played: "７六歩",
      best: "３四歩",
      text: "説明文",
      labels: { a: "10 秒以上で崩れた手" },
      oneLine: "ひとことで",
      actionCore: "行動の芯",
      evidenceName: "根拠の名",
      verifyName: "答え合わせの名",
      kind: "drop",
      state: "found",
      group: "3 分",
      result: "勝ち",
      ending: "投了",
      side: "先手",
      stage: "時間",
      top1Side: "attack",
      actualSide: "defense",
      n: 3,
      shown: true,
      score: null,
    };
    const stripped = numbersOnly(input) as Record<string, unknown>;
    // スカラーの文字列(そのキー自身が文字列の値を持つ)は、キーごと消える。
    for (const key of ["person", "title", "id", "sfen", "kifuId", "actualMove", "played", "best", "text", "oneLine", "actionCore", "evidenceName", "verifyName"]) {
      expect(Object.hasOwn(stripped, key), `${key} が落ちていない`).toBe(false);
    }
    // 配列・オブジェクトの中の文字列(moves・pv の要素、labels の値)は、入れ物ごとではなく中身だけ落ちる
    // (moves・pv は空配列に、labels は空オブジェクトになる ― キー名 moves・pv・labels 自体は白いリストに無いので、
    // その配下の文字列は 1 つも残らない)。
    expect(stripped.moves).toEqual([]);
    expect(stripped.pv).toEqual([]);
    expect(stripped.labels).toEqual({});
    const baseEnumKeyStrings = OBS_SNAPSHOT_ENUM_KEYS.filter((k): k is string => typeof k === "string");
    for (const key of baseEnumKeyStrings) {
      expect(stripped[key], `${key} が残っていない`).toBe((input as Record<string, unknown>)[key]);
    }
    expect(stripped.n).toBe(3);
    expect(stripped.shown).toBe(true);
    expect(stripped.score).toBeNull();
  });
});

// 3. 出力の全文字列が列挙の白いリストの値だけ(走査)。obsId ごとの extraEnumKeys(id は名前だけを見る。
// 値の形〈M パターン〉の検査は試験 11 が持つ)も許す集合に足す。
function allowedKeyNamesOf(def: SnapshotItemDefinition | undefined): Set<string> {
  const names = new Set<string>();
  for (const allow of OBS_SNAPSHOT_ENUM_KEYS) names.add(typeof allow === "string" ? allow : allow.key);
  for (const allow of def?.extraEnumKeys ?? []) names.add(typeof allow === "string" ? allow : allow.key);
  return names;
}

describe("白いリスト外の文字列", () => {
  it("材料が揃った fixture の出力を走査しても、白いリスト外の文字列は 0 件", () => {
    const snapshot = buildObsSnapshot(fullInputs(), optionsOf("3 分"));
    const offenders: string[] = [];
    const walk = (value: unknown, key: string | null, allowedNames: Set<string>): void => {
      if (typeof value === "string") {
        if (key === null || !allowedNames.has(key)) offenders.push(`${key ?? "(root)"}=${value}`);
        return;
      }
      if (Array.isArray(value)) {
        for (const item of value) walk(item, null, allowedNames);
        return;
      }
      if (value !== null && typeof value === "object") {
        for (const [k, v] of Object.entries(value as Record<string, unknown>)) walk(v, k, allowedNames);
      }
    };
    for (const item of snapshot.items) {
      const def = SNAPSHOT_ITEMS.find((d) => d.obsId === item.obsId);
      walk(item.value, null, allowedKeyNamesOf(def));
    }
    expect(offenders).toEqual([]);
  });
});

// 4. 登録簿にない obsId を SNAPSHOT_ITEMS に足すと例外(試験の中で写しを作って足す)
describe("登録簿(loadObsRegistry)", () => {
  it("SNAPSHOT_ITEMS に登録簿に無い obsId を足すと例外", () => {
    const items = [...SNAPSHOT_ITEMS, { obsId: "obs.bogus.notRegistered", path: "x", pick: () => 1 }];
    expect(() => buildObsSnapshotFromItems(items, fullInputs(), optionsOf("3 分"))).toThrow(/obs\.bogus\.notRegistered/);
  });
});

// 5. 入力の kind 違いで例外
describe("入力の kind", () => {
  it("time_cause・final_positions の kind が違えば例外", () => {
    const inputs = fullInputs();
    const badTimeCause: ObsSnapshotInputs = {
      ...inputs,
      timeCause: { ...inputs.timeCause, data: { ...(inputs.timeCause.data as Record<string, unknown>), kind: "something_else" } },
    };
    expect(() => buildObsSnapshot(badTimeCause, optionsOf("3 分"))).toThrow(/time_cause/);

    const badFinal: ObsSnapshotInputs = {
      ...inputs,
      finalPositions: { ...inputs.finalPositions!, data: { ...(inputs.finalPositions!.data as Record<string, unknown>), kind: "something_else" } },
    };
    expect(() => buildObsSnapshot(badFinal, optionsOf("3 分"))).toThrow(/final_positions/);
  });
});

// 6. 無い任意入力の obsId が出ない(空で埋めない)
describe("任意入力が無いとき", () => {
  it("fork.*・direct.*・menu.item・(STEP OBS-5')time.pairSpent 等の obsId は出ない", () => {
    const inputs = fullInputs();
    const minimal: ObsSnapshotInputs = { patient: inputs.patient, timeCause: inputs.timeCause };
    const snapshot = buildObsSnapshot(minimal, optionsOf("3 分"));
    const obsIds = snapshot.items.map((i) => i.obsId);
    const optionalOnly = [
      "obs.fork.values",
      "obs.fork.game",
      "obs.fork.representative",
      "obs.fork.scene",
      "obs.fork.summary",
      "obs.direct.answer",
      "obs.direct.counts",
      "obs.direct.finalPosition",
      "obs.menu.item",
      // STEP OBS-5'(docs/LANE_DIAG_LOG_2026-09.md §12.6)。--extra を渡さなければこの 3 本も出ない。
      "obs.time.pairSpent",
      "obs.time.phaseMoves",
      "obs.time.phaseSecPerMoveMedians",
      // STEP OBS-5(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A))。--geo を渡さなければこの 4 本も出ない。
      "obs.geo.moveCombination",
      "obs.geo.replyToCapture",
      "obs.geo.replyToCheck",
      "obs.time.decisionContext",
    ];
    for (const id of optionalOnly) expect(obsIds, id).not.toContain(id);
    expect(snapshot.items.length).toBe(SNAPSHOT_ITEMS.length - optionalOnly.length);
  });
});

// 7. inputs[].sha256 と basename
describe("inputs[]", () => {
  it("name は basename・sha256 は recordSha256 と一致", () => {
    const inputs = fullInputs();
    const snapshot = buildObsSnapshot(inputs, optionsOf("3 分"));
    expect(snapshot.inputs.map((i) => i.name).sort()).toEqual(
      ["answer_menu.json", "direct_answers.json", "final_positions.json", "obs_extra.json", "obs_geo.json", "patient.json", "time_cause.json", "whatif_report_data.json"].sort(),
    );
    for (const name of [
      "patient.json",
      "time_cause.json",
      "whatif_report_data.json",
      "direct_answers.json",
      "final_positions.json",
      "answer_menu.json",
      "obs_extra.json",
      "obs_geo.json",
    ]) {
      const expected = recordSha256(readFileSync(join(FIXTURES_DIR, name)));
      const found = snapshot.inputs.find((i) => i.name === name);
      expect(found?.sha256, name).toBe(expected);
    }
  });
});

// 8. items の本数 = 材料が揃った fixture で SNAPSHOT_ITEMS の本数
describe("items の本数", () => {
  it("材料が揃った fixture では items.length === SNAPSHOT_ITEMS.length", () => {
    const snapshot = buildObsSnapshot(fullInputs(), optionsOf("3 分"));
    expect(snapshot.items.length).toBe(SNAPSHOT_ITEMS.length);
  });
});

// 9. CLI: exit 0(揃った引数)・引数不足で exit 2
describe("CLI(obsSnapshot.ts)", () => {
  it(
    "子プロセス: 揃った引数は exit 0(items.length が一致)、引数不足は exit 2",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "obs-snapshot-cli-"));
      try {
        const outPath = join(dir, "obs_snapshot.json");
        const stdout = execFileSync(
          "npx",
          [
            "tsx",
            OBS_SNAPSHOT_CLI,
            "--customer",
            "p9",
            "--group",
            "3 分",
            "--patient",
            join(FIXTURES_DIR, "patient.json"),
            "--time-cause",
            join(FIXTURES_DIR, "time_cause.json"),
            "--whatif-data",
            join(FIXTURES_DIR, "whatif_report_data.json"),
            "--direct",
            join(FIXTURES_DIR, "direct_answers.json"),
            "--final-positions",
            join(FIXTURES_DIR, "final_positions.json"),
            "--menu",
            join(FIXTURES_DIR, "answer_menu.json"),
            // STEP OBS-5'(docs/LANE_DIAG_LOG_2026-09.md §12.6)。--extra を足さないと items.length が
            // SNAPSHOT_ITEMS.length と合わなくなる(他の任意入力と同じ理由)。
            "--extra",
            join(FIXTURES_DIR, "obs_extra.json"),
            // STEP OBS-5(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A))。同じ理由で --geo も足す。
            "--geo",
            join(FIXTURES_DIR, "obs_geo.json"),
            "--out",
            outPath,
          ],
          { cwd: REPO_ROOT, encoding: "utf-8" },
        );
        expect(stdout).toContain("書き込み");
        const written = JSON.parse(readFileSync(outPath, "utf-8")) as { items: unknown[] };
        expect(written.items.length).toBe(SNAPSHOT_ITEMS.length);

        let failure: { status: number | null } | undefined;
        try {
          execFileSync("npx", ["tsx", OBS_SNAPSHOT_CLI, "--customer", "p9"], { cwd: REPO_ROOT, encoding: "utf-8" });
        } catch (error) {
          failure = error as { status: number | null };
        }
        expect(failure, "引数不足で止まらなかった").toBeDefined();
        expect(failure!.status).toBe(2);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );
});

// 10. 合計や割合を作っていない(fixture の数の集合 ⊇ 出力の数の集合)
describe("新しい数を作っていない", () => {
  it("出力の数の集合は、入力ファイルの数の集合の部分集合(合計・割合を新しく作っていない)", () => {
    const inputs = fullInputs();
    const fixtureNumbers = new Set<number>();
    for (const file of [inputs.patient, inputs.timeCause, inputs.whatifData!, inputs.direct!, inputs.finalPositions!, inputs.menu!, inputs.extra!, inputs.geo!]) {
      collectNumbers(file.data, fixtureNumbers);
    }
    const snapshot = buildObsSnapshot(inputs, optionsOf("3 分"));
    const outputNumbers = new Set<number>();
    for (const item of snapshot.items) collectNumbers(item.value, outputNumbers);
    const extra = [...outputNumbers].filter((n) => !fixtureNumbers.has(n));
    expect(extra).toEqual([]);
  });
});

// 11. obs.menu.item の id は M1〜M9(^M[0-9]+$)のときだけ残る(2026-09-25 の司令塔の REVISE)。
// 同じ規則(base ∪ obs.menu.item の extraEnumKeys)でも、M パターンでない id(fixture の games[].id)は落ちる。
describe("obs.menu.item の id", () => {
  it("menu の id(M1〜M9)は残り、同じ規則でも M パターンでない id(games[].id)は落ちる", () => {
    const snapshot = buildObsSnapshot(fullInputs(), optionsOf("3 分"));
    const menuItem = snapshot.items.find((i) => i.obsId === "obs.menu.item");
    expect(menuItem, "obs.menu.item が出ていない").toBeDefined();
    const ids = (menuItem!.value as Array<{ id?: string }>).map((i) => i.id);
    expect(ids).toEqual(["M1", "M9"]); // fixture の answer_menu.json の 2 件

    const menuDef = SNAPSHOT_ITEMS.find((d) => d.obsId === "obs.menu.item")!;
    const allowedForMenu = [...OBS_SNAPSHOT_ENUM_KEYS, ...(menuDef.extraEnumKeys ?? [])];
    const patient = JSON.parse(readFileSync(join(FIXTURES_DIR, "patient.json"), "utf-8")) as { games: Array<{ id: string }> };
    const nonMenuId = patient.games[0]!.id; // "kifu-a"(M パターンでない)
    const stripped = numbersOnly({ id: nonMenuId }, allowedForMenu) as Record<string, unknown>;
    expect(Object.hasOwn(stripped, "id"), "M パターンでない id が残ってしまった").toBe(false);
  });
});

// 12. STEP OBS-5'(docs/LANE_DIAG_LOG_2026-09.md §12.6)。--extra(obs_extra.json)の 3 項目。
describe("--extra(obs_extra.json。STEP OBS-5')", () => {
  it("渡せば obs.time.pairSpent・phaseMoves・phaseSecPerMoveMedians の 3 項目が載る(fixture の値をそのまま写す)", () => {
    const snapshot = buildObsSnapshot(fullInputs(), optionsOf("3 分"));
    const pairSpent = snapshot.items.find((i) => i.obsId === "obs.time.pairSpent");
    const phaseMoves = snapshot.items.find((i) => i.obsId === "obs.time.phaseMoves");
    const medians = snapshot.items.find((i) => i.obsId === "obs.time.phaseSecPerMoveMedians");
    expect(pairSpent, "obs.time.pairSpent が出ていない").toBeDefined();
    expect(phaseMoves, "obs.time.phaseMoves が出ていない").toBeDefined();
    expect(medians, "obs.time.phaseSecPerMoveMedians が出ていない").toBeDefined();

    const extraFixture = JSON.parse(readFileSync(join(FIXTURES_DIR, "obs_extra.json"), "utf-8")) as {
      pairs: unknown[];
      phaseMoves: unknown[];
      phaseSecPerMoveMedians: unknown;
    };
    // numbersOnly は phase(early/mid/late)を extraEnumKeys で残すので、pairs はそのまま一致する。
    expect(pairSpent!.value).toEqual(extraFixture.pairs);
    expect(phaseMoves!.value).toEqual(extraFixture.phaseMoves);
    expect(medians!.value).toEqual(extraFixture.phaseSecPerMoveMedians);
  });

  it("渡さなければ 3 項目とも出ない(空で埋めない。任意入力が無いときの一般規則と同じ)", () => {
    const inputs = fullInputs();
    const minimal: ObsSnapshotInputs = { patient: inputs.patient, timeCause: inputs.timeCause };
    const snapshot = buildObsSnapshot(minimal, optionsOf("3 分"));
    const obsIds = snapshot.items.map((i) => i.obsId);
    expect(obsIds).not.toContain("obs.time.pairSpent");
    expect(obsIds).not.toContain("obs.time.phaseMoves");
    expect(obsIds).not.toContain("obs.time.phaseSecPerMoveMedians");
  });
});

// 13. STEP OBS-5(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A))。--geo(obs_geo.json)の 4 項目。
describe("--geo(obs_geo.json。STEP OBS-5)", () => {
  it("渡せば obs.geo.moveCombination・replyToCapture・replyToCheck・obs.time.decisionContext の 4 項目が載る(fixture の値をそのまま写す)", () => {
    const snapshot = buildObsSnapshot(fullInputs(), optionsOf("3 分"));
    const moveCombination = snapshot.items.find((i) => i.obsId === "obs.geo.moveCombination");
    const replyToCapture = snapshot.items.find((i) => i.obsId === "obs.geo.replyToCapture");
    const replyToCheck = snapshot.items.find((i) => i.obsId === "obs.geo.replyToCheck");
    const decisionContext = snapshot.items.find((i) => i.obsId === "obs.time.decisionContext");
    expect(moveCombination, "obs.geo.moveCombination が出ていない").toBeDefined();
    expect(replyToCapture, "obs.geo.replyToCapture が出ていない").toBeDefined();
    expect(replyToCheck, "obs.geo.replyToCheck が出ていない").toBeDefined();
    expect(decisionContext, "obs.time.decisionContext が出ていない").toBeDefined();

    const geoFixture = JSON.parse(readFileSync(join(FIXTURES_DIR, "obs_geo.json"), "utf-8")) as {
      moves: Array<{ gameNo: number; kifPly: number; side: string; facts: unknown; combination: string; replyToCapture: string; replyToCheck: string }>;
      decisionContext: unknown[];
    };
    expect(moveCombination!.value).toEqual(
      geoFixture.moves.map((m) => ({ gameNo: m.gameNo, kifPly: m.kifPly, side: m.side, facts: m.facts, combination: m.combination })),
    );
    expect(replyToCapture!.value).toEqual(geoFixture.moves.map((m) => ({ gameNo: m.gameNo, kifPly: m.kifPly, replyToCapture: m.replyToCapture })));
    expect(replyToCheck!.value).toEqual(geoFixture.moves.map((m) => ({ gameNo: m.gameNo, kifPly: m.kifPly, replyToCheck: m.replyToCheck })));
    // numbersOnly は spentBucket・phase・evalBand を extraEnumKeys で残すので、decisionContext はそのまま一致する。
    expect(decisionContext!.value).toEqual(geoFixture.decisionContext);
  });

  it("渡さなければ 4 項目とも出ない(空で埋めない。任意入力が無いときの一般規則と同じ)", () => {
    const inputs = fullInputs();
    const minimal: ObsSnapshotInputs = { patient: inputs.patient, timeCause: inputs.timeCause };
    const snapshot = buildObsSnapshot(minimal, optionsOf("3 分"));
    const obsIds = snapshot.items.map((i) => i.obsId);
    expect(obsIds).not.toContain("obs.geo.moveCombination");
    expect(obsIds).not.toContain("obs.geo.replyToCapture");
    expect(obsIds).not.toContain("obs.geo.replyToCheck");
    expect(obsIds).not.toContain("obs.time.decisionContext");
  });
});
