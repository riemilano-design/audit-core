// 元はSTEP T-7(A-1、docs/STEP_T-7_PLAN_2026-09-11.md 2. A.)でハーネス専用の
// 関数として実装された(scripts/playtest/lib/engineReference.ts)。
// STEP 5-F(docs/STEP_5-F_PLAN_2026-09-12.md 4. A-1)で、本番の③(何が重要か)を
// 作るために本番側(apps/server/src/analysis/)へ移設した(算法を二重に持たない
// ため。2026-09-12人間の確認)。移設時点では関数のシグネチャ・返り値の形・
// 計算の中身は変えていない(A-1)。その後A-2b(9.3)で、measureEngineReferenceの
// 第3引数(nodes)を必須からoptionalへ変えた(本番はmovetime既定で呼ぶため。
// 「nodesで固定しない」という人間決定に従う)。EngineReferenceの返り値の形
// (nodesフィールドの存在)は変えていない。nodesの型はnumber|nullへ広げた
// (movetimeのときは「ノード数で制限していない」を表すnull。0にしない)。
// 本番関数(rules/gameStatus.ts の isGameOver/isInCheck、rules/sfenPosition.ts の
// parsePosition)は import して呼ぶだけで、複製・改変はしない。
// 将棋の判断(良し悪し)・新しい閾値はここでは一切行わない。
//
// 【このモジュールの位置づけについて】
// 本番の③(STEP 5-F)で使うために移設した。閾値・表示の判断はこのモジュールでは
// 行わない(そちらはSTEP 5-Fの他のファイルの管轄)。
// 本番側の別の閾値(analysis/candidateMoveReferenceFilter.tsの300cp)とは無関係。
// ハーネス側では、I-7(draft、scripts/playtest/invariants/i7-urgent-but-other-talk.ts)
// の判定材料としても引き続き使われる(nodesを指定して呼ぶため、挙動は変わらない)。

import { parseSquareName } from "shogiops/util";
import { isGameOver, isInCheck } from "../rules/gameStatus.js";
import { parsePosition } from "../rules/sfenPosition.js";
import type { LowPriorityEngine } from "../engine/prioritizedEngine.js";
import type { GoOptions, MultiPvGoResult } from "../engine/usiEngine.js";

/** USI形式の指し手(ドロップではない)から移動先マスを取り出す(成り"+"は無視)。
 * scripts/playtest/lib/players.tsのtoSquareOfと同じ実装(移設に伴い、共有
 * exportを新設せずこのモジュール内のprivateヘルパーとして複製した)。 */
function toSquareOf(moveUsi: string): string {
  return moveUsi.slice(2, 4);
}

/** MultiPV1本(先頭)を読んだ結果。score が cp/mate のどちらかしか立たない
 * (両方とも無ければ欠測=null)。 */
export interface EngineReferenceSide {
  scoreCp: number | null;
  mate: number | null;
  bestmove: string | null;
}

export interface EngineReferenceAfterPass extends EngineReferenceSide {
  /** afterPass.bestmove の移動先に先手の駒があるマス(USI形式)。無ければnull。 */
  captureSquare: string | null;
}

export interface EngineReference {
  /** 現局面(先手番)をMultiPV1で読んだ結果(先手視点)。 */
  baseline: EngineReferenceSide;
  /** 手番を入れ替えた局面(先手がパスしたのと同じ盤面)をMultiPV1で読んだ結果
   * (後手視点)。 */
  afterPass: EngineReferenceAfterPass;
  /** baseline.scoreCp − (−afterPass.scoreCp)(先手視点の落ち幅)。両方cpの
   * ときだけ算出し、それ以外(mateが絡む・いずれかが欠測)はnull。 */
  dropCp: number | null;
  /**
   * 実際に使ったノード数(呼び出し時の引数のコピー。観測記録用)。
   * **nodesを指定せずmovetimeで探索した場合はnull**(「ノード数で制限していない」の意味)。
   * 0にしない ― 0は「0ノード探索した」と読めてしまい、後から読んだ人が測定値として
   * 誤読しうるため(2026-09-12 人間の指示。同日、CPU 0%を「止まっている」と読み違えて
   * 再現確認を124回空費した件と同じ型の取り違えを避ける)。
   * ハーネス(scripts/playtest)は常にnodesを渡すため、記録の値は従来どおり。
   */
  nodes: number | null;
}

/** SFENの手番フィールド(空白区切りの2番目、"b"または"w")を入れ替えた
 * SFENを返す。文字列操作のみ(将棋の判断はしない)。 */
export function passSfen(sfen: string): string {
  const parts = sfen.split(" ");
  const turn = parts[1];
  if (turn === "b") parts[1] = "w";
  else if (turn === "w") parts[1] = "b";
  return parts.join(" ");
}

/** moveUsi(nullなら常にnull)の移動先(toSquareOf)に、sfenの局面で先手の駒が
 * あればそのマス(USI形式)、無ければnullを返す。捕獲判定の純粋部分だけを
 * 切り出したもの(盤の読み取りはparsePositionへ委ねるだけ)。 */
export function captureSquareOf(sfen: string, moveUsi: string | null): string | null {
  if (moveUsi === null) return null;
  const squareName = toSquareOf(moveUsi);
  const square = parseSquareName(squareName);
  if (square === undefined) return null;
  const piece = parsePosition(sfen).board.get(square);
  if (!piece) return null;
  return piece.color === "sente" ? squareName : null;
}

function sideFromMultiPv(result: MultiPvGoResult): EngineReferenceSide {
  const top = result.lines[0];
  const score = top?.score;
  return {
    scoreCp: score?.type === "cp" ? score.value : null,
    mate: score?.type === "mate" ? score.value : null,
    bestmove: result.bestmove ?? null,
  };
}

/**
 * sfen(先手番の局面)について、(1) 現局面をMultiPV1で読んだ結果
 * (baseline、先手視点)、(2) 手番を入れ替えた局面(passSfen)を同条件で読んだ結果
 * (afterPass、後手視点)、(3) afterPass.bestmoveの移動先に先手の駒があるか
 * (captureSquare)、(4) 両方cpのときのdropCpを組み立てて返す。
 *
 * 測らない場合(null を返す): 終局(isGameOver)、先手が王手中
 * (isInCheck(sfen, "sente")。パスが成立しない)、エンジンの例外・タイムアウト
 * (try/catchで握りつぶす。原因を推測しない)。
 *
 * 【探索条件について(STEP 5-F 9.3、人間決定)】
 * nodesを省略した場合はgo movetime(engine.goMultiPvの既定、2000ms)で探索する。
 * これが本番(analysis/pieceThreatFocusExplanation.tsが使う③)の呼び方であり、
 * 「nodesで固定しない」という人間決定に従う。nodesを指定した場合は`go nodes N`で
 * 固定する(ハーネス、scripts/playtest/lib/recorder.tsのreferenceEngineが使う。
 * 回帰用の再現性のため既存どおりnodesを渡す)。
 */
export async function measureEngineReference(
  sfen: string,
  engine: LowPriorityEngine,
  nodes?: number,
): Promise<EngineReference | null> {
  try {
    if (isGameOver(sfen)) return null;
    if (isInCheck(sfen, "sente")) return null;

    const goOptions: GoOptions = nodes !== undefined ? { nodes } : {};

    engine.setMultiPv(1);
    engine.position(sfen);
    const baseline = sideFromMultiPv(await engine.goMultiPv(goOptions));

    const passedSfen = passSfen(sfen);
    engine.setMultiPv(1);
    engine.position(passedSfen);
    const afterPassSide = sideFromMultiPv(await engine.goMultiPv(goOptions));

    const captureSquare = captureSquareOf(sfen, afterPassSide.bestmove);
    const dropCp =
      baseline.scoreCp !== null && afterPassSide.scoreCp !== null
        ? baseline.scoreCp - -afterPassSide.scoreCp
        : null;

    return {
      baseline,
      afterPass: { ...afterPassSide, captureSquare },
      dropCp,
      // nodesを省略した場合(movetime探索)はnull =「ノード数で制限していない」。
      // 0にしない(型定義のコメント参照。2026-09-12 人間の指示)。
      nodes: nodes ?? null,
    };
  } catch {
    return null;
  }
}
