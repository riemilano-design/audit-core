# -*- coding: utf-8 -*-
"""封 docs/XBRL_NIL_READ_SEAL_2026-11-17.md(NR ― engine の inline XBRL の読み取りが自己閉じの空の欄を次の fact まで読む欠陥は、過去の便の数にどれだけ効いたか)の門。封 §1〜§4。

**この門が縛るもの**

1. 封の字: 封の commit(720a473d)・path・要点の字・入れ物の棚卸しの数(7 folder)が script の定数と同じ。封の file は commit した blob と 1 字も変わっていない。
2. 入力 6 つの sha256 が script の表と実物で同じ。
3. 直した入力(封 §2-2): 取り除く関数を当たる例・当たらない例で直接呼ぶ。ZIP を作り直す関数は ``XBRL/PublicDoc/`` の ``.htm`` だけを変え、ほかの member・member の順・ほかの bytes を変えない。
4. 独立の読み(封 §2-1)と fact の差(封 §2-3)を、封 §0 の作り物の例(小さい ZIP を memory で作る)で直接呼ぶ。
   **2026-11-17(NRE)で engine の読み取りが自己閉じを始まりの tag と読まなくなったので、この項は「直った後の形」に書き直した**(封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md §2-3 の型 6。同じ作り物で、
   いまの engine が「作られた fact 0・消えた fact 0」を出し、独立の読みと同じ列になる)。**直す前の欠陥の形(作られた fact 1・消えた fact 1)は、直す前の式の写しを使う参照の engine
   (``SGR.nre_old_formula_instance``。engine の字の中の式を封 §1 の「前」の字に戻した memory の module)で残す**(参照の engine で同じ作り物を読むと欠陥の形が出る)。
5. 判定の差(封 §2-4): 移り変わりの表・state が変わった行・reason だけ変わった行・そのままでだけ合う行と直した入力でだけ合う行(向き)を、作り物の行で直接呼ぶ。止まり方(「そのまま」が TSS の記録と違う・独立の読みが engine と違う・行の集合が違う・集計の鍵の集合が違う・棚卸しが封の数と違う)。
6. 棚卸し(封 §1 の 1)と 2026-11-09 の便の ZIP の経路(封 §1 の 3): 経路の判定を 3 つの形の ZIP で、棚卸しを使い捨ての folder で。NR-6 の数を作り物の経路で。
7. 記録 ``fixtures/xbrl/nil_read/states_2026-11-17.json``: 封の字・script の sha256・入力・engine の指紋・行の形(6 欄。文や値や要素名を持たない)・集計が行からの独立の数え直しと一致・「そのまま」の集計の葉が TSS の記録の集計の葉と同じ・
   GROUNDED の数が行と集計で食い違わない・本ごとの欄の合計が全体と一致・予測 NR-1〜NR-6 の判定に要る数が行と本ごとの欄からの数え直しと一致・率の字。
8. engine 0 行: 封の commit から HEAD まで ``core/``・``adapters/``・``measure/lib``・``measure/inject.py`` と入力を触っていない。作業木に未 commit の変更も無い。``tests/adapters/xbrl/test_boundary.py`` の import 一覧は広げない。
9. 順序: 封の commit が script・この門・記録より前(commit の順。未 commit は赤)。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
400 本の作り直しは門の中では走らせない(重い)。``states --check`` は「作り直した記録が在る記録と同じか」しか見ないので、読みの正しさは作り物の ZIP を ``load_instance`` で読む上の 4 で縛る。この file は docID の字を持たない。
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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_nr_seal")       # 順序の部品。門としては走らせない
SGR = load_module("tests/measure/test_xbrl_rmix_seal.py", "rmix_seal_gate_for_nr_seal")      # 宣言された遷移の部品・直す前の式の参照の engine(2026-11-17 NRE)。門としては走らせない
MS = load_module("measure/xbrl_nil_read_2026-11-17.py", "nil_read_script_for_seal_gate")

SEAL_REL = "docs/XBRL_NIL_READ_SEAL_2026-11-17.md"
SEAL_COMMIT_SHORT = "720a473d"                 # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_nil_read_2026-11-17.py"
GATE_REL = "tests/measure/test_xbrl_nil_read_seal.py"
RECORD_REL = "fixtures/xbrl/nil_read/states_2026-11-17.json"
TSS_RECORD_REL = "fixtures/xbrl/tanshin_self/states_2026-11-14.json"
ORDER_FILES = (SCRIPT_REL, GATE_REL, RECORD_REL)
#: 入力の表(literal。script の表と実物の両方と照らす)
INPUT_SHAS = (
    ("fixtures/xbrl/tanshin_self/population_2026-11-14.json", "48ba8e5574be70d85b3d1affacc9403cffbfc698f529c095c6c882cd8ccfa9b0"),
    ("fixtures/xbrl/tanshin_self/states_2026-11-14.json", "00414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"),
    ("measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    ("measure/xbrl_tanshin_self_stage_2026-11-14.py", "4ed60b591366dd65a431dba5348aff6edb3889676d8e9a4154a5b0298486f7f9"),
    ("measure/xbrl_tanshin_2026-11-09.py", "b7ea491bf5cd34c4976bde86c4329583e0d9af09ec8895ea0caf48491492b5bd"),
    ("fixtures/xbrl/tanshin/states_2026-11-09.json", "6779b451b30aa7619923cbc8c390049f682deeb7bf5e198ddb21c9005b6362d4"))
INPUT_RELS = tuple(rel for rel, _sha in INPUT_SHAS)
ENGINE_RELS = ("adapters", "core", "measure/lib", "measure/inject.py")
NOT_TOUCHED_RELS = ENGINE_RELS + INPUT_RELS
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "io", "json", "os", "re", "sys", "time", "zipfile")
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
RATE_TEXT = re.compile(r"^(\d+\.\d%|分母 0)$")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
ROUTES = (u".xbrl の経路", u".htm の経路", u"どちらも無い")
K_FACT, K_JUDGE, K_KEYS, K_PRED, K_INV, K_TB, K_BOOKS = (u"fact の差(封 §2-3)", u"判定の差(封 §2-4)", u"集計の鍵ごと(封 §2-4。[道, そのまま, 直した入力, 差])",
                                                       u"予測の判定に要る数(NR-1〜NR-6。当たり・外れは結果の文書で)", u"棚卸し(封 §1 の 1)", u"2026-11-09 の便の ZIP(封 §1 の 3)", u"本ごと(切れた本だけ)")
#: 封 §0 の作り物の例(Prior の自己閉じの空の欄の直後に、同じ要素の Current の本物の fact)
NIL_TAG = b'<ix:nonFraction name="ex:A" contextRef="Prior" unitRef="JPY" scale="6" xsi:nil="true"/>'
REAL_TAG = b'<ix:nonFraction name="ex:A" contextRef="Current" unitRef="JPY" scale="6">120</ix:nonFraction>'
OTHER_TAG = b'<ix:nonFraction name="ex:B" contextRef="Current" unitRef="JPY" decimals="-6" scale="6">1,234</ix:nonFraction>'


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
    mod = types.ModuleType("nil_read_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def mem_zip(members):
    u"""[(名前, bytes)] から memory の ZIP の bytes。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n, d in members:
            z.writestr(n, d)
    return buf.getvalue()


# ---------------------------------------------------------------- 1. 封の字
def seal_text():
    return read(SEAL_REL)


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.STATES_REL != RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    for phrase in (u"属性の並びが `/` で終わる `<ix:nonFraction …/>` は「空の欄」", u"正規表現 `<ix:nonFraction[^>]*/>` に当たる所を全部消す", u"**作られた fact**", u"**消えた fact**",
                   u"**state が変わった行の数**", u"そのままでは合い、直した入力では合わなくなった行", u"NR-1", u"NR-6", u"`.htm` の経路で自己閉じを持つ本は 0"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    if ms.NIL_TAG_RE.pattern != br"<ix:nonFraction[^>]*/>":
        out.append(u"直した入力の正規表現が封 §2-2 と違う")
    if ms.PROFILE != u"P33E" or ms.STATE_G != u"GROUNDED" or tuple(ms.STATES) != STATES:
        out.append(u"profile か state の名が違う")
    sealed = dict((m.group(1), int(m.group(2))) for m in re.finditer(r"`(edinet|edinet-demo-cabocia|edinet-fresh-2026-10-21|edinet-prior-2026-11-02|tanshin-self-2026-11-14|tanshin-2026-11-09|sheet)` (\d+)", seal))
    if len(sealed) != 7 or dict((k, sum(v)) for k, v in ms.SEALED_INVENTORY.items()) != sealed:
        out.append(u"script の棚卸しの数(7 folder の合計)が封の字の数と違う")
    for k in (u"edinet", u"edinet-demo-cabocia", u"edinet-fresh-2026-10-21", u"edinet-prior-2026-11-02"):
        if tuple(ms.SEALED_INVENTORY[k][1:]) != (0, 0):
            out.append(u"EDINET の folder が .xbrl の経路だけでない: %s" % k)
    for k in (u"tanshin-self-2026-11-14", u"tanshin-2026-11-09", u"sheet"):
        if tuple(ms.SEALED_INVENTORY[k][:2]) != (0, 0):
            out.append(u"どちらも無い folder が違う: %s" % k)
    return out


def seal_history_problems(root=REPO):
    u"""封の file の履歴は 1 commit(720a473d)で、今の file はその commit の blob と 1 字も変わらない。"""
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


# ---------------------------------------------------------------- 3. 直した入力
def strip_problems(ms=None):
    u"""封 §2-2: 当たる例・当たらない例・ほかは 1 byte も変えない。ZIP の作り直しは ``XBRL/PublicDoc/`` の ``.htm`` だけ。"""
    ms = ms or MS
    out = []
    keep = b'<ix:nonFraction name="x" contextRef="c" unitRef="JPY" scale="6">1,234</ix:nonFraction>'
    if ms.strip_nil(NIL_TAG) != (b"", 1):
        out.append(u"封 §0 の自己閉じの tag を取り除かない")
    if ms.strip_nil(b'<ix:nonFraction name="x" xsi:nil="true" />') != (b"", 1):
        out.append(u"空白を挟んだ自己閉じの tag を取り除かない")
    if ms.strip_nil(keep) != (keep, 0):
        out.append(u"値の在る fact(/> で終わらない)を取り除いた")
    body = u"前<b>日本語の字</b>\n".encode("utf-8")
    html = body + NIL_TAG + b"\n" + keep + NIL_TAG + NIL_TAG + body
    if ms.strip_nil(html) != (body + b"\n" + keep + body, 3):
        out.append(u"ほかの bytes を 1 byte も変えずに空の欄だけ取り除いていない")
    if ms.strip_nil(NIL_TAG + REAL_TAG) != (REAL_TAG, 1):
        out.append(u"自己閉じの直後の本物の fact まで取り除いた(貪欲)か残した")
    # ZIP の作り直し: PublicDoc の .htm だけ・順と名前と ZIP の外の member は変えない
    members = [(u"XBRL/PublicDoc/b_ixbrl.htm", NIL_TAG + REAL_TAG), (u"XBRL/PublicDoc/a_ixbrl.htm", REAL_TAG + NIL_TAG + NIL_TAG),
               (u"XBRL/PublicDoc/c.xml", NIL_TAG), (u"XBRLData/Attachment/z-ixbrl.htm", NIL_TAG + REAL_TAG), (u"META-INF/x.txt", b"x")]
    fixed, n = ms.fix_zip(mem_zip(members))
    with zipfile.ZipFile(io.BytesIO(fixed)) as z:
        got = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    want = [(u"XBRL/PublicDoc/b_ixbrl.htm", REAL_TAG), (u"XBRL/PublicDoc/a_ixbrl.htm", REAL_TAG), (u"XBRL/PublicDoc/c.xml", NIL_TAG),
            (u"XBRLData/Attachment/z-ixbrl.htm", NIL_TAG + REAL_TAG), (u"META-INF/x.txt", b"x")]
    if got != want:
        out.append(u"ZIP の作り直しが PublicDoc の .htm だけを変え、順・名前・ほかの member を変えない形になっていない")
    if n != 3:
        out.append(u"取り除いた数が 3 でない(%s)" % n)
    return out


# ---------------------------------------------------------------- 4. 独立の読みと fact の差(封 §0 の作り物の例)
def example_zip(html):
    return mem_zip([(u"XBRL/PublicDoc/x_ixbrl.htm", html)])


def read_problems(ms=None):
    ms = ms or MS
    out = []
    html = NIL_TAG + b"\n" + REAL_TAG                      # 封 §0 の「…」は空白(読み取りの中身が数だけになる形)
    zb = example_zip(html)
    # 2026-11-17(NRE): 直った後の形。engine(いま在るもの。封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md §1 の式)は自己閉じの空の欄を始まりの tag と読まず、
    # 「Current の ex:A が 120 百万」の fact 1 つだけを作る(そのまま = 自己閉じを消した入力。作られた fact 0・消えた fact 0)
    want_cur = {(u"ex:A", u"Current", u"JPY", None, 120000000.0): 1}
    asis = ms.engine_counter(zb)
    if dict(asis) != want_cur:
        out.append(u"engine がいまの読み取りで「Current の ex:A が 120 百万」の fact 1 つにならない(式が自己閉じを始まりの tag と読む疑い): %s" % dict(asis))
    fixed_zb, n = ms.fix_zip(zb)
    fixed = ms.engine_counter(fixed_zb)
    if n != 1 or dict(fixed) != want_cur:
        out.append(u"直した入力を engine に渡しても「Current の ex:A が 120 百万」の fact 1 つにならない: %s" % dict(fixed))
    if asis != fixed or ms.fact_diff(asis, fixed) != (0, 0, 0):
        out.append(u"直した engine で「そのまま」と「自己閉じを消した入力」の fact の列が同じでない(作られた fact 0・消えた fact 0 にならない): %s" % (ms.fact_diff(asis, fixed),))
    # 直す前の欠陥の形は、直す前の式の写しを使う参照の engine で残す: Prior の ex:A が 120 百万を持つ fact 1 つ(作られた)・Current の ex:A は読まない(消えた)
    want_made = {(u"ex:A", u"Prior", u"JPY", None, 120000000.0): 1}
    with patched(ms, I=SGR.nre_old_formula_instance()):
        old_asis = ms.engine_counter(zb)
        old_fixed = ms.engine_counter(fixed_zb)
    if dict(old_asis) != want_made:
        out.append(u"直す前の式の参照の engine が「Prior の ex:A が 120 百万」の fact 1 つにならない(参照が欠陥の形を出さない): %s" % dict(old_asis))
    if dict(old_fixed) != want_cur or ms.fact_diff(old_asis, old_fixed) != (1, 1, 1) or ms.fact_diff(old_asis, fixed) != (1, 1, 1):
        out.append(u"直した入力が、直す前の式の参照の engine でも「Current の ex:A が 120 百万」の fact 1 つにならない(自己閉じを消す直しが効いていない): %s" % dict(old_fixed))
    # 独立の読み(engine を呼ばない)が直した入力の engine と同じ・そのままの入力でも空の欄を fact にしない
    if ms.independent_counter(zb) != fixed or ms.independent_counter(fixed_zb) != fixed or ms.independent_counter(zb) != asis:
        out.append(u"独立の読みが直した入力の engine の fact と違う(直した engine の「そのまま」とも同じ列になる)")
    if dict(ms.independent_counter(example_zip(NIL_TAG + NIL_TAG))) != {}:
        out.append(u"空の欄だけの入力から fact を作った")
    if ms.independent_reads(u"<ix:nonFraction name=\"a\" scale=\"3\" sign=\"-\">1,5</ix:nonFraction>") != [(u"a", None, None, None, -15000.0)]:
        out.append(u"独立の読みの値の式(, を消す・scale・sign)が engine と同じでない")
    if ms.independent_reads(u"<ix:nonFraction name=\"a\">x</ix:nonFraction>") != []:
        out.append(u"数の形でない中身を fact にした")
    # fact の差(向き): 作られた = そのままに在って直した入力に無い・消えた = 逆(欠陥の形は参照の engine の「そのまま」で)
    if ms.fact_diff(old_asis, fixed) != (1, 1, 1):
        out.append(u"fact の差が (作られた 1・消えた 1・期の取り違えの形 1) にならない: %s" % (ms.fact_diff(old_asis, fixed),))
    a = collections.Counter({(u"n", u"c1", u"JPY", None, 1.0): 2, (u"m", u"c1", u"JPY", None, 5.0): 1})
    b = collections.Counter({(u"n", u"c2", u"JPY", None, 3.0): 1, (u"m", u"c1", u"JPY", None, 5.0): 1})
    if ms.fact_diff(a, b) != (2, 1, 2):
        out.append(u"期の取り違えの形の数が作られた fact の個数で数えられていない: %s" % (ms.fact_diff(a, b),))
    if ms.fact_diff(b, a) != (1, 2, 1):
        out.append(u"作られた・消えたの向きが逆になっている: %s" % (ms.fact_diff(b, a),))
    c = collections.Counter({(u"n", u"c1", u"JPY", None, 1.0): 1})
    d = collections.Counter({(u"k", u"c2", u"JPY", None, 3.0): 1})
    if ms.fact_diff(c, d) != (1, 1, 0):
        out.append(u"要素名が違う fact を期の取り違えの形に数えた")
    e = collections.Counter({(u"n", u"c1", u"JPY", None, 1.0): 1})
    f = collections.Counter({(u"n", u"c1", u"JPY", None, 3.0): 1})
    if ms.fact_diff(e, f) != (1, 1, 0):
        out.append(u"context が同じ fact を期の取り違えの形に数えた")
    if ms.fact_diff(e, e) != (0, 0, 0):
        out.append(u"同じ fact の列で差が出た")
    # engine の自己閉じの読み取りの数(属性の列が / で終わる一致)
    if ms.engine_self_reads(zb) != 1 or ms.engine_self_reads(fixed_zb) != 0 or ms.engine_self_reads(example_zip(REAL_TAG + NIL_TAG)) != 0:
        out.append(u"engine の自己閉じの読み取りの数が違う")
    return out


# ---------------------------------------------------------------- 5. 判定の差・止まり方
def row(n, si, pos, a, b, same=True):
    return [n, si, pos, a, b, same]


def judge_problems(ms=None):
    ms = ms or MS
    out = []
    G, VM, UN, PN = STATES
    rows = [row(1, 1, 1, G, G), row(1, 1, 2, VM, G), row(1, 1, 3, PN, G), row(2, 1, 1, G, VM), row(2, 1, 2, UN, UN, False), row(3, 1, 1, UN, UN), row(3, 1, 2, VM, UN, False), row(3, 1, 3, G, UN)]
    jb = ms.judge_block(rows, None)
    t = jb[u"state の移り変わり(そのまま → 直した入力)"]
    if sum(t.values()) != len(rows) or len(t) != 16:
        out.append(u"移り変わりの表が 16 の組・行の数の合計になっていない")
    if t[u"VALUE_MISMATCH → GROUNDED"] != 1 or t[u"GROUNDED → VALUE_MISMATCH"] != 1 or t[u"GROUNDED → UNVERIFIABLE"] != 1 or t[u"GROUNDED → GROUNDED"] != 1:
        out.append(u"移り変わりの表の向き(そのまま → 直した入力)が違う")
    if jb[u"state が変わった行"][u"分子"] != 5 or jb[u"state が変わった行"][u"分母"] != 8:
        out.append(u"state が変わった行の数が違う: %s" % jb[u"state が変わった行"])
    if jb[u"state が変わった行を持つ本"] != 3 or jb[u"state が変わった行を持つ本の #"] != [1, 2, 3]:
        out.append(u"state が変わった行を持つ本が違う")
    if jb[u"state は同じで reason だけ変わった行"] != 1:
        out.append(u"state は同じで reason だけ変わった行の数が違う(state が違う行を数えている・reason の見方が逆)")
    if jb[u"そのままでだけ合う行(作られた fact に頼っていた一致)"] != 2 or jb[u"直した入力でだけ合う行"] != 2:
        out.append(u"そのままでだけ合う行・直した入力でだけ合う行の数か向きが違う: %s" % ((jb[u"そのままでだけ合う行(作られた fact に頼っていた一致)"], jb[u"直した入力でだけ合う行"]),))
    jb2 = ms.judge_block([row(1, 1, 1, G, UN), row(1, 1, 2, G, UN), row(2, 1, 1, PN, G)], None)
    if jb2[u"そのままでだけ合う行(作られた fact に頼っていた一致)"] != 2 or jb2[u"直した入力でだけ合う行"] != 1:
        out.append(u"合う行の 2 方向の向きが逆")
    # pair_rows(行の鍵は同じ並びの対・reason が同じか)
    def book(n, cut, ra, rf):
        return collections.OrderedDict([(u"#", n), (u"切れた", cut), (u"asis", {u"行": ra}), (u"fixed", {u"行": rf})])
    ra = [[1, 2, G, None], [3, 4, VM, u"x"]]
    rf = [[1, 2, G, None], [3, 4, UN, u"y"]]
    got = ms.pair_rows([book(7, True, ra, rf), book(8, False, [[9, 9, G, None]], [[9, 9, G, None]])])
    if got != [[7, 1, 2, G, G, True], [7, 3, 4, VM, UN, False]]:
        out.append(u"対の行が [本の #, 文の番号, 位置, そのまま, 直した入力, reason が同じか] にならない(切れない本の行は入れない): %s" % got)
    try:
        ms.pair_rows([book(7, True, [[1, 2, G, None]], [[1, 3, G, None]])])
        out.append(u"行の鍵が対にならないのに止まらない")
    except ms.Stop:
        pass
    # fact_block(本ごとの欄と全体)
    def fbook(n, nil, made, gone, swap, reads):
        return collections.OrderedDict([(u"#", n), (u"切れた", True), (u"nil", nil), (u"engine の自己閉じの読み取り", reads), (u"fact の差", (made, gone, swap))])
    fb, per = ms.fact_block([fbook(1, 5, 2, 3, 2, 2), fbook(2, 0, 0, 0, 0, 0), fbook(3, 4, 0, 1, 0, 1), collections.OrderedDict([(u"#", 4), (u"切れた", False)])])
    if per != [[1, 5, 2, 3, 2], [2, 0, 0, 0, 0], [3, 4, 0, 1, 0]]:
        out.append(u"本ごとの欄が切れた本だけ [本の #, 自己閉じ, 作られた, 消えた, 期の取り違え] にならない: %s" % per)
    if (fb[u"自己閉じの数(消した数)"], fb[u"自己閉じを 1 つ以上持つ本"], fb[u"作られた fact"], fb[u"消えた fact"], fb[u"作られた fact を持つ本"], fb[u"消えた fact を持つ本"],
            fb[u"作られた fact か消えた fact が 1 つ以上の本"], fb[u"engine の読み取りのうち自己閉じの tag から始まるもの"], fb[u"切れた本"]) != (9, 2, 2, 4, 1, 2, 2, 3, 3):
        out.append(u"fact の差の全体の数が違う: %s" % dict(fb))
    if fb[u"期の取り違えの形(作られた fact のうち)"] != ms.rate(2, 2):
        out.append(u"期の取り違えの形の率の分母が作られた fact でない")
    # 予測の数
    tb = ms.tanshin_0911_block([(1, ROUTES[0], ROUTES[0], 0), (2, ROUTES[1], ROUTES[1], 3), (3, ROUTES[1], ROUTES[1], 0), (4, ROUTES[2], ROUTES[2], 0)])
    if (tb[u"本"], tb[u".htm の経路を通る本"], tb[u".htm の経路で自己閉じを持つ本"], tb[u".htm の経路の本の自己閉じの数の合計"]) != (4, 2, 1, 3):
        out.append(u"2026-11-09 の便の経路の数(NR-6)が違う: %s" % [tb[k] for k in (u"本", u".htm の経路を通る本", u".htm の経路で自己閉じを持つ本")])
    if dict(tb[u"verify_document に渡す ZIP の経路"]) != {ROUTES[0]: 1, ROUTES[1]: 2, ROUTES[2]: 1}:
        out.append(u"経路ごとの本の数が違う")
    tb2 = ms.tanshin_0911_block([(1, ROUTES[0], ROUTES[1], 2)])
    if tb2[u".htm の経路を通る本"] != 1 or tb2[u".htm の経路で自己閉じを持つ本"] != 1:
        out.append(u"zm だけが htm の経路の本を数えない")
    pr = ms.prediction_numbers(fb, jb, per, tb)
    if pr[u"NR-3 そのままでだけ値が合う行"] != 2 or pr[u"NR-2 直した入力でだけ値が合う行・そのままでだけ値が合う行"] != {u"直した入力でだけ": 2, u"そのままでだけ": 2}:
        out.append(u"予測の数の NR-2・NR-3 が違う")
    if pr[u"NR-5 state が変わった行を持つ本 / 自己閉じを持つ本"] != ms.rate(3, 2) or pr[u"NR-1 state が変わった行 / 全部の行"] != ms.rate(5, 8):
        out.append(u"予測の数の NR-1・NR-5 の分子・分母が違う")
    return out


def stop_problems(ms=None):
    u"""止まり方: 「そのまま」が TSS の記録と違う・独立の読みが engine と違う・行の集合が違う・集計の鍵の集合が違う・入力の sha256 が違う・棚卸しが封の数と違う。"""
    ms = ms or MS
    out = []

    def must_stop(label, fn, *a):
        try:
            fn(*a)
            out.append(u"%s のに止まらない" % label)
        except ms.Stop:
            pass
        except BaseException as exc:             # noqa: BLE001
            out.append(u"%s: Stop でない例外 %s" % (label, type(exc).__name__))

    def must_pass(label, fn, *a):
        try:
            fn(*a)
        except BaseException as exc:             # noqa: BLE001
            out.append(u"%s のに止まった: %s" % (label, type(exc).__name__))

    book = collections.OrderedDict([(u"#", 1), (u"行", [[1, 2, u"GROUNDED", None]]), (u"claim", 1)])
    rec = json.loads(json.dumps(book))
    must_pass(u"同じ本", ms.check_asis, 1, book, rec)
    rec2 = json.loads(json.dumps(book))
    rec2[u"claim"] = 2
    must_stop(u"「そのまま」の本が TSS の記録と違う", ms.check_asis, 1, book, rec2)
    c1 = collections.Counter({(u"a", u"c", u"JPY", None, 1.0): 1})
    must_pass(u"同じ fact の列", ms.check_independent, 1, c1, collections.Counter(c1))
    must_stop(u"独立の読みが engine と違う", ms.check_independent, 1, c1, collections.Counter({(u"a", u"c", u"JPY", None, 2.0): 1}))
    must_stop(u"独立の読みが engine より少ない", ms.check_independent, 1, collections.Counter(), c1)
    a = collections.OrderedDict([(u"行", [[1, 2, u"G", None]]), (u"対応", True)])
    must_pass(u"同じ行の集合", ms.check_same_rows, 1, a, collections.OrderedDict(a))
    must_stop(u"行の集合が違う", ms.check_same_rows, 1, a, collections.OrderedDict([(u"行", [[1, 3, u"G", None]]), (u"対応", True)]))
    must_stop(u"行が足りない", ms.check_same_rows, 1, a, collections.OrderedDict([(u"行", []), (u"対応", True)]))
    must_stop(u"対応しない", ms.check_same_rows, 1, a, collections.OrderedDict([(u"行", [[1, 2, u"G", None]]), (u"対応", False)]))
    t1 = collections.OrderedDict([(u"群", collections.OrderedDict([(u"甲", collections.OrderedDict([(u"claim", 3), (u"4 state", collections.OrderedDict([(u"GROUNDED", 2)]))]))]))])
    t2 = json.loads(json.dumps(t1), object_pairs_hook=collections.OrderedDict)
    t2[u"群"][u"甲"][u"claim"] = 5
    tab = ms.key_diff_table(t1, t2)
    if tab != [[u"群/甲/claim", 3, 5, 2], [u"群/甲/4 state/GROUNDED", 2, 2, 0]]:
        out.append(u"集計の鍵の表が [道, そのまま, 直した入力, 差(直した入力 − そのまま)] にならない: %s" % tab)
    t3 = json.loads(json.dumps(t1), object_pairs_hook=collections.OrderedDict)
    t3[u"群"][u"甲"][u"4 state"][u"VALUE_MISMATCH"] = 1
    must_stop(u"集計の鍵の集合が違う", ms.key_diff_table, t1, t3)
    # 入力の sha256(複製の木の 1 byte を変える)
    tmp = tempfile.mkdtemp(prefix="nr_gate_")
    try:
        for rel in INPUT_RELS:
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(ROOT, rel), dst)
        must_pass(u"変えない入力", ms.check_inputs, tmp)
        with open(os.path.join(tmp, INPUT_RELS[1]), "ab") as fh:
            fh.write(b" ")
        must_stop(u"入力の sha256 が違う", ms.check_inputs, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def rate_problems_fn(ms=None):
    ms = ms or MS
    out = []
    for n, d, want in ((1, 3, u"33.3%"), (2, 3, u"66.7%"), (1, 8, u"12.5%"), (1, 16, u"6.3%"), (0, 5, u"0.0%"), (5, 5, u"100.0%"), (3, 0, u"分母 0"), (207, 24531, u"0.8%"), (81, 184, u"44.0%")):
        got = ms.rate(n, d)
        if got != collections.OrderedDict([(u"分子", n), (u"分母", d), (u"率", want)]):
            out.append(u"率が違う: %d/%d → %s" % (n, d, got[u"率"]))
    return out


# ---------------------------------------------------------------- 6. 棚卸しと経路
def route_problems(ms=None):
    ms = ms or MS
    out = []
    if ms.route_of(mem_zip([(u"XBRL/PublicDoc/a.xbrl", b"x"), (u"XBRL/PublicDoc/a_ixbrl.htm", b"x")])) != ROUTES[0]:
        out.append(u".xbrl も .htm も在る ZIP が xbrl の経路にならない(engine は .xbrl を先に読む)")
    if ms.route_of(mem_zip([(u"XBRL/PublicDoc/a_ixbrl.htm", b"x")])) != ROUTES[1]:
        out.append(u".htm だけの ZIP が htm の経路にならない")
    if ms.route_of(mem_zip([(u"XBRLData/Attachment/a-ixbrl.htm", b"x"), (u"XBRL/AuditDoc/a.xbrl", b"x"), (u"XBRL/PublicDoc/a.xml", b"x")])) != ROUTES[2]:
        out.append(u"PublicDoc の外の file だけの ZIP が どちらも無い にならない")
    if ms.route_of(mem_zip([])) != ROUTES[2]:
        out.append(u"空の ZIP が どちらも無い にならない")
    tmp = tempfile.mkdtemp(prefix="nr_inv_")
    try:
        def put(rel, data):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as fh:
                fh.write(data)
        put("f1/a.zip", mem_zip([(u"XBRL/PublicDoc/a.xbrl", b"x")]))
        put("f1/sub/b.zip", mem_zip([(u"XBRL/PublicDoc/b_ixbrl.htm", b"x")]))
        put("f1/c.zip", mem_zip([(u"XBRL/PublicDoc/c_ixbrl.htm", b"x")]))
        put("f2/d.xlsx", mem_zip([(u"xl/x.xml", b"x")]))
        put("f2/e.json", b"{}")
        os.makedirs(os.path.join(tmp, "f3"))
        inv = ms.inventory(tmp)
        want = {u"f1": (1, 2, 0, 3, 0), u"f2": (0, 0, 1, 1, 1), u"f3": (0, 0, 0, 0, 0)}
        got = dict((k, tuple(v[x] for x in (ROUTES + (u"ZIP として読める file", u"ZIP でない file")))) for k, v in inv.items())
        if got != want or list(inv) != [u"f1", u"f2", u"f3"]:
            out.append(u"棚卸しの数が違う: %s" % got)
        try:
            if ms.check_inventory(inv, collections.OrderedDict([(u"f1", (1, 2, 0)), (u"f2", (0, 0, 1))])) != [u"f1", u"f2"]:
                out.append(u"封の数と一致した folder の名の並びが返らない")
        except ms.Stop:
            out.append(u"封の数と同じなのに止まった")
        for label, sealed in ((u"数が違う", {u"f1": (1, 1, 0)}), (u"folder が無い", {u"f9": (0, 0, 0)}), (u"経路が違う", {u"f1": (2, 1, 0)})):
            try:
                ms.check_inventory(inv, collections.OrderedDict(sealed))
                out.append(u"棚卸しが封の数と違う(%s)のに止まらない" % label)
            except ms.Stop:
                pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


# ---------------------------------------------------------------- 7. 記録
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
    u"""記録に文・span・値・要素名・context・会社名・docID が無い(禁止の欄の名前・字の形)。行は [int, int, int, state, state, bool]。"""
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
        if (len(r) != 6 or not all(isinstance(x, int) and not isinstance(x, bool) for x in r[:3]) or r[3] not in STATES or r[4] not in STATES or not isinstance(r[5], bool)):
            out.append(u"行の形が決めと違う")
            break
    for r in rec.get(K_BOOKS, []):
        if len(r) != 5 or not all(isinstance(x, int) and not isinstance(x, bool) and x >= 0 for x in r):
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


def tss_record():
    with open(os.path.join(ROOT, TSS_RECORD_REL), encoding="utf-8") as fh:
        return json.load(fh, object_pairs_hook=collections.OrderedDict)


def leaves(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            for x in leaves(v, path + (k,)):
                yield x
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        yield u"/".join(path), o


def record_problems(ms=None, text=None, with_script_tally=True):
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
    tss = tss_record()
    fp = ms.VD.engine_fingerprint()
    # 2026-11-17(NRE): 記録の指紋 = TSS の記録のもの(T の後・NRE の前の engine)で、今の engine はそこから NRE の宣言された遷移だけ離れている(SGR.nre_record_fingerprint_ok)。記録は作り直さない
    now_fp = collections.OrderedDict((k, fp[k]) for k in ms.FP_KEYS)
    rec_fp = rec.get(u"engine の指紋") or {}
    fp_ok = all(rec_fp.get(k) == now_fp[k] for k in ms.FP_KEYS if k != "adapter_xbrl_py_sha256") and SGR.nre_record_fingerprint_ok(rec_fp.get("adapter_xbrl_py_sha256"), now_fp["adapter_xbrl_py_sha256"])
    if not fp_ok or any(rec[u"engine の指紋"][k] != tss[u"engine の指紋"][k] for k in ms.FP_KEYS):
        out.append(u"記録の engine の指紋が今の engine か TSS の記録のものと違う")
    if rec.get(u"profile") != u"P33E" or rec.get(u"key_leaks") != []:
        out.append(u"profile か key_leaks が違う")
    if tuple(rec.get(u"行の欄", ())) != tuple(ms.ROW_COLUMNS) or tuple(rec.get(u"本ごとの欄", ())) != tuple(ms.BOOK_COLUMNS):
        out.append(u"行の欄・本ごとの欄が違う")
    rows = rec.get(u"行", [])
    books = rec.get(K_BOOKS, [])
    # 行の鍵の一意・本の対応
    keys = [(r[0], r[1], r[2]) for r in rows]
    if len(set(keys)) != len(keys) or keys != sorted(keys):
        out.append(u"行の鍵が一意・並び順でない")
    if [b[0] for b in books] != sorted(set(b[0] for b in books)) or not set(r[0] for r in rows) <= set(b[0] for b in books):
        out.append(u"本ごとの欄が本の # の順・一意でないか、行の本を含まない")
    # TSS の記録からの独立の数え直し
    tss_cut = [b for b in tss[u"本"] if b[u"切り出し"] == u"切れた"]
    if [b[0] for b in books] != [b[u"#"] for b in tss_cut]:
        out.append(u"本ごとの欄の本が TSS の切れた本とそろわない")
    tss_rows = [(b[u"#"], r[0], r[1], r[2], r[3]) for b in tss_cut for r in b[u"行"]]
    if [(r[0], r[1], r[2], r[3]) for r in rows] != [(a[0], a[1], a[2], a[3]) for a in tss_rows]:
        out.append(u"行の鍵と「そのまま」の state が TSS の記録の行と同じ並びでない")
    # 集計の鍵(葉)
    tab = rec.get(K_KEYS, [])
    tss_leaves = list(leaves(tss[u"集計"]))
    if [(t[0], t[1]) for t in tab] != tss_leaves:
        out.append(u"集計の鍵の「そのまま」の列が TSS の記録の集計の葉と同じでない")
    if any(t[3] != t[2] - t[1] or len(t) != 4 for t in tab):
        out.append(u"集計の鍵の差が 直した入力 − そのまま でない")
    g_as = sum(t[1] for t in tab if re.fullmatch(u"群/[甲乙丙]/4 state/GROUNDED", t[0]))
    g_fx = sum(t[2] for t in tab if re.fullmatch(u"群/[甲乙丙]/4 state/GROUNDED", t[0]))
    if g_as != sum(1 for r in rows if r[3] == u"GROUNDED") or g_fx != sum(1 for r in rows if r[4] == u"GROUNDED"):
        out.append(u"集計の GROUNDED の数が行からの数え直しと違う")
    c_as = sum(t[1] for t in tab if re.fullmatch(u"群/[甲乙丙]/claim", t[0]))
    c_fx = sum(t[2] for t in tab if re.fullmatch(u"群/[甲乙丙]/claim", t[0]))
    if c_as != len(rows) or c_fx != len(rows):
        out.append(u"集計の claim の合計が行の数と違う")
    for st in STATES:
        if sum(t[2] for t in tab if re.fullmatch(u"群/[甲乙丙]/4 state/%s" % st, t[0])) != sum(1 for r in rows if r[4] == st):
            out.append(u"集計の %s(直した入力)が行からの数え直しと違う" % st)
        if sum(t[1] for t in tab if re.fullmatch(u"群/[甲乙丙]/4 state/%s" % st, t[0])) != sum(1 for r in rows if r[3] == st):
            out.append(u"集計の %s(そのまま)が行からの数え直しと違う" % st)
    # 判定の差(行からの独立の数え直し)
    jb = rec.get(K_JUDGE, {})
    trans = collections.Counter((r[3], r[4]) for r in rows)
    if jb.get(u"行の数(切れた本の全部の行)") != len(rows):
        out.append(u"判定の差の行の数が行の数と違う")
    t = jb.get(u"state の移り変わり(そのまま → 直した入力)", {})
    if t != collections.OrderedDict((u"%s → %s" % (a, b), trans.get((a, b), 0)) for a in STATES for b in STATES) or sum(t.values()) != len(rows):
        out.append(u"移り変わりの表が行からの数え直しと違う(合計が行の数でない)")
    changed = [r for r in rows if r[3] != r[4]]
    if jb.get(u"state が変わった行") != ms.rate(len(changed), len(rows)) or jb.get(u"state が変わった行を持つ本") != len(set(r[0] for r in changed)) \
            or jb.get(u"state が変わった行を持つ本の #") != sorted(set(r[0] for r in changed)):
        out.append(u"state が変わった行・本の数が行からの数え直しと違う")
    if jb.get(u"state は同じで reason だけ変わった行") != sum(1 for r in rows if r[3] == r[4] and not r[5]):
        out.append(u"reason だけ変わった行の数が行からの数え直しと違う")
    only_as = sum(1 for r in rows if r[3] == u"GROUNDED" and r[4] != u"GROUNDED")
    only_fx = sum(1 for r in rows if r[3] != u"GROUNDED" and r[4] == u"GROUNDED")
    if jb.get(u"そのままでだけ合う行(作られた fact に頼っていた一致)") != only_as or jb.get(u"直した入力でだけ合う行") != only_fx:
        out.append(u"合う行の 2 方向の数が行からの数え直しと違う")
    # fact の差(本ごとの欄からの数え直し)
    fb = rec.get(K_FACT, {})
    if (fb.get(u"切れた本"), fb.get(u"自己閉じの数(消した数)"), fb.get(u"自己閉じを 1 つ以上持つ本"), fb.get(u"作られた fact"), fb.get(u"消えた fact"), fb.get(u"作られた fact を持つ本"),
            fb.get(u"消えた fact を持つ本"), fb.get(u"作られた fact か消えた fact が 1 つ以上の本")) != (
            len(books), sum(b[1] for b in books), sum(1 for b in books if b[1] > 0), sum(b[2] for b in books), sum(b[3] for b in books), sum(1 for b in books if b[2] > 0),
            sum(1 for b in books if b[3] > 0), sum(1 for b in books if b[2] > 0 or b[3] > 0)):
        out.append(u"fact の差の全体の数が本ごとの欄からの数え直しと違う")
    if fb.get(u"期の取り違えの形(作られた fact のうち)") != ms.rate(sum(b[4] for b in books), sum(b[2] for b in books)) or any(b[4] > b[2] for b in books):
        out.append(u"期の取り違えの形の数が本ごとの欄からの数え直しと違う")
    if any(b[2] > 0 and b[1] == 0 for b in books) or any(b[3] > 0 and b[1] == 0 for b in books):
        out.append(u"自己閉じが 0 なのに作られた fact か消えた fact が在る本(直した入力が効いていない疑い)")
    # 棚卸し・2026-11-09 の便
    inv = rec.get(K_INV, {})
    per = inv.get(u"folder ごと", {})
    if any(sum(v[r] for r in ROUTES) != v[u"ZIP として読める file"] for v in per.values()):
        out.append(u"棚卸しの folder の経路の合計が ZIP として読める file の数と違う")
    if inv.get(u"経路ごとの合計") != collections.OrderedDict((r, sum(v[r] for v in per.values())) for r in ROUTES) or inv.get(u"ZIP として読める file の合計") != sum(v[u"ZIP として読める file"] for v in per.values()):
        out.append(u"棚卸しの合計が folder ごとの数からの数え直しと違う")
    if [k for k in ms.SEALED_INVENTORY] != inv.get(u"封が字で書いた数と一致した folder") or any(tuple(per[k][r] for r in ROUTES) != tuple(v) for k, v in ms.SEALED_INVENTORY.items()):
        out.append(u"棚卸しが封の字の数と違う")
    tb = rec.get(K_TB, {})
    tbl = [r for r in tb.get(u"本ごと([その便の表の行番号, verify_document の経路, build_raw_claims の経路, 自己閉じの数])", [])]
    if ms.tanshin_0911_block([tuple(r) for r in tbl]) != tb or tb.get(u"本") != len(tbl) or sum(tb.get(u"verify_document に渡す ZIP の経路", {}).values()) != len(tbl):
        out.append(u"2026-11-09 の便の経路の数が本ごとからの数え直しと違う")
    # 予測の判定に要る数
    pr = rec.get(K_PRED, {})
    if pr.get(u"NR-1 state が変わった行 / 全部の行") != ms.rate(len(changed), len(rows)) or pr.get(u"NR-3 そのままでだけ値が合う行") != only_as \
            or pr.get(u"NR-2 直した入力でだけ値が合う行・そのままでだけ値が合う行") != collections.OrderedDict([(u"直した入力でだけ", only_fx), (u"そのままでだけ", only_as)]) \
            or pr.get(u"NR-4 期の取り違えの形の作られた fact / 作られた fact") != fb.get(u"期の取り違えの形(作られた fact のうち)") \
            or pr.get(u"NR-5 state が変わった行を持つ本 / 自己閉じを持つ本") != ms.rate(len(set(r[0] for r in changed)), sum(1 for b in books if b[1] > 0)) \
            or pr.get(u"NR-6 2026-11-09 の便の ZIP のうち .htm の経路で自己閉じを持つ本") != collections.OrderedDict([(u"分子", tb.get(u".htm の経路で自己閉じを持つ本")), (u"分母", tb.get(u"本"))]):
        out.append(u"予測の判定に要る数が行・本ごとの欄からの数え直しと違う")
    # 「0」が出たときの自分の欠陥の疑い(直した入力が効いていること・差が実在すること)
    if not (len(rows) > 20000 and fb.get(u"消えた fact", 0) > 0 and fb.get(u"作られた fact", 0) > 0 and len(changed) > 0):
        out.append(u"差が 0 か行が少なすぎる(直した入力が効いていない・行の対応の鍵の取り違えを疑う)")
    if with_script_tally and not out:
        tb_rows = [list(r) for r in rows]
        jb2 = ms.judge_block(tb_rows, None)
        if jb2 != jb:
            out.append(u"script の判定の集計関数が記録の行から同じ数を作らない")
    return out


# ---------------------------------------------------------------- 8. 配線
def import_problems(src=None):
    u"""script の import は標準ライブラリの一覧と engine の adapters.xbrl の 2 module(instance・verify_document)だけ。通信・subprocess を import しない(ast)。"""
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
                if not (nm.startswith(u"adapters.xbrl.") and nm.split(".")[2] in (u"instance", u"verify_document")):
                    out.append(u"許す engine の module の外: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    return out


def boundary_problems():
    p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
    with open(p, encoding="utf-8") as fh:
        t = fh.read()
    return [u"test_boundary.py にこの便の名前が在る"] if (u"nil_read" in t) else []


def engine_since_seal_problems(root=REPO):
    c = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(c) != 1:
        return [u"封の commit が履歴に 1 つに決まらない"]
    rc, log = PR.git_in(root, "log", "--format=%H", "%s..HEAD" % c[0], "--", *[PREFIX + r for r in NOT_TOUCHED_RELS])
    if rc != 0:
        return [u"git log が失敗した"]
    # 2026-11-17(NRE): 封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md §2-3 が宣言した遷移(instance.py の式 1 行の置き換え 1・1)だけを許す。NRE の engine の commit ただ 1 つで、その commit の NOT_TOUCHED_RELS への変更が宣言の行だけのときに限り一覧から外す(SGR.nre_explained_commit。他の commit・他の行は問題のまま)
    return [u"封の後に engine・lib・入力を触った commit %s" % x[:7] for x in log.split() if x and not SGR.nre_explained_commit(root, x, [PREFIX + r for r in NOT_TOUCHED_RELS])]


def engine_worktree_problems(root=REPO):
    rc, st = PR.git_in(root, "status", "--porcelain", "--untracked-files=all", "--", *[PREFIX + r for r in NOT_TOUCHED_RELS])
    if rc != 0:
        return [u"git status が失敗した"]
    return [u"engine・lib・入力に未 commit の変更: %s" % ln.strip()[:2] for ln in st.splitlines() if ln.strip()]


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(ORDER_FILES) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 8b. 配線(script の states_job・build_record・tanshin_0911 を作り物で実走させる)
#: 外の部品(TSS の cut・wrap・judge_book・tally、2026-11-09 の script の読み込み、profile_rows)だけ作り物に差し替え、script の中の配線そのものを走らせる。
PD = u"XBRL/PublicDoc/"
NIL_C = b'<ix:nonFraction name="ex:C" contextRef="Prior" unitRef="JPY" scale="6" xsi:nil="true"/>'
REAL_C = b'<ix:nonFraction name="ex:C" contextRef="Current" unitRef="JPY" scale="6">120</ix:nonFraction>'
#: 封 §0 の例(自己閉じ 1 つ + 次の fact)。作られた 1・消えた 1・期の取り違えの形 1
SCEN_A = NIL_TAG + b"\n" + REAL_TAG
#: 作られた 1・消えた 2(向きを入れ替えると数が変わる)。2 つ目の自己閉じは次の fact との間に字が在り、読み取りが数にならない
SCEN_B = NIL_TAG + b"\n" + REAL_TAG + b"\n" + NIL_C + b"text" + REAL_C
SCEN_FACTS = {u"A": (SCEN_A, 1, 1, (1, 1, 1), 1), u"B": (SCEN_B, 2, 2, (1, 2, 1), 2)}      # (html, 自己閉じの数, engine の自己閉じの読み取り, fact の差, 直した入力の fact の数)


def strip_expected(html):
    return re.sub(br"<ix:nonFraction[^>]*/>", b"", html)           # 門自身の独立の式(script の関数を使わない)


def zb_members(zb):
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        return [(n, z.read(n)) for n in z.namelist()]


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


def fake_asis(ms, n, grp, kind, sha, zb):
    cut = zb.startswith(b"cut")
    return collections.OrderedDict([
        (u"#", n), (u"群", grp), (u"様式の種類", kind), (u"ZIP の sha256", sha), (u"切り出し", ms.TSS.CUT_OK if cut else u"切れない"),
        (u"行", [[1, 1, u"GROUNDED", u"r-GROUNDED"]] if cut else []), (u"対応", True)])


def fake_parts(ms, spy, wrapped, rows_key=(1, 1)):
    u"""外の部品の作り物。呼ばれた引数を ``spy`` に残す。profile_rows の state は受け取った ZIP の自己閉じの有無で決まる(自己閉じが在れば GROUNDED・無ければ UNVERIFIABLE)。"""
    def judge_book(n, grp, kind, sha, zb):
        spy.setdefault("judge_book", []).append(zb)
        return fake_asis(ms, n, grp, kind, sha, zb)

    def cut(zb):
        spy.setdefault("cut", []).append(zb)
        return u"text", 7, None

    def wrap(zb, text):
        spy.setdefault("wrap", []).append((zb, text))
        return wrapped, 1

    def profile_rows(a, b, c, profile):
        spy.setdefault("profile_rows", []).append((a, b, c, profile))
        has_nil = any(b'xsi:nil="true"' in d for _n, d in zb_members(a))
        return collections.OrderedDict([(rows_key, u"GROUNDED" if has_nil else u"UNVERIFIABLE")]), True, 1

    tss = ns(ms.TSS, judge_book=judge_book, cut=cut, wrap=wrap)
    ts = ns(ms.TS, profile_rows=profile_rows, row_entry=lambda k, v: [k[0], k[1], v, u"r-" + v])
    return tss, ts


def spy_counter(spy, key, fn, extra=False):
    def f(zb):
        spy.setdefault(key, []).append(zb)
        c = fn(zb)
        if extra:
            c = collections.Counter(c)
            c[(u"ex:Z", u"Current", u"JPY", None, 1.0)] += 1
        return c
    return f


def old_engine_counter(ms):
    u"""直す前の式の参照の engine(``SGR.nre_old_formula_instance``)で fact の多重集合を作る関数。配線の試験が「作られた fact と消えた fact の数が違う非対称な例」を保つために使う
    (2026-11-17 NRE で engine が直ったので、いまの engine では差が 0 になる。配線の試験の数は参照の engine で作る)。"""
    mod = SGR.nre_old_formula_instance()

    def engine_counter(zb):
        return collections.Counter((f["name"], f["context"], f["unit"], f["decimals"], f["value"]) for f in mod.load_instance(zb)["facts"])
    return engine_counter


def run_job(ms, html, cut=True, bad_rec=False, engine_extra=False, rows_key=(1, 1), old=True):
    u"""``ms.states_job`` を作り物の 1 本で走らせる。(spy, 結果, 例外, ファイルの bytes)。``old`` が真なら fact の多重集合を直す前の式の参照の engine で作り、偽ならいまの engine で作る。"""
    spy = {}
    content = (b"cut-" if cut else b"nocut-") + b"material"
    sha = hashlib.sha256(content).hexdigest()
    tmp = tempfile.mkdtemp(prefix="nr_job_")
    try:
        path = os.path.join(tmp, sha + ".zip")
        with open(path, "wb") as fh:
            fh.write(content)
        wrapped = example_zip(html)
        tss, ts = fake_parts(ms, spy, wrapped, rows_key)
        rec_book = json.loads(json.dumps(fake_asis(ms, 1, u"甲", u"k", sha, content)), object_pairs_hook=collections.OrderedDict)
        if bad_rec:
            rec_book[u"対応"] = False
        over = dict(TSS=tss, TS=ts, independent_counter=spy_counter(spy, "independent", ms.independent_counter),
                    engine_counter=spy_counter(spy, "engine", old_engine_counter(ms) if old else ms.engine_counter, engine_extra))
        with patched(ms, **over):
            try:
                return spy, ms.states_job((1, u"甲", u"k", sha, path, rec_book)), None, content, wrapped
            except BaseException as exc:                 # noqa: BLE001
                return spy, None, exc, content, wrapped
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def job_wire_problems(ms=None):
    u"""``states_job`` の配線: 判定は直した ZIP で・独立の読みは包んだままの側で・fact の差の向き・自己閉じの数・engine の自己閉じの読み取り・止まり方。"""
    ms = ms or MS
    out = []
    for label, (html, want_nil, want_reads, want_diff, want_facts) in sorted(SCEN_FACTS.items()):
        spy, res, exc, content, wrapped = run_job(ms, html)
        if exc is not None or res is None:
            out.append(u"%s: states_job が落ちた %s" % (label, type(exc).__name__))
            continue
        fixed_members = [(PD + u"x_ixbrl.htm", strip_expected(html))]
        if spy.get("judge_book") != [content]:
            out.append(u"%s: 「そのまま」の判定が材料の ZIP に掛かっていない" % label)
        pr = spy.get("profile_rows", [])
        if len(pr) != 1 or zb_members(pr[0][0]) != fixed_members or zb_members(pr[0][2]) != fixed_members or pr[0][1] is not None or pr[0][3] != ms.PROFILE:
            out.append(u"%s: 直した入力の判定が、自己閉じを消した ZIP に掛かっていない(包んだままに掛けた疑い)" % label)
        if [zb_members(z) for z in spy.get("independent", [])] != [zb_members(wrapped)]:
            out.append(u"%s: 独立の読みが包んだままの ZIP に掛かっていない(確かめが空回りする疑い)" % label)
        eng = spy.get("engine", [])
        if len(eng) != 2 or zb_members(eng[0]) != zb_members(wrapped) or zb_members(eng[1]) != fixed_members:
            out.append(u"%s: engine の fact の多重集合が(包んだまま, 直した入力)の順・組で作られていない" % label)
        if res.get(u"nil") != want_nil:
            out.append(u"%s: 自己閉じの数が違う: %s" % (label, res.get(u"nil")))
        if res.get(u"engine の自己閉じの読み取り") != want_reads:
            out.append(u"%s: engine の自己閉じの読み取りの数が違う: %s" % (label, res.get(u"engine の自己閉じの読み取り")))
        if res.get(u"fact の差") != want_diff:
            out.append(u"%s: fact の差が(作られた・消えた・期の取り違えの形)=%s にならない: %s" % (label, want_diff, res.get(u"fact の差")))
        if res[u"fixed"].get(u"fact の数") != want_facts:
            out.append(u"%s: 直した入力の fact の数が違う" % label)
        if res[u"fixed"].get(u"行") != [[1, 1, u"UNVERIFIABLE", u"r-UNVERIFIABLE"]] or res[u"asis"].get(u"行") != [[1, 1, u"GROUNDED", u"r-GROUNDED"]]:
            out.append(u"%s: 行(そのまま・直した入力)が判定の側に結ばれていない" % label)
        if res.get(u"切れた") is not True:
            out.append(u"%s: 切れた本を切れたとしない" % label)
    # 2026-11-17(NRE): いまの engine(直った後)では、同じ作り物で作られた fact 0・消えた fact 0(そのまま = 自己閉じを消した入力)。判定は直した ZIP・独立の読みは包んだままの側のまま
    for label, (html, want_nil, want_reads, _want_diff, want_facts) in sorted(SCEN_FACTS.items()):
        spy, res, exc, content, wrapped = run_job(ms, html, old=False)
        if exc is not None or res is None:
            out.append(u"%s(いまの engine): states_job が落ちた %s" % (label, type(exc).__name__))
            continue
        if res.get(u"fact の差") != (0, 0, 0) or res[u"fixed"].get(u"fact の数") != want_facts or res.get(u"nil") != want_nil:
            out.append(u"%s(いまの engine): fact の差が(0, 0, 0)・自己閉じの数・fixed の fact の数にならない: %s" % (label, res.get(u"fact の差")))
        eng = spy.get("engine", [])
        if len(eng) != 2 or zb_members(eng[0]) != zb_members(wrapped):
            out.append(u"%s(いまの engine): engine の fact の多重集合が(包んだまま, 直した入力)の順で作られていない" % label)
    # 切れない本: 直した入力を作らず、そのまま = 直した入力
    spy, res, exc, content, wrapped = run_job(ms, SCEN_A, cut=False)
    if exc is not None or res is None or res[u"切れた"] or res[u"fixed"] is not res[u"asis"] or u"nil" in res or spy.get("profile_rows") or spy.get("wrap"):
        out.append(u"切れない本が wrap・判定に進んだか、結果の形が違う")
    # 止まり方(配線の中の検査が呼ばれている)
    for label, kw in ((u"「そのまま」が TSS の記録と違う", dict(bad_rec=True)), (u"独立の読みが engine と違う", dict(engine_extra=True)), (u"行の集合が違う", dict(rows_key=(1, 2)))):
        spy, res, exc, content, wrapped = run_job(ms, SCEN_B, **kw)
        if not isinstance(exc, ms.Stop):
            out.append(u"%s のに states_job が止まらない(%s)" % (label, type(exc).__name__ if exc is not None else u"通った"))
    return out


def record_wire_problems(ms=None):
    u"""``build_record`` の配線: 「直した入力」の集計は直した入力の行から作る・行の対・本ごとの欄・集計の鍵ごとの差・2026-11-09 の便の数が記録の欄に入る。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="nr_rec_")
    try:
        spy = {}
        wrapped = example_zip(SCEN_B)
        files = {1: b"cut-material-1", 2: b"nocut-material-2"}
        shas = dict((n, hashlib.sha256(c).hexdigest()) for n, c in files.items())
        for n, c in files.items():
            with open(os.path.join(tmp, shas[n] + ".zip"), "wb") as fh:
                fh.write(c)
        pop = [(1, u"甲", u"k1", shas[1]), (2, u"甲", u"k2", shas[2])]
        tss, ts = fake_parts(ms, spy, wrapped)

        def tally(books):
            g = sum(1 for b in books for r in b[u"行"] if r[2] == u"GROUNDED")
            return collections.OrderedDict([(u"群", collections.OrderedDict([(u"甲", collections.OrderedDict([
                (u"claim", sum(len(b[u"行"]) for b in books)), (u"4 state", collections.OrderedDict([(u"GROUNDED", g)]))]))]))])

        tss = ns(tss, tally=tally)
        rec_books = [json.loads(json.dumps(fake_asis(ms, n, u"甲", u"k%d" % n, shas[n], files[n])), object_pairs_hook=collections.OrderedDict) for n in (1, 2)]
        states_in = collections.OrderedDict([(u"profile", u"P33E"), (u"本", rec_books), (u"集計", json.loads(json.dumps(tally(rec_books)), object_pairs_hook=collections.OrderedDict))])
        route_rows = [(1, ROUTES[0], ROUTES[1], 2)]
        inv = collections.OrderedDict([(u"f", collections.OrderedDict([(r, 0) for r in ROUTES] + [(u"ZIP として読める file", 0), (u"ZIP でない file", 0)]))])
        st = ns(ms.ST, validate_population=lambda p, a, b: p, read_population=lambda root: pop, names_snapshot=lambda d: 0, display_path=lambda p: u"x")
        ts = ns(ts, NF=types.SimpleNamespace(map_pool=lambda f, jobs, procs: [f(j) for j in jobs]))
        over = dict(TSS=tss, TS=ts, ST=st, independent_counter=ms.independent_counter, engine_counter=old_engine_counter(ms), material_dir=lambda m, o, r: (tmp, True), check_inputs=lambda root: [],
                    inventory=lambda base: inv, check_inventory=lambda i: [], check_population=lambda r, p: None, load_json=lambda p: states_in,
                    engine_fp=lambda s: collections.OrderedDict(), cache_base_dir=lambda: tmp)
        with patched(ms, **over):
            try:
                rec = ms.build_record(root=tmp, procs=1, material=tmp, out=None, say=lambda *a, **k: None, clock=lambda: 0.0, base=tmp, tanshin_rows=route_rows)
            except BaseException as exc:                  # noqa: BLE001
                return [u"build_record が作り物の入力で落ちた: %s" % type(exc).__name__]
        if rec[u"行"] != [[1, 1, 1, u"GROUNDED", u"UNVERIFIABLE", False]]:
            out.append(u"行の対が [本の #, 文の番号, 位置, そのまま, 直した入力, reason が同じか] にならない: %s" % rec[u"行"])
        if rec[K_KEYS] != [[u"群/甲/claim", 1, 1, 0], [u"群/甲/4 state/GROUNDED", 1, 0, -1]]:
            out.append(u"集計の鍵ごとの差が「直した入力の行から作った集計」− 「そのままの集計」になっていない(直した入力の集計をそのまま側から作った疑い): %s" % rec[K_KEYS])
        fb = rec[K_FACT]
        if (fb[u"切れた本"], fb[u"自己閉じの数(消した数)"], fb[u"作られた fact"], fb[u"消えた fact"], fb[u"engine の読み取りのうち自己閉じの tag から始まるもの"]) != (1, 2, 1, 2, 2) \
                or fb[u"期の取り違えの形(作られた fact のうち)"] != ms.rate(1, 1):
            out.append(u"fact の差の全体の数が違う: %s" % dict(fb))
        if rec[K_BOOKS] != [[1, 2, 1, 2, 1]]:
            out.append(u"本ごとの欄が違う: %s" % rec[K_BOOKS])
        jb = rec[K_JUDGE]
        if jb[u"state が変わった行"] != ms.rate(1, 1) or jb[u"そのままでだけ合う行(作られた fact に頼っていた一致)"] != 1 or jb[u"直した入力でだけ合う行"] != 0:
            out.append(u"判定の差が行の対から数えられていない")
        if rec[K_TB] != ms.tanshin_0911_block(route_rows):
            out.append(u"2026-11-09 の便の数が記録の欄に入っていない")
        if rec[K_PRED][u"NR-6 2026-11-09 の便の ZIP のうち .htm の経路で自己閉じを持つ本"] != collections.OrderedDict([(u"分子", 1), (u"分母", 1)]):
            out.append(u"予測 NR-6 の分子・分母が違う")
        # 「そのまま」の集計が TSS の記録の集計と違えば止まる
        bad = collections.OrderedDict(states_in)
        bad[u"集計"] = json.loads(json.dumps(states_in[u"集計"]), object_pairs_hook=collections.OrderedDict)
        bad[u"集計"][u"群"][u"甲"][u"claim"] += 1
        with patched(ms, **dict(over, load_json=lambda p: bad)):
            try:
                ms.build_record(root=tmp, procs=1, material=tmp, out=None, say=lambda *a, **k: None, clock=lambda: 0.0, base=tmp, tanshin_rows=route_rows)
                out.append(u"「そのまま」の集計が TSS の記録と違うのに build_record が止まらない")
            except ms.Stop:
                pass
            except BaseException as exc:                  # noqa: BLE001
                out.append(u"集計の食い違いで Stop でない例外 %s" % type(exc).__name__)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def tanshin_wire_problems(ms=None):
    u"""``tanshin_0911`` の配線(便 2026-11-09 の経路の数え): どの ZIP の経路を数えたか・どの ZIP に自己閉じを数えたか・build_modified_zip に渡す引数。"""
    ms = ms or MS
    out = []
    zb1 = mem_zip([(PD + u"a.xbrl", b"x")])                                  # xbrl の経路
    zm1 = mem_zip([(PD + u"a_ixbrl.htm", NIL_TAG + REAL_TAG + NIL_TAG)])     # htm の経路・自己閉じ 2
    zb2 = mem_zip([(PD + u"b_ixbrl.htm", NIL_TAG + NIL_TAG + NIL_TAG)])      # htm の経路・自己閉じ 3
    zm2 = mem_zip([(PD + u"b.xbrl", b"x")])
    zips = {u"r1": (zb1, zm1), u"r2": (zb2, zm2)}
    calls = {"read": [], "mod": []}

    def load_books(root):
        return [(1, 0, 0, 0, 0, 0, u"r1", u"t1"), (2, 0, 0, 0, 0, 0, u"r2", u"t2")]

    def read_zip(row, caches):
        calls["read"].append((row, caches))
        return zips[row][0]

    def build_modified_zip(zb, text):
        calls["mod"].append((zb, text))
        return zips[u"r1" if text == u"t1" else u"r2"][1], None

    ts = ns(ms.TS, load_books=load_books, GEN=types.SimpleNamespace(read_zip=read_zip, EXISTING_CACHES=u"caches"), PR=types.SimpleNamespace(build_modified_zip=build_modified_zip))
    with patched(ms, TS=ts):
        try:
            got = ms.tanshin_0911(ROOT)
        except BaseException as exc:                      # noqa: BLE001
            return [u"tanshin_0911 が作り物で落ちた: %s" % type(exc).__name__]
    if got != [(1, ROUTES[0], ROUTES[1], 2), (2, ROUTES[1], ROUTES[0], 0)]:
        out.append(u"便 2026-11-09 の経路(verify_document の経路・build_raw_claims の経路・自己閉じの数)が数えた ZIP と結ばれていない: %s" % got)
    if calls["read"] != [(u"r1", u"caches"), (u"r2", u"caches")] or calls["mod"] != [(zb1, u"t1"), (zb2, u"t2")]:
        out.append(u"build_modified_zip・read_zip に渡す引数が(その本の ZIP, その本の文)になっていない")
    return out


# ---------------------------------------------------------------- 変異
#: (名前, script の中の字 old, new, 赤になるはずの検査の名前の並び)。old は script に 1 回だけ在る字
MUTANTS = (
    (u"M01 直した入力の正規表現を > で終わる形にする(本物の fact も消す)", u'NIL_TAG_RE = re.compile(br"<ix:nonFraction[^>]*/>")', u'NIL_TAG_RE = re.compile(br"<ix:nonFraction[^>]*>")', ("seal", "strip", "read")),
    (u"M02 直した入力の正規表現を貪欲にする(本物の fact にまたがる)", u'NIL_TAG_RE = re.compile(br"<ix:nonFraction[^>]*/>")', u'NIL_TAG_RE = re.compile(br"<ix:nonFraction.*/>")', ("seal", "strip")),
    (u"M03 直した入力が PublicDoc の外の member も変える", u"if info.filename.startswith(PUBLIC_DOC) and info.filename.endswith(\".htm\"):", u"if info.filename.endswith(\".htm\"):", ("strip",)),
    (u"M04 直した入力を作らず包んだ ZIP をそのまま返す", u"            out.writestr(TSS._info(info.filename), data)\n    return buf.getvalue(), total", u"            out.writestr(TSS._info(info.filename), z.read(info.filename))\n    return buf.getvalue(), total", ("strip", "read")),
    (u"M05 独立の読みが自己閉じを飛ばさない", u'        if m.group(1).endswith("/"):\n            pos = m.end()\n            continue\n', u"", ("read",)),
    (u"M06 独立の読みの sign を見ない", u'    if a.get("sign") == "-":\n        val = -val\n    return (a.get("name")', u'    return (a.get("name")', ("read",)),
    (u"M07 独立の読みの , を消さない", u'.replace(",", "").strip()\n    if not re.fullmatch', u'.strip()\n    if not re.fullmatch', ("read",)),
    (u"M08 作られた fact の向きを逆にする", u"    made = before - after\n", u"    made = after - before\n", ("read",)),
    (u"M09 消えた fact の向きを逆にする", u"    gone = after - before\n", u"    gone = before - after\n", ("read",)),
    (u"M10 期の取り違えの形を context が同じものにする", u"if any(c != ctx for c in gone_ctx.get(name, ()))", u"if any(c == ctx for c in gone_ctx.get(name, ()))", ("read",)),
    (u"M11 期の取り違えの形を個数でなく種類で数える", u"swap = sum(k for (name, ctx, _u, _d, _v), k in made.items() if", u"swap = sum(1 for (name, ctx, _u, _d, _v), k in made.items() if", ("read",)),
    (u"M12 engine の自己閉じの読み取りに属性の列の見方を外す", u'for m in ENGINE_FACT_RE.finditer(data.decode("utf-8", "ignore")) if m.group(1).endswith("/"))', u'for m in ENGINE_FACT_RE.finditer(data.decode("utf-8", "ignore")) if True)', ("read",)),
    (u"M13 そのままでだけ合う行の向きを逆にする", u"only_as = [r for r in rows if r[3] == STATE_G and r[4] != STATE_G]", u"only_as = [r for r in rows if r[3] != STATE_G and r[4] == STATE_G]", ("judge", "tally")),
    (u"M14 直した入力でだけ合う行の向きを逆にする", u"only_fx = [r for r in rows if r[3] != STATE_G and r[4] == STATE_G]", u"only_fx = [r for r in rows if r[3] == STATE_G and r[4] != STATE_G]", ("judge", "tally")),
    (u"M15 reason だけ変わった行の見方を逆にする", u"reason_only = [r for r in rows if r[3] == r[4] and not r[5]]", u"reason_only = [r for r in rows if r[3] == r[4] and r[5]]", ("judge", "tally")),
    (u"M16 reason だけ変わった行に state が変わった行も入れる", u"reason_only = [r for r in rows if r[3] == r[4] and not r[5]]", u"reason_only = [r for r in rows if not r[5]]", ("judge", "tally")),
    (u"M17 移り変わりの表の向き(行と列)を取り違える", u"c.get((a, b), 0)) for a in STATES for b in STATES)", u"c.get((b, a), 0)) for a in STATES for b in STATES)", ("judge", "tally")),
    (u"M18 state が変わった行を持つ本を数えない(行の数にする)", u'(u"state が変わった行を持つ本", len(changed_books)),', u'(u"state が変わった行を持つ本", len(changed)),', ("judge", "tally")),
    (u"M19 対の行の reason が同じかの向きを逆にする", u"rows.append([b[u\"#\"], ra[0], ra[1], ra[2], rf[2], ra[3] == rf[3]])", u"rows.append([b[u\"#\"], ra[0], ra[1], ra[2], rf[2], ra[3] != rf[3]])", ("judge",)),
    (u"M20 対の行の state の向きを逆にする", u"rows.append([b[u\"#\"], ra[0], ra[1], ra[2], rf[2], ra[3] == rf[3]])", u"rows.append([b[u\"#\"], ra[0], ra[1], rf[2], ra[2], ra[3] == rf[3]])", ("judge",)),
    (u"M21 集計の鍵の差の向きを逆にする", u"return [[p, x, y, y - x] for", u"return [[p, x, y, x - y] for", ("stop",)),
    (u"M22 集計の鍵の集合が違っても止めない", u"    if [p for p, _v in a] != [p for p, _v in b]:\n        raise Stop", u"    if False:\n        raise Stop", ("stop",)),
    (u"M23 「そのまま」の本が TSS の記録と違っても止めない", u"    if jsonable(asis) != rec_book:", u"    if False:", ("stop",)),
    (u"M24 独立の読みが engine と違っても止めない", u"    if indep != engine_fixed:", u"    if False:", ("stop",)),
    (u"M25 行の集合が違っても止めない", u'    if [(r[0], r[1]) for r in asis[u"行"]] != [(r[0], r[1]) for r in fixed[u"行"]] or not fixed[u"対応"]:', u"    if False:", ("stop",)),
    (u"M26 入力の sha256 の照合を外す", u"if not os.path.isfile(p) or ST.sha256_file(p) != want:", u"if False:", ("stop",)),
    (u"M27 入力の表の 1 つの sha256 の先頭を替える", u'"00414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"', u'"10414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"', ("input_sha", "stop")),
    (u"M28 棚卸しが封の数と違っても止めない", u"        if got != tuple(want):", u"        if False:", ("inv",)),
    (u"M29 棚卸しの経路で .xbrl を見ない", u"    if any(n.startswith(PUBLIC_DOC) and n.endswith(\".xbrl\") for n in names):", u"    if False:", ("inv",)),
    (u"M30 棚卸しの経路で .htm を先にする", u'    if any(n.startswith(PUBLIC_DOC) and n.endswith(".xbrl") for n in names):\n        return ROUTE_XBRL\n    if any(n.startswith(PUBLIC_DOC) and n.endswith(".htm") for n in names):\n        return ROUTE_HTM',
     u'    if any(n.startswith(PUBLIC_DOC) and n.endswith(".htm") for n in names):\n        return ROUTE_HTM\n    if any(n.startswith(PUBLIC_DOC) and n.endswith(".xbrl") for n in names):\n        return ROUTE_XBRL', ("inv",)),
    (u"M31 棚卸しが ZIP でない file を数える", u"                if not zipfile.is_zipfile(p):", u"                if False:", ("inv",)),
    (u"M32 棚卸しが下の folder を見ない(直下だけ)", u"        for dp, dns, fns in os.walk(top):\n            dns.sort()", u"        for dp, dns, fns in os.walk(top):\n            dns[:] = []", ("inv",)),
    (u"M33 封の棚卸しの数を 1 つ替える", u'("edinet", (281, 0, 0))', u'("edinet", (282, 0, 0))', ("seal",)),
    (u"M34 封の commit の定数を替える", u'SEAL_COMMIT = "720a473d"', u'SEAL_COMMIT = "720a473e"', ("seal",)),
    (u"M35 2026-11-09 の便の .htm の経路の本を zm だけで数える", u"    htm = [r for r in rows if ROUTE_HTM in (r[1], r[2])]", u"    htm = [r for r in rows if r[1] == ROUTE_HTM]", ("judge",)),
    (u"M36 2026-11-09 の便の自己閉じを持つ本の見方を >= 0 にする", u'(u".htm の経路で自己閉じを持つ本", sum(1 for r in htm if r[3] > 0)),', u'(u".htm の経路で自己閉じを持つ本", sum(1 for r in htm if r[3] >= 0)),', ("judge",)),
    (u"M37 率の字の四捨五入を切り捨てにする", u"(n * 2000 + d) // (2 * d)", u"(n * 1000) // d", ("rate",)),
    (u"M38 期の取り違えの形の率の分母を消えた fact にする", u'(u"期の取り違えの形(作られた fact のうち)", rate(swap, made))', u'(u"期の取り違えの形(作られた fact のうち)", rate(swap, gone))', ("judge",)),
    (u"M39 予測 NR-5 の分母を全部の本にする", u'(u"NR-5 state が変わった行を持つ本 / 自己閉じを持つ本", rate(jb[u"state が変わった行を持つ本"], nil_books)),', u'(u"NR-5 state が変わった行を持つ本 / 自己閉じを持つ本", rate(jb[u"state が変わった行を持つ本"], fb[u"切れた本"])),', ("judge",)),
    (u"M40 通信の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport urllib.request\n", ("import",)),
    (u"M41 許す一覧の外の engine の module を import する(行を足す)", u"import argparse\n", u"import argparse\nfrom adapters.xbrl import prose\n", ("import",)),
    (u"M42 判定(直した入力)を、自己閉じを消した ZIP でなく包んだままの ZIP に掛ける", u"fixed = judge_fixed(n, grp, kind, sha, text, head, fixed_zb, nfiles)", u"fixed = judge_fixed(n, grp, kind, sha, text, head, wrapped, nfiles)", ("wire_job",)),
    (u"M43 直した入力側の fact を包んだままから作る", u"c_as, c_fx = engine_counter(wrapped), engine_counter(fixed_zb)", u"c_as, c_fx = engine_counter(wrapped), engine_counter(wrapped)", ("wire_job",)),
    (u"M44 直した入力を作らず包んだままを直した入力とする", u"fixed_zb, nil = fix_zip(wrapped)", u"fixed_zb, nil = wrapped, fix_zip(wrapped)[1]", ("wire_job",)),
    (u"M45 独立の読みを直した ZIP に掛ける(確かめが空回りする)", u"check_independent(n, independent_counter(wrapped), c_fx)", u"check_independent(n, independent_counter(fixed_zb), c_fx)", ("wire_job",)),
    (u"M46 自己閉じの数を 0 にする", u'res[u"nil"] = nil', u'res[u"nil"] = 0', ("wire_job", "wire_rec")),
    (u"M47 直した入力側の集計をそのまま側の行から作る", u'tally_fx = TSS.tally([b[u"fixed"] for b in books])', u'tally_fx = TSS.tally([b[u"asis"] for b in books])', ("wire_rec",)),
    (u"M48 fact_diff の引数を入れ替える", u"made, gone, swap = fact_diff(c_as, c_fx)", u"made, gone, swap = fact_diff(c_fx, c_as)", ("wire_job", "wire_rec")),
    (u"M49 便 2026-11-09 の経路の数えで、verify_document と build_raw_claims の ZIP を入れ替える", u"rb, rm = route_of(zb), route_of(zm)", u"rb, rm = route_of(zm), route_of(zb)", ("wire_0911",)),
    (u"M50 便 2026-11-09 の経路の数えで、build_raw_claims の ZIP を別の ZIP(verify_document の側)に替える", u"zm = TS.PR.build_modified_zip(zb, text)[0]", u"zm = zb", ("wire_0911",)),
    (u"M51 便 2026-11-09 の自己閉じの数を別の ZIP から数える", u"for _n, d in htm_members(zm)) if rm == ROUTE_HTM else 0", u"for _n, d in htm_members(zb)) if rm == ROUTE_HTM else 0", ("wire_0911",)),
    (u"M52 独立の読みの確かめの呼びを外す", u"    check_independent(n, independent_counter(wrapped), c_fx)\n", u"", ("wire_job",)),
    (u"M53 「そのまま」の照合の呼びを外す", u"    check_asis(n, asis, rec_book)\n", u"", ("wire_job",)),
    (u"M54 行の集合の確かめの呼びを外す", u"    check_same_rows(n, asis, fixed)\n", u"", ("wire_job",)),
    (u"M55 engine の自己閉じの読み取りを直した ZIP から数える", u'res[u"engine の自己閉じの読み取り"] = engine_self_reads(wrapped)', u'res[u"engine の自己閉じの読み取り"] = engine_self_reads(fixed_zb)', ("wire_job",)),
    (u"M56 「そのまま」の集計を直した入力の行から作る", u'tally_as = TSS.tally([b[u"asis"] for b in books])', u'tally_as = TSS.tally([b[u"fixed"] for b in books])', ("wire_rec",)),
    (u"M57 2026-11-09 の便の数を記録の欄に入れない(空にする)", u"tb = tanshin_0911_block(tanshin_rows if tanshin_rows is not None else tanshin_0911(root))", u"tb = tanshin_0911_block([])", ("wire_rec",)),
)


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"input_sha": input_sha_problems, u"strip": strip_problems, u"read": read_problems, u"judge": judge_problems, u"stop": stop_problems,
             u"rate": rate_problems_fn, u"inv": route_problems, u"wire_job": job_wire_problems, u"wire_rec": record_wire_problems,
             u"wire_0911": tanshin_wire_problems}
    if name in table:
        return table[name](mod)
    if name == u"tally":
        return record_problems(mod, with_script_tally=True)
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

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"`edinet` 281", u"`edinet` 282", 1)))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"正規表現 `<ix:nonFraction[^>]*/>` に当たる所を全部消す", u"", 1)))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"NR-6", u"NR-7")))


class InputTest(unittest.TestCase):
    def test_b_1_the_inputs_have_the_pinned_sha256(self):
        self.assertEqual([], input_sha_problems())

    def test_b_2_the_stops_work_on_made_up_input(self):
        self.assertEqual([], stop_problems())


class ReadTest(unittest.TestCase):
    def test_c_1_the_stripper_matches_the_sealed_examples_and_only_touches_public_doc_htm(self):
        self.assertEqual([], strip_problems())

    def test_c_2_the_independent_read_and_the_fact_diff_on_the_sealed_made_up_example(self):
        u"""封 §0 の作り物の例を ``load_instance`` で読むと、直した engine では作られた fact 0・消えた fact 0(2026-11-17 NRE で直った後の形に書き直した)。直す前の式の参照の engine では作られた fact 1・消えた fact 1。"""
        self.assertEqual([], read_problems())

    def test_c_3_the_judge_counts_and_directions(self):
        self.assertEqual([], judge_problems())

    def test_c_4_rates_are_rounded_by_integer_arithmetic(self):
        self.assertEqual([], rate_problems_fn())

    def test_c_5_routes_and_the_inventory(self):
        self.assertEqual([], route_problems())

    def test_c_6_states_job_wiring_runs_on_made_up_parts(self):
        u"""script の ``states_job`` そのものを作り物の ZIP(封 §0 の形)で走らせる。判定は直した ZIP・独立の読みは包んだままの側・fact の差の向き・自己閉じの数。"""
        self.assertEqual([], job_wire_problems())

    def test_c_7_build_record_wiring_runs_on_made_up_parts(self):
        u"""script の ``build_record`` そのもの(集計・行の対・本ごとの欄・鍵ごとの差)を作り物で走らせる。"""
        self.assertEqual([], record_wire_problems())

    def test_c_8_the_2026_11_09_route_count_is_bound_to_the_zip_it_counts(self):
        self.assertEqual([], tanshin_wire_problems())


class RecordTest(unittest.TestCase):
    def test_d_1_the_record_has_the_sealed_fields_and_equals_the_recount_from_its_rows(self):
        self.assertEqual([], record_problems())

    def test_d_2_a_record_with_one_number_changed_is_red(self):
        text = read(RECORD_REL)
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
        changed = rec[K_JUDGE][u"state が変わった行"][u"分子"]
        self.assertNotEqual([], record_problems(text=text.replace(u'"分子": %d,' % changed, u'"分子": %d,' % (changed + 1), 1)))
        r = json.loads(text, object_pairs_hook=collections.OrderedDict)
        r[u"入力"][0][u"sha256"] = u"0" * 64
        self.assertNotEqual([], record_problems(text=json.dumps(r, ensure_ascii=False)))
        r = json.loads(text, object_pairs_hook=collections.OrderedDict)
        i = next(n for n, x in enumerate(r[u"行"]) if x[3] != x[4])
        r[u"行"][i][4] = r[u"行"][i][3]                                  # 変わった行を 1 つ入れ替える
        self.assertNotEqual([], record_problems(text=json.dumps(r, ensure_ascii=False)))
        r = json.loads(text, object_pairs_hook=collections.OrderedDict)
        r[u"行"].pop()
        self.assertNotEqual([], record_problems(text=json.dumps(r, ensure_ascii=False)))
        r = json.loads(text, object_pairs_hook=collections.OrderedDict)
        r[K_BOOKS][0][2] += 1
        self.assertNotEqual([], record_problems(text=json.dumps(r, ensure_ascii=False)))
        r = json.loads(text, object_pairs_hook=collections.OrderedDict)
        r[K_KEYS][3][3] += 1
        self.assertNotEqual([], record_problems(text=json.dumps(r, ensure_ascii=False)))
        r = json.loads(text, object_pairs_hook=collections.OrderedDict)
        r[u"この script の sha256"] = u"0" * 64
        self.assertNotEqual([], record_problems(text=json.dumps(r, ensure_ascii=False)))

    def test_d_3_a_record_with_a_sentence_a_value_or_an_element_name_is_red(self):
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"行"][0].append(u"売上高")
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"要素名"] = u"jppfs_cor:NetSales"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        self.assertEqual([], leak_problems(read(RECORD_REL)))
        self.assertFalse(DOCID_RE.search(read(RECORD_REL)))

    def test_d_4_the_record_has_a_real_difference_not_a_defect_of_zero(self):
        u"""「0」の疑い: 直した入力は効いていて(作られた・消えた fact が在る)・行が在り・そのままの数が TSS の記録と同じ。"""
        rec = json.loads(read(RECORD_REL))
        self.assertGreater(len(rec[u"行"]), 20000)
        fb = rec[K_FACT]
        self.assertGreater(fb[u"作られた fact"], 0)
        self.assertGreater(fb[u"消えた fact"], 0)
        self.assertGreater(fb[u"自己閉じの数(消した数)"], 0)
        self.assertGreater(rec[K_JUDGE][u"state が変わった行"][u"分子"], 0)


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
    def test_h_1_the_real_history_has_the_seal_before_the_script_the_gate_and_the_record(self):
        u"""script・門・記録のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_h_2_good_order_is_green_and_bad_orders_are_red(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        others = ["measure/s.py", "tests/g.py", "fixtures/r.json"]
        for o in others:
            r.put(o)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("fixtures/new.json")                                             # 未 commit
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["fixtures/new.json"]))
        r2 = PR.Repo()                                                          # 記録が封より前
        r2.put("fixtures/r.json")
        r2.commit("fixtures/r.json")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["fixtures/r.json"]))

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
        for name in (u"seal", u"input_sha", u"strip", u"read", u"judge", u"stop", u"rate", u"inv", u"import", u"wire_job", u"wire_rec", u"wire_0911"):
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
