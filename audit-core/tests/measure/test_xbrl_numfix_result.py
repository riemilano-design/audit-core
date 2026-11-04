# -*- coding: utf-8 -*-
"""数の読み取り N(P29 = P28 + N・P29E = P28E + N)の測定の結果の門。封 docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md §5-4。

記録 4 つ(``fixtures/xbrl/numfix/``: ai200・inject・regress97・shapes)から、封 §3 の予測 C-1〜C-13 と §4 の採用の基準 K-1〜K-5 を**機械で求め**(予測の幅は封の字から読む。
字のコピーにしない)、結果の文書 ``docs/XBRL_NUMBER_READER_ENGINE_RESULT_2026-11-04.md`` の表(``<!-- 門:start pred -->``・``<!-- 門:start judge -->`` の中)を
記録から作り直した表と一行も違わないことを見る。測定の script(``measure/xbrl_numfix_2026-11-04.py`` の ``build_J``・``render_pred``・``render_judge``)の関数を呼んで照らす。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文など)が無い・key_leaks が空・docID を持つ記録が ``LATER_NAMING_FILES`` に宣言されている・cache の前後が同じ・script の sha256 が現物と一致・
     engine の指紋が engine の commit の木から作り直した値と一致する。
  b  記録の中身が再計算と一致する: 本ごとの数の整合・集計(``aggregate``)・注入の集計(``inject_summary``)・97 書類の集計(``summarize_docs``)・形の数の和・C-13(git の履歴から)。
  c  判定: 記録を 1 つ変えると判定が変わる。境界の値(幅の端と端の外)で当たり ↔ 外れが替わる。採用は K-1〜K-4 を全部満たすときだけ。
  d  文書の表 = 記録から作り直した表。禁止語なし。docID なし。散文の 3 桁以上の数には【門なし】。
  e  順序: 封 48e7078 ⊏ engine を触った commit ⊏ 記録・結果の文書(script・門の順序は封の門が見る)。未 commit は赤(skip にしない)。
  g  変異: 小さい標本の記録 4 つと文書で同じ検査が緑 → 変異(記録の数 1 つ・表の 1 字・封の予測の 1 字・順序・記録の禁止欄・指紋の 1 字・cache の前後)で赤。

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


SG = load_module("tests/measure/test_xbrl_numfix_seal.py", "numfix_seal_gate_for_result")        # engine の commit を履歴から探す関数。門としては走らせない
PR = SG.PR                                                                                       # doc_blocks・prose_problems・order_problems・Repo
NF = load_module("measure/xbrl_numfix_2026-11-04.py", "numfix_script_for_gate")
R97 = load_module("measure/xbrl_numfix_regress97_2026-11-04.py", "numfix_regress97_for_gate")
SH = load_module("measure/xbrl_numfix_shapes_2026-11-04.py", "numfix_shapes_for_gate")
GEN, RUN = NF.GEN, NF.RUN
TUNE = RUN.TUNE

SEAL_REL = NF.SEAL_REL
DOC_REL = NF.DOC_REL
SEAL_COMMIT_SHORT = NF.SEAL_COMMIT
REC_REL = collections.OrderedDict(NF.REC_REL)
REC_SCRIPT = {"ai200": "measure/xbrl_numfix_2026-11-04.py", "inject": "measure/xbrl_numfix_2026-11-04.py",
              "regress97": "measure/xbrl_numfix_regress97_2026-11-04.py", "shapes": "measure/xbrl_numfix_shapes_2026-11-04.py"}
ENGINE_FILES = SG.ENGINE_FILES
NOT_GATED = PR.NOT_GATED
HIT, MISS = NF.HIT, NF.MISS
FORBIDDEN_KEYS = tuple(RUN.FORBIDDEN_KEYS) + (u"理由", u"根拠", u"周り", u"content")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = SG.DOCID_RE
FOR_RESULT_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
HAVE_CACHE = all(os.path.isdir(p) for p in NF.caches_all().values())
FP_KEY = {"ai200": u"engine の指紋", "inject": u"engine の指紋", "shapes": u"engine の指紋", "regress97": u"engine の指紋(この tree)"}
#: 封 §3・§4 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("C-1", (200, 200)), ("C-2", (97, 97, 6)), ("C-3", 0), ("C-4", (0.0, 2.0)), ("C-5", (5000.0, 6300.0)), ("C-6", (40.0, 65.0)), ("C-7", (0.0, 300.0)),
    ("C-8", (20.0, 40.0)), ("C-9", (2.0, 10.0)), ("C-10", 0),
    ("C-11", collections.OrderedDict([("T1_VALUE", (0.5, 3.0)), ("T8_REL", (0.0, 1.5))])), ("C-12", (75.0, 95.0)), ("C-13", (50.0, 80.0)), ("K-4", 30.0), ("K-5", 5)])


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def jload(rel):
    return json.loads(read(rel))


def sha256_rel(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


#: 注入の土台の字(依頼 2026-11-04 の直し 1: P29E が GROUNDED の claim。測定の script の定数と同じでなければ赤)
BASE_WORD_PIN = u"無改変の文で P29E が GROUNDED の claim"
#: 注入の限界の事実の字(監査の実測: N.scan は万・億のコンマの数を断片に切るので、新しく読めた数は土台に結べない)。測定の script の定数と同じでなければ赤
LIMIT_PIN = u"注入の仕掛け(N.scan)は万・億のコンマの数を断片に切るため、C-11・C-12・K-3 は新しく読めた数を測れない。測れるのは P28E・P29E の両方が読む数の site だけ"
LIMIT_WRONG = u"P28E が読まない数(万・億のコンマ)の site も土台に入り"
FORCE = {"no_records": False}                  # 試験が『記録が無い』状態を作るための旗(SkipLineTest だけが立てる)


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
    u"""C-13 の欄を履歴から作り直す(測定の script とは別に書く)。"""
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
def bounds_problems(seal):
    u"""封の字から読んだ予測の幅が、ここに留めた値と同じか。"""
    got = NF.seal_bounds(seal)
    out = []
    for k, v in BOUNDS_PIN.items():
        g = got.get(k)
        if json.dumps(norm_t(g), sort_keys=True) != json.dumps(norm_t(v), sort_keys=True):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, g, v))
    if list(NF.seal_pred_rows(seal)) != list(SG.PRED_IDS):
        out.append(u"封 §3 の予測の行が C-1〜C-13 でない")
    return out


def norm_t(v):
    if isinstance(v, dict):
        return dict((k, norm_t(x)) for k, x in v.items())
    if isinstance(v, (tuple, list)):
        return [float(x) for x in v]
    return float(v)


# ---------------------------------------------------------------- 記録(a)(b)
def walk(o):
    return list(RUN.walk_keys(o))


def r97_docs_from_prev():
    u"""前の便の記録の書類の一覧 {docID: 行}。"""
    return dict((r["docID"], r) for r in jload("fixtures/xbrl/p28e/regress97_2026-11-03.json")[u"書類"])


def header_problems(k, rec, script_rel):
    out = []
    if rec.get(u"seal") not in (SEAL_REL, "audit-core/" + SEAL_REL) or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"%s: 封の名か commit が違う" % k)
    if rec.get(u"この script の sha256") != sha256_rel(script_rel):
        out.append(u"%s: この script の sha256 が現物と違う" % k)
    if k == "shapes" and rec.get(u"numfix script の sha256") != sha256_rel(REC_SCRIPT["ai200"]):
        out.append(u"%s: numfix script の sha256 が現物と違う" % k)
    if k in ("ai200", "inject"):
        if rec.get(u"前の便の run script の sha256") != sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py"):
            out.append(u"%s: 前の便の run script の sha256 が現物と違う" % k)
        if rec.get(u"生成の script の sha256") != sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py"):
            out.append(u"%s: 生成の script の sha256 が現物と違う" % k)
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
    n = b[u"数の claim の数"]
    ex = b[u"既存の行"]
    new = b[u"新しい行の数"]
    if n["P29E"] - n["P28E"] != new - b[u"P28E にあって P29E に無い行"]:
        out.append(u"%s: P29E の数 − P28E の数 が 新しい行 − 消えた行 と合わない" % b[u"name"])
    if ex[u"行の数"] != n["P29E"] - new:
        out.append(u"%s: 既存の行の数が P29E の数 − 新しい行 と合わない" % b[u"name"])
    if sum(b[u"新しい行の state"].values()) != new or list(b[u"新しい行の state"]) != list(NF.STATES):
        out.append(u"%s: 新しい行の state の和が新しい行の数と合わない" % b[u"name"])
    if not (0 <= b[u"置き換えの行の数"] <= new) or b[u"そのうち新しい行と範囲が交わらない行"] > b[u"P28E にあって P29E に無い行"]:
        out.append(u"%s: 置き換えか消えた行の数がおかしい" % b[u"name"])
    ch = ex[u"変わった行の中身"]
    if len(ch) != ex[u"変わった行"] or sum(ex[u"変わった行の内訳"].values()) != ex[u"変わった行"]:
        out.append(u"%s: 変わった行の数が中身・内訳と合わない" % b[u"name"])
    if ex[u"変わった行の内訳"][NF.SAME_SENTENCE_NEW] != sum(1 for c in ch if c[6]) or ex[u"変わった行のうち state が変わった行"] != sum(1 for c in ch if c[2] != c[3]):
        out.append(u"%s: 変わった行の内訳が中身と合わない" % b[u"name"])
    f = b[u"旗が偽の byte 一致"]
    if f[u"一致"] != (f[u"行"] and f[u"4 state"] and f[u"claim の数"]):
        out.append(u"%s: 旗が偽の byte 一致が 3 つの欄と合わない" % b[u"name"])
    if b[u"O が決めた行"]["P29E"] > b[u"O の形の行"]["P29E"] or b[u"O が決めた行"]["P28E"] > b[u"O の形の行"]["P28E"]:
        out.append(u"%s: O が決めた行が O の形の行より多い" % b[u"name"])
    if list(b[u"対応"]) != list(NF.NOW_PROFILES):
        out.append(u"%s: 対応の欄の profile が違う" % b[u"name"])
    ro = b[u"書類の丸め方"]
    if list(ro) != ["P28E", "P29E"] or any(list(v) != list(NF.ROUNDING_NONE) for v in ro.values()):
        out.append(u"%s: 書類の丸め方の欄の形が違う" % b[u"name"])
    else:
        for v in ro.values():
            if v[u"決定"] not in (None, "round", "truncate") or any(not isinstance(v[k], int) or v[k] < 0 for k in (u"round-only", u"truncate-only", u"両方")):
                out.append(u"%s: 書類の丸め方の決定か根拠の数がおかしい" % b[u"name"])
        if b[u"丸め方の決定が P28E と P29E で違う"] != (ro["P28E"][u"決定"] != ro["P29E"][u"決定"]):
            out.append(u"%s: 丸め方の決定が違うかの欄が決定と合わない" % b[u"name"])
    nn = b[u"同じ文に新しい行が無いのに変わった既存の行"]
    if [(c[0], c[1], c[2], c[3]) for c in ch if not c[6]] != [(x[1], x[2], x[3], x[4]) for x in nn if len(x) == 7]:
        out.append(u"%s: 同じ文に新しい行が無いのに変わった既存の行の一覧が変わった行の中身と合わない" % b[u"name"])
    for x in nn:
        if len(x) != 7 or x[0] != u"num" or not isinstance(x[1], int) or not isinstance(x[2], int) or x[3] not in NF.STATES or x[4] not in NF.STATES \
                or any(not (y is None or isinstance(y, str)) for y in x[5:]):
            out.append(u"%s: 一覧の行の形が(種類, 文の番号, 位置, state 前, state 後, reason 前, reason 後)でない" % b[u"name"])
    return out


def ai200_problems(rec, full):
    out = []
    if rec.get(u"profile") != list(NF.NOW_PROFILES):
        out.append(u"ai200: profile が (P28E, P29E, P29E-O) でない")
    books = rec[u"本"]
    for b in books:
        out += book_problems(b)
    try:
        agg = norm(NF.aggregate(books))
    except Exception as e:                                   # noqa: BLE001  壊れた記録は集計できない = 赤
        return out + [u"ai200: 本から集計を作れない(%s)" % type(e).__name__]
    if agg != rec[u"集計"]:
        out.append(u"ai200: 集計が本から作り直した値と違う")
    if not all(all(b[u"対応"].values()) for b in books):
        out.append(u"ai200: claim の並びが profile 間で対応しない本がある")
    if full:
        prior = []
        for src, p in NF.SOURCES.items():
            c = jload(p["claims"])
            prior += [(src, b) for b in c[u"本"] if not b.get(u"欠け")]
        if [(b[u"材料"], b[u"name"], b[u"docID"], b[u"form"], b[u"model"]) for b in books] != [(s, b[u"name"], b[u"docID"], b[u"form"], b[u"model"]) for s, b in prior]:
            out.append(u"ai200: 本の並びが前の便の claims の記録の本(160 + 40)と違う")
        if len(books) != 200:
            out.append(u"ai200: 本が 200 本でない")
        shas = dict((u"%s_%s" % (src, k), sha256_rel(p[k])) for src, p in NF.SOURCES.items() for k in ("gen", "claims"))
        if rec.get(u"入力の記録の sha256") != shas:
            out.append(u"ai200: 入力の記録の sha256 が現物と違う")
        gens = dict((src, sha256_rel(p["gen"])) for src, p in NF.SOURCES.items())
        if rec.get(u"生成の記録の sha256") != gens:
            out.append(u"ai200: 生成の記録の sha256 が現物と違う")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(NF.caches_all())):
            out.append(u"ai200: cache の件数か名前が記録の前と違う")
    return out


def inject_problems(rec, full):
    out = []
    if rec.get(u"profile") != list(NF.INJECT_PROFILES):
        out.append(u"inject: profile が (P28E, P29E) でない")
    if rec[u"型"].get(u"土台") != BASE_WORD_PIN or NF.BASE_WORD != BASE_WORD_PIN:
        out.append(u"inject: 型.土台 の字が P29E が GROUNDED の claim でない")
    lim = rec.get(u"限界") or []
    if LIMIT_PIN not in lim or NF.LIMIT_SCAN != LIMIT_PIN:
        out.append(u"inject: 限界に事実の字(N.scan は万・億のコンマの数を断片に切る = 新しく読めた数は測れない)が無い")
    if any(LIMIT_WRONG in x or u"新しく読めた数も土台に入る" in x for x in lim):
        out.append(u"inject: 限界に事実と逆の字(新しく読めた数も土台に入る)がある")
    want = collections.OrderedDict([(u"全体", sum(1 for r in rec[u"行"] if r.get(u"P28E の土台に対応") is not True))])
    for t in RUN.INJECT_TYPES:
        want[t] = sum(1 for r in rec[u"行"] if r.get(u"型") == t and r.get(u"P28E の土台に対応") is not True)
    if norm(rec.get(u"P28E に対応なしの行の数")) != norm(want):
        out.append(u"inject: P28E に対応なしの行の数が行から数え直した値と違う")
    labels = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
    seen, cnt = set(), collections.Counter()
    for r in rec[u"行"]:
        if r[u"型"] not in RUN.INJECT_TYPES:
            out.append(u"inject: 型が語でない")
        if r[u"id"] in seen:
            out.append(u"inject: 同じ注入の id が 2 回ある")
        seen.add(r[u"id"])
        cnt[(r[u"docID"], r[u"form"], r[u"model"], r[u"型"])] += 1
        linked = r.get(u"P28E の土台に対応")
        unmapped = {u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}
        if not isinstance(linked, bool):
            out.append(u"inject: P28E の土台に対応の欄が真偽でない")
        elif not linked and norm(r["P28E"]) != unmapped:
            out.append(u"inject: P28E の土台に対応が無い行の P28E の欄が対応なしでない")
        if r["P29E"][u"対応"] is True and r["P29E"][u"結果"] == TUNE.LABEL_UNMAPPED:
            out.append(u"inject: P29E の欄の対応と結果が合わない")
        if r[u"型"] == "T8_REL" and (r.get("r") not in TUNE.T8_R_VALUES or not (1 <= r[u"r を決めた回"] <= TUNE.T8_TRIES)):
            out.append(u"inject: T8_REL の r が決めた値でない")
        for p in NF.INJECT_PROFILES:
            c = r[p]
            if c[u"結果"] not in labels:
                out.append(u"inject: 結果が classify の語でない")
            if not RUN.reason_ok(c[u"reason"]):
                out.append(u"inject: reason が符号の形でない")
    if any(n > RUN.INJECT_CAP for n in cnt.values()):
        out.append(u"inject: 1 本あたり型ごとの上限 %d を超えている" % RUN.INJECT_CAP)
    with Patch() as pt:
        pt.set(RUN, "PROFILES", NF.INJECT_PROFILES)
        summ = norm(RUN.inject_summary(rec[u"行"]))
        summ_cmp = norm(RUN.inject_summary([r for r in rec[u"行"] if r.get(u"P28E の土台に対応") is True]))
    if summ != rec[u"集計"] or rec[u"注入の行の数"] != len(rec[u"行"]):
        out.append(u"inject: 集計が行から作り直した値と違う")
    if summ_cmp != rec.get(NF.COMPARE_KEY):
        out.append(u"inject: 比較用の集計(P28E にも対応が付く site だけ)が行から作り直した値と違う")
    if full:
        names = [b[u"name"] for src in NF.SOURCES.values() for b in jload(src["claims"])[u"本"] if not b.get(u"欠け")]
        if list(rec[u"本ごとの数え"]) != names:
            out.append(u"inject: 本ごとの数えの本が 200 本(前の便の claims の並び)でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(NF.caches_all())):
            out.append(u"inject: cache の件数か名前が記録の前と違う")
    return out


def regress97_problems(rec, full):
    out = []
    docs = rec[u"書類"]
    try:
        T = norm(R97.summarize_docs(docs))
    except Exception as e:                                   # noqa: BLE001
        return [u"regress97: 書類から集計を作れない(%s)" % type(e).__name__]
    got = dict((k, v) for k, v in rec[u"集計"].items() if k != u"C-13 engine の留めの連動で直す試験 file")
    if T != got:
        out.append(u"regress97: 集計が書類から作り直した値と違う")
    for d in docs:
        for n, a, b in R97.PAIRS:
            mv = d[u"動いた行と増えた行"][n]
            if sum(mv[u"増えた行の state"].values()) != mv[u"増えた行"]:
                out.append(u"regress97: 増えた行の state の和が増えた行と合わない")
            if d[u"claims"][b] - d[u"claims"][a] != mv[u"増えた行"] - mv[u"消えた行"]:
                out.append(u"regress97: claim の数の差が 増えた行 − 消えた行 と合わない")
        if sorted(d[u"4 state"]) != sorted(R97.NOW_PROFILES):
            out.append(u"regress97: 4 state の profile が違う")
    if full:
        prev = r97_docs_from_prev()
        if sorted(d[u"docID"] for d in docs) != sorted(prev):
            out.append(u"regress97: 書類が前の便の記録の 97 書類と違う")
        for d in docs:
            pr = prev.get(d[u"docID"])
            if pr is None:
                continue
            if d[u"前の便の記録の sha256"] != dict((p, pr[u"出力の sha256(engine の欄を除く)"][p]) for p in R97.BASE_PROFILES) or d[u"zip の sha256"] != pr[u"zip の sha256"]:
                out.append(u"regress97: 前の便の記録の sha256 か zip の sha256 が前の便の記録と違う")
        if rec[u"前の便の記録の sha256"] != sha256_rel(R97.PREV_RECORD_REL):
            out.append(u"regress97: 前の便の記録の sha256 が現物と違う")
        if rec[u"集計"][u"C-13 engine の留めの連動で直す試験 file"] != norm(link_at_history()):
            out.append(u"regress97: C-13 が git の履歴から作り直した値と違う")
        if len(docs) != 97:
            out.append(u"regress97: 書類が 97 でない")
    return out


def group_problems(name, g, unit):
    out = []
    n = g[u"円族の候補"]
    for r in SH.READERS:
        if sum(g[u"読み %s" % r].values()) != n:
            out.append(u"shapes: %s の読み %s の和が候補の数と合わない" % (name, r))
    if sum(c[u"候補"] for c in g[u"形"].values()) != n:
        out.append(u"shapes: %s の形の候補の和が候補の数と合わない" % name)
    for r in SH.READERS:
        for kj in SH.KIND_JA.values():
            if sum(c[r][kj] for c in g[u"形"].values()) != g[u"読み %s" % r][kj]:
                out.append(u"shapes: %s の形別の和が読み %s と合わない" % (name, r))
    for sh, c in g[u"形"].items():
        if any(sum(c[r].values()) != c[u"候補"] for r in SH.READERS):
            out.append(u"shapes: %s の形 %s の読みの和が候補と合わない" % (name, sh))
    left = collections.OrderedDict(sorted(((sh, c["11_04"][SH.KIND_JA["none"]]) for sh, c in g[u"形"].items() if c["11_04"][SH.KIND_JA["none"]]), key=lambda kv: (-kv[1], kv[0])))
    if norm(left) != g[u"11_04 でも読まない形"]:
        out.append(u"shapes: %s の 11_04 でも読まない形が形から作り直した値と違う" % name)
    o = g[u"「その他」の直後"]
    for r in SH.READERS:
        if sum(o[u"読み %s" % r].values()) != o[u"直後が円の数"]:
            out.append(u"shapes: %s の「その他」の読み %s の和が円の数と合わない" % (name, r))
    if o[u"直後が円の数"] > o[u"「その他」の位置"] or sum(c[u"候補"] for c in o[u"形"].values()) != o[u"直後が円の数"]:
        out.append(u"shapes: %s の「その他」の数がおかしい" % name)
    return out


def shapes_problems(rec, full):
    out = []
    G = rec[u"群"]
    for name, g in G.items():
        out += group_problems(name, g, u"本" if name.startswith(u"AI") else u"書類")
    forms = [u"AI の文 %s" % f for f in SH.FORMS]
    if full:
        if list(G) != forms + [u"AI の文 200 本", u"有報 fresh 40", u"有報 prior 94", u"有報 手元の 97 書類"]:
            out.append(u"shapes: 群の並びが違う")
        tot = G[u"AI の文 200 本"]
        if tot[u"本"] != 200 or sum(G[f][u"本"] for f in forms) != 200:
            out.append(u"shapes: AI の文が 200 本でない")
        for key in (u"円族の候補", u"読み 10_27", u"読み 11_04"):
            a = tot[key]
            if isinstance(a, dict):
                if any(sum(G[f][key][k] for f in forms) != a[k] for k in a):
                    out.append(u"shapes: AI の文 200 本の %s が形の和と合わない" % key)
            elif sum(G[f][key] for f in forms) != a:
                out.append(u"shapes: AI の文 200 本の %s が形の和と合わない" % key)
        if [G[u"有報 fresh 40"][u"書類"], G[u"有報 prior 94"][u"書類"], G[u"有報 手元の 97 書類"][u"書類"]] != [40, 94, 97]:
            out.append(u"shapes: 有報の書類の数が 40・94・97 でない")
        if any(G[k][u"取れなかった書類"] for k in (u"有報 fresh 40", u"有報 prior 94", u"有報 手元の 97 書類")):
            out.append(u"shapes: 取れなかった書類がある")
        if rec[u"範囲"] != u"全材料":
            out.append(u"shapes: 範囲が全材料でない")
        if HAVE_CACHE and rec[u"cache の前後"][u"前"] != norm(GEN.caches_snapshot(NF.caches_all())):
            out.append(u"shapes: cache の件数か名前が記録の前と違う")
    return out


def record_problems(R, full=True):
    u"""記録 4 つの検査(禁止欄・鍵・script の sha256・engine の指紋・cache・再計算)。問題の列。"""
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
    out += safe("shapes", shapes_problems, R["shapes"], full)
    if full and R["regress97"].get(u"範囲") != u"全 97 書類":
        out.append(u"regress97: 範囲が全 97 書類でない")
    return out


def judge_problems(R, seal):
    u"""判定の関数が記録から作り直せるか(壊れた記録は赤)。"""
    try:
        J = NF.build_J(R, seal)
    except Exception as e:                                   # noqa: BLE001
        return [u"判定を作れない(%s)" % type(e).__name__]
    out = []
    if list(J[u"C"]) != list(SG.PRED_IDS) or list(J[u"K"]) != list(SG.K_IDS):
        out.append(u"判定の行が C-1〜C-13・K-1〜K-5 でない")
    return out


# ---------------------------------------------------------------- 文書(d)
def doc_problems(doc, R, seal):
    J = NF.build_J(R, seal)
    got = PR.doc_blocks(doc)
    out = []
    if got.get("pred") != NF.render_pred(J, seal).split(u"\n"):
        out.append(u"表 pred が記録から作り直した表と違う")
    if got.get("judge") != NF.render_judge(J, seal).split(u"\n"):
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


# ================================================================ 小さい標本の記録 4 つ(通信しない・cache を読まない)
def prow(b, state, reason=None, ptr=(), o=None):
    return {"b": b, "state": state, "reason": reason, "pointers": list(ptr), "o": o}


def sample_books():
    G, V_, U, P = "GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"
    items = [dict(docID="DOC1", form="F1", model="m1", writer="W1", sha256="0" * 64), dict(docID="DOC2", form="F5", model="m2", writer="W2", sha256="1" * 64)]
    same_ok = collections.OrderedDict([(u"行", True), (u"4 state", True), (u"claim の数", True)])
    ok = dict((p, True) for p in NF.NOW_PROFILES)
    # 本 1: P28E 3 行。P29E は新しい行 3(うち 1 つは P28E の行 (2, 4) と範囲が交わる置き換え)・既存の行 (1, 5) が同じ文に新しい行 (1, 30) があって変わる
    r28 = {(0, 5): prow(9, G, None, ["a@当期"]), (1, 5): prow(9, P, "no_element"), (2, 4): prow(9, V_, None, ["b@当期"], o=[None, 1, False])}
    r29 = {(0, 5): prow(9, G, None, ["a@当期"]), (1, 5): prow(9, G, None, ["c@当期"]), (1, 30): prow(40, G, None, ["d@当期"]), (2, 2): prow(14, U, "x"), (3, 7): prow(20, P, "no_element"),
           }
    r29o = dict(r29)
    rnd_same = {"P28E": collections.OrderedDict([(u"決定", "round"), (u"round-only", 8), (u"truncate-only", 0), (u"両方", 7)]),
                "P29E": collections.OrderedDict([(u"決定", "round"), (u"round-only", 29), (u"truncate-only", 0), (u"両方", 43)])}
    rnd_diff = {"P28E": collections.OrderedDict([(u"決定", "truncate"), (u"round-only", 0), (u"truncate-only", 1), (u"両方", 1)]),
                "P29E": collections.OrderedDict([(u"決定", "round"), (u"round-only", 10), (u"truncate-only", 1), (u"両方", 13)])}
    b1 = NF.assemble_book("aiforms", "DOC1_F1_m1", items[0], same_ok, {"P28E": r28, "P29E": r29, "P29E-O": r29o}, ok, rnd_same)
    # 本 2: 新しい行 1・O の形の行が P29E で決まる(P29E−O では GROUNDED でない)
    # 文 3 の既存の行 (3, 1) は同じ文に新しい行が無いのに変わる(この本は書類の丸め方の決定が替わる本)
    q28 = {(0, 3): prow(8, P, "no_same_value", o=[None, 1, False]), (3, 1): prow(7, G)}
    q29 = {(0, 3): prow(8, G, None, ["a@当期"], o=[None, 1, True]), (0, 20): prow(30, V_, None, ["e@当期"]), (3, 1): prow(7, V_, "x")}
    q29o = {(0, 3): prow(8, P, "no_same_value"), (0, 20): prow(30, V_, None, ["e@当期"]), (3, 1): prow(7, V_, "x")}
    same_bad = collections.OrderedDict([(u"行", True), (u"4 state", False), (u"claim の数", True)])
    b2 = NF.assemble_book("f5", "DOC2_F5_m2", items[1], same_bad, {"P28E": q28, "P29E": q29, "P29E-O": q29o}, ok, rnd_diff)
    return [b1, b2]


def sample_header(k, script_rel, step):
    cache = collections.OrderedDict([("edinet", {u"存在": True, u"件数": 3, u"名前の一覧の sha256": "2" * 64})])
    h = collections.OrderedDict([
        (u"seal", SEAL_REL), (u"封の commit", SEAL_COMMIT_SHORT), (u"step", step), (u"HEAD の commit", "3" * 40), (u"この script の sha256", sha256_rel(script_rel)),
        (FP_KEY[k], dict(engine_fingerprint_at_commit(), adapter_xbrl_py_files=16, core_py_files=4, git_commit="3" * 40)),
        (u"cache の前後", collections.OrderedDict([(u"前", cache), (u"後", copy.deepcopy(cache)), (u"変化なし", True)]))])
    if k in ("ai200", "inject"):
        h[u"前の便の run script の sha256"] = sha256_rel("measure/xbrl_aiforms_run_2026-11-03.py")
        h[u"生成の script の sha256"] = sha256_rel("measure/xbrl_aiforms_gen_2026-11-03.py")
    if k == "shapes":
        h[u"numfix script の sha256"] = sha256_rel(REC_SCRIPT["ai200"])
    return h


def sample_ai200():
    books = sample_books()
    rec = sample_header("ai200", REC_SCRIPT["ai200"], u"標本")
    rec[u"profile"] = list(NF.NOW_PROFILES)
    rec[u"本"] = books
    rec[u"集計"] = norm(NF.aggregate(books))
    return norm(rec)


def sample_inject():
    def cell(res, state, reason=None):
        return collections.OrderedDict([(u"対応", True), (u"結果", res), (u"state", state), (u"reason", reason)])
    base = collections.OrderedDict([(u"docID", "DOC1"), (u"form", "F1"), (u"model", "m1"), (u"writer", "W1")])
    rows = []
    rows.append(collections.OrderedDict(list(base.items()) + [("id", "DOC1_F1_m1-T1-01"), (u"型", "T1_VALUE"), (u"基準の claim", "N001"), (u"P28E の土台に対応", True),
                                                               ("P28E", cell(TUNE.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH")), ("P29E", cell(TUNE.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH"))]))
    rows.append(collections.OrderedDict(list(base.items()) + [("id", "DOC1_F1_m1-T8-01"), (u"型", "T8_REL"), (u"基準の claim", "N002"), (u"P28E の土台に対応", True), ("r", 0.1), (u"r を決めた回", 1),
                                                               ("P28E", cell(TUNE.LABEL_PASS, "GROUNDED")), ("P29E", cell(TUNE.LABEL_PNF, "POINTER_NOT_FOUND", "no_element"))]))
    rows.append(collections.OrderedDict(list(base.items()) + [("id", "DOC1_F1_m1-T8-02"), (u"型", "T8_REL"), (u"基準の claim", "N003"), (u"P28E の土台に対応", False), ("r", -0.03), (u"r を決めた回", 2),
                                                               ("P28E", TUNE.classify(None, None)), ("P29E", cell(TUNE.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH"))]))
    with Patch() as pt:
        pt.set(RUN, "PROFILES", NF.INJECT_PROFILES)
        summ = norm(RUN.inject_summary(rows))
        summ_cmp = norm(RUN.inject_summary([r for r in rows if r[u"P28E の土台に対応"]]))
    rec = sample_header("inject", REC_SCRIPT["inject"], u"標本")
    rec[u"profile"] = list(NF.INJECT_PROFILES)
    rec[u"型"] = collections.OrderedDict([(u"土台", BASE_WORD_PIN)])
    rec[u"本ごとの数え"] = collections.OrderedDict([("DOC1_F1_m1", {})])
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"] = summ
    rec[NF.COMPARE_KEY] = summ_cmp
    rec[u"限界"] = [u"他の限界", LIMIT_PIN]
    rec[u"P28E に対応なしの行の数"] = collections.OrderedDict([(u"全体", 1), ("T1_VALUE", 0), ("T8_REL", 1)])
    rec[u"行"] = rows
    return norm(rec)


def sample_regress97():
    st = lambda g, v, u, p: collections.OrderedDict([("GROUNDED", g), ("VALUE_MISMATCH", v), ("UNVERIFIABLE", u), ("POINTER_NOT_FOUND", p)])    # noqa: E731
    docs = []
    for i, (n28, n29, moved, added) in enumerate(((10, 10, 0, 0), (12, 13, 2, 1))):
        d = u"DOC%d" % (i + 1)
        claims = collections.OrderedDict((p, n28 if p not in ("P29", "P29E") else n29) for p in R97.NOW_PROFILES)
        shas = collections.OrderedDict((p, hashlib.sha256((d + p).encode()).hexdigest()) for p in R97.NOW_PROFILES)
        mv = collections.OrderedDict()
        for name, a, b in R97.PAIRS:
            mv[name] = collections.OrderedDict([
                (u"動いた既存の行", [["num", 0, 3, 0, "POINTER_NOT_FOUND", "GROUNDED", "r", None, True]] * moved),
                (u"増えた行", added), (u"増えた行の state", st(added, 0, 0, 0)), (u"消えた行", 0)])
        docs.append(collections.OrderedDict([
            (u"docID", d), (u"標本", u"手元の 67"), (u"zip の sha256", "4" * 64), (u"claims", claims),
            (u"4 state", collections.OrderedDict((p, st(claims[p], 0, 0, 0)) for p in R97.NOW_PROFILES)),
            (u"出力の sha256(engine の欄を除く)", shas),
            (u"前の便の記録の sha256", collections.OrderedDict((p, shas[p]) for p in R97.BASE_PROFILES)),
            (u"動いた行と増えた行", mv)]))
    rec = sample_header("regress97", REC_SCRIPT["regress97"], u"標本")
    rec[u"範囲"] = u"標本"
    T = R97.summarize_docs(docs)
    T[u"C-13 engine の留めの連動で直す試験 file"] = collections.OrderedDict([(u"直した file(M)", 52), (u"新しい file(A)", 1), (u"engine の挿入の行数", 44)])
    rec[u"集計"] = T
    rec[u"書類"] = docs
    rec[u"key_leaks"] = []
    return norm(rec)


def sample_shapes():
    def group(sents, unit, n):
        acc = SH.new_acc()
        SH.count_sentences(sents, acc)
        acc["n"] = n
        return SH.group_json(acc, unit)
    ai = [u"売上高は12億3,456万円でした。", u"その他の費用は1,234万円で、営業利益は5億円でした。", u"利益は1万2,345円でした。"]
    G = collections.OrderedDict()
    G[u"AI の文 F1"] = group(ai[:2], u"本", 1)
    G[u"AI の文 F5"] = group(ai[2:], u"本", 1)
    G[u"有報 fresh 40"] = group([u"売上高は1,234百万円でした。"], u"書類", 1)
    for g in (G[u"有報 fresh 40"],):
        g[u"取れなかった書類"] = 0
    rec = sample_header("shapes", REC_SCRIPT["shapes"], u"標本")
    rec[u"範囲"] = u"標本"
    rec[u"群"] = G
    rec[u"key_leaks"] = []
    return norm(rec)


def sample_records():
    return collections.OrderedDict([("ai200", sample_ai200()), ("inject", sample_inject()), ("regress97", sample_regress97()), ("shapes", sample_shapes())])


def sample_agg_records(**ov):
    u"""判定の関数の境界の試験用: 集計だけを持つ記録(幅の真ん中の値)。ov = {名前: 値} で 1 つだけ替える。"""
    v = collections.OrderedDict([
        ("c1", 200), ("c2", 97), ("c3a", 0), ("c3b", 0), ("c4", 1), ("c4p", 50), ("c5", 5600), ("c6", 50.0), ("c7", 100), ("c7none", 0), ("c8", 30), ("c9", 6), ("c10", 0),
        ("t1", 1.0), ("t8", 0.5), ("o", 85.0), ("c13", 60)])
    v.update(ov)
    ai = {u"全体": {u"C-1 旗が偽の byte 一致": {u"一致した本": v["c1"], u"本": 200},
                  u"C-5 数の claim": {"P28E": 1000, "P29E": 1000 + v["c5"], u"P29E − P28E": v["c5"]},
                  u"C-6 新しい行の state": {u"GROUNDED の率": v["c6"], u"分母": 5600},
                  u"C-7 既存の行": {u"変わった行": v["c7"], NF.SAME_SENTENCE_NEW: v["c7"] - v["c7none"], NF.SAME_SENTENCE_NONE: v["c7none"]},
                  u"C-8 O の形の行": {"P28E": 12, "P29E": v["c8"]}, u"C-9 O が決めた行": {"P28E": 0, "P29E": v["c9"]},
                  u"C-10 P29E 対 P29E-O": {u"GROUNDED でなくなった行": v["c10"], u"O が GROUNDED にした行": 5}}}
    inj = {"T1_VALUE": {"P28E": {u"全体": {u"通した": {u"率": 9.9}}}, "P29E": {u"全体": {u"通した": {u"率": v["t1"]}}}},
           "T8_REL": {"P28E": {u"全体": {u"通した": {u"率": 9.9}, u"名指して原本の値を返した": {u"率": 9.9}}},
                      "P29E": {u"全体": {u"通した": {u"率": v["t8"]}, u"名指して原本の値を返した": {u"率": v["o"]}}}}}
    # inj = 全 site の集計(C-11・C-12・K-3 の P29E はこちら。P28E の欄は対応なしが混ざるので比較に使わない 9.9)。inj_cmp = 比較用(P28E にも対応が付く site だけ)
    inj_cmp = {"T1_VALUE": {"P28E": {u"全体": {u"通した": {u"率": 1.8}}}, "P29E": {u"全体": {u"通した": {u"率": 1.7}}}},
                           "T8_REL": {"P28E": {u"全体": {u"通した": {u"率": 0.6}, u"名指して原本の値を返した": {u"率": 85.1}}},
                                      "P29E": {u"全体": {u"通した": {u"率": 0.5}, u"名指して原本の値を返した": {u"率": 85.0}}}}}
    c2 = collections.OrderedDict((p, {u"byte が同じ書類": v["c2"], u"書類": 97}) for p in R97.BASE_PROFILES)
    r97 = {u"集計": {u"C-2 旗が偽の profile の byte 一致": c2, u"C-3 動いた既存の行": {"P29 対 P28": v["c3a"], "P29E 対 P28E": v["c3b"]},
                    u"C-4 増えた claim": {"P29": v["c4p"], "P29E": v["c4"]}, u"C-13 engine の留めの連動で直す試験 file": {u"直した file(M)": v["c13"], u"新しい file(A)": 1, u"engine の挿入の行数": 44}}}
    return {"ai200": {u"集計": ai}, "inject": {u"集計": inj, NF.COMPARE_KEY: inj_cmp}, "regress97": r97, "shapes": {}}


def sample_doc(R, seal):
    J = NF.build_J(R, seal)
    return u"\n".join([u"# 結果", u"", u"<!-- 門:start pred -->", NF.render_pred(J, seal), u"<!-- 門:end -->", u"",
                       u"<!-- 門:start judge -->", NF.render_judge(J, seal), u"<!-- 門:end -->", u"", u"散文の行。数は表に在る。", u"200 本の標本です。" + NOT_GATED, u""])


# ================================================================ (a) 封の字
class SealPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_bounds_read_from_the_seal_equal_the_pinned_values(self):
        self.assertEqual([], bounds_problems(self.seal))

    def test_a_2_a_changed_character_in_the_seal_prediction_turns_the_pin_red(self):
        rows = NF.seal_pred_rows(self.seal)
        for cid, old, new in (("C-5", "5,000", "5,001"), ("C-6", "40〜65%", "40〜64%"), ("C-9", "2〜10", "2〜11"), ("C-12", "75〜95%", "75〜96%"), ("C-11", "0.5〜3.0%", "0.5〜3.1%"), ("C-13", "50〜80", "49〜80")):
            self.assertIn(old, rows[cid][1], cid)
            mutated = self.seal.replace("| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1]), "| %s | %s | %s" % (cid, rows[cid][0], rows[cid][1].replace(old, new, 1)), 1)
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], bounds_problems(mutated), cid)

    def test_a_3_k4_and_k5_thresholds_are_read_from_the_seal(self):
        b = NF.seal_bounds(self.seal)
        self.assertEqual((30.0, 5), (b["K-4"], b["K-5"]))
        self.assertNotEqual([], bounds_problems(self.seal.replace("GROUNDED 率 ≥ 30%", "GROUNDED 率 ≥ 31%", 1)))
        self.assertNotEqual([], bounds_problems(self.seal.replace("C-9 の O が決めた行 ≥ 5 なら", "C-9 の O が決めた行 ≥ 6 なら", 1)))


# ================================================================ (c) 判定
class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def J(self, **ov):
        return NF.build_J(sample_agg_records(**ov), self.seal)

    def test_c_1_the_middle_of_every_range_is_a_hit_and_adoption_follows(self):
        J = self.J()
        for k, v in J[u"C"].items():
            self.assertEqual(HIT, v[u"判定"], k)
        for k in ("K-1", "K-2", "K-3", "K-4"):
            self.assertEqual(HIT, J[u"K"][k][u"判定"], k)
        self.assertTrue(J[u"採用"])
        self.assertIn(u"O は N のあとで効く", J[u"K"]["K-5"][u"値"][u"読み"])

    def test_c_2_each_prediction_flips_at_the_seal_boundary(self):
        b = BOUNDS_PIN
        cases = [("c1", "C-1", b["C-1"][0], b["C-1"][0] - 1), ("c2", "C-2", b["C-2"][0], b["C-2"][0] - 1),
                 ("c3a", "C-3", 0, 1), ("c3b", "C-3", 0, 1),
                 ("c4", "C-4", b["C-4"][0], None), ("c4", "C-4", b["C-4"][1], b["C-4"][1] + 1),
                 ("c5", "C-5", b["C-5"][0], b["C-5"][0] - 1), ("c5", "C-5", b["C-5"][1], b["C-5"][1] + 1),
                 ("c6", "C-6", b["C-6"][0], b["C-6"][0] - 0.1), ("c6", "C-6", b["C-6"][1], b["C-6"][1] + 0.1),
                 ("c7", "C-7", b["C-7"][1], b["C-7"][1] + 1), ("c7none", "C-7", 0, 1),
                 ("c8", "C-8", b["C-8"][0], b["C-8"][0] - 1), ("c8", "C-8", b["C-8"][1], b["C-8"][1] + 1),
                 ("c9", "C-9", b["C-9"][0], b["C-9"][0] - 1), ("c9", "C-9", b["C-9"][1], b["C-9"][1] + 1),
                 ("c10", "C-10", 0, 1),
                 ("t1", "C-11", b["C-11"]["T1_VALUE"][1], b["C-11"]["T1_VALUE"][1] + 0.1), ("t1", "C-11", b["C-11"]["T1_VALUE"][0], b["C-11"]["T1_VALUE"][0] - 0.1),
                 ("t8", "C-11", b["C-11"]["T8_REL"][1], b["C-11"]["T8_REL"][1] + 0.1),
                 ("o", "C-12", b["C-12"][0], b["C-12"][0] - 0.1), ("o", "C-12", b["C-12"][1], b["C-12"][1] + 0.1),
                 ("c13", "C-13", b["C-13"][0], b["C-13"][0] - 1), ("c13", "C-13", b["C-13"][1], b["C-13"][1] + 1)]
        for name, cid, inside, outside in cases:
            self.assertEqual(HIT, self.J(**{name: inside})[u"C"][cid][u"判定"], (name, inside))
            if outside is not None:
                self.assertEqual(MISS, self.J(**{name: outside})[u"C"][cid][u"判定"], (name, outside))

    def test_c_3_the_adoption_follows_k1_to_k4_and_k5_does_not_decide(self):
        self.assertFalse(self.J(c1=199)[u"採用"])                       # K-1(C-1)
        self.assertFalse(self.J(c2=96)[u"採用"])                        # K-1(C-2)
        self.assertFalse(self.J(c7=100, c7none=1)[u"採用"])              # K-2
        self.assertFalse(self.J(t1=3.1)[u"採用"])                       # K-3
        self.assertFalse(self.J(t8=1.6)[u"採用"])                       # K-3
        self.assertFalse(self.J(c6=29.9)[u"採用"])                      # K-4
        self.assertTrue(self.J(c6=30.0)[u"採用"])                       # K-4 の端は満たす(C-6 の予測は外れでも採用の基準は満たす)
        self.assertEqual(MISS, self.J(c6=30.0)[u"C"]["C-6"][u"判定"])
        self.assertTrue(self.J(c9=0)[u"採用"])                          # K-5 は採用に使わない
        self.assertIn(u"2 便続けて効かない", self.J(c9=4)[u"K"]["K-5"][u"値"][u"読み"])
        self.assertIn(u"N のあとで効く", self.J(c9=5)[u"K"]["K-5"][u"値"][u"読み"])

    def test_c_4_k3_uses_the_seal_upper_bounds_not_the_lower(self):
        J = self.J(t1=0.0)                                                        # C-11 の下の幅(0.5)の外。K-3 は上限(≤ 3.0)だけを見る
        self.assertEqual(MISS, J[u"C"]["C-11"][u"判定"])
        self.assertEqual(HIT, J[u"K"]["K-3"][u"判定"])

    def test_c_4b_the_p28e_comparison_comes_from_the_linked_sites_summary(self):
        J = self.J()
        self.assertEqual(1.8, J[u"C"]["C-11"][u"値"][u"T1_VALUE 通した率 P28E(比較用)"])
        self.assertEqual(0.6, J[u"C"]["C-11"][u"値"][u"T8_REL 通した率 P28E(比較用)"])
        self.assertEqual(85.1, J[u"C"]["C-12"][u"値"][u"P28E(比較用)"])
        self.assertEqual(0.0 + 1.0, J[u"C"]["C-11"][u"値"][u"T1_VALUE 通した率 P29E"])             # P29E は全 site の集計(比較用の 1.7 ではない)
        self.assertEqual(85.0, self.J(o=85.0)[u"C"]["C-12"][u"値"][u"T8_REL 名指して原本 P29E"])

    def test_c_5_the_judgment_moves_with_the_records(self):
        R = sample_agg_records()
        base = NF.build_J(R, self.seal)
        R2 = copy.deepcopy(R)
        R2["ai200"][u"集計"][u"全体"][u"C-5 数の claim"][u"P29E − P28E"] = 7000
        self.assertNotEqual(norm(base), norm(NF.build_J(R2, self.seal)))
        mutated_seal = self.seal.replace("+5,000〜+6,300", "+5,000〜+5,500", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertEqual(MISS, NF.build_J(R, mutated_seal)[u"C"]["C-5"][u"判定"])

    def test_c_6_a_broken_record_is_red_not_an_exception(self):
        R = sample_agg_records()
        del R["ai200"][u"集計"][u"全体"][u"C-5 数の claim"]
        self.assertNotEqual([], judge_problems(R, self.seal))
        self.assertEqual([], judge_problems(sample_agg_records(), self.seal))


# ================================================================ (g) 小さい標本の記録 4 つと文書の変異
class SampleFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.R = sample_records()

    def test_g_0_the_sample_is_green(self):
        self.assertEqual([], record_problems(copy.deepcopy(self.R), full=False))
        doc = sample_doc(self.R, self.seal)
        self.assertEqual([], doc_problems(doc, self.R, self.seal))

    def test_g_1_the_sample_exercises_new_replaced_changed_and_O_rows(self):
        b1, b2 = self.R["ai200"][u"本"]
        self.assertEqual((3, 1, 1), (b1[u"新しい行の数"], b1[u"置き換えの行の数"], b1[u"P28E にあって P29E に無い行"]))
        self.assertEqual({NF.SAME_SENTENCE_NEW: 1, NF.SAME_SENTENCE_NONE: 0}, b1[u"既存の行"][u"変わった行の内訳"])
        self.assertEqual((1, 1), (b2[u"O が決めた行"]["P29E"], b2[u"P29E 対 P29E-O"][u"O が GROUNDED にした行"]))
        self.assertEqual(0, b2[u"P29E 対 P29E-O"][u"GROUNDED でなくなった行"])
        self.assertFalse(b2[u"旗が偽の byte 一致"][u"一致"])

    def _red(self, mutate, **kw):
        R = copy.deepcopy(self.R)
        mutate(R)
        self.assertNotEqual([], record_problems(R, full=False), kw)

    def test_g_2_one_number_in_a_record_turns_it_red(self):
        self._red(lambda R: R["ai200"][u"本"][0][u"数の claim の数"].__setitem__("P29E", 99))
        self._red(lambda R: R["ai200"][u"本"][0].__setitem__(u"新しい行の数", 4))
        self._red(lambda R: R["ai200"][u"集計"][u"全体"][u"C-5 数の claim"].__setitem__("P29E", 1))
        self._red(lambda R: R["ai200"][u"集計"][u"全体"][u"C-6 新しい行の state"][u"state"].__setitem__("GROUNDED", 0))
        self._red(lambda R: R["ai200"][u"本"][0][u"既存の行"][u"変わった行の内訳"].__setitem__(NF.SAME_SENTENCE_NEW, 0))
        self._red(lambda R: R["ai200"][u"本"][1][u"旗が偽の byte 一致"].__setitem__(u"一致", True))
        self._red(lambda R: R["inject"][u"行"][0]["P29E"].__setitem__(u"結果", TUNE.LABEL_PASS))
        self._red(lambda R: R["inject"][u"集計"]["T1_VALUE"]["P29E"][u"全体"].__setitem__(u"注入の行", 9))
        self._red(lambda R: R["inject"][u"行"][1].__setitem__("r", 0.2))
        self._red(lambda R: R["inject"][u"型"].__setitem__(u"土台", u"無改変の文で 4 profile 全部が GROUNDED の claim"))
        self._red(lambda R: R["regress97"][u"書類"][1][u"動いた行と増えた行"]["P29E 対 P28E"].__setitem__(u"増えた行", 5))
        self._red(lambda R: R["regress97"][u"集計"][u"C-3 動いた既存の行"].__setitem__("P29E 対 P28E", 0))
        self._red(lambda R: R["regress97"][u"書類"][0][u"出力の sha256(engine の欄を除く)"].__setitem__("P28E", "5" * 64))
        self._red(lambda R: R["shapes"][u"群"][u"AI の文 F1"].__setitem__(u"円族の候補", 99))
        self._red(lambda R: R["shapes"][u"群"][u"AI の文 F1"][u"読み 11_04"].__setitem__(u"読まない", 1))
        self._red(lambda R: R["shapes"][u"群"][u"AI の文 F1"][u"11_04 でも読まない形"].__setitem__(u"N円", 1))

    def test_g_2b_a_consistently_edited_book_still_breaks_the_invariants(self):
        u"""本を直してから集計も作り直しても(集計との食い違いでは見つからない)、本の中の欄の間の関係で赤になる。"""
        def reagg(R):
            R["ai200"][u"集計"] = norm(NF.aggregate(R["ai200"][u"本"]))
        for mutate in (lambda b: b[u"数の claim の数"].__setitem__("P29E", 99), lambda b: b[u"数の claim の数"].__setitem__("P28E", 99), lambda b: b.__setitem__(u"新しい行の数", 9),
                       lambda b: b[u"既存の行"].__setitem__(u"行の数", 9), lambda b: b[u"新しい行の state"].__setitem__("GROUNDED", 9),
                       lambda b: b.__setitem__(u"置き換えの行の数", 9), lambda b: b[u"既存の行"].__setitem__(u"変わった行", 5),
                       lambda b: b[u"旗が偽の byte 一致"].__setitem__(u"一致", not b[u"旗が偽の byte 一致"][u"一致"]),
                       lambda b: b[u"O が決めた行"].__setitem__("P29E", 9), lambda b: b[u"対応"].__setitem__("P29E-O", False)):
            R = copy.deepcopy(self.R)
            mutate(R["ai200"][u"本"][0])
            reagg(R)
            self.assertNotEqual([], record_problems(R, full=False))
        R = copy.deepcopy(self.R)
        reagg(R)
        self.assertEqual([], record_problems(R, full=False))

    def test_g_2d_rounding_and_no_new_row_fields_are_checked(self):
        u"""足した欄(書類の丸め方・同じ文に新しい行が無いのに変わった既存の行)を直して集計も作り直しても、欄の間の関係と形で赤になる。"""
        def reagg(R):
            R["ai200"][u"集計"] = norm(NF.aggregate(R["ai200"][u"本"]))

        def drop_item(b):
            b[u"同じ文に新しい行が無いのに変わった既存の行"].pop()

        def bad_item(b):
            b[u"同じ文に新しい行が無いのに変わった既存の行"][0][0] = u"text"

        def shift_pos(b):
            b[u"同じ文に新しい行が無いのに変わった既存の行"][0][2] += 1

        def swap_state(b):
            b[u"同じ文に新しい行が無いのに変わった既存の行"][0][3] = "UNVERIFIABLE"
        for mutate in (drop_item, bad_item, shift_pos, swap_state,
                       lambda b: b.__setitem__(u"丸め方の決定が P28E と P29E で違う", not b[u"丸め方の決定が P28E と P29E で違う"]),
                       lambda b: b[u"書類の丸め方"]["P28E"].__setitem__(u"決定", "round"),
                       lambda b: b[u"書類の丸め方"]["P29E"].__setitem__(u"決定", "floor"),
                       lambda b: b[u"書類の丸め方"]["P29E"].__setitem__(u"両方", -1),
                       lambda b: b[u"書類の丸め方"]["P29E"].pop(u"両方"),
                       lambda b: b[u"書類の丸め方"].pop("P28E")):
            R = copy.deepcopy(self.R)
            mutate(R["ai200"][u"本"][1])
            try:
                reagg(R)
            except Exception:                                   # noqa: BLE001  集計を作れない形も赤(record_problems が例外を問題に数える)
                pass
            self.assertNotEqual([], record_problems(R, full=False))
        # 集計の K-2 の外れの説明だけを直す
        R = copy.deepcopy(self.R)
        R["ai200"][u"集計"][u"全体"][u"K-2 の外れの説明"][u"うち丸め方の決定が P28E と P29E で違う本に在る行"] = 0
        self.assertNotEqual([], record_problems(R, full=False))

    def test_g_8b_the_k2_explanation_counts_only_rows_in_books_whose_rounding_decision_differs(self):
        b1, b2 = copy.deepcopy(self.R["ai200"][u"本"])
        b1[u"同じ文に新しい行が無いのに変わった既存の行"] = [[u"num", 9, 9, "GROUNDED", "VALUE_MISMATCH", None, None], [u"num", 9, 10, "GROUNDED", "VALUE_MISMATCH", None, None]]
        E = NF.aggregate([b1, b2])[u"全体"][u"K-2 の外れの説明"]                          # b1 は決定が同じ本(2 行)・b2 は違う本(1 行)
        self.assertEqual({u"同じ文に新しい行が無いのに変わった既存の行": 3, u"うち丸め方の決定が P28E と P29E で違う本に在る行": 1, u"丸め方の決定が P28E と P29E で違う本": 1,
                          u"同じ文に新しい行が無いのに変わった既存の行がある本": 2}, dict(E))

    def test_g_2f_the_inject_limit_text_and_unlinked_count_are_pinned(self):
        for mutate in (lambda r: r.__setitem__(u"限界", [u"他の限界", LIMIT_WRONG + u"、その行の P28E の欄は対応なし"]),            # 元の逆の字
                       lambda r: r.__setitem__(u"限界", [u"他の限界"]),
                       lambda r: r.pop(u"限界"),
                       lambda r: r.__setitem__(u"限界", [LIMIT_PIN, u"新しく読めた数も土台に入る"]),
                       lambda r: r[u"P28E に対応なしの行の数"].__setitem__(u"全体", 0),
                       lambda r: r[u"P28E に対応なしの行の数"].__setitem__("T1_VALUE", 1),
                       lambda r: r.pop(u"P28E に対応なしの行の数")):
            R = copy.deepcopy(self.R)
            mutate(R["inject"])
            self.assertNotEqual([], record_problems(R, full=False))

    def test_g_2e_inject_base_fields_are_checked(self):
        for mutate in (lambda r: r[u"行"][0].__setitem__(u"P28E の土台に対応", False),                                  # 対応ありの行を対応なしに(P28E の欄が対応なしでない)
                       lambda r: r[u"行"][2].__setitem__(u"P28E の土台に対応", True) or r.__setitem__(u"注入の行の数", len(r[u"行"])),
                       lambda r: r[u"行"][2].__setitem__(u"P28E の土台に対応", u"いいえ"),
                       lambda r: r[NF.COMPARE_KEY]["T8_REL"]["P28E"][u"全体"].__setitem__(u"注入の行", 9),
                       lambda r: r.pop(NF.COMPARE_KEY),
                       lambda r: r[u"行"][2]["P28E"].__setitem__(u"結果", TUNE.LABEL_PASS)):
            R = copy.deepcopy(self.R)
            mutate(R["inject"])
            self.assertNotEqual([], record_problems(R, full=False))

    def test_g_2c_inject_cap_and_shape_sums_are_checked_on_their_own(self):
        R = copy.deepcopy(self.R)
        row = R["inject"][u"行"][0]
        R["inject"][u"行"] = [dict(row, id=u"x-%d" % i) for i in range(RUN.INJECT_CAP + 1)]
        R["inject"][u"注入の行の数"] = len(R["inject"][u"行"])
        with Patch() as pt:
            pt.set(RUN, "PROFILES", NF.INJECT_PROFILES)
            R["inject"][u"集計"] = norm(RUN.inject_summary(R["inject"][u"行"]))
        self.assertTrue(any(u"上限" in x for x in inject_problems(R["inject"], full=False)))
        R2 = copy.deepcopy(self.R)
        g = R2["shapes"][u"群"][u"AI の文 F1"]
        g[u"円族の候補"] += 1
        for r in SH.READERS:
            g[u"読み %s" % r][SH.KIND_JA["full"]] += 1
        self.assertTrue(any(u"形の候補の和" in x for x in shapes_problems(R2["shapes"], full=False)))
        R3 = copy.deepcopy(self.R)
        g3 = R3["shapes"][u"群"][u"AI の文 F1"]
        first = next(iter(g3[u"形"].values()))
        first[u"候補"] += 1
        self.assertTrue(any(u"読みの和" in x for x in shapes_problems(R3["shapes"], full=False)))

    def test_g_3_a_forbidden_key_or_a_key_or_a_company_name_turns_it_red(self):
        for key in (u"span", u"value", u"recomputed", u"文", u"sentence", u"数", u"理由"):
            self._red(lambda R, key=key: R["ai200"][u"本"][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["inject"][u"行"][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["regress97"][u"書類"][0].__setitem__(key, 1))
            self._red(lambda R, key=key: R["shapes"][u"群"].__setitem__(key, {}))
        self._red(lambda R: R["shapes"].__setitem__(u"メモ", u"株式会社テスト"))
        self._red(lambda R: R["ai200"].__setitem__(u"メモ", u"sk-" + u"a" * 20))
        self._red(lambda R: R["regress97"].__setitem__(u"key_leaks", [u"鍵の形"]))

    def test_g_4_one_character_of_the_fingerprint_or_the_script_sha_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][FP_KEY[k]].__setitem__("adapter_xbrl_py_sha256", R[k][FP_KEY[k]]["adapter_xbrl_py_sha256"][:-1] + ("0" if R[k][FP_KEY[k]]["adapter_xbrl_py_sha256"][-1] != "0" else "1")))
            self._red(lambda R, k=k: R[k][FP_KEY[k]].__setitem__("core_py_sha256", "f" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"この script の sha256", "e" * 64))
            self._red(lambda R, k=k: R[k].__setitem__(u"封の commit", u"0000000"))

    def test_g_5_a_changed_cache_turns_it_red(self):
        for k in REC_REL:
            self._red(lambda R, k=k: R[k][u"cache の前後"].__setitem__(u"変化なし", False))
            self._red(lambda R, k=k: R[k][u"cache の前後"][u"後"]["edinet"].__setitem__(u"件数", 4))

    def test_g_6_the_document_follows_the_records_and_the_seal(self):
        doc = sample_doc(self.R, self.seal)
        lines = doc.split(u"\n")
        i = lines.index(u"<!-- 門:start pred -->") + 3                  # 表の 1 行目(C-1)
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
        # 記録を 1 つ変えると、変える前の文書が赤
        R2 = copy.deepcopy(self.R)
        R2["regress97"][u"集計"][u"C-4 増えた claim"]["P29E"] = 9
        R2["ai200"][u"集計"][u"全体"][u"C-5 数の claim"][u"P29E − P28E"] += 1
        self.assertNotEqual([], doc_problems(doc, R2, self.seal))
        # 封の予測の 1 字
        mutated_seal = self.seal.replace("+5,000〜+6,300", "+5,000〜+6,301", 1)
        self.assertNotEqual(mutated_seal, self.seal)
        self.assertNotEqual([], doc_problems(doc, self.R, mutated_seal))
        # 知らない表・消えた表
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
        T = R97.summarize_docs(self.R["regress97"][u"書類"])
        self.assertEqual({"P29 対 P28": 2, "P29E 対 P28E": 2}, T[u"C-3 動いた既存の行"])
        self.assertEqual({"P29": 1, "P29E": 1}, T[u"C-4 増えた claim"])
        self.assertEqual({"P29": 1, "P29E": 1}, T[u"増えた claim のある書類"])
        self.assertEqual({"P22": 2, "P26": 2, "P27": 2, "P27E": 2, "P28": 2, "P28E": 2}, dict((p, v[u"byte が同じ書類"]) for p, v in T[u"C-2 旗が偽の profile の byte 一致"].items()))
        A = NF.aggregate(self.R["ai200"][u"本"])[u"全体"]
        self.assertEqual({"P28E": 5, "P29E": 8, "P29E-O": 8, u"P29E − P28E": 3}, dict(A[u"C-5 数の claim"]))
        self.assertEqual({u"行の数": 4, u"置き換えの行": 1, u"P28E にあって P29E に無い行": 1, u"そのうち新しい行と範囲が交わらない行": 0}, dict(A[u"新しい行"]))
        self.assertEqual((4, 25.0), (A[u"C-6 新しい行の state"][u"分母"], A[u"C-6 新しい行の state"][u"GROUNDED の率"]))
        self.assertEqual({u"既存の行": 4, u"変わった行": 3, NF.SAME_SENTENCE_NEW: 2, NF.SAME_SENTENCE_NONE: 1, u"うち state が変わった行": 3}, dict(A[u"C-7 既存の行"]))
        self.assertEqual({u"同じ文に新しい行が無いのに変わった既存の行": 1, u"うち丸め方の決定が P28E と P29E で違う本に在る行": 1, u"丸め方の決定が P28E と P29E で違う本": 1,
                          u"同じ文に新しい行が無いのに変わった既存の行がある本": 1}, dict(A[u"K-2 の外れの説明"]))
        b2 = self.R["ai200"][u"本"][1]
        self.assertEqual([[u"num", 3, 1, "GROUNDED", "VALUE_MISMATCH", None, "x"]], b2[u"同じ文に新しい行が無いのに変わった既存の行"])
        self.assertEqual("truncate", b2[u"書類の丸め方"]["P28E"][u"決定"])
        self.assertEqual({"P28E": 2, "P29E": 1}, dict(A[u"C-8 O の形の行"]))
        self.assertEqual({"P28E": 0, "P29E": 1}, dict(A[u"C-9 O が決めた行"]))
        self.assertEqual({u"GROUNDED でなくなった行": 0, u"O が GROUNDED にした行": 1, u"数の claim の鍵が違う本": 0}, dict(A[u"C-10 P29E 対 P29E-O"]))
        self.assertEqual({u"一致した本": 1, u"本": 2}, dict(A[u"C-1 旗が偽の byte 一致"]))

    def test_g_9_analyse_book_pairs_by_position_not_by_id(self):
        ok = dict((p, True) for p in NF.NOW_PROFILES)
        p = prow
        # P28E の行 (0, 5) は P29E で位置が同じなら同じ行(id は持たない)。(0, 6) は範囲が交わるので置き換え。(1, 0) は交わらない新しい行
        a = {(0, 5): p(10, "GROUNDED")}
        b = {(0, 6): p(12, "GROUNDED"), (1, 0): p(3, "GROUNDED")}
        rec = NF.analyse_book({"P28E": a, "P29E": b, "P29E-O": b}, ok)
        self.assertEqual((2, 1, 1, 0), (rec[u"新しい行の数"], rec[u"置き換えの行の数"], rec[u"P28E にあって P29E に無い行"], rec[u"そのうち新しい行と範囲が交わらない行"]))
        c = {(0, 5): p(10, "GROUNDED")}
        d = {(0, 20): p(30, "GROUNDED")}                          # P28E の行 (0, 5) が消え、交わらない新しい行
        rec2 = NF.analyse_book({"P28E": c, "P29E": d, "P29E-O": d}, ok)
        self.assertEqual((1, 0, 1, 1), (rec2[u"新しい行の数"], rec2[u"置き換えの行の数"], rec2[u"P28E にあって P29E に無い行"], rec2[u"そのうち新しい行と範囲が交わらない行"]))
        e = {(0, 5): p(10, "GROUNDED"), (4, 1): p(6, "GROUNDED")}
        f = {(0, 5): p(10, "VALUE_MISMATCH"), (4, 1): p(6, "GROUNDED"), (0, 40): p(44, "GROUNDED")}       # 同じ文に新しい行が在る行 (0, 5) が変わる
        rec3 = NF.analyse_book({"P28E": e, "P29E": f, "P29E-O": f}, ok)
        self.assertEqual({NF.SAME_SENTENCE_NEW: 1, NF.SAME_SENTENCE_NONE: 0}, rec3[u"既存の行"][u"変わった行の内訳"])
        g = {(0, 5): p(10, "GROUNDED"), (4, 1): p(6, "VALUE_MISMATCH"), (0, 40): p(44, "GROUNDED")}       # 新しい行が無い文 (4, 1) が変わる
        rec4 = NF.analyse_book({"P28E": e, "P29E": g, "P29E-O": g}, ok)
        self.assertEqual({NF.SAME_SENTENCE_NEW: 0, NF.SAME_SENTENCE_NONE: 1}, rec4[u"既存の行"][u"変わった行の内訳"])


# ================================================================ 既知の答えのある小さい入力(位置の対応・97 書類の行・形の数)
class KnownAnswerTest(unittest.TestCase):
    def test_k_1_ranges_that_only_touch_are_not_a_replacement(self):
        ok = dict((p, True) for p in NF.NOW_PROFILES)
        a = {(0, 5): prow(10, "GROUNDED")}                         # P28E: [5, 10)
        touch = {(0, 10): prow(14, "GROUNDED")}                    # P29E: [10, 14) ― 接するだけで交わらない
        rec = NF.analyse_book({"P28E": a, "P29E": touch, "P29E-O": touch}, ok)
        self.assertEqual((0, 1, 1), (rec[u"置き換えの行の数"], rec[u"新しい行の数"], rec[u"そのうち新しい行と範囲が交わらない行"]))
        cross = {(0, 9): prow(14, "GROUNDED")}                     # [9, 14) ― 1 字交わる
        rec2 = NF.analyse_book({"P28E": a, "P29E": cross, "P29E-O": cross}, ok)
        self.assertEqual((1, 1, 0), (rec2[u"置き換えの行の数"], rec2[u"新しい行の数"], rec2[u"そのうち新しい行と範囲が交わらない行"]))
        other_sentence = {(1, 6): prow(11, "GROUNDED")}            # 位置が重なっても別の文なら置き換えでない
        rec3 = NF.analyse_book({"P28E": a, "P29E": other_sentence, "P29E-O": other_sentence}, ok)
        self.assertEqual(0, rec3[u"置き換えの行の数"])

    def test_k_5_a_row_that_changes_only_in_reason_or_pointers_counts_as_changed(self):
        ok = dict((p, True) for p in NF.NOW_PROFILES)
        a = {(0, 5): prow(10, "POINTER_NOT_FOUND", "no_element", ["a@当期"]), (0, 40): prow(50, "GROUNDED", None, ["a@当期"])}
        b = {(0, 5): prow(10, "POINTER_NOT_FOUND", "no_same_value", ["a@当期"]), (0, 40): prow(50, "GROUNDED", None, ["b@当期"]), (0, 70): prow(80, "GROUNDED")}
        rec = NF.analyse_book({"P28E": a, "P29E": b, "P29E-O": b}, ok)
        ex = rec[u"既存の行"]
        self.assertEqual((2, 0), (ex[u"変わった行"], ex[u"変わった行のうち state が変わった行"]))
        self.assertEqual([[0, 5, "POINTER_NOT_FOUND", "POINTER_NOT_FOUND", False, True, True], [0, 40, "GROUNDED", "GROUNDED", True, False, True]], ex[u"変わった行の中身"])

    def test_k_6_the_script_and_the_history_agree_on_the_engine_link(self):
        link = norm(R97.engine_link())
        self.assertEqual(norm(link_at_history()), link)
        self.assertEqual(["adapters/xbrl/extract.py", "adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py"], link[u"engine の変更 file"])
        self.assertEqual(0, link[u"engine の削除の行数"])

    def test_k_7_engine_link_counts_modified_files_apart_from_added_ones(self):
        P = PREFIX
        num = ["30\t0\t%sadapters/xbrl/extract.py" % P, "2\t0\t%sadapters/xbrl/recipes.py" % P]
        tests = ["M\t%stests/a.py" % P, "M\t%stests/b.py" % P, "A\t%stests/c.py" % P, "D\t%stests/d.py" % P]
        with Patch() as pt:
            pt.set(R97, "engine_commits", lambda: ("s" * 40, "e" * 40, num, tests))
            link = R97.engine_link()
        self.assertEqual((2, 1, 1, 4), (link[u"直した file(M)"], link[u"新しい file(A)"], link[u"消した file(D)"], link[u"tests の変更 file"]))
        self.assertEqual((32, 0), (link[u"engine の挿入の行数"], link[u"engine の削除の行数"]))

    def test_k_8_the_prediction_table_rows_have_a_fixed_shape(self):
        seal = read(SEAL_REL)
        P = NF.seal_pred_rows(seal)
        J = NF.build_J(sample_agg_records(), seal)
        lines = NF.render_pred(J, seal).split(u"\n")
        self.assertEqual(u"| # | 欄 | 予測 | 測った値 | 判定 |", lines[0])
        by = dict((ln.split(u" | ")[0][2:], ln) for ln in lines[2:])
        self.assertEqual(u"| C-5 | " + P["C-5"][0] + u" | +5,000〜+6,300 | P28E 1,000・P29E 6,600・差 5,600 | **当たり** |", by["C-5"])
        self.assertEqual(u"| C-1 | " + P["C-1"][0] + u" | 200 / 200 | 一致した本 200・本 200 | **当たり** |", by["C-1"])
        for ln in lines[2:]:
            self.assertEqual(5, len(ln.strip(u"|").split(u" | ")), ln)
            self.assertNotIn(u"(", ln.split(u" | ")[2])                             # 予測の欄は封の字の括弧の前まで
        j = NF.render_judge(J, seal).split(u"\n")
        self.assertEqual(u"| # | 基準 | 測った値 | 判定 |", j[0])
        self.assertIn(u"採用の判定(K-1〜K-4 を全部満たす): **採用**", j[-1])

    def test_k_2_o_effect_direction(self):
        ok = dict((p, True) for p in NF.NOW_PROFILES)
        base = {(0, 1): prow(5, "GROUNDED"), (0, 9): prow(12, "POINTER_NOT_FOUND")}
        with_o = {(0, 1): prow(5, "VALUE_MISMATCH"), (0, 9): prow(12, "GROUNDED")}          # P29E: (0, 1) が GROUNDED でなくなり (0, 9) が GROUNDED になる
        rec = NF.analyse_book({"P28E": base, "P29E": with_o, "P29E-O": base}, ok)
        self.assertEqual((1, 1), (rec[u"P29E 対 P29E-O"][u"GROUNDED でなくなった行"], rec[u"P29E 対 P29E-O"][u"O が GROUNDED にした行"]))
        missing = {(0, 9): prow(12, "GROUNDED")}                  # P29E に鍵が無い GROUNDED の行(P29E−O の (0, 1))は GROUNDED でなくなった行に数える
        rec2 = NF.analyse_book({"P28E": base, "P29E": missing, "P29E-O": base}, ok)
        self.assertEqual(1, rec2[u"P29E 対 P29E-O"][u"GROUNDED でなくなった行"])
        self.assertFalse(rec2[u"P29E 対 P29E-O"][u"数の claim の鍵が同じ"])

    def test_k_3_pair_moves_and_doc_rows(self):
        def keyed(rows):
            return collections.OrderedDict(rows)
        k1, k2, k3 = ("num", 0, 5, 0), ("num", 0, 9, 0), ("num", 1, 2, 0)
        t1, t2 = ("text", 0, 3, 0), ("text", 2, 2, 0)
        res = {u"doc": "DOC9", u"fresh": False, u"zip の sha256": "6" * 64, u"profiles": {}, u"keyed": {
            "P28": keyed([(k1, ("GROUNDED", None, ("a",))), (k2, ("POINTER_NOT_FOUND", "x", ())), (t1, ("UNVERIFIABLE", "t", ()))]),
            "P29": keyed([(k1, ("GROUNDED", None, ("a",))), (k2, ("GROUNDED", None, ("b",))), (k3, ("VALUE_MISMATCH", None, ())), (t1, ("UNVERIFIABLE", "t", ())), (t2, ("UNVERIFIABLE", "t", ()))]),
            "P28E": keyed([(k1, ("GROUNDED", None, ("a",))), (k2, ("GROUNDED", None, ("a",)))]),
            "P29E": keyed([(k1, ("GROUNDED", None, ("a",))), (k2, ("GROUNDED", None, ("a",)))])}}
        mv, add, gone = R97.pair_moves(res, "P28", "P29")
        self.assertEqual(([k2], [k3, t2], []), (mv, add, gone))                              # 増えた行は種類(num・text)を問わない
        self.assertEqual(([], [], []), R97.pair_moves(res, "P28E", "P29E"))
        rev = dict(res, keyed={"P28": res["keyed"]["P29"], "P29": res["keyed"]["P28"]})                  # 向きを逆にすると 増えた行 と 消えた行 が入れ替わる
        self.assertEqual(([k2], [], [k3, t2]), R97.pair_moves(rev, "P28", "P29"))
        # 動いた(pointers だけ違う)行は state が同じでも数える
        res2 = dict(res, keyed=dict(res["keyed"], P29E=keyed([(k1, ("GROUNDED", None, ("a",))), (k2, ("GROUNDED", None, ("c",)))])))
        self.assertEqual([k2], R97.pair_moves(res2, "P28E", "P29E")[0])
        # 行の形
        rows = [("N001", "GROUNDED", None, ())] * 3
        res["profiles"] = dict((p, {u"sha256": hashlib.sha256(p.encode()).hexdigest(), u"rows": rows}) for p in R97.NOW_PROFILES)
        prev_by = {"DOC9": {u"出力の sha256(engine の欄を除く)": dict((p, hashlib.sha256(p.encode()).hexdigest()) for p in R97.BASE_PROFILES)}}
        d = R97.doc_rows([res], prev_by)[0]
        self.assertEqual("DOC9", d[u"docID"])
        m = d[u"動いた行と増えた行"]["P29 対 P28"]
        self.assertEqual([["num", 0, 9, 0, "POINTER_NOT_FOUND", "GROUNDED", "x", None, True]], m[u"動いた既存の行"])
        self.assertEqual((2, 0), (m[u"増えた行"], m[u"消えた行"]))
        self.assertEqual({"GROUNDED": 0, "VALUE_MISMATCH": 1, "UNVERIFIABLE": 1, "POINTER_NOT_FOUND": 0}, dict(m[u"増えた行の state"]))
        self.assertEqual(0, d[u"動いた行と増えた行"]["P29E 対 P28E"][u"増えた行"])
        self.assertEqual(dict((p, 3) for p in R97.NOW_PROFILES), dict(d[u"claims"]))
        self.assertEqual(R97.summarize_docs([d])[u"C-2 旗が偽の profile の byte 一致"]["P28E"][u"byte が同じ書類"], 1)

    def test_k_4_shape_counts_known_sentences(self):
        def count(sents):
            acc = SH.new_acc()
            SH.count_sentences(sents, acc)
            return acc
        acc = count([u"売上高は12億3,456万円でした。", u"利益は1万2,345円でした。", u"費用は12億円でした。", u"粗利は1,234百万円でした。"])
        self.assertEqual(3, acc["cand"])                                                       # 1,234百万円 は円族の候補の正規表現に当たらない
        self.assertEqual({"full": 1, "part": 1, "none": 1}, {k: acc["kind"]["10_27"].get(k, 0) for k in ("full", "part", "none")})
        self.assertEqual({"full": 3, "part": 0, "none": 0}, {k: acc["kind"]["11_04"].get(k, 0) for k in ("full", "part", "none")})
        self.assertEqual({"N億N,N万円", "N万N,N円", "N億円"}, set(acc["shape"]))
        self.assertEqual({"full": 0, "part": 1, "none": 0}, {k: acc["shape"]["N万N,N円"]["kind"]["10_27"].get(k, 0) for k in ("full", "part", "none")})
        # 「その他」の直後。桁を食う正規表現の語の部分(数の途中で終わる)でも数の頭から数える
        o = count([u"その他の費用は1,234万円でした。", u"その他の費用1,234万円でした。", u"その他は5億円、その他の収益は2.5%でした。", u"その他、費用は12億円でした。"])["other"]
        self.assertEqual((4, 3), (o["pos"], o["yen"]))                                           # 2 文目の 2 つ目の「その他」は 2.5% (円でない)・4 文目は「その他、」の後に数が続かない
        self.assertEqual({"none": 2, "full": 1}, {k: v for k, v in o["kind"]["10_27"].items() if v})
        self.assertEqual({"full": 3}, {k: v for k, v in o["kind"]["11_04"].items() if v})
        # 符号つき
        o2 = count([u"その他△1,234万円でした。", u"その他の費用は△1,234万円でした。"])["other"]                # 語の部分が無いと符号は m.end() の次の字になる
        self.assertEqual((2, 2), (o2["pos"], o2["yen"]))
        g = SH.group_json(acc, u"本")
        self.assertEqual({}, g[u"11_04 でも読まない形"])                                           # N の読みでは読まない形が残らない
        self.assertEqual({"N億N,N万円": 1}, SH.left(acc["shape"], "10_27", "none"))
        self.assertEqual({"N万N,N円": 1}, SH.left(acc["shape"], "10_27", "part"))


# ================================================================ judge_book・profile_view を小さい合成の入力で通す(engine・zip・文は偽。通信なし)
class JudgeBookFlowTest(unittest.TestCase):
    u"""``verify_document``・``build_raw_claims``・``_numbers_of``・``sentence_list`` と zip / 文の読み込みを偽に替え、profile_view と judge_book の本体を 1 回通す。
    合成の入力(P28E は数の claim 2・P29E は 3 = 新しい行 1、P29E の N002 は O が決めて GROUNDED、丸め方は P28E が round・P29E が truncate)で、記録の欄が既知の答えになる。"""
    G, V_, P = "GROUNDED", "VALUE_MISMATCH", "POINTER_NOT_FOUND"
    PTR = "xbrl:jppfs_cor:Sales@CurrentYearDuration"
    # profile ごとの数の claim: (id, 文の番号, 位置, state, reason, O の欄 or None)
    CLAIMS = {
        "P28E": [("N001", 0, 4, "GROUNDED", None, None), ("N002", 0, 20, "POINTER_NOT_FOUND", "no_same_value", {u"前期": None, u"候補": 1, u"決まった": False})],
        "P29E": [("N001", 0, 4, "GROUNDED", None, None), ("N002", 0, 20, "GROUNDED", None, {u"前期": None, u"候補": 1, u"決まった": True}), ("N003", 0, 40, "VALUE_MISMATCH", None, None)],
        "P29E-O": [("N001", 0, 4, "GROUNDED", None, None), ("N002", 0, 20, "POINTER_NOT_FOUND", "no_same_value", None), ("N003", 0, 40, "VALUE_MISMATCH", None, None)]}
    EVIDENCE = {"P28E": [(-1.0, 10)], "P29E": [(9.0, 10), (8.0, 10)], "P29E-O": [(9.0, 10), (8.0, 10)]}

    def fakes(self, pt, prior_row_ok=True):
        from adapters.xbrl import vocabulary as V
        claims = self.CLAIMS

        def verify(zb, pname, text):
            cl = [{"id": i, "kind": "num", "state": st, "reason": rs, "pointers": [self.PTR] if st == self.G else []} for (i, _s, _p, st, rs, _o) in claims[pname]]
            return {"claims": cl, "document": {"states": dict((k, sum(1 for c in cl if c["state"] == k)) for k in NF.STATES)}}

        def raw(zm, prof):
            V.decide_rounding(self.EVIDENCE[prof.name])                                # engine と同じ呼び方(包みが写す)
            return ([{"id": i, "sentence": si, "pos": pos, "other_subject_2026_11_02": o} for (i, si, pos, _st, _rs, o) in claims[prof.name]], [])

        def numbers_of(prof, sentence):
            return [(pos, pos + 6, 1.0, u"円", 1.0) for (_i, _si, pos, _st, _rs, _o) in claims[prof.name]]
        pt.set(NF.VD, "verify_document", verify)
        pt.set(NF.R, "build_raw_claims", raw)
        pt.set(NF.R, "_numbers_of", numbers_of)
        pt.set(NF.RUN, "sentence_list", lambda zm, prof: [u"x" * 60])
        pt.set(NF.GEN, "read_zip", lambda row, caches=None: b"zip")
        pt.set(NF.RUN, "read_text", lambda name, item, d: u"text")
        pt.set(NF.PR, "build_modified_zip", lambda zb, text: (b"zm", None, None))
        old = {u"行": [["N001", "num"]], u"4 state": {"P27": {}}, u"claim の数": 3}
        pt.set(NF.RUN, "judge_text", lambda zb, text: (copy.deepcopy(old), []))
        return old

    def job(self, prior):
        item = {u"docID": "DOC1", u"form": "F1", u"model": "m1", u"writer": "W1", u"sha256": "0" * 64}
        return ("aiforms", "DOC1_F1_m1", item, {}, "d", {}, prior)

    def test_j_1_profile_view_keys_rows_by_position_and_copies_the_rounding_and_o_cell(self):
        from adapters.xbrl import vocabulary as V
        with Patch() as pt:
            self.fakes(pt)
            rows, ok, states, rnd = NF.profile_view(b"zip", u"text", b"zm", "P29E")
        self.assertTrue(ok)
        self.assertEqual([(0, 4), (0, 20), (0, 40)], list(rows))
        self.assertEqual({"b": 10, "state": "GROUNDED", "reason": None, "pointers": ["jppfs_cor:Sales@当期"], "o": None}, rows[(0, 4)])
        self.assertEqual([None, True], [rows[(0, 20)]["o"][0], rows[(0, 20)]["o"][2]])                 # O の欄 [前期, 候補, 決まった]
        self.assertEqual({u"決定": "truncate", u"round-only": 0, u"truncate-only": 2, u"両方": 0}, dict(rnd))
        self.assertEqual({"GROUNDED": 2, "VALUE_MISMATCH": 1, "UNVERIFIABLE": 0, "POINTER_NOT_FOUND": 0}, states)
        self.assertEqual(V.decide_rounding.__name__, "decide_rounding")                                # 包みが戻っている

    def test_j_2_judge_book_assembles_the_book_record_from_the_three_profiles(self):
        from adapters.xbrl import vocabulary as V
        with Patch() as pt:
            old = self.fakes(pt)
            prior = copy.deepcopy(old)
            rec = NF.judge_book(self.job(prior))
        self.assertNotIn("P29E-O", V.PROFILES)                                                         # with の外では登録が戻っている
        self.assertEqual({"P28E": 2, "P29E": 3, "P29E-O": 3}, dict(rec[u"数の claim の数"]))
        self.assertEqual((1, 0, 0), (rec[u"新しい行の数"], rec[u"置き換えの行の数"], rec[u"P28E にあって P29E に無い行"]))
        self.assertEqual({"GROUNDED": 0, "VALUE_MISMATCH": 1, "UNVERIFIABLE": 0, "POINTER_NOT_FOUND": 0}, dict(rec[u"新しい行の state"]))
        self.assertEqual({"P28E": 1, "P29E": 1}, dict(rec[u"O の形の行"]))                              # O の形の行 = O の欄が null でない行
        self.assertEqual({"P28E": 0, "P29E": 1}, dict(rec[u"O が決めた行"]))
        self.assertEqual(1, rec[u"P29E 対 P29E-O"][u"O が GROUNDED にした行"])
        self.assertEqual("round", rec[u"書類の丸め方"]["P28E"][u"決定"])
        self.assertEqual("truncate", rec[u"書類の丸め方"]["P29E"][u"決定"])
        self.assertTrue(rec[u"丸め方の決定が P28E と P29E で違う"])
        self.assertEqual({u"行": True, u"4 state": True, u"claim の数": True, u"一致": True}, dict(rec[u"旗が偽の byte 一致"]))
        self.assertEqual(1, rec[u"既存の行"][u"変わった行"])                                              # N002 は P → G、同じ文に新しい行 N003 が在る
        self.assertEqual(1, rec[u"既存の行"][u"変わった行の内訳"][NF.SAME_SENTENCE_NEW])
        self.assertEqual([], book_problems(rec))

    def test_j_3_the_flag_off_byte_match_is_compared_for_each_of_the_three_fields(self):
        for field, alter in ((u"行", lambda d: d.__setitem__(u"行", [["N999", "num"]])), (u"4 state", lambda d: d.__setitem__(u"4 state", {"P27": {"x": 1}})),
                             (u"claim の数", lambda d: d.__setitem__(u"claim の数", 4))):
            with Patch() as pt:
                old = self.fakes(pt)
                prior = copy.deepcopy(old)
                alter(prior)
                rec = NF.judge_book(self.job(prior))
            same = rec[u"旗が偽の byte 一致"]
            self.assertFalse(same[field], field)
            self.assertFalse(same[u"一致"], field)
            self.assertEqual(2, sum(1 for k in (u"行", u"4 state", u"claim の数") if same[k]), field)


# ================================================================ 注入の土台の結び方(profile ごとの claim id)
def fake_claim(cid, state="GROUNDED", value=100.0, span=u"売上高は100億円でした", pointers=("xbrl:a:b",), recomputed=1.0e10):
    return {"id": cid, "value": value, "unit": u"億円", "span": span, "state": state, "pointers": list(pointers), "reason": None, "recomputed": recomputed}


class InjectFlowTest(unittest.TestCase):
    text = u"売上高は100億円でした。\n"

    def tok(self):
        return RUN.N.scan(self.text)[0]

    def test_i_1_the_base_is_the_p29e_grounded_claim_and_p28e_is_paired_by_value_span_unit_not_by_id(self):
        base = {"P28E": [fake_claim("N001")], "P29E": [fake_claim("N005")]}
        st, bc = NF.base_status_n(base, {}, self.tok(), self.text)
        self.assertEqual(NF.LINKED, st)
        self.assertEqual({"P28E": "N001", "P29E": "N005"}, bc["ids"])
        self.assertEqual("N005", bc["id"])                                         # 土台は P29E の claim
        # P28E の claim が GROUNDED でなくても、同じ site の claim なら結ぶ(P28E の欄はその claim の判定)
        st2, bc2 = NF.base_status_n({"P28E": [fake_claim("N001", "UNVERIFIABLE")], "P29E": [fake_claim("N005")]}, {}, self.tok(), self.text)
        self.assertEqual((NF.LINKED, "N001"), (st2, bc2["ids"]["P28E"]))

    def test_i_2_without_a_p28e_claim_the_site_is_still_a_base_with_no_p28e_pairing(self):
        t = self.tok()
        for p28 in ([], [fake_claim("N001", span=u"別の文脈の100億円")], [fake_claim("N001"), fake_claim("N002")]):          # 無い・span が違う・同じ鍵が 2 件
            st, bc = NF.base_status_n({"P28E": p28, "P29E": [fake_claim("N005")]}, {}, t, self.text)
            self.assertEqual(NF.UNLINKED, st)
            self.assertEqual({"P28E": None, "P29E": "N005"}, bc["ids"])

    def test_i_2b_a_site_where_p29e_is_not_grounded_or_has_no_claim_is_not_a_base(self):
        t = self.tok()
        self.assertEqual((u"P29E が GROUNDED でない", None), NF.base_status_n({"P28E": [fake_claim("N001")], "P29E": [fake_claim("N005", "VALUE_MISMATCH")]}, {}, t, self.text))
        self.assertEqual((u"P29E が GROUNDED でない", None), NF.base_status_n({"P28E": [fake_claim("N001")], "P29E": [fake_claim("N005", "UNVERIFIABLE")]}, {}, t, self.text))
        self.assertEqual((u"基準に対応が付かない", None), NF.base_status_n({"P28E": [fake_claim("N001")], "P29E": []}, {}, t, self.text))
        self.assertEqual((u"基準に対応が付かない", None), NF.base_status_n({"P28E": [fake_claim("N001")], "P29E": [fake_claim("N005"), fake_claim("N006")]}, {}, t, self.text))

    def _inject(self, p28_claims):
        tok = self.tok()
        new = 150.0
        inj = {"type": "T1_VALUE", "id": "K-T1-01", "new_value": new, "replacement": RUN.N.render_value(new, tok), "span": [tok.start, tok.end], "detail": {"original_value": tok.value}}
        ids = {"P28E": "N001", "P29E": "N005"}
        calls = []

        def verify(zb, p, t):
            calls.append((p, u"150" in t))
            if u"150" in t:                                    # 改ざんした文: 原本と同じ pointer を名指し、recomputed も原本のまま(= 名指して原本の値を返した)
                return {"claims": [fake_claim(ids[p], "VALUE_MISMATCH", value=150.0, span=u"売上高は150億円でした")]}
            return {"claims": p28_claims if p == "P28E" else [fake_claim(ids[p])]}
        with Patch() as pt:
            pt.set(RUN, "PROFILES", NF.INJECT_PROFILES)
            pt.set(RUN, "base_status4", NF.base_status_n)
            pt.set(NF.IJ, "select", lambda *a, **k: ([inj], {"T1_VALUE": 1}, None, None))
            rows, counts = NF.inject_text_n(b"", self.text, [], "seed", "K", 10, verify)
        return [r for r in rows if r[u"型"] == "T1_VALUE"], counts, calls

    def test_i_3_inject_text_n_classifies_each_profile_against_its_own_base_claim(self):
        t1, counts, _calls = self._inject([fake_claim("N001")])
        self.assertEqual(1, len(t1))
        self.assertEqual("N005", t1[0][u"基準の claim"])                           # 基準の claim は P29E の claim の id
        self.assertTrue(t1[0][u"P28E の土台に対応"])
        for p in NF.INJECT_PROFILES:
            self.assertEqual(TUNE.LABEL_NAMED_ORIGINAL, t1[0][p][u"結果"], p)
        self.assertEqual(1, counts["T1_VALUE"][NF.LINKED])

    def test_i_3b_a_row_without_a_p28e_claim_gets_not_corresponding_for_p28e_and_p28e_is_not_run_on_it(self):
        t1, counts, calls = self._inject([])
        self.assertEqual(1, len(t1))
        self.assertFalse(t1[0][u"P28E の土台に対応"])
        self.assertEqual({u"対応": False, u"結果": TUNE.LABEL_UNMAPPED, u"state": None, u"reason": None}, dict(t1[0]["P28E"]))
        self.assertEqual(TUNE.LABEL_NAMED_ORIGINAL, t1[0]["P29E"][u"結果"])
        self.assertEqual(1, counts["T1_VALUE"][NF.UNLINKED])
        self.assertNotIn(("P28E", True), calls)                                     # 改ざんした文を P28E で判定しない
        rows = [dict(r, form="F1", model="m", writer="W1") for r in t1]                 # 本の欄は inject_job_n が足す
        with Patch() as pt:
            pt.set(RUN, "PROFILES", NF.INJECT_PROFILES)
            full = RUN.inject_summary(rows)
            cmp_ = RUN.inject_summary([r for r in rows if r[u"P28E の土台に対応"]])
            self.assertEqual((full, cmp_), NF.inject_summaries(rows))
            two = rows + [dict(rows[0], **{"id": "x", u"P28E の土台に対応": True, "P28E": dict(rows[0]["P28E"], **{u"対応": True, u"結果": TUNE.LABEL_PASS})})]
            f2, c2 = NF.inject_summaries(two)
            self.assertEqual((2, 1), (f2["T1_VALUE"]["P28E"][u"全体"][u"注入の行"], c2["T1_VALUE"]["P28E"][u"全体"][u"注入の行"]))        # 比較用は P28E に対応が付く site だけ
        self.assertEqual((1, 0), (full["T1_VALUE"]["P28E"][u"全体"][u"対応が付かない"], full["T1_VALUE"]["P28E"][u"全体"][u"対応が付く"]))
        self.assertEqual(0, cmp_["T1_VALUE"]["P28E"][u"全体"][u"注入の行"])

    def test_i_6_capture_rounding_copies_the_engine_return_and_restores_the_function(self):
        from adapters.xbrl import vocabulary as V
        orig = V.decide_rounding
        with NF.capture_rounding() as cap:
            self.assertIsNot(V.decide_rounding, orig)
            self.assertEqual(NF.ROUNDING_NONE, cap.result())                          # 呼ばれなければ決定なし
            got = V.decide_rounding([(-1.0, 10), (9.0, 10), (0.0, 10), (6.0, 10)])    # R = 1(diff < 0)・T = 2(diff > unit / 2)・根拠 4
            self.assertEqual(orig([(-1.0, 10), (9.0, 10), (0.0, 10), (6.0, 10)]), got)
            self.assertEqual({u"決定": "truncate", u"round-only": 1, u"truncate-only": 2, u"両方": 1}, dict(cap.result()))
            V.decide_rounding([(0.0, 10)])
            self.assertEqual({u"決定": V.DOC_ROUNDING_DEFAULT, u"round-only": 0, u"truncate-only": 0, u"両方": 1}, dict(cap.result()))      # 最後の呼び出し(2 周目の決定)
        self.assertIs(V.decide_rounding, orig)

    def test_i_7_run_inject_writes_the_record_with_the_limit_text_the_two_summaries_and_the_unlinked_count(self):
        u"""run_inject の記録の組み立て(土台の字・限界・集計 2 本・対応なしの行の数)を、読み込み・並列・cache を偽にして 1 回通す。"""
        rows = norm(sample_inject()[u"行"])
        item = {u"docID": "DOC1", u"form": "F1", u"model": "m1", u"writer": "W1", u"sha256": "0" * 64}
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d, Patch() as pt:
            pt.set(RUN, "PROFILES", RUN.PROFILES)
            pt.set(RUN, "base_status4", RUN.base_status4)
            pt.set(NF, "load_books", lambda root=ROOT, only=None: [("aiforms", "DOC1_F1_m1", item, {}, {})])
            pt.set(NF, "map_pool", lambda fn, jobs_, procs: [("DOC1_F1_m1", [collections.OrderedDict(r) for r in rows], {})])
            pt.set(NF, "caches_all", lambda: collections.OrderedDict())
            pt.set(GEN, "seed_value", lambda root=ROOT: ("seed", {"seed_file": "x"}))
            out = os.path.join(d, "inject.json")
            rec = NF.run_inject(root=ROOT, procs=1, out=out, say=lambda *a: None, work_root=d)
            with open(out, encoding="utf-8") as fh:
                disk = json.load(fh)
        self.assertEqual(norm(rec), disk)
        self.assertEqual(BASE_WORD_PIN, disk[u"型"][u"土台"])
        self.assertIn(LIMIT_PIN, disk[u"限界"])
        self.assertFalse(any(LIMIT_WRONG in x for x in disk[u"限界"]))
        self.assertEqual({u"全体": 1, "T1_VALUE": 0, "T8_REL": 1}, disk[u"P28E に対応なしの行の数"])
        self.assertEqual(sample_inject()[NF.COMPARE_KEY], disk[NF.COMPARE_KEY])
        self.assertEqual(sample_inject()[u"集計"], disk[u"集計"])
        self.assertEqual([], [x for x in inject_problems(disk, False) if u"土台" in x or u"限界" in x or u"対応なし" in x or u"集計" in x])

    def test_i_4_the_runner_swap_reaches_the_callers(self):
        with Patch() as pt:
            pt.set(RUN, "PROFILES", RUN.PROFILES)
            pt.set(RUN, "base_status4", RUN.base_status4)
            self.assertNotEqual([], NF.inject_wiring_problems())                       # 入れ替える前は赤
            NF.install_inject()
            self.assertEqual([], NF.inject_wiring_problems())
            self.assertIs(RUN.t8_candidates4.__globals__["base_status4"], NF.base_status_n)      # 使う側(t8_candidates4)が引く名前に届いている
            RUN.PROFILES = ("P27", "P27E", "P28", "P28E")
            self.assertNotEqual([], NF.inject_wiring_problems())
        self.assertEqual(("P27", "P27E", "P28", "P28E"), tuple(RUN.PROFILES))              # 戻っている

    def test_i_5_p29e_without_o_is_registered_only_inside_the_with(self):
        from adapters.xbrl import vocabulary as V
        self.assertNotIn("P29E-O", V.PROFILES)
        with NF.registered_p29e_no_o():
            self.assertIs(V.PROFILES["P29E-O"], NF.P29E_NO_O)
            with NF.registered_p29e_no_o():
                self.assertIn("P29E-O", V.PROFILES)
            self.assertIn("P29E-O", V.PROFILES)
        self.assertNotIn("P29E-O", V.PROFILES)
        self.assertFalse(NF.P29E_NO_O.other_subject_2026_11_02)
        self.assertTrue(V.P29E.other_subject_2026_11_02)
        self.assertEqual(V.P29E, __import__("dataclasses").replace(NF.P29E_NO_O, name="P29E", other_subject_2026_11_02=True))


# ================================================================ 宣言(docID を持つ記録 4 つは LATER_NAMING_FILES に宣言する)
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
    def test_h_1_the_four_records_are_declared_as_naming_files(self):
        src = read("tests/measure/test_xbrl_fresh_seal.py")
        self.assertEqual([], naming_problems(src))
        for rel in REC_REL.values():
            self.assertNotEqual([], naming_problems(src.replace('"%s"' % rel, '"x/%s"' % rel)), rel)
        self.assertNotEqual([], naming_problems(src.replace("LATER_NAMING_FILES", "LATER_NAMING_FILE")))
        self.assertNotEqual([], naming_problems(src.replace('"fixtures/xbrl/numfix/shapes_2026-11-04.json"', '"fixtures/xbrl/numfix/shapes_2026-11-04.json", "%s"' % SG.GATE_RELS[0])))

    def test_h_2_the_previous_declarations_are_still_there(self):
        got = later_naming_files(read("tests/measure/test_xbrl_fresh_seal.py"))
        for rel in ("fixtures/xbrl/aiforms/f5_gen_2026-11-03.json", "fixtures/xbrl/p28e/regress97_2026-11-03.json"):
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
            self.skipTest(u"記録が無い(判定・注入・97 書類・形の数を走らせた後に走る)")
        return load_records()

    def test_r_1_records_are_clean_and_consistent(self):
        R = self.need()
        self.assertEqual([], record_problems(copy.deepcopy(R), full=True))

    def test_r_2_judgment_is_rebuilt_from_the_records(self):
        R = self.need()
        self.assertEqual([], judge_problems(R, self.seal))
        J = NF.build_J(R, self.seal)
        self.assertEqual(set(J), {u"C", u"K", u"採用", u"欄"})

    def test_r_3_the_result_document_follows_the_records(self):
        R = self.need()
        self.assertTrue(os.path.exists(os.path.join(ROOT, DOC_REL)), "結果の文書が無い")
        self.assertEqual([], doc_problems(read(DOC_REL), R, self.seal))

    def test_r_4_order_is_seal_then_engine_then_records_and_document(self):
        self.need()
        self.assertEqual([], order_of(REPO))


class SkipLineTest(unittest.TestCase):
    def test_s_1_a_skipped_real_record_test_still_prints_a_line(self):
        u"""記録が無いと本番の記録の試験は skip になるが、skip でも行が出る(黙って消えない)。記録が在るかのように見せかけた標本でも確かめる。"""
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
