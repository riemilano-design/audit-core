// 居飛車(相手側)の序盤を一定の手順で強制進行させる、Phase 0時点での最小限の仕組み。
// docs/PHASES.md Phase 0成果物「AI側(居飛車)の序盤を一定の手順で強制進行させる仕組みの
// 最小実装(定跡を「大量に」用意する必要はなく、四間飛車vs居飛車が成立する最小限の手順で良い)」
// に対応する。
//
// 重要: これは docs/SCENARIOS.md で設計されている「対局シナリオ」(棒銀・早仕掛け等を選べる
// 仕組み)の実装ではない。CLAUDE.mdの「現段階でやらないこと」により対局シナリオの実装は
// Phase4以降まで着手しない。ここでの「一定の手順」は、居飛車の定義そのもの
// (data/openings/ibisha.json: 「飛車を初期位置から動かさない戦法」)を機械的に満たすための
// 決定的なルール(飛車を動かさない合法手を決まった優先順位で選ぶ)であり、
// 特定の定跡・作戦(棒銀等)を指させるものではない。将棋の定跡データや意図判定ロジックは
// Phase1でdata/intents・data/openingsのレビュー済みデータをもとに実装する。
//
// 序盤の一定手数(maxForcedPlies)を過ぎたら undefined を返す。呼び出し側はこの場合、
// 実際のエンジン(UsiEngine.go())にbestmoveを問い合わせて対局を最後まで進行させる想定。

import { parseSfen } from "shogiops/sfen";
import { isDrop, parseUsi } from "shogiops/util";
import { getLegalMoves } from "../rules/legalMoves.js";

export class InvalidSfenError extends Error {}

export const DEFAULT_MAX_FORCED_OPPONENT_PLIES = 6;

export interface PickForcedOpponentMoveOptions {
  maxForcedPlies?: number;
}

function parsePosition(sfen: string) {
  const parsed = parseSfen("standard", sfen);
  if (parsed.isErr) {
    throw new InvalidSfenError(
      `SFENの解析に失敗しました: "${sfen}" (${parsed.error?.message ?? "unknown error"})`,
    );
  }
  return parsed.value;
}

/**
 * 局面(SFEN)と、これまでに強制進行させた相手側(居飛車)の手数から、
 * 次に指すべき手をUSI形式で返す。
 *
 * - `forcedPliesSoFar` が `maxForcedPlies` 以上の場合、強制進行の対象外として `undefined` を返す。
 * - 飛車を動かさない合法手が存在しない場合も `undefined` を返す
 *   (例: 飛車を動かす以外に王手を回避できない局面。この場合は呼び出し側が
 *   エンジンに自由に指させることで、対局が不自然に止まらないようにする)。
 * - 飛車を動かさない合法手の中では、歩を一段進める手を優先し、
 *   USI表記の昇順(筋の若い順)で先頭のものを機械的に選ぶ
 *   (どの歩から進めるべきかという定跡上の判断はしていない)。
 */
export function pickForcedOpponentMove(
  sfen: string,
  forcedPliesSoFar: number,
  { maxForcedPlies = DEFAULT_MAX_FORCED_OPPONENT_PLIES }: PickForcedOpponentMoveOptions = {},
): string | undefined {
  if (forcedPliesSoFar >= maxForcedPlies) return undefined;

  const pos = parsePosition(sfen);
  const nonRookMoves = getLegalMoves(sfen).filter((usiMove) => {
    const md = parseUsi(usiMove);
    if (!md) return false;
    if (isDrop(md)) return md.role !== "rook";
    const piece = pos.board.get(md.from);
    return piece?.role !== "rook";
  });

  if (nonRookMoves.length === 0) return undefined;

  const pawnPushes = nonRookMoves.filter((usiMove) => {
    const md = parseUsi(usiMove);
    if (!md || isDrop(md)) return false;
    return pos.board.get(md.from)?.role === "pawn";
  });

  const candidates = pawnPushes.length > 0 ? pawnPushes : nonRookMoves;
  return [...candidates].sort()[0];
}
