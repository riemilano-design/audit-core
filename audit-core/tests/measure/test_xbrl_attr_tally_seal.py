# -*- coding: utf-8 -*-
"""封 docs/XBRL_ATTR_TALLY_SEAL_2026-11-17.md(AT ― 「値が違う」と「結べたが別のもの」の行のうち、数の身元の 5 つの属性の取り違えに写る行の割合を、既に在る型の読みの記録だけで数える)の集計の門。封 §1・§2・§3。

**この門が縛るもの**

1. 封の字: §1 の入力の表(5 行)・§2-1 の写しの表が、script の字(``INPUTS``・``TABLE``)と 1 行ずつ同じ。封の commit・path。
2. 入力 5 つの sha256 が封の表と同じ(実物)。違えば script は止まる(実物の複製の 1 byte を変えて止まるのを見る)。
3. 記録 ``fixtures/xbrl/attr_tally/tally_2026-11-17.json`` が script の組み直しと byte で同じ・封の字(封の commit・入力・写しの表)を持つ・行・本の番号を持たない・1 株あたりは 0(作り)・限界の字・率の字が小数 1 桁。
4. 封で既に計算できると書いた数(YS の V 11/18・TSS の V 84/119)が記録と一致する。
5. 記録の集計の欄と行から数え直した数が違えば止まる(型の集計・b の違うもの・細目の集計・近い行の型の集計)。表に無い型の字・細目の無い行は止まる。
6. 配線: script が標準ライブラリだけを import する(engine・通信を import しない。ast で)。``tests/adapters/xbrl/test_boundary.py`` の import 一覧は広げない。
7. engine 0 行: 封の commit から HEAD まで ``core/``・``adapters/``・``measure/lib``・``measure/inject.py`` と入力 5 つを触っていない。作業木に未 commit の変更も無い。
8. 順序: 封 52f3a228 ⊏ script・この門・記録(**commit の順**。未 commit は赤(skip にしない))。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作り、検査が赤になることを見る。file は書き換えない。変異の前後で script・記録の sha256 が同じことも見る)。
全数の測り直しは無い(入力は数え直すだけで、数秒で終わる)。この file は docID の字を持たない。
"""
import ast
import contextlib
import copy
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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_at_seal")       # 順序の部品(order_problems・Repo・git_in・added_commits)。門としては走らせない
MS = load_module("measure/xbrl_attr_tally_2026-11-17.py", "attr_tally_script_for_seal_gate")

SEAL_REL = "docs/XBRL_ATTR_TALLY_SEAL_2026-11-17.md"
SEAL_COMMIT_SHORT = "52f3a228"                 # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_attr_tally_2026-11-17.py"
GATE_REL = "tests/measure/test_xbrl_attr_tally_seal.py"
RECORD_REL = "fixtures/xbrl/attr_tally/tally_2026-11-17.json"
ORDER_FILES = (SCRIPT_REL, GATE_REL, RECORD_REL)
INPUT_RELS = tuple(rel for _no, _b, rel, _sha in MS.INPUTS)
#: 封の commit から 0 行でなければならない path(engine・lib・仕掛けと入力 5 つ)
ENGINE_RELS = ("adapters", "core", "measure/lib", "measure/inject.py")
NOT_TOUCHED_RELS = ENGINE_RELS + INPUT_RELS
#: script が import してよい module(標準ライブラリだけ)
STDLIB_OK = ("__future__", "argparse", "collections", "hashlib", "io", "json", "os", "sys")
ENGINE_TOPS = ("adapters", "core", "audit_core", "measure")
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
RATE_TEXT = re.compile(r"^(\d+\.\d%|分母 0)$")


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
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script(sha256 と root の計算が同じになる)。"""
    mod = types.ModuleType("attr_tally_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


# ---------------------------------------------------------------- 1. 封の字
def seal_text():
    return read(SEAL_REL)


def seal_inputs(seal):
    u"""封 §1 の表 → [(#, 便, path, sha256)]。"""
    return [(int(m.group(1)), m.group(2), m.group(3), m.group(4))
            for m in re.finditer(r"^\| (\d) \| (KAM|YS|TSS) \| `([^`]+)` \| `([0-9a-f]{64})` \|$", seal, re.M)]


def seal_table(seal):
    u"""封 §2-1 の表 → [(便, 型・細目, 写す先(太字を外す), 理由)]。§2-1 の見出しから §2-2 の見出しまで。"""
    a = seal.index(u"### §2-1")
    b = seal.index(u"### §2-2")
    out = []
    for ln in seal[a:b].split(u"\n"):
        if not (ln.startswith(u"| KAM・YS |") or ln.startswith(u"| TSS |")):
            continue
        cells = [c.strip() for c in ln.strip().strip(u"|").split(u"|")]
        if len(cells) != 4:
            return None
        out.append((cells[0], cells[1], cells[2].replace(u"**", u""), cells[3]))
    return out


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    si = seal_inputs(seal)
    if len(si) != 5 or [i[0] for i in si] != [1, 2, 3, 4, 5]:
        out.append(u"封 §1 の表が 5 行の # の順でない")
    if [tuple(x) for x in ms.INPUTS] != si:
        out.append(u"script の入力の表が封 §1 の表と違う")
    st = seal_table(seal)
    if not st or len(st) != 21:
        out.append(u"封 §2-1 の写しの表が 21 行で読めない")
    elif [tuple(r) for r in ms.TABLE] != st:
        out.append(u"script の写しの表が封 §2-1 の表と 1 行ずつ違う")
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.OUT_REL != RECORD_REL:
        out.append(u"script の封の commit・path が門と違う")
    for phrase in (u"**1 株あたり**に写る型は、この表には無い", u"記録は `fixtures/xbrl/attr_tally/tally_2026-11-17.json` の 1 つ。行は持たず数だけ",
                   u"数え直した数が記録の集計の欄と違えば script は止まる", u"表に無い型の字が出たら止まる"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    return out


def seal_history_problems():
    c = PR.added_commits(REPO, PREFIX + SEAL_REL)
    if len(c) != 1 or not c[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の commit が履歴に 1 つで %s に決まらない" % SEAL_COMMIT_SHORT]
    return []


# ---------------------------------------------------------------- 2. 入力の sha256
def input_sha_problems(ms=None):
    ms = ms or MS
    return [u"入力の sha256 が封と違う: %s" % rel for _no, _b, rel, want in ms.INPUTS if sha_of(rel) != want]


def make_root(tmp, tweak_input=None, with_record=False):
    u"""script と入力 5 つ(と記録)の複製を ``tmp`` の下に作る(``--root`` で使う)。``tweak_input`` = path なら、その複製の末尾に 1 字足す。"""
    for rel in (SCRIPT_REL,) + INPUT_RELS + ((RECORD_REL,) if with_record else ()):
        dst = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(ROOT, rel), dst)
        if rel == tweak_input:
            with open(dst, "ab") as fh:
                fh.write(b" ")
    return tmp


def real_inputs():
    return MS.load_inputs(ROOT)


def stop_problems(ms=None):
    u"""入力の sha256 が違う・集計の欄が行と違う・表に無い型の字・細目の無い行 は Stop で止まる。変えない入力では止まらない。"""
    ms = ms or MS
    out = []
    base = guard(lambda: ms.load_inputs(ROOT) and [])
    if base:
        return [u"本物の入力が読めない"]
    inp = ms.load_inputs(ROOT)
    if guard(lambda: ms.tally(copy.deepcopy(inp)) and []):
        out.append(u"変えない入力で止まる")

    def must_stop(label, tweak):
        i2 = copy.deepcopy(inp)
        tweak(i2)
        try:
            ms.tally(i2)
        except ms.Stop:
            return
        except BaseException as exc:               # noqa: BLE001
            out.append(u"%s: Stop でない例外 %s" % (label, type(exc).__name__))
            return
        out.append(u"%s: 止まらない" % label)

    def bump(d, *path):
        for k in path[:-1]:
            d = d[k]
        d[path[-1]] += 1

    must_stop(u"KAM 型の集計 +1", lambda i: bump(i[1], u"型の集計", u"V 連結", u"ア"))
    must_stop(u"YS 型の集計 +1", lambda i: bump(i[2], u"型の集計", u"G 配当", u"a"))
    must_stop(u"KAM b の違うもの +1", lambda i: bump(i[1], u"b の違うものの集計", u"G 単体", u"側"))
    must_stop(u"YS 読む行の数 +1", lambda i: bump(i[2], u"読む行の規則", u"読む行の数", u"V 設備"))
    must_stop(u"TSS 型の集計 +1", lambda i: bump(i[3], u"型の集計", u"ア"))
    must_stop(u"TSS 細目の集計 +1", lambda i: bump(i[4], u"細目の集計", u"イ2"))
    must_stop(u"近い行の型の集計 +1", lambda i: bump(i[5], u"型の集計", u"い"))
    must_stop(u"KAM の行の型が決めの外", lambda i: i[1][u"行"][0].__setitem__(4, u"ソ"))
    must_stop(u"YS の b の行に違うものが無い", lambda i: [r.__setitem__(5, None) for r in i[2][u"行"] if r[4] == u"b"][:1])
    must_stop(u"TSS の細目の行が 1 つ無い", lambda i: i[4][u"行"].pop())
    def drop_detail_keep_counts(i):
        r = i[4][u"行"].pop()
        i[4][u"細目の集計"][r[2]] -= 1
    must_stop(u"TSS の細目の行が 1 つ無い(細目の集計も合わせて 1 引く)", drop_detail_keep_counts)
    must_stop(u"TSS の細目の字が型と合わない", lambda i: i[4][u"行"][0].__setitem__(2, u"カ1"))

    def unknown_in_table(i):
        i[4][u"細目の字"][u"イ9"] = u"x"
        for r in i[4][u"行"]:
            if r[1] == u"イ":
                r[2] = u"イ9"
                break
        c = i[4][u"細目の集計"]
        c[u"イ9"] = 1
        c[u"イ1"] -= 1 if c[u"イ1"] else 0
        # 細目の集計の数え直しも合わせる(表に無い字で止まることだけを見るため、集計の違いで止まらないようにする)
        cnt = {}
        for r in i[4][u"行"]:
            cnt[r[2]] = cnt.get(r[2], 0) + 1
        i[4][u"細目の集計"] = {k: cnt.get(k, 0) for k in i[4][u"細目の字"]}
    must_stop(u"表に無い細目の字", unknown_in_table)
    # 実物の複製の 1 byte を変えれば、入力の sha256 が違うので止まる
    tmp = tempfile.mkdtemp(prefix="at_gate_")
    try:
        make_root(tmp, tweak_input=INPUT_RELS[0])
        try:
            ms.load_inputs(tmp)
            out.append(u"入力の sha256 が違うのに止まらない")
        except ms.Stop:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


# ---------------------------------------------------------------- 3. 記録
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
    u"""記録に行・文・値・本の番号が無い(``行`` の欄・本の # の字・整数だけの行の並び・docID・証券コードらしい字)。"""
    out = []
    try:
        rec = json.loads(text)
    except ValueError:
        return [u"記録が JSON でない"]
    for p, v in walk(rec):
        if p and p[-1] in (u"行", u"行の欄", u"本の #", u"文の番号", u"位置", u"span", u"標本の番号"):
            out.append(u"行・本の番号の欄が在る: %s" % (p[-1],))
        if isinstance(v, list) and v and all(isinstance(x, list) for x in v) and p and p[0] != u"写しの表":
            out.append(u"行らしい並びが在る: %s" % (p,))
    if u"本の #" in text:
        out.append(u"本の # の字が在る")
    if DOCID_RE.search(text) or re.search(r"0812\d{14}", text):
        out.append(u"docID・TDnet の番号らしい字が在る")
    return out


def rates(rec):
    for p, v in walk(rec):
        if isinstance(v, dict) and set(v) == {u"分子", u"分母", u"率"}:
            yield p, v


def rate_problems(rec):
    u"""率の欄: 分子・分母は整数、率は小数 1 桁の %(分母 0 は「分母 0」)、率の字は分子 / 分母を独立に(Fraction で四捨五入)計算した字と同じ。"""
    out = []
    n_seen = 0
    for p, v in rates(rec):
        n_seen += 1
        n, d, t = v[u"分子"], v[u"分母"], v[u"率"]
        if not (isinstance(n, int) and isinstance(d, int) and n <= d + 0 and n >= 0) or not RATE_TEXT.match(t):
            out.append(u"率の欄の形が決めと違う: %s" % (p,))
            continue
        want = u"分母 0" if d == 0 else u"%d.%d%%" % divmod(int(Fraction(n, d) * 1000 + Fraction(1, 2)), 10)
        if t != want:
            out.append(u"率の字が分子・分母から出る字と違う: %s %s" % (p, t))
    if n_seen < 10:
        out.append(u"率の欄が少なすぎる(%d)" % n_seen)
    return out


def record_problems(ms=None, text=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    p = os.path.join(ROOT, RECORD_REL)
    if text is None:
        if not os.path.isfile(p):
            return [u"記録が無い"]
        with open(p, encoding="utf-8", newline="") as fh:
            text = fh.read()
    rebuilt = guard(lambda: ms.dumps(ms.build(ROOT)))
    if not isinstance(rebuilt, str):
        out.append(u"組み直しが止まった")
    elif rebuilt != text:
        out.append(u"記録が script の組み直しと byte で違う")
    out.extend(leak_problems(text))
    try:
        rec = json.loads(text)
    except ValueError:
        return out + [u"記録が JSON でない"]
    out.extend(rate_problems(rec))
    if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"記録の封の path・commit が違う")
    if rec.get(u"この script の sha256") != sha_of(SCRIPT_REL):
        out.append(u"記録の script の sha256 が実物と違う")
    si = seal_inputs(seal)
    if [(x.get(u"#"), x.get(u"便"), x.get(u"記録"), x.get(u"sha256")) for x in rec.get(u"入力", [])] != si:
        out.append(u"記録の入力が封 §1 の表と違う")
    if [tuple(r) for r in rec.get(u"写しの表", [])] != seal_table(seal):
        out.append(u"記録の写しの表が封 §2-1 の表と違う")
    lim = u"\n".join(rec.get(u"限界", []))
    for phrase in (u"AI の席(司令塔)1 席", u"盲検でなく", u"人は読んでいない", u"あと知恵"):
        if phrase not in lim:
            out.append(u"記録の限界の字に無い: %s" % phrase)
    b = rec.get(u"便ごとの数", {})
    for batch in (u"KAM", u"YS", u"TSS"):
        v = b.get(batch, {}).get(u"V", {})
        if v.get(u"属性ごとの行の数", {}).get(u"1 株あたり") != 0 or u"作りで" not in v.get(u"1 株あたりについて", u""):
            out.append(u"%s の 1 株あたりが 0(作り)と書かれていない" % batch)
        if sum(v.get(u"属性ごとの行の数", {}).values()) != v.get(u"属性の内の行"):
            out.append(u"%s の属性ごとの数の合計が内の行と違う" % batch)
        if v.get(u"属性の内の行", -1) + v.get(u"外の行", -1) + v.get(u"ク の行(分母から除く)", -1) != v.get(u"読んだ行の数"):
            out.append(u"%s の内・外・ク の合計が読んだ行と違う" % batch)
        if sum(v.get(u"外の理由ごとの行の数", {}).values()) != v.get(u"外の行"):
            out.append(u"%s の外の理由ごとの数の合計が外の行と違う" % batch)
    ref = b.get(u"参考の合計", {})
    if u"母集団の率ではない" not in ref.get(u"注", u""):
        out.append(u"参考の合計に「母集団の率ではない」が無い")
    return out


def precomputed_problems(text=None):
    u"""封 §0・§4 で既に計算できると書いた数: YS の V 11/18(61.1%)・TSS の V 84/119(70.6%)。"""
    p = os.path.join(ROOT, RECORD_REL)
    if text is None:
        if not os.path.isfile(p):
            return [u"記録が無い"]
        text = read(RECORD_REL)
    rec = json.loads(text)
    out = []
    ys = rec[u"便ごとの数"][u"YS"][u"V"][u"率(主。分母は ク を除く)"]
    tss = rec[u"便ごとの数"][u"TSS"][u"V"][u"率(主。分母は ク を除く)"]
    if (ys[u"分子"], ys[u"分母"], ys[u"率"]) != (11, 18, u"61.1%"):
        out.append(u"YS の V が 11/18(61.1%%)と違う: %s/%s" % (ys[u"分子"], ys[u"分母"]))
    if (tss[u"分子"], tss[u"分母"], tss[u"率"]) != (84, 119, u"70.6%"):
        out.append(u"TSS の V が 84/119(70.6%%)と違う: %s/%s" % (tss[u"分子"], tss[u"分母"]))
    return out


def write_check_problems(ms=None):
    u"""``--write`` は在る記録を上書きせず止まる・``--check`` は byte が同じなら通り 1 byte 違えば止まる(複製の木で)。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="at_gate_")
    try:
        make_root(tmp)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            guard(ms.main, ["--root", tmp, "--write"])
        target = os.path.join(tmp, RECORD_REL)
        if not os.path.isfile(target):
            return [u"--write が記録を書かない"]
        if open(target, encoding="utf-8", newline="").read() != read(RECORD_REL):
            out.append(u"複製の木で書いた記録が本物の記録と違う(script の sha256 が同じなので同じになるはず)")
        try:
            ms.main(["--root", tmp, "--write"])
            out.append(u"在る記録に --write が止まらない")
        except ms.Stop:
            pass
        try:
            with contextlib.redirect_stdout(buf):
                ms.main(["--root", tmp, "--check"])
        except ms.Stop:
            out.append(u"同じ内容なのに --check が止まる")
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(u" ")
        try:
            ms.main(["--root", tmp, "--check"])
            out.append(u"1 字違う記録に --check が止まらない")
        except ms.Stop:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


# ---------------------------------------------------------------- 6. 配線
def import_problems(src=None):
    u"""script の import は標準ライブラリだけ(許す名前の一覧)・engine と通信の module を import しない(ast)。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [n.module or u""]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "exec", "eval"):
            out.append(u"動的な import・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in ENGINE_TOPS:
                out.append(u"engine の module を import している: %s" % nm)
            if top in NETWORK_MODULES:
                out.append(u"通信の module を import している: %s" % nm)
            if top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    return out


def boundary_problems():
    u"""``tests/adapters/xbrl/test_boundary.py`` の import 一覧にこの便の名前を足していない。"""
    p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
    with open(p, encoding="utf-8") as fh:
        t = fh.read()
    return [u"test_boundary.py にこの便の名前が在る"] if (u"attr_tally" in t) else []


# ---------------------------------------------------------------- 7. engine 0 行・8. 順序
def engine_since_seal_problems(root=REPO):
    c = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(c) != 1:
        return [u"封の commit が履歴に 1 つに決まらない"]
    rc, log = PR.git_in(root, "log", "--format=%H", "%s..HEAD" % c[0], "--", *[PREFIX + r for r in NOT_TOUCHED_RELS])
    if rc != 0:
        return [u"git log が失敗した"]
    return [u"封の後に engine・lib・入力を触った commit %s" % x[:7] for x in log.split() if x]


def engine_worktree_problems(root=REPO):
    rc, st = PR.git_in(root, "status", "--porcelain", "--untracked-files=all", "--", *[PREFIX + r for r in NOT_TOUCHED_RELS])
    if rc != 0:
        return [u"git status が失敗した"]
    return [u"engine・lib・入力に未 commit の変更: %s" % ln.strip()[:2] for ln in st.splitlines() if ln.strip()]


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(ORDER_FILES) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 変異
#: (名前, script の中の字 old, new, 赤になるはずの検査の名前の並び)。old は script に 1 回だけ在る字
MUTANTS = (
    (u"M01 写しの表の 1 行(KAM・YS の ウ)の先を 範囲 → 期", u'(u"KAM・YS", u"ウ", u"範囲",', u'(u"KAM・YS", u"ウ", u"期",', ("seal", "record")),
    (u"M02 写しの表の 1 行(TSS の カ1)の先を 外 → 単位", u'(u"TSS", u"カ1", u"外(数の読み取り)",', u'(u"TSS", u"カ1", u"単位",', ("seal", "record")),
    (u"M03 写しの表の 1 行(TSS の イ3)の理由の字を 1 字替える", u'u"となりの内訳・別の表の要素"', u'u"となりの内訳・別の表の要素。"', ("seal", "record")),
    (u"M04 入力の表の 1 つの sha256 の先頭を替える", u'"8c9fe6b8def7430908bf925f697ea5a1b1d634dd754933aab7c71b0a913c964a"', u'"9c9fe6b8def7430908bf925f697ea5a1b1d634dd754933aab7c71b0a913c964a"', ("seal", "input_sha", "stop")),
    (u"M05 入力の sha256 の照合を外す", u"if sha256_file(p) != want:", u"if False:", ("stop",)),
    (u"M06 集計の欄との照合を外す(数え直しが違っても止まらない)", u"if dict(got) != dict(want):", u"if False:", ("stop",)),
    (u"M07 細目が無い行の検査を 3 か所とも外す(読む所・数える所・表の引き。1 か所ずつでは他の 2 か所が止めるので黙る)",
     ((u"if need != set(detail_of):", u"if False:"), (u"if d is None:", u"if False:"), (u"if key not in lookup:", u"if False:")), None, ("stop",)),
    (u"M08 表に無い型・細目の字の検査を外す", u"if key not in lookup:", u"if False:", ("stop",)),
    (u"M09 V の率の分母に ク を入れる(主の率)", u"b[u\"率(主。分母は ク を除く)\"] = rate(n_in, n - n_drop)", u"b[u\"率(主。分母は ク を除く)\"] = rate(n_in, n)", ("record", "precomputed")),
    (u"M10 TSS の ク を内に数える(ク の行を外に混ぜる)", u"            drop += 1", u"            attrs[u\"項目\"] += 1", ("record", "precomputed")),
    (u"M11 G の c /(b + c)の分母を b だけにする", u'(u"c /(b + c)", rate(cc, b + cc))', u'(u"c /(b + c)", rate(cc, b))', ("record",)),
    (u"M12 G の b の 側 を 期 に写す", u'(u"側", u"範囲")', u'(u"側", u"期")', ("record",)),
    (u"M13 率の字の四捨五入を切り捨てにする", u"tenths = (n * 2000 + d) // (2 * d)", u"tenths = (n * 1000) // d", ("record", "precomputed")),
    (u"M14 本の片寄りの最大を 1 少なく数える", u"mx = max(per.values()) if per else 0", u"mx = (max(per.values()) - 1) if per else 0", ("record",)),
    (u"M15 TSS の ケ を細目の字で引く(表の ケ を使わない)", u'pairs.append((book, u"ケ" if t == u"ケ" else d))', u'pairs.append((book, d))', ("record", "stop")),
    (u"M16 engine の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport adapters.xbrl.prose\n", ("import",)),
    (u"M17 通信の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport urllib.request\n", ("import",)),
    (u"M18 標準ライブラリの外の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport re\n", ("import",)),
)


def check_by_name(name, mod, src):
    u"""変異した module に対する検査の名前 → 問題の並び。"""
    if name == u"seal":
        return seal_problems(mod)
    if name == u"record":
        return record_problems(mod)
    if name == u"input_sha":
        return input_sha_problems(mod)
    if name == u"stop":
        return stop_problems(mod)
    if name == u"import":
        return import_problems(src)
    if name == u"precomputed":
        # 組み直した記録の字で、既に計算できた数を見る
        return guard(lambda: precomputed_problems(mod.dumps(mod.build(ROOT))))
    raise AssertionError(name)


def run_mutants():
    u"""各変異で、赤になるはずの検査が全部赤か。[(名前, [(検査, 赤か)])]。"""
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in MUTANTS:
        pairs = old if new is None else ((old, new),)
        src = base
        for o, n in pairs:
            assert base.count(o) == 1, (name, base.count(o))
            src = src.replace(o, n)
        try:
            mod = load_source(src)
        except BaseException as exc:                # noqa: BLE001
            out.append((name, [(c, True) for c in checks], u"読めない: %s" % type(exc).__name__))
            continue
        res = []
        for c in checks:
            res.append((c, bool(guard(check_by_name, c, mod, src))))
        out.append((name, res, u""))
    return out


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_tables_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_is_in_history_as_the_sealed_commit(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"| KAM・YS | ウ | 範囲 |", u"| KAM・YS | ウ | 期 |", 1)))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"`d1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183`", u"`e1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183`", 1)))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"表に無い型の字が出たら止まる", u"", 1)))

    def test_a_4_the_seal_table_has_the_rows_the_script_reads(self):
        st = seal_table(seal_text())
        self.assertEqual(21, len(st))
        self.assertEqual({u"KAM・YS": 9, u"TSS": 12}, {b: sum(1 for r in st if r[0] == b) for b in (u"KAM・YS", u"TSS")})


class InputTest(unittest.TestCase):
    def test_b_1_the_five_inputs_have_the_sealed_sha256(self):
        self.assertEqual([], input_sha_problems())

    def test_b_2_a_changed_expected_sha_is_red(self):
        src = read(SCRIPT_REL).replace(u"8c9fe6b8def7430908bf925f697ea5a1b1d634dd754933aab7c71b0a913c964a", u"9c9fe6b8def7430908bf925f697ea5a1b1d634dd754933aab7c71b0a913c964a", 1)
        self.assertNotEqual([], input_sha_problems(load_source(src)))

    def test_b_3_stops_on_a_changed_input_a_recount_difference_an_unknown_type_and_a_missing_detail(self):
        self.assertEqual([], stop_problems())


class RecordTest(unittest.TestCase):
    def test_c_1_the_record_equals_the_rebuild_and_has_the_sealed_fields(self):
        self.assertEqual([], record_problems())

    def test_c_2_the_record_has_the_numbers_already_computable_from_the_seal(self):
        self.assertEqual([], precomputed_problems())

    def test_c_3_a_record_with_a_row_or_a_book_number_is_red(self):
        rec = json.loads(read(RECORD_REL))
        rec[u"行"] = [[u"V 連結", 4, 8, 69, u"ア", None]]
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL))
        rec[u"便ごとの数"][u"KAM"][u"本の #"] = [1, 2]
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL))
        rec[u"便ごとの数"][u"KAM"][u"x"] = [[1, 2], [3, 4]]
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        self.assertEqual([], leak_problems(read(RECORD_REL)))

    def test_c_4_a_record_with_one_number_changed_is_red(self):
        text = read(RECORD_REL)
        a = text.index(u'"読んだ行の数": 37')
        self.assertNotEqual([], record_problems(text=text[:a] + u'"読んだ行の数": 38' + text[a + len(u'"読んだ行の数": 37'):]))
        rec = json.loads(text)
        rec[u"便ごとの数"][u"TSS"][u"V"][u"率(主。分母は ク を除く)"][u"分母"] = 120
        self.assertNotEqual([], precomputed_problems(json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"))
        rec = json.loads(text)
        rec[u"便ごとの数"][u"YS"][u"V"][u"率(主。分母は ク を除く)"][u"率"] = u"61.2%"
        self.assertNotEqual([], rate_problems(rec))
        rec = json.loads(text)
        rec[u"便ごとの数"][u"KAM"][u"V"][u"属性ごとの行の数"][u"1 株あたり"] = 1
        self.assertNotEqual([], record_problems(text=json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"))

    def test_c_5_write_refuses_to_overwrite_and_check_compares_bytes(self):
        self.assertEqual([], write_check_problems())

    def test_c_6_the_record_has_no_docid_or_code(self):
        self.assertFalse(DOCID_RE.search(read(RECORD_REL)))


class WiringTest(unittest.TestCase):
    def test_d_1_the_script_imports_only_the_standard_library(self):
        self.assertEqual([], import_problems())

    def test_d_2_the_boundary_import_list_is_not_widened(self):
        self.assertEqual([], boundary_problems())

    def test_d_3_the_script_does_not_open_a_book_or_the_network_or_a_key(self):
        src = read(SCRIPT_REL)
        for bad in (u"zipfile", u"socket", u"urllib", u"ANTHROPIC", u"API_KEY", u"subprocess"):
            self.assertNotIn(bad, src)


class EngineZeroTest(unittest.TestCase):
    def test_e_1_the_real_history_has_no_engine_or_input_change_since_the_seal(self):
        self.assertEqual([], engine_since_seal_problems())

    def test_e_2_the_working_tree_has_no_uncommitted_engine_or_input_change(self):
        self.assertEqual([], engine_worktree_problems())

    def test_e_3_every_not_touched_path_is_a_real_path(self):
        for r in NOT_TOUCHED_RELS:
            self.assertTrue(os.path.exists(os.path.join(ROOT, r)), r)


class OrderTest(unittest.TestCase):
    def test_f_1_the_real_history_has_the_seal_before_the_script_the_gate_and_the_record(self):
        u"""script・門・記録のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_f_2_good_order_is_green_and_bad_orders_are_red(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        for o in ("measure/s.py", "tests/g.py", "fixtures/r.json"):
            r.put(o)
        r.commit("measure/s.py", "tests/g.py", "fixtures/r.json")
        others = ["measure/s.py", "tests/g.py", "fixtures/r.json"]
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("fixtures/new.json")                                                      # 未 commit
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["fixtures/new.json"]))
        r2 = PR.Repo()
        r2.put("fixtures/r.json")
        r2.commit("fixtures/r.json")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["fixtures/r.json"]))     # 記録が封より前

    def test_f_3_the_order_check_lists_the_script_the_gate_and_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))


class MutantTest(unittest.TestCase):
    def test_g_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_of(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        results = run_mutants()
        after = (sha_of(SCRIPT_REL), sha_of(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        self.assertEqual(before, after)
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))

    def test_g_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ("seal", "record", "input_sha", "stop", "import", "precomputed"):
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
