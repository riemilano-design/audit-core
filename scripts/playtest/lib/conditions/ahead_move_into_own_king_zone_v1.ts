// 【判断的知識・approved】条件式の定義 C-5「優勢のとき自玉のそばへ動かす」。
// 人間の承認: 2026-09-21(人間が「判定にかけるかどうか」を司令塔 e3 に任せ、司令塔が判定にかけると決めた。STEP D3-COND 計画 §13 の候補 C-5・§15)。
// 定義の文・閾値・読む欄を変えるときは、新しい id(v2)の別ファイルにし、このファイルは変えない(definitionSha256 が記録と結びついているため)。
import type { ConditionDefinition } from "../condition.js";

interface View {
  standingPair: { before: string };
  counterfactual: { actual: { userMoveFacts: { toInOwnKingZone: boolean } } };
}

const definition: ConditionDefinition = {
  id: "ahead_move_into_own_king_zone_v1",
  label: "優勢のとき自玉のそばへ動かす(仮)",
  status: "approved",
  definitionText:
    "自分の手の前の局面の形勢の区分が優勢(評価値 +300 以上)で、かつ、自分の手を指した後の局面で、その手の行き先の升が先手玉のまわり(指した後の玉の升と、その周囲 8 升のうち盤の中にある升)に入っている。打つ手も含む。玉を動かす手は、行き先が動いた後の玉の升そのものなので、必ず区域に含まれて該当する。",
  readableText: "形勢が優勢のときに、自分の手の行き先が自分の玉のまわりの升に入ったか(打つ手も含む)を見ています。",
  uses: ["standingPair.before", "counterfactual.actual.userMoveFacts.toInOwnKingZone"],
  thresholds: {},
  appliesTo: ["rise", "maxDropPair", "pair"],
  approval: {
    approvedBy: "司令塔 e3(人間が 2026-09-21 に判定するかどうかを司令塔へ任せ、司令塔が判定にかけると決めた。候補 C-5)",
    date: "2026-09-21",
    record: "docs/STEP_D3-COND_PLAN_2026-09-15.md §15",
  },
  evaluate: (view) => {
    const { standingPair, counterfactual } = view as unknown as View;
    return standingPair.before === "ahead" && counterfactual.actual.userMoveFacts.toInOwnKingZone === true;
  },
};
export default definition;
