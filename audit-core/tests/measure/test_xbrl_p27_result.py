# -*- coding: utf-8 -*-
"""封 docs/XBRL_P27_SEAL_2026-10-27.md §3-2(V-1〜V-7)・§3-3(N-1〜N-3)・§4(K-1〜K-5 と 3 つの判定の字)・§7 末尾・§9-4 後半 ― P27 段 2 の**結果の門**
(結果文書 docs/XBRL_P27_RESULT_2026-10-27.md を縛る)。

**この門が縛るもの**(数は字で留めず、記録から計算する。幅・閾値は封の文書の太字から読む)

1. 結果文書の数。文書の ``<!-- 門:start 名前 -->`` 〜 ``<!-- 門:end -->`` の間の表は、記録(評価用の 3 つと E の 3 つ・W の記録)から**ここで作り直した表と 1 行も違わない**。
   記録の自前の集計(script が書いた欄)とも別実装で照らす。門の外の散文は数を持たない(持つ行には【門なし】の印)。
2. V-1〜V-7・N-1〜N-3・K-1〜K-5 の実測(記録の**行**から数える)・封の幅との当否・採用の判定(P27E を採用する/しない・P27 を既定の候補として記録する/しない)。
   判定の字は記録から求めた判定と一致しなければ赤(定数でない)。
3. 独立監査の推奨 (i)〜(v): (i) 記録の script の sha256 = いまの script = HEAD の script、engine の指紋 = E の engine(git の blob から求め直す)、
   (ii) 対象 = W の記録の区分が評価用の 10 件の全部、(iii) 束の定数 3 つ = 記録の欄 = script の定数、
   (iv) K-3・K-4 の「合わせた側が道具」を細目が割れた行(側は道具・細目は分からない)を含めて数える、(v) V-5 を P27 で(P27E でなく)数える。
4. 記録 3 つの中身: (a) 欄の名前の木が許可の一覧と一致 (b) span・subject・value・recomputed・理由・道5の形・本文・抜粋の欄が無い (c) ``key_leaks`` が空
   (d) W の記録が W の blob と同じ (e) 偽の会社名・偽の抜粋を足した写しで赤。

文の字・DB の値・理由の字は、この file にも文書にも書かない(読むのは repo の記録と封の文書だけ。評価用の文・DB の応答・束・理由は開かない)。
この file は docID の字を持たない(docID は W の記録から読む)。結果文書は評価用の docID を名指すので LATER_NAMING_FILES に宣言済み。
"""
import collections
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
for _p in (ROOT, os.path.join(ROOT, "core", "py")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SEAL_REL = "docs/XBRL_P27_SEAL_2026-10-27.md"
DEFAULT_P27_SEAL_REL = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"       # 2026-10-28: 既定を P26 -> P27 に切り替える 段 2 の封(下の test_61・test_65 の遷移)
DEFAULT_P27_FP_TO = "92326a0f4dcefd21fae4393a611e4206ef174b19258ddadd0213117191e7b399"
# 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。動いてよい engine の file は上の 2 file に report_customer.py を足した 3 file で、
# 作業木の指紋が下の値のときに限る。上の DEFAULT_P27_FP_TO(既定を P27 に切り替える 段 2 の後の値)は測った時点の値として残す。
CAND_SEAL_REL = "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"
CAND_FP_TO = "dc7e35fbfb0f56ca6410bb7bfa8b8a366cc3ec19d6614c4cb866400cd9994ff6"
DOC_REL = "docs/XBRL_P27_RESULT_2026-10-27.md"
EVAL_REC_REL = collections.OrderedDict([
    ("eval", "fixtures/xbrl/p27/eval_2026-10-27.json"),
    ("eval_inject", "fixtures/xbrl/p27/eval_inject_2026-10-27.json"),
    ("eval_readings", "fixtures/xbrl/p27/eval_readings_2026-10-27.json"),
])
E_REC_REL = collections.OrderedDict([
    ("regress97", "fixtures/xbrl/p27/regress97_2026-10-27.json"),
    ("tune_p27", "fixtures/xbrl/p27/tune_p27_2026-10-27.json"),
    ("tune_p27_inject", "fixtures/xbrl/p27/tune_p27_inject_2026-10-27.json"),
])
W_REC_REL = "fixtures/xbrl/p27/reports_2026-10-27.json"
DOC_SHA_REL = collections.OrderedDict(list(EVAL_REC_REL.items()) + list(E_REC_REL.items()) + [("reports", W_REC_REL)])
EVAL_SCRIPT_REL = "measure/xbrl_p27_eval_2026-10-27.py"
TUNE_SCRIPT_REL = "measure/xbrl_p27_tune_2026-10-27.py"
REGRESS_SCRIPT_REL = "measure/xbrl_p27_regress97_2026-10-27.py"
PRECEDENT_GATE_REL = "tests/measure/test_xbrl_p27_tune_result.py"
ENGINE_DIRS = ("audit-core/adapters/xbrl", "audit-core/core/py/audit_core")        # git の path(REPO から)
ENGINE_TREES = ("audit-core/adapters", "audit-core/core")

P4 = ("P22", "P26", "P27", "P27E")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
STYLES = ("A", "B", "C")
TYPES = ("T1_VALUE", "T8_REL")
LABEL_PASS = u"通した"
LABEL_NAMED_ORIGINAL = u"名指して原本の値を返した"
LABEL_NAMED_OTHER = u"名指したが別の値"
LABEL_PNF = u"止めたが名指さない(POINTER_NOT_FOUND)"
LABEL_UNV = u"止めたが名指さない(UNVERIFIABLE)"
LABELS = (LABEL_PASS, LABEL_NAMED_ORIGINAL, LABEL_NAMED_OTHER, LABEL_PNF, LABEL_UNV)
SIDE_TOOL = u"道具"
SIDE_SENT = u"文"
UNSURE = u"分からない"
NO_SAME_VALUE = "no_same_value"
OTHER_CONCEPT = "other_concept"
POP67 = u"手元の 67"
POP30 = u"新しい標本 30"
COND_K3 = "P27E_VALUE_MISMATCH_and_P26_not_VALUE_MISMATCH"
COND_K4 = "P26_GROUNDED_and_P27_not_GROUNDED"


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


def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# ======================================================================================================
# 封の文書から幅・閾値を読む(字で留めない)
def seal_row_tokens(seal_text, rid):
    """封の表の行 ``| **<rid>** | 予測 | 外れ方 |`` の予測の欄の太字(``**x**``)を出現順に返す。"""
    m = re.search(r"^\| \*\*%s\*\* \|(.*)$" % re.escape(rid), seal_text, re.M)
    assert m, rid
    cells = [c for c in m.group(1).split("|")]
    return re.findall(r"\*\*([^*]+)\*\*", cells[0])


def seal_k_tokens(seal_text, kid):
    """封 §4 の箇条書き ``- **K-n(…)**: …`` の太字を、見出し(最初の太字)を除いて出現順に返す。"""
    m = re.search(r"^- \*\*%s\([^)]*\)\*\*:(.*)$" % re.escape(kid), seal_text, re.M)
    assert m, kid
    return re.findall(r"\*\*([^*]+)\*\*", m.group(1))


NUM = r"(\d+(?:\.\d+)?)"


def parse_token(tok):
    """封の太字 -> ('range', lo, hi) / ('ge', x) / ('le', x) / ('eq', x) / ('le_ref', delta) / ('ratio', a, b)。値は Fraction(区間は両端を含む)。"""
    t = tok.replace(",", "").strip()
    m = re.fullmatch(NUM + u"〜" + NUM + u"\\s*(?:%|行)?", t)
    if m:
        return ("range", Fraction(m.group(1)), Fraction(m.group(2)))
    m = re.fullmatch(u"≥ " + NUM + u"\\s*(?:%|ポイント)?", t)
    if m:
        return ("ge", Fraction(m.group(1)))
    m = re.fullmatch(u"≤ " + NUM + u"\\s*(?:%|ポイント)?", t)
    if m:
        return ("le", Fraction(m.group(1)))
    m = re.fullmatch(u"≤ P26 の率 \\+ " + NUM + u" ポイント", t)
    if m:
        return ("le_ref", Fraction(m.group(1)))
    m = re.fullmatch(NUM + u" / " + NUM, t)
    if m:
        return ("ratio", Fraction(m.group(1)), Fraction(m.group(2)))
    m = re.fullmatch(NUM, t)
    if m:
        return ("eq", Fraction(m.group(1)))
    raise AssertionError(u"封の字の幅を読めない: %r" % tok)


def in_band(parsed, x):
    """x は Fraction か int(le_ref のときは『P27E の率 − P26 の率』のポイント差)。ratio のときは (a, b) の組。"""
    if x is None:
        return False
    kind = parsed[0]
    if kind == "ratio":
        return Fraction(x[0]) == parsed[1] and Fraction(x[1]) == parsed[2]
    x = Fraction(x)
    if kind == "range":
        return parsed[1] <= x <= parsed[2]
    if kind == "ge":
        return x >= parsed[1]
    if kind in ("le", "le_ref"):
        return x <= parsed[1]
    return x == parsed[1]


def fnum(x):
    x = Fraction(x)
    return u"{:,}".format(int(x)) if x.denominator == 1 else u"%.1f" % float(x)


def pct(a, b):
    """% の厳密値(Fraction)。分母 0 は None。"""
    return None if not b else Fraction(100 * a, b)


def show_pct(x):
    return u"—" if x is None else u"%.1f%%" % float(x)


def ab(a, b):
    return u"%d/%d(%s)" % (a, b, show_pct(pct(a, b)))


def bold_text(tok):
    return tok


# ======================================================================================================
# 計算(評価用の 3 つの記録の**行**から数え直す。記録の自前の集計は見ない)
class Calc(object):
    def __init__(self, recs):
        self.recs = recs
        e, i, r = recs["eval"], recs["eval_inject"], recs["eval_readings"]
        self.docs = [c["docID"] for c in e["会社"]]
        self.style = dict((c["docID"], c["型"]) for c in e["会社"])
        self.prov = dict((c["docID"], c["規則ごと(build_raw_claims の provenance)"]) for c in e["会社"])
        self.claims = e["claim"]
        self.by_key = dict(((c["docID"], c["id"]), c) for c in self.claims)
        self.readings = r["行"]
        self.read_by_key = dict(((x["docID"], x["id"]), x) for x in self.readings)
        self.inj = i["行"]

    # ---- 判定
    def st(self, key, p):
        return self.by_key[key][p]["state"]

    def state_counts(self, p, docs=None):
        c = collections.Counter(x[p]["state"] for x in self.claims if docs is None or x["docID"] in docs)
        return dict((s, c.get(s, 0)) for s in STATES)

    def vm(self, p):
        return self.state_counts(p)["VALUE_MISMATCH"]

    def keys_where(self, pred):
        return set(k for k in self.by_key if pred(k))

    # 読む行の条件(封 §7)。K-3 の行 = P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない。K-4 の行 = P26 で GROUNDED かつ P27E で GROUNDED でない。
    def k3_keys(self):
        return self.keys_where(lambda k: self.st(k, "P27E") == "VALUE_MISMATCH" and self.st(k, "P26") != "VALUE_MISMATCH")

    def k4_keys(self, p="P27E"):
        return self.keys_where(lambda k: self.st(k, "P26") == "GROUNDED" and self.st(k, p) != "GROUNDED")

    def sealed_read_keys(self):
        """封 §7: (P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない)∪(P26 で GROUNDED かつ P27 で GROUNDED でない)。"""
        return self.k3_keys() | self.k4_keys("P27")

    # ---- 読み(席の合わせ方: 側が割れたら分からない。側が同じなら細目が同じときだけ細目を残す)
    @staticmethod
    def side_of(row):
        a, b = row["席1"]["側"], row["席2"]["側"]
        return a if a == b else UNSURE

    @staticmethod
    def merged(row):
        a, b = (row["席1"]["側"], row["席1"]["細目"]), (row["席2"]["側"], row["席2"]["細目"])
        if a[0] != b[0] or a[0] == UNSURE:
            return UNSURE, None
        return a[0], (a[1] if a[1] == b[1] else UNSURE)

    def tool_rows(self, keys):
        """keys のうち、2 席の側が一致して道具の行(細目が割れた行 = 側は道具・細目は分からない を含む)。読んでいない行は数えない。"""
        return [k for k in sorted(keys) if k in self.read_by_key and self.side_of(self.read_by_key[k]) == SIDE_TOOL]

    # ---- 注入
    def inj_rows(self, typ, style=None):
        return [x for x in self.inj if x["型"] == typ and (style is None or x["文体"] == style)]

    def all_mapped(self, typ, style=None):
        """封 §3-2 の分母: 4 profile の全部で対応が付く注入の行。"""
        return [x for x in self.inj_rows(typ, style) if all(x[p]["対応"] for p in P4)]

    def mapped(self, typ, p, style=None):
        """各 profile の分母: その profile で対応が付く注入の行。"""
        return [x for x in self.inj_rows(typ, style) if x[p]["対応"]]

    @staticmethod
    def count(rows, p, label):
        return sum(1 for x in rows if x[p]["結果"] == label)


# ======================================================================================================
# 97 書類の記録(N-1〜N-3)。E の門とは別に書く(動いた行の列から数える)
class Regress(object):
    def __init__(self, rec):
        self.rec = rec
        docs = rec[u"書類"]
        self.n_docs = len(docs)
        key_out = u"出力の sha256(engine の欄を除く)"
        key_cmp = u"比べる側の engine の出力の sha256"
        self.same = dict((p, sum(1 for d in docs if d[key_out][p] == d[key_cmp][p])) for p in ("P22", "P26"))
        self.pop = {}
        for pop in (POP67, POP30):
            rows = [d for d in docs if d[u"標本"] == pop]
            st = dict((p, collections.Counter()) for p in ("P26", "P27", "P27E"))
            for d in rows:
                for p in st:
                    st[p].update(d[u"4 state"][p])
            a = rec[u"動いた行"][pop][u"P26 → P27"]
            b = rec[u"動いた行"][pop][u"P27 → P27E"]
            a_state = [m for m in a if m[u"前"][u"state"] != m[u"後"][u"state"]]
            a_between = [m for m in a_state if set((m[u"前"][u"state"], m[u"後"][u"state"])) == set(("UNVERIFIABLE", "POINTER_NOT_FOUND"))]
            b_vm = [m for m in b if (m[u"前"][u"state"], m[u"前"][u"reason"], m[u"後"][u"state"]) == ("POINTER_NOT_FOUND", NO_SAME_VALUE, "VALUE_MISMATCH")]
            b_oc = [m for m in b if (m[u"前"][u"state"], m[u"前"][u"reason"], m[u"後"][u"state"], m[u"後"][u"reason"]) ==
                    ("POINTER_NOT_FOUND", NO_SAME_VALUE, "POINTER_NOT_FOUND", OTHER_CONCEPT)]
            self.pop[pop] = {
                "docs": len(rows), "state": dict((p, dict(st[p])) for p in st),
                "a_state_moved": len(a_state), "a_other_dir": len(a_state) - len(a_between),
                "a_ptr_only_grounded": sum(1 for m in a if m[u"前"][u"state"] == "GROUNDED" == m[u"後"][u"state"] and m[u"pointer だけ替わった"]),
                "a_to_vm": sum(1 for m in a if m[u"後"][u"state"] == "VALUE_MISMATCH" != m[u"前"][u"state"]),
                "a_new_g": sum(1 for m in a if m[u"後"][u"state"] == "GROUNDED" != m[u"前"][u"state"]),
                "b_to_vm": len(b_vm), "b_other_dir": len(b) - len(b_vm) - len(b_oc),
                "b_touch_g": sum(1 for m in b if "GROUNDED" in (m[u"前"][u"state"], m[u"後"][u"state"])),
            }


# ======================================================================================================
# 封の項目(小項目 -> 見るもの・封の行・太字の位置・実測の関数)
#: (小項目, 見るもの, 封の行, 太字の位置, 実測の名前)
V_ITEMS = [
    ("V-1a", u"T8_REL: 通した率 P22", "V-1", 0, "v1a"), ("V-1b", u"T8_REL: 通した率 P26", "V-1", 0, "v1b"),
    ("V-1c", u"T8_REL: 通した率 P27", "V-1", 1, "v1c"), ("V-1d", u"T8_REL: 通した率 P27E", "V-1", 1, "v1d"),
    ("V-2a", u"T8_REL: 名指して原本の値を返した率 P22", "V-2", 0, "v2a"), ("V-2b", u"T8_REL: 名指して原本の値を返した率 P26", "V-2", 1, "v2b"),
    ("V-2c", u"T8_REL: 名指して原本の値を返した率 P27", "V-2", 2, "v2c"), ("V-2d", u"T8_REL: 名指して原本の値を返した率 P27E", "V-2", 3, "v2d"),
    ("V-3a", u"T1_VALUE: 通した行 P22", "V-3", 0, "v3a"), ("V-3b", u"T1_VALUE: 通した行 P26", "V-3", 0, "v3b"),
    ("V-3c", u"T1_VALUE: 通した行 P27", "V-3", 0, "v3c"), ("V-3d", u"T1_VALUE: 通した行 P27E", "V-3", 0, "v3d"),
    ("V-3e", u"T1_VALUE: 名指して原本の値を返した率 P27E", "V-3", 1, "v3e"),
    ("V-4a", u"無改変の VALUE_MISMATCH の率 P22", "V-4", 0, "v4a"), ("V-4b", u"無改変の VALUE_MISMATCH の率 P26", "V-4", 1, "v4b"),
    ("V-4c", u"無改変の VALUE_MISMATCH の率 P27", "V-4", 2, "v4c"), ("V-4d", u"P27E − P27 の VALUE_MISMATCH の行の差", "V-4", 3, "v4d"),
    ("V-5a", u"P26 → P27 で GROUNDED を離れる行(P27 で数える)", "V-5", 0, "v5a"), ("V-5b", u"P26 → P27 で新しい GROUNDED(P27 で数える)", "V-5", 1, "v5b"),
    ("V-6a", u"C2 で止めた claim(P27 の provenance)", "V-6", 0, "v6a"), ("V-6b", u"C3 で target_or_plan にした claim(P27 の provenance)", "V-6", 1, "v6b"),
    ("V-6c", u"C1 で other_concept になった行(P27 の provenance)", "V-6", 2, "v6c"), ("V-6d", u"B で名指した行(P27E の無改変の provenance)", "V-6", 3, "v6d"),
    ("V-7a", u"読む行の数", "V-7", 0, "v7a"), ("V-7b", u"読む行のうち合わせた側が道具の行", "V-7", 1, "v7b"),
]
V_IDS = ("V-1", "V-2", "V-3", "V-4", "V-5", "V-6", "V-7")
#: P27E を採用する条件(封 §4)
K_ITEMS = [
    ("K-1a", u"T8_REL の通した率 P27E", "K-1", 0, "k1a"), ("K-1b", u"T1_VALUE の通した行 P27E", "K-1", 1, "k1b"),
    ("K-2a", u"T8_REL の名指して原本の値を返した率 P27E", "K-2", 0, "k2a"), ("K-2b", u"同じ率の P26 との差(ポイント)", "K-2", 1, "k2b"),
    ("K-3a", u"P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない行のうち合わせた側が道具の行", "K-3", 0, "k3a"),
    ("K-3b", u"P27E の VALUE_MISMATCH の率 − P26 の率(ポイント)", "K-3", 1, "k3b"),
    ("K-4", u"P26 で GROUNDED かつ P27E で GROUNDED でない行のうち合わせた側が道具の行", "K-4", 0, "k4"),
    ("K-5", u"97 書類のうち旗が偽の P22・P26 が封の時点の engine と byte 一致した書類(§5 の N-1)", "N-1", 0, "k5"),
]
K_IDS = ("K-1", "K-2", "K-3", "K-4", "K-5")
#: P27 を既定の候補として記録する条件(封 §4: K-1・K-4・K-5 を P27 で満たし、K-3 の代わりに VALUE_MISMATCH の行 ≤ P26 の行と N-2 の 4 つの数)
D_ITEMS = [
    ("D-1a", u"T8_REL の通した率 P27(K-1)", "K-1", 0, "d1a"), ("D-1b", u"T1_VALUE の通した行 P27(K-1)", "K-1", 1, "d1b"),
    ("D-3", u"無改変の VALUE_MISMATCH の行 P27 − P26(K-3 の代わり。≤ 0)", None, None, "d3"),
    ("D-4", u"P26 で GROUNDED かつ P27 で GROUNDED でない行のうち合わせた側が道具の行(K-4)", "K-4", 0, "d4"),
    ("D-5", u"97 書類のうち旗が偽の P22・P26 が byte 一致した書類(K-5 = N-1)", "N-1", 0, "k5"),
    ("D-N2a", u"手元の 67 の P27 の GROUNDED が P26 と封の数に同じ(N-2)", "N-2", 0, "dn2a"),
    ("D-N2b", u"手元の 67 の P27 の VALUE_MISMATCH が P26 と封の数に同じ(N-2)", "N-2", 1, "dn2b"),
    ("D-N2c", u"新しい標本 30 の P27 の GROUNDED が P26 と封の数に同じ(N-2)", "N-2", 2, "dn2c"),
    ("D-N2d", u"新しい標本 30 の P27 の VALUE_MISMATCH が P26 と封の数に同じ(N-2)", "N-2", 3, "dn2d"),
]
N_ITEMS = [
    ("N-1a", u"旗が偽の P22: byte が同じ書類 / 書類", "N-1", 0, "n1a"), ("N-1b", u"旗が偽の P26: byte が同じ書類 / 書類", "N-1", 0, "n1b"),
    ("N-2a", u"手元の 67: P27 の GROUNDED", "N-2", 0, "n2a"), ("N-2b", u"手元の 67: P27 の VALUE_MISMATCH", "N-2", 1, "n2b"),
    ("N-2c", u"新しい標本 30: P27 の GROUNDED", "N-2", 2, "n2c"), ("N-2d", u"新しい標本 30: P27 の VALUE_MISMATCH", "N-2", 3, "n2d"),
    ("N-2e", u"手元の 67: GROUNDED のまま pointer が替わる行", "N-2", 4, "n2e"), ("N-2f", u"新しい標本 30: GROUNDED のまま pointer が替わる行", "N-2", 4, "n2f"),
    ("N-2g", u"手元の 67: 動いた行(UNVERIFIABLE と POINTER_NOT_FOUND の間)", "N-2", 5, "n2g"),
    ("N-2h", u"新しい標本 30: 動いた行(UNVERIFIABLE と POINTER_NOT_FOUND の間)", "N-2", 6, "n2h"),
    ("N-2i", u"他の向きに動いた行(67 + 30)・VALUE_MISMATCH に入る行・新しい GROUNDED(基準は全部 0。封 §5)", None, None, "n2i"),
    ("N-3a", u"P27E の GROUNDED が P27 と同じ(67 と 30 の両方)・GROUNDED が動いた行 0", None, None, "n3a"),
    ("N-3b", u"他の向きの行(67 + 30)", None, None, "n3b"),
    ("N-3c", u"手元の 67: VALUE_MISMATCH に入る行", "N-3", 0, "n3c"), ("N-3d", u"新しい標本 30: VALUE_MISMATCH に入る行", "N-3", 1, "n3d"),
]
N_IDS = ("N-1", "N-2", "N-3")


class Measures(object):
    """V・K・D・N の実測。値は Fraction か整数(le_ref の K-3b はポイント差)。"""

    def __init__(self, calc, regress, seal_text):
        self.c = calc
        self.r = regress
        self.seal = seal_text

    # ---- V-1〜V-3(封の分母 = 4 profile の全部で対応が付く行)
    def _rate(self, typ, p, label):
        rows = self.c.all_mapped(typ)
        return pct(self.c.count(rows, p, label), len(rows))

    def v1a(self): return self._rate("T8_REL", "P22", LABEL_PASS)
    def v1b(self): return self._rate("T8_REL", "P26", LABEL_PASS)
    def v1c(self): return self._rate("T8_REL", "P27", LABEL_PASS)
    def v1d(self): return self._rate("T8_REL", "P27E", LABEL_PASS)
    def v2a(self): return self._rate("T8_REL", "P22", LABEL_NAMED_ORIGINAL)
    def v2b(self): return self._rate("T8_REL", "P26", LABEL_NAMED_ORIGINAL)
    def v2c(self): return self._rate("T8_REL", "P27", LABEL_NAMED_ORIGINAL)
    def v2d(self): return self._rate("T8_REL", "P27E", LABEL_NAMED_ORIGINAL)

    def _t1_pass(self, p):
        return self.c.count(self.c.all_mapped("T1_VALUE"), p, LABEL_PASS)

    def v3a(self): return self._t1_pass("P22")
    def v3b(self): return self._t1_pass("P26")
    def v3c(self): return self._t1_pass("P27")
    def v3d(self): return self._t1_pass("P27E")
    def v3e(self): return self._rate("T1_VALUE", "P27E", LABEL_NAMED_ORIGINAL)

    # ---- V-4・V-5(無改変の claim。分母は claim の数)
    def _vm_rate(self, p):
        return pct(self.c.vm(p), len(self.c.claims))

    def v4a(self): return self._vm_rate("P22")
    def v4b(self): return self._vm_rate("P26")
    def v4c(self): return self._vm_rate("P27")
    def v4d(self): return self.c.vm("P27E") - self.c.vm("P27")

    def v5a(self):                                          # (v) P27 で数える(P27E でなく)
        return len(self.c.k4_keys("P27"))

    def v5b(self):
        return len(self.c.keys_where(lambda k: self.c.st(k, "P27") == "GROUNDED" and self.c.st(k, "P26") != "GROUNDED"))

    # ---- V-6(provenance。会社ごとの欄の和)
    def _prov(self, p, key):
        return sum(v[p][key] for v in self.c.prov.values())

    def v6a(self): return self._prov("P27", "C2 per_unit_counter")
    def v6b(self): return self._prov("P27", "C3 future_period")
    def v6c(self): return self._prov("P27", u"C1 の窓に入って other_concept になった claim")
    def v6d(self): return self._prov("P27E", "B relative_within_rho")

    # ---- V-7
    def v7a(self): return len(self.c.readings)

    def v7b(self):
        return sum(1 for x in self.c.readings if self.c.side_of(x) == SIDE_TOOL)

    # ---- K(P27E を採用する条件)
    def k1a(self): return self._rate("T8_REL", "P27E", LABEL_PASS)
    def k1b(self): return self._t1_pass("P27E")
    def k2a(self): return self._rate("T8_REL", "P27E", LABEL_NAMED_ORIGINAL)

    def k2b(self):
        a, b = self.k2a(), self._rate("T8_REL", "P26", LABEL_NAMED_ORIGINAL)
        return None if a is None or b is None else a - b

    def k3a(self): return len(self.c.tool_rows(self.c.k3_keys()))

    def k3b(self):
        a, b = self._vm_rate("P27E"), self._vm_rate("P26")
        return None if a is None or b is None else a - b

    def k4(self): return len(self.c.tool_rows(self.c.k4_keys("P27E")))
    def k5(self): return (min(self.r.same["P22"], self.r.same["P26"]), self.r.n_docs) if self.r.same["P22"] == self.r.same["P26"] else (-1, self.r.n_docs)

    # ---- D(P27 を既定の候補として記録する条件)
    def d1a(self): return self._rate("T8_REL", "P27", LABEL_PASS)
    def d1b(self): return self._t1_pass("P27")
    def d3(self): return self.c.vm("P27") - self.c.vm("P26")
    def d4(self): return len(self.c.tool_rows(self.c.k4_keys("P27")))

    def _dn2(self, pop, state):
        """P27 の 4 state の数が P26 の数と同じなら、その数を返す(封の数との照合は in_band が行う)。違えば -1。"""
        p27, p26 = self.r.pop[pop]["state"]["P27"][state], self.r.pop[pop]["state"]["P26"][state]
        return p27 if p27 == p26 else -1

    def dn2a(self): return self._dn2(POP67, "GROUNDED")
    def dn2b(self): return self._dn2(POP67, "VALUE_MISMATCH")
    def dn2c(self): return self._dn2(POP30, "GROUNDED")
    def dn2d(self): return self._dn2(POP30, "VALUE_MISMATCH")

    # ---- N
    def n1a(self): return (self.r.same["P22"], self.r.n_docs)
    def n1b(self): return (self.r.same["P26"], self.r.n_docs)
    def n2a(self): return self.r.pop[POP67]["state"]["P27"]["GROUNDED"]
    def n2b(self): return self.r.pop[POP67]["state"]["P27"]["VALUE_MISMATCH"]
    def n2c(self): return self.r.pop[POP30]["state"]["P27"]["GROUNDED"]
    def n2d(self): return self.r.pop[POP30]["state"]["P27"]["VALUE_MISMATCH"]
    def n2e(self): return self.r.pop[POP67]["a_ptr_only_grounded"]
    def n2f(self): return self.r.pop[POP30]["a_ptr_only_grounded"]
    def n2g(self): return self.r.pop[POP67]["a_state_moved"]
    def n2h(self): return self.r.pop[POP30]["a_state_moved"]

    def n2i(self):
        return sum(self.r.pop[p][k] for p in (POP67, POP30) for k in ("a_other_dir", "a_to_vm", "a_new_g"))

    def n3a(self):
        ok = all(self.r.pop[p]["state"]["P27E"]["GROUNDED"] == self.r.pop[p]["state"]["P27"]["GROUNDED"] for p in (POP67, POP30))
        return sum(self.r.pop[p]["b_touch_g"] for p in (POP67, POP30)) if ok else -1

    def n3b(self): return sum(self.r.pop[p]["b_other_dir"] for p in (POP67, POP30))
    def n3c(self): return self.r.pop[POP67]["b_to_vm"]
    def n3d(self): return self.r.pop[POP30]["b_to_vm"]


def item_parsed(seal_text, item):
    sid, what, row, idx, key = item
    if row is None:
        if sid == "D-3":
            return ("le", Fraction(0))
        return ("eq", Fraction(0))
    if row.startswith("K-"):
        toks = seal_k_tokens(seal_text, row)
    else:
        toks = seal_row_tokens(seal_text, row)
    return parse_token(toks[idx])


def item_token_text(seal_text, item):
    sid, what, row, idx, key = item
    if row is None:
        return u"≤ 0 行(P26 の行以下)" if sid == "D-3" else u"0 行"
    toks = seal_k_tokens(seal_text, row) if row.startswith("K-") else seal_row_tokens(seal_text, row)
    return toks[idx]


def measure(meas, key):
    return getattr(meas, key)()


def show_value(item, x):
    sid, what, row, idx, key = item
    if x is None:
        return u"—"
    if isinstance(x, tuple):
        return u"%d / %d" % x
    if key in ("v1a", "v1b", "v1c", "v1d", "v2a", "v2b", "v2c", "v2d", "v3e", "v4a", "v4b", "v4c", "k1a", "k2a", "d1a"):
        return show_pct(x)
    if key in ("k2b", "k3b"):
        return u"%.1f ポイント" % float(x)
    return fnum(x)


def judged_rows(meas, seal_text, items):
    """(小項目の表の行の列, [(小項目, 当否)])。"""
    rows, verdicts = [], []
    for it in items:
        sid, what, row, idx, key = it
        parsed = item_parsed(seal_text, it)
        x = measure(meas, key)
        ok = in_band(parsed, x)
        verdicts.append((sid, ok))
        rows.append(u"| %s | %s | %s | %s | %s |" % (sid, what, item_token_text(seal_text, it), show_value(it, x), u"当たり" if ok else u"外れ"))
    return rows, verdicts


def summarize(verdicts):
    out = collections.OrderedDict()
    for sid, ok in verdicts:
        out.setdefault(group(sid), []).append((sid, ok))
    return out


def group(sid):
    """小項目の id -> 項目の id(末尾の小文字を外す。K-4 のように無ければそのまま)。"""
    return re.sub(r"[a-z]$", "", sid)


def verdict_rows(groups, ids, head):
    rows = [u"| %s | 当否 | 外れた小項目 |" % head, u"|---|---|---|"]
    for gid in ids:
        vs = groups.get(gid, [])
        ok = bool(vs) and all(o for _s, o in vs)
        miss = u"・".join(s for s, o in vs if not o) or u"—"
        rows.append(u"| %s | %s | %s |" % (gid, u"当たり" if ok else u"外れ", miss))
    return rows


def all_ok(verdicts):
    return bool(verdicts) and all(o for _s, o in verdicts)


def decisions(meas, seal_text):
    """記録から求めた判定。{'K': [(小項目, 当否)], 'D': [...], 'adopt_P27E': bool, 'default_P27': bool}。"""
    krows, kv = judged_rows(meas, seal_text, K_ITEMS)
    drows, dv = judged_rows(meas, seal_text, D_ITEMS)
    return {"krows": krows, "K": kv, "drows": drows, "D": dv, "adopt_P27E": all_ok(kv), "default_P27": all_ok(dv)}


VERDICT_P27E = (u"P27E を「外部の数の文に使う profile」として", u"採用する", u"採用しない")
VERDICT_P27 = (u"P27 を「既定の候補」として", u"記録する", u"記録しない")


def verdict_sentences(dec):
    """文書に字のまま在るべき 2 つの判定の文(門が記録から求めた判定の字)。"""
    a = VERDICT_P27E
    b = VERDICT_P27
    return (u"判定(P27E): %s%s。" % (a[0], a[1] if dec["adopt_P27E"] else a[2]),
            u"判定(P27): %s%s。" % (b[0], b[1] if dec["default_P27"] else b[2]))


# ======================================================================================================
# 文書の表(門の中身。文書はこの表と 1 行も違わない)
def reason_str(c):
    return c["state"] if not c["reason"] else u"%s / %s" % (c["state"], c["reason"])


def sha_rows(file_bytes):
    return [u"| 記録 | sha256 |", u"|---|---|"] + [u"| %s | %s |" % (rel, sha256_hex(file_bytes[k])) for k, rel in DOC_SHA_REL.items()]


def commit_rows(recs):
    e = recs["eval"]
    fp = e["engine の指紋"]
    rows = [u"| 項目 | 値 |", u"|---|---|"]
    for lab, key in ((u"W(評価用の文の凍結)", u"W の commit"), (u"T(調整用の診断)", u"T の commit"), (u"S2(段 2 の封)", u"S2 の commit"),
                     (u"E(P27・P27E を足した engine)", u"E の commit"), (u"HEAD(測った時)", u"HEAD の commit")):
        rows.append(u"| %s | %s |" % (lab, e[key]))
    rows.append(u"| 評価用の測定の script の sha256 | %s |" % e[u"この script の sha256"])
    rows.append(u"| 段 1 の測定の script の sha256 | %s |" % e[u"段 1 の測定の script(読むだけ・1 字も変えない)の sha256"])
    rows.append(u"| 97 書類の測定の script の sha256 | %s |" % e[u"97 書類の測定の script(rule_counts を読むだけ・1 字も変えない)の sha256"])
    rows.append(u"| engine の指紋 adapters/xbrl(file 数) | %s(%d) |" % (fp["adapter_xbrl_py_sha256"], fp["adapter_xbrl_py_files"]))
    rows.append(u"| engine の指紋 core(file 数) | %s(%d) |" % (fp["core_py_sha256"], fp["core_py_files"]))
    rows.append(u"| 既存の cache(edinet / edinet-fresh-2026-10-21)の件数の前 → 後 | %d / %d → %d / %d |" % (
        e[u"cache の前後"][u"前"][u"既存の cache"][u"件数"], e[u"cache の前後"][u"前"][u"ZIP の folder"][u"件数"],
        e[u"cache の前後"][u"後"][u"既存の cache"][u"件数"], e[u"cache の前後"][u"後"][u"ZIP の folder"][u"件数"]))
    return rows


def verdict_table(dec):
    a, b = VERDICT_P27E, VERDICT_P27
    return [u"| 判定 | 結果 |", u"|---|---|",
            u"| %s | %s |" % (a[0], a[1] if dec["adopt_P27E"] else a[2]),
            u"| %s | %s |" % (b[0], b[1] if dec["default_P27"] else b[2])]


def v6_rows(calc, meas):
    """V-6 の 4 つの数と、別の数え(claim の判定から)。別の数えが無い規則は —。"""
    c = calc
    c2_alt = sum(1 for x in c.claims if x["P27"]["reason"] == "per_unit_counter")
    c1_alt = sum(1 for x in c.claims if x["P27"]["state"] == "POINTER_NOT_FOUND" and x["P27"]["reason"] == OTHER_CONCEPT
                 and x["P26"]["state"] == "VALUE_MISMATCH")
    b_alt = sum(1 for x in c.claims if x["P27E"]["state"] == "VALUE_MISMATCH" and x["P27"]["state"] == "POINTER_NOT_FOUND"
                and x["P27"]["reason"] == NO_SAME_VALUE)
    rows = [u"| 規則 | provenance の数(V-6 の実測) | 別の数え(claim の判定から) | 別の数えの意味 |", u"|---|---|---|---|"]
    rows.append(u"| C2 で止めた claim(P27) | %d | %d | P27 の reason が per_unit_counter の claim |" % (meas.v6a(), c2_alt))
    rows.append(u"| C3 で target_or_plan にした claim(P27) | %d | — | 別の数えは無い(target_or_plan は C3 以外の規則でも付く) |" % meas.v6b())
    rows.append(u"| C1 で other_concept になった行(P27) | %d | %d | P26 で VALUE_MISMATCH かつ P27 で POINTER_NOT_FOUND / other_concept の claim |" % (meas.v6c(), c1_alt))
    rows.append(u"| B で名指した行(P27E の無改変) | %d | %d | P27 で POINTER_NOT_FOUND / no_same_value かつ P27E で VALUE_MISMATCH の claim |" % (meas.v6d(), b_alt))
    return rows


def scale_rows(calc):
    c = calc
    n_style = collections.Counter(c.style[d] for d in c.docs)
    rows = [u"| 項目 | 値 |", u"|---|---|"]
    rows.append(u"| 評価用の会社の数(型 A / B / C) | %d(%d / %d / %d) |" % (len(c.docs), n_style["A"], n_style["B"], n_style["C"]))
    rows.append(u"| claim の数(P22 / P26 / P27 / P27E) | %s |" % u" / ".join(u"%d" % sum(1 for x in c.claims if x[p]) for p in P4))
    rows.append(u"| 読む行の数 | %d |" % len(c.readings))
    rows.append(u"| 注入の行の数(T1_VALUE / T8_REL / 合計) | %d / %d / %d |" % (len(c.inj_rows("T1_VALUE")), len(c.inj_rows("T8_REL")), len(c.inj)))
    rows.append(u"| 4 profile の全部で対応が付く注入の行(T1_VALUE / T8_REL) | %d / %d |" % (len(c.all_mapped("T1_VALUE")), len(c.all_mapped("T8_REL"))))
    return rows


def state_rows(calc):
    c = calc
    rows = [u"| profile | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND | 計 | VALUE_MISMATCH の率 |", u"|---|---|---|---|---|---|---|"]
    for p in P4:
        sc = c.state_counts(p)
        rows.append(u"| %s | %d | %d | %d | %d | %d | %s |" % (p, sc["GROUNDED"], sc["VALUE_MISMATCH"], sc["UNVERIFIABLE"], sc["POINTER_NOT_FOUND"],
                                                         sum(sc.values()), show_pct(pct(sc["VALUE_MISMATCH"], len(c.claims)))))
    return rows


def per_doc_rows(calc):
    c = calc
    rows = [u"| docID | 型 | claim | VALUE_MISMATCH(P22 / P26 / P27 / P27E) | 読む行 | 注入 T1_VALUE | 注入 T8_REL | T8_REL で通した(P22 / P26 / P27 / P27E) |",
            u"|---|---|---|---|---|---|---|---|"]
    for d in c.docs:
        cl = [x for x in c.claims if x["docID"] == d]
        t8 = [x for x in c.inj_rows("T8_REL") if x["docID"] == d]
        rows.append(u"| %s | %s | %d | %s | %d | %d | %d | %s |" % (
            d, c.style[d], len(cl), u" / ".join(u"%d" % sum(1 for x in cl if x[p]["state"] == "VALUE_MISMATCH") for p in P4),
            sum(1 for x in c.readings if x["docID"] == d), len([x for x in c.inj_rows("T1_VALUE") if x["docID"] == d]), len(t8),
            u" / ".join(u"%d" % sum(1 for x in t8 if x[p]["結果"] == LABEL_PASS) for p in P4)))
    return rows


def moved_rows(calc):
    """無改変の claim の判定が profile の間で動いた行(state・reason・pointer)。span・value は無い。"""
    c = calc
    rows = [u"| 比べる profile | 動き | 前(state / reason) | 後(state / reason) | 行 |", u"|---|---|---|---|---|"]
    for a, b in (("P22", "P26"), ("P26", "P27"), ("P27", "P27E")):
        cnt = collections.Counter()
        for x in c.claims:
            u, v = x[a], x[b]
            if (u["state"], u["reason"]) != (v["state"], v["reason"]):
                cnt[(u"state か reason", reason_str(u), reason_str(v))] += 1
            elif u["pointers"] != v["pointers"]:
                cnt[(u"pointer だけ", reason_str(u), reason_str(v))] += 1
        for (kind, f, t), n in sorted(cnt.items(), key=lambda kv: tuple(u"%s" % z for z in kv[0])):
            rows.append(u"| %s → %s | %s | %s | %s | %d |" % (a, b, kind, f, t, n))
    return rows


def inject_rows(calc):
    c = calc
    rows = [u"| 型 | profile | 文体 | 分母(4 profile の全部で対応が付く) | 通した | 名指して原本の値を返した | 名指したが別の値 | "
            u"止めたが名指さない(POINTER_NOT_FOUND) | 止めたが名指さない(UNVERIFIABLE) | 名指して原本の値の率 | 通した率 |", u"|" + u"---|" * 11]
    for typ in TYPES:
        for p in P4:
            for st in STYLES + (None,):
                m = c.all_mapped(typ, st)
                lc = [c.count(m, p, lab) for lab in LABELS]
                rows.append(u"| %s | %s | %s | %d | %s | %s | %s |" % (typ, p, st or u"全体", len(m), u" | ".join(u"%d" % k for k in lc),
                                                                   show_pct(pct(lc[1], len(m))), show_pct(pct(lc[0], len(m)))))
    return rows


def denom_rows(calc):
    c = calc
    rows = [u"| 型 | profile | 各 profile で対応が付く(各 profile の分母) | 通した | 通した率 | 名指して原本の値を返した | 名指して原本の値の率 | "
            u"4 profile の全部で対応が付く(封の分母) | 2 つの分母が同じ |", u"|" + u"---|" * 9]
    for typ in TYPES:
        for p in P4:
            m, a = c.mapped(typ, p), c.all_mapped(typ)
            ps, no = c.count(m, p, LABEL_PASS), c.count(m, p, LABEL_NAMED_ORIGINAL)
            rows.append(u"| %s | %s | %d | %d | %s | %d | %s | %d | %s |" % (typ, p, len(m), ps, show_pct(pct(ps, len(m))), no, show_pct(pct(no, len(m))),
                                                                       len(a), u"同じ" if len(m) == len(a) else u"違う"))
    return rows


def reason_rows(calc):
    c = calc
    cnt = collections.Counter()
    for typ in TYPES:
        for x in c.all_mapped(typ):
            for p in P4:
                if x[p]["結果"] in (LABEL_PNF, LABEL_UNV):
                    cnt[(typ, p, x[p]["結果"], x[p]["reason"] or u"(reason なし)")] += 1
    rows = [u"| 型 | profile | 結果 | reason | 行 |", u"|---|---|---|---|---|"]
    for k, v in sorted(cnt.items(), key=lambda kv: tuple(u"%s" % y for y in kv[0])):
        rows.append(u"| %s | %s | %s | %s | %d |" % (k + (v,)))
    return rows


def cross_rows(calc):
    """同じ注入の行の、隣り合う profile の結果の対(4 profile の全部で対応が付く行)。"""
    c = calc
    rows = [u"| 型 | 比べる profile | 前の結果 | 後の結果 | 行 |", u"|---|---|---|---|---|"]
    for typ in TYPES:
        for a, b in (("P22", "P26"), ("P26", "P27"), ("P27", "P27E")):
            cnt = collections.Counter((x[a]["結果"], x[b]["結果"]) for x in c.all_mapped(typ))
            for (u, v), n in sorted(cnt.items(), key=lambda kv: tuple(u"%s" % z for z in kv[0])):
                rows.append(u"| %s | %s → %s | %s | %s | %d |" % (typ, a, b, u, v, n))
    return rows


def r_rows(calc):
    c = calc
    rows = [u"| r(T8_REL) | profile | 分母 | 通した | 名指して原本の値を返した | 名指したが別の値 | 止めたが名指さない |", u"|---|---|---|---|---|---|---|"]
    both = c.all_mapped("T8_REL")
    for r in sorted(set(x["r"] for x in both)):
        rs = [x for x in both if x["r"] == r]
        for p in P4:
            k = lambda lab: c.count(rs, p, lab)                                    # noqa: E731
            rows.append(u"| %+g | %s | %d | %d | %d | %d | %d |" % (r, p, len(rs), k(LABEL_PASS), k(LABEL_NAMED_ORIGINAL), k(LABEL_NAMED_OTHER),
                                                                 k(LABEL_PNF) + k(LABEL_UNV)))
    return rows


def cond_rows(calc):
    c = calc
    rows = [u"| 条件 | 行 | 合わせた側 道具 | 文 | 分からない | 2 席の側が一致した行 | 細目が割れた行(側は道具) |", u"|---|---|---|---|---|---|---|"]
    sets = ((u"K-3 の行: P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない", c.k3_keys()),
            (u"K-4 の行: P26 で GROUNDED かつ P27E で GROUNDED でない", c.k4_keys("P27E")),
            (u"封 §7 の P27 の条件: P26 で GROUNDED かつ P27 で GROUNDED でない", c.k4_keys("P27")),
            (u"読む行の全体(封 §7 の和集合)", c.sealed_read_keys()))
    for name, ks in sets:
        rs = [c.read_by_key[k] for k in sorted(ks) if k in c.read_by_key]
        sides = collections.Counter(c.merged(r)[0] for r in rs)
        split = sum(1 for r in rs if c.side_of(r) == SIDE_TOOL and c.merged(r)[1] == UNSURE)
        rows.append(u"| %s | %d | %d | %d | %d | %d | %d |" % (name, len(ks), sides.get(SIDE_TOOL, 0), sides.get(SIDE_SENT, 0), sides.get(UNSURE, 0),
                                                        sum(1 for r in rs if r["席1"]["側"] == r["席2"]["側"]), split))
    return rows


def read_row_rows(calc):
    c = calc
    rows = [u"| 行 | 条件 | P26 | P27 | P27E | 席1(側 / 細目) | 席2(側 / 細目) | 合わせた(側 / 細目) |", u"|---|---|---|---|---|---|---|---|"]
    for r in sorted(c.readings, key=lambda x: (x["docID"], x["id"])):
        cl = c.by_key[(r["docID"], r["id"])]
        m = c.merged(r)
        rows.append(u"| %s | %s | %s | %s | %s | %s / %s | %s / %s | %s / %s |" % (
            r["行"], u"・".join(r["条件"]), reason_str(cl["P26"]), reason_str(cl["P27"]), reason_str(cl["P27E"]),
            r["席1"]["側"], r["席1"]["細目"], r["席2"]["側"], r["席2"]["細目"], m[0], m[1]))
    return rows


def seat_rows(calc):
    c = calc
    n = len(c.readings)
    side = sum(1 for r in c.readings if r["席1"]["側"] == r["席2"]["側"])
    det = sum(1 for r in c.readings if r["席1"]["側"] == r["席2"]["側"] and r["席1"]["細目"] == r["席2"]["細目"])
    rows = [u"| 項目 | 値 |", u"|---|---|", u"| 2 席の側が一致した行 | %s |" % ab(side, n), u"| 側が一致し細目も一致した行 | %s |" % ab(det, n)]
    for seat in ("席1", "席2"):
        cnt = collections.Counter(r[seat]["細目"] for r in c.readings)
        rows.append(u"| %s の細目の内訳 | %s |" % (seat, u"・".join(u"%s %d" % (k, v) for k, v in sorted(cnt.items(), key=lambda kv: u"%s" % kv[0]))))
    side_c = collections.Counter(c.merged(r)[0] for r in c.readings)
    rows.append(u"| 合わせた側の内訳(文 / 道具 / 分からない) | %d / %d / %d |" % (side_c.get(SIDE_SENT, 0), side_c.get(SIDE_TOOL, 0), side_c.get(UNSURE, 0)))
    rows.append(u"| 合わせた札が文2の行 | %d |" % sum(1 for r in c.readings if c.merged(r) == (SIDE_SENT, u"文2")))
    return rows


def build_blocks(recs, e_recs, file_bytes, seal_text):
    """文書の門の表。名前 -> 行の列。"""
    calc = Calc(recs)
    regress = Regress(e_recs["regress97"])
    meas = Measures(calc, regress, seal_text)
    vrows, vv = judged_rows(meas, seal_text, V_ITEMS)
    nrows, nv = judged_rows(meas, seal_text, N_ITEMS)
    dec = decisions(meas, seal_text)
    b = collections.OrderedDict()
    b["sha"] = sha_rows(file_bytes)
    b["commit"] = commit_rows(recs)
    b["K-小項目"] = [u"| 小項目 | 見るもの | 封の字(幅・閾値) | 実測 | 当否 |", u"|---|---|---|---|---|"] + dec["krows"]
    b["K-当否"] = verdict_rows(summarize(dec["K"]), K_IDS, u"K")
    b["D-小項目"] = [u"| 小項目 | 見るもの | 封の字(幅・閾値) | 実測 | 当否 |", u"|---|---|---|---|---|"] + dec["drows"]
    b["D-当否"] = verdict_rows(summarize(dec["D"]), ("D-1", "D-3", "D-4", "D-5", "D-N2"), u"D(P27 を既定の候補とする条件)")
    b["判定"] = verdict_table(dec)
    b["V-小項目"] = [u"| 小項目 | 見るもの | 予測(封 §3-2 の幅) | 実測 | 当否 |", u"|---|---|---|---|---|"] + vrows
    b["V-当否"] = verdict_rows(summarize(vv), V_IDS, u"V")
    b["V-6"] = v6_rows(calc, meas)
    b["N-小項目"] = [u"| 小項目 | 見るもの | 予測(封 §3-3 の幅) | 実測 | 当否 |", u"|---|---|---|---|---|"] + nrows
    b["N-当否"] = verdict_rows(summarize(nv), N_IDS, u"N")
    b["規模"] = scale_rows(calc)
    b["state"] = state_rows(calc)
    b["書類別"] = per_doc_rows(calc)
    b["動いた行"] = moved_rows(calc)
    b["注入-分布"] = inject_rows(calc)
    b["注入-分母"] = denom_rows(calc)
    b["注入-reason"] = reason_rows(calc)
    b["注入-交差"] = cross_rows(calc)
    b["注入-r"] = r_rows(calc)
    b["読む行-条件"] = cond_rows(calc)
    b["読む行-行"] = read_row_rows(calc)
    b["読み-席"] = seat_rows(calc)
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
# 記録の中身の門(a)(b)(c)。木の走査・禁止の名前・鍵の検査器は、段 1 の結果の門(PRECEDENT_GATE_REL)の部品を読んで使う(写さない)
PT = _load_module(PRECEDENT_GATE_REL, "p27_tune_result_gate_machinery")
M = _load_module(EVAL_SCRIPT_REL, "p27_eval_script_for_result_gate")                      # 評価用の測定の script(定数と検査器を読む)
FK, Opt, leaf = PT.FK, PT.Opt, PT.leaf
DOC_RE = PT.DOC_RE
ROW_RE = PT.ROW_RE
RATE = PT.RATE
STATE4 = PT.STATE4
CACHE_BEFORE_AFTER = PT.CACHE_BEFORE_AFTER
CLAIM_SIDE = PT.CLAIM_SIDE
REASON_KEY_RE = PT.REASON_KEY_RE
FORBIDDEN_NAMES = PT.FORBIDDEN_NAMES
JP_RE = PT.JP_RE
NONJP_SAFE = PT.NONJP_SAFE


def PROF4(node):
    return (u"4 profile の対", dict((p, node) for p in P4))


def PROF3(node):
    return (u"P26・P27・P27E の対", dict((p, node) for p in ("P26", "P27", "P27E")))


COND_RE = r"[A-Za-z0-9_]+$"
RULE_KEYS = (u"C2 per_unit_counter", u"C3 future_period", u"C1 の窓に入った claim", u"C1 の窓に入って other_concept になった claim", u"B relative_within_rho")

RUN_HEADER4 = {
    u"seal": leaf(u"封の path"), u"step": leaf(u"この記録の段の名前(固定の文)"), u"dry_run": leaf(u"下見(作り物の engine)か"),
    u"backend": leaf(u"engine の種類(real / stub / なし)"),
    u"HEAD の commit": leaf(u"走らせた時の HEAD(40 桁)"), u"W の commit": leaf(u"凍結 W の commit(40 桁)"), u"T の commit": leaf(u"T の commit(40 桁)"),
    u"S2 の commit": leaf(u"S2 の commit(40 桁)"), u"E の commit": leaf(u"E の commit(40 桁)"),
    u"走る前の確かめ": (u"封 §7 の (a)(b) の確かめの結果", {
        u"封の file は HEAD で追跡され作業木と同じ": leaf(u"真偽"), u"W ⊑ S2": leaf(u"真偽"), u"S2 ⊏ E": leaf(u"真偽"), u"E ⊑ HEAD": leaf(u"真偽"),
        u"E と HEAD の間で adapters・core に差が無い": leaf(u"真偽"), u"profile の一覧": leaf(u"profile の名前の列"), u"既定の profile": leaf(u"既定の profile の名前")}),
    u"この script の sha256": leaf(u"評価用の測定の script の sha256"),
    u"段 1 の測定の script(読むだけ・1 字も変えない)の sha256": leaf(u"段 1 の script の sha256"),
    u"97 書類の測定の script(rule_counts を読むだけ・1 字も変えない)の sha256": leaf(u"97 書類の script の sha256"),
    u"対象の docID": leaf(u"対象の docID の列(評価用)"), u"対象は評価用の全部": leaf(u"対象が評価用の全部か"), u"評価用の件数": leaf(u"数"),
    u"使った文の sha256": (u"docID -> 文の sha256(文の字は無い)", FK(DOC_RE.pattern, leaf(u"文の sha256"))),
    u"engine の指紋": (u"engine の file の sha256 と数(real のときだけ中身がある)", {
        u"adapter_xbrl_py_sha256": Opt(leaf(u"adapters/xbrl の sha256")), u"adapter_xbrl_py_files": Opt(leaf(u"file の数")),
        u"core_py_sha256": Opt(leaf(u"core の sha256")), u"core_py_files": Opt(leaf(u"file の数")), u"git_commit": Opt(leaf(u"git の commit(40 桁)"))}),
    u"cache の前後": CACHE_BEFORE_AFTER,
}

PAIR_LISTS = (u"profile ごとの id の列", dict((p, leaf(u"id の列")) for p in ("P26", "P27", "P27E")))
CLAIM4 = dict((p, CLAIM_SIDE) for p in P4)
AGG_RATES = dict((lab, RATE) for lab in LABELS)
AGG = (u"文体(と全体)の集計", dict(AGG_RATES, **{
    u"注入の行": leaf(u"数"), u"対応が付く": leaf(u"数"), u"対応が付かない": leaf(u"数"),
    u"POINTER_NOT_FOUND の reason の内訳": (u"reason -> 数", FK(REASON_KEY_RE.pattern, leaf(u"数"))),
    u"UNVERIFIABLE の reason の内訳": (u"reason -> 数", FK(REASON_KEY_RE.pattern, leaf(u"数")))}))
INJ_AGG = (u"型の集計", dict(dict((p, (u"profile の集計", dict((st, AGG) for st in STYLES + (u"全体",)))) for p in P4),
                          **{u"両方の profile で対応が付く": leaf(u"数")}))
SIDES3 = (u"側 -> 数", {u"文": leaf(u"数"), u"道具": leaf(u"数"), u"分からない": leaf(u"数")})
INJ_P = lambda: (u"profile の結果", {u"対応": leaf(u"対応が付くか"), u"結果": leaf(u"結果の語"), u"state": leaf(u"state"), u"reason": leaf(u"理由の符号")})   # noqa: E731
SEAT = lambda: (u"席の札", {u"側": leaf(u"文 / 道具 / 分からない"), u"細目": leaf(u"文1〜道5 か null")})                                              # noqa: E731

ALLOWED = {
    "eval": dict(RUN_HEADER4, **{
        u"claim の対の付け方": leaf(u"対の付け方の文"),
        u"会社": (u"評価用の会社ごと(文の sha256 と claim の数と規則ごとの数)", [{
            u"docID": leaf(u"書類 ID"), u"型": leaf(u"A / B / C"), u"文の sha256": leaf(u"文の sha256"),
            u"claim の数": PROF4(leaf(u"数")), u"state の数": PROF4(STATE4),
            u"片方の profile にしか無い id": PAIR_LISTS, u"値・span・単位が profile 間で違う id": PAIR_LISTS,
            u"規則ごと(build_raw_claims の provenance)": (u"P27・P27E の規則ごとの数", dict((p, (u"規則 -> 数", dict((k, leaf(u"数")) for k in RULE_KEYS)))
                                                                             for p in ("P27", "P27E")))}]),
        u"claim": (u"claim ごとの判定(id・kind・form・unit・state・reason・pointers だけ)", [dict({u"docID": leaf(u"書類 ID"), u"id": leaf(u"claim の id")}, **CLAIM4)]),
        u"集計": (u"script の自前の集計", {
            u"claim": PROF4(leaf(u"数")), u"state の数": PROF4(STATE4), u"VALUE_MISMATCH の率": PROF4(RATE),
            u"P27E の VALUE_MISMATCH の行 − P27 の VALUE_MISMATCH の行": leaf(u"数"),
            u"P26 → P27 で GROUNDED を離れた行": leaf(u"数"), u"P26 → P27 で新しい GROUNDED": leaf(u"数"), u"P26 → P27 で VALUE_MISMATCH に入る行": leaf(u"数"),
            u"P27 → P27E で state が動いた行": leaf(u"数"), u"P27 と P27E で GROUNDED の行が同じ": leaf(u"真偽"),
            u"P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない行": leaf(u"数"),
            u"規則ごとに当たった claim(V-6。build_raw_claims の provenance)": (u"規則 -> 数", {
                u"C2 で止めた claim(P27)": leaf(u"数"), u"C3 で target_or_plan にした claim(P27)": leaf(u"数"),
                u"C1 で other_concept になった行(P27)": leaf(u"数"), u"B で名指した行(P27E の無改変)": leaf(u"数")}),
            u"読む行": (u"読む行の数と条件ごとの数", {u"数": leaf(u"数"), u"条件ごと(重なる)": (u"条件 -> 数", FK(COND_RE, leaf(u"数")))})}),
        u"読む行": (u"読む行の一覧", [{u"行": leaf(u"docID:claim id"), u"docID": leaf(u"書類 ID"), u"id": leaf(u"claim id"), u"条件": leaf(u"当たった条件の符号の列")}]),
        u"束の P27・P27E の欄を足す形(script の定数)": (u"束に足す欄の字(script の定数)", {
            u"DOSSIER_P27_BLOCK": leaf(u"定数の字"), u"DOSSIER_NO_CLAIM": leaf(u"定数の字"), u"DOSSIER_P27_FACTS_HEAD": leaf(u"定数の字"),
            u"profile": leaf(u"束に足す profile の名前の列")}),
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
    "eval_inject": dict(RUN_HEADER4, **{
        u"種": (u"種 file の追跡と sha256", {u"file": leaf(u"path"), u"sealed_in_commit": leaf(u"封じた commit"), u"seed_file_sha256": leaf(u"sha256")}),
        u"型": (u"注入の型の宣言", {u"T1_VALUE": leaf(u"宣言の文"), u"T8_REL": leaf(u"宣言の文"), u"上限": leaf(u"宣言の文"), u"土台": leaf(u"宣言の文"),
                                  u"率の分母": leaf(u"宣言の文")}),
        u"round-trip": (u"round-trip の確かめ", {u"確かめた注入の数": leaf(u"数"), u"注入した字を元に戻すと無改変の文と byte 一致": leaf(u"真偽"),
                                              u"確かめ方": leaf(u"確かめ方の文")}),
        u"書類別の数え": (u"docID -> 型 -> 数え", FK(DOC_RE.pattern, (u"型ごとの数え", dict((t, (u"数えの名前 -> 数", FK(
            u"(?:作れる site|採った|円族の token|r が決まらず site にしない|基準に対応が付かない|profile 間で claim が合わない|"
            u"両方 GROUNDED|P22 のみ GROUNDED|P26 のみ GROUNDED|どちらも GROUNDED でない)$", leaf(u"数")))) for t in TYPES)))),
        u"注入の行の数": leaf(u"数"),
        u"集計(各 profile で対応が付く行が分母)": (u"script の自前の集計", dict((t, INJ_AGG) for t in TYPES)),
        u"集計(4 profile の全部で対応が付く行が分母。V-1〜V-3)": (u"script の自前の集計", dict((t, INJ_AGG) for t in TYPES)),
        u"4 profile の全部で対応が付く行": (u"型 -> 数", dict((t, leaf(u"数")) for t in TYPES)),
        u"T8_REL の site": (u"T8_REL の site の数", {u"注入の行": leaf(u"数"), u"作れる site(上限の前)": leaf(u"数")}),
        u"行": (u"注入の行ごとの結果(注入の字・新しい値は無い)", [dict({
            u"docID": leaf(u"書類 ID"), u"id": leaf(u"注入の id"), u"型": leaf(u"T1_VALUE / T8_REL"), u"文体": leaf(u"A / B / C"),
            u"基準の claim": leaf(u"土台の claim id"), u"r": Opt(leaf(u"T8_REL の相対の変え幅")), u"r を決めた回": Opt(leaf(u"r を決めた試行の回"))},
            **dict((p, INJ_P()) for p in P4))]),
        u"repo の外に置いたもの": (u"repo の外の file の sha256", {u"folder": leaf(u"置き場"), u"注入の字・新しい値": (u"注入の字の file", {
            u"file": leaf(u"file 名"), u"sha256": leaf(u"sha256"), u"bytes": leaf(u"bytes")})}),
        u"限界": leaf(u"限界の文の列"),
    }),
    "eval_readings": dict(RUN_HEADER4, **{
        u"読みは": leaf(u"エージェントの読みで人間の読みでない宣言"), u"合わせ方(段 1 の封 §5-5)": leaf(u"合わせ方の文"),
        u"入力": (u"入力の sha256", {u"判定の記録": leaf(u"path"), u"判定の記録の sha256": leaf(u"sha256"),
                                  u"席1 の札の file の sha256": leaf(u"sha256"), u"席2 の札の file の sha256": leaf(u"sha256")}),
        u"行": (u"読む行ごとの札(側と細目の語だけ。理由と道5の形は無い)", [{
            u"行": leaf(u"docID:claim id"), u"docID": leaf(u"書類 ID"), u"id": leaf(u"claim id"), u"条件": leaf(u"当たった条件の符号の列"),
            u"席1": SEAT(), u"席2": SEAT(), u"合わせた": (u"合わせた札", {u"側": leaf(u"側"), u"細目": leaf(u"細目")})}]),
        u"集計": (u"script の自前の集計", {
            u"読む行": leaf(u"数"), u"2 席の側が一致した行": RATE, u"合わせた側の内訳": SIDES3, u"合わせた側が道具の行": leaf(u"数"),
            u"合わせた細目が付いた道具の行": (u"細目が付いた道具の行", {
                u"行": leaf(u"数"), u"細目の内訳": (u"細目 -> 数", FK(r"道[1-5]$", leaf(u"数"))), u"道1〜道4": RATE, u"道5": RATE}),
            u"合わせた札が文2の行": leaf(u"数"),
            u"条件ごと(重なる)": (u"条件 -> 集計", FK(COND_RE, (u"条件の集計", {u"行": leaf(u"数"), u"合わせた側の内訳": SIDES3, u"合わせた側が道具の行": leaf(u"数")})))}),
        u"repo の外に置いたもの": (u"repo の外の file の sha256", {u"folder": leaf(u"置き場"), u"道5 の形と各席の理由の文": (u"自由文の file", {
            u"file": leaf(u"file 名"), u"sha256": leaf(u"sha256"), u"bytes": leaf(u"bytes")})}),
    }),
}
# 注: 『読む行』の記録(eval_readings)の engine の指紋は空の欄の集まり({})。RUN_HEADER4 の子はどれも Opt なので許可される

#: 日本語を含む文字列の値の集合の指紋(各記録の、重複を除いた日本語を含む文字列を並べ替えて改行で結んだ sha256)。記録を作り直したら直す(凍結の面)。
JP_DIGEST = {
    "eval": "be658d9c37d0612101345674ea68df3b3620a2bc970601ab39d17adf97c38167",
    "eval_inject": "48e147b5bba0a63199d7953c5766becc837595505db38f336a07adc7c12e3ad4",
    "eval_readings": "0c5df8ecf160dcdc4f358dfaf076e6bb3d1837d2f3e2ee04790bc271808b3b6e",
}


def required_paths(allowed):
    out, req = set(), set()
    PT._static_paths(allowed, "", out, req)
    return req


def record_problems(name, obj, allowed=None, jp_digest=None, check_jp_digest=True, key_leak_fns=None):
    """記録 1 本の中身の検査。問題の文の列(空なら通す)。値の字は返さない(欄の path と種類だけ)。
    (a) 欄の木が許可の一覧と一致  (b) 禁止の名前の欄が無い  (c) 鍵らしい字が無い  + 日本語を含まない文字列の値の形 + 日本語を含む文字列の集合の指紋。"""
    allowed = ALLOWED[name] if allowed is None else allowed
    problems = []
    seen = set()
    PT._walk(obj, (u"記録の根", allowed), "", problems, seen)
    for p in sorted(required_paths(allowed) - seen):
        problems.append(u"許可の一覧にあるのに記録に無い欄: %s" % p)
    PT._forbidden_name_problems(obj, "", problems)
    for s in PT.strings_of(obj):
        if JP_RE.search(s):
            continue
        if not any(rx.fullmatch(s) for rx in NONJP_SAFE):
            problems.append(u"日本語を含まない文字列の値が許可の形でない(長さ %d)" % len(s))
    want = (JP_DIGEST if jp_digest is None else jp_digest)[name]
    if check_jp_digest and PT.jp_digest(obj) != want:
        problems.append(u"日本語を含む文字列の値の集合が凍結の指紋と違う")
    for fn in (key_leak_fns if key_leak_fns is not None else [M.T.record_key_leaks]):
        leaks = fn(obj)
        if leaks:
            problems.append(u"鍵らしい字(%s)" % u"/".join(sorted(set(leaks))))
    return problems


# ======================================================================================================
# git・engine の指紋(E の engine を git の blob から求め直す)
def git_show(commit, rel_from_repo):
    r = git("show", "%s:%s" % (commit, rel_from_repo))
    assert r.returncode == 0, (commit, rel_from_repo, r.stderr[:200])
    return r.stdout


def engine_fp_at(commit):
    """adapters/xbrl の直下の .py と core/py/audit_core の直下の .py の指紋(verify_document.engine_fingerprint と同じ作り方)を commit の blob から求める。"""
    out = {}
    for key, d in (("adapter_xbrl_py", ENGINE_DIRS[0]), ("core_py", ENGINE_DIRS[1])):
        ls = git("ls-tree", "--name-only", commit, d + "/")
        assert ls.returncode == 0, ls.stderr[:200]
        names = sorted(os.path.basename(n) for n in ls.stdout.decode("utf-8").split("\n") if n.endswith(".py"))
        rows = ["%s\t%s" % (n, sha256_hex(git_show(commit, d + "/" + n))) for n in names]
        out[key + "_sha256"] = sha256_hex("\n".join(rows).encode("utf-8"))
        out[key + "_files"] = len(rows)
    return out


def load_all():
    file_bytes = collections.OrderedDict((k, read_bytes(rel)) for k, rel in DOC_SHA_REL.items())
    recs = collections.OrderedDict((k, json.loads(file_bytes[k].decode("utf-8"))) for k in EVAL_REC_REL)
    e_recs = collections.OrderedDict((k, json.loads(file_bytes[k].decode("utf-8"))) for k in E_REC_REL)
    return file_bytes, recs, e_recs


def measures_of(recs, e_recs, seal_text):
    return Measures(Calc(recs), Regress(e_recs["regress97"]), seal_text)


def with_changes(recs, fn):
    r2 = copy.deepcopy(recs)
    fn(r2)
    return r2


# ======================================================================================================
class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file_bytes, cls.recs, cls.e_recs = load_all()
        cls.seal = read_text(SEAL_REL)
        cls.doc = read_text(DOC_REL)
        cls.calc = Calc(cls.recs)
        cls.regress = Regress(cls.e_recs["regress97"])
        cls.meas = Measures(cls.calc, cls.regress, cls.seal)
        cls.blocks = build_blocks(cls.recs, cls.e_recs, cls.file_bytes, cls.seal)
        cls.dec = decisions(cls.meas, cls.seal)
        cls.w = json.loads(read_text(W_REC_REL))
        cls.eval_ids = [c["docID"] for c in cls.w["会社"] if c["区分"] == u"評価用"]
        cls.tune_ids = [c["docID"] for c in cls.w["会社"] if c["区分"] == u"調整用"]


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
            if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席|書類|試行|回|本|ポイント)", l) and u"【門なし】" not in l:
                bad.append(l[:50])
        self.assertEqual(bad, [], u"散文の数に【門なし】の印が無い")

    def test_04_doc_names_only_the_eval_docids_and_all_of_them(self):
        self.assertEqual(len(self.eval_ids), 10)
        named = set(re.findall(r"S100[0-9A-Z]{4}", self.doc))
        self.assertLessEqual(named, set(self.eval_ids))
        self.assertEqual(named, set(self.eval_ids))
        for d in self.tune_ids:
            self.assertNotIn(d, self.doc)

    def test_05_record_shas_in_the_doc_equal_the_files(self):
        got = doc_blocks(self.doc)["sha"]
        self.assertEqual(len(got), 2 + len(DOC_SHA_REL))
        for k, rel in DOC_SHA_REL.items():
            self.assertIn(u"| %s | %s |" % (rel, sha256_hex(read_bytes(rel))), got)

    def test_06_the_verdict_sentences_are_the_ones_the_records_give(self):
        lines = self.doc.split("\n")
        for s in verdict_sentences(self.dec):
            self.assertEqual(sum(1 for l in lines if l.strip() == s), 1, s)
        # 反対の判定の字は文書のどこにも無い
        opposite = verdict_sentences(dict(adopt_P27E=not self.dec["adopt_P27E"], default_P27=not self.dec["default_P27"]))
        for s in opposite:
            self.assertNotIn(s, self.doc)
        self.assertEqual(sum(1 for l in lines if l.startswith(u"判定(")), 2)

    def test_07_doc_declares_what_is_gated_and_what_is_not(self):
        for needle in (u"門なし", u"エージェントの読み", u"人の目", u"同じ model", u"既定の切り替えは人間の決定", u"規則の案は書かない"):
            self.assertIn(needle, self.doc, needle)

    def test_08_doc_says_which_denominator_is_the_seal_one(self):
        self.assertIn(u"封の分母(§3-2): 4 profile の全部で対応が付く行", self.doc)

    def test_09_doc_sections_come_in_order_and_the_verdict_comes_first(self):
        heads = re.findall(r"^## (\d+)\.", self.doc, re.M)
        self.assertEqual(heads, [str(i) for i in range(8)])
        first_verdict = self.doc.index(u"判定(P27E):")
        for h in ("## 2.", "## 3.", "## 4.", "## 5."):
            self.assertLess(first_verdict, self.doc.index(h))
        self.assertGreater(first_verdict, self.doc.index("## 1."))

    def test_10_provenance_of_the_readers_is_marked_not_gated(self):
        marked = [l for l in self.doc.split("\n") if u"試行" in l]
        self.assertTrue(marked)
        for l in marked:
            self.assertIn(u"【門なし】", l)


class TestSealBounds(Base):
    def test_20_the_bands_are_read_from_the_seal_text(self):
        t = self.seal
        self.assertEqual(seal_row_tokens(t, "V-1"), [u"15〜50%", u"0〜3%"])
        self.assertEqual(seal_row_tokens(t, "V-2"), [u"45〜80%", u"10〜35%", u"10〜35%", u"70〜95%"])
        self.assertEqual(seal_row_tokens(t, "V-3"), [u"0〜1 行", u"50〜100%"])
        self.assertEqual(seal_row_tokens(t, "V-4"), [u"6〜14%", u"3〜8%", u"1.5〜6%", u"0〜4"])
        self.assertEqual(seal_row_tokens(t, "V-5"), [u"0〜6", u"0〜1"])
        self.assertEqual(seal_row_tokens(t, "V-6"), [u"3〜25", u"0〜12", u"0〜4", u"0〜4"])
        self.assertEqual(seal_row_tokens(t, "V-7"), [u"0〜10 行", u"0〜3"])
        self.assertEqual(seal_row_tokens(t, "N-1"), [u"97 / 97"])
        self.assertEqual(seal_row_tokens(t, "N-2"), [u"4,371", u"433", u"2,194", u"250", u"0〜3", u"20〜40", u"10〜25"])
        self.assertEqual(seal_row_tokens(t, "N-3"), [u"70〜95", u"15〜35"])
        self.assertEqual(seal_k_tokens(t, "K-1"), [u"≤ 2%", u"0"])
        self.assertEqual(seal_k_tokens(t, "K-2"), [u"≥ 70%", u"≥ 35 ポイント"])
        self.assertEqual(seal_k_tokens(t, "K-3"), [u"≤ 2", u"≤ P26 の率 + 1.0 ポイント"])
        self.assertEqual(seal_k_tokens(t, "K-4"), [u"≤ 3"])
        self.assertEqual(seal_k_tokens(t, "K-5"), [])

    def test_21_the_words_of_the_three_verdicts_and_the_unbolded_rules_are_in_the_seal(self):
        t = self.seal
        self.assertIn(u"**P27E を「外部の数の文に使う profile」として採用する**", t)
        self.assertIn(u"**P27 を「既定の候補」として記録する**", t)
        self.assertIn(u"K-1・K-4・K-5 を P27 で満たし、K-3 の代わりに「評価用の無改変で P27 の VALUE_MISMATCH の行 ≤ P26 の行」と §5 の N-2 の 4 つの数を満たすとき", t)
        self.assertIn(u"§5 の N-1 を満たす", t)
        self.assertIn(u"**採用しない**とき(どれか 1 つでも外れたら)", t)
        self.assertIn(u"外れ", t)

    def test_22_every_item_has_a_parsable_seal_text_and_a_value_from_the_records(self):
        for it in V_ITEMS + K_ITEMS + D_ITEMS + N_ITEMS:
            parsed = item_parsed(self.seal, it)
            self.assertIn(parsed[0], ("range", "ge", "le", "le_ref", "eq", "ratio"), it[0])
            self.assertTrue(item_token_text(self.seal, it), it[0])
            self.assertIsNotNone(measure(self.meas, it[4]), it[0])

    def test_23_band_edges_are_inclusive_like_the_seal_words(self):
        rng = parse_token(u"1.5〜6%")
        self.assertTrue(in_band(rng, Fraction(3, 2)) and in_band(rng, 6))
        self.assertFalse(in_band(rng, Fraction(149, 100)) or in_band(rng, Fraction(601, 100)))
        ge, le = parse_token(u"≥ 70%"), parse_token(u"≤ 2%")
        self.assertTrue(in_band(ge, 70) and not in_band(ge, Fraction(6999, 100)))
        self.assertTrue(in_band(le, 2) and not in_band(le, Fraction(201, 100)))
        ref = parse_token(u"≤ P26 の率 + 1.0 ポイント")
        self.assertTrue(in_band(ref, 1) and not in_band(ref, Fraction(101, 100)))
        self.assertTrue(in_band(parse_token(u"≥ 35 ポイント"), 35))
        self.assertTrue(in_band(parse_token(u"0"), 0) and not in_band(parse_token(u"0"), 1))
        self.assertTrue(in_band(parse_token(u"97 / 97"), (97, 97)) and not in_band(parse_token(u"97 / 97"), (96, 97)))
        self.assertTrue(in_band(parse_token(u"4,371"), 4371) and not in_band(parse_token(u"4,371"), 4370))
        self.assertFalse(in_band(rng, None))
        with self.assertRaises(AssertionError):
            parse_token(u"多い")


class TestRecompute(Base):
    """記録の自前の集計(script が書いた欄)と、ここで行から作り直した数が同じ(実装を 2 つ持つ)。"""

    def test_30_claim_counts_states_and_rates_equal_the_judge_record_own_summary(self):
        s, c = self.recs["eval"]["集計"], self.calc
        for p in P4:
            self.assertEqual(s["claim"][p], len(c.claims))
            self.assertEqual(s["state の数"][p], c.state_counts(p))
            self.assertEqual(s["VALUE_MISMATCH の率"][p]["件"], c.vm(p))
            self.assertEqual(s["VALUE_MISMATCH の率"][p]["分母"], len(c.claims))
            self.assertAlmostEqual(s["VALUE_MISMATCH の率"][p]["率"], float(pct(c.vm(p), len(c.claims))), delta=0.051)
        self.assertEqual(s["P27E の VALUE_MISMATCH の行 − P27 の VALUE_MISMATCH の行"], self.meas.v4d())
        self.assertEqual(s["P26 → P27 で GROUNDED を離れた行"], self.meas.v5a())
        self.assertEqual(s["P26 → P27 で新しい GROUNDED"], self.meas.v5b())
        self.assertEqual(s["P26 → P27 で VALUE_MISMATCH に入る行"], len(c.keys_where(lambda k: c.st(k, "P27") == "VALUE_MISMATCH" and c.st(k, "P26") != "VALUE_MISMATCH")))
        self.assertEqual(s["P27 → P27E で state が動いた行"], len(c.keys_where(lambda k: c.st(k, "P27") != c.st(k, "P27E"))))
        for d in self.recs["eval"]["会社"]:
            for p in P4:
                self.assertEqual(d["state の数"][p], c.state_counts(p, set([d["docID"]])))
                self.assertEqual(d["claim の数"][p], sum(d["state の数"][p].values()))
            self.assertEqual((d["片方の profile にしか無い id"], d["値・span・単位が profile 間で違う id"]),
                             (dict((p, []) for p in ("P26", "P27", "P27E")), dict((p, []) for p in ("P26", "P27", "P27E"))))

    def test_31_the_claim_ids_are_unique_and_the_same_for_the_four_profiles(self):
        self.assertEqual(len(self.calc.by_key), len(self.calc.claims))
        for x in self.calc.claims:
            for p in P4:
                self.assertIn(x[p]["state"], STATES)
        self.assertEqual(set(self.calc.docs), set(x["docID"] for x in self.calc.claims))

    def test_32_inject_aggregates_equal_the_rows_for_both_denominators(self):
        i, c = self.recs["eval_inject"], self.calc
        self.assertEqual(i["注入の行の数"], len(c.inj))
        for key, rows_of in ((u"集計(各 profile で対応が付く行が分母)", None), (u"集計(4 profile の全部で対応が付く行が分母。V-1〜V-3)", c.all_mapped)):
            for typ in TYPES:
                for p in P4:
                    for st in STYLES + (None,):
                        d = i[key][typ][p][st or u"全体"]
                        rows = rows_of(typ, st) if rows_of else c.mapped(typ, p, st)
                        self.assertEqual(d[u"対応が付く"], len(rows), (key, typ, p, st))
                        for lab in LABELS:
                            self.assertEqual(d[lab][u"件"], c.count(rows, p, lab), (key, typ, p, st, lab))
                            self.assertEqual(d[lab][u"分母"], len(rows))
                    self.assertEqual(i[key][typ][u"両方の profile で対応が付く"], len(c.all_mapped(typ)))
        for typ in TYPES:
            self.assertEqual(i[u"4 profile の全部で対応が付く行"][typ], len(c.all_mapped(typ)))

    def test_33_inject_labels_agree_with_states(self):
        for x in self.calc.inj:
            for p in P4:
                r = x[p]
                if not r["対応"]:
                    self.assertIsNone(r["state"])
                    continue
                want = {"GROUNDED": [LABEL_PASS], "VALUE_MISMATCH": [LABEL_NAMED_ORIGINAL, LABEL_NAMED_OTHER],
                        "POINTER_NOT_FOUND": [LABEL_PNF], "UNVERIFIABLE": [LABEL_UNV]}[r["state"]]
                self.assertIn(r["結果"], want)
        self.assertTrue(all(x["r"] in (-0.10, -0.03, 0.03, 0.10) for x in self.calc.inj_rows("T8_REL")))

    def test_34_v6_provenance_equals_the_record_summary_and_the_claim_side_counts(self):
        s = self.recs["eval"]["集計"][u"規則ごとに当たった claim(V-6。build_raw_claims の provenance)"]
        m = self.meas
        self.assertEqual((s[u"C2 で止めた claim(P27)"], s[u"C3 で target_or_plan にした claim(P27)"], s[u"C1 で other_concept になった行(P27)"],
                          s[u"B で名指した行(P27E の無改変)"]), (m.v6a(), m.v6b(), m.v6c(), m.v6d()))
        rows = v6_rows(self.calc, m)
        self.assertEqual(rows[2].split("|")[2].strip(), rows[2].split("|")[3].strip())          # C2 の 2 通りの数えが同じ
        self.assertEqual(rows[4].split("|")[2].strip(), rows[4].split("|")[3].strip())          # C1
        self.assertEqual(rows[5].split("|")[2].strip(), rows[5].split("|")[3].strip())          # B

    def test_35_read_rows_follow_the_sealed_condition_and_the_conditions_in_the_records(self):
        c = self.calc
        keys = set((r["docID"], r["id"]) for r in c.readings)
        self.assertEqual(len(keys), len(c.readings))
        self.assertEqual(c.sealed_read_keys(), keys)                       # 読む行 = 条件から求めた集合(多くも少なくもない)
        self.assertEqual(set((x["docID"], x["id"]) for x in self.recs["eval"]["読む行"]), keys)
        for x in self.recs["eval"]["読む行"]:
            want = []
            if (x["docID"], x["id"]) in c.k3_keys():
                want.append(M.COND_K3)
            if (x["docID"], x["id"]) in c.k4_keys("P27"):
                want.append(M.COND_K4)
            self.assertEqual(x["条件"], want)
            self.assertEqual(c.read_by_key[(x["docID"], x["id"])]["条件"], want)
        self.assertEqual((M.COND_K3, M.COND_K4), (COND_K3, COND_K4))
        s = self.recs["eval"]["集計"][u"読む行"]
        self.assertEqual(s[u"数"], len(keys))
        self.assertEqual(s[u"条件ごと(重なる)"], {COND_K3: len(c.k3_keys()), COND_K4: len(c.k4_keys("P27"))})
        self.assertEqual(self.recs["eval"]["集計"][u"P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない行"], len(c.k3_keys()))

    def test_36_p27_and_p27e_grounded_rows_are_the_same_so_k4_rows_equal_the_p27_rows(self):
        c = self.calc
        self.assertEqual(c.k4_keys("P27"), c.k4_keys("P27E"))
        g = lambda p: c.keys_where(lambda k: c.st(k, p) == "GROUNDED")            # noqa: E731
        self.assertEqual(g("P27"), g("P27E"))
        self.assertTrue(self.recs["eval"]["集計"][u"P27 と P27E で GROUNDED の行が同じ"])

    def test_37_readings_equal_the_readings_record_own_summary_and_merge_rule(self):
        c, s = self.calc, self.recs["eval_readings"]["集計"]
        for r in c.readings:
            self.assertEqual((r["合わせた"]["側"], r["合わせた"]["細目"]), c.merged(r))
        side = collections.Counter(c.merged(r)[0] for r in c.readings)
        self.assertEqual(s[u"合わせた側の内訳"], dict((k, side.get(k, 0)) for k in (SIDE_SENT, SIDE_TOOL, UNSURE)))
        self.assertEqual(s[u"読む行"], len(c.readings))
        self.assertEqual(s[u"2 席の側が一致した行"][u"件"], sum(1 for r in c.readings if r["席1"]["側"] == r["席2"]["側"]))
        self.assertEqual(s[u"合わせた側が道具の行"], self.meas.v7b())
        self.assertEqual(s[u"合わせた札が文2の行"], sum(1 for r in c.readings if c.merged(r) == (SIDE_SENT, u"文2")))
        det = collections.Counter(c.merged(r)[1] for r in c.readings if c.merged(r)[0] == SIDE_TOOL and c.merged(r)[1] != UNSURE)
        self.assertEqual(s[u"合わせた細目が付いた道具の行"][u"細目の内訳"], dict(det))
        for cond, ks in ((COND_K3, c.k3_keys()), (COND_K4, c.k4_keys("P27"))):
            d = s[u"条件ごと(重なる)"][cond]
            self.assertEqual(d[u"行"], len(ks))
            self.assertEqual(d[u"合わせた側が道具の行"], len(c.tool_rows(ks)))

    def test_38_regress97_own_summary_equals_the_recomputed_numbers(self):
        rec, rg = self.e_recs["regress97"], self.regress
        self.assertEqual(rg.n_docs, 97)
        for p in ("P22", "P26"):
            self.assertEqual(rec[u"N-1"][p][u"byte が同じ書類"], rg.same[p])
        for pop in (POP67, POP30):
            s, mine = rec[u"集計"][pop], rg.pop[pop]
            self.assertEqual(s[u"書類"], mine["docs"])
            for p in ("P26", "P27", "P27E"):
                self.assertEqual(s[u"4 state"][p], mine["state"][p])
            self.assertEqual(s[u"P26 → P27"][u"state が違う行"], mine["a_state_moved"])
            self.assertEqual(s[u"P26 → P27"][u"他の向きの行"], mine["a_other_dir"])
            self.assertEqual(s[u"P26 → P27"][u"GROUNDED のまま pointer が替わる行"], mine["a_ptr_only_grounded"])
            self.assertEqual(s[u"P27 → P27E"][u"VALUE_MISMATCH に入る行(no_same_value → VALUE_MISMATCH)"], mine["b_to_vm"])
            self.assertEqual(s[u"P27 → P27E"][u"他の向きの行"], mine["b_other_dir"])


class TestJudgments(Base):
    """V・K・D・N の当否と採用の判定は記録の行から求まり、定数でない(記録を変えると変わる)。"""

    def test_40_the_judgment_the_records_give(self):
        # 外れは外れのまま残る。いまの記録が与える判定(この期待は記録が変われば、事実に直す = 封と結果を書き換えない)
        self.assertEqual(sorted(s for s, ok in self.dec["K"] if not ok), [])
        self.assertEqual(sorted(s for s, ok in self.dec["D"] if not ok), [])
        self.assertTrue(self.dec["adopt_P27E"] and self.dec["default_P27"])
        vrows, vv = judged_rows(self.meas, self.seal, V_ITEMS)
        self.assertEqual(sorted(s for s, ok in vv if not ok), ["V-2b"])
        nrows, nv = judged_rows(self.meas, self.seal, N_ITEMS)
        self.assertEqual(sorted(s for s, ok in nv if not ok), [])

    def _dec(self, fn, e_fn=None):
        recs = with_changes(self.recs, fn)
        e_recs = copy.deepcopy(self.e_recs)
        if e_fn:
            e_fn(e_recs)
        return decisions(measures_of(recs, e_recs, self.seal), self.seal)

    def _flip_t8(self, p, n, label, only_pass=False):
        def fn(r):
            k = 0
            for x in r["eval_inject"]["行"]:
                if x["型"] == "T8_REL" and all(x[q]["対応"] for q in P4) and x[p]["結果"] != label and k < n:
                    x[p]["結果"] = label
                    x[p]["state"] = "GROUNDED" if label == LABEL_PASS else x[p]["state"]
                    k += 1
        return fn

    def test_41_k1_follows_the_pass_rate_of_p27e(self):
        d = self._dec(self._flip_t8("P27E", 2, LABEL_PASS))                # 2/87 = 2.3% > 2%
        self.assertFalse(d["adopt_P27E"])
        self.assertIn(("K-1a", False), d["K"])
        d = self._dec(self._flip_t8("P27E", 1, LABEL_PASS))                # 1/87 = 1.1% ≤ 2%
        self.assertIn(("K-1a", True), d["K"])
        self.assertTrue(d["adopt_P27E"])

    def test_42_k1_t1_pass_of_p27e_is_a_hard_zero(self):
        def fn(r):
            for x in r["eval_inject"]["行"]:
                if x["型"] == "T1_VALUE" and all(x[q]["対応"] for q in P4):
                    x["P27E"]["結果"] = LABEL_PASS
                    break
        d = self._dec(fn)
        self.assertIn(("K-1b", False), d["K"])
        self.assertFalse(d["adopt_P27E"])
        self.assertTrue(d["default_P27"])                                    # P27 の側は動かない

    def test_43_k2_follows_the_named_rate_and_the_difference_from_p26(self):
        def fn(r):                                                         # P26 の名指しを増やして差を 35 ポイント未満にする
            k = 0
            for x in r["eval_inject"]["行"]:
                if x["型"] == "T8_REL" and all(x[q]["対応"] for q in P4) and x["P26"]["結果"] != LABEL_NAMED_ORIGINAL and k < 20:
                    x["P26"]["結果"] = LABEL_NAMED_ORIGINAL
                    k += 1
        d = self._dec(fn)
        self.assertIn(("K-2b", False), d["K"])
        self.assertIn(("K-2a", True), d["K"])
        self.assertFalse(d["adopt_P27E"])

    def _read_rows_with(self, n_k3_tool, sides=((SIDE_TOOL, u"道4"), (SIDE_TOOL, u"道4"))):
        """P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない行を増やし、読みを付ける(作り物の変更)。"""
        def fn(r):
            have = set((x["docID"], x["id"]) for x in r["eval_readings"]["行"])
            k3 = sum(1 for x in r["eval"]["読む行"] if M.COND_K3 in x["条件"])
            added = 0
            for c in r["eval"]["claim"]:
                if added >= n_k3_tool - k3:
                    break
                key = (c["docID"], c["id"])
                if key in have or c["P26"]["state"] == "VALUE_MISMATCH" or c["P26"]["state"] == "GROUNDED" or c["P27"]["state"] == "VALUE_MISMATCH":
                    continue
                c["P27E"]["state"] = "VALUE_MISMATCH"
                row = {"行": "%s:%s" % key, "docID": key[0], "id": key[1], "条件": [M.COND_K3],
                       "席1": {"側": sides[0][0], "細目": sides[0][1]}, "席2": {"側": sides[1][0], "細目": sides[1][1]},
                       "合わせた": {"側": sides[0][0], "細目": sides[0][1]}}
                r["eval_readings"]["行"].append(row)
                r["eval"]["読む行"].append({"行": row["行"], "docID": key[0], "id": key[1], "条件": [M.COND_K3]})
                added += 1
        return fn

    def test_44_k3_counts_tool_rows_and_the_threshold_is_at_two(self):
        d2 = self._dec(self._read_rows_with(2))
        self.assertIn(("K-3a", True), d2["K"])
        d3 = self._dec(self._read_rows_with(3))
        self.assertIn(("K-3a", False), d3["K"])
        self.assertFalse(d3["adopt_P27E"])

    def test_45_iv_a_row_whose_sides_agree_on_tool_but_whose_details_split_is_counted_as_tool(self):
        split = ((SIDE_TOOL, u"道4"), (SIDE_TOOL, u"道5"))
        d3 = self._dec(self._read_rows_with(3, sides=split))
        self.assertIn(("K-3a", False), d3["K"])                           # 細目が割れた行も道具に数える(3 行 > 2)
        # 側が割れた行は道具に数えない
        d3b = self._dec(self._read_rows_with(3, sides=((SIDE_TOOL, u"道4"), (SIDE_SENT, u"文1"))))
        self.assertIn(("K-3a", True), d3b["K"])
        self.assertEqual(Calc.side_of({"席1": {"側": SIDE_TOOL}, "席2": {"側": SIDE_TOOL}}), SIDE_TOOL)
        self.assertEqual(Calc.side_of({"席1": {"側": SIDE_TOOL}, "席2": {"側": SIDE_SENT}}), UNSURE)
        row = {"席1": {"側": SIDE_TOOL, "細目": u"道4"}, "席2": {"側": SIDE_TOOL, "細目": u"道5"}}
        self.assertEqual(Calc.merged(row), (SIDE_TOOL, UNSURE))
        self.assertEqual(Calc.side_of(row), SIDE_TOOL)

    def test_46_k3_vm_rate_difference_follows_the_one_point_threshold(self):
        def more_vm(n):
            def fn(r):
                k = 0
                for c in r["eval"]["claim"]:
                    if k < n and c["P27E"]["state"] != "VALUE_MISMATCH" and c["P26"]["state"] != "VALUE_MISMATCH":
                        c["P27E"]["state"] = "VALUE_MISMATCH"
                        k += 1
            return fn
        # P26 は 26 行・P27E は 24 行。P27E を 26 + 5 行にする(5/523 = 0.96 ポイント ≤ 1.0)と 26 + 6(1.15 ポイント)で境を跨ぐ
        ok = measures_of(with_changes(self.recs, more_vm(7)), self.e_recs, self.seal)           # 24 + 7 = 31 行 → 31/523 − 26/523 = 0.956
        self.assertTrue(in_band(parse_token(u"≤ P26 の率 + 1.0 ポイント"), ok.k3b()))
        bad = measures_of(with_changes(self.recs, more_vm(8)), self.e_recs, self.seal)          # 32 行 → 1.147
        self.assertFalse(in_band(parse_token(u"≤ P26 の率 + 1.0 ポイント"), bad.k3b()))

    def test_47_k4_counts_tool_rows_among_the_rows_that_left_grounded(self):
        def fn(r):                                                         # GROUNDED を離れる行を 4 行にして、4 行とも道具と読んだ
            have = set((x["docID"], x["id"]) for x in r["eval_readings"]["行"])
            k = sum(1 for x in r["eval"]["読む行"] if M.COND_K4 in x["条件"])
            for c in r["eval"]["claim"]:
                key = (c["docID"], c["id"])
                if k >= 4:
                    break
                if key in have or c["P26"]["state"] != "GROUNDED":
                    continue
                c["P27"]["state"] = c["P27E"]["state"] = "UNVERIFIABLE"
                row = {"行": "%s:%s" % key, "docID": key[0], "id": key[1], "条件": [M.COND_K4],
                       "席1": {"側": SIDE_TOOL, "細目": u"道4"}, "席2": {"側": SIDE_TOOL, "細目": u"道4"}, "合わせた": {"側": SIDE_TOOL, "細目": u"道4"}}
                r["eval_readings"]["行"].append(row)
                r["eval"]["読む行"].append({"行": row["行"], "docID": key[0], "id": key[1], "条件": [M.COND_K4]})
                k += 1
        d = self._dec(fn)
        self.assertIn(("K-4", False), d["K"])
        self.assertIn(("D-4", False), d["D"])
        self.assertFalse(d["adopt_P27E"] or d["default_P27"])

    def test_48_k5_follows_the_97_documents_of_the_regress_record(self):
        def e_fn(e):
            d = e["regress97"][u"書類"][0]
            d[u"出力の sha256(engine の欄を除く)"]["P26"] = "0" * 64                       # 1 書類が byte 一致でなくなった
        d = self._dec(lambda r: None, e_fn)
        self.assertIn(("K-5", False), d["K"])
        self.assertIn(("D-5", False), d["D"])
        self.assertFalse(d["adopt_P27E"] or d["default_P27"])

    def test_49_the_default_candidate_follows_the_vm_rows_of_p27_against_p26(self):
        def fn(r):
            k = 0
            for c in r["eval"]["claim"]:
                if k < 5 and c["P27"]["state"] != "VALUE_MISMATCH" and c["P26"]["state"] != "VALUE_MISMATCH" and c["P27E"]["state"] != "VALUE_MISMATCH":
                    c["P27"]["state"] = "VALUE_MISMATCH"
                    k += 1
        d = self._dec(fn)                                                  # P27 の VALUE_MISMATCH が 22 + 5 = 27 行 > P26 の 26 行
        self.assertIn(("D-3", False), d["D"])
        self.assertFalse(d["default_P27"])
        self.assertTrue(d["adopt_P27E"] or not d["adopt_P27E"])             # P27E の判定は K で決まる(ここでは見ない)

    def test_50_the_default_candidate_follows_the_four_n2_numbers(self):
        def e_fn(e):
            e["regress97"][u"書類"][0][u"4 state"]["P27"]["GROUNDED"] += 1
        d = self._dec(lambda r: None, e_fn)
        self.assertIn(("D-N2a", False), d["D"])
        self.assertFalse(d["default_P27"])
        self.assertTrue(d["adopt_P27E"])                                    # P27E の採用は N-2 を見ない

    def test_51_v5_counts_p27_not_p27e(self):
        """(v) V-5 は P27 で数える。P27E の GROUNDED だけを動かしても V-5 は動かず、P27 を動かせば動く。"""
        base = (self.meas.v5a(), self.meas.v5b())

        def p27e_only(r):
            for c in r["eval"]["claim"]:
                if c["P27E"]["state"] == "GROUNDED" and c["P26"]["state"] == "GROUNDED" and c["P27"]["state"] == "GROUNDED":
                    c["P27E"]["state"] = "UNVERIFIABLE"
                    break
        m = measures_of(with_changes(self.recs, p27e_only), self.e_recs, self.seal)
        self.assertEqual((m.v5a(), m.v5b()), base)

        def p27_only(r):
            for c in r["eval"]["claim"]:
                if c["P27"]["state"] == "GROUNDED" and c["P26"]["state"] == "GROUNDED":
                    c["P27"]["state"] = "UNVERIFIABLE"
                    break
        m = measures_of(with_changes(self.recs, p27_only), self.e_recs, self.seal)
        self.assertEqual(m.v5a(), base[0] + 1)

    def test_52_v_rows_move_with_the_records_and_the_verdict_text_follows_the_decision(self):
        # V-1c(P27 の通した率)を上げると V-1 が外れ、当否の表の行が変わる
        recs = with_changes(self.recs, self._flip_t8("P27", 4, LABEL_PASS))
        rows, vv = judged_rows(measures_of(recs, self.e_recs, self.seal), self.seal, V_ITEMS)
        self.assertIn(("V-1c", False), vv)
        self.assertIn(u"| V-1 | 外れ | V-1c |", verdict_rows(summarize(vv), V_IDS, u"V"))
        # 判定の字は decision から: 採用しない → 『採用しない』の字
        s_no = verdict_sentences({"adopt_P27E": False, "default_P27": False})
        s_yes = verdict_sentences({"adopt_P27E": True, "default_P27": True})
        self.assertEqual(s_no[0], u"判定(P27E): P27E を「外部の数の文に使う profile」として採用しない。")
        self.assertEqual(s_yes[0], u"判定(P27E): P27E を「外部の数の文に使う profile」として採用する。")
        self.assertEqual(s_no[1], u"判定(P27): P27 を「既定の候補」として記録しない。")
        self.assertEqual(s_yes[1], u"判定(P27): P27 を「既定の候補」として記録する。")
        self.assertNotEqual(s_no, s_yes)

    def test_54_the_denominator_is_the_four_profile_one_when_the_two_denominators_differ(self):
        """封 §3-2 の分母は 4 profile の全部で対応が付く行。この標本では各 profile の分母と同じ数になるので、1 行を P22 だけ対応が付かなくして 2 つの分母を割る。"""
        recs = copy.deepcopy(self.recs)
        victim = None
        for x in recs["eval_inject"]["行"]:
            if x["型"] == "T8_REL" and all(x[q]["対応"] for q in P4) and x["P27"]["結果"] == LABEL_NAMED_ORIGINAL:
                victim = x
                break
        victim["P22"] = {"対応": False, "結果": u"対応が付かない", "state": None, "reason": None}
        c = Calc(recs)
        m = measures_of(recs, self.e_recs, self.seal)
        all_n, p27_n = len(c.all_mapped("T8_REL")), len(c.mapped("T8_REL", "P27"))
        self.assertEqual((all_n, p27_n), (len(self.calc.all_mapped("T8_REL")) - 1, len(self.calc.mapped("T8_REL", "P27"))))
        self.assertEqual(m.v2c(), pct(c.count(c.all_mapped("T8_REL"), "P27", LABEL_NAMED_ORIGINAL), all_n))           # 封の分母
        self.assertNotEqual(m.v2c(), pct(c.count(c.mapped("T8_REL", "P27"), "P27", LABEL_NAMED_ORIGINAL), p27_n))      # 各 profile の分母ではない
        self.assertEqual(m.v1d(), pct(0, all_n))

    def test_53_n_items_follow_the_regress_record(self):
        def e_fn(e):                                                        # 動いた行の向きを 1 つ他の向きにする
            e["regress97"][u"動いた行"][POP67][u"P26 → P27"][0][u"後"][u"state"] = "VALUE_MISMATCH"
        recs, e_recs = copy.deepcopy(self.recs), copy.deepcopy(self.e_recs)
        e_fn(e_recs)
        rows, nv = judged_rows(measures_of(recs, e_recs, self.seal), self.seal, N_ITEMS)
        self.assertIn(("N-2i", False), nv)
        e_recs = copy.deepcopy(self.e_recs)
        e_recs["regress97"][u"動いた行"][POP30][u"P27 → P27E"].pop()           # P27E の名指しが 1 行減る(24 → 23: 幅の内)
        rows, nv = judged_rows(measures_of(recs, e_recs, self.seal), self.seal, N_ITEMS)
        self.assertIn(("N-3d", True), nv)
        e_recs["regress97"][u"動いた行"][POP30][u"P27 → P27E"] = e_recs["regress97"][u"動いた行"][POP30][u"P27 → P27E"][:14]      # 14 行 < 15
        rows, nv = judged_rows(measures_of(recs, e_recs, self.seal), self.seal, N_ITEMS)
        self.assertIn(("N-3d", False), nv)


class TestPins(Base):
    """独立監査の推奨 (i)〜(iii)(結果の門で script と engine の指紋と対象の全部と束の定数を縛る)。"""

    def _commit(self, key):
        return self.recs["eval"][key]

    def test_60_i_the_script_sha_in_the_records_is_the_script_at_head(self):
        for name, rec in self.recs.items():
            self.assertEqual(rec[u"この script の sha256"], sha256_hex(read_bytes(EVAL_SCRIPT_REL)), name)
            self.assertEqual(rec[u"この script の sha256"], sha256_hex(git_show("HEAD", "audit-core/" + EVAL_SCRIPT_REL)), name)
            self.assertEqual(rec[u"段 1 の測定の script(読むだけ・1 字も変えない)の sha256"], sha256_hex(git_show("HEAD", "audit-core/" + TUNE_SCRIPT_REL)), name)
            self.assertEqual(rec[u"97 書類の測定の script(rule_counts を読むだけ・1 字も変えない)の sha256"],
                             sha256_hex(git_show("HEAD", "audit-core/" + REGRESS_SCRIPT_REL)), name)
        self.assertEqual(self.e_recs["regress97"][u"この script の sha256"], sha256_hex(read_bytes(REGRESS_SCRIPT_REL)))

    def test_61_i_the_engine_fingerprint_in_the_records_is_the_engine_of_E(self):
        e = self._commit(u"E の commit")
        self.assertRegex(e, r"^[0-9a-f]{40}$")
        self.assertEqual(git("merge-base", "--is-ancestor", e, "HEAD").returncode, 0)
        fp_e = engine_fp_at(e)
        for name in ("eval", "eval_inject"):
            fp = self.recs[name][u"engine の指紋"]
            self.assertEqual(dict((k, fp[k]) for k in fp_e), fp_e, name)
        self.assertEqual(self.recs["eval_readings"][u"engine の指紋"], {})
        # E の記録(97 書類)が測った engine と同じ
        fp97 = self.e_recs["regress97"][u"engine の指紋"]
        self.assertEqual(dict((k, fp97[k]) for k in fp_e), fp_e)
        # E から作業木まで engine は動いていない(動いたら宣言された遷移が要る)。
        # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §4 (j) が宣言した遷移。動いてよいのは vocabulary.py と verify_document.py の 2 file だけで、
        # 作業木の指紋が段 2 の後の値(下の DEFAULT_P27_FP_TO)のときに限る。封が履歴に無ければ従来どおり 0 行。
        from adapters.xbrl import verify_document as VD
        now = VD.engine_fingerprint()
        moved = [l.decode("utf-8") for l in git("diff", "--name-only", e, "--", *ENGINE_TREES).stdout.split() if l]
        if now["adapter_xbrl_py_sha256"] != fp_e["adapter_xbrl_py_sha256"]:
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", "audit-core/" + DEFAULT_P27_SEAL_REL).stdout.split(), u"engine が動いているのに、遷移を宣言した封が履歴に無い")
            if now["adapter_xbrl_py_sha256"] == CAND_FP_TO:
                self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", "audit-core/" + CAND_SEAL_REL).stdout.split(), u"engine が動いているのに、遷移を宣言した封が履歴に無い")
                self.assertEqual(sorted(moved), ["audit-core/adapters/xbrl/report_customer.py", "audit-core/adapters/xbrl/verify_document.py", "audit-core/adapters/xbrl/vocabulary.py"])
            else:
                self.assertEqual(now["adapter_xbrl_py_sha256"], DEFAULT_P27_FP_TO)
                self.assertEqual(sorted(moved), ["audit-core/adapters/xbrl/verify_document.py", "audit-core/adapters/xbrl/vocabulary.py"])
            self.assertEqual(dict((k, now[k]) for k in fp_e if k != "adapter_xbrl_py_sha256"), dict((k, fp_e[k]) for k in fp_e if k != "adapter_xbrl_py_sha256"))
        else:
            self.assertEqual(moved, [])
            self.assertEqual(dict((k, now[k]) for k in fp_e), fp_e)

    def test_62_i_the_commits_in_the_three_records_agree_with_each_other(self):
        for key in (u"HEAD の commit", u"W の commit", u"T の commit", u"S2 の commit", u"E の commit"):
            self.assertEqual(len(set(r[key] for r in self.recs.values())), 1, key)
        for r in self.recs.values():
            pre = r[u"走る前の確かめ"]
            self.assertTrue(all(v is True for k, v in pre.items() if k not in (u"profile の一覧", u"既定の profile")))
            self.assertEqual(pre[u"profile の一覧"], list(P4))
            self.assertEqual(pre[u"既定の profile"], "P26")
            self.assertIs(r["dry_run"], False)
        self.assertEqual((self.recs["eval"]["backend"], self.recs["eval_inject"]["backend"], self.recs["eval_readings"]["backend"]), ("real", "real", u"なし"))

    def test_63_ii_the_targets_are_all_ten_documents_the_w_record_calls_evaluation(self):
        self.assertEqual(len(self.eval_ids), 10)
        for name, rec in self.recs.items():
            self.assertEqual(sorted(rec[u"対象の docID"]), sorted(self.eval_ids), name)
            self.assertIs(rec[u"対象は評価用の全部"], True)
            self.assertEqual(rec[u"評価用の件数"], 10)
            sh = dict((c["docID"], c["文の sha256"]) for c in self.w["会社"])
            self.assertEqual(rec[u"使った文の sha256"], dict((d, sh[d]) for d in self.eval_ids), name)
        # 判定の記録の会社・claim・読む行・注入の行は、評価用の 10 件だけ(調整用や区分の外は 1 件も無い)で、10 件が全部ある
        e = self.recs["eval"]
        self.assertEqual(sorted(c["docID"] for c in e[u"会社"]), sorted(self.eval_ids))
        self.assertEqual(set(x["docID"] for x in e["claim"]), set(self.eval_ids))
        self.assertEqual(set(x["docID"] for x in self.recs["eval_inject"]["行"]) - set(self.eval_ids), set())
        self.assertEqual(set(x["docID"] for x in self.recs["eval_readings"]["行"]) - set(self.eval_ids), set())
        self.assertEqual(set(self.calc.style), set(self.eval_ids))
        self.assertEqual(dict((c["docID"], c["型"]) for c in self.w["会社"] if c["区分"] == u"評価用"), self.calc.style)
        for d in self.tune_ids:
            self.assertNotIn(d, json.dumps(self.recs, ensure_ascii=False))

    def test_64_iii_the_dossier_constants_in_the_record_are_the_ones_in_the_script_and_the_reader_prompt_is_the_sealed_one(self):
        c = self.recs["eval"][u"束の P27・P27E の欄を足す形(script の定数)"]
        self.assertEqual(c, {"DOSSIER_P27_BLOCK": M.DOSSIER_P27_BLOCK, "DOSSIER_NO_CLAIM": M.DOSSIER_NO_CLAIM,
                             "DOSSIER_P27_FACTS_HEAD": M.DOSSIER_P27_FACTS_HEAD, "profile": list(M.DOSSIER_P27_PROFILES)})
        # script は HEAD の script と同じ(test_60)ので、定数は HEAD の字。字の形も見る(差し込みの置き場 {profile}・{body})
        self.assertIn("{profile}", M.DOSSIER_P27_BLOCK)
        self.assertIn("{body}", M.DOSSIER_P27_BLOCK)
        self.assertEqual(list(M.DOSSIER_P27_PROFILES), ["P27", "P27E"])
        out = self.recs["eval"][u"repo の外に置いたもの"][u"dossier"]
        self.assertEqual(out[u"読み手の指示文 reader_prompt.txt の sha256"], sha256_hex(M.PR.READER_PROMPT.encode("utf-8")))
        self.assertIs(out[u"読み手の指示文は封 §5-6 の字(prompts の READER_PROMPT)と同じ"], True)
        self.assertEqual(sorted(out[u"各 file の sha256"]), sorted(r["行"] for r in self.calc.readings))
        self.assertEqual(out[u"件数"], len(self.calc.readings))

    def test_65_the_p27_profiles_and_the_default_in_the_engine_are_the_sealed_ones(self):
        self.assertTrue(set(P4) <= set(M.V.PROFILES))
        # 2026-10-28: 既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)が履歴に在るときは P27(P26 は測った当時の既定)
        declared = bool(git("log", "--diff-filter=A", "--format=%H", "--", "audit-core/" + DEFAULT_P27_SEAL_REL).stdout.split())
        self.assertEqual(M.V.DEFAULT_PROFILE, "P27" if declared else "P26")
        self.assertIs(M.V.PROFILES["P27"].per_unit_counter_2026_10_27, True)
        self.assertIs(M.V.PROFILES["P27"].last_branch_relative_2026_10_27, False)
        self.assertIs(M.V.PROFILES["P27E"].last_branch_relative_2026_10_27, True)

    def test_66_cache_counts_are_unchanged_in_every_record(self):
        for name, rec in self.recs.items():
            c = rec[u"cache の前後"]
            self.assertIs(c[u"変化なし"], True)
            self.assertEqual(c[u"前"], c[u"後"])
            self.assertEqual((c[u"前"][u"既存の cache"][u"件数"], c[u"前"][u"ZIP の folder"][u"件数"]), (281, 40), name)
        c = self.e_recs["regress97"][u"cache の前後"]
        self.assertEqual((c[u"前"][u"edinet"][u"件数"], c[u"前"][u"edinet-fresh-2026-10-21"][u"件数"]), (281, 40))


class TestRecordContent(Base):
    @classmethod
    def setUpClass(cls):
        Base.setUpClass.__func__(cls)
        # 凍結の指紋は、この file の定数(JP_DIGEST)。作り直したら直す
        cls.fns = [M.T.record_key_leaks]

    def test_70_real_records_pass_every_content_check(self):
        for name, obj in self.recs.items():
            self.assertEqual(record_problems(name, obj, key_leak_fns=self.fns), [], name)

    def test_71_allowed_lists_cover_the_three_records_and_every_node_has_a_gloss(self):
        self.assertEqual(sorted(ALLOWED), sorted(EVAL_REC_REL))
        self.assertEqual(sorted(JP_DIGEST), sorted(EVAL_REC_REL))
        for name in ALLOWED:
            out, req = set(), set()
            PT._static_paths(ALLOWED[name], "", out, req)               # 欄ごとの説明(gloss)が空なら assert で落ちる
            self.assertTrue(req <= out)
            self.assertGreater(len(req), 5)

    def test_72_forbidden_names_are_absent_from_every_record(self):
        for name, obj in self.recs.items():
            bad = []
            PT._forbidden_name_problems(obj, "", bad)
            self.assertEqual(bad, [], name)
            names = set(PT.keys_of(obj))
            for f in (u"span", u"subject", u"value", u"recomputed", u"理由", u"道5の形", u"本文", u"抜粋"):
                self.assertNotIn(f, names, (name, f))

    def test_73_key_leaks_are_empty_and_the_checker_reacts_to_a_key_shaped_string(self):
        for name, obj in self.recs.items():
            self.assertEqual(M.T.record_key_leaks(obj), [], name)
        self.assertTrue(M.T.record_key_leaks({"x": "Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0xR"}))

    def test_74_W_record_is_the_same_as_the_blob_of_commit_W(self):
        w_commit = self.recs["eval"][u"W の commit"]
        blob = git_show(w_commit, "audit-core/" + W_REC_REL)
        w = json.loads(blob.decode("utf-8"))
        self.assertEqual(len(w["会社"]), 20)
        w_rows = dict((c["docID"], (c["区分"], c["型"], c["文の sha256"])) for c in w["会社"])
        now_rows = dict((c["docID"], (c["区分"], c["型"], c["文の sha256"])) for c in self.w["会社"])
        self.assertEqual(now_rows, w_rows)
        self.assertEqual(sum(1 for v in w_rows.values() if v[0] == u"評価用"), 10)
        self.assertEqual(sha256_hex(blob), sha256_hex(read_bytes(W_REC_REL)))             # file 全体も W の blob と同じ
        added = [c for c in git("log", "--diff-filter=A", "--format=%H", "--", "audit-core/" + W_REC_REL).stdout.decode("utf-8").split() if c]
        self.assertEqual(added, [w_commit])

    def test_75_fakes_turn_the_checks_red(self):
        FAKE_NAME = u"架空商事株式会社"
        FAKE_EXCERPT = u"当社の売上高は架空の数字で前期比を大きく伸ばした。"
        for name, obj in self.recs.items():
            self.assertEqual(record_problems(name, copy.deepcopy(obj), key_leak_fns=self.fns), [], name)
            fakes = []
            a = copy.deepcopy(obj)
            a[u"会社名"] = FAKE_NAME
            fakes.append(("新しい欄 会社名", a))
            a = copy.deepcopy(obj)
            a[u"限界を足した"] = [FAKE_EXCERPT]
            fakes.append(("新しい欄 抜粋の 1 文", a))
            a = copy.deepcopy(obj)
            first_list = [k for k, v in a.items() if isinstance(v, list) and v and isinstance(v[0], str)]
            if first_list:
                a[first_list[0]].append(FAKE_NAME)
                fakes.append(("既存の列に偽の会社名", a))
            a = copy.deepcopy(obj)
            a["step"] = a["step"] + FAKE_EXCERPT
            fakes.append(("既存の文に偽の抜粋", a))
            a = copy.deepcopy(obj)
            a["seal"] = u"Acme Holdings Ltd"
            fakes.append(("英字の偽の会社名", a))
            a = copy.deepcopy(obj)
            a["seal"] = u"Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0xR"
            fakes.append(("鍵の形の字", a))
            for label, bad in fakes:
                self.assertTrue(record_problems(name, bad, key_leak_fns=self.fns), (name, label))
        a = copy.deepcopy(self.recs["eval"])
        a["claim"][0]["P27"]["span"] = FAKE_EXCERPT
        bad = []
        PT._forbidden_name_problems(a, "", bad)
        self.assertTrue(bad)
        a = copy.deepcopy(self.recs["eval_readings"])
        a["行"][0][u"理由"] = FAKE_EXCERPT
        a["行"][0][u"道5の形"] = FAKE_NAME
        bad = []
        PT._forbidden_name_problems(a, "", bad)
        self.assertEqual(len(bad), 2)

    def test_76_a_missing_allowed_field_and_a_changed_jp_string_are_caught(self):
        for name, obj in self.recs.items():
            a = copy.deepcopy(obj)
            del a["seal"]
            self.assertTrue([p for p in record_problems(name, a, key_leak_fns=self.fns) if u"記録に無い欄" in p], name)
            a = copy.deepcopy(obj)
            a["step"] = a["step"] + u"。"
            self.assertTrue([p for p in record_problems(name, a, key_leak_fns=self.fns) if u"指紋" in p], name)
            # 許可の一覧から欄を 1 つ消すと、実物の記録が赤になる(許可の一覧が実物を覆っていること)
            allowed = dict(ALLOWED[name])
            del allowed[u"step"]
            self.assertTrue([p for p in record_problems(name, obj, allowed=allowed, key_leak_fns=self.fns) if u"許可の一覧に無い" in p], name)

    def test_77_each_layer_catches_what_the_others_do_not(self):
        for name, obj in self.recs.items():
            a = copy.deepcopy(obj)
            a["extra_field"] = "x1"
            p = record_problems(name, a, key_leak_fns=self.fns)
            self.assertEqual([x for x in p if u"許可の一覧に無い" in x], [u"欄が許可の一覧に無い: /extra_field"], name)
            self.assertEqual([x for x in p if u"許可の一覧に無い" not in x], [], name)
            a = copy.deepcopy(obj)
            a["step"] = a["step"].replace(u"P27", u"P28")
            p = record_problems(name, a, key_leak_fns=self.fns)
            self.assertEqual(len(p), 1, (name, p))
            self.assertIn(u"指紋", p[0])
            a = copy.deepcopy(obj)
            a["seal"] = u"Acme Holdings Ltd"
            p = record_problems(name, a, key_leak_fns=self.fns)
            self.assertEqual(len(p), 1, (name, p))
            self.assertIn(u"許可の形でない", p[0])
            a = copy.deepcopy(obj)
            a["seal"] = u"Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0xR"
            p = record_problems(name, a, key_leak_fns=self.fns)
            self.assertTrue(p and all(u"鍵らしい字" in x for x in p), (name, p))

    def test_78_the_gates_do_not_open_the_outside_material(self):
        """この門と順序の門の source に、repo の外の置き場(評価用の文・DB の応答・束・理由)を指す字と、~ の展開が無い。"""
        import ast
        needle = "/." + "cache"
        for rel in ("tests/measure/test_xbrl_p27_result.py", "tests/measure/test_xbrl_p27_order.py"):
            if not os.path.exists(os.path.join(ROOT, rel)):
                continue
            tree = ast.parse(read_text(rel))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(needle, node.value, rel)
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, ("expanduser", "environ"), rel)


if __name__ == "__main__":
    unittest.main()
