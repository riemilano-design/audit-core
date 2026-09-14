// STEP T-3。docs/PLAYTEST_LOOP_PROPOSAL.md 4.2、STEP T-3計画書「対局者(自分側)の
// 5プロファイル」(人間承認済み)に定めた規則をそのまま実装する。
//
// 台本はテストの入力であり、ユーザーに見せる知識でも本番の判断でもない。
// 規則はすべて「画面(APIレスポンス)に出ている情報」とrules/(合法手・利きの事実)
// だけで決まる。将棋の良し悪しを判断する規則はここには置かない。同じ局面・
// 同じ乱数状態なら同じ手を返す(決定的)。
//
// 本番関数(apps/server/src配下)はimportして呼ぶだけで、複製・改変はしない。
//
// STEP D3: プロファイル B・B2(縛った初心者の決め方)は lib/beginnerProfile.ts にあり、ここからは薄く呼ぶだけ
// (engine も応答も渡さない。docs/STEP_D3_PLAN_2026-09-14.md 8.4 の決定 12・13)。

import type { StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import type { HighPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { listAttackedPieces } from "../../../apps/server/src/rules/attackedPieces.js";
import { getLegalMoves, isLegalMove } from "../../../apps/server/src/rules/legalMoves.js";
import { detectPieceThreats } from "../../../apps/server/src/analysis/pieceThreatDetector.js";
import { pickByBeginnerProfile, type BeginnerTier } from "./beginnerProfile.js";
import type { Prng } from "./prng.js";

export type PlayerProfileId = "S1" | "S2" | "S3" | "E" | "R" | "B" | "B2";

/** --profile に渡せる値(STEP D3 で B・B2 を足した)。 */
export const PLAYER_PROFILE_IDS: readonly PlayerProfileId[] = ["S1", "S2", "S3", "E", "R", "B", "B2"];

/** 10局の既定の内訳(計画書表): S1×2、S2×2、S3×2、E×2、R×2。 */
export const DEFAULT_PROFILE_ORDER: readonly PlayerProfileId[] = [
  "S1",
  "S1",
  "S2",
  "S2",
  "S3",
  "S3",
  "E",
  "E",
  "R",
  "R",
];

/**
 * STEP D3(計画 Q-1・F-B13)。explore.ts の --profile を読む。無ければ undefined(既定の並び)。
 * **値が分からないとき・値が無いときはエラーで止める**(黙って既定の並びにしない。計画 8.3 の 2)。
 */
export function parseProfileOption(argv: readonly string[]): PlayerProfileId | undefined {
  const index = argv.indexOf("--profile");
  if (index === -1) return undefined;
  const value = argv[index + 1];
  const found = PLAYER_PROFILE_IDS.find((id) => id === value);
  if (found === undefined) {
    throw new Error(`--profile の値が分からない: ${value === undefined ? "(値が無い)" : `"${value}"`}(使えるのは ${PLAYER_PROFILE_IDS.join(" / ")})`);
  }
  return found;
}

/** 何局目をどのプロファイルで指すか。--profile があれば全局それ、無ければ既定の10局構成を繰り返す(F-B13)。 */
export function profileForGame(gameIndex1Based: number, fixedProfile: PlayerProfileId | undefined): PlayerProfileId {
  if (fixedProfile !== undefined) return fixedProfile;
  const order = DEFAULT_PROFILE_ORDER;
  const zeroBased = (gameIndex1Based - 1) % order.length;
  // order.length > 0 であることは定数配列から自明。
  return order[zeroBased] as PlayerProfileId;
}

/** R(乱択混合)の既定のrandomRate(人間承認済み)。S1〜S3・Eは0。 */
export const DEFAULT_RANDOM_RATE = 0.3;

/** S3(振り飛車定型)が消費する定型序盤列(人間承認済み。ランク別検証の共通序盤)。 */
export const S3_SCRIPT: readonly string[] = [
  "7g7f",
  "6g6f",
  "2h6h",
  "5i4h",
  "4h3h",
  "3h2h",
  "3i3h",
  "6i5h",
];

/**
 * S1「文どおり」ルール①②。
 * ① candidateMove.status === "ready" なら explanations[0].move。
 * ② そうでなく plan.candidateMoveLabels に手があれば、その最初のUSI
 *   (Object.keysの順。routePlanner.tsの決定的な生成順に由来する。除外されても
 *   道のりの一手を指す = C-1の初心者)。
 * どちらも成り立たなければ undefined を返す(呼び出し側で③=浅い読みへ
 * フォールバックする)。
 */
export function pickByS1Rule(response: StateResponseBodyWithPlan): string | undefined {
  const { plan } = response;
  const candidateMove = plan.candidateMove;
  if (candidateMove?.status === "ready") {
    const first = candidateMove.explanations[0];
    if (first?.move) return first.move;
  }
  const firstLabelMove = Object.keys(plan.candidateMoveLabels)[0];
  if (firstLabelMove !== undefined) return firstLabelMove;
  return undefined;
}

/** USI形式の指し手(ドロップではない)から移動元マスを取り出す。
 * STEP T-8(I-8)がinvariants/i8-band-piece-then-captured.tsと共用するためexportした
 * (実装は変えていない。exportを足しただけ)。 */
export function fromSquareOf(moveUsi: string): string {
  return moveUsi.slice(0, 2);
}

/** USI形式の指し手(ドロップではない)から移動先マスを取り出す(成り"+"は無視)。
 * STEP T-6(B-3)がinvariants/i6-advice-then-loss.tsと共用するためexportした
 * (実装は変えていない)。 */
export function toSquareOf(moveUsi: string): string {
  return moveUsi.slice(2, 4);
}

/**
 * S2「逃げる」ルール①。
 * plan.urgentMessages に kind: "piece_attacked" が無ければ undefined を返す
 * (呼び出し側で②=S1ルールへフォールバックする)。
 * あれば、detectPieceThreats(listAttackedPieces(sfen,"sente")) の先頭の駒について、
 * その駒の合法手のうち、移動先に相手の利きが無い手(applyMove後の局面で
 * listAttackedPieces にその移動先が現れない)を getLegalMoves の順で最初の1つ返す。
 * 該当が無ければ undefined を返す(呼び出し側で②へフォールバックする)。
 */
export function pickByS2Rule(sfen: string, response: StateResponseBodyWithPlan): string | undefined {
  const hasPieceAttacked = response.plan.urgentMessages.some((m) => m.kind === "piece_attacked");
  if (!hasPieceAttacked) return undefined;

  const threats = detectPieceThreats(listAttackedPieces(sfen, "sente"));
  const target = threats[0];
  if (!target) return undefined;

  const candidateMoves = getLegalMoves(sfen).filter((move) => fromSquareOf(move) === target.square);
  for (const move of candidateMoves) {
    const destination = toSquareOf(move);
    const nextSfen = applyMove(sfen, move);
    const stillAttacked = listAttackedPieces(nextSfen, "sente").some((p) => p.square === destination);
    if (!stillAttacked) return move;
  }
  return undefined;
}

/** pickByS3Ruleの戻り値(次に消費するcursorを含む)。 */
export interface S3PickResult {
  move: string;
  nextCursor: number;
}

/**
 * S3「振り飛車定型」ルール①。cursorから順にS3_SCRIPTを走査し、現局面で合法な
 * 最初の1手を返す(非合法な手は消費せず読み飛ばす。cursor自体はその手の次から
 * 再開できるよう、見つかった手の直後まで進める)。使い切った(=末尾まで合法な手が
 * 無い)場合は undefined を返す(呼び出し側で②=S1ルールへフォールバックする)。
 */
export function pickByS3Rule(sfen: string, cursor: number): S3PickResult | undefined {
  for (let i = cursor; i < S3_SCRIPT.length; i++) {
    const move = S3_SCRIPT[i];
    if (move !== undefined && isLegalMove(sfen, move)) {
      return { move, nextCursor: i + 1 };
    }
  }
  return undefined;
}

/**
 * E「浅い読み」。同じエンジンプロセス(呼び出し側が渡すHighPriorityEngine)に
 * position → go(movetimeMs既定100)。bestmoveが無い/resign/winなら undefined を返す
 * (呼び出し側は自分側の手なし=終局扱いにする)。
 */
export async function pickByEProfile(
  sfen: string,
  engine: HighPriorityEngine,
  movetimeMs = 100,
): Promise<string | undefined> {
  engine.position(sfen);
  const { bestmove } = await engine.go({ movetimeMs });
  if (!bestmove || bestmove === "resign" || bestmove === "win") return undefined;
  return bestmove;
}

/**
 * R「乱択混合」。各手番で prng.next() < randomRate なら getLegalMoves(sfen) から
 * prng で1手選ぶ。そうでなければ E(浅い読み)。
 */
export async function pickByRProfile(
  sfen: string,
  prng: Prng,
  randomRate: number,
  engine: HighPriorityEngine,
): Promise<string | undefined> {
  if (prng.next() < randomRate) {
    const legalMoves = getLegalMoves(sfen);
    if (legalMoves.length === 0) return undefined;
    const index = prng.nextInt(legalMoves.length);
    return legalMoves[index];
  }
  return pickByEProfile(sfen, engine);
}

/** S3のcursorを対局ごとに保持するための入れ物(explore.tsが対局ごとに1つ持つ)。 */
export interface S3ScriptState {
  cursor: number;
}

/** pickMoveが1回の手選択に必要とする文脈。 */
export interface PickMoveContext {
  prng: Prng;
  randomRate: number;
  engine: HighPriorityEngine;
  s3: S3ScriptState;
}

/**
 * プロファイルごとの手選択を、計画書「対局者(自分側)の5プロファイル」の表の順で
 * 試す。戻り値が undefined の場合、自分側の手が決まらなかった(Eのエンジンが
 * bestmoveを返さなかった)ことを意味し、呼び出し側は終局扱いにする。
 */
export async function pickMove(
  profile: PlayerProfileId,
  sfen: string,
  response: StateResponseBodyWithPlan,
  context: PickMoveContext,
): Promise<string | undefined> {
  switch (profile) {
    case "S1":
      return pickByS1Rule(response) ?? (await pickByEProfile(sfen, context.engine));
    case "S2":
      return (
        pickByS2Rule(sfen, response) ??
        pickByS1Rule(response) ??
        (await pickByEProfile(sfen, context.engine))
      );
    case "S3": {
      const result = pickByS3Rule(sfen, context.s3.cursor);
      if (result) {
        context.s3.cursor = result.nextCursor;
        return result.move;
      }
      return pickByS1Rule(response) ?? (await pickByEProfile(sfen, context.engine));
    }
    case "E":
      return pickByEProfile(sfen, context.engine);
    case "R":
      return pickByRProfile(sfen, context.prng, context.randomRate, context.engine);
    case "B":
    case "B2":
      // STEP D3(計画 8.8 の A8): B・B2 の振り分けは pickMoveWithTier の 1 か所だけ。ここへ来たら配線の誤りなので止める
      // (黙って undefined を返すと、呼び出し側で「自分側の手なし=終局」に化ける)。
      throw new Error(`プロファイル ${profile} は pickMove では扱わない(pickMoveWithTier を使う)`);
    default:
      return undefined;
  }
}

/** pickMoveWithTier の戻り値。tier は B・B2 のときだけ段の名前、S1〜R は null(段を持たない)。 */
export interface PickedMove {
  move: string | undefined;
  tier: BeginnerTier | null;
}

/**
 * STEP D3(計画 8.4 の決定 11・F-B14)。プロファイル → 決め方の振り分け。B・B2 は beginnerProfile の { move, tier }、
 * S1〜R は既存の pickMove(戻り値は変えない)で tier は null。explore.ts はこれだけを呼ぶ。
 */
export async function pickMoveWithTier(
  profile: PlayerProfileId,
  sfen: string,
  response: StateResponseBodyWithPlan,
  context: PickMoveContext,
): Promise<PickedMove> {
  if (profile === "B" || profile === "B2") {
    const picked = pickByBeginnerProfile(sfen, profile);
    return { move: picked?.move, tier: picked?.tier ?? null };
  }
  return { move: await pickMove(profile, sfen, response, context), tier: null };
}

/**
 * STEP D3(計画 Q-4・F-B15)。探索の棋譜 JSON の本文。欄の並びは既存のまま(id・source・profile・seed・moves)で、
 * **B・B2 のときだけ tiers(先手の手ごとの段の名前)を足す。** replay.ts は id と moves しか読まないので再生は変わらない。
 */
export function buildKifuJsonText(kifu: {
  id: string;
  profile: PlayerProfileId;
  seed: number;
  moves: readonly string[];
  tiers: readonly (BeginnerTier | null)[];
}): string {
  const base = { id: kifu.id, source: "explore", profile: kifu.profile, seed: kifu.seed, moves: kifu.moves };
  const body = kifu.profile === "B" || kifu.profile === "B2" ? { ...base, tiers: kifu.tiers } : base;
  return `${JSON.stringify(body, null, 2)}\n`;
}
