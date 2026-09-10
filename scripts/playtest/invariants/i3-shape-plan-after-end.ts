// I-3(矛盾、draft): 終局後(status.isEnd)に、道のり・目標形の組み上がり・候補手・
// 参考の弱点・方向の注記などが残ったまま表示される状態を検出する。
//
// 出典: docs/PLAYTEST_LOOP_PROPOSAL.md P-6、STEP 4-5 完了記録の X-1・W-1(回帰確認)。
//
// 計画書の例外: I-3のみphase:"ready"・"immediate"の両方を検査する
// (終局時はwebがimmediateをそのまま表示し続けるため)。

import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-3";

interface CheckItem {
  name: string;
  triggered: boolean;
  detail: string;
}

function buildCheckItems(record: RecordLine): CheckItem[] {
  const { plan } = record.response;
  return [
    {
      name: "routes",
      triggered: plan.routes.length > 0,
      detail: `routes.length = ${plan.routes.length}`,
    },
    {
      name: "targetShapeProgress",
      triggered: plan.targetShapeProgress !== null,
      detail: `targetShapeProgress = ${plan.targetShapeProgress?.shapeId ?? "null"}`,
    },
    {
      name: "resolvedTargetShapeId",
      triggered: plan.resolvedTargetShapeId !== null,
      detail: `resolvedTargetShapeId = ${plan.resolvedTargetShapeId}`,
    },
    {
      name: "nextConsiderations",
      triggered: plan.nextConsiderations.length > 0,
      detail: `nextConsiderations.length = ${plan.nextConsiderations.length}`,
    },
    {
      name: "candidateMove",
      triggered: plan.candidateMove?.status === "ready",
      detail: `candidateMove.status = ${plan.candidateMove?.status ?? "undefined"}`,
    },
    {
      name: "shapeWeakness",
      triggered: plan.shapeWeakness !== null,
      detail: `shapeWeakness = ${plan.shapeWeakness?.shapeId ?? "null"}`,
    },
    {
      name: "directionNote",
      triggered: plan.directionNote !== null,
      detail: `directionNote = ${plan.directionNote ?? "null"}`,
    },
  ];
}

export const i3ShapePlanAfterEnd: Invariant = {
  id: ID,
  title: "終局後に道のり・組み上がり・候補手などが残ったまま表示される",
  type: "矛盾",
  status: "draft",
  source: "docs/PLAYTEST_LOOP_PROPOSAL.md P-6、STEP 4-5 完了記録 X-1・W-1",
  check(records: RecordLine[]): Finding[] {
    const findings: Finding[] = [];
    for (const record of records) {
      if (!record.response.status.isEnd) continue;
      for (const item of buildCheckItems(record)) {
        if (!item.triggered) continue;
        findings.push({
          invariantId: ID,
          kifuId: "",
          ply: record.ply,
          phase: record.phase,
          condition: item.name,
          detail: `終局後(phase: ${record.phase})に ${item.name} が残っています(${item.detail})。`,
          sfen: record.sfen,
          senteMove: record.senteMove,
          goteMove: record.goteMove,
        });
      }
    }
    return findings;
  },
};
