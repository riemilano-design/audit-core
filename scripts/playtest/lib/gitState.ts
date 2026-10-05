// 測ったときの作業ツリーの状態(HEAD と、コミットされていない編集の有無)を読む。
// STEP U6-R(docs/STEP_U6-R_PLAN_2026-09-13.md)。
//
// 【なぜ要るか】
// meta.gitHead はコミットされた状態しか指さない。共有ツリーで測ると、記録の gitHead
// はそのコミットを指すのに、実際に動いたコードは「そのコミット + 誰かの未コミットの
// 編集」である。つまりどのコミットのものでもない数字が出る。check.ts の gitHead 混在
// 警告も gitHead しか見ていないので鳴らない。
//
// 【このファイルがやること】
// git rev-parse HEAD と git status --porcelain を 1 か所で読み、
// { gitHead, dirty, dirtyPaths, dirtyCount } を返す。
//
// 【このファイルが絶対にやらないこと】
// - 測定の中止・ブロック。汚れていても測れる。ここは観測だけを行う。
// - git stash・git add・git checkout などツリーを変える操作(他セッションの差分に触れる)。
// - 「その差分が結果に影響したか」の判断。分かるのは「影響しうる編集があった」ことだけ。

import { execFileSync } from "node:child_process";


/** 汚れとして数えるパスの接頭辞。docs/ は結果に影響しないため数えない
 * (数えると常に汚れることになり、警告が意味を失う)。 */
const COUNTED_PREFIXES = ["apps/", "data/", "scripts/"];

/** dirtyPaths に載せる最大件数。超えた分は dirtyCount にだけ残る。 */
const MAX_DIRTY_PATHS = 20;

export interface GitState {
  /** HEAD のコミット。取得に失敗したら null。 */
  gitHead: string | null;
  /** 数える範囲に、コミットされていない編集(未追跡を含む)があったか。
   * null は「汚れを測れなかった」であり、「きれいだった」ではない。
   * 記録にはそのまま null で載せ、check.ts は「不明」と表示する。 */
  dirty: boolean | null;
  /** 汚れていたパス(最大 MAX_DIRTY_PATHS 件)。 */
  dirtyPaths: string[];
  /** 汚れていたパスの総数(dirtyPaths が切り詰められていても本当の件数)。 */
  dirtyCount: number;
}

/**
 * `git status --porcelain -z` の出力からパスを取り出す。
 *
 * 【なぜ -z か(2026-09-13 の再監査の指摘。非必須 b。実測した)】
 * `-z` なしでは、**空白を含むパスは `core.quotepath=false` でも引用符で囲まれる**
 * (`R  apps/old.ts -> "apps/new name.ts"`)。引用符で始まるパスは `apps/` 等の接頭辞に
 * 一致しないので、**汚れとして数えられなかった。** `-z` では引用符も `\nnn` の
 * エスケープも付かず、日本語もそのまま出る。したがって `core.quotepath` の指定は要らない。
 *
 * 【形式(実測)】各項目は NUL で区切られる。通常は `XY PATH`。リネーム・コピー
 * (X か Y が R / C)は `XY 新しいPATH` のあとに**元の PATH が別の項目として続く**:
 * `R  apps/new name.ts\0apps/old.ts\0`。リネームは両方を返す(どちらも変わったパス)。
 */
export function pathsOfPorcelainZ(out: string): string[] {
  const tokens = out.split("\0");
  const paths: string[] = [];
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i]!;
    if (token.length < 4) continue; // 末尾の空の項目
    const xy = token.slice(0, 2);
    paths.push(token.slice(3));
    if (/[RC]/.test(xy)) {
      const orig = tokens[i + 1];
      if (orig !== undefined && orig.length > 0) paths.push(orig);
      i++; // 元の PATH は状態記号を持たないので、次の項目として読まない
    }
  }
  return paths;
}

/**
 * そのパスを汚れとして数えるか。
 *
 * node_modules を含むパスは、追跡・未追跡・シンボリックリンクの別を問わず数えない。
 * 理由(2026-09-13 の実測): worktree では node_modules を共有ツリーからシンボリック
 * リンクで貼っており、.gitignore の "node_modules/"(末尾スラッシュ付き)は
 * シンボリックリンクにマッチしない。そのため worktree では
 * "?? apps/server/node_modules" 等が必ず出る。apps/ に掛かるので、除外しないと
 * 編集の有無に関わらず常に dirty になり、常に鳴る警告は見なくなる。
 * 共有ツリーでは同じ 3 つが実ディレクトリなので .gitignore が効き、この問題は出ない。
 */
export function isCountedPath(p: string): boolean {
  if (p.split("/").includes("node_modules")) return false;
  return COUNTED_PREFIXES.some((prefix) => p.startsWith(prefix));
}

/**
 * `git status --porcelain -z` の出力から、数える対象のパスを取り出す(純粋関数)。
 * 重複は畳み、昇順に並べる。**ここが本モジュールの判定の全部である。**
 */
export function collectDirtyPaths(porcelainZ: string): string[] {
  const seen = new Set<string>();
  for (const p of pathsOfPorcelainZ(porcelainZ)) {
    if (isCountedPath(p)) seen.add(p);
  }
  return Array.from(seen).sort();
}

/** git を呼ぶところ。テストで差し替えられるようにしてある(失敗の経路を試すため)。 */
export type GitRunner = (args: string[], cwd: string) => string;

const defaultRunner: GitRunner = (args, cwd) => execFileSync("git", args, { cwd }).toString();

export function readGitState(cwd: string, runGit: GitRunner = defaultRunner): GitState {
  let gitHead: string | null;
  try {
    gitHead = runGit(["rev-parse", "HEAD"], cwd).trim();
  } catch {
    gitHead = null;
  }

  let dirtyPaths: string[] = [];
  try {
    // -z: パスを引用符で囲ませない(空白・非 ASCII を含むパスも接頭辞で判定できる)。
    // --untracked-files=normal: 未追跡も出させる(data/ の未追跡ファイルが結果を変える。8.3)。
    // **どちらの引数も、一時リポジトリで本物の git を呼ぶ試験で見張っている**(gitState.test.ts)。
    const out = runGit(["status", "--porcelain", "-z", "--untracked-files=normal"], cwd);
    dirtyPaths = collectDirtyPaths(out);
  } catch {
    // git status が取れないときは「汚れていない」ではない。false を返すと
    // 「測れなかった」が「きれいだった」に化ける(この STEP が防ごうとしている型
    // そのもの)。したがって null を返し、表示側で「不明」に落とす。
    return { gitHead, dirty: null, dirtyPaths: [], dirtyCount: 0 };
  }

  return {
    gitHead,
    dirty: dirtyPaths.length > 0,
    dirtyPaths: dirtyPaths.slice(0, MAX_DIRTY_PATHS),
    dirtyCount: dirtyPaths.length,
  };
}

// ---- 読む側(記録された dirty をどう読むか) ----

/**
 * 記録の `meta.dirty` の状態。invariants/types.ts の規約の表と 1 対 1 に対応する。
 *
 * **当初は `"unknown"` の 1 つに `undefined` と `null` の両方を落としていた**
 * (2026-09-13 の独立監査の指摘)。**それは「記録していない」と「測れなかった」を
 * 混ぜることであり、この STEP が防ごうとしている型そのものだった。**
 * しかも表示が「この記録は汚れを記録していない」と**片方の理由を名乗って**いたため、
 * **`null` の記録について事実に反することを言っていた**(その記録は汚れを記録している
 * ―「取れなかった」と記録している)。**入口を 3 種類に分けたのに、出口で 2 つに畳んでいた。**
 */
export type DirtyState =
  /** `true`。測って、汚れていた */
  | "dirty"
  /** `false`。測って、汚れていなかった */
  | "clean"
  /** 欄が無い。**この記録は汚れを記録していない**(U6-R より前の記録) */
  | "unrecorded"
  /** `null`。**記録はしているが、測れなかった**(`git status` が取れなかった) */
  | "unmeasured";

/**
 * `meta.dirty` を 4 つの状態へ落とす(`true` → dirty / `false` → clean /
 * `null` → unmeasured / 欄が無い → unrecorded)。
 *
 * **`meta?.dirty ?? false` と書かないこと。** 欄が無い古い記録がすべて「きれい」に
 * 化ける(docs/AGENT_PROTOCOL.md 3. の 11.6)。`=== true` / `=== false` /
 * `=== null` / それ以外、の明示分岐にしてある。**`null` と欄が無いことは別の状態である**
 * (前者は「測ろうとして取れなかった」と記録している。後者は何も記録していない)。
 */
export function readDirtyState(meta: { readonly dirty?: boolean | null } | undefined): DirtyState {
  if (meta?.dirty === true) return "dirty";
  if (meta?.dirty === false) return "clean";
  if (meta?.dirty === null) return "unmeasured";
  return "unrecorded";
}

/**
 * 「## 入力」の 1 行に出す汚れの表示。
 *
 * **4 つの状態に 4 つの文を対応させる。** どれか 2 つを同じ文にすると、
 * 読む側で区別が消える(それが当初の誤りだった)。
 */
export function displayDirty(state: DirtyState, dirtyCount: number | undefined): string {
  switch (state) {
    case "dirty":
      return `汚れ: あり(${dirtyCount ?? 0} 件)`;
    case "clean":
      return "汚れ: なし";
    case "unrecorded":
      return "汚れ: 不明(この記録は汚れを記録していない)";
    case "unmeasured":
      return "汚れ: 不明(測ろうとしたが取れなかったと記録されている)";
  }
}

/** 「## 入力」の各行の下に出す、汚れていたパスの行。出さないときは null。 */
export function renderDirtyPathsLine(input: { dirtyState: DirtyState; dirtyPaths: string[] | undefined }): string | null {
  if (input.dirtyState === "dirty" && input.dirtyPaths !== undefined && input.dirtyPaths.length > 0) {
    return `  - 汚れていたパス: ${input.dirtyPaths.join(", ")}`;
  }
  return null;
}

/**
 * 「## 入力」の末尾に出す注意の行。汚れた入力・記録していない入力・測れなかった入力の
 * それぞれについて、該当があれば 1 行ずつ返す。
 *
 * **「記録していない」と「測れなかった」は別の注意にする。** 一つに畳むと、片方の理由を
 * 名乗って両方を飲み込む(2026-09-13 の独立監査の指摘。必須 1)。
 */
export function renderDirtyWarnings(inputs: readonly { kifuId: string; dirtyState: DirtyState }[]): string[] {
  const lines: string[] = [];
  const dirtyInputs = inputs.filter((input) => input.dirtyState === "dirty");
  if (dirtyInputs.length > 0) {
    lines.push(
      `- 注意: 測ったとき作業ツリーが汚れていた入力が ${dirtyInputs.length} 件あります(${dirtyInputs
        .map((input) => input.kifuId)
        .join(", ")})。**gitHead が同じでも、動いたコードは同じではありません。** ` +
        `この記録から分かるのは「結果に影響しうる編集があった」ことだけで、実際に影響したかどうかは分かりません。`,
    );
  }
  const unrecordedInputs = inputs.filter((input) => input.dirtyState === "unrecorded");
  if (unrecordedInputs.length > 0) {
    lines.push(
      `- 注意: 汚れを記録していない入力が ${unrecordedInputs.length} 件あります(${unrecordedInputs
        .map((input) => input.kifuId)
        .join(", ")})。**「きれいだった」ではなく「記録していない」です。**`,
    );
  }
  const unmeasuredInputs = inputs.filter((input) => input.dirtyState === "unmeasured");
  if (unmeasuredInputs.length > 0) {
    lines.push(
      `- 注意: 汚れを測れなかった入力が ${unmeasuredInputs.length} 件あります(${unmeasuredInputs
        .map((input) => input.kifuId)
        .join(", ")})。**「きれいだった」ではなく「取れなかった」と記録されています。**`,
    );
  }
  return lines;
}
