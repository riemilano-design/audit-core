# -*- coding: utf-8 -*-
"""RB(丸め方の根拠が混ざる桁は両方の帯で照らす。P30E = P29E + RB)の測定の結果の門。封 docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md §5。

記録 3 つ(``fixtures/xbrl/rmix/``: ai200・inject・regress97)から、封 §3 の予測 D-1〜D-10 と §4 の採用の基準 K-1〜K-5 を**機械で求め**(予測の幅は封の字から読む。字のコピーにしない)、
結果の文書 ``docs/XBRL_ROUNDING_MIXED_ENGINE_RESULT_2026-11-04.md`` の表(``<!-- 門:start pred -->``・``<!-- 門:start judge -->`` の中)を記録から作り直した表と一行も違わないことを見る。
測定の script(``measure/xbrl_rmix_2026-11-04.py`` の ``build_J``・``render_pred``・``render_judge``)の関数を呼んで照らす。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文など)が無い・key_leaks が空・docID を持つ記録が ``LATER_NAMING_FILES`` に宣言されている・cache の前後が同じ・script の sha256 が現物と一致・
     engine の指紋が engine の commit の木から作り直した値と一致する。
  b  記録の中身が再計算と一致する: 本ごとの数の整合(GROUNDED の増減と動いた行・札の内訳)・集計(``aggregate``)・注入の集計(``inject_summaries``)・97 書類の集計(``summarize_docs``)・D-10(git の履歴から)。
  c  判定: 記録を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。採用は K-1〜K-5 を全部満たすときだけ。
  d  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 de23edc ⊏ engine を触った commit ⊏ 記録・結果の文書(script・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  g  変異: 小さい標本の記録 3 つと文書で同じ検査が緑 → 変異(記録の数 1 つ・表の 1 字・封の予測の 1 字・順序・記録の禁止欄・指紋の 1 字・cache の前後)で赤。

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


SG = load_module("tests/measure/test_xbrl_rmix_seal.py", "rmix_seal_gate_for_result")          # engine の commit を履歴から探す関数。門としては走らせない
PR = SG.PR                                                                                       # doc_blocks・prose_problems・order_problems・Repo
RM = load_module("measure/xbrl_rmix_2026-11-04.py", "rmix_script_for_gate")
RR = load_module("measure/xbrl_rmix_regress97_2026-11-04.py", "rmix_regress97_for_gate")
NF = RM.NF
GEN, RUN = RM.GEN, RM.RUN
TUNE = RUN.TUNE

SEAL_REL = RM.SEAL_REL
DOC_REL = RM.DOC_REL
SEAL_COMMIT_SHORT = RM.SEAL_COMMIT
REC_REL = collections.OrderedDict(RM.REC_REL)
REC_SCRIPT = {"ai200": "measure/xbrl_rmix_2026-11-04.py", "inject": "measure/xbrl_rmix_2026-11-04.py", "regress97": "measure/xbrl_rmix_regress97_2026-11-04.py"}
ENGINE_FILES = SG.ENGINE_FILES
NOT_GATED = PR.NOT_GATED
HIT, MISS = RM.HIT, RM.MISS
FORBIDDEN_KEYS = tuple(RUN.FORBIDDEN_KEYS) + (u"理由", u"根拠", u"周り", u"content")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = SG.DOCID_RE
FOR_RESULT_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
HAVE_CACHE = all(os.path.isdir(p) for p in RM.caches_all().values())
FP_KEY = {"ai200": u"engine の指紋", "inject": u"engine の指紋", "regress97": u"engine の指紋(この tree)"}
#: 封 §3・§4 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("D-1", (200, 200, 97, 97, 8)), ("D-2", (110.0, 135.0)), ("D-3", 0),
    ("D-4", collections.OrderedDict([(u"真", (90.0, 110.0)), (u"偽", (0.0, 12.0))])), ("D-5", (7, 7)), ("D-6", (60.0, 120.0)),
    ("D-7", collections.OrderedDict([(u"動いた行", (0.0, 5.0)), (u"失う行", 0)])),
    ("D-8", collections.OrderedDict([("T1_VALUE", (0.0, 1.0)), ("T8_REL", (2.0, 3.5))])), ("D-9", (78.0, 84.0)), ("D-10", (45.0, 75.0)),
    ("K-2", 0), ("K-3", collections.OrderedDict([(u"偽", 12.0), (u"真", 80.0)])), ("K-4", collections.OrderedDict([("T1_VALUE", 1.0), ("T8_REL", 3.5)])),
    ("K-5", collections.OrderedDict([(u"失う行", 0), (u"動いた行", 5.0)]))])
#: 注入の土台の字・限界の事実の字(測定の script の定数と同じでなければ赤)
BASE_WORD_PIN = u"無改変の文で P30E が GROUNDED の claim"
LIMIT_PIN = u"注入の仕掛け(N.scan)は万・億のコンマの数を断片に切るため、D-8・D-9 は万・億のコンマの数に注入した誤りを測っていない(封 §6 の 1)。測れるのは断片に切られない数の site だけ"
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)
G, V_, U_, P_ = "GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"


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


# ---------------------------------------------------------------- engine の指紋(engine の commit の木から作り直す)
_FP = []


def engine_fingerprint_at_commit():
    u"""engine の commit(履歴から探す)の木の ``adapters/xbrl`` と ``core/py/audit_core`` の .py から作った指紋 {adapter_xbrl_py_sha256, core_py_sha256}。"""
    if not _FP:
        seal, e = SG.engine_commit(REPO, PREFIX, SEAL_REL, ENGINE_FILES)
        if e is None:
            raise AssertionError(u"engine の commit が履歴に無い")
        from adapters.xbrl import verify_document as VD
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            arc = subprocess.run(["git", "archive", e, PREFIX + "adapters/xbrl", PREFIX + "core/py/audit_core"], cwd=REPO, stdout=subprocess.PIPE, check=True)
            subprocess.run(["tar", "-x", "-C", d], input=arc.stdout, check=True)
            a, _na = VD._py_digest(os.path.join(d, PREFIX, "adapters", "xbrl"))
            c, _nc = VD._py_digest(os.path.join(d, PREFIX, "core", "py", "audit_core"))
        _FP.append({"adapter_xbrl_py_sha256": a, "core_py_sha256": c})
    return _FP[0]


def link_at_history():
    u"""D-10 の欄を履歴から作り直す(測定の script とは別に書く)。"""
    seal, e = SG.engine_commit(REPO, PREFIX, SEAL_REL, ENGINE_FILES)
    num = [x for x in PR.git_in(REPO, "diff", "--numstat", seal, e, "--", PREFIX + "adapters", PREFIX + "core")[1].splitlines() if x]
    tests = [x for x in PR.git_in(REPO, "diff", "--name-status", seal, e, "--", PREFIX + "tests")[1].splitlines() if x]
    st = collections.Counter(t.split("\t")[0][0] for t in tests)
    return collections.OrderedDict([
        (u"封の commit", seal), (u"engine の commit", e),
        (u"engine の変更 file", sorted(x.split("\t")[2][len(PREFIX):] for x in num)),
        (u"engine の挿入の行数", sum(int(x.split("\t")[0]) for x in num)), (u"engine の削除の行数", sum(int(x.split("\t")[1]) for x in num)),
        (u"直した file(M)", st.get("M", 0)), (u"新しい file(A)", st.get("A", 0)), (u"消した file(D)", st.get("D", 0)), (u"tests の変更 file", len(tests))])


# ---------------------------------------------------------------- 封の字(a)
def norm_t(v):
    if isinstance(v, dict):
        return dict((k, norm_t(x)) for k, x in v.items())
    if isinstance(v, (tuple, list)):
        return [float(x) for x in v]
    return float(v)


def bounds_problems(seal):
    u"""封の字から読んだ予測の幅が、ここに留めた値と同じか。"""
    got = RM.seal_bounds(seal)
    out = []
    for k, v in BOUNDS_PIN.items():
        g = got.get(k)
        if json.dumps(norm_t(g), sort_keys=True) != json.dumps(norm_t(v), sort_keys=True):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, g, v))
    if list(RM.seal_pred_rows(seal)) != list(SG.PRED_IDS):
        out.append(u"封 §3 の予測の行が D-1〜D-10 でない")
    return out


# ---------------------------------------------------------------- 記録(a)(b)
def walk(o):
    return list(RUN.walk_keys(o))


def r97_docs_from_prev():
    u"""N の便の regress97 の記録の書類の一覧 {docID: 行}。"""
    return dict((r["docID"], r) for r in jload(RR.PREV_RECORD_REL)[u"書類"])


def header_problems(k, rec, script_rel):
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"%s: 封の名か commit が違う" % k)
    if rec.get(u"この script の sha256") != sha256_rel(script_rel):
        out.append(u"%s: この script の sha256 が現物と違う" % k)
    if k in ("ai200", "inject"):
        if rec.get(u"numfix script の sha256") != sha256_rel(SG.READ_ONLY_RELS[0]):
            out.append(u"%s: numfix script の sha256 が現物と違う" % k)
        if rec.get(u"前の便の run script の sha256") != sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py"):
            out.append(u"%s: 前の便の run script の sha256 が現物と違う" % k)
        if rec.get(u"生成の script の sha256") != sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py"):
            out.append(u"%s: 生成の script の sha256 が現物と違う" % k)
        want = {"ai200": sha256_rel(RM.N_AI200_REL), "regress97": sha256_rel(RM.N_REGRESS97_REL)}
        if rec.get(u"N の便の記録の sha256") != want:
            out.append(u"%s: N の便の記録の sha256 が現物と違う" % k)
    if k == "regress97" and rec.get(u"numfix regress97 script の sha256") != sha256_rel(SG.READ_ONLY_RELS[1]):
        out.append(u"%s: numfix regress97 script の sha256 が現物と違う" % k)
    fp = rec.get(FP_KEY[k]) or {}
    want = engine_fingerprint_at_commit()
    for name in want:
        if fp.get(name) != want[name]:
            out.append(u"%s: engine の指紋 %s が engine の commit の木から作り直した値と違う" % (k, name))
    cb = rec.get(u"cache の前後") or {}
    if cb.get(u"変化なし") is not True or cb.get(u"前") != cb.get(u"後"):
        out.append(u"%s: cache の前後が同じでない" % k)
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


def book_problems(b):
    u"""本ごとの数の整合(自分の欄の間の関係)。"""
    out = []
    nm = b[u"name"]
    n = b[u"数の claim の数"]
    gr = b[u"GROUNDED の数"]
    ent = b[u"state が変わった行の中身"]
    if list(b[u"対応"]) != list(RM.PROFILES) or list(n) != list(RM.PROFILES):
        out.append(u"%s: 対応か数の claim の数の欄の profile が違う" % nm)
    if b[u"P29E と P30E で数の claim の鍵が同じ"] and n["P29E"] != n["P30E"]:
        out.append(u"%s: 鍵が同じなのに P29E と P30E の数の claim の数が違う" % nm)
    if gr["P29E"] > n["P29E"] or gr["P30E"] > n["P30E"]:
        out.append(u"%s: GROUNDED の数が数の claim の数より多い" % nm)
    if b[u"state が変わった行"] != len(ent) or b[u"動いた行"] < b[u"state が変わった行"]:
        out.append(u"%s: 動いた行か state が変わった行の数が中身と合わない" % nm)
    for x in ent:
        if len(x) != 7 or x[0] != u"num" or not isinstance(x[1], int) or not isinstance(x[2], int) or x[3] not in NF.STATES or x[4] not in NF.STATES or x[3] == x[4] \
                or x[5] not in (None,) + RM.LABEL_WORDS or x[6] not in (u"既存", u"新") or (x[6] == u"新" and x[5] is not None):
            out.append(u"%s: state が変わった行の中身の形がおかしい" % nm)
    dirs = collections.Counter(u"%s → %s" % (x[3], x[4]) for x in ent)
    if dict(b[u"動いた行の向き別"]) != dict(dirs):
        out.append(u"%s: 向き別が中身から数えた値と合わない" % nm)
    lost = sum(1 for x in ent if x[3] == G and x[4] != G)
    gained = [x for x in ent if x[3] != G and x[4] == G]
    if b[u"GROUNDED を失った行"] != lost or b[u"GROUNDED になった行"] != len(gained):
        out.append(u"%s: GROUNDED を失った行・なった行が中身から数えた値と合わない" % nm)
    lab = collections.Counter((x[5] or RM.NO_LABEL) for x in gained if x[6] == u"既存")
    if dict(b[u"GROUNDED になった既存の行の札"]) != dict((w, lab.get(w, 0)) for w in RM.LABEL_WORDS + (RM.NO_LABEL,)) or list(b[u"GROUNDED になった既存の行の札"]) != list(RM.LABEL_WORDS + (RM.NO_LABEL,)):
        out.append(u"%s: GROUNDED になった既存の行の札が中身から数えた値と合わない" % nm)
    if b[u"GROUNDED になった新しい行"] != sum(1 for x in gained if x[6] == u"新"):
        out.append(u"%s: GROUNDED になった新しい行が中身から数えた値と合わない" % nm)
    if b[u"P29E と P30E で数の claim の鍵が同じ"] and gr["P30E"] - gr["P29E"] != len(gained) - lost:
        out.append(u"%s: GROUNDED の増減が なった行 − 失った行 と合わない" % nm)
    if not isinstance(b[u"混ざる桁"], list) or b[u"混ざる桁"] != sorted(b[u"混ざる桁"]) or any(not isinstance(x, (int, float)) or isinstance(x, bool) for x in b[u"混ざる桁"]):
        out.append(u"%s: 混ざる桁が昇順の数の列でない" % nm)
    for x in b[u"K-2 の行"]:
        if len(x) != 7 or x[0] != u"num" or not isinstance(x[1], int) or not isinstance(x[2], int) or x[3] not in NF.STATES or x[4] not in NF.STATES \
                or any(y is not None and y not in NF.STATES for y in x[5:]):
            out.append(u"%s: K-2 の行の形が(種類, 文の番号, 位置, 前, 後, 今回の P29E, P30E)でない" % nm)
    f = b[u"旗が偽の byte 一致"]
    if f[u"一致"] != all(v for k, v in f.items() if k != u"一致") or f[u"P29E が N の便の記録と一致"] != (b[u"N の便の記録と違った欄"] == []):
        out.append(u"%s: 旗が偽の byte 一致が他の欄と合わない" % nm)
    if not isinstance(b[u"P27 の鍵が一意"], bool):
        out.append(u"%s: P27 の鍵が一意の欄が真偽でない" % nm)
    return out


def ai200_problems(rec, full):
    out = []
    if rec.get(u"profile") != list(RM.PROFILES):
        out.append(u"ai200: profile が (P28E, P29E, P30E) でない")
    books = rec[u"本"]
    for b in books:
        out += book_problems(b)
    try:
        agg = norm(RM.aggregate(books))
    except Exception as e:                                   # noqa: BLE001  壊れた記録は集計できない = 赤
        return out + [u"ai200: 本から集計を作れない(%s)" % type(e).__name__]
    if agg != rec[u"集計"]:
        out.append(u"ai200: 集計が本から作り直した値と違う")
    if not all(all(b[u"対応"].values()) for b in books):
        out.append(u"ai200: claim の並びが profile 間で対応しない本がある")
    if full:
        prior = []
        for src, p in RM.SOURCES.items():
            c = jload(p["claims"])
            prior += [(src, b) for b in c[u"本"] if not b.get(u"欠け")]
        if [(b[u"材料"], b[u"name"], b[u"docID"], b[u"form"], b[u"model"]) for b in books] != [(s, b[u"name"], b[u"docID"], b[u"form"], b[u"model"]) for s, b in prior]:
            out.append(u"ai200: 本の並びが前の便の claims の記録の本(160 + 40)と違う")
        if len(books) != 200:
            out.append(u"ai200: 本が 200 本でない")
        shas = collections.OrderedDict(
            [(u"%s_%s" % (src, k), sha256_rel(p[k])) for src, p in RM.SOURCES.items() for k in ("gen", "claims")] + [(u"%s_labels" % src, sha256_rel(rel)) for src, rel in RM.LABELS_REL.items()])
        if rec.get(u"入力の記録の sha256") != norm(shas):
            out.append(u"ai200: 入力の記録の sha256 が現物と違う")
        gens = dict((src, sha256_rel(p["gen"])) for src, p in RM.SOURCES.items())
        if rec.get(u"生成の記録の sha256") != gens:
            out.append(u"ai200: 生成の記録の sha256 が現物と違う")
        nb = dict((b[u"name"], b) for b in jload(RM.N_AI200_REL)[u"本"])
        for b in books:
            n = nb.get(b[u"name"])
            if n is None or [x[:5] for x in b[u"K-2 の行"]] != [x[:5] for x in n[u"同じ文に新しい行が無いのに変わった既存の行"]]:
                out.append(u"ai200: K-2 の行が N の便の記録と違う: %s" % b[u"name"])
                break
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(RM.caches_all())):
            out.append(u"ai200: cache の件数か名前が記録の前と違う")
    return out


def inject_problems(rec, full):
    out = []
    if rec.get(u"profile") != list(RM.INJECT_PROFILES):
        out.append(u"inject: profile が (P29E, P30E) でない")
    if rec[u"型"].get(u"土台") != BASE_WORD_PIN or RM.BASE_WORD != BASE_WORD_PIN:
        out.append(u"inject: 型.土台 の字が P30E が GROUNDED の claim でない")
    lim = rec.get(u"限界") or []
    if LIMIT_PIN not in lim or RM.LIMIT_SCAN != LIMIT_PIN:
        out.append(u"inject: 限界に事実の字(N.scan は万・億のコンマの数を断片に切る)が無い")
    want = collections.OrderedDict([(u"全体", sum(1 for r in rec[u"行"] if r.get(RM.LINK_KEY) is not True))])
    for t in RUN.INJECT_TYPES:
        want[t] = sum(1 for r in rec[u"行"] if r.get(u"型") == t and r.get(RM.LINK_KEY) is not True)
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
        linked = r.get(RM.LINK_KEY)
        unmapped = {u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}
        if not isinstance(linked, bool):
            out.append(u"inject: P29E の土台に対応の欄が真偽でない")
        elif not linked and norm(r["P29E"]) != unmapped:
            out.append(u"inject: P29E の土台に対応が無い行の P29E の欄が対応なしでない")
        if r["P30E"][u"対応"] is True and r["P30E"][u"結果"] == TUNE.LABEL_UNMAPPED:
            out.append(u"inject: P30E の欄の対応と結果が合わない")
        if r[u"型"] == "T8_REL" and (r.get("r") not in TUNE.T8_R_VALUES or not (1 <= r[u"r を決めた回"] <= TUNE.T8_TRIES)):
            out.append(u"inject: T8_REL の r が決めた値でない")
        for p in RM.INJECT_PROFILES:
            c = r[p]
            if c[u"結果"] not in labels:
                out.append(u"inject: 結果が classify の語でない")
            if not RUN.reason_ok(c[u"reason"]):
                out.append(u"inject: reason が符号の形でない")
    if any(n > RUN.INJECT_CAP for n in cnt.values()):
        out.append(u"inject: 1 本あたり型ごとの上限 %d を超えている" % RUN.INJECT_CAP)
    with Patch() as pt:
        pt.set(RUN, "PROFILES", RM.INJECT_PROFILES)
        summ, summ_cmp = (norm(x) for x in RM.inject_summaries(rec[u"行"]))
    if summ != rec[u"集計"] or rec[u"注入の行の数"] != len(rec[u"行"]):
        out.append(u"inject: 集計が行から作り直した値と違う")
    if summ_cmp != rec.get(RM.COMPARE_KEY):
        out.append(u"inject: 比較用の集計(P29E にも対応が付く site だけ)が行から作り直した値と違う")
    if full:
        names = [b[u"name"] for src in RM.SOURCES.values() for b in jload(src["claims"])[u"本"] if not b.get(u"欠け")]
        if list(rec[u"本ごとの数え"]) != names:
            out.append(u"inject: 本ごとの数えの本が 200 本(前の便の claims の並び)でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(RM.caches_all())):
            out.append(u"inject: cache の件数か名前が記録の前と違う")
    return out


def regress97_problems(rec, full):
    out = []
    docs = rec[u"書類"]
    try:
        T = norm(RR.summarize_docs(docs))
    except Exception as e:                                   # noqa: BLE001
        return [u"regress97: 書類から集計を作れない(%s)" % type(e).__name__]
    got = dict((k, v) for k, v in rec[u"集計"].items() if k != u"D-10 engine の留めの連動で直す試験 file")
    if T != got:
        out.append(u"regress97: 集計が書類から作り直した値と違う")
    for d in docs:
        for n, a, b in RR.PAIRS:
            mv = d[u"動いた行と増えた行"][n]
            if sum(mv[u"増えた行の state"].values()) != mv[u"増えた行"]:
                out.append(u"regress97: 増えた行の state の和が増えた行と合わない")
            if d[u"claims"][b] - d[u"claims"][a] != mv[u"増えた行"] - mv[u"消えた行"]:
                out.append(u"regress97: claim の数の差が 増えた行 − 消えた行 と合わない")
        if sorted(d[u"4 state"]) != sorted(RR.NOW_PROFILES):
            out.append(u"regress97: 4 state の profile が違う")
    if full:
        prev = r97_docs_from_prev()
        if sorted(d[u"docID"] for d in docs) != sorted(prev):
            out.append(u"regress97: 書類が N の便の記録の 97 書類と違う")
        for d in docs:
            pr = prev.get(d[u"docID"])
            if pr is None:
                continue
            if d[u"前の便の記録の sha256"] != dict((p, pr[u"出力の sha256(engine の欄を除く)"][p]) for p in RR.BASE_PROFILES) or d[u"zip の sha256"] != pr[u"zip の sha256"]:
                out.append(u"regress97: 前の便の記録の sha256 か zip の sha256 が N の便の記録と違う")
        if rec[u"前の便の記録の sha256"] != sha256_rel(RR.PREV_RECORD_REL):
            out.append(u"regress97: 前の便の記録の sha256 が現物と違う")
        if rec[u"集計"][u"D-10 engine の留めの連動で直す試験 file"] != norm(link_at_history()):
            out.append(u"regress97: D-10 が git の履歴から作り直した値と違う")
        if len(docs) != 97:
            out.append(u"regress97: 書類が 97 でない")
    return out


def record_problems(R, full=True):
    u"""記録 3 つの検査(禁止欄・鍵・script の sha256・engine の指紋・cache・再計算)。問題の列。"""
    out = []

    def safe(label, fn, *a):
        try:
            return fn(*a)
        except Exception as e:                               # noqa: BLE001  壊れた記録は検査できない = 赤(例外で落とさず問題に数える)
            return [u"%s: 検査できない(%s)" % (label, type(e).__name__)]
    for k, rec in R.items():
        out += safe(k, clean_problems, k, rec)
        out += safe(k, header_problems, k, rec, REC_SCRIPT[k])
    out += safe("ai200", ai200_problems, R["ai200"], full)
    out += safe("inject", inject_problems, R["inject"], full)
    out += safe("regress97", regress97_problems, R["regress97"], full)
    if full and R["regress97"].get(u"範囲") != u"全 97 書類":
        out.append(u"regress97: 範囲が全 97 書類でない")
    return out


def judge_problems(R, seal):
    u"""判定の関数が記録から作り直せるか(壊れた記録は赤)。"""
    try:
        J = RM.build_J(R, seal)
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"D"]) != list(SG.PRED_IDS) or list(J[u"K"]) != list(SG.K_IDS):
        out.append(u"判定の行が D-1〜D-10・K-1〜K-5 でない")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R, seal):
    J = RM.build_J(R, seal)
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != RM.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("judge") != RM.render_judge(J, seal).split(u"\n"):
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


# ================================================================ 小さい標本の記録 3 つ(通信しない・cache を読まない)
def prow(b, state, reason=None, ptr=(), o=None):
    return {"b": b, "state": state, "reason": reason, "pointers": list(ptr), "o": o}


ITEMS = [dict(docID="DOC1", form="F1", model="m1", writer="W1", sha256="0" * 64), dict(docID="DOC2", form="F5", model="m2", writer="W2", sha256="1" * 64)]
RND = {"P28E": collections.OrderedDict([(u"決定", "round"), (u"round-only", 8), (u"truncate-only", 0), (u"両方", 7)]),
       "P29E": collections.OrderedDict([(u"決定", "round"), (u"round-only", 29), (u"truncate-only", 0), (u"両方", 43)])}
OKS = dict((p, True) for p in RM.PROFILES)


def n_book_of(name, item, r28, r29):
    u"""N の便の ai200 の本(P29E−O の席に P29E の行を置く = O の欄だけ使わない)。"""
    ok = dict((p, True) for p in NF.NOW_PROFILES)
    same = collections.OrderedDict([(u"行", True), (u"4 state", True), (u"claim の数", True)])
    return norm(NF.assemble_book("aiforms", name, item, same, {"P28E": r28, "P29E": r29, "P29E-O": r29}, ok, RND))


def sample_book(src, name, item, r28, r29, r30, idmap, labels, mixed, same_ok=True, n_book=None):
    n_book = n_book if n_book is not None else n_book_of(name, item, r28, r29)
    rec, diff = RM.analyse_book_rb({"P28E": r28, "P29E": r29, "P30E": r30}, OKS, mixed, idmap, labels, RND, n_book)
    same = collections.OrderedDict([(u"行", True), (u"4 state", same_ok), (u"claim の数", True)])
    return norm(RM.assemble_book_rb(src, name, item, same, rec, diff, True))


def sample_books():
    # 本 1: P28E 3 行(文 2 の (2, 4) は GROUNDED)。P29E は新しい行 (3, 7)・(2, 4) が GROUNDED を失う(同じ文に新しい行が無い = N の便の K-2 の行)。
    #       P30E は (1, 5) VALUE_MISMATCH → GROUNDED(札 真)・(2, 4) VALUE_MISMATCH → GROUNDED(札 偽)・新しい行 (3, 7) POINTER_NOT_FOUND → GROUNDED(札なし)
    r28 = {(0, 5): prow(9, G, None, ["a@当期"]), (1, 5): prow(9, P_, "no_element"), (2, 4): prow(9, G, None, ["b@当期"])}
    r29 = {(0, 5): prow(9, G, None, ["a@当期"]), (1, 5): prow(9, V_), (2, 4): prow(9, V_), (3, 7): prow(20, P_, "no_element")}
    r30 = {(0, 5): prow(9, G, None, ["a@当期"]), (1, 5): prow(9, G, None, ["c@当期"]), (2, 4): prow(9, G, None, ["b@当期"]), (3, 7): prow(20, G, None, ["d@当期"])}
    b1 = sample_book("aiforms", "DOC1_F1_m1", ITEMS[0], r28, r29, r30, {(0, 5): "N001", (1, 5): "N002", (2, 4): "N003"}, {"N001": u"真", "N002": u"真", "N003": u"偽"}, [10000.0])
    # 本 2: 混ざる桁なし。P30E が P29E の GROUNDED の行を 1 つ失う(D-3 の外れの標本)・札なしの既存の行が GROUNDED になる
    q28 = {(0, 3): prow(8, G, None, ["a@当期"]), (4, 1): prow(7, P_, "no_element")}
    q29 = {(0, 3): prow(8, G, None, ["a@当期"]), (4, 1): prow(7, P_, "no_element")}
    q30 = {(0, 3): prow(8, V_), (4, 1): prow(7, G, None, ["e@当期"])}
    b2 = sample_book("f5", "DOC2_F5_m2", ITEMS[1], q28, q29, q30, {(0, 3): "N001"}, {}, [], same_ok=False)
    return [b1, b2]


def sample_header(k, script_rel, step):
    cache = collections.OrderedDict([("edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": "2" * 64})])
    h = collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"step", step), (u"HEAD の commit", "3" * 40), (u"この script の sha256", sha256_rel(script_rel)),
        (FP_KEY[k], dict(engine_fingerprint_at_commit(), adapter_xbrl_py_files=16, core_py_files=4, git_commit="3" * 40)),
        (u"cache の前後", collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)]))])
    if k in ("ai200", "inject"):
        h[u"numfix script の sha256"] = sha256_rel(SG.READ_ONLY_RELS[0])
        h[u"前の便の run script の sha256"] = sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")
        h[u"生成の script の sha256"] = sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")
        h[u"N の便の記録の sha256"] = collections.OrderedDict([("ai200", sha256_rel(RM.N_AI200_REL)), ("regress97", sha256_rel(RM.N_REGRESS97_REL))])
    if k == "regress97":
        h[u"numfix regress97 script の sha256"] = sha256_rel(SG.READ_ONLY_RELS[1])
    return h


def sample_ai200():
    books = sample_books()
    rec = sample_header("ai200", REC_SCRIPT["ai200"], u"標本")
    rec[u"profile"] = list(RM.PROFILES)
    rec[u"本"] = books
    rec[u"集計"] = norm(RM.aggregate(books))
    return norm(rec)


def sample_inject():
    def cell(res, state, reason=None):
        return collections.OrderedDict([(u"対応", True), (u"結果", res), (u"state", state), (u"reason", reason)])
    base = collections.OrderedDict([(u"docID", "DOC1"), (u"form", "F1"), (u"model", "m1"), (u"writer", "W1")])
    rows = []
    rows.append(collections.OrderedDict(list(base.items()) + [("id", "DOC1_F1_m1-T1-01"), (u"型", "T1_VALUE"), (u"基準の claim", "N001"), (RM.LINK_KEY, True),
                                                               ("P29E", cell(TUNE.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH")), ("P30E", cell(TUNE.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH"))]))
    rows.append(collections.OrderedDict(list(base.items()) + [("id", "DOC1_F1_m1-T8-01"), (u"型", "T8_REL"), (u"基準の claim", "N002"), (RM.LINK_KEY, True), ("r", 0.1), (u"r を決めた回", 1),
                                                               ("P29E", cell(TUNE.LABEL_PNF, "POINTER_NOT_FOUND", "no_element")), ("P30E", cell(TUNE.LABEL_PASS, "GROUNDED"))]))
    rows.append(collections.OrderedDict(list(base.items()) + [("id", "DOC1_F1_m1-T8-02"), (u"型", "T8_REL"), (u"基準の claim", "N003"), (RM.LINK_KEY, False), ("r", -0.03), (u"r を決めた回", 2),
                                                               ("P29E", TUNE.classify(None, None)), ("P30E", cell(TUNE.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH"))]))
    with Patch() as pt:
        pt.set(RUN, "PROFILES", RM.INJECT_PROFILES)
        summ, summ_cmp = (norm(x) for x in RM.inject_summaries(rows))
    rec = sample_header("inject", REC_SCRIPT["inject"], u"標本")
    rec[u"profile"] = list(RM.INJECT_PROFILES)
    rec[u"型"] = collections.OrderedDict([(u"土台", BASE_WORD_PIN)])
    rec[u"本ごとの数え"] = collections.OrderedDict([("DOC1_F1_m1", {})])
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"] = summ
    rec[RM.COMPARE_KEY] = summ_cmp
    rec[u"限界"] = [u"他の限界", LIMIT_PIN]
    rec[u"P29E に対応なしの行の数"] = collections.OrderedDict([(u"全体", 1), ("T1_VALUE", 0), ("T8_REL", 1)])
    rec[u"行"] = rows
    return norm(rec)


def sample_regress97():
    st = lambda g, v, u, p: collections.OrderedDict([("GROUNDED", g), ("VALUE_MISMATCH", v), ("UNVERIFIABLE", u), ("POINTER_NOT_FOUND", p)])    # noqa: E731
    docs = []
    for i, (n29, moved, lost, added) in enumerate(((10, 0, 0, 0), (12, 2, 1, 1))):
        d = u"DOC%d" % (i + 1)
        claims = collections.OrderedDict((p, n29 if p != "P30E" else n29 + added) for p in RR.NOW_PROFILES)
        shas = collections.OrderedDict((p, hashlib.sha256((d + p).encode()).hexdigest()) for p in RR.NOW_PROFILES)
        rows_moved = [["num", 0, 3 + j, 0, P_ if j >= lost else G, G if j >= lost else U_, "r", None, True] for j in range(moved)]       # 失う行は GROUNDED → UNVERIFIABLE(VALUE_MISMATCH 以外へも失う)
        mv = collections.OrderedDict([(RR.PAIRS[0][0], collections.OrderedDict([
            (u"動いた既存の行", rows_moved), (u"増えた行", added), (u"増えた行の state", st(added, 0, 0, 0)), (u"消えた行", 0)]))])
        docs.append(collections.OrderedDict([
            (u"docID", d), (u"標本", u"手元の 67"), (u"zip の sha256", "4" * 64), (u"claims", claims),
            (u"4 state", collections.OrderedDict((p, st(claims[p], 0, 0, 0)) for p in RR.NOW_PROFILES)),
            (u"出力の sha256(engine の欄を除く)", shas),
            (u"前の便の記録の sha256", collections.OrderedDict((p, shas[p]) for p in RR.BASE_PROFILES)),
            (u"動いた行と増えた行", mv)]))
    rec = sample_header("regress97", REC_SCRIPT["regress97"], u"標本")
    rec[u"範囲"] = u"標本"
    rec[u"前の便の記録の sha256"] = sha256_rel(RR.PREV_RECORD_REL)
    T = RR.summarize_docs(docs)
    T[u"D-10 engine の留めの連動で直す試験 file"] = collections.OrderedDict([(u"直した file(M)", 55), (u"新しい file(A)", 1), (u"engine の挿入の行数", 27)])
    rec[u"集計"] = T
    rec[u"書類"] = docs
    rec[u"key_leaks"] = []
    return norm(rec)


def sample_records():
    return collections.OrderedDict([("ai200", sample_ai200()), ("inject", sample_inject()), ("regress97", sample_regress97())])


def sample_agg_records(**ov):
    u"""判定の関数の境界の試験用: 集計だけを持つ記録(幅の真ん中の値)。ov = {名前: 値} で 1 つだけ替える。"""
    v = collections.OrderedDict([
        ("d1", 200), ("d1r", 97), ("d2", 120), ("d3", 0), ("tru", 100), ("fal", 5), ("d5g", 7), ("d5n", 7), ("d6", 90), ("mv", 2), ("lost", 0),
        ("t1", 0.5), ("t8", 2.8), ("o", 81.0), ("d10", 60)])
    v.update(ov)
    ai = {u"全体": {u"D-1 旗が偽の byte 一致": {u"一致した本": v["d1"], u"本": 200},
                  u"D-2 GROUNDED の数(数の claim)": {"P29E": 11000, "P30E": 11000 + v["d2"], u"差": v["d2"]},
                  u"D-3 P29E で GROUNDED・P30E で GROUNDED でない行": v["d3"],
                  u"D-4 GROUNDED になった既存の行の札": {u"真": v["tru"], u"偽": v["fal"], u"判定不能": 0, RM.NO_LABEL: 0, u"合計": v["tru"] + v["fal"]},
                  u"D-5 N の便の K-2 の行": {u"行": 8, u"うち N の便で GROUNDED を失った行": v["d5n"], u"うち P30E で GROUNDED": v["d5g"], u"P30E で GROUNDED": 8},
                  u"D-6 混ざる桁がある本": {u"本": v["d6"], u"混ざる桁の延べ数": v["d6"]}}}
    inj = {"T1_VALUE": {"P29E": {u"全体": {u"通した": {u"率": 9.9}}}, "P30E": {u"全体": {u"通した": {u"率": v["t1"]}}}},
           "T8_REL": {"P29E": {u"全体": {u"通した": {u"率": 9.9}, u"名指して原本の値を返した": {u"率": 9.9}}},
                      "P30E": {u"全体": {u"通した": {u"率": v["t8"]}, u"名指して原本の値を返した": {u"率": v["o"]}}}}}
    # inj = 全 site の集計(D-8・D-9 の P30E はこちら。P29E の欄は対応なしが混ざるので比較に使わない 9.9)。inj_cmp = 比較用(P29E にも対応が付く site だけ)
    inj_cmp = {"T1_VALUE": {"P29E": {u"全体": {u"通した": {u"率": 0.4}}}, "P30E": {u"全体": {u"通した": {u"率": 0.4}}}},
               "T8_REL": {"P29E": {u"全体": {u"通した": {u"率": 0.8}, u"名指して原本の値を返した": {u"率": 82.2}}},
                          "P30E": {u"全体": {u"通した": {u"率": 2.7}, u"名指して原本の値を返した": {u"率": 81.1}}}}}
    c1 = collections.OrderedDict((p, {u"byte が同じ書類": v["d1r"], u"書類": 97}) for p in RR.BASE_PROFILES)
    r97 = {u"集計": {u"D-1 旗が偽の profile の byte 一致": c1, u"D-7 P30E 対 P29E": {u"動いた既存の行": v["mv"], u"GROUNDED を失う行": v["lost"]},
                    u"D-10 engine の留めの連動で直す試験 file": {u"直した file(M)": v["d10"], u"新しい file(A)": 1, u"engine の挿入の行数": 27}}}
    return {"ai200": {u"集計": ai}, "inject": {u"集計": inj, RM.COMPARE_KEY: inj_cmp}, "regress97": r97}


def sample_doc(R, seal):
    J = RM.build_J(R, seal)
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", RM.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start judge -->", RM.render_judge(J, seal), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"200 本の標本です。" + NOT_GATED, u""])


# ================================================================ (a) 封の字
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def test_a_2_a_changed_character_in_the_seal_turns_the_pin_red(self):
        rows = RM.seal_pred_rows(self.seal)
        for cid, old, new in (("D-2", "+110〜+135", "+111〜+135"), ("D-2", "+110〜+135", "+110〜+136"), ("D-4", "真 90〜110", "真 90〜111"), ("D-4", "偽 0〜12", "偽 0〜13"),
                              ("D-6", "60〜120", "60〜121"), ("D-7", "0〜5 / 0", "0〜6 / 0"), ("D-8", "T8 2.0〜3.5%", "T8 2.0〜3.6%"), ("D-8", "T1 0.0〜1.0%", "T1 0.0〜1.1%"),
                              ("D-9", "78〜84%", "78〜85%"), ("D-10", "45〜75", "45〜76"), ("D-5", "7 / 7", "7 / 6"), ("D-1", "97 / 97 × 8", "97 / 97 × 7")):
            self.assertIn(old, rows[cid][1], cid)
            mutated = self.seal.replace("| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1]), "| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1].replace(old, new, 1)), 1)
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], bounds_problems(mutated), (cid, new))

    def test_a_3_the_thresholds_of_k2_to_k5_are_read_from_the_seal(self):
        b = RM.seal_bounds(self.seal)
        self.assertEqual((0, {u"偽": 12.0, u"真": 80.0}, {"T1_VALUE": 1.0, "T8_REL": 3.5}, {u"失う行": 0, u"動いた行": 5.0}), (b["K-2"], dict(b["K-3"]), dict(b["K-4"]), dict(b["K-5"])))
        for old, new in (("D-3 = 0", "D-3 = 1"), ("偽 ≤ 12 かつ札 真 ≥ 80", "偽 ≤ 13 かつ札 真 ≥ 80"), ("偽 ≤ 12 かつ札 真 ≥ 80", "偽 ≤ 12 かつ札 真 ≥ 81"),
                         ("T1_VALUE ≤ 1.0%", "T1_VALUE ≤ 1.1%"), ("T8_REL ≤ 3.5%", "T8_REL ≤ 3.6%"), ("失う行 = 0 かつ動いた行 ≤ 5", "失う行 = 0 かつ動いた行 ≤ 6")):
            self.assertIn(old, self.seal, old)
            self.assertNotEqual([], bounds_problems(self.seal.replace(old, new, 1)), new)


# ================================================================ (c) 判定
class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def J(self, **ov):
        return RM.build_J(sample_agg_records(**ov), self.seal)

    def test_c_1_the_middle_of_every_range_is_a_hit_and_adoption_follows(self):
        J = self.J()
        for k, v in J[u"D"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        for k, v in J[u"K"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        self.assertTrue(J[u"採用"])

    def test_c_2_each_prediction_flips_at_the_seal_boundary(self):
        b = BOUNDS_PIN
        cases = [("d1", "D-1", 200, 199), ("d1r", "D-1", 97, 96),
                 ("d2", "D-2", b["D-2"][0], b["D-2"][0] - 1), ("d2", "D-2", b["D-2"][1], b["D-2"][1] + 1),
                 ("d3", "D-3", 0, 1),
                 ("tru", "D-4", b["D-4"][u"真"][0], b["D-4"][u"真"][0] - 1), ("tru", "D-4", b["D-4"][u"真"][1], b["D-4"][u"真"][1] + 1),
                 ("fal", "D-4", b["D-4"][u"偽"][1], b["D-4"][u"偽"][1] + 1),
                 ("d5g", "D-5", 7, 6), ("d5n", "D-5", 7, 8),
                 ("d6", "D-6", b["D-6"][0], b["D-6"][0] - 1), ("d6", "D-6", b["D-6"][1], b["D-6"][1] + 1),
                 ("mv", "D-7", b["D-7"][u"動いた行"][1], b["D-7"][u"動いた行"][1] + 1), ("lost", "D-7", 0, 1),
                 ("t1", "D-8", b["D-8"]["T1_VALUE"][1], b["D-8"]["T1_VALUE"][1] + 0.1), ("t1", "D-8", b["D-8"]["T1_VALUE"][0], b["D-8"]["T1_VALUE"][0] - 0.1),
                 ("t8", "D-8", b["D-8"]["T8_REL"][0], b["D-8"]["T8_REL"][0] - 0.1), ("t8", "D-8", b["D-8"]["T8_REL"][1], b["D-8"]["T8_REL"][1] + 0.1),
                 ("o", "D-9", b["D-9"][0], b["D-9"][0] - 0.1), ("o", "D-9", b["D-9"][1], b["D-9"][1] + 0.1),
                 ("d10", "D-10", b["D-10"][0], b["D-10"][0] - 1), ("d10", "D-10", b["D-10"][1], b["D-10"][1] + 1)]
        for name, cid, inside, outside in cases:
            self.assertEqual(HIT, self.J(**{name: inside})[u"D"][cid][u"判定"], (name, inside))
            self.assertEqual(MISS, self.J(**{name: outside})[u"D"][cid][u"判定"], (name, outside))

    def test_c_2b_d1_needs_every_profile_to_be_byte_identical_on_every_document(self):
        R = sample_agg_records()
        R["regress97"][u"集計"][u"D-1 旗が偽の profile の byte 一致"]["P22"][u"byte が同じ書類"] = 96                      # 1 つの profile だけ 1 書類ずれた
        J = RM.build_J(R, self.seal)
        self.assertEqual(MISS, J[u"D"]["D-1"][u"判定"])
        self.assertEqual(MISS, J[u"K"]["K-1"][u"判定"])
        R2 = sample_agg_records()
        del R2["regress97"][u"集計"][u"D-1 旗が偽の profile の byte 一致"]["P29E"]                                          # profile が 7 つしか無い
        self.assertEqual(MISS, RM.build_J(R2, self.seal)[u"D"]["D-1"][u"判定"])
        R3 = sample_agg_records()
        R3["regress97"][u"集計"][u"D-1 旗が偽の profile の byte 一致"]["P28"][u"書類"] = 96                                 # 書類の数が 97 でない
        self.assertEqual(MISS, RM.build_J(R3, self.seal)[u"D"]["D-1"][u"判定"])

    def test_c_3_the_adoption_follows_k1_to_k5(self):
        self.assertFalse(self.J(d1=199)[u"採用"])                          # K-1
        self.assertFalse(self.J(d1r=96)[u"採用"])                          # K-1
        self.assertEqual(MISS, self.J(d1=199)[u"K"]["K-1"][u"判定"])
        self.assertFalse(self.J(d3=1)[u"採用"])                            # K-2
        self.assertEqual(MISS, self.J(d3=1)[u"K"]["K-2"][u"判定"])
        self.assertFalse(self.J(fal=13)[u"採用"])                          # K-3(偽 ≤ 12)
        self.assertTrue(self.J(fal=12)[u"採用"])
        self.assertFalse(self.J(tru=79)[u"採用"])                          # K-3(真 ≥ 80)
        self.assertTrue(self.J(tru=80)[u"採用"])
        self.assertFalse(self.J(t1=1.1)[u"採用"])                          # K-4
        self.assertFalse(self.J(t8=3.6)[u"採用"])
        self.assertTrue(self.J(t8=3.5)[u"採用"])
        self.assertFalse(self.J(lost=1)[u"採用"])                          # K-5
        self.assertFalse(self.J(mv=6)[u"採用"])
        self.assertTrue(self.J(mv=5)[u"採用"])

    def test_c_4_k3_and_k4_use_the_seal_k_thresholds_not_the_prediction_ranges(self):
        J = self.J(tru=85)                                                        # D-4 の幅(90〜110)の外。K-3 は 80 以上
        self.assertEqual(MISS, J[u"D"]["D-4"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-3"][u"判定"])
        J = self.J(t8=1.0)                                                        # D-8 の幅(2.0〜3.5)の外(下)。K-4 は ≤ 3.5 だけを見る
        self.assertEqual(MISS, J[u"D"]["D-8"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-4"][u"判定"])
        J = self.J(mv=0)
        self.assertEqual(HIT, J[u"D"]["D-7"][u"判定"])

    def test_c_4b_the_p29e_comparison_comes_from_the_linked_sites_summary(self):
        J = self.J()
        self.assertEqual(0.4, J[u"D"]["D-8"][u"値"][u"T1_VALUE 通した率 P29E(比較用)"])
        self.assertEqual(0.8, J[u"D"]["D-8"][u"値"][u"T8_REL 通した率 P29E(比較用)"])
        self.assertEqual(82.2, J[u"D"]["D-9"][u"値"][u"P29E(比較用)"])
        self.assertEqual(2.8, J[u"D"]["D-8"][u"値"][u"T8_REL 通した率 P30E"])               # P30E は全 site の集計(比較用の 2.7 ではない)
        self.assertEqual(81.0, J[u"D"]["D-9"][u"値"][u"T8_REL 名指して原本 P30E"])

    def test_c_5_the_judgment_moves_with_the_records(self):
        R = sample_agg_records()
        base = RM.build_J(R, self.seal)
        R2 = copy.deepcopy(R)
        R2["ai200"][u"集計"][u"全体"][u"D-2 GROUNDED の数(数の claim)"][u"差"] = 200
        self.assertNotEqual(norm(base), norm(RM.build_J(R2, self.seal)))
        mutated_seal = self.seal.replace("+110〜+135", "+110〜+119", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertEqual(MISS, RM.build_J(R, mutated_seal)[u"D"]["D-2"][u"判定"])

    def test_c_6_a_broken_record_is_red_not_an_exception(self):
        R = sample_agg_records()
        del R["ai200"][u"集計"][u"全体"][u"D-2 GROUNDED の数(数の claim)"]
        self.assertNotEqual([], judge_problems(R, self.seal))
        self.assertEqual([], judge_problems(sample_agg_records(), self.seal))


# ================================================================ (g) 小さい標本の記録 3 つと文書の変異
class SampleFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.R = sample_records()

    def test_g_0_the_sample_is_green(self):
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=False))
        doc = sample_doc(self.R, self.seal)
        self.assertEqual([], doc_problems(doc, self.R, self.seal))

    def test_g_1_the_sample_exercises_gained_lost_labelled_and_k2_rows(self):
        b1, b2 = self.R["ai200"][u"本"]
        self.assertEqual({"P29E": 1, "P30E": 4}, dict(b1[u"GROUNDED の数"]))
        self.assertEqual({u"真": 1, u"偽": 1, u"判定不能": 0, RM.NO_LABEL: 0}, dict(b1[u"GROUNDED になった既存の行の札"]))
        self.assertEqual(1, b1[u"GROUNDED になった新しい行"])
        self.assertEqual([10000.0], b1[u"混ざる桁"])
        self.assertEqual(1, b2[u"GROUNDED を失った行"])
        self.assertEqual({u"真": 0, u"偽": 0, u"判定不能": 0, RM.NO_LABEL: 1}, dict(b2[u"GROUNDED になった既存の行の札"]))
        self.assertFalse(b2[u"旗が偽の byte 一致"][u"一致"])

    def _red(self, mutate, **kw):
        R = copy.deepcopy(self.R)
        mutate(R)
        self.assertNotEqual([], record_problems(R, full=False), kw)

    def test_g_2_one_number_in_a_record_turns_it_red(self):
        self._red(lambda R: R["ai200"][u"本"][0][u"GROUNDED の数"].__setitem__("P30E", 99))
        self._red(lambda R: R["ai200"][u"本"][0].__setitem__(u"GROUNDED を失った行", 1))
        self._red(lambda R: R["ai200"][u"本"][0][u"GROUNDED になった既存の行の札"].__setitem__(u"真", 2))
        self._red(lambda R: R["ai200"][u"本"][0].__setitem__(u"GROUNDED になった新しい行", 0))
        self._red(lambda R: R["ai200"][u"集計"][u"全体"][u"D-2 GROUNDED の数(数の claim)"].__setitem__(u"差", 9))
        self._red(lambda R: R["ai200"][u"集計"][u"全体"][u"D-4 GROUNDED になった既存の行の札"].__setitem__(u"偽", 0))
        self._red(lambda R: R["ai200"][u"集計"][u"全体"][u"D-5 N の便の K-2 の行"].__setitem__(u"うち P30E で GROUNDED", 0))
        self._red(lambda R: R["ai200"][u"本"][1][u"旗が偽の byte 一致"].__setitem__(u"一致", True))
        self._red(lambda R: R["ai200"][u"本"][0][u"混ざる桁"].append(1.0))
        self._red(lambda R: R["inject"][u"行"][0]["P30E"].__setitem__(u"結果", TUNE.LABEL_PASS))
        self._red(lambda R: R["inject"][u"集計"]["T1_VALUE"]["P30E"][u"全体"].__setitem__(u"注入の行", 9))
        self._red(lambda R: R["inject"][u"行"][1].__setitem__("r", 0.2))
        self._red(lambda R: R["inject"][u"型"].__setitem__(u"土台", u"無改変の文で P29E が GROUNDED の claim"))
        self._red(lambda R: R["regress97"][u"書類"][1][u"動いた行と増えた行"]["P30E 対 P29E"].__setitem__(u"増えた行", 5))
        self._red(lambda R: R["regress97"][u"集計"][u"D-7 P30E 対 P29E"].__setitem__(u"GROUNDED を失う行", 0))
        self._red(lambda R: R["regress97"][u"書類"][0][u"出力の sha256(engine の欄を除く)"].__setitem__("P28E", "5" * 64))

    def test_g_2b_a_consistently_edited_book_still_breaks_the_invariants(self):
        u"""本を直してから集計も作り直しても(集計との食い違いでは見つからない)、本の中の欄の間の関係で赤になる。"""
        def reagg(R):
            R["ai200"][u"集計"] = norm(RM.aggregate(R["ai200"][u"本"]))
        for mutate in (lambda b: b[u"GROUNDED の数"].__setitem__("P30E", 99), lambda b: b[u"GROUNDED の数"].__setitem__("P29E", 99), lambda b: b[u"GROUNDED の数"].__setitem__("P29E", 2),
                       lambda b: b[u"GROUNDED の数"].__setitem__("P30E", 3), lambda b: b.__setitem__(u"GROUNDED を失った行", 3),
                       lambda b: b.__setitem__(u"GROUNDED になった行", 9), lambda b: b[u"GROUNDED になった既存の行の札"].__setitem__(u"偽", 0),
                       lambda b: b[u"GROUNDED になった既存の行の札"].__setitem__(u"判定不能", 1), lambda b: b.__setitem__(u"GROUNDED になった新しい行", 5),
                       lambda b: b.__setitem__(u"state が変わった行", 9), lambda b: b.__setitem__(u"動いた行", 0), lambda b: b[u"動いた行の向き別"].clear(),
                       lambda b: b[u"state が変わった行の中身"][0].__setitem__(5, u"偽" if b[u"state が変わった行の中身"][0][5] == u"真" else u"真"),
                       lambda b: b[u"state が変わった行の中身"][0].__setitem__(4, b[u"state が変わった行の中身"][0][3]),
                       lambda b: b[u"数の claim の数"].__setitem__("P30E", 99), lambda b: b[u"対応"].__setitem__("P30E", False),
                       lambda b: b.__setitem__(u"混ざる桁", [3.0, 1.0]),
                       lambda b: b[u"旗が偽の byte 一致"].__setitem__(u"一致", not b[u"旗が偽の byte 一致"][u"一致"]),
                       lambda b: b.__setitem__(u"N の便の記録と違った欄", [u"既存の行"]),
                       lambda b: b.__setitem__(u"P27 の鍵が一意", u"はい"),
                       lambda b: b[u"K-2 の行"].append([u"text", 1, 1, "GROUNDED", "GROUNDED", None, None])):
            R = copy.deepcopy(self.R)
            mutate(R["ai200"][u"本"][0])
            try:
                reagg(R)
            except Exception:                                   # noqa: BLE001  集計を作れない形も赤(record_problems が例外を問題に数える)
                pass
            self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        reagg(R)
        self.assertEqual([], record_problems(R, full=False))

    def test_g_2e_inject_base_fields_are_checked(self):
        for mutate in (lambda r: r[u"行"][0].__setitem__(RM.LINK_KEY, False),                                       # 対応ありの行を対応なしに(P29E の欄が対応なしでない)
                       lambda r: r[u"行"][2].__setitem__(RM.LINK_KEY, True) or r.__setitem__(u"注入の行の数", len(r[u"行"])),
                       lambda r: r[u"行"][2].__setitem__(RM.LINK_KEY, u"いいえ"),
                       lambda r: r[RM.COMPARE_KEY]["T8_REL"]["P29E"][u"全体"].__setitem__(u"注入の行", 9),
                       lambda r: r.pop(RM.COMPARE_KEY),
                       lambda r: r[u"行"][2]["P29E"].__setitem__(u"結果", TUNE.LABEL_PASS),
                       lambda r: r[u"P29E に対応なしの行の数"].__setitem__(u"全体", 0),
                       lambda r: r[u"P29E に対応なしの行の数"].__setitem__("T1_VALUE", 1),
                       lambda r: r.pop(u"P29E に対応なしの行の数"),
                       lambda r: r.__setitem__(u"限界", [u"他の限界"]),
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
            pt.set(RUN, "PROFILES", RM.INJECT_PROFILES)
            R["inject"][u"集計"], R["inject"][RM.COMPARE_KEY] = (norm(x) for x in RM.inject_summaries(R["inject"][u"行"]))
        R["inject"][u"P29E に対応なしの行の数"] = collections.OrderedDict([(u"全体", 0), ("T1_VALUE", 0), ("T8_REL", 0)])
        self.assertTrue(any(u"上限" in x for x in inject_problems(R["inject"], full=False)), inject_problems(R["inject"], full=False))

    def test_g_2g_the_full_only_checks_are_exercised_on_the_sample(self):
        u"""full=True だけが見る検査(本番の記録でだけ走る)を、標本の記録で 1 つずつ。他の full の検査(本の並び・97 書類)は標本では赤のままなので、その検査の問題の字だけを見る。"""
        R = copy.deepcopy(self.R)
        link = norm(link_at_history())
        R["regress97"][u"集計"][u"D-10 engine の留めの連動で直す試験 file"] = link
        self.assertFalse(any(u"D-10" in x for x in regress97_problems(R["regress97"], full=True)))
        R["regress97"][u"集計"][u"D-10 engine の留めの連動で直す試験 file"][u"直した file(M)"] += 1
        self.assertTrue(any(u"D-10" in x for x in regress97_problems(R["regress97"], full=True)))
        R["regress97"][u"前の便の記録の sha256"] = sha256_rel(RR.PREV_RECORD_REL)
        self.assertFalse(any(u"前の便の記録の sha256 が現物と違う" in x for x in regress97_problems(R["regress97"], full=True)))
        R["regress97"][u"前の便の記録の sha256"] = "0" * 64
        self.assertTrue(any(u"前の便の記録の sha256 が現物と違う" in x for x in regress97_problems(R["regress97"], full=True)))
        want = norm(collections.OrderedDict(
            [(u"%s_%s" % (src, k), sha256_rel(p[k])) for src, p in RM.SOURCES.items() for k in ("gen", "claims")] + [(u"%s_labels" % src, sha256_rel(rel)) for src, rel in RM.LABELS_REL.items()]))
        a = copy.deepcopy(self.R["ai200"])
        a[u"入力の記録の sha256"] = want
        self.assertFalse(any(u"入力の記録の sha256" in x for x in ai200_problems(a, full=True)))
        a[u"入力の記録の sha256"] = dict(want, aiforms_labels="0" * 64)
        self.assertTrue(any(u"入力の記録の sha256" in x for x in ai200_problems(a, full=True)))
        self.assertTrue(any(u"本が 200 本でない" in x for x in ai200_problems(a, full=True)))                 # 標本は 200 本でない
        self.assertTrue(any(u"本の並び" in x for x in ai200_problems(a, full=True)))

    def test_g_2h_the_k2_rows_are_compared_with_the_previous_record_on_the_full_path(self):
        a = copy.deepcopy(self.R["ai200"])
        b1 = a[u"本"][0]
        n_rec = {u"本": [{u"name": b[u"name"], u"同じ文に新しい行が無いのに変わった既存の行": [x[:5] + [None, None] for x in b[u"K-2 の行"]]} for b in a[u"本"]]}
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            path = os.path.join(d, "n_ai200.json")
            with io.open(path, "w", encoding="utf-8") as fh:
                json.dump(n_rec, fh, ensure_ascii=False)
            pt.set(RM, "N_AI200_REL", path)                                                                   # 絶対 path は ROOT に連ねても絶対 path のまま
            self.assertFalse(any(u"K-2 の行が N の便の記録と違う" in x for x in ai200_problems(a, full=True)))
            b1[u"K-2 の行"][0][3] = "UNVERIFIABLE"
            self.assertTrue(any(u"K-2 の行が N の便の記録と違う" in x for x in ai200_problems(a, full=True)))

    def test_g_3_a_forbidden_key_or_a_key_or_a_company_name_turns_it_red(self):
        for key in (u"span", u"value", u"recomputed", u"文", u"sentence", u"数", u"理由"):
            self._red(lambda R, key=key: R["ai200"][u"本"][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["inject"][u"行"][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["regress97"][u"書類"][0].__setitem__(key, 1))
        self._red(lambda R: R["regress97"].__setitem__(u"メモ", u"株式会社テスト"))
        self._red(lambda R: R["ai200"].__setitem__(u"メモ", u"sk-" + u"a" * 20))
        self._red(lambda R: R["regress97"].__setitem__(u"key_leaks", [u"鍵の形"]))

    def test_g_4_one_character_of_the_fingerprint_or_the_script_sha_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][FP_KEY[k]].__setitem__("adapter_xbrl_py_sha256", R[k][FP_KEY[k]]["adapter_xbrl_py_sha256"][:-1] + ("0" if R[k][FP_KEY[k]]["adapter_xbrl_py_sha256"][-1] != "0" else "1")))
            self._red(lambda R, k=k: R[k][FP_KEY[k]].__setitem__("core_py_sha256", "f" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"この script の sha256", "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"封の commit", u"0000000"))
        self._red(lambda R: R["ai200"].__setitem__(u"numfix script の sha256", "e" * 64))
        self._red(lambda R: R["inject"][u"N の便の記録の sha256"].__setitem__("ai200", "e" * 64))
        self._red(lambda R: R["regress97"].__setitem__(u"numfix regress97 script の sha256", "e" * 64))

    def test_g_5_a_changed_cache_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][u"cache の前後"].__setitem__(u"変化なし", False))
            self._red(lambda R, k=k: R[k][u"cache の前後"][u"後"]["edinet"].__setitem__(u"件数", 4))

    def test_g_6_the_document_follows_the_records_and_the_seal(self):
        doc = sample_doc(self.R, self.seal)
        lines = doc.split(u"\n")
        i = lines.index(u"<!-- 門:start pred -->") + 3                  # 表の 1 行目(D-1)
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
        R2["regress97"][u"集計"][u"D-7 P30E 対 P29E"][u"動いた既存の行"] = 9
        R2["ai200"][u"集計"][u"全体"][u"D-2 GROUNDED の数(数の claim)"][u"差"] += 1
        self.assertNotEqual([], doc_problems(doc, R2, self.seal))
        mutated_seal = self.seal.replace("+110〜+135", "+110〜+136", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertNotEqual([], doc_problems(doc, self.R, mutated_seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"門:start judge", u"門:start other"), self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc.replace(u"<!-- 門:start judge -->", u"<!-- 門:start judge2 -->", 1), self.R, self.seal))

    def test_g_7_forbidden_words_docids_and_ungated_numbers_turn_the_document_red(self):
        doc = sample_doc(self.R, self.seal)
        for w in FOR_RESULT_WORDS:
            self.assertNotEqual([], doc_problems(doc + u"\n" + w + u"。\n", self.R, self.seal), w)
        self.assertNotEqual([], doc_problems(doc + u"\nS100" + u"ABCD の文。\n", self.R, self.seal))
        self.assertNotEqual([], doc_problems(doc + u"\n新しい行は 1234 行でした。\n", self.R, self.seal))
        self.assertEqual([], doc_problems(doc + u"\n新しい行は 1234 行でした。" + NOT_GATED + u"\n", self.R, self.seal))

    def test_g_8_the_aggregation_functions_give_known_answers(self):
        A = RM.aggregate(self.R["ai200"][u"本"])[u"全体"]
        self.assertEqual({"P29E": 2, "P30E": 5, u"差": 3}, dict(A[u"D-2 GROUNDED の数(数の claim)"]))
        self.assertEqual(1, A[u"D-3 P29E で GROUNDED・P30E で GROUNDED でない行"])
        self.assertEqual({u"真": 1, u"偽": 1, u"判定不能": 0, RM.NO_LABEL: 1, u"合計": 3}, dict(A[u"D-4 GROUNDED になった既存の行の札"]))
        self.assertEqual(1, A[u"GROUNDED になった新しい行"])
        self.assertEqual({u"行": 2, u"うち N の便で GROUNDED を失った行": 1, u"うち P30E で GROUNDED": 1, u"P30E で GROUNDED": 2}, dict(A[u"D-5 N の便の K-2 の行"]))
        self.assertEqual({u"本": 1, u"混ざる桁の延べ数": 1}, dict(A[u"D-6 混ざる桁がある本"]))
        self.assertEqual({u"一致した本": 1, u"本": 2}, dict(A[u"D-1 旗が偽の byte 一致"]))
        self.assertEqual({u"動いた行": 5, u"state が変わった行": 5, u"向き別": {u"GROUNDED → VALUE_MISMATCH": 1, u"POINTER_NOT_FOUND → GROUNDED": 2, u"VALUE_MISMATCH → GROUNDED": 2}}, norm(A[u"動いた行"]))
        T = RR.summarize_docs(self.R["regress97"][u"書類"])
        self.assertEqual({u"動いた既存の行": 2, u"GROUNDED を失う行": 1, u"GROUNDED になった行": 1, u"state が変わった行": 2, u"向き別": {u"GROUNDED → UNVERIFIABLE": 1, u"POINTER_NOT_FOUND → GROUNDED": 1},
                          u"増えた行": 1, u"消えた行": 0, u"動いた行のある書類": 1, u"claim の数が違う書類": 1}, norm(T[u"D-7 P30E 対 P29E"]))
        self.assertEqual({p: 2 for p in RR.BASE_PROFILES}, dict((p, v[u"byte が同じ書類"]) for p, v in T[u"D-1 旗が偽の profile の byte 一致"].items()))


# ================================================================ 既知の答えのある小さい入力(札・K-2・動いた行)
class KnownAnswerTest(unittest.TestCase):
    def analyse(self, r28, r29, r30, idmap=None, labels=None, mixed=None):
        n_book = n_book_of("DOC1_F1_m1", ITEMS[0], r28, r29)
        return RM.analyse_book_rb({"P28E": r28, "P29E": r29, "P30E": r30}, OKS, mixed, idmap or {}, labels or {}, RND, n_book)

    def test_k_1_the_label_is_taken_only_for_rows_that_exist_in_p28e_and_by_the_p27_id(self):
        r28 = {(0, 5): prow(9, P_), (1, 5): prow(9, P_)}
        r29 = {(0, 5): prow(9, V_), (1, 5): prow(9, V_), (2, 5): prow(9, P_)}
        r30 = {(0, 5): prow(9, G), (1, 5): prow(9, G), (2, 5): prow(9, G)}
        rec, diff = self.analyse(r28, r29, r30, {(0, 5): "N001", (1, 5): "N002", (2, 5): "N003"}, {"N001": u"偽", "N002": u"判定不能", "N003": u"真"})
        self.assertEqual([], diff)
        self.assertEqual([[u"num", 0, 5, V_, G, u"偽", u"既存"], [u"num", 1, 5, V_, G, u"判定不能", u"既存"], [u"num", 2, 5, P_, G, None, u"新"]], rec[u"state が変わった行の中身"])   # 新しい行の札は引かない
        self.assertEqual({u"真": 0, u"偽": 1, u"判定不能": 1, RM.NO_LABEL: 0}, dict(rec[u"GROUNDED になった既存の行の札"]))
        self.assertEqual(1, rec[u"GROUNDED になった新しい行"])
        rec2, _d = self.analyse(r28, r29, r30, {(0, 5): "N001"}, {"N001": u"真"})                       # id が無い・札が無い既存の行は 札なし
        self.assertEqual({u"真": 1, u"偽": 0, u"判定不能": 0, RM.NO_LABEL: 1}, dict(rec2[u"GROUNDED になった既存の行の札"]))

    def test_k_2_lost_rows_and_the_k2_rows_of_the_previous_record(self):
        r28 = {(0, 5): prow(9, G), (1, 5): prow(9, G), (3, 5): prow(9, G)}
        r29 = {(0, 5): prow(9, V_), (1, 5): prow(9, G), (2, 5): prow(9, G), (3, 5): prow(9, G)}          # (0, 5) は N の便で GROUNDED を失った(同じ文に新しい行が無い)
        r30 = {(0, 5): prow(9, G), (1, 5): prow(9, V_), (2, 5): prow(9, G), (3, 5): prow(9, P_)}          # P30E: (0, 5) は戻り、(1, 5) と (3, 5) が GROUNDED を失う(VALUE_MISMATCH へも POINTER_NOT_FOUND へも)
        rec, diff = self.analyse(r28, r29, r30)
        self.assertEqual([], diff)
        self.assertEqual([[u"num", 0, 5, G, V_, V_, G]], rec[u"K-2 の行"])
        self.assertEqual((2, 1, 3), (rec[u"GROUNDED を失った行"], rec[u"GROUNDED になった行"], rec[u"state が変わった行"]))
        self.assertEqual({u"GROUNDED → POINTER_NOT_FOUND": 1, u"GROUNDED → VALUE_MISMATCH": 1, u"VALUE_MISMATCH → GROUNDED": 1}, dict(rec[u"動いた行の向き別"]))
        self.assertEqual({"P29E": 3, "P30E": 2}, dict(rec[u"GROUNDED の数"]))

    def test_k_3_a_row_that_changes_only_in_reason_or_pointers_counts_as_moved_not_as_state_changed(self):
        r28 = {(0, 5): prow(9, P_, "no_element")}
        r29 = {(0, 5): prow(9, P_, "no_element", ["a@当期"]), (0, 40): prow(50, G, None, ["x@当期"])}
        r30 = {(0, 5): prow(9, P_, "no_same_value", ["a@当期"]), (0, 40): prow(50, G, None, ["y@当期"])}
        rec, _d = self.analyse(r28, r29, r30)
        self.assertEqual((2, 0, 0, 0), (rec[u"動いた行"], rec[u"state が変わった行"], rec[u"GROUNDED を失った行"], rec[u"GROUNDED になった行"]))

    def test_k_4_keys_that_differ_between_p29e_and_p30e_are_reported(self):
        r28 = {(0, 5): prow(9, G)}
        rec, _d = self.analyse(r28, {(0, 5): prow(9, G)}, {(0, 5): prow(9, G), (0, 20): prow(30, G)})
        self.assertFalse(rec[u"P29E と P30E で数の claim の鍵が同じ"])
        self.assertEqual(0, rec[u"GROUNDED になった行"])                                                      # 共通の鍵だけを見る
        rec2, _d = self.analyse(r28, {(0, 5): prow(9, G)}, {(0, 5): prow(9, G)})
        self.assertTrue(rec2[u"P29E と P30E で数の claim の鍵が同じ"])

    def test_k_5_a_disagreement_with_the_previous_record_is_reported(self):
        r28 = {(0, 5): prow(9, G)}
        r29 = {(0, 5): prow(9, V_)}
        n_book = n_book_of("DOC1_F1_m1", ITEMS[0], r28, r29)
        n_book[u"新しい行の数"] += 1
        n_book[u"数の claim の数"]["P29E"] += 1
        rec, diff = RM.analyse_book_rb({"P28E": r28, "P29E": r29, "P30E": r29}, OKS, [], {}, {}, RND, n_book)
        self.assertEqual({u"新しい行の数", u"数の claim の数"}, set(diff))
        head = RM.assemble_book_rb("aiforms", "DOC1_F1_m1", ITEMS[0], {u"行": True, u"4 state": True, u"claim の数": True}, rec, diff, True)
        self.assertFalse(head[u"旗が偽の byte 一致"][u"P29E が N の便の記録と一致"])
        self.assertFalse(head[u"旗が偽の byte 一致"][u"一致"])
        self.assertEqual([], book_problems(norm(head)))

    def test_k_6_the_script_and_the_history_agree_on_the_engine_link(self):
        link = norm(RR.XR.engine_link())
        self.assertEqual(norm(link_at_history()), link)
        self.assertEqual(["adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py"], link[u"engine の変更 file"])
        self.assertEqual(0, link[u"engine の削除の行数"])

    def test_k_7_engine_link_counts_modified_files_apart_from_added_ones(self):
        P = PREFIX
        num = ["18\t0\t%sadapters/xbrl/recipes.py" % P, "2\t0\t%sadapters/xbrl/comparators.py" % P]
        tests = ["M\t%stests/a.py" % P, "M\t%stests/b.py" % P, "A\t%stests/c.py" % P, "D\t%stests/d.py" % P]
        with Patch() as pt:
            pt.set(RR.XR, "engine_commits", lambda: ("s" * 40, "e" * 40, num, tests))
            link = RR.XR.engine_link()
        self.assertEqual((2, 1, 1, 4), (link[u"直した file(M)"], link[u"新しい file(A)"], link[u"消した file(D)"], link[u"tests の変更 file"]))
        self.assertEqual((20, 0), (link[u"engine の挿入の行数"], link[u"engine の削除の行数"]))

    def test_k_8_the_prediction_table_rows_have_a_fixed_shape(self):
        seal = read(SEAL_REL)
        P = RM.seal_pred_rows(seal)
        J = RM.build_J(sample_agg_records(), seal)
        lines = RM.render_pred(J, seal).split(u"\n")
        self.assertEqual(u"| # | 欄 | 予測 | 測った値 | 判定 |", lines[0])
        by = dict((ln.split(u" | ")[0][2:], ln) for ln in lines[2:])
        self.assertEqual(u"| D-2 | " + P["D-2"][0] + u" | +110〜+135 | P29E 11,000・P30E 11,120・差 120 | **当たり** |", by["D-2"])
        self.assertEqual(u"| D-3 | " + P["D-3"][0] + u" | 0 | 0 | **当たり** |", by["D-3"])
        for ln in lines[2:]:
            self.assertEqual(5, len(ln.strip(u"|").split(u" | ")), ln)
            self.assertNotIn(u"(", ln.split(u" | ")[2])                             # 予測の欄は封の字の括弧の前まで
        j = RM.render_judge(J, seal).split(u"\n")
        self.assertEqual(u"| # | 基準 | 測った値 | 判定 |", j[0])
        self.assertEqual(9, len(j))                                                    # 見出し 2 + K 5 + 空行 + 採用の一文
        self.assertIn(u"採用の判定(K-1〜K-5 を全部満たす): **採用**", j[-1])

    def test_k_9_id_map_and_label_of(self):
        from adapters.xbrl import recipes as R
        from adapters.xbrl import vocabulary as V
        nums = [{"sentence": 0, "pos": 4}, {"sentence": 1, "pos": 2}]
        with Patch() as pt:
            pt.set(R, "build_raw_claims", lambda zm, prof, info=None: (nums, [{"sentence": 0, "pos": 99}]))
            m, ok = RM.id_map(b"zm", {u"対応": True, u"行": [["N001", "num"], ["N002", "num"], ["T001", "text"]]})
            self.assertEqual(({(0, 4): "N001", (1, 2): "N002"}, True), (m, ok))
            self.assertFalse(RM.id_map(b"zm", {u"対応": False, u"行": [["N001"], ["N002"], ["T001"]]})[1])                  # 並びが対応しない
            self.assertFalse(RM.id_map(b"zm", {u"対応": True, u"行": [["N001"], ["N002"]]})[1])                              # 行の数が合わない
            nums.append({"sentence": 0, "pos": 4})                                                                          # 同じ鍵が 2 つ
            self.assertFalse(RM.id_map(b"zm", {u"対応": True, u"行": [["N001"], ["N002"], ["N003"], ["T001"]]})[1])
        self.assertEqual(u"真", RM.label_of((0, 4), {(0, 4): "N001"}, {"N001": u"真"}, True))
        self.assertIsNone(RM.label_of((0, 4), {(0, 4): "N001"}, {"N001": u"真"}, False))                                    # 新しい行は引かない
        self.assertIsNone(RM.label_of((0, 4), {}, {"N001": u"真"}, True))
        self.assertIsNone(RM.label_of((0, 4), {(0, 4): "N001"}, {}, True))
        self.assertIn("P27", V.PROFILES)


# ================================================================ judge_book を小さい合成の入力で通す(engine・zip・文は偽。通信なし)
class JudgeBookFlowTest(unittest.TestCase):
    u"""``verify_document``・``build_raw_claims``・``_numbers_of``・``sentence_list`` と zip / 文の読み込みを偽に替え、profile_view_rb と judge_book_rb の本体を 1 回通す。
    合成の入力(P28E は数の claim 2・P29E は 3 = 新しい行 1、P30E は N002・N003 が GROUNDED)で、記録の欄が既知の答えになる。"""
    PTR = "xbrl:jppfs_cor:Sales@CurrentYearDuration"
    # profile ごとの数の claim: (id, 文の番号, 位置, state, reason)
    CLAIMS = {
        "P27": [("N001", 0, 4, G, None), ("N002", 0, 20, P_, "no_same_value")],
        "P28E": [("N001", 0, 4, G, None), ("N002", 0, 20, P_, "no_same_value")],
        "P29E": [("N001", 0, 4, G, None), ("N002", 0, 20, V_, None), ("N003", 0, 40, V_, None)],
        "P30E": [("N001", 0, 4, G, None), ("N002", 0, 20, G, None), ("N003", 0, 40, G, None)]}
    EVIDENCE = {"P28E": [(-1.0, 10)], "P29E": [(9.0, 10), (8.0, 10)], "P30E": [(9.0, 10), (-1.0, 10)]}

    def fakes(self, pt):
        from adapters.xbrl import vocabulary as V
        claims = self.CLAIMS

        def verify(zb, pname, text):
            cl = [{"id": i, "kind": "num", "state": st, "reason": rs, "pointers": [self.PTR] if st == G else []} for (i, _s, _p, st, rs) in claims[pname]]
            return {"claims": cl, "document": {"states": dict((k, sum(1 for c in cl if c["state"] == k)) for k in NF.STATES)}}

        def raw(zm, prof, info=None):
            V.decide_rounding(self.EVIDENCE.get(prof.name, [(0.0, 10)]))                  # engine と同じ呼び方(包みが写す)
            if info is not None and prof.name == "P30E":
                info["rounding_mixed_scales_2026_11_04"] = [10000.0]
            return ([{"id": i, "sentence": si, "pos": pos, "other_subject_2026_11_02": None} for (i, si, pos, _st, _rs) in claims[prof.name]], [])

        def numbers_of(prof, sentence):
            return [(pos, pos + 6, 1.0, u"円", 1.0) for (_i, _si, pos, _st, _rs) in claims[prof.name]]
        pt.set(RM.VD, "verify_document", verify)
        pt.set(RM.R, "build_raw_claims", raw)
        pt.set(RM.R, "_numbers_of", numbers_of)
        pt.set(RUN, "sentence_list", lambda zm, prof: [u"x" * 60])
        pt.set(GEN, "read_zip", lambda row, caches=None: b"zip")
        pt.set(RUN, "read_text", lambda name, item, d: u"text")
        pt.set(RM.PR, "build_modified_zip", lambda zb, text: (b"zm", None, None))
        old = {u"対応": True, u"行": [["N001", "num"], ["N002", "num"]], u"4 state": {"P27": {}}, u"claim の数": 2}
        pt.set(RUN, "judge_text", lambda zb, text: (copy.deepcopy(old), []))
        return old

    def n_book(self, pt):
        rows = {}
        for p in ("P28E", "P29E"):
            rows[p] = RM.profile_view_rb(b"zip", u"text", b"zm", p)
        with NF.capture_rounding() as cap:
            RM.profile_view_rb(b"zip", u"text", b"zm", "P28E")
        return rows

    def job(self, prior, labels, n_book):
        return ("aiforms", "DOC1_F1_m1", ITEMS[0], {}, "d", {}, prior, labels, n_book)

    def make_n_book(self):
        rounding = {}
        rows = {}
        for p in ("P28E", "P29E"):
            with NF.capture_rounding() as cap:
                rows[p], _ok, _st, _m = RM.profile_view_rb(b"zip", u"text", b"zm", p)
            rounding[p] = cap.result()
        ok = dict((p, True) for p in NF.NOW_PROFILES)
        same = collections.OrderedDict([(u"行", True), (u"4 state", True), (u"claim の数", True)])
        return norm(NF.assemble_book("aiforms", "DOC1_F1_m1", ITEMS[0], same, {"P28E": rows["P28E"], "P29E": rows["P29E"], "P29E-O": rows["P29E"]}, ok, rounding))

    def test_j_1_profile_view_rb_keys_rows_by_position_and_returns_the_mixed_scales(self):
        with Patch() as pt:
            self.fakes(pt)
            rows, ok, states, mixed = RM.profile_view_rb(b"zip", u"text", b"zm", "P30E")
            rows28, _ok, _st, mixed28 = RM.profile_view_rb(b"zip", u"text", b"zm", "P28E")
        self.assertTrue(ok)
        self.assertEqual([(0, 4), (0, 20), (0, 40)], list(rows))
        self.assertEqual({"b": 10, "state": G, "reason": None, "pointers": ["jppfs_cor:Sales@当期"], "o": None}, rows[(0, 4)])
        self.assertEqual([10000.0], mixed)
        self.assertIsNone(mixed28)                                                                 # RB の旗が無い profile は info に混ざる桁を書かない
        self.assertEqual({"GROUNDED": 3, "VALUE_MISMATCH": 0, "UNVERIFIABLE": 0, "POINTER_NOT_FOUND": 0}, states)

    def test_j_2_judge_book_rb_assembles_the_book_record_from_the_three_profiles(self):
        with Patch() as pt:
            old = self.fakes(pt)
            nb = self.make_n_book()
            prior = copy.deepcopy(old)
            rec = RM.judge_book_rb(self.job(prior, {"N002": u"真"}, nb))
        self.assertEqual({"P28E": 2, "P29E": 3, "P30E": 3}, dict(rec[u"数の claim の数"]))
        self.assertEqual({"P29E": 1, "P30E": 3}, dict(rec[u"GROUNDED の数"]))
        self.assertEqual([[u"num", 0, 20, V_, G, u"真", u"既存"], [u"num", 0, 40, V_, G, None, u"新"]], rec[u"state が変わった行の中身"])
        self.assertEqual({u"真": 1, u"偽": 0, u"判定不能": 0, RM.NO_LABEL: 0}, dict(rec[u"GROUNDED になった既存の行の札"]))
        self.assertEqual(1, rec[u"GROUNDED になった新しい行"])
        self.assertEqual([10000.0], rec[u"混ざる桁"])
        self.assertEqual({u"行": True, u"4 state": True, u"claim の数": True, u"P29E が N の便の記録と一致": True, u"一致": True}, dict(rec[u"旗が偽の byte 一致"]))
        self.assertEqual([], rec[u"N の便の記録と違った欄"])
        self.assertTrue(rec[u"P27 の鍵が一意"])
        self.assertEqual([], book_problems(norm(rec)))

    def test_j_3_the_flag_off_byte_match_and_the_previous_record_are_compared_field_by_field(self):
        for field, alter in ((u"行", lambda d: d.__setitem__(u"行", [["N999", "num"]])), (u"4 state", lambda d: d.__setitem__(u"4 state", {"P27": {"x": 1}})),
                             (u"claim の数", lambda d: d.__setitem__(u"claim の数", 4))):
            with Patch() as pt:
                old = self.fakes(pt)
                nb = self.make_n_book()
                prior = copy.deepcopy(old)
                alter(prior)
                rec = RM.judge_book_rb(self.job(prior, {}, nb))
            same = rec[u"旗が偽の byte 一致"]
            self.assertFalse(same[field], field)
            self.assertFalse(same[u"一致"], field)
            self.assertEqual(3, sum(1 for k in (u"行", u"4 state", u"claim の数", u"P29E が N の便の記録と一致") if same[k]), field)
        with Patch() as pt:                                                                     # N の便の記録の P29E の欄が違えば P29E の一致が偽
            old = self.fakes(pt)
            nb = self.make_n_book()
            nb[u"新しい行の state"]["GROUNDED"] += 1
            rec = RM.judge_book_rb(self.job(copy.deepcopy(old), {}, nb))
        self.assertFalse(rec[u"旗が偽の byte 一致"][u"P29E が N の便の記録と一致"])
        self.assertEqual([u"新しい行の state"], rec[u"N の便の記録と違った欄"])

    def test_j_5_run_judge_refuses_a_changed_runner_profile_list_and_writes_the_record(self):
        books = sample_books()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            def reached(root=ROOT, only=None):
                raise AssertionError(u"守りを越えて材料を読みに行った")
            pt.set(RM, "load_jobs", reached)
            pt.set(RUN, "PROFILES", ("P27",))
            with self.assertRaises(GEN.Stop):
                RM.run_judge(root=ROOT, out=os.path.join(d, "x.json"), say=lambda *a: None)
            pt.undo()
            pt.set(RM, "load_jobs", lambda root=ROOT, only=None: [])
            pt.set(NF, "map_pool", lambda fn, jobs_, procs: [copy.deepcopy(b) for b in books])
            pt.set(RM, "caches_all", lambda: collections.OrderedDict())
            pt.set(GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
            out = os.path.join(d, "ai200.json")
            rec = RM.run_judge(root=ROOT, out=out, say=lambda *a: None)
            with open(out, encoding="utf-8") as fh:
                disk = json.load(fh)
            pt.set(NF, "map_pool", lambda fn, jobs_, procs: (_ for _ in ()).throw(AssertionError(u"出力が既に在るのに測りに行った")))
            with self.assertRaises(GEN.Stop):                                                                  # 出力が既に在れば測りに行く前に止める
                RM.run_judge(root=ROOT, out=out, say=lambda *a: None)
            pt.undo()
            pt.set(RM, "load_jobs", lambda root=ROOT, only=None: [])
            pt.set(NF, "map_pool", lambda fn, jobs_, procs: [])
            pt.set(RM, "caches_all", lambda: collections.OrderedDict([("c", "x")]))
            snaps = iter([{"n": 1}, {"n": 2}])
            pt.set(GEN, "caches_snapshot", lambda caches: next(snaps))                                       # cache が前後で変わった
            pt.set(GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
            with self.assertRaises(GEN.Stop):
                RM.run_judge(root=ROOT, out=os.path.join(d, "ai200_changed.json"), say=lambda *a: None)
            self.assertFalse(os.path.exists(os.path.join(d, "ai200_changed.json")))
        self.assertEqual(norm(rec), disk)
        self.assertEqual(books, disk[u"本"])
        self.assertEqual(norm(RM.aggregate(books)), disk[u"集計"])
        self.assertEqual([u"P28E", u"P29E", u"P30E"], disk[u"profile"])
        self.assertEqual([u"aiforms_gen", u"aiforms_claims", u"f5_gen", u"f5_claims", u"aiforms_labels", u"f5_labels"], list(disk[u"入力の記録の sha256"]))
        self.assertEqual(sha256_rel(REC_SCRIPT["ai200"]), disk[u"この script の sha256"])
        self.assertEqual([], [x for x in ai200_problems(disk, False)])

    def test_j_4_a_claim_order_mismatch_is_reported_as_an_unpaired_book(self):
        with Patch() as pt:
            old = self.fakes(pt)
            nb = self.make_n_book()
            old2 = dict(old, **{u"対応": False})
            pt.set(RUN, "judge_text", lambda zb, text: (copy.deepcopy(old2), []))
            rec = RM.judge_book_rb(self.job(copy.deepcopy(old), {"N002": u"真"}, nb))
        self.assertFalse(rec[u"P27 の鍵が一意"])


# ================================================================ 差し替えが使う側に届くこと・注入の土台の結び方
def fake_claim(cid, state="GROUNDED", value=100.0, span=u"売上高は100億円でした", pointers=("xbrl:a:b",), recomputed=1.0e10):
    return {"id": cid, "value": value, "unit": u"億円", "span": span, "state": state, "pointers": list(pointers), "reason": None, "recomputed": recomputed}


class WiringAndInjectTest(unittest.TestCase):
    text = u"売上高は100億円でした。\n"

    def tok(self):
        return RUN.N.scan(self.text)[0]

    def test_w_1_the_nf_swap_reaches_the_users(self):
        self.assertEqual([], RM.wiring_problems())
        with Patch() as pt:
            for name, bad in (("SEAL_REL", "docs/x.md"), ("SEAL_COMMIT", "0000000"), ("REC_DIR_REL", "fixtures/x"), ("AI200_REL", "x.json"), ("INJECT_REL", "x.json"),
                              ("INJECT_PROFILES", ("P28E", "P29E")), ("BASE_WORD", "x"), ("COMPARE_KEY", "x"), ("header", RM.ORIG["header"]), ("DOC_REL", "docs/x.md")):
                pt.set(NF, name, bad)
                self.assertNotEqual([], RM.wiring_problems(), name)
                pt.undo()
        self.assertEqual([], RM.wiring_problems())
        self.assertIs(GEN.key_leaks, NF.key_leaks_n)

    def test_w_2_the_swap_makes_the_inherited_header_carry_this_seal_and_script(self):
        with Patch() as pt:
            pt.set(RM.GEN, "git_head", lambda *a, **k: "3" * 40)
            h = NF.header(ROOT, u"標本", {u"種": 1}, {}, {}, RM.PROFILES)
        self.assertEqual((SEAL_REL, SEAL_COMMIT_SHORT), (h[u"seal"], h[u"封の commit"]))
        self.assertEqual(sha256_rel(REC_SCRIPT["ai200"]), h[u"この script の sha256"])                 # N の便の script の sha256 でない
        self.assertEqual(sha256_rel(SG.READ_ONLY_RELS[0]), h[u"numfix script の sha256"])
        self.assertEqual(list(RM.PROFILES), h[u"profile"])

    def test_w_3_the_regress97_swap_reaches_the_users(self):
        self.assertEqual([], RR.wiring_problems())
        with Patch() as pt:
            for name, bad in (("NOW_PROFILES", RR.XR.NOW_PROFILES[:-1]), ("PAIRS", (("x", "P28E", "P29E"),)), ("KEYED", ("P28E",)), ("SEAL_COMMIT", "0000000"),
                              ("ENGINE_FILES", ("adapters/xbrl/extract.py",)), ("PREV_RECORD_REL", "x.json"), ("BASE_PROFILES", ("P22",))):
                pt.set(RR.XR, name, bad)
                self.assertNotEqual([], RR.wiring_problems(), name)
                pt.undo()
        self.assertEqual([], RR.wiring_problems())
        self.assertEqual(("P22", "P26", "P27", "P27E", "P28", "P28E", "P29", "P29E", "P30E"), RR.XR.NOW_PROFILES)
        self.assertEqual(9, len(RR.NOW_PROFILES))

    def test_i_1_the_base_is_the_p30e_grounded_claim_and_p29e_is_paired_by_value_span_unit(self):
        base = {"P29E": [fake_claim("N001")], "P30E": [fake_claim("N005")]}
        st, bc = RM.base_status_rb(base, {}, self.tok(), self.text)
        self.assertEqual(RM.LINKED, st)
        self.assertEqual({"P29E": "N001", "P30E": "N005"}, bc["ids"])
        self.assertEqual("N005", bc["id"])                                         # 土台は P30E の claim
        st2, bc2 = RM.base_status_rb({"P29E": [fake_claim("N001", "VALUE_MISMATCH")], "P30E": [fake_claim("N005")]}, {}, self.tok(), self.text)   # P29E の claim が GROUNDED でなくても結ぶ
        self.assertEqual((RM.LINKED, "N001"), (st2, bc2["ids"]["P29E"]))

    def test_i_2_without_a_p29e_claim_the_site_is_still_a_base_with_no_pairing(self):
        t = self.tok()
        for p29 in ([], [fake_claim("N001", span=u"別の文脈の100億円")], [fake_claim("N001"), fake_claim("N002")]):          # 無い・span が違う・同じ鍵が 2 件
            st, bc = RM.base_status_rb({"P29E": p29, "P30E": [fake_claim("N005")]}, {}, t, self.text)
            self.assertEqual(RM.UNLINKED, st)
            self.assertEqual({"P29E": None, "P30E": "N005"}, bc["ids"])

    def test_i_2b_a_site_where_p30e_is_not_grounded_or_has_no_claim_is_not_a_base(self):
        t = self.tok()
        self.assertEqual((u"P30E が GROUNDED でない", None), RM.base_status_rb({"P29E": [fake_claim("N001")], "P30E": [fake_claim("N005", "VALUE_MISMATCH")]}, {}, t, self.text))
        self.assertEqual((u"基準に対応が付かない", None), RM.base_status_rb({"P29E": [fake_claim("N001")], "P30E": []}, {}, t, self.text))
        self.assertEqual((u"基準に対応が付かない", None), RM.base_status_rb({"P29E": [fake_claim("N001")], "P30E": [fake_claim("N005"), fake_claim("N006")]}, {}, t, self.text))
        # P29E だけが GROUNDED の site は土台にならない(土台を P30E から決める)
        self.assertEqual((u"P30E が GROUNDED でない", None), RM.base_status_rb({"P29E": [fake_claim("N001")], "P30E": [fake_claim("N005", "UNVERIFIABLE")]}, {}, t, self.text))

    def _inject(self, p29_claims):
        tok = self.tok()
        new = 150.0
        inj = {"type": "T1_VALUE", "id": "K-T1-01", "new_value": new, "replacement": RUN.N.render_value(new, tok), "span": [tok.start, tok.end], "detail": {"original_value": tok.value}}
        ids = {"P29E": "N001", "P30E": "N005"}
        calls = []

        def verify(zb, p, t):
            calls.append((p, u"150" in t))
            if u"150" in t:                                    # 改ざんした文: 原本と同じ pointer を名指し、recomputed も原本のまま(= 名指して原本の値を返した)
                return {"claims": [fake_claim(ids[p], "VALUE_MISMATCH", value=150.0, span=u"売上高は150億円でした")]}
            return {"claims": p29_claims if p == "P29E" else [fake_claim(ids[p])]}
        with Patch() as pt:
            pt.set(RUN, "PROFILES", RM.INJECT_PROFILES)
            pt.set(RUN, "base_status4", RM.base_status_rb)
            pt.set(RM.IJ, "select", lambda *a, **k: ([inj], {"T1_VALUE": 1}, None, None))
            rows, counts = RM.inject_text_rb(b"", self.text, [], "seed", "K", 10, verify)
        return [r for r in rows if r[u"型"] == "T1_VALUE"], counts, calls

    def test_i_3_inject_text_rb_classifies_each_profile_against_its_own_base_claim(self):
        t1, counts, _calls = self._inject([fake_claim("N001")])
        self.assertEqual(1, len(t1))
        self.assertEqual("N005", t1[0][u"基準の claim"])                           # 基準の claim は P30E の claim の id
        self.assertTrue(t1[0][RM.LINK_KEY])
        for p in RM.INJECT_PROFILES:
            self.assertEqual(TUNE.LABEL_NAMED_ORIGINAL, t1[0][p][u"結果"], p)
        self.assertEqual(1, counts["T1_VALUE"][RM.LINKED])
        self.assertNotIn(u"P28E の土台に対応", t1[0])

    def test_i_3b_a_row_without_a_p29e_claim_gets_not_corresponding_for_p29e_and_p29e_is_not_run_on_it(self):
        t1, counts, calls = self._inject([])
        self.assertEqual(1, len(t1))
        self.assertFalse(t1[0][RM.LINK_KEY])
        self.assertEqual({u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}, dict(t1[0]["P29E"]))
        self.assertEqual(TUNE.LABEL_NAMED_ORIGINAL, t1[0]["P30E"][u"結果"])
        self.assertEqual(1, counts["T1_VALUE"][RM.UNLINKED])
        self.assertNotIn(("P29E", True), calls)                                     # 改ざんした文を P29E で判定しない
        rows = [dict(r, form="F1", model="m", writer="W1") for r in t1]                 # 本の欄は inject_job_rb が足す
        with Patch() as pt:
            pt.set(RUN, "PROFILES", RM.INJECT_PROFILES)
            full = RUN.inject_summary(rows)
            cmp_ = RUN.inject_summary([r for r in rows if r[RM.LINK_KEY]])
            self.assertEqual((full, cmp_), RM.inject_summaries(rows))
            two = rows + [dict(rows[0], **{"id": "x", RM.LINK_KEY: True, "P29E": dict(rows[0]["P29E"], **{u"対応": True, u"結果": TUNE.LABEL_PASS})})]
            f2, c2 = RM.inject_summaries(two)
            self.assertEqual((2, 1), (f2["T1_VALUE"]["P29E"][u"全体"][u"注入の行"], c2["T1_VALUE"]["P29E"][u"全体"][u"注入の行"]))        # 比較用は P29E に対応が付く site だけ
        self.assertEqual((1, 0), (full["T1_VALUE"]["P29E"][u"全体"][u"対応が付かない"], full["T1_VALUE"]["P29E"][u"全体"][u"対応が付く"]))
        self.assertEqual(0, cmp_["T1_VALUE"]["P29E"][u"全体"][u"注入の行"])
        self.assertEqual({u"全体": 1, "T1_VALUE": 1, "T8_REL": 0}, dict(RM.unlinked_counts(rows)))

    def test_i_5_the_site_choice_is_the_same_as_the_inherited_injection(self):
        u"""rmix の注入が site を選ぶ呼び方(``IJ.select`` の types・cap・鍵と、T8_REL の site を作る ``RUN.t8_candidates4`` の引数)を、前の便の ``RUN.inject_text`` と同じ入力で呼び比べて同じと留める。
        違いは土台の判定(profile)だけ。types に T8_REL を足す・cap を替える・T8 の site の作り方を替える変異は、呼び方が前の便とずれて赤になる。"""
        def calls(fn):
            seen = {"select": [], "t8": []}
            claims = [fake_claim("N001")]
            with Patch() as pt:
                pt.set(RUN, "PROFILES", RM.INJECT_PROFILES)
                pt.set(RUN, "base_status4", RM.base_status_rb)
                pt.set(RM.IJ, "select", lambda *a, **k: (seen["select"].append((a[1:], dict(k))) or ([], {"T1_VALUE": 0}, None, None)))
                pt.set(RUN, "t8_candidates4", lambda text, refs, base_claims, base_by_id, seed, key, cap: (seen["t8"].append((text, refs, sorted(base_claims), seed, key, cap)) or ([], collections.Counter())))
                rows, counts = fn(b"", self.text, ["ref"], "seed", "K", 7, lambda zb, p, t: {"claims": claims})
            return seen, rows, sorted(counts)
        mine = calls(RM.inject_text_rb)
        prev = calls(RUN.inject_text)
        self.assertEqual(prev, mine)
        self.assertEqual([((["ref"], "xbrl", "seed", "K", 7), {"types": ["T1_VALUE"]})], [(a, k) for a, k in mine[0]["select"]])
        self.assertEqual(1, len(mine[0]["t8"]))
        self.assertEqual(["T1_VALUE", "T8_REL"], mine[2])

    def test_i_4_the_runner_swap_reaches_the_callers(self):
        with Patch() as pt:
            pt.set(RUN, "PROFILES", RUN.PROFILES)
            pt.set(RUN, "base_status4", RUN.base_status4)
            self.assertNotEqual([], RM.inject_wiring_problems())                       # 入れ替える前は赤
            RM.install_inject()
            self.assertEqual([], RM.inject_wiring_problems())
            self.assertIs(RUN.t8_candidates4.__globals__["base_status4"], RM.base_status_rb)      # 使う側(t8_candidates4)が引く名前に届いている
            RUN.PROFILES = ("P27", "P27E", "P28", "P28E")
            self.assertNotEqual([], RM.inject_wiring_problems())
        self.assertEqual(("P27", "P27E", "P28", "P28E"), tuple(RUN.PROFILES))              # 戻っている

    def test_w_4_regress97_runs_with_two_processes(self):
        u"""``--procs 2`` 以上で doc_job を module 名で pickle できる(読み込んだ module が sys.modules に登録されている)。``--only`` 1 書類・出力は TMPDIR の下(本番の記録は作らない)。"""
        if not all(os.path.isdir(p) for p in RR.R97.CACHES.values()):
            self.skipTest(u"手元の cache が無い")
        first = sorted(r97_docs_from_prev())[0]
        self.assertIs(sys.modules.get(RR.XR.__name__), RR.XR)
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            out = os.path.join(d, "r97.json")
            RR.main(["--only", first, "--out", out, "--procs", "2"])
            with open(out, encoding="utf-8") as fh:
                rec = json.load(fh)
        self.assertEqual([first], [x[u"docID"] for x in rec[u"書類"]])
        self.assertTrue(rec[u"範囲"].startswith(u"**--only"))                                     # 本番の記録ではない

    def test_i_7_run_inject_writes_the_record_with_the_base_text_the_two_summaries_and_the_unlinked_count(self):
        u"""run_inject の記録の組み立て(土台の字・限界・集計 2 本・対応なしの行の数)を、読み込み・並列・cache を偽にして 1 回通す。"""
        rows = norm(sample_inject()[u"行"])
        item = {u"docID": "DOC1", u"form": "F1", u"model": "m1", u"writer": "W1", u"sha256": "0" * 64}
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(RUN, "PROFILES", RUN.PROFILES)
            pt.set(RUN, "base_status4", RUN.base_status4)
            pt.set(NF, "load_books", lambda root=ROOT, only=None: [("aiforms", "DOC1_F1_m1", item, {}, {})])
            pt.set(NF, "map_pool", lambda fn, jobs_, procs: [("DOC1_F1_m1", [collections.OrderedDict(r) for r in rows], {})])
            pt.set(RM, "caches_all", lambda: collections.OrderedDict())
            pt.set(GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
            out = os.path.join(d, "inject.json")
            rec = RM.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with open(out, encoding="utf-8") as fh:
                disk = json.load(fh)
        self.assertEqual(norm(rec), disk)
        self.assertEqual(BASE_WORD_PIN, disk[u"型"][u"土台"])
        self.assertIn(LIMIT_PIN, disk[u"限界"])
        self.assertEqual({u"全体": 1, "T1_VALUE": 0, "T8_REL": 1}, disk[u"P29E に対応なしの行の数"])
        self.assertEqual(sample_inject()[RM.COMPARE_KEY], disk[RM.COMPARE_KEY])
        self.assertEqual(sample_inject()[u"集計"], disk[u"集計"])
        self.assertEqual([u"P29E", u"P30E"], disk[u"profile"])
        self.assertEqual([], [x for x in inject_problems(disk, False) if u"土台" in x or u"限界" in x or u"対応なし" in x or u"集計" in x])


# ================================================================ 宣言(docID を持つ記録 3 つは LATER_NAMING_FILES に宣言する)
def later_naming_files(src):
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "LATER_NAMING_FILES":
            return list(ast.literal_eval(n.value))
    return None


def naming_problems(src):
    got = later_naming_files(src)
    if got is None:
        return [u"LATER_NAMING_FILES が読めない"]
    return [u"LATER_NAMING_FILES に %s が無い" % rel for rel in REC_REL.values() if rel not in got] + \
        [u"LATER_NAMING_FILES に docID を持たない %s がある" % rel for rel in list(REC_SCRIPT.values()) + [DOC_REL] + list(SG.GATE_RELS) if rel in got]


class DeclarationTest(unittest.TestCase):
    def test_h_1_the_three_records_are_declared_as_naming_files(self):
        src = read("tests/measure/test_xbrl_fresh_seal.py")
        self.assertEqual([], naming_problems(src))
        for rel in REC_REL.values():
            self.assertNotEqual([], naming_problems(src.replace('"%s"' % rel, '"x/%s"' % rel)), rel)
        self.assertNotEqual([], naming_problems(src.replace("LATER_NAMING_FILES", "LATER_NAMING_FILE")))
        self.assertNotEqual([], naming_problems(src.replace('"fixtures/xbrl/rmix/regress97_2026-11-04.json"', '"fixtures/xbrl/rmix/regress97_2026-11-04.json", "%s"' % SG.GATE_RELS[0])))

    def test_h_2_the_previous_declarations_are_still_there(self):
        got = later_naming_files(read("tests/measure/test_xbrl_fresh_seal.py"))
        for rel in ("fixtures/xbrl/numfix/ai200_2026-11-04.json", "fixtures/xbrl/numfix/regress97_2026-11-04.json", "fixtures/xbrl/p28e/regress97_2026-11-03.json"):
            self.assertIn(rel, got)


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

    def test_e_5_order_of_uses_the_engine_files_and_the_records_and_the_document(self):
        r, s = self._repo()
        self.assertEqual([], order_of(r.d, s[:7]))
        r2, s2 = self._repo(commit_others=OTHERS[:-1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[-1]], order_of(r2.d, s2[:7]))
        r3, s3 = self._repo(commit_impl=False)
        self.assertTrue(any(x.startswith("IMPL_UNCOMMITTED:") for x in order_of(r3.d, s3[:7])))
        self.assertEqual(list(ENGINE_FILES), IMPLS)

    def test_e_3_a_wrong_seal_is_red(self):
        r, _s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", PR.order_problems(r.d, PREFIX, SEAL_REL, "abcdef0", IMPLS, OTHERS))

    def test_e_4_the_engine_fingerprint_comes_from_the_tree_at_the_engine_commit(self):
        fp = engine_fingerprint_at_commit()
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
            self.skipTest(u"記録が無い(判定・注入・97 書類を走らせた後に走る)")
        return load_records()

    def test_r_1_records_are_clean_and_consistent(self):
        R = self.need()
        self.assertEqual([], record_problems(copy.deepcopy(R), full=True))

    def test_r_2_judgment_is_rebuilt_from_the_records(self):
        R = self.need()
        self.assertEqual([], judge_problems(R, self.seal))
        J = RM.build_J(R, self.seal)
        self.assertEqual(set(J), {u"D", u"K", u"採用", u"欄"})

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


if __name__ == "__main__":
    unittest.main()
