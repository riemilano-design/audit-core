// STEP U6-J の事前確認(docs/STEP_U6-J_PLAN_2026-09-12.md 4.)。
//
// 【このファイルがやること】
// 記録済みのJSONL(固定棋譜4局・ready 59行)に対して、本番関数
// analyzeShapeFormation(apps/server/src/analysis/shapeFormationAnalyzer.ts)を
// 呼び直し、その出力(matchedSquares / missingSquares / formationEvidence)へ
// 案ごとのformingの述語を当てて、案どうしが本当に違う答えを出すかを数える。
//
// 【このファイルが絶対にやらないこと】
// - apps/ の変更。ここでは本番の判定を1行も変えない(述語は本ファイル内にだけ書く)。
// - 案の優劣の判断・閾値の決定(判断的知識。人間が決める)。
// - 「異常」の判定。ここで出るのは案の間の差の行数だけである。
//
// 【校正(必須)】
// 案 current の述語は、本番のresolveStatusをそのまま写したものである。したがって
// 本番が返したstatusと、本ファイルのcurrentの述語の結果は、59行×形の全件で
// 一致しなければならない。一致しなければ、案の比較ではなく本ファイルが壊れている
// (docs/AGENT_PROTOCOL.md「既知の正解で校正してから未知のデータに使う」)。
//
// 使い方: npx tsx scripts/u6j-precheck.ts <a.jsonl> [<b.jsonl> ...]

import { readFileSync } from "node:fs";

import {
  analyzeShapeFormation,
  type ShapeFormationResult,
} from "../apps/server/src/analysis/shapeFormationAnalyzer.js";
import { getShapes } from "../apps/server/src/analysis/shapeRepository.js";

/** 案の名前。docs/STEP_U6-J_PLAN_2026-09-12.md 3. の表と同じ。 */
type FormingRule = "current" | "evidenceMin2" | "keyPieceEvidence" | "evidenceHalf";

const RULES: FormingRule[] = ["current", "evidenceMin2", "keyPieceEvidence", "evidenceHalf"];

/** その形のrequired_pieces(optionalでないもの)のうち、玉のマス。無ければundefined。 */
function kingSquareOf(shapeId: string): string | undefined {
  const shape = getShapes().find((s) => s.id === shapeId);
  if (!shape) return undefined;
  const king = shape.required_pieces.find((p) => !p.optional && (p.piece === "玉" || p.piece === "王"));
  return king?.square;
}

/** 案ごとのformingの述語。completedの分岐(missing===0)は本STEPでは変えないため、
 * ここではcompletedでない形についてだけ呼ぶ。 */
function isForming(rule: FormingRule, result: ShapeFormationResult): boolean {
  const matched = result.matchedSquares.length;
  const evidence = result.formationEvidence.length;
  if (matched < 1) return false;

  switch (rule) {
    case "current":
      return evidence >= 1;
    case "evidenceMin2":
      return evidence >= 2;
    case "keyPieceEvidence": {
      if (evidence < 1) return false;
      const kingSquare = kingSquareOf(result.shapeId);
      if (kingSquare === undefined) return true; // 玉を要求しない形は従来どおり
      return result.formationEvidence.some((e) => e.square === kingSquare);
    }
    case "evidenceHalf":
      return evidence >= Math.ceil(matched / 2);
  }
}

interface Row {
  kifuId: string;
  ply: number;
  /** 案ごとの「formingになった形のid」(ソート済み)。 */
  forming: Record<FormingRule, string[]>;
  /** completedの形のid(全案共通)。 */
  completed: string[];
}

function main(): void {
  const files = process.argv.slice(2);
  if (files.length === 0) {
    console.error("使い方: npx tsx scripts/u6j-precheck.ts <a.jsonl> [<b.jsonl> ...]");
    process.exit(1);
  }

  const rows: Row[] = [];
  let calibrationChecked = 0;
  let calibrationMismatch = 0;

  for (const file of files) {
    const lines = readFileSync(file, "utf-8").trim().split("\n");
    for (const line of lines) {
      const record = JSON.parse(line) as {
        kind?: string;
        phase?: string;
        ply?: number;
        sfen?: string;
        response?: { moveHistory?: string[] };
      };
      if (record.kind === "meta") continue;
      if (record.phase !== "ready") continue;
      const sfen = record.sfen;
      const moveHistory = record.response?.moveHistory;
      if (sfen === undefined || moveHistory === undefined) {
        console.error(`sfen または moveHistory が無い行があります: ${file} ply=${record.ply}`);
        process.exit(1);
      }

      const results = analyzeShapeFormation(sfen, moveHistory);
      const forming: Record<FormingRule, string[]> = {
        current: [],
        evidenceMin2: [],
        keyPieceEvidence: [],
        evidenceHalf: [],
      };
      const completed: string[] = [];

      for (const result of results) {
        if (result.status === "completed") {
          completed.push(result.shapeId);
          continue;
        }
        for (const rule of RULES) {
          if (isForming(rule, result)) forming[rule].push(result.shapeId);
        }
        // 校正: 本番のstatusとcurrentの述語が一致すること。
        calibrationChecked += 1;
        const productionForming = result.status === "forming";
        if (productionForming !== isForming("current", result)) {
          calibrationMismatch += 1;
          console.error(
            `校正NG: ${file} ply=${record.ply} shape=${result.shapeId} 本番=${result.status} current述語=${isForming("current", result)}`,
          );
        }
      }

      for (const rule of RULES) forming[rule].sort();
      completed.sort();
      rows.push({ kifuId: file.replace(/^.*\//, "").replace(/\.jsonl$/, ""), ply: record.ply ?? -1, forming, completed });
    }
  }

  console.log(`## 校正`);
  console.log(`- 突き合わせた (行 × 形) の件数: ${calibrationChecked}`);
  console.log(`- 不一致: ${calibrationMismatch} 件${calibrationMismatch === 0 ? "(校正OK)" : "(校正NG。ここで止める)"}`);
  if (calibrationMismatch > 0) process.exit(1);

  console.log(`\n## 行数`);
  console.log(`- ready 行: ${rows.length}`);

  console.log(`\n## 案ごとの「formingが1件以上ある行」の数`);
  for (const rule of RULES) {
    const n = rows.filter((r) => r.forming[rule].length > 0).length;
    const total = rows.reduce((sum, r) => sum + r.forming[rule].length, 0);
    console.log(`- ${rule}: ${n} 行 / ${rows.length}(formingの延べ件数 ${total})`);
  }

  console.log(`\n## 案どうしで答えが違う行数(formingになった形の集合で比較)`);
  for (let i = 0; i < RULES.length; i += 1) {
    for (let j = i + 1; j < RULES.length; j += 1) {
      const a = RULES[i]!;
      const b = RULES[j]!;
      const diff = rows.filter((r) => r.forming[a].join(",") !== r.forming[b].join(","));
      console.log(`- ${a} vs ${b}: ${diff.length} 行`);
    }
  }

  console.log(`\n## 全案で同じになる行を除いた残り`);
  const allSame = rows.filter((r) => {
    const first = r.forming[RULES[0]!].join(",");
    return RULES.every((rule) => r.forming[rule].join(",") === first);
  });
  console.log(`- 全案一致: ${allSame.length} 行 / 残り: ${rows.length - allSame.length} 行`);

  console.log(`\n## 残った行の内訳`);
  for (const row of rows) {
    const first = row.forming[RULES[0]!].join(",");
    if (RULES.every((rule) => row.forming[rule].join(",") === first)) continue;
    const parts = RULES.map((rule) => `${rule}=[${row.forming[rule].join(" ")}]`).join(" / ");
    console.log(`- ${row.kifuId} ply=${row.ply}: ${parts}`);
  }
}

main();
