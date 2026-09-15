// 試験だけの架空の定義(lib/condition.test.ts の K-8 で loadCondition を当てる)。**将棋の判断を含めない。**本番の定義の置き場(lib/conditions/)には置かない。

import type { ConditionDefinition } from "../condition.js";

const definition: ConditionDefinition = {
  id: "test_only_loadable",
  label: "試験だけの読み込み(仮)",
  status: "draft",
  definitionText: "試験だけ。counterfactual.state を読み、compared なら真",
  uses: ["counterfactual.state"],
  thresholds: {},
  appliesTo: ["failureEvent"],
  approval: null,
  evaluate: (view) => (view.counterfactual as { state: string }).state === "compared",
};

export default definition;
