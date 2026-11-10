# -*- coding: utf-8 -*-
"""封 docs/XBRL_LABEL_ONLY_RATES_SEAL_2026-11-10.md(札のある行だけの率 LB)の結果の門。封 §0-2 の 3・5・§1・§2・§3・§4・§6。

**この門が縛るもの**(封の門 ``test_xbrl_labelonly_seal.py`` は封の字・script の定数・触らない file・配線・順序を縛る)

  a  記録の形: 禁止欄・会社名・pointer の字・鍵が無い / 頭(封・script の sha256・engine の指紋・範囲・profile 5 つ・cache の前後・札の記録の sha256 と (本, id) の数・限界)/
     本(200 本の名と順が N の便の記録と同じ・形・対応・L-0 の差)/ 行の欄と型 / 本 × profile の並び / 行数が本の欄と同じ。
     **この門が別に書いた計算**で: 札の結び方(P28E の行の札の分布 = 札の記録の分布・P29E 以降の行は『同じ鍵の P28E の行が在れば既存でその札、無ければ新で札なし』)・
     N の便の記録の既存の行の数・新しい行の数・数の claim の数と今回の数の一致。
  b  判定: L-0〜L-2 を記録の行から**この門が別に書いた計算**で求め、script の ``build_L`` の値と同じ。封の数(literal に留めた値)との一致 / 1 違いの不一致・分母 0 の率は『なし』。
  c  結果の文書: ``<!-- 門:start pred -->``(L-0〜L-2 の照合)・``<!-- 門:start rates -->``(profile × 範囲)・``<!-- 門:start forms -->``(形ごと)を記録から作り直した表と一字ずつ照らす。散文の 3 桁の数に【門なし】。
  d  順序: 封 9ad2c7d0 ⊏ script・門 ⊏ 記録 ⊑ 結果の文書。未 commit は赤(skip にしない)。
  e  宣言: docID を持つ記録は fresh_seal の LATER_NAMING_FILES に宣言する(記録が在るときだけ見る)。
  f  変異: 標本の記録で、a・b・c・d のどれを壊しても赤になる。

記録が無いときは本番の記録の試験を skip する(skip でも行が出ることを試験が確かめる)。標本の試験は記録が無くても走る。この file は docID の字を持たない。
"""
import collections
import copy
import decimal
import hashlib
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
    import importlib.util
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


SG = load_module("tests/measure/test_xbrl_labelonly_seal.py", "labelonly_seal_gate_for_result")                # 封の門の部品。門としては走らせない
PSR = load_module("tests/measure/test_xbrl_pswap_result.py", "pswap_result_gate_for_labelonly_result")        # 禁止欄・語・差し替えの部品。門としては走らせない
SC = SG.SC
PR = SG.PR
GEN, RUN, RM = SC.GEN, SC.RUN, SC.RM
SEAL_REL, DOC_REL, SCRIPT_REL, REC_REL = SC.SEAL_REL, SC.DOC_REL, SC.SCRIPT_REL, SC.REC_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
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
PROFILES = ("P28E", "P29E", "P30E", "P32E", "P33E")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
FORMS = ("F1", "F2", "F3", "F4", "F5")
WORDS = (u"真", u"偽", u"判定不能")
NONE_WORD = u"なし"
EXIST, NEWW = u"既存", u"新"
RANGE_FULL = u"全部(AI の文 200 本)"
RANGE_ONLY = u"**--only の docID だけ(本番の記録ではない)**"
MATCH_W, DIFF_W = u"**一致**", u"**不一致**"
N_AI200_REL = "fixtures/xbrl/numfix/ai200_2026-11-04.json"
LABEL_RELS = ("fixtures/xbrl/aiforms/labels_2026-11-03.json", "fixtures/xbrl/aiforms/f5_labels_2026-11-03.json")
#: 記録の限界の字の頭(literal に留める。script の字を変えたら赤)
LIMITS_PIN = (u"札は盲検の LLM の席", u"札の無い行", u"材料は AI の文 200 本", u"注入の率", u"有料の API")
ROW_FIELDS = (u"本の id", u"形", u"profile", u"文の番号", u"文の中の位置", u"state", u"札", u"既存か新か")
BOOK_KEYS = (u"本の id", u"形", u"model", u"材料", u"対応", u"数の claim の数", u"L-0 の差")
#: 結果の文書の表の見出し
RATES_HEAD = u"| profile | 範囲 | 行数 | GROUNDED | 率(%) |"
FORMS_HEAD = u"| 形 | profile | 範囲 | 行数 | GROUNDED | 率(%) |"
PRED_HEAD = u"| # | 欄 | 照合 | 測った値 | 判定 |"
#: 範囲の名前と、それが数える札の語(literal に留める。script の定義と違えば赤)
GROUP_DEFS = collections.OrderedDict([
    (u"全部の行", (u"真", u"偽", u"判定不能", u"なし")), (u"札のある行", (u"真", u"偽", u"判定不能")), (u"札 真", (u"真",)), (u"札 偽", (u"偽",)), (u"札 判定不能", (u"判定不能",)), (u"札の無い行", (u"なし",))])
FORM_GROUPS = (u"札のある行", u"札 真", u"札 偽", u"札 判定不能")
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


# ---------------------------------------------------------------- engine の指紋(封の commit の木から。engine はこの便で変えない)
_FP = []


def engine_fingerprint_at_seal():
    if not _FP:
        s = SG.seal_commit_of()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            arc = subprocess.run(["git", "archive", s, PREFIX + "adapters/xbrl", PREFIX + "core/py/audit_core"], cwd=REPO, stdout=subprocess.PIPE, check=True)
            subprocess.run(["tar", "-x", "-C", d], input=arc.stdout, check=True)
            a, _na = SC.VD._py_digest(os.path.join(d, PREFIX, "adapters", "xbrl"))
            c, _nc = SC.VD._py_digest(os.path.join(d, PREFIX, "core", "py", "audit_core"))
        _FP.append({"adapter_xbrl_py_sha256": a, "core_py_sha256": c})
    return _FP[0]


# ---------------------------------------------------------------- 期待する材料(札の記録と N の便の記録から。読むだけ)
class Expect(object):
    u"""記録の検査が照らす材料の期待。names = 本の名の列(順)・forms = {名: 形}・label_dist = {名: {語: 数}}(札の記録の分布)・label_count = {名: 札の記録の id の数}・
    n28 / n29 / existing / new = {名: 数}(N の便の記録)・label_total = 札の記録の (本, id) の全部の数・full = 本番の全部か。"""

    def __init__(self, names, forms, label_dist, label_count, n28, n29, existing, new, label_total, full):
        self.names, self.forms, self.label_dist, self.label_count = list(names), dict(forms), dict(label_dist), dict(label_count)
        self.n28, self.n29, self.existing, self.new = dict(n28), dict(n29), dict(existing), dict(new)
        self.label_total, self.full = label_total, full


_REAL = {}


def real_expect(only=None):
    u"""200 本(N の便の記録の本の順)。札の記録は 2 つ。only = docID(その docID の本だけ)。"""
    if not _REAL:
        n = jload(N_AI200_REL)
        labels = {}
        for rel in LABEL_RELS:
            for b in jload(rel)[u"本"]:
                labels[b[u"name"]] = collections.Counter(x[1] for x in b[u"札"]), len(b[u"札"])
        _REAL["n"] = n[u"本"]
        _REAL["labels"] = labels
        _REAL["total"] = sum(c for _d, c in labels.values())
    books = [b for b in _REAL["n"] if only is None or b[u"docID"] == only]
    names = [b[u"name"] for b in books]
    return Expect(names, dict((b[u"name"], b[u"form"]) for b in books), dict((nm, dict(_REAL["labels"][nm][0])) for nm in names), dict((nm, _REAL["labels"][nm][1]) for nm in names),
                  dict((b[u"name"], b[u"数の claim の数"]["P28E"]) for b in books), dict((b[u"name"], b[u"数の claim の数"]["P29E"]) for b in books),
                  dict((b[u"name"], b[u"既存の行"][u"行の数"]) for b in books), dict((b[u"name"], b[u"新しい行の数"]) for b in books), _REAL["total"], only is None)


# ---------------------------------------------------------------- 数え(この門が別に書いた計算。script の ``row_group_counts`` を使わない)
def indep_group_counts(rows):
    u"""{(profile, 範囲): (行数, GROUNDED)}。1 行ずつ 6 つの範囲に当てはまるかを調べる(script とは別の書き方)。"""
    res = dict(((p, g), [0, 0]) for p in PROFILES for g in GROUP_DEFS)
    for r in rows:
        for g, words in GROUP_DEFS.items():
            if any(r[6] == w for w in words):
                res[(r[2], g)][0] += 1
                res[(r[2], g)][1] += 1 if r[5] == "GROUNDED" else 0
    return dict((k, tuple(v)) for k, v in res.items())


def indep_form_counts(rows):
    res = dict(((f, p, g), [0, 0]) for f in FORMS for p in PROFILES for g in FORM_GROUPS)
    for r in rows:
        for g in FORM_GROUPS:
            if r[6] in GROUP_DEFS[g]:
                res[(r[1], r[2], g)][0] += 1
                res[(r[1], r[2], g)][1] += 1 if r[5] == "GROUNDED" else 0
    return dict((k, tuple(v)) for k, v in res.items())


def indep_rate(g, n):
    u"""百分率の小数 1 桁(0.5 は切り上げ)。分母 0 は『なし』。Decimal で。"""
    if n == 0:
        return u"なし"
    q = (decimal.Decimal(g) * 100 / decimal.Decimal(n)).quantize(decimal.Decimal("0.1"), rounding=decimal.ROUND_HALF_UP)
    return u"%s" % q


def comma(x):
    return u"{:,}".format(x)


def indep_rates_lines(rows):
    c = indep_group_counts(rows)
    lines = [RATES_HEAD, u"|---|---|---|---|---|"]
    for p in PROFILES:
        for g in GROUP_DEFS:
            n, gr = c[(p, g)]
            lines.append(u"| %s | %s | %s | %s | %s |" % (p, g, comma(n), comma(gr), indep_rate(gr, n)))
    return lines


def indep_forms_lines(rows):
    c = indep_form_counts(rows)
    lines = [FORMS_HEAD, u"|---|---|---|---|---|---|"]
    for f in FORMS:
        for p in PROFILES:
            for g in FORM_GROUPS:
                n, gr = c[(f, p, g)]
                lines.append(u"| %s | %s | %s | %s | %s | %s |" % (f, p, g, comma(n), comma(gr), indep_rate(gr, n)))
    return lines


def seal_cells(seal):
    u"""封 §2 の表の {L-n: [欄, 照合 / 予測, 外れ方]}(この門が別に書いた読み)。"""
    sec = seal[seal.index("## §2"):seal.index("## §3")]
    out = collections.OrderedDict()
    for line in sec.split(u"\n"):
        m = re.match(r"^\| (L-\d) \| (.*) \|$", line)
        if m:
            out[m.group(1)] = m.group(2).split(u" | ")
    return out


# 封の数(literal。封の門が封の字と照らす)
PIN = SG.EXPECT_PIN


def indep_L(rec):
    u"""L-0〜L-2 の {判定, 値の字} を記録から。値の字もこの門が別に書く。"""
    c = indep_group_counts(rec[u"行"])
    books = rec[u"本"]
    only_run = sum(b[u"L-0 の差"][u"P28E のみ"] for b in books)
    only_lab = sum(b[u"L-0 の差"][u"札のみ"] for b in books)
    n28 = c[("P28E", u"全部の行")][0]
    total = rec[u"札の記録の (本, id) の数"]
    ok0 = (only_run, only_lab, n28, total) == (0, 0, PIN["L-0"], PIN["L-0"])
    v0 = u"P28E のみ %s・札のみ %s・数の claim の行数 %s・札の記録の (本, id) %s" % (comma(only_run), comma(only_lab), comma(n28), comma(total))
    ok1 = all((c[(p, u"全部の行")][0], c[(p, u"札のある行")][0]) == PIN["L-1"][p] for p in PROFILES)
    v1 = u"、".join(u"%s %s / %s" % (p, comma(c[(p, u"全部の行")][0]), comma(c[(p, u"札のある行")][0])) for p in PROFILES)
    ok2 = True
    for p in PROFILES:
        want_all, want_lab = PIN["L-2"][p]
        if c[(p, u"札のある行")][1] != want_lab or (want_all is not None and c[(p, u"全部の行")][1] != want_all):
            ok2 = False
    v2 = u"・".join(u"%s %s / %s" % (p, comma(c[(p, u"全部の行")][1]), comma(c[(p, u"札のある行")][1])) for p in PROFILES)
    return collections.OrderedDict([("L-0", (ok0, v0)), ("L-1", (ok1, v1)), ("L-2", (ok2, v2))])


def indep_pred_lines(rec, seal):
    cells = seal_cells(seal)
    L = indep_L(rec)
    lines = [PRED_HEAD, u"|---|---|---|---|---|"]
    for k, (ok, val) in L.items():
        lines.append(u"| %s | %s | %s | %s | %s |" % (k, cells[k][0], cells[k][1], val, MATCH_W if ok else DIFF_W))
    return lines


def judge_problems(rec, seal):
    u"""判定が記録から作り直せ、この門の別計算と同じか。壊れた記録は赤。"""
    try:
        J = SC.build_L(rec, seal)
        want = indep_L(rec)
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J) != ["L-0", "L-1", "L-2"]:
        return [u"判定の行が L-0〜L-2 でない"]
    for k, (ok, val) in want.items():
        if J[k][u"判定"] != (MATCH_W if ok else DIFF_W):
            out.append(u"%s: script の判定 %s がこの門の別計算 %s と違う" % (k, J[k][u"判定"], ok))
        if SC.fmt_L(k, J[k]) != val:
            out.append(u"%s: script の値の字がこの門の別計算と違う" % k)
    if SC.render_pred(J, seal).split(u"\n") != indep_pred_lines(rec, seal):
        out.append(u"表 pred が別計算の表と違う")
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
        with SC.key_check_lb(GEN):
            RUN.assert_clean(copy.deepcopy(rec))
    except GEN.Stop:
        out.append(u"鍵らしい字が記録に在る")
    if rec.get(u"key_leaks", []) != []:
        out.append(u"key_leaks が空でない")
    return out


def header_problems(rec, ex):
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
    want_range = RANGE_FULL if ex.full else RANGE_ONLY
    if rec.get(u"範囲") != want_range:
        out.append(u"範囲が %s でない" % want_range)
    if rec.get(u"profile") != list(PROFILES):
        out.append(u"profile が (P28E, P29E, P30E, P32E, P33E) でない")
    cb = rec.get(u"cache の前後") or {}
    if cb.get(u"変化なし") is not True or cb.get(u"前") != cb.get(u"後"):
        out.append(u"cache の前後が同じでない")
    shas = rec.get(u"札の記録の sha256") or {}
    if list(shas) != [u"aiforms", u"f5"] or [shas.get(u"aiforms"), shas.get(u"f5")] != [sha256_rel(rel) for rel in LABEL_RELS]:
        out.append(u"札の記録の sha256 が現物と違う")
    if rec.get(u"札の記録の (本, id) の数") != ex.label_total or type(rec.get(u"札の記録の (本, id) の数")) is not int:
        out.append(u"札の記録の (本, id) の数が札の記録の現物と違う")
    lim = list(rec.get(u"限界") or [])
    if len(lim) != len(LIMITS_PIN) or [x[:len(p)] for x, p in zip(lim, LIMITS_PIN)] != list(LIMITS_PIN):
        out.append(u"限界の字か数が留めた値と違う")
    if list((rec.get(u"欄") or {}).get(u"行の欄") or []) != list(ROW_FIELDS):
        out.append(u"欄の『行の欄』が行の欄の並びと違う")
    return out


def book_problems(rec, ex):
    u"""本の欄: 名と順・形・欄の並び・対応・数の claim の数の型。"""
    books = rec.get(u"本")
    if not isinstance(books, list):
        return [u"本が無い"]
    out = []
    if [b.get(u"本の id") for b in books] != ex.names:
        return [u"本の名の並びが N の便の記録の本(200 本の順)と違う"]
    isint = lambda x: type(x) is int                                                           # noqa: E731
    for b in books:
        nm = b[u"本の id"]
        if list(b) != list(BOOK_KEYS):
            out.append(u"%s: 本の欄の名前か並びが違う" % nm)
            continue
        if b[u"形"] != ex.forms[nm]:
            out.append(u"%s: 形が N の便の記録と違う" % nm)
        if b[u"対応"] != dict((p, True) for p in PROFILES) or list(b[u"対応"]) != list(PROFILES):
            out.append(u"%s: 対応が付かない profile がある(id の並び・kind・鍵の一意のどれかが崩れた)" % nm)
        if list(b[u"数の claim の数"]) != list(PROFILES) or not all(isint(v) and v >= 0 for v in b[u"数の claim の数"].values()):
            out.append(u"%s: 数の claim の数が profile 5 つの 0 以上の整数でない" % nm)
        d = b[u"L-0 の差"]
        if list(d) != [u"P28E のみ", u"札のみ", u"札の記録の id の数"] or not all(isint(v) and v >= 0 for v in d.values()):
            out.append(u"%s: L-0 の差の欄が違う" % nm)
    return out


def row_shape_problems(rows):
    out = []
    isint = lambda x: type(x) is int                                                           # noqa: E731
    for i, r in enumerate(rows):
        tag = u"行 %d" % i
        if not isinstance(r, list) or len(r) != 8:
            out.append(u"%s: 8 つの配列でない" % tag)
            continue
        if not (isinstance(r[0], str) and r[0] and r[1] in FORMS and r[2] in PROFILES and isint(r[3]) and r[3] >= 0 and isint(r[4]) and r[4] >= 0):
            out.append(u"%s: 本の id・形・profile・鍵が違う" % tag)
        if r[5] not in STATES:
            out.append(u"%s: state が 4 つのどれでもない" % tag)
        if r[6] not in WORDS + (NONE_WORD,) or r[7] not in (EXIST, NEWW):
            out.append(u"%s: 札か既存 / 新が違う" % tag)
    return out


def rows_problems(rec, ex):
    u"""行の集まりの検査: 形・並び・本の欄との数・札の結び方(この門が別に書いた計算)・N の便の記録との一致。"""
    rows = rec.get(u"行")
    if not isinstance(rows, list) or not rows:
        return [u"行が無い"]
    out = row_shape_problems(rows)
    if out:
        return out
    books = dict((b[u"本の id"], b) for b in rec[u"本"])
    order = dict((nm, i) for i, nm in enumerate(ex.names))
    pidx = dict((p, i) for i, p in enumerate(PROFILES))
    seq = [(order.get(r[0], -1), pidx[r[2]]) for r in rows]
    if any(a[0] < 0 for a in seq):
        return [u"本の欄に無い本の行がある"]
    if any(seq[i] > seq[i + 1] for i in range(len(seq) - 1)):
        return [u"行が (本の順, profile の順) に並んでいない"]
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault((r[0], r[2]), []).append(r)
        if r[1] != ex.forms[r[0]]:
            out.append(u"%s: 行の形が本の形と違う" % r[0])
            break
    for nm in ex.names:
        b = books[nm]
        for p in PROFILES:
            got = len(by.get((nm, p), []))
            if got != b[u"数の claim の数"][p]:
                out.append(u"%s %s: 行の数 %d が本の欄の数の claim の数 %d と違う" % (nm, p, got, b[u"数の claim の数"][p]))
            keys = [(r[3], r[4]) for r in by.get((nm, p), [])]
            if len(set(keys)) != len(keys):
                out.append(u"%s %s: 鍵が重複している" % (nm, p))
        # 札の結び方: P28E の行は全部既存。P29E 以降は同じ鍵の P28E の行が在れば既存でその札、無ければ新で札なし
        base = by.get((nm, "P28E"), [])
        base_label = {}
        for r in base:
            base_label.setdefault((r[3], r[4]), r[6])
        if any(r[7] != EXIST for r in base):
            out.append(u"%s: P28E の行に既存でない行がある" % nm)
        for p in PROFILES[1:]:
            for r in by.get((nm, p), []):
                k = (r[3], r[4])
                want = (base_label[k], EXIST) if k in base_label else (NONE_WORD, NEWW)
                if (r[6], r[7]) != want:
                    out.append(u"%s %s 鍵 %r: 札と既存 / 新が P28E の行から結んだ値 %r と違う" % (nm, p, k, want))
                    break
        # P28E の行の札の分布 = 札の記録の分布(札の記録に無い id の行だけ『なし』)
        cnt = collections.Counter(r[6] for r in base)
        dist = ex.label_dist[nm]
        d = b[u"L-0 の差"]
        labelled = sum(cnt[w] for w in WORDS)
        if d[u"P28E のみ"] != cnt[NONE_WORD] or d[u"札のみ"] != ex.label_count[nm] - labelled or d[u"札の記録の id の数"] != ex.label_count[nm]:
            out.append(u"%s: L-0 の差が P28E の行の札の数と札の記録の id の数から求めた値と違う" % nm)
        for w in WORDS:
            if cnt[w] > dist.get(w, 0) or (d[u"札のみ"] == 0 and d[u"P28E のみ"] == 0 and cnt[w] != dist.get(w, 0)):
                out.append(u"%s: P28E の行の札 %s の数が札の記録の分布と合わない" % (nm, w))
        # N の便の記録
        n_new = sum(1 for r in by.get((nm, "P29E"), []) if r[7] == NEWW)
        n_old = sum(1 for r in by.get((nm, "P29E"), []) if r[7] == EXIST)
        if (len(base), len(by.get((nm, "P29E"), [])), n_old, n_new) != (ex.n28[nm], ex.n29[nm], ex.existing[nm], ex.new[nm]):
            out.append(u"%s: 数の claim の数・既存の行・新しい行の数が N の便の記録と違う" % nm)
    return out


def record_problems(rec, ex, seal=None):
    u"""記録の検査(禁止欄・鍵・頭・本・行・判定の再計算)。問題の列。壊れた記録は例外で落とさず問題に数える。"""
    seal = seal if seal is not None else read(SEAL_REL)
    out = []

    def safe(label, fn, *a):
        try:
            return fn(*a)
        except Exception as e:                               # noqa: BLE001
            return [u"%s: 検査できない(%s)" % (label, type(e).__name__)]
    out += safe(u"clean", clean_problems, rec)
    out += safe(u"頭", header_problems, rec, ex)
    out += safe(u"本", book_problems, rec, ex)
    if not out:
        out += safe(u"行", rows_problems, rec, ex)
    if not out:
        out += safe(u"判定", judge_problems, rec, seal)
    return out


# ---------------------------------------------------------------- 文書(c)
def doc_problems(doc, rec, seal):
    J = SC.build_L(rec, seal)
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != SC.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("pred") != indep_pred_lines(rec, seal):
        out.append(u"表 pred がこの門が別に作った表と違う")
    if got.get("rates") != SC.render_rates(rec[u"行"]).split(u"\n"):
        out.append(u"表 rates が記録から作り直した表と違う")
    if got.get("rates") != indep_rates_lines(rec[u"行"]):
        out.append(u"表 rates がこの門が別に作った表と違う")
    if got.get("forms") != SC.render_forms(rec[u"行"]).split(u"\n"):
        out.append(u"表 forms が記録から作り直した表と違う")
    if got.get("forms") != indep_forms_lines(rec[u"行"]):
        out.append(u"表 forms がこの門が別に作った表と違う")
    for k in got:
        if k not in ("pred", "rates", "forms"):
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


# ================================================================ 標本の記録(通信しない・cache を読まない)
def sample_inputs(nbooks=4):
    u"""小さい標本の入力 [(名, 形, 札の記録 {id: 語}, {profile: [(id, 鍵, state)]})]。本ごと profile ごとに state・札・新しい行が違う。1 本は札の記録に無い id と、今回に無い札の id を持つ。"""
    out = []
    pattern = [u"真", u"真", u"偽", u"判定不能", u"真", u"偽", u"真"]
    for i in range(nbooks):
        name, form = "B%d_%s_m" % (i, FORMS[i % 5]), FORMS[i % 5]
        k28 = 7 + i
        base = [("N%03d" % (k + 1), (k // 3, k % 3 + i), STATES[(k + i) % 4]) for k in range(k28)]
        labels = dict(("N%03d" % (k + 1), pattern[(k + i) % 7]) for k in range(k28))
        if i == 1:
            del labels["N003"]                                    # 今回の P28E に在るが札の記録に無い id
            labels["N099"] = u"真"                                # 札の記録に在るが今回の P28E に無い id
        views = collections.OrderedDict([("P28E", base)])
        for j, p in enumerate(PROFILES[1:], 1):
            rows = []
            for k in range(k28 + 3):                              # id は前にずれる。鍵は P28E と同じものに新しい鍵 3 つが混ざる
                if k % 4 == 3:
                    key = (50 + k, j)
                else:
                    key = base[min(k - k // 4, k28 - 1)][1]
                rows.append(("N%03d" % (k + 1), key, STATES[(k * j + i + (k > 4)) % 4]))
            seen, uniq = set(), []
            for cid, key, st in rows:
                if key in seen:
                    key = (80 + len(uniq), j)
                seen.add(key)
                uniq.append((cid, key, st))
            views[p] = uniq
        out.append((name, form, labels, views))
    return out


def sample_parts(nbooks=4):
    u"""(記録の 本 の列, 行の列, 期待 ex)。本と行は script の ``assemble_book`` で作り、期待は入力から(札の記録の分布・N の便の相当の数)この門が別に数える。"""
    books, rows = [], []
    names, forms, dist, lcount, n28, n29, ex_old, ex_new = [], {}, {}, {}, {}, {}, {}, {}
    for name, form, labels, views in sample_inputs(nbooks):
        b, r = SC.assemble_book(name, form, "m", "aiforms", dict((p, (v, True)) for p, v in views.items()), labels)
        books.append(b)
        rows += r
        names.append(name)
        forms[name] = form
        dist[name] = dict(collections.Counter(labels.values()))
        lcount[name] = len(labels)
        base_keys = set(k for _i, k, _s in views["P28E"])
        n28[name], n29[name] = len(views["P28E"]), len(views["P29E"])
        ex_old[name] = sum(1 for _i, k, _s in views["P29E"] if k in base_keys)
        ex_new[name] = sum(1 for _i, k, _s in views["P29E"] if k not in base_keys)
    ex = Expect(names, forms, dist, lcount, n28, n29, ex_old, ex_new, sum(lcount.values()), False)
    return books, rows, ex


def sample_header(ex, full=False):
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
    h[u"範囲"] = RANGE_FULL if full else RANGE_ONLY
    h[u"profile"] = list(PROFILES)
    h[u"cache の前後"] = collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)])
    h[u"札の記録の sha256"] = collections.OrderedDict([(u"aiforms", sha256_rel(LABEL_RELS[0])), (u"f5", sha256_rel(LABEL_RELS[1]))])
    h[u"札の記録の (本, id) の数"] = ex.label_total
    h[u"欄"] = collections.OrderedDict([(u"行の欄", list(ROW_FIELDS))])
    return h


def sample_record(nbooks=4):
    books, rows, ex = sample_parts(nbooks)
    rec = sample_header(ex)
    rec[u"本"] = books
    rec[u"行"] = rows
    rec[u"限界"] = list(SC.LIMITS)
    rec[u"key_leaks"] = []
    return norm(rec), ex


def sample_doc(rec, seal):
    J = SC.build_L(rec, seal)
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", SC.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start rates -->", SC.render_rates(rec[u"行"]), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start forms -->", SC.render_forms(rec[u"行"]), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"札のある行は表の数です。" + NOT_GATED, u""])


def exact_rec():
    u"""封の L-0〜L-2 の数にちょうど合う大きい標本(1 本)。(記録, 期待)。P28E 10,371 行(真 9,590・偽 368・判定不能 413。GROUNDED 6,597)、
    P29E〜P33E は 16,588 行のうち既存 10,357(札あり)と新しい 6,231(札なし)で、全部の GROUNDED と札のある行の GROUNDED が封の数。"""
    name = "B0_F1_m"
    words = [u"真"] * 9590 + [u"偽"] * 368 + [u"判定不能"] * 413
    rows = []
    for i, w in enumerate(words):
        rows.append([name, "F1", "P28E", 0, i, "GROUNDED" if i < 6597 else "VALUE_MISMATCH", w, EXIST])
    lab_g = {"P29E": 6586, "P30E": 6696, "P32E": 6695, "P33E": 6979}
    all_g = {"P29E": 11137, "P30E": 11260, "P32E": 11259, "P33E": 11625}
    for p in PROFILES[1:]:
        for i in range(10357):
            rows.append([name, "F1", p, 0, i, "GROUNDED" if i < lab_g[p] else "UNVERIFIABLE", words[i], EXIST])
        for j in range(6231):
            rows.append([name, "F1", p, 1, j, "GROUNDED" if j < all_g[p] - lab_g[p] else "POINTER_NOT_FOUND", NONE_WORD, NEWW])
    book = collections.OrderedDict([(u"本の id", name), (u"形", "F1"), (u"model", "m"), (u"材料", "aiforms"), (u"対応", collections.OrderedDict((p, True) for p in PROFILES)),
                                    (u"数の claim の数", collections.OrderedDict([("P28E", 10371)] + [(p, 16588) for p in PROFILES[1:]])),
                                    (u"L-0 の差", collections.OrderedDict([(u"P28E のみ", 0), (u"札のみ", 0), (u"札の記録の id の数", 10371)]))])
    ex = Expect([name], {name: "F1"}, {name: {u"真": 9590, u"偽": 368, u"判定不能": 413}}, {name: 10371}, {name: 10371}, {name: 16588}, {name: 10357}, {name: 6231}, 10371, True)
    rec = sample_header(ex, full=True)
    rec[u"本"] = [book]
    rec[u"行"] = rows
    rec[u"限界"] = list(SC.LIMITS)
    rec[u"key_leaks"] = []
    return rec, ex


# ================================================================ 試験
class SealPinTest(unittest.TestCase):
    def test_a_1_the_engine_fingerprint_at_the_seal_commit_equals_the_working_tree_one(self):
        u"""この便は engine を変えない: 封の commit の木の指紋は作業木の ``VD.engine_fingerprint()`` と同じ。"""
        fp = SC.VD.engine_fingerprint()
        want = engine_fingerprint_at_seal()
        for name in want:
            self.assertEqual(want[name], fp[name], name)
            self.assertRegex(want[name], r"^[0-9a-f]{64}$")

    def test_a_2_the_group_and_row_definitions_are_pinned(self):
        self.assertEqual(repr(GROUP_DEFS), repr(SC.GROUPS))
        self.assertEqual(FORM_GROUPS, SC.FORM_GROUPS)
        self.assertEqual(ROW_FIELDS, SC.ROW_FIELDS)
        self.assertEqual(BOOK_KEYS, SC.BOOK_KEYS)
        self.assertEqual((MATCH_W, DIFF_W), (SC.MATCH, SC.DIFF))
        self.assertEqual(FORMS, SC.FORMS)
        self.assertEqual(STATES, tuple(SC.STATES))
        self.assertEqual(RANGE_FULL, u"全部(AI の文 200 本)")

    def test_a_3_the_expected_materials_are_two_hundred_books_and_ten_thousand_labels(self):
        ex = real_expect()
        self.assertEqual(200, len(ex.names))
        self.assertEqual(200, len(set(ex.names)))
        self.assertEqual(10371, ex.label_total)
        self.assertEqual(10371, sum(ex.n28.values()))
        self.assertEqual(16588, sum(ex.n29.values()))
        self.assertEqual(10357, sum(ex.existing.values()))
        self.assertEqual(6231, sum(ex.new.values()))
        self.assertEqual({u"真": 9590, u"偽": 368, u"判定不能": 413}, dict(sum((collections.Counter(d) for d in ex.label_dist.values()), collections.Counter())))
        self.assertEqual(sorted(FORMS), sorted(set(ex.forms.values())))
        one = real_expect(only=jload(N_AI200_REL)[u"本"][0][u"docID"])
        self.assertEqual(10, len(one.names))
        self.assertFalse(one.full)


class SampleRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.rec, cls.ex = sample_record()

    def test_b_1_the_sample_record_is_clean_and_has_every_kind_of_row(self):
        self.assertEqual([], record_problems(copy.deepcopy(self.rec), self.ex, self.seal))
        c = collections.Counter((r[2], r[6], r[7]) for r in self.rec[u"行"])
        for p in PROFILES[1:]:
            for w in WORDS:
                self.assertGreater(c[(p, w, EXIST)], 0, (p, w))
            self.assertGreater(c[(p, NONE_WORD, NEWW)], 0, p)
        self.assertEqual(0, sum(v for (p, w, e), v in c.items() if p == "P28E" and e == NEWW))
        self.assertGreater(sum(v for (p, w, e), v in c.items() if p == "P28E" and w == NONE_WORD), 0)        # 札の記録に無い id の行
        self.assertEqual(1, sum(1 for b in self.rec[u"本"] if b[u"L-0 の差"][u"札のみ"] > 0))

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
            self._bad(lambda r, k=k: r[u"本"][0].update({k: u"x"}), u"repo へ入れない欄")
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
        self._bad(lambda r: r.update({u"範囲": RANGE_FULL}), u"範囲")                                  # 下見の標本が本番の範囲を名乗る
        self._bad(lambda r: r.update({u"profile": [u"P33E", u"P28E", u"P29E", u"P30E", u"P32E"]}), u"profile")
        self._bad(lambda r: r.update({u"profile": [u"P28E", u"P29E", u"P30E", u"P32E"]}), u"profile")
        self._bad(lambda r: r[u"cache の前後"].update({u"変化なし": False}), u"cache")
        self._bad(lambda r: r[u"cache の前後"].update({u"後": {}}), u"cache")
        self._bad(lambda r: r[u"札の記録の sha256"].update({u"f5": u"0" * 64}), u"札の記録の sha256")
        self._bad(lambda r: r[u"札の記録の sha256"].update({u"aiforms": u"0" * 64}), u"札の記録の sha256")
        self._bad(lambda r: r.update({u"札の記録の (本, id) の数": r[u"札の記録の (本, id) の数"] + 1}), u"(本, id) の数")
        self._bad(lambda r: r.update({u"札の記録の (本, id) の数": True}), u"(本, id) の数")
        self._bad(lambda r: r.update({u"限界": r[u"限界"][:-1]}), u"限界")
        self._bad(lambda r: r[u"限界"].__setitem__(0, u"x" + r[u"限界"][0]), u"限界")
        self._bad(lambda r: r[u"欄"].update({u"行の欄": list(reversed(ROW_FIELDS))}), u"行の欄")
        ex = copy.copy(self.ex)
        ex.full = True
        self.assertTrue(any(u"範囲" in x for x in record_problems(copy.deepcopy(self.rec), ex, self.seal)))      # 本番の期待に下見の範囲

    def test_c_3_the_book_checks_turn_red(self):
        self._bad(lambda r: r[u"本"].pop(), u"本の名")
        self._bad(lambda r: r[u"本"].reverse(), u"本の名")
        self._bad(lambda r: r[u"本"][0].update({u"本の id": u"B9_F1_m"}), u"本の名")
        self._bad(lambda r: r[u"本"][0].update({u"形": u"F5"}), u"形")
        self._bad(lambda r: r[u"本"][0].pop(u"model"), u"本の欄")
        self._bad(lambda r: r[u"本"][0][u"対応"].update({"P30E": False}), u"対応")
        self._bad(lambda r: r[u"本"][0].update({u"対応": {"P28E": True}}), u"対応")
        self._bad(lambda r: r[u"本"][0][u"数の claim の数"].update({"P33E": -1}), u"数の claim の数")
        self._bad(lambda r: r[u"本"][0][u"数の claim の数"].update({"P33E": r[u"本"][0][u"数の claim の数"]["P33E"] + 1}), u"行の数")
        self._bad(lambda r: r[u"本"][0][u"L-0 の差"].update({u"札のみ": 1}), u"L-0 の差")
        self._bad(lambda r: r[u"本"][1][u"L-0 の差"].update({u"P28E のみ": 0}), u"L-0 の差")
        self._bad(lambda r: r[u"本"][1][u"L-0 の差"].update({u"札のみ": 0}), u"L-0 の差")
        self._bad(lambda r: r[u"本"][2][u"L-0 の差"].update({u"札の記録の id の数": 1}), u"L-0 の差")
        self._bad(lambda r: r[u"本"][0][u"L-0 の差"].update({u"P28E のみ": 1.0}), u"L-0 の差")

    def test_c_4_the_row_shape_checks_turn_red(self):
        self._bad(lambda r: r[u"行"].pop(), u"行の数")
        self._bad(lambda r: r[u"行"].append(copy.deepcopy(r[u"行"][-1])), u"行の数")
        self._bad(lambda r: r[u"行"].reverse(), u"並んでいない")
        i = [k for k, x in enumerate(self.rec[u"行"]) if x[2] == "P29E"][0]
        j = [k for k, x in enumerate(self.rec[u"行"]) if x[2] == "P30E"][0]
        self._bad(lambda r: r[u"行"].__setitem__(slice(i, i + 1), [r[u"行"][j]]), u"")
        self._bad(lambda r: r[u"行"][0].append(1), u"8 つ")
        self._bad(lambda r: r[u"行"][0].pop(), u"8 つ")
        self._bad(lambda r: r[u"行"].__setitem__(0, tuple(r[u"行"][0])), u"8 つ")
        self._bad(lambda r: r[u"行"][0].__setitem__(1, u"F9"), u"形")
        self._bad(lambda r: r[u"行"][0].__setitem__(2, u"P27"), u"profile")
        self._bad(lambda r: r[u"行"][0].__setitem__(3, -1), u"鍵")
        self._bad(lambda r: r[u"行"][0].__setitem__(3, True), u"鍵")
        self._bad(lambda r: r[u"行"][0].__setitem__(4, u"0"), u"鍵")
        self._bad(lambda r: r[u"行"][0].__setitem__(5, u"OK"), u"state")
        self._bad(lambda r: r[u"行"][0].__setitem__(6, u"x"), u"札")
        self._bad(lambda r: r[u"行"][0].__setitem__(7, u"旧"), u"既存")
        self._bad(lambda r: r[u"行"][0].__setitem__(0, u""), u"本の id")

    def test_c_5_the_label_binding_checks_turn_red(self):
        rows = self.rec[u"行"]
        later = [k for k, x in enumerate(rows) if x[2] == "P29E" and x[7] == EXIST and x[6] == u"真"][0]
        self._bad(lambda r: r[u"行"][later].__setitem__(6, u"偽"), u"結んだ値")                          # 既存の行の札が P28E の行の札と違う
        self._bad(lambda r: r[u"行"][later].__setitem__(6, NONE_WORD), u"結んだ値")
        self._bad(lambda r: r[u"行"][later].__setitem__(7, NEWW), u"結んだ値")                           # 既存の行を新と言う
        new = [k for k, x in enumerate(rows) if x[2] == "P33E" and x[7] == NEWW][0]
        self._bad(lambda r: r[u"行"][new].__setitem__(6, u"真"), u"結んだ値")                            # 新しい行に札を付ける
        self._bad(lambda r: r[u"行"][new].__setitem__(7, EXIST), u"結んだ値")
        base = [k for k, x in enumerate(rows) if x[2] == "P28E"][0]
        self._bad(lambda r: r[u"行"][base].__setitem__(7, NEWW), u"既存でない")
        self._bad(lambda r: r[u"行"][base].__setitem__(6, u"偽" if r[u"行"][base][6] != u"偽" else u"真"), u"分布")      # P28E の行の札が札の記録の分布と合わない
        self._bad(lambda r: r[u"行"][later].__setitem__(4, r[u"行"][later][4] + 1000), u"")                    # 鍵が P28E に無くなる(既存が新になるはずなのに既存のまま)

    def test_c_6_a_mismatch_with_the_previous_numbers_record_turns_red(self):
        for attr in ("n28", "n29", "existing", "new"):
            ex = copy.deepcopy(self.ex)
            getattr(ex, attr)[ex.names[0]] += 1
            self.assertNotEqual([], record_problems(copy.deepcopy(self.rec), ex, self.seal), attr)
        ex = copy.deepcopy(self.ex)
        ex.label_dist[ex.names[0]][u"真"] += 1
        self.assertNotEqual([], record_problems(copy.deepcopy(self.rec), ex, self.seal))
        ex = copy.deepcopy(self.ex)
        ex.forms[ex.names[0]] = u"F5" if ex.forms[ex.names[0]] != u"F5" else u"F4"
        self.assertNotEqual([], record_problems(copy.deepcopy(self.rec), ex, self.seal))

    def test_c_7_duplicate_keys_in_a_profile_turn_red(self):
        rows = self.rec[u"行"]
        k = [i for i, x in enumerate(rows) if x[2] == "P30E"][:2]
        self._bad(lambda r: r[u"行"][k[1]].__setitem__(4, r[u"行"][k[0]][4]) or r[u"行"][k[1]].__setitem__(3, r[u"行"][k[0]][3]), u"重複")


class FullSizeSampleTest(unittest.TestCase):
    u"""封の数にちょうど合う大きい標本(76,723 行)。端の一致と、1 違いの不一致(L-0〜L-2 のそれぞれ)。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.rec, cls.ex = exact_rec()

    def judged(self, rec):
        return SC.build_L(rec, self.seal)

    def test_e_1_the_exact_sample_matches_every_row_and_passes_the_record_checks(self):
        J = self.judged(self.rec)
        self.assertEqual([MATCH_W] * 3, [J[k][u"判定"] for k in ("L-0", "L-1", "L-2")])
        self.assertEqual([], judge_problems(self.rec, self.seal))
        self.assertEqual([], record_problems(copy.deepcopy(self.rec), self.ex, self.seal))
        self.assertEqual(10371 + 4 * 16588, len(self.rec[u"行"]))

    def _only_other_changes(self, mutate, red):
        rec = copy.deepcopy(self.rec)
        mutate(rec)
        J = self.judged(rec)
        self.assertEqual(red, [k for k in ("L-0", "L-1", "L-2") if J[k][u"判定"] == DIFF_W], red)
        self.assertEqual([], judge_problems(rec, self.seal))                                    # script の判定はこの門の別計算と同じ

    def test_e_2_one_row_less_or_more_or_one_state_off_turns_the_matching_l_red(self):
        first = lambda rec, p: [i for i, r in enumerate(rec[u"行"]) if r[2] == p]                  # noqa: E731
        # P28E の行を 1 つ消す: L-0(行数)・L-1(P28E の行数)・L-2(P28E の札のある行の GROUNDED が減るなら)
        def drop_p28e_non_grounded(rec):
            i = [k for k in first(rec, "P28E") if rec[u"行"][k][5] != "GROUNDED"][0]
            del rec[u"行"][i]
        self._only_other_changes(drop_p28e_non_grounded, ["L-0", "L-1"])
        # P29E の札なしの行を 1 つ消す: L-1(全部の行)・L-2(全部の GROUNDED が減らない行を消した場合は L-1 だけ)
        def drop_p29e_new_not_grounded(rec):
            i = [k for k in first(rec, "P29E") if rec[u"行"][k][7] == NEWW and rec[u"行"][k][5] != "GROUNDED"][0]
            del rec[u"行"][i]
        self._only_other_changes(drop_p29e_new_not_grounded, ["L-1"])
        # P30E の札なしの行の state を GROUNDED でないものに: 全部の GROUNDED だけが 1 減る
        def flip_p30e_new(rec):
            i = [k for k in first(rec, "P30E") if rec[u"行"][k][7] == NEWW and rec[u"行"][k][5] == "GROUNDED"][0]
            rec[u"行"][i][5] = "VALUE_MISMATCH"
        self._only_other_changes(flip_p30e_new, ["L-2"])
        # P32E の札のある行の state を GROUNDED でないものに: 全部と札のある行の両方の GROUNDED が減る
        def flip_p32e_labelled(rec):
            i = [k for k in first(rec, "P32E") if rec[u"行"][k][7] == EXIST and rec[u"行"][k][5] == "GROUNDED"][0]
            rec[u"行"][i][5] = "VALUE_MISMATCH"
        self._only_other_changes(flip_p32e_labelled, ["L-2"])
        # P33E の札のある行を札なしにする(札のある行数 -1 = L-1・札のある GROUNDED が減る場合は L-2 も)
        def relabel_p33e(rec):
            i = [k for k in first(rec, "P33E") if rec[u"行"][k][7] == EXIST and rec[u"行"][k][5] != "GROUNDED"][0]
            rec[u"行"][i][6] = NONE_WORD
        self._only_other_changes(relabel_p33e, ["L-1"])

        # 数が 1 多い向きも不一致(『以上』で通さない): 札のない行 1 つ・札のある行 1 つを GROUNDED にする
        def raise_p30e_new(rec):
            i = [k for k in first(rec, "P30E") if rec[u"行"][k][7] == NEWW and rec[u"行"][k][5] != "GROUNDED"][0]
            rec[u"行"][i][5] = "GROUNDED"
        self._only_other_changes(raise_p30e_new, ["L-2"])

        def raise_p29e_labelled(rec):
            i = [k for k in first(rec, "P29E") if rec[u"行"][k][7] == EXIST and rec[u"行"][k][5] != "GROUNDED"][0]
            rec[u"行"][i][5] = "GROUNDED"
        self._only_other_changes(raise_p29e_labelled, ["L-2"])

        def raise_p28e(rec):
            i = [k for k in first(rec, "P28E") if rec[u"行"][k][5] != "GROUNDED"][0]
            rec[u"行"][i][5] = "GROUNDED"
        self._only_other_changes(raise_p28e, ["L-2"])

        def add_p29e_row(rec):
            at = max(first(rec, "P29E"))
            rec[u"行"].insert(at + 1, [u"B0_F1_m", "F1", "P29E", 9, 9, "VALUE_MISMATCH", NONE_WORD, NEWW])
        self._only_other_changes(add_p29e_row, ["L-1"])

    def test_e_3_the_l0_fields_turn_l0_red_only(self):
        for fn in (lambda r: r[u"本"][0][u"L-0 の差"].update({u"P28E のみ": 1}), lambda r: r[u"本"][0][u"L-0 の差"].update({u"札のみ": 1}),
                   lambda r: r.update({u"札の記録の (本, id) の数": 10372}), lambda r: r.update({u"札の記録の (本, id) の数": 10370})):
            self._only_other_changes(fn, ["L-0"])

    def test_e_4_the_values_text_and_the_table_are_rebuilt_from_the_record(self):
        J = self.judged(self.rec)
        self.assertIn(u"P29E 16,588 / 10,357", SC.fmt_L("L-1", J["L-1"]))
        self.assertIn(u"P33E 11,625 / 6,979", SC.fmt_L("L-2", J["L-2"]))
        self.assertIn(u"P28E 10,371 / 10,371", SC.fmt_L("L-1", J["L-1"]))
        lines = SC.render_pred(J, self.seal).split(u"\n")
        self.assertEqual(5, len(lines))
        self.assertEqual(lines, indep_pred_lines(self.rec, self.seal))


class RatesTest(unittest.TestCase):
    def test_f_1_the_rate_agrees_with_the_independent_decimal_rounding_on_a_grid_including_ties(self):
        for n in list(range(0, 41)) + [2000, 2001, 3000, 4000, 6231, 9578, 10357, 16588]:
            for g in sorted(set(range(0, min(n, 41) + 1)) | set([n, n // 2, n // 3, (n * 17) // 40, n - 1] if n else [0])):
                if g < 0 or g > n:
                    continue
                self.assertEqual(indep_rate(g, n), SC.rate_str(g, n), (g, n))
        self.assertEqual(u"なし", SC.rate_str(0, 0))
        self.assertEqual(u"0.1", SC.rate_str(1, 2000))                                           # 0.05 は切り上げ
        self.assertEqual(u"0.2", SC.rate_str(3, 2000))                                           # 0.15 は切り上げ(float の %.1f は 0.1)
        self.assertEqual(u"0.1", u"%.1f" % (100.0 * 3 / 2000))                                    # 前提: float の書き方では 0.1 になる(だから整数で書く)

    def test_f_2_counts_equal_the_independent_counts_and_the_ranges_nest(self):
        rec, _ex = sample_record(5)
        rows = rec[u"行"]
        want = indep_group_counts(rows)
        got = SC.row_group_counts(rows)
        self.assertEqual(want, dict((k, tuple(v)) for k, v in got.items()))
        for p in PROFILES:
            n = lambda g: want[(p, g)][0]                                                         # noqa: E731
            self.assertEqual(n(u"全部の行"), n(u"札のある行") + n(u"札の無い行"))
            self.assertEqual(n(u"札のある行"), n(u"札 真") + n(u"札 偽") + n(u"札 判定不能"))
            self.assertEqual(n(u"全部の行"), sum(1 for r in rows if r[2] == p))
        self.assertEqual(0, want[("P28E", u"札の無い行")][0] - sum(1 for r in rows if r[2] == "P28E" and r[6] == NONE_WORD))
        fwant = indep_form_counts(rows)
        fgot = SC.form_group_counts(rows)
        self.assertEqual(fwant, dict((k, tuple(v)) for k, v in fgot.items()))
        self.assertEqual(sum(v[0] for (f, p, g), v in fwant.items() if g == u"札のある行" and p == "P29E"), want[("P29E", u"札のある行")][0])

    def test_f_3_a_range_with_no_rows_prints_none_not_zero(self):
        rec, _ex = sample_record()
        rows = [r for r in rec[u"行"] if r[6] != u"偽"]
        lines = SC.render_rates(rows).split(u"\n")
        self.assertTrue(any(l.startswith(u"| P28E | 札 偽 | 0 | 0 | なし |") for l in lines))
        self.assertEqual(lines, indep_rates_lines(rows))


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.rec, cls.ex = sample_record(5)
        cls.doc = sample_doc(cls.rec, cls.seal)

    def test_d_1_the_sample_document_follows_the_record(self):
        self.assertEqual([], doc_problems(self.doc, self.rec, self.seal))

    def test_d_2_one_changed_character_in_a_table_cell_turns_it_red(self):
        lines = self.doc.split(u"\n")
        for marker in (u"<!-- 門:start pred -->", u"<!-- 門:start rates -->", u"<!-- 門:start forms -->"):
            i = lines.index(marker) + 3                         # 表の 1 行目(データ行)
            for j in (i, i + 1, i + 2):
                for cell_idx in (1, 3, 4, 5):
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
        for name in ("pred", "rates", "forms"):
            self.assertNotEqual([], doc_problems(self.doc.replace(u"門:start %s" % name, u"門:start other"), self.rec, self.seal), name)
        lines = self.doc.split(u"\n")
        for marker in (u"<!-- 門:start pred -->", u"<!-- 門:start rates -->", u"<!-- 門:start forms -->"):
            i = lines.index(marker) + 3
            self.assertNotEqual([], doc_problems(u"\n".join(lines[:i] + lines[i + 1:]), self.rec, self.seal), marker)          # 行が 1 つ欠けた
        self.assertNotEqual([], doc_problems(self.doc + u"\n<!-- 門:start x -->\na\n<!-- 門:end -->\n", self.rec, self.seal))

    def test_d_4_a_changed_record_turns_the_document_red(self):
        rec2 = copy.deepcopy(self.rec)
        i = [k for k, r in enumerate(rec2[u"行"]) if r[2] == "P33E" and r[5] != "GROUNDED"][0]
        rec2[u"行"][i][5] = "GROUNDED"
        self.assertNotEqual([], doc_problems(self.doc, rec2, self.seal))
        rec3 = copy.deepcopy(self.rec)
        j = [k for k, r in enumerate(rec3[u"行"]) if r[2] == "P29E" and r[6] == u"真"][0]
        rec3[u"行"][j][6] = u"偽"
        self.assertNotEqual([], doc_problems(self.doc, rec3, self.seal))

    def test_d_5_prose_numbers_forbidden_words_and_docids_turn_it_red(self):
        self.assertNotEqual([], doc_problems(self.doc + u"\n札のある行は 123 行でした。\n", self.rec, self.seal))                # 3 桁の数に【門なし】が無い
        self.assertEqual([], doc_problems(self.doc + u"\n札のある行は 123 行でした。" + NOT_GATED + u"\n", self.rec, self.seal))
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(self.doc + u"\n" + w + u"\n", self.rec, self.seal), w)
        self.assertNotEqual([], doc_problems(self.doc + u"\nS100" + u"ABCD\n", self.rec, self.seal))

    def test_d_6_the_tally_prints_the_three_tables_from_a_record(self):
        out = []
        SC.run_tally(root=ROOT, say=out.append, rec=self.rec)
        text = u"\n".join(out)
        self.assertIn(SC.render_pred(SC.build_L(self.rec, self.seal), self.seal), text)
        self.assertIn(SC.render_rates(self.rec[u"行"]), text)
        self.assertIn(SC.render_forms(self.rec[u"行"]), text)
        self.assertEqual(5 + 1 + 32 + 1 + 102, len(text.split(u"\n")))                         # 表 3 つ(pred 2+3 行・rates 2+30 行・forms 2+100 行)と空行 2 つ

    def test_d_7_the_tables_have_the_declared_headers_and_sizes(self):
        got = PR.doc_blocks(self.doc)
        self.assertEqual((PRED_HEAD, RATES_HEAD, FORMS_HEAD), (got["pred"][0], got["rates"][0], got["forms"][0]))
        self.assertEqual((5, 32, 102), (len(got["pred"]), len(got["rates"]), len(got["forms"])))


class OrderChainTest(unittest.TestCase):
    SEALF = "docs/seal.md"
    SCRIPTS = ["measure/s.py", "tests/g1.py", "tests/g2.py"]
    REC = "fixtures/xbrl/labelonly/rec.json"
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
        for rel in ("fixtures/xbrl/nonfunc/timing_2026-11-10.json", "fixtures/xbrl/tperiod/moves_200_2026-11-09.json", "fixtures/xbrl/pbind/moves_200_2026-11-06.json"):
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
        J = SC.build_L(rec, self.seal)
        self.assertEqual(["L-0", "L-1", "L-2"], list(J))

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


# ================================================================ 小さな 1 docID の走り(cache を読むだけ。記録は TMPDIR の下。cache が無ければ skip)
class RealRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HAVE_CACHE:
            raise unittest.SkipTest(u"cache が無い(実書類を通す試験は skip)")
        cls.seal = read(SEAL_REL)
        cls.doc = jload(N_AI200_REL)[u"本"][0][u"docID"]

    def test_x_1_one_docid_runs_with_rc_0_and_the_record_has_the_right_shape(self):
        u"""``run --only <1 docID> --out <TMPDIR の下> --procs 3`` が rc 0。記録の形・札の結び方・N の便の記録との一致を門の検査に通す。"""
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            out = os.path.join(d, "one.json")
            r = subprocess.run([sys.executable, os.path.join(ROOT, SCRIPT_REL), "run", "--only", self.doc, "--out", out, "--procs", "3"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True)
            self.assertEqual(0, r.returncode, r.stdout[-1500:])
            with io.open(out, encoding="utf-8") as fh:
                rec = json.load(fh)
        ex = real_expect(only=self.doc)
        self.assertEqual(10, len(ex.names))
        self.assertEqual([], record_problems(rec, ex, self.seal))
        self.assertEqual(RANGE_ONLY, rec[u"範囲"])
        self.assertEqual(ex.names, [b[u"本の id"] for b in rec[u"本"]])
        self.assertEqual(ex.label_total, rec[u"札の記録の (本, id) の数"])

    def test_x_2_the_default_out_is_refused_for_an_only_run_and_nothing_is_written(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with self.assertRaises(SC.Stop):
                SC.run(root=d, only=self.doc, say=lambda *a: None)
            self.assertEqual([], os.listdir(d))


if __name__ == "__main__":
    unittest.main()
