// STEP D0-SIDE 段 1(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の R-8・Q-9)。replay.ts が再生する手順を決める純粋関数。
//
// replay.ts は手を 2 手ずつ(先手 = playHumanMove、後手 = 固定の応手)読むので、手数が奇数の棋譜は最後の組で
// odd_move_count に当たり、最後の組を欠いた記録と error 行を残して止まる(計画 E-1)。
// **負け方の診断に最後の 1 手は要らない**ので、手数が奇数なら最後の先手の手を落として再生し、落としたことを meta に残す
// (司令塔の決定、2026-09-15)。落としたことは記録の meta から辿れる。
//
// 【meta の形(司令塔の決定、2026-09-15。null は使わない)】
// - `trailingMoveTruncated: boolean` を**常に**書く(落とした = true、落とさない = false)
// - `truncatedTrailingMove: string`(落とした手の USI)は **true のときだけ**書く(false のときは欄そのものを書かない)
// - 古い記録(R-8 より前)は、`trailingMoveTruncated` の欄が無いことで見分ける
//
// 【このファイルがやること】
// - 手数が奇数なら最後の 1 手を落とす。偶数なら何も落とさない
// - 落とした後に再生する手が 0 手なら、再生しない印(`no_moves_to_replay`)を返す(黙って捨てない。Q-9)
//
// 【このファイルが絶対にやらないこと】
// - 最初の手や途中の手を落とすこと。偶数の手順を変えること
// - 局面を読むこと(合法かどうかは replay.ts の playHumanMove / playOpponentMove が確かめる)
//
// 【限界(計画 3.1)】落とした手が本人の詰ませた手だった局は、Event の行では「窓が足りない」に見える
// (actualContinuation の windowShort。元の棋譜では終局した局面が、落とした記録では終局していない)。
// 段 2(回した局で 1 手目を開始局面に畳む)を足すときは、**畳んだ後の手順**をこの関数に渡す(畳む → 落とす の順)。

/** 最後の手を落としたかどうか。落としたときだけ、落とした手(USI)を持つ。 */
export type TrailingTruncation = { trailingMoveTruncated: true; truncatedTrailingMove: string } | { trailingMoveTruncated: false };

/** 再生する手順と、最後の手を落としたかどうか。 */
export type ReplayPlan =
  | ({ kind: "replay"; moves: string[] } & TrailingTruncation)
  | ({ kind: "noMovesToReplay"; reason: "no_moves_to_replay" } & TrailingTruncation);

export function planReplayMoves(moves: readonly string[]): ReplayPlan {
  const truncation: TrailingTruncation =
    moves.length % 2 === 1 ? { trailingMoveTruncated: true, truncatedTrailingMove: moves[moves.length - 1]! } : { trailingMoveTruncated: false };
  const replayMoves = truncation.trailingMoveTruncated ? moves.slice(0, -1) : [...moves];
  if (replayMoves.length === 0) return { kind: "noMovesToReplay", reason: "no_moves_to_replay", ...truncation };
  return { kind: "replay", moves: replayMoves, ...truncation };
}

/**
 * meta の extra に書く欄だけを取り出す。**落とさなかったときは `truncatedTrailingMove` の欄そのものを持たない**
 * (undefined を入れた欄も作らない。null も使わない)。
 */
export function truncationMetaFields(truncation: TrailingTruncation): TrailingTruncation {
  return truncation.trailingMoveTruncated
    ? { trailingMoveTruncated: true, truncatedTrailingMove: truncation.truncatedTrailingMove }
    : { trailingMoveTruncated: false };
}
