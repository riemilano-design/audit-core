// packet の中の場所(packetRef.path)の**文法** ― 1 か所だけに置く(司令塔の条件 2026-09-30、STEP R2 §8 の 1)。
//
// 読む側: R1 の render(lib/seatInput.ts、集計の列 `aggregates.<id>`)・R2 の封筒の検査 E-4・H-2 の分岐(lib/hypothesis.ts)・
//   自動化レーンの検証器 H-9(実在の照合)。**文法を 2 つ作らない。**
// 【この module は packet を読まない】observationPacket*.ts を import しない。path が packet に実在するかは H-9 の仕事。
// 【文法】
//   集計: `aggregates.<id>.numerator` / `aggregates.<id>.denominator`(分数の行)/ `aggregates.<id>.value`(単独の数の行)。
//     **数ごとに 1 つの参照**(司令塔の決定 2026-09-30: `aggregates.<id>` 単独は受けない ― 単独だと分子と分母のどちらを引いたかが
//     決まらず、H-9 の照合が「どこかに同じ数が在れば通る」P-178 の型に戻る)。id は packet の aggregates[].id そのまま(`.` を含む)。
//   事実: `facts.<列>[添字]` に `.欄名`(と添字)が 1 つ以上続く(`facts.branches[12].topGapCp`・`facts.recognition.rows[3].selfSignature`)。
//   `facts.games[]`(添字なし)は節の見出しの書き方であって観測の参照ではない ― 参照は 1 つの値を指す。

export const PACKET_OBS_ID_PREFIX = "packet." as const;

export const PACKET_FACTS_COLUMNS = ["games", "moves", "engine", "time", "branches", "collapse", "recognition"] as const;

export const AGGREGATE_PARTS = ["numerator", "denominator", "value"] as const;
export type AggregatePart = (typeof AGGREGATE_PARTS)[number];
export const AGGREGATE_REF_RE = /^aggregates\.[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*\.(?:numerator|denominator|value)$/;
/**
 * 事実の参照は **列の直後に添字**(`facts.time[3].midSpentSec`)。列は配列なので、添字の無い `facts.time.bySpent[3]` は
 * packet の形に無い書き方として文法で落ちる(recognition だけ `rows` / `definitions` の下が配列)。値の実在はやはり見ない。
 */
export const FACTS_REF_RE = /^facts\.(?:(?:games|moves|engine|time|branches|collapse)|recognition\.(?:rows|definitions))\[\d+\](?:\.[A-Za-z0-9_]+(?:\[\d+\])?)+$/;

/** 集計の**数**の参照(render がこの形で写し、席がそのまま packetRef.path に使う)。分数は numerator / denominator、単独の数は value */
export function aggregateRef(id: string, part: AggregatePart): string {
  return `aggregates.${id}.${part}`;
}

/** path が文法に合わなければ 1 行(合えば空)。**実在は見ない。** */
export function packetRefPathProblems(path: unknown): string[] {
  if (typeof path !== "string" || path.length === 0) return ["packetRef.path が文字列でない・空"];
  if (AGGREGATE_REF_RE.test(path) || FACTS_REF_RE.test(path)) return [];
  return [`packetRef.path「${path}」が文法(aggregates.<id>.numerator|denominator|value / facts.<列>[添字].欄名)に合わない`];
}

/** packet の場所を指す obsId(`packet.` + path)。登録簿でなく文法で見る(H-2 の分岐) */
export function packetObsIdOf(path: string): string {
  return `${PACKET_OBS_ID_PREFIX}${path}`;
}

export function isPacketObsId(obsId: unknown): obsId is string {
  return typeof obsId === "string" && obsId.startsWith(PACKET_OBS_ID_PREFIX);
}
