// STEP FIG-2 (a)(docs/STEP_FIG2A_PLAN_2026-09-26.md)。実戦の 1 局面から
// **「この局面では、こういう自玉側の形が選択肢になります」**と言える候補を出す純関数の層。
//
// 【この道具が言うこと・言わないこと】
// - 言うこと: 到達できる形の候補と、その順位(matchScore 降順 → shapeId 昇順)。
// - 言わないこと: 「この囲いが正解です」(人間の指定)。何件見せるかの切れ目(計画 §8.3。
//   `rankReachableShapes` が返すのは順位であって切れ目ではなく、**新しい閾値を作らずに
//   「ここから下は候補でない」と言える線は既存の道具の中に無い**)。だから **v1 は切らず、
//   到達できる候補を全件、順位つきで返す**。何件見せるかは見せ方 (b) の判断。
//
// 【新しい閾値を 1 つも作らない】
// 候補に残すかどうかを決めるのは `rankReachableShapes`(side=opponent と completed を外す)だけで、
// **名前の露出では候補を捨てない**(計画 §8.2 の司令塔の直し。序盤で図が必ず空になるのを避けるため)。
// 名前をどう出すかだけを `decideNameExposure` に D'' の値で聞く。個数の上限・下限も matchScore の線も置かない。
//
// 【この図は形の名前を断定できない作りになっている(計画 §8.5。P3 は予測ではなく道具の性質)】
// `rankReachableShapes` は `completed` を候補から外し、`decideNameExposure` の R4(named)は
// `completed` / `matched` にしか当たらない。したがって `label.level` に `"named"` は**構造上現れない**。
// 「断定しないよう気をつけている」のではなく「**断定できない作り**」である(試験と変異で示す)。
//
// 【このファイルが絶対にやらないこと】
// - 新しい判定・新しい閾値・新しい将棋知識を書くこと(判定は apps/server の既存関数がすべて行う)。
// - 名前を作ること。名前は `data/` の認識(`review_status`)を経たものだけを運ぶ(CLAUDE.md 規則 4)。
// - 「そこへ行く手順があるか」の**経路の判定**(v1 でやらない。注 2 に書く)。
// - 狙い(⑤)で絞ること(`selectTargetPurpose` を呼ばない劣化版。注 1 に書く)。
// - ファイルの読み書き以外の入出力・エンジンの起動。**材料の読み込みは CLI
//   (scripts/playtest/figShapeCandidates.ts)の責務**(この層が読むのは `data/` の形の定義だけ)。

import path from "node:path";
import { fileURLToPath } from "node:url";

import type { Role } from "shogiops/types";
import { unpromote } from "shogiops/variant/util";

import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import {
  decideNameExposure,
  type NameExposureLevel,
  type NameExposureRule,
  type NameExposureValues,
} from "../../../apps/server/src/analysis/nameExposure.js";
import {
  analyzeShapeFormation,
  type ShapeFormationResult,
} from "../../../apps/server/src/analysis/shapeFormationAnalyzer.js";
import { rankReachableShapes, type RankedReachableShape } from "../../../apps/server/src/analysis/shapeGraphRanking.js";
import { DEFAULT_SHAPES_DIR, loadShapes, type ShapeDefinition } from "../../../apps/server/src/analysis/shapeRepository.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { movedRequiredCountOf } from "../lib/recognitionMeasure.js";

export class ShapeCandidatesError extends Error {}

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * 下書きの形の置き場所(2026-09-25 の知識レーン)。
 *
 * **`analyzeShapeFormation` は下書きを読まない**(`shapeRepository.ts` の `DEFAULT_SHAPES_DIR` は
 * `data/shapes/` だけで、`data/drafts/…` を読む口はリポジトリ内に 1 つも無い)。下書きを候補に
 * 入れるには、この道具が `options.shapes` に明示して渡すしかない ― **そうすることを選んだ**ので、
 * 注 3(`FIG2A_NOTES`)に必ず書く(計画 §8.1・§8.5)。
 */
const DRAFT_SHAPES_DIR = path.join(__dirname, "..", "..", "..", "data", "drafts", "2026-09-25-knowledge", "shapes");

/**
 * 形の読み先の既定(確定の置き場 → 下書きの置き場の順)。**本番の呼び出し
 * (`figShapeCandidates.ts`)は引数を渡さないので、この既定がそのまま使われる。**
 */
export const DEFAULT_SHAPE_DIRS: readonly string[] = [DEFAULT_SHAPES_DIR, DRAFT_SHAPES_DIR];

/**
 * `data/shapes/`(確定の置き場)と `data/drafts/2026-09-25-knowledge/shapes/`(下書き)の形を
 * すべて読み、id 昇順で返す。**読み込みは既存の `loadShapes` に委ね、ここでは形式の判断をしない。**
 * 同じ id が 2 つの置き場に跨って現れたら例外(どちらを採ったか黙って決めない)。
 *
 * 【0 件は正当な入力ではなく読み込みの失敗として止める(STEP P-100。計画 §9.2)】
 * 黙って 0 件を返すと、呼び出し側では**候補 0 件 = `figure: false`(図なし)**に化けてしまい、
 * 読み込みの失敗が「図を出さない」という正常な出口と見分けられなくなる。だから
 * **読んだディレクトリ「ごと」に 0 件で例外にし、文面にそのディレクトリのパスを入れる。**
 * **合計で判定しない** ― 合計だと片方だけ読めなくなった場合(82 → 2)を見逃すため。
 * **件数を期待値(82/80/2)と突き合わせることはしない**(それは試験の仕事で、実行時に持つと新しい閾値になる)。
 * ディレクトリ自体が無い場合は `loadShapes` が既にパス入りの例外を投げる(ここでは足さない)。
 */
export function loadAllShapes(dirs: readonly string[] = DEFAULT_SHAPE_DIRS): ShapeDefinition[] {
  const shapes: ShapeDefinition[] = [];
  for (const dir of dirs) {
    const loaded = loadShapes(dir);
    if (loaded.length === 0) {
      throw new ShapeCandidatesError(`形の JSON が 1 件もありません(読み込みの失敗として止めます): "${dir}"`);
    }
    shapes.push(...loaded);
  }
  const seen = new Set<string>();
  for (const shape of shapes) {
    if (seen.has(shape.id)) throw new ShapeCandidatesError(`形の id が重複しています: "${shape.id}"`);
    seen.add(shape.id);
  }
  return shapes.sort((a, b) => a.id.localeCompare(b.id));
}

/**
 * 露出の値。**`EXPOSURE_VALUE_SETS["D''"]` と同値**(試験で 5 欄を明示的に照合する)。
 * 道具が値を明示して渡すことで、**既定の `NAME_EXPOSURE_VALUES` は動かさない**(計画 §3)。
 */
export const FIG2A_EXPOSURE_VALUES: NameExposureValues = {
  minRequiredForName: 1,
  minEvidenceForHedged: 2,
  hideCompletedWithoutEvidence: true,
  hedgeOneEvidenceIfMissingLe1: true,
  minEvidenceForCompleted: "movedRequired",
};

/**
 * 出力に必ず添える注(劣化の注)。**3 つ全部を `notes` に入れる**(試験で固定する)。
 * 1 と 2 は「この道具が見ていないもの」、3 は「この道具が自分で選んでやったこと」。
 */
export const FIG2A_NOTES: readonly string[] = [
  "狙い(⑤)で絞っていません。目的で選んだ結果ではありません。",
  "経路の判定をしていません。そこへ行く手順があるかは見ていません。",
  "未レビューの下書き 80 件を含む 82 形から探しました。下書きの名前は断定せず、最大でも「〜のような形」までにとどめます。",
];

/** 1 局面ぶんの入口。 */
export interface ShapeCandidateInput {
  kifuId: string;
  displayPly: number;
  sfen: string;
  /** その局の USI の全手(固定棋譜の `moves`)。 */
  moves: readonly string[];
  /**
   * `moves` の開始局面。**既定は平手**(`mirrored: false` の局)。
   * 回した局(`mirrored: true`)は固定棋譜の `startSfen` を渡す(計画 §8.6 の決定 (B))。
   * 既存の `lib/sideAlignment.ts` の `initialSfenOf`・`lib/finalPosition.ts` と同じ読み方。
   */
  initialSfen?: string;
}

/** 名前の見せ方。`none` は**盤だけ出す**(名前欄を空にする。計画 §8.2)。 */
export interface ShapeCandidateLabel {
  /** `decideNameExposure` の `hidden` を `none`(盤だけ出す)に読み替えたもの。 */
  level: "named" | "hedged" | "none";
  /** `none` のときは null。`hedged` は「〜のような形」。 */
  text: string | null;
}

/** 露出の判断の材料になった数(そのまま出す。計算し直さない)。 */
export interface ShapeCandidateEvidence {
  evidenceCount: number;
  missingCount: number;
  requiredCount: number;
  movedRequiredCount: number;
}

export interface ShapeCandidate {
  shapeId: string;
  family: string;
  parentShapeId: string | null;
  /** `rankReachableShapes` が `completed` を外すので `forming` か `none` だけ。 */
  status: RankedReachableShape["status"];
  matchScore: number;
  /** 1 から始まる順位(`matchScore` 降順 → `shapeId` 昇順)。**切れ目ではない。** */
  rank: number;
  label: ShapeCandidateLabel;
  evidence: ShapeCandidateEvidence;
  /** 内部用(どの規則で決まったか)。顧客に見せるものではない。 */
  exposureRule: NameExposureRule;
  pendingNote: string | null;
}

/**
 * 顧客版に出さない欄(`customerVisible: false` の印を付ける。計画 §2。
 * `obs.vocab.exposure` の 0 / 657 / 4703 と同じ型の数 = 道具の振る舞いであって顧客の指し方ではない。P-99)。
 */
export interface ShapeCandidatesInternal {
  customerVisible: false;
  /** 名前の見せ方ごとの件数(この局面ぶん)。 */
  exposureCounts: Record<"named" | "hedged" | "none", number>;
  /**
   * 規則ごとの件数。**計画 §2 の欄名は `droppedByRule` だったが、§8.2 で「露出では候補を捨てない」
   * ことになったため、落ちた件数ではなく「どの規則で決まったかの件数」に読み替えた**(実装上の命名)。
   */
  countsByRule: Record<NameExposureRule, number>;
}

export interface ShapeCandidatesResult {
  kifuId: string;
  displayPly: number;
  sfen: string;
  /**
   * **到達できる候補が 0 件のときだけ false**(名前が出せないことは図を出さない理由にしない。計画 §8.2)。
   *
   * **`figure` は到達できる候補が 0 件かどうかであって、図を載せるかどうかではない**
   * (STEP P-100。紙面に図を載せるかの判断は別の数 ― `internal.exposureCounts.hedged` ― を見る側の仕事で、
   * この旗を「図あり」と読むと食い違う)。
   */
  figure: boolean;
  candidates: ShapeCandidate[];
  notes: string[];
  internal: ShapeCandidatesInternal;
}

export interface FindShapeCandidatesOptions {
  /** 渡さなければ `loadAllShapes()`(82 形)。 */
  shapes?: ShapeDefinition[];
}

const EXPOSURE_RULES: readonly NameExposureRule[] = ["R0", "R1", "R2", "R3", "R4", "R5", "R5p", "R6"];

// ---------------------------------------------------------------------------
// 駒数の検査(2026-09-26 に追加。納品レーン長・司令塔の決定)
//
// 【なぜ足したか】司令塔が実戦の `sfen` に先手の角が 2 枚あるのを見て「成立しない」と止めたが、
// 相手の角を取って打ち直した結果の正しい局面だった(道具の出力に誤りは無かった)。
// ただし **この型を機械で止める場所がどこにも無かった**のは事実なので、ここで止める。
// **`parseSfen` は駒数を見ない**(歩 17 枚・20 枚の局面をどちらも通すことを実測で確かめた)。
//
// 【新しい閾値ではなく将棋の決まり。しかも表を書かない】
// 期待する数(玉 2・飛 2・角 2・金 4・銀 4・桂 4・香 4・歩 18)は**平手の初期局面から 1 回数えて引く**
// (`recognitionMeasure.ts` が初期位置を引くのと同じやり方。新しい将棋知識を書かない)。
// 数えるのは**成駒を元の駒に戻し、持ち駒を含め、両者ぶんを合算した数**。
// ---------------------------------------------------------------------------

/** 成駒を元の駒種へ戻す(shogiops。自作しない)。 */
const toBaseRole = unpromote("standard");

/** 1 局面の駒を、成駒を戻し・持ち駒を含め・両者ぶん合算して数える。 */
function countPieces(sfen: string): Map<Role, number> {
  const position = parsePosition(sfen);
  const counts = new Map<Role, number>();
  const bump = (role: Role): void => {
    counts.set(role, (counts.get(role) ?? 0) + 1);
  };
  for (const [, piece] of position.board) bump(toBaseRole(piece.role) ?? piece.role);
  for (const color of ["sente", "gote"] as const) {
    for (const [role, count] of position.hands.color(color)) {
      for (let i = 0; i < count; i += 1) bump(toBaseRole(role) ?? role);
    }
  }
  return counts;
}

/** 平手の初期局面から引いた駒の総数。**表を手で書かない**(上のコメント参照)。 */
export const STANDARD_PIECE_COUNTS: ReadonlyMap<Role, number> = countPieces(DEFAULT_INITIAL_SFEN);

/**
 * 局面の駒数が平手の総数と合っているかを確かめ、合わなければ例外にする。
 *
 * **入口の `sfen` だけを検査すれば、再生後の局面も覆える** ― `analyzeShapeFormation` が
 * 「再生結果が `sfen` と一致しなければ例外」を既に保証しているため、通った時点で両者は同じ文字列である。
 */
function assertStandardPieceCounts(sfen: string): void {
  const counts = countPieces(sfen);
  const roles = [...new Set([...STANDARD_PIECE_COUNTS.keys(), ...counts.keys()])].sort();
  const mismatched = roles
    .filter((role) => (counts.get(role) ?? 0) !== (STANDARD_PIECE_COUNTS.get(role) ?? 0))
    .map((role) => `${role}: ${counts.get(role) ?? 0}(平手は ${STANDARD_PIECE_COUNTS.get(role) ?? 0})`);
  if (mismatched.length > 0) {
    throw new ShapeCandidatesError(`駒数が平手の総数と合いません(${mismatched.join("・")}): "${sfen}"`);
  }
}

/** SFEN の手数欄(4 つ目の欄 = 「次に指す手の番号」)。 */
function sfenMoveNumber(sfen: string): number {
  const field = sfen.split(" ")[3];
  if (field === undefined || !/^[1-9][0-9]*$/.test(field)) {
    throw new ShapeCandidatesError(`SFEN の手数欄を読めません: "${sfen}"`);
  }
  return Number(field);
}

/**
 * `moves` から、その局面までの指し手履歴を切り出す。
 *
 * **進める手数は `displayPly -(開始局面の SFEN の手数欄)`。**固定棋譜の `plyOffset` ではなく
 * **渡された開始局面の SFEN の手数欄**を読む(計画 §8.6 で「どちらを読んだかを書く」ことになっている)。
 * 理由: この層は棋譜の欄を知らず、渡された開始局面だけから決めたいため(`plyOffset` を読むと
 * 棋譜の形に依存する)。平手なら 1、回した局の `startSfen` なら 2 になり、どちらも同じ式で足りる。
 *
 * **切り出しが正しいことは道具に確かめさせる**: 手数が範囲の外なら例外、範囲内でも再生結果が `sfen` と
 * 一致しなければ `analyzeShapeFormation` が例外を投げる(黙って別の局面を評価しない。計画 §2)。
 */
function cutMoveHistory(input: ShapeCandidateInput, initialSfen: string): string[] {
  const count = input.displayPly - sfenMoveNumber(initialSfen);
  if (!Number.isInteger(count) || count < 0 || count > input.moves.length) {
    throw new ShapeCandidatesError(
      `displayPly から切り出す手数が範囲の外です(displayPly=${input.displayPly}, ` +
        `開始局面の手数欄=${sfenMoveNumber(initialSfen)}, 手数=${input.moves.length})`,
    );
  }
  return input.moves.slice(0, count);
}

function labelOf(level: NameExposureLevel, name: string): ShapeCandidateLabel {
  if (level === "named") return { level: "named", text: name };
  if (level === "hedged") return { level: "hedged", text: `${name}のような形` };
  return { level: "none", text: null };
}

/**
 * `shapeId` から判定結果と形の定義を引く索引。同じ `shapeId` が 2 つ以上あれば例外
 * (`side: "both"` の形は視点ごとに 2 件返るため。黙ってどちらかを採らない)。
 */
function indexByShapeId<T extends { shapeId: string }>(rows: T[]): Map<string, T> {
  const index = new Map<string, T>();
  for (const row of rows) {
    if (index.has(row.shapeId)) throw new ShapeCandidatesError(`同じ shapeId の判定結果が 2 件あります: "${row.shapeId}"`);
    index.set(row.shapeId, row);
  }
  return index;
}

/**
 * 1 局面から候補形を探す。同じ入力に対しては常に同じ結果を返す(決定的)。
 *
 * 手順(計画 §3 を §8.2 で読み替えたもの):
 * 1. `analyzeShapeFormation` … 形の判定(既存。判定を足さない)。局面と履歴が食い違えば例外。
 * 2. `rankReachableShapes(results, [])` … 到達できる形の順位。**`selectTargetPurpose` を呼ばない劣化版**で、
 *    `[]` を渡すので全件が中立の段になり、並びは `matchScore` 降順 → `shapeId` 昇順だけで決まる(注 1)。
 * 3. 各候補に `decideNameExposure(..., D'')` を当てる。**候補は捨てず、名前の出し方だけを決める。**
 * 4. 候補が 0 件なら `figure: false`(0 個は正常な出口)。
 */
export function findShapeCandidates(
  input: ShapeCandidateInput,
  options: FindShapeCandidatesOptions = {},
): ShapeCandidatesResult {
  const shapes = options.shapes ?? loadAllShapes();
  assertStandardPieceCounts(input.sfen);
  const initialSfen = input.initialSfen ?? DEFAULT_INITIAL_SFEN;
  const moveHistory = cutMoveHistory(input, initialSfen);

  // 例外はそのまま呼び出し側へ返す(握りつぶして別の局面を評価しない)。
  const results: ShapeFormationResult[] = analyzeShapeFormation(input.sfen, moveHistory, { shapes, initialSfen });
  const resultByShapeId = indexByShapeId(results);
  const shapeById = new Map(shapes.map((shape) => [shape.id, shape]));

  const exposureCounts: Record<"named" | "hedged" | "none", number> = { named: 0, hedged: 0, none: 0 };
  const countsByRule = Object.fromEntries(EXPOSURE_RULES.map((rule) => [rule, 0])) as Record<NameExposureRule, number>;

  const candidates = rankReachableShapes(results, []).map((ranked, index): ShapeCandidate => {
    const result = resultByShapeId.get(ranked.shapeId);
    const definition = shapeById.get(ranked.shapeId);
    if (result === undefined || definition === undefined) {
      throw new ShapeCandidatesError(`順位に出た形の判定結果・定義が見つかりません: "${ranked.shapeId}"`);
    }
    // 露出の入力は既存の組み立て方をそのまま使う(計画 §3)。
    const evidence: ShapeCandidateEvidence = {
      evidenceCount: result.formationEvidence.length,
      missingCount: result.missingSquares.length,
      requiredCount: result.matchedSquares.length + result.missingSquares.length,
      movedRequiredCount: movedRequiredCountOf(
        definition.required_pieces.filter((piece) => !piece.optional),
        result.perspectiveColor,
      ),
    };
    const decision = decideNameExposure(
      { kind: "shape", status: ranked.status, ...evidence, reviewStatus: ranked.reviewStatus },
      FIG2A_EXPOSURE_VALUES,
    );
    const label = labelOf(decision.level, ranked.name);
    exposureCounts[label.level] += 1;
    countsByRule[decision.rule] += 1;

    return {
      shapeId: ranked.shapeId,
      family: ranked.family,
      parentShapeId: ranked.parentShapeId,
      status: ranked.status,
      matchScore: ranked.matchScore,
      rank: index + 1,
      label,
      evidence,
      exposureRule: decision.rule,
      pendingNote: decision.pendingNote,
    };
  });

  return {
    kifuId: input.kifuId,
    displayPly: input.displayPly,
    sfen: input.sfen,
    figure: candidates.length > 0,
    candidates,
    notes: [...FIG2A_NOTES],
    internal: { customerVisible: false, exposureCounts, countsByRule },
  };
}
