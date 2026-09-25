// STEP OPEN-2(docs/LANE_DIAG_LOG_2026-09.md §12.8)。lib/recognitionMeasure.ts の試験。
//
// (1)〜(5) は数え方そのもの(小さな作り物の形・狙い・戦型で、1 局面ずつ数を突き合わせる)。
// (6) は CLI(scripts/playtest/recognitionMeasure.ts)を実際に spawn する。
// (7)(8) は局数の欄(STEP OPEN-2b)。(9)〜(11) は露出の欄(STEP EXPO-1、§12.9)。
// **一時ディレクトリ以外に書かない**(他の CLI 試験と同じ理由。作業ツリーへは書かない)。
//
// 【作り物の形・戦型・狙いについて】
// ここで作る required_pieces / recognition_pattern は**将棋知識ではない**。実在の囲い・戦型とは
// 無関係で、「指し手で作られた駒」「初期配置のままの駒」「盤に無い駒」を 1 局面の中に作り分ける
// ために置いただけの駒とマスの対である(openingDetector.test.ts の makeOpening と同じ流儀)。

import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, describe, expect, it } from "vitest";

import type { IntentDefinition } from "../../../apps/server/src/analysis/intentRepository.js";
import { loadIntents } from "../../../apps/server/src/analysis/intentRepository.js";
import type { OpeningDefinition } from "../../../apps/server/src/analysis/openingDetector.js";
import type { ShapeDefinition } from "../../../apps/server/src/analysis/shapeRepository.js";
import { loadShapes } from "../../../apps/server/src/analysis/shapeRepository.js";
import {
  measureRecognition,
  plyStepsOf,
  type GameRow,
  type MeasuredGame,
  type MeasureRecognitionOptions,
} from "./recognitionMeasure.js";

const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const CLI_TS = fileURLToPath(new URL("../recognitionMeasure.ts", import.meta.url));
const KIFU_DIR = fileURLToPath(new URL("../kifu/", import.meta.url));

/** 既知の正解に使う固定棋譜 4 局(`-round2` は含めない)。docs/BASELINE_2026-09-12.md §2 と同じ 4 局。 */
const FIXED_4_IDS = [
  "2026-09-10-claude-10moves",
  "2026-09-12-live-30moves-claude-1",
  "2026-09-12-live-30moves-claude-2",
  "2026-09-12-live-30moves-claude-3",
];

const tmpDirs: string[] = [];
function makeTmpDir(): string {
  const dir = mkdtempSync(join(tmpdir(), "recognition-measure-"));
  tmpDirs.push(dir);
  return dir;
}
afterAll(() => {
  for (const dir of tmpDirs) rmSync(dir, { recursive: true, force: true });
});

// ---- 作り物(将棋知識ではない) ----

/** 先手が 7g7f と 3i3h、後手が 3c3d と 8c8d を指すだけの並び。ply 0 / 2 / 4 の 3 局面を作る。 */
const MOVES_4 = ["7g7f", "3c3d", "3i3h", "8c8d"];
/** ply 0 / 2 の 2 局面だけを作る並び。 */
const MOVES_2 = ["7g7f", "3c3d"];

function makeShape(
  id: string,
  side: ShapeDefinition["side"],
  pieces: Array<{ piece: string; square: string }>,
): ShapeDefinition {
  return {
    id,
    name: `試験用の形_${id}`,
    name_kana: `しけんようのかたち_${id}`,
    side,
    family: "試験用",
    parent_shape_id: null,
    required_pieces: pieces.map((p) => ({ ...p, optional: false })),
    characteristics: "",
    confidence_level: "low",
    review_status: "draft",
  };
}

function makeIntent(id: string, pattern: Array<{ piece: string; to: string }>): IntentDefinition {
  return {
    id,
    name: `試験用の狙い_${id}`,
    opening_id: "test_opening",
    recognition_pattern: pattern,
    current_aim_explanation: "",
    next_aim_explanation: "",
    confidence_level: "low",
    review_status: "draft",
  };
}

function makeOpening(
  id: string,
  side: OpeningDefinition["side"],
  pattern: Array<{ piece: string; to: string }>,
): OpeningDefinition {
  return {
    id,
    name: `試験用の戦型_${id}`,
    name_kana: `しけんようのせんけい_${id}`,
    side,
    family: "試験用",
    leads_to_shape_ids: [],
    recognition_pattern: pattern,
    source: "試験用のダミー(将棋知識ではない)",
    confidence_level: "low",
    review_status: "draft",
  };
}

const NO_KNOWLEDGE: Omit<MeasureRecognitionOptions, "maxPly"> = { shapes: [], intents: [], openings: [] };

/** 1 局だけ測って行を返す(渡さなかった種類は空のまま)。 */
function measureOne(moves: string[], options: Partial<MeasureRecognitionOptions> & { maxPly: number }): GameRow {
  const game: MeasuredGame = { group: "g", id: "test-01", moves };
  return measureRecognition([game], { ...NO_KNOWLEDGE, ...options }).rows[0]!;
}

/** 固定棋譜 4 局を読む。 */
function readFixed4(): MeasuredGame[] {
  return FIXED_4_IDS.map((id) => {
    const fixed = JSON.parse(readFileSync(join(KIFU_DIR, `${id}.json`), "utf-8")) as {
      id: string;
      moves: string[];
      startSfen?: string;
    };
    return { group: "fixed4", id: fixed.id, moves: fixed.moves, startSfen: fixed.startSfen };
  });
}

// ---- (1) 分母 ----

describe("(1) 分母は ply 0, 2, 4, … ≤ min(maxPly, 手数)", () => {
  it("maxPly 30 と 0 で数が合い、固定棋譜 4 局 + 本体の形・狙いで既知の正解 34/59 が出る", () => {
    // maxPly 0 は全手。ply が奇数の局は、最後は先手番の局面で止まる。
    expect(plyStepsOf(0, 0)).toEqual([0]);
    expect(plyStepsOf(4, 0)).toEqual([0, 2, 4]);
    expect(plyStepsOf(5, 0)).toEqual([0, 2, 4]);
    // 30 未満(20 手)は maxPly 30 を渡しても手数で止まり、maxPly 0 と同じになる。
    expect(plyStepsOf(20, 30)).toHaveLength(11);
    expect(plyStepsOf(20, 0)).toEqual(plyStepsOf(20, 30));
    // 30 を超える局は maxPly 30 で切られる。maxPly 0 なら最後まで。
    expect(plyStepsOf(40, 30)).toHaveLength(16);
    expect(plyStepsOf(40, 30).at(-1)).toBe(30);
    expect(plyStepsOf(40, 0)).toHaveLength(21);
    expect(plyStepsOf(31, 0)).toHaveLength(16);
    expect(plyStepsOf(31, 0).at(-1)).toBe(30);

    // measureRecognition の positions が同じ数になる。
    expect(measureOne(MOVES_4, { maxPly: 0 }).positions).toBe(3);
    expect(measureOne(MOVES_2, { maxPly: 0 }).positions).toBe(2);
    expect(measureOne(MOVES_4, { maxPly: 2 }).positions).toBe(2);

    // 既知の正解 = docs/BASELINE_2026-09-12.md §2「全手数 59・認識あり 34」。
    // この 2 つが動いたら、数え方・本番の判定・本体のデータのどれかが変わったということ。
    // (本体の data/shapes・data/intents を増やす変更には人間の承認が要るので、ここで結合してよい。
    //  下書き data/drafts/ の件数には結合しない ― そちらは CLI で測る。)
    const shapes = loadShapes(join(REPO_ROOT, "data", "shapes"));
    const intents = loadIntents(join(REPO_ROOT, "data", "intents"));
    const { byGroup } = measureRecognition(readFixed4(), { shapes, intents, openings: [], maxPly: 0 });
    expect(byGroup["fixed4"]?.positions).toBe(59);
    expect(byGroup["fixed4"]?.recShape).toBe(34);
    // 4 局とも 30 手以内なので、maxPly 30 でも同じ分母になる。
    const capped = measureRecognition(readFixed4(), { shapes, intents, openings: [], maxPly: 30 });
    expect(capped.byGroup["fixed4"]?.positions).toBe(59);
  });
});

// ---- (2) 「強い」の定義 ----

describe("(2) 強い = completed か証拠 2 件以上", () => {
  it("証拠 1 件の forming は強くない / completed は証拠 0 件でも強い / 狙いも同じ数え方", () => {
    // 7f(歩を動かした)・3h(銀を動かした)は証拠あり、5h は空。
    const strong = measureOne(MOVES_4, {
      maxPly: 0,
      shapes: [
        makeShape("t_strong", "self", [
          { piece: "歩", square: "7f" },
          { piece: "銀", square: "3h" },
          { piece: "金", square: "5h" },
        ]),
      ],
    });
    // ply 0 は一致 0 件 → none。ply 2 は証拠 1 件の forming(強くない)。ply 4 は証拠 2 件の forming(強い)。
    expect(strong.recShape).toBe(2);
    expect(strong.recShapeEvid2).toBe(1);
    expect(strong.silentEvid2).toBe(2);

    // 7f だけが証拠で、7i の銀は初期配置のまま(証拠にならない)。2h は飛なので欠け。
    const weak = measureOne(MOVES_4, {
      maxPly: 0,
      shapes: [
        makeShape("t_weak", "self", [
          { piece: "歩", square: "7f" },
          { piece: "銀", square: "7i" },
          { piece: "玉", square: "2h" },
        ]),
      ],
    });
    expect(weak.recShape).toBe(2);
    expect(weak.recShapeEvid2).toBe(0);
    expect(weak.silentEvid2).toBe(3);

    // 4i の金は初期配置のまま = 証拠 0 件。欠けが無いので completed = 強い。
    const completed = measureOne(MOVES_4, {
      maxPly: 0,
      shapes: [makeShape("t_completed", "self", [{ piece: "金", square: "4i" }])],
    });
    expect(completed.recShapeEvid2).toBe(3);
    expect(completed.silentEvid2).toBe(0);
    expect(completed.shapeCompleted["t_completed"]).toBe(3);

    // 狙いは相手(後手)の指し手だけを見る。後手は 3c3d と 8c8d を指した。
    const formingIntent = measureOne(MOVES_4, {
      maxPly: 0,
      intents: [
        makeIntent("t_forming", [
          { piece: "歩", to: "3d" },
          { piece: "銀", to: "6b" },
        ]),
      ],
    });
    expect(formingIntent.recIntent).toBe(2);
    expect(formingIntent.recIntent2).toBe(0);

    const matchedIntent = measureOne(MOVES_4, {
      maxPly: 0,
      intents: [makeIntent("t_matched", [{ piece: "歩", to: "3d" }])],
    });
    expect(matchedIntent.recIntent).toBe(2);
    expect(matchedIntent.recIntent2).toBe(2);
  });
});

// ---- (3) 沈黙は側ごと ----

describe("(3) 沈黙は自分側・相手側・全体を別々に数える", () => {
  it("形は recEvid2Self / recEvid2Opp、戦型は openSilentSelf / openSilentOpp / openSilentAny が別の数になる", () => {
    const selfShape = makeShape("t_self", "self", [
      { piece: "歩", square: "7f" },
      { piece: "銀", square: "3h" },
      { piece: "金", square: "5h" },
    ]);
    const oppShape = makeShape("t_opp", "opponent", [
      { piece: "歩", square: "3d" },
      { piece: "歩", square: "8d" },
      { piece: "金", square: "5b" },
    ]);

    const onlySelf = measureOne(MOVES_4, { maxPly: 0, shapes: [selfShape] });
    expect(onlySelf.recEvid2Self).toBe(1);
    expect(onlySelf.recEvid2Opp).toBe(0);
    expect(onlySelf.silentEvid2).toBe(2);

    const onlyOpp = measureOne(MOVES_4, { maxPly: 0, shapes: [oppShape] });
    expect(onlyOpp.recEvid2Self).toBe(0);
    expect(onlyOpp.recEvid2Opp).toBe(1);
    expect(onlyOpp.silentEvid2).toBe(2);

    const both = measureOne(MOVES_4, { maxPly: 0, shapes: [selfShape, oppShape] });
    expect(both.recEvid2Self).toBe(1);
    expect(both.recEvid2Opp).toBe(1);
    expect(both.silentEvid2).toBe(2);

    // 戦型。自分側は ply 4 でだけ強い → 自分側の沈黙 2。相手側の戦型は 1 件も無いので 3 局面すべて沈黙。
    const openSelf = measureOne(MOVES_4, {
      maxPly: 0,
      openings: [
        makeOpening("o_self", "self", [
          { piece: "歩", to: "7f" },
          { piece: "銀", to: "3h" },
          { piece: "金", to: "5h" },
        ]),
      ],
    });
    expect(openSelf.openSilentSelf).toBe(2);
    expect(openSelf.openSilentOpp).toBe(3);
    expect(openSelf.openSilentAny).toBe(2);

    const openOpp = measureOne(MOVES_4, {
      maxPly: 0,
      openings: [
        makeOpening("o_opp", "opponent", [
          { piece: "歩", to: "3d" },
          { piece: "歩", to: "8d" },
          { piece: "金", to: "5b" },
        ]),
      ],
    });
    expect(openOpp.openSilentSelf).toBe(3);
    expect(openOpp.openSilentOpp).toBe(2);
    expect(openOpp.openSilentAny).toBe(2);
  });
});

// ---- (4) I-9 は立った行だけ ----

describe("(4) I-9 相当は立った行だけに当たる", () => {
  it("none の行は数えず、forming は自分側・相手側を分けて数える(戦型は forming の行だけ)", () => {
    // 4i の金は初期配置のまま一致(証拠 0)。2h は飛なので欠け、5h は空なので欠け → status は none。
    const noneRow = measureOne(MOVES_2, {
      maxPly: 0,
      shapes: [
        makeShape("t_none", "self", [
          { piece: "金", square: "4i" },
          { piece: "玉", square: "2h" },
          { piece: "飛", square: "5h" },
        ]),
      ],
    });
    // 「証拠 ≤ 1 かつ 欠け ≥ 2」を満たすが、立っていない(none)ので数えない。
    expect(noneRow.recShape).toBe(0);
    expect(noneRow.i9type).toBe(0);

    const selfRow = measureOne(MOVES_2, {
      maxPly: 0,
      shapes: [
        makeShape("t_forming_self", "self", [
          { piece: "歩", square: "7f" },
          { piece: "玉", square: "2h" },
          { piece: "飛", square: "5h" },
        ]),
      ],
    });
    expect(selfRow.recShape).toBe(1);
    expect(selfRow.i9type).toBe(1);
    expect(selfRow.i9Opp).toBe(0);

    const oppRow = measureOne(MOVES_2, {
      maxPly: 0,
      shapes: [
        makeShape("t_forming_opp", "opponent", [
          { piece: "歩", square: "3d" },
          { piece: "玉", square: "2b" },
          { piece: "飛", square: "5b" },
        ]),
      ],
    });
    expect(oppRow.recShape).toBe(1);
    expect(oppRow.i9type).toBe(1);
    expect(oppRow.i9Opp).toBe(1);

    // 戦型は forming の行だけに当てる(completed の行は数えない)。
    const openRow = measureOne(MOVES_2, {
      maxPly: 0,
      openings: [
        makeOpening("o_completed", "self", [{ piece: "金", to: "4i" }]),
        makeOpening("o_forming", "self", [
          { piece: "歩", to: "7f" },
          { piece: "玉", to: "2h" },
          { piece: "飛", to: "5h" },
        ]),
      ],
    });
    expect(openRow.openCompleted).toBe(2);
    expect(openRow.openForming).toBe(1);
    expect(openRow.openI9Self).toBe(1);
    expect(openRow.openI9Opp).toBe(0);
  });
});

// ---- (5) 戦型の証拠 0 の completed ----

describe("(5) 戦型の「証拠 0 件の completed」", () => {
  it("数えられ、openCompNoEvidById に id で入る(証拠のある completed は入らない)", () => {
    const result = measureRecognition([{ group: "g", id: "test-01", moves: MOVES_2 }], {
      shapes: [],
      intents: [],
      openings: [
        // 4i の金は初期配置のまま = 証拠 0 件の completed(ply 0・2 の 2 局面)。
        makeOpening("o_no_evidence", "self", [{ piece: "金", to: "4i" }]),
        // 7f は指し手で作られた = 証拠 1 件の completed(ply 2 だけ)。
        makeOpening("o_with_evidence", "self", [{ piece: "歩", to: "7f" }]),
      ],
      maxPly: 0,
    });
    const row = result.rows[0]!;
    expect(row.openCompleted).toBe(3);
    expect(row.openCompletedNoEvidence).toBe(2);
    expect(row.openCompNoEvidById).toEqual({ o_no_evidence: 2 });

    // byGroup にも id のまま足し上がる。
    expect(result.byGroup["g"]?.openCompletedNoEvidence).toBe(2);
    expect(result.byGroup["g"]?.openCompNoEvidById).toEqual({ o_no_evidence: 2 });
  });
});

// ---- (6) CLI ----

describe("(6) CLI(scripts/playtest/recognitionMeasure.ts)", () => {
  it("exit 0 で kind と byGroup が読める / --games が無ければ exit 2", () => {
    const dir = makeTmpDir();
    const listPath = join(dir, "games.json");
    const outPath = join(dir, "out.json");
    writeFileSync(
      listPath,
      JSON.stringify({
        games: FIXED_4_IDS.map((id) => ({ group: "fixed4", id, path: join(KIFU_DIR, `${id}.json`) })),
      }),
      "utf-8",
    );

    const ok = spawnSync(
      "npx",
      [
        "tsx",
        CLI_TS,
        "--games",
        listPath,
        "--shapes",
        join(REPO_ROOT, "data", "shapes"),
        "--intents",
        join(REPO_ROOT, "data", "intents"),
        "--maxply",
        "0",
        "--out",
        outPath,
      ],
      { cwd: REPO_ROOT, encoding: "utf-8" },
    );
    expect(ok.status).toBe(0);

    const written = JSON.parse(readFileSync(outPath, "utf-8")) as {
      kind: string;
      schemaVersion: string;
      maxPly: number;
      shapesDirs: string[];
      openingsDirs: string[];
      byGroup: Record<string, { positions: number; recShape: number }>;
      rows: Array<{ id: string }>;
    };
    expect(written.kind).toBe("recognition_measure");
    expect(written.schemaVersion).toBe("0.1");
    expect(written.maxPly).toBe(0);
    expect(written.byGroup["fixed4"]?.positions).toBe(59);
    expect(written.byGroup["fixed4"]?.recShape).toBe(34);
    expect(written.rows.map((r) => r.id)).toEqual(FIXED_4_IDS);
    // 入力ディレクトリは cwd 相対で残す(絶対パスを書かない)。
    expect(written.shapesDirs).toEqual(["data/shapes"]);
    expect(written.openingsDirs).toEqual([]);

    const missing = spawnSync("npx", ["tsx", CLI_TS, "--maxply", "0", "--out", join(dir, "never.json")], {
      cwd: REPO_ROOT,
      encoding: "utf-8",
    });
    expect(missing.status).toBe(2);
    expect(missing.stderr).toContain("--games");
  }, 60_000);
});

// ---- (7) 局数は延べでない(STEP OPEN-2b) ----

describe("(7) レコード 1 件ごとの局数は延べ局面ではない", () => {
  it("同じ局の 2 局面以上で立っても 1、2 局で立てば 2", () => {
    // 形・戦型は ply 2・4 の 2 局面で forming(完成はしない)。
    const shape = makeShape("t_on", "self", [
      { piece: "歩", square: "7f" },
      { piece: "銀", square: "3h" },
      { piece: "金", square: "5h" },
    ]);
    // 狙いは ply 2・4 の 2 局面で matched。
    const intent = makeIntent("t_on_intent", [{ piece: "歩", to: "3d" }]);
    const openForming = makeOpening("o_on", "self", [
      { piece: "歩", to: "7f" },
      { piece: "銀", to: "3h" },
      { piece: "金", to: "5h" },
    ]);
    // 4i の金は初期配置のまま = ply 0・2・4 の 3 局面で completed。
    const openCompleted = makeOpening("o_comp", "self", [{ piece: "金", to: "4i" }]);
    const options: MeasureRecognitionOptions = {
      shapes: [shape],
      intents: [intent],
      openings: [openForming, openCompleted],
      maxPly: 0,
    };

    const one = measureRecognition([{ group: "g", id: "a", moves: MOVES_4 }], options);
    const row = one.rows[0]!;
    // 延べ(局面の数)は 2・2・3 だが、rows が持つのは「この局に出た id」の集合。
    expect(row.shapeHits["t_on"]).toBe(2);
    expect(row.intentHits["t_on_intent"]).toBe(2);
    expect(row.openCompleted).toBe(3);
    expect(row.shapeOnIds).toEqual(["t_on"]);
    expect(row.shapeCompIds).toEqual([]);
    expect(row.intentOnIds).toEqual(["t_on_intent"]);
    expect(row.intentCompIds).toEqual(["t_on_intent"]);
    expect(row.openOnIds).toEqual(["o_comp", "o_on"]);
    expect(row.openCompIds).toEqual(["o_comp"]);

    const oneTotals = one.byGroup["g"]!;
    expect(oneTotals.games).toBe(1);
    expect(oneTotals.shapeOnGames).toEqual({ t_on: 1 });
    expect(oneTotals.shapeCompGames).toEqual({});
    expect(oneTotals.intentOnGames).toEqual({ t_on_intent: 1 });
    expect(oneTotals.intentCompGames).toEqual({ t_on_intent: 1 });
    expect(oneTotals.openOnGames).toEqual({ o_comp: 1, o_on: 1 });
    expect(oneTotals.openCompGames).toEqual({ o_comp: 1 });

    // 同じ並びを 2 局に分けると、局数だけが 2 になる(延べは 2 倍)。
    const two = measureRecognition(
      [
        { group: "g", id: "a", moves: MOVES_4 },
        { group: "g", id: "b", moves: MOVES_4 },
      ],
      options,
    );
    const twoTotals = two.byGroup["g"]!;
    expect(twoTotals.games).toBe(2);
    expect(twoTotals.shapeHits["t_on"]).toBe(4);
    expect(twoTotals.openCompleted).toBe(6);
    expect(twoTotals.shapeOnGames).toEqual({ t_on: 2 });
    expect(twoTotals.shapeCompGames).toEqual({});
    expect(twoTotals.intentOnGames).toEqual({ t_on_intent: 2 });
    expect(twoTotals.intentCompGames).toEqual({ t_on_intent: 2 });
    expect(twoTotals.openOnGames).toEqual({ o_comp: 2, o_on: 2 });
    expect(twoTotals.openCompGames).toEqual({ o_comp: 2 });

    // 1 局でしか立たない id は 1 のまま。2 局目を「1 手も指していない局」にすると、
    // 指し手で作られる形・狙い・戦型は立たず、初期配置のままで完成する戦型だけが立つ。
    const onlyFirst = measureRecognition(
      [
        { group: "g", id: "a", moves: MOVES_4 },
        { group: "g", id: "b", moves: [] },
      ],
      options,
    );
    expect(onlyFirst.byGroup["g"]?.games).toBe(2);
    expect(onlyFirst.byGroup["g"]?.shapeOnGames).toEqual({ t_on: 1 });
    expect(onlyFirst.byGroup["g"]?.intentOnGames).toEqual({ t_on_intent: 1 });
    expect(onlyFirst.byGroup["g"]?.openOnGames).toEqual({ o_comp: 2, o_on: 1 });
    expect(onlyFirst.byGroup["g"]?.openCompGames).toEqual({ o_comp: 2 });
  });
});

// ---- (8) 局数の欄どうしの整合(STEP OPEN-2b) ----

describe("(8) gamesCompleted と shapeCompGames は同じ値・局数は分母を超えない", () => {
  it("固定棋譜 4 局 + 本体の形・狙いで、全 id が *CompGames ≤ *OnGames ≤ games を満たす", () => {
    const shapes = loadShapes(join(REPO_ROOT, "data", "shapes"));
    const intents = loadIntents(join(REPO_ROOT, "data", "intents"));
    // 戦型は作り物(将棋知識ではない)。completed になるもの・forming どまりのものを 1 件ずつ。
    const openings = [
      makeOpening("o_check_comp", "self", [{ piece: "金", to: "4i" }]),
      makeOpening("o_check_forming", "self", [
        { piece: "歩", to: "7f" },
        { piece: "銀", to: "3h" },
        { piece: "金", to: "5h" },
      ]),
    ];
    const { byGroup } = measureRecognition(readFixed4(), { shapes, intents, openings, maxPly: 0 });
    const totals = byGroup["fixed4"]!;
    expect(totals.games).toBe(4);

    // 既存の欄(形の完成した局数)と、新しい欄が同じ値になる。
    expect(totals.shapeCompGames).toEqual(totals.gamesCompleted);

    const pairs: Array<[string, Record<string, number>, Record<string, number>]> = [
      ["形", totals.shapeOnGames, totals.shapeCompGames],
      ["狙い", totals.intentOnGames, totals.intentCompGames],
      ["戦型", totals.openOnGames, totals.openCompGames],
    ];
    for (const [what, onGames, compGames] of pairs) {
      for (const [id, count] of Object.entries(onGames)) {
        expect(count, `${what} ${id} の立った局数`).toBeGreaterThan(0);
        expect(count, `${what} ${id} の立った局数`).toBeLessThanOrEqual(totals.games);
      }
      for (const [id, count] of Object.entries(compGames)) {
        expect(count, `${what} ${id} の完成した局数`).toBeGreaterThan(0);
        expect(count, `${what} ${id} の完成した局数`).toBeLessThanOrEqual(onGames[id] ?? 0);
      }
    }

    // 空でないことを確かめる(全部 0 件でも上のループは通ってしまうため)。
    expect(Object.keys(totals.shapeOnGames).length).toBeGreaterThan(0);
    expect(Object.keys(totals.intentOnGames).length).toBeGreaterThan(0);
    expect(totals.openCompGames["o_check_comp"]).toBeGreaterThan(0);
    expect(Object.keys(totals.openOnGames)).toContain("o_check_forming");

    // 局ごとの集合と、組の局数が食い違わない(rows から数え直しても同じになる)。
    const recounted: Record<string, number> = {};
    for (const row of measureRecognition(readFixed4(), { shapes, intents, openings, maxPly: 0 }).rows) {
      for (const id of row.shapeOnIds) recounted[id] = (recounted[id] ?? 0) + 1;
    }
    expect(recounted).toEqual(totals.shapeOnGames);
  });
});

// ---- (9)〜(11) 露出の欄(STEP EXPO-1、docs/LANE_DIAG_LOG_2026-09.md §12.9) ----
// 判定は apps/server の decideNameExposure が行う。ここで見るのは「どの行に当てたか」と
// 「何を数えたか」だけ。**本体の見え方は変わらない**(この関数はまだ画面から呼ばれていない)。

/** 露出の 3 組 × 形・狙い・戦型 × 自分側・相手側の、named / hedged / hidden を足した数。 */
function levelSumOf(counts: { named: number; hedged: number; hidden: number }): number {
  return counts.named + counts.hedged + counts.hidden;
}

describe("(9) A(今日の規則)の値の組では forming の行が 1 つも見えない", () => {
  it("forming だけを作った形・狙い・戦型で、A は全部 hidden(B は hedged になる)", () => {
    // どれも「完成しない」ように作る(3 件のうち 1 件が最後まで欠ける)。
    const selfShape = makeShape("t_forming_self", "self", [
      { piece: "歩", square: "7f" },
      { piece: "銀", square: "3h" },
      { piece: "金", square: "5h" },
    ]);
    const oppShape = makeShape("t_forming_opp", "opponent", [
      { piece: "歩", square: "3d" },
      { piece: "歩", square: "8d" },
      { piece: "金", square: "5b" },
    ]);
    const intent = makeIntent("t_forming_intent", [
      { piece: "歩", to: "3d" },
      { piece: "銀", to: "6b" },
    ]);
    const opening = makeOpening("o_forming", "self", [
      { piece: "歩", to: "7f" },
      { piece: "銀", to: "3h" },
      { piece: "金", to: "5h" },
    ]);
    const row = measureOne(MOVES_4, {
      maxPly: 0,
      shapes: [selfShape, oppShape],
      intents: [intent],
      openings: [opening],
    });

    // ply 2・4 の 2 局面ずつ立つ(ply 0 はどれも none なので数えない)。
    const a = row.exposure.A;
    for (const [what, counts] of [
      ["形(自分側)", a.shape.self],
      ["形(相手側)", a.shape.opponent],
      ["狙い(相手側)", a.intent.opponent],
      ["戦型(自分側)", a.opening.self],
    ] as const) {
      expect(levelSumOf(counts), `${what} の行数`).toBe(2);
      expect(counts.hidden, `${what} の hidden`).toBe(2);
      expect(counts.hedged, `${what} の hedged`).toBe(0);
      expect(counts.named, `${what} の named`).toBe(0);
    }
    // 当てていない側は 0 のまま(狙いは常に相手側に数える)。
    expect(levelSumOf(a.intent.self)).toBe(0);
    expect(levelSumOf(a.opening.opponent)).toBe(0);

    // 行が無いから 0 になったのではないことを示す(同じ行が B では hedged になる)。
    const b = row.exposure.B;
    expect(b.shape.self.hedged).toBe(2);
    expect(b.intent.opponent.hedged).toBe(2);
    expect(b.opening.self.hedged).toBe(2);
    expect(b.shape.self.hidden).toBe(0);
  });
});

describe("(10) B の hidden に入る「必要な数が 1 の completed」と、証拠 0 件の内訳", () => {
  it("hiddenCompletedNoEvidence は証拠 0 件のときだけ増える(必要な数 1 で落ちた行は入らない)", () => {
    const row = measureOne(MOVES_4, {
      maxPly: 0,
      openings: [
        // 4i の金は初期配置のまま = ply 0・2・4 の 3 局面とも「証拠 0 件の completed」。
        makeOpening("o_no_evid", "self", [{ piece: "金", to: "4i" }]),
        // 7f の歩は指し手で作られた = ply 2・4 の 2 局面が「証拠 1 件の completed」(必要な数は 1)。
        makeOpening("o_with_evid", "self", [{ piece: "歩", to: "7f" }]),
        // 必要な数 2 でレビュー済み。ply 2 は forming(証拠 1)、ply 4 は completed(証拠 2)。
        {
          ...makeOpening("o_two_reviewed", "self", [
            { piece: "歩", to: "7f" },
            { piece: "銀", to: "3h" },
          ]),
          review_status: "human_reviewed",
        },
      ],
    });

    const b = row.exposure.B.opening.self;
    expect(levelSumOf(b)).toBe(7); // 3 + 2 + 2
    expect(b.hidden).toBe(5); // 証拠 0 の completed 3 件(R2)+ 必要な数 1 の completed 2 件(R3)
    expect(b.hiddenCompletedNoEvidence).toBe(3); // 増えるのは R2 で落ちた 3 件だけ
    expect(b.hedged).toBe(1); // 必要な数 2 の forming(証拠 1)
    expect(b.named).toBe(1); // 必要な数 2 の completed(証拠 2、レビュー済み)

    // A(今日の規則)では R2・R3 が当たらないので、同じ行が hidden に落ちない。
    const a = row.exposure.A.opening.self;
    expect(a.hiddenCompletedNoEvidence).toBe(0);
    expect(a.hedged).toBe(5); // 下書きの completed 5 件(証拠の有無を問わない)
    expect(a.named).toBe(1); // レビュー済みの completed
    expect(a.hidden).toBe(1); // forming の 1 件だけ

    // C は B の minEvidenceForHedged だけが違う(証拠 1 の forming が hedged から hidden へ)。
    const c = row.exposure.C.opening.self;
    expect(c.hedged).toBe(0);
    expect(c.hidden).toBe(6);
    expect(c.hiddenCompletedNoEvidence).toBe(3);
  });
});

describe("(11) 露出の合計と「証拠の少ない主張」の分母・分子", () => {
  it("named + hedged + hidden は行数と一致し、weakClaims は値の組によらない(weakClaimsShown はその一部)", () => {
    // 手で数えられる作り物: 形 2 件で 5 行(forming 2 + 証拠 0 の completed 3)。
    const row = measureOne(MOVES_4, {
      maxPly: 0,
      shapes: [
        makeShape("s_evid", "self", [
          { piece: "歩", square: "7f" },
          { piece: "銀", square: "3h" },
          { piece: "金", square: "5h" },
        ]),
        makeShape("s_comp", "self", [{ piece: "金", square: "4i" }]),
      ],
    });

    // 行数 5 = ply 2(証拠 1 の forming)・ply 4(証拠 2 の forming)+ ply 0/2/4(証拠 0 の completed)。
    for (const set of ["A", "B", "C"] as const) {
      expect(levelSumOf(row.exposure[set].shape.self), `${set} の行数`).toBe(5);
      // 証拠 ≤ 1 の行は 4 件(forming の ply 2 と、completed 3 件)。値の組によらない。
      expect(row.exposure[set].shape.self.weakClaims, `${set} の weakClaims`).toBe(4);
      expect(
        row.exposure[set].shape.self.weakClaimsShown,
        `${set} の weakClaimsShown`,
      ).toBeLessThanOrEqual(row.exposure[set].shape.self.weakClaims);
    }
    // A は completed 3 件を hedged で見せる(証拠 0 でも)。B は forming の 1 件だけ。C は 0 件。
    expect(row.exposure.A.shape.self.weakClaimsShown).toBe(3);
    expect(row.exposure.B.shape.self.weakClaimsShown).toBe(1);
    expect(row.exposure.C.shape.self.weakClaimsShown).toBe(0);

    // 固定棋譜 4 局 + 本体の形・狙い + 作り物の戦型でも、合計は「延べの行数」と一致する。
    const shapes = loadShapes(join(REPO_ROOT, "data", "shapes"));
    const intents = loadIntents(join(REPO_ROOT, "data", "intents"));
    const openings = [
      makeOpening("o_sum_comp", "self", [{ piece: "金", to: "4i" }]),
      makeOpening("o_sum_forming", "self", [
        { piece: "歩", to: "7f" },
        { piece: "銀", to: "3h" },
        { piece: "金", to: "5h" },
      ]),
    ];
    const { byGroup } = measureRecognition(readFixed4(), { shapes, intents, openings, maxPly: 0 });
    const totals = byGroup["fixed4"]!;
    const sumOf = (counter: Record<string, number>): number =>
      Object.values(counter).reduce((acc, n) => acc + n, 0);
    const shapeRows = sumOf(totals.shapeHits);
    const intentRows = sumOf(totals.intentHits);
    const openingRows = totals.openCompleted + totals.openForming;
    expect(shapeRows).toBeGreaterThan(0);
    expect(intentRows).toBeGreaterThan(0);
    expect(openingRows).toBeGreaterThan(0);

    for (const set of ["A", "B", "C"] as const) {
      const e = totals.exposure[set];
      expect(levelSumOf(e.shape.self) + levelSumOf(e.shape.opponent), `${set} の形の行数`).toBe(shapeRows);
      expect(levelSumOf(e.intent.self) + levelSumOf(e.intent.opponent), `${set} の狙いの行数`).toBe(intentRows);
      expect(levelSumOf(e.opening.self) + levelSumOf(e.opening.opponent), `${set} の戦型の行数`).toBe(openingRows);
      // weakClaims は値の組によらない(A と同じ数になる)。
      expect(e.shape.self.weakClaims).toBe(totals.exposure.A.shape.self.weakClaims);
      expect(e.opening.self.weakClaims).toBe(totals.exposure.A.opening.self.weakClaims);
    }
  });
});
