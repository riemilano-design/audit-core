// STEP U6-O(え): U6-M が測った材料(PvMaterials)から、日本語の文を組み立てる純粋関数。
// docs/STEP_U6-O_PLAN_2026-09-13.md に従う。
//
// 【この関数が絶対にやらないこと】
// - 「得」「損」「有利」「不利」「互角」を使う。差引きの合計を述べる
//   (captureSummary.ts 冒頭の人間承認済みの制約)。
// - 持ち駒の増減(材料4)を文にする(同じ制約の理由に当たる。buildSlot3 の注記)。
// - 場所を言う(設計書3.1。解説文の67.0%が場所に言及しない)。手は符号が担う。
// - 固定した分類へ当てはめる(設計書5.1。人間が明確に否定)。
// - 読み筋そのものを見せる・順位や評価値や記号を付ける(設計書12.)。
// - エンジン・LLMに依存する(決定的な純粋関数)。
//
// 【本番には出さない】
// この関数は画面にもAPIにも出さない((か) U6-Q の仕事)。本番から呼ばれる経路も
// 作らない。「測れるようにする」と「本番で効くようにする」は別の作業である。
//
// 【3種類の「無い」を潰さない(規則11.6)】
// 入力の `PvMaterialsResult` は「測れなかった(insufficient)」「途中まで測った
// (truncatedAtPly)」「測って無かった(材料がnull)」を別々に運んでくる。U6-M は
// 「nullを『無い』と読み替えるのは文を組み立てる段の責任」と明記して渡している。
// **この関数は materials だけを受け取らない。** usablePlies と truncatedAtPly を
// 必ず一緒に見るため、PvMaterialsResult 全体を受け取る。
// 返り値も3値の直和型にする。文字列1本で返すと、空文字列が3種類の「無い」を
// すべて背負う。

import type { Role } from "shogiops/types";
import type { PvMaterials, PvMaterialsResult, PvRoleCounts } from "./pvMaterials.js";
import { roleToJapanese } from "./pieceMapping.js";

/** スロット1(誰が動くか)に割り当てられた材料。材料1・2。 */
export type Slot1Material = "firstCapture" | "firstContactPly";
/** スロット2(何が起きるか)に割り当てられた材料。材料6・7・8・9・10。 */
export type Slot2Material =
  | "firstCheck"
  | "firstPromotion"
  | "bishopExchangePly"
  | "firstDrop"
  | "kingMovePlies";
/**
 * スロット3(そのあとどうなるか)に割り当てられた材料。材料3・5・11・12。
 *
 * **材料4(handDelta)はここに無い。文にしない**(2026-09-13。独立監査 2 回目を受けた
 * 司令塔の決定)。型から外したので、`use.slot3` に書けば tsc が止める
 * (効かない指定を静かに受け付けない)。理由は buildSlot3 の注記。
 */
export type Slot3Material =
  | "capturedRoles"
  | "kingNeighborDelta"
  | "advanceRetreat"
  | "slidingReachDelta";

/**
 * 文の組み立て方の規則。**判断的知識なので既定値を置かない**
 * (CLAUDE.md ルール4。PvMaterialRules と同じ形)。
 *
 * 既定値を置くと、規則が確定していないのに黙って1つの規則で動くことになる
 * (U6-F の directionRule が「計測用としてのみ存在し本番から到達できなかった」件と
 * 同じ轍を踏まない)。指定を忘れれば tsc が止まる。
 */
export interface SentenceRules {
  /**
   * 攻め/受けをどう決めるか。設計書4.1:
   * 「読み筋の中で最初に駒を取ったのがどちらか」。**未確定。測ってから確定する。**
   */
  initiative: "first_capture";
  /**
   * 「起きなかった」と言ってよい最小の再生手数。
   * **これを下回る場合、材料がnullでも「無かった」とは言わない**(測れる長さが
   * 無かっただけかもしれないため)。**何手あれば言えるかは判断的知識であり、
   * ここでは決めない。**
   * **読み筋が打ち切られていれば、手数に関わらず「無かった」とは言わない**(計画書 18.)。
   */
  minPliesForAbsence: number;
  /**
   * どの材料を文にするか(取捨)。**判断的知識なので既定値を置かない。**
   * 司令塔はスロットへの割り当て(どの材料がどのスロットか)を型から決めたが、
   * **取捨は決めていない。**
   */
  use: {
    slot1: readonly Slot1Material[];
    slot2: readonly Slot2Material[];
    slot3: readonly Slot3Material[];
  };
}

export type PvSentenceResult =
  /**
   * 測っていない・測れなかった。**「起きなかった」ではない。**
   * - `pv_too_short`: 読み筋が短くて材料を測れなかった
   * - `too_few_plies_for_absence`: 最後まで再生できたが、「無かった」と言えるだけの手数が無い
   * - `pv_truncated`: 読み筋が途中で打ち切られており、読めなかった続きがある。**手数が足りていても
   *   「無かった」とは言わない**(2026-09-13 の司令塔の決定。計画書 18.)
   */
  | { kind: "not_measured"; reason: "pv_too_short" | "too_few_plies_for_absence" | "pv_truncated" }
  /** 測ったが、文にする材料が1つも立たなかった。 */
  | { kind: "no_material" }
  /** 文が組み立てられた。**sentences は必ず1つ以上**(空配列を「無い」に使わない)。 */
  | { kind: "text"; sentences: readonly [string, ...string[]] };

/** 駒種の並びを入力の順序に依存させない(決定的にする)ための固定順。 */
function sortedRoles(counts: Map<Role, number>): Role[] {
  return [...counts.keys()].filter((role) => (counts.get(role) ?? 0) > 0).sort();
}

/**
 * 駒種の日本語名。**対応表に無い駒種では null を返し、呼び出し側はその節を出さない**
 * (pieceMapping.ts の義務「未対応の駒種は null を返す(呼び出し側は駒種を述べない)」)。
 * 英語の駒種名で埋めない。
 *
 * いま材料が渡してくる駒種は、すべて成っていない駒種であり、null には到達しない
 * (捕獲は元の駒種に正規化・成りは成る前の駒種・打つ駒は持ち駒。pvMaterials.test.ts の
 * 材料3・7・9)。**到達しないことと、到達したときに英語が出ないことの両方を試験で押さえる。**
 */
function jp(role: Role): string | null {
  return roleToJapanese(role);
}

/**
 * スロット1: 誰が動くか(材料1・2)。
 *
 * 【肯定の文と否定の文を分ける(2026-09-13。計画書 18.)】
 * - 「こちらから仕掛けていく」「相手から攻めてくる」は**起きたことを言う肯定の文**。再生できた
 *   範囲で起きた最初の捕獲は、残りの手を足しても最初の捕獲のままなので**単調**。打ち切りでも使う
 * - 「駒はぶつかりますが、取り合いにはならない」「しばらく駒はぶつからない」は**不在を言う否定の文**。
 *   **否定の文は、範囲が読む人に見えない限り、残りの手で覆る**(「しばらく」も範囲の長さを言わない)。
 *   したがって `canAssertAbsence`(無かったと言える手数を再生でき、**かつ打ち切られていない**)
 *   のときだけ出す
 * 当初は「しばらくぶつからない」を単調として打ち切りでも使っていたが、**誤りだった**
 * (打ち切りとみなした 13 回中 13 回、読み筋全体では接触か捕獲があった。計画書 18.)。
 *
 * 【打ち切られていない読み筋の否定の文は、暫定で残している(2026-09-13。計画書 18.7.2)】
 * 読み筋の終わりも読む人には見えない。打ち切りで外した理由(範囲が読む人に見えない)は、ここにも当たる。
 * **正しいから残しているのではない。** いまは画面に出ていない(どこからも呼ばれていない)ので、
 * 露出の量と沈黙の増え方を見てから決める。門: (1) U6-T の段 A で読み筋の長さの分布が出たら見直す
 * (2) (か)で文を画面に出す前に、否定の文をスロット1 に残すかを必ず決める。決めないまま画面に出さない。
 */
function buildSlot1(m: PvMaterials, rules: SentenceRules, canAssertAbsence: boolean): string | null {
  const useCapture = rules.use.slot1.includes("firstCapture");
  const useContact = rules.use.slot1.includes("firstContactPly");

  if (useCapture && m.firstCapture !== null) {
    return m.firstCapture.byUs
      ? "こちらから仕掛けていく流れになりそうです。"
      : "相手から攻めてくる流れになりそうです。";
  }
  // **firstContactPly は 0 が「root で既にぶつかっている」を意味する。**
  // `if (m.firstContactPly)` と書くと 0 が null と同じ扱いになり、
  // 「既にぶつかっている」が「起きなかった」に化ける(pvMaterials.ts の注意書き)。
  if (useContact && m.firstContactPly !== null) {
    // 後半の「取り合いにはならない」は不在を言う。言えないときは、この文ごと出さない
    // (前半だけを言う文言は作らない。文言の決定になるため)。
    return canAssertAbsence ? "駒はぶつかりますが、取り合いにはならない流れになりそうです。" : null;
  }
  // ここへ来るのは「使うと指定された材料がすべて null」のときだけ。
  // **十分な手数を再生できていない、または打ち切られていれば、無かったとは言わない。**
  if (useCapture && useContact && canAssertAbsence) {
    return "しばらく駒はぶつからない流れになりそうです。";
  }
  return null;
}

/**
 * スロット2: 何が起きるか(材料6・7・8・9・10)。読み筋の一点で起きる出来事。
 *
 * 打ち切りでも使う。どれも「起きた」ことを言う文で、再生できた範囲で起きた出来事は
 * 残りの手を足しても起きたままなので**単調**である。
 */
function buildSlot2(m: PvMaterials, rules: SentenceRules): string | null {
  const use = rules.use.slot2;
  const clauses: string[] = [];

  if (use.includes("firstCheck") && m.firstCheck !== null) clauses.push("王手がかかる");
  if (use.includes("firstPromotion") && m.firstPromotion !== null) {
    const name = jp(m.firstPromotion.role);
    if (name !== null) clauses.push(`${name}が成る`);
  }
  if (use.includes("bishopExchangePly") && m.bishopExchangePly !== null) clauses.push("角を交換する");
  if (use.includes("firstDrop") && m.firstDrop !== null) {
    const name = jp(m.firstDrop.role);
    if (name !== null) clauses.push(`${name}を打つ`);
  }
  if (use.includes("kingMovePlies") && (m.kingMovePlies.us.length > 0 || m.kingMovePlies.opponent.length > 0)) {
    clauses.push("玉が動く");
  }
  if (clauses.length === 0) return null;
  return `途中で、${clauses.join("、")}、といった流れになりそうです。`;
}

/**
 * 取った駒の描き方。**差引きの合計は述べない**(captureSummary.ts の制約)。
 *
 * 【打ち切りのとき、片側の言い方を出さない(2026-09-13。計画書 18.7.1)】
 * 「○の取り合いになる」は、再生できた範囲で両方が取ったという**肯定の事実**なので、残りの手で覆らない。
 * 「こちらが○を取る」「相手が○を取る」は、**相手側がその駒を取っていないという不在の判定**で言い方を
 * 選んでいる。**文字列は肯定でも、どちらの言い方になるかは不在で決まる**ので、打ち切りでは覆りうる
 * (模擬で 2,738 回中 563 回、読み筋全体では相手側も同じ駒を取っていた)。形態素では拾えない否定である。
 * 新しい文言は作らず、節を落とすだけにする。
 */
function capturedClauses(counts: PvRoleCounts, truncated: boolean): string[] {
  const ours = new Set(sortedRoles(counts.us));
  const theirs = new Set(sortedRoles(counts.opponent));
  const clauses: string[] = [];
  for (const role of [...new Set([...ours, ...theirs])].sort()) {
    const name = jp(role);
    if (name === null) continue;
    if (ours.has(role) && theirs.has(role)) clauses.push(`${name}の取り合いになる`);
    else if (truncated) continue;
    else if (ours.has(role)) clauses.push(`こちらが${name}を取る`);
    else clauses.push(`相手が${name}を取る`);
  }
  return clauses;
}

/**
 * スロット3: そのあとどうなるか(材料3・5・11・12)。
 * 一点ではなく、通した結果として残るもの。
 *
 * 【材料4(持ち駒の増減)は文にしない(2026-09-13。独立監査 2 回目を受けた司令塔の決定)】
 * 材料4 は「取ると +1・打つと −1」の符号付きの和で、値の意味は「末端の持ち駒 − root の
 * 持ち駒」である。captureSummary.ts 冒頭の人間承認済みの理由 ―「持ち駒の枚数は、打った駒が
 * 差し引かれるため、取った事実の集約にならない」― にそのまま当たる(字面ではなく理由に反する)。
 * 取った事実は材料3 が言うので、材料4 が足すのは差し引きだけである。
 * 例: 歩 +1・角 −1 のとき持ち駒の総数は同じなのに「こちらの持ち駒が増える」と言ってしまう。
 * **材料4 を数えること(U6-M)は変えない。文から外すだけである。**
 * **文に戻すなら、この人間承認済みの理由との関係を人間に確認すること**(委任の範囲外になりうる)。
 *
 * 【打ち切り(truncated)のとき ― 残りの手で覆りうる材料を外す。基準は「単調かどうか」】
 * - 材料3 のうち「○の取り合いになる」は、両方が取ったという肯定の事実で**単調**。使う
 * - 材料3 のうち片側の言い方(「こちらが○を取る」「相手が○を取る」)は、**相手側が取っていないという
 *   不在の判定**で言い方を選ぶので覆りうる。出さない(capturedClauses の注記。計画書 18.7.1)
 * - 材料5・12(root と末端の差)は、末端が変われば変わる。外す
 * - 材料11(前に出た手と引いた手の比較)は、残りの手で逆転する。外す
 * - スロット3 の節に、否定の形の文字列は無い(文字列リテラルを全部拾って確かめた。計画書 18.)。
 *   ただし片側の言い方は、文字列が肯定でも不在の判定で選ばれていた(上の 2 つ目。18.7.1)
 * 当初の決定(Q3 = (b))は「末端に依存する材料だけを外す」で、材料11 は線全体の集計なので
 * 残していた。**集計であっても、比較は覆る。** 独立監査 2 回目の実測(完全に再生できた
 * 136 本の前半を打ち切りとみなした 1,946 組)で、「前に出る/引く」は 1,817 件中 68 件が
 * 全体では向きが違った(材料3 は 5,390 件中 0 件)。基準を書き直した(計画書 17.1)。
 *
 * 【打ち切り時に数を出さない(人間承認済みの条件)】
 * 打ち切られた読み筋の集計は「**少なくともそれだけ起きた**」であって
 * 「**それで全部**」ではない。「歩を1枚取り合う」と書くと1枚で終わったと読める ―
 * 断定できないことを断定することになる(CLAUDE.md ルール6)。
 * **材料3 は数を出さず、有無だけを述べる**(節を見よ)。数を出すのは材料5(「○枚減る」)
 * だけで、それは打ち切り時に外れる。**したがって条件は構造的に満たされている。**
 * 将来ここへ数を足すなら、打ち切り時に落とす仕掛けを同時に入れること(試験が押さえている)。
 */
function buildSlot3(m: PvMaterials, rules: SentenceRules, truncated: boolean): string | null {
  const use = rules.use.slot3;
  const clauses: string[] = [];

  // 材料3 は打ち切りでも使う。ただし片側の言い方は、不在の判定に依るので capturedClauses が落とす。
  if (use.includes("capturedRoles")) clauses.push(...capturedClauses(m.capturedRoles, truncated));
  // 以下の 3 つ(5・11・12)は残りの手で覆りうるので、打ち切られた読み筋では使わない。
  if (!truncated && use.includes("kingNeighborDelta")) {
    const d = m.kingNeighborDelta.us;
    if (d < 0) clauses.push(`玉の周りの駒が${-d}枚減る`);
    else if (d > 0) clauses.push(`玉の周りの駒が${d}枚増える`);
  }
  if (!truncated && use.includes("advanceRetreat")) {
    // 数えた値どうしの比較だけを行う(閾値を置かない)。
    const { up, down } = m.advanceRetreat.us;
    if (up > down) clauses.push("こちらの駒が前に出る");
    else if (down > up) clauses.push("こちらの駒が引く");
  }
  if (!truncated && use.includes("slidingReachDelta")) {
    const { us, opponent } = m.slidingReachDelta;
    if (us > opponent) clauses.push("こちらの駒の動ける範囲が広がる");
    else if (opponent > us) clauses.push("相手の駒の動ける範囲が広がる");
  }

  if (clauses.length === 0) return null;
  return `そのあと、${clauses.join("、")}、といった形になりそうです。`;
}

/**
 * 材料から文を組み立てる。**決定的**(同じ入力からは常に同じ結果)。
 *
 * - スロット1 = 「誰が」「いつ始まるか」を定める材料(1・2)
 * - スロット2 = **一点の出来事**(ply を持つ / ply の並び。6・7・8・9・10)
 * - スロット3 = **一点ではなく、通した結果として残るもの**(3・5・11・12)
 * - 材料4 は文にしない(buildSlot3 の注記)
 *
 * 【3 つの別々の基準(2026-09-13。「唯一の判定基準」を取り消した)】
 * 当初「ply を保つか、数へ畳むか」を 3 分類の唯一の判定基準と書いたが、**誤りだった。**
 * それは二値の基準で、3 つには分けられない。割り当てと打ち切りの扱いは、次の 3 つで決まる。
 *
 * 1. **スロット2 と 3 の境: ply を保つか、ply を捨てて数へ畳むか。** 材料10 は
 *    `push(step.ply)` で ply を保つので一点の出来事の並び、材料3・11 は数へ畳むので
 *    線全体の量である。「ループ内かどうか」では分かれない(10 も 11 も再生ループの中で積む)。
 * 2. **スロット1: 意味の基準 ―「始まりを定める」。** 材料1・2 も ply を保つので、1. の基準
 *    だけで分けるとスロット2 に入る。スロット1 を分けているのは initiative の規則であり、
 *    **判断的知識で、未確定である**(`SentenceRules.initiative`)。
 *    **したがって「型から決めるので将棋の判断を持ち込まない」という保証は、スロット1 には効かない。**
 * 3. **打ち切り: 単調かどうか。** 残りの手で覆りうる材料(5・11・12)と、**不在を言う否定の文**
 *    (スロット1 の 2 文)と、**不在の判定で言い方を選ぶ節**(材料3 の片側の言い方)を外す
 *    (buildSlot1・capturedClauses・buildSlot3 の注記)。**否定の文は、範囲が読む人に見えない限り、
 *    覆りうる側に入る**(2026-09-13 に足した。計画書 18.・18.7.1)。
 *
 * 【2026-09-13 の訂正】当初は「スロット3 = root と末端の差」としていたが、**誤りだった。**
 * 材料3(capturedRoles)・材料4(handDelta)・材料11(advanceRetreat)は
 * pvMaterials.ts の再生ループの中で increment / += 1 される**線全体の集計**であり、
 * root と末端の差ではない(差なのは材料5・12 だけ)。材料11 はこの訂正で
 * スロット2 からスロット3 へ移した。**戻り値の形(Map か number か)が同じでも、
 * 積み上げか差分かは別である**(規則 11.1 と同じ型の誤り。詳細は計画書 12.)。
 */
export function buildPvSentences(result: PvMaterialsResult, rules: SentenceRules): PvSentenceResult {
  if (result.kind === "insufficient") {
    return { kind: "not_measured", reason: "pv_too_short" };
  }

  const truncated = result.truncatedAtPly !== null;
  // 「無かった」と言えるのは、言えるだけの手数を再生でき、**かつ読めなかった続きが無い**ときだけ
  // (否定の文は範囲が読む人に見えない限り覆る。計画書 18.)。
  const canAssertAbsence = result.usablePlies >= rules.minPliesForAbsence && !truncated;

  const sentences: string[] = [];
  const s1 = buildSlot1(result.materials, rules, canAssertAbsence);
  if (s1 !== null) sentences.push(s1);
  const s2 = buildSlot2(result.materials, rules);
  if (s2 !== null) sentences.push(s2);
  const s3 = buildSlot3(result.materials, rules, truncated);
  if (s3 !== null) sentences.push(s3);

  const [first, ...rest] = sentences;
  if (first === undefined) {
    // 1文も立たなかった。**「言うことが無い」と「言えるだけ測れていない」を分ける。**
    // 打ち切りと手数不足は、別の理由として返す(同じ値に 2 種類の「無い」を背負わせない。規則 11.6)。
    if (canAssertAbsence) return { kind: "no_material" };
    return { kind: "not_measured", reason: truncated ? "pv_truncated" : "too_few_plies_for_absence" };
  }
  return { kind: "text", sentences: [first, ...rest] };
}
