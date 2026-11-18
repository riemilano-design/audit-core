# -*- coding: utf-8 -*-
"""封 docs/XBRL_SUMMARY_ENGINE_SEAL_2026-11-18.md(SE ― サマリーを engine に渡したときに動く行と、engine の語彙が予想の枠の fact に届くか)の門。封 §6。

**この門が縛るもの**

1. 封の字: 封の commit(fabd87ba)・path・要点の字・札の順が script の定数と同じ。封の file は commit した blob と 1 字も変わっていない。
2. 入力 9 件の sha256 が封の表・script の表・門の表・実物で同じ。入力の確かめは 1 byte 違う複製で止まる。前の便の封・結果の文書は封の commit から 0 行。
3. engine は封の commit から 0 行(``core/``・``adapters/``)。作業木にも engine の未 commit の変更が無い。
4. 順序: 封の commit ⊏ script・この門・記録を足した commit(未 commit は赤)。
5. **札の付け方**(封 §2-4): 8 つの順・完全一致が在れば部分一致を見ない・読み 2 通り・対照(別の本の F)を作り物の入力で本物のまま走らせる。
   ``instance.facts_for`` の名前の選び方と同じ答えを返すこと。
6. **段 1 の突き合わせ**: 前と後を鍵で結び、pointer の並びだけが違う行を「state が変わった行」に数えない。非対称な例(前と後・前にだけ・後にだけ・群を取り違えると数が変わる)。
7. **つなぐ配線**: ``after_zip``(「後」の ZIP にサマリーを 1 byte も変えず足す)・``book_job``(前と後を取り違えない・F・fact の個数)・
   ``orchestrate``(作り物の本で本物のまま走らせ、対照が別の本の F・読みが取り違えられない・配線の確認が止める)。
8. 記録 ``fixtures/xbrl/summary_engine/states_2026-11-18.json``: 封の字・script の sha256・入力・指紋(今 = 今の engine = 便 RT の記録の今)・
   段 2 の数が行から数え直せる・予測の判定に要る数が段の数から作り直せる・便 PS の記録の行(当てない・字のとおりの自)と合う・文や値や要素名や主語の語を持たない。
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
import zipfile
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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_se_seal")       # 順序・履歴の部品。門としては走らせない
MS = load_module("measure/xbrl_summary_engine_2026-11-18.py", "summary_engine_script_for_seal_gate")

SEAL_REL = "docs/XBRL_SUMMARY_ENGINE_SEAL_2026-11-18.md"
SEAL_COMMIT_SHORT = "fabd87ba"               # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_summary_engine_2026-11-18.py"
GATE_REL = "tests/measure/test_xbrl_summary_engine_seal.py"
RECORD_REL = "fixtures/xbrl/summary_engine/states_2026-11-18.json"
ORDER_FILES = (SCRIPT_REL, GATE_REL, RECORD_REL)
#: 入力の表(literal。封の表・script の表・実物と照らす)
INPUT_SHAS = (
    ("fixtures/xbrl/tss_retake/retake_2026-11-18.json", "34845f1b3772993aebc0a48d1cec0f6ee5889f9f66843a88f94e572392263cd7"),
    ("fixtures/xbrl/plan_source/read_types_2026-11-17.json", "c244d1bf51e7867e1772f98bd6d4c0085fa816faf1ec09f7855050aa99fe5e56"),
    ("measure/xbrl_plan_source_2026-11-17.py", "0617d75a98e9aca390426b2751bed5ae40a8aa8759b3e80bffab163e1abeb8ea"),
    ("measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    ("measure/xbrl_tss_retake_2026-11-18.py", "4d1c4276f67f2fd5551ba0372b2a09c07a2ee4c493b09942e3f360ee35e5b82e"),
    ("adapters/xbrl/recipes.py", "346adb0d586e3af233b381f721c3512eea02809c287e02aa948bb0d04031e403"),
    ("adapters/xbrl/instance.py", "1b8c00f86eafe765ce44be9ee93cc9ff7a492bd119074e9aa8f49e13e4970cd8"),
    ("adapters/xbrl/vocabulary.py", "369891933a5876c4a942e59b85b500d7fa2aa826f8b0c95e2b1c905623b3806c"),
    ("adapters/xbrl/extract.py", "a61da3fc3c336e80a214a5fc71978d9ce63f52b4eec5a763e91f434c2ef06d05"))
INPUT_RELS = tuple(rel for rel, _sha in INPUT_SHAS)
#: 前の便の封・結果の文書(封の commit から 0 行)
PRIOR_DOCS = (
    "docs/XBRL_PLAN_SOURCE_SEAL_2026-11-17.md", "docs/XBRL_PLAN_SOURCE_RESULT_2026-11-17.md", "docs/XBRL_TSS_RETAKE_SEAL_2026-11-18.md", "docs/XBRL_TSS_RETAKE_RESULT_2026-11-18.md")
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "io", "json", "os", "sys", "time", "zipfile")
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
G, VM, UN, PN = STATES
LABELS = (u"当てない", u"F が空", u"主語なし", u"語彙の外", u"両方", u"値だけ", u"名前だけ", u"どちらも無し")
L_NA, L_FE, L_NS, L_OV, L_BOTH, L_VAL, L_NAME, L_NONE = LABELS
EXACT, LOOSE = u"完全一致", u"部分一致"
REASON_P = u"target_or_plan"
K_RT = u"配線の確認(封 §2-2。予測ではない。違えば止まる)"
K_S1 = u"段 1(サマリーを足したときに動く行)"
K_S2 = u"段 2(engine の語彙は予想の枠の fact に届くか)"
K_PRED = u"予測の判定に要る数(SE-1〜SE-7。当たり・外れは結果の文書で)"
K_FG = u"fact の個数の確かめ(SE-2a の欠陥の確認)"
LIT, FAM = u"字のとおり", u"円の族"


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
    mod = types.ModuleType("summary_engine_mutant")
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


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    for phrase in (u"SE-1", u"SE-2a", u"SE-2b", u"SE-3", u"SE-4", u"SE-5", u"SE-6", u"SE-7", u"fixtures/xbrl/summary_engine/states_2026-11-18.json", u"measure/xbrl_summary_engine_2026-11-18.py",
                   u"target_or_plan", u"profile は `P33E`", u"両方(他)", u"完全一致が 1 つでも在れば部分一致は見ない", u"summary_ixbrl.htm", u"794"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    for i, lab in enumerate(LABELS, 1):
        if u"%d. %s" % (i, lab) not in seal:
            out.append(u"封の札 %d が「%s」でない" % (i, lab))
    if tuple(ms.LABELS) != LABELS:
        out.append(u"script の札の順が封の札の順(8 つ)でない")
    if (ms.PROFILE, ms.REASON_P, ms.EXPECT_P, ms.EXPECT_READ_ROWS, ms.SUMMARY_NAME) != (u"P33E", REASON_P, 794, 90, u"XBRL/PublicDoc/summary_ixbrl.htm"):
        out.append(u"profile・P の reason・P の行の数・読みの軸の行の数・「後」のサマリーの名前が封と違う")
    if tuple(ms.STATES) != STATES or tuple(ms.READINGS) != (LIT, FAM):
        out.append(u"state の名か読みの名が違う")
    if (ms.K_RT, ms.K_S1, ms.K_S2, ms.K_PRED) != (K_RT, K_S1, K_S2, K_PRED):
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
    u"""封の file の履歴は 1 commit(fabd87ba)で、今の file はその commit の blob と 1 字も変わらない。"""
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
    tmp = tempfile.mkdtemp(prefix="se_inputs_")
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


# ---------------------------------------------------------------- 4. 札の付け方(封 §2-4)
VOC = ((u"売上", [u"NetSales", u"Revenue"]), (u"売上", [u"OperatingRevenues"]), (u"利益", [u"Profit"]))


def C(subject, unit, value, us=1, cs=1, tol=None):
    return {u"subject": subject, u"unit": unit, u"value": value, u"unit_scale": us, u"claim_scale": cs, u"pct_tolerance": tol}


def label_problems(ms=None):
    ms = ms or MS
    out = []
    lab = lambda claim, rd, facts: ms.label_claim(claim, rd, facts, VOC)
    yen = C(u"売上", u"円", 1234)
    f_exact = (u"jppfs_cor:NetSales", u"JPY", 1234)
    # ---- 1 当てない が 2 F が空 より先
    if lab(C(u"売上", u"円", 0), LIT, [])[0] != L_NA or lab(C(u"売上", u"その他", 5), LIT, [f_exact])[0] != L_NA:
        out.append(u"札 1 当てない(値が 0・単位が円と % でない)が F が空より先でない")
    if lab(C(u"売上", u"百万円", 100, 1000000, 1000000), LIT, [(u"a:NetSales", u"JPY", 100000000)])[0] != L_NA:
        out.append(u"字のとおりの読みで 百万円 が当てない行でない")
    if lab(C(u"売上", u"百万円", 100, 1000000, 1000000), FAM, [(u"a:NetSales", u"JPY", 100000000)]) != (L_BOTH, True, EXACT):
        out.append(u"円の族の読みで 百万円 が両方(完全一致)でない")
    if lab(C(u"売上", u"円", 5, None, 1), LIT, [f_exact])[0] != L_NA:
        out.append(u"円で unit_scale が無い行が当てない行でない")
    # ---- 2 F が空 が 3 主語なし より先
    if lab(C(u"", u"円", 1234), LIT, []) != (L_FE, False, None) or lab(yen, LIT, []) != (L_FE, False, None):
        out.append(u"札 2 F が空が主語なしより先でない")
    # ---- 3 主語なし・4 語彙の外(副: F のどれかに値が合うか)
    if lab(C(u"", u"円", 1234), LIT, [f_exact]) != (L_NS, True, None) or lab(C(None, u"円", 1234), LIT, [(u"a:Other", u"JPY", 1)]) != (L_NS, False, None):
        out.append(u"札 3 主語なしと副(値が合うか)が違う")
    if lab(C(u"売", u"円", 1234), LIT, [f_exact]) != (L_OV, True, None) or lab(C(u"売上高", u"円", 1), LIT, [f_exact]) != (L_OV, False, None):
        out.append(u"札 4 語彙の外(語が字で同じでない)と副が違う")
    # ---- 5 両方(完全一致・部分一致・要素名の合わせ・大文字小文字・SummaryOfBusinessResults)
    if lab(yen, LIT, [f_exact, (u"a:Other", u"JPY", 99)]) != (L_BOTH, True, EXACT):
        out.append(u"札 5 両方(完全一致)が違う")
    if lab(yen, LIT, [(u"a:OperatingRevenues", u"JPY", 1234)]) != (L_BOTH, True, EXACT):
        out.append(u"同じ語の 2 組の要素名が合わさっていない")
    if lab(yen, LIT, [(u"a:xREVENUEy", u"JPY", 1234)]) != (L_BOTH, True, LOOSE):
        out.append(u"札 5 両方(部分一致。小文字にして含む)が違う")
    if lab(yen, LIT, [(u"a:NetSalesSummaryOfBusinessResults", u"JPY", 1234), (u"a:xRevenuey", u"JPY", 1)]) != (L_BOTH, True, EXACT):
        out.append(u"SummaryOfBusinessResults つきの名前が完全一致でない")
    if lab(C(u"利益", u"円", 1234), LIT, [(u"a:ProfitSummaryOfBusinessResults", u"JPY", 1234)]) != (L_BOTH, True, EXACT):
        out.append(u"別の語の要素名が使われていない")
    # ---- 完全一致が在れば部分一致は見ない(値が合うのは部分一致の側だけ → 両方でなく 値だけ)
    if lab(yen, LIT, [(u"a:NetSales", u"JPY", 1), (u"a:xRevenuey", u"JPY", 1234)]) != (L_VAL, True, EXACT):
        out.append(u"完全一致が在るのに部分一致も見ている(値だけ・完全一致 のはず)")
    # ---- 6 値だけ・7 名前だけ・8 どちらも無し
    if lab(yen, LIT, [(u"a:Other", u"JPY", 1234)]) != (L_VAL, True, None):
        out.append(u"札 6 値だけ(N が空でもよい)が違う")
    if lab(yen, LIT, [(u"a:NetSales", u"JPY", 1)]) != (L_NAME, False, EXACT):
        out.append(u"札 7 名前だけが違う")
    if lab(yen, LIT, [(u"a:Zzz", u"JPY", 1)]) != (L_NONE, False, None):
        out.append(u"札 8 どちらも無しが違う")
    # ---- % の claim
    pct = C(u"売上", u"%", 5.0, None, None)
    if lab(pct, LIT, [(u"a:NetSales", u"Pure", 0.05)]) != (L_BOTH, True, EXACT) or lab(pct, LIT, [(u"a:NetSales", u"JPY", 0.05)])[0] != L_NAME:
        out.append(u"% の claim の照合(単位 Pure)が違う")
    # ---- 非対称(自分の本の F と別の本の F で札が違う。対照を自分の本の F にすると変わる)
    f_self = [(u"a:NetSales", u"JPY", 555)]
    f_other = [(u"a:NetSales", u"JPY", 1234)]
    r = ms.row_labels(yen, f_self, f_other, VOC)
    if r != [L_NAME, False, EXACT, L_BOTH] * 2:
        out.append(u"row_labels が(読みごとの 札・値が合う・届き方・札(他))の並びでない: %s" % (r,))
    r2 = ms.row_labels(C(u"売上", u"百万円", 100, 1000000, 1000000), [(u"a:NetSales", u"JPY", 100000000)], f_self, VOC)
    if r2 != [L_NA, False, None, L_NA, L_BOTH, True, EXACT, L_NAME]:
        out.append(u"row_labels の読みの順(字のとおり → 円の族)・札(他)が違う: %s" % (r2,))
    # ---- subject_elems
    if ms.subject_elems(u"売上", VOC) != (True, [u"NetSales", u"Revenue", u"OperatingRevenues"]) or ms.subject_elems(u"売", VOC) != (False, []) or ms.subject_elems(u"", VOC) != (False, []):
        out.append(u"subject_elems(語が字で同じ組の要素名を全部合わせる)が違う")
    real = dict((w, e) for w, e in ms.V.PROFILES[u"P33E"].subjects)
    if not real or ms.subject_elems(u"売上高")[0] is not True or ms.subject_elems(u"売上高")[1][:2] != real[u"売上高"][:2]:
        out.append(u"既定の語彙が P33E の主語の語彙でない")
    return out


def facts_for_problems(ms=None):
    u"""``is_exact_name``・``is_loose_name``・``reached`` が ``instance.facts_for`` の名前の選び方(context の選別を除く)と同じ答えを返す。"""
    ms = ms or MS
    out = []
    names = [u"jppfs_cor:NetSales", u"jppfs_cor:NetSalesSummaryOfBusinessResults", u"x:xnetsalesy", u"x:OperatingIncomeLossSummaryOfBusinessResults", u"x:OperatingIncome", u"x:Other", u"x:OperatingProfitX"]
    facts = [{u"name": n, u"context": u"c", u"unit": u"JPY", u"value": i + 1} for i, n in enumerate(names)]
    ctxs = {u"c": {}}
    for elems in ([u"NetSales"], [u"OperatingIncome"], [u"operatingprofit"], [u"Zzz"], [u"NetSales", u"OperatingIncome"], [u"OperatingIncome", u"Other"]):
        with patched(ms.I, ctx_ok=lambda *a, **k: True):
            want = [f[u"name"] for f in ms.I.facts_for(elems, facts, ctxs)]
        got, how = ms.reached([(f[u"name"], f[u"unit"], f[u"value"]) for f in facts], elems)
        if [g[0] for g in got] != want:
            out.append(u"reached が instance.facts_for と違う: %s" % (elems,))
        if got and how not in (EXACT, LOOSE):
            out.append(u"reached の届き方の字が違う")
        if not got and how is not None:
            out.append(u"reached が空のとき届き方が None でない")
        if want and how != (EXACT if any(ms.is_exact_name(n.split(":")[-1], elems) for n in want) else LOOSE):
            out.append(u"reached の届き方が完全一致・部分一致と合わない")
    return out


# ---------------------------------------------------------------- 5. 段 1 の突き合わせ
def rw(si, pos, state, reason=None, ptr=()):
    return (si, pos, state, reason, list(ptr))


def sbook(n, grp, before, after, cut=True, rt=None, claims=None, F=(), fb=10, fa=12):
    b = collections.OrderedDict([(u"#", n), (u"群", grp), (u"切れた", cut), (u"前", list(before)), (u"後", list(after)),
                                (u"前の claim", list(claims) if claims is not None else [C(u"x", u"円", 1) for _r in before]), (u"F", list(F)),
                                (u"fact(前)", fb), (u"fact(後)", fa), (u"RT の行", [list(r[:4]) for r in before] if rt is None else rt)])
    return b


def compare_problems(ms=None):
    ms = ms or MS
    out = []
    b1 = sbook(1, u"甲", [rw(1, 1, VM, u"a", [u"p"]), rw(1, 2, G, None, [u"q"]), rw(1, 3, UN, u"u"), rw(1, 4, G, None, [u"r"]), rw(1, 5, G, None, [u"s"])],
               [rw(1, 1, G, None, [u"p"]), rw(1, 2, G, None, [u"q"]), rw(1, 3, UN, u"u2"), rw(1, 6, VM, u"v"), rw(1, 5, G, None, [u"s", u"t"])])
    b2 = sbook(2, u"乙", [rw(1, 1, G, None, [u"p"]), rw(1, 2, G, None, [u"z"])], [rw(1, 1, UN, u"z", [u"p"]), rw(1, 2, VM, u"y", [u"z"])])
    b3 = sbook(3, u"丙", [], [], cut=False)
    s = ms.compare_rows([b1, b2, b3])
    w = s[u"全体"]
    want = [(u"前の行", 7), (u"後の行", 7), (u"両方に在る行", 6), (u"前にだけ在る行", 1), (u"後にだけ在る行", 1), (u"state が変わった行", 3),
            (u"state は同じで reason だけ変わった行", 1), (u"state も reason も同じで pointer の並びだけ変わった行", 1), (u"全部同じ行", 1),
            (u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)", 2), (u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)", 1),
            (u"前は GROUNDED で後に無い行(前にだけ在る行)", 1), (u"前の GROUNDED の行", 5), (u"state が変わった行を持つ本", 2),
            (u"前後のどこかの欄が違う行(前にだけ・後にだけを含む)を持つ本", 2)]
    got = [(k, w[k]) for k, _v in want]
    if got != want:
        out.append(u"compare_rows の全体の数が手計算(前 7・後 7・両方 6・前にだけ 1・後にだけ 1・state 3・reason 1・pointer 1・同じ 1)と違う: %s" % ([(a, b) for (a, b), (_c, d) in zip(got, want) if b != d],))
    t = w[u"state の移り変わり(前 → 後。両方に在る行)"]
    if t[u"%s → %s" % (VM, G)] != 1 or t[u"%s → %s" % (G, UN)] != 1 or t[u"%s → %s" % (G, G)] != 2 or t[u"%s → %s" % (G, VM)] != 1 or sum(t.values()) != 6:
        out.append(u"移り変わりの表が(前 → 後)の向き・両方に在る行の数でない")
    # pointer の並びだけが違う行は state が変わった行に数えない(当たらない例)
    only_ptr = ms.compare_rows([sbook(1, u"甲", [rw(1, 1, G, None, [u"a", u"b"])], [rw(1, 1, G, None, [u"b", u"a"])])])[u"全体"]
    if (only_ptr[u"state が変わった行"], only_ptr[u"state も reason も同じで pointer の並びだけ変わった行"], only_ptr[u"全部同じ行"]) != (0, 1, 0):
        out.append(u"pointer の並びだけが違う行が「pointer だけ」の欄に 1 で state が変わった行に 0 でない")
    # 当たる例: 鍵が同じで前が VALUE_MISMATCH・後が GROUNDED
    hit = ms.compare_rows([sbook(1, u"甲", [rw(1, 1, VM, u"a")], [rw(1, 1, G)])])[u"全体"]
    if hit[u"state が変わった行"] != 1 or hit[u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)"] != 1:
        out.append(u"前が VALUE_MISMATCH・後が GROUNDED の行が state が変わった行でない")
    g = s[u"群別"]
    if (g[u"甲"][u"state が変わった行"], g[u"甲"][u"両方に在る行"], g[u"甲"][u"前にだけ在る行"], g[u"乙"][u"state が変わった行"], g[u"丙"][u"前の行"]) != (1, 4, 1, 2, 0):
        out.append(u"群別の数が(甲: state 1・両方 4・前にだけ 1 / 乙: state 2 / 丙: 0)でない")
    bs = s[u"前の state 別"]
    if (bs[VM][u"両方に在る行"], bs[VM][u"state が変わった行"], bs[G][u"両方に在る行"], bs[G][u"前にだけ在る行"], bs[G][u"state が変わった行"], bs[G][u"pointer の並びだけ変わった行"],
            bs[UN][u"state は同じで reason だけ変わった行"], bs[PN][u"両方に在る行"]) != (1, 1, 4, 1, 2, 1, 1, 0):
        out.append(u"前の state 別の数が違う: %s" % (dict((k, dict(v)) for k, v in bs.items()),))
    if s[u"後にだけ在る行の後の state 別"][VM] != 1 or sum(s[u"後にだけ在る行の後の state 別"].values()) != 1:
        out.append(u"後にだけ在る行の後の state 別が違う")
    if s[u"前にだけ在る行"] != [[1, 1, 4, G, None, None, None]] or s[u"後にだけ在る行"] != [[1, 1, 6, None, VM, None, u"v"]]:
        out.append(u"前にだけ・後にだけ在る行の一覧が違う")
    if [r[:5] for r in s[u"変わった行(state・reason・pointer のどれか。pointer だけの行も入る)"]] != [[1, 1, 1, VM, G], [1, 1, 3, UN, UN], [1, 1, 5, G, G], [2, 1, 1, G, UN], [2, 1, 2, G, VM]]:
        out.append(u"変わった行の一覧が [本, 文, 位置, 前, 後] の並びでない")
    fg = ms.fact_growth([sbook(1, u"甲", [], [], fb=5, fa=7), sbook(2, u"乙", [], [], fb=5, fa=5), sbook(3, u"丙", [], [], fb=6, fa=4), sbook(4, u"丙", [], [], cut=False, fb=0, fa=0)])
    if (fg[u"切れた本"], fg[u"fact の個数が前より増えた本"], fg[u"fact の個数が前より減った本"], fg[u"fact の個数の合計(前)"], fg[u"fact の個数の合計(後)"]) != (3, 1, 1, 16, 16):
        out.append(u"fact_growth が(切れた 3・増えた 1・減った 1・前の合計 16・後の合計 16)でない")
    return out


def wiring_problems(ms=None):
    ms = ms or MS
    out = []
    good = [sbook(1, u"甲", [rw(1, 1, G), rw(1, 2, UN, REASON_P)], [rw(1, 1, VM, u"x"), rw(1, 2, UN, REASON_P)]), sbook(2, u"乙", [rw(1, 1, UN, REASON_P, [u"p"])], [rw(1, 1, UN, REASON_P, [u"q"])])]
    w = ms.wiring(good, 3, 2)
    if (w[u"「前」の行"], w[u"P の行(前)"], w[u"「前」の行が便 RT の段 1 の行と同じ本"]) != (3, 2, 2):
        out.append(u"wiring の数が(前の行 3・P 2・同じ本 2)でない")
    if stops(ms, ms.wiring, good, 4, 2) is not True or stops(ms, ms.wiring, good, 3, 3) is not True:
        out.append(u"「前」の行の数・P の行の数が違うのに止まらない")
    bad_rt = copy.deepcopy(good)
    bad_rt[0][u"RT の行"][0][2] = VM
    if stops(ms, ms.wiring, bad_rt, None, None) is not True:
        out.append(u"「前」の行が便 RT の段 1 の行と違うのに止まらない")
    bad_rt2 = copy.deepcopy(good)
    bad_rt2[1][u"RT の行"][0][3] = u"other"
    if stops(ms, ms.wiring, bad_rt2, None, None) is not True:
        out.append(u"「前」の reason が便 RT の段 1 の行と違うのに止まらない")
    gone = copy.deepcopy(good)
    gone[1][u"後"] = []
    if stops(ms, ms.wiring, gone, None, None) is not True:
        out.append(u"P の行が「後」に無いのに止まらない")
    moved = copy.deepcopy(good)
    moved[1][u"後"] = [rw(1, 1, VM, REASON_P)]
    if stops(ms, ms.wiring, moved, None, None) is not True:
        out.append(u"P の行の state が「後」で違うのに止まらない")
    moved2 = copy.deepcopy(good)
    moved2[1][u"後"] = [rw(1, 1, UN, u"other")]
    if stops(ms, ms.wiring, moved2, None, None) is not True:
        out.append(u"P の行の reason が「後」で違うのに止まらない")
    return out


# ---------------------------------------------------------------- 6. 「後」の ZIP・1 本の job
def make_zip(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in members:
            z.writestr(MS.TSS._info(name), data)
    return buf.getvalue()


def names_of(zb):
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        return [i.filename for i in z.infolist()], dict((i.filename, z.read(i.filename)) for i in z.infolist()), [(i.filename, i.date_time, i.compress_type) for i in z.infolist()]


def after_zip_problems(ms=None):
    ms = ms or MS
    out = []
    members = [(u"XBRL/PublicDoc/a.xhtml", b"<a/>\n"), (u"XBRL/PublicDoc/overview.xhtml", u"概況".encode("utf-8") + b"\x00\xff"), (u"XBRL/Z/last.bin", b"")]
    wrapped = make_zip(members)
    summary = b"  <ix:nonFraction a=\"1\"/>\r\n \x00 tail \r\n "
    got = ms.after_zip(wrapped, summary)
    names, data, infos = names_of(got)
    if names != [m[0] for m in members] + [ms.SUMMARY_NAME] or ms.SUMMARY_NAME != u"XBRL/PublicDoc/summary_ixbrl.htm":
        out.append(u"「後」の ZIP の member が「前」の全部 + サマリーの名前の順でない: %s" % (names,))
    if any(data.get(n) != d for n, d in members):
        out.append(u"「後」の ZIP が「前」の member を 1 byte も変えずに写していない")
    if data.get(ms.SUMMARY_NAME) != summary:
        out.append(u"「後」の ZIP のサマリーが入っていない・1 byte 変わっている")
    if infos != [(n, ms.TSS._info(n).date_time, ms.TSS._info(n).compress_type) for n in names]:
        out.append(u"「後」の ZIP の member の info が TSS._info(名前)でない")
    if names_of(wrapped)[0] != [m[0] for m in members]:
        out.append(u"「前」の ZIP の bytes が変わっている")
    if stops(ms, ms.after_zip, make_zip(members + [(ms.SUMMARY_NAME, b"x")]), summary) is not True:
        out.append(u"「前」にサマリーの名前が既に在るのに止まらない")
    return out


class FakeInst(object):
    pass


def forecast_problems(ms=None):
    ms = ms or MS
    out = []
    inst = {u"facts": [
        {u"name": u"p:A", u"context": u"cf", u"unit": u"JPY", u"value": 5},
        {u"name": u"p:B", u"context": u"cf", u"unit": u"", u"value": 5},
        {u"name": u"p:C", u"context": u"cf", u"unit": u"JPY", u"value": 0},
        {u"name": u"p:D", u"context": u"cr", u"unit": u"JPY", u"value": 7},
        {u"name": u"p:E", u"context": u"none", u"unit": u"JPY", u"value": 8},
        {u"name": u"p:F", u"context": u"cu", u"unit": u"Pure", u"value": 0.1},
        {u"name": u"p:G", u"context": None, u"unit": u"JPY", u"value": 9}],
        u"contexts": {u"cf": {u"members": [u"jpcrp:ForecastMember"]}, u"cr": {u"members": [u"jpcrp:ConsolidatedMember"]}, u"cu": {u"members": [u"jpcrp:UpperMember"]}}}
    with patched(ms.I, load_instance=lambda zb: inst), patched(ms.PS, summary_zip=lambda zb: b""):
        got = ms.forecast_facts(b"")
        if got != [(u"p:A", u"JPY", 5), (u"p:F", u"Pure", 0.1)]:
            out.append(u"forecast_facts が(予想の枠・単位あり・値が 0 でない)の fact を名前つきで返さない: %s" % (got,))
        with patched(ms.PS, split_facts=lambda i: ([1], [])):
            if stops(ms, ms.forecast_facts, b"") is not True:
                out.append(u"F の個数が PS.split_facts の F の個数と違うのに止まらない")
    return out


def tmp_file(data):
    d = tempfile.mkdtemp(prefix="se_job_")
    p = os.path.join(d, u"x.zip")
    with open(p, "wb") as fh:
        fh.write(data)
    return d, p


def job_problems(ms=None):
    u"""``book_job`` を、材料の ZIP の字と重い道具(切り出し・engine)を作り物にして本物のまま走らせる。前と後を取り違えない。"""
    ms = ms or MS
    out = []
    zb = b"fake-material"
    sha = ms.ST.sha256_bytes(zb)
    wrapped = make_zip([(u"XBRL/PublicDoc/a.xhtml", b"<a/>")])
    seen = []

    def raw(si, pos, subject, value):
        return {u"sentence": si, u"pos": pos, u"subject": subject, u"unit": u"円", u"value": value, u"unit_scale": 1, u"claim_scale": 1, u"pct_tolerance": None}

    def cl(state, reason, ptr):
        return {u"state": state, u"reason": reason, u"pointers": ptr}
    before = [(raw(1, 1, u"売上高", 100), cl(VM, u"no_same_value", [u"b1"])), (raw(1, 2, u"", 200), cl(UN, REASON_P, []))]
    after = [(raw(1, 1, u"利益", 150), cl(G, None, [u"a1", u"a2"])), (raw(1, 2, u"後", 250), cl(UN, REASON_P, []))]

    def fake_claims(zbytes):
        names = names_of(zbytes)[0]
        seen.append(names)
        return after if ms.SUMMARY_NAME in names else before

    def fake_load(zbytes):
        names = names_of(zbytes)[0]
        if names == [ms.SUMMARY_NAME]:
            return {u"facts": [{u"name": u"p:Ok", u"context": u"cf", u"unit": u"JPY", u"value": 3}, {u"name": u"p:R", u"context": u"cr", u"unit": u"JPY", u"value": 4}],
                    u"contexts": {u"cf": {u"members": [u"x:ForecastMember"]}, u"cr": {u"members": []}}}
        return {u"facts": [{}] * (11 if ms.SUMMARY_NAME in names else 7), u"contexts": {}}

    def fake_judge(n, g, k, s, zbytes):
        return {u"行": [[1, 1, VM, u"no_same_value", u"x"], [1, 2, UN, REASON_P, u"y"]]}

    d, p = tmp_file(zb)
    try:
        sm = lambda z: b"SUMMARY"
        with patched(ms.TSS, cut=lambda z: (u"text", 0, None), wrap=lambda z, t: (wrapped, 1)), patched(ms.RT.TSS, judge_book=fake_judge), \
                patched(ms.PS, claims_of=fake_claims, summary_member_bytes=sm, summary_zip=lambda z: make_zip([(ms.SUMMARY_NAME, b"S")])), patched(ms.I, load_instance=fake_load):
            b = ms.book_job((7, u"乙", u"k", sha, p))
            if b[u"#"] != 7 or b[u"群"] != u"乙" or b[u"切れた"] is not True:
                out.append(u"book_job の本の #・群・切れたが違う")
            if [r[:4] for r in b[u"前"]] != [(1, 1, VM, u"no_same_value"), (1, 2, UN, REASON_P)] or b[u"前"][0][4] != [u"b1"]:
                out.append(u"book_job の「前」が前の ZIP の claim の行(文・位置・state・reason・pointer)でない: %s" % (b[u"前"],))
            if [r[:4] for r in b[u"後"]] != [(1, 1, G, None), (1, 2, UN, REASON_P)] or b[u"後"][0][4] != [u"a1", u"a2"]:
                out.append(u"book_job の「後」が後の ZIP の claim の行でない(前と後を取り違えた): %s" % (b[u"後"],))
            if len(seen) != 2 or ms.SUMMARY_NAME in seen[0] or ms.SUMMARY_NAME not in seen[1] or seen[1][:-1] != seen[0]:
                out.append(u"book_job が PS.claims_of に「前」(サマリー無し)・「後」(サマリー足し)の順で渡していない: %s" % (seen,))
            if b[u"RT の行"] != [[1, 1, VM, u"no_same_value"], [1, 2, UN, REASON_P]]:
                out.append(u"book_job の RT の行が便 RT の段 1(judge_book)の行でない")
            if [c[u"subject"] for c in b[u"前の claim"]] != [u"売上高", u""] or b[u"前の claim"][0][u"value"] != 100:
                out.append(u"book_job の前の claim が「前」の raw の claim(主語・値)でない")
            if b[u"F"] != [(u"p:Ok", u"JPY", 3)]:
                out.append(u"book_job の F が(予想の枠・名前つき)でない: %s" % (b[u"F"],))
            if (b[u"fact(前)"], b[u"fact(後)"]) != (7, 11):
                out.append(u"book_job の fact の個数が(前 7・後 11)でない: %s" % ((b[u"fact(前)"], b[u"fact(後)"]),))
            # 切り出せない本は数だけ
            with patched(ms.TSS, cut=lambda z: (None, None, u"x")):
                nb = ms.book_job((7, u"乙", u"k", sha, p))
                if nb[u"切れた"] or nb[u"前"] or nb[u"後"] or nb[u"F"]:
                    out.append(u"切り出せない本が空の本でない")
            # sha256 が表と違えば止まる
            if stops(ms, ms.book_job, (7, u"乙", u"k", u"0" * 64, p)) is not True:
                out.append(u"材料の ZIP の sha256 が表と違うのに止まらない")
            if stops(ms, ms.book_job, (7, u"乙", u"k", sha, p + u"x")) is not True:
                out.append(u"材料の ZIP が無いのに止まらない")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return out


# ---------------------------------------------------------------- 7. つなぐ配線(orchestrate を作り物の本で本物のまま走らせる)
W = u"売上高"
E1 = u"jppfs_cor:NetSales"
X_LOOSE = u"x:xRevenueY"
X_LOOSE2 = u"x:XRevenueY"
OTHER = u"jppfs_cor:Other"


def fake_books():
    u"""作り物の 8 本(甲 1・2・乙 3・4・5・丙 6・7・8)。手計算は ``orchestrate_problems`` の中。"""
    P = REASON_P
    b = []
    b.append(sbook(1, u"甲", [rw(1, 1, G, None, [u"p"]), rw(1, 2, UN, P)], [rw(1, 1, VM, u"x", [u"p"]), rw(1, 2, UN, P)],
                   claims=[C(u"x", u"円", 1), C(W, u"円", 1234)], F=[(E1, u"JPY", 1234), (OTHER, u"JPY", 99)], fb=10, fa=12))
    b.append(sbook(2, u"甲", [rw(1, 1, G, None, [u"a", u"b"]), rw(1, 2, UN, P), rw(1, 3, UN, P)], [rw(1, 1, G, None, [u"b", u"a"]), rw(1, 2, UN, P), rw(1, 3, UN, P)],
                   claims=[C(u"x", u"円", 1), C(W, u"円", 1234), C(W, u"百万円", 100, 1000000, 1000000)], F=[(E1, u"JPY", 555), (E1, u"JPY", 100000000)], fb=10, fa=12))
    b.append(sbook(3, u"乙", [rw(1, 1, UN, P)], [rw(1, 1, UN, P)], claims=[C(W, u"%", 5.0, None, None)], F=[(u"jppfs_cor:Foo", u"Pure", 0.05)], fb=10, fa=12))
    b.append(sbook(4, u"乙", [rw(1, 1, UN, P), rw(1, 2, UN, P)], [rw(1, 1, UN, P), rw(1, 2, UN, P)], claims=[C(u"", u"円", 42), C(u"未知の語", u"円", 43)],
                   F=[(u"jppfs_cor:Bar", u"JPY", 42)], fb=10, fa=12))
    b.append(sbook(5, u"乙", [rw(1, 1, UN, P), rw(1, 2, UN, u"a")], [rw(1, 1, UN, P), rw(1, 2, UN, u"b")], claims=[C(W, u"円", 1), C(u"x", u"円", 1)], F=[], fb=10, fa=10))
    b.append(sbook(6, u"丙", [rw(1, 1, UN, P)], [rw(1, 1, UN, P)], claims=[C(W, u"円", 7)], F=[(E1, u"JPY", 8), (X_LOOSE, u"JPY", 7)], fb=10, fa=12))
    b.append(sbook(7, u"丙", [rw(1, 1, UN, P), rw(1, 9, G)], [rw(1, 1, UN, P), rw(1, 8, VM, u"n")], claims=[C(W, u"円", 9), C(u"x", u"円", 1)], F=[(X_LOOSE2, u"JPY", 9)], fb=10, fa=12))
    b.append(sbook(8, u"丙", [], [], cut=False, fb=0, fa=0))
    return b


def fake_pop():
    return [(1, u"甲", u"k", u"s1"), (2, u"甲", u"k", u"s2"), (3, u"乙", u"k", u"s3"), (4, u"乙", u"k", u"s4"), (5, u"乙", u"k", u"s5"), (6, u"丙", u"k", u"s6"), (7, u"丙", u"k", u"s7"), (8, u"丙", u"k", u"s8")]


def fake_engine_fp():
    fp = MS.VD.engine_fingerprint()
    return collections.OrderedDict((k, fp[k]) for k in MS.FP_KEYS)


def fake_rt_rec(fp=None):
    return {u"engine の指紋(今。便 NRE の記録の直した後と同じ)": fp or fake_engine_fp(), u"段 1(第 1 便。400 本の判定)": {u"行(前)": 21, u"行(後)": 13, u"両方に在る行": 17}}


def fake_read_rec():
    return {u"行": [[1, 1, 1, 2, u"甲組"], [2, 2, 1, 3, u"乙組"], [3, 4, 1, 1, u"甲組"], [4, 6, 1, 1, u"W組"], [5, 9, 1, 1, u"甲組"]]}


def run_orchestrate(ms, books=None, rt_rec=None, pop=None, hook=None, full=False, capture=None):
    u"""``hook`` は 1 本目の job の中で材料の置き場(folder)に何かする関数。``full`` は 400 本の経路(``full``)を通す(母集団の形の確かめだけ外す)。
    ``capture`` は list(渡すと ``wiring`` の期待の引数を (行の数, P の行の数) で入れ、数を返すだけの作り物にする)。"""
    books = books if books is not None else fake_books()
    table = dict((b[u"#"], b) for b in books)
    pop = pop or fake_pop()
    tmp = tempfile.mkdtemp(prefix="se_orch_")
    calls = []
    try:
        for (_n, _g, _k, sha) in pop:
            open(os.path.join(tmp, sha + u".zip"), "w").close()

        def fake_job(args):
            calls.append(args)
            if hook is not None and len(calls) == 1:
                hook(os.path.dirname(args[4]))
            return copy.deepcopy(table[args[0]])

        def spy(books_, expect_rows=None, expect_p=None):
            capture.append((expect_rows, expect_p))
            return collections.OrderedDict([(u"本", len(books_))])
        over = {"book_job": fake_job}
        if capture is not None:
            over["wiring"] = spy
        if full:
            over["subset_shape"] = lambda pop_: None
        with patched(ms, **over), patched(ms.ST, **({"validate_population": lambda *a, **k: None} if full else {})):
            rec = ms.orchestrate(root=ROOT, procs=1, material=tmp, say=lambda *a: None, population=pop, rt_rec=rt_rec or fake_rt_rec(), read_rec=fake_read_rec())
        return rec, calls
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_stops(ms, **kw):
    u"""止まれば True・止まらなければ False・Stop でない例外なら例外の名前の字。"""
    try:
        run_orchestrate(ms, **kw)
    except ms.Stop:
        return True
    except BaseException as exc:                   # noqa: BLE001
        return type(exc).__name__
    return False


def row_of(rows, n, si, pos):
    return [r for r in rows if (r[0], r[1], r[2]) == (n, si, pos)][0]


def orchestrate_problems(ms=None):
    ms = ms or MS
    out = []
    rec, calls = run_orchestrate(ms)
    if [c[:4] for c in calls] != [(n, g, k, s) for (n, g, k, s) in fake_pop()] or any(os.path.basename(c[4]) != c[3] + u".zip" for c in calls):
        out.append(u"orchestrate が母集団の順に本ごとの job を呼んでいない")
    if rec[u"切り出し"] != collections.OrderedDict([(u"本", 8), (u"切れた本", 7), (u"切れない本", 1)]):
        out.append(u"記録の切り出しの数が(8・7・1)でない")
    # 段 1: 前 13 行・state が変わった行 1(本 1 の G → VM)・pointer だけ 1(本 2)・reason だけ 1(本 5)・前にだけ 1(本 7 の G)・後にだけ 1(本 7 の VM)・前の GROUNDED 3
    w = rec[K_S1][u"全体"]
    if (w[u"前の行"], w[u"後の行"], w[u"state が変わった行"], w[u"state も reason も同じで pointer の並びだけ変わった行"], w[u"前の GROUNDED の行"],
            w[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"], w[u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)"]) != (13, 13, 1, 1, 3, 1, 0):
        out.append(u"段 1 の数が作り物の手計算(前 13・後 13・state 1・pointer 1・前の G 3・G でなくなった 1・G になった 0)と違う: %s" % ({k: v for k, v in w.items() if not isinstance(v, (dict, list))},))
    if (w[u"前にだけ在る行"], w[u"後にだけ在る行"], w[u"state は同じで reason だけ変わった行"], w[u"前は GROUNDED で後に無い行(前にだけ在る行)"], w[u"両方に在る行"]) != (1, 1, 1, 1, 12):
        out.append(u"段 1 の前にだけ・後にだけ・reason だけ・G で消えた行の数が作り物の手計算(1・1・1・1・両方 12)と違う")
    if rec[K_S1][u"群別"][u"甲"][u"state が変わった行"] != 1 or rec[K_S1][u"群別"][u"乙"][u"state が変わった行"] != 0:
        out.append(u"段 1 の群別が作り物と違う")
    fg = rec[K_FG]
    if (fg[u"切れた本"], fg[u"fact の個数が前より増えた本"], fg[u"fact の個数の合計(前)"], fg[u"fact の個数の合計(後)"]) != (7, 6, 70, 82):
        out.append(u"fact の個数の確かめが(切れた 7・増えた 6・前 70・後 82)でない: %s" % (dict(fg),))
    wire = rec[K_RT]
    if (wire[u"「前」の行"], wire[u"P の行(前)"], wire[u"「前」の行が便 RT の段 1 の行と同じ本"]) != (13, 9, 8):
        out.append(u"配線の確認の数が(前 13・P 9・同じ本 8)でない")
    # 段 2: P の行 9。字のとおり: 両方 b1(1,2)・b7 / 名前だけ b2(1,2) / 当てない b2(1,3) / 値だけ b3・b6 / 主語なし b4a / 語彙の外 b4b / F が空 b5
    s2 = rec[K_S2]
    rows = s2[u"行"]
    if s2[u"P の行"] != 9 or [r[:3] for r in rows] != sorted(r[:3] for r in rows) or len(rows) != 9:
        out.append(u"段 2 の P の行が 9 行(鍵の順)でない")
    want = {
        (1, 1, 2): [u"甲", L_BOTH, True, EXACT, L_NAME, L_BOTH, True, EXACT, L_NAME],
        (2, 1, 2): [u"甲", L_NAME, False, EXACT, L_BOTH, L_NAME, False, EXACT, L_BOTH],
        (2, 1, 3): [u"甲", L_NA, False, None, L_NA, L_BOTH, True, EXACT, L_NAME],
        (3, 1, 1): [u"乙", L_VAL, True, None, L_NONE, L_VAL, True, None, L_NONE],
        (4, 1, 1): [u"乙", L_NS, True, None, L_NS, L_NS, True, None, L_NS],
        (4, 1, 2): [u"乙", L_OV, False, None, L_OV, L_OV, False, None, L_OV],
        (5, 1, 1): [u"乙", L_FE, False, None, L_NONE, L_FE, False, None, L_NONE],
        (6, 1, 1): [u"丙", L_VAL, True, EXACT, L_NAME, L_VAL, True, EXACT, L_NAME],
        (7, 1, 1): [u"丙", L_BOTH, True, LOOSE, L_NAME, L_BOTH, True, LOOSE, L_NAME]}
    for k, v in want.items():
        got = row_of(rows, *k)[3:]
        if got != v:
            out.append(u"段 2 の行 %s の群・札が手計算と違う: %s" % (k, got))
    lit = s2[u"読み"][LIT]
    fam = s2[u"読み"][FAM]
    if dict(lit[u"札"]) != {L_NA: 1, L_FE: 1, L_NS: 1, L_OV: 1, L_BOTH: 2, L_VAL: 2, L_NAME: 1, L_NONE: 0}:
        out.append(u"字のとおりの札の数が手計算と違う: %s" % (dict(lit[u"札"]),))
    if dict(fam[u"札"]) != {L_NA: 0, L_FE: 1, L_NS: 1, L_OV: 1, L_BOTH: 3, L_VAL: 2, L_NAME: 1, L_NONE: 0}:
        out.append(u"円の族の札の数が手計算と違う: %s" % (dict(fam[u"札"]),))
    if (lit[u"札 1・2 でない行(副の分母)"], lit[u"F のどれかに値が合う行(副の分母)"], fam[u"札 1・2 でない行(副の分母)"], fam[u"F のどれかに値が合う行(副の分母)"]) != (7, 5, 8, 6):
        out.append(u"副の分母が(字のとおり 7・5 / 円の族 8・6)でない")
    if (lit[u"対照: 両方(他)の行"], fam[u"対照: 両方(他)の行"]) != (1, 1) or lit[u"対照: 札(他)"][L_NONE] != 2 or lit[u"対照: 札(他)"][L_NAME] != 3:
        out.append(u"対照の数が手計算(両方(他) 1・1。字のとおりのどちらも無し 2・名前だけ 3)と違う: %s" % (dict(lit[u"対照: 札(他)"]),))
    if dict(lit[u"札 5(両方)の行の届き方"]) != {EXACT: 1, LOOSE: 1} or dict(fam[u"札 5(両方)の行の届き方"]) != {EXACT: 2, LOOSE: 1}:
        out.append(u"札 5 の届き方の数が違う")
    if dict(lit[u"札 3・4(主語なし・語彙の外)の行のうち F のどれかに値が合う行"]) != {L_NS: 1, L_OV: 0}:
        out.append(u"札 3・4 の副の数が違う")
    # 読みの軸との重ね: 引けた 3・引けない 1(本 9)・W 組は使わない・円の族の両方 2
    ov = s2[u"読みの軸との重ね"]
    if (ov[u"甲組・乙組の行"], ov[u"鍵が段 2 の P の行に引けた行"], ov[u"鍵が引けない行"], ov[u"円の族の読みの札"][L_BOTH], ov[u"円の族の読みの札"][L_NS]) != (4, 3, 1, 2, 1):
        out.append(u"読みの軸との重ねの数が(4・引けた 3・引けない 1・両方 2・主語なし 1)でない: %s" % ({k: v for k, v in ov.items() if k != u"札の行"},))
    if ov[u"札の行"] != [[1, 1, 2, L_BOTH], [2, 1, 3, L_BOTH], [4, 1, 1, L_NS]]:
        out.append(u"読みの軸との重ねの札の行が違う")
    # 予測の数
    p = rec[K_PRED]
    if rec[K_PRED] != ms.predictions(rec[K_S1], rec[K_FG], rec[K_S2]):
        out.append(u"予測の数が段の数から作り直したものと違う")
    pv = list(p.values())
    if pv[0] != collections.OrderedDict([(u"前にだけ在る行", 1), (u"後にだけ在る行", 1)]) or pv[1] != 1 or pv[2] != nd(6, 7) or pv[5] != 1:
        out.append(u"SE-1・SE-2a の数が(前にだけ 1・後にだけ 1・state 1・fact が増えた本 6 / 7)でない")
    sedict = dict((k.split(u" ")[0] + (u"参考" if u"参考" in k else u"") + (u"引けない" if u"引けなかった" in k else u""), v) for k, v in p.items() if k.startswith(u"SE-"))
    if sedict.get(u"SE-2b") != nd(1, 13) or sedict.get(u"SE-3") != nd(1, 3) or sedict.get(u"SE-4") != nd(2, 7) or sedict.get(u"SE-4参考") != nd(2, 8) \
            or sedict.get(u"SE-5") != nd(2, 5) or sedict.get(u"SE-5参考") != nd(3, 6) or sedict.get(u"SE-6") != nd(1, 2) or sedict.get(u"SE-6参考") != nd(1, 3) or sedict.get(u"SE-7") != nd(2, 4) or sedict.get(u"SE-7引けない") != 1:
        out.append(u"予測の分子・分母が作り物の手計算(SE-2b 1/13・SE-3 1/3・SE-4 2/7(参考 2/8)・SE-5 2/5(参考 3/6)・SE-6 1/2(参考 1/3)・SE-7 2/4)と違う: %s" % (sedict,))
    if rec[u"seal"] != SEAL_REL or rec[u"封の commit"] != SEAL_COMMIT_SHORT or rec[u"profile"] != u"P33E" or rec[u"key_leaks"] != []:
        out.append(u"記録の封の path・commit・profile・key_leaks が違う")
    if list(rec[u"engine の指紋(今。便 RT の記録の今と同じ)"].items()) != list(fake_engine_fp().items()):
        out.append(u"記録の engine の指紋が今の engine でない")
    # ---- 止める条件
    if run_stops(ms, rt_rec=fake_rt_rec(collections.OrderedDict((k, u"x-" + k) for k in ms.FP_KEYS))) is not True:
        out.append(u"engine の指紋が便 RT の記録の今と違うのに止まらない")
    bad = fake_books()
    bad[1][u"RT の行"][0][2] = VM
    if run_stops(ms, books=bad) is not True:
        out.append(u"「前」の行が便 RT の段 1 の行と違うのに orchestrate が止まらない")
    bad = fake_books()
    bad[0][u"後"][1] = rw(1, 2, VM, P_NEW)
    if run_stops(ms, books=bad) is not True:
        out.append(u"P の行が「後」で変わったのに orchestrate が止まらない")
    # 対照の輪: F が空の本(5)は輪に入らない・輪が 1 本以下の群は止まる
    one = [b for b in fake_books() if b[u"#"] != 2]
    pop1 = [(i + 1, b[u"群"], u"k", u"s%d" % b[u"#"]) for i, b in enumerate(one)]
    for i, b in enumerate(one):
        b[u"#"] = i + 1
    if run_stops(ms, books=one, pop=pop1) is not True:
        out.append(u"輪が 1 本以下の群が在るのに止まらない")
    return out


# ---------------------------------------------------------------- 7b. 独立監査 REVISE への強化(C・W・L・R・P3・P2・I)
def p_rows_problems(ms=None):
    u"""段 2 の P の行は「前」の reason で選ぶ(「後」の reason では選ばない)。前後で P の行が違う本で見る。"""
    ms = ms or MS
    out = []
    P = REASON_P
    b1 = sbook(1, u"甲", [rw(1, 1, UN, u"a"), rw(1, 2, UN, P)], [rw(1, 1, UN, P), rw(1, 2, UN, u"b")], claims=[C(W, u"円", 1), C(W, u"円", 2)], F=[(E1, u"JPY", 2)])
    b2 = sbook(2, u"乙", [rw(1, 1, UN, P)], [rw(1, 1, UN, P)], claims=[C(W, u"円", 1)], F=[(E1, u"JPY", 1)])
    rows = ms.p_rows_of([b1, b2], {1: 2, 2: 1})
    if [tuple(r[:3]) for r in rows] != [(1, 1, 2), (2, 1, 1)]:
        out.append(u"p_rows_of が「前」の reason が P の行でなく選んでいる: %s" % ([tuple(r[:3]) for r in rows],))
    elif row_of(rows, 1, 1, 2)[4] != L_BOTH:
        out.append(u"p_rows_of の行が自分の行の claim で札を付けていない")
    # orchestrate: 「後」にだけ P の reason が在る行(前は P でない)は段 2 の行に入らない
    base, _c = run_orchestrate(ms)
    books = fake_books()
    books[4][u"後"][1] = rw(1, 2, UN, REASON_P)
    rec, _c = run_orchestrate(ms, books=books)
    if rec[K_S2][u"P の行"] != 9 or [tuple(r[:3]) for r in rec[K_S2][u"行"]] != [tuple(r[:3]) for r in base[K_S2][u"行"]]:
        out.append(u"「後」にだけ P の reason が在る行が段 2 の行に入っている(P の行は「前」の reason で選ぶ)")
    return out


def se1_problems(ms=None):
    u"""SE-1 の「前にだけ在る行」と「後にだけ在る行」を、互いに違う数の本で別々に縛る(1・1 や 0・0 では取り違えが見えない)。"""
    ms = ms or MS
    out = []
    P = REASON_P
    for n_before_only, n_after_only in ((3, 1), (1, 2)):
        books = fake_books()
        before = [rw(1, 1, UN, P)] + [rw(1, 20 + i, G, None) for i in range(n_before_only)]
        after = [rw(1, 1, UN, P)] + [rw(1, 40 + i, VM, u"n") for i in range(n_after_only)]
        books[6] = sbook(7, u"丙", before, after, claims=[C(W, u"円", 9)] + [C(u"x", u"円", 1) for _i in range(n_before_only)], F=[(X_LOOSE2, u"JPY", 9)], fb=10, fa=12)
        rec, _c = run_orchestrate(ms, books=books)
        w = rec[K_S1][u"全体"]
        if (w[u"前にだけ在る行"], w[u"後にだけ在る行"]) != (n_before_only, n_after_only):
            out.append(u"作り物の段 1 の前にだけ・後にだけ在る行が手計算(%d・%d)と違う" % (n_before_only, n_after_only))
        pv = rec[K_PRED]
        got = list(pv.values())[0]
        if list(got.items()) != [(u"前にだけ在る行", n_before_only), (u"後にだけ在る行", n_after_only)]:
            out.append(u"SE-1 の 2 欄が(前にだけ %d・後にだけ %d)でない: %s" % (n_before_only, n_after_only, dict(got)))
        if pv[u"SE-3 参考: 前は GROUNDED で後に無い行(前にだけ在る行)"] != n_before_only:
            out.append(u"SE-3 参考(前は GROUNDED で後に無い行)が前にだけ在る行の GROUNDED の数でない")
    return out


def default_vocab_problems(ms=None):
    u"""語彙の既定(引数なし)が P33E の実物の語彙。別の profile では答えが変わる語で縛る。"""
    ms = ms or MS
    out = []
    if ms.PROFILE != u"P33E":
        out.append(u"PROFILE の定数が P33E でない")
    real = ms.V.PROFILES[u"P33E"].subjects
    for word in [w for w, _e in real]:
        want = []
        for w2, es in real:
            if w2 == word:
                want.extend(e for e in es if e not in want)
        if ms.subject_elems(word) != (True, want):
            out.append(u"既定の語彙の答えが P33E の実物と違う: %d 字の語" % len(word))
            break
    if ms.subject_elems(u"退職給付に係る負債") != (True, [u"RetirementBenefitLiability", u"NetDefinedBenefitLiability"]) \
            or ms.subject_elems(u"退職給付に係る資産") != (True, [u"RetirementBenefitAsset", u"NetDefinedBenefitAsset"]) or ms.subject_elems(u"固定負債") != (True, [u"NoncurrentLiabilities"]):
        out.append(u"既定の語彙が P33E の実物の語(別の profile では答えが変わる語)を返さない")
    if ms.subject_elems(u"存在しない語") != (False, []):
        out.append(u"語彙に無い語が語彙の外でない")
    # 別の profile では答えが変わる語を選んでいること(この縛りが別の profile の取り違えを見分ける)
    for other in (u"P1", u"P6"):
        if ms.subject_elems(u"退職給付に係る負債", ms.V.PROFILES[other].subjects) == ms.subject_elems(u"退職給付に係る負債"):
            out.append(u"縛りの語が別の profile(%s)と同じ答えで、取り違えを見分けない" % other)
    if ms.label_claim(C(u"退職給付に係る負債", u"円", 7), LIT, [(u"jppfs_cor:NetDefinedBenefitLiability", u"JPY", 7)]) != (L_BOTH, True, EXACT):
        out.append(u"label_claim の既定の語彙が P33E でない")
    return out


def fingerprint_problems(ms=None):
    u"""engine の指紋は 4 欄のどれが違っても止まる(1 欄だけの比較では残りの欄の違いを通す)。"""
    ms = ms or MS
    out = []
    if tuple(ms.FP_KEYS) != (u"adapter_xbrl_py_sha256", u"adapter_xbrl_py_files", u"core_py_sha256", u"core_py_files"):
        out.append(u"engine の指紋の欄が 4 つの決まった名前でない")
    base = fake_engine_fp()
    if run_stops(ms, rt_rec=fake_rt_rec(base)) is not False:
        out.append(u"engine の指紋が同じなのに止まる")
    for k in ms.FP_KEYS:
        fp = collections.OrderedDict(base)
        fp[k] = u"x-%s" % (base[k],)
        if run_stops(ms, rt_rec=fake_rt_rec(fp)) is not True:
            out.append(u"engine の指紋の欄 %s だけが違うのに止まらない" % k)
    return out


def full_path_problems(ms=None):
    u"""400 本の経路(``full``)で ``wiring`` に渡す期待が、便 RT の記録の「段 1」の「行(後)」・P の行 794 から取られる。"""
    ms = ms or MS
    out = []
    cap = []
    run_orchestrate(ms, capture=cap)
    if cap != [(None, None)]:
        out.append(u"小さい母集団の経路が wiring に期待を渡している: %s" % (cap,))
    cap = []
    run_orchestrate(ms, full=True, capture=cap)
    if cap != [(13, 794)]:
        out.append(u"400 本の経路が wiring に渡す期待が(便 RT の記録の行(後)・794)でない: %s" % (cap,))
    if run_stops(ms, full=True) is not True:
        out.append(u"400 本の経路で行の数・P の行の数が期待と違うのに止まらない")
    return out


def snapshot_problems(ms=None):
    u"""材料の置き場の件数か名前が測定の間に変われば止まる。"""
    ms = ms or MS
    out = []
    if run_stops(ms, hook=lambda d: None) is not False:
        out.append(u"置き場が変わらないのに止まる")
    if run_stops(ms, hook=lambda d: open(os.path.join(d, u"added.zip"), "w").close()) is not True:
        out.append(u"置き場に file が増えたのに止まらない")
    if run_stops(ms, hook=lambda d: os.rename(os.path.join(d, u"s2.zip"), os.path.join(d, u"renamed.zip"))) is not True:
        out.append(u"置き場の名前が変わった(件数は同じ)のに止まらない")
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


P_NEW = u"other"


# ---------------------------------------------------------------- 8. 記録
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


FORBIDDEN_KEYS = (u"文", u"span", u"sentence", u"値", u"要素名", u"context", u"name", u"会社名", u"証券コード", u"docID", u"value", u"text", u"数", u"recomputed", u"subject", u"主語", u"語")


def leak_problems(text):
    u"""記録に文・値・要素名・主語の語・枠の id・会社名・docID が無い(禁止の欄の名前・字の形・手書きの語彙の語と要素名)。"""
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
    body = json.dumps(rec, ensure_ascii=False)
    for word, elems in MS.V.PROFILES[u"P33E"].subjects:
        if len(word) >= 2 and u'"%s"' % word in body:
            out.append(u"記録に主語の語が在る")
        for e in elems:
            if e in body:
                out.append(u"記録に要素名が在る")
    return list(sorted(set(out)))


def old_population():
    return load_json(u"fixtures/xbrl/tanshin_self/population_2026-11-14.json")[u"行"]


def nd(n, d):
    return collections.OrderedDict([(u"分子", n), (u"分母", d)])


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
    if now != fp_rt or now != fake_engine_fp():
        out.append(u"記録の engine の指紋が便 RT の記録の今・今の engine と合わない")
    for k in (K_RT, K_S1, K_S2, K_PRED, K_FG, u"切り出し"):
        if k not in rec:
            return out + [u"記録に欄が無い: %s" % k]
    # ---- 切り出し・配線
    tss = load_json(u"fixtures/xbrl/tanshin_self/states_2026-11-14.json")[u"本"]
    ncut = sum(1 for b in tss if b[u"切り出し"] == u"切れた")
    cut = rec[u"切り出し"]
    if (cut[u"本"], cut[u"切れた本"], cut[u"切れない本"]) != (400, ncut, 400 - ncut):
        out.append(u"切り出しの数が TSS の記録の切り出しと違う")
    wire = rec[K_RT]
    s1_rt = rt[u"段 1(第 1 便。400 本の判定)"]
    if wire[u"本"] != 400 or wire[u"「前」の行が便 RT の段 1 の行と同じ本"] != 400 or wire[u"「前」の行"] != s1_rt[u"行(後)"] or wire[u"P の行(前)"] != 794 or wire[u"P の行のうち後でも同じ鍵・state・reason で在る行"] != 794:
        out.append(u"配線の確認の数が(400 本・便 RT の記録の行(後)・P 794)と違う")
    # ---- 段 1: 変わった行の一覧から数え直す
    s1 = rec[K_S1]
    w = s1[u"全体"]
    diff = [tuple(x) for x in s1[u"変わった行(state・reason・pointer のどれか。pointer だけの行も入る)"]]
    only_b = [tuple(x) for x in s1[u"前にだけ在る行"]]
    only_a = [tuple(x) for x in s1[u"後にだけ在る行"]]
    if w[u"前の行"] != wire[u"「前」の行"] or w[u"両方に在る行"] != w[u"前の行"] - len(only_b) or w[u"後の行"] != w[u"両方に在る行"] + len(only_a):
        out.append(u"段 1 の行の数が前にだけ・後にだけの一覧から数え直した数と違う")
    n_state = sum(1 for x in diff if x[3] != x[4])
    n_reason = sum(1 for x in diff if x[3] == x[4] and x[5] != x[6])
    n_ptr = len(diff) - n_state - n_reason
    if (w[u"state が変わった行"], w[u"state は同じで reason だけ変わった行"], w[u"state も reason も同じで pointer の並びだけ変わった行"]) != (n_state, n_reason, n_ptr) \
            or w[u"全部同じ行"] != w[u"両方に在る行"] - len(diff):
        out.append(u"段 1 の state・reason・pointer の行の数が一覧から数え直した数と違う")
    if w[u"state が変わった行を持つ本"] != len(set(x[0] for x in diff if x[3] != x[4])):
        out.append(u"段 1 の state が変わった行を持つ本が一覧と違う")
    tr = w[u"state の移り変わり(前 → 後。両方に在る行)"]
    for a in STATES:
        for b in STATES:
            if a != b and tr[u"%s → %s" % (a, b)] != sum(1 for x in diff if (x[3], x[4]) == (a, b)):
                out.append(u"段 1 の移り変わりの表の対角でない升が一覧と違う: %s → %s" % (a, b))
    if sum(tr.values()) != w[u"両方に在る行"] or w[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"] != sum(1 for x in diff if x[3] == G and x[4] != G) \
            or w[u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)"] != sum(1 for x in diff if x[3] != G and x[4] == G) \
            or w[u"前は GROUNDED で後に無い行(前にだけ在る行)"] != sum(1 for x in only_b if x[3] == G):
        out.append(u"段 1 の GROUNDED の向き・移り変わりの合計が一覧と違う")
    if sum(s1[u"群別"][g][u"state が変わった行"] for g in (u"甲", u"乙", u"丙")) != w[u"state が変わった行"] or sum(s1[u"群別"][g][u"前の行"] for g in (u"甲", u"乙", u"丙")) != w[u"前の行"]:
        out.append(u"段 1 の群別の合計が全体と違う")
    group_of = dict((r[0], r[1]) for r in old_population())
    for g in (u"甲", u"乙", u"丙"):
        if s1[u"群別"][g][u"state が変わった行"] != sum(1 for x in diff if x[3] != x[4] and group_of[x[0]] == g):
            out.append(u"段 1 の群別が一覧と違う: %s" % g)
    if sum(v[u"state が変わった行"] for v in s1[u"前の state 別"].values()) != w[u"state が変わった行"] or sum(v[u"両方に在る行"] for v in s1[u"前の state 別"].values()) != w[u"両方に在る行"]:
        out.append(u"段 1 の前の state 別の合計が全体と違う")
    for s_ in STATES:
        if s1[u"前の state 別"][s_][u"state が変わった行"] != sum(1 for x in diff if x[3] != x[4] and x[3] == s_):
            out.append(u"段 1 の前の state 別が一覧と違う: %s" % s_)
    if w[u"前の GROUNDED の行"] != sum(tr[u"%s → %s" % (G, b)] for b in STATES) + sum(1 for x in only_b if x[3] == G):
        out.append(u"段 1 の前の GROUNDED の行が移り変わりの表から数え直した数と違う")
    fg = rec[K_FG]
    if fg[u"切れた本"] != ncut or fg[u"fact の個数が前より減った本"] != 0 or not (0 < fg[u"fact の個数が前より増えた本"] <= ncut) or fg[u"fact の個数の合計(後)"] <= fg[u"fact の個数の合計(前)"]:
        out.append(u"fact の個数の確かめ(SE-2a の欠陥の確認)が合わない")
    # ---- 段 2: 行から数え直す
    s2 = rec[K_S2]
    rows = s2[u"行"]
    keys = [tuple(r[:3]) for r in rows]
    if s2[u"P の行"] != len(rows) or len(set(keys)) != len(keys) or keys != sorted(keys) or len(rows) != 794:
        out.append(u"段 2 の P の行が 794 行・鍵が重ならない・鍵の順でない")
    if any(len(r) != 12 for r in rows) or any(r[3] != group_of.get(r[0]) for r in rows):
        out.append(u"段 2 の行の欄の数か群が母集団の表と違う")
    for r in rows:
        for (il, iv, ih, io_) in ((4, 5, 6, 7), (8, 9, 10, 11)):
            lab, anyv, how, lab_o = r[il], r[iv], r[ih], r[io_]
            if lab not in LABELS or lab_o not in LABELS or not isinstance(anyv, bool) or how not in (None, EXACT, LOOSE):
                out.append(u"段 2 の行の札・値・届き方の字が違う: %s" % (r[:3],))
                break
            if (lab in (L_NA, L_FE) and anyv) or (lab in (L_BOTH, L_VAL) and not anyv) or (lab in (L_NAME, L_NONE) and anyv) or (lab in (L_BOTH, L_NAME) and how is None) or (lab == L_NONE and how is not None):
                out.append(u"段 2 の行の札と値・届き方が合わない: %s" % (r[:3],))
                break
            if (lab == L_NA) != (lab_o == L_NA) or (lab in (L_NS, L_OV) and lab_o != lab):
                out.append(u"段 2 の行の札(他)が自分の本の札と合わない(当てない・主語なし・語彙の外は本によらない): %s" % (r[:3],))
                break
        if r[4] != L_NA and r[8:12] != r[4:8]:
            out.append(u"字のとおりで当てた行の円の族の読みの欄が字のとおりと違う: %s" % (r[:3],))
            break
    for rd in (LIT, FAM):
        if s2[u"読み"][rd] != ms.tally_reading(rows, rd):
            out.append(u"段 2 の読み %s の数が行から数え直した数と違う" % rd)
        t = s2[u"読み"][rd]
        if sum(t[u"札"].values()) != len(rows) or sum(t[u"対照: 札(他)"].values()) != len(rows):
            out.append(u"段 2 の札の合計が行の数と違う: %s" % rd)
    if sum(1 for r in rows if r[4] == L_NA) != sum(1 for r in rows if r[8] == L_NA) + sum(1 for r in rows if r[4] == L_NA and r[8] != L_NA) or any(r[8] == L_NA and r[4] != L_NA for r in rows):
        out.append(u"円の族で当てない行が字のとおりで当てない行より多い")
    # 読みの軸との重ね
    rtypes = load_json(u"fixtures/xbrl/plan_source/read_types_2026-11-17.json")[u"行"]
    if s2[u"読みの軸との重ね"] != ms.overlay(rows, rtypes) or s2[u"読みの軸との重ね"][u"甲組・乙組の行"] != 90:
        out.append(u"読みの軸との重ねが行・read_types から数え直した数と違う")
    # 予測
    if rec[K_PRED] != ms.predictions(s1, fg, s2):
        out.append(u"予測の判定に要る数が段の欄からの作り直しと違う")
    if rec.get(u"限界") != list(ms.LIMITS):
        out.append(u"限界が script の字と違う")
    # ---- 便 PS の記録の P の行と合う(鍵・当てない・字のとおりの自(便 RT の記録で変わった欄を除く))
    ps = load_json(u"fixtures/xbrl/plan_source/states_2026-11-17.json")[u"行"]
    ps_p = dict(((r[0], r[1], r[2]), r) for r in ps if r[3] == u"P")
    s5 = rt[u"段 5(便 PS。サマリーの当てる先)"]
    changed = dict(((x[0], x[1], x[2]), x[4]) for x in s5[u"変わった行"] if x[3] == u"P")
    gone = set(tuple(x[:3]) for x in s5[u"消えた行"] if x[3] == u"P")
    new = set(tuple(x[:3]) for x in s5[u"増えた行"] if x[3] == u"P")
    expect_keys = (set(ps_p) - gone) | new
    if set(keys) != expect_keys:
        out.append(u"段 2 の P の行の鍵が便 PS の記録の P の行に便 RT の記録の消えた行・増えた行を足し引きした鍵と違う")
    for r in rows:
        k = tuple(r[:3])
        if k not in ps_p:
            continue
        o = ps_p[k]
        if (r[4] == L_NA) != bool(o[5]) or (r[8] == L_NA) != bool(o[10]):
            out.append(u"段 2 の当てない(字のとおり・円の族)が便 PS の記録の当てないと違う: %s" % (k,))
            break
        if 7 not in changed.get(k, []) and r[4] != L_NA and bool(r[5]) != bool(o[7]):
            out.append(u"段 2 の字のとおりの「F のどれかに値が合う」が便 PS の記録の自と違う: %s" % (k,))
            break
        if 11 not in changed.get(k, []) and r[8] != L_NA and bool(r[9]) != bool(o[11]):
            out.append(u"段 2 の円の族の「F のどれかに値が合う」が便 PS の記録の自(円の族)と違う: %s" % (k,))
            break
    return out


# ---------------------------------------------------------------- 9. 配線
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
    if sorted(c.args[0].value for c in loads if c.args and isinstance(c.args[0], ast.Constant)) != sorted(["xbrl_tss_retake_2026-11-18.py", "xbrl_plan_source_2026-11-17.py"]):
        out.append(u"読む前の便の script が便 RT・便 PS の 2 本だけでない")
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
    (u"M01 封の commit の定数を替える", u'SEAL_COMMIT = "fabd87ba"', u'SEAL_COMMIT = "fabd87bb"', ("seal",)),
    (u"M02 記録の path の定数を替える", u'RECORD_REL = REC_DIR_REL + "/states_2026-11-18.json"', u'RECORD_REL = REC_DIR_REL + "/states_2026-11-19.json"', ("seal",)),
    (u"M03 入力の表の 1 つの sha256 を替える", u'"a61da3fc3c336e80a214a5fc71978d9ce63f52b4eec5a763e91f434c2ef06d05"', u'"b61da3fc3c336e80a214a5fc71978d9ce63f52b4eec5a763e91f434c2ef06d05"', ("input_sha", "seal_table", "wire_inputs")),
    (u"M04 入力の sha256 の照合を外す", u"if not os.path.isfile(p) or ST.sha256_file(p) != want:", u"if False:", ("wire_inputs",)),
    (u"M05 札の順の入れ替え(F が空と当てない)", u"LABELS = (L_NA, L_FEMPTY, L_NOSUBJ, L_OUTVOCAB, L_BOTH, L_VALONLY, L_NAMEONLY, L_NEITHER)", u"LABELS = (L_FEMPTY, L_NA, L_NOSUBJ, L_OUTVOCAB, L_BOTH, L_VALONLY, L_NAMEONLY, L_NEITHER)", ("seal",)),
    (u"M06 札 1 と 2 の判定の順を入れ替える", u"    if PS.claim_kind(claim, reading) is None:\n        return L_NA, any_v, None\n    if not facts:\n        return L_FEMPTY, any_v, None\n",
     u"    if not facts:\n        return L_FEMPTY, any_v, None\n    if PS.claim_kind(claim, reading) is None:\n        return L_NA, any_v, None\n", ("label",)),
    (u"M07 札 2(F が空)を主語なしより後にする", u"    if not facts:\n        return L_FEMPTY, any_v, None\n    subject = claim.get(\"subject\")\n    if not subject:\n        return L_NOSUBJ, any_v, None\n",
     u"    subject = claim.get(\"subject\")\n    if not subject:\n        return L_NOSUBJ, any_v, None\n    if not facts:\n        return L_FEMPTY, any_v, None\n", ("label",)),
    (u"M08 主語なしと語彙の外の判定の順を入れ替える", u"    subject = claim.get(\"subject\")\n    if not subject:\n        return L_NOSUBJ, any_v, None\n    found, elems = subject_elems(subject, subjects)\n    if not found:\n        return L_OUTVOCAB, any_v, None\n",
     u"    subject = claim.get(\"subject\")\n    found, elems = subject_elems(subject, subjects)\n    if not found:\n        return L_OUTVOCAB, any_v, None\n    if not subject:\n        return L_NOSUBJ, any_v, None\n", ("label",)),
    (u"M09 完全一致が在っても部分一致を見る(完全一致を優先しない)", u"    if exact:\n        return exact, REACH_EXACT\n", u"    if False:\n        return exact, REACH_EXACT\n", ("label", "facts_for")),
    (u"M10 完全一致と部分一致の和を N にする", u"    if exact:\n        return exact, REACH_EXACT\n    loose = [f for f in facts if is_loose_name(f[0].split(\":\")[-1], elems)]\n",
     u"    loose = [f for f in facts if is_loose_name(f[0].split(\":\")[-1], elems)]\n    if exact:\n        return exact + [f for f in loose if f not in exact], REACH_EXACT\n", ("label", "facts_for")),
    (u"M11 部分一致が大文字小文字を区別する", u"    return any(e.lower() in local.lower() for e in elems)", u"    return any(e in local for e in elems)", ("label", "facts_for")),
    (u"M12 完全一致の SummaryOfBusinessResults の条件を落とす", u"local == e + \"SummaryOfBusinessResults\" or local == e.replace(\"Income\", \"IncomeLoss\") + \"SummaryOfBusinessResults\" for e in elems)",
     u"False for e in elems)", ("label", "facts_for")),
    (u"M13 完全一致の IncomeLoss の条件を落とす", u" or local == e.replace(\"Income\", \"IncomeLoss\") + \"SummaryOfBusinessResults\" for e in elems)", u" for e in elems)", ("facts_for",)),
    (u"M14 語が字で同じ組でなく前方一致で要素名を合わせる", u"        if word == subject:\n            found = True", u"        if subject.startswith(word):\n            found = True", ("label",)),
    (u"M15 同じ語の組を最初の 1 つしか合わせない", u"            for e in elems:\n                if e not in out:\n                    out.append(e)\n", u"            for e in elems:\n                if e not in out and not out:\n                    out.append(e)\n", ("label",)),
    (u"M16 読みを取り違える(当てるかどうかを常に字のとおりで見る)", u"    if PS.claim_kind(claim, reading) is None:\n        return L_NA, any_v, None", u"    if PS.claim_kind(claim, READ_LITERAL) is None:\n        return L_NA, any_v, None", ("label", "orch")),
    (u"M17 値の照合を常に字のとおりで見る", u"    return any(PS.match_fact(claim, f[1], f[2], reading) for f in facts)", u"    return any(PS.match_fact(claim, f[1], f[2], READ_LITERAL) for f in facts)", ("label", "orch")),
    (u"M18 row_labels が読みの順を入れ替える", u"    for rd in READINGS:\n        lab, anyv, how = label_claim(claim, rd, f_self, subjects)", u"    for rd in reversed(READINGS):\n        lab, anyv, how = label_claim(claim, rd, f_self, subjects)", ("label", "orch")),
    (u"M19 row_labels の対照が自分の本の F を使う", u"        lab_o, _a, _h = label_claim(claim, rd, f_other, subjects)", u"        lab_o, _a, _h = label_claim(claim, rd, f_self, subjects)", ("label", "orch")),
    (u"M20 値だけを N の中の値で判定する(F 全体を見ない)", u"    if any_v:\n        return L_VALONLY, any_v, how", u"    if False:\n        return L_VALONLY, any_v, how", ("label", "orch")),
    (u"M21 名前だけが N の空でないことでなく空であることを見る", u"    if n:\n        return L_NAMEONLY, any_v, how", u"    if not n:\n        return L_NAMEONLY, any_v, how", ("label",)),
    (u"M22 orchestrate の対照が自分の本の輪(自分自身)を指す", u"    s2 = stage2(books, other, read_rec[u\"行\"])", u"    s2 = stage2(books, dict((n, n) for n in other), read_rec[u\"行\"])", ("orch",)),
    (u"M23 p_rows_of の対照が自分の本の F を使う", u"by_n[other[b[u\"#\"]]][u\"F\"]", u"b[u\"F\"]", ("orch",)),
    (u"M24 別の本の輪を F が空でも作る", u"    other = PS.other_books([(b[u\"群\"], b[u\"#\"], b[u\"切れた\"], bool(b[u\"F\"])) for b in books])", u"    other = PS.other_books([(b[u\"群\"], b[u\"#\"], b[u\"切れた\"], True) for b in books])", ("orch",)),
    (u"M25 P の行でなく P でない行を段 2 に入れる", u"            if why != REASON_P:\n                continue", u"            if why == REASON_P:\n                continue", ("orch",)),
    (u"M26 「後」の ZIP にサマリーを入れ忘れる", u"        out.writestr(TSS._info(SUMMARY_NAME), summary_bytes)\n", u"        pass\n", ("after_zip", "job")),
    (u"M27 「後」の ZIP のサマリーの bytes を変える", u"        out.writestr(TSS._info(SUMMARY_NAME), summary_bytes)\n", u"        out.writestr(TSS._info(SUMMARY_NAME), summary_bytes.strip())\n", ("after_zip",)),
    (u"M28 「後」の ZIP が「前」の member を落とす", u"        for info in z.infolist():\n            out.writestr(TSS._info(info.filename), z.read(info.filename))\n", u"        for info in z.infolist()[:-1]:\n            out.writestr(TSS._info(info.filename), z.read(info.filename))\n", ("after_zip",)),
    (u"M29 「後」の ZIP のサマリーの名前を変える", u"SUMMARY_NAME = PS.SUMMARY_MEMBER", u"SUMMARY_NAME = \"XBRL/PublicDoc/summary.htm\"", ("seal", "after_zip")),
    (u"M30 サマリーの名前が既に在っても止めない", u"        if SUMMARY_NAME in names:\n            raise Stop(u\"**包んだ ZIP にサマリーの名前が既に在る。止める**\")\n", u"", ("after_zip",)),
    (u"M31 book_job の「前」と「後」を取り違える", u"    book[u\"前\"] = [row4(r, c) for r, c in before]\n    book[u\"後\"] = [row4(r, c) for r, c in after]\n", u"    book[u\"前\"] = [row4(r, c) for r, c in after]\n    book[u\"後\"] = [row4(r, c) for r, c in before]\n", ("job",)),
    (u"M32 book_job の「後」を「前」の ZIP で作る", u"    after = PS.claims_of(after_zip(wrapped, PS.summary_member_bytes(zb)))", u"    after = PS.claims_of(wrapped)", ("job",)),
    (u"M33 book_job の fact の個数の「後」が前の ZIP", u"    book[u\"fact(後)\"] = len(I.load_instance(after_zip(wrapped, PS.summary_member_bytes(zb)))[\"facts\"])", u"    book[u\"fact(後)\"] = len(I.load_instance(wrapped)[\"facts\"])", ("job",)),
    (u"M34 book_job の前の claim が「後」の claim", u"for r, _c in before]", u"for r, _c in after]", ("job",)),
    (u"M35 book_job の RT の行を「前」の ZIP の claim で作る", u"    book[u\"RT の行\"] = [[r[0], r[1], r[2], r[3]] for r in rt[u\"行\"]]", u"    book[u\"RT の行\"] = [[r[0], r[1], r[2], r[3]] for r in rt[u\"行\"]][:1]", ("job",)),
    (u"M36 book_job が材料の sha256 を確かめない", u"    if ST.sha256_bytes(zb) != sha:\n        raise Stop(u\"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**\" % n)\n    text = TSS.cut(zb)[0]", u"    text = TSS.cut(zb)[0]", ("job",)),
    (u"M37 forecast_facts の F の個数の確かめを外す", u"    if len(f_list) != len(PS.split_facts(inst)[0]):", u"    if False:", ("forecast",)),
    (u"M38 forecast_facts が単位の無い fact を入れる", u"        if not f.get(\"unit\") or not f.get(\"value\"):\n            continue\n        if PS.is_forecast_context", u"        if not f.get(\"value\"):\n            continue\n        if PS.is_forecast_context", ("forecast",)),
    (u"M39 forecast_facts が値 0 の fact を入れる", u"        if not f.get(\"unit\") or not f.get(\"value\"):\n            continue\n        if PS.is_forecast_context", u"        if not f.get(\"unit\"):\n            continue\n        if PS.is_forecast_context", ("forecast",)),
    (u"M40 forecast_facts が予想の枠でない fact を入れる", u"        if PS.is_forecast_context(inst[\"contexts\"].get(f.get(\"context\"))):\n            f_list.append", u"        if True:\n            f_list.append", ("forecast",)),
    (u"M41 forecast_facts が名前を落とす", u"            f_list.append((f[\"name\"], f[\"unit\"], f[\"value\"]))", u"            f_list.append((\"\", f[\"unit\"], f[\"value\"]))", ("forecast", "job")),
    (u"M42 compare_rows が前と後の行を取り違える", u"    before, after = key_rows(books, u\"前\"), key_rows(books, u\"後\")", u"    after, before = key_rows(books, u\"前\"), key_rows(books, u\"後\")", ("compare", "orch")),
    (u"M43 compare_rows が pointer だけの違いを state が変わった行に数える", u"        if b[0] != a[0]:\n            return u\"state\"", u"        if b[0] != a[0] or b[2] != a[2]:\n            return u\"state\"", ("compare", "orch")),
    (u"M44 compare_rows が pointer の違いを見ない", u"        if b[2] != a[2]:\n            return u\"pointer\"", u"        if False:\n            return u\"pointer\"", ("compare", "orch")),
    (u"M45 compare_rows が reason の違いを見ない", u"        if b[1] != a[1]:\n            return u\"reason\"", u"        if False:\n            return u\"reason\"", ("compare", "orch")),
    (u"M46 compare_rows の鍵に位置を入れない", u"            out[(b[u\"#\"], si, pos)] = (st, why, tuple(ptr))", u"            out[(b[u\"#\"], si, 0)] = (st, why, tuple(ptr))", ("compare",)),
    (u"M47 compare_rows の鍵に本の # を入れない", u"            out[(b[u\"#\"], si, pos)] = (st, why, tuple(ptr))", u"            out[(0, si, pos)] = (st, why, tuple(ptr))", ("compare",)),
    (u"M48 compare_rows の GROUNDED でなくなった行が前後を取り違える", u"sum(1 for k in changed if before[k][0] == G)),\n            (u\"前は GROUNDED でなく後は GROUNDED の行", u"sum(1 for k in changed if after[k][0] == G)),\n            (u\"前は GROUNDED でなく後は GROUNDED の行", ("compare",)),
    (u"M49 compare_rows の前の GROUNDED の行を後から数える", u"sum(1 for k in list(keys_both) + list(keys_only_b) if before[k][0] == G)", u"sum(1 for k in list(keys_both) + list(keys_only_a) if after[k][0] == G)", ("compare",)),
    (u"M50 compare_rows の群別が群を取り違える", u"(g, part([k for k in both if grp_of[k[0]] == g]", u"(g, part([k for k in both if grp_of[k[0]] != g]", ("compare",)),
    (u"M51 compare_rows の移り変わりの表が(後 → 前)", u"        trans = collections.Counter((before[k][0], after[k][0]) for k in keys_both)", u"        trans = collections.Counter((after[k][0], before[k][0]) for k in keys_both)", ("compare",)),
    (u"M52 compare_rows の前にだけ在る行を後にだけ在る行と取り違える", u"    only_b = sorted(k for k in before if k not in after)\n    only_a = sorted(k for k in after if k not in before)", u"    only_a = sorted(k for k in before if k not in after)\n    only_b = sorted(k for k in after if k not in before)", ("compare", "orch")),
    (u"M53 fact_growth が増えた本を数えない", u"(u\"fact の個数が前より増えた本\", sum(1 for b in cut if b[u\"fact(後)\"] > b[u\"fact(前)\"]))", u"(u\"fact の個数が前より増えた本\", sum(1 for b in cut if b[u\"fact(後)\"] >= b[u\"fact(前)\"]))", ("compare",)),
    (u"M54 配線の確認の便 RT の行の照合を外す", u"        if [list(r[:4]) for r in b[u\"前\"]] != [list(r) for r in b[u\"RT の行\"]]:", u"        if False:", ("wiring", "orch")),
    (u"M55 配線の確認の P の行の数を確かめない", u"    if expect_p is not None and len(p_keys) != expect_p:", u"    if False:", ("wiring",)),
    (u"M56 配線の確認の「前」の行の数を確かめない", u"    if expect_rows is not None and len(before) != expect_rows:", u"    if False:", ("wiring",)),
    (u"M57 配線の確認の P の行が後で在るかを確かめない", u"        if k not in after or after[k][0] != before[k][0] or after[k][1] != before[k][1]:", u"        if False:", ("wiring", "orch")),
    (u"M58 配線の確認の P の行の state の同じを確かめない", u"        if k not in after or after[k][0] != before[k][0] or after[k][1] != before[k][1]:", u"        if k not in after or after[k][1] != before[k][1]:", ("wiring",)),
    (u"M59 engine の指紋が違っても止めない", u"    if now != want:", u"    if False:", ("orch",)),
    (u"M60 配線の確認を 400 本のときだけでなく常に外す", u"    wire = wiring(books, rt_rec[u\"段 1(第 1 便。400 本の判定)\"][u\"行(後)\"] if full else None, EXPECT_P if full else None)", u"    wire = collections.OrderedDict([(u\"本\", 0)])", ("orch",)),
    (u"M61 読みの軸との重ねが W 組も数える", u"    sel = [t for t in read_types if t[4] in (PS.GRP_KOU, PS.GRP_OTSU)]", u"    sel = [t for t in read_types if t[4] in (PS.GRP_KOU, PS.GRP_OTSU, PS.GRP_W)]", ("orch",)),
    (u"M62 読みの軸との重ねが字のとおりの読みの札を数える", u"    c = COLS[READ_FAMILY]\n    found = [", u"    c = COLS[READ_LITERAL]\n    found = [", ("orch",)),
    (u"M63 読みの軸との重ねの鍵が文の番号と位置を取り違える", u"    keyed = dict(((r[C_BOOK], r[C_SI], r[C_POS]), r) for r in rows)", u"    keyed = dict(((r[C_BOOK], r[C_POS], r[C_SI]), r) for r in rows)", ("orch",)),
    (u"M64 SE-7 の分母を引けた行にする", u"(u\"SE-7 読みの軸の甲組・乙組の行のうち円の族の読みで両方 / 甲組・乙組の行\", frac(ov[u\"円の族の読みの札\"][L_BOTH], ov[u\"甲組・乙組の行\"]))", u"(u\"SE-7 読みの軸の甲組・乙組の行のうち円の族の読みで両方 / 甲組・乙組の行\", frac(ov[u\"円の族の読みの札\"][L_BOTH], ov[u\"鍵が段 2 の P の行に引けた行\"]))", ("orch",)),
    (u"M65 SE-5 の分母を札 1・2 でない行にする", u"(u\"SE-5 両方 / F のどれかに値が合う行(字のとおり。主)\", frac(labs[L_BOTH], lit[u\"F のどれかに値が合う行(副の分母)\"]))", u"(u\"SE-5 両方 / F のどれかに値が合う行(字のとおり。主)\", frac(labs[L_BOTH], lit[u\"札 1・2 でない行(副の分母)\"]))", ("orch",)),
    (u"M66 SE-4 の分子が主語なしだけ", u"        return frac(n[L_NOSUBJ] + n[L_OUTVOCAB], t[u\"札 1・2 でない行(副の分母)\"])", u"        return frac(n[L_NOSUBJ], t[u\"札 1・2 でない行(副の分母)\"])", ("orch",)),
    (u"M67 SE-6 の分子が自分の本の両方", u"frac(lit[u\"対照: 両方(他)の行\"], labs[L_BOTH])", u"frac(lit[u\"両方の行(自分の本)\"], labs[L_BOTH])", ("orch",)),
    (u"M68 SE-3 の分母が両方に在る行", u"frac(w[u\"前は GROUNDED で後は GROUNDED でない行(両方に在る行)\"], w[u\"前の GROUNDED の行\"])", u"frac(w[u\"前は GROUNDED で後は GROUNDED でない行(両方に在る行)\"], w[u\"両方に在る行\"])", ("orch",)),
    (u"M69 SE-2b の分母が両方に在る行(前の行ではない)", u"frac(w[u\"state が変わった行\"], w[u\"前の行\"])", u"frac(w[u\"state が変わった行\"], w[u\"後の行\"] + 1)", ("orch",)),
    (u"M70 SE-2a の欠陥の確認が減った本を数える", u"frac(fg[u\"fact の個数が前より増えた本\"], fg[u\"切れた本\"])", u"frac(fg[u\"fact の個数が前より減った本\"], fg[u\"切れた本\"])", ("orch",)),
    (u"M71 札の副の分母(F のどれかに値が合う行)が札 1・2 を含める", u"    anyv = [r for r in rows if r[c[u\"値\"]]]", u"    anyv = [r for r in rows if r[c[u\"値\"]] or r[c[u\"札\"]] == L_NA]", ("orch",)),
    (u"M72 札 5 の届き方が全部の行を数える", u"(h, sum(1 for r in both if r[c[u\"届\"]] == h))", u"(h, sum(1 for r in rows if r[c[u\"届\"]] == h))", ("orch",)),
    (u"M73 通信の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport urllib.request\n", ("import",)),
    (u"M74 許す一覧の外の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport shutil\n", ("import",)),
    (u"M75 前の便の script を 1 本足して読む(行を足す)", u"PS = load_module(", u"def unused_loader():\n    return load_module(\"xbrl_nil_read_2026-11-17.py\", \"nr_for_se\")\n\n\nPS = load_module(", ("import",)),
    (u'M76 段 2 の P の行を「後」の行で選ぶ', u'zip(b[u"前"], b[u"前の claim"]):', u'zip(b[u"後"], b[u"前の claim"]):', ('p_rows',)),
    (u'M77 SE-1 の前にだけ在る行を後にだけ在る行の数で出す(逆も)', u'(u"前にだけ在る行", w[u"前にだけ在る行"]), (u"後にだけ在る行", w[u"後にだけ在る行"])', u'(u"前にだけ在る行", w[u"後にだけ在る行"]), (u"後にだけ在る行", w[u"前にだけ在る行"])', ('se1',)),
    (u'M78 SE-1 の後にだけ在る行を前にだけ在る行の数で出す', u'(u"後にだけ在る行", w[u"後にだけ在る行"])', u'(u"後にだけ在る行", w[u"前にだけ在る行"])', ('se1',)),
    (u'M79 語彙の既定が別の profile(P6)', u'subjects = V.PROFILES[PROFILE].subjects if subjects is None', u'subjects = V.PROFILES["P6"].subjects if subjects is None', ('default_voc',)),
    (u'M80 語彙の既定が別の profile(P1)', u'subjects = V.PROFILES[PROFILE].subjects if subjects is None', u'subjects = V.PROFILES["P1"].subjects if subjects is None', ('default_voc',)),
    (u'M81 engine の指紋の比較が 1 欄(adapter_xbrl_py_sha256)だけ', u'    if now != want:', u"    if now['adapter_xbrl_py_sha256'] != want['adapter_xbrl_py_sha256']:", ('fp',)),
    (u'M82 engine の指紋の比較が 1 欄(adapter_xbrl_py_files)だけ', u'    if now != want:', u"    if now['adapter_xbrl_py_files'] != want['adapter_xbrl_py_files']:", ('fp',)),
    (u'M83 engine の指紋の比較が 1 欄(core_py_sha256)だけ', u'    if now != want:', u"    if now['core_py_sha256'] != want['core_py_sha256']:", ('fp',)),
    (u'M84 engine の指紋の比較が 1 欄(core_py_files)だけ', u'    if now != want:', u"    if now['core_py_files'] != want['core_py_files']:", ('fp',)),
    (u'M85 400 本の経路の「行(後)」の期待を別の欄(行(前))から取る', u'[u"段 1(第 1 便。400 本の判定)"][u"行(後)"] if full', u'[u"段 1(第 1 便。400 本の判定)"][u"行(前)"] if full', ('full',)),
    (u'M86 400 本の経路の「行(後)」の期待を別の欄(両方に在る行)から取る', u'[u"段 1(第 1 便。400 本の判定)"][u"行(後)"] if full', u'[u"段 1(第 1 便。400 本の判定)"][u"両方に在る行"] if full', ('full',)),
    (u'M87 400 本の経路の P の行の期待が別の数', u'EXPECT_P if full else None', u'EXPECT_READ_ROWS if full else None', ('full',)),
    (u'M88 400 本の経路で行の期待を渡さない', u'rt_rec[u"段 1(第 1 便。400 本の判定)"][u"行(後)"] if full else None', u'None', ('full',)),
    (u'M89 材料の置き場の変化を見ない', u'    if before_names != ST.names_snapshot(mat):', u'    if False:', ('snapshot',)),
    (u'M90 check_text が漏れの検査を呼ばない', u'    TSS.check_clean(rec, scan, key_value)', u'    pass', ('clean',)),
)


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"seal_table": seal_table_problems, u"input_sha": input_sha_problems, u"wire_inputs": input_wire_problems, u"label": label_problems, u"facts_for": facts_for_problems,
             u"compare": compare_problems, u"wiring": wiring_problems, u"after_zip": after_zip_problems, u"forecast": forecast_problems, u"job": job_problems, u"orch": orchestrate_problems,
             u"p_rows": p_rows_problems, u"se1": se1_problems, u"default_voc": default_vocab_problems, u"fp": fingerprint_problems, u"full": full_path_problems, u"snapshot": snapshot_problems, u"clean": check_text_problems}
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


def history_problems_on(repo_dir, seal_short):
    return engine_zero_problems(repo_dir) + prior_docs_problems(repo_dir) + order_of(repo_dir, seal_short, others=["measure/s.py"])


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_tables_equal_the_seal(self):
        self.assertEqual([], seal_problems())
        self.assertEqual([], seal_table_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"SE-6", u"SE-8")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"3. 主語なし", u"3. 主語あり")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"完全一致が 1 つでも在れば部分一致は見ない", u"部分一致も見る")))
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


class LabelTest(unittest.TestCase):
    def test_e_1_the_eight_labels_in_order_exact_before_loose_two_readings_and_the_control(self):
        self.assertEqual([], label_problems())

    def test_e_2_the_name_selection_equals_instance_facts_for(self):
        self.assertEqual([], facts_for_problems())

    def test_e_3_the_forecast_facts_keep_names_and_stop_on_a_count_difference(self):
        self.assertEqual([], forecast_problems())


class Stage1Test(unittest.TestCase):
    def test_f_1_the_compare_rows_on_hand_computed_made_up_books(self):
        self.assertEqual([], compare_problems())

    def test_f_2_the_wiring_check_stops(self):
        self.assertEqual([], wiring_problems())


class WireTest(unittest.TestCase):
    def test_g_1_the_after_zip_copies_every_member_and_adds_the_summary_unchanged(self):
        self.assertEqual([], after_zip_problems())

    def test_g_2_the_book_job_keeps_before_and_after_apart(self):
        self.assertEqual([], job_problems())

    def test_g_3_orchestrate_on_made_up_books_equals_the_hand_computation_and_stops(self):
        u"""作り物の本(甲 2・乙 3・丙 3)で ``orchestrate`` を本物のまま走らせる。対照は別の本の F・読みの順・配線の確認の止め。"""
        self.assertEqual([], orchestrate_problems())


class HardeningTest(unittest.TestCase):
    u"""独立監査 REVISE への強化。どれも MUTANTS(M76〜M90)で赤になることを ``test_j_1`` が確かめる。"""

    def test_k_1_the_p_rows_are_chosen_by_the_before_reason(self):
        self.assertEqual([], p_rows_problems())

    def test_k_2_se1_keeps_the_before_only_and_the_after_only_apart(self):
        self.assertEqual([], se1_problems())

    def test_k_3_the_default_vocabulary_is_the_p33e_one(self):
        self.assertEqual([], default_vocab_problems())

    def test_k_4_the_engine_fingerprint_stops_on_any_of_its_four_fields(self):
        self.assertEqual([], fingerprint_problems())

    def test_k_5_the_full_path_takes_the_expectation_from_the_retake_record(self):
        self.assertEqual([], full_path_problems())

    def test_k_6_a_change_of_the_material_folder_stops(self):
        self.assertEqual([], snapshot_problems())

    def test_k_7_check_text_stops_on_a_leak(self):
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
        self.assertNotEqual([], changed(lambda r: r[K_RT].__setitem__(u"P の行(前)", 793)))
        self.assertNotEqual([], changed(lambda r: r[K_S1][u"全体"].__setitem__(u"state が変わった行", r[K_S1][u"全体"][u"state が変わった行"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_S1][u"全体"].__setitem__(u"前の GROUNDED の行", r[K_S1][u"全体"][u"前の GROUNDED の行"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_S1][u"変わった行(state・reason・pointer のどれか。pointer だけの行も入る)"].pop()))
        self.assertNotEqual([], changed(lambda r: r[K_FG].__setitem__(u"fact の個数が前より増えた本", 0)))
        self.assertNotEqual([], changed(lambda r: r[K_S2][u"行"][0].__setitem__(4, L_BOTH if r[K_S2][u"行"][0][4] != L_BOTH else L_VAL)))
        self.assertNotEqual([], changed(lambda r: r[K_S2][u"行"].pop()))
        self.assertNotEqual([], changed(lambda r: r[K_S2][u"読み"][LIT][u"札"].__setitem__(L_BOTH, r[K_S2][u"読み"][LIT][u"札"][L_BOTH] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_S2][u"読み"][FAM].__setitem__(u"対照: 両方(他)の行", r[K_S2][u"読み"][FAM][u"対照: 両方(他)の行"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_S2][u"読みの軸との重ね"][u"円の族の読みの札"].__setitem__(L_BOTH, 0)))
        self.assertNotEqual([], changed(lambda r: r[K_PRED].__setitem__(u"SE-2a state が変わった行(1 行以上か)", 0)))
        self.assertNotEqual([], changed(lambda r: r[u"engine の指紋(今。便 RT の記録の今と同じ)"].__setitem__(u"core_py_sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r.__setitem__(u"限界", r[u"限界"][:-1])))
        self.assertNotEqual([], changed(lambda r: r[u"切り出し"].__setitem__(u"切れた本", r[u"切り出し"][u"切れた本"] + 1)))

    def test_h_3_a_record_with_a_sentence_a_value_an_element_name_or_a_subject_word_is_red(self):
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"要素名"] = u"jppfs_cor:NetSales"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"文"] = u"売上高は増加した"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"置き場"] = u"S100" + u"ABCD"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"x"] = u"売上高"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"x"] = u"Revenue"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        self.assertEqual([], leak_problems(read(RECORD_REL)))
        self.assertFalse(DOCID_RE.search(read(RECORD_REL)))


class WiringTest(unittest.TestCase):
    def test_i_1_the_script_imports_only_the_allowed_modules(self):
        self.assertEqual([], import_problems())

    def test_i_2_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with open(p, encoding="utf-8") as fh:
            self.assertNotIn(u"summary_engine", fh.read())

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
                fh.write("SE_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rel="g.py", base=d))

    def test_i_6_the_script_leaves_sys_modules_as_it_found_them(self):
        u"""前の便の script を読んでも、読み込みの前に居た名前を上書きしたまま残さない(門を 2 通りの順で走らせても赤くならない)。"""
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "summary_engine_script_for_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        self.assertIn("summary_engine_script_for_sysmodules_check", sys.modules)
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
        for name in (u"seal", u"seal_table", u"input_sha", u"wire_inputs", u"label", u"facts_for", u"compare", u"wiring", u"after_zip", u"forecast", u"job", u"orch", u"import",
                     u"p_rows", u"se1", u"default_voc", u"fp", u"full", u"snapshot", u"clean"):
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
