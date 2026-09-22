// STEP D0-SIDE 段 2(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の 3. 案 1・R-1〜R-4・Q-7)。本人が後手の棋譜を、本人が先手の形にそろえる。
//
// 【そろえ方(案 1。司令塔の決定)】
// - 手順をすべて 180 度回す(lib/usiRotation.ts)。回した 1 手目は元の相手(先手)の 1 手目で、後手の駒の手になる
// - その 1 手目を**平手・後手番の初期局面**に当てた局面を `startSfen`(先手番)にし、`moves` は 2 手目から(**畳む**)
// - 本人の手が 1, 3, 5, … 手目(先手の手)に来る。元の手数との対応は `plyOffset: 1`(元の ply = 回した ply + 1)
// - **`startSfen` は手で書かず、`applyMove` の出力をそのまま使う**(`detectIntents` などは手数の欄まで文字列で比べるため。F-S8)
// - 手数が奇数なら最後の手を落とすのは replay.ts(lib/replayPlan.ts)。**畳む → 落とす の順**で、奇数かどうかは畳んだ後の手数で決まる
//
// 【記録の形(司令塔の決定、2026-09-15。null は使わない)】
// - `mirrored: boolean` を**常に**書く
// - `startSfen`・`plyOffset`・`originalUserSide` は **mirrored が true のときだけ**書く(false では欄そのものを書かない)
// - 古い記録(D0-SIDE 段 2 より前)は `mirrored` の欄が無いことで見分ける。**開始局面は平手として読む**(その頃は平手からしか再生していない)
//
// 【このファイルが絶対にやらないこと】
// - 本人の側を決めること(lib/userSide.ts)。後手視点の文言に変えること(本番の「自分 = 先手固定」は変えない。計画 8.)
// - 形の食い違う固定棋譜・meta を黙って平手として読むこと(例外を投げる)

import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import type { MetaLine } from "../invariants/types.js";
import type { FixedKifuEnding } from "./kifuImport.js";
import { rotateUsiMove } from "./usiRotation.js";
import type { UserSide } from "./userSide.js";

/** 平手・後手番の初期局面(手番の欄だけを w にした平手の初期局面)。回した 1 手目を当てる局面。 */
export const GOTE_TO_MOVE_INITIAL_SFEN = (() => {
  const fields = DEFAULT_INITIAL_SFEN.split(" ");
  fields[1] = "w";
  return fields.join(" ");
})();

export type SideAlignment =
  | { mirrored: false }
  | { mirrored: true; originalUserSide: "gote"; plyOffset: 1; startSfen: string };

export class InvalidSideAlignmentError extends Error {}

/**
 * 本人の側に合わせて手順をそろえる。本人が先手なら何も変えない。後手なら回して 1 手目を開始局面に畳む。
 * **元が 1 手の後手の局は、畳んだ後の手順が 0 手になる**(再生しない判定は replay.ts。Q-9 の (c))。
 */
export function alignMovesToSente(moves: readonly string[], userSide: UserSide): { alignment: SideAlignment; moves: string[] } {
  if (userSide === "sente") return { alignment: { mirrored: false }, moves: [...moves] };
  if (moves.length === 0) throw new InvalidSideAlignmentError("手順が 0 手の棋譜は、畳む 1 手目が無いのでそろえられません");
  const rotated = moves.map(rotateUsiMove);
  const startSfen = applyMove(GOTE_TO_MOVE_INITIAL_SFEN, rotated[0]!);
  return { alignment: { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen }, moves: rotated.slice(1) };
}

const MIRRORED_ONLY_FIELDS = ["originalUserSide", "plyOffset", "startSfen", "originalMoves"] as const;

/** 固定棋譜のそろえの欄を読んだ結果。`sideAlignmentChecked` は、回した局の欄を `originalMoves` から作り直して照合したか(司令塔の決定、2026-09-15) */
export interface SideAlignmentRead {
  alignment: SideAlignment;
  sideAlignmentChecked: boolean;
}

const isMoveList = (value: unknown): value is string[] => Array.isArray(value) && value.every((move) => typeof move === "string");

/**
 * 固定棋譜 JSON のそろえの欄を読む(replay.ts)。**欄の形が決まりと食い違えば例外を投げる**(黙って平手として読まない):
 * - `mirrored` が無い・`false` … 先手の局。`startSfen`・`plyOffset`・`originalUserSide`・`originalMoves` があってはならない。`sideAlignmentChecked: false`
 * - `mirrored` が `true` … `originalUserSide: "gote"`・`plyOffset: 1`・空でない `startSfen` がすべて要る
 *   - **`originalMoves` があれば、`alignMovesToSente(originalMoves, "gote")` で `startSfen`・`moves`・`plyOffset` を作り直し、書かれている値と一致することを確かめる**
 *     (食い違えば例外。手で直した JSON で startSfen だけが古いと、黙って別の局面から再生するため。監査 A の指摘、司令塔の決定)。`sideAlignmentChecked: true`
 *   - `originalMoves` が無ければ照合しない(必須にはしない。司令塔の決定)。`sideAlignmentChecked: false` で、**照合せずに通したことが記録に残る**
 */
export function readSideAlignment(kifu: Readonly<Record<string, unknown>>): SideAlignmentRead {
  if (kifu.mirrored === true) {
    const { originalUserSide, plyOffset, startSfen } = kifu;
    if (originalUserSide !== "gote" || plyOffset !== 1 || typeof startSfen !== "string" || startSfen.length === 0) {
      throw new InvalidSideAlignmentError(
        `mirrored が true の棋譜には originalUserSide: "gote"・plyOffset: 1・startSfen が要ります(originalUserSide: ${JSON.stringify(originalUserSide)}, plyOffset: ${JSON.stringify(plyOffset)}, startSfen: ${JSON.stringify(startSfen)})`,
      );
    }
    const alignment: SideAlignment = { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen };
    if (!Object.hasOwn(kifu, "originalMoves")) return { alignment, sideAlignmentChecked: false };

    const { originalMoves, moves } = kifu;
    if (!isMoveList(originalMoves) || originalMoves.length === 0 || !isMoveList(moves)) {
      throw new InvalidSideAlignmentError("mirrored が true の棋譜の originalMoves・moves は手(文字列)の配列です(originalMoves は 1 手以上)");
    }
    let rebuilt: ReturnType<typeof alignMovesToSente>;
    try {
      rebuilt = alignMovesToSente(originalMoves, "gote");
    } catch (error) {
      throw new InvalidSideAlignmentError(`originalMoves を回して畳み直せません: ${error instanceof Error ? error.message : String(error)}`);
    }
    if (!rebuilt.alignment.mirrored) throw new InvalidSideAlignmentError("originalMoves を回して畳み直した結果が、回した形になっていません");
    const mismatched = [
      ...(rebuilt.alignment.startSfen === startSfen ? [] : ["startSfen"]),
      ...(rebuilt.alignment.plyOffset === plyOffset ? [] : ["plyOffset"]),
      ...(rebuilt.moves.length === moves.length && rebuilt.moves.every((move, index) => move === moves[index]) ? [] : ["moves"]),
    ];
    if (mismatched.length > 0) {
      throw new InvalidSideAlignmentError(`mirrored が true の棋譜の ${mismatched.join("・")} が、originalMoves を回して畳み直した値と一致しません`);
    }
    return { alignment, sideAlignmentChecked: true };
  }
  if (Object.hasOwn(kifu, "mirrored") && kifu.mirrored !== false) {
    throw new InvalidSideAlignmentError(`mirrored は true か false です(${JSON.stringify(kifu.mirrored)})`);
  }
  const stray = MIRRORED_ONLY_FIELDS.filter((field) => Object.hasOwn(kifu, field));
  if (stray.length > 0) throw new InvalidSideAlignmentError(`mirrored が true でない棋譜に ${stray.join("・")} があります`);
  return { alignment: { mirrored: false }, sideAlignmentChecked: false };
}

/**
 * meta の extra に書く欄だけを取り出す。**mirrored が false のときは `startSfen`・`plyOffset`・`originalUserSide` の欄そのものを持たない**
 * (undefined を入れた欄も作らない。null も使わない)。
 */
export function sideMetaFields(alignment: SideAlignment): SideAlignment {
  return alignment.mirrored
    ? { mirrored: true, originalUserSide: alignment.originalUserSide, plyOffset: alignment.plyOffset, startSfen: alignment.startSfen }
    : { mirrored: false };
}

/**
 * 記録を読み直す解析(R-5〜R-7)に渡す開始局面。**3 つに分けて読む**(`?? DEFAULT` と書かない):
 * - `meta.mirrored === true` … `meta.startSfen`(無ければ例外。形の食い違う記録を平手として読まない)
 * - `meta.mirrored === false` … 平手(先手の局)
 * - 欄が無い(D0-SIDE 段 2 より前の記録)・meta が無い … 平手(その頃は平手からしか再生していない)
 */
export function initialSfenOf(meta: Pick<MetaLine, "mirrored" | "startSfen"> | undefined): string {
  if (meta?.mirrored === true) {
    if (typeof meta.startSfen !== "string" || meta.startSfen.length === 0) {
      throw new InvalidSideAlignmentError("meta の mirrored が true なのに startSfen がありません");
    }
    return meta.startSfen;
  }
  return DEFAULT_INITIAL_SFEN;
}

/**
 * 固定棋譜 JSON(kifu-import-check.ts の --fixed)を、本人の側に合わせてそろえた形にする。
 * - 本人が先手 … `mirrored: false` を書き、手順はそのまま
 * - 本人が後手 … `mirrored: true`・`originalUserSide`・`plyOffset`・`startSfen` を書き、`moves` は回して畳んだ手順、
 *   **回す前の手順を `originalMoves` に残す**(戻す計算を報告の根拠にしない。計画 Q-4)
 * STEP D0-KIFU3: 入力に `ending` のキーがあれば同じ値を moves の直前に写し、無ければ出さない(キーが無い = 終局の行を見ていない)。
 * STEP TIME: 入力に `moveSeconds` のキーがあれば**そのまま**(回さず・詰めず)写す。`moveSeconds` は元の手順の順のまま
 *   (`originalMoves` と同じ並び)なので、ここで手を加える必要が無い(欄が無ければ出さない)。
 * **本人の名前は書かない**(ヘッダの値は kifu-import-check.ts の標準出力にだけ出す)。
 */
export function alignedFixedKifu(
  fixed: {
    id: string;
    source: string;
    ending?: FixedKifuEnding | null;
    moves: readonly string[];
    moveSeconds?: ReadonlyArray<{ spentSec: number; totalSec: number } | null>;
  },
  userSide: UserSide,
): Record<string, unknown> {
  const { alignment, moves } = alignMovesToSente(fixed.moves, userSide);
  const ending = Object.hasOwn(fixed, "ending") ? { ending: fixed.ending } : {};
  const moveSeconds = Object.hasOwn(fixed, "moveSeconds") ? { moveSeconds: fixed.moveSeconds } : {};
  if (!alignment.mirrored) return { id: fixed.id, source: fixed.source, mirrored: false, ...ending, ...moveSeconds, moves };
  return { id: fixed.id, source: fixed.source, ...sideMetaFields(alignment), ...ending, ...moveSeconds, moves, originalMoves: [...fixed.moves] };
}
