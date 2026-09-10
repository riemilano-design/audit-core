// I-4(矛盾、draft): 選択中の目標形(resolvedTargetShapeId)が、既に完成した形
// (referenceShapesのstatus:"completed")の真の祖先へ戻っている状態を検出する
// (「もう出来ている、より進んだ形」があるのに、その手前の形をなお目標として
// 示し続けている)。
//
// 出典: docs/PLAYTEST_LOOP_PROPOSAL.md P-1、STEP 4-1 完了記録(everCompletedShapeIdsと
// 同じ考え方の回帰確認)。
//
// 祖先関係の出所: referenceShapesにはparentShapeIdが無いため、
// apps/server/src/analysis/shapeRepository.ts の getShapes() (data/shapes/*.json の
// 記述的データ)から ShapeDefinition.id -> parent_shape_id のマップを1回組み立てて使う。
// これは検査対象の判定ロジック(本番のresolveRecognizedDirection等)ではなく、
// 形の親子関係という記述的データを読むだけであり、本番の判定関数は呼ばない
// (検査対象の判定を、その判定自身で検査しないため)。

import { getShapes } from "../../../apps/server/src/analysis/shapeRepository.js";
import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-4";

function buildParentMap(): Map<string, string | null> {
  const map = new Map<string, string | null>();
  for (const shape of getShapes()) {
    map.set(shape.id, shape.parent_shape_id);
  }
  return map;
}

/** xがyの真の祖先(x !== y)かどうかを、yから親をたどって判定する。
 * たどる途中でマップに無いshapeIdに当たったら判定不能として false を返す
 * (計画書「マップに無い shapeId は祖先判定不能として Finding にしない」)。 */
function isTrueAncestor(x: string, y: string, parentOf: Map<string, string | null>): boolean {
  if (x === y) return false;
  let current: string = y;
  while (parentOf.has(current)) {
    const parent = parentOf.get(current);
    if (parent === null || parent === undefined) return false;
    if (parent === x) return true;
    current = parent;
  }
  return false;
}

function completedShapeIdsInRecord(record: RecordLine): string[] {
  return record.response.plan.referenceShapes.filter((s) => s.status === "completed").map((s) => s.shapeId);
}

export const i4CompletedShapeStillTargeted: Invariant = {
  id: ID,
  title: "既に完成した形の祖先を、なお目標形として示し続けている",
  type: "矛盾",
  status: "draft",
  source: "docs/PLAYTEST_LOOP_PROPOSAL.md P-1、STEP 4-1 完了記録",
  check(records: RecordLine[]): Finding[] {
    const parentOf = buildParentMap();
    const findings: Finding[] = [];
    const everCompletedShapeIds = new Set<string>();

    for (const record of records) {
      if (record.phase !== "ready") continue;

      const x = record.response.plan.resolvedTargetShapeId;
      const currentCompleted = completedShapeIdsInRecord(record);

      if (x !== null) {
        const candidateYs = new Set<string>([...currentCompleted, ...everCompletedShapeIds]);
        for (const y of candidateYs) {
          if (!isTrueAncestor(x, y, parentOf)) continue;
          findings.push({
            invariantId: ID,
            kifuId: "",
            ply: record.ply,
            phase: record.phase,
            condition: `${x}<-${y}`,
            detail: `目標形が "${x}" のままですが、より進んだ形 "${y}" が既に完成しています("${x}" は "${y}" の祖先です)。`,
            sfen: record.sfen,
            senteMove: record.senteMove,
            goteMove: record.goteMove,
          });
        }
      }

      for (const y of currentCompleted) everCompletedShapeIds.add(y);
    }

    return findings;
  },
};
