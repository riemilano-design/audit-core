// STEP D0-SIDE 段 2(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の F-S7・Q-4・Q-8)。kifu-import-check.ts の --me / --as の配線を子プロセスで見張る。
// **期待値は試験を回す前に手で書いた**(規則 11.1)。**名前はすべて架空**。
// 【静かにスキップしない】npx・tsx・git が無ければ execFileSync が例外を投げて赤になる(status が期待と違うので)。
// 【一時ディレクトリ以外に書かない】走らせる前と後で git status(node_modules だけを除く)が同じであることを確かめる。

import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const CHECK_TS = join(PLAYTEST_DIR, "kifu-import-check.ts");

/** F-S8 と同じ開始局面(平手・後手番に 3c3d を当てた局面。手で導いた値) */
const FS8_START = "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2";
const OPPONENT = "相手役甲";

const KIF = [
  `先手：${OPPONENT}`,
  "後手：テスト太郎@△3四歩",
  "手合割：平手",
  "手数----指手---------消費時間--",
  "   1 ７六歩(77)",
  "   2 ３四歩(33)",
  "   3 ２六歩(27)",
  "   4 投了",
  "まで3手で先手の勝ち",
  "",
].join("\n");

/**
 * 1 文字の成り駒「圭」を含む架空の最小 KIF(D0-KIFU2 の計画 3. の T-4 と同じ手順。9 手目 ３二圭(33) を 成桂 に揃えて読む)。
 * STEP D0-SIDE 段 2 の後の小さな追加(監査 A の段 2 の任意 1): kifu-import-check.ts の表の「揃えた手」の列と詳細行を見張る。
 */
const KEI_KIF = [
  "手合割：平手",
  "手数----指手---------消費時間--",
  "   1 ３六歩(37)",
  "   2 ８四歩(83)",
  "   3 ３七桂(29)",
  "   4 ８五歩(84)",
  "   5 ４五桂(37)",
  "   6 ８六歩(85)",
  "   7 ３三桂成(45)",
  "   8 ８七歩成(86)",
  "   9 ３二圭(33)",
  "  10 投了",
  "まで9手で先手の勝ち",
  "",
].join("\n");

/** 表の見出しの行と、指定したファイルの行を突き合わせ、列の名前 → 欄の値 にする(列が消えれば値がずれる)。 */
function tableCells(stdout: string, fileName: string): Record<string, string> {
  const lines = stdout.split("\n");
  const split = (line: string | undefined) => (line ?? "").replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
  const header = split(lines.find((line) => line.startsWith("| ファイル |")));
  const row = split(lines.find((line) => line.startsWith(`| ${fileName} |`)));
  return Object.fromEntries(header.map((name, index) => [name, row[index] ?? "(欄が無い)"]));
}

const gitStatus = (): string =>
  execFileSync(
    "git",
    ["status", "--porcelain", "-z", "--untracked-files=all", "--ignored", "--", ".", ":(exclude,glob)**/node_modules", ":(exclude,glob)**/node_modules/**"],
    { cwd: REPO_ROOT },
  ).toString();

/** 一時ディレクトリに KIF を書き、kifu-import-check.ts を --fixed 付きで回す。書いた固定棋譜(書かれなければ null)を返す。 */
function runCheck(extraArgs: string[], options: { directory?: boolean; kif?: string } = {}): { status: number | null; stdout: string; stderr: string; fixed: Record<string, unknown> | null } {
  const dir = mkdtempSync(join(tmpdir(), "d0side-kifu-check-"));
  try {
    const kifPath = join(dir, "game.kif");
    const fixedPath = join(dir, "fixed.json");
    writeFileSync(kifPath, options.kif ?? KIF, "utf-8");
    const target = options.directory ? dir : kifPath;
    let status: number | null = 0;
    let stdout = "";
    let stderr = "";
    try {
      stdout = execFileSync("npx", ["tsx", CHECK_TS, target, "--fixed", fixedPath, "--id", "k1", "--source", "試験の KIF", ...extraArgs], {
        cwd: REPO_ROOT,
        encoding: "utf-8",
        stdio: "pipe",
      });
    } catch (error) {
      const failure = error as { status: number | null; stdout: string; stderr: string };
      status = failure.status;
      stdout = String(failure.stdout);
      stderr = String(failure.stderr);
    }
    const fixed = existsSync(fixedPath) ? (JSON.parse(readFileSync(fixedPath, "utf-8")) as Record<string, unknown>) : null;
    return { status, stdout, stderr, fixed };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

describe("kifu-import-check.ts の --me / --as(子プロセス)", () => {
  it(
    "--me が後手の名前に一致: 本人の側は後手。回して 1 手目を開始局面に畳んだ固定棋譜を書き、回す前の手順を残す。相手の名前は出さない",
    () => {
      const before = gitStatus();
      const result = runCheck(["--me", "テスト太郎"]);
      expect(gitStatus()).toBe(before);
      expect(result.status, result.stderr).toBe(0);
      expect(result.stdout).toContain("本人の側: 後手(--me がヘッダの名前に一致。本人の側の値「テスト太郎@△3四歩」)");
      expect(result.stdout).not.toContain(OPPONENT);
      expect(result.fixed).not.toBeNull();
      expect(Object.keys(result.fixed!)).toStrictEqual(["id", "source", "mirrored", "originalUserSide", "plyOffset", "startSfen", "moves", "originalMoves"]);
      // 元の手順 7g7f・3c3d・2g2f を回すと 3c3d・7g7f・8c8d。1 手目 3c3d を開始局面に畳む(手で回した)
      expect(result.fixed).toStrictEqual({
        id: "k1",
        source: "試験の KIF",
        mirrored: true,
        originalUserSide: "gote",
        plyOffset: 1,
        startSfen: FS8_START,
        moves: ["7g7f", "8c8d"],
        originalMoves: ["7g7f", "3c3d", "2g2f"],
      });
      expect(JSON.stringify(result.fixed)).not.toContain("テスト太郎");
    },
    60_000,
  );

  it(
    "--me が先手の名前に一致: 本人の側は先手。mirrored: false を書き、手順はそのまま",
    () => {
      const result = runCheck(["--me", OPPONENT]);
      expect(result.status, result.stderr).toBe(0);
      expect(result.stdout).toContain("本人の側: 先手");
      expect(result.fixed).toStrictEqual({ id: "k1", source: "試験の KIF", mirrored: false, moves: ["7g7f", "3c3d", "2g2f"] });
    },
    60_000,
  );

  it(
    "--me がどちらにも一致しない・--as と食い違う: 理由を出して固定棋譜を書かない(exit 0)",
    () => {
      const unknown = runCheck(["--me", "別の人"]);
      expect(unknown.status, unknown.stderr).toBe(0);
      expect(unknown.stdout).toContain("本人の側: 決めない(user_side_unknown)");
      expect(unknown.stdout).toContain("--fixed: 本人の側が決まらない(user_side_unknown)ので書かない");
      expect(unknown.fixed).toBeNull();

      const conflict = runCheck(["--me", "テスト太郎", "--as", "sente"]);
      expect(conflict.status, conflict.stderr).toBe(0);
      expect(conflict.stdout).toContain("本人の側: 決めない(user_side_conflict)");
      expect(conflict.fixed).toBeNull();
    },
    60_000,
  );

  it(
    "--as だけ: ヘッダを見ずにその側で書く",
    () => {
      const result = runCheck(["--as", "gote"]);
      expect(result.status, result.stderr).toBe(0);
      expect(result.stdout).toContain("本人の側: 後手(--as で指定)");
      expect(result.fixed).toMatchObject({ mirrored: true, startSfen: FS8_START, moves: ["7g7f", "8c8d"] });
    },
    60_000,
  );

  it(
    "--me も --as も無ければ、今までと同じ形(id・source・moves の 3 欄)で書き、本人の側の行を出さない",
    () => {
      const result = runCheck([]);
      expect(result.status, result.stderr).toBe(0);
      expect(result.stdout).not.toContain("本人の側");
      expect(result.fixed).toStrictEqual({ id: "k1", source: "試験の KIF", moves: ["7g7f", "3c3d", "2g2f"] });
    },
    60_000,
  );

  it(
    "止める: --me が空・空白だけ・半角の @ を含む、--as が sente / gote でない、フォルダに --me(exit 2、固定棋譜を書かない)",
    () => {
      for (const args of [["--me", ""], ["--me", "  "], ["--me", "テスト太郎@△3四歩"], ["--as", "black"]]) {
        const result = runCheck(args);
        expect(result.status, JSON.stringify(args)).toBe(2);
        expect(result.fixed, JSON.stringify(args)).toBeNull();
      }
      const onDirectory = runCheck(["--me", "テスト太郎"], { directory: true });
      expect(onDirectory.status).toBe(2);
    },
    120_000,
  );

  it(
    "D0-KIFU2 の表: 1 文字の成り駒を含む KIF は、表の「揃えた手」の欄が 1 で、詳細行「揃えて読んだ: 圭→成桂」を出す。含まない KIF は 0 で詳細行を出さない(監査 A の段 2 の任意 1)",
    () => {
      const kei = runCheck([], { kif: KEI_KIF });
      expect(kei.status, kei.stderr).toBe(0);
      expect(tableCells(kei.stdout, "game.kif")).toMatchObject({ 結果: "読めた", 手数: "9", 往復: "局面 一致 / 表記の食い違い 0", 揃えた手: "1", 読めなかった行: "0" });
      expect(kei.stdout).toContain("- game.kif 9 手目 揃えて読んだ: 圭→成桂");

      const plain = runCheck([]);
      expect(plain.status, plain.stderr).toBe(0);
      expect(tableCells(plain.stdout, "game.kif")).toMatchObject({ 結果: "読めた", 手数: "3", 揃えた手: "0" });
      expect(plain.stdout).not.toContain("揃えて読んだ:");
    },
    60_000,
  );
});
