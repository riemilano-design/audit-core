// D-2b-1(audit-core/docs/CLAIM_DECOMPOSITION_D2B1_PLAN_2026-10-08.md §3(c)・§7 決-2・決-3)。
// `runClaimDecomposer.ts` に足した CLI の旗(`--only`・`--max-retries`・`--attempt-timeout-ms`)の純粋関数、
// および `productionConfigOf` → `assertPricesPresent` の結線(前回の監査が D-2b の GO に付けた必須項目)を試験する。
//
// 【このファイルが import するだけでは `main()` を実行しない】`numericArg`・`selectGoldFixtures` はどちらも
// `process.argv`・`.env`・fetch を読まない純粋関数。`main` も import するだけでは走らない(ファイル末尾が
// `import.meta.url` の一致を見る isMainModule guard のため)。
// 【決-3 の試験だけは `main` を直接呼ぶ】ただし鍵は使わない ― `.env` を読ませず(`--env` に存在しないパスを渡す)、
// 単価・鍵・モデル名の環境変数は試験の中で差し替える(`withIsolatedEnv`)。単価が欠けている(または両方そろって
// いても鍵が無い)ケースは **`assertPricesPresent`(または次の鍵チェック)で投げて `runOneConfig` に届く前に
// 終わる** ので、fetch は一度も呼ばれない(本番の配線には入らない)。
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { ENV_NAMES } from "./lib/env.js";
import { main, numericArg, selectGoldFixtures } from "./runClaimDecomposer.js";

describe("numericArg(--max-retries・--attempt-timeout-ms の読み取り)", () => {
  it("旗が無ければ undefined(既定の挙動のまま)", () => {
    expect(numericArg(["--out-dir", "x"], "max-retries")).toBeUndefined();
  });
  it("数の文字列を読む", () => {
    expect(numericArg(["--max-retries", "0"], "max-retries")).toBe(0);
    expect(numericArg(["--attempt-timeout-ms", "900000"], "attempt-timeout-ms")).toBe(900_000);
  });
  it("数にならない値は投げる(黙って既定値に落とさない)", () => {
    expect(() => numericArg(["--max-retries", "abc"], "max-retries")).toThrow(/数ではない/);
  });
  it("値が次の旗(次が `--` から始まる)なら無い扱いで undefined", () => {
    // argOf と同じ約束(値が省略されて次の旗が続く形)。数のつもりで次の旗の名前を拾わない。
    expect(numericArg(["--max-retries", "--out-dir"], "max-retries")).toBeUndefined();
  });
});

describe("selectGoldFixtures(--only <goldId>)", () => {
  const golds = [{ id: "gold-01" }, { id: "gold-02" }, { id: "gold-03" }];
  it("onlyId が undefined なら全部をそのまま返す(既定の挙動のまま)", () => {
    expect(selectGoldFixtures(golds, undefined)).toEqual(golds);
  });
  it("一致する 1 本だけに絞る", () => {
    expect(selectGoldFixtures(golds, "gold-02")).toEqual([{ id: "gold-02" }]);
  });
  it("一致するものが無ければ投げる(黙って 0 本で回さない)", () => {
    expect(() => selectGoldFixtures(golds, "gold-99")).toThrow(/gold-99 に一致する gold が無い/);
  });
  it("投げた理由に、ある id の一覧を含む(原因を追いやすくする)", () => {
    expect(() => selectGoldFixtures(golds, "gold-99")).toThrow(/gold-01, gold-02, gold-03/);
  });
});

describe("main を import しても実行されない(isMainModule guard)", () => {
  it("main が関数としてだけ import できる(呼んでいないので .env・fetch に触れない)", () => {
    expect(typeof main).toBe("function");
  });
});

// ---------------------------------------------------------------------------
// D-2b-1 §7 決-3(司令塔の判断で範囲を追加): `productionConfigOf` → `assertPricesPresent` の結線を直接試験する。
// 前回の監査(CLAIM_DECOMPOSITION_D2B_PLAN_2026-10-07.md §7 条件 2)が「任意ではなく必須」とした項目で、
// 決-2(`main` の argv 化・isMainModule guard)で `main` が呼べるようになったので、ここで初めて満たす。
//
// 守る約束は 2 つ。
//   (1) 単価が欠けていたら `main()` は送る前に投げる ― 入力側だけ・出力側だけ・両方、の 3 通り全部。
//       (前回の監査が独立に当てた変異「`productionConfigOf` の `||` を `&&` に変える」は、片方だけ欠けた
//       ケースを黙らせる ― その変異をこの 3 通りで赤くする。)
//   (2) `assertPricesPresent` の呼び出しが `main()` の経路に実在する ― 引数を `[]` に差し替える変異・
//       呼び出しごと消す変異のどちらも、単価が欠けているのに「単価が .env に無い」で投げなくなるので、
//       (1) の 3 通りの試験がそのまま赤くなる(別の試験を新設しなくても同じ検査で捕まる)。
// ---------------------------------------------------------------------------
describe("D-2b-1 §7 決-3: productionConfigOf → assertPricesPresent の結線", () => {
  // 鍵・単価・モデル名の環境変数は試験の前後で保存・復元する(ambient な process.env を汚さない・実鍵を拾わない)。
  const ISOLATED_ENV_KEYS = [
    "DECOMPOSE_PROVIDER", "DECOMPOSE_COST_CAP_USD",
    ENV_NAMES.prices.gpt[0], ENV_NAMES.prices.gpt[1],
    ENV_NAMES.keys.openai, ENV_NAMES.models.gpt, ENV_NAMES.inputLimits.gpt,
  ] as const;

  async function withIsolatedEnv(overrides: Record<string, string>, fn: () => Promise<void>): Promise<void> {
    const saved = new Map<string, string | undefined>();
    for (const k of ISOLATED_ENV_KEYS) saved.set(k, process.env[k]);
    try {
      for (const k of ISOLATED_ENV_KEYS) delete process.env[k];
      for (const [k, v] of Object.entries(overrides)) process.env[k] = v;
      await fn();
    } finally {
      for (const k of ISOLATED_ENV_KEYS) {
        const prev = saved.get(k);
        if (prev === undefined) delete process.env[k]; else process.env[k] = prev;
      }
    }
  }

  /** main() に渡す argv。--env は存在しないパス(本物の .env を読ませない)。--out-dir は使い捨ての一時 dir。 */
  function argvWith(outDir: string): string[] {
    return ["--out-dir", outDir, "--env", path.join(outDir, "no-such.env")];
  }

  it("入力側の単価だけ欠けると、main() は送る前に「単価が .env に無い」で投げる", async () => {
    const outDir = mkdtempSync(path.join(tmpdir(), "d2b1-prices-"));
    try {
      await withIsolatedEnv({ DECOMPOSE_PROVIDER: "gpt", DECOMPOSE_COST_CAP_USD: "1", [ENV_NAMES.prices.gpt[1]]: "30" }, async () => {
        await expect(main(argvWith(outDir))).rejects.toThrow(/単価が .env に無い/);
      });
    } finally {
      rmSync(outDir, { recursive: true, force: true });
    }
  });

  it("出力側の単価だけ欠けると、main() は送る前に「単価が .env に無い」で投げる", async () => {
    const outDir = mkdtempSync(path.join(tmpdir(), "d2b1-prices-"));
    try {
      await withIsolatedEnv({ DECOMPOSE_PROVIDER: "gpt", DECOMPOSE_COST_CAP_USD: "1", [ENV_NAMES.prices.gpt[0]]: "5" }, async () => {
        await expect(main(argvWith(outDir))).rejects.toThrow(/単価が .env に無い/);
      });
    } finally {
      rmSync(outDir, { recursive: true, force: true });
    }
  });

  it("両方の単価が欠けると、main() は送る前に「単価が .env に無い」で投げる", async () => {
    const outDir = mkdtempSync(path.join(tmpdir(), "d2b1-prices-"));
    try {
      await withIsolatedEnv({ DECOMPOSE_PROVIDER: "gpt", DECOMPOSE_COST_CAP_USD: "1" }, async () => {
        await expect(main(argvWith(outDir))).rejects.toThrow(/単価が .env に無い/);
      });
    } finally {
      rmSync(outDir, { recursive: true, force: true });
    }
  });

  it("両方の単価がそろっていれば assertPricesPresent は投げず、次の門(鍵が無い)まで進む(結線が実在する証拠)", async () => {
    // 単価が無いときの「単価が .env に無い」ではなく、単価チェックの次にある「鍵かモデル名が .env に無い」で
    // 投げる ― assertPricesPresent を素通りした(= 呼ばれて、かつ正しく判定した)ことの裏返しの確認。
    const outDir = mkdtempSync(path.join(tmpdir(), "d2b1-prices-"));
    try {
      await withIsolatedEnv({ DECOMPOSE_PROVIDER: "gpt", DECOMPOSE_COST_CAP_USD: "1", [ENV_NAMES.prices.gpt[0]]: "5", [ENV_NAMES.prices.gpt[1]]: "30" }, async () => {
        await expect(main(argvWith(outDir))).rejects.toThrow(/鍵かモデル名が .env に無い/);
      });
    } finally {
      rmSync(outDir, { recursive: true, force: true });
    }
  });
});
