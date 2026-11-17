# -*- coding: utf-8 -*-
"""封 docs/XBRL_PLAN_SOURCE_SEAL_2026-11-17.md(PS ― engine が計画・予想の数として止めた行に、同じ短信のサマリーの予想の fact という当てる先が在るかを数える)と、その追記 §7・§8 の門。封 §1・§2・§3・§7・§8。

**この門が縛るもの**

1. 封の字: §1 の入力の表(5 行)が script の ``INPUTS`` と 1 行ずつ同じ。封の commit・追記の commit・path。§7 の要点の字。**§0〜§6 が追記の後も最初の封の commit と、§0〜§7 が §8 の追記の後も §7 の追記の commit と 1 字も変わっていない**(git の blob の前半を比べる。封の file の履歴は 最初の封 a080ce5f・追記 5b38862e・追記 3e8a722d の 3 commit)。
2. 入力 5 つの sha256 が封の表と同じ(実物)。違えば script は止まる(複製の 1 byte を変えて止まるのを見る)。
3. 照合(封 §2-4・§7。単位の接頭辞 ``JPY`` は ``JPXX`` のような字に当てない): 1 つの claim と 1 つの fact を直接呼ぶ。円の例(1,200 億円・claim_scale 1e8 が fact 120,034,000,000 に当たり 121,000,000,000 に当たらない)は、**字のとおりの読みでは当てない・円の族の読みでは当たる**。% の例(5.2% と fact 0.052 が当たり 0.053 が当たらない)・当てない(単位が株・値が 0・scale が無い)・scale が無い行の札。
4. F と R の分け(ForecastMember・UpperMember・LowerMember)・別の本の決め方(封 §2-6)・標本の組(封 §2-7・§7 の 4・§8 の 5)・W の型の字・``analyze``(自分の F でなく別の本の F を使う・読みごとの輪)を小さい作り物の入力で直接呼ぶ。
   **空の欄を除く関数(封 §8 の 4)を、当たる例・当たらない例で直接呼ぶ。** 小さい作り物のサマリー(空の欄の直後に本物の fact が在る形)で、そのままの読みでは本物の fact が落ちて偽の fact が出ること・空の欄を除く読みでは本物の fact が倍率つきで出ることを ``load_instance`` で確かめる。自己閉じの読み取りの数え方(engine と同じ正規表現・属性の列が ``/`` で終わる)も直接呼ぶ。
5. 記録 ``fixtures/xbrl/plan_source/states_2026-11-17.json``: 封の字・script の sha256・入力・P の行 794(群別 129・632・33)・W の行 20・行の形(22 欄・文や値や要素名を持たない)・
   主の数の固定(P の自 193・実 71・他 8・当てない 355・W 5・3・0・7)・読み 4 通りの集計が記録の行からの独立の数え直しと一致・自己閉じの数・script の集計関数が記録の行から同じ数を作る・行の不変(自 ≤ 当てた行・F が空の本の行は自が偽・字のとおりの自は円の族の自に含まれる・scale が無い行は両方で当てない)・率の字。
6. types の記録(読みの軸の封 06d7b8a7 §6 の形。1 行 7 列の入口): 記録が在ることと形・行が標本の行と 1 対 1・集計が行からの数え直しと一致・元の封の字が身元の 5 字から §2-3 で決めた字と一致・states の sha256 が実物と同じ。
   入口は作り物の字の file で直接走らせる(標本の行と 1 対 1・順も同じ・値の軸は 1〜4・身元は 合・違・不 の 5 字・字は あ/い/う で身元から決めた字と食い違えば止まる・文や値を持たない)。
7. sheet は repo の中への書き出しを止める。
8. engine 0 行: 封の commit から HEAD まで ``core/``・``adapters/``・``measure/lib``・``measure/inject.py`` と入力 5 つを触っていない。作業木に未 commit の変更も無い。``tests/adapters/xbrl/test_boundary.py`` の import 一覧は広げない。
9. 順序: **最初の封 a080ce5f と追記 5b38862e・3e8a722d の全部**が script・この門・記録より前(commit の順。未 commit は赤)。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
400 本の作り直しは門の中では走らせない(重い)。``states --check`` は「作り直した記録が在る記録と同じか」しか見ず、fact の読みの正しさは見えない(封 §8 の欠陥は ``--check`` が緑のまま在った)。読みの正しさは、小さい作り物のサマリーを ``load_instance`` で読む門(上の 4)で縛る。この file は docID の字を持たない。
"""
import ast
import collections
import hashlib
import importlib.util
import json
import os
import random
import re
import shutil
import sys
import tempfile
import types
import unittest
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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_ps_seal")       # 順序の部品。門としては走らせない
SGR = load_module("tests/measure/test_xbrl_rmix_seal.py", "rmix_seal_gate_for_plan_source_seal")      # 宣言された遷移の部品(2026-11-17 NRE: nre_explained_commit)。門としては走らせない
MS = load_module("measure/xbrl_plan_source_2026-11-17.py", "plan_source_script_for_seal_gate")

SEAL_REL = "docs/XBRL_PLAN_SOURCE_SEAL_2026-11-17.md"
SEAL_COMMIT_SHORT = "a080ce5f"                 # 最初の封の commit(literal に留める。script の定数と違えば赤)
ADDENDUM_COMMIT_SHORT = "5b38862e"             # 追記 §7 の commit
ADDENDUM8_COMMIT_SHORT = "3e8a722d"            # 追記 §8 の commit
AXES_SEAL_REL = "docs/XBRL_PLAN_SOURCE_READ_AXES_SEAL_2026-11-17.md"      # 読みの軸の封(§6 が types の入口を決める)
AXES_SEAL_COMMIT_SHORT = "06d7b8a7"
SCRIPT_REL = "measure/xbrl_plan_source_2026-11-17.py"
GATE_REL = "tests/measure/test_xbrl_plan_source_seal.py"
RECORD_REL = "fixtures/xbrl/plan_source/states_2026-11-17.json"
TYPES_REL = "fixtures/xbrl/plan_source/read_types_2026-11-17.json"
POPULATION_REL = "fixtures/xbrl/tanshin_self/population_2026-11-14.json"
ORDER_FILES = (SCRIPT_REL, GATE_REL, RECORD_REL)
INPUT_RELS = tuple(rel for _no, rel, _sha in MS.INPUTS)
ENGINE_RELS = ("adapters", "core", "measure/lib", "measure/inject.py")
NOT_TOUCHED_RELS = ENGINE_RELS + INPUT_RELS
#: script が import してよい module(標準ライブラリと、engine の 3 module(adapters.xbrl の instance・verify_document・vocabulary)と前の便の script を読むための importlib)
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "io", "json", "os", "random", "re", "sys", "time", "zipfile")
ENGINE_OK = ("adapters.xbrl",)
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
RATE_TEXT = re.compile(r"^(\d+\.\d%|分母 0)$")
GROUPS = (u"甲", u"乙", u"丙")
RD_LIT = u"字のとおりの読み(主)"
RD_FAM_PREFIX = u"円の族の読み"
NOTE_FAMILY = u"封の後・試走の数を見た後に足した読み"
NOTE_NONNIL = u"封の後・監査の数え直しを見た後に足した読み"
#: 記録の行の札の列(当てない, F が空, 自, 実, 他)。読み 4 通りの順(主・円の族・空の欄を除く・円の族 × 空の欄を除く)
RD_IDX = ((5, 6, 7, 8, 9), (10, 6, 11, 12, 13), (5, 15, 16, 17, 18), (10, 15, 19, 20, 21))
N_COL = 22


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
    mod = types.ModuleType("plan_source_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


# ---------------------------------------------------------------- 1. 封の字
def seal_text():
    return read(SEAL_REL)


def seal_inputs(seal):
    return [(int(m.group(1)), m.group(2), m.group(3)) for m in re.finditer(r"^\| (\d) \| `([^`]+)` \| `([0-9a-f]{64})` \|$", seal, re.M)]


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    si = seal_inputs(seal)
    if [i[0] for i in si] != [1, 2, 3, 4, 5]:
        out.append(u"封 §1 の表が 5 行の # の順でない")
    if [tuple(x) for x in ms.INPUTS] != si:
        out.append(u"script の入力の表が封 §1 の表と違う")
    if (ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.ADDENDUM_COMMIT != ADDENDUM_COMMIT_SHORT or ms.ADDENDUM8_COMMIT != ADDENDUM8_COMMIT_SHORT
            or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL):
        out.append(u"script の封の commit・追記の commit(§7・§8)・path が門と違う")
    if ms.STATES_REL != RECORD_REL or ms.TYPES_REL != TYPES_REL:
        out.append(u"script の記録の path が門と違う")
    for phrase in (u"同じ ZIP のサマリーの予想の fact に同じ値が在るか", u"`ForecastMember`・`UpperMember`・`LowerMember`", u"random.Random(20261117).sample(range(行の数), 60)",
                   u"## §7 追記", u"**主の数は字のとおりの読み(単位の字が `円` だけ)**", u"円・千円・万円・百万円・億円・兆円のどれか", u"同じ種で 30 行",
                   u"単位の表から scale を作る規則は足さない", u"## §8 追記", u"正規表現 `<ix:nonFraction[^>]*/>` に当たる所", u"**PS-6 は封のとおり(そのままの読みの札から引く)には測らない。**",
                   u"主の数が「同じ短信のサマリーの予想の fact に当たった率」としては読めない"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    if ms.PROFILE != u"P33E" or ms.SAMPLE_SEED != 20261117 or ms.SAMPLE_N != 60 or ms.SAMPLE_N_OTSU != 30 or ms.EXPECT_P != 794 or ms.EXPECT_W != 20:
        out.append(u"script の決めごと(profile・種・標本の数・P と W の行の数)が封と違う")
    if tuple(ms.FORECAST_MEMBERS) != (u"ForecastMember", u"UpperMember", u"LowerMember") or tuple(ms.YEN_UNITS) != (u"円", u"千円", u"万円", u"百万円", u"億円", u"兆円"):
        out.append(u"F の member の名か円の族の単位の字が封と違う")
    if ms.NIL_TAG_RE.pattern != br"<ix:nonFraction[^>]*/>" or ms.JPY_PREFIX != u"JPY" or ms.PURE_UNIT != u"Pure" or ms.TYPE_W != u"ウ":
        out.append(u"空の欄を除く正規表現・円の fact の単位の接頭辞・Pure・W の型の字が封と違う")
    return out


def seal_history_problems(root=REPO):
    u"""封の file の履歴 = 最初の封 + 追記 §7 + 追記 §8 の 3 commit。追記の commit は封の file だけを触る。
    今の封の §0〜§6 は最初の封のまま、§0〜§7 は §7 の追記の commit のまま、全部は §8 の追記の commit のまま(1 字も変わっていない)。"""
    c = PR.added_commits(root, PREFIX + SEAL_REL)
    out = []
    if len(c) != 1 or not c[0].startswith(SEAL_COMMIT_SHORT):
        out.append(u"封の commit が履歴に 1 つで %s に決まらない" % SEAL_COMMIT_SHORT)
        return out
    rc, log = PR.git_in(root, "log", "--format=%H", "--", PREFIX + SEAL_REL)
    commits = [x for x in log.split() if x]
    add7 = [x for x in commits if x.startswith(ADDENDUM_COMMIT_SHORT)]
    add8 = [x for x in commits if x.startswith(ADDENDUM8_COMMIT_SHORT)]
    if len(add7) != 1 or len(add8) != 1 or len(commits) != 3:
        out.append(u"封の file の履歴が 最初の封 + 追記 §7 + 追記 §8 の 3 commit でない")
        return out
    for a in (add7[0], add8[0]):
        rc, names = PR.git_in(root, "show", "--name-only", "--format=", a)
        if names.split() != [PREFIX + SEAL_REL]:
            out.append(u"追記の commit が封の file だけを触っていない")
    rc, first = PR.git_in(root, "show", "%s:%s" % (c[0], PREFIX + SEAL_REL))
    rc, second = PR.git_in(root, "show", "%s:%s" % (add7[0], PREFIX + SEAL_REL))
    rc, third = PR.git_in(root, "show", "%s:%s" % (add8[0], PREFIX + SEAL_REL))
    now = seal_text().rstrip(u"\n")
    cut7 = now.index(u"\n## §7")
    cut8 = now.index(u"\n## §8")
    # git_in は末尾を strip するので、字も末尾の改行を落として比べる
    if now[:cut7].rstrip(u"\n") != first.rstrip(u"\n"):
        out.append(u"追記の後の封の §0〜§6 が最初の封と違う")
    if now[:cut8].rstrip(u"\n") != second.rstrip(u"\n"):
        out.append(u"§8 の追記の後の封の §0〜§7 が §7 の追記の commit と違う")
    if now != third.rstrip(u"\n"):
        out.append(u"今の封が §8 の追記の commit と違う")
    return out


# ---------------------------------------------------------------- 2. 入力の sha256
def input_sha_problems(ms=None):
    ms = ms or MS
    return [u"入力の sha256 が封と違う: %s" % rel for _no, rel, want in ms.INPUTS if sha_of(rel) != want]


def stop_problems(ms=None):
    u"""入力の sha256 が違えば止まる(複製の木の 1 byte を変える)・変えなければ止まらない・P の行の数が違う・W の行が当たらないときも止まる。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="ps_gate_")
    try:
        for rel in INPUT_RELS:
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(ROOT, rel), dst)
        if guard(lambda: ms.check_inputs(tmp) and []):
            out.append(u"変えない入力で止まる")
        with open(os.path.join(tmp, INPUT_RELS[1]), "ab") as fh:
            fh.write(b" ")
        try:
            ms.check_inputs(tmp)
            out.append(u"入力の sha256 が違うのに止まらない")
        except ms.Stop:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # analyze の止まり方(作り物の本)
    f_a = [(u"JPY", 1.0), (u"Pure", 0.052)]
    claim = collections.OrderedDict([(u"si", 1), (u"pos", 2), (u"state", u"UNVERIFIABLE"), (u"reason", u"target_or_plan"), (u"unit", u"%"), (u"value", 5.2),
                                    (u"unit_scale", None), (u"claim_scale", None), (u"pct_tolerance", 0.06)])
    books = [collections.OrderedDict([(u"#", n), (u"群", u"甲"), (u"切れた", True), (u"claims", [dict(claim)] if n == 1 else []), (u"F", list(f_a)), (u"R", []), (u"F2", list(f_a)), (u"R2", [])]) for n in (1, 2, 3)]
    try:
        rows, _n = ms.analyze(books, set(), 1, None)
        if len(rows) != 1:
            out.append(u"作り物の本から P の行が 1 つにならない")
    except BaseException as exc:                      # noqa: BLE001
        out.append(u"作り物の本で止まった: %s" % type(exc).__name__)
    for label, args in ((u"P の行の数が違う", (books, set(), 2, None)), (u"W の行が当たらない", (books, set([(9, 9, 9)]), None, None))):
        try:
            ms.analyze(*args)
            out.append(u"%s のに止まらない" % label)
        except ms.Stop:
            pass
        except BaseException as exc:                  # noqa: BLE001
            out.append(u"%s: Stop でない例外 %s" % (label, type(exc).__name__))
    return out


# ---------------------------------------------------------------- 3. 照合(封 §2-4・§7)
def claim(unit, value, unit_scale=None, claim_scale=None, tol=None):
    d = {u"unit": unit, u"value": value, u"unit_scale": unit_scale, u"claim_scale": claim_scale}
    if tol is not None:
        d[u"pct_tolerance"] = tol
    return d


def match_problems(ms=None):
    ms = ms or MS
    L, F = ms.READING_LITERAL, ms.READING_FAMILY
    out = []

    def expect(label, got, want):
        if got != want:
            out.append(u"%s: %r(期待 %r)" % (label, got, want))
    oku = claim(u"億円", 1200.0, 1e8, 1e8)                       # 文「売上高 1,200 億円を見込む」(値 1.2e11・claim_scale 1e8)
    expect(u"億円の例 当たる(円の族)", ms.match_fact(oku, u"JPY", 120034000000.0, F), True)
    expect(u"億円の例 当たる(字のとおりでは当てない)", ms.match_fact(oku, u"JPY", 120034000000.0, L), False)
    expect(u"億円の例 当たらない(円の族)", ms.match_fact(oku, u"JPY", 121000000000.0, F), False)
    expect(u"億円の例 当たらない(字のとおり)", ms.match_fact(oku, u"JPY", 121000000000.0, L), False)
    expect(u"億円の例 JPYPerShares も JPY で始まる", ms.match_fact(oku, u"JPYPerShares", 120034000000.0, F), True)
    expect(u"億円の例 単位が JPY で始まらない", ms.match_fact(oku, u"USD", 120034000000.0, F), False)
    expect(u"億円の例 Pure の fact には当てない", ms.match_fact(oku, u"Pure", 120034000000.0, F), False)
    expect(u"億円の例 絶対値で当たる", ms.match_fact(oku, u"JPY", -120034000000.0, F), True)
    # 円の fact の単位の接頭辞(JPY・JPYPerShares は円の fact。JPXX・JP・XJPY のような字は違う。小文字は大文字にして見る)
    for u_, want in ((u"JPY", True), (u"JPYPerShares", True), (u"jpy", True), (u"JPXX", False), (u"JP", False), (u"XJPY", False), (u"", False)):
        expect(u"単位の接頭辞 %r" % u_, ms.match_fact(oku, u_, 120034000000.0, F), want)
    en = claim(u"円", 1.2e11, 1.0, 1e8)
    expect(u"円の claim は両方の読みで当たる(字)", ms.match_fact(en, u"JPY", 120034000000.0, L), True)
    expect(u"円の claim は両方の読みで当たる(族)", ms.match_fact(en, u"JPY", 120034000000.0, F), True)
    expect(u"円の claim 当たらない", ms.match_fact(en, u"JPY", 121000000000.0, L), False)
    expect(u"円の claim 切り捨ての帯(fact が帯の上端の外)", ms.match_fact(en, u"JPY", 1.2e11 + 1.1e8, L), False)
    pc = claim(u"%", 5.2, tol=0.06)
    expect(u"% の例 当たる", ms.match_fact(pc, u"Pure", 0.052), True)
    expect(u"% の例 当たらない", ms.match_fact(pc, u"Pure", 0.053), False)
    expect(u"% の例 単位が Pure でない", ms.match_fact(pc, u"JPY", 0.052), False)
    expect(u"% の例 符号だけ違うのは絶対値で当たる", ms.match_fact(claim(u"%", -5.2, tol=0.06), u"Pure", 0.052), True)
    expect(u"% の例 符号が逆の fact も絶対値で当たる", ms.match_fact(pc, u"Pure", -0.052), True)
    expect(u"% の既定の tol 0.15 の内", ms.match_fact(claim(u"%", 5.2), u"Pure", 0.053), True)
    expect(u"% の既定の tol 0.15 の外", ms.match_fact(claim(u"%", 5.2), u"Pure", 0.054), False)
    expect(u"% は読みに依らない", ms.match_fact(pc, u"Pure", 0.052, F), True)
    # 当てない
    for label, c in ((u"株", claim(u"株", 100.0)), (u"値が 0 の%", claim(u"%", 0.0, tol=0.1)), (u"値が 0 の円", claim(u"円", 0.0, 1.0, 1)),
                     (u"scale の無い円", claim(u"円", 63000.0)), (u"scale の無い億円", claim(u"億円", 3.0)), (u"claim_scale だけ無い億円", claim(u"億円", 3.0, 1e8, None)),
                     (u"unit_scale だけ無い百万円", claim(u"百万円", 3.0, None, 1e6))):
        for rd in (L, F):
            got = ms.claim_flags(c, [(u"JPY", 63000.0), (u"JPY", 3e8), (u"Pure", 0.0)], [(u"JPY", 63000.0)], [(u"JPY", 63000.0)], rd)
            expect(u"当てない(%s・%s)" % (label, rd), got, (True, False, False, False))
    expect(u"札: 自だけ", ms.claim_flags(pc, [(u"Pure", 0.052)], [], [], L), (False, True, False, False))
    expect(u"札: 実だけ", ms.claim_flags(pc, [], [(u"Pure", 0.052)], [], L), (False, False, True, False))
    expect(u"札: 他だけ", ms.claim_flags(pc, [], [], [(u"Pure", 0.052)], L), (False, False, False, True))
    expect(u"札: 億円は字のとおりで当てない・円の族で自", (ms.claim_flags(oku, [(u"JPY", 120034000000.0)], [], [], L), ms.claim_flags(oku, [(u"JPY", 120034000000.0)], [], [], F)),
           ((True, False, False, False), (False, True, False, False)))
    expect(u"scale が無い行の札(円の族の単位)", [ms.no_scale(claim(u"億円", 3.0)), ms.no_scale(claim(u"円", 3.0, None, 1)), ms.no_scale(claim(u"円", 3.0, 1.0, None))], [True, True, True])
    expect(u"scale が無い行の札(あるもの・円の族でないもの)", [ms.no_scale(claim(u"億円", 3.0, 1e8, 1e8)), ms.no_scale(claim(u"%", 3.0)), ms.no_scale(claim(u"株", 3.0))], [False, False, False])
    expect(u"単位の族", [ms.unit_family(claim(u, 1.0)) for u in (u"円", u"億円", u"百万円", u"%", u"株", u"店舗")], [u"円", u"円", u"円", u"%", u"他", u"他"])
    return out


def rate_function_problems(ms=None):
    ms = ms or MS
    out = []
    for n, d in ((0, 0), (1, 3), (2, 3), (5, 8), (1, 8), (193, 794), (269, 794), (7, 200), (1, 2000)):
        want = u"分母 0" if d == 0 else u"%d.%d%%" % divmod(int(Fraction(n, d) * 1000 + Fraction(1, 2)), 10)
        got = ms.rate(n, d)
        if got[u"率"] != want or got[u"分子"] != n or got[u"分母"] != d:
            out.append(u"率の字が独立の計算と違う: %d/%d" % (n, d))
    if ms.ratio_text(5, 0) != u"他は 0" or ms.ratio_text(10, 4) != u"2.5":
        out.append(u"比の字が違う")
    return out


# ---------------------------------------------------------------- 4. F と R・別の本・標本の組
def instance(contexts, facts):
    return {u"contexts": contexts, u"facts": facts}


def split_problems(ms=None):
    ms = ms or MS
    out = []
    ctx = {u"cF": {u"members": [u"tse-ed-t:ForecastMember"]}, u"cU": {u"members": [u"x:ConsolidatedMember", u"tse-ed-t:UpperMember"]}, u"cL": {u"members": [u"LowerMember"]},
           u"cR": {u"members": [u"tse-ed-t:ResultMember"]}, u"c0": {u"members": []}, u"cX": {u"members": [u"tse-ed-t:XForecastMember"]}}

    def f(name, c, unit=u"JPY", value=5.0):
        return {u"name": name, u"context": c, u"unit": unit, u"value": value}
    facts = [f(u"a", u"cF"), f(u"b", u"cU"), f(u"c", u"cL"), f(u"d", u"cR"), f(u"e", u"c0"), f(u"g", u"cX"), f(u"h", u"cF", value=0.0), f(u"i", u"cF", unit=None),
             f(u"j", u"cR", unit=u""), f(u"k", u"cR", value=0), f(u"m", u"nosuchcontext")]
    fl, rl = ms.split_facts(instance(ctx, facts))
    if sorted(x[u"name"] for x in fl) != [u"a", u"b", u"c"]:
        out.append(u"F の分けが違う: %s" % sorted(x[u"name"] for x in fl))
    if sorted(x[u"name"] for x in rl) != [u"d", u"e", u"g", u"m"]:
        out.append(u"R の分けが違う: %s" % sorted(x[u"name"] for x in rl))
    return out


def other_problems(ms=None):
    ms = ms or MS
    out = []
    # (群, #, 切れた, F が空でない)
    infos = [(u"甲", 1, True, True), (u"甲", 2, True, True), (u"甲", 3, True, False), (u"甲", 4, True, True), (u"甲", 5, False, True), (u"甲", 6, True, False),
             (u"乙", 7, True, True), (u"乙", 8, True, False), (u"乙", 9, True, True), (u"丙", 10, True, True), (u"丙", 11, True, True)]
    got = ms.other_books(infos)
    want = {1: 2, 2: 4, 4: 1, 3: 4, 5: 1, 6: 1, 7: 9, 9: 7, 8: 9, 10: 11, 11: 10}
    if got != want:
        out.append(u"別の本が決めと違う: %s" % sorted(got.items()))
    if any(got[n] == n for n in got):
        out.append(u"別の本が自分になっている")
    if got != ms.other_books(list(reversed(infos))):
        out.append(u"別の本が並べ順に依る")
    try:
        ms.other_books([(u"甲", 1, True, True), (u"甲", 2, True, False), (u"乙", 3, True, True), (u"乙", 4, True, True)])
        out.append(u"輪の本が 1 本以下の群で止まらない")
    except ms.Stop:
        pass
    return out


def sample_problems(ms=None):
    u"""標本の組(封 §2-7・§7 の 4・§8 の 5)を作り物の記録で。**空の欄を除く読みの札(列 16・19)から引く**(そのままの読みの札 7・11 は逆の値にして、そちらから引くと赤)。"""
    ms = ms or MS
    out = []

    def row(n, si, which, s, s2):
        return [n, si, 1, which, u"円", False, False, not s, False, False, False, not s2, False, False, False, False, s, False, False, s2, False, False]
    rows = []
    for i in range(100):
        rows.append(row(1 + i // 10, i, u"P", True, True))                   # 甲組の母集団 100 行(字のとおりで自)
    for i in range(50):
        rows.append(row(20 + i // 10, i, u"P", False, True))                 # 乙組の母集団 50 行(円の族でだけ自)
    for i in range(30):
        rows.append(row(40, i, u"P", False, False))                          # どちらでも自でない
    rows.append(row(50, 1, u"W", True, True))
    rows.append(row(50, 2, u"W", False, True))
    rows.append(row(50, 3, u"W", False, False))
    rows.append(row(52, 1, u"W", False, True))
    rows.append(row(51, 1, u"W", True, False))                                # 字のとおりでだけ自(円の族では自でない → W 組に入らない。作りでは起きない形を入れて条件を見る)
    rows = list(reversed(rows))
    items = ms.sample_items({u"行": rows})
    cnt = collections.Counter(it[4] for it in items)
    if (cnt[u"甲組"], cnt[u"乙組"], cnt[u"W組"]) != (60, 30, 3) or len(items) != 93:
        out.append(u"標本の組の数が違う: %s" % dict(cnt))
    if [it[0] for it in items] != list(range(1, len(items) + 1)):
        out.append(u"標本の番号が 1 から続かない")
    kou = [(it[1], it[2]) for it in items if it[4] == u"甲組"]
    pool = sorted((r[0], r[1]) for r in rows if r[3] == u"P" and r[16])
    want = [pool[j] for j in sorted(random.Random(20261117).sample(range(len(pool)), 60))]
    if kou != want:
        out.append(u"甲組が封の引き方(種 20261117・番号の順)と違う")
    otsu = [(it[1], it[2]) for it in items if it[4] == u"乙組"]
    pool2 = sorted((r[0], r[1]) for r in rows if r[3] == u"P" and r[19] and not r[16])
    want2 = [pool2[j] for j in sorted(random.Random(20261117).sample(range(len(pool2)), 30))]
    if otsu != want2:
        out.append(u"乙組が同じ種の 30 行・円の族でだけ自、と違う")
    if [it[4] for it in items] != [u"甲組"] * 60 + [u"乙組"] * 30 + [u"W組"] * 3:
        out.append(u"組の並びが 甲組 → 乙組 → W組 でない")
    few = ms.sample_items({u"行": [row(1, 1, u"P", False, True), row(1, 2, u"P", False, True)]})
    if [it[4] for it in few] != [u"乙組", u"乙組"]:
        out.append(u"満たなければ全部、が違う")
    return out


def w_keys_problems(ms=None):
    u"""W の型の字(ウ)だけを (本の #, 文の番号, 位置) の鍵にする。ほかの字は入れない。"""
    ms = ms or MS
    out = []
    rec = {u"行": [[0, 5, 6, 7, u"ウ"], [1, 8, 9, 10, u"エ"], [2, 11, 12, 13, u"ア"], [3, 14, 15, 16, u"イ"], [4, 17, 18, 19, u"ウ"]]}
    if ms.w_keys_of(rec) != set([(5, 6, 7), (17, 18, 19)]):
        out.append(u"W の鍵が型 ウ の行だけでない: %s" % sorted(ms.w_keys_of(rec)))
    real = ms.w_keys_of(ms.load_json(os.path.join(ROOT, ms.TYPES_IN_REL)))
    if len(real) != 20:
        out.append(u"実物の型の記録から W が 20 行にならない(%d)" % len(real))
    return out


def analyze_problems(ms=None):
    u"""``analyze`` を小さい作り物の本で直接呼ぶ(封 §2-5・§2-6・§8)。自分の本の F でなく別の本の F を使う・読みごとに輪を作る。
    b1(F が 0.052 の本)・b2・b3(raw では F が空 = 輪に居ない。空の欄を除く読みでは F2 が在る)。% の claim を 3 冊に 1 つずつ。"""
    ms = ms or MS
    out = []

    def book(n, f, r, f2, r2, claims):
        return collections.OrderedDict([(u"#", n), (u"群", u"甲"), (u"切れた", True), (u"claims", claims), (u"F", f), (u"R", r), (u"F2", f2), (u"R2", r2)])
    cl = lambda: [collections.OrderedDict([(u"si", 1), (u"pos", 1), (u"state", u"UNVERIFIABLE"), (u"reason", u"target_or_plan"), (u"unit", u"%"), (u"value", 5.2),  # noqa: E731
                                           (u"unit_scale", None), (u"claim_scale", None), (u"pct_tolerance", 0.06)])]
    books = [book(1, [(u"Pure", 0.052)], [(u"Pure", 0.011)], [(u"Pure", 0.077)], [(u"Pure", 0.052)], cl()),
             book(2, [(u"Pure", 0.099)], [], [(u"Pure", 0.052)], [], cl()),
             book(3, [], [], [(u"Pure", 0.052)], [], cl())]
    rows, n_c = ms.analyze(books, set(), 3, None)
    T, Fa = True, False
    #        #  si pos 組    族    当てない F空 自  実  他   族:当てない 自  実  他   無  | F2空 自  実  他  族の自 実  他
    want = [[1, 1, 1, u"P", u"%", Fa, Fa, T, Fa, Fa, Fa, T, Fa, Fa, Fa, Fa, Fa, T, T, Fa, T, T],
            [2, 1, 1, u"P", u"%", Fa, Fa, Fa, Fa, T, Fa, Fa, Fa, T, Fa, Fa, T, Fa, T, T, Fa, T],
            [3, 1, 1, u"P", u"%", Fa, T, Fa, Fa, T, Fa, Fa, Fa, T, Fa, Fa, T, Fa, Fa, T, Fa, Fa]]
    if [list(r) for r in rows] != want:
        out.append(u"analyze の行が決めと違う: %s" % [list(r) for r in rows])
    # N: GROUNDED の行は数える(読みごと)。b1 の claim を GROUNDED にして数える
    books2 = [book(1, [(u"Pure", 0.052)], [], [(u"Pure", 0.077)], [], []), book(2, [(u"Pure", 0.099)], [], [(u"Pure", 0.052)], [], [])]
    c = cl()
    c[0][u"state"], c[0][u"reason"] = u"GROUNDED", u"x"
    books2[0][u"claims"] = c
    _r, n_c2 = ms.analyze(books2, set())
    got = [(n_c2[(rd, u"甲")][u"行"], n_c2[(rd, u"甲")][u"自"], n_c2[(rd, u"甲")][u"他"]) for rd in ms.READS]
    if got != [(1, 1, 0), (1, 1, 0), (1, 0, 1), (1, 0, 1)]:
        out.append(u"N の数が読みごとに決めと違う: %s" % got)
    return out


# 空の欄が自己閉じの tag で在り、その直後に本物の fact が在るサマリー(封 §8 の 1)
NIL_TAG = b'<ix:nonFraction name="x:Empty" contextRef="cF" unitRef="JPY" xsi:nil="true" />'
REAL_TAG = b'<ix:nonFraction name="x:Real" contextRef="cF" unitRef="JPY" decimals="-6" scale="6">1,234</ix:nonFraction>'
CTX = (b'<xbrli:context id="cF"><xbrli:entity></xbrli:entity><xbrli:period><xbrli:instant>2027-03-31</xbrli:instant></xbrli:period>'
       b'<xbrli:scenario><xbrldi:explicitMember dimension="d:Axis">tse-ed-t:ForecastMember</xbrldi:explicitMember></xbrli:scenario></xbrli:context>')


def tiny_summary_zip(html):
    import io as _io
    import zipfile as _zf
    buf = _io.BytesIO()
    with _zf.ZipFile(buf, "w") as z:
        z.writestr(u"XBRLData/Summary/tse-acedjpsm-00000-2027-ixbrl.htm", html)
    return buf.getvalue()


def strip_problems(ms=None):
    u"""封 §8 の 4: 当たる例・当たらない例・ほかは 1 byte も変えない・小さい作り物のサマリーを ``load_instance`` で読む(そのままでは本物の fact が落ちて偽の fact が出る)。"""
    ms = ms or MS
    out = []
    keep = b'<ix:nonFraction name="x" contextRef="c" unitRef="JPY" scale="6">1,234</ix:nonFraction>'
    if ms.strip_nil_tags(b'<ix:nonFraction name="x" contextRef="c" unitRef="JPY" xsi:nil="true" />') != b"":
        out.append(u"空の欄(自己閉じの tag)を取り除かない")
    if ms.strip_nil_tags(b'<ix:nonFraction name="x"/>') != b"":
        out.append(u"空白の無い自己閉じの tag を取り除かない")
    if ms.strip_nil_tags(keep) != keep:
        out.append(u"値の在る fact を取り除いた")
    body = u"前<b>日本語の字</b>\n".encode("utf-8")
    html = body + NIL_TAG + b"\n" + keep + u" 後 ".encode("utf-8") + NIL_TAG + NIL_TAG + body
    if ms.strip_nil_tags(html) != body + b"\n" + keep + u" 後 ".encode("utf-8") + body:
        out.append(u"ほかの bytes を 1 byte も変えずに空の欄だけ取り除いていない")
    if ms.strip_nil_tags(b'<ix:nonFraction name="a">1</ix:nonFraction><ix:nonFraction name="b" xsi:nil="true"/><ix:nonFraction name="c">2</ix:nonFraction>') != \
            b'<ix:nonFraction name="a">1</ix:nonFraction><ix:nonFraction name="c">2</ix:nonFraction>':
        out.append(u"本物の fact にまたがって取り除いた(貪欲)")
    # 小さい作り物のサマリー: 空の欄の直後に本物の fact
    zb = tiny_summary_zip(b"<html>" + CTX + NIL_TAG + REAL_TAG + b"</html>")
    if ms.summary_member_bytes(zb) != b"<html>" + CTX + NIL_TAG + REAL_TAG + b"</html>":
        out.append(u"サマリーの member の bytes が読めない")
    # 2026-11-17(NRE): 直った後の形。engine(封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md §1 の式)は空の欄を始まりの tag と読まないので、そのままの読みも「本物の fact 1 つ(倍率つき)」で、
    # 空の欄を除く読みと同じ列になる。直す前の欠陥の形(偽の fact 1 つ)は、直す前の式の写しを使う参照の engine(SGR.nre_old_formula_instance)で残す
    raw_f, raw_r = ms.summary_facts(zb)
    if [(f[u"name"], f[u"value"], f[u"unit"]) for f in raw_f + raw_r] != [(u"x:Real", 1234000000.0, u"JPY")]:
        out.append(u"そのままの読みが「本物の fact 1 つ(倍率つき)」にならない(式が空の欄を始まりの tag と読む疑い): %s" % [(f[u"name"], f[u"value"]) for f in raw_f + raw_r])
    nn_f, nn_r = ms.summary_facts(zb, True)
    if [(f[u"name"], f[u"value"], f[u"unit"]) for f in nn_f + nn_r] != [(u"x:Real", 1234000000.0, u"JPY")]:
        out.append(u"空の欄を除く読みが「本物の fact 1 つ(倍率つき)」にならない: %s" % [(f[u"name"], f[u"value"]) for f in nn_f + nn_r])
    if (raw_f, raw_r) != (nn_f, nn_r):
        out.append(u"直した engine でそのままの読みと空の欄を除く読みが同じ列でない")
    saved_i = ms.I
    ms.I = SGR.nre_old_formula_instance()
    try:
        old_f, old_r = ms.summary_facts(zb)
        old_nn_f, old_nn_r = ms.summary_facts(zb, True)
    finally:
        ms.I = saved_i
    if [(f[u"name"], f[u"value"]) for f in old_f + old_r] != [(u"x:Empty", 1234.0)]:
        out.append(u"直す前の式の参照の engine のそのままの読みが「偽の fact 1 つ(名前は空の欄・値は次の fact の字・倍率なし)」にならない: %s" % [(f[u"name"], f[u"value"]) for f in old_f + old_r])
    if [(f[u"name"], f[u"value"], f[u"unit"]) for f in old_nn_f + old_nn_r] != [(u"x:Real", 1234000000.0, u"JPY")]:
        out.append(u"空の欄を除く読みが直す前の式の参照の engine でも「本物の fact 1 つ(倍率つき)」にならない")
    if [f[u"name"] for f in nn_f] != [u"x:Real"]:
        out.append(u"予想の context の fact が F に入らない")
    # サマリーの member が 0 個・2 個は止まる
    import io as _io
    import zipfile as _zf
    for names in ([], [u"XBRLData/Summary/a-ixbrl.htm", u"XBRLData/Summary/b-ixbrl.htm"]):
        buf = _io.BytesIO()
        with _zf.ZipFile(buf, "w") as z:
            z.writestr(u"XBRLData/Attachment/x.htm", b"x")
            for n in names:
                z.writestr(n, b"x")
        try:
            ms.summary_zip(buf.getvalue())
            out.append(u"サマリーの member が 1 つでないのに止まらない(%d)" % len(names))
        except ms.Stop:
            pass
    return out


def self_closed_problems(ms=None):
    u"""封 §8 の 6: engine と同じ正規表現の一致のうち属性の列が ``/`` で終わるものを数える(数えるだけ)。"""
    ms = ms or MS
    out = []
    t = NIL_TAG.decode() + REAL_TAG.decode()
    if ms.self_closed_reads(t) != 1:
        out.append(u"自己閉じの読み取りが 1 つにならない: %d" % ms.self_closed_reads(t))
    if ms.self_closed_reads(REAL_TAG.decode()) != 0:
        out.append(u"普通の fact を自己閉じに数えた")
    if ms.self_closed_reads(NIL_TAG.decode() + NIL_TAG.decode() + REAL_TAG.decode()) != 1:
        out.append(u"自己閉じが続くときの一致の数が違う(engine の正規表現は最初の自己閉じから次の終わりの tag までを 1 つと読む)")
    if ms.self_closed_reads(REAL_TAG.decode() + NIL_TAG.decode()) != 0:
        out.append(u"終わりの tag の無い自己閉じを一致に数えた")
    if ms.self_closed_reads(u"<ix:nonFraction a=\"1\">\n9</ix:nonFraction>") != 0:
        out.append(u"改行を含む普通の fact を自己閉じに数えた")
    import io as _io
    import zipfile as _zf
    buf = _io.BytesIO()
    with _zf.ZipFile(buf, "w") as z:
        z.writestr(u"XBRLData/Summary/s-ixbrl.htm", NIL_TAG + REAL_TAG)
        z.writestr(u"XBRLData/Attachment/b-ixbrl.htm", NIL_TAG + REAL_TAG + NIL_TAG + REAL_TAG)
        z.writestr(u"XBRLData/Attachment/q.htm", b"<p>text</p>")
        z.writestr(u"XBRLData/Attachment/x.xml", NIL_TAG + REAL_TAG)
    if ms.self_closed_counts(buf.getvalue()) != (1, 2):
        out.append(u"サマリーと本体の数え分けが違う: %s" % (ms.self_closed_counts(buf.getvalue()),))
    return out


# ---------------------------------------------------------------- 5. 記録
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
    u"""記録に文・span・値・要素名・context・会社名・docID が無い(行の欄・字の形・禁止の欄の名前)。行は 22 欄の ints・真偽・固定の字だけ。"""
    out = []
    try:
        rec = json.loads(text)
    except ValueError:
        return [u"記録が JSON でない"]
    for p, v in walk(rec):
        if p and isinstance(p[-1], str) and p[-1] in (u"文", u"span", u"sentence", u"値", u"要素名", u"context", u"name", u"会社名", u"証券コード", u"docID", u"value"):
            out.append(u"記録に持たない欄が在る: %s" % (p[-1],))
    if DOCID_RE.search(text) or re.search(r"0812\d{14}", text):
        out.append(u"docID・TDnet の番号らしい字が在る")
    for r in rec.get(u"行", []):
        if len(r) != N_COL or not (isinstance(r[0], int) and isinstance(r[1], int) and isinstance(r[2], int)) or r[3] not in (u"P", u"W") or r[4] not in (u"円", u"%", u"他"):
            out.append(u"行の形が決めと違う")
            break
        if not all(isinstance(x, bool) for x in r[5:]):
            out.append(u"行の札が真偽でない")
            break
    return out


def rates(rec):
    for p, v in walk(rec):
        if isinstance(v, dict) and set(v) == {u"分子", u"分母", u"率"}:
            yield p, v


def rate_problems(rec):
    out = []
    n_seen = 0
    for p, v in rates(rec):
        n_seen += 1
        n, d, t = v[u"分子"], v[u"分母"], v[u"率"]
        if not (isinstance(n, int) and isinstance(d, int) and 0 <= n <= d) or not RATE_TEXT.match(t):
            out.append(u"率の欄の形が決めと違う: %s" % (p,))
            continue
        want = u"分母 0" if d == 0 else u"%d.%d%%" % divmod(int(Fraction(n, d) * 1000 + Fraction(1, 2)), 10)
        if t != want:
            out.append(u"率の字が分子・分母から出る字と違う: %s %s" % (p, t))
    if n_seen < 50:
        out.append(u"率の欄が少なすぎる(%d)" % n_seen)
    return out


def group_map():
    with open(os.path.join(ROOT, POPULATION_REL), encoding="utf-8") as fh:
        pop = json.load(fh)
    return dict((r[0], r[1]) for r in pop[u"行"])


def recount(rows, rd_idx, grp, group=None):
    u"""行から独立に数える(script の関数を使わない)。rd_idx = (当てない, F が空, 自, 実, 他) の列の番号。"""
    p = [r for r in rows if r[3] == u"P" and (group is None or grp[r[0]] == group)]
    na_i, fe_i, s_i, re_i, o_i = rd_idx
    applied = [r for r in p if not r[na_i] and not r[fe_i]]
    per, per_s = collections.Counter(r[0] for r in p), collections.Counter(r[0] for r in p if r[s_i])
    return {u"行": len(p), u"当てない": sum(r[na_i] for r in p), u"自": sum(r[s_i] for r in p), u"実": sum(r[re_i] for r in p), u"他": sum(r[o_i] for r in p),
            u"F が空の本の行": sum(r[fe_i] for r in p), u"当てた行で F が空でない本のもの": len(applied), u"scale が無い": sum(r[14] for r in p),
            u"本": len(per), u"自の本": len(per_s), u"最大": max(per_s.values()) if per_s else 0}


def invariant_problems(rows):
    u"""記録の行の不変(行の数の再現を要さない)。4 通りの読みの全部で。"""
    out = []
    for r in rows:
        if len(r) != N_COL:
            out.append(u"行の欄の数が %d でない" % N_COL)
            continue
        na, na2, ns = r[5], r[10], r[14]
        for (i_na, i_fe, i_s, i_re, i_o) in RD_IDX:
            if r[i_na] and (r[i_s] or r[i_re] or r[i_o]):
                out.append(u"当てない行に自・実・他が真")
            if r[i_fe] and r[i_s]:
                out.append(u"F が空の本の行で自が真")
        if r[7] and not r[11]:
            out.append(u"字のとおりで自なのに円の族で自でない")
        if r[16] and not r[19]:
            out.append(u"空の欄を除く読みで、字のとおりで自なのに円の族で自でない")
        if r[4] == u"他" and not (na and na2):
            out.append(u"単位の族が他の行が当てるになっている")
        if ns and not (na and na2):
            out.append(u"scale が無い行が当てるになっている")
        if na and not na2 and r[4] != u"円":
            out.append(u"字のとおりでだけ当てない行が円の族の単位でない")
        if na2 and not na:
            out.append(u"円の族で当てなくて字のとおりで当てる行(包含が逆)")
    return sorted(set(out))


#: 主の数(字のとおりの読み × サマリーをそのまま読む)。いまの記録の値で、空の欄を除く読みを足しても動かない(封 §8 の 3)
MAIN_P = {u"行": 794, u"当てない": 355, u"自": 193, u"実": 71, u"他": 8}
MAIN_W = {u"行": 20, u"当てない": 7, u"自": 5, u"実": 3, u"他": 0}
#: 自己閉じの tag から始まる読み取り(数えただけ)。サマリー 4,418 個・202 本・短信の本体 5,588 個・192 本(400 本のうち。封 §8 の 2・6 が司令塔の数えた数として書いた数と同じ)
SELF_CLOSED = {u"サマリー": (4418, 202, 400), u"短信の本体(Attachment の側の .htm)": (5588, 192, 400)}


def fact_stats_problems(fs):
    out = []
    subs = [(u"主", fs)] + [(k, v) for k, v in fs.items() if k.startswith(u"空の欄を除く読み(") and isinstance(v, dict)]
    if len(subs) != 2 or NOTE_NONNIL not in subs[1][0]:
        return [u"サマリーの fact の欄に空の欄を除く読み(あと知恵の字つき)が無い"]
    for name, d in subs:
        if sum(d[u"F の単位別の数"].values()) != d[u"F の fact の数の合計"] or d[u"F の fact の数の合計"] <= 0:
            out.append(u"F の fact の数の合計と単位別が合わない: %s" % name)
        if sum(d[u"R の単位別の数"].values()) != d[u"R の fact の数の合計"] or d[u"R の fact の数の合計"] <= 0:
            out.append(u"R の fact の数の合計と単位別が合わない: %s" % name)
        if sum(d[u"F が空の本の数の群別"].values()) != d[u"F が空の本の数(切れた本のうち)"]:
            out.append(u"F が空の本の数の群別の合計が合わない: %s" % name)
        if not (d[u"F の単位別の数"].get(u"JPY", 0) > 0 and d[u"F の単位別の数"].get(u"Pure", 0) > 0):
            out.append(u"F の単位別に JPY か Pure が無い(単位の字の取り違えを疑う): %s" % name)
    # 空の欄を除くと、壊れた fact が本物の fact になる: fact が減らない
    if subs[1][1][u"F の fact の数の合計"] < fs[u"F の fact の数の合計"] or subs[1][1][u"R の fact の数の合計"] < fs[u"R の fact の数の合計"]:
        out.append(u"空の欄を除く読みで fact の数が減った")
    sc = [v for k, v in fs.items() if k.startswith(u"自己閉じの tag から始まる読み取り")]
    if len(sc) != 1 or {k: (v[u"読み取りの数"], v[u"その読み取りを持つ本"], v[u"本"]) for k, v in sc[0].items()} != SELF_CLOSED:
        out.append(u"自己閉じの読み取りの数が決め(サマリー・本体)と違う")
    return out


def record_problems(ms=None, text=None, seal=None, with_script_tally=True):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
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
    out.extend(rate_problems(rec))
    if (rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT or rec.get(u"封の追記(§7)の commit") != ADDENDUM_COMMIT_SHORT
            or rec.get(u"封の追記(§8)の commit") != ADDENDUM8_COMMIT_SHORT):
        out.append(u"記録の封の path・commit・追記の commit(§7・§8)が違う")
    if rec.get(u"この script の sha256") != sha_of(SCRIPT_REL):
        out.append(u"記録の script の sha256 が実物と違う")
    if [(x.get(u"#"), x.get(u"path"), x.get(u"sha256")) for x in rec.get(u"入力", [])] != seal_inputs(seal):
        out.append(u"記録の入力が封 §1 の表と違う")
    if rec.get(u"母集団の記録の sha256") != sha_of(POPULATION_REL):
        out.append(u"記録の母集団の記録の sha256 が実物と違う")
    if rec.get(u"profile") != u"P33E":
        out.append(u"記録の profile が違う")
    lim = u"\n".join(rec.get(u"限界", []))
    for phrase in (u"同定ではない", u"engine は動かしていない", u"人は読んでいない", u"あと知恵", u"壊れた fact に当てた数で、同じ短信のサマリーの予想の fact に当たった率としては読めない",
                   NOTE_NONNIL):
        if phrase not in lim:
            out.append(u"記録の限界の字に無い: %s" % phrase[:20])
    rule = json.dumps(rec.get(u"照合の規則", {}), ensure_ascii=False)
    for phrase in (NOTE_FAMILY, u"字のとおり", u"scale は作らない", NOTE_NONNIL, u"<ix:nonFraction[^>]*/>"):
        if phrase not in rule:
            out.append(u"記録の照合の規則に無い: %s" % phrase)
    rows = rec.get(u"行", [])
    grp = group_map()
    out.extend(invariant_problems(rows))
    ps, ws = [r for r in rows if r[3] == u"P"], [r for r in rows if r[3] == u"W"]
    if len(ps) != 794 or len(ws) != 20 or rec.get(u"P の行の数") != 794 or rec.get(u"W の行の数") != 20:
        out.append(u"P が 794 行・W が 20 行でない")
    if [sum(1 for r in ps if grp[r[0]] == g) for g in GROUPS] != [129, 632, 33]:
        out.append(u"P の群別が 129・632・33 でない")
    if len(set((r[0], r[1], r[2], r[3]) for r in rows)) != len(rows):
        out.append(u"行の鍵が重なる")
    # 主の数(字のとおり × そのまま)の固定
    main_p = recount(rows, RD_IDX[0], grp)
    if {k: main_p[k] for k in MAIN_P} != MAIN_P:
        out.append(u"主の数(P)が決めと違う: %s" % {k: main_p[k] for k in MAIN_P})
    mw = {u"行": len(ws), u"当てない": sum(r[5] for r in ws), u"自": sum(r[7] for r in ws), u"実": sum(r[8] for r in ws), u"他": sum(r[9] for r in ws)}
    if mw != MAIN_W:
        out.append(u"主の数(W)が決めと違う: %s" % mw)
    # 記録の集計(4 通り)と行からの独立の数え直し
    labels = list(rec.get(u"集計", {}))
    ok_labels = (len(labels) == 4 and labels[0] == RD_LIT and labels[1].startswith(RD_FAM_PREFIX) and NOTE_FAMILY in labels[1] and NOTE_NONNIL not in labels[1]
                 and labels[2].startswith(u"字のとおりの読み") and NOTE_NONNIL in labels[2] and NOTE_FAMILY not in labels[2]
                 and labels[3].startswith(RD_FAM_PREFIX) and NOTE_NONNIL in labels[3] and NOTE_FAMILY in labels[3])
    if not ok_labels:
        out.append(u"集計の塊の名前が 4 通り(字のとおり・円の族・字のとおり × 空の欄を除く・円の族 × 空の欄を除く。あと知恵の字つき)でない")
        return out
    rd_list = (ms.READING_LITERAL, ms.READING_FAMILY, (ms.SUM_NONNIL, ms.READING_LITERAL), (ms.SUM_NONNIL, ms.READING_FAMILY))
    for label, rd_idx, rd in zip(labels, RD_IDX, rd_list):
        for gname, sect in [(None, rec[u"集計"][label][u"全体"])] + [(g, rec[u"集計"][label][u"群"][g]) for g in GROUPS]:
            want = recount(rows, rd_idx, grp, gname)
            pp = sect[u"P"]
            got = {u"行": pp[u"行"], u"当てない": pp[u"当てない"], u"自": pp[u"自"], u"実": pp[u"実"], u"他": pp[u"他"], u"F が空の本の行": pp[u"F が空の本の行"],
                   u"当てた行で F が空でない本のもの": pp[u"当てた行で F が空でない本のもの"], u"scale が無い": pp[u"うち scale が無い行"],
                   u"本": pp[u"本"][u"P の行を持つ本"], u"自の本": pp[u"本"][u"自の行を持つ本"], u"最大": pp[u"本"][u"いちばん多い 1 本が持つ自の行の数"]}
            if got != want:
                out.append(u"記録の P の集計が行の数え直しと違う: %s %s" % (label[:12], gname))
            if pp[u"主の率(自 / 行の全部)"] != {u"分子": want[u"自"], u"分母": want[u"行"], u"率": ms.rate(want[u"自"], want[u"行"])[u"率"]}:
                out.append(u"主の率が自 / 行の全部でない: %s %s" % (label[:12], gname))
            if pp[u"並べる率(自 / 当てた行で F が空でない本のもの)"][u"分母"] != want[u"当てた行で F が空でない本のもの"]:
                out.append(u"並べる率の分母が違う: %s %s" % (label[:12], gname))
            for fam in (u"円", u"%", u"他"):
                sub = [r for r in ps if r[4] == fam and (gname is None or grp[r[0]] == gname)]
                if pp[u"単位別"][fam][u"行"] != len(sub) or pp[u"単位別"][fam][u"自"] != sum(r[rd_idx[2]] for r in sub):
                    out.append(u"単位別の数が行の数え直しと違う: %s %s %s" % (label[:12], gname, fam))
            w = [r for r in ws if gname is None or grp[r[0]] == gname]
            ww = sect[u"W"]
            if (ww[u"行"], ww[u"当てない"], ww[u"自"], ww[u"実"], ww[u"他"], ww[u"うち scale が無い行"]) != (
                    len(w), sum(r[rd_idx[0]] for r in w), sum(r[rd_idx[2]] for r in w), sum(r[rd_idx[3]] for r in w), sum(r[rd_idx[4]] for r in w), sum(r[14] for r in w)):
                out.append(u"W の集計が行の数え直しと違う: %s %s" % (label[:12], gname))
            nn = sect[u"N"]
            if not (nn[u"自"] <= nn[u"行"] - nn[u"当てない"] and nn[u"他"] <= nn[u"行"] - nn[u"当てない"] and nn[u"実"] <= nn[u"行"] - nn[u"当てない"]):
                out.append(u"N の自・実・他が当てた行より多い: %s %s" % (label[:12], gname))
            if with_script_tally:
                pr = [r for r in ps if gname is None or grp[r[0]] == gname]
                a = json.dumps(ms.p_part(pr, rd), ensure_ascii=False, sort_keys=True)
                b = dict(pp)
                for k in (u"単位別", u"本"):
                    b.pop(k)
                if a != json.dumps(b, ensure_ascii=False, sort_keys=True):
                    out.append(u"script の集計関数が記録の行から作る数が記録と違う: %s %s" % (label[:12], gname))
    # 群別の N の合計が全体
    for label in labels:
        for k in (u"行", u"自", u"他"):
            if sum(rec[u"集計"][label][u"群"][g][u"N"][k] for g in GROUPS) != rec[u"集計"][label][u"全体"][u"N"][k]:
                out.append(u"N の群別の合計が全体と違う")
    # N の行の数は読みに依らない(GROUNDED の行の全部)
    if len(set(rec[u"集計"][l][u"全体"][u"N"][u"行"] for l in labels)) != 1:
        out.append(u"N の行の数が読みで違う")
    out.extend(fact_stats_problems(rec[u"サマリーの fact"]))
    if rec[u"作り直しの確認"][u"本"] != 400:
        out.append(u"作り直しの確認の本が 400 でない")
    return out


# ---------------------------------------------------------------- 6. types・sheet
def sample_items_real():
    return MS.sample_items(MS.load_json(os.path.join(ROOT, RECORD_REL)))


def gate_letter(ident):
    u"""読みの軸の封 §2-3 を門の側で独立に書いた決め方(script の関数を使わない)。"""
    if any(ch == u"違" for ch in ident):
        return u"い"
    if ident[0] == u"合" and ident[1] == u"合":
        return u"あ"
    return u"う"


IDENT_PATTERNS = (u"合合合合合", u"合不合合合", u"不合合合合", u"合違合合合", u"違合不合合", u"合合不合合", u"合合合違違", u"不不不不不", u"合合合合不")
AXES = (1, 2, 3, 4)
ATTR_NAMES = (u"項目", u"期", u"範囲", u"予想の種類", u"1 株あたり")


def fake_typed(items):
    u"""作り物の 7 列の字(標本の行に 1 対 1)。値の軸と身元の型を回して全部の字・全部の値の軸が出る。[(標本の番号, 本の #, 文の番号, 位置, 値の軸, 身元, 字)]。"""
    out = []
    for it in items:
        ident = IDENT_PATTERNS[it[0] % len(IDENT_PATTERNS)]
        out.append((it[0], it[1], it[2], it[3], AXES[(it[0] // 3) % 4], ident, gate_letter(ident)))
    return out


def tsv_lines(rows):
    return [u"\t".join([str(x) for x in r[:5]] + [r[5], r[6]]) for r in rows]


def recount_types(items, typed):
    u"""集計の数を作り物の字から独立に数え直す。{組: (読んだ行, 値の軸ごと, 属性 × 合違不, あいう, 値の軸 × あいう, 違の属性ごと, 値 1・2 の違の属性ごと)}。"""
    res = {}
    for g in (u"甲組", u"乙組", u"W組"):
        rows = [t for it, t in zip(items, typed) if it[4] == g]
        ax = [sum(1 for t in rows if t[4] == a) for a in AXES]
        at = [[sum(1 for t in rows if t[5][i] == ch) for ch in u"合違不"] for i in range(5)]
        lt = [sum(1 for t in rows if t[6] == ch) for ch in u"あいう"]
        cross = [[sum(1 for t in rows if t[4] == a and t[6] == ch) for ch in u"あいう"] for a in AXES]
        d = [t for t in rows if u"違" in t[5]]
        d12 = [t for t in d if t[4] in (1, 2)]
        res[g] = (len(rows), ax, at, lt, cross, [sum(1 for t in d if t[5][i] == u"違") for i in range(5)], [sum(1 for t in d12 if t[5][i] == u"違") for i in range(5)], len(d), len(d12))
    return res


def counts_of_record(sec):
    ax = [sec[u"値の軸ごとの行の数"][str(a)][u"分子"] for a in AXES]
    at = [[sec[u"身元の属性ごとの 合・違・不 の行の数"][nm][ch][u"分子"] for ch in u"合違不"] for nm in ATTR_NAMES]
    lt = [sec[u"あ・い・う の行の数"][ch][u"分子"] for ch in u"あいう"]
    cross = [[sec[u"値の軸 × あ・い・う の行の数"][str(a)][ch] for ch in u"あいう"] for a in AXES]
    dk = [k for k in sec[u"身元に 違 が在る行"] if k.startswith(u"違 の属性")][0]
    dk12 = [k for k in sec[u"値の軸が 1 か 2 で身元に 違 が在る行"] if k.startswith(u"違 の属性")][0]
    d = [sec[u"身元に 違 が在る行"][dk][nm] for nm in ATTR_NAMES]
    d12 = [sec[u"値の軸が 1 か 2 で身元に 違 が在る行"][dk12][nm] for nm in ATTR_NAMES]
    return (sec[u"読んだ行"], ax, at, lt, cross, d, d12, sec[u"身元に 違 が在る行"][u"行の数"][u"分子"], sec[u"値の軸が 1 か 2 で身元に 違 が在る行"][u"行の数"][u"分子"])


def types_entry_problems(ms=None):
    u"""作り物の字の file で ``types`` を走らせる(複製の先)。7 列・標本の行と 1 対 1(順も)・値の軸は 1〜4・身元は 合・違・不・字は身元から決めた字・文や値を持たない・組別の集計が独立の数え直しと同じ。"""
    ms = ms or MS
    out = []
    items = ms.sample_items(ms.load_json(os.path.join(ROOT, RECORD_REL)))
    tmp = tempfile.mkdtemp(prefix="ps_types_")
    try:
        def write(name, lines):
            p = os.path.join(tmp, name)
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(u"\n".join(lines) + u"\n")
            return p
        typed = fake_typed(items)
        good = tsv_lines(typed)
        path = write("typed.tsv", good)
        o = os.path.join(tmp, "out.json")
        rec = ms.run_types(os.path.join(ROOT, RECORD_REL), path, o, say=lambda *a: None)
        text = open(o, encoding="utf-8").read()
        want = recount_types(items, typed)
        for g in (u"甲組", u"乙組", u"W組"):
            if g not in rec[u"集計"] or counts_of_record(rec[u"集計"][g]) != want[g]:
                out.append(u"types の組別の集計が独立の数え直しと違う: %s" % g)
        if [r[:5] for r in rec[u"行"]] != [list(it[:5]) for it in items] or [r[5:] for r in rec[u"行"]] != [[t[4], t[5], t[6]] for t in typed] or leak_problems_types(text):
            out.append(u"types の行が標本とそろわない・文や値が在る")
        if rec.get(u"読みの軸の封の commit") != AXES_SEAL_COMMIT_SHORT or rec.get(u"読みの軸の封") != AXES_SEAL_REL:
            out.append(u"types の記録の読みの軸の封の path・commit が違う")
        L = good[0].split(u"\t")

        def line(k, **ch):
            c = list(good[k].split(u"\t"))
            for i, v in ch.items():
                c[int(i[1:])] = v
            return u"\t".join(c)
        bad_cases = (
            (u"字が あ/い/う の外", good[:-1] + [line(len(good) - 1, c6=u"え")]),
            (u"字が身元から決めた字と食い違う(あ → い)", [line(0, c5=u"合合合合合", c6=u"い")] + good[1:]),
            (u"字が身元から決めた字と食い違う(違が在るのに あ)", good[:3] + [line(3, c5=u"合違合合合", c6=u"あ")] + good[4:]),
            (u"字が身元から決めた字と食い違う(項目が 不 なのに あ)", good[:1] + [line(1, c5=u"不合合合合", c6=u"あ")] + good[2:]),
            (u"値の軸が 5", [line(0, c4=u"5")] + good[1:]),
            (u"値の軸が 0", [line(0, c4=u"0")] + good[1:]),
            (u"身元が 4 字", [line(0, c5=u"合合合合", c6=u"あ")] + good[1:]),
            (u"身元が 6 字", [line(0, c5=u"合合合合合合", c6=u"あ")] + good[1:]),
            (u"身元に 合・違・不 の外の字", [line(0, c5=u"合合合合×", c6=u"あ")] + good[1:]),
            (u"行が 1 つ足りない", good[:-1]),
            (u"同じ番号が 2 行", good + [good[0]]),
            (u"順が標本と違う", [good[1], good[0]] + good[2:]),
            (u"本の # が標本と違う", [line(0, c1=u"9" + L[1])] + good[1:]),
            (u"列が足りない(5 列の古い形)", [u"\t".join(L[:4] + [u"あ"])] + good[1:]),
            (u"列が多い", [good[0] + u"\tx"] + good[1:]))
        for label, lines in bad_cases:
            try:
                ms.run_types(os.path.join(ROOT, RECORD_REL), write("bad.tsv", lines), os.path.join(tmp, "o_%d.json" % abs(hash(label))), say=lambda *a: None)
                out.append(u"types が止まらない: %s" % label)
            except ms.Stop:
                pass
        try:
            ms.run_types(os.path.join(ROOT, RECORD_REL), path, o, say=lambda *a: None)
            out.append(u"在る出力に types が止まらない")
        except ms.Stop:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def leak_problems_types(text):
    rec = json.loads(text)
    bad = [p[-1] for p, _v in walk(rec) if p and isinstance(p[-1], str) and p[-1] in (u"文", u"span", u"sentence", u"値", u"要素名", u"context", u"name", u"value", u"会社名", u"証券コード", u"docID")]
    cells = all(len(r) == 8 and all(isinstance(x, int) for x in r[:4]) and r[4] in (u"甲組", u"乙組", u"W組") and r[5] in (1, 2, 3, 4)
                and len(r[6]) == 5 and all(ch in u"合違不" for ch in r[6]) and r[7] in (u"あ", u"い", u"う") for r in rec[u"行"])
    return bad or not cells or DOCID_RE.search(text)


def types_rec_problems(rec, text, states_sha, items, ms=None):
    u"""read_types の記録の形と不変(行が標本の行と 1 対 1・集計が行からの数え直しと一致・字が §2-3 の決め方と一致・states の sha256・key_leaks・席・盲検)。"""
    ms = ms or MS
    out = []
    if leak_problems_types(text):
        out.append(u"types の記録に文や値が在る・行が形に合わない")
        return out
    if [r[:5] for r in rec[u"行"]] != [list(it[:5]) for it in items]:
        out.append(u"types の記録の行が標本の行と違う")
    if len(rec[u"行"]) != 109 or [sum(1 for r in rec[u"行"] if r[4] == g) for g in (u"甲組", u"乙組", u"W組")] != [60, 30, 19]:
        out.append(u"types の記録が 109 行・組 60・30・19 でない")
    if rec.get(u"states の記録の sha256") != states_sha:
        out.append(u"types の記録の states の sha256 が実物と違う")
    if u"人は読んでいない" not in rec.get(u"型を付けた席", u"") or u"盲検ではない" not in rec.get(u"盲検", u""):
        out.append(u"types の記録の席・盲検の字が無い")
    if rec.get(u"key_leaks") != []:
        out.append(u"types の記録の key_leaks が空でない")
    if rec.get(u"読みの軸の封") != AXES_SEAL_REL or rec.get(u"読みの軸の封の commit") != AXES_SEAL_COMMIT_SHORT:
        out.append(u"types の記録の読みの軸の封の path・commit が違う")
    if (rec.get(u"seal"), rec.get(u"封の commit"), rec.get(u"封の追記(§7)の commit"), rec.get(u"封の追記(§8)の commit")) != (SEAL_REL, SEAL_COMMIT_SHORT, ADDENDUM_COMMIT_SHORT, ADDENDUM8_COMMIT_SHORT):
        out.append(u"types の記録の封の path・commit が違う")
    if rec.get(u"この script の sha256") != sha_of(SCRIPT_REL):
        out.append(u"types の記録の script の sha256 が実物と違う")
    for r in rec[u"行"]:
        if gate_letter(r[6]) != r[7]:
            out.append(u"types の記録の字が身元の 5 字から §2-3 で決めた字と違う: 標本 %d" % r[0])
            break
    typed = [(r[0], r[1], r[2], r[3], r[5], r[6], r[7]) for r in rec[u"行"]]
    want = recount_types(items, typed)
    for g in (u"甲組", u"乙組", u"W組"):
        if g not in rec.get(u"集計", {}) or counts_of_record(rec[u"集計"][g]) != want[g]:
            out.append(u"types の記録の集計が行の数え直しと違う: %s" % g)
    out.extend(rate_problems_loose(rec))
    return out


def types_record_problems():
    u"""types の記録が在り、形と不変が合う(記録が無ければ赤)。"""
    p = os.path.join(ROOT, TYPES_REL)
    if not os.path.isfile(p):
        return [u"types の記録が無い"]
    text = read(TYPES_REL)
    return types_rec_problems(json.loads(text, object_pairs_hook=collections.OrderedDict), text, sha_of(RECORD_REL), sample_items_real())


def rate_problems_loose(rec):
    out = []
    n_seen = 0
    for p, v in rates(rec):
        n_seen += 1
        want = u"分母 0" if v[u"分母"] == 0 else u"%d.%d%%" % divmod(int(Fraction(v[u"分子"], v[u"分母"]) * 1000 + Fraction(1, 2)), 10)
        if v[u"率"] != want:
            out.append(u"types の率の字が違う")
    if n_seen < 72:
        out.append(u"types の率の欄が少なすぎる(%d)" % n_seen)
    return out


def sheet_problems(ms=None):
    u"""sheet は repo の中への書き出しを止める(紙は書かない)。標本の組の数が封 §7・§8 のとおり(実物の記録で、空の欄を除く読みの札から 甲組 60・乙組 30・W組は円の族で自の W)。"""
    ms = ms or MS
    out = []
    inside = os.path.join(ROOT, "fixtures", "x_ps_gate_sheet.tsv")
    try:
        ms.run_sheet(os.path.join(ROOT, RECORD_REL), os.path.join(ROOT, "fixtures"), inside, say=lambda *a: None)
        out.append(u"repo の中の紙で止まらない")
    except ms.Stop:
        pass
    if os.path.exists(inside):
        out.append(u"repo の中に紙が書かれた")
        os.remove(inside)
    states = ms.load_json(os.path.join(ROOT, RECORD_REL))
    items = ms.sample_items(states)
    rows = states[u"行"]
    want = (min(60, sum(1 for r in rows if r[3] == u"P" and r[16])), min(30, sum(1 for r in rows if r[3] == u"P" and r[19] and not r[16])),
            sum(1 for r in rows if r[3] == u"W" and r[19]))
    got = (sum(1 for it in items if it[4] == u"甲組"), sum(1 for it in items if it[4] == u"乙組"), sum(1 for it in items if it[4] == u"W組"))
    if got != want:
        out.append(u"実物の記録の標本の組の数が違う: %s(期待 %s)" % (got, want))
    return out


# ---------------------------------------------------------------- 7. 配線
def import_problems(src=None):
    u"""script の import は 標準ライブラリの一覧と engine の adapters.xbrl だけ。通信・subprocess を import しない(ast)。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"") + (u"." + a.name if n.module == u"adapters.xbrl" else u"") for a in n.names]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "exec", "eval"):
            out.append(u"動的な import・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK_MODULES:
                out.append(u"通信・subprocess の module を import している: %s" % nm)
            elif top == u"adapters":
                if not (nm.startswith(u"adapters.xbrl.") and nm.split(".")[2] in (u"instance", u"verify_document", u"vocabulary")):
                    out.append(u"許す engine の module の外: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    return out


def boundary_problems():
    p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
    with open(p, encoding="utf-8") as fh:
        t = fh.read()
    return [u"test_boundary.py にこの便の名前が在る"] if (u"plan_source" in t) else []


def engine_since_seal_problems(root=REPO):
    c = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(c) != 1:
        return [u"封の commit が履歴に 1 つに決まらない"]
    rc, log = PR.git_in(root, "log", "--format=%H", "%s..HEAD" % c[0], "--", *[PREFIX + r for r in NOT_TOUCHED_RELS])
    if rc != 0:
        return [u"git log が失敗した"]
    return [u"封の後に engine・lib・入力を触った commit %s" % x[:7] for x in log.split() if x and not SGR.nre_explained_commit(root, x, [PREFIX + r for r in NOT_TOUCHED_RELS])]      # 2026-11-17(NRE): 封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md §2-3 が宣言した遷移(instance.py の式 1 行の置き換え 1・1)だけを許す。NRE の engine の commit ただ 1 つで、その commit の rels への変更が宣言の行だけのときに限り一覧から外す(SGR.nre_explained_commit。他の commit・他の行は問題のまま)


def engine_worktree_problems(root=REPO):
    rc, st = PR.git_in(root, "status", "--porcelain", "--untracked-files=all", "--", *[PREFIX + r for r in NOT_TOUCHED_RELS])
    if rc != 0:
        return [u"git status が失敗した"]
    return [u"engine・lib・入力に未 commit の変更: %s" % ln.strip()[:2] for ln in st.splitlines() if ln.strip()]


# ---------------------------------------------------------------- 8. 順序
def addendum_problems(root, prefix, seal_rel, addendum_short, others):
    u"""追記の commit(封の file を触った commit のうち addendum_short で始まるもの)が、others の各 file を足した commit の祖先であること。未 commit・追記が無い・追記が後は赤。"""
    out = []
    rc, log = PR.git_in(root, "log", "--format=%H", "--", prefix + seal_rel)
    add = [x for x in log.split() if x.startswith(addendum_short)]
    if len(add) != 1:
        return [u"ADDENDUM_NOT_FOUND"]
    for rel in others:
        a = PR.added_commits(root, prefix + rel)
        if not a:
            out.append(u"UNCOMMITTED:" + rel)
        elif a[-1] == add[0] or not PR.is_anc(root, add[0], a[-1]):
            out.append(u"NOT_AFTER_ADDENDUM:" + rel)
    return out


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(ORDER_FILES) if others is None else others
    return (PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others) + addendum_problems(root, PREFIX, SEAL_REL, ADDENDUM_COMMIT_SHORT, others)
            + addendum_problems(root, PREFIX, SEAL_REL, ADDENDUM8_COMMIT_SHORT, others))


# ---------------------------------------------------------------- 変異
#: (名前, script の中の字 old, new, 赤になるはずの検査の名前の並び)。old は script に 1 回だけ在る字
MUTANTS = (
    (u"M01 円の族の単位の字から 億円 を落とす", u'YEN_UNITS = (u"円", u"千円", u"万円", u"百万円", u"億円", u"兆円")', u'YEN_UNITS = (u"円", u"千円", u"万円", u"百万円", u"兆円")', ("seal", "match")),
    (u"M02 字のとおりの読みに円の族を混ぜる", u'yen = (u"円",) if reading == READING_LITERAL else YEN_UNITS', u"yen = YEN_UNITS", ("match",)),
    (u"M03 Pure に ×100 を掛けない", u"x = fact_value * 100", u"x = fact_value", ("match",)),
    (u"M04 円の照合の帯を 10 倍に広げる", u'claim["claim_scale"], None, False) is not None', u'claim["claim_scale"] * 10, None, False) is not None', ("match",)),
    (u"M05 円の fact の単位の見方を外す(JPY で始まらなくても当てる)", u"if not str(fact_unit).upper().startswith(JPY_PREFIX):", u"if False:", ("match",)),
    (u"M06 % の fact の単位が Pure かの見方を外す", u"if fact_unit != PURE_UNIT:", u"if False:", ("match",)),
    (u"M07 % の絶対値の当たりを落とす", u' or abs(abs(x) - abs(claim["value"])) <= tol', u"", ("match",)),
    (u"M08 % の既定の帯を 0.15 → 0.5", u"PCT_TOLERANCE_DEFAULT = 0.15", u"PCT_TOLERANCE_DEFAULT = 0.5", ("match",)),
    (u"M09 F の member の名を 1 つ落とす(LowerMember)", u'FORECAST_MEMBERS = ("ForecastMember", "UpperMember", "LowerMember")', u'FORECAST_MEMBERS = ("ForecastMember", "UpperMember")', ("seal", "split")),
    (u"M10 値が 0 の fact を除かない", u'if not f.get("unit") or not f.get("value"):', u'if not f.get("unit"):', ("split",)),
    (u"M11 別の本を自分にする", u"out[n] = r[(r.index(n) + 1) % len(r)]", u"out[n] = n", ("other",)),
    (u"M12 輪の本が 1 本以下でも止めない", u"if len(r) <= 1:", u"if False:", ("other",)),
    (u"M13 輪に居ない本の行き先を最初の本に固定する", u"out[n] = later[0] if later else r[0]", u"out[n] = r[0]", ("other",)),
    (u"M14 scale が無い claim も当てる(scale の見方を外す)", u'if claim.get("unit_scale") is None or claim.get("claim_scale") is None:\n            return None', u"if False:\n            return None", ("match",)),
    (u"M15 scale が無い行の札を「と」にする(片方だけ無いものを落とす)", u'(claim.get("unit_scale") is None or claim.get("claim_scale") is None)', u'(claim.get("unit_scale") is None and claim.get("claim_scale") is None)', ("match",)),
    (u"M16 標本の種を替える", u"SAMPLE_SEED = 20261117", u"SAMPLE_SEED = 20261118", ("seal", "sample")),
    (u"M17 乙組の「字のとおりでは自でない」を外す", u"and r[R_SELF2_N] and not r[R_SELF_N]), key=key)", u"and r[R_SELF2_N]), key=key)", ("sample",)),
    (u"M18 W組を字のとおりの読みの自で引く", u"if r[R_SET] == SET_W and r[R_SELF2_N]), key=key)", u"if r[R_SET] == SET_W and r[R_SELF_N]), key=key)", ("sample",)),
    (u"M19 P の行の数の確認を外す", u"if expect_p is not None and n_p != expect_p:", u"if False:", ("stop",)),
    (u"M20 W の行が当たらなくても止めない", u"if w_left:", u"if False:", ("stop",)),
    (u"M21 入力の sha256 の照合を外す", u"if not os.path.isfile(p) or ST.sha256_file(p) != want:", u"if False:", ("stop",)),
    (u"M22 入力の表の 1 つの sha256 の先頭を替える", u'"00414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"', u'"10414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"', ("seal", "input_sha", "stop")),
    (u"M23 率の字の四捨五入を切り捨てにする", u"(n * 2000 + d) // (2 * d)", u"(n * 1000) // d", ("rate",)),
    (u"M24 主の率の分母を当てた行だけにする", u'(u"主の率(自 / 行の全部)", rate(s, n))', u'(u"主の率(自 / 行の全部)", rate(s, applied))', ("tally",)),
    (u"M25 他の数に別の本でなく自分の本の F を使う(札の数え)", u"s = sum(1 for r in rows if r[iS])\n    re_", u"s = sum(1 for r in rows if r[iS] and not r[R_OTHER])\n    re_", ("tally",)),
    (u"M26 追記の commit の定数を替える", u'ADDENDUM_COMMIT = "5b38862e"', u'ADDENDUM_COMMIT = "5b38862f"', ("seal",)),
    (u"M31 analyze が別の本の F でなく自分の本の F を使う", u"f_other = by_n[other[rd[0]][b[u\"#\"]]][fk]", u"f_other = b[fk]", ("analyze",)),
    (u"M32 W の型の字を ウ から エ に取り違える", u'TYPE_W = u"ウ"', u'TYPE_W = u"エ"', ("seal", "wkeys")),
    (u"M33 円の fact の単位の接頭辞を JPY から JP に緩める(JPXX が円の fact になる)", u'JPY_PREFIX = "JPY"', u'JPY_PREFIX = "JP"', ("seal", "match")),
    (u"M34 空の欄を除く正規表現を当たらない形にする", u'NIL_TAG_RE = re.compile(br"<ix:nonFraction[^>]*/>")', u'NIL_TAG_RE = re.compile(br"<ix:nonFractionX[^>]*/>")', ("seal", "strip")),
    (u"M35 空の欄を除く正規表現を貪欲にする(本物の fact にまたがる)", u'NIL_TAG_RE = re.compile(br"<ix:nonFraction[^>]*/>")', u'NIL_TAG_RE = re.compile(br"<ix:nonFraction.*/>")', ("seal", "strip")),
    (u"M36 サマリーを除く読みを作らない(strip が効かない)", u"    if strip:\n        data = strip_nil_tags(data)\n", u"", ("strip",)),
    (u"M37 別の本の輪をそのままの読みの F で作る(空の欄を除く読みの輪に使う)", u'for sr, fk in ((SUM_RAW, u"F"), (SUM_NONNIL, u"F2")):', u'for sr, fk in ((SUM_RAW, u"F"), (SUM_NONNIL, u"F")):', ("analyze",)),
    (u"M38 空の欄を除く読みの札に F でなく F2 でない側(F)を渡す", u"fk, rk = fk_of[rd[0]]", u"fk, rk = fk_of[SUM_RAW]", ("analyze",)),
    (u"M39 標本の甲組をそのままの読みの札から引く", u"kou = sorted((r for r in rows if r[R_SET] == SET_P and r[R_SELF_N]), key=key)", u"kou = sorted((r for r in rows if r[R_SET] == SET_P and r[R_SELF]), key=key)", ("sample",)),
    (u"M40 自己閉じの数えで属性の列が / で終わる条件を外す", u'if m.group(1).endswith("/"))', u"if True)", ("selfclosed",)),
    (u"M41 本体の数えを .htm でなく .xml にする", u'BODY_SUFFIX = ".htm"', u'BODY_SUFFIX = ".xml"', ("selfclosed",)),
    (u"M42 F が空の本の札を空の欄を除く読みでもそのままの F で付ける", u"not b[u\"F\"], s, re_, ot, na2, s2, re2, ot2, no_scale(e),\n                                 not b[u\"F2\"]", u"not b[u\"F\"], s, re_, ot, na2, s2, re2, ot2, no_scale(e),\n                                 not b[u\"F\"]", ("analyze",)),
    (u"M27 通信の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport urllib.request\n", ("import",)),
    (u"M28 許す一覧の外の engine の module を import する(行を足す)", u"import argparse\n", u"import argparse\nfrom adapters.xbrl import prose\n", ("import",)),
    (u"M29 types が標本の行との合致を見ない", u"if k not in want or tuple(int(p) for p in parts[1:4]) != tuple(want[k]):", u"if False:", ("types",)),
    (u"M30 types が あ/い/う の外の字を通す(字の形の検査と身元との食い違いの検査の両方を外す。1 つだけ外しても、もう 1 つが止める)",
     ((u"or parts[6] not in READ_LETTERS):", u"or False):"), (u"if letter_of(parts[5]) != parts[6]:", u"if False:")), None, ("types",)),
    (u"M43 types が元の封の字と身元の食い違いを見ない", u"if letter_of(parts[5]) != parts[6]:", u"if False:", ("types",)),
    (u"M44 元の封の字の決め方で 違 が在っても い にしない", u'if u"違" in ident:\n        return u"い"', u'if False:\n        return u"い"', ("types",)),
    (u"M45 元の封の字の決め方で あ に期を要らなくする", u'ident[0] == u"合" and ident[1] == u"合"', u'ident[0] == u"合"', ("types",)),
    (u"M46 値の軸の範囲を 1〜5 に広げる", u"int(parts[4]) not in VALUE_AXES", u"int(parts[4]) not in (1, 2, 3, 4, 5)", ("types",)),
    (u"M47 身元の字の外の字を通す", u"any(ch not in IDENT_LETTERS for ch in parts[5])", u"False", ("types",)),
    (u"M48 身元の字数を見ない", u"len(parts[5]) != len(IDENT_ATTRS) or ", u"", ("types",)),
    (u"M49 行の順を見ない", u"if list(out) != [it[0] for it in items]:", u"if False:", ("types",)),
    (u"M50 集計の 違 の属性の数え方で属性の添字をずらす", u'(nm, sum(1 for x in rows if x[1][i] == u"違")) for i, nm in enumerate(IDENT_ATTRS))', u'(nm, sum(1 for x in rows if x[1][(i + 1) % 5] == u"違")) for i, nm in enumerate(IDENT_ATTRS))', ("types",)),
    (u"M51 集計の「値が 1 か 2」を 1 だけにする", u"diff12 = [x for x in diff if x[0] in (1, 2)]", u"diff12 = [x for x in diff if x[0] in (1,)]", ("types",)),
    (u"M52 集計の 値の軸 × あ・い・う の行と列を取り違える", u"sum(1 for x in t if x[0] == a and x[2] == ch)", u"sum(1 for x in t if x[0] == a and x[2] == u\"あ\")", ("types",)),
    (u"M53 読みの軸の封の commit の字を替える", u'AXES_SEAL_COMMIT = "06d7b8a7"', u'AXES_SEAL_COMMIT = "06d7b8a8"', ("types",)),
)


def tally_problems(ms):
    u"""script の集計関数に、記録の行から数えさせて記録と照らす(変異 M24・M25 用)。"""
    return record_problems(ms, with_script_tally=True)


def check_by_name(name, mod, src):
    if name == u"seal":
        return seal_problems(mod)
    if name == u"input_sha":
        return input_sha_problems(mod)
    if name == u"stop":
        return stop_problems(mod)
    if name == u"match":
        return match_problems(mod)
    if name == u"split":
        return split_problems(mod)
    if name == u"other":
        return other_problems(mod)
    if name == u"sample":
        return sample_problems(mod)
    if name == u"rate":
        return rate_function_problems(mod)
    if name == u"tally":
        return tally_problems(mod)
    if name == u"analyze":
        return analyze_problems(mod)
    if name == u"wkeys":
        return w_keys_problems(mod)
    if name == u"strip":
        return strip_problems(mod)
    if name == u"selfclosed":
        return self_closed_problems(mod)
    if name == u"types":
        return types_entry_problems(mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


def run_mutants():
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in MUTANTS:
        if new is None:                              # 複数の字を同時に替える変異(old は (old, new) の並び)
            src = base
            for o, n in old:
                assert src.count(o) == 1, (name, o, src.count(o))
                src = src.replace(o, n)
        else:
            assert base.count(old) == 1, (name, base.count(old))
            src = base.replace(old, new)
        try:
            mod = load_source(src)
        except BaseException as exc:                # noqa: BLE001
            out.append((name, [(c, True) for c in checks], u"読めない: %s" % type(exc).__name__))
            continue
        res = [(c, bool(guard(check_by_name, c, mod, src))) for c in checks]
        out.append((name, res, u""))
    return out


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_tables_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_history_is_the_sealed_commit_plus_the_addendum_and_the_first_six_sections_are_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"`d1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183`", u"`e1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183`", 1)))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"同じ種で 30 行", u"")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"単位の表から scale を作る規則は足さない", u"", 1)))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"## §8 追記", u"## §9 追記", 1)))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"`<ix:nonFraction[^>]*/>`", u"`<ix:nonFraction[^>]*>`")))


class InputTest(unittest.TestCase):
    def test_b_1_the_five_inputs_have_the_sealed_sha256(self):
        self.assertEqual([], input_sha_problems())

    def test_b_2_stops_on_a_changed_input_a_wrong_p_count_and_an_unmatched_w_row(self):
        self.assertEqual([], stop_problems())


class MatchTest(unittest.TestCase):
    def test_c_1_the_money_example_does_not_match_literally_and_matches_by_the_yen_family(self):
        self.assertEqual([], match_problems())

    def test_c_2_rates_are_rounded_by_integer_arithmetic(self):
        self.assertEqual([], rate_function_problems())

    def test_c_3_forecast_and_real_facts_are_split_by_member_name(self):
        self.assertEqual([], split_problems())

    def test_c_4_the_other_book_is_the_next_one_in_the_ring_of_the_same_group(self):
        self.assertEqual([], other_problems())

    def test_c_5_the_three_sample_groups_are_drawn_as_sealed(self):
        self.assertEqual([], sample_problems())

    def test_c_6_analyze_uses_the_other_books_forecast_facts_and_one_ring_per_summary_reading(self):
        self.assertEqual([], analyze_problems())

    def test_c_7_the_w_rows_are_the_rows_typed_u_only(self):
        self.assertEqual([], w_keys_problems())

    def test_c_8_the_empty_cell_stripper_matches_the_sealed_examples_and_fixes_the_broken_fact(self):
        self.assertEqual([], strip_problems())

    def test_c_9_self_closed_reads_are_counted_as_the_engine_reads_them(self):
        self.assertEqual([], self_closed_problems())


class RecordTest(unittest.TestCase):
    def test_d_1_the_record_has_the_sealed_fields_and_equals_the_recount_from_its_rows(self):
        self.assertEqual([], record_problems())

    def test_d_2_a_record_with_one_number_changed_is_red(self):
        text = read(RECORD_REL)
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
        lab = list(rec[u"集計"])[0]
        a = text.index(u'"自": 193')
        self.assertNotEqual([], record_problems(text=text[:a] + u'"自": 194' + text[a + len(u'"自": 193'):]))
        rec[u"集計"][lab][u"全体"][u"P"][u"主の率(自 / 行の全部)"][u"率"] = u"24.4%"
        self.assertNotEqual([], rate_problems(rec))
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
        i = next(n for n, r in enumerate(rec[u"行"]) if r[3] == u"P" and r[7])
        rec[u"行"][i][5] = True                                              # 当てないなのに自
        self.assertNotEqual([], record_problems(text=json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"))
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
        rec[u"行"][0][4] = u"円族"
        self.assertNotEqual([], record_problems(text=json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"))
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
        rec[u"入力"][0][u"sha256"] = u"0" * 64
        self.assertNotEqual([], record_problems(text=json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"))
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
        rec[u"行"].pop()
        self.assertNotEqual([], record_problems(text=json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"))

    def test_d_3_a_record_with_a_sentence_a_value_or_an_element_name_is_red(self):
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"行"][0].append(u"売上高")
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"要素名"] = u"jppfs_cor:NetSales"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        self.assertEqual([], leak_problems(read(RECORD_REL)))
        self.assertFalse(DOCID_RE.search(read(RECORD_REL)))

    def test_d_4_the_row_invariants_hold_and_a_broken_row_is_red(self):
        rows = json.loads(read(RECORD_REL))[u"行"]
        self.assertEqual([], invariant_problems(rows))
        bad = [list(r) for r in rows]
        i = next(n for n, r in enumerate(bad) if r[6])
        bad[i][7] = True                                                     # F が空の本の行で自が真
        self.assertNotEqual([], invariant_problems(bad))
        bad = [list(r) for r in rows]
        i = next(n for n, r in enumerate(bad) if r[7])
        bad[i][11] = False                                                   # 字のとおりの自が円の族の自に含まれない
        self.assertNotEqual([], invariant_problems(bad))

    def test_d_5_the_unit_split_and_the_scale_less_rows_are_real_not_a_defect_of_zero(self):
        u"""「0」が出た欄の自分の欠陥の疑い: 円の族の自が字のとおりの自より多く、scale が無い行が在り、F の単位別に JPY・Pure が在る。"""
        rec = json.loads(read(RECORD_REL))
        lab = list(rec[u"集計"])
        lit, fam = rec[u"集計"][lab[0]][u"全体"][u"P"], rec[u"集計"][lab[1]][u"全体"][u"P"]
        self.assertGreater(fam[u"自"], lit[u"自"])
        self.assertGreater(lit[u"うち scale が無い行"], 0)
        self.assertEqual(lit[u"うち scale が無い行"], fam[u"うち scale が無い行"])
        fu = rec[u"サマリーの fact"][u"F の単位別の数"]
        self.assertGreater(fu.get(u"JPY", 0), 0)
        self.assertGreater(fu.get(u"Pure", 0), 0)


class TypesSheetTest(unittest.TestCase):
    def test_e_1_the_types_entry_checks_one_to_one_letters_and_writes_no_text(self):
        self.assertEqual([], types_entry_problems())

    def test_e_2_the_types_record_when_present_has_the_form(self):
        u"""司令塔が読んだ後に作られる。無い間は「無い」ことを見て通る(足されたら形を縛る)。"""
        self.assertEqual([], types_record_problems())

    def test_e_3_the_sheet_refuses_a_path_inside_the_repo_and_the_sample_groups_are_the_sealed_size(self):
        self.assertEqual([], sheet_problems())


class WiringTest(unittest.TestCase):
    def test_f_1_the_script_imports_only_the_allowed_modules(self):
        self.assertEqual([], import_problems())

    def test_f_2_the_boundary_import_list_is_not_widened(self):
        self.assertEqual([], boundary_problems())

    def test_f_3_the_script_has_no_network_key_or_llm(self):
        src = read(SCRIPT_REL)
        for bad in (u"socket", u"urllib", u"ANTHROPIC", u"API_KEY", u"subprocess", u"requests"):
            self.assertNotIn(bad, src)


class EngineZeroTest(unittest.TestCase):
    def test_g_1_the_real_history_has_no_engine_or_input_change_since_the_seal(self):
        self.assertEqual([], engine_since_seal_problems())

    def test_g_2_the_working_tree_has_no_uncommitted_engine_or_input_change(self):
        self.assertEqual([], engine_worktree_problems())

    def test_g_3_every_not_touched_path_is_a_real_path(self):
        for r in NOT_TOUCHED_RELS:
            self.assertTrue(os.path.exists(os.path.join(ROOT, r)), r)


class OrderTest(unittest.TestCase):
    def test_h_1_the_real_history_has_the_seal_and_the_addendum_before_the_script_the_gate_and_the_record(self):
        u"""script・門・記録のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_h_2_good_order_is_green_and_bad_orders_are_red(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("docs/seal.md")
        a = r.commit("docs/seal.md")                                          # 追記
        others = ["measure/s.py", "tests/g.py", "fixtures/r.json"]
        for o in others:
            r.put(o)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertEqual([], addendum_problems(r.d, PREFIX, "docs/seal.md", a[:7], others))
        self.assertNotEqual([], addendum_problems(r.d, PREFIX, "docs/seal.md", "0000000", others))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("fixtures/new.json")                                             # 未 commit
        self.assertNotEqual([], addendum_problems(r.d, PREFIX, "docs/seal.md", a[:7], others + ["fixtures/new.json"]))
        # 記録が追記より前(封の後・追記の前)に足された
        r2 = PR.Repo()
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        r2.put("fixtures/r.json")
        r2.commit("fixtures/r.json")
        r2.put("docs/seal.md")
        a2 = r2.commit("docs/seal.md")
        self.assertEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["fixtures/r.json"]))
        self.assertNotEqual([], addendum_problems(r2.d, PREFIX, "docs/seal.md", a2[:7], ["fixtures/r.json"]))

    def test_h_3_the_order_check_lists_the_script_the_gate_and_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))


class MutantTest(unittest.TestCase):
    def test_i_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_of(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        results = run_mutants()
        after = (sha_of(SCRIPT_REL), sha_of(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        self.assertEqual(before, after)
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))

    def test_i_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ("seal", "input_sha", "stop", "match", "split", "other", "sample", "rate", "tally", "types", "import", "analyze", "wkeys", "strip", "selfclosed"):
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
