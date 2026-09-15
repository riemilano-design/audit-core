// STEP D4(docs/STEP_D4_PLAN_2026-09-15.md §13.6)。gate.test.ts が道具 gate.ts に渡す試験だけの固定の記録の中身。
// GAME01 の手順に評価を植えた記録で、将棋の判断を含めない。**このディレクトリの *.jsonl は gateFixtureText の出力とバイト一致**(gate.test.ts が見る)。
//
// 【なぜ固定の記録にしたか】道具は作業ツリーの根の外の入力を止める(監査 93 の R-1)。一時の記録を根の中に書くと、子プロセスの前後で
// `git status --ignored` を比べるほかの試験(diagnose・rescreen・scan-compare・screen-calibrate)が並行の実行で落ちた。試験の実行中は作業ツリーにファイルを作らない。

import { engineRef, GAME01_MOVES, plantedRecords } from "../lib/failureEventFixtures.js";

interface GateFixture {
  kifuId: string;
  /** meta に足す欄 */
  meta?: Record<string, unknown>;
  /** [ply, 本人視点の評価値] */
  plant: ReadonlyArray<readonly [number, number]>;
}

/** ply 20 = +400(ahead)・22 = 0(level): ahead→level の崩れが 1 組 */
const ONE_COLLAPSE = [[20, 400], [22, 0]] as const;
/** 10・20・30 の 3 組とも ahead→level(直後の行も植えて未定にしない) */
const THREE_COLLAPSES = [[10, 400], [12, 0], [20, 400], [22, 0], [30, 400], [32, 0]] as const;

export const GATE_FIXTURES: Readonly<Record<string, GateFixture>> = {
  "m1.jsonl": { kifuId: "gate-fx-m1", plant: ONE_COLLAPSE },
  "m2.jsonl": { kifuId: "gate-fx-m2", plant: ONE_COLLAPSE },
  "s1.jsonl": { kifuId: "gate-fx-s1", plant: ONE_COLLAPSE },
  "s-nodes.jsonl": { kifuId: "gate-fx-s-nodes", meta: { referenceNodes: 400_000 }, plant: ONE_COLLAPSE },
  "g1.jsonl": { kifuId: "gate-fx-g1", meta: { mirrored: true, originalUserSide: "gote" }, plant: ONE_COLLAPSE },
  // R-2: 真の組 = 直前の評価が +300 以上。m1 は 10→12(崩れ)・20→22(崩れ)・30→32(ahead→ahead)・32→34(崩れ)で tn 4、m2・m3 は tn 3 → 材料 tn 10・崩れ 9・3 局
  "r2-m1.jsonl": { kifuId: "gate-fx-r2-m1", plant: [[10, 400], [12, 0], [20, 400], [22, 0], [30, 400], [32, 400], [34, 0]] },
  "r2-m2.jsonl": { kifuId: "gate-fx-r2-m2", plant: THREE_COLLAPSES },
  "r2-m3.jsonl": { kifuId: "gate-fx-r2-m3", plant: THREE_COLLAPSES },
  "r2-s1.jsonl": { kifuId: "gate-fx-r2-s1", plant: THREE_COLLAPSES },
};

/** 固定の記録 1 本の中身(meta の行と ready 行、末尾に改行) */
export function gateFixtureText(name: string): string {
  const spec = GATE_FIXTURES[name];
  if (spec === undefined) throw new Error(`固定の記録 ${name} は GATE_FIXTURES に無い`);
  const meta = { kind: "meta", kifuId: spec.kifuId, startedAt: "t", gitHead: null, enginePath: "/e", searchMode: "nodes", nodes: 4_000_000, threads: 1, referenceNodes: 4_000_000, ...spec.meta };
  const records = plantedRecords(GAME01_MOVES, Object.fromEntries(spec.plant.map(([ply, cp]) => [ply, engineRef(cp)])));
  return [meta, ...records].map((line) => JSON.stringify(line)).join("\n") + "\n";
}
