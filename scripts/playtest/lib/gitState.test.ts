// STEP U6-R。gitState の判定を、git を呼ばずに確かめる。
//
// 【なぜ要るか(2026-09-13)】
// 合流のときに 1 行ずつ壊して測ったところ、**U6-R の 3 値には試験が 1 件も無く、
// 「測れなかった」を false に戻す変異が沈黙した**(U6-L の searchPvs 側は鳴った)。
// 「両方入っている」を目で見て済ませていたら気づいていない。

import { describe, expect, it } from "vitest";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  collectDirtyPaths,
  displayDirty,
  isCountedPath,
  pathsOfPorcelainZ,
  readDirtyState,
  readGitState,
  renderDirtyPathsLine,
  renderDirtyWarnings,
} from "./gitState.js";

/** `git status --porcelain -z` の出力を作る(項目を NUL で区切り、末尾にも NUL)。 */
const z = (...entries: string[]): string => entries.map((e) => `${e}\0`).join("");

describe("collectDirtyPaths: 何を汚れと数えるか", () => {
  it("apps/・data/・scripts/ を数え、docs/ は数えない", () => {
    const out = z(" M apps/server/src/a.ts", " M data/shapes/b.json", " M scripts/playtest/c.ts", " M docs/PHASES.md", " M README.md");
    expect(collectDirtyPaths(out)).toEqual(["apps/server/src/a.ts", "data/shapes/b.json", "scripts/playtest/c.ts"]);
  });

  it("未追跡(??)も数える ―― data/ に未追跡の形があると結果が変わるため", () => {
    expect(collectDirtyPaths(z("?? data/shapes/new.json"))).toEqual(["data/shapes/new.json"]);
  });

  // worktree では node_modules が共有ツリーへのシンボリックリンクで、.gitignore の
  // "node_modules/"(末尾スラッシュ)はリンクにマッチしないため必ず ?? として出る。
  it("node_modules は追跡・未追跡を問わず数えない", () => {
    const out = z("?? node_modules", "?? apps/server/node_modules", "?? apps/web/node_modules", " M apps/server/src/real.ts");
    expect(collectDirtyPaths(out)).toEqual(["apps/server/src/real.ts"]);
  });

  it("node_modules を含む名前でも、階層の名前そのものでなければ数える", () => {
    expect(isCountedPath("scripts/node_modules_helper.ts")).toBe(true);
    expect(isCountedPath("scripts/node_modules/x.ts")).toBe(false);
  });

  // -z のリネームは「新しい PATH」の項目のあとに「元の PATH」が別の項目として続く(実測)。
  it("リネームは新旧の両方を数え、元の PATH を状態記号付きの項目として読み違えない", () => {
    expect(pathsOfPorcelainZ(z("R  data/b.json", "data/a.json", " M apps/x.ts"))).toEqual([
      "data/b.json",
      "data/a.json",
      "apps/x.ts",
    ]);
  });

  // 3 回目の再監査(非必須 a。変異 Y06): 作業ツリー側のリネーム(Y 列の R)の入力が無く、
  // 状態記号の 1 文字目だけを見る書き換えが鳴らなかった。
  it("作業ツリー側のリネーム( R)も、新旧の両方を数える", () => {
    expect(pathsOfPorcelainZ(z(" R apps/new.ts", "apps/old.ts", " M data/x.json"))).toEqual([
      "apps/new.ts",
      "apps/old.ts",
      "data/x.json",
    ]);
  });

  it("空白や日本語を含むパスを、引用符なしでそのまま読む", () => {
    expect(collectDirtyPaths(z("?? data/新規 形.json", "R  apps/new name.ts", "apps/old.ts"))).toEqual([
      "apps/new name.ts",
      "apps/old.ts",
      "data/新規 形.json",
    ]);
  });

  it("重複は畳み、昇順に並べる", () => {
    expect(collectDirtyPaths(z(" M data/b.json", " M data/a.json", "?? data/b.json"))).toEqual(["data/a.json", "data/b.json"]);
  });
});

describe("readGitState: 「測れなかった」を「きれいだった」にしない", () => {
  it("git status が取れなければ dirty は null(false ではない)", () => {
    const state = readGitState("/nowhere", (args) => {
      if (args[0] === "rev-parse") return "abc123\n";
      throw new Error("git status に失敗した");
    });
    expect(state.dirty).toBeNull();
    expect(state.dirty).not.toBe(false);
    expect(state.gitHead).toBe("abc123");
  });

  it("HEAD が取れなくても、汚れの判定は続ける", () => {
    const state = readGitState("/x", (args) => {
      if (args[0] === "rev-parse") throw new Error("HEAD が無い");
      return z(" M data/a.json");
    });
    expect(state.gitHead).toBeNull();
    expect(state.dirty).toBe(true);
    expect(state.dirtyPaths).toEqual(["data/a.json"]);
  });

  it("数える対象が無ければ dirty は false(測って、汚れていなかった)", () => {
    const state = readGitState("/x", (args) => (args[0] === "rev-parse" ? "def456\n" : z("?? node_modules", " M docs/PHASES.md")));
    expect(state.dirty).toBe(false);
    expect(state.dirtyCount).toBe(0);
  });

  it("dirtyPaths は 20 件で切るが、dirtyCount は本当の件数を持つ", () => {
    const many = z(...Array.from({ length: 25 }, (_, i) => ` M data/f${String(i).padStart(2, "0")}.json`));
    const state = readGitState("/x", (args) => (args[0] === "rev-parse" ? "x\n" : many));
    expect(state.dirtyPaths).toHaveLength(20);
    expect(state.dirtyCount).toBe(25);
  });
});

// STEP U6-R。**本物の git を呼ぶ**(2026-09-13 の再監査の指摘。必須 2)。
//
// 差し替えの runner は引数を見ないので、`--untracked-files=no` にしても `-z` を外しても、
// 上の試験は緑のままだった(変異 X05・X06 が沈黙)。**git に何を渡すかは、git に渡して
// 確かめるしかない。** 一時ディレクトリにリポジトリを作り、既定の runner で読む。
describe("readGitState: 本物の git に何を渡しているか", () => {
  const git = (cwd: string, ...args: string[]) =>
    execFileSync("git", ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", ...args], { cwd }).toString();

  const withRepo = (body: (dir: string) => void) => {
    const dir = mkdtempSync(join(tmpdir(), "u6r-git-"));
    try {
      git(dir, "init", "-q");
      mkdirSync(join(dir, "apps"));
      mkdirSync(join(dir, "data"));
      mkdirSync(join(dir, "docs"));
      writeFileSync(join(dir, "apps/old.ts"), "a\n");
      writeFileSync(join(dir, "data/keep.json"), "{}\n");
      git(dir, "add", ".");
      git(dir, "commit", "-q", "-m", "init");
      body(dir);
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  };

  it("きれいなリポジトリでは dirty は false", () => {
    withRepo((dir) => {
      const state = readGitState(dir);
      expect(state.dirty).toBe(false);
      expect(state.gitHead).toMatch(/^[0-9a-f]{40}$/);
    });
  });

  // 8.3 の実例: data/ に未追跡の 1 ファイルを置くだけで沈黙率が 64% → 100% に動いた。
  it("data/ の未追跡ファイルを汚れとして数える(--untracked-files を見張る)", () => {
    withRepo((dir) => {
      writeFileSync(join(dir, "data/new.json"), "{}\n");
      const state = readGitState(dir);
      expect(state.dirty).toBe(true);
      expect(state.dirtyPaths).toEqual(["data/new.json"]);
    });
  });

  it("空白・日本語を含むパスとリネームを、引用符なしで数える(-z を見張る)", () => {
    withRepo((dir) => {
      git(dir, "mv", "apps/old.ts", "apps/new name.ts");
      writeFileSync(join(dir, "data/新規 形.json"), "{}\n");
      writeFileSync(join(dir, "docs/memo.md"), "x\n");
      const state = readGitState(dir);
      expect(state.dirty).toBe(true);
      expect(state.dirtyPaths).toEqual(["apps/new name.ts", "apps/old.ts", "data/新規 形.json"]);
    });
  });
});

describe("readDirtyState: 3 値を潰さない(invariants/types.ts の規約の表)", () => {
  it("true は「汚れていた」", () => {
    expect(readDirtyState({ dirty: true })).toBe("dirty");
  });

  it("false は「測って、汚れていなかった」", () => {
    expect(readDirtyState({ dirty: false })).toBe("clean");
  });

  // ここが潰れると、U6-R より前のすべての記録が「きれいだった」に化ける。
  it("欄が無い記録は「記録していない」であって「きれい」ではない", () => {
    expect(readDirtyState({})).toBe("unrecorded");
    expect(readDirtyState(undefined)).toBe("unrecorded");
  });

  // 当初は null も欄なしと同じ状態に落とし、表示が「この記録は汚れを記録していない」と
  // 事実に反することを言っていた(null の記録は「取れなかった」と記録している)。
  it("null(測れなかった)は「記録していない」とも「きれい」とも別の状態になる", () => {
    expect(readDirtyState({ dirty: null })).toBe("unmeasured");
    expect(readDirtyState({ dirty: null })).not.toBe(readDirtyState({}));
  });

  it("4 つの状態が、4 つとも別の表示になる", () => {
    const texts = [
      displayDirty("dirty", 3),
      displayDirty("clean", 0),
      displayDirty("unrecorded", undefined),
      displayDirty("unmeasured", undefined),
    ];
    expect(texts[0]).toBe("汚れ: あり(3 件)");
    expect(texts[1]).toBe("汚れ: なし");
    expect(texts[2]).toBe("汚れ: 不明(この記録は汚れを記録していない)");
    expect(texts[3]).toBe("汚れ: 不明(測ろうとしたが取れなかったと記録されている)");
    // どの 2 つも同じ文になっていないこと(畳んだら区別が消える)。
    expect(new Set(texts).size).toBe(4);
  });
});

// STEP U6-R。check.ts の「## 入力」に出す注意(2026-09-13)。
//
// 【なぜ要るか】独立監査の再指摘(必須 2)を塞いだあと、担当が規則 11.8(中心を壊す変異を
// 必ず 1 つ入れる)に従って check.ts 側も壊したところ、**「測れなかった」の注意を消しても、
// 入力行の汚れ表示を常に「なし」にしても、165 件中 0 件だった。** この STEP の名前は
// 「meta に記録し、check.ts が警告する」であり、**警告は周辺ではなく中心だった。**
// check.ts は import すると main() が走って終了するため試験を置けない。そこで注意の
// 組み立てをここへ移し、check.ts には呼び出しだけを残した。
describe("renderDirtyWarnings: 状態ごとに別の注意を出す", () => {
  const input = (kifuId: string, dirtyState: Parameters<typeof displayDirty>[0]) => ({ kifuId, dirtyState });

  it("汚れた入力があれば、その件数と kifuId を挙げて注意を出す", () => {
    const lines = renderDirtyWarnings([input("a", "dirty"), input("b", "clean")]);
    expect(lines).toHaveLength(1);
    expect(lines[0]).toContain("汚れていた入力が 1 件");
    expect(lines[0]).toContain("(a)");
  });

  it("「記録していない」と「測れなかった」は別の注意になる(畳まない)", () => {
    const lines = renderDirtyWarnings([input("u", "unrecorded"), input("m", "unmeasured")]);
    expect(lines).toHaveLength(2);
    expect(lines.some((l) => l.includes("記録していない入力が 1 件") && l.includes("(u)"))).toBe(true);
    expect(lines.some((l) => l.includes("測れなかった入力が 1 件") && l.includes("(m)"))).toBe(true);
  });

  it("すべてきれいなら注意は出ない", () => {
    expect(renderDirtyWarnings([input("a", "clean"), input("b", "clean")])).toEqual([]);
  });

  it("汚れていたパスの行は、汚れていてパスがあるときだけ出る", () => {
    expect(renderDirtyPathsLine({ dirtyState: "dirty", dirtyPaths: ["data/a.json", "scripts/b.ts"] })).toBe(
      "  - 汚れていたパス: data/a.json, scripts/b.ts",
    );
    expect(renderDirtyPathsLine({ dirtyState: "dirty", dirtyPaths: [] })).toBeNull();
    expect(renderDirtyPathsLine({ dirtyState: "clean", dirtyPaths: ["x"] })).toBeNull();
    expect(renderDirtyPathsLine({ dirtyState: "unmeasured", dirtyPaths: undefined })).toBeNull();
  });

  // 呼び出しの 1 行は関数の試験では守られない(P-32)。check.ts は import できないので、
  // ソースそのものに配線が残っていることを見る。**結果を捨てる形(push しない)も落とす。**
  // 2026-09-13 の再監査(必須 1): 関数を呼んでいるかだけを見ていたので、
  // `readDirtyState({ dirty: false })`・`displayDirty("clean", …)`・呼び出し側で二値に潰す
  // 書き換え(変異 X01・X02・X09)が沈黙した。**何を渡しているかまで照合する。**
  // 照合は片側にしか壊れない(整形を変えると緑でも落ちる。文字列を残して意味を変える
  // 書き換えは捕まらない)。
  it("check.ts は meta から読んだ値をそのまま渡し、3 つとも呼んで結果を lines へ積んでいる", () => {
    const source = readFileSync(new URL("../check.ts", import.meta.url), "utf8");
    expect(source).toContain("  const dirtyState = readDirtyState(meta);");
    expect(source).toContain("  const dirtyPaths = meta?.dirtyPaths;");
    expect(source).toContain("  const dirtyCount = meta?.dirtyCount;");
    expect(source).toContain("${displayDirty(input.dirtyState, input.dirtyCount ?? input.dirtyPaths?.length)}");
    expect(source).toMatch(/const dirtyPathsLine = renderDirtyPathsLine\(input\);\s*if \(dirtyPathsLine !== null\) lines\.push\(dirtyPathsLine\);/);
    expect(source).toContain("lines.push(...renderDirtyWarnings(inputs));");
  });
});
