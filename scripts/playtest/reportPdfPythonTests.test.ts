// 既知事項 P-113 を塞ぐ。**`report-pdf/` の python の試験を、2 本の門の下に入れる。**
//
// 【なぜ要るか】`report-pdf/*_test.py` は 2026-09-28 まで **`git grep` で参照 0 件**だった ―
// 2 本の門(`npx vitest run --root scripts/playtest`・`npm run typecheck:scripts`)はどちらも
// python を見ないので、**`check_answer.py` の検査 1〜7(顧客に出る文と数の照合そのもの)を壊しても
// 門は緑のまま通っていた。**門を 3 本目にすると 2 本を覚える運用(RUNBOOK)を全部書き直すことになるため、
// **`vitest` の中から回す**(門は 2 本のまま。司令塔の判断)。
//
// 【一覧は書き写さない。ただし道具に並べさせて人が差分を承認する】
// 試験のファイルは **`readdirSync` で見つける**。一覧を手で書くと、5 本目を足したときに黙って外れる
// (`LANE_AUTOMATION_LOG` §40 と同じ型 ― 手で並べた一覧は代表だけになる)。
// **しかし「本数の床」だけでは「1 本消して 1 本足す」が通る**(既知事項 P-117。2026-09-28 の監査が
// 「実在するギャップ」と判定)。そこで **2 つを重ねる**:
//   (a) **名前の集合のスナップショット** ― 集合が変われば**赤**になり、人が `-u` で意図的に更新する。
//       **消して足す形も捕まる。**「手で並べた一覧」とは違い、**並べるのは道具で、人は差分を承認するだけ**
//       (司令塔の判断 2026-09-28: 「§40 で捨てたのは手で並べた一覧。スナップショットは同じものではない」)。
//   (b) **本数の床** ― スナップショットを誤って空で更新する事故の下限として残す。
//
// 【静かにスキップしない】`python3` や `fitz` が無ければ `spawnSync` の status が 0 でなく**赤になる**
// (`gate.test.ts` と同じ流儀)。**skip にすると P-113 が「緑のまま」に戻る**ので、skip の枝は書かない。

import { spawnSync } from "node:child_process";
import { readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const REPORT_PDF = fileURLToPath(new URL("./report-pdf/", import.meta.url));

/** `report-pdf/` の python の試験(名前の末尾が `_test.py`)。並びは固定(読む側が追えるように)。 */
const PYTHON_TESTS: readonly string[] = readdirSync(REPORT_PDF)
  .filter((name) => name.endsWith("_test.py"))
  .sort();

/**
 * 本数の床。**ファイルが消えたら赤にする**ための下限
 * (2026-09-28 時点で 4 本: answer_facts・check_answer・check_delivery・check_structure)。
 * 試験を足したときに上げる必要は無い(足すぶんは `readdirSync` が拾う)。
 */
const MIN_PYTHON_TESTS = 10;

/**
 * python を起こす 1 本ぶんの上限(ms)。**vitest の既定 5000ms では足りない。**
 * 実測(2026-09-29): `check_structure_test.py` は単独 2.58 秒・**並行の負荷がかかると 4.88〜6.69 秒**。
 * 既定のままだと 6 回に 2 回、`Test timed out in 5000ms` で落ちた(P-138)。
 * **本物の固まり(無限ループ・入力待ち)は 30 秒で捕まる。**
 */
const PYTHON_TEST_TIMEOUT_MS = 30_000;

describe("report-pdf の python の試験(P-113)", () => {
  it(`試験のファイルが ${MIN_PYTHON_TESTS} 本以上ある(消えたら赤)`, () => {
    expect(PYTHON_TESTS.length, `見つかった試験: ${PYTHON_TESTS.join(", ") || "なし"}`).toBeGreaterThanOrEqual(MIN_PYTHON_TESTS);
  });

  // P-117 の解(司令塔の判断 2026-09-28)。**名前の集合**を正本にする ― 本数の床が見逃す
  // 「1 本消して 1 本足す」を捕まえる。**足す・消す・改名のどれでも赤になり、人が `-u` で承認する。**
  it("試験のファイルの名前の集合が、承認済みの一覧と一致する(足す・消す・改名で赤)", () => {
    expect(PYTHON_TESTS).toMatchSnapshot();
  });

  for (const name of PYTHON_TESTS) {
    // **上限を明示する。**vitest の既定は 5000ms だが、この `it` は **python の子プロセスを起こし、
    // その中で PDF を組む**。実測(2026-09-29): `check_structure_test.py` は**単独で 2.58 秒**でも、
    // **vitest が 95 本の試験ファイルを並行で回している最中は 4.88〜6.69 秒**になり、
    // 5 秒を超えて 6 回に 2 回落ちた(`Test timed out in 5000ms`)。
    // **これは偽の赤** ― 門が見ているのは「python の試験が通るか」であって、所要時間ではない。
    // 所要を測りたいなら別の物差しを置く(いまの上限は負荷しか測っていない)。
    // 上限は**本物の固まりを捕まえられる長さ**にする(負荷の最悪 6.69 秒に対して 30 秒)。
    it(`${name} が通る`, () => {
      const result = spawnSync("python3", ["-X", "utf8", name], { cwd: REPORT_PDF, encoding: "utf-8" });
      // 落ちた理由が読めない門にしない ― 標準出力・標準エラーを失敗の文に載せる。
      const detail = [
        `status=${result.status}`,
        result.error ? `error=${result.error.message}` : "",
        `stdout:\n${result.stdout ?? ""}`,
        `stderr:\n${result.stderr ?? ""}`,
      ]
        .filter((part) => part !== "")
        .join("\n");
      expect(result.status, detail).toBe(0);
    }, PYTHON_TEST_TIMEOUT_MS);
  }
});
