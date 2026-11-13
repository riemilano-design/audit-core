# -*- coding: utf-8 -*-
"""封 docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md(TSS ― 決算短信の概況の文を、同じ短信の添付の財務諸表で確かめる)の測定の門。封 §0-2・§1・§2・§3・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_tanshin_self_result.py`` は次の段。記録・文書・標本の行を縛る)

1. 封の字: §1 の表が 400 行(群 甲 50・乙 200・丙 150・様式の種類の数)・§3 が S-1〜S-10 の 10 行でどの行も欄・予測・外れ方を持つ・切り出しの正規表現 2 本・包み直しの名前・profile・種・標本の数・置き場・記録の path。
2. 封の字と script の定数が同じ(置く script と測る script)。表は封の file から読む(script に 400 行を写さない)。
3. engine 0 行: 封の commit から HEAD まで ``core/``・``adapters/``・``measure/lib``・``measure/inject.py`` と、この便が読み込む前の便の script・記録を触っていない。
4. 順序: 封 e56d6782 ⊏ script 2 本・この門(**commit の順**。未 commit は赤(skip にしない。2026-11-09 の門と同じ))。
5. 切り出し(``cut_lines``・``cut_html``・``cut``)・包み直し(``wrap``)・判定の配線(``judge_book``)・集計・標本・型の記録の振る舞い。
6. 置く script: 400 本そろわなければ何も書かない・sha256 が違う既存 file で止まる・``--out`` で本番に書かない・表に無い ZIP は写さない・様式の種類が違えば止まる・ほかの cache の一覧が変われば止まる・通信の module を import しない。
7. 配線: 前の便の関数を **呼ぶ**(同名の関数を定義しない)・読み込みの前に居た ``sys.modules`` の名前は戻る・既存の門が行頭の名前を数える変数名を置かない・docID・証券コード・TDnet の番号の字が無い。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。関数の字を 1 か所替えた版を module の中に差し込み、検査が赤になることを見て、必ず元の object に戻す)。
この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import ast
import collections
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
import os
import random
import re
import sys
import tempfile
import types
import unittest
import warnings
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_tanshin_self_seal")      # 順序の部品(order_problems・Repo・git_in・added_commits)。門としては走らせない
MS = load_module("measure/xbrl_tanshin_self_2026-11-14.py", "tanshin_self_script_for_seal_gate")
ST = MS.ST
TS = MS.TS
from adapters.xbrl import instance as I       # noqa: E402

SEAL_REL = "docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md"
SEAL_COMMIT_SHORT = "e56d6782"                 # 封の commit(literal に留める。script の定数と違えば script_problems が赤)
STAGE_REL = "measure/xbrl_tanshin_self_stage_2026-11-14.py"
SCRIPT_REL = "measure/xbrl_tanshin_self_2026-11-14.py"
SCRIPT_RELS = (STAGE_REL, SCRIPT_REL)
GATE_REL = "tests/measure/test_xbrl_tanshin_self_seal.py"
#: 結果の門(次の段で足す)。この段では順序の検査に入れない
LATER_GATE_REL = "tests/measure/test_xbrl_tanshin_self_result.py"
DOC_REL = "docs/XBRL_TANSHIN_SELF_RESULT_2026-11-14.md"
RECORD_RELS = ("fixtures/xbrl/tanshin_self/population_2026-11-14.json", "fixtures/xbrl/tanshin_self/states_2026-11-14.json", "fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json")
#: 封の commit から 0 行でなければならない path(engine・lib・仕掛けと、この便が読み込む 2026-11-09 の便の script・記録)
NOT_TOUCHED_RELS = ("adapters", "core", "measure/lib", "measure/inject.py", "measure/xbrl_tanshin_2026-11-09.py", "measure/xbrl_tanshin_fetch_2026-11-09.py", "fixtures/xbrl/tanshin")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT",
                     "FINGERPRINT_", "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL", "ENGINE_AT_MEASURE", "ENGINE_DECLARED")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
TDNET_RE = re.compile(r"0812\d{14}")
PRED_IDS = tuple("S-%d" % i for i in range(1, 11))
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx")
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"ZIP の member がちょうど `XBRLData/Attachment/qualitative.htm` のものを utf-8(strict)で読む。",
    u"`measure/xbrl_tanshin_2026-11-09.py` の `html_to_lines` で行にし、各行に NFKC を掛けて前後の空白を落とし、空の行を捨てる。",
    u"`^1\\s*\\.\\s*(経営成績等の概況|当中間決算に関する定性的情報|当四半期決算に関する定性的情報)`",
    u"`^2\\s*\\.\\s*[^\\d\\s]`",
    u"切れない(member なし)", u"切れない(decode)", u"切れない(始まりなし)", u"切れない(終わりなし)",
    u"NFKC を掛けたことは記録に書く",
    u"文は `XBRL/PublicDoc/zz_overview_ixbrl.htm` として入れる",
    u"`verify_document(包んだ ZIP, \"P33E\")` に渡す(`text` は渡さない)。",
    u"包んだ ZIP は memory の中だけで作り、どこにも書かない。",
    u"サマリー(`XBRLData/Summary/`)の iXBRL は入れない。",
    u"`~/.cache/audit-core/tanshin-self-2026-11-14/<sha256>.zip`",
    u"`random.Random(20261114).sample(range(行の数), 120)`",
    u"司令塔(**AI の席。人は読んでいない**)",
    u"採用 / 不採用の判定は無い",
    u"jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock",
)
SEAL_TABLE_ROW = re.compile(r"^\| (\d+) \| (甲|乙|丙) \| (\w+) \| `([0-9a-f]{64})` \| (切れた|切れない) \| (\d+|-) \|$", re.M)
#: 封 §0-1 の 3 の様式の種類の数(A = 甲 + 乙・B = 丙)
KINDS_A = collections.OrderedDict([(u"acedifsm", 43), (u"acedjpsm", 203), (u"anedjpsm", 4)])
KINDS_B = collections.OrderedDict([(u"scedifsy", 29), (u"scedjpsm", 7), (u"scedjpsy", 110), (u"snedjpsy", 4)])
#: 封 §1 の表の 400 行(# TAB 群 TAB 様式 TAB sha256 TAB 下見: 切り出し TAB 下見: claim を改行でつないだ字)の sha256。封の表の 1 字が変われば赤(封の file は commit で凍結されるが、門も字で留める)
TABLE_DIGEST = "e738f88be521383c1eb12b45eca313e4c94df73011485df1bd03da1adb55b752"


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def guard(fn, *a, **k):
    u"""検査を呼ぶ。例外は「問題」として返す(変異した関数が落ちても赤として数える)。"""
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  Stop(SystemExit)を含む
        return [u"例外: %s" % type(exc).__name__]


@contextlib.contextmanager
def mutated(mod, name, old, new):
    u"""``mod`` の関数 ``name`` の字の ``old`` を ``new`` に替えた版を、module の中に差し込む(使う側は module の名前で引くので届く)。出るときは必ず元の object に戻す。"""
    orig = getattr(mod, name)
    src = inspect.getsource(orig)
    assert old in src, (name, old)
    exec(compile(src.replace(old, new, 1), "<mutant %s>" % name, "exec"), mod.__dict__)
    assert getattr(mod, name) is not orig
    try:
        yield
    finally:
        mod.__dict__[name] = orig
        assert getattr(mod, name) is orig


@contextlib.contextmanager
def patched(mod, **kw):
    old = dict((k, getattr(mod, k)) for k in kw)
    for k, v in kw.items():
        setattr(mod, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(mod, k, v)


def tmpdir():
    return tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))


# ---------------------------------------------------------------- 1. 封の字
def seal_table(seal):
    u"""封 §1 の表 [(#, 群, 様式の種類, sha256, 下見: 切り出し, 下見: claim)]。"""
    try:
        sec = seal[seal.index(u"## §1"):seal.index(u"## §2")]
    except ValueError:
        return []
    return [(int(m[0]), m[1], m[2], m[3], m[4], m[5]) for m in SEAL_TABLE_ROW.findall(sec)]


def seal_problems(seal):
    out = []
    try:
        sec2 = seal[seal.index(u"## §2"):seal.index(u"## §3")]
        sec3 = seal[seal.index(u"## §3"):seal.index(u"## §4")]
        sec5 = seal[seal.index(u"## §5"):seal.index(u"## §6")]
    except ValueError:
        return [u"封の節(§1〜§6)が揃っていない"]
    rows = seal_table(seal)
    if len(rows) != 400:
        out.append(u"封 §1 の表が 400 行でない: %d" % len(rows))
    if hashlib.sha256(u"\n".join(u"%d\t%s\t%s\t%s\t%s\t%s" % r for r in rows).encode("utf-8")).hexdigest() != TABLE_DIGEST:
        out.append(u"封 §1 の表の字が、門に留めた sha256 と違う")
    if [r[0] for r in rows] != list(range(1, len(rows) + 1)):
        out.append(u"封 §1 の表の # が 1 から続いていない")
    if len(set(r[3] for r in rows)) != len(rows):
        out.append(u"封 §1 の表の sha256 に重複がある")
    g = collections.Counter(r[1] for r in rows)
    if [g[x] for x in (u"甲", u"乙", u"丙")] != [50, 200, 150]:
        out.append(u"封 §1 の群が 甲 50・乙 200・丙 150 でない")
    ka = collections.Counter(r[2] for r in rows if r[1] in (u"甲", u"乙"))
    kb = collections.Counter(r[2] for r in rows if r[1] == u"丙")
    if collections.OrderedDict(sorted(ka.items())) != KINDS_A or collections.OrderedDict(sorted(kb.items())) != KINDS_B:
        out.append(u"封 §1 の様式の種類の数が封 §0-1 の 3 と違う")
    a_cut = [r for r in rows if r[1] in (u"甲", u"乙") and r[4] == u"切れた"]
    b_cut = [r for r in rows if r[1] == u"丙" and r[4] == u"切れた"]
    if (len(a_cut), len(b_cut)) != (239, 133):
        out.append(u"封 §1 の下見の切れた本が A 239・B 133 でない")
    if (sum(int(r[5]) for r in a_cut if r[5].isdigit()), sum(int(r[5]) for r in b_cut if r[5].isdigit())) != (17697, 6834):
        out.append(u"封 §1 の下見の claim の合計が A 17,697・B 6,834 でない")
    ids = re.findall(r"^\| (S-\d+) \| (.*) \|$", sec3, re.M)
    if [i[0] for i in ids] != list(PRED_IDS):
        out.append(u"封 §3 の表が S-1〜S-10 の 10 行でない: %s" % [i[0] for i in ids])
    for k, rest in ids:
        cells = rest.split(u" | ")
        if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
            out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % k)
    for rel in SCRIPT_RELS:
        if rel not in sec5:
            out.append(u"封 §5 に script の path が無い: %s" % rel)
    for rel in (u"test_xbrl_tanshin_self_seal.py", u"test_xbrl_tanshin_self_result.py"):
        if rel not in sec2:
            out.append(u"封 §2 に門の path が無い: %s" % rel)
    for rel in RECORD_RELS + (DOC_REL,):
        if rel not in sec2:
            out.append(u"封 §2 に path が無い: %s" % rel)
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, ms=None, st=None):
    u"""封の字と script の定数が同じか。ms・st = script の module(試験が壊した写しを渡す)。"""
    ms = ms or MS
    st = st or ms.ST
    out = []
    want = [(r[0], r[1], r[2], r[3]) for r in seal_table(seal)]
    if list(st.population_from_text(seal)) != want:
        out.append(u"置く script が封の表と別の行を読む")
    if ms.ST is not st:
        out.append(u"測る script が置く script と別の instance を使っている")
    if st.SEAL_REL != SEAL_REL or ms.SEAL_REL != SEAL_REL or st.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_COMMIT != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if st.SCRIPT_REL != STAGE_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.STAGE_SCRIPT_REL != STAGE_REL or ms.DOC_REL != DOC_REL:
        out.append(u"script・結果の文書の path が封 §5 と違う")
    if (st.POPULATION_REL, ms.STATES_REL, ms.TYPES_REL) != RECORD_RELS:
        out.append(u"記録の path が封 §2 と違う")
    if st.N_ROWS != 400 or list(st.GROUP_COUNTS.items()) != [(u"甲", 50), (u"乙", 200), (u"丙", 150)]:
        out.append(u"母集団の本数・群の本数が封 §0-1 の 2・§1 と違う")
    if st.CACHE_NAME != "tanshin-self-2026-11-14" or not st.default_cache_dir().endswith(os.path.join(".cache", "audit-core", "tanshin-self-2026-11-14")):
        out.append(u"置き場の名前が封 §0-2 の 6 と違う")
    if u"edinetdb-p27" not in st.SKIP_CACHES:
        out.append(u"開かない cache folder が宣言されていない")
    if (st.SUMMARY_PREFIX, st.SUMMARY_FILE_PREFIX, st.SUMMARY_FILE_SUFFIX, st.KIND_LEN) != ("XBRLData/Summary/", "tse-", "-ixbrl.htm", 8):
        out.append(u"様式の種類を読む file 名の決め方が封 §0-1 の 3 と違う")
    if tuple(st.KEY_PATTERNS) != tuple(TS.GEN.KEY_PATTERNS) or st.LONG_ALNUM.pattern != TS.GEN.LONG_ALNUM.pattern:
        out.append(u"鍵らしい字の検査が手本(2026-11-09 の便)と違う")
    if ms.HEAD_RE.pattern not in seal or ms.END_RE.pattern not in seal:
        out.append(u"切り出しの正規表現が封の字と違う")
    if ms.HEADINGS != (u"経営成績等の概況", u"当中間決算に関する定性的情報", u"当四半期決算に関する定性的情報") or tuple(ms.TOC_MARKS) != (u"...", u"・・"):
        out.append(u"見出し・目次の印が封 §0-2 の 3 と違う")
    if ms.QUALITATIVE != "XBRLData/Attachment/qualitative.htm":
        out.append(u"qualitative.htm の path が封 §0-2 の 3 と違う")
    if (ms.ATTACH_PREFIX, ms.OLD_SUFFIX, ms.NEW_SUFFIX, ms.PUBLIC_DOC, ms.OVERVIEW_MEMBER) != (
            "XBRLData/Attachment/", "-ixbrl.htm", "_ixbrl.htm", "XBRL/PublicDoc/", "XBRL/PublicDoc/zz_overview_ixbrl.htm"):
        out.append(u"包み直しの名前が封 §0-2 の 4 と違う")
    if ms.TEXTBLOCK_NAME not in seal or ms.TEXTBLOCK_NAME != "jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock" or u'contextRef="FilingDateInstant" escape="true"' not in ms.OVERVIEW_HEAD:
        out.append(u"文の要素の名前・属性が封 §0-2 の 4 と違う")
    if ms.PROFILE != "P33E":
        out.append(u"profile が P33E でない")
    if (ms.SAMPLE_SEED, ms.SAMPLE_N) != (20261114, 120):
        out.append(u"標本の種・本数が封 §0-2 の 7 と違う")
    if (ms.A_GROUPS, ms.B_GROUPS) != ((u"甲", u"乙"), (u"丙",)):
        out.append(u"A・B の群が封 §0-1 の 2 と違う")
    if ms.WHYS != (u"member なし", u"decode", u"始まりなし", u"終わりなし") or (ms.CUT_OK, ms.CUT_NG) != (u"切れた", u"切れない"):
        out.append(u"切れない理由の字が封 §0-2 の 3 と違う")
    if list(ms.TYPES) != list(u"アイウエオカキクケ"):
        out.append(u"型が (ア)〜(ケ) の 9 つでない")
    for k, v in ms.TYPES.items():
        if u"(%s) %s" % (k, v) not in seal.replace(u"**", u""):
            out.append(u"型 (%s) の字が封 §0-2 の 7 と違う" % k)
    if u"AI の席" not in ms.TYPED_BY or u"人は読んでいない" not in ms.TYPED_BY:
        out.append(u"型を付けた席の字が封 §0-2 の 7 と違う")
    return out


# ---------------------------------------------------------------- 3. engine 0 行
def engine_since_seal_problems(root=REPO, seal_rel=SEAL_REL, prefix=PREFIX, rels=NOT_TOUCHED_RELS):
    u"""封の commit から HEAD までに rels を触った commit を列挙する(宣言された遷移は無い。1 つでも在れば問題)。"""
    seal_commits = PR.added_commits(root, prefix + seal_rel)
    if len(seal_commits) != 1:
        return [u"封の commit が履歴に 1 つに決まらない"]
    rc, log = PR.git_in(root, "log", "--format=%H", "%s..HEAD" % seal_commits[0], "--", *[prefix + r for r in rels])
    if rc != 0:
        return [u"git log が失敗した"]
    return [u"封の後に engine・lib・仕掛け・読み込む前の便を触った commit %s" % c[:7] for c in log.split() if c]


# ---------------------------------------------------------------- 4. 順序
def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(SCRIPT_RELS + (GATE_REL,)) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 7. 配線・名前・docID・通信
#: 前の便・置く script の関数(測る script は同名の関数を定義せず、module の関数を呼ぶ)。(module の別名, 関数名)
REUSED_FUNCS = (("TS", "html_to_lines"), ("TS", "profile_rows"), ("TS", "row_entry"), ("TS", "state_counts"), ("TS", "reason_counts"), ("TS", "vm_breakdown"), ("TS", "dumps_states"),
                ("TS.NF", "map_pool"), ("TS.RUN", "sentence_list"), ("TS.R", "build_raw_claims"), ("ST", "read_population"), ("ST", "validate_population"), ("ST", "write_text_exclusive"),
                ("ST", "dumps_record"), ("ST", "key_leaks"), ("ST", "sha256_file"), ("ST", "names_snapshot"), ("ST", "git_head"))


def defined_functions(path):
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    return set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))


def resolve(ms, dotted):
    obj = ms
    for part in dotted.split("."):
        obj = getattr(obj, part, None)
    return obj


def reuse_problems(ms=None, src_path=None):
    u"""測る script が前の便・置く script の関数を呼ぶ(同名の関数を定義しない)。"""
    ms = ms or MS
    path = src_path or os.path.join(ROOT, SCRIPT_REL)
    defs = defined_functions(path)
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    out = []
    for alias, fn in REUSED_FUNCS:
        if fn in defs:
            out.append(u"%s.%s と同名の関数を script が定義している(呼ぶ)" % (alias, fn))
        if not callable(getattr(resolve(ms, alias), fn, None)):
            out.append(u"%s.%s が module に無い" % (alias, fn))
        if not re.search(r"\b%s\.%s\b" % (re.escape(alias), fn), body):
            out.append(u"script が %s.%s を呼んでいない" % (alias, fn))
    return out


def network_problems(path=None):
    u"""置く script が通信の module を import しない(``import`` 文を ast で見る)。"""
    path = path or os.path.join(ROOT, STAGE_REL)
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    out = []
    for n in ast.walk(tree):
        names = [a.name for a in n.names] if isinstance(n, ast.Import) else ([n.module or u""] if isinstance(n, ast.ImportFrom) else [])
        for nm in names:
            if nm.split(".")[0] in NETWORK_MODULES:
                out.append(u"通信の module を import している: %s" % nm)
    return out


def reserved_problems(rels=(GATE_REL,), base=ROOT):
    out = []
    for rel in rels:
        with open(os.path.join(base, rel), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for n, line in enumerate(lines, 1):
            if any(re.match(r"%s\w*\s*=" % re.escape(p), line) for p in RESERVED_PREFIXES):
                out.append(u"%s:%d が既存の門の数える名前を行頭に置いている" % (rel, n))
    return out


def name_problems(rels=SCRIPT_RELS + (GATE_REL,), base=ROOT, codes=None):
    u"""新しい file に docID・TDnet の番号・2026-11-09 の便の証券コード・番号が無い。"""
    codes = codes if codes is not None else [r[1] for r in TS.FE.TABLE] + [r[2] for r in TS.FE.TABLE]
    out = []
    for rel in rels:
        p = os.path.join(base, rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            src = fh.read()
        if DOCID_RE.search(src):
            out.append(u"%s に docID の字がある" % rel)
        if TDNET_RE.search(src):
            out.append(u"%s に TDnet の番号の字がある" % rel)
        if any(c in src for c in codes):
            out.append(u"%s に既知の証券コード・番号の字がある" % rel)
    return out


# ================================================================ 振る舞いの検査(``*_problems`` は問題の字の列を返す。変異した版でも呼べるよう、module の名前で引く)
IX = u'''<html><body>
<xbrli:context id="CurrentYearDuration"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:startDate>2025-04-01</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period></xbrli:context>
<xbrli:context id="Prior1YearDuration"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:startDate>2024-04-01</xbrli:startDate><xbrli:endDate>2025-03-31</xbrli:endDate></xbrli:period></xbrli:context>
<ix:nonFraction name="jppfs_cor:NetSales" contextRef="CurrentYearDuration" unitRef="JPY" decimals="-6" scale="6">1,234</ix:nonFraction>
<ix:nonFraction name="jppfs_cor:NetSales" contextRef="Prior1YearDuration" unitRef="JPY" decimals="-6" scale="6">1,000</ix:nonFraction>
</body></html>'''
Q_BODY = u"<p>1.経営成績等の概況</p><p>売上高は1,234百万円となりました。</p>%s<p>2.次の節</p><p>売上高は9百万円です。</p>"


def make_zip(members):
    u"""[(名前, bytes)] から ZIP の bytes(作り物。材料ではない)。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in members:
            z.writestr(n, b)
    return buf.getvalue()


def tanshin_zip(kind=u"acedjpsm", extra_sentence=u"", with_q=True, q_body=None, tag=b""):
    body = q_body if q_body is not None else Q_BODY % extra_sentence
    m = []
    if with_q:
        m.append(("XBRLData/Attachment/qualitative.htm", body.encode("utf-8")))
    m.append(("XBRLData/Attachment/0200000-ixbrl.htm", IX.encode("utf-8")))
    m.append(("XBRLData/Summary/tse-%s-00001-ixbrl.htm" % kind, b"summary" + tag))
    return make_zip(m)


def eqp(out, label, got, want):
    if got != want:
        out.append(u"%s: 期待と違う" % label)


def cut_problems():
    u"""切り出し(封 §0-2 の 3)の当たる例・当たらない例・目次・最後の見出し・終わり・NFKC・member なし・decode。"""
    out = []
    L = MS.cut_lines
    eqp(out, u"基本", L([u"1.経営成績等の概況", u"a", u"2.会計基準"]), (u"1.経営成績等の概況\na", 0, None))
    eqp(out, u"中間", L([u"1. 当中間決算に関する定性的情報", u"a", u"2. 次"]), (u"1. 当中間決算に関する定性的情報\na", 1, None))
    eqp(out, u"四半期", L([u"1.当四半期決算に関する定性的情報", u"a", u"2.次"]), (u"1.当四半期決算に関する定性的情報\na", 2, None))
    for bad in (u"1.経営成績・財政状態の概況", u"1.当中間期決算に関する定性的情報", u"(1)経営成績に関する説明", u"1.経営成績等の概況 ......... 2", u"1.経営成績等の概況 ・・・ 2"):
        eqp(out, u"当たらない例 %s" % bad, L([bad, u"a", u"2.次"]), (None, None, MS.WHY_START))
    eqp(out, u"目次の行は始まりにならない", L([u"1.経営成績等の概況 ... 2", u"2.次 ... 9", u"1.経営成績等の概況", u"本文", u"2.次"]), (u"1.経営成績等の概況\n本文", 0, None))
    eqp(out, u"最後の見出しが勝つ", L([u"1.経営成績等の概況", u"a", u"1.当中間決算に関する定性的情報", u"b", u"2.次"]), (u"1.当中間決算に関する定性的情報\nb", 1, None))
    eqp(out, u"2.5% は終わりでない", L([u"1.経営成績等の概況", u"売上", u"2.5%増加しました", u"2.次"]), (u"1.経営成績等の概況\n売上\n2.5%増加しました", 0, None))
    eqp(out, u"終わりは最初の 2.", L([u"1.経営成績等の概況", u"a", u"2 . 次", u"b", u"2.さらに次"]), (u"1.経営成績等の概況\na", 0, None))
    eqp(out, u"2. だけの行は終わりでない", L([u"1.経営成績等の概況", u"a", u"2."]), (None, None, MS.WHY_END))
    eqp(out, u"始まりより前の 2. は終わりでない", L([u"2.前", u"1.経営成績等の概況", u"a", u"2.次"]), (u"1.経営成績等の概況\na", 0, None))
    eqp(out, u"終わりなし", L([u"1.経営成績等の概況", u"a"]), (None, None, MS.WHY_END))
    eqp(out, u"始まりなし", L([u"a", u"2.次"]), (None, None, MS.WHY_START))
    H = MS.cut_html
    eqp(out, u"NFKC", H(u"<p>１．経営成績等の概況</p><p>売上高は１，２３４百万円(前期比＋５．６％増)でした。（注）</p><p>２．次</p>"), (u"1.経営成績等の概況\n売上高は1,234百万円(前期比+5.6%増)でした。(注)", 0, None))
    eqp(out, u"NFKC で 目次の …… が ... になり始まりにならない", H(u"<p>１．経営成績等の概況……２</p><p>x</p><p>１．経営成績等の概況</p><p>本文</p><p>２．次</p>"), (u"1.経営成績等の概況\n本文", 0, None))
    eqp(out, u"前後の空白", H(u"<p>  １．経営成績等の概況  </p><p>　本文　</p><p>２．次</p>"), (u"1.経営成績等の概況\n本文", 0, None))
    eqp(out, u"li で行が切れる", H(u"<p>1.経営成績等の概況</p><ul><li>A</li><li>B</li></ul><p>2.次</p>"), (u"1.経営成績等の概況\nA\nB", 0, None))
    calls = []
    real = MS.TS.html_to_lines

    def spy(h):
        calls.append(h)
        return [u"1.経営成績等の概況", u" ", u" ", u"a", u"2.次"]
    with patched(MS.TS, html_to_lines=spy):
        got = H(u"<p>x</p>")
    eqp(out, u"html_to_lines を呼ぶ・空の行を捨てる", (got, calls), ((u"1.経営成績等の概況\na", 0, None), [u"<p>x</p>"]))
    if MS.TS.html_to_lines is not real:
        out.append(u"html_to_lines が戻っていない")
    good = tanshin_zip()
    eqp(out, u"zip の切り出し", MS.cut(good), (u"1.経営成績等の概況\n売上高は1,234百万円となりました。", 0, None))
    for label, members in ((u"member が .bak", [("XBRLData/Attachment/qualitative.htm.bak", Q_BODY.encode("utf-8"))]),
                           (u"member が深い所", [("x/XBRLData/Attachment/qualitative.htm", Q_BODY.encode("utf-8"))]),
                           (u"member が無い", [("XBRLData/Attachment/other.htm", b"x")])):
        eqp(out, u"member なし(%s)" % label, MS.cut(make_zip(members)), (None, None, MS.WHY_MEMBER))
    eqp(out, u"decode", MS.cut(make_zip([(MS.QUALITATIVE, b"\xff\xfe<p>1.</p>")])), (None, None, MS.WHY_DECODE))
    eqp(out, u"始まりなし(zip)", MS.cut(tanshin_zip(q_body=u"<p>無関係</p>")), (None, None, MS.WHY_START))
    eqp(out, u"終わりなし(zip)", MS.cut(tanshin_zip(q_body=u"<p>1.経営成績等の概況</p><p>a</p>")), (None, None, MS.WHY_END))
    try:
        MS.cut(b"not a zip")
        out.append(u"ZIP でない bytes で止まらない")
    except SystemExit:
        pass
    return out


def wrap_problems():
    u"""包み直し(封 §0-2 の 4): 名前の替え方・順・中身が byte で同じ・サマリーを入れない・文の block・load_instance が読める。"""
    out = []
    members = [("XBRLData/Attachment/sub/z-ixbrl.htm", b"Z"), ("XBRLData/Attachment/b-ixbrl.htm", b"B"), ("XBRLData/Attachment/a-ixbrl.htm", IX.encode("utf-8")),
               ("XBRLData/Attachment/qualitative.htm", b"Q"), ("XBRLData/Summary/tse-acedjpsm-1-ixbrl.htm", b"S"), ("XBRLData/Attachment/c-ixbrl.html", b"C"),
               ("XBRLData/Attachment/d.htm", b"D"), ("XBRLData/Other/e-ixbrl.htm", b"E"), ("a-ixbrl.htm", b"F")]
    zb = make_zip(members)
    text = u"1.経営成績等の概況\n売上高は1,234百万円となりました。<&>"
    wrapped, n = MS.wrap(zb, text)
    z = zipfile.ZipFile(io.BytesIO(wrapped))
    want = ["XBRL/PublicDoc/a_ixbrl.htm", "XBRL/PublicDoc/b_ixbrl.htm", "XBRL/PublicDoc/z_ixbrl.htm", "XBRL/PublicDoc/zz_overview_ixbrl.htm"]
    eqp(out, u"名前と順(文は最後)", (z.namelist(), n), (want, 3))
    if z.namelist() == want:
        eqp(out, u"中身が byte で同じ", [z.read(w) for w in want[:3]], [IX.encode("utf-8"), b"B", b"Z"])
        expect_html = (u'<html><body><ix:nonNumeric name="jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock" contextRef="FilingDateInstant" escape="true">'
                       + u"<p>1.経営成績等の概況</p>\n<p>売上高は1,234百万円となりました。&lt;&amp;&gt;</p>" + u"</ix:nonNumeric></body></html>").encode("utf-8")
        eqp(out, u"文の block の字", z.read(want[3]), expect_html)
        eqp(out, u"member の日時・圧縮が固定", sorted(set((i.date_time, i.compress_type) for i in z.infolist())), [((1980, 1, 1, 0, 0, 0), zipfile.ZIP_DEFLATED)])
    eqp(out, u"同じ入力は同じ名前と中身", (zipfile.ZipFile(io.BytesIO(MS.wrap(zb, text)[0])).namelist(), MS.wrap(zb, text)[1]), (want, 3))
    inst = I.load_instance(wrapped)
    eqp(out, u"load_instance が fact を読む", len(inst["facts"]), 2)
    eqp(out, u"load_instance が文を読む", I.select_mdna(inst["textblocks"]), MS.TEXTBLOCK_NAME)
    if I.select_mdna(inst["textblocks"]) == MS.TEXTBLOCK_NAME and u"売上高は1,234百万円となりました。" not in I.strip_html(inst["textblocks"][MS.TEXTBLOCK_NAME]):
        out.append(u"load_instance が文の字を読めない")
    dup = make_zip([("XBRLData/Attachment/a-ixbrl.htm", b"1"), ("XBRLData/Attachment/sub/a-ixbrl.htm", b"2")])
    try:
        MS.wrap(dup, u"x")
        out.append(u"名前が重なっても止まらない")
    except SystemExit:
        pass
    return out


def judge_problems():
    u"""判定の配線: ``judge_book`` の記録の形・``profile_rows`` を P33E・text なし・同じ ZIP で呼ぶ・切れない本は行を持たない。"""
    out = []
    sha = u"a" * 64
    b = MS.judge_book(1, u"甲", u"acedjpsm", sha, tanshin_zip(extra_sentence=u"<p>売上高は1,300百万円となりました。</p>"))
    want_rows = [[1, 4, u"GROUNDED", None, u"CurrentYear", False, u"円族", False, False], [2, 4, u"VALUE_MISMATCH", None, u"CurrentYear", False, u"円族", False, False]]
    eqp(out, u"切れた本の記録", json.loads(json.dumps(b)), json.loads(json.dumps(collections.OrderedDict([
        (u"#", 1), (u"群", u"甲"), (u"様式の種類", u"acedjpsm"), (u"ZIP の sha256", sha), (u"切り出し", u"切れた"), (u"理由", None), (u"見出しの番号", 0),
        (u"字数", len(u"1.経営成績等の概況\n売上高は1,234百万円となりました。\n売上高は1,300百万円となりました。")), (u"入れた iXBRL の file の数", 1), (u"fact の数", 2),
        (u"claim", 2), (u"対応", True), (u"行", want_rows)]))))
    eqp(out, u"欄の順", list(b), [u"#", u"群", u"様式の種類", u"ZIP の sha256", u"切り出し", u"理由", u"見出しの番号", u"字数", u"入れた iXBRL の file の数", u"fact の数", u"claim", u"対応", u"行"])
    c = MS.judge_book(2, u"丙", u"scedjpsy", sha, tanshin_zip(with_q=False))
    eqp(out, u"切れない本の記録", json.loads(json.dumps(c)), json.loads(json.dumps(collections.OrderedDict([
        (u"#", 2), (u"群", u"丙"), (u"様式の種類", u"scedjpsy"), (u"ZIP の sha256", sha), (u"切り出し", u"切れない"), (u"理由", u"member なし"), (u"見出しの番号", None),
        (u"字数", None), (u"入れた iXBRL の file の数", None), (u"fact の数", None), (u"claim", 0), (u"対応", None), (u"行", [])]))))
    h1 = MS.judge_book(3, u"丙", u"scedjpsy", sha, tanshin_zip(q_body=u"<p>1.当中間決算に関する定性的情報</p><p>売上高は1,234百万円となりました。</p><p>2.次</p>"))
    h2 = MS.judge_book(4, u"丙", u"scedjpsy", sha, tanshin_zip(q_body=u"<p>1.当四半期決算に関する定性的情報</p><p>売上高は1,234百万円となりました。</p><p>2.次</p>"))
    eqp(out, u"見出しの番号", (h1[u"見出しの番号"], h2[u"見出しの番号"], b[u"見出しの番号"]), (1, 2, 0))
    seen = []
    real = MS.TS.profile_rows

    def spy(zb, text, zm, pname):
        seen.append((zb is zm, text, pname, zipfile.ZipFile(io.BytesIO(zb)).namelist()[-1]))
        return real(zb, text, zm, pname)
    with patched(MS.TS, profile_rows=spy):
        MS.judge_book(1, u"甲", u"acedjpsm", sha, tanshin_zip())
    eqp(out, u"profile_rows に 包んだ ZIP・text なし・P33E", seen, [(True, None, u"P33E", u"XBRL/PublicDoc/zz_overview_ixbrl.htm")])
    return out


# ---------------------------------------------------------------- 置く script の振る舞い
SHAPE3 = (3, collections.OrderedDict([(u"甲", 1), (u"乙", 1), (u"丙", 1)]))


def stage_fixture(d):
    u"""d の下に 作り物の ZIP 3 本(+ 表に無い 1 本・zip でない file)・src・cache の根(folder 2 つ。1 つは開かない名前)・root を作る。(表, src folder, base, root, ZIP の bytes の列)。"""
    zips = [tanshin_zip(u"acedjpsm", tag=b"1"), tanshin_zip(u"acedifsm", tag=b"2"), tanshin_zip(u"scedjpsy", tag=b"3")]
    kinds = [u"acedjpsm", u"acedifsm", u"scedjpsy"]
    pop = [(i + 1, g, k, hashlib.sha256(z).hexdigest()) for i, (g, k, z) in enumerate(zip([u"甲", u"乙", u"丙"], kinds, zips))]
    src = os.path.join(d, "src")
    os.makedirs(os.path.join(src, "x", "y"))
    os.makedirs(os.path.join(src, "z"))
    for name, z in zip(("one.zip", "x/two.zip", "x/y/three.zip"), zips):
        with open(os.path.join(src, name), "wb") as fh:
            fh.write(z)
    with open(os.path.join(src, "z", "extra.zip"), "wb") as fh:
        fh.write(tanshin_zip(u"acedjpsm", tag=b"not in the table"))
    with open(os.path.join(src, "z", "note.txt"), "wb") as fh:
        fh.write(zips[0])
    base = os.path.join(d, "base")
    os.makedirs(os.path.join(base, "edinet"))
    os.makedirs(os.path.join(base, ST.SKIP_CACHES[0]))
    for n in ("a.zip", "b.zip"):
        with open(os.path.join(base, "edinet", n), "wb") as fh:
            fh.write(b"x")
    with open(os.path.join(base, ST.SKIP_CACHES[0], "k.zip"), "wb") as fh:
        fh.write(b"x")
    root = os.path.join(d, "root")
    os.makedirs(root)
    return pop, src, base, root, zips


def tree_listing(folder):
    out = []
    for dp, dn, fn in os.walk(folder):
        for f in fn:
            p = os.path.join(dp, f)
            out.append((os.path.relpath(p, folder), os.stat(p).st_size, os.stat(p).st_mtime_ns))
    return sorted(out)


def expect_stop(out, label, fn):
    try:
        fn()
    except SystemExit:
        return
    out.append(u"%s: 止まらない" % label)


def stage_problems():
    u"""置く script の run_stage: 良い走り・400 本そろわない・既存 file の sha256 違い・様式の種類違い・本番の記録・ほかの cache・鍵らしい字・置き先の位置。
    (試験の置き場は長い英数字の path なので、本番の置き場の表示 ``~/…`` の代わりに短い字にする。長い path は鍵らしい字として止まる)"""
    with patched(ST, display_path=lambda p: u"(試験の置き場)"):
        return _stage_problems()


def _stage_problems():
    out = []
    with tmpdir() as d:
        pop, src, base, root, zips = stage_fixture(d)
        kw = dict(root=root, population=pop, shape=SHAPE3, cache_base_dir=base, say=lambda *a: None)
        before_base = tree_listing(base)
        rec_path = os.path.join(d, "rec", "p1.json")
        rec = ST.run_stage(srcs=[src], out=os.path.join(d, "out1"), record=rec_path, **kw)
        eqp(out, u"置いた ZIP の名前と中身", sorted(os.listdir(os.path.join(d, "out1"))), sorted(r[3] + ".zip" for r in pop))
        if all(os.path.exists(os.path.join(d, "out1", r[3] + ".zip")) for r in pop):
            eqp(out, u"置いた ZIP の中身が同じ", [open(os.path.join(d, "out1", r[3] + ".zip"), "rb").read() for r in pop], zips)
        eqp(out, u"記録の行", json.loads(json.dumps(rec[u"行"])), [[r[0], r[1], r[2], r[3], len(z)] for r, z in zip(pop, zips)])
        on_disk = open(rec_path, encoding="utf-8").read()
        eqp(out, u"記録の file と返り値", json.loads(on_disk), json.loads(json.dumps(rec)))
        eqp(out, u"ほかの cache は触らない", tree_listing(base), before_base)
        eqp(out, u"ほかの cache の前後(開かない folder は数えない)", (rec[u"ほかの cache の前後"][u"変化なし"], rec[u"ほかの cache の前後"][u"比べた folder の数"]), (True, 1))
        eqp(out, u"記録に元の path・材料の字が無い", [d in on_disk, u"extra" in on_disk, u"証券コード" in on_disk, u"one.zip" in on_disk], [False, False, False, False])
        eqp(out, u"件数", (rec[u"表と一致した ZIP"], rec[u"新しく置いた ZIP"], rec[u"在って触らなかった ZIP(sha256 が同じ)"]), (3, 3, 0))
        # 2 回目: 在る file は触らない
        listing = tree_listing(os.path.join(d, "out1"))
        rec2 = ST.run_stage(srcs=[src], out=os.path.join(d, "out1"), record=os.path.join(d, "rec", "p2.json"), **kw)
        eqp(out, u"在る file は触らない", (tree_listing(os.path.join(d, "out1")), rec2[u"新しく置いた ZIP"], rec2[u"在って触らなかった ZIP(sha256 が同じ)"]), (listing, 0, 3))
        # 記録が在れば止まる(置く前に)
        expect_stop(out, u"記録が在る", lambda: ST.run_stage(srcs=[src], out=os.path.join(d, "outX"), record=rec_path, **kw))
        if os.path.exists(os.path.join(d, "outX")):
            out.append(u"記録が在るのに置き先を作った")
        # 3 本のうち 1 本が src に無い
        src2 = os.path.join(d, "src2")
        os.makedirs(src2)
        with open(os.path.join(src2, "one.zip"), "wb") as fh:
            fh.write(zips[0])
        expect_stop(out, u"そろわない", lambda: ST.run_stage(srcs=[src2], out=os.path.join(d, "out2"), record=os.path.join(d, "rec", "p3.json"), **kw))
        if os.path.exists(os.path.join(d, "out2")) or os.path.exists(os.path.join(d, "rec", "p3.json")):
            out.append(u"そろわないのに何かを書いた")
        # 置き先の既存 file の sha256 が名前と違う
        os.makedirs(os.path.join(d, "out4"))
        with open(os.path.join(d, "out4", pop[1][3] + ".zip"), "wb") as fh:
            fh.write(zips[1] + b"x")
        l4 = tree_listing(os.path.join(d, "out4"))
        expect_stop(out, u"既存 file の sha256 違い", lambda: ST.run_stage(srcs=[src], out=os.path.join(d, "out4"), record=os.path.join(d, "rec", "p4.json"), **kw))
        if tree_listing(os.path.join(d, "out4")) != l4 or os.path.exists(os.path.join(d, "rec", "p4.json")):
            out.append(u"既存 file の sha256 が違うのに何かを書いた")
        # 様式の種類が表と違う
        bad = [(pop[0][0], pop[0][1], u"acedifsm", pop[0][3])] + pop[1:]
        expect_stop(out, u"様式の種類違い", lambda: ST.run_stage(srcs=[src], out=os.path.join(d, "out5"), record=os.path.join(d, "rec", "p5.json"),
                                                             **dict(kw, population=bad)))
        if os.path.exists(os.path.join(d, "out5")):
            out.append(u"様式の種類が違うのに置き先を作った")
        # --out と --record の組み合わせ
        expect_stop(out, u"--out に --record が無い", lambda: ST.run_stage(srcs=[src], out=os.path.join(d, "out6"), record=None, **kw))
        expect_stop(out, u"--out と本番の記録の path", lambda: ST.run_stage(srcs=[src], out=os.path.join(d, "out6"), record=os.path.join(root, ST.POPULATION_REL), **kw))
        expect_stop(out, u"--out なしで本番でない記録", lambda: ST.run_stage(srcs=[src], out=None, record=os.path.join(d, "rec", "p6.json"), **kw))
        expect_stop(out, u"--src が無い", lambda: ST.run_stage(srcs=[], out=os.path.join(d, "out6"), record=os.path.join(d, "rec", "p6.json"), **kw))
        expect_stop(out, u"--src が folder でない", lambda: ST.run_stage(srcs=[os.path.join(d, "nothing")], out=os.path.join(d, "out6"), record=os.path.join(d, "rec", "p6.json"), **kw))
        # 置き先が既存の cache の中・根
        for bad_out in (os.path.join(base, "edinet", "sub"), base, os.path.join(base, "edinet")):
            expect_stop(out, u"置き先が既存の cache の中 %s" % os.path.basename(bad_out), lambda: ST.run_stage(srcs=[src], out=bad_out, record=os.path.join(d, "rec", "p7.json"), **kw))
        eqp(out, u"置き先違いで cache は変わらない", tree_listing(base), before_base)
        # 本番(--out なし): base/<CACHE_NAME> と root/<記録の path>
        ST.run_stage(srcs=[src], out=None, record=None, **kw)
        eqp(out, u"本番の置き場", sorted(os.listdir(os.path.join(base, ST.CACHE_NAME))), sorted(r[3] + ".zip" for r in pop))
        if not os.path.exists(os.path.join(root, ST.POPULATION_REL)):
            out.append(u"本番の記録が無い")
        expect_stop(out, u"本番の記録が在る", lambda: ST.run_stage(srcs=[src], out=None, record=None, **kw))
        eqp(out, u"本番でもほかの cache は触らない", tree_listing(base)[:len(before_base)], before_base)
        # ほかの cache の一覧が走っている間に変われば記録を書かずに止める
        snaps = []
        real = ST.others_snapshot

        def flip(base_=None, skip=ST.SKIP_CACHES, names=None):
            r = real(base_, skip, names)
            snaps.append(1)
            if len(snaps) >= 2 and r:
                r = [(r[0][0], r[0][1] + 1, r[0][2])] + list(r[1:])
            return r
        with patched(ST, others_snapshot=flip):
            expect_stop(out, u"ほかの cache が変わった", lambda: ST.run_stage(srcs=[src], out=os.path.join(d, "out8"), record=os.path.join(d, "rec", "p8.json"), **kw))
        if os.path.exists(os.path.join(d, "rec", "p8.json")):
            out.append(u"ほかの cache が変わったのに記録を書いた")
        # 鍵らしい字が記録に入るなら、ZIP を置く前に止まる
        with patched(ST, SEAL_COMMIT=u"a" * 40 + u"Z" * 8):
            expect_stop(out, u"鍵らしい字", lambda: ST.run_stage(srcs=[src], out=os.path.join(d, "out9"), record=os.path.join(d, "rec", "p9.json"), **kw))
        if os.path.exists(os.path.join(d, "out9")) or os.path.exists(os.path.join(d, "rec", "p9.json")):
            out.append(u"鍵らしい字が在るのに何かを書いた")
    return out


def population_problems():
    u"""母集団の検査: 行の数・番号・sha256 の重なり・群の本数が違えば止まる。良い表は通る。"""
    out = []
    good = [(1, u"甲", u"a", u"0" * 64), (2, u"乙", u"a", u"1" * 64), (3, u"丙", u"a", u"2" * 64)]
    V_ = ST.validate_population
    try:
        if V_(good, *SHAPE3) != good:
            out.append(u"良い表が通らない")
    except SystemExit:
        out.append(u"良い表で止まった")
    for label, rows in ((u"行が少ない", good[:2]), (u"行が多い", good + [(4, u"丙", u"a", u"3" * 64)]), (u"番号が飛ぶ", [good[0], (3, u"乙", u"a", u"1" * 64), (2, u"丙", u"a", u"2" * 64)]),
                        (u"sha256 の重なり", [good[0], good[1], (3, u"丙", u"a", u"1" * 64)]), (u"群の本数", [good[0], (2, u"甲", u"a", u"1" * 64), good[2]])):
        expect_stop(out, label, lambda rows=rows: V_(rows, *SHAPE3))
    expect_stop(out, u"行の数が n と違う(群の本数は合っている形)", lambda: V_(good, 4, SHAPE3[1]))
    return out


def scan_problems():
    out = []
    with tmpdir() as d:
        pop, src, base, root, zips = stage_fixture(d)
        got = ST.scan_sources([src], dict((r[3], r) for r in pop))
        eqp(out, u"表に在る ZIP だけ選ぶ", sorted(got), sorted(r[3] for r in pop))
        eqp(out, u"byte 数", [got[r[3]][1] for r in pop], [len(z) for z in zips])
    return out


def kinds_problems():
    out = []
    K = ST.summary_kinds
    eqp(out, u"様式の種類", K(make_zip([("XBRLData/Summary/tse-acedjpsm-1-ixbrl.htm", b"x")])), set([u"acedjpsm"]))
    eqp(out, u"2 種類", K(make_zip([("XBRLData/Summary/tse-acedjpsm-1-ixbrl.htm", b"x"), ("XBRLData/Summary/tse-scedjpsy-2-ixbrl.htm", b"x")])), set([u"acedjpsm", u"scedjpsy"]))
    eqp(out, u"Summary の外・tse- でない・-ixbrl.htm でない", K(make_zip([("XBRLData/Attachment/tse-acedjpsm-1-ixbrl.htm", b"x"), ("XBRLData/Summary/xtse-acedjpsm-1-ixbrl.htm", b"x"),
                                                                 ("XBRLData/Summary/tse-acedjpsm-1.htm", b"x")])), set())
    return out


def exclusive_problems():
    out = []
    with tmpdir() as d:
        p = os.path.join(d, "sub", "a.json")
        ST.write_text_exclusive(p, u"x")
        eqp(out, u"書く", open(p, encoding="utf-8").read(), u"x")
        expect_stop(out, u"在れば止まる", lambda: ST.write_text_exclusive(p, u"y"))
        eqp(out, u"在る file は変わらない", open(p, encoding="utf-8").read(), u"x")
    return out


# ---------------------------------------------------------------- states・標本・型
SHAPE4 = (5, collections.OrderedDict([(u"甲", 1), (u"乙", 1), (u"丙", 3)]))
VM_ONLY_Q = u"<p>1.経営成績等の概況</p><p>売上高は1,300百万円となりました。</p><p>2.次の節</p>"


def states_fixture(d):
    u"""作り物の材料 5 本(甲: GROUNDED と VALUE_MISMATCH・乙: VALUE_MISMATCH だけ・丙: member なし・丙: 始まりなし・丙: 切れるが数が無い)。(表, 材料の folder, root)。"""
    zips = [tanshin_zip(u"acedjpsm", extra_sentence=u"<p>売上高は1,300百万円となりました。</p>", tag=b"1"), tanshin_zip(u"acedifsm", q_body=VM_ONLY_Q, tag=b"2"),
            tanshin_zip(u"scedjpsy", with_q=False, tag=b"3"), tanshin_zip(u"scedjpsy", q_body=u"<p>無関係</p>", tag=b"4"),
            tanshin_zip(u"scedjpsy", q_body=u"<p>1.当中間決算に関する定性的情報</p><p>業績は堅調でした。</p><p>2.次の節</p>", tag=b"5")]
    kinds = [u"acedjpsm", u"acedifsm", u"scedjpsy", u"scedjpsy", u"scedjpsy"]
    pop = [(i + 1, g, k, hashlib.sha256(z).hexdigest()) for i, (g, k, z) in enumerate(zip([u"甲", u"乙", u"丙", u"丙", u"丙"], kinds, zips))]
    mat = os.path.join(d, "mat")
    os.makedirs(mat)
    for r, z in zip(pop, zips):
        with open(os.path.join(mat, r[3] + ".zip"), "wb") as fh:
            fh.write(z)
    root = os.path.join(d, "root")
    os.makedirs(root)
    return pop, mat, root


def strip_time(text):
    return re.sub(r'^ *"時間\(秒\)": .*$', u"", text, flags=re.M)


def recount(books):
    u"""集計を、記録の ``行`` から別の書き方で数え直す(script の ``block`` を使わない)。"""
    def one(bs):
        cut = [b for b in bs if b[u"切り出し"] == u"切れた"]
        rows = [r for b in cut for r in b[u"行"]]
        st = collections.Counter(r[2] for r in rows)
        return collections.OrderedDict([
            (u"本", len(bs)), (u"切れた", len(cut)), (u"切れない", len(bs) - len(cut)), (u"字数の合計", sum(b[u"字数"] for b in cut)), (u"claim", len(rows)),
            (u"4 state", [st.get(k, 0) for k in (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")]),
            (u"claim が 0", sum(1 for b in cut if not b[u"行"])), (u"GROUNDED が 0", sum(1 for b in cut if not any(r[2] == u"GROUNDED" for r in b[u"行"]))),
            (u"VALUE_MISMATCH が 1 以上", sum(1 for b in cut if any(r[2] == u"VALUE_MISMATCH" for r in b[u"行"]))),
            (u"切れない理由", sorted(collections.Counter(b[u"理由"] for b in bs if b[u"切り出し"] == u"切れない").items()))])
    return one(books)


def counted(block):
    return collections.OrderedDict([
        (u"本", block[u"本"]), (u"切れた", block[u"切れた"]), (u"切れない", block[u"切れない"]), (u"字数の合計", block[u"字数の合計"]), (u"claim", block[u"claim"]),
        (u"4 state", [block[u"4 state"][k] for k in (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")]),
        (u"claim が 0", block[u"切れた本のうち claim が 0 の本"]), (u"GROUNDED が 0", block[u"切れた本のうち GROUNDED が 0 の本"]),
        (u"VALUE_MISMATCH が 1 以上", block[u"VALUE_MISMATCH が 1 以上の本"]),
        (u"切れない理由", sorted((k, v) for k, v in block[u"切れない理由"].items() if v))])


def states_problems():
    u"""run_states: 記録の形・集計を行から数え直して一致・文を持たない・2 回(procs 違い)で byte が同じ(時間を除く)・止める所。"""
    out = []
    with tmpdir() as d:
        pop, mat, root = states_fixture(d)
        kw = dict(root=root, population=pop, shape=SHAPE4, material=mat, say=lambda *a: None)
        p1 = os.path.join(d, "o", "s1.json")
        ticks = iter([10.0, 13.5])
        rec = MS.run_states(procs=1, out=p1, clock=lambda: next(ticks), **kw)
        text = open(p1, encoding="utf-8").read()
        eqp(out, u"返り値と file", json.loads(text), json.loads(json.dumps(rec)))
        books = rec[u"本"]
        eqp(out, u"本の順と切り出し", [(b[u"#"], b[u"群"], b[u"切り出し"], b[u"理由"]) for b in books],
            [(1, u"甲", u"切れた", None), (2, u"乙", u"切れた", None), (3, u"丙", u"切れない", u"member なし"), (4, u"丙", u"切れない", u"始まりなし"), (5, u"丙", u"切れた", None)])
        eqp(out, u"行", [b[u"行"] for b in books[:2]] + [books[4][u"行"], books[4][u"見出しの番号"]], [[[1, 4, u"GROUNDED", None, u"CurrentYear", False, u"円族", False, False], [2, 4, u"VALUE_MISMATCH", None, u"CurrentYear", False, u"円族", False, False]],
                                                     [[1, 4, u"VALUE_MISMATCH", None, u"CurrentYear", False, u"円族", False, False]], [], 1])
        eqp(out, u"時間は 1 つの欄", (rec[u"時間(秒)"], len(re.findall(u"時間", text))), (3.5, 1))
        eqp(out, u"行の欄と行の長さ", (len(rec[u"行の欄"]), set(len(r) for b in books for r in b[u"行"])), (9, set([9])))
        t = rec[u"集計"]
        eqp(out, u"A の集計を行から数え直す", counted(t[u"A(甲 + 乙)"]), recount([b for b in books if b[u"群"] in (u"甲", u"乙")]))
        eqp(out, u"B の集計を行から数え直す", counted(t[u"B(丙)"]), recount([b for b in books if b[u"群"] == u"丙"]))
        eqp(out, u"群ごとの集計", [counted(t[u"群"][g]) for g in (u"甲", u"乙", u"丙")], [recount([b for b in books if b[u"群"] == g]) for g in (u"甲", u"乙", u"丙")])
        eqp(out, u"様式ごとの集計", [counted(t[u"様式の種類"][k]) for k in sorted(t[u"様式の種類"])], [recount([b for b in books if b[u"様式の種類"] == k]) for k in sorted(t[u"様式の種類"])])
        a = t[u"A(甲 + 乙)"]
        eqp(out, u"A の数(独立に数えた値)", (a[u"claim"], dict(a[u"4 state"]), a[u"切れた本のうち GROUNDED が 0 の本"], a[u"VALUE_MISMATCH が 1 以上の本"], a[u"VALUE_MISMATCH の内訳"][u"行"]),
            (3, {u"GROUNDED": 1, u"VALUE_MISMATCH": 2, u"UNVERIFIABLE": 0, u"POINTER_NOT_FOUND": 0}, 1, 2, 2))
        bb = t[u"B(丙)"]
        eqp(out, u"B の数(独立に数えた値)", (bb[u"本"], bb[u"切れた"], bb[u"切れない"], dict(bb[u"切れない理由"]), bb[u"claim"], bb[u"切れた本のうち claim が 0 の本"], bb[u"切れた本のうち GROUNDED が 0 の本"],
                                  dict(bb[u"見出しの番号の本数"])),
            (3, 1, 2, {u"member なし": 1, u"decode": 0, u"始まりなし": 1, u"終わりなし": 0}, 0, 1, 1, {u"0": 0, u"1": 1, u"2": 0}))
        eqp(out, u"記録に文・span・値の字が無い", [x in text for x in (u"売上高", u"百万円", u'"span"', u'"value"', u"extra")], [False] * 5)
        eqp(out, u"材料の置き場の前後", (rec[u"材料"][u"置き場の一覧の前後"][u"変化なし"], rec[u"材料"][u"表と一致した ZIP"]), (True, 5))
        p2 = os.path.join(d, "o", "s2.json")
        MS.run_states(procs=2, out=p2, clock=lambda: 99.0, **kw)
        eqp(out, u"2 回(procs 違い)で byte が同じ(時間を除く)", strip_time(open(p2, encoding="utf-8").read()), strip_time(text))
        # 止める所(何も書かない)
        expect_stop(out, u"出力が在る", lambda: MS.run_states(out=p1, **kw))
        eqp(out, u"在る出力は変わらない", open(p1, encoding="utf-8").read(), text)
        expect_stop(out, u"--out が無い", lambda: MS.run_states(out=None, **kw))
        expect_stop(out, u"本番の記録を使い捨ての材料から作る", lambda: MS.run_states(out=os.path.join(root, MS.STATES_REL), **kw))
        if os.path.exists(os.path.join(root, MS.STATES_REL)):
            out.append(u"本番の記録の path に書いた")
        with open(os.path.join(mat, pop[3][3] + ".zip"), "ab") as fh:
            fh.write(b"x")
        expect_stop(out, u"材料の sha256 が違う", lambda: MS.run_states(out=os.path.join(d, "o", "s3.json"), **kw))
        os.remove(os.path.join(mat, pop[2][3] + ".zip"))
        expect_stop(out, u"材料が無い", lambda: MS.run_states(out=os.path.join(d, "o", "s4.json"), **kw))
        if os.path.exists(os.path.join(d, "o", "s3.json")) or os.path.exists(os.path.join(d, "o", "s4.json")):
            out.append(u"止まったのに記録を書いた")
    with tmpdir() as d:
        pop, mat, root = states_fixture(d)
        kw = dict(root=root, population=pop, shape=SHAPE4, material=mat, say=lambda *a: None)
        snaps = iter([(4, u"a"), (4, u"b")])
        with patched(ST, names_snapshot=lambda folder: next(snaps)):
            expect_stop(out, u"材料の置き場が変わった", lambda: MS.run_states(out=os.path.join(d, "o", "s5.json"), **kw))
        if os.path.exists(os.path.join(d, "o", "s5.json")):
            out.append(u"材料の置き場が変わったのに記録を書いた")
        expect_stop(out, u"表の形が違う", lambda: MS.run_states(out=os.path.join(d, "o", "s6.json"), **dict(kw, shape=(3, SHAPE3[1]))))
    return out


def sample_problems():
    u"""標本: 行の並べ方・引き方(種 20261114・120 行)・120 に満たなければ全部。"""
    out = []
    for n in (1898, 500):
        want = sorted(random.Random(20261114).sample(list(range(n)), 120))
        eqp(out, u"引き方 %d" % n, MS.pick_sample(n), want)
    p = MS.pick_sample(1898)
    eqp(out, u"pin 1898", (p[:5], p[-3:], sum(p), len(set(p))), ([50, 54, 124, 131, 151], [1856, 1879, 1893], 116940, 120))
    p = MS.pick_sample(500)
    eqp(out, u"pin 500", (p[:5], p[-3:], sum(p)), ([12, 13, 31, 32, 37], [488, 493, 495], 30786))
    eqp(out, u"120 に満たなければ全部", (MS.pick_sample(0), MS.pick_sample(7), MS.pick_sample(119), MS.pick_sample(120)), ([], list(range(7)), list(range(119)), list(range(120))))
    eqp(out, u"121 は引く", MS.pick_sample(121)[:5] + [len(MS.pick_sample(121))], [0, 1, 2, 3, 4, 120])
    # 行の並べ方: A だけ・VALUE_MISMATCH だけ・# の順・文の番号の順・位置の順
    def book(n, g, rows):
        return {u"#": n, u"群": g, u"行": [[r[0], r[1], r[2], None, u"CurrentYear", False, u"円族", False, False] for r in rows]}
    states = {u"本": [book(3, u"乙", [(5, 2, u"VALUE_MISMATCH"), (2, 9, u"VALUE_MISMATCH"), (2, 1, u"VALUE_MISMATCH"), (2, 4, u"GROUNDED")]),
                      book(1, u"甲", [(9, 1, u"VALUE_MISMATCH"), (0, 0, u"POINTER_NOT_FOUND")]), book(2, u"丙", [(0, 0, u"VALUE_MISMATCH")])]}
    eqp(out, u"行の並べ方", MS.vm_rows_a(states), [(1, 9, 1), (3, 2, 1), (3, 2, 9), (3, 5, 2)])
    eqp(out, u"標本の番号", MS.sample_items(states), [(1, 1, 9, 1), (2, 3, 2, 1), (3, 3, 2, 9), (4, 3, 5, 2)])
    return out


def repo_problems():
    u"""読むための紙を repo の中に書かせない: repo の中・別の git の木の中は真、外は偽。"""
    out = []
    eqp(out, u"repo の中(まだ無い file)", MS.inside_repo(os.path.join(ROOT, "x", "new_sheet.txt")), True)
    eqp(out, u"repo の根", MS.inside_repo(REPO), True)
    with tmpdir() as d:
        eqp(out, u"repo の外", MS.inside_repo(os.path.join(d, "a", "sheet.txt")), False)
        r = PR.Repo()
        r.put("x.txt")
        r.commit("x.txt")
        eqp(out, u"別の git の木の中(まだ無い folder)", MS.inside_repo(os.path.join(r.d, "new", "sheet.txt")), True)
    return out


def sheet_problems():
    u"""run_sample: 標本の行の文・span・値・結んだ先を紙に書く(標準出力は件数だけ)・repo の中は断る・在れば止める・記録と合わなければ止める。"""
    out = []
    with tmpdir() as d:
        pop, mat, root = states_fixture(d)
        sp = os.path.join(d, "o", "s.json")
        MS.run_states(root=root, population=pop, shape=SHAPE4, material=mat, out=sp, say=lambda *a: None)
        said = []
        sheet = os.path.join(d, "paper", "sheet.txt")
        items = MS.run_sample(sp, mat, sheet, root=root, say=said.append, population=pop)
        eqp(out, u"標本", items, [(1, 1, 2, 4), (2, 2, 1, 4)])
        text = open(sheet, encoding="utf-8").read()
        eqp(out, u"紙に文と読んだ値と結んだ先", [x in text for x in (u"=== 標本 1 / 本 # 1 / 文 2 / 位置 4 ===", u"=== 標本 2 / 本 # 2 / 文 1 / 位置 4 ===", u"文: 売上高は1,300百万円となりました。",
                                                          u"span: ", u"読んだ値: 1300", u"state: VALUE_MISMATCH", u"結んだ先: xbrl:jppfs_cor:NetSales@CurrentYearDuration", u"その値: 1234")], [True] * 8)
        eqp(out, u"標準出力は件数だけ", [u"売上高" in x or u"百万円" in x for x in said] + [bool(said)], [False] * len(said) + [True])
        expect_stop(out, u"紙が在る", lambda: MS.run_sample(sp, mat, sheet, root=root, say=lambda *a: None, population=pop))
        inside = os.path.join(ROOT, "zz_sheet_must_not_exist.txt")
        expect_stop(out, u"repo の中", lambda: MS.run_sample(sp, mat, inside, root=root, say=lambda *a: None, population=pop))
        if os.path.exists(inside):
            out.append(u"repo の中に紙を書いた")
            os.remove(inside)
        rec = json.load(open(sp, encoding="utf-8"))
        rec[u"本"][0][u"行"][0][2] = u"VALUE_MISMATCH"                              # 記録は VALUE_MISMATCH だが、測り直すと GROUNDED の行
        bad = os.path.join(d, "o", "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False))
        rec[u"本"][0][u"行"][0][2] = u"GROUNDED"
        rec[u"本"][0][u"行"][1][1] = 5                                             # 位置が違う行(測り直した claim が無い)
        bad2 = os.path.join(d, "o", "bad2.json")
        with open(bad2, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False))
        expect_stop(out, u"記録と合わない state", lambda: MS.run_sample(bad, mat, os.path.join(d, "paper", "s1.txt"), root=root, say=lambda *a: None, population=pop))
        expect_stop(out, u"記録と合わない位置", lambda: MS.run_sample(bad2, mat, os.path.join(d, "paper", "s2.txt"), root=root, say=lambda *a: None, population=pop))
        if os.path.exists(os.path.join(d, "paper", "s1.txt")) or os.path.exists(os.path.join(d, "paper", "s2.txt")):
            out.append(u"記録と合わないのに紙を書いた")
    return out


def typed_file(d, lines):
    p = os.path.join(d, "typed.tsv")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(u"\n".join(lines) + u"\n")
    return p


def types_problems():
    u"""run_types: 型の file が標本とそろう・型が 9 つのどれか・番号が重ならない・付けた席を書く・文を持たない。"""
    out = []
    with tmpdir() as d:
        pop, mat, root = states_fixture(d)
        sp = os.path.join(d, "o", "s.json")
        MS.run_states(root=root, population=pop, shape=SHAPE4, material=mat, out=sp, say=lambda *a: None)
        kw = dict(root=root, say=lambda *a: None)
        o1 = os.path.join(d, "o", "t1.json")
        rec = MS.run_types(sp, typed_file(d, [u"1\tア", u"2\tク"]), o1, **kw)
        text = open(o1, encoding="utf-8").read()
        eqp(out, u"返り値と file", json.loads(text), json.loads(json.dumps(rec)))
        eqp(out, u"行", rec[u"行"], [[1, 1, 2, 4, u"ア"], [2, 2, 1, 4, u"ク"]])
        eqp(out, u"型の集計", [rec[u"型の集計"][k] for k in u"アイウエオカキクケ"], [1, 0, 0, 0, 0, 0, 0, 1, 0])
        eqp(out, u"付けた席・盲検", (u"AI の席" in rec[u"型を付けた席"] and u"人は読んでいない" in rec[u"型を付けた席"], u"盲検ではない" in rec[u"盲検"]), (True, True))
        eqp(out, u"標本の規則", (rec[u"標本の規則"][u"種"], rec[u"標本の規則"][u"標本の数"], rec[u"標本の規則"][u"A の VALUE_MISMATCH の行の数"]), (20261114, 2, 2))
        eqp(out, u"記録に文の字が無い", [x in text for x in (u"売上高", u"百万円", u"span")], [False] * 3)
        for label, lines in ((u"行が足りない", [u"1\tア"]), (u"行が多い", [u"1\tア", u"2\tク", u"3\tケ"]), (u"番号が違う", [u"1\tア", u"3\tク"]), (u"重なる", [u"1\tア", u"1\tイ", u"2\tク"]),
                             (u"型が 9 つの外", [u"1\tア", u"2\tコ"]), (u"TAB でない", [u"1 ア", u"2 ク"]), (u"番号が数でない", [u"x\tア", u"2\tク"]), (u"3 列", [u"1\tア\tx", u"2\tク"])):
            o = os.path.join(d, "o", "bad_%s.json" % abs(hash(label)))
            expect_stop(out, label, lambda lines=lines, o=o: MS.run_types(sp, typed_file(d, lines), o, **kw))
            if os.path.exists(o):
                out.append(u"%s: 止まったのに記録を書いた" % label)
        expect_stop(out, u"出力が在る", lambda: MS.run_types(sp, typed_file(d, [u"1\tア", u"2\tク"]), o1, **kw))
    return out


def clean_problems():
    u"""記録に repo へ入れない欄・鍵らしい字が在れば止まる。"""
    out = []
    ok = collections.OrderedDict([(u"seal", MS.SEAL_REL), (u"本", [{u"行": [[1, 2]]}])])
    try:
        MS.check_clean(ok, json.dumps(ok, ensure_ascii=False))
    except SystemExit:
        out.append(u"良い記録で止まった")
    for key in (u"span", u"value", u"text", u"文"):
        bad = collections.OrderedDict([(u"本", [{key: u"x"}])])
        expect_stop(out, u"欄 %s" % key, lambda bad=bad: MS.check_clean(bad, json.dumps(bad, ensure_ascii=False)))
    leak = collections.OrderedDict([(u"x", u"a" * 40 + u"Z" * 8)])
    expect_stop(out, u"鍵らしい字", lambda: MS.check_clean(leak, json.dumps(leak, ensure_ascii=False)))
    return out


# ================================================================ 変異の表(約束の側から。関数の字を 1 か所替えた版を差し込み、検査が赤になることを見る)
def _m(label, mod, fn, old, new, check):
    return (label, mod, fn, old, new, check)


MUTANTS = (
    # 切り出し
    _m(u"切り出し: 最初の見出しが勝つ", MS, "cut_lines", u"            start, head = i, HEADINGS.index(m.group(1))", u"            start, head = i, HEADINGS.index(m.group(1))\n            break", cut_problems),
    _m(u"切り出し: 目次の行を外さない", MS, "cut_lines", u"if m and not any(t in ln for t in TOC_MARKS):", u"if m:", cut_problems),
    _m(u"切り出し: 目次の印を 1 つだけ見る", MS, "cut_lines", u"for t in TOC_MARKS)", u"for t in TOC_MARKS[:1])", cut_problems),
    _m(u"切り出し: 終わりが 2 で始まる行", MS, "cut_lines", u"if END_RE.match(lines[j]):", u"if lines[j].startswith(u\"2\"):", cut_problems),
    _m(u"切り出し: 終わりを始まりより前から探す", MS, "cut_lines", u"range(start + 1, len(lines))", u"range(len(lines))", cut_problems),
    _m(u"切り出し: 終わりの行を含める", MS, "cut_lines", u"lines[start:j]", u"lines[start:j + 1]", cut_problems),
    _m(u"切り出し: 見出しの番号が常に 0", MS, "cut_lines", u"HEADINGS.index(m.group(1))", u"0", cut_problems),
    _m(u"切り出し: 終わりなしを始まりなしと言う", MS, "cut_lines", u"return None, None, WHY_END", u"return None, None, WHY_START", cut_problems),
    _m(u"切り出し: NFKC を掛けない", MS, "cut_html", u"unicodedata.normalize(\"NFKC\", ln).strip()", u"ln.strip()", cut_problems),
    _m(u"切り出し: 前後の空白を落とさない", MS, "cut_html", u"unicodedata.normalize(\"NFKC\", ln).strip()", u"unicodedata.normalize(\"NFKC\", ln)", cut_problems),
    _m(u"切り出し: NFC にする", MS, "cut_html", u"\"NFKC\"", u"\"NFC\"", cut_problems),
    _m(u"切り出し: 空の行を捨てない", MS, "cut_html", u"        if ln:", u"        if True:", cut_problems),
    _m(u"切り出し: 手本の html_to_lines を呼ばない", MS, "cut_html", u"TS.html_to_lines(h)", u"h.split(u\"\\n\")", cut_problems),
    _m(u"切り出し: member を部分一致で探す", MS, "cut", u"if QUALITATIVE not in z.namelist():", u"if not any(n.endswith(u\"qualitative.htm\") for n in z.namelist()):", cut_problems),
    _m(u"切り出し: decode を緩める", MS, "cut", u"raw.decode(\"utf-8\")", u"raw.decode(\"utf-8\", \"replace\")", cut_problems),
    _m(u"切り出し: ZIP でなくても止めない", MS, "cut", u"raise Stop(u\"**ZIP として読めない。止める**\")", u"return None, None, WHY_MEMBER", cut_problems),
    # 包み直し
    _m(u"包み直し: 名前の順にしない", MS, "wrap", u"sorted(z.infolist(), key=lambda i: i.filename)", u"z.infolist()", wrap_problems),
    _m(u"包み直し: .htm を全部入れる", MS, "wrap", u"base.endswith(OLD_SUFFIX)", u"base.endswith(u\".htm\")", wrap_problems),
    _m(u"包み直し: Attachment の外(サマリー)も入れる", MS, "wrap", u"info.filename.startswith(ATTACH_PREFIX) and ", u"", wrap_problems),
    _m(u"包み直し: 名前を替えない", MS, "wrap", u"base[:-len(OLD_SUFFIX)] + NEW_SUFFIX", u"base", wrap_problems),
    _m(u"包み直し: 中身を 1 byte 変える", MS, "wrap", u"out.writestr(_info(new), z.read(info.filename))", u"out.writestr(_info(new), z.read(info.filename)[:-1])", wrap_problems),
    _m(u"包み直し: 名前が重なっても止めない", MS, "wrap", u"if new in names or new == OVERVIEW_MEMBER:", u"if False:", wrap_problems),
    _m(u"包み直し: 文の member の名前が違う", MS, "wrap", u"out.writestr(_info(OVERVIEW_MEMBER), overview_html(text))", u"out.writestr(_info(OVERVIEW_MEMBER + u\"x\"), overview_html(text))", wrap_problems),
    _m(u"包み直し: member の日時が固定でない", MS, "_info", u"date_time=ZIP_DATE_TIME", u"date_time=(2000, 1, 1, 0, 0, 0)", wrap_problems),
    _m(u"包み直し: 圧縮を替える", MS, "_info", u"zipfile.ZIP_DEFLATED", u"zipfile.ZIP_STORED", wrap_problems),
    _m(u"包み直し: 文を段落にしない", MS, "overview_html", u"OVERVIEW_HEAD + PR.prose_to_html(text) + OVERVIEW_TAIL", u"OVERVIEW_HEAD + text + OVERVIEW_TAIL", wrap_problems),
    # 判定の配線
    _m(u"判定: profile が違う", MS, "judge_book", u"TS.profile_rows(wrapped, None, wrapped, PROFILE)", u"TS.profile_rows(wrapped, None, wrapped, u\"P30E\")", judge_problems),
    _m(u"判定: text を渡す", MS, "judge_book", u"TS.profile_rows(wrapped, None, wrapped, PROFILE)", u"TS.profile_rows(wrapped, text, wrapped, PROFILE)", judge_problems),
    _m(u"判定: 包む前の ZIP を渡す", MS, "judge_book", u"TS.profile_rows(wrapped, None, wrapped, PROFILE)", u"TS.profile_rows(zb, None, wrapped, PROFILE)", judge_problems),
    _m(u"判定: fact の数を元の ZIP で数える", MS, "judge_book", u"I.load_instance(wrapped)", u"I.load_instance(zb)", judge_problems),
    _m(u"判定: 字数が違う", MS, "judge_book", u"(u\"字数\", len(text))", u"(u\"字数\", len(text) + 1)", judge_problems),
    _m(u"判定: 見出しの番号が違う", MS, "judge_book", u"(u\"見出しの番号\", head)", u"(u\"見出しの番号\", 0)", judge_problems),
    _m(u"判定: 切れない本の理由が無い", MS, "judge_book", u"(u\"理由\", why)", u"(u\"理由\", None)", judge_problems),
    # states・集計・記録
    _m(u"states: 材料の sha256 を見ない", MS, "states_job", u"if ST.sha256_bytes(zb) != sha:", u"if False:", states_problems),
    _m(u"states: 材料の置き場が変わっても止めない", MS, "run_states", u"if before != after:", u"if False:", states_problems),
    _m(u"states: 本番の記録を使い捨ての材料で作る", MS, "material_dir", u"and mat != prod:", u"and False:", states_problems),
    _m(u"states: 時間を測らない", MS, "run_states", u"elapsed = clock() - t0", u"elapsed = 0.0", states_problems),
    _m(u"states: 本の順が # の順でない", MS, "run_states", u"books = TS.NF.map_pool(states_job, jobs, procs)", u"books = list(reversed(TS.NF.map_pool(states_job, jobs, procs)))", states_problems),
    _m(u"集計: GROUNDED が 0 の本の条件が逆", MS, "block", u"if not c.get(G, 0):", u"if c.get(G, 0):", states_problems),
    _m(u"集計: VALUE_MISMATCH が 1 以上の本の閾値が違う", MS, "block", u"if c.get(VM, 0) >= 1:", u"if c.get(VM, 0) >= 2:", states_problems),
    _m(u"集計: 切れた本の数え方が逆", MS, "block", u"b[u\"切り出し\"] == CUT_OK]", u"b[u\"切り出し\"] == CUT_NG]", states_problems),
    _m(u"集計: 字数の合計が字数でない", MS, "block", u"sum(b[u\"字数\"] for b in cut_books)", u"sum(1 for b in cut_books)", states_problems),
    _m(u"集計: A に丙を入れる", MS, "tally", u"out[u\"A(甲 + 乙)\"] = block([b for b in books if b[u\"群\"] in A_GROUPS])", u"out[u\"A(甲 + 乙)\"] = block(books)", states_problems),
    _m(u"集計: 切れた本の claim が 0 の本が数えられない", MS, "block", u"if not b[u\"行\"]:", u"if False:", states_problems),
    _m(u"記録: 欄の禁止を見ない", MS, "check_clean", u"    if bad:", u"    if False:", clean_problems),
    _m(u"記録: 鍵らしい字を見ない", MS, "check_clean", u"    if leaks:", u"    if False:", clean_problems),
    # 標本・型
    _m(u"標本: 番号の順にしない", MS, "pick_sample", u"return sorted(random.Random(seed).sample(range(n_rows), k))", u"return random.Random(seed).sample(range(n_rows), k)", sample_problems),
    _m(u"標本: 種が違う", MS, "pick_sample", u"seed=SAMPLE_SEED", u"seed=SAMPLE_SEED + 1", sample_problems),
    _m(u"標本: 本数が違う", MS, "pick_sample", u"k=SAMPLE_N", u"k=SAMPLE_N + 1", sample_problems),
    _m(u"標本: 少ないとき全部にしない", MS, "pick_sample", u"if n_rows <= k:", u"if n_rows <= 5:", sample_problems),
    _m(u"標本: 行の母集団が A だけでない", MS, "vm_rows_a", u"if b[u\"群\"] not in A_GROUPS:", u"if False:", sample_problems),
    _m(u"標本: VALUE_MISMATCH 以外も入れる", MS, "vm_rows_a", u"if r[2] == VM)", u"if r[2] != VM)", sample_problems),
    _m(u"標本: 本の順が # の順でない", MS, "vm_rows_a", u"key=lambda b: b[u\"#\"]", u"key=lambda b: -b[u\"#\"]", sample_problems),
    _m(u"標本: 行の順が文・位置の順でない", MS, "vm_rows_a", u"key=lambda r: (r[0], r[1])", u"key=lambda r: (r[1], r[0])", sample_problems),
    _m(u"標本: 番号が 0 から", MS, "sample_items", u"(i + 1,)", u"(i,)", sample_problems),
    _m(u"紙: git の木の中を見ない", MS, "inside_repo", u"return r.returncode == 0 and r.stdout.strip() == b\"true\"", u"return False", repo_problems),
    _m(u"紙: repo の中でも書く", MS, "run_sample", u"if inside_repo(sheet, repo):", u"if False:", sheet_problems),
    _m(u"紙: 在っても書く", MS, "run_sample", u"if os.path.exists(sheet):", u"if False:", sheet_problems),
    _m(u"紙: 記録と合わない行を通す", MS, "run_sample", u"if c is None or c[\"state\"] != VM:", u"if c is None:", sheet_problems),
    _m(u"紙: 記録に無い行を通す", MS, "run_sample", u"if c is None or c[\"state\"] != VM:", u"if False:", sheet_problems),
    _m(u"型: 標本と型の番号がそろわなくても通す", MS, "run_types", u"if sorted(typed) != [it[0] for it in items]:", u"if False:", types_problems),
    _m(u"型: 9 つの外の字を通す", MS, "read_typed", u" or parts[1] not in TYPES", u"", types_problems),
    _m(u"型: 列の数を見ない", MS, "read_typed", u"len(parts) != 2 or ", u"", types_problems),
    _m(u"型: 同じ番号を通す", MS, "read_typed", u"if k in out:", u"if False:", types_problems),
    _m(u"型: 付けた席を書かない", MS, "run_types", u"rec[u\"型を付けた席\"] = TYPED_BY", u"rec[u\"型を付けた席\"] = u\"人\"", types_problems),
    # 置く script
    _m(u"置く: 母集団の行の数を見ない", ST, "validate_population", u"if len(rows) != n:", u"if False:", population_problems),
    _m(u"置く: 母集団の番号を見ない", ST, "validate_population", u"if [r[0] for r in rows] != list(range(1, len(rows) + 1)):", u"if False:", population_problems),
    _m(u"置く: sha256 の重なりを見ない", ST, "validate_population", u"if len(set(r[3] for r in rows)) != len(rows):", u"if False:", population_problems),
    _m(u"置く: 群の本数を見ない", ST, "validate_population", u"if [(g, c.get(g, 0)) for g in groups] != list(groups.items()) or sum(c.values()) != len(rows):", u"if False:", population_problems),
    _m(u"置く: 表に無い ZIP も選ぶ", ST, "scan_sources", u"if s in wanted and s not in found:", u"if s not in found:", scan_problems),
    _m(u"置く: サマリーの外も見る", ST, "summary_kinds", u"if m.startswith(SUMMARY_PREFIX) and b.startswith", u"if b.startswith", kinds_problems),
    _m(u"置く: 様式の字を別の欄から読む", ST, "summary_kinds", u"b.split(\"-\")[1][:KIND_LEN]", u"b.split(\"-\")[2][:KIND_LEN]", kinds_problems),
    _m(u"置く: 在る記録に上書きする", ST, "write_text_exclusive", u"if os.path.exists(path):", u"if False:", exclusive_problems),
    _m(u"置く: 400 本そろわなくても進む", ST, "run_stage", u"if len(found) != len(rows):", u"if False:", stage_problems),
    _m(u"置く: 様式の種類を見ない", ST, "run_stage", u"if kinds != set([kind]):", u"if False:", stage_problems),
    _m(u"置く: 在る file の sha256 を見ない", ST, "run_stage", u"if sha256_file(p) != sha:", u"if False:", stage_problems),
    _m(u"置く: 置き先の位置を見ない", ST, "run_stage", u"        check_out_dir(dest, base)\n", u"        pass\n", stage_problems),
    _m(u"置く: 在る記録を上書きする", ST, "run_stage", u"if os.path.exists(record):", u"if False:", stage_problems),
    _m(u"置く: 置く前の字の検査をしない", ST, "run_stage", u"    compose(before, before)", u"    pass", stage_problems),
    _m(u"置く: ほかの cache の変化を見ない", ST, "run_stage", u"    if before != after:", u"    if False:", stage_problems),
    _m(u"置く: --out なのに本番の記録に書く", ST, "run_stage", u"if os.path.abspath(record) == os.path.abspath(prod_record):", u"if False:", stage_problems),
    _m(u"置く: --out に --record が要らない", ST, "run_stage", u"if record is None:", u"if False:", stage_problems),
    _m(u"置く: 本番の置き場が違う", ST, "run_stage", u"dest = os.path.join(base, CACHE_NAME)", u"dest = os.path.join(base, u\"x\")", stage_problems),
    _m(u"置く: 開かない folder も数える", ST, "others_snapshot", u"if n != CACHE_NAME and n not in skip", u"if n != CACHE_NAME", stage_problems),
    _m(u"置く: 置き先が cache の根でも通す", ST, "check_out_dir", u"if real == base:", u"if False:", stage_problems),
    _m(u"置く: 置き先が既存の cache の中でも通す", ST, "check_out_dir", u"if real.startswith(base + os.sep) and", u"if False and", stage_problems),
    _m(u"置く: --out なしで本番でない記録を許す", ST, "run_stage", u"if record is not None and os.path.abspath(record) != os.path.abspath(prod_record):", u"if False:", stage_problems),
)


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_seal_tables_paths_and_key_phrases_are_complete(self):
        self.assertEqual([], seal_problems(self.seal))
        self.assertEqual(400, len(seal_table(self.seal)))

    def test_a_2_a_changed_key_phrase_turns_the_seal_check_red(self):
        for ph in SEAL_PHRASES:
            self.assertIn(ph, self.seal)
            mutated_seal = self.seal.replace(ph, ph[:-1] + u"？", 1)
            self.assertNotEqual(mutated_seal, self.seal)
            self.assertNotEqual([], seal_problems(mutated_seal), ph)

    def test_a_3_a_broken_table_or_prediction_row_turns_it_red(self):
        lines = self.seal.split("\n")
        first = [i for i, ln in enumerate(lines) if ln.startswith("| 1 | 甲 |")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:first] + lines[first + 1:])))                              # 400 行が 399 行
        row5 = [i for i, ln in enumerate(lines) if ln.startswith("| 5 | 甲 |")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:row5] + [lines[row5].replace(u"| 甲 |", u"| 乙 |", 1)] + lines[row5 + 1:])))     # 群の本数
        self.assertNotEqual([], seal_problems("\n".join(lines[:row5] + [lines[row5].replace(u"acedifsm", u"acedjpsm", 1)] + lines[row5 + 1:])))   # 様式の種類の数
        self.assertNotEqual([], seal_problems("\n".join(lines[:row5] + [lines[row5].replace(u"| 43 |", u"| 44 |", 1)] + lines[row5 + 1:])))        # 下見の claim の合計
        self.assertNotEqual([], seal_problems("\n".join(lines[:row5] + [lines[row5].replace(u"| 切れた |", u"| 切れない |", 1)] + lines[row5 + 1:])))   # 下見の切れた本
        self.assertNotEqual([], seal_problems("\n".join(lines[:row5] + [lines[1:][0]] + lines[row5 + 1:])))                  # 行が表でなくなる
        sha1 = seal_table(self.seal)[0][3]
        sha2 = seal_table(self.seal)[1][3]
        self.assertNotEqual([], seal_problems(self.seal.replace(sha2, sha1, 1)))                                          # sha256 の重なり
        s7 = [i for i, ln in enumerate(lines) if ln.startswith("| S-7 |")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:s7] + lines[s7 + 1:])))                                   # 10 行が 9 行
        cells = lines[s7].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:s7] + [" | ".join(cells[:2]) + " |"] + lines[s7 + 1:])))       # 外れ方が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:s7] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[s7 + 1:])))   # 予測が空
        self.assertNotEqual([], seal_problems(self.seal.replace("## §5 ", "## 五 ", 1)))                                  # 節が揃わない
        self.assertNotEqual([], seal_problems(self.seal.replace(RECORD_RELS[1], "fixtures/xbrl/tanshin_self/other.json")))     # 記録の path が封に無い
        self.assertNotEqual([], seal_problems(self.seal.replace(STAGE_REL, "measure/other_stage.py")))

    def test_a_4_the_seal_is_in_history_as_the_sealed_commit(self):
        added = PR.added_commits(REPO, PREFIX + SEAL_REL)
        self.assertEqual(1, len(added))
        self.assertTrue(added[0].startswith(SEAL_COMMIT_SHORT))


class ScriptConstantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def test_b_2_the_population_is_read_from_the_seal_not_copied_into_the_script(self):
        rows = ST.read_population()
        self.assertEqual([(r[0], r[1], r[2], r[3]) for r in seal_table(self.seal)], rows)
        self.assertEqual(400, len(rows))
        for rel in SCRIPT_RELS:
            src = read(rel)
            self.assertEqual([], [r[0] for r in rows if r[3] in src], rel)           # 表の sha256 を script に 1 本も写していない

    def _each_constant_changed(self, which, name, val):
        ms2 = types.SimpleNamespace(**dict((k, getattr(MS, k)) for k in dir(MS) if not k.startswith("__")))
        st2 = types.SimpleNamespace(**dict((k, getattr(ST, k)) for k in dir(ST) if not k.startswith("__")))
        setattr(ms2 if which == "ms" else st2, name, val)
        ms2.ST = st2
        return script_problems(self.seal, ms=ms2, st=st2)

    def test_b_3_each_script_constant_turns_the_check_red_when_changed(self):
        ms_changes = (
            ("SEAL_REL", "docs/x.md"), ("SEAL_COMMIT", "0000000"), ("SCRIPT_REL", "measure/x.py"), ("STAGE_SCRIPT_REL", "measure/x.py"), ("DOC_REL", "docs/x.md"),
            ("STATES_REL", "fixtures/x.json"), ("TYPES_REL", "fixtures/x.json"),
            ("HEAD_RE", re.compile(u"^1\\s*\\.\\s*(経営成績等の概況|当中間決算に関する定性的情報)")), ("END_RE", re.compile(u"^2\\s*\\.\\s*[^\\s]")),
            ("HEADINGS", (u"当中間決算に関する定性的情報", u"経営成績等の概況", u"当四半期決算に関する定性的情報")), ("TOC_MARKS", (u"...",)), ("QUALITATIVE", "XBRLData/Attachment/x.htm"),
            ("ATTACH_PREFIX", "XBRLData/Summary/"), ("OLD_SUFFIX", "-ixbrl.html"), ("NEW_SUFFIX", "-ixbrl.htm"), ("PUBLIC_DOC", "XBRL/AuditDoc/"),
            ("OVERVIEW_MEMBER", "XBRL/PublicDoc/overview_ixbrl.htm"), ("TEXTBLOCK_NAME", "jpcrp_cor:Other"), ("OVERVIEW_HEAD", u'<ix:nonNumeric name="x">'), ("PROFILE", "P32E"),
            ("SAMPLE_SEED", 20261115), ("SAMPLE_N", 100), ("A_GROUPS", (u"甲",)), ("B_GROUPS", (u"乙", u"丙")), ("WHYS", (u"member なし", u"decode", u"始まりなし")),
            ("CUT_OK", u"切れ"), ("TYPES", collections.OrderedDict(list(MS.TYPES.items())[:-1])), ("TYPED_BY", u"司令塔"))
        for name, val in ms_changes:
            self.assertNotEqual([], self._each_constant_changed("ms", name, val), name)
        st_changes = (
            ("SEAL_REL", "docs/x.md"), ("SEAL_COMMIT", "0000000"), ("SCRIPT_REL", "measure/x.py"), ("POPULATION_REL", "fixtures/x.json"), ("N_ROWS", 399),
            ("GROUP_COUNTS", collections.OrderedDict([(u"甲", 50), (u"乙", 200), (u"丙", 149)])), ("CACHE_NAME", "tanshin-self-x"), ("SKIP_CACHES", ()),
            ("SUMMARY_PREFIX", "XBRLData/Attachment/"), ("SUMMARY_FILE_PREFIX", "tsx-"), ("SUMMARY_FILE_SUFFIX", "-ixbrl.html"), ("KIND_LEN", 7),
            ("KEY_PATTERNS", tuple(ST.KEY_PATTERNS[:-1])), ("LONG_ALNUM", re.compile(r"[A-Za-z0-9_\-]{33,}")))
        for name, val in st_changes:
            self.assertNotEqual([], self._each_constant_changed("st", name, val), name)
        ms3 = types.SimpleNamespace(**dict((k, getattr(MS, k)) for k in dir(MS) if not k.startswith("__")))
        ms3.ST = types.SimpleNamespace(**dict((k, getattr(ST, k)) for k in dir(ST) if not k.startswith("__")))
        self.assertNotEqual([], script_problems(self.seal, ms=ms3, st=ST))                   # 測る script が別の置く script を持つ

    def test_b_3b_a_changed_row_reader_turns_the_check_red(self):
        with patched(ST, SEAL_ROW=re.compile(r"^\| (\d+) \| (甲|乙) \| (\w+) \| `([0-9a-f]{64})` \| (?:切れた|切れない) \| (?:\d+|-) \|$", re.M)):
            self.assertNotEqual([], script_problems(self.seal))
        self.assertEqual([], script_problems(self.seal))

    def test_b_4_a_changed_character_in_the_seal_turns_the_comparison_red(self):
        sha = seal_table(self.seal)[0][3]
        self.assertNotEqual([], seal_problems(self.seal.replace(sha, sha[:-1] + (u"0" if sha[-1] != u"0" else u"1"), 1)))           # 表の 1 字は門に留めた sha256 で赤
        self.assertNotEqual([], script_problems(self.seal.replace(u"^2\\s*\\.\\s*[^\\d\\s]", u"^2\\s*\\.\\s*[^\\s]", 1)))
        self.assertNotEqual([], script_problems(self.seal.replace(u"(ケ) 読んでも分けられない", u"(ケ) 読んでも分けない")))

    def test_b_5_the_default_places_are_the_new_folder_and_the_new_record(self):
        self.assertTrue(ST.default_cache_dir().endswith(os.path.join(".cache", "audit-core", "tanshin-self-2026-11-14")))
        self.assertEqual(os.path.join(ROOT, RECORD_RELS[0]), os.path.join(ROOT, ST.POPULATION_REL))


class EngineZeroTest(unittest.TestCase):
    def test_c_1_the_real_history_has_no_engine_lib_device_or_previous_script_change_since_the_seal(self):
        self.assertEqual([], engine_since_seal_problems())

    def _repo(self):
        r = PR.Repo()
        for rel in ("adapters/xbrl/other.py", "core/py/x.py", "measure/lib/numbers.py", "measure/inject.py", "measure/xbrl_tanshin_2026-11-09.py", "measure/xbrl_tanshin_fetch_2026-11-09.py", "fixtures/xbrl/tanshin/a.json", "measure/free.py"):
            r.put(rel)
        r.commit("adapters/xbrl/other.py", "core/py/x.py", "measure/lib/numbers.py", "measure/inject.py", "measure/xbrl_tanshin_2026-11-09.py", "measure/xbrl_tanshin_fetch_2026-11-09.py", "fixtures/xbrl/tanshin/a.json", "measure/free.py")
        r.put("docs/seal.md")
        r.commit("docs/seal.md")
        return r

    def _problems(self, r):
        return engine_since_seal_problems(root=r.d, seal_rel="docs/seal.md")

    def test_c_2_a_clean_range_is_green_and_each_touched_path_is_red(self):
        r = self._repo()
        self.assertEqual([], self._problems(r))
        r.put("measure/free.py")                                      # 関係の無い file は触ってよい(未 commit のまま)
        self.assertEqual([], self._problems(r))
        for rel in ("adapters/xbrl/other.py", "core/py/x.py", "measure/lib/numbers.py", "measure/inject.py", "measure/xbrl_tanshin_2026-11-09.py", "measure/xbrl_tanshin_fetch_2026-11-09.py", "fixtures/xbrl/tanshin/a.json"):
            r = self._repo()
            r.put(rel)
            r.commit(rel)
            self.assertNotEqual([], self._problems(r), rel)
        r = self._repo()
        r.put("measure/free.py")
        r.commit("measure/free.py")
        self.assertEqual([], self._problems(r))

    def test_c_3_an_unknown_seal_is_red(self):
        r = self._repo()
        self.assertNotEqual([], engine_since_seal_problems(root=r.d, seal_rel="docs/none.md"))


class OrderTest(unittest.TestCase):
    def test_i_1_the_real_history_has_the_seal_before_the_scripts_and_the_gate(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def _good(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        for o in ("measure/s.py", "tests/g.py"):
            r.put(o)
        r.commit("measure/s.py", "tests/g.py")
        return r, s

    def test_i_2_good_order_is_green_and_bad_orders_are_red(self):
        r, s = self._good()
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], ["measure/s.py", "tests/g.py"]))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], ["measure/s.py"]))
        r.put("tests/new.py")                                                          # 未 commit
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], ["measure/s.py", "tests/new.py"]))
        r2 = PR.Repo()
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["measure/s.py"]))     # script が封より前

    def test_i_3_the_order_check_lists_the_two_scripts_and_this_gate(self):
        self.assertEqual(list(SCRIPT_RELS) + [GATE_REL], [STAGE_REL, SCRIPT_REL, GATE_REL])
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in SCRIPT_RELS + (GATE_REL,)))


class CutTest(unittest.TestCase):
    def test_d_1_the_cut_rules_hold(self):
        self.assertEqual([], cut_problems())


class WrapTest(unittest.TestCase):
    def test_e_1_the_wrapped_zip_follows_the_rules(self):
        self.assertEqual([], wrap_problems())

    def test_e_2_the_wrapped_zip_is_never_written_by_the_script(self):
        src = read(SCRIPT_REL)
        self.assertEqual([], [m for m in re.findall(r"open\([^)]*[\"']wb[\"']", src)])        # 包んだ ZIP を書く経路が無い(binary で書く open が無い)


class JudgeTest(unittest.TestCase):
    def test_f_1_the_book_record_and_the_profile_wiring_hold(self):
        self.assertEqual([], judge_problems())


class StageTest(unittest.TestCase):
    def test_g_1_the_stage_script_follows_the_rules(self):
        self.assertEqual([], stage_problems())

    def test_g_2_the_population_checks_hold(self):
        self.assertEqual([], population_problems())
        self.assertEqual([], scan_problems())
        self.assertEqual([], kinds_problems())
        self.assertEqual([], exclusive_problems())

    def test_g_3_the_real_population_passes_the_checks(self):
        self.assertEqual(400, len(ST.validate_population(ST.read_population())))


class StatesTest(unittest.TestCase):
    def test_h_1_the_states_record_is_whole_and_reproducible(self):
        self.assertEqual([], states_problems())
        self.assertEqual([], clean_problems())


class SampleTest(unittest.TestCase):
    def test_j_1_the_sample_is_drawn_by_the_rule(self):
        self.assertEqual([], sample_problems())

    def test_j_2_the_sheet_is_written_outside_the_repo_only(self):
        self.assertEqual([], repo_problems())
        self.assertEqual([], sheet_problems())

    def test_j_3_the_types_record_follows_the_rules(self):
        self.assertEqual([], types_problems())


class MutantTest(unittest.TestCase):
    def test_k_1_every_check_is_green_on_the_real_code_and_red_on_each_mutant(self):
        checks = sorted(set(m[5] for m in MUTANTS), key=lambda f: f.__name__)
        for chk in checks:
            self.assertEqual([], chk(), chk.__name__)
        silent = []
        for (label, mod, fn, old, new, chk) in MUTANTS:
            orig = getattr(mod, fn)
            with mutated(mod, fn, old, new), warnings.catch_warnings():
                warnings.simplefilter("ignore")                  # 「名前が重なっても止めない」変異は zipfile が Duplicate name を警告する
                got = guard(chk)
            self.assertIs(getattr(mod, fn), orig)
            if not got:
                silent.append(label)
        self.assertEqual([], silent)

    def test_k_2_a_mutant_is_always_put_back(self):
        orig = MS.cut_lines
        with self.assertRaises(RuntimeError):
            with mutated(MS, "cut_lines", u"range(start + 1, len(lines))", u"range(len(lines))"):
                self.assertIsNot(MS.cut_lines, orig)
                raise RuntimeError("x")
        self.assertIs(MS.cut_lines, orig)
        with self.assertRaises(AssertionError):
            with mutated(MS, "cut_lines", u"this text is not in the function", u"x"):
                pass
        self.assertIs(MS.cut_lines, orig)


class WiringTest(unittest.TestCase):
    def test_l_1_the_script_calls_the_previous_functions_and_defines_none_of_the_same_name(self):
        self.assertEqual([], reuse_problems())

    def test_l_2_a_same_name_definition_or_a_missing_call_turns_it_red(self):
        with tmpdir() as d:
            src = read(SCRIPT_REL)
            p = os.path.join(d, "s.py")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(src + u"\n\ndef html_to_lines(h):\n    return []\n")
            self.assertNotEqual([], reuse_problems(src_path=p))
            for alias, fn in REUSED_FUNCS:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(src.replace(u"%s.%s" % (alias, fn), u"%s.%sx" % (alias, fn)))
                self.assertNotEqual([], reuse_problems(src_path=p), (alias, fn))
        ms2 = types.SimpleNamespace(**dict((k, getattr(MS, k)) for k in dir(MS) if not k.startswith("__")))
        ms2.TS = types.SimpleNamespace()
        self.assertNotEqual([], reuse_problems(ms=ms2))

    def test_l_3_the_stage_script_imports_no_network_module(self):
        self.assertEqual([], network_problems())
        with tmpdir() as d:
            for line in (u"import urllib.request", u"from urllib import request", u"import socket", u"import http.client", u"from http import client", u"import ssl", u"import requests"):
                p = os.path.join(d, "s.py")
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(u"import os\n" + line + u"\n")
                self.assertNotEqual([], network_problems(p), line)
            with open(os.path.join(d, "s.py"), "w", encoding="utf-8") as fh:
                fh.write(u"import os\nimport hashlib\n")
            self.assertEqual([], network_problems(os.path.join(d, "s.py")))

    def test_l_4_names_that_existed_before_loading_are_put_back(self):
        marker = types.ModuleType("pswap_for_idmap")
        before = sys.modules.get("pswap_for_idmap")
        sys.modules["pswap_for_idmap"] = marker
        sentinel = types.ModuleType("rmix_for_pbind")
        before2 = sys.modules.get("rmix_for_pbind")
        sys.modules["rmix_for_pbind"] = sentinel
        try:
            mod = load_module(SCRIPT_REL, "tanshin_self_script_reload_probe")
            self.assertIs(marker, sys.modules["pswap_for_idmap"])                      # 先に居た名前は元の object
            self.assertIs(sentinel, sys.modules["rmix_for_pbind"])
            self.assertIs(mod, sys.modules["tanshin_self_script_reload_probe"])        # 自分の名前は残る
            self.assertIsNot(mod.TS, None)
        finally:
            for k, v in (("pswap_for_idmap", before), ("rmix_for_pbind", before2)):
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
            sys.modules.pop("tanshin_self_script_reload_probe", None)

    def test_l_5_no_reserved_names_no_docid_no_tdnet_no_known_code_in_the_new_files(self):
        self.assertEqual([], reserved_problems())
        self.assertEqual([], name_problems())
        with tmpdir() as d:
            with open(os.path.join(d, "g.py"), "w") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rels=("g.py",), base=d))
            with open(os.path.join(d, "g.py"), "w") as fh:
                fh.write("X_ENGINE_LATER = 1\n")
            self.assertEqual([], reserved_problems(rels=("g.py",), base=d))
            for text, codes in (("x = 'S100" + "ABCD'\n", None), ("x = '0812" + "20260810517389'\n", None), ("x = 'ab" + "12345cd'\n", ["12345"])):
                with open(os.path.join(d, "s.py"), "w") as fh:
                    fh.write(text)
                self.assertNotEqual([], name_problems(rels=("s.py",), base=d, codes=codes), text)

    def test_l_6_the_new_files_carry_no_secret_material_markers(self):
        handoff = u"sgogi-coach" + u"-handoff"                                        # 開かない folder(この file が自分の字に当たらないよう、つないで書く)
        for rel in SCRIPT_RELS + (GATE_REL,):
            self.assertNotIn(handoff, read(rel), rel)
        skipped = ST.SKIP_CACHES[0]
        self.assertEqual([], [rel for rel in SCRIPT_RELS if skipped in read(rel) and rel != STAGE_REL])           # 開かない folder の名前を持つのは置く script の SKIP だけ
        self.assertEqual(1, read(STAGE_REL).count(skipped))                                        # 置く script の中でも SKIP_CACHES の 1 か所だけ

    def test_l_7_the_two_scripts_share_one_stage_instance_and_the_previous_script_instance(self):
        self.assertIs(MS.ST.default_cache_dir.__globals__["CACHE_NAME"], MS.ST.CACHE_NAME)
        self.assertIsNot(MS.TS, None)
        self.assertTrue(callable(MS.TS.html_to_lines) and callable(MS.TS.profile_rows))


if __name__ == "__main__":
    unittest.main()
