// STEP U6-T2(docs/STEP_U6-T2_PLAN_2026-09-15.md)。段 A の校正に使う既知の値と、その出どころ。
//
// 【値】NNUE 版の記録(scripts/playtest/records/d0-nnue)のうち、U6-L と同じ 4 局を 56 局面に畳み、
// 代表の行の focus_baseline(MultiPV 1・nodes 4,000,000・Threads 1)の読み筋 1 本を見た値
// (計画 §1.7 の定義。2026-09-15 の司令塔の決定 (1))。**記録を観測した数**である。
// **手で書き写した値を信じない**: lib/calibrationBaseline.test.ts が、同じ記録から observeCalibrationBaseline で
// 数え直した値と一致することを見る。記録を取り直したら、ここを書き換える前にその試験が落ちる。
//
// 【幅】CALIBRATION_BOUND_RATE_TOLERANCE は**観測ではなく選んだ許容であり、測って決めた値ではない**(計画 §4)。取り直さない。
//
// 【書き換えない】値は凍結してある。CLI などで後から `source` を代入すると、型検査で落ち、実行時にも例外になる
// (U6-T の再監査 A の G-5: 後から代入する形は、門も照合もすり抜けた)。
//
// 【参考】MATERIAL 版の評価関数で取った U6-L の記録では 28 / 56・2・3 だった(校正には使わない)。

import type { CalibrationBaseline, CalibrationSource } from "./multiPvSurvey.js";

/** 校正の値を数えた 4 局(記録のファイル名から .jsonl を除いたもの = meta 行の kifuId)。段 A の roots と同じ 56 局面になる */
export const CALIBRATION_KIFU_IDS: readonly string[] = Object.freeze([
  "2026-09-10-claude-10moves",
  "2026-09-12-live-30moves-claude-1",
  "2026-09-12-live-30moves-claude-2",
  "2026-09-12-live-30moves-claude-3",
]);

export const CALIBRATION_BASELINE: Readonly<Omit<CalibrationBaseline, "source">> & { readonly source: Readonly<CalibrationSource> } =
  Object.freeze({
    marked: 25,
    total: 56,
    maxBoundedPvLength: 2,
    minPlies: 3,
    source: Object.freeze({
      recordsDir: "scripts/playtest/records/d0-nnue",
      // 記録の meta 行の gitHead(7 本とも同じ。dirty false)
      gitHead: "a9da05898d3a099cd2f1d5be0b1e123e824070b6",
      // 記録をリポジトリに置いたコミット
      recordsCommit: "0cce0c34c02a9c6c84d1afdf8a442c61d325b063",
      evaluator:
        "nn.bin sha256 768068f0d534a0603a5d38bcd143de6bbca820d5f1c95a14d40863e5b7892d76" +
        "(apps/server/engine/nnue/eval/nn.bin で確かめた)/ id name「YaneuraOu NNUE 9.80git 64APPLEM1」" +
        "(D0-NNUE 計画書 f64ae13 の 6.9 にある担当 C の観測。B は確かめていない)",
    }),
  });

/** 標識付きの割合の幅(± 15 ポイント)。**選んだ許容であり、測って決めた値ではない。** */
export const CALIBRATION_BOUND_RATE_TOLERANCE = 0.15;
