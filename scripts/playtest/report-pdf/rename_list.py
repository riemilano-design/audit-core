# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT。**実物から文・題を写す前に通す「改名の一覧」をコミットの diff から作る。**
#
# 【なぜ要るか】正本 `docs/GOLDEN_MASTER_CUSTOMER_EXIT.md` §9:
#   **実物は「正しい形」ではなく「ある時点の形」である。写してよいのは、その後に直していないものだけ。**
# §10 が実物の時点を mtime で固定した。**この突き合わせを記憶でやると、同じ日の直しが戻る**
# (実例: 実物の表紙に「2. 盤上はこう勝てた」が残っていた ― `0d50a38` で改名済みの旧い題)。
# **記憶にある安全規則は規則ではない**(人間の言葉、2026-09-28)ので、道具にする。
#
# 【範囲は日付ではなく実物の mtime】**納品ファイルの名前の日付は当てにならない**
# (実測: 名前が `_2026-09-25_` で mtime が 09-23 のものがある)。
#
# 【拾う行】改名の実体は md の `## ` ではなく**組版の中の文字列**:
#   コード: `S_H1)` `S_H2)` `_TITLE =` `SECTION_HEADINGS` のある行だけ
#   md:     `#`〜`###` の行だけ(python の `# ==== …` を除くため、md 見出しは .md に限る)
#
# 【この道具を作るときに踏んだ穴 3 つ。どれも「黙って落ちる」型だった】
#   (1) **定数に置き換えた改名が「新名なし」に見える**(`"盤上はこう勝てた"` → `FINAL_SECTION_TITLE`)。
#       → 大文字の識別子は、そのコミット時点のファイルから値を引いて文字列に直す。
#   (2) **片側だけの hunk が 1 行も出ずに消えた。** → 1:1 にならない hunk は C「要目視」に必ず出す。
#   (3) **新規ファイルは全行が「足された」になり、雑音 60 件に膨らむ。** → 新規は出さない。
# **(2) の直しが (1) を黙らせない歯止めになっている** ― (1) を止めても消えず C に落ちる。
#
# 使い方:
#   python3 -X utf8 rename_list.py --since "2026-09-24 13:26" [--since-newer "2026-09-25 07:06"] \
#     [--repo <リポジトリの根>] [--path <見る経路>]…
import os
import re
import subprocess
import sys

HEADING_LINE = re.compile(r"(S_H[12]\)|_TITLE\s*=|SECTION_HEADINGS)")
MD_HEADING = re.compile(r"^#{1,3}\s+\S")
CJK = re.compile(r"[぀-ヿ一-鿿]")
# **1 文字も拾う。**`{2,}` にすると、`P("題", S_H2)` のような 1 文字の文字列で
# **引用符の対応がずれ、その行の後ろの文字列が黙って消える**(閉じ引用符が開き引用符として使われる)。
# 日本語が入っているかは後で見るので、長さで落とす必要は無い(`rename_list_test.py` の test_04 が捕まえた)。
QUOTED = re.compile(r"""(?:"([^"\n]+)"|'([^'\n]+)')""")
CONST = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\b")

# 既定で見る経路: **冊子を作るものだけ。**
# `records/` は内部の記録、`out/` は成果物で、顧客が読む題ではない(混ぜると雑音で本物が埋まる)。
DEFAULT_PATHS = ["scripts/playtest/report-pdf", "scripts/playtest/lib",
                 ":(glob)scripts/playtest/*.ts"]


class RenameListError(Exception):
    pass


class Scanner:
    def __init__(self, repo, paths=None):
        self.repo = repo
        self.paths = list(paths) if paths else list(DEFAULT_PATHS)
        self._blobs = {}

    def git(self, *args):
        r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=self.repo)
        return r.stdout

    def blob(self, sha, path):
        key = (sha, path)
        if key not in self._blobs:
            self._blobs[key] = self.git("show", f"{sha}:{path}")
        return self._blobs[key]

    def resolve_const(self, sha, path, name):
        """`NAME = "…"` をそのコミット時点(と 1 つ前)のファイルから引く。"""
        for s in (sha, f"{sha}^"):
            m = re.search(rf'^{re.escape(name)}\s*=\s*["\']([^"\'\n]+)["\']',
                          self.blob(s, path), re.M)
            if m and CJK.search(m.group(1)):
                return m.group(1)
        return None

    def strings_of(self, line, sha, path):
        """行から「見出しとして出る日本語」を取る。**定数名は値に直す**(穴 1)。"""
        out = []
        for m in QUOTED.finditer(line):
            s = next((g for g in m.groups() if g is not None), None)
            if s and CJK.search(s):
                out.append(s)
        for name in CONST.findall(line):
            if name.startswith("S_H"):
                continue
            v = self.resolve_const(sha, path, name)
            if v:
                out.append(v)
        if path.endswith(".md"):
            h = line.strip()
            if MD_HEADING.match(h):
                h = h.lstrip("#").strip()
                if CJK.search(h):
                    out.append(h)
        return out

    @staticmethod
    def is_heading_line(line, path):
        if path.endswith(".md"):
            return bool(MD_HEADING.match(line.strip()))
        return bool(HEADING_LINE.search(line))

    def hunks(self, sha):
        """(path, 消えた行, 足された行, 消えたファイルか) を hunk ごとに。

        **新規ファイルは返さない**(穴 3 ― 全行が「足された」になり雑音で本物が埋まる)。
        **ファイル全削除は返す**(独立監査の指摘 2026-09-29):
        `+++ /dev/null` は `+++ b/` で始まらないので、直さないと **path が前のファイルのまま**になり、
        消えたファイルの行が前のファイルに付くか、先頭なら **A・B・C のどこにも出ずに黙って消える。**
        自分のコメントに書いた「黙って 0 にしない」に反していた。
        """
        diff = self.git("show", sha, "--unified=0", "--format=", "--", *self.paths)
        path, minus, plus = None, [], []
        prev_path = None
        pending_new, path_is_new, path_is_gone = False, False, False

        def emit():
            if path and not path_is_new:
                return (path, minus, plus, path_is_gone)
            return None

        for line in diff.splitlines():
            if line.startswith("--- /dev/null"):
                pending_new = True
            elif line.startswith("--- a/"):
                prev_path = line[6:]
            elif line.startswith("+++ b/"):
                got = emit()
                if got:
                    yield got
                path, minus, plus = line[6:], [], []
                path_is_new, pending_new, path_is_gone = pending_new, False, False
            elif line.startswith("+++ /dev/null"):
                got = emit()
                if got:
                    yield got
                # **消えたファイル。**`--- a/` で覚えた名前を使う。
                path, minus, plus = prev_path, [], []
                path_is_new, pending_new, path_is_gone = False, False, True
            elif line.startswith("@@"):
                got = emit()
                if got:
                    yield got
                minus, plus = [], []
            elif line.startswith("-") and not line.startswith("---"):
                minus.append(line[1:])
            elif line.startswith("+") and not line.startswith("+++"):
                plus.append(line[1:])
        got = emit()
        if got:
            yield got

    def scan(self, since, since_newer=None):
        """`renamed`(1:1)・`wrapped`(包み替え)・`eyeball`(要目視)を返す。

        **`eyeball` に落ちるものを捨てない**(穴 2) ― 拾えなかったものを、
        拾えなかったと言える場所に出す。
        """
        rows = self.git("log", f"--since={since}", "--format=%h %ad",
                        "--date=format:%Y-%m-%d", "--", *self.paths).splitlines()
        if not rows:
            raise RenameListError(
                f"その範囲にコミットが無い: since={since} paths={self.paths}"
                "(範囲か経路が間違っている ― 0 件を『改名なし』と読まないため落とす)")
        newer = set()
        if since_newer:
            newer = set(self.git("log", f"--since={since_newer}", "--format=%h",
                                 "--", *self.paths).split())
        renamed, wrapped, eyeball = [], [], []
        for row in rows:
            sha, date = row.split(" ", 1)
            for path, minus, plus, gone_file in self.hunks(sha):
                m_h = [ln for ln in minus if self.is_heading_line(ln, path)]
                p_h = [ln for ln in plus if self.is_heading_line(ln, path)]
                if not m_h and not p_h:
                    continue
                a = [s for ln in m_h for s in self.strings_of(ln, sha, path)]
                b = [s for ln in p_h for s in self.strings_of(ln, sha, path)]
                gone = [s for s in a if s not in b]
                came = [s for s in b if s not in a]
                which = "両方" if (not since_newer or sha in newer) else "古い実物のみ"
                base = path.rsplit("/", 1)[-1]
                # **A(改名確定)に入れるのは、生の抽出が片側 1 本ずつのときだけ。**
                # 独立監査の指摘(2026-09-29): 見出しの行が `X_TITLE = tool.title("種別", "節")` の形だと、
                # **呼び出しの引数の日本語まで拾う**。旧題の対になる文字列が新旧に共通して消えると、
                # **無関係な引数(付録名)が「新名」として 1:1 に組まれる** ―
                # つまり**いまの正しい題を「写してはいけない旧名」として警告する**。
                # 道具の目的と正反対なので、**引数が混ざりうる形は確定させず C に落とす。**
                one_to_one = len(a) == 1 and len(b) == 1 and a[0] != b[0]
                if gone_file:
                    # **消えたファイルは確定させない**(何に置き換わったかは diff から分からない)
                    eyeball.append({"sha": sha, "date": date, "file": base, "gone": gone,
                                    "came": came, "which": which, "note": "ファイルごと消えた"})
                elif not gone and not came:
                    if m_h and p_h:
                        wrapped.append({"sha": sha, "date": date, "file": base,
                                        "title": a[0] if a else None})
                elif one_to_one:
                    renamed.append({"sha": sha, "date": date, "file": base,
                                    "old": gone[0], "new": came[0], "which": which})
                else:
                    eyeball.append({"sha": sha, "date": date, "file": base,
                                    "gone": gone, "came": came, "which": which, "note": None})
        return {"renamed": dedup(renamed, ("file", "old", "new")),
                "wrapped": dedup(wrapped, ("sha", "file", "title")),
                "eyeball": dedup(eyeball, ("sha", "file"))}


def dedup(rows, keys):
    seen, out = set(), []
    for r in rows:
        k = tuple(str(r.get(x)) for x in keys)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def render(result, since, since_newer):
    lines = ["# 改名の一覧(実物から文・題を写す前に通す)", "",
             f"範囲: `--since {since}`" + (f" / 新しい実物: `{since_newer}`" if since_newer else ""), "",
             f"## A. 改名({len(result['renamed'])} 件。**旧名を写すと直しが戻る**)", "",
             "| # | 旧名(写してはいけない) | 新名 | コミット | 出る場所 | 効く実物 |",
             "|---|---|---|---|---|---|"]
    for i, r in enumerate(result["renamed"], 1):
        lines.append(f"| {i} | {r['old']} | {r['new']} | `{r['sha']}`({r['date'][5:]}) "
                     f"| {r['file']} | {r['which']} |")
    lines += ["", f"## B. 改名なし(包み替えだけ ― 文字列は同じ): {len(result['wrapped'])} 件"]
    for r in result["wrapped"]:
        lines.append(f"- `{r['sha']}`({r['date'][5:]}) {r['file']} ― 「{r['title']}」の行が動いたが文字列は同じ")
    lines += ["", f"## C. 要目視(1:1 でない ― **自動で決めない**): {len(result['eyeball'])} 件"]
    for r in result["eyeball"]:
        note = f" ― {r['note']}" if r.get("note") else ""
        lines.append(f"- `{r['sha']}`({r['date'][5:]}) {r['file']} [{r['which']}]{note}")
        lines.append(f"    消えた: {r['gone'] or 'なし'}")
        lines.append(f"    足された: {r['came'] or 'なし'}")
    return "\n".join(lines) + "\n"


def parse_args(argv):
    out = {"since": None, "since_newer": None,
           "repo": os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "..", "..", "..")),
           "paths": [], "out": None}
    i = 0
    while i < len(argv):
        flag, value = argv[i], argv[i + 1] if i + 1 < len(argv) else None
        if value is None or value.startswith("--"):
            raise RenameListError(f"{flag} に値が無い")
        if flag == "--since":
            out["since"] = value
        elif flag == "--since-newer":
            out["since_newer"] = value
        elif flag == "--repo":
            out["repo"] = value
        elif flag == "--path":
            out["paths"].append(value)
        elif flag == "--out":
            out["out"] = value
        else:
            raise RenameListError(f"知らない引数: {flag}")
        i += 2
    if not out["since"]:
        raise RenameListError("--since を渡す(実物の mtime。**名前の日付は使わない**)")
    return out


def main(argv):
    args = parse_args(argv)
    result = Scanner(args["repo"], args["paths"] or None).scan(args["since"], args["since_newer"])
    text = render(result, args["since"], args["since_newer"])
    if args["out"]:
        with open(args["out"], "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {args['out']}(改名 {len(result['renamed'])} 件・"
              f"包み替え {len(result['wrapped'])} 件・要目視 {len(result['eyeball'])} 件)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except RenameListError as e:
        print(f"一覧を作れない: {e}", file=sys.stderr)
        sys.exit(2)
