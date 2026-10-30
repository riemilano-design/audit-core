# -*- coding: utf-8 -*-
"""封 docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md §5-7・§7・§10-4 後半 ― P27 段 1 の調整用の診断(docs/XBRL_P27_TUNE_DIAG_2026-10-27.md)の門。

**この門が縛るもの**

1. 診断の文書の数。文書の `<!-- 門:start 名前 -->` 〜 `<!-- 門:end -->` の間の表は、3 つの記録(判定・注入・読み)から**ここで作り直した表と 1 行も違わない**。
   数は字で留めず、記録から計算する。記録の自前の集計(script が書いた欄)とも照らす(実装を 2 つ持つ)。
2. 記録 5 本の sha256(文書の表と実物)。
3. 封 §7 の R-5〜R-12 の当否の字。予測の幅は封の字から読み、実測は記録から計算して、文書の当否の字が違えば赤。
4. P27 の記録 5 本(dbfetch・reports・tune・tune_inject・tune_readings)の**中身**:
   (a) 欄の名前の木が許可の一覧と一致(一覧は下の ALLOWED に字で持ち、欄ごとに何かを書く)
   (b) span・subject・value・recomputed・理由の文・道5の形・本文・抜粋にあたる欄が無い
   (c) 前例の ``key_leaks`` と tune の ``record_key_leaks`` が空
   (d) W の記録の文の sha256 が W の commit の blob と今の file で同じ
   (e) 偽の会社名・偽の抜粋の 1 文を足した写しで、(a)(b)(c) の検査が赤になる

**この門が縛らないもの(文書にも「門なし」と書く)**: 下見の記録(repo の外)・T8 で通った行の書かれた単位(repo の外 inject_full.json にしか無い)・
文書の散文の読み(当否の解釈・限界の文)。散文には数を書かない(書くなら【門なし】の印をつける)ことだけを字面で見る。

文の字・DB の値・理由の字・docID の接頭辞は、この file に書かない(引きの門 test_xbrl_fresh_seal が追跡 file の docID を数える。
この file は LATER_NAMING_FILES に宣言済みだが、字は持たない)。評価用の文は開かない(読むのは W の記録の sha256 の欄だけ)。
"""
import collections
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import statistics
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

SEAL_REL = "docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md"
DOC_REL = "docs/XBRL_P27_TUNE_DIAG_2026-10-27.md"
RECORD_REL = collections.OrderedDict([
    ("dbfetch", "fixtures/xbrl/p27/dbfetch_2026-10-27.json"),
    ("reports", "fixtures/xbrl/p27/reports_2026-10-27.json"),
    ("tune", "fixtures/xbrl/p27/tune_2026-10-27.json"),
    ("tune_inject", "fixtures/xbrl/p27/tune_inject_2026-10-27.json"),
    ("tune_readings", "fixtures/xbrl/p27/tune_readings_2026-10-27.json"),
])
W_COMMIT = "c48f464"                                  # 封 §4-1 の commit W(評価用の凍結)
SCRIPT_REL = "measure/xbrl_p27_tune_2026-10-27.py"
DBFETCH_SCRIPT_REL = "measure/xbrl_p27_dbfetch_2026-10-27.py"

PROFILES = ("P22", "P26")
STYLES = ("A", "B", "C")
TYPES = ("T1_VALUE", "T8_REL")
LABEL_PASS = u"通した"
LABEL_NAMED_ORIGINAL = u"名指して原本の値を返した"
LABEL_NAMED_OTHER = u"名指したが別の値"
LABEL_PNF = u"止めたが名指さない(POINTER_NOT_FOUND)"
LABEL_UNV = u"止めたが名指さない(UNVERIFIABLE)"
LABELS = (LABEL_PASS, LABEL_NAMED_ORIGINAL, LABEL_NAMED_OTHER, LABEL_PNF, LABEL_UNV)
UNSURE = u"分からない"
NO_SAME_VALUE = "no_same_value"


def _load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_text(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def read_bytes(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as f:
        return f.read()


def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def load_records():
    return collections.OrderedDict((k, json.loads(read_text(rel))) for k, rel in RECORD_REL.items())


# ======================================================================================================
# 計算(3 つの記録から作り直す。記録の自前の集計は見ずに、行と claim から数える)
def pc_num(a, b):
    return 100.0 * a / b if b else None


def pc(a, b):
    return u"—" if not b else u"%.1f%%" % (100.0 * a / b)


def ab(a, b):
    return u"%d/%d(%s)" % (a, b, pc(a, b))


def med(xs):
    m = statistics.median(xs)
    return int(m) if float(m).is_integer() else m


class Calc(object):
    """記録 3 つ(tune・tune_inject・tune_readings)からの数え直し。"""

    def __init__(self, recs):
        self.recs = recs
        t, i, r = recs["tune"], recs["tune_inject"], recs["tune_readings"]
        self.docs = [c["docID"] for c in t["会社"]]
        self.style = dict((c["docID"], c["型"]) for c in t["会社"])
        self.claims = t["claim"]
        self.by_key = dict(((c["docID"], c["id"]), c) for c in self.claims)
        self.read_keys = set((x["docID"], x["id"]) for x in t["読む行"])
        self.readings = r["行"]
        self.inj = i["行"]

    # ---- 判定
    def state_counts(self, p):
        c = collections.Counter(x[p]["state"] for x in self.claims)
        return dict((s, c.get(s, 0)) for s in ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"))

    def claims_of_doc(self, doc):
        return [c for c in self.claims if c["docID"] == doc]

    def style_median_p26(self, style):
        return med([len(self.claims_of_doc(d)) for d in self.docs if self.style[d] == style])

    def read_rows_by_rule(self):
        out = set()
        for c in self.claims:
            a, b = c["P22"], c["P26"]
            if b["state"] == "VALUE_MISMATCH" or a["state"] == "VALUE_MISMATCH" or (b["state"] == "POINTER_NOT_FOUND" and b["reason"] == NO_SAME_VALUE):
                out.add((c["docID"], c["id"]))
        return out

    # ---- 読み
    @staticmethod
    def combine(a, b):
        (sa, da), (sb, db) = a, b
        if sa != sb or sa == UNSURE:
            return UNSURE, None
        return sa, (da if da == db else UNSURE)

    def merged(self, row):
        return self.combine((row["席1"]["側"], row["席1"]["細目"]), (row["席2"]["側"], row["席2"]["細目"]))

    def p26_group(self, row):
        c = self.by_key[(row["docID"], row["id"])]["P26"]
        return c["state"] if not c["reason"] else u"%s / %s" % (c["state"], c["reason"])

    def reading_counts(self, rows=None):
        rows = self.readings if rows is None else rows
        c = collections.Counter()
        for r in rows:
            side, det = self.merged(r)
            c[(side, det)] += 1
        return c

    # ---- 注入
    def inj_rows(self, typ, style=None):
        return [x for x in self.inj if x["型"] == typ and (style is None or x["文体"] == style)]

    def mapped(self, typ, p, style=None):
        return [x for x in self.inj_rows(typ, style) if x[p]["対応"]]

    def label_count(self, typ, p, label, style=None):
        return sum(1 for x in self.mapped(typ, p, style) if x[p]["結果"] == label)

    def both_mapped(self, typ):
        return [x for x in self.inj_rows(typ) if all(x[p]["対応"] for p in PROFILES)]


# ======================================================================================================
# 封 §7 の R-5〜R-12(予測の幅は封の字から読む。実測は記録から計算する)
#: (小項目, 見るもの, 封の行の中の字, 実測の関数名)。字は封の R の行にそのまま在り、順序も封の字の並びのとおり
PREDICTIONS = [
    ("R-5a", u"A の文あたり claim の数(P26)の中央値", "R-5", "**40〜100**", "r5a"),
    ("R-5b", u"B の文あたり claim の数(P26)の中央値", "R-5", "**30〜80**", "r5b"),
    ("R-5c", u"C の文あたり claim の数(P26)の中央値", "R-5", "**12〜45**", "r5c"),
    ("R-5d", u"調整用の全体の claim の数", "R-5", "**350〜800**", "r5d"),
    ("R-6a", u"P26 の VALUE_MISMATCH の率", "R-6", "**4〜14%**", "r6a"),
    ("R-6b", u"P22 の VALUE_MISMATCH の率", "R-6", "**10〜25%**", "r6b"),
    ("R-7a", u"P26 の VALUE_MISMATCH の行で合わせた側が `道具` の割合", "R-7", "**55〜90%**", "r7a"),
    ("R-7b", u"同じ行で合わせた側が `分からない` の割合", "R-7", "**≤ 20%**", "r7b"),
    ("R-8a", u"合わせた細目が付いた `道具` の行のうち `道1`〜`道4` の割合", "R-8", "**65% 以上**", "r8a"),
    ("R-8b", u"同じ行のうち `道5` の割合", "R-8", "35% 以下", "r8b"),
    ("R-9", u"読む行の全体で 2 席の側が一致する行の割合", "R-9", "**≥ 80%**", "r9"),
    ("R-10", u"読む行のうち合わせた札が `文2` の行の数", "R-10", "**0〜6**", "r10"),
    ("R-11a", u"T8_REL: 名指して原本の値を返した率 P22", "R-11", "**≥ 75%**", "r11a"),
    ("R-11b", u"T8_REL: 名指して原本の値を返した率 P26", "R-11", "**≤ 35%**", "r11b"),
    ("R-11c", u"T1_VALUE: 名指して原本の値を返した率 P26", "R-11", "**≥ 60%**", "r11c"),
    ("R-11d", u"通した(GROUNDED)の率 T1_VALUE・P22", "R-11", "**≤ 2%**", "r11d"),
    ("R-11e", u"通した(GROUNDED)の率 T1_VALUE・P26", "R-11", "**≤ 2%**", "r11e"),
    ("R-11f", u"通した(GROUNDED)の率 T8_REL・P22", "R-11", "**≤ 2%**", "r11f"),
    ("R-11g", u"通した(GROUNDED)の率 T8_REL・P26", "R-11", "**≤ 2%**", "r11g"),
    ("R-12", u"T8_REL の対応が付く注入の数(両 profile で対応が付く)", "R-12", "**≥ 60**", "r12"),
]
R_IDS = ("R-5", "R-6", "R-7", "R-8", "R-9", "R-10", "R-11", "R-12")


def parse_fragment(fragment):
    """封の字の幅 -> ("range", lo, hi) / ("ge", n, None) / ("le", None, n)。"""
    m = re.search(r"(\d+)〜(\d+)", fragment)
    if m:
        return ("range", float(m.group(1)), float(m.group(2)))
    m = re.search(r"≥ (\d+)", fragment) or re.search(r"(\d+)% 以上", fragment)
    if m:
        return ("ge", float(m.group(1)), None)
    m = re.search(r"≤ (\d+)", fragment) or re.search(r"(\d+)% 以下", fragment)
    if m:
        return ("le", None, float(m.group(1)))
    raise AssertionError("封の字の幅を読めない: %r" % fragment)


def in_band(parsed, x):
    kind, lo, hi = parsed
    if x is None:
        return False
    if kind == "range":
        return lo <= x <= hi
    if kind == "ge":
        return x >= lo
    return x <= hi


def measure(calc, key):
    """小項目の実測(数。率は % の実数)。"""
    c = calc
    rc = c.reading_counts()
    p26vm = [r for r in c.readings if c.by_key[(r["docID"], r["id"])]["P26"]["state"] == "VALUE_MISMATCH"]
    side26 = collections.Counter(c.merged(r)[0] for r in p26vm)
    tool = [(s, d) for (s, d), n in rc.items() if s == u"道具" and d != UNSURE for _ in range(n)]
    n_b = sum(1 for s, d in tool if d in (u"道1", u"道2", u"道3", u"道4"))
    n5 = sum(1 for s, d in tool if d == u"道5")

    def named(typ, p):
        return pc_num(c.label_count(typ, p, LABEL_NAMED_ORIGINAL), len(c.mapped(typ, p)))

    def passed(typ, p):
        return pc_num(c.label_count(typ, p, LABEL_PASS), len(c.mapped(typ, p)))
    table = {
        "r5a": lambda: c.style_median_p26("A"), "r5b": lambda: c.style_median_p26("B"), "r5c": lambda: c.style_median_p26("C"),
        "r5d": lambda: len(c.claims),
        "r6a": lambda: pc_num(c.state_counts("P26")["VALUE_MISMATCH"], len(c.claims)),
        "r6b": lambda: pc_num(c.state_counts("P22")["VALUE_MISMATCH"], len(c.claims)),
        "r7a": lambda: pc_num(side26.get(u"道具", 0), len(p26vm)), "r7b": lambda: pc_num(side26.get(UNSURE, 0), len(p26vm)),
        "r8a": lambda: pc_num(n_b, len(tool)), "r8b": lambda: pc_num(n5, len(tool)),
        "r9": lambda: pc_num(sum(1 for r in c.readings if r["席1"]["側"] == r["席2"]["側"]), len(c.readings)),
        "r10": lambda: sum(n for (s, d), n in rc.items() if s == u"文" and d == u"文2"),
        "r11a": lambda: named("T8_REL", "P22"), "r11b": lambda: named("T8_REL", "P26"), "r11c": lambda: named("T1_VALUE", "P26"),
        "r11d": lambda: passed("T1_VALUE", "P22"), "r11e": lambda: passed("T1_VALUE", "P26"),
        "r11f": lambda: passed("T8_REL", "P22"), "r11g": lambda: passed("T8_REL", "P26"),
        "r12": lambda: len(c.both_mapped("T8_REL")),
    }
    return table[key]()


def seal_rows(seal_text):
    rows = {}
    for rid in R_IDS:
        m = re.search(r"^\| \*\*%s\*\* \|(.*)$" % rid, seal_text, re.M)
        rows[rid] = m.group(1) if m else None
    return rows


RATE_KEYS = ("r6a", "r6b", "r7a", "r7b", "r8a", "r8b", "r9", "r11a", "r11b", "r11c", "r11d", "r11e", "r11f", "r11g")


def show_pred(parsed, pct=False):
    kind, lo, hi = parsed
    u = u"%" if pct else u""

    def f(x):
        return (u"%d" % x) if float(x).is_integer() else (u"%g" % x)
    if kind == "range":
        return u"%s〜%s%s" % (f(lo), f(hi), u)
    if kind == "ge":
        return u"≥ %s%s" % (f(lo), u)
    return u"≤ %s%s" % (f(hi), u)


def show_val(key, x):
    if x is None:
        return u"—"
    if key in ("r5a", "r5b", "r5c"):
        return u"%g" % x
    if key in ("r5d", "r10", "r12"):
        return u"%d" % x
    return u"%.1f%%" % x


def r_rows(calc, seal_text):
    """(小項目の行の列, R ごとの行の列)。予測の幅は封の R の行の字から読む(順序も封の字の並びと照らす)。"""
    srows = seal_rows(seal_text)
    sub, verdict = [], collections.OrderedDict((rid, []) for rid in R_IDS)
    last_pos = {}
    for sid, what, rid, frag, key in PREDICTIONS:
        row = srows[rid]
        assert row is not None, rid
        pos = row.index(frag)
        assert pos >= last_pos.get(rid, -1), (sid, "封の字の並びと違う")
        last_pos[rid] = pos
        parsed = parse_fragment(frag)
        x = measure(calc, key)
        ok = in_band(parsed, x)
        verdict[rid].append((sid, ok))
        sub.append(u"| %s | %s | %s | %s | %s |" % (sid, what, show_pred(parsed, key in RATE_KEYS), show_val(key, x), u"当たり" if ok else u"外れ"))
    summary = []
    for rid in R_IDS:
        ok = all(o for _s, o in verdict[rid])
        miss = u"・".join(s for s, o in verdict[rid] if not o) or u"—"
        summary.append(u"| %s | %s | %s |" % (rid, u"当たり" if ok else u"外れ", miss))
    return sub, summary


# ======================================================================================================
# 文書の表(門の中身。文書はこの表と 1 行も違わない)
def rec_sha_rows(recs_bytes):
    return [u"| 記録 | sha256 |", u"|---|---|"] + [u"| %s | %s |" % (rel, sha256_hex(recs_bytes[k])) for k, rel in RECORD_REL.items()]


def scale_rows(calc):
    c = calc
    n_style = collections.Counter(c.style[d] for d in c.docs)
    rows = [u"| 項目 | 値 |", u"|---|---|"]
    rows.append(u"| 調整用の会社の数(型 A / B / C) | %d(%d / %d / %d) |" % (len(c.docs), n_style["A"], n_style["B"], n_style["C"]))
    rows.append(u"| claim の数(P22 / P26) | %d / %d |" % (len(c.claims), len(c.claims)))
    rows.append(u"| 読む行の数 | %d |" % len(c.read_keys))
    rows.append(u"| 注入の行の数(T1_VALUE / T8_REL / 合計) | %d / %d / %d |" % (len(c.inj_rows("T1_VALUE")), len(c.inj_rows("T8_REL")), len(c.inj)))
    rows.append(u"| 両 profile で対応が付く注入の行(T1_VALUE / T8_REL) | %d / %d |" % (len(c.both_mapped("T1_VALUE")), len(c.both_mapped("T8_REL"))))
    return rows


def state_rows(calc):
    c = calc
    rows = [u"| profile | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND | 計 | VALUE_MISMATCH の率 |", u"|---|---|---|---|---|---|---|"]
    for p in PROFILES:
        sc = c.state_counts(p)
        rows.append(u"| %s | %d | %d | %d | %d | %d | %s |" % (p, sc["GROUNDED"], sc["VALUE_MISMATCH"], sc["UNVERIFIABLE"], sc["POINTER_NOT_FOUND"],
                                                         sum(sc.values()), pc(sc["VALUE_MISMATCH"], len(c.claims))))
    return rows


def per_doc_rows(calc):
    c = calc
    rows = [u"| docID | 型 | claim(P26) | VALUE_MISMATCH(P22) | VALUE_MISMATCH(P26) | 読む行 | 注入 T1_VALUE | 注入 T8_REL | T8_REL で通した(P22 / P26) |",
            u"|---|---|---|---|---|---|---|---|---|"]
    for d in c.docs:
        cl = c.claims_of_doc(d)
        t8 = [x for x in c.inj_rows("T8_REL") if x["docID"] == d]
        rows.append(u"| %s | %s | %d | %d | %d | %d | %d | %d | %d / %d |" % (
            d, c.style[d], len(cl), sum(1 for x in cl if x["P22"]["state"] == "VALUE_MISMATCH"), sum(1 for x in cl if x["P26"]["state"] == "VALUE_MISMATCH"),
            sum(1 for k in c.read_keys if k[0] == d), len([x for x in c.inj_rows("T1_VALUE") if x["docID"] == d]), len(t8),
            sum(1 for x in t8 if x["P22"]["結果"] == LABEL_PASS), sum(1 for x in t8 if x["P26"]["結果"] == LABEL_PASS)))
    return rows


CELLS = [(u"道具", u"道1"), (u"道具", u"道2"), (u"道具", u"道3"), (u"道具", u"道4"), (u"道具", u"道5"), (u"道具", UNSURE),
         (u"文", u"文1"), (u"文", u"文2"), (u"文", u"文3"), (u"文", u"文4"), (u"文", UNSURE), (UNSURE, None)]


def reading_rows(calc):
    """読む行の合わせた札の内訳。P26 の判定(state と reason)ごとと全体。"""
    c = calc
    head = u"| P26 の判定 | 行 | " + u" | ".join(u"%s%s" % (s, u"/" + d if d else u"") for s, d in CELLS) + u" |"
    rows = [head, u"|" + u"---|" * (len(CELLS) + 2)]
    groups = collections.OrderedDict()
    for r in c.readings:
        groups.setdefault(c.p26_group(r), []).append(r)
    items = sorted(groups.items(), key=lambda kv: kv[0])
    for name, rs in items + [(u"全体", c.readings)]:
        cnt = c.reading_counts(rs)
        rows.append(u"| %s | %d | " % (name, len(rs)) + u" | ".join(u"%d" % cnt.get(cell, 0) for cell in CELLS) + u" |")
    return rows


def seat_rows(calc):
    c = calc
    n = len(c.readings)
    side = sum(1 for r in c.readings if r["席1"]["側"] == r["席2"]["側"])
    det = sum(1 for r in c.readings if r["席1"]["側"] == r["席2"]["側"] and r["席1"]["細目"] == r["席2"]["細目"])
    rows = [u"| 項目 | 値 |", u"|---|---|", u"| 2 席の側が一致した行 | %s |" % ab(side, n), u"| 側が一致し細目も一致した行 | %s |" % ab(det, n)]
    split = collections.Counter((r["席1"]["細目"], r["席2"]["細目"], c.merged(r)[0], c.merged(r)[1]) for r in c.readings
                                if r["席1"]["側"] == r["席2"]["側"] and r["席1"]["細目"] != r["席2"]["細目"])
    for (a, b, s, d), k in sorted(split.items(), key=lambda kv: tuple(u"%s" % x for x in kv[0])):
        rows.append(u"| 細目が割れた行(席1=%s・席2=%s → 合わせた %s/%s) | %d |" % (a, b, s, d, k))
    for seat in ("席1", "席2"):
        cnt = collections.Counter(r[seat]["細目"] for r in c.readings)
        rows.append(u"| %s の細目の内訳 | %s |" % (seat, u"・".join(u"%s %d" % (k, v) for k, v in sorted(cnt.items(), key=lambda kv: u"%s" % kv[0]))))
    return rows


def form_rows(calc):
    """読む行の claim の形(form・unit、P26 の記録)と合わせた細目。"""
    c = calc
    cnt = collections.Counter()
    for r in c.readings:
        cl = c.by_key[(r["docID"], r["id"])]["P26"]
        cnt[(cl["form"], cl["unit"] if cl["unit"] is not None else u"(単位なし)", c.merged(r)[1])] += 1
    rows = [u"| form | unit | 合わせた細目 | 行 |", u"|---|---|---|---|"]
    for (form, unit, det), k in sorted(cnt.items(), key=lambda kv: tuple(u"%s" % x for x in kv[0])):
        rows.append(u"| %s | %s | %s | %d |" % (form, unit, det, k))
    return rows


def inject_rows(calc):
    c = calc
    rows = [u"| 型 | profile | 文体 | 注入の行 | 対応が付く | 通した | 名指して原本の値を返した | 名指したが別の値 | 止めたが名指さない(POINTER_NOT_FOUND) | 止めたが名指さない(UNVERIFIABLE) | 名指して原本の値の率 | 通した率 |",
            u"|" + u"---|" * 12]
    for typ in TYPES:
        for p in PROFILES:
            for st in STYLES + (None,):
                m = c.mapped(typ, p, st)
                lc = [c.label_count(typ, p, lab, st) for lab in LABELS]
                rows.append(u"| %s | %s | %s | %d | %d | %s | %s | %s |" % (
                    typ, p, st or u"全体", len(c.inj_rows(typ, st)), len(m), u" | ".join(u"%d" % k for k in lc), pc(lc[1], len(m)), pc(lc[0], len(m))))
    return rows


def reason_rows(calc):
    c = calc
    cnt = collections.Counter()
    for x in c.inj:
        for p in PROFILES:
            if x[p]["対応"] and x[p]["結果"] in (LABEL_PNF, LABEL_UNV):
                cnt[(x["型"], p, x[p]["結果"], x[p]["reason"] or u"(reason なし)")] += 1
    rows = [u"| 型 | profile | 結果 | reason | 行 |", u"|---|---|---|---|---|"]
    for k, v in sorted(cnt.items(), key=lambda kv: tuple(u"%s" % y for y in kv[0])):
        rows.append(u"| %s | %s | %s | %s | %d |" % (k + (v,)))
    return rows


def cross_rows(calc):
    c = calc
    rows = [u"| 型 | P22 の結果 | P26 の結果 | 行 |", u"|---|---|---|---|"]
    for typ in TYPES:
        cnt = collections.Counter((x["P22"]["結果"], x["P26"]["結果"]) for x in c.both_mapped(typ))
        for (a, b), k in sorted(cnt.items(), key=lambda kv: tuple(u"%s" % y for y in kv[0])):
            rows.append(u"| %s | %s | %s | %d |" % (typ, a, b, k))
    return rows


def r_value_rows(calc):
    c = calc
    rows = [u"| r(T8_REL) | 対応が付く行 | P22: 通した | P22: 名指して原本の値 | P22: 名指したが別の値 | P26: 通した | P26: 名指して原本の値 | P26: 名指したが別の値 | P26: 止めたが名指さない |",
            u"|" + u"---|" * 9]
    both = c.both_mapped("T8_REL")
    for r in sorted(set(x["r"] for x in both)):
        rs = [x for x in both if x["r"] == r]
        k = lambda p, lab: sum(1 for x in rs if x[p]["結果"] == lab)               # noqa: E731
        rows.append(u"| %+g | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            r, len(rs), k("P22", LABEL_PASS), k("P22", LABEL_NAMED_ORIGINAL), k("P22", LABEL_NAMED_OTHER),
            k("P26", LABEL_PASS), k("P26", LABEL_NAMED_ORIGINAL), k("P26", LABEL_NAMED_OTHER), k("P26", LABEL_PNF) + k("P26", LABEL_UNV)))
    return rows


def passed_rows(calc):
    """T8_REL で通った行の内訳。基準の claim の unit は記録の claim の欄から(書かれた単位は記録に無い)。"""
    c = calc
    both = c.both_mapped("T8_REL")
    axes = [(u"基準の claim の unit", lambda x: c.by_key[(x["docID"], x["基準の claim"])]["P26"]["unit"] or u"(単位なし)"),
            (u"基準の claim の form", lambda x: c.by_key[(x["docID"], x["基準の claim"])]["P26"]["form"]),
            (u"文体", lambda x: x["文体"])]
    rows = [u"| 見る軸 | 値 | 対応が付く行 | 通した(P22) | 通した(P26) |", u"|---|---|---|---|---|"]
    for name, fn in axes:
        vals = sorted(set(fn(x) for x in both))
        for v in vals:
            rs = [x for x in both if fn(x) == v]
            rows.append(u"| %s | %s | %d | %d | %d |" % (name, v, len(rs), sum(1 for x in rs if x["P22"]["結果"] == LABEL_PASS), sum(1 for x in rs if x["P26"]["結果"] == LABEL_PASS)))
    return rows


def not_passed_rows(calc):
    """通した以外の行(対応が付く行から通した行を除く)のうち、名指して原本の値を返した行。"""
    c = calc
    rows = [u"| 型 | profile | 対応が付く | 通した | 通した以外 | 通した以外のうち名指して原本の値を返した | 率 |", u"|---|---|---|---|---|---|---|"]
    for typ in TYPES:
        for p in PROFILES:
            m = len(c.mapped(typ, p))
            ps = c.label_count(typ, p, LABEL_PASS)
            no = c.label_count(typ, p, LABEL_NAMED_ORIGINAL)
            rows.append(u"| %s | %s | %d | %d | %d | %d | %s |" % (typ, p, m, ps, m - ps, no, pc(no, m - ps)))
    return rows


def r8_ref_rows(calc):
    """R-8 の分母の読み方の参考。封の R-8 は分母の行を指定していないので読む行の全体で当否を付け、P26 の VALUE_MISMATCH の行だけで数えた場合を並べる。"""
    c = calc
    rows = [u"| 分母の読み方 | 細目が付いた道具の行 | 道1〜道4 | 道5 |", u"|---|---|---|---|"]
    for name, sel in ((u"読む行の全体(当否に使った)", c.readings),
                      (u"P26 の VALUE_MISMATCH の行だけ(参考。当否には使っていない)",
                       [r for r in c.readings if c.by_key[(r["docID"], r["id"])]["P26"]["state"] == "VALUE_MISMATCH"])):
        cnt = collections.Counter(c.merged(r) for r in sel)
        tool = sum(n for (sd, d), n in cnt.items() if sd == u"道具" and d != UNSURE)
        b = sum(n for (sd, d), n in cnt.items() if sd == u"道具" and d in (u"道1", u"道2", u"道3", u"道4"))
        n5 = sum(n for (sd, d), n in cnt.items() if sd == u"道具" and d == u"道5")
        rows.append(u"| %s | %d | %s | %s |" % (name, tool, ab(b, tool), ab(n5, tool)))
    return rows


def build_blocks(recs, recs_bytes, seal_text):
    """文書の門の表。名前 -> 行の列。"""
    calc = Calc(recs)
    sub, summary = r_rows(calc, seal_text)
    b = collections.OrderedDict()
    b["sha"] = rec_sha_rows(recs_bytes)
    b["規模"] = scale_rows(calc)
    b["state"] = state_rows(calc)
    b["書類別"] = per_doc_rows(calc)
    b["R-小項目"] = [u"| 小項目 | 見るもの | 予測(封 §7 の幅) | 実測 | 当否 |", u"|---|---|---|---|---|"] + sub
    b["R-当否"] = [u"| R | 当否 | 外れた小項目 |", u"|---|---|---|"] + summary
    b["R-8-参考"] = r8_ref_rows(calc)
    b["読み-札"] = reading_rows(calc)
    b["読み-席"] = seat_rows(calc)
    b["読み-形"] = form_rows(calc)
    b["注入-分布"] = inject_rows(calc)
    b["注入-通した以外"] = not_passed_rows(calc)
    b["注入-reason"] = reason_rows(calc)
    b["注入-交差"] = cross_rows(calc)
    b["注入-r"] = r_value_rows(calc)
    b["T8-通った"] = passed_rows(calc)
    return b


BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)


def doc_blocks(doc_text):
    out = collections.OrderedDict()
    for m in BLOCK_RE.finditer(doc_text):
        assert m.group(1) not in out, "同じ名前の門の表が 2 つ: %s" % m.group(1)
        out[m.group(1)] = m.group(2).split("\n")
    return out


def render_block(name, lines):
    return u"<!-- 門:start %s -->\n%s\n<!-- 門:end -->" % (name, u"\n".join(lines))


# ======================================================================================================
# 記録の中身の門(a)(b)(c)
DOC_RE = re.compile(r"S100[0-9A-Z]{4}$")
ROW_RE = re.compile(r"S100[0-9A-Z]{4}:[A-Z][0-9]{3}$")
REASON_WORDS = (u"当期の doc_id が違う", u"応答なし", u"行なし", u"当期が 1 行でない", u"差し替えの節なし")
REASON_WORDS_RE = u"(?:%s)$" % u"|".join(re.escape(w) for w in REASON_WORDS)
REASON_KEY_RE = re.compile(r"(?:[A-Za-z_]+(?:\([A-Za-z_ ;,:\-]*\))?|\(reason なし\))$")
JP_RE = re.compile(u"[\u3000-\u30ff\u3400-\u9fff\uff00-\uffef]")


class FK(object):
    """自由な名前の欄の集まり(名前の形を regex で縛り、中身の木を持つ)。"""

    def __init__(self, regex, node):
        self.regex = re.compile(regex)
        self.node = node


class Opt(object):
    """その欄は記録によっては無い(逆向きの『許可にあるのに記録に無い』検査から外す)。"""

    def __init__(self, node):
        self.node = node


def leaf(gloss):
    return (gloss, None)


RATE = (u"件・分母・率の 3 つ組", {u"件": leaf(u"数"), u"分母": leaf(u"率の分母の数"), u"率": leaf(u"% の実数")})
SNAP = (u"folder の件数と名前の一覧の sha256", {u"folder": leaf(u"folder の名前(~ 始まりの path)"), u"存在": Opt(leaf(u"folder が在るか")),
                                              u"件数": leaf(u"file の数"), u"名前の一覧の sha256": leaf(u"名前の一覧の sha256")})
SNAP_PAIR = (u"既存の cache と ZIP の folder の snapshot", {u"既存の cache": SNAP, u"ZIP の folder": SNAP})
CACHE_BEFORE_AFTER = (u"cache の前後(件数と名前の一覧の sha256。変わっていないこと)", {u"前": SNAP_PAIR, u"後": SNAP_PAIR, u"変化なし": leaf(u"前後で同じか")})
STATE4 = (u"4 つの state の数", {u"GROUNDED": leaf(u"数"), u"VALUE_MISMATCH": leaf(u"数"), u"UNVERIFIABLE": leaf(u"数"), u"POINTER_NOT_FOUND": leaf(u"数")})
PROF2 = lambda node: (u"P22 と P26 の対", {u"P22": node, u"P26": node})            # noqa: E731

RUN_HEADER = {
    u"seal": leaf(u"封の path"), u"step": leaf(u"この記録の段の名前(固定の文)"), u"dry_run": leaf(u"下見(作り物の engine)か"),
    u"backend": leaf(u"engine の種類(real / stub / なし)"),
    u"HEAD の commit": leaf(u"走らせた時の HEAD(40 桁)"), u"W の commit": leaf(u"凍結 W の commit(40 桁)"), u"W は HEAD の祖先": leaf(u"W が HEAD の祖先か"),
    u"この script の sha256": leaf(u"測定の script の sha256"), u"対象の docID": leaf(u"対象の docID の列(調整用)"),
    u"対象は調整用の全部": leaf(u"対象が調整用の全部か"),
    u"使った文の sha256": (u"docID -> 文の sha256(文の字は無い)", FK(DOC_RE.pattern, leaf(u"文の sha256"))),
    u"engine の指紋": (u"engine の file の sha256 と数(real のときだけ中身がある)", {
        u"adapter_xbrl_py_sha256": Opt(leaf(u"adapters/xbrl の sha256")), u"adapter_xbrl_py_files": Opt(leaf(u"file の数")),
        u"core_py_sha256": Opt(leaf(u"core の sha256")), u"core_py_files": Opt(leaf(u"file の数")), u"git_commit": Opt(leaf(u"git の commit(40 桁)"))}),
    u"cache の前後": CACHE_BEFORE_AFTER,
}

CLAIM_SIDE = (u"1 つの profile の claim の判定(span・subject・value・recomputed は無い)", {
    u"kind": leaf(u"claim の種類"), u"form": leaf(u"claim の形(direct_value など)"), u"unit": leaf(u"単位"),
    u"state": leaf(u"state(4 つの語)"), u"reason": leaf(u"理由の符号(自由文でない)"), u"pointers": leaf(u"XBRL の要素と context の字の列")})

ALLOWED = {
    "dbfetch": {
        u"seal": leaf(u"封の path"), u"step": leaf(u"記録の段の名前"), u"dry_run": leaf(u"下見か"),
        u"鍵": (u"鍵の扱いの宣言(値は無い)", {u"環境変数の名前": leaf(u"環境変数の名前"), u"値": leaf(u"『読まない』の宣言の文")}),
        u"応答の値の扱い": leaf(u"応答の値を入れない宣言の文"),
        u"除いた 3 コード": (u"前の 3 本の EDINET コードと除かれた件数", {u"コード": leaf(u"EDINET コードの列"), u"除かれた件数": leaf(u"数")}),
        u"照らし": (u"候補ごとの照らし", [{
            u"docID": leaf(u"書類 ID"), u"位置": leaf(u"候補の位置"), u"区分": leaf(u"主 / 予備"), u"EDINET コード": Opt(leaf(u"EDINET コード")),
            u"ZIP の sha256 が記録と一致": Opt(leaf(u"ZIP の照合")),
            u"financials の応答": Opt((u"status と試行の数", {u"status": leaf(u"HTTP の status"), u"試行": leaf(u"試行の数")})),
            u"判定": leaf(u"残る / 除く / 照らさなかった"), u"理由": Opt(leaf(u"除いた理由(閉じた語。自由文でない)")), u"差し替え": Opt(leaf(u"差し替えの結果"))}]),
        u"予備の候補を照らしたか": leaf(u"真偽"), u"除いた理由の内訳": (u"理由の語 -> 数", FK(REASON_WORDS_RE, leaf(u"数"))),
        u"K": leaf(u"残る会社の列(docID)"), u"|K|": leaf(u"数"), u"U": leaf(u"使う会社の列(docID)"), u"|U|": leaf(u"数"),
        u"調整用": leaf(u"調整用の docID の列"), u"評価用": leaf(u"評価用の docID の列"), u"予備": leaf(u"予備の docID の列"),
        u"型の割り当て": (u"docID -> 型", FK(DOC_RE.pattern, leaf(u"A / B / C"))), u"止め": leaf(u"止まった理由。無ければ null"),
        u"U の材料": (u"U の会社の応答の取得結果(値は無い)", [{
            u"docID": leaf(u"書類 ID"),
            u"companies": (u"status と JSON として読めたか", {u"status": leaf(u"HTTP の status"), u"JSON として読める": leaf(u"真偽")}),
            u"ratios": (u"status と JSON として読めたか", {u"status": leaf(u"HTTP の status"), u"JSON として読める": leaf(u"真偽")})}]),
        u"材料が欠けた U の会社": leaf(u"docID の列"),
        u"呼び出し": (u"API 呼び出しの記録(応答は bytes と sha256 だけ)", [{
            u"順": leaf(u"呼んだ順"), u"docID": leaf(u"書類 ID"), u"EDINET コード": leaf(u"EDINET コード"), u"種類": leaf(u"financials / companies / ratios"),
            u"path": leaf(u"API の path(鍵なし)"),
            u"試行": (u"試行ごとの時刻・status", [{u"時刻(UTC)": leaf(u"時刻"), u"JST の日付": leaf(u"日付"), u"status": leaf(u"HTTP の status")}]),
            u"status": leaf(u"最終の status"), u"再試行の回数": leaf(u"数"), u"時刻(UTC)": leaf(u"時刻"), u"bytes": leaf(u"応答の bytes 数"),
            u"sha256": leaf(u"応答の sha256"), u"JSON として読める": leaf(u"真偽")}]),
        u"回数": (u"呼び出しの回数の集計", {
            u"上限(1 日 JST・再試行を含む)": leaf(u"数"),
            u"既に使った数として数えた分(封 §11-0 の下見)": (u"日付 -> 数", FK(r"\d{4}-\d\d-\d\d", leaf(u"数"))),
            u"この script の試行の合計": leaf(u"数"), u"試行の日別(JST)": (u"日付 -> 数", FK(r"\d{4}-\d\d-\d\d", leaf(u"数"))),
            u"最大の 1 日(下見の分を含む)": leaf(u"数"), u"呼び出し(応答の最終の行)の数": leaf(u"数"), u"応答なしの数": leaf(u"数")}),
        u"上限で止まった履歴": leaf(u"履歴の列"),
        u"置いた場所": (u"repo の外の置き場の宣言", {u"応答": leaf(u"置き場の path"), u"既存の cache": leaf(u"既存 cache に足さない宣言の文")}),
        u"cache の前後": CACHE_BEFORE_AFTER, u"取得した時刻(UTC)": leaf(u"時刻"), u"引き直さない": leaf(u"宣言の文"), u"limits": leaf(u"限界の文の列"),
    },
    "reports": {
        u"seal": leaf(u"封の path"), u"step": leaf(u"記録の段の名前"),
        u"依って立つ commit": (u"依った commit(短縮)", {
            u"取得の記録": leaf(u"commit の短縮"), u"封の 2 つ目の追記": leaf(u"commit の短縮"),
            u"封の 3 つ目の追記(包みの 1 文と path で渡す)": leaf(u"commit の短縮")}),
        u"取得の記録": leaf(u"取得の記録の path"), u"指示文の型板の sha256": leaf(u"型板の sha256"),
        u"包みの 1 文の sha256(UTF-8、改行を含めない)": leaf(u"包みの 1 文の sha256"),
        u"字数の数え方": leaf(u"数え方の文"), u"行数の数え方": leaf(u"数え方の文"),
        u"型の幅": (u"型 -> 字数の幅", FK(r"[ABC]$", leaf(u"幅の文"))),
        u"返事の取り出し": leaf(u"取り出し方の文"), u"入力の照合の仕方": leaf(u"照合の仕方の文"),
        u"置いた場所": (u"repo の外の置き場", {u"指示文": leaf(u"path"), u"文": leaf(u"path")}), u"文の扱い": leaf(u"文を入れない宣言の文"),
        u"会社": (u"書き手 1 席ごとの記録(文の字は無い。sha256・字数・行数だけ)", [{
            u"docID": leaf(u"書類 ID"), u"区分": leaf(u"調整用 / 評価用"), u"型": leaf(u"A / B / C"),
            u"指示文の型板の sha256": leaf(u"sha256"), u"渡した指示文の全体の sha256": leaf(u"sha256"), u"席に渡した字": leaf(u"包みの 1 文と path の説明"),
            u"包みの 1 文の sha256": leaf(u"sha256"), u"入力の照合": leaf(u"一致 / 不一致"), u"Read の回数": leaf(u"数"),
            u"文の sha256": leaf(u"文の sha256(W の凍結)"), u"文の bytes": leaf(u"数"), u"文の字数(len。改行を含む)": leaf(u"数"),
            u"文の字数(改行を除く)": leaf(u"数"), u"文の行数(str.splitlines の数)": leaf(u"数"), u"字数が型の幅の内(改行を含む len)": leaf(u"真偽"),
            u"試行の回数": leaf(u"数"), u"やり直しの理由": leaf(u"null か符号"), u"席が道具を使った回数(Read 1 回と返事を返す 1 回を除く)": leaf(u"数"),
            u"返事の出どころ": leaf(u"SubagentHandback"),
            u"席の model": (u"設定と会話の記録に出た model の id", {u"設定": leaf(u"設定の説明の文"), u"会話の記録に出た model の id": leaf(u"model の id の列")}),
            u"書いた時刻(UTC)": leaf(u"時刻"), u"書けなかった": leaf(u"真偽")}]),
        u"集計": (u"書き手の集計", {
            u"書けた数": leaf(u"数"), u"書けなかった数": leaf(u"数"), u"試行の合計": leaf(u"数"), u"やり直しの数": leaf(u"数"),
            u"入力の照合が一致した数": leaf(u"数"), u"Read の回数の内訳": (u"回数 -> 席の数", FK(r"\d+$", leaf(u"数"))),
            u"道具を使った席の数(Read 1 回と返事を除く)": leaf(u"数"),
            u"型ごと": (u"型(区分) -> 幅の内の数", FK(r"[ABC]\((?:調整用|評価用|全体)\)$", (u"数と幅の内の数", {
                u"数": leaf(u"数"), u"幅": leaf(u"幅の文"), u"幅の内(改行を含む len)": leaf(u"数"), u"幅の内(改行を除く)": leaf(u"数")}))),
            u"字数が型の幅の内に入った数(改行を含む len)": leaf(u"数")}),
        u"cache の前後": CACHE_BEFORE_AFTER,
    },
    "tune": dict(RUN_HEADER, **{
        u"claim の対の付け方": leaf(u"対の付け方の文"),
        u"会社": (u"調整用の会社ごと(文の sha256 と claim の数)", [{
            u"docID": leaf(u"書類 ID"), u"型": leaf(u"A / B / C"), u"文の sha256": leaf(u"文の sha256"),
            u"claim の数": PROF2(leaf(u"数")), u"state の数": PROF2(STATE4),
            u"片方の profile にしか無い id": leaf(u"id の列"), u"値・span・単位が profile 間で違う id": leaf(u"id の列")}]),
        u"claim": (u"claim ごとの判定(id・kind・form・unit・state・reason・pointers だけ)", [{
            u"docID": leaf(u"書類 ID"), u"id": leaf(u"claim の id"), u"P22": CLAIM_SIDE, u"P26": CLAIM_SIDE}]),
        u"集計": (u"script の自前の集計", {
            u"claim": PROF2(leaf(u"数")), u"state の数": PROF2(STATE4), u"VALUE_MISMATCH の率": PROF2(RATE),
            u"文あたりの claim の数(P26)の型ごと": (u"型 -> 数と中央値", {s: (u"数と中央値", {
                u"文の数": leaf(u"数"), u"文あたりの claim の数(P26)": leaf(u"数の列"), u"中央値": leaf(u"中央値")}) for s in STYLES}),
            u"読む行": (u"読む行の数と条件ごとの数", {u"数": leaf(u"数"), u"条件ごと(重なる)": (u"条件 -> 数", FK(r"[A-Za-z0-9_]+$", leaf(u"数")))})}),
        u"読む行": (u"読む行の一覧", [{u"行": leaf(u"docID:claim id"), u"docID": leaf(u"書類 ID"), u"id": leaf(u"claim id"), u"条件": leaf(u"当たった条件の符号の列")}]),
        u"repo の外に置いたもの": (u"repo の外の file の sha256", {
            u"folder": leaf(u"置き場"), u"全部の欄(span・subject・value・recomputed を含む)": (u"全部の欄の file", {
                u"file": leaf(u"file 名"), u"sha256": leaf(u"sha256"), u"bytes": leaf(u"bytes")}),
            u"dossier": (u"読み手の束", {
                u"folder": leaf(u"置き場"), u"件数": leaf(u"数"), u"index.json の sha256": leaf(u"sha256"),
                u"各 file の sha256": (u"行 -> sha256", FK(ROW_RE.pattern, leaf(u"sha256"))),
                u"読み手の指示文 reader_prompt.txt の sha256": leaf(u"sha256"),
                u"読み手の指示文は封 §5-6 の字(prompts の READER_PROMPT)と同じ": leaf(u"真偽")})}),
        u"限界": leaf(u"限界の文の列"),
    }),
    "tune_inject": dict(RUN_HEADER, **{
        u"種": (u"種 file の追跡と sha256", {u"file": leaf(u"path"), u"sealed_in_commit": leaf(u"封じた commit"), u"seed_file_sha256": leaf(u"sha256")}),
        u"型": (u"注入の型の宣言", {u"T1_VALUE": leaf(u"宣言の文"), u"T8_REL": leaf(u"宣言の文"), u"上限": leaf(u"宣言の文")}),
        u"書類別の数え": (u"docID -> 型 -> 数え", FK(DOC_RE.pattern, (u"型ごとの数え", {
            t: (u"数えの名前 -> 数", FK(u"(?:作れる site|採った|円族の token|r が決まらず site にしない|基準に対応が付かない|profile 間で claim が合わない|"
                                      u"両方 GROUNDED|P22 のみ GROUNDED|P26 のみ GROUNDED|どちらも GROUNDED でない)$", leaf(u"数"))) for t in TYPES}))),
        u"注入の行の数": leaf(u"数"),
        u"集計": (u"script の自前の集計", {t: (u"型の集計", dict({p: (u"profile の集計", {st: (u"文体(と全体)の集計", {
            u"注入の行": leaf(u"数"), u"対応が付く": leaf(u"数"), u"対応が付かない": leaf(u"数"),
            LABEL_PASS: RATE, LABEL_NAMED_ORIGINAL: RATE, LABEL_NAMED_OTHER: RATE, LABEL_PNF: RATE, LABEL_UNV: RATE,
            u"POINTER_NOT_FOUND の reason の内訳": (u"reason -> 数", FK(REASON_KEY_RE.pattern, leaf(u"数"))),
            u"UNVERIFIABLE の reason の内訳": (u"reason -> 数", FK(REASON_KEY_RE.pattern, leaf(u"数")))}) for st in STYLES + (u"全体",)}) for p in PROFILES},
            **{u"両方の profile で対応が付く": leaf(u"数")})) for t in TYPES}),
        u"T8_REL の site": (u"T8_REL の site の数", {u"注入の行": leaf(u"数"), u"作れる site(上限の前)": leaf(u"数")}),
        u"行": (u"注入の行ごとの結果(注入の字・新しい値は無い)", [{
            u"docID": leaf(u"書類 ID"), u"id": leaf(u"注入の id"), u"型": leaf(u"T1_VALUE / T8_REL"), u"文体": leaf(u"A / B / C"),
            u"基準の claim": leaf(u"土台の claim id"),
            u"P22": (u"profile の結果", {u"対応": leaf(u"対応が付くか"), u"結果": leaf(u"結果の語"), u"state": leaf(u"state"), u"reason": leaf(u"理由の符号")}),
            u"P26": (u"profile の結果", {u"対応": leaf(u"対応が付くか"), u"結果": leaf(u"結果の語"), u"state": leaf(u"state"), u"reason": leaf(u"理由の符号")}),
            u"r": Opt(leaf(u"T8_REL の相対の変え幅")), u"r を決めた回": Opt(leaf(u"r を決めた試行の回"))}]),
        u"repo の外に置いたもの": (u"repo の外の file の sha256", {u"folder": leaf(u"置き場"), u"注入の字・新しい値": (u"注入の字の file", {
            u"file": leaf(u"file 名"), u"sha256": leaf(u"sha256"), u"bytes": leaf(u"bytes")})}),
        u"限界": leaf(u"限界の文の列"),
    }),
    "tune_readings": dict(RUN_HEADER, **{
        u"読みは": leaf(u"エージェントの読みで人間の読みでない宣言"), u"合わせ方(封 §5-5)": leaf(u"合わせ方の文"),
        u"入力": (u"入力の sha256", {u"判定の記録": leaf(u"path"), u"判定の記録の sha256": leaf(u"sha256"),
                                  u"席1 の札の file の sha256": leaf(u"sha256"), u"席2 の札の file の sha256": leaf(u"sha256")}),
        u"行": (u"読む行ごとの札(側と細目の語だけ。理由と道5の形は無い)", [{
            u"行": leaf(u"docID:claim id"), u"docID": leaf(u"書類 ID"), u"id": leaf(u"claim id"),
            u"席1": (u"席1 の札", {u"側": leaf(u"文 / 道具 / 分からない"), u"細目": leaf(u"文1〜道5 か null")}),
            u"席2": (u"席2 の札", {u"側": leaf(u"文 / 道具 / 分からない"), u"細目": leaf(u"文1〜道5 か null")}),
            u"合わせた": (u"合わせた札", {u"側": leaf(u"側"), u"細目": leaf(u"細目")})}]),
        u"集計": (u"script の自前の集計", {
            u"読む行": leaf(u"数"), u"2 席の側が一致した行": RATE,
            u"合わせた側の内訳": (u"側 -> 数", {u"文": leaf(u"数"), u"道具": leaf(u"数"), u"分からない": leaf(u"数")}),
            u"P26 で VALUE_MISMATCH の行": (u"P26 VALUE_MISMATCH の行の側", {
                u"行": leaf(u"数"), u"合わせた側の内訳": (u"側 -> 数", {u"文": leaf(u"数"), u"道具": leaf(u"数"), u"分からない": leaf(u"数")}),
                u"道具の率": RATE, u"分からないの率": RATE}),
            u"合わせた細目が付いた道具の行": (u"細目が付いた道具の行", {
                u"行": leaf(u"数"), u"細目の内訳": (u"細目 -> 数", FK(r"道[1-5]$", leaf(u"数"))), u"道1〜道4": RATE, u"道5": RATE}),
            u"合わせた札が文2の行": leaf(u"数")}),
        u"repo の外に置いたもの": (u"repo の外の file の sha256", {u"folder": leaf(u"置き場"), u"道5 の形と各席の理由の文": (u"自由文の file", {
            u"file": leaf(u"file 名"), u"sha256": leaf(u"sha256"), u"bytes": leaf(u"bytes")})}),
    }),
}

#: 欄の名前として置かない(repo に入れない)。完全一致。理由の文・道5の形・本文・抜粋・会社名にあたる欄
FORBIDDEN_NAMES = (u"span", u"subject", u"value", u"recomputed", u"理由", u"道5の形", u"本文", u"抜粋", u"text", u"excerpt", u"quote",
                   u"会社名", u"name", u"company", u"title", u"paragraph", u"段落", u"reason_text", u"why")
#: 禁止の名前でも置いてよい欄(path)と、その値の規則。dbfetch の除いた理由は閉じた語(自由文でない)
EXEMPT_PATHS = {"/照らし[]/理由": lambda v: v is None or v in REASON_WORDS}

#: 日本語を含む文字列の値の集合の指紋(各記録の、重複を除いた日本語を含む文字列を並べ替えて改行で結んだ sha256)。
#: 新しい日本語の文字列(偽の会社名・偽の抜粋の 1 文)が 1 つ足されても、1 つ書き換えられても変わる。記録を作り直したら直す(凍結の面)。
JP_DIGEST = {
    "dbfetch": "534e5e74769599d00d8589076119f4046083faf2d983607799be65956fd022b6",
    "reports": "671b90e9e89144933d06191d213240f2ba7c6375074495f83e2736245f981547",
    "tune": "00d29706448e108d188527e22f5f57212066c5488f511731ee565e5d9c6c9981",
    "tune_inject": "a4d17426a3c04880568bbae0e67fa8418e48a516a93a45487298fc6a72aa89b1",
    "tune_readings": "46b4999c70bda2800d7d3dc3c5cf0934ca0d7e6ac5928573a6968f126bec34b8",
}

NONJP_SAFE = [re.compile(p) for p in (
    r"[0-9a-f]{64}", r"[0-9a-f]{40}", r"[0-9a-f]{7,12}", r"S100[0-9A-Z]{4}", r"S100[0-9A-Z]{4}:[A-Z][0-9]{3}", r"S100[0-9A-Z]{4}-T[18]-\d{2}",
    r"[NT][0-9]{3}", r"E[0-9]{5}", r"/companies/E[0-9]{5}(?:/ratios|/financials\?years=3&include_nulls=true&include_null_reasons=true)?",
    r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", r"\d{4}-\d\d-\d\d", r"[ABC]", r"P2[26]", r"%",
    r"[A-Za-z][A-Za-z0-9_]*(?:\([A-Za-z_ ;,:\-]*\))?",                                   # 符号・state・reason・model の id 以外の語
    r"claude-[a-z0-9\-]+", r"[A-Za-z_]+:[A-Za-z0-9_:@/*+\-().=<>]*", r"[a-z]+/",
    r"(?:audit-core/)?(?:docs|fixtures|measure)/[A-Za-z0-9_./\-]+", r"~/\.cache/audit-core/[A-Za-z0-9_<>./\-{},]*", r"[A-Za-z0-9_]+\.(?:json|txt)",
    r"[A-Za-z0-9_.]+@[A-Za-z0-9_]+",
)]


def strings_of(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            for s in strings_of(v):
                yield s
    elif isinstance(obj, list):
        for v in obj:
            for s in strings_of(v):
                yield s
    elif isinstance(obj, basestring_t):
        yield obj


try:
    basestring_t = basestring            # noqa: F821
except NameError:
    basestring_t = str


def keys_of(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            for x in keys_of(v):
                yield x
    elif isinstance(obj, list):
        for v in obj:
            for x in keys_of(v):
                yield x


def jp_digest(obj):
    jp = sorted(set(s for s in strings_of(obj) if JP_RE.search(s)))
    return sha256_hex(u"\n".join(jp).encode("utf-8"))


def _walk(value, node, path, problems, seen):
    seen.add(path)
    if isinstance(node, Opt):
        node = node.node
    gloss, child = node
    if child is None:
        if isinstance(value, dict):
            problems.append(u"入れ子の欄が許可に無い: %s" % path)
        elif isinstance(value, list):
            for v in value:
                if isinstance(v, (dict, list)):
                    problems.append(u"入れ子の欄が許可に無い: %s" % path)
                    break
        return
    if isinstance(child, FK):
        if not isinstance(value, dict):
            problems.append(u"欄の集まりでない: %s" % path)
            return
        for k, v in value.items():
            if not child.regex.match(k):
                problems.append(u"欄の名前が許可の形でない: %s/*" % path)
                continue
            _walk(v, child.node, path + "/*", problems, seen)
        return
    if isinstance(child, list):
        if not isinstance(value, list):
            problems.append(u"列でない: %s" % path)
            return
        for item in value:
            if not isinstance(item, dict):
                problems.append(u"列の要素が欄の集まりでない: %s[]" % path)
                continue
            _walk_obj(item, child[0], path + "[]", problems, seen)
        return
    if not isinstance(value, dict):
        problems.append(u"欄の集まりでない: %s" % path)
        return
    _walk_obj(value, child, path, problems, seen)


def _walk_obj(value, children, path, problems, seen):
    for k, v in value.items():
        sub = children.get(k)
        if sub is None:
            problems.append(u"欄が許可の一覧に無い: %s/%s" % (path, k))
            continue
        _walk(v, sub, path + "/" + k, problems, seen)


def _static_paths(children, path, out, required):
    """許可の木の欄の path(Opt と FK の下は『記録に在ること』を要求しない)。"""
    for k, node in children.items():
        opt = isinstance(node, Opt)
        n = node.node if opt else node
        gloss, child = n
        assert isinstance(gloss, basestring_t) and gloss, (path, k)
        p = path + "/" + k
        out.add(p)
        if not opt and required is not None:
            required.add(p)
        if isinstance(child, dict):
            _static_paths(child, p, out, required if not opt else None)
        elif isinstance(child, list):
            _static_paths(child[0], p + "[]", out, required if not opt else None)
        elif isinstance(child, FK):
            pass


def required_paths(name):
    out, req = set(), set()
    _static_paths(ALLOWED[name], "", out, req)
    return req


def _exempt_ok(path, value):
    return path in EXEMPT_PATHS and EXEMPT_PATHS[path](value)


def _forbidden_name_problems(obj, path, problems):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = path + "/" + k
            if k in FORBIDDEN_NAMES and not _exempt_ok(re.sub(r"/S100[0-9A-Z]{4}", "/<docID>", p), v):
                problems.append(u"repo に置かない欄: %s" % p)
            _forbidden_name_problems(v, p, problems)
    elif isinstance(obj, list):
        for v in obj:
            _forbidden_name_problems(v, path + "[]", problems)


def record_problems(name, obj, check_jp_digest=True, key_leak_fns=None):
    """記録 1 本の中身の検査。問題の文の列(空なら通す)。値の字は返さない(欄の path と種類だけ)。
    (a) 欄の木が許可の一覧と一致  (b) 禁止の名前の欄が無い  (c) 前例の key_leaks / record_key_leaks が空  + 文字列の値の形。"""
    problems = []
    seen = set()
    node = (u"記録の根", ALLOWED[name])
    _walk(obj, node, "", problems, seen)
    for p in sorted(required_paths(name) - seen):
        problems.append(u"許可の一覧にあるのに記録に無い欄: %s" % p)
    _forbidden_name_problems(obj, "", problems)
    for s in strings_of(obj):
        if JP_RE.search(s):
            continue
        if not any(rx.fullmatch(s) for rx in NONJP_SAFE):
            problems.append(u"日本語を含まない文字列の値が許可の形でない(長さ %d)" % len(s))
    if check_jp_digest and jp_digest(obj) != JP_DIGEST[name]:
        problems.append(u"日本語を含む文字列の値の集合が凍結の指紋と違う")
    for fn in (key_leak_fns or []):
        leaks = fn(obj)
        if leaks:
            problems.append(u"鍵らしい字(%s)" % u"/".join(sorted(set(leaks))))
    return problems


def git(*args):
    return subprocess.run(["git", "-C", ROOT] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# ======================================================================================================
class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec_bytes = collections.OrderedDict((k, read_bytes(rel)) for k, rel in RECORD_REL.items())
        cls.recs = collections.OrderedDict((k, json.loads(b.decode("utf-8"))) for k, b in cls.rec_bytes.items())
        cls.seal = read_text(SEAL_REL)
        cls.doc = read_text(DOC_REL)
        cls.calc = Calc(cls.recs)
        cls.blocks = build_blocks(cls.recs, cls.rec_bytes, cls.seal)


class TestDocNumbers(Base):
    def test_01_every_gated_table_in_the_doc_equals_the_table_rebuilt_from_the_records(self):
        got = doc_blocks(self.doc)
        self.assertEqual(list(got), list(self.blocks), u"文書の門の表の名前と順が違う")
        for name, lines in self.blocks.items():
            self.assertEqual(got[name], lines, name)

    def test_02_no_table_row_is_outside_a_gated_block(self):
        stripped = BLOCK_RE.sub("", self.doc)
        rows = [l for l in stripped.split("\n") if l.lstrip().startswith("|")]
        self.assertEqual(rows, [], u"門の外に表の行がある(数を持つ表は門の中に置く)")

    def test_03_prose_numbers_need_the_not_gated_mark(self):
        stripped = BLOCK_RE.sub("", self.doc)
        bad = []
        for l in stripped.split("\n"):
            if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席)", l) and u"【門なし】" not in l:
                bad.append(l[:50])
        self.assertEqual(bad, [], u"散文の数に【門なし】の印が無い")

    def test_04_doc_does_not_name_any_eval_docid(self):
        eval_ids = [c["docID"] for c in self.recs["reports"]["会社"] if c["区分"] == u"評価用"]
        self.assertEqual(len(eval_ids), 10)
        for d in eval_ids:
            self.assertNotIn(d, self.doc)
            self.assertNotIn(d, read_text("tests/measure/test_xbrl_p27_tune_result.py"))

    def test_05_doc_names_only_tuning_docids(self):
        tune_ids = set(self.calc.docs)
        named = set(re.findall(r"S100[0-9A-Z]{4}", self.doc))
        self.assertLessEqual(named, tune_ids)
        self.assertEqual(len(tune_ids), 10)

    def test_06_record_shas_in_the_doc_equal_the_files(self):
        rows = self.blocks["sha"]
        self.assertEqual(len(rows), 7)
        for k, rel in RECORD_REL.items():
            self.assertIn(u"| %s | %s |" % (rel, sha256_hex(read_bytes(rel))), doc_blocks(self.doc)["sha"])

    def test_07_doc_declares_what_is_gated_and_what_is_not(self):
        for needle in (u"門なし", u"規則の案は書かない", u"エージェントの読み", u"人の目", u"同じ model"):
            self.assertIn(needle, self.doc, needle)


class TestRecompute(Base):
    """記録の自前の集計(script が書いた欄)と、ここで作り直した数が同じ(実装を 2 つ持つ)。"""

    def test_10_claims_and_states_equal_the_judge_record_own_summary(self):
        t = self.recs["tune"]
        c = self.calc
        for p in PROFILES:
            self.assertEqual(t["集計"]["claim"][p], len(c.claims))
            self.assertEqual(t["集計"]["state の数"][p], c.state_counts(p))
            self.assertEqual(t["集計"]["VALUE_MISMATCH の率"][p]["件"], c.state_counts(p)["VALUE_MISMATCH"])
            self.assertAlmostEqual(t["集計"]["VALUE_MISMATCH の率"][p]["率"], pc_num(c.state_counts(p)["VALUE_MISMATCH"], len(c.claims)), delta=0.051)
        for s in STYLES:
            self.assertEqual(t["集計"]["文あたりの claim の数(P26)の型ごと"][s]["中央値"], c.style_median_p26(s))
        for d in t["会社"]:
            self.assertEqual(d["claim の数"], {"P22": len(c.claims_of_doc(d["docID"])), "P26": len(c.claims_of_doc(d["docID"]))})
            self.assertEqual((d["片方の profile にしか無い id"], d["値・span・単位が profile 間で違う id"]), ([], []))

    def test_11_read_rows_follow_the_sealed_condition(self):
        self.assertEqual(self.calc.read_rows_by_rule(), self.calc.read_keys)
        self.assertEqual(set((r["docID"], r["id"]) for r in self.calc.readings), self.calc.read_keys)
        self.assertEqual(len(self.calc.readings), len(self.calc.read_keys))
        self.assertEqual(self.recs["tune"]["集計"]["読む行"]["数"], len(self.calc.read_keys))

    def test_16_read_rows_are_exactly_the_p22_value_mismatch_rows_here(self):
        """この標本では読む行の全体が P22 の VALUE_MISMATCH の行と一致する(文書の散文がそう書く。標本が変われば散文も直す)。"""
        p22 = set((c["docID"], c["id"]) for c in self.calc.claims if c["P22"]["state"] == "VALUE_MISMATCH")
        self.assertEqual(self.calc.read_keys, p22)

    def test_12_readings_equal_the_readings_record_own_summary_and_merge_rule(self):
        c, s = self.calc, self.recs["tune_readings"]["集計"]
        for r in c.readings:
            self.assertEqual((r["合わせた"]["側"], r["合わせた"]["細目"]), c.merged(r))
        side = collections.Counter(c.merged(r)[0] for r in c.readings)
        self.assertEqual(s["合わせた側の内訳"], dict((k, side.get(k, 0)) for k in (u"文", u"道具", u"分からない")))
        self.assertEqual(s["2 席の側が一致した行"]["件"], sum(1 for r in c.readings if r["席1"]["側"] == r["席2"]["側"]))
        self.assertEqual(s["合わせた札が文2の行"], measure(c, "r10"))
        det = collections.Counter(c.merged(r)[1] for r in c.readings if c.merged(r)[0] == u"道具" and c.merged(r)[1] != UNSURE)
        self.assertEqual(s["合わせた細目が付いた道具の行"]["細目の内訳"], dict(det))
        self.assertEqual(s["合わせた細目が付いた道具の行"]["行"], sum(det.values()))

    def test_13_inject_equals_the_inject_record_own_summary(self):
        c, s = self.calc, self.recs["tune_inject"]["集計"]
        self.assertEqual(self.recs["tune_inject"]["注入の行の数"], len(c.inj))
        for typ in TYPES:
            self.assertEqual(s[typ]["両方の profile で対応が付く"], len(c.both_mapped(typ)))
            for p in PROFILES:
                for st in STYLES + (None,):
                    d = s[typ][p][st or u"全体"]
                    self.assertEqual(d["対応が付く"], len(c.mapped(typ, p, st)))
                    self.assertEqual(d["注入の行"], len(c.inj_rows(typ, st)))
                    for lab in LABELS:
                        self.assertEqual(d[lab]["件"], c.label_count(typ, p, lab, st), (typ, p, st, lab))

    def test_14_inject_labels_agree_with_states(self):
        for x in self.calc.inj:
            for p in PROFILES:
                r = x[p]
                if not r["対応"]:
                    self.assertIsNone(r["state"])
                    continue
                want = {"GROUNDED": [LABEL_PASS], "VALUE_MISMATCH": [LABEL_NAMED_ORIGINAL, LABEL_NAMED_OTHER],
                        "POINTER_NOT_FOUND": [LABEL_PNF], "UNVERIFIABLE": [LABEL_UNV]}[r["state"]]
                self.assertIn(r["結果"], want)

    def test_15_t8_site_rows_and_r_fields(self):
        i = self.recs["tune_inject"]
        self.assertEqual(i["T8_REL の site"]["注入の行"], i["T8_REL の site"]["作れる site(上限の前)"])
        self.assertEqual(sum(1 for x in self.calc.inj if "r" in x), len(self.calc.inj_rows("T8_REL")))
        self.assertTrue(all(x["r"] in (-0.10, -0.03, 0.03, 0.10) for x in self.calc.inj_rows("T8_REL")))


class TestRPredictions(Base):
    def test_20_prediction_fragments_are_in_the_seal_row_in_order_and_the_bands_parse(self):
        rows = seal_rows(self.seal)
        for rid in R_IDS:
            self.assertIsNotNone(rows[rid], rid)
        sub, summary = r_rows(self.calc, self.seal)                  # 並びの検査は r_rows の中
        self.assertEqual(len(sub), len(PREDICTIONS))
        self.assertEqual(parse_fragment("**40〜100**"), ("range", 40.0, 100.0))
        self.assertEqual(parse_fragment("**≥ 75%**"), ("ge", 75.0, None))
        self.assertEqual(parse_fragment("**≤ 2%**"), ("le", None, 2.0))
        self.assertEqual(parse_fragment("**65% 以上**"), ("ge", 65.0, None))
        self.assertEqual(parse_fragment("35% 以下"), ("le", None, 35.0))

    def test_21_verdict_follows_the_records_not_a_constant(self):
        """記録を変えると当否が変わる(当否の字を定数で持つ実装を弾く)。"""
        base_sub, base_sum = r_rows(self.calc, self.seal)
        r6b = [i for i, p in enumerate(PREDICTIONS) if p[0] == "R-6b"][0]
        self.assertIn(u"外れ", base_sub[r6b])                                 # 実測 8.8% < 10%
        # P22 の VALUE_MISMATCH を足して 10% 以上にすると当たりになる
        recs = copy.deepcopy(self.recs)
        n_flip = 0
        for c in recs["tune"]["claim"]:
            if c["P22"]["state"] != "VALUE_MISMATCH" and n_flip < 10:
                c["P22"]["state"] = "VALUE_MISMATCH"
                n_flip += 1
        sub, _ = r_rows(Calc(recs), self.seal)
        self.assertIn(u"当たり", sub[r6b])
        # 2 席の読みで道具でない行を足すと R-7a が動く
        recs = copy.deepcopy(self.recs)
        moved = 0
        for r in recs["tune_readings"]["行"]:
            if moved < 5 and r["席1"]["側"] == u"道具":
                r["席1"]["側"] = u"文"
                r["席1"]["細目"] = u"文1"
                moved += 1
        c2 = Calc(recs)
        self.assertNotEqual(measure(c2, "r7a"), measure(self.calc, "r7a"))
        self.assertNotEqual(measure(c2, "r9"), measure(self.calc, "r9"))
        # 通した行を名指しに書き換えると R-11 の通した率が動く
        recs = copy.deepcopy(self.recs)
        for x in recs["tune_inject"]["行"]:
            for p in PROFILES:
                if x["型"] == "T8_REL" and x[p]["結果"] == LABEL_PASS:
                    x[p]["結果"] = LABEL_NAMED_OTHER
        c3 = Calc(recs)
        self.assertEqual(measure(c3, "r11g"), 0.0)
        self.assertGreater(measure(self.calc, "r11g"), 2.0)

    def test_22_sub_table_equals_the_doc_and_the_summary_is_the_and_of_the_subitems(self):
        got = doc_blocks(self.doc)
        sub, summary = r_rows(self.calc, self.seal)
        self.assertEqual(got["R-小項目"][2:], sub)
        self.assertEqual(got["R-当否"][2:], summary)
        for line in summary:
            rid, verdict, _miss = [x.strip() for x in line.strip("|").split("|")]
            subs = [l for l in sub if re.match(r"R-\d+", l.strip("| ").split("|")[0].strip()).group(0) == rid]
            self.assertTrue(subs, rid)
            self.assertEqual(verdict == u"当たり", all(l.rstrip(" |").endswith(u"当たり") for l in subs), rid)

    def test_23_the_doc_states_the_verdicts_the_records_give(self):
        """文書の外れ/当たりの字を、記録から計算した当否と別に並べて見る(外れは外れとして残る)。"""
        sub, summary = r_rows(self.calc, self.seal)
        verdict = dict((l.strip("|").split("|")[0].strip(), l.strip("|").split("|")[1].strip()) for l in summary)
        got = doc_blocks(self.doc)["R-当否"][2:]
        gv = dict((l.strip("|").split("|")[0].strip(), l.strip("|").split("|")[1].strip()) for l in got)
        self.assertEqual(gv, verdict)
        for rid in R_IDS:
            self.assertIn(verdict[rid], (u"当たり", u"外れ"))


    def test_24_band_edges_are_inclusive_like_the_seal_words(self):
        """封の幅は『〜』『以上』『≥』『≤』『以下』で端を含む。今の実測は端に無いので、端の入力で直接確かめる(端を外す変異を黙らせない)。"""
        rng = parse_fragment("**40〜100**")
        self.assertTrue(in_band(rng, 40.0) and in_band(rng, 100.0))
        self.assertFalse(in_band(rng, 39.99) or in_band(rng, 100.01))
        ge, le = parse_fragment("**≥ 75%**"), parse_fragment("**≤ 2%**")
        self.assertTrue(in_band(ge, 75.0) and not in_band(ge, 74.99))
        self.assertTrue(in_band(le, 2.0) and not in_band(le, 2.01))
        self.assertFalse(in_band(rng, None))
        self.assertEqual(show_pred(("range", 4.0, 14.0), True), u"4〜14%")
        self.assertEqual(show_pred(("ge", 60.0, None)), u"≥ 60")
        self.assertEqual(show_pred(("le", None, 20.0), True), u"≤ 20%")


class TestRecordContent(Base):
    @staticmethod
    def leak_fns(name, dbm, tm):
        fns = [lambda o: tm.record_key_leaks(o)]
        if name in ("dbfetch", "reports"):                    # 前例の key_leaks を直に当てる(commit の 40 桁を持つ記録には record_key_leaks が免除をつけて当てる)
            fns.append(lambda o: dbm.key_leaks(json.dumps(o, ensure_ascii=False)))
        return fns

    @classmethod
    def setUpClass(cls):
        Base.setUpClass.__func__(cls)
        cls.tm = _load_module(SCRIPT_REL, "p27_tune_for_result_gate")
        cls.dbm = _load_module(DBFETCH_SCRIPT_REL, "p27_dbfetch_for_result_gate")

    def test_30_real_records_pass_every_content_check(self):
        for name, obj in self.recs.items():
            self.assertEqual(record_problems(name, obj, key_leak_fns=self.leak_fns(name, self.dbm, self.tm)), [], name)

    def test_31_allowed_lists_cover_all_five_records_and_every_node_has_a_gloss(self):
        self.assertEqual(sorted(ALLOWED), sorted(RECORD_REL))
        self.assertEqual(sorted(JP_DIGEST), sorted(RECORD_REL))
        for name in ALLOWED:
            out, req = set(), set()
            _static_paths(ALLOWED[name], "", out, req)               # 欄ごとの説明(gloss)が空なら assert で落ちる
            self.assertTrue(req <= out)

    def test_32_forbidden_names_are_absent_from_every_record(self):
        for name, obj in self.recs.items():
            bad = []
            _forbidden_name_problems(obj, "", bad)
            self.assertEqual(bad, [], name)
            names = set(keys_of(obj))
            for f in (u"span", u"subject", u"value", u"recomputed", u"道5の形", u"本文", u"抜粋"):
                self.assertNotIn(f, names, (name, f))

    def test_33_key_leaks_are_empty_for_the_precedent_checker_and_the_tune_checker(self):
        for name, obj in self.recs.items():
            self.assertEqual(self.tm.record_key_leaks(obj), [], name)
            if name in ("dbfetch", "reports"):
                self.assertEqual(self.dbm.key_leaks(json.dumps(obj, ensure_ascii=False)), [], name)
        # 検査器そのものが鍵の形の字に反応する(反応しない検査器を門と呼ばない)
        self.assertTrue(self.tm.record_key_leaks({"x": "Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0xR"}))
        self.assertTrue(self.dbm.key_leaks("Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0xR"))

    def test_34_W_record_is_the_same_as_the_blob_of_commit_W(self):
        rel = RECORD_REL["reports"]
        rc = git("rev-parse", "--verify", W_COMMIT + "^{commit}")
        self.assertEqual(rc.returncode, 0, u"W の commit が読めない")
        # W の commit は、この記録を最初に足した commit(評価用の凍結)であること
        added = [c for c in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.decode("utf-8").split() if c]
        self.assertTrue(added, u"W の記録が追跡されていない")
        self.assertEqual(added[-1], rc.stdout.decode("utf-8").strip())
        blob = git("show", "%s:./%s" % (W_COMMIT, rel))
        self.assertEqual(blob.returncode, 0, blob.stderr)
        w = json.loads(blob.stdout.decode("utf-8"))
        now = self.recs["reports"]
        self.assertEqual(len(w["会社"]), 20)
        w_rows = dict((c["docID"], (c["区分"], c["型"], c["文の sha256"])) for c in w["会社"])
        now_rows = dict((c["docID"], (c["区分"], c["型"], c["文の sha256"])) for c in now["会社"])
        self.assertEqual(now_rows, w_rows)
        self.assertEqual(sum(1 for v in w_rows.values() if v[0] == u"評価用"), 10)
        # file 全体も W の blob と同じ(W の後に書き換えられていない)
        self.assertEqual(sha256_hex(blob.stdout), sha256_hex(read_bytes(rel)))

    def test_35_the_tune_docs_of_the_three_records_equal_the_tuning_list_of_W(self):
        tune_w = [c["docID"] for c in self.recs["reports"]["会社"] if c["区分"] == u"調整用"]
        self.assertEqual(sorted(self.calc.docs), sorted(tune_w))
        for k in ("tune", "tune_inject", "tune_readings"):
            self.assertEqual(sorted(self.recs[k]["対象の docID"]), sorted(tune_w), k)
        sh = dict((c["docID"], c["文の sha256"]) for c in self.recs["reports"]["会社"])
        for k in ("tune", "tune_inject", "tune_readings"):
            self.assertEqual(self.recs[k]["使った文の sha256"], dict((d, sh[d]) for d in tune_w), k)

    def test_36_fakes_turn_the_checks_red(self):
        """(e) 偽の会社名・偽の抜粋の 1 文を足した写しで、検査が赤になる。足す前の写しは緑。"""
        FAKE_NAME = u"架空商事株式会社"
        FAKE_EXCERPT = u"当社の売上高は架空の数字で前期比を大きく伸ばした。"
        fns = lambda n: self.leak_fns(n, self.dbm, self.tm)                       # noqa: E731
        for name, obj in self.recs.items():
            self.assertEqual(record_problems(name, copy.deepcopy(obj), key_leak_fns=fns(name)), [], name)
            fakes = []
            a = copy.deepcopy(obj)
            a[u"会社名"] = FAKE_NAME                                              # 偽の欄
            fakes.append(("新しい欄 会社名", a))
            a = copy.deepcopy(obj)
            a[u"限界を足した"] = [FAKE_EXCERPT]                                    # 偽の抜粋(新しい欄)
            fakes.append(("新しい欄 抜粋の 1 文", a))
            a = copy.deepcopy(obj)
            first_list = [k for k, v in a.items() if isinstance(v, list) and v and isinstance(v[0], str)]
            if first_list:
                a[first_list[0]].append(FAKE_NAME)                                # 既存の欄の列に偽の会社名
                fakes.append(("既存の列に偽の会社名", a))
            a = copy.deepcopy(obj)
            a["step"] = a["step"] + FAKE_EXCERPT                                  # 既存の欄の文に偽の抜粋
            fakes.append(("既存の文に偽の抜粋", a))
            a = copy.deepcopy(obj)
            a["seal"] = u"Acme Holdings Ltd"                                      # 日本語でない偽の会社名
            fakes.append(("英字の偽の会社名", a))
            a = copy.deepcopy(obj)
            a["seal"] = u"Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0xR"                       # 鍵の形の字
            fakes.append(("鍵の形の字", a))
            for label, bad in fakes:
                self.assertTrue(record_problems(name, bad, key_leak_fns=fns(name)), (name, label))
        # 禁止の名前を既存の入れ子に足す(木の許可と別に、名前の検査でも赤)
        a = copy.deepcopy(self.recs["tune"])
        a["claim"][0]["P26"]["span"] = FAKE_EXCERPT
        bad = []
        _forbidden_name_problems(a, "", bad)
        self.assertTrue(bad)
        a = copy.deepcopy(self.recs["tune_readings"])
        a["行"][0][u"理由"] = FAKE_EXCERPT
        a["行"][0][u"道5の形"] = FAKE_NAME
        bad = []
        _forbidden_name_problems(a, "", bad)
        self.assertEqual(len(bad), 2)

    def test_37_a_missing_allowed_field_and_a_changed_jp_string_are_caught(self):
        for name, obj in self.recs.items():
            a = copy.deepcopy(obj)
            del a["seal"]
            self.assertTrue([p for p in record_problems(name, a) if u"記録に無い欄" in p], name)
            a = copy.deepcopy(obj)
            a["step"] = a["step"] + u"。"
            self.assertTrue([p for p in record_problems(name, a) if u"指紋" in p], name)

    def test_38_W_blob_check_notices_a_changed_sha(self):
        """W の記録の sha256 を 1 字変えた写しは、W の blob の行と一致しない(比較の関数そのものを確かめる)。"""
        rel = RECORD_REL["reports"]
        blob = git("show", "%s:./%s" % (W_COMMIT, rel)).stdout
        w = json.loads(blob.decode("utf-8"))
        now = copy.deepcopy(self.recs["reports"])
        s = now["会社"][-1]["文の sha256"]
        now["会社"][-1]["文の sha256"] = s[:-1] + ("0" if s[-1] != "0" else "1")
        w_rows = dict((c["docID"], c["文の sha256"]) for c in w["会社"])
        now_rows = dict((c["docID"], c["文の sha256"]) for c in now["会社"])
        self.assertNotEqual(now_rows, w_rows)


    def test_39_each_layer_catches_what_the_others_do_not(self):
        """(a) 欄の木・日本語の指紋・日本語でない値の形・鍵の検査は、それぞれ他が見逃す偽を単独で止める(層を 1 つ外しても他の層が覆わない)。"""
        fns = lambda n: self.leak_fns(n, self.dbm, self.tm)                       # noqa: E731
        for name, obj in self.recs.items():
            # (a) 日本語でない・符号の形の値の新しい欄: 欄の木だけが止める
            a = copy.deepcopy(obj)
            a["extra_field"] = "x1"
            p = record_problems(name, a, key_leak_fns=fns(name))
            self.assertEqual([x for x in p if u"許可の一覧に無い" in x], [u"欄が許可の一覧に無い: /extra_field"], name)
            self.assertEqual([x for x in p if u"許可の一覧に無い" not in x], [], name)
            # 日本語の指紋: 既存の欄の文を書き換える(欄の名前も値の形も変わらない)
            a = copy.deepcopy(obj)
            a["step"] = a["step"].replace(u"P27", u"P28")
            p = record_problems(name, a, key_leak_fns=fns(name))
            self.assertEqual(len(p), 1, (name, p))
            self.assertIn(u"指紋", p[0])
            # 日本語でない値の形: 空白を含む英字の値(欄は既存・日本語でない・鍵の形でない)
            a = copy.deepcopy(obj)
            a["seal"] = u"Acme Holdings Ltd"
            p = record_problems(name, a, key_leak_fns=fns(name))
            self.assertEqual(len(p), 1, (name, p))
            self.assertIn(u"許可の形でない", p[0])
            # 鍵の形: 単語の形(日本語でない値の形の検査は通る)だが鍵の検査が止める
            a = copy.deepcopy(obj)
            a["seal"] = u"Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0xR"
            p = record_problems(name, a, key_leak_fns=fns(name))
            self.assertTrue(p and all(u"鍵らしい字" in x for x in p), (name, p))               # 鍵の検査器(2 つ在る記録は 2 つとも)だけが止める


if __name__ == "__main__":
    unittest.main()
