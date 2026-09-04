// GameState -> HTTPレスポンス用オブジェクトの組み立て。
// server.tsから対局状態のレスポンス生成ロジックを切り出したもの(テスト容易性のため)。
// server.ts自体はHTTPサーバーの起動処理(server.listen/シグナルハンドラ登録)を
// importした時点で実行してしまうため、テストコードから直接importすると
// 実際にポート待受が発生する。この副作用を避けるため、レスポンス組み立てという
// テスト可能な部分のみをここに分離する(server.tsの既存の外部インターフェース・
// 挙動は変えていない)。

import {
  explainPositionWithStatus,
  type CoachExplanation,
  type ExplainPositionOptions,
} from "../analysis/explanationGenerator.js";
import { getStatus, type GameState, type GameStatus } from "../game/gameSession.js";

export interface StateResponseBody extends GameState {
  status: GameStatus;
  /**
   * Unit3(analysis/explanationGenerator.ts)による「現在の形・相手の意図・相手の次の狙い」の説明。
   * 説明生成の失敗時(想定外のデータ不整合等)はundefinedになる(対局自体は継続する)。
   */
  coach: CoachExplanation[] | undefined;
}

// 説明生成は対局の合法性判定とは独立した機能である。ここで万一例外が起きても
// (想定外のデータ不整合等)、対局そのもの(盤面・指し手)は止めない
// (docs/PHASES.md Phase1完了条件「無言・エラーにならない」を、コーチ機能自体の
// 障害からも守るための最後の防御線)。
export function safeExplainPosition(
  current: GameState,
  options: ExplainPositionOptions = {},
): CoachExplanation[] | undefined {
  try {
    return explainPositionWithStatus(current.sfen, current.moveHistory, options);
  } catch (err) {
    console.error("説明生成(analysis/explanationGenerator.ts)でエラーが発生しました:", err);
    return undefined;
  }
}

// options.initialSfenは実サーバー(server.ts)では常に既定値(標準初期局面)のまま使う
// (対局は常にstartposから始まるため)。テストコードが、実際の対局進行を経ずに
// 特定の局面を直接検証したい場合にのみ上書きする(analysis/intentDetector.tsの
// sfen/moveHistory整合性チェックを、任意の盤面に対しても有効なまま使うため)。
export function buildStateResponse(current: GameState, options: ExplainPositionOptions = {}): StateResponseBody {
  return { ...current, status: getStatus(current), coach: safeExplainPosition(current, options) };
}
