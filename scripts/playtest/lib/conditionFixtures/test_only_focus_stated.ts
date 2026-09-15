// 試験だけの架空の定義(diagnose.test.ts の D3-COND の子プロセス)。**将棋の判断を含めない。**③の状態の門で判定不能になる行を出すために置く。

import type { ConditionDefinition } from "../condition.js";

const definition: ConditionDefinition = {
  id: "test_only_focus_stated",
  label: "試験だけの③の状態(仮)",
  status: "draft",
  definitionText: "試験だけ。trigger.focus.state を読み、stated なら真",
  uses: ["trigger.focus.state"],
  thresholds: {},
  appliesTo: ["failureEvent", "rise", "maxDropPair"],
  approval: null,
  evaluate: (view) => (view.trigger as { focus: { state: string } }).focus.state === "stated",
};

export default definition;
