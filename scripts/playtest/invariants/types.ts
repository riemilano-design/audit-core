// 不変条件(draft)の共通の型。docs/PLAYTEST_LOOP_PROPOSAL.md 4.3・4.4・4.5・STEP T-2計画書。
//
// 【このファイルがやること】
// - Invariant / Finding / RecordLine の型定義だけ。判定ロジックは各 i*.ts に置く。
// - statusは"draft" | "approved"のリテラル型を定義するが、本STEPで作る5件は
//   すべて"draft"。"approved"にする操作は人間承認事項であり、このファイル自体には
//   "approved"の値を一切書かない(4.5 規則1)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・評価・閾値・文言。
// - 本番の型(apps/server/src/api/stateResponse.ts)の複製・改変。ここでは import する
//   だけで、必要最小の追加型(RecordLine等、JSONLの入れ物)のみを新設する。

import type { StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";

/** docs/PLAYTEST_LOOP_PROPOSAL.md 4.4 の6型。 */
export type InvariantType = "沈黙" | "矛盾" | "断定" | "未説明用語" | "盤との不一致" | "陳腐化";

/** 4.5の概念の境界: draft(AIが自由に追加してよい) / approved(人間だけが有効化する)。
 * 本STEPで作る5件はすべてdraft(コードにapprovedの値は書かない)。 */
export type InvariantStatus = "draft" | "approved";

/** T-1のJSONLの"kind":"record"行(1行分)。replay.ts / scripts/playtest/README.md の
 * JSONL形式そのまま。responseはbuildStateResponseWithPlanの戻り値そのまま。 */
export interface RecordLine {
  kind: "record";
  ply: number;
  sfen: string;
  senteMove: string | null;
  goteMove: string | null;
  phase: "immediate" | "ready";
  elapsedMs: number;
  response: StateResponseBodyWithPlan;
}

/** T-1のJSONLの"kind":"meta"行(先頭行)。 */
export interface MetaLine {
  kind: "meta";
  kifuId: string;
  startedAt: string;
  gitHead: string | null;
  enginePath: string;
}

/** 不変条件1件が検出した1件分。束ねる単位は(invariantId, condition)。 */
export interface Finding {
  invariantId: string;
  /** どの入力ファイル(run)由来か。check.ts が実際のkifuIdへ上書きする
   * (各invariantの check() はファイルをまたいだ文脈を持たないため)。 */
  kifuId: string;
  ply: number;
  phase: "immediate" | "ready";
  /** 束ねるための識別子。既存のkind / notReadyReason / shapeIdのような値だけを使い、
   * 新しい語は作らない(計画書「実装してよい範囲」の制約)。 */
  condition: string;
  /** 検出内容を人が読める形で1〜2文にしたもの。将棋の評価語は含めない。 */
  detail: string;
  sfen: string;
  senteMove: string | null;
  goteMove: string | null;
}

/** 不変条件(draft)1件。真偽を返す決定的な関数(check)を持つだけで、
 * LLM・エンジンの新規呼び出しは行わない(既存の本番関数のimportのみ許可)。 */
export interface Invariant {
  id: string;
  title: string;
  type: InvariantType;
  status: InvariantStatus;
  /** この不変条件がどの観測・既知事項に由来するか(計画書の表の"source"列)。 */
  source: string;
  /** 1つのrun(1つのJSONLファイル由来のrecord行、ply昇順)に対して真偽判定を行い、
   * 検出をFinding[]で返す。kifuIdはcheck.ts側で確定させるため、ここでは
   * 空文字列を入れておく(check.ts が上書きする)。 */
  check(records: RecordLine[]): Finding[];
}
