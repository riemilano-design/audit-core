// recognitionTimeline.ts(Phase 7 Unit 2)のテスト。
//
// 期待値は「現在のdata/ + 既存の判定(resolveStatus / evaluateIntent) + 将棋のルール」から
// 機械的に決まる値であり、将棋的な良し悪しの主張ではない。
// 段階の判定そのものは既存モジュールのテストが担保しているため、ここで検証するのは
// 「時系列としての組み立て方」(いつ・何を・どの順で出すか)に絞る。

import { describe, expect, it } from "vitest";
import { buildRecognitionTimeline } from "./recognitionTimeline.js";
import { DEFAULT_INITIAL_SFEN } from "./moveHistory.js";
import { applyMove } from "../rules/applyMove.js";
import { getLegalMoves } from "../rules/legalMoves.js";

/**
 * 形と狙いの両方が動く、実際に指せる手順(全手が合法であることを確認済み)。
 *
 * - 先手: 角を8hからどけたうえで、玉を5i→6h→7h→8h、銀7i→7h、金4i→5h と動かして
 *   本美濃囲い(玉8h・銀7h・金6i・金5h)を作る。6iの金は初期位置のまま
 * - 後手: 6筋の歩を2回突く。これは data/intents/hayajikake.json の
 *   recognition_pattern(歩 6d → 6e)そのもので、狙いの段階が動く
 *
 * 期待される遷移(既存の判定から機械的に決まる。将棋的な良し悪しの主張ではない):
 *   ply 2  狙い hayajikake      none    -> forming    (6c6d)
 *   ply 4  狙い hayajikake      forming -> matched    (6d6e)
 *   ply 9  形   3件すべて        none    -> forming    (7h8h)
 *   ply 13 形   mino_honmino    forming -> completed  (4i5h)
 */
const SHAPE_AND_INTENT = [
  "7g7f", "6c6d",
  "8h7g", "6d6e",
  "5i6h", "3c3d",
  "6h7h", "8c8d",
  "7h8h", "4a3b",
  "7i7h", "3b4b",
  "4i5h", "4b3b",
];

describe("buildRecognitionTimeline", () => {
  it("初期局面(履歴なし)では、変化が1件も無いため空になる", () => {
    // ply 0 は基準となる最初の観測であり、どの手も原因になっていないため遷移として出さない。
    expect(buildRecognitionTimeline([])).toEqual([]);
  });

  it("形と狙いの変化が、同じ1本の時系列に ply の昇順で並ぶ", () => {
    const timeline = buildRecognitionTimeline(SHAPE_AND_INTENT);

    expect(timeline.length).toBeGreaterThan(0);

    const plies = timeline.map((entry) => entry.ply);
    expect([...plies].sort((a, b) => a - b)).toEqual(plies);

    // 何手目の手が原因かを追えること(根拠になった手と、その時点の局面を持つ)。
    for (const entry of timeline) {
      expect(entry.moveUsi).toBe(SHAPE_AND_INTENT[entry.ply - 1]);
      expect(entry.sfen.length).toBeGreaterThan(0);
      expect(entry.from).not.toBe(entry.to);
    }
  });

  it("本美濃囲いが completed に達した時点が、その手とともに記録される", () => {
    const timeline = buildRecognitionTimeline(SHAPE_AND_INTENT);
    const completed = timeline.find(
      (entry) => entry.kind === "shape" && entry.targetId === "mino_honmino" && entry.to === "completed",
    );

    // 玉8h・銀7h・金6i・金5h が揃うのは 4i5h(最終手)。
    expect(completed).toBeDefined();
    expect(completed?.moveUsi).toBe("4i5h");
  });

  it("相手の狙いの変化も、根拠になった手とともに記録される", () => {
    const timeline = buildRecognitionTimeline(SHAPE_AND_INTENT);
    const intents = timeline.filter((entry) => entry.kind === "intent");

    // 空振りで通らないよう、狙いの遷移が実際に出ていることを確かめる。
    expect(intents.length).toBeGreaterThan(0);
    const matched = intents.find((entry) => entry.to === "matched");
    expect(matched?.targetId).toBe("hayajikake");
    expect(matched?.moveUsi).toBe("6d6e");
  });

  it("認識が形より先に狙いで動いた場合も、起きた順に並ぶ", () => {
    const timeline = buildRecognitionTimeline(SHAPE_AND_INTENT);
    const firstShapePly = timeline.find((e) => e.kind === "shape")?.ply;
    const firstIntentPly = timeline.find((e) => e.kind === "intent")?.ply;

    expect(firstIntentPly).toBeLessThan(firstShapePly!);
  });

  // docs/PHASES.md Phase 7 Unit 2(2026-09-10 に人間が確定): 形と狙いは別々の尺度のままにする。
  // 型でも保証しているが、実行時にも混ざらないことを確認する。
  it("形の段階に matched が、狙いの段階に completed が混ざらない", () => {
    const timeline = buildRecognitionTimeline(SHAPE_AND_INTENT);

    for (const entry of timeline) {
      if (entry.kind === "shape") {
        expect(["none", "forming", "completed"]).toContain(entry.from);
        expect(["none", "forming", "completed"]).toContain(entry.to);
      } else {
        expect(["none", "forming", "matched"]).toContain(entry.from);
        expect(["none", "forming", "matched"]).toContain(entry.to);
        // 狙いの検出範囲は広げていない(相手側のみ)。
        expect(entry.side).toBe("opponent");
      }
    }
  });

  it("同じ入力に対しては常に同じ結果を返す(決定的)", () => {
    expect(buildRecognitionTimeline(SHAPE_AND_INTENT)).toEqual(buildRecognitionTimeline(SHAPE_AND_INTENT));
  });

  it("履歴を1手進めても、既に出ている過去の遷移は変わらない(毎回の再計算が安定している)", () => {
    const shorter = buildRecognitionTimeline(SHAPE_AND_INTENT.slice(0, 8));
    const longer = buildRecognitionTimeline(SHAPE_AND_INTENT);

    expect(longer.slice(0, shorter.length)).toEqual(shorter);
  });

  it("非合法な手を含む履歴では、既存モジュールと同じ例外がそのまま伝播する", () => {
    // 1手目に指せない手。replayMoveHistory(applyMove)が投げる例外を握りつぶさない。
    expect(() => buildRecognitionTimeline(["9i9a"])).toThrow();
  });

  it("解析できない表記の手でも例外がそのまま伝播する", () => {
    expect(() => buildRecognitionTimeline(["zzzz"])).toThrow();
  });

  it("空の shapes / intents を渡した場合は、変化が観測されず空になる", () => {
    expect(buildRecognitionTimeline(SHAPE_AND_INTENT, { shapes: [], intents: [] })).toEqual([]);
  });

  // 完了条件⑤(120手で実用的な時間に収まる)の記録。閾値による合否判定ではなく、
  // O(n^2)へ逆戻りしていないことを検出するための上限として広めに取る。
  it("120手の履歴でも実用的な時間で計算できる", () => {
    let sfen = DEFAULT_INITIAL_SFEN;
    const history: string[] = [];
    for (let i = 0; i < 120; i += 1) {
      const legal = getLegalMoves(sfen).slice().sort();
      if (legal.length === 0) break;
      const move = legal[(i * 7) % legal.length]!;
      sfen = applyMove(sfen, move);
      history.push(move);
    }
    expect(history.length).toBe(120);

    const started = performance.now();
    buildRecognitionTimeline(history);
    const elapsed = performance.now() - started;

    // 素直な実装(plyごとに履歴を再生し直す)は同条件で約2,000msかかっていた。
    expect(elapsed).toBeLessThan(500);
  });
});
