# -*- coding: utf-8 -*-
"""封 docs/XBRL_KAM_SEAL_2026-11-15.md(KAM ― 有価証券報告書の監査報告書の「監査上の主要な検討事項」の文を、同じ有報の fact で確かめる)の測定の門。封 §0-2・§1・§2・§3・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_kam_result.py`` は次の段。本番の記録・結果の文書の数を縛る。この門は本番の記録が無い状態でも緑で、在れば形だけを縛る)

1. 封の字: §1 の表が 201 行(群 甲 67・乙 40・丙 94・# と並び)・§0-1 の表が §1 の下見の列と同じ数・§3 が K-1〜K-11 の 11 行でどの行も欄・予測・外れ方を持つ・規則の正規表現・札の名前・種・本数・記録の path。
2. 封の字と script の定数が同じ(表は封の file から読む。script に 201 行を写さない)。
3. engine 0 行: 封の commit から HEAD まで ``core/``・``adapters/``・``measure/lib``・``measure/inject.py`` と、この便が読み込む前の便の script・記録を触っていない。
4. 順序: 封 497a4661 ⊏ script・この門(**commit の順**。未 commit は赤(skip にしない))。
5. 切り出し(``cut_kam``)・判定の配線(``judge_book``・``row10``)・集計・読む行の引き方・型の記録・紙の置き場の振る舞い。
6. 材料を探す所: 201 本そろわなければ何も書かない・重なり・群違い・folder の一覧が変われば止まる・file 名(docID)を書かない。
7. 配線: 前の便の関数を **呼ぶ**(同名の関数を定義しない)・読み込みの前に居た ``sys.modules`` の名前は戻る・既存の門が行頭の名前を数える変数名を置かない・docID・証券コード・TDnet の番号の字が無い。
8. 本番の記録(``fixtures/xbrl/kam/`` の 3 つ)が在れば、母集団・本の順・書かない字・読む行の形が封と合う。無ければ何も言わない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``・``CONST_MUTANTS``。関数の字を 1 か所替えた版・定数を替えた版を module の中に差し込み、検査が赤になることを見て、必ず元の object に戻す)。
材料から測り直す試験(201 本の切り出しと判定を封の下見の列と照らす)は、環境変数 ``AUDIT_CORE_KAM_REMEASURE=1`` のときだけ走る。
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
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import warnings
import zipfile
from xml.sax.saxutils import escape

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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_kam_seal")      # 順序の部品(order_problems・Repo・git_in・added_commits)。門としては走らせない
MS = load_module("measure/xbrl_kam_2026-11-15.py", "kam_script_for_seal_gate")
TSS = MS.TSS
ST = MS.ST
TS = MS.TS

SEAL_REL = "docs/XBRL_KAM_SEAL_2026-11-15.md"
SEAL_COMMIT_SHORT = "497a4661"                 # 封の commit(literal に留める。script の定数と違えば script_problems が赤)
SCRIPT_REL = "measure/xbrl_kam_2026-11-15.py"
GATE_REL = "tests/measure/test_xbrl_kam_seal.py"
#: 結果の門(次の段で足す)。この段では順序の検査に入れない
LATER_GATE_REL = "tests/measure/test_xbrl_kam_result.py"
DOC_REL = "docs/XBRL_KAM_RESULT_2026-11-15.md"
RECORD_RELS = ("fixtures/xbrl/kam/population_2026-11-15.json", "fixtures/xbrl/kam/states_2026-11-15.json", "fixtures/xbrl/kam/read_types_2026-11-15.json")
#: 封の commit から 0 行でなければならない path(engine・lib・仕掛けと、この便が読み込む前の便の script・記録)
NOT_TOUCHED_RELS = ("adapters", "core", "measure/lib", "measure/inject.py", "measure/xbrl_tanshin_2026-11-09.py", "measure/xbrl_tanshin_fetch_2026-11-09.py",
                    "measure/xbrl_tanshin_self_2026-11-14.py", "measure/xbrl_tanshin_self_stage_2026-11-14.py", "fixtures/xbrl/tanshin", "fixtures/xbrl/tanshin_self")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT",
                     "FINGERPRINT_", "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL", "ENGINE_AT_MEASURE", "ENGINE_DECLARED")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
TDNET_RE = re.compile(r"0812\d{14}")
PRED_IDS = tuple("K-%d" % i for i in range(1, 12))
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx")
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"ZIP の member のうち、名前に `/AuditDoc/` を含み `.htm` で終わるものを名前の順に、utf-8(strict)で読む。",
    u"`<ix:nonNumeric\\b[^>]*\\bname=\"<札の名前>\"[^>]*>`",
    u"`<ix:nonNumeric\\b[^>]*?(/?)>|</ix:nonNumeric>`",
    u"`jpcrp_cor:KeyAuditMattersConsolidatedTextBlock`", u"`jpcrp_cor:KeyAuditMattersNonConsolidatedTextBlock`",
    u"切れない(decode)", u"切れない(札なし)", u"切れない(札が複数)", u"切れない(続きあり)", u"切れない(閉じない)", u"切れない(空)",
    u"`measure/xbrl_tanshin_2026-11-09.py` の `html_to_lines` で行にし、各行に NFKC を掛けて前後の空白を落とし、空の行を捨て、`\\n` でつないだもの。",
    u"NFKC を掛けたことは記録に書く。",
    u"`verify_document(元の ZIP の bytes, \"P33E\", text=文)`",
    u"連結の文と単体の文は**別々に** 1 回ずつ渡す。**数は連結と単体を足さない**",
    u"`random.Random(20261115).sample(range(行の数), 60)`",
    u"**AI の席**", u"**人は読まない**",
    u"pointer の字のどれかに `NonConsolidatedMember` を含む(真偽)",
    u"採用 / 不採用の判定は無い",
    u"**注入はこの便では測らない。**",
    u"`edinet` 67・`edinet-fresh-2026-10-21` 40・`edinet-prior-2026-11-02` 94",
    u"docID(cache の file 名)",
)
SEAL_TABLE_ROW = re.compile(r"^\| (\d+) \| (甲|乙|丙) \| `([0-9a-f]{64})` \| (切れた|札なし) \| (\d+|―) \| (切れた|札なし) \| (\d+|―) \|$", re.M)
#: §0-1 の 5 の表の行 (文の種類, 群, 本, 切れた本, 数の claim, GROUNDED, VALUE_MISMATCH, UNVERIFIABLE, POINTER_NOT_FOUND)
SEAL_FIVE_ROW = re.compile(r"^\s*\| \**(連結|単体)\** \| \**(甲|乙|丙|計)\** \| \**(\d+)\** \| \**(\d+)\** \| \**(\d+)\** \| \**(\d+)\** \| \**(\d+)\** \| \**(\d+)\** \| \**(\d+)\** \|$", re.M)
#: 封 §1 の表の 201 行(# TAB 群 TAB sha256 TAB 連結の切り出し TAB 連結の claim TAB 単体の切り出し TAB 単体の claim)の sha256。封の表の 1 字が変われば赤
TABLE_DIGEST = "ecaa541bb6638dd4cc0d7fadeb4ff426dab0b00b3d81313b9373a657eb824111"
CONS, NON = u"連結", u"単体"
#: 記録の字を門で縛る(script の字を写した。記録からは外さない。script の字が変われば赤)。限界は script の 8 行(封 §6 は 10 項目で字が違う。封の字は §6 に、記録の字はここに)
LIMITS_PINNED = (
    u"材料は過去の便で取った有報 201 本(提出者 108。同じ会社の 2 つの年度が入る)で、上場会社全体の標本ではない。本と本は独立でない(封 §6)",
    u"切れない本は測れていない。「札なし」が「KAM が無い」「連結財務諸表が無い」「札の付け方が違う」のどれかは分けない",
    u"engine は渡された文を経営者による分析の塊として読む。監査報告書の文であること・単体の文であることを知らない。単体の数は限界の記録で、成績ではない",
    u"文と fact が同じ誤りを共有していれば、この照合では見えない(同じ有報の中の照合)",
    u"KAM の数の多くは見積りの前提・一部分の残高で、fact の表に相手が無い。「見つからない」「止まった」が多いのはその形のため",
    u"NFKC を掛けた文を測っている(原文の全角・半角の違いは見ていない)",
    u"注入はしていないので、誤りを通す率は言えない",
    u"行は [文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む, pointer の字のどれかに NonConsolidatedMember を含む] だけで、文・span・値・要素名は持たない")
CUT_RECORD_PINNED = collections.OrderedDict([
    (u"member", u"名前に /AuditDoc/ を含み .htm で終わるもの(名前の順に utf-8 strict で全部読む)"),
    (u"札の名前", u"連結と単体で別(要素名は script の SIDES。長い英字なので記録には書かない)"),
    (u"始まりの規則", u'<ix:nonNumeric\\b[^>]*\\bname="%s"[^>]*>'), (u"深さの規則", u"<ix:nonNumeric\\b[^>]*?(/?)>|</ix:nonNumeric>"), (u"続きありの印", u"continuedAt"),
    (u"NFKC", True), (u"行にする関数", u"2026-11-09 の便の html_to_lines(呼ぶ)"), (u"切れない理由", [u"decode", u"札なし", u"札が複数", u"続きあり", u"閉じない", u"空"])])
JUDGE_RECORD_PINNED = collections.OrderedDict([
    (u"呼び方", u"verify_document(元の ZIP, P33E, text=文)。連結の文と単体の文は別々に 1 回ずつ。数は連結と単体を足さない"),
    (u"10 欄目", u"pointer の字のどれかに NonConsolidatedMember を含む(真偽)")])


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


def boom(*a, **k):
    raise AssertionError(u"ここへ来てはいけない(先に止まるはず)")


def eqp(out, label, got, want):
    if got != want:
        out.append(u"%s: 期待と違う" % label)


def expect_stop(out, label, fn):
    try:
        fn()
    except SystemExit:
        return
    out.append(u"%s: 止まらない" % label)


# ---------------------------------------------------------------- 1. 封の字
def seal_table(seal):
    u"""封 §1 の表 [(#, 群, sha256, 連結の切り出し(下見), 連結の claim(下見), 単体の切り出し(下見), 単体の claim(下見))]。"""
    try:
        sec = seal[seal.index(u"## §1"):seal.index(u"## §2")]
    except ValueError:
        return []
    return [(int(m[0]), m[1], m[2], m[3], m[4], m[5], m[6]) for m in SEAL_TABLE_ROW.findall(sec)]


def seal_five(seal):
    u"""§0-1 の 5 の表 {(文の種類, 群): (本, 切れた本, claim, G, VM, UNV, PNF)}。"""
    try:
        sec = seal[seal.index(u"### §0-1"):seal.index(u"### §0-2")]
    except ValueError:
        return {}
    return dict(((m[0], m[1]), tuple(int(x) for x in m[2:])) for m in SEAL_FIVE_ROW.findall(sec))


def seal_problems(seal):
    out = []
    try:
        sec2 = seal[seal.index(u"## §2"):seal.index(u"## §3")]
        sec3 = seal[seal.index(u"## §3"):seal.index(u"## §4")]
        sec5 = seal[seal.index(u"## §5"):seal.index(u"## §6")]
    except ValueError:
        return [u"封の節(§1〜§6)が揃っていない"]
    rows = seal_table(seal)
    if len(rows) != 201:
        out.append(u"封 §1 の表が 201 行でない: %d" % len(rows))
    if hashlib.sha256(u"\n".join(u"\t".join(str(c) for c in r) for r in rows).encode("utf-8")).hexdigest() != TABLE_DIGEST:
        out.append(u"封 §1 の表の字が、門に留めた sha256 と違う")
    if [r[0] for r in rows] != list(range(1, len(rows) + 1)):
        out.append(u"封 §1 の表の # が 1 から続いていない")
    if len(set(r[2] for r in rows)) != len(rows):
        out.append(u"封 §1 の表の sha256 に重複がある")
    g = collections.Counter(r[1] for r in rows)
    if [g[x] for x in (u"甲", u"乙", u"丙")] != [67, 40, 94]:
        out.append(u"封 §1 の群が 甲 67・乙 40・丙 94 でない")
    order = [(u"甲乙丙".index(r[1]), r[2]) for r in rows]
    if order != sorted(order):
        out.append(u"封 §1 の並びが 群 → sha256 の順でない")
    for r in rows:
        for cut, n in ((r[3], r[4]), (r[5], r[6])):
            if (cut == u"切れた") != n.isdigit():
                out.append(u"封 §1 の # %d の下見の切れ方と claim が合わない" % r[0])
    five = seal_five(seal)
    if len(five) != 8:
        out.append(u"封 §0-1 の 5 の表が 8 行(連結・単体 × 甲・乙・丙・計)でない: %d" % len(five))
    for side, ci, ni in ((CONS, 3, 4), (NON, 5, 6)):
        for grp in (u"甲", u"乙", u"丙", u"計"):
            sub = [r for r in rows if grp == u"計" or r[1] == grp]
            cut = [r for r in sub if r[ci] == u"切れた"]
            got = (len(sub), len(cut), sum(int(r[ni]) for r in cut if r[ni].isdigit()))
            want = five.get((side, grp))
            if want is None or (want[0], want[1], want[2]) != got:
                out.append(u"封 §0-1 の 5 の表(%s %s)が §1 の下見の列の数と違う" % (side, grp))
            if want is not None and sum(want[3:]) != want[2]:
                out.append(u"封 §0-1 の 5 の表(%s %s)の 4 state の合計が claim と違う" % (side, grp))
    if (five.get((CONS, u"計")), five.get((NON, u"計"))) != ((201, 151, 480, 136, 29, 72, 243), (201, 192, 308, 36, 8, 50, 214)):
        out.append(u"封 §0-1 の 5 の計の行が K-3・K-4 の数と違う")
    ids = re.findall(r"^\| (K-\d+) \| (.*) \|$", sec3, re.M)
    if [i[0] for i in ids] != list(PRED_IDS):
        out.append(u"封 §3 の表が K-1〜K-11 の 11 行でない: %s" % [i[0] for i in ids])
    for k, rest in ids:
        cells = rest.split(u" | ")
        if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
            out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % k)
    if SCRIPT_REL not in sec5:
        out.append(u"封 §5 に script の path が無い: %s" % SCRIPT_REL)
    for rel in (u"test_xbrl_kam_seal.py", u"test_xbrl_kam_result.py"):
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
def script_problems(seal, ms=None):
    u"""封の字と script の定数が同じか。ms = script の module(試験が壊した写しを渡す)。"""
    ms = ms or MS
    out = []
    try:
        seal02 = seal[seal.index(u"### §0-2"):seal.index(u"## §1")]                  # 規則を決めた節(§0-1 の下見の説明に同じ字が在っても、規則の節の字を見る)
    except ValueError:
        return [u"封の節(§0-2・§1)が揃っていない"]
    want = [(r[0], r[1], r[2]) for r in seal_table(seal)]
    if list(ms.population_from_text(seal)) != want:
        out.append(u"script が封の表と別の行を読む")
    if ms.ST is not ms.TSS.ST or ms.TS is not ms.TSS.TS or ms.Stop is not ms.ST.Stop:
        out.append(u"script が前の便の script と別の instance を使っている")
    if ms.SEAL_REL != SEAL_REL or ms.SEAL_COMMIT != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if ms.SCRIPT_REL != SCRIPT_REL or ms.DOC_REL != DOC_REL:
        out.append(u"script・結果の文書の path が封 §5 と違う")
    if (ms.POPULATION_REL, ms.STATES_REL, ms.TYPES_REL) != RECORD_RELS:
        out.append(u"記録の path が封 §2 と違う")
    if ms.N_ROWS != 201 or list(ms.GROUP_COUNTS.items()) != [(u"甲", 67), (u"乙", 40), (u"丙", 94)]:
        out.append(u"母集団の本数・群の本数が封 §0-1 の 1・§1 と違う")
    if list(ms.CACHES.items()) != [(u"甲", "edinet"), (u"乙", "edinet-fresh-2026-10-21"), (u"丙", "edinet-prior-2026-11-02")]:
        out.append(u"群と cache の folder が封 §0-1 の 1・2 と違う")
    if list(ms.SIDES) != [u"連結", u"単体"] or ms.SIDES[u"連結"] != "jpcrp_cor:KeyAuditMattersConsolidatedTextBlock" or ms.SIDES[u"単体"] != "jpcrp_cor:KeyAuditMattersNonConsolidatedTextBlock":
        out.append(u"札の名前が封 §0-2 の 3 と違う")
    for nm in ms.SIDES.values():
        if u"`%s`" % nm not in seal02:
            out.append(u"札の名前が封 §0-2 に無い: %s" % nm)
    if (ms.AUDIT_MARK, ms.AUDIT_SUFFIX) != ("/AuditDoc/", ".htm"):
        out.append(u"AuditDoc の member の決め方が封 §0-2 の 3 と違う")
    if ms.START_RE.replace(u"%s", u"<札の名前>") not in seal02 or ms.DEPTH_RE.pattern not in seal02:
        out.append(u"切り出しの正規表現が封の字と違う")
    if ms.CONTINUED != "continuedAt" or ms.NONCONSOLIDATED_MARK != "NonConsolidatedMember":
        out.append(u"続きありの印・10 欄目の印が封と違う")
    if ms.WHYS != (u"decode", u"札なし", u"札が複数", u"続きあり", u"閉じない", u"空") or (ms.CUT_OK, ms.CUT_NG) != (u"切れた", u"切れない"):
        out.append(u"切れない理由の字が封 §0-2 の 3 と違う")
    if (ms.WHY_DECODE, ms.WHY_NOTAG, ms.WHY_MANY, ms.WHY_CONT, ms.WHY_OPEN, ms.WHY_EMPTY) != tuple(ms.WHYS):
        out.append(u"切れない理由の字と並びが一致しない")
    for w in ms.WHYS:
        if u"切れない(%s)" % w not in seal02:
            out.append(u"切れない理由が封 §0-2 に無い: %s" % w)
    if ms.PROFILE != "P33E":
        out.append(u"profile が P33E でない")
    if (ms.READ_SEED, ms.READ_N) != (20261115, 60):
        out.append(u"G 連結の引き方(種・本数)が封 §0-2 の 7 と違う")
    if list(ms.READ_SETS.items()) != [(u"V 連結", (u"連結", u"VALUE_MISMATCH", False)), (u"V 単体", (u"単体", u"VALUE_MISMATCH", False)),
                                      (u"G 連結", (u"連結", u"GROUNDED", True)), (u"G 単体", (u"単体", u"GROUNDED", False))]:
        out.append(u"読みの組が封 §0-2 の 7 と違う")
    if list(ms.TYPES_V) != list(u"アイウエオカキクケ") or list(ms.TYPES_G) != [u"a", u"b", u"c"] or tuple(ms.DIFFS) != (u"項目", u"範囲", u"側", u"期") or ms.DIFF_TYPE != u"b":
        out.append(u"型・違うものの字の並びが封 §0-2 の 7 と違う")
    flat = seal.replace(u"**", u"")
    for k, v in list(ms.TYPES_V.items()) + list(ms.TYPES_G.items()):
        if u"(%s) %s" % (k, v) not in flat:
            out.append(u"型 (%s) の字が封 §0-2 の 7 と違う" % k)
    if u"AI の席" not in ms.TYPED_BY or u"人は読んでいない" not in ms.TYPED_BY:
        out.append(u"型を付けた席の字が封 §0-2 の 7 と違う")
    if len(ms.ROW_COLUMNS) != 10 or tuple(ms.ROW_COLUMNS[:9]) != tuple(TSS.ROW_COLUMNS) or u"NonConsolidatedMember" not in ms.ROW_COLUMNS[9]:
        out.append(u"行の欄が封 §2 の 2(9 欄 + 10 欄目)と違う")
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
ORDER_FILES = (SCRIPT_REL, GATE_REL)


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(ORDER_FILES) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 7. 配線・名前・docID・通信
#: 前の便・置く script の関数(script は同名の関数を定義せず、module の関数を呼ぶ)。(module の別名, 関数名)
REUSED_FUNCS = (("TS", "html_to_lines"), ("TS", "profile_rows"), ("TS", "row_entry"), ("TS", "state_counts"), ("TS", "reason_counts"), ("TS", "vm_breakdown"), ("TS", "dumps_states"),
                ("TS.NF", "map_pool"), ("TS.RUN", "sentence_list"), ("TSS", "pick_sample"), ("TSS", "inside_repo"), ("TSS", "load_json"),
                ("ST", "write_text_exclusive"), ("ST", "dumps_record"), ("ST", "key_leaks"), ("ST", "sha256_file"), ("ST", "sha256_bytes"),
                ("ST", "names_snapshot"), ("ST", "git_head"), ("ST", "cache_base"))


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
    u"""script が前の便・置く script の関数を呼ぶ(同名の関数を定義しない)。"""
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
    u"""script が通信の module を import しない(``import`` 文を ast で見る)。"""
    path = path or os.path.join(ROOT, SCRIPT_REL)
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


def name_problems(rels=(SCRIPT_REL, GATE_REL), base=ROOT, codes=None, shas=None):
    u"""新しい file に docID・TDnet の番号・2026-11-09 の便の証券コード・番号・封の表の sha256 が無い。"""
    codes = codes if codes is not None else [r[1] for r in TS.FE.TABLE] + [r[2] for r in TS.FE.TABLE]
    shas = shas if shas is not None else [r[2] for r in seal_table(read(SEAL_REL))]
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
        if any(s in src for s in shas):
            out.append(u"%s に封の表の sha256 が写してある(表は封の file から読む)" % rel)
    return out


# ================================================================ 材料の作り物(本物の engine が読む形。会社の字は無い)
def _ctx(cid, member, s, e):
    seg = (u'<xbrli:segment><xbrldi:explicitMember dimension="jpcrp_cor:ConsolidatedOrNonConsolidatedAxis">jpcrp_cor:NonConsolidatedMember</xbrldi:explicitMember></xbrli:segment>'
           if member else u"")
    return (u'<xbrli:context id="%s"><xbrli:entity><xbrli:identifier scheme="http://x">1</xbrli:identifier>%s</xbrli:entity>'
            u'<xbrli:period><xbrli:startDate>%s</xbrli:startDate><xbrli:endDate>%s</xbrli:endDate></xbrli:period></xbrli:context>') % (cid, seg, s, e)


def xbrl_instance(consolidated=True, nonconsolidated=True):
    u"""作り物の .xbrl(売上高だけ。連結の枠: 当期 1,234 百万・前期 1,000 百万・単体の枠: 当期 900 百万・前期 800 百万)と経営者による分析の塊。"""
    ctxs, facts = [], []
    if consolidated:
        ctxs += [_ctx("CurrentYearDuration", False, "2025-04-01", "2026-03-31"), _ctx("Prior1YearDuration", False, "2024-04-01", "2025-03-31")]
        facts += [u'<jppfs_cor:NetSales contextRef="CurrentYearDuration" unitRef="JPY" decimals="-6">1234000000</jppfs_cor:NetSales>',
                  u'<jppfs_cor:NetSales contextRef="Prior1YearDuration" unitRef="JPY" decimals="-6">1000000000</jppfs_cor:NetSales>']
    if nonconsolidated:
        ctxs += [_ctx("CurrentYearDuration_NonConsolidatedMember", True, "2025-04-01", "2026-03-31"), _ctx("Prior1YearDuration_NonConsolidatedMember", True, "2024-04-01", "2025-03-31")]
        facts += [u'<jppfs_cor:NetSales contextRef="CurrentYearDuration_NonConsolidatedMember" unitRef="JPY" decimals="-6">900000000</jppfs_cor:NetSales>',
                  u'<jppfs_cor:NetSales contextRef="Prior1YearDuration_NonConsolidatedMember" unitRef="JPY" decimals="-6">800000000</jppfs_cor:NetSales>']
    md = (u'<jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock contextRef="FilingDateInstant">%s'
          u'</jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock>') % escape(u"<p>経営者の文です。</p>")
    return (u'<?xml version="1.0" encoding="utf-8"?><xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi" '
            u'xmlns:jppfs_cor="http://example.org/jppfs" xmlns:jpcrp_cor="http://example.org/jpcrp" xmlns:iso4217="http://www.xbrl.org/2003/iso4217">'
            + u"".join(ctxs) + u'<xbrli:unit id="JPY"><xbrli:measure>iso4217:JPY</xbrli:measure></xbrli:unit>' + u"".join(facts) + md + u"</xbrli:xbrl>")


def tag(name, inner, extra=u""):
    return u'<ix:nonNumeric name="%s" contextRef="CurrentYearDuration"%s escape="true">%s</ix:nonNumeric>' % (name, extra, inner)


def page(*parts):
    return (u"<html><body>" + u"".join(parts) + u"</body></html>").encode("utf-8")


def make_zip(members):
    u"""[(名前, bytes)] から ZIP の bytes(作り物。材料ではない)。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in members:
            z.writestr(n, b)
    return buf.getvalue()


CONS_NAME, NON_NAME = MS.SIDES[CONS], MS.SIDES[NON]
INNER_NAME = "jpcrp_cor:DescriptionIncludingReasonKeyAuditMattersConsolidatedTextBlock"
C_TEXT = u"<p>見出し</p><p>売上高は1,300百万円となりました。</p><p>売上高は1,234百万円となりました。</p>"
N_TEXT = u"<p>売上高は900百万円となりました。</p><p>売上高は1,300百万円となりました。</p>"


def kam_zip(cons=C_TEXT, non=N_TEXT, instance=None, tag_no=b"", audit=True, **kw):
    u"""作り物の有報の ZIP。``cons``・``non`` が None ならその札を入れない。``audit`` が偽なら監査報告書の file を入れない。"""
    m = [("XBRL/PublicDoc/0000000-asr-001.xbrl", (instance if instance is not None else xbrl_instance(**kw)).encode("utf-8"))]
    if audit:
        parts = []
        if cons is not None:
            parts.append(tag(CONS_NAME, cons))
        if non is not None:
            parts.append(tag(NON_NAME, non))
        m.append(("XBRL/AuditDoc/0100010-aar-cc.htm", page(*parts)))
    if tag_no:
        m.append(("XBRL/PublicDoc/zz-note.txt", tag_no))
    return make_zip(m)


def audit_zip(files, extra=()):
    u"""AuditDoc の file だけを持つ ZIP(切り出しの試験用)。files = [(名前, bytes)]。"""
    return make_zip(list(files) + list(extra))


# ================================================================ 振る舞いの検査(``*_problems`` は問題の字の列を返す。変異した版でも呼べるよう、module の名前で引く)
def cut_problems():
    u"""切り出し(封 §0-2 の 3)の当たる例・当たらない例・最初の一致・札が複数・続きあり・閉じない・空・decode・member の選び方・深さ・NFKC。"""
    out = []
    K = MS.cut_kam
    AD = "XBRL/AuditDoc/a.htm"

    def one(label, files, side, want, extra=()):
        eqp(out, label, K(audit_zip(files, extra), side), want)

    one(u"基本(連結)", [(AD, page(u"<p>前置き</p>", tag(CONS_NAME, u"<p>見出し</p><p>本文１２３</p>"), u"<p>後ろ</p>"))], CONS, (u"見出し\n本文123", None))
    one(u"基本(単体)", [(AD, page(u"<p>前置き</p>", tag(NON_NAME, u"<p>単体の本文</p>"), u"<p>後ろ</p>"))], NON, (u"単体の本文", None))
    one(u"連結の札を単体の名前で探さない", [(AD, page(tag(CONS_NAME, u"<p>連結</p>")))], NON, (None, MS.WHY_NOTAG))
    one(u"単体の札を連結の名前で探さない", [(AD, page(tag(NON_NAME, u"<p>単体</p>")))], CONS, (None, MS.WHY_NOTAG))
    one(u"入れ子の札だけ(内容及び決定理由)には当たらない", [(AD, page(tag(INNER_NAME, u"<p>内容</p>")))], CONS, (None, MS.WHY_NOTAG))
    one(u"札の名前が完全一致でなければ当たらない", [(AD, page(tag(CONS_NAME + "X", u"<p>x</p>")))], CONS, (None, MS.WHY_NOTAG))
    one(u"name の前に字が付く属性(xname)には当たらない", [(AD, page(u'<ix:nonNumeric contextRef="c" xname="%s" escape="true"><p>x</p></ix:nonNumeric>' % CONS_NAME))], CONS, (None, MS.WHY_NOTAG))
    one(u"name が最初の属性でなくても当たる", [(AD, page(u'<ix:nonNumeric contextRef="c" name="%s" escape="true"><p>属性の順</p></ix:nonNumeric>' % CONS_NAME))], CONS, (u"属性の順", None))
    one(u"入れ子の札の後ろの字も塊に入る", [(AD, page(tag(CONS_NAME, u"<p>見出し</p>" + tag(INNER_NAME, u"<p>内容</p>") + u"<p>後続</p>"), u"<p>外</p>"))], CONS, (u"見出し\n内容\n後続", None))
    one(u"二重の入れ子", [(AD, page(tag(CONS_NAME, u"<p>a</p>" + tag(INNER_NAME, u"<p>b</p>" + tag(INNER_NAME, u"<p>c</p>") + u"<p>d</p>") + u"<p>e</p>"), u"<p>外</p>"))], CONS,
        (u"a\nb\nc\nd\ne", None))
    one(u"自分で閉じる札は深さを増やさない", [(AD, page(tag(CONS_NAME, u"<p>a</p><ix:nonNumeric name=\"x\" contextRef=\"c\"/><p>b</p>"), u"<p>外</p>"))], CONS, (u"a\nb", None))
    one(u"属性に / を含む入れ子の開く札は深さを増やす(自分で閉じる札ではない)", [(AD, page(tag(CONS_NAME, u"<p>a</p>" + tag(INNER_NAME, u"<p>b</p>", u' format="ixt:a/b"') + u"<p>c</p>"), u"<p>外</p>"))], CONS,
        (u"a\nb\nc", None))
    one(u"属性に / を含み自分で閉じる札は深さを増やさない", [(AD, page(tag(CONS_NAME, u"<p>a</p><ix:nonNumeric name=\"x\" format=\"ixt:a/b\" contextRef=\"c\"/><p>b</p>"), u"<p>外</p>"))], CONS, (u"a\nb", None))
    one(u"最初の一致だけ使う(同じ file に 2 つ)", [(AD, page(tag(CONS_NAME, u"<p>先</p>"), tag(CONS_NAME, u"<p>後</p>")))], CONS, (u"先", None))
    one(u"札が複数(2 つの file)", [(AD, page(tag(CONS_NAME, u"<p>先</p>"))), ("XBRL/AuditDoc/b.htm", page(tag(CONS_NAME, u"<p>後</p>")))], CONS, (None, MS.WHY_MANY))
    one(u"続きあり", [(AD, page(u'<ix:nonNumeric name="%s" contextRef="c" continuedAt="k1" escape="true"><p>x</p></ix:nonNumeric>' % CONS_NAME))], CONS, (None, MS.WHY_CONT))
    one(u"続きありは始まりの札だけを見る", [(AD, page(tag(CONS_NAME, u'<p>x</p><ix:nonNumeric name="y" continuedAt="k1"><p>z</p></ix:nonNumeric>')))], CONS, (u"x\nz", None))
    one(u"閉じない", [(AD, u'<html><body><ix:nonNumeric name="%s" contextRef="c"><p>x</p></body></html>'.replace(u"%s", CONS_NAME).encode("utf-8"))], CONS, (None, MS.WHY_OPEN))
    one(u"閉じない(入れ子の分だけ閉じる札が足りない)", [(AD, u'<html><body><ix:nonNumeric name="%s"><p>x</p><ix:nonNumeric name="y"><p>z</p></ix:nonNumeric></body></html>'.replace(u"%s", CONS_NAME).encode("utf-8"))],
        CONS, (None, MS.WHY_OPEN))
    one(u"空", [(AD, page(tag(CONS_NAME, u"<p> </p><br/>　")))], CONS, (None, MS.WHY_EMPTY))
    one(u"札の無い file は札なし", [(AD, page(u"<p>x</p>"))], CONS, (None, MS.WHY_NOTAG))
    one(u"AuditDoc の file が無ければ札なし", [], CONS, (None, MS.WHY_NOTAG), extra=[("XBRL/PublicDoc/a.htm", page(tag(CONS_NAME, u"<p>x</p>")))])
    one(u"PublicDoc の札は読まない", [(AD, page(u"<p>x</p>"))], CONS, (None, MS.WHY_NOTAG), extra=[("XBRL/PublicDoc/a.htm", page(tag(CONS_NAME, u"<p>x</p>")))])
    one(u".html で終わる file は読まない", [("XBRL/AuditDoc/a.html", page(tag(CONS_NAME, u"<p>x</p>")))], CONS, (None, MS.WHY_NOTAG))
    one(u"/AuditDoc/ を含まない名前は読まない", [("AuditDoc/a.htm", page(tag(CONS_NAME, u"<p>x</p>")))], CONS, (None, MS.WHY_NOTAG))
    one(u"名前に /AuditDoc/ を含めば読む(深い所)", [("top/XBRL/AuditDoc/a.htm", page(tag(CONS_NAME, u"<p>x</p>")))], CONS, (u"x", None))
    one(u"札の在る file が 1 つでも decode できなければ decode(あとの名前)", [(AD, page(tag(CONS_NAME, u"<p>x</p>"))), ("XBRL/AuditDoc/z.htm", b"\xff\xfe<p>x</p>")], CONS, (None, MS.WHY_DECODE))
    one(u"札の在る file が 1 つでも decode できなければ decode(まえの名前)", [("XBRL/AuditDoc/0.htm", b"\xff\xfe<p>x</p>"), (AD, page(tag(CONS_NAME, u"<p>x</p>")))], CONS, (None, MS.WHY_DECODE))
    one(u"AuditDoc の外の decode できない file は見ない", [(AD, page(tag(CONS_NAME, u"<p>x</p>")))], CONS, (u"x", None), extra=[("XBRL/PublicDoc/z.htm", b"\xff\xfe"), ("XBRL/AuditDoc/z.txt", b"\xff\xfe")])
    one(u"NFKC・前後の空白・空の行", [(AD, page(tag(CONS_NAME, u"<p>  ＡＢＣ　１，２３４百万円(注)  </p><p> </p><p>２０２６年</p>")))], CONS, (u"ABC 1,234百万円(注)\n2026年", None))
    calls = []
    real = MS.TS.html_to_lines

    def spy(h):
        calls.append(h)
        return [u"  A  ", u" ", u"b"]
    with patched(MS.TS, html_to_lines=spy):
        got = K(audit_zip([(AD, page(tag(CONS_NAME, u"<p>zzz</p>")))]), CONS)
    eqp(out, u"html_to_lines を呼ぶ(塊の字だけ渡す)・NFKC・空の行を捨てる", (got, calls), ((u"A\nb", None), [u"<p>zzz</p>"]))
    if MS.TS.html_to_lines is not real:
        out.append(u"html_to_lines が戻っていない")
    expect_stop(out, u"ZIP でない bytes", lambda: K(b"not a zip", CONS))
    return out


def row10_problems():
    u"""10 欄目: pointer の字のどれかに NonConsolidatedMember を含む。formula の pointer・文字でない pointer も扱える。"""
    out = []
    key = (3, 7)

    def mk(ptrs):
        return (u"GROUNDED", None, tuple(ptrs), u"円族", False)
    eqp(out, u"含まない", MS.row10(key, mk([u"xbrl:jppfs_cor:NetSales@CurrentYearDuration"])), [3, 7, u"GROUNDED", None, u"CurrentYear", False, u"円族", False, False, False])
    eqp(out, u"含む", MS.row10(key, mk([u"xbrl:jppfs_cor:NetSales@CurrentYearDuration_NonConsolidatedMember"]))[9], True)
    eqp(out, u"2 つのうち 2 つ目だけ含む", MS.row10(key, mk([u"xbrl:a@CurrentYearDuration", u"xbrl:b@Prior1YearDuration_NonConsolidatedMember"]))[9], True)
    eqp(out, u"含まない(ConsolidatedMember の字だけ)", MS.row10(key, mk([u"xbrl:a@CurrentYearDuration_ConsolidatedMember"]))[9], False)
    eqp(out, u"pointer が無い", MS.row10(key, mk([]))[9], False)
    eqp(out, u"formula の pointer", MS.row10(key, mk([u"formula:a-b", u"xbrl:a@CurrentYearDuration_NonConsolidatedMember"]))[9], True)
    eqp(out, u"9 欄は row_entry と同じ", MS.row10(key, mk([u"xbrl:a@CurrentYearDuration"]))[:9], TS.row_entry(key, mk([u"xbrl:a@CurrentYearDuration"])))
    eqp(out, u"真偽は bool", type(MS.row10(key, mk([u"xbrl:a@x_NonConsolidatedMember"]))[9]), bool)
    return out


# 本物の engine で判定した行(作り物の材料。独立に決めた期待値: 連結の枠は売上高 1,234 百万円・単体の枠は 900 百万円)
ROWS_A_CONS = [[1, 4, u"VALUE_MISMATCH", None, u"CurrentYear", False, u"円族", False, False, False], [2, 4, u"GROUNDED", None, u"CurrentYear", False, u"円族", False, False, False]]
ROWS_A_NON = [[0, 4, u"UNVERIFIABLE", u"other_frame", u"なし", False, u"円族", False, False, False], [1, 4, u"VALUE_MISMATCH", None, u"CurrentYear", False, u"円族", False, False, False]]
ROWS_B_CONS = [[1, 4, u"POINTER_NOT_FOUND", u"no_same_value", u"なし", False, u"円族", False, False, False], [2, 4, u"POINTER_NOT_FOUND", u"no_same_value", u"なし", False, u"円族", False, False, False]]
ROWS_B_NON = [[0, 4, u"GROUNDED", None, u"CurrentYear", False, u"円族", False, False, True], [1, 4, u"POINTER_NOT_FOUND", u"no_same_value", u"なし", False, u"円族", False, False, False]]


def judge_problems():
    u"""判定の配線: ``judge_book`` の記録の形・``profile_rows`` を P33E・元の ZIP と文を渡す・連結と単体は別々・切れない側は行を持たない・10 欄目。"""
    out = []
    sha = u"a" * 64
    za = kam_zip()
    b = MS.judge_book(1, u"甲", sha, za)
    want = collections.OrderedDict([
        (u"#", 1), (u"群", u"甲"), (u"ZIP の sha256", sha),
        (u"連結", collections.OrderedDict([(u"切り出し", u"切れた"), (u"理由", None), (u"字数", len(u"見出し\n売上高は1,300百万円となりました。\n売上高は1,234百万円となりました。")), (u"claim", 2), (u"対応", True), (u"行", ROWS_A_CONS)])),
        (u"単体", collections.OrderedDict([(u"切り出し", u"切れた"), (u"理由", None), (u"字数", len(u"売上高は900百万円となりました。\n売上高は1,300百万円となりました。")), (u"claim", 2), (u"対応", True), (u"行", ROWS_A_NON)]))])
    eqp(out, u"切れた本の記録", json.loads(json.dumps(b)), json.loads(json.dumps(want)))
    eqp(out, u"欄の順", (list(b), list(b[u"連結"])), ([u"#", u"群", u"ZIP の sha256", u"連結", u"単体"], [u"切り出し", u"理由", u"字数", u"claim", u"対応", u"行"]))
    bb = MS.judge_book(2, u"乙", sha, kam_zip(consolidated=False))
    eqp(out, u"連結の枠が無い本(単体の枠だけ結べる。10 欄目が真)", ([r for r in bb[u"連結"][u"行"]], [r for r in bb[u"単体"][u"行"]]), (ROWS_B_CONS, ROWS_B_NON))
    c = MS.judge_book(3, u"丙", sha, kam_zip(cons=None, non=None, audit=False))
    cut_ng = lambda why: collections.OrderedDict([(u"切り出し", u"切れない"), (u"理由", why), (u"字数", None), (u"claim", 0), (u"対応", None), (u"行", [])])
    eqp(out, u"切れない本の記録", json.loads(json.dumps(c)), json.loads(json.dumps(collections.OrderedDict([(u"#", 3), (u"群", u"丙"), (u"ZIP の sha256", sha), (u"連結", cut_ng(u"札なし")), (u"単体", cut_ng(u"札なし"))]))))
    d = MS.judge_book(4, u"丙", sha, kam_zip(cons=u"<p>数はありません。</p>", non=None))
    eqp(out, u"連結だけ切れた本(claim 0)・単体は札なし", (d[u"連結"][u"切り出し"], d[u"連結"][u"claim"], d[u"連結"][u"行"], d[u"単体"][u"理由"]), (u"切れた", 0, [], u"札なし"))
    real0 = MS.TS.profile_rows
    with patched(MS.TS, profile_rows=lambda zb, text, zm, pname: (lambda r: (r[0], False, r[2]))(real0(zb, text, zm, pname))):
        w = MS.judge_book(1, u"甲", sha, za)
    eqp(out, u"claim と raw の並びが対応しなければ 対応 が偽", (w[u"連結"][u"対応"], w[u"単体"][u"対応"]), (False, False))
    eqp(out, u"対応が真の本", (b[u"連結"][u"対応"], b[u"単体"][u"対応"]), (True, True))
    seen = []
    real = MS.TS.profile_rows

    def spy(zb, text, zm, pname):
        seen.append((zb is za, text, pname, zm is not zb, zipfile.ZipFile(io.BytesIO(zm)).namelist()))
        return real(zb, text, zm, pname)
    with patched(MS.TS, profile_rows=spy):
        MS.judge_book(1, u"甲", sha, za)
    eqp(out, u"profile_rows に 元の ZIP・その側の文・P33E・差し替えた ZIP(memory)を連結 → 単体の順で渡す",
        [(s[0], s[1], s[2], s[3]) for s in seen],
        [(True, u"見出し\n売上高は1,300百万円となりました。\n売上高は1,234百万円となりました。", u"P33E", True), (True, u"売上高は900百万円となりました。\n売上高は1,300百万円となりました。", u"P33E", True)])
    if seen:
        eqp(out, u"差し替えた ZIP は元の member を持つ", seen[0][4], zipfile.ZipFile(io.BytesIO(za)).namelist())
    return out


# ---------------------------------------------------------------- 材料の置き場・母集団・states・紙・型
def fixture_books():
    u"""作り物の 4 本: 甲(両方の枠・連結と単体が切れる)・乙(連結の枠が無い)・丙(監査報告書が無い)・丙(連結だけ切れて数が無い)。"""
    return [(u"甲", kam_zip(tag_no=b"1")), (u"乙", kam_zip(consolidated=False, tag_no=b"2")), (u"丙", kam_zip(cons=None, non=None, audit=False, tag_no=b"3")),
            (u"丙", kam_zip(cons=u"<p>数はありません。</p>", non=None, tag_no=b"4"))]


SHAPE4 = (4, collections.OrderedDict([(u"甲", 1), (u"乙", 1), (u"丙", 2)]))
SHAPE3 = (3, collections.OrderedDict([(u"甲", 1), (u"乙", 1), (u"丙", 1)]))


def states_fixture(d):
    u"""d の下に cache の根(3 つの folder)と root を作る。材料は 4 本。表は 群 → sha256 の順。(表, cache の根, root, 表の順の ZIP の bytes)。"""
    items = [(g, hashlib.sha256(z).hexdigest(), z) for g, z in fixture_books()]
    items.sort(key=lambda t: (u"甲乙丙".index(t[0]), t[1]))
    pop = [(i + 1, g, s) for i, (g, s, _z) in enumerate(items)]
    base = os.path.join(d, "base")
    for g, f in MS.CACHES.items():
        os.makedirs(os.path.join(base, f))
    for i, (g, s, z) in enumerate(items):
        with open(os.path.join(base, MS.CACHES[g], "m%d.zip" % i), "wb") as fh:
            fh.write(z)
    with open(os.path.join(base, MS.CACHES[u"甲"], "other.zip"), "wb") as fh:                   # 表に無い ZIP
        fh.write(kam_zip(tag_no=b"not in the table"))
    with open(os.path.join(base, MS.CACHES[u"乙"], "note.txt"), "wb") as fh:                    # zip でない file
        fh.write(items[0][2])
    os.makedirs(os.path.join(base, "other-folder"))                                            # 3 つの外の folder(読まない)
    with open(os.path.join(base, "other-folder", "x.zip"), "wb") as fh:
        fh.write(items[0][2])
    root = os.path.join(d, "root")
    os.makedirs(os.path.join(root, "docs"))
    shutil.copyfile(os.path.join(ROOT, SEAL_REL), os.path.join(root, SEAL_REL))                  # 封の表の sha256 を記録に書くので、封の写しを置く
    return pop, base, root, [z for _g, _s, z in items]


def tree_listing(folder):
    out = []
    for dp, dn, fn in os.walk(folder):
        for f in fn:
            p = os.path.join(dp, f)
            out.append((os.path.relpath(p, folder), os.stat(p).st_size, os.stat(p).st_mtime_ns))
    return sorted(out)


def strip_time(text):
    return re.sub(r'^ *"時間\(秒\)": .*$', u"", text, flags=re.M)


def recount(books, side):
    u"""集計を、記録の ``行`` から別の書き方で数え直す(script の ``block`` を使わない)。"""
    sides = [b[side] for b in books]
    cut = [s for s in sides if s[u"切り出し"] == u"切れた"]
    rows = [r for s in cut for r in s[u"行"]]
    st = collections.Counter(r[2] for r in rows)
    return collections.OrderedDict([
        (u"本", len(sides)), (u"切れた", len(cut)), (u"切れない", len(sides) - len(cut)), (u"字数の合計", sum(s[u"字数"] for s in cut)), (u"claim", len(rows)),
        (u"4 state", [st.get(k, 0) for k in (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")]),
        (u"claim が 0", sum(1 for s in cut if not s[u"行"])), (u"GROUNDED が 0", sum(1 for s in cut if not any(r[2] == u"GROUNDED" for r in s[u"行"]))),
        (u"VALUE_MISMATCH が 1 以上", sum(1 for s in cut if any(r[2] == u"VALUE_MISMATCH" for r in s[u"行"]))),
        (u"10 欄目が真の GROUNDED / 偽の GROUNDED", [sum(1 for r in rows if r[2] == u"GROUNDED" and r[9]), sum(1 for r in rows if r[2] == u"GROUNDED" and not r[9])]),
        (u"10 欄目が真の VALUE_MISMATCH / 偽の VALUE_MISMATCH", [sum(1 for r in rows if r[2] == u"VALUE_MISMATCH" and r[9]), sum(1 for r in rows if r[2] == u"VALUE_MISMATCH" and not r[9])]),
        (u"切れない理由", sorted(collections.Counter(s[u"理由"] for s in sides if s[u"切り出し"] == u"切れない").items()))])


def counted(block):
    k = u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む)の数"
    return collections.OrderedDict([
        (u"本", block[u"本"]), (u"切れた", block[u"切れた"]), (u"切れない", block[u"切れない"]), (u"字数の合計", block[u"字数の合計"]), (u"claim", block[u"claim"]),
        (u"4 state", [block[u"4 state"][s] for s in (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")]),
        (u"claim が 0", block[u"切れた本のうち claim が 0 の本"]), (u"GROUNDED が 0", block[u"切れた本のうち GROUNDED が 0 の本"]),
        (u"VALUE_MISMATCH が 1 以上", block[u"VALUE_MISMATCH が 1 以上の本"]),
        (u"10 欄目が真の GROUNDED / 偽の GROUNDED", [block[k][u"GROUNDED"][u"真"], block[k][u"GROUNDED"][u"偽"]]),
        (u"10 欄目が真の VALUE_MISMATCH / 偽の VALUE_MISMATCH", [block[k][u"VALUE_MISMATCH"][u"真"], block[k][u"VALUE_MISMATCH"][u"偽"]]),
        (u"切れない理由", sorted((w, n) for w, n in block[u"切れない理由"].items() if n))])


def scan_problems():
    u"""材料を探す: 表に在る ZIP だけ選ぶ・byte 数・欠け・重なり・群違い・folder の外は読まない・file 名は返り値の path の中だけ。"""
    out = []
    with tmpdir() as d:
        pop, base, root, zips = states_fixture(d)
        got = MS.scan_material(base, pop)
        eqp(out, u"表に在る ZIP だけ選ぶ", sorted(got), sorted(r[2] for r in pop))
        eqp(out, u"byte 数", [got[r[2]][1] for r in pop], [len(z) for z in zips])
        eqp(out, u"path が各 folder の下", [os.path.dirname(got[r[2]][0]) == os.path.join(base, MS.CACHES[r[1]]) for r in pop], [True] * 4)
        # 表に在る ZIP が 1 本欠ける
        os.remove(got[pop[1][2]][0])
        expect_stop(out, u"1 本欠ける", lambda: MS.scan_material(base, pop))
        # 同じ sha256 が 2 か所
        with open(got[pop[1][2]][0], "wb") as fh:
            fh.write(zips[1])
        with open(os.path.join(base, MS.CACHES[u"甲"], "dup.zip"), "wb") as fh:                   # 同じ群の folder に同じ ZIP
            fh.write(zips[0])
        expect_stop(out, u"同じ sha256 が 2 か所(同じ folder)", lambda: MS.scan_material(base, pop))
        os.remove(os.path.join(base, MS.CACHES[u"甲"], "dup.zip"))
        with open(os.path.join(base, MS.CACHES[u"乙"], "dup.zip"), "wb") as fh:                   # 別の群の folder に同じ ZIP
            fh.write(zips[0])
        expect_stop(out, u"同じ sha256 が 2 か所(別の folder)", lambda: MS.scan_material(base, pop))
        os.remove(os.path.join(base, MS.CACHES[u"乙"], "dup.zip"))
        # 表の群と違う folder
        wrong = [(pop[0][0], u"乙", pop[0][2])] + list(pop[1:])
        expect_stop(out, u"表の群と違う folder", lambda: MS.scan_material(base, wrong))
        eqp(out, u"直す前は通る", sorted(MS.scan_material(base, pop)), sorted(r[2] for r in pop))
        shutil.rmtree(os.path.join(base, MS.CACHES[u"丙"]))
        expect_stop(out, u"folder が無い", lambda: MS.scan_material(base, pop))
    return out


def population_problems():
    u"""表の検査: 行の数・番号・sha256 の重なり・群の本数・並びが違えば止まる。良い表は通る。"""
    out = []
    good = [(1, u"甲", u"0" * 64), (2, u"乙", u"1" * 64), (3, u"丙", u"2" * 64)]
    V_ = MS.validate_population
    try:
        if V_(good, *SHAPE3) != good:
            out.append(u"良い表が通らない")
    except SystemExit:
        out.append(u"良い表で止まった")
    for label, rows in ((u"行が少ない", good[:2]), (u"行が多い", good + [(4, u"丙", u"3" * 64)]), (u"番号が飛ぶ", [good[0], (3, u"乙", u"1" * 64), (2, u"丙", u"2" * 64)]),
                        (u"sha256 の重なり", [good[0], good[1], (3, u"丙", u"1" * 64)]), (u"群の本数", [good[0], (2, u"甲", u"1" * 64), good[2]]),
                        (u"群の順(乙が甲より前)", [(1, u"乙", u"0" * 64), (2, u"甲", u"1" * 64), (3, u"丙", u"2" * 64)])):
        expect_stop(out, label, lambda rows=rows: V_(rows, *SHAPE3))
    shape2 = (3, collections.OrderedDict([(u"甲", 2), (u"乙", 0), (u"丙", 1)]))
    try:
        V_([(1, u"甲", u"4" * 64), (2, u"甲", u"5" * 64), (3, u"丙", u"2" * 64)], *shape2)
    except SystemExit:
        out.append(u"同じ群の中で sha256 の順の表で止まった")
    expect_stop(out, u"同じ群の中の sha256 の順が逆", lambda: V_([(1, u"甲", u"5" * 64), (2, u"甲", u"4" * 64), (3, u"丙", u"2" * 64)], *shape2))
    expect_stop(out, u"行の数が n と違う(群の本数は合っている形)", lambda: V_(good, 4, SHAPE3[1]))
    return out


def fingerprint_rebuilt():
    u"""記録の ``engine の指紋`` を、門の側で作り直す(script・engine の関数を呼ばない)。``adapters/xbrl`` と ``core/py/audit_core`` 直下の .py の「名前 TAB 内容の sha256」を名前の順につないだ字の sha256 と本数、HEAD の commit(取れなければ None)。"""
    def digest(folder):
        rows = []
        for nm in sorted(os.listdir(folder)):
            if nm.endswith(".py"):
                with open(os.path.join(folder, nm), "rb") as fh:
                    rows.append(u"%s\t%s" % (nm, hashlib.sha256(fh.read()).hexdigest()))
        return hashlib.sha256(u"\n".join(rows).encode("utf-8")).hexdigest(), len(rows)
    a, na = digest(os.path.join(ROOT, "adapters", "xbrl"))
    c, nc = digest(os.path.join(ROOT, "core", "py", "audit_core"))
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=os.path.join(ROOT, "adapters", "xbrl"), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        head = r.stdout.decode("ascii", "replace").strip() or None if r.returncode == 0 else None
    except OSError:
        head = None
    return collections.OrderedDict([(u"adapter_xbrl_py_sha256", a), (u"adapter_xbrl_py_files", na), (u"core_py_sha256", c), (u"core_py_files", nc), (u"git_commit", head)])


def states_problems():
    u"""run_states: 記録の形・集計を行から数え直して一致・文を持たない・2 回(procs 違い)で byte が同じ(時間を除く)・止める所。"""
    out = []
    with tmpdir() as d:
        pop, base, root, zips = states_fixture(d)
        kw = dict(root=root, population=pop, shape=SHAPE4, cache_base=base, say=lambda *a: None)
        before = tree_listing(base)
        p1 = os.path.join(d, "o", "s1.json")
        ticks = iter([10.0, 13.5])
        rec = MS.run_states(procs=1, out=p1, clock=lambda: next(ticks), **kw)
        text = open(p1, encoding="utf-8").read()
        eqp(out, u"返り値と file", json.loads(text), json.loads(json.dumps(rec)))
        eqp(out, u"材料は触らない", tree_listing(base), before)
        books = rec[u"本"]
        eqp(out, u"本の順(表の順)と sha256", [(b[u"#"], b[u"群"], b[u"ZIP の sha256"]) for b in books], [(r[0], r[1], r[2]) for r in pop])
        by_group = dict((b[u"群"], b) for b in books if b[u"群"] != u"丙")
        eqp(out, u"甲の行(連結・単体)", (by_group[u"甲"][u"連結"][u"行"], by_group[u"甲"][u"単体"][u"行"]), (ROWS_A_CONS, ROWS_A_NON))
        eqp(out, u"乙の行(連結・単体)", (by_group[u"乙"][u"連結"][u"行"], by_group[u"乙"][u"単体"][u"行"]), (ROWS_B_CONS, ROWS_B_NON))
        eqp(out, u"時間は 1 つの欄", (rec[u"時間(秒)"], len(re.findall(u"時間", text))), (3.5, 1))
        eqp(out, u"行の欄と行の長さ", (len(rec[u"行の欄"]), set(len(r) for b in books for s in (u"連結", u"単体") for r in b[s][u"行"])), (10, set([10])))
        eqp(out, u"切り出しの記録の NFKC の印", rec[u"切り出し"].get(u"NFKC") is True, True)
        eqp(out, u"切り出しの記録の字", json.loads(json.dumps(rec[u"切り出し"])), json.loads(json.dumps(CUT_RECORD_PINNED)))
        eqp(out, u"限界の 8 行を字で固定", list(rec[u"限界"]), list(LIMITS_PINNED))
        eqp(out, u"判定の記録の字(呼び方・10 欄目)", json.loads(json.dumps(rec[u"判定"])), json.loads(json.dumps(JUDGE_RECORD_PINNED)))
        eqp(out, u"engine の指紋を門の側で作り直して比べる", json.loads(json.dumps(rec[u"engine の指紋"])), json.loads(json.dumps(fingerprint_rebuilt())))
        t = rec[u"集計"]
        for side in (u"連結", u"単体"):
            eqp(out, u"%s の計を行から数え直す" % side, counted(t[side][u"計"]), recount(books, side))
            eqp(out, u"%s の群ごとを行から数え直す" % side, [counted(t[side][g]) for g in (u"甲", u"乙", u"丙")],
                [recount([b for b in books if b[u"群"] == g], side) for g in (u"甲", u"乙", u"丙")])
        eqp(out, u"対応が揃った本では 対応しなかった本 は 0(連結・単体・群ごと・計)",
            [blk[u"claim と raw の並びが対応しなかった本"] for side in (u"連結", u"単体") for blk in t[side].values()], [0] * 8)
        real0 = MS.TS.profile_rows
        with patched(MS.TS, profile_rows=lambda zb, text, zm, pname: (lambda r: (r[0], False, r[2]))(real0(zb, text, zm, pname))):
            rec_bad = MS.run_states(procs=1, out=os.path.join(d, "o", "s_pair.json"), **kw)
        tb = rec_bad[u"集計"]
        eqp(out, u"claim と raw の並びが対応しない本は切れた本のうちだけ数える(連結 3・単体 2。群ごとは 甲 1・1 / 乙 1・1 / 丙 1・0)",
            ([tb[side][u"計"][u"claim と raw の並びが対応しなかった本"] for side in (u"連結", u"単体")],
             [[tb[side][g][u"claim と raw の並びが対応しなかった本"] for g in (u"甲", u"乙", u"丙")] for side in (u"連結", u"単体")]),
            ([3, 2], [[1, 1, 1], [1, 1, 0]]))
        c = t[u"連結"][u"計"]
        eqp(out, u"連結の数(独立に数えた値)", (c[u"本"], c[u"切れた"], c[u"切れない"], dict(c[u"切れない理由"]), c[u"字数の合計"], c[u"claim"], dict(c[u"4 state"]),
                                        c[u"切れた本のうち claim が 0 の本"], c[u"切れた本のうち GROUNDED が 0 の本"], c[u"VALUE_MISMATCH が 1 以上の本"], c[u"VALUE_MISMATCH の内訳"][u"行"]),
            (4, 3, 1, {u"decode": 0, u"札なし": 1, u"札が複数": 0, u"続きあり": 0, u"閉じない": 0, u"空": 0},
             len(u"見出し\n売上高は1,300百万円となりました。\n売上高は1,234百万円となりました。") * 2 + len(u"数はありません。"), 4,
             {u"GROUNDED": 1, u"VALUE_MISMATCH": 1, u"UNVERIFIABLE": 0, u"POINTER_NOT_FOUND": 2}, 1, 2, 1, 1))
        n = t[u"単体"][u"計"]
        eqp(out, u"単体の数(独立に数えた値)", (n[u"本"], n[u"切れた"], n[u"切れない"], n[u"字数の合計"], n[u"claim"], dict(n[u"4 state"]),
                                        n[u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む)の数"][u"GROUNDED"][u"真"],
                                        n[u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む)の数"][u"GROUNDED"][u"偽"],
                                        n[u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む)の数"][u"VALUE_MISMATCH"][u"偽"]),
            (4, 2, 2, len(u"売上高は900百万円となりました。\n売上高は1,300百万円となりました。") * 2, 4, {u"GROUNDED": 1, u"VALUE_MISMATCH": 1, u"UNVERIFIABLE": 1, u"POINTER_NOT_FOUND": 1}, 1, 0, 1))
        eqp(out, u"連結と単体を足さない(集計の欄は文の種類ごと)", list(t), [u"連結", u"単体"])
        eqp(out, u"記録に文・span・値・要素名の字が無い", [x in text for x in (u"売上高", u"百万円", u'"span"', u'"value"', u"NetSales", u"jppfs_cor", u"KeyAuditMatters", u"経営者の文")], [False] * 8)
        eqp(out, u"記録に file 名・path が無い", [x in text for x in (u"m0.zip", u"other.zip", base, u"x.zip", u"other-folder", u"edinet")], [False] * 6)
        mat = rec[u"材料"]
        eqp(out, u"材料の一覧の前後", (mat[u"表と一致した ZIP"], mat[u"3 つの folder の一覧の前後(件数・名前の sha256)"][u"変化なし"]), (4, True))
        eqp(out, u"HEAD・script・封の表・母集団の表の sha256 を持つ", (rec[u"この script の sha256"], rec[u"封の commit"], rec[u"封の表の sha256"], rec[u"母集団の表(# TAB 群 TAB sha256 の行)の sha256"]),
            (ST.sha256_file(os.path.join(ROOT, SCRIPT_REL)), SEAL_COMMIT_SHORT, hashlib.sha256(open(os.path.join(ROOT, SEAL_REL), "rb").read()).hexdigest(),
             hashlib.sha256(u"\n".join(u"%d\t%s\t%s" % r for r in pop).encode("utf-8")).hexdigest()))
        p2 = os.path.join(d, "o", "s2.json")
        MS.run_states(procs=2, out=p2, clock=lambda: 99.0, **kw)
        eqp(out, u"2 回(procs 違い)で byte が同じ(時間を除く)", strip_time(open(p2, encoding="utf-8").read()), strip_time(text))
        # 止める所(何も書かない)
        with patched(MS.TS.NF, map_pool=boom):                                             # 在る出力で止まるのは材料を判定する前
            expect_stop(out, u"出力が在る", lambda: MS.run_states(out=p1, **kw))
        eqp(out, u"在る出力は変わらない", open(p1, encoding="utf-8").read(), text)
        found = MS.scan_material(base, pop)
        swapped = collections.OrderedDict(found)
        swapped[pop[0][2]] = found[pop[1][2]]                                              # 表の sha256 と別の中身の ZIP を指す
        with patched(MS, scan_material=lambda b, pp: swapped):
            expect_stop(out, u"判定の直前に材料の sha256 が表と違う", lambda: MS.run_states(out=os.path.join(d, "o", "s7.json"), **kw))
        if os.path.exists(os.path.join(d, "o", "s7.json")):
            out.append(u"材料の sha256 が違うのに記録を書いた")
        gone = collections.OrderedDict(found)
        gone[pop[0][2]] = (os.path.join(base, "no-such-file-name.zip"), 1)
        with patched(MS, scan_material=lambda b, pp: gone):
            try:
                MS.run_states(out=os.path.join(d, "o", "s8.json"), **kw)
                out.append(u"判定の直前に材料が読めなくても止まらない")
            except SystemExit as exc:
                if u"no-such-file-name" in str(exc) or base in str(exc):
                    out.append(u"止める文言に file 名・path が入っている")
            except BaseException:                                                          # noqa: BLE001
                out.append(u"判定の直前に材料が読めないとき Stop でなく別の例外になる")
        expect_stop(out, u"本番の記録を使い捨ての材料から作る", lambda: MS.run_states(out=os.path.join(root, MS.STATES_REL), **kw))
        if os.path.exists(os.path.join(root, MS.STATES_REL)):
            out.append(u"本番の記録の path に書いた")
        expect_stop(out, u"表の形が違う", lambda: MS.run_states(out=os.path.join(d, "o", "s6.json"), **dict(kw, shape=(3, SHAPE3[1]))))
        with open(os.path.join(base, MS.CACHES[u"丙"], "m3.zip"), "ab") as fh:
            fh.write(b"x")
        expect_stop(out, u"材料の sha256 が違う(表の ZIP が欠ける)", lambda: MS.run_states(out=os.path.join(d, "o", "s3.json"), **kw))
        if os.path.exists(os.path.join(d, "o", "s3.json")) or os.path.exists(os.path.join(d, "o", "s6.json")):
            out.append(u"止まったのに記録を書いた")
    with tmpdir() as d:
        pop, base, root, zips = states_fixture(d)
        kw = dict(root=root, population=pop, shape=SHAPE4, cache_base=base, say=lambda *a: None)
        snaps = iter([(4, u"a"), (4, u"a"), (4, u"a"), (5, u"b"), (5, u"b"), (5, u"b")])
        with patched(ST, names_snapshot=lambda folder: next(snaps)):
            expect_stop(out, u"材料の folder が変わった", lambda: MS.run_states(out=os.path.join(d, "o", "s5.json"), **kw))
        if os.path.exists(os.path.join(d, "o", "s5.json")):
            out.append(u"材料の folder が変わったのに記録を書いた")
        # 件数は同じで名前の sha256 だけが変わる(3 つの folder の全部が変わる・最後の 1 つだけが変わる)
        for i, (label, after) in enumerate(((u"全部の folder", [(4, u"b")] * 3), (u"最後の folder だけ", [(4, u"a"), (4, u"a"), (4, u"b")]))):
            snaps = iter([(4, u"a")] * 3 + after)
            o = os.path.join(d, "o", "s5_%d.json" % i)
            with patched(ST, names_snapshot=lambda folder: next(snaps)):
                expect_stop(out, u"材料の folder の名前の sha256 だけが変わった(states。%s)" % label, lambda o=o: MS.run_states(out=o, **kw))
            if os.path.exists(o):
                out.append(u"材料の folder の名前が変わったのに記録を書いた(states。%s)" % label)
    return out


def population_record_problems():
    u"""run_population: 201 本の記録の形(# ・群・sha256・byte 数)・byte 数の合計・書かない字・止める所。"""
    out = []
    with tmpdir() as d:
        pop, base, root, zips = states_fixture(d)
        kw = dict(root=root, population=pop, shape=SHAPE4, cache_base=base, say=lambda *a: None)
        p1 = os.path.join(d, "o", "p1.json")
        rec = MS.run_population(out=p1, **kw)
        text = open(p1, encoding="utf-8").read()
        eqp(out, u"返り値と file", json.loads(text), json.loads(json.dumps(rec)))
        eqp(out, u"行", rec[u"行"], [[r[0], r[1], r[2], len(z)] for r, z in zip(pop, zips)])
        eqp(out, u"byte 数の合計・群", (rec[u"byte 数の合計"], dict(rec[u"群"])), (sum(len(z) for z in zips), {u"甲": 1, u"乙": 1, u"丙": 2}))
        eqp(out, u"記録に file 名・path が無い", [x in text for x in (u"m0.zip", u"other.zip", base, u"other-folder", u"edinet")], [False] * 5)
        eqp(out, u"封の表・母集団の表の sha256 を持つ", (rec[u"封の表の sha256"], rec[u"母集団の表(# TAB 群 TAB sha256 の行)の sha256"]),
            (hashlib.sha256(open(os.path.join(ROOT, SEAL_REL), "rb").read()).hexdigest(), hashlib.sha256(u"\n".join(u"%d\t%s\t%s" % r for r in pop).encode("utf-8")).hexdigest()))
        with patched(MS, scan_material=boom):                                              # 在る出力で止まるのは材料を探す前
            expect_stop(out, u"出力が在る", lambda: MS.run_population(out=p1, **kw))
        expect_stop(out, u"本番の記録を使い捨ての材料から作る", lambda: MS.run_population(out=os.path.join(root, MS.POPULATION_REL), **kw))
        for i, (label, before_after) in enumerate(((u"件数が変わった", [(4, u"a")] * 3 + [(5, u"b")] * 3), (u"名前の sha256 だけが変わった(全部の folder)", [(4, u"a")] * 3 + [(4, u"b")] * 3),
                                                    (u"名前の sha256 だけが変わった(最後の folder だけ)", [(4, u"a")] * 3 + [(4, u"a")] * 2 + [(4, u"b")]))):
            snaps = iter(before_after)
            o = os.path.join(d, "o", "pn_%d.json" % i)
            with patched(ST, names_snapshot=lambda folder: next(snaps)):
                expect_stop(out, u"材料の folder が変わった(population。%s)" % label, lambda o=o: MS.run_population(out=o, **kw))
            if os.path.exists(o):
                out.append(u"材料の folder が変わったのに記録を書いた(population。%s)" % label)
        os.remove(os.path.join(base, MS.CACHES[u"乙"], "m1.zip"))
        expect_stop(out, u"1 本欠ける", lambda: MS.run_population(out=os.path.join(d, "o", "p2.json"), **kw))
        if os.path.exists(os.path.join(d, "o", "p2.json")) or os.path.exists(os.path.join(root, MS.POPULATION_REL)):
            out.append(u"止まったのに記録を書いた")
    return out


# ---------------------------------------------------------------- 読む行(封 §0-2 の 7)・紙・型
def fake_states(g_rows, v_rows=(), n_books=10):
    u"""作り物の states(読む行の引き方の試験用)。g_rows = 連結の GROUNDED の行 [(本の #, 文の番号, 位置)](順は崩して持たせる)。"""
    def row(r, state):
        return [r[1], r[2], state, None, u"CurrentYear", False, u"円族", False, False, False]
    books = []
    for n in range(1, n_books + 1):
        rows = [row(r, u"GROUNDED") for r in g_rows if r[0] == n] + [row(r, u"VALUE_MISMATCH") for r in v_rows if r[0] == n]
        books.append({u"#": n, u"連結": {u"行": list(reversed(rows))}, u"単体": {u"行": []}})
    return {u"本": list(reversed(books))}


def reading_problems():
    u"""読む行: V・G 単体は全部・G 連結は 60 行を引く・並べ方(# → 文 → 位置)・60 に満たなければ全部・通し番号は 1 から。"""
    out = []
    n = 136
    p = MS.TSS.pick_sample(n, seed=MS.READ_SEED, k=MS.READ_N)
    eqp(out, u"引き方 136(独立に引く)", p, sorted(random.Random(20261115).sample(list(range(n)), 60)))
    eqp(out, u"pin 136", (p[:5], p[-3:], sum(p), len(set(p))), ([1, 4, 5, 6, 10], [125, 130, 132], 3924, 60))
    q = MS.TSS.pick_sample(500, seed=MS.READ_SEED, k=MS.READ_N)
    eqp(out, u"pin 500", (q[:5], q[-3:], sum(q)), ([4, 12, 22, 23, 40], [477, 483, 485], 15874))
    rows = [(1 + (i % 10), 1 + i // 10, 1 + (i * 7) % 5) for i in range(136)]
    rows = sorted(set(rows))
    states = fake_states(rows)
    items = MS.reading_items(states)
    eqp(out, u"組の並び", list(items), [u"V 連結", u"V 単体", u"G 連結", u"G 単体"])
    srt = sorted(rows)
    want = [(i + 1,) + srt[j] for i, j in enumerate(MS.TSS.pick_sample(len(srt), seed=20261115, k=60))]
    eqp(out, u"G 連結は並べた行から 60 行(通し番号は 1 から)", items[u"G 連結"], want)
    eqp(out, u"G 連結の行の数・V・G 単体は空", (len(items[u"G 連結"]), items[u"V 連結"], items[u"V 単体"], items[u"G 単体"]), (60, [], [], []))
    small = fake_states([(2, 3, 1), (1, 9, 2), (1, 2, 5), (1, 2, 1)], v_rows=[(3, 1, 1), (3, 1, 0), (2, 5, 5)])
    s_items = MS.reading_items(small)
    eqp(out, u"60 に満たなければ全部・並べ方 # → 文 → 位置", s_items[u"G 連結"], [(1, 1, 2, 1), (2, 1, 2, 5), (3, 1, 9, 2), (4, 2, 3, 1)])
    eqp(out, u"V 連結は VALUE_MISMATCH の全部(並べ方)", s_items[u"V 連結"], [(1, 2, 5, 5), (2, 3, 1, 0), (3, 3, 1, 1)])
    many_v = fake_states([], v_rows=[(1 + i % 10, 1 + i // 10, 1) for i in range(70)])
    eqp(out, u"V 連結は 70 行でも全部", (len(MS.reading_items(many_v)[u"V 連結"]), len(MS.reading_items(many_v)[u"G 連結"])), (70, 0))
    many_n = {u"本": [{u"#": 1, u"連結": {u"行": []}, u"単体": {u"行": [[i, 1, st, None, u"CurrentYear", False, u"円族", False, False, False] for i in range(70) for st in (u"GROUNDED", u"VALUE_MISMATCH")]}}]}
    eqp(out, u"V 単体・G 単体は 70 行でも全部", (len(MS.reading_items(many_n)[u"V 単体"]), len(MS.reading_items(many_n)[u"G 単体"])), (70, 70))
    exact = fake_states([(1 + i % 10, 1 + i // 10, 1) for i in range(60)])
    eqp(out, u"ちょうど 60 行なら全部", len(MS.reading_items(exact)[u"G 連結"]), 60)
    more = fake_states([(1 + i % 10, 1 + i // 10, 1) for i in range(61)])
    eqp(out, u"61 行なら 60 行引く", len(MS.reading_items(more)[u"G 連結"]), 60)
    # 単体の行は G 単体・V 単体に入る(連結に入らない)
    st2 = {u"本": [{u"#": 1, u"連結": {u"行": []}, u"単体": {u"行": [[1, 1, u"GROUNDED", None, u"CurrentYear", False, u"円族", False, False, True], [2, 1, u"VALUE_MISMATCH", None, u"CurrentYear", False, u"円族", False, False, False],
                                                                      [3, 1, u"UNVERIFIABLE", None, u"なし", False, u"円族", False, False, False]]}}]}
    i2 = MS.reading_items(st2)
    eqp(out, u"単体の行は G 単体・V 単体へ", (i2[u"G 連結"], i2[u"V 連結"], i2[u"G 単体"], i2[u"V 単体"]), ([], [], [(1, 1, 1, 1)], [(1, 1, 2, 1)]))
    return out


def run_fixture(d):
    u"""states の記録を 1 本作る。(表, cache の根, root, states の path)。"""
    pop, base, root, zips = states_fixture(d)
    sp = os.path.join(d, "o", "s.json")
    MS.run_states(root=root, population=pop, shape=SHAPE4, cache_base=base, out=sp, say=lambda *a: None)
    return pop, base, root, sp


SHEET_TAIL = [u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む): ", u"型: "]
SHEET_BLOCKS_WANT = collections.OrderedDict([
    (u"=== V 連結 1 / 本 # 1 / 文 1 / 位置 4 ===", [u"文: 売上高は1,300百万円となりました。", u"span: 売上高は1,300百万円となりました。", u"読んだ値: 1300.0 百万円", u"state: VALUE_MISMATCH  reason: None",
                                              u"結んだ先: xbrl:jppfs_cor:NetSales@CurrentYearDuration", u"その値: 1234000000.0", SHEET_TAIL[0] + u"偽", SHEET_TAIL[1]]),
    (u"=== V 単体 1 / 本 # 1 / 文 1 / 位置 4 ===", [u"文: 売上高は1,300百万円となりました。", u"span: 売上高は1,300百万円となりました。", u"読んだ値: 1300.0 百万円", u"state: VALUE_MISMATCH  reason: None",
                                              u"結んだ先: xbrl:jppfs_cor:NetSales@CurrentYearDuration", u"その値: 1234000000.0", SHEET_TAIL[0] + u"偽", SHEET_TAIL[1]]),
    (u"=== G 連結 1 / 本 # 1 / 文 2 / 位置 4 ===", [u"文: 売上高は1,234百万円となりました。", u"span: 売上高は1,234百万円となりました。", u"読んだ値: 1234.0 百万円", u"state: GROUNDED  reason: None",
                                              u"結んだ先: xbrl:jppfs_cor:NetSales@CurrentYearDuration", u"その値: 1234000000.0", SHEET_TAIL[0] + u"偽", SHEET_TAIL[1]]),
    (u"=== G 単体 1 / 本 # 2 / 文 0 / 位置 4 ===", [u"文: 売上高は900百万円となりました。", u"span: 売上高は900百万円となりました。", u"読んだ値: 900000000.0 円", u"state: GROUNDED  reason: None",
                                              u"結んだ先: xbrl:jppfs_cor:NetSales@CurrentYearDuration_NonConsolidatedMember", u"その値: 900000000.0", SHEET_TAIL[0] + u"真", SHEET_TAIL[1]])])


def sheet_blocks(text):
    u"""紙を「=== 組 通し番号 ... ===」の見出しごとに分け、見出し → 直後からその block の終わりまでの行(空行を除く)。見出しの直後の行が 文: であることも、行の並びで見る。"""
    out = collections.OrderedDict()
    cur = None
    for ln in text.split(u"\n"):
        if ln.startswith(u"=== ") and ln.endswith(u" ==="):
            cur = out.setdefault(ln, [])
        elif cur is not None and ln:
            cur.append(ln)
    return out


def sheet_problems():
    u"""run_sheet: 読む行の文・span・値・結んだ先・10 欄目を紙に書く(標準出力は件数だけ)・repo の中は断る・在れば止める・記録と合わなければ止める。"""
    out = []
    with tmpdir() as d:
        pop, base, root, sp = run_fixture(d)
        said = []
        sheet = os.path.join(d, "paper", "sheet.txt")
        items = MS.run_sheet(sp, sheet, cache_base=base, root=root, say=said.append, population=pop, shape=SHAPE4)
        eqp(out, u"読む行", dict((k, v) for k, v in items.items()),
            {u"V 連結": [(1, 1, 1, 4)], u"V 単体": [(1, 1, 1, 4)], u"G 連結": [(1, 1, 2, 4)], u"G 単体": [(1, 2, 0, 4)]})
        text = open(sheet, encoding="utf-8").read()
        eqp(out, u"紙のブロックごとの 見出し → 文: の行 と 続く欄(組・通し番号に付いた文が取り違えられない)", sheet_blocks(text), SHEET_BLOCKS_WANT)
        eqp(out, u"紙に組・番号・文・読んだ値・結んだ先・10 欄目・型の欄",
            [x in text for x in (u"=== V 連結 1 / 本 # 1 / 文 1 / 位置 4 ===", u"=== V 単体 1 / 本 # 1 / 文 1 / 位置 4 ===", u"=== G 連結 1 / 本 # 1 / 文 2 / 位置 4 ===", u"=== G 単体 1 / 本 # 2 / 文 0 / 位置 4 ===",
                                u"文: 売上高は1,300百万円となりました。", u"span: ", u"読んだ値: 1300.0 百万円", u"読んだ値: 900000000.0 円", u"state: VALUE_MISMATCH", u"state: GROUNDED",
                                u"結んだ先: xbrl:jppfs_cor:NetSales@CurrentYearDuration", u"結んだ先: xbrl:jppfs_cor:NetSales@CurrentYearDuration_NonConsolidatedMember",
                                u"その値: 1234000000.0", u"その値: 900000000.0", u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む): 真", u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む): 偽",
                                u"型: ", u"型の file は 1 行に「組 TAB 通し番号 TAB 型」")], [True] * 18)
        eqp(out, u"標準出力は件数だけ", [u"売上高" in x or u"百万円" in x or u"NetSales" in x for x in said] + [bool(said)], [False] * len(said) + [True])
        eqp(out, u"標準出力に本の件数", said and (u"V 連結 1" in said[0] and u"G 単体 1" in said[0] and u"本 2" in said[0]), True)
        expect_stop(out, u"紙が在る", lambda: MS.run_sheet(sp, sheet, cache_base=base, root=root, say=lambda *a: None, population=pop, shape=SHAPE4))
        inside = os.path.join(ROOT, "zz_sheet_must_not_exist.txt")
        expect_stop(out, u"repo の中", lambda: MS.run_sheet(sp, inside, cache_base=base, root=root, say=lambda *a: None, population=pop, shape=SHAPE4))
        if os.path.exists(inside):
            out.append(u"repo の中に紙を書いた")
            os.remove(inside)
        rec = json.load(open(sp, encoding="utf-8"))
        rec[u"本"][0][u"連結"][u"行"][0][2] = u"GROUNDED"                              # 記録は GROUNDED だが、測り直すと VALUE_MISMATCH の行
        bad = os.path.join(d, "o", "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False))
        rec[u"本"][0][u"連結"][u"行"][0][2] = u"VALUE_MISMATCH"
        rec[u"本"][1][u"単体"][u"行"][0][9] = False                                    # 10 欄目が測り直しと違う行
        bad2 = os.path.join(d, "o", "bad2.json")
        with open(bad2, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False))
        rec[u"本"][1][u"単体"][u"行"][0][9] = True
        rec[u"本"][1][u"単体"][u"行"][0][1] = 5                                         # 位置が違う行(測り直した claim が無い)
        bad3 = os.path.join(d, "o", "bad3.json")
        with open(bad3, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False))
        found = MS.scan_material(base, pop)
        for i, (num, kamkw) in enumerate(((1, dict(tag_no=b"1-changed")), (2, dict(consolidated=False, tag_no=b"2-changed")))):
            alt = os.path.join(d, "alt%d.zip" % i)                                          # 中身の判定は同じで byte だけが違う ZIP(材料の sha256 が表と違う)
            with open(alt, "wb") as fh:
                fh.write(kam_zip(**kamkw))
            swapped = collections.OrderedDict(found)
            swapped[pop[num - 1][2]] = (alt, os.path.getsize(alt))
            with patched(MS, scan_material=lambda b, pp, swapped=swapped: swapped):
                expect_stop(out, u"材料の sha256 が表と違う(# %d)" % num, lambda i=i: MS.run_sheet(sp, os.path.join(d, "paper", "sw%d.txt" % i), cache_base=base, root=root, say=lambda *a: None, population=pop, shape=SHAPE4))
            if os.path.exists(os.path.join(d, "paper", "sw%d.txt" % i)):
                out.append(u"材料の sha256 が表と違うのに紙を書いた(# %d)" % num)
        for i, b in enumerate((bad, bad2, bad3)):
            expect_stop(out, u"記録と合わない行 %d" % i, lambda b=b, i=i: MS.run_sheet(b, os.path.join(d, "paper", "s%d.txt" % i), cache_base=base, root=root, say=lambda *a: None, population=pop, shape=SHAPE4))
            if os.path.exists(os.path.join(d, "paper", "s%d.txt" % i)):
                out.append(u"記録と合わないのに紙を書いた")
    return out


def repo_problems():
    u"""読むための紙を repo の中に書かせない: repo の中・別の git の木の中は真、外は偽。"""
    out = []
    eqp(out, u"repo の中(まだ無い file)", MS.TSS.inside_repo(os.path.join(ROOT, "x", "new_sheet.txt")), True)
    with tmpdir() as d:
        eqp(out, u"repo の外", MS.TSS.inside_repo(os.path.join(d, "a", "sheet.txt")), False)
    return out


def typed_file(d, lines):
    p = os.path.join(d, "typed.tsv")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(u"\n".join(lines) + u"\n")
    return p


GOOD_TYPED = [u"V 連結\t1\tク", u"V 単体\t1\tウ", u"G 連結\t1\ta", u"G 単体\t1\tb\t側"]


def types_problems():
    u"""run_types: 型の file が読む行と 1 対 1・型が組の字・b の行だけ違うもの・付けた席・書かない字。"""
    out = []
    with tmpdir() as d:
        pop, base, root, sp = run_fixture(d)
        kw = dict(root=root, say=lambda *a: None)
        o1 = os.path.join(d, "o", "t1.json")
        rec = MS.run_types(sp, typed_file(d, GOOD_TYPED), o1, **kw)
        text = open(o1, encoding="utf-8").read()
        eqp(out, u"返り値と file", json.loads(text), json.loads(json.dumps(rec)))
        eqp(out, u"行", rec[u"行"], [[u"V 連結", 1, 1, 4, u"ク", None], [u"V 単体", 1, 1, 4, u"ウ", None], [u"G 連結", 1, 2, 4, u"a", None], [u"G 単体", 2, 0, 4, u"b", u"側"]])
        eqp(out, u"型の集計", dict((k, [v[t] for t in v]) for k, v in rec[u"型の集計"].items()),
            {u"V 連結": [0, 0, 0, 0, 0, 0, 0, 1, 0], u"V 単体": [0, 0, 1, 0, 0, 0, 0, 0, 0], u"G 連結": [1, 0, 0], u"G 単体": [0, 1, 0]})
        eqp(out, u"b の違うものの集計", dict((k, list(v.values())) for k, v in rec[u"b の違うものの集計"].items()), {u"G 連結": [0, 0, 0, 0], u"G 単体": [0, 0, 1, 0]})
        eqp(out, u"付けた席・盲検", (u"AI の席" in rec[u"型を付けた席"] and u"人は読んでいない" in rec[u"型を付けた席"], u"盲検ではない" in rec[u"盲検"]), (True, True))
        eqp(out, u"読む行の規則", (rec[u"読む行の規則"][u"種"], rec[u"読む行の規則"][u"引く数"], rec[u"読む行の規則"][u"読む行の数の合計"], rec[u"読む行の規則"][u"G 連結の行の数"]), (20261115, 60, 4, 1))
        eqp(out, u"記録に文の字が無い", [x in text for x in (u"売上高", u"百万円", u"span", u"NetSales")], [False] * 4)
        # 組ごとに行の数が違い、合計が組の数(4)と違う states(G 連結 3・G 単体 5・V 連結 2・V 単体 1 = 11 行)で、規則の欄を数え直す
        def srow(si, st):
            return [si, 1, st, None, u"CurrentYear", False, u"円族", False, False, False]
        uneven = {u"本": [{u"#": 1, u"連結": {u"行": [srow(1, u"GROUNDED"), srow(2, u"GROUNDED"), srow(3, u"GROUNDED"), srow(4, u"VALUE_MISMATCH"), srow(5, u"VALUE_MISMATCH")]},
                                u"単体": {u"行": [srow(i, u"GROUNDED") for i in range(1, 6)] + [srow(6, u"VALUE_MISMATCH")]}}]}
        up = os.path.join(d, "o", "uneven.json")
        with open(up, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(uneven, ensure_ascii=False))
        utyped = [u"V 連結\t1\tア", u"V 連結\t2\tク", u"V 単体\t1\tカ", u"G 連結\t1\ta", u"G 連結\t2\tb\t項目", u"G 連結\t3\tc",
                  u"G 単体\t1\ta", u"G 単体\t2\ta", u"G 単体\t3\tb\t側", u"G 単体\t4\tb\t期", u"G 単体\t5\tc"]
        ur = MS.run_types(up, typed_file(d, utyped), os.path.join(d, "o", "t_uneven.json"), **kw)
        rule = ur[u"読む行の規則"]
        eqp(out, u"組ごとに行の数が違う states の 規則の欄", (rule[u"G 連結の行の数"], dict(rule[u"読む行の数"]), rule[u"読む行の数の合計"], len(ur[u"行"])),
            (3, {u"V 連結": 2, u"V 単体": 1, u"G 連結": 3, u"G 単体": 5}, 11, 11))
        eqp(out, u"組ごとに行の数が違う states の 型の集計・違うものの集計",
            (dict((k, [v[t] for t in v]) for k, v in ur[u"型の集計"].items()), dict((k, list(v.values())) for k, v in ur[u"b の違うものの集計"].items())),
            ({u"V 連結": [1, 0, 0, 0, 0, 0, 0, 1, 0], u"V 単体": [0, 0, 0, 0, 0, 1, 0, 0, 0], u"G 連結": [1, 1, 1], u"G 単体": [2, 2, 1]}, {u"G 連結": [1, 0, 0, 0], u"G 単体": [0, 0, 1, 1]}))
        set_bads = ((u"行が足りない", GOOD_TYPED[:3]), (u"行が多い", GOOD_TYPED + [u"G 単体\t2\ta"]), (u"番号が違う", GOOD_TYPED[:3] + [u"G 単体\t2\ta"]))
        format_bads = ((u"重なる", GOOD_TYPED + [GOOD_TYPED[0]]), (u"V の型に a", [u"V 連結\t1\ta"] + GOOD_TYPED[1:]), (u"G の型に ク", GOOD_TYPED[:2] + [u"G 連結\t1\tク"] + GOOD_TYPED[3:]),
                       (u"型が 9 つの外", [u"V 連結\t1\tコ"] + GOOD_TYPED[1:]), (u"組が 4 つの外", [u"X 連結\t1\tク"] + GOOD_TYPED[1:]), (u"TAB でない", [u"V 連結 1 ク"] + GOOD_TYPED[1:]),
                       (u"番号が数でない", [u"V 連結\tx\tク"] + GOOD_TYPED[1:]), (u"b に違うものが無い", GOOD_TYPED[:3] + [u"G 単体\t1\tb"]),
                       (u"b の違うものが 4 つの外", GOOD_TYPED[:3] + [u"G 単体\t1\tb\t色"]), (u"a に違うもの", GOOD_TYPED[:2] + [u"G 連結\t1\ta\t側"] + GOOD_TYPED[3:]),
                       (u"V に違うもの", [u"V 連結\t1\tク\t側"] + GOOD_TYPED[1:]), (u"5 列", GOOD_TYPED[:3] + [u"G 単体\t1\tb\t側\tx"]))
        eqp(out, u"良い型の file は read_typed が通す", sorted(MS.read_typed(typed_file(d, GOOD_TYPED)).items()),
            sorted([((u"V 連結", 1), (u"ク", None)), ((u"V 単体", 1), (u"ウ", None)), ((u"G 連結", 1), (u"a", None)), ((u"G 単体", 1), (u"b", u"側"))]))
        format_bads = format_bads + ((u"2 列", [u"V 連結\t1"] + GOOD_TYPED[1:]), (u"1 列", [u"V 連結"] + GOOD_TYPED[1:]))
        for i, (label, lines) in enumerate(set_bads + format_bads):
            o = os.path.join(d, "o", "bad_%d.json" % i)
            expect_stop(out, label, lambda lines=lines, o=o: MS.run_types(sp, typed_file(d, lines), o, **kw))
            if os.path.exists(o):
                out.append(u"%s: 止まったのに記録を書いた" % label)
        for label, lines in format_bads:
            expect_stop(out, u"read_typed: %s" % label, lambda lines=lines: MS.read_typed(typed_file(d, lines)))
        expect_stop(out, u"出力が在る", lambda: MS.run_types(sp, typed_file(d, GOOD_TYPED), o1, **kw))
        expect_stop(out, u"出力が在れば states を読む前に止まる", lambda: MS.run_types(os.path.join(d, "none.json"), typed_file(d, GOOD_TYPED), o1, **kw))
    return out


def clean_problems():
    u"""記録に repo へ入れない欄・鍵らしい字・docID の字が在れば止まる。"""
    out = []
    ok = collections.OrderedDict([(u"seal", MS.SEAL_REL), (u"本", [{u"行": [[1, 2]]}])])
    try:
        MS.check_clean(ok, json.dumps(ok, ensure_ascii=False))
    except SystemExit:
        out.append(u"良い記録で止まった")
    for key in (u"span", u"value", u"text", u"文", u"recomputed", u"sentence"):
        bad = collections.OrderedDict([(u"本", [{key: u"x"}])])
        expect_stop(out, u"欄 %s" % key, lambda bad=bad: MS.check_clean(bad, json.dumps(bad, ensure_ascii=False)))
    leak = collections.OrderedDict([(u"x", u"a" * 40 + u"Z" * 8)])
    expect_stop(out, u"鍵らしい字", lambda: MS.check_clean(leak, json.dumps(leak, ensure_ascii=False)))
    docid = collections.OrderedDict([(u"x", u"S100" + u"AB12")])
    expect_stop(out, u"docID の字", lambda: MS.check_clean(docid, json.dumps(docid, ensure_ascii=False)))
    return out


# ---------------------------------------------------------------- 8. 本番の記録が在れば形を縛る(無ければ何も言わない)
def record_problems(base=ROOT, seal=None):
    u"""本番の記録(``fixtures/xbrl/kam/`` の 3 つ)の形: 在る記録だけを見る。母集団は封の表と同じ・本は表の順と sha256・書かない字が無い・読む行の形。"""
    out = []
    seal = seal if seal is not None else read(SEAL_REL)
    want = [(r[0], r[1], r[2]) for r in seal_table(seal)]
    paths = [os.path.join(base, rel) for rel in RECORD_RELS]
    for p, rel in zip(paths, RECORD_RELS):
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        if DOCID_RE.search(text) or TDNET_RE.search(text):
            out.append(u"%s に docID・TDnet の番号の字がある" % rel)
        rec = json.loads(text)
        bad_keys = sorted(set(k for k in TS.RUN.walk_keys(rec) if k in TS.RUN.FORBIDDEN_KEYS))
        if bad_keys:
            out.append(u"%s に repo へ入れない欄がある: %s" % (rel, u",".join(bad_keys)))
        if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
            out.append(u"%s の seal・封の commit が違う" % rel)
        if rec.get(u"key_leaks") != []:
            out.append(u"%s の key_leaks が空でない" % rel)
        if rel == RECORD_RELS[0]:
            if [tuple(r[:3]) for r in rec.get(u"行", [])] != want or any(not isinstance(r[3], int) for r in rec.get(u"行", [])):
                out.append(u"%s の行が封 §1 の表と違う" % rel)
        elif rel == RECORD_RELS[1]:
            if [(b[u"#"], b[u"群"], b[u"ZIP の sha256"]) for b in rec.get(u"本", [])] != want:
                out.append(u"%s の本の順・sha256 が封 §1 の表と違う" % rel)
            if any(len(r) != 10 for b in rec.get(u"本", []) for s in (u"連結", u"単体") for r in b[s][u"行"]):
                out.append(u"%s の行の長さが 10 でない" % rel)
        else:
            lab = [u"V 連結", u"V 単体", u"G 連結", u"G 単体"]
            if [r[0] for r in rec.get(u"行", [])] != sorted((r[0] for r in rec.get(u"行", [])), key=lab.index):
                out.append(u"%s の行が組の順でない" % rel)
            for r in rec.get(u"行", []):
                good = (list(u"アイウエオカキクケ") if r[0] in (u"V 連結", u"V 単体") else [u"a", u"b", u"c"])
                if len(r) != 6 or r[4] not in good or ((r[4] == u"b") != (r[5] is not None)) or (r[5] is not None and r[5] not in (u"項目", u"範囲", u"側", u"期")):
                    out.append(u"%s の行の型・違うものが規則と合わない" % rel)
                    break
            if len([r for r in rec.get(u"行", []) if r[0] == u"G 連結"]) > 60:
                out.append(u"%s の G 連結が 60 行を超える" % rel)
    return out


def record_fixture_problems():
    u"""``record_problems`` 自体の検査: 記録が無ければ何も言わない・正しい記録は通る・壊した記録は赤。"""
    out = []
    seal = read(SEAL_REL)
    pop = [(r[0], r[1], r[2]) for r in seal_table(seal)]
    with tmpdir() as d:
        eqp(out, u"記録が無ければ何も言わない", record_problems(base=d, seal=seal), [])
        os.makedirs(os.path.join(d, "fixtures", "xbrl", "kam"))
        head = {u"seal": SEAL_REL, u"封の commit": SEAL_COMMIT_SHORT, u"key_leaks": []}

        def put(i, rec):
            with open(os.path.join(d, RECORD_RELS[i]), "w", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False))
        put(0, dict(head, **{u"行": [list(r) + [10] for r in pop]}))
        eqp(out, u"正しい母集団の記録", record_problems(base=d, seal=seal), [])
        put(0, dict(head, **{u"行": [list(r) + [10] for r in pop[:-1]]}))
        if not record_problems(base=d, seal=seal):
            out.append(u"母集団の行が 200 行でも黙る")
        put(0, dict(head, **{u"行": [list(r) + [10] for r in pop[1:] + pop[:1]]}))
        if not record_problems(base=d, seal=seal):
            out.append(u"母集団の行の順が違っても黙る")
        put(0, dict(head, **{u"行": [list(r) + [10] for r in pop], u"span": u"x"}))
        if not record_problems(base=d, seal=seal):
            out.append(u"禁じた欄が在っても黙る")
        put(0, dict(head, **{u"行": [list(r) + [10] for r in pop], u"note": u"S100" + u"AB12"}))
        if not record_problems(base=d, seal=seal):
            out.append(u"docID の字が在っても黙る")
        put(0, dict(head, **{u"封の commit": u"0000000", u"行": [list(r) + [10] for r in pop]}))
        if not record_problems(base=d, seal=seal):
            out.append(u"封の commit が違っても黙る")
        put(0, dict(head, **{u"key_leaks": [u"x"], u"行": [list(r) + [10] for r in pop]}))
        if not record_problems(base=d, seal=seal):
            out.append(u"key_leaks が空でなくても黙る")
        os.remove(os.path.join(d, RECORD_RELS[0]))
        row = [0, 0, u"GROUNDED", None, u"CurrentYear", False, u"円族", False, False, False]
        book = lambda r: {u"#": r[0], u"群": r[1], u"ZIP の sha256": r[2], u"連結": {u"行": [row]}, u"単体": {u"行": []}}
        put(1, dict(head, **{u"本": [book(r) for r in pop]}))
        eqp(out, u"正しい states の記録", record_problems(base=d, seal=seal), [])
        put(1, dict(head, **{u"本": [book(r) for r in pop[1:]]}))
        if not record_problems(base=d, seal=seal):
            out.append(u"本が 200 本でも黙る")
        put(1, dict(head, **{u"本": [dict(book(r), **{u"連結": {u"行": [row[:9]]}}) for r in pop]}))
        if not record_problems(base=d, seal=seal):
            out.append(u"行が 9 欄でも黙る")
        os.remove(os.path.join(d, RECORD_RELS[1]))
        good = [[u"V 連結", 1, 1, 1, u"ア", None], [u"G 単体", 1, 1, 1, u"b", u"側"]]
        put(2, dict(head, **{u"行": good}))
        eqp(out, u"正しい型の記録", record_problems(base=d, seal=seal), [])
        for label, rows in ((u"V に a", [[u"V 連結", 1, 1, 1, u"a", None]]), (u"G に ア", [[u"G 単体", 1, 1, 1, u"ア", None]]), (u"b に違うものが無い", [[u"G 単体", 1, 1, 1, u"b", None]]),
                            (u"a に違うもの", [[u"G 単体", 1, 1, 1, u"a", u"側"]]), (u"違うものが 4 つの外", [[u"G 単体", 1, 1, 1, u"b", u"色"]]), (u"組の順が違う", [good[1], good[0]])):
            put(2, dict(head, **{u"行": rows}))
            if not record_problems(base=d, seal=seal):
                out.append(u"型の記録: %s でも黙る" % label)
    return out


# ================================================================ 変異の表(約束の側から。関数の字を 1 か所替えた版を差し込み、検査が赤になることを見る)
def _m(label, mod, fn, old, new, check):
    return (label, mod, fn, old, new, check)


MUTANTS = (
    # 切り出し
    _m(u"切り出し: 札の名前を前方一致で探す(閉じ引用符を外す)", MS, "cut_kam", u"pat = re.compile(START_RE % re.escape(SIDES[side]))", u"pat = re.compile(START_RE.replace(u'\"%s\"', u'\"%s') % re.escape(SIDES[side]))", cut_problems),
    _m(u"切り出し: 連結の札で単体を探す", MS, "cut_kam", u"SIDES[side]", u"SIDES[u\"連結\"]", cut_problems),
    _m(u"切り出し: 単体の札で連結を探す", MS, "cut_kam", u"SIDES[side]", u"SIDES[u\"単体\"]", cut_problems),
    _m(u"切り出し: 最初の一致でなく最後の一致", MS, "cut_kam", u"m = pat.search(t)", u"ms = list(pat.finditer(t))\n        m = ms[-1] if ms else None", cut_problems),
    _m(u"切り出し: 一致を数えて複数でも通す", MS, "cut_kam", u"if len(hits) >= 2:", u"if len(hits) >= 3:", cut_problems),
    _m(u"切り出し: 札の無い本を札が複数と言う", MS, "cut_kam", u"        return None, WHY_NOTAG", u"        return None, WHY_MANY", cut_problems),
    _m(u"切り出し: 続きありを見ない", MS, "cut_kam", u"if CONTINUED in m.group(0):", u"if False:", cut_problems),
    _m(u"切り出し: 続きありを塊の全体で見る", MS, "cut_kam", u"if CONTINUED in m.group(0):", u"if CONTINUED in t:", cut_problems),
    _m(u"切り出し: 閉じなくても通す", MS, "cut_kam", u"if inner is None:", u"if False:", cut_problems),
    _m(u"切り出し: 空を通す", MS, "cut_kam", u"if not text:", u"if False:", cut_problems),
    _m(u"切り出し: decode を緩める", MS, "cut_kam", u"raw.decode(\"utf-8\")", u"raw.decode(\"utf-8\", \"replace\")", cut_problems),
    _m(u"切り出し: decode できない file を読み飛ばす", MS, "cut_kam", u"            return None, WHY_DECODE", u"            continue", cut_problems),
    _m(u"切り出し: 全部の member を読む", MS, "cut_kam", u"if AUDIT_MARK in n and n.endswith(AUDIT_SUFFIX)", u"if n.endswith(AUDIT_SUFFIX)", cut_problems),
    _m(u"切り出し: .html も読む", MS, "cut_kam", u"n.endswith(AUDIT_SUFFIX)", u"n.endswith(u\".htm\") or n.endswith(u\".html\")", cut_problems),
    _m(u"切り出し: /AuditDoc/ の頭の斜線を見ない", MS, "cut_kam", u"AUDIT_MARK in n", u"u\"AuditDoc/\" in n", cut_problems),
    _m(u"切り出し: ZIP でなくても止めない", MS, "cut_kam", u"raise Stop(u\"**ZIP として読めない。止める**\")", u"return None, WHY_NOTAG", cut_problems),
    # 深さ・文
    _m(u"深さ: 入れ子の閉じ札で終わる(深さを数えない)", MS, "cut_inner", u"depth = 1", u"depth = 0", cut_problems),
    _m(u"深さ: 開く札を数えない", MS, "cut_inner", u"depth += 1", u"depth += 0", cut_problems),
    _m(u"深さ: 自分で閉じる札も開く札に数える", MS, "cut_inner", u"elif mm.group(1) != \"/\":", u"else:", cut_problems),
    _m(u"深さ: 閉じる札で 2 減らす", MS, "cut_inner", u"depth -= 1", u"depth -= 2", cut_problems),
    _m(u"深さ: 始まりの札の字から読む", MS, "cut_inner", u"tail = t[start_end:]", u"tail = t[:]", cut_problems),
    _m(u"文: NFKC を掛けない", MS, "lines_to_text", u"unicodedata.normalize(\"NFKC\", ln).strip()", u"ln.strip()", cut_problems),
    _m(u"文: NFC にする", MS, "lines_to_text", u"\"NFKC\"", u"\"NFC\"", cut_problems),
    _m(u"文: 前後の空白を落とさない", MS, "lines_to_text", u"unicodedata.normalize(\"NFKC\", ln).strip()", u"unicodedata.normalize(\"NFKC\", ln)", cut_problems),
    _m(u"文: 空の行を捨てない", MS, "lines_to_text", u"        if ln:", u"        if True:", cut_problems),
    _m(u"文: 手本の html_to_lines を呼ばない", MS, "lines_to_text", u"TS.html_to_lines(inner)", u"inner.split(u\"\\n\")", cut_problems),
    _m(u"文: 行を空白でつなぐ", MS, "lines_to_text", u"u\"\\n\".join(out)", u"u\" \".join(out)", cut_problems),
    # 10 欄目
    _m(u"10 欄目: 印の字が違う", MS, "row10", u"NONCONSOLIDATED_MARK in p", u"u\"ConsolidatedMember\" in p", row10_problems),
    _m(u"10 欄目: 全部の pointer でなく先頭だけ見る", MS, "row10", u"for p in v[2])", u"for p in v[2][:1])", row10_problems),
    _m(u"10 欄目: 全部の pointer が含むときだけ真", MS, "row10", u"return TS.row_entry(key, v) + [any(", u"return TS.row_entry(key, v) + [bool(v[2]) and all(", row10_problems),
    _m(u"10 欄目: 常に偽", MS, "row10", u"return TS.row_entry(key, v) + [any(isinstance(p, str) and NONCONSOLIDATED_MARK in p for p in v[2])]", u"return TS.row_entry(key, v) + [False]", row10_problems),
    _m(u"10 欄目: 9 欄目に置く", MS, "row10", u"return TS.row_entry(key, v) + [", u"return TS.row_entry(key, v)[:8] + [", row10_problems),
    # 判定の配線
    _m(u"判定: profile が違う", MS, "judge_side", u"TS.profile_rows(zb, text, zm, PROFILE)", u"TS.profile_rows(zb, text, zm, u\"P30E\")", judge_problems),
    _m(u"判定: 差し替えた ZIP を元の ZIP にする", MS, "judge_side", u"TS.profile_rows(zb, text, zm, PROFILE)", u"TS.profile_rows(zb, text, zb, PROFILE)", judge_problems),
    _m(u"判定: 文を渡さない", MS, "judge_side", u"TS.profile_rows(zb, text, zm, PROFILE)", u"TS.profile_rows(zb, None, zm, PROFILE)", judge_problems),
    _m(u"判定: 連結の文を単体にも渡す", MS, "judge_book", u"book[side] = judge_side(zb, side)", u"book[side] = judge_side(zb, u\"連結\")", judge_problems),
    _m(u"判定: 字数が違う", MS, "judge_side", u"(u\"字数\", len(text))", u"(u\"字数\", len(text) + 1)", judge_problems),
    _m(u"判定: 切れない側の理由が無い", MS, "judge_side", u"(u\"理由\", why)", u"(u\"理由\", None)", judge_problems),
    _m(u"判定: 切れない側が claim を持つ", MS, "judge_side", u"(u\"claim\", 0)", u"(u\"claim\", 1)", judge_problems),
    _m(u"判定: 対応を見ない", MS, "judge_side", u"(u\"対応\", bool(ok))", u"(u\"対応\", True)", judge_problems),
    _m(u"判定: 本の欄の順が違う", MS, "judge_book", u"for side in SIDES:", u"for side in reversed(list(SIDES)):", judge_problems),
    # 材料・母集団
    _m(u"材料: 表に無い ZIP も選ぶ", MS, "scan_material", u"if s not in want:", u"if False:", scan_problems),
    _m(u"材料: 同じ sha256 が 2 か所でも通す", MS, "scan_material", u"if s in found:", u"if False:", scan_problems),
    _m(u"材料: 群が違っても通す", MS, "scan_material", u"if want[s][1] != grp:", u"if False:", scan_problems),
    _m(u"材料: 欠けても通す", MS, "scan_material", u"if len(found) != len(pop):", u"if False:", scan_problems),
    _m(u"材料: folder が無くても通す", MS, "scan_material", u"if not os.path.isdir(d):", u"if False:", scan_problems),
    _m(u"材料: zip でない file も読む", MS, "scan_material", u"if not f.endswith(\".zip\") or not os.path.isfile(p):", u"if False:", scan_problems),
    _m(u"材料: byte 数が違う", MS, "scan_material", u"found[s] = (p, len(b))", u"found[s] = (p, len(b) + 1)", scan_problems),
    _m(u"母集団: 行の数を見ない", MS, "validate_population", u"if len(rows) != n:", u"if False:", population_problems),
    _m(u"母集団: 番号を見ない", MS, "validate_population", u"if [r[0] for r in rows] != list(range(1, len(rows) + 1)):", u"if False:", population_problems),
    _m(u"母集団: sha256 の重なりを見ない", MS, "validate_population", u"if len(set(r[2] for r in rows)) != len(rows):", u"if False:", population_problems),
    _m(u"母集団: 群の本数を見ない", MS, "validate_population", u"if [(g, c.get(g, 0)) for g in groups] != list(groups.items()) or sum(c.values()) != len(rows):", u"if False:", population_problems),
    _m(u"母集団: 並びを見ない", MS, "validate_population", u"if order != sorted(order):", u"if False:", population_problems),
    # states・集計・記録
    _m(u"states: 材料の sha256 を見ない", MS, "states_job", u"if ST.sha256_bytes(zb) != sha:", u"if False:", states_problems),
    _m(u"states: 材料が読めなくても Stop にしない", MS, "read_zip", u"except OSError:", u"except ZeroDivisionError:", states_problems),
    _m(u"states: 止める文言に path を入れる", MS, "read_zip", u"u\"**材料の ZIP が読めない(# %d)。止める**\" % n", u"u\"**%s**\" % path", states_problems),
    _m(u"states: 材料の folder が変わっても止めない", MS, "run_states", u"if before != after:", u"if False:", states_problems),
    _m(u"states: 本番の記録を使い捨ての材料で作る", MS, "is_production_out", u"and os.path.abspath(base) != os.path.abspath(default_base())", u"and False", states_problems),
    _m(u"states: 在る出力に書く", MS, "run_states", u"if os.path.exists(out):", u"if False:", states_problems),
    _m(u"states: 時間を測らない", MS, "run_states", u"elapsed = clock() - t0", u"elapsed = 0.0", states_problems),
    _m(u"states: 本の順が表の順でない", MS, "run_states", u"books = TS.NF.map_pool(states_job, jobs, procs)", u"books = list(reversed(TS.NF.map_pool(states_job, jobs, procs)))", states_problems),
    _m(u"states: 連結と単体を足す(集計の欄)", MS, "tally", u"for side in SIDES:", u"for side in list(SIDES)[:1]:", states_problems),
    _m(u"集計: GROUNDED が 0 の本の条件が逆", MS, "block", u"if not c.get(G, 0):", u"if c.get(G, 0):", states_problems),
    _m(u"集計: VALUE_MISMATCH が 1 以上の本の閾値が違う", MS, "block", u"if c.get(VM, 0) >= 1:", u"if c.get(VM, 0) >= 2:", states_problems),
    _m(u"集計: 切れた本の数え方が逆", MS, "block", u"s[u\"切り出し\"] == CUT_OK]", u"s[u\"切り出し\"] == CUT_NG]", states_problems),
    _m(u"集計: 字数の合計が本の数", MS, "block", u"sum(s[u\"字数\"] for s in cut_sides)", u"sum(1 for s in cut_sides)", states_problems),
    _m(u"集計: claim が 0 の本が数えられない", MS, "block", u"if not s[u\"行\"]:", u"if False:", states_problems),
    _m(u"集計: 10 欄目の真と偽が逆", MS, "block", u"(u\"真\", sum(1 for r in sub if r[9])), (u\"偽\", sum(1 for r in sub if not r[9]))", u"(u\"真\", sum(1 for r in sub if not r[9])), (u\"偽\", sum(1 for r in sub if r[9]))", states_problems),
    _m(u"集計: 10 欄目を 9 欄目で数える", MS, "block", u"if r[9])", u"if r[8])", states_problems),
    _m(u"集計: 切れない理由を数えない", MS, "block", u"why = collections.Counter(s[u\"理由\"] for s in sides if s[u\"切り出し\"] == CUT_NG)", u"why = collections.Counter()", states_problems),
    _m(u"集計: 群ごとを計と同じにする", MS, "tally", u"sub[g] = block([b[side] for b in books if b[u\"群\"] == g])", u"sub[g] = block([b[side] for b in books])", states_problems),
    _m(u"記録: 欄の禁止を見ない", MS, "check_clean", u"    if bad:", u"    if False:", clean_problems),
    _m(u"記録: 鍵らしい字を見ない", MS, "check_clean", u"    if leaks:", u"    if False:", clean_problems),
    _m(u"記録: docID の字を見ない", MS, "check_clean", u"    if DOCID_RE.search(text):", u"    if False:", clean_problems),
    _m(u"母集団の記録: 在る出力に書く", MS, "run_population", u"if os.path.exists(out):", u"if False:", population_record_problems),
    _m(u"母集団の記録: byte 数の合計が違う", MS, "run_population", u"rec[u\"byte 数の合計\"] = sum(found[r[2]][1] for r in pop)", u"rec[u\"byte 数の合計\"] = len(pop)", population_record_problems),
    _m(u"母集団の記録: 行に byte 数が無い", MS, "run_population", u"[r[0], r[1], r[2], found[r[2]][1]]", u"[r[0], r[1], r[2], 0]", population_record_problems),
    _m(u"母集団の記録: 本番の記録を使い捨ての材料で作る", MS, "run_population", u"if is_production_out(out, base, root, POPULATION_REL):", u"if False:", population_record_problems),
    # 読む行・紙・型
    _m(u"読む行: 種が違う", MS, "reading_items", u"seed=READ_SEED", u"seed=READ_SEED + 1", reading_problems),
    _m(u"読む行: 引く数が違う", MS, "reading_items", u"k=READ_N", u"k=READ_N + 1", reading_problems),
    _m(u"読む行: 引かずに全部", MS, "reading_items", u"if draw:", u"if False:", reading_problems),
    _m(u"読む行: V 連結も引く", MS, "reading_items", u"if draw:", u"if draw or label == V_CONS:", reading_problems),
    _m(u"読む行: 通し番号が 0 から", MS, "reading_items", u"(i + 1,)", u"(i,)", reading_problems),
    _m(u"読む行: 本の順が # の順でない", MS, "side_rows", u"key=lambda b: b[u\"#\"]", u"key=lambda b: -b[u\"#\"]", reading_problems),
    _m(u"読む行: 行の順が文・位置の順でない", MS, "side_rows", u"key=lambda r: (r[0], r[1])", u"key=lambda r: (r[1], r[0])", reading_problems),
    _m(u"読む行: state の絞り込みが無い", MS, "side_rows", u"if r[2] == state)", u"if True)", reading_problems),
    _m(u"読む行: 文の種類が違う", MS, "side_rows", u"b[side][u\"行\"]", u"b[u\"連結\"][u\"行\"]", reading_problems),
    _m(u"紙: git の木の中を見ない(TSS の判定を使わない)", MS, "run_sheet", u"if TSS.inside_repo(sheet, repo):", u"if False:", sheet_problems),
    _m(u"紙: 在っても書く", MS, "run_sheet", u"if os.path.exists(sheet):", u"if False:", sheet_problems),
    _m(u"紙: 10 欄目の食い違いを通す", MS, "run_sheet", u" or row10(key, rows[key]) != rec_rows.get(key):", u":", sheet_problems),
    _m(u"紙: 10 欄目を書かない", MS, "sheet_text", u"u\"真\" if ten else u\"偽\"", u"u\"偽\"", sheet_problems),
    _m(u"紙: 結んだ先を書かない", MS, "sheet_text", u"u\" , \".join(claim[\"pointers\"] or [])", u"u\"\"", sheet_problems),
    _m(u"型: 読む行と型の行がそろわなくても通す", MS, "run_types", u"if sorted(typed) != sorted(", u"if False and sorted(typed) != sorted(", types_problems),
    _m(u"型: 組の外の型を通す", MS, "read_typed", u" or parts[2] not in types_of(parts[0])", u"", types_problems),
    _m(u"型: 組の外の字を通す", MS, "read_typed", u"parts[0] not in READ_SETS or ", u"", types_problems),
    _m(u"型: 列の数を見ない", MS, "read_typed", u"len(parts) not in (3, 4) or ", u"", types_problems),
    _m(u"型: 同じ行を通す", MS, "read_typed", u"if k in out:", u"if False:", types_problems),
    _m(u"型: b でない行の違うものを通す", MS, "read_typed", u"(len(parts) == 4) != (parts[2] == DIFF_TYPE) or ", u"", types_problems),
    _m(u"型: 違うものの字を見ない", MS, "read_typed", u" or (len(parts) == 4 and parts[3] not in DIFFS)", u"", types_problems),
    _m(u"型: 付けた席を書かない", MS, "run_types", u"rec[u\"型を付けた席\"] = TYPED_BY", u"rec[u\"型を付けた席\"] = u\"人\"", types_problems),
    _m(u"型: 出力が在っても書く", MS, "run_types", u"if os.path.exists(out):", u"if False:", types_problems),
    _m(u"型: G の組の型の字が V の字", MS, "types_of", u"TYPES_G if label in (G_CONS, G_NON) else TYPES_V", u"TYPES_V", types_problems),
    _m(u"型: b の集計が G 連結だけ", MS, "run_types", u"for label in (G_CONS, G_NON):", u"for label in (G_CONS,):", types_problems),
    # 監査の REVISE 8 点(2026-11-15)
    _m(u"記録: 切り出しの NFKC の印が偽", MS, "run_states", u"(u\"NFKC\", True)", u"(u\"NFKC\", False)", states_problems),
    _m(u"記録: 切り出しの member の字が違う", MS, "run_states", u"(u\"member\", u\"名前に /AuditDoc/ を含み", u"(u\"member\", u\"名前に /AuditDocs/ を含み", states_problems),
    _m(u"記録: 限界の 1 行を落とす", MS, "run_states", u"rec[u\"限界\"] = list(STATES_LIMITS)", u"rec[u\"限界\"] = list(STATES_LIMITS)[1:]", states_problems),
    _m(u"記録: 限界の最後の行を落とす", MS, "run_states", u"rec[u\"限界\"] = list(STATES_LIMITS)", u"rec[u\"限界\"] = list(STATES_LIMITS)[:-1]", states_problems),
    _m(u"記録: engine の指紋の本数が違う", MS, "run_states", u"rec[u\"engine の指紋\"] = VD.engine_fingerprint()", u"rec[u\"engine の指紋\"] = dict(VD.engine_fingerprint(), core_py_files=0)", states_problems),
    _m(u"記録: engine の指紋を持たない", MS, "run_states", u"rec[u\"engine の指紋\"] = VD.engine_fingerprint()", u"rec[u\"engine の指紋\"] = {}", states_problems),
    _m(u"記録: 判定の呼び方の字が違う", MS, "run_states", u"verify_document(元の ZIP, P33E, text=文)", u"verify_document(元の ZIP, P32E, text=文)", states_problems),
    _m(u"記録: 判定の 10 欄目の説明の字が違う", MS, "run_states", u"を含む(真偽)\" % NONCONSOLIDATED_MARK", u"を含む\" % NONCONSOLIDATED_MARK", states_problems),
    _m(u"集計: 対応しなかった本を 0 固定にする", MS, "block", u"sum(1 for s in cut_sides if not s[u\"対応\"])", u"0", states_problems),
    _m(u"集計: 対応しなかった本に切れない本も数える", MS, "block", u"sum(1 for s in cut_sides if not s[u\"対応\"])", u"sum(1 for s in sides if not s[u\"対応\"])", states_problems),
    _m(u"states: folder の前後を件数だけで比べる", MS, "run_states", u"if before != after:", u"if [x[0] for x in before] != [x[0] for x in after]:", states_problems),
    _m(u"states: folder の前後を最初の 1 つだけで比べる", MS, "run_states", u"if before != after:", u"if before[:1] != after[:1]:", states_problems),
    _m(u"母集団の記録: folder の前後を件数だけで比べる", MS, "run_population", u"if before != after:", u"if [x[0] for x in before] != [x[0] for x in after]:", population_record_problems),
    _m(u"母集団の記録: folder の前後を最初の 1 つだけで比べる", MS, "run_population", u"if before != after:", u"if before[:1] != after[:1]:", population_record_problems),
    _m(u"深さ: 属性に / を含む入れ子の開く札を自分で閉じる札と見なす", MS, "cut_inner", u"elif mm.group(1) != \"/\":", u"elif u\"/\" not in mm.group(0):", cut_problems),
    _m(u"紙: 文の番号を 1 つ前にする", MS, "run_sheet", u"sents[it[2]]", u"sents[it[2] - 1]", sheet_problems),
    _m(u"紙: 文を位置の番号で引く", MS, "run_sheet", u"sents[it[2]]", u"sents[it[3] - 4]", sheet_problems),
    _m(u"紙: 文を通し番号で引く", MS, "run_sheet", u"sents[it[2]]", u"sents[it[0]]", sheet_problems),
    _m(u"紙: 材料の sha256 が表と違っても通す", MS, "run_sheet", u"if ST.sha256_bytes(zb) != sha:", u"if False:", sheet_problems),
    _m(u"型: G 連結の行の数を単体の側で数える", MS, "run_types", u"len(side_rows(states, u\"連結\", G))", u"len(side_rows(states, u\"単体\", G))", types_problems),
    _m(u"型: 読む行の数の合計を組の数にする", MS, "run_types", u"sum(len(its) for its in items.values())", u"len(items)", types_problems),
)

#: 定数の変異(``patched``)。(説明, module, 名前, 替えた値, 赤になるべき検査)。検査は定数を見るもの・振る舞いを見るもののどちらか
CONST_MUTANTS = (
    (u"札の名前(連結)を 1 字替える", MS, "SIDES", collections.OrderedDict([(u"連結", "jpcrp_cor:KeyAuditMattersConsolidatedTextBlocx"), (u"単体", MS.SIDES[u"単体"])]), (script_problems, cut_problems)),
    (u"札の名前(単体)を 1 字替える", MS, "SIDES", collections.OrderedDict([(u"連結", MS.SIDES[u"連結"]), (u"単体", "jpcrp_cor:KeyAuditMattersNonConsolidatedTextBlocx")]), (script_problems, cut_problems)),
    (u"始まりの規則の \\b を外す", MS, "START_RE", MS.START_RE.replace(u"\\bname", u"name"), (script_problems, cut_problems)),
    (u"始まりの規則の [^>]* を .* にする", MS, "START_RE", MS.START_RE.replace(u"\"[^>]*>", u"\".*>"), (script_problems, cut_problems)),
    (u"深さの規則の自分で閉じる印を落とす", MS, "DEPTH_RE", re.compile(r'<ix:nonNumeric\b[^>]*?()>|</ix:nonNumeric>'), (script_problems, cut_problems)),
    (u"深さの規則の閉じる札を落とす", MS, "DEPTH_RE", re.compile(r'<ix:nonNumeric\b[^>]*?(/?)>'), (script_problems, cut_problems)),
    (u"続きありの印", MS, "CONTINUED", "continuedat", (script_problems, cut_problems)),
    (u"AuditDoc の印", MS, "AUDIT_MARK", "/AuditDocs/", (script_problems, cut_problems)),
    (u"AuditDoc の拡張子", MS, "AUDIT_SUFFIX", ".html", (script_problems, cut_problems)),
    (u"10 欄目の印", MS, "NONCONSOLIDATED_MARK", "ConsolidatedMember", (script_problems, row10_problems)),
    (u"切れない理由の字", MS, "WHY_OPEN", u"閉じていない", (script_problems, cut_problems)),
    (u"切れない理由の並び", MS, "WHYS", (u"札なし", u"decode", u"札が複数", u"続きあり", u"閉じない", u"空"), (script_problems,)),
    (u"profile", MS, "PROFILE", "P32E", (script_problems, judge_problems)),
    (u"乱数の種", MS, "READ_SEED", 20261114, (script_problems, reading_problems)),
    (u"G 連結の本数(60)", MS, "READ_N", 59, (script_problems, reading_problems)),
    (u"本数(201)", MS, "N_ROWS", 200, (script_problems,)),
    (u"群の本数(甲)", MS, "GROUP_COUNTS", collections.OrderedDict([(u"甲", 66), (u"乙", 40), (u"丙", 94)]), (script_problems,)),
    (u"乙の folder", MS, "CACHES", collections.OrderedDict([(u"甲", "edinet"), (u"乙", "edinet-fresh"), (u"丙", "edinet-prior-2026-11-02")]), (script_problems,)),
    (u"読みの組の絞り込み", MS, "READ_SETS", collections.OrderedDict([(u"V 連結", (u"連結", u"VALUE_MISMATCH", False)), (u"V 単体", (u"単体", u"VALUE_MISMATCH", False)),
                                                                     (u"G 連結", (u"連結", u"GROUNDED", False)), (u"G 単体", (u"単体", u"GROUNDED", False))]), (script_problems, reading_problems)),
    (u"V の型を 1 つ減らす", MS, "TYPES_V", collections.OrderedDict(list(MS.TYPES_V.items())[:-1]), (script_problems,)),
    (u"G の型の字", MS, "TYPES_G", collections.OrderedDict([(u"a", MS.TYPES_G[u"a"]), (u"b", MS.TYPES_G[u"b"] + u"。"), (u"c", MS.TYPES_G[u"c"])]), (script_problems,)),
    (u"違うものの字", MS, "DIFFS", (u"項目", u"範囲", u"側", u"時期"), (script_problems,)),
    (u"型を付けた席の字", MS, "TYPED_BY", u"司令塔", (script_problems,)),
    (u"行の欄に 10 欄目が無い", MS, "ROW_COLUMNS", tuple(MS.ROW_COLUMNS[:9]), (script_problems,)),
    (u"封の commit", MS, "SEAL_COMMIT", "0000000", (script_problems,)),
    (u"記録の path", MS, "STATES_REL", "fixtures/xbrl/kam/states.json", (script_problems,)),
    (u"書かない字の検査(docID の形)", MS, "DOCID_RE", re.compile(r"S200[A-Z0-9]{4}"), (clean_problems,)),
)


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_seal_tables_paths_and_key_phrases_are_complete(self):
        self.assertEqual([], seal_problems(self.seal))
        self.assertEqual(201, len(seal_table(self.seal)))

    def test_a_2_a_changed_key_phrase_turns_the_seal_check_red(self):
        for ph in SEAL_PHRASES:
            self.assertIn(ph, self.seal)
            mutated_seal = self.seal.replace(ph, ph[:-1] + u"？")
            self.assertNotEqual(mutated_seal, self.seal)
            self.assertNotEqual([], seal_problems(mutated_seal), ph)

    def test_a_3_a_broken_table_or_prediction_row_turns_it_red(self):
        lines = self.seal.split("\n")
        first = [i for i, ln in enumerate(lines) if ln.startswith("| 1 | 甲 |")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:first] + lines[first + 1:])))                              # 201 行が 200 行
        row5 = [i for i, ln in enumerate(lines) if ln.startswith("| 5 | 甲 |")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:row5] + [lines[row5].replace(u"| 甲 |", u"| 乙 |", 1)] + lines[row5 + 1:])))     # 群の本数
        self.assertNotEqual([], seal_problems("\n".join(lines[:row5] + [lines[row5].replace(u"| 切れた | 0 |", u"| 切れた | 1 |", 1)] + lines[row5 + 1:])))    # 下見の claim
        row6 = [i for i, ln in enumerate(lines) if ln.startswith("| 6 | 甲 |")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:row6] + [lines[row6].replace(u"| 札なし | ― |", u"| 切れた | 2 |", 1)] + lines[row6 + 1:])))    # 下見の切れた本
        self.assertNotEqual([], seal_problems("\n".join(lines[:row5] + [lines[1:][0]] + lines[row5 + 1:])))                  # 行が表でなくなる
        sha1 = seal_table(self.seal)[0][2]
        sha2 = seal_table(self.seal)[1][2]
        self.assertNotEqual([], seal_problems(self.seal.replace(sha2, sha1, 1)))                                          # sha256 の重なり
        self.assertNotEqual([], seal_problems(self.seal.replace(sha1, sha1[:-1] + (u"0" if sha1[-1] != u"0" else u"1"), 1)))   # 表の 1 字は門に留めた sha256 で赤
        k7 = [i for i, ln in enumerate(lines) if ln.startswith("| K-7 |")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:k7] + lines[k7 + 1:])))                                   # 11 行が 10 行
        cells = lines[k7].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:k7] + [" | ".join(cells[:2]) + " |"] + lines[k7 + 1:])))       # 外れ方が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:k7] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[k7 + 1:])))   # 予測が空
        self.assertNotEqual([], seal_problems(self.seal.replace("## §5 ", "## 五 ", 1)))                                  # 節が揃わない
        self.assertNotEqual([], seal_problems(self.seal.replace(RECORD_RELS[1], "fixtures/xbrl/kam/other.json")))          # 記録の path が封に無い
        self.assertNotEqual([], seal_problems(self.seal.replace(u"| **連結** | **計** | **201** | **151** | **480** |", u"| **連結** | **計** | **201** | **151** | **481** |", 1)))   # §0-1 の 5 の計
        self.assertNotEqual([], seal_problems(self.seal.replace(u"| 連結 | 乙 | 40 | 29 | 83 |", u"| 連結 | 乙 | 40 | 29 | 84 |", 1)))   # §0-1 の 5 の群の行
        self.assertIn(u"**36** | **8** | **50** | **214**", self.seal)
        self.assertNotEqual([], seal_problems(self.seal.replace(u"**36** | **8** | **50** | **214**", u"**36** | **8** | **50** | **215**", 1)))

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
        rows = MS.read_population()
        self.assertEqual([(r[0], r[1], r[2]) for r in seal_table(self.seal)], rows)
        self.assertEqual(201, len(rows))
        for rel in (SCRIPT_REL, GATE_REL):
            src = read(rel)
            self.assertEqual([], [r[0] for r in rows if r[2] in src], rel)           # 表の sha256 を 1 本も写していない

    def test_b_3_a_changed_character_in_the_seal_turns_the_comparison_red(self):
        self.assertNotEqual([], script_problems(self.seal.replace(u"`jpcrp_cor:KeyAuditMattersConsolidatedTextBlock`", u"`jpcrp_cor:KeyAuditMattersConsolidatedTextBlocx`")))
        self.assertNotEqual([], script_problems(self.seal.replace(u"`<ix:nonNumeric\\b[^>]*?(/?)>|</ix:nonNumeric>`", u"`<ix:nonNumeric\\b[^>]*?>|</ix:nonNumeric>`")))
        self.assertNotEqual([], script_problems(self.seal.replace(u"(ク) **本当の差の候補**", u"(ク) **本当の差の疑い**")))
        self.assertNotEqual([], script_problems(self.seal.replace(u"(c) 読んでも分けられない", u"(c) 読んでも分けない")))
        self.assertNotEqual([], script_problems(self.seal.replace(u"切れない(閉じない)", u"切れない(閉じていない)")))

    def test_b_4_a_changed_row_reader_turns_the_check_red(self):
        with patched(MS, SEAL_ROW=re.compile(r"^\| (\d+) \| (甲|乙) \| `([0-9a-f]{64})` \| (切れた|札なし) \| (\d+|―) \| (切れた|札なし) \| (\d+|―) \|$", re.M)):
            self.assertNotEqual([], script_problems(self.seal))
        self.assertEqual([], script_problems(self.seal))

    def test_b_5_the_default_places_are_the_new_record_folder(self):
        for rel in RECORD_RELS:
            self.assertTrue(rel.startswith("fixtures/xbrl/kam/"))
        self.assertEqual(os.path.join(ROOT, RECORD_RELS[1]), os.path.join(ROOT, MS.STATES_REL))
        self.assertTrue(MS.default_base().endswith(os.path.join(".cache", "audit-core")))


class EngineZeroTest(unittest.TestCase):
    def test_c_1_the_real_history_has_no_engine_lib_device_or_previous_script_change_since_the_seal(self):
        self.assertEqual([], engine_since_seal_problems())

    @staticmethod
    def _files():
        u"""NOT_TOUCHED_RELS の path に当たる作り物の file(folder は中の file)と、関係の無い file。"""
        dirs = ("adapters", "core", "measure/lib", "fixtures/xbrl/tanshin", "fixtures/xbrl/tanshin_self")
        return [(rel + "/x.py" if rel in dirs else rel) for rel in NOT_TOUCHED_RELS]

    def _repo(self):
        r = PR.Repo()
        files = self._files() + ["measure/free.py"]
        for rel in files:
            r.put(rel)
        r.commit(*files)
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
        for rel in self._files():
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

    def test_c_4_every_not_touched_path_is_a_real_path(self):
        for rel in NOT_TOUCHED_RELS:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)


class OrderTest(unittest.TestCase):
    def test_i_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
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

    def test_i_3_the_order_check_lists_the_script_and_this_gate(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in (SCRIPT_REL, GATE_REL)))
        self.assertEqual((SCRIPT_REL, GATE_REL), ORDER_FILES)
        self.assertEqual("measure/xbrl_kam_2026-11-15.py", SCRIPT_REL)
        self.assertEqual("tests/measure/test_xbrl_kam_seal.py", GATE_REL)


class CutTest(unittest.TestCase):
    def test_d_1_the_cut_rules_hold(self):
        self.assertEqual([], cut_problems())


class JudgeTest(unittest.TestCase):
    def test_f_1_the_book_record_and_the_profile_wiring_hold(self):
        self.assertEqual([], judge_problems())

    def test_f_2_the_tenth_column_follows_the_rule(self):
        self.assertEqual([], row10_problems())

    def test_f_3_the_script_never_writes_a_zip(self):
        src = read(SCRIPT_REL)
        self.assertEqual([], [m for m in re.findall(r"open\([^)]*[\"']wb[\"']", src)])        # ZIP を書く経路が無い(binary で書く open が無い)


class MaterialTest(unittest.TestCase):
    def test_g_1_the_material_is_found_by_sha256_only(self):
        self.assertEqual([], scan_problems())

    def test_g_2_the_population_checks_hold(self):
        self.assertEqual([], population_problems())

    def test_g_3_the_real_population_passes_the_checks(self):
        self.assertEqual(201, len(MS.validate_population(MS.read_population())))

    def test_g_4_the_population_record_follows_the_rules(self):
        self.assertEqual([], population_record_problems())


class StatesTest(unittest.TestCase):
    def test_h_1_the_states_record_is_whole_and_reproducible(self):
        self.assertEqual([], states_problems())
        self.assertEqual([], clean_problems())


class ReadingTest(unittest.TestCase):
    def test_j_1_the_reading_rows_are_drawn_by_the_rule(self):
        self.assertEqual([], reading_problems())

    def test_j_2_the_sheet_is_written_outside_the_repo_only(self):
        self.assertEqual([], repo_problems())
        self.assertEqual([], sheet_problems())

    def test_j_3_the_types_record_follows_the_rules(self):
        self.assertEqual([], types_problems())


class RecordShapeTest(unittest.TestCase):
    def test_n_1_the_production_records_if_present_follow_the_seal(self):
        self.assertEqual([], record_problems())

    def test_n_2_the_record_check_is_green_on_good_records_and_red_on_broken_ones(self):
        self.assertEqual([], record_fixture_problems())


class MutantTest(unittest.TestCase):
    def test_k_1_every_check_is_green_on_the_real_code_and_red_on_each_mutant(self):
        checks = sorted(set(m[5] for m in MUTANTS), key=lambda f: f.__name__)
        for chk in checks:
            self.assertEqual([], chk(), chk.__name__)
        silent = []
        for (label, mod, fn, old, new, chk) in MUTANTS:
            orig = getattr(mod, fn)
            with mutated(mod, fn, old, new), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                got = guard(chk)
            self.assertIs(getattr(mod, fn), orig)
            if not got:
                silent.append(label)
        self.assertEqual([], silent)

    def test_k_2_every_constant_mutant_turns_a_check_red(self):
        seal = read(SEAL_REL)
        silent = []
        for (label, mod, name, val, checks) in CONST_MUTANTS:
            orig = getattr(mod, name)
            with patched(mod, **{name: val}), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                got = [guard(chk, seal) if chk is script_problems else guard(chk) for chk in checks]
            self.assertIs(getattr(mod, name), orig)
            if not any(got):
                silent.append(label)
        self.assertEqual([], silent)

    def test_k_3_a_mutant_is_always_put_back(self):
        orig = MS.cut_inner
        with self.assertRaises(RuntimeError):
            with mutated(MS, "cut_inner", u"depth = 1", u"depth = 0"):
                self.assertIsNot(MS.cut_inner, orig)
                raise RuntimeError("x")
        self.assertIs(MS.cut_inner, orig)
        with self.assertRaises(AssertionError):
            with mutated(MS, "cut_inner", u"this text is not in the function", u"x"):
                pass
        self.assertIs(MS.cut_inner, orig)
        old = MS.READ_N
        with self.assertRaises(RuntimeError):
            with patched(MS, READ_N=1):
                raise RuntimeError("x")
        self.assertEqual(old, MS.READ_N)

    def test_k_4_the_mutant_table_is_big_enough(self):
        self.assertGreaterEqual(len(MUTANTS) + len(CONST_MUTANTS), 15)


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

    def test_l_3_the_script_imports_no_network_module(self):
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
            mod = load_module(SCRIPT_REL, "kam_script_reload_probe")
            self.assertIs(marker, sys.modules["pswap_for_idmap"])                      # 先に居た名前は元の object
            self.assertIs(sentinel, sys.modules["rmix_for_pbind"])
            self.assertIs(mod, sys.modules["kam_script_reload_probe"])                 # 自分の名前は残る
            self.assertIsNot(mod.TS, None)
        finally:
            for k, v in (("pswap_for_idmap", before), ("rmix_for_pbind", before2)):
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
            sys.modules.pop("kam_script_reload_probe", None)

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
            for text, codes, shas in (("x = 'S100" + "ABCD'\n", None, None), ("x = '0812" + "20260810517389'\n", None, None), ("x = 'ab" + "12345cd'\n", ["12345"], None),
                                      ("x = '" + "ab" * 32 + "'\n", None, ["ab" * 32])):
                with open(os.path.join(d, "s.py"), "w") as fh:
                    fh.write(text)
                self.assertNotEqual([], name_problems(rels=("s.py",), base=d, codes=codes, shas=shas), text)

    def test_l_6_the_new_files_carry_no_secret_material_markers(self):
        handoff = u"sgogi-coach" + u"-handoff"                                        # 開かない folder(この file が自分の字に当たらないよう、つないで書く)
        skipped = ST.SKIP_CACHES[0]
        for rel in (SCRIPT_REL, GATE_REL):
            self.assertNotIn(handoff, read(rel), rel)
            self.assertNotIn(skipped, read(rel), rel)                                 # 開かない folder の名前を持たない(3 つの folder だけ読む)

    def test_l_7_the_script_shares_the_previous_instances(self):
        self.assertIs(MS.ST, MS.TSS.ST)
        self.assertIs(MS.TS, MS.TSS.TS)
        self.assertTrue(callable(MS.TS.html_to_lines) and callable(MS.TS.profile_rows))


@unittest.skipUnless(os.environ.get("AUDIT_CORE_KAM_REMEASURE") == "1", u"材料から測り直す試験は AUDIT_CORE_KAM_REMEASURE=1 のときだけ走る")
class RemeasureTest(unittest.TestCase):
    def test_m_1_the_material_reproduces_the_seal_pilot_columns_and_the_k1_to_k4_numbers(self):
        u"""既定の材料(読むだけ)で ``run_states`` を使い捨ての path に走らせ、封 §1 の下見の列(切り出し・claim)と §0-1 の 5 の表の数と本ごとに同じ。本番の path には書かない。"""
        seal = read(SEAL_REL)
        rows = seal_table(seal)
        with tmpdir() as d:
            out = os.path.join(d, "states_remeasure.json")
            MS.run_states(out=out, say=lambda *a, **k: None)
            with io.open(out, encoding="utf-8") as fh:
                rec = json.load(fh)
        got = [(b[u"#"], b[u"群"], b[u"ZIP の sha256"],
                (u"切れた" if b[u"連結"][u"切り出し"] == u"切れた" else b[u"連結"][u"理由"]), (str(b[u"連結"][u"claim"]) if b[u"連結"][u"切り出し"] == u"切れた" else u"―"),
                (u"切れた" if b[u"単体"][u"切り出し"] == u"切れた" else b[u"単体"][u"理由"]), (str(b[u"単体"][u"claim"]) if b[u"単体"][u"切り出し"] == u"切れた" else u"―"))
               for b in rec[u"本"]]
        self.assertEqual([tuple(r) for r in rows], got)
        five = seal_five(seal)
        for side in (u"連結", u"単体"):
            for g, blk in rec[u"集計"][side].items():
                want = five[(side, g)]
                s = blk[u"4 state"]
                self.assertEqual(want, (blk[u"本"], blk[u"切れた"], blk[u"claim"], s[u"GROUNDED"], s[u"VALUE_MISMATCH"], s[u"UNVERIFIABLE"], s[u"POINTER_NOT_FOUND"]), (side, g))
        self.assertEqual((244159, 147934), (rec[u"集計"][u"連結"][u"計"][u"字数の合計"], rec[u"集計"][u"単体"][u"計"][u"字数の合計"]))
        ten = rec[u"集計"][u"単体"][u"計"][u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む)の数"][u"GROUNDED"]
        self.assertEqual((30, 6), (ten[u"真"], ten[u"偽"]))
        self.assertEqual(26, rec[u"集計"][u"連結"][u"計"][u"VALUE_MISMATCH が 1 以上の本"])


if __name__ == "__main__":
    unittest.main()
