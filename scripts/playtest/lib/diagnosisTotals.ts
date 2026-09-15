// STEP D3(docs/STEP_D3_PLAN_2026-09-14.md 6. の Q-5)。diagnose.ts の入力ごとの分母の行(lib/failureEvent.ts の
// DiagnosisRow)を、群(B の 10 本・B′ の 10 本)ごとに足す。**手で足さない**ためのもの。
//
// 【このファイルがやること】
// - 数えた入力の DiagnosisCounts を欄ごとに足す。**欄の一覧は COUNT_KEYS の 1 か所**で、DiagnosisCounts に欄が
//   増えたのに足し忘れると型検査で落ちる(satisfies)
// - 数えられなかった入力を、合計に混ぜずに名前で並べる(黙って 0 として足さない)
// - 急落候補の欄は、D1 と同じく「比べた組が 1 つも無ければ 0 ではなく『比べる組が無い』」(dropCountCell を共有する)
//
// 【このファイルが絶対にやらないこと】
// - 合計から「どちらの群が多い」を言うこと(計画 5. の L-7)。件数を並べるだけ
// - 死因のタグ・閾値を変えること

import { dropCountCell, type DiagnosisCounts, type DiagnosisRow } from "./failureEvent.js";

/** 足す欄。DiagnosisCounts の欄と過不足なく一致しないと型検査で落ちる。 */
const COUNT_KEYS = {
  readyRows: true,
  measured: true,
  notMeasuredGameEnd: true,
  notMeasuredInCheck: true,
  notMeasurable: true,
  unrecorded: true,
  notEvaluation: true,
  comparedPairs: true,
  mateAfterPairs: true,
  notComparedPairs: true,
  dropCandidates: true,
  matedIfPassPairs: true,
  events: true,
  fromAdvantage: true,
  withCheck: true,
  withMate: true,
  windowShort: true,
  beforeAfterPassMate: true,
  beforeDropCpAtLeast: true,
  cause1Draft: true,
} satisfies Record<keyof DiagnosisCounts, true>;

export interface DiagnosisTotals {
  /** 合計に入れた入力の kifuId(入力の順)。 */
  counted: string[];
  /** 数えられなかったので合計に入れなかった入力の kifuId(入力の順)。 */
  notCounted: string[];
  /** STEP D0-SIDE 段 1(R-9)。error 行を持つので合計に入れなかった入力の kifuId(入力の順)。 */
  excluded: string[];
  /** 数えた入力が 1 つも無ければ null(0 の合計と区別する)。 */
  counts: DiagnosisCounts | null;
}

export function totalDiagnosisCounts(rows: readonly DiagnosisRow[]): DiagnosisTotals {
  const counted: string[] = [];
  const notCounted: string[] = [];
  const excluded: string[] = [];
  let counts: DiagnosisCounts | null = null;
  for (const row of rows) {
    if (row.result.kind === "excluded") {
      excluded.push(row.kifuId);
      continue;
    }
    if (row.result.kind !== "counted") {
      notCounted.push(row.kifuId);
      continue;
    }
    counted.push(row.kifuId);
    const rowCounts = row.result.counts;
    if (counts === null) {
      counts = { ...rowCounts };
      continue;
    }
    for (const key of Object.keys(COUNT_KEYS) as (keyof DiagnosisCounts)[]) {
      counts[key] += rowCounts[key];
    }
  }
  return { counted, notCounted, excluded, counts };
}

/**
 * 入力が 2 つ以上のときだけ、合計の節を返す(1 つなら入力ごとの表と同じなので出さない)。
 * 表の欄は renderDiagnosisReport の 2 つの表と同じ並び。
 */
export function renderDiagnosisTotals(rows: readonly DiagnosisRow[]): string[] {
  if (rows.length < 2) return [];
  const totals = totalDiagnosisCounts(rows);
  const lines: string[] = [];
  lines.push(`## 合計(入力 ${rows.length} 本。数えた ${totals.counted.length} 本・数えられなかった ${totals.notCounted.length} 本・error 行のため使わなかった ${totals.excluded.length} 本)`);
  lines.push("");
  lines.push("- 数えた入力の件数を欄ごとに足したもの。**群の差として読まない**(局どうしの揺れと分けられない)");
  for (const kifuId of totals.notCounted) {
    lines.push(`- 合計に入れなかった入力(数えられなかった): ${kifuId}`);
  }
  for (const kifuId of totals.excluded) {
    lines.push(`- 合計に入れなかった入力(error 行のため使わない): ${kifuId}`);
  }
  lines.push("");
  const c = totals.counts;
  if (c === null) {
    lines.push("- 数えた入力が無い");
    lines.push("");
    return lines;
  }
  lines.push("| ready 行 | 測った | 測らない(終局) | 測らない(王手中) | 測れなかった | 測っていない | 評価値でない(cp の絶対値 ≥ 30000) | 比べた組 | 直後が mate の組 | 比べられなかった組 |");
  lines.push("|---|---|---|---|---|---|---|---|---|---|");
  lines.push(
    `| ${c.readyRows} | ${c.measured} | ${c.notMeasuredGameEnd} | ${c.notMeasuredInCheck} | ${c.notMeasurable} | ${c.unrecorded} | ${c.notEvaluation} | ${c.comparedPairs} | ${c.mateAfterPairs} | ${c.notComparedPairs} |`,
  );
  lines.push("");
  const drop = (value: number) => dropCountCell(c, value);
  lines.push(
    "| 急落候補 | うち直前が優勢 | うち窓の中に王手 | うち窓の中に詰み | うち窓が足りない | うち直前 afterPass.mate > 0 | うち直前 dropCp ≥ 300 | 直後にパスすると詰まされる読み | Failure Event | 死因①(draft) |",
  );
  lines.push("|---|---|---|---|---|---|---|---|---|---|");
  lines.push(
    `| ${drop(c.dropCandidates)} | ${drop(c.fromAdvantage)} | ${drop(c.withCheck)} | ${drop(c.withMate)} | ${drop(c.windowShort)} | ${drop(c.beforeAfterPassMate)} | ${drop(c.beforeDropCpAtLeast)} | ${c.matedIfPassPairs} | ${c.events} | ${c.cause1Draft} |`,
  );
  lines.push("");
  return lines;
}
