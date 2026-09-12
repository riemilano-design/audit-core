// STEP T-7(A-1)で作った関数群。STEP 5-F(docs/STEP_5-F_PLAN_2026-09-12.md 4. A-1)
// で本番側(apps/server/src/analysis/engineReference.ts)へ移設した(算法を
// 二重に持たないため。2026-09-12人間の確認)。
// このファイルは、ハーネス側(replay.ts・explore.ts・invariants/*)の呼び出し
// 箇所を壊さないための薄いre-exportだけを行う。実装・テストは本番側にある。

export {
  captureSquareOf,
  measureEngineReference,
  passSfen,
  type EngineReference,
  type EngineReferenceAfterPass,
  type EngineReferenceSide,
} from "../../../apps/server/src/analysis/engineReference.js";
