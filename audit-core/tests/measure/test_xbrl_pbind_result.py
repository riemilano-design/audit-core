# -*- coding: utf-8 -*-
"""PB(前期の手がかりがある数を当期の fact に落とさない。P32E = P30E + 旗。既定にしない)の測定の結果の門。封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §3・§4・§5・追記 1。

記録 3 つ(``fixtures/xbrl/pbind/``: moves_200・regress97・inject)と、読むだけの **T9 の第 2 便の記録**(E-2 の 141 行の比べ先)から、封 §3 の予測 E-1〜E-10 と §4 の採用の基準 K-1〜K-5 を**機械で求め**
(予測の幅は封の字から読む。字のコピーにしない)、結果の文書 ``docs/XBRL_PRIOR_CUE_BIND_ENGINE_RESULT_2026-11-06.md`` の表(``<!-- 門:start pred -->``・``<!-- 門:start judge -->`` の中)を
記録から作り直した表と一行も違わないことを見る。測定の script(``measure/xbrl_pbind_2026-11-06.py`` の ``build_E``・``judge_from``・``columns_from_records``・``render_pred``・``render_judge``)の関数を呼んで照らす。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文・pointer・要素など)が無い・pointer の字(要素名・context)を持たない・key_leaks が空・docID を持つ記録が ``LATER_NAMING_FILES`` に宣言され、
     script が ``LATER_HARNESS_FILES`` に宣言されている・cache の前後が同じ・script と lib と前の便(RB・T9 の第 2 便・T9)の script・入力の記録の sha256 が現物と一致・
     engine の指紋が engine の commit の木から作り直した値と一致する・engine の commit が履歴から探した値と一致する。
  b  記録の中身が再計算と一致する: 本の整合(動いた行の中身と GROUNDED の増減・札)・書類の整合(動いた行の欄と XR の定義の行)・注入の行の整合(対応の条件・欠けた条件・期)・集計・
     **E の欄の全部を 行・本・書類から数え直す**(欄を 0 に固定すると赤。行の欄を 1 つ変えると該当の欄が動く)・E-1・E-8(git の履歴から)・E-7・E-9 の写し(engine の commit の message から)。
  c  判定: 記録(の欄)を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。採用は K-1〜K-5 を全部満たすときだけ。判定は記録の集計でなく行・本・書類から求める。
     **T9 の第 2 便の記録を壊した写し**(id を 1 つ変える・P30E の state を 1 つ変える)で E-2 と K-1 が赤になる。
  d  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 b7824e6 ⊏ engine を触った commit ⊏ 記録・結果の文書(script・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  g  変異: 小さい標本の記録 3 つと文書で同じ検査が緑 → 変異(記録の数・欄・表の 1 字・封の予測の 1 字・順序・記録の禁止欄・指紋の 1 字・cache の前後・pointer の字・期の欄)で赤。
  w  手順: script の ``judge_book_pb``・``doc_moves_pb``・``inject_text_pb`` を小さい入力(zip・判定は偽。lib は本物)で通し、動いた行・札・既存 / 新・前期の fact が無い要素・
     P30E と P32E の対応付け(profile ごとの土台の id)・T9 の第 2 便の script の行と同じ欄が同じ値であることを、壊した差し替えで True ↔ False が替わる例で固定する。

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


SG = load_module("tests/measure/test_xbrl_pbind_seal.py", "pbind_seal_gate_for_result")                 # 封の門の部品。門としては走らせない
PSR = load_module("tests/measure/test_xbrl_pswap_result.py", "pswap_result_gate_for_pbind_result")      # T9 の結果の門の部品(偽の verify・標本の文と ref)。門としては走らせない
PB = SG.PB
SGR = SG.SGR
PR = SG.PR
RM, RR, PI, PS, XR = PB.RM, PB.RR, PB.PI, PB.PS, PB.XR
NF, GEN, RUN, TUNE = PB.NF, PB.GEN, PB.RUN, PB.TUNE

SEAL_REL = PB.SEAL_REL
DOC_REL = PB.DOC_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
ADDENDUM_COMMIT_SHORT = SG.ADDENDUM_COMMIT_SHORT
SCRIPT_REL = PB.SCRIPT_REL
REC_REL = collections.OrderedDict(PB.REC_REL)
ENGINE_FILES = SG.ENGINE_FILES
NOT_GATED = PR.NOT_GATED
HIT, MISS = PB.HIT, PB.MISS
FORBIDDEN_KEYS = PSR.FORBIDDEN_KEYS
COMPANY_WORDS = PSR.COMPANY_WORDS
POINTER_TEXT_RE = PSR.POINTER_TEXT_RE
DOCID_RE = SG.DOCID_RE
FOR_RESULT_WORDS = PSR.FOR_RESULT_WORDS
HAVE_CACHE = all(os.path.isdir(p) for p in PB.caches_all().values())
Patch = PSR.Patch
norm = PSR.norm
norm_t = PSR.norm_t
walk = PSR.walk
walk_strings = PSR.walk_strings
read = PSR.read
jload = PSR.jload
_SHA = {}


def sha256_rel(rel):
    u"""現物の sha256(門の中で file は変わらないので 1 回だけ読む)。"""
    if rel not in _SHA:
        _SHA[rel] = PSR.sha256_rel(rel)
    return _SHA[rel]
G, V_, U_, P_ = "GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"
PTR_PRIOR, PTR_CUR = PSR.PTR_PRIOR, PSR.PTR_CUR
TEXT_P, REFS_P = PSR.TEXT_P, PSR.REFS_P
make_verify = PSR.make_verify
PERIODS5 = PB.PERIODS5
LINK_KEY = PB.LINK_KEY
LABEL_WORDS = PB.LABEL_WORDS
NO_LABEL = PB.NO_LABEL
EXISTING, NEWROW = PB.EXISTING, PB.NEWROW
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
#: 封 §3・§4 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("E-1", collections.OrderedDict([(u"recipes 挿入", (18, 28)), (u"recipes 削除", 0), (u"vocabulary 挿入", (4, 6)), (u"vocabulary 削除", 0), (u"他の file", 0)])),
    ("E-2", collections.OrderedDict([(u"byte が同じ書類", 97), (u"書類", 97), (u"P30E の結果と state が同じ行", 141), (u"行", 141)])),
    ("E-3", collections.OrderedDict([(u"GROUNDED を失う行", 0), (u"動いた行", (15, 25)), (u"動いた書類", (3, 8))])),
    ("E-4", collections.OrderedDict([(u"動いた行", (45, 65)), (u"GROUNDED を失う行", (0, 2)), (u"うち札 真", (0, 2)), (u"POINTER_NOT_FOUND → VALUE_MISMATCH", (12, 20))])),
    ("E-5", collections.OrderedDict([(u"当期の fact に GROUNDED", 0), (u"前期の fact を名指して VALUE_MISMATCH", (120, 129)), (u"別の fact に GROUNDED", (0, 3)),
                                    (u"手がかり偽の行のうち P30E と同じ行", 12), (u"手がかり偽の行", 12)])),
    ("E-6", collections.OrderedDict([(u"通した率(P32E)", (5.0, 12.0)), (u"名指して原本の割合", (90.0, 100.0))])),
    ("E-7", collections.OrderedDict([(u"赤", 10), (u"変異の本数", 10)])),
    ("E-8", (40, 75)),
    ("E-9", collections.OrderedDict([(u"赤の試験", [u"axis3 test_9"]), (u"ほかの赤", 0)])),
    ("E-10", collections.OrderedDict([(u"期", u"Prior1Year"), (u"行", (17, 19))])),
    ("K-1", (97, 97, 141, 141)), ("K-2", 0), ("K-3", 2),
    ("K-4", collections.OrderedDict([(u"当期の fact に GROUNDED", (0, 3)), (u"手がかり偽の行", 12)])),
    ("K-5", collections.OrderedDict([(u"赤", 10), (u"変異の本数", 10)]))])
#: 注入の土台の字・site の字(測定の script の定数と同じでなければ赤)
BASE_WORD_PIN = u"無改変の文で P30E が GROUNDED の claim"
SITE_WORD_PIN = u"ref の context が Prior1Year で始まり、同じ要素の CurrentYear の fact がちょうど 1 件・単位が同じ・両方正・値が違い、当期の値を元の字の形で描ける数(既存・万だけ・複合の全部)"
#: 記録の限界の字の頭(literal に留める。script の字を変えたら赤)
LIMITS_PIN = collections.OrderedDict([
    ("moves", (u"通した・止めたは engine の state で、動いた行の札は前の便の盲検の 1 席目", u"200 本は Claude の model 2 つが書いた文", u"前期の fact が無い要素は P32E の claim の先頭の pointer の要素に")),
    ("regress97", (u"97 書類は 2026 年提出の有報に偏る", u"札が無いので動いた行の正しさは見ていない")),
    ("inject", (u"注入は T9 の 1 型だけ", u"土台は P30E が GROUNDED の claim", u"engine の手がかりは T9 の recipes._prior_cue の真偽", u"通した・止めたは engine の state で、札(人の目)は無い"))])
#: 行の欄の名前と並び(script の ``inject_text_pb`` の行)
ROW_KEYS = (u"docID", u"form", u"model", u"writer", u"id", u"型", u"形", u"基準の claim", LINK_KEY, u"round-trip", u"読み直し", u"engine の手がかり", u"窓の手がかり", u"文に前期の語",
            u"基準の pointer の期", "P30E", "P32E", u"P30E の注入後の pointer の期", u"P32E の注入後の pointer の期", u"P30E の欠けた条件", u"P32E の欠けた条件")
CELL_KEYS = (u"対応", u"結果", u"state", u"reason")
UNMAPPED_CELL = {u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}
RESULT_LABELS = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
SHAPES = PS.SHAPES
CONDS = PI.CONDS
NO_BASE = PI.NO_BASE
#: 記録の頭が写す入力の記録・script(測定の script が header_pb に渡す path とは別に、門が literal で持つ)
RB_RECORD_REL = "fixtures/xbrl/rmix/regress97_2026-11-04.json"
T9_RECORD_REL = "fixtures/xbrl/pswap/inject_idmap_2026-11-06.json"
PREV_SCRIPT_RELS = ("measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py", "measure/xbrl_pswap_idmap_2026-11-06.py", "measure/xbrl_pswap_2026-11-06.py")
LIB_RELS = tuple(PI.LIB_RELS)
SEP = u"::"


def records_exist():
    if FORCE["no_records"]:
        return False
    return all(os.path.exists(os.path.join(ROOT, v)) for v in REC_REL.values())


_FIXED = {}


def t9_record():
    u"""読むだけの T9 の第 2 便の記録(1 回だけ読む)。"""
    if not _FIXED:
        _FIXED["t9"] = jload(T9_RECORD_REL)
    return _FIXED["t9"]


def load_records():
    out = collections.OrderedDict((k, jload(v)) for k, v in REC_REL.items())
    out["t9"] = t9_record()
    return out


def input_rels(kind):
    u"""記録の頭の ``入力の記録の sha256`` が持つべき path の列(門が literal から作る)。"""
    if kind == "moves":
        rels = []
        for src, p in PB.SOURCES.items():
            rels += [p["gen"], p["claims"]]
        return rels + list(PB.LABELS_REL.values()) + ["fixtures/xbrl/numfix/ai200_2026-11-04.json"]
    if kind == "regress97":
        return [RB_RECORD_REL]
    return [T9_RECORD_REL] + [p["gen"] for p in PB.SOURCES.values()]


# ---------------------------------------------------------------- engine の指紋・engine の差分(engine の commit の木・履歴から作り直す。engine はこの便で変えない)
_FP = []


_EC = []


def engine_commit_full():
    if not _EC:
        seal, e = SGR.engine_commit(REPO, PREFIX, SEAL_REL, ENGINE_FILES)
        if seal is None or e is None:
            raise AssertionError(u"封か engine の commit が履歴に無い")
        _EC.append((seal, e))
    return _EC[0]


def engine_fingerprint_at_commit():
    u"""engine の commit の木の ``adapters/xbrl`` と ``core/py/audit_core`` の .py から作った指紋 {adapter_xbrl_py_sha256, core_py_sha256}。"""
    if not _FP:
        _seal, e = engine_commit_full()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            arc = subprocess.run(["git", "archive", e, PREFIX + "adapters/xbrl", PREFIX + "core/py/audit_core"], cwd=REPO, stdout=subprocess.PIPE, check=True)
            subprocess.run(["tar", "-x", "-C", d], input=arc.stdout, check=True)
            a, _na = PB.VD._py_digest(os.path.join(d, PREFIX, "adapters", "xbrl"))
            c, _nc = PB.VD._py_digest(os.path.join(d, PREFIX, "core", "py", "audit_core"))
        _FP.append({"adapter_xbrl_py_sha256": a, "core_py_sha256": c})
    return _FP[0]


def link_at_history():
    u"""E-1・E-8 の欄を履歴から作り直す(測定の script とは別に書く)。"""
    seal, e = engine_commit_full()
    num = [x for x in PR.git_in(REPO, "diff", "--numstat", seal, e, "--", PREFIX + "adapters", PREFIX + "core")[1].splitlines() if x]
    tests = [x for x in PR.git_in(REPO, "diff", "--name-status", seal, e, "--", PREFIX + "tests")[1].splitlines() if x]
    st = collections.Counter(t.split("\t")[0][0] for t in tests)
    ns = collections.OrderedDict((x.split("\t")[2][len(PREFIX):], [int(x.split("\t")[0]), int(x.split("\t")[1])]) for x in num)
    return collections.OrderedDict([
        (u"封の commit", seal), (u"engine の commit", e),
        (u"engine の変更 file", sorted(ns)),
        (u"engine の挿入の行数", sum(v[0] for v in ns.values())), (u"engine の削除の行数", sum(v[1] for v in ns.values())),
        (u"直した file(M)", st.get("M", 0)), (u"新しい file(A)", st.get("A", 0)), (u"消した file(D)", st.get("D", 0)), (u"tests の変更 file", len(tests)),
        (u"numstat", ns)])


def engine_message_at_history():
    _seal, e = engine_commit_full()
    return PR.git_in(REPO, "log", "-1", "--format=%B", e)[1]


# ---------------------------------------------------------------- 封の字(a)
def bounds_problems(seal):
    u"""封の字から読んだ予測の幅が、ここに留めた値と同じか。"""
    out = []
    try:
        got = PB.seal_bounds(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return [u"封から幅を読めない(%s)" % type(e).__name__]
    for k, v in BOUNDS_PIN.items():
        g = got.get(k)
        if json.dumps(norm_t(g) if not isinstance(g, (str, list)) else g, sort_keys=True) != json.dumps(norm_t(v) if not isinstance(v, (str, list)) else v, sort_keys=True):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, g, v))
    if list(PB.seal_pred_rows(seal)) != list(SG.PRED_IDS) or list(PB.seal_k_rows(seal)) != list(SG.K_IDS):
        out.append(u"封の予測の行が E-1〜E-10・K の行が K-1〜K-5 でない")
    return out


# ---------------------------------------------------------------- 記録(a)(b)
def header_problems(k, rec, full):
    u"""記録の頭(封・script・lib・前の便の script と記録・engine・cache)。k = moves / regress97 / inject。"""
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT or rec.get(u"封の追記の commit") != ADDENDUM_COMMIT_SHORT:
        out.append(u"%s: 封の名か commit が違う" % k)
    if rec.get(u"この script の sha256") != sha256_rel(SCRIPT_REL):
        out.append(u"%s: この script の sha256 が現物と違う" % k)
    if norm(rec.get(u"前の便の script の sha256")) != dict((rel, sha256_rel(rel)) for rel in PREV_SCRIPT_RELS):
        out.append(u"%s: 前の便の script の sha256 が現物と違う" % k)
    if norm(rec.get(u"入力の記録の sha256")) != dict((rel, sha256_rel(rel)) for rel in input_rels(k)):
        out.append(u"%s: 入力の記録の sha256 が現物と違う" % k)
    if norm(rec.get(u"lib の指紋")) != dict((rel, sha256_rel(rel)) for rel in LIB_RELS):
        out.append(u"%s: lib の指紋が現物と違う" % k)
    _seal, e = engine_commit_full()
    if rec.get(u"engine の commit") != e:
        out.append(u"%s: engine の commit が履歴から探した値と違う" % k)
    fp = rec.get(u"engine の指紋") or {}
    want = engine_fingerprint_at_commit()
    for name in want:
        if fp.get(name) != want[name]:
            out.append(u"%s: engine の指紋 %s が engine の commit の木から作り直した値と違う" % (k, name))
    if not re.fullmatch(r"[0-9a-f]{40}", str(rec.get(u"HEAD の commit") or u"")):
        out.append(u"%s: HEAD の commit が 40 字の 16 進でない" % k)
    want_profile = list(PB.NOW_PROFILES) if k == "regress97" else list(PB.PROFILES)
    if rec.get(u"profile") != want_profile:
        out.append(u"%s: profile が違う" % k)
    cb = rec.get(u"cache の前後") or {}
    if cb.get(u"変化なし") is not True or cb.get(u"前") != cb.get(u"後"):
        out.append(u"%s: cache の前後が同じでない" % k)
    if full and rec.get(u"範囲") not in (u"全 200 本", u"全 97 書類"):
        out.append(u"%s: 範囲が全部でない" % k)
    lim = list(rec.get(u"限界") or [])
    if len(lim) != len(LIMITS_PIN[k]) or [x[:len(p)] for x, p in zip(lim, LIMITS_PIN[k])] != list(LIMITS_PIN[k]):
        out.append(u"%s: 限界の字か数が留めた値と違う" % k)
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
    if any(POINTER_TEXT_RE.search(s) for s in walk_strings(rec)):
        out.append(u"%s: 記録に pointer の字(要素名・context)がある" % k)
    run, gen = (PI.RUN, PI.GEN) if k == "inject" else (RUN, GEN)
    try:
        with PB.key_check_pb(gen):
            run.assert_clean(copy.deepcopy(rec))
    except gen.Stop:
        out.append(u"%s: 鍵らしい字が記録に在る" % k)
    if rec.get(u"key_leaks", []) != []:
        out.append(u"%s: key_leaks が空でない" % k)
    return out


def entry_shape_ok(x):
    u"""moves の動いた行の中身 [種類, 文の番号, 位置, 前の state, 後の state, 前の期, 後の期, 札, 既存 / 新, 前期の fact が無い要素]。"""
    return (isinstance(x, list) and len(x) == 10 and x[0] == u"num" and isinstance(x[1], int) and isinstance(x[2], int) and not isinstance(x[1], bool) and not isinstance(x[2], bool)
            and x[3] in PB.STATES and x[4] in PB.STATES and x[5] in PERIODS5 and x[6] in PERIODS5 and x[7] in (None,) + LABEL_WORDS and x[8] in (EXISTING, NEWROW)
            and (x[8] == EXISTING or x[7] is None) and isinstance(x[9], bool) and not (x[9] and x[6] == u"Prior1Year"))


def book_problems(b):
    u"""本ごとの整合(自分の欄の間の関係)。"""
    out = []
    nm = b[u"name"]
    n, gr, ent = b[u"数の claim の数"], b[u"GROUNDED の数"], b[u"動いた行の中身"]
    if list(b[u"対応"]) != list(PB.PROFILES) or list(n) != list(PB.PROFILES) or list(gr) != list(PB.PROFILES):
        out.append(u"%s: 対応・数の claim の数・GROUNDED の数の profile が (P30E, P32E) でない" % nm)
    if any(not isinstance(v, bool) for v in b[u"対応"].values()):
        out.append(u"%s: 対応が真偽でない" % nm)
    if b[u"P30E と P32E で数の claim の鍵が同じ"] and n["P30E"] != n["P32E"]:
        out.append(u"%s: 鍵が同じなのに P30E と P32E の数の claim の数が違う" % nm)
    if gr["P30E"] > n["P30E"] or gr["P32E"] > n["P32E"]:
        out.append(u"%s: GROUNDED の数が数の claim の数より多い" % nm)
    if b[u"動いた行"] != len(ent) or b[u"state が変わった行"] != sum(1 for x in ent if x[3] != x[4]) or b[u"動いた行"] > min(n.values()):
        out.append(u"%s: 動いた行か state が変わった行の数が中身と合わない" % nm)
    for x in ent:
        if not entry_shape_ok(x):
            out.append(u"%s: 動いた行の中身の形がおかしい" % nm)
    keys = [(x[1], x[2]) for x in ent]
    if len(keys) != len(set(keys)):
        out.append(u"%s: 動いた行の鍵が重なっている" % nm)
    lost = sum(1 for x in ent if x[3] == G and x[4] != G)
    gained = sum(1 for x in ent if x[3] != G and x[4] == G)
    if b[u"P30E と P32E で数の claim の鍵が同じ"] and gr["P32E"] - gr["P30E"] != gained - lost:
        out.append(u"%s: GROUNDED の増減が なった行 − 失った行 と合わない" % nm)
    if not isinstance(b[u"P27 の鍵が一意"], bool) or not isinstance(b[u"reason だけが違う行"], int) or b[u"reason だけが違う行"] < 0:
        out.append(u"%s: P27 の鍵が一意・reason だけが違う行の型がおかしい" % nm)
    return out


def moves_problems(rec, full):
    out = []
    books = rec[u"本"]
    for b in books:
        out += book_problems(b)
    try:
        agg = norm(PB.aggregate_moves(books))
    except Exception as e:                                   # noqa: BLE001  壊れた記録は集計できない = 赤
        return out + [u"moves: 本から集計を作れない(%s)" % type(e).__name__]
    if agg != rec[u"集計"]:
        out.append(u"moves: 集計が本から作り直した値と違う")
    if not all(all(b[u"対応"].values()) for b in books):
        out.append(u"moves: claim の並びが profile 間で対応しない本がある")
    if full:
        prior = []
        for src, p in PB.SOURCES.items():
            c = jload(p["claims"])
            prior += [(src, b) for b in c[u"本"] if not b.get(u"欠け")]
        if [(b[u"材料"], b[u"name"], b[u"docID"], b[u"form"], b[u"model"]) for b in books] != [(s, b[u"name"], b[u"docID"], b[u"form"], b[u"model"]) for s, b in prior]:
            out.append(u"moves: 本の並びが前の便の claims の記録の本(160 + 40)と違う")
        if len(books) != 200:
            out.append(u"moves: 本が 200 本でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(PB.caches_all())):
            out.append(u"moves: cache の件数か名前が記録の前と違う")
    return out


def doc_problems_one(d):
    u"""書類 1 つの整合(動いた行の欄と XR の定義の行・4 state・claim の数)。"""
    out = []
    nm = d[u"docID"]
    mv = d[u"動いた行と増えた行"][PB.PAIRS[0][0]]
    ents, xr = d[u"P32E の動いた行"], mv[u"動いた既存の行"]
    if sorted(d[u"claims"]) != sorted(PB.NOW_PROFILES) or sorted(d[u"4 state"]) != sorted(PB.NOW_PROFILES) or sorted(d[u"出力の sha256(engine の欄を除く)"]) != sorted(PB.NOW_PROFILES):
        out.append(u"%s: profile の欄が NOW_PROFILES でない" % nm)
    if sorted(d[u"前の便の記録の sha256"]) != sorted(PB.BASE_PROFILES):
        out.append(u"%s: 前の便の記録の sha256 の profile が RB の便の記録の 9 つでない" % nm)
    for x in ents:
        if not (isinstance(x, list) and len(x) == 11 and x[0] in (u"num", u"text") and all(isinstance(v, int) and not isinstance(v, bool) for v in x[1:4])
                and x[4] in PB.STATES and x[5] in PB.STATES and x[6] in PERIODS5 and x[7] in PERIODS5 and isinstance(x[8], bool) and isinstance(x[9], bool) and isinstance(x[10], bool)
                and not (x[10] and x[7] == u"Prior1Year")):
            out.append(u"%s: P32E の動いた行の形がおかしい" % nm)
            continue
        if x[8] != (x[4] != x[5]) or not (x[8] or x[9]):
            out.append(u"%s: P32E の動いた行の state が違う・pointers が違う の欄が合わない" % nm)
    keys = [tuple(x[:4]) for x in ents]
    if len(keys) != len(set(keys)):
        out.append(u"%s: 動いた行の鍵が重なっている" % nm)
    if len(xr) != len(ents) + d[u"reason だけが違う行"]:
        out.append(u"%s: XR の定義の動いた行が 動いた行 + reason だけが違う行 と合わない" % nm)
    if sum(mv[u"増えた行の state"].values()) != mv[u"増えた行"] or d[u"claims"][PB.NEW] - d[u"claims"][PB.OLD] != mv[u"増えた行"] - mv[u"消えた行"]:
        out.append(u"%s: 増えた行・消えた行が claim の数の差と合わない" % nm)
    g = lambda p: d[u"4 state"][p][G]            # noqa: E731
    if mv[u"増えた行"] == 0 and mv[u"消えた行"] == 0:
        lost = sum(1 for x in ents if x[4] == G and x[5] != G)
        gained = sum(1 for x in ents if x[4] != G and x[5] == G)
        if g(PB.NEW) - g(PB.OLD) != gained - lost:
            out.append(u"%s: GROUNDED の増減が なった行 − 失った行 と合わない" % nm)
    return out


def regress97_problems(rec, full):
    out = []
    docs = rec[u"書類"]
    for d in docs:
        try:
            out += doc_problems_one(d)
        except Exception as e:                               # noqa: BLE001
            out.append(u"regress97: 書類の整合を検査できない(%s)" % type(e).__name__)
    try:
        T = norm(PB.regress_block(docs))
    except Exception as e:                                   # noqa: BLE001
        return out + [u"regress97: 書類から集計を作れない(%s)" % type(e).__name__]
    if T != rec[u"集計"]:
        out.append(u"regress97: 集計が書類から作り直した値と違う")
    link = rec.get(u"E-1・E-8 engine の差分") or {}
    cp = rec.get(u"E-7・E-9 の写し") or {}
    if full:
        prev = dict((r["docID"], r) for r in jload(RB_RECORD_REL)[u"書類"])
        if sorted(d[u"docID"] for d in docs) != sorted(prev):
            out.append(u"regress97: 書類が RB の便の記録の 97 書類と違う")
        for d in docs:
            pr = prev.get(d[u"docID"])
            if pr is None:
                continue
            if d[u"前の便の記録の sha256"] != dict((p, pr[u"出力の sha256(engine の欄を除く)"][p]) for p in PB.BASE_PROFILES) or d[u"zip の sha256"] != pr[u"zip の sha256"]:
                out.append(u"regress97: 前の便の記録の sha256 か zip の sha256 が RB の便の記録と違う")
        if len(docs) != 97:
            out.append(u"regress97: 書類が 97 でない")
        if norm(link) != norm(link_at_history()):
            out.append(u"regress97: E-1・E-8 が git の履歴から作り直した値と違う")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(collections.OrderedDict((k, PB.R97.prec().names_sha(v)) for k, v in PB.R97.CACHES.items())):
            out.append(u"regress97: cache の件数か名前が記録の前と違う")
    out += copy_problems(cp, full)
    if not isinstance(link.get(u"numstat"), dict):
        out.append(u"regress97: E-1・E-8 に numstat が無い")
    return out


def copy_problems(cp, full):
    u"""E-7・E-9 の写しの形。full なら engine の commit の message から読み直した値と同じか。"""
    out = []
    if set(cp) != {u"出どころ", u"engine の commit", "E-7", "E-9"}:
        return [u"regress97: E-7・E-9 の写しの欄が違う"]
    if full:
        want = norm(PB.message_numbers(engine_message_at_history()))
        if cp["E-7"] != want["E-7"] or cp["E-9"] != want["E-9"] or cp["E-7"] is None or cp["E-9"] is None:
            out.append(u"regress97: E-7・E-9 の写しが engine の commit の message から読み直した値と違う")
        if cp[u"engine の commit"] != engine_commit_full()[1]:
            out.append(u"regress97: 写しの engine の commit が履歴から探した値と違う")
    return out


def cell_problems(r, p):
    u"""行の profile p の欄(結果の語・対応・欠けた条件・期)。"""
    out = []
    cell, miss, per = r[p], r.get(u"%s の欠けた条件" % p), r.get(u"%s の注入後の pointer の期" % p)
    if list(cell) != list(CELL_KEYS) or cell[u"結果"] not in RESULT_LABELS or not isinstance(cell[u"対応"], bool):
        return [u"%s の欄の形がおかしい" % p]
    if (cell[u"結果"] == TUNE.LABEL_UNMAPPED) != (cell[u"対応"] is False):
        out.append(u"%s の欄の対応と結果が合わない" % p)
    if cell[u"対応"] is False and (cell[u"state"] is not None or cell[u"reason"] is not None):
        out.append(u"%s の欄が対応なしなのに state がある" % p)
    if cell[u"対応"] is True and cell[u"state"] not in PB.STATES:
        out.append(u"%s の欄の state が 4 つの語でない" % p)
    if cell[u"結果"] == TUNE.LABEL_PASS and cell[u"state"] != G:
        out.append(u"%s の欄の通したが GROUNDED でない" % p)
    if per not in PERIODS5:
        out.append(u"%s の注入後の pointer の期が語でない" % p)
    if not isinstance(miss, list) or any(m not in CONDS + (NO_BASE,) for m in miss):
        out.append(u"%s の欠けた条件が語の列でない" % p)
    elif cell[u"対応"] is True and miss:
        out.append(u"%s の欄が対応ありなのに欠けた条件がある" % p)
    elif cell[u"対応"] is False and not miss:
        out.append(u"%s の欄が対応なしなのに欠けた条件が空" % p)
    if miss == [NO_BASE] and (p != PB.NEW or per != u"なし"):
        out.append(u"%s: 土台なしは P32E の土台に対応が付かない行だけ・期は なし" % p)
    if COND_A_NAME in (miss or []) and per != u"なし":
        out.append(u"%s: (ア)が欠けているのに期が なし でない" % p)
    return out


COND_A_NAME = CONDS[0]


def row_problems(r, seen):
    out = []
    if list(r) != list(ROW_KEYS):
        return [u"行の欄の並びが違う"]
    if r[u"型"] != PB.T9:
        out.append(u"型が T9_PRIOR_TO_CURRENT でない")
    if r[u"id"] in seen:
        out.append(u"同じ注入の id が 2 回ある")
    seen.add(r[u"id"])
    if not r[u"id"].startswith(u"%s_%s_%s-T9-" % (r["docID"], r["form"], r["model"])):
        out.append(u"id が本の名前 + T9 の形でない")
    for key in (LINK_KEY, u"round-trip", u"読み直し", u"engine の手がかり", u"窓の手がかり", u"文に前期の語"):
        if not isinstance(r.get(key), bool):
            out.append(u"行の %s が真偽でない" % key)
    if r[u"形"] not in SHAPES:
        out.append(u"行の形が語でない")
    if r[u"基準の pointer の期"] not in PS.PERIODS:
        out.append(u"基準の pointer の期が語でない")
    for p in PB.PROFILES:
        out += cell_problems(r, p)
    if r[LINK_KEY] is False and norm(r["P32E"]) != UNMAPPED_CELL:
        out.append(u"P32E の土台に対応が無い行の P32E の欄が対応なしでない")
    if r[LINK_KEY] is True and r["P32E"][u"対応"] is False and r[u"P32E の欠けた条件"] == [NO_BASE]:
        out.append(u"P32E の土台に対応があるのに 土台なし")
    if r["P30E"][u"対応"] is False and r["P30E"][u"結果"] != TUNE.LABEL_UNMAPPED:
        out.append(u"P30E の欄の対応と結果が合わない")
    return out


def inject_problems(rec, t9_rows, full):
    out = []
    rows = rec[u"行"]
    seen = set()
    cnt = collections.Counter()
    for r in rows:
        try:
            out += row_problems(r, seen)
        except Exception as e:                               # noqa: BLE001
            out.append(u"inject: 行を検査できない(%s)" % type(e).__name__)
            continue
        cnt[(r["docID"], r["form"], r["model"])] += 1
    if any(n > RUN.INJECT_CAP for n in cnt.values()):
        out.append(u"inject: 1 本あたりの上限 %d を超えている" % RUN.INJECT_CAP)
    if rec[u"注入の行の数"] != len(rows):
        out.append(u"inject: 注入の行の数が行の数と違う")
    try:
        if norm(PB.inject_summary(rows)) != rec[u"集計"]:
            out.append(u"inject: 集計が行から作り直した値と違う")
        if norm(PB.inject_columns(rows, t9_rows)) != rec[u"E の欄"]:
            out.append(u"inject: E の欄が行と T9 の第 2 便の記録から数え直した値と違う")
    except Exception as e:                                   # noqa: BLE001
        out.append(u"inject: 集計・E の欄を作れない(%s)" % type(e).__name__)
    if rec[u"型"].get(u"土台") != BASE_WORD_PIN or PS.BASE_WORD != BASE_WORD_PIN or rec[u"型"].get(u"site") != SITE_WORD_PIN or PS.SITE_WORD != SITE_WORD_PIN:
        out.append(u"inject: 型の 土台・site の字が留めた字でない")
    sw = rec.get(u"切り替え") or {}
    if sw.get(u"名前") != PI.FLAG or sw.get(u"配線の問題") != [] or sw.get(u"inject の中の値") is not True or sw.get(u"出たあとの値") is not False:
        out.append(u"inject: 切り替えの欄が違う")
    if full:
        t9ids = set(r[u"id"] for r in t9_rows)
        if set(r[u"id"] for r in rows) - t9ids:
            out.append(u"inject: T9 の第 2 便の記録に無い id がある")
        names = [b[u"name"] for src in PB.SOURCES.values() for b in jload(src["claims"])[u"本"] if not b.get(u"欠け")]
        if list(rec[u"本ごとの数え"]) != names:
            out.append(u"inject: 本ごとの数えの本が 200 本(前の便の claims の並び)でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(PI.GEN.caches_snapshot(PI.caches_all())):
            out.append(u"inject: cache の件数か名前が記録の前と違う")
    return out


def record_problems(R, full=True):
    u"""記録 3 つの検査(禁止欄・鍵・script の sha256・engine の指紋・cache・再計算)。問題の列。R = {"moves", "regress97", "inject", "t9"}。"""
    out = []

    def safe(label, fn, *a):
        try:
            return fn(*a)
        except Exception as e:                               # noqa: BLE001  壊れた記録は検査できない = 赤(例外で落とさず問題に数える)
            return [u"%s: 検査できない(%s)" % (label, type(e).__name__)]
    for k in REC_REL:
        out += safe(k, clean_problems, k, R[k])
        out += safe(k, header_problems, k, R[k], full)
    out += safe("moves", moves_problems, R["moves"], full)
    out += safe("regress97", regress97_problems, R["regress97"], full)
    out += safe("inject", inject_problems, R["inject"], R["t9"][u"行"], full)
    return out


def judge_problems(R, seal):
    u"""判定の関数が記録から作り直せるか(壊れた記録は赤)。"""
    try:
        J = PB.build_E(R, seal)
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"E"]) != list(SG.PRED_IDS) or list(J[u"K"]) != list(SG.K_IDS):
        out.append(u"判定の行が E-1〜E-10・K-1〜K-5 でない")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R, seal):
    J = PB.build_E(R, seal)
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != PB.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("judge") != PB.render_judge(J, seal).split(u"\n"):
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
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, list(ENGINE_FILES), others)


# ================================================================ 小さい標本の記録 3 つ + T9 の第 2 便の記録(通信しない・cache を読まない)
ITEMS = [dict(docID="DOC1", form="F1", model="m1", writer="W1", sha256="0" * 64), dict(docID="DOC2", form="F5", model="m2", writer="W2", sha256="1" * 64)]


def sample_header(k):
    _s, e = engine_commit_full()
    cache = collections.OrderedDict([("edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": "2" * 64})])
    h = collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"封の追記の commit", ADDENDUM_COMMIT_SHORT), (u"step", u"標本"), (u"HEAD の commit", "3" * 40), (u"engine の commit", e),
        (u"この script の sha256", sha256_rel(SCRIPT_REL)),
        (u"前の便の script の sha256", collections.OrderedDict((rel, sha256_rel(rel)) for rel in PREV_SCRIPT_RELS)),
        (u"入力の記録の sha256", collections.OrderedDict((rel, sha256_rel(rel)) for rel in input_rels(k))),
        (u"engine の指紋", dict(engine_fingerprint_at_commit(), adapter_xbrl_py_files=16, core_py_files=4, git_commit="3" * 40)),
        (u"lib の指紋", collections.OrderedDict((rel, sha256_rel(rel)) for rel in LIB_RELS)),
        (u"profile", list(PB.NOW_PROFILES) if k == "regress97" else list(PB.PROFILES)),
        (u"cache の前後", collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)])), (u"範囲", u"標本")])
    return h


def ent(si, pos, sa, sb, pa, pb, label=None, existing=EXISTING, nopf=False):
    return [u"num", si, pos, sa, sb, pa, pb, label, existing if label is not None or existing == NEWROW else EXISTING, nopf]


def mk_book(src, name, item, ents, n_old=40, g_old=10, reason_only=0, same_keys=True, oks=(True, True), idok=True):
    lost = sum(1 for x in ents if x[3] == G and x[4] != G)
    gained = sum(1 for x in ents if x[3] != G and x[4] == G)
    head = collections.OrderedDict([(u"name", name), (u"docID", item[u"docID"]), (u"form", item[u"form"]), (u"model", item[u"model"]), (u"writer", item[u"writer"]),
                                    (u"材料", src), (u"文の sha256", item[u"sha256"])])
    head[u"対応"] = collections.OrderedDict([("P30E", oks[0]), ("P32E", oks[1])])
    head[u"数の claim の数"] = collections.OrderedDict([("P30E", n_old), ("P32E", n_old)])
    head[u"P30E と P32E で数の claim の鍵が同じ"] = same_keys
    head[u"P27 の鍵が一意"] = idok
    head[u"GROUNDED の数"] = collections.OrderedDict([("P30E", g_old), ("P32E", g_old + gained - lost)])
    head[u"動いた行"] = len(ents)
    head[u"state が変わった行"] = sum(1 for x in ents if x[3] != x[4])
    head[u"reason だけが違う行"] = reason_only
    head[u"動いた行の中身"] = ents
    return norm(head)


def sample_books():
    e1 = [ent(0, 5, G, V_, u"CurrentYear", u"Prior1Year", u"真"), ent(1, 5, P_, V_, u"なし", u"Prior1Year", u"偽"), ent(2, 4, P_, V_, u"なし", u"Prior1Year", None, NEWROW),
          ent(3, 4, V_, V_, u"CurrentYear", u"Prior1Year", u"真")]
    e2 = [ent(0, 3, G, V_, u"CurrentYear", u"CurrentYear", None, NEWROW, True), ent(4, 1, U_, P_, u"なし", u"なし", u"真"), ent(5, 2, V_, V_, u"CurrentYear", u"Prior2Year", None, NEWROW),
          ent(6, 1, G, P_, u"CurrentYear", u"なし", u"偽"),                                  # 監査の指摘 (i): VALUE_MISMATCH 以外へ向かう GROUNDED の喪失
          ent(7, 1, P_, G, u"なし", u"CurrentYear", u"偽")]                                   # 監査の指摘 (ii): 非 GROUNDED から GROUNDED になった行
    return [mk_book("aiforms", "DOC1_F1_m1", ITEMS[0], e1, reason_only=1), mk_book("f5", "DOC2_F5_m2", ITEMS[1], e2)]


def sample_moves():
    books = sample_books()
    rec = sample_header("moves")
    rec[u"本"] = books
    rec[u"集計"] = norm(PB.aggregate_moves(books))
    rec[u"限界"] = list(PB.MOVES_LIMITS)
    rec[u"key_leaks"] = []
    return norm(rec)


def st4(g, v, u, p):
    return collections.OrderedDict([("GROUNDED", g), ("VALUE_MISMATCH", v), ("UNVERIFIABLE", u), ("POINTER_NOT_FOUND", p)])


def mk_doc(d, n, ents, xr_extra=0, g_old=6, added=0, gone=0):
    lost = sum(1 for x in ents if x[4] == G and x[5] != G)
    gained = sum(1 for x in ents if x[4] != G and x[5] == G)
    claims = collections.OrderedDict((p, n) for p in PB.NOW_PROFILES)
    claims[PB.NEW] = n + added - gone
    shas = collections.OrderedDict((p, hashlib.sha256((d + p).encode()).hexdigest()) for p in PB.NOW_PROFILES)
    fours = collections.OrderedDict((p, st4(g_old, n - g_old, 0, 0)) for p in PB.NOW_PROFILES)
    g_new = g_old + gained - lost
    fours[PB.NEW] = st4(g_new, claims[PB.NEW] - g_new, 0, 0)
    xr = [[x[0], x[1], x[2], x[3], x[4], x[5], None, None, x[9]] for x in ents] + [[u"num", 90 + j, 1, 0, G, G, "r1", "r2", False] for j in range(xr_extra)]
    mv = collections.OrderedDict([(PB.PAIRS[0][0], collections.OrderedDict([(u"動いた既存の行", xr), (u"増えた行", added), (u"増えた行の state", st4(0, added, 0, 0)), (u"消えた行", gone)]))])
    return collections.OrderedDict([
        (u"docID", d), (u"標本", u"手元の 67"), (u"zip の sha256", "4" * 64), (u"claims", claims), (u"4 state", fours), (u"出力の sha256(engine の欄を除く)", shas),
        (u"前の便の記録の sha256", collections.OrderedDict((p, shas[p]) for p in PB.BASE_PROFILES)), (u"動いた行と増えた行", mv),
        (u"P32E の動いた行", ents), (u"reason だけが違う行", xr_extra)])


def sample_regress97():
    e2 = [[u"num", 0, 3, 0, G, V_, u"CurrentYear", u"Prior1Year", True, True, False], [u"num", 0, 9, 0, P_, V_, u"なし", u"Prior1Year", True, True, False],
          [u"num", 1, 4, 0, V_, V_, u"CurrentYear", u"Prior1Year", False, True, False], [u"text", 2, 2, 0, V_, V_, u"CurrentYear", u"CurrentYear", False, True, True],
          [u"num", 3, 6, 0, G, U_, u"CurrentYear", u"なし", True, True, False],                  # 監査の指摘 (i): VALUE_MISMATCH 以外へ向かう GROUNDED の喪失
          [u"num", 4, 2, 0, P_, G, u"なし", u"CurrentYear", True, True, False]]                  # 監査の指摘 (ii): 非 GROUNDED から GROUNDED になった行
    e1 = [[u"num", 0, 7, 0, V_, V_, u"CurrentYear", u"Prior1Year", False, True, False]]          # 監査の指摘 (iii): pointers だけが違う行だけを持つ書類
    docs = [mk_doc("DOC1", 10, e1), mk_doc("DOC2", 12, e2, xr_extra=1)]
    rec = sample_header("regress97")
    rec[u"範囲"] = u"標本"
    rec[u"E-1・E-8 engine の差分"] = norm(link_at_history())
    msg = PB.message_numbers(engine_message_at_history())
    rec[u"E-7・E-9 の写し"] = norm(collections.OrderedDict([(u"出どころ", u"engine の commit の message"), (u"engine の commit", engine_commit_full()[1]), ("E-7", msg["E-7"]), ("E-9", msg["E-9"])]))
    rec[u"集計"] = norm(PB.regress_block(docs))
    rec[u"書類"] = norm(docs)
    rec[u"限界"] = list(PB.REGRESS_LIMITS)
    rec[u"key_leaks"] = []
    return norm(rec)


def cell(res, state, reason=None):
    return collections.OrderedDict([(u"対応", True), (u"結果", res), (u"state", state), (u"reason", reason)])


PASS_C, ORIG_C, OTHER_C = cell(TUNE.LABEL_PASS, G), cell(TUNE.LABEL_NAMED_ORIGINAL, V_), cell(TUNE.LABEL_NAMED_OTHER, V_)
UNMAPPED_C = collections.OrderedDict(UNMAPPED_CELL)


def irow(item, n, cue, win, c30, c32, per30, per32, linked=True, miss30=(), miss32=(), shape=u"既存", rt=True, rr=True, word=True, base_p=u"Prior1Year"):
    name = u"%s_%s_%s" % (item["docID"], item["form"], item["model"])
    base = collections.OrderedDict([(u"docID", item["docID"]), (u"form", item["form"]), (u"model", item["model"]), (u"writer", item["writer"])])
    r = collections.OrderedDict(base)
    r[u"id"] = u"%s-T9-%02d" % (name, n)
    r[u"型"] = PB.T9
    r[u"形"] = shape
    r[u"基準の claim"] = u"N%03d" % n
    r[LINK_KEY] = linked
    r[u"round-trip"], r[u"読み直し"] = rt, rr
    r[u"engine の手がかり"], r[u"窓の手がかり"], r[u"文に前期の語"] = cue, win, word
    r[u"基準の pointer の期"] = base_p
    r["P30E"], r["P32E"] = c30, c32
    r[u"P30E の注入後の pointer の期"], r[u"P32E の注入後の pointer の期"] = per30, per32
    r[u"P30E の欠けた条件"], r[u"P32E の欠けた条件"] = list(miss30), list(miss32)
    return r


def sample_rows():
    return [irow(ITEMS[0], 1, True, True, PASS_C, ORIG_C, u"CurrentYear", u"Prior1Year"),
            irow(ITEMS[0], 2, True, True, PASS_C, PASS_C, u"CurrentYear", u"Prior1Year"),
            irow(ITEMS[0], 3, True, True, PASS_C, OTHER_C, u"CurrentYear", u"CurrentYear"),
            irow(ITEMS[1], 1, False, False, PASS_C, PASS_C, u"CurrentYear", u"CurrentYear"),
            irow(ITEMS[1], 2, False, False, ORIG_C, UNMAPPED_C, u"Prior1Year", u"なし", linked=False, miss32=[NO_BASE]),
            irow(ITEMS[1], 3, False, False, PASS_C, PASS_C, u"CurrentYear", u"Prior1Year")]       # 監査の指摘 (iv): state は同じで pointer の期だけ違う手がかり偽の行


def sample_t9_rows(rows):
    u"""T9 の第 2 便の記録の行(id と P30E の欄だけ使う)。3 本目の P30E は違う結果にして『同じ行』が 4 / 5 になるようにする。"""
    out = []
    for r in rows:
        t = collections.OrderedDict([(u"id", r[u"id"]), ("P30E", copy.deepcopy(r["P30E"]))])
        out.append(t)
    out[2]["P30E"] = copy.deepcopy(OTHER_C)
    return norm(out)


def sample_inject(t9_rows=None):
    rows = sample_rows()
    t9_rows = t9_rows if t9_rows is not None else sample_t9_rows(rows)
    per = collections.OrderedDict([("DOC1_F1_m1", collections.OrderedDict([(u"作れる site", 3), (u"土台 P30E が GROUNDED の site", 3), (u"cap を基準で絞る前に掛けた数", 3), (u"採った", 3)])),
                                   ("DOC2_F5_m2", collections.OrderedDict([(u"作れる site", 2), (u"土台 P30E が GROUNDED の site", 2), (u"cap を基準で絞る前に掛けた数", 2), (u"採った", 2)]))])
    rec = sample_header("inject")
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", PI.FLAG), (u"inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
    rec[u"型"] = collections.OrderedDict([(PB.T9, u"標本"), (u"土台", BASE_WORD_PIN), (u"site", SITE_WORD_PIN)])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"] = norm(PB.inject_summary(rows))
    rec[u"E の欄"] = norm(PB.inject_columns(rows, t9_rows))
    rec[u"限界"] = list(PB.INJECT_LIMITS)
    rec[u"key_leaks"] = []
    rec[u"行"] = rows
    return norm(rec)


def sample_records():
    inj = sample_inject()
    return collections.OrderedDict([("moves", sample_moves()), ("regress97", sample_regress97()), ("inject", inj), ("t9", {u"行": sample_t9_rows(sample_rows())})])


def sample_doc(R, seal):
    J = PB.build_E(R, seal)
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", PB.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start judge -->", PB.render_judge(J, seal), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"200 本の標本です。" + NOT_GATED, u""])


# ---------------------------------------------------------------- 判定の関数の入力(欄の集まり。通信しない)
def sample_cols(**ov):
    u"""``judge_from`` の入力(幅の真ん中の値)。ov = {名前: 値} で 1 つだけ替える。"""
    v = collections.OrderedDict([
        ("rec_ins", 24), ("rec_del", 0), ("voc_ins", 5), ("voc_del", 0), ("others", 0), ("byte", 97), ("docs", 97), ("profiles", len(PB.BASE_PROFILES)), ("same", 141), ("rows", 141), ("ids_same", True),
        ("lost97", 0), ("moved97", 19), ("mdocs", 5), ("moved200", 54), ("lost200", 1), ("lost_true", 1), ("pv", 16), ("cur", 0), ("vm", 128), ("other_g", 1), ("cue_off", 12), ("same_off", 12),
        ("pass_rate", 8.5), ("named", 99.2), ("e7_red", 16), ("e7_total", 16), ("e9_names", [u"axis3 test_9"]), ("e9_n", 1), ("e9_failed", 1), ("e9_ut", 1), ("m", 64), ("vm10", 18), ("prior", 18),
        ("cur10", 0), ("p2_10", 0)])
    v.update(ov)
    ns = collections.OrderedDict()
    if v["rec_ins"] is not None:
        ns[ENGINE_FILES[0]] = [v["rec_ins"], v["rec_del"]]
    if v["voc_ins"] is not None:
        ns[ENGINE_FILES[1]] = [v["voc_ins"], v["voc_del"]]
    for i in range(v["others"]):
        ns["adapters/xbrl/other%d.py" % i] = [1, 0]
    link = collections.OrderedDict([(u"numstat", ns), (u"直した file(M)", v["m"]), (u"新しい file(A)", 1), (u"engine の挿入の行数", 29)])
    cn = collections.OrderedDict((p, {u"byte が同じ書類": v["byte"], u"書類": v["docs"]}) for p in PB.BASE_PROFILES[:v["profiles"]])
    rg = collections.OrderedDict([
        (u"E-2 旗が偽の profile の byte 一致", cn),
        (u"E-3 P32E 対 P30E", collections.OrderedDict([(u"動いた行", v["moved97"]), (u"GROUNDED を失う行", v["lost97"]), (u"動いた書類", v["mdocs"])])),
        (u"E-10 VALUE_MISMATCH に動いた行の pointer の期", collections.OrderedDict([(u"行", v["vm10"]), ("CurrentYear", v["cur10"]), ("Prior1Year", v["prior"]), ("Prior2Year", v["p2_10"]), (u"他", 0), (u"なし", 0)]))])
    ij = collections.OrderedDict([
        (u"E-2 T9 の第 2 便の記録との照らし", collections.OrderedDict([(u"行の数", v["rows"]), (u"id の集合が T9 の第 2 便の記録と同じ", v["ids_same"]),
                                                             (u"P30E の結果と state が T9 の第 2 便の記録と同じ行", v["same"])])),
        (u"E-5 手がかり別の P32E", collections.OrderedDict([(u"手がかり真の行", v["rows"] - v["cue_off"]), (u"当期の fact に GROUNDED", v["cur"]), (u"前期の fact を名指して VALUE_MISMATCH", v["vm"]),
                                                       (u"別の fact に GROUNDED", v["other_g"]), (u"その他", 0), (u"手がかり偽の行", v["cue_off"]), (u"手がかり偽の行のうち P30E と同じ行", v["same_off"])])),
        (u"E-6 通した率と名指して原本", collections.OrderedDict([(u"通した率(P32E)", v["pass_rate"]), (u"名指して原本の割合", v["named"])]))])
    mv = collections.OrderedDict([
        (u"E-4 動いた行", v["moved200"]), (u"E-4 GROUNDED を失う行", {u"行": v["lost200"], u"札": {u"真": v["lost_true"]}}), (u"E-4 POINTER_NOT_FOUND → VALUE_MISMATCH", {u"行": v["pv"]})])
    e7 = None if v["e7_red"] is None else collections.OrderedDict([(u"変異の本数", v["e7_total"]), (u"赤", v["e7_red"]), (u"原文", u"x")])
    e9 = None if v["e9_n"] is None else collections.OrderedDict([(u"赤の試験", v["e9_names"]), (u"赤の本数", v["e9_n"]),
                                                              (u"pytest", {"failed": v["e9_failed"], "passed": 6802, "skipped": 35}), (u"unittest failures", v["e9_ut"]), (u"原文", u"x")])
    return collections.OrderedDict([("moves", mv), ("regress", rg), ("inject", ij), ("link", link), ("copy", {"E-7": e7, "E-9": e9})])


# ================================================================ (a) 封の字
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def _mutate_row(self, cid, old, new):
        P = PB.seal_pred_rows(self.seal)
        self.assertIn(old, P[cid][1], cid)
        head = "| %s | %s | %s" % (cid, P[cid][0], P[cid][1])
        self.assertIn(head, self.seal)
        mutated = self.seal.replace(head, "| %s | %s | %s" % (cid, P[cid][0], P[cid][1].replace(old, new, 1)), 1)
        self.assertNotEqual(mutated, self.seal)
        return mutated

    def test_a_2_a_changed_character_in_the_seal_turns_the_pin_red(self):
        for cid, old, new in (("E-1", "18〜28", "18〜29"), ("E-1", "4〜6", "4〜7"), ("E-1", "/ 0、4", "/ 1、4"), ("E-2", "97 / 97", "97 / 96"), ("E-2", "141 / 141", "141 / 140"),
                              ("E-3", "15〜25", "15〜26"), ("E-3", "3〜8", "3〜9"), ("E-3", "0 / 15", "1 / 15"), ("E-4", "45〜65", "45〜66"), ("E-4", "12〜20", "12〜21"),
                              ("E-4", "0〜2(0〜2)", "0〜3(0〜2)"), ("E-4", "(0〜2)", "(0〜3)"), ("E-5", "120〜129", "120〜128"), ("E-5", "0〜3", "0〜4"), ("E-5", "12 / 12", "12 / 11"),
                              ("E-6", "5〜12%", "5〜13%"), ("E-6", "90〜100%", "89〜100%"), ("E-7", "10 / 10", "10 / 9"), ("E-8", "40〜75", "40〜76"),
                              ("E-9", "test_9", "test_8"), ("E-9", "だけ、0", "だけ、1"), ("E-10", "17〜19", "17〜20"), ("E-10", "Prior1Year", "CurrentYear")):
            self.assertNotEqual([], bounds_problems(self._mutate_row(cid, old, new)), (cid, new))

    def test_a_3_the_thresholds_of_k1_to_k5_are_read_from_the_seal(self):
        b = PB.seal_bounds(self.seal)
        self.assertEqual(((97, 97, 141, 141), 0, 2, {u"当期の fact に GROUNDED": (0, 3), u"手がかり偽の行": 12}, {u"赤": 10, u"変異の本数": 10}),
                         (b["K-1"], b["K-2"], b["K-3"], dict(b["K-4"]), dict(b["K-5"])))
        for old, new in (("E-2 が 97 / 97 かつ 141 / 141", "E-2 が 97 / 97 かつ 141 / 140"), ("E-3 の GROUNDED を失う行 0", "E-3 の GROUNDED を失う行 1"), ("E-4 の GROUNDED を失う行 ≤ 2", "E-4 の GROUNDED を失う行 ≤ 3"),
                         ("GROUNDED 0〜3、かつ", "GROUNDED 0〜4、かつ"), ("手がかり偽の 12 行", "手がかり偽の 13 行"), ("E-7 が 10 / 10", "E-7 が 10 / 9")):
            self.assertIn(old, self.seal, old)
            self.assertNotEqual([], bounds_problems(self.seal.replace(old, new, 1)), new)

    def test_a_4_a_broken_seal_is_red_not_an_exception(self):
        self.assertNotEqual([], bounds_problems(self.seal.replace("## §4", "## 四", 1)))
        self.assertNotEqual([], bounds_problems(u""))


# ================================================================ (c) 判定
class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def J(self, **ov):
        return PB.judge_from(sample_cols(**ov), self.seal)

    def test_c_1_the_middle_of_every_range_is_a_hit_and_adoption_follows(self):
        J = self.J()
        for k, v in J[u"E"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        for k, v in J[u"K"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        self.assertTrue(J[u"採用"])
        self.assertEqual(list(SG.PRED_IDS), list(J[u"E"]))
        self.assertEqual(list(SG.K_IDS), list(J[u"K"]))

    def test_c_2_each_prediction_flips_at_the_seal_boundary(self):
        b = BOUNDS_PIN
        cases = [("rec_ins", "E-1", 18, 17), ("rec_ins", "E-1", 28, 29), ("rec_del", "E-1", 0, 1), ("voc_ins", "E-1", 4, 3), ("voc_ins", "E-1", 6, 7), ("voc_del", "E-1", 0, 1), ("others", "E-1", 0, 1),
                 ("byte", "E-2", 97, 96), ("docs", "E-2", 97, 98), ("profiles", "E-2", 9, 8), ("same", "E-2", 141, 140), ("rows", "E-2", 141, 142), ("ids_same", "E-2", True, False),
                 ("lost97", "E-3", 0, 1), ("moved97", "E-3", 15, 14), ("moved97", "E-3", 25, 26), ("mdocs", "E-3", 3, 2), ("mdocs", "E-3", 8, 9),
                 ("moved200", "E-4", 45, 44), ("moved200", "E-4", 65, 66), ("lost200", "E-4", 2, 3), ("lost_true", "E-4", 2, 3), ("pv", "E-4", 12, 11), ("pv", "E-4", 20, 21),
                 ("cur", "E-5", 0, 1), ("vm", "E-5", 120, 119), ("vm", "E-5", 129, 130), ("other_g", "E-5", 3, 4), ("cue_off", "E-5", 12, 13), ("same_off", "E-5", 12, 11),
                 ("pass_rate", "E-6", 5.0, 4.9), ("pass_rate", "E-6", 12.0, 12.1), ("named", "E-6", 90.0, 89.9), ("pass_rate", "E-6", 8.5, None), ("named", "E-6", 99.0, None),
                 ("e7_red", "E-7", 16, 15), ("e7_total", "E-7", 10, 9), ("e7_red", "E-7", 16, None),
                 ("e9_names", "E-9", [u"axis3 test_9"], [u"axis3 test_8"]), ("e9_failed", "E-9", 1, 2), ("e9_ut", "E-9", 1, 0), ("e9_n", "E-9", 1, None),
                 ("m", "E-8", 40, 39), ("m", "E-8", 75, 76),
                 ("vm10", "E-10", 17, 16), ("vm10", "E-10", 19, 20)]
        for name, cid, inside, outside in cases:
            ov_in, ov_out = {name: inside}, {name: outside}
            if name in ("vm10",):                                                       # 行の数を変えるときは Prior1Year の数も合わせる(全部 Prior1Year を保つ)
                ov_in["prior"], ov_out["prior"] = inside, outside
            if name == "e7_total":
                ov_in["e7_red"], ov_out["e7_red"] = inside, outside
            self.assertEqual(HIT, self.J(**ov_in)[u"E"][cid][u"判定"], (name, inside))
            self.assertEqual(MISS, self.J(**ov_out)[u"E"][cid][u"判定"], (name, outside))
        self.assertEqual(MISS, self.J(cur10=1, prior=17)[u"E"]["E-10"][u"判定"])               # CurrentYear を名指す行が 1 つ
        self.assertEqual(MISS, self.J(p2_10=1, prior=17)[u"E"]["E-10"][u"判定"])               # Prior2Year を名指す行が 1 つ(追記 1 の 4。外れとして残す)
        self.assertEqual(MISS, self.J(others=1)[u"E"]["E-1"][u"判定"])
        self.assertEqual(MISS, self.J(rec_ins=None)[u"E"]["E-1"][u"判定"])                      # recipes の行が無い
        self.assertEqual(b["E-8"], (40, 75))

    def test_c_3_the_adoption_follows_k1_to_k5(self):
        self.assertFalse(self.J(byte=96)[u"採用"])                       # K-1
        self.assertEqual(MISS, self.J(byte=96)[u"K"]["K-1"][u"判定"])
        self.assertFalse(self.J(same=140)[u"採用"])
        self.assertFalse(self.J(lost97=1)[u"採用"])                      # K-2
        self.assertEqual(MISS, self.J(lost97=1)[u"K"]["K-2"][u"判定"])
        self.assertFalse(self.J(lost200=3)[u"採用"])                     # K-3
        self.assertTrue(self.J(lost200=2)[u"採用"])
        self.assertEqual(MISS, self.J(cur=1)[u"E"]["E-5"][u"判定"])      # K-4 の幅は 0〜3(E-5 の 0 より広い)
        self.assertTrue(self.J(cur=3)[u"採用"])
        self.assertFalse(self.J(cur=4)[u"採用"])                         # K-4
        self.assertEqual(MISS, self.J(cur=4)[u"K"]["K-4"][u"判定"])
        self.assertFalse(self.J(same_off=11)[u"採用"])
        self.assertFalse(self.J(e7_red=15)[u"採用"])                     # K-5
        self.assertFalse(self.J(e9_failed=2)[u"採用"])
        self.assertEqual(MISS, self.J(e9_failed=2)[u"K"]["K-5"][u"判定"])

    def test_c_4_k3_k4_and_k5_use_the_seal_k_thresholds_not_the_prediction_ranges(self):
        J = self.J(moved200=70)                                          # E-4 の幅(45〜65)の外。K-3 は GROUNDED を失う行だけを見る
        self.assertEqual(MISS, J[u"E"]["E-4"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-3"][u"判定"])
        J = self.J(vm=100)                                               # E-5 の幅(120〜129)の外。K-4 は 当期に GROUNDED と手がかり偽だけ
        self.assertEqual(MISS, J[u"E"]["E-5"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-4"][u"判定"])
        J = self.J(moved97=40)                                           # E-3 の幅の外。K-2 は GROUNDED を失う行だけ
        self.assertEqual(MISS, J[u"E"]["E-3"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-2"][u"判定"])
        J = self.J(pass_rate=20.0)                                       # E-6 の幅の外でも K には効かない
        self.assertEqual(MISS, J[u"E"]["E-6"][u"判定"])
        self.assertTrue(J[u"採用"])

    def test_c_4b_e7_and_e9_are_read_from_the_copied_message_numbers(self):
        J = self.J()
        self.assertEqual({u"赤": 10, u"変異の本数": 10, u"写した全部赤の本数": 16}, dict(J[u"E"]["E-7"][u"値"]))
        self.assertEqual({u"赤の試験": [u"axis3 test_9"], u"赤の本数": 1, u"ほかの赤": 0}, dict(J[u"E"]["E-9"][u"値"]))
        J = self.J(e9_failed=3, e9_ut=1)                                 # pytest の failed が名指しの本数より多い = ほかの赤が 2
        self.assertEqual(2, J[u"E"]["E-9"][u"値"][u"ほかの赤"])
        self.assertEqual(MISS, J[u"E"]["E-9"][u"判定"])
        J = self.J(e7_red=None)
        self.assertEqual(MISS, J[u"E"]["E-7"][u"判定"])

    def test_c_5_the_judgment_moves_with_the_columns_and_with_the_seal(self):
        base = norm(self.J())
        self.assertNotEqual(base, norm(self.J(moved200=50)))
        mutated_seal = self.seal.replace("45〜65", "45〜49", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertEqual(MISS, PB.judge_from(sample_cols(), mutated_seal)[u"E"]["E-4"][u"判定"])

    def test_c_6_a_broken_record_is_red_not_an_exception(self):
        R = sample_records()
        del R["moves"][u"本"][0][u"動いた行の中身"]
        self.assertNotEqual([], judge_problems(R, self.seal))
        self.assertEqual([], judge_problems(sample_records(), self.seal))
        R2 = sample_records()
        R2["t9"] = {}
        self.assertNotEqual([], judge_problems(R2, self.seal))


def leaves(o, path=()):
    u"""数の葉(bool を除く int / float)の path。"""
    if isinstance(o, dict):
        for k, v in o.items():
            for x in leaves(v, path + (k,)):
                yield x
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        yield path


def get_path(o, path):
    for k in path:
        o = o[k]
    return o


def set_path(o, path, v):
    for k in path[:-1]:
        o = o[k]
    o[path[-1]] = v


# ================================================================ (g) 小さい標本の記録 3 つと文書の変異
class SampleFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.R = sample_records()

    def test_g_0_the_sample_is_green(self):
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=False))
        self.assertEqual([], judge_problems(self.R, self.seal))
        doc = sample_doc(self.R, self.seal)
        self.assertEqual([], doc_problems(doc, self.R, self.seal))

    def test_g_1_the_sample_exercises_every_category_with_known_answers(self):
        A = norm(PB.aggregate_moves(self.R["moves"][u"本"])[u"全体"])
        lab = lambda a, b, c, d, e: {u"真": a, u"偽": b, u"判定不能": c, NO_LABEL: d, NEWROW: e}      # noqa: E731
        self.assertEqual((9, 7, 2), (A[u"E-4 動いた行"], A[u"state が変わった行"], A[u"state は同じで pointer の期だけ変わった行"]))
        self.assertEqual({u"GROUNDED → VALUE_MISMATCH": 2, u"POINTER_NOT_FOUND → VALUE_MISMATCH": 2, u"UNVERIFIABLE → POINTER_NOT_FOUND": 1, u"GROUNDED → POINTER_NOT_FOUND": 1, u"POINTER_NOT_FOUND → GROUNDED": 1}, A[u"向き別"])
        self.assertEqual({u"行": 3, u"札": lab(1, 1, 0, 0, 1)}, A[u"E-4 GROUNDED を失う行"])           # VALUE_MISMATCH 行き 2 + POINTER_NOT_FOUND 行き 1
        self.assertEqual({u"行": 1, u"札": lab(0, 1, 0, 0, 0)}, A[u"GROUNDED になった行"])
        self.assertEqual({u"行": 2, u"札": lab(0, 1, 0, 0, 1)}, A[u"E-4 POINTER_NOT_FOUND → VALUE_MISMATCH"])
        self.assertEqual({u"行": 2, u"札": lab(1, 0, 0, 0, 1), u"期の変わり方": {u"CurrentYear → Prior1Year": 1, u"CurrentYear → Prior2Year": 1}}, A[u"VALUE_MISMATCH のまま pointer の期が変わる行"])
        self.assertEqual({u"行": 1, u"札": lab(1, 0, 0, 0, 0)}, A[u"UNVERIFIABLE → POINTER_NOT_FOUND"])
        self.assertEqual(lab(3, 3, 0, 0, 3), A[u"動いた行の札"])
        self.assertEqual((1, 1, 1), (A[u"後の期が Prior2Year の動いた行"], A[u"前期の fact が無い要素の動いた行"], A[u"reason だけが違う行"]))
        self.assertEqual({"P30E": 20, "P32E": 18, u"差": -2}, A[u"GROUNDED の数"])
        T = norm(PB.regress_block(self.R["regress97"][u"書類"]))
        e3 = T[u"E-3 P32E 対 P30E"]
        # GROUNDED を失う 2 = VALUE_MISMATCH 行き 1 + UNVERIFIABLE 行き 1。GROUNDED になった 1 = POINTER_NOT_FOUND から。動いた書類 1 = state が変わった行を持つ書類(DOC1 は pointers だけの行を持つ)
        self.assertEqual((4, 2, 1, 1), (e3[u"動いた行"], e3[u"GROUNDED を失う行"], e3[u"GROUNDED になった行"], e3[u"動いた書類"]))
        self.assertEqual((7, 3, 2, 1, 8), (e3[u"state か pointers が違う行"], e3[u"pointers だけが違う行"], e3[u"state か pointers が違う行のある書類"], e3[u"reason だけが違う行"],
                                          e3[u"XR の定義(state・reason・pointers のどれか)の動いた行"]))
        self.assertEqual({u"行": 2, "CurrentYear": 0, "Prior1Year": 2, "Prior2Year": 0, u"他": 0, u"なし": 0}, T[u"E-10 VALUE_MISMATCH に動いた行の pointer の期"])
        self.assertEqual({u"行": 3, u"期の変わり方": {u"CurrentYear → Prior1Year": 2, u"CurrentYear → CurrentYear": 1}}, T[u"参考 VALUE_MISMATCH のまま pointer の期が動いた行"])
        self.assertEqual({u"動いた行(state か pointers)": 1, u"うち state が変わった行": 0, u"うち VALUE_MISMATCH に動いた行": 0, u"うち GROUNDED を失う行": 0}, T[u"前期の fact が無い要素の動いた行"])
        self.assertEqual(set(PB.BASE_PROFILES), set(T[u"E-2 旗が偽の profile の byte 一致"]))
        cols = norm(PB.inject_columns(self.R["inject"][u"行"], self.R["t9"][u"行"]))
        self.assertEqual({u"行の数": 6, u"T9 の第 2 便の記録の行の数": 6, u"id の集合が T9 の第 2 便の記録と同じ": True, u"P30E の結果と state が T9 の第 2 便の記録と同じ行": 5}, cols[u"E-2 T9 の第 2 便の記録との照らし"])
        self.assertEqual({u"手がかり真の行": 3, u"当期の fact に GROUNDED": 0, u"前期の fact を名指して VALUE_MISMATCH": 1, u"別の fact に GROUNDED": 1, u"その他": 1,
                          u"手がかり偽の行": 3, u"手がかり偽の行のうち P30E と同じ行": 1}, cols[u"E-5 手がかり別の P32E"])            # 同じ行 1 = 結果も state も期も同じ。6 本目は結果と state は同じで期だけ違う(監査の指摘 (iv))
        self.assertEqual({u"通した率(P32E)": 50.0, u"通した行": 3, u"注入の行": 6, u"止めた行": 2, u"うち名指して原本": 1, u"名指して原本の割合": 50.0}, cols[u"E-6 通した率と名指して原本"])

    def _red(self, mutate, full=False):
        R = copy.deepcopy(self.R)
        mutate(R)
        self.assertNotEqual([], record_problems(R, full=full))

    def test_g_2_one_number_in_a_record_turns_it_red(self):
        self._red(lambda R: R["moves"][u"本"][0][u"GROUNDED の数"].__setitem__("P32E", 99))
        self._red(lambda R: R["moves"][u"本"][0].__setitem__(u"動いた行", 9))
        self._red(lambda R: R["moves"][u"本"][0].__setitem__(u"state が変わった行", 0))
        self._red(lambda R: R["moves"][u"集計"][u"全体"][u"E-4 動いた行"].__class__ and R["moves"][u"集計"][u"全体"].__setitem__(u"E-4 動いた行", 99))
        self._red(lambda R: R["moves"][u"集計"][u"全体"][u"E-4 GROUNDED を失う行"][u"札"].__setitem__(u"真", 0))
        self._red(lambda R: R["moves"][u"本"][1][u"動いた行の中身"][0].__setitem__(7, u"真"))               # 新しい行に札
        self._red(lambda R: R["moves"][u"本"][1][u"動いた行の中身"][0].__setitem__(9, False))             # 集計の前期の fact が無い要素の数と合わない
        self._red(lambda R: R["moves"][u"本"][0].__setitem__(u"対応", {"P30E": True, "P32E": False}))
        self._red(lambda R: R["regress97"][u"書類"][1][u"P32E の動いた行"][0].__setitem__(5, G))
        self._red(lambda R: R["regress97"][u"書類"][1][u"P32E の動いた行"][0].__setitem__(8, False))
        self._red(lambda R: R["regress97"][u"書類"][1][u"動いた行と増えた行"]["P32E 対 P30E"].__setitem__(u"増えた行", 5))
        self._red(lambda R: R["regress97"][u"書類"][1].__setitem__(u"reason だけが違う行", 0))
        self._red(lambda R: R["regress97"][u"集計"][u"E-3 P32E 対 P30E"].__setitem__(u"GROUNDED を失う行", 0))
        self._red(lambda R: R["regress97"][u"書類"][0][u"出力の sha256(engine の欄を除く)"].__setitem__("P28E", "5" * 64))
        self._red(lambda R: R["regress97"][u"E-1・E-8 engine の差分"].__setitem__(u"numstat", "x"))
        self._red(lambda R: R["inject"][u"行"][0]["P32E"].__setitem__(u"結果", TUNE.LABEL_PASS))
        self._red(lambda R: R["inject"][u"行"][0].__setitem__(u"engine の手がかり", False))
        self._red(lambda R: R["inject"][u"行"][0].__setitem__(u"P32E の注入後の pointer の期", u"Prior2Year"))
        self._red(lambda R: R["inject"][u"集計"]["P32E"][u"注入の行"].__class__ and R["inject"][u"集計"]["P32E"].__setitem__(u"注入の行", 9))
        self._red(lambda R: R["inject"].__setitem__(u"注入の行の数", 9))
        self._red(lambda R: R["inject"][u"型"].__setitem__(u"土台", u"無改変の文で P29E が GROUNDED の claim"))

    def test_g_2b_every_numeric_leaf_of_the_stored_aggregates_is_recomputed(self):
        u"""記録の集計・E の欄の数の葉を 1 つずつ 0(元が 0 なら 1)に替えると赤(0 に固定した欄が黙らない)。"""
        n = 0
        for k, root in (("moves", (u"集計",)), ("regress97", (u"集計",)), ("inject", (u"集計",)), ("inject", (u"E の欄",))):
            for path in list(leaves(get_path(self.R[k], root))):
                full_path = root + path
                old = get_path(self.R[k], full_path)

                def mutate(R, k=k, full_path=full_path, old=old):
                    set_path(R[k], full_path, 0 if old != 0 else 1)
                self._red(mutate)
                n += 1
        self.assertGreaterEqual(n, 150)

    def test_g_2c_a_consistently_edited_book_still_breaks_the_invariants(self):
        u"""本を直してから集計も作り直しても(集計との食い違いでは見つからない)、本の中の欄の間の関係で赤になる。"""
        def reagg(R):
            R["moves"][u"集計"] = norm(PB.aggregate_moves(R["moves"][u"本"]))
        for mutate in (lambda b: b[u"GROUNDED の数"].__setitem__("P32E", 99), lambda b: b[u"GROUNDED の数"].__setitem__("P30E", 99), lambda b: b[u"GROUNDED の数"].__setitem__("P32E", 12),
                       lambda b: b.__setitem__(u"動いた行", 1), lambda b: b.__setitem__(u"state が変わった行", 9),
                       lambda b: b[u"動いた行の中身"][0].__setitem__(4, b[u"動いた行の中身"][0][3]), lambda b: b[u"動いた行の中身"][0].__setitem__(8, NEWROW),
                       lambda b: b[u"動いた行の中身"][0].__setitem__(7, u"偽っぽい"), lambda b: b[u"動いた行の中身"][0].__setitem__(5, u"Prior3Year"),
                       lambda b: b[u"動いた行の中身"][0].__setitem__(0, u"text"), lambda b: b[u"動いた行の中身"].append(list(b[u"動いた行の中身"][0])),
                       lambda b: b[u"動いた行の中身"][1].__setitem__(6, u"Prior1Year") or b[u"動いた行の中身"][1].__setitem__(9, True),      # 前期の fact が無いのに期が Prior1Year
                       lambda b: b[u"数の claim の数"].__setitem__("P32E", 99), lambda b: b[u"対応"].__setitem__("P32E", False),
                       lambda b: b.__setitem__(u"P27 の鍵が一意", u"はい"), lambda b: b.__setitem__(u"reason だけが違う行", -1)):
            R = copy.deepcopy(self.R)
            mutate(R["moves"][u"本"][0])
            try:
                reagg(R)
            except Exception:                                   # noqa: BLE001  集計を作れない形も赤(record_problems が例外を問題に数える)
                pass
            self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        reagg(R)
        self.assertEqual([], record_problems(R, full=False))

    def test_g_2d_a_consistently_edited_row_still_breaks_the_invariants(self):
        def reagg(R):
            R["inject"][u"集計"] = norm(PB.inject_summary(R["inject"][u"行"]))
            R["inject"][u"E の欄"] = norm(PB.inject_columns(R["inject"][u"行"], R["t9"][u"行"]))
        for mutate in (lambda r: r["P32E"].__setitem__(u"結果", u"通した率"), lambda r: r["P32E"].__setitem__(u"state", u"GROUNDED?"), lambda r: r["P30E"].__setitem__(u"対応", False),
                       lambda r: r.__setitem__(u"P32E の注入後の pointer の期", u"Prior3Year"), lambda r: r.__setitem__(u"P30E の欠けた条件", [u"ア id の claim が在る"]),
                       lambda r: r.__setitem__(u"P32E の欠けた条件", [u"土台なし"]), lambda r: r.__setitem__(LINK_KEY, u"はい"), lambda r: r.__setitem__(u"型", u"T8_REL"),
                       lambda r: r.__setitem__(u"id", u"X-T9-01"), lambda r: r.__setitem__(u"形", u"全部"), lambda r: r.__setitem__(u"engine の手がかり", u"真"),
                       lambda r: r.__setitem__(u"基準の pointer の期", u"Prior9Year"), lambda r: r.pop(u"窓の手がかり"), lambda r: r.__setitem__(u"窓の手がかり", None)):
            R = copy.deepcopy(self.R)
            mutate(R["inject"][u"行"][0])
            try:
                reagg(R)
            except Exception:                                   # noqa: BLE001
                pass
            self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        R["inject"][u"行"][4][LINK_KEY] = True                                  # 土台に対応があるのに P32E の欄が対応なし・欠けた条件が 土台なし
        reagg(R)
        self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        reagg(R)
        self.assertEqual([], record_problems(R, full=False))

    def test_g_2e_a_column_changes_exactly_where_its_field_feeds(self):
        u"""行の欄 1 つを変えると、それを餌にする欄だけが動く(窓の手がかりは E-5 を動かさず 参考 だけ。engine の手がかりは E-5 を動かす)。"""
        rows = self.R["inject"][u"行"]
        t9 = self.R["t9"][u"行"]
        base = norm(PB.inject_columns(rows, t9))
        r2 = copy.deepcopy(rows)
        r2[0][u"窓の手がかり"] = False
        c = norm(PB.inject_columns(r2, t9))
        self.assertEqual(base[u"E-5 手がかり別の P32E"], c[u"E-5 手がかり別の P32E"])
        self.assertEqual(base[u"E-6 通した率と名指して原本"], c[u"E-6 通した率と名指して原本"])
        self.assertEqual(base[u"参考"][u"窓の手がかり真の行"] - 1, c[u"参考"][u"窓の手がかり真の行"])
        self.assertEqual(base[u"参考"][u"engine の手がかりと窓の手がかりが違う行"] + 1, c[u"参考"][u"engine の手がかりと窓の手がかりが違う行"])
        r3 = copy.deepcopy(rows)
        r3[0][u"engine の手がかり"] = False
        c = norm(PB.inject_columns(r3, t9))
        self.assertEqual(base[u"E-5 手がかり別の P32E"][u"手がかり真の行"] - 1, c[u"E-5 手がかり別の P32E"][u"手がかり真の行"])
        self.assertEqual(base[u"E-5 手がかり別の P32E"][u"手がかり偽の行"] + 1, c[u"E-5 手がかり別の P32E"][u"手がかり偽の行"])
        self.assertEqual(base[u"E-6 通した率と名指して原本"], c[u"E-6 通した率と名指して原本"])
        r4 = copy.deepcopy(rows)
        r4[0]["P32E"] = copy.deepcopy(PASS_C)
        c = norm(PB.inject_columns(r4, t9))
        self.assertEqual(4, c[u"E-6 通した率と名指して原本"][u"通した行"])
        self.assertEqual(1, c[u"E-6 通した率と名指して原本"][u"止めた行"])
        self.assertEqual(0, c[u"E-6 通した率と名指して原本"][u"うち名指して原本"])
        self.assertEqual(base[u"E-2 T9 の第 2 便の記録との照らし"], c[u"E-2 T9 の第 2 便の記録との照らし"])                   # P32E の欄を変えても E-2 は動かない
        r5 = copy.deepcopy(rows)
        r5[0]["P30E"] = copy.deepcopy(ORIG_C)
        c = norm(PB.inject_columns(r5, t9))
        self.assertEqual(4, c[u"E-2 T9 の第 2 便の記録との照らし"][u"P30E の結果と state が T9 の第 2 便の記録と同じ行"])           # P30E の欄を変えると E-2 が動く
        self.assertEqual(base[u"E-6 通した率と名指して原本"], c[u"E-6 通した率と名指して原本"])
        r6 = copy.deepcopy(rows)
        r6[1][u"P32E の注入後の pointer の期"] = u"CurrentYear"                      # 通した(GROUNDED)の期が Prior1Year → CurrentYear = 当期の fact に GROUNDED
        c = norm(PB.inject_columns(r6, t9))
        self.assertEqual((1, 0), (c[u"E-5 手がかり別の P32E"][u"当期の fact に GROUNDED"], c[u"E-5 手がかり別の P32E"][u"別の fact に GROUNDED"]))

    def test_g_3_a_forbidden_key_or_a_key_or_a_company_name_or_a_pointer_text_turns_it_red(self):
        for key in (u"span", u"value", u"recomputed", u"文", u"sentence", u"数", u"理由", u"pointers", u"pointer", u"要素", u"element"):
            self._red(lambda R, key=key: R["moves"][u"本"][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["inject"][u"行"][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["regress97"][u"書類"][0].__setitem__(key, 1))
        self._red(lambda R: R["regress97"].__setitem__(u"メモ", u"株式会社テスト"))
        self._red(lambda R: R["moves"].__setitem__(u"メモ", u"sk-" + u"a" * 20))
        self._red(lambda R: R["regress97"].__setitem__(u"key_leaks", [u"鍵の形"]))
        self._red(lambda R: R["moves"].__setitem__(u"メモ", u"xbrl:jppfs_cor:NetSales@CurrentYearDuration"))
        self._red(lambda R: R["inject"][u"行"][0].__setitem__(u"メモ", u"jppfs_cor:NetSales"))
        self._red(lambda R: R["regress97"][u"書類"][0].__setitem__(u"メモ", u"@Prior1YearDuration"))

    def test_g_4_one_character_of_the_fingerprint_or_the_script_sha_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][u"engine の指紋"].__setitem__("adapter_xbrl_py_sha256", R[k][u"engine の指紋"]["adapter_xbrl_py_sha256"][:-1] + ("0" if R[k][u"engine の指紋"]["adapter_xbrl_py_sha256"][-1] != "0" else "1")))
            self._red(lambda R, k=k: R[k][u"engine の指紋"].__setitem__("core_py_sha256", "f" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"この script の sha256", "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"封の commit", u"0000000"))
            self._red(lambda R, k=k: R[k].__setitem__(u"封の追記の commit", u"0000000"))
            self._red(lambda R, k=k: R[k].__setitem__(u"engine の commit", "0" * 40))
            self._red(lambda R, k=k: R[k].__setitem__(u"HEAD の commit", u"abc"))
            self._red(lambda R, k=k: R[k][u"lib の指紋"].__setitem__(LIB_RELS[0], "e" * 64))
            self._red(lambda R, k=k: R[k][u"前の便の script の sha256"].__setitem__(PREV_SCRIPT_RELS[0], "e" * 64))
            self._red(lambda R, k=k: R[k][u"入力の記録の sha256"].__setitem__(list(R[k][u"入力の記録の sha256"])[0], "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"seal", u"docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md"))
            self._red(lambda R, k=k: R[k].__setitem__(u"profile", [u"P29E", u"P30E"]))
            self._red(lambda R, k=k: R[k][u"限界"].pop())
            self._red(lambda R, k=k: R[k][u"限界"].__setitem__(0, u"別の字"))

    def test_g_5_a_changed_cache_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][u"cache の前後"].__setitem__(u"変化なし", False))
            self._red(lambda R, k=k: R[k][u"cache の前後"][u"後"]["edinet"].__setitem__(u"件数", 4))

    def test_g_5b_the_switch_record_of_the_injection_turns_red_when_the_wiring_or_the_values_are_wrong(self):
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"配線の問題", [u"N がちがう"]))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"inject の中の値", False))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"出たあとの値", True))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"名前", u"compound_yen_2026_11_05"))

    def test_g_5c_the_inject_cap_is_checked_on_its_own(self):
        R = copy.deepcopy(self.R)
        rows = R["inject"][u"行"]
        extra = []
        for i in range(RUN.INJECT_CAP):
            r = copy.deepcopy(rows[0])
            r[u"id"] = u"DOC1_F1_m1-T9-%02d" % (50 + i)
            extra.append(r)
        rows += extra
        R["inject"][u"注入の行の数"] = len(rows)
        R["inject"][u"集計"] = norm(PB.inject_summary(rows))
        R["t9"][u"行"] += [{u"id": r[u"id"], "P30E": r["P30E"]} for r in extra]
        R["inject"][u"E の欄"] = norm(PB.inject_columns(rows, R["t9"][u"行"]))
        self.assertTrue(any(u"上限" in x for x in inject_problems(R["inject"], R["t9"][u"行"], False)), inject_problems(R["inject"], R["t9"][u"行"], False))

    def test_g_5d_the_full_only_checks_are_exercised_on_the_sample(self):
        u"""full=True だけが見る検査(本番の記録でだけ走る)を、標本の記録で 1 つずつ。"""
        rg = copy.deepcopy(self.R["regress97"])
        self.assertTrue(any(u"97" in x for x in regress97_problems(rg, True)))                      # 標本は 97 書類でない
        self.assertFalse(any(u"E-1・E-8" in x for x in regress97_problems(rg, True)))               # 履歴から作り直した値と同じ
        rg[u"E-1・E-8 engine の差分"][u"直した file(M)"] += 1
        self.assertTrue(any(u"E-1・E-8" in x for x in regress97_problems(rg, True)))
        rg = copy.deepcopy(self.R["regress97"])
        self.assertFalse(any(u"写し" in x for x in regress97_problems(rg, True)))
        rg[u"E-7・E-9 の写し"]["E-7"][u"赤"] = 15
        self.assertTrue(any(u"写し" in x for x in regress97_problems(rg, True)))
        rg = copy.deepcopy(self.R["regress97"])
        rg[u"E-7・E-9 の写し"]["E-9"] = None
        self.assertTrue(any(u"写し" in x for x in regress97_problems(rg, True)))
        rg = copy.deepcopy(self.R["regress97"])
        rg[u"E-7・E-9 の写し"][u"engine の commit"] = "0" * 40
        self.assertTrue(any(u"写し" in x for x in regress97_problems(rg, True)))
        mv = copy.deepcopy(self.R["moves"])
        self.assertTrue(any(u"200" in x for x in moves_problems(mv, True)))                          # 標本は 200 本でない
        self.assertTrue(any(u"本の並び" in x for x in moves_problems(mv, True)))
        inj = copy.deepcopy(self.R["inject"])
        self.assertFalse(any(u"T9 の第 2 便の記録に無い id" in x for x in inject_problems(inj, self.R["t9"][u"行"], True)))
        self.assertTrue(any(u"T9 の第 2 便の記録に無い id" in x for x in inject_problems(inj, self.R["t9"][u"行"][1:], True)))      # T9 の記録に無い id の行がある
        self.assertTrue(any(u"本ごとの数え" in x for x in inject_problems(inj, self.R["t9"][u"行"], True)))

    def test_g_6_the_document_follows_the_records_and_the_seal(self):
        doc = sample_doc(self.R, self.seal)
        lines = doc.split(u"\n")
        i = lines.index(u"<!-- 門:start pred -->") + 3                  # 表の 1 行目(E-1)
        for col_char in (u"E", u"1", u"当"):
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
        R2["inject"][u"行"][0][u"engine の手がかり"] = False
        self.assertNotEqual([], doc_problems(doc, R2, self.seal))
        R3 = copy.deepcopy(self.R)
        R3["moves"][u"本"][0][u"動いた行の中身"][0][4] = G
        self.assertNotEqual([], doc_problems(doc, R3, self.seal))
        mutated_seal = self.seal.replace("45〜65", "45〜66", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertNotEqual([], doc_problems(doc, self.R, mutated_seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"門:start judge", u"門:start other"), self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"<!-- 門:start judge -->", u"<!-- 門:start judge2 -->", 1), self.R, self.seal))

    def test_g_7_forbidden_words_docids_and_ungated_numbers_turn_the_document_red(self):
        doc = sample_doc(self.R, self.seal)
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(doc + u"\n" + w + u"。\n", self.R, self.seal), w)
        self.assertNotEqual([], doc_problems(doc + u"\nS100" + u"ABCD の文。\n", self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n動いた行は 1234 行でした。\n", self.R, self.seal))
        self.assertEqual([], doc_problems(doc + u"\n動いた行は 1234 行でした。" + NOT_GATED + u"\n", self.R, self.seal))

    def test_g_8_a_damaged_t9_record_changes_e2_and_the_stored_columns_turn_red(self):
        rows, t9 = self.R["inject"][u"行"], self.R["t9"][u"行"]
        base = norm(PB.inject_columns(rows, t9))[u"E-2 T9 の第 2 便の記録との照らし"]
        t9b = copy.deepcopy(t9)
        t9b[0][u"id"] = u"X-T9-97"                                                              # id を 1 つ変える
        c = norm(PB.inject_columns(rows, t9b))[u"E-2 T9 の第 2 便の記録との照らし"]
        self.assertEqual((True, False, base[u"P30E の結果と state が T9 の第 2 便の記録と同じ行"] - 1), (base[u"id の集合が T9 の第 2 便の記録と同じ"], c[u"id の集合が T9 の第 2 便の記録と同じ"],
                                                                                          c[u"P30E の結果と state が T9 の第 2 便の記録と同じ行"]))
        t9c = copy.deepcopy(t9)
        t9c[3]["P30E"][u"state"] = V_                                                           # P30E の state を 1 つ変える
        c = norm(PB.inject_columns(rows, t9c))[u"E-2 T9 の第 2 便の記録との照らし"]
        self.assertEqual(base[u"P30E の結果と state が T9 の第 2 便の記録と同じ行"] - 1, c[u"P30E の結果と state が T9 の第 2 便の記録と同じ行"])
        t9d = copy.deepcopy(t9)
        t9d[3]["P30E"][u"結果"] = TUNE.LABEL_NAMED_OTHER                                        # 結果の語だけ変える
        c = norm(PB.inject_columns(rows, t9d))[u"E-2 T9 の第 2 便の記録との照らし"]
        self.assertEqual(base[u"P30E の結果と state が T9 の第 2 便の記録と同じ行"] - 1, c[u"P30E の結果と state が T9 の第 2 便の記録と同じ行"])
        for damaged in (t9b, t9c, t9d):
            R = copy.deepcopy(self.R)
            R["t9"][u"行"] = damaged
            self.assertNotEqual([], record_problems(R, full=False))                              # 記録の E の欄が壊した T9 の記録と合わない
        R = copy.deepcopy(self.R)
        R["t9"][u"行"] = t9b
        self.assertFalse(norm(PB.columns_from_records(R)["inject"])[u"E-2 T9 の第 2 便の記録との照らし"][u"id の集合が T9 の第 2 便の記録と同じ"])

    def test_g_9_the_judgment_comes_from_rows_books_and_docs_not_from_the_stored_aggregates(self):
        base = norm(PB.build_E(self.R, self.seal))
        R = copy.deepcopy(self.R)
        for path in list(leaves(R["moves"][u"集計"])):
            set_path(R["moves"][u"集計"], path, 0)
        for path in list(leaves(R["regress97"][u"集計"])):
            set_path(R["regress97"][u"集計"], path, 0)
        for path in list(leaves(R["inject"][u"E の欄"])):
            set_path(R["inject"][u"E の欄"], path, 0)
        self.assertEqual(base, norm(PB.build_E(R, self.seal)))                                  # 記録の集計・E の欄を 0 に固定しても判定は行・本・書類から作る
        R2 = copy.deepcopy(self.R)
        R2["moves"][u"本"][0][u"動いた行の中身"].append(ent(9, 9, P_, V_, u"なし", u"Prior1Year", u"偽"))
        self.assertNotEqual(base[u"E"]["E-4"][u"値"], norm(PB.build_E(R2, self.seal))[u"E"]["E-4"][u"値"])
        R3 = copy.deepcopy(self.R)
        R3["regress97"][u"書類"][1][u"P32E の動いた行"].pop(1)
        self.assertNotEqual(base[u"E"]["E-3"][u"値"], norm(PB.build_E(R3, self.seal))[u"E"]["E-3"][u"値"])
        R4 = copy.deepcopy(self.R)
        R4["inject"][u"行"][1]["P32E"] = copy.deepcopy(ORIG_C)
        self.assertNotEqual(base[u"E"]["E-6"][u"値"], norm(PB.build_E(R4, self.seal))[u"E"]["E-6"][u"値"])
        R5 = copy.deepcopy(self.R)
        R5["regress97"][u"E-1・E-8 engine の差分"][u"numstat"][ENGINE_FILES[0]] = [99, 0]
        self.assertEqual(MISS, PB.build_E(R5, self.seal)[u"E"]["E-1"][u"判定"])
        R6 = copy.deepcopy(self.R)
        R6["regress97"][u"E-7・E-9 の写し"]["E-9"][u"赤の試験"] = [u"他の試験"]
        self.assertEqual(MISS, PB.build_E(R6, self.seal)[u"E"]["E-9"][u"判定"])


# ================================================================ 既知の答えのある小さい入力(部品の関数)
class KnownAnswerTest(unittest.TestCase):
    def test_k_1_period5_and_pointer_parts_split_prior2year_and_never_return_an_element(self):
        self.assertEqual(u"なし", PB.period5([]))
        self.assertEqual(u"なし", PB.period5(None))
        self.assertEqual(u"CurrentYear", PB.period5(["xbrl:jppfs_cor:A@CurrentYearDuration"]))
        self.assertEqual(u"Prior1Year", PB.period5(["xbrl:jppfs_cor:A@Prior1YearInstant", "xbrl:jppfs_cor:A@CurrentYearInstant"]))     # 先頭だけ
        self.assertEqual(u"Prior2Year", PB.period5(["xbrl:jppfs_cor:A@Prior2YearDuration"]))
        self.assertEqual(u"他", PB.period5(["xbrl:jppfs_cor:A@InterimDuration"]))
        self.assertEqual(u"他", PB.period5(["text:abc"]))
        self.assertEqual(u"他", PB.period5([5]))
        self.assertEqual(("jppfs_cor:A", "Prior1YearDuration_Seg"), PB.pointer_parts(["xbrl:jppfs_cor:A@Prior1YearDuration_Seg"]))
        self.assertEqual((None, None), PB.pointer_parts(["text:x"]))
        self.assertEqual((None, None), PB.pointer_parts([]))
        self.assertEqual(PS.pointer_period(["xbrl:jppfs_cor:A@Prior2YearDuration"]), u"他")                                         # T9 の関数は Prior2Year を 他 に畳む(この script が別に持つ理由)

    def test_k_2_no_prior_fact_is_true_only_for_an_xbrl_element_without_a_prior_fact(self):
        prior = {"jppfs_cor:Sales"}
        self.assertFalse(PB.no_prior_fact(["xbrl:jppfs_cor:Sales@CurrentYearDuration"], prior))
        self.assertTrue(PB.no_prior_fact(["xbrl:jppfs_cor:Other@CurrentYearDuration"], prior))
        self.assertFalse(PB.no_prior_fact([], prior))                                         # 要素が分からないので『無い』と言わない
        self.assertFalse(PB.no_prior_fact(["text:x"], prior))
        self.assertTrue(PB.no_prior_fact(["xbrl:jppfs_cor:Sales@CurrentYearDuration"], set()))

    def test_k_3_prior_elements_reads_prior1year_jpy_facts_of_the_document(self):
        facts = [{"name": "jppfs_cor:A", "context": "Prior1YearDuration", "unit": "JPY"}, {"name": "jppfs_cor:B", "context": "CurrentYearDuration", "unit": "JPY"},
                 {"name": "jppfs_cor:C", "context": "Prior1YearInstant", "unit": "shares"}, {"name": "jppfs_cor:D", "context": "Prior2YearDuration", "unit": "JPY"},
                 {"name": "jppfs_cor:E", "context": "Prior1YearDuration", "unit": None}, {"name": "jppfs_cor:F", "context": "Prior1YearInstant", "unit": "jpy"}]
        with Patch() as pt:
            pt.set(PB.INST, "load_instance", lambda zb: {"facts": facts})
            self.assertEqual({"jppfs_cor:A", "jppfs_cor:F"}, PB.prior_elements(b"zip"))

    def test_k_4_diff_rows_counts_state_or_pointers_as_moved_and_reason_alone_apart(self):
        ra = collections.OrderedDict([((0, 1), (G, None, ("p",))), ((0, 2), (P_, "a", ())), ((0, 3), (V_, None, ("p",))), ((0, 4), (G, None, ("p",))), ((0, 9), (G, None, ()))])
        rb = collections.OrderedDict([((0, 1), (G, None, ("p",))), ((0, 2), (P_, "b", ())), ((0, 3), (V_, None, ("q",))), ((0, 4), (V_, None, ("p",))), ((0, 8), (G, None, ()))])
        common, moved, reason_only = PB.diff_rows(ra, rb)
        self.assertEqual([(0, 1), (0, 2), (0, 3), (0, 4)], common)
        self.assertEqual([(0, 3), (0, 4)], moved)
        self.assertEqual([(0, 2)], reason_only)

    def test_k_5_move_entry_has_the_fixed_shape_and_no_text_or_element(self):
        e = PB.move_entry((3, 7), (G, None, ("xbrl:jppfs_cor:A@CurrentYearDuration",)), (V_, None, ("xbrl:jppfs_cor:A@Prior1YearDuration",)), u"真", True, False)
        self.assertEqual([u"num", 3, 7, G, V_, u"CurrentYear", u"Prior1Year", u"真", EXISTING, False], e)
        e2 = PB.move_entry((3, 7), (P_, "r", ()), (V_, None, ("xbrl:jppfs_cor:A@Prior2YearDuration",)), None, False, True)
        self.assertEqual([u"num", 3, 7, P_, V_, u"なし", u"Prior2Year", None, NEWROW, True], e2)
        self.assertTrue(entry_shape_ok(e) and entry_shape_ok(e2))
        self.assertFalse(any(isinstance(x, str) and POINTER_TEXT_RE.search(x) for x in e + e2))

    def test_k_6_message_numbers_read_the_engine_commit_message_and_nothing_else(self):
        msg = u"engine(...)。新しい試験 32 本、変異 16 本全部赤。全数(clone)で赤は axis3 test_9 の 1 本だけ(pytest 1 failed / 6,802 passed / 35 skipped、unittest failures=1)= 期待どおり"
        r = PB.message_numbers(msg)
        self.assertEqual({u"変異の本数": 16, u"赤": 16, u"原文": u"変異 16 本全部赤"}, dict(r["E-7"]))
        self.assertEqual(([u"axis3 test_9"], 1, {"failed": 1, "passed": 6802, "skipped": 35}, 1), (r["E-9"][u"赤の試験"], r["E-9"][u"赤の本数"], dict(r["E-9"][u"pytest"]), r["E-9"][u"unittest failures"]))
        r2 = PB.message_numbers(msg.replace(u"全部赤", u"のうち 15 本が赤"))
        self.assertIsNone(r2["E-7"])
        self.assertIsNotNone(r2["E-9"])
        r3 = PB.message_numbers(msg.replace(u"unittest failures=1", u"unittest failures=2"))
        self.assertEqual(2, r3["E-9"][u"unittest failures"])
        self.assertIsNone(PB.message_numbers(msg.replace(u"だけ", u""))["E-9"])
        self.assertEqual({"E-7": None, "E-9": None}, dict(PB.message_numbers(u"")))
        self.assertEqual({"E-7": None, "E-9": None}, dict(PB.message_numbers(None)))
        real = PB.message_numbers(engine_message_at_history())
        self.assertEqual((16, 16), (real["E-7"][u"変異の本数"], real["E-7"][u"赤"]))
        self.assertEqual(([u"axis3 test_9"], 1), (real["E-9"][u"赤の試験"], real["E-9"][u"赤の本数"]))

    def test_k_7_e7_and_e9_values(self):
        B7 = collections.OrderedDict([(u"赤", 10), (u"変異の本数", 10)])
        ok = collections.OrderedDict([(u"変異の本数", 16), (u"赤", 16), (u"原文", u"x")])
        self.assertEqual(10, PB.e7_value({"E-7": ok}, B7)[u"赤"])
        self.assertIsNone(PB.e7_value({"E-7": dict(ok, 赤=15)}, B7))                              # 全部赤でない
        self.assertIsNone(PB.e7_value({"E-7": dict(ok, 変異の本数=9, 赤=9)}, B7))                  # 封の本数より少ない
        self.assertIsNone(PB.e7_value({"E-7": None}, B7))
        self.assertIsNone(PB.e7_value({}, B7))
        e9 = collections.OrderedDict([(u"赤の試験", [u"axis3 test_9"]), (u"赤の本数", 1), (u"pytest", {"failed": 1, "passed": 1, "skipped": 0}), (u"unittest failures", 1), (u"原文", u"x")])
        self.assertEqual(0, PB.e9_value({"E-9": e9})[u"ほかの赤"])
        self.assertEqual(2, PB.e9_value({"E-9": dict(e9, pytest={"failed": 3, "passed": 1, "skipped": 0})})[u"ほかの赤"])
        self.assertIsNone(PB.e9_value({"E-9": dict(e9, **{u"unittest failures": 2})}))
        self.assertIsNone(PB.e9_value({"E-9": dict(e9, pytest={"failed": 0, "passed": 1, "skipped": 0})}))
        self.assertIsNone(PB.e9_value({"E-9": None}))

    def test_k_8_the_prediction_table_rows_have_a_fixed_shape(self):
        seal = read(SEAL_REL)
        P = PB.seal_pred_rows(seal)
        J = PB.judge_from(sample_cols(), seal)
        lines = PB.render_pred(J, seal).split(u"\n")
        self.assertEqual(u"| # | 欄 | 予測 | 測った値 | 判定 |", lines[0])
        by = dict((ln.split(u" | ")[0][2:], ln) for ln in lines[2:])
        self.assertEqual(u"| E-8 | " + P["E-8"][0] + u" | 40〜75 | 直した file(M) 64・新しい file(A) 1・engine の挿入の行数 29 | **当たり** |", by["E-8"])
        self.assertEqual(u"| E-9 | " + P["E-9"][0] + u" | axis3 の test_9 だけ、0 | 赤の試験 axis3 test_9・赤の本数 1・ほかの赤 0 | **当たり** |", by["E-9"])
        self.assertEqual(10 + 2, len(lines))
        for ln in lines[2:]:
            self.assertEqual(5, len(ln.strip(u"|").split(u" | ")), ln)
        j = PB.render_judge(J, seal).split(u"\n")
        self.assertEqual(u"| # | 基準 | 測った値 | 判定 |", j[0])
        self.assertEqual(9, len(j))                                                    # 見出し 2 + K 5 + 空行 + 採用の一文
        self.assertEqual(u"採用の判定(K-1〜K-5 を全部満たす): **採用**。最後に決めるのは人間。", j[-1])
        J2 = PB.judge_from(sample_cols(lost97=1), seal)
        self.assertEqual(u"採用の判定(K-1〜K-5 を全部満たす): **採用しない(人間に返す)**。最後に決めるのは人間。", PB.render_judge(J2, seal).split(u"\n")[-1])

    def test_k_9_the_script_and_the_history_agree_on_the_engine_link(self):
        link = norm(PB.XR.engine_link())
        want = norm(link_at_history())
        self.assertEqual(dict((k, v) for k, v in want.items() if k != u"numstat"), link)
        self.assertEqual(want[u"numstat"], norm(PB.engine_numstat()))
        self.assertEqual([ENGINE_FILES[0], ENGINE_FILES[1]], want[u"engine の変更 file"])
        self.assertEqual(0, want[u"engine の削除の行数"])

    def test_k_10_engine_numstat_reads_the_lines_per_file(self):
        P = PREFIX
        num = ["24\t0\t%sadapters/xbrl/recipes.py" % P, "5\t0\t%sadapters/xbrl/vocabulary.py" % P]
        tests = ["M\t%stests/a.py" % P, "M\t%stests/b.py" % P, "A\t%stests/c.py" % P, "D\t%stests/d.py" % P]
        with Patch() as pt:
            pt.set(XR, "engine_commits", lambda: ("s" * 40, "e" * 40, num, tests))
            ns = PB.engine_numstat()
            link = XR.engine_link()
            pt.set(XR, "engine_commits", lambda: ("s" * 40, "e" * 40, num + ["-\t-\t%sadapters/xbrl/x.bin" % P], tests))
            ns2 = PB.engine_numstat()                                                            # バイナリの行(- -)は None
        self.assertEqual({ENGINE_FILES[0]: [24, 0], ENGINE_FILES[1]: [5, 0]}, dict(ns))
        self.assertEqual({"adapters/xbrl/x.bin": [None, None]}, dict((k, v) for k, v in ns2.items() if k not in ENGINE_FILES))
        self.assertEqual((2, 1, 1, 4), (link[u"直した file(M)"], link[u"新しい file(A)"], link[u"消した file(D)"], link[u"tests の変更 file"]))
        self.assertEqual((29, 0), (link[u"engine の挿入の行数"], link[u"engine の削除の行数"]))

    def test_k_11_window_cue_reads_the_untampered_text_at_the_token_start(self):
        import types
        t = types.SimpleNamespace
        self.assertTrue(PB.window_cue(u"前期の1億円でした", t(start=3)))
        self.assertTrue(PB.window_cue(u"売上高は(前期1億円)でした", t(start=u"売上高は(前期1億円)でした".index(u"1"))))
        self.assertFalse(PB.window_cue(u"営業外収益3億円から営業外費用1億円を引く", t(start=11)))        # 『A から B を』の A(「から」の枝だけ。窓は持たない)
        self.assertFalse(PB.window_cue(u"営業外収益3億円から営業外費用1億円を引く", t(start=6)))
        self.assertFalse(PB.window_cue(u"前期比2.9%増の100億円", t(start=9)))
        self.assertTrue(PB.R._prior_cue(u"営業外収益3億円から営業外費用1億円を引く", 6, 9) or True)       # `_prior_cue`(「から」の枝を持つ)は別の関数

    def test_k_12_seal_reading_functions(self):
        seal = read(SEAL_REL)
        self.assertEqual(list(SG.PRED_IDS), list(PB.seal_pred_rows(seal)))
        self.assertEqual(list(SG.K_IDS), list(PB.seal_k_rows(seal)))
        self.assertEqual(u"K-1: E-2 が 97 / 97 かつ 141 / 141(旗が偽で不変)", u"K-1: " + PB.k_cell(PB.seal_k_rows(seal)["K-1"]))
        self.assertEqual(u"a・b", PB.fmt([u"a", u"b"]))
        self.assertEqual(u"x 1・y はい", PB.fmt({u"x": 1, u"y": True}))
        self.assertEqual(u"12.5", PB.fmt(12.5))
        self.assertEqual(u"1,234", PB.fmt(1234))


# ================================================================ judge_book_pb を小さい合成の入力で通す(engine・zip・文は偽。通信なし)
class JudgeBookFlowTest(unittest.TestCase):
    PC, PP, PX = "xbrl:jppfs_cor:Sales@CurrentYearDuration", "xbrl:jppfs_cor:Sales@Prior1YearDuration", "xbrl:jppfs_cor:Other@CurrentYearDuration"
    # profile ごとの数の claim: (id, 文の番号, 位置, state, reason, pointers)
    CLAIMS = {
        "P27": [("N001", 0, 4, G, None, [PC]), ("N002", 0, 20, V_, None, [PC]), ("N004", 2, 4, P_, "no_same_value", []), ("N005", 3, 4, G, None, [PX])],
        "P30E": [("N001", 0, 4, G, None, [PC]), ("N002", 0, 20, V_, None, [PC]), ("N003", 1, 4, P_, "no_element", []), ("N004", 2, 4, P_, "no_same_value", []), ("N005", 3, 4, G, None, [PX])],
        "P32E": [("N001", 0, 4, G, None, [PC]), ("N002", 0, 20, V_, None, [PP]), ("N003", 1, 4, V_, None, [PP]), ("N004", 2, 4, P_, "no_element", []), ("N005", 3, 4, V_, None, [PX])]}
    LABELS = {"N001": u"真", "N002": u"偽", "N004": u"真", "N005": u"真"}

    def fakes(self, pt, claims=None, prior=None):
        claims = claims or self.CLAIMS

        def verify(zb, pname, text):
            return {"claims": [{"id": i, "kind": "num", "state": st, "reason": rs, "pointers": list(ptr)} for (i, _s, _p, st, rs, ptr) in claims[pname]]}

        def raw(zm, prof, info=None):
            return ([{"id": i, "sentence": si, "pos": pos} for (i, si, pos, _st, _rs, _ptr) in claims[prof.name]], [])
        pt.set(PB.VD, "verify_document", verify)
        pt.set(PB.R, "build_raw_claims", raw)
        pt.set(PB.GEN, "read_zip", lambda row, caches=None: b"zip")
        pt.set(PB.RUN, "read_text", lambda name, item, d: u"text")
        pt.set(PB.PR, "build_modified_zip", lambda zb, text: (b"zm", None, None))
        old = {u"対応": True, u"行": [[i, "num"] for (i, _s, _p, _st, _rs, _ptr) in claims["P27"]]}
        pt.set(PB.RUN, "judge_text", lambda zb, text: (copy.deepcopy(old), []))
        calls = []
        pt.set(PB, "prior_elements", lambda zb: calls.append(1) or (prior if prior is not None else {"jppfs_cor:Sales"}))
        return calls

    def job(self, labels=None):
        return ("aiforms", "DOC1_F1_m1", ITEMS[0], {}, "d", {}, {}, dict(self.LABELS if labels is None else labels), {})

    def test_j_1_judge_book_pb_assembles_the_book_record_from_the_two_profiles(self):
        with Patch() as pt:
            calls = self.fakes(pt)
            b = norm(PB.judge_book_pb(self.job()))
        self.assertEqual({"P30E": 5, "P32E": 5}, b[u"数の claim の数"])
        self.assertEqual({"P30E": 2, "P32E": 1}, b[u"GROUNDED の数"])
        self.assertEqual((3, 2, 1), (b[u"動いた行"], b[u"state が変わった行"], b[u"reason だけが違う行"]))
        self.assertEqual([[u"num", 0, 20, V_, V_, u"CurrentYear", u"Prior1Year", u"偽", EXISTING, False],
                          [u"num", 1, 4, P_, V_, u"なし", u"Prior1Year", None, NEWROW, False],
                          [u"num", 3, 4, G, V_, u"CurrentYear", u"CurrentYear", u"真", EXISTING, True]], b[u"動いた行の中身"])
        self.assertEqual((True, True, {"P30E": True, "P32E": True}), (b[u"P30E と P32E で数の claim の鍵が同じ"], b[u"P27 の鍵が一意"], b[u"対応"]))
        self.assertEqual([1], calls)                                                              # 前期の fact は動いた行のある本で 1 回だけ読む
        self.assertEqual([], book_problems(b))
        self.assertEqual(u"DOC1", b[u"docID"])
        self.assertFalse(any(isinstance(x, str) and POINTER_TEXT_RE.search(x) for x in walk_strings(b)))        # 要素名・context を持たない

    def test_j_2_no_prior_fact_flag_follows_the_document_facts(self):
        for prior, want in (({"jppfs_cor:Sales", "jppfs_cor:Other"}, [False, False, False]), ({"jppfs_cor:Sales"}, [False, False, True]), (set(), [True, True, True])):
            with Patch() as pt:
                self.fakes(pt, prior=prior)
                b = norm(PB.judge_book_pb(self.job()))
            self.assertEqual(want, [x[9] for x in b[u"動いた行の中身"]], sorted(prior))            # 行の順は P30E の鍵の順: N002(Sales)・N003(Sales)・N005(Other)
            if prior == {"jppfs_cor:Sales"}:                                                    # 本の整合の検査を通るのは pointer の期と前期の fact の有無が合う場合だけ
                self.assertEqual([], book_problems(b))
            elif not prior:                                                                     # 前期の fact が無い要素なのに pointer の期が Prior1Year の行 = 整合しない
                self.assertNotEqual([], book_problems(b))

    def test_j_3_labels_are_taken_only_for_rows_that_exist_in_p27_by_the_p27_id(self):
        with Patch() as pt:
            self.fakes(pt)
            b = norm(PB.judge_book_pb(self.job(labels={u"N002": u"判定不能"})))
        self.assertEqual([u"判定不能", None, None], [x[7] for x in b[u"動いた行の中身"]])             # N003 は P27 に無い = 新しい行(札を引かない)・N005 は札が無い
        self.assertEqual([EXISTING, NEWROW, EXISTING], [x[8] for x in b[u"動いた行の中身"]])
        with Patch() as pt:
            self.fakes(pt)
            b = norm(PB.judge_book_pb(self.job(labels={u"N003": u"真"})))                          # 新しい行の id に札があっても引かない
        self.assertEqual([None, None, None], [x[7] for x in b[u"動いた行の中身"]])

    def test_j_4_a_claim_order_mismatch_and_unequal_keys_are_reported_not_hidden(self):
        claims = copy.deepcopy(self.CLAIMS)
        claims["P32E"] = claims["P32E"][:-1]                                                        # P32E の数の claim が 1 つ少ない
        with Patch() as pt:
            self.fakes(pt, claims=claims)
            b = norm(PB.judge_book_pb(self.job()))
        self.assertFalse(b[u"P30E と P32E で数の claim の鍵が同じ"])
        self.assertEqual(4, b[u"数の claim の数"]["P32E"])
        self.assertEqual([], book_problems(b))
        claims2 = copy.deepcopy(self.CLAIMS)
        claims2["P27"] = claims2["P27"] + [("N009", 0, 4, G, None, [self.PC])]                      # 同じ鍵が P27 に 2 つ = P27 の鍵が一意でない
        with Patch() as pt:
            self.fakes(pt, claims=claims2)
            b2 = norm(PB.judge_book_pb(self.job()))
        self.assertFalse(b2[u"P27 の鍵が一意"])

    def test_j_5_run_moves_refuses_what_it_must_and_writes_the_record_parts(self):
        job = self.job()
        seen = []
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            self.fakes(pt)
            pt.set(RM, "load_jobs", lambda root=ROOT, only=None: [job])

            def pool(fn, jobs_, procs):
                seen.append(len(jobs_))
                return [fn(j) for j in jobs_]
            pt.set(NF, "map_pool", pool)
            pt.set(PB, "caches_all", lambda: collections.OrderedDict())
            out = os.path.join(d, "moves.json")
            rec = PB.run_moves(root=ROOT, procs=1, out=out, say=lambda *a: None)
            with open(out, encoding="utf-8") as fh:
                disk = json.load(fh)
            with self.assertRaises(PB.Stop):                                                       # 出力が在れば測り直さない
                PB.run_moves(root=ROOT, procs=1, out=out, say=lambda *a: None)
            with self.assertRaises(PB.Stop):                                                       # --only は --out が要る
                PB.run_moves(root=d, procs=1, only="DOC1", say=lambda *a: None)
            self.assertFalse(os.path.exists(os.path.join(d, PB.MOVES_REL)))
        self.assertEqual([1], seen)
        self.assertEqual(norm(rec), disk)
        self.assertEqual(norm(PB.aggregate_moves(disk[u"本"])), disk[u"集計"])
        self.assertEqual(list(PB.MOVES_LIMITS), disk[u"限界"])
        self.assertEqual(u"**--only の本だけ(本番の記録ではない)**" if False else u"全 200 本", disk[u"範囲"])
        self.assertEqual([], clean_problems("moves", disk))
        self.assertEqual([], header_problems("moves", dict(disk, **{u"範囲": u"全 200 本"}), False) if False else [x for x in header_problems("moves", disk, False) if u"cache" not in x and u"HEAD" not in x])

    def test_j_6_run_moves_stops_when_a_guard_fires(self):
        job = self.job()
        for why, extra in ((u"配線が崩れている", (PB, "wiring_problems", lambda: [u"x"])), (u"cache の件数か名前が変わった", (PB.GEN, "caches_snapshot", self._moving()))):
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
                self.fakes(pt)
                pt.set(RM, "load_jobs", lambda root=ROOT, only=None: [job])
                pt.set(NF, "map_pool", lambda fn, jobs_, procs: [fn(j) for j in jobs_])
                pt.set(PB, "caches_all", lambda: collections.OrderedDict())
                pt.set(*extra)
                out = os.path.join(d, "moves.json")
                with self.assertRaises(PB.Stop) as cm:
                    PB.run_moves(root=ROOT, procs=1, out=out, say=lambda *a: None)
                self.assertIn(why, str(cm.exception))
                self.assertFalse(os.path.exists(out))
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(PB.RUN, "PROFILES", ("P27",))                                                   # 前の便の 4 つでない
            with self.assertRaises(PB.Stop) as cm:
                PB.run_moves(root=ROOT, procs=1, out=os.path.join(d, "m.json"), say=lambda *a: None)
            self.assertIn(u"前の便の 4 つでない", str(cm.exception))

    @staticmethod
    def _moving():
        calls = {"n": 0}

        def snap(caches):
            calls["n"] += 1
            return {u"n": calls["n"]}
        return snap


class DocMovesFlowTest(unittest.TestCase):
    def res(self, ra, rb):
        return {u"keyed": {"P30E": collections.OrderedDict(ra), "P32E": collections.OrderedDict(rb)}}

    def test_d_1_doc_moves_pb_reads_the_prior_facts_only_for_a_document_with_moves(self):
        PC, PP = "xbrl:jppfs_cor:Sales@CurrentYearDuration", "xbrl:jppfs_cor:Sales@Prior1YearDuration"
        PX = "xbrl:jppfs_cor:Other@CurrentYearDuration"
        ra = [(("num", 0, 4, 0), (G, None, (PC,))), (("num", 1, 4, 0), (V_, None, (PC,))), (("text", 2, 0, 0), (V_, "a", (PX,))), (("num", 3, 3, 0), (P_, "r", ()))]
        rb = [(("num", 0, 4, 0), (G, None, (PC,))), (("num", 1, 4, 0), (V_, None, (PP,))), (("text", 2, 0, 0), (V_, "b", (PX,))), (("num", 3, 3, 0), (V_, None, (PP,)))]
        calls = []
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            z = os.path.join(d, "doc.zip")
            with open(z, "wb") as fh:
                fh.write(b"zip")
            pt.set(PB, "prior_elements", lambda zb: calls.append(zb) or {"jppfs_cor:Sales"})
            ents, ro = PB.doc_moves_pb(self.res(ra, rb), z)
            self.assertEqual([b"zip"], calls)
            self.assertEqual([[u"num", 1, 4, 0, V_, V_, u"CurrentYear", u"Prior1Year", False, True, False],
                              [u"num", 3, 3, 0, P_, V_, u"なし", u"Prior1Year", True, True, False]], ents)
            self.assertEqual(1, ro)                                                              # text の reason だけが違う行
            calls[:] = []
            same = self.res(ra, ra)
            ents2, ro2 = PB.doc_moves_pb(same, os.path.join(d, "no_such_file.zip"))              # 動いた行が無ければ ZIP を読まない
            self.assertEqual(([], 0, []), (ents2, ro2, calls))
            rb2 = [(k, v) for k, v in rb]
            rb2[0] = (rb2[0][0], (V_, None, (PX,)))                                                 # GROUNDED を失う行・前期の fact が無い要素
            ents3, _ro = PB.doc_moves_pb(self.res(ra, rb2), z)
            self.assertEqual([u"num", 0, 4, 0, G, V_, u"CurrentYear", u"CurrentYear", True, True, True], ents3[0])
        for x in ents + ents3:
            self.assertTrue(isinstance(x[8], bool) and (x[8] == (x[4] != x[5])))


# ================================================================ (w) inject_text_pb を小さい入力で通す(zip・判定は偽。lib は本物)
def verify_pb(text0, old=(G, PTR_CUR), new=(V_, PTR_PRIOR), shift_new=False, edit=None):
    u"""無改変の文の数は GROUNDED(pointers = PTR_PRIOR)、注入した文で増えた数は P30E が old = (state, pointer)・P32E が new。edit(profile, claims, 注入後か) で claim を書き換える。"""
    v30 = make_verify(text0, base_ptr=PTR_PRIOR, inj_state=old[0], inj_ptr=old[1])
    v32 = make_verify(text0, base_ptr=PTR_PRIOR, inj_state=new[0], inj_ptr=new[1])

    def verify(zb, p, t):
        out = (v30 if p == "P30E" else v32)(zb, p, t)
        if shift_new and p == "P32E":
            for c in out["claims"]:
                c["id"] = "X" + c["id"]
        if edit is not None:
            edit(p, out["claims"], t != text0)
        return out
    return verify


def run_pb(text=TEXT_P, refs=REFS_P, verify=None, **kw):
    with PB.PI.yen_scan_on():
        return PB.inject_text_pb(b"zip", text, refs, u"sd", u"bk", verify=verify or verify_pb(text), **kw)


def full_row(r, n=1):
    u"""``inject_text_pb`` の行に本の欄(docID・form・model・writer)を足して行の検査に渡せる形にする。"""
    d = collections.OrderedDict([(u"docID", u"DOC1"), (u"form", u"F1"), (u"model", u"m1"), (u"writer", u"W1")])
    d.update(r)
    d[u"id"] = u"DOC1_F1_m1-T9-%02d" % n
    return d


class InjectProcedureTest(unittest.TestCase):
    def test_i_1_rows_carry_every_column_for_an_honest_injection(self):
        rows, c = run_pb()
        self.assertEqual(3, len(rows))
        self.assertEqual(list(ROW_KEYS[4:]), list(rows[0]))
        self.assertEqual({u"作れる site": 3, u"土台 P30E が GROUNDED の site": 3, u"cap を基準で絞る前に掛けた数": 3, u"採った": 3}, dict(c))
        for n, r in enumerate(rows, 1):
            self.assertEqual(["bk-T9-%02d" % n], [r[u"id"]])
            self.assertEqual((PB.T9, True, True, True, True), (r[u"型"], r[LINK_KEY], r[u"engine の手がかり"], r[u"窓の手がかり"], r[u"文に前期の語"]))
            self.assertEqual((TUNE.LABEL_PASS, G, u"CurrentYear"), (r["P30E"][u"結果"], r["P30E"][u"state"], r[u"P30E の注入後の pointer の期"]))
            self.assertEqual((TUNE.LABEL_NAMED_ORIGINAL, V_, u"Prior1Year"), (r["P32E"][u"結果"], r["P32E"][u"state"], r[u"P32E の注入後の pointer の期"]))
            self.assertEqual(([], []), (r[u"P30E の欠けた条件"], r[u"P32E の欠けた条件"]))
            self.assertEqual((True, True), (r[u"round-trip"], r[u"読み直し"]))
            self.assertEqual([], row_problems(full_row(r, n), set()))
        self.assertEqual([], sorted(set(k for r in rows for k in RUN.walk_keys(r) if k in FORBIDDEN_KEYS)))
        cols = norm(PB.inject_columns([full_row(r, n) for n, r in enumerate(rows, 1)], [{u"id": full_row(r, n)[u"id"], "P30E": r["P30E"]} for n, r in enumerate(rows, 1)]))
        self.assertEqual({u"手がかり真の行": 3, u"当期の fact に GROUNDED": 0, u"前期の fact を名指して VALUE_MISMATCH": 3, u"別の fact に GROUNDED": 0, u"その他": 0,
                          u"手がかり偽の行": 0, u"手がかり偽の行のうち P30E と同じ行": 0}, cols[u"E-5 手がかり別の P32E"])
        self.assertEqual((0.0, 3, 100.0), (cols[u"E-6 通した率と名指して原本"][u"通した率(P32E)"], cols[u"E-6 通した率と名指して原本"][u"止めた行"], cols[u"E-6 通した率と名指して原本"][u"名指して原本の割合"]))

    def test_i_2_the_t9_columns_have_the_same_values_as_the_t9_script_rows(self):
        rows, _c = run_pb(verify=verify_pb(TEXT_P, old=(V_, PTR_PRIOR), new=(V_, PTR_PRIOR)))              # T9 の偽の verify と同じ(注入した数は全部 前期の fact を名指す)
        t9rows, _t9c = PSR.run_ps()
        self.assertEqual(len(t9rows), len(rows))
        for r, r9 in zip(rows, t9rows):
            for key in (u"id", u"型", u"形", u"基準の claim", u"round-trip", u"読み直し", u"engine の手がかり", u"文に前期の語", u"基準の pointer の期"):
                self.assertEqual(r9[key], r[key], key)
            self.assertEqual(r9["P30E"], r["P30E"])                                                      # 正直な注入では P30E の欄は T9 の script と同じ

    def test_i_3_each_missing_condition_of_p32e_turns_its_mapping_off_and_names_the_missing_one(self):
        def drop_id(p, claims, tampered):
            if p == "P32E" and tampered:
                for c in claims:
                    if c["state"] == V_:
                        c["id"] = u"Z" + c["id"]

        def wrong_value(p, claims, tampered):
            if p == "P32E" and tampered:
                for c in claims:
                    if c["state"] == V_:
                        c["value"] = c["value"] * 2

        def cut_span(p, claims, tampered):
            if p == "P32E" and tampered:
                for c in claims:
                    if c["state"] == V_:
                        c["span"] = c["span"][:1]
        for edit, want_miss, want_period in ((drop_id, list(CONDS), u"なし"), (wrong_value, [CONDS[1]], u"Prior1Year"), (cut_span, [CONDS[2]], u"Prior1Year")):
            rows, _c = run_pb(verify=verify_pb(TEXT_P, edit=edit))
            for r in rows:
                self.assertEqual(UNMAPPED_CELL, norm(r["P32E"]), want_miss)
                self.assertEqual(want_miss, r[u"P32E の欠けた条件"])
                self.assertEqual(want_period, r[u"P32E の注入後の pointer の期"])
                self.assertEqual((TUNE.LABEL_PASS, [], u"CurrentYear"), (r["P30E"][u"結果"], r[u"P30E の欠けた条件"], r[u"P30E の注入後の pointer の期"]))      # P30E は変わらない
                self.assertTrue(r[LINK_KEY])
                self.assertEqual([], row_problems(full_row(r), set()))

    def test_i_4_a_p30e_edit_does_not_move_the_p32e_cell(self):
        def drop_id(p, claims, tampered):
            if p == "P30E" and tampered:
                for c in claims:
                    if c["state"] == G:
                        c["id"] = u"Z" + c["id"]
        rows, _c = run_pb(verify=verify_pb(TEXT_P, edit=drop_id))
        for r in rows:
            self.assertEqual(UNMAPPED_CELL, norm(r["P30E"]))
            self.assertEqual(list(CONDS), r[u"P30E の欠けた条件"])
            self.assertEqual((TUNE.LABEL_NAMED_ORIGINAL, []), (r["P32E"][u"結果"], r[u"P32E の欠けた条件"]))

    def test_i_5_a_site_without_a_p32e_twin_leaves_the_p32e_cell_unmapped(self):
        def no_twin(p, claims, tampered):
            if p == "P32E" and not tampered:
                for c in claims:
                    c["value"] = c["value"] * 3 + 1
        rows, c = run_pb(verify=verify_pb(TEXT_P, edit=no_twin))
        self.assertEqual(3, len(rows))                                                                    # 土台は P30E の claim で決まる(P32E の claim が無くても site は残る)
        for r in rows:
            self.assertFalse(r[LINK_KEY])
            self.assertEqual(UNMAPPED_CELL, norm(r["P32E"]))
            self.assertEqual(([NO_BASE], u"なし"), (r[u"P32E の欠けた条件"], r[u"P32E の注入後の pointer の期"]))
            self.assertEqual(TUNE.LABEL_PASS, r["P30E"][u"結果"])
            self.assertEqual([], row_problems(full_row(r), set()))

    def test_i_6_each_profile_is_looked_up_by_its_own_base_claim_id(self):
        rows, _c = run_pb(verify=verify_pb(TEXT_P, shift_new=True))
        for r in rows:
            self.assertTrue(r[LINK_KEY])
            self.assertEqual((TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL), (r["P30E"][u"結果"], r["P32E"][u"結果"]))
            self.assertEqual([], r[u"P32E の欠けた条件"])

    def test_i_7_the_base_is_the_p30e_grounded_claim_not_the_p32e_one(self):
        def p30e_not_grounded(p, claims, tampered):
            if p == "P30E" and not tampered:
                for c in claims:
                    c["state"] = V_
        rows, c = run_pb(verify=verify_pb(TEXT_P, edit=p30e_not_grounded))
        self.assertEqual(([], 3, 0), (rows, c[u"作れる site"], c[u"土台 P30E が GROUNDED の site"]))
        self.assertEqual(0, c[u"採った"])

        def p32e_not_grounded(p, claims, tampered):
            if p == "P32E" and not tampered:
                for c in claims:
                    c["state"] = V_
        rows, c = run_pb(verify=verify_pb(TEXT_P, edit=p32e_not_grounded))
        self.assertEqual(3, len(rows))                                                                    # P32E の無改変の判定は土台を決めない

    def test_i_8_the_base_pair_swap_is_restored_and_the_ids_are_keyed_by_profile(self):
        before = tuple(PI.RM.INJECT_PROFILES)
        run_pb()
        self.assertEqual(before, tuple(PI.RM.INJECT_PROFILES))
        v = verify_pb(TEXT_P)
        base_claims = dict((p, v(b"zip", p, TEXT_P)["claims"]) for p in PB.PROFILES)
        by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in PB.PROFILES)
        with PB.PI.yen_scan_on():
            tok = PS.t9_all_sites(TEXT_P, REFS_P, u"sd", u"bk")[1][0]["token"]
            st, bc = PB.base_status_pb(base_claims, by_id, tok, TEXT_P)
        self.assertEqual({"P32E", "P30E"}, set(bc["ids"]))
        self.assertEqual(before, tuple(PI.RM.INJECT_PROFILES))
        self.assertIsNotNone(bc["ids"]["P32E"])

    def test_i_9_the_cap_and_the_fullwidth_digit_skip(self):
        rows, c = run_pb(cap=2)
        self.assertEqual(["bk-T9-01", "bk-T9-02"], [r[u"id"] for r in rows])
        self.assertEqual((3, 2, 2), (c[u"作れる site"], c[u"cap を基準で絞る前に掛けた数"], c[u"採った"]))
        rows, c = run_pb(text=u"前期は９億7,000万円でした。")
        self.assertEqual([], rows)
        self.assertEqual([u"注入しない"], list(c))

    def test_i_10_the_prior2year_period_is_kept_apart_in_the_row(self):
        P2 = "xbrl:jppfs_cor:NetSales@Prior2YearDuration"
        rows, _c = run_pb(verify=verify_pb(TEXT_P, new=(G, P2)))
        for r in rows:
            self.assertEqual((TUNE.LABEL_PASS, u"Prior2Year"), (r["P32E"][u"結果"], r[u"P32E の注入後の pointer の期"]))
            self.assertEqual([], row_problems(full_row(r), set()))
        cols = norm(PB.inject_columns([full_row(r, n) for n, r in enumerate(rows, 1)], []))
        self.assertEqual(3, cols[u"参考"][u"P32E の注入後の期が Prior2Year の行"])
        self.assertEqual(3, cols[u"E-5 手がかり別の P32E"][u"別の fact に GROUNDED"])                       # Prior2Year に GROUNDED は 別の fact に GROUNDED(追記 1 の 4)

    def test_i_11_the_job_adds_the_book_columns_and_refuses_a_switch_that_is_off(self):
        item = {u"docID": "DOC1", u"form": "F1", u"model": "m1", u"writer": "W1", u"sha256": "0" * 64}
        job = ("aiforms", "DOC1_F1_m1", item, {}, "d", {}, u"sd", "w")
        with Patch() as pt:
            pt.set(PI.GEN, "read_zip", lambda row, caches=None: b"zip")
            pt.set(PI.RUN, "read_text", lambda name, it, d: TEXT_P)
            pt.set(PI.RUN, "refs_for", lambda row, caches, work: REFS_P)
            pt.set(PB.VD, "verify_document", verify_pb(TEXT_P))
            with self.assertRaises(PB.Stop):
                PB.inject_job_pb(job)                                                                      # 切り替えが偽のまま
            with PB.PI.yen_scan_on():
                name, rows, counts = PB.inject_job_pb(job)
        self.assertEqual("DOC1_F1_m1", name)
        self.assertEqual(list(ROW_KEYS), list(rows[0]))
        self.assertEqual(["DOC1_F1_m1-T9-01", "DOC1_F1_m1-T9-02", "DOC1_F1_m1-T9-03"], [r[u"id"] for r in rows])
        self.assertEqual([], [x for r in rows for x in row_problems(r, set())][:0])
        self.assertEqual([], row_problems(rows[0], set()))
        self.assertEqual(3, counts[u"採った"])
        self.assertFalse(getattr(PI.N, PI.FLAG))


class RunInjectTest(unittest.TestCase):
    def _fakes(self, pt, d, rows, per, flag_before=False):
        item = {u"docID": "DOC1", u"form": "F1", u"model": "m1", u"writer": "W1", u"sha256": "0" * 64}
        pt.set(PI, "load_books", lambda root=ROOT, only=None: [("aiforms", "DOC1_F1_m1", item, {}, {})])
        seen = []

        def pool(fn, jobs_, procs):
            seen.append(getattr(PI.N, PI.FLAG))
            return [("DOC1_F1_m1", [collections.OrderedDict(r) for r in rows if r["docID"] == "DOC1"], norm(per))]
        pt.set(PI.NF, "map_pool", pool)
        pt.set(PI, "caches_all", lambda: collections.OrderedDict())
        pt.set(PI.GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
        return seen

    def test_w_20_run_inject_leaves_the_switch_off_and_writes_the_record_parts(self):
        base = sample_inject()
        rows = norm(base[u"行"])
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            seen = self._fakes(pt, d, rows, base[u"本ごとの数え"][u"DOC1_F1_m1"])
            out = os.path.join(d, "inject.json")
            rec = PB.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with open(out, encoding="utf-8") as fh:
                disk = json.load(fh)
            with self.assertRaises(PB.Stop):                                                    # 出力が在れば測り直さない
                PB.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with self.assertRaises(PB.Stop):                                                    # --only は --out が要る(守りが壊れても root の下の使い捨ての場所に書く)
                PB.run_inject(root=d, procs=1, only="DOC1", say=lambda *a: None, work_root=d)
            self.assertFalse(os.path.exists(os.path.join(d, PB.INJECT_REL)))
        self.assertEqual([True], seen)                                    # map_pool の呼ばれた間は真
        self.assertFalse(getattr(PI.N, PI.FLAG))                          # 出たら偽
        self.assertEqual(norm(rec), disk)
        self.assertEqual((BASE_WORD_PIN, SITE_WORD_PIN), (disk[u"型"][u"土台"], disk[u"型"][u"site"]))
        self.assertEqual(list(PB.INJECT_LIMITS), disk[u"限界"])
        self.assertEqual({u"名前": PI.FLAG, u"inject の中の値": True, u"出たあとの値": False, u"配線の問題": []}, disk[u"切り替え"])
        self.assertEqual(norm(PB.inject_columns(disk[u"行"], t9_record()[u"行"])), disk[u"E の欄"])      # E の欄は T9 の第 2 便の記録を読んで数える
        self.assertEqual(norm(PB.inject_summary(disk[u"行"])), disk[u"集計"])
        self.assertEqual([u"P30E", u"P32E"], disk[u"profile"])
        self.assertEqual(u"**--only(本番の記録ではない)**" if False else u"全 200 本", disk[u"範囲"])
        self.assertEqual([], clean_problems("inject", disk))
        self.assertEqual([], [x for x in header_problems("inject", disk, True) if u"cache" not in x and u"HEAD" not in x])

    def _stops(self, why, *extra, flag_before=False):
        base = sample_inject()
        rows = norm(base[u"行"])
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            self._fakes(pt, d, rows, base[u"本ごとの数え"][u"DOC1_F1_m1"])
            for mod, name, v in extra:
                pt.set(mod, name, v)
            out = os.path.join(d, "inject.json")
            setattr(PI.N, PI.FLAG, flag_before)
            try:
                with self.assertRaises(PB.Stop) as cm:
                    PB.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            finally:
                setattr(PI.N, PI.FLAG, False)                                                      # 試験が立てた旗は必ず戻す
            self.assertIn(why, str(cm.exception))
            self.assertFalse(os.path.exists(out))                                                  # Stop したら記録を書かない
        self.assertFalse(getattr(PI.N, PI.FLAG))

    def test_w_20b_run_inject_stops_before_writing_when_a_guard_fires(self):
        u"""正常な入力では発火しない守り(旗が真のまま・差し替えが届かない・配線が崩れた・with を出ても真・cache が変わった)を、故障を作って当てる。"""
        import contextlib
        calls = {"n": 0}

        def moving_snapshot(caches):
            calls["n"] += 1
            return {u"n": calls["n"]}                                                              # 前と後で違う

        @contextlib.contextmanager
        def leaky_switch():
            setattr(PI.N, PI.FLAG, True)
            yield                                                                                  # 出るときに戻さない
        seq = {"n": 0}

        def broken_inside():
            seq["n"] += 1
            return [] if seq["n"] == 1 else [u"N がちがう"]                                        # 1 回目(with の外)は空・2 回目(with の中)で崩れた
        self._stops(u"差し替えが届いていない", (PB, "wiring_problems", lambda: [u"差し替えが届いていない"]))
        self._stops(u"差し替えが届いていない", (PI, "wiring_problems", lambda: [u"N がちがう"]))
        self._stops(u"切り替えを真にできない・配線が崩れた", (PI, "wiring_problems", broken_inside))
        self._stops(u"with を出ても切り替えが真のまま", (PI, "yen_scan_on", leaky_switch))
        self._stops(u"cache の件数か名前が変わった", (PI.GEN, "caches_snapshot", moving_snapshot))
        self._stops(u"切り替えが真のまま inject を始めた", flag_before=True)

    def test_w_21_write_record_stops_on_a_forbidden_key_a_key_shape_and_an_existing_file(self):
        rec = collections.OrderedDict([(u"seal", SEAL_REL), (u"ok", 1)])
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            p = os.path.join(d, "a.json")
            PB.write_record(p, rec, RUN, GEN)                                                      # 封の path 自体は鍵の形と見ない
            self.assertTrue(os.path.exists(p))
            with self.assertRaises(PB.Stop):
                PB.write_record(p, rec, RUN, GEN)                                                  # 在れば測り直さない
            with self.assertRaises(PB.Stop):
                PB.write_record(os.path.join(d, "b.json"), dict(rec, span=1), RUN, GEN)
            with self.assertRaises(PB.Stop):
                PB.write_record(os.path.join(d, "c.json"), dict(rec, メモ=u"sk-" + u"a" * 30), RUN, GEN)
            with self.assertRaises(PB.Stop):
                PB.write_record(os.path.join(d, "e.json"), dict(rec, メモ=u"A" * 40), RUN, GEN)    # 32 字以上の英数字の連なり(封の path の字を除いても残る)
            self.assertFalse(os.path.exists(os.path.join(d, "b.json")) or os.path.exists(os.path.join(d, "c.json")) or os.path.exists(os.path.join(d, "e.json")))
            p2 = os.path.join(d, "f.json")
            PB.write_record(p2, rec, PI.RUN, PI.GEN, text=PI.RUN.dumps_inject(dict(rec, **{u"行": []})))        # 注入の側(別の instance)でも封の path は通る
            self.assertTrue(os.path.exists(p2))
        self.assertTrue(PB.key_leaks_pb(GEN)(SEAL_REL) == [])
        self.assertTrue(PB.key_leaks_pb(GEN)(u"sk-" + u"a" * 30))
        old = GEN.key_leaks
        with PB.key_check_pb(GEN):
            self.assertIsNot(GEN.key_leaks, old)
        self.assertIs(GEN.key_leaks, old)
        try:
            with PB.key_check_pb(GEN):
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertIs(GEN.key_leaks, old)

    def test_w_22_regress97_and_moves_refuse_what_they_must(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with self.assertRaises(PB.Stop):
                PB.run_regress97(root=d, procs=1, only="DOC1", say=lambda *a: None)              # --only は --out が要る
            existing = os.path.join(d, "r.json")
            with open(existing, "w", encoding="utf-8") as fh:
                fh.write("{}")
            with self.assertRaises(PB.Stop):
                PB.run_regress97(root=d, procs=1, out=existing, say=lambda *a: None)             # 在れば測り直さない
            with self.assertRaises(PB.Stop):
                PB.run_moves(root=d, procs=1, out=existing, say=lambda *a: None)
            with Patch() as pt:
                pt.set(PB, "wiring_problems", lambda: [u"XR.PAIRS が差し替えた先でない"])
                with self.assertRaises(PB.Stop) as cm:
                    PB.run_regress97(root=d, procs=1, out=os.path.join(d, "n.json"), say=lambda *a: None)
                self.assertIn(u"差し替えが届いていない", str(cm.exception))
            self.assertFalse(os.path.exists(os.path.join(d, "n.json")))
            self.assertFalse(os.path.exists(os.path.join(d, PB.REGRESS97_REL)) or os.path.exists(os.path.join(d, PB.MOVES_REL)))

    def test_w_23_run_regress97_calls_the_previous_functions_and_adds_the_columns(self):
        u"""run_regress97 の本文が前の便の関数(doc_job・doc_rows・engine_commits・engine_link)と自分の部品を呼ぶ。1 つ外すと赤。"""
        fn = [n for n in ast.parse(read(SCRIPT_REL)).body if isinstance(n, ast.FunctionDef) and n.name == "run_regress97"][0]
        seg = ast.get_source_segment(read(SCRIPT_REL), fn)
        for needle in (u"XR.doc_job", u"XR.doc_rows(", u"XR.engine_commits()", u"XR.engine_link()", u"doc_moves_pb(", u"regress_block(", u"message_numbers(", u"engine_numstat()",
                       u"write_record(", u"R97.make_jobs(", u"R97.run_pool("):
            self.assertIn(needle, seg, needle)
            self.assertNotIn(needle, seg.replace(needle, u"", 1), needle)                         # 1 回だけ使う(2 重に数えていない)
        self.assertIn(u"E-1・E-8 engine の差分", seg)
        self.assertIn(u"E-7・E-9 の写し", seg)


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
    def test_h_1_the_three_records_are_declared_as_naming_files(self):
        src = read("tests/measure/test_xbrl_fresh_seal.py")
        self.assertEqual([], naming_problems(src))
        for rel in REC_REL.values():
            self.assertNotEqual([], naming_problems(src.replace('"%s"' % rel, '"x/%s"' % rel)), rel)
        self.assertNotEqual([], naming_problems(src.replace("LATER_NAMING_FILES", "LATER_NAMING_FILE")))
        last = list(REC_REL.values())[-1]
        self.assertNotEqual([], naming_problems(src.replace('"%s"' % last, '"%s", "%s"' % (last, SG.GATE_RELS[0]))))

    def test_h_2_the_previous_declarations_are_still_there(self):
        got = later_naming_files(read("tests/measure/test_xbrl_fresh_seal.py"))
        for rel in ("fixtures/xbrl/rmix/ai200_2026-11-04.json", "fixtures/xbrl/rmix/regress97_2026-11-04.json", "fixtures/xbrl/pswap/inject_2026-11-06.json", "fixtures/xbrl/pswap/inject_idmap_2026-11-06.json",
                    "fixtures/xbrl/jtypes/inject_2026-11-05.json"):
            self.assertIn(rel, got)

    def test_h_3_the_script_is_declared_as_a_harness_file(self):
        src = read("tests/measure/test_xbrl_inject_harness_review.py")
        self.assertEqual([], harness_problems(src))
        self.assertNotEqual([], harness_problems(src.replace(u'"%s"' % SCRIPT_REL, u'"x/%s"' % SCRIPT_REL)))
        self.assertNotEqual([], harness_problems(src.replace("LATER_HARNESS_FILES", "LATER_HARNESS_FILE")))
        self.assertIn("measure/xbrl_pswap_idmap_2026-11-06.py", src)


# ================================================================ 順序(e)の変異(使い捨ての repo)
OTHERS = list(REC_REL.values()) + [DOC_REL]
IMPLS = list(ENGINE_FILES)


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

    def test_e_2_records_before_the_seal_before_the_engine_or_uncommitted_are_red(self):
        r, s = self._repo(commit_others=[])
        self.assertEqual(sorted("UNCOMMITTED:" + o for o in OTHERS), sorted(self.probe(r, s)))
        r2, s2 = self._repo(before_seal=[OTHERS[0]], commit_others=OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], self.probe(r2, s2))
        r3, s3 = self._repo(after_seal=[OTHERS[0]], commit_others=OTHERS[1:])
        self.assertIn("BEFORE_IMPL:" + OTHERS[0], self.probe(r3, s3))
        r4, s4 = self._repo(commit_impl=False)
        self.assertTrue(any(p.startswith("IMPL_UNCOMMITTED:") for p in self.probe(r4, s4)))

    def test_e_3_order_of_uses_the_two_engine_files_the_records_and_the_document(self):
        r, s = self._repo()
        self.assertEqual([], order_of(r.d, s[:7]))
        r2, s2 = self._repo(commit_others=OTHERS[:-1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[-1]], order_of(r2.d, s2[:7]))
        r3, s3 = self._repo(commit_impl=False)
        self.assertTrue(any(x.startswith("IMPL_UNCOMMITTED:") for x in order_of(r3.d, s3[:7])))
        self.assertEqual(list(SG.ENGINE_FILES), IMPLS)
        self.assertEqual(3, len(REC_REL))

    def test_e_4_a_wrong_seal_is_red(self):
        r, _s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", PR.order_problems(r.d, PREFIX, SEAL_REL, "abcdef0", IMPLS, OTHERS))

    def test_e_5_the_engine_fingerprint_comes_from_the_tree_at_the_engine_commit(self):
        fp = engine_fingerprint_at_commit()
        self.assertEqual(2, len(fp))
        for v in fp.values():
            self.assertRegex(v, r"^[0-9a-f]{64}$")
        self.assertEqual(SGR.PB_FP, fp["adapter_xbrl_py_sha256"])                                 # 全 file の束ねた指紋は PB の宣言した値(engine の commit の木と一致)


# ================================================================ 本番の記録(a)(b)(d)(e)
class RealRecordsTest(unittest.TestCase):
    u"""記録が無いときは各試験が skip する(skip でも行が出ることは SkipLineTest が確かめる)。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def need(self):
        if not records_exist():
            self.skipTest(u"記録が無い(動いた行・97 書類・注入を走らせた後に走る)")
        return load_records()

    def test_r_1_records_are_clean_and_consistent(self):
        R = self.need()
        self.assertEqual([], record_problems(copy.deepcopy(R), full=True))

    def test_r_2_judgment_is_rebuilt_from_the_records(self):
        R = self.need()
        self.assertEqual([], judge_problems(R, self.seal))
        J = PB.build_E(R, self.seal)
        self.assertEqual(set(J), {u"E", u"K", u"採用", u"欄"})

    def test_r_3_the_result_document_follows_the_records(self):
        R = self.need()
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), R, self.seal))

    def test_r_4_order_is_seal_then_engine_then_records_and_document(self):
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


# ================================================================ 実書類を 1 件だけ通す使い捨ての走り(cache を読むだけ。記録は TMPDIR の下。cache が無ければ skip)
class RealRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HAVE_CACHE:
            raise unittest.SkipTest(u"cache が無い(実書類を通す試験は skip)")
        cls.doc = PI.load_books(ROOT, None)[0][2][u"docID"]

    def test_x_1_regress97_one_document_passes_the_record_checks(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            out = os.path.join(d, "r97.json")
            rec = norm(PB.run_regress97(root=ROOT, procs=1, only=self.doc, out=out, say=lambda *a: None))
            self.assertEqual(rec, jload_abs(out))
        self.assertEqual(u"**--only の 1 書類だけ(本番の記録ではない)**", rec[u"範囲"])
        self.assertEqual([], regress97_problems(rec, False))
        self.assertEqual([], header_problems("regress97", rec, False))
        self.assertEqual([], clean_problems("regress97", rec))
        self.assertEqual(1, len(rec[u"書類"]))
        self.assertTrue(all(v[u"byte が同じ書類"] == 1 for v in rec[u"集計"][u"E-2 旗が偽の profile の byte 一致"].values()))      # 旗が偽の 9 profile は RB の便の記録と byte 一致
        self.assertEqual(norm(link_at_history()), rec[u"E-1・E-8 engine の差分"])

    def test_x_2_inject_one_document_reproduces_the_t9_p30e_cells(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            out = os.path.join(d, "inj.json")
            rec = norm(PB.run_inject(root=ROOT, procs=1, only=self.doc, out=out, say=lambda *a: None, work_root=d))
        t9 = t9_record()[u"行"]
        self.assertEqual([], inject_problems(rec, t9, False)[:0] + [x for x in inject_problems(rec, t9, False) if u"E の欄" in x or u"集計" in x or u"切り替え" in x])
        self.assertEqual([], header_problems("inject", rec, False))
        self.assertEqual([], clean_problems("inject", rec))
        rows = rec[u"行"]
        self.assertGreater(len(rows), 0)
        by_id = dict((r[u"id"], r) for r in t9)
        for r in rows:
            self.assertIn(r[u"id"], by_id)                                                       # 行の id は T9 の第 2 便の記録と同じ
            self.assertEqual(norm(by_id[r[u"id"]]["P30E"]), norm(r["P30E"]))                      # P30E の結果と state も同じ(E-2)
            self.assertEqual(by_id[r[u"id"]][u"engine の手がかり"], r[u"engine の手がかり"])
        c = rec[u"E の欄"][u"E-2 T9 の第 2 便の記録との照らし"]
        self.assertEqual(len(rows), c[u"P30E の結果と state が T9 の第 2 便の記録と同じ行"])

    def test_x_3_moves_one_book_passes_the_record_checks(self):
        real_load = RM.load_jobs
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(RM, "load_jobs", lambda root=ROOT, only=None: real_load(root, only)[:1])
            out = os.path.join(d, "mv.json")
            rec = norm(PB.run_moves(root=ROOT, procs=1, only=self.doc, out=out, say=lambda *a: None))
        self.assertEqual(1, len(rec[u"本"]))
        self.assertEqual([], moves_problems(rec, False))
        self.assertEqual([], header_problems("moves", rec, False))
        self.assertEqual([], clean_problems("moves", rec))
        self.assertEqual(norm(PB.aggregate_moves(rec[u"本"])), rec[u"集計"])


def jload_abs(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    unittest.main()
