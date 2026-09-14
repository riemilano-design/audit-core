// STEP D-COST の lib の試験(docs/STEP_D-COST_PLAN_2026-09-15.md 7.2)。**エンジンは起動しない。**
// 深い記録・軽い記録は、探索モード game-01 の実際の指し手に合成の評価を植えて作る(lib/failureEventFixtures.ts)。

import { describe, expect, it } from "vitest";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { DRAFT_RULE_1 } from "./failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords, type PlantedEvaluation } from "./failureEventFixtures.js";
import {
  batchSeconds,
  buildScanReport,
  compareScans,
  missRate,
  renderScanReport,
  singleStageSeconds,
  sumComparisons,
  twoStageReferencePliesSeconds,
  twoStageTargetPliesSeconds,
  type ScanComparison,
  type ScanInput,
} from "./scanCompare.js";

const DEEP = 4_000_000;
const LIGHT = 100_000;
const BAND = 100;
/** ply 0〜24 の ready 行 13 行。game-01 で先手が王手を受けるのは 34 手目以降なので、この範囲に王手中の行は無い */
const MOVES = GAME01_MOVES.slice(0, 24);
const META = { kind: "meta", kifuId: "k", startedAt: "t", gitHead: null, enginePath: "/e/nnue/YaneuraOu-by-gcc" } as MetaLine;

/** 植えた評価の engineReference.nodes を、その走査のノード数にそろえる(fixtures の engineRef は 4,000,000) */
function scan(plant: Record<number, PlantedEvaluation>, nodes: number, moves: readonly string[] = MOVES): ScanInput {
  const records = plantedRecords(moves, plant).map((record): RecordLine =>
    record.engineReference ? { ...record, engineReference: { ...record.engineReference, nodes } } : record,
  );
  return { records, meta: META, expectedNodes: nodes };
}

const compare = (deep: ScanInput, light: ScanInput): ScanComparison => compareScans("k", deep, light, DRAFT_RULE_1, BAND);
const counted = (result: ScanComparison) => {
  if (result.kind !== "counted") throw new Error(`数えられなかった: ${result.reason} ${result.detail}`);
  return result;
};

describe("急落候補の突き合わせ(計画 2.2 の 4 区分)", () => {
  it("F-C1 拾えた: 深い −600・軽い −450 はどちらも急落候補", () => {
    const result = counted(compare(scan({ 4: engineRef(100), 6: engineRef(-500) }, DEEP), scan({ 4: engineRef(100), 6: engineRef(-350) }, LIGHT)));
    expect(result.drops).toEqual({ base: 1, found: 1, notFound: 0, notComparable: 0, notComparableReasons: {}, notMeasured: 0 });
    expect(result.diffGaps).toEqual([150]);
    expect(result.kindMismatch).toBe(0);
  });

  it("F-C2 取りこぼし: 深い −450・軽い −350 は、軽い走査で比べたが急落にならない。深い差は閾値の近く", () => {
    const result = counted(compare(scan({ 4: engineRef(100), 6: engineRef(-350) }, DEEP), scan({ 4: engineRef(100), 6: engineRef(-250) }, LIGHT)));
    expect(result.drops).toMatchObject({ base: 1, found: 0, notFound: 1, notComparable: 0, notMeasured: 0 });
    expect(missRate(result.drops)).toEqual({ numerator: 1, denominator: 1, value: 1 });
    expect(result.nearThreshold).toEqual({ deepPairs: 1, missed: 1 });
  });

  it("閾値から遠い取りこぼし(深い −800・軽い −300)は「うち閾値の近く」に入れない(変異 V-14 が沈黙したので足した)", () => {
    const result = counted(compare(scan({ 4: engineRef(100), 6: engineRef(-700) }, DEEP), scan({ 4: engineRef(100), 6: engineRef(-200) }, LIGHT)));
    expect(result.drops).toMatchObject({ base: 1, found: 0, notFound: 1 });
    expect(result.nearThreshold).toEqual({ deepPairs: 0, missed: 0 });
  });

  it("F-C3 比べられなかった: 軽い走査の直後の行が測れなかった(null)なら、取りこぼしに入れない", () => {
    const result = counted(compare(scan({ 4: engineRef(100), 6: engineRef(-500) }, DEEP), scan({ 4: engineRef(100), 6: null }, LIGHT)));
    expect(result.drops).toEqual({
      base: 1,
      found: 0,
      notFound: 0,
      notComparable: 1,
      notComparableReasons: { notMeasurable: 1 },
      notMeasured: 0,
    });
    expect(missRate(result.drops).value).toBeNull();
  });

  it("F-C4 測っていない: 軽い記録が途中で終わり、その組が無ければ、取りこぼしに入れない", () => {
    const result = counted(compare(scan({ 6: engineRef(-500) }, DEEP), scan({}, LIGHT, MOVES.slice(0, 4))));
    expect(result.drops).toMatchObject({ base: 1, found: 0, notFound: 0, notComparable: 0, notMeasured: 1 });
  });

  it("F-C5 余計に拾った: 深い −300・軽い −450 は、軽い走査だけの急落候補", () => {
    const result = counted(compare(scan({ 4: engineRef(100), 6: engineRef(-200) }, DEEP), scan({ 4: engineRef(100), 6: engineRef(-350) }, LIGHT)));
    expect(result.drops.base).toBe(0);
    expect(result.extras).toMatchObject({ base: 1, found: 0, notFound: 1, notComparable: 0, notMeasured: 0 });
  });

  it("F-C6 種類の食い違い: 深い cpDrop・軽い mateDrop は拾えたに入れ、食い違いを 1 と数える", () => {
    const result = counted(compare(scan({ 6: engineRef(-500) }, DEEP), scan({ 6: engineRef(null, { mate: -3 }) }, LIGHT)));
    expect(result.drops).toMatchObject({ base: 1, found: 1, notFound: 0 });
    expect(result.kindMismatch).toBe(1);
    expect(result.diffGaps).toEqual([]); // 軽い側は差を取っていない
  });
});

describe("比べる前の確かめ(計画 7.1 の G)", () => {
  it("F-C7 G-1: 軽い記録に nodes 4,000,000 の行が 1 行でも混ざれば、その棋譜は数えられなかった", () => {
    const light = scan({}, LIGHT);
    const records = light.records.map((record) =>
      record.ply === 2 && record.engineReference ? { ...record, engineReference: { ...record.engineReference, nodes: DEEP } } : record,
    );
    const result = compare(scan({}, DEEP), { ...light, records });
    expect(result).toMatchObject({ kind: "notCounted", reason: "nodes_mismatch" });
  });

  it("F-C8 G-2: 同じ ply の sfen が違えば、数えられなかった", () => {
    const light = scan({}, LIGHT);
    const other = light.records.find((record) => record.ply === 6)!.sfen;
    const records = light.records.map((record) => (record.ply === 4 ? { ...record, sfen: other } : record));
    expect(compare(scan({}, DEEP), { ...light, records })).toMatchObject({ kind: "notCounted", reason: "sfen_mismatch" });
  });

  it("G-3: meta の enginePath が違う・meta が無い なら、数えられなかった", () => {
    const light = scan({}, LIGHT);
    expect(compare(scan({}, DEEP), { ...light, meta: { ...META, enginePath: "/e/other/YaneuraOu-by-gcc" } })).toMatchObject({
      kind: "notCounted",
      reason: "engine_path_mismatch",
    });
    expect(compare(scan({}, DEEP), { ...light, meta: undefined })).toMatchObject({ kind: "notCounted", reason: "meta_missing" });
  });
});

describe("率の分母と合計", () => {
  // 深い: 2→4・6→8・10→12・14→16・18→20 が急落候補。軽い: 2→4・6→8 は拾えた、10→12 は取りこぼし、14→16・18→20 は比べられなかった
  const deep = scan({ 4: engineRef(-500), 8: engineRef(-500), 12: engineRef(-500), 16: engineRef(-500), 20: engineRef(-500) }, DEEP);
  const light = scan({ 4: engineRef(-450), 8: engineRef(-450), 12: engineRef(-300), 16: null, 20: null }, LIGHT);

  it("F-C9 取りこぼし率の分母に、比べられなかった組を入れない(1/3 であって 1/5 ではない)", () => {
    const result = counted(compare(deep, light));
    expect(result.drops).toMatchObject({ base: 5, found: 2, notFound: 1, notComparable: 2, notMeasured: 0 });
    expect(missRate(result.drops)).toEqual({ numerator: 1, denominator: 3, value: 1 / 3 });
  });

  it("合計は数を足してから率を出し直す。数えられなかった棋譜は足さない", () => {
    const one = counted(compare(deep, light));
    const bad: ScanComparison = { kind: "notCounted", kifuId: "x", reason: "sfen_mismatch", detail: "-" };
    const total = sumComparisons([one, one, bad]);
    expect(total.drops).toMatchObject({ base: 10, found: 4, notFound: 2, notComparable: 4, notMeasured: 0 });
    expect(missRate(total.drops)).toEqual({ numerator: 2, denominator: 6, value: 1 / 3 });
    expect(total.drops.notComparableReasons).toEqual({ notMeasurable: 4 });
  });

  it("合計は閾値の近くの組と、そのうちの取りこぼしも足す(監査 A の任意 a)", () => {
    // F-C2 と同じ形: 深い −450(閾値の近く)・軽い −350(取りこぼし)
    const near = counted(compare(scan({ 4: engineRef(100), 6: engineRef(-350) }, DEEP), scan({ 4: engineRef(100), 6: engineRef(-250) }, LIGHT)));
    expect(sumComparisons([near, near]).nearThreshold).toEqual({ deepPairs: 2, missed: 2 });
  });
});

describe("パスすると詰まされる読み(matedIfPass。急落候補とは別に数える)", () => {
  it("深い走査だけで当たり、軽い走査の直後の行は測れていれば「比べて無し」、測れなかったなら「比べられなかった」", () => {
    const deep = scan({ 6: engineRef(100, { afterPassMate: 3 }) }, DEEP);
    const measured = counted(compare(deep, scan({ 6: engineRef(100) }, LIGHT)));
    expect(measured.matedIfPass.deepToLight).toMatchObject({ base: 1, found: 0, notFound: 1, notComparable: 0 });
    // matedIfPass だけで当たった Failure Event は、急落候補(drops・extras)に入れない(計画 2.2。監査 A の必須 2)
    expect(measured.drops.base).toBe(0);
    expect(measured.extras.base).toBe(0);
    const notMeasurable = counted(compare(deep, scan({ 6: null }, LIGHT)));
    expect(notMeasurable.matedIfPass.deepToLight).toMatchObject({ base: 1, found: 0, notFound: 0, notComparable: 1, notComparableReasons: { notMeasurable: 1 } });
  });

  it("軽い記録にその組が無ければ「測っていない」(比べて無しに畳まない。監査 A の必須 1)", () => {
    const deep = scan({ 6: engineRef(100, { afterPassMate: 3 }) }, DEEP);
    const result = counted(compare(deep, scan({}, LIGHT, MOVES.slice(0, 4))));
    expect(result.matedIfPass.deepToLight).toEqual({ base: 1, found: 0, notFound: 0, notComparable: 0, notComparableReasons: {}, notMeasured: 1 });
  });
});

describe("報告(例外を外へ出さない・0 件も出す)", () => {
  it("例外は「数えられなかった」行にし、表に理由を出す", () => {
    const report = buildScanReport([{ kifuId: "bad", deep: scan({}, DEEP), light: scan({}, LIGHT) }], DRAFT_RULE_1, BAND, () => {
      throw new RangeError("壊れた");
    });
    expect(report[0]).toEqual({ kind: "notCounted", kifuId: "bad", reason: "exception", detail: "RangeError: 壊れた" });
    expect(renderScanReport(report, { onlyDeep: [], onlyLight: [] })).toContain("- 数えられなかった: bad(exception: RangeError: 壊れた)");
  });

  it("棋譜ごとの行と合計の行、片方にしか無い記録を出す。分母 0 は 0% と書かない", () => {
    const report = buildScanReport(
      [
        { kifuId: "g1", deep: scan({ 4: engineRef(-500) }, DEEP), light: scan({ 4: engineRef(-300) }, LIGHT) },
        { kifuId: "g2", deep: scan({}, DEEP), light: scan({}, LIGHT) },
      ],
      DRAFT_RULE_1,
      BAND,
    );
    const text = renderScanReport(report, { onlyDeep: ["only-deep.jsonl"], onlyLight: [] }).join("\n");
    expect(text).toContain("| g1 | 1 | 0 | 1 | 0 | 0 | 1/1(100.0%) | 0 |");
    expect(text).toContain("| g2 | 0 | 0 | 0 | 0 | 0 | 分母 0 | 0 |");
    expect(text).toContain("| 合計 | 1 | 0 | 1 | 0 | 0 | 1/1(100.0%) | 0 |");
    expect(text).toContain("- 深い走査にしか無い(軽い走査は測っていない): only-deep.jsonl");
    expect(text).toContain("「比べられなかった」「測っていない」は取りこぼしではない。");
  });
});

describe("見積もりの式(計画 5.・3.)", () => {
  it("F-C10 手で計算した値と一致する(二段の式の K と 2 行ぶんを含む)", () => {
    expect(singleStageSeconds({ tBootSec: 2, readyRows: 16, tRowSec: 1.5 })).toBe(26);
    expect(batchSeconds({ games: 1000, perGameSec: 26 })).toBe(26_000);
    // 2 + 16 × 1.5 + 3 × 2 × (14 − 0.4) = 2 + 24 + 81.6
    expect(twoStageReferencePliesSeconds({ tBootSec: 2, readyRows: 16, tRowLightSec: 1.5, candidates: 3, tRefDeepSec: 14, tRefLightSec: 0.4 })).toBeCloseTo(107.6, 10);
    // 2 + 16 × 0.05 + 3 × 2 × 25 = 2 + 0.8 + 150
    expect(twoStageTargetPliesSeconds({ tBootSec: 2, readyRows: 16, tImmSec: 0.05, candidates: 3, tRowDeepSec: 25 })).toBeCloseTo(152.8, 10);
  });
});
