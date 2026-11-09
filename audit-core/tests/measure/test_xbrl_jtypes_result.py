# -*- coding: utf-8 -*-
"""J(AI の文 200 本に注入の型を広げる: T2_UNIT・T6_PRIOR・T7_ROUND。切り替え ``yen_scan_2026_11_05``)の測定の結果の門。封 docs/XBRL_INJECT_TYPES_SEAL_2026-11-05.md §5。

記録 1 つ(``fixtures/xbrl/jtypes/inject_2026-11-05.json``)と、読むだけの H の記録・RB の記録から、封 §3 の予測 J-1〜J-10 と §4 の採用の基準 K-1〜K-4 を**機械で求め**(予測の幅は封の字から読む。字のコピーにしない)、
結果の文書 ``docs/XBRL_INJECT_TYPES_RESULT_2026-11-05.md`` の表(``<!-- 門:start pred -->``・``<!-- 門:start judge -->`` の中)を記録から作り直した表と一行も違わないことを見る。
測定の script(``measure/xbrl_jtypes_2026-11-05.py`` の ``build_J``・``judge_from``・``j_columns``・``render_pred``・``render_judge``)の関数を呼んで照らす。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文など)が無い・key_leaks が空・docID を持つ記録が ``LATER_NAMING_FILES`` に宣言され、script が ``LATER_HARNESS_FILES`` に宣言されている・
     cache の前後が同じ・script と lib と前の便の script・記録の sha256 が現物と一致・engine の指紋が封の commit の木から作り直した値と一致する・切り替えの欄(inject の中が真・出たあとが偽)。
  b  記録の中身が再計算と一致する: 本ごとの数えの整合(欄の間・行との関係・型ごとの cap)・行の整合・集計(``inject_summaries``)・型 × 形の内訳・
     **J の欄の全部を 本ごとの数えと行から数え直す**(欄を 0 に固定すると赤。行の欄を 1 つ変えると該当の欄が動く)・限界(封 §6 の字 + script の限界)。
  c  判定: 記録(の欄)を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。採用は K-1〜K-4 を全部満たすときだけ。
  d  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 edad5cd ⊏ 記録・結果の文書(script・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  g  変異: 小さい標本の記録と文書で同じ検査が緑 → 変異(記録の数・J の欄・表の 1 字・封の予測の 1 字・順序・記録の禁止欄・指紋の 1 字・cache の前後・切り替え・届いた の欄・T2 の後の単位)で赤。
  w  手順: script の ``inject_text_j`` を小さい入力(zip・判定は偽。lib は本物)で通す。T2 の注入後の claim を後の単位で引く・複合の写しだけが複合・仕掛けの経路の site は既存 / 万だけ。

記録が無いときは (a)(b)(d)(e) の本番の記録の試験を skip する(skip でも行が出ることを試験が確かめる)。標本の試験 (c)(g)(w) は記録が無くても走る。この file は docID の字を持たない。
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
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


SG = load_module("tests/measure/test_xbrl_jtypes_seal.py", "jtypes_seal_gate_for_result")        # 封の門の部品。門としては走らせない
PR = SG.PR                                                                                    # doc_blocks・prose_problems・order_problems・Repo
JT = SG.JT
NS = JT.NS
RM, NF, GEN, RUN, TUNE, IJ, S = JT.RM, JT.NF, JT.GEN, JT.RUN, JT.TUNE, JT.IJ, JT.S
N, SC = JT.N, JT.SC

SEAL_REL = JT.SEAL_REL
DOC_REL = JT.DOC_REL
SEAL_COMMIT_SHORT = JT.SEAL_COMMIT
REC_REL = collections.OrderedDict(JT.REC_REL)
SCRIPT_REL = JT.SCRIPT_REL
LIB_RELS = JT.LIB_RELS
FLAG = JT.FLAG
NOT_GATED = PR.NOT_GATED
HIT, MISS = JT.HIT, JT.MISS
J_TYPES = JT.J_TYPES
SHAPES = JT.SHAPES
LINK_KEY = JT.LINK_KEY
FORBIDDEN_KEYS = tuple(RUN.FORBIDDEN_KEYS) + (u"理由", u"根拠", u"周り", u"content")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = SG.DOCID_RE
FOR_RESULT_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
HAVE_CACHE = all(os.path.isdir(p) for p in JT.caches_all().values())
INJECT_PROFILES = JT.INJECT_PROFILES
STATES = NF.STATES
#: 封 §3・§4 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("J-1", u"一致"),
    ("J-2", collections.OrderedDict([
        ("T2", collections.OrderedDict([(u"既存", (7900.0, 8150.0)), (u"万だけ", (1780.0, 1860.0)), (u"site にしない複合", (5300.0, 5500.0))])),
        ("T6", collections.OrderedDict([(u"既存", (55.0, 70.0)), (u"万だけ", (12.0, 20.0)), (u"複合", (250.0, 300.0))])),
        ("T7", collections.OrderedDict([(u"既存", (360.0, 390.0)), (u"万だけ", (230.0, 260.0)), (u"複合", (1150.0, 1300.0))]))])),
    ("J-3", collections.OrderedDict([
        ("T2", collections.OrderedDict([(u"採った", (1700.0, 2000.0)), (u"うち土台 P30E が GROUNDED の行", (700.0, 1300.0))])),
        ("T6", collections.OrderedDict([(u"採った", (280.0, 349.0)), (u"うち土台 P30E が GROUNDED の行", (150.0, 300.0))])),
        ("T7", collections.OrderedDict([(u"採った", (1500.0, 1900.0)), (u"うち土台 P30E が GROUNDED の行", (800.0, 1400.0))]))])),
    ("J-4", collections.OrderedDict([("T2_UNIT", (0.0, 1.0)), ("T6_PRIOR", (0.0, 12.0)), ("T7_ROUND", (10.0, 40.0))])),
    ("J-5", 2.0),
    ("J-6", collections.OrderedDict([("T2_UNIT", (55.0, 90.0)), ("T6_PRIOR", (55.0, 95.0)), ("T7_ROUND", (50.0, 90.0))])),
    ("J-7", collections.OrderedDict([(u"違う行", (10.0, 150.0)), (u"T7 の割合", 80.0)])),
    ("J-8", 0),
    ("J-9", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"先頭の位が減った行", (0, 40))])),
    ("J-10", collections.OrderedDict([(u"偽", 0), (u"真", (600.0, 750.0)), (u"その他を含む", 0)])),
    ("K-1", u"一致"), ("K-2", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0)])), ("K-3", 1800.0), ("K-4", 0)])
#: 注入の土台の字・site の字(測定の script の定数と同じでなければ赤)
BASE_WORD_PIN = u"無改変の文で P30E が GROUNDED の claim"
SITE_WORD_PIN = u"T2 は複合を除く・T6 と T7 は仕掛けの経路(既存・万だけ)+ 複合の写し"
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
G, V_, U_, P_ = "GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
INFO_J1 = (u"lib の指紋が H の記録と一致", u"engine の指紋が RB の記録と一致", u"inject.py・sites.py が封の commit から変わった file")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def jload(rel):
    return json.loads(read(rel))


def sha256_rel(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def records_exist():
    if FORCE["no_records"]:
        return False
    return all(os.path.exists(os.path.join(ROOT, v)) for v in REC_REL.values())


_FIXED = {}


def fixed_records():
    u"""読むだけの H の記録・RB の記録(1 回だけ読む)。"""
    if not _FIXED:
        _FIXED["h"] = jload(JT.H_RECORD_REL)
        _FIXED["rb"] = jload(JT.RB_RECORD_REL)
    return _FIXED


def load_records():
    f = fixed_records()
    return collections.OrderedDict([("inject", jload(INJECT_REL_STR())), ("h", f["h"]), ("rb", f["rb"])])


def INJECT_REL_STR():
    return REC_REL["inject"]


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
        got = JT.seal_bounds(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return [u"封から幅を読めない(%s)" % type(e).__name__]
    for k, v in BOUNDS_PIN.items():
        g = got.get(k)
        if json.dumps(norm_t(g), sort_keys=True) != json.dumps(norm_t(v), sort_keys=True):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, g, v))
    if list(JT.seal_pred_rows(seal)) != list(SG.PRED_IDS) or list(JT.seal_k_rows(seal)) != list(SG.K_IDS):
        out.append(u"封の予測の行が J-1〜J-10 でない・K の行が K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 記録(a)(b)
def walk(o):
    return list(RUN.walk_keys(o))


def header_problems(rec, full):
    u"""記録の頭(封・script・lib・前の便の script と記録・engine・cache・切り替え)。"""
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"封の名か commit が違う")
    want = collections.OrderedDict([
        (u"この script の sha256", sha256_rel(SCRIPT_REL)), (u"nscan script の sha256", sha256_rel(JT.NS_SCRIPT_REL)), (u"rmix script の sha256", sha256_rel("measure/xbrl_rmix_2026-11-04.py")),
        (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")), (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")),
        (u"生成の script の sha256", sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")), (u"H の記録の sha256", sha256_rel(JT.H_RECORD_REL)), (u"RB の記録の sha256", sha256_rel(JT.RB_RECORD_REL))])
    for name, v in want.items():
        if rec.get(name) != v:
            out.append(u"%s が現物と違う" % name)
    gens = dict((src, sha256_rel(p["gen"])) for src, p in JT.SOURCES.items())
    if norm(rec.get(u"生成の記録の sha256")) != gens:
        out.append(u"生成の記録の sha256 が現物と違う")
    if norm(rec.get(u"lib の指紋")) != dict((rel, sha256_rel(rel)) for rel in LIB_RELS):
        out.append(u"lib の指紋が現物と違う")
    if rec.get(u"profile") != list(INJECT_PROFILES):
        out.append(u"profile が (P29E, P30E) でない")
    fp = rec.get(u"engine の指紋") or {}
    want_fp = engine_fingerprint_at_seal()
    for name in want_fp:
        if name == "adapter_xbrl_py_sha256" and (SG.SGR.pb_declared_fingerprint(fp.get(name)) or SG.SGR.t_declared_fingerprint(fp.get(name))):      # 2026-11-09(T): 封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md §2-3 が宣言した遷移の指紋も(封が履歴に在るときだけ。SGR.t_declared_fingerprint)。2026-11-06(PB): 封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §2-3 が宣言した遷移の指紋(封が履歴に在るときだけ)
            continue
        if fp.get(name) != want_fp[name]:
            out.append(u"engine の指紋 %s が封の commit の木から作り直した値と違う" % name)
    cb = rec.get(u"cache の前後") or {}
    if cb.get(u"変化なし") is not True or cb.get(u"前") != cb.get(u"後"):
        out.append(u"cache の前後が同じでない")
    sw = rec.get(u"切り替え") or {}
    if sw.get(u"名前") != FLAG or sw.get(u"配線の問題") != []:
        out.append(u"切り替えの名前が違う・配線の問題が空でない")
    if sw.get(u"inject の中の値") is not True or sw.get(u"出たあとの値") is not False:
        out.append(u"inject の中が真・出たあとが偽になっていない")
    if full and rec.get(u"範囲") != u"全 200 本":
        out.append(u"範囲が全 200 本でない")
    return out


def clean_problems(rec):
    out = []
    bad = sorted(set(x for x in walk(rec) if x in FORBIDDEN_KEYS))
    if bad:
        out.append(u"記録に repo へ入れない欄がある: %s" % u",".join(bad))
    text = json.dumps(rec, ensure_ascii=False)
    for w in COMPANY_WORDS:
        if w in text:
            out.append(u"会社名らしい字がある")
    try:
        JT.assert_clean_j(copy.deepcopy(rec))
    except GEN.Stop:
        out.append(u"鍵らしい字が記録に在る")
    if rec.get(u"key_leaks", []) != []:
        out.append(u"key_leaks が空でない")
    return out


def count_problems(name, c, rows, cap):
    u"""本ごとの数え 1 本の整合(自分の欄の間と、その本の行との関係)。"""
    out = []
    kinds = c[u"token の数え"]
    allk, qk = kinds[u"全部"], kinds[u"うち is_quantity 真"]
    if list(allk) != list(JT.KIND4) or list(qk) != list(JT.KIND4) or any(qk[k] > allk[k] for k in allk):
        out.append(u"%s: token の種類別の数が合わない" % name)
    if u"注入しない" in c:
        if rows:
            out.append(u"%s: 注入しない本に行がある" % name)
        return out
    t5 = c["T5_COINCIDENT"]
    if t5[u"真"] != sum(t5[u"真の相手の単位"].values()) or t5[u"偽"] < 0 or min(t5[u"others の単位の内訳"].values()) < 0:
        out.append(u"%s: T5 の数えが合わない" % name)
    if t5[u"真の相手の単位"][u"その他を含む"] > 0 and t5[u"others の単位の内訳"][u"その他"] == 0:
        out.append(u"%s: T5 の相手の単位の内訳が合わない" % name)
    ok_keys = (JT.LINKED, JT.UNLINKED)
    existing = allk[u"既存"] + allk[u"万円(空白入り)"]
    for t in J_TYPES:
        ct = c[t]
        sh = ct[u"作れる site"]
        sites = sum(sh.values())
        pop, taken = ct[u"作れる site の状態"], ct[u"採った の状態"]
        mine = [r for r in rows if r[u"型"] == t]
        if sum(pop.values()) != sites:
            out.append(u"%s: %s の作れる site の状態の和が作れる site と合わない" % (name, t))
        if sum(taken.values()) != ct[u"採った"] or ct[u"採った"] > cap or ct[u"cap を基準で絞る前に掛けた数"] > cap:
            out.append(u"%s: %s の採った・cap の数えが合わない" % (name, t))
        if any(taken.get(k, 0) > pop.get(k, 0) for k in taken):
            out.append(u"%s: %s の採った の状態が作れる site の状態より多い" % (name, t))
        if sh.get(u"既存", 0) > existing or sh.get(u"万だけ", 0) > allk[u"万だけ"] or sh.get(u"複合", 0) > allk[u"複合"]:
            out.append(u"%s: %s の site が token の数より多い" % (name, t))
        linked = sum(1 for r in mine if r[LINK_KEY])
        if len(mine) != sum(taken.get(k, 0) for k in ok_keys) or linked != taken.get(JT.LINKED, 0):
            out.append(u"%s: %s の行の数・P29E に対応が付く行の数が 採った の状態と合わない" % (name, t))
        if t == "T2_UNIT":
            if list(sh) != [u"既存", u"万だけ"] or ct[u"select の作れる site"] != sites or ct[u"採った"] != min(cap, sites) or ct[u"cap を基準で絞る前に掛けた数"] != ct[u"採った"]:
                out.append(u"%s: T2_UNIT の作れる site・採った が select の数えと合わない" % name)
            if not (0 <= ct[u"site にしなかった複合"] <= allk[u"複合"]):
                out.append(u"%s: site にしなかった複合が token の数より多い" % name)
        else:
            good = pop.get(JT.LINKED, 0) + pop.get(JT.UNLINKED, 0)
            if list(sh) != list(SHAPES) or ct[u"土台 P30E が GROUNDED の site"] != good or ct[u"cap を基準で絞る前に掛けた数"] != min(cap, sites) or ct[u"採った"] != min(cap, good):
                out.append(u"%s: %s の土台 GROUNDED の site・cap・採った の関係が合わない" % (name, t))
            if set(taken) - set(ok_keys):
                out.append(u"%s: %s の採った の状態に土台 GROUNDED でない状態がある" % (name, t))
    return out


def row_problems(r, labels, seen):
    out = []
    if r[u"型"] not in J_TYPES:
        out.append(u"型が語でない")
    if r[u"id"] in seen:
        out.append(u"同じ注入の id が 2 回ある")
    seen.add(r[u"id"])
    name = u"%s_%s_%s" % (r["docID"], r["form"], r["model"])
    if not r[u"id"].startswith(name + u"-" + r[u"型"].split("_")[0] + u"-"):
        out.append(u"id が本の名前 + 型の形でない")
    linked = r.get(LINK_KEY)
    unmapped = {u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}
    if not isinstance(linked, bool):
        out.append(u"P29E の土台に対応の欄が真偽でない")
    elif not linked and norm(r["P29E"]) != unmapped:
        out.append(u"P29E の土台に対応が無い行の P29E の欄が対応なしでない")
    if r["P30E"][u"対応"] is True and r["P30E"][u"結果"] == TUNE.LABEL_UNMAPPED:
        out.append(u"P30E の欄の対応と結果が合わない")
    for key in (u"round-trip", u"読み直し", u"先頭の位が減った", u"届いた"):
        if not isinstance(r.get(key), bool):
            out.append(u"行の %s が真偽でない" % key)
    if r.get(u"形") not in SHAPES or (r[u"型"] == "T2_UNIT" and r.get(u"形") == u"複合"):
        out.append(u"行の形が語でない・T2_UNIT に複合がある")
    if r[u"型"] == "T2_UNIT":
        if not isinstance(r.get(u"単位"), str) or not r.get(u"単位"):
            out.append(u"T2_UNIT の行の単位が語でない")                       # T2 は単位の差し替えなので単位が要る
    elif r.get(u"単位") is not None and (not isinstance(r.get(u"単位"), str) or not r.get(u"単位")):
        out.append(u"行の単位が語でも None でもない")                          # T6・T7 は単位の無い数(件数など)にも在る
    if r[u"型"] == "T2_UNIT":
        if not isinstance(r.get(u"単位の後"), str) or r.get(u"単位の後") == r.get(u"単位") or r.get(u"符号") is not None:
            out.append(u"T2_UNIT の単位の後・符号の欄が合わない")
    elif r.get(u"単位の後") is not None:
        out.append(u"T2_UNIT でない行に単位の後がある")
    if r[u"型"] == "T7_ROUND":
        if r.get(u"符号") not in (1, -1) or isinstance(r.get(u"符号"), bool):
            out.append(u"T7_ROUND の符号が +1 か -1 でない")
    elif r[u"型"] == "T6_PRIOR" and r.get(u"符号") is not None:
        out.append(u"T6_PRIOR に符号がある")
    if r[u"先頭の位が減った"] and (r[u"型"] == "T2_UNIT" or r[u"形"] != u"複合"):
        out.append(u"先頭の位が減ったのは T6・T7 の複合だけ")
    if r[u"届いた"] and not r["P30E"][u"対応"]:
        out.append(u"P30E に対応が付かない行が届いた")
    for p in INJECT_PROFILES:
        c = r[p]
        if c[u"結果"] not in labels:
            out.append(u"結果が classify の語でない")
        if not RUN.reason_ok(c[u"reason"]):
            out.append(u"reason が符号の形でない")
    return out


def inject_problems(rec, full):
    out = []
    if rec.get(u"profile") != list(INJECT_PROFILES):
        out.append(u"inject: profile が (P29E, P30E) でない")
    if rec[u"型"].get(u"土台") != BASE_WORD_PIN or JT.BASE_WORD != BASE_WORD_PIN:
        out.append(u"inject: 型.土台 の字が P30E が GROUNDED の claim でない")
    if rec[u"型"].get(u"site") != SITE_WORD_PIN or JT.SITE_WORD != SITE_WORD_PIN:
        out.append(u"inject: 型.site の字が違う")
    seal = read(SEAL_REL)
    if rec.get(u"限界") != JT.seal_limits(seal) + list(JT.EXTRA_LIMITS) or len(rec.get(u"限界") or []) != 10:
        out.append(u"inject: 限界が封 §6 の字(6 つ)とこの script の限界(4 つ)と違う")
    want = collections.OrderedDict([(u"全体", sum(1 for r in rec[u"行"] if r.get(LINK_KEY) is not True))])
    for t in J_TYPES:
        want[t] = sum(1 for r in rec[u"行"] if r.get(u"型") == t and r.get(LINK_KEY) is not True)
    if norm(rec.get(u"P29E に対応なしの行の数")) != norm(want):
        out.append(u"inject: P29E に対応なしの行の数が行から数え直した値と違う")
    labels = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
    seen, cnt = set(), collections.Counter()
    for r in rec[u"行"]:
        out += [u"inject: " + x for x in row_problems(r, labels, seen)]
        cnt[(r[u"docID"], r[u"form"], r[u"model"], r[u"型"])] += 1
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
            out += [u"inject: " + x for x in count_problems(name, c, by_book.get(name, []), RUN.INJECT_CAP)]
        except Exception as e:                               # noqa: BLE001  壊れた記録は数え直せない = 赤
            out.append(u"inject: %s の数えを検査できない(%s)" % (name, type(e).__name__))
    with Patch() as pt:
        pt.set(RUN, "PROFILES", INJECT_PROFILES)
        summ, summ_cmp = (norm(x) for x in JT.inject_summaries(rec[u"行"]))
        bd = norm(JT.breakdown(rec[u"行"]))
    if summ != rec[u"集計"] or rec[u"注入の行の数"] != len(rec[u"行"]):
        out.append(u"inject: 集計が行から作り直した値と違う")
    if list(summ) != list(J_TYPES):
        out.append(u"inject: 集計の型が J の 3 型でない")
    if summ_cmp != rec.get(JT.COMPARE_KEY):
        out.append(u"inject: 比較用の集計(P29E にも対応が付く site だけ)が行から作り直した値と違う")
    if bd != rec.get(JT.BREAKDOWN_KEY):
        out.append(u"inject: 型 × 形の内訳が行から作り直した値と違う")
    try:
        cols = norm(JT.j_columns(per, rec[u"行"]))
    except Exception as e:                                   # noqa: BLE001
        return out + [u"inject: J の欄を作れない(%s)" % type(e).__name__]
    if cols != rec.get(JT.J_KEY):
        out.append(u"inject: J の欄が 本ごとの数え と 行 から作り直した値と違う")
    if full:
        names = [x[u"name"] for src in JT.SOURCES.values() for x in jload(src["claims"])[u"本"] if not x.get(u"欠け")]
        if list(per) != names:
            out.append(u"inject: 本ごとの数えの本が 200 本(前の便の claims の並び)でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(JT.caches_all())):
            out.append(u"inject: cache の件数か名前が記録の前と違う")
    return out


def record_problems(R, full=True):
    u"""記録(R["inject"])の検査(禁止欄・鍵・script と lib と前の便の sha256・engine の指紋・cache・再計算)。問題の列。"""
    rec = R["inject"]
    out = []

    def safe(label, fn, *a):
        try:
            return fn(*a)
        except Exception as e:                               # noqa: BLE001  壊れた記録は検査できない = 赤(例外で落とさず問題に数える)
            return [u"%s: 検査できない(%s)" % (label, type(e).__name__)]
    out += safe("clean", clean_problems, rec)
    out += safe("header", header_problems, rec, full)
    out += safe("inject", inject_problems, rec, full)
    return out


def judge_problems(R, seal):
    u"""判定の関数が記録から作り直せるか(壊れた記録は赤)。"""
    try:
        J = JT.build_J(R, seal, [])
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"J"]) != list(SG.PRED_IDS) or list(J[u"K"]) != list(SG.K_IDS):
        out.append(u"判定の行が J-1〜J-10・K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R, seal, numstat=()):
    J = JT.build_J(R, seal, list(numstat))
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != JT.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("judge") != JT.render_judge(J, seal).split(u"\n"):
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
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ================================================================ 小さい標本の記録(通信しない・cache を読まない)
ITEMS = [dict(docID="DOC1", form="F1", model="m1", writer="W1"), dict(docID="DOC2", form="F5", model="m2", writer="W2"), dict(docID="DOC3", form="F1", model="m1", writer="W1")]


def sample_header():
    cache = collections.OrderedDict([("edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": "2" * 64})])
    return collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"step", u"標本"), (u"HEAD の commit", "3" * 40),
        (u"この script の sha256", sha256_rel(SCRIPT_REL)), (u"生成の script の sha256", sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")),
        (u"生成の記録の sha256", collections.OrderedDict((src, sha256_rel(p["gen"])) for src, p in JT.SOURCES.items())),
        (u"engine の指紋", dict(engine_fingerprint_at_seal(), adapter_xbrl_py_files=16, core_py_files=4, git_commit="3" * 40)),
        (u"種の確認", {u"seed_file": u"x"}), (u"profile", list(INJECT_PROFILES)),
        (u"cache の前後", collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)])),
        (u"nscan script の sha256", sha256_rel(JT.NS_SCRIPT_REL)), (u"rmix script の sha256", sha256_rel("measure/xbrl_rmix_2026-11-04.py")),
        (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")), (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")),
        (u"H の記録の sha256", sha256_rel(JT.H_RECORD_REL)), (u"RB の記録の sha256", sha256_rel(JT.RB_RECORD_REL)),
        (u"lib の指紋", collections.OrderedDict((rel, sha256_rel(rel)) for rel in LIB_RELS)), (u"範囲", u"標本")])


def kinds_of(a, b, c, d, qa=None, qb=None, qc=None, qd=None):
    u"""token の種類別の数。全部 = (既存, 万円(空白入り), 万だけ, 複合)。is_quantity 真は省略時に全部と同じ。"""
    allk = collections.OrderedDict(zip(JT.KIND4, (a, b, c, d)))
    q = collections.OrderedDict(zip(JT.KIND4, (a if qa is None else qa, b if qb is None else qb, c if qc is None else qc, d if qd is None else qd)))
    return collections.OrderedDict([(u"全部", allk), (u"うち is_quantity 真", q)])


def t5_of(off, on, none_yen, other, e_none, e_yen, e_other):
    return collections.OrderedDict([(u"偽", off), (u"真", on), (u"真の相手の単位", collections.OrderedDict([(u"全部 None か 円", none_yen), (u"その他を含む", other)])),
                                    (u"others の単位の内訳", collections.OrderedDict([("None", e_none), (u"円", e_yen), (u"その他", e_other)]))])


def sd(**kw):
    return collections.OrderedDict(sorted(kw.items()))


def pop_of(linked=0, unlinked=0, not_g=0, no_base=0):
    d = {}
    for k, v in ((JT.LINKED, linked), (JT.UNLINKED, unlinked), (JT.STATUS_NOT_G, not_g), (JT.STATUS_NO_BASE, no_base)):
        if v:
            d[k] = v
    return collections.OrderedDict(sorted(d.items()))


def t2_count(exist, man, skipped, pop, taken, taken_pop):
    sites = exist + man
    return collections.OrderedDict([(u"作れる site", collections.OrderedDict([(u"既存", exist), (u"万だけ", man)])), (u"site にしなかった複合", skipped), (u"作れる site の状態", pop),
                                    (u"採った", taken), (u"cap を基準で絞る前に掛けた数", taken), (u"採った の状態", taken_pop), (u"select の作れる site", sites)])


def t67_count(exist, man, comp, pop, taken_pop):
    sites = exist + man + comp
    good = pop.get(JT.LINKED, 0) + pop.get(JT.UNLINKED, 0)
    return collections.OrderedDict([(u"作れる site", collections.OrderedDict([(u"既存", exist), (u"万だけ", man), (u"複合", comp)])), (u"作れる site の状態", pop),
                                    (u"土台 P30E が GROUNDED の site", good), (u"cap を基準で絞る前に掛けた数", min(RUN.INJECT_CAP, sites)), (u"採った", min(RUN.INJECT_CAP, good)),
                                    (u"採った の状態", taken_pop)])


def cell(res, state, reason=None):
    return collections.OrderedDict([(u"対応", True), (u"結果", res), (u"state", state), (u"reason", reason)])


PASS_ = (TUNE.LABEL_PASS, G)
NAMED = (TUNE.LABEL_NAMED_ORIGINAL, V_)
OTHER = (TUNE.LABEL_NAMED_OTHER, V_)
PNF = (TUNE.LABEL_PNF, P_, "no_element")


def jrow(item, rid, typ, shape, unit, linked, p29, p30, after=None, sign=None, rt=True, rr=True, lead=False, reached=False):
    row = collections.OrderedDict([(u"docID", item["docID"]), (u"form", item["form"]), (u"model", item["model"]), (u"writer", item["writer"]),
                                   ("id", u"%s_%s_%s-%s" % (item["docID"], item["form"], item["model"], rid)), (u"型", typ), (u"形", shape), (u"単位", unit), (u"単位の後", after), (u"符号", sign),
                                   (u"基準の claim", u"N%03d" % (len(rid) + 1)), (LINK_KEY, linked), (u"round-trip", rt), (u"読み直し", rr), (u"先頭の位が減った", lead)])
    row["P29E"] = cell(*p29) if linked else TUNE.classify(None, None)
    row["P30E"] = cell(*p30)
    row[u"届いた"] = reached
    return row


def sample_rows():
    a, c = ITEMS[0], ITEMS[2]
    return [
        jrow(a, "T2-01", "T2_UNIT", u"既存", u"百万円", True, NAMED, NAMED, after=u"千円", reached=True),
        jrow(a, "T2-02", "T2_UNIT", u"万だけ", u"万円", True, NAMED, PASS_, after=u"円"),
        jrow(a, "T6-01", "T6_PRIOR", u"既存", u"円", True, PNF, NAMED),
        jrow(a, "T6-02", "T6_PRIOR", u"複合", u"万円", True, NAMED, NAMED),
        jrow(a, "T6-03", "T6_PRIOR", u"複合", u"万円", False, None, OTHER, lead=True),
        jrow(a, "T7-01", "T7_ROUND", u"既存", u"円", True, NAMED, NAMED, sign=1),
        jrow(a, "T7-02", "T7_ROUND", u"万だけ", u"万円", True, NAMED, PASS_, sign=-1),
        jrow(a, "T7-03", "T7_ROUND", u"複合", u"万円", True, NAMED, NAMED, sign=1),
        jrow(a, "T7-04", "T7_ROUND", u"複合", u"万円", False, None, OTHER, sign=-1),
        jrow(c, "T2-01", "T2_UNIT", u"既存", u"百万円", True, NAMED, NAMED, after=u"千円", reached=True),
        jrow(c, "T2-02", "T2_UNIT", u"万だけ", u"万円", True, NAMED, NAMED, after=u"円", reached=True),
        jrow(c, "T7-01", "T7_ROUND", u"既存", None, True, NAMED, NAMED, sign=1)]


def sample_per():
    ca = collections.OrderedDict([
        (u"token の数え", kinds_of(5, 1, 3, 4)), ("T5_COINCIDENT", t5_of(0, 3, 2, 1, 2, 7, 1)),
        ("T2_UNIT", t2_count(4, 2, 4, pop_of(linked=2, not_g=3, no_base=1), 6, sd(**{JT.LINKED: 2, JT.STATUS_NOT_G: 3, JT.STATUS_NO_BASE: 1}))),
        ("T6_PRIOR", t67_count(1, 0, 2, pop_of(linked=2, unlinked=1), sd(**{JT.LINKED: 2, JT.UNLINKED: 1}))),
        ("T7_ROUND", t67_count(1, 1, 2, pop_of(linked=3, unlinked=1), sd(**{JT.LINKED: 3, JT.UNLINKED: 1})))])
    cb = collections.OrderedDict([(u"token の数え", kinds_of(2, 0, 1, 0)), (u"注入しない", u"文に全角の数字がある(select は半角の文を前提にする)")])
    cc = collections.OrderedDict([
        (u"token の数え", kinds_of(2, 0, 1, 0)), ("T5_COINCIDENT", t5_of(2, 2, 2, 0, 1, 3, 0)),
        ("T2_UNIT", t2_count(2, 1, 0, pop_of(linked=2, no_base=1), 3, sd(**{JT.LINKED: 2, JT.STATUS_NO_BASE: 1}))),
        ("T6_PRIOR", t67_count(0, 0, 0, pop_of(), sd())),
        ("T7_ROUND", t67_count(1, 0, 0, pop_of(linked=1), sd(**{JT.LINKED: 1})))])
    return collections.OrderedDict([(u"DOC1_F1_m1", ca), (u"DOC2_F5_m2", cb), (u"DOC3_F1_m1", cc)])


def sample_inject():
    rows = sample_rows()
    per = sample_per()
    rec = sample_header()
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
    rec[u"型"] = collections.OrderedDict([(u"site", SITE_WORD_PIN), (u"土台", BASE_WORD_PIN)])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"], rec[JT.COMPARE_KEY] = (norm(x) for x in JT.inject_summaries(rows))
    rec[JT.BREAKDOWN_KEY] = norm(JT.breakdown(rows))
    rec[u"P29E に対応なしの行の数"] = norm(JT.unlinked_counts(rows))
    rec[JT.J_KEY] = norm(JT.j_columns(per, rows))
    rec[u"限界"] = JT.seal_limits(read(SEAL_REL)) + list(JT.EXTRA_LIMITS)
    rec[u"行"] = rows
    return norm(rec)


def sample_records():
    f = fixed_records()
    return collections.OrderedDict([("inject", sample_inject()), ("h", f["h"]), ("rb", f["rb"])])


def sample_j1(**ov):
    d = collections.OrderedDict([(INFO_J1[0], True), (INFO_J1[1], True), (INFO_J1[2], 0)])
    d.update(ov)
    return d


def sample_cols(**ov):
    u"""判定の関数の境界の試験用: ``j_columns`` と同じ形の欄(幅の真ん中の値)。ov = {"欄/キー/...": 値} で 1 つだけ替える。"""
    c = collections.OrderedDict([
        (u"J-2 作れる site(種類別)", collections.OrderedDict([
            ("T2_UNIT", collections.OrderedDict([(u"既存", 8030), (u"万だけ", 1820), (u"site にしない複合", 5400)])),
            ("T6_PRIOR", collections.OrderedDict([(u"既存", 61), (u"万だけ", 16), (u"複合", 272)])),
            ("T7_ROUND", collections.OrderedDict([(u"既存", 376), (u"万だけ", 243), (u"複合", 1223)]))])),
        (u"J-3 採った / うち土台 P30E が GROUNDED の行", collections.OrderedDict([
            ("T2_UNIT", collections.OrderedDict([(u"採った", 1900), (u"うち土台 P30E が GROUNDED の行", 1000)])),
            ("T6_PRIOR", collections.OrderedDict([(u"採った", 320), (u"うち土台 P30E が GROUNDED の行", 230)])),
            ("T7_ROUND", collections.OrderedDict([(u"採った", 1700), (u"うち土台 P30E が GROUNDED の行", 1100)]))])),
        (u"J-4 通した率(P30E)", collections.OrderedDict([("T2_UNIT", 0.3), ("T6_PRIOR", 5.0), ("T7_ROUND", 25.0)])),
        (u"J-5 T7_ROUND の通した率(P29E にも対応が付く行だけ)", collections.OrderedDict([("P29E", 20.0), ("P30E", 25.0), (u"差(pt)", 5.0), (u"行", 1000)])),
        (u"J-6 名指して原本の率(P30E。T7 は止めた行の中で)", collections.OrderedDict([("T2_UNIT", 70.0), ("T6_PRIOR", 80.0), ("T7_ROUND", 70.0)])),
        (u"J-7 P29E と P30E で判定が違う行(P29E に対応が付く行)", collections.OrderedDict([(u"違う行", 80), (u"うち T7", 72), (u"T7 の割合", 90.0)])),
        (u"J-8 T2_UNIT で通した行(P30E)", collections.OrderedDict([(u"通した行", 3), (u"うち届いた", 0)])),
        (u"J-9", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"先頭の位が減った行", 12)])),
        (u"J-10 T5 の site(注入しない)", collections.OrderedDict([(u"偽", 0), (u"真", 672), (u"真のうち相手の参照の単位が None か 円 でない site", 0)])),
        (u"届いた行(型別。参考)", collections.OrderedDict([("T2_UNIT", 1000), ("T6_PRIOR", 200), ("T7_ROUND", 1000)]))])
    for path, v in ov.items():
        keys = path.split(SEP)
        d = c
        for kk in keys[:-1]:
            d = d[kk]
        d[keys[-1]] = v
    return c


def sample_doc(R, seal):
    J = JT.build_J(R, seal, [])
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", JT.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start judge -->", JT.render_judge(J, seal), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"200 本の標本です。" + NOT_GATED, u""])


SEP = u"::"                                  # sample_cols の path の区切り(欄の名前に / が入るため)
KEY = {"J-2": u"J-2 作れる site(種類別)", "J-3": u"J-3 採った / うち土台 P30E が GROUNDED の行", "J-4": u"J-4 通した率(P30E)", "J-5": u"J-5 T7_ROUND の通した率(P29E にも対応が付く行だけ)",
       "J-6": u"J-6 名指して原本の率(P30E。T7 は止めた行の中で)", "J-7": u"J-7 P29E と P30E で判定が違う行(P29E に対応が付く行)", "J-8": u"J-8 T2_UNIT で通した行(P30E)",
       "J-9": u"J-9", "J-10": u"J-10 T5 の site(注入しない)"}


# ================================================================ (a) 封の字
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def test_a_2_a_changed_character_in_the_seal_turns_the_pin_red(self):
        rows = JT.seal_pred_rows(self.seal)
        for cid, old, new in (("J-1", "一致", "不一致"), ("J-2", "T2 7,900〜8,150", "T2 7,901〜8,150"), ("J-2", "/ 1,780〜1,860 /", "/ 1,780〜1,861 /"), ("J-2", "/ 5,300〜5,500、", "/ 5,300〜5,501、"),
                              ("J-2", "T6 55〜70", "T6 55〜71"), ("J-2", "/ 12〜20 /", "/ 12〜21 /"), ("J-2", "/ 250〜300、", "/ 250〜301、"),
                              ("J-2", "T7 360〜390", "T7 360〜391"), ("J-2", "/ 230〜260 /", "/ 230〜261 /"), ("J-2", "/ 1,150〜1,300", "/ 1,150〜1,301"),
                              ("J-3", "T2 1,700〜2,000", "T2 1,700〜2,001"), ("J-3", "/ 700〜1,300、", "/ 700〜1,301、"), ("J-3", "T6 280〜349", "T6 280〜350"), ("J-3", "/ 150〜300、", "/ 150〜301、"),
                              ("J-3", "T7 1,500〜1,900", "T7 1,500〜1,901"), ("J-3", "/ 800〜1,400", "/ 800〜1,401"),
                              ("J-4", "T2_UNIT 0.0〜1.0%", "T2_UNIT 0.0〜1.1%"), ("J-4", "T6_PRIOR 0.0〜12.0%", "T6_PRIOR 0.0〜12.1%"), ("J-4", "T7_ROUND 10.0〜40.0%", "T7_ROUND 10.1〜40.0%"),
                              ("J-5", "差 2.0 pt 以上", "差 2.1 pt 以上"), ("J-6", "T2 55〜90%", "T2 55〜91%"), ("J-6", "T6 55〜95%", "T6 56〜95%"), ("J-6", "50〜90%", "50〜91%"),
                              ("J-7", "10〜150 行", "10〜151 行"), ("J-7", "T7 が 80% 以上", "T7 が 81% 以上"), ("J-8", "0", "1"),
                              ("J-9", "0 / 0 / 0〜40", "1 / 0 / 0〜40"), ("J-9", "0 / 0 / 0〜40", "0 / 1 / 0〜40"), ("J-9", "0 / 0 / 0〜40", "0 / 0 / 0〜41"),
                              ("J-10", "0 / 600〜750 / 0", "1 / 600〜750 / 0"), ("J-10", "0 / 600〜750 / 0", "0 / 600〜751 / 0"), ("J-10", "0 / 600〜750 / 0", "0 / 600〜750 / 1")):
            self.assertIn(old, rows[cid][1], (cid, old))
            mutated = self.seal.replace("| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1]), "| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1].replace(old, new, 1)), 1)
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], bounds_problems(mutated), (cid, new))

    def test_a_3_the_thresholds_of_k1_to_k4_are_read_from_the_seal(self):
        b = JT.seal_bounds(self.seal)
        self.assertEqual((u"一致", {u"round-trip 不一致": 0, u"読み直し不一致": 0}, 1800.0, 0), (b["K-1"], dict(b["K-2"]), b["K-3"], b["K-4"]))
        for old, new in (("J-9 の round-trip 不一致 0・読み直し不一致 0", "J-9 の round-trip 不一致 1・読み直し不一致 0"), ("J-9 の round-trip 不一致 0・読み直し不一致 0", "J-9 の round-trip 不一致 0・読み直し不一致 1"),
                         ("和 ≥ 1,800", "和 ≥ 1,801"), ("J-8 が 0", "J-8 が 1")):
            self.assertIn(old, self.seal, old)
            self.assertNotEqual([], bounds_problems(self.seal.replace(old, new, 1)), new)


# ================================================================ (c) 判定
class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def J(self, j1=None, **ov):
        return JT.judge_from(j1 or sample_j1(), sample_cols(**ov), self.seal)

    def test_c_1_the_middle_of_every_range_is_a_hit_and_adoption_follows(self):
        J = self.J()
        for k, v in J[u"J"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        for k, v in J[u"K"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        self.assertTrue(J[u"採用"])

    def test_c_2_each_prediction_flips_at_the_seal_boundary(self):
        b = BOUNDS_PIN
        cases = []
        for t, d in b["J-2"].items():
            full = dict((x, u"%s_UNIT" % t if False else None) for x in d)
            tn = {"T2": "T2_UNIT", "T6": "T6_PRIOR", "T7": "T7_ROUND"}[t]
            for k, (lo, hi) in d.items():
                cases += [("J-2", u"%s::%s::%s" % (KEY["J-2"], tn, k), lo, lo - 1), ("J-2", u"%s::%s::%s" % (KEY["J-2"], tn, k), hi, hi + 1)]
        for t, d in b["J-3"].items():
            tn = {"T2": "T2_UNIT", "T6": "T6_PRIOR", "T7": "T7_ROUND"}[t]
            for k, (lo, hi) in d.items():
                cases += [("J-3", u"%s::%s::%s" % (KEY["J-3"], tn, k), lo, lo - 1), ("J-3", u"%s::%s::%s" % (KEY["J-3"], tn, k), hi, hi + 1)]
        for t, (lo, hi) in b["J-4"].items():
            cases += [("J-4", u"%s::%s" % (KEY["J-4"], t), lo, lo - 0.1), ("J-4", u"%s::%s" % (KEY["J-4"], t), hi, hi + 0.1)]
        for t, (lo, hi) in b["J-6"].items():
            cases += [("J-6", u"%s::%s" % (KEY["J-6"], t), lo, lo - 0.1), ("J-6", u"%s::%s" % (KEY["J-6"], t), hi, hi + 0.1)]
        lo, hi = b["J-7"][u"違う行"]
        cases += [("J-7", KEY["J-7"] + u"::違う行", lo, lo - 1), ("J-7", KEY["J-7"] + u"::違う行", hi, hi + 1),
                  ("J-7", KEY["J-7"] + u"::T7 の割合", b["J-7"][u"T7 の割合"], b["J-7"][u"T7 の割合"] - 0.1)]
        cases += [("J-8", KEY["J-8"] + u"::うち届いた", 0, 1)]
        cases += [("J-9", KEY["J-9"] + u"::round-trip 不一致", 0, 1), ("J-9", KEY["J-9"] + u"::読み直し不一致", 0, 1),
                  ("J-9", KEY["J-9"] + u"::先頭の位が減った行", 0, -1), ("J-9", KEY["J-9"] + u"::先頭の位が減った行", 40, 41)]
        lo, hi = b["J-10"][u"真"]
        cases += [("J-10", KEY["J-10"] + u"::偽", 0, 1), ("J-10", KEY["J-10"] + u"::真", lo, lo - 1), ("J-10", KEY["J-10"] + u"::真", hi, hi + 1),
                  ("J-10", KEY["J-10"] + u"::真のうち相手の参照の単位が None か 円 でない site", 0, 1)]
        for cid, path, inside, outside in cases:
            self.assertEqual(HIT, self.J(**{path: inside})[u"J"][cid][u"判定"], (path, inside))
            self.assertEqual(MISS, self.J(**{path: outside})[u"J"][cid][u"判定"], (path, outside))

    def test_c_2b_j2_needs_every_cell_and_j5_is_the_difference_in_points(self):
        c = sample_cols()
        del c[KEY["J-2"]]["T2_UNIT"][u"site にしない複合"]
        self.assertEqual(MISS, JT.judge_from(sample_j1(), c, self.seal)[u"J"]["J-2"][u"判定"])           # 欄が欠けたら当たりにしない
        base = {KEY["J-5"] + u"::差(pt)": 2.0}
        self.assertEqual(HIT, self.J(**base)[u"J"]["J-5"][u"判定"])
        self.assertEqual(MISS, self.J(**{KEY["J-5"] + u"::差(pt)": 1.9})[u"J"]["J-5"][u"判定"])
        self.assertEqual(MISS, self.J(**{KEY["J-5"] + u"::差(pt)": None})[u"J"]["J-5"][u"判定"])
        self.assertEqual(MISS, self.J(**{KEY["J-7"] + u"::T7 の割合": None})[u"J"]["J-7"][u"判定"])

    def test_c_2c_j1_needs_the_three_agreements(self):
        for ov in ({INFO_J1[0]: False}, {INFO_J1[1]: False}, {INFO_J1[2]: 1}, {INFO_J1[2]: None}):
            J = self.J(j1=sample_j1(**ov))
            self.assertEqual(MISS, J[u"J"]["J-1"][u"判定"], ov)
            self.assertEqual(MISS, J[u"K"]["K-1"][u"判定"], ov)
            self.assertFalse(J[u"採用"])

    def test_c_3_the_adoption_follows_k1_to_k4(self):
        self.assertFalse(self.J(j1=sample_j1(**{INFO_J1[0]: False}))[u"採用"])                                                              # K-1
        for k, path in (("round-trip", KEY["J-9"] + u"::round-trip 不一致"), ("読み直し", KEY["J-9"] + u"::読み直し不一致")):               # K-2
            J = self.J(**{path: 1})
            self.assertEqual(MISS, J[u"K"]["K-2"][u"判定"], k)
            self.assertFalse(J[u"採用"])
        # K-3: 行の和 = 1,800 は当たり
        three = lambda a, b, c: {KEY["J-3"] + u"::T2_UNIT::うち土台 P30E が GROUNDED の行": a, KEY["J-3"] + u"::T6_PRIOR::うち土台 P30E が GROUNDED の行": b, KEY["J-3"] + u"::T7_ROUND::うち土台 P30E が GROUNDED の行": c}
        self.assertEqual(HIT, self.J(**three(1000, 200, 600))[u"K"]["K-3"][u"判定"])
        J = self.J(**three(1000, 200, 599))
        self.assertEqual(MISS, J[u"K"]["K-3"][u"判定"])
        self.assertFalse(J[u"採用"])
        J = self.J(**{KEY["J-8"] + u"::うち届いた": 1})                                                                                      # K-4
        self.assertEqual(MISS, J[u"K"]["K-4"][u"判定"])
        self.assertFalse(J[u"採用"])

    def test_c_4_k3_uses_the_seal_k_threshold_not_the_prediction_ranges(self):
        J = self.J(**{KEY["J-3"] + u"::T2_UNIT::うち土台 P30E が GROUNDED の行": 650, KEY["J-3"] + u"::T6_PRIOR::うち土台 P30E が GROUNDED の行": 300, KEY["J-3"] + u"::T7_ROUND::うち土台 P30E が GROUNDED の行": 850})
        self.assertEqual(MISS, J[u"J"]["J-3"][u"判定"])                                  # J-3 の幅(T2 700〜1,300)の外
        self.assertEqual(HIT, J[u"K"]["K-3"][u"判定"])                                    # 和 1,800 は K-3 を満たす
        J = self.J(**{KEY["J-4"] + u"::T7_ROUND": 90.0})                                 # J-4 の外でも K は J-4 を見ない(採用は K だけで決まる)
        self.assertEqual(MISS, J[u"J"]["J-4"][u"判定"])
        self.assertTrue(J[u"採用"])
        J = self.J(**{KEY["J-4"] + u"::T7_ROUND": 90.0, KEY["J-5"] + u"::差(pt)": 0.0})
        self.assertTrue(J[u"採用"])

    def test_c_5_the_judgment_moves_with_the_records(self):
        base = self.J()
        mutated_seal = self.seal.replace("T2 7,900〜8,150", "T2 7,900〜8,029", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertEqual(MISS, JT.judge_from(sample_j1(), sample_cols(), mutated_seal)[u"J"]["J-2"][u"判定"])
        self.assertNotEqual(norm(base), norm(self.J(**{KEY["J-7"] + u"::違う行": 4})))

    def test_c_6_a_broken_record_is_red_not_an_exception(self):
        R = norm(sample_records())
        self.assertEqual([], judge_problems(R, self.seal))
        del R["inject"][u"本ごとの数え"]
        self.assertNotEqual([], judge_problems(R, self.seal))
        R2 = norm(sample_records())
        R2["h"].pop(u"lib の指紋")
        self.assertEqual(MISS, JT.build_J(R2, self.seal, [])[u"J"]["J-1"][u"判定"])
        R3 = norm(sample_records())
        R3["rb"].pop(u"engine の指紋")
        self.assertEqual(MISS, JT.build_J(R3, self.seal, [])[u"J"]["J-1"][u"判定"])

    def test_c_7_the_judgment_follows_the_columns_counted_from_the_rows_not_the_recorded_columns(self):
        R = norm(sample_records())
        J = JT.build_J(R, self.seal, [])
        R["inject"][JT.J_KEY][KEY["J-9"]][u"round-trip 不一致"] = 7                          # 記録の J の欄だけ変えても判定は動かない(行から数え直す)
        self.assertEqual(norm(J), norm(JT.build_J(R, self.seal, [])))
        R["inject"][u"行"][0][u"round-trip"] = False                                       # 行を変えると J-9 が動く
        self.assertEqual(MISS, JT.build_J(R, self.seal, [])[u"J"]["J-9"][u"判定"])
        self.assertEqual(MISS, JT.build_J(R, self.seal, [])[u"K"]["K-2"][u"判定"])

    def test_c_8_the_j1_inputs_come_from_the_records_and_the_numstat(self):
        R = norm(sample_records())
        ok = JT.j1_value(R["inject"], R["h"], R["rb"], [])
        self.assertEqual((True, True, 0), tuple(ok.values()))
        R2 = copy.deepcopy(R)
        R2["inject"][u"lib の指紋"][LIB_RELS[0]] = "0" * 64
        self.assertFalse(JT.j1_value(R2["inject"], R2["h"], R2["rb"], [])[INFO_J1[0]])
        R3 = copy.deepcopy(R)
        R3["inject"][u"engine の指紋"]["core_py_sha256"] = "0" * 64
        self.assertFalse(JT.j1_value(R3["inject"], R3["h"], R3["rb"], [])[INFO_J1[1]])
        R4 = copy.deepcopy(R)
        R4["inject"][u"engine の指紋"]["git_commit"] = "9" * 40                                # git_commit は比べない(記録ごとに違う)
        self.assertTrue(JT.j1_value(R4["inject"], R4["h"], R4["rb"], [])[INFO_J1[1]])
        self.assertEqual(1, JT.j1_value(R["inject"], R["h"], R["rb"], ["1\t0\tmeasure/inject.py"])[INFO_J1[2]])
        self.assertIsNone(JT.j1_value(R["inject"], R["h"], R["rb"], None)[INFO_J1[2]])
        R5 = copy.deepcopy(R)
        R5["inject"].pop(u"lib の指紋")
        self.assertFalse(JT.j1_value(R5["inject"], R5["h"], R5["rb"], [])[INFO_J1[0]])
        seal = read(SEAL_REL)
        self.assertEqual(MISS, JT.build_J(R, seal, None)[u"J"]["J-1"][u"判定"])                    # git が読めなかったら外れ(作業木の答えで代えない)
        self.assertEqual(HIT, JT.build_J(R, seal, [])[u"J"]["J-1"][u"判定"])
        calls = []
        with Patch() as pt:
            pt.set(JT, "git_numstat_since_seal", lambda root=ROOT: calls.append(1) or ["1\t0\tmeasure/inject.py"])
            self.assertEqual(MISS, JT.build_J(R, seal)[u"J"]["J-1"][u"判定"])                       # 省略したら git に聞く
        self.assertEqual([1], calls)

    def test_c_9_the_numstat_since_the_seal_is_empty_in_the_real_tree_and_not_in_a_changed_one(self):
        # 2026-11-06(T5Y): 封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §2-1 が宣言した遷移(仕掛けの 2 file に挿入だけ)は実物の木の numstat から外す(SGR.t5y_declared_numstat)
        self.assertEqual([], [x for x in JT.git_numstat_since_seal(ROOT) if not SG.SGR.t5y_declared_numstat(x)])
        r = PR.Repo()
        r.put("measure/inject.py")
        r.put("measure/lib/sites.py")
        r.put("x.md")
        sh = r.commit("measure/inject.py", "measure/lib/sites.py", "x.md")
        base = os.path.join(r.d, "audit-core")
        old = JT.SEAL_COMMIT
        try:
            JT.SEAL_COMMIT = sh[:7]
            self.assertEqual([], JT.git_numstat_since_seal(base))
            with open(os.path.join(base, "measure/lib/sites.py"), "a", encoding="utf-8") as fh:
                fh.write("x = 1\n")
            self.assertEqual(1, len(JT.git_numstat_since_seal(base)))
            JT.SEAL_COMMIT = "0000000"
            self.assertIsNone(JT.git_numstat_since_seal(base))                             # 読めなければ None(当たりにしない)
        finally:
            JT.SEAL_COMMIT = old


# ================================================================ (b)(g) 小さい標本の記録と文書の変異
class SampleFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.R = sample_records()

    def test_g_0_the_sample_is_green(self):
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=False))
        doc = sample_doc(self.R, self.seal)
        self.assertEqual([], doc_problems(doc, self.R, self.seal))

    def test_g_1_the_sample_exercises_a_skipped_book_unlinked_rows_and_every_column(self):
        inj = self.R["inject"]
        self.assertIn(u"注入しない", inj[u"本ごとの数え"][u"DOC2_F5_m2"])
        self.assertEqual({u"全体": 2, "T2_UNIT": 0, "T6_PRIOR": 1, "T7_ROUND": 1}, dict(inj[u"P29E に対応なしの行の数"]))
        cols = inj[JT.J_KEY]
        self.assertEqual(3, cols[KEY["J-7"]][u"違う行"])
        self.assertEqual(1, cols[KEY["J-9"]][u"先頭の位が減った行"])
        self.assertEqual(1, cols[KEY["J-8"]][u"通した行"])

    def _red(self, mutate, **kw):
        R = copy.deepcopy(self.R)
        mutate(R)
        self.assertNotEqual([], record_problems(R, full=False), kw)

    def test_g_2_one_number_in_a_record_turns_it_red(self):
        inj = lambda f: (lambda R: f(R["inject"]))
        self._red(inj(lambda r: r[u"行"][0]["P30E"].__setitem__(u"結果", TUNE.LABEL_PASS)))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"round-trip", u"はい")))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"単位", u"")))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"単位", None)))                                      # T2 は単位が要る
        self._red(inj(lambda r: r[u"行"][5].__setitem__(u"単位", u"")))                                       # T7 の単位は語か None
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"形", u"複合")))                                     # T2_UNIT に複合
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"単位の後", r[u"行"][0][u"単位"])))                    # 後の単位が元と同じ
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"符号", 1)))
        self._red(inj(lambda r: r[u"行"][5].__setitem__(u"符号", 0)))
        self._red(inj(lambda r: r[u"行"][5].__setitem__(u"単位の後", u"円")))
        self._red(inj(lambda r: r[u"行"][2].__setitem__(u"符号", 1)))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"先頭の位が減った", True)))                           # T2 の行は減らない
        self._red(inj(lambda r: r[u"行"][2].__setitem__(u"先頭の位が減った", True)))                           # 既存の行は減らない
        self._red(inj(lambda r: r[u"行"][3].__setitem__(u"届いた", u"はい")))
        self._red(inj(lambda r: r[u"行"][0].__setitem__("id", r[u"行"][1]["id"])))
        self._red(inj(lambda r: r[u"集計"]["T2_UNIT"]["P30E"][u"全体"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r[JT.BREAKDOWN_KEY]["T7_ROUND"][u"複合"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r[u"型"].__setitem__(u"土台", u"無改変の文で P29E が GROUNDED の claim")))
        self._red(inj(lambda r: r[u"型"].__setitem__(u"site", u"全部の site")))
        self._red(inj(lambda r: r[u"限界"].pop()))
        self._red(inj(lambda r: r[u"限界"].__setitem__(0, u"別の限界")))
        self._red(inj(lambda r: r.pop(JT.COMPARE_KEY)))
        self._red(inj(lambda r: r[JT.COMPARE_KEY]["T7_ROUND"]["P29E"][u"全体"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r.pop(JT.BREAKDOWN_KEY)))

    def test_g_2b_every_column_of_the_j_record_is_recounted_from_the_rows_and_the_counts(self):
        u"""J の欄の全部(J-2〜J-10 と参考の欄)を 0 に固定すると赤。記録の欄を直しても行・数えと食い違えば赤。"""
        cols = self.R["inject"][JT.J_KEY]

        def leaves(d, path=()):
            for k, v in d.items():
                if isinstance(v, dict):
                    for x in leaves(v, path + (k,)):
                        yield x
                else:
                    yield path + (k,), v
        n = 0
        for path, v in leaves(cols):
            R = copy.deepcopy(self.R)
            d = R["inject"][JT.J_KEY]
            for k in path[:-1]:
                d = d[k]
            d[path[-1]] = 0 if v != 0 else 1                       # 0 に固定(元が 0 なら 1)
            self.assertNotEqual([], record_problems(R, full=False), path)
            n += 1
        self.assertGreaterEqual(n, 30)
        R = copy.deepcopy(self.R)
        R["inject"].pop(JT.J_KEY)
        self.assertNotEqual([], record_problems(R, full=False))

    def test_g_2c_the_script_columns_function_zeroed_in_one_column_turns_the_record_red(self):
        u"""script の ``j_columns`` が欄を 0 に固定する変異(記録は正しい欄で作ってある)で赤。"""
        real = JT.j_columns
        paths = [(KEY["J-2"], "T2_UNIT", u"既存"), (KEY["J-3"], "T7_ROUND", u"採った"), (KEY["J-4"], "T7_ROUND"), (KEY["J-5"], "P30E"), (KEY["J-6"], "T2_UNIT"), (KEY["J-7"], u"違う行"),
                 (KEY["J-8"], u"通した行"), (KEY["J-9"], u"先頭の位が減った行"), (KEY["J-10"], u"真"), (u"届いた行(型別。参考)", "T2_UNIT"), (KEY["J-3"], "T2_UNIT", u"うち土台 P30E が GROUNDED の行")]
        for path in paths:
            def fixed(per, rows, path=path):
                c = real(per, rows)
                d = c
                for k in path[:-1]:
                    d = d[k]
                d[path[-1]] = 0
                return c
            with Patch() as pt:
                pt.set(JT, "j_columns", fixed)
                self.assertNotEqual([], record_problems(copy.deepcopy(self.R), full=False), path)
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=False))

    def test_g_2d_a_row_field_changes_exactly_the_columns_it_feeds(self):
        per, rows = self.R["inject"][u"本ごとの数え"], self.R["inject"][u"行"]
        base = norm(JT.j_columns(per, rows))
        self.assertEqual(
            {KEY["J-2"]: {"T2_UNIT": {u"既存": 6, u"万だけ": 3, u"site にしない複合": 4}, "T6_PRIOR": {u"既存": 1, u"万だけ": 0, u"複合": 2}, "T7_ROUND": {u"既存": 2, u"万だけ": 1, u"複合": 2}},
             KEY["J-3"]: {"T2_UNIT": {u"採った": 9, u"うち土台 P30E が GROUNDED の行": 4}, "T6_PRIOR": {u"採った": 3, u"うち土台 P30E が GROUNDED の行": 3}, "T7_ROUND": {u"採った": 5, u"うち土台 P30E が GROUNDED の行": 5}},
             KEY["J-4"]: {"T2_UNIT": 25.0, "T6_PRIOR": 0.0, "T7_ROUND": 20.0},
             KEY["J-5"]: {"P29E": 0.0, "P30E": 25.0, u"差(pt)": 25.0, u"行": 4},
             KEY["J-6"]: {"T2_UNIT": 75.0, "T6_PRIOR": 66.7, "T7_ROUND": 75.0},
             KEY["J-7"]: {u"違う行": 3, u"うち T7": 1, u"T7 の割合": 33.3},
             KEY["J-8"]: {u"通した行": 1, u"うち届いた": 0},
             KEY["J-9"]: {u"round-trip 不一致": 0, u"読み直し不一致": 0, u"先頭の位が減った行": 1},
             KEY["J-10"]: {u"偽": 2, u"真": 5, u"真のうち相手の参照の単位が None か 円 でない site": 1},
             u"届いた行(型別。参考)": {"T2_UNIT": 3, "T6_PRIOR": 0, "T7_ROUND": 0}}, base)
        ref = u"届いた行(型別。参考)"
        for idx, key, val, where, feeds in ((0, u"round-trip", False, (KEY["J-9"], u"round-trip 不一致"), [KEY["J-9"]]), (0, u"読み直し", False, (KEY["J-9"], u"読み直し不一致"), [KEY["J-9"]]),
                                            (3, u"先頭の位が減った", True, (KEY["J-9"], u"先頭の位が減った行"), [KEY["J-9"]]), (0, u"届いた", False, (ref, "T2_UNIT"), [ref]),
                                            (1, u"届いた", True, (KEY["J-8"], u"うち届いた"), [KEY["J-8"], ref])):
            r2 = copy.deepcopy(rows)
            r2[idx][key] = val
            c2 = norm(JT.j_columns(per, r2))
            self.assertNotEqual(base[where[0]][where[1]], c2[where[0]][where[1]], (key, where))
            changed = [k for k in base if base[k] != c2[k]]
            self.assertEqual(feeds, changed, (key, changed))                                                      # 動くのはその欄が餌にする欄だけ
        r2 = copy.deepcopy(rows)
        r2[1]["P30E"] = cell(*NAMED)                                                                              # T2 の通した行が名指しに
        self.assertEqual(0, JT.j_columns(per, r2)[KEY["J-8"]][u"通した行"])
        r2 = copy.deepcopy(rows)
        r2[6]["P30E"] = cell(*NAMED)                                                                              # T7 の通した行が名指しに: J-4 と J-5 と J-7 が動く
        c2 = JT.j_columns(per, r2)
        self.assertEqual((0.0, 0.0, 0.0), (c2[KEY["J-4"]]["T7_ROUND"], c2[KEY["J-5"]]["P30E"], c2[KEY["J-5"]][u"差(pt)"]))
        self.assertEqual(2, c2[KEY["J-7"]][u"違う行"])                                                              # 3 → 2(T7-02 は P29E も P30E も名指しで同じになった)

    def test_g_2e_a_consistently_edited_count_still_breaks_the_invariants(self):
        u"""本ごとの数えを直してから J の欄も作り直しても(欄との食い違いでは見つからない)、数えの欄の間の関係と行との関係で赤になる。"""
        def reh(R):
            R["inject"][JT.J_KEY] = norm(JT.j_columns(R["inject"][u"本ごとの数え"], R["inject"][u"行"]))
        for mutate in (lambda c: c["T2_UNIT"].__setitem__(u"採った", 5), lambda c: c["T2_UNIT"].__setitem__(u"select の作れる site", 9), lambda c: c["T2_UNIT"][u"作れる site"].__setitem__(u"既存", 9),
                       lambda c: c["T2_UNIT"][u"採った の状態"].__setitem__(JT.LINKED, 9), lambda c: c["T2_UNIT"].__setitem__(u"site にしなかった複合", 99),
                       lambda c: c["T6_PRIOR"].__setitem__(u"採った", 2), lambda c: c["T6_PRIOR"].__setitem__(u"土台 P30E が GROUNDED の site", 9),
                       lambda c: c["T6_PRIOR"].__setitem__(u"cap を基準で絞る前に掛けた数", 9), lambda c: c["T6_PRIOR"][u"作れる site"].__setitem__(u"複合", 9),
                       lambda c: c["T6_PRIOR"][u"作れる site の状態"].__setitem__(JT.LINKED, 9), lambda c: c["T7_ROUND"].__setitem__(u"採った", 9),
                       lambda c: c["T7_ROUND"][u"採った の状態"].__setitem__(JT.STATUS_NOT_G, 1), lambda c: c["T7_ROUND"][u"作れる site"].__setitem__(u"万だけ", 9),
                       lambda c: c[u"token の数え"][u"全部"].__setitem__(u"複合", 1), lambda c: c[u"token の数え"][u"うち is_quantity 真"].__setitem__(u"既存", 99),
                       lambda c: c["T5_COINCIDENT"].__setitem__(u"真", 9), lambda c: c["T5_COINCIDENT"][u"others の単位の内訳"].__setitem__(u"その他", 0)):
            R = copy.deepcopy(self.R)
            mutate(R["inject"][u"本ごとの数え"][u"DOC1_F1_m1"])
            try:
                reh(R)
            except Exception:                                   # noqa: BLE001  J の欄を作れない形も赤(record_problems が例外を問題に数える)
                pass
            self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        R["inject"][u"本ごとの数え"][u"DOC2_F5_m2"].pop(u"注入しない")                               # 注入しない本に数えを置かずに印だけ消した
        self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        reh(R)
        self.assertEqual([], record_problems(R, full=False))

    def test_g_2f_cap_and_linked_counts_are_checked_on_their_own(self):
        R = copy.deepcopy(self.R)
        row = R["inject"][u"行"][0]
        R["inject"][u"行"] = [dict(row, id=u"DOC1_F1_m1-T2-%02d" % (i + 1)) for i in range(RUN.INJECT_CAP + 1)]
        R["inject"][u"注入の行の数"] = len(R["inject"][u"行"])
        with Patch() as pt:
            pt.set(RUN, "PROFILES", INJECT_PROFILES)
            R["inject"][u"集計"], R["inject"][JT.COMPARE_KEY] = (norm(x) for x in JT.inject_summaries(R["inject"][u"行"]))
        R["inject"][u"P29E に対応なしの行の数"] = collections.OrderedDict([(u"全体", 0), ("T2_UNIT", 0), ("T6_PRIOR", 0), ("T7_ROUND", 0)])
        self.assertTrue(any(u"上限" in x for x in inject_problems(R["inject"], full=False)), inject_problems(R["inject"], full=False))
        R2 = copy.deepcopy(self.R)
        R2["inject"][u"行"][0][LINK_KEY] = False                               # 対応ありの行を対応なしに(P29E の欄が対応なしでない)
        self.assertNotEqual([], record_problems(R2, full=False))

    def test_g_2g_the_full_only_checks_are_exercised_on_the_sample(self):
        u"""full=True だけが見る検査(本番の記録でだけ走る)を、標本の記録で。標本は 200 本でなく範囲も標本。"""
        R = copy.deepcopy(self.R)
        self.assertTrue(any(u"200 本" in x for x in inject_problems(R["inject"], full=True)))
        self.assertTrue(any(u"範囲" in x for x in header_problems(R["inject"], True)))
        self.assertFalse(any(u"範囲" in x for x in header_problems(R["inject"], False)))

    def test_g_3_a_forbidden_key_or_a_key_or_a_company_name_turns_it_red(self):
        for key in (u"span", u"value", u"recomputed", u"文", u"sentence", u"数", u"理由"):
            self._red(lambda R, key=key: R["inject"][u"行"][0].__setitem__(key, 1))
        self._red(lambda R: R["inject"].__setitem__(u"メモ", u"株式会社テスト"))
        self._red(lambda R: R["inject"].__setitem__(u"メモ", u"sk-" + u"a" * 20))
        self._red(lambda R: R["inject"].__setitem__(u"key_leaks", [u"鍵の形"]))

    def test_g_4_one_character_of_the_fingerprints_or_the_script_sha_turns_it_red(self):
        for name in (u"この script の sha256", u"nscan script の sha256", u"rmix script の sha256", u"numfix script の sha256", u"前の便の run script の sha256", u"生成の script の sha256",
                     u"H の記録の sha256", u"RB の記録の sha256"):
            if name in self.R["inject"]:
                self._red(lambda R, name=name: R["inject"].__setitem__(name, "e" * 64))
            self._red(lambda R, name=name: R["inject"].pop(name, None) or R["inject"].__setitem__(u"x", 1))
        fp = lambda R: R["inject"][u"engine の指紋"]
        self._red(lambda R: fp(R).__setitem__("adapter_xbrl_py_sha256", fp(R)["adapter_xbrl_py_sha256"][:-1] + ("0" if fp(R)["adapter_xbrl_py_sha256"][-1] != "0" else "1")))
        self._red(lambda R: fp(R).__setitem__("core_py_sha256", "f" * 64))
        self._red(lambda R: R["inject"].__setitem__(u"封の commit", u"0000000"))
        self._red(lambda R: R["inject"][u"lib の指紋"].__setitem__(LIB_RELS[0], "e" * 64))
        self._red(lambda R: R["inject"][u"lib の指紋"].__setitem__(LIB_RELS[1], "e" * 64))
        self._red(lambda R: R["inject"][u"生成の記録の sha256"].__setitem__("aiforms", "e" * 64))
        self._red(lambda R: R["inject"].__setitem__(u"profile", [u"P28E", u"P29E"]))

    def test_g_4b_the_switch_record_turns_red_when_the_wiring_or_the_values_are_wrong(self):
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"配線の問題", [u"N がちがう"]))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"inject の中の値", False))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"出たあとの値", True))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"名前", WRONG_FLAG))

    def test_g_5_a_changed_cache_turns_it_red(self):
        self._red(lambda R: R["inject"][u"cache の前後"].__setitem__(u"変化なし", False))
        self._red(lambda R: R["inject"][u"cache の前後"][u"後"]["edinet"].__setitem__(u"件数", 4))

    def test_g_6_the_document_follows_the_records_and_the_seal(self):
        doc = sample_doc(self.R, self.seal)
        lines = doc.split(u"\n")
        i = lines.index(u"<!-- 門:start pred -->") + 3                  # 表の 1 行目(J-1)
        for col_char in (u"J", u"一", u"当"):
            mutated = lines[:]
            self.assertIn(col_char, mutated[i])
            j = mutated[i].index(col_char)
            mutated[i] = mutated[i][:j] + u"9" + mutated[i][j + 1:]
            self.assertNotEqual([], doc_problems(u"\n".join(mutated), self.R, self.seal), col_char)
        k = lines.index(u"<!-- 門:start judge -->") + 3
        mutated = lines[:]
        mutated[k] = mutated[k].replace(u"K-1", u"K-9", 1)
        self.assertNotEqual([], doc_problems(u"\n".join(mutated), self.R, self.seal))
        R2 = copy.deepcopy(self.R)
        R2["inject"][u"行"][0][u"round-trip"] = False
        self.assertNotEqual([], doc_problems(doc, R2, self.seal))
        mutated_seal = self.seal.replace("T2 7,900〜8,150", "T2 7,900〜8,151", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertNotEqual([], doc_problems(doc, self.R, mutated_seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"門:start judge", u"門:start other"), self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"<!-- 門:start judge -->", u"<!-- 門:start judge2 -->", 1), self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc, self.R, self.seal, numstat=["1\t0\tmeasure/inject.py"]))      # J-1 の行が変わる

    def test_g_7_forbidden_words_docids_and_ungated_numbers_turn_the_document_red(self):
        doc = sample_doc(self.R, self.seal)
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(doc + u"\n" + w + u"。\n", self.R, self.seal), w)
        self.assertNotEqual([], doc_problems(doc + u"\nS100" + u"ABCD の文。\n", self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n新しい token は 1234 でした。\n", self.R, self.seal))
        self.assertEqual([], doc_problems(doc + u"\n新しい token は 1234 でした。" + NOT_GATED + u"\n", self.R, self.seal))

    def test_g_8_the_judge_table_ends_with_the_adoption_line(self):
        J = JT.build_J(self.R, self.seal, [])
        t = JT.render_judge(J, self.seal).split(u"\n")
        self.assertEqual(u"採用の判定(K-1〜K-4 を全部満たす): **%s**。最後に決めるのは人間。" % (u"採用" if J[u"採用"] else u"見送り"), t[-1])
        J2 = JT.build_J(self.R, self.seal, ["1\t0\tmeasure/inject.py"])
        self.assertFalse(J2[u"採用"])
        self.assertIn(u"**見送り**", JT.render_judge(J2, self.seal))
        self.assertEqual(u"| # | 欄 | 予測 | 測った値 | 判定 |", JT.render_pred(J, self.seal).split(u"\n")[0])


WRONG_FLAG = "compound_yen_2026_11_05"


# ================================================================ (w) 手順(script の関数を小さい入力で通す。zip・判定は偽。lib は本物。通信なし)
TEXT_P = u"売上高は12億3,456万円でした。粗利益は1,234百万円でした。費用は5,000千円でした。"
REFS_P = [{"key": "jppfs:NetSales@CurrentYearDuration", "value": 1234560000.0, "unit": u"円", "label": u"売上高"},
          {"key": "jppfs:NetSales@Prior1YearDuration", "value": 970000000.0, "unit": u"円", "label": u"売上高"},
          {"key": "jppfs:GrossProfit@CurrentYearDuration", "value": 1234000000.0, "unit": u"円", "label": u"粗利益"},
          {"key": "jppfs:Cost@CurrentYearDuration", "value": 5000000.0, "unit": u"円", "label": u"費用"}]


def fake_verify_for(text0):
    u"""無改変の文の数は GROUNDED、注入した文で増えた数(字が元の文に無い claim)は VALUE_MISMATCH。名指しは元の文の先頭の pointer と同じ。lib の ``N.scan`` で読む。"""
    def verify(zb, p, t):
        claims = []
        for i, tok in enumerate(N.scan(t)):
            if tok.unit is None:
                continue
            span = t[tok.start:tok.unit_end]
            claims.append({"id": "N%03d" % (i + 1), "kind": "num", "value": tok.value, "unit": tok.unit, "span": span, "state": G if span in text0 else V_,
                           "pointers": ["ptr"], "recomputed": 1.0, "reason": None})
        return {"claims": claims}
    return verify


def run_procedure(text=TEXT_P, refs=REFS_P, patches=(), seed=u"sd", key=u"bk"):
    with Patch() as pt, JT.yen_scan_on():
        pt.set(RUN, "PROFILES", INJECT_PROFILES)
        for mod, name, v in patches:
            pt.set(mod, name, v)
        return JT.inject_text_j(b"zip", text, refs, seed, key, verify=fake_verify_for(text))


class ProcedureTest(unittest.TestCase):
    def test_w_1_each_type_builds_rows_from_its_own_site_population(self):
        rows, c = run_procedure()
        by = collections.defaultdict(list)
        for r in rows:
            by[r[u"型"]].append(r)
        self.assertEqual([], sorted(set(k for r in rows for k in RUN.walk_keys(r) if k in FORBIDDEN_KEYS)))           # 行に repo へ入れない欄を持たない
        self.assertEqual({u"既存": 2, u"万だけ": 0}, dict(c["T2_UNIT"][u"作れる site"]))
        self.assertEqual(1, c["T2_UNIT"][u"site にしなかった複合"])                                   # 12億3,456万円 は T2 の site にしない
        self.assertEqual(2, len(by["T2_UNIT"]))
        self.assertEqual([u"既存", u"既存"], [r[u"形"] for r in by["T2_UNIT"]])
        self.assertEqual({u"既存": 0, u"万だけ": 0, u"複合": 1}, dict(c["T6_PRIOR"][u"作れる site"]))           # 複合は写し
        self.assertEqual([u"複合"], [r[u"形"] for r in by["T6_PRIOR"]])
        self.assertEqual({u"既存": 2, u"万だけ": 0, u"複合": 1}, dict(c["T7_ROUND"][u"作れる site"]))           # 既存は仕掛けの経路・複合は写し
        self.assertEqual(sorted([u"既存", u"既存", u"複合"]), sorted(r[u"形"] for r in by["T7_ROUND"]))
        for t in ("T6_PRIOR", "T7_ROUND"):
            self.assertEqual(c[t][u"採った"], len(by[t]))
        self.assertEqual(3, c["T7_ROUND"][u"採った"])
        self.assertEqual({JT.LINKED: 3}, dict(c["T7_ROUND"][u"採った の状態"]))

    def test_w_2_t2_rows_look_up_the_injected_claim_by_the_unit_after(self):
        rows, _c = run_procedure()
        t2 = [r for r in rows if r[u"型"] == "T2_UNIT"]
        self.assertEqual(2, len(t2))
        for r in t2:
            self.assertNotEqual(r[u"単位"], r[u"単位の後"])
            self.assertTrue(r["P30E"][u"対応"], r)                       # 注入後の claim が後の単位で引ける
            self.assertTrue(r["P29E"][u"対応"], r)
            self.assertTrue(r[u"読み直し"] and r[u"round-trip"], r)
            self.assertTrue(r[u"届いた"], r)                             # 元の数の字 + 後の単位が注入後の claim の span に在る
            self.assertEqual(TUNE.LABEL_NAMED_ORIGINAL, r["P30E"][u"結果"])

    def test_w_3_t6_and_t7_compound_rows_are_written_by_the_copy_and_read_back(self):
        rows, _c = run_procedure()
        t6 = [r for r in rows if r[u"型"] == "T6_PRIOR"]
        t7 = [r for r in rows if r[u"型"] == "T7_ROUND"]
        self.assertEqual([None], [r[u"単位の後"] for r in t6])
        self.assertTrue(all(r[u"読み直し"] and r[u"round-trip"] and r["P30E"][u"対応"] and r[u"届いた"] for r in t6 + t7), (t6, t7))
        self.assertEqual({1, -1}, set([1, -1]) & set(r[u"符号"] for r in t7) | {1, -1})
        self.assertTrue(all(r[u"符号"] in (1, -1) for r in t7))
        self.assertTrue(all(r[u"単位の後"] is None for r in t7))
        self.assertFalse(any(r[u"先頭の位が減った"] for r in rows))

    def test_w_4_the_t2_claim_lookup_by_the_unit_before_would_not_map(self):
        u"""T2 の注入後の claim を元の単位で引く変異を、script の ``TUNE.claim_for_p27`` の引数の差し替えで再現して赤にする(引きは後の単位)。"""
        real = TUNE.claim_for_p27
        seen = []

        def spy(claims, inj, unit):
            if inj["type"] == "T2_UNIT":
                seen.append((inj["detail"]["unit_before"], inj["detail"]["unit_after"], unit))
            return real(claims, inj, unit)
        run_procedure(patches=((TUNE, "claim_for_p27", spy),))
        self.assertEqual(4, len(seen))                                  # 2 つの注入 × 2 profile
        for before, after, used in seen:
            self.assertEqual(after, used)
            self.assertNotEqual(before, used)

    def test_w_5_a_false_reach_is_not_counted_when_the_span_does_not_carry_the_replacement(self):
        def verify_no_tail(text0):
            base = fake_verify_for(text0)

            def v(zb, p, t):
                out = base(zb, p, t)
                if t != text0:
                    for c in out["claims"]:
                        if c["state"] == V_:
                            c["span"] = c["span"][:1]                       # 注入後の claim の span が差し替えの字を運ばない
                return out
            return v
        with Patch() as pt, JT.yen_scan_on():
            pt.set(RUN, "PROFILES", INJECT_PROFILES)
            rows, _c = JT.inject_text_j(b"zip", TEXT_P, REFS_P, u"sd", u"bk", verify=verify_no_tail(TEXT_P))
        self.assertTrue(rows)
        self.assertFalse(any(r[u"届いた"] for r in rows if r[u"型"] == "T2_UNIT"))

    def test_w_6_the_reach_needs_the_original_digits_in_the_base_claim_span(self):
        def verify_other_span(text0):
            base = fake_verify_for(text0)

            def v(zb, p, t):
                out = base(zb, p, t)
                if t == text0:
                    for c in out["claims"]:
                        c["span"] = u"x" + c["span"][-2:]                   # 基準の claim の span が元の字を運ばない(単位の字だけ)
                return out
            return v
        with Patch() as pt, JT.yen_scan_on():
            pt.set(RUN, "PROFILES", INJECT_PROFILES)
            rows, _c = JT.inject_text_j(b"zip", TEXT_P, REFS_P, u"sd", u"bk", verify=verify_other_span(TEXT_P))
        self.assertFalse(any(r[u"届いた"] for r in rows))

    def test_w_6b_the_t2_reach_keeps_the_separator_of_the_original_text(self):
        u"""「5 万円」(区切りの空白が入る既存の token)の T2 は『5 千円』と空白を元のまま書く。届いたは元の数の字 + 区切り + 後の単位で見る。"""
        text = u"その他の収益は5 万円でした。"
        refs = [{"key": "jppfs:Other@CurrentYearDuration", "value": 50000.0, "unit": u"円", "label": u"その他の収益"}]
        rows, c = run_procedure(text=text, refs=refs)
        t2 = [r for r in rows if r[u"型"] == "T2_UNIT"]
        self.assertEqual(1, len(t2))
        self.assertEqual(u"既存", t2[0][u"形"])
        self.assertEqual(u"万円", t2[0][u"単位"])
        self.assertTrue(t2[0][u"読み直し"] and t2[0][u"round-trip"] and t2[0]["P30E"][u"対応"] and t2[0][u"届いた"], t2[0])
        self.assertEqual(1, c["token の数え"][u"全部"][u"万円(空白入り)"])

    def test_w_6c_the_cap_is_applied_per_type_at_the_place_the_seal_says(self):
        u"""T2 は cap を採用に(基準で絞る前)、T6・T7 は土台 GROUNDED の site を先頭から cap 件。作れる site が cap より多い本で見る。"""
        items = [(u"科目%s" % chr(0x41 + i), 1000 + 7 * i) for i in range(12)]
        text = u"".join(u"%sは%s千円でした。" % (lab, format(v, ",")) for lab, v in items)
        refs = [{"key": "jppfs:Item%d@CurrentYearDuration" % i, "value": float(v * 1000), "unit": u"円", "label": lab} for i, (lab, v) in enumerate(items)]
        rows, c = run_procedure(text=text, refs=refs)
        self.assertEqual(12, sum(c["T2_UNIT"][u"作れる site"].values()))
        self.assertEqual(10, c["T2_UNIT"][u"採った"])
        self.assertEqual(12, sum(c["T7_ROUND"][u"作れる site"].values()))
        self.assertEqual((10, 10, 12), (c["T7_ROUND"][u"採った"], c["T7_ROUND"][u"cap を基準で絞る前に掛けた数"], c["T7_ROUND"][u"土台 P30E が GROUNDED の site"]))
        self.assertEqual(10, len([r for r in rows if r[u"型"] == "T7_ROUND"]))
        self.assertEqual(10, len([r for r in rows if r[u"型"] == "T2_UNIT"]))
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))
        self.assertEqual(0, c["T6_PRIOR"][u"採った"])

    def test_w_6d_the_cap_after_the_base_filter_takes_only_grounded_sites(self):
        u"""T6・T7 の cap は土台が GROUNDED の site だけを先頭から数える(基準で絞った後)。cap より多い 12 件の GROUNDED と 4 件の GROUNDED でない site で、行は cap 件。"""
        items = [(u"科目%s" % chr(0x41 + i), 1000 + 7 * i) for i in range(16)]
        text = u"".join(u"%sは%s千円でした。" % (lab, format(v, ",")) for lab, v in items)
        refs = [{"key": "jppfs:Item%d@CurrentYearDuration" % i, "value": float(v * 1000), "unit": u"円", "label": lab} for i, (lab, v) in enumerate(items)]
        base = fake_verify_for(text)

        def verify_some(zb, p, t):
            out = base(zb, p, t)
            if t == text:
                for k, cl in enumerate(out["claims"]):
                    if k % 5 == 0:
                        cl["state"] = V_                       # 土台が GROUNDED でない claim を 4 件(0・5・10・15 番目)
            return out
        with Patch() as pt, JT.yen_scan_on():
            pt.set(RUN, "PROFILES", INJECT_PROFILES)
            rows, c = JT.inject_text_j(b"zip", text, refs, u"sd", u"bk", verify=verify_some)
        t7 = c["T7_ROUND"]
        self.assertEqual((16, 12, 10, 10), (sum(t7[u"作れる site"].values()), t7[u"土台 P30E が GROUNDED の site"], t7[u"採った"], t7[u"cap を基準で絞る前に掛けた数"]))
        self.assertEqual(10, len([r for r in rows if r[u"型"] == "T7_ROUND"]))
        self.assertEqual({JT.LINKED: 12, JT.STATUS_NOT_G: 4}, dict(t7[u"作れる site の状態"]))
        self.assertEqual({JT.LINKED: 10}, dict(t7[u"採った の状態"]))
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))

    def test_w_6e_a_claim_that_does_not_pair_between_the_profiles_leaves_the_p29e_cell_unmapped(self):
        base = fake_verify_for(TEXT_P)

        def verify(zb, p, t):
            out = base(zb, p, t)
            if p == "P29E":
                for cl in out["claims"]:
                    cl["span"] = cl["span"] + u"x"                  # (value, span, unit) が P30E の claim と結べない
            return out
        with Patch() as pt, JT.yen_scan_on():
            pt.set(RUN, "PROFILES", INJECT_PROFILES)
            rows, c = JT.inject_text_j(b"zip", TEXT_P, REFS_P, u"sd", u"bk", verify=verify)
        self.assertTrue(rows)
        for r in rows:
            self.assertIs(False, r[LINK_KEY], r)
            self.assertEqual(TUNE.LABEL_UNMAPPED, r["P29E"][u"結果"])
            self.assertTrue(r["P30E"][u"対応"])
        for t in J_TYPES:
            self.assertEqual({JT.UNLINKED}, set(c[t][u"採った の状態"]), t)
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))

    def test_w_7_a_fullwidth_digit_book_is_skipped_with_its_token_counts(self):
        rows, c = run_procedure(text=u"売上高は１２億円でした。")
        self.assertEqual([], rows)
        self.assertIn(u"注入しない", c)
        self.assertIn(u"token の数え", c)

    def test_w_8_the_summaries_use_the_three_types_and_put_the_types_back(self):
        rows, _c = run_procedure()
        base = [(u"docID", u"D"), (u"form", u"F1"), (u"model", u"m"), (u"writer", u"W")]
        rows = [collections.OrderedDict(base + list(r.items())) for r in rows]
        self.assertEqual(("T1_VALUE", "T8_REL"), tuple(RUN.INJECT_TYPES))                    # H・RB の便の型の並び(他の門が読む)
        summ, cmp_ = JT.inject_summaries(rows)
        self.assertEqual(list(J_TYPES), list(summ))
        self.assertEqual(list(J_TYPES), list(cmp_))
        self.assertEqual(("T1_VALUE", "T8_REL"), tuple(RUN.INJECT_TYPES))
        self.assertEqual(len([r for r in rows if r[u"型"] == "T7_ROUND"]), summ["T7_ROUND"]["P30E"][u"全体"][u"注入の行"])
        try:
            with JT.j_types_in_run():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertEqual(("T1_VALUE", "T8_REL"), tuple(RUN.INJECT_TYPES))

    def test_w_9_the_job_refuses_a_switch_that_is_off(self):
        with self.assertRaises(JT.Stop):
            JT.inject_job_j(("aiforms", "n", {}, {}, "d", {}, "s", "w"))

    def test_w_10_run_inject_leaves_the_switch_off_and_writes_the_record_parts(self):
        u"""run_inject の記録の組み立てと切り替えの出入りを、読み込み・並列・cache を偽にして 1 回通す。"""
        base = sample_inject()
        rows = norm(base[u"行"])
        item = {u"docID": "DOC1", u"form": "F1", u"model": "m1", u"writer": "W1", u"sha256": "0" * 64}
        seen = []
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(RUN, "PROFILES", RUN.PROFILES)
            pt.set(RUN, "base_status4", RUN.base_status4)
            pt.set(JT, "load_books", lambda root=ROOT, only=None: [("aiforms", "DOC1_F1_m1", item, {}, {})])

            def pool(fn, jobs_, procs):
                seen.append(getattr(N, FLAG))
                return [("DOC1_F1_m1", [collections.OrderedDict(r) for r in rows if r["docID"] == "DOC1"], norm(base[u"本ごとの数え"][u"DOC1_F1_m1"]))]
            pt.set(NF, "map_pool", pool)
            pt.set(JT, "caches_all", lambda: collections.OrderedDict())
            pt.set(GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
            pt.set(JT, "header_j", lambda root, step, seed_meta, before, after, profiles: collections.OrderedDict([(u"seal", SEAL_REL), (u"profile", list(profiles))]))
            out = os.path.join(d, "inject.json")
            rec = JT.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with open(out, encoding="utf-8") as fh:
                disk = json.load(fh)
            with self.assertRaises(JT.Stop):                                                    # 出力が在れば測り直さない
                JT.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with self.assertRaises(JT.Stop):                                                    # --only は --out が要る(本番の記録を作らない。守りが壊れても root の下の使い捨ての場所に書く)
                JT.run_inject(root=d, procs=1, only="DOC1", say=lambda *a: None, work_root=d)
            self.assertFalse(os.path.exists(os.path.join(d, JT.INJECT_REL)))
        self.assertEqual([True], seen)                                    # map_pool の呼ばれた間は真
        self.assertFalse(getattr(N, FLAG))                                # 出たら偽
        self.assertEqual(norm(rec), disk)
        self.assertEqual(BASE_WORD_PIN, disk[u"型"][u"土台"])
        self.assertEqual(SITE_WORD_PIN, disk[u"型"][u"site"])
        self.assertEqual(JT.seal_limits(read(SEAL_REL)) + list(JT.EXTRA_LIMITS), disk[u"限界"])
        self.assertEqual({u"名前": FLAG, u"inject の中の値": True, u"出たあとの値": False, u"配線の問題": []}, disk[u"切り替え"])
        self.assertEqual(norm(JT.j_columns(disk[u"本ごとの数え"], disk[u"行"])), disk[JT.J_KEY])
        self.assertEqual([u"P29E", u"P30E"], disk[u"profile"])
        self.assertEqual(list(J_TYPES), list(disk[u"集計"]))
        self.assertEqual(u"**--only(本番の記録ではない)**", JT.scope_word("x"))
        self.assertEqual(u"全 200 本", JT.scope_word(None))

    def test_w_11_the_header_of_a_real_record_passes_the_header_check(self):
        u"""script の ``header_j`` が作る頭が、門の頭の検査を通る。1 欄ずつ落とすと赤。"""
        h = JT.header_j(ROOT, u"標本", {u"seed_file": u"x"}, {}, {}, INJECT_PROFILES)
        rec = collections.OrderedDict(h)
        rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
        rec[u"範囲"] = u"全 200 本"
        self.assertEqual([], header_problems(norm(rec), True))
        for key in (u"lib の指紋", u"nscan script の sha256", u"rmix script の sha256", u"H の記録の sha256", u"RB の記録の sha256", u"engine の指紋", u"この script の sha256", u"生成の記録の sha256"):
            r2 = norm(rec)
            r2.pop(key)
            self.assertNotEqual([], header_problems(r2, True), key)

    def test_w_12_load_books_filters_by_docid_and_stops_on_an_unknown_one(self):
        if not os.path.exists(os.path.join(ROOT, JT.SOURCES["aiforms"]["claims"])):
            self.skipTest(u"前の便の claims の記録が無い")
        books = JT.load_books(ROOT, None)
        ids = sorted(set(b[2]["docID"] for b in books))
        self.assertEqual(200, len(books))
        two = JT.load_books(ROOT, u"%s,%s" % (ids[0], ids[1]))
        self.assertEqual(set(ids[:2]), set(b[2]["docID"] for b in two))
        self.assertEqual(sum(1 for b in books if b[2]["docID"] in ids[:2]), len(two))
        with self.assertRaises(JT.Stop):
            JT.load_books(ROOT, u"X0000000")
        with self.assertRaises(JT.Stop):
            JT.load_books(ROOT, u"%s,X0000000" % ids[0])


class TokenCountTest(unittest.TestCase):
    def test_t_1_token_kinds_and_t5_counts_on_a_small_text(self):
        text = u"売上高は12億3,456万円、利益は1,234万円、資本は10億円、費用は5 万円、件数は12人でした。"
        with JT.yen_scan_on():
            k = JT.token_kinds(text)
        self.assertEqual({u"既存": 2, u"万円(空白入り)": 1, u"万だけ": 1, u"複合": 1}, dict(k[u"全部"]))          # 既存 = 10億円・12人
        self.assertEqual(list(JT.KIND4), list(k[u"全部"]))
        refs = [{"key": "a@CurrentYearDuration", "value": 12340000.0, "unit": u"円", "label": u"利益"}, {"key": "b@CurrentYearDuration", "value": 12345000.0, "unit": None, "label": u"他"}]
        with JT.yen_scan_on():
            t5 = JT.t5_counts(u"利益は1,234万円でした。", refs)
        self.assertEqual(0, t5[u"偽"] if t5[u"偽"] == 0 else 0)
        self.assertEqual(t5[u"真"], sum(t5[u"真の相手の単位"].values()))
        self.assertEqual({"None", u"円", u"その他"}, set(t5[u"others の単位の内訳"]))
        self.assertFalse(getattr(N, FLAG))

    def test_t_2_unit_class_names_none_yen_and_other(self):
        self.assertEqual("None", JT.unit_class(None))
        self.assertEqual(u"円", JT.unit_class(u"円"))
        self.assertEqual(u"その他", JT.unit_class(u"株"))
        self.assertEqual(u"その他", JT.unit_class(u"千円"))


# ================================================================ 宣言(docID を持つ記録は LATER_NAMING_FILES に、script は LATER_HARNESS_FILES に宣言する)
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
    def test_h_1_the_record_is_declared_as_a_naming_file(self):
        src = read("tests/measure/test_xbrl_fresh_seal.py")
        self.assertEqual([], naming_problems(src))
        for rel in REC_REL.values():
            self.assertNotEqual([], naming_problems(src.replace('"%s"' % rel, '"x/%s"' % rel)), rel)
        self.assertNotEqual([], naming_problems(src.replace("LATER_NAMING_FILES", "LATER_NAMING_FILE")))
        last = list(REC_REL.values())[-1]
        self.assertNotEqual([], naming_problems(src.replace('"%s"' % last, '"%s", "%s"' % (last, SG.GATE_RELS[0]))))

    def test_h_2_the_previous_declarations_are_still_there(self):
        got = later_naming_files(read("tests/measure/test_xbrl_fresh_seal.py"))
        for rel in ("fixtures/xbrl/nscan/inject_2026-11-05.json", "fixtures/xbrl/nscan/offcheck_2026-11-05.json", "fixtures/xbrl/rmix/ai200_2026-11-04.json", "fixtures/xbrl/numfix/ai200_2026-11-04.json"):
            self.assertIn(rel, got)

    def test_h_3_the_script_is_declared_as_a_harness_file(self):
        src = read("tests/measure/test_xbrl_inject_harness_review.py")
        self.assertEqual([], harness_problems(src))
        self.assertNotEqual([], harness_problems(src.replace(u'"%s"' % SCRIPT_REL, u'"x/%s"' % SCRIPT_REL)))
        self.assertNotEqual([], harness_problems(src.replace("LATER_HARNESS_FILES", "LATER_HARNESS_FILE")))


# ================================================================ 順序(e)の変異(使い捨ての repo)
OTHERS = list(REC_REL.values()) + [DOC_REL]


class OrderMutationTest(unittest.TestCase):
    def _repo(self, before_seal=(), commit_others=OTHERS):
        r = PR.Repo()
        for f in before_seal:
            r.put(f)
            r.commit(f)
        r.put(SEAL_REL)
        s = r.commit(SEAL_REL)
        for f in commit_others:
            r.put(f)
        if commit_others:
            r.commit(*commit_others)
        return r, s

    def probe(self, r, s):
        return PR.order_problems(r.d, PREFIX, SEAL_REL, s[:7], [], OTHERS)

    def test_e_1_good_order_is_green(self):
        r, s = self._repo()
        self.assertEqual([], self.probe(r, s))

    def test_e_2_records_before_the_seal_or_uncommitted_are_red(self):
        r, s = self._repo(commit_others=[])
        self.assertEqual(sorted("UNCOMMITTED:" + o for o in OTHERS), sorted(self.probe(r, s)))
        r2, s2 = self._repo(before_seal=[OTHERS[0]], commit_others=OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], self.probe(r2, s2))
        r3, s3 = self._repo(commit_others=OTHERS[:-1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[-1]], self.probe(r3, s3))

    def test_e_3_a_wrong_seal_is_red(self):
        r, _s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", PR.order_problems(r.d, PREFIX, SEAL_REL, "abcdef0", [], OTHERS))

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
            self.skipTest(u"記録が無い(inject を走らせた後に走る)")
        return load_records()

    def test_r_1_records_are_clean_and_consistent(self):
        R = self.need()
        self.assertEqual([], record_problems(copy.deepcopy(R), full=True))

    def test_r_2_judgment_is_rebuilt_from_the_records(self):
        R = self.need()
        self.assertEqual([], [x for x in judge_problems(R, self.seal)])
        J = JT.build_J(R, self.seal)
        self.assertEqual(set(J), {u"J", u"K", u"採用", u"欄"})

    def test_r_3_the_result_document_follows_the_records(self):
        R = self.need()
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), R, self.seal, [x for x in JT.git_numstat_since_seal(ROOT) if not SG.SGR.t5y_declared_numstat(x)]))

    def test_r_4_order_is_seal_then_records_and_document(self):
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
