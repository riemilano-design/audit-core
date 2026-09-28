// STEP ANSWER 作業(docs/STEP_ANSWER_PLAN_2026-09-23.md §2.3・§3)。B(「どうしたら」の冊子)の
// 行動のメニュー(条件 → 行動)を TS の定数にする。判断的知識(§3 の表)の正本は docs §3、ここはその写し
// (findingTexts.ts と同じ形。試験(answerMenu.test.ts)が docs との一致(id・行動の文の芯・minN)を確かめる)。
//
// 【このファイルがやること】
// - ANSWER_MENU: docs §3 の表 8 行(M1〜M8)をそのまま写した定数(id・段階・行動の文の芯・根拠の数の名・
//   minN・答え合わせの数の名)。文言はここが正本ではなく docs §3 の引用。
// - menuConditionHoldsOf(id, materials): 「出す条件」(§3 の「出す条件」列)を、道具が計算した事実(材料)から
//   判定する純粋関数。材料の形(AnswerMenuMaterials)はこの STEP の実装担当の判断(計画は「JSON の値で判定する
//   純粋関数」とだけ書き、材料の形までは決めていない)。
// - answerMenuDenominatorOf(id, materials): 検査 5(数が足りなければ言わない)で見る「根拠の数の分母」。
//   `minN` と比べる相手の数(§3 の「根拠の数」列に対応する分母 1 つ)。
//
// 【司令塔の事前監査 REVISE(2026-09-23、コミット前)を反映した点】
// - M4(側の一致)は、whatif-v2 jsonl の position 行(`scenes.fork` が true)の `candidates[0].side`・
//   `actualSide`(`lib/whatif.ts` の `sideOf` がすでに計算した値。tags を書き写して再計算しない)から、
//   check_answer.py が「第 1 候補が攻め(both を含む)のうち実戦も攻め(both を含む)」「…守り…」の 2 分数を
//   数える(`AnswerMenuSideMatch`)。この TS 側は、その 2 分数を材料として受け取り、条件(両方とも 70% 未満。
//   実装担当の判断 ― §3 は「両方同様」とだけ書き AND/OR を決めていないため、より条件の厳しい AND を選んだ)
//   を判定するだけ(fitz・jsonl の読み書きは python 側)。
// - M1(時間)は、STEP ANSWER 追加作業 ANSWER-M1(docs/STEP_ANSWER_PLAN_2026-09-23.md §7)で `needsData` を解消した。
//   `lib/reportData.ts` の `PatientPhaseSpent.midOver`(局ごとの中盤 1 手あたり秒が閾値(TIME_VALUES.quickSec)を
//   超えた局の数)を `AnswerMenuPatientGroup` の `midOverGames`・`midOverOver`・`midOverOverAndTimeUpLoss` として
//   受け取り、3 分の組(min3)で `timeUpLosses.n ≥ 2` かつ `midOverOver ≥ 5` を条件、`midOverOver` を分母にする(§7.2)。
// - M6(捨て駒)は、司令塔が書いた B v3(2026-09-24)の校正材料で数え方が確認された(実例: 57 のうち 17)ため、
//   `tagCrossTable.sacrifice` の行合計(実戦側の印が 0 個/複数個の局面で理論上は過不足がありうるが、v3 の実例で
//   実際に使われた数え方)を分母、対角(`sacrifice`×`sacrifice`)を分子にして判定する(`AnswerMenuReadCombined`)。
//   検査 1(数の照合)の「同じ組」にも同じ行合計/対角を登録する(司令塔の指示 6・v3 の「書いた側の記録」)。
// - M3・M5 の「序盤の消費」「afterLongThink」は、docs §3 がどの組(3 分・10 分のどちらか、または限定なし)を
//   指すか明記していない。**渡された patient の中で min3(タグ付け。下記)があればそれ、無ければ先頭の組**
//   (primaryGroupOf)を使う(実装担当の判断)。
// - 「3 分の組」「10 分の組」の見分け方は、patient_report_data.json 自体に時間設定の欄が無いため、
//   check_answer.py の `--time-limit-sec`(patient ごと)で 180 秒 = min3、600 秒 = min10 とタグ付けする
//   (実装担当の判断。他の秒数はタグ無し = 条件判定に使えない)。**同じタグの patient が複数渡されたら
//   (前回 20 局 + 今回 14 局 = 3 分の組)、python 側が合算(分子・分母を別々に)してから 1 つの
//   `AnswerMenuPatientGroup` にする**(司令塔の指示 1。TS 側はすでに合算された 1 組ずつを受け取るだけ)。
//
// 【追加作業 ANSWER-MENU2(2026-09-24、docs §8)を反映した点】
// - `AnswerMenuItem.verifyGate`(答え合わせの下限。§8.1): M1 だけが持つ(`midOver.overAndTimeUpLoss / midOver.over
//   ≥ 1/2`)。`menuVerifyGateHoldsOf(id, materials)` は、`verifyGate` が null の項目(M1 以外)は常に true を返す
//   (§8.4 の指示どおり)。
// - M9(§8.2): `AnswerMenuPatientGroup` に `timeUpLossMidSecs`(min3 の組の、時間負けの局の
//   `perGame[i].midSec` を連結した配列)と `otherGamesMidMedian`(`phaseSpent.otherGames.mid`)を足した。
//   **§8 が決めていない点(実装担当の判断、報告に明記)**: 「同じタグ(min3)の patient が複数(前回 20 局 +
//   今回 14 局)あるとき、中央値をどう扱うか」を §8 は決めていない。この実装では、`otherGamesMidMedian` は
//   既存の `phaseSpentOtherMidMedian` と同じ「合算した組の中で games が最も少ないファイル(primary)の中央値」
//   を代表値として使う(`primaryGroupOf`・`CombinedGroup` の既存の考え方の延長。§8 の「組ごとに自分の組の
//   中央値と比べ、判定は組ごとの結果の AND」は、この代表値 1 つに対して `timeUpLossMidSecs`(連結した配列。
//   複数ファイルにまたがる時間負け局をすべて含む)の**全部**が上回るかを見ることで実現する ― 個々のファイルを
//   それぞれ独立に判定して真偽値を AND するのではなく、代表の中央値 1 つに対する「すべて」判定 1 回に
//   まとめている。今回の実データでは時間負けの局数が少ない(3 局)ため、この近似による違いは実測では出ない
//   と考えるが、複数ファイルの中央値が大きく食い違う入力では厳密な意味論とは一致しない可能性がある)。
//   `foundInSameData: true`(今回の対局から見つけた読みのため、B の文に句を必須にする。検査は python 側)。
// - docs §3 の表は司令塔がこの REVISE の内容(M1・M8 の minN 等)に合わせて書き直す途中のため、
//   `answerMenu.test.ts` の docs 一致試験は **id・段階・minN だけ**にした(行動の文の芯は今回は比べない。
//   司令塔の指示)。M1・M8 の minN は、書き直された docs にまだ合わせられないため、docs 由来ではなく
//   このファイルの値をそのまま確かめる単独の試験にしてある(試験内に「未照合」と明記)。

export type AnswerMenuId = "M1" | "M2" | "M3" | "M4" | "M5" | "M6" | "M7" | "M8" | "M9";

export type AnswerMenuStage = "時間" | "条件" | "否定" | "手順";

/** docs §3 の表 1 行(判断的知識。正本は docs §3、ここはその写し)。 */
export interface AnswerMenuItem {
  id: AnswerMenuId;
  stage: AnswerMenuStage;
  /** 行動(顧客向けの文の芯)。docs §3 の該当列そのまま。 */
  actionCore: string;
  /** 根拠の数(docs §3 の該当列そのまま)。 */
  evidenceName: string;
  /** 検査 5(数が足りなければ言わない)で見る下限。docs §3・§8.2 の minN 列に書かれた数だけを取り出したもの。 */
  minN: number;
  /** 答え合わせの数(docs §3・§8.2 の該当列そのまま)。 */
  verifyName: string;
  /**
   * 答え合わせの下限(docs §8.1)。null の項目は条件だけで出す(今までどおり)。M1 だけが持つ
   * (`{ fraction: "midOver.overAndTimeUpLoss / midOver.over", min: 0.5 }`)。`fraction` は表示・説明用の文字列
   * (正本は docs §8.1)、実際の判定は `menuVerifyGateHoldsOf` の中の id ごとの関数で行う。
   */
  verifyGate: { fraction: string; min: number } | null;
  /**
   * この行動が、今回の対局(patient に渡したデータ)から見つけた読みか(docs §8.2)。true の項目(M9)は、
   * B の印の行に「今回の対局から見つけた読みです」の句を含めなければならない(検査は check_answer.py)。
   */
  foundInSameData: boolean;
}

/** docs/STEP_ANSWER_PLAN_2026-09-23.md §3(M1〜M8)・§8.2(M9)の表 9 行(id の順のまま)。文言の正本は docs。 */
export const ANSWER_MENU: readonly AnswerMenuItem[] = [
  {
    id: "M1",
    stage: "時間",
    actionCore: "3 分切れ負けの中盤は 1 手 4 秒を目安に",
    evidenceName: "中盤 4 秒超の局のうち、持ち時間に到達した局",
    // 司令塔の指示(2026-09-23 REVISE 3): minN は「中盤 4 秒超の局 5 かつ 時間で負けた局 2」の 2 本。
    // この欄は number 型なので、大きい方(5)を代表として持たせる(実装担当の判断)。分母(中盤 1 手あたり
    // 4 秒超の局)は ANSWER-M1(§7.2)で `midOver.over` として出せるようになった。
    minN: 5,
    verifyName: "持ち時間に到達した局の数、中盤 4 秒超の局数",
    // ANSWER-MENU2(§8.1): 4 秒超の局の半分以上が時間負けでなければ、「1 手 4 秒」は時間負けの処方にならない。
    verifyGate: { fraction: "midOver.overAndTimeUpLoss / midOver.over", min: 0.5 },
    foundInSameData: false,
  },
  {
    id: "M2",
    stage: "条件",
    actionCore: "勝ちたい対局は持ち時間の長い形(10 分 + 30 秒)で",
    evidenceName: "両組の崩れ率、持ち時間に到達した局 0",
    minN: 5,
    verifyName: "次の組で持ち時間に到達した局・崩れ率",
    verifyGate: null,
    foundInSameData: false,
  },
  {
    id: "M3",
    stage: "否定",
    actionCore: "序盤を急ぐ必要は数からは出ていない",
    evidenceName: "序盤の崩れ回数、序中の消費中央値",
    minN: 10,
    verifyName: "",
    verifyGate: null,
    foundInSameData: false,
  },
  {
    id: "M4",
    stage: "手順",
    actionCore: "10 秒以上考える局面では、攻めの候補と自玉側の候補を 1 つずつ思い浮かべてから比べる",
    evidenceName: "一致の分数 2 つ",
    minN: 30,
    verifyName: "側の一致率",
    verifyGate: null,
    foundInSameData: false,
  },
  {
    id: "M5",
    stage: "手順",
    actionCore: "長考した次の 1 手は、相手の返しを見てからひと呼吸",
    evidenceName: "afterLongThink の分数",
    minN: 30,
    verifyName: "同じ分数",
    verifyGate: null,
    foundInSameData: false,
  },
  {
    id: "M6",
    stage: "手順",
    actionCore: "攻めの局面で候補を作るとき、駒を捨てる手を 1 つ候補に入れてから比べる",
    evidenceName: "READ の sacrifice の分数",
    minN: 20,
    verifyName: "同じ分数",
    verifyGate: null,
    foundInSameData: false,
  },
  {
    id: "M7",
    stage: "否定",
    actionCore: "深く読む力より、候補を 2 つ並べる手順の方が数に合う",
    evidenceName: "READ の firstVisibleNodes の内訳",
    minN: 30,
    verifyName: "",
    verifyGate: null,
    foundInSameData: false,
  },
  {
    id: "M8",
    stage: "否定",
    actionCore: "終盤の詰将棋より、そこまでに残す時間が先",
    evidenceName: "timeUpLosses の m = n",
    // 司令塔の指示(2026-09-23 REVISE 3): minN は「時間で負けた局 2」(旧: 1)。
    minN: 2,
    verifyName: "",
    verifyGate: null,
    foundInSameData: false,
  },
  {
    id: "M9",
    stage: "時間",
    actionCore: "中盤の消費が自分のふだんの中央値を超えたら、次の手の前に残り時間を見る",
    evidenceName: "持ち時間に到達した局の中盤の消費と、他の局の中央値",
    // docs §8.2: minN は「時間負け 2」。
    minN: 2,
    verifyName: "持ち時間に到達した局のうち中央値超え / 持ち時間に到達した局",
    // docs §8.2: 条件そのものが答え合わせなので null。
    verifyGate: null,
    // docs §8.2: 今回の 44 局から見つけた読み(§7.6)。B に出すときは句が必須(検査は check_answer.py)。
    foundInSameData: true,
  },
] as const;

/** `answer_menu.json` の形(§2.3)。`answerMenu.ts`(CLI)がこのオブジェクトをそのまま JSON にする。 */
export interface AnswerMenuFile {
  items: readonly AnswerMenuItem[];
}

export function buildAnswerMenuFile(): AnswerMenuFile {
  return { items: ANSWER_MENU };
}

// ==================== 条件を判定する材料(実装担当の判断。計画は形までは決めていない) ====================

export interface AnswerMenuTimeUpLosses {
  /** 持ち時間を使い切って負けた局の数(patient.time.timeUpLosses.length)。 */
  n: number;
  /** その局の最後の評価が、すべて +300 以上だったか(n === 0 のときは null ― 比べる材料が無い)。 */
  allAtLeast300: boolean | null;
}

/** 崩れの分数(分子 / 分母)。 */
export interface AnswerMenuRate {
  collapsed: number;
  n: number;
}

/** patient_report_data.json 1 本ぶんの、メニューの条件判定に要る材料だけを抜いたもの。 */
export interface AnswerMenuPatientGroup {
  /** check_answer.py の `--time-limit-sec` で見分けたタグ(180 秒 = min3・600 秒 = min10・他/無指定は null)。 */
  group: "min3" | "min10" | null;
  games: number;
  timeUpLosses: AnswerMenuTimeUpLosses | null;
  /** time.bySpent の 4 段をすべて足した分数(崩れ率の分母。3 分/10 分の組の比較(M2)に使う)。 */
  bySpentTotal: AnswerMenuRate | null;
  /** time.bySpent[0](0〜1 秒)の分数(M5 の比較相手)。 */
  bySpentZeroToOne: AnswerMenuRate | null;
  /** overview.fell(崩れの総数)。 */
  overviewFell: number | null;
  /** overview.early(序盤の崩れ数)。 */
  overviewEarly: number | null;
  /** time.phaseSpent.otherGames.early(中央値)。 */
  phaseSpentOtherEarlyMedian: number | null;
  /** time.phaseSpent.otherGames.mid(中央値)。 */
  phaseSpentOtherMidMedian: number | null;
  /** time.afterLongThink.afterLongThinkAny の分数。 */
  afterLongThinkAny: AnswerMenuRate | null;
  /** time.afterLongThink.quickAfterLongThink の分数(M5 の主語)。 */
  afterLongThinkQuick: AnswerMenuRate | null;
  /** time.phaseSpent.midOver.games(ANSWER-M1、§7.2)。 */
  midOverGames: number | null;
  /** time.phaseSpent.midOver.over(M1 の分母)。 */
  midOverOver: number | null;
  /** time.phaseSpent.midOver.overAndTimeUpLoss。 */
  midOverOverAndTimeUpLoss: number | null;
  /**
   * M9(docs §8.2、ANSWER-MENU2)。この組(タグ)に属する時間負けの局の `phaseSpent.perGame[i].midSec` を
   * 連結した配列(同じタグの patient が複数あれば python 側がファイルの順に連結する)。
   */
  timeUpLossMidSecs: readonly number[];
  /**
   * M9 の比較相手(`phaseSpent.otherGames.mid`、中央値)。同じタグの patient が複数あるときの扱いは
   * §8 が決めていない(実装担当の判断、ファイル冒頭のコメントを参照): `phaseSpentOtherMidMedian` と同じ
   * 代表値(games が最小のファイルの中央値)を使う。
   */
  otherGamesMidMedian: number | null;
}

/**
 * READ(scripts/playtest/read.ts)の summary 行を複数局ぶん合算した材料(M6・M7 用)。
 * `sacrificeRowTotal`・`sacrificeDiagonal`(M6)は、司令塔が書いた B v3(2026-09-24)の実例(57 のうち 17)で
 * 確認された数え方 ― `tagCrossTable.sacrifice`(第 1 候補が捨て駒の行)の「行合計(7 種類の実戦の印の値の和。
 * 1 局面が複数の実戦の印に当たれば複数回数える)」を分母、対角(`tagCrossTable.sacrifice.sacrifice`、
 * 第 1 候補も実戦も捨て駒)を分子とする。
 */
export interface AnswerMenuReadCombined {
  /** 読んだ分かれ道の総数(forkPositionsRead の合算)。 */
  forkPositionsRead: number;
  /** firstVisibleNodesBuckets["none"](100 万ノードまで読んでも 600 に届かなかった数)の合算。 */
  firstVisibleNodesNoneCount: number;
  /** tagCrossTable.sacrifice の行合計(M6 の分母)。 */
  sacrificeRowTotal: number;
  /** tagCrossTable.sacrifice.sacrifice(M6 の分子)。 */
  sacrificeDiagonal: number;
}

/**
 * M4(側の一致)用の 2 分数(司令塔の指示 2)。whatif-v2 jsonl の position 行(`scenes.fork` が true)の
 * `candidates[0].side`・`actualSide`(`lib/whatif.ts` の `sideOf`。both を含む)から、python 側が数える。
 */
export interface AnswerMenuSideMatch {
  /** 第 1 候補が攻め(both を含む)だった局面のうち、実戦の手も攻め(both を含む)だった分数。 */
  attack: AnswerMenuRate;
  /** 第 1 候補が守り(both を含む)だった局面のうち、実戦の手も守り(both を含む)だった分数。 */
  defense: AnswerMenuRate;
  /** `scenes.fork` が true の局面の総数(攻め・守りの重なりを除いた実数。minN の分母)。 */
  forkTotal: number;
}

export interface AnswerMenuMaterials {
  patientGroups: readonly AnswerMenuPatientGroup[];
  readCombined: AnswerMenuReadCombined | null;
  sideMatch: AnswerMenuSideMatch | null;
}

function groupOf(materials: AnswerMenuMaterials, tag: "min3" | "min10"): AnswerMenuPatientGroup | null {
  return materials.patientGroups.find((g) => g.group === tag) ?? null;
}

/** M3・M5 が使う「既定の組」(min3 があればそれ、無ければ先頭の組)。実装担当の判断(上の説明を参照)。 */
function primaryGroupOf(materials: AnswerMenuMaterials): AnswerMenuPatientGroup | null {
  return groupOf(materials, "min3") ?? materials.patientGroups[0] ?? null;
}

function rateOf(rate: AnswerMenuRate | null): number | null {
  if (rate === null || rate.n === 0) return null;
  return rate.collapsed / rate.n;
}

// ---- M1: 時間(ANSWER-M1、§7.2)。3 分の組(min3)で timeUpLosses.n ≥ 2 かつ midOverOver ≥ 5。 ----
function m1Holds(materials: AnswerMenuMaterials): boolean {
  const g = groupOf(materials, "min3");
  if (g === null || g.timeUpLosses === null || g.timeUpLosses.n < 2) return false;
  if (g.midOverOver === null) return false;
  return g.midOverOver >= 5;
}
function m1Denominator(materials: AnswerMenuMaterials): number | null {
  return groupOf(materials, "min3")?.midOverOver ?? null;
}

// ---- M2: 条件 ----
function m2Holds(materials: AnswerMenuMaterials): boolean {
  const min3 = groupOf(materials, "min3");
  const min10 = groupOf(materials, "min10");
  if (min3 !== null && min3.timeUpLosses !== null && min3.timeUpLosses.n >= 1) return true;
  if (min3 === null || min10 === null) return false;
  const rate3 = rateOf(min3.bySpentTotal);
  const rate10 = rateOf(min10.bySpentTotal);
  if (rate3 === null || rate10 === null) return false;
  return rate3 > rate10 * 1.5;
}
function m2Denominator(materials: AnswerMenuMaterials): number | null {
  return groupOf(materials, "min10")?.games ?? null;
}

// ---- M3: 否定(序盤) ----
function m3Holds(materials: AnswerMenuMaterials): boolean {
  const g = primaryGroupOf(materials);
  if (g === null) return false;
  if (g.overviewFell === null || g.overviewFell === 0 || g.overviewEarly === null) return false;
  const earlyShareOk = g.overviewEarly / g.overviewFell <= 0.15;
  if (g.phaseSpentOtherEarlyMedian === null || g.phaseSpentOtherMidMedian === null) return false;
  const earlyLessThanMid = g.phaseSpentOtherEarlyMedian < g.phaseSpentOtherMidMedian;
  return earlyShareOk && earlyLessThanMid;
}
function m3Denominator(materials: AnswerMenuMaterials): number | null {
  return primaryGroupOf(materials)?.overviewFell ?? null;
}

// ---- M4: 手順(側の一致)。司令塔の指示(2026-09-23 REVISE 2): check_answer.py が whatif-v2 jsonl から
// 非対称に数えた 2 分数(AnswerMenuSideMatch。実装担当の判断: §3「両方同様」を、より厳しい AND で判定) ----
function m4Holds(materials: AnswerMenuMaterials): boolean {
  const sm = materials.sideMatch;
  if (sm === null) return false;
  const attackRate = rateOf(sm.attack);
  const defenseRate = rateOf(sm.defense);
  if (attackRate === null || defenseRate === null) return false;
  return attackRate < 0.7 && defenseRate < 0.7;
}
function m4Denominator(materials: AnswerMenuMaterials): number | null {
  return materials.sideMatch?.forkTotal ?? null;
}

// ---- M5: 手順(長考の次) ----
function m5Holds(materials: AnswerMenuMaterials): boolean {
  const g = primaryGroupOf(materials);
  if (g === null) return false;
  const quickRate = rateOf(g.afterLongThinkQuick);
  const zeroToOneRate = rateOf(g.bySpentZeroToOne);
  if (quickRate === null || zeroToOneRate === null) return false;
  return quickRate >= zeroToOneRate * 2;
}
function m5Denominator(materials: AnswerMenuMaterials): number | null {
  return primaryGroupOf(materials)?.afterLongThinkQuick?.n ?? null;
}

// ---- M6: 手順(捨て駒)。B v3(2026-09-24、司令塔)の実例で確認された数え方(上の AnswerMenuReadCombined の
// コメントを参照): tagCrossTable.sacrifice の行合計を分母、対角を分子にする。 ----
function m6Holds(materials: AnswerMenuMaterials): boolean {
  const r = materials.readCombined;
  if (r === null || r.sacrificeRowTotal < 20) return false;
  return r.sacrificeDiagonal / r.sacrificeRowTotal < 0.4;
}
function m6Denominator(materials: AnswerMenuMaterials): number | null {
  return materials.readCombined?.sacrificeRowTotal ?? null;
}

// ---- M7: 否定(読みの深さ) ----
function m7Holds(materials: AnswerMenuMaterials): boolean {
  const r = materials.readCombined;
  if (r === null || r.forkPositionsRead === 0) return false;
  const atLeast600 = r.forkPositionsRead - r.firstVisibleNodesNoneCount;
  return atLeast600 <= 0.4 * r.forkPositionsRead;
}
function m7Denominator(materials: AnswerMenuMaterials): number | null {
  return materials.readCombined?.forkPositionsRead ?? null;
}

// ---- M8: 否定(終盤より時間) ----
function m8Holds(materials: AnswerMenuMaterials): boolean {
  const g = groupOf(materials, "min3") ?? primaryGroupOf(materials);
  return g !== null && g.timeUpLosses !== null && g.timeUpLosses.n >= 1 && g.timeUpLosses.allAtLeast300 === true;
}
function m8Denominator(materials: AnswerMenuMaterials): number | null {
  const g = groupOf(materials, "min3") ?? primaryGroupOf(materials);
  return g?.timeUpLosses?.n ?? null;
}

// ---- M9: 時間(中盤の消費の合計。docs §8.2、ANSWER-MENU2)。3 分の組(min3)で timeUpLosses.n ≥ 2 かつ、
// 時間で負けた局のすべての midSec が otherGamesMidMedian を超える(ファイル冒頭のコメントの実装担当の判断)。 ----
function m9Holds(materials: AnswerMenuMaterials): boolean {
  const g = groupOf(materials, "min3");
  if (g === null || g.timeUpLosses === null || g.timeUpLosses.n < 2) return false;
  if (g.otherGamesMidMedian === null) return false;
  if (g.timeUpLossMidSecs.length === 0) return false;
  return g.timeUpLossMidSecs.every((sec) => sec > g.otherGamesMidMedian!);
}
function m9Denominator(materials: AnswerMenuMaterials): number | null {
  return groupOf(materials, "min3")?.timeUpLosses?.n ?? null;
}

const HOLDS: Record<AnswerMenuId, (materials: AnswerMenuMaterials) => boolean> = {
  M1: m1Holds,
  M2: m2Holds,
  M3: m3Holds,
  M4: m4Holds,
  M5: m5Holds,
  M6: m6Holds,
  M7: m7Holds,
  M8: m8Holds,
  M9: m9Holds,
};

const DENOMINATORS: Record<AnswerMenuId, (materials: AnswerMenuMaterials) => number | null> = {
  M1: m1Denominator,
  M2: m2Denominator,
  M3: m3Denominator,
  M4: m4Denominator,
  M5: m5Denominator,
  M6: m6Denominator,
  M7: m7Denominator,
  M8: m8Denominator,
  M9: m9Denominator,
};

// ==================== 答え合わせの下限(verifyGate。docs §8.1) ====================

// id ごとの verifyGate 判定関数(verifyGate を持つ id だけ)。M1 以外は ANSWER_MENU 側で verifyGate が null
// なので menuVerifyGateHoldsOf が呼ぶ前に true を返す(この Record には登場しない)。
function m1VerifyGateHolds(materials: AnswerMenuMaterials): boolean {
  const g = groupOf(materials, "min3");
  if (g === null || g.midOverOver === null || g.midOverOver === 0 || g.midOverOverAndTimeUpLoss === null) return false;
  return g.midOverOverAndTimeUpLoss / g.midOverOver >= 0.5;
}

const VERIFY_GATE_HOLDS: Partial<Record<AnswerMenuId, (materials: AnswerMenuMaterials) => boolean>> = {
  M1: m1VerifyGateHolds,
};

export class AnswerMenuError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AnswerMenuError";
  }
}

/** id の「出す条件」(§3)が、渡された材料で成り立つか。 */
export function menuConditionHoldsOf(id: AnswerMenuId, materials: AnswerMenuMaterials): boolean {
  const fn = HOLDS[id];
  if (fn === undefined) throw new AnswerMenuError(`知らない id: ${id}`);
  return fn(materials);
}

/** id の「根拠の数」の分母(検査 5(§2.1 の 5)。minN と比べる相手)。測れなければ null。 */
export function answerMenuDenominatorOf(id: AnswerMenuId, materials: AnswerMenuMaterials): number | null {
  const fn = DENOMINATORS[id];
  if (fn === undefined) throw new AnswerMenuError(`知らない id: ${id}`);
  return fn(materials);
}

/**
 * id の答え合わせの下限(docs §8.1)が、渡された材料で成り立つか。`verifyGate` が null の項目は常に true
 * (docs §8.4 の指示どおり)。
 */
export function menuVerifyGateHoldsOf(id: AnswerMenuId, materials: AnswerMenuMaterials): boolean {
  const item = ANSWER_MENU.find((entry) => entry.id === id);
  if (item === undefined) throw new AnswerMenuError(`知らない id: ${id}`);
  if (item.verifyGate === null) return true;
  const fn = VERIFY_GATE_HOLDS[id];
  if (fn === undefined) throw new AnswerMenuError(`verifyGate はあるが判定関数が無い: ${id}`);
  return fn(materials);
}
