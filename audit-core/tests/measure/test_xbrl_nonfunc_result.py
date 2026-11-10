# -*- coding: utf-8 -*-
"""封 docs/XBRL_NONFUNCTIONAL_SEAL_2026-11-10.md(非機能の実測 NF)の結果の門。封 §0-2 の 4・§2・§3・§4・§6。

**この門が縛るもの**(封の門 ``test_xbrl_nonfunc_seal.py`` は封の字・script の定数・触らない file・配線・順序を縛る)

  a  記録の形: 禁止欄・会社名・pointer の字・鍵が無い / 頭(封・script の sha256・engine の指紋・機械が封 §0-1 の 1 と同じ・範囲・回数 3・profile・cache の前後・import 5 回・限界)/
     行の欄と型 / 回の数 = 3 × 材料 × profile(97 書類・AI の文 200 本は前の便の記録と同じ集合・同じ順)/ 回の間で claim の数が同じ / claim の数が前の便の記録と同じ(書類は P27・AI の文は P33E の数の claim)。
  b  判定: N-1〜N-9 を記録の行から**この門が別に書いた計算**で求め、script の ``build_E`` の値と同じ。各 N の端の当たり・すぐ外の外れ・分母 0 や値なしは外れ。
  c  結果の文書: ``<!-- 門:start pred -->``(N-1〜N-9 の表)と ``<!-- 門:start stats -->``(材料 × profile の数の表)を記録から作り直した表と一字ずつ照らす。散文の 3 桁の数に【門なし】。
  d  順序: 封 abe8f4d ⊏ script・門 ⊏ 記録 ⊑ 結果の文書。未 commit は赤(skip にしない)。
  e  宣言: docID を持つ記録は fresh_seal の LATER_NAMING_FILES に宣言する(記録が在るときだけ見る)。
  f  変異: 標本の記録で、a・b・c・d のどれを壊しても赤になる。

**時間を測り直して照らす試験は作らない**(封 §0-2 の 4)。小さな 1 書類の走り(``run --only``)は rc 0 と行の形・claim の数だけを見て、時間の値は見ない。
記録が無いときは本番の記録の試験を skip する(skip でも行が出ることを試験が確かめる)。標本の試験は記録が無くても走る。この file は docID の字を持たない。
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
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た ``sys.modules`` の名前は、読み込みの後に元の object へ戻す(7109c97 の直しと同じ形)。読み込んだ module 自身の名前は残す。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SG = load_module("tests/measure/test_xbrl_nonfunc_seal.py", "nonfunc_seal_gate_for_result")               # 封の門の部品。門としては走らせない
PSR = load_module("tests/measure/test_xbrl_pswap_result.py", "pswap_result_gate_for_nonfunc_result")      # 禁止欄・語・差し替えの部品。門としては走らせない
SC = SG.SC
PR = SG.PR
GEN, RUN, RM, R97 = SC.GEN, SC.RUN, SC.RM, SC.R97
SEAL_REL, DOC_REL, SCRIPT_REL, REC_REL = SC.SEAL_REL, SC.DOC_REL, SC.SCRIPT_REL, SC.REC_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
HIT, MISS = SC.HIT, SC.MISS
NOT_GATED = PR.NOT_GATED
FORBIDDEN_KEYS = PSR.FORBIDDEN_KEYS
COMPANY_WORDS = PSR.COMPANY_WORDS
POINTER_TEXT_RE = PSR.POINTER_TEXT_RE
FOR_RESULT_WORDS = PSR.FOR_RESULT_WORDS
DOCID_RE = SG.DOCID_RE
HAVE_CACHE = all(os.path.isdir(p) for p in RM.caches_all().values())
Patch = PSR.Patch
norm = PSR.norm
walk = PSR.walk
walk_strings = PSR.walk_strings
later_naming_files = PSR.later_naming_files
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
KINDS = (u"書類", u"AI の文")
PROFILES = ("P27", "P33E")
MB = 1048576
RANGE_FULL = u"全部(97 書類・AI の文 200 本)"
PB_REGRESS97_REL = "fixtures/xbrl/pbind/regress97_2026-11-06.json"
TPERIOD_MOVES_REL = "fixtures/xbrl/tperiod/moves_200_2026-11-09.json"
#: 記録の限界の字の頭(literal に留める。script の字を変えたら赤)
LIMITS_PIN = (u"数はこの 1 台", u"並行の処理", u"材料は手元の 97 書類", u"ru_maxrss は子 process", u"有料の API", u"import の時間は親が先に")
ROW_KEYS = (u"材料の種類", u"本の id", u"profile", u"回", u"時間", u"CPU 時間", u"ru_maxrss の前", u"ru_maxrss の後", u"claim の数", u"数の claim の数", u"zip の byte 数", u"文の byte 数")
#: 結果の文書の表の見出し(表 stats)
STATS_HEAD = u"| 材料 | profile | 回の数 | 時間の中央値(秒) | 時間の最大(秒) | 1 claim あたりの中央値(ms) | 後の ru_maxrss の中央値(MB) | 後の ru_maxrss の最大(MB) | 後 − 前の中央値(MB) |"
_SHA = {}


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def jload(rel):
    return json.loads(read(rel))


def sha256_rel(rel):
    u"""現物の sha256(門の中で file は変わらないので 1 回だけ読む)。"""
    if rel not in _SHA:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            _SHA[rel] = hashlib.sha256(fh.read()).hexdigest()
    return _SHA[rel]


def records_exist():
    if FORCE["no_records"]:
        return False
    return os.path.exists(os.path.join(ROOT, REC_REL))


# ---------------------------------------------------------------- 封の字から機械・engine の指紋(履歴から)
def seal_machine(seal):
    u"""封 §0-1 の 1 の機械の字(Apple M2・8 コア・メモリ 24 GiB・macOS 13.4・Python 3.9.6)から {CPU, コア, メモリ, OS, python}。"""
    m = re.search(r"\*\*機械\*\*: (Apple M\d)・(\d+) コア・メモリ (\d+) GiB・macOS ([\d.]+)・Python ([\d.]+)", seal)
    if not m:
        raise AssertionError(u"封 §0-1 の 1 の機械の字が読めない")
    return {"CPU": m.group(1), "コア": int(m.group(2)), "メモリ": int(m.group(3)) * 2 ** 30, "OS": "macOS-" + m.group(4), "python": m.group(5)}


_FP = []


def engine_fingerprint_at_seal():
    u"""封の commit の木の ``adapters/xbrl`` と ``core/py/audit_core`` の .py から作った指紋 {adapter_xbrl_py_sha256, core_py_sha256}。この便は engine を変えないので記録の指紋と同じ。"""
    if not _FP:
        s = SG.seal_commit_of()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            arc = subprocess.run(["git", "archive", s, PREFIX + "adapters/xbrl", PREFIX + "core/py/audit_core"], cwd=REPO, stdout=subprocess.PIPE, check=True)
            subprocess.run(["tar", "-x", "-C", d], input=arc.stdout, check=True)
            a, _na = SC.VD._py_digest(os.path.join(d, PREFIX, "adapters", "xbrl"))
            c, _nc = SC.VD._py_digest(os.path.join(d, PREFIX, "core", "py", "audit_core"))
        _FP.append({"adapter_xbrl_py_sha256": a, "core_py_sha256": c})
    return _FP[0]


# ---------------------------------------------------------------- 期待する材料(前の便の記録から。読むだけ)
class Expect(object):
    u"""記録の検査が照らす材料の期待。docs = 書類の id の列(順)・books = 本の名の列(順)・doc_claims / book_num = 前の便の記録の claim の数・reps・full(本番の全部か)。"""

    def __init__(self, docs, books, doc_claims, book_num, reps, full, snapshot=None):
        self.docs, self.books, self.doc_claims, self.book_num, self.reps, self.full = list(docs), list(books), dict(doc_claims), dict(book_num), reps, full
        self.snapshot = full if snapshot is None else snapshot                      # cache の前を現物の cache と照らすか(本番の記録だけ)


_REAL = {}


def real_expect(only=None, reps=3):
    u"""97 書類(``R97.make_jobs`` の順 = 前の便の記録の集合)と AI の文 200 本(tperiod の記録の本の順)。書類は P27 の claim の数(PB の記録)、本は P33E の数の claim(tperiod の記録)。"""
    if not _REAL:
        pb = jload(PB_REGRESS97_REL)
        mv = jload(TPERIOD_MOVES_REL)
        order = [j[0] for j in R97.make_jobs(("P27",))[0]]
        assert sorted(order) == sorted(r["docID"] for r in pb[u"書類"])
        _REAL["docs"] = order
        _REAL["doc_claims"] = dict((r["docID"], r[u"claims"]["P27"]) for r in pb[u"書類"])
        _REAL["books"] = [b[u"name"] for b in mv[u"本"]]
        _REAL["book_num"] = dict((b[u"name"], b[u"数の claim の数"]["P33E"]) for b in mv[u"本"])
        _REAL["book_doc"] = dict((b[u"name"], b[u"docID"]) for b in mv[u"本"])
    if only is None:
        return Expect(_REAL["docs"], _REAL["books"], _REAL["doc_claims"], _REAL["book_num"], reps, True)
    books = [n for n in _REAL["books"] if _REAL["book_doc"][n] == only]
    return Expect([only], books, _REAL["doc_claims"], _REAL["book_num"], reps, False)


# ---------------------------------------------------------------- 判定(この門が別に書いた計算。script の ``columns_from_rows`` を使わない)
def med(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def indep(rows, imports):
    u"""N-1〜N-9 の数を記録の行から数える(丸めない)。値が無いものは None。script の計算とは別の書き方。"""
    def sel(k, p):
        return [r for r in rows if r[u"材料の種類"] == k and r[u"profile"] == p]
    d27, d33, a33 = sel(u"書類", "P27"), sel(u"書類", "P33E"), sel(u"AI の文", "P33E")
    out = collections.OrderedDict()
    m27, m33 = med([r[u"時間"] for r in d27]), med([r[u"時間"] for r in d33])
    out["N-1"] = m27
    out["N-2"] = None if not m27 or m33 is None else m33 / m27
    out["N-3"] = max([r[u"時間"] for r in d27]) if d27 else None
    ms = [r[u"時間"] * 1000.0 / r[u"claim の数"] for r in d27 if r[u"claim の数"] > 0]
    out["N-4"] = med(ms) if d27 and len(ms) == len(d27) else None
    ta = [r[u"時間"] for r in a33]
    out["N-5"] = (med(ta), max(ta) if ta else None)
    mb = [r[u"ru_maxrss の後"] / float(MB) for r in rows]
    out["N-6"] = (med(mb), max(mb) if mb else None)
    groups = collections.OrderedDict()
    for r in rows:
        groups.setdefault((r[u"材料の種類"], r[u"本の id"], r[u"profile"]), []).append(r[u"時間"])
    sp = []
    ok = True
    for ts in groups.values():
        m = med(ts)
        if not m:
            ok = False
            break
        sp.append(100.0 * (max(ts) - min(ts)) / m)
    out["N-7"] = med(sp) if ok and sp else None
    out["N-8"] = med(imports) if imports else None
    out["N-9"] = (sum(r[u"claim の数"] for r in d27 if r[u"回"] == 1) if d27 else None, sum(r[u"数の claim の数"] for r in a33 if r[u"回"] == 1) if a33 else None)
    return out


def same_num(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def script_values(J):
    u"""script の判定の値を ``indep`` と同じ形(数か 2 つ組)にする。"""
    E = J[u"E"]
    out = collections.OrderedDict()
    for k in ("N-1", "N-2", "N-3", "N-4", "N-7", "N-8"):
        out[k] = E[k][u"値"]
    for k in ("N-5", "N-6"):
        out[k] = (E[k][u"値"][u"中央値"], E[k][u"値"][u"最大"])
    out["N-9"] = (E["N-9"][u"値"][u"書類"], E["N-9"][u"値"][u"AI の文"])
    return out


def expected_hit(k, v, B):
    u"""封の幅(``SC.seal_bounds``)と値 v から当たりか(この門が別に書いた比べ)。値なしは外れ。"""
    def inr(x, lo_hi):
        return x is not None and lo_hi[0] <= x <= lo_hi[1]

    def le(x, hi):
        return x is not None and x <= hi
    b = B[k]
    if k in ("N-1", "N-2", "N-4"):
        return inr(v, b)
    if k in ("N-3", "N-7", "N-8"):
        return le(v, b)
    if k in ("N-5", "N-6"):
        return inr(v[0], b[u"中央値"]) and le(v[1], b[u"最大"])
    return v[0] == b[u"書類"] and v[1] == b[u"AI の文"] and v[0] is not None


def judge_problems(rec, seal):
    u"""判定が記録から作り直せ、この門の別計算と同じか。壊れた記録は赤。"""
    try:
        J = SC.build_E(rec, seal)
        want = indep(rec[u"行"], rec[u"import の時間"][u"秒"])
        B = SC.seal_bounds(seal)
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"E"]) != list(SG.PRED_IDS):
        out.append(u"判定の行が N-1〜N-9 でない")
        return out
    got = script_values(J)
    for k in SG.PRED_IDS:
        a, b = got[k], want[k]
        same = all(same_num(x, y) for x, y in zip(a, b)) if isinstance(b, tuple) else same_num(a, b)
        if not same:
            out.append(u"%s: script の値 %r と別計算の値 %r が違う" % (k, a, b))
        if J[u"E"][k][u"判定"] != (HIT if expected_hit(k, b, B) else MISS):
            out.append(u"%s: 判定が封の幅と別計算の値から求めた判定と違う" % k)
    return out


# ---------------------------------------------------------------- 記録(a)
def clean_problems(rec):
    out = []
    bad = sorted(set(x for x in walk(rec) if x in FORBIDDEN_KEYS))
    if bad:
        out.append(u"記録に repo へ入れない欄がある: %s" % u",".join(bad))
    text = json.dumps(rec, ensure_ascii=False)
    for w in COMPANY_WORDS:
        if w in text:
            out.append(u"会社名らしい字がある")
    if any(POINTER_TEXT_RE.search(s) for s in walk_strings(rec)):
        out.append(u"記録に pointer の字(要素名・context)がある")
    try:
        with SC.key_check_nf(GEN):
            RUN.assert_clean(copy.deepcopy(rec))
    except GEN.Stop:
        out.append(u"鍵らしい字が記録に在る")
    if rec.get(u"key_leaks", []) != []:
        out.append(u"key_leaks が空でない")
    return out


def header_problems(rec, ex, seal):
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"封の名か commit が違う")
    if rec.get(u"この script の sha256") != sha256_rel(SCRIPT_REL):
        out.append(u"この script の sha256 が現物と違う")
    fp = rec.get(u"engine の指紋") or {}
    want = engine_fingerprint_at_seal()
    for name in want:
        if fp.get(name) != want[name]:
            out.append(u"engine の指紋 %s が封の commit の木から作り直した値と違う(この便は engine を変えない)" % name)
    if not re.fullmatch(r"[0-9a-f]{40}", str(rec.get(u"HEAD の commit") or u"")):
        out.append(u"HEAD の commit が 40 字の 16 進でない")
    m = rec.get(u"機械") or {}
    sm = seal_machine(seal)
    if not (isinstance(m.get(u"CPU の名"), str) and sm["CPU"] in m[u"CPU の名"]):
        out.append(u"機械の CPU の名が封 §0-1 の 1 と違う")
    if m.get(u"コア数") != sm["コア"] or m.get(u"メモリ(byte)") != sm["メモリ"]:
        out.append(u"機械のコア数かメモリが封 §0-1 の 1 と違う")
    if not (isinstance(m.get(u"OS"), str) and m[u"OS"].startswith(sm["OS"])) or m.get(u"python") != sm["python"]:
        out.append(u"機械の OS か python が封 §0-1 の 1 と違う")
    if not isinstance(m.get(u"ru_maxrss の単位"), str) or not m[u"ru_maxrss の単位"]:
        out.append(u"ru_maxrss の単位が書かれていない")
    if rec.get(u"範囲") != (RANGE_FULL if ex.full else rec.get(u"範囲")) or (not ex.full and u"本番の記録ではない" not in str(rec.get(u"範囲"))):
        out.append(u"範囲が全部でない(本番)か --only の印が無い(下見)")
    want_reps = 3 if ex.full else ex.reps
    if rec.get(u"回数") != want_reps or isinstance(rec.get(u"回数"), bool):
        out.append(u"回数が %d でない" % want_reps)
    if rec.get(u"profile") != list(PROFILES):
        out.append(u"profile が (P27, P33E) でない")
    cb = rec.get(u"cache の前後") or {}
    if cb.get(u"変化なし") is not True or cb.get(u"前") != cb.get(u"後"):
        out.append(u"cache の前後が同じでない")
    if ex.snapshot and HAVE_CACHE and cb.get(u"前") != norm(GEN.caches_snapshot(RM.caches_all())):
        out.append(u"cache の件数か名前が記録の前と違う")
    it = rec.get(u"import の時間") or {}
    secs = it.get(u"秒")
    if it.get(u"回数") != 5 or not isinstance(secs, list) or len(secs) != 5 or any(not isinstance(x, float) or x <= 0 for x in secs):
        out.append(u"import の時間が 5 回の正の秒でない")
    lim = list(rec.get(u"限界") or [])
    if len(lim) != len(LIMITS_PIN) or [x[:len(p)] for x, p in zip(lim, LIMITS_PIN)] != list(LIMITS_PIN):
        out.append(u"限界の字か数が留めた値と違う")
    return out


def row_problems(r, i):
    out = []
    tag = u"行 %d" % i
    if list(r) != list(ROW_KEYS):
        return [u"%s: 欄の名前か並びが違う" % tag]
    isint = lambda x: type(x) is int                                                           # noqa: E731  bool を int に数えない
    isflt = lambda x: type(x) in (int, float) and not isinstance(x, bool)                       # noqa: E731
    if r[u"材料の種類"] not in KINDS or r[u"profile"] not in PROFILES or not isinstance(r[u"本の id"], str) or not r[u"本の id"]:
        out.append(u"%s: 材料の種類・profile・本の id が違う" % tag)
    if not isint(r[u"回"]) or r[u"回"] < 1:
        out.append(u"%s: 回が 1 以上の整数でない" % tag)
    if not isflt(r[u"時間"]) or r[u"時間"] <= 0 or not isflt(r[u"CPU 時間"]) or r[u"CPU 時間"] < 0:
        out.append(u"%s: 時間が正でないか CPU 時間が負" % tag)
    if not (isint(r[u"ru_maxrss の前"]) and isint(r[u"ru_maxrss の後"]) and 0 < r[u"ru_maxrss の前"] <= r[u"ru_maxrss の後"]):
        out.append(u"%s: ru_maxrss の前後が 0 < 前 ≤ 後 の整数でない" % tag)
    if not (isint(r[u"claim の数"]) and isint(r[u"数の claim の数"]) and r[u"claim の数"] > 0 and 0 <= r[u"数の claim の数"] <= r[u"claim の数"]):
        out.append(u"%s: claim の数が正の整数でないか数の claim の数が多い" % tag)
    if not (isint(r[u"zip の byte 数"]) and r[u"zip の byte 数"] > 0):
        out.append(u"%s: zip の byte 数が正の整数でない" % tag)
    tb = r[u"文の byte 数"]
    if r[u"材料の種類"] == u"書類" and tb is not None:
        out.append(u"%s: 書類の文の byte 数が null でない(原文は text なし)" % tag)
    if r[u"材料の種類"] == u"AI の文" and not (isint(tb) and tb > 0):
        out.append(u"%s: AI の文の文の byte 数が正の整数でない" % tag)
    return out


def rows_problems(rec, ex):
    u"""行の集まりの検査: 形・材料の集合と順・回の数・回の間の一致・前の便の記録との claim の数。"""
    rows = rec.get(u"行")
    if not isinstance(rows, list) or not rows:
        return [u"行が無い"]
    out = []
    for i, r in enumerate(rows):
        out += row_problems(r, i)
    if out:
        return out
    docs = [(u"書類", d) for d in ex.docs]
    books = [(u"AI の文", b) for b in ex.books]
    want = []
    for rep in range(1, ex.reps + 1):
        for kind, ident in docs:
            for p in PROFILES:
                want.append((kind, ident, p, rep))
        for kind, ident in books:
            for p in PROFILES:
                want.append((kind, ident, p, rep))
    got = [(r[u"材料の種類"], r[u"本の id"], r[u"profile"], r[u"回"]) for r in rows]
    if len(got) != ex.reps * (len(docs) + len(books)) * len(PROFILES):
        out.append(u"行の数が 回数 × 材料 × profile と違う(%d)" % len(got))
    if got != want:
        out.append(u"行の (材料の種類, 本の id, profile, 回) の並びが (回, 材料の種類, 本, profile) の順の期待と違う")
        return out
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault((r[u"材料の種類"], r[u"本の id"], r[u"profile"]), []).append(r)
    for key, rs in by.items():
        if [x[u"回"] for x in rs] != list(range(1, ex.reps + 1)):
            out.append(u"%r: 回が 1.. で揃っていない" % (key,))
        if len(set((x[u"claim の数"], x[u"数の claim の数"], x[u"zip の byte 数"], x[u"文の byte 数"]) for x in rs)) != 1:
            out.append(u"%r: 回の間で claim の数か byte 数が違う" % (key,))
    for d in ex.docs:
        for p in PROFILES:
            if by[(u"書類", d, p)][0][u"claim の数"] != ex.doc_claims[d] and p == "P27":
                out.append(u"書類 %s: P27 の claim の数が前の便の記録と違う" % d)
    for b in ex.books:
        if by[(u"AI の文", b, "P33E")][0][u"数の claim の数"] != ex.book_num[b]:
            out.append(u"本 %s: P33E の数の claim の数が前の便の記録と違う" % b)
    if ex.full:
        if len(ex.docs) != 97 or len(ex.books) != 200 or len(set(ex.docs)) != 97 or len(set(ex.books)) != 200:
            out.append(u"本番の材料が 97 書類・200 本でない")
        if sum(ex.doc_claims[d] for d in ex.docs) != SC.seal_bounds(read(SEAL_REL))["N-9"][u"書類"]:
            out.append(u"前の便の記録の書類の claim の合計が封 N-9 と違う")
        if sum(ex.book_num[b] for b in ex.books) != SC.seal_bounds(read(SEAL_REL))["N-9"][u"AI の文"]:
            out.append(u"前の便の記録の本の数の claim の合計が封 N-9 と違う")
    return out


def record_problems(rec, ex, seal=None):
    u"""記録の検査(禁止欄・鍵・頭・行・判定の再計算)。問題の列。壊れた記録は例外で落とさず問題に数える。"""
    seal = seal if seal is not None else read(SEAL_REL)
    out = []

    def safe(label, fn, *a):
        try:
            return fn(*a)
        except Exception as e:                               # noqa: BLE001
            return [u"%s: 検査できない(%s)" % (label, type(e).__name__)]
    out += safe(u"clean", clean_problems, rec)
    out += safe(u"頭", header_problems, rec, ex, seal)
    out += safe(u"行", rows_problems, rec, ex)
    if not out:
        out += safe(u"判定", judge_problems, rec, seal)
    return out


# ---------------------------------------------------------------- 文書(c)
def indep_stats_lines(rows):
    u"""材料 × profile の数の表をこの門が別に書いた字で作る(script の ``render_stats`` を使わない)。"""
    lines = [STATS_HEAD, u"|---|---|---|---|---|---|---|---|---|"]
    for kind in KINDS:
        for p in PROFILES:
            rs = [r for r in rows if r[u"材料の種類"] == kind and r[u"profile"] == p]
            ts = sorted(r[u"時間"] for r in rs)
            pc = sorted(r[u"時間"] * 1000.0 / r[u"claim の数"] for r in rs)
            af = sorted(r[u"ru_maxrss の後"] / float(MB) for r in rs)
            df = sorted((r[u"ru_maxrss の後"] - r[u"ru_maxrss の前"]) / float(MB) for r in rs)
            lines.append(u"| %s | %s | %s | %.3f | %.3f | %.2f | %.1f | %.1f | %.1f |" % (kind, p, u"{:,}".format(len(rs)), med(ts), ts[-1], med(pc), med(af), af[-1], med(df)))
    return lines


def doc_problems(doc, rec, seal):
    J = SC.build_E(rec, seal)
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != SC.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("stats") != SC.render_stats(rec[u"行"]).split(u"\n"):
        out.append(u"表 stats が記録から作り直した表と違う")
    if got.get("stats") != indep_stats_lines(rec[u"行"]):
        out.append(u"表 stats がこの門が別に作った表と違う")
    for k in got:
        if k not in ("pred", "stats"):
            out.append(u"知らない表 %s" % k)
    if DOCID_RE.search(doc):
        out.append(u"docID が文書にある")
    for w in FOR_RESULT_WORDS:
        if w in doc:
            out.append(u"禁止語: " + w)
    out += [u"散文の数に【門なし】が無い: 行 %d %s" % x for x in PR.prose_problems(doc)]
    return out


# ---------------------------------------------------------------- 順序(d)
def chain_problems(root=REPO, seal_rel=SEAL_REL, seal_short=SEAL_COMMIT_SHORT, script_rels=SG.SCRIPT_RELS + SG.GATE_RELS, rec_rel=REC_REL, doc_rel=DOC_REL):
    u"""封 ⊏ script・門 ⊏ 記録 ⊑ 結果の文書(記録と結果の文書は同じ commit でよい)。未 commit は赤。"""
    out = list(PR.order_problems(root, PREFIX, seal_rel, seal_short, [], list(script_rels) + [rec_rel, doc_rel]))
    if out:
        return out
    last = {}
    for rel in list(script_rels) + [rec_rel, doc_rel]:
        last[rel] = PR.added_commits(root, PREFIX + rel)[-1]
    c_script = last[script_rels[0]]
    for rel in script_rels:
        if PR.is_anc(root, c_script, last[rel]):
            c_script = last[rel]
    c_rec, c_doc = last[rec_rel], last[doc_rel]
    if c_rec == c_script or not PR.is_anc(root, c_script, c_rec):
        out.append(u"RECORD_NOT_AFTER_SCRIPT")
    if not PR.is_anc(root, c_rec, c_doc):
        out.append(u"DOC_BEFORE_RECORD")
    return out


# ================================================================ 標本の記録(通信しない・cache を読まない・時間は作り物)
def sample_expect(reps=3, ndocs=3, nbooks=4, full=False):
    docs = ["D%d" % i for i in range(ndocs)]
    books = ["B%d_F1_m" % i for i in range(nbooks)]
    return Expect(docs, books, dict((d, 80 + 7 * i) for i, d in enumerate(docs)), dict((b, 60 + 5 * i) for i, b in enumerate(books)), reps, full, snapshot=False)


def mk_row(kind, ident, prof, rep, t, claims, num, rss_after, rss_before=10 * MB, zbytes=700000, tbytes=None):
    return collections.OrderedDict([(u"材料の種類", kind), (u"本の id", ident), (u"profile", prof), (u"回", rep), (u"時間", t), (u"CPU 時間", round(t * 0.98, 6)), (u"ru_maxrss の前", rss_before),
                                    (u"ru_maxrss の後", rss_after), (u"claim の数", claims), (u"数の claim の数", num), (u"zip の byte 数", zbytes), (u"文の byte 数", tbytes)])


def sample_rows(ex):
    u"""期待 ex の順で、時間・メモリが本ごと profile ごと回ごとに違う標本の行(揺れや中央値が別の式で壊れたとき値が変わるように、全部違う数にする)。"""
    rows = []
    for rep in range(1, ex.reps + 1):
        for i, d in enumerate(ex.docs):
            for j, p in enumerate(PROFILES):
                rows.append(mk_row(u"書類", d, p, rep, round(0.50 + 0.043 * i + 0.021 * j + 0.0113 * rep * (i + 1), 6), ex.doc_claims[d], ex.doc_claims[d] - 3, (95 + 3 * i + j + rep) * MB + 17 * rep))
        for i, b in enumerate(ex.books):
            for j, p in enumerate(PROFILES):
                rows.append(mk_row(u"AI の文", b, p, rep, round(0.55 + 0.051 * i + 0.032 * j + 0.0097 * rep * (i + 2), 6), ex.book_num[b] + 11 * (p == "P27") + 20 * j, ex.book_num[b] if p == "P33E" else ex.book_num[b] - 2,
                                   (110 + 4 * i + 2 * j + rep) * MB + 29 * rep, zbytes=800000 + i, tbytes=3000 + 11 * i))
    return rows


def sample_header(ex, seal):
    m = seal_machine(seal)
    cache = collections.OrderedDict([(u"edinet", collections.OrderedDict([(u"存在", True), (u"件数", 3), (u"名前の一覧の sha256", "0" * 64)]))])
    fp = dict(engine_fingerprint_at_seal())
    fp.update({"adapter_xbrl_py_files": 16, "core_py_files": 4, "git_commit": "1" * 40})
    h = collections.OrderedDict()
    h[u"seal"] = SEAL_REL
    h[u"封の commit"] = SEAL_COMMIT_SHORT
    h[u"step"] = u"標本"
    h[u"HEAD の commit"] = "2" * 40
    h[u"この script の sha256"] = sha256_rel(SCRIPT_REL)
    h[u"engine の指紋"] = fp
    h[u"機械"] = collections.OrderedDict([(u"CPU の名", m["CPU"]), (u"コア数", m["コア"]), (u"メモリ(byte)", m["メモリ"]), (u"OS", m["OS"] + "-13.4-arm64"), (u"python", m["python"]),
                                         (u"ru_maxrss の単位", u"byte(macOS)")])
    h[u"範囲"] = RANGE_FULL if ex.full else u"**--only の docID だけ(本番の記録ではない)**"
    h[u"回数"] = 3 if ex.full else ex.reps
    h[u"profile"] = list(PROFILES)
    h[u"cache の前後"] = collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)])
    h[u"import の時間"] = collections.OrderedDict([(u"回数", 5), (u"秒", [0.31, 0.32, 0.33, 0.34, 0.35])])
    return h


def sample_record(ex=None, seal=None):
    seal = seal if seal is not None else read(SEAL_REL)
    ex = ex or sample_expect()
    rec = sample_header(ex, seal)
    rec[u"欄"] = collections.OrderedDict([(u"時間", u"秒")])
    rec[u"行"] = sample_rows(ex)
    rec[u"限界"] = list(SC.LIMITS)
    rec[u"key_leaks"] = []
    return norm(rec)


def sample_doc(rec, seal):
    J = SC.build_E(rec, seal)
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", SC.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start stats -->", SC.render_stats(rec[u"行"]), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"1 回の中央値は表の数です。" + NOT_GATED, u""])


def crafted(**kw):
    u"""端の試験用の小さい行の集まり。既定は 書類 1 本・AI の文 1 本・各 profile 3 回で、全部の欄が幅の中。kw で時間(dict の kind/profile → 3 回の時間の列)・claim の数・メモリを替える。"""
    t = {(u"書類", "P27"): [0.6, 0.6, 0.6], (u"書類", "P33E"): [0.6, 0.6, 0.6], (u"AI の文", "P27"): [0.6, 0.6, 0.6], (u"AI の文", "P33E"): [0.6, 0.6, 0.6]}
    t.update(kw.get("times", {}))
    claims = kw.get("claims", 100)
    rss = kw.get("rss", 100 * MB)
    rows = []
    for rep in (1, 2, 3):
        for kind, ident in ((u"書類", "D0"), (u"AI の文", "B0")):
            for p in PROFILES:
                rows.append(mk_row(kind, ident, p, rep, t[(kind, p)][rep - 1], claims, claims - 5, rss, tbytes=(None if kind == u"書類" else 9)))
    return rows


def judged(rows, imports=None, seal=None):
    seal = seal if seal is not None else read(SEAL_REL)
    return SC.judge_from(SC.columns_from_rows(rows, imports if imports is not None else [0.3] * 5), seal)[u"E"]


# ================================================================ 試験
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_machine_in_the_seal_is_read_from_its_text(self):
        m = seal_machine(self.seal)
        self.assertEqual({"CPU": "Apple M2", "コア": 8, "メモリ": 24 * 2 ** 30, "OS": "macOS-13.4", "python": "3.9.6"}, m)
        with self.assertRaises(AssertionError):
            seal_machine(self.seal.replace(u"**機械**: ", u"**機械** ", 1))

    def test_a_2_the_engine_fingerprint_at_the_seal_commit_equals_the_working_tree_one(self):
        u"""この便は engine を変えない: 封の commit の木の指紋は作業木の ``VD.engine_fingerprint()`` と同じ。"""
        fp = SC.VD.engine_fingerprint()
        want = engine_fingerprint_at_seal()
        for name in want:
            self.assertEqual(want[name], fp[name], name)
            self.assertRegex(want[name], r"^[0-9a-f]{64}$")


class SampleRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.ex = sample_expect()
        cls.rec = sample_record(cls.ex, cls.seal)

    def test_b_1_the_sample_record_is_clean(self):
        self.assertEqual([], record_problems(copy.deepcopy(self.rec), self.ex, self.seal))
        self.assertEqual(3 * (3 + 4) * 2, len(self.rec[u"行"]))

    def test_b_2_the_sample_with_the_full_header_text_and_three_reps_is_also_clean(self):
        ex = sample_expect(full=True)
        # 全部の材料の個数と合計の検査は本番の材料だけに当てる。標本は個数が違うので、その 3 つだけが出る(頭・行・判定の検査は通る)
        self.assertEqual(sorted([u"本番の材料が 97 書類・200 本でない", u"前の便の記録の書類の claim の合計が封 N-9 と違う", u"前の便の記録の本の数の claim の合計が封 N-9 と違う"]),
                         sorted(record_problems(sample_record(ex, self.seal), ex, self.seal)))

    def _bad(self, mutate, want=None):
        rec = copy.deepcopy(self.rec)
        mutate(rec)
        got = record_problems(rec, self.ex, self.seal)
        self.assertNotEqual([], got)
        if want:
            self.assertTrue(any(want in x for x in got), got)
        return got

    def test_c_1_forbidden_keys_company_words_pointer_text_and_key_like_strings_turn_it_red(self):
        for k in (u"文", u"span", u"value", u"text", u"理由", u"根拠", u"context", u"pointers", u"label", u"element"):
            self.assertIn(k, FORBIDDEN_KEYS)
            self._bad(lambda r, k=k: r[u"行"][0].update({k: u"x"}), u"repo へ入れない欄")
        self._bad(lambda r: r[u"欄"].update({u"c": u"株式会社テスト"}), u"会社名")
        self._bad(lambda r: r[u"欄"].update({u"c": u"xbrl:jppfs_cor:X@CurrentYear"}), u"pointer")
        self._bad(lambda r: r[u"欄"].update({u"c": u"sk-ant-" + u"a" * 40}), u"鍵")
        self._bad(lambda r: r[u"欄"].update({u"c": u"A" * 40}), u"鍵")
        self._bad(lambda r: r.update({u"key_leaks": [u"鍵の形"]}), u"key_leaks")

    def test_c_2_the_header_checks_turn_red(self):
        self._bad(lambda r: r.update({u"seal": u"docs/x.md"}), u"封")
        self._bad(lambda r: r.update({u"封の commit": u"0000000"}), u"封")
        self._bad(lambda r: r.update({u"この script の sha256": u"0" * 64}), u"script の sha256")
        self._bad(lambda r: r[u"engine の指紋"].update({"adapter_xbrl_py_sha256": u"0" * 64}), u"engine の指紋")
        self._bad(lambda r: r[u"engine の指紋"].update({"core_py_sha256": u"0" * 64}), u"engine の指紋")
        self._bad(lambda r: r.update({u"HEAD の commit": u"abc"}), u"HEAD")
        self._bad(lambda r: r[u"機械"].update({u"CPU の名": u"Intel"}), u"CPU")
        self._bad(lambda r: r[u"機械"].update({u"コア数": 4}), u"コア数")
        self._bad(lambda r: r[u"機械"].update({u"メモリ(byte)": 8 * 2 ** 30}), u"メモリ")
        self._bad(lambda r: r[u"機械"].update({u"OS": u"macOS-14.0-arm64"}), u"OS")
        self._bad(lambda r: r[u"機械"].update({u"python": u"3.12.0"}), u"python")
        self._bad(lambda r: r[u"機械"].update({u"ru_maxrss の単位": u""}), u"単位")
        self._bad(lambda r: r.update({u"範囲": u"全部(97 書類・AI の文 200 本)"}), u"範囲")            # 下見の標本が本番の範囲を名乗る
        self._bad(lambda r: r.update({u"回数": 2}), u"回数")
        self._bad(lambda r: r.update({u"回数": True}), u"回数")
        self._bad(lambda r: r.update({u"profile": [u"P33E", u"P27"]}), u"profile")
        self._bad(lambda r: r.update({u"profile": [u"P27"]}), u"profile")
        self._bad(lambda r: r[u"cache の前後"].update({u"変化なし": False}), u"cache")
        self._bad(lambda r: r[u"cache の前後"].update({u"後": {}}), u"cache")
        self._bad(lambda r: r[u"import の時間"].update({u"秒": [0.3] * 4}), u"import")
        self._bad(lambda r: r[u"import の時間"].update({u"秒": [0.3, 0.3, 0.3, 0.3, 0]}), u"import")
        self._bad(lambda r: r[u"import の時間"].update({u"回数": 3}), u"import")
        self._bad(lambda r: r.update({u"限界": r[u"限界"][:-1]}), u"限界")
        self._bad(lambda r: r[u"限界"].__setitem__(0, u"x" + r[u"限界"][0]), u"限界")
        ex = sample_expect(full=True)
        rec = sample_record(ex, self.seal)
        rec[u"範囲"] = u"**--only の docID だけ(本番の記録ではない)**"
        self.assertTrue(any(u"範囲" in x for x in record_problems(rec, ex, self.seal)))                   # 本番の期待に下見の範囲
        rec = sample_record(ex, self.seal)
        rec[u"回数"] = 1
        self.assertTrue(any(u"回数" in x for x in record_problems(rec, ex, self.seal)))                   # 本番は回数 3 でなければ赤

    def test_c_3_the_row_checks_turn_red(self):
        self._bad(lambda r: r[u"行"].pop(), u"行の数")
        self._bad(lambda r: r[u"行"].append(copy.deepcopy(r[u"行"][-1])), u"行の数")
        self._bad(lambda r: r[u"行"].__setitem__(slice(0, 2), [r[u"行"][1], r[u"行"][0]]), u"並び")          # 順が違う(profile の入れ替え)
        self._bad(lambda r: r[u"行"].__setitem__(slice(2, 4), [r[u"行"][3], r[u"行"][2]]), u"並び")
        self._bad(lambda r: r[u"行"][0].update({u"本の id": u"D9"}), u"並び")
        self._bad(lambda r: r[u"行"][0].update({u"回": 2}), u"並び")
        self._bad(lambda r: r[u"行"][0].update({u"profile": u"P28"}), u"profile")
        self._bad(lambda r: r[u"行"][0].update({u"材料の種類": u"他"}), u"材料の種類")
        self._bad(lambda r: r[u"行"][0].pop(u"CPU 時間"), u"欄")
        self._bad(lambda r: r[u"行"][0].update({u"extra": 1}), u"欄")
        self._bad(lambda r: r[u"行"].__setitem__(0, collections.OrderedDict(reversed(list(r[u"行"][0].items())))), u"欄")
        self._bad(lambda r: r[u"行"][0].update({u"時間": 0}), u"時間")
        self._bad(lambda r: r[u"行"][0].update({u"時間": -0.1}), u"時間")
        self._bad(lambda r: r[u"行"][0].update({u"時間": True}), u"時間")
        self._bad(lambda r: r[u"行"][0].update({u"時間": u"0.5"}), u"時間")
        self._bad(lambda r: r[u"行"][0].update({u"CPU 時間": -1}), u"CPU")
        self._bad(lambda r: r[u"行"][0].update({u"ru_maxrss の後": r[u"行"][0][u"ru_maxrss の前"] - 1}), u"ru_maxrss")
        self._bad(lambda r: r[u"行"][0].update({u"ru_maxrss の前": 0}), u"ru_maxrss")
        self._bad(lambda r: r[u"行"][0].update({u"ru_maxrss の後": 1.5 * MB}), u"ru_maxrss")
        self._bad(lambda r: r[u"行"][0].update({u"claim の数": 0}), u"claim")
        self._bad(lambda r: r[u"行"][0].update({u"数の claim の数": r[u"行"][0][u"claim の数"] + 1}), u"数の claim")
        self._bad(lambda r: r[u"行"][0].update({u"zip の byte 数": 0}), u"zip")
        self._bad(lambda r: r[u"行"][0].update({u"文の byte 数": 5}), u"書類の文の byte 数")
        ai = [i for i, x in enumerate(self.rec[u"行"]) if x[u"材料の種類"] == u"AI の文"][0]
        self._bad(lambda r: r[u"行"][ai].update({u"文の byte 数": None}), u"AI の文の文の byte 数")

    def test_c_4_a_count_that_changes_between_reps_or_differs_from_the_previous_record_turns_red(self):
        n = len(self.rec[u"行"])
        self._bad(lambda r: r[u"行"][n - 1].update({u"claim の数": r[u"行"][n - 1][u"claim の数"] + 1}), u"回の間")                 # 最後の回だけ違う
        self._bad(lambda r: r[u"行"][n - 1].update({u"zip の byte 数": 1}), u"回の間")
        self._bad(lambda r: [x.update({u"claim の数": x[u"claim の数"] + 1, u"数の claim の数": x[u"数の claim の数"] + 1}) for x in r[u"行"] if x[u"本の id"] == u"D0" and x[u"profile"] == "P27"], u"前の便の記録")
        self._bad(lambda r: [x.update({u"数の claim の数": x[u"数の claim の数"] - 1}) for x in r[u"行"] if x[u"本の id"] == u"B1_F1_m" and x[u"profile"] == "P33E"], u"前の便の記録")

    def test_c_5_a_rep_that_is_missing_or_repeated_turns_red(self):
        rows = copy.deepcopy(self.rec[u"行"])
        rec = copy.deepcopy(self.rec)
        rec[u"行"] = [x for x in rows if not (x[u"本の id"] == u"D1" and x[u"回"] == 3)]
        self.assertNotEqual([], record_problems(rec, self.ex, self.seal))
        rec[u"行"] = rows + [x for x in rows if x[u"本の id"] == u"D1" and x[u"回"] == 3]
        self.assertNotEqual([], record_problems(rec, self.ex, self.seal))


class JudgeEdgeTest(unittest.TestCase):
    u"""N-1〜N-9 の端: 幅の端は当たり・すぐ外は外れ。分母 0・値なしは外れ。小さい行(``crafted``)から script の判定を通す(行から数えて判定する経路ごと)。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def one(self, k, rows, imports=None):
        return judged(rows, imports, self.seal)[k]

    def test_j_0_the_crafted_base_is_inside_every_range_except_n9(self):
        E = judged(crafted(), None, self.seal)
        for k in SG.PRED_IDS:
            if k != "N-9":
                self.assertEqual(HIT, E[k][u"判定"], k)
        self.assertEqual(MISS, E["N-9"][u"判定"])                              # 材料が 97 書類・200 本でないので外れ

    def t(self, kind, prof, ts, **kw):
        times = {(kind, prof): ts}
        return crafted(times=times, **kw)

    def test_j_1_n1_median_of_the_p27_documents(self):
        for ts, hit in (([0.4, 0.4, 0.4], True), ([0.3999, 0.3999, 0.3999], False), ([1.0, 1.0, 1.0], True), ([1.0001, 1.0001, 1.0001], False), ([0.1, 0.5, 5.0], True), ([0.1, 0.1, 5.0], False)):
            self.assertEqual(HIT if hit else MISS, self.one("N-1", self.t(u"書類", "P27", ts))[u"判定"], ts)

    def test_j_2_n2_ratio_of_the_p33e_median_to_the_p27_median(self):
        for p33, hit in ((0.9, True), (0.8999, False), (1.15, True), (1.1501, False)):
            rows = crafted(times={(u"書類", "P27"): [1.0, 1.0, 1.0], (u"書類", "P33E"): [p33] * 3})
            self.assertEqual(HIT if hit else MISS, self.one("N-2", rows)[u"判定"], p33)
        zero = crafted(times={(u"書類", "P27"): [0.0, 0.0, 0.0]})
        self.assertEqual(MISS, self.one("N-2", zero)[u"判定"])                    # P27 の中央値 0 = 分母 0 は外れ(値なし)
        self.assertIsNone(SC.columns_from_rows(zero, [0.3])["N-2"])
        self.assertIsNone(indep(zero, [0.3])["N-2"])

    def test_j_3_n3_maximum_of_the_p27_documents(self):
        for ts, hit in (([0.5, 0.5, 2.0], True), ([0.5, 0.5, 2.0001], False), ([2.0, 0.5, 0.5], True), ([0.5, 2.1, 0.5], False)):
            self.assertEqual(HIT if hit else MISS, self.one("N-3", self.t(u"書類", "P27", ts))[u"判定"], ts)

    def test_j_4_n4_median_of_the_time_per_claim_in_ms(self):
        lo = self.t(u"書類", "P27", [3.0, 3.0, 3.0], claims=1000)
        hi = self.t(u"書類", "P27", [9.0, 9.0, 9.0], claims=1000)
        self.assertEqual(3.0, indep(lo, [0.3])["N-4"])
        self.assertEqual(9.0, indep(hi, [0.3])["N-4"])
        self.assertEqual(HIT, self.one("N-4", lo)[u"判定"])
        self.assertEqual(HIT, self.one("N-4", hi)[u"判定"])
        self.assertEqual(MISS, self.one("N-4", self.t(u"書類", "P27", [2.999, 2.999, 2.999], claims=1000))[u"判定"])
        self.assertEqual(MISS, self.one("N-4", self.t(u"書類", "P27", [9.001, 9.001, 9.001], claims=1000))[u"判定"])
        zero = crafted()
        zero[0][u"claim の数"] = 0
        self.assertEqual(MISS, self.one("N-4", zero)[u"判定"])                    # 分母 0 は外れ(値なし)
        self.assertIsNone(SC.columns_from_rows(zero, [0.3])["N-4"])

    def test_j_5_n5_median_and_maximum_of_the_ai_texts_under_p33e(self):
        for ts, hit in (([0.4, 0.4, 0.4], True), ([0.3999, 0.3999, 0.3999], False), ([1.0, 1.0, 1.0], True), ([1.0001, 1.0001, 1.0001], False),
                        ([0.6, 0.6, 2.5], True), ([0.6, 0.6, 2.5001], False)):
            self.assertEqual(HIT if hit else MISS, self.one("N-5", self.t(u"AI の文", "P33E", ts))[u"判定"], ts)
        self.assertEqual(HIT, self.one("N-5", self.t(u"AI の文", "P27", [9.0, 9.0, 9.0]))[u"判定"])                       # P27 の AI の文は遅くても N-5 は動かない

    def test_j_6_n6_median_and_maximum_of_the_rss_after_the_call(self):
        def rows_rss(vals):
            rows = crafted()
            for r, v in zip(rows, vals):
                r[u"ru_maxrss の後"] = v
            return rows
        n = len(crafted())
        for med_mb, hit in ((70, True), (69.9, False), (150, True), (150.1, False)):
            rows = rows_rss([int(med_mb * MB)] * n)
            self.assertEqual(HIT if hit else MISS, self.one("N-6", rows)[u"判定"], med_mb)
        rows = rows_rss([100 * MB] * (n - 1) + [250 * MB])
        self.assertEqual(HIT, self.one("N-6", rows)[u"判定"])
        rows = rows_rss([100 * MB] * (n - 1) + [int(250.1 * MB)])
        self.assertEqual(MISS, self.one("N-6", rows)[u"判定"])

    def test_j_7_n7_median_of_the_spreads_over_all_book_profile_groups(self):
        def spread_rows(frac_hi):
            rows = crafted()
            for r in rows:
                if r[u"回"] == 3:
                    r[u"時間"] = 0.6 * (1.0 + frac_hi)
            return rows
        self.assertEqual(HIT, self.one("N-7", spread_rows(0.0))[u"判定"])
        self.assertEqual(HIT, self.one("N-7", spread_rows(0.099))[u"判定"])
        self.assertEqual(MISS, self.one("N-7", spread_rows(0.101))[u"判定"])
        self.assertAlmostEqual(9.9, indep(spread_rows(0.099), [0.3])["N-7"], places=6)
        # 中央値(全部の群の揺れの中央値)なので、群の少数が大きく揺れても外れにならない(4 群のうち 1 群が揺れても中央値は 0・2 群が揺れると中央値は揺れの半分)
        def swing(groups):
            rows = crafted()
            for r in rows:
                if r[u"回"] == 3 and (r[u"材料の種類"], r[u"profile"]) in groups:
                    r[u"時間"] = 0.6 * 1.5
            return rows
        self.assertEqual(HIT, self.one("N-7", swing({(u"書類", "P27")}))[u"判定"])
        self.assertAlmostEqual(0.0, indep(swing({(u"書類", "P27")}), [0.3])["N-7"])
        self.assertEqual(MISS, self.one("N-7", swing({(u"書類", "P27"), (u"AI の文", "P27")}))[u"判定"])
        self.assertAlmostEqual(25.0, indep(swing({(u"書類", "P27"), (u"AI の文", "P27")}), [0.3])["N-7"], places=6)
        self.assertEqual(MISS, self.one("N-7", spread_rows(0.5))[u"判定"])
        zero = crafted(times={(u"書類", "P27"): [0.0, 0.0, 0.0]})
        self.assertEqual(MISS, self.one("N-7", zero)[u"判定"])                    # 中央値 0 の群 = 分母 0 は外れ(値なし)
        self.assertIsNone(SC.columns_from_rows(zero, [0.3])["N-7"])

    def test_j_8_n8_median_of_the_five_import_times(self):
        self.assertEqual(HIT, self.one("N-8", crafted(), [1.5] * 5)[u"判定"])
        self.assertEqual(MISS, self.one("N-8", crafted(), [1.5001] * 5)[u"判定"])
        self.assertEqual(HIT, self.one("N-8", crafted(), [0.1, 0.2, 1.5, 9.0, 9.0])[u"判定"])
        self.assertEqual(MISS, self.one("N-8", crafted(), [0.1, 0.2, 1.6, 1.7, 9.0])[u"判定"])
        self.assertEqual(MISS, self.one("N-8", crafted(), [0.1, 9.0, 9.0, 9.0, 0.2])[u"判定"])
        self.assertEqual(MISS, self.one("N-8", crafted(), [])[u"判定"])                 # 値なしは外れ

    def test_j_9_n9_totals_must_equal_the_sealed_numbers_exactly(self):
        B = SC.seal_bounds(self.seal)["N-9"]
        self.assertEqual((11722, 16588), (B[u"書類"], B[u"AI の文"]))
        for dv, av, hit in ((11722, 16588, True), (11721, 16588, False), (11723, 16588, False), (11722, 16587, False), (11722, 16589, False)):
            E = SC.judge_from(dict(SC.columns_from_rows(crafted(), [0.3]), **{"N-9": collections.OrderedDict([(u"書類", dv), (u"AI の文", av)])}), self.seal)[u"E"]
            self.assertEqual(HIT if hit else MISS, E["N-9"][u"判定"], (dv, av))
        E = SC.judge_from(dict(SC.columns_from_rows(crafted(), [0.3]), **{"N-9": collections.OrderedDict([(u"書類", None), (u"AI の文", 16588)])}), self.seal)[u"E"]
        self.assertEqual(MISS, E["N-9"][u"判定"])
        # 回 1 の行だけを足す(3 回足さない)
        rows = crafted(claims=100)
        c = SC.columns_from_rows(rows, [0.3])["N-9"]
        self.assertEqual((100, 95), (c[u"書類"], c[u"AI の文"]))

    def test_j_10_empty_populations_are_all_misses_not_errors(self):
        E = judged([], [0.3] * 5, self.seal)
        for k in SG.PRED_IDS:
            self.assertEqual(HIT if k == "N-8" else MISS, E[k][u"判定"], k)                  # N-8 は行に依らない(import の時間)ので材料が無くても当たりうる
        only_ai = [r for r in crafted() if r[u"材料の種類"] == u"AI の文"]
        E = judged(only_ai, [0.3] * 5, self.seal)
        for k in ("N-1", "N-2", "N-3", "N-4"):
            self.assertEqual(MISS, E[k][u"判定"], k)
        self.assertEqual(HIT, E["N-5"][u"判定"])

    def test_j_11_the_bounds_come_from_the_seal_text(self):
        seal2 = self.seal.replace("| 0.4〜1.0 秒 |", "| 0.4〜0.5 秒 |", 1)
        self.assertNotEqual(seal2, self.seal)
        self.assertEqual(MISS, judged(crafted(), None, seal2)["N-1"][u"判定"])               # 中央値 0.6 が新しい幅の外
        self.assertEqual(HIT, judged(crafted(), None, self.seal)["N-1"][u"判定"])


class SampleJudgeTest(unittest.TestCase):
    u"""標本の記録(行ごとに違う数)で、script の判定の値がこの門の別計算と同じ。値が 1 つの式の違いで動くように標本を作ってある。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.ex = sample_expect(reps=3, ndocs=4, nbooks=5)
        cls.rec = sample_record(cls.ex, cls.seal)

    def test_s_1_script_values_equal_the_independent_computation(self):
        self.assertEqual([], judge_problems(self.rec, self.seal))
        want = indep(self.rec[u"行"], self.rec[u"import の時間"][u"秒"])
        got = script_values(SC.build_E(self.rec, self.seal))
        for k in SG.PRED_IDS:
            b = want[k]
            self.assertTrue(all(same_num(x, y) for x, y in zip(got[k], b)) if isinstance(b, tuple) else same_num(got[k], b), k)
        self.assertGreater(want["N-7"], 0)                                                # 揺れは 0 でない標本
        self.assertNotAlmostEqual(want["N-1"], want["N-3"])                                # 中央値と最大が違う標本

    def test_s_4_the_gate_and_the_script_agree_at_each_edge_of_every_range(self):
        u"""幅の端(当たり)とすぐ外(外れ)の行を持つ最小の記録で、``judge_problems``(script の判定とこの門の別計算の照らし)が空。門の比べ(``expected_hit``)の端の向きの誤りも拾う。"""
        def rec_of(rows, imports=(0.3,) * 5):
            return {u"行": rows, u"import の時間": {u"秒": list(imports)}}
        cases = [crafted(times={(u"書類", "P27"): [t] * 3}) for t in (0.4, 0.3999, 1.0, 1.0001, 2.0, 2.0001)]
        cases += [crafted(times={(u"書類", "P27"): [1.0] * 3, (u"書類", "P33E"): [t] * 3}) for t in (0.9, 0.8999, 1.15, 1.1501)]
        cases += [crafted(times={(u"書類", "P27"): [t] * 3}, claims=1000) for t in (3.0, 2.999, 9.0, 9.001)]
        cases += [crafted(times={(u"AI の文", "P33E"): [0.6, 0.6, t]}) for t in (2.5, 2.5001)]
        cases += [crafted(times={(u"AI の文", "P33E"): [t] * 3}) for t in (0.4, 0.3999, 1.0, 1.0001)]
        n = len(crafted())
        for v in (70 * MB, 69 * MB, 150 * MB, 151 * MB):
            rows = crafted()
            for r in rows:
                r[u"ru_maxrss の後"] = v
            cases.append(rows)
        for v in (250 * MB, 251 * MB):
            rows = crafted()
            rows[-1][u"ru_maxrss の後"] = v
            cases.append(rows)
        self.assertEqual(n, len(cases[-1]))
        for rows in cases:
            self.assertEqual([], judge_problems(rec_of(rows), self.seal))
        for imports in ([1.5] * 5, [1.5001] * 5, [1.4999] * 5):
            self.assertEqual([], judge_problems(rec_of(crafted(), imports), self.seal))
        # 端の判定がこの門の比べと script で食い違う標本を作れること(門が端を見ていることの確認): 範囲の外の値で当たりを返す script の写しは食い違う
        src = read(SCRIPT_REL)
        mod = types_module(src.replace(u"return x is not None and x <= hi", u"return x is not None and x < hi"))
        with Patch() as pt:
            pt.set(SC, "atmost", mod.atmost)
            self.assertNotEqual([], judge_problems(rec_of(crafted(times={(u"書類", "P27"): [2.0] * 3})), self.seal))

    def test_s_2_a_changed_statistic_in_a_copy_of_the_script_turns_the_check_red(self):
        u"""script の計算を 1 つずつ壊した写し(同じ file の字から作る)で、``judge_problems`` が赤になる。"""
        src = read(SCRIPT_REL)
        muts = (
            (u"m = median(ts)\n        if not m:\n            return None\n        out.append((max(ts) - min(ts)) / m)", u"m = max(ts)\n        if not m:\n            return None\n        out.append((max(ts) - min(ts)) / m)"),   # 揺れを最大で割る
            (u"out.append((max(ts) - min(ts)) / m)", u"out.append((max(ts) - min(ts)) / m * 2)"),
            (u"c[\"N-3\"] = max(t27) if t27 else None", u"c[\"N-3\"] = median(t27) if t27 else None"),
            (u"c[\"N-2\"] = (m33 / m27)", u"c[\"N-2\"] = (m27 / m33)"),
            (u"r[u\"時間\"] / r[u\"claim の数\"] * 1000.0 for r in d27", u"r[u\"時間\"] / r[u\"数の claim の数\"] * 1000.0 for r in d27"),
            (u"rss = [r[u\"ru_maxrss の後\"] / float(MB) for r in rows]", u"rss = [(r[u\"ru_maxrss の後\"] - r[u\"ru_maxrss の前\"]) / float(MB) for r in rows]"),
            (u"c[\"N-8\"] = median(imports) if imports else None", u"c[\"N-8\"] = max(imports) if imports else None"),
            (u"c[\"N-7\"] = (median(sp) * 100.0) if sp else None", u"c[\"N-7\"] = (max(sp) * 100.0) if sp else None"),
            (u"if r[u\"回\"] == 1) if d27 else None", u"if r[u\"回\"] <= 3) if d27 else None"),
            (u"a33 = select(rows, KIND_AI, \"P33E\")", u"a33 = select(rows, KIND_AI, \"P27\")"),
            (u"d27, d33 = select(rows, KIND_DOC, \"P27\"), select(rows, KIND_DOC, \"P33E\")", u"d33, d27 = select(rows, KIND_DOC, \"P27\"), select(rows, KIND_DOC, \"P33E\")"),
        )
        for old, new in muts:
            self.assertEqual(1, src.count(old), old)
            mod = types_module(src.replace(old, new))
            with Patch() as pt:
                pt.set(SC, "columns_from_rows", mod.columns_from_rows)
                pt.set(SC, "spreads", mod.spreads)
                self.assertNotEqual([], judge_problems(self.rec, self.seal), old)
        self.assertEqual([], judge_problems(self.rec, self.seal))

    def test_s_3_a_changed_judgement_in_a_copy_of_the_script_turns_the_edge_probes_red(self):
        u"""判定の式(幅の比べ・当たりにする条件)を 1 つずつ壊した写しは、端の標本(幅の端・外・N-9 の片方だけ一致)のどれかで本物と判定が変わる。"""
        src = read(SCRIPT_REL)

        def probes(mod):
            res = []
            for rows, imports in ((crafted(times={(u"書類", "P27"): [0.4, 0.4, 0.4]}), [1.5] * 5), (crafted(times={(u"書類", "P27"): [0.5, 0.5, 5.0]}), [0.3] * 5), (crafted(), [0.3] * 5), ([], [0.3] * 5)):
                cols = SC.columns_from_rows(rows, imports)
                res.append(tuple(v[u"判定"] for v in mod.judge_from(cols, self.seal)[u"E"].values()))
                cols9 = dict(cols, **{"N-9": collections.OrderedDict([(u"書類", 11722), (u"AI の文", 1)])})
                res.append(tuple(v[u"判定"] for v in mod.judge_from(cols9, self.seal)[u"E"].values()))
            return res
        base = probes(SC)
        self.assertEqual(base, probes(types_module(src)))                                  # 壊していない写しは本物と同じ
        muts = ((u"put(\"N-3\", atmost(cols[\"N-3\"], B[\"N-3\"]), cols[\"N-3\"])", u"put(\"N-3\", True, cols[\"N-3\"])"),
                (u"put(\"N-1\", within(cols[\"N-1\"], B[\"N-1\"]), cols[\"N-1\"])", u"put(\"N-1\", False, cols[\"N-1\"])"),
                (u"return x is not None and lo_hi[0] <= x <= lo_hi[1]", u"return x is not None and lo_hi[0] < x < lo_hi[1]"),
                (u"return x is not None and x <= hi", u"return x is not None and x < hi"),
                (u"v9[u\"書類\"] == b9[u\"書類\"] and v9[u\"AI の文\"] == b9[u\"AI の文\"]", u"v9[u\"書類\"] == b9[u\"書類\"]"),
                (u"return x is not None and lo_hi[0] <= x <= lo_hi[1]", u"return x is None or lo_hi[0] <= x <= lo_hi[1]"))
        for old, new in muts:
            self.assertEqual(1, src.count(old), old)
            self.assertNotEqual(base, probes(types_module(src.replace(old, new))), old)


def types_module(src):
    u"""script の字(壊した写し)から module を作る。import の副作用(PB の読み込み)は本物の module の名前を使い回す(sys.modules を触らない)ため、ここでは必要な関数だけを取り出す。"""
    import types
    ns = {"__name__": "nonfunc_mutant", "__file__": os.path.join(ROOT, SCRIPT_REL)}
    for name in ("collections", "statistics", "re", "io", "json", "os", "sys", "time"):
        ns[name] = __import__(name)
    for name in ("KIND_DOC", "KIND_AI", "KINDS", "PROFILES", "MB", "HIT", "MISS", "SEAL_REL", "ROOT"):
        ns[name] = getattr(SC, name)
    # 必要な関数の定義だけを字から取り出して実行する
    import ast
    tree = ast.parse(src)
    keep = []
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in ("median", "within", "atmost", "select", "spreads", "columns_from_rows", "judge_from", "seal_bounds", "seal_pred_rows", "_f", "read_seal"):
            keep.append(n)
    mod = ast.Module(body=keep, type_ignores=[])
    exec(compile(mod, "<mutant>", "exec"), ns)
    return types.SimpleNamespace(**dict((k, v) for k, v in ns.items() if callable(v) and not k.startswith("__")))


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.ex = sample_expect(reps=3, ndocs=4, nbooks=5)
        cls.rec = sample_record(cls.ex, cls.seal)
        cls.doc = sample_doc(cls.rec, cls.seal)

    def test_d_1_the_sample_document_follows_the_record(self):
        self.assertEqual([], doc_problems(self.doc, self.rec, self.seal))

    def test_d_2_one_changed_character_in_a_table_cell_turns_it_red(self):
        lines = self.doc.split(u"\n")
        for marker in (u"<!-- 門:start pred -->", u"<!-- 門:start stats -->"):
            i = lines.index(marker) + 3                         # 表の 1 行目(データ行)
            for j in (i, i + 1):
                for cell_idx in (1, 3, 4):
                    cells = lines[j].split(u" | ")
                    if cell_idx >= len(cells):
                        continue
                    c = cells[cell_idx]
                    digits = [m.start() for m in re.finditer(r"\d", c)]
                    if not digits:
                        continue
                    k = digits[-1]
                    cells[cell_idx] = c[:k] + (u"0" if c[k] != u"0" else u"1") + c[k + 1:]
                    mutated = u"\n".join(lines[:j] + [u" | ".join(cells)] + lines[j + 1:])
                    self.assertNotEqual(self.doc, mutated)
                    self.assertNotEqual([], doc_problems(mutated, self.rec, self.seal), (marker, j, cell_idx))

    def test_d_3_a_missing_or_extra_table_or_block_turns_it_red(self):
        self.assertNotEqual([], doc_problems(self.doc.replace(u"門:start stats", u"門:start other"), self.rec, self.seal))
        self.assertNotEqual([], doc_problems(self.doc.replace(u"門:start pred", u"門:start pred2", 1), self.rec, self.seal))
        lines = self.doc.split(u"\n")
        i = lines.index(u"<!-- 門:start pred -->") + 3
        self.assertNotEqual([], doc_problems(u"\n".join(lines[:i] + lines[i + 1:]), self.rec, self.seal))          # 行が 1 つ欠けた
        self.assertNotEqual([], doc_problems(self.doc + u"\n<!-- 門:start x -->\na\n<!-- 門:end -->\n", self.rec, self.seal))

    def test_d_4_a_changed_record_turns_the_document_red(self):
        rec2 = copy.deepcopy(self.rec)
        rec2[u"行"][0][u"時間"] = round(rec2[u"行"][0][u"時間"] + 0.5, 6)
        self.assertNotEqual([], doc_problems(self.doc, rec2, self.seal))
        rec3 = copy.deepcopy(self.rec)
        rec3[u"import の時間"][u"秒"] = [2.0] * 5
        self.assertNotEqual([], doc_problems(self.doc, rec3, self.seal))                              # N-8 の値と判定が変わる

    def test_d_5_prose_numbers_forbidden_words_and_docids_turn_it_red(self):
        self.assertNotEqual([], doc_problems(self.doc + u"\n中央値は 123 ミリ秒でした。\n", self.rec, self.seal))                # 3 桁の数に【門なし】が無い
        self.assertEqual([], doc_problems(self.doc + u"\n中央値は 123 ミリ秒でした。" + NOT_GATED + u"\n", self.rec, self.seal))
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(self.doc + u"\n" + w + u"\n", self.rec, self.seal), w)
        self.assertNotEqual([], doc_problems(self.doc + u"\nS100" + u"ABCD\n", self.rec, self.seal))

    def test_d_6_the_stats_table_is_checked_against_a_second_independent_rendering(self):
        J = SC.build_E(self.rec, self.seal)
        self.assertEqual(SC.render_stats(self.rec[u"行"]).split(u"\n"), indep_stats_lines(self.rec[u"行"]))
        self.assertEqual(4 + 2, len(indep_stats_lines(self.rec[u"行"])))
        self.assertEqual(11, len(SC.render_pred(J, self.seal).split(u"\n")))                      # 見出し 2 行 + N-1〜N-9

    def test_d_7_the_tally_prints_both_tables_from_a_record(self):
        out = []
        SC.run_tally(root=ROOT, say=out.append, rec=self.rec)
        text = u"\n".join(out)
        self.assertIn(SC.render_pred(SC.build_E(self.rec, self.seal), self.seal), text)
        self.assertIn(SC.render_stats(self.rec[u"行"]), text)


class OrderChainTest(unittest.TestCase):
    SEALF = "docs/seal.md"
    SCRIPTS = ["measure/s.py", "tests/g1.py", "tests/g2.py"]
    REC = "fixtures/xbrl/nonfunc/rec.json"
    DOCF = "docs/res.md"

    def _repo(self, order):
        r = PR.Repo()
        r.put(self.SEALF)
        s = r.commit(self.SEALF)
        for group in order:
            for f in group:
                r.put(f)
            r.commit(*group)
        return r, s[:7]

    def probe(self, r, s):
        return chain_problems(root=r.d, seal_rel=self.SEALF, seal_short=s, script_rels=tuple(self.SCRIPTS), rec_rel=self.REC, doc_rel=self.DOCF)

    def test_k_1_scripts_then_record_then_document_is_green_and_record_with_document_in_one_commit_too(self):
        r, s = self._repo([self.SCRIPTS, [self.REC], [self.DOCF]])
        self.assertEqual([], self.probe(r, s))
        r2, s2 = self._repo([self.SCRIPTS, [self.REC, self.DOCF]])
        self.assertEqual([], self.probe(r2, s2))

    def test_k_2_a_record_in_the_scripts_commit_or_before_them_is_red(self):
        r, s = self._repo([self.SCRIPTS + [self.REC], [self.DOCF]])
        self.assertIn("RECORD_NOT_AFTER_SCRIPT", self.probe(r, s))
        r2, s2 = self._repo([[self.REC], self.SCRIPTS, [self.DOCF]])
        self.assertTrue(any(x.startswith("BEFORE_") or x == "RECORD_NOT_AFTER_SCRIPT" for x in self.probe(r2, s2)))
        self.assertNotEqual([], self.probe(r2, s2))
        r3, s3 = self._repo([self.SCRIPTS[:2], [self.REC], self.SCRIPTS[2:], [self.DOCF]])             # 門の 1 本が記録より後
        self.assertIn("RECORD_NOT_AFTER_SCRIPT", self.probe(r3, s3))

    def test_k_3_a_document_before_the_record_or_uncommitted_files_are_red(self):
        r, s = self._repo([self.SCRIPTS, [self.DOCF], [self.REC]])
        self.assertIn("DOC_BEFORE_RECORD", self.probe(r, s))
        r2, s2 = self._repo([self.SCRIPTS, [self.REC]])
        self.assertEqual(["UNCOMMITTED:" + self.DOCF], self.probe(r2, s2))
        r3, s3 = self._repo([self.SCRIPTS])
        self.assertEqual(sorted(["UNCOMMITTED:" + self.REC, "UNCOMMITTED:" + self.DOCF]), sorted(self.probe(r3, s3)))
        r4, _s4 = self._repo([self.SCRIPTS, [self.REC], [self.DOCF]])
        self.assertIn("SEAL_NOT_THE_SEALED", self.probe(r4, "0000000"))


class DeclarationTest(unittest.TestCase):
    u"""docID を持つ記録は fresh_seal の LATER_NAMING_FILES に宣言する。宣言は記録を走らせる便が足すので、記録が在るときだけ宣言を見る。"""

    @staticmethod
    def naming_problems(src):
        got = later_naming_files(src)
        if got is None:
            return [u"LATER_NAMING_FILES が読めない"]
        return ([u"LATER_NAMING_FILES に %s が無い" % REC_REL] if REC_REL not in got else []) + \
            [u"LATER_NAMING_FILES に docID を持たない %s がある" % rel for rel in [SCRIPT_REL, DOC_REL] + list(SG.GATE_RELS) if rel in got]

    def test_h_1_naming_check_sees_a_missing_or_a_wrongly_declared_record(self):
        src = u'LATER_NAMING_FILES = ("a.json", "%s")\n' % REC_REL
        self.assertEqual([], self.naming_problems(src))
        self.assertNotEqual([], self.naming_problems(src.replace(REC_REL, u"x/" + REC_REL)))
        self.assertNotEqual([], self.naming_problems(src.replace("LATER_NAMING_FILES", "LATER_NAMING_FILE")))
        self.assertNotEqual([], self.naming_problems(src.replace(u'")\n', u'", "%s")\n' % SG.GATE_RELS[0])))
        self.assertNotEqual([], self.naming_problems(src.replace(u'")\n', u'", "%s")\n' % SCRIPT_REL)))

    def test_h_2_the_previous_declarations_are_still_there(self):
        got = later_naming_files(read("tests/measure/test_xbrl_fresh_seal.py"))
        for rel in ("fixtures/xbrl/tperiod/moves_200_2026-11-09.json", "fixtures/xbrl/pbind/moves_200_2026-11-06.json"):
            self.assertIn(rel, got)

    def test_h_3_when_the_record_exists_it_is_declared(self):
        if not records_exist():
            self.skipTest(u"記録が無い(記録を走らせた後に走る)")
        self.assertEqual([], self.naming_problems(read("tests/measure/test_xbrl_fresh_seal.py")))


# ================================================================ 本番の記録
class RealRecordTest(unittest.TestCase):
    u"""記録が無いときは各試験が skip する(skip でも行が出ることは SkipLineTest が確かめる)。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def need(self):
        if not records_exist():
            self.skipTest(u"記録が無い(本番の測定を走らせた後に走る)")
        return jload(REC_REL)

    def test_r_1_the_record_is_clean_and_consistent(self):
        rec = self.need()
        self.assertEqual([], record_problems(copy.deepcopy(rec), real_expect(), self.seal))

    def test_r_2_judgement_is_rebuilt_from_the_record(self):
        rec = self.need()
        self.assertEqual([], judge_problems(rec, self.seal))
        J = SC.build_E(rec, self.seal)
        self.assertEqual(set(J), {u"E", u"欄"})

    def test_r_3_the_result_document_follows_the_record(self):
        rec = self.need()
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), rec, self.seal))

    def test_r_4_order_is_seal_then_scripts_then_record_then_document(self):
        self.need()
        self.assertEqual([], chain_problems())


class SkipLineTest(unittest.TestCase):
    def test_s_1_a_skipped_real_record_test_still_prints_a_line(self):
        u"""記録が無いと本番の記録の試験は skip になるが、skip でも行が出る(黙って消えない)。"""
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(RealRecordTest)
        n = suite.countTestCases()
        self.assertGreaterEqual(n, 4)
        stream = io.StringIO()
        FORCE["no_records"] = True
        try:
            res = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        finally:
            FORCE["no_records"] = False
        self.assertEqual(n, len(res.skipped))
        self.assertEqual(0, len(res.failures) + len(res.errors))
        self.assertEqual(n, len(re.findall(r"\.\.\. skipped '", stream.getvalue())))
        for _t, why in res.skipped:
            self.assertIn(u"記録が無い", why)


# ================================================================ 小さな 1 書類の走り(cache を読むだけ。記録は TMPDIR の下。cache が無ければ skip)
class RealRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HAVE_CACHE:
            raise unittest.SkipTest(u"cache が無い(実書類を通す試験は skip)")
        cls.seal = read(SEAL_REL)
        cls.doc = RM.load_jobs(ROOT, None)[0][2][u"docID"]

    def test_x_1_one_document_runs_with_rc_0_and_the_record_has_the_right_shape(self):
        u"""``run --only <1 書類> --reps 1 --out <TMPDIR の下>`` が rc 0。行の形・材料の集合と順・claim の数が前の便の記録と同じ(時間の値は見ない)。"""
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            out = os.path.join(d, "one.json")
            r = subprocess.run([sys.executable, os.path.join(ROOT, SCRIPT_REL), "run", "--only", self.doc, "--reps", "1", "--out", out], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True)
            self.assertEqual(0, r.returncode, r.stdout[-1500:])
            with io.open(out, encoding="utf-8") as fh:
                rec = json.load(fh)
        ex = real_expect(only=self.doc, reps=1)
        self.assertEqual(1, len(ex.docs))
        self.assertGreater(len(ex.books), 0)
        self.assertEqual([], record_problems(rec, ex, self.seal))
        self.assertEqual((1 + len(ex.books)) * 2, len(rec[u"行"]))
        self.assertEqual(u"**--only の docID だけ(本番の記録ではない)**", rec[u"範囲"])
        self.assertTrue(all(r[u"ru_maxrss の後"] > r[u"ru_maxrss の前"] for r in rec[u"行"]))                   # 1 回の呼び出しで常駐の最大は増える(後が前と同じなら読み違い)
        self.assertTrue(all(r[u"CPU 時間"] <= r[u"時間"] * 1.5 for r in rec[u"行"]))                          # 1 thread の CPU 時間は時間とほぼ同じ以下(欄の取り違えの検出。時間の値は見ない)

    def test_x_2_the_default_out_is_refused_for_an_only_run_and_nothing_is_written(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with self.assertRaises(SC.Stop):
                SC.run(root=d, only=self.doc, reps=1, say=lambda *a: None)
            self.assertEqual([], os.listdir(d))


if __name__ == "__main__":
    unittest.main()
