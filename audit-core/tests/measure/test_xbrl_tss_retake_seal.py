# -*- coding: utf-8 -*-
"""封 docs/XBRL_TSS_RETAKE_SEAL_2026-11-18.md(RT ― TSS の系列(第 1 便・第 2 便・便 1b・便 PS)を、直した engine で取り直して前の記録と並べる)の門。封 §2-5。

**この門が縛るもの**

1. 封の字: 封の commit(b4c08fc6)・path・要点の字が script の定数と同じ。封の file は commit した blob と 1 字も変わっていない。
2. 入力 17 件(前の 4 便の script と記録・便 NRE の記録)の sha256 が script の表・門の表・実物で同じ。入力の確かめは 1 byte 違う複製で止まる。前の便の結果の文書・封も封の commit から 0 行。
3. engine は封の commit から 0 行(``core/``・``adapters/``)。作業木にも engine の未 commit の変更が無い。
4. 順序: 封の commit ⊏ script・この門・記録を足した commit(未 commit は赤)。
5. **つなぐ配線**: ``orchestrate`` を作り物の前の記録・作り物の段(段 1・2・3・4・5)で本物のまま走らせ、前の段の「取り直した出力」が次の段へ渡ること
   (段 2 の ``tss_states`` = 段 1 の本そのもの・段 3 の ``interim`` = 段 2 が書いた file・``tss_states`` = 段 1 の本・段 4 の ``bases`` = 段 1 の A の本と段 2 の丙の本・段 5 の本 = 段 1 の本)を縛る。
   RT-1 が外れたら段 2 以降を呼ばない・engine の指紋が違えば止まる。段 1・段 5 は ``states_job`` を作り物にして、W の鍵が取り直した claim に無いときの数え方を縛る。
6. **前後を突き合わせる関数**(``state_compare``・``rt1_numbers``・``near_compare``・``inject_compare``・``ps_compare``・``rt6_block``・``prediction_numbers``)を手計算の作り物で。非対称な例(前と後・消えた行と増えた行・群と型を取り違えると数が変わる)。
7. 記録 ``fixtures/xbrl/tss_retake/retake_2026-11-18.json``: 封の字・script の sha256・入力・指紋(今 = 今の engine = 便 NRE の記録の直した後・直す前 = TSS の記録のもの)・
   段ごとの数が前の記録(file)と変わった行の一覧から数え直せる・予測の判定に要る数が段の数から作り直せる・RT-4c・RT-6 が変わった行の一覧と前の記録から再計算できる・文や値や要素名を持たない。
8. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
全数の作り直しは門の中では走らせない(重い)。この file は docID の字を持たない。
"""
import ast
import collections
import contextlib
import hashlib
import importlib.util
import json
import os
import re
import shutil
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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_rt_seal")       # 順序・履歴の部品。門としては走らせない
MS = load_module("measure/xbrl_tss_retake_2026-11-18.py", "tss_retake_script_for_seal_gate")

SEAL_REL = "docs/XBRL_TSS_RETAKE_SEAL_2026-11-18.md"
SEAL_COMMIT_SHORT = "b4c08fc6"               # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_tss_retake_2026-11-18.py"
GATE_REL = "tests/measure/test_xbrl_tss_retake_seal.py"
RECORD_REL = "fixtures/xbrl/tss_retake/retake_2026-11-18.json"
ORDER_FILES = (SCRIPT_REL, GATE_REL, RECORD_REL)
#: 入力の表(literal。script の表と実物の両方と照らす)
INPUT_SHAS = (
    ("fixtures/xbrl/tanshin_self/population_2026-11-14.json", "48ba8e5574be70d85b3d1affacc9403cffbfc698f529c095c6c882cd8ccfa9b0"),
    ("fixtures/xbrl/tanshin_self/states_2026-11-14.json", "00414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"),
    ("fixtures/xbrl/tanshin_self/states_interim_2026-11-14.json", "ef443ec1b1331fa05ca314122fe36ad28746816e890f73f27efde55738bb5e7e"),
    ("fixtures/xbrl/tanshin_self/near_2026-11-14.json", "5c2b6ee418495ac184ab51eb424e2e0ef11a04b881bbf719cb31e2c3018e0952"),
    ("fixtures/xbrl/tanshin_self/inject_2026-11-14.json", "ea9a2e22932f0c5f4c8158291b0fa224c47709b07bb1fd4f61b3a64e8148b742"),
    ("fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json", "d1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183"),
    ("fixtures/xbrl/tanshin_self/near_types_2026-11-14.json", "f59cfc68a6ddf98b9a713efdda52f8bf04d183bc9b415964bb724812810f779f"),
    ("fixtures/xbrl/tanshin_self/inject_passed_types_2026-11-14.json", "6387b09d9e51f20da9e7fd8d2cf36ba5d006b7f72d93da3d56f2fe1bdb8aa01b"),
    ("fixtures/xbrl/plan_source/states_2026-11-17.json", "d007b1454c0b4c6f30b3627d54221376767d0f0a1233578dbd37bcfe2df51424"),
    ("fixtures/xbrl/plan_source/read_types_2026-11-17.json", "c244d1bf51e7867e1772f98bd6d4c0085fa816faf1ec09f7855050aa99fe5e56"),
    ("fixtures/xbrl/nil_read_engine/states_2026-11-17.json", "13674c80a367e2c54889cccce0c59418891c8ad66dc10bf52f5744e4697900a0"),
    ("measure/xbrl_tanshin_self_stage_2026-11-14.py", "4ed60b591366dd65a431dba5348aff6edb3889676d8e9a4154a5b0298486f7f9"),
    ("measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    ("measure/xbrl_tanshin_self2_2026-11-14.py", "7a3db37e77e8013f56668d7202dbddae023778d57fecaf7b8bc5c621a68583b8"),
    ("measure/xbrl_tanshin_self_inject_2026-11-14.py", "ad33fef1537cfb7a0d866dfe38576abe0528b441f50512e03ad72232a7cc2c9a"),
    ("measure/xbrl_plan_source_2026-11-17.py", "0617d75a98e9aca390426b2751bed5ae40a8aa8759b3e80bffab163e1abeb8ea"),
    ("measure/xbrl_tanshin_2026-11-09.py", "b7ea491bf5cd34c4976bde86c4329583e0d9af09ec8895ea0caf48491492b5bd"))
INPUT_RELS = tuple(rel for rel, _sha in INPUT_SHAS)
#: 入力の表の外で、前の 4 便の記録・script として 1 byte も変えない file(門だけが縛る)
EXTRA_PINNED = (
    ("fixtures/xbrl/tanshin_self/vm_types_subreading_2026-11-14.json", "d5d336bf3eeda37b36db41c02f8a84142257c22921daeb56b5818b262b3235bb"),
    ("fixtures/xbrl/nil_read/states_2026-11-17.json", "16c07159f88973932f70e9c422734330dcdf7893b6ca26ed2898623b614c3864"),
    ("measure/xbrl_nil_read_2026-11-17.py", "f1489d091a55d420052b8f208d344d237b7f168ac0d66b6f2170b7d5f35e7ac4"),
    ("measure/xbrl_nil_read_engine_2026-11-17.py", "e20123a485153384f37162e04a5382d65656b568ec41b6359213113052505775"))
#: 前の便の封・結果の文書(封の commit から 0 行)
PRIOR_DOCS = (
    "docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md", "docs/XBRL_TANSHIN_SELF_RESULT_2026-11-14.md", "docs/XBRL_TANSHIN_SELF2_SEAL_2026-11-14.md", "docs/XBRL_TANSHIN_SELF2_RESULT_2026-11-14.md",
    "docs/XBRL_TANSHIN_SELF_INJECT_SEAL_2026-11-14.md", "docs/XBRL_TANSHIN_SELF_INJECT_RESULT_2026-11-14.md", "docs/XBRL_PLAN_SOURCE_SEAL_2026-11-17.md",
    "docs/XBRL_PLAN_SOURCE_READ_AXES_SEAL_2026-11-17.md", "docs/XBRL_PLAN_SOURCE_RESULT_2026-11-17.md", "docs/XBRL_NIL_READ_SEAL_2026-11-17.md", "docs/XBRL_NIL_READ_RESULT_2026-11-17.md",
    "docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md", "docs/XBRL_NIL_READ_ENGINE_RESULT_2026-11-17.md")
STDLIB_OK = ("__future__", "argparse", "collections", "fractions", "importlib", "json", "os", "sys", "time")
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
RATE_TEXT = re.compile(r"^(\d+\.\d%|分母 0)$")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
G, VM, UN, PN = STATES
CUT_OK, CUT_NG = u"切れた", u"切れない"
W_PASS, W_ORIG, W_OTHER = u"通した", u"名指して原本の値を返した", u"名指したが別の値"
T1, T5, T8, T9 = u"T1_VALUE", u"T5_COINCIDENT", u"T8_REL", u"T9_PRIOR_TO_CURRENT"
K_RT1 = u"RT-1(段 1 の行 対 便 NRE の記録の「直した engine の state」)"
K_PRED = u"予測の判定に要る数(RT-1〜RT-6。当たり・外れは結果の文書で)"
K_STAGES = (u"段 1(第 1 便。400 本の判定)", u"段 2(第 2 便(一)。中間 150 本の期の名前を写した判定)", u"段 3(第 2 便(二)。近い行)", u"段 4(便 1b。注入)", u"段 5(便 PS。サマリーの当てる先)")
WIRE_SENTINEL = u"配線の作り物"


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.isfile(os.path.join(ROOT, rel)) else None


def load_json(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh, object_pairs_hook=collections.OrderedDict)


def guard(fn, *a, **k):
    u"""検査を呼ぶ。例外は「問題」として返す(変異した関数が落ちても赤として数える)。"""
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  Stop(SystemExit)を含む
        return [u"例外: %s" % type(exc).__name__]


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("tss_retake_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


@contextlib.contextmanager
def patched(obj, **over):
    saved = dict((k, getattr(obj, k)) for k in over)
    for k, v in over.items():
        setattr(obj, k, v)
    try:
        yield
    finally:
        for k, v in saved.items():
            setattr(obj, k, v)


def stops(ms, fn, *a, **k):
    u"""``fn`` が ``Stop`` で止まるか。止まらなければ False・Stop でない例外なら例外の名前の字。"""
    try:
        fn(*a, **k)
    except ms.Stop:
        return True
    except BaseException as exc:                   # noqa: BLE001
        return type(exc).__name__
    return False


# ---------------------------------------------------------------- 1. 封の字
def seal_text():
    return read(SEAL_REL)


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    for phrase in (u"RT-1", u"RT-2a", u"RT-2b", u"RT-3a", u"RT-3b", u"RT-4a", u"RT-4b", u"RT-4c", u"RT-5a", u"RT-5b", u"RT-6", u"RT-7", u"消えた行", u"増えた行", u"読み替えた所",
                   u"fixtures/xbrl/tss_retake/retake_2026-11-18.json", u"measure/xbrl_tss_retake_2026-11-18.py", u"外れたら段 2 へ進まず止めて報告する", u"profile: P33E"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    if ms.PROFILE != u"P33E" or tuple(ms.STATES) != STATES:
        out.append(u"profile か state の名が違う")
    if tuple(ms.K_STAGES) != K_STAGES or ms.K_RT1 != K_RT1 or ms.K_PRED != K_PRED:
        out.append(u"記録の欄の名が門と違う")
    return out


def seal_history_problems(root=REPO):
    u"""封の file の履歴は 1 commit(b4c08fc6)で、今の file はその commit の blob と 1 字も変わらない。"""
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


# ---------------------------------------------------------------- 2. 入力・前の記録・前の文書
def input_sha_problems(ms=None):
    ms = ms or MS
    out = []
    if [(rel, sha) for _no, rel, sha in ms.INPUTS] != list(INPUT_SHAS):
        out.append(u"script の入力の表が門の表と違う")
    out.extend(u"入力の sha256 が表と違う: %s" % rel for rel, want in INPUT_SHAS + EXTRA_PINNED if sha_of(rel) != want)
    return out


def input_wire_problems(ms=None):
    u"""``check_inputs`` が、表のとおりの複製では通り、1 byte 違う複製では止まる。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="rt_inputs_")
    try:
        for rel in INPUT_RELS:
            os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(ROOT, rel), os.path.join(tmp, rel))
        if [r[u"sha256"] for r in ms.check_inputs(tmp)] != [s for _r, s in INPUT_SHAS]:
            out.append(u"表のとおりの複製で check_inputs が表の sha256 を返さない")
        for i in range(len(INPUT_RELS)):
            p = os.path.join(tmp, INPUT_RELS[i])
            with open(p, "ab") as fh:
                fh.write(b" ")
            if stops(ms, ms.check_inputs, tmp) is not True:
                out.append(u"入力 %d が 1 byte 違うのに止まらない" % (i + 1))
            shutil.copyfile(os.path.join(ROOT, INPUT_RELS[i]), p)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def prior_docs_problems(root=REPO):
    u"""前の便の封・結果の文書は封の commit から 0 行(``git diff --name-only 封の commit HEAD``)。"""
    s = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(s) != 1:
        return [u"封の commit が履歴に 1 つで決まらない"]
    rc, txt = PR.git_in(root, "diff", "--name-only", s[0], "HEAD", "--", *[PREFIX + d for d in PRIOR_DOCS])
    if rc != 0:
        return [u"git diff が失敗した"]
    return [u"前の便の文書が封の後に変わっている: %s" % ln for ln in txt.splitlines() if ln.strip()]


# ---------------------------------------------------------------- 3. engine は 0 行
def engine_zero_problems(root=REPO, seal_rel=SEAL_REL, prefix=PREFIX):
    u"""封の commit から HEAD までの ``core/``・``adapters/`` の差分が 0 行。作業木にも engine の未 commit の変更が無い。"""
    s = PR.added_commits(root, prefix + seal_rel)
    if len(s) != 1:
        return [u"封の commit が履歴に 1 つで決まらない"]
    rc, txt = PR.git_in(root, "diff", "--numstat", s[0], "HEAD", "--", prefix + "adapters", prefix + "core")
    if rc != 0:
        return [u"git diff が失敗した"]
    out = [u"engine の差分が在る: %s" % ln.split("\t")[-1] for ln in txt.splitlines() if ln.strip()]
    rc, st = PR.git_in(root, "status", "--porcelain", "--untracked-files=all", "--", prefix + "adapters", prefix + "core")
    if rc != 0:
        return out + [u"git status が失敗した"]
    return out + [u"engine に未 commit の変更: %s" % ln.strip()[:2] for ln in st.splitlines() if ln.strip()]


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(ORDER_FILES) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 4. 前後を突き合わせる関数(手計算の作り物)
def row(si, pos, state, reason=None):
    return [si, pos, state, reason, u"CurrentYear", False, u"円族", False, False]


def book(n, grp, rows, cut=True):
    b = collections.OrderedDict([(u"#", n), (u"群", grp), (u"様式の種類", u"k"), (u"ZIP の sha256", u"s%d" % n)])
    if cut:
        b.update([(u"切り出し", CUT_OK), (u"理由", None), (u"見出しの番号", 0), (u"字数", 10), (u"入れた iXBRL の file の数", 1), (u"fact の数", 5), (u"claim", len(rows)), (u"対応", True), (u"行", rows)])
    else:
        b.update([(u"切り出し", CUT_NG), (u"理由", u"member なし"), (u"見出しの番号", None), (u"字数", None), (u"入れた iXBRL の file の数", None), (u"fact の数", None),
                  (u"claim", 0), (u"対応", None), (u"行", [])])
    return b


def compare_problems(ms=None):
    ms = ms or MS
    out = []
    # ---- 率・ポイントの差・突き合わせの基本
    r = ms.rate(1, 3)
    if (r[u"分子"], r[u"分母"], r[u"率"]) != (1, 3, u"33.3%") or ms.rate(2, 3)[u"率"] != u"66.7%" or ms.rate(0, 0)[u"率"] != u"分母 0":
        out.append(u"rate が 分子・分母・率(小数 1 桁。分母 0 は「分母 0」)でない")
    if ms.point_diff(1, 4, 1, 2) != u"25.00" or ms.point_diff(1, 2, 1, 4) != u"-25.00" or ms.point_diff(1, 3, 1, 3) != u"0.00" or ms.point_diff(0, 0, 1, 2) != u"分母 0":
        out.append(u"point_diff が (後 − 前) のポイント(小数 2 桁)でない: %s %s" % (ms.point_diff(1, 4, 1, 2), ms.point_diff(1, 2, 1, 4)))
    if ms.point_diff(1, 3, 1, 2) != u"16.67" or ms.point_diff(1, 2, 1, 3) != u"-16.67" or ms.point_diff(1000, 1000, 999, 1000) != u"-0.10":
        out.append(u"point_diff の丸めが違う")
    both, oo, nn = ms.pair_up({1: u"a", 2: u"b"}, {2: u"c", 3: u"d"})
    if (both, oo, nn) != ([2], [1], [3]):
        out.append(u"pair_up が (両方・前にだけ・後にだけ) でない: %s" % ((both, oo, nn),))
    # ---- state_compare(段 1・2): 本 1 = VM→G・G のまま・UN のまま・G が消えた・VM が増えた
    old = [book(1, u"甲", [row(1, 1, VM, u"a"), row(1, 2, G), row(1, 3, UN, u"u"), row(1, 4, G), row(1, 6, G)]), book(2, u"乙", [row(1, 1, G)]), book(3, u"丙", [], cut=False)]
    new = [book(1, u"甲", [row(1, 1, G, u"b"), row(1, 2, UN, u"x"), row(1, 3, UN, u"u2"), row(1, 5, VM, u"v"), row(1, 6, UN, u"z")]), book(2, u"乙", [row(1, 1, G)]), book(3, u"丙", [], cut=False)]
    s = ms.state_compare(old, new)
    if (s[u"行(前)"], s[u"行(後)"], s[u"両方に在る行"], s[u"前にだけ在る行(消えた行)"], s[u"後にだけ在る行(増えた行)"]) != (6, 6, 5, 1, 1):
        out.append(u"state_compare の行の数が違う(前 6・後 6・両方 5・消えた 1・増えた 1): %s" % ((s[u"行(前)"], s[u"行(後)"], s[u"両方に在る行"], s[u"前にだけ在る行(消えた行)"], s[u"後にだけ在る行(増えた行)"]),))
    if (s[u"state が変わった行"][u"分子"], s[u"state が変わった行"][u"分母"]) != (3, 5) or s[u"state が変わった行を持つ本"] != 1:
        out.append(u"state_compare の state が変わった行が 3 / 5・本 1 でない")
    if s[u"変わった行"] != [[1, 1, 1, VM, G], [1, 1, 2, G, UN], [1, 1, 6, G, UN]]:
        out.append(u"state_compare の変わった行が [本, 文, 位置, 前, 後] の並びでない: %s" % (s[u"変わった行"],))
    if s[u"消えた行"] != [[1, 1, 4, G]] or s[u"増えた行"] != [[1, 1, 5, VM]]:
        out.append(u"state_compare の消えた行・増えた行が違う")
    if (s[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"], s[u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)"], s[u"前は GROUNDED で消えた行"]) != (2, 1, 1):
        out.append(u"state_compare の GROUNDED の向きの数が(前 G → 後 非 G 2・前 非 G → 後 G 1・G で消えた 1)でない")
    t = s[u"両方に在る行の state の移り変わり(前 → 後)"]
    if t[u"%s → %s" % (VM, G)] != 1 or t[u"%s → %s" % (G, VM)] != 0 or t[u"%s → %s" % (G, UN)] != 2 or sum(t.values()) != 5:
        out.append(u"state_compare の移り変わりの向き(前 → 後)が違う")
    if s[u"state は同じで reason だけ変わった行"] != 1:
        out.append(u"state_compare の reason だけ変わった行が 1 でない")
    if ms.state_compare(old, new, set([2]))[u"行(前)"] != 1:
        out.append(u"state_compare が nums で本を絞らない")
    if ms.cut_differences(old, new) != 0 or ms.cut_differences(old, [new[0], new[1], book(3, u"丙", [row(1, 1, G)])]) != 1 or ms.cut_differences(old, new[:2]) != 1:
        out.append(u"cut_differences が(切り出しの結果が違う本・片方にだけ在る本)を数えない")
    # ---- rt1_numbers: 便 NRE の記録の 4 番目 = 直した engine の state
    nre = [[1, 1, 1, G, True, VM], [1, 1, 2, UN, True, G], [1, 1, 3, G, True, UN], [1, 1, 9, G, True, G], [2, 1, 1, G, True, G]]
    r1 = ms.rt1_numbers(new[:2], nre)
    if (r1[u"行(便 NRE の記録)"], r1[u"行(取り直し)"], r1[u"両方に在る行"], r1[u"state が違う行"][u"分子"], r1[u"state が違う行"][u"分母"], r1[u"便 NRE の記録にだけ在る行"], r1[u"取り直しにだけ在る行"]) != (5, 6, 4, 1, 4, 1, 2):
        out.append(u"rt1_numbers が(NRE の行 5・取り直し 6・両方 4・違う 1・NRE にだけ 1・取り直しにだけ 2)でない: %s" % (r1,))
    if ms.rt1_numbers(new[:2], nre, set([2]))[u"行(便 NRE の記録)"] != 1:
        out.append(u"rt1_numbers が nums で絞らない")
    # ---- near_compare
    old_near = collections.OrderedDict([(u"行", [[1, 1, 1, [u"N-円"], u"円"], [1, 1, 2, [u"N-桁"], u"円"], [2, 1, 1, [u"N-率"], u"%"]])])
    new_near = collections.OrderedDict([(u"行", [[1, 1, 1, [u"N-円", u"N-桁"], u"円"], [2, 1, 1, [u"N-率"], u"%"], [2, 3, 3, [u"N-率"], u"%"], [3, 1, 1, [u"N-円"], u"円"]])])
    n = ms.near_compare(old_near, new_near)
    if (n[u"近い行(前)"], n[u"近い行(後)"], n[u"前の近い行のうち後も近い行"], n[u"前にだけ在る行(消えた行)"], n[u"後にだけ在る行(増えた行)"],
            n[u"両方に在る行のうち当たった規則が変わった行"]) != (3, 4, 2, 1, 2, 1):
        out.append(u"near_compare が(前 3・後 4・両方 2・消えた 1・増えた 2・規則が変わった 1)でない: %s" % ({k: v for k, v in n.items() if not isinstance(v, list)},))
    if n[u"消えた行"] != [[1, 1, 2, [u"N-桁"], u"円"]] or [r[:3] for r in n[u"増えた行"]] != [[2, 3, 3], [3, 1, 1]] or n[u"規則が変わった行"] != [[1, 1, 1, [u"N-円"], [u"N-円", u"N-桁"]]]:
        out.append(u"near_compare の行の一覧が違う")
    # ---- inject_compare
    def ir(n_, rid, typ, grp, word, claim=u"N001"):
        return collections.OrderedDict([(u"本の #", n_), (u"群", grp), (u"id", rid), (u"型", typ), (u"形", u"既存"), (u"単位", u"円"), (u"基準の claim", claim), (u"P33E", {u"結果": word})])
    old_i = [ir(1, u"B1-a", T1, u"甲", W_ORIG), ir(1, u"B1-b", T1, u"甲", W_PASS), ir(2, u"B2-a", T5, u"乙", W_ORIG), ir(3, u"B3-a", T9, u"丙", W_PASS), ir(3, u"B3-b", T8, u"丙", W_ORIG), ir(1, u"B1-t", T9, u"甲", W_PASS)]
    new_i = [ir(1, u"B1-a", T1, u"甲", W_OTHER), ir(1, u"B1-b", T1, u"甲", W_PASS, u"N002"), ir(3, u"B3-a", T9, u"丙", W_PASS), ir(3, u"B3-b", T8, u"丙", W_ORIG), ir(3, u"B3-c", T9, u"丙", W_PASS), ir(3, u"B3-d", T8, u"丙", W_ORIG), ir(1, u"B1-t", T9, u"甲", W_PASS)]
    c = ms.inject_compare(old_i, new_i)
    if (c[u"注入の行(前)"], c[u"注入の行(後)"], c[u"両方に在る行"], c[u"前にだけ在る行(消えた行)"], c[u"後にだけ在る行(増えた行)"]) != (6, 7, 5, 1, 2):
        out.append(u"inject_compare の行の数が違う(前 6・後 7・両方 5・消えた 1・増えた 2)")
    if c[u"結果の語が変わった行"][u"分子"] != 1 or c[u"両方に在る行のうち型・形・単位・基準の claim のどれかが違う行"] != 1:
        out.append(u"inject_compare の結果の語が変わった行 1・別の基準の claim の行 1 でない")
    if c[u"変わった行"] != [[1, u"B1-a", T1, W_ORIG, W_OTHER]] or c[u"消えた行"] != [[2, u"B2-a", T5, W_ORIG]] or c[u"増えた行"] != [[3, u"B3-c", T9, W_PASS], [3, u"B3-d", T8, W_ORIG]]:
        out.append(u"inject_compare の行の一覧が(前 → 後の向き)でない")
    if (c[u"通した行(前)"][u"通した行の合計"], c[u"通した行(後)"][u"通した行の合計"], c[u"通した行(前)"][u"うち丙の期の入れ替えの型"], c[u"通した行(後)"][u"うち丙の期の入れ替えの型"]) != (3, 4, 1, 2):
        out.append(u"inject_compare の通した行(前 3・後 4・丙の期の入れ替えの型 前 1・後 2)が違う: %s %s" % (c[u"通した行(前)"], c[u"通した行(後)"]))
    cell = dict(((x[u"群"], x[u"型"]), x) for x in c[u"升ごとの「名指して原本の値を返した」"])
    a1, p8, p5 = cell[(u"A", T1)], cell[(u"丙", T8)], cell[(u"A", T5)]
    if (a1[u"前の分子"], a1[u"前の分母"], a1[u"後の分子"], a1[u"後の分母"], a1[u"差(ポイント。小数 2 桁。後 − 前)"]) != (1, 2, 0, 2, u"-50.00"):
        out.append(u"inject_compare の 群 A × T1 の升(前 1/2・後 0/2・差 -50.00)が違う: %s" % (dict(a1),))
    if (p8[u"前の分子"], p8[u"前の分母"], p8[u"後の分子"], p8[u"後の分母"], p8[u"差(ポイント。小数 2 桁。後 − 前)"]) != (1, 1, 2, 2, u"0.00"):
        out.append(u"inject_compare の 群 丙 × T8 の升が(1/1・2/2・0.00)でない: %s" % (dict(p8),))
    if (p5[u"前の分母"], p5[u"後の分母"]) != (1, 0) or p5[u"差(ポイント。小数 2 桁。後 − 前)"] != u"分母 0":
        out.append(u"inject_compare の 群 A × T5 の升(前 1・後 0・分母 0)が違う")
    if ms.inject_compare(old_i, new_i, set([3]))[u"注入の行(前)"] != 2:
        out.append(u"inject_compare が nums で絞らない")
    # ---- ps_compare
    R = ms.PS
    def pr(n_, si, pos, which, fam=u"円", **flags):
        r_ = [n_, si, pos, which, fam] + [False] * (R.N_COLUMNS - 5)
        for k, v in flags.items():
            r_[getattr(R, k)] = v
        return r_
    old_p = [pr(1, 1, 1, u"P", R_SELF_N=True), pr(1, 1, 2, u"P", R_OTHER=True), pr(1, 1, 3, u"P"), pr(2, 1, 1, u"W", R_SELF=True), pr(2, 2, 2, u"P", R_REAL_N=True)]
    new_p = [pr(1, 1, 1, u"P", R_SELF=True, R_SELF_N=True), pr(1, 1, 2, u"P", R_OTHER=True, R_OTHER_N=True), pr(2, 1, 1, u"W", fam=u"%", R_SELF=True), pr(3, 1, 1, u"P", R_SELF=True), pr(3, 1, 2, u"P", R_SELF=True)]
    p = ms.ps_compare(old_p, new_p)
    if (p[u"P の行(前)"], p[u"P の行(後)"], p[u"W の行(前)"], p[u"W の行(後)"], p[u"両方に在る行"], p[u"両方に在る P の行"], p[u"前にだけ在る行(消えた行)"], p[u"後にだけ在る行(増えた行)"]) != (4, 4, 1, 1, 3 + 1 - 1 + 0, 2, 2, 2):
        out.append(u"ps_compare の行の数が違う(P 前 4・後 4・W 1・1・両方 3・両方の P 2・消えた 2・増えた 2): %s" % ({k: v for k, v in p.items() if not isinstance(v, (list, dict))},))
    # 両方に在る P の行 = (1,1,1) と (1,1,2)。RT-5b: 後の字のとおり(R_SELF・R_REAL・R_OTHER)対 前の空の欄を除く(R_SELF_N・R_REAL_N・R_OTHER_N)
    #   (1,1,1): 後 自 真・前 自_N 真 → 同じ。(1,1,2): 後 他 真・前 他_N 偽 → 違う。→ 1 行(後の字のとおり 対 後の空の欄を除く にすると (1,1,1)・(1,1,2) とも同じ → 0 行になる)
    if p[u"両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの自・実・他と違う行"] != 1:
        out.append(u"ps_compare の RT-5b(後の字のとおり 対 前の空の欄を除く)が 1 行でない")
    # 参考: 後の P の行のうち 字のとおり 対 空の欄を除く(後の側)が違う行 = (1,1,1) 後: 自 真・自_N 真 → 同じ / (1,1,2) 他 真・他_N 真 → 同じ / (3,1,1) 自 真・自_N 偽 → 違う / (3,1,2) 同じく違う → 2
    if p[u"参考: 後の P の行のうち字のとおりの読みの自・実・他が空の欄を除く読みの自・実・他と違う行"] != 2:
        out.append(u"ps_compare の参考の数(後の字のとおり 対 後の空の欄を除く)が 2 でない")
    if p[u"どれかの欄が変わった行"] != 3:
        out.append(u"ps_compare のどれかの欄が変わった行が 3(札 2・単位の族 1)でない")
    if p[u"消えた行"] != [[1, 1, 3, u"P"], [2, 2, 2, u"P"]] or p[u"増えた行"] != [[3, 1, 1, u"P"], [3, 1, 2, u"P"]]:
        out.append(u"ps_compare の消えた行・増えた行が違う")
    if ms.ps_compare(old_p, new_p, set([1]))[u"両方に在る P の行"] != 2 or ms.ps_compare(old_p, new_p, set([3]))[u"両方に在る行"] != 0:
        out.append(u"ps_compare が nums で絞らない")
    # ---- rt6_block
    vm_rows = [[1, 1, 1, 1, u"ア"], [2, 1, 1, 2, u"ア"], [3, 1, 1, 3, u"ア"], [4, 2, 1, 1, u"ア"]]
    new_states = {(1, 1, 1): row(1, 1, G), (1, 1, 2): row(1, 2, VM), (1, 1, 3): row(1, 3, UN)}          # (4: 本 2 の行は取り直しに無い)
    near_read = [[1, 1, 1, 1, u"い"], [2, 1, 1, 2, u"い"], [3, 2, 1, 1, u"い"]]
    near_new = [[1, 1, 1, [u"N-円"], u"円"], [2, 1, 1, [u"N-率"], u"%"]]
    passed_rows = [[1, 1, u"B1-a", T1, u"a"], [2, 1, u"B1-b", T1, u"a"], [3, 3, u"B3-a", T9, u"a"], [4, 3, u"B3-z", T9, u"a"]]
    passed_new = ms.inject_rows(new_i)
    read_rows = [[1, 1, 1, 1, u"甲組"], [2, 2, 1, 1, u"W組"], [3, 1, 1, 2, u"乙組"], [4, 3, 1, 1, u"甲組"]]
    ps_keys = set([(1, 1, 1, u"P"), (2, 1, 1, u"P"), (1, 1, 2, u"W")])
    b6 = ms.rt6_block(vm_rows, near_read, near_new, passed_rows, passed_new, read_rows, ps_keys, new_states)
    got = [(v[u"分子"], v[u"分母"]) for v in b6.values()]
    # 第 1 便の標本: (1,1,1)=G → 違う・(1,1,2)=VM → 同じ・(1,1,3)=UN → 違う・(2,1,1) 無し → 違う → 3 / 4
    # 近い行の読み: (1,1,1) 在る・(1,1,2) 無し → 違う・(2,1,1) 在る → 1 / 3 (行の 2 番目の本 # は列 1)
    # 通した行の札: B1-a は取り直しで 名指したが別の値 → 違う・B1-b は通したまま(基準の claim が違っても語は同じ)・B3-a は通したまま・B3-z は無い → 違う → 2 / 4
    # 便 PS の読み: 甲組 (1,1,1,P) 在る・W組 (2,1,1,W) 無し → 違う(P は在るが W でない)・乙組 (1,1,2,P) 無し(W は在る) → 違う・甲組 (3,1,1,P) 無し → 違う → 3 / 4
    if got != [(3, 4), (1, 3), (2, 4), (3, 4)]:
        out.append(u"rt6_block の 4 つの分子・分母が(3/4・1/3・2/4・3/4)でない: %s" % (got,))
    if [v[u"分母"] for v in ms.rt6_block(vm_rows, near_read, near_new, passed_rows, passed_new, read_rows, ps_keys, new_states, set([1])).values()] != [3, 2, 2, 2]:
        out.append(u"rt6_block が nums で絞らない")
    # ---- prediction_numbers が各段の欄を正しい予測へ渡す
    stage = ms.prediction_numbers(s, s, n, c, p, r1, b6)
    if stage[u"RT-3a 段 3 の近い行の数(後)"] != 4 or stage[u"RT-3b 前の近い行のうち後も近い行 / 前の近い行"] != collections.OrderedDict([(u"分子", 2), (u"分母", 3)]):
        out.append(u"prediction_numbers の RT-3a・RT-3b が段 3 の数(後 4・両方 2・前 3)でない")
    if stage[u"RT-4a 段 4 の注入の行の数(後)"] != 7 or list(stage[u"RT-4b 通した行の合計(前・後)と、うち丙の期の入れ替えの型(前・後)"].values()) != [3, 4, 1, 2]:
        out.append(u"prediction_numbers の RT-4a・RT-4b が段 4 の数でない")
    if stage[u"RT-4c 群 × 型の 6 つの升の「名指して原本の値を返した」の率の差(ポイント。後 − 前)"][u"A × T1_VALUE"] != u"-50.00":
        out.append(u"prediction_numbers の RT-4c が升の差でない")
    if stage[u"RT-5a 段 5 の P の行の数(後)"] != 4:
        out.append(u"prediction_numbers の RT-5a が段 5 の P の行(後)でない")
    two = [v for k, v in stage.items() if k.startswith(u"RT-5b 両方に在る")][0]
    if two != collections.OrderedDict([(u"分子", 1), (u"分母", 2)]):
        out.append(u"prediction_numbers の RT-5b が(違う行 1・両方の P 2)でない")
    if [v for k, v in stage.items() if k.startswith(u"RT-2a 段 2 で")][0] != s[u"state が変わった行"]:
        out.append(u"prediction_numbers の RT-2a が段 2 の state が変わった行でない")
    if stage[u"RT-6 AI の席が読んだ行のうち前提が変わった行"] is not b6:
        out.append(u"prediction_numbers の RT-6 が rt6 の数でない")
    return out


# ---------------------------------------------------------------- 5. つなぐ配線(作り物の段で orchestrate を本物のまま走らせる)
def psrow(n, si, pos, which, fam=u"円", **flags):
    u"""便 PS の行(22 欄)の作り物。``flags`` の名前は ``PS.R_*``(例 ``R_SELF=True``)。"""
    r_ = [n, si, pos, which, fam] + [False] * (MS.PS.N_COLUMNS - 5)
    for k, v in flags.items():
        r_[getattr(MS.PS, k)] = v
    return r_


#: 作り物の段 5 の前(便 PS の記録の行)・後(取り直した行)。手計算(非対称):
#:   前 P: (1,1,1)[自 真・自_N 偽]・(1,1,2)[全部 偽]・(2,1,1)[消える]・(4,1,1)[母集団の外]  前 W: (1,1,2)・(2,1,2)[消える]
#:   後 P: (1,1,1)[自 真・自_N 真]・(1,1,2)[全部 偽]・(3,1,1)[自 真・自_N 偽]・(3,1,2)[他 真・他_N 偽]  後 W: (1,1,2)・(3,1,3)
def fake_ps_old_rows():
    return [psrow(1, 1, 1, u"P", R_SELF=True), psrow(1, 1, 2, u"P"), psrow(2, 1, 1, u"P"), psrow(4, 1, 1, u"P"), psrow(1, 1, 2, u"W"), psrow(2, 1, 2, u"W")]


def fake_ps_new_rows():
    return [psrow(1, 1, 1, u"P", R_SELF=True, R_SELF_N=True), psrow(1, 1, 2, u"P"), psrow(3, 1, 1, u"P", R_SELF=True), psrow(3, 1, 2, u"P", R_OTHER=True),
            psrow(1, 1, 2, u"W"), psrow(3, 1, 3, u"W")]


def fake_engine_fp():
    fp = MS.VD.engine_fingerprint()
    return collections.OrderedDict((k, fp[k]) for k in MS.FP_KEYS)


def fake_old(fp_nre=None, fp_tss=None):
    u"""作り物の「前の記録」。本 1(甲)・本 2(乙)・本 3(丙)。"""
    fp_nre = fp_nre or fake_engine_fp()
    fp_tss = fp_tss or collections.OrderedDict((k, u"old-" + k) for k in MS.FP_KEYS)
    tss_books = [book(1, u"甲", [row(1, 1, VM, u"a"), row(1, 2, G), row(1, 3, UN, u"u")]), book(2, u"乙", [row(1, 1, G), row(1, 2, PN, u"p")]),
                 book(3, u"丙", [row(1, 1, VM, u"v"), row(1, 2, G)]), book(4, u"丁", [row(1, 1, G)])]          # 本 4 は母集団の外(nums で絞らないと数が変わる)
    new_books = [book(1, u"甲", [row(1, 1, G, u"b"), row(1, 2, G), row(1, 3, UN, u"u")]), book(2, u"乙", [row(1, 1, G), row(1, 3, VM, u"w")]),
                 book(3, u"丙", [row(1, 1, VM, u"v"), row(1, 2, G)])]
    old_state = dict(((b[u"#"], r[0], r[1]), r[2]) for b in tss_books for r in b[u"行"])
    nre_rows = [[b[u"#"], r[0], r[1], r[2], True, old_state.get((b[u"#"], r[0], r[1]), UN)] for b in new_books for r in b[u"行"]] + [[4, 1, 1, G, True, G]]
    interim_old = [book(3, u"丙", [row(1, 1, VM, u"v"), row(1, 2, G)])]
    interim_new = [book(3, u"丙", [row(1, 1, G, u"v2"), row(1, 2, UN, u"y")])]
    old_inject_rows = [
        collections.OrderedDict([(u"本の #", 1), (u"群", u"甲"), (u"id", u"B1-a"), (u"型", T1), (u"形", u"既存"), (u"単位", u"円"), (u"基準の claim", u"N001"), (u"P33E", {u"結果": W_ORIG})]),
        collections.OrderedDict([(u"本の #", 3), (u"群", u"丙"), (u"id", u"B3-a"), (u"型", T9), (u"形", u"既存"), (u"単位", u"円"), (u"基準の claim", u"N001"), (u"P33E", {u"結果": W_PASS})]),
        collections.OrderedDict([(u"本の #", 2), (u"群", u"乙"), (u"id", u"B2-a"), (u"型", T1), (u"形", u"既存"), (u"単位", u"円"), (u"基準の claim", u"N001"), (u"P33E", {u"結果": W_PASS})]),
        collections.OrderedDict([(u"本の #", 4), (u"群", u"丁"), (u"id", u"B4-a"), (u"型", T1), (u"形", u"既存"), (u"単位", u"円"), (u"基準の claim", u"N001"), (u"P33E", {u"結果": W_PASS})])]
    new_inject_rows = [
        collections.OrderedDict([(u"本の #", 1), (u"群", u"甲"), (u"id", u"B1-a"), (u"型", T1), (u"形", u"既存"), (u"単位", u"円"), (u"基準の claim", u"N001"), (u"P33E", {u"結果": W_OTHER})]),
        collections.OrderedDict([(u"本の #", 3), (u"群", u"丙"), (u"id", u"B3-a"), (u"型", T9), (u"形", u"既存"), (u"単位", u"円"), (u"基準の claim", u"N001"), (u"P33E", {u"結果": W_PASS})]),
        collections.OrderedDict([(u"本の #", 2), (u"群", u"乙"), (u"id", u"B2-a"), (u"型", T1), (u"形", u"既存"), (u"単位", u"円"), (u"基準の claim", u"N001"), (u"P33E", {u"結果": W_OTHER})])]
    old = {
        u"tss": collections.OrderedDict([(u"profile", u"P33E"), (u"engine の指紋", fp_tss), (u"本", tss_books), (u"集計", {u"fake": 1})]),
        u"nre": collections.OrderedDict([(u"profile", u"P33E"), (u"engine の指紋(直した後)", fp_nre), (u"行", nre_rows)]),
        u"interim": collections.OrderedDict([(u"本", interim_old), (u"本の数", 1), (u"名前がぶつかる本", 0), (u"写した本", 1), (u"置き換えた回数の合計(規則 1・2・3)", [1, 1, 1]),
                                           (u"集計", {u"fake": 2}), (u"TSS の B(写さない)との動き", {u"fake": 3})]),
        u"near": collections.OrderedDict([(u"行", [[3, 1, 1, [u"N-円"], u"円"], [4, 1, 1, [u"N-円"], u"円"]]), (u"集計", {u"fake": 4}), (u"近い行の数(A と B)", 1), (u"読む行の規則", {u"fake": 5})]),
        u"inject": collections.OrderedDict([(u"行", old_inject_rows), (u"集計", {u"fake": 6}), (u"母集団", {u"fake": 7}), (u"覆い", {u"群ごと": {u"fake": 8}})]),
        u"ps": collections.OrderedDict([(u"行", fake_ps_old_rows()), (u"集計", {u"fake": 9}), (u"サマリーの fact", {u"fake": 10})]),
        u"vm_types": {u"行": [[1, 1, 1, 1, u"ア"], [2, 1, 1, 2, u"ウ"], [3, 2, 1, 1, u"ア"], [4, 3, 1, 1, u"ア"]]},
        u"near_types": {u"行": [[1, 3, 1, 1, u"い"], [2, 1, 1, 3, u"い"], [3, 3, 1, 2, u"い"]]},
        u"passed_types": {u"行": [[1, 3, u"B3-a", T9, u"a"], [2, 2, u"B2-a", T1, u"a"], [3, 1, u"B1-a", T1, u"a"]]},
        u"read_types": {u"行": [[1, 1, 1, 1, u"甲組"], [2, 2, 1, 1, u"W組"], [3, 2, 1, 1, u"乙組"], [4, 3, 1, 1, u"甲組"], [5, 3, 1, 2, u"甲組"]]}}
    return old, new_books, interim_new, new_inject_rows


def fake_pop():
    return [(1, u"甲", u"k", u"s1"), (2, u"乙", u"k", u"s2"), (3, u"丙", u"k", u"s3")]


def run_orchestrate(ms, old=None, new_books=None, interim_new=None, new_inject=None, fp_now_override=None):
    u"""作り物の段を差して ``orchestrate`` を本物のまま走らせる。(記録, 各段が受け取った引数の記録)を返す。"""
    old0, nb0, in0, ni0 = fake_old()
    old = old or old0
    new_books = new_books or nb0
    interim_new = interim_new or in0
    new_inject = new_inject or ni0
    calls = collections.OrderedDict()
    tmp = tempfile.mkdtemp(prefix="rt_orch_")

    def f_stage1(pop, mat, procs, say, shape=None):
        calls[u"stage1"] = (list(pop), shape)
        return new_books

    def f_interim(**kw):
        calls[u"interim"] = kw
        with open(kw[u"out"], "w") as fh:
            fh.write(WIRE_SENTINEL)
        return collections.OrderedDict([(u"本", interim_new), (u"本の数", 1), (u"名前がぶつかる本", 0), (u"写した本", 1), (u"置き換えた回数の合計(規則 1・2・3)", [2, 2, 2]),
                                        (u"集計", {u"fake": 12}), (u"TSS の B(写さない)との動き", {u"fake": 13})])

    def f_near(**kw):
        calls[u"near"] = kw
        with open(kw[u"interim"]) as fh:
            calls[u"near_interim_content"] = fh.read()
        return collections.OrderedDict([(u"行", [[3, 1, 1, [u"N-円"], u"円"], [1, 1, 3, [u"N-率"], u"%"]]), (u"集計", {u"fake": 14}), (u"近い行の数(A と B)", 2), (u"読む行の規則", {u"fake": 15})])

    def f_inject(**kw):
        calls[u"inject"] = kw
        return collections.OrderedDict([(u"行", new_inject), (u"集計", {u"fake": 16}), (u"母集団", {u"fake": 17}), (u"覆い", {u"群ごと": {u"fake": 18}})])

    def f_stage5(pop, mat, procs, say, books1, w_keys):
        calls[u"stage5"] = (books1, w_keys)
        return fake_ps_new_rows(), collections.OrderedDict(), [], 0

    try:
        with patched(ms, stage1=f_stage1, stage5=f_stage5), patched(ms.S2, run_interim=f_interim, run_near=f_near), patched(ms.INJ, run_inject=f_inject), \
                patched(ms.PS, tally=lambda rows, n_c, grp: {u"fake": 19}, fact_stats=lambda books: {u"fake": 20}):
            rec = ms.orchestrate(root=ROOT, procs=1, material=None, scratch=os.path.join(tmp, u"s"), say=lambda *a: None, population=fake_pop(), old=old)
        return rec, calls
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def orchestrate_problems(ms=None):
    ms = ms or MS
    out = []
    old, nb, inn, ni = fake_old()
    rec, calls = run_orchestrate(ms, old, nb, inn, ni)
    # 前の段の取り直した出力が次の段へ渡る(同じ object。前の記録の本ではない)
    by1 = calls[u"interim"][u"tss_states"]
    if sorted(by1) != [1, 2, 3] or any(by1[b[u"#"]] is not b for b in nb) or any(by1[b[u"#"]] is b for b in old[u"tss"][u"本"] if b[u"#"] in by1):
        out.append(u"段 2 の tss_states が段 1 の取り直した本そのものでない")
    if calls[u"near"][u"tss_states"] is not by1 and calls[u"near"][u"tss_states"] != by1:
        out.append(u"段 3 の tss_states が段 1 の取り直した本でない")
    if any(calls[u"near"][u"tss_states"].get(b[u"#"]) is not b for b in nb):
        out.append(u"段 3 の tss_states の本が段 1 の取り直した本そのものでない")
    if calls[u"near"][u"interim"] != calls[u"interim"][u"out"] or calls[u"near_interim_content"] != WIRE_SENTINEL:
        out.append(u"段 3 の interim が段 2 の書いた file でない")
    bases = calls[u"inject"][u"bases"]
    if sorted(bases) != [1, 2, 3] or bases[1] is not nb[0] or bases[2] is not nb[1] or bases[3] is not inn[0]:
        out.append(u"段 4 の bases が(1・2 は段 1 の取り直した本・3 は段 2 の丙の本)でない")
    if bases[3] is nb[2] or bases[3] is old[u"interim"][u"本"][0]:
        out.append(u"段 4 の bases の丙が段 1 の丙の本か前の interim の本になっている")
    if calls[u"stage5"][0] is not nb:
        out.append(u"段 5 の本が段 1 の取り直した本でない")
    if sorted(calls[u"stage5"][1]) != sorted(ms.PS.w_keys_of(old[u"vm_types"])):
        out.append(u"段 5 の W の鍵が第 1 便の標本の型 ウ の行でない")
    # 3 つの scratch の file は別の path で、scratch の中
    ps = [calls[u"interim"][u"out"], calls[u"near"][u"out"], calls[u"inject"][u"out"]]
    if len(set(ps)) != 3 or any(os.path.basename(p) not in ms.SCRATCH_NAMES for p in ps):
        out.append(u"段 2・3・4 の出力の path が scratch の 3 つの名前でない")
    # 記録の数: 段 1 の変わった行 1(本 1 の VM → G)・消えた行 1(本 2 の位置 2)・増えた行 1(本 2 の位置 3)
    s1 = rec[ms.K_STAGES[0]]
    if s1[u"変わった行"] != [[1, 1, 1, VM, G]] or s1[u"消えた行"] != [[2, 1, 2, PN]] or s1[u"増えた行"] != [[2, 1, 3, VM]]:
        out.append(u"段 1 の変わった行・消えた行・増えた行が作り物の本と違う")
    if s1[u"両方に在る行の state の移り変わり(前 → 後)"][u"%s → %s" % (VM, G)] != 1 or s1[u"両方に在る行の state の移り変わり(前 → 後)"][u"%s → %s" % (G, VM)] != 0:
        out.append(u"段 1 の移り変わりの表が(前 → 後)の向きでない")
    s2 = rec[ms.K_STAGES[1]]
    if s2[u"変わった行"] != [[3, 1, 1, VM, G], [3, 1, 2, G, UN]] or s2[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"] != 1:
        out.append(u"段 2 の変わった行が前の interim の本と段 2 の本の差でない")
    if s2[u"置き換えた回数の合計(規則 1・2・3)(前)"] != [1, 1, 1] or s2[u"置き換えた回数の合計(規則 1・2・3)(後)"] != [2, 2, 2]:
        out.append(u"段 2 の前・後の欄が前の記録・段 2 の出力の順でない")
    s3 = rec[ms.K_STAGES[2]]
    if (s3[u"近い行(前)"], s3[u"近い行(後)"], s3[u"前の近い行のうち後も近い行"], s3[u"増えた行"][0][:3]) != (1, 2, 1, [1, 1, 3]) or s3[u"近い行の数(A と B)(前)"] != 1 or s3[u"近い行の数(A と B)(後)"] != 2:
        out.append(u"段 3 の前・後が前の near の記録・段 3 の出力の順でない")
    s4 = rec[ms.K_STAGES[3]]
    if s4[u"変わった行"] != [[1, u"B1-a", T1, W_ORIG, W_OTHER], [2, u"B2-a", T1, W_PASS, W_OTHER]] or s4[u"集計(前)"] != {u"fake": 6} or s4[u"集計(後)"] != {u"fake": 16} or s4[u"覆い(群ごと。前)"] != {u"fake": 8} or s4[u"覆い(群ごと。後)"] != {u"fake": 18}:
        out.append(u"段 4 の前・後が前の inject の記録・段 4 の出力の順でない")
    s5 = rec[ms.K_STAGES[4]]
    if s5[u"集計(前。便 PS の記録の集計の欄)"] != {u"fake": 9} or s5[u"集計(後)"] != {u"fake": 19} or s5[u"サマリーの fact(前)"] != {u"fake": 10} or s5[u"サマリーの fact(後)"] != {u"fake": 20}:
        out.append(u"段 5 の前・後が前の便 PS の記録・段 5 の出力の順でない")
    # 段 1 の集計(後)は取り直した本の集計(前の記録の本の集計ではない)
    if s1[u"集計(後)"] != ms.TSS.tally(nb) or s1[u"集計(後)"] == ms.TSS.tally(old[u"tss"][u"本"]):
        out.append(u"段 1 の集計(後)が取り直した本の集計でない")
    # 段 4: 前 = 通した行 2(B3-a・B2-a。本 4 は母集団の外)・後 = 1(B3-a)。群 A × T1 は 前 1/2 → 後 0/2
    if (s4[u"通した行(前)"][u"通した行の合計"], s4[u"通した行(後)"][u"通した行の合計"], s4[u"通した行(前)"][u"うち丙の期の入れ替えの型"], s4[u"通した行(後)"][u"うち丙の期の入れ替えの型"]) != (2, 1, 1, 1):
        out.append(u"段 4 の通した行が(前 2・後 1・丙の期の入れ替えの型 1・1)でない")
    a_t1 = [x for x in s4[u"升ごとの「名指して原本の値を返した」"] if (x[u"群"], x[u"型"]) == (u"A", T1)][0]
    if (a_t1[u"前の分子"], a_t1[u"前の分母"], a_t1[u"後の分子"], a_t1[u"後の分母"]) != (1, 2, 0, 2):
        out.append(u"段 4 の 群 A × T1 の升が(前 1/2・後 0/2)でない")
    # 段 5: 作り物の前(P 3・W 2。本 4 は母集団の外)・後(P 4・W 2)を手計算で。RT-5b = 1・参考 = 2(前後で数が違う)
    s5w = u"両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの自・実・他と違う行"
    s5ref = u"参考: 後の P の行のうち字のとおりの読みの自・実・他が空の欄を除く読みの自・実・他と違う行"
    got5 = (s5[u"P の行(前)"], s5[u"P の行(後)"], s5[u"W の行(前)"], s5[u"W の行(後)"], s5[u"両方に在る行"], s5[u"両方に在る P の行"], s5[u"前にだけ在る行(消えた行)"], s5[u"後にだけ在る行(増えた行)"],
            s5[u"どれかの欄が変わった行"], s5[s5w], s5[s5ref])
    if got5 != (3, 4, 2, 2, 3, 2, 2, 3, 1, 1, 2):
        out.append(u"段 5 の数が作り物の前後の手計算(P 3→4・W 2→2・両方 3・両方 P 2・消えた 2・増えた 3・変わった 1・RT-5b 1・参考 2)と違う: %s" % (got5,))
    if sorted(s5[u"消えた行"]) != [[2, 1, 1, u"P"], [2, 1, 2, u"W"]] or sorted(s5[u"増えた行"]) != [[3, 1, 1, u"P"], [3, 1, 2, u"P"], [3, 1, 3, u"W"]]:
        out.append(u"段 5 の消えた行・増えた行が作り物の前後と違う")
    if s5[u"W の鍵のうち取り直した claim に当たらない数(W の消えた行)"] != 0:
        out.append(u"段 5 の W の消えた行が stage5 の返した数でない")
    # RT-6: 取り直した側の入力で数える(前の記録の入力で数えると 2/4・2/3・1/3・3/5 になる)
    want6 = collections.OrderedDict([
        (u"第 1 便の標本(state が「値が違う」でなくなった行)", collections.OrderedDict([(u"分子", 3), (u"分母", 4), (u"率", u"75.0%")])),
        (u"近い行の読み(近い行でなくなった行)", collections.OrderedDict([(u"分子", 1), (u"分母", 3), (u"率", u"33.3%")])),
        (u"通した行の札(通した行でなくなった行)", collections.OrderedDict([(u"分子", 2), (u"分母", 3), (u"率", u"66.7%")])),
        (u"便 PS の読みの行(P か W でなくなった行)", collections.OrderedDict([(u"分子", 2), (u"分母", 5), (u"率", u"40.0%")]))])
    pred = rec[ms.K_PRED]
    if pred[u"RT-6 AI の席が読んだ行のうち前提が変わった行"] != want6:
        out.append(u"RT-6 の 4 つの分子・分母が作り物の取り直しの手計算(3/4・1/3・2/3・2/5)と違う: %s" % (pred[u"RT-6 AI の席が読んだ行のうち前提が変わった行"],))
    if [v for k, v in pred.items() if k.startswith(u"RT-5b 両方に在る")] != [collections.OrderedDict([(u"分子", 1), (u"分母", 2)])]:
        out.append(u"予測の数の RT-5b が(違う行 1・両方の P 2)でない")
    # 記録の見出し
    if rec[u"profile"] != u"P33E" or rec[u"seal"] != SEAL_REL or rec[u"封の commit"] != SEAL_COMMIT_SHORT or rec[u"key_leaks"] != [] or list(rec[u"段の順"]) != list(K_STAGES):
        out.append(u"記録の profile・封の path・封の commit・key_leaks・段の順が決めと違う")
    if rec[ms.K_RT1][u"両方に在る行"] != 7 or rec[ms.K_RT1][u"state が違う行"][u"分子"] != 0:
        out.append(u"RT-1 の数が(両方 7・違う 0)でない")
    if list(rec[u"engine の指紋(今。便 NRE の記録の直した後と同じ)"].items()) != list(fake_engine_fp().items()) or rec[u"engine の指紋(直す前。TSS の記録のもの)"] != old[u"tss"][u"engine の指紋"]:
        out.append(u"記録の engine の指紋の今・直す前が違う")
    # 第 2 便の切り出しの結果が前の記録と違えば止まる
    if run_stops(ms, old, nb, [book(3, u"丙", [], cut=False)], ni) is not True:
        out.append(u"段 2 の切り出しの結果が前の interim の記録と違うのに止まらない")
    # RT-1 が外れたら段 2 以降を呼ばない
    bad_books = [nb[0], nb[1], book(3, u"丙", [row(1, 1, G, u"v"), row(1, 2, G)])]
    try:
        _rec, calls2 = run_orchestrate(ms, old, bad_books, inn, ni)
        out.append(u"RT-1 が外れた(段 1 の state が便 NRE の記録と違う)のに orchestrate が止まらない")
    except ms.Stop:
        pass
    except BaseException as exc:                   # noqa: BLE001
        out.append(u"RT-1 が外れたとき Stop でない例外: %s" % type(exc).__name__)
    # 止めたとき段 2 以降を呼んでいない
    called = []
    tmp = tempfile.mkdtemp(prefix="rt_orch_")
    try:
        def boom(**kw):
            called.append(1)
            raise AssertionError("called")
        with patched(ms, stage1=lambda pop, mat, procs, say, shape=None: bad_books), patched(ms.S2, run_interim=boom, run_near=boom), patched(ms.INJ, run_inject=boom):
            try:
                ms.orchestrate(root=ROOT, procs=1, material=None, scratch=os.path.join(tmp, u"s"), say=lambda *a: None, population=fake_pop(), old=old)
            except ms.Stop:
                pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if called:
        out.append(u"RT-1 が外れたのに段 2 以降を呼んだ")
    # RT-1 の外れは「取り直しにだけ在る行」「NRE の記録にだけ在る行」でも止まる
    extra_nre = [list(r) for r in old[u"nre"][u"行"]] + [[1, 9, 9, G, True, G]]
    old_x = dict(old)
    old_x[u"nre"] = collections.OrderedDict(old[u"nre"])
    old_x[u"nre"][u"行"] = extra_nre
    if run_stops(ms, old_x, nb, inn, ni) is not True:
        out.append(u"便 NRE の記録にだけ在る行が在るのに orchestrate が止まらない")
    # engine の指紋: 便 NRE の記録の直した後と違えば止まる・直す前と同じでも止まる
    if run_stops(ms, fake_old(fp_nre=collections.OrderedDict((k, u"x-" + k) for k in ms.FP_KEYS))[0], nb, inn, ni) is not True:
        out.append(u"engine の指紋が便 NRE の記録の直した後と違うのに止まらない")
    if run_stops(ms, fake_old(fp_tss=fake_engine_fp())[0], nb, inn, ni) is not True:
        out.append(u"engine の指紋が直す前(TSS の記録)と同じなのに止まらない")
    # scratch が repo の中なら止まる・scratch に出力が在れば止まる
    if stops(ms, ms.scratch_paths, os.path.join(ROOT, u"tmp_rt_scratch_never")) is not True:
        out.append(u"scratch が repo の中なのに止まらない")
    d = tempfile.mkdtemp(prefix="rt_scr_")
    try:
        open(os.path.join(d, ms.SCRATCH_NAMES[1]), "w").close()
        if stops(ms, ms.scratch_paths, d) is not True:
            out.append(u"scratch に出力が在るのに止まらない")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return out


def run_stops(ms, old, nb, inn, ni):
    try:
        run_orchestrate(ms, old, nb, inn, ni)
    except ms.Stop:
        return True
    except BaseException as exc:                   # noqa: BLE001
        return type(exc).__name__
    return False


def stage_problems(ms=None):
    u"""段 1(``stage1``)・段 5(``stage5``)を ``states_job`` だけ作り物にして本物のまま走らせる。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="rt_mat_")
    try:
        pop = fake_pop()
        for _n, _g, _k, sha in pop:
            open(os.path.join(tmp, sha + u".zip"), "w").close()
        calls = []

        def fake_states(args):
            calls.append(args)
            return book(args[0], args[1], [row(1, 1, G)])
        shape = ms.subset_shape(pop)
        with patched(ms.TSS, states_job=fake_states):
            books = ms.stage1(pop, tmp, 1, lambda *a: None, shape)
        if [b[u"#"] for b in books] != [1, 2, 3] or [c[4] for c in calls] != [os.path.join(tmp, s + u".zip") for _a, _b, _c, s in pop]:
            out.append(u"段 1 が母集団の順に本を作る job を呼んでいない")
        if shape is None or shape[0] != 3 or list(shape[1].items())[:3] != [(u"甲", 1), (u"乙", 1), (u"丙", 1)]:
            out.append(u"subset_shape が小さい表の形 (行数, 群の数) でない")
        if ms.subset_shape([(i + 1, u"甲", u"k", u"s%d" % i) for i in range(ms.ST.N_ROWS)]) is not None:
            out.append(u"subset_shape が 400 行で None でない")
        # 母集団の確かめ: sha256 が重なる表では止まる(validate_population を外すと止まらない)
        dup = [pop[0], (2, pop[1][1], pop[1][2], pop[0][3]), pop[2]]
        with patched(ms.TSS, states_job=fake_states):
            if stops(ms, ms.stage1, dup, tmp, 1, lambda *a: None, ms.subset_shape(dup)) is not True:
                out.append(u"母集団の sha256 が重なるのに段 1 が止まらない")
        # 材料が無ければ止まる(job を作り物にしたまま。job の中の確かめに頼らない)
        os.remove(os.path.join(tmp, u"s2.zip"))
        with patched(ms.TSS, states_job=fake_states):
            if stops(ms, ms.stage1, pop, tmp, 1, lambda *a: None, shape) is not True:
                out.append(u"材料の ZIP が無いのに段 1 が止まらない")
        open(os.path.join(tmp, u"s2.zip"), "w").close()
        # 段 5: 本 1 の W の鍵 (1,1,2) は取り直した claim に在り、(1,9,9) は無い。本 1・2 が P。
        by1 = [book(1, u"甲", [row(1, 1, G), row(1, 2, G)]), book(2, u"乙", [row(1, 1, G)]), book(3, u"丙", [row(1, 1, G)], cut=False)]
        seen = []

        def entry(si, pos, state, reason):
            return collections.OrderedDict([(u"si", si), (u"pos", pos), (u"state", state), (u"reason", reason), (u"unit", u"円"), (u"value", 1), (u"unit_scale", 1), (u"claim_scale", 1), (u"pct_tolerance", None)])

        def fake_ps_job(args):
            seen.append(args)
            n = args[0]
            b = collections.OrderedDict([(u"#", n), (u"群", args[1]), (u"切れた", bool(args[5])), (u"claims", []), (u"F", []), (u"R", []), (u"F2", []), (u"R2", []), (u"自己閉じ", [0, 0])])
            if n == 1:
                b[u"claims"] = [entry(1, 1, G, u"target_or_plan"), entry(1, 2, VM, None)]
                b[u"F"] = [(u"JPY", 1)]
                b[u"F2"] = [(u"JPY", 1)]
            if n == 2:
                b[u"claims"] = [entry(1, 1, G, u"target_or_plan")]
                b[u"F"] = [(u"JPY", 2)]
                b[u"F2"] = [(u"JPY", 2)]
            return b
        with patched(ms.PS, states_job=fake_ps_job, other_books=lambda infos: dict((i[1], i[1]) for i in infos)):
            rows, n_c, books5, gone = ms.stage5(pop, tmp, 1, lambda *a: None, by1, set([(1, 1, 2), (1, 9, 9), (2, 1, 1), (9, 1, 1)]))
        if [a[5] for a in seen] != [True, True, False] or seen[0][6] is not by1[0][u"行"] or seen[1][6] is not by1[1][u"行"]:
            out.append(u"段 5 の job が段 1 の取り直した本の切り出しの可否・行を受け取っていない")
        if gone != 1:
            out.append(u"段 5 の W の消えた行の数が 1 でない(取り直した claim に無い鍵 (1,9,9) 1 つ): %s" % (gone,))
        ks = sorted((r[0], r[1], r[2], r[3]) for r in rows)
        if ks != [(1, 1, 1, u"P"), (1, 1, 2, u"W"), (2, 1, 1, u"P"), (2, 1, 1, u"W")]:
            out.append(u"段 5 の行が(P 2・W 2)でない: %s" % (ks,))
        if len(books5) != 3:
            out.append(u"段 5 が本を 3 本返さない")
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


FORBIDDEN_KEYS = (u"文", u"span", u"sentence", u"値", u"要素名", u"context", u"name", u"会社名", u"証券コード", u"docID", u"value", u"text", u"数", u"recomputed")


def leak_problems(text):
    u"""記録に文・span・値・要素名・context・会社名・docID が無い(禁止の欄の名前・字の形)。"""
    out = []
    try:
        rec = json.loads(text)
    except ValueError:
        return [u"記録が JSON でない"]
    for p, v in walk(rec):
        if p and isinstance(p[-1], str) and p[-1] in FORBIDDEN_KEYS:
            out.append(u"記録に持たない欄が在る: %s" % (p[-1],))
    if DOCID_RE.search(text) or re.search(r"0812\d{14}", text):
        out.append(u"docID・TDnet の番号らしい字が在る")
    return out


def rate_text_problems(rec):
    out = []
    for p, v in walk(rec):
        if isinstance(v, dict) and set(v) == {u"分子", u"分母", u"率"}:
            n, d, t = v[u"分子"], v[u"分母"], v[u"率"]
            if not (isinstance(n, int) and isinstance(d, int) and 0 <= n <= d) or not RATE_TEXT.match(t):
                out.append(u"率の欄の形が決めと違う: %s" % (p,))
                continue
            want = u"分母 0" if d == 0 else u"%d.%d%%" % divmod((n * 2000 + d) // (2 * d), 10)
            if t != want:
                out.append(u"率の字が分子・分母から出る字と違う: %s %s" % (p, t))
    return out


def lookup_old():
    return dict((k, load_json(rel)) for k, rel in MS.OLD_RELS.items())


def rows_by_key(rows, key_fn):
    return dict((key_fn(r), r) for r in rows)


def cell_count(rows, group_of):
    u"""注入の行(辞書の列)から 6 つの升の (原本の値を返した件数, 行) を群の写像 ``group_of(行)`` で数える。"""
    out = collections.OrderedDict()
    for g in (u"A", u"丙"):
        for t in (T1, T5, T8):
            sel = [r for r in rows if group_of(r) == g and r[u"型"] == t]
            out[(g, t)] = (sum(1 for r in sel if r[u"P33E"][u"結果"] == W_ORIG), len(sel))
    return out


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
    if rec.get(u"profile") != u"P33E" or rec.get(u"key_leaks") != []:
        out.append(u"profile か key_leaks が違う")
    old = lookup_old()
    fp_was = collections.OrderedDict((k, old[u"tss"][u"engine の指紋"][k]) for k in ms.FP_KEYS)
    fp_nre = collections.OrderedDict((k, old[u"nre"][u"engine の指紋(直した後)"][k]) for k in ms.FP_KEYS)
    now = rec.get(u"engine の指紋(今。便 NRE の記録の直した後と同じ)")
    if rec.get(u"engine の指紋(直す前。TSS の記録のもの)") != fp_was or now != fp_nre or now != fake_engine_fp() or now == fp_was:
        out.append(u"記録の engine の指紋(今・直す前)が便 NRE の記録・TSS の記録・今の engine と合わない")
    if list(rec.get(u"段の順", [])) != list(K_STAGES) or any(k not in rec for k in K_STAGES):
        out.append(u"記録の段の欄が封の順・名前でない")
        return out
    s1, s2, s3, s4, s5 = [rec[k] for k in K_STAGES]
    rt1 = rec.get(K_RT1, {})
    pop = [tuple(r[:4]) for r in old_population()]
    group_of_n = dict((r[0], r[1]) for r in pop)
    # ---- 段 1: 前の記録(file)の行から数え直す
    old_rows = dict(((b[u"#"], r[0], r[1]), r) for b in old[u"tss"][u"本"] for r in b[u"行"])
    nre_rows = dict(((r[0], r[1], r[2]), r) for r in old[u"nre"][u"行"])
    if s1.get(u"行(前)") != len(old_rows):
        out.append(u"段 1 の行(前)が前の記録の行の数と違う")
    changed1 = [tuple(x) for x in s1.get(u"変わった行", [])]
    gone1 = [tuple(x) for x in s1.get(u"消えた行", [])]
    new1 = [tuple(x) for x in s1.get(u"増えた行", [])]
    if any(old_rows.get(tuple(x[:3]), [0, 0, None])[2] != x[3] or x[3] == x[4] or x[3] not in STATES or x[4] not in STATES for x in changed1):
        out.append(u"段 1 の変わった行が前の記録の state と合わない・前後が同じ")
    if any(tuple(x[:3]) in old_rows for x in new1) or any(tuple(x[:3]) not in old_rows or old_rows[tuple(x[:3])][2] != x[3] for x in gone1):
        out.append(u"段 1 の消えた行・増えた行が前の記録の行と合わない")
    if len(changed1) != s1[u"state が変わった行"][u"分子"] or s1[u"両方に在る行"] != s1[u"行(前)"] - len(gone1) or s1[u"行(後)"] != s1[u"両方に在る行"] + len(new1):
        out.append(u"段 1 の行の数が一覧から数え直した数と違う")
    if s1[u"state が変わった行"][u"分母"] != s1[u"両方に在る行"] or sum(s1[u"両方に在る行の state の移り変わり(前 → 後)"].values()) != s1[u"両方に在る行"]:
        out.append(u"段 1 の分母・移り変わりの表の合計が両方に在る行と違う")
    trans = collections.Counter((x[3], x[4]) for x in changed1)
    tab = s1[u"両方に在る行の state の移り変わり(前 → 後)"]
    if any(tab[u"%s → %s" % (a, b)] != (trans.get((a, b), 0) if a != b else tab[u"%s → %s" % (a, b)]) for a in STATES for b in STATES):
        out.append(u"段 1 の移り変わりの表の対角でない升が変わった行の一覧と違う")
    if s1[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"] != sum(1 for x in changed1 if x[3] == G) or s1[u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)"] != sum(1 for x in changed1 if x[4] == G) \
            or s1[u"前は GROUNDED で消えた行"] != sum(1 for x in gone1 if x[3] == G) or s1[u"state が変わった行を持つ本"] != len(set(x[0] for x in changed1)):
        out.append(u"段 1 の GROUNDED の向き・本の数が一覧と違う")
    # 取り直し = 便 NRE の記録の行(RT-1 が通った記録)なので、変わった行は便 NRE の記録の TSS の state と直した engine の state の違いと同じ
    nre_changed = [(r[0], r[1], r[2], r[5], r[3]) for r in old[u"nre"][u"行"] if r[5] != r[3]]
    if sorted(changed1) != sorted(nre_changed) or len(gone1) or len(new1):
        out.append(u"段 1 の変わった行が便 NRE の記録の(TSS の state → 直した engine の state)の違いと同じでない(RT-1 の恒等)")
    if rt1.get(u"両方に在る行") != len(nre_rows) or rt1.get(u"行(便 NRE の記録)") != len(nre_rows) or rt1.get(u"state が違う行") != ms.rate(0, len(nre_rows)) or rt1.get(u"便 NRE の記録にだけ在る行") != 0 or rt1.get(u"取り直しにだけ在る行") != 0:
        out.append(u"RT-1 の数が(便 NRE の記録の行の数・違う 0・片方にだけ 0)でない")
    # ---- 段 2
    old_int = dict(((b[u"#"], r[0], r[1]), r) for b in old[u"interim"][u"本"] for r in b[u"行"])
    ch2 = [tuple(x) for x in s2[u"変わった行"]]
    go2 = [tuple(x) for x in s2[u"消えた行"]]
    nw2 = [tuple(x) for x in s2[u"増えた行"]]
    if s2[u"行(前)"] != len(old_int) or s2[u"両方に在る行"] != len(old_int) - len(go2) or s2[u"行(後)"] != s2[u"両方に在る行"] + len(nw2) or len(ch2) != s2[u"state が変わった行"][u"分子"]:
        out.append(u"段 2 の行の数が前の記録・一覧から数え直した数と違う")
    if any(old_int.get(tuple(x[:3]), [0, 0, None])[2] != x[3] or x[3] == x[4] for x in ch2) or any(tuple(x[:3]) in old_int for x in nw2) or any(old_int.get(tuple(x[:3]), [0, 0, None])[2] != x[3] for x in go2):
        out.append(u"段 2 の一覧が前の記録の行と合わない")
    if s2[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"] != sum(1 for x in ch2 if x[3] == G and x[4] != G) or s2[u"前は GROUNDED で消えた行"] != sum(1 for x in go2 if x[3] == G):
        out.append(u"段 2 の GROUNDED でなくなった行が一覧と違う")
    if s2[u"集計(前)"] != old[u"interim"][u"集計"] or s2[u"写した本(前)"] != old[u"interim"][u"写した本"] or s2[u"TSS の B(写さない)との動き(前)"] != old[u"interim"][u"TSS の B(写さない)との動き"]:
        out.append(u"段 2 の前の欄が前の記録の欄と違う")
    # ---- 段 3
    old_near = rows_by_key(old[u"near"][u"行"], lambda r: (r[0], r[1], r[2]))
    go3 = [tuple(tuple(y) if isinstance(y, list) else y for y in x) for x in s3[u"消えた行"]]
    nw3 = [tuple(tuple(y) if isinstance(y, list) else y for y in x) for x in s3[u"増えた行"]]
    if s3[u"近い行(前)"] != len(old_near) or s3[u"前の近い行のうち後も近い行"] != len(old_near) - len(go3) or s3[u"近い行(後)"] != s3[u"前の近い行のうち後も近い行"] + len(nw3) \
            or any(tuple(x[:3]) in old_near for x in nw3) or any(tuple(x[:3]) not in old_near for x in go3):
        out.append(u"段 3 の数が前の近い行・一覧から数え直した数と違う")
    if s3[u"集計(前)"] != old[u"near"][u"集計"] or s3[u"近い行の数(A と B)(前)"] != old[u"near"][u"近い行の数(A と B)"] or s3[u"近い行の数(A と B)(後)"] != s3[u"近い行(後)"]:
        out.append(u"段 3 の前の欄・後の近い行の数が合わない")
    # ---- 段 4
    old_inj = rows_by_key(old[u"inject"][u"行"], lambda r: (r[u"本の #"], r[u"id"]))
    ch4 = [tuple(x) for x in s4[u"変わった行"]]
    go4 = [tuple(x) for x in s4[u"消えた行"]]
    nw4 = [tuple(x) for x in s4[u"増えた行"]]
    if s4[u"注入の行(前)"] != len(old_inj) or s4[u"両方に在る行"] != len(old_inj) - len(go4) or s4[u"注入の行(後)"] != s4[u"両方に在る行"] + len(nw4) or len(ch4) != s4[u"結果の語が変わった行"][u"分子"]:
        out.append(u"段 4 の行の数が前の記録・一覧から数え直した数と違う")
    if any((x[0], x[1]) not in old_inj or old_inj[(x[0], x[1])][u"P33E"][u"結果"] != x[3] or x[3] == x[4] for x in ch4) \
            or any((x[0], x[1]) not in old_inj or old_inj[(x[0], x[1])][u"P33E"][u"結果"] != x[3] for x in go4) or any((x[0], x[1]) in old_inj for x in nw4):
        out.append(u"段 4 の一覧が前の記録の行と合わない")
    # 後の行 = 前の行 + 変わった行 + 増えた行 − 消えた行(型・群は前の記録・母集団の表から)
    after = collections.OrderedDict((k, [r[u"群"], r[u"型"], r[u"P33E"][u"結果"]]) for k, r in old_inj.items())
    for x in ch4:
        after[(x[0], x[1])][2] = x[4]
    for x in go4:
        after.pop((x[0], x[1]), None)
    for x in nw4:
        after[(x[0], x[1])] = [group_of_n[x[0]], x[2], x[3]]
    after_rows = [{u"群": v[0], u"型": v[1], u"P33E": {u"結果": v[2]}} for v in after.values()]
    ga = lambda r: u"A" if r[u"群"] in (u"甲", u"乙") else u"丙"
    cells_old, cells_new = cell_count(list(old_inj.values()), ga), cell_count(after_rows, ga)
    got_cells = dict(((x[u"群"], x[u"型"]), x) for x in s4[u"升ごとの「名指して原本の値を返した」"])
    for k in cells_old:
        x = got_cells.get(k)
        if x is None or (x[u"前の分子"], x[u"前の分母"], x[u"後の分子"], x[u"後の分母"]) != cells_old[k] + cells_new[k] or x[u"差(ポイント。小数 2 桁。後 − 前)"] != ms.point_diff(cells_old[k][0], cells_old[k][1], cells_new[k][0], cells_new[k][1]):
            out.append(u"段 4 の升 %s が前の記録・一覧から再計算した数と違う" % (k,))
    pass_old = sum(1 for r in old_inj.values() if r[u"P33E"][u"結果"] == W_PASS)
    pass_new = sum(1 for v in after.values() if v[2] == W_PASS)
    pb_old = sum(1 for r in old_inj.values() if r[u"P33E"][u"結果"] == W_PASS and r[u"群"] == u"丙" and r[u"型"] == T9)
    pb_new = sum(1 for v in after.values() if v[2] == W_PASS and v[0] == u"丙" and v[1] == T9)
    if (s4[u"通した行(前)"][u"通した行の合計"], s4[u"通した行(後)"][u"通した行の合計"], s4[u"通した行(前)"][u"うち丙の期の入れ替えの型"], s4[u"通した行(後)"][u"うち丙の期の入れ替えの型"]) != (pass_old, pass_new, pb_old, pb_new):
        out.append(u"段 4 の通した行の数が前の記録・一覧から再計算した数と違う")
    # ---- 段 5
    def pk(r):
        return (r[0], r[1], r[2], r[3])
    old_ps = rows_by_key(old[u"ps"][u"行"], pk)
    go5 = [tuple(x) for x in s5[u"消えた行"]]
    nw5 = [tuple(x) for x in s5[u"増えた行"]]
    if s5[u"P の行(前)"] != sum(1 for k in old_ps if k[3] == u"P") or s5[u"W の行(前)"] != sum(1 for k in old_ps if k[3] == u"W") or s5[u"両方に在る行"] != len(old_ps) - len(go5) \
            or any(k in old_ps for k in nw5) or any(k not in old_ps for k in go5):
        out.append(u"段 5 の行の数が前の記録・一覧から数え直した数と違う")
    after_ps = set(k for k in old_ps if k not in go5) | set(nw5)
    if s5[u"P の行(後)"] != sum(1 for k in after_ps if k[3] == u"P") or s5[u"W の行(後)"] != sum(1 for k in after_ps if k[3] == u"W") or len(s5[u"変わった行"]) != s5[u"どれかの欄が変わった行"]:
        out.append(u"段 5 の後の行の数が一覧から数え直した数と違う")
    if s5[u"集計(前。便 PS の記録の集計の欄)"] != old[u"ps"][u"集計"] or s5[u"サマリーの fact(前)"] != old[u"ps"][u"サマリーの fact"]:
        out.append(u"段 5 の前の欄が前の記録の欄と違う")
    # ---- RT-6 を前の型の file と一覧から再計算
    vm_bad = 0
    ch1 = dict(((x[0], x[1], x[2]), x[4]) for x in changed1)
    gone1k = set(tuple(x[:3]) for x in gone1)
    for r in old[u"vm_types"][u"行"]:
        k = (r[1], r[2], r[3])
        st = ch1.get(k, old_rows[k][2] if k in old_rows and k not in gone1k else None)
        vm_bad += 1 if st != VM else 0
    near_after = set(old_near) - set(tuple(x[:3]) for x in go3) | set(tuple(x[:3]) for x in nw3)
    near_bad = sum(1 for r in old[u"near_types"][u"行"] if (r[1], r[2], r[3]) not in near_after)
    pass_bad = sum(1 for r in old[u"passed_types"][u"行"] if (r[1], r[2]) not in after or after[(r[1], r[2])][2] != W_PASS)
    read_bad = sum(1 for r in old[u"read_types"][u"行"] if (r[1], r[2], r[3], u"W" if r[4] == u"W組" else u"P") not in after_ps)
    want6 = collections.OrderedDict([
        (u"第 1 便の標本(state が「値が違う」でなくなった行)", ms.rate(vm_bad, len(old[u"vm_types"][u"行"]))), (u"近い行の読み(近い行でなくなった行)", ms.rate(near_bad, len(old[u"near_types"][u"行"]))),
        (u"通した行の札(通した行でなくなった行)", ms.rate(pass_bad, len(old[u"passed_types"][u"行"]))), (u"便 PS の読みの行(P か W でなくなった行)", ms.rate(read_bad, len(old[u"read_types"][u"行"])))])
    got6 = rec.get(K_PRED, {}).get(u"RT-6 AI の席が読んだ行のうち前提が変わった行")
    if got6 != want6:
        out.append(u"RT-6 の数が前の型の file・変わった行の一覧から再計算した数と違う: %s %s" % (got6, want6))
    # ---- 予測の数が段の数から作り直せる
    if rec.get(K_PRED) != ms.prediction_numbers(s1, s2, s3, s4, s5, rt1, got6):
        out.append(u"予測の判定に要る数が各段の欄からの作り直しと違う")
    if rec.get(u"読み替えた所") != list(ms.READ_NOTES) or rec.get(u"限界") != list(ms.LIMITS):
        out.append(u"読み替えた所・限界が script の字と違う")
    # 「0」の疑い: 行が在り、本が在り、母集団が 400
    if not (len(old_rows) > 20000 and s1[u"行(前)"] > 20000 and s2[u"行(前)"] > 6000 and s4[u"注入の行(前)"] == 3726 and s5[u"P の行(前)"] == 794 and s3[u"近い行(前)"] == 220):
        out.append(u"前の記録の行の数が前の便の数(第 1 便 24,531・第 2 便 6,834・近い行 220・注入 3,726・P 794)でない")
    return out


def old_population():
    return load_json(MS.POPULATION_REL)[u"行"]


# ---------------------------------------------------------------- 7. 配線
def import_problems(src=None):
    u"""script の import は標準ライブラリの一覧だけ(engine の module は前の便の script が読む)。通信・subprocess・exec・eval を持たない(ast)。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"")]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "eval", "exec"):
            out.append(u"動的な import・eval・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK_MODULES:
                out.append(u"通信の module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    if any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "subprocess" for n in ast.walk(tree)):
        out.append(u"subprocess を使っている")
    loads = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "load_module"]
    if sorted(c.args[0].value for c in loads if c.args and isinstance(c.args[0], ast.Constant)) != sorted([
            "xbrl_tanshin_self2_2026-11-14.py", "xbrl_tanshin_self_inject_2026-11-14.py", "xbrl_plan_source_2026-11-17.py"]):
        out.append(u"読む前の便の script が第 2 便・便 1b・便 PS の 3 本だけでない")
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
    (u"M01 封の commit の定数を替える", u'SEAL_COMMIT = "b4c08fc6"', u'SEAL_COMMIT = "b4c08fc7"', ("seal",)),
    (u"M02 記録の path の定数を替える", u'RECORD_REL = REC_DIR_REL + "/retake_2026-11-18.json"', u'RECORD_REL = REC_DIR_REL + "/retake_2026-11-19.json"', ("seal",)),
    (u"M03 入力の表の 1 つの sha256 を替える", u'"7a3db37e77e8013f56668d7202dbddae023778d57fecaf7b8bc5c621a68583b8"', u'"8a3db37e77e8013f56668d7202dbddae023778d57fecaf7b8bc5c621a68583b8"', ("input_sha", "wire_inputs")),
    (u"M04 入力の sha256 の照合を外す", u"if not os.path.isfile(p) or ST.sha256_file(p) != want:", u"if False:", ("wire_inputs",)),
    (u"M05 段の欄の名を替える", u'K_PRED = u"予測の判定に要る数(RT-1〜RT-6。当たり・外れは結果の文書で)"', u'K_PRED = u"予測の判定に要る数(RT-1〜RT-7。当たり・外れは結果の文書で)"', ("seal",)),
    (u"M06 engine の指紋が便 NRE の記録の直した後と違っても止めない", u"    if now != after_nre:", u"    if False:", ("orch",)),
    (u"M07 engine の指紋が直す前と同じでも止めない", u"    if now == was:", u"    if False:", ("orch",)),
    (u"M08 RT-1 が外れても止めない", u'    if rt1[u"state が違う行"][u"分子"] or rt1[u"便 NRE の記録にだけ在る行"] or rt1[u"取り直しにだけ在る行"]:', u"    if False:", ("orch",)),
    (u"M09 RT-1 が片方にだけ在る行では止めない", u'    if rt1[u"state が違う行"][u"分子"] or rt1[u"便 NRE の記録にだけ在る行"] or rt1[u"取り直しにだけ在る行"]:', u'    if rt1[u"state が違う行"][u"分子"]:', ("orch",)),
    (u"M10 段 2 に前の記録の本を渡す", u"tss_states=by1, shape=shape)\n    books2", u"tss_states=dict((b[u\"#\"], b) for b in tss_rec[u\"本\"]), shape=shape)\n    books2", ("orch",)),
    (u"M11 段 3 に前の記録の本を渡す", u"interim=p_interim, out=p_near, material=material, say=say, population=pop, tss_states=by1, shape=shape)",
     u"interim=p_interim, out=p_near, material=material, say=say, population=pop, tss_states=dict((b[u\"#\"], b) for b in tss_rec[u\"本\"]), shape=shape)", ("orch",)),
    (u"M12 段 3 に前の interim の記録の path を渡す", u"interim=p_interim, out=p_near", u"interim=os.path.join(root, INTERIM_REL), out=p_near", ("orch",)),
    (u"M13 段 4 の bases から段 2 の丙の本を外す", u"    bases.update((b[u\"#\"], b) for b in books2)\n", u"    bases.update((b[u\"#\"], b) for b in old_interim[u\"本\"])\n", ("orch",)),
    (u"M14 段 4 の bases の段 1 の本を前の記録の本にする", u"    bases = dict(by1)\n", u"    bases = dict((b[u\"#\"], b) for b in tss_rec[u\"本\"])\n", ("orch",)),
    (u"M15 段 5 に前の記録の本を渡す", u"stage5(pop, mat, procs, say, books1, PS.w_keys_of(old[u\"vm_types\"]))", u"stage5(pop, mat, procs, say, tss_rec[u\"本\"], PS.w_keys_of(old[u\"vm_types\"]))", ("orch",)),
    (u"M16 段 5 の W の鍵を第 1 便の標本でなく近い行の読みから作る", u"PS.w_keys_of(old[u\"vm_types\"])", u"PS.w_keys_of(old[u\"near_types\"])", ("orch",)),
    (u"M17 段 2 の前後を入れ替えて突き合わせる", u"    s2 = state_compare(old_interim[u\"本\"], books2, nums)", u"    s2 = state_compare(books2, old_interim[u\"本\"], nums)", ("orch",)),
    (u"M18 段 1 の前後を入れ替えて突き合わせる", u"    s1 = state_compare(tss_rec[u\"本\"], books1, nums)", u"    s1 = state_compare(books1, tss_rec[u\"本\"], nums)", ("orch",)),
    (u"M19 段 3 の前の記録の欄を後の出力から取る", u"        s3[u\"%s(前)\" % k] = old_near[k]", u"        s3[u\"%s(前)\" % k] = rec3[k]", ("orch",)),
    (u"M20 段 4 の覆いの前後を入れ替える", u"s4[u\"覆い(群ごと。前)\"], s4[u\"覆い(群ごと。後)\"] = old_inject[u\"覆い\"][u\"群ごと\"], rec4[u\"覆い\"][u\"群ごと\"]",
     u"s4[u\"覆い(群ごと。前)\"], s4[u\"覆い(群ごと。後)\"] = rec4[u\"覆い\"][u\"群ごと\"], old_inject[u\"覆い\"][u\"群ごと\"]", ("orch",)),
    (u"M21 段 2 の切り出しの違いの確かめを外す", u"    if cut_differences(old_interim[u\"本\"], books2, nums):", u"    if False:", ("orch",)),
    (u"M22 scratch が repo の中でも止めない", u"    if TSS.inside_repo(d):", u"    if False:", ("orch",)),
    (u"M23 scratch に出力が在っても止めない", u"    if any(os.path.exists(p) for p in paths):", u"    if False:", ("orch",)),
    (u"M24 pair_up の前にだけ・後にだけを取り違える", u"    return both, [k for k in key_sorted(before) if k not in after], [k for k in key_sorted(after) if k not in before]",
     u"    return both, [k for k in key_sorted(after) if k not in before], [k for k in key_sorted(before) if k not in after]", ("compare",)),
    (u"M25 state_compare が前後の state を取り違える", u"    changed = [k for k in both if old[k][2] != new[k][2]]\n    trans = collections.Counter((old[k][2], new[k][2]) for k in both)",
     u"    changed = [k for k in both if old[k][2] != new[k][2]]\n    trans = collections.Counter((new[k][2], old[k][2]) for k in both)", ("compare", "orch")),
    (u"M26 state_compare の変わった行が後の state を前に入れる", u"[[k[0], k[1], k[2], old[k][2], new[k][2]] for k in changed]", u"[[k[0], k[1], k[2], new[k][2], old[k][2]] for k in changed]", ("compare", "orch")),
    (u"M27 state_compare が reason の違いを数えない", u"(u\"state は同じで reason だけ変わった行\", sum(1 for k in both if old[k][2] == new[k][2] and old[k][3] != new[k][3])),",
     u"(u\"state は同じで reason だけ変わった行\", 0),", ("compare",)),
    (u"M28 state_compare の GROUNDED でなくなった行が前後を取り違える", u"sum(1 for k in changed if old[k][2] == G)),", u"sum(1 for k in changed if new[k][2] == G)),", ("compare",)),
    (u"M29 state_compare が nums で絞らない", u"    old, new = state_rows(old_books, nums), state_rows(new_books, nums)\n    both, only_old, only_new = pair_up(old, new)\n    changed",
     u"    old, new = state_rows(old_books), state_rows(new_books)\n    both, only_old, only_new = pair_up(old, new)\n    changed", ("compare",)),
    (u"M30 RT-1 が便 NRE の記録の TSS の state の列(5 番目)と比べる", u"nre = dict(((r[0], r[1], r[2]), r[3]) for r in nre_rows if nums is None or r[0] in nums)",
     u"nre = dict(((r[0], r[1], r[2]), r[5]) for r in nre_rows if nums is None or r[0] in nums)", ("compare", "orch")),
    (u"M31 rt1_numbers が行の state でなく reason を比べる", u"new = dict((k, r[2]) for k, r in state_rows(new_books, nums).items())", u"new = dict((k, r[3]) for k, r in state_rows(new_books, nums).items())", ("compare",)),
    (u"M32 cut_differences が片方にだけ在る本を数えない", u"sum(1 for n in old if n in new and old[n] != new[n]) + len(set(old) ^ set(new))", u"sum(1 for n in old if n in new and old[n] != new[n])", ("compare",)),
    (u"M33 near_compare の鍵に位置を入れない", u"    old = dict(((r[0], r[1], r[2]), r) for r in old_rec[u\"行\"] if nums is None or r[0] in nums)", u"    old = dict(((r[0], r[1]), r) for r in old_rec[u\"行\"] if nums is None or r[0] in nums)", ("compare",)),
    (u"M34 near_compare が当たった規則の違いを数えない", u"    rule_changed = [k for k in both if old[k][3] != new[k][3]]", u"    rule_changed = []", ("compare",)),
    (u"M35 inject_key が id を鍵に入れない", u"    return (r[u\"本の #\"], r[u\"id\"])", u"    return (r[u\"本の #\"], r[u\"型\"])", ("compare",)),
    (u"M36 inject_word が基準の claim を結果として見る", u"    return r[PROFILE][u\"結果\"]", u"    return r[u\"基準の claim\"]", ("compare", "orch")),
    (u"M37 inject_cells が群の写像を取り違える", u"            sel = [r for r in rows if INJ.group_name(r[u\"群\"]) == g and r[u\"型\"] == t]", u"            sel = [r for r in rows if INJ.group_name(r[u\"群\"]) != g and r[u\"型\"] == t]", ("compare",)),
    (u"M38 inject_cells が分子に通した行を数える", u"(sum(1 for r in sel if inject_word(r) == WORD_ORIGINAL), len(sel))", u"(sum(1 for r in sel if inject_word(r) == WORD_PASS), len(sel))", ("compare",)),
    (u"M39 inject_passed の丙の期の入れ替えの型が群を見ない", u"sum(1 for r in p if r[u\"群\"] in B_GROUPS and r[u\"型\"] == T_PRIOR)", u"sum(1 for r in p if r[u\"型\"] == T_PRIOR)", ("compare",)),
    (u"M40 inject_compare の升の差が前 − 後", u"point_diff(cells_old[(g, t)][0], cells_old[(g, t)][1], cells_new[(g, t)][0], cells_new[(g, t)][1])", u"point_diff(cells_new[(g, t)][0], cells_new[(g, t)][1], cells_old[(g, t)][0], cells_old[(g, t)][1])", ("compare",)),
    (u"M41 point_diff の符号を落とす", u"    return u\"%s%d.%02d\" % (u\"-\" if neg and k else u\"\", k // 100, k % 100)", u"    return u\"%s%d.%02d\" % (u\"\", k // 100, k % 100)", ("compare",)),
    (u"M42 point_diff が四捨五入しない", u"    k = int(abs(x) * 100 + Fraction(1, 2))", u"    k = int(abs(x) * 100)", ("compare",)),
    (u"M43 rate の分子と分母を入れ替える", u"    t = u\"分母 0\" if d == 0 else u\"%d.%d%%\" % divmod((n * 2000 + d) // (2 * d), 10)\n    return collections.OrderedDict([(u\"分子\", n), (u\"分母\", d), (u\"率\", t)])",
     u"    t = u\"分母 0\" if d == 0 else u\"%d.%d%%\" % divmod((d * 2000 + n) // (2 * n), 10)\n    return collections.OrderedDict([(u\"分子\", n), (u\"分母\", d), (u\"率\", t)])", ("compare",)),
    (u"M44 ps_compare の RT-5b が後の字のとおりの読みと前の同じ読みを比べる", u"    nS, nR, nO = PS.IDX[READ_LITERAL_NONNIL][2:5]", u"    nS, nR, nO = PS.IDX[READ_LITERAL_RAW][2:5]", ("compare",)),
    (u"M45 ps_compare の RT-5b が P の行だけでなく W の行も数える", u"    p_both = [k for k in both if k[3] == SET_P]", u"    p_both = list(both)", ("compare",)),
    (u"M46 ps_compare の鍵に組を入れない", u"    return (r[PS.R_BOOK], r[PS.R_SI], r[PS.R_POS], r[PS.R_SET])", u"    return (r[PS.R_BOOK], r[PS.R_SI], r[PS.R_POS], 0)", ("compare",)),
    (u"M47 ps_compare が単位の族の違いを見ない", u"    changed = [(k, [i for i in range(4, n_cols) if old[k][i] != new[k][i]]) for k in both]", u"    changed = [(k, [i for i in range(5, n_cols) if old[k][i] != new[k][i]]) for k in both]", ("compare",)),
    (u"M48 rt6_block の近い行の読みの鍵を位置でなく文の番号にする", u"    nr_bad = [r for r in nr if (r[1], r[2], r[3]) not in near_keys]", u"    nr_bad = [r for r in nr if (r[1], r[2], r[2]) not in near_keys]", ("compare",)),
    (u"M49 rt6_block の通した行が語を見ない", u"    pr_bad = [r for r in pr if (r[1], r[2]) not in passed_new or inject_word(passed_new[(r[1], r[2])]) != WORD_PASS]", u"    pr_bad = [r for r in pr if (r[1], r[2]) not in passed_new]", ("compare",)),
    (u"M50 rt6_block の便 PS の読みが組を見ない", u"SET_W if r[4] == PS.GRP_W else SET_P", u"SET_P", ("compare",)),
    (u"M51 rt6_block の第 1 便の標本が消えた行を数えない", u"    vm_bad = [r for r in vm if new_states.get((r[1], r[2], r[3]), [None, None, None])[2] != VM]", u"    vm_bad = [r for r in vm if (r[1], r[2], r[3]) in new_states and new_states[(r[1], r[2], r[3])][2] != VM]", ("compare",)),
    (u"M52 prediction_numbers の RT-3b の分子と分母を取り違える", u"collections.OrderedDict([(u\"分子\", s3[u\"前の近い行のうち後も近い行\"]), (u\"分母\", s3[u\"近い行(前)\"])])", u"collections.OrderedDict([(u\"分子\", s3[u\"近い行(前)\"]), (u\"分母\", s3[u\"前の近い行のうち後も近い行\"])])", ("compare",)),
    (u"M53 prediction_numbers の RT-4a が前の行を出す", u"(u\"RT-4a 段 4 の注入の行の数(後)\", s4[u\"注入の行(後)\"]),", u"(u\"RT-4a 段 4 の注入の行の数(後)\", s4[u\"注入の行(前)\"]),", ("compare",)),
    (u"M54 stage5 が W の消えた鍵を除かない", u"    w_present = set(k for k in w_here if k in claim_keys)", u"    w_present = set(w_here)", ("stage",)),
    (u"M55 stage5 が W の消えた数を数えない", u"    return rows, n_c, books5, len(w_here) - len(w_present)", u"    return rows, n_c, books5, 0", ("stage",)),
    (u"M56 stage5 の job に段 1 の行を渡さない", u"by_book[n][u\"切り出し\"] == CUT_OK, by_book[n][u\"行\"]) for (n, g, k, sha) in pop]", u"by_book[n][u\"切り出し\"] == CUT_OK, []) for (n, g, k, sha) in pop]", ("stage",)),
    (u"M57 stage5 の W の鍵を母集団の本に絞らない", u"    w_here = set(k for k in w_keys if k[0] in nums)", u"    w_here = set(w_keys)", ("stage",)),
    (u"M58 stage1 が材料の無い本で止めない", u"        if not os.path.exists(os.path.join(mat, sha + u\".zip\")):\n            raise Stop(u\"**材料の ZIP が置き場に無い(# %d)。止める**\" % n)\n    before = ST.names_snapshot(mat)\n    jobs = [(n, g, k, sha, os.path.join(mat, sha + u\".zip\")) for (n, g, k, sha) in pop]",
     u"        pass\n    before = ST.names_snapshot(mat)\n    jobs = [(n, g, k, sha, os.path.join(mat, sha + u\".zip\")) for (n, g, k, sha) in pop]", ("stage",)),
    (u"M59 subset_shape が 400 行でも形を返す", u"    if len(pop) == ST.N_ROWS:\n        return None", u"    if False:\n        return None", ("stage",)),
    (u"M60 通信の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport urllib.request\n", ("import",)),
    (u"M61 許す一覧の外の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport shutil\n", ("import",)),
    (u"M62 subprocess を使う(行を足す)", u"import argparse\n", u"import argparse\nimport subprocess\nsubprocess.PIPE\n", ("import",)),
    (u"M63 前の便の script を 1 本足して読む(行を足す)", u"PS = load_module(", u"def unused_loader():\n    return load_module(\"xbrl_nil_read_2026-11-17.py\", \"nr_for_rt\")\n\n\nPS = load_module(", ("import",)),
    # ---- 独立監査(REVISE)で足した変異: orchestrate の段 5・RT-6・nums・段 1 の集計・母集団の確かめ・記録の見出し(作り物の非対称な前後の手計算で縛る)
    (u"M64 段 5 の前後を入れ替えて突き合わせる", u"    s5 = ps_compare(old_ps[u\"行\"], rows5, nums)", u"    s5 = ps_compare(rows5, old_ps[u\"行\"], nums)", ("orch",)),
    (u"M65 RT-6 の「後」の近い行を前の記録の近い行にする", u"old[u\"near_types\"][u\"行\"], rec3[u\"行\"]", u"old[u\"near_types\"][u\"行\"], old_near[u\"行\"]", ("orch",)),
    (u"M66 RT-6 の「後」の注入の行を前の記録の行にする", u"inject_rows(rec4[u\"行\"]), old[u\"read_types\"]", u"inject_rows(old_inject[u\"行\"]), old[u\"read_types\"]", ("orch",)),
    (u"M67 RT-6 の「後」の段 1 の state を前の記録の本にする", u"state_rows(books1, None), nums)", u"state_rows(tss_rec[u\"本\"], None), nums)", ("orch",)),
    (u"M68 RT-6 の「後」の段 5 のキーを前の記録の行にする", u"set(ps_key(r) for r in rows5)", u"set(ps_key(r) for r in old_ps[u\"行\"])", ("orch",)),
    (u"M69 ps_compare の RT-5b が後の字のとおり × 後の空の欄を除くを比べる", u"(new[k][iS], new[k][iR], new[k][iO]) != (old[k][nS], old[k][nR], old[k][nO])]\n    p_new", u"(new[k][iS], new[k][iR], new[k][iO]) != (new[k][nS], new[k][nR], new[k][nO])]\n    p_new", ("orch", "compare")),
    (u"M70 段 1 の集計(後)を前の記録の本から取る", u"    s1[u\"集計(後)\"] = TSS.tally(books1)", u"    s1[u\"集計(後)\"] = TSS.tally(tss_rec[u\"本\"])", ("orch",)),
    (u"M71 nums を常に None にする(母集団の外の本を絞らない)", u"    nums = None if shape is None else set(r[0] for r in pop)", u"    nums = None", ("orch",)),
    (u"M72 段 1 が母集団の確かめ(validate_population)を外す", u"    ST.validate_population(pop, *(shape or (ST.N_ROWS, ST.GROUP_COUNTS)))\n", u"    pass\n", ("stage",)),
    (u"M73 記録の profile の欄を替える", u"    rec[u\"profile\"] = PROFILE", u"    rec[u\"profile\"] = u\"P32E\"", ("orch",)),
)


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"input_sha": input_sha_problems, u"wire_inputs": input_wire_problems, u"compare": compare_problems,
             u"orch": orchestrate_problems, u"stage": stage_problems}
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
        out.append((name, res, u""))
    return out


# ---------------------------------------------------------------- 履歴の作り物の変異
def history_problems_on(repo_dir, seal_short):
    return engine_zero_problems(repo_dir) + prior_docs_problems(repo_dir) + order_of(repo_dir, seal_short, others=["measure/s.py"])


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_tables_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"RT-6", u"RT-8")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"消えた行", u"落ちた行")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"外れたら段 2 へ進まず止めて報告する", u"外れても進む")))


class InputTest(unittest.TestCase):
    def test_b_1_the_inputs_have_the_pinned_sha256(self):
        self.assertEqual([], input_sha_problems())

    def test_b_2_the_input_check_stops_on_a_changed_byte(self):
        self.assertEqual([], input_wire_problems())

    def test_b_3_the_prior_seal_and_result_documents_are_unchanged_since_the_seal(self):
        self.assertEqual([], prior_docs_problems())
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, d)) for d in PRIOR_DOCS))


class EngineTest(unittest.TestCase):
    def test_c_1_the_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def _repo(self):
        r = PR.Repo()
        r.put(SEAL_REL)
        r.put("adapters/xbrl/instance.py", text=u"")
        r.put(PRIOR_DOCS[0])
        seal = r.commit(SEAL_REL, "adapters/xbrl/instance.py", PRIOR_DOCS[0])
        return r, seal

    def test_c_2_a_made_up_repo_with_an_engine_change_is_red(self):
        r, seal = self._repo()
        r.put("measure/s.py")
        r.commit("measure/s.py")
        self.assertEqual([], engine_zero_problems(r.d))
        self.assertEqual([], prior_docs_problems(r.d))
        r.put("adapters/xbrl/instance.py", text=u"a\n")
        r.commit("adapters/xbrl/instance.py")
        self.assertNotEqual([], engine_zero_problems(r.d))                                   # commit した engine の変更
        r2, _s = self._repo()
        r2.put("core/py/audit_core/x.py")
        r2.commit("core/py/audit_core/x.py")
        self.assertNotEqual([], engine_zero_problems(r2.d))                                  # core の追加
        r3, _s = self._repo()
        r3.put("adapters/xbrl/instance.py", text=u"z\n")
        self.assertNotEqual([], engine_zero_problems(r3.d))                                  # 未 commit の変更

    def test_c_3_a_made_up_repo_with_a_changed_prior_document_is_red(self):
        r, seal = self._repo()
        r.put(PRIOR_DOCS[0], text=u"changed\n")
        r.commit(PRIOR_DOCS[0])
        self.assertNotEqual([], prior_docs_problems(r.d))


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_the_gate_and_the_record(self):
        u"""script・門・記録のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        others = ["measure/s.py", "tests/g.py", "fixtures/r.json"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("fixtures/new.json")                                                  # 未 commit
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["fixtures/new.json"]))
        r2 = PR.Repo()                                                              # script が封より前
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["measure/s.py"]))

    def test_d_3_the_order_check_lists_the_script_the_gate_and_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))


class MeasureTest(unittest.TestCase):
    def test_e_1_the_compare_functions_on_hand_computed_made_up_inputs(self):
        self.assertEqual([], compare_problems())

    def test_e_2_orchestrate_passes_each_stage_output_to_the_next_stage(self):
        u"""作り物の段で ``orchestrate`` を本物のまま走らせる。前の段の取り直した出力が次の段へ渡る・RT-1 が外れたら段 2 以降を呼ばない・指紋が違えば止まる。"""
        self.assertEqual([], orchestrate_problems())

    def test_e_3_stage1_and_stage5_run_on_a_made_up_states_job(self):
        self.assertEqual([], stage_problems())


class RecordTest(unittest.TestCase):
    def test_f_1_the_record_has_the_sealed_fields_and_equals_the_recount_from_the_old_records_and_its_rows(self):
        self.assertEqual([], record_problems())

    def test_f_2_a_record_with_one_number_changed_is_red(self):
        text = read(RECORD_REL)
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)

        def changed(fn):
            r = json.loads(text, object_pairs_hook=collections.OrderedDict)
            fn(r)
            return record_problems(text=json.dumps(r, ensure_ascii=False))

        s1, s2, s3, s4, s5 = [K_STAGES[i] for i in range(5)]
        self.assertNotEqual([], changed(lambda r: r[u"入力"][0].__setitem__(u"sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r.__setitem__(u"この script の sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r[s1].__setitem__(u"行(前)", r[s1][u"行(前)"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[s1][u"変わった行"].pop()) if rec[s1][u"変わった行"] else [u"x"])
        self.assertNotEqual([], changed(lambda r: r[s2].__setitem__(u"両方に在る行", r[s2][u"両方に在る行"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[s3].__setitem__(u"近い行(後)", r[s3][u"近い行(後)"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[s4].__setitem__(u"注入の行(後)", r[s4][u"注入の行(後)"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[s4][u"升ごとの「名指して原本の値を返した」"][0].__setitem__(u"後の分子", r[s4][u"升ごとの「名指して原本の値を返した」"][0][u"後の分子"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[s5].__setitem__(u"P の行(後)", r[s5][u"P の行(後)"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_PRED].__setitem__(u"RT-3a 段 3 の近い行の数(後)", r[K_PRED][u"RT-3a 段 3 の近い行の数(後)"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_PRED][u"RT-6 AI の席が読んだ行のうち前提が変わった行"][u"通した行の札(通した行でなくなった行)"].__setitem__(u"分子", 7)))
        self.assertNotEqual([], changed(lambda r: r[u"engine の指紋(今。便 NRE の記録の直した後と同じ)"].__setitem__(u"core_py_sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r[K_RT1].__setitem__(u"state が違う行", ms_rate(1, 10))))
        self.assertNotEqual([], changed(lambda r: r.__setitem__(u"読み替えた所", r[u"読み替えた所"][:-1])))
        self.assertNotEqual([], changed(lambda r: r.__setitem__(u"段の順", list(reversed(r[u"段の順"])))))

    def test_f_3_a_record_with_a_sentence_a_value_or_an_element_name_is_red(self):
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"要素名"] = u"jppfs_cor:NetSales"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"文"] = u"売上高は増加した"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"置き場"] = u"S100" + u"ABCD"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        self.assertEqual([], leak_problems(read(RECORD_REL)))
        self.assertFalse(DOCID_RE.search(read(RECORD_REL)))


def ms_rate(n, d):
    return MS.rate(n, d)


class WiringTest(unittest.TestCase):
    def test_g_1_the_script_imports_only_the_allowed_modules(self):
        self.assertEqual([], import_problems())

    def test_g_2_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with open(p, encoding="utf-8") as fh:
            self.assertNotIn(u"tss_retake", fh.read())

    def test_g_3_the_script_has_no_network_key_or_llm(self):
        src = read(SCRIPT_REL)
        for bad in (u"socket", u"urllib", u"ANTHROPIC", u"API_KEY", u"requests"):
            self.assertNotIn(bad, src)

    def test_g_4_the_gate_does_not_use_the_reserved_names_and_has_no_docid(self):
        self.assertEqual([], reserved_problems())
        self.assertIsNone(DOCID_RE.search(read(GATE_REL)))
        self.assertIsNone(DOCID_RE.search(read(SCRIPT_REL)))

    def test_g_5_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("RT_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rel="g.py", base=d))

    def test_g_6_the_script_leaves_sys_modules_as_it_found_them(self):
        u"""前の便の script を読んでも、読み込みの前に居た名前を上書きしたまま残さない(門を 2 通りの順で走らせても赤くならない)。"""
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "tss_retake_script_for_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        self.assertIn("tss_retake_script_for_sysmodules_check", sys.modules)
        del mod


class MutantTest(unittest.TestCase):
    def test_h_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        results = run_mutants()
        after = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        self.assertEqual(before, after)
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))

    def test_h_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in (u"seal", u"input_sha", u"wire_inputs", u"compare", u"orch", u"stage", u"import"):
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
