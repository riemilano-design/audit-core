// 検証用: Unit1〜5で実装したIntent判定(相手の意図のリアルタイム通訳)が、
// 実際の対局中に発火する場面を人間が確認できるようにするための、
// 最小限の「検証用対局シナリオ」。
//
// 重要な位置づけ: これはdocs/SCENARIOS.mdが将来設計する本格的な「対局シナリオ」機能
// (将来、data/openings/*.jsonのscenarioフィールドを使う想定のもの)の
// 先取り実装ではない。docs/SCENARIOS.mdが強調する「認識(recognition)データと
// 制御(control)データを混同しない」という方針に従い、本ファイルの指し手列は
// data/へは一切書き込まず、コード内の検証専用定数として完全に閉じている
// (本格実装が必要になった場合は、改めて別途設計する。Phase 4 では見送りと判断済み)。
//
// スクリプトの中身(相手がどう指すか)は、data/intents/boh_gin.json /
// hayajikake.jsonのrecognition_pattern(既存データ、変更していない)が要求する
// 移動先マスへ、実際に合法に到達できる手順として構成したもの
// (apps/server/src/analysis/intentDetector.test.ts 等のテストで使ったものと同一)。
// 新しい将棋知識を作っているのではなく、既存データが既に要求している内容を
// 満たすための機械的な経路(歩を退避させてから銀を通す、等)にすぎない。
//
// forcedOpponentOpening.tsと同じく、合法性チェック(legalMoves.ts)への照会のみ行い、
// 局面への適用はgameSession.ts側(applyMove.ts)に委ねる。

import { isLegalMove } from "../rules/legalMoves.js";

export type ScenarioId = "boh_gin" | "hayajikake";

export function isScenarioId(value: unknown): value is ScenarioId {
  return value === "boh_gin" || value === "hayajikake";
}

/**
 * `?scenario=`(検証用の対局シナリオ指定)を有効にするかどうかを、環境変数から
 * 純粋関数として判定する。engine/enginePath.tsのSHOGI_ENGINE_PATHと同じ
 * 「未設定なら既定の(=無効化された)挙動」という書き方に合わせる。
 * STEP ζ-4c-1(C-5): `?scenario=`は開発モード限定とする。
 */
export function isDevScenarioEnabled(env: NodeJS.ProcessEnv = process.env): boolean {
  return Boolean(env.SHOGI_DEV_SCENARIO);
}

// data/intents/boh_gin.json の recognition_pattern(銀 7c→7d→7e)へ実際に到達する手順。
// 銀が通る前に、同じ筋の歩(7c/7d/7e)を1マスずつ先に退避させる必要がある
// (7c/7dは初期配置で歩に占有されているため)。
const BOH_GIN_SCRIPT = ["7c7d", "7a7b", "7b7c", "7d7e", "7c7d", "7e7f", "7d7e"];

// data/intents/hayajikake.json の recognition_pattern(歩 6d→6e)へそのまま到達する手順。
const HAYAJIKAKE_SCRIPT = ["6c6d", "6d6e"];

const SCENARIO_SCRIPTS: Record<ScenarioId, readonly string[]> = {
  boh_gin: BOH_GIN_SCRIPT,
  hayajikake: HAYAJIKAKE_SCRIPT,
};

/**
 * 検証用シナリオの、stepIndex番目(0始まり)の相手の手を返す。
 * - シナリオの手を使い切った場合はundefined(呼び出し側は通常のエンジンにフォールバックする)
 * - 人間側の手によって局面が変わり、予定していた手が非合法になった場合もundefined
 *   (forcedOpponentOpening.tsと同じフォールバック方針。無理に局面を歪めない)
 */
export function pickScenarioMove(sfen: string, stepIndex: number, scenario: ScenarioId): string | undefined {
  const script = SCENARIO_SCRIPTS[scenario];
  const moveUsi = script[stepIndex];
  if (moveUsi === undefined) return undefined;
  if (!isLegalMove(sfen, moveUsi)) return undefined;
  return moveUsi;
}
