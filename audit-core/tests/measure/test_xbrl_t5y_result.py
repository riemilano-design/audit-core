# -*- coding: utf-8 -*-
"""T5Y(注入の仕掛けの T5 を円族の数に作れるようにする切り替え ``t5_yen_2026_11_06``)の測定の結果の門。封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §1・§3・§4・§5。

記録 1 つ(``fixtures/xbrl/t5y/inject_2026-11-06.json``)と、読むだけの J の記録・H の記録から、封 §3 の予測 Y-1〜Y-10 と §4 の採用の基準 K-1〜K-4 を**機械で求め**(予測の幅は封の字から読む。字のコピーにしない)、
結果の文書 ``docs/XBRL_T5_YEN_RESULT_2026-11-06.md`` の表(``<!-- 門:start pred -->``・``<!-- 門:start judge -->`` の中)を記録から作り直した表と一行も違わないことを見る。
測定の script(``measure/xbrl_t5y_2026-11-06.py`` の ``build_Y``・``judge_from``・``y_columns``・``y1_value``・``render_pred``・``render_judge``)の関数を呼んで照らす。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文・pointer・要素など)が無い・pointer の字(要素名)を持たない・key_leaks が空・docID を持つ記録が ``LATER_NAMING_FILES`` に宣言され、
     script が ``LATER_HARNESS_FILES`` に宣言されている・cache の前後が同じ・script と lib と仕掛けの 2 file と前の便(T9 の第 2 便を含む)の script・記録の sha256 が現物と一致・
     **engine の指紋が PB の engine の commit の adapters の束ねた値(この門に literal で留める。RB の記録の値とは違う)と一致**・切り替え 2 つの欄。
  b  記録の中身が再計算と一致する: 本ごとの数えの整合・行の整合(対応の 3 条件と欠けた条件・相手の期・相手と同じ要素・pointer の期・pointer が相手と同じ・届いた)・集計・形別・相手の期別・同じ要素別・
     通した行の期の内訳・**Y の欄の全部を 本ごとの数えと行から数え直す**(欄を 0 に固定すると赤。行の欄を 1 つ変えると該当の欄が動く)・Y-10 の試験の欄・限界(封 §6 の字 + script の限界)。
  c  判定: 記録(の欄)を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。採用は K-1〜K-4 を全部満たすときだけ。
  d  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 79d05cd ⊏ 記録・結果の文書(仕掛け・script・試験・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  f  **偽で不変**: 切り替え 2 つ 偽で 200 本の ``t5_sites`` を数え直し、J の記録の T5 の偽・真と本ごとに一致する(H の ``offcheck`` の形)。偽の経路を壊すと赤。
  g  変異: 小さい標本の記録と文書で同じ検査が緑 → 変異(記録の数・Y の欄・表の 1 字・封の予測の 1 字・順序・記録の禁止欄・指紋の 1 字・cache の前後・切り替え 2 つ・pointer の字・期の欄・試験の欄)で赤。
  w  手順・**行の欄**: script の ``inject_text_ty`` を小さい入力(zip・判定は偽。lib は本物)で通し、行の欄(round-trip・読み直し・届いた・相手の期・相手と同じ要素・pointer が相手と同じ・対応の条件)が
     壊した差し替えで True ↔ False が替わる例で固定する。仕掛けの関数(``S.t5_sites``・``IJ.build_t5``)と H の関数(T1・T8 の数え)を差し替えると行・数えが動く。

記録が無いときは (a)(b)(d)(e) の本番の記録の試験を skip する(skip でも行が出ることを試験が確かめる)。標本の試験 (c)(g)(w) は記録が無くても走る。この file は docID の字を持たない。
"""
import ast
import collections
import copy
import importlib.util
import io
import json
import os
import re
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


SG = load_module("tests/measure/test_xbrl_t5y_seal.py", "t5y_seal_gate_for_result")                         # 封の門の部品。門としては走らせない
PIR = load_module("tests/measure/test_xbrl_pswap_idmap_result.py", "pswap_idmap_result_gate_for_t5y_result")   # T9 の第 2 便の結果の門の部品(標本の組み立て・偽の verify・対応の条件の検査)。門としては走らせない
PSR = PIR.PSR
PR = SG.PR
TY = SG.TY
PI = TY.PI
PS = TY.PS
JT = TY.JT
NS = TY.NS
RM, NF, GEN, RUN, TUNE, IJ, S = TY.RM, TY.NF, TY.GEN, TY.RUN, TY.TUNE, TY.IJ, TY.S
N, SC = TY.N, TY.SC

SEAL_REL = TY.SEAL_REL
DOC_REL = TY.DOC_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
REC_REL = collections.OrderedDict(TY.REC_REL)
SCRIPT_REL = TY.SCRIPT_REL
LIB_RELS = TY.LIB_RELS
DEVICE_RELS = TY.DEVICE_RELS
FLAG = TY.FLAG
FLAG2 = TY.FLAG2
T5 = TY.T5
NOT_GATED = PR.NOT_GATED
HIT, MISS = TY.HIT, TY.MISS
SHAPES = TY.SHAPES
PERIODS = PS.PERIODS
PARTNER_PERIODS = TY.PARTNER_PERIODS
LINK_KEY = TY.LINK_KEY
CONDS = PI.CONDS
COND_A, COND_I, COND_U = PI.COND_A, PI.COND_I, PI.COND_U
NO_BASE = PI.NO_BASE
F_COND, F_MISS = TY.F_COND, TY.F_MISS
YCOL = TY.YCOL
Y_KEY = TY.Y_KEY
FORBIDDEN_KEYS = PSR.FORBIDDEN_KEYS
COMPANY_WORDS = PSR.COMPANY_WORDS
POINTER_TEXT_RE = PSR.POINTER_TEXT_RE
DOCID_RE = SG.DOCID_RE
FOR_RESULT_WORDS = PSR.FOR_RESULT_WORDS
HAVE_CACHE = all(os.path.isdir(p) for p in TY.caches_all().values())
INJECT_PROFILES = TY.INJECT_PROFILES
Patch = PSR.Patch
norm = PSR.norm
norm_t = PSR.norm_t
walk = PSR.walk
walk_strings = PSR.walk_strings
read = PSR.read
jload = PSR.jload
sha256_rel = PSR.sha256_rel
G, V_, U_, P_ = PSR.G, PSR.V_, PSR.U_, PSR.P_
make_verify = PSR.make_verify
#: 封 §3・§4 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("Y-1", 672),
    ("Y-2", collections.OrderedDict([(u"計", (950.0, 1030.0)), (u"複合", (600.0, 660.0)), (u"万だけ", (80.0, 100.0)), (u"既存", (250.0, 300.0)), (u"読み直せる site", (940.0, 1000.0))])),
    ("Y-3", collections.OrderedDict([(u"採った", (500.0, 900.0)), (u"うち土台 P30E が GROUNDED の行", (300.0, 700.0))])),
    ("Y-4", (90.0, 100.0)),
    ("Y-5", collections.OrderedDict([(u"通した率(P30E)", (3.0, 20.0)), (u"割合", (60.0, 95.0))])),
    ("Y-6", (70.0, 100.0)),
    ("Y-7", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"届かない行(対応が付く行の中)", 0)])),
    ("Y-8", (0, 10)), ("Y-9", (3.0, 25.0)),
    ("Y-10", collections.OrderedDict([(u"失敗", 0), (u"赤", 5), (u"変異", 5)])),
    ("K-1", u"一致"), ("K-2", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0)])), ("K-3", 300.0),
    ("K-4", collections.OrderedDict([(u"失敗", 0), (u"赤", 5), (u"変異", 5)]))])
#: 注入の土台の字(測定の script の定数と同じでなければ赤)
BASE_WORD_PIN = u"無改変の文で P30E が GROUNDED の claim"
#: この script の限界(封 §6 の 4 つの後ろに足した 5 つ)の字の頭(literal に留める。script の字を変えたら赤)
EXTRA_LIMITS_PIN = (u"作れる site は T5 の切り替え 真の t5_sites の数", u"差し替えの相手は IJ.build_t5 が決める", u"対応付けは基準の claim の id で引く",
                    u"Y-1 の T1_VALUE・T8_REL の作れる site は T5 の切り替え 偽のまま", u"round-trip 不一致は止めずに数える")
#: 記録の頭の engine の指紋 adapter_xbrl_py_sha256 = PB の engine の commit の adapters の束ねた値(司令塔の訂正 2026-11-06 夕。RB の記録の 4ea77c93… とは違う)
ENGINE_ADAPTER_PIN = "dc13edfee7a9ac6b900ae610d056424b622b8447491113b78c4debf902bcfee8"
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
SEP = u"::"                                  # sample_cols の path の区切り(欄の名前に / が入るため)
UNMAPPED_CELL = PIR.UNMAPPED_CELL


def records_exist():
    if FORCE["no_records"]:
        return False
    return all(os.path.exists(os.path.join(ROOT, v)) for v in REC_REL.values())


_FIXED = {}


def fixed_records():
    u"""読むだけの J の記録・H の記録・RB の記録(1 回だけ読む)。"""
    if not _FIXED:
        _FIXED["j"] = jload(TY.J_RECORD_REL)
        _FIXED["h"] = jload(TY.H_RECORD_REL)
        _FIXED["rb"] = jload(TY.RB_RECORD_REL)
    return _FIXED


def load_records():
    f = fixed_records()
    return collections.OrderedDict([("inject", jload(REC_REL["inject"])), ("j", f["j"]), ("h", f["h"])])


# ---------------------------------------------------------------- 封の字(a)
def bounds_problems(seal):
    u"""封の字から読んだ予測の幅が、ここに留めた値と同じか。"""
    out = []
    try:
        got = TY.seal_bounds(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return [u"封から幅を読めない(%s)" % type(e).__name__]
    for k, v in BOUNDS_PIN.items():
        g = got.get(k)
        if json.dumps(norm_t(g), sort_keys=True) != json.dumps(norm_t(v), sort_keys=True):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, g, v))
    if list(TY.seal_pred_rows(seal)) != list(SG.PRED_IDS) or list(TY.seal_k_rows(seal)) != list(SG.K_IDS):
        out.append(u"封の予測の行が Y-1〜Y-10 でない・K の行が K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 記録(a)(b)
def header_problems(rec, full):
    u"""記録の頭(封・script・lib・仕掛け・前の便(T9 の第 2 便を含む)の script と記録・engine・cache・切り替え 2 つ)。"""
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"封の名か commit が違う")
    want = collections.OrderedDict([
        (u"この script の sha256", sha256_rel(SCRIPT_REL)), (u"T9 の第 2 便の script の sha256", sha256_rel(TY.PI_SCRIPT_REL)), (u"T9 の第 2 便の記録の sha256", sha256_rel(TY.PI_RECORD_REL)),
        (u"T9 の script の sha256", sha256_rel(PI.PS_SCRIPT_REL)), (u"T9 の記録の sha256", sha256_rel(PI.PS_RECORD_REL)),
        (u"J の script の sha256", sha256_rel(PS.JT_SCRIPT_REL)), (u"nscan script の sha256", sha256_rel(PS.NS_SCRIPT_REL)),
        (u"rmix script の sha256", sha256_rel("measure/xbrl_rmix_2026-11-04.py")), (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")),
        (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")), (u"生成の script の sha256", sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")),
        (u"J の記録の sha256", sha256_rel(TY.J_RECORD_REL)), (u"H の記録の sha256", sha256_rel(TY.H_RECORD_REL)), (u"RB の記録の sha256", sha256_rel(TY.RB_RECORD_REL))])
    for name, v in want.items():
        if rec.get(name) != v:
            out.append(u"%s が現物と違う" % name)
    gens = dict((src, sha256_rel(p["gen"])) for src, p in TY.SOURCES.items())
    if norm(rec.get(u"生成の記録の sha256")) != gens:
        out.append(u"生成の記録の sha256 が現物と違う")
    if norm(rec.get(u"lib の指紋")) != dict((rel, sha256_rel(rel)) for rel in LIB_RELS):
        out.append(u"lib の指紋が現物と違う")
    if norm(rec.get(u"仕掛けの指紋")) != dict((rel, sha256_rel(rel)) for rel in DEVICE_RELS):
        out.append(u"仕掛けの指紋(sites.py・inject.py)が現物と違う")
    if rec.get(u"profile") != list(INJECT_PROFILES):
        out.append(u"profile が (P29E, P30E) でない")
    fp = rec.get(u"engine の指紋") or {}
    if fp.get("adapter_xbrl_py_sha256") != ENGINE_ADAPTER_PIN:
        out.append(u"engine の指紋 adapter_xbrl_py_sha256 が PB の engine の commit の値(留めた値)と違う")
    if fp.get("core_py_sha256") != (fixed_records()["rb"].get(u"engine の指紋") or {}).get("core_py_sha256") or fp.get("core_py_sha256") is None:
        out.append(u"engine の指紋 core_py_sha256 が RB の記録の値(core は PB で不変)と違う")
    cb = rec.get(u"cache の前後") or {}
    if cb.get(u"変化なし") is not True or cb.get(u"前") != cb.get(u"後"):
        out.append(u"cache の前後が同じでない")
    sw = rec.get(u"切り替え") or {}
    if sw.get(u"名前") != FLAG or sw.get(u"T5 の切り替えの名前") != FLAG2 or sw.get(u"配線の問題") != []:
        out.append(u"切り替えの名前が違う・配線の問題が空でない")
    if sw.get(u"inject の中の値") is not True or sw.get(u"出たあとの値") is not False:
        out.append(u"H の切り替えが inject の中で真・出たあとで偽になっていない")
    if sw.get(u"T5 の切り替え inject の中の値") is not True or sw.get(u"T5 の切り替え 出たあとの値") is not False:
        out.append(u"T5 の切り替えが inject の中で真・出たあとで偽になっていない")
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
        TY.assert_clean_ty(copy.deepcopy(rec))
    except GEN.Stop:
        out.append(u"鍵らしい字が記録に在る")
    if rec.get(u"key_leaks", []) != []:
        out.append(u"key_leaks が空でない")
    return out


cond_problems = PIR.cond_problems


def count_problems(name, c, rows, cap):
    u"""本ごとの数え 1 本の整合(自分の欄の間と、その本の行との関係)。"""
    out = []
    if u"注入しない" in c:
        if rows:
            out.append(u"%s: 注入しない本に行がある" % name)
        if set(c) != {u"注入しない"}:
            out.append(u"%s: 注入しない本に数えがある" % name)
        return out
    t = c[u"T5 の site"]
    shapes = list(SHAPES)
    for key in (u"篩だけの site", u"作れる site"):
        if list(t[key]) != [u"計"] + shapes or sum(t[key][k] for k in shapes) != t[key][u"計"]:
            out.append(u"%s: %s の形別の和が計と合わない" % (name, key))
    sites = t[u"作れる site"][u"計"]
    if sites > t[u"篩だけの site"][u"計"] or t[u"読み直せる site"] > t[u"篩だけの site"][u"計"] or min(t[u"読み直せる site"], t[u"相手の候補の和"]) < 0:
        out.append(u"%s: 作れる site・読み直せる site が篩だけの site を超えている" % name)
    if list(t[u"偽"]) != [u"H の切り替え 偽", u"H の切り替え 真"] or min(t[u"偽"].values()) < 0:
        out.append(u"%s: 偽の site の数の欄が合わない" % name)
    for ty in ("T1_VALUE", "T8_REL"):
        v = c[ty]
        if list(v) != [u"作れる site", u"採った"] or v[u"採った"] > min(cap, v[u"作れる site"]) or min(v.values()) < 0:
            out.append(u"%s: %s の作れる site・採った が合わない" % (name, ty))
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
    for k in shapes:
        if sum(1 for r in rows if r[u"形"] == k) > t[u"作れる site"].get(k, 0):
            out.append(u"%s: 形 %s の行が作れる site より多い" % (name, k))
    return out


def row_problems(r, labels, seen):
    out = []
    if r[u"型"] != T5:
        out.append(u"型が T5_COINCIDENT でない")
    if r[u"id"] in seen:
        out.append(u"同じ注入の id が 2 回ある")
    seen.add(r[u"id"])
    name = u"%s_%s_%s" % (r["docID"], r["form"], r["model"])
    if not r[u"id"].startswith(name + u"-T5-"):
        out.append(u"id が本の名前 + T5 の形でない")
    linked = r.get(LINK_KEY)
    if not isinstance(linked, bool):
        out.append(u"P29E の土台に対応の欄が真偽でない")
    elif not linked and norm(r["P29E"]) != UNMAPPED_CELL:
        out.append(u"P29E の土台に対応が無い行の P29E の欄が対応なしでない")
    for key in (u"round-trip", u"読み直し", u"先頭の位が減った", u"届いた", u"相手と同じ要素か", u"注入後の pointer が相手の fact と同じか"):
        if not isinstance(r.get(key), bool):
            out.append(u"行の %s が真偽でない" % key)
    if r.get(u"形") not in SHAPES:
        out.append(u"行の形が語でない")
    if r.get(u"単位") is not None and (not isinstance(r.get(u"単位"), str) or not r.get(u"単位")):
        out.append(u"行の単位が語でも None でもない")
    if r[u"先頭の位が減った"] and r[u"形"] != u"複合":
        out.append(u"先頭の位が減ったのは複合だけ")
    if r.get(u"相手の fact の期") not in PARTNER_PERIODS:
        out.append(u"行の相手の fact の期が 3 つの語でない")
    for key in (u"基準の pointer の期", u"注入後の pointer の期"):
        if r.get(key) not in PERIODS:
            out.append(u"行の %s が 4 つの語でない" % key)
    for p in INJECT_PROFILES:
        c = r[p]
        if c[u"結果"] not in labels:
            out.append(u"結果が classify の語でない")
        if not RUN.reason_ok(c[u"reason"]):
            out.append(u"reason が符号の形でない")
        if c[u"対応"] is True and c[u"結果"] == TUNE.LABEL_UNMAPPED:
            out.append(u"%s の欄の対応と結果が合わない" % p)
        out += cond_problems(r, p)
    c30 = r.get(F_COND % "P30E") or {}
    if r[u"届いた"] and not c30.get(COND_U):
        out.append(u"(ウ)が偽の行が届いた")
    if c30.get(COND_A) is False and (r.get(u"注入後の pointer の期") != u"なし" or r.get(u"注入後の pointer が相手の fact と同じか")):
        out.append(u"id の claim が無い行の注入後の pointer の期が なし でない・pointer が相手と同じ")
    if r[u"注入後の pointer が相手の fact と同じか"] and r.get(u"注入後の pointer の期") != r.get(u"相手の fact の期"):
        out.append(u"pointer が相手の fact と同じなのに、注入後の pointer の期と相手の fact の期が違う")
    return out


def suite_record_problems(rec_tests, seal):
    u"""Y-10 の試験の欄(``試験``): path と sha256 が現物と同じ・失敗 0・変異の名前が封の字と同じ・戻した。"""
    out = []
    if not isinstance(rec_tests, dict):
        return [u"試験の欄が無い"]
    for key, rel in ((u"既存の試験(偽のまま)", TY.TEST_INJECT_REL), (u"足した試験", TY.TEST_T5_REL)):
        t = rec_tests.get(key) or {}
        if t.get(u"path") != rel or t.get(u"sha256") != sha256_rel(rel):
            out.append(u"試験 %s の path か sha256 が現物と違う" % key)
        if t.get(u"失敗") != 0 or t.get(u"エラー") != 0 or not t.get(u"試験"):
            out.append(u"試験 %s に失敗・エラーがある・試験が 0 本" % key)
    muts = rec_tests.get(u"変異") or []
    if [m.get(u"名前") for m in muts] != list(TY.seal_mutation_names(seal)):
        out.append(u"変異の名前が封の字と違う")
    if any(not m.get(u"戻した") or not isinstance(m.get(u"赤"), int) or m[u"赤"] < 0 for m in muts):
        out.append(u"変異が戻っていない・赤の本数が整数でない")
    if rec_tests.get(u"変異のあと lib が元に戻った") is not True:
        out.append(u"変異のあと lib が元に戻っていない")
    return out


def inject_problems(rec, full):
    out = []
    if rec.get(u"profile") != list(INJECT_PROFILES):
        out.append(u"inject: profile が (P29E, P30E) でない")
    if rec[u"型"].get(u"土台") != BASE_WORD_PIN or TY.BASE_WORD != BASE_WORD_PIN:
        out.append(u"inject: 型.土台 の字が P30E が GROUNDED の claim でない")
    if not all(w in rec[u"型"].get(u"対応付け", u"") for w in (u"(ア)", u"(イ)", u"(ウ)")):
        out.append(u"inject: 型.対応付け に(ア)(イ)(ウ)が無い")
    if rec[u"型"].get(u"上限") != u"1 本あたり %d" % RUN.INJECT_CAP:
        out.append(u"inject: 型.上限 が cap と違う")
    seal = read(SEAL_REL)
    if rec.get(u"限界") != TY.seal_limits(seal) + list(TY.EXTRA_LIMITS) or len(TY.seal_limits(seal)) != 4 or len(TY.EXTRA_LIMITS) != 5:
        out.append(u"inject: 限界が封 §6 の字(4 つ)とこの script の限界(5 つ)と違う")
    if len(TY.EXTRA_LIMITS) != len(EXTRA_LIMITS_PIN) or any(not x.startswith(pin) for x, pin in zip(TY.EXTRA_LIMITS, EXTRA_LIMITS_PIN)):
        out.append(u"inject: script の限界の字が留めた字の頭と違う")
    want = collections.OrderedDict([(u"全体", sum(1 for r in rec[u"行"] if r.get(LINK_KEY) is not True)), (T5, sum(1 for r in rec[u"行"] if r.get(u"型") == T5 and r.get(LINK_KEY) is not True))])
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
        summ, summ_cmp = (norm(x) for x in TY.inject_summaries(rec[u"行"]))
        extras = collections.OrderedDict([
            (TY.BREAKDOWN_KEY, norm(TY.breakdown(rec[u"行"]))), (TY.PARTNER_PERIOD_KEY, norm(TY.partner_period_breakdown(rec[u"行"]))),
            (TY.SAME_ELEMENT_KEY, norm(TY.same_element_breakdown(rec[u"行"]))), (TY.PERIOD_KEY, norm(TY.period_breakdown(rec[u"行"]))),
            (TY.SAME_POINTER_KEY, norm(TY.same_pointer_breakdown(rec[u"行"])))])
    if summ != rec[u"集計"] or rec[u"注入の行の数"] != len(rec[u"行"]):
        out.append(u"inject: 集計が行から作り直した値と違う")
    if list(summ) != [T5]:
        out.append(u"inject: 集計の型が T5 の 1 型でない")
    if summ_cmp != rec.get(TY.COMPARE_KEY):
        out.append(u"inject: 比較用の集計(P29E にも対応が付く site だけ)が行から作り直した値と違う")
    for k, v in extras.items():
        if v != rec.get(k):
            out.append(u"inject: %s が行から作り直した値と違う" % k)
    try:
        cols = norm(TY.y_columns(per, rec[u"行"]))
    except Exception as e:                                   # noqa: BLE001
        return out + [u"inject: Y の欄を作れない(%s)" % type(e).__name__]
    if cols != rec.get(Y_KEY):
        out.append(u"inject: Y の欄が 本ごとの数えと行から作り直した値と違う")
    out += [u"inject: " + x for x in suite_record_problems(rec.get(u"試験"), seal)]
    if full:
        names = [x[u"name"] for src in TY.SOURCES.values() for x in jload(src["claims"])[u"本"] if not x.get(u"欠け")]
        if list(per) != names:
            out.append(u"inject: 本ごとの数えの本が 200 本(前の便の claims の並び)でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(TY.caches_all())):
            out.append(u"inject: cache の件数か名前が記録の前と違う")
    return out


def record_problems(R, full=True):
    u"""記録(R["inject"])の検査(禁止欄・鍵・script と lib と仕掛けと前の便の sha256・engine の指紋・cache・再計算)。問題の列。"""
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
        J = TY.build_Y(R, seal)
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"Y"]) != list(SG.PRED_IDS) or list(J[u"K"]) != list(SG.K_IDS):
        out.append(u"判定の行が Y-1〜Y-10・K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 偽で不変(f)
def off_problems(books, jrec):
    u"""切り替え 2 つ 偽で books(``TY.load_books`` の形)の ``S.t5_sites`` を数え直し、J の記録の T5 の偽(H の切り替え 偽)・真(H の切り替え 真)と本ごとに照らす。"""
    out = []
    if getattr(N, FLAG) or getattr(S, FLAG2):
        return [u"切り替えが真のまま偽の数を数えようとした"]
    jper = jrec[u"本ごとの数え"]
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as work:
        for (src, name, item, row, _p) in books:
            text = RUN.read_text(name, item, TY.SOURCES[src]["cache"])
            refs = RUN.refs_for(row, GEN.EXISTING_CACHES, work)
            a = len(S.t5_sites(text, refs))
            with NS.yen_scan_on():
                b = len(S.t5_sites(text, refs))
            jc = (jper.get(name) or {}).get("T5_COINCIDENT") or {}
            if (a, b) != (jc.get(u"偽"), jc.get(u"真")):
                out.append(u"%s: 偽の site の数 (%s, %s) が J の記録 (%s, %s) と違う" % (name[-8:], a, b, jc.get(u"偽"), jc.get(u"真")))
    if getattr(N, FLAG) or getattr(S, FLAG2):
        out.append(u"数えたあとも切り替えが真のまま")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R, seal):
    J = TY.build_Y(R, seal)
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != TY.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("judge") != TY.render_judge(J, seal).split(u"\n"):
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
ITEMS = PIR.ITEMS
sd = PIR.sd
pop_of = PIR.pop_of
cell = PIR.cell
PASS_, NAMED, OTHER, UNMAPPED = PIR.PASS_, PIR.NAMED, PIR.OTHER, PIR.UNMAPPED
conds_of = PIR.conds_of


def sample_header():
    cache = collections.OrderedDict([("edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": "2" * 64})])
    f = fixed_records()
    return collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"step", u"標本"), (u"HEAD の commit", "3" * 40),
        (u"この script の sha256", sha256_rel(SCRIPT_REL)), (u"生成の script の sha256", sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")),
        (u"生成の記録の sha256", collections.OrderedDict((src, sha256_rel(p["gen"])) for src, p in TY.SOURCES.items())),
        (u"engine の指紋", dict(adapter_xbrl_py_sha256=ENGINE_ADAPTER_PIN, core_py_sha256=f["rb"][u"engine の指紋"]["core_py_sha256"], adapter_xbrl_py_files=16, core_py_files=4, git_commit="3" * 40)),
        (u"種の確認", {u"seed_file": u"x"}), (u"profile", list(INJECT_PROFILES)),
        (u"cache の前後", collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)])),
        (u"J の script の sha256", sha256_rel(PS.JT_SCRIPT_REL)), (u"nscan script の sha256", sha256_rel(PS.NS_SCRIPT_REL)),
        (u"rmix script の sha256", sha256_rel("measure/xbrl_rmix_2026-11-04.py")),
        (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")), (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")),
        (u"J の記録の sha256", sha256_rel(TY.J_RECORD_REL)), (u"H の記録の sha256", sha256_rel(TY.H_RECORD_REL)), (u"RB の記録の sha256", sha256_rel(TY.RB_RECORD_REL)),
        (u"lib の指紋", collections.OrderedDict((rel, sha256_rel(rel)) for rel in LIB_RELS)),
        (u"T9 の script の sha256", sha256_rel(PI.PS_SCRIPT_REL)), (u"T9 の記録の sha256", sha256_rel(PI.PS_RECORD_REL)),
        (u"T9 の第 2 便の script の sha256", sha256_rel(TY.PI_SCRIPT_REL)), (u"T9 の第 2 便の記録の sha256", sha256_rel(TY.PI_RECORD_REL)),
        (u"仕掛けの指紋", collections.OrderedDict((rel, sha256_rel(rel)) for rel in DEVICE_RELS)), (u"範囲", u"標本")])


def trow(item, rid, shape, unit, linked, p29, p30, rt=True, rr=True, lead=False, partner=u"CurrentYear", same_el=False, base_p=u"Prior1Year", post_p=u"CurrentYear",
         same_ptr=False, reached=True, miss30=(), miss29=()):
    u"""標本の行(script の ``inject_text_ty`` の行と同じ欄の並び)。p30 / p29 が None の profile は対応なし(その profile の miss を渡す)。"""
    row = collections.OrderedDict([(u"docID", item["docID"]), (u"form", item["form"]), (u"model", item["model"]), (u"writer", item["writer"]),
                                   ("id", u"%s_%s_%s-%s" % (item["docID"], item["form"], item["model"], rid)), (u"型", T5), (u"形", shape), (u"単位", unit),
                                   (u"基準の claim", u"N%03d" % (len(rid) + 1)), (LINK_KEY, linked), (u"round-trip", rt), (u"読み直し", rr), (u"先頭の位が減った", lead),
                                   (u"相手の fact の期", partner), (u"相手と同じ要素か", same_el), (u"基準の pointer の期", base_p)])
    c30, m30 = conds_of(miss30)
    row["P29E"] = cell(*p29) if (linked and p29 is not None) else TUNE.classify(None, None)
    row["P30E"] = cell(*p30) if p30 is not None else TUNE.classify(None, None)
    row[u"注入後の pointer の期"] = post_p
    row[u"注入後の pointer が相手の fact と同じか"] = same_ptr
    row[u"届いた"] = reached
    if linked:
        c29, m29 = conds_of(miss29)
    else:
        c29, m29 = None, [NO_BASE]
    row[F_COND % "P29E"], row[F_COND % "P30E"] = c29, c30
    row[F_MISS % "P29E"], row[F_MISS % "P30E"] = m29, m30
    return row


def sample_rows():
    a, c = ITEMS[0], ITEMS[2]
    return [
        trow(a, "T5-01", u"複合", u"万円", True, NAMED, NAMED, partner=u"Prior1Year", post_p=u"Prior1Year"),
        trow(a, "T5-02", u"複合", u"万円", True, NAMED, PASS_, partner=u"CurrentYear", same_ptr=True),
        trow(a, "T5-03", u"既存", u"億円", True, NAMED, PASS_, partner=u"Prior1Year", post_p=u"Prior1Year", same_ptr=True),
        trow(a, "T5-04", u"万だけ", u"万円", False, None, OTHER, partner=u"他", post_p=u"他"),
        trow(a, "T5-05", u"複合", u"万円", True, NAMED, None, lead=True, post_p=u"他", reached=False, miss30=(COND_U,)),
        trow(a, "T5-06", u"複合", u"万円", True, None, None, post_p=u"なし", reached=False, miss30=(COND_A,), miss29=(COND_A,)),
        trow(c, "T5-01", u"既存", u"百万円", True, NAMED, NAMED, same_el=True),
        trow(c, "T5-02", u"複合", u"万円", True, None, PASS_, miss29=(COND_U,))]


def tcount(rows, sites, shapes, screen=None, read=None, off=(0, 0), t1=(12, 10), t8=(71, 10), pop=None, cand=0):
    u"""標本の本ごとの数え(行と整合する)。shapes = (既存, 万だけ, 複合)の作れる site。"""
    screen = screen if screen is not None else shapes
    n = len(rows)
    linked = sum(1 for r in rows if r[LINK_KEY])
    pop = pop or pop_of(linked=linked, unlinked=n - linked, not_g=max(sites - n, 0))
    good = pop.get(PS.LINKED, 0) + pop.get(PS.UNLINKED, 0)
    return collections.OrderedDict([
        (u"T5 の site", collections.OrderedDict([
            (u"偽", collections.OrderedDict([(u"H の切り替え 偽", off[0]), (u"H の切り替え 真", off[1])])),
            (u"篩だけの site", collections.OrderedDict([(u"計", sum(screen))] + list(zip(SHAPES, screen)))),
            (u"作れる site", collections.OrderedDict([(u"計", sum(shapes))] + list(zip(SHAPES, shapes)))),
            (u"読み直せる site", read if read is not None else sum(screen)), (u"相手の候補の和", cand)])),
        ("T1_VALUE", collections.OrderedDict([(u"作れる site", t1[0]), (u"採った", t1[1])])), ("T8_REL", collections.OrderedDict([(u"作れる site", t8[0]), (u"採った", t8[1])])),
        (u"作れる site の状態", pop), (u"土台 P30E が GROUNDED の site", good), (u"cap を基準で絞る前に掛けた数", min(RUN.INJECT_CAP, sum(shapes))),
        (u"採った", min(RUN.INJECT_CAP, good)), (u"採った の状態", sd(**dict((k, v) for k, v in {PS.LINKED: linked, PS.UNLINKED: n - linked}.items() if v)))])


def sample_per(rows):
    ra = [r for r in rows if r["docID"] == "DOC1"]
    rc = [r for r in rows if r["docID"] == "DOC3"]
    ca = tcount(ra, 9, (2, 1, 6), screen=(2, 1, 6), read=8, off=(0, 4), cand=120)
    ca[u"採った"] = len(ra)
    ca[u"土台 P30E が GROUNDED の site"] = len(ra)
    cb = collections.OrderedDict([(u"注入しない", u"文に全角の数字がある(select は半角の文を前提にする)")])
    cc = tcount(rc, 2, (1, 0, 1), off=(0, 2), cand=30)
    return collections.OrderedDict([(u"DOC1_F1_m1", ca), (u"DOC2_F5_m2", cb), (u"DOC3_F1_m1", cc)])


def sample_tests(**ov):
    t = collections.OrderedDict([
        (u"既存の試験(偽のまま)", collections.OrderedDict([(u"path", TY.TEST_INJECT_REL), (u"sha256", sha256_rel(TY.TEST_INJECT_REL)), (u"試験", 96), (u"失敗", 0), (u"エラー", 0), (u"skip", 0)])),
        (u"足した試験", collections.OrderedDict([(u"path", TY.TEST_T5_REL), (u"sha256", sha256_rel(TY.TEST_T5_REL)), (u"試験", 22), (u"失敗", 0), (u"エラー", 0), (u"skip", 0)])),
        (u"変異", [collections.OrderedDict([(u"名前", n), (u"試験", 22), (u"赤", 3), (u"戻した", True)]) for n in SG.MUTATION_NAMES_PIN]),
        (u"変異のあと lib が元に戻った", True)])
    t.update(ov)
    return t


def sample_inject():
    rows = sample_rows()
    per = sample_per(rows)
    rec = sample_header()
    rec[u"範囲"] = u"標本"
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"T5 の切り替えの名前", FLAG2),
                                            (u"T5 の切り替え inject の中の値", True), (u"T5 の切り替え 出たあとの値", False), (u"配線の問題", [])])
    rec[u"型"] = collections.OrderedDict([(T5, u"標本"), (u"上限", u"1 本あたり %d" % RUN.INJECT_CAP), (u"土台", BASE_WORD_PIN), (u"対応付け", u"(ア)(イ)(ウ)の 3 つ全部")])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"], rec[TY.COMPARE_KEY] = (norm(x) for x in TY.inject_summaries(rows))
    rec[TY.BREAKDOWN_KEY] = norm(TY.breakdown(rows))
    rec[TY.PARTNER_PERIOD_KEY] = norm(TY.partner_period_breakdown(rows))
    rec[TY.SAME_ELEMENT_KEY] = norm(TY.same_element_breakdown(rows))
    rec[TY.PERIOD_KEY] = norm(TY.period_breakdown(rows))
    rec[TY.SAME_POINTER_KEY] = norm(TY.same_pointer_breakdown(rows))
    rec[u"P29E に対応なしの行の数"] = norm(TY.unlinked_counts(rows))
    rec[Y_KEY] = norm(TY.y_columns(per, rows))
    rec[u"試験"] = sample_tests()
    rec[u"限界"] = TY.seal_limits(read(SEAL_REL)) + list(TY.EXTRA_LIMITS)
    rec[u"行"] = rows
    return norm(rec)


def sample_records():
    f = fixed_records()
    return collections.OrderedDict([("inject", sample_inject()), ("j", f["j"]), ("h", f["h"])])


def sample_y1(**ov):
    d = collections.OrderedDict([(u"T5 の site(H の切り替え 偽)", 0), (u"J の記録の 偽", 0), (u"T5 の site(H の切り替え 真)", 672), (u"J の記録の 真", 672),
                                 (u"J の記録と違う本", 0), (u"T1_VALUE の作れる site が H の記録と違う本", 0), (u"T8_REL の作れる site が H の記録と違う本", 0),
                                 (u"lib の指紋が H の記録と一致", True), (u"本", 154)])
    d.update(ov)
    return d


def sample_y10(**ov):
    d = collections.OrderedDict([("失敗", 0), ("赤", 5), ("変異", 5), ("戻した", True)])
    d.update(ov)
    return d


def sample_cols(**ov):
    u"""判定の関数の境界の試験用: ``y_columns`` と同じ形の欄(幅の真ん中の値)。ov = {"欄::キー": 値} で 1 つだけ替える。"""
    c = collections.OrderedDict([
        (YCOL["Y-2"], collections.OrderedDict([(u"計", 990), (u"複合", 630), (u"万だけ", 90), (u"既存", 270), (u"読み直せる site", 970), (u"篩だけの site", 990), (u"相手の候補の和", 286550)])),
        (YCOL["Y-3"], collections.OrderedDict([(u"採った", 700), (u"うち土台 P30E が GROUNDED の行", 500), (u"作れる site のうち土台 P30E が GROUNDED の site", 800)])),
        (YCOL["Y-4"], collections.OrderedDict([(u"注入の行", 500), (u"id で対応が付く行(P30E)", 480), (u"割合", 96.0)])),
        (YCOL["Y-5"], collections.OrderedDict([(u"通した率(P30E)", 10.0), (u"通した行", 48), (u"対応が付く行", 480), (u"止めた行", 432), (u"うち名指して原本", 324), (u"割合", 75.0)])),
        (YCOL["Y-6"], collections.OrderedDict([(u"通した行", 48), (u"うち注入後の pointer が相手の fact と同じ", 40), (u"割合", 83.3)])),
        (YCOL["Y-7"], collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"届かない行(対応が付く行の中)", 0)])),
        (YCOL["Y-8"], collections.OrderedDict([(u"違う行", 3), (u"両方に対応が付く行", 480)])),
        (YCOL["Y-9"], collections.OrderedDict([(u"相手の期が CurrentYear の行の通した率", 10.0), (u"相手の期が Prior1Year の行の通した率", 12.0), (u"対応が付く行(CurrentYear)", 300), (u"対応が付く行(Prior1Year)", 180)])),
        (u"参考", collections.OrderedDict([(u"届いた行", 500)]))])
    for path, v in ov.items():
        keys = path.split(SEP)
        d = c
        for kk in keys[:-1]:
            d = d[kk]
        d[keys[-1]] = v
    return c


def sample_doc(R, seal):
    J = TY.build_Y(R, seal)
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", TY.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start judge -->", TY.render_judge(J, seal), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"200 本の標本です。" + NOT_GATED, u""])


# ================================================================ (a) 封の字
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def test_a_2_a_changed_character_in_the_seal_turns_the_pin_red(self):
        rows = TY.seal_pred_rows(self.seal)
        for cid, old, new in (("Y-1", "672・一致", "673・一致"), ("Y-1", "672・一致", "672・違う"),
                              ("Y-2", "950〜1,030", "951〜1,030"), ("Y-2", "950〜1,030", "950〜1,031"), ("Y-2", "600〜660", "601〜660"), ("Y-2", "600〜660", "600〜661"),
                              ("Y-2", "80〜100", "81〜100"), ("Y-2", "80〜100", "80〜101"), ("Y-2", "250〜300", "251〜300"), ("Y-2", "250〜300", "250〜301"),
                              ("Y-2", "読み直せる 940〜1,000", "読み直せる 941〜1,000"), ("Y-2", "読み直せる 940〜1,000", "読み直せる 940〜1,001"),
                              ("Y-3", "500〜900", "501〜900"), ("Y-3", "500〜900", "500〜901"), ("Y-3", "300〜700", "301〜700"), ("Y-3", "300〜700", "300〜701"),
                              ("Y-4", "90〜100%", "91〜100%"), ("Y-4", "90〜100%", "90〜99%"),
                              ("Y-5", "3〜20%、60〜95%", "4〜20%、60〜95%"), ("Y-5", "3〜20%、60〜95%", "3〜21%、60〜95%"), ("Y-5", "3〜20%、60〜95%", "3〜20%、61〜95%"),
                              ("Y-5", "3〜20%、60〜95%", "3〜20%、60〜96%"),
                              ("Y-6", "70〜100%", "71〜100%"), ("Y-6", "70〜100%", "70〜99%"),
                              ("Y-7", "0 / 0 / 0", "1 / 0 / 0"), ("Y-7", "0 / 0 / 0", "0 / 1 / 0"), ("Y-7", "0 / 0 / 0", "0 / 0 / 1"),
                              ("Y-8", "0〜10", "0〜11"), ("Y-8", "0〜10", "1〜10"),
                              ("Y-9", "両方 3〜25%", "両方 4〜25%"), ("Y-9", "両方 3〜25%", "両方 3〜26%"),
                              ("Y-10", "失敗 0・赤 5 / 5", "失敗 1・赤 5 / 5"), ("Y-10", "失敗 0・赤 5 / 5", "失敗 0・赤 4 / 5"), ("Y-10", "失敗 0・赤 5 / 5", "失敗 0・赤 5 / 6")):
            self.assertIn(old, rows[cid][1], (cid, old))
            mutated = self.seal.replace("| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1]), "| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1].replace(old, new, 1)), 1)
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], bounds_problems(mutated), (cid, new))

    def test_a_3_the_thresholds_of_k1_to_k4_are_read_from_the_seal(self):
        b = TY.seal_bounds(self.seal)
        self.assertEqual((u"一致", {u"round-trip 不一致": 0, u"読み直し不一致": 0}, 300.0, {u"失敗": 0, u"赤": 5, u"変異": 5}),
                         (b["K-1"], dict(b["K-2"]), b["K-3"], dict(b["K-4"])))
        for old, new in (("Y-7 の round-trip 不一致 0・読み直し不一致 0", "Y-7 の round-trip 不一致 1・読み直し不一致 0"), ("Y-7 の round-trip 不一致 0・読み直し不一致 0", "Y-7 の round-trip 不一致 0・読み直し不一致 1"),
                         ("注入の行 ≥ 300", "注入の行 ≥ 301"), ("Y-10 が 失敗 0・赤 5 / 5", "Y-10 が 失敗 1・赤 5 / 5"), ("Y-10 が 失敗 0・赤 5 / 5", "Y-10 が 失敗 0・赤 4 / 5"),
                         ("Y-10 が 失敗 0・赤 5 / 5", "Y-10 が 失敗 0・赤 5 / 6")):
            self.assertIn(old, self.seal, old)
            self.assertNotEqual([], bounds_problems(self.seal.replace(old, new, 1)), new)


# ================================================================ (c) 判定
class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def J(self, y1=None, y10=None, **ov):
        return TY.judge_from(y1 or sample_y1(), sample_cols(**ov), y10 if y10 is not None else sample_y10(), self.seal)

    def test_c_1_the_middle_of_every_range_is_a_hit_and_adoption_follows(self):
        J = self.J()
        for k, v in J[u"Y"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        for k, v in J[u"K"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        self.assertTrue(J[u"採用"])

    def test_c_2_each_prediction_flips_at_the_seal_boundary(self):
        b = BOUNDS_PIN
        cases = []
        for k, (lo, hi) in b["Y-2"].items():
            cases += [("Y-2", YCOL["Y-2"] + SEP + k, lo, lo - 1), ("Y-2", YCOL["Y-2"] + SEP + k, hi, hi + 1)]
        for k, (lo, hi) in b["Y-3"].items():
            cases += [("Y-3", YCOL["Y-3"] + SEP + k, lo, lo - 1), ("Y-3", YCOL["Y-3"] + SEP + k, hi, hi + 1)]
        lo, hi = b["Y-4"]
        cases += [("Y-4", YCOL["Y-4"] + SEP + u"割合", lo, lo - 0.1), ("Y-4", YCOL["Y-4"] + SEP + u"割合", hi, hi + 0.1)]
        for k, (lo, hi) in b["Y-5"].items():
            cases += [("Y-5", YCOL["Y-5"] + SEP + k, lo, lo - 0.1), ("Y-5", YCOL["Y-5"] + SEP + k, hi, hi + 0.1)]
        lo, hi = b["Y-6"]
        cases += [("Y-6", YCOL["Y-6"] + SEP + u"割合", lo, lo - 0.1), ("Y-6", YCOL["Y-6"] + SEP + u"割合", hi, hi + 0.1)]
        for k, v in b["Y-7"].items():
            cases += [("Y-7", YCOL["Y-7"] + SEP + k, v, v + 1)]
        lo, hi = b["Y-8"]
        cases += [("Y-8", YCOL["Y-8"] + SEP + u"違う行", lo, lo - 1), ("Y-8", YCOL["Y-8"] + SEP + u"違う行", hi, hi + 1)]
        lo, hi = b["Y-9"]
        for k in (u"相手の期が CurrentYear の行の通した率", u"相手の期が Prior1Year の行の通した率"):
            cases += [("Y-9", YCOL["Y-9"] + SEP + k, lo, lo - 0.1), ("Y-9", YCOL["Y-9"] + SEP + k, hi, hi + 0.1)]
        for cid, path, inside, outside in cases:
            self.assertEqual(HIT, self.J(**{path: inside})[u"Y"][cid][u"判定"], (path, inside))
            self.assertEqual(MISS, self.J(**{path: outside})[u"Y"][cid][u"判定"], (path, outside))

    def test_c_2b_a_missing_value_is_a_miss_not_a_hit(self):
        for cid, path in (("Y-4", YCOL["Y-4"] + SEP + u"割合"), ("Y-5", YCOL["Y-5"] + SEP + u"通した率(P30E)"), ("Y-5", YCOL["Y-5"] + SEP + u"割合"), ("Y-6", YCOL["Y-6"] + SEP + u"割合"),
                          ("Y-9", YCOL["Y-9"] + SEP + u"相手の期が CurrentYear の行の通した率"), ("Y-9", YCOL["Y-9"] + SEP + u"相手の期が Prior1Year の行の通した率")):
            self.assertEqual(MISS, self.J(**{path: None})[u"Y"][cid][u"判定"], path)           # 分母が 0 で率が出ない = 外れ(当たりにしない)
        c = sample_cols()
        del c[YCOL["Y-3"]][u"採った"]
        self.assertRaises(KeyError, TY.judge_from, sample_y1(), c, sample_y10(), self.seal)       # 欄が欠けた記録は判定を作れない = 赤(当たりにしない)

    def test_c_2c_y1_needs_every_agreement(self):
        for ov in ({u"J の記録の 偽": 1}, {u"J の記録の 真": 671}, {u"T5 の site(H の切り替え 真)": 673}, {u"T5 の site(H の切り替え 偽)": 1}, {u"J の記録と違う本": 1},
                   {u"T1_VALUE の作れる site が H の記録と違う本": 1}, {u"T8_REL の作れる site が H の記録と違う本": 1}, {u"lib の指紋が H の記録と一致": False},
                   {u"lib の指紋が H の記録と一致": None}, {u"本": 0}):
            J = self.J(y1=sample_y1(**ov))
            self.assertEqual(MISS, J[u"Y"]["Y-1"][u"判定"], ov)
            self.assertEqual(MISS, J[u"K"]["K-1"][u"判定"], ov)
            self.assertFalse(J[u"採用"])

    def test_c_2d_y10_needs_no_failure_every_mutation_red_and_restored(self):
        for ov in ({"失敗": 1}, {"赤": 4}, {"変異": 6}, {"戻した": False}):
            J = self.J(y10=sample_y10(**ov))
            self.assertEqual(MISS, J[u"Y"]["Y-10"][u"判定"], ov)
            self.assertEqual(MISS, J[u"K"]["K-4"][u"判定"], ov)
            self.assertFalse(J[u"採用"])
        J = TY.judge_from(sample_y1(), sample_cols(), None, self.seal)                            # 試験の欄が無い記録
        self.assertEqual(MISS, J[u"Y"]["Y-10"][u"判定"])
        self.assertEqual(MISS, J[u"K"]["K-4"][u"判定"])

    def test_c_3_the_adoption_follows_k1_to_k4(self):
        self.assertFalse(self.J(y1=sample_y1(**{u"J の記録の 偽": 1}))[u"採用"])                                                            # K-1
        for k, path in (("round-trip", YCOL["Y-7"] + SEP + u"round-trip 不一致"), ("読み直し", YCOL["Y-7"] + SEP + u"読み直し不一致")):       # K-2
            J = self.J(**{path: 1})
            self.assertEqual(MISS, J[u"K"]["K-2"][u"判定"], k)
            self.assertFalse(J[u"採用"])
        rows = YCOL["Y-4"] + SEP + u"注入の行"                                                                                              # K-3
        self.assertEqual(HIT, self.J(**{rows: 300})[u"K"]["K-3"][u"判定"])
        J = self.J(**{rows: 299})
        self.assertEqual(MISS, J[u"K"]["K-3"][u"判定"])
        self.assertFalse(J[u"採用"])
        self.assertFalse(self.J(y10=sample_y10(**{"赤": 4}))[u"採用"])                                                                      # K-4

    def test_c_4_k_ignores_the_prediction_misses(self):
        J = self.J(**{YCOL["Y-5"] + SEP + u"通した率(P30E)": 60.0, YCOL["Y-6"] + SEP + u"割合": 10.0, YCOL["Y-2"] + SEP + u"計": 100})
        self.assertEqual(MISS, J[u"Y"]["Y-5"][u"判定"])
        self.assertEqual(MISS, J[u"Y"]["Y-2"][u"判定"])
        self.assertTrue(J[u"採用"])                                                                # 採用は K だけで決まる(率が高くても採用は採用 ― 封 §4)

    def test_c_5_the_judgment_moves_with_the_records(self):
        base = self.J()
        row = TY.seal_pred_rows(self.seal)["Y-8"]
        mutated_seal = self.seal.replace("| Y-8 | %s | %s" % (row[0], row[1]), "| Y-8 | %s | %s" % (row[0], row[1].replace("0〜10", "0〜1", 1)), 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertEqual(MISS, TY.judge_from(sample_y1(), sample_cols(), sample_y10(), mutated_seal)[u"Y"]["Y-8"][u"判定"])
        self.assertNotEqual(norm(base), norm(self.J(**{YCOL["Y-8"] + SEP + u"違う行": 11})))

    def test_c_6_a_broken_record_is_red_not_an_exception(self):
        R = norm(sample_records())
        self.assertEqual([], judge_problems(R, self.seal))
        del R["inject"][u"行"][0]["P30E"]
        self.assertNotEqual([], judge_problems(R, self.seal))
        R2 = norm(sample_records())
        R2["h"].pop(u"lib の指紋")
        self.assertEqual([], judge_problems(R2, self.seal))                                         # lib の指紋が無い H の記録は Y-1 を外れにする(例外にしない)
        self.assertEqual(MISS, TY.build_Y(R2, self.seal)[u"Y"]["Y-1"][u"判定"])
        R3 = norm(sample_records())
        R3["inject"].pop(u"本ごとの数え")
        self.assertNotEqual([], judge_problems(R3, self.seal))

    def test_c_7_y1_is_counted_from_the_per_book_counts_and_the_two_records(self):
        per = collections.OrderedDict([
            ("A", {u"T5 の site": {u"偽": {u"H の切り替え 偽": 0, u"H の切り替え 真": 5}}, "T1_VALUE": {u"作れる site": 3}, "T8_REL": {u"作れる site": 4}}),
            ("B", {u"注入しない": u"x"})])
        j = {u"本ごとの数え": {"A": {"T5_COINCIDENT": {u"偽": 0, u"真": 5}}}}
        h = {u"本ごとの数え": {"A": {"T1_VALUE": {u"作れる site": 3}, "T8_REL": {u"作れる site": 4}}}, u"lib の指紋": {"a": "1"}}
        y = TY.y1_value(per, j, h, {u"lib の指紋": {"a": "1"}})
        self.assertEqual((0, 0, 5, 5, 0, 0, 0, True, 1), tuple(y.values()))
        for j2, h2 in (({u"本ごとの数え": {"A": {"T5_COINCIDENT": {u"偽": 0, u"真": 6}}}}, h),
                       (j, {u"本ごとの数え": {"A": {"T1_VALUE": {u"作れる site": 2}, "T8_REL": {u"作れる site": 4}}}, u"lib の指紋": {"a": "1"}}),
                       (j, {u"本ごとの数え": {"A": {"T1_VALUE": {u"作れる site": 3}, "T8_REL": {u"作れる site": 5}}}, u"lib の指紋": {"a": "1"}})):
            y2 = TY.y1_value(per, j2, h2, {u"lib の指紋": {"a": "1"}})
            self.assertNotEqual(y, y2)
            self.assertEqual(1, sum(1 for k in (u"J の記録と違う本", u"T1_VALUE の作れる site が H の記録と違う本", u"T8_REL の作れる site が H の記録と違う本") if y2[k]))
        self.assertFalse(TY.y1_value(per, j, h, {u"lib の指紋": {"a": "2"}})[u"lib の指紋が H の記録と一致"])
        self.assertIsNone(TY.y1_value(per, j, h)[u"lib の指紋が H の記録と一致"])


# ================================================================ 欄の数え直し(b)・標本の記録(g)
class ColumnsRebuildTest(unittest.TestCase):
    def cols(self, rows):
        return TY.y_columns(sample_per(rows), rows)

    def test_b_1_every_y_column_is_counted_from_the_rows_and_the_per_book_counts(self):
        rows = sample_rows()
        cols = self.cols(rows)
        self.assertEqual(list(YCOL.values()) + [u"参考"], list(cols))
        y2 = cols[YCOL["Y-2"]]
        self.assertEqual((11, 7, 1, 3, 10, 11), (y2[u"計"], y2[u"複合"], y2[u"万だけ"], y2[u"既存"], y2[u"読み直せる site"], y2[u"篩だけの site"]))
        y3 = cols[YCOL["Y-3"]]
        self.assertEqual((11, 8), (y3[u"採った"], y3[u"うち土台 P30E が GROUNDED の行"]))
        y4 = cols[YCOL["Y-4"]]
        self.assertEqual((8, 6, 75.0), (y4[u"注入の行"], y4[u"id で対応が付く行(P30E)"], y4[u"割合"]))
        y5 = cols[YCOL["Y-5"]]
        self.assertEqual((50.0, 3, 6, 3, 2, 66.7), (y5[u"通した率(P30E)"], y5[u"通した行"], y5[u"対応が付く行"], y5[u"止めた行"], y5[u"うち名指して原本"], y5[u"割合"]))
        y6 = cols[YCOL["Y-6"]]
        self.assertEqual((3, 2, 66.7), (y6[u"通した行"], y6[u"うち注入後の pointer が相手の fact と同じ"], y6[u"割合"]))
        y7 = cols[YCOL["Y-7"]]
        self.assertEqual((0, 0, 0), (y7[u"round-trip 不一致"], y7[u"読み直し不一致"], y7[u"届かない行(対応が付く行の中)"]))
        y8 = cols[YCOL["Y-8"]]
        self.assertEqual((2, 4), (y8[u"違う行"], y8[u"両方に対応が付く行"]))
        y9 = cols[YCOL["Y-9"]]
        self.assertEqual((66.7, 50.0, 3, 2), (y9[u"相手の期が CurrentYear の行の通した率"], y9[u"相手の期が Prior1Year の行の通した率"],
                                              y9[u"対応が付く行(CurrentYear)"], y9[u"対応が付く行(Prior1Year)"]))

    def test_b_2_a_changed_row_field_moves_the_column_that_counts_it(self):
        base = norm(self.cols(sample_rows()))

        def moved(idx, key, value, path):
            rows = sample_rows()
            rows[idx][key] = value
            cols = norm(self.cols(rows))
            self.assertNotEqual(base, cols, (key, value))
            got = cols
            ref = base
            for k in path:
                got, ref = got[k], ref[k]
            self.assertNotEqual(ref, got, (key, value, path))
        moved(0, u"round-trip", False, (YCOL["Y-7"], u"round-trip 不一致"))
        moved(0, u"読み直し", False, (YCOL["Y-7"], u"読み直し不一致"))
        moved(0, u"届いた", False, (YCOL["Y-7"], u"届かない行(対応が付く行の中)"))
        moved(1, u"注入後の pointer が相手の fact と同じか", False, (YCOL["Y-6"], u"うち注入後の pointer が相手の fact と同じ"))
        moved(0, u"相手の fact の期", u"CurrentYear", (YCOL["Y-9"], u"対応が付く行(CurrentYear)"))
        moved(1, u"相手の fact の期", u"Prior1Year", (YCOL["Y-9"], u"対応が付く行(Prior1Year)"))
        moved(2, u"相手と同じ要素か", True, (u"参考", u"相手と同じ要素の行"))
        moved(1, u"先頭の位が減った", True, (u"参考", u"先頭の位が減った行"))
        rows = sample_rows()
        rows[0]["P30E"] = cell(*PASS_)
        self.assertEqual(4, norm(self.cols(rows))[YCOL["Y-5"]][u"通した行"])
        rows = sample_rows()
        rows[1]["P30E"] = cell(*NAMED)
        self.assertEqual(2, norm(self.cols(rows))[YCOL["Y-5"]][u"通した行"])

    def test_b_3_the_per_book_counts_move_the_site_columns(self):
        rows = sample_rows()
        per = sample_per(rows)
        base = norm(TY.y_columns(per, rows))
        per2 = copy.deepcopy(per)
        per2[u"DOC1_F1_m1"][u"T5 の site"][u"作れる site"][u"複合"] += 1
        self.assertEqual(base[YCOL["Y-2"]][u"複合"] + 1, TY.y_columns(per2, rows)[YCOL["Y-2"]][u"複合"])
        per3 = copy.deepcopy(per)
        per3[u"DOC3_F1_m1"][u"T5 の site"][u"読み直せる site"] -= 1
        self.assertEqual(base[YCOL["Y-2"]][u"読み直せる site"] - 1, TY.y_columns(per3, rows)[YCOL["Y-2"]][u"読み直せる site"])
        per4 = copy.deepcopy(per)
        per4[u"DOC1_F1_m1"][u"cap を基準で絞る前に掛けた数"] += 1
        self.assertEqual(base[YCOL["Y-3"]][u"採った"] + 1, TY.y_columns(per4, rows)[YCOL["Y-3"]][u"採った"])


class TestsColumnLiveTest(unittest.TestCase):
    u"""Y-10 の試験の欄を作る ``y10_tests`` を実物で通す(既存の試験・足した試験・変異 5 つ)。変異が黙ったら赤。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.tests = TY.y10_tests(ROOT)

    def test_y_1_the_live_tests_column_has_no_failure_and_every_mutation_red(self):
        self.assertEqual([], suite_record_problems(self.tests, self.seal))
        y = TY.y10_value(self.tests)
        self.assertEqual((0, 5, 5, True), (y["失敗"], y["赤"], y["変異"], y["戻した"]))
        self.assertEqual(list(SG.MUTATION_NAMES_PIN), [m[u"名前"] for m in self.tests[u"変異"]])
        self.assertFalse(getattr(N, FLAG))
        self.assertFalse(getattr(S, FLAG2))

    def test_y_2_a_mutation_that_does_nothing_is_counted_as_silent(self):
        @__import__("contextlib").contextmanager
        def nothing():
            yield
        for name in SG.MUTATION_NAMES_PIN:
            with Patch() as pt:
                muts = collections.OrderedDict(TY.MUTATIONS)
                muts[name] = nothing
                pt.set(TY, "MUTATIONS", muts)
                y = TY.y10_value(TY.y10_tests(ROOT))
            self.assertEqual(4, y["赤"], name)
            self.assertEqual(5, y["変異"], name)
            self.assertTrue(y["戻した"], name)
        self.assertEqual((5, 5), (TY.y10_value(TY.y10_tests(ROOT))["赤"], len(TY.MUTATIONS)))

    def test_y_3_a_failing_test_file_is_counted_as_a_failure(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            os.makedirs(os.path.join(d, "measure", "tests"))
            for rel in (TY.TEST_INJECT_REL, TY.TEST_T5_REL):
                with open(os.path.join(d, rel), "w", encoding="utf-8") as fh:
                    fh.write("import unittest\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        self.fail('x')\n")
            r = TY.run_unittests(TY.TEST_T5_REL, "failing_for_t5y_gate", d)
            self.assertEqual((1, 1), (r[u"試験"], r[u"失敗"]))
            self.assertNotEqual(0, TY.y10_value(collections.OrderedDict([(u"既存の試験(偽のまま)", r), (u"足した試験", r), (u"変異", []), (u"変異のあと lib が元に戻った", True)]))["失敗"])

    def test_y_4_the_y10_value_is_none_without_a_tests_column(self):
        self.assertIsNone(TY.y10_value(None))
        self.assertIsNone(TY.y10_value({}))


class SampleRecordTest(unittest.TestCase):
    u"""小さい標本の記録が緑 → 1 つ壊すと赤(g)。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def probe(self, mutate, full=False):
        R = norm(sample_records())
        mutate(R["inject"])
        return record_problems(R, full=full)

    def test_g_1_the_sample_record_is_green(self):
        self.assertEqual([], record_problems(norm(sample_records()), full=False))
        self.assertEqual([], judge_problems(norm(sample_records()), self.seal))

    def test_g_2_each_header_field_turns_it_red(self):
        def setk(k, v):
            return lambda r: r.__setitem__(k, v)
        self.assertNotEqual([], self.probe(setk(u"封の commit", u"0000000")))
        self.assertNotEqual([], self.probe(setk(u"seal", u"docs/x.md")))
        for k in (u"この script の sha256", u"T9 の第 2 便の script の sha256", u"T9 の第 2 便の記録の sha256", u"T9 の script の sha256", u"T9 の記録の sha256", u"J の script の sha256",
                  u"nscan script の sha256", u"rmix script の sha256", u"numfix script の sha256", u"前の便の run script の sha256", u"生成の script の sha256",
                  u"J の記録の sha256", u"H の記録の sha256", u"RB の記録の sha256"):
            self.assertNotEqual([], self.probe(lambda r, k=k: r.__setitem__(k, r[k][:-1] + (u"0" if r[k][-1] != u"0" else u"1"))), k)
        self.assertNotEqual([], self.probe(lambda r: r[u"仕掛けの指紋"].__setitem__(DEVICE_RELS[0], u"0" * 64)))
        self.assertNotEqual([], self.probe(lambda r: r[u"仕掛けの指紋"].__setitem__(DEVICE_RELS[1], u"0" * 64)))
        self.assertNotEqual([], self.probe(lambda r: r[u"仕掛けの指紋"].pop(DEVICE_RELS[1])))
        self.assertNotEqual([], self.probe(lambda r: r[u"lib の指紋"].__setitem__(LIB_RELS[0], u"0" * 64)))
        self.assertNotEqual([], self.probe(lambda r: r[u"生成の記録の sha256"].__setitem__(list(r[u"生成の記録の sha256"])[0], u"0" * 64)))
        self.assertNotEqual([], self.probe(setk(u"profile", [u"P29E"])))

    def test_g_3_the_engine_fingerprint_is_the_pb_value_not_the_rb_value(self):
        self.assertEqual("dc13edfee7a9ac6b900ae610d056424b622b8447491113b78c4debf902bcfee8", ENGINE_ADAPTER_PIN)
        rb_value = fixed_records()["rb"][u"engine の指紋"]["adapter_xbrl_py_sha256"]
        self.assertNotEqual(ENGINE_ADAPTER_PIN, rb_value)                                      # RB の記録の 4ea77c93… とは違う(司令塔の訂正)
        self.assertNotEqual([], self.probe(lambda r: r[u"engine の指紋"].__setitem__("adapter_xbrl_py_sha256", rb_value)))
        self.assertNotEqual([], self.probe(lambda r: r[u"engine の指紋"].__setitem__("adapter_xbrl_py_sha256", ENGINE_ADAPTER_PIN[:-1] + u"0")))
        self.assertNotEqual([], self.probe(lambda r: r[u"engine の指紋"].__setitem__("core_py_sha256", u"0" * 64)))
        self.assertNotEqual([], self.probe(lambda r: r[u"engine の指紋"].pop("core_py_sha256")))

    def test_g_4_cache_and_the_two_switches_turn_it_red(self):
        self.assertNotEqual([], self.probe(lambda r: r[u"cache の前後"].__setitem__(u"変化なし", False)))
        self.assertNotEqual([], self.probe(lambda r: r[u"cache の前後"][u"後"][u"edinet"].__setitem__(u"件数", 4)))
        for k, v in ((u"名前", u"compound_yen_2026_11_05"), (u"T5 の切り替えの名前", u"t5_yen_x"), (u"配線の問題", [u"x"]), (u"inject の中の値", False), (u"出たあとの値", True),
                     (u"T5 の切り替え inject の中の値", False), (u"T5 の切り替え 出たあとの値", True)):
            self.assertNotEqual([], self.probe(lambda r, k=k, v=v: r[u"切り替え"].__setitem__(k, v)), k)
        self.assertNotEqual([], self.probe(lambda r: r[u"切り替え"].pop(u"T5 の切り替えの名前")))
        self.assertNotEqual([], self.probe(lambda r: r.__setitem__(u"範囲", u"標本"), full=True))

    def test_g_5_forbidden_keys_pointer_text_company_names_and_key_like_strings_turn_it_red(self):
        for k in ("span", "value", "recomputed", u"文", u"理由", "pointers", "pointer", u"要素", "element", "context", "label"):
            self.assertNotEqual([], self.probe(lambda r, k=k: r[u"行"][0].__setitem__(k, u"x")), k)
        self.assertNotEqual([], self.probe(lambda r: r[u"行"][0].__setitem__(u"単位", u"xbrl:jppfs_cor:NetSales@CurrentYearDuration")))
        self.assertNotEqual([], self.probe(lambda r: r[u"行"][0].__setitem__(u"form", u"@Prior1YearDuration")))
        self.assertNotEqual([], self.probe(lambda r: r.__setitem__(u"step", u"株式会社テスト")))
        self.assertNotEqual([], self.probe(lambda r: r.__setitem__(u"step", u"sk-" + u"a" * 30)))
        self.assertNotEqual([], self.probe(lambda r: r.__setitem__(u"key_leaks", [u"x"])))

    def test_g_6_a_zeroed_y_column_or_aggregate_turns_it_red(self):
        def zero_all(r):
            for sec in r[Y_KEY].values():
                for k in sec:
                    sec[k] = 0
        self.assertNotEqual([], self.probe(zero_all))
        for y in YCOL.values():
            first = lambda r, y=y: r[Y_KEY][y].__setitem__(list(r[Y_KEY][y])[0], 0 if r[Y_KEY][y][list(r[Y_KEY][y])[0]] else 1)
            self.assertNotEqual([], self.probe(first), y)
        self.assertNotEqual([], self.probe(lambda r: r[Y_KEY].pop(YCOL["Y-9"])))
        for key in (TY.BREAKDOWN_KEY, TY.PARTNER_PERIOD_KEY, TY.SAME_ELEMENT_KEY, TY.PERIOD_KEY, TY.SAME_POINTER_KEY):
            self.assertNotEqual([], self.probe(lambda r, key=key: r.__setitem__(key, {})), key)
        self.assertNotEqual([], self.probe(lambda r: r.__setitem__(u"集計", {})))
        self.assertNotEqual([], self.probe(lambda r: r.__setitem__(TY.COMPARE_KEY, {})))
        self.assertNotEqual([], self.probe(lambda r: r.__setitem__(u"注入の行の数", 99)))
        self.assertNotEqual([], self.probe(lambda r: r.__setitem__(u"P29E に対応なしの行の数", {u"全体": 0, T5: 0})))

    def test_g_7_the_per_book_counts_turn_it_red(self):
        name = u"DOC1_F1_m1"
        for mut in (lambda c: c.__setitem__(u"採った", c[u"採った"] + 1), lambda c: c.__setitem__(u"土台 P30E が GROUNDED の site", 0),
                    lambda c: c.__setitem__(u"cap を基準で絞る前に掛けた数", 1), lambda c: c[u"T5 の site"][u"作れる site"].__setitem__(u"複合", 99),
                    lambda c: c[u"T5 の site"][u"篩だけの site"].__setitem__(u"計", 1), lambda c: c[u"T5 の site"].__setitem__(u"読み直せる site", 99),
                    lambda c: c[u"T5 の site"][u"偽"].__setitem__(u"H の切り替え 偽", -1), lambda c: c[u"T5 の site"].pop(u"偽"),
                    lambda c: c[u"T1_VALUE"].__setitem__(u"採った", 11), lambda c: c[u"T8_REL"].__setitem__(u"採った", 99), lambda c: c[u"作れる site の状態"].clear(),
                    lambda c: c[u"採った の状態"].clear(), lambda c: c.__setitem__(u"採った の状態", {PS.NS.STATUS_NOT_G: 6})):
            self.assertNotEqual([], self.probe(lambda r, mut=mut: mut(r[u"本ごとの数え"][name])))
        self.assertNotEqual([], self.probe(lambda r: r[u"本ごとの数え"].__setitem__(u"DOC2_F5_m2", {u"採った": 0})))
        self.assertNotEqual([], self.probe(lambda r: r[u"本ごとの数え"].pop(u"DOC1_F1_m1")))
        self.assertNotEqual([], self.probe(lambda r: r[u"行"].append(copy.deepcopy(r[u"行"][0]))))                      # 同じ id が 2 回

    def test_g_8_each_row_column_turns_it_red(self):
        rows = lambda r: r[u"行"]
        for mut in (lambda r: rows(r)[0].__setitem__(u"型", u"T9_PRIOR_TO_CURRENT"), lambda r: rows(r)[0].__setitem__(u"id", u"DOC1_F1_m1-T9-01"),
                    lambda r: rows(r)[0].__setitem__(u"形", u"その他"), lambda r: rows(r)[0].__setitem__(u"相手の fact の期", u"なし"),
                    lambda r: rows(r)[0].__setitem__(u"基準の pointer の期", u"Prior2Year"), lambda r: rows(r)[0].__setitem__(u"注入後の pointer の期", u"x"),
                    lambda r: rows(r)[0].__setitem__(u"相手と同じ要素か", u"はい"), lambda r: rows(r)[0].__setitem__(u"届いた", None),
                    lambda r: rows(r)[0].__setitem__(u"round-trip", 1), lambda r: rows(r)[0].__setitem__(u"読み直し", None),
                    lambda r: rows(r)[0].__setitem__(u"注入後の pointer が相手の fact と同じか", None),
                    lambda r: rows(r)[1].__setitem__(u"注入後の pointer の期", u"Prior1Year"),            # pointer が相手と同じなのに期が違う
                    lambda r: rows(r)[4].__setitem__(u"届いた", True),                                    # (ウ)が偽の行が届いた
                    lambda r: rows(r)[5].__setitem__(u"注入後の pointer の期", u"CurrentYear"),            # (ア)が偽の行の期が なし でない
                    lambda r: rows(r)[0].__setitem__(u"先頭の位が減った", True),                          # 複合の行でも Y の欄が動く
                    lambda r: rows(r)[2].__setitem__(u"先頭の位が減った", True),                          # 既存の行が先頭の位が減った
                    lambda r: rows(r)[0].__setitem__(LINK_KEY, u"x"), lambda r: rows(r)[3].__setitem__(LINK_KEY, True),
                    lambda r: rows(r)[0][u"P30E"].__setitem__(u"結果", u"x"), lambda r: rows(r)[0][u"P30E"].__setitem__(u"reason", u"x y"),
                    lambda r: rows(r)[0][u"P30E"].__setitem__(u"対応", False), lambda r: rows(r)[0].__setitem__(F_COND % "P30E", None),
                    lambda r: rows(r)[0][F_COND % "P30E"].__setitem__(COND_I, False), lambda r: rows(r)[0].__setitem__(F_MISS % "P30E", [COND_U]),
                    lambda r: rows(r)[3].__setitem__(F_MISS % "P29E", []), lambda r: rows(r)[0].pop(F_MISS % "P30E")):
            self.assertNotEqual([], self.probe(mut))

    def test_g_9_the_tests_column_turns_it_red(self):
        self.assertNotEqual([], self.probe(lambda r: r.pop(u"試験")))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"][u"既存の試験(偽のまま)"].__setitem__(u"sha256", u"0" * 64)))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"][u"足した試験"].__setitem__(u"path", u"measure/tests/x.py")))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"][u"既存の試験(偽のまま)"].__setitem__(u"失敗", 1)))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"][u"足した試験"].__setitem__(u"エラー", 1)))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"][u"足した試験"].__setitem__(u"試験", 0)))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"][u"変異"].pop()))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"][u"変異"][0].__setitem__(u"名前", u"x")))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"][u"変異"][0].__setitem__(u"戻した", False)))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"][u"変異"][0].__setitem__(u"赤", -1)))
        self.assertNotEqual([], self.probe(lambda r: r[u"試験"].__setitem__(u"変異のあと lib が元に戻った", False)))

    def test_g_10_the_type_block_and_the_limits_turn_it_red(self):
        self.assertNotEqual([], self.probe(lambda r: r[u"型"].__setitem__(u"土台", u"無改変の文で P29E が GROUNDED の claim")))
        self.assertNotEqual([], self.probe(lambda r: r[u"型"].__setitem__(u"対応付け", u"")))
        self.assertNotEqual([], self.probe(lambda r: r[u"型"].__setitem__(u"上限", u"1 本あたり 11")))
        self.assertNotEqual([], self.probe(lambda r: r.__setitem__(u"限界", r[u"限界"][:-1])))
        self.assertNotEqual([], self.probe(lambda r: r[u"限界"].__setitem__(0, r[u"限界"][0] + u"x")))
        self.assertNotEqual([], self.probe(lambda r: r[u"限界"].__setitem__(-1, u"x")))

    def test_g_11_a_cap_overflow_turns_it_red(self):
        def many(r):
            base = r[u"行"][0]
            for i in range(RUN.INJECT_CAP):
                row = copy.deepcopy(base)
                row[u"id"] = u"DOC1_F1_m1-T5-%02d" % (50 + i)
                r[u"行"].append(row)
        self.assertNotEqual([], self.probe(many))


# ================================================================ (f) 偽で不変
class OffInvarianceTest(unittest.TestCase):
    def books(self, n=None):
        books = TY.load_books(ROOT, None)
        return books if n is None else books[:n]

    def test_f_1_the_false_site_counts_of_all_200_books_equal_the_j_record(self):
        if not HAVE_CACHE:
            self.skipTest(u"cache が無い(200 本の偽の数を数えられない)")
        books = self.books()
        self.assertEqual(200, len(books))
        self.assertEqual([], off_problems(books, fixed_records()["j"]))

    def test_f_2_the_off_check_sees_a_broken_false_path(self):
        if not HAVE_CACHE:
            self.skipTest(u"cache が無い")
        books = self.books(4)
        j = fixed_records()["j"]
        self.assertEqual([], off_problems(books, j))
        with Patch() as pt:                                           # 偽のときも円の経路を通す(= 偽の経路が変わった)
            pt.set(S, "t5_sites", lambda text, refs: S.t5_sites_yen(text, refs))
            self.assertNotEqual([], off_problems(books, j))
        j2 = copy.deepcopy(j)
        name = books[0][1]
        j2[u"本ごとの数え"][name]["T5_COINCIDENT"][u"真"] += 1
        self.assertNotEqual([], off_problems(books, j2))
        j3 = copy.deepcopy(j)
        j3[u"本ごとの数え"].pop(name)
        self.assertNotEqual([], off_problems(books, j3))
        S.t5_yen_2026_11_06 = True
        try:
            self.assertNotEqual([], off_problems(books, j))
        finally:
            S.t5_yen_2026_11_06 = False
        self.assertFalse(getattr(S, FLAG2))

    def test_f_3_the_j_record_has_the_expected_false_and_true_totals(self):
        per = fixed_records()["j"][u"本ごとの数え"]
        self.assertEqual((0, 672), (sum(c["T5_COINCIDENT"][u"偽"] for c in per.values()), sum(c["T5_COINCIDENT"][u"真"] for c in per.values())))


# ================================================================ (w) 手順・行の欄(script の関数を小さい入力で通す。zip・判定は偽。lib は本物。通信なし)
TEXT_T = u"売上高は14億3,300万円でした。営業利益は12.3億円でした。\n"
REFS_T = [{"key": "NetSales@CurrentYearDuration", "value": 1433000000.0, "unit": u"円", "label": u"売上高"},
          {"key": "OperatingIncome@Prior1YearDuration", "value": 1230000000.0, "unit": u"円", "label": u"営業利益"}]
#: 相手が同じ要素の別の期(label は違う)になる refs
REFS_SAME = [{"key": "NetSales@CurrentYearDuration", "value": 1433000000.0, "unit": u"円", "label": u"売上高"},
             {"key": "NetSales@Prior1YearDuration", "value": 1230000000.0, "unit": u"円", "label": u"売上高(前期)"}]
PTR_PARTNER_OPERATING = "xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration"
PTR_PARTNER_SALES = "xbrl:jppfs_cor:NetSales@CurrentYearDuration"


def run_ty(text=TEXT_T, refs=REFS_T, patches=(), seed=u"sd", key=u"bk", verify=None, cap=None):
    with Patch() as pt, TY.yen_scan_on(), TY.t5_yen_on():
        pt.set(RUN, "PROFILES", INJECT_PROFILES)
        for mod, name, v in patches:
            pt.set(mod, name, v)
        kw = {} if cap is None else {"cap": cap}
        return TY.inject_text_ty(b"zip", text, refs, seed, key, verify=verify or make_verify(text), **kw)


def capture_build():
    u"""``IJ.build_t5`` を包んで、作った注入(detail を含む)を id の順に貯める。(patches 用の差し替え, 貯めた列)"""
    got = []
    orig = IJ.build_t5

    def wrapped(site, refs, rng):
        inj = orig(site, refs, rng)
        got.append(inj)
        return inj
    return (IJ, "build_t5", wrapped), got


class ProcedureTest(unittest.TestCase):
    def test_w_1_rows_come_from_the_t5_sites_and_carry_every_column(self):
        rows, c = run_ty()
        self.assertEqual(2, len(rows))
        self.assertEqual([], sorted(set(k for r in rows for k in RUN.walk_keys(r) if k in FORBIDDEN_KEYS)))
        self.assertEqual({u"既存": 1, u"万だけ": 0, u"複合": 1}, dict((k, v) for k, v in c[u"T5 の site"][u"作れる site"].items() if k != u"計"))
        self.assertEqual(2, c[u"T5 の site"][u"作れる site"][u"計"])
        self.assertEqual(2, c[u"採った"])
        self.assertEqual({PS.LINKED: 2}, dict(c[u"採った の状態"]))
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))
        want_keys = [u"id", u"型", u"形", u"単位", u"基準の claim", LINK_KEY, u"round-trip", u"読み直し", u"先頭の位が減った", u"相手の fact の期", u"相手と同じ要素か", u"基準の pointer の期",
                     "P29E", "P30E", u"注入後の pointer の期", u"注入後の pointer が相手の fact と同じか", u"届いた", F_COND % "P29E", F_COND % "P30E", F_MISS % "P29E", F_MISS % "P30E"]
        for r in rows:
            self.assertEqual(want_keys, list(r))
            self.assertEqual(T5, r[u"型"])
        self.assertEqual(sorted([u"既存", u"複合"]), sorted(r[u"形"] for r in rows))
        self.assertEqual(["bk-T5-01", "bk-T5-02"], [r[u"id"] for r in rows])
        labels = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
        self.assertEqual([], [x for r in rows for x in row_problems(dict(r, docID=u"D", form=u"F", model=u"m", id=u"D_F_m-" + r[u"id"][3:]), labels, set())])

    def test_w_2_the_columns_are_true_for_an_honest_injection(self):
        patch, got = capture_build()
        rows, _c = run_ty(patches=(patch,))
        self.assertEqual(2, len(got))
        for r, inj in zip(rows, got):
            self.assertTrue(r[u"round-trip"])
            self.assertTrue(r[u"読み直し"])
            self.assertTrue(r[u"届いた"])
            self.assertEqual(TY.partner_period(inj["detail"]["coincident_ref_key"]), r[u"相手の fact の期"])
            self.assertEqual(TY.same_element(inj["detail"]["true_ref_key"], inj["detail"]["coincident_ref_key"]), r[u"相手と同じ要素か"])
            self.assertEqual({u"ア id の claim が在る": True, u"イ 値が注入した値": True, u"ウ span に差し替えの字": True}, dict(r[F_COND % "P30E"]))
            self.assertEqual([], r[F_MISS % "P30E"])
        by_shape = dict((r[u"形"], (r, inj)) for r, inj in zip(rows, got))
        comp, comp_inj = by_shape[u"複合"]
        self.assertEqual(u"万円", comp[u"単位"])
        self.assertEqual("OperatingIncome@Prior1YearDuration", comp_inj["detail"]["coincident_ref_key"])
        self.assertEqual(u"Prior1Year", comp[u"相手の fact の期"])
        self.assertEqual(u"12億3,000", comp_inj["replacement"])
        exist, exist_inj = by_shape[u"既存"]
        self.assertEqual(u"億円", exist[u"単位"])
        self.assertEqual("NetSales@CurrentYearDuration", exist_inj["detail"]["coincident_ref_key"])
        self.assertEqual(u"CurrentYear", exist[u"相手の fact の期"])
        self.assertEqual(u"14.3", exist_inj["replacement"])
        self.assertFalse(comp[u"相手と同じ要素か"])

    def test_w_3_the_same_element_column_follows_the_two_keys(self):
        rows, _c = run_ty(refs=REFS_SAME)
        self.assertEqual([True, True], [r[u"相手と同じ要素か"] for r in rows])
        rows2, _c2 = run_ty(refs=REFS_T)
        self.assertEqual([False, False], [r[u"相手と同じ要素か"] for r in rows2])

    def test_w_4_the_pointer_columns_follow_the_id_claim_pointers(self):
        for ptr, want in ((PTR_PARTNER_OPERATING, {u"複合": True, u"既存": False}), (PTR_PARTNER_SALES, {u"複合": False, u"既存": True})):
            rows, _c = run_ty(verify=make_verify(TEXT_T, base_ptr=PSR.PTR_PRIOR, inj_ptr=ptr))
            self.assertEqual(want, dict((r[u"形"], r[u"注入後の pointer が相手の fact と同じか"]) for r in rows), ptr)
            for r in rows:
                self.assertEqual(r[u"注入後の pointer の期"] if r[u"注入後の pointer が相手の fact と同じか"] else None, r[u"相手の fact の期"] if r[u"注入後の pointer が相手の fact と同じか"] else None)
        rows, _c = run_ty(verify=make_verify(TEXT_T, base_ptr=PSR.PTR_PRIOR, inj_ptr="xbrl:jppfs_cor:Other@CurrentYearDuration"))
        self.assertEqual([False, False], [r[u"注入後の pointer が相手の fact と同じか"] for r in rows])
        self.assertEqual([u"CurrentYear", u"CurrentYear"], [r[u"注入後の pointer の期"] for r in rows])
        rows, _c = run_ty(verify=make_verify(TEXT_T, base_ptr=PSR.PTR_PRIOR, inj_ptr=PTR_PARTNER_OPERATING.replace("xbrl:jppfs_cor:", "xbrl:")))   # 名前空間の接頭辞が無くても同じ key
        self.assertTrue(dict((r[u"形"], r[u"注入後の pointer が相手の fact と同じか"]) for r in rows)[u"複合"])

    def test_w_5_the_pointer_key_function_strips_the_namespace_only(self):
        self.assertEqual("NetSales@CurrentYearDuration", TY.pointer_key("xbrl:jppfs_cor:NetSales@CurrentYearDuration"))
        self.assertEqual("NetSales@CurrentYearDuration", TY.pointer_key("xbrl:NetSales@CurrentYearDuration"))
        self.assertIsNone(TY.pointer_key("table:x"))
        self.assertIsNone(TY.pointer_key("xbrl:NetSales"))
        self.assertIsNone(TY.pointer_key(None))
        self.assertTrue(TY.pointer_is_partner([PTR_PARTNER_SALES], "NetSales@CurrentYearDuration"))
        self.assertFalse(TY.pointer_is_partner([PTR_PARTNER_SALES], "NetSales@Prior1YearDuration"))
        self.assertFalse(TY.pointer_is_partner([], "NetSales@CurrentYearDuration"))
        self.assertFalse(TY.pointer_is_partner(None, "NetSales@CurrentYearDuration"))
        self.assertFalse(TY.pointer_is_partner(["xbrl:x:Other@CurrentYearDuration", PTR_PARTNER_SALES], "NetSales@CurrentYearDuration"))      # 先頭だけ見る

    def test_w_6_partner_period_and_same_element_functions(self):
        self.assertEqual(u"CurrentYear", TY.partner_period("A@CurrentYearDuration"))
        self.assertEqual(u"CurrentYear", TY.partner_period("A@CurrentYearInstant_Member"))
        self.assertEqual(u"Prior1Year", TY.partner_period("A@Prior1YearDuration"))
        self.assertEqual(u"他", TY.partner_period("A@Prior2YearDuration"))
        self.assertEqual(u"他", TY.partner_period("A"))
        self.assertTrue(TY.same_element("A@CurrentYearDuration", "A@Prior1YearDuration"))
        self.assertFalse(TY.same_element("A@CurrentYearDuration", "B@CurrentYearDuration"))

    def test_w_7_round_trip_is_false_when_the_revert_does_not_give_the_original_back(self):
        rows, _c = run_ty(patches=((IJ, "revert", lambda tampered, chosen, placements, original: tampered),))
        self.assertEqual([False, False], [r[u"round-trip"] for r in rows])
        rows, _c = run_ty()
        self.assertEqual([True, True], [r[u"round-trip"] for r in rows])

    def test_w_8_reread_is_false_when_the_text_carries_another_value(self):
        orig = IJ.build_t5

        def off_by_one(site, refs, rng):
            inj = orig(site, refs, rng)
            inj["new_value"] = inj["new_value"] + 1
            return inj
        rows, _c = run_ty(patches=((IJ, "build_t5", off_by_one),))
        self.assertEqual([False, False], [r[u"読み直し"] for r in rows])

    def test_w_9_each_missing_condition_turns_the_mapping_off_and_names_the_missing_one(self):
        for edit, miss, reached in ((PIR.edit_drop_id, [COND_A, COND_I, COND_U], False), (PIR.edit_wrong_value, [COND_I], True), (PIR.edit_cut_span, [COND_U], False)):
            rows, _c = run_ty(verify=PIR.verify_edit(TEXT_T, edit))
            for r in rows:
                self.assertEqual(miss, r[F_MISS % "P30E"], edit.__name__)
                self.assertFalse(r["P30E"][u"対応"])
                self.assertEqual(reached, r[u"届いた"], edit.__name__)
            self.assertEqual([], [x for r in rows for x in cond_problems(r, "P30E")])
        rows, _c = run_ty(verify=PIR.verify_edit(TEXT_T, PIR.edit_drop_id, only_profile="P30E"))
        self.assertTrue(all(r["P29E"][u"対応"] for r in rows))                                  # P29E は別に引く

    def test_w_10_the_cap_is_applied_after_the_base_filter(self):
        rows, c = run_ty(cap=1)
        self.assertEqual(1, len(rows))
        self.assertEqual(1, c[u"採った"])
        self.assertEqual(1, c[u"cap を基準で絞る前に掛けた数"])
        self.assertEqual(2, c[u"T5 の site"][u"作れる site"][u"計"])
        self.assertEqual([], count_problems(u"bk", c, rows, 1))

    def test_w_11_a_fullwidth_digit_book_is_skipped(self):
        rows, c = run_ty(text=u"売上高は１４億３，３００万円でした。\n")
        self.assertEqual([], rows)
        self.assertIn(u"注入しない", c)

    def test_w_12_the_job_refuses_a_switch_that_is_off(self):
        args = ("s", "n", {}, {}, "t", {}, "sd", "w")
        with self.assertRaises(GEN.Stop):
            TY.inject_job_ty(args)
        with TY.yen_scan_on():
            with self.assertRaises(GEN.Stop):
                TY.inject_job_ty(args)                                       # H の切り替えだけ真
        with TY.t5_yen_on():
            with self.assertRaises(GEN.Stop):
                TY.inject_job_ty(args)                                       # T5 の切り替えだけ真

    def test_w_13_the_script_uses_the_lib_site_function_and_the_inject_builder(self):
        rows, _c = run_ty(patches=((S, "t5_sites", lambda text, refs: []),))
        self.assertEqual([], rows)
        patch, got = capture_build()
        run_ty(patches=(patch,))
        self.assertEqual(2, len(got))                                        # 差し替えは IJ.build_t5 を通る
        orig = IJ.build_t5

        def other_replacement(site, refs, rng):
            inj = orig(site, refs, rng)
            inj["replacement"] = u"1"
            inj["new_value"] = 1.0
            return inj
        rows2, _c2 = run_ty(patches=((IJ, "build_t5", other_replacement),))
        self.assertEqual(2, len(rows2))
        self.assertEqual([u"複合"], [r[u"形"] for r in rows2 if r[u"先頭の位が減った"]])       # 差し替えの字「1」は複合の先頭の位を落とす
        self.assertEqual([], [r[u"形"] for r in run_ty()[0] if r[u"先頭の位が減った"]])

    def test_w_14_the_false_site_counts_are_taken_with_the_t5_switch_off(self):
        refs = REFS_T + [{"key": "Count@CurrentYearDuration", "value": 50.0, "unit": None, "label": u"人数"}]
        rows, c = run_ty(refs=refs)
        off = c[u"T5 の site"][u"偽"]
        self.assertEqual({u"H の切り替え 偽": 1, u"H の切り替え 真": 1}, dict(off))              # 書かれた値(12.3)で比べる経路は 50 を相手にできる(円で比べる真では相手にならない)
        self.assertEqual(2, c[u"T5 の site"][u"作れる site"][u"計"])
        self.assertEqual(2, len(rows))
        self.assertFalse(getattr(S, FLAG2))
        self.assertFalse(getattr(N, FLAG))

    def test_w_15_the_h_counts_come_from_the_h_functions(self):
        fake = lambda text, refs, base_claims, base_by_id, seed, key, cap: ([], collections.OrderedDict([(u"作れる site", 77), (u"採った", 3)]))
        _rows, c = run_ty(patches=((NS, "t8_candidates_new", fake),))
        self.assertEqual({u"作れる site": 77, u"採った": 3}, dict(c["T8_REL"]))
        _rows, c0 = run_ty()
        self.assertNotEqual(77, c0["T8_REL"][u"作れる site"])

    def test_w_16_the_readable_site_count_uses_the_first_three_of_the_unit_preferred_pool(self):
        with TY.yen_scan_on():
            screen = S.t5_sites_yen(TEXT_T, REFS_T, False)
            self.assertEqual(2, len(screen))
            self.assertTrue(all(TY.head3_readable(s) for s in screen))
            with Patch() as pt:
                pt.set(S, "t5_readable", lambda t, v: False)
                self.assertFalse(any(TY.head3_readable(s) for s in screen))

    def test_w_16b_the_t8_count_is_taken_with_the_run_cap_and_the_base_claims(self):
        seen = []

        def spy(text, refs, base_claims, base_by_id, seed, key, cap):
            seen.append((seed, key, cap, sorted(base_claims), sorted(base_by_id)))
            return [], collections.OrderedDict([(u"作れる site", 5), (u"採った", 1)])
        run_ty(patches=((NS, "t8_candidates_new", spy),), cap=3)
        self.assertEqual([(u"sd", u"bk", 3, ["P29E", "P30E"], ["P29E", "P30E"])], seen)
        seen[:] = []
        run_ty(patches=((NS, "t8_candidates_new", spy),))
        self.assertEqual(RUN.INJECT_CAP, seen[0][2])

    def test_w_16c_the_readable_count_needs_the_first_three_readable_and_not_the_rest(self):
        ref = {"key": "R@c", "label": u"A", "unit": u"円", "value": 1.0}
        with TY.yen_scan_on():
            tok = [t for t in N.scan(u"売上は12.3億円でした。\n") if t.unit == u"億円"][0]
        others = [{"key": "o%d@c" % i, "label": u"B", "unit": u"円", "value": float(1000 + i)} for i in range(5)]
        site = {"token": tok, "ref": ref, "others": others}

        def readable_for(ok):
            return lambda t, v: int(round(v)) - 1000 in ok
        with Patch() as pt:
            pt.set(S, "t5_readable", readable_for({0, 1, 2}))
            self.assertTrue(TY.head3_readable(site))                       # 先頭 3 件が読めて 4 件目以降が読めなくても真
            pt.set(S, "t5_readable", readable_for({0, 1, 2, 3, 4}))
            self.assertTrue(TY.head3_readable(site))
            pt.set(S, "t5_readable", readable_for({1, 2, 3, 4}))
            self.assertFalse(TY.head3_readable(site))                      # 先頭の 1 件が読めない
            pt.set(S, "t5_readable", readable_for({0, 1, 3, 4}))
            self.assertFalse(TY.head3_readable(site))                      # 3 件目が読めない
            pt.set(S, "t5_readable", readable_for({0, 2}))
            self.assertFalse(TY.head3_readable(site))
        same_unit = dict(others[3], unit=u"円")
        other_unit = [dict(o, unit=u"千円") for o in others[:3]] + [same_unit]
        site2 = {"token": tok, "ref": ref, "others": other_unit}
        with Patch() as pt:
            pt.set(S, "t5_readable", lambda t, v: int(round(v)) == 1003)
            self.assertTrue(TY.head3_readable(site2))                      # 相手の単位の優先: 本当の参照と同じ単位の相手だけが pool になる

    def test_w_17_the_switches_are_back_to_false_after_a_run(self):
        run_ty()
        self.assertFalse(getattr(N, FLAG))
        self.assertFalse(getattr(S, FLAG2))

    def test_w_18_the_site_order_is_the_start_order_then_the_sealed_shuffle_and_the_builder_continues_the_same_rng(self):
        import random
        refs = REFS_T
        with TY.yen_scan_on(), TY.t5_yen_on():
            sites = sorted(S.t5_sites(TEXT_T, refs), key=lambda s: s["token"].start)
            want = list(sites)
            rng = random.Random("sd|bk|T5_COINCIDENT")
            rng.shuffle(want)
            state_after = rng.getstate()
            got, rng2 = TY.t5_all_sites(TEXT_T, refs, u"sd", u"bk")
        self.assertEqual([s["token"].start for s in want], [s["token"].start for s in got])
        self.assertEqual(state_after, rng2.getstate())                       # 並べ替えに使った同じ Random の続きを差し替えに渡す
        # 別の種・別の本の名前では並べ替えが変わりうる(種の字が型の名前を含む)
        seen = set()
        for i in range(12):
            with TY.yen_scan_on(), TY.t5_yen_on():
                g, _r = TY.t5_all_sites(TEXT_T, refs, u"sd%d" % i, u"bk")
            seen.add(tuple(s["token"].start for s in g))
        self.assertEqual(2, len(seen))
        captured = []
        orig = IJ.build_t5

        def spy(site, refs_, rng_):
            captured.append(rng_.getstate())
            return orig(site, refs_, rng_)
        rows, _c = run_ty(patches=((IJ, "build_t5", spy),))
        self.assertEqual(2, len(rows))
        self.assertEqual(state_after, captured[0])                                # 最初に差し替える site には並べ替えの直後の乱数の状態が渡る
        self.assertEqual(T5, rows[0][u"型"])
        first_shape = PS.shape_of_token(want[0]["token"])
        self.assertEqual(first_shape, rows[0][u"形"])                              # 行の並びは並べ替えた順

    def test_w_19_the_header_the_script_writes_passes_the_header_check(self):
        cache = collections.OrderedDict([("edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": "2" * 64})])
        h = TY.header_ty(ROOT, u"標本", {u"seed_file": u"x"}, cache, copy.deepcopy(cache), INJECT_PROFILES)
        h[u"範囲"] = u"全 200 本"
        h[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"T5 の切り替えの名前", FLAG2),
                                              (u"T5 の切り替え inject の中の値", True), (u"T5 の切り替え 出たあとの値", False), (u"配線の問題", [])])
        h = norm(h)
        self.assertEqual([], header_problems(h, True))
        for k in (u"仕掛けの指紋", u"T9 の第 2 便の script の sha256", u"T9 の第 2 便の記録の sha256", u"この script の sha256", u"封の commit", u"seal"):
            h2 = copy.deepcopy(h)
            h2.pop(k)
            self.assertNotEqual([], header_problems(h2, True), k)
        self.assertEqual(SEAL_REL, h[u"seal"])
        self.assertEqual(SEAL_COMMIT_SHORT, h[u"封の commit"])
        self.assertEqual(sorted(DEVICE_RELS), sorted(h[u"仕掛けの指紋"]))


# ================================================================ (d) 文書
class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_d_1_the_sample_document_is_green_and_a_changed_character_turns_it_red(self):
        R = norm(sample_records())
        doc = sample_doc(R, self.seal)
        self.assertEqual([], doc_problems(doc, R, self.seal))
        lines = doc.split(u"\n")
        row = [i for i, ln in enumerate(lines) if ln.startswith(u"| Y-5 |")][0]
        mutated = lines[:]
        mutated[row] = mutated[row][:-3] + u"x" + mutated[row][-2:]
        self.assertNotEqual([], doc_problems(u"\n".join(mutated), R, self.seal))
        jrow = [i for i, ln in enumerate(lines) if ln.startswith(u"| K-3 |")][0]
        mutated = lines[:]
        mutated[jrow] = mutated[jrow].replace(u"当たり", u"外れ") if u"当たり" in mutated[jrow] else mutated[jrow].replace(u"外れ", u"当たり")
        self.assertNotEqual([], doc_problems(u"\n".join(mutated), R, self.seal))
        verdict = u"**採用**" if u"**採用**" in doc else u"**見送り**"
        other = u"**見送り**" if verdict == u"**採用**" else u"**採用**"
        self.assertNotEqual([], doc_problems(doc.replace(verdict, other), R, self.seal))

    def test_d_2_a_forbidden_word_a_docid_a_foreign_table_or_an_ungated_number_turns_it_red(self):
        R = norm(sample_records())
        doc = sample_doc(R, self.seal)
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(doc + u"\n" + w + u"\n", R, self.seal), w)
        self.assertNotEqual([], doc_problems(doc + u"\nS100" + u"ABCD\n", R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n<!-- 門:start other -->\nx\n<!-- 門:end -->\n", R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n通した行は 123 件でした。\n", R, self.seal))
        self.assertEqual([], doc_problems(doc + u"\n通した行は 123 件でした。" + NOT_GATED + u"\n", R, self.seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"<!-- 門:start pred -->", u"<!-- 門:start pred2 -->"), R, self.seal))

    def test_d_3_the_tables_follow_the_record(self):
        R = norm(sample_records())
        doc = sample_doc(R, self.seal)
        R2 = norm(sample_records())
        R2["inject"][u"行"][1]["P30E"] = cell(*NAMED)
        R2["inject"][Y_KEY] = norm(TY.y_columns(R2["inject"][u"本ごとの数え"], R2["inject"][u"行"]))
        self.assertNotEqual([], doc_problems(doc, R2, self.seal))


# ================================================================ 宣言(docID を持つ記録は LATER_NAMING_FILES に、script は LATER_HARNESS_FILES に宣言する)
literal_assign = PSR.literal_assign
later_naming_files = PSR.later_naming_files


def naming_problems(src):
    got = later_naming_files(src)
    if got is None:
        return [u"LATER_NAMING_FILES が読めない"]
    return [u"LATER_NAMING_FILES に %s が無い" % rel for rel in REC_REL.values() if rel not in got] + \
        [u"LATER_NAMING_FILES に docID を持たない %s がある" % rel for rel in [SCRIPT_REL, DOC_REL] + list(SG.GATE_RELS) + list(SG.TEST_RELS) if rel in got]


def harness_problems(src):
    node = literal_assign(src, "LATER_HARNESS_FILES")
    if node is None:
        return [u"LATER_HARNESS_FILES が読めない"]
    rows = [r for r in ast.literal_eval(node) if r[0] == SCRIPT_REL]
    if len(rows) != 1:
        return [u"LATER_HARNESS_FILES に %s が 1 回だけ無い" % SCRIPT_REL]
    if u"inject" in os.path.basename(SCRIPT_REL) or u"false_pass" in os.path.basename(SCRIPT_REL):
        return [u"script の file 名に inject・false_pass が入っている(引きの門が名前で数える)"]
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
                    "fixtures/xbrl/numfix/ai200_2026-11-04.json", "fixtures/xbrl/jtypes/inject_2026-11-05.json", "fixtures/xbrl/pswap/inject_2026-11-06.json",
                    "fixtures/xbrl/pswap/inject_idmap_2026-11-06.json"):
            self.assertIn(rel, got)

    def test_h_3_the_script_is_declared_as_a_harness_file(self):
        src = read("tests/measure/test_xbrl_inject_harness_review.py")
        self.assertEqual([], harness_problems(src))
        self.assertNotEqual([], harness_problems(src.replace(u'"%s"' % SCRIPT_REL, u'"x/%s"' % SCRIPT_REL)))
        self.assertNotEqual([], harness_problems(src.replace("LATER_HARNESS_FILES", "LATER_HARNESS_FILE")))
        self.assertIn("measure/xbrl_pswap_idmap_2026-11-06.py", src)


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


# ================================================================ 本番の記録(a)(b)(d)(e)(f)
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
        J = TY.build_Y(R, self.seal)
        self.assertEqual(set(J), {u"Y", u"K", u"採用", u"欄"})

    def test_r_3_the_result_document_follows_the_records(self):
        R = self.need()
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), R, self.seal))

    def test_r_4_order_is_seal_then_records_and_document(self):
        self.need()
        self.assertEqual([], order_of(REPO))

    def test_r_5_the_false_site_counts_in_the_record_equal_the_j_record_and_the_live_count(self):
        R = self.need()
        y1 = TY.y1_value(R["inject"][u"本ごとの数え"], R["j"], R["h"], R["inject"])
        self.assertEqual((0, 0, 672, 672, 0, 0, 0, True), tuple(list(y1.values())[:8]))


class SkipLineTest(unittest.TestCase):
    def test_s_1_a_skipped_real_record_test_still_prints_a_line(self):
        u"""記録が無いと本番の記録の試験は skip になるが、skip でも行が出る(黙って消えない)。"""
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(RealRecordsTest)
        n = suite.countTestCases()
        self.assertGreaterEqual(n, 5)
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
