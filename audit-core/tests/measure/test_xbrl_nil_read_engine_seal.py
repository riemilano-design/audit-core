# -*- coding: utf-8 -*-
"""封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md(NRE ― engine の inline XBRL の読み取りが自己閉じの空の欄を始まりの tag と読まないようにする直し。``adapters/xbrl/instance.py`` の式 1 行)の門。封 §1〜§5。

**この門が縛るもの**

1. 封の字: 封の commit(36ca78f1)・path・要点の字・式の前後の字(封 §1)が script の定数と同じ。封の file は commit した blob と 1 字も変わっていない。
2. 入力 8 つの sha256 が script の表と実物で同じ。
3. engine の式(封 §1): 今の ``instance.py`` は封の commit の blob と **式の 1 行だけ**違い、その行は封の「後」の字。式を当たる例・当たらない例(自己閉じ・自己閉じの直後に fact が続く・属性の値の中の ``/``)で実際に走らせる。
4. engine の差分(履歴): 封の commit から engine の commit(封の後に ``instance.py`` を最初に触った commit。履歴から探す。hash を字で持たない)までの numstat が ``adapters/xbrl/instance.py`` の挿入 1・削除 1 だけ(``core/``・ほかの ``adapters/`` は 0 行)。
   engine の commit が履歴に無い(未 commit)ときは赤(skip にしない)。作業木に engine の未 commit の変更が在っても赤。
5. 順序: 封の commit ⊏ engine の commit ⊑ script・この門・記録を足した commit(未 commit は赤)。
6. 測定の部品を作り物で直接呼ぶ(``start_positions``・``start_block``・``pair_book``・``nre*_block``・``nre4_block``・``compare_zip``・``old_engine_module``)と、**つなぐ関数(``states_job``・``build_record``)を作り物の部品で本物のまま走らせる**。
   非対称な例: 作られた fact と消えた fact の数が違う作り物(1 と 2)・NR の記録と TSS の記録・直した engine の行を取り違えると数が変わる作り物。
   **検出力**: 直す前の式の engine(旧い blob の module)を測定の engine に差し替えて同じ配線を走らせると、作られた fact・消えた fact が 0 でなくなり NRE-1 の違う行が出る(0 が出たときに自分の欠陥を疑う確認)。
7. 記録 ``fixtures/xbrl/nil_read_engine/states_2026-11-17.json``: 封の字・script の sha256・入力・指紋(直した後が今の engine・直す前が TSS の記録のもの)・行の形(6 欄。文や値や要素名を持たない)・集計が行・本ごとの欄からの数え直しと一致・行の鍵が NR の記録の行の鍵と同じ・
   TSS の state の列が TSS の記録の行と同じ・NR の記録の「そのまま」の state の列と同じ・NRE-4 の数が群ごとの数と合う・EDINET の folder の ZIP の数が封の数と同じ。
8. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。式の変異・engine の差分の変異・履歴の変異は作り物の字・作り物の repo で当てる。
400 本の作り直しは門の中では走らせない(重い)。この file は docID の字を持たない。
"""
import ast
import collections
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``name`` は残す)。"""
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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_nre_seal")       # 順序・履歴の部品。門としては走らせない
MS = load_module("measure/xbrl_nil_read_engine_2026-11-17.py", "nil_read_engine_script_for_seal_gate")

SEAL_REL = "docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md"
SEAL_COMMIT_SHORT = "36ca78f1"               # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_nil_read_engine_2026-11-17.py"
GATE_REL = "tests/measure/test_xbrl_nil_read_engine_seal.py"
RECORD_REL = "fixtures/xbrl/nil_read_engine/states_2026-11-17.json"
TSS_RECORD_REL = "fixtures/xbrl/tanshin_self/states_2026-11-14.json"
NR_RECORD_REL = "fixtures/xbrl/nil_read/states_2026-11-17.json"
INSTANCE_REL = "adapters/xbrl/instance.py"
ORDER_FILES = (SCRIPT_REL, GATE_REL, RECORD_REL)
ENGINE_FILES = (INSTANCE_REL,)
#: 封 §1 の式(literal。script の写し・封の字・engine の行の 3 つと照らす)
FORMULA_BEFORE = r"r'<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>'"
FORMULA_AFTER = r"r'<ix:nonFraction([^>]*)(?<!/)>(.*?)</ix:nonFraction>'"
OLD_SHA16 = "f2d9e040f19adebf"                # 直す前の instance.py(TSS の時の値)
NEW_SHA16 = "1b8c00f86eafe765"                # engine の commit の instance.py
#: 入力の表(literal。script の表と実物の両方と照らす)
INPUT_SHAS = (
    ("fixtures/xbrl/tanshin_self/population_2026-11-14.json", "48ba8e5574be70d85b3d1affacc9403cffbfc698f529c095c6c882cd8ccfa9b0"),
    ("fixtures/xbrl/tanshin_self/states_2026-11-14.json", "00414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"),
    ("measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    ("measure/xbrl_tanshin_self_stage_2026-11-14.py", "4ed60b591366dd65a431dba5348aff6edb3889676d8e9a4154a5b0298486f7f9"),
    ("measure/xbrl_tanshin_2026-11-09.py", "b7ea491bf5cd34c4976bde86c4329583e0d9af09ec8895ea0caf48491492b5bd"),
    ("fixtures/xbrl/tanshin/states_2026-11-09.json", "6779b451b30aa7619923cbc8c390049f682deeb7bf5e198ddb21c9005b6362d4"),
    ("measure/xbrl_nil_read_2026-11-17.py", "f1489d091a55d420052b8f208d344d237b7f168ac0d66b6f2170b7d5f35e7ac4"),
    ("fixtures/xbrl/nil_read/states_2026-11-17.json", "16c07159f88973932f70e9c422734330dcdf7893b6ca26ed2898623b614c3864"))
INPUT_RELS = tuple(rel for rel, _sha in INPUT_SHAS)
STDLIB_OK = ("__future__", "argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "subprocess", "sys", "time", "types", "zipfile")
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
RATE_TEXT = re.compile(r"^(\d+\.\d%|分母 0)$")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
ROUTES = (u".xbrl の経路", u".htm の経路", u"どちらも無い")
K_NRE1 = u"NRE-1(直した engine のそのままの行 対 NR の記録の直した入力の行)"
K_NRE2 = u"NRE-2(直した engine の fact の差。そのまま 対 自己閉じを消した入力)"
K_NRE3 = u"NRE-3(直した engine のそのままの行 対 TSS の記録の行)"
K_NRE4 = u"NRE-4(.xbrl の経路の ZIP。旧い engine の blob 対 今の load_instance)"
K_NRE5 = u"NRE-5(直す前の式の始まり 対 直した式の始まり。位置ごと)"
K_PRED = u"予測の判定に要る数(NRE-1〜NRE-5。当たり・外れは結果の文書で)"
K_BOOKS = u"本ごと(切れた本だけ)"
PD = u"XBRL/PublicDoc/"
#: 封 §1 の作り物の例
NIL_TAG = b'<ix:nonFraction name="ex:A" contextRef="Prior" unitRef="JPY" scale="6" xsi:nil="true"/>'
REAL_TAG = b'<ix:nonFraction name="ex:A" contextRef="Current" unitRef="JPY" scale="6">120</ix:nonFraction>'
NIL_C = b'<ix:nonFraction name="ex:C" contextRef="Prior" unitRef="JPY" scale="6" xsi:nil="true"/>'
REAL_C = b'<ix:nonFraction name="ex:C" contextRef="Current" unitRef="JPY" scale="6">347</ix:nonFraction>'
SLASH_TAG = (b'<ix:nonFraction name="ex:D" contextRef="Current" unitRef="JPY" scale="3" format="ixt:numdotdecimal" '
             b'href="http://example.invalid/a/b/" title="x/">58</ix:nonFraction>')


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def guard(fn, *a, **k):
    u"""検査を呼ぶ。例外は「問題」として返す(変異した関数が落ちても赤として数える)。"""
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  Stop(SystemExit)を含む
        return [u"例外: %s" % type(exc).__name__]


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("nil_read_engine_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def mem_zip(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n, d in members:
            z.writestr(n, d)
    return buf.getvalue()


def example_zip(html):
    return mem_zip([(PD + u"x_ixbrl.htm", html)])


def ns(real, **over):
    d = dict(vars(real))
    d.update(over)
    return types.SimpleNamespace(**d)


@contextlib.contextmanager
def patched(ms, **over):
    saved = dict((k, getattr(ms, k)) for k in over)
    for k, v in over.items():
        setattr(ms, k, v)
    try:
        yield
    finally:
        for k, v in saved.items():
            setattr(ms, k, v)


def git_blob_text(commit, rel, root=REPO):
    r = subprocess.run(["git", "show", "%s:%s%s" % (commit, PREFIX, rel)], cwd=root, capture_output=True)
    return r.stdout if r.returncode == 0 else None


# ---------------------------------------------------------------- 1. 封の字
def seal_text():
    return read(SEAL_REL)


def seal_formulas(seal):
    u"""封 §1 の「前:」「後:」の行の式(``r'…'`` の字)。なければ None。"""
    b = re.search(r"^前: (r'.*')$", seal, re.M)
    a = re.search(r"^後: (r'.*')$", seal, re.M)
    return (b.group(1) if b else None, a.group(1) if a else None)


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.STATES_REL != RECORD_REL or ms.INSTANCE_REL != INSTANCE_REL:
        out.append(u"script の封の commit・path・記録の path・engine の path が門と違う")
    for phrase in (u"(?<!/)", u"NRE-1", u"NRE-2", u"NRE-3", u"NRE-4", u"NRE-5", u"NRE-6", u"NRE-7", u"挿入 1・削除 1", u"旗なし", u"**engine(`adapters/`)を変える。**",
                   u"便 NR の script を sys.modules を汚さない形で読んで**呼ぶ**"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    before, after = seal_formulas(seal)
    if before != FORMULA_BEFORE or after != FORMULA_AFTER:
        out.append(u"封 §1 の式の字が門の字と違う")
    if "r'%s'" % ms.OLD_FACT_RE_SRC != FORMULA_BEFORE or "r'%s'" % ms.NEW_FACT_RE_SRC != FORMULA_AFTER:
        out.append(u"script の式の写しが封 §1 の前・後の字と違う")
    if ms.OLD_INSTANCE_SHA16 != OLD_SHA16:
        out.append(u"script の旧い instance.py の sha16 が門と違う")
    if ms.PROFILE != u"P33E" or ms.STATE_G != u"GROUNDED" or tuple(ms.STATES) != STATES:
        out.append(u"profile か state の名が違う")
    if dict(ms.EDINET_FOLDERS) != {"edinet": 281, "edinet-demo-cabocia": 3, "edinet-fresh-2026-10-21": 40, "edinet-prior-2026-11-02": 94} or ms.N_0911 != 17:
        out.append(u"NRE-4 の folder の数が封(便 NR の棚卸しの数)と違う")
    return out


def seal_history_problems(root=REPO):
    u"""封の file の履歴は 1 commit(36ca78f1)で、今の file はその commit の blob と 1 字も変わらない。"""
    c = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(c) != 1 or not c[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の commit が履歴に 1 つで %s に決まらない" % SEAL_COMMIT_SHORT]
    rc, log = PR.git_in(root, "log", "--format=%H", "--", PREFIX + SEAL_REL)
    if len([x for x in log.split() if x]) != 1:
        return [u"封の file の履歴が 1 commit でない(封の後に封が書き換えられた)"]
    rc, blob = PR.git_in(root, "show", "%s:%s" % (c[0], PREFIX + SEAL_REL))
    if seal_text().rstrip(u"\n") != blob.rstrip(u"\n"):
        return [u"今の封が封の commit の blob と違う"]
    return []


# ---------------------------------------------------------------- 2. 入力の sha256
def input_sha_problems(ms=None):
    ms = ms or MS
    out = []
    if [(rel, sha) for _no, rel, sha in ms.INPUTS] != list(INPUT_SHAS):
        out.append(u"script の入力の表が門の表と違う")
    out.extend(u"入力の sha256 が表と違う: %s" % rel for rel, want in INPUT_SHAS if sha_of(rel) != want)
    return out


# ---------------------------------------------------------------- 3. engine の式
def formula_literals(src):
    u"""engine の字(``src``)の中で ``ix:nonFraction`` の開始を探す ``re.finditer`` の呼びの、最初の引数の式の字(1 つ)。ast で読む。(式の列, 呼びの数)。"""
    found = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "finditer" and n.args and isinstance(n.args[0], ast.Constant) \
                and isinstance(n.args[0].value, str) and "<ix:nonFraction" in n.args[0].value:
            found.append(n.args[0].value)
    return found


def formula_behavior_problems(pattern):
    u"""式(字)を ``re.S`` で走らせた振る舞い: 自己閉じは始まりでない・自己閉じの後ろの fact は拾う・属性の値の中の ``/`` は影響しない・空白を挟んだ自己閉じも始まりでない。"""
    out = []
    rx = re.compile(pattern, re.S)
    nil, real, slash = NIL_TAG.decode(), REAL_TAG.decode(), SLASH_TAG.decode()

    def got(html):
        return [(m.group(1), m.group(2)) for m in rx.finditer(html)]

    g = got(nil + real)
    if len(g) != 1 or 'contextRef="Current"' not in g[0][0] or g[0][1] != "120":
        out.append(u"自己閉じの後ろに fact が続く例で「Current の fact 1 つ」にならない: %s" % len(g))
    if got(nil):
        out.append(u"自己閉じだけの入力から fact を拾った")
    if got(nil.replace("/>", " />")):
        out.append(u"空白を挟んだ自己閉じを始まりと読んだ")
    if len(got(real)) != 1:
        out.append(u"自己閉じが無い入力で fact が 1 つにならない")
    gs = got(slash)
    if len(gs) != 1 or gs[0][1] != "58":
        out.append(u"属性の値の中に / が在る tag を拾わなかった")
    if len(got(nil + nil + real + nil + slash)) != 2:
        out.append(u"自己閉じが散らばった入力で本物の fact 2 つにならない")
    return out


def engine_formula_problems(src=None):
    u"""今の ``instance.py`` の字: ``ix:nonFraction`` の開始を探す呼びが 1 つで、式は封の「後」の字(前の字はどこにも無い)・振る舞いが封どおり。"""
    src = src if src is not None else read(INSTANCE_REL)
    out = []
    pats = formula_literals(src)
    if len(pats) != 1:
        return [u"inline XBRL の開始を探す finditer の呼びが 1 つでない(%d)" % len(pats)]
    if "r'%s'" % pats[0] != FORMULA_AFTER:
        out.append(u"engine の式が封 §1 の「後」の字でない")
    if FORMULA_BEFORE in src or src.count(FORMULA_AFTER) != 1:
        out.append(u"封 §1 の「前」の字が残っているか、「後」の字が 1 回でない")
    out.extend(formula_behavior_problems(pats[0]))
    return out


def engine_diff_problems(old_src, new_src):
    u"""旧い blob と今の字は、式の 1 行だけが違う: 行の数が同じ・違う行が 1 つ・旧い行が封の「前」の字を含み、新しい行がその 1 か所だけを「後」の字に替えた行。"""
    old, new = old_src.splitlines(), new_src.splitlines()
    if len(old) != len(new):
        return [u"行の数が違う(式の 1 行の置き換えだけでない)"]
    idx = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
    if len(idx) != 1:
        return [u"違う行が 1 つでない(%d)" % len(idx)]
    a, b = old[idx[0]], new[idx[0]]
    if a.count(FORMULA_BEFORE) != 1 or b != a.replace(FORMULA_BEFORE, FORMULA_AFTER):
        return [u"違う 1 行が封 §1 の「前」から「後」への置き換えだけでない"]
    return []


def real_diff_problems(root=REPO):
    old = git_blob_text(SEAL_COMMIT_SHORT, INSTANCE_REL, root)
    if old is None:
        return [u"封の commit の instance.py を読めない"]
    if hashlib.sha256(old).hexdigest()[:16] != OLD_SHA16:
        return [u"封の commit の instance.py の sha16 が直す前の値と違う"]
    return engine_diff_problems(old.decode("utf-8"), read(INSTANCE_REL))


def sha16_problems():
    return [] if sha_of(INSTANCE_REL)[:16] == NEW_SHA16 else [u"今の instance.py の sha16 が engine の commit の値と違う"]


# ---------------------------------------------------------------- 4. engine の差分(履歴)
def numstat_problems(lines):
    u"""``git diff --numstat`` の行の列は ``adapters/xbrl/instance.py`` の 挿入 1・削除 1 の 1 行だけ。"""
    want = ["1\t1\t%s%s" % (PREFIX, INSTANCE_REL)]
    return [] if list(lines) == want else [u"engine の差分が instance.py の挿入 1・削除 1 だけでない: %s" % (list(lines),)]


def engine_commit(root, prefix, seal_rel, impl_files):
    u"""(封の commit, engine の commit)。engine の commit = 封の後に各 file を最初に触った commit(子孫の最後)。履歴から探す(hash を字で持たない)。"""
    s = PR.added_commits(root, prefix + seal_rel)
    if len(s) != 1:
        return None, None
    firsts = []
    for rel in impl_files:
        lst = [c for c in PR.git_in(root, "log", "--format=%H", s[0] + "..HEAD", "--", prefix + rel)[1].split() if c]
        if not lst:
            return s[0], None
        firsts.append(lst[-1])
    e = firsts[0]
    for c in firsts[1:]:
        if PR.is_anc(root, e, c):
            e = c
    return s[0], e


def real_numstat_problems(root=REPO, prefix=PREFIX, seal_rel=SEAL_REL, impl_files=ENGINE_FILES):
    sh, e = engine_commit(root, prefix, seal_rel, impl_files)
    if sh is None or e is None:
        return [u"封か engine の commit が履歴に無い(未 commit)"]
    rc, txt = PR.git_in(root, "diff", "--numstat", sh, e, "--", prefix + "adapters", prefix + "core")
    if rc != 0:
        return [u"git diff が失敗した"]
    return numstat_problems([x for x in txt.splitlines() if x])


def engine_worktree_problems(root=REPO):
    rc, st = PR.git_in(root, "status", "--porcelain", "--untracked-files=all", "--", PREFIX + "adapters", PREFIX + "core")
    if rc != 0:
        return [u"git status が失敗した"]
    return [u"engine に未 commit の変更: %s" % ln.strip()[:2] for ln in st.splitlines() if ln.strip()]


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, impls=ENGINE_FILES, others=None):
    others = list(ORDER_FILES) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, list(impls), others)


# ---------------------------------------------------------------- 5. 測定の部品(作り物)
def start_problems(ms=None):
    u"""NRE-5 の始まりの位置。封 §1 の例と、直した式の側が一致を全部数えること(式が自己閉じを拾えば違いが出る)。"""
    ms = ms or MS
    out = []
    s = lambda b: b.decode()
    both = s(NIL_TAG + b"\n" + REAL_TAG)
    real_at = len(NIL_TAG) + 1
    old_p = ms.start_positions(both, ms.OLD_FACT_RE)
    new_p = ms.start_positions(both, ms.NEW_FACT_RE)
    if old_p != [(0, True), (real_at, False)] or new_p != [(real_at, False)]:
        out.append(u"自己閉じ + 本物の fact の始まりが 直す前 [(0, 自己閉じ), (本物, 違う)]・直した [(本物, 違う)] にならない: %s %s" % (old_p, new_p))
    if ms.start_positions(s(NIL_TAG), ms.OLD_FACT_RE) != [] or ms.start_positions(s(NIL_TAG), ms.NEW_FACT_RE) != []:
        out.append(u"自己閉じだけの入力(終わりの tag が無い)に始まりが在る")
    if ms.start_positions(s(NIL_TAG + b"</ix:nonFraction>"), ms.OLD_FACT_RE) != [(0, True)] or ms.start_positions(s(NIL_TAG + b"</ix:nonFraction>"), ms.NEW_FACT_RE) != []:
        out.append(u"自己閉じの後ろに終わりの tag だけが在る入力で、直す前の式は自己閉じを始まりと読み、直した式は読まない形にならない")
    if ms.start_positions(s(SLASH_TAG), ms.OLD_FACT_RE) != [(0, False)] or ms.start_positions(s(SLASH_TAG), ms.NEW_FACT_RE) != [(0, False)]:
        out.append(u"属性の値の中に / が在る tag の始まりを数えない(自己閉じと取り違えた疑い)")
    if ms.start_positions(s(REAL_TAG), ms.OLD_FACT_RE) != ms.start_positions(s(REAL_TAG), ms.NEW_FACT_RE):
        out.append(u"自己閉じが無い入力で始まりの位置が前後で違う")
    # 位置ごとに当てる: finditer の飲み込み(直す前の式の自己閉じの一致が次の fact を飲む)で数が合わなくならない
    two = s(NIL_TAG + REAL_TAG + NIL_C + REAL_C)
    old_real = [p for p, sc in ms.start_positions(two, ms.OLD_FACT_RE) if not sc]
    new_all = [p for p, _sc in ms.start_positions(two, ms.NEW_FACT_RE)]
    if len(old_real) != 2 or old_real != new_all:
        out.append(u"位置ごとに当てた始まりが(直す前の自己閉じでないもの 2・直した式 2・同じ位置)でない: %s %s" % (old_real, new_all))
    # start_block: (直す前の始まり(自己閉じでない)・直した式が拾う始まり・位置の集合が違う・直した式が finditer で拾う数)
    zb_b = example_zip(NIL_TAG + b"\n" + REAL_TAG + b"\n" + NIL_C + b"text" + REAL_C)
    if ms.start_block(zb_b) != (2, 2, 0, 2):
        out.append(u"start_block が(2, 2, 0, 2)にならない: %s" % (ms.start_block(zb_b),))
    zb_m = mem_zip([(PD + u"a_ixbrl.htm", REAL_TAG), (PD + u"b_ixbrl.htm", NIL_TAG + REAL_C), (PD + u"c.xml", REAL_TAG)])
    if ms.start_block(zb_m) != (2, 2, 0, 2):
        out.append(u"start_block が htm の member だけを数えていない・member をまたいで数えている: %s" % (ms.start_block(zb_m),))
    # 検出力: 式が自己閉じを拾う版(lookbehind を \s にした版)に差し替えると、直した式の側の始まりが増えて位置の集合が違う本になる
    bad_re = re.compile(r"<ix:nonFraction([^>]*)(?<!\s)>(.*?)</ix:nonFraction>", re.S)
    bad_globals = dict(vars(ms), NEW_FACT_RE=bad_re)
    bad_block = types.FunctionType(ms.start_block.__code__, bad_globals)
    r = bad_block(example_zip(NIL_TAG + b"\n" + REAL_TAG))
    if r != (1, 2, 1, 1):
        out.append(u"自己閉じを拾う式に差し替えたとき start_block が(1, 2, 1, 1)にならない(検出力がない): %s" % (r,))
    return out


def pair_problems(ms=None):
    u"""行の対: [本の #, 文の番号, 位置, 直した engine の state, NR の直した入力の state と同じか, TSS の state]。取り違えると数が変わる非対称な例。"""
    ms = ms or MS
    out = []
    G, VM, UN, PN = STATES
    # new = 直した engine の行([文, 位置, state, reason])・tss = TSS の記録の行・nr = NR の記録の行([本, 文, 位置, そのまま, 直した入力, reason が同じか])
    new = [[1, 1, G, u"a"], [1, 2, G, u"b"], [2, 1, UN, u"c"], [3, 1, VM, u"d"]]
    tss = [[1, 1, G, u"a"], [1, 2, UN, u"x"], [2, 1, UN, u"c"], [3, 1, G, u"e"]]
    nr = [[7, 1, 1, G, G, True], [7, 1, 2, UN, G, False], [7, 2, 1, UN, UN, True], [7, 3, 1, G, VM, False]]
    got = ms.pair_book(7, new, tss, nr)
    if got != [[7, 1, 1, G, True, G], [7, 1, 2, G, True, UN], [7, 2, 1, UN, True, UN], [7, 3, 1, VM, True, G]]:
        out.append(u"行の対が違う: %s" % got)
    # 違い: state が違う・reason の同じかが違う
    nr2 = [list(r) for r in nr]
    nr2[0][4] = VM
    nr2[1][5] = True
    got2 = ms.pair_book(7, new, tss, nr2)
    if [r[4] for r in got2] != [False, False, True, True]:
        out.append(u"state の違い・reason の同じかの違いを行の対が見ていない: %s" % [r[4] for r in got2])
    # 止まり方: 鍵の並びが違う・NR の「そのまま」の state が TSS の記録と違う・別の本の行
    for label, args in ((u"鍵の並び(新)が違う", (new[:3] + [[3, 2, VM, u"d"]], tss, nr)), (u"鍵の並び(TSS)が違う", (new, tss[:3] + [[3, 2, G, u"e"]], nr)),
                        (u"鍵の並び(NR)が違う", (new, tss, nr[:3] + [[7, 3, 2, G, VM, False]])), (u"行が足りない", (new[:3], tss, nr)),
                        (u"NR の「そのまま」が TSS と違う", (new, tss, [nr[0], nr[1], nr[2], [7, 3, 1, UN, VM, False]])), (u"本の # が違う", (new, tss, [nr[0], nr[1], nr[2], [8, 3, 1, G, VM, False]]))):
        try:
            ms.pair_book(7, *args)
            out.append(u"%s のに pair_book が止まらない" % label)
        except ms.Stop:
            pass
        except BaseException as exc:                       # noqa: BLE001
            out.append(u"%s: Stop でない例外 %s" % (label, type(exc).__name__))
    return out


def block_problems(ms=None):
    u"""NRE-1・NRE-2・NRE-3・NRE-5 と本ごとの欄・予測の数を手計算の作り物で。"""
    ms = ms or MS
    out = []
    G, VM, UN, PN = STATES
    rows = [[1, 1, 1, G, True, G], [1, 1, 2, G, False, UN], [2, 1, 1, UN, True, VM], [2, 1, 2, VM, True, VM], [3, 1, 1, G, True, G]]
    books = [
        collections.OrderedDict([(u"#", 1), (u"切れた", True), (u"行の対", rows[:2]), (u"fact の差", (3, 1, 1)), (u"独立の読みと同じ", True), (u"自己閉じの数", 4), (u"始まり", (5, 5, 1, 6))]),
        collections.OrderedDict([(u"#", 2), (u"切れた", True), (u"行の対", rows[2:4]), (u"fact の差", (0, 2, 0)), (u"独立の読みと同じ", False), (u"自己閉じの数", 0), (u"始まり", (2, 3, 1, 3))]),
        collections.OrderedDict([(u"#", 3), (u"切れた", True), (u"行の対", rows[4:]), (u"fact の差", (0, 0, 0)), (u"独立の読みと同じ", True), (u"自己閉じの数", 1), (u"始まり", (0, 0, 0, 0))]),
        collections.OrderedDict([(u"#", 4), (u"切れた", False)])]
    if ms.rows_of(books) != rows:
        out.append(u"rows_of が切れた本の行だけを本の順に並べない")
    per = ms.per_book_table(books)
    if per != [[1, 1, 3, 1, 5, 5, 1, 6], [2, 0, 0, 2, 2, 3, 1, 3], [3, 0, 0, 0, 0, 0, 0, 0]]:
        out.append(u"本ごとの欄が [本の #, NRE-1 で違う行, 作られた, 消えた, 直す前の始まり, 直した始まり, 位置の集合が違う, finditer] にならない: %s" % per)
    b1 = ms.nre1_block(rows, per)
    if (b1[u"切れた本"], b1[u"行の数"], b1[u"NR の直した入力の行と違う行"], b1[u"NR の直した入力の行と違う行を持つ本"], b1[u"NR の直した入力の行と同じ本"]) != (3, 5, ms.rate(1, 5), 1, 2):
        out.append(u"NRE-1 の数が違う: %s" % dict(b1))
    b2 = ms.nre2_block(per, books)
    if (b2[u"切れた本"], b2[u"自己閉じの数(消した数)"], b2[u"作られた fact"], b2[u"消えた fact"], b2[u"作られた fact を持つ本"], b2[u"消えた fact を持つ本"],
            b2[u"独立の読みと直した engine の fact が同じ本"]) != (3, 5, 3, 3, 1, 2, 2):
        out.append(u"NRE-2 の数が違う(作られた・消えたの向き・本の数え方): %s" % dict(b2))
    b3 = ms.nre3_block(rows)
    t = b3[u"state の移り変わり(TSS の記録 → 直した engine)"]
    if len(t) != 16 or sum(t.values()) != 5 or t[u"UNVERIFIABLE → GROUNDED"] != 1 or t[u"GROUNDED → UNVERIFIABLE"] != 0 or t[u"GROUNDED → GROUNDED"] != 2 or t[u"VALUE_MISMATCH → VALUE_MISMATCH"] != 1 or t[u"VALUE_MISMATCH → UNVERIFIABLE"] != 1:
        out.append(u"NRE-3 の移り変わりの表の向き(TSS の記録 → 直した engine)が違う: %s" % dict((k, v) for k, v in t.items() if v))
    rows2 = [[1, 1, 1, G, True, UN], [1, 1, 2, UN, True, G], [2, 1, 1, G, True, UN], [2, 1, 2, VM, True, VM]]
    b3b = ms.nre3_block(rows2)
    if (b3b[u"state が変わった行"], b3b[u"state が変わった行を持つ本"], b3b[u"state が変わった行を持つ本の #"], b3b[u"直した engine でだけ値が合う行"], b3b[u"TSS の記録(直す前)でだけ値が合う行"]) != (
            ms.rate(3, 4), 2, [1, 2], 2, 1):
        out.append(u"NRE-3 の 2 方向(直した engine でだけ合う・直す前でだけ合う)の数か向きが違う: %s" % dict(b3b))
    b5 = ms.nre5_block(per)
    if (b5[u"包んだ本"], b5[u"直す前の式の始まり(自己閉じでない)の合計"], b5[u"直した式が拾う始まりの合計"], b5[u"始まりの位置の集合が違う本"], b5[u"始まりの数が違う本"],
            b5[u"直した式が finditer で拾う数の合計"]) != (3, 7, 8, 2, 1, 9):
        out.append(u"NRE-5 の数が違う: %s" % dict(b5))
    b4 = collections.OrderedDict([(u"facts の列が違う ZIP の合計", 1), (u"読んだ ZIP の合計", 9)])
    pr = ms.prediction_numbers(b1, b2, b3, b4, b5)
    if pr[u"NRE-1 NR の直した入力の行と違う本 / 切れた本"] != collections.OrderedDict([(u"分子", 1), (u"分母", 3)]) or pr[u"NRE-4 facts の列が違う ZIP / 読んだ ZIP"] != collections.OrderedDict([(u"分子", 1), (u"分母", 9)]):
        out.append(u"予測の数の NRE-1・NRE-4 の分子・分母が違う")
    if pr[u"NRE-2 作られた fact・消えた fact"] != collections.OrderedDict([(u"作られた fact", 3), (u"消えた fact", 3)]) or pr[u"NRE-3 state が変わった行を持つ本"] != b3[u"state が変わった行を持つ本"]:
        out.append(u"予測の数の NRE-2・NRE-3 が違う")
    return out


def old_engine_problems(ms=None):
    u"""NRE-4: 旧い engine の blob を memory の module として走らせた ``load_instance`` と今の ``load_instance`` の比べ。"""
    ms = ms or MS
    out = []
    old_src = git_blob_text(SEAL_COMMIT_SHORT, INSTANCE_REL)
    if old_src is None:
        return [u"封の commit の instance.py を読めない"]
    old = ms.old_engine_module(old_src)
    if "old_instance_for_nil_read_engine" in sys.modules:
        out.append(u"旧い engine の module を sys.modules に登録した")
    new = MS.I
    htm = example_zip(NIL_TAG + b"\n" + REAL_TAG)
    same, same_all, xb = ms.compare_zip(old, new, htm)
    if same or same_all or xb:
        out.append(u"自己閉じ + fact の .htm の ZIP で 旧い engine と今の engine の facts が違わない(違い・経路の見え方): %s" % ((same, same_all, xb),))
    xbrl = mem_zip([(PD + u"a.xbrl", (u'<?xml version="1.0" encoding="utf-8"?><xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:ex="http://example.invalid/ns">'
                                     u'<xbrli:context id="c"><xbrli:period><xbrli:instant>2020-03-31</xbrli:instant></xbrli:period></xbrli:context>'
                                     u'<ex:A contextRef="c" unitRef="JPY" decimals="0">58</ex:A></xbrli:xbrl>').encode("utf-8"))])
    if ms.compare_zip(old, new, xbrl) != (True, True, True):
        out.append(u".xbrl の経路の ZIP で 旧い engine と今の engine が違う、か経路が .xbrl と見えない")
    plain = example_zip(REAL_TAG)
    if ms.compare_zip(old, new, plain) != (True, True, False):
        out.append(u"自己閉じの無い .htm の ZIP で facts が違うと出した")
    per = ms.nre4_block(old, new, [(u"g1", [lambda: xbrl, lambda: xbrl, lambda: htm]), (u"g2", [lambda: plain])])
    if per[u"g1"] != collections.OrderedDict([(u"読んだ ZIP", 3), (u"facts の列が違う ZIP", 1), (u"返り値の全体が違う ZIP", 1), (u".xbrl の経路でない ZIP", 1), (u"facts の列が違う ZIP の番号(群の中の順)", [2])]) \
            or per[u"g2"][u"facts の列が違う ZIP"] != 0 or per[u"g2"][u".xbrl の経路でない ZIP"] != 1:
        out.append(u"nre4_block の群ごとの数が違う: %s" % dict(per))
    tot = ms.nre4_total(per)
    if (tot[u"読んだ ZIP の合計"], tot[u"facts の列が違う ZIP の合計"], tot[u"返り値の全体が違う ZIP の合計"], tot[u".xbrl の経路でない ZIP の合計"]) != (4, 1, 1, 2):
        out.append(u"nre4_total の合計が違う")
    # facts は同じで返り値の全体だけ違う作り物(全体の違いと facts の違いを混ぜない非対称な例)
    fa = types.SimpleNamespace(load_instance=lambda zb: {"facts": [1], "meta": 1})
    fb = types.SimpleNamespace(load_instance=lambda zb: {"facts": [1], "meta": 2})
    if ms.compare_zip(fa, fb, xbrl)[:2] != (True, False):
        out.append(u"facts が同じで全体だけ違う作り物を compare_zip が見分けない")
    per_f = ms.nre4_block(fa, fb, [(u"f", [lambda: xbrl])])
    if per_f[u"f"][u"facts の列が違う ZIP"] != 0 or per_f[u"f"][u"返り値の全体が違う ZIP"] != 1:
        out.append(u"nre4_block が全体の違いを facts の違いと混ぜている: %s" % dict(per_f[u"f"]))
    # old/new の取り違え(同じ module 2 つ)では違いが出ない = 引数の位置が効いている確認(違い自体は上で出ている)
    if ms.compare_zip(new, new, htm)[0] is not True:
        out.append(u"同じ module 同士で facts が違うと出した")
    # sha16 が違う blob は止まる
    try:
        ms.old_engine_module(old_src + b"\n# x\n")
        out.append(u"sha16 が違う旧い blob のに old_engine_module が止まらない")
    except ms.Stop:
        pass
    try:
        ms.git_blob(u"0" * 40, ms.INSTANCE_GIT_PATH)
        out.append(u"読めない commit のに git_blob が止まらない")
    except ms.Stop:
        pass
    return out


def material_problems(ms=None):
    u"""材料の数の確かめ: EDINET の folder の ZIP の数が封の数・2026-11-09 の便の本の数が 17 と違えば止まる。"""
    ms = ms or MS
    out = []
    good = collections.OrderedDict([("edinet", 281), ("edinet-demo-cabocia", 3), ("edinet-fresh-2026-10-21", 40), ("edinet-prior-2026-11-02", 94)])
    try:
        ms.check_material_counts(good, 17)
    except ms.Stop:
        out.append(u"封の数のとき check_material_counts が止まった")
    for label, counts, n in ((u"EDINET の folder の数が 1 つ違う", collections.OrderedDict(good, edinet=280), 17), (u"folder が足りない", collections.OrderedDict(list(good.items())[:3]), 17),
                             (u"便 2026-11-09 の数が違う", good, 16), (u"2 つ目の folder が違う", collections.OrderedDict(good, **{"edinet-demo-cabocia": 4}), 17)):
        try:
            ms.check_material_counts(counts, n)
            out.append(u"%s のに check_material_counts が止まらない" % label)
        except ms.Stop:
            pass
    return out


def rate_problems_fn(ms=None):
    ms = ms or MS
    out = []
    for n, d, want in ((1, 3, u"33.3%"), (2, 3, u"66.7%"), (1, 8, u"12.5%"), (1, 16, u"6.3%"), (0, 5, u"0.0%"), (5, 5, u"100.0%"), (3, 0, u"分母 0")):
        if ms.rate(n, d) != collections.OrderedDict([(u"分子", n), (u"分母", d), (u"率", want)]):
            out.append(u"率が違う: %d/%d" % (n, d))
    return out


# ---------------------------------------------------------------- 5b. つなぐ関数(states_job・build_record を作り物の部品で本物のまま走らせる)
def fake_judge(ms, rows, cut=True):
    def judge_book(n, grp, kind, sha, zb):
        return collections.OrderedDict([(u"#", n), (u"群", grp), (u"様式の種類", kind), (u"ZIP の sha256", sha), (u"切り出し", ms.TSS.CUT_OK if cut else u"切れない"), (u"行", rows if cut else [])])
    return judge_book


def counter_from(mod):
    def engine_counter(zb):
        return collections.Counter((f["name"], f["context"], f["unit"], f["decimals"], f["value"]) for f in mod.load_instance(zb)["facts"])
    return engine_counter


def run_job(ms, html, cut=True, new_rows=None, tss_rows=None, nr_rows=None, nr_book_n=1, engine_mod=None, tss_cut=True, extra_nr=None):
    u"""``ms.states_job`` を作り物の 1 本で走らせる。(結果, 例外)。外の部品(TSS の cut・wrap・judge_book)だけ作り物。fix_zip・engine_counter・independent_counter・fact_diff・start_block は本物
    (``engine_mod`` を渡せばその module の ``load_instance`` で fact を読む)。"""
    G, UN = u"GROUNDED", u"UNVERIFIABLE"
    new_rows = new_rows if new_rows is not None else [[1, 1, G, u"rn"]]
    tss_rows = tss_rows if tss_rows is not None else [[1, 1, UN, u"rt"]]
    nr_rows = nr_rows if nr_rows is not None else [[nr_book_n, 1, 1, UN, G, False]]
    content = (b"cut-" if cut else b"nocut-") + b"material"
    sha = hashlib.sha256(content).hexdigest()
    tmp = tempfile.mkdtemp(prefix="nre_job_")
    try:
        path = os.path.join(tmp, sha + ".zip")
        with open(path, "wb") as fh:
            fh.write(content)
        wrapped = example_zip(html)
        tss = ns(ms.TSS, judge_book=fake_judge(ms, new_rows, cut), cut=lambda zb: (u"text", 7, None) if cut else (None, None, u"x"), wrap=lambda zb, text: (wrapped, 1))
        over = dict(TSS=tss)
        if engine_mod is not None:
            over["NR"] = ns(ms.NR, engine_counter=counter_from(engine_mod))
        tss_book = collections.OrderedDict([(u"#", 1), (u"切り出し", ms.TSS.CUT_OK if tss_cut else u"切れない"), (u"行", tss_rows)])
        with patched(ms, **over):
            try:
                return ms.states_job((1, u"甲", u"k", sha, path, tss_book, nr_rows)), None
            except BaseException as exc:                   # noqa: BLE001
                return None, exc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


SCEN_A = NIL_TAG + b"\n" + REAL_TAG
SCEN_B = NIL_TAG + b"\n" + REAL_TAG + b"\n" + NIL_C + b"text" + REAL_C


def job_wire_problems(ms=None):
    u"""``states_job`` の配線: 直した engine の fact の差(そのまま 対 自己閉じを消した入力)・行の対・始まりの位置・止まり方・検出力(旧い engine なら差が出る)。"""
    ms = ms or MS
    out = []
    old_src = git_blob_text(SEAL_COMMIT_SHORT, INSTANCE_REL)
    old = ms.old_engine_module(old_src) if old_src is not None else None
    # 直した engine(今の engine): 作られた 0・消えた 0
    for label, html, nil in (("A", SCEN_A, 1), ("B", SCEN_B, 2)):
        res, exc = run_job(ms, html)
        if exc is not None or res is None:
            out.append(u"%s: states_job が落ちた %s" % (label, type(exc).__name__))
            continue
        if res.get(u"fact の差") != (0, 0, 0):
            out.append(u"%s: 直した engine で fact の差が(0, 0, 0)にならない: %s" % (label, res.get(u"fact の差")))
        if res.get(u"自己閉じの数") != nil or res.get(u"独立の読みと同じ") is not True:
            out.append(u"%s: 自己閉じの数か独立の読みとの一致が違う" % label)
        if res.get(u"行の対") != [[1, 1, 1, u"GROUNDED", True, u"UNVERIFIABLE"]]:
            out.append(u"%s: 行の対が(直した engine の state・NR と同じか・TSS の state)に結ばれていない: %s" % (label, res.get(u"行の対")))
        if res.get(u"始まり")[:3] != (res[u"始まり"][0], res[u"始まり"][0], 0) or res[u"始まり"][0] != (1 if label == "A" else 2):
            out.append(u"%s: 始まりの位置の数が違う: %s" % (label, res.get(u"始まり")))
    # 検出力: 旧い engine に差し替えると、同じ作り物で 作られた・消えたが 0 でなくなる(非対称: A は 1・1・1、B は 1・2・1)
    if old is not None:
        for label, html, want in (("A", SCEN_A, (1, 1, 1)), ("B", SCEN_B, (1, 2, 1))):
            res, exc = run_job(ms, html, engine_mod=old)
            if exc is not None and not isinstance(exc, ms.Stop):
                out.append(u"%s: 旧い engine で states_job が落ちた %s" % (label, type(exc).__name__))
            elif res is not None and res.get(u"fact の差") != want:
                out.append(u"%s: 旧い engine のとき fact の差が %s にならない(測定が欠陥を検出しない): %s" % (label, want, res.get(u"fact の差")))
            elif res is None and not isinstance(exc, ms.Stop):
                out.append(u"%s: 旧い engine で結果が無い" % label)
    # 独立の読み: 旧い engine のそのままの読みは独立の読みと違う(自己閉じの後ろの fact を飲む)
    if old is not None:
        res, exc = run_job(ms, SCEN_A, engine_mod=old)
        if res is not None and res.get(u"独立の読みと同じ") is not False:
            out.append(u"旧い engine のとき独立の読みとの一致が False にならない(独立の読みを比べる相手が違う疑い)")
    # 始まりの位置: 直した式が自己閉じを拾う形(lookbehind 無し)なら位置の集合が違いに出る(包んだ入力から数えている)
    with patched(ms, NEW_FACT_RE=ms.OLD_FACT_RE):
        res, exc = run_job(ms, SCEN_A)
    if exc is not None or res is None or res.get(u"始まり")[2] != 1:
        out.append(u"直した式が自己閉じを拾う形のとき、始まりの位置の集合が違いに出ない(包んだ入力から数えていない疑い)")
    # NRE-1 の違い: 直した engine の行が NR の直した入力の行と違えば行の対の「同じか」が False
    res, exc = run_job(ms, SCEN_A, new_rows=[[1, 1, u"VALUE_MISMATCH", u"rn"]])
    if exc is not None or res is None or res[u"行の対"] != [[1, 1, 1, u"VALUE_MISMATCH", False, u"UNVERIFIABLE"]]:
        out.append(u"直した engine の行が NR の直した入力の行と違うのに「同じか」が False にならない")
    # 切れない本: 行なし・切り出しの成否が TSS の記録と違えば止まる・切れない本に NR の行が在れば止まる
    res, exc = run_job(ms, SCEN_A, cut=False, new_rows=[], tss_rows=[], nr_rows=[], tss_cut=False)
    if exc is not None or res is None or res.get(u"切れた") is not False or u"行の対" in res:
        out.append(u"切れない本の結果の形が違う")
    for label, kw in ((u"切り出しの成否が TSS の記録と違う", dict(tss_cut=False)), (u"鍵の並びが違う", dict(new_rows=[[1, 2, u"GROUNDED", u"rn"]])), (u"別の本の NR の行", dict(nr_book_n=9))):
        res, exc = run_job(ms, SCEN_A, **kw)
        if not isinstance(exc, ms.Stop):
            out.append(u"%s のに states_job が止まらない(%s)" % (label, type(exc).__name__ if exc is not None else u"通った"))
    res, exc = run_job(ms, SCEN_A, cut=False, new_rows=[], tss_rows=[], tss_cut=False, nr_rows=[[1, 1, 1, u"GROUNDED", u"GROUNDED", True]])
    if not isinstance(exc, ms.Stop):
        out.append(u"切れない本に NR の行が在るのに states_job が止まらない")
    return out


def record_wire_problems(ms=None):
    u"""``build_record`` の配線: 行・本ごとの欄・NRE-1〜NRE-5 が記録の欄に入る・NR の記録と TSS の記録を別の入力として使う・指紋(直した後・直す前)・検出力。"""
    ms = ms or MS
    out = []
    G, UN = u"GROUNDED", u"UNVERIFIABLE"
    old_src = git_blob_text(SEAL_COMMIT_SHORT, INSTANCE_REL)
    if old_src is None:
        return [u"封の commit の instance.py を読めない"]
    tmp = tempfile.mkdtemp(prefix="nre_rec_")
    try:
        files = {1: b"cut-material-1", 2: b"nocut-material-2"}
        shas = dict((n, hashlib.sha256(c).hexdigest()) for n, c in files.items())
        for n, c in files.items():
            with open(os.path.join(tmp, shas[n] + ".zip"), "wb") as fh:
                fh.write(c)
        pop = [(1, u"甲", u"k1", shas[1]), (2, u"甲", u"k2", shas[2])]
        wrapped = example_zip(SCEN_B)
        new_rows = [[1, 1, G, u"rn"], [1, 2, UN, u"rm"]]
        tss_book1 = collections.OrderedDict([(u"#", 1), (u"ZIP の sha256", shas[1]), (u"切り出し", ms.TSS.CUT_OK), (u"行", [[1, 1, UN, u"rt"], [1, 2, UN, u"rm"]])])
        tss_book2 = collections.OrderedDict([(u"#", 2), (u"ZIP の sha256", shas[2]), (u"切り出し", u"切れない"), (u"行", [])])
        fp_was = collections.OrderedDict([(k, u"w" + k) for k in ms.FP_KEYS] + [(u"git_commit", u"g")])
        tss_rec = collections.OrderedDict([(u"profile", u"P33E"), (u"本", [tss_book1, tss_book2]), (u"engine の指紋", fp_was)])
        nr_rec = collections.OrderedDict([(u"profile", u"P33E"), (u"行", [[1, 1, 1, UN, G, False], [1, 1, 2, UN, UN, True]])])
        fp_now = collections.OrderedDict((k, u"n" + k) for k in ms.FP_KEYS)
        fp_was_rec = collections.OrderedDict((k, fp_was[k]) for k in ms.FP_KEYS)
        jb = fake_judge(ms, new_rows)

        def judge_book(n, grp, kind, sha, zb):
            return jb(n, grp, kind, sha, zb) if zb.startswith(b"cut") else fake_judge(ms, [], False)(n, grp, kind, sha, zb)

        tss = ns(ms.TSS, judge_book=judge_book, cut=lambda zb: (u"text", 7, None), wrap=lambda zb, text: (wrapped, 1))
        st = ns(ms.ST, validate_population=lambda p, a, b: p, read_population=lambda root: pop, names_snapshot=lambda d: 0, display_path=lambda p: u"x")
        ts = ns(ms.TS, NF=types.SimpleNamespace(map_pool=lambda f, jobs, procs: [f(j) for j in jobs]))
        nr = ns(ms.NR, check_population=lambda r, p: None, cache_base_dir=lambda: tmp)

        def load_json(p):
            return nr_rec if p.endswith(ms.NR_STATES_REL) else tss_rec if p.endswith(ms.TSS_STATES_REL) else None

        zips = [lambda: example_zip(SCEN_A), lambda: mem_zip([(PD + u"a.xbrl", b"<x/>")])]
        groups = [(u"g1", zips), (u"g2", zips[:1])]

        def run(**over):
            base = dict(TSS=tss, ST=st, TS=ts, NR=nr, load_json=load_json, material_dir=lambda m, o, r: (tmp, True), check_inputs=lambda root: [], engine_fp=lambda t: (fp_now, fp_was_rec))
            base.update(over)
            with patched(ms, **base):
                return ms.build_record(root=tmp, procs=1, material=tmp, out=None, say=lambda *a, **k: None, clock=lambda: 0.0, base=tmp, old_src=old_src, groups=groups)

        try:
            rec = run()
        except BaseException as exc:                      # noqa: BLE001
            return [u"build_record が作り物の入力で落ちた: %s" % type(exc).__name__]
        if rec[u"行"] != [[1, 1, 1, G, True, UN], [1, 1, 2, UN, True, UN]]:
            out.append(u"行が [本の #, 文の番号, 位置, 直した engine の state, NR の直した入力の state と同じか, TSS の state] にならない: %s" % rec[u"行"])
        if rec[K_BOOKS] != [[1, 0, 0, 0, 2, 2, 0, 2]]:
            out.append(u"本ごとの欄が違う: %s" % rec[K_BOOKS])
        b1, b2, b3, b4, b5 = rec[K_NRE1], rec[K_NRE2], rec[K_NRE3], rec[K_NRE4], rec[K_NRE5]
        if (b1[u"切れた本"], b1[u"行の数"], b1[u"NR の直した入力の行と違う行"]) != (1, 2, ms.rate(0, 2)):
            out.append(u"NRE-1 の数が違う: %s" % dict(b1))
        if (b2[u"作られた fact"], b2[u"消えた fact"], b2[u"自己閉じの数(消した数)"]) != (0, 0, 2):
            out.append(u"NRE-2 の数が違う: %s" % dict(b2))
        if b3[u"state が変わった行"] != ms.rate(1, 2) or b3[u"直した engine でだけ値が合う行"] != 1 or b3[u"TSS の記録(直す前)でだけ値が合う行"] != 0:
            out.append(u"NRE-3 の数が違う(TSS の記録の state の側から数えていない疑い): %s" % dict(b3))
        if b4[u"合計"][u"読んだ ZIP の合計"] != 3 or b4[u"合計"][u"facts の列が違う ZIP の合計"] != 2 or b4[u"群ごと"][u"g1"][u"facts の列が違う ZIP"] != 1 or b4[u"群ごと"][u"g2"][u"読んだ ZIP"] != 1:
            out.append(u"NRE-4 の数が群ごとに結ばれていない: %s" % dict(b4[u"合計"]))
        if b5[u"直す前の式の始まり(自己閉じでない)の合計"] != 2 or b5[u"直した式が拾う始まりの合計"] != 2 or b5[u"始まりの位置の集合が違う本"] != 0:
            out.append(u"NRE-5 の数が違う: %s" % dict(b5))
        if rec[u"engine の指紋(直した後)"] != fp_now or rec[u"engine の指紋(直す前。TSS の記録のもの)"] != fp_was_rec:
            out.append(u"指紋(直した後・直す前)の欄が入れ替わっているか違う")
        # NR の記録と TSS の記録を取り違えると数が変わる: NR の行の state を変えると NRE-1 が動き、TSS の行の state を変えると NRE-3 が動く
        nr_bad = collections.OrderedDict(nr_rec)
        nr_bad[u"行"] = [[1, 1, 1, UN, UN, False], [1, 1, 2, UN, UN, True]]
        r2 = None
        with patched(ms, load_json=lambda p: nr_bad if p.endswith(ms.NR_STATES_REL) else tss_rec):
            try:
                r2 = run(load_json=lambda p: nr_bad if p.endswith(ms.NR_STATES_REL) else tss_rec)
            except BaseException as exc:                  # noqa: BLE001
                out.append(u"NR の記録を変えた作り物で build_record が落ちた: %s" % type(exc).__name__)
        if r2 is not None and (r2[K_NRE1][u"NR の直した入力の行と違う行"] != ms.rate(1, 2) or r2[K_NRE3] != b3):
            out.append(u"NRE-1 が NR の記録の行から・NRE-3 が TSS の記録の行から数えられていない(取り違えの疑い)")
        tss_bad_rows = collections.OrderedDict(tss_book1)
        tss_bad_rows[u"行"] = [[1, 1, G, u"rt"], [1, 2, UN, u"rm"]]
        tss_bad = collections.OrderedDict(tss_rec)
        tss_bad[u"本"] = [tss_bad_rows, tss_book2]
        nr_bad2 = collections.OrderedDict(nr_rec)
        nr_bad2[u"行"] = [[1, 1, 1, G, G, False], [1, 1, 2, UN, UN, True]]
        try:
            r3 = run(load_json=lambda p: nr_bad2 if p.endswith(ms.NR_STATES_REL) else tss_bad)
            if r3[K_NRE3][u"state が変わった行"] != ms.rate(0, 2) or r3[K_NRE1] != b1:
                out.append(u"TSS の記録の行を変えたとき NRE-3 だけが動かない(NRE-3 が TSS の記録の行から数えられていない疑い)")
        except BaseException as exc:                      # noqa: BLE001
            out.append(u"TSS の記録を変えた作り物で build_record が落ちた: %s" % type(exc).__name__)
        # 止まり方: 指紋が直す前と同じ・profile 違い
        try:
            ms.engine_fp(collections.OrderedDict([(u"engine の指紋", collections.OrderedDict((k, ms.VD.engine_fingerprint()[k]) for k in ms.FP_KEYS))]))
            out.append(u"直す前の指紋が今の engine と同じなのに engine_fp が止まらない")
        except ms.Stop:
            pass
        bad_profile = collections.OrderedDict(nr_rec)
        bad_profile[u"profile"] = u"P27"
        try:
            run(load_json=lambda p: bad_profile if p.endswith(ms.NR_STATES_REL) else tss_rec)
            out.append(u"NR の記録の profile が違うのに build_record が止まらない")
        except ms.Stop:
            pass
        except BaseException as exc:                      # noqa: BLE001
            out.append(u"profile 違いで Stop でない例外 %s" % type(exc).__name__)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def input_wire_problems(ms=None):
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="nre_inp_")
    try:
        for rel in INPUT_RELS:
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(ROOT, rel), dst)
        try:
            if len(ms.check_inputs(tmp)) != 8:
                out.append(u"入力が 8 つ返らない")
        except BaseException as exc:                      # noqa: BLE001
            out.append(u"変えない入力で止まった: %s" % type(exc).__name__)
        for i in (0, 6, 7):                                 # 母集団・NR の script・NR の記録(1 byte 変える)
            with open(os.path.join(tmp, INPUT_RELS[i]), "ab") as fh:
                fh.write(b" ")
            try:
                ms.check_inputs(tmp)
                out.append(u"入力 %d の sha256 が違うのに止まらない" % (i + 1))
            except ms.Stop:
                pass
            shutil.copyfile(os.path.join(ROOT, INPUT_RELS[i]), os.path.join(tmp, INPUT_RELS[i]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


# ---------------------------------------------------------------- 6. 記録
def walk(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield path + (k,), v
            for x in walk(v, path + (k,)):
                yield x
    elif isinstance(o, list):
        for n, v in enumerate(o):
            for x in walk(v, path + (n,)):
                yield x


def leak_problems(text):
    u"""記録に文・span・値・要素名・context・会社名・docID が無い(禁止の欄の名前・字の形)。行は [int, int, int, state, bool, state]。"""
    out = []
    try:
        rec = json.loads(text)
    except ValueError:
        return [u"記録が JSON でない"]
    for p, v in walk(rec):
        if p and isinstance(p[-1], str) and p[-1] in (u"文", u"span", u"sentence", u"値", u"要素名", u"context", u"name", u"会社名", u"証券コード", u"docID", u"value", u"text", u"数"):
            out.append(u"記録に持たない欄が在る: %s" % (p[-1],))
    if DOCID_RE.search(text) or re.search(r"0812\d{14}", text):
        out.append(u"docID・TDnet の番号らしい字が在る")
    for r in rec.get(u"行", []):
        if len(r) != 6 or not all(isinstance(x, int) and not isinstance(x, bool) for x in r[:3]) or r[3] not in STATES or not isinstance(r[4], bool) or r[5] not in STATES:
            out.append(u"行の形が決めと違う")
            break
    for r in rec.get(K_BOOKS, []):
        if len(r) != 8 or not all(isinstance(x, int) and not isinstance(x, bool) and x >= 0 for x in r):
            out.append(u"本ごとの欄の形が決めと違う")
            break
    return out


def rate_text_problems(rec):
    out = []
    n_seen = 0
    for p, v in walk(rec):
        if isinstance(v, dict) and set(v) == {u"分子", u"分母", u"率"}:
            n_seen += 1
            n, d, t = v[u"分子"], v[u"分母"], v[u"率"]
            if not (isinstance(n, int) and isinstance(d, int) and 0 <= n <= d) or not RATE_TEXT.match(t):
                out.append(u"率の欄の形が決めと違う: %s" % (p,))
                continue
            want = u"分母 0" if d == 0 else u"%d.%d%%" % divmod(int(Fraction(n, d) * 1000 + Fraction(1, 2)), 10)
            if t != want:
                out.append(u"率の字が分子・分母から出る字と違う: %s %s" % (p, t))
    if n_seen < 4:
        out.append(u"率の欄が少なすぎる(%d)" % n_seen)
    return out


def load_json(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh, object_pairs_hook=collections.OrderedDict)


def record_problems(ms=None, text=None):
    ms = ms or MS
    out = []
    p = os.path.join(ROOT, RECORD_REL)
    if text is None:
        if not os.path.isfile(p):
            return [u"記録が無い"]
        with open(p, encoding="utf-8", newline="") as fh:
            text = fh.read()
    out.extend(leak_problems(text))
    try:
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    except ValueError:
        return out + [u"記録が JSON でない"]
    out.extend(rate_text_problems(rec))
    if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"記録の封の path・commit が違う")
    if rec.get(u"この script の sha256") != sha_of(SCRIPT_REL):
        out.append(u"記録の script の sha256 が実物と違う")
    if [(i[u"path"], i[u"sha256"]) for i in rec.get(u"入力", [])] != list(INPUT_SHAS) or any(sha_of(rel) != sha for rel, sha in INPUT_SHAS):
        out.append(u"記録の入力が表・実物と違う")
    tss, nr = load_json(TSS_RECORD_REL), load_json(NR_RECORD_REL)
    was = collections.OrderedDict((k, tss[u"engine の指紋"][k]) for k in ms.FP_KEYS)
    if rec.get(u"engine の指紋(直す前。TSS の記録のもの)") != was:
        out.append(u"記録の直す前の指紋が TSS の記録の指紋と違う")
    now = rec.get(u"engine の指紋(直した後)")
    if now is None or list(now) != list(ms.FP_KEYS) or now == was:
        out.append(u"記録の直した後の指紋が直す前と同じか、欄が違う")
    if rec.get(u"profile") != u"P33E" or rec.get(u"key_leaks") != []:
        out.append(u"profile か key_leaks が違う")
    if rec.get(u"直した式(封 §1)") != collections.OrderedDict([(u"前", ms.OLD_FACT_RE_SRC), (u"後", ms.NEW_FACT_RE_SRC)]) or "r'%s'" % rec[u"直した式(封 §1)"][u"後"] != FORMULA_AFTER:
        out.append(u"記録の式が封 §1 と違う")
    if tuple(rec.get(u"行の欄", ())) != tuple(ms.ROW_COLUMNS) or tuple(rec.get(u"本ごとの欄", ())) != tuple(ms.BOOK_COLUMNS):
        out.append(u"行の欄・本ごとの欄が違う")
    rows = rec.get(u"行", [])
    books = rec.get(K_BOOKS, [])
    keys = [(r[0], r[1], r[2]) for r in rows]
    nr_keys = [(r[0], r[1], r[2]) for r in nr[u"行"]]
    if keys != nr_keys:
        out.append(u"行の鍵の並びが NR の記録の行の鍵と同じでない")
    tss_cut = [b for b in tss[u"本"] if b[u"切り出し"] == u"切れた"]
    tss_keys = [(b[u"#"], r[0], r[1]) for b in tss_cut for r in b[u"行"]]
    if keys != tss_keys:
        out.append(u"行の鍵の並びが TSS の記録の行の鍵と同じでない")
    if [r[5] for r in rows] != [x[2] for b in tss_cut for x in b[u"行"]] or [r[5] for r in rows] != [x[3] for x in nr[u"行"]]:
        out.append(u"行の TSS の state の列が TSS の記録・NR の記録の「そのまま」の state の列と同じでない")
    if [b[0] for b in books] != [b[u"#"] for b in tss_cut]:
        out.append(u"本ごとの欄の本が TSS の切れた本とそろわない")
    # 本ごとの欄の NRE-1 の列 = 行の「同じか」が False の数
    for b in books:
        if sum(1 for r in rows if r[0] == b[0] and not r[4]) != b[1]:
            out.append(u"本ごとの欄の NRE-1 で違う行が行からの数え直しと違う(#%d)" % b[0])
            break
    if any(b[6] not in (0, 1) for b in books):
        out.append(u"本ごとの欄の「位置の集合が違う」が 0・1 でない")
    changed = [r for r in rows if r[5] != r[3]]
    b1, b2, b3, b4, b5 = rec.get(K_NRE1, {}), rec.get(K_NRE2, {}), rec.get(K_NRE3, {}), rec.get(K_NRE4, {}), rec.get(K_NRE5, {})
    bad = [r for r in rows if not r[4]]
    if (b1.get(u"切れた本"), b1.get(u"行の数"), b1.get(u"NR の直した入力の行と違う行"), b1.get(u"NR の直した入力の行と違う行を持つ本"), b1.get(u"NR の直した入力の行と同じ本")) != (
            len(books), len(rows), ms.rate(len(bad), len(rows)), len(set(r[0] for r in bad)), len(books) - len(set(r[0] for r in bad))):
        out.append(u"NRE-1 の数が行・本ごとの欄からの数え直しと違う")
    if (b2.get(u"切れた本"), b2.get(u"作られた fact"), b2.get(u"消えた fact"), b2.get(u"作られた fact を持つ本"), b2.get(u"消えた fact を持つ本")) != (
            len(books), sum(b[2] for b in books), sum(b[3] for b in books), sum(1 for b in books if b[2] > 0), sum(1 for b in books if b[3] > 0)):
        out.append(u"NRE-2 の数が本ごとの欄からの数え直しと違う")
    trans = collections.Counter((r[5], r[3]) for r in rows)
    t = b3.get(u"state の移り変わり(TSS の記録 → 直した engine)", {})
    if t != collections.OrderedDict((u"%s → %s" % (a, b), trans.get((a, b), 0)) for a in STATES for b in STATES) or sum(t.values()) != len(rows):
        out.append(u"NRE-3 の移り変わりの表が行からの数え直しと違う")
    if b3.get(u"state が変わった行") != ms.rate(len(changed), len(rows)) or b3.get(u"state が変わった行を持つ本") != len(set(r[0] for r in changed)) \
            or b3.get(u"state が変わった行を持つ本の #") != sorted(set(r[0] for r in changed)) or b3.get(u"行の数") != len(rows):
        out.append(u"NRE-3 の state が変わった行・本が行からの数え直しと違う")
    if b3.get(u"直した engine でだけ値が合う行") != sum(1 for r in rows if r[5] != u"GROUNDED" and r[3] == u"GROUNDED") \
            or b3.get(u"TSS の記録(直す前)でだけ値が合う行") != sum(1 for r in rows if r[5] == u"GROUNDED" and r[3] != u"GROUNDED"):
        out.append(u"NRE-3 の 2 方向の数が行からの数え直しと違う")
    # NRE-4: 群ごと
    per4 = b4.get(u"群ごと", {})
    if list(per4)[:4] != list(ms.EDINET_FOLDERS) or [per4[k][u"読んだ ZIP"] for k in ms.EDINET_FOLDERS] != list(ms.EDINET_FOLDERS.values()):
        out.append(u"NRE-4 の EDINET の folder の ZIP の数が封(便 NR の棚卸し)の数と違う")
    if len(per4) != 6 or any(per4[k][u"読んだ ZIP"] != ms.N_0911 for k in list(per4)[4:]):
        out.append(u"NRE-4 の 2026-11-09 の便の ZIP の数が 17 でない")
    tot = b4.get(u"合計", {})
    if tot != ms.nre4_total(per4) or any(len(v[u"facts の列が違う ZIP の番号(群の中の順)"]) != v[u"facts の列が違う ZIP"] or v[u"返り値の全体が違う ZIP"] < v[u"facts の列が違う ZIP"] for v in per4.values()):
        out.append(u"NRE-4 の合計・違う ZIP の番号の数が群ごとの数と合わない")
    if (b5.get(u"包んだ本"), b5.get(u"直す前の式の始まり(自己閉じでない)の合計"), b5.get(u"直した式が拾う始まりの合計"), b5.get(u"始まりの位置の集合が違う本"), b5.get(u"始まりの数が違う本"),
            b5.get(u"直した式が finditer で拾う数の合計")) != (len(books), sum(b[4] for b in books), sum(b[5] for b in books), sum(b[6] for b in books), sum(1 for b in books if b[4] != b[5]),
                                                                    sum(b[7] for b in books)):
        out.append(u"NRE-5 の数が本ごとの欄からの数え直しと違う")
    pr = rec.get(K_PRED, {})
    if pr != ms.prediction_numbers(b1, b2, b3, tot, b5):
        out.append(u"予測の判定に要る数が各欄からの作り直しと違う")
    # 「0」の疑い: 行が在り・本が在り・NR の記録と同じ行数・読んだ ZIP が在る・直す前の式の始まりが在る
    if not (len(rows) > 20000 and len(books) == 372 and tot.get(u"読んだ ZIP の合計", 0) > 400 and b5.get(u"直す前の式の始まり(自己閉じでない)の合計", 0) > 0):
        out.append(u"行・本・読んだ ZIP・始まりの数が少なすぎる(測定が空回りしている疑い)")
    return out


# ---------------------------------------------------------------- 7. 配線
def import_problems(src=None):
    u"""script の import は標準ライブラリの一覧だけ(engine の module は便 NR の script が読む)。通信を import しない(ast)。subprocess は ``git show`` の 1 か所だけ。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"")]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "eval"):
            out.append(u"動的な import・eval の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK_MODULES:
                out.append(u"通信の module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess"]
    if len(calls) != 1 or calls[0].func.attr != "check_output" or not (calls[0].args and isinstance(calls[0].args[0], ast.List) and len(calls[0].args[0].elts) >= 5
                                                                       and isinstance(calls[0].args[0].elts[0], ast.Constant) and calls[0].args[0].elts[0].value == "git"
                                                                       and isinstance(calls[0].args[0].elts[3], ast.Constant) and calls[0].args[0].elts[3].value == "show"):
        out.append(u"subprocess の呼びが ``git ... show`` の check_output 1 か所だけでない")
    execs = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "exec"]
    if len(execs) != 1:
        out.append(u"exec の呼びが旧い blob を読む 1 か所だけでない(%d)" % len(execs))
    return out


def reserved_problems(rel=GATE_REL, base=ROOT):
    out = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(re.match(r"%s\w*\s*=" % re.escape(p), line) for p in RESERVED_PREFIXES):
            out.append(u"%s:%d が既存の門の数える名前を行頭に置いている" % (rel, n))
    return out


# ---------------------------------------------------------------- 変異(script)
#: (名前, script の中の字 old, new, 赤になるはずの検査の名前の並び)。old は script に 1 回だけ在る字
MUTANTS = (
    (u"M01 直した式の写し(後)を直す前の式にする", u"NEW_FACT_RE_SRC = r'<ix:nonFraction([^>]*)(?<!/)>(.*?)</ix:nonFraction>'", u"NEW_FACT_RE_SRC = r'<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>'", ("seal", "start")),
    (u"M02 直した式の写しの lookbehind を (?<!\\s) にする", u"NEW_FACT_RE_SRC = r'<ix:nonFraction([^>]*)(?<!/)>(.*?)</ix:nonFraction>'", u"NEW_FACT_RE_SRC = r'<ix:nonFraction([^>]*)(?<!\\s)>(.*?)</ix:nonFraction>'", ("seal", "start")),
    (u"M03 直す前の式の写しを直した式にする", u"OLD_FACT_RE_SRC = r'<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>'", u"OLD_FACT_RE_SRC = r'<ix:nonFraction([^>]*)(?<!/)>(.*?)</ix:nonFraction>'", ("seal", "start")),
    (u"M04 旧い instance.py の sha16 の定数を替える", u'OLD_INSTANCE_SHA16 = "f2d9e040f19adebf"', u'OLD_INSTANCE_SHA16 = "f2d9e040f19adebe"', ("seal", "old")),
    (u"M05 封の commit の定数を替える", u'SEAL_COMMIT = "36ca78f1"', u'SEAL_COMMIT = "36ca78f2"', ("seal",)),
    (u"M06 EDINET の folder の数を 1 つ替える", u'("edinet", 281)', u'("edinet", 282)', ("seal",)),
    (u"M07 入力の表の 1 つの sha256 を替える", u'"4ed60b591366dd65a431dba5348aff6edb3889676d8e9a4154a5b0298486f7f9"', u'"5ed60b591366dd65a431dba5348aff6edb3889676d8e9a4154a5b0298486f7f9"', ("input_sha", "wire_inputs")),
    (u"M08 入力の sha256 の照合を外す", u"if not os.path.isfile(p) or ST.sha256_file(p) != want:", u"if False:", ("wire_inputs",)),
    (u"M09 直す前の式の側で自己閉じの一致も数える", u"for p, selfc in start_positions(raw, OLD_FACT_RE) if not selfc)", u"for p, selfc in start_positions(raw, OLD_FACT_RE))", ("start",)),
    (u"M10 直した式の側で自己閉じの一致を除く(式が自己閉じを拾っても違いに出ない)", u"for p, _selfc in start_positions(raw, NEW_FACT_RE))", u"for p, _selfc in start_positions(raw, NEW_FACT_RE) if not _selfc)", ("start",)),
    (u"M11 始まりの位置を finditer で数える(位置ごとに当てない)", u"        old_set.update((i, p) for p, selfc in start_positions(raw, OLD_FACT_RE) if not selfc)\n        new_set.update((i, p) for p, _selfc in start_positions(raw, NEW_FACT_RE))",
     u"        old_set.update((i, m.start()) for m in OLD_FACT_RE.finditer(raw))\n        new_set.update((i, m.start()) for m in NEW_FACT_RE.finditer(raw))", ("start",)),
    (u"M12 始まりの位置に member の番号を入れない(member をまたいで重なる)", u"        old_set.update((i, p) for p, selfc in start_positions(raw, OLD_FACT_RE) if not selfc)", u"        old_set.update((0, p) for p, selfc in start_positions(raw, OLD_FACT_RE) if not selfc)", ("start",)),
    (u"M13 位置の集合が違うを数にしない(常に 0)", u"return len(old_set), len(new_set), 1 if old_set != new_set else 0, nfind", u"return len(old_set), len(new_set), 0, nfind", ("start",)),
    (u"M13b 直した式が finditer で拾う数を数えない", u"        nfind += len(NEW_FACT_RE.findall(raw))", u"        nfind += 0", ("start",)),
    (u"M13c start_positions が一致の位置でなく探した位置を返す", u"            out.append((p, m.group(1).endswith(\"/\")))", u"            out.append((p + 1, m.group(1).endswith(\"/\")))", ("start",)),
    (u"M13d start_positions が自己閉じかの見方を逆にする", u"            out.append((p, m.group(1).endswith(\"/\")))", u"            out.append((p, not m.group(1).endswith(\"/\")))", ("start",)),
    (u"M13e EDINET の folder の数の確かめを外す", u"        if counts.get(name) != want:", u"        if False:", ("material",)),
    (u"M13f 2026-11-09 の便の数の確かめを外す", u"    if n_0911 != N_0911:", u"    if False:", ("material",)),
    (u"M14 旧い blob の sha16 の確かめを外す", u"    if hashlib.sha256(src_bytes).hexdigest()[:16] != OLD_INSTANCE_SHA16:", u"    if False:", ("old",)),
    (u"M15 旧い engine の module を sys.modules に登録する", u"    mod.__file__ = os.path.join(ROOT, INSTANCE_REL)\n    exec(", u"    mod.__file__ = os.path.join(ROOT, INSTANCE_REL)\n    sys.modules[mod.__name__] = mod\n    exec(", ("old",)),
    (u"M16 compare_zip で旧い engine と今の engine を同じ module にする", u"    a, b = old_mod.load_instance(zb), new_mod.load_instance(zb)", u"    a, b = new_mod.load_instance(zb), new_mod.load_instance(zb)", ("old", "wire_rec")),
    (u"M17 compare_zip が facts でなく contexts を比べる", u'    return a["facts"] == b["facts"], a == b,', u'    return a["contexts"] == b["contexts"], a == b,', ("old",)),
    (u"M18 compare_zip の経路の見方を .htm にする", u"NR.route_of(zb) == NR.ROUTE_XBRL", u"NR.route_of(zb) == NR.ROUTE_HTM", ("old",)),
    (u"M19 nre4_block が違う ZIP の数を数えない", u"            diff += 0 if same else 1\n", u"            diff += 0\n", ("old", "wire_rec")),
    (u"M20 nre4_block が全体の違いを facts の違いで数える", u"            diff_all += 0 if same_all else 1\n", u"            diff_all += 0 if same else 1\n", ("old",)),
    (u"M21 nre4_block が .xbrl でない ZIP を数えない", u"            non_xbrl += 0 if xb else 1\n", u"            non_xbrl += 0\n", ("old",)),
    (u"M22 nre4_total の合計を 1 群だけにする", u'(u"読んだ ZIP の合計", sum(v[u"読んだ ZIP"] for v in per.values())),', u'(u"読んだ ZIP の合計", list(per.values())[0][u"読んだ ZIP"]),', ("old",)),
    (u"M23 行の対の「同じか」が reason の比べを外す", u"        same = rn[2] == rr[4] and ((rn[3] == rt[3]) == rr[5])", u"        same = rn[2] == rr[4]", ("pair",)),
    (u"M24 行の対の「同じか」が state の比べを外す", u"        same = rn[2] == rr[4] and ((rn[3] == rt[3]) == rr[5])", u"        same = ((rn[3] == rt[3]) == rr[5])", ("pair",)),
    (u"M25 行の対が NR の「直した入力」でなく「そのまま」の state と比べる", u"        same = rn[2] == rr[4] and ((rn[3] == rt[3]) == rr[5])", u"        same = rn[2] == rr[3] and ((rn[3] == rt[3]) == rr[5])", ("pair", "wire_job")),
    (u"M26 行の対が TSS の state でなく直した engine の state を末尾に入れる", u"        out.append([n, rn[0], rn[1], rn[2], bool(same), rt[2]])", u"        out.append([n, rn[0], rn[1], rn[2], bool(same), rn[2]])", ("pair", "wire_job")),
    (u"M27 行の対の末尾に NR の「そのまま」の state を入れる(TSS の記録でない)", u"        out.append([n, rn[0], rn[1], rn[2], bool(same), rt[2]])", u"        out.append([n, rn[0], rn[1], rn[2], bool(same), rn[2]])", ("pair",)),
    (u"M28 鍵の並びの確かめで NR の鍵を見ない", u" or k_new != [(r[1], r[2]) for r in nr_rows] or any(r[0] != n for r in nr_rows):", u":", ("pair",)),
    (u"M29 鍵の並びの確かめで TSS の鍵を見ない", u"    if k_new != [row_key(r) for r in tss_rows]", u"    if False", ("pair",)),
    (u"M30 NR の「そのまま」と TSS の state の確かめを外す", u"        if rt[2] != rr[3]:", u"        if False:", ("pair",)),
    (u"M31 NRE-1 の違う行を数えない(同じを数える)", u"sum(1 for r in b[u\"行の対\"] if not r[4])", u"sum(1 for r in b[u\"行の対\"] if r[4])", ("blocks", "wire_rec")),
    (u"M32 作られた fact と消えた fact を取り違える", u'        made, gone, _swap = b[u"fact の差"]\n        old_n', u'        gone, made, _swap = b[u"fact の差"]\n        old_n', ("blocks",)),
    (u"M33 NRE-3 の移り変わりを(直した engine → TSS)の向きにする", u"c = collections.Counter((r[5], r[3]) for r in rows)", u"c = collections.Counter((r[3], r[5]) for r in rows)", ("blocks",)),
    (u"M34 NRE-3 の直した engine でだけ合う行の向きを逆にする", u"only_new = [r for r in rows if r[5] != STATE_G and r[3] == STATE_G]", u"only_new = [r for r in rows if r[5] == STATE_G and r[3] != STATE_G]", ("blocks",)),
    (u"M35 NRE-3 の直す前でだけ合う行の向きを逆にする", u"only_old = [r for r in rows if r[5] == STATE_G and r[3] != STATE_G]", u"only_old = [r for r in rows if r[5] != STATE_G and r[3] == STATE_G]", ("blocks",)),
    (u"M36 NRE-3 の state が変わった行を行の NR の同じかで数える", u"changed = [r for r in rows if r[5] != r[3]]", u"changed = [r for r in rows if not r[4]]", ("blocks", "wire_rec")),
    (u"M37 NRE-3 の state が変わった行を持つ本を行の数にする", u'(u"state が変わった行を持つ本", len(books))', u'(u"state が変わった行を持つ本", len(changed))', ("blocks",)),
    (u"M38 NRE-5 の始まりの数が違う本を位置の集合が違う本で数える", u"(u\"始まりの数が違う本\", sum(1 for p in per if p[4] != p[5]))", u"(u\"始まりの数が違う本\", sum(1 for p in per if p[6]))", ("blocks",)),
    (u"M39 NRE-2 の独立の読みと同じ本を数えない", u'sum(1 for b in cut if b[u"独立の読みと同じ"])', u"len(cut)", ("blocks",)),
    (u"M40 予測の数の NRE-4 の分子を読んだ ZIP にする", u'(u"分子", b4[u"facts の列が違う ZIP の合計"])', u'(u"分子", b4[u"読んだ ZIP の合計"])', ("blocks",)),
    (u"M41 率の分子と分母を入れ替える", u"    return NR.rate(n, d)", u"    return NR.rate(d, n)", ("rate",)),
    (u"M42 states_job が fact の差を(自己閉じを消した入力, そのまま)の順で数える", u"made, gone, swap = NR.fact_diff(c_asis, c_fixed)", u"made, gone, swap = NR.fact_diff(c_fixed, c_asis)", ("wire_job",)),
    (u"M43 states_job が直した入力の fact を包んだままから作る", u"c_asis, c_fixed = NR.engine_counter(wrapped), NR.engine_counter(fixed_zb)", u"c_asis, c_fixed = NR.engine_counter(wrapped), NR.engine_counter(wrapped)", ("wire_job",)),
    (u"M44 states_job が自己閉じを消さずに包んだままを渡す", u"    fixed_zb, nil = NR.fix_zip(wrapped)", u"    fixed_zb, nil = wrapped, NR.fix_zip(wrapped)[1]", ("wire_job",)),
    (u"M45 states_job が独立の読みを自己閉じを消した入力の engine の読みと比べる", u'res[u"独立の読みと同じ"] = NR.independent_counter(wrapped) == c_asis', u'res[u"独立の読みと同じ"] = NR.independent_counter(wrapped) == c_fixed', ("wire_job",)),
    (u"M46 states_job が始まりの位置を直した入力から数える", u'res[u"始まり"] = start_block(wrapped)', u'res[u"始まり"] = start_block(fixed_zb)', ("wire_job",)),
    (u"M47 states_job が行の対に TSS の記録の行を使わず直した engine の行を 2 度渡す", u'pair_book(n, book[u"行"], tss_book[u"行"], nr_rows)', u'pair_book(n, book[u"行"], book[u"行"], nr_rows)', ("wire_job", "wire_rec")),
    (u"M48 states_job が行の対の引数の順を入れ替える(TSS の行と直した engine の行)", u'pair_book(n, book[u"行"], tss_book[u"行"], nr_rows)', u'pair_book(n, tss_book[u"行"], book[u"行"], nr_rows)', ("wire_job", "wire_rec")),
    (u"M49 states_job が本の番号をずらして行の対を作る", u'    res[u"行の対"] = pair_book(n, book[u"行"], tss_book[u"行"], nr_rows)', u'    res[u"行の対"] = pair_book(n + 1, book[u"行"], tss_book[u"行"], nr_rows)', ("wire_job",)),
    (u"M50 states_job が切り出しの成否の確かめを外す", u"    if cut != (tss_book[u\"切り出し\"] == TSS.CUT_OK):", u"    if False:", ("wire_job",)),
    (u"M51 states_job が切れない本に NR の行が在っても止めない", u"        if nr_rows:\n            raise Stop", u"        if False:\n            raise Stop", ("wire_job",)),
    (u"M52 build_record が NR の記録を TSS の記録の path から読む", u"    nr_rec = load_json(os.path.join(root, NR_STATES_REL))", u"    nr_rec = load_json(os.path.join(root, TSS_STATES_REL))", ("wire_rec",)),
    (u"M53 build_record が TSS の記録を NR の記録の path から読む", u"    tss_rec = load_json(os.path.join(root, TSS_STATES_REL))", u"    tss_rec = load_json(os.path.join(root, NR_STATES_REL))", ("wire_rec",)),
    (u"M54 build_record が指紋(直した後・直す前)を入れ替える", u'rec[u"engine の指紋(直した後)"] = fp_now', u'rec[u"engine の指紋(直した後)"] = fp_was', ("wire_rec",)),
    (u"M55 engine_fp が直す前と同じ指紋でも止めない", u"    if now == was:", u"    if False:", ("wire_rec",)),
    (u"M56 build_record が NR の記録の profile を見ない", u"    if tss_rec[u\"profile\"] != PROFILE or nr_rec[u\"profile\"] != PROFILE:", u"    if tss_rec[u\"profile\"] != PROFILE:", ("wire_rec",)),
    (u"M57 build_record が NRE-4 の旧い engine を今の engine にする", u"    per4 = nre4_block(old_mod, I, groups)", u"    per4 = nre4_block(I, I, groups)", ("wire_rec",)),
    (u"M58 build_record が NRE-4 の旧い engine の代わりに今の engine を渡す", u"    per4 = nre4_block(old_mod, I, groups)", u"    per4 = nre4_block(I, I, groups)", ("wire_rec",)),
    (u"M59 build_record が NRE-1 に TSS の行を使う(NR の行の数を使わない)", u"    b1, b2, b3, b5 = nre1_block(rows, per), nre2_block(per, books), nre3_block(rows), nre5_block(per)", u"    b1, b2, b3, b5 = nre1_block(rows, per), nre2_block(per, books), nre3_block([[r[0], r[1], r[2], r[3], True, r[3]] for r in rows]), nre5_block(per)", ("wire_rec",)),
    (u"M60 通信の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport urllib.request\n", ("import",)),
    (u"M61 許す一覧の外の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport shutil\n", ("import",)),
    (u"M62 subprocess の呼びを増やす(行を足す)", u"import argparse\n", u"import argparse\nimport subprocess\nsubprocess.run(['git'])\n", ("import",)),
)


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"input_sha": input_sha_problems, u"start": start_problems, u"pair": pair_problems, u"blocks": block_problems, u"old": old_engine_problems,
             u"rate": rate_problems_fn, u"material": material_problems, u"wire_job": job_wire_problems, u"wire_rec": record_wire_problems, u"wire_inputs": input_wire_problems}
    if name in table:
        return table[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


def run_mutants():
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in MUTANTS:
        assert base.count(old) == 1, (name, base.count(old))
        src = base.replace(old, new)
        try:
            mod = load_source(src)
        except BaseException as exc:                # noqa: BLE001
            out.append((name, [(c, True) for c in checks], u"読めない: %s" % type(exc).__name__))
            continue
        res = [(c, bool(guard(check_by_name, c, mod, src))) for c in checks]
        sys.modules.pop("old_instance_for_nil_read_engine", None)       # 変異が登録した module を次の変異・検査に残さない
        out.append((name, res, u""))
    return out


# ---------------------------------------------------------------- 変異(engine の式・差分・履歴の作り物)
def engine_text():
    return read(INSTANCE_REL)


def engine_mutants():
    u"""(名前, 作った字, 赤になるはずの検査)。engine の file は書き換えない(字の写しを変える)。"""
    src = engine_text()
    out = [
        (u"E01 式を直す前の字に戻す", src.replace(FORMULA_AFTER, FORMULA_BEFORE), "formula"),
        (u"E02 lookbehind を (?<!\\s) にする", src.replace("(?<!/)", "(?<!\\s)"), "formula"),
        (u"E03 lookbehind を外す(式は前と同じ字)", src.replace("(?<!/)", ""), "formula"),
        (u"E04 lookbehind を肯定にする", src.replace("(?<!/)", "(?<=/)"), "formula"),
        (u"E05 属性の並びの手前に lookbehind を置く", src.replace("([^>]*)(?<!/)>", "(?<!/)([^>]*)>"), "formula"),
        (u"E06 lookbehind の字を別の文字にする", src.replace("(?<!/)", "(?<!>)"), "formula"),
        (u"E07 式の中身(値の部分)を替える", src.replace("(.*?)</ix:nonFraction>'", "(.+?)</ix:nonFraction>'"), "formula"),
    ]
    old_src = git_blob_text(SEAL_COMMIT_SHORT, INSTANCE_REL)
    if old_src is not None:
        o = old_src.decode("utf-8")
        out.extend([
            (u"D01 式の行のほかに 1 行足す", src + "\nx = 1\n", "diff"),
            (u"D02 式の行のほかの 1 行を替える", src.replace("def strip_html(s):", "def strip_html(t):", 1), "diff"),
            (u"D03 式を替えずに旧い字のまま", o, "diff"),
            (u"D04 置き換えが「後」の字でなく別の式", o.replace(FORMULA_BEFORE, FORMULA_AFTER.replace("(?<!/)", "(?<!\\s)")), "diff"),
        ])
    return out


def engine_mutant_problems(kind, text, old_src):
    if kind == "formula":
        return engine_formula_problems(text)
    return engine_diff_problems(old_src, text)


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_tables_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"前: r'<ix:nonFraction([^>]*)>", u"前: r'<ix:nonFraction([^>]+)>", 1)))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"(?<!/)", u"(?<!\\s)")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"NRE-7", u"NRE-8")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"挿入 1・削除 1", u"挿入 2・削除 1")))


class InputTest(unittest.TestCase):
    def test_b_1_the_inputs_have_the_pinned_sha256(self):
        self.assertEqual([], input_sha_problems())

    def test_b_2_the_input_check_stops_on_a_changed_byte(self):
        self.assertEqual([], input_wire_problems())


class EngineFormulaTest(unittest.TestCase):
    def test_c_1_the_engine_formula_is_the_sealed_after_form_and_behaves_as_sealed(self):
        self.assertEqual([], engine_formula_problems())

    def test_c_2_the_engine_differs_from_the_sealed_blob_in_the_one_formula_line_only(self):
        self.assertEqual([], real_diff_problems())

    def test_c_3_the_engine_sha16_is_the_declared_value(self):
        self.assertEqual([], sha16_problems())

    def test_c_4_every_engine_mutation_is_red(self):
        old_src = git_blob_text(SEAL_COMMIT_SHORT, INSTANCE_REL).decode("utf-8")
        silent = []
        for name, text, kind in engine_mutants():
            if not guard(engine_mutant_problems, kind, text, old_src):
                silent.append(name)
        self.assertEqual([], silent)
        self.assertEqual([], engine_formula_problems(read(INSTANCE_REL)))
        self.assertEqual([], engine_diff_problems(old_src, read(INSTANCE_REL)))

    def test_c_5_the_formula_behavior_check_sees_the_old_formula(self):
        self.assertNotEqual([], formula_behavior_problems(FORMULA_BEFORE[2:-1]))
        self.assertEqual([], formula_behavior_problems(FORMULA_AFTER[2:-1]))
        self.assertNotEqual([], formula_behavior_problems(FORMULA_AFTER[2:-1].replace("(?<!/)", "(?<!\\s)")))


class EngineHistoryTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_engine_commit_with_one_insertion_and_one_deletion(self):
        u"""engine の commit が履歴に無い(未 commit)ときは赤。commit の後で初めて緑。"""
        self.assertEqual([], real_numstat_problems())

    def test_d_2_the_working_tree_has_no_uncommitted_engine_change(self):
        self.assertEqual([], engine_worktree_problems())

    def test_d_3_numstat_mutations_turn_it_red(self):
        good = ["1\t1\t%s%s" % (PREFIX, INSTANCE_REL)]
        self.assertEqual([], numstat_problems(good))
        for bad in ([], good + ["1\t0\t%sadapters/xbrl/recipes.py" % PREFIX], ["2\t1\t%s%s" % (PREFIX, INSTANCE_REL)], ["1\t2\t%s%s" % (PREFIX, INSTANCE_REL)],
                    ["1\t0\t%s%s" % (PREFIX, INSTANCE_REL)], ["1\t1\t%sadapters/xbrl/recipes.py" % PREFIX], ["1\t1\t%score/py/audit_core/x.py" % PREFIX], good + good):
            self.assertNotEqual([], numstat_problems(bad), bad)

    def _repo(self, extra_engine=False, files=("adapters/xbrl/instance.py",), after_engine_line=False):
        r = PR.Repo()
        r.put(SEAL_REL)
        r.put(INSTANCE_REL, text=u"")
        r.put("adapters/xbrl/recipes.py", text=u"")
        seal = r.commit(SEAL_REL, INSTANCE_REL, "adapters/xbrl/recipes.py")
        for f in files:
            r.put(f, text=u"")
        r.commit(*files)
        return r, seal

    def test_d_4_the_engine_commit_is_found_from_history_and_checked_on_a_made_up_repo(self):
        r, seal = self._repo()
        s, e = engine_commit(r.d, PREFIX, SEAL_REL, ENGINE_FILES)
        self.assertTrue(s == seal and e and e != s)
        self.assertEqual([], real_numstat_problems(root=r.d))

    def test_d_5_a_made_up_repo_with_the_wrong_engine_change_is_red(self):
        r, seal = self._repo(files=("adapters/xbrl/instance.py", "adapters/xbrl/recipes.py"))
        self.assertNotEqual([], real_numstat_problems(root=r.d))                      # recipes.py も触った
        r2 = PR.Repo()
        r2.put(SEAL_REL)
        r2.commit(SEAL_REL)
        self.assertNotEqual([], real_numstat_problems(root=r2.d))                     # engine の commit が無い(未 commit)
        r3 = PR.Repo()
        r3.put(SEAL_REL)
        r3.put(INSTANCE_REL, text=u"")
        r3.commit(SEAL_REL, INSTANCE_REL)
        r3.put(INSTANCE_REL, text=u"a\nb\nc\n")
        r3.commit(INSTANCE_REL)
        self.assertNotEqual([], real_numstat_problems(root=r3.d))                     # 3 行の置き換え

    def test_d_6_the_working_tree_check_sees_an_uncommitted_engine_change(self):
        r, seal = self._repo()
        self.assertEqual([], engine_worktree_problems(r.d))
        r.put(INSTANCE_REL, text=u"z\n")
        self.assertNotEqual([], engine_worktree_problems(r.d))


class OrderTest(unittest.TestCase):
    def test_e_1_the_real_history_has_the_seal_before_the_engine_before_the_script_the_gate_and_the_record(self):
        u"""engine・script・門・記録のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_e_2_good_order_is_green_and_bad_orders_are_red(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        impls = ["adapters/xbrl/instance.py"]
        others = ["measure/s.py", "tests/g.py", "fixtures/r.json"]
        for f in impls + others:
            r.put(f)
        r.commit(*(impls + others))                                                  # 同じ commit(engine と一緒に足す)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], impls, others))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", impls, others))
        r.put("fixtures/new.json")                                                  # 未 commit
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], impls, others + ["fixtures/new.json"]))
        r2 = PR.Repo()                                                              # script が封より前
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        r2.put(impls[0])
        r2.commit(impls[0])
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], impls, ["measure/s.py"]))
        r3 = PR.Repo()                                                              # script が engine の commit より前
        r3.put("docs/seal.md")
        s3 = r3.commit("docs/seal.md")
        r3.put("measure/s.py")
        r3.commit("measure/s.py")
        r3.put(impls[0])
        r3.commit(impls[0])
        self.assertNotEqual([], PR.order_problems(r3.d, PREFIX, "docs/seal.md", s3[:7], impls, ["measure/s.py"]))

    def test_e_3_the_order_check_lists_the_script_the_gate_and_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))


class MeasureTest(unittest.TestCase):
    def test_f_1_start_positions_and_the_start_block(self):
        self.assertEqual([], start_problems())

    def test_f_2_the_pair_of_rows_and_its_stops(self):
        self.assertEqual([], pair_problems())

    def test_f_3_the_blocks_and_the_prediction_numbers(self):
        self.assertEqual([], block_problems())

    def test_f_4_the_old_engine_blob_runs_in_memory_and_is_compared_with_the_load_instance_now(self):
        self.assertEqual([], old_engine_problems())

    def test_f_5_rates_are_rounded_by_integer_arithmetic(self):
        self.assertEqual([], rate_problems_fn())

    def test_f_6_states_job_wiring_runs_on_made_up_parts_and_sees_the_old_engine(self):
        u"""script の ``states_job`` そのものを作り物の部品で走らせる。直した engine では差 0・旧い engine に差し替えると差が出る(検出力)。非対称な例。"""
        self.assertEqual([], job_wire_problems())

    def test_f_7_build_record_wiring_runs_on_made_up_parts(self):
        u"""script の ``build_record`` そのもの(行・本ごとの欄・NRE-1〜NRE-5・指紋・NR の記録と TSS の記録の使い分け)を作り物で走らせる。"""
        self.assertEqual([], record_wire_problems())


class RecordTest(unittest.TestCase):
    def test_g_1_the_record_has_the_sealed_fields_and_equals_the_recount_from_its_rows(self):
        self.assertEqual([], record_problems())

    def test_g_2_a_record_with_one_number_changed_is_red(self):
        text = read(RECORD_REL)
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
        n = rec[K_NRE3][u"state が変わった行"][u"分子"]
        self.assertNotEqual([], record_problems(text=text.replace(u'"分子": %d,' % n, u'"分子": %d,' % (n + 1), 1)))

        def changed(fn):
            r = json.loads(text, object_pairs_hook=collections.OrderedDict)
            fn(r)
            return record_problems(text=json.dumps(r, ensure_ascii=False))

        self.assertNotEqual([], changed(lambda r: r[u"入力"][0].__setitem__(u"sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r[u"行"].pop()))
        self.assertNotEqual([], changed(lambda r: r[K_BOOKS][0].__setitem__(2, r[K_BOOKS][0][2] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_BOOKS][0].__setitem__(1, r[K_BOOKS][0][1] + 1)))
        self.assertNotEqual([], changed(lambda r: r[u"この script の sha256"].__class__ and r.__setitem__(u"この script の sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r[u"行"][0].__setitem__(4, not r[u"行"][0][4])))
        self.assertNotEqual([], changed(lambda r: r[u"行"][0].__setitem__(5, [s for s in STATES if s != r[u"行"][0][5]][0])))
        self.assertNotEqual([], changed(lambda r: r[u"行"][0].__setitem__(3, [s for s in STATES if s != r[u"行"][0][3]][0])))
        self.assertNotEqual([], changed(lambda r: r[K_NRE4][u"群ごと"][u"edinet"].__setitem__(u"読んだ ZIP", 280)))
        self.assertNotEqual([], changed(lambda r: r[K_NRE4][u"合計"].__setitem__(u"facts の列が違う ZIP の合計", r[K_NRE4][u"合計"][u"facts の列が違う ZIP の合計"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_NRE5].__setitem__(u"直した式が拾う始まりの合計", r[K_NRE5][u"直した式が拾う始まりの合計"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_NRE2].__setitem__(u"消えた fact", r[K_NRE2][u"消えた fact"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[u"engine の指紋(直した後)"].__setitem__(u"adapter_xbrl_py_sha256", r[u"engine の指紋(直す前。TSS の記録のもの)"][u"adapter_xbrl_py_sha256"])))
        self.assertNotEqual([], changed(lambda r: r[u"直した式(封 §1)"].__setitem__(u"後", r[u"直した式(封 §1)"][u"前"])))

    def test_g_3_a_record_with_a_sentence_a_value_or_an_element_name_is_red(self):
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"行"][0].append(u"売上高")
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"要素名"] = u"jppfs_cor:NetSales"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        self.assertEqual([], leak_problems(read(RECORD_REL)))
        self.assertFalse(DOCID_RE.search(read(RECORD_REL)))


class WiringTest(unittest.TestCase):
    def test_h_1_the_script_imports_only_the_allowed_modules(self):
        self.assertEqual([], import_problems())

    def test_h_2_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with open(p, encoding="utf-8") as fh:
            self.assertNotIn(u"nil_read_engine", fh.read())

    def test_h_3_the_script_has_no_network_key_or_llm(self):
        src = read(SCRIPT_REL)
        for bad in (u"socket", u"urllib", u"ANTHROPIC", u"API_KEY", u"requests"):
            self.assertNotIn(bad, src)

    def test_h_4_the_gate_does_not_use_the_reserved_names_and_has_no_docid(self):
        self.assertEqual([], reserved_problems())
        self.assertIsNone(DOCID_RE.search(read(GATE_REL)))
        self.assertIsNone(DOCID_RE.search(read(SCRIPT_REL)))

    def test_h_5_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("NRE_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rel="g.py", base=d))


class MutantTest(unittest.TestCase):
    def test_i_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_of(RECORD_REL), sha_of(INSTANCE_REL), tuple(sha_of(r) for r in INPUT_RELS))
        results = run_mutants()
        after = (sha_of(SCRIPT_REL), sha_of(RECORD_REL), sha_of(INSTANCE_REL), tuple(sha_of(r) for r in INPUT_RELS))
        self.assertEqual(before, after)
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))

    def test_i_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in (u"seal", u"input_sha", u"start", u"pair", u"blocks", u"old", u"rate", u"material", u"import", u"wire_job", u"wire_rec", u"wire_inputs"):
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
