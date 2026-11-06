# -*- coding: utf-8 -*-
"""T9 の第 2 便(注入後の claim を基準の claim の id で引く対応付け。切り替え ``yen_scan_2026_11_05``)の測定の結果の門。封 docs/XBRL_PERIOD_SWAP_IDMAP_SEAL_2026-11-06.md §1・§3・§4・§5。

記録 1 つ(``fixtures/xbrl/pswap/inject_idmap_2026-11-06.json``)と、読むだけの H の記録・RB の記録・**T9 の記録**から、封 §3 の予測 Q-1〜Q-10 と §4 の採用の基準 K-1〜K-4 を**機械で求め**(予測の幅は封の字から読む。字のコピーにしない)、
結果の文書 ``docs/XBRL_PERIOD_SWAP_IDMAP_RESULT_2026-11-06.md`` の表(``<!-- 門:start pred -->``・``<!-- 門:start judge -->`` の中)を記録から作り直した表と一行も違わないことを見る。
測定の script(``measure/xbrl_pswap_idmap_2026-11-06.py`` の ``build_Q``・``judge_from``・``q_columns``・``render_pred``・``render_judge``)の関数を呼んで照らす。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文・pointer・要素など)が無い・pointer の字(要素名)を持たない・key_leaks が空・docID を持つ記録が ``LATER_NAMING_FILES`` に宣言され、
     script が ``LATER_HARNESS_FILES`` に宣言されている・cache の前後が同じ・script と lib と前の便(T9 を含む)の script・記録の sha256 が現物と一致・engine の指紋が封の commit の木から作り直した値と一致する・切り替えの欄。
  b  記録の中身が再計算と一致する: 本ごとの数えの整合・行の整合(対応の 3 条件と欠けた条件・旧の対応・届いた・pointer の期の間の関係)・集計・形別・手がかり別・通した行の期の内訳・
     **Q の欄の全部を 行と T9 の記録から数え直す**(欄を 0 に固定すると赤。行の欄を 1 つ変えると該当の欄が動く)・限界(封 §6 の字 + script の限界)。
  c  判定: 記録(の欄)を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。採用は K-1〜K-4 を全部満たすときだけ。
     **T9 の記録を壊した写し**(id を 1 つ変える・旧で付いた行の state を 1 つ変える)で Q-2・Q-5・K-4 が赤になる。
  d  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 ec00fa1 ⊏ 記録・結果の文書(script・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  g  変異: 小さい標本の記録と文書で同じ検査が緑 → 変異(記録の数・Q の欄・表の 1 字・封の予測の 1 字・順序・記録の禁止欄・指紋の 1 字・cache の前後・切り替え・pointer の字・期の欄・対応の条件・旧の対応の欄)で赤。
  w  手順・**対応付けと行の欄**: script の ``inject_text_pi`` を小さい入力(zip・判定は偽。lib は本物)で通し、(ア)(イ)(ウ)を 1 つずつ欠いた claim の列
     (id が無い・値が違う・span に字が無い・id は同じだが値が別の claim・同じ値の claim が 2 件在っても id で 1 件に決まる)で 対応 / 対応なし と欠けた条件の欄が動くこと、旧の対応の欄、
     T9 の関数(site・行の欄)を差し替えると行が動くこと、T9 の script の行と同じ欄が同じ値であることを、壊した差し替えで True ↔ False が替わる例で固定する。

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


SG = load_module("tests/measure/test_xbrl_pswap_idmap_seal.py", "pswap_idmap_seal_gate_for_result")     # 封の門の部品。門としては走らせない
PSR = load_module("tests/measure/test_xbrl_pswap_result.py", "pswap_result_gate_for_idmap_result")      # T9 の結果の門の部品(標本の組み立て・偽の verify)。門としては走らせない
PR = SG.PR
PI = SG.PI
PS = PI.PS
JT = PI.JT
NS = PI.NS
RM, NF, GEN, RUN, TUNE, IJ, S = PI.RM, PI.NF, PI.GEN, PI.RUN, PI.TUNE, PI.IJ, PI.S
N, SC = PI.N, PI.SC

SEAL_REL = PI.SEAL_REL
DOC_REL = PI.DOC_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
REC_REL = collections.OrderedDict(PI.REC_REL)
SCRIPT_REL = PI.SCRIPT_REL
LIB_RELS = PI.LIB_RELS
FLAG = PI.FLAG
T9 = PI.T9
NOT_GATED = PR.NOT_GATED
HIT, MISS = PI.HIT, PI.MISS
SHAPES = PI.SHAPES
PERIODS = PI.PERIODS
LINK_KEY = PI.LINK_KEY
CONDS = PI.CONDS
COND_A, COND_I, COND_U = PI.COND_A, PI.COND_I, PI.COND_U
NO_BASE = PI.NO_BASE
F_COND, F_MISS, F_OLD, F_SAMEN = PI.F_COND, PI.F_MISS, PI.F_OLD, PI.F_SAMEN
OLD_KEYS = PI.OLD_KEYS
QCOL = PI.QCOL
Q_KEY = PI.Q_KEY
FORBIDDEN_KEYS = PSR.FORBIDDEN_KEYS
COMPANY_WORDS = PSR.COMPANY_WORDS
POINTER_TEXT_RE = PSR.POINTER_TEXT_RE
DOCID_RE = SG.DOCID_RE
FOR_RESULT_WORDS = PSR.FOR_RESULT_WORDS
HAVE_CACHE = all(os.path.isdir(p) for p in PI.caches_all().values())
INJECT_PROFILES = PI.INJECT_PROFILES
Patch = PSR.Patch
norm = PSR.norm
norm_t = PSR.norm_t
walk = PSR.walk
walk_strings = PSR.walk_strings
read = PSR.read
jload = PSR.jload
sha256_rel = PSR.sha256_rel
G, V_, U_, P_ = PSR.G, PSR.V_, PSR.U_, PSR.P_
PTR_PRIOR, PTR_CUR = PSR.PTR_PRIOR, PSR.PTR_CUR
make_verify = PSR.make_verify
TEXT_P, REFS_P = PSR.TEXT_P, PSR.REFS_P
count_problems = PSR.count_problems
#: 封 §3・§4 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("Q-1", u"一致"), ("Q-2", 141),
    ("Q-3", collections.OrderedDict([(u"P30E で対応が付く行", 141), (u"P29E で対応が付く行", 141), (u"注入の前後で claim の数が同じ行", 141)])),
    ("Q-4", collections.OrderedDict([(u"旧の対応付けが付く行(P30E)", 13), (u"うち id で引いた claim と同じ claim の行", 13)])),
    ("Q-5", collections.OrderedDict([(u"P29E・P30E の結果と state が T9 の記録と同じ行", 13), (u"旧の対応付けが付いた行(P30E)", 13)])),
    ("Q-6", collections.OrderedDict([(u"通した率(P30E)", (55.0, 95.0)), (u"旧で付かなかった行の通した率", (50.0, 95.0))])),
    ("Q-7", collections.OrderedDict([(u"割合", (95.0, 100.0)), (u"手がかり真の行の通した率", (55.0, 95.0))])),
    ("Q-8", (0, 6)),
    ("Q-9", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"先頭の位が減った行", 1), (u"届いた行", 141)])),
    ("Q-10", (60.0, 100.0)),
    ("K-1", u"一致"), ("K-2", collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0)])), ("K-3", 130.0),
    ("K-4", collections.OrderedDict([(u"P29E・P30E の結果と state が T9 の記録と同じ行", 13), (u"旧の対応付けが付いた行(P30E)", 13)]))])
#: 注入の土台の字・site の字(測定の script の定数と同じでなければ赤)
BASE_WORD_PIN = u"無改変の文で P30E が GROUNDED の claim"
SITE_WORD_PIN = u"ref の context が Prior1Year で始まり、同じ要素の CurrentYear の fact がちょうど 1 件・単位が同じ・両方正・値が違い、当期の値を元の字の形で描ける数(既存・万だけ・複合の全部)"
#: この script の限界(封 §6 の 4 つの後ろに足した 5 つ)の字の頭(literal に留める。script の字を変えたら赤)
EXTRA_LIMITS_PIN = (u"対応付けは profile ごとの土台の claim の id で引く", u"「届いた」と注入後の pointer の期は id で引いた claim(P30E)で決める",
                    u"Q-3 の「注入の前後で claim の数が同じ行」は P30E の claim の数", u"Q-5 は旧の対応付け(P30E)が付いた行について", u"Q-2 の id の集合は T9 の記録と比べる")
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
INFO_Q1 = (u"lib の指紋が H の記録と一致", u"engine の指紋が RB の記録と一致", u"inject.py・sites.py・T9 の script が封の commit から変わった file")
SEP = u"::"                                  # sample_cols の path の区切り(欄の名前に / が入るため)
UNMAPPED_CELL = {u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}


def records_exist():
    if FORCE["no_records"]:
        return False
    return all(os.path.exists(os.path.join(ROOT, v)) for v in REC_REL.values())


_FIXED = {}


def fixed_records():
    u"""読むだけの H の記録・RB の記録・T9 の記録(1 回だけ読む)。"""
    if not _FIXED:
        _FIXED["h"] = jload(PI.H_RECORD_REL)
        _FIXED["rb"] = jload(PI.RB_RECORD_REL)
        _FIXED["t9"] = jload(PI.PS_RECORD_REL)
    return _FIXED


def load_records():
    f = fixed_records()
    return collections.OrderedDict([("inject", jload(REC_REL["inject"])), ("h", f["h"]), ("rb", f["rb"]), ("t9", f["t9"])])


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
def bounds_problems(seal):
    u"""封の字から読んだ予測の幅が、ここに留めた値と同じか。"""
    out = []
    try:
        got = PI.seal_bounds(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return [u"封から幅を読めない(%s)" % type(e).__name__]
    for k, v in BOUNDS_PIN.items():
        g = got.get(k)
        if json.dumps(norm_t(g), sort_keys=True) != json.dumps(norm_t(v), sort_keys=True):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, g, v))
    if list(PI.seal_pred_rows(seal)) != list(SG.PRED_IDS) or list(PI.seal_k_rows(seal)) != list(SG.K_IDS):
        out.append(u"封の予測の行が Q-1〜Q-10 でない・K の行が K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 記録(a)(b)
def header_problems(rec, full):
    u"""記録の頭(封・script・lib・前の便(T9 を含む)の script と記録・engine・cache・切り替え)。"""
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"封の名か commit が違う")
    want = collections.OrderedDict([
        (u"この script の sha256", sha256_rel(SCRIPT_REL)), (u"T9 の script の sha256", sha256_rel(PI.PS_SCRIPT_REL)), (u"T9 の記録の sha256", sha256_rel(PI.PS_RECORD_REL)),
        (u"J の script の sha256", sha256_rel(PS.JT_SCRIPT_REL)), (u"nscan script の sha256", sha256_rel(PS.NS_SCRIPT_REL)),
        (u"rmix script の sha256", sha256_rel("measure/xbrl_rmix_2026-11-04.py")), (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")),
        (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")), (u"生成の script の sha256", sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")),
        (u"J の記録の sha256", sha256_rel(PS.JT_RECORD_REL)), (u"H の記録の sha256", sha256_rel(PI.H_RECORD_REL)), (u"RB の記録の sha256", sha256_rel(PI.RB_RECORD_REL))])
    for name, v in want.items():
        if rec.get(name) != v:
            out.append(u"%s が現物と違う" % name)
    gens = dict((src, sha256_rel(p["gen"])) for src, p in PI.SOURCES.items())
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
        PI.assert_clean_pi(copy.deepcopy(rec))
    except GEN.Stop:
        out.append(u"鍵らしい字が記録に在る")
    if rec.get(u"key_leaks", []) != []:
        out.append(u"key_leaks が空でない")
    return out


def cond_problems(r, p):
    u"""行の profile p の対応の条件・欠けた条件・P30E / P29E の欄の間の関係。"""
    out = []
    conds, miss, cell = r.get(F_COND % p), r.get(F_MISS % p), r[p]
    if conds is None:                                                   # 土台に対応が付かない profile(P29E だけ)
        if p != "P29E" or r.get(LINK_KEY) is not False:
            out.append(u"%s の対応の条件が なし なのは P29E の土台に対応が付かない行だけ" % p)
        if miss != [NO_BASE]:
            out.append(u"%s の欠けた条件が 土台なし でない" % p)
        if norm(cell) != UNMAPPED_CELL:
            out.append(u"%s の欄が対応なしでない" % p)
        return out
    if not isinstance(conds, dict) or list(conds) != list(CONDS) or any(not isinstance(v, bool) for v in conds.values()):
        return [u"%s の対応の条件が (ア)(イ)(ウ)の真偽でない" % p]
    if not conds[COND_A] and (conds[COND_I] or conds[COND_U]):
        out.append(u"%s: (ア)が偽なのに(イ)か(ウ)が真" % p)
    if miss != [k for k in CONDS if not conds[k]]:
        out.append(u"%s の欠けた条件が条件の真偽から数え直した値と違う" % p)
    if cell[u"対応"] is not all(conds.values()):
        out.append(u"%s の欄の対応が 3 つの条件が全部真かと合わない" % p)
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
    if not isinstance(linked, bool):
        out.append(u"P29E の土台に対応の欄が真偽でない")
    elif not linked and norm(r["P29E"]) != UNMAPPED_CELL:
        out.append(u"P29E の土台に対応が無い行の P29E の欄が対応なしでない")
    for key in (u"round-trip", u"読み直し", u"先頭の位が減った", u"届いた", u"engine の手がかり", u"文に前期の語", F_SAMEN):
        if not isinstance(r.get(key), bool):
            out.append(u"行の %s が真偽でない" % key)
    if r.get(u"形") not in SHAPES:
        out.append(u"行の形が語でない")
    if r.get(u"単位") is not None and (not isinstance(r.get(u"単位"), str) or not r.get(u"単位")):
        out.append(u"行の単位が語でも None でもない")                          # 単位の無い数(件数など)にも在る
    if r[u"先頭の位が減った"] and r[u"形"] != u"複合":
        out.append(u"先頭の位が減ったのは複合だけ")
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
        old = r.get(F_OLD % p)
        if not isinstance(old, dict) or list(old) != list(OLD_KEYS) or any(not isinstance(v, bool) for v in old.values()):
            out.append(u"%s の旧の対応の欄が (付いた, 同じ id) の真偽でない" % p)
        elif old[OLD_KEYS[1]] and not old[OLD_KEYS[0]]:
            out.append(u"%s: 旧の対応が付かないのに同じ id" % p)
    c30 = r.get(F_COND % "P30E") or {}
    if r[u"届いた"] and not c30.get(COND_U):
        out.append(u"(ウ)が偽の行が届いた")
    if c30.get(COND_A) is False and r.get(u"注入後の pointer の期") != u"なし":
        out.append(u"id の claim が無い行の注入後の pointer の期が なし でない")
    return out


def inject_problems(rec, t9_rows, full):
    out = []
    if rec.get(u"profile") != list(INJECT_PROFILES):
        out.append(u"inject: profile が (P29E, P30E) でない")
    if rec[u"型"].get(u"土台") != BASE_WORD_PIN or PI.BASE_WORD != BASE_WORD_PIN:
        out.append(u"inject: 型.土台 の字が P30E が GROUNDED の claim でない")
    if rec[u"型"].get(u"site") != SITE_WORD_PIN or PI.SITE_WORD != SITE_WORD_PIN:
        out.append(u"inject: 型.site の字が留めた字と違う")
    if not all(w in rec[u"型"].get(u"対応付け", u"") for w in (u"(ア)", u"(イ)", u"(ウ)")):
        out.append(u"inject: 型.対応付け に(ア)(イ)(ウ)が無い")
    seal = read(SEAL_REL)
    if rec.get(u"限界") != PI.seal_limits(seal) + list(PI.EXTRA_LIMITS) or len(PI.seal_limits(seal)) != 4 or len(PI.EXTRA_LIMITS) != 5:
        out.append(u"inject: 限界が封 §6 の字(4 つ)とこの script の限界(5 つ)と違う")
    if len(PI.EXTRA_LIMITS) != len(EXTRA_LIMITS_PIN) or any(not x.startswith(pin) for x, pin in zip(PI.EXTRA_LIMITS, EXTRA_LIMITS_PIN)):
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
        summ, summ_cmp = (norm(x) for x in PI.inject_summaries(rec[u"行"]))
        bd = norm(PI.breakdown(rec[u"行"]))
        cb = norm(PI.cue_breakdown(rec[u"行"]))
        pb = norm(PI.period_breakdown(rec[u"行"]))
    if summ != rec[u"集計"] or rec[u"注入の行の数"] != len(rec[u"行"]):
        out.append(u"inject: 集計が行から作り直した値と違う")
    if list(summ) != [T9]:
        out.append(u"inject: 集計の型が T9 の 1 型でない")
    if summ_cmp != rec.get(PI.COMPARE_KEY):
        out.append(u"inject: 比較用の集計(P29E にも対応が付く site だけ)が行から作り直した値と違う")
    if bd != rec.get(PI.BREAKDOWN_KEY):
        out.append(u"inject: 形別の内訳が行から作り直した値と違う")
    if cb != rec.get(PI.CUE_KEY):
        out.append(u"inject: engine の手がかり別の内訳が行から作り直した値と違う")
    if pb != rec.get(PI.PERIOD_KEY):
        out.append(u"inject: 通した行の注入後の pointer の期の内訳が行から作り直した値と違う")
    try:
        cols = norm(PI.q_columns(rec[u"行"], t9_rows))
    except Exception as e:                                   # noqa: BLE001
        return out + [u"inject: Q の欄を作れない(%s)" % type(e).__name__]
    if cols != rec.get(Q_KEY):
        out.append(u"inject: Q の欄が 行 と T9 の記録の 行 から作り直した値と違う")
    if full:
        names = [x[u"name"] for src in PI.SOURCES.values() for x in jload(src["claims"])[u"本"] if not x.get(u"欠け")]
        if list(per) != names:
            out.append(u"inject: 本ごとの数えの本が 200 本(前の便の claims の並び)でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(PI.caches_all())):
            out.append(u"inject: cache の件数か名前が記録の前と違う")
    return out


def record_problems(R, full=True):
    u"""記録(R["inject"])の検査(禁止欄・鍵・script と lib と前の便の sha256・engine の指紋・cache・再計算)。R["t9"] = T9 の記録。問題の列。"""
    rec = R["inject"]
    out = []

    def safe(label, fn, *a):
        try:
            return fn(*a)
        except Exception as e:                               # noqa: BLE001  壊れた記録は検査できない = 赤(例外で落とさず問題に数える)
            return [u"%s: 検査できない(%s)" % (label, type(e).__name__)]
    out += safe("clean", clean_problems, rec)
    out += safe("header", header_problems, rec, full)
    out += safe("inject", inject_problems, rec, R["t9"][u"行"], full)
    return out


def judge_problems(R, seal):
    u"""判定の関数が記録から作り直せるか(壊れた記録は赤)。"""
    try:
        J = PI.build_Q(R, seal, [])
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"Q"]) != list(SG.PRED_IDS) or list(J[u"K"]) != list(SG.K_IDS):
        out.append(u"判定の行が Q-1〜Q-10・K-1〜K-4 でない")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R, seal, numstat=()):
    J = PI.build_Q(R, seal, list(numstat))
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != PI.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("judge") != PI.render_judge(J, seal).split(u"\n"):
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
ITEMS = PSR.ITEMS
sd = PSR.sd
pop_of = PSR.pop_of
cell = PSR.cell
PASS_, NAMED, OTHER, UNMAPPED = PSR.PASS_, PSR.NAMED, PSR.OTHER, PSR.UNMAPPED


def sample_header():
    cache = collections.OrderedDict([("edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": "2" * 64})])
    return collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"step", u"標本"), (u"HEAD の commit", "3" * 40),
        (u"この script の sha256", sha256_rel(SCRIPT_REL)), (u"生成の script の sha256", sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")),
        (u"生成の記録の sha256", collections.OrderedDict((src, sha256_rel(p["gen"])) for src, p in PI.SOURCES.items())),
        (u"engine の指紋", dict(engine_fingerprint_at_seal(), adapter_xbrl_py_files=16, core_py_files=4, git_commit="3" * 40)),
        (u"種の確認", {u"seed_file": u"x"}), (u"profile", list(INJECT_PROFILES)),
        (u"cache の前後", collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)])),
        (u"J の script の sha256", sha256_rel(PS.JT_SCRIPT_REL)), (u"nscan script の sha256", sha256_rel(PS.NS_SCRIPT_REL)),
        (u"rmix script の sha256", sha256_rel("measure/xbrl_rmix_2026-11-04.py")),
        (u"numfix script の sha256", sha256_rel("measure/xbrl_numfix_2026-11-04.py")), (u"前の便の run script の sha256", sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")),
        (u"T9 の script の sha256", sha256_rel(PI.PS_SCRIPT_REL)), (u"T9 の記録の sha256", sha256_rel(PI.PS_RECORD_REL)),
        (u"J の記録の sha256", sha256_rel(PS.JT_RECORD_REL)), (u"H の記録の sha256", sha256_rel(PI.H_RECORD_REL)), (u"RB の記録の sha256", sha256_rel(PI.RB_RECORD_REL)),
        (u"lib の指紋", collections.OrderedDict((rel, sha256_rel(rel)) for rel in LIB_RELS)), (u"範囲", u"標本")])


def conds_of(miss):
    u"""欠けた条件の列 → (ア)(イ)(ウ)の真偽。(ア)が欠ければ(イ)(ウ)も欠ける。"""
    miss = set(miss)
    if COND_A in miss:
        miss = set(CONDS)
    return collections.OrderedDict((k, k not in miss) for k in CONDS), [k for k in CONDS if k in miss]


def irow(item, rid, shape, unit, linked, p29, p30, rt=True, rr=True, lead=False, cue=True, word=True, base_p=u"Prior1Year", post_p=u"Prior1Year", reached=False,
         miss30=(), miss29=(), old30=(False, False), old29=(False, False), samen=True):
    u"""標本の行(T9 の行の欄 + 対応の条件・欠けた条件・旧の対応・claim の数)。p30 / p29 が None の profile は対応なし(その profile の miss を渡す)。"""
    row = collections.OrderedDict([(u"docID", item["docID"]), (u"form", item["form"]), (u"model", item["model"]), (u"writer", item["writer"]),
                                   ("id", u"%s_%s_%s-%s" % (item["docID"], item["form"], item["model"], rid)), (u"型", T9), (u"形", shape), (u"単位", unit),
                                   (u"基準の claim", u"N%03d" % (len(rid) + 1)), (LINK_KEY, linked), (u"round-trip", rt), (u"読み直し", rr), (u"先頭の位が減った", lead),
                                   (u"engine の手がかり", cue), (u"文に前期の語", word), (u"基準の pointer の期", base_p)])
    c30, m30 = conds_of(miss30)
    row["P29E"] = cell(*p29) if (linked and p29 is not None) else TUNE.classify(None, None)
    row["P30E"] = cell(*p30) if p30 is not None else TUNE.classify(None, None)
    row[u"注入後の pointer の期"] = post_p
    row[u"届いた"] = reached
    if linked:
        c29, m29 = conds_of(miss29)
    else:
        c29, m29 = None, [NO_BASE]
    row[F_COND % "P29E"], row[F_COND % "P30E"] = c29, c30
    row[F_MISS % "P29E"], row[F_MISS % "P30E"] = m29, m30
    row[F_OLD % "P29E"] = collections.OrderedDict(zip(OLD_KEYS, old29))
    row[F_OLD % "P30E"] = collections.OrderedDict(zip(OLD_KEYS, old30))
    row[F_SAMEN] = samen
    return row


def sample_rows():
    a, c = ITEMS[0], ITEMS[2]
    return [
        irow(a, "T9-01", u"複合", u"万円", True, NAMED, NAMED, reached=True, old30=(True, True), old29=(True, True)),
        irow(a, "T9-02", u"複合", u"万円", True, NAMED, PASS_, post_p=u"CurrentYear", reached=True),
        irow(a, "T9-03", u"既存", u"円", True, NAMED, PASS_, cue=False, word=False, base_p=u"他", post_p=u"CurrentYear", reached=True),
        irow(a, "T9-04", u"万だけ", u"万円", False, None, OTHER, post_p=u"他", reached=True),
        irow(a, "T9-05", u"複合", u"万円", True, NAMED, None, lead=True, post_p=u"他", miss30=(COND_U,)),
        irow(a, "T9-06", u"複合", u"万円", True, None, None, post_p=u"なし", miss30=(COND_A,), miss29=(COND_A,), samen=False),
        irow(c, "T9-01", u"既存", None, True, NAMED, NAMED, reached=True, old30=(True, True), old29=(True, True)),
        irow(c, "T9-02", u"複合", u"万円", True, None, PASS_, post_p=u"CurrentYear", reached=True, miss29=(COND_U,))]


def sample_t9_rows(rows):
    u"""標本の T9 の記録の行: 旧の対応(P30E)が付いた行は同じ判定、付かない行は対応なし(T9 の記録は旧の対応付けで判定した)。"""
    out = []
    for r in rows:
        old = r[F_OLD % "P30E"][OLD_KEYS[0]]
        out.append({u"id": r[u"id"], u"P29E": copy.deepcopy(r["P29E"]) if old else copy.deepcopy(UNMAPPED_CELL),
                    u"P30E": copy.deepcopy(r["P30E"]) if old else copy.deepcopy(UNMAPPED_CELL)})
    return out


def sample_per():
    ca = PSR.t9_count((9, 9, 8, 7), 1, 1, 5, 6, pop_of(linked=5, unlinked=1, not_g=1), sd(**{PI.LINKED: 5, PI.UNLINKED: 1}))
    ca[u"採った"] = 6
    ca[u"土台 P30E が GROUNDED の site"] = 6
    cb = collections.OrderedDict([(u"注入しない", u"文に全角の数字がある(select は半角の文を前提にする)")])
    cc = PSR.t9_count((4, 4, 3, 3), 1, 0, 2, 2, pop_of(linked=2, no_base=1), sd(**{PI.LINKED: 2}))
    return collections.OrderedDict([(u"DOC1_F1_m1", ca), (u"DOC2_F5_m2", cb), (u"DOC3_F1_m1", cc)])


def sample_inject(t9_rows=None):
    rows = sample_rows()
    per = sample_per()
    rec = sample_header()
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
    rec[u"型"] = collections.OrderedDict([(u"site", SITE_WORD_PIN), (u"土台", BASE_WORD_PIN), (u"対応付け", u"(ア)(イ)(ウ)の 3 つ全部")])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"], rec[PI.COMPARE_KEY] = (norm(x) for x in PI.inject_summaries(rows))
    rec[PI.BREAKDOWN_KEY] = norm(PI.breakdown(rows))
    rec[PI.CUE_KEY] = norm(PI.cue_breakdown(rows))
    rec[PI.PERIOD_KEY] = norm(PI.period_breakdown(rows))
    rec[u"P29E に対応なしの行の数"] = norm(PI.unlinked_counts(rows))
    rec[Q_KEY] = norm(PI.q_columns(rows, t9_rows if t9_rows is not None else sample_t9_rows(rows)))
    rec[u"限界"] = PI.seal_limits(read(SEAL_REL)) + list(PI.EXTRA_LIMITS)
    rec[u"行"] = rows
    return norm(rec)


def sample_records():
    f = fixed_records()
    inj = sample_inject()
    return collections.OrderedDict([("inject", inj), ("h", f["h"]), ("rb", f["rb"]), ("t9", {u"行": sample_t9_rows(inj[u"行"])})])


def sample_q1(**ov):
    d = collections.OrderedDict([(INFO_Q1[0], True), (INFO_Q1[1], True), (INFO_Q1[2], 0)])
    d.update(ov)
    return d


def sample_cols(**ov):
    u"""判定の関数の境界の試験用: ``q_columns`` と同じ形の欄(幅の真ん中の値)。ov = {"欄::キー::...": 値} で 1 つだけ替える。"""
    c = collections.OrderedDict([
        (QCOL["Q-2"], collections.OrderedDict([(u"行の数", 141), (u"T9 の記録の行の数", 141), (u"id の集合が T9 の記録と同じ", True), (u"T9 の記録にだけ在る id", 0), (u"この記録にだけ在る id", 0)])),
        (QCOL["Q-3"], collections.OrderedDict([(u"P30E で対応が付く行", 141), (u"P29E で対応が付く行", 141), (u"注入の前後で claim の数が同じ行", 141)])),
        (QCOL["Q-4"], collections.OrderedDict([(u"旧の対応付けが付く行(P30E)", 13), (u"うち id で引いた claim と同じ claim の行", 13)])),
        (QCOL["Q-5"], collections.OrderedDict([(u"旧の対応付けが付いた行(P30E)", 13), (u"P29E・P30E の結果と state が T9 の記録と同じ行", 13)])),
        (QCOL["Q-6"], collections.OrderedDict([(u"通した率(P30E)", 75.0), (u"通した行", 106), (u"id で対応が付く行", 141), (u"旧で付かなかった行の通した率", 74.2),
                                               (u"旧で付かなかった行の通した行", 95), (u"旧で付かなかった行", 128)])),
        (QCOL["Q-7"], collections.OrderedDict([(u"通した行", 106), (u"うち注入後の pointer の期が CurrentYear", 105), (u"割合", 99.1), (u"手がかり真の行の通した率", 75.0),
                                               (u"対応が付く行のうち手がかり真", 120)])),
        (QCOL["Q-8"], collections.OrderedDict([(u"違う行", 2), (u"両方に対応が付く行", 141)])),
        (QCOL["Q-9"], collections.OrderedDict([(u"round-trip 不一致", 0), (u"読み直し不一致", 0), (u"先頭の位が減った行", 1), (u"届いた行", 141)])),
        (QCOL["Q-10"], collections.OrderedDict([(u"対応が付く行", 141), (u"止めた行", 35), (u"うち名指して原本", 30), (u"割合", 85.7)])),
        (u"参考", collections.OrderedDict([(u"文に前期の語がある行", 137), (u"手がかり真の行(全部)", 129)]))])
    for path, v in ov.items():
        keys = path.split(SEP)
        d = c
        for kk in keys[:-1]:
            d = d[kk]
        d[keys[-1]] = v
    return c


def sample_doc(R, seal):
    J = PI.build_Q(R, seal, [])
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", PI.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start judge -->", PI.render_judge(J, seal), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"200 本の標本です。" + NOT_GATED, u""])


# ================================================================ (a) 封の字
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def test_a_2_a_changed_character_in_the_seal_turns_the_pin_red(self):
        rows = PI.seal_pred_rows(self.seal)
        for cid, old, new in (("Q-1", "一致", "不一致"),
                              ("Q-2", "141・同じ", "142・同じ"), ("Q-2", "141・同じ", "141・違う"),
                              ("Q-3", "141 / 141・141", "140 / 141・141"), ("Q-3", "141 / 141・141", "141 / 140・141"), ("Q-3", "141 / 141・141", "141 / 141・140"),
                              ("Q-4", "13・13", "14・13"), ("Q-4", "13・13", "13・12"), ("Q-5", "13 / 13", "12 / 13"), ("Q-5", "13 / 13", "13 / 14"),
                              ("Q-6", "55〜95%、50〜95%", "56〜95%、50〜95%"), ("Q-6", "55〜95%、50〜95%", "55〜96%、50〜95%"), ("Q-6", "55〜95%、50〜95%", "55〜95%、51〜95%"),
                              ("Q-6", "55〜95%、50〜95%", "55〜95%、50〜96%"),
                              ("Q-7", "95〜100%、55〜95%", "96〜100%、55〜95%"), ("Q-7", "95〜100%、55〜95%", "95〜99%、55〜95%"), ("Q-7", "95〜100%、55〜95%", "95〜100%、56〜95%"),
                              ("Q-7", "95〜100%、55〜95%", "95〜100%、55〜96%"),
                              ("Q-8", "0〜6", "0〜7"), ("Q-8", "0〜6", "1〜6"),
                              ("Q-9", "0 / 0 / 1 / 141", "1 / 0 / 1 / 141"), ("Q-9", "0 / 0 / 1 / 141", "0 / 1 / 1 / 141"), ("Q-9", "0 / 0 / 1 / 141", "0 / 0 / 2 / 141"),
                              ("Q-9", "0 / 0 / 1 / 141", "0 / 0 / 1 / 140"),
                              ("Q-10", "60〜100%", "61〜100%"), ("Q-10", "60〜100%", "60〜99%")):
            self.assertIn(old, rows[cid][1], (cid, old))
            mutated = self.seal.replace("| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1]), "| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1].replace(old, new, 1)), 1)
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], bounds_problems(mutated), (cid, new))

    def test_a_3_the_thresholds_of_k1_to_k4_are_read_from_the_seal(self):
        b = PI.seal_bounds(self.seal)
        self.assertEqual((u"一致", {u"round-trip 不一致": 0, u"読み直し不一致": 0}, 130.0, {u"P29E・P30E の結果と state が T9 の記録と同じ行": 13, u"旧の対応付けが付いた行(P30E)": 13}),
                         (b["K-1"], dict(b["K-2"]), b["K-3"], dict(b["K-4"])))
        for old, new in (("Q-9 の round-trip 不一致 0・読み直し不一致 0", "Q-9 の round-trip 不一致 1・読み直し不一致 0"), ("Q-9 の round-trip 不一致 0・読み直し不一致 0", "Q-9 の round-trip 不一致 0・読み直し不一致 1"),
                         ("id で対応が付く行(P30E)≥ 130", "id で対応が付く行(P30E)≥ 131"), ("Q-5 が 13 / 13", "Q-5 が 12 / 13"), ("Q-5 が 13 / 13", "Q-5 が 13 / 12")):
            self.assertIn(old, self.seal, old)
            self.assertNotEqual([], bounds_problems(self.seal.replace(old, new, 1)), new)


# ================================================================ (c) 判定
class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def J(self, q1=None, **ov):
        return PI.judge_from(q1 or sample_q1(), sample_cols(**ov), self.seal)

    def test_c_1_the_middle_of_every_range_is_a_hit_and_adoption_follows(self):
        J = self.J()
        for k, v in J[u"Q"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        for k, v in J[u"K"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        self.assertTrue(J[u"採用"])

    def test_c_2_each_prediction_flips_at_the_seal_boundary(self):
        b = BOUNDS_PIN
        K2, K3, K4, K5, K6, K7, K9, K10 = (QCOL["Q-%d" % i] for i in (2, 3, 4, 5, 6, 7, 9, 10))
        cases = [("Q-2", K2 + SEP + u"行の数", 141, 140), ("Q-2", K2 + SEP + u"行の数", 141, 142), ("Q-2", K2 + SEP + u"id の集合が T9 の記録と同じ", True, False)]
        for k in b["Q-3"]:
            cases += [("Q-3", K3 + SEP + k, 141, 140), ("Q-3", K3 + SEP + k, 141, 142)]
        for k in b["Q-4"]:
            cases += [("Q-4", K4 + SEP + k, 13, 12), ("Q-4", K4 + SEP + k, 13, 14)]
        for k in b["Q-5"]:
            cases += [("Q-5", K5 + SEP + k, 13, 12), ("Q-5", K5 + SEP + k, 13, 14)]
        for k, (lo, hi) in b["Q-6"].items():
            cases += [("Q-6", K6 + SEP + k, lo, lo - 0.1), ("Q-6", K6 + SEP + k, hi, hi + 0.1)]
        for k, (lo, hi) in b["Q-7"].items():
            cases += [("Q-7", K7 + SEP + k, lo, lo - 0.1), ("Q-7", K7 + SEP + k, hi, hi + 0.1)]
        lo, hi = b["Q-8"]
        cases += [("Q-8", QCOL["Q-8"] + SEP + u"違う行", lo, lo - 1), ("Q-8", QCOL["Q-8"] + SEP + u"違う行", hi, hi + 1)]
        for k, v in b["Q-9"].items():
            cases += [("Q-9", K9 + SEP + k, v, v + 1), ("Q-9", K9 + SEP + k, v, v - 1)]
        lo, hi = b["Q-10"]
        cases += [("Q-10", K10 + SEP + u"割合", lo, lo - 0.1), ("Q-10", K10 + SEP + u"割合", hi, hi + 0.1)]
        for cid, path, inside, outside in cases:
            self.assertEqual(HIT, self.J(**{path: inside})[u"Q"][cid][u"判定"], (path, inside))
            self.assertEqual(MISS, self.J(**{path: outside})[u"Q"][cid][u"判定"], (path, outside))

    def test_c_2b_a_missing_value_is_a_miss_not_a_hit(self):
        for cid, path in (("Q-6", QCOL["Q-6"] + SEP + u"通した率(P30E)"), ("Q-6", QCOL["Q-6"] + SEP + u"旧で付かなかった行の通した率"), ("Q-7", QCOL["Q-7"] + SEP + u"割合"),
                          ("Q-7", QCOL["Q-7"] + SEP + u"手がかり真の行の通した率"), ("Q-10", QCOL["Q-10"] + SEP + u"割合")):
            self.assertEqual(MISS, self.J(**{path: None})[u"Q"][cid][u"判定"], path)             # 分母が 0 で率が出ない = 外れ(当たりにしない)
        c = sample_cols()
        del c[QCOL["Q-3"]][u"P29E で対応が付く行"]
        self.assertRaises(KeyError, PI.judge_from, sample_q1(), c, self.seal)                    # 欄が欠けた記録は判定を作れない = 赤(当たりにしない)

    def test_c_2c_q1_needs_the_three_agreements(self):
        for ov in ({INFO_Q1[0]: False}, {INFO_Q1[1]: False}, {INFO_Q1[2]: 1}, {INFO_Q1[2]: None}):
            J = self.J(q1=sample_q1(**ov))
            self.assertEqual(MISS, J[u"Q"]["Q-1"][u"判定"], ov)
            self.assertEqual(MISS, J[u"K"]["K-1"][u"判定"], ov)
            self.assertFalse(J[u"採用"])

    def test_c_3_the_adoption_follows_k1_to_k4(self):
        self.assertFalse(self.J(q1=sample_q1(**{INFO_Q1[0]: False}))[u"採用"])                                                                # K-1
        for k, path in (("round-trip", QCOL["Q-9"] + SEP + u"round-trip 不一致"), ("読み直し", QCOL["Q-9"] + SEP + u"読み直し不一致")):         # K-2
            J = self.J(**{path: 1})
            self.assertEqual(MISS, J[u"K"]["K-2"][u"判定"], k)
            self.assertFalse(J[u"採用"])
        mapped = QCOL["Q-3"] + SEP + u"P30E で対応が付く行"                                                                                    # K-3
        self.assertEqual(HIT, self.J(**{mapped: 130})[u"K"]["K-3"][u"判定"])
        J = self.J(**{mapped: 129})
        self.assertEqual(MISS, J[u"K"]["K-3"][u"判定"])
        self.assertFalse(J[u"採用"])
        for k in (u"P29E・P30E の結果と state が T9 の記録と同じ行", u"旧の対応付けが付いた行(P30E)"):                                           # K-4
            J = self.J(**{QCOL["Q-5"] + SEP + k: 12})
            self.assertEqual(MISS, J[u"K"]["K-4"][u"判定"], k)
            self.assertFalse(J[u"採用"])

    def test_c_4_k3_uses_the_p30e_mapped_rows_and_k_ignores_the_prediction_misses(self):
        J = self.J(**{QCOL["Q-6"] + SEP + u"通した率(P30E)": 99.0, QCOL["Q-7"] + SEP + u"割合": 10.0, QCOL["Q-2"] + SEP + u"行の数": 100})
        self.assertEqual(MISS, J[u"Q"]["Q-6"][u"判定"])
        self.assertEqual(MISS, J[u"Q"]["Q-2"][u"判定"])
        self.assertTrue(J[u"採用"])                                                      # 採用は K だけで決まる(率が高くても採用は採用)
        J = self.J(**{QCOL["Q-3"] + SEP + u"P29E で対応が付く行": 0})
        self.assertEqual(MISS, J[u"Q"]["Q-3"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-3"][u"判定"])                                   # K-3 は P30E で対応が付く行だけを見る
        self.assertTrue(J[u"採用"])

    def test_c_5_the_judgment_moves_with_the_records(self):
        base = self.J()
        mutated_seal = self.seal.replace("0〜6", "0〜1", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertEqual(MISS, PI.judge_from(sample_q1(), sample_cols(), mutated_seal)[u"Q"]["Q-8"][u"判定"])
        self.assertNotEqual(norm(base), norm(self.J(**{QCOL["Q-8"] + SEP + u"違う行": 7})))

    def test_c_6_a_broken_record_is_red_not_an_exception(self):
        R = norm(sample_records())
        self.assertEqual([], judge_problems(R, self.seal))
        del R["inject"][u"行"][0][F_OLD % "P30E"]
        self.assertNotEqual([], judge_problems(R, self.seal))
        R2 = norm(sample_records())
        R2["h"].pop(u"lib の指紋")
        self.assertEqual(MISS, PI.build_Q(R2, self.seal, [])[u"Q"]["Q-1"][u"判定"])
        R3 = norm(sample_records())
        R3["rb"].pop(u"engine の指紋")
        self.assertEqual(MISS, PI.build_Q(R3, self.seal, [])[u"Q"]["Q-1"][u"判定"])
        R4 = norm(sample_records())
        del R4["t9"]
        self.assertNotEqual([], judge_problems(R4, self.seal))

    def test_c_7_the_judgment_follows_the_columns_counted_from_the_rows_not_the_recorded_columns(self):
        R = norm(sample_records())
        J = PI.build_Q(R, self.seal, [])
        R["inject"][Q_KEY][QCOL["Q-9"]][u"round-trip 不一致"] = 7                           # 記録の Q の欄だけ変えても判定は動かない(行から数え直す)
        self.assertEqual(norm(J), norm(PI.build_Q(R, self.seal, [])))
        R["inject"][u"行"][0][u"round-trip"] = False                                      # 行を変えると Q-9 が動く
        self.assertEqual(MISS, PI.build_Q(R, self.seal, [])[u"Q"]["Q-9"][u"判定"])
        self.assertEqual(MISS, PI.build_Q(R, self.seal, [])[u"K"]["K-2"][u"判定"])

    def test_c_8_the_q1_inputs_come_from_the_records_and_the_numstat(self):
        R = norm(sample_records())
        ok = PI.q1_value(R["inject"], R["h"], R["rb"], [])
        self.assertEqual((True, True, 0), tuple(ok.values()))
        R2 = copy.deepcopy(R)
        R2["inject"][u"lib の指紋"][LIB_RELS[0]] = "0" * 64
        self.assertFalse(PI.q1_value(R2["inject"], R2["h"], R2["rb"], [])[INFO_Q1[0]])
        R3 = copy.deepcopy(R)
        R3["inject"][u"engine の指紋"]["core_py_sha256"] = "0" * 64
        self.assertFalse(PI.q1_value(R3["inject"], R3["h"], R3["rb"], [])[INFO_Q1[1]])
        R4 = copy.deepcopy(R)
        R4["inject"][u"engine の指紋"]["git_commit"] = "9" * 40                                # git_commit は比べない(記録ごとに違う)
        self.assertTrue(PI.q1_value(R4["inject"], R4["h"], R4["rb"], [])[INFO_Q1[1]])
        self.assertEqual(1, PI.q1_value(R["inject"], R["h"], R["rb"], ["1\t0\tmeasure/inject.py"])[INFO_Q1[2]])
        self.assertEqual(1, PI.q1_value(R["inject"], R["h"], R["rb"], ["1\t0\tmeasure/xbrl_pswap_2026-11-06.py"])[INFO_Q1[2]])         # T9 の script の 1 行も数える
        self.assertIsNone(PI.q1_value(R["inject"], R["h"], R["rb"], None)[INFO_Q1[2]])
        R5 = copy.deepcopy(R)
        R5["inject"].pop(u"lib の指紋")
        self.assertFalse(PI.q1_value(R5["inject"], R5["h"], R5["rb"], [])[INFO_Q1[0]])
        seal = read(SEAL_REL)
        self.assertEqual(MISS, PI.build_Q(R, seal, None)[u"Q"]["Q-1"][u"判定"])                    # git が読めなかったら外れ(作業木の答えで代えない)
        self.assertEqual(HIT, PI.build_Q(R, seal, [])[u"Q"]["Q-1"][u"判定"])
        calls = []
        with Patch() as pt:
            pt.set(PI, "git_numstat_since_seal", lambda root=ROOT: calls.append(1) or ["1\t0\tmeasure/inject.py"])
            self.assertEqual(MISS, PI.build_Q(R, seal)[u"Q"]["Q-1"][u"判定"])                       # 省略したら git に聞く
        self.assertEqual([1], calls)

    def test_c_9_the_numstat_since_the_seal_is_empty_in_the_real_tree_and_not_in_a_changed_one(self):
        # 2026-11-06(T5Y): 封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §2-1 が宣言した遷移(仕掛けの 2 file に挿入だけ)は実物の木の numstat から外す(SGR.t5y_declared_numstat)
        self.assertEqual([], [x for x in PI.git_numstat_since_seal(ROOT) if not SG.SGR.t5y_declared_numstat(x)])
        self.assertEqual(list(PI.UNTOUCHED_FOR_Q1), ["measure/inject.py", "measure/lib/sites.py", "measure/xbrl_pswap_2026-11-06.py"])
        r = PR.Repo()
        r.put("measure/inject.py")
        r.put("measure/lib/sites.py")
        r.put("measure/xbrl_pswap_2026-11-06.py")
        r.put("x.md")
        sh = r.commit("measure/inject.py", "measure/lib/sites.py", "measure/xbrl_pswap_2026-11-06.py", "x.md")
        base = os.path.join(r.d, "audit-core")
        old = PI.SEAL_COMMIT
        try:
            PI.SEAL_COMMIT = sh[:7]
            self.assertEqual([], PI.git_numstat_since_seal(base))
            for rel in ("measure/lib/sites.py", "measure/xbrl_pswap_2026-11-06.py", "measure/inject.py"):
                with open(os.path.join(base, rel), "a", encoding="utf-8") as fh:
                    fh.write("x = 1\n")
                self.assertGreaterEqual(len(PI.git_numstat_since_seal(base)), 1, rel)
            self.assertEqual(3, len(PI.git_numstat_since_seal(base)))
            PI.SEAL_COMMIT = "0000000"
            self.assertIsNone(PI.git_numstat_since_seal(base))                             # 読めなければ None(当たりにしない)
        finally:
            PI.SEAL_COMMIT = old

    def small_seal(self):
        u"""標本(8 行・旧で付いた 2 行)の大きさに幅を縮めた封(Q-2 は 8 行、Q-5・K-4 は 2 / 2)。他は封のまま。"""
        s = self.seal.replace(u"141・同じ", u"8・同じ", 1).replace(u" | 13 / 13 | ", u" | 2 / 2 | ", 1).replace(u"Q-5 が 13 / 13", u"Q-5 が 2 / 2", 1)
        self.assertEqual(3, sum(1 for a, b in zip(s.split(u"\n"), self.seal.split(u"\n")) if a != b))
        return s

    def test_c_10_a_damaged_t9_record_turns_q2_q5_and_k4_red(self):
        u"""T9 の記録を壊した写し(id を 1 つ変える・旧で付いた行の state か結果を 1 つ変える)。"""
        seal = self.small_seal()
        R = norm(sample_records())
        J0 = PI.build_Q(R, seal, [])
        self.assertEqual((HIT, HIT, HIT), (J0[u"Q"]["Q-2"][u"判定"], J0[u"Q"]["Q-5"][u"判定"], J0[u"K"]["K-4"][u"判定"]))
        t9 = R["t9"][u"行"]
        old_ids = [r[u"id"] for r in R["inject"][u"行"] if r[F_OLD % "P30E"][OLD_KEYS[0]]]
        self.assertEqual(2, len(old_ids))
        idx = [i for i, r in enumerate(t9) if r[u"id"] in old_ids][0]
        # id を 1 つ変える: id の集合が違う(Q-2 外れ)。旧で付いた行の id を変えれば Q-5・K-4 も外れる
        R1 = copy.deepcopy(R)
        R1["t9"][u"行"][2][u"id"] = u"X-T9-99"                                            # 旧で付いていない行の id
        J1 = PI.build_Q(R1, seal, [])
        self.assertEqual((MISS, HIT, HIT), (J1[u"Q"]["Q-2"][u"判定"], J1[u"Q"]["Q-5"][u"判定"], J1[u"K"]["K-4"][u"判定"]))
        R2 = copy.deepcopy(R)
        R2["t9"][u"行"][idx][u"id"] = u"X-T9-98"
        J2 = PI.build_Q(R2, seal, [])
        self.assertEqual((MISS, MISS, MISS, False), (J2[u"Q"]["Q-2"][u"判定"], J2[u"Q"]["Q-5"][u"判定"], J2[u"K"]["K-4"][u"判定"], J2[u"採用"]))
        # state / 結果を 1 つ変える: Q-5・K-4 が外れる(Q-2 は id の集合なので当たりのまま)
        for profile in INJECT_PROFILES:
            for field, val in ((u"state", V_ if t9[idx][profile][u"state"] != V_ else U_), (u"結果", TUNE.LABEL_PNF)):
                R3 = copy.deepcopy(R)
                R3["t9"][u"行"][idx][profile][field] = val
                J3 = PI.build_Q(R3, seal, [])
                self.assertEqual((HIT, MISS, MISS, False), (J3[u"Q"]["Q-2"][u"判定"], J3[u"Q"]["Q-5"][u"判定"], J3[u"K"]["K-4"][u"判定"], J3[u"採用"]), (profile, field))
                self.assertNotEqual([], record_problems(R3, full=False), (profile, field))                # 記録の Q の欄(正しい T9 で作った)と食い違う
        # 旧で付いていない行の T9 の判定を変えても Q-5 は動かない(Q-5 は旧で付いた行だけ)
        R4 = copy.deepcopy(R)
        R4["t9"][u"行"][2][u"P30E"][u"state"] = V_
        self.assertEqual(HIT, PI.build_Q(R4, seal, [])[u"Q"]["Q-5"][u"判定"])
        self.assertEqual([], record_problems(copy.deepcopy(R), full=False))
        self.assertNotEqual([], record_problems(R2, full=False))
        R5 = copy.deepcopy(R)
        R5["t9"][u"行"] = R5["t9"][u"行"][:-1]                                               # T9 の行が 1 つ少ない
        self.assertEqual(MISS, PI.build_Q(R5, seal, [])[u"Q"]["Q-2"][u"判定"])
        self.assertNotEqual([], record_problems(R5, full=False))
        # 封の幅のままなら、標本は Q-2・Q-5 を外す(標本は 8 行)
        self.assertEqual((MISS, MISS), (PI.build_Q(R, self.seal, [])[u"Q"]["Q-2"][u"判定"], PI.build_Q(R, self.seal, [])[u"Q"]["Q-5"][u"判定"]))


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

    def test_g_1_the_sample_exercises_a_skipped_book_unlinked_rows_unmapped_rows_and_every_missing_condition(self):
        inj = self.R["inject"]
        self.assertIn(u"注入しない", inj[u"本ごとの数え"][u"DOC2_F5_m2"])
        self.assertEqual({u"全体": 1, T9: 1}, dict(inj[u"P29E に対応なしの行の数"]))
        cols = inj[Q_KEY]
        self.assertEqual({COND_A, COND_I, COND_U}, set(k for r in inj[u"行"] for k in r[F_MISS % "P30E"]))
        self.assertEqual(1, cols[QCOL["Q-9"]][u"先頭の位が減った行"])
        self.assertEqual(6, cols[QCOL["Q-3"]][u"P30E で対応が付く行"])                              # 8 行のうち P30E に対応が付かない 2 行を除く
        self.assertEqual(2, cols[QCOL["Q-4"]][u"旧の対応付けが付く行(P30E)"])
        self.assertEqual((2, 4), (cols[QCOL["Q-8"]][u"違う行"], cols[QCOL["Q-8"]][u"両方に対応が付く行"]))
        self.assertEqual((6, 5), (cols[QCOL["Q-3"]][u"P30E で対応が付く行"], cols[QCOL["Q-3"]][u"P29E で対応が付く行"]))      # P30E と P29E で対応が付く行の数が違う標本

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
        self._red(inj(lambda r: r[u"行"][4].__setitem__(u"届いた", True)))                                    # (ウ)が偽の行は届かない
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"engine の手がかり", u"はい")))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"文に前期の語", 1)))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(u"基準の pointer の期", u"前期")))                    # 4 つの語でない
        self._red(inj(lambda r: r[u"行"][1].__setitem__(u"注入後の pointer の期", u"当期")))
        self._red(inj(lambda r: r[u"行"][5].__setitem__(u"注入後の pointer の期", u"CurrentYear")))          # id の claim が無い行は なし
        self._red(inj(lambda r: r[u"行"][0].__setitem__("id", r[u"行"][1]["id"])))
        self._red(inj(lambda r: r[u"集計"][T9]["P30E"][u"全体"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r[PI.BREAKDOWN_KEY][u"複合"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r[PI.CUE_KEY][u"真"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r[PI.PERIOD_KEY].__setitem__(u"CurrentYear", 9)))
        self._red(inj(lambda r: r[u"型"].__setitem__(u"土台", u"無改変の文で P29E が GROUNDED の claim")))
        self._red(inj(lambda r: r[u"型"].__setitem__(u"site", u"全部の site")))
        self._red(inj(lambda r: r[u"型"].__setitem__(u"対応付け", u"値で引く")))
        self._red(inj(lambda r: r[u"限界"].pop()))
        self._red(inj(lambda r: r[u"限界"].__setitem__(0, u"別の限界")))
        self._red(inj(lambda r: r.pop(PI.COMPARE_KEY)))
        self._red(inj(lambda r: r[PI.COMPARE_KEY][T9]["P29E"][u"全体"].__setitem__(u"注入の行", 9)))
        self._red(inj(lambda r: r.pop(PI.BREAKDOWN_KEY)))
        self._red(inj(lambda r: r.pop(PI.CUE_KEY)))
        self._red(inj(lambda r: r.pop(PI.PERIOD_KEY)))

    def test_g_2a_the_condition_columns_and_the_old_mapping_columns_turn_the_record_red_when_broken(self):
        u"""対応の条件・欠けた条件・旧の対応・claim の数の欄を 1 つずつ壊す(行の欄の間の関係で赤になる)。"""
        inj = lambda f: (lambda R: f(R["inject"]))
        c30, m30, o30 = F_COND % "P30E", F_MISS % "P30E", F_OLD % "P30E"
        self._red(inj(lambda r: r[u"行"][0][c30].__setitem__(COND_I, False)))                               # 条件が偽なのに P30E に対応が付いた
        self._red(inj(lambda r: r[u"行"][0][c30].__setitem__(COND_U, False)))
        self._red(inj(lambda r: r[u"行"][0][c30].__setitem__(COND_A, False)))                               # (ア)が偽で(イ)(ウ)が真
        self._red(inj(lambda r: r[u"行"][4][c30].__setitem__(COND_U, True)))                                # 全部真なのに対応が付かない
        self._red(inj(lambda r: r[u"行"][4].__setitem__(m30, [])))                                          # 欠けた条件が条件の真偽と合わない
        self._red(inj(lambda r: r[u"行"][4].__setitem__(m30, [COND_I])))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(m30, [COND_A])))
        self._red(inj(lambda r: r[u"行"][0].pop(c30)))
        self._red(inj(lambda r: r[u"行"][0].pop(m30)))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(c30, {COND_A: True, COND_I: True})))                # 条件が 2 つ
        self._red(inj(lambda r: r[u"行"][3].__setitem__(F_COND % "P29E", r[u"行"][0][F_COND % "P29E"])))    # 土台に対応が付かない P29E に条件を置いた
        self._red(inj(lambda r: r[u"行"][3].__setitem__(F_MISS % "P29E", [])))                              # 土台なし の印が無い
        self._red(inj(lambda r: r[u"行"][0].__setitem__(F_COND % "P29E", None)))                            # 土台に対応が付く行の条件が なし
        self._red(inj(lambda r: r[u"行"][0][o30].__setitem__(OLD_KEYS[0], u"はい")))
        self._red(inj(lambda r: r[u"行"][1][o30].__setitem__(OLD_KEYS[1], True)))                           # 旧の対応が付かないのに同じ id
        self._red(inj(lambda r: r[u"行"][0].pop(o30)))
        self._red(inj(lambda r: r[u"行"][0].pop(F_OLD % "P29E")))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(o30, {OLD_KEYS[0]: True})))
        self._red(inj(lambda r: r[u"行"][0].__setitem__(F_SAMEN, u"はい")))
        self._red(inj(lambda r: r[u"行"][0].pop(F_SAMEN)))
        # 欠けた条件の欄を持つ行が変わると、Q の欄と本ごとの数えも合わなくなる
        self._red(inj(lambda r: r[Q_KEY][u"参考"].__setitem__(u"P30E の欠けた条件(ウ)", 9)))

    def test_g_2b_every_column_of_the_q_record_is_recounted_from_the_rows_and_the_t9_record(self):
        u"""Q の欄の全部(Q-2〜Q-10 と参考の欄)を 0 に固定すると赤。記録の欄を直しても行・T9 の記録と食い違えば赤。"""
        cols = self.R["inject"][Q_KEY]

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
            d = R["inject"][Q_KEY]
            for k in path[:-1]:
                d = d[k]
            d[path[-1]] = 0 if (v != 0 and v is not True) else (False if v is True else 1)             # 0 に固定(元が 0 なら 1。真偽は反対に)
            self.assertNotEqual([], record_problems(R, full=False), path)
            n += 1
        self.assertGreaterEqual(n, 39)
        R = copy.deepcopy(self.R)
        R["inject"].pop(Q_KEY)
        self.assertNotEqual([], record_problems(R, full=False))

    def test_g_2c_the_script_columns_function_changed_in_one_column_turns_the_record_red(self):
        u"""script の ``q_columns`` が欄を 1 つ変える変異(0 に固定・0 なら 1)。記録は正しい欄で作ってある。"""
        real = PI.q_columns
        paths = []
        for k, v in real(self.R["inject"][u"行"], self.R["t9"][u"行"]).items():
            for kk in v:
                paths.append((k, kk))
        self.assertGreaterEqual(len(paths), 39)
        for path in paths:
            def fixed(rows, t9_rows, path=path):
                c = real(rows, t9_rows)
                v = c[path[0]][path[1]]
                c[path[0]][path[1]] = 0 if (v != 0 and v is not True) else (False if v is True else 1)
                return c
            with Patch() as pt:
                pt.set(PI, "q_columns", fixed)
                self.assertNotEqual([], record_problems(copy.deepcopy(self.R), full=False), path)
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=False))

    def test_g_2d_a_row_field_changes_exactly_the_columns_it_feeds(self):
        rows, t9 = self.R["inject"][u"行"], self.R["t9"][u"行"]
        base = norm(PI.q_columns(rows, t9))
        k2, k3, k4, k5, k6, k7, k8, k9, k10, ref = (QCOL["Q-2"], QCOL["Q-3"], QCOL["Q-4"], QCOL["Q-5"], QCOL["Q-6"], QCOL["Q-7"], QCOL["Q-8"], QCOL["Q-9"], QCOL["Q-10"], u"参考")
        self.assertEqual(
            {k2: {u"行の数": 8, u"T9 の記録の行の数": 8, u"id の集合が T9 の記録と同じ": True, u"T9 の記録にだけ在る id": 0, u"この記録にだけ在る id": 0},
             k3: {u"P30E で対応が付く行": 6, u"P29E で対応が付く行": 5, u"注入の前後で claim の数が同じ行": 7},
             k4: {u"旧の対応付けが付く行(P30E)": 2, u"うち id で引いた claim と同じ claim の行": 2},
             k5: {u"旧の対応付けが付いた行(P30E)": 2, u"P29E・P30E の結果と state が T9 の記録と同じ行": 2},
             k6: {u"通した率(P30E)": 50.0, u"通した行": 3, u"id で対応が付く行": 6, u"旧で付かなかった行の通した率": 50.0, u"旧で付かなかった行の通した行": 3, u"旧で付かなかった行": 6},
             k7: {u"通した行": 3, u"うち注入後の pointer の期が CurrentYear": 3, u"割合": 100.0, u"手がかり真の行の通した率": 40.0, u"対応が付く行のうち手がかり真": 5},
             k8: {u"違う行": 2, u"両方に対応が付く行": 4},
             k9: {u"round-trip 不一致": 0, u"読み直し不一致": 0, u"先頭の位が減った行": 1, u"届いた行": 6},
             k10: {u"対応が付く行": 6, u"止めた行": 3, u"うち名指して原本": 2, u"割合": 66.7},
             ref: {u"文に前期の語がある行": 7, u"手がかり真の行(全部)": 7, u"P30E の欠けた条件(ア)": 1, u"P30E の欠けた条件(イ)": 1, u"P30E の欠けた条件(ウ)": 2, u"P29E の欠けた条件がある行": 3}}, base)

        def edit(idx, fn):
            r2 = copy.deepcopy(rows)
            fn(r2[idx])
            return norm(PI.q_columns(r2, t9))
        cases = (
            (0, lambda r: r.__setitem__(u"round-trip", False), (k9, u"round-trip 不一致"), [k9]),
            (0, lambda r: r.__setitem__(u"読み直し", False), (k9, u"読み直し不一致"), [k9]),
            (0, lambda r: r.__setitem__(u"先頭の位が減った", True), (k9, u"先頭の位が減った行"), [k9]),
            (1, lambda r: r.__setitem__(u"届いた", False), (k9, u"届いた行"), [k9]),
            (0, lambda r: r.__setitem__(u"engine の手がかり", False), (k7, u"対応が付く行のうち手がかり真"), [k7, ref]),
            (2, lambda r: r.__setitem__(u"engine の手がかり", True), (k7, u"対応が付く行のうち手がかり真"), [k7, ref]),
            (0, lambda r: r.__setitem__(u"文に前期の語", False), (ref, u"文に前期の語がある行"), [ref]),
            (1, lambda r: r.__setitem__(u"注入後の pointer の期", u"Prior1Year"), (k7, u"うち注入後の pointer の期が CurrentYear"), [k7]),
            (0, lambda r: r.__setitem__(u"基準の pointer の期", u"他"), None, []),                                    # 基準の pointer の期は Q の欄の餌ではない(行の整合で見る)
            (0, lambda r: r[F_OLD % "P30E"].__setitem__(OLD_KEYS[1], False), (k4, u"うち id で引いた claim と同じ claim の行"), [k4]),
            (1, lambda r: r[F_OLD % "P30E"].__setitem__(OLD_KEYS[0], True), (k4, u"旧の対応付けが付く行(P30E)"), [k4, k5, k6]),
            (0, lambda r: r.__setitem__(F_SAMEN, False), (k3, u"注入の前後で claim の数が同じ行"), [k3]),
            (4, lambda r: r.__setitem__(F_SAMEN, False), (k3, u"注入の前後で claim の数が同じ行"), [k3]),
            (4, lambda r: r.__setitem__(F_MISS % "P30E", [COND_I]), (ref, u"P30E の欠けた条件(イ)"), [ref]),
            (0, lambda r: r.__setitem__(F_MISS % "P29E", [COND_U]), (ref, u"P29E の欠けた条件がある行"), [ref]))
        for idx, fn, where, feeds in cases:
            c2 = edit(idx, fn)
            if where is not None:
                self.assertNotEqual(base[where[0]][where[1]], c2[where[0]][where[1]], where)
            changed = [k for k in base if base[k] != c2[k]]
            self.assertEqual(feeds, changed, (where, changed))                                                       # 動くのはその欄が餌にする欄だけ
        c2 = edit(1, lambda r: r.__setitem__("P30E", cell(*NAMED)))                                                   # 通した行が名指しに: Q-6・Q-7・Q-8・Q-10 が動く
        self.assertEqual(2, c2[k7][u"通した行"])
        self.assertEqual(4, c2[k10][u"止めた行"])
        self.assertEqual([k6, k7, k8, k10], [k for k in base if base[k] != c2[k]])                                   # Q-5 は旧で付いた行だけなので動かない

    def test_g_2e_a_consistently_edited_count_still_breaks_the_invariants(self):
        u"""本ごとの数えを直してから Q の欄も作り直しても(欄との食い違いでは見つからない)、数えの欄の間の関係と行との関係で赤になる。"""
        def reh(R):
            R["inject"][Q_KEY] = norm(PI.q_columns(R["inject"][u"行"], R["t9"][u"行"]))
        for mutate in (lambda c: c.__setitem__(u"採った", 3), lambda c: c.__setitem__(u"土台 P30E が GROUNDED の site", 9), lambda c: c.__setitem__(u"cap を基準で絞る前に掛けた数", 9),
                       lambda c: c[u"作れる site"].__setitem__(u"複合", 9), lambda c: c[u"作れる site"].__setitem__(u"既存", 0), lambda c: c[u"作れる site の手がかり"].__setitem__(u"真", 9),
                       lambda c: c[u"作れる site の手がかり"].__setitem__(u"真", 0), lambda c: c[u"作れる site の状態"].__setitem__(PI.LINKED, 9),
                       lambda c: c[u"採った の状態"].__setitem__(PI.LINKED, 9), lambda c: c[u"採った の状態"].__setitem__(PS.STATUS_NOT_G, 1),
                       lambda c: c[u"段"].__setitem__(u"site", 9), lambda c: c[u"段"].__setitem__(u"単位が同じ・両方正・値が違う", 1), lambda c: c[u"段"].__setitem__(u"参照先が Prior1Year", 0),
                       lambda c: c[u"段"].pop(u"site")):
            R = copy.deepcopy(self.R)
            mutate(R["inject"][u"本ごとの数え"][u"DOC1_F1_m1"])
            try:
                reh(R)
            except Exception:                                   # noqa: BLE001  Q の欄を作れない形も赤(record_problems が例外を問題に数える)
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
            R["inject"][u"集計"], R["inject"][PI.COMPARE_KEY] = (norm(x) for x in PI.inject_summaries(R["inject"][u"行"]))
        R["inject"][u"P29E に対応なしの行の数"] = collections.OrderedDict([(u"全体", 0), (T9, 0)])
        self.assertTrue(any(u"上限" in x for x in inject_problems(R["inject"], R["t9"][u"行"], full=False)), inject_problems(R["inject"], R["t9"][u"行"], full=False))
        R2 = copy.deepcopy(self.R)
        R2["inject"][u"行"][0][LINK_KEY] = False                               # 対応ありの行を対応なしに(P29E の欄が対応なしでない)
        self.assertNotEqual([], record_problems(R2, full=False))

    def test_g_2g_the_full_only_checks_are_exercised_on_the_sample(self):
        u"""full=True だけが見る検査(本番の記録でだけ走る)を、標本の記録で。標本は 200 本でなく範囲も標本。"""
        R = copy.deepcopy(self.R)
        self.assertTrue(any(u"200 本" in x for x in inject_problems(R["inject"], R["t9"][u"行"], full=True)))
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
        for name in (u"この script の sha256", u"T9 の script の sha256", u"T9 の記録の sha256", u"J の script の sha256", u"nscan script の sha256", u"rmix script の sha256",
                     u"numfix script の sha256", u"前の便の run script の sha256", u"生成の script の sha256", u"J の記録の sha256", u"H の記録の sha256", u"RB の記録の sha256"):
            self.assertIn(name, self.R["inject"])
            self._red(lambda R, name=name: R["inject"].__setitem__(name, "e" * 64))
            self._red(lambda R, name=name: R["inject"].pop(name))
        fp = lambda R: R["inject"][u"engine の指紋"]
        self._red(lambda R: fp(R).__setitem__("adapter_xbrl_py_sha256", fp(R)["adapter_xbrl_py_sha256"][:-1] + ("0" if fp(R)["adapter_xbrl_py_sha256"][-1] != "0" else "1")))
        self._red(lambda R: fp(R).__setitem__("core_py_sha256", "f" * 64))
        self._red(lambda R: R["inject"].__setitem__(u"封の commit", u"0000000"))
        self._red(lambda R: R["inject"].__setitem__(u"seal", u"docs/XBRL_PERIOD_SWAP_SEAL_2026-11-06.md"))
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
        i = lines.index(u"<!-- 門:start pred -->") + 3                  # 表の 1 行目(Q-1)
        for col_char in (u"Q", u"一", u"当"):
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
        R3 = copy.deepcopy(self.R)
        R3["t9"][u"行"][0][u"id"] = u"X-T9-97"                              # T9 の記録を壊すと Q-2 の行が変わる
        self.assertNotEqual([], doc_problems(doc, R3, self.seal))
        mutated_seal = self.seal.replace("0〜6", "0〜5", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertNotEqual([], doc_problems(doc, self.R, mutated_seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"門:start judge", u"門:start other"), self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"<!-- 門:start judge -->", u"<!-- 門:start judge2 -->", 1), self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc, self.R, self.seal, numstat=["1\t0\tmeasure/inject.py"]))      # Q-1 の行が変わる

    def test_g_7_forbidden_words_docids_and_ungated_numbers_turn_the_document_red(self):
        doc = sample_doc(self.R, self.seal)
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(doc + u"\n" + w + u"。\n", self.R, self.seal), w)
        self.assertNotEqual([], doc_problems(doc + u"\nS100" + u"ABCD の文。\n", self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n新しい token は 1234 でした。\n", self.R, self.seal))
        self.assertEqual([], doc_problems(doc + u"\n新しい token は 1234 でした。" + NOT_GATED + u"\n", self.R, self.seal))

    def test_g_8_the_judge_table_ends_with_the_adoption_line(self):
        J = PI.build_Q(self.R, self.seal, [])
        t = PI.render_judge(J, self.seal).split(u"\n")
        self.assertEqual(u"採用の判定(K-1〜K-4 を全部満たす): **%s**。最後に決めるのは人間。" % (u"採用" if J[u"採用"] else u"見送り"), t[-1])
        J2 = PI.build_Q(self.R, self.seal, ["1\t0\tmeasure/inject.py"])
        self.assertFalse(J2[u"採用"])
        self.assertIn(u"**見送り**", PI.render_judge(J2, self.seal))
        self.assertEqual(u"| # | 欄 | 予測 | 測った値 | 判定 |", PI.render_pred(J, self.seal).split(u"\n")[0])
        self.assertEqual(10 + 2, len(PI.render_pred(J, self.seal).split(u"\n")))
        self.assertEqual(4 + 2 + 2, len(t))


WRONG_FLAG = "compound_yen_2026_11_05"


# ================================================================ (w) 手順・対応付け・行の欄(script の関数を小さい入力で通す。zip・判定は偽。lib は本物。通信なし)
def run_pi(text=TEXT_P, refs=REFS_P, patches=(), seed=u"sd", key=u"bk", verify=None):
    with Patch() as pt, PI.yen_scan_on():
        pt.set(RUN, "PROFILES", INJECT_PROFILES)
        for mod, name, v in patches:
            pt.set(mod, name, v)
        return PI.inject_text_pi(b"zip", text, refs, seed, key, verify=verify or make_verify(text))


def verify_edit(text0, edit, only_profile=None, **kw):
    u"""``make_verify`` の claim の列を、注入後の文(text0 と違う文)でだけ ``edit(claims)`` で書き換える(only_profile = その profile だけ)。"""
    base = make_verify(text0, **kw)

    def v(zb, p, t):
        out = base(zb, p, t)
        if t != text0 and (only_profile is None or p == only_profile):
            edit(out["claims"])
        return out
    return v


def injected(claims):
    u"""注入後の文で増えた claim(span が元の文に無い = make_verify が inj_state にした claim)。"""
    return [c for c in claims if c["state"] == V_]


def edit_drop_id(claims):                                    # (ア)を欠く: 基準の claim の id の claim が無い
    for c in injected(claims):
        c["id"] = u"Z" + c["id"]


def edit_wrong_value(claims):                                # (イ)を欠く: id は同じだが値が別
    for c in injected(claims):
        c["value"] = c["value"] * 2


def edit_cut_span(claims):                                   # (ウ)を欠く: span に差し替えの字が無い
    for c in injected(claims):
        c["span"] = c["span"][:1]


def edit_other_claim_holds_the_value(claims):                # id の claim は値が別で、別の id の claim が注入した値を持つ(旧の対応付けはそちらに付く)
    extra = []
    for c in injected(claims):
        extra.append(dict(c, value=c["value"] * 2, span=u"x", state=G))
        c["id"] = u"Z" + c["id"]
    claims.extend(extra)
    for e in extra:
        e["id"] = e["id"][1:] if e["id"].startswith(u"Z") else e["id"]


def edit_duplicate_value_first(claims):                      # 同じ値・同じ span の claim が別の id でもう 1 件(先頭に置く)
    for c in injected(claims):
        claims.insert(0, dict(c, id=u"D" + c["id"]))


def conds_tuple(r, p):
    c = r[F_COND % p]
    return None if c is None else tuple(c.values())


class MappingTest(unittest.TestCase):
    u"""封 §1-1: 注入後の claim は 基準の claim の id で引き、(ア)(イ)(ウ)を全部満たすときだけ対応が付く。"""

    CL = [{"id": "N001", "value": 5.0, "unit": u"円", "span": u"5円"}, {"id": "N002", "value": 7.0, "unit": u"円", "span": u"今期は7円でした"}]

    def test_m_1_each_condition_removes_the_mapping_alone(self):
        res, conds, miss, found = PI.id_map(self.CL, "N002", 7.0, u"7")
        self.assertIs(res, self.CL[1])
        self.assertIs(found, self.CL[1])
        self.assertEqual(((True, True, True), []), (tuple(conds.values()), miss))
        self.assertEqual(list(CONDS), list(conds))
        for base_id, target, rendered, want_conds, want_miss in (
                ("N009", 7.0, u"7", (False, False, False), list(CONDS)),                # (ア) id の claim が無い
                (None, 7.0, u"7", (False, False, False), list(CONDS)),                  # 基準の claim の id が無い
                ("N002", 8.0, u"7", (True, False, True), [COND_I]),                     # (イ) 値が違う
                ("N002", 7.0, u"9", (True, True, False), [COND_U]),                     # (ウ) span に字が無い
                ("N002", 8.0, u"9", (True, False, False), [COND_I, COND_U])):
            res, conds, miss, found = PI.id_map(self.CL, base_id, target, rendered)
            self.assertIsNone(res, (base_id, target, rendered))
            self.assertEqual((want_conds, want_miss), (tuple(conds.values()), miss), (base_id, target, rendered))
            self.assertIs(found, None if want_conds[0] is False else self.CL[1])

    def test_m_2_the_id_decides_not_the_value(self):
        cl = [{"id": "N001", "value": 7.0, "unit": u"円", "span": u"7円"}, {"id": "N002", "value": 7.0, "unit": u"円", "span": u"7円"}]
        for base_id in ("N001", "N002"):
            res, _c, miss, _f = PI.id_map(cl, base_id, 7.0, u"7")
            self.assertIs(res, cl[int(base_id[-1]) - 1])                                # 同じ値の claim が 2 件在っても id で 1 件に決まる
            self.assertEqual([], miss)
        self.assertIsNone(TUNE.claim_for_p27(cl, {"new_value": 7.0, "replacement": u"7"}, u"円"))     # 旧の対応付けは 1 件に決められない
        cl2 = [{"id": "N001", "value": 7.0, "unit": u"円", "span": u"7円"}, {"id": "N002", "value": 9.0, "unit": u"円", "span": u"今期は7円でした"}]
        res, _c, miss, _f = PI.id_map(cl2, "N002", 7.0, u"7")                           # 値を持つのは別の id の claim: id の claim は(イ)で欠ける
        self.assertIsNone(res)
        self.assertEqual([COND_I], miss)

    def test_m_3_the_value_uses_the_unit_scale_and_the_tolerance(self):
        cl = [{"id": "N001", "value": 12.0, "unit": u"億円", "span": u"12億円"}]
        self.assertEqual([], PI.id_map(cl, "N001", SC.scaled_value(12.0, u"億円"), u"12")[2])
        self.assertEqual([COND_I], PI.id_map(cl, "N001", 12.0, u"12")[2])               # 円に直さない target とは合わない(claim 側だけ直して比べる)
        big = [{"id": "N001", "value": 1.0e9 + 0.5, "unit": u"円", "span": u"x"}]
        self.assertEqual([COND_U], PI.id_map(big, "N001", 1.0e9, u"7")[2])             # 許容 1e-9 倍の内
        big = [{"id": "N001", "value": 1.0e9 + 5.0, "unit": u"円", "span": u"7"}]
        self.assertEqual([COND_I], PI.id_map(big, "N001", 1.0e9, u"7")[2])             # 許容の外
        self.assertEqual([COND_I], PI.id_map([{"id": "N001", "value": None, "unit": u"円", "span": u"7"}], "N001", 7.0, u"7")[2])     # value が無い
        self.assertEqual([COND_U], PI.id_map([{"id": "N001", "value": 7.0, "unit": u"円"}], "N001", 7.0, u"7")[2])                   # span が無い
        self.assertEqual([COND_U], PI.id_map([{"id": "N001", "value": 7.0, "unit": u"円", "span": None}], "N001", 7.0, u"7")[2])

    def test_m_4_the_old_mapping_is_the_claim_for_p27_result_and_the_same_id_is_a_second_fact(self):
        inj = {"new_value": 7.0, "replacement": u"7"}
        cl = [{"id": "N001", "value": 5.0, "unit": u"円", "span": u"5円"}, {"id": "N002", "value": 7.0, "unit": u"円", "span": u"7円"}]
        self.assertEqual({OLD_KEYS[0]: True, OLD_KEYS[1]: True}, dict(PI.old_map(cl, inj, u"円", "N002")))
        self.assertEqual({OLD_KEYS[0]: True, OLD_KEYS[1]: False}, dict(PI.old_map(cl, inj, u"円", "N001")))        # 付いたが別の claim
        self.assertEqual({OLD_KEYS[0]: True, OLD_KEYS[1]: False}, dict(PI.old_map(cl, inj, u"円", None)))
        self.assertEqual({OLD_KEYS[0]: False, OLD_KEYS[1]: False}, dict(PI.old_map(cl, dict(inj, new_value=9.0), u"円", "N002")))      # 付かない
        two = cl + [{"id": "N003", "value": 7.0, "unit": u"円", "span": u"7円"}]
        self.assertEqual({OLD_KEYS[0]: False, OLD_KEYS[1]: False}, dict(PI.old_map(two, inj, u"円", "N002")))    # 同じ値が 2 件なら付かない

    def test_m_5_the_aliases_are_the_t9_functions_and_the_helpers_are_not_t9_names(self):
        for name in ("inject_summaries", "unlinked_counts", "breakdown", "cue_breakdown", "period_breakdown", "pass_rate", "load_books", "caches_all"):
            self.assertIs(getattr(PI, name), getattr(PS, name), name)


class ProcedureTest(unittest.TestCase):
    def test_w_1_rows_carry_the_t9_columns_with_the_same_values_and_the_new_columns(self):
        rows, c = run_pi()
        t9rows, t9c = PSR.run_ps()
        self.assertEqual(3, len(rows))
        self.assertEqual(norm(t9c), norm(c))                                                            # 本ごとの数えは T9 のまま
        t9keys = list(t9rows[0])
        new_keys = [F_COND % "P29E", F_COND % "P30E", F_MISS % "P29E", F_MISS % "P30E", F_OLD % "P29E", F_OLD % "P30E", F_SAMEN]
        for r, r9 in zip(rows, t9rows):
            self.assertEqual(t9keys + new_keys, list(r))
            self.assertEqual(norm(r9), norm(dict((k, r[k]) for k in t9keys)))                           # T9 の欄は T9 の script の行と同じ値(正直な注入では対応付けを替えても同じ)
            self.assertEqual(((True, True, True), (True, True, True)), (conds_tuple(r, "P29E"), conds_tuple(r, "P30E")))
            self.assertEqual(([], []), (r[F_MISS % "P29E"], r[F_MISS % "P30E"]))
            self.assertEqual(({OLD_KEYS[0]: True, OLD_KEYS[1]: True},) * 2, (dict(r[F_OLD % "P29E"]), dict(r[F_OLD % "P30E"])))
            self.assertIs(True, r[F_SAMEN])
        self.assertEqual([], sorted(set(k for r in rows for k in RUN.walk_keys(r) if k in FORBIDDEN_KEYS)))
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))
        labels = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
        self.assertEqual([], [x for r in rows for x in row_problems(dict(r, docID=u"D", form=u"F", model=u"m", id=u"D_F_m-" + r[u"id"][3:]), labels, set())])

    def test_w_2_each_missing_condition_turns_the_mapping_off_and_names_the_missing_one(self):
        for name, edit, want_conds, want_miss in (
                ("id", edit_drop_id, (False, False, False), list(CONDS)),
                ("value", edit_wrong_value, (True, False, True), [COND_I]),
                ("span", edit_cut_span, (True, True, False), [COND_U])):
            rows, c = run_pi(verify=verify_edit(TEXT_P, edit))
            self.assertEqual(3, len(rows), name)
            for r in rows:
                for p in INJECT_PROFILES:
                    self.assertEqual(want_conds, conds_tuple(r, p), (name, p))
                    self.assertEqual(want_miss, r[F_MISS % p], (name, p))
                    self.assertEqual(UNMAPPED_CELL, norm(r[p]), (name, p))                           # 対応が付かない
                self.assertTrue(r[LINK_KEY], name)                                                   # 土台の対応は付いている
            self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP), name)
            labels = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
            self.assertEqual([], [x for r in rows for x in row_problems(dict(r, docID=u"D", form=u"F", model=u"m", id=u"D_F_m-" + r[u"id"][3:]), labels, set())], name)
        rows, _c = run_pi()
        self.assertTrue(all(r["P30E"][u"対応"] for r in rows))                                          # 欠けなければ対応が付く

    def test_w_3_reach_and_the_post_pointer_period_follow_the_id_claim_not_the_mapping(self):
        rows, _c = run_pi(verify=verify_edit(TEXT_P, edit_drop_id))                                   # id の claim が無い: 届かず、期は なし
        self.assertEqual(([False] * 3, [u"なし"] * 3), ([r[u"届いた"] for r in rows], [r[u"注入後の pointer の期"] for r in rows]))
        rows, _c = run_pi(verify=verify_edit(TEXT_P, edit_cut_span))                                  # (ウ)が欠ける: 届かない。id の claim は在るので期は読める
        self.assertEqual(([False] * 3, [u"Prior1Year"] * 3), ([r[u"届いた"] for r in rows], [r[u"注入後の pointer の期"] for r in rows]))
        rows, _c = run_pi(verify=verify_edit(TEXT_P, edit_wrong_value))                               # (イ)だけ欠ける: 対応は付かないが(ウ)の字は在るので届いた
        self.assertEqual(([True] * 3, [u"Prior1Year"] * 3, [False] * 3), ([r[u"届いた"] for r in rows], [r[u"注入後の pointer の期"] for r in rows], [r["P30E"][u"対応"] for r in rows]))
        rows, _c = run_pi()
        self.assertEqual(([True] * 3, [u"Prior1Year"] * 3), ([r[u"届いた"] for r in rows], [r[u"注入後の pointer の期"] for r in rows]))

    def test_w_4_two_claims_with_the_same_value_still_map_by_id_and_the_old_mapping_does_not(self):
        rows, c = run_pi(verify=verify_edit(TEXT_P, edit_duplicate_value_first))
        self.assertEqual(3, len(rows))
        for r in rows:
            self.assertEqual(((True, True, True), (True, True, True)), (conds_tuple(r, "P29E"), conds_tuple(r, "P30E")))
            self.assertEqual(TUNE.LABEL_NAMED_ORIGINAL, r["P30E"][u"結果"])                            # id で 1 件に決まり、判定が付く
            self.assertEqual({OLD_KEYS[0]: False, OLD_KEYS[1]: False}, dict(r[F_OLD % "P30E"]))     # 旧の対応付けは付かない
            self.assertEqual({OLD_KEYS[0]: False, OLD_KEYS[1]: False}, dict(r[F_OLD % "P29E"]))
            self.assertIs(False, r[F_SAMEN])                                                        # claim の数が増えた
            self.assertTrue(r[u"届いた"])

    def test_w_5_the_old_mapping_can_land_on_another_claim_than_the_id_one(self):
        rows, _c = run_pi(verify=verify_edit(TEXT_P, edit_other_claim_holds_the_value))
        self.assertEqual(3, len(rows))
        for r in rows:
            self.assertEqual(((True, False, False), (True, False, False)), (conds_tuple(r, "P29E"), conds_tuple(r, "P30E")))            # id の claim は別の値・別の span
            self.assertEqual({OLD_KEYS[0]: True, OLD_KEYS[1]: False}, dict(r[F_OLD % "P30E"]))        # 旧は付くが別の claim
            self.assertEqual(TUNE.LABEL_UNMAPPED, r["P30E"][u"結果"])

    def test_w_6_the_old_mapping_does_not_decide_the_row(self):
        rows, _c = run_pi()
        with Patch() as pt:
            pt.set(TUNE, "claim_for_p27", lambda claims, inj, unit: None)                          # 旧の対応付けが常に付かない
            rows2, _c2 = run_pi()
        self.assertEqual(3, len(rows2))
        for r, r2 in zip(rows, rows2):
            self.assertEqual(norm(dict((k, v) for k, v in r.items() if not k.startswith(u"旧の対応"))), norm(dict((k, v) for k, v in r2.items() if not k.startswith(u"旧の対応"))))
            self.assertEqual({OLD_KEYS[0]: False, OLD_KEYS[1]: False}, dict(r2[F_OLD % "P30E"]))
            self.assertEqual({OLD_KEYS[0]: True, OLD_KEYS[1]: True}, dict(r[F_OLD % "P30E"]))

    def test_w_7_the_old_mapping_is_looked_up_with_the_new_value_and_the_unit_once_per_profile(self):
        real = TUNE.claim_for_p27
        seen = []

        def spy(claims, inj, unit):
            seen.append((inj["type"], inj["new_value"], inj["replacement"], unit))
            return real(claims, inj, unit)
        run_pi(patches=((TUNE, "claim_for_p27", spy),))
        self.assertEqual(6, len(seen))                                                              # 3 つの注入 × 2 profile
        self.assertEqual({T9}, set(x[0] for x in seen))
        self.assertEqual(sorted([(123456.0, u"12億3,456", u"万円"), (1200.0, u"1,200", u"百万円"), (6000.0, u"6,000", u"千円")] * 2), sorted((x[1], x[2], x[3]) for x in seen))

    def test_w_8_a_profile_only_edit_changes_only_that_profile(self):
        rows, _c = run_pi(verify=verify_edit(TEXT_P, edit_drop_id, only_profile="P29E"))
        for r in rows:
            self.assertEqual(((False, False, False), (True, True, True)), (conds_tuple(r, "P29E"), conds_tuple(r, "P30E")))
            self.assertEqual((UNMAPPED_CELL, TUNE.LABEL_NAMED_ORIGINAL), (norm(r["P29E"]), r["P30E"][u"結果"]))
            self.assertTrue(r[u"届いた"])                                                            # 届いたと期は P30E の claim で決まる
            self.assertEqual(u"Prior1Year", r[u"注入後の pointer の期"])
        rows, _c = run_pi(verify=verify_edit(TEXT_P, edit_cut_span, only_profile="P30E"))
        for r in rows:
            self.assertEqual(((True, True, True), (True, True, False)), (conds_tuple(r, "P29E"), conds_tuple(r, "P30E")))
            self.assertFalse(r[u"届いた"])
        # 注入後の claim の期: P30E の claim が別の期を名指すとき、P29E の claim の期は行に出ない
        base = make_verify(TEXT_P, base_ptr=PTR_PRIOR, inj_state=V_, inj_ptr=PTR_PRIOR)
        other = make_verify(TEXT_P, base_ptr=PTR_PRIOR, inj_state=V_, inj_ptr=PTR_CUR)
        rows, _c = run_pi(verify=lambda zb, p, t: (other if (p == "P30E" and t != TEXT_P) else base)(zb, p, t))
        self.assertEqual([u"CurrentYear"] * 3, [r[u"注入後の pointer の期"] for r in rows])
        rows, _c = run_pi(verify=lambda zb, p, t: (other if (p == "P29E" and t != TEXT_P) else base)(zb, p, t))
        self.assertEqual([u"Prior1Year"] * 3, [r[u"注入後の pointer の期"] for r in rows])

    def test_w_9_a_claim_that_does_not_pair_between_the_profiles_leaves_the_p29e_cell_unmapped(self):
        base = make_verify(TEXT_P)

        def verify(zb, p, t):
            out = base(zb, p, t)
            if p == "P29E":
                for cl in out["claims"]:
                    cl["span"] = cl["span"] + u"x"                  # (value, span, unit) が P30E の claim と結べない
            return out
        rows, c = run_pi(verify=verify)
        self.assertTrue(rows)
        for r in rows:
            self.assertIs(False, r[LINK_KEY], r)
            self.assertEqual(TUNE.LABEL_UNMAPPED, r["P29E"][u"結果"])
            self.assertIsNone(r[F_COND % "P29E"])
            self.assertEqual([NO_BASE], r[F_MISS % "P29E"])
            self.assertEqual({OLD_KEYS[0]: False, OLD_KEYS[1]: False}, dict(r[F_OLD % "P29E"]))
            self.assertTrue(r["P30E"][u"対応"])
        self.assertEqual({PI.UNLINKED}, set(c[u"採った の状態"]))
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))

    def test_w_9b_each_profile_is_looked_up_by_its_own_base_claim_id(self):
        u"""P29E の土台の claim の id が P30E の土台の id と違っても(値と span で結ぶので在りうる)、P29E は自分の土台の id で引く。"""
        base = make_verify(TEXT_P)

        def verify(zb, p, t):
            out = base(zb, p, t)
            if p == "P29E":
                for cl in out["claims"]:
                    cl["id"] = u"A" + cl["id"][1:]                                              # P29E の claim の id は N でなく A で始まる
            return out
        rows, c = run_pi(verify=verify)
        self.assertEqual(3, len(rows))
        for r in rows:
            self.assertTrue(r[LINK_KEY])
            self.assertTrue(r[u"基準の claim"].startswith(u"N"))                          # 基準の claim の欄は P30E の id
            self.assertEqual(((True, True, True), (True, True, True)), (conds_tuple(r, "P29E"), conds_tuple(r, "P30E")))
            self.assertTrue(r["P29E"][u"対応"] and r["P30E"][u"対応"])
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))

    def test_w_10_the_claim_count_column_is_the_p30e_count_before_and_after(self):
        rows, _c = run_pi()
        self.assertEqual([True] * 3, [r[F_SAMEN] for r in rows])
        for edit in (lambda cl: cl.append(dict(cl[0], id=u"Q999")), lambda cl: cl.pop()):
            rows, _c = run_pi(verify=verify_edit(TEXT_P, edit, only_profile="P30E"))
            self.assertEqual([False] * 3, [r[F_SAMEN] for r in rows])
        rows, _c = run_pi(verify=verify_edit(TEXT_P, lambda cl: cl.append(dict(cl[0], id=u"Q999")), only_profile="P29E"))     # P29E の数の違いは欄に出ない(P30E の数)
        self.assertEqual([True] * 3, [r[F_SAMEN] for r in rows])

    def test_w_11_round_trip_is_false_when_the_revert_does_not_give_the_original_back(self):
        real = IJ.revert
        rows, _c = run_pi(patches=((IJ, "revert", lambda tampered, chosen, placements, original: tampered),))          # 壊した revert(差し替えを戻さない)
        self.assertEqual([False, False, False], [r[u"round-trip"] for r in rows])
        self.assertTrue(all(r[u"読み直し"] for r in rows))                                  # 他の欄は動かない
        rows, _c = run_pi(patches=((IJ, "revert", lambda tampered, chosen, placements, original: real(tampered, chosen, placements, original) + u"。"),))
        self.assertEqual([False, False, False], [r[u"round-trip"] for r in rows])
        rows, _c = run_pi()
        self.assertEqual([True, True, True], [r[u"round-trip"] for r in rows])

    def test_w_12_reread_is_false_when_the_text_carries_another_value_or_unit(self):
        real = IJ.apply_edits

        def other_value(text, chosen):
            return real(text, [dict(c, replacement=u"9" + c["replacement"]) for c in chosen])             # 先頭に 1 字足して値を変える
        rows, _c = run_pi(patches=((IJ, "apply_edits", other_value),))
        self.assertEqual([False, False, False], [r[u"読み直し"] for r in rows])
        self.assertTrue(all(r[u"round-trip"] for r in rows))                                  # round-trip は revert が元の字を持つので別の欄

        def drop_unit(text, chosen):
            out, pl = real(text, chosen)
            return out.replace(u"万円", u"", 1).replace(u"百万円", u"", 1).replace(u"千円", u"", 1), pl
        rows, _c = run_pi(patches=((IJ, "apply_edits", drop_unit),))
        self.assertFalse(all(r[u"読み直し"] for r in rows))
        rows, _c = run_pi()
        self.assertEqual([True, True, True], [r[u"読み直し"] for r in rows])

    def test_w_13_the_leading_group_column_is_true_only_for_a_compound_that_loses_a_group(self):
        text = u"前期の売上高は1億500万円でした。"                 # 前期 1億500万円 → 当期 9,700万円(先頭の位の「億」が落ちる複合)
        refs = [{"key": "jppfs:NetSales@CurrentYearDuration", "value": 97000000.0, "unit": u"円", "label": u"売上高"},
                {"key": "jppfs:NetSales@Prior1YearDuration", "value": 105000000.0, "unit": u"円", "label": u"売上高"}]
        rows, _c = run_pi(text=text, refs=refs)
        self.assertEqual(1, len(rows))
        self.assertEqual((u"複合", True, True, True), (rows[0][u"形"], rows[0][u"先頭の位が減った"], rows[0][u"読み直し"], rows[0][u"round-trip"]))
        rows, _c = run_pi()                                   # 位が減らない複合・既存
        self.assertEqual([False, False, False], [r[u"先頭の位が減った"] for r in rows])
        with Patch() as pt:
            pt.set(NS, "groups_in", lambda s: 99)                                          # 位の数を数える関数を壊すと欄が動く(この script は NS.groups_in を呼ぶ)
            rows, _c = run_pi(text=text, refs=refs)
        self.assertEqual([False], [r[u"先頭の位が減った"] for r in rows])

    def test_w_14_the_cap_is_applied_after_the_base_filter_and_before_nothing_else(self):
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
        rows, c = run_pi(text=text, refs=refs, verify=verify_some)
        self.assertEqual((16, 12, 10, 10), (sum(c[u"作れる site"].values()), c[u"土台 P30E が GROUNDED の site"], c[u"採った"], c[u"cap を基準で絞る前に掛けた数"]))
        self.assertEqual(10, len(rows))
        self.assertEqual({PI.LINKED: 12, PS.STATUS_NOT_G: 4}, dict(c[u"作れる site の状態"]))
        self.assertEqual({PI.LINKED: 10}, dict(c[u"採った の状態"]))
        self.assertEqual([], count_problems(u"bk", c, rows, RUN.INJECT_CAP))
        rows2, c2 = run_pi(text=text, refs=refs, verify=verify_some, patches=((RUN, "INJECT_CAP", 3),))      # cap は script の既定の引数(RUN.INJECT_CAP を import 時に読む)ではなく引数で渡せる
        self.assertEqual(10, len(rows2))

    def test_w_15_a_fullwidth_digit_book_is_skipped(self):
        rows, c = run_pi(text=u"前期の売上高は９億円でした。")
        self.assertEqual([], rows)
        self.assertEqual([u"注入しない"], list(c))

    def test_w_16_the_job_refuses_a_switch_that_is_off(self):
        with self.assertRaises(PI.Stop):
            PI.inject_job_pi(("aiforms", "n", {}, {}, "d", {}, "s", "w"))

    def test_w_17_swapped_t9_functions_reach_the_rows_of_this_script(self):
        u"""この script は T9 の site・行の欄の関数を呼ぶ(コピーを持たない)。T9 の関数を差し替えると行が変わる。"""
        text = u"前期は9億7,000万円でした。前期の1,000百万円でした。前期は5,000千円でした。"
        for const in (True, False):
            rows, c = run_pi(patches=((PI.PS, "engine_cue", lambda t, tok, const=const: const),))
            self.assertEqual([const] * 3, [r[u"engine の手がかり"] for r in rows], const)
            self.assertEqual(3 if const else 0, c[u"作れる site の手がかり"][u"真"])
            rows, _c = run_pi(patches=((PI.PS, "has_prior_word", lambda t, tok, const=const: const),))
            self.assertEqual([const] * 3, [r[u"文に前期の語"] for r in rows], const)
            rows, _c = run_pi(patches=((PI.PS, "reached_of", lambda *a, const=const: const),))
            self.assertEqual([const] * 3, [r[u"届いた"] for r in rows], const)
        rows, _c = run_pi(patches=((PI.PS, "pointer_period", lambda ptrs: u"他"),))
        self.assertEqual(([u"他"] * 3, [u"他"] * 3), ([r[u"基準の pointer の期"] for r in rows], [r[u"注入後の pointer の期"] for r in rows]))
        rows, _c = run_pi(patches=((PI.PS, "shape_of_token", lambda tok: u"万だけ"),))
        self.assertEqual([u"万だけ"] * 3, [r[u"形"] for r in rows])
        real_build = PS.build_t9
        rows, _c = run_pi(patches=((PI.PS, "build_t9", lambda site, inj_id: real_build(site, u"Z" + inj_id)),))
        self.assertEqual(["Zbk-T9-01", "Zbk-T9-02", "Zbk-T9-03"], [r[u"id"] for r in rows])
        seen = []
        real_sites = PS.t9_all_sites
        rows, _c = run_pi(patches=((PI.PS, "t9_all_sites", lambda *a: seen.append(a[2:]) or real_sites(*a)),))
        self.assertEqual([(u"sd", u"bk")], seen)                                                  # 種と本の名前をそのまま T9 の関数に渡す
        self.assertEqual(3, len(rows))
        rows, c = run_pi(patches=((PI.PS, "t9_all_sites", lambda *a: (collections.OrderedDict((k, 0) for k in PS.STAGE_KEYS), [])),))
        self.assertEqual(([], 0), (rows, c[u"採った"]))

    def test_w_18_the_engine_cue_is_read_from_the_untampered_text_and_token(self):
        seen = []
        real = PS.R._prior_cue
        run_pi(patches=((PI.PS.R, "_prior_cue", lambda s, a, b=None: seen.append((s, a, b)) or real(s, a, b)),))
        self.assertTrue(seen)
        with PI.yen_scan_on():
            spans = [(t.start, t.end) for t in N.scan(TEXT_P)]
        for s, a, b in seen:
            self.assertEqual(TEXT_P, s)                                                           # 注入前の文
            self.assertIn((a, b), spans)                                                          # 注入前の token の start・end

    def test_w_19_the_t9_book_names_and_site_population_do_not_change(self):
        u"""同じ入力で T9 の script と同じ site・同じ id・同じ cap(行の id の集合が T9 の記録と同じになる根拠)。"""
        rows, c = run_pi(seed=u"s1", key=u"bkA")
        t9rows, t9c = PSR.run_ps(seed=u"s1", key=u"bkA")
        self.assertEqual([r[u"id"] for r in t9rows], [r[u"id"] for r in rows])
        self.assertEqual([r[u"基準の claim"] for r in t9rows], [r[u"基準の claim"] for r in rows])
        self.assertEqual(norm(t9c), norm(c))


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
            pt.set(PI, "load_books", lambda root=ROOT, only=None: [("aiforms", "DOC1_F1_m1", item, {}, {})])

            def pool(fn, jobs_, procs):
                seen.append(getattr(N, FLAG))
                return [("DOC1_F1_m1", [collections.OrderedDict(r) for r in rows if r["docID"] == "DOC1"], norm(base[u"本ごとの数え"][u"DOC1_F1_m1"]))]
            pt.set(NF, "map_pool", pool)
            pt.set(PI, "caches_all", lambda: collections.OrderedDict())
            pt.set(GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
            pt.set(PI, "header_pi", lambda root, step, seed_meta, before, after, profiles: collections.OrderedDict([(u"seal", SEAL_REL), (u"profile", list(profiles))]))
            out = os.path.join(d, "inject.json")
            rec = PI.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with open(out, encoding="utf-8") as fh:
                disk = json.load(fh)
            with self.assertRaises(PI.Stop):                                                    # 出力が在れば測り直さない
                PI.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with self.assertRaises(PI.Stop):                                                    # --only は --out が要る(本番の記録を作らない。守りが壊れても root の下の使い捨ての場所に書く)
                PI.run_inject(root=d, procs=1, only="DOC1", say=lambda *a: None, work_root=d)
            self.assertFalse(os.path.exists(os.path.join(d, PI.INJECT_REL)))
        self.assertEqual([True], seen)                                    # map_pool の呼ばれた間は真
        self.assertFalse(getattr(N, FLAG))                                # 出たら偽
        self.assertEqual(norm(rec), disk)
        self.assertEqual(BASE_WORD_PIN, disk[u"型"][u"土台"])
        self.assertEqual(SITE_WORD_PIN, disk[u"型"][u"site"])
        self.assertEqual(PI.seal_limits(read(SEAL_REL)) + list(PI.EXTRA_LIMITS), disk[u"限界"])
        self.assertEqual({u"名前": FLAG, u"inject の中の値": True, u"出たあとの値": False, u"配線の問題": []}, disk[u"切り替え"])
        self.assertEqual(norm(PI.q_columns(disk[u"行"], fixed_records()["t9"][u"行"])), disk[Q_KEY])      # Q の欄は T9 の記録を読んで数える
        self.assertEqual(norm(PI.cue_breakdown(disk[u"行"])), disk[PI.CUE_KEY])
        self.assertEqual(norm(PI.period_breakdown(disk[u"行"])), disk[PI.PERIOD_KEY])
        self.assertEqual([u"P29E", u"P30E"], disk[u"profile"])
        self.assertEqual([T9], list(disk[u"集計"]))
        self.assertEqual(u"**--only(本番の記録ではない)**", PI.scope_word("x"))
        self.assertEqual(u"全 200 本", PI.scope_word(None))

    def _stops(self, why, *extra, flag_before=False):
        u"""run_inject を読み込み・並列・cache を偽にして走らせ、extra の差し替えで Stop になり(Stop の文に why が入る = 別の守りが代わりに止めたのではない)記録が書かれないことを見る。"""
        base = sample_inject()
        rows = norm(base[u"行"])
        item = {u"docID": "DOC1", u"form": "F1", u"model": "m1", u"writer": "W1", u"sha256": "0" * 64}
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(RUN, "PROFILES", RUN.PROFILES)
            pt.set(RUN, "base_status4", RUN.base_status4)
            pt.set(PI, "load_books", lambda root=ROOT, only=None: [("aiforms", "DOC1_F1_m1", item, {}, {})])
            pt.set(NF, "map_pool", lambda fn, jobs_, procs: [("DOC1_F1_m1", [collections.OrderedDict(r) for r in rows if r["docID"] == "DOC1"], norm(base[u"本ごとの数え"][u"DOC1_F1_m1"]))])
            pt.set(PI, "caches_all", lambda: collections.OrderedDict())
            pt.set(GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
            pt.set(PI, "header_pi", lambda root, step, seed_meta, before, after, profiles: collections.OrderedDict([(u"seal", SEAL_REL), (u"profile", list(profiles))]))
            for mod, name, v in extra:
                pt.set(mod, name, v)
            out = os.path.join(d, "inject.json")
            setattr(N, FLAG, flag_before)
            try:
                with self.assertRaises(PI.Stop) as cm:
                    PI.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            finally:
                setattr(N, FLAG, False)                                                           # 試験が立てた旗は必ず戻す
            self.assertIn(why, str(cm.exception))
            self.assertFalse(os.path.exists(out))                                                 # Stop したら記録を書かない
        self.assertFalse(getattr(N, FLAG))

    def test_w_20b_run_inject_stops_before_writing_when_a_guard_fires(self):
        u"""正常な入力では発火しない守り(旗が真のまま・差し替えが届かない・配線が崩れた・with を出ても真・cache が変わった)を、故障を作って当てる。"""
        calls = {"n": 0}

        def moving_snapshot(caches):
            calls["n"] += 1
            return {u"n": calls["n"]}                                                             # 前と後で違う
        import contextlib

        @contextlib.contextmanager
        def leaky_switch():
            setattr(N, FLAG, True)
            yield                                                                                 # 出るときに戻さない
        self._stops(u"差し替えが届いていない", (PI, "inject_wiring_problems", lambda: [u"差し替えが届いていない"]))
        self._stops(u"切り替えを真にできない・配線が崩れた", (PI, "wiring_problems", lambda: [u"N がちがう"]))      # with の中で配線が崩れた
        self._stops(u"with を出ても切り替えが真のまま", (PI, "yen_scan_on", leaky_switch))
        self._stops(u"cache の件数か名前が変わった", (GEN, "caches_snapshot", moving_snapshot))
        self._stops(u"切り替えが真のまま inject を始めた", flag_before=True)                           # 旗が真のまま始めたら止める(with の外で真)

    def test_w_21_the_header_of_a_real_record_passes_the_header_check(self):
        u"""script の ``header_pi`` が作る頭が、門の頭の検査を通る。1 欄ずつ落とすと赤。"""
        h = PI.header_pi(ROOT, u"標本", {u"seed_file": u"x"}, {}, {}, INJECT_PROFILES)
        rec = collections.OrderedDict(h)
        rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
        rec[u"範囲"] = u"全 200 本"
        self.assertEqual([], header_problems(norm(rec), True))
        self.assertEqual((SEAL_REL, SEAL_COMMIT_SHORT), (rec[u"seal"], rec[u"封の commit"]))
        for key in (u"lib の指紋", u"J の script の sha256", u"nscan script の sha256", u"rmix script の sha256", u"H の記録の sha256", u"J の記録の sha256", u"RB の記録の sha256",
                    u"engine の指紋", u"この script の sha256", u"生成の記録の sha256", u"T9 の script の sha256", u"T9 の記録の sha256"):
            r2 = norm(rec)
            r2.pop(key)
            self.assertNotEqual([], header_problems(r2, True), key)
        self.assertEqual(sha256_rel(SCRIPT_REL), rec[u"この script の sha256"])                     # T9 の script の sha ではなくこの script の sha
        self.assertNotEqual(rec[u"この script の sha256"], rec[u"T9 の script の sha256"])

    def test_w_22_the_q_columns_read_the_t9_record_given_not_a_cached_one(self):
        rows = sample_rows()
        c = PI.q_columns(rows, sample_t9_rows(rows))
        self.assertEqual(8, c[QCOL["Q-2"]][u"行の数"])
        c2 = PI.q_columns(rows, sample_t9_rows(rows)[:5])
        self.assertEqual((5, False, 3), (c2[QCOL["Q-2"]][u"T9 の記録の行の数"], c2[QCOL["Q-2"]][u"id の集合が T9 の記録と同じ"], c2[QCOL["Q-2"]][u"この記録にだけ在る id"]))
        self.assertEqual(1, PI.q_columns(rows[:5], sample_t9_rows(rows))[QCOL["Q-2"]][u"T9 の記録にだけ在る id"] - 2)       # 行が 5 本・T9 が 8 本: T9 にだけ在る 3


# ================================================================ 宣言(docID を持つ記録は LATER_NAMING_FILES に、script は LATER_HARNESS_FILES に宣言する)
literal_assign = PSR.literal_assign
later_naming_files = PSR.later_naming_files


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
        for rel in ("fixtures/xbrl/nscan/inject_2026-11-05.json", "fixtures/xbrl/nscan/offcheck_2026-11-05.json", "fixtures/xbrl/rmix/ai200_2026-11-04.json",
                    "fixtures/xbrl/numfix/ai200_2026-11-04.json", "fixtures/xbrl/jtypes/inject_2026-11-05.json", "fixtures/xbrl/pswap/inject_2026-11-06.json"):
            self.assertIn(rel, got)

    def test_h_3_the_script_is_declared_as_a_harness_file(self):
        src = read("tests/measure/test_xbrl_inject_harness_review.py")
        self.assertEqual([], harness_problems(src))
        self.assertNotEqual([], harness_problems(src.replace(u'"%s"' % SCRIPT_REL, u'"x/%s"' % SCRIPT_REL)))
        self.assertNotEqual([], harness_problems(src.replace("LATER_HARNESS_FILES", "LATER_HARNESS_FILE")))
        self.assertIn("measure/xbrl_pswap_2026-11-06.py", src)


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
        J = PI.build_Q(R, self.seal)
        self.assertEqual(set(J), {u"Q", u"K", u"採用", u"欄"})

    def test_r_3_the_result_document_follows_the_records(self):
        R = self.need()
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), R, self.seal, [x for x in PI.git_numstat_since_seal(ROOT) if not SG.SGR.t5y_declared_numstat(x)]))

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
