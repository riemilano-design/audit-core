// STEP OPEN-2(docs/LANE_DIAG_LOG_2026-09.md §12.8)。lib/recognitionMeasure.ts の試験。
//
// (1)〜(5) は数え方そのもの(小さな作り物の形・狙い・戦型で、1 局面ずつ数を突き合わせる)。
// (6) は CLI(scripts/playtest/recognitionMeasure.ts)を実際に spawn する。
// (7)(8) は局数の欄(STEP OPEN-2b)。(9)〜(11) は露出の欄(STEP EXPO-1、§12.9)。
// (12)(13) は中間案の値の組 D・D'・D''(STEP EXPO-1b。R5' と R6 の内訳の欄)。
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
import { replayMoveHistory } from "../../../apps/server/src/analysis/moveHistory.js";
import type { OpeningDefinition } from "../../../apps/server/src/analysis/openingDetector.js";
import { analyzeShapeFormationFromEvents } from "../../../apps/server/src/analysis/shapeFormationAnalyzer.js";
import type { ShapeDefinition } from "../../../apps/server/src/analysis/shapeRepository.js";
import { loadShapes } from "../../../apps/server/src/analysis/shapeRepository.js";
import {
  measureRecognition,
  movedRequiredPiecesOf,
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
      movedRequiredZeroShapeIds: { self: string[]; opponent: string[] };
      movedRequiredZeroShapeCounts: { self: number; opponent: number };
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
    // STEP OBS-5e。id の一覧と、件数だけの版が両方 CLI の出力に乗る。
    expect(written.movedRequiredZeroShapeIds.self.length).toBe(written.movedRequiredZeroShapeCounts.self);
    expect(written.movedRequiredZeroShapeIds.opponent.length).toBe(written.movedRequiredZeroShapeCounts.opponent);

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

// ---- (12)(13) 中間案の値の組 D・D'・D''(STEP EXPO-1b、§12.9 の追記) ----
// ここでも判定は apps/server の decideNameExposure が行う。見るのは「新しい内訳の欄が
// 数えられること」と「行数は値の組によらないこと」だけ。

/** 作り物の形 4 件(将棋知識ではない)。R5' と R6 の当たり方を 1 局の中に作り分けるためのもの。 */
function makeR5pR6Shapes(): ShapeDefinition[] {
  return [
    // ply 2 = forming(証拠 1・欠け 1 → R5' が拾う)、ply 4 = completed(証拠 2・必要 2)。
    makeShape("s_r5p", "self", [
      { piece: "歩", square: "7f" },
      { piece: "銀", square: "3h" },
    ]),
    // 4i の金は初期配置のまま = ply 2・4 は completed だが証拠は 1 件(7f の歩)だけ。
    makeShape("s_r6", "self", [
      { piece: "金", square: "4i" },
      { piece: "歩", square: "7f" },
    ]),
    // 必要 3(うち 1 つは初期配置の 4i)。ply 4 は completed・証拠 2。
    makeShape("s_three", "self", [
      { piece: "歩", square: "7f" },
      { piece: "銀", square: "3h" },
      { piece: "金", square: "4i" },
    ]),
    // ply 2 は forming(証拠 1・欠け 2 → R5' は拾わない)、ply 4 は forming(証拠 2)。
    makeShape("s_miss2", "self", [
      { piece: "歩", square: "7f" },
      { piece: "銀", square: "3h" },
      { piece: "金", square: "5h" },
    ]),
  ];
}

describe("(12) D の pickedByR5p・droppedByR6・droppedByR6ById", () => {
  it("R5' と R6 の行が数えられ、named + hedged + hidden は A/B/C/D/D'/D'' で同じ", () => {
    const row = measureOne(MOVES_4, { maxPly: 0, shapes: makeR5pR6Shapes() });

    // 立った行は 8(4 件 × ply 2・4。ply 0 はどれも none)。値の組によらず同じ行を数える。
    for (const set of ["A", "B", "C", "D", "D'", "D''"] as const) {
      expect(levelSumOf(row.exposure[set].shape.self), `${set} の行数`).toBe(8);
    }

    // A・B・C は EXPO-1 の決定のまま(新しい 2 つの規則は当たらない)。
    for (const set of ["A", "B", "C"] as const) {
      expect(row.exposure[set].shape.self.pickedByR5p, `${set} の pickedByR5p`).toBe(0);
      expect(row.exposure[set].shape.self.droppedByR6, `${set} の droppedByR6`).toBe(0);
      expect(row.exposure[set].shape.self.droppedByR6ById, `${set} の droppedByR6ById`).toEqual({});
    }

    // D: R5' が 2 行(s_r5p・s_three の ply 2)、R6 が 3 行(s_r6 の 2 行 + s_three の ply 4)。
    const d = row.exposure.D.shape.self;
    expect(d.pickedByR5p).toBe(2);
    expect(d.droppedByR6).toBe(3);
    expect(d.droppedByR6ById).toEqual({ s_r6: 2, s_three: 1 });
    expect(d.named).toBe(0); // 作り物は全部 draft(R1 で hedged 止まり)
    expect(d.hedged).toBe(4);
    expect(d.hidden).toBe(3 + 1); // R6 の 3 行 + 証拠 1・欠け 2 の forming(R5)

    // D'(下限 2): s_three の ply 4(証拠 2)は落ちない。落ちるのは s_r6 の 2 行だけ。
    const dPrime = row.exposure["D'"].shape.self;
    expect(dPrime.pickedByR5p).toBe(2);
    expect(dPrime.droppedByR6).toBe(2);
    expect(dPrime.droppedByR6ById).toEqual({ s_r6: 2 });

    // D''(下限 = 初期位置と違う必要な駒の数): s_r6 は動くべき駒が 1 つ(7f)なので落ちない。
    const dPrime2 = row.exposure["D''"].shape.self;
    expect(dPrime2.pickedByR5p).toBe(2);
    expect(dPrime2.droppedByR6).toBe(0);
    expect(dPrime2.droppedByR6ById).toEqual({});
    expect(dPrime2.hedged).toBe(7);
    expect(dPrime2.hidden).toBe(1);

    // 固定棋譜 4 局 + 本体の形・狙いでも、行数は値の組によらない(延べの行数と一致する)。
    const shapes = loadShapes(join(REPO_ROOT, "data", "shapes"));
    const intents = loadIntents(join(REPO_ROOT, "data", "intents"));
    const { byGroup } = measureRecognition(readFixed4(), { shapes, intents, openings: [], maxPly: 0 });
    const totals = byGroup["fixed4"]!;
    const sumOf = (counter: Record<string, number>): number =>
      Object.values(counter).reduce((acc, n) => acc + n, 0);
    for (const set of ["A", "B", "C", "D", "D'", "D''"] as const) {
      const e = totals.exposure[set];
      expect(levelSumOf(e.shape.self) + levelSumOf(e.shape.opponent), `${set} の形の行数`).toBe(
        sumOf(totals.shapeHits),
      );
      expect(levelSumOf(e.intent.self) + levelSumOf(e.intent.opponent), `${set} の狙いの行数`).toBe(
        sumOf(totals.intentHits),
      );
    }
  });
});

describe("(13) D' の named + hedged は D 以上", () => {
  it("作り物でも固定棋譜 4 局でも、D' が D を下回らない(D の下限は必要な数なので D' 以上)", () => {
    const shownOf = (counts: { named: number; hedged: number }): number => counts.named + counts.hedged;

    const row = measureOne(MOVES_4, { maxPly: 0, shapes: makeR5pR6Shapes() });
    // 作り物では差がつく(s_three の ply 4 は D で落ち、D' では落ちない)。
    expect(shownOf(row.exposure["D'"].shape.self)).toBe(5);
    expect(shownOf(row.exposure.D.shape.self)).toBe(4);
    expect(shownOf(row.exposure["D'"].shape.self)).toBeGreaterThan(shownOf(row.exposure.D.shape.self));

    // 固定棋譜 4 局 + 本体の形・狙い + 作り物の戦型でも、向きは変わらない。
    const shapes = loadShapes(join(REPO_ROOT, "data", "shapes"));
    const intents = loadIntents(join(REPO_ROOT, "data", "intents"));
    const openings = [
      makeOpening("o_d_comp", "self", [
        { piece: "歩", to: "7f" },
        { piece: "銀", to: "3h" },
        { piece: "金", to: "4i" },
      ]),
    ];
    const { byGroup } = measureRecognition(readFixed4(), { shapes, intents, openings, maxPly: 0 });
    const totals = byGroup["fixed4"]!;
    for (const kind of ["shape", "intent", "opening"] as const) {
      for (const side of ["self", "opponent"] as const) {
        expect(
          shownOf(totals.exposure["D'"][kind][side]),
          `${kind} ${side} の D' の named+hedged`,
        ).toBeGreaterThanOrEqual(shownOf(totals.exposure.D[kind][side]));
      }
    }
    // 「どちらも 0 だから等しい」ではないことを示す(見せる行が実在する)。
    expect(shownOf(totals.exposure["D'"].shape.self)).toBeGreaterThan(0);
  });
});

// STEP OBS-5c(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A2)「計画の直し」2026-09-26)。
// `statusCounts` は露出(countExposure)と違い `none` を捨てずに数える。
describe("(14) statusCounts は none を含めて数える(STEP OBS-5c)", () => {
  it("none だけの記録は none だけを数え、他の状態・当てていない側は 0(none が捨てられていないことを示す)", () => {
    // 5e は初期配置でも MOVES_4 の指し手でも駒が来ないマス(作り物、将棋知識ではない)。3 局面とも一致 0 件 = none。
    const row = measureOne(MOVES_4, {
      maxPly: 0,
      shapes: [makeShape("t_never", "self", [{ piece: "香", square: "5e" }])],
    });
    expect(row.statusCounts.shape.self).toEqual({ none: 3, forming: 0, completed: 0, matched: 0 });
    // 側を当てていない相手側・狙い・戦型は 0 のまま。
    expect(row.statusCounts.shape.opponent).toEqual({ none: 0, forming: 0, completed: 0, matched: 0 });
    expect(row.statusCounts.intent.self).toEqual({ none: 0, forming: 0, completed: 0, matched: 0 });
    expect(row.statusCounts.intent.opponent).toEqual({ none: 0, forming: 0, completed: 0, matched: 0 });
    expect(row.statusCounts.opening.self).toEqual({ none: 0, forming: 0, completed: 0, matched: 0 });
    expect(row.statusCounts.opening.opponent).toEqual({ none: 0, forming: 0, completed: 0, matched: 0 });
  });

  it("forming・completed・matched が混ざる形・狙い・戦型で、4 状態の合計が「局面数 × 記録数」(行数)と一致する(不変条件)", () => {
    // t_forming_self・o_forming は (9) と同じ作り物(ply 0 は none、ply 2・4 は forming のまま完成しない)。
    const selfForming = makeShape("t_forming_self", "self", [
      { piece: "歩", square: "7f" },
      { piece: "銀", square: "3h" },
      { piece: "金", square: "5h" },
    ]);
    // 1a の香は後手の初期配置のまま(指し手で動かない)= 3 局面とも matchedSquares>0・missing 0 の completed。
    const oppCompleted = makeShape("t_completed_opp", "opponent", [{ piece: "香", square: "1a" }]);
    const intentForming = makeIntent("t_forming_intent", [
      { piece: "歩", to: "3d" },
      { piece: "銀", to: "6b" },
    ]);
    // (2) の matchedIntent と同じ作り物(ply 0 は none、ply 2・4 は matched)。
    const intentMatched = makeIntent("t_matched_intent", [{ piece: "歩", to: "3d" }]);
    const openingForming = makeOpening("o_forming", "self", [
      { piece: "歩", to: "7f" },
      { piece: "銀", to: "3h" },
      { piece: "金", to: "5h" },
    ]);
    // (10) の o_no_evid と同じ作り物(4i の金は先手の初期配置のまま = 3 局面とも completed)。
    const openingCompleted = makeOpening("o_completed", "self", [{ piece: "金", to: "4i" }]);

    const row = measureOne(MOVES_4, {
      maxPly: 0,
      shapes: [selfForming, oppCompleted],
      intents: [intentForming, intentMatched],
      openings: [openingForming, openingCompleted],
    });

    expect(row.positions).toBe(3);
    expect(row.statusCounts.shape.self).toEqual({ none: 1, forming: 2, completed: 0, matched: 0 });
    expect(row.statusCounts.shape.opponent).toEqual({ none: 0, forming: 0, completed: 3, matched: 0 });
    expect(row.statusCounts.intent.self).toEqual({ none: 0, forming: 0, completed: 0, matched: 0 });
    expect(row.statusCounts.intent.opponent).toEqual({ none: 2, forming: 2, completed: 0, matched: 2 });
    expect(row.statusCounts.opening.self).toEqual({ none: 1, forming: 2, completed: 3, matched: 0 });
    expect(row.statusCounts.opening.opponent).toEqual({ none: 0, forming: 0, completed: 0, matched: 0 });

    // 不変条件(機械で照合できる): 4 状態の合計 = 局面数(row.positions)× その側に渡した記録の数。
    // countExposure と違い none を捨てていないので、この和は必ず一致する(取りこぼしがあれば崩れる)。
    const sumOf = (c: { none: number; forming: number; completed: number; matched: number }): number =>
      c.none + c.forming + c.completed + c.matched;
    expect(sumOf(row.statusCounts.shape.self)).toBe(row.positions * 1);
    expect(sumOf(row.statusCounts.shape.opponent)).toBe(row.positions * 1);
    expect(sumOf(row.statusCounts.intent.opponent)).toBe(row.positions * 2);
    expect(sumOf(row.statusCounts.opening.self)).toBe(row.positions * 2);

    // byGroup の合計は rows をそのまま足し上げたもの(1 局だけなので row と同じ値になる)。
    const { byGroup } = measureRecognition(
      [{ group: "g", id: "test-01", moves: MOVES_4 }],
      { shapes: [selfForming, oppCompleted], intents: [intentForming, intentMatched], openings: [openingForming, openingCompleted], maxPly: 0 },
    );
    expect(byGroup["g"]!.statusCounts.shape.self).toEqual(row.statusCounts.shape.self);
    expect(byGroup["g"]!.statusCounts.opening.self).toEqual(row.statusCounts.opening.self);
  });
});

// STEP OBS-5e(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A4))。「あと 1 枚」の中身。
// 作り物の駒・マスは (12)(13) と同じ流儀(将棋知識ではない)。
//
// t_three: 歩7f(移動で一致)・銀3h(移動で一致)・金4i(先手の初期配置のまま一致)。
//   ply0 = none(0/3)、ply2 = forming(2/3, 欠け 3h)、ply4 = completed(3/3, 欠け 0)。
// t_one_away: 歩7f・銀3h(どちらも移動で一致しうる)・銀4h(この棋譜のどの手でも一致しない = 永久に欠け)。
//   ply0 = none、ply2 = forming(欠け 3h・4h)、ply4 = forming(欠け 4h だけ。matchScore 最大はここ)。
// t_zero: 金4i だけ(先手の初期配置のまま)。「初期位置でない必要駒」が 0 の形。
describe("(15) 欠けたマスと駒の内訳(STEP OBS-5e)", () => {
  const t_three = makeShape("t_three", "self", [
    { piece: "歩", square: "7f" },
    { piece: "銀", square: "3h" },
    { piece: "金", square: "4i" },
  ]);
  const t_one_away = makeShape("t_one_away", "self", [
    { piece: "歩", square: "7f" },
    { piece: "銀", square: "3h" },
    { piece: "銀", square: "4h" },
  ]);

  it("欠けたマスの件数の合計は forming の行の欠けの総数と一致する(不変条件。analyzeShapeFormationFromEvents を直接呼んで数え直す)", () => {
    const shapes = [t_three, t_one_away];
    const row = measureOne(MOVES_4, { maxPly: 0, shapes });

    const total = Object.values(row.shapeMissingCounts).reduce((acc, n) => acc + n, 0);
    expect(total).toBe(row.shapeMissingTotal);

    const { events, sfens } = replayMoveHistory(MOVES_4);
    let expectedTotal = 0;
    for (const ply of plyStepsOf(MOVES_4.length, 0)) {
      const results = analyzeShapeFormationFromEvents(sfens[ply]!, events.slice(0, ply), { shapes });
      for (const r of results) {
        if (r.status === "forming") expectedTotal += r.missingSquares.length;
      }
    }
    expect(row.shapeMissingTotal).toBe(expectedTotal);
    // t_three は ply2 だけ forming・欠け 1(3h)。t_one_away は ply2(欠け 2: 3h・4h)+ ply4(欠け 1: 4h)。
    expect(row.shapeMissingCounts).toEqual({
      "t_three:3h:銀": 1,
      "t_one_away:3h:銀": 1,
      "t_one_away:4h:銀": 2,
    });
    expect(expectedTotal).toBe(1 + 1 + 2);
  });

  it("局ごとに最も近づいた自分側の形(matchScore 最大)と、そのとき欠けていた駒を持つ", () => {
    const row = measureOne(MOVES_4, { maxPly: 0, shapes: [t_three, t_one_away] });
    // t_three は ply4 で matchScore 1(completed・欠け 0)、t_one_away は ply4 で matchScore 2/3(欠け 1)。
    // 最も近づいた = matchScore が高いほう(t_three の 1 のほう)。
    // STEP OBS-5g: 金 4i は平手の初期配置にあるので「動かして持って来る必要がある駒」に入らない。
    // 残る 2 枚(歩 7f・銀 3h)は matchScore 1 の局面なので両方とも来ている。
    expect(row.closestSelfShape).toEqual({
      shapeId: "t_three",
      matchScore: 1,
      missing: [],
      movedRequired: [
        { square: "7f", piece: "歩", arrived: true },
        { square: "3h", piece: "銀", arrived: true },
      ],
    });
  });

  it("「あと 1 枚」だけの形しか無ければ、closestSelfShape の欠けは 1 枚になる", () => {
    const row = measureOne(MOVES_4, { maxPly: 0, shapes: [t_one_away] });
    expect(row.closestSelfShape).toEqual({
      shapeId: "t_one_away",
      matchScore: 2 / 3,
      missing: [{ square: "4h", piece: "銀" }],
      // STEP OBS-5g: 3 枚とも初期配置に無いので全部が「動かして持って来る必要がある駒」。
      // 欠けている 4h の銀だけが arrived: false。
      movedRequired: [
        { square: "7f", piece: "歩", arrived: true },
        { square: "3h", piece: "銀", arrived: true },
        { square: "4h", piece: "銀", arrived: false },
      ],
    });

    // byGroup の selfClosestOneAwayGames(局ごとの「欠け 1 枚」の局数)にも 1 局として数えられる。
    const { byGroup } = measureRecognition([{ group: "g", id: "test-01", moves: MOVES_4 }], {
      ...NO_KNOWLEDGE,
      shapes: [t_one_away],
      maxPly: 0,
    });
    expect(byGroup["g"]!.selfClosestOneAwayGames).toBe(1);
  });

  it("形が無ければ closestSelfShape は null のまま", () => {
    const row = measureOne(MOVES_4, { maxPly: 0 });
    expect(row.closestSelfShape).toBeNull();
  });
});

describe("(16) 到達率を「初期位置でない必要駒」だけで数え直す(STEP OBS-5e)", () => {
  // t_one_away: 3 つとも初期位置とは一致しない(動くべき駒 3)が、4h はこの棋譜のどの手でも
  // 一致しない(永久に欠け)ので、数え直した到達率は 2/3 止まりで 1.0 に達しない。
  const t_one_away = makeShape("t_one_away", "self", [
    { piece: "歩", square: "7f" },
    { piece: "銀", square: "3h" },
    { piece: "銀", square: "4h" },
  ]);
  // t_recount_complete: 動くべき駒 2(7f・3h)がどちらも ply4 までに一致する = 数え直した到達率 1.0。
  const t_recount_complete = makeShape("t_recount_complete", "self", [
    { piece: "歩", square: "7f" },
    { piece: "銀", square: "3h" },
  ]);
  const t_zero = makeShape("t_zero", "self", [{ piece: "金", square: "4i" }]);

  it("movedRequiredPiecesOf は初期位置と一致する駒を除いた一覧を返す(movedRequiredCountOf はその件数)", () => {
    const pieces = [
      { piece: "金", square: "4i" }, // 先手の初期配置のまま
      { piece: "歩", square: "7f" }, // 初期配置には無い(歩は 7g)
    ];
    expect(movedRequiredPiecesOf(pieces, "sente")).toEqual([{ piece: "歩", square: "7f" }]);
  });

  it("数え直した到達率は 0〜1 に入り、初期位置でない必要駒が 0 の形には持たない", () => {
    const { byGroup, rows, movedRequiredZeroShapeIds, movedRequiredZeroShapeCounts } = measureRecognition(
      [{ group: "g", id: "test-01", moves: MOVES_4 }],
      { ...NO_KNOWLEDGE, shapes: [t_one_away, t_recount_complete, t_zero], maxPly: 0 },
    );
    const row = rows[0]!;

    // t_one_away: 動くべき駒 3(7f・3h・4h。4h は一致した局面が無いので分子に入らない)。
    // ply4 で 3 件中 2 件一致 = 2/3(1.0 には届かない ― 居玉と同じ理屈で「あと 1 枚」)。
    expect(row.shapeMovedRequiredBest["t_one_away"]).toBeCloseTo(2 / 3);
    // t_recount_complete: 動くべき駒 2(7f・3h)がどちらも ply4 で一致 = 1.0。
    expect(row.shapeMovedRequiredBest["t_recount_complete"]).toBe(1);
    // t_zero: 必要な駒(金4i)が先手の初期配置そのもの → 動くべき駒が 0 → 到達率を持たない。
    expect(row.shapeMovedRequiredBest["t_zero"]).toBeUndefined();

    for (const value of Object.values(row.shapeMovedRequiredBest)) {
      expect(value).toBeGreaterThanOrEqual(0);
      expect(value).toBeLessThanOrEqual(1);
    }

    expect(movedRequiredZeroShapeIds.self).toContain("t_zero");
    expect(movedRequiredZeroShapeIds.self).not.toContain("t_one_away");
    expect(movedRequiredZeroShapeIds.self).not.toContain("t_recount_complete");
    expect(movedRequiredZeroShapeIds.self.length).toBe(movedRequiredZeroShapeCounts.self);

    // 到達率が 1.0 に達した局・形だけが gamesMovedRequiredComplete に 1 として数えられる。
    // t_one_away は 1.0 に届かない(=「あと 1 枚」のまま数え直しても完成しない形の例)。
    expect(byGroup["g"]!.gamesMovedRequiredComplete["t_one_away"]).toBeUndefined();
    expect(byGroup["g"]!.gamesMovedRequiredComplete["t_recount_complete"]).toBe(1);
    expect(byGroup["g"]!.gamesMovedRequiredComplete["t_zero"]).toBeUndefined();
    expect(byGroup["g"]!.shapeMovedRequiredCompleteTotal).toBe(1);
  });

  it("数え直すと、初期配置と偶然一致する駒を含む生の matchScore とは違う値になりうる(t_three の ply2)", () => {
    const t_three = makeShape("t_three", "self", [
      { piece: "歩", square: "7f" },
      { piece: "銀", square: "3h" },
      { piece: "金", square: "4i" }, // 先手の初期配置のまま(動くべき駒から除かれる)
    ]);
    const { events, sfens } = replayMoveHistory(MOVES_4);
    const ply2Results = analyzeShapeFormationFromEvents(sfens[2]!, events.slice(0, 2), { shapes: [t_three] });
    const r = ply2Results.find((x) => x.shapeId === "t_three")!;
    expect(r.matchScore).toBeCloseTo(2 / 3); // 7f・4i が一致(4i は偶然)、3h が欠け
    const moved = movedRequiredPiecesOf(
      [
        { piece: "歩", square: "7f" },
        { piece: "銀", square: "3h" },
        { piece: "金", square: "4i" },
      ],
      "sente",
    );
    const movedMatched = moved.filter((p) => r.matchedSquares.includes(p.square)).length;
    const recounted = movedMatched / moved.length;
    expect(recounted).toBeCloseTo(0.5); // 動くべき駒は 7f・3h の 2 つ、一致は 7f だけ
    expect(recounted).not.toBeCloseTo(r.matchScore);
  });
});
