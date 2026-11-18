# -*- coding: utf-8 -*-
"""封 docs/XBRL_SCOPE_COND_SEAL_2026-11-19.md(SC ― 「文は一部分を言うのに全体の fact に結んだ行」を文の字で止める後付けの規則が、取り違えをどれだけ止め、正しい結びをどれだけ減らすか)の門。封 §6。

**この門が縛るもの**

1. 封の字: 封の commit(5b77133b)・path・手がかりの語の表(§2-3)・事業の形・見出しの決め・段の字・予測 SC-1〜SC-7 が script の定数と同じ。封の file は commit した blob と 1 字も変わっていない。
2. 入力 21 件の sha256 が封の表・script の表・門の表・実物で同じ。入力の確かめは 1 byte 違う複製で止まる。前の便の封・結果の文書は封の commit から 0 行。
3. engine は封の commit から 0 行(``core/``・``adapters/``)。作業木にも engine の未 commit の変更が無い。
4. 順序: 封の commit ⊏ script・この門・記録を足した commit(未 commit は赤)。
5. **止める条件**(封 §2-4): 事業の形・語の表(1 語ずつ)・N のただし書き・見出しの決め(40 字・「。」・数の claim)・最も近い見出しだけ・member が入っていれば止めない・段の包含を、作り物の入力で本物のまま走らせる。
6. **札の引き方**: 同じ state で引けた行だけが分母。引けなかった行は分母に入れず、理由(行が無い・state が違う)別に数える。
7. **つなぐ配線**: ``book_job``(1 本分の job)と ``orchestrate``(集計)を作り物の本で本物のまま走らせ、前後・段・便で非対称な手計算と合わせる。引数を明示で渡さない本番の既定の経路も通す。
8. 記録 ``fixtures/xbrl/scope_cond/stops_2026-11-19.json``: 封の字・script の sha256・入力・指紋・集計が行から数え直せる・予測の判定に要る数が作り直せる・文や値や要素名や主語の語を持たない。
9. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
全数の作り直しは門の中では走らせない(重い)。この file は docID の字を持たない。
"""
import ast
import collections
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import tempfile
import types
import unittest
import sys

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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_sc_seal")       # 順序・履歴の部品。門としては走らせない
MS = load_module("measure/xbrl_scope_cond_2026-11-19.py", "scope_cond_script_for_seal_gate")

SEAL_REL = "docs/XBRL_SCOPE_COND_SEAL_2026-11-19.md"
SEAL_COMMIT_SHORT = "5b77133b"               # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_scope_cond_2026-11-19.py"
GATE_REL = "tests/measure/test_xbrl_scope_cond_seal.py"
RECORD_REL = "fixtures/xbrl/scope_cond/stops_2026-11-19.json"
ORDER_FILES = (SCRIPT_REL, GATE_REL, RECORD_REL)
#: 入力の表(literal。封の表・script の表・実物と照らす)
INPUT_SHAS = (
    ("fixtures/xbrl/kam/read_types_2026-11-15.json", "8c9fe6b8def7430908bf925f697ea5a1b1d634dd754933aab7c71b0a913c964a"),
    ("fixtures/xbrl/kam/population_2026-11-15.json", "86e31ca230850d9a13061a18f647c17dea2b95a76927d2587374978af2aef410"),
    ("fixtures/xbrl/kam/states_2026-11-15.json", "3ba57f55e62a29e20578b87f527de35d9bc3d2310cbba232d9311c9b187103e7"),
    ("fixtures/xbrl/yuho_sections/read_types_2026-11-16.json", "9087a95d0f51e559012b72a9f5f2af7c9575e57589120b50b7ba1d93f46fd3bb"),
    ("fixtures/xbrl/yuho_sections/population_2026-11-16.json", "7264bd201eeff1f2b011e783fe26ae4b9435ca7e3fb0436f148a662ff16a3374"),
    ("fixtures/xbrl/yuho_sections/states_2026-11-16.json", "130498b4781160154210cacd31d35a8498e4d460f7d3ac88968bf21a7aae4ac5"),
    ("fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json", "d1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183"),
    ("fixtures/xbrl/tanshin_self/vm_types_subreading_2026-11-14.json", "d5d336bf3eeda37b36db41c02f8a84142257c22921daeb56b5818b262b3235bb"),
    ("fixtures/xbrl/tanshin_self/population_2026-11-14.json", "48ba8e5574be70d85b3d1affacc9403cffbfc698f529c095c6c882cd8ccfa9b0"),
    ("fixtures/xbrl/tss_retake/retake_2026-11-18.json", "34845f1b3772993aebc0a48d1cec0f6ee5889f9f66843a88f94e572392263cd7"),
    ("fixtures/xbrl/attr_tally/tally_2026-11-17.json", "dbbf45e5cd0363bfbc533b5a832454c325de546b845a292d08d17a58194545b6"),
    ("measure/xbrl_kam_2026-11-15.py", "cc2aab3029ef76d91e73aceae562370d3e74a58f51d90cecfb6153e28259aa4a"),
    ("measure/xbrl_yuho_sections_2026-11-16.py", "23162fa9221aaa7a71e2ab602c46ac92cb473bb85d3fdeef75ba4c2d22373191"),
    ("measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    ("measure/xbrl_plan_source_2026-11-17.py", "0617d75a98e9aca390426b2751bed5ae40a8aa8759b3e80bffab163e1abeb8ea"),
    ("measure/xbrl_attr_tally_2026-11-17.py", "e6f66feaf3027ee425c3d421e97abd6edf49f77f5e9e2e515061afdcb4014346"),
    ("measure/xbrl_tss_retake_2026-11-18.py", "4d1c4276f67f2fd5551ba0372b2a09c07a2ee4c493b09942e3f360ee35e5b82e"),
    ("adapters/xbrl/recipes.py", "346adb0d586e3af233b381f721c3512eea02809c287e02aa948bb0d04031e403"),
    ("adapters/xbrl/instance.py", "1b8c00f86eafe765ce44be9ee93cc9ff7a492bd119074e9aa8f49e13e4970cd8"),
    ("adapters/xbrl/vocabulary.py", "369891933a5876c4a942e59b85b500d7fa2aa826f8b0c95e2b1c905623b3806c"),
    ("adapters/xbrl/extract.py", "a61da3fc3c336e80a214a5fc71978d9ce63f52b4eec5a763e91f434c2ef06d05"))
INPUT_RELS = tuple(rel for rel, _sha in INPUT_SHAS)
#: 前の便の封・結果の文書(封の commit から 0 行)
PRIOR_DOCS = (
    "docs/XBRL_KAM_SEAL_2026-11-15.md", "docs/XBRL_KAM_RESULT_2026-11-15.md", "docs/XBRL_YUHO_SECTIONS_SEAL_2026-11-16.md", "docs/XBRL_YUHO_SECTIONS_RESULT_2026-11-16.md",
    "docs/XBRL_ATTR_TALLY_SEAL_2026-11-17.md", "docs/XBRL_ATTR_TALLY_RESULT_2026-11-17.md", "docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md", "docs/XBRL_TANSHIN_SELF_RESULT_2026-11-14.md",
    "docs/XBRL_PLAN_SOURCE_SEAL_2026-11-17.md", "docs/XBRL_PLAN_SOURCE_RESULT_2026-11-17.md", "docs/XBRL_TSS_RETAKE_SEAL_2026-11-18.md", "docs/XBRL_TSS_RETAKE_RESULT_2026-11-18.md",
    "docs/XBRL_SUMMARY_ENGINE_SEAL_2026-11-18.md", "docs/XBRL_SUMMARY_ENGINE_RESULT_2026-11-18.md")
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "io", "json", "os", "re", "sys", "time")
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
G, VM, UN, PN = STATES
#: 封 §2-3 の手がかりの語の表(literal。封の字・script の表と照らす)
WORD_TABLE = collections.OrderedDict([
    (u"S", (u"セグメント", u"部門", u"分野")), (u"N", (u"単体", u"個別", u"提出会社")), (u"U", (u"うち", u"内訳")),
    (u"R", (u"国内", u"海外", u"日本", u"北米", u"米国", u"欧州", u"アジア", u"中国", u"地域")), (u"K", (u"子会社", u"関連会社"))])
BIZ_AFTER = (u"は", u"では", u"において", u"におきまして", u"につきまして", u"について", u"の売上", u"セグメント", u"部門", u"分野")
BIZ_CLOSE = (u"]", u")", u"】", u"〕", u">", u"》", u"」")
NONCONS_PTR = u"xbrl:jppfs_cor:Assets@CurrentYearInstantNonConsolidatedMember"
CONS_PTR = u"xbrl:jppfs_cor:Assets@CurrentYearInstant_ConsolidatedMember"
K_WIRE = u"配線の確認(封 §2-2。予測ではない。違えば止まる)"
K_ALL = u"結んだ行の全部(封 §2-5 の 1)"
K_LABEL = u"読みの札つきの行(封 §2-5 の 2)"
K_CLASS = u"当たった類ごとの数(封 §2-5 の 3)"
K_PRED = u"予測の判定に要る数(SC-1〜SC-7。当たり・外れは結果の文書で)"
S1, S2, S3 = u"段 1", u"段 2", u"段 3"


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


_REAL = {}


def real_recs():
    u"""本物の入力の記録(大きい。1 度だけ読む)。"""
    if "recs" not in _REAL:
        _REAL["recs"] = MS.load_records(ROOT)
    return _REAL["recs"]


def guard(fn, *a, **k):
    u"""検査を呼ぶ。例外は「問題」として返す(変異した関数が落ちても赤として数える)。"""
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  Stop(SystemExit)を含む
        return [u"例外: %s" % type(exc).__name__]


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("scope_cond_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
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


def seal_words(seal):
    u"""封 §2-3 の表から {類: (語の並び)}(S の「事業の形」は語に数えない)。"""
    out = collections.OrderedDict()
    for m in re.finditer(r"^\| ([SNURK])\([^)]*\) \| (.*) \|$", seal, re.M):
        out[m.group(1)] = tuple(w for w in re.findall(u"「([^」]+)」", m.group(2)) if w != u"事業の形")
    return out


def seal_biz(seal):
    u"""封 §2-3 の「事業の形」の行から ((直後の語), (閉じ括弧))。"""
    line = [ln for ln in seal.splitlines() if ln.startswith(u"- **事業の形**")][0]
    seg = line.split(u"次のどれか ―")[1].split(u"(「事業年度」")[0]
    return tuple(re.findall(u"「([^」]+)」", seg.split(u"・閉じ括弧")[0])), tuple(re.findall(u"`(.)`", seg))


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    for phrase in (u"SC-1", u"SC-2", u"SC-3", u"SC-4a", u"SC-4b", u"SC-5", u"SC-6", u"SC-7", u"fixtures/xbrl/scope_cond/stops_2026-11-19.json", u"measure/xbrl_scope_cond_2026-11-19.py",
                   u"長さが 40 字以下・「。」で終わらない・数の claim を 1 つも持たない文", u"NonConsolidated", u"最も近い見出し", u"profile は 3 便とも `P33E`", u"24531"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    if seal_words(seal) != WORD_TABLE:
        out.append(u"封の手がかりの語の表が門の表と違う")
    if tuple(ms.WORDS.items()) != tuple(WORD_TABLE.items()):
        out.append(u"script の手がかりの語の表が封の表と違う")
    if seal_biz(seal) != (BIZ_AFTER, BIZ_CLOSE):
        out.append(u"封の事業の形が門の表と違う")
    if (ms.BIZ, tuple(ms.BIZ_AFTER), tuple(ms.BIZ_CLOSE)) != (u"事業", BIZ_AFTER, BIZ_CLOSE):
        out.append(u"script の事業の形が封と違う")
    if (ms.HEAD_MAX, ms.HEAD_END, ms.NONCONS, tuple(ms.STAGES), ms.CLASS_ORDER) != (40, u"。", u"NonConsolidated", (1, 2, 3), u"SNURKH"):
        out.append(u"見出しの決め・N のただし書きの字・段・類の順が封と違う")
    if (ms.PROFILE, tuple(ms.STATES)) != (u"P33E", STATES):
        out.append(u"profile か state の名が違う")
    if (ms.K_WIRE, ms.K_ALL, ms.K_LABEL, ms.K_CLASS, ms.K_PRED) != (K_WIRE, K_ALL, K_LABEL, K_CLASS, K_PRED):
        out.append(u"記録の欄の名が門と違う")
    return out


def seal_table_problems(ms=None, seal=None):
    u"""封 §1 の表の (path, sha256) が門・script の表と同じ。"""
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    rows = re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", seal)
    out = []
    if rows != list(INPUT_SHAS):
        out.append(u"封の入力の表が門の表と違う")
    if [(rel, sha) for _no, rel, sha in ms.INPUTS] != list(INPUT_SHAS):
        out.append(u"script の入力の表が門の表と違う")
    return out


def seal_history_problems(root=REPO):
    u"""封の file の履歴は 1 commit(5b77133b)で、今の file はその commit の blob と 1 字も変わらない。"""
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


# ---------------------------------------------------------------- 2. 入力・前の文書
def input_sha_problems(ms=None):
    ms = ms or MS
    out = []
    if [(rel, sha) for _no, rel, sha in ms.INPUTS] != list(INPUT_SHAS):
        out.append(u"script の入力の表が門の表と違う")
    out.extend(u"入力の sha256 が表と違う: %s" % rel for rel, want in INPUT_SHAS if sha_of(rel) != want)
    return out


def input_wire_problems(ms=None):
    u"""``check_inputs`` が、表のとおりの複製では通り、1 byte 違う複製では止まる。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="sc_inputs_")
    try:
        for rel in INPUT_RELS:
            os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
            os.symlink(os.path.join(ROOT, rel), os.path.join(tmp, rel))
        if [r[u"sha256"] for r in ms.check_inputs(tmp)] != [s for _r, s in INPUT_SHAS]:
            out.append(u"表のとおりの複製で check_inputs が表の sha256 を返さない")
        for i in range(len(INPUT_RELS)):
            p = os.path.join(tmp, INPUT_RELS[i])
            os.unlink(p)
            with open(os.path.join(ROOT, INPUT_RELS[i]), "rb") as fh:
                data = fh.read()
            with open(p, "wb") as fh:
                fh.write(data + b" ")
            if stops(ms, ms.check_inputs, tmp) is not True:
                out.append(u"入力 %d が 1 byte 違うのに止まらない" % (i + 1))
            os.unlink(p)
            os.symlink(os.path.join(ROOT, INPUT_RELS[i]), p)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def prior_docs_problems(root=REPO):
    s = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(s) != 1:
        return [u"封の commit が履歴に 1 つで決まらない"]
    rc, txt = PR.git_in(root, "diff", "--name-only", s[0], "HEAD", "--", *[PREFIX + d for d in PRIOR_DOCS])
    if rc != 0:
        return [u"git diff が失敗した"]
    return [u"前の便の文書が封の後に変わっている: %s" % ln for ln in txt.splitlines() if ln.strip()]


# ---------------------------------------------------------------- 3. engine は 0 行・順序
def engine_zero_problems(root=REPO, seal_rel=SEAL_REL, prefix=PREFIX):
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


# ---------------------------------------------------------------- 4. 規則(封 §2-3・§2-4)
def rule_problems(ms=None):
    u"""事業の形・語の表(1 語ずつ)・N のただし書き。"""
    ms = ms or MS
    out = []
    # 事業の形: 当たる形
    for after in BIZ_AFTER:
        if not ms.has_biz_form(u"海外事業" + after + u"は好調"):
            out.append(u"事業の直後が「%s」の字が事業の形に当たらない" % after)
    for ch in BIZ_CLOSE:
        if not ms.has_biz_form(u"[A事業" + ch + u"好調"):
            out.append(u"事業の直後が閉じ括弧「%s」の字が事業の形に当たらない" % ch)
    if not ms.has_biz_form(u"A事業") or not ms.has_biz_form(u"事業"):
        out.append(u"字の終わりの「事業」が事業の形に当たらない")
    if not ms.has_biz_form(u"事業年度の事業は好調"):
        out.append(u"1 つ目が当たらなくても 2 つ目の「事業」を見ない")
    # 当たらない形
    for bad in (u"事業年度", u"事業環境", u"事業の拡大", u"事業を", u"事業と", u"事業部は", u"事業 は", u"事 業は", u"業事は", u"事業年度に事業環境"):
        if ms.has_biz_form(bad):
            out.append(u"事業の形でない字が当たる: %s" % bad)
    # 語の表: 1 語ずつ・その類だけ
    for cls, words in WORD_TABLE.items():
        for w in words:
            got = [c for c in u"SNURK" if ms.has_class(u"前" + w + u"後", c)]
            if got != [cls]:
                out.append(u"語「%s」が類 %s だけに当たらない: %s" % (w, cls, got))
    if ms.has_class(u"売上高は増加した", u"S") or ms.has_class(u"売上高は増加した", u"R"):
        out.append(u"語の無い字が当たる")
    if not ms.has_class(u"A事業は", u"S") or ms.has_class(u"A事業は", u"N") or ms.has_class(u"A事業年度", u"S"):
        out.append(u"S が事業の形を数えない(または事業年度を数える)")
    if ms.has_class(u"A事業は", u"R"):
        out.append(u"事業の形が S 以外の類に当たる")
    # N のただし書き
    if ms.snu_hits(u"単体の売上", []) != [u"N"]:
        out.append(u"N の語だけの当たりが pointer 無しで当たらない")
    if ms.snu_hits(u"単体の売上", [NONCONS_PTR]) != []:
        out.append(u"N の語だけの当たりが NonConsolidated の pointer が在っても止める")
    if ms.snu_hits(u"単体の売上", [CONS_PTR]) != [u"N"]:
        out.append(u"NonConsolidated の字を含まない pointer(連結)で N のただし書きが働く")
    if ms.snu_hits(u"単体の売上", [u"p", NONCONS_PTR]) != []:
        out.append(u"pointer の 2 つ目に NonConsolidated が在るのにただし書きが働かない(どれにも無いときだけ止める)")
    if ms.snu_hits(u"単体のうち", [NONCONS_PTR]) != [u"N", u"U"]:
        out.append(u"N と U に当たる字がただし書きで捨てられる(N の語だけの当たりだけ)")
    if sorted(ms.snu_hits(u"単体のセグメント", [NONCONS_PTR])) != [u"N", u"S"]:
        out.append(u"N と S に当たる字がただし書きで捨てられる")
    if ms.snu_hits(u"セグメント", [NONCONS_PTR]) != [u"S"] or ms.snu_hits(u"内訳", [NONCONS_PTR]) != [u"U"]:
        out.append(u"S・U の当たりが NonConsolidated の pointer で捨てられる")
    if ms.snu_hits(u"国内", []) != [] or ms.snu_hits(u"子会社", []) != []:
        out.append(u"snu_hits が R・K を数える(S・N・U だけ)")
    if ms.snu_hits(u"単体の売上", [None, 5]) != [u"N"]:
        out.append(u"字でない pointer でただし書きが働く・落ちる")
    return out


def stage_problems(ms=None):
    u"""段の包含・前の字と文の全部・見出しは最も近い 1 つ・R と K は前の字だけ。(hits は段 1・2・3 の字)"""
    ms = ms or MS
    out = []

    def sh(prefix, whole, heading=None, ptr=()):
        return ms.stage_hits(prefix, whole, heading, list(ptr))
    cases = [
        ((u"売上高は", u"売上高は100円", None), (u"", u"", u"")),
        ((u"国内の売上高は", u"国内の売上高は100円", None), (u"", u"", u"R")),
        ((u"売上高は", u"売上高は100円で、うち海外は5円", None), (u"", u"", u"U")),                         # R は文の全部では見ない・U は見る
        ((u"売上高は", u"売上高は100円(セグメント)", None), (u"", u"", u"S")),                              # 前の字に無く文の全部に在る S は段 3 だけ
        ((u"売上高は", u"売上高は100円", u"(3)ヘルスケア等セグメント"), (u"", u"H", u"H")),
        ((u"売上高は", u"売上高は100円", u"(4)その他"), (u"", u"", u"")),
        ((u"売上高は", u"売上高は100円", u"A事業は"), (u"", u"H", u"H")),                                    # 見出しの S は事業の形も数える
        ((u"セグメントの売上高は", u"セグメントの売上高は100円", u"セグメント別"), (u"S", u"SH", u"SH")),
        ((u"子会社の売上高は", u"子会社の売上高は100円", None), (u"", u"", u"K")),
        ((u"うち国内は", u"うち国内は100円", None), (u"U", u"U", u"UR")),
        ((u"関連会社と海外の", u"関連会社と海外の100円", u"全体"), (u"", u"", u"RK")),
        ((u"内訳は", u"内訳は100円で、単体の", None), (u"U", u"U", u"NU")),
    ]
    for (args, want) in cases:
        got = sh(*args)
        if got != want:
            out.append(u"stage_hits が手計算と違う: %s → %s(手計算 %s)" % (args[0], got, want))
    # N のただし書きは前の字と文の全部で別々に
    if sh(u"単体の売上は", u"単体の売上は100円", None, [NONCONS_PTR]) != (u"", u"", u""):
        out.append(u"N の語だけの行が NonConsolidated の pointer で止まる")
    if sh(u"単体の売上は", u"単体の売上は100円", None, [CONS_PTR]) != (u"N", u"N", u"N"):
        out.append(u"N の語だけの行が連結の pointer で止まらない")
    if sh(u"単体の売上は", u"単体の売上は100円", u"全体セグメント", [NONCONS_PTR]) != (u"", u"H", u"H"):
        out.append(u"N のただし書きで落ちた行が見出しの S で止まらない")
    if sh(u"単体の売上は", u"単体の売上は100円でうちの", None, [NONCONS_PTR]) != (u"", u"", u"NU"):
        out.append(u"N のただし書きで落ちた前の字の後ろの U(文の全部)が段 3 で止めない(N の語だけの当たりでない行は N も数える)")
    if sh(u"単体の売上は", u"単体の売上は100円で単体", None, [NONCONS_PTR]) != (u"", u"", u""):
        out.append(u"文の全部の N の語だけの当たりが NonConsolidated の pointer で止まる")
    # 段の包含: どの組でも h1 ⊆ h2 ⊆ h3
    for (args, _w) in cases:
        a, b, c = sh(*args)
        if not (set(a) <= set(b) <= set(c)):
            out.append(u"段の包含が成り立たない: %s" % ((a, b, c),))
    return out


def hh(ms, sentences, specs):
    u"""作り物の [(raw, verify)] と文の列から unit_digest。specs = [(文の番号, 数の字, state, member, pointer の列)]。"""
    pairs = []
    for si, token, state, member, ptr in specs:
        s = sentences[si]
        pos = s.index(token)
        pairs.append(({u"sentence": si, u"pos": pos, u"span": s[max(0, pos - 30):pos + len(token) + 10], u"member": member},
                      {u"state": state, u"pointers": list(ptr)}))
    return ms.unit_digest(pairs, sentences), pairs


def pos_of(sentences, si, token):
    return sentences[si].index(token)


def digest_problems(ms=None):
    u"""見出し・最も近い見出し・member・N のただし書き・位置の確かめを unit_digest で。"""
    ms = ms or MS
    out = []
    sent = [u"経営成績の概況", u"売上高は100円となりました。", u"セグメント別の概況", u"売上高は200円でした。", u"その他", u"売上高は300円でした。",
            u"その他の事業は400円で、うち海外は50円。", u"単体の売上高は60円でした。", u"単体の売上高は70円でした。"]
    specs = [(1, u"100", G, u"", []), (3, u"200", VM, u"", []), (5, u"300", G, u"", []), (6, u"400", G, u"", []), (6, u"50", VM, u"", [NONCONS_PTR]),
             (7, u"60", VM, u"", [NONCONS_PTR]), (8, u"70", G, u"", [CONS_PTR])]
    d, pairs = hh(ms, sent, specs)
    rows = dict(((r[0], r[1]), r[2:]) for r in d[u"rows"])
    pos = lambda si, tok: pos_of(sent, si, tok)
    # 見出し: 0・2・4(数の claim を持たない 40 字以下で「。」で終わらない文)。1・3・5・6・7・8 は数の claim を持つか「。」で終わる
    heads = ms.heading_indices(sent, set(r[u"sentence"] for r, _c in pairs))
    if heads != [0, 2, 4]:
        out.append(u"見出しが(0・2・4)でない: %s" % (heads,))
    want = {
        (1, pos(1, u"100")): [u"G", True, u"", u"", u""],                                      # 前の字「売上高は」・最も近い見出し 0(S なし)
        (3, pos(3, u"200")): [u"V", True, u"", u"H", u"H"],                                    # 最も近い見出し 2(S あり)
        (5, pos(5, u"300")): [u"G", True, u"", u"", u""],                                      # 最も近い見出し 4(S なし)。2 の S は見ない
        (6, pos(6, u"400")): [u"G", True, u"S", u"S", u"SU"],                                  # 前の字「その他の事業は」→ S。最も近い見出し 4(S なし)。文の全部に U
        (6, pos(6, u"50")): [u"V", True, u"SU", u"SU", u"SUR"],
        (7, pos(7, u"60")): [u"V", True, u"", u"", u""],                                       # N だけ + NonConsolidated → 止めない
        (8, pos(8, u"70")): [u"G", True, u"N", u"N", u"N"],                                    # N だけ + 連結の pointer → 止める
    }
    for k, v in want.items():
        if rows.get(k) != v:
            out.append(u"unit_digest の行 %s が手計算と違う: %s(手計算 %s)" % (k, rows.get(k), v))
    if len(d[u"rows"]) != 7 or [(r[0], r[1]) for r in d[u"rows"]] != sorted((r[0], r[1]) for r in d[u"rows"]):
        out.append(u"unit_digest の行が結んだ行 7 つ・(文の番号, 位置)の順でない")
    # 結んだ行でない state は行に入らない・triples には入る
    d2, _p = hh(ms, sent, [(1, u"100", UN, u"", []), (3, u"200", PN, u"", []), (5, u"300", G, u"", [])])
    if len(d2[u"rows"]) != 1 or [t[2] for t in d2[u"triples"]] != [UN, PN, G]:
        out.append(u"結んだ行でない state が行に入る・triples に入らない")
    # member が入っている行はどの段でも止めない(同じ文・同じ前の字で member が空の行は止める)
    sent2 = [u"その他の事業は500円で、うち海外は5円。"]
    d3, _p = hh(ms, sent2, [(0, u"500", G, u"", []), (0, u"5円", G, u"jpcrp:XMember", [])])
    if [(r[3], r[4], r[5], r[6]) for r in d3[u"rows"]] != [(True, u"S", u"S", u"SU"), (False, u"", u"", u"")]:
        out.append(u"member が入っている行が止まる(または空の行が止まらない): %s" % ([(r[3], r[4], r[5], r[6]) for r in d3[u"rows"]],))
    # 見出しの長さ: 40 字は見出し・41 字は見出しでない・「。」で終わる文は見出しでない・数の claim を持つ文は見出しでない
    h40 = u"セ" * 36 + u"グメント"
    h41 = u"セ" * 37 + u"グメント"
    if len(h40) != 40 or len(h41) != 41:
        out.append(u"試験の字の長さが 40・41 でない")
    sent3 = [h40, u"売上高は9円", h41, u"売上高は8円", u"セグメント。", u"売上高は7円", u"セグメント別", u"売上高は6円"]
    heads3 = ms.heading_indices(sent3, {1, 3, 5, 7})
    if heads3 != [0, 6]:
        out.append(u"見出しの決め(40 字は見出し・41 字は見出しでない・「。」で終わる文と数の claim を持つ文は見出しでない)が手計算(0・6)と違う: %s" % (heads3,))
    d4, _p = hh(ms, sent3, [(1, u"9", G, u"", []), (3, u"8", G, u"", []), (5, u"7", G, u"", []), (7, u"6", G, u"", [])])
    got4 = dict(((r[0]), (r[4], r[5], r[6])) for r in d4[u"rows"])
    if got4 != {1: (u"", u"H", u"H"), 3: (u"", u"H", u"H"), 5: (u"", u"H", u"H"), 7: (u"", u"H", u"H")}:
        out.append(u"見出しの決めが行の段 2 に効いていない: %s" % (got4,))
    # 最も近い見出しだけ(間に別の見出しが在れば近いほうだけ)・見出しが無ければ当たらない
    if ms.nearest_heading([0, 2, 4], 5) != 4 or ms.nearest_heading([0, 2, 4], 4) != 2 or ms.nearest_heading([0, 2, 4], 0) is not None or ms.nearest_heading([3, 9], 2) is not None:
        out.append(u"nearest_heading が「その文より前で最も近い見出し」でない")
    if ms.nearest_heading([1, 3], 9) != 3 or ms.nearest_heading([1, 3], 3) != 1:
        out.append(u"nearest_heading が文の番号と同じ見出しや先の見出しを数える・最も近いものを選ばない")
    # 位置の確かめ
    if stops(ms, ms.unit_digest, [({u"sentence": 0, u"pos": 1, u"span": None}, {u"state": G, u"pointers": []})], [u"売上高は100円"]) is not True:
        out.append(u"位置が数の字で始まらない行が止まらない")
    if stops(ms, ms.unit_digest, [({u"sentence": 0, u"pos": 4, u"span": u"売上高は101円"}, {u"state": G, u"pointers": []})], [u"売上高は100円"]) is not True:
        out.append(u"span が位置の前後と合わない行が止まらない")
    if stops(ms, ms.unit_digest, [({u"sentence": 3, u"pos": 0, u"span": None}, {u"state": G, u"pointers": []})], [u"1"]) is not True:
        out.append(u"文の番号が文の列の外の行が止まらない")
    if stops(ms, ms.unit_digest, [({u"sentence": 0, u"pos": 99, u"span": None}, {u"state": G, u"pointers": []})], [u"売上高は100円"]) is not True:
        out.append(u"位置が文の外の行が止まらない")
    s5 = u"利益は 1,060百万円"
    p5 = s5.index(u" ")
    d5 = ms.unit_digest([({u"sentence": 0, u"pos": p5, u"span": s5, u"member": u""}, {u"state": G, u"pointers": []})], [s5])
    if d5[u"counts"].get(u"位置: 符号か空白から") != 1 or d5[u"rows"][0][4:] != [u"", u"", u""]:
        out.append(u"数の字の手前の空白から始まる位置が通らない(engine の数の読みは空白を数の一部に読む)")
    s6 = u"利益は△100円"
    d6 = ms.unit_digest([({u"sentence": 0, u"pos": s6.index(u"△"), u"span": s6, u"member": u""}, {u"state": G, u"pointers": []})], [s6])
    if d6[u"counts"].get(u"位置: 符号か空白から") != 1:
        out.append(u"符号から始まる位置が通らない")
    # 前の字は位置の手前まで(数の後ろの字は前の字に入らない)
    d7, _p = hh(ms, [u"売上高は100円で、セグメントは5円"], [(0, u"100", G, u"", [])])
    if d7[u"rows"][0][4:] != [u"", u"", u"S"]:
        out.append(u"前の字が位置の手前まででない(数の後ろの S が段 1 に入る)")
    # 前の字の終わりが「事業」の数
    s8 = u"A事業 100円"
    d8 = ms.unit_digest([({u"sentence": 0, u"pos": s8.index(u" "), u"span": s8, u"member": u""}, {u"state": G, u"pointers": []})], [s8])
    if d8[u"counts"].get(u"前の字の終わりが「事業」") != 1:
        out.append(u"前の字の終わりが「事業」の数が数えられない")
    d9, _p = hh(ms, [u"子会社の費用は5円。"], [(0, u"5", G, u"", [])])
    if d9[u"rows"][0][4:] != [u"", u"", u"K"]:
        out.append(u"K の語(子会社)が前の字に在るのに段 3 だけに入らない")
    long_s = u"あ" * 35 + u"売上高は700円となりました。"
    d10, _p = hh(ms, [long_s], [(0, u"700", G, u"", [])])
    if len(d10[u"rows"]) != 1 or d10[u"counts"].get(u"位置: 数字から") != 1:
        out.append(u"位置が 30 字より後ろの行の span の確かめが通らない(span は位置の 30 字前から)")
    if ms.empty_digest()[u"cut"] is not False:
        out.append(u"切れない単位の結果が切れたになっている")
    return out


# ---------------------------------------------------------------- 5. 札の引き方(封 §2-5 の 2)
def label_problems(ms=None):
    u"""札の読みの検査(本物の読みの記録)・TSS の細目・同じ state で引けた行だけ・引けなかった理由。"""
    ms = ms or MS
    out = []
    recs = real_recs()
    labels = ms.build_labels(recs)
    cnt = collections.Counter((lab[u"便"], lab[u"state"]) for lab in labels)
    if len(labels) != 133 + 169 + 120 or sum(v for (b, _s), v in cnt.items() if b == u"KAM") != 133 or sum(v for (b, _s), v in cnt.items() if b == u"YS") != 169 \
            or sum(v for (b, _s), v in cnt.items() if b == u"TSS") != 120 or cnt.get((u"TSS", u"G"), 0) != 0:
        out.append(u"札つきの行の数が(KAM 133・YS 169・TSS 120・TSS の G は 0)でない: %s" % (dict(cnt),))
    # 札の鍵: 読みの組 → 文の種類か節・state(KAM の最初の V 連結の行・YS の最初の G 配当の行・TSS の最初の行)
    kam_rows = recs[u"kam_read"][u"行"]
    first_vc = [r for r in kam_rows if r[0] == u"V 連結"][0]
    first_gn = [r for r in kam_rows if r[0] == u"G 単体"][0]
    got = [lab for lab in labels if lab[u"便"] == u"KAM" and lab[u"#"] == first_vc[1] and lab[u"si"] == first_vc[2] and lab[u"pos"] == first_vc[3]]
    if len(got) != 1 or got[0][u"側"] != u"連結" or got[0][u"state"] != u"V" or got[0][u"型"] != first_vc[4]:
        out.append(u"KAM の V 連結の札が(連結・V)に写っていない")
    got = [lab for lab in labels if lab[u"便"] == u"KAM" and lab[u"#"] == first_gn[1] and lab[u"si"] == first_gn[2] and lab[u"pos"] == first_gn[3]]
    if len(got) != 1 or got[0][u"側"] != u"単体" or got[0][u"state"] != u"G":
        out.append(u"KAM の G 単体の札が(単体・G)に写っていない")
    ys_rows = recs[u"ys_read"][u"行"]
    first_gd = [r for r in ys_rows if r[0] == u"G 配当"][0]
    got = [lab for lab in labels if lab[u"便"] == u"YS" and lab[u"#"] == first_gd[1] and lab[u"si"] == first_gd[2] and lab[u"pos"] == first_gd[3]]
    if len(got) != 1 or got[0][u"側"] != u"配当政策" or got[0][u"state"] != u"G":
        out.append(u"YS の G 配当の札が(配当政策・G)に写っていない")
    # 範囲の札の数(前の記録: KAM 25・YS 4・TSS 76)・G の a(KAM 89・YS 125)
    rng = collections.Counter(lab[u"便"] for lab in labels if lab[u"state"] == u"V" and ms.is_range(lab))
    if dict(rng) != {u"KAM": 25, u"YS": 4, u"TSS": 76}:
        out.append(u"範囲の札の V の行が(KAM 25・YS 4・TSS 76)でない: %s" % (dict(rng),))
    ga = collections.Counter(lab[u"便"] for lab in labels if lab[u"state"] == u"G" and lab[u"型"] == u"a")
    if dict(ga) != {u"KAM": 89, u"YS": 125}:
        out.append(u"札 a の G の行が(KAM 89・YS 125)でない: %s" % (dict(ga),))
    # TSS の細目: ケ は細目によらず ケ・細目を持つ型は細目の字・他は型の字
    if (ms.tss_key(u"ケ", u"ケ1"), ms.tss_key(u"カ", u"カ3"), ms.tss_key(u"イ", u"イ2"), ms.tss_key(u"ア", None), ms.tss_key(u"ク", None)) != (u"ケ", u"カ3", u"イ2", u"ア", u"ク"):
        out.append(u"TSS の型・細目の字の写しが違う")
    if stops(ms, ms.tss_key, u"カ", None) is not True:
        out.append(u"細目を持つはずの型に細目が無いのに止まらない")
    at = ms.AT
    for key, want in ((u"ア", (u"内", u"範囲")), (u"カ3", (u"内", u"単位")), (u"カ1", (u"外", u"数の読み取り")), (u"ク", (u"除く", u""))):
        if at.table_lookup(u"TSS")[key] != want:
            out.append(u"便 AT の写しの表の TSS の %s が(%s)でない" % (key, want))
    return out


def lab_rows():
    u"""札つきの行(作り物)。"""
    ms = MS
    lk = lambda b: ms.AT.table_lookup(b)
    L = lambda batch, n, side, si, pos, state, key, diff=None: ms.label_row(batch, n, side, si, pos, state, key, diff, lk(batch))
    K, Y, T = u"KAM", u"YS", u"TSS"
    return od_list([
        L(K, 1, u"連結", 1, 10, u"V", u"ア"), L(K, 1, u"連結", 2, 10, u"V", u"ア"), L(K, 2, u"連結", 1, 5, u"V", u"ア"), L(K, 3, u"連結", 1, 1, u"V", u"ウ"),
        L(K, 1, u"連結", 3, 10, u"V", u"エ"), L(K, 1, u"連結", 4, 10, u"V", u"ク"), L(K, 1, u"連結", 5, 10, u"V", u"イ"),
        L(Y, 5, u"研究開発活動", 1, 2, u"V", u"ア"), L(Y, 5, u"研究開発活動", 2, 2, u"V", u"オ"),
        L(T, 7, None, 1, 1, u"V", u"ア"), L(T, 7, None, 2, 2, u"V", u"ア"), L(T, 7, None, 3, 3, u"V", u"カ1"),
        L(K, 1, u"連結", 10, 1, u"G", u"a"), L(K, 1, u"連結", 11, 1, u"G", u"a"), L(K, 1, u"連結", 14, 1, u"G", u"a"),
        L(K, 1, u"連結", 12, 1, u"G", u"b", u"範囲"), L(K, 1, u"連結", 13, 1, u"G", u"b", u"側"), L(K, 1, u"連結", 15, 1, u"G", u"b", u"項目"), L(K, 1, u"連結", 16, 1, u"G", u"c"),
        L(Y, 5, u"配当政策", 1, 1, u"G", u"a"), L(Y, 5, u"配当政策", 2, 1, u"G", u"b", u"範囲")])


def od_list(xs):
    return list(xs)


def R(batch, n, side, si, pos, state, empty, h1, h2, h3):
    return [batch, n, side, si, pos, state, empty, h1, h2, h3]


def hand_rows():
    u"""札つきの行・札なしの行を持つ、手計算の作り物の結んだ行(便・state・段で非対称)。"""
    K, Y, T = u"KAM", u"YS", u"TSS"
    return [
        R(K, 1, u"連結", 1, 10, u"V", True, u"S", u"S", u"S"), R(K, 1, u"連結", 2, 10, u"V", True, u"", u"H", u"H"), R(K, 2, u"連結", 1, 5, u"G", True, u"S", u"S", u"S"),
        R(K, 1, u"連結", 3, 10, u"V", True, u"", u"", u"R"), R(K, 1, u"連結", 4, 10, u"V", True, u"S", u"S", u"S"), R(K, 1, u"連結", 5, 10, u"V", False, u"", u"", u""),
        R(K, 1, u"連結", 10, 1, u"G", True, u"S", u"S", u"S"), R(K, 1, u"連結", 11, 1, u"G", True, u"", u"", u"R"), R(K, 1, u"連結", 14, 1, u"G", False, u"", u"", u""),
        R(K, 1, u"連結", 12, 1, u"G", True, u"", u"H", u"H"), R(K, 1, u"連結", 13, 1, u"G", True, u"S", u"S", u"S"), R(K, 1, u"連結", 15, 1, u"G", True, u"", u"", u""),
        R(K, 1, u"連結", 16, 1, u"G", True, u"U", u"U", u"U"),
        R(Y, 5, u"研究開発活動", 1, 2, u"V", True, u"", u"", u"K"), R(Y, 5, u"研究開発活動", 2, 2, u"V", True, u"U", u"U", u"U"),
        R(Y, 5, u"配当政策", 1, 1, u"G", True, u"", u"", u"K"), R(Y, 5, u"配当政策", 2, 1, u"G", True, u"", u"", u"SU"),
        R(T, 7, None, 1, 1, u"V", True, u"N", u"N", u"N"), R(T, 7, None, 2, 2, u"V", True, u"", u"", u""), R(T, 7, None, 3, 3, u"V", True, u"S", u"S", u"S"),
        R(T, 7, None, 10, 1, u"G", True, u"S", u"S", u"S"), R(T, 7, None, 11, 1, u"G", True, u"", u"H", u"H"), R(T, 7, None, 12, 1, u"G", True, u"", u"", u"R"),
        R(T, 7, None, 13, 1, u"G", True, u"", u"", u""), R(T, 7, None, 14, 1, u"G", False, u"", u"", u"")]


def fr_of(n, d):
    return MS.rate(n, d)


def tally_problems(ms=None):
    u"""引けた行だけが分母・属性ごと・範囲 / 範囲でない / 除く・G の a・b・c と違うもの・全体の便ごと・類ごとの数・予測の数を、手計算の作り物で。"""
    ms = ms or MS
    out = []
    labels = lab_rows()
    rows = hand_rows()
    idx = ms.index_rows(rows)
    # --- match: 同じ state で引けた行だけ
    m = ms.match(labels, idx)
    got = [(x[1] is not None, x[2]) for x in m[:7]]
    if got != [(True, None), (True, None), (False, u"state が違う"), (False, u"行が無い"), (True, None), (True, None), (True, None)]:
        out.append(u"match の引けた・引けなかった理由が手計算と違う: %s" % (got,))
    # --- V の札
    vms, gms = ms.split_labels(labels, idx)
    if [len(vms[b]) for b in (u"TSS", u"KAM", u"YS")] != [3, 7, 2] or [len(gms[b]) for b in (u"KAM", u"YS")] != [7, 2]:
        out.append(u"split_labels の便ごとの札の数が(V: TSS 3・KAM 7・YS 2 / G: KAM 7・YS 2)でない")
    vt = ms.v_tally(vms)
    k = vt[u"KAM"]
    c = k[u"全体"]
    if (c[u"札の行"], c[u"引けた行(分母)"], c[u"引けなかった行"], dict(c[u"引けなかった理由"]), dict(c[u"止めた行"])) != (7, 5, 2, {u"行が無い": 1, u"state が違う": 1}, {S1: 2, S2: 3, S3: 4}):
        out.append(u"V の札 KAM の全体の数が手計算(7・5・2・理由 1+1・止めた 2/3/4)と違う: %s" % (dict(c),))
    r = k[u"範囲"]
    if (r[u"札の行"], r[u"引けた行(分母)"], dict(r[u"止めた行"])) != (4, 2, {S1: 1, S2: 2, S3: 2}):
        out.append(u"V の札 KAM の範囲の数が手計算(4・2・止めた 1/2/2)と違う: %s" % (dict(r),))
    n = k[u"範囲でない(分母から除く札は除く)"]
    if (n[u"札の行"], n[u"引けた行(分母)"], dict(n[u"止めた行"])) != (2, 2, {S1: 0, S2: 0, S3: 1}):
        out.append(u"V の札 KAM の範囲でないの数が手計算(2・2・止めた 0/0/1)と違う: %s" % (dict(n),))
    d = k[u"分母から除く札"]
    if (d[u"札の行"], d[u"引けた行(分母)"], dict(d[u"止めた行"])) != (1, 1, {S1: 1, S2: 1, S3: 1}):
        out.append(u"V の札 KAM の分母から除く札の数が手計算と違う")
    a = k[u"属性ごと"]
    if dict(a[u"期"][u"止めた行"]) != {S1: 0, S2: 0, S3: 1} or a[u"範囲"][u"引けた行(分母)"] != 2 or a[u"外(見積り・計画)"][u"引けた行(分母)"] != 1 or dict(a[u"外(見積り・計画)"][u"止めた行"]) != {S1: 0, S2: 0, S3: 0}:
        out.append(u"V の札 KAM の属性ごとの数が手計算と違う")
    if a[u"1 株あたり"][u"札の行"] != 0:
        out.append(u"1 株あたりの札の行が 0 でない(作りで 0)")
    if vt[u"YS"][u"範囲"][u"引けた行(分母)"] != 1 or dict(vt[u"YS"][u"範囲でない(分母から除く札は除く)"][u"止めた行"]) != {S1: 1, S2: 1, S3: 1}:
        out.append(u"V の札 YS の数が手計算と違う")
    if dict(vt[u"TSS"][u"範囲"][u"止めた行"]) != {S1: 1, S2: 1, S3: 1} or vt[u"TSS"][u"範囲"][u"引けた行(分母)"] != 2 or vt[u"TSS"][u"属性ごと"][u"外(数の読み取り)"][u"引けた行(分母)"] != 1:
        out.append(u"V の札 TSS の数が手計算と違う")
    t = vt[u"合計"]
    if (t[u"範囲"][u"引けた行(分母)"], dict(t[u"範囲"][u"止めた行"])) != (5, {S1: 2, S2: 3, S3: 4}) or (t[u"範囲でない(分母から除く札は除く)"][u"引けた行(分母)"], dict(t[u"範囲でない(分母から除く札は除く)"][u"止めた行"])) != (4, {S1: 2, S2: 2, S3: 3}):
        out.append(u"V の札の合計の範囲・範囲でないが手計算(範囲 5 / 2・3・4、範囲でない 4 / 2・2・3)と違う: %s" % (dict(t[u"範囲"][u"止めた行"]),))
    # --- G の札
    gt = ms.g_tally(gms)
    kk = gt[u"KAM"]
    if dict(kk[u"型ごと"][u"a"][u"止めた行"]) != {S1: 1, S2: 1, S3: 2} or kk[u"型ごと"][u"a"][u"引けた行(分母)"] != 3 or kk[u"型ごと"][u"b"][u"引けた行(分母)"] != 3 or kk[u"型ごと"][u"c"][u"引けた行(分母)"] != 1:
        out.append(u"G の札 KAM の型ごとの数が手計算と違う: %s" % (dict(kk[u"型ごと"][u"a"][u"止めた行"]),))
    if dict(kk[u"型ごと"][u"c"][u"止めた行"]) != {S1: 1, S2: 1, S3: 1}:
        out.append(u"G の札 KAM の c の止めた行が手計算と違う")
    dv = kk[u"b の違うものごと"]
    if (dv[u"範囲"][u"引けた行(分母)"], dict(dv[u"範囲"][u"止めた行"]), dict(dv[u"側"][u"止めた行"]), dv[u"項目"][u"引けた行(分母)"], dict(dv[u"項目"][u"止めた行"]), dv[u"期"][u"札の行"]) \
            != (1, {S1: 0, S2: 1, S3: 1}, {S1: 1, S2: 1, S3: 1}, 1, {S1: 0, S2: 0, S3: 0}, 0):
        out.append(u"G の札 KAM の b の違うものごとの数が手計算と違う")
    if dict(kk[u"b の違うものが範囲(字のとおり)"][u"止めた行"]) != {S1: 0, S2: 1, S3: 1} or dict(kk[u"b の違うものが範囲か側(便 AT の写し)"][u"止めた行"]) != {S1: 1, S2: 2, S3: 2} \
            or kk[u"b の違うものが範囲か側(便 AT の写し)"][u"引けた行(分母)"] != 2:
        out.append(u"G の札 KAM の b の範囲(字のとおり)と範囲か側の数が手計算と違う")
    tg = gt[u"合計"]
    if (tg[u"型ごと"][u"a"][u"引けた行(分母)"], dict(tg[u"型ごと"][u"a"][u"止めた行"])) != (4, {S1: 1, S2: 1, S3: 3}) or dict(tg[u"b の違うものが範囲(字のとおり)"][u"止めた行"]) != {S1: 0, S2: 1, S3: 2}:
        out.append(u"G の札の合計が手計算(a 4 / 1・1・3、b 範囲 0・1・2)と違う")
    # --- 結んだ行の全部
    ta = ms.tally_all(rows)
    kv = ta[u"KAM"][u"全体"][u"V"]
    if (kv[u"結んだ行"], kv[u"member が空の行"], dict(kv[u"止めた行"])) != (5, 4, {S1: 2, S2: 3, S3: 4}):
        out.append(u"結んだ行 KAM の V が手計算(5・4・2/3/4)と違う: %s" % (dict(kv),))
    kg = ta[u"KAM"][u"全体"][u"G"]
    if (kg[u"結んだ行"], kg[u"member が空の行"], dict(kg[u"止めた行"])) != (8, 7, {S1: 4, S2: 5, S3: 6}):
        out.append(u"結んだ行 KAM の G が手計算(8・member が空 7・止めた 4/5/6)と違う: %s" % (dict(kg),))
    if dict(ta[u"KAM"][u"文の種類別"][u"連結"][u"V"][u"止めた行"]) != {S1: 2, S2: 3, S3: 4} or ta[u"KAM"][u"文の種類別"][u"単体"][u"V"][u"結んだ行"] != 0:
        out.append(u"結んだ行 KAM の文の種類別が(連結に全部・単体に 0)でない")
    if ta[u"YS"][u"節別"][u"研究開発活動"][u"V"][u"結んだ行"] != 2 or ta[u"YS"][u"節別"][u"配当政策"][u"G"][u"結んだ行"] != 2 or ta[u"YS"][u"節別"][u"設備投資等の概要"][u"V"][u"結んだ行"] != 0:
        out.append(u"結んだ行 YS の節別が手計算と違う")
    tv, tgg = ta[u"TSS"][u"全体"][u"V"], ta[u"TSS"][u"全体"][u"G"]
    if (tv[u"結んだ行"], dict(tv[u"止めた行"]), tgg[u"結んだ行"], tgg[u"member が空の行"], dict(tgg[u"止めた行"])) != (3, {S1: 2, S2: 2, S3: 2}, 5, 4, {S1: 1, S2: 2, S3: 3}):
        out.append(u"結んだ行 TSS が手計算と違う")
    if u"文の種類別" in ta[u"TSS"] or u"節別" in ta[u"TSS"]:
        out.append(u"TSS に文の種類別・節別が在る")
    # --- 当たった類
    tc = ms.tally_class(rows)
    g3 = tc[u"合計"][S3][u"G"]
    if dict(g3) != {u"止めた行": 11, u"S": 5, u"N": 0, u"U": 2, u"R": 2, u"K": 1, u"H": 2}:
        out.append(u"当たった類 合計・段 3・G が手計算と違う: %s" % (dict(g3),))
    g1 = tc[u"合計"][S1][u"G"]
    g2 = tc[u"合計"][S2][u"G"]
    if dict(g1) != {u"止めた行": 5, u"S": 4, u"N": 0, u"U": 1, u"R": 0, u"K": 0, u"H": 0} or dict(g2) != {u"止めた行": 7, u"S": 4, u"N": 0, u"U": 1, u"R": 0, u"K": 0, u"H": 2}:
        out.append(u"当たった類 合計・段 1・段 2・G が手計算と違う")
    v3 = tc[u"合計"][S3][u"V"]
    if dict(v3) != {u"止めた行": 8, u"S": 3, u"N": 1, u"U": 1, u"R": 1, u"K": 1, u"H": 1}:
        out.append(u"当たった類 合計・段 3・V が手計算と違う: %s" % (dict(v3),))
    if dict(tc[u"TSS"][S3][u"G"]) != {u"止めた行": 3, u"S": 1, u"N": 0, u"U": 0, u"R": 1, u"K": 0, u"H": 1} or dict(tc[u"YS"][S3][u"V"]) != {u"止めた行": 2, u"S": 0, u"N": 0, u"U": 1, u"R": 0, u"K": 1, u"H": 0}:
        out.append(u"当たった類の便ごとの数が手計算と違う")
    # --- 予測の数
    p = ms.predictions(rows, labels)
    pv = list(p.values())
    keys = list(p.keys())
    for i, pre in enumerate((u"SC-1", u"SC-2", u"SC-3", u"SC-4a", u"SC-4b", u"SC-5", u"SC-5", u"SC-6", u"SC-7", u"SC-7")):
        if not keys[i].startswith(pre):
            out.append(u"予測の欄の順・名前が違う: %s" % keys[i][:8])
    nd = lambda n_, d_: (n_, d_)
    flat = lambda f: dict((s, (f[s][u"分子"], f[s][u"分母"])) for s in (S1, S2, S3))
    if flat(pv[0][u"3 便の合計"]) != {S1: nd(2, 5), S2: nd(3, 5), S3: nd(4, 5)} or flat(pv[0][u"KAM"]) != {S1: nd(1, 2), S2: nd(2, 2), S3: nd(2, 2)} \
            or flat(pv[0][u"YS"]) != {S1: nd(0, 1), S2: nd(0, 1), S3: nd(1, 1)} or flat(pv[0][u"TSS"]) != {S1: nd(1, 2), S2: nd(1, 2), S3: nd(1, 2)}:
        out.append(u"SC-1 の分子・分母が手計算(3 便 2・3・4 / 5、KAM 1・2・2 / 2、YS 0・0・1 / 1、TSS 1・1・1 / 2)と違う")
    if flat(pv[1][u"KAM と YS の合計"]) != {S1: nd(1, 4), S2: nd(1, 4), S3: nd(3, 4)} or flat(pv[1][u"KAM"]) != {S1: nd(1, 3), S2: nd(1, 3), S3: nd(2, 3)} or flat(pv[1][u"YS"]) != {S1: nd(0, 1), S2: nd(0, 1), S3: nd(1, 1)}:
        out.append(u"SC-2 の分子・分母が手計算(1・1・3 / 4)と違う")
    if (pv[2][u"引けた行"], pv[2][u"段 1 の止めた行"], pv[2][u"段 3 の止めた行"]) != (4, 1, 3):
        out.append(u"SC-3 の数が手計算(4・1・3)と違う")
    if flat(pv[3]) != {S1: nd(1, 5), S2: nd(2, 5), S3: nd(3, 5)} or flat(pv[4]) != {S1: nd(2, 3), S2: nd(2, 3), S3: nd(2, 3)}:
        out.append(u"SC-4a・SC-4b の分子・分母が手計算(TSS の G 1・2・3 / 5、V 2・2・2 / 3)と違う")
    if flat(pv[5][u"3 便の合計"]) != {S1: nd(2, 4), S2: nd(2, 4), S3: nd(3, 4)} or flat(pv[5][u"KAM"]) != {S1: nd(0, 2), S2: nd(0, 2), S3: nd(1, 2)}:
        out.append(u"SC-5 の分子・分母が手計算と違う")
    if dict(pv[6]) != {S1: u"-10.00", S2: u"10.00", S3: u"5.00"}:
        out.append(u"SC-5 の率の差が手計算(-10.00・10.00・5.00)と違う: %s" % (dict(pv[6]),))
    if pv[7][S2][u"範囲の札の V の行"] != p[keys[0]][u"3 便の合計"][S2] or pv[7][S3][u"札 a の G の行"] != p[keys[1]][u"KAM と YS の合計"][S3] or pv[7][S1][u"札 a の G の行"][u"分子"] != 1:
        out.append(u"SC-6 の欄が SC-1・SC-2 の合計と合わない")
    if flat(pv[8]) != {S1: nd(0, 2), S2: nd(1, 2), S3: nd(2, 2)} or flat(pv[9]) != {S1: nd(1, 3), S2: nd(2, 3), S3: nd(3, 3)}:
        out.append(u"SC-7 の分子・分母が手計算(違うものが範囲 0・1・2 / 2、範囲か側 1・2・3 / 3)と違う")
    last = pv[10]
    if (last[u"V の札の行(札)"], last[u"V の札の行(引けた)"], last[u"G の札の行(札)"], last[u"G の札の行(引けた)"]) != (12, 10, 9, 9):
        out.append(u"分母の確かめが手計算(V 12・10 / G 9・9)と違う: %s" % (dict(last),))
    # 引けなかった行は分母に入れない(同じ札で、行を足すと分母が増える)
    more = rows + [R(u"KAM", 3, u"連結", 1, 1, u"V", True, u"S", u"S", u"S")]
    p2 = ms.predictions(more, labels)
    if flat(list(p2.values())[0][u"KAM"]) != {S1: nd(2, 3), S2: nd(3, 3), S3: nd(3, 3)}:
        out.append(u"引けなかった札が行を足すと引ける・分母に入る数が手計算(KAM 2・3・3 / 3)と違う")
    # label_tally が predictions と同じ行から
    lt = ms.tally_label(labels, rows)
    if lt[u"V の札"][u"合計"][u"範囲"][u"引けた行(分母)"] != 5 or lt[u"G の札(KAM・YS)"][u"合計"][u"型ごと"][u"a"][u"引けた行(分母)"] != 4:
        out.append(u"tally_label の合計が手計算と違う")
    return out


# ---------------------------------------------------------------- 6. 配線の確認(封 §2-2)
def fake_rt_rec(rows=7, states=None, fp=None):
    states = states or {G: 4, VM: 3, UN: 0, PN: 0}
    fp = fp or collections.OrderedDict((k, MS.VD.engine_fingerprint()[k]) for k in MS.FP_KEYS)
    return {u"engine の指紋(今。便 NRE の記録の直した後と同じ)": fp,
            u"段 1(第 1 便。400 本の判定)": {u"行(後)": rows, u"集計(後)": {u"群": {u"甲": {u"4 state": dict(states)}, u"乙": {u"4 state": dict((s, 0) for s in STATES)}}}}}


def fbook(batch, n, units):
    return collections.OrderedDict([(u"便", batch), (u"#", n), (u"units", list(units))])


def fdig(triples, cut=True, counts=None):
    return collections.OrderedDict([(u"cut", cut), (u"triples", list(triples)), (u"rows", []), (u"counts", counts or {}), (u"claims", len(triples))])


def wire_problems(ms=None):
    u"""配線の確認: TSS の行・state ごとの数(400 本のとき止める)・KAM と YS の前の記録との突き合わせ・位置と member の数。"""
    ms = ms or MS
    out = []
    tss = [fbook(u"TSS", 1, [(None, fdig([(1, 1, G), (1, 2, G), (2, 5, VM)]))]), fbook(u"TSS", 2, [(None, fdig([(3, 3, G), (3, 4, G), (4, 1, VM), (4, 2, UN)]))]),
           fbook(u"TSS", 3, [(None, fdig([], cut=False))])]
    rt = fake_rt_rec(rows=7, states={G: 4, VM: 2, UN: 1, PN: 0})
    w = ms.wire_tss(tss, rt, True)
    if (w[u"TSS の引き直しの行"], dict(w[u"TSS の state ごとの行"])) != (7, {G: 4, VM: 2, UN: 1, PN: 0}) or w[u"400 本の確かめを掛けた"] is not True:
        out.append(u"wire_tss の数が手計算と違う")
    if stops(ms, ms.wire_tss, tss, fake_rt_rec(rows=8, states={G: 4, VM: 2, UN: 1, PN: 0}), True) is not True:
        out.append(u"TSS の行の数が便 RT の記録と違うのに 400 本の経路で止まらない")
    if stops(ms, ms.wire_tss, tss, fake_rt_rec(rows=7, states={G: 3, VM: 3, UN: 1, PN: 0}), True) is not True:
        out.append(u"TSS の state ごとの数が便 RT の記録と違う(合計は同じ)のに 400 本の経路で止まらない")
    if stops(ms, ms.wire_tss, tss, fake_rt_rec(rows=8, states={G: 3, VM: 3, UN: 1, PN: 0}), False) is not False:
        out.append(u"小さい母集団の経路で TSS の行の数の確かめが止める")
    rs = ms.rt_state_counts(fake_rt_rec(rows=9, states={G: 5, VM: 2, UN: 1, PN: 1}))
    if dict(rs) != {G: 5, VM: 2, UN: 1, PN: 1}:
        out.append(u"rt_state_counts が便 RT の記録の群ごとの 4 state の合計でない")
    two = fake_rt_rec(rows=9, states={G: 5, VM: 2, UN: 1, PN: 1})
    two[u"段 1(第 1 便。400 本の判定)"][u"集計(後)"][u"群"][u"乙"][u"4 state"] = {G: 1, VM: 0, UN: 0, PN: 0}
    if dict(ms.rt_state_counts(two)) != {G: 6, VM: 2, UN: 1, PN: 1}:
        out.append(u"rt_state_counts が群を足さない")
    # KAM の前の記録との突き合わせ(手計算)
    def prev_rec(rows_by_book):
        return {u"本": [{u"#": n, u"連結": {u"切り出し": c1, u"行": [[si, pos, st] for si, pos, st in r1]}, u"単体": {u"切り出し": c2, u"行": [[si, pos, st] for si, pos, st in r2]}}
                       for n, (c1, r1, c2, r2) in rows_by_book.items()]}
    cut_ok, cut_ng = ms.KAM.CUT_OK, ms.KAM.CUT_NG
    prev = prev_rec({1: (cut_ok, [(1, 1, G), (1, 2, VM), (1, 3, UN), (1, 9, G)], cut_ng, []), 2: (cut_ok, [(2, 2, G)], cut_ok, [(5, 5, VM)])})
    kam = [fbook(u"KAM", 1, [(u"連結", fdig([(1, 1, G), (1, 2, G), (1, 3, UN), (1, 4, VM)])), (u"単体", fdig([], cut=False))]),
           fbook(u"KAM", 2, [(u"連結", fdig([(2, 2, G)])), (u"単体", fdig([(5, 5, VM), (6, 6, G)]))])]
    c = ms.compare_prev(kam, u"KAM", prev, {1, 2})
    w0 = c[u"全体"]
    if (w0[u"同じ鍵で同じ state の行"], w0[u"同じ鍵で state が違う行"], w0[u"今の引き直しにだけ在る行"], w0[u"前の記録にだけ在る行"], w0[u"前の記録の行"], w0[u"今の引き直しの行"], w0[u"切り出しの成否が前と違う本 × 側"]) \
            != (4, 1, 2, 1, 6, 7, 0):
        out.append(u"compare_prev の全体が手計算(同じ 4・違う 1・今にだけ 2・前にだけ 1・前 6・今 7)と違う: %s" % (dict(w0),))
    l0, t0 = c[u"文の種類別"][u"連結"], c[u"文の種類別"][u"単体"]
    if (l0[u"同じ鍵で同じ state の行"], l0[u"同じ鍵で state が違う行"], l0[u"今の引き直しにだけ在る行"], l0[u"前の記録にだけ在る行"]) != (3, 1, 1, 1) or (t0[u"同じ鍵で同じ state の行"], t0[u"今の引き直しにだけ在る行"]) != (1, 1):
        out.append(u"compare_prev の文の種類別が手計算と違う(連結 3・1・1・1 / 単体 同じ 1・今にだけ 1)")
    # 前の記録の本の鍵は本の #・文の種類を取り違えない(本 2 の連結 (2,2) は本 1 の連結 (2,2) と別)
    kam2 = [fbook(u"KAM", 1, [(u"連結", fdig([(2, 2, G)])), (u"単体", fdig([], cut=False))])]
    c2 = ms.compare_prev(kam2, u"KAM", prev, {1})
    if c2[u"全体"][u"同じ鍵で同じ state の行"] != 0 or c2[u"全体"][u"今の引き直しにだけ在る行"] != 1 or c2[u"全体"][u"前の記録にだけ在る行"] != 4:
        out.append(u"compare_prev が本の #(または文の種類)を取り違える: %s" % (dict(c2[u"全体"]),))
    # 切り出しの成否が前と違う本
    kam3 = [fbook(u"KAM", 1, [(u"連結", fdig([], cut=False)), (u"単体", fdig([]))])]
    c3 = ms.compare_prev(kam3, u"KAM", prev, {1})
    if c3[u"全体"][u"切り出しの成否が前と違う本 × 側"] != 2:
        out.append(u"切り出しの成否が前と違う本 × 側が手計算(2)と違う")
    # YS: 節別
    ysp = {u"本": [{u"#": 1, u"研究開発活動": {u"切り出し": cut_ok, u"行": [[1, 1, G]]}, u"設備投資等の概要": {u"切り出し": cut_ok, u"行": []}, u"配当政策": {u"切り出し": cut_ok, u"行": [[2, 2, VM]]}}]}
    ysb = [fbook(u"YS", 1, [(u"研究開発活動", fdig([(1, 1, VM)])), (u"設備投資等の概要", fdig([(3, 3, G)])), (u"配当政策", fdig([(2, 2, VM)]))])]
    cy = ms.compare_prev(ysb, u"YS", ysp, {1})
    if (cy[u"全体"][u"同じ鍵で同じ state の行"], cy[u"全体"][u"同じ鍵で state が違う行"], cy[u"全体"][u"今の引き直しにだけ在る行"]) != (1, 1, 1) or cy[u"節別"][u"配当政策"][u"同じ鍵で同じ state の行"] != 1 \
            or cy[u"節別"][u"研究開発活動"][u"同じ鍵で state が違う行"] != 1:
        out.append(u"compare_prev の YS の節別が手計算と違う")
    # 母集団の表と母集団の記録の照合
    pop = [(1, u"甲", u"s1"), (2, u"乙", u"s2")]
    recp = {u"行": [[1, u"甲", u"s1", 10], [2, u"乙", u"s2", 20]]}
    if stops(ms, ms.check_pop_record, pop, recp, u"KAM") is not False:
        out.append(u"母集団の表と記録が同じなのに check_pop_record が止まる")
    if stops(ms, ms.check_pop_record, pop, {u"行": [[1, u"甲", u"s1", 10], [2, u"乙", u"sX", 20]]}, u"KAM") is not True or \
            stops(ms, ms.check_pop_record, pop, {u"行": [[1, u"甲", u"s1", 10]]}, u"KAM") is not True or stops(ms, ms.check_pop_record, pop, {u"行": [[1, u"乙", u"s1", 10], [2, u"乙", u"s2", 20]]}, u"KAM") is not True:
        out.append(u"母集団の表と記録が違う(sha256・行の数・群)のに check_pop_record が止まらない")
    # 位置・member の数・事業で終わる前の字・切り出しの数
    cnt = [fbook(u"TSS", 1, [(None, fdig([], counts={u"位置: 数字から": 5, u"位置: 符号か空白から": 2, u"member の欄が在る": 7, u"前の字の終わりが「事業」": 1}))]),
           fbook(u"TSS", 2, [(None, fdig([], counts={u"位置: 数字から": 1, u"member の欄が無い": 1}))]),
           fbook(u"KAM", 1, [(u"連結", fdig([], counts={u"位置: 数字から": 3, u"member の欄が在る": 3})), (u"単体", fdig([], cut=False))])]
    wc = ms.wiring_counts(cnt)
    if (wc[u"TSS"][u"位置を確かめた数の claim(state を問わない)"], wc[u"TSS"][u"うち pos の字が数字"], wc[u"TSS"][u"うち pos の字が符号か空白"], wc[u"TSS"][u"raw の claim に member の欄が在る"],
            wc[u"TSS"][u"raw の claim に member の欄が無い"], wc[u"TSS"][u"前の字の終わりが「事業」の結んだ行(member が空)"]) != (8, 6, 2, 7, 1, 1) or wc[u"KAM"][u"うち pos の字が数字"] != 3 or wc[u"YS"][u"うち pos の字が数字"] != 0:
        out.append(u"wiring_counts が手計算(TSS 8・6・2・7・1・1、KAM 3、YS 0)と違う: %s" % (dict(wc[u"TSS"]),))
    cc = ms.cut_counts([fbook(u"KAM", 1, [(u"連結", fdig([(1, 1, G)])), (u"単体", fdig([], cut=False))]), fbook(u"KAM", 2, [(u"連結", fdig([], cut=False)), (u"単体", fdig([(1, 1, G), (2, 2, G)]))])])
    if (cc[u"KAM"][u"連結"][u"切れた"], cc[u"KAM"][u"連結"][u"切れない"], cc[u"KAM"][u"連結"][u"数の claim"], cc[u"KAM"][u"単体"][u"切れた"], cc[u"KAM"][u"単体"][u"数の claim"]) != (1, 1, 1, 1, 2):
        out.append(u"cut_counts が手計算と違う")
    return out


# ---------------------------------------------------------------- 7. 1 本の job(本物のまま。重い道具だけ作り物)
def make_book_args(tmp, batch, n, data=b"fake-material"):
    p = os.path.join(tmp, u"%s_%d.zip" % (batch, n))
    with open(p, "wb") as fh:
        fh.write(data)
    return (batch, n, u"甲", MS.ST.sha256_bytes(data), p)


def job_problems(ms=None):
    u"""``book_job`` を、材料の ZIP の字と重い道具(切り出し・engine)を作り物にして本物のまま走らせる。便・側・節を取り違えない。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="sc_job_")
    try:
        sentences = {u"zT": [u"売上高は100円でした。", u"その他の事業は10円。"], u"zW": [u"売上高は5円。"],
                     u"zK1": [u"監査上の項目", u"セグメントの売上は20円。"], u"zK2": [u"単体の売上は30円。"],
                     u"zY1": [u"研究の項目", u"子会社の費用は40円。"], u"zY2": [u"設備の項目", u"売上は50円。"], u"zY3": [u"配当の項目", u"売上は60円。"]}

        def mkpairs(z, specs):
            return hh(ms, sentences[z], specs)[1]
        pairs = {u"zW": mkpairs(u"zT", [(0, u"100", G, u"", []), (1, u"10", VM, u"", [])]),
                 u"zK1": mkpairs(u"zK1", [(1, u"20", G, u"", [])]), u"zK2": mkpairs(u"zK2", [(0, u"30", VM, u"", [])]),
                 u"zY1": mkpairs(u"zY1", [(1, u"40", G, u"", [])]), u"zY2": mkpairs(u"zY2", [(1, u"50", VM, u"", [])]), u"zY3": mkpairs(u"zY3", [(1, u"60", G, u"jpcrp:XMember", [])])}
        sent_of = {b"zW": sentences[u"zT"], b"zK1": sentences[u"zK1"], b"zK2": sentences[u"zK2"], b"zY1": sentences[u"zY1"], b"zY2": sentences[u"zY2"], b"zY3": sentences[u"zY3"]}
        seen = []

        def fake_claims(z):
            seen.append(z)
            return pairs[z.decode()]
        texts = {u"連結": u"TK1", u"単体": u"TK2"}
        sections = {u"研究開発活動": u"TY1", u"設備投資等の概要": u"TY2", u"配当政策": u"TY3"}
        zm = {u"TK1": b"zK1", u"TK2": b"zK2", u"TY1": b"zY1", u"TY2": b"zY2", u"TY3": b"zY3"}
        fake_zip = lambda zb, text: (zm[text], u"e", u"m")
        with patched(ms.TSS, cut=lambda z: (u"TXT", 0, None), wrap=lambda z, t: (b"zW", 1)), patched(ms.PS, claims_of=fake_claims), patched(ms, sentences_of=lambda z: sent_of[z]), \
                patched(ms.KAM, cut_kam=lambda z, side: (texts[side], None)), patched(ms.YS, cut_section=lambda z, sec: (sections[sec], None)), patched(ms.KAM.PR, build_modified_zip=fake_zip):
            b = ms.book_job(make_book_args(tmp, u"TSS", 7))
            if b[u"便"] != u"TSS" or b[u"#"] != 7 or [s for s, _u in b[u"units"]] != [None]:
                out.append(u"TSS の book_job の便・#・単位が違う")
            u = b[u"units"][0][1]
            if [(r[0], r[2:4]) for r in u[u"rows"]] != [(0, [u"G", True]), (1, [u"V", True])] or u[u"rows"][1][4:] != [u"S", u"S", u"S"] or u[u"rows"][0][4:] != [u"", u"", u""]:
                out.append(u"TSS の book_job の行が手計算(0 は G・止めない / 1 は V・S)と違う: %s" % (u[u"rows"],))
            b = ms.book_job(make_book_args(tmp, u"KAM", 3))
            if [s for s, _u in b[u"units"]] != [u"連結", u"単体"]:
                out.append(u"KAM の book_job が文の種類を 連結・単体 の順で返さない")
            k1, k2 = b[u"units"][0][1], b[u"units"][1][1]
            if [r[2] for r in k1[u"rows"]] != [u"G"] or [r[2] for r in k2[u"rows"]] != [u"V"] or k1[u"rows"][0][4:] != [u"S", u"S", u"S"] or k2[u"rows"][0][4:] != [u"N", u"N", u"N"]:
                out.append(u"KAM の book_job が連結と単体を取り違える(連結は G・S / 単体は V・N): %s" % ([k1[u"rows"], k2[u"rows"]],))
            b = ms.book_job(make_book_args(tmp, u"YS", 4))
            if [s for s, _u in b[u"units"]] != [u"研究開発活動", u"設備投資等の概要", u"配当政策"]:
                out.append(u"YS の book_job が節を決めた順で返さない")
            y = [x[1][u"rows"] for x in b[u"units"]]
            if [len(r) for r in y] != [1, 1, 1] or y[0][0][4:] != [u"", u"", u"K"] or y[1][0][2] != u"V" or y[2][0][3] is not False or y[2][0][4:] != [u"", u"", u""]:
                out.append(u"YS の book_job が節を取り違える(研究は G・段 3 の K / 設備は V / 配当は member が入っていて止めない): %s" % (y,))
            # 切れない側は空の単位
            with patched(ms.KAM, cut_kam=lambda z, side: (None, u"x")):
                nb = ms.book_job(make_book_args(tmp, u"KAM", 3))
                if any(un[u"cut"] or un[u"rows"] for _s, un in nb[u"units"]) or len(nb[u"units"]) != 2:
                    out.append(u"切れない KAM の側が空の単位でない")
            # sha256 が表と違えば止まる・材料が無ければ止まる
            a = make_book_args(tmp, u"TSS", 8)
            if stops(ms, ms.book_job, (a[0], a[1], a[2], u"0" * 64, a[4])) is not True:
                out.append(u"材料の ZIP の sha256 が表と違うのに止まらない")
            if stops(ms, ms.book_job, (a[0], a[1], a[2], a[3], a[4] + u"x")) is not True:
                out.append(u"材料の ZIP が無いのに止まらない")
        # claims_of に渡る ZIP: TSS は包んだ ZIP・KAM・YS は書き換えた ZIP
        if seen != [b"zW", b"zK1", b"zK2", b"zY1", b"zY2", b"zY3"]:
            out.append(u"PS.claims_of に渡る ZIP が(TSS は包んだ ZIP・KAM と YS は書き換えた ZIP)の順でない: %s" % (seen,))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


# ---------------------------------------------------------------- 8. つなぐ配線(orchestrate を作り物の本で本物のまま走らせる)
def fake_read_rec(batch, rows):
    u"""便 AT の検査を通る作り物の読みの記録(rows = [組, 本の #, 文の番号, 位置, 型, 違うもの])。"""
    groups = list(MS.AT.GROUPS[batch])
    rec = {u"行の欄": list(MS.AT.ROW_FIELDS), u"行": [list(r) for r in rows], u"型の集計": {}, u"b の違うものの集計": {}, u"読む行の規則": {u"読む行の数": {}, u"読む行の数の合計": len(rows)}}
    for g in groups:
        grows = [r for r in rows if r[0] == g]
        types = MS.AT.G_TYPES if g.startswith(u"G") else MS.AT.V_TYPES
        c = collections.Counter(r[4] for r in grows)
        rec[u"型の集計"][g] = collections.OrderedDict((t, c.get(t, 0)) for t in types)
        if g.startswith(u"G"):
            d = collections.Counter(r[5] for r in grows if r[4] == u"b")
            rec[u"b の違うものの集計"][g] = collections.OrderedDict((x, d.get(x, 0)) for x in MS.AT.DIFFS)
        rec[u"読む行の規則"][u"読む行の数"][g] = len(grows)
    return rec


class FakeWorld(object):
    u"""作り物の 3 便。TSS 3 本・KAM 2 本・YS 2 本。便・state・段・文の種類・節で非対称。手計算は ``orchestrate_problems``。"""

    def __init__(self, ms):
        self.ms = ms
        A = [u"経営成績の概況", u"売上高は100円となりました。", u"セグメント別の概況", u"売上高は200円でした。", u"その他の事業は300円で、うち海外は50円。", u"利益は10円。"]
        B = [u"売上高は100円でした。", u"うち国内は30円でした。", u"海外子会社の売上高は5円。"]
        K1 = [u"監査上の主要な検討事項", u"セグメントの売上高は1,000円。", u"子会社の資産は50円。"]
        K2 = [u"売上高は2,000円。"]
        Y1 = [u"研究開発活動", u"当期の単体の研究開発費は10円。"]
        Y2 = [u"設備投資の概要", u"単体の設備投資は20円。"]
        hh_ = lambda s, specs: hh(ms, s, specs)[0]
        self.tss1 = hh_(A, [(1, u"100", G, u"", []), (3, u"200", VM, u"", []), (4, u"300", G, u"", []), (4, u"50", VM, u"", [NONCONS_PTR]), (5, u"10", UN, u"", [])])
        self.tss3 = hh_(B, [(0, u"100", VM, u"", []), (1, u"30", G, u"", []), (2, u"5", G, u"jpcrp:XMember", [])])
        self.kam1 = hh_(K1, [(1, u"1,000", VM, u"", []), (2, u"50", G, u"", [])])
        self.kam2 = hh_(K2, [(0, u"2,000", VM, u"", [])])
        self.ys1 = hh_(Y1, [(1, u"10", G, u"", [])])
        self.ys2 = hh_(Y2, [(1, u"20", VM, u"", [NONCONS_PTR])])
        pos = lambda s, si, t: s[si].index(t)
        self.pos = {u"t200": pos(A, 3, u"200"), u"t50": pos(A, 4, u"50"), u"t300": pos(A, 4, u"300"), u"t100": pos(A, 1, u"100"), u"b100": pos(B, 0, u"100"), u"b30": pos(B, 1, u"30"), u"b5": pos(B, 2, u"5"),
                    u"k1000": pos(K1, 1, u"1,000"), u"k50": pos(K1, 2, u"50"), u"k2000": pos(K2, 0, u"2,000"), u"y10": pos(Y1, 1, u"10"), u"y20": pos(Y2, 1, u"20")}
        E = ms.empty_digest
        self.books = {
            (u"TSS", 1): fbook(u"TSS", 1, [(None, self.tss1)]), (u"TSS", 2): fbook(u"TSS", 2, [(None, E())]), (u"TSS", 3): fbook(u"TSS", 3, [(None, self.tss3)]),
            (u"KAM", 1): fbook(u"KAM", 1, [(u"連結", self.kam1), (u"単体", E())]), (u"KAM", 2): fbook(u"KAM", 2, [(u"連結", E()), (u"単体", self.kam2)]),
            (u"YS", 1): fbook(u"YS", 1, [(u"研究開発活動", self.ys1), (u"設備投資等の概要", self.ys2), (u"配当政策", E())]),
            (u"YS", 2): fbook(u"YS", 2, [(u"研究開発活動", E()), (u"設備投資等の概要", E()), (u"配当政策", E())])}
        # 札: KAM の V 連結(ア)・V 単体(エ。行が無い)・G 連結(a)。YS の V 設備(ア。止めない)・G 研究(b 範囲)。TSS の V(ア・カ3)
        p = self.pos
        kam_rows = [[u"V 連結", 1, 1, p[u"k1000"], u"ア", None], [u"V 単体", 2, 0, p[u"k2000"], u"エ", None], [u"V 単体", 2, 5, 1, u"エ", None], [u"V 連結", 1, 2, p[u"k50"], u"ウ", None],
                    [u"G 連結", 1, 2, p[u"k50"], u"a", None], [u"G 連結", 1, 1, p[u"k1000"], u"a", None]]
        ys_rows = [[u"V 設備", 1, 1, p[u"y20"], u"ア", None], [u"G 研究", 1, 1, p[u"y10"], u"b", u"範囲"]]
        self.recs = {
            u"rt": fake_rt_rec(rows=7, states={G: 4, VM: 3, UN: 1, PN: 0}),
            u"kam_read": fake_read_rec(u"KAM", kam_rows), u"ys_read": fake_read_rec(u"YS", ys_rows),
            u"tss_vm": {u"行の欄": list(ms.AT.VM_FIELDS), u"標本の規則": {u"標本の数": 3}, u"行": [[1, 1, 3, p[u"t200"], u"ア"], [2, 1, 4, p[u"t50"], u"カ"], [3, 3, 0, p[u"b100"], u"ク"]]},
            u"tss_sub": {u"行の欄": list(ms.AT.SUB_FIELDS), u"細目の字": [u"カ1", u"カ2", u"カ3"], u"行": [[2, u"カ", u"カ3"]]},
            u"kam_states": {u"本": [{u"#": 1, u"連結": {u"切り出し": ms.KAM.CUT_OK, u"行": [[1, p[u"k1000"], VM], [2, p[u"k50"], VM], [7, 7, G]]}, u"単体": {u"切り出し": ms.KAM.CUT_NG, u"行": []}},
                                     {u"#": 2, u"連結": {u"切り出し": ms.KAM.CUT_NG, u"行": []}, u"単体": {u"切り出し": ms.KAM.CUT_OK, u"行": [[0, p[u"k2000"], VM]]}}]},
            u"ys_states": {u"本": [{u"#": 1, u"研究開発活動": {u"切り出し": ms.KAM.CUT_OK, u"行": [[1, p[u"y10"], G]]}, u"設備投資等の概要": {u"切り出し": ms.KAM.CUT_OK, u"行": [[1, p[u"y20"], VM]]},
                                    u"配当政策": {u"切り出し": ms.KAM.CUT_NG, u"行": []}},
                                   {u"#": 2, u"研究開発活動": {u"切り出し": ms.KAM.CUT_NG, u"行": []}, u"設備投資等の概要": {u"切り出し": ms.KAM.CUT_NG, u"行": []}, u"配当政策": {u"切り出し": ms.KAM.CUT_NG, u"行": []}}]}}
        self.pops = {u"TSS": [(1, u"甲", u"k", u"t1"), (2, u"甲", u"k", u"t2"), (3, u"甲", u"k", u"t3")], u"KAM": [(1, u"甲", u"kam1"), (2, u"甲", u"kam2")], u"YS": [(1, u"甲", u"ys1"), (2, u"甲", u"ys2")]}


def run_orchestrate(ms, world=None, hook=None, hook_cache=None, mutate=None, rt_rec=None, capture=None, procs=1):
    u"""``mutate`` は books(作り物の job の返り値の表)を書き換える関数。材料の置き場は使い捨て。"""
    world = world or FakeWorld(ms)
    books = copy.deepcopy(world.books)
    if mutate:
        mutate(books)
    recs = copy.deepcopy(world.recs)
    if rt_rec is not None:
        recs[u"rt"] = rt_rec
    tmp = tempfile.mkdtemp(prefix="sc_orch_")
    tmp2 = tempfile.mkdtemp(prefix="sc_orch_cache_")
    calls = []
    try:
        for (_n, _g, _k, sha) in world.pops[u"TSS"]:
            open(os.path.join(tmp, sha + u".zip"), "w").close()
        for r in world.pops[u"KAM"] + world.pops[u"YS"]:
            open(os.path.join(tmp2, r[2] + u".zip"), "w").close()

        def fake_job(args):
            calls.append(args)
            if hook is not None and len(calls) == 1:
                hook(tmp)
            if hook_cache is not None and len(calls) == 1:
                hook_cache(tmp2)
            return copy.deepcopy(books[(args[0], args[1])])
        fake_scan = lambda base, pop: dict((r[2], (os.path.join(base, r[2] + u".zip"), 0)) for r in pop)
        snap = lambda base: [[len(os.listdir(base)), u"|".join(sorted(os.listdir(base)))]]
        over = {"book_job": fake_job, "scan_material": fake_scan, "folder_snapshots": snap}
        if capture is not None:
            real = ms.wire_tss

            def spy(b, rt, full):
                capture.append((rt, full))
                return real(b, rt, full) if not full else collections.OrderedDict([(u"x", 0)])
            over["wire_tss"] = spy
        with patched(ms, **over):
            rec = ms.orchestrate(root=ROOT, procs=procs, material=tmp, cache_base=tmp2, say=lambda *a: None, populations=world.pops, recs=recs)
        return rec, calls
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(tmp2, ignore_errors=True)


def run_stops(ms, **kw):
    try:
        run_orchestrate(ms, **kw)
    except ms.Stop:
        return True
    except BaseException as exc:                   # noqa: BLE001
        return type(exc).__name__
    return False


def orchestrate_problems(ms=None):
    u"""作り物の 3 便(TSS 3・KAM 2・YS 2 本)で ``orchestrate`` を本物のまま走らせ、手計算と合わせる。便・state・段・文の種類・節で非対称。"""
    ms = ms or MS
    out = []
    world = FakeWorld(ms)
    rec, calls = run_orchestrate(ms, world=world)
    if [(c[0], c[1]) for c in calls] != [(u"TSS", 1), (u"TSS", 2), (u"TSS", 3), (u"KAM", 1), (u"KAM", 2), (u"YS", 1), (u"YS", 2)]:
        out.append(u"orchestrate が(TSS・KAM・YS の順・母集団の順)に本ごとの job を呼んでいない: %s" % ([(c[0], c[1]) for c in calls],))
    # 行: TSS 本 1 は G 2(100・300)V 2(200・50)・本 3 は G 2(30・5)V 1(100)・KAM は V 2(1,000・2,000)G 1(50)・YS は G 1(10)V 1(20)
    rows = rec[u"行"]
    keys = [(r[0], r[1], r[2]) for r in rows]
    want_keys = [(u"TSS", 1, None)] * 4 + [(u"TSS", 3, None)] * 3 + [(u"KAM", 1, u"連結")] * 2 + [(u"KAM", 2, u"単体")] + [(u"YS", 1, u"研究開発活動"), (u"YS", 1, u"設備投資等の概要")]
    if keys != want_keys:
        out.append(u"orchestrate の行の鍵の順が(便 → 本の # → 文の種類か節)でない: %s" % (keys,))
    p = world.pos
    by = dict(((r[0], r[1], r[2], r[3], r[4]), r) for r in rows)
    want = {
        (u"TSS", 1, None, 1, p[u"t100"]): [u"G", True, u"", u"", u""],
        (u"TSS", 1, None, 3, p[u"t200"]): [u"V", True, u"", u"H", u"H"],
        (u"TSS", 1, None, 4, p[u"t300"]): [u"G", True, u"S", u"SH", u"SUH"],
        (u"TSS", 1, None, 4, p[u"t50"]): [u"V", True, u"SU", u"SUH", u"SURH"],
        (u"TSS", 3, None, 0, p[u"b100"]): [u"V", True, u"", u"", u""],
        (u"TSS", 3, None, 1, p[u"b30"]): [u"G", True, u"U", u"U", u"UR"],
        (u"TSS", 3, None, 2, p[u"b5"]): [u"G", False, u"", u"", u""],
        (u"KAM", 1, u"連結", 1, p[u"k1000"]): [u"V", True, u"S", u"S", u"S"],
        (u"KAM", 1, u"連結", 2, p[u"k50"]): [u"G", True, u"", u"", u"K"],
        (u"KAM", 2, u"単体", 0, p[u"k2000"]): [u"V", True, u"", u"", u""],
        (u"YS", 1, u"研究開発活動", 1, p[u"y10"]): [u"G", True, u"N", u"N", u"N"],
        (u"YS", 1, u"設備投資等の概要", 1, p[u"y20"]): [u"V", True, u"", u"", u""]}
    for k, v in want.items():
        if by.get(k, [None] * 3)[5:] != v:
            out.append(u"orchestrate の行 %s が手計算と違う: %s(手計算 %s)" % (k[:4], by.get(k, [None] * 3)[5:], v))
    # 結んだ行の全部
    ta = rec[K_ALL]
    if (ta[u"TSS"][u"全体"][u"G"][u"結んだ行"], ta[u"TSS"][u"全体"][u"V"][u"結んだ行"], ta[u"KAM"][u"全体"][u"V"][u"結んだ行"], ta[u"KAM"][u"全体"][u"G"][u"結んだ行"],
            ta[u"YS"][u"全体"][u"V"][u"結んだ行"], ta[u"YS"][u"全体"][u"G"][u"結んだ行"]) != (4, 3, 2, 1, 1, 1):
        out.append(u"結んだ行の便ごと・state ごとの数が手計算(TSS G 4・V 3 / KAM V 2・G 1 / YS V 1・G 1)と違う")
    if ta[u"KAM"][u"文の種類別"][u"連結"][u"V"][u"結んだ行"] != 1 or ta[u"KAM"][u"文の種類別"][u"単体"][u"V"][u"結んだ行"] != 1 or ta[u"YS"][u"節別"][u"設備投資等の概要"][u"V"][u"結んだ行"] != 1:
        out.append(u"結んだ行の文の種類別・節別が手計算と違う")
    tg = ta[u"TSS"][u"全体"][u"G"]
    tv = ta[u"TSS"][u"全体"][u"V"]
    if (tg[u"member が空の行"], dict(tg[u"止めた行"]), dict(tv[u"止めた行"])) != (3, {S1: 2, S2: 2, S3: 2}, {S1: 1, S2: 2, S3: 2}):
        out.append(u"結んだ行 TSS の止めた行が手計算(G 空 3・止め 2/2/2、V 止め 1/2/2)と違う: %s" % (dict(tg[u"止めた行"]), dict(tv[u"止めた行"])))
    # 配線の確認
    wire = rec[K_WIRE]
    w = wire[u"TSS の行(便 RT の記録との確かめ)"]
    if (w[u"TSS の引き直しの行"], dict(w[u"TSS の state ごとの行"])) != (8, {G: 4, VM: 3, UN: 1, PN: 0}):
        out.append(u"TSS の引き直しの行・state ごとが手計算(8・G 4・V 3・UNV 1)と違う: %s" % (w,))
    k = wire[u"KAM の行(前の記録との突き合わせ。止めない)"][u"全体"]
    if (k[u"同じ鍵で同じ state の行"], k[u"同じ鍵で state が違う行"], k[u"今の引き直しにだけ在る行"], k[u"前の記録にだけ在る行"]) != (2, 1, 0, 1):
        out.append(u"KAM の前の記録との突き合わせが手計算(同じ 2・違う 1・今にだけ 0・前にだけ 1)と違う: %s" % (dict(k),))
    y = wire[u"YS の行(前の記録との突き合わせ。止めない)"][u"全体"]
    if (y[u"同じ鍵で同じ state の行"], y[u"同じ鍵で state が違う行"], y[u"今の引き直しにだけ在る行"], y[u"前の記録にだけ在る行"]) != (2, 0, 0, 0):
        out.append(u"YS の前の記録との突き合わせが手計算(同じ 2)と違う")
    wc = wire[u"位置の確かめ・member の欄・「事業」で終わる前の字(便ごと)"]
    if wc[u"TSS"][u"位置を確かめた数の claim(state を問わない)"] != 8 or wc[u"TSS"][u"うち pos の字が数字"] != 8 or wc[u"KAM"][u"位置を確かめた数の claim(state を問わない)"] != 3 \
            or wc[u"YS"][u"位置を確かめた数の claim(state を問わない)"] != 2 or wc[u"TSS"][u"raw の claim に member の欄が在る"] != 8:
        out.append(u"位置の確かめ・member の欄の数が手計算(TSS 8・KAM 3・YS 2)と違う")
    if wire[u"本の数"] != collections.OrderedDict([(u"TSS", 3), (u"KAM", 2), (u"YS", 2)]):
        out.append(u"配線の本の数が(3・2・2)でない")
    cut = rec[u"切り出し"]
    if (cut[u"TSS"][u"(文の種類なし)"][u"切れた"], cut[u"TSS"][u"(文の種類なし)"][u"切れない"], cut[u"KAM"][u"連結"][u"切れた"], cut[u"KAM"][u"単体"][u"切れた"], cut[u"YS"][u"配当政策"][u"切れた"]) != (2, 1, 1, 1, 0):
        out.append(u"切り出しの数が手計算と違う")
    # 札(作り物の読みの記録から。V の札 KAM: ア(1,000 止める)・エ 2 行(行が無い 1・引けた 1)。G の札 KAM: a。YS: V 設備ア・G 研究 b 範囲。TSS: ア 200・カ3 50・ク 100)
    lb = rec[K_LABEL][u"V の札"]
    kc = lb[u"KAM"][u"全体"]
    if (kc[u"札の行"], kc[u"引けた行(分母)"], kc[u"引けなかった行"], dict(kc[u"引けなかった理由"]), dict(kc[u"止めた行"])) != (4, 2, 2, {u"行が無い": 1, u"state が違う": 1}, {S1: 1, S2: 1, S3: 1}):
        out.append(u"V の札 KAM の全体が手計算(4・2・2・行が無い 1・state が違う 1・止めた 1/1/1)と違う: %s" % (dict(kc),))
    if (lb[u"YS"][u"全体"][u"引けた行(分母)"], dict(lb[u"YS"][u"全体"][u"止めた行"])) != (1, {S1: 0, S2: 0, S3: 0}):
        out.append(u"V の札 YS の全体が手計算(1・止めた 0/0/0。N のただし書きで止めない)と違う")
    tt = lb[u"TSS"]
    if (tt[u"全体"][u"引けた行(分母)"], dict(tt[u"全体"][u"止めた行"]), dict(tt[u"範囲"][u"止めた行"]), tt[u"属性ごと"][u"単位"][u"引けた行(分母)"], dict(tt[u"属性ごと"][u"単位"][u"止めた行"]),
            tt[u"分母から除く札"][u"引けた行(分母)"]) != (3, {S1: 1, S2: 2, S3: 2}, {S1: 0, S2: 1, S3: 1}, 1, {S1: 1, S2: 1, S3: 1}, 1):
        out.append(u"V の札 TSS が手計算(3・止めた 1/2/2、範囲 0/1/1、単位 1・1/1/1、除く 1)と違う: %s" % (dict(tt[u"全体"][u"止めた行"]),))
    nr = lb[u"TSS"][u"範囲でない(分母から除く札は除く)"]
    if (nr[u"札の行"], nr[u"引けた行(分母)"], dict(nr[u"止めた行"])) != (1, 1, {S1: 1, S2: 1, S3: 1}):
        out.append(u"V の札 TSS の範囲でないが手計算(1・1・止めた 1/1/1。分母から除く札を入れない)と違う")
    sc1 = list(rec[K_PRED].values())[0]
    if dict((k_, (v_[u"分子"], v_[u"分母"])) for k_, v_ in sc1[u"3 便の合計"].items()) != {S1: (1, 3), S2: (2, 3), S3: (2, 3)}:
        out.append(u"SC-1 の 3 便の合計が手計算(分母 3・止めた 1/2/2)と違う: %s" % (dict(sc1[u"3 便の合計"]),))
    gl = rec[K_LABEL][u"G の札(KAM・YS)"]
    ga = gl[u"KAM"][u"型ごと"][u"a"]
    if (ga[u"札の行"], ga[u"引けなかった行"], dict(ga[u"引けなかった理由"])) != (2, 1, {u"行が無い": 0, u"state が違う": 1}):
        out.append(u"G の札 KAM の a の引けなかった行が手計算(札 2・引けなかった 1・state が違う 1)と違う")
    if (gl[u"KAM"][u"型ごと"][u"a"][u"引けた行(分母)"], dict(gl[u"KAM"][u"型ごと"][u"a"][u"止めた行"]), gl[u"YS"][u"型ごと"][u"b"][u"引けた行(分母)"], dict(gl[u"YS"][u"b の違うものが範囲(字のとおり)"][u"止めた行"])) \
            != (1, {S1: 0, S2: 0, S3: 1}, 1, {S1: 1, S2: 1, S3: 1}):
        out.append(u"G の札の KAM・YS が手計算と違う")
    # 予測の数が行・札から作り直せる
    if rec[K_PRED] != ms.predictions(rec[u"行"], ms.build_labels(world.recs)) or rec[K_CLASS] != ms.tally_class(rec[u"行"]):
        out.append(u"予測・当たった類の数が行・札から作り直したものと違う")
    if rec[u"seal"] != SEAL_REL or rec[u"封の commit"] != SEAL_COMMIT_SHORT or rec[u"profile"] != u"P33E" or rec[u"key_leaks"] != [] or rec[u"行の欄"] != list(ms.ROW_COLUMNS):
        out.append(u"記録の封の path・commit・profile・key_leaks・行の欄が違う")
    if rec[u"手がかりの語の表"] != collections.OrderedDict((c, list(w)) for c, w in WORD_TABLE.items()):
        out.append(u"記録の手がかりの語の表が封の表と違う")
    # 記録の字にして漏れの検査を通る(欄の名前に禁止の欄が無い)・字は JSON で読み戻せる
    text = ms.record_text(rec)
    if json.loads(text, object_pairs_hook=collections.OrderedDict) != json.loads(ms.dumps(rec), object_pairs_hook=collections.OrderedDict) or leak_problems(text):
        out.append(u"作り物の記録が記録の字にならない・漏れの検査を通らない: %s" % (leak_problems(text),))
    # ---- 止める条件
    bad = fake_rt_rec(rows=7, states={G: 4, VM: 3, UN: 1, PN: 0}, fp=collections.OrderedDict((k_, u"x-" + k_) for k_ in ms.FP_KEYS))
    if run_stops(ms, world=world, rt_rec=bad) is not True:
        out.append(u"engine の指紋が便 RT の記録の今と違うのに止まらない")

    if run_stops(ms, world=world, hook=lambda d: open(os.path.join(d, u"added.zip"), "w").close()) is not True:
        out.append(u"材料の置き場に file が増えたのに止まらない")
    if run_stops(ms, world=world, hook=lambda d: None, hook_cache=lambda d: None) is not False:
        out.append(u"置き場が変わらないのに止まる")
    if run_stops(ms, world=world, hook_cache=lambda d: open(os.path.join(d, u"added.zip"), "w").close()) is not True:
        out.append(u"KAM・YS の置き場に file が増えたのに止まらない")
    if run_stops(ms, world=world, hook_cache=lambda d: os.rename(os.path.join(d, u"kam1.zip"), os.path.join(d, u"renamed.zip"))) is not True:
        out.append(u"KAM・YS の置き場の名前が変わった(件数は同じ)のに止まらない")
    # 小さい母集団の経路は TSS の行の確かめを掛けない
    if run_stops(ms, world=world, rt_rec=fake_rt_rec(rows=999, states={G: 1, VM: 1, UN: 1, PN: 1})) is not False:
        out.append(u"小さい母集団の経路が TSS の行の確かめで止まる")
    return out


def default_path_problems(ms=None):
    u"""引数を明示で渡さない本番の既定の経路: 入力の確かめ・記録の読み・3 便の母集団(封の表)・400 本の経路の期待が便 RT の記録から取られる。"""
    ms = ms or MS
    out = []
    pops = {u"TSS": ms.ST.read_population(ROOT), u"KAM": ms.KAM.read_population(ROOT), u"YS": ms.YS.read_population(ROOT)}
    if (len(pops[u"TSS"]), len(pops[u"KAM"]), len(pops[u"YS"])) != (400, 201, 201):
        out.append(u"封の表から読んだ母集団が(400・201・201)でない")
    tmp = tempfile.mkdtemp(prefix="sc_default_")
    calls = []
    cap = []
    try:
        for (_n, _g, _k, sha) in pops[u"TSS"]:
            open(os.path.join(tmp, sha + u".zip"), "w").close()

        def fake_job(args):
            calls.append(args)
            batch = args[0]
            sides = ms.SIDE_ORDER[batch]
            return collections.OrderedDict([(u"便", batch), (u"#", args[1]), (u"units", [(s, ms.empty_digest()) for s in sides])])

        def spy(books, rt, full):
            cap.append((len(books), rt[u"段 1(第 1 便。400 本の判定)"][u"行(後)"], full, dict(ms.rt_state_counts(rt))))
            return collections.OrderedDict([(u"x", 0)])
        with patched(ms, book_job=fake_job, wire_tss=spy, scan_material=lambda base, pop: dict((r[2], (os.path.join(base, r[2] + u".zip"), 0)) for r in pop),
                     folder_snapshots=lambda base: [[0, u"x"]]):
            rec = ms.orchestrate(root=ROOT, procs=1, material=tmp, cache_base=tmp, say=lambda *a: None)
        n = collections.Counter(c[0] for c in calls)
        if dict(n) != {u"TSS": 400, u"KAM": 201, u"YS": 201} or [c[0] for c in calls] != [u"TSS"] * 400 + [u"KAM"] * 201 + [u"YS"] * 201:
            out.append(u"既定の経路の job が(TSS 400・KAM 201・YS 201 の順)でない: %s" % (dict(n),))
        if [c[1] for c in calls[:400]] != list(range(1, 401)) or [c[1] for c in calls[400:601]] != list(range(1, 202)):
            out.append(u"既定の経路の job の本の # が母集団の表の順でない")
        if len(cap) != 1 or cap[0][0] != 802 or cap[0][1] != 24531 or cap[0][2] is not True or cap[0][3] != {G: 6720, VM: 1858, UN: 4945, PN: 11008}:
            out.append(u"400 本の経路で wire_tss に渡す期待が便 RT の記録(行 24531・G 6720・V 1858・UNV 4945・PNF 11008)でない: %s" % (cap,))
        if [(i[u"path"], i[u"sha256"]) for i in rec[u"入力"]] != list(INPUT_SHAS):
            out.append(u"既定の経路の記録の入力が表と違う")
        if rec[u"材料"][u"表と一致した ZIP"] != collections.OrderedDict([(u"TSS", 400), (u"KAM", 201), (u"YS", 201)]):
            out.append(u"既定の経路の記録の ZIP の数が(400・201・201)でない")
        if rec[u"行"] != [] or rec[u"engine の指紋(今。便 RT の記録の今と同じ)"] != collections.OrderedDict((k, ms.VD.engine_fingerprint()[k]) for k in ms.FP_KEYS):
            out.append(u"既定の経路の記録の行・指紋が違う")
        # 400 本の経路は便 RT の記録と違えば本物の wire_tss で止まる・同じなら通る
        def job_with(states_counts):
            def fj(args):
                b = fake_job(args)
                if args[0] == u"TSS" and args[1] == 1:
                    tri = []
                    for st, k in states_counts:
                        tri.extend((i, 0, st) for i in range(len(tri), len(tri) + k))
                    b[u"units"] = [(None, collections.OrderedDict([(u"cut", True), (u"triples", tri), (u"rows", []), (u"counts", {}), (u"claims", len(tri))]))]
                return b
            return fj
        run_kw = dict(root=ROOT, procs=1, material=tmp, cache_base=tmp, say=lambda *a: None)
        fake_scan = lambda base, pop: dict((r[2], (os.path.join(base, r[2] + u".zip"), 0)) for r in pop)
        right = [(G, 6720), (VM, 1858), (UN, 4945), (PN, 11008)]
        with patched(ms, book_job=fake_job, scan_material=fake_scan, folder_snapshots=lambda base: [[0, u"x"]]):
            if stops(ms, ms.orchestrate, **run_kw) is not True:
                out.append(u"400 本の経路で TSS の行が便 RT の記録と違う(行 0)のに止まらない")
        with patched(ms, book_job=job_with([(G, 24531)]), scan_material=fake_scan, folder_snapshots=lambda base: [[0, u"x"]]):
            if stops(ms, ms.orchestrate, **run_kw) is not True:
                out.append(u"400 本の経路で TSS の行の数は同じで state ごとの数が便 RT の記録と違うのに止まらない")
        with patched(ms, book_job=job_with([(G, 6720), (VM, 1858), (UN, 4945), (PN, 11008)]), scan_material=fake_scan, folder_snapshots=lambda base: [[0, u"x"]]):
            if stops(ms, ms.orchestrate, **run_kw) is not False:
                out.append(u"400 本の経路で TSS の行・state ごとの数が便 RT の記録と同じなのに止まる")
        with patched(ms, book_job=job_with(right[:3] + [(PN, 11007)]), scan_material=fake_scan, folder_snapshots=lambda base: [[0, u"x"]]):
            if stops(ms, ms.orchestrate, **run_kw) is not True:
                out.append(u"400 本の経路で TSS の行が 1 行足りないのに止まらない")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def fingerprint_problems(ms=None):
    u"""engine の指紋は 4 欄のどれが違っても止まる。"""
    ms = ms or MS
    out = []
    if tuple(ms.FP_KEYS) != (u"adapter_xbrl_py_sha256", u"adapter_xbrl_py_files", u"core_py_sha256", u"core_py_files"):
        out.append(u"engine の指紋の欄が 4 つの決まった名前でない")
    base = collections.OrderedDict((k, ms.VD.engine_fingerprint()[k]) for k in ms.FP_KEYS)
    if run_stops(ms, rt_rec=fake_rt_rec(rows=7, states={G: 4, VM: 3, UN: 1, PN: 0}, fp=base)) is not False:
        out.append(u"engine の指紋が同じなのに止まる")
    for k in ms.FP_KEYS:
        fp = collections.OrderedDict(base)
        fp[k] = u"x-%s" % (base[k],)
        if run_stops(ms, rt_rec=fake_rt_rec(rows=7, states={G: 4, VM: 3, UN: 1, PN: 0}, fp=fp)) is not True:
            out.append(u"engine の指紋の欄 %s だけが違うのに止まらない" % k)
    return out


def check_text_problems(ms=None):
    u"""``check_text`` が漏れ(repo へ入れない欄・鍵の形・環境の鍵の値)を止める。封の path・入力の path は漏れに数えない。"""
    ms = ms or MS
    out = []
    if stops(ms, ms.check_text, {}, u"ok") is not False:
        out.append(u"漏れの無い字が止まる")
    if stops(ms, ms.check_text, collections.OrderedDict([(u"value", 1)]), u"ok") is not True:
        out.append(u"repo へ入れない欄が在るのに check_text が止まらない")
    if stops(ms, ms.check_text, {}, u"Zz" * 20) is not True:
        out.append(u"32 字以上の英数字の連なりが在るのに check_text が止まらない")
    if stops(ms, ms.check_text, {}, u"a secretvalue b", u"secretvalue") is not True:
        out.append(u"環境の鍵の値が在るのに check_text が止まらない")
    if stops(ms, ms.check_text, {}, u" ".join([SEAL_REL] + list(INPUT_RELS))) is not False:
        out.append(u"封・入力の path が漏れに数えられている")
    if stops(ms, ms.record_text, collections.OrderedDict([(u"value", 1)])) is not True:
        out.append(u"record_text が漏れを止めない")
    return out


# ---------------------------------------------------------------- 9. 記録
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


FORBIDDEN_KEYS = (u"文", u"span", u"sentence", u"値", u"要素名", u"context", u"name", u"会社名", u"証券コード", u"docID", u"value", u"text", u"数", u"recomputed", u"subject", u"主語", u"語",
                  u"pointer", u"pointers", u"member", u"金額")


def leak_problems(text):
    u"""記録に文・値・要素名・主語の語・枠の id・pointer の字・会社名・docID が無い(禁止の欄の名前・字の形・手書きの語彙の語と要素名)。手がかりの語の表の語は書いてよい(封 §2-6)。"""
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
    table_words = set(w for ws in WORD_TABLE.values() for w in ws)
    body = json.dumps(rec, ensure_ascii=False)
    for word, elems in MS.V.PROFILES[u"P33E"].subjects:
        if len(word) >= 2 and word not in table_words and u'"%s"' % word in body:
            out.append(u"記録に主語の語が在る")
        for e in elems:
            if e in body:
                out.append(u"記録に要素名が在る")
    if re.search(r"xbrl:[A-Za-z]", body) or u"@Current" in body or u"@Prior" in body:
        out.append(u"記録に pointer の字が在る")
    return list(sorted(set(out)))


def recount_problems(rec, ms=None):
    u"""記録の行から集計を数え直して、記録と合わせる(札は本物の読みの記録から)。"""
    ms = ms or MS
    out = []
    rows = rec[u"行"]
    if rec[u"行の欄"] != list(ms.ROW_COLUMNS) or any(len(r) != 10 for r in rows):
        return [u"記録の行の欄・行の欄の数が違う"]
    keys = [tuple(r[:5]) for r in rows]
    if len(set(keys)) != len(keys):
        out.append(u"記録の行の鍵が重なる")
    order = lambda r: (ms.BATCHES.index(r[0]), r[1], ms.SIDE_ORDER[r[0]].index(r[2]), r[3], r[4])
    if rows != sorted(rows, key=order):
        out.append(u"記録の行が(便 → 本の # → 文の種類か節 → 文の番号 → 位置)の順でない")
    for r in rows:
        if r[0] not in ms.BATCHES or r[2] not in ms.SIDE_ORDER[r[0]] or r[5] not in (u"G", u"V") or not isinstance(r[6], bool) or not isinstance(r[3], int) or not isinstance(r[4], int):
            out.append(u"記録の行の形が違う: %s" % (r[:5],))
            break
        if r[6] is False and (r[7] or r[8] or r[9]):
            out.append(u"member が入っている行が止められている: %s" % (r[:5],))
            break
        if not (set(r[7]) <= set(r[8]) <= set(r[9])) or set(r[7]) - set(u"SNU") or set(r[8]) - set(u"SNUH") or set(r[9]) - set(u"SNURKH") or (r[9] == u"" and (r[7] or r[8])):
            out.append(u"当たった類の字が段の包含・各段の許す類に合わない: %s" % (r[:5],))
            break
        if (u"H" in r[7]) or any(r[i] != u"".join(c for c in u"SNURKH" if c in r[i]) for i in (7, 8, 9)):
            out.append(u"当たった類の字が決めた順(SNURKH)・段 1 に H 無しでない: %s" % (r[:5],))
            break
    if rec[K_ALL] != ms.tally_all(rows):
        out.append(u"結んだ行の全部の数が行から数え直した数と違う")
    if rec[K_CLASS] != ms.tally_class(rows):
        out.append(u"当たった類ごとの数が行から数え直した数と違う")
    labels = ms.build_labels(real_recs())
    if rec[K_LABEL] != ms.tally_label(labels, rows):
        out.append(u"札つきの行の数が行・札から数え直した数と違う")
    if rec[K_PRED] != ms.predictions(rows, labels):
        out.append(u"予測の判定に要る数が行・札から数え直した数と違う")
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
    if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"記録の封の path・commit が違う")
    if rec.get(u"この script の sha256") != sha_of(SCRIPT_REL):
        out.append(u"記録の script の sha256 が実物と違う")
    if [(i[u"path"], i[u"sha256"]) for i in rec.get(u"入力", [])] != list(INPUT_SHAS) or any(sha_of(rel) != sha for rel, sha in INPUT_SHAS):
        out.append(u"記録の入力が表・実物と違う")
    if rec.get(u"profile") != u"P33E" or rec.get(u"key_leaks") != []:
        out.append(u"profile か key_leaks が違う")
    rt = load_json(u"fixtures/xbrl/tss_retake/retake_2026-11-18.json")
    fp_rt = collections.OrderedDict((k, rt[u"engine の指紋(今。便 NRE の記録の直した後と同じ)"][k]) for k in ms.FP_KEYS)
    now = rec.get(u"engine の指紋(今。便 RT の記録の今と同じ)")
    if now != fp_rt or now != collections.OrderedDict((k, ms.VD.engine_fingerprint()[k]) for k in ms.FP_KEYS):
        out.append(u"記録の engine の指紋が便 RT の記録の今・今の engine と合わない")
    for k in (K_WIRE, K_ALL, K_LABEL, K_CLASS, K_PRED, u"切り出し", u"手がかりの語の表", u"事業の形", u"段の定義", u"限界", u"行"):
        if k not in rec:
            return out + [u"記録に欄が無い: %s" % k]
    if rec[u"手がかりの語の表"] != collections.OrderedDict((c, list(w)) for c, w in WORD_TABLE.items()) or rec[u"限界"] != list(ms.LIMITS) or rec[u"段の定義"] != ms.STAGE_DEFS:
        out.append(u"記録の手がかりの語の表・限界・段の定義が script・封の字と違う")
    if rec[u"事業の形"][u"基準の字"] != u"事業" or rec[u"事業の形"][u"直後"][:len(BIZ_AFTER) + len(BIZ_CLOSE)] != list(BIZ_AFTER) + list(BIZ_CLOSE):
        out.append(u"記録の事業の形が封の字と違う")
    out.extend(recount_problems(rec, ms))
    # ---- 配線: TSS の行・state ごとの数は便 RT の記録と同じ・G と V の行は結んだ行の数と同じ
    w = rec[K_WIRE][u"TSS の行(便 RT の記録との確かめ)"]
    s1 = rt[u"段 1(第 1 便。400 本の判定)"]
    want = ms.rt_state_counts(rt)
    if w[u"TSS の引き直しの行"] != s1[u"行(後)"] or w[u"TSS の引き直しの行"] != 24531 or dict(w[u"TSS の state ごとの行"]) != dict(want) or w[u"400 本の確かめを掛けた"] is not True:
        out.append(u"記録の TSS の行・state ごとの数が便 RT の記録の段 1(後)と違う")
    tss_rows = [r for r in rec[u"行"] if r[0] == u"TSS"]
    if sum(1 for r in tss_rows if r[5] == u"G") != want[G] or sum(1 for r in tss_rows if r[5] == u"V") != want[VM]:
        out.append(u"記録の TSS の G・V の行の数が便 RT の記録の G・V の数と違う")
    if rec[K_WIRE][u"本の数"] != collections.OrderedDict([(u"TSS", 400), (u"KAM", 201), (u"YS", 201)]):
        out.append(u"記録の本の数が(400・201・201)でない")
    # ---- KAM・YS: 突き合わせの数は行の数と矛盾せず、前の記録の行の数は前の記録の行から
    for batch, rel, key in ((u"KAM", u"fixtures/xbrl/kam/states_2026-11-15.json", u"KAM の行(前の記録との突き合わせ。止めない)"),
                            (u"YS", u"fixtures/xbrl/yuho_sections/states_2026-11-16.json", u"YS の行(前の記録との突き合わせ。止めない)")):
        c = rec[K_WIRE][key][u"全体"]
        prev = load_json(rel)[u"本"]
        sides = ms.SIDE_ORDER[batch]
        n_prev = sum(len(b[s][u"行"]) for b in prev for s in sides)
        if c[u"前の記録の行"] != n_prev or c[u"同じ鍵で同じ state の行"] + c[u"同じ鍵で state が違う行"] + c[u"今の引き直しにだけ在る行"] != c[u"今の引き直しの行"] \
                or c[u"同じ鍵で同じ state の行"] + c[u"同じ鍵で state が違う行"] + c[u"前の記録にだけ在る行"] != c[u"前の記録の行"]:
            out.append(u"%s の前の記録との突き合わせの数が前の記録の行・行の合計と合わない" % batch)
        side_key = u"文の種類別" if batch == u"KAM" else u"節別"
        for f in (u"同じ鍵で同じ state の行", u"同じ鍵で state が違う行", u"今の引き直しにだけ在る行", u"前の記録にだけ在る行", u"前の記録の行", u"今の引き直しの行", u"切り出しの成否が前と違う本 × 側"):
            if sum(rec[K_WIRE][key][side_key][s][f] for s in sides) != c[f]:
                out.append(u"%s の突き合わせの %s の合計が全体と違う" % (batch, f))
        cut = rec[u"切り出し"][batch]
        for s in sides:
            pc = sum(1 for b in prev if b[s][u"切り出し"] == ms.KAM.CUT_OK)
            if cut[s][u"切れた"] + cut[s][u"切れない"] != 201 or (c[u"切り出しの成否が前と違う本 × 側"] == 0 and cut[s][u"切れた"] != pc):
                out.append(u"%s の切り出しの数が前の記録と合わない: %s" % (batch, s))
    # ---- 切り出しの数: TSS は TSS の記録の切り出しと数の claim の合計・KAM と YS は前の記録の側ごとの行の数
    tss_books = load_json(u"fixtures/xbrl/tanshin_self/states_2026-11-14.json")[u"本"]
    ct = rec[u"切り出し"][u"TSS"][ms.NO_SIDE]
    if (ct[u"本"], ct[u"切れた"], ct[u"切れない"], ct[u"数の claim"]) != (400, sum(1 for b in tss_books if b[u"切り出し"] == u"切れた"), sum(1 for b in tss_books if b[u"切り出し"] != u"切れた"), 24531):
        out.append(u"記録の TSS の切り出しの数が TSS の記録の切り出し・便 RT の記録の行(後)24531 と違う")
    for batch, rel in ((u"KAM", u"fixtures/xbrl/kam/states_2026-11-15.json"), (u"YS", u"fixtures/xbrl/yuho_sections/states_2026-11-16.json")):
        prev = load_json(rel)[u"本"]
        for s_ in ms.SIDE_ORDER[batch]:
            cs = rec[u"切り出し"][batch][s_]
            if cs[u"数の claim"] != sum(len(b[s_][u"行"]) for b in prev) or cs[u"本"] != 201:
                out.append(u"記録の %s の %s の数の claim が前の記録の行の数と違う" % (batch, s_))
    pos = rec[K_WIRE][u"位置の確かめ・member の欄・「事業」で終わる前の字(便ごと)"]
    for batch in ms.BATCHES:
        b = pos[batch]
        if b[u"位置を確かめた数の claim(state を問わない)"] != b[u"うち pos の字が数字"] + b[u"うち pos の字が符号か空白"] \
                or b[u"raw の claim に member の欄が在る"] + b[u"raw の claim に member の欄が無い"] != b[u"位置を確かめた数の claim(state を問わない)"]:
            out.append(u"位置の確かめ・member の欄の数が合わない: %s" % batch)
    if pos[u"TSS"][u"位置を確かめた数の claim(state を問わない)"] != 24531:
        out.append(u"TSS で位置を確かめた数が便 RT の記録の行(後)24531 でない(全部の行で確かめる)")
    return out


# ---------------------------------------------------------------- 10. 配線(import・予約名)
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
    if sorted(c.args[0].value for c in loads if c.args and isinstance(c.args[0], ast.Constant)) != sorted(
            ["xbrl_attr_tally_2026-11-17.py", "xbrl_tss_retake_2026-11-18.py", "xbrl_plan_source_2026-11-17.py", "xbrl_yuho_sections_2026-11-16.py"]):
        out.append(u"読む前の便の script が便 AT・RT・PS・YS の 4 本だけでない")
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
    (u"M01 封の commit の定数を替える", u'SEAL_COMMIT = "5b77133b"', u'SEAL_COMMIT = "5b77133c"', ("seal",)),
    (u"M02 記録の path の定数を替える", u'RECORD_REL = REC_DIR_REL + "/stops_2026-11-19.json"', u'RECORD_REL = REC_DIR_REL + "/stops_2026-11-20.json"', ("seal",)),
    (u"M03 入力の表の 1 つの sha256 を替える", u'"a61da3fc3c336e80a214a5fc71978d9ce63f52b4eec5a763e91f434c2ef06d05"', u'"b61da3fc3c336e80a214a5fc71978d9ce63f52b4eec5a763e91f434c2ef06d05"', ("input_sha", "seal_table", "wire_inputs")),
    (u"M04 入力の sha256 の照合を外す", u"if not os.path.isfile(p) or ST.sha256_file(p) != want:", u"if False:", ("wire_inputs",)),
    (u"M05 手がかりの語を 1 つ抜く(セグメント)", u'(u"S", (u"セグメント", u"部門", u"分野")),', u'(u"S", (u"部門", u"分野")),', ("seal", "rules")),
    (u"M06 手がかりの語を 1 つ抜く(単体)", u'(u"N", (u"単体", u"個別", u"提出会社")),', u'(u"N", (u"個別", u"提出会社")),', ("seal", "rules")),
    (u"M07 手がかりの語を 1 つ抜く(内訳)", u'(u"U", (u"うち", u"内訳")),', u'(u"U", (u"うち",)),', ("seal", "rules")),
    (u"M08 手がかりの語を 1 つ抜く(アジア)", u'u"北米", u"米国", u"欧州", u"アジア", u"中国", u"地域")),', u'u"北米", u"米国", u"欧州", u"中国", u"地域")),', ("seal", "rules")),
    (u"M09 手がかりの語を 1 つ抜く(関連会社)", u'(u"K", (u"子会社", u"関連会社"))])', u'(u"K", (u"子会社",))])', ("seal", "rules")),
    (u"M10 事業の形の後ろの字を 1 つ抜く(において)", u'BIZ_AFTER = (u"は", u"では", u"において", u"におきまして",', u'BIZ_AFTER = (u"は", u"では", u"におきまして",', ("seal", "rules")),
    (u"M11 事業の形の後ろの字を 1 つ抜く(の売上)", u'u"について", u"の売上", u"セグメント"', u'u"について", u"セグメント"', ("seal", "rules")),
    (u"M12 事業の形の閉じ括弧を 1 つ抜く(〕)", u'BIZ_CLOSE = (u"]", u")", u"】", u"〕", u">", u"》", u"」")', u'BIZ_CLOSE = (u"]", u")", u"】", u">", u"》", u"」")', ("seal", "rules")),
    (u"M13 事業の形の字の終わりを数えない", u'        if rest == u"" or rest.startswith(BIZ_AFTER) or rest[:1] in BIZ_CLOSE:', u'        if rest.startswith(BIZ_AFTER) or rest[:1] in BIZ_CLOSE:', ("rules",)),
    (u"M14 事業の形が「事業」の最初の 1 つしか見ない", u'        i = text.find(BIZ, i + 1)\n    return False', u'        break\n    return False', ("rules",)),
    (u"M15 S が事業の形を数えない", u'    return cls == u"S" and has_biz_form(text)', u'    return False', ("rules", "stage")),
    (u"M16 事業の形が S 以外にも当たる", u'    return cls == u"S" and has_biz_form(text)', u'    return has_biz_form(text)', ("rules",)),
    (u"M17 N のただし書きを外す", u'    if raw == [u"N"] and any(isinstance(p, str) and NONCONS in p for p in pointers):', u'    if False:', ("rules", "stage", "digest")),
    (u"M18 N のただし書きが N を含む当たり全部に掛かる", u'    if raw == [u"N"] and any(', u'    if u"N" in raw and any(', ("rules", "stage")),
    (u"M19 N のただし書きが pointer の全部が NonConsolidated のときだけ", u'any(isinstance(p, str) and NONCONS in p for p in pointers):\n        return []', u'pointers and all(isinstance(p, str) and NONCONS in p for p in pointers):\n        return []', ("rules",)),
    (u"M20 N のただし書きの字を Consolidated にする", u'NONCONS = u"NonConsolidated"', u'NONCONS = u"Consolidated"', ("seal", "rules")),
    (u"M21 snu_hits が R を数える", u'    raw = [c for c in u"SNU" if has_class(text, c)]', u'    raw = [c for c in u"SNUR" if has_class(text, c)]', ("rules", "stage")),
    (u"M22 段 1 が前の字でなく文の全部を見る", u'    h1 = set(snu_hits(prefix, pointers))', u'    h1 = set(snu_hits(whole, pointers))', ("stage", "digest")),
    (u"M23 段 3 の文の全部が前の字", u'    h3.update(snu_hits(whole, pointers))', u'    h3.update(snu_hits(prefix, pointers))', ("stage", "digest")),
    (u"M24 段 3 の R・K が文の全部", u'    h3.update(c for c in u"RK" if has_class(prefix, c))', u'    h3.update(c for c in u"RK" if has_class(whole, c))', ("stage", "digest")),
    (u"M25 段 3 に R を入れ忘れる", u'    h3.update(c for c in u"RK" if has_class(prefix, c))', u'    h3.update(c for c in u"K" if has_class(prefix, c))', ("stage", "digest")),
    (u"M26 段 3 に K を入れ忘れる", u'    h3.update(c for c in u"RK" if has_class(prefix, c))', u'    h3.update(c for c in u"R" if has_class(prefix, c))', ("stage", "digest")),
    (u"M27 段 2 から見出しを抜く", u'    if heading is not None and has_class(heading, u"S"):\n        h2.add(u"H")', u'    if False:\n        h2.add(u"H")', ("stage", "digest", "orch")),
    (u"M28 段 3 が段 2 を含まない", u'    h3 = set(h2)\n', u'    h3 = set(h1)\n', ("stage", "digest")),
    (u"M29 段 2 が段 1 を含まない", u'    h2 = set(h1)\n    if heading', u'    h2 = set()\n    if heading', ("stage", "digest")),
    (u"M30 見出しが S の語でなく N の語を見る", u'    if heading is not None and has_class(heading, u"S"):', u'    if heading is not None and has_class(heading, u"N"):', ("stage", "digest")),
    (u"M31 見出しの 40 字を 41 字にする", u'HEAD_MAX = 40', u'HEAD_MAX = 41', ("seal", "digest")),
    (u"M32 見出しの 40 字を 39 字にする", u'HEAD_MAX = 40', u'HEAD_MAX = 39', ("seal", "digest")),
    (u"M33 見出しの決めから「。」を外す", u'    return len(sentence) <= HEAD_MAX and not sentence.endswith(HEAD_END)', u'    return len(sentence) <= HEAD_MAX', ("digest",)),
    (u"M34 見出しの決めから長さを外す", u'    return len(sentence) <= HEAD_MAX and not sentence.endswith(HEAD_END)', u'    return not sentence.endswith(HEAD_END)', ("digest",)),
    (u"M35 見出しが数の claim を持つ文も数える", u'    return [i for i, s in enumerate(sentences) if is_heading(s) and i not in num_sentences]', u'    return [i for i, s in enumerate(sentences) if is_heading(s)]', ("digest",)),
    (u"M36 近い見出しでなく最初の見出しを見る", u'        if h < si:\n            best = h\n        else:\n            break', u'        if h < si:\n            best = h if best is None else best\n        else:\n            break', ("digest", "orch")),
    (u"M37 近い見出しが文の番号と同じ見出しも数える", u'        if h < si:\n            best = h', u'        if h <= si:\n            best = h', ("digest",)),
    (u"M38 近い見出しが先の見出しを数える", u'        else:\n            break\n    return best', u'        else:\n            best = h\n            break\n    return best', ("digest",)),
    (u"M39 member が入っていても止める", u'        empty = not r.get(u"member")', u'        empty = True', ("digest", "orch", "job")),
    (u"M40 member の欄が空の判定を取り違える(入っていれば空)", u'        empty = not r.get(u"member")', u'        empty = bool(r.get(u"member"))', ("digest", "orch", "job")),
    (u"M41 前の字が文の全部", u'            prefix = s[:pos]\n', u'            prefix = s\n', ("digest", "orch")),
    (u"M42 前の字が位置の 1 字前まで", u'            prefix = s[:pos]\n', u'            prefix = s[:pos - 1]\n', ("digest",)),
    (u"M43 位置の確かめを外す(数の字で始まるか)", u'    if not POS_RE.match(sentence, pos):\n        return None', u'    if False:\n        return None', ("digest",)),
    (u"M44 位置の確かめの span の照合を外す", u'        if not tail or sentence[pos:pos + len(tail)] != tail:\n            return None', u'        if False:\n            return None', ("digest",)),
    (u"M45 位置の確かめの span の起点を 30 字でなく位置にする", u'        tail = span[min(pos, SPAN_BEFORE):]', u'        tail = span[pos:]', ("digest",)),
    (u"M46 位置の確かめが空白から始まる位置を通さない", u'POS_RE = re.compile(u"(?:△|▲|－|-|マイナス)?\\\\s*\\\\d")', u'POS_RE = re.compile(u"(?:△|▲|－|-|マイナス)?\\\\d")', ("digest",)),
    (u"M47 文の番号が文の列の外でも止めない", u'        if not isinstance(si, int) or not 0 <= si < len(sentences):\n            raise Stop(', u'        if False:\n            raise Stop(', ("digest",)),
    (u"M48 結んだ行に G だけ入れる", u'        if state not in SHORT:\n            continue', u'        if state != G_STATE:\n            continue', ("digest",)),
    (u"M49 結んだ行に G・V でない state も入れる", u'        if state not in SHORT:\n            continue', u'        if False:\n            continue', ("digest",)),
    (u"M50 G と V を取り違える", u'SHORT = {G_STATE: u"G", V_STATE: u"V"}', u'SHORT = {G_STATE: u"V", V_STATE: u"G"}', ("digest", "orch", "job")),
    (u"M51 札の引けた条件から state の一致を外す", u'        elif row[C_STATE] != lab[u"state"]:\n            out.append((lab, None, u"state が違う"))', u'        elif False:\n            out.append((lab, None, u"state が違う"))', ("tally", "orch")),
    (u"M52 札の鍵から本の # を外す", u'    return (lab[u"便"], lab[u"#"], lab[u"側"], lab[u"si"], lab[u"pos"])', u'    return (lab[u"便"], 0, lab[u"側"], lab[u"si"], lab[u"pos"])', ("tally", "orch")),
    (u"M53 札の鍵から文の種類か節を外す", u'    return (lab[u"便"], lab[u"#"], lab[u"側"], lab[u"si"], lab[u"pos"])', u'    return (lab[u"便"], lab[u"#"], None, lab[u"si"], lab[u"pos"])', ("tally", "orch")),
    (u"M54 札の鍵の文の番号と位置を取り違える", u'    return (lab[u"便"], lab[u"#"], lab[u"側"], lab[u"si"], lab[u"pos"])', u'    return (lab[u"便"], lab[u"#"], lab[u"側"], lab[u"pos"], lab[u"si"])', ("tally", "orch")),
    (u"M55 引けなかった行を分母に入れる", u'    got = [m[1] for m in matched if m[1] is not None]\n    why =', u'    got = [m[1] for m in matched]\n    why =', ("tally", "orch")),
    (u"M56 引けなかった行を止めた行に数える", u'               (u"止めた行", od((STAGE_NAMES[t], sum(1 for r in got if stopped(r, t))) for t in STAGES))])', u'               (u"止めた行", od((STAGE_NAMES[t], sum(1 for m in matched if m[1] is None or stopped(m[1], t))) for t in STAGES))])', ("tally",)),
    (u"M57 範囲と範囲でないを取り違える", u'    rng = [m for m in ms if is_range(m[0])]\n    non = [m for m in ms if not is_range(m[0]) and not is_drop(m[0])]', u'    non = [m for m in ms if is_range(m[0])]\n    rng = [m for m in ms if not is_range(m[0]) and not is_drop(m[0])]', ("tally", "orch")),
    (u"M58 範囲でないに分母から除く札を入れる", u'    non = [m for m in ms if not is_range(m[0]) and not is_drop(m[0])]', u'    non = [m for m in ms if not is_range(m[0])]', ("tally", "orch")),
    (u"M59 範囲が属性の範囲でなく外も含む", u'    return lab[u"種別"] == AT.KIND_IN and lab[u"先"] == u"範囲"', u'    return lab[u"種別"] == AT.KIND_IN and lab[u"先"] in (u"範囲", u"期")', ("tally",)),
    (u"M60 分母から除く札の判定を外す", u'    return lab[u"種別"] == AT.KIND_DROP', u'    return False', ("tally", "orch")),
    (u"M61 V の札と G の札を取り違える", u'        if lab[u"state"] == u"V":\n            vms[lab[u"便"]].append((lab, row, why))', u'        if lab[u"state"] == u"G":\n            vms[lab[u"便"]].append((lab, row, why))', ("tally", "orch")),
    (u"M62 G の札の state を V にする", u'            state = u"V" if g.startswith(u"V") else u"G"', u'            state = u"V"', ("label", "orch")),
    (u"M63 札の読みの組から文の種類を取り違える(連結と単体)", u'            side = READ_SETS[batch][g][0]', u'            side = u"単体" if READ_SETS[batch][g][0] == u"連結" else READ_SETS[batch][g][0]', ("label", "orch")),
    (u"M64 b の違うものが範囲(字のとおり)に側も入る", u'(u"b の違うものが範囲(字のとおり)", cell([m for m in b if m[0][u"違うもの"] == u"範囲"]))', u'(u"b の違うものが範囲(字のとおり)", cell([m for m in b if m[0][u"違うもの"] in (u"範囲", u"側")]))', ("tally",)),
    (u"M65 b の違うものが範囲か側が範囲だけ", u'cell([m for m in b if AT.DIFF_TO_ATTR[m[0][u"違うもの"]] == u"範囲"]))])', u'cell([m for m in b if m[0][u"違うもの"] == u"範囲"]))])', ("tally",)),
    (u"M66 SC-1 の分母が札の行", u'    out[u"SC-1 段 2 で「範囲」の札の V の行(3 便の合計)のうち止めた行 / 引けた行(段 1・3 も並べる)"] = od([\n        (u"3 便の合計", fr(rng))]', u'    out[u"SC-1 段 2 で「範囲」の札の V の行(3 便の合計)のうち止めた行 / 引けた行(段 1・3 も並べる)"] = od([\n        (u"3 便の合計", fr(rng_b[u"KAM"]))]', ("tally", "orch")),
    (u"M67 SC-2 が G の a でなく b を見る", u'    a_b = dict((b, [m for m in gms[b] if m[0][u"型"] == u"a"]) for b in (u"KAM", u"YS"))', u'    a_b = dict((b, [m for m in gms[b] if m[0][u"型"] == u"b"]) for b in (u"KAM", u"YS"))', ("tally",)),
    (u"M68 SC-4a が G でなく V の行", u'    tss_g = [r for r in tss if r[C_STATE] == u"G"]', u'    tss_g = [r for r in tss if r[C_STATE] == u"V"]', ("tally",)),
    (u"M69 SC-4b が V でなく G の行", u'    tss_v = [r for r in tss if r[C_STATE] == u"V"]', u'    tss_v = [r for r in tss if r[C_STATE] == u"G"]', ("tally",)),
    (u"M70 SC-5 の率の差が逆向き", u'    return RT.point_diff(cb[t], db, ca[t], da)', u'    return RT.point_diff(ca[t], da, cb[t], db)', ("tally",)),
    (u"M71 SC-3 の段 1 と段 3 の取り違え", u'(u"段 1 の止めた行", c_all[1][1]), (u"段 3 の止めた行", c_all[1][3]),', u'(u"段 1 の止めた行", c_all[1][3]), (u"段 3 の止めた行", c_all[1][1]),', ("tally",)),
    (u"M72 当たった類の数が止めた行の全部でなく段 1 の行", u'    hit = [r for r in rows if stopped(r, t)]', u'    hit = [r for r in rows if stopped(r, 1)]', ("tally",)),
    (u"M73 当たった類が複数でも 1 つにしか数えない", u'    return od([(u"止めた行", len(hit))] + [(c, sum(1 for r in hit if c in r[C_HIT[t]])) for c in CLASS_ORDER])', u'    return od([(u"止めた行", len(hit))] + [(c, sum(1 for r in hit if r[C_HIT[t]][:1] == c)) for c in CLASS_ORDER])', ("tally",)),
    (u"M74 当たった類の state を取り違える", u'od((s, class_counts([r for r in br if r[C_STATE] == s], t)) for s in GV)) for t in STAGES)', u'od((s, class_counts([r for r in br if r[C_STATE] != s], t)) for s in GV)) for t in STAGES)', ("tally",)),
    (u"M75 結んだ行の止めた行が段を取り違える", u'               (u"止めた行", od((STAGE_NAMES[t], sum(1 for r in rows if stopped(r, t))) for t in STAGES))])\n\n\ndef tally_all', u'               (u"止めた行", od((STAGE_NAMES[t], sum(1 for r in rows if stopped(r, 3 - t + 1))) for t in STAGES))])\n\n\ndef tally_all', ("tally", "orch")),
    (u"M76 結んだ行の文の種類別が側を取り違える", u'                (side, od((s, stage_cells([r for r in br if r[C_SIDE] == side and r[C_STATE] == s])) for s in GV)) for side in SIDE_ORDER[batch])', u'                (side, od((s, stage_cells([r for r in br if r[C_SIDE] != side and r[C_STATE] == s])) for s in GV)) for side in SIDE_ORDER[batch])', ("tally",)),
    (u"M77 結んだ行の便ごとの数が便を取り違える", u'        br = [r for r in rows if r[C_BATCH] == batch]\n        b = od(', u'        br = [r for r in rows if r[C_BATCH] != batch]\n        b = od(', ("tally",)),
    (u"M78 link_rows が文の種類か節を落とす", u'            rows.append([b[u"便"], b[u"#"], side] + list(r))', u'            rows.append([b[u"便"], b[u"#"], None] + list(r))', ("orch",)),
    (u"M79 link_rows が便の順を取り違える", u'    for b in sorted(books, key=lambda b: (BATCHES.index(b[u"便"]), b[u"#"])):', u'    for b in sorted(books, key=lambda b: (-BATCHES.index(b[u"便"]), b[u"#"])):', ("orch",)),
    (u"M80 job が KAM を YS の切り出しで処理する", u'UNITS_OF = {u"TSS": tss_units, u"KAM": kam_units, u"YS": ys_units}', u'UNITS_OF = {u"TSS": tss_units, u"KAM": ys_units, u"YS": kam_units}', ("job",)),
    (u"M81 KAM の job が連結と単体の順を取り違える", u'    for side in KAM.SIDES:\n        text = KAM.cut_kam(zb, side)[0]', u'    for side in reversed(list(KAM.SIDES)):\n        text = KAM.cut_kam(zb, side)[0]', ("job",)),
    (u"M82 TSS の job が包んだ ZIP でなく元の ZIP を渡す", u'    return [(None, unit_digest(PS.claims_of(wrapped), sentences_of(wrapped)))]', u'    return [(None, unit_digest(PS.claims_of(zb), sentences_of(zb)))]', ("job",)),
    (u"M83 KAM の job が書き換えた ZIP でなく元の ZIP を渡す", u'        out.append((side, unit_digest(PS.claims_of(zm), sentences_of(zm))))\n    return out\n\n\ndef ys_units', u'        out.append((side, unit_digest(PS.claims_of(zb), sentences_of(zb))))\n    return out\n\n\ndef ys_units', ("job",)),
    (u"M84 job が材料の sha256 を確かめない", u'    if ST.sha256_bytes(zb) != sha:\n        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)\n    return zb', u'    return zb', ("job",)),
    (u"M85 job が材料が無くても止めない", u'    if not os.path.exists(path):\n        raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)\n    with io.open(path, "rb") as fh:\n        zb = fh.read()\n    if ST.sha256_bytes', u'    with io.open(path, "rb") as fh:\n        zb = fh.read()\n    if ST.sha256_bytes', ("job",)),
    (u"M86 TSS の行の確かめを常に外す", u'    if full and (len(tr) != want_rows or now != want):', u'    if False:', ("wire", "default")),
    (u"M87 TSS の行の確かめが state ごとの数を見ない", u'    if full and (len(tr) != want_rows or now != want):', u'    if full and len(tr) != want_rows:', ("wire", "default")),
    (u"M88 TSS の行の確かめが行の数を見ない", u'    if full and (len(tr) != want_rows or now != want):', u'    if full and now != want:', ("wire",)),
    (u"M89 rt_state_counts が群を足さない", u'    for g in groups.values():\n        for s, k in g[u"4 state"].items():\n            c[s] += k', u'    for g in list(groups.values())[:1]:\n        for s, k in g[u"4 state"].items():\n            c[s] += k', ("wire", "default")),
    (u"M90 400 本の経路の期待の行の数が 1 ずれる", u'    want_rows = rt_rec[u"段 1(第 1 便。400 本の判定)"][u"行(後)"]', u'    want_rows = rt_rec[u"段 1(第 1 便。400 本の判定)"][u"行(後)"] - 1', ("default",)),
    (u"M91 前の記録との突き合わせが state を見ない", u'        same = sum(1 for k in ks_n if k in prev and prev[k] == now[k])', u'        same = sum(1 for k in ks_n if k in prev)', ("wire", "orch")),
    (u"M92 前の記録との突き合わせの鍵に本の # を入れない", u'                out[(b[u"#"], side, r[0], r[1])] = r[2]', u'                out[(0, side, r[0], r[1])] = r[2]', ("wire", "orch")),
    (u"M93 前の記録との突き合わせの鍵に文の種類を入れない", u'                out[(b[u"#"], side, r[0], r[1])] = r[2]', u'                out[(b[u"#"], None, r[0], r[1])] = r[2]', ("wire", "orch")),
    (u"M94 前の記録との突き合わせが今と前を取り違える", u'                   (u"今の引き直しにだけ在る行", sum(1 for k in ks_n if k not in prev)), (u"前の記録にだけ在る行", sum(1 for k in ks_p if k not in now)),', u'                   (u"今の引き直しにだけ在る行", sum(1 for k in ks_p if k not in now)), (u"前の記録にだけ在る行", sum(1 for k in ks_n if k not in prev)),', ("wire", "orch")),
    (u"M95 engine の指紋が違っても止めない", u'    if now != want:', u'    if False:', ("fp", "orch")),
    (u"M96 engine の指紋の比較が 1 欄だけ", u'    if now != want:', u"    if now['core_py_files'] != want['core_py_files']:", ("fp",)),
    (u"M97 材料の置き場の変化を見ない", u'    if before_tss != ST.names_snapshot(mat) or before_cache != folder_snapshots(base):', u'    if False:', ("orch",)),
    (u"M98 KAM・YS の置き場の変化を見ない", u'    if before_tss != ST.names_snapshot(mat) or before_cache != folder_snapshots(base):', u'    if before_tss != ST.names_snapshot(mat):', ("orch",)),
    (u"M99 job の順が YS・KAM", u'    jobs += [(u"KAM", n, g, sha, kam_found[sha][0]) for (n, g, sha) in kam_pop]\n    jobs += [(u"YS", n, g, sha, ys_found[sha][0]) for (n, g, sha) in ys_pop]', u'    jobs += [(u"YS", n, g, sha, ys_found[sha][0]) for (n, g, sha) in ys_pop]\n    jobs += [(u"KAM", n, g, sha, kam_found[sha][0]) for (n, g, sha) in kam_pop]', ("orch", "default")),
    (u"M101 母集団の記録との照合を外す", u'    if [list(r[:3]) for r in rec[u"行"]] != [[r[0], r[1], r[2]] for r in pop]:', u'    if False:', ("wire",)),
    (u"M102 通信の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport urllib.request\n", ("import",)),
    (u"M103 許す一覧の外の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport shutil\n", ("import",)),
    (u"M104 前の便の script を 1 本足して読む(行を足す)", u"PS = load_module(", u"def unused_loader():\n    return load_module(\"xbrl_nil_read_2026-11-17.py\", \"nr_for_sc\")\n\n\nPS = load_module(", ("import",)),
    (u"M105 check_text が漏れの検査を呼ばない", u'    TSS.check_clean(rec, scan, key_value)', u'    pass', ("clean",)),
    (u"M106 手がかりの語の表の S に「事業」を足す(封と違う語)", u'(u"S", (u"セグメント", u"部門", u"分野")),', u'(u"S", (u"セグメント", u"部門", u"分野", u"事業")),', ("seal", "rules")),
)


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"seal_table": seal_table_problems, u"input_sha": input_sha_problems, u"wire_inputs": input_wire_problems, u"rules": rule_problems, u"stage": stage_problems,
             u"digest": digest_problems, u"label": label_problems, u"tally": tally_problems, u"wire": wire_problems, u"job": job_problems, u"orch": orchestrate_problems,
             u"default": default_path_problems, u"fp": fingerprint_problems, u"clean": check_text_problems}
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


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_tables_equal_the_seal(self):
        self.assertEqual([], seal_problems())
        self.assertEqual([], seal_table_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"SC-6", u"SC-8")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"「個別」", u"「別個」")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"「について」", u"「にて」")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"`〕`", u"`｝`")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"長さが 40 字以下", u"長さが 41 字以下")))
        self.assertNotEqual([], seal_table_problems(seal=seal.replace(INPUT_SHAS[0][1], u"0" * 64)))


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
        self.assertNotEqual([], engine_zero_problems(r.d))
        r2, _s = self._repo()
        r2.put("core/py/audit_core/x.py")
        r2.commit("core/py/audit_core/x.py")
        self.assertNotEqual([], engine_zero_problems(r2.d))
        r3, _s = self._repo()
        r3.put("adapters/xbrl/instance.py", text=u"z\n")
        self.assertNotEqual([], engine_zero_problems(r3.d))

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
        r.put("fixtures/new.json")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["fixtures/new.json"]))
        r2 = PR.Repo()
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["measure/s.py"]))

    def test_d_3_the_order_check_lists_the_script_the_gate_and_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))


class RuleTest(unittest.TestCase):
    def test_e_1_the_words_the_business_form_and_the_nonconsolidated_proviso(self):
        self.assertEqual([], rule_problems())

    def test_e_2_the_three_stages_include_each_other_and_use_the_right_text(self):
        self.assertEqual([], stage_problems())

    def test_e_3_the_digest_headings_nearest_heading_member_and_position(self):
        self.assertEqual([], digest_problems())


class LabelTest(unittest.TestCase):
    def test_f_1_the_labels_come_from_the_real_read_records_and_map_to_the_right_side_and_attribute(self):
        self.assertEqual([], label_problems())

    def test_f_2_the_tallies_use_only_the_rows_found_in_the_same_state(self):
        self.assertEqual([], tally_problems())


class WireTest(unittest.TestCase):
    def test_g_1_the_wiring_checks_stop_and_the_comparison_counts_are_by_hand(self):
        self.assertEqual([], wire_problems())

    def test_g_2_the_book_job_keeps_the_batches_sides_and_sections_apart(self):
        self.assertEqual([], job_problems())

    def test_g_3_orchestrate_on_made_up_books_equals_the_hand_computation_and_stops(self):
        u"""作り物の本(TSS 3・KAM 2・YS 2)で ``orchestrate`` を本物のまま走らせる。便・state・段・文の種類・節で非対称。"""
        self.assertEqual([], orchestrate_problems())

    def test_g_4_the_default_path_without_explicit_arguments(self):
        self.assertEqual([], default_path_problems())

    def test_g_5_the_engine_fingerprint_stops_on_any_of_its_four_fields(self):
        self.assertEqual([], fingerprint_problems())

    def test_g_6_check_text_stops_on_a_leak(self):
        self.assertEqual([], check_text_problems())


class RecordTest(unittest.TestCase):
    def test_h_1_the_record_has_the_sealed_fields_and_equals_the_recount_from_its_rows(self):
        self.assertEqual([], record_problems())

    def test_h_2_a_record_with_one_number_changed_is_red(self):
        text = read(RECORD_REL)

        def changed(fn):
            r = json.loads(text, object_pairs_hook=collections.OrderedDict)
            fn(r)
            return record_problems(text=json.dumps(r, ensure_ascii=False))

        self.assertNotEqual([], changed(lambda r: r[u"入力"][0].__setitem__(u"sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r.__setitem__(u"この script の sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r[K_WIRE][u"TSS の行(便 RT の記録との確かめ)"].__setitem__(u"TSS の引き直しの行", 24530)))
        self.assertNotEqual([], changed(lambda r: r[K_WIRE][u"KAM の行(前の記録との突き合わせ。止めない)"][u"全体"].__setitem__(u"同じ鍵で同じ state の行", r[K_WIRE][u"KAM の行(前の記録との突き合わせ。止めない)"][u"全体"][u"同じ鍵で同じ state の行"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_ALL][u"TSS"][u"全体"][u"V"].__setitem__(u"結んだ行", r[K_ALL][u"TSS"][u"全体"][u"V"][u"結んだ行"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_ALL][u"KAM"][u"全体"][u"G"][u"止めた行"].__setitem__(S2, r[K_ALL][u"KAM"][u"全体"][u"G"][u"止めた行"][S2] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_CLASS][u"合計"][S3][u"G"].__setitem__(u"S", r[K_CLASS][u"合計"][S3][u"G"][u"S"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_LABEL][u"V の札"][u"合計"][u"範囲"][u"止めた行"].__setitem__(S2, r[K_LABEL][u"V の札"][u"合計"][u"範囲"][u"止めた行"][S2] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_LABEL][u"G の札(KAM・YS)"][u"合計"][u"型ごと"][u"a"].__setitem__(u"引けた行(分母)", 0)))
        self.assertNotEqual([], changed(lambda r: list(r[K_PRED].values())[0][u"3 便の合計"][S2].__setitem__(u"分子", 0)))
        self.assertNotEqual([], changed(lambda r: r[u"行"].pop()))
        self.assertNotEqual([], changed(lambda r: r[u"行"][0].__setitem__(8, u"SNURKH")))
        self.assertNotEqual([], changed(lambda r: r[u"行"][0].__setitem__(6, not r[u"行"][0][6])))
        self.assertNotEqual([], changed(lambda r: r[u"engine の指紋(今。便 RT の記録の今と同じ)"].__setitem__(u"core_py_sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r.__setitem__(u"限界", r[u"限界"][:-1])))
        self.assertNotEqual([], changed(lambda r: r[u"手がかりの語の表"][u"S"].pop()))
        self.assertNotEqual([], changed(lambda r: r[u"切り出し"][u"TSS"][u"(文の種類なし)"].__setitem__(u"切れた", r[u"切り出し"][u"TSS"][u"(文の種類なし)"][u"切れた"] + 1)))

    def test_h_3_a_record_with_a_sentence_a_value_an_element_name_or_a_subject_word_is_red(self):
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"要素名"] = u"jppfs_cor:NetSales"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"文"] = u"売上高は増加した"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"TSS の置き場"] = u"S100" + u"ABCD"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"x"] = u"売上高"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"x"] = u"Revenue"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"x"] = u"xbrl:jppfs_cor:Assets@CurrentYearInstant"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"pointers"] = []
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        self.assertEqual([], leak_problems(read(RECORD_REL)))
        self.assertFalse(DOCID_RE.search(read(RECORD_REL)))


class WiringTest(unittest.TestCase):
    def test_i_1_the_script_imports_only_the_allowed_modules(self):
        self.assertEqual([], import_problems())

    def test_i_2_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with open(p, encoding="utf-8") as fh:
            self.assertNotIn(u"scope_cond", fh.read())

    def test_i_3_the_script_has_no_network_key_or_llm(self):
        src = read(SCRIPT_REL)
        for bad in (u"socket", u"urllib", u"ANTHROPIC", u"API_KEY", u"requests"):
            self.assertNotIn(bad, src)

    def test_i_4_the_gate_does_not_use_the_reserved_names_and_has_no_docid(self):
        self.assertEqual([], reserved_problems())
        self.assertIsNone(DOCID_RE.search(read(GATE_REL)))
        self.assertIsNone(DOCID_RE.search(read(SCRIPT_REL)))

    def test_i_5_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("SC_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rel="g.py", base=d))

    def test_i_6_the_script_leaves_sys_modules_as_it_found_them(self):
        u"""前の便の script を読んでも、読み込みの前に居た名前を上書きしたまま残さない(門を 2 通りの順で走らせても赤くならない)。"""
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "scope_cond_script_for_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        self.assertIn("scope_cond_script_for_sysmodules_check", sys.modules)
        del mod


class MutantTest(unittest.TestCase):
    def test_j_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        modules_before = dict(sys.modules)
        results = run_mutants()
        after = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        self.assertEqual(before, after)
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))

    def test_j_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in (u"seal", u"seal_table", u"input_sha", u"wire_inputs", u"rules", u"stage", u"digest", u"label", u"tally", u"wire", u"job", u"orch", u"default", u"fp", u"clean", u"import"):
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
