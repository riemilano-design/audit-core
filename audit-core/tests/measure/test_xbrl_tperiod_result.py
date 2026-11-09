# -*- coding: utf-8 -*-
"""規則 T(表の見出しの「前期」の列の数を前期の手がかりがある数として扱う。P33E = P32E + 旗。既定にしない)の測定の結果の門。封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md §3・§4・§5。

記録 3 つ(``fixtures/xbrl/tperiod/``: moves_200・regress97・inject)と、読むだけの **PB の便の記録**(``fixtures/xbrl/pbind/inject_2026-11-06.json`` = T-2 の 141 行の比べ先)から、封 §3 の予測 T-1〜T-10 と
§4 の採用の基準 K-1〜K-5 を**機械で求め**(予測の幅は封の字から読む。字のコピーにしない)、結果の文書 ``docs/XBRL_TABLE_PERIOD_ENGINE_RESULT_2026-11-09.md`` の表
(``<!-- 門:start pred -->``・``<!-- 門:start judge -->`` の中)を記録から作り直した表と一行も違わないことを見る。測定の script(``measure/xbrl_tperiod_2026-11-09.py`` の ``build_E``・``judge_from``・
``columns_from_records``・``render_pred``・``render_judge``)の関数を呼んで照らす。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文・pointer・要素など)が無い・pointer の字(要素名・context)を持たない・key_leaks が空・docID を持つ記録が ``LATER_NAMING_FILES`` に宣言され、
     script が ``LATER_HARNESS_FILES`` に宣言されている(宣言は記録を走らせる便の仕事。いまの宣言の状態を試験が見る)・cache の前後が同じ・script と lib と前の便(PB・RB・T9 の第 2 便・T9)の script・
     入力の記録の sha256 が現物と一致・engine の指紋が engine の commit の木から作り直した値と一致・engine の commit が履歴から探した値と一致する。
  b  記録の中身が再計算と一致する: 本の整合(動いた行の中身と GROUNDED の増減・札・表の前期の列の数か)・書類の整合・注入の行の整合(a の対応と b の TP・TC の対)・集計・
     **判定に使う欄の全部を 行・本・書類から数え直す**(欄を 0 に固定すると赤。行の欄を 1 つ変えると該当の欄が動く)・T-1・T-9(git の履歴から)・T-8・T-10 の写し(engine の commit の message から)。
  c  判定: 記録(の欄)を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。採用は K-1〜K-5 を全部満たすときだけ。判定は記録の集計でなく行・本・書類から求める。
     **PB の記録を壊した写し**(id を 1 つ変える・P32E の state を 1 つ変える)で T-2 と K-1 が赤になる。
  d  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 eb281f1 ⊏ engine を触った commit ⊏ 記録・結果の文書(script・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  g  変異: 小さい標本の記録 3 つと文書で同じ検査が緑 → 変異(記録の数・欄・表の 1 字・封の予測の 1 字・順序・記録の禁止欄・指紋の 1 字・cache の前後・pointer の字・期の欄・表の前期の列か)で赤。
  w  手順: script の ``judge_book_t``・``doc_job_t``・``table_book``・``table_sites`` を小さい入力(合成の claim。lib は本物)で通し、表の前期の列か・TP・TC の site の条件・対応の条件を
     壊した差し替えで True ↔ False が替わる例で固定する。

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
    u"""importlib で読み込む。読み込んだ file が中で読む前の便の script は、決まった名前で ``sys.modules`` に登録し直して**先に居た module を上書きする**
    (RB の ``numfix_regress97_for_rmix`` など。``--procs 2`` の pickle は名前で引く)。読み込みの前に居た名前は、読み込みの後に元の object へ戻す
    (さもないと pytest の引数で RB・PB・T5Y の結果の門を先に並べたとき、先に読まれた門が持つ object と ``sys.modules`` の object が別になって赤くなる。7109c97 の直しと同じ形)。
    読み込んだ module 自身の名前 ``name`` は残す。"""
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


SG = load_module("tests/measure/test_xbrl_tperiod_seal.py", "tperiod_seal_gate_for_result")               # 封の門の部品。門としては走らせない
PSR = load_module("tests/measure/test_xbrl_pswap_result.py", "pswap_result_gate_for_tperiod_result")      # T9 の結果の門の部品(禁止欄・語・差し替え)。門としては走らせない
TP = SG.TPR
SGR = SG.SGR
PR = SG.PR
PB, RM, RR, PI, PS, XR = TP.PB, TP.RM, TP.RR, TP.PI, TP.PS, TP.XR
NF, GEN, RUN, TUNE = TP.NF, TP.GEN, TP.RUN, TP.TUNE
E_, V = TP.R, TP.V

SEAL_REL = TP.SEAL_REL
DOC_REL = TP.DOC_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = TP.SCRIPT_REL
REC_REL = collections.OrderedDict(TP.REC_REL)
ENGINE_FILES = SG.ENGINE_FILES
NOT_GATED = PR.NOT_GATED
HIT, MISS = TP.HIT, TP.MISS
FORBIDDEN_KEYS = PSR.FORBIDDEN_KEYS
COMPANY_WORDS = PSR.COMPANY_WORDS
POINTER_TEXT_RE = PSR.POINTER_TEXT_RE
DOCID_RE = SG.DOCID_RE
FOR_RESULT_WORDS = PSR.FOR_RESULT_WORDS
HAVE_CACHE = all(os.path.isdir(p) for p in PI.caches_all().values())
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
PERIODS5 = TP.PERIODS5
LABEL_WORDS = TP.LABEL_WORDS
NO_LABEL = TP.NO_LABEL
EXISTING, NEWROW = TP.EXISTING, TP.NEWROW
SECTION_A, SECTION_B = TP.SECTION_A, TP.SECTION_B
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
#: 封 §3・§4 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("T-1", collections.OrderedDict([(u"recipes 挿入", (45, 75)), (u"recipes 削除", 0), (u"vocabulary 挿入", (3, 6)), (u"vocabulary 削除", 0), (u"他の file", 0)])),
    ("T-2", collections.OrderedDict([(u"byte が同じ書類", 97), (u"書類", 97), (u"P33E の結果と state が同じ行", 141), (u"行", 141)])),
    ("T-3", collections.OrderedDict([(u"行頭が | の文", 0), (u"動いた行", 0), (u"GROUNDED を失う行", 0)])),
    ("T-4", collections.OrderedDict([(u"動いた行", (380, 400)), (u"表の前期の列の数でない動いた行", 0), (u"GROUNDED を失う行", 0), (u"GROUNDED の数の増え", (350, 380))])),
    ("T-5", collections.OrderedDict([(u"VALUE_MISMATCH → GROUNDED の札 真", (270, 295)), (u"札 偽の行が GROUNDED になった行", 0)])),
    ("T-6", collections.OrderedDict([(u"site", (360, 390)), (u"P32E が通した率", (90, 100)), (u"P33E が通した率", (0, 3)), (u"名指した割合", (95, 100))])),
    ("T-7", (0, 3)),
    ("T-8", collections.OrderedDict([(u"赤", 10), (u"変異の本数", 10)])),
    ("T-9", (40, 80)),
    ("T-10", collections.OrderedDict([(u"赤の試験", [u"axis3 test_9"]), (u"ほかの赤", 0)])),
    ("K-1", (97, 97, 141, 141)), ("K-2", (0, 0)), ("K-3", (0, 0)),
    ("K-4", collections.OrderedDict([(u"P33E の通した率の上限", 3), (u"P32E の通した率の下限", 90)])),
    ("K-5", collections.OrderedDict([(u"赤", 10), (u"変異の本数", 10)]))])
#: 記録の限界の字の頭(literal に留める。script の字を変えたら赤)
LIMITS_PIN = collections.OrderedDict([
    ("moves", (u"通した・止めたは engine の state で、動いた行の札は前の便の盲検の 1 席目", u"200 本は Claude の model 2 つが書いた文。表は F3 の 40 本だけ", u"表の前期の列の数か = engine の _table_prior_keys_2026_11_09")),
    ("regress97", (u"97 書類は 2026 年提出の有報に偏る", u"札が無いので動いた行の正しさは見ていない")),
    ("inject", (u"(a) は T9 の 1 型だけ", u"(b) の TP・TC は司令塔が作った新しい注入", u"通した・止めたは engine の state で、札(人の目)は無い"))])
#: 行の欄の名前と並び
A_ROW_KEYS = (u"docID", u"form", u"model", u"writer", u"id", u"型", u"形", u"基準の claim", u"P33E の土台に対応", u"round-trip", u"読み直し", u"engine の手がかり", u"窓の手がかり", u"文に前期の語",
              u"基準の pointer の期", "P30E", "P33E", u"P30E の注入後の pointer の期", u"P33E の注入後の pointer の期", u"P30E の欠けた条件", u"P33E の欠けた条件")
A_CELL_KEYS = (u"対応", u"結果", u"state", u"reason")
B_ROW_KEYS = (u"docID", u"id", u"形", u"model", u"型", "P32E", "P33E")
B_CELL_KEYS = (u"対応", u"state", u"期", u"結果")
RESULT_LABELS = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
B_RESULT_WORDS = (TP.PASSED_WORD, TP.NAMED_PRIOR_WORD, TP.NAMED_OTHER_WORD, U_, P_, TP.UNMAPPED_WORD)
SHAPES = PS.SHAPES
CONDS = PI.CONDS
NO_BASE = PI.NO_BASE
#: 記録の頭が写す入力の記録・script(測定の script が header_t に渡す path とは別に、門が literal で持つ)
PB_REGRESS97_REL = "fixtures/xbrl/pbind/regress97_2026-11-06.json"
PB_INJECT_REL = "fixtures/xbrl/pbind/inject_2026-11-06.json"
PREV_SCRIPT_RELS = ("measure/xbrl_pbind_2026-11-06.py", "measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py", "measure/xbrl_pswap_idmap_2026-11-06.py", "measure/xbrl_pswap_2026-11-06.py")
LIB_RELS = tuple(PI.LIB_RELS)
LIMIT_BOOK_FORM = "F3"


def records_exist():
    if FORCE["no_records"]:
        return False
    return all(os.path.exists(os.path.join(ROOT, v)) for v in REC_REL.values())


_FIXED = {}


def pb_inject_record():
    u"""読むだけの PB の便の inject の記録(1 回だけ読む)。"""
    if not _FIXED:
        _FIXED["pb"] = jload(PB_INJECT_REL)
    return _FIXED["pb"]


def load_records():
    out = collections.OrderedDict((k, jload(v)) for k, v in REC_REL.items())
    out["pb_inject"] = pb_inject_record()
    return out


def input_rels(kind):
    u"""記録の頭の ``入力の記録の sha256`` が持つべき path の列(門が literal から作る)。"""
    if kind == "moves":
        rels = []
        for src, p in TP.SOURCES.items():
            rels += [p["gen"], p["claims"]]
        return rels + list(TP.LABELS_REL.values()) + ["fixtures/xbrl/numfix/ai200_2026-11-04.json"]
    if kind == "regress97":
        return [PB_REGRESS97_REL]
    return [PB_INJECT_REL] + [p["gen"] for p in TP.SOURCES.values()]


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
            a, _na = TP.VD._py_digest(os.path.join(d, PREFIX, "adapters", "xbrl"))
            c, _nc = TP.VD._py_digest(os.path.join(d, PREFIX, "core", "py", "audit_core"))
        _FP.append({"adapter_xbrl_py_sha256": a, "core_py_sha256": c})
    return _FP[0]


def link_at_history():
    u"""T-1・T-9 の欄を履歴から作り直す(測定の script とは別に書く)。"""
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
        got = TP.seal_bounds(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return [u"封から幅を読めない(%s)" % type(e).__name__]
    for k, v in BOUNDS_PIN.items():
        g = got.get(k)
        if json.dumps(norm_t(g) if not isinstance(g, (str, list)) else g, sort_keys=True) != json.dumps(norm_t(v) if not isinstance(v, (str, list)) else v, sort_keys=True):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, g, v))
    if list(TP.seal_pred_rows(seal)) != list(SG.PRED_IDS) or list(TP.seal_k_rows(seal)) != list(SG.K_IDS):
        out.append(u"封の予測の行が T-1〜T-10・K の行が K-1〜K-5 でない")
    return out


# ---------------------------------------------------------------- 記録(a)(b)
def header_problems(k, rec, full):
    u"""記録の頭(封・script・lib・前の便の script と記録・engine・cache)。k = moves / regress97 / inject。"""
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
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
    want_profile = list(TP.NOW_PROFILES) if k == "regress97" else (list(TP.PROFILES) if k == "moves" else list(TP.PROFILES) + [TP.BASE_OLD])
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
    u"""moves の動いた行の中身 [種類, 文の番号, 位置, 前の state, 後の state, 前の期, 後の期, 札, 既存 / 新, 前期の fact が無い要素, 表の前期の列の数か]。"""
    return (isinstance(x, list) and len(x) == 11 and x[0] == u"num" and isinstance(x[1], int) and isinstance(x[2], int) and not isinstance(x[1], bool) and not isinstance(x[2], bool)
            and x[3] in TP.STATES and x[4] in TP.STATES and x[5] in PERIODS5 and x[6] in PERIODS5 and x[7] in (None,) + LABEL_WORDS and x[8] in (EXISTING, NEWROW)
            and (x[8] == EXISTING or x[7] is None) and isinstance(x[9], bool) and isinstance(x[10], bool))
    # PB の便の門にあった「前期の fact が無い要素なら期は Prior1Year でない」は置かない: 前期の fact が無い要素の欄は Prior1Year の **JPY** の fact が無いことで、表の % の行は
    # Prior1Year の fact(単位が pure)に結ばれるので、欄が真で期が Prior1Year の行が在る(測定の便の使い捨ての 1 本で見つかった。PB の 97 書類では起きなかった仮定)


def book_problems(b):
    u"""本ごとの整合(自分の欄の間の関係)。"""
    out = []
    nm = b[u"name"]
    n, gr, ent = b[u"数の claim の数"], b[u"GROUNDED の数"], b[u"動いた行の中身"]
    if list(b[u"対応"]) != list(TP.PROFILES) or list(n) != list(TP.PROFILES) or list(gr) != list(TP.PROFILES):
        out.append(u"%s: 対応・数の claim の数・GROUNDED の数の profile が (P32E, P33E) でない" % nm)
    if any(not isinstance(v, bool) for v in b[u"対応"].values()):
        out.append(u"%s: 対応が真偽でない" % nm)
    if b[u"P30E と P32E で数の claim の鍵が同じ"] and n["P32E"] != n["P33E"]:
        out.append(u"%s: 鍵が同じなのに P32E と P33E の数の claim の数が違う" % nm)
    if gr["P32E"] > n["P32E"] or gr["P33E"] > n["P33E"]:
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
    if b[u"P30E と P32E で数の claim の鍵が同じ"] and gr["P33E"] - gr["P32E"] != gained - lost:
        out.append(u"%s: GROUNDED の増減が なった行 − 失った行 と合わない" % nm)
    if not isinstance(b[u"P27 の鍵が一意"], bool) or not isinstance(b[u"reason だけが違う行"], int) or b[u"reason だけが違う行"] < 0:
        out.append(u"%s: P27 の鍵が一意・reason だけが違う行の型がおかしい" % nm)
    bars, tab = b.get(u"行頭が | の文の数"), b.get(u"表の前期の列の数")
    if not (isinstance(bars, int) and isinstance(tab, int) and not isinstance(bars, bool) and not isinstance(tab, bool) and bars >= 0 and tab >= 0):
        out.append(u"%s: 行頭が | の文の数・表の前期の列の数の型がおかしい" % nm)
    else:
        if tab > 0 and bars == 0:
            out.append(u"%s: 表の前期の列の数があるのに行頭が | の文が無い" % nm)
        if tab == 0 and any(x[10] is True for x in ent if isinstance(x, list) and len(x) == 11):
            out.append(u"%s: 表の前期の列の数が 0 なのに表の前期の列の数の動いた行がある" % nm)
    return out


def moves_problems(rec, full):
    out = []
    books = rec[u"本"]
    for b in books:
        out += book_problems(b)
    try:
        agg = norm(TP.aggregate_moves_t(books))
    except Exception as e:                                   # noqa: BLE001  壊れた記録は集計できない = 赤
        return out + [u"moves: 本から集計を作れない(%s)" % type(e).__name__]
    if agg != rec[u"集計"]:
        out.append(u"moves: 集計が本から作り直した値と違う")
    if not all(all(b[u"対応"].values()) for b in books):
        out.append(u"moves: claim の並びが profile 間で対応しない本がある")
    if full:
        prior = []
        for src, p in TP.SOURCES.items():
            c = jload(p["claims"])
            prior += [(src, b) for b in c[u"本"] if not b.get(u"欠け")]
        if [(b[u"材料"], b[u"name"], b[u"docID"], b[u"form"], b[u"model"]) for b in books] != [(s, b[u"name"], b[u"docID"], b[u"form"], b[u"model"]) for s, b in prior]:
            out.append(u"moves: 本の並びが前の便の claims の記録の本(160 + 40)と違う")
        if len(books) != 200:
            out.append(u"moves: 本が 200 本でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(RM.caches_all())):
            out.append(u"moves: cache の件数か名前が記録の前と違う")
    return out


def doc_problems_one(d):
    u"""書類 1 つの整合(動いた行の欄と XR の定義の行・4 state・claim の数・行頭が | の文)。"""
    out = []
    nm = d[u"docID"]
    mv = d[u"動いた行と象えた行".replace(u"象", u"増")][TP.PAIRS[0][0]]
    ents, xr = d[u"P33E の動いた行"], mv[u"動いた既存の行"]
    if sorted(d[u"claims"]) != sorted(TP.NOW_PROFILES) or sorted(d[u"4 state"]) != sorted(TP.NOW_PROFILES) or sorted(d[u"出力の sha256(engine の欄を除く)"]) != sorted(TP.NOW_PROFILES):
        out.append(u"%s: profile の欄が NOW_PROFILES でない" % nm)
    if sorted(d[u"前の便の記録の sha256"]) != sorted(TP.BASE_PROFILES):
        out.append(u"%s: 前の便の記録の sha256 の profile が PB の便の記録の 10 でない" % nm)
    for x in ents:
        if not (isinstance(x, list) and len(x) == 11 and x[0] in (u"num", u"text") and all(isinstance(v, int) and not isinstance(v, bool) for v in x[1:4])
                and x[4] in TP.STATES and x[5] in TP.STATES and x[6] in PERIODS5 and x[7] in PERIODS5 and isinstance(x[8], bool) and isinstance(x[9], bool) and isinstance(x[10], bool)):
            out.append(u"%s: P33E の動いた行の形がおかしい" % nm)
            continue
        if x[8] != (x[4] != x[5]) or not (x[8] or x[9]):
            out.append(u"%s: P33E の動いた行の state が違う・pointers が違う の欄が合わない" % nm)
    keys = [tuple(x[:4]) for x in ents]
    if len(keys) != len(set(keys)):
        out.append(u"%s: 動いた行の鍵が重なっている" % nm)
    if len(xr) != len(ents) + d[u"reason だけが違う行"]:
        out.append(u"%s: XR の定義の動いた行が 動いた行 + reason だけが違う行 と合わない" % nm)
    if sum(mv[u"増えた行の state"].values()) != mv[u"増えた行"] or d[u"claims"][TP.NEW] - d[u"claims"][TP.OLD] != mv[u"増えた行"] - mv[u"消えた行"]:
        out.append(u"%s: 増えた行・消えた行が claim の数の差と合わない" % nm)
    g = lambda p: d[u"4 state"][p][G]            # noqa: E731
    if mv[u"増えた行"] == 0 and mv[u"消えた行"] == 0:
        lost = sum(1 for x in ents if x[4] == G and x[5] != G)
        gained = sum(1 for x in ents if x[4] != G and x[5] == G)
        if g(TP.NEW) - g(TP.OLD) != gained - lost:
            out.append(u"%s: GROUNDED の増減が なった行 − 失った行 と合わない" % nm)
    bars, tab = d.get(u"行頭が | の文の数"), d.get(u"表の前期の列の数")
    if not (isinstance(bars, int) and isinstance(tab, int) and not isinstance(bars, bool) and not isinstance(tab, bool) and bars >= 0 and tab >= 0):
        out.append(u"%s: 行頭が | の文の数・表の前期の列の数の型がおかしい" % nm)
    elif tab > 0 and bars == 0:
        out.append(u"%s: 表の前期の列の数があるのに行頭が | の文が無い" % nm)
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
        T = norm(TP.regress_block_t(docs))
    except Exception as e:                                   # noqa: BLE001
        return out + [u"regress97: 書類から集計を作れない(%s)" % type(e).__name__]
    if T != rec[u"集計"]:
        out.append(u"regress97: 集計が書類から作り直した値と違う")
    link = rec.get(u"T-1・T-9 engine の差分") or {}
    cp = rec.get(u"T-8・T-10 の写し") or {}
    if full:
        prev = dict((r["docID"], r) for r in jload(PB_REGRESS97_REL)[u"書類"])
        if sorted(d[u"docID"] for d in docs) != sorted(prev):
            out.append(u"regress97: 書類が PB の便の記録の 97 書類と違う")
        for d in docs:
            pr = prev.get(d[u"docID"])
            if pr is None:
                continue
            if d[u"前の便の記録の sha256"] != dict((p, pr[u"出力の sha256(engine の欄を除く)"][p]) for p in TP.BASE_PROFILES) or d[u"zip の sha256"] != pr[u"zip の sha256"]:
                out.append(u"regress97: 前の便の記録の sha256 か zip の sha256 が PB の便の記録と違う")
        if len(docs) != 97:
            out.append(u"regress97: 書類が 97 でない")
        if norm(link) != norm(link_at_history()):
            out.append(u"regress97: T-1・T-9 が git の履歴から作り直した値と違う")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(collections.OrderedDict((k, TP.R97.prec().names_sha(v)) for k, v in TP.R97.CACHES.items())):
            out.append(u"regress97: cache の件数か名前が記録の前と違う")
    out += copy_problems(cp, full)
    if not isinstance(link.get(u"numstat"), dict):
        out.append(u"regress97: T-1・T-9 に numstat が無い")
    return out


def copy_problems(cp, full):
    u"""T-8・T-10 の写しの形。full なら engine の commit の message から読み直した値と同じか。"""
    out = []
    if set(cp) != {u"出どころ", u"engine の commit", "T-8", "T-10"}:
        return [u"regress97: T-8・T-10 の写しの欄が違う"]
    if full:
        want = norm(TP.message_numbers_t(engine_message_at_history()))
        if cp["T-8"] != want["T-8"] or cp["T-10"] != want["T-10"] or cp["T-8"] is None or cp["T-10"] is None:
            out.append(u"regress97: T-8・T-10 の写しが engine の commit の message から読み直した値と違う")
        if cp[u"engine の commit"] != engine_commit_full()[1]:
            out.append(u"regress97: 写しの engine の commit が履歴から探した値と違う")
    return out


def a_cell_problems(r, p):
    u"""(a) の行の profile p の欄(結果の語・対応・欠けた条件・期)。"""
    out = []
    cell, miss, per = r[p], r.get(u"%s の欠けた条件" % p), r.get(u"%s の注入後の pointer の期" % p)
    if list(cell) != list(A_CELL_KEYS) or cell[u"結果"] not in RESULT_LABELS or not isinstance(cell[u"対応"], bool):
        return [u"%s の欄の形がおかしい" % p]
    if (cell[u"結果"] == TUNE.LABEL_UNMAPPED) != (cell[u"対応"] is False):
        out.append(u"%s の欄の対応と結果が合わない" % p)
    if cell[u"対応"] is False and (cell[u"state"] is not None or cell[u"reason"] is not None):
        out.append(u"%s の欄が対応なしなのに state がある" % p)
    if cell[u"対応"] is True and cell[u"state"] not in TP.STATES:
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
    if miss == [NO_BASE] and (p != TP.NEW or per != u"なし"):
        out.append(u"%s: 土台なしは P33E の土台に対応が付かない行だけ・期は なし" % p)
    return out


def a_row_problems(r, seen):
    out = []
    if list(r) != list(A_ROW_KEYS):
        return [u"(a) 行の欄の並びが違う"]
    if r[u"型"] != PB.T9:
        out.append(u"(a) 型が T9_PRIOR_TO_CURRENT でない")
    if r[u"id"] in seen:
        out.append(u"(a) 同じ注入の id が 2 回ある")
    seen.add(r[u"id"])
    if not r[u"id"].startswith(u"%s_%s_%s-T9-" % (r["docID"], r["form"], r["model"])):
        out.append(u"(a) id が本の名前 + T9 の形でない")
    for key in (u"P33E の土台に対応", u"round-trip", u"読み直し", u"engine の手がかり", u"窓の手がかり", u"文に前期の語"):
        if not isinstance(r.get(key), bool):
            out.append(u"(a) 行の %s が真偽でない" % key)
    if r[u"形"] not in SHAPES:
        out.append(u"(a) 行の形が語でない")
    if r[u"基準の pointer の期"] not in PS.PERIODS:
        out.append(u"(a) 基準の pointer の期が語でない")
    for p in ("P30E", "P33E"):
        out += a_cell_problems(r, p)
    if r[u"P33E の土台に対応"] is False and norm(r["P33E"]) != {u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}:
        out.append(u"(a) P33E の土台に対応が無い行の P33E の欄が対応なしでない")
    if r[u"P33E の土台に対応"] is True and r["P33E"][u"対応"] is False and r[u"P33E の欠けた条件"] == [NO_BASE]:
        out.append(u"(a) P33E の土台に対応があるのに 土台なし")
    return out


def b_cell_problems(c, p):
    u"""(b) の行の profile p の欄 {対応, state, 期, 結果}。結果は state と期から決まる語。"""
    if not isinstance(c, dict) or list(c) != list(B_CELL_KEYS) or not isinstance(c[u"対応"], bool):
        return [u"(b) %s の欄の形がおかしい" % p]
    out = []
    if c[u"期"] not in PERIODS5:
        out.append(u"(b) %s の期が語でない" % p)
    if c[u"対応"] is False and (c[u"state"] is not None or c[u"期"] != u"なし"):
        out.append(u"(b) %s の欄が対応なしなのに state か期がある" % p)
    if c[u"対応"] is True and c[u"state"] not in TP.STATES:
        out.append(u"(b) %s の欄の state が 4 つの語でない" % p)
    if c[u"結果"] not in B_RESULT_WORDS or c[u"結果"] != TP.result_word(c):
        out.append(u"(b) %s の欄の結果が state と期から決まる語と違う" % p)
    return out


def b_row_problems(r, seen):
    out = []
    if list(r) != list(B_ROW_KEYS):
        return [u"(b) 行の欄の並びが違う"]
    if r[u"型"] not in (TP.TP, TP.TC):
        out.append(u"(b) 型が TP・TC でない")
    if r[u"id"] in seen:
        out.append(u"(b) 同じ注入の id が 2 回ある")
    seen.add(r[u"id"])
    if not re.match(r"^%s_%s_%s-TT-\d{3}-%s$" % (re.escape(r["docID"]), re.escape(r[u"形"]), re.escape(r["model"]), r[u"型"]), r[u"id"]):
        out.append(u"(b) id が 本の名前 + TT + 番号 + 型 の形でない")
    for p in TP.PROFILES:
        out += b_cell_problems(r[p], p)
    return out


def inject_problems(rec, pb_rows, full):
    out = []
    rows_a, rows_b = rec[u"行"][SECTION_A], rec[u"行"][SECTION_B]
    seen = set()
    cnt = collections.Counter()
    for r in rows_a:
        try:
            out += a_row_problems(r, seen)
        except Exception as e:                               # noqa: BLE001
            out.append(u"inject: (a) の行を検査できない(%s)" % type(e).__name__)
            continue
        cnt[(r["docID"], r["form"], r["model"])] += 1
    if any(n > RUN.INJECT_CAP for n in cnt.values()):
        out.append(u"inject: (a) の 1 本あたりの上限 %d を超えている" % RUN.INJECT_CAP)
    seen_b = set()
    for r in rows_b:
        try:
            out += b_row_problems(r, seen_b)
        except Exception as e:                               # noqa: BLE001
            out.append(u"inject: (b) の行を検査できない(%s)" % type(e).__name__)
    ids_b = collections.Counter(re.sub(r"-(TP|TC)$", u"", r[u"id"]) for r in rows_b if isinstance(r.get(u"id"), str))
    per_book_b = rec[SECTION_B][u"本ごとの数え"]
    if any(n != 2 for n in ids_b.values()) or collections.Counter(r[u"型"] for r in rows_b)[TP.TP] != collections.Counter(r[u"型"] for r in rows_b)[TP.TC]:
        out.append(u"inject: (b) の site ごとに TP と TC が 1 行ずつでない")
    if len(ids_b) != sum(c[u"採った site"] for c in per_book_b.values()):
        out.append(u"inject: (b) の site の数が 本ごとの数え の 採った site の合計と違う")
    for name, c in per_book_b.items():
        if c[u"採った site"] != (c[u"site 候補(見出しの前期 1 列・当期 1 列・セルに数 1 つずつ)"] - c[u"土台が合わない"] - c[u"2 つのセルの字が同じ"] - c[u"行の字が文に 1 回でない"]):
            out.append(u"inject: (b) %s の 採った site が 候補 − 除いた行 と合わない" % name)
    if rec[SECTION_A][u"注入の行の数"] != len(rows_a) or rec[SECTION_B][u"注入の行の数"] != len(rows_b):
        out.append(u"inject: 注入の行の数が行の数と違う")
    try:
        if norm(TP.inject_summary_t(rows_b)) != rec[SECTION_B][u"集計"]:
            out.append(u"inject: (b) の集計が行から作り直した値と違う")
        if norm(TP.inject_columns_t(rows_a, rows_b, pb_rows)) != rec[u"集計の欄"]:
            out.append(u"inject: 集計の欄が行と PB の記録から数え直した値と違う")
    except Exception as e:                                   # noqa: BLE001
        out.append(u"inject: 集計・集計の欄を作れない(%s)" % type(e).__name__)
    sw = rec.get(u"切り替え") or {}
    if sw.get(u"名前") != PI.FLAG or sw.get(u"配線の問題") != [] or sw.get(u"(a) の inject の中の値") is not True or sw.get(u"出たあとの値") is not False:
        out.append(u"inject: 切り替えの欄が違う")
    if full:
        pbids = set(r[u"id"] for r in pb_rows)
        if set(r[u"id"] for r in rows_a) - pbids:
            out.append(u"inject: PB の記録に無い id が (a) にある")
        names = [b[u"name"] for src in TP.SOURCES.values() for b in jload(src["claims"])[u"本"] if not b.get(u"欠け")]
        if list(rec[SECTION_A][u"本ごとの数え"]) != names or list(per_book_b) != names:
            out.append(u"inject: 本ごとの数えの本が 200 本(前の便の claims の並び)でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(PI.GEN.caches_snapshot(PI.caches_all())):
            out.append(u"inject: cache の件数か名前が記録の前と違う")
    return out


def record_problems(R, full=True):
    u"""記録 3 つの検査(禁止欄・鍵・script の sha256・engine の指紋・cache・再計算)。問題の列。R = {"moves", "regress97", "inject", "pb_inject"}。"""
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
    out += safe("inject", inject_problems, R["inject"], R["pb_inject"][u"行"], full)
    return out


def judge_problems(R, seal):
    u"""判定の関数が記録から作り直せるか(壊れた記録は赤)。"""
    try:
        J = TP.build_E(R, seal)
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"E"]) != list(SG.PRED_IDS) or list(J[u"K"]) != list(SG.K_IDS):
        out.append(u"判定の行が T-1〜T-10・K-1〜K-5 でない")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R, seal):
    J = TP.build_E(R, seal)
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != TP.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("judge") != TP.render_judge(J, seal).split(u"\n"):
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


# ================================================================ 小さい標本の記録 3 つ + PB の記録(通信しない・cache を読まない)
ITEMS = [dict(docID="DOC1", form="F3", model="m1", writer="W1", sha256="0" * 64), dict(docID="DOC2", form="F1", model="m2", writer="W2", sha256="1" * 64)]


def sample_header(k):
    _s, e = engine_commit_full()
    cache = collections.OrderedDict([("edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": "2" * 64})])
    h = collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"step", u"標本"), (u"HEAD の commit", "3" * 40), (u"engine の commit", e),
        (u"この script の sha256", sha256_rel(SCRIPT_REL)),
        (u"前の便の script の sha256", collections.OrderedDict((rel, sha256_rel(rel)) for rel in PREV_SCRIPT_RELS)),
        (u"入力の記録の sha256", collections.OrderedDict((rel, sha256_rel(rel)) for rel in input_rels(k))),
        (u"engine の指紋", dict(engine_fingerprint_at_commit(), adapter_xbrl_py_files=16, core_py_files=4, git_commit="3" * 40)),
        (u"lib の指紋", collections.OrderedDict((rel, sha256_rel(rel)) for rel in LIB_RELS)),
        (u"profile", list(TP.NOW_PROFILES) if k == "regress97" else (list(TP.PROFILES) if k == "moves" else list(TP.PROFILES) + [TP.BASE_OLD])),
        (u"cache の前後", collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)])), (u"範囲", u"標本")])
    return h


def ent(si, pos, sa, sb, pa, pb, label=None, existing=EXISTING, nopf=False, table=False):
    return [u"num", si, pos, sa, sb, pa, pb, label, existing if label is not None or existing == NEWROW else EXISTING, nopf, table]


def mk_book(src, name, item, ents, n_old=40, g_old=10, reason_only=0, same_keys=True, oks=(True, True), idok=True, bars=4, tab=None):
    lost = sum(1 for x in ents if x[3] == G and x[4] != G)
    gained = sum(1 for x in ents if x[3] != G and x[4] == G)
    head = collections.OrderedDict([(u"name", name), (u"docID", item[u"docID"]), (u"form", item[u"form"]), (u"model", item[u"model"]), (u"writer", item[u"writer"]),
                                    (u"材料", src), (u"文の sha256", item[u"sha256"])])
    head[u"対応"] = collections.OrderedDict([("P32E", oks[0]), ("P33E", oks[1])])
    head[u"数の claim の数"] = collections.OrderedDict([("P32E", n_old), ("P33E", n_old)])
    head[u"P30E と P32E で数の claim の鍵が同じ"] = same_keys
    head[u"P27 の鍵が一意"] = idok
    head[u"GROUNDED の数"] = collections.OrderedDict([("P32E", g_old), ("P33E", g_old + gained - lost)])
    head[u"動いた行"] = len(ents)
    head[u"state が変わった行"] = sum(1 for x in ents if x[3] != x[4])
    head[u"reason だけが違う行"] = reason_only
    head[u"動いた行の中身"] = ents
    head[u"行頭が | の文の数"] = bars
    head[u"表の前期の列の数"] = sum(1 for x in ents if x[10]) if tab is None else tab
    return norm(head)


def sample_books():
    e1 = [ent(0, 5, V_, G, u"CurrentYear", u"Prior1Year", u"真", table=True), ent(1, 5, V_, G, u"CurrentYear", u"Prior1Year", None, NEWROW, table=True),
          ent(2, 4, V_, V_, u"CurrentYear", u"Prior1Year", u"偽", table=True), ent(3, 4, P_, V_, u"なし", u"Prior1Year", None, NEWROW, table=True),
          ent(4, 4, U_, G, u"なし", u"Prior1Year", u"真", table=True)]
    e2 = [ent(0, 3, G, V_, u"CurrentYear", u"CurrentYear", None, NEWROW, True),
          ent(7, 1, P_, G, u"なし", u"CurrentYear", u"偽"),                                   # 札 偽の行が GROUNDED になった行
          ent(6, 1, G, P_, u"CurrentYear", u"なし", u"偽"),                                   # GROUNDED を失う行
          ent(8, 2, V_, G, u"CurrentYear", u"Prior2Year", u"真")]                               # 表でない行(札 真の VALUE_MISMATCH → GROUNDED)
    return [mk_book("aiforms", "DOC1_F3_m1", ITEMS[0], e1, reason_only=1, bars=6), mk_book("f5", "DOC2_F1_m2", ITEMS[1], e2, bars=0, tab=0)]


def sample_moves():
    books = sample_books()
    rec = sample_header("moves")
    rec[u"本"] = books
    rec[u"集計"] = norm(TP.aggregate_moves_t(books))
    rec[u"限界"] = list(TP.MOVES_LIMITS)
    rec[u"key_leaks"] = []
    return norm(rec)


def st4(g, v, u, p):
    return collections.OrderedDict([("GROUNDED", g), ("VALUE_MISMATCH", v), ("UNVERIFIABLE", u), ("POINTER_NOT_FOUND", p)])


def mk_doc(d, n, ents, xr_extra=0, g_old=6, added=0, gone=0, bars=0, tab=0):
    lost = sum(1 for x in ents if x[4] == G and x[5] != G)
    gained = sum(1 for x in ents if x[4] != G and x[5] == G)
    claims = collections.OrderedDict((p, n) for p in TP.NOW_PROFILES)
    claims[TP.NEW] = n + added - gone
    shas = collections.OrderedDict((p, hashlib.sha256((d + p).encode()).hexdigest()) for p in TP.NOW_PROFILES)
    fours = collections.OrderedDict((p, st4(g_old, n - g_old, 0, 0)) for p in TP.NOW_PROFILES)
    g_new = g_old + gained - lost
    fours[TP.NEW] = st4(g_new, claims[TP.NEW] - g_new, 0, 0)
    xr = [[x[0], x[1], x[2], x[3], x[4], x[5], None, None, x[9]] for x in ents] + [[u"num", 90 + j, 1, 0, G, G, "r1", "r2", False] for j in range(xr_extra)]
    mv = collections.OrderedDict([(TP.PAIRS[0][0], collections.OrderedDict([(u"動いた既存の行", xr), (u"増えた行", added), (u"増えた行の state", st4(0, added, 0, 0)), (u"消えた行", gone)]))])
    return collections.OrderedDict([
        (u"docID", d), (u"標本", u"手元の 67"), (u"zip の sha256", "4" * 64), (u"claims", claims), (u"4 state", fours), (u"出力の sha256(engine の欄を除く)", shas),
        (u"前の便の記録の sha256", collections.OrderedDict((p, shas[p]) for p in TP.BASE_PROFILES)), (u"動いた行と増えた行", mv),
        (u"P33E の動いた行", ents), (u"reason だけが違う行", xr_extra), (u"行頭が | の文の数", bars), (u"表の前期の列の数", tab)])


def sample_regress97():
    e2 = [[u"num", 0, 3, 0, G, V_, u"CurrentYear", u"Prior1Year", True, True, False], [u"num", 0, 9, 0, P_, V_, u"なし", u"Prior1Year", True, True, False],
          [u"num", 1, 4, 0, V_, V_, u"CurrentYear", u"Prior1Year", False, True, False], [u"text", 2, 2, 0, V_, V_, u"CurrentYear", u"CurrentYear", False, True, True],
          [u"num", 3, 6, 0, G, U_, u"CurrentYear", u"なし", True, True, False],                  # VALUE_MISMATCH 以外へ向かう GROUNDED の喪失
          [u"num", 4, 2, 0, P_, G, u"なし", u"CurrentYear", True, True, False]]                  # 非 GROUNDED から GROUNDED になった行
    e1 = [[u"num", 0, 7, 0, V_, V_, u"CurrentYear", u"Prior1Year", False, True, False]]          # pointers だけが違う行だけを持つ書類
    docs = [mk_doc("DOC1", 10, e1, bars=2, tab=3), mk_doc("DOC2", 12, e2, xr_extra=1)]
    rec = sample_header("regress97")
    rec[u"範囲"] = u"標本"
    rec[u"T-1・T-9 engine の差分"] = norm(link_at_history())
    msg = TP.message_numbers_t(engine_message_at_history())
    rec[u"T-8・T-10 の写し"] = norm(collections.OrderedDict([(u"出どころ", u"engine の commit の message"), (u"engine の commit", engine_commit_full()[1]), ("T-8", msg["T-8"]), ("T-10", msg["T-10"])]))
    rec[u"集計"] = norm(TP.regress_block_t(docs))
    rec[u"書類"] = norm(docs)
    rec[u"限界"] = list(TP.REGRESS_LIMITS)
    rec[u"key_leaks"] = []
    return norm(rec)


def cell(res, state, reason=None):
    return collections.OrderedDict([(u"対応", True), (u"結果", res), (u"state", state), (u"reason", reason)])


PASS_C, ORIG_C, OTHER_C = cell(TUNE.LABEL_PASS, G), cell(TUNE.LABEL_NAMED_ORIGINAL, V_), cell(TUNE.LABEL_NAMED_OTHER, V_)
UNMAPPED_C = collections.OrderedDict([(u"対応", False), (u"結果", TUNE.LABEL_UNMAPPED), (u"state", None), (u"reason", None)])


def arow(item, n, cue, win, c30, c33, per30, per33, linked=True, miss30=(), miss33=(), shape=u"既存", rt=True, rr=True, word=True, base_p=u"Prior1Year"):
    name = u"%s_%s_%s" % (item["docID"], item["form"], item["model"])
    base = collections.OrderedDict([(u"docID", item["docID"]), (u"form", item["form"]), (u"model", item["model"]), (u"writer", item["writer"])])
    r = collections.OrderedDict(base)
    r[u"id"] = u"%s-T9-%02d" % (name, n)
    r[u"型"] = PB.T9
    r[u"形"] = shape
    r[u"基準の claim"] = u"N%03d" % n
    r[u"P33E の土台に対応"] = linked
    r[u"round-trip"], r[u"読み直し"] = rt, rr
    r[u"engine の手がかり"], r[u"窓の手がかり"], r[u"文に前期の語"] = cue, win, word
    r[u"基準の pointer の期"] = base_p
    r["P30E"], r["P33E"] = c30, c33
    r[u"P30E の注入後の pointer の期"], r[u"P33E の注入後の pointer の期"] = per30, per33
    r[u"P30E の欠けた条件"], r[u"P33E の欠けた条件"] = list(miss30), list(miss33)
    return r


def sample_rows_a():
    return [arow(ITEMS[0], 1, True, True, PASS_C, ORIG_C, u"CurrentYear", u"Prior1Year"),
            arow(ITEMS[0], 2, True, True, PASS_C, PASS_C, u"CurrentYear", u"Prior1Year"),
            arow(ITEMS[0], 3, True, True, PASS_C, OTHER_C, u"CurrentYear", u"CurrentYear"),
            arow(ITEMS[1], 1, False, False, PASS_C, PASS_C, u"CurrentYear", u"CurrentYear"),
            arow(ITEMS[1], 2, False, False, ORIG_C, UNMAPPED_C, u"Prior1Year", u"なし", linked=False, miss33=[NO_BASE]),
            arow(ITEMS[1], 3, False, False, PASS_C, PASS_C, u"CurrentYear", u"Prior1Year")]


def pb_rows_of(rows):
    u"""PB の記録の行(id と P30E・P32E の欄だけ使う)。P33E の欄 = P32E の欄の写し(旗が偽の経路と同じ)にし、3 本目の P30E は違う結果にして『同じ行』が 5 / 6 になるようにする。"""
    out = []
    for r in rows:
        t = collections.OrderedDict([(u"id", r[u"id"]), ("P30E", copy.deepcopy(r["P30E"])), ("P32E", copy.deepcopy(r["P33E"]))])
        out.append(t)
    out[2]["P30E"] = copy.deepcopy(OTHER_C)
    return norm(out)


def bcell(state, per, mapped=True):
    c = collections.OrderedDict([(u"対応", mapped), (u"state", state if mapped else None), (u"期", per if mapped else u"なし")])
    c[u"結果"] = TP.result_word(c)
    return c


def brow(item, n, typ, c32, c33):
    r = collections.OrderedDict([(u"docID", item["docID"]), (u"id", u"%s_%s_%s-TT-%03d-%s" % (item["docID"], item["form"], item["model"], n, typ)), (u"形", item["form"]), (u"model", item["model"]), (u"型", typ)])
    r["P32E"], r["P33E"] = c32, c33
    return r


def sample_rows_b():
    rows = []
    # TP: P32E は 当期の fact に GROUNDED(通す)、P33E は前期の fact を名指して VALUE_MISMATCH(止める)。4 つ目 P33E は通す・5 つ目は対応なし・6 つ目は名指す前期以外
    spec = [(bcell(G, u"CurrentYear"), bcell(V_, u"Prior1Year")), (bcell(G, u"CurrentYear"), bcell(V_, u"Prior1Year")), (bcell(G, u"CurrentYear"), bcell(V_, u"Prior1Year")),
            (bcell(G, u"CurrentYear"), bcell(G, u"Prior1Year")), (bcell(G, u"CurrentYear"), bcell(None, None, mapped=False)), (bcell(U_, u"なし"), bcell(V_, u"CurrentYear"))]
    for n, (c32, c33) in enumerate(spec, 1):
        rows.append(brow(ITEMS[0], n, TP.TP, c32, c33))
        # TC: ほとんど同じ。6 つ目だけ P32E と P33E で state が違う
        rows.append(brow(ITEMS[0], n, TP.TC, bcell(V_, u"CurrentYear"), bcell(V_, u"CurrentYear") if n != 6 else bcell(U_, u"なし")))
    return rows


def sample_inject():
    ra, rb = sample_rows_a(), sample_rows_b()
    pb_rows = pb_rows_of(ra)
    per_a = collections.OrderedDict([("DOC1_F3_m1", collections.OrderedDict([(u"作れる site", 3), (u"土台 P30E が GROUNDED の site", 3), (u"cap を基準で絞る前に掛けた数", 3), (u"採った", 3)])),
                                     ("DOC2_F1_m2", collections.OrderedDict([(u"作れる site", 3), (u"土台 P30E が GROUNDED の site", 3), (u"cap を基準で絞る前に掛けた数", 3), (u"採った", 3)]))])
    key = u"site 候補(見出しの前期 1 列・当期 1 列・セルに数 1 つずつ)"
    per_b = collections.OrderedDict([("DOC1_F3_m1", collections.OrderedDict([(u"表の前期の列の数", 9), (key, 8), (u"土台が合わない", 1), (u"2 つのセルの字が同じ", 1), (u"行の字が文に 1 回でない", 0), (u"採った site", 6)])),
                                     ("DOC2_F1_m2", collections.OrderedDict([(u"表の前期の列の数", 0), (key, 0), (u"土台が合わない", 0), (u"2 つのセルの字が同じ", 0), (u"行の字が文に 1 回でない", 0), (u"採った site", 0)]))])
    rec = sample_header("inject")
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", PI.FLAG), (u"(a) の inject の中の値", True), (u"出たあとの値", False), (u"配線の問題", [])])
    rec[u"型"] = collections.OrderedDict([(u"a", u"標本"), (u"b", u"標本")])
    rec[SECTION_A] = collections.OrderedDict([(u"本ごとの数え", per_a), (u"注入の行の数", len(ra))])
    rec[SECTION_B] = collections.OrderedDict([(u"本ごとの数え", per_b), (u"注入の行の数", len(rb)), (u"集計", TP.inject_summary_t(rb))])
    rec[u"集計の欄"] = TP.inject_columns_t(ra, rb, pb_rows)
    rec[u"限界"] = list(TP.INJECT_LIMITS)
    rec[u"key_leaks"] = []
    rec[u"行"] = collections.OrderedDict([(SECTION_A, ra), (SECTION_B, rb)])
    return norm(rec), pb_rows


def sample_records():
    inj, pb_rows = sample_inject()
    return collections.OrderedDict([("moves", sample_moves()), ("regress97", sample_regress97()), ("inject", inj), ("pb_inject", {u"行": pb_rows})])


def sample_doc(R, seal):
    J = TP.build_E(R, seal)
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", TP.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start judge -->", TP.render_judge(J, seal), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"200 本の標本です。" + NOT_GATED, u""])


# ---------------------------------------------------------------- 判定の関数の入力(欄の集まり。通信しない)
def sample_cols(**ov):
    u"""``judge_from`` の入力(幅の真ん中の値)。ov = {名前: 値} で 1 つだけ替える。"""
    v = collections.OrderedDict([
        ("rec_ins", 57), ("rec_del", 0), ("voc_ins", 5), ("voc_del", 0), ("others", 0), ("byte", 97), ("docs", 97), ("profiles", len(TP.BASE_PROFILES)), ("same", 141), ("rows", 141), ("ids_same", True),
        ("bars97", 0), ("moved97", 0), ("lost97", 0), ("moved200", 390), ("nontable", 0), ("lost200", 0), ("gdiff", 365), ("vmg_true", 283), ("false_g", 0),
        ("site", 377), ("p32", 97.0), ("p33", 1.1), ("named", 98.9), ("tc_diff", 1),
        ("t8_red", 12), ("t8_total", 12), ("t10_names", [u"axis3 test_9"]), ("t10_n", 1), ("t10_failed", 1), ("m", 69)])
    v.update(ov)
    ns = collections.OrderedDict()
    if v["rec_ins"] is not None:
        ns[ENGINE_FILES[0]] = [v["rec_ins"], v["rec_del"]]
    if v["voc_ins"] is not None:
        ns[ENGINE_FILES[1]] = [v["voc_ins"], v["voc_del"]]
    for i in range(v["others"]):
        ns["adapters/xbrl/other%d.py" % i] = [1, 0]
    link = collections.OrderedDict([(u"numstat", ns), (u"直した file(M)", v["m"]), (u"新しい file(A)", 1), (u"engine の挿入の行数", 62)])
    cn = collections.OrderedDict((p, {u"byte が同じ書類": v["byte"], u"書類": v["docs"]}) for p in TP.BASE_PROFILES[:v["profiles"]])
    rg = collections.OrderedDict([
        (u"T-2 旗が偽の profile の byte 一致", cn),
        (u"T-3 P33E 対 P32E", collections.OrderedDict([(u"行頭が | の文", v["bars97"]), (u"動いた行", v["moved97"]), (u"GROUNDED を失う行", v["lost97"])]))])
    ij = collections.OrderedDict([
        (u"T-2 PB の記録との照らし", collections.OrderedDict([(u"行の数", v["rows"]), (u"id の集合が PB の記録と同じ", v["ids_same"]),
                                                    (u"P33E の結果と state が PB の記録の P32E の欄と同じ行", v["same"])])),
        (u"T-6 TP", collections.OrderedDict([(u"site(TP の行)", v["site"]), (u"P32E が通した率", v["p32"]), (u"P33E が通した率", v["p33"]), (u"名指した割合", v["named"])])),
        (u"T-7 TC", collections.OrderedDict([(u"P32E と P33E で結果か state が違う行", v["tc_diff"])]))])
    mv = collections.OrderedDict([
        (u"動いた行", v["moved200"]), (u"表の前期の列の数でない動いた行", v["nontable"]), (u"GROUNDED を失う行", {u"行": v["lost200"]}), (u"GROUNDED の数", {u"差": v["gdiff"]}),
        (u"T-5 VALUE_MISMATCH → GROUNDED", {u"札 真": v["vmg_true"]}), (u"T-5 札 偽の行が GROUNDED になった行", v["false_g"])])
    t8 = None if v["t8_red"] is None else collections.OrderedDict([(u"変異の本数", v["t8_total"]), (u"赤", v["t8_red"]), (u"原文", u"x")])
    t10 = None if v["t10_n"] is None else collections.OrderedDict([(u"赤の試験", v["t10_names"]), (u"赤の本数", v["t10_n"]),
                                                                  (u"tests/measure", {"failed": v["t10_failed"], "passed": 5191, "skipped": 34}), (u"原文", u"x")])
    return collections.OrderedDict([("moves", mv), ("regress", rg), ("inject", ij), ("link", link), ("copy", {"T-8": t8, "T-10": t10})])


# ================================================================ (a) 封の字
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def _mutate_row(self, cid, old, new):
        P = TP.seal_pred_rows(self.seal)
        self.assertIn(old, P[cid][1], cid)
        head = "| %s | %s | %s" % (cid, P[cid][0], P[cid][1])
        self.assertIn(head, self.seal)
        mutated = self.seal.replace(head, "| %s | %s | %s" % (cid, P[cid][0], P[cid][1].replace(old, new, 1)), 1)
        self.assertNotEqual(mutated, self.seal)
        return mutated

    def test_a_2_a_changed_character_in_the_seal_turns_the_pin_red(self):
        for cid, old, new in (("T-1", "45〜75", "45〜76"), ("T-1", "3〜6", "3〜7"), ("T-1", "/ 0、3", "/ 1、3"), ("T-2", "97 / 97", "97 / 96"), ("T-2", "141 / 141", "141 / 140"),
                              ("T-3", "0 / 0 / 0", "1 / 0 / 0"), ("T-3", "0 / 0 / 0", "0 / 0 / 1"), ("T-4", "380〜400", "380〜401"), ("T-4", "+350〜+380", "+350〜+381"), ("T-4", "400 / 0", "400 / 1"),
                              ("T-5", "270〜295", "270〜296"), ("T-5", "295 / 0", "295 / 1"), ("T-6", "360〜390", "360〜391"), ("T-6", "90〜100%", "89〜100%"), ("T-6", "0〜3%", "0〜4%"),
                              ("T-6", "95〜100%", "94〜100%"), ("T-7", "0〜3", "0〜4"), ("T-8", "10 / 10", "10 / 9"), ("T-9", "40〜80", "40〜81"), ("T-10", "test_9", "test_8"), ("T-10", "だけ、0", "だけ、1")):
            self.assertNotEqual([], bounds_problems(self._mutate_row(cid, old, new)), (cid, new))

    def test_a_3_the_thresholds_of_k1_to_k5_are_read_from_the_seal(self):
        b = TP.seal_bounds(self.seal)
        self.assertEqual(((97, 97, 141, 141), (0, 0), (0, 0), {u"P33E の通した率の上限": 3, u"P32E の通した率の下限": 90}, {u"赤": 10, u"変異の本数": 10}),
                         (b["K-1"], b["K-2"], b["K-3"], dict(b["K-4"]), dict(b["K-5"])))
        for old, new in (("T-2 が 97 / 97 かつ 141 / 141", "T-2 が 97 / 97 かつ 141 / 140"), ("T-3 の GROUNDED を失う行 0、", "T-3 の GROUNDED を失う行 1、"), ("T-4 の GROUNDED を失う行 0", "T-4 の GROUNDED を失う行 1"),
                         ("T-4 の表の前期の列でない動いた行 0", "T-4 の表の前期の列でない動いた行 1"), ("T-5 の札 偽が GROUNDED になった行 0", "T-5 の札 偽が GROUNDED になった行 1"),
                         ("P33E の通した率 ≤ 3%", "P33E の通した率 ≤ 4%"), ("P32E の通した率 ≥ 90%", "P32E の通した率 ≥ 89%"), ("T-8 が 10 / 10", "T-8 が 10 / 9")):
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
        return TP.judge_from(sample_cols(**ov), self.seal)

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
        cases = [("rec_ins", "T-1", 45, 44), ("rec_ins", "T-1", 75, 76), ("rec_del", "T-1", 0, 1), ("voc_ins", "T-1", 3, 2), ("voc_ins", "T-1", 6, 7), ("voc_del", "T-1", 0, 1), ("others", "T-1", 0, 1),
                 ("byte", "T-2", 97, 96), ("docs", "T-2", 97, 98), ("profiles", "T-2", 10, 9), ("same", "T-2", 141, 140), ("rows", "T-2", 141, 142), ("ids_same", "T-2", True, False),
                 ("bars97", "T-3", 0, 1), ("moved97", "T-3", 0, 1), ("lost97", "T-3", 0, 1),
                 ("moved200", "T-4", 380, 379), ("moved200", "T-4", 400, 401), ("nontable", "T-4", 0, 1), ("lost200", "T-4", 0, 1), ("gdiff", "T-4", 350, 349), ("gdiff", "T-4", 380, 381),
                 ("vmg_true", "T-5", 270, 269), ("vmg_true", "T-5", 295, 296), ("false_g", "T-5", 0, 1),
                 ("site", "T-6", 360, 359), ("site", "T-6", 390, 391), ("p32", "T-6", 90.0, 89.9), ("p33", "T-6", 3.0, 3.1), ("named", "T-6", 95.0, 94.9), ("p33", "T-6", 1.1, None), ("named", "T-6", 98.9, None),
                 ("tc_diff", "T-7", 0, 4), ("tc_diff", "T-7", 3, 4),
                 ("t8_red", "T-8", 12, 9), ("t8_total", "T-8", 10, 9), ("t8_red", "T-8", 12, None),
                 ("t10_names", "T-10", [u"axis3 test_9"], [u"axis3 test_8"]), ("t10_failed", "T-10", 1, 2), ("t10_n", "T-10", 1, None),
                 ("m", "T-9", 40, 39), ("m", "T-9", 80, 81)]
        for name, cid, inside, outside in cases:
            ov_in, ov_out = {name: inside}, {name: outside}
            if name == "t8_total":
                ov_in["t8_red"], ov_out["t8_red"] = inside, outside
            self.assertEqual(HIT, self.J(**ov_in)[u"E"][cid][u"判定"], (name, inside))
            self.assertEqual(MISS, self.J(**ov_out)[u"E"][cid][u"判定"], (name, outside))
        self.assertEqual(MISS, self.J(rec_ins=None)[u"E"]["T-1"][u"判定"])                      # recipes の行が無い
        self.assertEqual(MISS, self.J(site=0)[u"E"]["T-6"][u"判定"])

    def test_c_3_the_adoption_follows_k1_to_k5(self):
        self.assertFalse(self.J(byte=96)[u"採用"])                       # K-1
        self.assertEqual(MISS, self.J(byte=96)[u"K"]["K-1"][u"判定"])
        self.assertFalse(self.J(same=140)[u"採用"])
        self.assertFalse(self.J(lost97=1)[u"採用"])                      # K-2(T-3 の側)
        self.assertEqual(MISS, self.J(lost97=1)[u"K"]["K-2"][u"判定"])
        self.assertFalse(self.J(lost200=1)[u"採用"])                     # K-2(T-4 の側)
        self.assertEqual(MISS, self.J(lost200=1)[u"K"]["K-2"][u"判定"])
        self.assertFalse(self.J(nontable=1)[u"採用"])                    # K-3(T-4 の表の前期の列でない行)
        self.assertEqual(MISS, self.J(nontable=1)[u"K"]["K-3"][u"判定"])
        self.assertFalse(self.J(false_g=1)[u"採用"])                     # K-3(T-5 の札 偽)
        self.assertEqual(MISS, self.J(false_g=1)[u"K"]["K-3"][u"判定"])
        self.assertFalse(self.J(p33=3.1)[u"採用"])                       # K-4(P33E の通した率 ≤ 3%)
        self.assertEqual(MISS, self.J(p33=3.1)[u"K"]["K-4"][u"判定"])
        self.assertTrue(self.J(p33=3.0)[u"採用"])
        self.assertFalse(self.J(p32=89.9)[u"採用"])                      # K-4(P32E の通した率 ≥ 90%)
        self.assertEqual(MISS, self.J(p32=89.9)[u"K"]["K-4"][u"判定"])
        self.assertFalse(self.J(p33=None)[u"採用"])                      # K-4: 分母 0 は外れ
        self.assertFalse(self.J(site=0, p32=None, p33=None, named=None)[u"採用"])
        self.assertFalse(self.J(t8_red=9)[u"採用"])                      # K-5
        self.assertFalse(self.J(t10_failed=2)[u"採用"])
        self.assertEqual(MISS, self.J(t10_failed=2)[u"K"]["K-5"][u"判定"])

    def test_c_4_each_k_condition_alone_is_enough_to_miss_k4_and_k_uses_the_seal_k_thresholds_not_the_prediction_ranges(self):
        for ov in (dict(p33=3.5), dict(p32=80.0)):                      # K-4 の 2 条件の片方ずつ(片方を外した判定器は黙る)
            self.assertEqual(MISS, self.J(**ov)[u"K"]["K-4"][u"判定"], ov)
        self.assertEqual(HIT, self.J(p33=0.0, p32=100.0)[u"K"]["K-4"][u"判定"])
        J = self.J(moved200=500)                                         # T-4 の幅の外。K-2・K-3 は GROUNDED を失う行・表でない行・札 偽だけを見る
        self.assertEqual(MISS, J[u"E"]["T-4"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-2"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-3"][u"判定"])
        J = self.J(site=100)                                             # T-6 の site の幅の外でも K-4 は率だけ
        self.assertEqual(MISS, J[u"E"]["T-6"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-4"][u"判定"])
        J = self.J(vmg_true=100, tc_diff=10)                             # T-5 の幅・T-7 の外でも K には効かない
        self.assertEqual(MISS, J[u"E"]["T-5"][u"判定"])
        self.assertEqual(MISS, J[u"E"]["T-7"][u"判定"])
        self.assertTrue(J[u"採用"])

    def test_c_4b_t8_and_t10_are_read_from_the_copied_message_numbers(self):
        J = self.J()
        self.assertEqual({u"赤": 10, u"変異の本数": 10, u"写した全部赤の本数": 12}, dict(J[u"E"]["T-8"][u"値"]))
        self.assertEqual({u"赤の試験": [u"axis3 test_9"], u"赤の本数": 1, u"ほかの赤": 0}, dict(J[u"E"]["T-10"][u"値"]))
        J = self.J(t10_failed=3)                                         # failed が名指しの本数より多い = ほかの赤が 2
        self.assertEqual(2, J[u"E"]["T-10"][u"値"][u"ほかの赤"])
        self.assertEqual(MISS, J[u"E"]["T-10"][u"判定"])
        J = self.J(t8_red=None)
        self.assertEqual(MISS, J[u"E"]["T-8"][u"判定"])

    def test_c_5_the_judgment_moves_with_the_columns_and_with_the_seal(self):
        base = norm(self.J())
        self.assertNotEqual(base, norm(self.J(moved200=395)))
        mutated_seal = self.seal.replace("380〜400", "380〜384", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertEqual(MISS, TP.judge_from(sample_cols(), mutated_seal)[u"E"]["T-4"][u"判定"])

    def test_c_6_a_broken_record_is_red_not_an_exception(self):
        R = sample_records()
        del R["moves"][u"本"][0][u"動いた行の中身"]
        self.assertNotEqual([], judge_problems(R, self.seal))
        self.assertEqual([], judge_problems(sample_records(), self.seal))
        R2 = sample_records()
        R2["pb_inject"] = {}
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
        A = norm(TP.aggregate_moves_t(self.R["moves"][u"本"])[u"全体"])
        lab = lambda a, b, c, d, e: {u"真": a, u"偽": b, u"判定不能": c, NO_LABEL: d, NEWROW: e}      # noqa: E731
        # 9 行 = 1 本目 5(全部表の前期の列)+ 2 本目 4。state が変わった行 8・期だけ変わった行 1
        self.assertEqual((9, 8, 1), (A[u"動いた行"], A[u"state が変わった行"], A[u"state は同じで pointer の期だけ変わった行"]))
        self.assertEqual((5, 4), (A[u"表の前期の列の数の動いた行"], A[u"表の前期の列の数でない動いた行"]))
        # GROUNDED を失う 2(2 本目の VALUE_MISMATCH 行きと POINTER_NOT_FOUND 行き。札 偽 1・新しい行 1)
        self.assertEqual({u"行": 2, u"札": lab(0, 1, 0, 0, 1)}, A[u"GROUNDED を失う行"])
        # VALUE_MISMATCH → GROUNDED 3(札 真 2・新しい行 1)。札 偽の行が GROUNDED になった行 1(2 本目の POINTER_NOT_FOUND → GROUNDED)
        self.assertEqual({u"行": 3, u"札 真": 2, u"札 偽": 0, u"札 判定不能": 0, u"新しい行(札なし)": 1, u"既存で札なし": 0}, A[u"T-5 VALUE_MISMATCH → GROUNDED"])
        self.assertEqual(1, A[u"T-5 札 偽の行が GROUNDED になった行"])
        self.assertEqual({u"行": 5, u"札": lab(3, 1, 0, 0, 1)}, A[u"GROUNDED になった行"])
        self.assertEqual({"P32E": 20, "P33E": 23, u"差": 3}, A[u"GROUNDED の数"])
        self.assertEqual((6, 5), (A[u"行頭が | の文"], A[u"表の前期の列の数"]))
        T = norm(TP.regress_block_t(self.R["regress97"][u"書類"]))
        t3 = T[u"T-3 P33E 対 P32E"]
        # 動いた行 7(state か pointers) = 1 書類目 1 + 2 書類目 6。GROUNDED を失う 2 = VALUE_MISMATCH 行き 1 + UNVERIFIABLE 行き 1。GROUNDED になった 1。動いた書類 2。行頭が | の文のある書類 1
        self.assertEqual((7, 2, 1, 2, 1, 2), (t3[u"動いた行"], t3[u"GROUNDED を失う行"], t3[u"GROUNDED になった行"], t3[u"動いた書類"], t3[u"行頭が | の文のある書類"], t3[u"行頭が | の文"]))
        self.assertEqual((3, 4, 3, 1, 8), (t3[u"表の前期の列の数"], t3[u"state が変わった行"], t3[u"pointers だけが違う行"], t3[u"reason だけが違う行"],
                                           t3[u"XR の定義(state・reason・pointers のどれか)の動いた行"]))
        self.assertEqual(set(TP.BASE_PROFILES), set(T[u"T-2 旗が偽の profile の byte 一致"]))
        cols = norm(TP.inject_columns_t(self.R["inject"][u"行"][SECTION_A], self.R["inject"][u"行"][SECTION_B], self.R["pb_inject"][u"行"]))
        self.assertEqual({u"行の数": 6, u"PB の記録の行の数": 6, u"id の集合が PB の記録と同じ": True, u"P33E の結果と state が PB の記録の P32E の欄と同じ行": 6,
                          u"参考 P30E の結果と state が PB の記録の P30E の欄と同じ行": 5}, cols[u"T-2 PB の記録との照らし"])
        # TP 6 行: P32E が通した 5(6 本目は UNVERIFIABLE)・P33E が通した 1(4 本目)・P33E が止めた 4(対応のある行 5 のうち通さない 4。5 本目は対応なし)・名指した前期 3(6 本目は当期を名指す)
        self.assertEqual({u"site(TP の行)": 6, u"P32E が通した率": 83.3, u"P33E が通した率": 16.7, u"P32E が通した行": 5, u"P33E が通した行": 1, u"P33E が止めた行": 4,
                          u"うち前期の fact を名指して VALUE_MISMATCH": 3, u"名指した割合": 75.0, u"対応が付かない行": {"P32E": 0, "P33E": 1}}, cols[u"T-6 TP"])
        # TC 6 行: 結果か state が違う行 1(6 本目)。期だけが違う行 0
        self.assertEqual({u"TC の行": 6, u"P32E と P33E で結果か state が違う行": 1, u"参考 期だけが違う行": 0, u"対応が付かない行": {"P32E": 0, "P33E": 0}}, cols[u"T-7 TC"])

    def _red(self, mutate, full=False):
        R = copy.deepcopy(self.R)
        mutate(R)
        self.assertNotEqual([], record_problems(R, full=full))

    def test_g_2_one_number_in_a_record_turns_it_red(self):
        self._red(lambda R: R["moves"][u"本"][0][u"GROUNDED の数"].__setitem__("P33E", 99))
        self._red(lambda R: R["moves"][u"本"][0].__setitem__(u"動いた行", 9))
        self._red(lambda R: R["moves"][u"本"][0].__setitem__(u"state が変わった行", 0))
        self._red(lambda R: R["moves"][u"集計"][u"全体"].__setitem__(u"動いた行", 99))
        self._red(lambda R: R["moves"][u"集計"][u"全体"].__setitem__(u"表の前期の列の数でない動いた行", 0))
        self._red(lambda R: R["moves"][u"集計"][u"全体"][u"T-5 VALUE_MISMATCH → GROUNDED"].__setitem__(u"札 真", 0))
        self._red(lambda R: R["moves"][u"本"][1][u"動いた行の中身"][0].__setitem__(7, u"真"))               # 新しい行に札
        self._red(lambda R: R["moves"][u"本"][1][u"動いた行の中身"][0].__setitem__(9, False))             # 集計の前期の fact が無い要素の数と合わない
        self._red(lambda R: R["moves"][u"本"][0].__setitem__(u"対応", {"P32E": True, "P33E": False}))
        self._red(lambda R: R["regress97"][u"書類"][1][u"P33E の動いた行"][0].__setitem__(5, G))
        self._red(lambda R: R["regress97"][u"書類"][1][u"P33E の動いた行"][0].__setitem__(8, False))
        self._red(lambda R: R["regress97"][u"書類"][1][u"動いた行と増えた行"]["P33E 対 P32E"].__setitem__(u"増えた行", 5))
        self._red(lambda R: R["regress97"][u"書類"][1].__setitem__(u"reason だけが違う行", 0))
        self._red(lambda R: R["regress97"][u"集計"][u"T-3 P33E 対 P32E"].__setitem__(u"GROUNDED を失う行", 0))
        self._red(lambda R: R["regress97"][u"書類"][0][u"出力の sha256(engine の欄を除く)"].__setitem__("P28E", "5" * 64))
        self._red(lambda R: R["regress97"][u"T-1・T-9 engine の差分"].__setitem__(u"numstat", "x"))
        self._red(lambda R: R["inject"][u"行"][SECTION_B][0]["P33E"].__setitem__(u"結果", TP.PASSED_WORD))
        self._red(lambda R: R["inject"][u"行"][SECTION_B][0]["P33E"].__setitem__(u"期", u"CurrentYear"))
        self._red(lambda R: R["inject"][u"行"][SECTION_A][0]["P33E"].__setitem__(u"結果", TUNE.LABEL_PASS))                # 通したが GROUNDED でない
        self._red(lambda R: R["inject"][u"行"][SECTION_A][0].__setitem__(u"P33E の注入後の pointer の期", u"Prior9Year"))         # 期が語でない
        self._red(lambda R: R["inject"][u"行"][SECTION_A][0].__setitem__(u"P33E の土台に対応", False))                          # 土台に対応が無いのに P33E の欄が対応なしでない
        self._red(lambda R: R["inject"][SECTION_B][u"集計"]["TP"].__setitem__(u"行", 9))
        self._red(lambda R: R["inject"][SECTION_B].__setitem__(u"注入の行の数", 9))
        self._red(lambda R: R["inject"][SECTION_A].__setitem__(u"注入の行の数", 9))

    def test_g_2b_every_numeric_leaf_of_the_stored_aggregates_is_recomputed(self):
        u"""記録の集計・集計の欄の数の葉を 1 つずつ 0(元が 0 なら 1)に替えると赤(0 に固定した欄が黙らない)。"""
        n = 0
        for k, root in (("moves", (u"集計",)), ("regress97", (u"集計",)), ("inject", (SECTION_B, u"集計")), ("inject", (u"集計の欄",))):
            for path in list(leaves(get_path(self.R[k], root))):
                full_path = root + path
                old = get_path(self.R[k], full_path)

                def mutate(R, k=k, full_path=full_path, old=old):
                    set_path(R[k], full_path, 0 if old != 0 else 1)
                self._red(mutate)
                n += 1
        self.assertGreaterEqual(n, 120)

    def test_g_2c_a_consistently_edited_book_still_breaks_the_invariants(self):
        u"""本を直してから集計も作り直しても(集計との食い違いでは見つからない)、本の中の欄の間の関係で赤になる。"""
        def reagg(R):
            R["moves"][u"集計"] = norm(TP.aggregate_moves_t(R["moves"][u"本"]))
        for mutate in (lambda b: b[u"GROUNDED の数"].__setitem__("P33E", 99), lambda b: b[u"GROUNDED の数"].__setitem__("P32E", 99), lambda b: b[u"GROUNDED の数"].__setitem__("P33E", 12),
                       lambda b: b.__setitem__(u"動いた行", 1), lambda b: b.__setitem__(u"state が変わった行", 9),
                       lambda b: b[u"動いた行の中身"][0].__setitem__(4, b[u"動いた行の中身"][0][3]), lambda b: b[u"動いた行の中身"][0].__setitem__(8, NEWROW),
                       lambda b: b[u"動いた行の中身"][0].__setitem__(7, u"偽っぽい"), lambda b: b[u"動いた行の中身"][0].__setitem__(5, u"Prior3Year"),
                       lambda b: b[u"動いた行の中身"][0].__setitem__(0, u"text"), lambda b: b[u"動いた行の中身"].append(list(b[u"動いた行の中身"][0])),
                       lambda b: b[u"動いた行の中身"][0].__setitem__(10, u"真"), lambda b: b[u"動いた行の中身"][0].pop(),
                       lambda b: b.__setitem__(u"行頭が | の文の数", 0),                                               # 表の前期の列の数があるのに行頭が | の文が無い
                       lambda b: b.__setitem__(u"表の前期の列の数", 0),                                               # 表の前期の列の数が 0 なのに表の前期の列の数の動いた行がある
                       lambda b: b[u"数の claim の数"].__setitem__("P33E", 99), lambda b: b[u"対応"].__setitem__("P33E", False),
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
            ra, rb = R["inject"][u"行"][SECTION_A], R["inject"][u"行"][SECTION_B]
            R["inject"][SECTION_B][u"集計"] = norm(TP.inject_summary_t(rb))
            R["inject"][u"集計の欄"] = norm(TP.inject_columns_t(ra, rb, R["pb_inject"][u"行"]))
        for mutate in (lambda r: r["P33E"].__setitem__(u"結果", u"通した率"), lambda r: r["P33E"].__setitem__(u"state", u"GROUNDED?"), lambda r: r["P33E"].__setitem__(u"対応", False),
                       lambda r: r["P33E"].__setitem__(u"期", u"Prior3Year"), lambda r: r.__setitem__(u"型", u"TX"), lambda r: r.__setitem__(u"id", u"X-TT-001-TP"),
                       lambda r: r.pop(u"model"), lambda r: r["P32E"].pop(u"期"), lambda r: r.__setitem__("P32E", None)):
            R = copy.deepcopy(self.R)
            mutate(R["inject"][u"行"][SECTION_B][0])
            try:
                reagg(R)
            except Exception:                                   # noqa: BLE001
                pass
            self.assertNotEqual([], record_problems(R, full=False))
        for mutate in (lambda r: r["P33E"].__setitem__(u"結果", u"通した率"), lambda r: r["P33E"].__setitem__(u"state", u"GROUNDED?"), lambda r: r["P30E"].__setitem__(u"対応", False),
                       lambda r: r.__setitem__(u"P33E の注入後の pointer の期", u"Prior3Year"), lambda r: r.__setitem__(u"P30E の欠けた条件", [u"ア id の claim が在る"]),
                       lambda r: r.__setitem__(u"P33E の欠けた条件", [u"土台なし"]), lambda r: r.__setitem__(u"P33E の土台に対応", u"はい"), lambda r: r.__setitem__(u"型", u"T8_REL"),
                       lambda r: r.__setitem__(u"id", u"X-T9-01"), lambda r: r.__setitem__(u"形", u"全部"), lambda r: r.__setitem__(u"engine の手がかり", u"真"),
                       lambda r: r.__setitem__(u"基準の pointer の期", u"Prior9Year"), lambda r: r.pop(u"窓の手がかり"), lambda r: r.__setitem__(u"窓の手がかり", None)):
            R = copy.deepcopy(self.R)
            mutate(R["inject"][u"行"][SECTION_A][0])
            try:
                reagg(R)
            except Exception:                                   # noqa: BLE001
                pass
            self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)                                # TP の行だけ消して TC を残す(site ごとに 2 行でない)
        R["inject"][u"行"][SECTION_B].pop(0)
        R["inject"][SECTION_B][u"注入の行の数"] -= 1
        reagg(R)
        self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        R["inject"][SECTION_B][u"本ごとの数え"]["DOC1_F3_m1"][u"採った site"] = 5                  # 候補 − 除いた行 と合わない
        self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        reagg(R)
        self.assertEqual([], record_problems(R, full=False))

    def test_g_2e_a_column_changes_exactly_where_its_field_feeds(self):
        u"""行の欄 1 つを変えると、それを餌にする欄だけが動く(P32E の欄は T-6 の P32E の率・T-7 を、P33E の欄は T-6 の P33E の率と名指した割合・T-7 を、PB の記録は T-2 を動かす)。"""
        ra, rb, pb = self.R["inject"][u"行"][SECTION_A], self.R["inject"][u"行"][SECTION_B], self.R["pb_inject"][u"行"]
        base = norm(TP.inject_columns_t(ra, rb, pb))
        rb2 = copy.deepcopy(rb)
        rb2[0]["P33E"] = bcell(G, u"CurrentYear")                                            # TP の 1 行目を P33E が通す
        c = norm(TP.inject_columns_t(ra, rb2, pb))
        self.assertEqual(base[u"T-6 TP"][u"P33E が通した行"] + 1, c[u"T-6 TP"][u"P33E が通した行"])
        self.assertEqual(base[u"T-6 TP"][u"P33E が止めた行"] - 1, c[u"T-6 TP"][u"P33E が止めた行"])
        self.assertEqual(base[u"T-6 TP"][u"P32E が通した行"], c[u"T-6 TP"][u"P32E が通した行"])
        self.assertEqual(base[u"T-7 TC"], c[u"T-7 TC"])
        self.assertEqual(base[u"T-2 PB の記録との照らし"], c[u"T-2 PB の記録との照らし"])
        rb3 = copy.deepcopy(rb)
        rb3[0]["P32E"] = bcell(V_, u"CurrentYear")                                            # TP の 1 行目を P32E が通さない
        c = norm(TP.inject_columns_t(ra, rb3, pb))
        self.assertEqual(base[u"T-6 TP"][u"P32E が通した行"] - 1, c[u"T-6 TP"][u"P32E が通した行"])
        self.assertEqual(base[u"T-6 TP"][u"P33E が通した行"], c[u"T-6 TP"][u"P33E が通した行"])
        rb4 = copy.deepcopy(rb)
        rb4[1]["P33E"] = bcell(U_, u"なし")                                                   # TC の 1 行目の P33E の state を変える
        c = norm(TP.inject_columns_t(ra, rb4, pb))
        self.assertEqual(base[u"T-7 TC"][u"P32E と P33E で結果か state が違う行"] + 1, c[u"T-7 TC"][u"P32E と P33E で結果か state が違う行"])
        self.assertEqual(base[u"T-6 TP"], c[u"T-6 TP"])
        rb5 = copy.deepcopy(rb)
        rb5[1]["P32E"], rb5[1]["P33E"] = bcell(G, u"CurrentYear"), bcell(G, u"Prior1Year")    # TC の 1 行目は state も結果も同じで期だけ違う = 参考の欄だけ動く
        c = norm(TP.inject_columns_t(ra, rb5, pb))
        self.assertEqual(base[u"T-7 TC"][u"P32E と P33E で結果か state が違う行"], c[u"T-7 TC"][u"P32E と P33E で結果か state が違う行"])
        self.assertEqual(base[u"T-7 TC"][u"参考 期だけが違う行"] + 1, c[u"T-7 TC"][u"参考 期だけが違う行"])
        ra2 = copy.deepcopy(ra)
        ra2[0]["P33E"] = copy.deepcopy(PASS_C)                                                # (a) の P33E の欄を PB の記録と違う結果にする
        c = norm(TP.inject_columns_t(ra2, rb, pb))
        self.assertEqual(base[u"T-2 PB の記録との照らし"][u"P33E の結果と state が PB の記録の P32E の欄と同じ行"] - 1, c[u"T-2 PB の記録との照らし"][u"P33E の結果と state が PB の記録の P32E の欄と同じ行"])
        self.assertEqual(base[u"T-6 TP"], c[u"T-6 TP"])

    def test_g_3_a_forbidden_key_or_a_key_or_a_company_name_or_a_pointer_text_turns_it_red(self):
        for key in (u"span", u"value", u"recomputed", u"文", u"sentence", u"数", u"理由", u"pointers", u"pointer", u"要素", u"element"):
            self._red(lambda R, key=key: R["moves"][u"本"][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["inject"][u"行"][SECTION_A][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["inject"][u"行"][SECTION_B][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["regress97"][u"書類"][0].__setitem__(key, 1))
        self._red(lambda R: R["regress97"].__setitem__(u"メモ", u"株式会社テスト"))
        self._red(lambda R: R["moves"].__setitem__(u"メモ", u"sk-" + u"a" * 20))
        self._red(lambda R: R["regress97"].__setitem__(u"key_leaks", [u"鍵の形"]))
        self._red(lambda R: R["moves"].__setitem__(u"メモ", u"xbrl:jppfs_cor:NetSales@CurrentYearDuration"))
        self._red(lambda R: R["inject"][u"行"][SECTION_B][0].__setitem__(u"メモ", u"jppfs_cor:NetSales"))
        self._red(lambda R: R["regress97"][u"書類"][0].__setitem__(u"メモ", u"@Prior1YearDuration"))

    def test_g_4_one_character_of_the_fingerprint_or_the_script_sha_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][u"engine の指紋"].__setitem__("adapter_xbrl_py_sha256", R[k][u"engine の指紋"]["adapter_xbrl_py_sha256"][:-1] + ("0" if R[k][u"engine の指紋"]["adapter_xbrl_py_sha256"][-1] != "0" else "1")))
            self._red(lambda R, k=k: R[k][u"engine の指紋"].__setitem__("core_py_sha256", "f" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"この script の sha256", "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"封の commit", u"0000000"))
            self._red(lambda R, k=k: R[k].__setitem__(u"engine の commit", "0" * 40))
            self._red(lambda R, k=k: R[k].__setitem__(u"HEAD の commit", u"abc"))
            self._red(lambda R, k=k: R[k][u"lib の指紋"].__setitem__(LIB_RELS[0], "e" * 64))
            self._red(lambda R, k=k: R[k][u"前の便の script の sha256"].__setitem__(PREV_SCRIPT_RELS[0], "e" * 64))
            self._red(lambda R, k=k: R[k][u"入力の記録の sha256"].__setitem__(list(R[k][u"入力の記録の sha256"])[0], "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"seal", u"docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md"))
            self._red(lambda R, k=k: R[k].__setitem__(u"profile", [u"P29E", u"P30E"]))
            self._red(lambda R, k=k: R[k][u"限界"].pop())
            self._red(lambda R, k=k: R[k][u"限界"].__setitem__(0, u"別の字"))

    def test_g_5_a_changed_cache_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][u"cache の前後"].__setitem__(u"変化なし", False))
            self._red(lambda R, k=k: R[k][u"cache の前後"][u"後"]["edinet"].__setitem__(u"件数", 4))

    def test_g_5b_the_switch_record_of_the_injection_turns_red_when_the_wiring_or_the_values_are_wrong(self):
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"配線の問題", [u"N がちがう"]))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"(a) の inject の中の値", False))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"出たあとの値", True))
        self._red(lambda R: R["inject"][u"切り替え"].__setitem__(u"名前", u"compound_yen_2026_11_05"))

    def test_g_5c_the_inject_cap_of_the_a_section_is_checked_on_its_own(self):
        R = copy.deepcopy(self.R)
        rows = R["inject"][u"行"][SECTION_A]
        extra = []
        for i in range(RUN.INJECT_CAP):
            r = copy.deepcopy(rows[0])
            r[u"id"] = u"DOC1_F3_m1-T9-%02d" % (50 + i)
            extra.append(r)
        rows += extra
        R["inject"][SECTION_A][u"注入の行の数"] = len(rows)
        R["pb_inject"][u"行"] += [{u"id": r[u"id"], "P30E": r["P30E"], "P32E": r["P33E"]} for r in extra]
        R["inject"][u"集計の欄"] = norm(TP.inject_columns_t(rows, R["inject"][u"行"][SECTION_B], R["pb_inject"][u"行"]))
        self.assertTrue(any(u"上限" in x for x in inject_problems(R["inject"], R["pb_inject"][u"行"], False)), inject_problems(R["inject"], R["pb_inject"][u"行"], False))

    def test_g_5d_the_full_only_checks_are_exercised_on_the_sample(self):
        u"""full=True だけが見る検査(本番の記録でだけ走る)を、標本の記録で 1 つずつ。"""
        rg = copy.deepcopy(self.R["regress97"])
        self.assertTrue(any(u"97" in x for x in regress97_problems(rg, True)))                      # 標本は 97 書類でない
        self.assertFalse(any(u"T-1・T-9" in x for x in regress97_problems(rg, True)))               # 履歴から作り直した値と同じ
        rg[u"T-1・T-9 engine の差分"][u"直した file(M)"] += 1
        self.assertTrue(any(u"T-1・T-9" in x for x in regress97_problems(rg, True)))
        rg = copy.deepcopy(self.R["regress97"])
        self.assertFalse(any(u"写し" in x for x in regress97_problems(rg, True)))
        rg[u"T-8・T-10 の写し"]["T-8"][u"赤"] = 9
        self.assertTrue(any(u"写し" in x for x in regress97_problems(rg, True)))
        rg = copy.deepcopy(self.R["regress97"])
        rg[u"T-8・T-10 の写し"]["T-10"] = None
        self.assertTrue(any(u"写し" in x for x in regress97_problems(rg, True)))
        rg = copy.deepcopy(self.R["regress97"])
        rg[u"T-8・T-10 の写し"][u"engine の commit"] = "0" * 40
        self.assertTrue(any(u"写し" in x for x in regress97_problems(rg, True)))
        mv = copy.deepcopy(self.R["moves"])
        self.assertTrue(any(u"200" in x for x in moves_problems(mv, True)))                          # 標本は 200 本でない
        self.assertTrue(any(u"本の並び" in x for x in moves_problems(mv, True)))
        inj = copy.deepcopy(self.R["inject"])
        pb = self.R["pb_inject"][u"行"]
        self.assertFalse(any(u"PB の記録に無い id" in x for x in inject_problems(inj, pb, True)))
        self.assertTrue(any(u"PB の記録に無い id" in x for x in inject_problems(inj, pb[1:], True)))      # PB の記録に無い id の行がある
        self.assertTrue(any(u"本ごとの数え" in x for x in inject_problems(inj, pb, True)))

    def test_g_6_the_document_follows_the_records_and_the_seal(self):
        doc = sample_doc(self.R, self.seal)
        lines = doc.split(u"\n")
        i = lines.index(u"<!-- 門:start pred -->") + 3                  # 表の 1 行目(T-1)
        for col_char in (u"T", u"1", u"挿"):
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
        R2["inject"][u"行"][SECTION_B][0]["P33E"] = bcell(G, u"CurrentYear")
        self.assertNotEqual([], doc_problems(doc, R2, self.seal))
        R3 = copy.deepcopy(self.R)
        R3["moves"][u"本"][0][u"動いた行の中身"][0][4] = U_
        self.assertNotEqual([], doc_problems(doc, R3, self.seal))
        mutated_seal = self.seal.replace("380〜400", "380〜401", 1)
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

    def test_g_8_a_damaged_pb_record_changes_t2_and_the_stored_columns_turn_red(self):
        ra, rb, pb = self.R["inject"][u"行"][SECTION_A], self.R["inject"][u"行"][SECTION_B], self.R["pb_inject"][u"行"]
        key = u"P33E の結果と state が PB の記録の P32E の欄と同じ行"
        base = norm(TP.inject_columns_t(ra, rb, pb))[u"T-2 PB の記録との照らし"]
        pbb = copy.deepcopy(pb)
        pbb[0][u"id"] = u"X-T9-97"                                                              # id を 1 つ変える
        c = norm(TP.inject_columns_t(ra, rb, pbb))[u"T-2 PB の記録との照らし"]
        self.assertEqual((True, False, base[key] - 1), (base[u"id の集合が PB の記録と同じ"], c[u"id の集合が PB の記録と同じ"], c[key]))
        pbc = copy.deepcopy(pb)
        pbc[3]["P32E"][u"state"] = V_                                                           # P32E の state を 1 つ変える
        c = norm(TP.inject_columns_t(ra, rb, pbc))[u"T-2 PB の記録との照らし"]
        self.assertEqual(base[key] - 1, c[key])
        pbd = copy.deepcopy(pb)
        pbd[3]["P32E"][u"結果"] = TUNE.LABEL_NAMED_OTHER                                        # 結果の語だけ変える
        c = norm(TP.inject_columns_t(ra, rb, pbd))[u"T-2 PB の記録との照らし"]
        self.assertEqual(base[key] - 1, c[key])
        for damaged in (pbb, pbc, pbd):
            R = copy.deepcopy(self.R)
            R["pb_inject"][u"行"] = damaged
            self.assertNotEqual([], record_problems(R, full=False))                              # 記録の集計の欄が壊した PB の記録と合わない
        R = copy.deepcopy(self.R)
        R["pb_inject"][u"行"] = pbb
        self.assertFalse(norm(TP.columns_from_records(R)["inject"])[u"T-2 PB の記録との照らし"][u"id の集合が PB の記録と同じ"])
        self.assertEqual(MISS, TP.build_E(R, self.seal)[u"E"]["T-2"][u"判定"])
        self.assertEqual(MISS, TP.build_E(R, self.seal)[u"K"]["K-1"][u"判定"])

    def test_g_9_the_judgment_comes_from_rows_books_and_docs_not_from_the_stored_aggregates(self):
        base = norm(TP.build_E(self.R, self.seal))
        R = copy.deepcopy(self.R)
        for path in list(leaves(R["moves"][u"集計"])):
            set_path(R["moves"][u"集計"], path, 0)
        for path in list(leaves(R["regress97"][u"集計"])):
            set_path(R["regress97"][u"集計"], path, 0)
        for path in list(leaves(R["inject"][u"集計の欄"])):
            set_path(R["inject"][u"集計の欄"], path, 0)
        self.assertEqual(base, norm(TP.build_E(R, self.seal)))                                  # 記録の集計・集計の欄を 0 に固定しても判定は行・本・書類から作る
        R2 = copy.deepcopy(self.R)
        R2["moves"][u"本"][0][u"動いた行の中身"].append(ent(9, 9, P_, V_, u"なし", u"Prior1Year", u"偽", table=True))
        self.assertNotEqual(base[u"E"]["T-4"][u"値"], norm(TP.build_E(R2, self.seal))[u"E"]["T-4"][u"値"])
        R2b = copy.deepcopy(self.R)
        R2b["moves"][u"本"][0][u"動いた行の中身"][0][10] = False                                  # 表の前期の列の欄を偽にすると 表の前期の列でない動いた行 が動く
        self.assertNotEqual(base[u"E"]["T-4"][u"値"], norm(TP.build_E(R2b, self.seal))[u"E"]["T-4"][u"値"])
        R3 = copy.deepcopy(self.R)
        R3["regress97"][u"書類"][1][u"P33E の動いた行"].pop(1)
        self.assertNotEqual(base[u"E"]["T-3"][u"値"], norm(TP.build_E(R3, self.seal))[u"E"]["T-3"][u"値"])
        R4 = copy.deepcopy(self.R)
        R4["inject"][u"行"][SECTION_B][0]["P33E"] = bcell(G, u"CurrentYear")
        self.assertNotEqual(base[u"E"]["T-6"][u"値"], norm(TP.build_E(R4, self.seal))[u"E"]["T-6"][u"値"])
        R5 = copy.deepcopy(self.R)
        R5["regress97"][u"T-1・T-9 engine の差分"][u"numstat"][ENGINE_FILES[0]] = [99, 0]
        self.assertEqual(MISS, TP.build_E(R5, self.seal)[u"E"]["T-1"][u"判定"])
        R6 = copy.deepcopy(self.R)
        R6["regress97"][u"T-8・T-10 の写し"]["T-10"][u"赤の試験"] = [u"他の試験"]
        self.assertEqual(MISS, TP.build_E(R6, self.seal)[u"E"]["T-10"][u"判定"])


# ================================================================ 既知の答えのある小さい入力(部品の関数)
HEAD = u"| 項目 | 当期 | 前期 | 増減 |"
ROW = u"| 売上高 | 120億円 | 100億円 | +20.0% |"


class KnownAnswerTest(unittest.TestCase):
    def test_k_1_table_sites_follow_the_site_rule_of_the_seal(self):
        prof = V.PROFILES["P33E"]
        sents = [u"本文です。", HEAD, ROW, u"| 営業利益 | 12億円 | 10億円 | +20.0% |", u"説明", u"| 項目 | 2026年3月期 | 2025年3月期 |", u"| 売上高 | 120億円 | 100億円 |"]
        got = TP.table_sites(sents, prof)
        self.assertEqual([2, 3], [i for i, _c, _p in got])
        i, (ca, cb), (pa, pb) = got[0]
        self.assertEqual((u" 120億円", u" 100億円"), (sents[i][ca:cb], sents[i][pa:pb]))
        # 当たらない: 見出しが使えない(年だけ・前年同期比・前期 2 列)・セルの数が違う・セルに数が 2 つ・セルに数が無い
        self.assertEqual([], TP.table_sites([u"| 項目 | 当期 | 前年同期比 |", u"| 売上高 | 120億円 | 120.0% |"], prof))
        self.assertEqual([], TP.table_sites([u"| 項目 | 当期 | 前期 | 前年 |", u"| 売上高 | 120億円 | 100億円 | 90億円 |"], prof))
        self.assertEqual([], TP.table_sites([HEAD, u"| 売上高 | 120億円 | 100億円 |"], prof))
        self.assertEqual([], TP.table_sites([HEAD, u"| 売上高 | 120億円と130億円 | 100億円 | +20.0% |"], prof))
        self.assertEqual([], TP.table_sites([HEAD, u"| 売上高 | 120億円 | - | +20.0% |"], prof))
        self.assertEqual([], TP.table_sites([u"| 項目 | 前期 |", u"| 売上高 | 100億円 |"], prof))                       # 当期の列が無い表は site にしない(TP は当期のセルが要る)
        self.assertEqual([], TP.table_sites([HEAD], prof))                                                            # 見出しだけ

    def test_k_2_locate_finds_a_sentence_that_occurs_once(self):
        self.assertEqual(3, TP.locate(u"abcdef", u"def"))
        self.assertIsNone(TP.locate(u"abcabc", u"abc"))
        self.assertIsNone(TP.locate(u"abc", u"zzz"))

    def test_k_3_result_word_and_cell_of_follow_state_and_period(self):
        self.assertEqual(TP.PASSED_WORD, TP.result_word({u"対応": True, u"state": G, u"期": u"CurrentYear"}))
        self.assertEqual(TP.NAMED_PRIOR_WORD, TP.result_word({u"対応": True, u"state": V_, u"期": u"Prior1Year"}))
        self.assertEqual(TP.NAMED_OTHER_WORD, TP.result_word({u"対応": True, u"state": V_, u"期": u"CurrentYear"}))
        self.assertEqual(TP.NAMED_OTHER_WORD, TP.result_word({u"対応": True, u"state": V_, u"期": u"Prior2Year"}))
        self.assertEqual(U_, TP.result_word({u"対応": True, u"state": U_, u"期": u"なし"}))
        self.assertEqual(TP.UNMAPPED_WORD, TP.result_word({u"対応": False, u"state": None, u"期": u"なし"}))
        c = TP.cell_of({"state": G, "pointers": ["xbrl:jppfs_cor:NetSales@Prior1YearDuration"]}, True)
        self.assertEqual([(u"対応", True), (u"state", G), (u"期", u"Prior1Year"), (u"結果", TP.PASSED_WORD)], list(c.items()))
        c = TP.cell_of({"state": G, "pointers": []}, False)                                     # 対応が付かないとき claim があっても欄は対応なし
        self.assertEqual([(u"対応", False), (u"state", None), (u"期", u"なし"), (u"結果", TP.UNMAPPED_WORD)], list(c.items()))
        self.assertEqual(TP.UNMAPPED_WORD, TP.cell_of(None, True)[u"結果"])

    def test_k_4_message_numbers_read_the_engine_commit_message_and_nothing_else(self):
        m = TP.message_numbers_t(u"x。変異 12 本全部赤。y。全数(clone)で赤は axis3 test_9 の 1 本だけ(tests/measure 2 通りの順とも 5,191 passed / 34 skipped / 1 failed)= 期待どおり")
        self.assertEqual((12, 12), (m["T-8"][u"変異の本数"], m["T-8"][u"赤"]))
        self.assertEqual(([u"axis3 test_9"], 1, 5191, 34, 1), (m["T-10"][u"赤の試験"], m["T-10"][u"赤の本数"], m["T-10"][u"tests/measure"]["passed"], m["T-10"][u"tests/measure"]["skipped"],
                                                         m["T-10"][u"tests/measure"]["failed"]))
        self.assertEqual({"T-8": None, "T-10": None}, dict(TP.message_numbers_t(u"")))
        self.assertIsNone(TP.message_numbers_t(u"変異 12 本赤")["T-8"])
        self.assertIsNone(TP.message_numbers_t(u"全数で赤は axis3 test_9 の 1 本だけ")["T-10"])

    def test_k_5_t8_and_t10_values(self):
        b = BOUNDS_PIN["T-8"]
        self.assertEqual({u"赤": 10, u"変異の本数": 10, u"写した全部赤の本数": 12}, dict(TP.t8_value({"T-8": {u"変異の本数": 12, u"赤": 12}}, b)))
        self.assertIsNone(TP.t8_value({"T-8": {u"変異の本数": 12, u"赤": 11}}, b))                  # 全部赤でない
        self.assertIsNone(TP.t8_value({"T-8": {u"変異の本数": 9, u"赤": 9}}, b))                    # 封の本数に足りない
        self.assertIsNone(TP.t8_value({"T-8": None}, b))
        self.assertIsNone(TP.t8_value({}, b))
        v = TP.t10_value({"T-10": {u"赤の試験": [u"axis3 test_9"], u"赤の本数": 1, u"tests/measure": {"failed": 1}}})
        self.assertEqual((u"axis3 test_9", 1, 0), (v[u"赤の試験"][0], v[u"赤の本数"], v[u"ほかの赤"]))
        self.assertEqual(2, TP.t10_value({"T-10": {u"赤の試験": [u"x"], u"赤の本数": 1, u"tests/measure": {"failed": 3}}})[u"ほかの赤"])
        self.assertIsNone(TP.t10_value({"T-10": {u"赤の試験": [u"x"], u"赤の本数": 2, u"tests/measure": {"failed": 1}}}))
        self.assertIsNone(TP.t10_value({}))

    def test_k_6_the_prediction_table_rows_have_a_fixed_shape(self):
        P = TP.seal_pred_rows(read(SEAL_REL))
        self.assertEqual(list(SG.PRED_IDS), list(P))
        for k, (a, p, o) in P.items():
            self.assertTrue(a.strip() and p.strip() and o.strip(), k)
        self.assertEqual(list(SG.K_IDS), list(TP.seal_k_rows(read(SEAL_REL))))

    def test_k_7_the_script_and_the_history_agree_on_the_engine_link(self):
        self.assertEqual(norm(link_at_history())[u"numstat"], norm(TP.PB.engine_numstat()))
        link = norm(XR.engine_link())
        want = norm(link_at_history())
        for k in (u"封の commit", u"engine の commit", u"engine の変更 file", u"engine の挿入の行数", u"engine の削除の行数", u"直した file(M)", u"新しい file(A)", u"消した file(D)", u"tests の変更 file"):
            self.assertEqual(want[k], link[k], k)

    def test_k_8_bar_sentences_and_the_table_prior_view(self):
        self.assertEqual(2, TP.bar_sentences([HEAD, u"本文", ROW, u" | x |"][:3] + [u"  | y |"]) - 1 if False else TP.bar_sentences([HEAD, u"本文", ROW]))
        self.assertEqual(0, TP.bar_sentences([u"本文", u"x | y"]))
        sents = [HEAD, ROW]
        keys = E_._table_prior_keys_2026_11_09(sents, V.P33E)
        a = [a for (a, _b, *_r) in E_._numbers_of(V.P33E, ROW)][1]
        self.assertEqual({(ROW, a)}, keys)
        self.assertTrue(TP.is_table_prior(sents, keys, 1, a))
        self.assertFalse(TP.is_table_prior(sents, keys, 1, a + 1))                      # 位置が違う
        self.assertFalse(TP.is_table_prior(sents, keys, 0, a))                          # 文の番号が違う(見出し)
        self.assertFalse(TP.is_table_prior(sents, keys, 9, a))                          # 文の番号が範囲の外
        self.assertFalse(TP.is_table_prior(sents, keys, -1, a))
        self.assertFalse(TP.is_table_prior(sents, keys, None, a))

    def test_k_9_the_a_rows_rename_only_the_link_key(self):
        r = collections.OrderedDict([(u"id", u"x"), (PB.LINK_KEY, True), (u"形", u"既存")])
        out = TP.inject_a_rows([r])
        self.assertEqual([u"id", u"P33E の土台に対応", u"形"], list(out[0]))
        self.assertEqual([True], [out[0][u"P33E の土台に対応"]])


# ================================================================ 手順: 合成の claim で script の関数を通す(lib は本物・通信しない)
CUR_VALUES, PRI_VALUES = (120, 12, 50), (100, 10, 50)


def toy_claims_by_key(zb, text, pname):
    u"""``claims_by_key`` の合成版。数の値が当期の fact の値(120・12・50 億)なら当期の fact、前期の fact の値(100・10・50 億)なら前期の fact に結ぶ。
    P33E は表の前期の列の数を前期の fact に結び(前期の値なら GROUNDED・当期の値だけなら前期の fact を名指して VALUE_MISMATCH)、それ以外の数と P32E は当期の列と同じ(当期の値なら当期の fact に GROUNDED・
    前期の値だけなら当期の fact を名指して VALUE_MISMATCH)。どちらの値でもなければ POINTER_NOT_FOUND。"""
    from adapters.xbrl import extract as EX
    prof = V.PROFILES[pname]
    sents = EX.split_sentences(text, True)
    keys = E_._table_prior_keys_2026_11_09(sents, prof) if pname == "P33E" else set()
    cur_p, pri_p = "xbrl:jppfs_cor:NetSales@CurrentYearDuration", "xbrl:jppfs_cor:NetSales@Prior1YearDuration"
    rows = {}
    for i, s in enumerate(sents):
        for (a, b, _sg, _un, _pr) in E_._numbers_of(prof, s):
            m = re.match(r"\s*([\d.]+)", s[a:b])
            val = int(float(m.group(1))) if m else None
            in_c, in_p = val in CUR_VALUES, val in PRI_VALUES
            if (s, a) in keys:
                st, ptr = (G, pri_p) if in_p else ((V_, pri_p) if in_c else (P_, None))
            else:
                st, ptr = (G, cur_p) if in_c else ((V_, cur_p) if in_p else (P_, None))
            rows[(i, a)] = {"kind": "num", "state": st, "pointers": [ptr] if ptr else []}
    return rows, sents


class TableBookFlowTest(unittest.TestCase):
    u"""``table_book``(表の期の入れ替え TP・TC)を合成の claim で通す。site の条件・対応の条件を 1 つずつ外した差し替えで結果が替わる(= 条件の変異が赤になる)。"""

    def run_book(self, text, claims=toy_claims_by_key):
        item = {u"docID": "DOC1", u"form": "F3", u"model": "m1"}
        with Patch() as pt:
            pt.set(TP, "claims_by_key", claims)
            pt.set(TP.GEN, "read_zip", lambda row, caches: b"zip")
            pt.set(TP.RUN, "read_text", lambda name, it, d: text)
            return TP.table_book(("aiforms", "DOC1_F3_m1", item, {}, "dir", {}))

    GOOD = HEAD + u"\n" + ROW + u"\n" + u"| 営業利益 | 12億円 | 10億円 | +20.0% |"

    def test_w_1_a_good_table_row_gives_one_tp_and_one_tc_with_known_answers(self):
        name, form, counts, rows = self.run_book(HEAD + u"\n" + ROW)
        self.assertEqual("F3", form)
        self.assertEqual([(u"site 候補(見出しの前期 1 列・当期 1 列・セルに数 1 つずつ)", 1), (u"土台が合わない", 0), (u"2 つのセルの字が同じ", 0), (u"行の字が文に 1 回でない", 0), (u"採った site", 1)],
                         [(k, counts[k]) for k in list(counts)[1:]])
        self.assertEqual([(u"DOC1_F3_m1-TT-001-TP"), (u"DOC1_F3_m1-TT-001-TC")], [r[u"id"] for r in rows])
        tp, tc = rows
        # 注入の文は、前期のセルの字が 120億円(TP)・当期のセルの字が 100億円(TC)。toy では P32E は当期の fact に GROUNDED、P33E は前期の fact を名指して VALUE_MISMATCH(TP)
        self.assertEqual((TP.PASSED_WORD, TP.NAMED_PRIOR_WORD), (tp["P32E"][u"結果"], tp["P33E"][u"結果"]))
        self.assertEqual([u"対応", u"state", u"期", u"結果"], list(tp["P33E"]))
        self.assertTrue(tp["P32E"][u"対応"] and tp["P33E"][u"対応"] and tc["P32E"][u"対応"] and tc["P33E"][u"対応"])
        self.assertEqual([u"TP", u"TC"], [tp[u"型"], tc[u"型"]])

    def test_w_2_each_site_condition_excludes_its_row_and_counts_it(self):
        # 2 つのセルの字が同じ
        _n, _f, c, rows = self.run_book(HEAD + u"\n" + u"| 売上高 | 50億円 | 50億円 | +0.0% |")                 # 当期の値と前期の値が同じ(50 億は両方の fact の値)
        self.assertEqual(([], 1), (rows, c[u"2 つのセルの字が同じ"]))
        # 行の字が文に 1 回でない(同じ行が 2 回)
        _n, _f, c, rows = self.run_book(HEAD + u"\n" + ROW + u"\n" + ROW)
        self.assertEqual(([], 2), (rows, c[u"行の字が文に 1 回でない"]))
        # 土台が合わない(前期のセルの字が 100 億でも 120 億でもない = 土台の claim が GROUNDED でない)
        _n, _f, c, rows = self.run_book(HEAD + u"\n" + u"| 売上高 | 120億円 | 90億円 | +20.0% |")
        self.assertEqual(([], 1), (rows, c[u"土台が合わない"]))
        # 見出しが使えない表は site 候補にも入らない
        _n, _f, c, rows = self.run_book(u"| 項目 | 2026年3月期 | 2025年3月期 |\n| 売上高 | 120億円 | 100億円 |")
        self.assertEqual(([], 0), (rows, c[u"site 候補(見出しの前期 1 列・当期 1 列・セルに数 1 つずつ)"]))

    def test_w_3_the_site_condition_check_goes_red_when_a_condition_is_dropped(self):
        u"""条件(2 つのセルの字が同じ行を除く)を外した版の ``table_book`` を同じ file の字から作って走らせると、字が同じ行も採る(= w_2 が赤になる形)。
        外した版と正しい版を同じ入力で走らせ、行の数が替わることで固定する。"""
        src = read(SCRIPT_REL)
        i = src.index(u"def table_book(")
        j = src.index(u"\n\n\ndef table_job(")
        fn = src[i:j]
        block = u"        if cur_txt == pri_txt:\n            counts[u\"2 つのセルの字が同じ\"] += 1\n            continue\n"
        self.assertIn(block, fn)
        broken = fn.replace(block, u"")
        self.assertNotEqual(fn, broken)
        ns = dict(TP.__dict__)
        exec(compile(broken, "<broken_table_book>", "exec"), ns)
        item = {u"docID": "DOC1", u"form": "F3", u"model": "m1"}
        same_text = HEAD + u"\n" + u"| 売上高 | 50億円 | 50億円 | +0.0% |"
        _n, _f, c, rows = self.run_book(same_text)
        self.assertEqual(([], 1), (rows, c[u"2 つのセルの字が同じ"]))                            # 正しい版: 除く
        with Patch() as pt:
            pt.set(TP.GEN, "read_zip", lambda row, caches: b"zip")
            pt.set(TP.RUN, "read_text", lambda name, it, d: same_text)
            ns["claims_by_key"] = toy_claims_by_key
            _n, _f, c, rows = ns["table_book"](("aiforms", "DOC1_F3_m1", item, {}, "dir", {}))
        self.assertEqual(2, len(rows))                                                          # 条件を外した版: 字が同じ行も採る(= 正しい版の結果と違う)
        self.assertEqual(0, c[u"2 つのセルの字が同じ"])

    def test_w_4_a_mapping_that_fails_is_kept_as_unmapped(self):
        u"""注入後の文の列が元と違う長さ・替えた文と違う字・数の claim が無いときは、行を残して 対応なし にする。"""
        def short_sents(zb, text, pname):
            rows, sents = toy_claims_by_key(zb, text, pname)
            if "120億円 | 120億円" in text or "| 100億円 | 100億円" in text:                # 注入後の文
                return rows, sents + [u"余計な文"]
            return rows, sents
        _n, _f, c, rows = self.run_book(HEAD + u"\n" + ROW, claims=short_sents)
        self.assertEqual(2, len(rows))
        for r in rows:
            self.assertFalse(r["P32E"][u"対応"] or r["P33E"][u"対応"])
            self.assertEqual(TP.UNMAPPED_WORD, r["P33E"][u"結果"])

        def changed_sent(zb, text, pname):
            rows, sents = toy_claims_by_key(zb, text, pname)
            if "120億円 | 120億円" in text:
                sents = [s.replace(u"売上高", u"売上") for s in sents]
            return rows, sents
        _n, _f, c, rows = self.run_book(HEAD + u"\n" + ROW, claims=changed_sent)
        tp = [r for r in rows if r[u"型"] == u"TP"][0]
        self.assertFalse(tp["P33E"][u"対応"])

        def no_claim(zb, text, pname):
            rows, sents = toy_claims_by_key(zb, text, pname)
            if "120億円 | 120億円" in text:
                rows = dict((k, v) for k, v in rows.items() if k[0] != 1)
            return rows, sents
        _n, _f, c, rows = self.run_book(HEAD + u"\n" + ROW, claims=no_claim)
        tp = [r for r in rows if r[u"型"] == u"TP"][0]
        self.assertFalse(tp["P33E"][u"対応"])

    def test_w_5_table_job_adds_the_docid_and_keeps_the_rows(self):
        item = {u"docID": "DOC1", u"form": "F3", u"model": "m1"}
        with Patch() as pt:
            pt.set(TP, "claims_by_key", toy_claims_by_key)
            pt.set(TP.GEN, "read_zip", lambda row, caches: b"zip")
            pt.set(TP.RUN, "read_text", lambda name, it, d: HEAD + u"\n" + ROW)
            name, rows, counts = TP.table_job(("aiforms", "DOC1_F3_m1", item, {}, "dir", {}))
        self.assertEqual("DOC1_F3_m1", name)
        self.assertEqual([u"docID", u"id", u"形", u"model", u"型", u"P32E", u"P33E"], list(rows[0]))
        self.assertEqual(1, counts[u"採った site"])

    def test_w_6_the_row_checks_accept_the_rows_the_script_makes(self):
        item = {u"docID": "DOC1", u"form": "F3", u"model": "m1"}
        with Patch() as pt:
            pt.set(TP, "claims_by_key", toy_claims_by_key)
            pt.set(TP.GEN, "read_zip", lambda row, caches: b"zip")
            pt.set(TP.RUN, "read_text", lambda name, it, d: self.GOOD)
            _n, rows, _c = TP.table_job(("aiforms", "DOC1_F3_m1", item, {}, "dir", {}))
        self.assertEqual(4, len(rows))
        seen = set()
        for r in rows:
            self.assertEqual([], b_row_problems(norm(r), seen))


    def test_w_7_the_tc_row_has_known_answers_and_the_position_of_the_current_cell(self):
        u"""TC(参考。当期のセルの数の字を前期のセルの字に替える)の既知の答え。監査 2026-11-10 の指摘: TC の作り(文・数の位置)は w_1 では id と型しか見ていなかった。
        ROW の当期のセルは 120億円・前期のセルは 100億円。TC の文は 当期のセル = 100億円・前期のセル = 100億円。数の位置は**当期のセルの数**の位置(前期のセルの位置ではない)。
        toy では当期の列の 100 億は 前期の fact の値で当期の fact の値でないので、P32E も P33E も 当期の fact を名指して VALUE_MISMATCH(規則 T は当期の列に効かない)。
        TC を TP と同じ作り(前期のセルに入れる)にすると当期のセルの 120 億が残って 通した になる。数の位置を前期のセルにすると P33E は前期の fact に GROUNDED、P32E は VALUE_MISMATCH になる。どちらも下の assert が赤になる。"""
        seen = []

        def spy(zb, text, pname):
            rows, sents = toy_claims_by_key(zb, text, pname)
            seen.append((pname, text))
            return rows, sents
        _n, _f, _c, rows = self.run_book(HEAD + u"\n" + ROW, claims=spy)
        tc = [r for r in rows if r[u"型"] == u"TC"]
        tp = [r for r in rows if r[u"型"] == u"TP"]
        self.assertEqual(1, len(tc))
        self.assertEqual(1, len(tp))
        tc = tc[0]
        for p in ("P32E", "P33E"):
            self.assertEqual([(u"対応", True), (u"state", V_), (u"期", u"CurrentYear"), (u"結果", TP.NAMED_OTHER_WORD)], list(tc[p].items()), p)
        # 注入後の文: TC は 当期のセルだけが 100億円 になり、前期のセルは 100億円 のまま(= 同じ字が 2 つ)。TP は前期のセルが 120億円 になる
        texts = set(t for _p, t in seen)
        self.assertIn(HEAD + u"\n" + u"| 売上高 | 100億円 | 100億円 | +20.0% |", texts)
        self.assertIn(HEAD + u"\n" + u"| 売上高 | 120億円 | 120億円 | +20.0% |", texts)
        # TP の答え(TC と取り違えない): P32E は 当期の fact に GROUNDED、P33E は 前期の fact を名指して VALUE_MISMATCH
        self.assertEqual((TP.PASSED_WORD, TP.NAMED_PRIOR_WORD), (tp[0]["P32E"][u"結果"], tp[0]["P33E"][u"結果"]))


class MovesFlowTest(unittest.TestCase):
    u"""``judge_book_t``(表の前期の列の数か)と ``doc_job_t``(行頭が | の文・表の前期の列の数)を合成の入力で通す。"""

    SENTS = [HEAD, ROW, u"本文の 100億円 です。"]

    def _a(self):
        return [a for (a, _b, *_r) in E_._numbers_of(V.P33E, ROW)][1]

    def test_w_10_judge_book_t_marks_a_moved_row_that_is_a_table_prior_column_number(self):
        a = self._a()
        head = collections.OrderedDict([(u"動いた行の中身", [[u"num", 1, a, V_, G, u"CurrentYear", u"Prior1Year", u"真", EXISTING, False],
                                                      [u"num", 1, a + 1, V_, G, u"CurrentYear", u"Prior1Year", u"真", EXISTING, False],
                                                      [u"num", 2, 5, V_, G, u"CurrentYear", u"Prior1Year", u"真", EXISTING, False],
                                                      [u"num", 7, a, V_, G, u"CurrentYear", u"Prior1Year", u"真", EXISTING, False]])])
        with Patch() as pt:
            pt.set(PB, "judge_book_pb", lambda job: head)
            pt.set(TP.GEN, "read_zip", lambda row, caches: b"zip")
            pt.set(TP.RUN, "read_text", lambda name, it, d: u"t")
            pt.set(TP.PR, "build_modified_zip", lambda zb, text: (b"zm", None))
            pt.set(TP.RUN, "sentence_list", lambda zm, prof: self.SENTS)
            out = TP.judge_book_t(("aiforms", "n", {}, {}, "d", {}))
        self.assertEqual([True, False, False, False], [x[10] for x in out[u"動いた行の中身"]])
        self.assertEqual((2, 1), (out[u"行頭が | の文の数"], out[u"表の前期の列の数"]))

    def test_w_11_judge_book_t_marks_nothing_when_the_flag_function_is_all_false(self):
        a = self._a()
        head = collections.OrderedDict([(u"動いた行の中身", [[u"num", 1, a, V_, G, u"CurrentYear", u"Prior1Year", u"真", EXISTING, False]])])
        with Patch() as pt:
            pt.set(PB, "judge_book_pb", lambda job: head)
            pt.set(TP.GEN, "read_zip", lambda row, caches: b"zip")
            pt.set(TP.RUN, "read_text", lambda name, it, d: u"t")
            pt.set(TP.PR, "build_modified_zip", lambda zb, text: (b"zm", None))
            pt.set(TP.RUN, "sentence_list", lambda zm, prof: [u"本文", u"数は 100億円 です。"])      # 表が無い文の列
            out = TP.judge_book_t(("aiforms", "n", {}, {}, "d", {}))
        self.assertEqual([False], [x[10] for x in out[u"動いた行の中身"]])
        self.assertEqual((0, 0), (out[u"行頭が | の文の数"], out[u"表の前期の列の数"]))

    def test_w_12_doc_job_t_adds_the_table_counts_of_the_original_text(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            path = os.path.join(d, "z.zip")
            with open(path, "wb") as fh:
                fh.write(b"zip")
            with Patch() as pt:
                pt.set(XR, "doc_job", lambda args: {u"doc": u"DOC1", u"keyed": {}})
                pt.set(TP.RUN, "sentence_list", lambda zb, prof: self.SENTS)
                res = TP.doc_job_t(("DOC1", False, "x", (), path))
            self.assertEqual((2, 1), res[u"表"])
            with Patch() as pt:
                pt.set(XR, "doc_job", lambda args: {u"doc": u"DOC1", u"keyed": {}})
                pt.set(TP.RUN, "sentence_list", lambda zb, prof: [u"本文", u"x"])
                res = TP.doc_job_t(("DOC1", False, "x", (), path))
            self.assertEqual((0, 0), res[u"表"])

    def test_w_13_a_run_that_stops_before_writing(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            out = os.path.join(d, "x.json")
            for fn in (TP.run_moves, TP.run_regress97, TP.run_inject):
                with self.assertRaises(TP.Stop):
                    fn(root=ROOT, procs=1, only="X", out=None, say=lambda *a: None)                # --only で --out が無い
                with open(out, "w") as fh:
                    fh.write("{}")
                with self.assertRaises(TP.Stop):
                    fn(root=ROOT, procs=1, only=None, out=out, say=lambda *a: None)                # 出力が既に在る
                os.remove(out)


# ================================================================ 並べる順に依らない(pytest の引数の順で前の便の門が赤くならない)
class OrderIndependenceTest(unittest.TestCase):
    u"""T の script・門を読み込むと、PB・RB・T9 の script が決まった名前で ``sys.modules`` に登録した module(``--procs 2`` の pickle が引く)を上書きしてしまう。
    RB・PB・T5Y の結果の門を T の門より先に並べると、先に読まれた門が持つ object と ``sys.modules`` の object が別になり赤くなる(2026-11-06 の欠陥と同じ型)。
    T の門の ``load_module`` と script の ``load_module`` は読み込みの前後で ``sys.modules`` に在った名前を元の object に戻す。"""

    def _changed(self, before):
        return sorted(k for k, v in before.items() if sys.modules.get(k) is not v)

    def test_o_1_loading_the_tperiod_script_again_leaves_every_registered_name_as_it_was(self):
        before = dict(sys.modules)
        self.assertIn(RR.XR.__name__, before)                                                        # 前提: RB の script の登録名が在る
        probe = "tperiod_script_order_probe"
        try:
            mod = SG.load_module(SCRIPT_REL, probe)
            self.assertIsNot(mod.XR, RR.XR)                                                           # 前提: 読み直しは別の object を作る(上書きの機会がある)
            self.assertEqual([], self._changed(before))
            self.assertIs(sys.modules.get(RR.XR.__name__), before[RR.XR.__name__])                  # 読み込みの前に居た object のまま
        finally:
            sys.modules.pop(probe, None)

    def test_o_2_loading_another_gate_through_the_result_gate_loader_leaves_every_name_as_it_was(self):
        before = dict(sys.modules)
        probe = "pbind_result_gate_order_probe"
        try:
            load_module("tests/measure/test_xbrl_pswap_result.py", probe)
            self.assertEqual([], self._changed(before))
        finally:
            sys.modules.pop(probe, None)

    def test_o_3_the_loader_does_not_hide_the_new_names_it_registers(self):
        u"""読み込んだ module 自身の名前は残る(script の ``--procs`` の pickle は自分の名前を引く)。"""
        probe = "tperiod_script_order_probe2"
        try:
            mod = SG.load_module(SCRIPT_REL, probe)
            self.assertIs(sys.modules.get(probe), mod)
        finally:
            sys.modules.pop(probe, None)

    def test_o_4_earlier_result_gates_before_this_gate_run_green_in_a_fresh_process(self):
        u"""pytest の引数で RB・PB・T5Y の結果の門を T の結果の門より先に並べる(欠陥の再現)。cache が無いと RB の試験は skip になり意味が無いので skip。
        **入れ子の走りが自分自身(この試験)を選ばない**: ``-k`` は ``test_o_4`` を選ばない字(``test_o_1_``〜``test_o_3_`` と RB の ``test_w_4_regress97``)にし、
        環境変数 ``TPERIOD_NESTED`` が立っている走りではこの試験を skip する(二重の守り。選び方を間違えると試験が試験を呼び続ける)。"""
        if os.environ.get("TPERIOD_NESTED"):
            self.skipTest(u"入れ子の走り(この試験は呼び返さない)")
        if not HAVE_CACHE:
            self.skipTest(u"cache が無い(RB の test_w_4 は skip になる)")
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/measure/test_xbrl_rmix_result.py", "tests/measure/test_xbrl_pbind_result.py", "tests/measure/test_xbrl_t5y_result.py",
               "tests/measure/test_xbrl_tperiod_result.py", "-k", "test_w_4_regress97 or test_o_1_ or test_o_2_ or test_o_3_"]
        self.assertNotIn("test_o_4", cmd[-1])
        r = subprocess.run(cmd, cwd=ROOT, env=dict(os.environ, TPERIOD_NESTED="1"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        self.assertEqual(0, r.returncode, r.stdout[-1500:])
        self.assertRegex(r.stdout, r"\d+ passed")


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
    u"""宣言(記録の docID の LATER_NAMING_FILES・script の LATER_HARNESS_FILES)は記録を走らせる便が足す。この便は記録を作らないので、記録が在るときだけ宣言を見る。
    宣言を調べる関数(``naming_problems``・``harness_problems``)は、足した宣言を 1 字壊した標本で赤になることをここで固定する。"""

    def test_h_1_naming_check_sees_a_missing_or_a_wrongly_declared_record(self):
        src = u'LATER_NAMING_FILES = ("%s", "%s", "%s")\n' % tuple(REC_REL.values())
        self.assertEqual([], naming_problems(src))
        for rel in REC_REL.values():
            self.assertNotEqual([], naming_problems(src.replace(u'"%s"' % rel, u'"x/%s"' % rel)), rel)
        self.assertNotEqual([], naming_problems(src.replace("LATER_NAMING_FILES", "LATER_NAMING_FILE")))
        self.assertNotEqual([], naming_problems(src.replace(u'")\n', u'", "%s")\n' % SG.GATE_RELS[0])))

    def test_h_2_harness_check_sees_a_missing_declaration(self):
        src = u'LATER_HARNESS_FILES = (("%s", "仕掛け持ち + 使う側", "有", "f", "x", "2026-11-09"),)\n' % SCRIPT_REL
        self.assertEqual([], harness_problems(src))
        self.assertNotEqual([], harness_problems(src.replace(SCRIPT_REL, u"x/" + SCRIPT_REL)))
        self.assertNotEqual([], harness_problems(src.replace("LATER_HARNESS_FILES", "LATER_HARNESS_FILE")))

    def test_h_3_the_previous_declarations_are_still_there(self):
        got = later_naming_files(read("tests/measure/test_xbrl_fresh_seal.py"))
        for rel in ("fixtures/xbrl/rmix/ai200_2026-11-04.json", "fixtures/xbrl/pbind/moves_200_2026-11-06.json", "fixtures/xbrl/pbind/inject_2026-11-06.json", "fixtures/xbrl/t5y/inject_2026-11-06.json"):
            self.assertIn(rel, got)

    def test_h_4_when_the_records_exist_they_are_declared(self):
        if not records_exist():
            self.skipTest(u"記録が無い(記録を走らせた後に走る)")
        self.assertEqual([], naming_problems(read("tests/measure/test_xbrl_fresh_seal.py")))
        self.assertEqual([], harness_problems(read("tests/measure/test_xbrl_inject_harness_review.py")))


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
        self.assertEqual(SGR.T_FP, fp["adapter_xbrl_py_sha256"])                                 # 全 file の束ねた指紋は T の宣言した値(engine の commit の木と一致)


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
        J = TP.build_E(R, self.seal)
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


# ================================================================ 実書類を 1 本だけ通す使い捨ての走り(cache を読むだけ。記録は TMPDIR の下。cache が無ければ skip)
class RealRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HAVE_CACHE:
            raise unittest.SkipTest(u"cache が無い(実書類を通す試験は skip)")
        jobs = RM.load_jobs(ROOT, None)
        cls.job = [j for j in jobs if j[2][u"form"] == LIMIT_BOOK_FORM][0]
        cls.doc = cls.job[2][u"docID"]

    def _only_the_book(self, pt):
        real_jobs, real_books = RM.load_jobs, PI.load_books
        name = self.job[1]
        pt.set(RM, "load_jobs", lambda root=ROOT, only=None: [j for j in real_jobs(root, only) if j[1] == name])
        pt.set(PI, "load_books", lambda root=ROOT, only=None: [b for b in real_books(root, only) if b[1] == name])

    def test_x_1_regress97_one_document_passes_the_record_checks(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            out = os.path.join(d, "r97.json")
            rec = norm(TP.run_regress97(root=ROOT, procs=1, only=self.doc, out=out, say=lambda *a: None))
            self.assertEqual(rec, jload_abs(out))
        self.assertEqual(u"**--only の 1 書類だけ(本番の記録ではない)**", rec[u"範囲"])
        self.assertEqual([], regress97_problems(rec, False))
        self.assertEqual([], header_problems("regress97", rec, False))
        self.assertEqual([], clean_problems("regress97", rec))
        self.assertEqual(1, len(rec[u"書類"]))
        self.assertTrue(all(v[u"byte が同じ書類"] == 1 for v in rec[u"集計"][u"T-2 旗が偽の profile の byte 一致"].values()))      # 旗が偽の 10 profile は PB の便の記録と byte 一致
        self.assertEqual(norm(link_at_history()), rec[u"T-1・T-9 engine の差分"])

    def test_x_2_inject_one_book_passes_the_record_checks_and_reproduces_the_pb_p32e_cells(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            self._only_the_book(pt)
            out = os.path.join(d, "inj.json")
            rec = norm(TP.run_inject(root=ROOT, procs=1, only=self.doc, out=out, say=lambda *a: None, work_root=d))
        pb = pb_inject_record()[u"行"]
        bad = [x for x in inject_problems(rec, pb, False) if u"集計" in x or u"切り替え" in x or u"site" in x or u"行" in x]
        self.assertEqual([], bad)
        self.assertEqual([], header_problems("inject", rec, False))
        self.assertEqual([], clean_problems("inject", rec))
        ra, rb = rec[u"行"][SECTION_A], rec[u"行"][SECTION_B]
        self.assertGreater(len(rb), 0)                                                          # F3 の本には表の site が在る
        by_id = dict((r[u"id"], r) for r in pb)
        for r in ra:
            self.assertIn(r[u"id"], by_id)                                                      # (a) の行の id は PB の記録と同じ
            self.assertEqual(norm(by_id[r[u"id"]]["P30E"]), norm(r["P30E"]))                      # P30E の結果と state も同じ
        c = rec[u"集計の欄"]
        self.assertEqual(len(ra), c[u"T-2 PB の記録との照らし"][u"行の数"])
        for r in ra:
            self.assertEqual(norm(by_id[r[u"id"]]["P32E"][u"結果"]), r["P33E"][u"結果"], r[u"id"])   # P33E は PB の記録の P32E と同じ結果(表でない数は変わらない)
        tp = [r for r in rb if r[u"型"] == u"TP"]
        self.assertTrue(all(r["P32E"][u"結果"] == TP.PASSED_WORD for r in tp))                  # P32E は前期の列に当期の値を入れた TP を通す
        self.assertTrue(all(r["P33E"][u"結果"] != TP.PASSED_WORD for r in tp))                  # P33E は止める(この 1 本では)

    def test_x_3_moves_one_book_passes_the_record_checks(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            self._only_the_book(pt)
            out = os.path.join(d, "mv.json")
            rec = norm(TP.run_moves(root=ROOT, procs=1, only=self.doc, out=out, say=lambda *a: None))
        self.assertEqual(1, len(rec[u"本"]))
        self.assertEqual([], moves_problems(rec, False))
        self.assertEqual([], header_problems("moves", rec, False))
        self.assertEqual([], clean_problems("moves", rec))
        self.assertEqual(norm(TP.aggregate_moves_t(rec[u"本"])), rec[u"集計"])
        b = rec[u"本"][0]
        self.assertGreater(b[u"動いた行"], 0)                                                   # F3 の本は表の前期の列の数が動く
        self.assertTrue(all(x[10] is True for x in b[u"動いた行の中身"]))                       # 動いた行は全部表の前期の列の数


def jload_abs(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    unittest.main()
