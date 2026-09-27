// STEP OBS-5'(docs/LANE_DIAG_LOG_2026-09.md §12.6)。lib/obsExtra.ts の試験。
// 小さな作り物(GAME01_MOVES。既存の lib/reportData.test.ts と同じ流儀)で、既存の値の写しであることを確かめる。
// (a)〜(e) は組み立て(buildObsExtra)そのもの、(f) は CLI(scripts/playtest/obsExtra.ts)を実際に spawn する。
// **一時ディレクトリ以外に書かない**(他の CLI 試験〈gate.test.ts 等〉と同じ理由。作業ツリーへは書かない)。

import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, describe, expect, it } from "vitest";

import type { MetaLine, RecordLine } from "../invariants/types.js";
import { engineRef, GAME01_MOVES, plantedRecords } from "./failureEventFixtures.js";
import { buildObsExtra, ObsExtraError } from "./obsExtra.js";
import { buildGames, buildPatientGames, buildPatientTime, countedPairsOf, moveSecondsOf, phaseSpentOfGame, type GameSource } from "./reportData.js";

const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const OBS_EXTRA_TS = fileURLToPath(new URL("../obsExtra.ts", import.meta.url));

/** キーは KIF の手数(1 始まり。overrides 以外は null)。lib/reportData.test.ts の同名のローカル関数と同じ形。 */
function timeArrayWith(overrides: Record<number, { spentSec: number; totalSec: number }>): Array<{ spentSec: number; totalSec: number } | null> {
  return GAME01_MOVES.map((_, i) => overrides[i + 1] ?? null);
}

// ---- (a)〜(c)(e) 共通の 1 局(先手・GAME01_MOVES・分岐点 49 に急落 1 件) ----

const records: RecordLine[] = plantedRecords(GAME01_MOVES, { 48: engineRef(500, { bestmove: "2h2g" }), 50: engineRef(-300) });
const meta = { kind: "meta", kifuId: "obsx-01", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine;
// displayPly 1(early)・15(early)・29(mid)・49(late、崩れた組)にだけ秒を植える。他は null(spentSec が無い組を作る)。
const moveSeconds = timeArrayWith({
  1: { spentSec: 1, totalSec: 1 }, // bucket 0(0〜1 秒)
  15: { spentSec: 3, totalSec: 10 }, // bucket 1(2〜4 秒)
  29: { spentSec: 7, totalSec: 30 }, // bucket 2(5〜9 秒)
  49: { spentSec: 15, totalSec: 100 }, // bucket 3(10 秒以上)。崩れた組
});
const source: GameSource = { kifuId: "obsx-01", meta, records, fixed: { id: "obsx-01", ending: { kind: "mate", ply: 56 }, moves: GAME01_MOVES, moveSeconds } };

describe("buildObsExtra: pairs(a)組と局・手の対応 ― bucket ごとに数え直すと buildPatientTime(...).bySpent と一致", () => {
  it("4 段の {n, collapsed} が bySpent と同じ", () => {
    const games = buildGames([source]);
    const patientGames = buildPatientGames(games);
    const time = buildPatientTime(games, patientGames, undefined);
    const extra = buildObsExtra([source], null, null);

    const recount = [0, 1, 2, 3].map((bucket) => {
      const inBucket = extra.pairs.filter((pair) => pair.spentBucket === bucket);
      return { n: inBucket.length, collapsed: inBucket.filter((pair) => pair.collapsed).length };
    });
    expect(time.available).toBe(true);
    expect(recount).toStrictEqual(time.bySpent);
  });
});

describe("buildObsExtra: pairs(b)spentSec が取れない組は null で残る(落とさない)", () => {
  it("spentSec: null の組が存在し、spentBucket も null。全体の件数は countedPairsOf と同じ(落としていない)", () => {
    const games = buildGames([source]);
    const extra = buildObsExtra([source], null, null);

    const withoutSpent = extra.pairs.filter((pair) => pair.spentSec === null);
    expect(withoutSpent.length).toBeGreaterThan(0);
    for (const pair of withoutSpent) expect(pair.spentBucket).toBeNull();

    expect(extra.pairs.length).toBe(countedPairsOf(games[0]!).length);
  });
});

describe("buildObsExtra: phaseMoves(c)段ごとの消費(sec)が phaseSpentOfGame と一致", () => {
  it("early・mid・late の sec が phaseSpentOfGame(既存)と同じ", () => {
    const games = buildGames([source]);
    const patientGames = buildPatientGames(games);
    const seconds = moveSecondsOf(games[0]!.source.fixed) ?? [];
    const sums = phaseSpentOfGame(games[0]!, seconds, patientGames[0]!.total);
    const extra = buildObsExtra([source], null, null);

    expect(extra.phaseMoves).toHaveLength(1);
    expect(extra.phaseMoves[0]).toMatchObject({
      gameNo: 1,
      early: { sec: sums.early },
      mid: { sec: sums.mid },
      late: { sec: sums.late },
    });
  });
});

describe("buildObsExtra: phaseSecPerMoveMedians(d)moves が 0 の局はその段の中央値の分母に入れない", () => {
  // gameA: displayPly 1(early)だけに秒を持つ。mid・late の moves は 0。
  const movesSecondsA = timeArrayWith({ 1: { spentSec: 2, totalSec: 2 } });
  const sourceA: GameSource = {
    kifuId: "obsx-d-a",
    meta: { kind: "meta", kifuId: "obsx-d-a", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine,
    records: plantedRecords(GAME01_MOVES, {}),
    fixed: { id: "obsx-d-a", ending: { kind: "resign", ply: 57 }, moves: GAME01_MOVES, moveSeconds: movesSecondsA },
  };
  // gameB: early(4)・mid(8)・late(20)の 3 段すべてに秒を持つ。
  const movesSecondsB = timeArrayWith({ 1: { spentSec: 4, totalSec: 4 }, 29: { spentSec: 8, totalSec: 40 }, 49: { spentSec: 20, totalSec: 200 } });
  const sourceB: GameSource = {
    kifuId: "obsx-d-b",
    meta: { kind: "meta", kifuId: "obsx-d-b", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine,
    records: plantedRecords(GAME01_MOVES, {}),
    fixed: { id: "obsx-d-b", ending: { kind: "resign", ply: 57 }, moves: GAME01_MOVES, moveSeconds: movesSecondsB },
  };

  it("timeUpLoss は 0 局(ending が resign なので null)。other は 2 局: early = median(2,4) = 3, mid = median(8のみ) = 8, late = median(20のみ) = 20", () => {
    const extra = buildObsExtra([sourceA, sourceB], null, null);
    expect(extra.phaseSecPerMoveMedians.timeUpLoss).toStrictEqual({ games: 0, early: null, mid: null, late: null });
    expect(extra.phaseSecPerMoveMedians.other).toStrictEqual({ games: 2, early: 3, mid: 8, late: 20 });
  });
});

// STEP ENDING_CLOCK(docs/STEP_ENDING_CLOCK_PLAN_2026-09-27.md §4 の 5・§5 の 8)。
// `timeUpLossGameNos` を渡せば、`buildTimeUpLosses`(lib/reportData.ts)が出した判定と同じ局を指す(判定を 2 つにしない)。
describe("buildObsExtra: timeUpLossGameNos(判定を 2 つにしない。試験 8)", () => {
  // 4 手(偶数)・ending: resign(投了)。本人(先手)の最後の手(3 手目)の totalSec がちょうど 180(時計が一致)。
  const clockLossMoves = GAME01_MOVES.slice(0, 4);
  const clockLossSource: GameSource = {
    kifuId: "obsx-clock-loss",
    meta: { kind: "meta", kifuId: "obsx-clock-loss", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine,
    records: plantedRecords(clockLossMoves, {}),
    fixed: {
      id: "obsx-clock-loss",
      ending: { kind: "resign", ply: 5 },
      moves: clockLossMoves,
      moveSeconds: [
        { spentSec: 1, totalSec: 1 },
        { spentSec: 1, totalSec: 2 },
        { spentSec: 178, totalSec: 180 },
        { spentSec: 1, totalSec: 3 },
      ],
    },
  };
  // 同じ形だが本人の最後の手が 179 秒(時計は一致しない)。
  const nearMissSource: GameSource = {
    kifuId: "obsx-clock-nearmiss",
    meta: { kind: "meta", kifuId: "obsx-clock-nearmiss", startedAt: "", gitHead: null, enginePath: "" } as unknown as MetaLine,
    records: plantedRecords(clockLossMoves, {}),
    fixed: {
      id: "obsx-clock-nearmiss",
      ending: { kind: "resign", ply: 5 },
      moves: clockLossMoves,
      moveSeconds: [
        { spentSec: 1, totalSec: 1 },
        { spentSec: 1, totalSec: 2 },
        { spentSec: 177, totalSec: 179 },
        { spentSec: 1, totalSec: 3 },
      ],
    },
  };

  it("timeUpLossGameNos を渡さなければ、語だけの判定に落ちる(ending が resign なので 2 局とも false。既定の挙動)", () => {
    const extra = buildObsExtra([clockLossSource, nearMissSource], null, null);
    expect(extra.phaseMoves.map((row) => row.timeUpLoss)).toEqual([false, false]);
  });

  it("buildPatientTime(timeLimitSec: 180).timeUpLosses の局番号を渡すと、buildObsExtra の timeUpLoss はそれと同じ局を指す(時計で一致した局だけ true)", () => {
    const games = buildGames([clockLossSource, nearMissSource]);
    const patientGames = buildPatientGames(games);
    const time = buildPatientTime(games, patientGames, 180);
    const timeUpLossGameNos = new Set((time.timeUpLosses ?? []).map((g) => g.gameNo));
    expect(timeUpLossGameNos.size).toBe(1); // clockLossSource だけ(nearMiss は入らない)

    const extra = buildObsExtra([clockLossSource, nearMissSource], null, null, timeUpLossGameNos);
    const byId = new Map(extra.phaseMoves.map((row, index) => [patientGames[index]!.id, row.timeUpLoss]));
    expect(byId.get("obsx-clock-loss")).toBe(true);
    expect(byId.get("obsx-clock-nearmiss")).toBe(false);
  });
});

describe("buildObsExtra(e): 入力の形が違えば例外", () => {
  it("記録の kifuId と固定棋譜の id が違えば例外(既存の buildGames の検査をそのまま使う。落ちる先は ReportDataError なので ObsExtraError では拾わない)", () => {
    const badSource: GameSource = { kifuId: "obsx-01", meta, records, fixed: { id: "different-id", ending: { kind: "mate", ply: 56 }, moves: GAME01_MOVES } };
    expect(() => buildObsExtra([badSource], null, null)).toThrow();
    // ObsExtraError はこのファイルで定義しているが、この段では投げていない(将来の拡張用)。export だけ確かめる。
    expect(ObsExtraError.prototype).toBeInstanceOf(Error);
  });
});

// ---- (f) CLI(scripts/playtest/obsExtra.ts)を実際に spawn する ----

describe("obsExtra.ts(CLI)", () => {
  const WORK = mkdtempSync(join(tmpdir(), "obsExtra-cli-"));
  afterAll(() => rmSync(WORK, { recursive: true, force: true }));

  function writeFixture(): { recordsPath: string; kifuPath: string } {
    const cliMoves = GAME01_MOVES.slice(0, 4);
    const cliMeta = { kind: "meta", kifuId: "obsx-cli-01", startedAt: "", gitHead: null, enginePath: "" };
    const cliRecords = plantedRecords(cliMoves, {});
    const recordsPath = join(WORK, "records.jsonl");
    writeFileSync(recordsPath, [cliMeta, ...cliRecords].map((line) => JSON.stringify(line)).join("\n") + "\n", "utf-8");
    const kifuPath = join(WORK, "obsx-cli-01.fixed.json");
    writeFileSync(
      kifuPath,
      JSON.stringify({ id: "obsx-cli-01", ending: { kind: "resign", ply: 5 }, moves: cliMoves, moveSeconds: cliMoves.map(() => ({ spentSec: 1, totalSec: 1 })) }),
      "utf-8",
    );
    return { recordsPath, kifuPath };
  }

  it("(f)必須が揃えば exit 0 で obs_extra.json を書き、必須の引数が無ければ exit 2(使い方を出して止める)", () => {
    const { recordsPath, kifuPath } = writeFixture();
    const outPath = join(WORK, "obs_extra.json");
    const ok = spawnSync("npx", ["tsx", OBS_EXTRA_TS, "--records", recordsPath, "--kifu", kifuPath, "--out", outPath], { cwd: REPO_ROOT, encoding: "utf-8" });
    expect(ok.status, ok.stderr).toBe(0);
    const written = JSON.parse(readFileSync(outPath, "utf-8")) as { kind: string; schemaVersion: string; pairs: unknown[] };
    expect(written.kind).toBe("obs_extra");
    expect(written.schemaVersion).toBe("0.1");
    expect(Array.isArray(written.pairs)).toBe(true);

    const missingOutPath = join(WORK, "obs_extra_missing.json");
    const missing = spawnSync("npx", ["tsx", OBS_EXTRA_TS, "--out", missingOutPath], { cwd: REPO_ROOT, encoding: "utf-8" });
    expect(missing.status).toBe(2);
  });
});
