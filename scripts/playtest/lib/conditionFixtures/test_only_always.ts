// 試験だけの架空の定義(diagnose.test.ts の D3-COND の子プロセスと lib/conditionReport.test.ts)。**将棋の判断を含めない。**本番の定義の置き場(lib/conditions/)には置かない。

import type { ConditionDefinition } from "../condition.js";

const definition: ConditionDefinition = {
  id: "test_only_always",
  label: "試験だけのいつも該当(仮)",
  status: "draft",
  definitionText: "試験だけ。counterfactual.state を読み、いつも真",
  uses: ["counterfactual.state"],
  thresholds: {},
  appliesTo: ["failureEvent", "rise", "maxDropPair"],
  approval: null,
  evaluate: () => true,
};

export default definition;
