// STEP OPEN-2(docs/LANE_DIAG_LOG_2026-09.md §12.8)。lib/recognitionMeasure.ts の試験(6 本)。
//
// (1)〜(5) は数え方そのもの(小さな作り物の形・狙い・戦型で、1 局面ずつ数を突き合わせる)。
// (6) は CLI(scripts/playtest/recognitionMeasure.ts)を実際に spawn する。
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
