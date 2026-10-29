# -*- coding: utf-8 -*-
u"""注入の仕掛け(測定の harness)の総点検の門 ― 封 docs/XBRL_INJECT_HARNESS_REVIEW_SEAL_2026-10-29.md §5-2 の (a)〜(g)。

文書 ``docs/XBRL_INJECT_HARNESS_REVIEW_2026-10-29.md``。新しい記録 file も script も無い(数は既存の記録から、この門が数え直す)。

  (a) §1-1 の規準(封の字から読む)で ``measure/**/*.py`` を列挙し直し、文書の表の file の集合・行数・当たった字と一致。封の §1-2 の表とも一致。
  (b) §2-3 の数を既存の記録から数え直して文書の表と一致。仕掛けの表の関数名が file に在り、根拠の字が『その関数の中』に在る。使う側・記録の実在。
  (c) 文書が引く台帳の行の ID が台帳に在り、§2-4 の規準で選び直した行の集合と一致(読み分けの語は決まった 3 語、根拠と引用が在り、引用は台帳の行の中に在る)。
  (d) H-1〜H-16 の当否を、封の字(予測・外れ方)と文書の表と記録から読み直して一致。
  (e) 封と文書に docID 0(新しい標本 30・評価用・調整用の docID の字は記録から読む)・claim の id 0・禁止語 0・code fence 0。
  (f) 順序: 封の commit が文書・門の commit より前(git の commit の順。前例 test_xbrl_inject_reach.py の test_i_* の型)。
  (g) 偽物で赤: 文書の表の 1 字・記録の写しの 1 欄・封の予測の 1 字・規準に当たる偽の file 1 つを足すと、(a)〜(d) のどれかが赤。

**(f) は、文書・門のどれかが commit される前は赤になる**(追跡されていない file には『足した commit』が無い)。skip にしない。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門はそれらを行頭に置かない。
**2026-10-29 追記(門の列挙を測った時点の木に縛る)**: (a)(b) の列挙(規準の 39 file・規準の外の副産物の 6 file・使う側の本文)は、**いまの木でなく封の commit ``365b468`` の木**(``git ls-tree -r`` と ``git show``)に当てて文書の表と照らす。
いまの木で数えると、``measure/`` に file を足すたびに赤くなる(測った時点の値をいまの木で縛る型。人が直さないと古くなる)。文書の表と記録の数は測った時点の値のまま書き換えない。``git`` が使えない写し(履歴の無い写し)では SKIP を印字して省く
(前例 ``test_xbrl_default_p27_result.py``・``test_xbrl_default_p26_result.py`` の test_8)。**365b468 より後に足された(または変わった)``measure/**/*.py`` のうち、いまの木で規準か副産物の検査に当たる file** は、
この file の宣言 ``LATER_HARNESS_FILES``(path・役・届いたことの確かめ・根拠の字・足した日付)に載っていなければ赤(生きた門 (h))。宣言に在るのに当たらない・存在しない file も赤(古い宣言を残さない)。
この file は docID の字を持たない(記録から読む)。判断(仕掛けの役・確かめの有無・台帳の行の読み)は文書の表にあり、この門は語彙・実在・内部の整合・機械で数えた部分を見る。判断そのものは監査が code から読み直す。
"""
import ast
import collections
import copy
import glob
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_INJECT_HARNESS_REVIEW_SEAL_2026-10-29.md"
DOC_REL = "docs/XBRL_INJECT_HARNESS_REVIEW_2026-10-29.md"
GATE_REL = "tests/measure/test_xbrl_inject_harness_review.py"
LEDGER_REL = "docs/FACTS_FOR_BUYERS_2026-10-20.md"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
INJECT_REACH_REL = "fixtures/xbrl/inject_reach_2026-10-28.json"
SEAL, DOC = os.path.join(ROOT, SEAL_REL), os.path.join(ROOT, DOC_REL)
SEAL_COMMIT_SHORT = "365b468"
NOT_GATED = u"【門なし】"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
BOLD = re.compile(r"\*\*(.+?)\*\*")
BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)
RANGE_IN = re.compile(r"(\d+(?:\.\d+)?)%? 以上 (\d+(?:\.\d+)?)%? 以下")
LEDGER_ID = re.compile(r"^\| ((?:L|D|H|P)-\d+) \|")

# 語彙(判断の欄はこの語で始まる。『 ― 』の後ろは自由な注)
VOC_ROLE = (u"仕掛け持ち", u"仕掛け持ち + 使う側", u"使う側", u"共通部品", u"対象外")
VOC_OBJ = (u"本文の字", u"fact の属性", u"本文の字・fact の属性", u"構造化された claim の値")
VOC_BASE = (u"site の id", u"claim の id", u"値(と字)", u"fact の鍵", u"基準なし", u"位置(文の番号と文の中の位置)")
VOC_AFTER = (u"同じ id(値の読み返しあり)", u"同じ id(値の読み返しなし)", u"値(と字)", u"fact の鍵", u"位置(文の番号と文の中の位置)+ 値の読み返し", u"なし(値・鍵を検査に直に渡す)")
VOC_CHECK = (u"有", u"無", u"不要")
VOC_HOLE = (u"同じ型", u"別の型", u"無し")
VOC_READ = (u"通った", u"通っていない", u"記録から分からない")
VOC_VERDICT = (u"診断済み", u"対応付けの数でありうる", u"分けられない")
SEP = u" ― "


# ----------------------------------------------------------------------------------------------------------------
def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


#: 門 (a)(b) の列挙を縛る木(封の commit)。いまの木の ``measure/**/*.py`` は (h) だけが見る。
PIN_TREE = "365b468"
_PINNED = {}


def pinned_measure():
    u"""封の commit の木の ``measure/**/*.py``(OrderedDict {measure/ からの相対 path: 本文})。``git`` が使えない・commit が無い写しでは None。"""
    if "v" in _PINNED:
        return _PINNED["v"]
    out = None
    ls = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only", PIN_TREE, "--", PREFIX + "measure"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ls.returncode == 0 and ls.stdout.strip():
        out = collections.OrderedDict()
        for name in sorted(ls.stdout.decode("utf-8").splitlines()):
            if not name.endswith(".py"):
                continue
            r = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (PIN_TREE, name)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if r.returncode != 0:
                out = None
                break
            out[name[len(PREFIX):]] = r.stdout.decode("utf-8").replace(u"\r\n", u"\n")
    _PINNED["v"] = out
    return out


def live_measure_texts(root):
    u"""いまの木の ``measure/**/*.py``(OrderedDict {相対 path: 本文})。"""
    out = collections.OrderedDict()
    for p in sorted(glob.glob(os.path.join(root, "measure", "**", "*.py"), recursive=True)):
        out[os.path.relpath(p, root)] = jtext(p)
    return out


def measure_texts(root):
    u"""(a)(b) が数える ``measure/**/*.py``。``root`` がこの repo の audit-core なら封の commit の木、それ以外(偽の木)はそのディスク。"""
    if os.path.abspath(root) == os.path.abspath(ROOT):
        pinned = pinned_measure()
        if pinned is None:
            raise unittest.SkipTest(u"git ls-tree %s が失敗(履歴の無い写し)。列挙の比べを省く" % PIN_TREE)
        return pinned
    return live_measure_texts(root)


def file_text(root, rel):
    u"""文書が名指す file の本文。``measure/`` の file は封の commit の木の blob(無ければいまの木)、それ以外はいまの木。"""
    if rel.startswith("measure/") and os.path.abspath(root) == os.path.abspath(ROOT):
        pinned = pinned_measure()
        if pinned is not None and rel in pinned:
            return pinned[rel]
    return jtext(os.path.join(root, rel))


def cut(cell):
    u"""『語 ― 注』の語だけ。"""
    return cell.split(SEP)[0].strip()


def cells_of(line):
    return [c.strip() for c in line.strip().strip(u"|").split(u" | ")]


def table(head, rows):
    lines = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        lines.append(u"| " + u" | ".join(str(c) for c in r) + u" |")
    return lines


def rows_of(lines):
    u"""表の本体(見出し 2 行を除く)を cell の列の列にする。"""
    return [cells_of(l) for l in lines[2:]]


def doc_blocks(doc):
    out = collections.OrderedDict()
    for m in BLOCK_RE.finditer(doc):
        if m.group(1) in out:
            raise AssertionError(u"同じ名前の門の表が 2 つ: " + m.group(1))
        out[m.group(1)] = m.group(2).split(u"\n")
    return out


def bt(s):
    return u"`%s`" % s


def unbt(s):
    return s.strip().strip(u"`")


def split_list(cell):
    u"""『`a`・`b`』→ [a, b]。『―』は空。"""
    cell = cell.strip()
    if cell in (u"―", u""):
        return []
    return [unbt(x) for x in cell.split(u"・")]


def join_list(xs):
    return u"・".join(bt(x) for x in xs) if xs else u"―"


# ----------------------------------------------------------------------------------------------------------------
# 封
def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(H-\d+)\*\* \| (.*) \|$", l)
        if m:
            cells = m.group(2).split(u" | ")
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(c.strip() for c in cells)
    return out


def ranges_of(cell):
    return [(float(m.group(1)), float(m.group(2))) for m in (RANGE_IN.search(b) for b in BOLD.findall(cell)) if m]


def pcts_of(cell):
    return [float(m.group(1)) for m in (re.match(r"^(\d+(?:\.\d+)?)% 以上$", b) for b in BOLD.findall(cell)) if m]


def ticks(s):
    return re.findall(r"`([^`]+)`", s)


def seal_criterion(seal):
    u"""封 §1-1 の規準(字)。(a) の 7 つの字・(b) の file 名の字。§6-4 の 6 の副産物の検査の呼び出しの字。"""
    a = b = None
    for l in seal.splitlines():
        if u"次の 7 つの字のどれかが部分文字列として在る" in l:
            a = ticks(l)
        if l.strip().startswith(u"- (b) file 名(basename)に"):
            b = ticks(l)
    sec = seal[seal.index(u"6. **規準の外の file。**"):]
    sec = sec[:sec.index(u"7. 議事録の注入")]
    calls = [t for t in ticks(sec.split(u"で 6 file")[0]) if t.endswith(u"(")]
    m4 = [l for l in seal.splitlines() if l.startswith(u"3. **列挙の規準は字の部分一致である。**")][0]
    marks = [t for t in ticks(m4) if t in (u"replace(", u"tampered")]
    return {"a": a, "b": b, "calls": calls, "marks": marks}


#: 封の §4 の 3 は『本文を差し替える字(`replace(`・`tampered` など)』と書く。『など』の中身として足した字(封にない判断。文書に書く)。
EXTRA_MARKS = (u"注入",)


def enumerate_measure(root, crit, extra=None, texts=None):
    u"""(a) 規準に当たる file の列 [(rel, 行数, [当たった字], 名か)]。extra = {rel: text}(偽の file を足す試験用)。texts を省くと封の commit の木(``measure_texts``)。"""
    texts = collections.OrderedDict(measure_texts(root) if texts is None else texts)
    for rel, t in (extra or {}).items():
        texts[rel] = t
    out = []
    for rel in sorted(texts):
        t = texts[rel]
        hits = [s for s in crit["a"] if s in t]
        nm = any(k in os.path.basename(rel) for k in crit["b"])
        if hits or nm:
            out.append((rel, t.count(u"\n"), hits, nm))
    return out, len(texts)


def outside_criterion(root, crit, extra=None, texts=None):
    u"""§6-4 の 6 の副産物の検査: 規準に当たらず、検査の呼び出しを持ち、本文の差し替えの字を持つ file。texts を省くと封の commit の木。"""
    texts = collections.OrderedDict(measure_texts(root) if texts is None else texts)
    for rel, t in (extra or {}).items():
        texts[rel] = t
    inc = set(r[0] for r in enumerate_measure(root, crit, None, texts)[0])
    marks = list(crit["marks"]) + list(EXTRA_MARKS)
    out = []
    for rel in sorted(texts):
        if rel in inc:
            continue
        t = texts[rel]
        c = [x for x in crit["calls"] if x in t]
        m = [x for x in marks if x in t]
        if c and m:
            out.append((rel, c, m))
    return out


def fixtures_py(root, crit):
    fs = sorted(glob.glob(os.path.join(root, "fixtures", "**", "*.py"), recursive=True))
    hit = 0
    for p in fs:
        t = jtext(p)
        if any(s in t for s in crit["a"]) or any(k in os.path.basename(p) for k in crit["b"]):
            hit += 1
    return len(fs), hit


COPY_RE = re.compile(r"\[u?\"数の字面\"\] in")


def mapping_copies(root):
    u"""cd8 の行 → claim の対応付け(値が許容差の内側 かつ 数の字面が span に在る)を持つ measure の file。"""
    out = []
    texts = measure_texts(root)
    for rel in sorted(texts):
        t = texts[rel]
        if COPY_RE.search(t) and u"A1.TOL" in t:
            out.append(rel)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (b) 記録
class Recs(object):
    u"""記録の読み手。over = {rel: 読んだ後の object}(偽の記録を差す試験用)。"""

    def __init__(self, root=ROOT, over=None):
        self.root = root
        self.over = over or {}
        self.cache = {}

    def get(self, rel):
        if rel in self.over:
            return self.over[rel]
        if rel not in self.cache:
            self.cache[rel] = jload(os.path.join(self.root, rel))
        return self.cache[rel]


P17 = ["fixtures/xbrl/p17/false_pass_2026-10-14%s.json" % s for s in ("", "_P18", "_P19both", "_batch1", "_both", "_fixed")]
RITUAL = ["fixtures/xbrl/ritual_2026-10-20%s.json" % s for s in ("", "_p21", "_p22", "_p26")]
P27 = ["fixtures/xbrl/p27/%s_2026-10-27.json" % s for s in ("eval_inject", "tune_inject", "tune_p27_inject")]
W3 = (u"id_shift", u"sentence_not_found", u"missing")
W3U = W3 + (u"unmutable",)
WPOS = (u"主張が見つからない", u"値がずれた", u"文が見つからない", u"数が見つからない")
W6 = (u"(対応が付かない)", u"(文が 1 つに決まらない)", u"(届いた・止めた)", u"(届いた・通した)", u"(届かない・止めた)", u"(届かない・通した)")


def _state(p):
    return lambda r: ((r.get(p) or {}).get("state") or "")


def _pos(p):
    return lambda r: ((r.get(p) or {}).get("state") or (r.get(p) or {}).get("結果") or r.get("結果") or "")


def _p17_rows(rec):
    return [x for run in rec for x in run["rows"]]


def reach_specs():
    u"""[(K の番号, 記録, 節, 数えた欄, 行を取る関数, 語を取る関数, 語の列)] ― 『届かなかった行』の欄を持つ記録の側(§2-3 の 1・2・5・6)。"""
    S = []

    def add(rec, sec, col, rows, val, words, kind="rows"):
        S.append(("K-%02d" % (len(S) + 1), rec, sec, col, rows, val, words, kind))
    add("fixtures/xbrl/point_prior_2026-10-20.json", u"B", u"行の 結果の細目", lambda d: d["B"]["行"], lambda r: r["結果の細目"], W3)
    for rec, sec, ps in (("period_bind_2026-10-20", "E1", ("P21(対照)", "P22")), ("rounding_2026-10-21", "R3", ("P22", "P23")), ("vocab_2026-10-21", "W4", ("P23", "P24")),
                         ("lastbranch_2026-10-21", "L4", ("P24", "P25"))):
        for p in ps:
            add("fixtures/xbrl/%s.json" % rec, sec, u"行の %s の state" % p, (lambda s: lambda d: d[s]["行"])(sec), _state(p), W3)
    for p in ("P25", "P26"):
        add("fixtures/xbrl/p26_2026-10-21.json", u"Q3 穴 B", u"行の %s の state" % p, lambda d: d["Q3"]["穴 B"]["行"], _state(p), W3)
    for rel in P17:
        add(rel, u"全部の run", u"行の outcome", _p17_rows, lambda r: r["outcome"], W3U)
    for rel in RITUAL:
        add(rel, u"注入の一覧", u"行の 結果", lambda d: d["注入の一覧"], lambda r: r["結果"], W3)
    for rec, sec, ps in (("lastbranch_2026-10-21", "L7", ("P24", "P25")), ("vocab_2026-10-21", "W6", ("P23", "P24")), ("p26_2026-10-21", "Q4", ("P25", "P26")), ("p26_2026-10-21", "Q5", ("P25", "P26"))):
        for p in ps:
            add("fixtures/xbrl/%s.json" % rec, sec, u"行の %s の state か 結果" % p, (lambda s: lambda d: d[s]["行"])(sec), _pos(p), WPOS)
    add("fixtures/xbrl/default_p26_2026-10-23.json", u"S6", u"穴 B と段 2 の数(行を持たない)", lambda d: d["S6"], None,
        ((u"穴 B 注入", ("穴 B", "注入")), (u"穴 B 既定のその他", ("穴 B", "既定のその他")), (u"段 2 注入", ("段 2", "注入")), (u"段 2 の Core 自身(既定)が GROUNDED の件", ("段 2", "全注入で Core 自身(既定)が GROUNDED", "件"))), "kv")
    add("fixtures/xbrl/default_p27_2026-10-28.json", u"S6", u"穴 B と段 2 の数(行を持たない)", lambda d: d["S6"], None,
        ((u"穴 B 注入", ("穴 B", "注入")), (u"穴 B 既定のその他", ("穴 B", "既定の結果", "その他")), (u"段 2 注入", ("段 2", "注入")), (u"段 2 の Core 自身(既定)が GROUNDED の件", ("段 2", "全注入で Core 自身(既定)が GROUNDED", "件"))), "kv")
    add("fixtures/xbrl/cd8/attr_inject_2026-10-17.json", u"rows", u"行の **無効**", lambda d: d["rows"], lambda r: u"無効" if r.get(u"**無効**") else u"", (u"無効",))
    add("fixtures/kokkai/false_pass_round12_2026-10-15.json", u"rows", u"行の skipped", lambda d: d["rows"], lambda r: u"skipped" if r.get("skipped") else u"", (u"skipped",))
    add("fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json", u"rows", u"行の 対応が付いた", lambda d: d["rows"], lambda r: u"対応が付いた" if r[u"対応が付いた"] else u"対応が付かない", (u"対応が付いた", u"対応が付かない"))
    add("fixtures/xbrl/gen_c/c0_2026-10-20.json", u"C0-2 rows", u"行の 対応が付いた", lambda d: d["C0-2 rows"], lambda r: u"対応が付いた" if r[u"対応が付いた"] else u"対応が付かない", (u"対応が付いた", u"対応が付かない"))
    add("fixtures/xbrl/cd8/rowclaim_map_2026-10-17.json", u"合計", u"合計の欄(多対一を数えた記録)", lambda d: d[u"合計"], None,
        ((u"行", ("行",)), (u"対応が付かない行", ("対応が付かない行",)), (u"共有された行", ("共有された行",)), (u"共有された主張", ("共有された主張",)), (u"T5", ("T5",)), (u"T5 のうち 1 対 1", ("T5 のうち 1 対 1",)), (u"T5 のうち共有", ("T5 のうち共有",))), "kv")
    add("fixtures/xbrl/cd8/material_2026-10-17.json", u"合計", u"合計の欄", lambda d: d[u"合計"], None, ((u"書類", ("書類",)), (u"行", ("行",)), (u"注入", ("注入",))), "kv")
    add("fixtures/xbrl/fresh/fresh_2026-10-21.json", u"注入の行", u"行の 結果 P26 の state", lambda d: d[u"注入の行"], lambda r: (r[u"結果"]["P26"] or [""])[0], (u"GROUNDED",))
    add("fixtures/xbrl/t2_pass_diag_2026-10-28.json", u"rows", u"行の 結果 P22 の state(通した行だけの記録)", lambda d: d["rows"], lambda r: (r[u"結果"]["P22"] or [""])[0], (u"GROUNDED",))
    add(INJECT_REACH_REL, u"rows", u"行の profile P22 の 分類", lambda d: d["rows"], lambda r: r["profile"]["P22"][u"分類"], W6)
    return S


def run_spec(R, spec):
    u"""(行数 or None, [(語, 数)])。"""
    k, rec, sec, col, rowsf, valf, words, kind = spec
    d = R.get(rec)
    if kind == "kv":
        base = rowsf(d)
        res = []
        for label, path in words:
            v = base
            for key in path:
                v = v[key]
            res.append((label, v))
        return None, res
    rows = rowsf(d)
    vals = [valf(r) for r in rows]
    res = []
    for w in words:
        res.append((w, sum(1 for v in vals if v == w or v.startswith(w + u"("))))
    return len(rows), res


def fmt_words(res):
    return u"・".join(u"%s %d" % (w, n) for w, n in res)


def reach_block(R):
    out = []
    for spec in reach_specs():
        n, res = run_spec(R, spec)
        out.append([spec[0], bt(spec[1]), spec[2], spec[3], u"―" if n is None else str(n), fmt_words(res)])
    return table([u"K", u"記録の path", u"節", u"数えた欄", u"行", u"語と数"], out)


def reach_cell(R, ks):
    u"""仕掛けの表の『記録に残る届かなかった行』(記録から)。ks = K の番号の列。"""
    if not ks:
        return u"記録に該当の欄なし"
    spec = dict((s[0], s) for s in reach_specs())
    n, res = run_spec(R, spec[ks[0]])
    head = (u"%d 行で " % n if n is not None else u"") + fmt_words(res)
    return u"%s(%s → 表 reach)" % (head, u"・".join(ks))


# ritual / p27 の記録
def ritual_rows(R):
    out = []
    for rel in RITUAL:
        d = R.get(rel)
        rows = d[u"注入の一覧"]
        key = [k for k in d if u"のうち参照先が動いた" in k][0]
        moved = sum(1 for x in rows if x[u"結果"] == "PASSED" and x.get(u"参照先が動いた"))
        moved2 = sum(1 for x in rows if x[u"結果"] == "PASSED" and x.get(u"参照先(注入前)") != x.get(u"参照先(注入後)"))
        out.append((rel, len(rows), sum(1 for x in rows if x[u"結果"] == "PASSED"), d[key], moved, moved2))
    return out


def ritual_block(R):
    return table([u"記録の path", u"行", u"通した(PASSED)", u"記録の『通した のうち参照先が動いた』", u"行の欄 参照先が動いた で数え直した数", u"参照先(注入前)と(注入後)の違いで数え直した数"],
                 [[bt(r[0])] + [str(x) for x in r[1:]] for r in ritual_rows(R)])


def p27_info(R):
    out = collections.OrderedDict()
    for rel in P27:
        d = R.get(rel)
        rows = d[u"行"]
        profs = [k for k in rows[0] if re.match(r"^P2\d", k)]
        tot = collections.defaultdict(collections.Counter)
        for doc, v in d[u"書類別の数え"].items():
            for t, c in v.items():
                for kk, n in c.items():
                    if isinstance(n, int):
                        tot[t][kk] += n
        cnt = dict((p, collections.Counter(x[p][u"結果"] for x in rows)) for p in profs)
        other = dict((p, set(x[u"id"] for x in rows if x[p][u"結果"] == u"名指したが別の値")) for p in profs)
        out[rel] = {"rows": rows, "profs": profs, "tot": tot, "cnt": cnt, "other": other, "rowkeys": list(rows[0].keys()), "profkeys": list(rows[0][profs[0]].keys())}
    return out


def p27_block(R):
    info = p27_info(R)
    lines = []
    for rel, x in info.items():
        n = len(x["rows"])
        t1 = x["tot"]["T1_VALUE"]
        t8 = x["tot"]["T8_REL"]
        lines.append([bt(rel), str(n), u"%d / %d" % (t1[u"基準に対応が付かない"], t1[u"採った"]), u"%d / %d" % (t8[u"基準に対応が付かない"], t8[u"採った"]),
                      u"・".join(x["rowkeys"]), u"・".join(x["profkeys"])])
    head = table([u"記録の path", u"注入の行", u"T1_VALUE の基準に対応が付かない / 採った(書類別の数えの合計)", u"T8_REL の基準に対応が付かない / 採った",
                  u"行の欄", u"profile の欄"], lines)
    body = []
    for rel, x in info.items():
        for p in x["profs"]:
            c = x["cnt"][p]
            body.append([bt(rel), p, str(len(x["rows"])), str(c[u"通した"]), str(c[u"名指したが別の値"]), str(c[u"対応が付かない"])])
    head2 = table([u"記録の path", u"profile", u"行", u"通した", u"名指したが別の値", u"対応が付かない"], body)
    ev = info[P27[0]]
    ov = []
    ps = ev["profs"]
    for i, a in enumerate(ps):
        for b in ps[i + 1:]:
            both = len(ev["other"][a] & ev["other"][b])
            ov.append([u"%s・%s" % (a, b), str(both), str(len(ev["other"][a] - ev["other"][b])), str(len(ev["other"][b] - ev["other"][a]))])
    head3 = table([u"評価用の『名指したが別の値』の行の重なり", u"両方", u"前の profile だけ", u"後の profile だけ"], ov)
    return head + [u""] + head2 + [u""] + head3


def p27_facts(R):
    info = p27_info(R)
    ev = info[P27[0]]
    t1 = ev["tot"]["T1_VALUE"]
    other = dict((p, len(ev["other"][p])) for p in ev["profs"])
    both = len(ev["other"]["P26"] & ev["other"]["P27"])
    only = len(ev["other"]["P26"] - ev["other"]["P27"]) + len(ev["other"]["P27"] - ev["other"]["P26"])
    return {"t1_nomap": t1[u"基準に対応が付かない"], "t1_taken": t1[u"採った"], "other": other, "both": both, "only": only, "info": info}


# ----------------------------------------------------------------------------------------------------------------
# 文書の判断の表を読む
def parse_judgments(doc):
    u"""文書の judgment の表を読む(判断は文書の側に在る)。"""
    B = doc_blocks(doc)
    files = collections.OrderedDict()
    for c in rows_of(B["files"]):
        files[unbt(c[1])] = {"role": c[5], "note": c[6]}
    mech = collections.OrderedDict()
    for c in rows_of(B["mech"]):
        mech[c[0]] = {"file": unbt(c[1]), "funcs": split_list(c[2]), "role": c[3], "obj": c[4], "base": c[5], "after": c[6], "check": c[7], "hole": c[8], "reach": c[9]}
    ref = collections.OrderedDict()
    for c in rows_of(B["ref"]):
        ref[c[0]] = {"users": split_list(c[1]), "recs": split_list(c[2]), "docs": split_list(c[3]), "ledger": c[4]}
    ledger = collections.OrderedDict()
    for c in rows_of(B["ledger"]):
        ledger[c[0]] = {"mechs": c[1], "kinds": c[2], "read": c[3], "why": c[4], "quote": unbt(c[5]) if c[5].startswith(u"`") else c[5]}
    verdict = collections.OrderedDict()
    for c in rows_of(B["verdict"]):
        verdict[c[0]] = {"text": c[3]}
    ev = collections.OrderedDict()
    cur = None
    for l in B["evidence"]:
        m = re.match(r"^\*\*(M-\d+)\*\* `([^`]+)` の `([^`]+)`$", l)
        if m:
            cur = m.group(1)
            ev[cur] = {"file": m.group(2), "func": m.group(3), "quote": None}
        elif l.startswith(u"> ") and cur:
            ev[cur]["quote"] = l[2:]
    outside = collections.OrderedDict()
    for c in rows_of(B["outside"]):
        outside[unbt(c[0])] = {"calls": c[1], "marks": c[2], "role": c[3], "note": c[4]}
    return {"files": files, "mech": mech, "ref": ref, "ledger": ledger, "evidence": ev, "outside": outside, "verdict": verdict}


# ----------------------------------------------------------------------------------------------------------------
# (c) 台帳
def ledger_lines(root):
    out = collections.OrderedDict()
    for l in jtext(os.path.join(root, LEDGER_REL)).splitlines():
        m = LEDGER_ID.match(l)
        if m:
            out[m.group(1)] = l
    return out


def ledger_key(i):
    return ("LDHP".index(i[0]), int(i[2:]))


def ledger_pick(lines, J):
    u"""§2-4 の規準。同じ型の仕掛けごとに、(記録の path・script の file 名・結果文書の file 名)のどれかが行の字に在る台帳の行。{ID: {mech: [kinds]}}。"""
    out = {}
    for mid, m in J["mech"].items():
        if cut(m["hole"]) != u"同じ型":
            continue
        r = J["ref"][mid]
        scripts = [os.path.basename(m["file"])] + [os.path.basename(u) for u in r["users"]]
        for i, l in lines.items():
            kinds = []
            if any(x in l for x in r["recs"]):
                kinds.append(u"記録")
            if any(x in l for x in scripts):
                kinds.append(u"script")
            if any(x in l for x in r["docs"]):
                kinds.append(u"結果文書")
            if kinds:
                out.setdefault(i, {})[mid] = kinds
    return out


def ledger_cell(pick, mid):
    ids = sorted([i for i, v in pick.items() if mid in v], key=ledger_key)
    return u"・".join(ids) if ids else u"なし(台帳の行に記録の path・script 名・結果文書名が無い)"


def ledger_block(J, pick):
    rows = []
    for i in sorted(pick, key=ledger_key):
        d = J["ledger"].get(i, {"read": u"", "why": u"", "quote": u""})
        kinds = sorted(set(k for v in pick[i].values() for k in v), key=[u"記録", u"script", u"結果文書"].index)
        q = d["quote"]
        rows.append([i, u"・".join(sorted(pick[i])), u"・".join(kinds), d["read"], d["why"], bt(q) if q else u""])
    return table([u"台帳の行", u"引いた仕掛け", u"一致した字", u"読み", u"根拠", u"行の字(引用)"], rows)


# ----------------------------------------------------------------------------------------------------------------
# 文書の表を作り直す
def files_block(enum, J):
    rows = []
    for n, (rel, ln, hits, nm) in enumerate(enum, 1):
        d = J["files"].get(rel, {"role": u"", "note": u""})
        rows.append([str(n), bt(rel), str(ln), u"・".join(bt(h) for h in hits) if hits else u"―", u"名" if nm else u"―", d["role"], d["note"]])
    return table([u"#", u"path", u"行数", u"(a) で当たった字", u"(b)", u"役", u"仕掛け(関数)・使う先"], rows)


def mech_block(R, J, pick):
    rows = []
    for mid, m in J["mech"].items():
        ks = re.findall(r"K-\d+", m["reach"])
        cell = reach_cell(R, ks)
        if u"p27rec" in m["reach"]:
            cell = u"評価用・調整用の記録の『基準に対応が付かない』『対応が付かない』(→ 表 p27rec)"
        rows.append([mid, bt(m["file"]), join_list(m["funcs"]), m["role"], m["obj"], m["base"], m["after"], m["check"], m["hole"], cell])
    return table([u"ID", u"仕掛け(file)", u"関数", u"役", u"注入の対象", u"基準の対応付け", u"注入後の対応付け", u"届いたことの確かめ", u"穴の型", u"記録に残る届かなかった行"], rows)


def ref_block(J, pick):
    rows = []
    for mid in J["mech"]:
        r = J["ref"].get(mid, {"users": [], "recs": [], "docs": []})
        same = cut(J["mech"][mid]["hole"]) == u"同じ型"
        rows.append([mid, join_list(r["users"]), join_list(r["recs"]), join_list(r["docs"]), ledger_cell(pick, mid) if same else u"―(同じ型でない)"])
    return table([u"ID", u"使う側の script", u"記録", u"結果文書", u"依存する台帳の行"], rows)


def outside_block(root, crit, J):
    rows = []
    byrel = dict((r[0], r) for r in outside_criterion(root, crit))
    for rel, d in J["outside"].items():
        r = byrel.get(rel)
        rows.append([bt(rel), u"・".join(bt(c) for c in r[1]) if r else u"―", u"・".join(bt(m) for m in r[2]) if r else u"―", d["role"], d["note"]])
    return table([u"path", u"呼んでいる検査", u"本文の差し替えの字", u"役", u"注"], rows)


def verdict_block(R, J, pick):
    u"""同じ型の仕掛けごとに、数の出どころ(記録の欄。機械)・数(記録から)・言えること(文書の判断)・台帳の『通った』行(機械)。"""
    rows = []
    spec = dict((s[0], s) for s in reach_specs())
    f = p27_facts(R)
    for mid, m in J["mech"].items():
        if cut(m["hole"]) != u"同じ型":
            continue
        ks = re.findall(r"K-\d+", m["reach"])
        if u"p27rec" in m["reach"]:
            src = u"評価用・調整用の記録の行・書類別の数え(→ 表 p27rec)"
            ev = f["info"][P27[0]]
            c = ev["cnt"]
            num = u"評価用の注入の行 %d: 対応が付かない %d(各 profile)・基準に対応が付かない T1 %d / %d・名指したが別の値 P22 %d・P26 %d・P27 %d・通した P22 %d・P26 %d" % (
                len(ev["rows"]), c["P22"][u"対応が付かない"], f["t1_nomap"], f["t1_taken"], c["P22"][u"名指したが別の値"], c["P26"][u"名指したが別の値"], c["P27"][u"名指したが別の値"],
                c["P22"][u"通した"], c["P26"][u"通した"])
        elif ks:
            src = u"・".join(u"%s %s %s" % (os.path.basename(spec[k][1]), spec[k][2], spec[k][3]) for k in ks)
            n, res = run_spec(R, spec[ks[0]])
            num = (u"%d 行で " % n if n is not None else u"") + fmt_words(res) + (u"(%s ほか)" % ks[0] if len(ks) > 1 else u"")
        else:
            src = u"記録に該当の欄なし(記録は材料の Core 欄・行ごとの結果)"
            num = u"―"
        thru = sorted([i for i, d in J["ledger"].items() if mid in pick.get(i, {}) and d["read"] == u"通った"], key=ledger_key)
        rows.append([mid, src, num, J["verdict"].get(mid, {"text": u""})["text"], u"・".join(thru) if thru else u"―"])
    return table([u"ID", u"数の出どころ(記録の欄)", u"数(記録から)", u"言えること", u"台帳の読みが『通った』の行"], rows)


def counts_facts(J):
    mech = J["mech"]
    kinds = collections.Counter(cut(m["check"]) for m in mech.values())
    holes = collections.Counter(cut(m["hole"]) for m in mech.values())
    roles = collections.Counter(cut(f["role"]) for f in J["files"].values())
    return kinds, holes, roles


def summary_block(J, pick, enum, nmeasure, nfix, nfixhit, nout, ncopy):
    kinds, holes, roles = counts_facts(J)
    rows = [[u"measure/**/*.py の file", str(nmeasure)], [u"規準に当たった file", str(len(enum))],
            [u"仕掛け(表の行)", str(len(J["mech"]))],
            [u"届いたことの確かめ 有", str(kinds[u"有"])], [u"同 無", str(kinds[u"無"])], [u"同 不要", str(kinds[u"不要"])],
            [u"穴の型 同じ型", str(holes[u"同じ型"])], [u"穴の型 別の型", str(holes[u"別の型"])], [u"穴の型 無し", str(holes[u"無し"])],
            [u"file の役 仕掛け持ち(+ 使う側を含む)", str(sum(1 for f in J["files"].values() if cut(f["role"]).startswith(u"仕掛け持ち")))],
            [u"file の役 使う側だけ", str(roles[u"使う側"])], [u"file の役 共通部品", str(roles[u"共通部品"])], [u"file の役 対象外", str(roles[u"対象外"])],
            [u"台帳の行(§2-4 の規準)", str(len(pick))],
            [u"読み 通った", str(sum(1 for d in J["ledger"].values() if d["read"] == u"通った"))],
            [u"読み 通っていない", str(sum(1 for d in J["ledger"].values() if d["read"] == u"通っていない"))],
            [u"読み 記録から分からない", str(sum(1 for d in J["ledger"].values() if d["read"] == u"記録から分からない"))],
            [u"言えること 診断済み", str(sum(1 for d in J["verdict"].values() if cut(d["text"]) == u"診断済み"))],
            [u"言えること 対応付けの数でありうる", str(sum(1 for d in J["verdict"].values() if cut(d["text"]) == u"対応付けの数でありうる"))],
            [u"言えること 分けられない", str(sum(1 for d in J["verdict"].values() if cut(d["text"]) == u"分けられない"))],
            [u"cd8 の行 → claim の対応付けを持つ file(cd_material を含む)", str(ncopy)],
            [u"副産物の検査で見つかった規準の外の file", str(nout)],
            [u"fixtures/**/*.py の file / 規準に当たった file", u"%d / %d" % (nfix, nfixhit)]]
    return table([u"数えたもの", u"数"], rows)


# ----------------------------------------------------------------------------------------------------------------
# (d) 当否
def judge(R, J, seal, enum, crit, root=ROOT):
    u"""{名前: (実測の字, 当たりか(True / False / None))}。封 §3 の予測を、文書の表と記録から。幅は封の字から読む。"""
    SP = seal_predictions(seal)
    out = collections.OrderedDict()
    mech, files = J["mech"], J["files"]
    kinds, holes, roles = counts_facts(J)

    def rg(k):
        return ranges_of(SP[k][1])[0]

    def within(n, r):
        return r[0] <= n <= r[1]
    n = len(mech)
    out["H-1"] = (u"仕掛け(表の行)は %d" % n, within(n, rg("H-1")))
    out["H-2"] = (u"確かめ 有は %d" % kinds[u"有"], within(kinds[u"有"], rg("H-2")))
    out["H-3"] = (u"確かめ 無は %d" % kinds[u"無"], within(kinds[u"無"], rg("H-3")))
    out["H-4"] = (u"確かめ 不要は %d" % kinds[u"不要"], within(kinds[u"不要"], rg("H-4")))
    same = [mid for mid, m in mech.items() if cut(m["hole"]) == u"同じ型"]
    fresh_in = any(os.path.basename(mech[mid]["file"]).startswith("xbrl_fresh_") for mid in same)
    tune_in = any(os.path.basename(mech[mid]["file"]).startswith("xbrl_p27_tune_2") for mid in same)
    out["H-5"] = (u"同じ型は %d(新しい標本の注入 %s・調整用の注入 %s)" % (len(same), u"入る" if fresh_in else u"入らない", u"入る" if tune_in else u"入らない"),
                  within(len(same), rg("H-5")) and fresh_in and tune_in)
    ids = [mid for mid, m in mech.items() if cut(m["base"]) == u"site の id" and cut(m["after"]).startswith(u"同じ id")]
    bad = [mid for mid in ids if cut(mech[mid]["check"]) == u"無"]
    out["H-6"] = (u"site の id と同じ id で引く仕掛け %d(%s)、そのうち確かめ 無 %d" % (len(ids), u"・".join(ids), len(bad)), bool(ids) and not bad)
    # H-7 / H-8 / H-9 / H-10 / H-11: 記録
    pb = R.get("fixtures/xbrl/period_bind_2026-10-20.json")["E1"]["行"]
    has_field = any(("id_shift" in r or "sentence_not_found" in r) for r in pb)
    cnt = collections.Counter(r["P22"].get("state") for r in pb)
    ids_n, snf_n = cnt["id_shift"], cnt["sentence_not_found"]
    r7 = rg("H-7")
    out["H-7"] = (u"period_bind E1 の P22 の state: id_shift %d・sentence_not_found %d、行に id_shift・sentence_not_found の欄: %s" % (ids_n, snf_n, u"在る" if has_field else u"無い"),
                  within(ids_n, r7) and within(snf_n, r7) and has_field)
    rit = ritual_rows(R)
    out["H-8"] = (u"儀式 4 本の『通した のうち参照先が動いた』: %s" % u"・".join(str(x[3]) for x in rit), all(x[3] == 0 for x in rit))
    info = p27_info(R)
    bad9 = []
    for rel, x in info.items():
        for k in x["rowkeys"] + x["profkeys"]:
            if any(w in k for w in (u"文の番号", u"位置", u"届", u"sentence")):
                bad9.append(k)
    out["H-9"] = (u"3 本の行・profile の欄に文の番号・位置・届いた/届かないの欄: %s" % (u"無い" if not bad9 else u"在る(%s)" % u"・".join(bad9)), not bad9)
    word10 = re.search(u"「(.+?)」", SP["H-10"][0]).group(1)
    ev = info[P27[0]]
    per = dict((p, sum(1 for x in ev["rows"] if x[p][u"結果"] == word10)) for p in ("P22", "P26", "P27"))
    both = len(ev["other"]["P26"] & ev["other"]["P27"]) if word10 == u"名指したが別の値" else None
    only = (len(ev["other"]["P26"] - ev["other"]["P27"]) + len(ev["other"]["P27"] - ev["other"]["P26"])) if both is not None else None
    ok10 = bool(both is not None and all(per[p] >= 1 for p in per) and both > only)
    out["H-10"] = (u"評価用『%s』: P22 %d・P26 %d・P27 %d、P26 と P27 の両方 %s・どちらか一方だけ %s" % (word10, per["P22"], per["P26"], per["P27"], both, only), ok10)
    f = p27_facts(R)
    lo11 = pcts_of(SP["H-11"][1])[0]
    out["H-11"] = (u"評価用 T1_VALUE の基準に対応が付かない %d / 採った %d = %.1f%%" % (f["t1_nomap"], f["t1_taken"], 100.0 * f["t1_nomap"] / f["t1_taken"]), f["t1_nomap"] * 100 >= lo11 * f["t1_taken"])
    pick = ledger_pick(ledger_lines(root), J)
    out["H-12"] = (u"同じ型の仕掛け(と使う側)を引く台帳の行は %d" % len(pick), within(len(pick), rg("H-12")))
    out["H-13"] = (u"対象外の file は %d" % roles[u"対象外"], within(roles[u"対象外"], rg("H-13")))
    kp = [mid for mid, m in mech.items() if os.path.basename(m["file"]).startswith("kokkai_false_pass_")]
    ki = [rel for rel in files if os.path.basename(rel).startswith("kokkai_inject_")]
    ki_mech = [mid for mid, m in mech.items() if os.path.basename(m["file"]).startswith("kokkai_inject_")]
    ok14 = bool(kp) and bool(ki) and all(cut(mech[m]["hole"]) != u"同じ型" for m in kp + ki_mech)
    out["H-14"] = (u"kokkai_false_pass %s・kokkai_inject は役 %s" % (u"・".join(cut(mech[m]["hole"]) for m in kp), u"・".join(cut(files[r]["role"]) for r in ki)), ok14)
    at = [mid for mid, m in mech.items() if os.path.basename(m["file"]).startswith("xbrl_attr_inject_")]
    ok15 = bool(at) and all(cut(mech[m]["hole"]) == u"別の型" and cut(mech[m]["check"]) == u"有" for m in at)
    out["H-15"] = (u"attr_inject: 穴の型 %s・確かめ %s" % (u"・".join(cut(mech[m]["hole"]) for m in at), u"・".join(cut(mech[m]["check"]) for m in at)), ok15)
    cm = [mid for mid, m in mech.items() if os.path.basename(m["file"]).startswith("xbrl_cd_material_")]
    copies = [c for c in mapping_copies(root) if not os.path.basename(c).startswith("xbrl_cd_material_")]
    ok16 = bool(cm) and all(cut(mech[m]["hole"]) == u"同じ型" and cut(mech[m]["check"]) == u"無" for m in cm) and len(copies) >= 1
    out["H-16"] = (u"cd_material: 穴の型 %s・確かめ %s、同じ対応付けを持つ他の file %d" % (u"・".join(cut(mech[m]["hole"]) for m in cm), u"・".join(cut(mech[m]["check"]) for m in cm), len(copies)), ok16)
    return out


def hit_word(b):
    return u"**判定しない**" if b is None else (u"**当たり**" if b else u"**外れ**")


def pred_block(seal, jd):
    SP = seal_predictions(seal)
    rows = []
    for k, v in jd.items():
        rows.append([u"**%s**" % k, SP[k][0], SP[k][1], SP[k][2], v[0], hit_word(v[1])])
    return table([u"#", u"欄", u"予測(封の字のまま)", u"外れ方(封の字のまま)", u"実測(文書の表と記録から)", u"当否"], rows)


def render_blocks(R, J, seal, root=ROOT, crit=None, extra=None):
    crit = crit or seal_criterion(seal)
    enum, nmeasure = enumerate_measure(root, crit, extra)
    pick = ledger_pick(ledger_lines(root), J)
    jd = judge(R, J, seal, enum, crit, root)
    nfix, nfixhit = fixtures_py(root, crit)
    out = collections.OrderedDict()
    out["pred"] = pred_block(seal, jd)
    out["files"] = files_block(enum, J)
    out["outside"] = outside_block(root, crit, J)
    out["mech"] = mech_block(R, J, pick)
    out["evidence"] = None            # 判断の根拠(関数の中の字)。check_evidence が見る
    out["ref"] = ref_block(J, pick)
    out["reach"] = reach_block(R)
    out["ritual"] = ritual_block(R)
    out["p27rec"] = p27_block(R)
    out["ledger"] = ledger_block(J, pick)
    out["verdict"] = verdict_block(R, J, pick)
    out["summary"] = summary_block(J, pick, enum, nmeasure, nfix, nfixhit, len(outside_criterion(root, crit, extra)), len(mapping_copies(root)))
    return out, jd


def check_c(R, J, seal, doc, root=ROOT, extra=None):
    u"""文書の表を、記録と規準と文書の判断の表から作り直して比べる。問題の列。"""
    out = []
    try:
        B, _jd = render_blocks(R, J, seal, root, None, extra)
    except Exception as e:      # 記録や文書の判断が壊れていれば作り直せない(それも赤)
        return [u"表を作れない: %r" % (e,)]
    got = doc_blocks(doc)
    if list(got) != list(B):
        out.append(u"文書の門の表の名前と順が違う: %s" % list(got))
        return out
    for k, lines in B.items():
        if lines is None:
            continue
        if got[k] != lines:
            out.append(u"文書の表『%s』が作り直した表と違う" % k)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (a)(b) の検査
def seal_files_table(seal):
    rows = re.findall(r"^\| (\d+) \| `(measure/[^`]+)` \| (\d+) \| (.*?) \| (名|―) \|$", seal, re.M)
    out = []
    for n, rel, ln, hits, nm in rows:
        out.append((rel, int(ln), [x.strip("`") for x in hits.split(u"・")] if hits != u"―" else [], nm == u"名"))
    return out


def check_a(J, seal, doc, root=ROOT, extra=None):
    out = []
    crit = seal_criterion(seal)
    if not crit["a"] or len(crit["a"]) != 7 or crit["b"] != [u"inject", u"false_pass"]:
        out.append(u"封の規準の字を読めない: %r" % (crit,))
        return out
    enum, nmeasure = enumerate_measure(root, crit, extra)
    rels = [e[0] for e in enum]
    if set(rels) != set(J["files"]):
        out.append(u"文書の表の file の集合が規準の列挙と違う: 足りない %s / 余り %s" % (sorted(set(rels) - set(J["files"])), sorted(set(J["files"]) - set(rels))))
    sealed = seal_files_table(seal)
    if extra is None and sealed != enum:
        out.append(u"封 §1-2 の表が規準の列挙と違う")
    for rel, d in J["files"].items():
        if cut(d["role"]) not in VOC_ROLE:
            out.append(u"役の語が決まった語でない: %s %s" % (rel, d["role"]))
        if not d["note"].strip():
            out.append(u"仕掛け・使う先の欄が空: %s" % rel)
    # 仕掛け持ちの file と仕掛けの表の file が対応する
    mfiles = set(m["file"] for m in J["mech"].values())
    holders = set(rel for rel, d in J["files"].items() if cut(d["role"]).startswith(u"仕掛け持ち"))
    if mfiles != holders:
        out.append(u"仕掛けの表の file と役が仕掛け持ちの file が違う: %s / %s" % (sorted(mfiles - holders), sorted(holders - mfiles)))
    return out


def func_source(path, name, src=None):
    u"""file の中の関数 name(どの深さでも)の字。無ければ None。src を渡すとその本文(封の commit の木の blob など)から。"""
    src = jtext(path) if src is None else src
    tree = ast.parse(src)
    lines = src.split(u"\n")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return [l.strip() for l in lines[node.lineno - 1:node.end_lineno]]
    return None


def check_b(R, J, root=ROOT):
    u"""仕掛けの表の語彙・関数名・根拠の字・使う側・記録の実在。"""
    out = []
    mech, ref, ev = J["mech"], J["ref"], J["evidence"]
    if list(mech) != ["M-%02d" % i for i in range(1, len(mech) + 1)]:
        out.append(u"仕掛けの ID が M-01 から続いていない")
    for mid, m in mech.items():
        if m["role"] != u"仕掛け持ち":
            out.append(u"%s: 役が仕掛け持ちでない" % mid)
        for col, voc in (("obj", VOC_OBJ), ("base", VOC_BASE), ("after", VOC_AFTER), ("check", VOC_CHECK), ("hole", VOC_HOLE)):
            if cut(m[col]) not in voc:
                out.append(u"%s: %s の語が決まった語でない: %s" % (mid, col, m[col]))
        if cut(m["check"]) == u"有" and cut(m["hole"]) == u"同じ型":
            out.append(u"%s: 確かめ 有 なのに穴の型が同じ型" % mid)
        if cut(m["check"]) == u"無" and cut(m["hole"]) != u"同じ型":
            out.append(u"%s: 確かめ 無 なのに穴の型が同じ型でない" % mid)
        path = os.path.join(root, m["file"])
        if not os.path.exists(path):
            out.append(u"%s: file が無い %s" % (mid, m["file"]))
            continue
        if not m["funcs"]:
            out.append(u"%s: 関数名が空" % mid)
        for fn in m["funcs"]:
            if func_source(path, fn, file_text(root, m["file"])) is None:
                out.append(u"%s: 関数 %s が %s に無い" % (mid, fn, m["file"]))
        # 根拠の字
        e = ev.get(mid)
        if e is None or not e["quote"]:
            out.append(u"%s: 根拠の字が無い" % mid)
        else:
            if e["file"] != m["file"] or e["func"] not in m["funcs"]:
                out.append(u"%s: 根拠の file・関数が仕掛けの表と違う" % mid)
            src = func_source(path, e["func"], file_text(root, m["file"]))
            if src is None or e["quote"].strip() not in src:
                out.append(u"%s: 根拠の字が関数 %s の中に無い" % (mid, e["func"]))
            if u"|" in e["quote"] or u"`" in e["quote"]:
                out.append(u"%s: 根拠の字に表を壊す字" % mid)
        # 使う側・記録・結果文書の実在
        r = ref.get(mid)
        if r is None:
            out.append(u"%s: 使う側・記録の表に行が無い" % mid)
            continue
        for u in r["users"]:
            if not os.path.exists(os.path.join(root, u)):
                out.append(u"%s: 使う側が無い %s" % (mid, u))
        for rec in r["recs"]:
            if not os.path.exists(os.path.join(root, rec)):
                out.append(u"%s: 記録が無い %s" % (mid, rec))
        for d in r["docs"]:
            if not os.path.exists(os.path.join(root, "docs", d)):
                out.append(u"%s: 結果文書が無い %s" % (mid, d))
        # 使う側は、仕掛けの file の名か、挙げた記録の名を本文に持つ(使っている印)
        base = os.path.splitext(os.path.basename(m["file"]))[0]
        recnames = [os.path.basename(x) for x in r["recs"]]
        for u in r["users"]:
            p = os.path.join(root, u)
            if os.path.exists(p) and os.path.basename(u) != os.path.basename(m["file"]):
                t = file_text(root, u)
                if base not in t and not any(x in t for x in recnames):
                    out.append(u"%s: 使う側 %s が仕掛けの file も記録も本文に持たない" % (mid, u))
        # 『記録に残る届かなかった行』の K は実在する
        ks = re.findall(r"K-\d+", m["reach"])
        spec = set(s[0] for s in reach_specs())
        for k in ks:
            if k not in spec:
                out.append(u"%s: 知らない K %s" % (mid, k))
        for k in ks:
            s = [x for x in reach_specs() if x[0] == k]
            if s and not any(os.path.basename(s[0][1]) == os.path.basename(x) for x in r["recs"]):
                out.append(u"%s: %s の記録が使う側・記録の表に無い" % (mid, k))
    if list(ev) != list(mech):
        out.append(u"根拠の並びが仕掛けの表と違う")
    same = [mid for mid, m in mech.items() if cut(m["hole"]) == u"同じ型"]
    if list(J["verdict"]) != same:
        out.append(u"言えることの表の仕掛けが同じ型の仕掛けと違う: %s / %s" % (list(J["verdict"]), same))
    for mid, d in J["verdict"].items():
        w = cut(d["text"])
        if w not in VOC_VERDICT:
            out.append(u"%s: 言えることの語が決まった語でない: %s" % (mid, w))
        if len(d["text"].strip()) < len(w) + 10:
            out.append(u"%s: 言えることの注が短い・無い" % mid)
        diagnosed = os.path.basename(mech[mid]["file"]).startswith("xbrl_fresh_") if mid in mech else False
        if (w == u"診断済み") != diagnosed:
            out.append(u"%s: 診断済みは前の 2 便が位置で数えた仕掛け(新しい標本の注入)だけ" % mid)
        if (w == u"分けられない") != (u"p27rec" in mech[mid]["reach"] if mid in mech else False):
            out.append(u"%s: 分けられないは記録に注入後の claim の id が無い系統(評価用・調整用)だけ" % mid)
    # 規準の外の file(別の表)
    for rel in J["outside"]:
        if not os.path.exists(os.path.join(root, rel)):
            out.append(u"規準の外の表の file が無い: %s" % rel)
    return out


#: 365b468 より後に足された(または変わった)``measure/**/*.py`` のうち、いまの木で規準(封 §1-1)か副産物の検査(封 §6-4 の 6)に当たる file の宣言。
#: (path, 役, 届いたことの確かめ, 根拠の字を持つ関数, 根拠の字(その関数の中の 1 行), 足した日付)。役は VOC_ROLE、確かめは VOC_CHECK の語。
#: 宣言に無い file が在れば赤、宣言に在るのに当たらない・存在しない file も赤。止めた理由の script は 2026-10-29 の重ね直しで宣言した(下の 2 行目)。
LATER_HARNESS_FILES = (
    ("measure/xbrl_p27_inject_reach_2026-10-29.py", u"仕掛け持ち + 使う側", u"有", "work_doc", u"reached = bool(tidx is not None and si == tidx)", "2026-10-29"),
    ("measure/xbrl_stop_reason_2026-10-29.py", u"使う側", u"有", "work", u"r = RE.work_doc(a)", "2026-10-29"),
)
LATER_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def later_hits(root, crit, extra=None):
    u"""封の commit の木に無い・本文が違う file のうち、**いまの木**で規準か副産物の検査に当たるもの。(OrderedDict {rel: 本文}, [rel])。extra = 偽の file を足す試験用。"""
    pinned = measure_texts(root)
    live = live_measure_texts(root)
    for rel, tx in (extra or {}).items():
        live[rel] = tx
    hit = set(r[0] for r in enumerate_measure(root, crit, None, live)[0]) | set(r[0] for r in outside_criterion(root, crit, None, live))
    return live, sorted(rel for rel in hit if pinned.get(rel) != live[rel])


def check_later(root, crit, decl=None, extra=None):
    u"""(h) 後から足した file の宣言。問題の列。"""
    decl = LATER_HARNESS_FILES if decl is None else decl
    live, later = later_hits(root, crit, extra)
    out = []
    seen = collections.Counter(d[0] for d in decl)
    for rel in later:
        if rel not in seen:
            out.append(u"宣言が無い: 封の commit より後に足された・変わった file が規準か副産物の検査に当たる: %s" % rel)
    for d in decl:
        if len(d) != 6:
            out.append(u"宣言の欄が 6 つでない: %r" % (d,))
            continue
        rel, role, chk, fn, quote, day = d
        if seen[rel] > 1:
            out.append(u"同じ path が 2 回宣言されている: %s" % rel)
        if rel not in live:
            out.append(u"宣言に在るのに file が無い(古い宣言): %s" % rel)
            continue
        if rel not in later:
            out.append(u"宣言に在るのに、後から足された・変わった file で規準にも副産物の検査にも当たらない(古い宣言): %s" % rel)
        if role not in VOC_ROLE:
            out.append(u"%s: 役が決まった語でない: %s" % (rel, role))
        if chk not in VOC_CHECK:
            out.append(u"%s: 届いたことの確かめが決まった語でない: %s" % (rel, chk))
        if not LATER_DATE.match(day) or day < "2026-10-29":
            out.append(u"%s: 足した日付が YYYY-MM-DD でないか封の日(2026-10-29)より前: %s" % (rel, day))
        src = func_source(rel, fn, live[rel])
        if src is None:
            out.append(u"%s: 根拠の関数 %s が file に無い" % (rel, fn))
        elif not quote.strip() or quote.strip() not in src:
            out.append(u"%s: 根拠の字が関数 %s の中に無い" % (rel, fn))
    return out


def check_ledger(J, root=ROOT):
    out = []
    lines = ledger_lines(root)
    pick = ledger_pick(lines, J)
    if set(J["ledger"]) != set(pick):
        out.append(u"文書が引く台帳の行が規準で選んだ集合と違う: 足りない %s / 余り %s" % (sorted(set(pick) - set(J["ledger"]), key=ledger_key), sorted(set(J["ledger"]) - set(pick), key=ledger_key)))
    for i, d in J["ledger"].items():
        if i not in lines:
            out.append(u"台帳に無い ID: %s" % i)
            continue
        if d["read"] not in VOC_READ:
            out.append(u"%s: 読みの語が決まった語でない: %s" % (i, d["read"]))
        if len(d["why"].strip()) < 10:
            out.append(u"%s: 根拠が短い・無い" % i)
        if not d["quote"] or d["quote"] not in lines[i]:
            out.append(u"%s: 引用が台帳の行の中に無い" % i)
    return out


def check_doc_prose(R, J, seal, doc, root=ROOT):
    out = []
    stripped = BLOCK_RE.sub(u"", doc)
    if [l for l in stripped.split(u"\n") if l.lstrip().startswith(u"|")]:
        out.append(u"門の外に表の行がある")
    bad = [l[:40] for l in stripped.split(u"\n") if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席|書類|試行|回|本|ポイント|USD|file|倍|桁|字|組|つ)", l) and NOT_GATED not in l]
    if bad:
        out.append(u"散文の数に【門なし】の印が無い: %s" % bad)
    heads = re.findall(r"^## (\d+)\.", doc, re.M)
    if heads != [str(i) for i in range(1, len(heads) + 1)] or len(heads) < 8:
        out.append(u"節の番号が 1 から続いていない・8 節に足りない: %s" % heads)
    if not (doc.index(u"<!-- 門:start pred -->") < doc.index(u"## 2.")):
        out.append(u"予測の当否が先頭(第 2 節より前)にない")
    seal_t = seal
    jd = judge(R, J, seal_t, enumerate_measure(root, seal_criterion(seal_t))[0], seal_criterion(seal_t), root)
    missed = [k for k, v in jd.items() if v[1] is False]
    want = u"外れた予測: " + (u"・".join(missed) if missed else u"なし") + u"。外れは外れのまま残す(封も予測も直さない)。" + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
        out.append(u"『外れた予測』の行が求めた当否と違う(期待: %s)" % want)
    undecided = [k for k, v in jd.items() if v[1] is None]
    if undecided:
        out.append(u"判定しない予測が在る: %s" % undecided)
    for lit in (u"記録は不変", u"engine は走らせていない", u"測っていない", u"点検だけ", NOT_GATED, u"edinetdb-p27", u"同じ型", u"封にない判断", u"次に測ること", u"言えないこと", u"判定"):
        if lit not in doc:
            out.append(u"必要な字が無い: %s" % lit)
    for w in FORBIDDEN:
        if w in doc:
            out.append(u"禁止語: %s" % w)
    if u"```" in doc:
        out.append(u"code fence がある")
    # M-14 の行に書いた台帳の ID の列は、文書の台帳の表(読みが『通った』で、根拠に M-14 を書いた行)と同じ
    m14 = [l for l in doc.split(u"\n") if l.startswith(u"- **M-14")]
    if len(m14) != 1:
        out.append(u"M-14 の行がちょうど 1 つでない")
    else:
        said = set(re.findall(r"[LDHP]-\d+", m14[0].split(u"台帳の読みが")[-1]))
        want_ids = set(i for i, d in J["ledger"].items() if d["read"] == u"通った" and u"M-14" in d["why"])
        if said != want_ids:
            out.append(u"M-14 の行の台帳の ID が台帳の表と違う: %s / %s" % (sorted(said), sorted(want_ids)))
    # 見出しの順(封 §5-2)
    order = [u"予測", u"列挙", u"仕掛けの表", u"記録から数えた数", u"依存する台帳", u"判定", u"言えないこと", u"次に測ること"]
    titles = re.findall(r"^## \d+\. (.+)$", doc, re.M)
    pos = [next((i for i, t in enumerate(titles) if o in t), None) for o in order]
    if None in pos or pos != sorted(pos):
        out.append(u"節の並びが封 §5-2 の順でない: %s" % titles)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (e)
def secret_strings(R, root=ROOT):
    u"""docID(新しい標本 30・評価用・調整用)と claim の id を記録から読む。"""
    docs = set(jload(os.path.join(root, FETCHED_REL))[u"使う書類"])
    cids = set()
    for rel in P27:
        d = R.get(rel)
        for x in d[u"行"]:
            docs.add(x[u"docID"])
            if x.get(u"基準の claim"):
                cids.add(x[u"基準の claim"])
        docs.update(d[u"書類別の数え"].keys())
        docs.update(d.get(u"対象の docID") or [])
    ir = R.get(INJECT_REACH_REL)
    for r in ir[u"rows"]:
        if r[u"基準の claim"]:
            cids.add(r[u"基準の claim"])
    return docs, cids


def check_e(seal, doc, docs, cids):
    out = []
    for name, t in ((u"封", seal), (u"文書", doc)):
        for d in docs:
            if d in t:
                out.append(u"%s に docID の字がある" % name)
                break
        if re.findall(r"S100[0-9A-Z]{4}", t):
            out.append(u"%s に docID らしい字がある" % name)
        if re.findall(r"\b[NT]\d{3}\b", t):
            out.append(u"%s に claim の id らしい字がある" % name)
        for cid in cids:
            if re.search(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(cid), t):
                out.append(u"%s に記録の claim の id の字がある" % name)
                break
        if u"```" in t:
            out.append(u"%s に code fence がある" % name)
        for w in FORBIDDEN:
            if w in t:
                out.append(u"%s に禁止語: %s" % (name, w))
    return out


# ----------------------------------------------------------------------------------------------------------------
# (f) 順序
def make_run(repo_dir):
    def run(*args):
        r = subprocess.run(["git", "-C", repo_dir] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode, r.stdout.decode("utf-8", "replace").strip()
    return run


def added_commits(run, path):
    rc, out = run("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(run, a, b):
    return a is not None and b is not None and run("merge-base", "--is-ancestor", a, b)[0] == 0


def order_problems(run, prefix, head="HEAD"):
    u"""(f) 封の commit が文書・門の commit より前。問題の列 [(符号, 文)]。追跡されていない file は『足した commit が無い』で赤(skip にしない)。"""
    problems = []
    seal = prefix + SEAL_REL
    s_list = added_commits(run, seal)
    if len(s_list) != 1 or not HEX40.match(s_list[0]):
        problems.append(("SEAL_ONCE", u"封を足した commit がちょうど 1 つに決まらない(%d 行)" % len(s_list)))
        return problems
    S = s_list[0]
    if not is_anc(run, S, head):
        problems.append(("SEAL<=HEAD", u"封の commit が HEAD の祖先でない"))
    for name, rel in (("DOC", DOC_REL), ("GATE", GATE_REL)):
        lst = added_commits(run, prefix + rel)
        if len(lst) == 0:
            problems.append((name + "_UNCOMMITTED", u"%s がまだ commit されていない(足した commit が無い)" % rel))
        elif len(lst) != 1 or not HEX40.match(lst[0]):
            problems.append((name + "_ONCE", u"%s を足した commit がちょうど 1 つに決まらない(%d 行)" % (rel, len(lst))))
        elif not (lst[0] != S and is_anc(run, S, lst[0])):
            problems.append((name + "_BEFORE_SEAL", u"%s の commit が封の commit より前か同じ" % rel))
    rc, txt = run("log", "--format=%H", "%s..%s" % (S, head), "--", seal)
    for h in [l for l in txt.splitlines() if l.strip()]:
        rc2, parent = run("rev-parse", h + "^")
        base = parent if rc2 == 0 else EMPTY_TREE
        rc3, num = run("diff", "--numstat", base, h, "--", seal)
        for line in num.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1] != "0":
                problems.append(("SEAL_REWRITE", u"封の commit より後の commit %s が封の行を消している" % h[:7]))
    return problems


def codes(problems):
    return sorted(set(c for c, _m in problems))


class Tmp(object):
    def __init__(self, base):
        self.dir = tempfile.mkdtemp(prefix="harness_", dir=base)
        self.run = make_run(self.dir)
        self._g("init", "-q")

    def _g(self, *args):
        r = subprocess.run(["git", "-C", self.dir, "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"] + list(args),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert r.returncode == 0, (args, r.stderr[:300])
        return r.stdout.decode("utf-8").strip()

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        if os.path.dirname(p) and not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, msg, *paths):
        self._g("add", "--", *paths)
        self._g("commit", "-q", "-m", msg)
        return self._g("rev-parse", "HEAD")


FILES = {"SEAL": SEAL_REL, "DOC": DOC_REL, "GATE": GATE_REL}


def build(base, steps):
    u"""steps は 'SEAL' 'DOC' 'GATE'(その file を 1 つの commit で足す)と変異の手 'SEAL_REWRITE' 'SEAL_APPEND' 'SEAL_TWICE' 'BOTH'(文書と門を 1 commit)。"""
    t = Tmp(base)
    for s in steps:
        if s in FILES:
            t.write(FILES[s], u"# %s\n\n行 1\n行 2\n行 3\n" % s)
            t.commit(s, FILES[s])
        elif s == "BOTH":
            for k in ("DOC", "GATE"):
                t.write(FILES[k], u"# %s\n" % k)
            t.commit("BOTH", *[FILES[k] for k in ("DOC", "GATE")])
        elif s == "SEAL_REWRITE":
            t.write(FILES["SEAL"], u"# SEAL\n\n行 1\n行 3\n")
            t.commit("封を書き換える", FILES["SEAL"])
        elif s == "SEAL_APPEND":
            with open(os.path.join(t.dir, FILES["SEAL"]), "a", encoding="utf-8") as f:
                f.write(u"\n## 追記\n行 4\n")
            t.commit("封に追記", FILES["SEAL"])
        elif s == "SEAL_TWICE":
            t._g("rm", "-q", "--", FILES["SEAL"])
            t._g("commit", "-q", "-m", "封を消す")
            t.write(FILES["SEAL"], u"# SEAL\n")
            t.commit("封を足し直す", FILES["SEAL"])
        else:
            raise AssertionError(s)
    return t


# ----------------------------------------------------------------------------------------------------------------
class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if pinned_measure() is None:
            print(u"SKIP: git ls-tree %s が失敗(履歴の無い写し)。列挙の比べを省く" % PIN_TREE)
            raise unittest.SkipTest(u"履歴の無い写し")
        cls.R = Recs()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.J = parse_judgments(cls.doc)
        cls.crit = seal_criterion(cls.seal)


class EnumerationTest(Base):
    def test_a_1_the_criterion_is_read_from_the_seal(self):
        self.assertEqual(len(self.crit["a"]), 7)
        self.assertEqual(self.crit["b"], [u"inject", u"false_pass"])
        self.assertEqual(self.crit["calls"], [u"verify_document(", u"verify_external("])
        self.assertEqual(self.crit["marks"], [u"replace(", u"tampered"])

    def test_a_2_the_document_files_equal_the_enumeration_and_the_seal_table(self):
        self.assertEqual(check_a(self.J, self.seal, self.doc), [])

    def test_a_3_the_population_and_the_fixtures(self):
        enum, n = enumerate_measure(ROOT, self.crit)
        self.assertGreaterEqual(n, len(enum))
        nfix, hit = fixtures_py(ROOT, self.crit)
        self.assertGreater(nfix, 0)
        self.assertEqual(hit, 0)                     # fixtures/**/*.py に規準に当たる file は無い(封 §6-4 の 6)

    def test_a_4_the_outside_files_are_the_ones_the_seal_found(self):
        got = [r[0] for r in outside_criterion(ROOT, self.crit)]
        self.assertEqual(got, [u for u in self.J["outside"] if self.J["outside"][u]["calls"] != u"―"])
        for rel, d in self.J["outside"].items():
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)
            self.assertNotIn(rel, self.J["files"])      # 規準の外の file は 39 の表に入れない


class LaterFilesTest(Base):
    u"""(h) 封の commit より後に足された file の宣言(生きた門)。(a)(b) は 365b468 の木に縛り、後から足した file はここで扱う。"""

    def test_h_1_every_later_file_that_meets_the_criterion_is_declared_and_no_declaration_is_stale(self):
        self.assertEqual(check_later(ROOT, self.crit), [])

    def test_h_2_the_enumeration_is_the_commit_tree_not_the_working_tree(self):
        pinned = pinned_measure()
        ls = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only", PIN_TREE, "--", PREFIX + "measure"], stdout=subprocess.PIPE)
        self.assertEqual(sorted(pinned), sorted(n[len(PREFIX):] for n in ls.stdout.decode("utf-8").splitlines() if n.endswith(".py")))
        self.assertEqual(len(pinned), 179)                                     # 封 §0-4 の『measure/**/*.py の 179 file』
        self.assertEqual(list(enumerate_measure(ROOT, self.crit)[0]), enumerate_measure(ROOT, self.crit, None, pinned)[0])
        self.assertEqual(enumerate_measure(ROOT, self.crit)[1], 179)

    def test_h_3_the_declared_files_are_in_the_working_tree_and_not_in_the_commit_tree(self):
        pinned = pinned_measure()
        for d in LATER_HARNESS_FILES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, d[0])), d[0])
            self.assertNotIn(d[0], pinned, d[0])                               # この便の宣言は新しい file だけ(変わった file はまだ無い)


class RecordsAndJudgmentTest(Base):
    def test_b_1_the_judgment_tables_are_in_the_vocabulary_and_the_functions_and_quotes_exist(self):
        self.assertEqual(check_b(self.R, self.J), [])

    def test_b_2_the_document_tables_equal_the_ones_rebuilt_from_the_records(self):
        self.assertEqual(check_c(self.R, self.J, self.seal, self.doc), [])

    def test_b_3_the_records_counted_are_the_ones_in_the_seal(self):
        ks = reach_specs()
        self.assertEqual(len(set(k[0] for k in ks)), len(ks))
        for k in ks:
            n, res = run_spec(self.R, k)
            self.assertTrue(res)
        rit = ritual_rows(self.R)
        self.assertEqual(len(rit), 4)
        for r in rit:
            self.assertEqual(r[3], r[4])               # 記録の数と、行の欄で数え直した数
            self.assertEqual(r[4], r[5])               # 参照先(注入前)と(注入後)の違いで数え直した数

    def test_b_4_the_fresh_and_reach_records_are_the_earlier_gates_numbers(self):
        fr = self.R.get("fixtures/xbrl/fresh/fresh_2026-10-21.json")
        ir = self.R.get(INJECT_REACH_REL)
        self.assertEqual(len(fr[u"注入の行"]), 741)
        self.assertEqual(len(ir[u"rows"]), 741)
        n5 = sum(1 for r in fr[u"注入の行"] if all((r[u"結果"][p] or [None])[0] == "GROUNDED" for p in ("P22", "P23", "P24", "P25", "P26")))
        self.assertEqual(n5, 5)
        self.assertEqual(sum(1 for r in ir[u"rows"] if r["profile"]["P22"][u"分類"] == u"(届かない・通した)"), 5)

    def test_b_5_every_same_type_mechanism_has_its_records_and_users(self):
        for mid, m in self.J["mech"].items():
            if cut(m["hole"]) == u"同じ型":
                r = self.J["ref"][mid]
                self.assertTrue(r["recs"], mid)


class LedgerTest(Base):
    def test_c_1_the_ledger_rows_are_the_ones_the_rule_picks(self):
        self.assertEqual(check_ledger(self.J), [])

    def test_c_2_a_mechanism_with_no_ledger_row_is_not_my_own_miss(self):
        u"""0 件は先に自分の欠陥を疑う: 行が 0 の同じ型の仕掛けは、記録の basename・script の stem・結果文書の名のどれも台帳の本文のどこにも無い(path の書き方の違いで落としていない)。"""
        lines = ledger_lines(ROOT)
        whole = jtext(os.path.join(ROOT, LEDGER_REL))
        pick = ledger_pick(lines, self.J)
        same = [mid for mid, m in self.J["mech"].items() if cut(m["hole"]) == u"同じ型"]
        for mid in same:
            if any(mid in v for v in pick.values()):
                continue
            r = self.J["ref"][mid]
            names = [os.path.basename(x) for x in r["recs"]] + [os.path.splitext(os.path.basename(x))[0] for x in [self.J["mech"][mid]["file"]] + r["users"]] + list(r["docs"])
            for n in names:
                self.assertNotIn(n, whole, (mid, n))
        self.assertTrue(set(v for vals in pick.values() for v in vals) <= set(same))


class PredictionAndDocTest(Base):
    def test_d_1_judgments_are_recomputed_and_cover_the_sixteen_predictions(self):
        jd = judge(self.R, self.J, self.seal, enumerate_measure(ROOT, self.crit)[0], self.crit)
        self.assertEqual(list(jd), ["H-%d" % i for i in range(1, 17)])
        for k, v in jd.items():
            self.assertIn(v[1], (True, False), k)

    def test_d_2_the_seal_prediction_table_is_what_this_gate_reads(self):
        SP = seal_predictions(self.seal)
        self.assertEqual(list(SP), ["H-%d" % i for i in range(1, 17)])
        self.assertEqual([len(ranges_of(SP["H-%d" % i][1])) for i in range(1, 17)], [1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0])
        self.assertEqual(len(pcts_of(SP["H-11"][1])), 1)

    def test_d_3_the_prediction_table_copies_the_seal_and_the_judgments(self):
        jd = judge(self.R, self.J, self.seal, enumerate_measure(ROOT, self.crit)[0], self.crit)
        SP = seal_predictions(self.seal)
        got = doc_blocks(self.doc)["pred"]
        self.assertEqual(len(got), 2 + len(jd))
        for line, k in zip(got[2:], jd):
            cells = cells_of(line)
            self.assertEqual(cells[0], u"**%s**" % k)
            self.assertEqual(tuple(cells[1:4]), SP[k], k)
            self.assertEqual(cells[4], jd[k][0], k)
            self.assertEqual(cells[5], hit_word(jd[k][1]), k)

    def test_d_4_the_prose_outside_the_tables_is_in_order(self):
        self.assertEqual(check_doc_prose(self.R, self.J, self.seal, self.doc), [])

    def test_d_5_the_misses_are_kept_as_misses(self):
        jd = judge(self.R, self.J, self.seal, enumerate_measure(ROOT, self.crit)[0], self.crit)
        # 外れは外れのまま残す。封も予測も直さない。記録と文書の表から求めた当否の並びを留める(測った事実)。
        self.assertEqual([k for k, v in jd.items() if v[1] is False], MISSES)

    def test_e_1_no_docid_and_no_claim_id_in_the_seal_and_the_document(self):
        docs, cids = secret_strings(self.R)
        self.assertGreaterEqual(len(docs), 30)               # 評価用・調整用の docID は新しい標本 30 の中にある(記録から読む)
        self.assertGreater(len(cids), 100)
        self.assertEqual(check_e(self.seal, self.doc, docs, cids), [])

    def test_e_2_the_document_states_the_judgments_it_does_not_make(self):
        for lit in (u"対応付けの欠陥だった", u"engine が通した"):
            self.assertIn(lit, self.doc)               # 言い切らない旨を引用の形で書く(下の行)
        self.assertIn(u"言い切らない", self.doc)


#: 記録と文書の表から求めた当否のうち外れの名前(測った事実。外れは外れのまま残す。封も予測も直さない)。食い違えば d_5 が赤。
MISSES = ["H-1", "H-2", "H-3", "H-4", "H-5", "H-7", "H-8", "H-12", "H-13", "H-15"]


class FalseRecordsAreRedTest(Base):
    u"""(g) 偽物で赤: 文書の表の 1 字・記録の写しの 1 欄・封の予測の 1 字・規準に当たる偽の file 1 つ。"""

    def test_g_0_baseline_is_green(self):
        self.assertEqual(check_a(self.J, self.seal, self.doc), [])
        self.assertEqual(check_b(self.R, self.J), [])
        self.assertEqual(check_c(self.R, self.J, self.seal, self.doc), [])
        self.assertEqual(check_ledger(self.J), [])

    def test_g_1_one_character_of_a_document_table_turns_c_red(self):
        for name, find, rep in (("mech", u"同じ型", u"同じ形"), ("files", u"仕掛け持ち", u"仕掛け待ち"), ("reach", u"id_shift", u"id_shifts"), ("ledger", u"通った", u"通つた")):
            blk = BLOCK_RE.search(self.doc[self.doc.index(u"<!-- 門:start %s -->" % name):])
            body = blk.group(2)
            self.assertIn(find, body, name)
            doc = self.doc.replace(body, body.replace(find, rep, 1), 1)
            self.assertNotEqual(doc, self.doc)
            J2 = parse_judgments(doc)
            red = check_c(self.R, J2, self.seal, doc) + check_b(self.R, J2) + check_ledger(J2) + check_a(J2, self.seal, doc)
            self.assertNotEqual(red, [], name)

    def test_g_2_one_field_of_a_record_copy_turns_the_counts_red(self):
        # period_bind の E1 の 1 行の state を変えると、記録から作り直した表が文書と合わない
        rec = copy.deepcopy(self.R.get("fixtures/xbrl/period_bind_2026-10-20.json"))
        row = [r for r in rec["E1"]["行"] if r["P22"].get("state") == "id_shift"][0]
        row["P22"]["state"] = "GROUNDED"
        R2 = Recs(over={"fixtures/xbrl/period_bind_2026-10-20.json": rec})
        self.assertNotEqual(check_c(R2, self.J, self.seal, self.doc), [])
        # eval の記録の 1 欄(基準に対応が付かない)を変えると p27rec の表が合わない
        rec = copy.deepcopy(self.R.get(P27[0]))
        d0 = sorted(rec[u"書類別の数え"])[0]
        rec[u"書類別の数え"][d0][u"T1_VALUE"][u"基準に対応が付かない"] += 1
        R3 = Recs(over={P27[0]: rec})
        self.assertNotEqual(check_c(R3, self.J, self.seal, self.doc), [])
        # 儀式の記録の 1 行の『参照先が動いた』
        rel = RITUAL[0]
        rec = copy.deepcopy(self.R.get(rel))
        x = [x for x in rec[u"注入の一覧"] if x[u"結果"] == "PASSED"][0]
        x[u"参照先が動いた"] = True
        R4 = Recs(over={rel: rec})
        self.assertNotEqual(check_c(R4, self.J, self.seal, self.doc), [])

    def test_g_3_a_record_field_changes_the_judgment_of_h8_and_h9(self):
        rel = RITUAL[0]
        rec = copy.deepcopy(self.R.get(rel))
        key = [k for k in rec if u"のうち参照先が動いた" in k][0]
        rec[key] = 1
        R2 = Recs(over={rel: rec})
        enum = enumerate_measure(ROOT, self.crit)[0]
        self.assertTrue(judge(self.R, self.J, self.seal, enum, self.crit)["H-8"][0] != judge(R2, self.J, self.seal, enum, self.crit)["H-8"][0])
        rec = copy.deepcopy(self.R.get(P27[0]))
        rec[u"行"][0][u"文の番号"] = 3
        R3 = Recs(over={P27[0]: rec})
        self.assertIs(judge(R3, self.J, self.seal, enum, self.crit)["H-9"][1], False)

    def test_g_4_one_character_of_a_seal_prediction_turns_d_and_c_red(self):
        seal = u"\n".join(l.replace(u"**8 以上 13 以下**", u"**8 以上 30 以下**", 1) if l.startswith(u"| **H-1**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(seal_predictions(seal)["H-1"], seal_predictions(self.seal)["H-1"])
        self.assertNotEqual(check_c(self.R, self.J, seal, self.doc), [])            # 文書の予測の表が封の字と合わなくなる
        seal = u"\n".join(l.replace(u"**12 以上 22 以下**", u"**12 以上 42 以下**", 1) if l.startswith(u"| **H-13**") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(check_c(self.R, self.J, seal, self.doc), [])
        # 規準の字を 1 つ変えると列挙が変わり (a) が赤
        seal = self.seal.replace(u"`inject_doc(`", u"`inject_docx(`", 1)
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(check_a(self.J, seal, self.doc), [])

    def test_g_5_a_fake_file_that_meets_the_criterion_turns_a_red(self):
        fake = {"measure/zz_fake_%s.py" % "probe": u"import x\nx.apply_edits(1)\n"}
        self.assertNotEqual(check_a(self.J, self.seal, self.doc, extra=fake), [])
        fake = {"measure/zz_inject_only_name.py": u"pass\n"}
        self.assertNotEqual(check_a(self.J, self.seal, self.doc, extra=fake), [])
        self.assertNotEqual(check_c(self.R, self.J, self.seal, self.doc, extra=fake), [])

    def test_g_5b_a_later_file_without_a_declaration_or_a_stale_declaration_turns_h_red(self):
        self.assertEqual(check_later(ROOT, self.crit), [])
        # 規準(本文の字)に当たる偽の file・規準(file 名)に当たる偽の file・副産物の検査(呼び出し + 差し替えの字)に当たる偽の file を、宣言なしで足す
        for name, text in (("measure/zz_later_probe.py", u"import x\nx.apply_edits(1)\n"),
                           ("measure/zz_later_inject_name.py", u"pass\n"),
                           ("measure/zz_later_stop_like.py", u"verify_document(1)\ntext.replace(1, 2)\n")):
            self.assertNotEqual(check_later(ROOT, self.crit, extra={name: text}), [], name)
            # 宣言すれば緑(宣言の欄が合っていれば)
            decl = LATER_HARNESS_FILES + ((name, u"仕掛け持ち", u"無", "f", u"x = 1", "2026-10-30"),)
            ok = {name: u"def f():\n    x = 1\n" + text}
            self.assertEqual(check_later(ROOT, self.crit, decl=decl, extra=ok), [], name)
        # 規準にも副産物の検査にも当たらない偽の file は宣言不要(足しても緑)
        self.assertEqual(check_later(ROOT, self.crit, extra={"measure/zz_plain.py": u"pass\n"}), [])
        # 古い宣言: 存在しない path・当たらない file(封の commit の木に在る file で変わっていない)・宣言の重複
        for bad in ((("measure/zz_not_there.py", u"仕掛け持ち", u"有", "f", u"x", "2026-10-30"),),
                    (("measure/xbrl_fresh_2026-10-21.py", u"仕掛け持ち", u"有", "inject_doc", u"x", "2026-10-30"),),
                    (LATER_HARNESS_FILES[0], LATER_HARNESS_FILES[0])):
            self.assertNotEqual(check_later(ROOT, self.crit, decl=LATER_HARNESS_FILES + bad), [], bad)
        # 宣言を消す
        self.assertNotEqual(check_later(ROOT, self.crit, decl=()), [])

    def test_g_5c_a_declaration_with_a_wrong_word_or_evidence_turns_h_red(self):
        rel, role, chk, fn, quote, day = LATER_HARNESS_FILES[0]
        for d in ((rel, u"たぶん仕掛け", chk, fn, quote, day), (rel, role, u"たぶん有", fn, quote, day), (rel, role, chk, "no_such_function", quote, day),
                  (rel, role, chk, fn, quote + u" # この字は file に無い", day), (rel, role, chk, fn, u"", day), (rel, role, chk, fn, quote, "2026-10-28"),
                  (rel, role, chk, fn, quote, "10/29"), (rel, role, chk, fn, quote)):
            self.assertNotEqual(check_later(ROOT, self.crit, decl=(d,)), [], d)
        # 根拠の字は『その関数の中』: file の別の関数の字では足りない
        self.assertNotEqual(check_later(ROOT, self.crit, decl=((rel, role, chk, "branch", quote, day),)), [])

    def test_g_5d_the_commit_tree_binding_keeps_a_and_b_green_when_a_file_is_added_and_red_when_the_document_table_changes(self):
        # いまの木に規準に当たる file を足しても (a) は変わらない(縛っている)が、列挙には効く(extra で足すと赤 = test_g_5)
        live, later = later_hits(ROOT, self.crit)
        self.assertIn(LATER_HARNESS_FILES[0][0], later)
        self.assertNotIn(LATER_HARNESS_FILES[0][0], [r[0] for r in enumerate_measure(ROOT, self.crit)[0]])
        self.assertEqual(check_a(self.J, self.seal, self.doc), [])
        # 文書の表の 1 字を変えると、縛った列挙でも (a) が赤(元の門の効きが残る)
        doc = self.doc.replace(u"| 仕掛け持ち |", u"| 仕掛け待ち |", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_a(parse_judgments(doc), self.seal, doc), [])

    def test_g_6_a_wrong_function_name_or_quote_turns_b_red(self):
        blk = BLOCK_RE.search(self.doc[self.doc.index(u"<!-- 門:start mech -->"):]).group(2)
        doc = self.doc.replace(blk, blk.replace(u"`run_doc`", u"`run_dox`", 1), 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_b(self.R, parse_judgments(doc)), [])
        J2 = copy.deepcopy(self.J)
        J2["evidence"]["M-01"]["quote"] += u"x"
        self.assertNotEqual(check_b(self.R, J2), [])
        J3 = copy.deepcopy(self.J)
        J3["evidence"]["M-01"]["func"] = u"main"
        self.assertNotEqual(check_b(self.R, J3), [])
        J4 = copy.deepcopy(self.J)
        J4["mech"]["M-03"]["check"] = u"有"
        self.assertNotEqual(check_b(self.R, J4), [])            # 確かめ 有 なのに同じ型

    def test_g_7_the_ledger_reading_is_checked(self):
        J2 = copy.deepcopy(self.J)
        first = next(iter(J2["ledger"]))
        J2["ledger"][first]["read"] = u"たぶん通った"
        self.assertNotEqual(check_ledger(J2), [])
        J3 = copy.deepcopy(self.J)
        del J3["ledger"][first]
        self.assertNotEqual(check_ledger(J3), [])
        J4 = copy.deepcopy(self.J)
        J4["ledger"][first]["quote"] = u"この字は台帳の行に無い"
        self.assertNotEqual(check_ledger(J4), [])
        J5 = copy.deepcopy(self.J)
        J5["ledger"]["L-999"] = dict(J5["ledger"][first])
        self.assertNotEqual(check_ledger(J5), [])

    def test_g_7b_the_verdict_table_is_checked(self):
        J2 = copy.deepcopy(self.J)
        J2["verdict"]["M-03"]["text"] = u"診断済み ― 前の便の診断" + u"x" * 10
        self.assertNotEqual(check_b(self.R, J2), [])            # 診断済みは新しい標本の注入だけ
        J3 = copy.deepcopy(self.J)
        J3["verdict"]["M-03"]["text"] = u"たぶん対応付けの数 ― 言い切る"
        self.assertNotEqual(check_b(self.R, J3), [])
        J4 = copy.deepcopy(self.J)
        del J4["verdict"]["M-05"]
        self.assertNotEqual(check_b(self.R, J4), [])
        J5 = copy.deepcopy(self.J)
        J5["verdict"]["M-14"]["text"] = u"対応付けの数でありうる ― 分けられないはず" + u"x" * 10
        self.assertNotEqual(check_b(self.R, J5), [])            # 注入後の claim の id が無い系統は『分けられない』
        self.assertEqual(sorted(cut(d["text"]) for d in self.J["verdict"].values()).count(u"診断済み"), 1)

    def test_g_8_a_docid_a_claim_id_a_forbidden_word_or_a_fence_turns_e_red(self):
        docs, cids = secret_strings(self.R)
        d0 = sorted(docs)[0]
        self.assertNotEqual(check_e(self.seal, self.doc + u"\n" + d0 + u"\n", docs, cids), [])
        self.assertNotEqual(check_e(self.seal, self.doc + u"\nN012\n", docs, cids), [])
        self.assertNotEqual(check_e(self.seal, self.doc + u"\n%s\n" % sorted(cids)[0], docs, cids), [])
        self.assertNotEqual(check_e(self.seal, self.doc + u"\n" + FORBIDDEN[0] + u"\n", docs, cids), [])
        self.assertNotEqual(check_e(self.seal, self.doc + u"\n```\nx\n```\n", docs, cids), [])
        # 評価用・調整用の docID は記録から読んでいる(文書と封に出れば赤)
        ev = set(x[u"docID"] for x in self.R.get(P27[0])[u"行"])
        self.assertTrue(ev <= docs)

    def test_g_9_an_unmarked_number_in_prose_turns_the_prose_check_red(self):
        doc = self.doc + u"\n通した行は 7 行だった。\n"
        self.assertNotEqual(check_doc_prose(self.R, self.J, self.seal, doc), [])

    def test_g_10_changing_the_miss_line_turns_the_prose_check_red(self):
        doc = self.doc.replace(u"外れた予測: ", u"外れた予測: H-99・", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(check_doc_prose(self.R, self.J, self.seal, doc), [])


class OrderTest(unittest.TestCase):
    u"""(f) 封の commit が文書・門の commit より前。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="harness_root_")
        cls.grun = staticmethod(make_run(REPO))

    def _p(self, steps):
        t = build(self.base, steps)
        return order_problems(t.run, "")

    def test_f_1_the_real_history_has_the_seal_before_the_two_files(self):
        u"""文書・門のどちらかが未 commit なら赤(足した commit が無い)。2 つとも commit された後で初めて緑。"""
        p = order_problems(self.grun, PREFIX)
        self.assertEqual(p, [])

    def test_f_2_the_real_seal_is_one_commit_and_an_ancestor_of_head(self):
        lst = added_commits(self.grun, PREFIX + SEAL_REL)
        self.assertEqual(len(lst), 1)
        self.assertTrue(lst[0].startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(is_anc(self.grun, lst[0], "HEAD"))

    def test_f_3_a_correct_order_is_green(self):
        self.assertEqual(self._p(["SEAL", "DOC", "GATE"]), [])
        self.assertEqual(self._p(["SEAL", "BOTH"]), [])
        self.assertEqual(self._p(["SEAL", "BOTH", "SEAL_APPEND"]), [])               # 日付つきの追記(削除 0)は許される

    def test_f_4_a_file_before_the_seal_is_red(self):
        for first in ("DOC", "GATE"):
            steps = [first, "SEAL"] + [k for k in ("DOC", "GATE") if k != first]
            self.assertIn(first + "_BEFORE_SEAL", codes(self._p(steps)), first)

    def test_f_5_an_uncommitted_file_is_red_not_skipped(self):
        self.assertIn("GATE_UNCOMMITTED", codes(self._p(["SEAL", "DOC"])))
        self.assertIn("DOC_UNCOMMITTED", codes(self._p(["SEAL"])))

    def test_f_6_the_seal_missing_or_added_twice_is_red(self):
        self.assertIn("SEAL_ONCE", codes(self._p(["BOTH"])))
        self.assertIn("SEAL_ONCE", codes(self._p(["SEAL", "BOTH", "SEAL_TWICE"])))

    def test_f_7_rewriting_the_seal_after_the_fact_is_red(self):
        self.assertIn("SEAL_REWRITE", codes(self._p(["SEAL", "BOTH", "SEAL_REWRITE"])))

    def test_f_8_the_same_commit_as_the_seal_is_red(self):
        t = Tmp(self.base)
        for k in ("SEAL", "DOC", "GATE"):
            t.write(FILES[k], u"# %s\n" % k)
        t.commit("all", *FILES.values())
        self.assertIn("DOC_BEFORE_SEAL", codes(order_problems(t.run, "")))


if __name__ == "__main__":
    unittest.main()
