// 指し手履歴から「認識が変わった時点」の並びを再構成する(Phase 7 Unit 2)。
//
// 【このモジュールの責務】
// 各plyについて、その時点までの指し手だけから形(shapes)と狙い(intents)の認識状態を
// 求め、**前のplyから変化したものだけ**を時系列として返す。表示は一切行わない
// (表示は Unit 4「ここまでの対局で分かってきたこと」の責務。docs/ARCHITECTURE.md 5.)。
//
// 「変化した時点だけ」を返すのは、docs/ARCHITECTURE.md 5. が Unit 4 に許した4種の
// 1番目が「認識が変わった時点と、その根拠になった手」だからである。現在の認識そのものは
// 既存の analyzeShapeFormation / detectIntents から取れるため、ここでは二重に持たない。
//
// 【このモジュールが絶対にしないこと】
// - 新しい判定方式・閾値を作らない。段階の判定は既存の resolveStatus(形)と
//   evaluateIntent(狙い)をそのまま使う(docs/PHASES.md Phase 7 Unit 2)
// - 形の段階と狙いの段階を1つの尺度に統合しない。形は none/forming/completed、
//   狙いは none/forming/matched という**別々の尺度**のままにする
//   (2026-09-10 に人間が確定。docs/DATA_MODEL.md「②〜④は確定値ではなく『認識(仮説)』」)。
//   下の RecognitionTimelineEntry は kind による判別可能ユニオンにしてあり、
//   形に matched が、狙いに completed が入らないことを型で保証する
// - 狙いの検出範囲を広げない。detectIntentsFromEvents は従来どおり相手(gote)の手だけを見る
//   (data/intents/ は相手の作戦として作られたデータであるため。2026-09-10 の人間の判断)
// - エンジン・LLMに依存しない。決定的な純粋関数である
// - server.ts にモジュール変数を持たせない(状態を持たず、毎回履歴から再計算する)
//
// 【性能について】
// 各plyで analyzeShapeFormation / detectIntents をそのまま呼ぶと、そのたびに履歴を
// 頭から再生し直すためO(n^2)になる(120手で実測2,037ms)。本モジュールは履歴を
// **1回だけ**再生し、その events と中間局面(sfens)を各plyで使い回す。

import {
  analyzeShapeFormationFromEvents,
  type ShapeFormationResult,
} from "./shapeFormationAnalyzer.js";
import { detectIntentsFromEvents, type IntentMatchStatus } from "./intentDetector.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "./moveHistory.js";
import type { ShapeStatus } from "./shapeDetector.js";
import type { IntentDefinition } from "./intentRepository.js";
import type { ShapeDefinition } from "./shapeRepository.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";
export { IllegalMoveError, MoveHistoryError } from "./moveHistory.js";

/**
 * 認識が変わった時点1件。
 *
 * kind による判別可能ユニオンにしてあるため、形(shape)の段階に "matched" を、
 * 狙い(intent)の段階に "completed" を入れることは型の上でできない。
 * これは「2つの尺度を統合しない」という確定事項(docs/PHASES.md Phase 7 Unit 2)を
 * 実行時のテストだけでなく型でも守るためである。
 */
export type RecognitionTimelineEntry =
  | {
      /** 何手目を指した**後**の局面での変化か(1始まり) */
      ply: number;
      kind: "shape";
      /** data/shapes/*.json の id */
      targetId: string;
      /** その形がどちらの陣についてのものか(shapeDefinition.side をそのまま運ぶ) */
      side: ShapeDefinition["side"];
      from: ShapeStatus;
      to: ShapeStatus;
      /** 変化した時点の局面(ply手目を適用した後) */
      sfen: string;
      /** 変化の直前に指された手(=ply手目) */
      moveUsi: string;
    }
  | {
      ply: number;
      kind: "intent";
      /** data/intents/*.json の id */
      targetId: string;
      /**
       * 狙いは常に相手側である。detectIntents が相手(gote)の手だけを見る前提を
       * そのまま反映したもので、ここで検出範囲を広げてはいない。
       */
      side: "opponent";
      from: IntentMatchStatus;
      to: IntentMatchStatus;
      sfen: string;
      moveUsi: string;
    };

export interface BuildRecognitionTimelineOptions {
  shapes?: ShapeDefinition[];
  intents?: IntentDefinition[];
  /** 対局の初期局面。MVPでは常にstartposのため通常は指定不要(テスト用の差し替え口)。 */
  initialSfen?: string;
}

/** 1つのplyでの認識状態(形・狙いそれぞれ、id -> 段階)。 */
interface PlySnapshot {
  /** side は判定結果(ShapeDetectionResult.side)が持つ値をそのまま運ぶ。ここで推測しない。 */
  shapes: Map<string, { status: ShapeStatus; side: ShapeDefinition["side"] }>;
  intentStatuses: Map<string, IntentMatchStatus>;
}

function toSnapshot(
  shapeResults: ShapeFormationResult[],
  intentResults: { intentId: string; matchStatus: IntentMatchStatus }[],
): PlySnapshot {
  return {
    shapes: new Map(shapeResults.map((r) => [r.shapeId, { status: r.status, side: r.side }])),
    intentStatuses: new Map(intentResults.map((r) => [r.intentId, r.matchStatus])),
  };
}

/**
 * 指し手履歴から、認識が変わった時点の並びを再構成する。
 *
 * 【ply 0 の扱い】初期局面は「基準となる最初の観測」として使い、遷移としては出さない。
 * どの手も原因になっていないためで、仮に初期局面で既に none 以外の段階があっても
 * (現在のdata/では起こらないが)それを「変化した」とは述べない。この結果、
 * 返り値の from も moveUsi も必ず値を持つ(null にならない)。
 *
 * 【並び順】ply の昇順。同じ ply 内では、形 → 狙い の順、それぞれ id の昇順で、
 * 決定的に並ぶ。どちらが重要かという判断ではなく、順序を一意にするためだけの規則。
 *
 * 【例外】非合法手・解析できない手を含む履歴では、既存の replayMoveHistory が投げる
 * IllegalMoveError / MoveHistoryError / InvalidSfenError がそのまま伝播する
 * (ここで握りつぶさない。呼び出し側の責務)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 */
export function buildRecognitionTimeline(
  moveHistory: string[],
  options: BuildRecognitionTimelineOptions = {},
): RecognitionTimelineEntry[] {
  const initialSfen = options.initialSfen ?? DEFAULT_INITIAL_SFEN;

  // 履歴の再生は1回だけ。各plyの判定はここで得た events と sfens を使い回す。
  const { events, sfens } = replayMoveHistory(moveHistory, initialSfen);

  const snapshotAt = (ply: number): PlySnapshot => {
    // ply手目までのイベントと、それに対応する局面を必ず組で渡す
    // (*FromEvents は整合を検証しないため、組を崩さないのは呼び出し側=ここの責務)。
    const prefixEvents = events.slice(0, ply);
    const sfen = sfens[ply]!;
    return toSnapshot(
      analyzeShapeFormationFromEvents(sfen, prefixEvents, { shapes: options.shapes }),
      detectIntentsFromEvents(prefixEvents, { intents: options.intents }),
    );
  };

  const entries: RecognitionTimelineEntry[] = [];
  let previous = snapshotAt(0);

  for (let ply = 1; ply <= moveHistory.length; ply += 1) {
    const current = snapshotAt(ply);
    const sfen = sfens[ply]!;
    const moveUsi = moveHistory[ply - 1]!;

    for (const [shapeId, entry] of [...current.shapes].sort((a, b) => a[0].localeCompare(b[0]))) {
      const from = previous.shapes.get(shapeId)?.status;
      if (from === undefined || from === entry.status) continue;
      entries.push({
        ply,
        kind: "shape",
        targetId: shapeId,
        side: entry.side,
        from,
        to: entry.status,
        sfen,
        moveUsi,
      });
    }

    for (const [intentId, to] of [...current.intentStatuses].sort((a, b) => a[0].localeCompare(b[0]))) {
      const from = previous.intentStatuses.get(intentId);
      if (from === undefined || from === to) continue;
      entries.push({ ply, kind: "intent", targetId: intentId, side: "opponent", from, to, sfen, moveUsi });
    }

    previous = current;
  }

  return entries;
}
