// **原本のファイルに NUL を入れない。**入ると `grep` が「binary」として**黙って飛ばす**。
//
// 【なぜ要るか(2026-09-29 に実測)】`scripts/playtest/deliver.ts` に NUL が 2 つ入っていた ―
// 対の鍵を作る所で、区切りに**本物の NUL 文字**を書いていた(テンプレート文字列の中に生のまま)。
// TypeScript は通すので 2 本の門は緑のままで、**`file` が "data" と言い、`grep` が
// この 425 行の道具をまるごと飛ばしていた。** つまり**リポジトリ横断の grep が嘘をつく** ―
// 「この語はどこにも無い」と読んだ判断が全部あやしくなる(「影響範囲は grep でなく実測する」の裏返し)。
//
// 直し方は簡単で、**同じ文字を escape(バックスラッシュ + u0000)で書く**(実行時の値は変わらない)。
// この試験は「NUL が 1 バイトでもあれば赤」だけを見る。**読みやすさや書き方は見ない。**
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = new URL("./", import.meta.url).pathname;

/** 原本として見るもの。**生成物・顧客の材料は見ない**(`out/` は生成物置き場)。 */
const SKIP_DIRS = new Set(["node_modules", "out", ".git", "__pycache__"]);
const SOURCE_SUFFIXES = [".ts", ".py", ".md", ".json", ".sh", ".snap"];

function sourceFilesUnder(dir: string): string[] {
  const found: string[] = [];
  for (const name of readdirSync(dir)) {
    if (SKIP_DIRS.has(name)) continue;
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      found.push(...sourceFilesUnder(full));
      continue;
    }
    if (SOURCE_SUFFIXES.some((s) => name.endsWith(s))) found.push(full);
  }
  return found;
}

describe("原本のファイルは text である(NUL を含まない)", () => {
  const files = sourceFilesUnder(ROOT);

  it("原本を 1 本以上見つけている(見つけ方が壊れたら床で分かる)", () => {
    expect(files.length).toBeGreaterThan(50);
  });

  it("NUL を含むファイルが無い(あると grep が黙って飛ばす)", () => {
    const withNul = files.filter((f) => readFileSync(f).includes(0));
    expect(withNul.map((f) => f.slice(ROOT.length))).toEqual([]);
  });
});
