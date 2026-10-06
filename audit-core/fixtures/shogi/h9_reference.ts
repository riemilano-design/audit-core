// 監査専用・参照専用。Core も Adapter もこのファイルに依存しない(C-2 決定 8.2)。
//
// C-2 計器 6 の TS 側(audit-core/docs/CORE_CONNECTION_C2_PLAN_2026-10-06.md §5・§6、
// 人間の決定 8.2): 1 顧客フォルダの席の封筒を、将棋側の既存 H-9
// (scripts/playtest/lib/hypothesis.ts の validateHypothesisLine)に**そのまま**掛けて、
// 観測 1 件ごとの判定を書く。将棋側の lib は import するだけで 1 文字も変えない。
//
// seat run の読み方は scripts/playtest/goldenMasterCheck.ts の seat_runs の節と同じ規則
// (ディレクトリを sort、run_summary.json が無ければ飛ばし、
// seat_(gpt|gemini|claude).json だけを sort して拾う)。
//
// H-9 の messages は `${at}: ${message}` の形(例: "observations[3]: value が packet と
// 違う(...)")なので、at で観測に割り付け、message の種類を kind にする:
//   - "value が packet と違う" を含む -> value_mismatch
//   - "数え直し:" で始まる        -> recount(この段では再現しない。C-2 計画 §7)
//   - それ以外の resolve 失敗      -> not_found
//   - 該当する message が無い      -> ok
// 1 つの観測に複数の message が付くことがある(値が違い、かつ数え直しが落ちる場合)ので、
// 優先順位は value_mismatch > recount > not_found とする。
//
// 使い方:
//   npx tsx audit-core/fixtures/shogi/h9_reference.ts \
//     --customer-dir scripts/playtest/out/c5 --seats-dir llm-seats \
//     --packet packet/observation-packet.json --obs-items docs/OBSERVATION_ITEMS.md \
//     --out <path>
//
// **実物(scripts/playtest/out/)では回さない**: 1 回目の計測は司令塔が凍結時点で行う。

import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import { loadObsRegistry, validateHypothesisLine } from "../../../scripts/playtest/lib/hypothesis.js";

const SEAT_FILE_RE = /^seat_(gpt|gemini|claude)\.json$/;

function readJson(filePath: string): unknown {
  return JSON.parse(readFileSync(filePath, "utf-8"));
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function getAt(value: unknown, keys: readonly string[]): unknown {
  let current: unknown = value;
  for (const key of keys) {
    if (current === null || typeof current !== "object") return undefined;
    current = (current as Record<string, unknown>)[key];
  }
  return current;
}

/**
 * hypothesis.ts の private(非 export)な packetRefObservations の再実装。
 * その関数は export されていないので import できない ― ここは独立した再実装であり、
 * hypothesis.ts 自体は読むだけで変更しない。
 */
function packetRefObservationsAt(line: unknown): Array<{ at: string; path: string }> {
  const out: Array<{ at: string; path: string }> = [];
  const collect = (list: unknown, at: string): void => {
    asArray(list).forEach((obs, index) => {
      const p = getAt(obs, ["packetRef", "path"]);
      if (typeof p !== "string") return;
      out.push({ at: `${at}[${index}]`, path: p });
    });
  };
  collect(getAt(line, ["observations"]), "observations");
  asArray(getAt(line, ["counterEvidence", "items"])).forEach((item, index) => {
    collect(getAt(item, ["observations"]), `counterEvidence.items[${index}].observations`);
  });
  return out;
}

type Kind = "ok" | "value_mismatch" | "recount" | "not_found";

function kindOfMessages(texts: readonly string[]): Kind {
  if (texts.length === 0) return "ok";
  if (texts.some((t) => t.includes("value が packet と違う"))) return "value_mismatch";
  if (texts.some((t) => t.startsWith("数え直し:"))) return "recount";
  return "not_found";
}

function opt(args: readonly string[], name: string): string | undefined {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : undefined;
}

function main(argv: readonly string[]): number {
  const customerDir = opt(argv, "customer-dir");
  const seatsDirName = opt(argv, "seats-dir");
  const packetRel = opt(argv, "packet");
  const obsItemsPath = opt(argv, "obs-items");
  const outPath = opt(argv, "out");
  if (!customerDir || !seatsDirName || !packetRel || !obsItemsPath || !outPath) {
    console.error(
      "usage: h9_reference.ts --customer-dir <dir> --seats-dir <name> --packet <rel> --obs-items <path> --out <path>",
    );
    return 2;
  }

  const packetPath = path.join(customerDir, packetRel);
  const packet = readJson(packetPath);
  const registry = loadObsRegistry(obsItemsPath);

  const seatsDir = path.join(customerDir, seatsDirName);
  const runIds = existsSync(seatsDir)
    ? readdirSync(seatsDir)
        .filter((name) => statSync(path.join(seatsDir, name)).isDirectory())
        .sort()
    : [];

  const observations: Array<{ id: string; path: string; ok: boolean; kind: Kind }> = [];

  for (const runId of runIds) {
    const runDir = path.join(seatsDir, runId);
    const summaryPath = path.join(runDir, "run_summary.json");
    if (!existsSync(summaryPath)) continue;
    const summary = readJson(summaryPath) as { today?: unknown };
    const today = String(summary.today);
    const seatFiles = readdirSync(runDir).filter((name) => SEAT_FILE_RE.test(name)).sort();
    for (const seatFile of seatFiles) {
      const envelope = readJson(path.join(runDir, seatFile)) as { items?: unknown[] };
      const items = Array.isArray(envelope.items) ? envelope.items : [];
      for (const line of items) {
        const hypothesisId = String((line as { hypothesisId?: unknown } | null)?.hypothesisId);
        const results = validateHypothesisLine(line, { today, registry, packet });
        const h9 = results.find((r) => r.check === "H-9");
        const messages = h9?.messages ?? [];
        for (const { at, path: obsPath } of packetRefObservationsAt(line)) {
          const prefix = `${at}: `;
          const texts = messages.filter((m) => m.startsWith(prefix)).map((m) => m.slice(prefix.length));
          const kind = kindOfMessages(texts);
          observations.push({
            id: `${runId}/${seatFile}#${hypothesisId}/${at}`,
            path: obsPath,
            ok: kind === "ok",
            kind,
          });
        }
      }
    }
  }

  const out = {
    tool: "h9_reference",
    observations,
    tally: {
      total: observations.length,
      ok: observations.filter((o) => o.ok).length,
      by_kind: observations.reduce<Record<string, number>>((acc, o) => {
        acc[o.kind] = (acc[o.kind] ?? 0) + 1;
        return acc;
      }, {}),
    },
  };
  writeFileSync(outPath, JSON.stringify(out, null, 1), "utf-8");
  console.log(JSON.stringify({ total: out.tally.total, by_kind: out.tally.by_kind }, null, 1));
  console.log("written:", outPath);
  return 0;
}

process.exit(main(process.argv.slice(2)));
