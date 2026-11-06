# -*- coding: utf-8 -*-
"""T9(前期の fact に結ばれた数に当期の値を入れる注入 T9_PRIOR_TO_CURRENT。切り替え ``yen_scan_2026_11_05``)の測定の結果の門。封 docs/XBRL_PERIOD_SWAP_SEAL_2026-11-06.md §1・§3・§4・§5。

記録 1 つ(``fixtures/xbrl/pswap/inject_2026-11-06.json``)と、読むだけの H の記録・RB の記録から、封 §3 の予測 PS-1〜PS-10 と §4 の採用の基準 K-1〜K-4 を**機械で求め**(予測の幅は封の字から読む。字のコピーにしない)、
結果の文書 ``docs/XBRL_PERIOD_SWAP_RESULT_2026-11-06.md`` の表(``<!-- 門:start pred -->``・``<!-- 門:start judge -->`` の中)を記録から作り直した表と一行も違わないことを見る。
測定の script(``measure/xbrl_pswap_2026-11-06.py`` の ``build_PS``・``judge_from``・``ps_columns``・``render_pred``・``render_judge``)の関数を呼んで照らす。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文・pointer・要素など)が無い・pointer の字(要素名)を持たない・key_leaks が空・docID を持つ記録が ``LATER_NAMING_FILES`` に宣言され、
     script が ``LATER_HARNESS_FILES`` に宣言されている・cache の前後が同じ・script と lib と前の便の script・記録の sha256 が現物と一致・engine の指紋が封の commit の木から作り直した値と一致する・切り替えの欄。
  b  記録の中身が再計算と一致する: 本ごとの数えの整合(段・欄の間・行との関係・cap)・行の整合・集計・形別・手がかり別・通した行の期の内訳・
     **PS の欄の全部を 本ごとの数えと行から数え直す**(欄を 0 に固定すると赤。行の欄を 1 つ変えると該当の欄が動く)・限界(封 §6 の字 + script の限界)。
  c  判定: 記録(の欄)を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。採用は K-1〜K-4 を全部満たすときだけ。
  d  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 3a6aefa ⊏ 記録・結果の文書(script・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  g  変異: 小さい標本の記録と文書で同じ検査が緑 → 変異(記録の数・PS の欄・表の 1 字・封の予測の 1 字・順序・記録の禁止欄・指紋の 1 字・cache の前後・切り替え・pointer の字・期の欄)で赤。
  w  手順・**行の欄**: script の ``inject_text_ps`` を小さい入力(zip・判定は偽。lib は本物)で通し、行の欄(round-trip・読み直し・先頭の位が減った・届いた・engine の手がかり・文に前期の語・pointer の期)を
     **壊した差し替え(文を変える・値を変える・位を落とす・手がかりを常に真・期の分け方を固定)で True ↔ False が替わる例**で固定する(J の便で標本の行が欄を固定する変異に黙った 6 本の型を最初から潰す)。

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


SG = load_module("tests/measure/test_xbrl_pswap_seal.py", "pswap_seal_gate_for_result")        # 封の門の部品。門としては走らせない
PR = SG.PR                                                                                    # doc_blocks・prose_problems・order_problems・Repo
PS = SG.PS
JT = PS.JT
NS = PS.NS
RM, NF, GEN, RUN, TUNE, IJ, S = PS.RM, PS.NF, PS.GEN, PS.RUN, PS.TUNE, PS.IJ, PS.S
N, SC = PS.N, PS.SC

SEAL_REL = PS.SEAL_REL
DOC_REL = PS.DOC_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
REC_REL = collections.OrderedDict(PS.REC_REL)
SCRIPT_REL = PS.SCRIPT_REL
LIB_RELS = PS.LIB_RELS
FLAG = PS.FLAG
T9 = PS.T9
NOT_GATED = PR.NOT_GATED
HIT, MISS = PS.HIT, PS.MISS
SHAPES = PS.SHAPES
PERIODS = PS.PERIODS
LINK_KEY = PS.LINK_KEY
FORBIDDEN_KEYS = tuple(RUN.FORBIDDEN_KEYS) + (u"理由", u"根拠", u"周り", u"content", u"pointers", u"pointer", u"要素", u"element", u"context", u"label")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
#: 記録に持ってはいけない pointer の字(要素名・context)の形
POINTER_TEXT_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)")
DOCID_RE = SG.DOCID_RE
FOR_RESULT_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
HAVE_CACHE = all(os.path.isdir(p) for p in PS.caches_all().values())
INJECT_PROFILES = PS.INJECT_PROFILES
STATES = NF.STATES
#: 封 §3・§4 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("PS-1", u"一致"),
    ("PS-2", collections.OrderedDict([(u"計", (205.0, 230.0)), (u"既存", (25.0, 32.0)), (u"万だけ", (13.0, 19.0)), (u"複合", (165.0, 185.0)), (u"手がかり真", (140.0, 180.0))])),
    ("PS-3", collections.OrderedDict([(u"採った", (185.0, 218.0)), (u"うち土台 P30E が GROUNDED の行", (100.0, 200.0)), (u"割合", (85.0, 100.0))])),
    ("PS-4", (50.0, 95.0)), ("PS-5", (95.0, 100.0)),
    ("PS-6", collections.OrderedDict([(u"手がかり真の割合", (75.0, 100.0)), (u"手がかり真の行の通した率", (45.0, 95.0))])),
    ("PS-7", 0), ("PS-8", (0, 3)),
    ("PS-9", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"先頭の位が減った行", (0, 15))])),
    ("PS-10", (60.0, 100.0)),
    ("K-1", u"一致"), ("K-2", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0)])), ("K-3", 80.0), ("K-4", 0)])
#: 注入の土台の字・site の字(測定の script の定数と同じでなければ赤)
BASE_WORD_PIN = u"無改変の文で P30E が GROUNDED の claim"
SITE_WORD_PIN = u"ref の context が Prior1Year で始まり、同じ要素の CurrentYear の fact がちょうど 1 件・単位が同じ・両方正・値が違い、当期の値を元の字の形で描ける数(既存・万だけ・複合の全部)"
#: この script の限界(封 §6 の 5 つの後ろに足した 6 つ)の字の頭(literal に留める。script の字を変えたら赤)
EXTRA_LIMITS_PIN = (u"round-trip 不一致は止めずに数える", u"PS-3 の「採った」は cap を基準で絞る前に掛けた数", u"「届いた」は元の数の字が基準の claim の span に在り",
                    u"pointer の期は基準の claim と注入後の claim", u"engine の手がかりは注入前の文と注入前の token", u"PS-8 の「判定が違う行」は P29E と P30E の両方で")
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
G, V_, U_, P_ = "GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"
INFO_PS1 = (u"lib の指紋が H の記録と一致", u"engine の指紋が RB の記録と一致", u"inject.py・sites.py が封の commit から変わった file")
PTR_PRIOR = "xbrl:jppfs_cor:NetSales@Prior1YearDuration"
PTR_CUR = "xbrl:jppfs_cor:NetSales@CurrentYearDuration"
KEY = {"PS-2": u"PS-2 作れる site(種類別)と engine の手がかり真", "PS-3": u"PS-3 採った / うち土台 P30E が GROUNDED の行 / 基準の pointer の期", "PS-4": u"PS-4 通した率(P30E)",
       "PS-5": u"PS-5 通した行の注入後の pointer の期", "PS-6": u"PS-6 engine の手がかり", "PS-7": u"PS-7 通した行のうち届かない行",
       "PS-8": u"PS-8 P29E と P30E で判定が違う行(両方に対応が付く行)", "PS-9": u"PS-9", "PS-10": u"PS-10 止めた行の中で名指して原本の割合", "REF": u"参考"}
SEP = u"::"                                  # sample_cols の path の区切り(欄の名前に / が入るため)


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
        _FIXED["h"] = jload(PS.H_RECORD_REL)
        _FIXED["rb"] = jload(PS.RB_RECORD_REL)
    return _FIXED


def load_records():
    f = fixed_records()
    return collections.OrderedDict([("inject", jload(REC_REL["inject"])), ("h", f["h"]), ("rb", f["rb"])])


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
        got = PS.seal_bounds(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return [u"封から幅を読めない(%s)" % type(e).__name__]
    for k, v in BOUNDS_PIN.items():
        g = got.get(k)
        if json.dumps(norm_t(g), sort_keys=True) != json.dumps(norm_t(v), sort_keys=True):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, g, v))
    if list(PS.seal_pred_rows(seal)) != list(SG.PRED_IDS) or list(PS.seal_k_rows(seal)) != list(SG.K_IDS):
        out.append(u"封の予測の行が PS-1〜PS-10 でない・K の行が K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 記録(a)(b)
def walk(o):
    return list(RUN.walk_keys(o))


def walk_strings(o):
    if isinstance(o, dict):
        for k, v in o.items():
            for x in walk_strings(k):
                yield x
            for x in walk_strings(v):
                yield x
    elif isinstance(o, (list, tuple)):
        for v in o:
            for x in walk_strings(v):
                yield x
    elif isinstance(o, str):
        yield o


def header_problems(rec, full):
    u"""記録の頭(封・script・lib・前の便の script と記録・engine・cache・切り替え)。"""
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"封の名か commit が違う")
    want = collections.OrderedDict([
        (u"この script の sha256", sha256_rel(SCRIPT_REL)), (u"J の script の sha256", sha256_rel(PS.JT_SCRIPT_REL)), (u"nscan script の sha256", sha256_rel(PS.NS_SCRIPT_REL)),
        (u"rmix script の sha256", sha256_rel("measure/xbrl_rmix_2026-11-04.py")), (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")),
        (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")), (u"生成の script の sha256", sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")),
        (u"J の記録の sha256", sha256_rel(PS.JT_RECORD_REL)), (u"H の記録の sha256", sha256_rel(PS.H_RECORD_REL)), (u"RB の記録の sha256", sha256_rel(PS.RB_RECORD_REL))])
    for name, v in want.items():
        if rec.get(name) != v:
            out.append(u"%s が現物と違う" % name)
    gens = dict((src, sha256_rel(p["gen"])) for src, p in PS.SOURCES.items())
    if norm(rec.get(u"生成の記録の sha256")) != gens:
        out.append(u"生成の記録の sha256 が現物と違う")
    if norm(rec.get(u"lib の指紋")) != dict((rel, sha256_rel(rel)) for rel in LIB_RELS):
        out.append(u"lib の指紋が現物と違う")
    if rec.get(u"profile") != list(INJECT_PROFILES):
        out.append(u"profile が (P29E, P30E) でない")
    fp = rec.get(u"engine の指紋") or {}
    want_fp = engine_fingerprint_at_seal()
    for name in want_fp:
        if name == "adapter_xbrl_py_sha256" and SG.SGR.pb_declared_fingerprint(fp.get(name)):      # 2026-11-06(PB): 封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §2-3 が宣言した遷移の指紋(封が履歴に在るときだけ)
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
    if any(POINTER_TEXT_RE.search(s) for s in walk_strings(rec)):
        out.append(u"記録に pointer の字(要素名・context)がある")
    try:
        PS.assert_clean_ps(copy.deepcopy(rec))
    except GEN.Stop:
        out.append(u"鍵らしい字が記録に在る")
    if rec.get(u"key_leaks", []) != []:
        out.append(u"key_leaks が空でない")
    return out


def count_problems(name, c, rows, cap):
    u"""本ごとの数え 1 本の整合(自分の欄の間と、その本の行との関係)。"""
    out = []
    if u"注入しない" in c:
        if rows:
            out.append(u"%s: 注入しない本に行がある" % name)
        if set(c) != {u"注入しない"}:
            out.append(u"%s: 注入しない本に数えがある" % name)
        return out
    st = c[u"段"]
    if list(st) != list(PS.STAGE_KEYS):
        out.append(u"%s: 段の欄が封の段でない" % name)
    vals = [st[k] for k in PS.STAGE_KEYS]
    if any(vals[i] < vals[i + 1] for i in range(len(vals) - 1)) or min(vals) < 0:
        out.append(u"%s: 段の数が減っていない(Prior1Year ≥ 当期が 1 件 ≥ 単位が同じ・正・値が違う ≥ site)" % name)
    sh = c[u"作れる site"]
    sites = sum(sh.values())
    if list(sh) != list(SHAPES) or sites != st[u"site"]:
        out.append(u"%s: 作れる site の形別の和が段の site と合わない" % name)
    cue = c[u"作れる site の手がかり"]
    if list(cue) != [u"真", u"偽"] or sum(cue.values()) != sites:
        out.append(u"%s: 手がかりの真偽の和が作れる site と合わない" % name)
    pop, taken = c[u"作れる site の状態"], c[u"採った の状態"]
    ok_keys = (PS.LINKED, PS.UNLINKED)
    good = pop.get(PS.LINKED, 0) + pop.get(PS.UNLINKED, 0)
    if sum(pop.values()) != sites:
        out.append(u"%s: 作れる site の状態の和が作れる site と合わない" % name)
    if c[u"土台 P30E が GROUNDED の site"] != good or c[u"cap を基準で絞る前に掛けた数"] != min(cap, sites) or c[u"採った"] != min(cap, good):
        out.append(u"%s: 土台 GROUNDED の site・cap・採った の関係が合わない" % name)
    if sum(taken.values()) != c[u"採った"] or set(taken) - set(ok_keys) or any(taken.get(k, 0) > pop.get(k, 0) for k in taken):
        out.append(u"%s: 採った の状態が合わない" % name)
    if len(rows) != c[u"採った"] or sum(1 for r in rows if r[LINK_KEY]) != taken.get(PS.LINKED, 0) or len(rows) > cap:
        out.append(u"%s: 行の数・P29E に対応が付く行の数が 採った の状態と合わない" % name)
    for k in SHAPES:
        if sum(1 for r in rows if r[u"形"] == k) > sh.get(k, 0):
            out.append(u"%s: 形 %s の行が作れる site より多い" % (name, k))
    if sum(1 for r in rows if r[u"engine の手がかり"]) > cue[u"真"]:
        out.append(u"%s: 手がかり真の行が手がかり真の site より多い" % name)
    return out


def row_problems(r, labels, seen):
    out = []
    if r[u"型"] != T9:
        out.append(u"型が T9_PRIOR_TO_CURRENT でない")
    if r[u"id"] in seen:
        out.append(u"同じ注入の id が 2 回ある")
    seen.add(r[u"id"])
    name = u"%s_%s_%s" % (r["docID"], r["form"], r["model"])
    if not r[u"id"].startswith(name + u"-T9-"):
        out.append(u"id が本の名前 + T9 の形でない")
    linked = r.get(LINK_KEY)
    unmapped = {u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}
    if not isinstance(linked, bool):
        out.append(u"P29E の土台に対応の欄が真偽でない")
    elif not linked and norm(r["P29E"]) != unmapped:
        out.append(u"P29E の土台に対応が無い行の P29E の欄が対応なしでない")
    if r["P30E"][u"対応"] is True and r["P30E"][u"結果"] == TUNE.LABEL_UNMAPPED:
        out.append(u"P30E の欄の対応と結果が合わない")
    for key in (u"round-trip", u"読み直し", u"先頭の位が減った", u"届いた", u"engine の手がかり", u"文に前期の語"):
        if not isinstance(r.get(key), bool):
            out.append(u"行の %s が真偽でない" % key)
    if r.get(u"形") not in SHAPES:
        out.append(u"行の形が語でない")
    if r.get(u"単位") is not None and (not isinstance(r.get(u"単位"), str) or not r.get(u"単位")):
        out.append(u"行の単位が語でも None でもない")                          # 単位の無い数(件数など)にも在る
    if r[u"先頭の位が減った"] and r[u"形"] != u"複合":
        out.append(u"先頭の位が減ったのは複合だけ")
    if r[u"届いた"] and not r["P30E"][u"対応"]:
        out.append(u"P30E に対応が付かない行が届いた")
    for key in (u"基準の pointer の期", u"注入後の pointer の期"):
        if r.get(key) not in PERIODS:
            out.append(u"行の %s が 4 つの語でない" % key)
    if not r["P30E"][u"対応"] and r.get(u"注入後の pointer の期") != u"なし":
        out.append(u"P30E に対応が付かない行の注入後の pointer の期が なし でない")
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
    if rec[u"型"].get(u"土台") != BASE_WORD_PIN or PS.BASE_WORD != BASE_WORD_PIN:
        out.append(u"inject: 型.土台 の字が P30E が GROUNDED の claim でない")
    if rec[u"型"].get(u"site") != SITE_WORD_PIN or PS.SITE_WORD != SITE_WORD_PIN:
        out.append(u"inject: 型.site の字が留めた字と違う")
    seal = read(SEAL_REL)
    if rec.get(u"限界") != PS.seal_limits(seal) + list(PS.EXTRA_LIMITS) or len(PS.seal_limits(seal)) != 5 or len(PS.EXTRA_LIMITS) != 6:
        out.append(u"inject: 限界が封 §6 の字(5 つ)とこの script の限界(6 つ)と違う")
    if len(PS.EXTRA_LIMITS) != len(EXTRA_LIMITS_PIN) or any(not x.startswith(pin) for x, pin in zip(PS.EXTRA_LIMITS, EXTRA_LIMITS_PIN)):
        out.append(u"inject: script の限界の字が留めた字の頭と違う")
    want = collections.OrderedDict([(u"全体", sum(1 for r in rec[u"行"] if r.get(LINK_KEY) is not True)), (T9, sum(1 for r in rec[u"行"] if r.get(u"型") == T9 and r.get(LINK_KEY) is not True))])
    if norm(rec.get(u"P29E に対応なしの行の数")) != norm(want):
        out.append(u"inject: P29E に対応なしの行の数が行から数え直した値と違う")
    labels = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
    seen, cnt = set(), collections.Counter()
    for r in rec[u"行"]:
        out += [u"inject: " + x for x in row_problems(r, labels, seen)]
        cnt[(r[u"docID"], r[u"form"], r[u"model"])] += 1
    if any(n > RUN.INJECT_CAP for n in cnt.values()):
        out.append(u"inject: 1 本あたりの上限 %d を超えている" % RUN.INJECT_CAP)
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
        summ, summ_cmp = (norm(x) for x in PS.inject_summaries(rec[u"行"]))
        bd = norm(PS.breakdown(rec[u"行"]))
        cb = norm(PS.cue_breakdown(rec[u"行"]))
        pb = norm(PS.period_breakdown(rec[u"行"]))
    if summ != rec[u"集計"] or rec[u"注入の行の数"] != len(rec[u"行"]):
        out.append(u"inject: 集計が行から作り直した値と違う")
    if list(summ) != [T9]:
        out.append(u"inject: 集計の型が T9 の 1 型でない")
    if summ_cmp != rec.get(PS.COMPARE_KEY):
        out.append(u"inject: 比較用の集計(P29E にも対応が付く site だけ)が行から作り直した値と違う")
    if bd != rec.get(PS.BREAKDOWN_KEY):
        out.append(u"inject: 形別の内訳が行から作り直した値と違う")
    if cb != rec.get(PS.CUE_KEY):
        out.append(u"inject: engine の手がかり別の内訳が行から作り直した値と違う")
    if pb != rec.get(PS.PERIOD_KEY):
        out.append(u"inject: 通した行の注入後の pointer の期の内訳が行から作り直した値と違う")
    try:
        cols = norm(PS.ps_columns(per, rec[u"行"]))
    except Exception as e:                                   # noqa: BLE001
        return out + [u"inject: PS の欄を作れない(%s)" % type(e).__name__]
    if cols != rec.get(PS.PS_KEY):
        out.append(u"inject: PS の欄が 本ごとの数え と 行 から作り直した値と違う")
    if full:
        names = [x[u"name"] for src in PS.SOURCES.values() for x in jload(src["claims"])[u"本"] if not x.get(u"欠け")]
        if list(per) != names:
            out.append(u"inject: 本ごとの数えの本が 200 本(前の便の claims の並び)でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(PS.caches_all())):
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
        J = PS.build_PS(R, seal, [])
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"PS"]) != list(SG.PRED_IDS) or list(J[u"K"]) != list(SG.K_IDS):
        out.append(u"判定の行が PS-1〜PS-10・K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R, seal, numstat=()):
    J = PS.build_PS(R, seal, list(numstat))
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != PS.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("judge") != PS.render_judge(J, seal).split(u"\n"):
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
        (u"生成の記録の sha256", collections.OrderedDict((src, sha256_rel(p["gen"])) for src, p in PS.SOURCES.items())),
        (u"engine の指紋", dict(engine_fingerprint_at_seal(), adapter_xbrl_py_files=16, core_py_files=4, git_commit="3" * 40)),
        (u"種の確認", {u"seed_file": u"x"}), (u"profile", list(INJECT_PROFILES)),
        (u"cache の前後", collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)])),
        (u"J の script の sha256", sha256_rel(PS.JT_SCRIPT_REL)), (u"nscan script の sha256", sha256_rel(PS.NS_SCRIPT_REL)),
        (u"rmix script の sha256", sha256_rel("measure/xbrl_rmix_2026-11-04.py")),
        (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")), (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")),
        (u"J の記録の sha256", sha256_rel(PS.JT_RECORD_REL)), (u"H の記録の sha256", sha256_rel(PS.H_RECORD_REL)), (u"RB の記録の sha256", sha256_rel(PS.RB_RECORD_REL)),
        (u"lib の指紋", collections.OrderedDict((rel, sha256_rel(rel)) for rel in LIB_RELS)), (u"範囲", u"標本")])


def sd(**kw):
    return collections.OrderedDict(sorted(kw.items()))


def pop_of(linked=0, unlinked=0, not_g=0, no_base=0):
    d = {}
    for k, v in ((PS.LINKED, linked), (PS.UNLINKED, unlinked), (PS.STATUS_NOT_G, not_g), (PS.STATUS_NO_BASE, no_base)):
        if v:
            d[k] = v
    return collections.OrderedDict(sorted(d.items()))


def t9_count(stages, exist, man, comp, cue_true, pop, taken_pop):
    sites = exist + man + comp
    good = pop.get(PS.LINKED, 0) + pop.get(PS.UNLINKED, 0)
    return collections.OrderedDict([
        (u"段", collections.OrderedDict(zip(PS.STAGE_KEYS, stages))),
        (u"作れる site", collections.OrderedDict([(u"既存", exist), (u"万だけ", man), (u"複合", comp)])),
        (u"作れる site の手がかり", collections.OrderedDict([(u"真", cue_true), (u"偽", sites - cue_true)])),
        (u"作れる site の状態", pop), (u"土台 P30E が GROUNDED の site", good), (u"cap を基準で絞る前に掛けた数", min(RUN.INJECT_CAP, sites)),
        (u"採った の状態", taken_pop), (u"採った", min(RUN.INJECT_CAP, good))])


def cell(res, state, reason=None):
    return collections.OrderedDict([(u"対応", True), (u"結果", res), (u"state", state), (u"reason", reason)])


PASS_ = (TUNE.LABEL_PASS, G)
NAMED = (TUNE.LABEL_NAMED_ORIGINAL, V_)
OTHER = (TUNE.LABEL_NAMED_OTHER, V_)
PNF = (TUNE.LABEL_PNF, P_, "no_element")
UNMAPPED = None


def prow(item, rid, shape, unit, linked, p29, p30, rt=True, rr=True, lead=False, cue=True, word=True, base_p=u"Prior1Year", post_p=u"Prior1Year", reached=False):
    row = collections.OrderedDict([(u"docID", item["docID"]), (u"form", item["form"]), (u"model", item["model"]), (u"writer", item["writer"]),
                                   ("id", u"%s_%s_%s-%s" % (item["docID"], item["form"], item["model"], rid)), (u"型", T9), (u"形", shape), (u"単位", unit),
                                   (u"基準の claim", u"N%03d" % (len(rid) + 1)), (LINK_KEY, linked), (u"round-trip", rt), (u"読み直し", rr), (u"先頭の位が減った", lead),
                                   (u"engine の手がかり", cue), (u"文に前期の語", word), (u"基準の pointer の期", base_p)])
    row["P29E"] = cell(*p29) if linked else TUNE.classify(None, None)
    row["P30E"] = cell(*p30) if p30 is not None else TUNE.classify(None, None)
    row[u"注入後の pointer の期"] = post_p if p30 is not None else u"なし"
    row[u"届いた"] = reached
    return row


def sample_rows():
    a, c = ITEMS[0], ITEMS[2]
    return [
        prow(a, "T9-01", u"複合", u"万円", True, NAMED, NAMED, reached=True),
        prow(a, "T9-02", u"複合", u"万円", True, NAMED, PASS_, post_p=u"CurrentYear", reached=True),
        prow(a, "T9-03", u"既存", u"円", True, NAMED, PASS_, cue=False, word=False, base_p=u"他", post_p=u"CurrentYear", reached=True),
        prow(a, "T9-04", u"万だけ", u"万円", False, None, OTHER, post_p=u"他", reached=True),
        prow(a, "T9-05", u"複合", u"万円", True, NAMED, UNMAPPED, lead=True),
        prow(c, "T9-01", u"既存", None, True, NAMED, NAMED, reached=True),
        prow(c, "T9-02", u"複合", u"万円", True, NAMED, PASS_, post_p=u"CurrentYear", reached=True)]


def sample_per():
    ca = t9_count((8, 8, 7, 6), 2, 1, 3, 4, pop_of(linked=4, unlinked=1, not_g=1), sd(**{PS.LINKED: 4, PS.UNLINKED: 1}))
    cb = collections.OrderedDict([(u"注入しない", u"文に全角の数字がある(select は半角の文を前提にする)")])
    cc = t9_count((4, 4, 3, 3), 1, 0, 2, 2, pop_of(linked=2, no_base=1), sd(**{PS.LINKED: 2}))
    return collections.OrderedDict([(u"DOC1_F1_m1", ca), (u"DOC2_F5_m2", cb), (u"DOC3_F1_m1", cc)])


def sample_inject():
    rows = sample_rows()
    per = sample_per()
    rec = sample_header()
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
    rec[u"型"] = collections.OrderedDict([(u"site", SITE_WORD_PIN), (u"土台", BASE_WORD_PIN)])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"], rec[PS.COMPARE_KEY] = (norm(x) for x in PS.inject_summaries(rows))
    rec[PS.BREAKDOWN_KEY] = norm(PS.breakdown(rows))
    rec[PS.CUE_KEY] = norm(PS.cue_breakdown(rows))
    rec[PS.PERIOD_KEY] = norm(PS.period_breakdown(rows))
    rec[u"P29E に対応なしの行の数"] = norm(PS.unlinked_counts(rows))
    rec[PS.PS_KEY] = norm(PS.ps_columns(per, rows))
    rec[u"限界"] = PS.seal_limits(read(SEAL_REL)) + list(PS.EXTRA_LIMITS)
    rec[u"行"] = rows
    return norm(rec)


def sample_records():
    f = fixed_records()
    return collections.OrderedDict([("inject", sample_inject()), ("h", f["h"]), ("rb", f["rb"])])


def sample_ps1(**ov):
    d = collections.OrderedDict([(INFO_PS1[0], True), (INFO_PS1[1], True), (INFO_PS1[2], 0)])
    d.update(ov)
    return d


def sample_cols(**ov):
    u"""判定の関数の境界の試験用: ``ps_columns`` と同じ形の欄(幅の真ん中の値)。ov = {"欄::キー::...": 値} で 1 つだけ替える。"""
    c = collections.OrderedDict([
        (KEY["PS-2"], collections.OrderedDict([(u"計", 218), (u"既存", 28), (u"万だけ", 16), (u"複合", 174), (u"手がかり真", 164)])),
        (KEY["PS-3"], collections.OrderedDict([(u"採った", 200), (u"うち土台 P30E が GROUNDED の行", 150), (u"うち基準の pointer の期が Prior1Year の行", 130), (u"割合", 86.7)])),
        (KEY["PS-4"], collections.OrderedDict([(u"通した率(P30E)", 70.0), (u"通した行", 70), (u"対応が付く行", 100)])),
        (KEY["PS-5"], collections.OrderedDict([(u"通した行", 70), (u"うち注入後の pointer の期が CurrentYear", 69), (u"割合", 98.6)])),
        (KEY["PS-6"], collections.OrderedDict([(u"対応が付く行", 100), (u"うち手がかり真", 85), (u"手がかり真の割合", 85.0), (u"手がかり真の行の通した率", 70.0)])),
        (KEY["PS-7"], collections.OrderedDict([(u"通した行", 70), (u"うち届かない行", 0)])),
        (KEY["PS-8"], collections.OrderedDict([(u"違う行", 1), (u"両方に対応が付く行", 90)])),
        (KEY["PS-9"], collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"先頭の位が減った行", 5)])),
        (KEY["PS-10"], collections.OrderedDict([(u"対応が付く行", 100), (u"止めた行", 30), (u"うち名指して原本", 25), (u"割合", 83.3)])),
        (KEY["REF"], collections.OrderedDict([(u"届いた行", 70), (u"文に前期の語がある行", 140), (u"手がかり真の行(全部)", 120)]))])
    for path, v in ov.items():
        keys = path.split(SEP)
        d = c
        for kk in keys[:-1]:
            d = d[kk]
        d[keys[-1]] = v
    return c


def sample_doc(R, seal):
    J = PS.build_PS(R, seal, [])
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", PS.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start judge -->", PS.render_judge(J, seal), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"200 本の標本です。" + NOT_GATED, u""])


# ================================================================ (a) 封の字
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def test_a_2_a_changed_character_in_the_seal_turns_the_pin_red(self):
        rows = PS.seal_pred_rows(self.seal)
        for cid, old, new in (("PS-1", "一致", "不一致"),
                              ("PS-2", "205〜230", "206〜230"), ("PS-2", "205〜230", "205〜231"), ("PS-2", "/ 25〜32 /", "/ 25〜33 /"), ("PS-2", "/ 25〜32 /", "/ 26〜32 /"),
                              ("PS-2", "/ 13〜19 /", "/ 13〜20 /"), ("PS-2", "/ 165〜185、", "/ 165〜186、"), ("PS-2", "手がかり真 140〜180", "手がかり真 140〜181"),
                              ("PS-3", "185〜218", "185〜219"), ("PS-3", "/ 100〜200 /", "/ 100〜201 /"), ("PS-3", "85〜100%", "85〜101%"), ("PS-3", "85〜100%", "86〜100%"),
                              ("PS-4", "50〜95%", "50〜96%"), ("PS-4", "50〜95%", "51〜95%"), ("PS-5", "95〜100%", "96〜100%"),
                              ("PS-6", "75〜100%、", "75〜99%、"), ("PS-6", "、45〜95%", "、45〜96%"), ("PS-7", "0", "1"),
                              ("PS-8", "0〜3", "0〜4"), ("PS-9", "0 / 0 / 0〜15", "1 / 0 / 0〜15"), ("PS-9", "0 / 0 / 0〜15", "0 / 1 / 0〜15"), ("PS-9", "0 / 0 / 0〜15", "0 / 0 / 0〜16"),
                              ("PS-10", "60〜100%", "61〜100%")):
            self.assertIn(old, rows[cid][1], (cid, old))
            mutated = self.seal.replace("| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1]), "| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1].replace(old, new, 1)), 1)
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], bounds_problems(mutated), (cid, new))

    def test_a_3_the_thresholds_of_k1_to_k4_are_read_from_the_seal(self):
        b = PS.seal_bounds(self.seal)
        self.assertEqual((u"一致", {u"round-trip 不一致": 0, u"読み直し不一致": 0}, 80.0, 0), (b["K-1"], dict(b["K-2"]), b["K-3"], b["K-4"]))
        for old, new in (("PS-9 の round-trip 不一致 0・読み直し不一致 0", "PS-9 の round-trip 不一致 1・読み直し不一致 0"), ("PS-9 の round-trip 不一致 0・読み直し不一致 0", "PS-9 の round-trip 不一致 0・読み直し不一致 1"),
                         ("対応が付く行 ≥ 80", "対応が付く行 ≥ 81"), ("PS-7 が 0", "PS-7 が 1")):
            self.assertIn(old, self.seal, old)
            self.assertNotEqual([], bounds_problems(self.seal.replace(old, new, 1)), new)


# ================================================================ (c) 判定
class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def J(self, p1=None, **ov):
        return PS.judge_from(p1 or sample_ps1(), sample_cols(**ov), self.seal)

    def test_c_1_the_middle_of_every_range_is_a_hit_and_adoption_follows(self):
        J = self.J()
        for k, v in J[u"PS"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        for k, v in J[u"K"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        self.assertTrue(J[u"採用"])

    def test_c_2_each_prediction_flips_at_the_seal_boundary(self):
        b = BOUNDS_PIN
        cases = []
        for k, (lo, hi) in b["PS-2"].items():
            cases += [("PS-2", KEY["PS-2"] + SEP + k, lo, lo - 1), ("PS-2", KEY["PS-2"] + SEP + k, hi, hi + 1)]
        for k, (lo, hi) in b["PS-3"].items():
            step = 0.1 if k == u"割合" else 1
            cases += [("PS-3", KEY["PS-3"] + SEP + k, lo, lo - step), ("PS-3", KEY["PS-3"] + SEP + k, hi, hi + step)]
        lo, hi = b["PS-4"]
        cases += [("PS-4", KEY["PS-4"] + SEP + u"通した率(P30E)", lo, lo - 0.1), ("PS-4", KEY["PS-4"] + SEP + u"通した率(P30E)", hi, hi + 0.1)]
        lo, hi = b["PS-5"]
        cases += [("PS-5", KEY["PS-5"] + SEP + u"割合", lo, lo - 0.1), ("PS-5", KEY["PS-5"] + SEP + u"割合", hi, hi + 0.1)]
        for k, (lo, hi) in b["PS-6"].items():
            cases += [("PS-6", KEY["PS-6"] + SEP + k, lo, lo - 0.1), ("PS-6", KEY["PS-6"] + SEP + k, hi, hi + 0.1)]
        cases += [("PS-7", KEY["PS-7"] + SEP + u"うち届かない行", 0, 1)]
        lo, hi = b["PS-8"]
        cases += [("PS-8", KEY["PS-8"] + SEP + u"違う行", lo, lo - 1), ("PS-8", KEY["PS-8"] + SEP + u"違う行", hi, hi + 1)]
        cases += [("PS-9", KEY["PS-9"] + SEP + u"round-trip 不一致", 0, 1), ("PS-9", KEY["PS-9"] + SEP + u"読み直し不一致", 0, 1),
                  ("PS-9", KEY["PS-9"] + SEP + u"先頭の位が減った行", 0, -1), ("PS-9", KEY["PS-9"] + SEP + u"先頭の位が減った行", 15, 16)]
        lo, hi = b["PS-10"]
        cases += [("PS-10", KEY["PS-10"] + SEP + u"割合", lo, lo - 0.1), ("PS-10", KEY["PS-10"] + SEP + u"割合", hi, hi + 0.1)]
        for cid, path, inside, outside in cases:
            self.assertEqual(HIT, self.J(**{path: inside})[u"PS"][cid][u"判定"], (path, inside))
            self.assertEqual(MISS, self.J(**{path: outside})[u"PS"][cid][u"判定"], (path, outside))

    def test_c_2b_a_missing_value_is_a_miss_not_a_hit(self):
        for cid, path in (("PS-3", KEY["PS-3"] + SEP + u"割合"), ("PS-4", KEY["PS-4"] + SEP + u"通した率(P30E)"), ("PS-5", KEY["PS-5"] + SEP + u"割合"),
                          ("PS-6", KEY["PS-6"] + SEP + u"手がかり真の行の通した率"), ("PS-6", KEY["PS-6"] + SEP + u"手がかり真の割合"), ("PS-10", KEY["PS-10"] + SEP + u"割合")):
            self.assertEqual(MISS, self.J(**{path: None})[u"PS"][cid][u"判定"], path)             # 分母が 0 で率が出ない = 外れ(当たりにしない)
        c = sample_cols()
        del c[KEY["PS-2"]][u"手がかり真"]
        self.assertRaises(KeyError, PS.judge_from, sample_ps1(), c, self.seal)                    # 欄が欠けた記録は判定を作れない = 赤(当たりにしない)

    def test_c_2c_ps1_needs_the_three_agreements(self):
        for ov in ({INFO_PS1[0]: False}, {INFO_PS1[1]: False}, {INFO_PS1[2]: 1}, {INFO_PS1[2]: None}):
            J = self.J(p1=sample_ps1(**ov))
            self.assertEqual(MISS, J[u"PS"]["PS-1"][u"判定"], ov)
            self.assertEqual(MISS, J[u"K"]["K-1"][u"判定"], ov)
            self.assertFalse(J[u"採用"])

    def test_c_3_the_adoption_follows_k1_to_k4(self):
        self.assertFalse(self.J(p1=sample_ps1(**{INFO_PS1[0]: False}))[u"採用"])                                                              # K-1
        for k, path in (("round-trip", KEY["PS-9"] + SEP + u"round-trip 不一致"), ("読み直し", KEY["PS-9"] + SEP + u"読み直し不一致")):         # K-2
            J = self.J(**{path: 1})
            self.assertEqual(MISS, J[u"K"]["K-2"][u"判定"], k)
            self.assertFalse(J[u"採用"])
        mapped = KEY["PS-6"] + SEP + u"対応が付く行"                                                                                         # K-3
        self.assertEqual(HIT, self.J(**{mapped: 80})[u"K"]["K-3"][u"判定"])
        J = self.J(**{mapped: 79})
        self.assertEqual(MISS, J[u"K"]["K-3"][u"判定"])
        self.assertFalse(J[u"採用"])
        J = self.J(**{KEY["PS-7"] + SEP + u"うち届かない行": 1})                                                                              # K-4
        self.assertEqual(MISS, J[u"K"]["K-4"][u"判定"])
        self.assertFalse(J[u"採用"])

    def test_c_4_k3_uses_the_mapped_rows_not_the_site_counts_and_k_ignores_the_prediction_misses(self):
        J = self.J(**{KEY["PS-2"] + SEP + u"計": 100, KEY["PS-3"] + SEP + u"採った": 10, KEY["PS-3"] + SEP + u"うち土台 P30E が GROUNDED の行": 10})
        self.assertEqual(MISS, J[u"PS"]["PS-2"][u"判定"])
        self.assertEqual(MISS, J[u"PS"]["PS-3"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-3"][u"判定"])                                   # K-3 は対応が付く行(PS-6 の欄)だけを見る
        self.assertTrue(J[u"採用"])
        J = self.J(**{KEY["PS-4"] + SEP + u"通した率(P30E)": 99.0, KEY["PS-5"] + SEP + u"割合": 10.0})
        self.assertEqual(MISS, J[u"PS"]["PS-4"][u"判定"])
        self.assertTrue(J[u"採用"])                                                      # 採用は K だけで決まる(率が高くても採用は採用)

    def test_c_5_the_judgment_moves_with_the_records(self):
        base = self.J()
        mutated_seal = self.seal.replace("205〜230", "205〜217", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertEqual(MISS, PS.judge_from(sample_ps1(), sample_cols(), mutated_seal)[u"PS"]["PS-2"][u"判定"])
        self.assertNotEqual(norm(base), norm(self.J(**{KEY["PS-8"] + SEP + u"違う行": 4})))

    def test_c_6_a_broken_record_is_red_not_an_exception(self):
        R = norm(sample_records())
        self.assertEqual([], judge_problems(R, self.seal))
        del R["inject"][u"本ごとの数え"]
        self.assertNotEqual([], judge_problems(R, self.seal))
        R2 = norm(sample_records())
        R2["h"].pop(u"lib の指紋")
        self.assertEqual(MISS, PS.build_PS(R2, self.seal, [])[u"PS"]["PS-1"][u"判定"])
        R3 = norm(sample_records())
        R3["rb"].pop(u"engine の指紋")
        self.assertEqual(MISS, PS.build_PS(R3, self.seal, [])[u"PS"]["PS-1"][u"判定"])

    def test_c_7_the_judgment_follows_the_columns_counted_from_the_rows_not_the_recorded_columns(self):
        R = norm(sample_records())
        J = PS.build_PS(R, self.seal, [])
        R["inject"][PS.PS_KEY][KEY["PS-9"]][u"round-trip 不一致"] = 7                          # 記録の PS の欄だけ変えても判定は動かない(行から数え直す)
        self.assertEqual(norm(J), norm(PS.build_PS(R, self.seal, [])))
        R["inject"][u"行"][0][u"round-trip"] = False                                       # 行を変えると PS-9 が動く
        self.assertEqual(MISS, PS.build_PS(R, self.seal, [])[u"PS"]["PS-9"][u"判定"])
        self.assertEqual(MISS, PS.build_PS(R, self.seal, [])[u"K"]["K-2"][u"判定"])

    def test_c_8_the_ps1_inputs_come_from_the_records_and_the_numstat(self):
        R = norm(sample_records())
        ok = PS.ps1_value(R["inject"], R["h"], R["rb"], [])
        self.assertEqual((True, True, 0), tuple(ok.values()))
        R2 = copy.deepcopy(R)
        R2["inject"][u"lib の指紋"][LIB_RELS[0]] = "0" * 64
        self.assertFalse(PS.ps1_value(R2["inject"], R2["h"], R2["rb"], [])[INFO_PS1[0]])
        R3 = copy.deepcopy(R)
        R3["inject"][u"engine の指紋"]["core_py_sha256"] = "0" * 64
        self.assertFalse(PS.ps1_value(R3["inject"], R3["h"], R3["rb"], [])[INFO_PS1[1]])
        R4 = copy.deepcopy(R)
        R4["inject"][u"engine の指紋"]["git_commit"] = "9" * 40                                # git_commit は比べない(記録ごとに違う)
        self.assertTrue(PS.ps1_value(R4["inject"], R4["h"], R4["rb"], [])[INFO_PS1[1]])
        self.assertEqual(1, PS.ps1_value(R["inject"], R["h"], R["rb"], ["1\t0\tmeasure/inject.py"])[INFO_PS1[2]])
        self.assertIsNone(PS.ps1_value(R["inject"], R["h"], R["rb"], None)[INFO_PS1[2]])
        R5 = copy.deepcopy(R)
        R5["inject"].pop(u"lib の指紋")
        self.assertFalse(PS.ps1_value(R5["inject"], R5["h"], R5["rb"], [])[INFO_PS1[0]])
        seal = read(SEAL_REL)
        self.assertEqual(MISS, PS.build_PS(R, seal, None)[u"PS"]["PS-1"][u"判定"])                    # git が読めなかったら外れ(作業木の答えで代えない)
        self.assertEqual(HIT, PS.build_PS(R, seal, [])[u"PS"]["PS-1"][u"判定"])
        calls = []
        with Patch() as pt:
            pt.set(PS, "git_numstat_since_seal", lambda root=ROOT: calls.append(1) or ["1\t0\tmeasure/inject.py"])
            self.assertEqual(MISS, PS.build_PS(R, seal)[u"PS"]["PS-1"][u"判定"])                       # 省略したら git に聞く
        self.assertEqual([1], calls)

    def test_c_9_the_numstat_since_the_seal_is_empty_in_the_real_tree_and_not_in_a_changed_one(self):
        # 2026-11-06(T5Y): 封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §2-1 が宣言した遷移(仕掛けの 2 file に挿入だけ)は実物の木の numstat から外す(SGR.t5y_declared_numstat)
        self.assertEqual([], [x for x in PS.git_numstat_since_seal(ROOT) if not SG.SGR.t5y_declared_numstat(x)])
        r = PR.Repo()
        r.put("measure/inject.py")
        r.put("measure/lib/sites.py")
        r.put("x.md")
        sh = r.commit("measure/inject.py", "measure/lib/sites.py", "x.md")
        base = os.path.join(r.d, "audit-core")
        old = PS.SEAL_COMMIT
        try:
            PS.SEAL_COMMIT = sh[:7]
            self.assertEqual([], PS.git_numstat_since_seal(base))
            with open(os.path.join(base, "measure/lib/sites.py"), "a", encoding="utf-8") as fh:
                fh.write("x = 1\n")
            self.assertEqual(1, len(PS.git_numstat_since_seal(base)))
            PS.SEAL_COMMIT = "0000000"
            self.assertIsNone(PS.git_numstat_since_seal(base))                             # 読めなければ None(当たりにしない)
        finally:
            PS.SEAL_COMMIT = old


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

    def test_g_1_the_sample_exercises_a_skipped_book_unlinked_rows_unmapped_rows_and_every_column(self):
        inj = self.R["inject"]
        self.assertIn(u"注入しない", inj[u"本ごとの数え"][u"DOC2_F5_m2"])
        self.assertEqual({u"全体": 1, T9: 1}, dict(inj[u"P29E に対応なしの行の数"]))
        cols = inj[PS.PS_KEY]
        self.assertEqual(1, cols[KEY["PS-9"]][u"先頭の位が減った行"])
        self.assertEqual(3, cols[KEY["PS-5"]][u"通した行"])
        self.assertEqual(3, cols[KEY["PS-5"]][u"うち注入後の pointer の期が CurrentYear"])
        self.assertEqual(6, cols[KEY["PS-6"]][u"対応が付く行"])                                    # 7 行のうち P30E に対応が付かない 1 行を除く
        self.assertEqual((3, 5), (cols[KEY["PS-8"]][u"違う行"], cols[KEY["PS-8"]][u"両方に対応が付く行"]))

    def _red(self, mutate, **kw):
        R = copy.deepcopy(self.R)
        mutate(R)
        self.assertNotEqual([], record_problems(R, full=False), kw)

    def test_g_2_one_number_in_a_record_turns_it_red(self):
        inj = lambda f: (lambda R: f(R["inject"]))
        self._red(inj(lambda r: r[u"行"][0]["P30E"].__setitem__(u"結果", TUNE.LABEL_PASS)))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"round-trip", u"はい")))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"単位", u"")))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"形", u"全部")))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"型", u"T6_PRIOR")))
        self._red(inj(lambda r: r[u"行"][2].__setitem__(u"先頭の位が減った", True)))                           # 既存の行は減らない
        self._red(inj(lambda r: r[u"行"][3].__setitem__(u"届いた", u"はい")))
        self._red(inj(lambda r: r[u"行"][4].__setitem__(u"届いた", True)))                                    # P30E に対応が付かない行は届かない
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"engine の手がかり", u"はい")))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"文に前期の語", 1)))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"基準の pointer の期", u"前期")))                    # 4 つの語でない
        self._red(inj(lambda r: r[u"行"][1].__setitem__(u"注入後の pointer の期", u"当期")))
        self._red(inj(lambda r: r[u"行"][4].__setitem__(u"注入後の pointer の期", u"CurrentYear")))          # 対応が付かない行は なし
        self._red(inj(lambda r: r[u"行"][0].__setitem__("id", r[u"行"][1]["id"])))
        self._red(inj(lambda r: r[u"集計"][T9]["P30E"][u"全体"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r[PS.BREAKDOWN_KEY][u"複合"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r[PS.CUE_KEY][u"真"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r[PS.PERIOD_KEY].__setitem__(u"CurrentYear", 9)))
        self._red(inj(lambda r: r[u"型"].__setitem__(u"土台", u"無改変の文で P29E が GROUNDED の claim")))
        self._red(inj(lambda r: r[u"型"].__setitem__(u"site", u"全部の site")))
        self._red(inj(lambda r: r[u"限界"].pop()))
        self._red(inj(lambda r: r[u"限界"].__setitem__(0, u"別の限界")))
        self._red(inj(lambda r: r.pop(PS.COMPARE_KEY)))
        self._red(inj(lambda r: r[PS.COMPARE_KEY][T9]["P29E"][u"全体"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r.pop(PS.BREAKDOWN_KEY)))
        self._red(inj(lambda r: r.pop(PS.CUE_KEY)))
        self._red(inj(lambda r: r.pop(PS.PERIOD_KEY)))

    def test_g_2b_every_column_of_the_ps_record_is_recounted_from_the_rows_and_the_counts(self):
        u"""PS の欄の全部(PS-2〜PS-10 と参考の欄)を 0 に固定すると赤。記録の欄を直しても行・数えと食い違えば赤。"""
        cols = self.R["inject"][PS.PS_KEY]

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
            d = R["inject"][PS.PS_KEY]
            for k in path[:-1]:
                d = d[k]
            d[path[-1]] = 0 if v != 0 else 1                       # 0 に固定(元が 0 なら 1)
            self.assertNotEqual([], record_problems(R, full=False), path)
            n += 1
        self.assertGreaterEqual(n, 30)
        R = copy.deepcopy(self.R)
        R["inject"].pop(PS.PS_KEY)
        self.assertNotEqual([], record_problems(R, full=False))

    def test_g_2c_the_script_columns_function_zeroed_in_one_column_turns_the_record_red(self):
        u"""script の ``ps_columns`` が欄を 0 に固定する変異(記録は正しい欄で作ってある)で赤。"""
        real = PS.ps_columns
        paths = [(KEY["PS-2"], u"計"), (KEY["PS-2"], u"既存"), (KEY["PS-2"], u"手がかり真"), (KEY["PS-3"], u"採った"), (KEY["PS-3"], u"うち土台 P30E が GROUNDED の行"),
                 (KEY["PS-3"], u"うち基準の pointer の期が Prior1Year の行"), (KEY["PS-3"], u"割合"), (KEY["PS-4"], u"通した率(P30E)"), (KEY["PS-4"], u"通した行"),
                 (KEY["PS-5"], u"うち注入後の pointer の期が CurrentYear"), (KEY["PS-5"], u"割合"), (KEY["PS-6"], u"うち手がかり真"), (KEY["PS-6"], u"手がかり真の行の通した率"),
                 (KEY["PS-7"], u"通した行"), (KEY["PS-8"], u"違う行"), (KEY["PS-9"], u"先頭の位が減った行"), (KEY["PS-10"], u"止めた行"), (KEY["PS-10"], u"うち名指して原本"),
                 (KEY["REF"], u"届いた行"), (KEY["REF"], u"文に前期の語がある行"), (KEY["REF"], u"手がかり真の行(全部)")]
        for path in paths:
            def fixed(per, rows, path=path):
                c = real(per, rows)
                d = c
                for k in path[:-1]:
                    d = d[k]
                d[path[-1]] = 0
                return c
            with Patch() as pt:
                pt.set(PS, "ps_columns", fixed)
                self.assertNotEqual([], record_problems(copy.deepcopy(self.R), full=False), path)
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=False))

    def test_g_2d_a_row_field_changes_exactly_the_columns_it_feeds(self):
        per, rows = self.R["inject"][u"本ごとの数え"], self.R["inject"][u"行"]
        base = norm(PS.ps_columns(per, rows))
        self.assertEqual(
            {KEY["PS-2"]: {u"計": 9, u"既存": 3, u"万だけ": 1, u"複合": 5, u"手がかり真": 6},
             KEY["PS-3"]: {u"採った": 9, u"うち土台 P30E が GROUNDED の行": 7, u"うち基準の pointer の期が Prior1Year の行": 6, u"割合": 85.7},
             KEY["PS-4"]: {u"通した率(P30E)": 50.0, u"通した行": 3, u"対応が付く行": 6},
             KEY["PS-5"]: {u"通した行": 3, u"うち注入後の pointer の期が CurrentYear": 3, u"割合": 100.0},
             KEY["PS-6"]: {u"対応が付く行": 6, u"うち手がかり真": 5, u"手がかり真の割合": 83.3, u"手がかり真の行の通した率": 40.0},
             KEY["PS-7"]: {u"通した行": 3, u"うち届かない行": 0},
             KEY["PS-8"]: {u"違う行": 3, u"両方に対応が付く行": 5},
             KEY["PS-9"]: {u"round-trip 不一致": 0, u"読み直し不一致": 0, u"先頭の位が減った行": 1},
             KEY["PS-10"]: {u"対応が付く行": 6, u"止めた行": 3, u"うち名指して原本": 2, u"割合": 66.7},
             KEY["REF"]: {u"届いた行": 6, u"文に前期の語がある行": 6, u"手がかり真の行(全部)": 6}}, base)
        ref = KEY["REF"]
        for idx, key, val, where, feeds in (
                (0, u"round-trip", False, (KEY["PS-9"], u"round-trip 不一致"), [KEY["PS-9"]]),
                (0, u"読み直し", False, (KEY["PS-9"], u"読み直し不一致"), [KEY["PS-9"]]),
                (0, u"先頭の位が減った", True, (KEY["PS-9"], u"先頭の位が減った行"), [KEY["PS-9"]]),
                (1, u"届いた", False, (KEY["PS-7"], u"うち届かない行"), [KEY["PS-7"], ref]),
                (0, u"engine の手がかり", False, (KEY["PS-6"], u"うち手がかり真"), [KEY["PS-6"], ref]),
                (2, u"engine の手がかり", True, (KEY["PS-6"], u"うち手がかり真"), [KEY["PS-6"], ref]),
                (0, u"文に前期の語", False, (ref, u"文に前期の語がある行"), [ref]),
                (0, u"基準の pointer の期", u"他", (KEY["PS-3"], u"うち基準の pointer の期が Prior1Year の行"), [KEY["PS-3"]]),
                (2, u"基準の pointer の期", u"Prior1Year", (KEY["PS-3"], u"うち基準の pointer の期が Prior1Year の行"), [KEY["PS-3"]]),
                (1, u"注入後の pointer の期", u"Prior1Year", (KEY["PS-5"], u"うち注入後の pointer の期が CurrentYear"), [KEY["PS-5"]])):
            r2 = copy.deepcopy(rows)
            r2[idx][key] = val
            c2 = norm(PS.ps_columns(per, r2))
            self.assertNotEqual(base[where[0]][where[1]], c2[where[0]][where[1]], (key, where))
            changed = [k for k in base if base[k] != c2[k]]
            self.assertEqual(feeds, changed, (key, changed))                                                      # 動くのはその欄が餌にする欄だけ
        r2 = copy.deepcopy(rows)
        r2[1]["P30E"] = cell(*NAMED)                                                                              # 通した行が名指しに: PS-4・PS-5・PS-6・PS-7・PS-8・PS-10 が動く
        c2 = norm(PS.ps_columns(per, r2))
        self.assertEqual(2, c2[KEY["PS-5"]][u"通した行"])
        self.assertEqual(4, c2[KEY["PS-10"]][u"止めた行"])

    def test_g_2e_a_consistently_edited_count_still_breaks_the_invariants(self):
        u"""本ごとの数えを直してから PS の欄も作り直しても(欄との食い違いでは見つからない)、数えの欄の間の関係と行との関係で赤になる。"""
        def reh(R):
            R["inject"][PS.PS_KEY] = norm(PS.ps_columns(R["inject"][u"本ごとの数え"], R["inject"][u"行"]))
        for mutate in (lambda c: c.__setitem__(u"採った", 3), lambda c: c.__setitem__(u"土台 P30E が GROUNDED の site", 9), lambda c: c.__setitem__(u"cap を基準で絞る前に掛けた数", 9),
                       lambda c: c[u"作れる site"].__setitem__(u"複合", 9), lambda c: c[u"作れる site"].__setitem__(u"既存", 0), lambda c: c[u"作れる site の手がかり"].__setitem__(u"真", 9),
                       lambda c: c[u"作れる site の手がかり"].__setitem__(u"真", 0), lambda c: c[u"作れる site の状態"].__setitem__(PS.LINKED, 9),
                       lambda c: c[u"採った の状態"].__setitem__(PS.LINKED, 9), lambda c: c[u"採った の状態"].__setitem__(PS.STATUS_NOT_G, 1),
                       lambda c: c[u"段"].__setitem__(u"site", 9), lambda c: c[u"段"].__setitem__(u"単位が同じ・両方正・値が違う", 1), lambda c: c[u"段"].__setitem__(u"参照先が Prior1Year", 0),
                       lambda c: c[u"段"].pop(u"site")):
            R = copy.deepcopy(self.R)
            mutate(R["inject"][u"本ごとの数え"][u"DOC1_F1_m1"])
            try:
                reh(R)
            except Exception:                                   # noqa: BLE001  PS の欄を作れない形も赤(record_problems が例外を問題に数える)
                pass
            self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        R["inject"][u"本ごとの数え"][u"DOC2_F5_m2"].pop(u"注入しない")                               # 注入しない本に数えを置かずに印だけ消した
        self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        R["inject"][u"本ごとの数え"][u"DOC2_F5_m2"][u"採った"] = 0                                  # 注入しない本に数えを置いた
        self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        reh(R)
        self.assertEqual([], record_problems(R, full=False))

    def test_g_2f_cap_and_linked_counts_are_checked_on_their_own(self):
        R = copy.deepcopy(self.R)
        row = R["inject"][u"行"][0]
        R["inject"][u"行"] = [dict(row, id=u"DOC1_F1_m1-T9-%02d" % (i + 1)) for i in range(RUN.INJECT_CAP + 1)]
        R["inject"][u"注入の行の数"] = len(R["inject"][u"行"])
        with Patch() as pt:
            pt.set(RUN, "PROFILES", INJECT_PROFILES)
            R["inject"][u"集計"], R["inject"][PS.COMPARE_KEY] = (norm(x) for x in PS.inject_summaries(R["inject"][u"行"]))
        R["inject"][u"P29E に対応なしの行の数"] = collections.OrderedDict([(u"全体", 0), (T9, 0)])
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

    def test_g_3_a_forbidden_key_or_a_key_or_a_company_name_or_a_pointer_text_turns_it_red(self):
        for key in (u"span", u"value", u"recomputed", u"文", u"sentence", u"数", u"理由", u"pointers", u"pointer", u"要素", u"element", u"context", u"label"):
            self._red(lambda R, key=key: R["inject"][u"行"][0].__setitem__(key, 1))
        self._red(lambda R: R["inject"].__setitem__(u"メモ", u"株式会社テスト"))
        self._red(lambda R: R["inject"].__setitem__(u"メモ", u"sk-" + u"a" * 20))
        self._red(lambda R: R["inject"].__setitem__(u"key_leaks", [u"鍵の形"]))
        for text in (PTR_PRIOR, PTR_CUR, u"jppfs_cor:NetSales", u"x@CurrentYearDuration", u"y@Prior1YearInstant", u"jpcrp_cor:Foo"):          # pointer の字(要素名・context)を持たない
            self._red(lambda R, text=text: R["inject"][u"行"][0].__setitem__(u"メモ", text))
            self._red(lambda R, text=text: R["inject"][u"型"].__setitem__(u"メモ", text))

    def test_g_4_one_character_of_the_fingerprints_or_the_script_sha_turns_it_red(self):
        for name in (u"この script の sha256", u"J の script の sha256", u"nscan script の sha256", u"rmix script の sha256", u"numfix script の sha256", u"前の便の run script の sha256",
                     u"生成の script の sha256", u"J の記録の sha256", u"H の記録の sha256", u"RB の記録の sha256"):
            self.assertIn(name, self.R["inject"])
            self._red(lambda R, name=name: R["inject"].__setitem__(name, "e" * 64))
            self._red(lambda R, name=name: R["inject"].pop(name))
        fp = lambda R: R["inject"][u"engine の指紋"]
        self._red(lambda R: fp(R).__setitem__("adapter_xbrl_py_sha256", fp(R)["adapter_xbrl_py_sha256"][:-1] + ("0" if fp(R)["adapter_xbrl_py_sha256"][-1] != "0" else "1")))
        self._red(lambda R: fp(R).__setitem__("core_py_sha256", "f" * 64))
        self._red(lambda R: R["inject"].__setitem__(u"封の commit", u"0000000"))
        self._red(lambda R: R["inject"].__setitem__(u"seal", u"docs/other.md"))
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
        i = lines.index(u"<!-- 門:start pred -->") + 3                  # 表の 1 行目(PS-1)
        for col_char in (u"P", u"一", u"当"):
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
        mutated_seal = self.seal.replace("205〜230", "205〜231", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertNotEqual([], doc_problems(doc, self.R, mutated_seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"門:start judge", u"門:start other"), self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"<!-- 門:start judge -->", u"<!-- 門:start judge2 -->", 1), self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc, self.R, self.seal, numstat=["1\t0\tmeasure/inject.py"]))      # PS-1 の行が変わる

    def test_g_7_forbidden_words_docids_and_ungated_numbers_turn_the_document_red(self):
        doc = sample_doc(self.R, self.seal)
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(doc + u"\n" + w + u"。\n", self.R, self.seal), w)
        self.assertNotEqual([], doc_problems(doc + u"\nS100" + u"ABCD の文。\n", self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n新しい token は 1234 でした。\n", self.R, self.seal))
        self.assertEqual([], doc_problems(doc + u"\n新しい token は 1234 でした。" + NOT_GATED + u"\n", self.R, self.seal))

    def test_g_8_the_judge_table_ends_with_the_adoption_line(self):
        J = PS.build_PS(self.R, self.seal, [])
        t = PS.render_judge(J, self.seal).split(u"\n")
        self.assertEqual(u"採用の判定(K-1〜K-4 を全部満たす): **%s**。最後に決めるのは人間。" % (u"採用" if J[u"採用"] else u"見送り"), t[-1])
        J2 = PS.build_PS(self.R, self.seal, ["1\t0\tmeasure/inject.py"])
        self.assertFalse(J2[u"採用"])
        self.assertIn(u"**見送り**", PS.render_judge(J2, self.seal))
        self.assertEqual(u"| # | 欄 | 予測 | 測った値 | 判定 |", PS.render_pred(J, self.seal).split(u"\n")[0])
        self.assertEqual(10 + 2, len(PS.render_pred(J, self.seal).split(u"\n")))
        self.assertEqual(4 + 2 + 2, len(t))


WRONG_FLAG = "compound_yen_2026_11_05"


# ================================================================ (w) 手順・行の欄(script の関数を小さい入力で通す。zip・判定は偽。lib は本物。通信なし)
TEXT_P = u"前期は9億7,000万円でした。前期の1,000百万円でした。前期は5,000千円でした。"
REFS_P = [{"key": "jppfs:NetSales@CurrentYearDuration", "value": 1234560000.0, "unit": u"円", "label": u"売上高"},
          {"key": "jppfs:NetSales@Prior1YearDuration", "value": 970000000.0, "unit": u"円", "label": u"売上高"},
          {"key": "jppfs:GrossProfit@CurrentYearDuration", "value": 1200000000.0, "unit": u"円", "label": u"粗利益"},
          {"key": "jppfs:GrossProfit@Prior1YearDuration", "value": 1000000000.0, "unit": u"円", "label": u"粗利益"},
          {"key": "jppfs:Cost@CurrentYearDuration", "value": 6000000.0, "unit": u"円", "label": u"費用"},
          {"key": "jppfs:Cost@Prior1YearDuration", "value": 5000000.0, "unit": u"円", "label": u"費用"}]


def make_verify(text0, base_ptr=PTR_PRIOR, inj_state=V_, inj_ptr=None):
    u"""無改変の文の数は GROUNDED(pointers = base_ptr)、注入した文で増えた数(字が元の文に無い claim)は inj_state(pointers = inj_ptr。省略なら base_ptr)。lib の ``N.scan`` で読む。"""
    def verify(zb, p, t):
        claims = []
        for i, tok in enumerate(N.scan(t)):
            if tok.unit is None:
                continue
            span = t[tok.start:tok.unit_end]
            base = span in text0
            claims.append({"id": "N%03d" % (i + 1), "kind": "num", "value": tok.value, "unit": tok.unit, "span": span, "state": G if base else inj_state,
                           "pointers": [base_ptr if base else (inj_ptr or base_ptr)], "recomputed": 1.0, "reason": None})
        return {"claims": claims}
    return verify


def run_ps(text=TEXT_P, refs=REFS_P, patches=(), seed=u"sd", key=u"bk", verify=None):
    with Patch() as pt, PS.yen_scan_on():
        pt.set(RUN, "PROFILES", INJECT_PROFILES)
        for mod, name, v in patches:
            pt.set(mod, name, v)
        return PS.inject_text_ps(b"zip", text, refs, seed, key, verify=verify or make_verify(text))


class ProcedureTest(unittest.TestCase):
    def test_w_1_rows_come_from_the_site_population_and_carry_every_column(self):
        rows, c = run_ps()
        self.assertEqual(3, len(rows))
        self.assertEqual([], sorted(set(k for r in rows for k in RUN.walk_keys(r) if k in FORBIDDEN_KEYS)))           # 行に repo へ入れない欄を持たない
        self.assertEqual({u"既存": 2, u"万だけ": 0, u"複合": 1}, dict(c[u"作れる site"]))
        self.assertEqual({u"真": 3, u"偽": 0}, dict(c[u"作れる site の手がかり"]))
        self.assertEqual(3, c[u"採った"])
        self.assertEqual({PS.LINKED: 3}, dict(c[u"採った の状態"]))
        self.assertEqual(3, c[u"土台 P30E が GROUNDED の site"])
        self.assertEqual({u"参照先が Prior1Year": 3, u"同じ要素の CurrentYear が 1 件": 3, u"単位が同じ・両方正・値が違う": 3, u"site": 3}, dict(c[u"段"]))
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))
        want_keys = [u"id", u"型", u"形", u"単位", u"基準の claim", LINK_KEY, u"round-trip", u"読み直し", u"先頭の位が減った", u"engine の手がかり", u"文に前期の語", u"基準の pointer の期", "P29E", "P30E",
                     u"注入後の pointer の期", u"届いた"]
        for r in rows:
            self.assertEqual(want_keys, list(r))
            self.assertEqual(T9, r[u"型"])
        self.assertEqual(sorted([u"既存", u"既存", u"複合"]), sorted(r[u"形"] for r in rows))
        self.assertEqual(["bk-T9-01", "bk-T9-02", "bk-T9-03"], [r[u"id"] for r in rows])
        self.assertEqual([], [x for r in rows for x in row_problems(dict(r, docID=u"D", form=u"F", model=u"m", id=u"D_F_m-" + r[u"id"][3:]), (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER,
                                                                                                                                              TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED), set())])

    def test_w_2_the_row_columns_are_true_for_an_honest_injection(self):
        rows, _c = run_ps()
        for r in rows:
            self.assertTrue(r[u"round-trip"], r)
            self.assertTrue(r[u"読み直し"], r)
            self.assertFalse(r[u"先頭の位が減った"], r)
            self.assertTrue(r[u"届いた"], r)
            self.assertTrue(r[u"engine の手がかり"], r)
            self.assertTrue(r[u"文に前期の語"], r)
            self.assertTrue(r[LINK_KEY], r)
            self.assertTrue(r["P30E"][u"対応"] and r["P29E"][u"対応"], r)
            self.assertEqual(TUNE.LABEL_NAMED_ORIGINAL, r["P30E"][u"結果"])
            self.assertEqual((u"Prior1Year", u"Prior1Year"), (r[u"基準の pointer の期"], r[u"注入後の pointer の期"]))

    def test_w_3_round_trip_is_false_when_the_revert_does_not_give_the_original_back(self):
        real = IJ.revert
        rows, _c = run_ps(patches=((IJ, "revert", lambda tampered, chosen, placements, original: tampered),))          # 壊した revert(差し替えを戻さない)
        self.assertEqual([False, False, False], [r[u"round-trip"] for r in rows])
        self.assertTrue(all(r[u"読み直し"] for r in rows))                                  # 他の欄は動かない
        rows, _c = run_ps(patches=((IJ, "revert", lambda tampered, chosen, placements, original: real(tampered, chosen, placements, original) + u"。"),))
        self.assertEqual([False, False, False], [r[u"round-trip"] for r in rows])
        rows, _c = run_ps()
        self.assertEqual([True, True, True], [r[u"round-trip"] for r in rows])

    def test_w_4_reread_is_false_when_the_text_carries_another_value_or_unit(self):
        real = IJ.apply_edits

        def other_value(text, chosen):
            return real(text, [dict(c, replacement=u"9" + c["replacement"]) for c in chosen])             # 先頭に 1 字足して値を変える
        rows, _c = run_ps(patches=((IJ, "apply_edits", other_value),))
        self.assertEqual([False, False, False], [r[u"読み直し"] for r in rows])
        self.assertTrue(all(r[u"round-trip"] for r in rows))                                  # round-trip は revert が元の字を持つので別の欄

        def drop_unit(text, chosen):
            out, pl = real(text, chosen)
            return out.replace(u"万円", u"", 1).replace(u"百万円", u"", 1).replace(u"千円", u"", 1), pl
        rows, _c = run_ps(patches=((IJ, "apply_edits", drop_unit),))
        self.assertFalse(all(r[u"読み直し"] for r in rows))
        rows, _c = run_ps()
        self.assertEqual([True, True, True], [r[u"読み直し"] for r in rows])

    def test_w_5_the_leading_group_column_is_true_only_for_a_compound_that_loses_a_group(self):
        text = u"前期の売上高は1億500万円でした。"                 # 前期 1億500万円 → 当期 9,700万円(先頭の位の「億」が落ちる複合)
        refs = [{"key": "jppfs:NetSales@CurrentYearDuration", "value": 97000000.0, "unit": u"円", "label": u"売上高"},
                {"key": "jppfs:NetSales@Prior1YearDuration", "value": 105000000.0, "unit": u"円", "label": u"売上高"}]
        rows, _c = run_ps(text=text, refs=refs)
        self.assertEqual(1, len(rows))
        self.assertEqual((u"複合", True, True, True), (rows[0][u"形"], rows[0][u"先頭の位が減った"], rows[0][u"読み直し"], rows[0][u"round-trip"]))
        rows, _c = run_ps()                                   # 位が減らない複合・既存
        self.assertEqual([False, False, False], [r[u"先頭の位が減った"] for r in rows])
        self.assertEqual(3, NS.groups_in(u"1兆2億3,456"))
        self.assertEqual(2, NS.groups_in(u"12億3,456"))
        self.assertEqual(1, NS.groups_in(u"9,700"))

    def test_w_6_reach_needs_the_original_digits_in_the_base_span_and_the_new_digits_in_the_injected_span(self):
        def verify_changed(text0, on_base=None, on_inj=None):
            base = make_verify(text0)

            def v(zb, p, t):
                out = base(zb, p, t)
                for cl in out["claims"]:
                    if t == text0 and on_base:
                        cl["span"] = on_base(cl["span"])
                    elif t != text0 and cl["state"] == V_ and on_inj:
                        cl["span"] = on_inj(cl["span"])
                return out
            return v
        rows, _c = run_ps(verify=verify_changed(TEXT_P, on_inj=lambda s: s[:1]))                  # 注入後の claim の span が差し替えの字を運ばない
        self.assertTrue(rows)
        self.assertFalse(any(r[u"届いた"] for r in rows))
        rows, _c = run_ps(verify=verify_changed(TEXT_P, on_base=lambda s: u"x" + s[-2:]))          # 基準の claim の span が元の字を運ばない
        self.assertTrue(rows)
        self.assertFalse(any(r[u"届いた"] for r in rows))
        rows, _c = run_ps()
        self.assertTrue(all(r[u"届いた"] for r in rows))

    def test_w_6c_reach_and_the_post_pointer_period_come_from_the_p30e_claim_not_the_p29e_one(self):
        def by_profile(good, bad):
            base = make_verify(TEXT_P, base_ptr=PTR_PRIOR, inj_state=V_, inj_ptr=PTR_PRIOR)
            other = make_verify(TEXT_P, base_ptr=PTR_PRIOR, inj_state=V_, inj_ptr=PTR_CUR)

            def v(zb, p, t):
                out = base(zb, p, t)
                if t != TEXT_P and p == bad:
                    out = other(zb, p, t)
                    for cl in out["claims"]:
                        if cl["state"] == V_:
                            cl["span"] = cl["span"][:1]                     # この profile の注入後の claim は差し替えの字を運ばない
                return out
            return v
        rows, _c = run_ps(verify=by_profile("P30E", "P29E"))                # P29E だけ届かず別の期を名指す: 行は P30E の claim で決まる
        self.assertTrue(rows)
        self.assertTrue(all(r[u"届いた"] for r in rows))
        self.assertEqual([u"Prior1Year"] * len(rows), [r[u"注入後の pointer の期"] for r in rows])
        rows, _c = run_ps(verify=by_profile("P29E", "P30E"))                # P30E だけ届かず別の期を名指す
        self.assertTrue(rows)
        self.assertFalse(any(r[u"届いた"] for r in rows))
        self.assertEqual([u"CurrentYear"] * len(rows), [r[u"注入後の pointer の期"] for r in rows])

    def test_w_6b_reached_of_is_a_conjunction_of_the_two_spans(self):
        res = {"span": u"前期の12億3,456万円"}
        self.assertTrue(PS.reached_of(u"9億7,000", u"前期の9億7,000万円", res, u"12億3,456"))
        self.assertFalse(PS.reached_of(u"9億7,000", u"前期の1億万円", res, u"12億3,456"))              # 基準の span に元の字が無い
        self.assertFalse(PS.reached_of(u"9億7,000", u"前期の9億7,000万円", {"span": u"前期の1億万円"}, u"12億3,456"))   # 注入後の span に差し替えの字が無い
        self.assertFalse(PS.reached_of(u"9億7,000", None, res, u"12億3,456"))
        self.assertFalse(PS.reached_of(u"9億7,000", u"前期の9億7,000万円", {"span": None}, u"12億3,456"))
        self.assertFalse(PS.reached_of(u"9億7,000", u"前期の9億7,000万円", None, u"12億3,456"))            # 対応が付かない

    def test_w_7_the_engine_cue_column_is_the_engine_function_not_a_constant(self):
        text = u"前期は9億7,000万円でした。粗利益は1,000百万円でした。"        # 前期の数には手がかり(前期は)があり、粗利益の数には無い
        rows, c = run_ps(text=text, refs=REFS_P)
        by_unit = dict((r[u"単位"], r[u"engine の手がかり"]) for r in rows)
        self.assertEqual({u"万円": True, u"百万円": False}, by_unit)
        self.assertEqual({u"真": 1, u"偽": 1}, dict(c[u"作れる site の手がかり"]))
        for const in (True, False):
            rows2, c2 = run_ps(text=text, refs=REFS_P, patches=((PS.R, "_prior_cue", lambda s, a, b=None, const=const: const),))
            self.assertEqual({u"万円": const, u"百万円": const}, dict((r[u"単位"], r[u"engine の手がかり"]) for r in rows2), const)       # 手がかりを常に真 / 偽にすれば欄が動く
            self.assertEqual(2 if const else 0, c2[u"作れる site の手がかり"][u"真"])
        text_k = u"売上高は9億7,000万円から増えました。"                                 # 数の直後の「から」も手がかり(終わりの位置 b を渡さないと取れない)
        start, end = text_k.index(u"9億"), text_k.index(u"から")
        self.assertTrue(PS.engine_cue(text_k, types.SimpleNamespace(start=start, end=end)))
        self.assertFalse(PS.engine_cue(text_k, types.SimpleNamespace(start=start, end=end - 2)))
        self.assertFalse(PS.engine_cue(u"売上高は9億7,000万円に増えました。", types.SimpleNamespace(start=start, end=end)))
        seen = []
        real = PS.R._prior_cue
        run_ps(text=text, refs=REFS_P, patches=((PS.R, "_prior_cue", lambda s, a, b=None: seen.append((s, a, b)) or real(s, a, b)),))
        self.assertTrue(seen)
        for s, a, b in seen:
            self.assertEqual(text, s)                                                  # 注入前の文
            self.assertIn((a, b), [(t.start, t.end) for t in self._tokens(text)])      # 注入前の token の start・end

    def _tokens(self, text):
        with PS.yen_scan_on():
            return N.scan(text)

    def test_w_8_the_prior_word_column_looks_at_the_same_line(self):
        for word in PS.PRIOR_WORDS:
            text = u"%sの売上高は9億7,000万円でした。" % word
            with PS.yen_scan_on():
                tok = [t for t in N.scan(text) if t.unit == u"万円"][0]
            self.assertTrue(PS.has_prior_word(text, tok), word)
        with PS.yen_scan_on():
            text = u"前期の話です。\n売上高は9億7,000万円でした。\n前年の話です。"
            tok = [t for t in N.scan(text) if t.unit == u"万円"][0]
            self.assertFalse(PS.has_prior_word(text, tok))                           # 別の行の語は数えない
            text2 = u"売上高は9億7,000万円でした。"
            tok2 = [t for t in N.scan(text2) if t.unit == u"万円"][0]
            self.assertFalse(PS.has_prior_word(text2, tok2))
            text3 = u"売上高は9億7,000万円で、前年を上回りました。"                       # 同じ行で数の後に在る語も数える
            tok3 = [t for t in N.scan(text3) if t.unit == u"万円"][0]
            self.assertTrue(PS.has_prior_word(text3, tok3))
        rows, _c = run_ps(text=u"売上高は9億7,000万円でした。", refs=REFS_P)
        self.assertEqual([False], [r[u"文に前期の語"] for r in rows])
        rows, _c = run_ps()
        self.assertEqual([True, True, True], [r[u"文に前期の語"] for r in rows])

    def test_w_9_the_pointer_period_words_are_cut_from_the_first_pointer_context(self):
        self.assertEqual(u"CurrentYear", PS.pointer_period(["xbrl:jppfs_cor:NetSales@CurrentYearDuration"]))
        self.assertEqual(u"CurrentYear", PS.pointer_period(["xbrl:jppfs_cor:Assets@CurrentYearInstant"]))
        self.assertEqual(u"Prior1Year", PS.pointer_period(["xbrl:jppfs_cor:NetSales@Prior1YearDuration"]))
        self.assertEqual(u"Prior1Year", PS.pointer_period(("xbrl:jppfs_cor:Assets@Prior1YearInstant",)))
        self.assertEqual(u"他", PS.pointer_period(["xbrl:jppfs_cor:NetSales@Prior2YearDuration"]))
        self.assertEqual(u"他", PS.pointer_period(["xbrl:jppfs_cor:NetSales@Interim1Duration"]))
        self.assertEqual(u"他", PS.pointer_period(["text:sentence3"]))                          # xbrl の fact でない
        self.assertEqual(u"他", PS.pointer_period(["xbrl:jppfs_cor:NetSales"]))                  # context が無い
        self.assertEqual(u"なし", PS.pointer_period([]))
        self.assertEqual(u"なし", PS.pointer_period(None))
        self.assertEqual(u"Prior1Year", PS.pointer_period(["xbrl:jppfs_cor:A@Prior1YearDuration", "xbrl:jppfs_cor:B@CurrentYearDuration"]))     # 先頭だけを見る
        self.assertEqual(u"CurrentYear", PS.pointer_period(["xbrl:jppfs_cor:B@CurrentYearDuration", "xbrl:jppfs_cor:A@Prior1YearDuration"]))
        self.assertEqual(set(PERIODS), set([PS.pointer_period(p) for p in (["xbrl:a:b@CurrentYearX"], ["xbrl:a:b@Prior1YearX"], ["xbrl:a:b@Z"], [])]))

    def test_w_10_the_pointer_period_columns_follow_the_claims_before_and_after(self):
        # 注入後の claim が GROUNDED で当期の fact を名指す(= 期の取り違えを通した行)
        rows, c = run_ps(verify=make_verify(TEXT_P, base_ptr=PTR_PRIOR, inj_state=G, inj_ptr=PTR_CUR))
        for r in rows:
            self.assertEqual((u"Prior1Year", u"CurrentYear", TUNE.LABEL_PASS), (r[u"基準の pointer の期"], r[u"注入後の pointer の期"], r["P30E"][u"結果"]))
            self.assertTrue(r[u"届いた"])
        cols = PS.ps_columns(collections.OrderedDict([(u"bk", c)]), rows)
        self.assertEqual(3, cols[KEY["PS-5"]][u"うち注入後の pointer の期が CurrentYear"])
        self.assertEqual(3, cols[KEY["PS-3"]][u"うち基準の pointer の期が Prior1Year の行"])
        # 基準の claim が当期の fact を名指す / 注入後が他の期
        rows, _c = run_ps(verify=make_verify(TEXT_P, base_ptr=PTR_CUR, inj_state=V_, inj_ptr="xbrl:jppfs_cor:NetSales@Prior2YearDuration"))
        for r in rows:
            self.assertEqual((u"CurrentYear", u"他"), (r[u"基準の pointer の期"], r[u"注入後の pointer の期"]))
        # pointers が無い claim
        rows, _c = run_ps(verify=lambda zb, p, t: dict(make_verify(TEXT_P)(zb, p, t), claims=[dict(c, pointers=[]) for c in make_verify(TEXT_P)(zb, p, t)["claims"]]))
        for r in rows:
            self.assertEqual((u"なし", u"なし"), (r[u"基準の pointer の期"], r[u"注入後の pointer の期"]))
        # 期の分け方を固定する変異(常に Prior1Year / 常に CurrentYear)は上の例のどれかで赤
        for const in (u"Prior1Year", u"CurrentYear"):
            rows, _c = run_ps(patches=((PS, "pointer_period", lambda ptrs, const=const: const),), verify=make_verify(TEXT_P, base_ptr=PTR_CUR, inj_state=V_, inj_ptr="xbrl:jppfs_cor:NetSales@Prior2YearDuration"))
            self.assertNotEqual([(u"CurrentYear", u"他")] * 3, [(r[u"基準の pointer の期"], r[u"注入後の pointer の期"]) for r in rows])

    def test_w_11_the_injected_claim_is_looked_up_by_the_new_value_and_unmapped_when_two_claims_share_it(self):
        text = u"前期の売上高は9億7,000万円、当期の売上高は12億3,456万円でした。"                 # 当期の値が文に既に在る = 差し替えた字の claim が 2 件になる
        refs = [REFS_P[0], REFS_P[1]]
        rows, c = run_ps(text=text, refs=refs)
        self.assertEqual(1, len(rows))
        self.assertTrue(rows[0][LINK_KEY])                                                         # 土台の対応は付く
        self.assertEqual(TUNE.LABEL_UNMAPPED, rows[0]["P30E"][u"結果"])                             # 注入後の claim が 1 件に決まらない = 対応が付かない
        self.assertFalse(rows[0][u"届いた"])
        self.assertEqual(u"なし", rows[0][u"注入後の pointer の期"])
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))

    def test_w_12_the_cap_is_applied_after_the_base_filter_and_before_nothing_else(self):
        items = [(u"科目%s" % chr(0x41 + i), 1000 + 7 * i) for i in range(16)]
        text = u"".join(u"前期の%sは%s千円でした。" % (lab, format(v, ",")) for lab, v in items)
        refs = []
        for i, (lab, v) in enumerate(items):
            refs.append({"key": "jppfs:Item%d@Prior1YearDuration" % i, "value": float(v * 1000), "unit": u"円", "label": lab})
            refs.append({"key": "jppfs:Item%d@CurrentYearDuration" % i, "value": float((v + 3000) * 1000), "unit": u"円", "label": lab})
        base = make_verify(text)

        def verify_some(zb, p, t):
            out = base(zb, p, t)
            if t == text:
                for k, cl in enumerate(out["claims"]):
                    if k % 5 == 0:
                        cl["state"] = V_                       # 土台が GROUNDED でない claim を 4 件(0・5・10・15 番目)
            return out
        rows, c = run_ps(text=text, refs=refs, verify=verify_some)
        self.assertEqual((16, 12, 10, 10), (sum(c[u"作れる site"].values()), c[u"土台 P30E が GROUNDED の site"], c[u"採った"], c[u"cap を基準で絞る前に掛けた数"]))
        self.assertEqual(10, len(rows))
        self.assertEqual({PS.LINKED: 12, PS.STATUS_NOT_G: 4}, dict(c[u"作れる site の状態"]))
        self.assertEqual({PS.LINKED: 10}, dict(c[u"採った の状態"]))
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))

    def test_w_13_a_claim_that_does_not_pair_between_the_profiles_leaves_the_p29e_cell_unmapped(self):
        base = make_verify(TEXT_P)

        def verify(zb, p, t):
            out = base(zb, p, t)
            if p == "P29E":
                for cl in out["claims"]:
                    cl["span"] = cl["span"] + u"x"                  # (value, span, unit) が P30E の claim と結べない
            return out
        rows, c = run_ps(verify=verify)
        self.assertTrue(rows)
        for r in rows:
            self.assertIs(False, r[LINK_KEY], r)
            self.assertEqual(TUNE.LABEL_UNMAPPED, r["P29E"][u"結果"])
            self.assertTrue(r["P30E"][u"対応"])
        self.assertEqual({PS.UNLINKED}, set(c[u"採った の状態"]))
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))

    def test_w_14_a_fullwidth_digit_book_is_skipped(self):
        rows, c = run_ps(text=u"前期の売上高は９億円でした。")
        self.assertEqual([], rows)
        self.assertEqual([u"注入しない"], list(c))

    def test_w_15_the_summaries_use_the_one_type_and_put_the_types_back(self):
        rows, _c = run_ps()
        base = [(u"docID", u"D"), (u"form", u"F1"), (u"model", u"m"), (u"writer", u"W")]
        rows = [collections.OrderedDict(base + list(r.items())) for r in rows]
        self.assertEqual(("T1_VALUE", "T8_REL"), tuple(RUN.INJECT_TYPES))                    # H・RB の便の型の並び(他の門が読む)
        summ, cmp_ = PS.inject_summaries(rows)
        self.assertEqual([T9], list(summ))
        self.assertEqual([T9], list(cmp_))
        self.assertEqual(("T1_VALUE", "T8_REL"), tuple(RUN.INJECT_TYPES))
        self.assertEqual(len(rows), summ[T9]["P30E"][u"全体"][u"注入の行"])
        try:
            with PS.ps_types_in_run():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertEqual(("T1_VALUE", "T8_REL"), tuple(RUN.INJECT_TYPES))

    def test_w_16_the_job_refuses_a_switch_that_is_off(self):
        with self.assertRaises(PS.Stop):
            PS.inject_job_ps(("aiforms", "n", {}, {}, "d", {}, "s", "w"))

    def test_w_17_the_claim_lookup_uses_the_original_unit_and_the_new_value(self):
        real = TUNE.claim_for_p27
        seen = []

        def spy(claims, inj, unit):
            seen.append((inj["type"], inj["new_value"], inj["replacement"], unit))
            return real(claims, inj, unit)
        run_ps(patches=((TUNE, "claim_for_p27", spy),))
        self.assertEqual(6, len(seen))                                  # 3 つの注入 × 2 profile
        self.assertEqual({T9}, set(x[0] for x in seen))
        self.assertEqual(sorted([(123456.0, u"12億3,456", u"万円"), (1200.0, u"1,200", u"百万円"), (6000.0, u"6,000", u"千円")] * 2), sorted((x[1], x[2], x[3]) for x in seen))


class RunInjectTest(unittest.TestCase):
    def test_w_20_run_inject_leaves_the_switch_off_and_writes_the_record_parts(self):
        u"""run_inject の記録の組み立てと切り替えの出入りを、読み込み・並列・cache を偽にして 1 回通す。"""
        base = sample_inject()
        rows = norm(base[u"行"])
        item = {u"docID": "DOC1", u"form": "F1", u"model": "m1", u"writer": "W1", u"sha256": "0" * 64}
        seen = []
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(RUN, "PROFILES", RUN.PROFILES)
            pt.set(RUN, "base_status4", RUN.base_status4)
            pt.set(PS, "load_books", lambda root=ROOT, only=None: [("aiforms", "DOC1_F1_m1", item, {}, {})])

            def pool(fn, jobs_, procs):
                seen.append(getattr(N, FLAG))
                return [("DOC1_F1_m1", [collections.OrderedDict(r) for r in rows if r["docID"] == "DOC1"], norm(base[u"本ごとの数え"][u"DOC1_F1_m1"]))]
            pt.set(NF, "map_pool", pool)
            pt.set(PS, "caches_all", lambda: collections.OrderedDict())
            pt.set(GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
            pt.set(PS, "header_ps", lambda root, step, seed_meta, before, after, profiles: collections.OrderedDict([(u"seal", SEAL_REL), (u"profile", list(profiles))]))
            out = os.path.join(d, "inject.json")
            rec = PS.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with open(out, encoding="utf-8") as fh:
                disk = json.load(fh)
            with self.assertRaises(PS.Stop):                                                    # 出力が在れば測り直さない
                PS.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with self.assertRaises(PS.Stop):                                                    # --only は --out が要る(本番の記録を作らない。守りが壊れても root の下の使い捨ての場所に書く)
                PS.run_inject(root=d, procs=1, only="DOC1", say=lambda *a: None, work_root=d)
            self.assertFalse(os.path.exists(os.path.join(d, PS.INJECT_REL)))
        self.assertEqual([True], seen)                                    # map_pool の呼ばれた間は真
        self.assertFalse(getattr(N, FLAG))                                # 出たら偽
        self.assertEqual(norm(rec), disk)
        self.assertEqual(BASE_WORD_PIN, disk[u"型"][u"土台"])
        self.assertEqual(SITE_WORD_PIN, disk[u"型"][u"site"])
        self.assertEqual(PS.seal_limits(read(SEAL_REL)) + list(PS.EXTRA_LIMITS), disk[u"限界"])
        self.assertEqual({u"名前": FLAG, u"inject の中の値": True, u"出たあとの値": False, u"配線の問題": []}, disk[u"切り替え"])
        self.assertEqual(norm(PS.ps_columns(disk[u"本ごとの数え"], disk[u"行"])), disk[PS.PS_KEY])
        self.assertEqual(norm(PS.cue_breakdown(disk[u"行"])), disk[PS.CUE_KEY])
        self.assertEqual(norm(PS.period_breakdown(disk[u"行"])), disk[PS.PERIOD_KEY])
        self.assertEqual([u"P29E", u"P30E"], disk[u"profile"])
        self.assertEqual([T9], list(disk[u"集計"]))
        self.assertEqual(u"**--only(本番の記録ではない)**", PS.scope_word("x"))
        self.assertEqual(u"全 200 本", PS.scope_word(None))

    def test_w_21_the_header_of_a_real_record_passes_the_header_check(self):
        u"""script の ``header_ps`` が作る頭が、門の頭の検査を通る。1 欄ずつ落とすと赤。"""
        h = PS.header_ps(ROOT, u"標本", {u"seed_file": u"x"}, {}, {}, INJECT_PROFILES)
        rec = collections.OrderedDict(h)
        rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
        rec[u"範囲"] = u"全 200 本"
        self.assertEqual([], header_problems(norm(rec), True))
        for key in (u"lib の指紋", u"J の script の sha256", u"nscan script の sha256", u"rmix script の sha256", u"H の記録の sha256", u"J の記録の sha256", u"RB の記録の sha256",
                    u"engine の指紋", u"この script の sha256", u"生成の記録の sha256"):
            r2 = norm(rec)
            r2.pop(key)
            self.assertNotEqual([], header_problems(r2, True), key)

    def test_w_22_load_books_filters_by_docid_and_stops_on_an_unknown_one(self):
        if not os.path.exists(os.path.join(ROOT, PS.SOURCES["aiforms"]["claims"])):
            self.skipTest(u"前の便の claims の記録が無い")
        books = PS.load_books(ROOT, None)
        ids = sorted(set(b[2]["docID"] for b in books))
        self.assertEqual(200, len(books))
        two = PS.load_books(ROOT, u"%s,%s" % (ids[0], ids[1]))
        self.assertEqual(set(ids[:2]), set(b[2]["docID"] for b in two))
        self.assertEqual(sum(1 for b in books if b[2]["docID"] in ids[:2]), len(two))
        with self.assertRaises(PS.Stop):
            PS.load_books(ROOT, u"X0000000")
        with self.assertRaises(PS.Stop):
            PS.load_books(ROOT, u"%s,X0000000" % ids[0])


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
        [u"LATER_NAMING_FILES に docID を持たない %s がある" % rel for rel in [SCRIPT_REL, DOC_REL] + list(SG.GATE_RELS) + [SG.ROWS_REL] if rel in got]


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
        for rel in ("fixtures/xbrl/nscan/inject_2026-11-05.json", "fixtures/xbrl/nscan/offcheck_2026-11-05.json", "fixtures/xbrl/rmix/ai200_2026-11-04.json",
                    "fixtures/xbrl/numfix/ai200_2026-11-04.json", "fixtures/xbrl/jtypes/inject_2026-11-05.json"):
            self.assertIn(rel, got)

    def test_h_3_the_script_is_declared_as_a_harness_file(self):
        src = read("tests/measure/test_xbrl_inject_harness_review.py")
        self.assertEqual([], harness_problems(src))
        self.assertNotEqual([], harness_problems(src.replace(u'"%s"' % SCRIPT_REL, u'"x/%s"' % SCRIPT_REL)))
        self.assertNotEqual([], harness_problems(src.replace("LATER_HARNESS_FILES", "LATER_HARNESS_FILE")))
        self.assertIn("measure/xbrl_jtypes_2026-11-05.py", src)


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
        J = PS.build_PS(R, self.seal)
        self.assertEqual(set(J), {u"PS", u"K", u"採用", u"欄"})

    def test_r_3_the_result_document_follows_the_records(self):
        R = self.need()
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), R, self.seal, [x for x in PS.git_numstat_since_seal(ROOT) if not SG.SGR.t5y_declared_numstat(x)]))

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
