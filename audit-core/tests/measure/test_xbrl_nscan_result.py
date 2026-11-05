# -*- coding: utf-8 -*-
"""H(注入の仕掛けの数の読みに「万円」と「億+万の複合」を足す。切り替え ``yen_scan_2026_11_05``)の測定の結果の門。封 docs/XBRL_INJECT_SCAN_FIX_SEAL_2026-11-05.md §5(追記 1 まで)。

記録 2 つ(``fixtures/xbrl/nscan/``: offcheck・inject)から、封 §3 の予測 H-1〜H-10 と §4 の採用の基準 K-1〜K-4 を**機械で求め**(予測の幅は封の字から読む。字のコピーにしない)、
結果の文書 ``docs/XBRL_INJECT_SCAN_FIX_RESULT_2026-11-05.md`` の表(``<!-- 門:start pred -->``・``<!-- 門:start judge -->`` の中)を記録から作り直した表と一行も違わないことを見る。
測定の script(``measure/xbrl_nscan_2026-11-05.py`` の ``build_J``・``judge_from``・``render_pred``・``render_judge``)の関数を呼んで照らす。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文など)が無い・key_leaks が空・docID を持つ記録が ``LATER_NAMING_FILES`` に宣言され、script が ``LATER_HARNESS_FILES`` に宣言されている・
     cache の前後が同じ・script と lib と前の便の script の sha256 が現物と一致・封の commit の numbers.py の sha256 が git の blob と一致・engine の指紋が封の commit の木から作り直した値と一致する。
  b  記録の中身が再計算と一致する: offcheck の本ごとの整合と集計・K-4 の試験の記録(封の変異の名前・全部赤・戻した)・inject の本ごとの数えと行の整合・集計(``inject_summaries``)・
     H の欄(``h_columns``)・既存の site の率(RB の記録そのまま)・限界(封 §6 の字)。
  c  判定: 記録(の欄)を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。採用は K-1〜K-4 を全部満たすときだけ。
  d  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 89afc79 ⊏ lib を触った commit ⊏ 記録・結果の文書(script・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  g  変異: 小さい標本の記録 2 つと文書で同じ検査が緑 → 変異(記録の数・表の 1 字・封の予測の 1 字・順序・記録の禁止欄・指紋の 1 字・cache の前後・切り替えの配線)で赤。

記録が無いときは (a)(b)(d)(e) の本番の記録の試験を skip する(skip でも行が出ることを試験が確かめる)。標本の試験 (c)(g) は記録が無くても走る。この file は docID の字を持たない。
"""
import ast
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
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SG = load_module("tests/measure/test_xbrl_nscan_seal.py", "nscan_seal_gate_for_result")        # 封の門の部品。門としては走らせない
PR = SG.PR                                                                                    # doc_blocks・prose_problems・order_problems・Repo
NS = SG.NS
RM = NS.RM
NF = NS.NF
GEN, RUN, TUNE = NS.GEN, NS.RUN, NS.TUNE
N, SC = NS.N, NS.SC

SEAL_REL = NS.SEAL_REL
DOC_REL = NS.DOC_REL
SEAL_COMMIT_SHORT = NS.SEAL_COMMIT
REC_REL = collections.OrderedDict(NS.REC_REL)
SCRIPT_REL = "measure/xbrl_nscan_2026-11-05.py"
LIB_RELS = NS.LIB_RELS
FLAG = NS.FLAG
NOT_GATED = PR.NOT_GATED
HIT, MISS = NS.HIT, NS.MISS
FORBIDDEN_KEYS = tuple(RUN.FORBIDDEN_KEYS) + (u"理由", u"根拠", u"周り", u"content")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = SG.DOCID_RE
FOR_RESULT_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
HAVE_CACHE = all(os.path.isdir(p) for p in NS.caches_all().values())
INJECT_PROFILES = NS.INJECT_PROFILES
STATES = NF.STATES
#: 封 §3・§4 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("H-1", (200, 200)),
    ("H-2", collections.OrderedDict([(u"計", (7250.0, 7350.0)), (u"億+万", (5400.0, 5550.0)), (u"万", (1780.0, 1880.0)), (u"兆+億", (4.0, 8.0)), (u"is_quantity 真", (7150.0, 7300.0))])),
    ("H-3", (12200.0, 12600.0)),
    ("H-4", collections.OrderedDict([(u"作れる site", (1350.0, 1550.0)), (u"採った", (700.0, 800.0)), (u"うち P30E が GROUNDED", (480.0, 600.0))])),
    ("H-5", collections.OrderedDict([(u"作れる site", (4500.0, 4900.0)), (u"採った", (1150.0, 1280.0)), (u"P29E に対応が付く行", (1130.0, 1250.0))])),
    ("H-6", (7.0, 12.0)),
    ("H-7", collections.OrderedDict([("T1_VALUE", (0.0, 0.6)), ("T8_REL", (0.0, 0.5))])),
    ("H-8", collections.OrderedDict([("T1_VALUE", (82.0, 90.0)), ("T8_REL", (86.0, 93.0))])),
    ("H-9", (0.0, 5.0)),
    ("H-10", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"注入後の値(円)が refs に在る行", (0, 3))])),
    ("K-1", (200, 200)), ("K-2", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0)])), ("K-3", 1500.0),
    ("K-4", [u"切り替えを外す", u"万円 の行を 1e3 に壊す", u"描きのコンマ", u"先頭の 0", u"複合の value の指数"])])
#: 注入の土台の字・site の字(測定の script の定数と同じでなければ赤)
BASE_WORD_PIN = u"無改変の文で P30E が GROUNDED の claim"
NEW_WORD_PIN = u"新しい token(複合の数・万円)の site だけ"
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
G, V_, U_, P_ = "GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def jload(rel):
    return json.loads(read(rel))


def sha256_rel(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def records_exist(keys=None):
    if FORCE["no_records"]:
        return False
    return all(os.path.exists(os.path.join(ROOT, REC_REL[k])) for k in (keys or REC_REL))


def load_records():
    return collections.OrderedDict((k, jload(v)) for k, v in REC_REL.items())


def norm(v):
    return json.loads(json.dumps(v))


class Patch(object):
    u"""module の属性を差し替えて、終わりに戻す。"""

    def __init__(self):
        self.saved = []

    def set(self, mod, name, value):
        self.saved.append((mod, name, getattr(mod, name)))
        setattr(mod, name, value)

    def undo(self):
        for mod, name, old in reversed(self.saved):
            setattr(mod, name, old)
        self.saved = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.undo()
        return False


# ---------------------------------------------------------------- engine の指紋(封の commit の木から作り直す。engine はこの便で変えない)
_FP = []


def engine_fingerprint_at_seal():
    u"""封の commit の木の ``adapters/xbrl`` と ``core/py/audit_core`` の .py から作った指紋 {adapter_xbrl_py_sha256, core_py_sha256}。"""
    if not _FP:
        seal = SG.seal_commit(REPO)
        if seal is None:
            raise AssertionError(u"封の commit が履歴に無い")
        from adapters.xbrl import verify_document as VD
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            arc = subprocess.run(["git", "archive", seal, PREFIX + "adapters/xbrl", PREFIX + "core/py/audit_core"], cwd=REPO, stdout=subprocess.PIPE, check=True)
            subprocess.run(["tar", "-x", "-C", d], input=arc.stdout, check=True)
            a, _na = VD._py_digest(os.path.join(d, PREFIX, "adapters", "xbrl"))
            c, _nc = VD._py_digest(os.path.join(d, PREFIX, "core", "py", "audit_core"))
        _FP.append({"adapter_xbrl_py_sha256": a, "core_py_sha256": c})
    return _FP[0]


def seal_blob_sha(rel):
    u"""封の commit の blob の sha256。"""
    seal = SG.seal_commit(REPO)
    p = subprocess.run(["git", "show", "%s:%s%s" % (seal, PREFIX, rel)], cwd=REPO, stdout=subprocess.PIPE, check=True)
    return hashlib.sha256(p.stdout).hexdigest()


# ---------------------------------------------------------------- 封の字(a)
def norm_t(v):
    if isinstance(v, dict):
        return dict((k, norm_t(x)) for k, x in v.items())
    if isinstance(v, (tuple, list)):
        return [norm_t(x) for x in v]
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    return v


def bounds_problems(seal):
    u"""封の字から読んだ予測の幅が、ここに留めた値と同じか。"""
    out = []
    try:
        got = NS.seal_bounds(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return [u"封から幅を読めない(%s)" % type(e).__name__]
    for k, v in BOUNDS_PIN.items():
        g = got.get(k)
        if json.dumps(norm_t(g), sort_keys=True) != json.dumps(norm_t(v), sort_keys=True):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, g, v))
    if list(NS.seal_pred_rows(seal)) != list(SG.PRED_IDS) or list(NS.seal_k_rows(seal)) != list(SG.K_IDS):
        out.append(u"封の予測の行が H-1〜H-10 でない・K の行が K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 記録(a)(b)
def walk(o):
    return list(RUN.walk_keys(o))


def header_problems(k, rec, full):
    u"""記録の頭(封・script・lib・前の便の script・engine・cache)。"""
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"%s: 封の名か commit が違う" % k)
    want = collections.OrderedDict([
        (u"この script の sha256", sha256_rel(SCRIPT_REL)), (u"rmix script の sha256", sha256_rel(NS.RM_SCRIPT_REL)),
        (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")), (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")),
        (u"生成の script の sha256", sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")), (u"RB の記録の sha256", sha256_rel(NS.RB_INJECT_REL)),
        (u"封の commit の numbers.py の sha256", seal_blob_sha("measure/lib/numbers.py"))])
    for name, v in want.items():
        if rec.get(name) != v:
            out.append(u"%s: %s が現物と違う" % (k, name))
    gens = dict((src, sha256_rel(p["gen"])) for src, p in NS.SOURCES.items())
    if norm(rec.get(u"生成の記録の sha256")) != gens:
        out.append(u"%s: 生成の記録の sha256 が現物と違う" % k)
    if norm(rec.get(u"lib の指紋")) != dict((rel, sha256_rel(rel)) for rel in LIB_RELS):
        out.append(u"%s: lib の指紋が現物と違う" % k)
    if rec.get(u"profile") != list(INJECT_PROFILES):
        out.append(u"%s: profile が (P29E, P30E) でない" % k)
    fp = rec.get(u"engine の指紋") or {}
    want_fp = engine_fingerprint_at_seal()
    for name in want_fp:
        if fp.get(name) != want_fp[name]:
            out.append(u"%s: engine の指紋 %s が封の commit の木から作り直した値と違う" % (k, name))
    cb = rec.get(u"cache の前後") or {}
    if cb.get(u"変化なし") is not True or cb.get(u"前") != cb.get(u"後"):
        out.append(u"%s: cache の前後が同じでない" % k)
    sw = rec.get(u"切り替え") or {}
    if sw.get(u"名前") != FLAG or sw.get(u"配線の問題") != []:
        out.append(u"%s: 切り替えの名前が違う・配線の問題が空でない" % k)
    if k == "offcheck" and sw.get(u"この記録を作ったときの値") is not False:
        out.append(u"%s: offcheck を切り替え 偽 で走らせていない" % k)
    if k == "inject" and (sw.get(u"inject の中の値") is not True or sw.get(u"出たあとの値") is not False):
        out.append(u"%s: inject の中が真・出たあとが偽になっていない" % k)
    if full and rec.get(u"範囲") != u"全 200 本":
        out.append(u"%s: 範囲が全 200 本でない" % k)
    return out


def clean_problems(k, rec):
    out = []
    bad = sorted(set(x for x in walk(rec) if x in FORBIDDEN_KEYS))
    if bad:
        out.append(u"%s: 記録に repo へ入れない欄がある: %s" % (k, u",".join(bad)))
    text = json.dumps(rec, ensure_ascii=False)
    for w in COMPANY_WORDS:
        if w in text:
            out.append(u"%s: 会社名らしい字がある" % k)
    try:
        RUN.assert_clean(copy.deepcopy(rec))
    except GEN.Stop:
        out.append(u"%s: 鍵らしい字が記録に在る" % k)
    if rec.get(u"key_leaks", []) != []:
        out.append(u"%s: key_leaks が空でない" % k)
    return out


def rb_rows_by_book():
    rb = NS.load_rb(ROOT)
    out = collections.defaultdict(list)
    for r in rb[u"行"]:
        out[(r["docID"], r["form"], r["model"])].append(r)
    return out


def offcheck_book_problems(b):
    out = []
    nm = b[u"name"]
    for key in (u"token の sha256", u"封の commit の lib の token の sha256", u"関数の出力の sha256", u"封の commit の lib の関数の出力の sha256"):
        if not (isinstance(b[key], str) and HEX64.match(b[key])):
            out.append(u"%s: %s が sha256 の形でない" % (nm, key))
    same_lib = b[u"token の sha256"] == b[u"封の commit の lib の token の sha256"] and b[u"関数の出力の sha256"] == b[u"封の commit の lib の関数の出力の sha256"]
    if b[u"lib が封の commit と一致"] is not same_lib:
        out.append(u"%s: lib が封の commit と一致 が sha256 から数えた値と合わない" % nm)
    if b[u"一致"] is not bool(b[u"lib が封の commit と一致"] and b[u"RB の記録の行と一致"] and b[u"RB の記録の数えと一致"] and b[u"groups を持つ token"] == 0):
        out.append(u"%s: 一致 が他の欄と合わない" % nm)
    for key in (u"RB の記録の行と一致", u"RB の記録の数えと一致", u"lib が封の commit と一致", u"一致"):
        if not isinstance(b[key], bool):
            out.append(u"%s: %s が真偽でない" % (nm, key))
    for key in (u"token の数", u"groups を持つ token", u"行の数", u"RB の記録の行の数"):
        if not isinstance(b[key], int) or isinstance(b[key], bool) or b[key] < 0:
            out.append(u"%s: %s が 0 以上の整数でない" % (nm, key))
    if b[u"RB の記録の行と一致"] is True and b[u"行の数"] != b[u"RB の記録の行の数"]:
        out.append(u"%s: 行が一致なのに行の数が違う" % nm)
    return out


def k4_record_problems(tests, seal_names, full):
    u"""K-4 の試験の記録の形と中身。full なら現物の試験 file の sha256 と試験の本数も照らす。"""
    out = []
    try:
        old, added, muts = tests[u"既存の試験(偽のまま)"], tests[u"足した試験"], tests[u"変異"]
    except (KeyError, TypeError):
        return [u"試験の記録が無い・形が違う"]
    out += NS.k4_problems(tests, seal_names)
    if old.get(u"path") != NS.TEST_INJECT_REL or added.get(u"path") != NS.TEST_YEN_REL:
        out.append(u"試験の path が違う")
    for m in muts:
        if m[u"試験"] != added[u"試験"]:
            out.append(u"変異 %s で走らせた試験の本数が足した試験と違う" % m[u"名前"])
    if full:
        for t in (old, added):
            if t.get(u"sha256") != sha256_rel(t[u"path"]):
                out.append(u"%s の sha256 が現物と違う" % t[u"path"])
            spec = importlib.util.spec_from_file_location("count_for_nscan_gate", os.path.join(ROOT, t[u"path"]))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if unittest.defaultTestLoader.loadTestsFromModule(mod).countTestCases() != t[u"試験"]:
                out.append(u"%s の試験の本数が現物と違う" % t[u"path"])
    return out


def offcheck_problems(rec, full):
    out = []
    books = rec[u"本"]
    for b in books:
        out += offcheck_book_problems(b)
    try:
        agg = norm(NS.offcheck_aggregate(books))
    except Exception as e:                                   # noqa: BLE001  壊れた記録は集計できない = 赤
        return out + [u"offcheck: 本から集計を作れない(%s)" % type(e).__name__]
    if agg != rec[u"集計"]:
        out.append(u"offcheck: 集計が本から作り直した値と違う")
    out += k4_record_problems(rec.get(u"試験"), NS.seal_mutation_names(read(SEAL_REL)), full)
    if full:
        names = [b[u"name"] for src in NS.SOURCES.values() for b in jload(src["claims"])[u"本"] if not b.get(u"欠け")]
        if [b[u"name"] for b in books] != names or len(books) != 200:
            out.append(u"offcheck: 本が 200 本(前の便の claims の並び)でない")
        rb = rb_rows_by_book()
        rbc = jload(NS.RB_INJECT_REL)[u"本ごとの数え"]
        for b in books:
            if b[u"RB の記録の行の数"] != len(rb.get((b[u"docID"], b[u"form"], b[u"model"]), [])) or b[u"name"] not in rbc:
                out.append(u"offcheck: RB の記録の行の数か本が RB の記録と違う: %s" % b[u"name"])
                break
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(NS.caches_all())):
            out.append(u"offcheck: cache の件数か名前が記録の前と違う")
    return out


def count_problems(name, c, rows, cap):
    u"""本ごとの数え 1 本の整合(自分の欄の間と、その本の行との関係)。"""
    out = []
    st = c[u"token の数え"]
    new = st[u"新しい token"]
    if new[u"計"] != new[u"億+万"] + new[u"万"] + new[u"兆+億"] + new[u"その他"] or new[u"is_quantity 真"] > new[u"計"]:
        out.append(u"%s: 新しい token の欄が合わない" % name)
    cov = st[u"覆われた既存の token"]
    if cov[u"うち is_quantity 真"] > cov[u"捨てた"] or cov[u"うち単位が付いていた"] > cov[u"捨てた"]:
        out.append(u"%s: 覆われた既存の token の欄が合わない" % name)
    if cov[u"同じ span の置き換え"] > new[u"計"]:
        out.append(u"%s: 同じ span の置き換えが新しい token より多い" % name)
    if st[u"既存の token の単位だけ 万円 に変わったもの"][u"うち is_quantity 真"] > st[u"既存の token の単位だけ 万円 に変わったもの"][u"件"]:
        out.append(u"%s: 単位だけ変わった既存の token の欄が合わない" % name)
    fam = st[u"円族の token(is_quantity 真)"]
    if u"注入しない" in c:
        if rows:
            out.append(u"%s: 注入しない本に行がある" % name)
        return out
    t1, t8 = c["T1_VALUE"], c["T8_REL"]
    pop = c[u"T1_VALUE の作れる site の状態"]
    ok_keys = (NS.LINKED, NS.UNLINKED)
    s1 = sum(t1.get(k, 0) for k in ok_keys + (NS.STATUS_NOT_G, NS.STATUS_NO_BASE))
    if s1 != t1[u"採った"] or t1[u"採った"] > t1[u"作れる site"] or t1[u"採った"] > cap or sum(pop.values()) != t1[u"作れる site"]:
        out.append(u"%s: T1_VALUE の数えが合わない" % name)
    r1 = [r for r in rows if r[u"型"] == "T1_VALUE"]
    r8 = [r for r in rows if r[u"型"] == "T8_REL"]
    if len(r1) != t1.get(NS.LINKED, 0) + t1.get(NS.UNLINKED, 0):
        out.append(u"%s: T1_VALUE の行の数が数えと合わない" % name)
    s8 = sum(t8.get(k, 0) for k in ok_keys + (NS.STATUS_NOT_G, NS.STATUS_NO_BASE))
    if s8 != t8[u"円族の新しい token"] or t8[u"円族の新しい token"] > new[u"is_quantity 真"] or t8[u"円族の新しい token"] > fam[u"真"]:
        out.append(u"%s: T8_REL の円族の新しい token の数えが合わない" % name)
    can = t8.get(NS.LINKED, 0) + t8.get(NS.UNLINKED, 0) - t8.get(NS.NO_PICK, 0)
    if t8[u"作れる site"] != can or t8[u"採った"] != min(cap, can) or len(r8) != t8[u"採った"]:
        out.append(u"%s: T8_REL の作れる site・採った・行の数が合わない" % name)
    return out


def inject_problems(rec, full):
    out = []
    if rec.get(u"profile") != list(INJECT_PROFILES):
        out.append(u"inject: profile が (P29E, P30E) でない")
    if rec[u"型"].get(u"土台") != BASE_WORD_PIN or NS.BASE_WORD != BASE_WORD_PIN:
        out.append(u"inject: 型.土台 の字が P30E が GROUNDED の claim でない")
    if rec[u"型"].get(u"site") != NEW_WORD_PIN or NS.NEW_WORD != NEW_WORD_PIN:
        out.append(u"inject: 型.site の字が新しい token の site だけでない")
    seal = read(SEAL_REL)
    if rec.get(u"限界") != NS.seal_limits(seal) + list(NS.EXTRA_LIMITS) or len(rec.get(u"限界") or []) != 7:
        out.append(u"inject: 限界が封 §6 の字(5 つ)とこの script の限界(2 つ)と違う")
    want = collections.OrderedDict([(u"全体", sum(1 for r in rec[u"行"] if r.get(NS.LINK_KEY) is not True))])
    for t in RUN.INJECT_TYPES:
        want[t] = sum(1 for r in rec[u"行"] if r.get(u"型") == t and r.get(NS.LINK_KEY) is not True)
    if norm(rec.get(u"P29E に対応なしの行の数")) != norm(want):
        out.append(u"inject: P29E に対応なしの行の数が行から数え直した値と違う")
    labels = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
    seen, cnt = set(), collections.Counter()
    for r in rec[u"行"]:
        if r[u"型"] not in RUN.INJECT_TYPES:
            out.append(u"inject: 型が語でない")
        if r[u"id"] in seen:
            out.append(u"inject: 同じ注入の id が 2 回ある")
        seen.add(r[u"id"])
        cnt[(r[u"docID"], r[u"form"], r[u"model"], r[u"型"])] += 1
        linked = r.get(NS.LINK_KEY)
        unmapped = {u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}
        if not isinstance(linked, bool):
            out.append(u"inject: P29E の土台に対応の欄が真偽でない")
        elif not linked and norm(r["P29E"]) != unmapped:
            out.append(u"inject: P29E の土台に対応が無い行の P29E の欄が対応なしでない")
        if r["P30E"][u"対応"] is True and r["P30E"][u"結果"] == TUNE.LABEL_UNMAPPED:
            out.append(u"inject: P30E の欄の対応と結果が合わない")
        for key in (u"round-trip", u"読み直し", u"注入後の値(円)が refs に在る", u"先頭の位が減った", u"コンマ"):
            if not isinstance(r.get(key), bool):
                out.append(u"inject: 行の %s が真偽でない" % key)
        if r.get(u"単位") not in (u"万円", u"億円") or not isinstance(r.get(u"形"), str) or not r.get(u"形"):
            out.append(u"inject: 行の単位か形が新しい token の形でない")
        if r[u"型"] == "T8_REL" and (r.get("r") not in TUNE.T8_R_VALUES or not (1 <= r[u"r を決めた回"] <= TUNE.T8_TRIES)):
            out.append(u"inject: T8_REL の r が決めた値でない")
        for p in INJECT_PROFILES:
            c = r[p]
            if c[u"結果"] not in labels:
                out.append(u"inject: 結果が classify の語でない")
            if not RUN.reason_ok(c[u"reason"]):
                out.append(u"inject: reason が符号の形でない")
    if any(n > RUN.INJECT_CAP for n in cnt.values()):
        out.append(u"inject: 1 本あたり型ごとの上限 %d を超えている" % RUN.INJECT_CAP)
    by_book = collections.defaultdict(list)
    for r in rec[u"行"]:
        by_book[u"%s_%s_%s" % (r["docID"], r["form"], r["model"])].append(r)
    per = rec[u"本ごとの数え"]
    for name in by_book:
        if name not in per:
            out.append(u"inject: 行の本が本ごとの数えに無い: %s" % name)
    for name, c in per.items():
        try:
            out += count_problems(name, c, by_book.get(name, []), RUN.INJECT_CAP)
        except Exception as e:                               # noqa: BLE001  壊れた記録は数え直せない = 赤
            out.append(u"inject: %s の数えを検査できない(%s)" % (name, type(e).__name__))
    with Patch() as pt:
        pt.set(RUN, "PROFILES", INJECT_PROFILES)
        summ, summ_cmp = (norm(x) for x in NS.inject_summaries(rec[u"行"]))
        bd = norm(NS.breakdown(rec[u"行"]))
    if summ != rec[u"集計"] or rec[u"注入の行の数"] != len(rec[u"行"]):
        out.append(u"inject: 集計が行から作り直した値と違う")
    if summ_cmp != rec.get(NS.COMPARE_KEY):
        out.append(u"inject: 比較用の集計(P29E にも対応が付く site だけ)が行から作り直した値と違う")
    if bd != rec.get(NS.BREAKDOWN_KEY):
        out.append(u"inject: 新しい site の内訳が行から作り直した値と違う")
    try:
        cols = norm(NS.h_columns(per, rec[u"行"]))
    except Exception as e:                                   # noqa: BLE001
        return out + [u"inject: H の欄を作れない(%s)" % type(e).__name__]
    if cols != rec.get(NS.H_KEY):
        out.append(u"inject: H の欄が 本ごとの数え と 行 から作り直した値と違う")
    a, b = rec.get(NS.EXISTING_KEY), rec.get(NS.EXISTING_CMP_KEY)
    for label, x in ((u"既存の site の率", a), (u"既存の site の率・比較用", b)):
        if not isinstance(x, dict) or list(x) != list(RUN.INJECT_TYPES) or any(list(x[t]) != list(INJECT_PROFILES) for t in RUN.INJECT_TYPES):
            out.append(u"inject: %s の形が 型 × profile でない" % label)
    if full:
        rb = NS.load_rb(ROOT)
        want_a, want_b = (norm(x) for x in NS.existing_rates(rb))
        if a != want_a or b != want_b:
            out.append(u"inject: 既存の site の率が RB の記録そのままでない")
        names = [x[u"name"] for src in NS.SOURCES.values() for x in jload(src["claims"])[u"本"] if not x.get(u"欠け")]
        if list(per) != names:
            out.append(u"inject: 本ごとの数えの本が 200 本(前の便の claims の並び)でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(NS.caches_all())):
            out.append(u"inject: cache の件数か名前が記録の前と違う")
    return out


def record_problems(R, full=True):
    u"""記録 2 つの検査(禁止欄・鍵・script と lib の sha256・engine の指紋・cache・再計算)。問題の列。"""
    out = []

    def safe(label, fn, *a):
        try:
            return fn(*a)
        except Exception as e:                               # noqa: BLE001  壊れた記録は検査できない = 赤(例外で落とさず問題に数える)
            return [u"%s: 検査できない(%s)" % (label, type(e).__name__)]
    for k, rec in R.items():
        out += safe(k, clean_problems, k, rec)
        out += safe(k, header_problems, k, rec, full)
    out += safe("offcheck", offcheck_problems, R["offcheck"], full)
    out += safe("inject", inject_problems, R["inject"], full)
    return out


def judge_problems(R, seal):
    u"""判定の関数が記録から作り直せるか(壊れた記録は赤)。"""
    try:
        J = NS.build_J(R, seal)
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"H"]) != list(SG.PRED_IDS) or list(J[u"K"]) != list(SG.K_IDS):
        out.append(u"判定の行が H-1〜H-10・K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R, seal):
    J = NS.build_J(R, seal)
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != NS.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("judge") != NS.render_judge(J, seal).split(u"\n"):
        out.append(u"表 judge が記録から作り直した表と違う")
    for k in got:
        if k not in ("pred", "judge"):
            out.append(u"知らない表 %s" % k)
    if DOCID_RE.search(doc):
        out.append(u"docID が文書にある")
    for w in FOR_RESULT_WORDS:
        if w in doc:
            out.append(u"禁止語: " + w)
    out += [u"散文の数に【門なし】が無い: 行 %d %s" % x for x in PR.prose_problems(doc)]
    return out


# ---------------------------------------------------------------- 順序(e)
def order_of(root, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = (list(REC_REL.values()) + [DOC_REL]) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, list(LIB_RELS), others)


# ================================================================ 小さい標本の記録 2 つ(通信しない・cache を読まない)
ITEMS = [dict(docID="DOC1", form="F1", model="m1", writer="W1"), dict(docID="DOC2", form="F5", model="m2", writer="W2")]


def sample_tests():
    names = list(BOUNDS_PIN["K-4"])
    return collections.OrderedDict([
        (u"既存の試験(偽のまま)", collections.OrderedDict([(u"path", NS.TEST_INJECT_REL), (u"sha256", "a" * 64), (u"試験", 96), (u"失敗", 0), (u"エラー", 0), (u"skip", 0)])),
        (u"足した試験", collections.OrderedDict([(u"path", NS.TEST_YEN_REL), (u"sha256", "b" * 64), (u"試験", 23), (u"失敗", 0), (u"エラー", 0), (u"skip", 0)])),
        (u"変異", [collections.OrderedDict([(u"名前", n), (u"試験", 23), (u"赤", i + 1), (u"戻した", True)]) for i, n in enumerate(names)]),
        (u"変異のあと lib が元に戻った", True)])


def sample_header(k, step):
    cache = collections.OrderedDict([("edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": "2" * 64})])
    h = collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"step", step), (u"HEAD の commit", "3" * 40),
        (u"この script の sha256", sha256_rel(SCRIPT_REL)), (u"生成の script の sha256", sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")),
        (u"生成の記録の sha256", collections.OrderedDict((src, sha256_rel(p["gen"])) for src, p in NS.SOURCES.items())),
        (u"engine の指紋", dict(engine_fingerprint_at_seal(), adapter_xbrl_py_files=16, core_py_files=4, git_commit="3" * 40)),
        (u"種の確認", {u"seed_file": u"x"}), (u"profile", list(INJECT_PROFILES)),
        (u"cache の前後", collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)])),
        (u"rmix script の sha256", sha256_rel(NS.RM_SCRIPT_REL)), (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")),
        (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")), (u"RB の記録の sha256", sha256_rel(NS.RB_INJECT_REL)),
        (u"lib の指紋", collections.OrderedDict((rel, sha256_rel(rel)) for rel in LIB_RELS)),
        (u"封の commit の numbers.py の sha256", seal_blob_sha("measure/lib/numbers.py")), (u"範囲", u"標本")])
    return h


def sample_off_book(item, rows_ok=True, counts_ok=True):
    name = u"%s_%s_%s" % (item["docID"], item["form"], item["model"])
    h = hashlib.sha256(name.encode()).hexdigest()
    h2 = hashlib.sha256((name + u"f").encode()).hexdigest()
    return collections.OrderedDict([
        (u"name", name), (u"docID", item["docID"]), (u"form", item["form"]), (u"model", item["model"]), (u"writer", item["writer"]), (u"材料", "aiforms"),
        (u"token の数", 50), (u"groups を持つ token", 0), (u"token の sha256", h), (u"封の commit の lib の token の sha256", h),
        (u"関数の出力の sha256", h2), (u"封の commit の lib の関数の出力の sha256", h2), (u"lib が封の commit と一致", True),
        (u"行の数", 4), (u"RB の記録の行の数", 4), (u"RB の記録の行と一致", rows_ok), (u"RB の記録の数えと一致", counts_ok),
        (u"一致", bool(rows_ok and counts_ok))])


def sample_offcheck():
    books = [sample_off_book(ITEMS[0]), sample_off_book(ITEMS[1])]
    rec = sample_header("offcheck", u"標本")
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"この記録を作ったときの値", False), (u"配線の問題", [])])
    rec[u"本"] = books
    rec[u"集計"] = norm(NS.offcheck_aggregate(books))
    rec[u"試験"] = sample_tests()
    return norm(rec)


def stats_of(new_oku_man, new_man, new_cho_oku, quantity, fam_false, fam_true):
    total = new_oku_man + new_man + new_cho_oku
    return collections.OrderedDict([
        (u"新しい token", collections.OrderedDict([(u"億+万", new_oku_man), (u"万", new_man), (u"兆+億", new_cho_oku), (u"その他", 0), (u"計", total), (u"is_quantity 真", quantity)])),
        (u"覆われた既存の token", collections.OrderedDict([(u"同じ span の置き換え", new_man), (u"捨てた", 2 * new_oku_man), (u"うち is_quantity 真", 0), (u"うち単位が付いていた", 0)])),
        (u"既存の token の単位だけ 万円 に変わったもの", collections.OrderedDict([(u"件", 0), (u"うち is_quantity 真", 0)])),
        (u"円族の token(is_quantity 真)", collections.OrderedDict([(u"偽", fam_false), (u"真", fam_true)]))])


def inj_row(item, rid, typ, shape, comma, unit, linked, p29, p30, r=None, rt=True, rr=True, refs=False, lead=False):
    def cell(res, state, reason=None):
        return collections.OrderedDict([(u"対応", True), (u"結果", res), (u"state", state), (u"reason", reason)])
    row = collections.OrderedDict([(u"docID", item["docID"]), (u"form", item["form"]), (u"model", item["model"]), (u"writer", item["writer"]),
                                   ("id", u"%s_%s_%s-%s" % (item["docID"], item["form"], item["model"], rid)), (u"型", typ), (u"形", shape), (u"コンマ", comma), (u"単位", unit),
                                   (u"基準の claim", u"N%03d" % (len(rid) + 1)), (NS.LINK_KEY, linked), (u"round-trip", rt), (u"読み直し", rr),
                                   (u"注入後の値(円)が refs に在る", refs), (u"先頭の位が減った", lead)])
    if typ == "T8_REL":
        row["r"], row[u"r を決めた回"] = r, 1
    row["P29E"] = cell(*p29) if linked else TUNE.classify(None, None)
    row["P30E"] = cell(*p30)
    return row


def sample_inject():
    a, c = ITEMS[0], dict(docID="DOC3", form="F1", model="m1", writer="W1")
    pass_ = (TUNE.LABEL_PASS, G)
    named = (TUNE.LABEL_NAMED_ORIGINAL, V_)
    other = (TUNE.LABEL_NAMED_OTHER, V_)
    rows = [
        inj_row(a, "T1-01", "T1_VALUE", u"億+万", True, u"万円", True, named, named),
        inj_row(a, "T8-01", "T8_REL", u"万", False, u"万円", True, (TUNE.LABEL_PNF, P_, "no_element"), pass_, r=0.1),
        inj_row(a, "T8-02", "T8_REL", u"億+万", True, u"万円", True, named, other, r=-0.03),
        inj_row(a, "T8-03", "T8_REL", u"億+万", True, u"万円", False, None, named, r=0.03),
        inj_row(a, "T8-04", "T8_REL", u"万", True, u"万円", True, named, named, r=-0.1),
        inj_row(c, "T1-01", "T1_VALUE", u"万", True, u"万円", True, named, named),
    ]
    # 本 a: T1 作れる 3(状態 LINKED 2・NOT_G 1)・採った 2(LINKED 1・NOT_G 1)、T8 円族の新しい token 6(LINKED 3・UNLINKED 1・NOT_G 1・NO_BASE 1)・作れる 4・採った 4
    ca = collections.OrderedDict([
        (u"token の数え", stats_of(4, 2, 0, 6, 3, 9)),
        ("T1_VALUE", collections.OrderedDict(sorted({u"作れる site": 3, u"採った": 2, NS.LINKED: 1, NS.STATUS_NOT_G: 1}.items()))),
        (u"T1_VALUE の作れる site の状態", collections.OrderedDict(sorted({NS.LINKED: 2, NS.STATUS_NOT_G: 1}.items()))),
        ("T8_REL", collections.OrderedDict(sorted({u"円族の新しい token": 6, NS.LINKED: 3, NS.UNLINKED: 1, NS.STATUS_NOT_G: 1, NS.STATUS_NO_BASE: 1, u"作れる site": 4, u"採った": 4}.items())))])
    # 本 b: 文に全角の数字があり注入しない(行なし)
    cb = collections.OrderedDict([(u"token の数え", stats_of(0, 1, 0, 1, 2, 3)), (u"注入しない", u"文に全角の数字がある(select は半角の文を前提にする)")])
    # 本 c: T1 の作れる site 1・採った 1(行 1)、T8 は円族の新しい token なし
    cc = collections.OrderedDict([
        (u"token の数え", stats_of(0, 3, 0, 3, 1, 4)),
        ("T1_VALUE", collections.OrderedDict(sorted({u"作れる site": 1, u"採った": 1, NS.LINKED: 1}.items()))),
        (u"T1_VALUE の作れる site の状態", collections.OrderedDict(sorted({NS.LINKED: 1}.items()))),
        ("T8_REL", collections.OrderedDict(sorted({u"円族の新しい token": 0, u"作れる site": 0, u"採った": 0}.items())))])
    per = collections.OrderedDict([(u"DOC1_F1_m1", ca), (u"DOC2_F5_m2", cb), (u"DOC3_F1_m1", cc)])
    with Patch() as pt:
        pt.set(RUN, "PROFILES", INJECT_PROFILES)
        summ, summ_cmp = (norm(x) for x in NS.inject_summaries(rows))
    rec = sample_header("inject", u"標本")
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
    rec[u"型"] = collections.OrderedDict([(u"site", NEW_WORD_PIN), (u"土台", BASE_WORD_PIN)])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"], rec[NS.COMPARE_KEY] = summ, summ_cmp
    with Patch() as pt:
        pt.set(RUN, "PROFILES", INJECT_PROFILES)
        rec[NS.BREAKDOWN_KEY] = norm(NS.breakdown(rows))
    rec[u"P29E に対応なしの行の数"] = norm(NS.unlinked_counts(rows))
    rec[NS.H_KEY] = norm(NS.h_columns(per, rows))

    ex = collections.OrderedDict((t, collections.OrderedDict((p, collections.OrderedDict([(u"注入の行", 1)])) for p in INJECT_PROFILES)) for t in RUN.INJECT_TYPES)
    rec[NS.EXISTING_KEY], rec[NS.EXISTING_CMP_KEY] = ex, copy.deepcopy(ex)
    rec[u"限界"] = NS.seal_limits(read(SEAL_REL)) + list(NS.EXTRA_LIMITS)
    rec[u"行"] = rows
    return norm(rec)


def sample_records():
    return collections.OrderedDict([("offcheck", sample_offcheck()), ("inject", sample_inject())])


def sample_cols(**ov):
    u"""判定の関数の境界の試験用: ``h_columns`` と同じ形の欄(幅の真ん中の値)。ov = {名前: 値} で 1 つだけ替える。"""
    c = collections.OrderedDict([
        (u"H-2 新しい token", collections.OrderedDict([(u"億+万", 5470), (u"万", 1830), (u"兆+億", 6), (u"その他", 0), (u"計", 7300), (u"is_quantity 真", 7230)])),
        (u"H-3 円族の token(is_quantity 真)", collections.OrderedDict([(u"偽", 5211), (u"真", 12400)])),
        (u"H-4 T1_VALUE", collections.OrderedDict([(u"作れる site", 1450), (u"採った", 750), (u"うち P30E が GROUNDED", 540)])),
        (u"H-5 T8_REL", collections.OrderedDict([(u"作れる site", 4700), (u"採った", 1200), (u"P29E に対応が付く行", 1190)])),
        (u"H-6 T8_REL 基準に対応が付かない", collections.OrderedDict([(u"件", 680), (u"円族の新しい token", 7230), (u"率", 9.4), (u"P30E が GROUNDED でない", 1800)])),
        (u"H-7 通した率(P30E)", collections.OrderedDict([("T1_VALUE", 0.3), ("T8_REL", 0.2)])),
        (u"H-8 名指して原本の率(P30E)", collections.OrderedDict([("T1_VALUE", 86.0), ("T8_REL", 90.0)])),
        (u"H-9 P29E と P30E で判定が違う行(P29E に対応が付く行)", 1),
        (u"H-10", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"注入後の値(円)が refs に在る行", 1)]))])
    for path, v in ov.items():
        keys = path.split("/")
        d = c
        for kk in keys[:-1]:
            d = d[kk]
        d[keys[-1]] = v
    return c


def sample_off_agg(**ov):
    off = norm(sample_offcheck())
    off[u"集計"][u"H-1 一致した本"] = 200
    off[u"集計"][u"本"] = 200
    off[u"試験"] = norm(sample_tests())
    for k, v in ov.items():
        off[u"集計"][k] = v
    return off


def sample_doc(R, seal):
    J = NS.build_J(R, seal)
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", NS.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start judge -->", NS.render_judge(J, seal), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"200 本の標本です。" + NOT_GATED, u""])


# ================================================================ (a) 封の字
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def test_a_2_a_changed_character_in_the_seal_turns_the_pin_red(self):
        rows = NS.seal_pred_rows(self.seal)
        for cid, old, new in (("H-1", "200 / 200", "200 / 199"), ("H-2", "7,250〜7,350", "7,251〜7,350"), ("H-2", "5,400〜5,550", "5,400〜5,551"), ("H-2", "1,780〜1,880", "1,780〜1,881"),
                              ("H-2", "兆+億 4〜8", "兆+億 4〜9"), ("H-2", "is_quantity 真 7,150〜7,300", "is_quantity 真 7,150〜7,301"), ("H-3", "12,200〜12,600", "12,200〜12,601"),
                              ("H-4", "1,350〜1,550", "1,350〜1,551"), ("H-4", "700〜800", "700〜801"), ("H-4", "480〜600", "480〜601"),
                              ("H-5", "4,500〜4,900", "4,500〜4,901"), ("H-5", "1,150〜1,280", "1,150〜1,281"), ("H-5", "1,130〜1,250", "1,130〜1,251"),
                              ("H-6", "7〜12%", "7〜13%"), ("H-7", "T1_VALUE 0.0〜0.6%", "T1_VALUE 0.0〜0.7%"), ("H-7", "T8_REL 0.0〜0.5%", "T8_REL 0.0〜0.6%"),
                              ("H-8", "T1 82〜90%", "T1 82〜91%"), ("H-8", "T8 86〜93%", "T8 86〜94%"), ("H-9", "0〜5", "0〜6"), ("H-10", "0 / 0 / 0〜3", "0 / 0 / 0〜4"),
                              ("H-10", "0 / 0 / 0〜3", "1 / 0 / 0〜3"), ("H-10", "0 / 0 / 0〜3", "0 / 1 / 0〜3")):
            self.assertIn(old, rows[cid][1], (cid, old))
            mutated = self.seal.replace("| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1]), "| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1].replace(old, new, 1)), 1)
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], bounds_problems(mutated), (cid, new))

    def test_a_3_the_thresholds_of_k1_to_k4_are_read_from_the_seal(self):
        b = NS.seal_bounds(self.seal)
        self.assertEqual(((200, 200), {u"round-trip 不一致": 0, u"読み直し不一致": 0}, 1500.0, BOUNDS_PIN["K-4"]), (b["K-1"], dict(b["K-2"]), b["K-3"], b["K-4"]))
        for old, new in (("H-1 が 200 / 200", "H-1 が 200 / 199"), ("H-10 の round-trip 不一致 0・読み直し不一致 0。", "H-10 の round-trip 不一致 1・読み直し不一致 0。"), ("H-10 の round-trip 不一致 0・読み直し不一致 0。", "H-10 の round-trip 不一致 0・読み直し不一致 1。"), ("和 ≥ 1,500", "和 ≥ 1,501"),
                         ("描きのコンマ", "描きのコンマx"), ("複合の value の指数)で赤", "複合の value の指数・別の変異)で赤"), ("切り替えを外す・", "")):
            self.assertIn(old, self.seal, old)
            self.assertNotEqual([], bounds_problems(self.seal.replace(old, new, 1)), new)

    def test_a_4_the_pinned_k4_names_are_the_script_mutations(self):
        self.assertEqual(list(NS.MUTATIONS), BOUNDS_PIN["K-4"])


# ================================================================ (c) 判定
class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def J(self, off=None, **ov):
        return NS.judge_from(off or sample_off_agg(), sample_cols(**ov), self.seal)

    def test_c_1_the_middle_of_every_range_is_a_hit_and_adoption_follows(self):
        J = self.J()
        for k, v in J[u"H"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        for k, v in J[u"K"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        self.assertTrue(J[u"採用"])

    def test_c_2_each_prediction_flips_at_the_seal_boundary(self):
        b = BOUNDS_PIN
        cases = []
        for k, (lo, hi) in b["H-2"].items():
            cases += [(u"H-2 新しい token/" + k, "H-2", lo, lo - 1), (u"H-2 新しい token/" + k, "H-2", hi, hi + 1)]
        cases += [(u"H-3 円族の token(is_quantity 真)/真", "H-3", b["H-3"][0], b["H-3"][0] - 1), (u"H-3 円族の token(is_quantity 真)/真", "H-3", b["H-3"][1], b["H-3"][1] + 1)]
        for k, (lo, hi) in b["H-4"].items():
            cases += [(u"H-4 T1_VALUE/" + k, "H-4", lo, lo - 1), (u"H-4 T1_VALUE/" + k, "H-4", hi, hi + 1)]
        for k, (lo, hi) in b["H-5"].items():
            cases += [(u"H-5 T8_REL/" + k, "H-5", lo, lo - 1), (u"H-5 T8_REL/" + k, "H-5", hi, hi + 1)]
        cases += [(u"H-6 T8_REL 基準に対応が付かない/率", "H-6", b["H-6"][0], b["H-6"][0] - 0.1), (u"H-6 T8_REL 基準に対応が付かない/率", "H-6", b["H-6"][1], b["H-6"][1] + 0.1)]
        for t in ("T1_VALUE", "T8_REL"):
            lo, hi = b["H-7"][t]
            cases += [(u"H-7 通した率(P30E)/" + t, "H-7", hi, hi + 0.1)]
            lo, hi = b["H-8"][t]
            cases += [(u"H-8 名指して原本の率(P30E)/" + t, "H-8", lo, lo - 0.1), (u"H-8 名指して原本の率(P30E)/" + t, "H-8", hi, hi + 0.1)]
        cases += [(u"H-9 P29E と P30E で判定が違う行(P29E に対応が付く行)", "H-9", b["H-9"][1], b["H-9"][1] + 1),
                  (u"H-10/round-trip 不一致", "H-10", 0, 1), (u"H-10/読み直し不一致", "H-10", 0, 1),
                  (u"H-10/注入後の値(円)が refs に在る行", "H-10", b["H-10"][u"注入後の値(円)が refs に在る行"][1], b["H-10"][u"注入後の値(円)が refs に在る行"][1] + 1)]
        for path, cid, inside, outside in cases:
            self.assertEqual(HIT, self.J(**{path: inside})[u"H"][cid][u"判定"], (path, inside))
            self.assertEqual(MISS, self.J(**{path: outside})[u"H"][cid][u"判定"], (path, outside))

    def test_c_2b_h1_needs_every_book_to_agree(self):
        for ov in ({u"H-1 一致した本": 199}, {u"本": 199}, {u"H-1 一致した本": 200, u"本": 201}):
            J = NS.judge_from(sample_off_agg(**ov), sample_cols(), self.seal)
            self.assertEqual(MISS, J[u"H"]["H-1"][u"判定"], ov)
            self.assertEqual(MISS, J[u"K"]["K-1"][u"判定"], ov)
            self.assertFalse(J[u"採用"])

    def test_c_3_the_adoption_follows_k1_to_k4(self):
        self.assertFalse(NS.judge_from(sample_off_agg(**{u"H-1 一致した本": 199}), sample_cols(), self.seal)[u"採用"])                    # K-1
        J = self.J(**{u"H-10/round-trip 不一致": 1})                                                                                      # K-2
        self.assertEqual(MISS, J[u"K"]["K-2"][u"判定"])
        self.assertFalse(J[u"採用"])
        J = self.J(**{u"H-10/読み直し不一致": 1})
        self.assertEqual(MISS, J[u"K"]["K-2"][u"判定"])
        self.assertFalse(J[u"採用"])
        J = self.J(**{u"H-4 T1_VALUE/採った": 700, u"H-5 T8_REL/採った": 800})                                                           # K-3: 和 = 1,500 は当たり
        self.assertEqual(HIT, J[u"K"]["K-3"][u"判定"])
        J = self.J(**{u"H-4 T1_VALUE/採った": 700, u"H-5 T8_REL/採った": 799})
        self.assertEqual(MISS, J[u"K"]["K-3"][u"判定"])
        self.assertFalse(J[u"採用"])
        # K-4: 変異が 1 つ赤にならない・戻っていない・既存の試験が赤・足した試験が赤・変異の名前が封の字と違う
        for mutate in (lambda t: t[u"変異"][0].__setitem__(u"赤", 0), lambda t: t[u"変異"][1].__setitem__(u"戻した", False), lambda t: t[u"既存の試験(偽のまま)"].__setitem__(u"失敗", 1),
                       lambda t: t[u"足した試験"].__setitem__(u"エラー", 1), lambda t: t[u"変異"].pop(), lambda t: t[u"変異"][2].__setitem__(u"名前", u"描きのコンマx"),
                       lambda t: t.__setitem__(u"変異のあと lib が元に戻った", False), lambda t: t[u"既存の試験(偽のまま)"].__setitem__(u"試験", 0)):
            off = sample_off_agg()
            mutate(off[u"試験"])
            J = NS.judge_from(off, sample_cols(), self.seal)
            self.assertEqual(MISS, J[u"K"]["K-4"][u"判定"])
            self.assertFalse(J[u"採用"])
        off = sample_off_agg()
        del off[u"試験"]
        self.assertEqual(MISS, NS.judge_from(off, sample_cols(), self.seal)[u"K"]["K-4"][u"判定"])

    def test_c_4_k3_uses_the_seal_k_threshold_not_the_prediction_ranges(self):
        J = self.J(**{u"H-4 T1_VALUE/採った": 650})                                  # H-4 の幅(700〜800)の外。K-3 は和 ≥ 1,500 だけを見る
        self.assertEqual(MISS, J[u"H"]["H-4"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-3"][u"判定"])
        J = self.J(**{u"H-7 通した率(P30E)/T8_REL": 0.9})                           # H-7 の外でも K は H-7 を見ない(採用は K だけで決まる)
        self.assertEqual(MISS, J[u"H"]["H-7"][u"判定"])
        self.assertTrue(J[u"採用"])

    def test_c_5_the_judgment_moves_with_the_records(self):
        base = self.J()
        mutated_seal = self.seal.replace("7,250〜7,350", "7,250〜7,299", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertEqual(MISS, NS.judge_from(sample_off_agg(), sample_cols(), mutated_seal)[u"H"]["H-2"][u"判定"])
        self.assertNotEqual(norm(base), norm(self.J(**{u"H-9 P29E と P30E で判定が違う行(P29E に対応が付く行)": 4})))

    def test_c_6_a_broken_record_is_red_not_an_exception(self):
        R = norm(sample_records())
        self.assertEqual([], judge_problems(R, self.seal))
        del R["inject"][u"本ごとの数え"]
        self.assertNotEqual([], judge_problems(R, self.seal))
        R2 = norm(sample_records())
        R2["offcheck"].pop(u"集計")
        self.assertNotEqual([], judge_problems(R2, self.seal))

    def test_c_8_each_h10_column_and_the_dropped_leading_group_count_are_counted_from_the_rows(self):
        u"""読み直し不一致・注入後の値(円)が refs に在る行・先頭の位が減った行 を、行の欄 1 つずつから数える(列を 0 に固定すると赤)。"""
        R = norm(sample_records())
        per, rows = R["inject"][u"本ごとの数え"], R["inject"][u"行"]
        base = NS.h_columns(per, rows)
        self.assertEqual((0, 0, 0, 0), (base[u"H-10"][u"round-trip 不一致"], base[u"H-10"][u"読み直し不一致"], base[u"H-10"][u"注入後の値(円)が refs に在る行"], base[u"先頭の位が減った行"]))
        for key, path, want in ((u"読み直し", (u"H-10", u"読み直し不一致"), 1), (u"注入後の値(円)が refs に在る", (u"H-10", u"注入後の値(円)が refs に在る行"), 1),
                                (u"先頭の位が減った", (u"先頭の位が減った行",), 1), (u"round-trip", (u"H-10", u"round-trip 不一致"), 1)):
            r2 = copy.deepcopy(rows)
            r2[0][key] = (key not in (u"読み直し", u"round-trip"))
            r3 = copy.deepcopy(r2)
            r3[1][key] = r2[0][key]                                                       # 2 行目にも同じ値を入れると 2 になる(行ごとに数えている)
            for rr, n in ((r2, 1), (r3, 2)):
                cols = NS.h_columns(per, rr)
                v = cols
                for k in path:
                    v = v[k]
                self.assertEqual(n, v, (key, n))
        r2 = copy.deepcopy(rows)
        r2[0][u"読み直し"] = False
        J = NS.judge_from(sample_off_agg(), NS.h_columns(per, r2), read(SEAL_REL))
        self.assertEqual(MISS, J[u"K"]["K-2"][u"判定"])
        self.assertEqual(MISS, J[u"H"]["H-10"][u"判定"])
        r2 = copy.deepcopy(rows)
        r2[0][u"注入後の値(円)が refs に在る"] = True
        r2[1][u"注入後の値(円)が refs に在る"] = True
        r2[2][u"注入後の値(円)が refs に在る"] = True
        r2[3][u"注入後の値(円)が refs に在る"] = True
        self.assertEqual(4, NS.h_columns(per, r2)[u"H-10"][u"注入後の値(円)が refs に在る行"])
        self.assertEqual(MISS, NS.judge_from(sample_off_agg(), NS.h_columns(per, r2), read(SEAL_REL))[u"H"]["H-10"][u"判定"])      # 幅 0〜3 の外

    def test_c_7_the_columns_are_counted_from_the_counts_and_rows_not_copied_from_the_record(self):
        R = norm(sample_records())
        J = NS.build_J(R, self.seal)
        R["inject"][NS.H_KEY][u"H-10"][u"round-trip 不一致"] = 7                          # 記録の H の欄だけ変えても判定は動かない(行から数え直す)
        self.assertEqual(norm(J), norm(NS.build_J(R, self.seal)))
        R["inject"][u"行"][0][u"round-trip"] = False                                       # 行を変えると H-10 が動く
        self.assertEqual(MISS, NS.build_J(R, self.seal)[u"H"]["H-10"][u"判定"])
        self.assertEqual(MISS, NS.build_J(R, self.seal)[u"K"]["K-2"][u"判定"])


# ================================================================ (g) 小さい標本の記録 2 つと文書の変異
class SampleFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.R = sample_records()

    def test_g_0_the_sample_is_green(self):
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=False))
        doc = sample_doc(self.R, self.seal)
        self.assertEqual([], doc_problems(doc, self.R, self.seal))

    def test_g_1_the_sample_exercises_a_skipped_book_unlinked_rows_and_the_other_judgement(self):
        inj = self.R["inject"]
        self.assertIn(u"注入しない", inj[u"本ごとの数え"][u"DOC2_F5_m2"])
        self.assertEqual({u"全体": 1, "T1_VALUE": 0, "T8_REL": 1}, dict(inj[u"P29E に対応なしの行の数"]))
        cols = inj[NS.H_KEY]
        self.assertEqual(2, cols[u"H-9 P29E と P30E で判定が違う行(P29E に対応が付く行)"])                       # T8-01(止めた対 通した)と T8-02(名指して原本 対 別の値)。同じ判定の 3 行(T1 の 2 行と T8-04)と対応なしの T8-03 は数えない
        self.assertEqual({u"round-trip 不一致": 0, u"読み直し不一致": 0, u"注入後の値(円)が refs に在る行": 0}, dict(cols[u"H-10"]))

    def _red(self, mutate, **kw):
        R = copy.deepcopy(self.R)
        mutate(R)
        self.assertNotEqual([], record_problems(R, full=False), kw)

    def test_g_2_one_number_in_a_record_turns_it_red(self):
        self._red(lambda R: R["offcheck"][u"本"][0].__setitem__(u"一致", False))
        self._red(lambda R: R["offcheck"][u"本"][0].__setitem__(u"RB の記録の行と一致", False))
        self._red(lambda R: R["offcheck"][u"本"][0].__setitem__(u"lib が封の commit と一致", False))
        self._red(lambda R: R["offcheck"][u"本"][0].__setitem__(u"token の sha256", "0" * 64))
        self._red(lambda R: R["offcheck"][u"本"][0].__setitem__(u"token の sha256", u"x"))
        self._red(lambda R: R["offcheck"][u"本"][0].__setitem__(u"groups を持つ token", 1))
        self._red(lambda R: R["offcheck"][u"本"][0].__setitem__(u"行の数", 3))
        self._red(lambda R: R["offcheck"][u"集計"].__setitem__(u"H-1 一致した本", 9))
        self._red(lambda R: R["offcheck"][u"集計"][u"行の数"].__setitem__(u"今回", 9))
        self._red(lambda R: R["offcheck"][u"試験"][u"変異"][0].__setitem__(u"赤", 0))
        self._red(lambda R: R["offcheck"][u"試験"][u"変異"].pop())
        self._red(lambda R: R["offcheck"][u"試験"][u"足した試験"].__setitem__(u"失敗", 1))
        self._red(lambda R: R["offcheck"][u"試験"][u"既存の試験(偽のまま)"].__setitem__(u"path", u"measure/tests/test_x.py"))
        self._red(lambda R: R["offcheck"][u"試験"][u"変異"][0].__setitem__(u"試験", 22))
        self._red(lambda R: R["offcheck"].__setitem__(u"試験", None))
        self._red(lambda R: R["inject"][u"行"][0]["P30E"].__setitem__(u"結果", TUNE.LABEL_PASS))
        self._red(lambda R: R["inject"][u"行"][0].__setitem__(u"round-trip", u"はい"))
        self._red(lambda R: R["inject"][u"行"][0].__setitem__(u"単位", u"円"))
        self._red(lambda R: R["inject"][u"行"][0].__setitem__(u"形", u""))
        self._red(lambda R: R["inject"][u"集計"]["T1_VALUE"]["P30E"][u"全体"].__setitem__(u"注入の行", 9))
        self._red(lambda R: R["inject"][u"行"][1].__setitem__("r", 0.2))
        self._red(lambda R: R["inject"][u"型"].__setitem__(u"土台", u"無改変の文で P29E が GROUNDED の claim"))
        self._red(lambda R: R["inject"][u"型"].__setitem__(u"site", u"全部の site"))
        self._red(lambda R: R["inject"][NS.H_KEY][u"H-10"].__setitem__(u"読み直し不一致", 2))
        self._red(lambda R: R["inject"][NS.BREAKDOWN_KEY]["T8_REL"][u"形別"][u"万"].__setitem__(u"注入の行", 9))
        self._red(lambda R: R["inject"][u"限界"].pop())
        self._red(lambda R: R["inject"][u"限界"].__setitem__(0, u"別の限界"))
        self._red(lambda R: R["inject"].pop(NS.EXISTING_KEY))
        self._red(lambda R: R["inject"][NS.EXISTING_KEY].pop("T8_REL"))

    def test_g_2b_a_consistently_edited_count_still_breaks_the_invariants(self):
        u"""本ごとの数えを直してから H の欄も作り直しても(欄との食い違いでは見つからない)、数えの欄の間の関係と行との関係で赤になる。"""
        def reh(R):
            R["inject"][NS.H_KEY] = norm(NS.h_columns(R["inject"][u"本ごとの数え"], R["inject"][u"行"]))
        for mutate in (lambda c: c["T1_VALUE"].__setitem__(u"採った", 5), lambda c: c["T1_VALUE"].__setitem__(u"作れる site", 1),
                       lambda c: c[u"T1_VALUE の作れる site の状態"].__setitem__(NS.LINKED, 9), lambda c: c["T8_REL"].__setitem__(u"採った", 2),
                       lambda c: c["T8_REL"].__setitem__(u"作れる site", 9), lambda c: c["T8_REL"].__setitem__(u"円族の新しい token", 99),
                       lambda c: c["T8_REL"].__setitem__(NS.NO_PICK, 1), lambda c: c[u"token の数え"][u"新しい token"].__setitem__(u"計", 99),
                       lambda c: c[u"token の数え"][u"新しい token"].__setitem__(u"is_quantity 真", 99),
                       lambda c: c[u"token の数え"][u"覆われた既存の token"].__setitem__(u"うち is_quantity 真", 99),
                       lambda c: c[u"token の数え"][u"円族の token(is_quantity 真)"].__setitem__(u"真", 0)):
            R = copy.deepcopy(self.R)
            mutate(R["inject"][u"本ごとの数え"][u"DOC1_F1_m1"])
            try:
                reh(R)
            except Exception:                                   # noqa: BLE001  H の欄を作れない形も赤(record_problems が例外を問題に数える)
                pass
            self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        R["inject"][u"本ごとの数え"][u"DOC2_F5_m2"].pop(u"注入しない")                               # 注入しない本に数えを置かずに印だけ消した
        self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        reh(R)
        self.assertEqual([], record_problems(R, full=False))

    def test_g_2e_inject_base_fields_are_checked(self):
        for mutate in (lambda r: r[u"行"][0].__setitem__(NS.LINK_KEY, False),                                       # 対応ありの行を対応なしに(P29E の欄が対応なしでない)
                       lambda r: r[u"行"][3].__setitem__(NS.LINK_KEY, True) or r.__setitem__(u"注入の行の数", len(r[u"行"])),
                       lambda r: r[u"行"][3].__setitem__(NS.LINK_KEY, u"いいえ"),
                       lambda r: r[NS.COMPARE_KEY]["T8_REL"]["P29E"][u"全体"].__setitem__(u"注入の行", 9),
                       lambda r: r.pop(NS.COMPARE_KEY),
                       lambda r: r[u"行"][3]["P29E"].__setitem__(u"結果", TUNE.LABEL_PASS),
                       lambda r: r[u"P29E に対応なしの行の数"].__setitem__(u"全体", 0),
                       lambda r: r[u"P29E に対応なしの行の数"].__setitem__("T1_VALUE", 1),
                       lambda r: r.pop(u"P29E に対応なしの行の数"),
                       lambda r: r.pop(u"限界")):
            R = copy.deepcopy(self.R)
            mutate(R["inject"])
            self.assertNotEqual([], record_problems(R, full=False))

    def test_g_2c_inject_cap_is_checked_on_its_own(self):
        R = copy.deepcopy(self.R)
        row = R["inject"][u"行"][0]
        R["inject"][u"行"] = [dict(row, id=u"x-%d" % i) for i in range(RUN.INJECT_CAP + 1)]
        R["inject"][u"注入の行の数"] = len(R["inject"][u"行"])
        with Patch() as pt:
            pt.set(RUN, "PROFILES", INJECT_PROFILES)
            R["inject"][u"集計"], R["inject"][NS.COMPARE_KEY] = (norm(x) for x in NS.inject_summaries(R["inject"][u"行"]))
        R["inject"][u"P29E に対応なしの行の数"] = collections.OrderedDict([(u"全体", 0), ("T1_VALUE", 0), ("T8_REL", 0)])
        self.assertTrue(any(u"上限" in x for x in inject_problems(R["inject"], full=False)), inject_problems(R["inject"], full=False))

    def test_g_2g_the_full_only_checks_are_exercised_on_the_sample(self):
        u"""full=True だけが見る検査(本番の記録でだけ走る)を、標本の記録で 1 つずつ。他の full の検査(本の並び・200 本)は標本では赤のままなので、その検査の問題の字だけを見る。"""
        R = copy.deepcopy(self.R)
        self.assertTrue(any(u"既存の site の率が RB の記録そのままでない" in x for x in inject_problems(R["inject"], full=True)))            # 標本の率は RB の記録と違う
        rb = NS.load_rb(ROOT)
        a, b = (norm(x) for x in NS.existing_rates(rb))
        R["inject"][NS.EXISTING_KEY], R["inject"][NS.EXISTING_CMP_KEY] = a, b
        self.assertFalse(any(u"既存の site の率が RB の記録そのままでない" in x for x in inject_problems(R["inject"], full=True)))
        R["inject"][NS.EXISTING_KEY]["T8_REL"]["P30E"][u"注入の行"] += 1
        self.assertTrue(any(u"既存の site の率が RB の記録そのままでない" in x for x in inject_problems(R["inject"], full=True)))
        self.assertTrue(any(u"200 本" in x for x in inject_problems(R["inject"], full=True)))                                             # 標本は 200 本でない
        o = copy.deepcopy(self.R["offcheck"])
        self.assertTrue(any(u"200 本" in x for x in offcheck_problems(o, full=True)))
        # 試験 file の sha256 と本数(現物)
        o[u"試験"][u"足した試験"][u"sha256"] = sha256_rel(NS.TEST_YEN_REL)
        spec = importlib.util.spec_from_file_location("count_for_nscan_gate2", os.path.join(ROOT, NS.TEST_YEN_REL))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        o[u"試験"][u"足した試験"][u"試験"] = unittest.defaultTestLoader.loadTestsFromModule(mod).countTestCases()
        self.assertFalse(any(NS.TEST_YEN_REL in x for x in k4_record_problems(o[u"試験"], BOUNDS_PIN["K-4"], True)))
        o[u"試験"][u"足した試験"][u"sha256"] = "0" * 64
        self.assertTrue(any(u"sha256 が現物と違う" in x for x in k4_record_problems(o[u"試験"], BOUNDS_PIN["K-4"], True)))
        o[u"試験"][u"足した試験"][u"sha256"] = sha256_rel(NS.TEST_YEN_REL)
        o[u"試験"][u"足した試験"][u"試験"] += 1
        self.assertTrue(any(u"試験の本数が現物と違う" in x for x in k4_record_problems(o[u"試験"], BOUNDS_PIN["K-4"], True)))

    def test_g_3_a_forbidden_key_or_a_key_or_a_company_name_turns_it_red(self):
        for key in (u"span", u"value", u"recomputed", u"文", u"sentence", u"数", u"理由"):
            self._red(lambda R, key=key: R["offcheck"][u"本"][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["inject"][u"行"][0].__setitem__(key, 1))
        self._red(lambda R: R["inject"].__setitem__(u"メモ", u"株式会社テスト"))
        self._red(lambda R: R["offcheck"].__setitem__(u"メモ", u"sk-" + u"a" * 20))
        self._red(lambda R: R["inject"].__setitem__(u"key_leaks", [u"鍵の形"]))

    def test_g_4_one_character_of_the_fingerprints_or_the_script_sha_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][u"engine の指紋"].__setitem__("adapter_xbrl_py_sha256", R[k][u"engine の指紋"]["adapter_xbrl_py_sha256"][:-1] + ("0" if R[k][u"engine の指紋"]["adapter_xbrl_py_sha256"][-1] != "0" else "1")))
            self._red(lambda R, k=k: R[k][u"engine の指紋"].__setitem__("core_py_sha256", "f" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"この script の sha256", "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"封の commit", u"0000000"))
            self._red(lambda R, k=k: R[k][u"lib の指紋"].__setitem__(NS.LIB_RELS[0], "e" * 64))
            self._red(lambda R, k=k: R[k][u"lib の指紋"].__setitem__(NS.LIB_RELS[1], "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"封の commit の numbers.py の sha256", "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"rmix script の sha256", "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"numfix script の sha256", "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"RB の記録の sha256", "e" * 64))
            self._red(lambda R, k=k: R[k][u"生成の記録の sha256"].__setitem__("aiforms", "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"profile", [u"P28E", u"P29E"]))

    def test_g_4b_the_switch_record_turns_red_when_the_wiring_or_the_values_are_wrong(self):
        self._red(lambda R: R["offcheck"][u"切り替え"].__setitem__(u"この記録を作ったときの値", True))
        self._red(lambda R: R["offcheck"][u"切り替え"].__setitem__(u"配線の問題", [u"N がちがう"]))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"inject の中の値", False))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"出たあとの値", True))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"名前", WRONG_FLAG))

    def test_g_5_a_changed_cache_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][u"cache の前後"].__setitem__(u"変化なし", False))
            self._red(lambda R, k=k: R[k][u"cache の前後"][u"後"]["edinet"].__setitem__(u"件数", 4))

    def test_g_6_the_document_follows_the_records_and_the_seal(self):
        doc = sample_doc(self.R, self.seal)
        lines = doc.split(u"\n")
        i = lines.index(u"<!-- 門:start pred -->") + 3                  # 表の 1 行目(H-1)
        for col_char in (u"2", u"0", u"外"):
            mutated = lines[:]
            self.assertIn(col_char, mutated[i])
            j = mutated[i].index(col_char)
            mutated[i] = mutated[i][:j] + (u"9" if col_char != u"外" else u"当") + mutated[i][j + 1:]
            self.assertNotEqual([], doc_problems(u"\n".join(mutated), self.R, self.seal), col_char)
        k = lines.index(u"<!-- 門:start judge -->") + 3
        mutated = lines[:]
        mutated[k] = mutated[k].replace(u"K-1", u"K-9", 1)
        self.assertNotEqual([], doc_problems(u"\n".join(mutated), self.R, self.seal))
        R2 = copy.deepcopy(self.R)
        R2["inject"][u"行"][0][u"round-trip"] = False
        self.assertNotEqual([], doc_problems(doc, R2, self.seal))
        mutated_seal = self.seal.replace("7,250〜7,350", "7,250〜7,351", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertNotEqual([], doc_problems(doc, self.R, mutated_seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"門:start judge", u"門:start other"), self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"<!-- 門:start judge -->", u"<!-- 門:start judge2 -->", 1), self.R, self.seal))

    def test_g_7_forbidden_words_docids_and_ungated_numbers_turn_the_document_red(self):
        doc = sample_doc(self.R, self.seal)
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(doc + u"\n" + w + u"。\n", self.R, self.seal), w)
        self.assertNotEqual([], doc_problems(doc + u"\nS100" + u"ABCD の文。\n", self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n新しい token は 1234 でした。\n", self.R, self.seal))
        self.assertEqual([], doc_problems(doc + u"\n新しい token は 1234 でした。" + NOT_GATED + u"\n", self.R, self.seal))

    def test_g_8_the_aggregation_functions_give_known_answers(self):
        agg = NS.offcheck_aggregate(self.R["offcheck"][u"本"])
        self.assertEqual({u"本": 2, u"H-1 一致した本": 2, u"封の commit の lib と一致した本": 2, u"RB の記録の行と一致した本": 2, u"RB の記録の数えと一致した本": 2, u"token の数": 100, u"groups を持つ token": 0,
                          u"行の数": {u"今回": 8, u"RB の記録": 8}}, norm(agg))
        cols = NS.h_columns(self.R["inject"][u"本ごとの数え"], self.R["inject"][u"行"])
        self.assertEqual({u"億+万": 4, u"万": 6, u"兆+億": 0, u"その他": 0, u"計": 10, u"is_quantity 真": 10}, norm(cols[u"H-2 新しい token"]))
        self.assertEqual({u"偽": 6, u"真": 16}, norm(cols[u"H-3 円族の token(is_quantity 真)"]))
        self.assertEqual({u"作れる site": 4, u"採った": 3, u"うち P30E が GROUNDED": 2}, norm(cols[u"H-4 T1_VALUE"]))
        self.assertEqual({u"作れる site": 4, u"採った": 4, u"P29E に対応が付く行": 3}, norm(cols[u"H-5 T8_REL"]))
        self.assertEqual({u"件": 1, u"円族の新しい token": 6, u"率": 16.7, u"P30E が GROUNDED でない": 1}, norm(cols[u"H-6 T8_REL 基準に対応が付かない"]))
        self.assertEqual({"T1_VALUE": 0.0, "T8_REL": 25.0}, norm(cols[u"H-7 通した率(P30E)"]))                                         # P30E の通した: T1 は 0 / 2、T8 は 1 / 4
        self.assertEqual(2, cols[u"H-9 P29E と P30E で判定が違う行(P29E に対応が付く行)"])
        self.assertEqual(0, cols[u"先頭の位が減った行"])


WRONG_FLAG = "compound_yen_2026_11_05"


# ================================================================ 配線・注入の手順(script の関数を小さい入力で通す。engine・zip・文は偽。通信なし)
class WiringAndInjectTest(unittest.TestCase):
    def test_w_1_the_wiring_check_covers_the_script_and_a_broken_swap_is_red(self):
        self.assertEqual([], NS.wiring_problems())
        with Patch() as pt:
            pt.set(NS.RUN, "N", types.SimpleNamespace(__file__=N.__file__))
            self.assertNotEqual([], NS.wiring_problems())
        with Patch() as pt:
            pt.set(NS.GEN, "key_leaks", NS.NF.ORIG_KEY_LEAKS)
            self.assertNotEqual([], NS.wiring_problems())
        self.assertEqual([], NS.wiring_problems())
        self.assertFalse(getattr(N, FLAG))

    def test_w_2_the_inject_wiring_needs_the_rmix_swap(self):
        with Patch() as pt:
            pt.set(NS.RUN, "PROFILES", INJECT_PROFILES)
            pt.set(NS.RUN, "base_status4", NS.RM.base_status_rb)
            self.assertEqual([], NS.inject_wiring_problems())
            pt.set(NS.RUN, "PROFILES", ("P28E", "P29E"))
            self.assertTrue(any(u"RUN.PROFILES" in x for x in NS.inject_wiring_problems()))
            pt.undo()
            pt.set(NS.RUN, "PROFILES", INJECT_PROFILES)
            pt.set(NS.RUN, "base_status4", lambda *a: None)
            self.assertTrue(any(u"base_status4" in x for x in NS.inject_wiring_problems()))

    def test_w_3_run_inject_leaves_the_switch_off_and_refuses_when_it_cannot_turn_it_on(self):
        u"""run_inject の記録の組み立てと切り替えの出入りを、読み込み・並列・cache を偽にして 1 回通す。"""
        base = sample_inject()
        rows = norm(base[u"行"])
        item = {u"docID": "DOC1", u"form": "F1", u"model": "m1", u"writer": "W1", u"sha256": "0" * 64}
        seen = []
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(NS, "load_books", lambda root=ROOT, only=None: [("aiforms", "DOC1_F1_m1", item, {}, {})])

            def pool(fn, jobs_, procs):
                seen.append(getattr(N, FLAG))
                return [("DOC1_F1_m1", [collections.OrderedDict(r) for r in rows if r["docID"] == "DOC1"], norm(base[u"本ごとの数え"][u"DOC1_F1_m1"]))]
            pt.set(NF, "map_pool", pool)
            pt.set(NS, "caches_all", lambda: collections.OrderedDict())
            pt.set(GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
            pt.set(NS, "orig_sha256", lambda: "0" * 64)
            pt.set(NS, "header_h", lambda root, step, seed_meta, before, after, profiles: collections.OrderedDict([(u"seal", SEAL_REL), (u"profile", list(profiles))]))
            out = os.path.join(d, "inject.json")
            rec = NS.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with open(out, encoding="utf-8") as fh:
                disk = json.load(fh)
        self.assertEqual([True], seen)                                    # map_pool の呼ばれた間は真
        self.assertFalse(getattr(N, FLAG))                                # 出たら偽
        self.assertEqual(norm(rec), disk)
        self.assertEqual(BASE_WORD_PIN, disk[u"型"][u"土台"])
        self.assertEqual(NEW_WORD_PIN, disk[u"型"][u"site"])
        self.assertEqual(NS.seal_limits(read(SEAL_REL)) + list(NS.EXTRA_LIMITS), disk[u"限界"])
        self.assertIn(u"K-2", disk[u"限界"][5])
        self.assertIn(u"失敗とエラーを分けない", disk[u"限界"][6])
        self.assertEqual({u"全体": 1, "T1_VALUE": 0, "T8_REL": 1}, disk[u"P29E に対応なしの行の数"])
        self.assertEqual([], [x for x in inject_problems(dict(base, **{u"限界": disk[u"限界"]}), False) if u"限界" in x])
        self.assertEqual([u"P29E", u"P30E"], disk[u"profile"])
        self.assertEqual({u"名前": FLAG, u"inject の中の値": True, u"出たあとの値": False, u"配線の問題": []}, disk[u"切り替え"])

    def test_w_4_run_offcheck_refuses_a_switch_that_is_on_before_it_reads_anything(self):
        def reached(root=ROOT, only=None):
            raise RuntimeError(u"材料を読みに行った")
        N.__dict__[FLAG] = True
        try:
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
                pt.set(NS, "load_books", reached)                      # 検査が材料を読む前に止めるなら、ここへは来ない
                with self.assertRaises(NS.Stop):
                    NS.run_offcheck(root=ROOT, out=os.path.join(d, "o.json"), say=lambda *a: None)
        finally:
            N.__dict__[FLAG] = False
        self.assertFalse(getattr(N, FLAG))

    def test_w_5_the_inject_job_refuses_a_switch_that_is_off_and_the_offcheck_job_one_that_is_on(self):
        with self.assertRaises(NS.Stop):
            NS.inject_job_h(("aiforms", "n", {}, {}, "d", {}, "s", "w"))
        N.__dict__[FLAG] = True
        try:
            with self.assertRaises(NS.Stop):
                NS.offcheck_job(("aiforms", "n", {}, {}, "d", {}, "s", "w", {}))
        finally:
            N.__dict__[FLAG] = False

    def test_w_6_token_stats_counts_the_new_tokens_by_shape_and_what_they_cover(self):
        text = u"売上高は12億3,456万円で、利益は1,234万円、負債は5兆1,234億円、資本は10億円でした。"
        with NS.yen_scan_on():
            st = NS.token_stats(text)
        self.assertEqual({u"億+万": 1, u"万": 1, u"兆+億": 1, u"その他": 0, u"計": 3, u"is_quantity 真": 3}, norm(st[u"新しい token"]))
        self.assertEqual(1, st[u"覆われた既存の token"][u"同じ span の置き換え"])                       # 1,234万円 は同じ span の置き換え
        self.assertEqual(4, st[u"覆われた既存の token"][u"捨てた"])                                    # 12・3,456(12億3,456万円の部品)と 5・1,234(5兆1,234億円の部品)
        self.assertEqual(0, st[u"覆われた既存の token"][u"うち is_quantity 真"])                       # 部品は is_quantity 偽(位の記号の後ろに数字が続く)
        self.assertEqual(1, st[u"覆われた既存の token"][u"うち単位が付いていた"])                         # 5兆1,234億円 の 1,234 は 億円 の単位を持っていた
        self.assertEqual({u"偽": 1, u"真": 4}, norm(st[u"円族の token(is_quantity 真)"]))                # 偽: 10億円 だけ。真: 10億円 + 新しい 3 つ
        with NS.yen_scan_on():
            self.assertEqual(NS.shape_of(next(t for t in N.scan(text) if t.text == u"12億3,456")), u"億+万")

    def test_w_7_the_t8_candidates_take_only_new_tokens_and_count_every_status(self):
        text = u"売上高は12億3,456万円で、利益は1,234万円、資本は10億円でした。"
        claims = [{"id": "N001", "value": 123456.0, "unit": u"万円", "span": u"12億3,456万円", "state": "GROUNDED"},
                  {"id": "N002", "value": 1234.0, "unit": u"万円", "span": u"1,234万円", "state": "VALUE_MISMATCH"}]
        base_claims = {"P29E": claims, "P30E": claims}
        base_by_id = dict((p, dict((c["id"], c) for c in claims)) for p in base_claims)
        with Patch() as pt, NS.yen_scan_on():
            pt.set(NS.RUN, "PROFILES", INJECT_PROFILES)
            out, counts = NS.t8_candidates_new(text, [], base_claims, base_by_id, "seed", "bk", RUN.INJECT_CAP)
        self.assertEqual(2, counts[u"円族の新しい token"])                                              # 10億円 は新しい token でない
        self.assertEqual((1, 1, 1, 1), (counts[NS.LINKED], counts[NS.STATUS_NOT_G], counts[u"作れる site"], counts[u"採った"]))     # N001 は結べる・N002 は P30E で GROUNDED でない
        self.assertEqual(counts[u"採った"], len(out))
        for inj, tok, bc in out:
            self.assertIsNotNone(tok.groups)
            self.assertEqual(tok.unit, u"万円")

    def test_w_10_offcheck_job_compares_rows_counts_and_the_lib_blob(self):
        u"""offcheck_job の本体を、zip・文・refs と inject_text_rb を偽にして通す(lib は本物。封の commit の blob と比べる)。1 つずつ食い違わせると 一致 が偽になる。"""
        text = u"売上高は1,234百万円、費用は568千円でした。"
        item = {"docID": "DOC1", "form": "F1", "model": "m1", "writer": "W1"}
        rows = [collections.OrderedDict([("id", "a"), (u"型", "T1_VALUE"), (u"基準の claim", "N001"), (NS.LINK_KEY, True)])]
        counts = {"T1_VALUE": {u"作れる site": 1}}

        def run(expect, patches=()):
            with Patch() as pt:
                pt.set(NS.GEN, "read_zip", lambda row, caches=None: b"zip")
                pt.set(NS.RUN, "read_text", lambda name, it, d: text)
                pt.set(NS.RUN, "refs_for", lambda row, caches, work: [])
                pt.set(NS.RM, "inject_text_rb", lambda zb, t, refs, seed, key, verify=None: (copy.deepcopy(rows), copy.deepcopy(counts)))
                for mod, name, v in patches:
                    pt.set(mod, name, v)
                return NS.offcheck_job(("aiforms", "DOC1_F1_m1", item, {}, "d", {}, "seed", "w", expect))
        good = {"rows": [["a", "T1_VALUE", "N001", True]], "counts": counts}
        b = run(good)
        self.assertEqual((True, True, True, True, 0, 1, 1), (b[u"一致"], b[u"lib が封の commit と一致"], b[u"RB の記録の行と一致"], b[u"RB の記録の数えと一致"], b[u"groups を持つ token"], b[u"行の数"], b[u"RB の記録の行の数"]))
        self.assertEqual([], offcheck_book_problems(norm(b)))
        self.assertGreaterEqual(b[u"token の数"], 2)
        b = run({"rows": [["a", "T1_VALUE", "N002", True]], "counts": counts})                       # 基準の claim が違う
        self.assertEqual((False, False, True, True), (b[u"一致"], b[u"RB の記録の行と一致"], b[u"lib が封の commit と一致"], b[u"RB の記録の数えと一致"]))
        self.assertEqual([], offcheck_book_problems(norm(b)))
        b = run({"rows": good["rows"], "counts": {"T1_VALUE": {u"作れる site": 2}}})                    # 数えが違う
        self.assertEqual((False, False, True), (b[u"一致"], b[u"RB の記録の数えと一致"], b[u"RB の記録の行と一致"]))
        real_scan, real_render = N.scan, N.render_value

        def scan_shifted(t):
            toks = real_scan(t)
            toks[0].value += 1.0
            return toks
        b = run(good, ((N, "scan", scan_shifted),))                                                   # lib の scan が封の commit と違う
        self.assertEqual((False, False, True, True), (b[u"一致"], b[u"lib が封の commit と一致"], b[u"RB の記録の行と一致"], b[u"RB の記録の数えと一致"]))
        self.assertNotEqual(b[u"token の sha256"], b[u"封の commit の lib の token の sha256"])
        b = run(good, ((N, "render_value", lambda v, like: u"x"),))                                   # lib の描きだけが違う(token は同じ)
        self.assertEqual((False, False), (b[u"一致"], b[u"lib が封の commit と一致"]))
        self.assertEqual(b[u"token の sha256"], b[u"封の commit の lib の token の sha256"])
        self.assertNotEqual(b[u"関数の出力の sha256"], b[u"封の commit の lib の関数の出力の sha256"])
        self.assertIs(N.scan, real_scan)
        self.assertIs(N.render_value, real_render)

    def test_w_9_the_header_of_a_real_record_passes_the_header_check(self):
        u"""script の ``header_h`` が作る頭(封・script・lib・前の便の script・engine・cache)が、門の頭の検査を通る。1 欄ずつ落とすと赤。"""
        h = NS.header_h(ROOT, u"標本", {u"seed_file": u"x"}, {}, {}, INJECT_PROFILES)
        rec = collections.OrderedDict(h)
        rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
        rec[u"範囲"] = u"全 200 本"
        self.assertEqual([], header_problems("inject", norm(rec), True))
        for key in (u"lib の指紋", u"封の commit の numbers.py の sha256", u"rmix script の sha256", u"RB の記録の sha256", u"engine の指紋", u"この script の sha256", u"生成の記録の sha256"):
            r2 = norm(rec)
            r2.pop(key)
            self.assertNotEqual([], header_problems("inject", r2, True), key)

    def test_w_8_reread_and_groups_helpers(self):
        with NS.yen_scan_on():
            tok = N.scan(u"売上高は12億3,456万円でした。")[0]
            self.assertTrue(NS.reread_ok(u"売上高は12億3,458万円でした。", tok, 123458.0))
            self.assertFalse(NS.reread_ok(u"売上高は12億3,458万円でした。", tok, 123457.0))             # 値が違う
            self.assertFalse(NS.reread_ok(u"売上高は12億3,458万株でした。", tok, 123458.0))              # 円が続かない
            self.assertTrue(NS.reread_ok(u"売上高は9,700万円でした。", tok, 9700.0))                    # 先頭の位が落ちても値と単位が合えば合い
            like = N.scan(u"資本は10億円でした。")[0]                                                       # 億だけの token は単位 億円
            self.assertTrue(NS.reread_ok(u"資本は11億円でした。", like, 11.0))
            self.assertFalse(NS.reread_ok(u"資本は11億株でした。", like, 11.0))                          # start と値が合っても単位が違えば合わない
        self.assertEqual(2, NS.groups_in(u"5兆1,234"))
        self.assertEqual(1, NS.groups_in(u"9,700"))
        self.assertEqual(2, NS.groups_in(u"12億3,458"))


# ================================================================ 宣言(docID を持つ記録 2 つは LATER_NAMING_FILES に、script は LATER_HARNESS_FILES に宣言する)
def literal_assign(src, name):
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name:
            return n.value
    return None


def later_naming_files(src):
    node = literal_assign(src, "LATER_NAMING_FILES")
    return list(ast.literal_eval(node)) if node is not None else None


def naming_problems(src):
    got = later_naming_files(src)
    if got is None:
        return [u"LATER_NAMING_FILES が読めない"]
    return [u"LATER_NAMING_FILES に %s が無い" % rel for rel in REC_REL.values() if rel not in got] + \
        [u"LATER_NAMING_FILES に docID を持たない %s がある" % rel for rel in [SCRIPT_REL, DOC_REL] + list(SG.GATE_RELS) if rel in got]


def harness_problems(src):
    node = literal_assign(src, "LATER_HARNESS_FILES")
    if node is None:
        return [u"LATER_HARNESS_FILES が読めない"]
    rows = [r for r in ast.literal_eval(node) if r[0] == SCRIPT_REL]
    if len(rows) != 1:
        return [u"LATER_HARNESS_FILES に %s が 1 回だけ無い" % SCRIPT_REL]
    return []


class DeclarationTest(unittest.TestCase):
    def test_h_1_the_two_records_are_declared_as_naming_files(self):
        src = read("tests/measure/test_xbrl_fresh_seal.py")
        self.assertEqual([], naming_problems(src))
        for rel in REC_REL.values():
            self.assertNotEqual([], naming_problems(src.replace('"%s"' % rel, '"x/%s"' % rel)), rel)
        self.assertNotEqual([], naming_problems(src.replace("LATER_NAMING_FILES", "LATER_NAMING_FILE")))
        last = list(REC_REL.values())[-1]
        self.assertNotEqual([], naming_problems(src.replace('"%s"' % last, '"%s", "%s"' % (last, SG.GATE_RELS[0]))))

    def test_h_2_the_previous_declarations_are_still_there(self):
        got = later_naming_files(read("tests/measure/test_xbrl_fresh_seal.py"))
        for rel in ("fixtures/xbrl/rmix/ai200_2026-11-04.json", "fixtures/xbrl/numfix/ai200_2026-11-04.json", "fixtures/xbrl/p28e/regress97_2026-11-03.json"):
            self.assertIn(rel, got)

    def test_h_3_the_script_is_declared_as_a_harness_file(self):
        src = read("tests/measure/test_xbrl_inject_harness_review.py")
        self.assertEqual([], harness_problems(src))
        self.assertNotEqual([], harness_problems(src.replace(u'"%s"' % SCRIPT_REL, u'"x/%s"' % SCRIPT_REL)))
        self.assertNotEqual([], harness_problems(src.replace("LATER_HARNESS_FILES", "LATER_HARNESS_FILE")))


# ================================================================ 順序(e)の変異(使い捨ての repo)
OTHERS = list(REC_REL.values()) + [DOC_REL]
IMPLS = list(LIB_RELS)


class OrderMutationTest(unittest.TestCase):
    def _repo(self, before_seal=(), after_seal=(), commit_impl=True, commit_others=OTHERS):
        r = PR.Repo()
        for f in before_seal:
            r.put(f)
            r.commit(f)
        r.put(SEAL_REL)
        s = r.commit(SEAL_REL)
        for f in after_seal:
            r.put(f)
            r.commit(f)
        if commit_impl:
            for f in IMPLS:
                r.put(f)
            r.commit(*IMPLS)
        for f in commit_others:
            r.put(f)
        if commit_others:
            r.commit(*commit_others)
        return r, s

    def probe(self, r, s):
        return PR.order_problems(r.d, PREFIX, SEAL_REL, s[:7], IMPLS, OTHERS)

    def test_e_1_good_order_is_green(self):
        r, s = self._repo()
        self.assertEqual([], self.probe(r, s))

    def test_e_2_records_before_the_seal_before_the_lib_or_uncommitted_are_red(self):
        r, s = self._repo(commit_others=[])
        self.assertEqual(sorted("UNCOMMITTED:" + o for o in OTHERS), sorted(self.probe(r, s)))
        r2, s2 = self._repo(before_seal=[OTHERS[0]], commit_others=OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], self.probe(r2, s2))
        r3, s3 = self._repo(after_seal=[OTHERS[0]], commit_others=OTHERS[1:])
        self.assertIn("BEFORE_IMPL:" + OTHERS[0], self.probe(r3, s3))
        r4, s4 = self._repo(commit_impl=False)
        self.assertTrue(any(p.startswith("IMPL_UNCOMMITTED:") for p in self.probe(r4, s4)))

    def test_e_5_order_of_uses_the_lib_files_and_the_records_and_the_document(self):
        r, s = self._repo()
        self.assertEqual([], PR.order_problems(r.d, PREFIX, SEAL_REL, s[:7], list(LIB_RELS), OTHERS))
        self.assertEqual(IMPLS, list(LIB_RELS))
        r2, s2 = self._repo(commit_others=OTHERS[:-1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[-1]], PR.order_problems(r2.d, PREFIX, SEAL_REL, s2[:7], list(LIB_RELS), OTHERS))

    def test_e_3_a_wrong_seal_is_red(self):
        r, _s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", PR.order_problems(r.d, PREFIX, SEAL_REL, "abcdef0", IMPLS, OTHERS))

    def test_e_4_the_engine_fingerprint_comes_from_the_tree_at_the_seal_commit(self):
        fp = engine_fingerprint_at_seal()
        self.assertEqual(2, len(fp))
        for v in fp.values():
            self.assertRegex(v, r"^[0-9a-f]{64}$")


# ================================================================ 本番の記録(a)(b)(d)(e)
class RealRecordsTest(unittest.TestCase):
    u"""記録が無いときは各試験が skip する(skip でも行が出ることは SkipLineTest が確かめる)。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def need(self):
        if not records_exist():
            self.skipTest(u"記録が無い(offcheck・inject を走らせた後に走る)")
        return load_records()

    def test_r_1_records_are_clean_and_consistent(self):
        R = self.need()
        self.assertEqual([], record_problems(copy.deepcopy(R), full=True))

    def test_r_2_judgment_is_rebuilt_from_the_records(self):
        R = self.need()
        self.assertEqual([], judge_problems(R, self.seal))
        J = NS.build_J(R, self.seal)
        self.assertEqual(set(J), {u"H", u"K", u"採用", u"欄"})

    def test_r_3_the_result_document_follows_the_records(self):
        R = self.need()
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), R, self.seal))

    def test_r_4_order_is_seal_then_lib_then_records_and_document(self):
        self.need()
        self.assertEqual([], order_of(REPO))


class SkipLineTest(unittest.TestCase):
    def test_s_1_a_skipped_real_record_test_still_prints_a_line(self):
        u"""記録が無いと本番の記録の試験は skip になるが、skip でも行が出る(黙って消えない)。"""
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(RealRecordsTest)
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


if __name__ == "__main__":
    unittest.main()
