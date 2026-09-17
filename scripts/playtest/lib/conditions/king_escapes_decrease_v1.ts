// 【判断的知識・approved】条件式の定義 C-1「逃げ道が減る」。
// 人間の承認: 2026-09-17(STEP D3-COND 計画 §13 の選択肢 (a)。司令塔 e3 が候補を起こし、人間が承認)。
// 文の訂正(同日、司令塔 e3。監査 f2 の事前読み D-1): 比べる局面は「5 手の後」ではなく comparedPlies 手の後(最大 6 手、読み筋が短ければその長さ)。evaluate・uses は変えていない(§14)。
// 定義の文・閾値・読む欄を変えるときは、新しい id(v2)の別ファイルにし、このファイルは変えない(definitionSha256 が記録と結びついているため)。
import type { ConditionDefinition } from "../condition.js";

interface View {
  counterfactual: { kingEscapesRoot: { count: number }; actual: { kingEscapesEnd: { count: number } } };
}

const definition: ConditionDefinition = {
  id: "king_escapes_decrease_v1",
  label: "逃げ道が減る(仮)",
  status: "approved",
  definitionText:
    "自分の手から、実戦と読み筋を比べられた手数(自分の手を含めて最大 6 手。読み筋が短いときはその長さに合わせる)だけ実戦を進めた局面で、先手玉の逃げ道の数(手番を先手にして先手玉を動かせる合法手の数。駒を取る手を含む)が、自分の手の前の局面の逃げ道の数より少ない。",
  readableText: "自分の手から数手(読み筋と比べられた手数で、最大 6 手)進めた局面で、自分の玉が動ける先の数が、その手の前より減ったかどうかを見ています。",
  uses: ["counterfactual.kingEscapesRoot.count", "counterfactual.actual.kingEscapesEnd.count"],
  thresholds: {},
  appliesTo: ["failureEvent", "rise", "maxDropPair", "pair"],
  approval: {
    approvedBy: "人間(司令塔 e3 の候補 C-1 を、選択肢 (a) として承認)",
    date: "2026-09-17",
    record: "docs/STEP_D3-COND_PLAN_2026-09-15.md §13(候補の起こし)・§14(承認と実装の記録)",
  },
  evaluate: (view) => {
    const { counterfactual } = view as unknown as View;
    return counterfactual.actual.kingEscapesEnd.count < counterfactual.kingEscapesRoot.count;
  },
};
export default definition;
