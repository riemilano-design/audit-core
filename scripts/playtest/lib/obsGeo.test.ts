// STEP OBS-5(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A))。lib/obsGeo.ts の試験。
// 作りは STEP OBS-5'(§12.6、lib/obsExtra.test.ts)に揃える。小さな作り物(GAME01_MOVES。既存の
// lib/obsExtra.test.ts と同じ流儀)で、既存の道具の値の組み合わせであることを確かめる。
// (a)〜(f) は組み立て(buildObsGeo)そのもの、(g) は CLI(scripts/playtest/obsGeo.ts)を実際に spawn する。
//
// 【統括経由の追加指示(2026-09-25)】`decisionContext` は 10 秒以上(旧 longThink)だけでなく 5〜9 秒の帯も
// 対象にする(spentBucket が "≤9" または ">9")。(c)(d) はこの形で書いた。

import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, describe, expect, it } from "vitest";

import type { MetaLine, RecordLine } from "../invariants/types.js";
import { GAME01_MOVES, plantedRecords } from "./failureEventFixtures.js";
import { buildObsGeo, GEO_VOCABULARY_WORDS, replyToCheckOf, type ObsGeoMoveFacts } from "./obsGeo.js";
import type { GameSource } from "./reportData.js";
import type { MoveFeatureWhatifPosition } from "./timeFeatures.js";

const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const OBS_GEO_TS = fileURLToPath(new URL("../obsGeo.ts", import.meta.url));

/** キーは KIF の手数(1 始まり。overrides 以外は null)。lib/obsExtra.test.ts の同名のローカル関数と同じ形。 */
function timeArrayWith(overrides: Record<number, { spentSec: number; totalSec: number }>): Array<{ spentSec: number; totalSec: number } | null> {
  return GAME01_MOVES.map((_, i) => overrides[i + 1] ?? null);
}

// ---- 共通の 1 局(先手・GAME01_MOVES。plantedRecords は meta.mirrored を持たないので本人 = 先手) ----

const records: RecordLine[] = plantedRecords(GAME01_MOVES, {});
const meta = { kind: "meta", kifuId: "obsg-01", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine;
// kifPly 1(15 秒、>9)・29(7 秒、≤9)だけ対象の帯。3(3 秒、≤4)・55(1 秒、≤1)は境の外(対象外のまま残ることを試験 (d) で確かめる)。
// 他の本人の手は moveSeconds が無い(null)ので、buildGameMoveFeatureRows の own 手の集合にすら入らない
// (timeCause.ts の ownMoveTimesOf が秒の無い手を落とす。既存の動き)。
const moveSeconds = timeArrayWith({
  1: { spentSec: 15, totalSec: 15 },
  3: { spentSec: 3, totalSec: 3 },
  29: { spentSec: 7, totalSec: 7 },
  55: { spentSec: 1, totalSec: 1 },
});
const source: GameSource = { kifuId: "obsg-01", meta, records, fixed: { id: "obsg-01", ending: { kind: "mate", ply: 56 }, moves: GAME01_MOVES, moveSeconds } };

// (a) 本人の手の数
describe("buildObsGeo: moves(本人の手の数)", () => {
  it("28 手(56 手中、先手の奇数 kifPly)で、kifPly は 1,3,…,55", () => {
    const geo = buildObsGeo([source], null, null, null);
    expect(geo.moves).toHaveLength(28);
    expect(geo.moves.map((m) => m.kifPly)).toEqual(Array.from({ length: 28 }, (_, i) => i * 2 + 1));
    expect(geo.moves.every((m) => m.gameNo === 1)).toBe(true);
  });
});

// (b) 初手の reply
describe("buildObsGeo: moves(初手の reply)", () => {
  it("kifPly=1(相手の直前の手が無い)は replyToCapture『相手は取っていない』・replyToCheck『王手ではない』", () => {
    const geo = buildObsGeo([source], null, null, null);
    const first = geo.moves.find((m) => m.kifPly === 1)!;
    expect(first.replyToCapture).toBe("相手は取っていない");
    expect(first.replyToCheck).toBe("王手ではない");
  });
});

// (b2) 王手への応じ方の当てる順(独立監査の REVISE 2026-09-25。変異 2〈「玉を動かす」と「取る」の順の
// 入れ替え〉がどの試験にも当たらなかったため足した。基準の入力 18 局に、玉で王手駒を取る手が 10 件実在する)
describe("replyToCheckOf: 当てる順(玉を動かす → 取る)", () => {
  const facts = (over: Partial<ObsGeoMoveFacts>): ObsGeoMoveFacts => ({ capture: false, drop: false, givesCheck: false, kingMove: false, ...over });

  it("玉で王手駒を取る手(kingMove かつ capture)は『取る』ではなく『玉を動かす』", () => {
    expect(replyToCheckOf(facts({ kingMove: true, capture: true }), true)).toBe("玉を動かす");
  });

  it("玉を動かさずに取る手は『取る』、どちらでもない手は『それ以外』、王手を受けていなければ『王手ではない』", () => {
    expect(replyToCheckOf(facts({ capture: true }), true)).toBe("取る");
    expect(replyToCheckOf(facts({}), true)).toBe("それ以外");
    expect(replyToCheckOf(facts({ kingMove: true, capture: true }), false)).toBe("王手ではない");
  });
});

// (c) decisionContext の行数(統括経由の追加指示: 5〜9 秒・10 秒以上の 2 帯)
describe("buildObsGeo: decisionContext(5〜9 秒・10 秒以上の帯)", () => {
  it("15 秒(kifPly1・>9)と 7 秒(kifPly29・≤9)の 2 行だけが残る", () => {
    const geo = buildObsGeo([source], null, null, null);
    expect(geo.decisionContext).toHaveLength(2);
    expect(geo.decisionContext.map((r) => r.kifPly).sort((a, b) => a - b)).toEqual([1, 29]);
    const byPly = new Map(geo.decisionContext.map((r) => [r.kifPly, r]));
    expect(byPly.get(1)!.spentBucket).toBe(">9");
    expect(byPly.get(29)!.spentBucket).toBe("≤9");
    expect(byPly.get(1)!.gameNo).toBe(1);
  });
});

// (d) spentBucket が「≤4」以下の行は入らない(統括の指示どおり試験を 1 本足した)
describe("buildObsGeo: decisionContext(境の外の帯は入らない)", () => {
  it("3 秒(kifPly3・≤4)・1 秒(kifPly55・≤1)の手は decisionContext に無い", () => {
    const geo = buildObsGeo([source], null, null, null);
    expect(geo.decisionContext.some((r) => r.kifPly === 3)).toBe(false);
    expect(geo.decisionContext.some((r) => r.kifPly === 55)).toBe(false);
    for (const row of geo.decisionContext) expect(["≤9", ">9"]).toContain(row.spentBucket);
  });
});

// (e) --whatif-v2-dir 無しで fork が null
describe("buildObsGeo: decisionContext(--whatif-v2-dir 無し)", () => {
  it("fork はすべて null(行は落とさない)", () => {
    const geo = buildObsGeo([source], null, null, null);
    expect(geo.decisionContext.length).toBeGreaterThan(0);
    expect(geo.decisionContext.every((r) => r.fork === null)).toBe(true);
  });
});

// (h) sideCrossTable(STEP OBS-5d、§12.10 (A3))。側の一致の交差表。
function whatifPosition(overrides: Partial<MoveFeatureWhatifPosition>): MoveFeatureWhatifPosition {
  return {
    ply: 1,
    sfen: "startpos",
    fork: false,
    top1Side: "none",
    actualSide: "none",
    top1Move: "7g7f",
    actualMove: "7g7f",
    actualRank: 1,
    lossCpValue: null,
    lossIsLowerBound: false,
    ...overrides,
  };
}

// 2 局ぶんの作り物: fork===true が 5 行(attack-attack 1・attack-defense 1・both-attack 1・defense-both 1・
// none-none 1)、fork===false が 1 行(数えない)。
const CROSS_TABLE_POSITIONS = new Map<string, MoveFeatureWhatifPosition[]>([
  [
    "g1",
    [
      whatifPosition({ fork: true, top1Side: "attack", actualSide: "attack" }),
      whatifPosition({ fork: true, top1Side: "attack", actualSide: "defense" }),
      whatifPosition({ fork: false, top1Side: "attack", actualSide: "attack" }), // fork でないので数えない
      whatifPosition({ fork: true, top1Side: "both", actualSide: "attack" }),
    ],
  ],
  ["g2", [whatifPosition({ fork: true, top1Side: "defense", actualSide: "both" }), whatifPosition({ fork: true, top1Side: "none", actualSide: "none" })]],
]);

describe("buildObsGeo: sideCrossTable(側の一致の交差表)", () => {
  it("16 マス(4×4)を常に返し、合計は fork===true の行数(5)と一致する", () => {
    const geo = buildObsGeo([source], CROSS_TABLE_POSITIONS, null, null);
    expect(geo.sideCrossTable).toHaveLength(16);
    const total = geo.sideCrossTable.reduce((sum, cell) => sum + cell.count, 0);
    expect(total).toBe(5);
  });

  it("both は「同じ側」の分子に混ざらない(both-attack は attack-attack とは別マスに 1、defense-both は defense-defense に足されない)", () => {
    const geo = buildObsGeo([source], CROSS_TABLE_POSITIONS, null, null);
    const cellOf = (top1Side: string, actualSide: string) => geo.sideCrossTable.find((c) => c.top1Side === top1Side && c.actualSide === actualSide)!.count;
    expect(cellOf("attack", "attack")).toBe(1); // both-attack が足し込まれていない
    expect(cellOf("both", "attack")).toBe(1); // both は別マスとして独立に数えられている
    expect(cellOf("defense", "both")).toBe(1);
    expect(cellOf("defense", "defense")).toBe(0); // both が defense-defense へ紛れ込んでいない
    expect(cellOf("attack", "defense")).toBe(1);
    expect(cellOf("none", "none")).toBe(1);
  });

  it("--whatif-v2-dir 無し(null)なら 16 マスすべて 0(合計 0)", () => {
    const geo = buildObsGeo([source], null, null, null);
    expect(geo.sideCrossTable).toHaveLength(16);
    expect(geo.sideCrossTable.every((cell) => cell.count === 0)).toBe(true);
  });
});

// (i) sideCrossByGame(STEP OBS-5h、§12.14)。sideCrossTable の 16 マスを「何局に散っているか」でも数える。
// 2 局の作り物で「同じマスが両局に 1 件ずつ」と「片方の局に 2 件」が分かれることを見る。
// - (attack, attack): g1 に 1 件・g2 に 1 件 → gamesWithAtLeastOne 2・maxPositionsInOneGame 1(positions 2)
// - (defense, defense): g1 に 2 件・g2 に 0 件 → gamesWithAtLeastOne 1・maxPositionsInOneGame 2(positions 2)
// **独立監査の指摘(2026-09-26。REVISE)**: 「actualSide === "both" の件数を top1Side|attack のセルへ
// 二重に足し込む」変異(統括が 2026-09-26 に禁じた挙動そのもの)を入れても、`both` を含まない fixture では
// 試験が 1 本も落ちなかった(不変条件 2・3 が実質検査していなかった)。**`both-attack`(top1Side が both)・
// `defense-both`(actualSide が both)の行を 1 つずつ足す**(既存の `sideCrossTable` の describe にある
// 「both は『同じ側』の分子に混ざらない」試験と同型を、この fixture にも足すため)。
const BY_GAME_POSITIONS = new Map<string, MoveFeatureWhatifPosition[]>([
  [
    "g1",
    [
      whatifPosition({ fork: true, top1Side: "attack", actualSide: "attack" }),
      whatifPosition({ fork: true, top1Side: "defense", actualSide: "defense" }),
      whatifPosition({ fork: true, top1Side: "defense", actualSide: "defense" }),
      whatifPosition({ fork: false, top1Side: "attack", actualSide: "attack" }), // fork でないので数えない
      whatifPosition({ fork: true, top1Side: "both", actualSide: "attack" }), // top1Side が both
    ],
  ],
  [
    "g2",
    [
      whatifPosition({ fork: true, top1Side: "attack", actualSide: "attack" }),
      whatifPosition({ fork: true, top1Side: "defense", actualSide: "both" }), // actualSide が both
    ],
  ],
]);

describe("buildObsGeo: sideCrossByGame(STEP OBS-5h。何局に散っているか)", () => {
  it("16 マスを常に返し、gamesTotal は Map のキーの数(2)", () => {
    const geo = buildObsGeo([source], BY_GAME_POSITIONS, null, null);
    expect(geo.sideCrossByGame.cells).toHaveLength(16); // 不変条件 1
    expect(geo.sideCrossByGame.gamesTotal).toBe(2); // (a) 相当・§12.14 予測の考え方
  });

  it("同じマスが両局に 1 件ずつ(g1・g2)なら gamesWithAtLeastOne 2・maxPositionsInOneGame 1", () => {
    const geo = buildObsGeo([source], BY_GAME_POSITIONS, null, null);
    const cell = geo.sideCrossByGame.cells.find((c) => c.top1Side === "attack" && c.actualSide === "attack")!;
    expect(cell.positions).toBe(2);
    expect(cell.gamesWithAtLeastOne).toBe(2);
    expect(cell.maxPositionsInOneGame).toBe(1);
  });

  it("片方の局(g1)に 2 件・もう片方(g2)に 0 件なら gamesWithAtLeastOne 1・maxPositionsInOneGame 2", () => {
    const geo = buildObsGeo([source], BY_GAME_POSITIONS, null, null);
    const cell = geo.sideCrossByGame.cells.find((c) => c.top1Side === "defense" && c.actualSide === "defense")!;
    expect(cell.positions).toBe(2);
    expect(cell.gamesWithAtLeastOne).toBe(1);
    expect(cell.maxPositionsInOneGame).toBe(2);
  });

  it("both(top1Side が both・actualSide が both)は「同じ側」の分子に混ざらない(both-attack は attack-attack と別マスに、defense-both は defense-attack や defense-defense に足し込まれない)", () => {
    const geo = buildObsGeo([source], BY_GAME_POSITIONS, null, null);
    const cellOf = (top1Side: string, actualSide: string) => geo.sideCrossByGame.cells.find((c) => c.top1Side === top1Side && c.actualSide === actualSide)!;
    expect(cellOf("both", "attack").positions).toBe(1); // top1Side が both の行が独立に数えられている
    expect(cellOf("attack", "attack").positions).toBe(2); // both-attack が attack-attack に混ざっていない
    expect(cellOf("defense", "both").positions).toBe(1); // actualSide が both の行が独立に数えられている
    expect(cellOf("defense", "attack").positions).toBe(0); // defense-both が defense-attack へ二重に足し込まれていない(統括が 2026-09-26 に禁じた挙動)
    expect(cellOf("defense", "defense").positions).toBe(2); // defense-both が defense-defense にも紛れ込んでいない
  });

  it("positions は同じ入力の sideCrossTable の同じマスの count と 16/16 一致し、16 マスの和は sideCrossTable の和(= fork の行数)と一致する(不変条件 2・3)", () => {
    const geo = buildObsGeo([source], BY_GAME_POSITIONS, null, null);
    const tableByKey = new Map(geo.sideCrossTable.map((c) => [`${c.top1Side}|${c.actualSide}`, c.count]));
    for (const cell of geo.sideCrossByGame.cells) {
      expect(cell.positions).toBe(tableByKey.get(`${cell.top1Side}|${cell.actualSide}`));
    }
    const byGameTotal = geo.sideCrossByGame.cells.reduce((sum, c) => sum + c.positions, 0);
    const tableTotal = geo.sideCrossTable.reduce((sum, c) => sum + c.count, 0);
    expect(byGameTotal).toBe(tableTotal);
    // fork===true の行数: g1 は attack-attack 1 + defense-defense 2 + both-attack 1 = 4(fork===false の
    // 1 行は数えない)、g2 は attack-attack 1 + defense-both 1 = 2。合計 6。
    expect(byGameTotal).toBe(6);
  });

  it("positions が 0 のマスは gamesWithAtLeastOne も maxPositionsInOneGame も 0、正の数のマスはどちらも 1 以上(不変条件 4・5)", () => {
    const geo = buildObsGeo([source], BY_GAME_POSITIONS, null, null);
    for (const cell of geo.sideCrossByGame.cells) {
      if (cell.positions === 0) {
        expect(cell.gamesWithAtLeastOne).toBe(0);
        expect(cell.maxPositionsInOneGame).toBe(0);
      } else {
        expect(cell.gamesWithAtLeastOne).toBeGreaterThanOrEqual(1);
        expect(cell.maxPositionsInOneGame).toBeGreaterThanOrEqual(1);
      }
    }
  });

  it("gamesWithAtLeastOne ≤ min(positions, gamesTotal)、maxPositionsInOneGame ≤ positions(不変条件 6)", () => {
    const geo = buildObsGeo([source], BY_GAME_POSITIONS, null, null);
    for (const cell of geo.sideCrossByGame.cells) {
      expect(cell.gamesWithAtLeastOne).toBeLessThanOrEqual(Math.min(cell.positions, geo.sideCrossByGame.gamesTotal));
      expect(cell.maxPositionsInOneGame).toBeLessThanOrEqual(cell.positions);
    }
  });

  it("--whatif-v2-dir 無し(null)なら gamesTotal 0・16 マスすべて 0(不変条件 7。18 局測ったように見せない)", () => {
    const geo = buildObsGeo([source], null, null, null);
    expect(geo.sideCrossByGame.gamesTotal).toBe(0);
    expect(geo.sideCrossByGame.cells).toHaveLength(16);
    expect(geo.sideCrossByGame.cells.every((c) => c.positions === 0 && c.gamesWithAtLeastOne === 0 && c.maxPositionsInOneGame === 0)).toBe(true);
  });
});

// (f) 名前の表に将棋の語彙が無い(機械で確かめる。data/shapes・data/openings・data/intents の name・family と比べる)
function shogiVocabularyWords(): string[] {
  const words: string[] = [];
  for (const dir of ["shapes", "openings", "intents"]) {
    const dirPath = fileURLToPath(new URL(`../../../data/${dir}/`, import.meta.url));
    for (const file of readdirSync(dirPath).filter((name) => name.endsWith(".json"))) {
      const json = JSON.parse(readFileSync(join(dirPath, file), "utf-8")) as { name?: unknown; family?: unknown };
      if (typeof json.name === "string" && json.name.length > 0) words.push(json.name);
      if (typeof json.family === "string" && json.family.length > 0) words.push(json.family);
    }
  }
  return words;
}

describe("obsGeo の名前の表(将棋の語彙を含まない)", () => {
  it("GEO_VOCABULARY_WORDS のどの語も data/shapes・data/openings・data/intents の name・family と重ならない", () => {
    const shogiWords = shogiVocabularyWords();
    expect(shogiWords.length).toBeGreaterThan(0); // data/ を実際に読めていることの確認(0 件なら検査していないのと同じ)
    for (const word of GEO_VOCABULARY_WORDS) {
      for (const shogiWord of shogiWords) {
        expect(word.includes(shogiWord) || shogiWord.includes(word), `「${word}」と将棋の語彙「${shogiWord}」が重なる`).toBe(false);
      }
    }
  });
});

// ---- (g) CLI(scripts/playtest/obsGeo.ts)を実際に spawn する ----

describe("obsGeo.ts(CLI)", () => {
  const WORK = mkdtempSync(join(tmpdir(), "obsGeo-cli-"));
  afterAll(() => rmSync(WORK, { recursive: true, force: true }));

  function writeFixture(): { recordsPath: string; kifuPath: string } {
    const cliMoves = GAME01_MOVES.slice(0, 4);
    const cliMeta = { kind: "meta", kifuId: "obsg-cli-01", startedAt: "", gitHead: null, enginePath: "" };
    const cliRecords = plantedRecords(cliMoves, {});
    const recordsPath = join(WORK, "records.jsonl");
    writeFileSync(recordsPath, [cliMeta, ...cliRecords].map((line) => JSON.stringify(line)).join("\n") + "\n", "utf-8");
    const kifuPath = join(WORK, "obsg-cli-01.fixed.json");
    writeFileSync(
      kifuPath,
      JSON.stringify({ id: "obsg-cli-01", ending: { kind: "resign", ply: 5 }, moves: cliMoves, moveSeconds: cliMoves.map(() => ({ spentSec: 1, totalSec: 1 })) }),
      "utf-8",
    );
    return { recordsPath, kifuPath };
  }

  it("(g)必須が揃えば exit 0 で obs_geo.json を書き、必須の引数が無ければ exit 2(使い方を出して止める)", () => {
    const { recordsPath, kifuPath } = writeFixture();
    const outPath = join(WORK, "obs_geo.json");
    const ok = spawnSync("npx", ["tsx", OBS_GEO_TS, "--records", recordsPath, "--kifu", kifuPath, "--out", outPath], { cwd: REPO_ROOT, encoding: "utf-8" });
    expect(ok.status, ok.stderr).toBe(0);
    const written = JSON.parse(readFileSync(outPath, "utf-8")) as { kind: string; schemaVersion: string; moves: unknown[]; decisionContext: unknown[] };
    expect(written.kind).toBe("obs_geo");
    expect(written.schemaVersion).toBe("0.1");
    expect(Array.isArray(written.moves)).toBe(true);
    expect(Array.isArray(written.decisionContext)).toBe(true);

    const missingOutPath = join(WORK, "obs_geo_missing.json");
    const missing = spawnSync("npx", ["tsx", OBS_GEO_TS, "--out", missingOutPath], { cwd: REPO_ROOT, encoding: "utf-8" });
    expect(missing.status).toBe(2);
  });
});
