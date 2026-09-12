// data/shapes/*.json の下書きに対する機械的な検証(STEP U6-A)。
// docs/STEP_UNIT6_PLAN_2026-09-12.md 3.3 の多段階検証のうち、
//   段階A(静的: 盤の上で矛盾しないか・既存の形と重複しないか・下書きの印の規約)
//   段階B(初期局面から、その形の必須マスの配置へ到達できる手順が1つ以上あるか)
// を機械で回すためのもの。**開発補助であり、本番導線(apps/)には含めない。**
//
// 【このスクリプトが絶対にしないこと】
// 将棋としての正しさ(この形が本当にその名前の囲いか、この囲いが良いか)は一切判断しない。
// 判断するのは「盤の上で矛盾していないか」「その配置に到達できる手順が見つかるか」だけである。
// 段階Bで見つからなかった場合も「組めない」とは言わない。ここで使う探索は
// 「先手だけが動き、駒を取らず、成らない」という単純化した模型であり、
// 見つからなかったことは「この模型では見つからなかった」以上を意味しない。
//
// 使い方:
//   npx tsx scripts/verify-shapes.ts              # data/shapes/ の全件
//   npx tsx scripts/verify-shapes.ts --draft-only # review_status が draft のものだけ
//
// スキーマ準拠そのものは node scripts/validate-data.mjs の役割であり、ここでは重ねて行わない。

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { makeSfen, parseSfen } from "shogiops/sfen";
import { makeUsi, parseSquareName } from "shogiops/util";
import type { MoveOrDrop, Role, Square } from "shogiops/types";
import type { Position } from "shogiops/variant/position";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SHAPES_DIR = path.join(__dirname, "..", "data", "shapes");

/** 平手の初期局面。先手番。 */
const INITIAL_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

/** 下書きの印(2026-09-12 の人間の決定)。前半までが固定の文字列で、後半は下書きを書いた日の日付。 */
const DRAFT_MARK_PREFIX = "[LLM下書き ";
const DRAFT_MARK_PATTERN = /\[LLM下書き (\d{4}-\d{2}-\d{2})\]$/;

/** 段階Bの探索で展開するノード数の上限。将棋の判断ではなく、実行時間の上限にすぎない。 */
const MAX_NODES = 60000;

const PIECE_TO_ROLE: Record<string, Role> = {
  玉: "king",
  王: "king",
  飛: "rook",
  角: "bishop",
  金: "gold",
  銀: "silver",
  桂: "knight",
  香: "lance",
  歩: "pawn",
};

interface RequiredPiece {
  piece: string;
  square: string;
  optional: boolean;
}

interface Shape {
  id: string;
  name: string;
  side: string;
  required_pieces: RequiredPiece[];
  typical_build_order?: string[];
  source?: string;
  confidence_level?: string;
  review_status?: string;
}

interface Finding {
  level: "NG" | "注意";
  stage: "A" | "B";
  message: string;
}

function loadShapes(): Shape[] {
  return readdirSync(SHAPES_DIR)
    .filter((f) => f.endsWith(".json"))
    .sort()
    .map((f) => JSON.parse(readFileSync(path.join(SHAPES_DIR, f), "utf-8")) as Shape);
}

function isValidSquareName(square: string): boolean {
  return /^[1-9][a-i]$/.test(square);
}

// ---------------------------------------------------------------------------
// 段階A: 静的
// ---------------------------------------------------------------------------

function verifyStageA(shape: Shape, all: Shape[]): Finding[] {
  const findings: Finding[] = [];
  const add = (level: Finding["level"], message: string) =>
    findings.push({ level, stage: "A", message });

  // A-1 マス名の形式と、駒種の名前
  const seen = new Map<string, string>();
  for (const rp of shape.required_pieces) {
    if (!isValidSquareName(rp.square)) {
      add("NG", `マス名が盤の外か形式が違う: ${rp.piece}${rp.square}`);
      continue;
    }
    if (!(rp.piece in PIECE_TO_ROLE)) {
      add("NG", `駒の名前が解釈できない: 「${rp.piece}」`);
    }
    // A-2 同じマスに2枚
    const prev = seen.get(rp.square);
    if (prev !== undefined) {
      add("NG", `同じマスに2枚が指定されている: ${rp.square}(${prev} と ${rp.piece})`);
    } else {
      seen.set(rp.square, rp.piece);
    }
  }

  // A-3 玉の数と位置
  const kings = shape.required_pieces.filter((rp) => rp.piece === "玉" || rp.piece === "王");
  if (kings.length === 0) {
    add("注意", "玉が必須マスに含まれていない(囲いの形としては珍しい)");
  } else if (kings.length > 1) {
    add("NG", `玉が ${kings.length} 枚指定されている`);
  } else {
    const rank = kings[0]!.square[1]!;
    if (shape.side !== "opponent" && !["g", "h", "i"].includes(rank)) {
      add("注意", `先手の玉が自陣(七〜九段)の外にある: ${kings[0]!.square}`);
    }
  }

  // A-4 駒の枚数が実際の持ち駒数を超えていないか
  const limits: Record<string, number> = { 玉: 1, 王: 1, 飛: 1, 角: 1, 金: 2, 銀: 2, 桂: 2, 香: 2, 歩: 9 };
  const counts = new Map<string, number>();
  for (const rp of shape.required_pieces) {
    counts.set(rp.piece, (counts.get(rp.piece) ?? 0) + 1);
  }
  for (const [piece, count] of counts) {
    const limit = limits[piece];
    if (limit !== undefined && count > limit) {
      add("NG", `${piece} が ${count} 枚指定されているが、初形では ${limit} 枚しかない`);
    }
  }

  // A-5 typical_build_order が required_pieces のマスと対応しているか
  if (shape.typical_build_order) {
    const squares = new Set(shape.required_pieces.map((rp) => rp.square));
    for (const sq of shape.typical_build_order) {
      if (!squares.has(sq)) {
        add("NG", `typical_build_order のマス ${sq} が required_pieces に無い`);
      }
    }
    for (const sq of squares) {
      if (!shape.typical_build_order.includes(sq)) {
        add("注意", `required_pieces のマス ${sq} が typical_build_order に無い`);
      }
    }
  }

  // A-6 既存の形との重複(必須マスの集合が完全に一致するもの)
  const key = (s: Shape) =>
    s.required_pieces
      .filter((rp) => !rp.optional)
      .map((rp) => `${rp.piece}${rp.square}`)
      .sort()
      .join(",");
  for (const other of all) {
    if (other.id === shape.id) continue;
    if (key(other) === key(shape)) {
      add("NG", `必須マスの集合が ${other.id}(${other.name})と完全に一致している`);
    }
  }

  // A-7 下書きの印の規約(2026-09-12 の人間の決定)。
  // 印がある記録 = LLM の下書きとして規約を課す。印が無い draft は、規約より前に作られた
  // 記録か人間が書いたものでありうるため、NG ではなく注意に留める(ここで断定しない)。
  if (shape.review_status === "draft") {
    const source = shape.source ?? "";
    if (!source.includes(DRAFT_MARK_PREFIX)) {
      add("注意", `draft だが source に印「${DRAFT_MARK_PREFIX}…]」が無い(規約より前の記録か、人間が書いたもの)`);
    } else {
      if (!DRAFT_MARK_PATTERN.test(source.trim())) {
        add("NG", "source の末尾が「[LLM下書き YYYY-MM-DD]」の形になっていない");
      }
      if (source.replace(DRAFT_MARK_PATTERN, "").trim().length === 0) {
        add("NG", "source が印だけで、実際の出典が書かれていない");
      }
      if (shape.confidence_level !== "low") {
        add("NG", `LLM の下書きなのに confidence_level が "${shape.confidence_level}"(規約は low)`);
      }
    }
  } else if ((shape.source ?? "").includes(DRAFT_MARK_PREFIX)) {
    add("NG", `LLM の下書きの印があるのに review_status が "${shape.review_status}"(規約は draft)`);
  }

  // A-8 ランク付けに参加できるか(side)
  if (shape.side === "opponent") {
    add("注意", 'side が "opponent" のため、自分の目標形のランク付けには参加しない');
  }

  return findings;
}

// ---------------------------------------------------------------------------
// 段階B: 初期局面から必須マスの配置へ到達できるか
// ---------------------------------------------------------------------------

interface Target {
  role: Role;
  square: Square;
  name: string;
}

function positionKey(pos: Position): string {
  return makeSfen(pos).split(" ").slice(0, 3).join(" ");
}

function forceSenteToMove(pos: Position): Position {
  const next = pos.clone();
  next.turn = "sente";
  return next;
}

/** 未達成の目標について、駒の現在地からの単純な距離の和。将棋の評価ではなく探索の道案内。 */
function heuristic(pos: Position, targets: Target[]): number {
  let total = 0;
  for (const t of targets) {
    const occupant = pos.board.get(t.square);
    if (occupant && occupant.color === "sente" && occupant.role === t.role) continue;
    // その駒種の先手の駒のうち、いちばん近いものまでの距離
    let best = 9;
    for (const sq of pos.board.pieces("sente", t.role)) {
      const dFile = Math.abs((sq % 9) - (t.square % 9));
      const dRank = Math.abs(Math.floor(sq / 9) - Math.floor(t.square / 9));
      best = Math.min(best, Math.max(dFile, dRank));
    }
    total += best === 9 ? 9 : Math.max(best, 1);
    // 目標のマスを別の駒がふさいでいるなら、そのぶんも手数が要る
    if (occupant && occupant.color === "sente") total += 1;
  }
  return total;
}

function isSatisfied(pos: Position, targets: Target[]): boolean {
  return targets.every((t) => {
    const p = pos.board.get(t.square);
    return p !== undefined && p.color === "sente" && p.role === t.role;
  });
}

interface StageBResult {
  found: boolean;
  moves: string[];
  nodes: number;
}

/**
 * 先手だけが動き、駒を取らず、成らない、という単純化した模型で
 * 必須マスの配置へ到達する手順を探す(A*)。
 * 見つからなかった場合に言えるのは「この模型では見つからなかった」だけである。
 */
function verifyStageB(shape: Shape): StageBResult {
  const targets: Target[] = [];
  for (const rp of shape.required_pieces) {
    if (rp.optional) continue;
    const role = PIECE_TO_ROLE[rp.piece];
    if (!role || !isValidSquareName(rp.square)) return { found: false, moves: [], nodes: 0 };
    targets.push({ role, square: parseSquareName(rp.square as never), name: `${rp.piece}${rp.square}` });
  }

  const start = parseSfen("standard", INITIAL_SFEN);
  if (start.isErr) throw new Error("初期局面の解析に失敗した");
  const root = start.value;

  interface Node {
    pos: Position;
    moves: string[];
    f: number;
  }
  const open: Node[] = [{ pos: root, moves: [], f: heuristic(root, targets) }];
  const visited = new Set<string>([positionKey(root)]);
  let nodes = 0;

  while (open.length > 0 && nodes < MAX_NODES) {
    // いちばん f が小さいものを取り出す(小さな配列なので線形探索で足りる)
    let bestIndex = 0;
    for (let i = 1; i < open.length; i += 1) {
      if (open[i]!.f < open[bestIndex]!.f) bestIndex = i;
    }
    const node = open.splice(bestIndex, 1)[0]!;
    nodes += 1;

    if (isSatisfied(node.pos, targets)) {
      return { found: true, moves: node.moves, nodes };
    }
    if (node.moves.length >= 24) continue;

    const ctx = node.pos.ctx();
    const satisfiedSquares = new Set(
      targets
        .filter((t) => {
          const p = node.pos.board.get(t.square);
          return p !== undefined && p.color === "sente" && p.role === t.role;
        })
        .map((t) => t.square),
    );

    for (const [from, dests] of node.pos.allMoveDests(ctx)) {
      // すでに目標のマスに収まっている駒は動かさない
      if (satisfiedSquares.has(from)) continue;
      for (const to of dests) {
        // 駒を取る手・成る手は模型から外す(囲いを組む手順だけを見るため)
        if (node.pos.board.get(to) !== undefined) continue;
        const move: MoveOrDrop = { from, to, promotion: false };
        if (!node.pos.isLegal(move, ctx)) continue;
        const next = node.pos.clone();
        next.play(move);
        const forced = forceSenteToMove(next);
        const key = positionKey(forced);
        if (visited.has(key)) continue;
        visited.add(key);
        const moves = [...node.moves, makeUsi(move)];
        open.push({ pos: forced, moves, f: moves.length + heuristic(forced, targets) });
      }
    }
  }

  return { found: false, moves: [], nodes };
}

// ---------------------------------------------------------------------------

function main(): void {
  const draftOnly = process.argv.includes("--draft-only");
  const all = loadShapes();
  const targets = draftOnly ? all.filter((s) => s.review_status === "draft") : all;

  let ng = 0;
  let caution = 0;

  for (const shape of targets) {
    const findings = verifyStageA(shape, all);
    const b = verifyStageB(shape);
    const squares = shape.required_pieces.map((rp) => `${rp.piece}${rp.square}`).join("・");

    console.log(`\n## ${shape.id}(${shape.name})`);
    console.log(`  必須マス: ${squares}`);
    console.log(`  review_status: ${shape.review_status} / confidence_level: ${shape.confidence_level}`);
    console.log(
      `  段階A: ${findings.length === 0 ? "指摘なし" : `${findings.filter((f) => f.level === "NG").length} NG / ${findings.filter((f) => f.level === "注意").length} 注意`}`,
    );
    for (const f of findings) {
      console.log(`    [${f.level}] ${f.message}`);
      if (f.level === "NG") ng += 1;
      else caution += 1;
    }
    if (b.found) {
      console.log(`  段階B: 到達する手順が見つかった(${b.moves.length} 手 / 展開 ${b.nodes} ノード)`);
      console.log(`    手順の一例: ${b.moves.join(" ")}`);
    } else {
      console.log(
        `  段階B: この模型では見つからなかった(展開 ${b.nodes} ノード、上限 ${MAX_NODES})。「組めない」という意味ではない`,
      );
      caution += 1;
    }
  }

  console.log(`\n---\n対象 ${targets.length} 件 / NG ${ng} 件 / 注意 ${caution} 件`);
  process.exitCode = ng > 0 ? 1 : 0;
}

main();
