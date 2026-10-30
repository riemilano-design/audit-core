# -*- coding: utf-8 -*-
u"""「測った事実」1 冊(`docs/FACTS_FOR_BUYERS_2026-10-20.md`)の数を記録に照合する入口。

**新しい測定はしない。**1 冊の表の各行に付いた `〔…〕` の印(記録の path・key・数)を
読み、記録(`fixtures/**/*.json` など)をいま開いて値を取り出し、1 冊の字と一致するかを
1 行ずつ `OK` / `NG` で返す。API は呼ばない・通信しない・環境変数を読まない。

    python3 measure/facts_check_2026-10-20.py --check              全部の印
    python3 measure/facts_check_2026-10-20.py --check --row L-01   1 行だけ
    python3 measure/facts_check_2026-10-20.py --list               行の ID の一覧

終了コード: 全部 OK(SKIP は数えない)で 0、1 つでも NG なら 1。

印の文法(1 つの印は `〔種類 …〕`。表の `|` と衝突しないよう `|` は使わない):

  〔rec <path>#<key> > <key> ... = <値>〕
        記録の値(リストなら要素数)が <値> と等しい。
  〔sum <path>#<key> ＋ <path>#<key> ... = <値>〕
        足し算(項は全角の `＋` で区切る)。
  〔rate <path>#<key> ÷ <path>#<key> = x.x%〕
        分子 ÷ 分母 × 100 を四捨五入(小数 1 桁・0.05 は切り上げ)した値。
        分子・分母は `＋` で足した和でもよい。
  〔cnt <path>#<key> :: <欄>=<JSON 値> = N〕
        リストのうち <欄> が <JSON 値> と等しい要素の本数。
  〔wc <path> <path> ... = N〕
        file の改行の数の和(`wc -l` と同じ)。
  〔git <commit> <path 接頭辞> <正規表現> = N〕
        `git ls-tree -r --name-only <commit>` の道のうち、接頭辞で始まり正規表現に
        当たる本数。commit が無い clone では SKIP(別 repo に切り出した後の道)。

path は audit-core/ からの相対。key の並びは ` > ` で区切り、リストの添字は整数。
`#` の後ろが空なら記録の根(リストの本数など)。
key の中の `|`(git の正規表現の選択も同じ)は印では `¦` と書く(表のセルを壊さないため。照合のとき `|` に戻す)。
"""
import io
import json
import os
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOC = os.path.join(ROOT, "docs", "FACTS_FOR_BUYERS_2026-10-20.md")

TOKEN_RE = re.compile(u"〔([a-z]+) ([^〔〕]*)〕")
ID_RE = re.compile(r"^[A-Z]+-\d+$")
SEP = u" > "
PLUS = u" ＋ "
DIV = u" ÷ "
BAR = u"¦"   # 記録の key に `|` が在るとき、表を壊さないよう印では `¦` と書く

_CACHE = {}


class Ng(Exception):
    pass


class Skip(Exception):
    pass


def load_json(rel):
    if rel not in _CACHE:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            raise Ng(u"記録が無い: %s" % rel)
        with io.open(p, encoding="utf-8") as fh:
            _CACHE[rel] = json.load(fh)
    return _CACHE[rel]


def resolve(ref):
    u"""`<path>#<key> > <key> ...` -> 記録の値(リストは要素数、スカラーはそのまま)。"""
    if u"#" not in ref:
        raise Ng(u"印に # が無い: %r" % ref)
    rel, keypath = ref.split(u"#", 1)
    rel = rel.strip()
    node = load_json(rel)
    walked = []
    segs = keypath.strip().split(SEP) if keypath.strip() else []
    for seg in segs:
        walked.append(seg)
        if isinstance(node, list):
            if not re.match(r"^\d+$", seg) or int(seg) >= len(node):
                raise Ng(u"リストに添字 %r が無い(%s)" % (seg, SEP.join(walked)))
            node = node[int(seg)]
        elif isinstance(node, dict):
            if seg not in node and seg.replace(BAR, u"|") in node:
                seg = seg.replace(BAR, u"|")
            if seg not in node:
                raise Ng(u"key が無い: %r(%s)" % (seg, SEP.join(walked)))
            node = node[seg]
        else:
            raise Ng(u"スカラーの下は辿れない: %s" % SEP.join(walked))
    if isinstance(node, list):
        return len(node)
    if isinstance(node, dict):
        raise Ng(u"末端が object: %s(数でない)" % (keypath.strip() or u"(根)"))
    return node


def literal_equal(actual, lit):
    lit = lit.strip()
    if isinstance(actual, bool):
        return lit == (u"true" if actual else u"false")
    if actual is None:
        return lit == u"null"
    if isinstance(actual, (int, float)):
        try:
            return Decimal(lit) == Decimal(repr(actual))
        except Exception:
            return False
    return actual == lit


def num(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise Ng(u"数でない(%s): %r" % (what, v))
    return Decimal(repr(v))


def sum_terms(expr):
    total = Decimal(0)
    for term in expr.split(PLUS):
        total += num(resolve(term), term)
    return total


def pct(a, b):
    if b == 0:
        raise Ng(u"分母が 0")
    q = (a / b * Decimal(100)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return q


def git_count(rev, prefix, regex):
    r = subprocess.run(["git", "cat-file", "-e", rev + "^{commit}"], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise Skip(u"commit %s がこの clone に無い" % rev)
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", rev, "--", prefix],
                       cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise Ng(u"git ls-tree が失敗した")
    names = r.stdout.decode("utf-8").splitlines()
    return len([n for n in names if re.search(regex, n)])


def split_eq(body):
    if u" = " not in body:
        raise Ng(u"印に ' = ' が無い: %r" % body)
    left, right = body.rsplit(u" = ", 1)
    return left.strip(), right.strip()


def evaluate(kind, body):
    u"""印 1 つを評価する。戻り値 = (期待の字, 実測の字)。一致しなければ Ng。"""
    if u"|" in body:
        raise Ng(u"印に | が在る(表を壊す)")
    left, expected = split_eq(body)
    if kind == u"rec":
        actual = resolve(left)
        if not literal_equal(actual, expected):
            raise Ng(u"期待 %s / 記録 %r" % (expected, actual))
        return expected, actual
    if kind == u"sum":
        total = sum_terms(left)
        if total != Decimal(expected):
            raise Ng(u"期待 %s / 記録の和 %s" % (expected, total))
        return expected, total
    if kind == u"rate":
        if DIV not in left:
            raise Ng(u"rate に ÷ が無い")
        a_ref, b_ref = left.split(DIV, 1)
        a = sum_terms(a_ref)
        b = sum_terms(b_ref)
        want = expected.rstrip(u"%").strip()
        got = pct(a, b)
        if got != Decimal(want):
            raise Ng(u"期待 %s%% / 記録 %s ÷ %s = %s%%" % (want, a, b, got))
        return expected, u"%s ÷ %s = %s%%" % (a, b, got)
    if kind == u"cnt":
        if u" :: " not in left:
            raise Ng(u"cnt に ' :: ' が無い")
        ref, cond = left.split(u" :: ", 1)
        field, lit = cond.split(u"=", 1)
        rel, keypath = ref.split(u"#", 1)
        node = load_json(rel.strip())
        for seg in keypath.strip().split(SEP):
            if isinstance(node, list):
                node = node[int(seg)]
            else:
                node = node[seg.replace(BAR, u"|") if seg.replace(BAR, u"|") in node else seg]
        if not isinstance(node, list):
            raise Ng(u"cnt の対象がリストでない")
        want = json.loads(lit)
        n = len([x for x in node if isinstance(x, dict) and field in x and x[field] == want])
        if not literal_equal(n, expected):
            raise Ng(u"期待 %s / 記録の本数 %d" % (expected, n))
        return expected, n
    if kind == u"wc":
        total = 0
        for rel in left.split(u" "):
            p = os.path.join(ROOT, rel)
            if not os.path.isfile(p):
                raise Ng(u"file が無い: %s" % rel)
            with open(p, "rb") as fh:
                total += fh.read().count(b"\n")
        if not literal_equal(total, expected):
            raise Ng(u"期待 %s / 改行の数 %d" % (expected, total))
        return expected, total
    if kind == u"git":
        parts = left.split(u" ")
        if len(parts) != 3:
            raise Ng(u"git の印は <commit> <接頭辞> <正規表現>")
        n = git_count(parts[0], parts[1], parts[2].replace(BAR, u"|"))
        if not literal_equal(n, expected):
            raise Ng(u"期待 %s / git の本数 %d" % (expected, n))
        return expected, n
    raise Ng(u"知らない種類: %s" % kind)


def read_doc(path=DOC):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def row_id(line):
    u"""表の行の先頭の ID(`| L-01 | ...`)。ID でなければ None。"""
    if not line.startswith(u"|"):
        return None
    cells = [c.strip() for c in line.strip().strip(u"|").split(u"|")]
    if cells and ID_RE.match(cells[0]):
        return cells[0]
    return None


def claims(doc_text):
    u"""1 冊の全部の印を [(行番号, 行の ID か None, 種類, 本体, その行の印を除いた字)] で返す。"""
    out = []
    for i, line in enumerate(doc_text.splitlines(), 1):
        found = TOKEN_RE.findall(line)
        if not found:
            continue
        bare = TOKEN_RE.sub(u"", line)
        rid = row_id(line)
        for kind, body in found:
            out.append((i, rid, kind, body, bare))
    return out


def run_check(rows=None, doc_text=None, out=sys.stdout):
    u"""全部(または指定の行)の印を照合し、(OK 本数, NG 本数, SKIP 本数) を返す。"""
    doc_text = read_doc() if doc_text is None else doc_text
    ok = ng = skip = 0
    for lineno, rid, kind, body, _bare in claims(doc_text):
        if rows and rid not in rows:
            continue
        tag = u"%s" % (rid or u"-")
        try:
            evaluate(kind, body)
            ok += 1
            out.write(u"OK    %-6s L%-4d %s %s\n" % (tag, lineno, kind, body))
        except Skip as e:
            skip += 1
            out.write(u"SKIP  %-6s L%-4d %s %s  (%s)\n" % (tag, lineno, kind, body, e))
        except Ng as e:
            ng += 1
            out.write(u"NG    %-6s L%-4d %s %s  <- %s\n" % (tag, lineno, kind, body, e))
        except Exception as e:  # 想定外の形も NG として見せる(黙らせない)
            ng += 1
            out.write(u"NG    %-6s L%-4d %s %s  <- %s: %s\n"
                      % (tag, lineno, kind, body, type(e).__name__, e))
    return ok, ng, skip


def main(argv):
    if u"--list" in argv:
        seen = []
        for line in read_doc().splitlines():
            rid = row_id(line)
            if rid and rid not in seen:
                seen.append(rid)
        sys.stdout.write(u"\n".join(seen) + u"\n")
        return 0
    if u"--check" not in argv:
        sys.stdout.write(__doc__)
        return 2
    rows = None
    if u"--row" in argv:
        i = argv.index(u"--row")
        rows = set(argv[i + 1:i + 2])
    ok, ng, skip = run_check(rows)
    if rows and ok + ng + skip == 0:
        sys.stdout.write(u"NG    行 %s に印が無い\n" % u",".join(sorted(rows)))
        return 1
    sys.stdout.write(u"\n合計 OK %d / NG %d / SKIP %d\n" % (ok, ng, skip))
    return 1 if ng else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
