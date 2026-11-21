# -*- coding: utf-8 -*-
u"""封 docs/XBRL_SHEET_CONTEXT_SEAL_2026-11-22.md(XA1 ― 行・列の紙に収まらなかった fact の文脈を、終わりの日と member の組に分けて別々の線で決めると、どれだけ収まるか)の封の門。

**この門は置き場を読まない**(書類の置き場 ``~/.cache/audit-core/edinet/`` は 1 度も開かない)。通信しない。道具(Arelle)は呼ばない。subprocess を呼ぶのは git だけ。
作り物の書類(手で書いた htm)と作り物の置き場(使い捨ての folder の zip)で、置き場の読み方・数え方・記録の検査を本物の関数のまま通す。

**この門が縛るもの**

1. 封の字: 封の commit(d46f92aa)・封の file が commit した blob と同じ・封の決め(8 通りの並びと同点の順・書く欄の式の 3・4・1・1・7・書類 90%・欠陥を疑う条件の数・予測の境の数・限界の字)が script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 文脈の読み方(``id``・期間 3 通り・member の組の並び・typedMember・コメント・自己閉じ・同じ id で中身の違う文脈・定義の無い contextRef)。
4. 数え方(時点と期間が同じ行に並ぶ表・member が列で終わりの日が行の表・その逆・向き B の表・両方が要素の線の表・8 通りのそれぞれと同点の順・理由の数え分け・符号と書式・空の fact と表の外・
   期間の種類が 2 つ在る name・始まりの日が違う期間の文脈・断った書類)。
5. 段 0 が便 XA0 の記録と全部の数で同じでなければ止まる(書類ごとの行・5 本の塊・62 本の塊)。塊・判定に要る数・欠陥を疑う条件・記録の形と合計と禁止のもの・置き場から数え直す ``--check``・開発の入口は 5 本だけ。
6. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。変異の検査は変異した module そのものに当てる
(``check_by_name(name, mod, src)`` は変異した module の関数だけを呼ぶ)。表は実行より先に書いた(予測 = 赤になるべき検査の名前)。
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
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)


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


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("xbrl_sheet_context_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_SHEET_CONTEXT_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "d46f92aa"
SCRIPT_REL = "measure/xbrl_sheet_context_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_sheet_context_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/sheet_context_2026-11-22.json"
PRIOR_RECORD_REL = "fixtures/xbrl/cd8/sheet_wall_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_sheet_context_script_for_seal_gate")
ORDER_FILES = (SCRIPT_REL, GATE_REL)
od = collections.OrderedDict


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_text(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.exists(os.path.join(ROOT, rel)) else None


def guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except BaseException as exc:                # noqa: BLE001
        return [u"例外: %s" % type(exc).__name__]


def stops(ms, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


def refuses(ms, fn, *a, **kw):
    u"""``Refuse`` が上がれば断った理由の字・上がらなければ None。"""
    try:
        fn(*a, **kw)
    except ms.Refuse as exc:
        return exc.reason
    return None


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xa1_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def load_order_helpers():
    p = os.path.join(ROOT, "tests", "measure", "test_xbrl_p28_result.py")
    if not os.path.exists(p):
        return None
    return load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_sheet_context_seal")


def want_eq(out_, label, got, want):
    if got != want:
        out_.append(u"%s: 得 %r 正 %r" % (label, got, want))


# ======================================================================== 作り物の書類(手で書いた字)
AXIS = u"jppfs_cor:SegAxis"


def fx(name=u"jppfs_cor:E0", ctx=u"C0", unit=u"JPY", dec=u"0", scale=None, sign=None, fmt=u"ixt:numdotdecimal", text=u"1,000", nil=False):
    a = u'name="%s" contextRef="%s"' % (name, ctx)
    if unit is not None:
        a += u' unitRef="%s"' % unit
    if nil:
        return u'<ix:nonFraction %s xsi:nil="true" />' % a
    if dec is not None:
        a += u' decimals="%s"' % dec
    if scale is not None:
        a += u' scale="%s"' % scale
    if fmt is not None:
        a += u' format="%s"' % fmt
    if sign is not None:
        a += u' sign="%s"' % sign
    return u"<ix:nonFraction %s>%s</ix:nonFraction>" % (a, text)


def tbl(rows, tag=u"td"):
    return u"<table>" + u"".join(u"<tr>" + u"".join(u"<%s>%s</%s>" % (tag, c, tag) for c in r) + u"</tr>" for r in rows) + u"</table>"


def cdef(cid, end=u"2025-03-31", start=None, mem=()):
    u"""文脈の定義(EDINET の形: entity・period・scenario)。``start`` が在れば期間・無ければ時点。"""
    per = u"<xbrli:instant>%s</xbrli:instant>" % end if start is None else u"<xbrli:startDate>%s</xbrli:startDate><xbrli:endDate>%s</xbrli:endDate>" % (start, end)
    scen = u"<xbrli:scenario>%s</xbrli:scenario>" % u"".join(u'<xbrldi:explicitMember dimension="%s">%s</xbrldi:explicitMember>' % (d, m) for d, m in mem) if mem else u""
    return (u'<xbrli:context id="%s"><xbrli:entity><xbrli:identifier scheme="http://x">E0</xbrli:identifier></xbrli:entity><xbrli:period>%s</xbrli:period>%s</xbrli:context>' % (cid, per, scen))


def cpage(body, defs):
    return u"<html><body><ix:header><ix:resources>%s</ix:resources></ix:header>\n%s\n</body></html>\n" % (u"".join(defs), body)


def mem_of(i):
    return [(AXIS, u"jppfs_cor:Mem%d" % i)]


def grid_doc(tag, nr, nc, name_by, ctx_of, defs_of):
    u"""nr × nc の表 1 つ。``name_by(r, c)`` = 要素の名・``ctx_of(r, c)`` = contextRef・``defs_of`` = 文脈の定義の並び。"""
    rows = [[fx(name=u"jppfs_cor:%s%d" % (tag, name_by(r, c)), ctx=ctx_of(r, c)) for c in range(nc)] for r in range(nr)]
    return cpage(tbl(rows), defs_of)


ENDS3 = ((u"2024-03-31", None), (u"2025-03-31", u"2024-04-01"), (u"2025-06-30", None))


def doc_b():
    u"""member が列・終わりの日が行(3 × 3)。要素は行ごと。"""
    defs = [cdef(u"Kb%d%d" % (r, c), end=ENDS3[r][0], start=ENDS3[r][1], mem=mem_of(c)) for r in range(3) for c in range(3)]
    return grid_doc(u"Rb", 3, 3, lambda r, c: r, lambda r, c: u"Kb%d%d" % (r, c), defs)


def doc_a():
    u"""時点と期間が同じ行に並ぶ表(2 × 2)。列 0 は期間・列 1 は時点・終わりの日と member の組は同じ・id は行ごとに別。"""
    defs = [cdef(u"Da0", start=u"2024-04-01"), cdef(u"Da1", start=u"2024-04-01"), cdef(u"Ia0"), cdef(u"Ia1")]
    return grid_doc(u"Ra", 2, 2, lambda r, c: r, lambda r, c: [u"Da0", u"Ia0"][c] if r == 0 else [u"Da1", u"Ia1"][c], defs)


def doc_c():
    u"""終わりの日が列・member が行(3 行 × 2 列)。要素は行ごと。"""
    defs = [cdef(u"Kc%d%d" % (r, c), end=[u"2024-03-31", u"2025-03-31"][c], mem=mem_of(r)) for r in range(3) for c in range(2)]
    return grid_doc(u"Rc", 3, 2, lambda r, c: r, lambda r, c: u"Kc%d%d" % (r, c), defs)


def doc_d():
    u"""doc_b の転置(要素が列・終わりの日が列・member が行)。向き B。"""
    defs = [cdef(u"Kd%d%d" % (r, c), end=ENDS3[c][0], start=ENDS3[c][1], mem=mem_of(r)) for r in range(3) for c in range(3)]
    return grid_doc(u"Rd", 3, 3, lambda r, c: c, lambda r, c: u"Kd%d%d" % (r, c), defs)


def doc_e():
    u"""終わりの日も member の組も要素の線(行)で決まる(2 行 × 3 列)。行ごとに文脈 1 つ。"""
    defs = [cdef(u"Ke0", end=u"2024-03-31", mem=mem_of(0)), cdef(u"Ke1", end=u"2025-03-31", mem=mem_of(1))]
    return grid_doc(u"Re", 2, 3, lambda r, c: r, lambda r, c: u"Ke%d" % r, defs)


def doc_h(kind):
    u"""2 × 2 で全部同じ文脈。fact (1, 1) だけ ``kind``(name・unit・dec・scale)が違う。向き A・B のどちらでも決まる fact は 3。"""
    kw = {"name": dict(name=u"jppfs_cor:Rh9"), "unit": dict(unit=u"USD"), "dec": dict(dec=u"-3"), "scale": dict(scale=u"3")}[kind]
    rows = [[fx(**dict(dict(name=u"jppfs_cor:Rh", ctx=u"Kh0"), **(kw if (r, c) == (1, 1) else {}))) for c in range(2)] for r in range(2)]
    return cpage(tbl(rows), [cdef(u"Kh0")])


def doc_l():
    u"""表の中の fact 1 つ(書式 x)・表の外の fact 2 つ(書式 y)。書類の書式の最頻は表の外も数える。"""
    return cpage(tbl([[fx(ctx=u"Kl0", fmt=u"ixt:x")]]) + fx(ctx=u"Kl0", fmt=u"ixt:y") + fx(ctx=u"Kl0", fmt=u"ixt:y"), [cdef(u"Kl0")])


def doc_g(kind):
    u"""2 × 2 で文脈は列ごと。fact (1, 1) だけが別の文脈: ``end``(終わりの日だけ違う)・``member``(member の組だけ違う)・``both``(両方違う)。"""
    other = {"end": cdef(u"Kgx", end=u"2024-03-31", mem=mem_of(1)), "member": cdef(u"Kgx", mem=mem_of(9)), "both": cdef(u"Kgx", end=u"2024-03-31", mem=mem_of(9))}[kind]
    defs = [cdef(u"Kg0", mem=mem_of(0)), cdef(u"Kg1", mem=mem_of(1)), other]
    return grid_doc(u"Rg", 2, 2, lambda r, c: r, lambda r, c: u"Kgx" if (r, c) == (1, 1) else u"Kg%d" % c, defs)


def doc_j():
    u"""1 行 3 つ(線の決めは全部合う・符号が合わない 1・書式が合わない 1)。"""
    return cpage(tbl([[fx(sign=u"-", ctx=u"Kj0"), fx(ctx=u"Kj0"), fx(ctx=u"Kj0", fmt=u"ixt:other")]]), [cdef(u"Kj0")])


def doc_k():
    u"""表 1 つに fact と空の fact・表の外に fact 1 つ。"""
    return cpage(tbl([[fx(ctx=u"Kk0"), fx(ctx=u"Kk0", nil=True)]]) + fx(ctx=u"Kk0"), [cdef(u"Kk0")])


def doc_missing():
    u"""contextRef の指す定義が無い fact を持つ書類。"""
    return cpage(tbl([[fx(ctx=u"Kz0"), fx(ctx=u"Kz9")]]), [cdef(u"Kz0")])


def doc_broken():
    return u"<html><body><table><tr><td>%s</td></table></body></html>" % fx(name=u"jppfs_cor:BrE", ctx=u"B0")


def make_docs(d, htmls):
    u"""作り物の置き場。書類ごとに zip 1 つ(PublicDoc に xsd 1 つ・htm 1 つ・マニフェスト・画像)。ほかに有報でない zip を 1 つ。"""
    for i, h in enumerate(htmls, 1):
        with zipfile.ZipFile(os.path.join(d, "S2FAKE%02d.zip" % i), "w") as z:
            z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E9999%d-000_2026-03-31_01_2026-06-30.xsd" % i, b"<schema/>")
            z.writestr("XBRL/PublicDoc/0100000_a_E9999%d-000_ixbrl.htm" % i, h.encode("utf-8"))
            z.writestr("XBRL/PublicDoc/manifest_PublicDoc.xml", b"<manifest/>")
            z.writestr("XBRL/PublicDoc/logo.png", b"PNG")
    with zipfile.ZipFile(os.path.join(d, "S2OTHER1.zip"), "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


def make_zip(path, files):
    u"""PublicDoc に htm を複数持つ zip 1 つ(``files`` = [(名, 字)])。"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E99991-000_2026-03-31_01_2026-06-30.xsd", b"<schema/>")
        for n, t in files:
            z.writestr("XBRL/PublicDoc/%s" % n, t.encode("utf-8"))


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XA1-1", (82, 92)), ("XA1-2", (90, None)), ("XA1-3", (None, 3500)), ("XA1-4", None), ("XA1-5", (31, None)), ("XA1-6", (25, 38)), ("XA1-7", (None, 0.5)), ("XA1-8", (15, None))])
SEAL_BOUND_TEXT = od([("XA1-1", u"fact の 82% 以上 92% 未満"), ("XA1-2", u"fact の 90% 以上"), ("XA1-3", u"3500 以下"), ("XA1-4", u"いちばん多いのは `name`"), ("XA1-5", u"31 本以上"),
                      ("XA1-6", u"25% 以上 38% 未満"), ("XA1-7", u"fact の 0.5% 以下"), ("XA1-8", u"15% 以上")])
SEAL_RULE_PHRASES = (
    u"**終わりの日**: `instant` の日か、`endDate` の日。",
    u"**member の組**: `dimension` と member の字の組を、字の順に並べたもの(無ければ空の組)。",
    u"向き(A・B)× 終わりの日を決める線(文脈の線・要素の線)× member の組を決める線(文脈の線・要素の線)の 8 通りを試し",
    u"同じなら、この順で先のもの: 向き A が先・終わりの日は文脈の線が先・member の組は文脈の線が先(向き → 終わりの日 → member の組の順に比べる)",
    u"3(向き・終わりの日を決める線・member の組を決める線)+ fact の在る要素の線の数 × 4 + 終わりの日を決める側の fact の在る線の数 × 1 + member の組を決める側の fact の在る線の数 × 1",
    u"空の fact の数 × 1、表の中で全部決まらない fact の数 × 7、表の外の fact の数 × 7",
    u"**書く欄の比** = 書く欄の数 ÷(fact の数 × 7)",
    u"同じ `id` が 2 つ以上の file に在るときは、読んだ中身が同じでなければその書類は「断った」",
    u"fact の `contextRef` が指す `id` の定義が書類の中に無ければ「断った」",
    u"`typedMember` が 1 つでも在る文脈を指す fact が在る書類は「断った」に数えず",
    u"**62 本・5 本の全部の数が便 XA0 の記録と同じでなければ、この便は止める**",
    u"便 XA0 の script の関数は呼ぶ(写さない・変えない)",
    u"段 0 が便 XA0 の記録と違う(止める)・段 2 の全部決まる fact がちょうど 100%・段 2 が段 1 より少ない・段 1 が段 0 より少ない・断った書類が 6 本以上",
    u"始まりの日が違う期間の文脈を指す fact の数",
    u"同じ `name` の fact が時点の文脈と期間の文脈の両方を指している `name` の数と、その fact の数")
SEAL_LIMIT_PHRASES = (u"線の決めは答えから作っている", u"段 2 は表ごとに 8 通りから良いものを選ぶので", u"字の比べなので", u"便 XA0 の限界の全部", u"未使用の書類での確かめではない", u"「XBRL を作れる」「専用の道具が要らない」")
LIMIT_PHRASES = (u"線の決めは答え", u"8 通りからの選びも答えを見て選んでいる", u"便 XA0 の限界の全部", u"段 2 は表ごとに 8 通りから良いものを選ぶので", u"字の比べなので", u"未使用の書類での確かめではない",
                 u"「XBRL を作れる」「専用の道具が要らない」")


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out_ = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL or ms.PRIOR_RECORD_REL != PRIOR_RECORD_REL:
        out_.append(u"script の封の commit・path・記録の path が門と違う")
    if RECORD_REL not in seal:
        out_.append(u"封に記録の path が無い")
    if tuple(ms.ORIENTS) != ("A", "B") or tuple(ms.LINE_SRCS) != ("C", "E"):
        out_.append(u"向き・線の種類が封と違う")
    if tuple(ms.COMBOS) != ("ACC", "ACE", "AEC", "AEE", "BCC", "BCE", "BEC", "BEE"):
        out_.append(u"8 通りの並び(同点の順)が封と違う")
    if ms.CELL_PER_TABLE != 3 or ms.CELL_PER_ELEMENT_LINE != 4 or ms.CELL_PER_END_LINE != 1 or ms.CELL_PER_MEMBER_LINE != 1 or ms.CELLS_PER_FACT != 7:
        out_.append(u"書く欄の式の数(3・4・1・1・7)が封と違う")
    if ms.DOCS_WANT != 67 or ms.DEV_COUNT != 5:
        out_.append(u"67 本・開発の 5 本が封と違う")
    if ms.DOC_FULL_PCT != 90 or ms.SUSPECT_DECLINED != 6 or ms.DOC_FULL_PCT != ms.X.DOC_FULL_PCT:
        out_.append(u"書類 90%・欠陥を疑う条件の数が封と違う")
    if tuple(ms.STAGE_LABELS) != (u"段 0", u"段 1", u"段 2"):
        out_.append(u"段の名が封と違う")
    if (ms.KIND_INSTANT, ms.KIND_DURATION, ms.KIND_NONE) != ("I", "D", "N"):
        out_.append(u"期間の種類の符号が違う")
    for p in SEAL_RULE_PHRASES:
        if p not in seal:
            out_.append(u"封に字が無い: %s" % p[:30])
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS) or tuple(ms.BOUNDS_UPPER_EXCLUSIVE) != ("XA1-1", "XA1-6"):
        out_.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [x for x in seal.splitlines() if x.startswith(u"| %s" % k)]
        if len(row_) != 1 or t not in row_[0]:
            out_.append(u"封の予測の行の字が違う: %s" % k)
    for p in SEAL_LIMIT_PHRASES:
        if p not in seal.split(u"## §6", 1)[-1]:
            out_.append(u"封に限界の字が無い: %s" % p)
    for p in LIMIT_PHRASES:
        if p not in u"".join(ms.LIMITS):
            out_.append(u"限界の字が script に無い: %s" % p)
    if u"docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・member の名・日付・表の字" not in seal:
        out_.append(u"封の記録の禁止の字が違う")
    return out_


def seal_history_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "log", "--format=%H", "--", PREFIX + SEAL_REL], stdout=subprocess.PIPE, universal_newlines=True)
    hs = [x for x in rc.stdout.split() if x]
    if len(hs) != 1 or not hs[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の file の履歴が封 %s の 1 commit でない" % SEAL_COMMIT_SHORT]
    blob = subprocess.run(["git", "-C", root, "show", "%s:%s" % (hs[0], PREFIX + SEAL_REL)], stdout=subprocess.PIPE).stdout.decode("utf-8")
    if blob != seal_text():
        return [u"今の封が封の commit の blob と違う"]
    return []


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    pr = load_order_helpers()
    others = list(ORDER_FILES) if others is None else others
    return list(pr.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % x for x in rc.stdout.splitlines() if x.strip()]


def record_tracked(root=REPO):
    rc = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", PREFIX + RECORD_REL], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return rc.returncode == 0


# ======================================================================== 2. 文脈の読み方
def ctxread_problems(ms=None):
    ms = ms or MS
    out_ = []
    xml = lambda cid, per, scen=u"", attrs=u"": u'<xbrli:context %sid="%s"><xbrli:entity><xbrli:identifier scheme="x">E</xbrli:identifier></xbrli:entity><xbrli:period>%s</xbrli:period>%s</xbrli:context>' % (attrs, cid, per, scen)
    mem = lambda d, m: u'<xbrldi:explicitMember dimension="%s">%s</xbrldi:explicitMember>' % (d, m)
    # 期間 3 通り(時点・期間・なし)。日の字は前後の空白を落とす
    got = dict(ms.contexts_of_text(
        xml(u"i1", u"<xbrli:instant> 2025-03-31 \n</xbrli:instant>") + xml(u"d1", u"<xbrli:startDate>2024-04-01</xbrli:startDate><xbrli:endDate>2025-03-31</xbrli:endDate>") + xml(u"n1", u"<xbrli:forever/>")))
    want_eq(out_, u"時点", got.get(u"i1"), ("I", u"", u"2025-03-31", (), False))
    want_eq(out_, u"期間", got.get(u"d1"), ("D", u"2024-04-01", u"2025-03-31", (), False))
    want_eq(out_, u"期間なし", got.get(u"n1"), ("N", u"", u"", (), False))
    # 時点が在れば時点(endDate があっても)・endDate だけなら始まりは空
    got = dict(ms.contexts_of_text(xml(u"x1", u"<xbrli:instant>2025-01-01</xbrli:instant><xbrli:endDate>2025-03-31</xbrli:endDate>") + xml(u"x2", u"<xbrli:endDate>2025-02-02</xbrli:endDate>")))
    want_eq(out_, u"時点が先", got.get(u"x1"), ("I", u"", u"2025-01-01", (), False))
    want_eq(out_, u"endDate だけ", got.get(u"x2"), ("D", u"", u"2025-02-02", (), False))
    # member の組は字の順に並べる(入れた順に依らない)・空白を落とす
    c1 = xml(u"m1", u"<xbrli:instant>2025-03-31</xbrli:instant>", u"<xbrli:scenario>" + mem(u"b:Z", u"b:Q") + mem(u"a:Y", u" a:P ") + u"</xbrli:scenario>")
    c2 = xml(u"m2", u"<xbrli:instant>2025-03-31</xbrli:instant>", u"<xbrli:scenario>" + mem(u"a:Y", u"a:P") + mem(u"b:Z", u"b:Q") + u"</xbrli:scenario>")
    got = dict(ms.contexts_of_text(c1 + c2))
    want_eq(out_, u"member の組の並び", got.get(u"m1"), ("I", u"", u"2025-03-31", ((u"a:Y", u"a:P"), (u"b:Z", u"b:Q")), False))
    if got.get(u"m1") != got.get(u"m2"):
        out_.append(u"同じ member の組が入れた順で違う中身になる")
    # typedMember: (dimension, 中身の字(タグを除く))の組・typed の印
    typed = u'<xbrldi:typedMember dimension="t:Dim"><t:key> <b>k1</b> </t:key></xbrldi:typedMember>'
    got = dict(ms.contexts_of_text(xml(u"t1", u"<xbrli:instant>2025-03-31</xbrli:instant>", u"<xbrli:scenario>" + typed + mem(u"a:Y", u"a:P") + u"</xbrli:scenario>")))
    want_eq(out_, u"typedMember", got.get(u"t1"), ("I", u"", u"2025-03-31", ((u"a:Y", u"a:P"), (u"t:Dim", u"k1")), True))
    # id: xml:id でなく id・単引用符・接頭辞なしの context・属性の順
    got = ms.contexts_of_text(u"<context xml:id=\"Z\" id='q1'><period><instant>2025-03-31</instant></period></context>")
    want_eq(out_, u"id は xml:id でない・単引用符・接頭辞なし", [c[0] for c in got], [u"q1"])
    got = ms.contexts_of_text(u'<xbrli:context id="a1"><xbrli:period><xbrli:instant>2025-03-31</xbrli:instant></xbrli:period></xbrli:context><xbrli:context><xbrli:period><xbrli:instant>2025-03-31</xbrli:instant></xbrli:period></xbrli:context>')
    want_eq(out_, u"id の無い定義は数えない", [c[0] for c in got], [u"a1"])
    # コメントの中の定義は読まない・自己閉じの context は定義でない(次の定義の閉じタグまで食わない)・contextRef・contextXYZ は context でない
    got = ms.contexts_of_text(u'<!-- ' + xml(u"c1", u"<xbrli:instant>2025-03-31</xbrli:instant>") + u' -->' + u'<xbrli:context id="s1"/>'
                              + u'<xbrli:contextual id="w1"><xbrli:instant>2025-02-02</xbrli:instant></xbrli:contextual>' + xml(u"r1", u"<xbrli:instant>2025-01-01</xbrli:instant>")
                              + u'<ix:nonFraction contextRef="r1" name="a:b">1</ix:nonFraction>')
    want_eq(out_, u"コメント・自己閉じ・似た名", [(c[0], c[1][2]) for c in got], [(u"r1", u"2025-01-01")])
    # 同じ id: 同じ中身なら通り(別の file でも・member の順が違っても)・中身が違えば断る(別の file でも・同じ file の中でも)
    a = cpage(u"", [cdef(u"X1", mem=[(u"a:Y", u"a:P"), (u"b:Z", u"b:Q")])])
    b = cpage(u"", [cdef(u"X1", mem=[(u"b:Z", u"b:Q"), (u"a:Y", u"a:P")])])
    c = cpage(u"", [cdef(u"X1", mem=[(u"b:Z", u"b:Q")])])
    want_eq(out_, u"同じ中身の同じ id", len(ms.context_defs([(u"a.htm", a), (u"b.htm", b)])), 1)
    want_eq(out_, u"中身の違う同じ id(別の file)", refuses(ms, ms.context_defs, [(u"a.htm", a), (u"c.htm", c)]), ms.R_CTX_DUP)
    want_eq(out_, u"中身の違う同じ id(同じ file)", refuses(ms, ms.context_defs, [(u"a.htm", cpage(u"", [cdef(u"X1", end=u"2025-03-31"), cdef(u"X1", end=u"2025-03-30")]))]), ms.R_CTX_DUP)
    want_eq(out_, u"期間の種類だけ違う同じ id", refuses(ms, ms.context_defs, [(u"a.htm", cpage(u"", [cdef(u"X1"), cdef(u"X1", start=u"2024-04-01")]))]), ms.R_CTX_DUP)
    want_eq(out_, u"始まりだけ違う同じ id", refuses(ms, ms.context_defs, [(u"a.htm", cpage(u"", [cdef(u"X1", start=u"2024-04-01"), cdef(u"X1", start=u"2024-04-02")]))]), ms.R_CTX_DUP)
    # contextRef の定義が無い・属性が無い
    defs = ms.context_defs([(u"a.htm", cpage(u"", [cdef(u"X1")]))])
    fs = [dict(attrs={"contextRef": u"X1"}), dict(attrs={"contextRef": u"X2"})]
    want_eq(out_, u"定義の無い contextRef", refuses(ms, ms.resolve_facts, fs, defs), ms.R_CTX_MISSING)
    want_eq(out_, u"contextRef の属性が無い", refuses(ms, ms.resolve_facts, [dict(attrs={})], defs), ms.R_CTX_MISSING)
    want_eq(out_, u"定義が在る contextRef", [c[2] for c in ms.resolve_facts(fs[:1], defs)], [u"2025-03-31"])
    # 終わりの日・member の組・対
    c = ("D", u"2024-04-01", u"2025-03-31", ((u"a:Y", u"a:P"),), False)
    want_eq(out_, u"終わりの日・member の組・対", (ms.end_of(c), ms.members_of(c), ms.pair_of(c)), (u"2025-03-31", ((u"a:Y", u"a:P"),), (u"2025-03-31", ((u"a:Y", u"a:P"),))))
    want_eq(out_, u"時点と期間で終わりの日と member の組が同じなら対が同じ", ms.pair_of(("I", u"", u"2025-03-31", (), False)), ms.pair_of(("D", u"2024-04-01", u"2025-03-31", (), False)))
    want_eq(out_, u"終わりの日が違えば対が違う", ms.pair_of(("I", u"", u"2025-03-30", (), False)) == ms.pair_of(("I", u"", u"2025-03-31", (), False)), False)
    want_eq(out_, u"member の組が違えば対が違う", ms.pair_of(("I", u"", u"2025-03-31", ((u"a", u"b"),), False)) == ms.pair_of(("I", u"", u"2025-03-31", (), False)), False)
    return out_


# ======================================================================== 3. 数え方
def numbers(ms, html):
    fs = ms.X.facts_of_text(html)
    a0 = ms.X.count_facts(fs)
    return ms.count_doc(fs, ms.context_defs([(u"a.htm", html)]), a0)


def summary(ms, d):
    a2 = d["a2"]
    return ((d["a0"]["full"], d["a1"]["full"], a2["full"]), (ms.X.cells_of(d["a0"]), ms.X.cells_of(d["a1"]), ms.cells2(a2)), [c for c in ms.COMBOS for _ in range(a2["k_" + c])])


def form_problems(ms=None):
    ms = ms or MS
    out_ = []
    # (全部決まる 段 0・段 1・段 2)(書く欄 段 0・段 1・段 2)(選んだ 8 通り)。手で数えた値
    for what, html, want in (
            (u"member が列・終わりの日が行(向き A・要素の線で終わりの日・文脈の線で member)", doc_b(), ((3, 3, 9), (59, 59, 22), ["AEC"])),
            (u"時点と期間が同じ行に並ぶ表(id だけ違う・段 1 で収まる・同点は ACC)", doc_a(), ((2, 4, 4), (26, 12, 16), ["ACC"])),
            (u"終わりの日が列・member が行(文脈の線で終わりの日・要素の線で member)", doc_c(), ((2, 2, 6), (44, 44, 21), ["ACE"])),
            (u"転置(向き B・要素の線で終わりの日・文脈の線で member)", doc_d(), ((3, 3, 9), (59, 59, 22), ["BEC"])),
            (u"終わりの日も member の組も要素の線(2 行 × 3 列)", doc_e(), ((3, 3, 6), (34, 34, 16), ["AEE"])),
            (u"表の外の fact の書式が書類の最頻になる(表の中の fact は書式が合わない)", doc_l(), ((0, 0, 0), None, ["ACC"])),
            (u"終わりの日だけ違う fact が 1 つ", doc_g("end"), ((3, 3, 3), None, ["ACC"])),
            (u"member の組だけ違う fact が 1 つ", doc_g("member"), ((3, 3, 3), None, ["ACC"])),
            (u"両方違う fact が 1 つ", doc_g("both"), ((3, 3, 3), None, ["ACC"])),
            (u"符号・書式が合わない fact は全部決まらない(決まるは 3・全部決まるは 1)", doc_j(), ((1, 1, 1), (23, 23, 28), ["ACC"])),
            (u"空の fact・表の外の fact", doc_k(), ((2, 2, 2), (16, 16, 20), ["ACC"]))):
        d = guard(numbers, ms, html)
        if isinstance(d, list):
            out_.append(u"%s: %s" % (what, d))
            continue
        got = summary(ms, d)
        if want[1] is None:
            got = (got[0], None, got[2])
        want_eq(out_, what, got, want)
    # 理由の数え分け(終わりの日と member の組を別に数える・どちらかが違えば 1)
    for kind, (r_end, r_mem, anyn) in (("end", (1, 0, 1)), ("member", (0, 1, 1)), ("both", (1, 1, 1))):
        a2 = numbers(ms, doc_g(kind))["a2"]
        want_eq(out_, u"段 2 の理由 %s" % kind, (a2["r_end"], a2["r_member"], a2["r_endmember_any"], a2["r_name"], a2["r_unit"], a2["r_decimals"], a2["r_scale"]), (r_end, r_mem, anyn, 0, 0, 0, 0))
        a1 = numbers(ms, doc_g(kind))["a1"]
        want_eq(out_, u"段 1 は対の違いで 1 つ・理由は対の欄だけ(%s)" % kind, (a1["r_context"], a1["r_name"], a1["decided"]), (1, 0, 3))
        a0 = numbers(ms, doc_g(kind))["a0"]
        want_eq(out_, u"段 0 は contextRef の違いで 1 つ(%s)" % kind, (a0["r_context"], a0["decided"]), (1, 3))
    # name・unitRef・decimals・scale の理由は便 XA0 の線の決めのまま(段 1・段 2 とも 1 つだけ数える)
    for kind, key in (("name", "r_name"), ("unit", "r_unit"), ("dec", "r_decimals"), ("scale", "r_scale")):
        dd = numbers(ms, doc_h(kind))
        want_one = dict((k, 1 if k == key else 0) for k in ("r_name", "r_unit", "r_decimals", "r_scale"))
        for lab, acc in (("段 1", dd["a1"]), ("段 2", dd["a2"])):
            want_eq(out_, u"%s の理由 %s" % (lab, kind), dict((k, acc[k]) for k in want_one), want_one)
            want_eq(out_, u"%s の決まる fact(%s)" % (lab, kind), (acc["decided"], acc["full"]), (3, 3))
        want_eq(out_, u"段 2 は終わりの日・member の組の違いを数えない(%s)" % kind, (dd["a2"]["r_end"], dd["a2"]["r_member"], dd["a2"]["r_endmember_any"]), (0, 0, 0))
    # 段 1 の対は元の fact を書き換えない・段 0 の数は count_facts のまま
    fs = ms.X.facts_of_text(doc_a())
    defs = ms.context_defs([(u"a.htm", doc_a())])
    before = [dict(f["attrs"]) for f in fs]
    ms.pair_facts(fs, ms.resolve_facts(fs, defs))
    if [f["attrs"] for f in fs] != before:
        out_.append(u"pair_facts が元の fact の attrs を書き換えた")
    pf = ms.pair_facts(fs, ms.resolve_facts(fs, defs))
    want_eq(out_, u"対に置き換えた contextRef", [f["attrs"]["contextRef"] for f in pf], [(u"2025-03-31", ())] * 4)
    want_eq(out_, u"置き換え以外の属性は同じ", [dict((k, v) for k, v in f["attrs"].items() if k != "contextRef") for f in pf], [dict((k, v) for k, v in a.items() if k != "contextRef") for a in before])
    d = numbers(ms, doc_a())
    want_eq(out_, u"段 0 は便 XA0 の count_facts と同じ", dict(d["a0"]), dict(ms.X.count_facts(ms.X.facts_of_text(doc_a()))))
    # 書く欄の項(段 2)と欄の並び
    a2 = numbers(ms, doc_k())["a2"]
    want_eq(out_, u"書く欄の項(空の fact・表の外)", (a2["c_table"], a2["c_elem"], a2["c_end"], a2["c_member"], a2["c_formats"], a2["c_nil"], a2["c_undecided"], a2["c_outside"]), (3, 4, 2, 2, 1, 1, 0, 7))
    a2 = numbers(ms, doc_c())["a2"]
    want_eq(out_, u"書く欄の項(終わりの日は文脈の線・member は要素の線)", (a2["c_table"], a2["c_elem"], a2["c_end"], a2["c_member"], a2["c_formats"], a2["c_undecided"]), (3, 12, 2, 3, 1, 0))
    a2 = numbers(ms, doc_b())["a2"]
    want_eq(out_, u"書く欄の項(終わりの日は要素の線・member は文脈の線)", (a2["c_table"], a2["c_elem"], a2["c_end"], a2["c_member"]), (3, 12, 3, 3))
    want_eq(out_, u"段 2 の表の数・文脈の線・文脈の線を選ばなかった表", (a2["tables"], a2["tables_not_cc"], a2["inside"], a2["decided"]), (1, 1, 9, 9))
    if list(a2) != list(ms.S2_KEYS) or list(numbers(ms, doc_a())["a2"]) != list(ms.S2_KEYS):
        out_.append(u"段 2 の欄の並びが違う")
    a2 = numbers(ms, doc_a())["a2"]
    want_eq(out_, u"ACC を選んだ表は文脈の線・文脈の線を選ばなかった表に数えない", (a2["tables_not_cc"], a2["k_ACC"], a2["k_AEE"]), (0, 1, 0))
    # 全部決まる fact の数が表の中の決まる fact より多くならない・表が複数
    two = cpage(tbl([[fx(ctx=u"Kt0")]]) + tbl([[fx(name=u"jppfs_cor:T9", ctx=u"Kt0"), fx(name=u"jppfs_cor:T9", ctx=u"Kt1")]]), [cdef(u"Kt0"), cdef(u"Kt1", end=u"2024-03-31")])
    a2 = numbers(ms, two)["a2"]
    want_eq(out_, u"表が 2 つ", (a2["tables"], a2["decided"], a2["full"], a2["c_table"], a2["c_elem"], a2["c_end"], a2["c_member"]), (2, 3, 3, 6, 8, 3, 3))
    return out_


def item(row, col, name=u"N", ctx=u"C", unit=u"JPY", dec=u"0", scale=None, nil=False):
    a = {"name": name, "contextRef": ctx}
    if unit is not None:
        a["unitRef"] = unit
    if not nil:
        if dec is not None:
            a["decimals"] = dec
        if scale is not None:
            a["scale"] = scale
    return dict(attrs=a, nil=nil, text=u"1", table=0, row=row, col=col, between=u"")


def grid(orient, end_by, mem_by, name_by=None, n=3):
    u"""n × n の表。``end_by``・``mem_by`` = None(全部同じ)か "E"(要素の線の番号で決まる)か "C"(文脈の線の番号で決まる)。``name_by`` は既定で向きに合う(向き A は行・B は列)。"""
    items, ends, mems = [], [], []
    for r in range(n):
        for c in range(n):
            e_idx, c_idx = (r, c) if orient == "A" else (c, r)
            items.append(item(r, c, name=u"N%d" % (e_idx if name_by is None else name_by(r, c))))
            ends.append(u"2025-0%d" % {None: 1, "E": e_idx + 1, "C": c_idx + 1}[end_by])
            mems.append(((u"D", u"M%d" % {None: 0, "E": e_idx, "C": c_idx}[mem_by]),))
    return items, ends, mems


def combo_problems(ms=None):
    ms = ms or MS
    out_ = []
    # 8 通りのそれぞれが、そのときだけ全部決まるように作った表で選ばれる(3 × 3 の 9 つ)
    for combo in ms.COMBOS:
        o, es, mstr = combo
        items, ends, mems = grid(o, es, mstr)
        d, got, flags, lines, _tally = ms.choose_combo(items, ends, mems)
        want_eq(out_, u"8 通り %s" % combo, (d, got, sum(1 for fl in flags if not any(fl))), (9, combo, 9))
        want_eq(out_, u"線の数 %s" % combo, lines, (3, 3, 0))
    # 同点の順: 向き A が先
    items, ends, mems = grid("A", None, None)
    want_eq(out_, u"何も違わない(向き A が先・文脈の線が先)", ms.choose_combo(items, ends, mems)[:2], (9, "ACC"))
    items, ends, mems = grid("B", None, None)
    want_eq(out_, u"何も違わない(要素の名が列で決まる)", ms.choose_combo(items, ends, mems)[:2], (9, "BCC"))
    items, ends, mems = grid("A", None, None, name_by=lambda r, c: 0)
    want_eq(out_, u"向き A・B が同点", ms.choose_combo(items, ends, mems)[:2], (9, "ACC"))
    items, ends, mems = grid("A", "E", None)
    want_eq(out_, u"終わりの日が要素の線・member は同じ(member は文脈の線が先)", ms.choose_combo(items, ends, mems)[:2], (9, "AEC"))
    items, ends, mems = grid("A", None, "E")
    want_eq(out_, u"終わりの日は同じ・member が要素の線(終わりの日は文脈の線が先)", ms.choose_combo(items, ends, mems)[:2], (9, "ACE"))
    items, ends, mems = grid("A", "C", None)
    want_eq(out_, u"終わりの日が文脈の線", ms.choose_combo(items, ends, mems)[:2], (9, "ACC"))
    items, ends, mems = grid("B", "E", None)
    want_eq(out_, u"向き B・終わりの日が要素の線", ms.choose_combo(items, ends, mems)[:2], (9, "BEC"))
    items, ends, mems = grid("B", None, "E")
    want_eq(out_, u"向き B・member が要素の線", ms.choose_combo(items, ends, mems)[:2], (9, "BCE"))
    # 向き A が少なければ B(向きを先に比べる)・決まる fact が多い方を選ぶ(1 つ違えば)
    items, ends, mems = grid("B", "E", "E")
    got = ms.choose_combo(items, ends, mems)
    want_eq(out_, u"向き B で終わりの日も member も要素の線", (got[0], got[1]), (9, "BEE"))
    items, ends, mems = grid("A", "C", "C")
    ends[8] = u"2099-01"
    got = ms.choose_combo(items, ends, mems)
    want_eq(out_, u"1 つだけ終わりの日が違う", (got[0], got[1], sum(1 for fl in got[2] if fl[1]), sum(1 for fl in got[2] if fl[2])), (8, "ACC", 1, 0))
    mems[0] = ((u"D", u"M9"),)
    got = ms.choose_combo(items, ends, mems)
    want_eq(out_, u"終わりの日と member の組が別の fact で違う", (got[0], sum(1 for fl in got[2] if fl[1]), sum(1 for fl in got[2] if fl[2]), sum(1 for fl in got[2] if any(fl))), (7, 1, 1, 2))
    # ACE と AEC だけが同点で最多(手で数えた 3 × 3。向き A・要素の名は行ごと)。封の順で先の ACE(終わりの日は文脈の線が先)
    ends_rows, mems_rows = (u"baa", u"baa", u"abb"), (u"xyx", u"yxy", u"xxy")
    items = [item(r, c, name=u"N%d" % r) for r in range(3) for c in range(3)]
    ends = [ends_rows[r][c] for r in range(3) for c in range(3)]
    mems = [mems_rows[r][c] for r in range(3) for c in range(3)]
    got = ms.choose_combo(items, ends, mems)
    want_eq(out_, u"ACE と AEC が同点(先の ACE)", (got[0], got[1], dict(got[4])), (4, "ACE", dict(ACC=3, ACE=4, AEC=4, AEE=3, BCC=got[4]["BCC"], BCE=got[4]["BCE"], BEC=got[4]["BEC"], BEE=got[4]["BEE"])))
    if max(got[4][k] for k in ("BCC", "BCE", "BEC", "BEE")) >= 4:
        out_.append(u"向き B が 4 以上(手で数えた表と違う)")
    # 線の決めは空の fact も含む全部の fact の最頻(並んだら先)
    items = [item(0, 0), item(0, 1), item(0, 2)]
    want_eq(out_, u"最頻の線の決め(2 対 1)", ms.line_flags([0, 0, 0], [u"a", u"b", u"b"]), [True, False, False])
    want_eq(out_, u"最頻が並ぶ(先の値)", ms.line_flags([0, 0], [u"q", u"p"]), [False, True])
    want_eq(out_, u"線ごとに決める(並んだら先)", ms.line_flags([0, 1, 0, 1], [u"a", u"b", u"a", u"c"]), [False, False, False, True])
    want_eq(out_, u"線ごとに決める(違う値)", ms.line_flags([0, 1, 0, 1, 1], [u"a", u"b", u"a", u"c", u"c"]), [False, True, False, False, False])
    return out_


def stats_problems(ms=None):
    ms = ms or MS
    out_ = []
    mk = lambda name, ctx: fx(name=name, ctx=ctx)
    # 期間の種類が 2 つ在る name: N0 は時点 2・期間 1(3 fact)・N1 は時点だけ・N2 は期間だけ 2 つ・N3 は期間なしの文脈と時点・N4 は期間なしの文脈と期間(どちらも数えない)
    forever = u'<xbrli:context id="Fn"><xbrli:entity><xbrli:identifier scheme="x">E</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:forever/></xbrli:period></xbrli:context>'
    body = mk(u"jppfs_cor:N0", u"I1") + mk(u"jppfs_cor:N0", u"I2") + mk(u"jppfs_cor:N0", u"D1") + mk(u"jppfs_cor:N1", u"I1") + mk(u"jppfs_cor:N2", u"D1") + mk(u"jppfs_cor:N2", u"D2") \
        + mk(u"jppfs_cor:N3", u"Fn") + mk(u"jppfs_cor:N3", u"I1") + mk(u"jppfs_cor:N4", u"Fn") + mk(u"jppfs_cor:N4", u"D1")
    html = cpage(body, [cdef(u"I1"), cdef(u"I2", end=u"2024-03-31"), cdef(u"D1", start=u"2024-04-01"), cdef(u"D2", end=u"2024-03-31", start=u"2023-04-01"), forever])
    st = numbers(ms, html)["x"]
    want_eq(out_, u"期間の種類が 2 つ在る name", (st["mixed_names"], st["mixed_facts"]), (1, 3))
    want_eq(out_, u"文脈の定義の数", st["ctx_defs"], 5)
    # 始まりの日が違う期間の文脈: D1(2024-04-01)・D2(2025-01-01)は終わりの日と member の組が同じで始まりが違う(2 つとも数える)・D3 は同じ中身の別 id(数える)・
    # D4 は member が違うので束が別(数えない)・I1 は時点(数えない)・D5 は同じ終わりの日の時点 I2 と束ねない(期間は 1 つだけなので数えない)
    body = mk(u"jppfs_cor:S0", u"D1") + mk(u"jppfs_cor:S0", u"D2") + mk(u"jppfs_cor:S0", u"D3") + mk(u"jppfs_cor:S0", u"D4") + mk(u"jppfs_cor:S0", u"I1") + mk(u"jppfs_cor:S0", u"D1") \
        + mk(u"jppfs_cor:S0", u"D5") + mk(u"jppfs_cor:S0", u"I2")
    html = cpage(body, [cdef(u"D1", start=u"2024-04-01"), cdef(u"D2", start=u"2025-01-01"), cdef(u"D3", start=u"2024-04-01"), cdef(u"D4", start=u"2024-04-01", mem=mem_of(0)), cdef(u"I1"),
                        cdef(u"D5", end=u"2024-03-31", start=u"2023-04-01"), cdef(u"I2", end=u"2024-03-31")])
    st = numbers(ms, html)["x"]
    want_eq(out_, u"始まりの日が違う期間の文脈を指す fact", st["startdiff_facts"], 4)
    body = mk(u"jppfs_cor:S0", u"D1") + mk(u"jppfs_cor:S0", u"D3") + mk(u"jppfs_cor:S0", u"D4")
    html = cpage(body, [cdef(u"D1", start=u"2024-04-01"), cdef(u"D3", start=u"2024-04-01"), cdef(u"D4", start=u"2024-04-01", mem=mem_of(0))])
    want_eq(out_, u"始まりの日が同じなら数えない", numbers(ms, html)["x"]["startdiff_facts"], 0)
    # member を持つ文脈を指す fact(typedMember の文脈は read_context が印を付ける)
    body = mk(u"jppfs_cor:M0", u"M1") + mk(u"jppfs_cor:M0", u"I1") + mk(u"jppfs_cor:M0", u"M1")
    html = cpage(body, [cdef(u"M1", mem=mem_of(2)), cdef(u"I1")])
    st = numbers(ms, html)["x"]
    want_eq(out_, u"member を 1 つ以上持つ文脈を指す fact・typedMember", (st["member_facts"], st["typed_facts"]), (2, 0))
    typed = u'<xbrldi:typedMember dimension="t:Dim"><t:key>k</t:key></xbrldi:typedMember>'
    defs = od(ms.contexts_of_text(u'<xbrli:context id="T1"><xbrli:entity><xbrli:identifier scheme="x">E</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-03-31</xbrli:instant></xbrli:period>'
                                  u'<xbrli:scenario>' + typed + u'</xbrli:scenario></xbrli:context>' + cdef(u"I1")))
    fs = [dict(attrs={"name": u"a", "contextRef": u"T1"}), dict(attrs={"name": u"a", "contextRef": u"T1"}), dict(attrs={"name": u"a", "contextRef": u"I1"})]
    st = ms.context_stats(fs, defs, ms.resolve_facts(fs, defs))
    want_eq(out_, u"typedMember を持つ文脈を指す fact は member の fact にも数える", (st["typed_facts"], st["member_facts"], st["ctx_defs"]), (2, 2, 2))
    return out_


def refuse_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        ok = cpage(tbl([[fx(ctx=u"Q1")]]), [cdef(u"Q1")])
        miss = cpage(tbl([[fx(ctx=u"Q1"), fx(ctx=u"Q2")]]), [cdef(u"Q1")])
        dup_a = cpage(tbl([[fx(ctx=u"Q1")]]), [cdef(u"Q1")])
        dup_b = cpage(u"", [cdef(u"Q1", end=u"2025-03-30")])
        same_b = cpage(u"", [cdef(u"Q1")])
        p1, p2, p3, p4, p5 = [os.path.join(d, "z%d.zip" % i) for i in range(5)]
        make_zip(p1, [(u"0100000_a_ixbrl.htm", ok)])
        make_zip(p2, [(u"0100000_a_ixbrl.htm", miss)])
        make_zip(p3, [(u"0100000_a_ixbrl.htm", dup_a), (u"0200000_b_ixbrl.htm", dup_b)])
        make_zip(p4, [(u"0100000_a_ixbrl.htm", dup_a), (u"0200000_b_ixbrl.htm", same_b)])
        make_zip(p5, [(u"0100000_a_ixbrl.htm", u"<html><table><tr><td>%s</td></table></html>" % fx())])
        r = ms.read_doc(p1)
        want_eq(out_, u"通る書類", (r[0] is not None, r[1], r[2] is not None, r[3]), (True, u"", True, u""))
        r = ms.read_doc(p2)
        want_eq(out_, u"定義の無い contextRef を断る(便 XA0 の数は在る)", (r[0] is not None, r[1], r[2], r[3]), (True, u"", None, ms.R_CTX_MISSING))
        r = ms.read_doc(p3)
        want_eq(out_, u"別の file の中身の違う同じ id を断る", (r[0] is not None, r[1], r[2], r[3]), (True, u"", None, ms.R_CTX_DUP))
        r = ms.read_doc(p4)
        want_eq(out_, u"別の file の同じ中身の同じ id は通る", (r[2] is not None, r[3]), (True, u""))
        r = ms.read_doc(p5)
        want_eq(out_, u"便 XA0 の断りは同じ理由でそのまま(便 XA0 の数は無い)", (r[0], r[1], r[2], r[3]), (None, ms.X.R_TABLE, None, ms.X.R_TABLE))
        want_eq(out_, u"記録に書かない字を返す(要素の名・文脈の名・member の名)", (u"E0" in r[4], ), (False,))
        r = ms.read_doc(p1)
        want_eq(out_, u"記録に書かない字に要素の名と文脈の名が入る", (u"E0" in r[4], u"Q1" in r[4]), (True, True))
        # member の名・dimension の名も書かない字に入る
        pm = os.path.join(d, "zm.zip")
        make_zip(pm, [(u"0100000_a_ixbrl.htm", cpage(tbl([[fx(ctx=u"Q7")]]), [cdef(u"Q7", mem=[(u"jppfs_cor:SegAxis", u"jppfs_cor:MemberX")])]))])
        r = ms.read_doc(pm)
        want_eq(out_, u"dimension・member の局所名が書かない字に入る", (u"SegAxis" in r[4], u"MemberX" in r[4]), (True, True))
    return out_


def suspicion_problems(ms=None):
    ms = ms or MS
    stage = lambda full: {u"全部決まる fact の数": full}
    base = {u"fact の数": 100, ms.STAGE_LABELS[0]: stage(70), ms.STAGE_LABELS[1]: stage(80), ms.STAGE_LABELS[2]: stage(90), u"断った書類の数": 0}
    out_ = []
    want_eq(out_, u"何も当たらない", ms.suspicions(base), [])
    for what, change in ((u"段 2 の全部決まる fact がちょうど 100%", {ms.STAGE_LABELS[2]: stage(100)}), (u"段 2 が段 1 より少ない", {ms.STAGE_LABELS[2]: stage(79)}),
                         (u"段 1 が段 0 より少ない", {ms.STAGE_LABELS[1]: stage(69)}), (u"断った書類が 6 本以上", {u"断った書類の数": 6})):
        got = ms.suspicions(dict(base, **change))
        if got != [what]:
            out_.append(u"%s: 得 %r" % (what, got))
    # 境: 段 2 = 段 1 は当たらない・段 1 = 段 0 は当たらない・断った 5 本は当たらない
    want_eq(out_, u"段 2 = 段 1", ms.suspicions(dict(base, **{ms.STAGE_LABELS[2]: stage(80)})), [])
    want_eq(out_, u"段 1 = 段 0", ms.suspicions(dict(base, **{ms.STAGE_LABELS[1]: stage(70)})), [])
    want_eq(out_, u"断った 5 本", ms.suspicions(dict(base, **{u"断った書類の数": 5})), [])
    want_eq(out_, u"fact が無ければ 100% に当たらない", ms.suspicions(dict(base, **{u"fact の数": 0, ms.STAGE_LABELS[0]: stage(0), ms.STAGE_LABELS[1]: stage(0), ms.STAGE_LABELS[2]: stage(0)})), [])
    return out_


# ======================================================================== 4. 塊・判定・記録
def pipeline(ms, htmls, d, want, dev_count):
    u"""作り物の置き場と、その置き場から作った便 XA0 の記録(使い捨て)。(docs, 便 XA0 の記録の path)。"""
    docs = os.path.join(d, "docs")
    os.makedirs(docs)
    make_docs(docs, htmls)
    prior = ms.X.build_record(docs, want, dev_count)[0]
    pp = os.path.join(d, "prior.json")
    with io.open(pp, "w", encoding="utf-8") as fh:
        fh.write(ms.dumps(prior))
    return docs, pp


def chunk_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        docs, pp = pipeline(ms, [doc_b(), doc_broken(), doc_a(), doc_missing()], d, 4, 1)
        rec, _secret = ms.build_record(docs, want=4, dev_count=1, prior_path=pp)
    dev, prod = rec[u"開発の 5 本"], rec[u"本番だけの 62 本"]
    want_eq(out_, u"書類の行", [list(r.values()) for r in rec[u"書類"]], [[1, False, u"", 9, 3, 3, 9], [2, True, ms.X.R_TABLE, None, None, None, None], [3, False, u"", 4, 2, 4, 4],
                                                                       [4, True, ms.R_CTX_MISSING, None, None, None, None]])
    want_eq(out_, u"開発の塊(書類 b)", (dev[u"書類の数"], dev[u"断った書類の数"], dev[u"fact の数"], dev[u"文脈の定義の数"], dev[u"member を 1 つ以上持つ文脈を指す fact の数"],
                                   dev[u"typedMember を持つ文脈を指す fact の数"]), (1, 0, 9, 9, 9, 0))
    for label, want in ((u"段 0", (3, 3, 0, 59)), (u"段 1", (3, 3, 0, 59)), (u"段 2", (9, 9, 1, 22))):
        b = dev[label]
        want_eq(out_, u"開発の塊 %s" % label, (b[u"表の決めで決まる fact の数"], b[u"全部決まる fact の数"], b[u"全部決まる fact が 90% 以上の書類の数"], b[u"書く欄の数"]), want)
    want_eq(out_, u"本番の塊(書類 a と断った 2 本)", (prod[u"書類の数"], prod[u"断った書類の数"], prod[u"断らなかった書類の数"], prod[u"fact の数"], prod[u"文脈の定義の数"], prod[u"member を 1 つ以上持つ文脈を指す fact の数"]),
            (3, 2, 1, 4, 4, 0))
    want_eq(out_, u"断った理由ごとの数", dict(prod[u"断った理由ごとの数"]), {ms.X.R_TABLE: 1, ms.R_CTX_MISSING: 1})
    for label, want in ((u"段 0", (2, 2, 0, 26)), (u"段 1", (4, 4, 1, 12)), (u"段 2", (4, 4, 1, 16))):
        b = prod[label]
        want_eq(out_, u"本番の塊 %s" % label, (b[u"表の決めで決まる fact の数"], b[u"全部決まる fact の数"], b[u"全部決まる fact が 90% 以上の書類の数"], b[u"書く欄の数"]), want)
        want_eq(out_, u"本番の塊 %s の比" % label, (b[u"書く欄の比"][u"数"], b[u"書く欄の比"][u"分母"], b[u"fact の数 × 7"]), (want[3], 28, 28))
    want_eq(out_, u"本番の塊 段 0 の理由", list(prod[u"段 0"][u"決まらなかった理由ごとの fact の数(重ねて数える)"].values()), [0, 2, 0, 0, 0])
    want_eq(out_, u"本番の塊 段 1 の理由の名", list(prod[u"段 1"][u"決まらなかった理由ごとの fact の数(重ねて数える)"]), [u"name が線の決めと違う", u"対が線の決めと違う", u"unitRef が線の決めと違う",
                                                                                                           u"decimals が線の決めと違う", u"scale が線の決めと違う"])
    want_eq(out_, u"本番の塊 段 2 の理由の名", list(prod[u"段 2"][u"決まらなかった理由ごとの fact の数(重ねて数える)"]), [u"name が線の決めと違う", u"終わりの日が線の決めと違う", u"member の組が線の決めと違う",
                                                                                                           u"unitRef が線の決めと違う", u"decimals が線の決めと違う", u"scale が線の決めと違う"])
    s2 = prod[u"段 2"]
    want_eq(out_, u"本番の塊 段 2 の表", (s2[u"fact の在る表の数"], dict(s2[u"8 通りのそれぞれを選んだ表の数"]), s2[u"文脈の線・文脈の線を選ばなかった表の数"],
                                     s2[u"終わりの日か member の組が線の決めと違う fact の数(どちらかが違えば 1)"]), (1, dict((c, 1 if c == "ACC" else 0) for c in ms.COMBOS), 0, 0))
    want_eq(out_, u"本番の塊 段 2 の項", list(s2[u"書く欄の数(項ごと)"].values()), [3, 8, 2, 2, 1, 0, 0, 0])
    want_eq(out_, u"本番の塊 期間・始まり", (prod[u"期間の種類が 2 つ在る name の数"], prod[u"期間の種類が 2 つ在る name の fact の数"], prod[u"始まりの日が違う期間の文脈を指す fact の数"],
                                      prod[u"fact が 1 つ以上在る書類の数(断らなかった)"]), (2, 4, 0, 1))
    # 書類 90% の境(ちょうど 90% は含む)・断った書類は数えない
    for f, full, want_n in ((10, 9, 1), (10, 8, 0), (20, 18, 1), (21, 18, 0), (0, 0, 0)):
        want_eq(out_, u"90%% の境 %d/%d" % (full, f), ms.X.docs_full([{"fact": f, "full": full}]), want_n)
    # 判定に要る数
    j = list(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]].items())
    keys = [k.split(u" ")[0] for k, _v in j]
    want_eq(out_, u"判定の名", keys, [u"XA1-%d" % i for i in range(1, 9)])
    vals = [v for _k, v in j]
    want_eq(out_, u"XA1-1・XA1-2", [(v[u"数"], v[u"分母"], v[u"%"]) for v in vals[:2]], [(4, 4, 100.0), (4, 4, 100.0)])
    want_eq(out_, u"XA1-3", vals[2], {u"数": 0})
    want_eq(out_, u"XA1-4", dict(vals[3]), {u"理由ごとの数": od(zip((u"name の違い", u"終わりの日の違い", u"member の組の違い", u"unitRef の違い", u"decimals の違い", u"scale の違い"), (0, 0, 0, 0, 0, 0))),
                                           u"いちばん多い理由": [u"name の違い", u"終わりの日の違い", u"member の組の違い", u"unitRef の違い", u"decimals の違い", u"scale の違い"]})
    want_eq(out_, u"XA1-5", dict(vals[4]), {u"書類": 1, u"分母": 1})
    want_eq(out_, u"XA1-6", (vals[5][u"数"], vals[5][u"分母"], vals[5][u"%"]), (16, 28, 57.1))
    want_eq(out_, u"XA1-7・XA1-8", [(v[u"数"], v[u"分母"], v[u"%"]) for v in vals[6:]], [(4, 4, 100.0), (0, 1, 0.0)])
    return out_


def judged_problems(ms=None):
    ms = ms or MS
    out_ = []
    d = lambda f0, f1, f2, endmem, notcc, mixed, tables, cells: {
        "a0": dict(ms.X.new_acc(), **{"fact": 100, "full": f0}), "a1": dict(ms.X.new_acc(), **{"fact": 100, "full": f1}),
        "a2": dict(ms.new_acc2(), **{"fact": 100, "full": f2, "r_endmember_any": endmem, "tables_not_cc": notcc, "tables": tables, "c_table": cells, "r_name": 7, "r_end": 5, "r_member": 3}),
        "x": dict(ms.od((k, 0) for k in ms.XKEYS), **{"mixed_facts": mixed})}
    docs = [d(60, 80, 95, 11, 3, 2, 10, 1100), None, d(70, 85, 90, 7, 1, 4, 5, 900), d(50, 75, 85, 2, 2, 1, 3, 300)]
    j = list(ms.judged(docs).items())
    want_eq(out_, u"XA1-1", (j[0][1][u"数"], j[0][1][u"分母"], j[0][1][u"%"]), (240, 300, 80.0))
    want_eq(out_, u"XA1-2", (j[1][1][u"数"], j[1][1][u"分母"], j[1][1][u"%"]), (270, 300, 90.0))
    want_eq(out_, u"XA1-3", j[2][1][u"数"], 20)
    want_eq(out_, u"XA1-4 の最多(name 21・終わりの日 15・member の組 9)", j[3][1][u"いちばん多い理由"], [u"name の違い"])
    want_eq(out_, u"XA1-5", dict(j[4][1]), {u"書類": 2, u"分母": 3})
    want_eq(out_, u"XA1-6", (j[5][1][u"数"], j[5][1][u"分母"]), (2300, 2100))
    want_eq(out_, u"XA1-7", (j[6][1][u"数"], j[6][1][u"分母"]), (7, 300))
    want_eq(out_, u"XA1-8", (j[7][1][u"数"], j[7][1][u"分母"], j[7][1][u"%"]), (6, 18, 33.3))
    # 最多の理由が 2 つ並んだら両方書く
    docs2 = [dict(d(60, 80, 95, 0, 0, 0, 1, 0), a2=dict(ms.new_acc2(), **{"fact": 100, "full": 95, "tables": 1, "r_end": 9, "r_member": 9, "r_name": 2}))]
    want_eq(out_, u"最多が並ぶ", ms.judged(docs2)[u"XA1-4 段 2 の決まらなかった理由ごとの fact の数と、いちばん多い理由"][u"いちばん多い理由"], [u"終わりの日の違い", u"member の組の違い"])
    return out_


def record_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        docs, pp = pipeline(ms, [doc_b(), doc_broken(), doc_a(), doc_missing()], d, 4, 1)
        rec, secret = ms.build_record(docs, want=4, dev_count=1, prior_path=pp)
        keys = list(rec)
        if keys[:5] != [u"seal", u"封の commit", u"step", u"この script の sha256", u"材料"] or keys[5:8] != [u"書類", u"開発の 5 本", u"本番だけの 62 本"] or keys[-1] != u"限界":
            out_.append(u"記録の欄の並びが違う: %s" % keys)
        want_eq(out_, u"書類の数", len(rec[u"書類"]), 4)
        want_eq(out_, u"書類の断った理由", [r[u"断った理由"] for r in rec[u"書類"]], [u"", ms.X.R_TABLE, u"", ms.R_CTX_MISSING])
        want_eq(out_, u"script の sha256", rec[u"この script の sha256"], sha_of(SCRIPT_REL))
        want_eq(out_, u"材料", (rec[u"材料"][u"書類の本数"], rec[u"材料"][u"開発の 5 本の番号"], rec[u"材料"][u"script の決めの字"], rec[u"材料"][u"便 XA0 の記録の sha256"]),
                (4, [1], list(ms.RULES), hashlib.sha256(open(pp, "rb").read()).hexdigest()))
        jk = [k for k in rec if k.startswith(u"予測の判定に要る数")]
        if len(jk) != 1 or list(rec[jk[0]].values())[0][u"分母"] != 4:
            out_.append(u"判定に要る数が本番の塊(62 本)だけから作られていない")
        text = ms.dumps(rec)
        for t in (u"1,000", u"jppfs_cor", u"Rb0", u"Kb00", u".htm", u"E9999", u"S2FAKE", u"2025-03-31", u"2024-04-01", u"Mem0", u"SegAxis"):
            if t in text:
                out_.append(u"記録に禁止の字が在る: %s" % t)
        # secret(要素の局所名・文脈の名・member の名・docID・EDINET コード)
        if not {u"Rb0", u"Kb00", u"Mem1", u"SegAxis", u"Ra0"} <= set(secret[1]) or u"S2FAKE01" not in secret[2] or u"E99991" not in secret[3]:
            out_.append(u"secret に要素の名・文脈の名・member の名・docID・EDINET コードが入っていない")
        ms.verify_record(rec, text, 4, 1)
        # verify が壊れた記録を止める
        bad = []
        mutate_cases = (
            (u"書類の数(塊)", lambda r: r[u"開発の 5 本"].__setitem__(u"書類の数", 2)),
            (u"書類の fact の数", lambda r: r[u"書類"][0].__setitem__(u"fact の数", 22)), (u"塊の fact の数", lambda r: r[u"開発の 5 本"].__setitem__(u"fact の数", 22)),
            (u"段 2 の全部決まる(書類)", lambda r: r[u"書類"][0].__setitem__(u"段 2 の全部決まる fact の数", 8)), (u"段 0 の全部決まる(塊)", lambda r: r[u"開発の 5 本"][u"段 0"].__setitem__(u"全部決まる fact の数", 4)),
            (u"段 1 の全部決まる(塊)", lambda r: r[u"本番だけの 62 本"][u"段 1"].__setitem__(u"全部決まる fact の数", 3)),
            (u"書く欄の比の数", lambda r: r[u"開発の 5 本"][u"段 2"][u"書く欄の比"].__setitem__(u"数", 23)), (u"fact の数 × 7", lambda r: r[u"開発の 5 本"][u"段 1"].__setitem__(u"fact の数 × 7", 62)),
            (u"全部決まるが決まるを超える", lambda r: r[u"開発の 5 本"][u"段 1"].__setitem__(u"表の決めで決まる fact の数", 2)),
            (u"番号", lambda r: r[u"書類"][2].__setitem__(u"番号", 9)), (u"断った理由", lambda r: r[u"書類"][1].__setitem__(u"断った理由", u"")),
            (u"断った理由ごと", lambda r: r[u"本番だけの 62 本"].__setitem__(u"断った理由ごとの数", od())),
            (u"90% の書類(段 2)", lambda r: r[u"開発の 5 本"][u"段 2"].__setitem__(u"全部決まる fact が 90% 以上の書類の数", 0)),
            (u"8 通りの表の数", lambda r: r[u"開発の 5 本"][u"段 2"][u"8 通りのそれぞれを選んだ表の数"].__setitem__(u"BEE", 1)),
            (u"文脈の線・文脈の線を選ばなかった表", lambda r: r[u"開発の 5 本"][u"段 2"].__setitem__(u"文脈の線・文脈の線を選ばなかった表の数", 0)),
            (u"段 2 の項", lambda r: r[u"開発の 5 本"][u"段 2"][u"書く欄の数(項ごと)"].__setitem__(u"書式の類の数", 9)),
            (u"終わりの日か member の組の数", lambda r: r[u"開発の 5 本"][u"段 2"].__setitem__(u"終わりの日か member の組が線の決めと違う fact の数(どちらかが違えば 1)", 5)))
        for what, fn in mutate_cases:
            r2 = copy.deepcopy(rec)
            fn(r2)
            if not stops(ms, ms.verify_record, r2, None, 4, 1):
                bad.append(what)
        if bad:
            out_.append(u"verify_record が止めない: %s" % bad)
        if not stops(ms, ms.verify_record, rec, text, 67, 1):
            out_.append(u"書類が 67 本でないのに verify_record が止めない")
        # run → 記録 → check(置き場から数え直す)
        rp = os.path.join(d, "rec", "r.json")
        if not stops(ms, ms.run, docs=docs, out=rp, want=67, say=lambda *a: None, prior_path=pp) or os.path.exists(rp):
            out_.append(u"67 本でないのに run が止まらない(か記録を書いた)")
        lines = []
        rec2 = ms.run(docs=docs, out=rp, want=4, say=lambda *a: None, dev_count=1, prior_path=pp, progress=lines.append)
        if not os.path.exists(rp) or ms.dumps(rec2) != read_text(rp) or ms.dumps(rec2) != ms.dumps(rec) or len(lines) != 4:
            out_.append(u"記録が書かれていない・字が違う・進みを出さない")
        if not stops(ms, ms.run, docs=docs, out=rp, want=4, say=lambda *a: None, dev_count=1, prior_path=pp):
            out_.append(u"記録が既に在るのに run が止まらない")
        ms.check(docs=docs, rec_path=rp, want=4, say=lambda *a: None, dev_count=1, prior_path=pp)
        # 置き場が変われば check が止まる(数え直している)
        d2 = os.path.join(d, "docs2")
        os.makedirs(d2)
        make_docs(d2, [doc_b(), doc_broken(), doc_a(), doc_e()])
        prior2 = ms.X.build_record(d2, 4, 1)[0]
        pp2 = os.path.join(d, "prior2.json")
        with io.open(pp2, "w", encoding="utf-8") as fh:
            fh.write(ms.dumps(prior2))
        if not stops(ms, ms.check, docs=d2, rec_path=rp, want=4, say=lambda *a: None, dev_count=1, prior_path=pp2):
            out_.append(u"置き場が変わったのに check が止まらない")
        # 記録の字が書き換えられていれば止まる
        rp3 = os.path.join(d, "rec", "r3.json")
        with io.open(rp3, "w", encoding="utf-8") as fh:
            fh.write(read_text(rp).replace(u'"fact の数": 9,', u'"fact の数": 8,', 1))
        if not stops(ms, ms.check, docs=docs, rec_path=rp3, want=4, say=lambda *a: None, dev_count=1, prior_path=pp):
            out_.append(u"記録を書き換えたのに check が止まらない")
        if not stops(ms, ms.check, docs=docs, rec_path=os.path.join(d, "none.json"), want=4, say=lambda *a: None, prior_path=pp):
            out_.append(u"記録が無いのに check が止まらない")
    return out_


def stage0_problems_check(ms=None):
    u"""段 0 が便 XA0 の記録と全部の数で同じでなければ止まる。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        docs, pp = pipeline(ms, [doc_b(), doc_broken(), doc_a(), doc_missing()], d, 4, 1)
        ms.build_record(docs, want=4, dev_count=1, prior_path=pp)               # 同じなら通る
        prior = json.loads(read_text(pp), object_pairs_hook=od)

        def stops_with(change, label, dev=False):
            p2 = copy.deepcopy(prior)
            change(p2)
            path = os.path.join(d, "p_%d.json" % abs(hash(label)))
            with io.open(path, "w", encoding="utf-8") as fh:
                fh.write(ms.dumps(p2))
            if dev:
                return stops(ms, ms.dev_run, docs_dir=docs, say=lambda *a: None, count=1, prior_path=path)
            return stops(ms, ms.build_record, docs, 4, 1, path)
        cases = (
            (u"書類の fact の数", lambda p: p[u"書類"][0].__setitem__(u"fact の数", 10)), (u"断った書類の理由", lambda p: p[u"書類"][1].__setitem__(u"断った理由", u"x")),
            (u"開発の塊の全部決まる fact", lambda p: p[u"開発の 5 本"].__setitem__(u"全部決まる fact の数", 4)), (u"開発の塊の書く欄", lambda p: p[u"開発の 5 本"].__setitem__(u"書く欄の数", 1)),
            (u"本番の塊の書く欄の比", lambda p: p[u"本番だけの 62 本"][u"書く欄の比"].__setitem__(u"数", 1)), (u"本番の塊の向き", lambda p: p[u"本番だけの 62 本"].__setitem__(u"向き B を選んだ表の数", 5)),
            (u"本番の塊の理由", lambda p: p[u"本番だけの 62 本"][u"決まらなかった理由ごとの fact の数(重ねて数える)"].__setitem__(u"scale が線の決めと違う", 3)),
            (u"書類の行が足りない", lambda p: p[u"書類"].pop()))
        bad = [w for w, f in cases if not stops_with(f, w)]
        if bad:
            out_.append(u"段 0 が便 XA0 の記録と違うのに build_record が止まらない: %s" % bad)
        # 開発の入口は開発の塊と書類の行だけ照らす(本番の塊の食い違いでは止まらない)
        if not stops_with(cases[2][1], u"dev", True) or not stops_with(cases[0][1], u"dev2", True):
            out_.append(u"開発の入口が段 0 の食い違いで止まらない")
        if stops_with(cases[4][1], u"dev3", True):
            out_.append(u"開発の入口が本番の塊の食い違いで止まった(5 本だけ照らすはず)")
        if not stops(ms, ms.build_record, docs, 4, 1, os.path.join(d, "none.json")):
            out_.append(u"便 XA0 の記録が無いのに止まらない")
        # 関数そのもの: 同じなら空・違えば字
        rows0 = [ms.X.doc_row(1, None, u"x")]
        want_eq(out_, u"stage0_problems は空の入力の違いを見る", bool(ms.stage0_problems(rows0, [None], prior, 1, False)), True)
        # 実物の便 XA0 の記録の形(書類 67 本・塊 2 つ)
        real = ms.load_prior(os.path.join(ROOT, PRIOR_RECORD_REL))
        want_eq(out_, u"実物の便 XA0 の記録", (len(real[u"書類"]), u"開発の 5 本" in real, u"本番だけの 62 本" in real), (67, True, True))
    return out_


def clean_problems(ms=None):
    ms = ms or MS
    out_ = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"断った理由", u"固定の理由"), (u"fact の数", 5)])]), (u"hash", u"a" * 64)])
    secret = (set(), {u"NetSalesOfX", u"CurrentYearInstant", u"MemberY"}, [u"zzdoc"], {u"E99991"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out_.append(u"きれいな記録で止まる")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"company", 1)])), (u"禁止の欄(label)", od([(u"label", 1)])), (u"禁止の欄(element)", od([(u"element", 1)])),
        (u"禁止の欄(name)", od([(u"name", 1)])), (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])),
        (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])), (u"要素の名", od([(u"x", u"理由 NetSalesOfX")])),
        (u"文脈の名", od([(u"x", u"CurrentYearInstant")])), (u"member の名", od([(u"x", u"MemberY を含む")])), (u"日付の形", od([(u"x", u"終わりは 2025-03-31")])),
        (u"file の名(htm)", od([(u"x", u"0101010_honbun.htm")])), (u"file の名(xsd)", od([(u"x", u"jpcrp030000-asr-001.xsd")]))]
    for what, rec in cases:
        if not stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out_.append(u"%s が止まらない" % what)
        if not stops(ms, ms.record_text, rec, secret):
            out_.append(u"%s が record_text で止まらない" % what)
    if stops(ms, ms.check_clean, od([(u"x", u"2025 年 3 月・12345678・1-2-3")]), u"2025 年 3 月・12345678・1-2-3", secret):
        out_.append(u"日付でない字で止まる")
    with Temp() as d:
        p = os.path.join(d, "r.json")
        if not stops(ms, ms.write_record, p, od([(u"x", u"E12345")])) or os.path.exists(p):
            out_.append(u"禁止の字が在る記録を書いた(書く前の検査)")
        good = od([(u"x", 1)])
        ms.write_record(p, good)
        if not stops(ms, ms.write_record, p, good):
            out_.append(u"記録が既に在るのに書き直せる")
        orig = ms.write_exclusive
        q = os.path.join(d, "q.json")
        ms.write_exclusive = lambda path, data: orig(path, data + b" E12345")
        try:
            stopped = stops(ms, ms.write_record, q, good)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(q):
            out_.append(u"書いた後の検査が止めない(か file を消さない)")
    return out_


def devrun_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        docs, pp = pipeline(ms, [doc_b()] * 7, d, 7, 5)
        lines = []
        ch, ds = ms.dev_run(docs_dir=docs, say=lines.append, prior_path=pp)
        want_eq(out_, u"開発の入口は 5 本だけ", (ch[u"書類の数"], len(ds), sum(1 for x in lines if x.startswith(u"doc "))), (5, 5, 5))
        want_eq(out_, u"開発の入口の数", (ch[u"fact の数"], [ch[l][u"全部決まる fact の数"] for l in ms.STAGE_LABELS], [ch[l][u"書く欄の数"] for l in ms.STAGE_LABELS]), (45, [15, 15, 45], [295, 295, 110]))
        if not any(u"先に自分の欠陥を疑う場合に当たったもの" in x for x in lines):
            out_.append(u"欠陥を疑う場合の行を出さない")
        if not any(u"便 XA0 の記録" in x for x in lines):
            out_.append(u"段 0 の照らしの行を出さない")
        if os.path.exists(os.path.join(d, "docs", "sheet_context_2026-11-22.json")):
            out_.append(u"開発の入口が記録を書いた")
        want_eq(out_, u"dev_docs の本数", len(ms.dev_docs(docs, 2)), 2)
    return out_


def wall_equal_problems(ms=None):
    u"""この便の script が呼ぶ前の便の関数は、前の便の script の関数そのもの(写していない)。"""
    ms = ms or MS
    out_ = []
    for nm in ("mismatches", "count_facts", "mode_first", "lines_of", "line_keys", "doc_texts", "facts_of_files", "doc_row", "chunk_of", "docs_full", "reads_negative", "format_class", "strip_tags"):
        if not callable(getattr(ms.X, nm, None)):
            out_.append(u"便 XA0 の %s が無い" % nm)
    if ms.Stop is not ms.X.Stop or ms.Refuse is not ms.X.Refuse or ms.W is not ms.X.W:
        out_.append(u"Stop・Refuse・W が前の便と同じ object でない")
    return out_


# ======================================================================== 5. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "io", "json", "os", "re", "sys", "time")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "adapters", "core", "audit_core", "zipfile", "csv", "xml", "subprocess", "shutil", "tempfile")
#: 前の便の script の関数を呼ぶ(写さない): (module の名, 関数の名)
CALLED = (("X", "doc_texts"), ("X", "facts_of_files"), ("X", "count_facts"), ("X", "mismatches"), ("X", "lines_of"), ("X", "line_keys"), ("X", "mode_first"), ("X", "reads_negative"), ("X", "format_class"),
          ("X", "doc_row"), ("X", "chunk_of"), ("X", "dev_docs"), ("X", "check_clean"), ("X", "strip_tags"), ("X", "docs_full"), ("W", "select_docs"), ("W", "order_sha256"))
NOT_COPIED = ("select_docs", "order_sha256", "strip_text", "load_package", "is_public_htm", "mismatches", "count_facts", "mode_first", "lines_of", "line_keys", "doc_texts", "facts_of_files",
              "reads_negative", "format_class", "strip_tags", "docs_full", "colspan_of", "place_positions", "pct1", "sha256_file", "sha256_bytes", "facts_of_text", "table_tokens", "new_acc", "cells_of")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
#: 別の門の規準の字(関数の名・呼び出し・説明文のどこにも使わない)
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
OTHER_NAMES = (u"_xb0_inline_build_2026_11_21", u"_xt0_inline_build_2026_11_21", u"_xp0_taxonomy_build_2026_11_22", u"_xt0_taxonomy_build_2026_11_22", u"_xv0_tag_wall_2026_11_21", u"_xg1_tag_wall_2026_11_21",
               u"_xb0_tag_wall_2026_11_21", u"_xb0_tag_narrow", u"_xb0_edinet_validate_2026_11_21", u"_xa0_inline_build_2026_11_22")


def attr_names(tree):
    return [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]


def import_problems(src=None):
    u"""script の import は標準ライブラリだけ(engine・zipfile・csv・subprocess を読まない)。前の便の script は X・W から呼び写さない。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out_ = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"")]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "eval", "exec"):
            out_.append(u"動的な import・eval・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK_MODULES:
                out_.append(u"許さない module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out_.append(u"許す一覧に無い module: %s" % nm)
    attrs = attr_names(tree)
    if any(a in (("os", "environ"), ("os", "getenv"), ("os", "system"), ("os", "popen")) for a in attrs):
        out_.append(u"環境変数・shell を読んで/呼んでいる")
    for mod, fn in CALLED:
        if (mod, fn) not in attrs:
            out_.append(u"前の便の %s を %s から呼んでいない" % (fn, mod))
    funcs = set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in NOT_COPIED:
        if fn in funcs:
            out_.append(u"前の便の %s を script が自分で定義している(写している)" % fn)
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    if u"_xa1_sheet_wall_2026_11_22" not in consts:
        out_.append(u"便 XA0 の script を読む名が一意の名でない")
    if any(n in consts for n in OTHER_NAMES):
        out_.append(u"他の便と重なる名で読んでいる")
    for var, want in (("X", ("_load_sibling", None)), ("W", ("X", "W"))):
        ok = False
        for n in tree.body:
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var for t in n.targets):
                v = n.value
                if want[1] is None:
                    ok = isinstance(v, ast.Call) and getattr(v.func, "id", None) == want[0]
                else:
                    ok = isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name) and v.value.id == want[0] and v.attr == want[1]
        if not ok:
            out_.append(u"%s を前の便の script から受けていない(Stop の型・module の実体が 2 つになる)" % var)
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            if u".env" in n.value or u"dotenv" in n.value or u"API_KEY" in n.value:
                out_.append(u"鍵・.env の字が在る")
    for w in HARNESS_WORDS:
        bare = w.rstrip("(")
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and n.name == bare:
                out_.append(u"別の門の規準の字を関数の名に使っている: %s" % w)
            if isinstance(n, ast.Call):
                f = n.func
                nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else u"")
                if nm == bare:
                    out_.append(u"別の門の規準の字を呼んでいる: %s" % w)
        if w in src:
            out_.append(u"別の門の規準の字が script の字の中に在る(説明文も含む): %s" % w)
    return out_


def reserved_problems(rel=GATE_REL, base=ROOT):
    out_ = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(line.startswith(p) for p in RESERVED_PREFIXES):
            out_.append(u"%s:%d" % (rel, n))
    return out_


# ======================================================================== 変異
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**予測は「その検査が赤になる」。** この表は実行より先に書いた。
#: 検査の名前: seal・ctxread・form・combo・stats・refuse・suspicion・judged・chunk・record・stage0・clean・devrun・wall・wiring
MUTANTS = (
    # ---- 文脈の読み方
    (u"R1 id が xml:id も拾う", u'ID_RE = re.compile(r"""(?<![\\w:.\\-])id\\s*=', u'ID_RE = re.compile(r"""(?<![\\w.\\-])id\\s*=', ("ctxread",)),
    (u"R2 instant を見ない", u"    if inst is not None:\n        kind, s, e = KIND_INSTANT", u"    if False:\n        kind, s, e = KIND_INSTANT", ("ctxread", "form")),
    (u"R3 期間の始まりを捨てる", u"kind, s, e = KIND_DURATION, start or u\"\", end", u"kind, s, e = KIND_DURATION, u\"\", end", ("ctxread", "stats")),
    (u"R4 期間の無い文脈を時点に読む", u"        kind, s, e = KIND_NONE, u\"\", u\"\"", u"        kind, s, e = KIND_INSTANT, u\"\", u\"\"", ("ctxread", "stats")),
    (u"R5 member の組を並べない", u"tuple(sorted(members + typed))", u"tuple(members + typed)", ("ctxread",)),
    (u"R6 typedMember を member に入れない", u"tuple(sorted(members + typed))", u"tuple(sorted(members))", ("ctxread", "stats")),
    (u"R7 typedMember の印を付けない", u"bool(typed))", u"False)", ("ctxread", "stats")),
    (u"R8 typedMember の中身のタグを落とさない", u"typed = [(attr_value(DIM_RE, m.group(1)) or u\"\", X.strip_tags(m.group(2)).strip()) for m", u"typed = [(attr_value(DIM_RE, m.group(1)) or u\"\", m.group(2).strip()) for m", ("ctxread",)),
    (u"R9 explicitMember の中身の空白を落とさない", u"members.append((attr_value(DIM_RE, m.group(1)) or u\"\", X.strip_tags(m.group(2)).strip()))", u"members.append((attr_value(DIM_RE, m.group(1)) or u\"\", m.group(2)))", ("ctxread",)),
    (u"R10 日の字の前後の空白を落とさない", u"return X.strip_tags(m.group(1)).strip() if m else None", u"return X.strip_tags(m.group(1)) if m else None", ("ctxread",)),
    (u"R11 コメントの中も読む", u"    text = COMMENT_RE.sub(u\"\", text)\n", u"", ("ctxread",)),
    (u"R12 自己閉じの context も定義にする", u"        if m.group(1).rstrip().endswith(\"/\"):\n            continue\n", u"", ("ctxread",)),
    (u"R13 id の無い定義も数える", u"        if cid is not None:\n            out.append((cid, content))", u"        out.append((cid, content))", ("ctxread",)),
    (u"R14 同じ id で中身が違っても断らない", u"            if cid in defs and defs[cid] != content:", u"            if False:", ("ctxread", "refuse")),
    (u"R15 同じ id なら同じ中身でも断る", u"            if cid in defs and defs[cid] != content:", u"            if cid in defs:", ("ctxread", "refuse")),
    (u"R16 定義の無い contextRef を断らない", u"        if ref is None or ref not in defs:\n            raise Refuse(R_CTX_MISSING)\n        out.append(defs[ref])", u"        out.append(defs.get(ref, (KIND_NONE, u\"\", u\"\", (), False)))", ("ctxread", "refuse")),
    (u"R17 contextRef の属性が無い fact を通す", u"        if ref is None or ref not in defs:", u"        if ref is not None and ref not in defs:", ("ctxread",)),
    (u"R18 対の終わりの日に始まりの日を使う", u"    return (content[2], content[3])", u"    return (content[1], content[3])", ("ctxread", "form")),
    (u"R19 対から member の組を落とす", u"    return (content[2], content[3])", u"    return (content[2], ())", ("ctxread", "form")),
    (u"R20 対から終わりの日を落とす", u"    return (content[2], content[3])", u"    return (u\"\", content[3])", ("ctxread", "form")),
    (u"R21 終わりの日に始まりの日を返す", u"def end_of(content):\n    return content[2]", u"def end_of(content):\n    return content[1]", ("ctxread", "form")),
    (u"R22 member の組に空を返す", u"def members_of(content):\n    return content[3]", u"def members_of(content):\n    return ()", ("ctxread", "form")),
    (u"R23 context の閉じタグを探さず次の定義の頭までにする", u"        close = CTX_CLOSE_RE.search(text, m.end())\n        if not close:\n            continue\n", u"        close = CTX_OPEN_RE.search(text, m.end())\n        if not close:\n            continue\n", ("ctxread",)),
    (u"R24 context の名の後ろの区切りを見ない(contextual も context)", u'CTX_OPEN_RE = re.compile(r"<(?:%s:)?context(?=[\\s>/])([^>]*)>" % NAME)', u'CTX_OPEN_RE = re.compile(r"<(?:%s:)?context([^>]*)>" % NAME)', ("ctxread",)),
    (u"R25 member の dimension を見ない", u"members.append((attr_value(DIM_RE, m.group(1)) or u\"\", X", u"members.append((u\"\", X", ("ctxread",)),
    # ---- 段 1・段 2 の数え方
    (u"S1 段 1 が contextRef を対に置き換えない", u"    g[\"attrs\"][\"contextRef\"] = pair_of(c)", u"    pass", ("form", "chunk")),
    (u"S2 段 1 が元の fact の attrs を書き換える", u"        g[\"attrs\"] = dict(f[\"attrs\"])\n        g[\"attrs\"][\"contextRef\"]", u"        g[\"attrs\"] = f[\"attrs\"]\n        g[\"attrs\"][\"contextRef\"]", ("form",)),
    (u"S3 段 1 の対を終わりの日だけにする", u"    g[\"attrs\"][\"contextRef\"] = pair_of(c)", u"    g[\"attrs\"][\"contextRef\"] = end_of(c)", ("form",)),
    (u"S4 段 0 を段 1 の数で置き換える", u"return {\"a0\": a0, \"a1\": X.count_facts(pair_facts(facts, contents)),", u"return {\"a0\": X.count_facts(pair_facts(facts, contents)), \"a1\": X.count_facts(pair_facts(facts, contents)),", ("form", "chunk")),
    (u"T1 8 通りの並びを変える(同点の順)", u'COMBOS = tuple(o + e + m for o in ORIENTS for e in LINE_SRCS for m in LINE_SRCS)', u'COMBOS = tuple(o + e + m for o in ORIENTS for m in LINE_SRCS for e in LINE_SRCS)', ("seal",)),
    (u"T1b 8 通りを試す順を変える(member の組の線が外側)", u"        for es in LINE_SRCS:\n            for ms in LINE_SRCS:\n", u"        for ms in LINE_SRCS:\n            for es in LINE_SRCS:\n", ("combo",)),
    (u"T2 同点なら後を選ぶ", u"                if best is None or d > best[0]:", u"                if best is None or d >= best[0]:", ("combo", "form")),
    (u"T3 決まる fact が少ない方を選ぶ", u"                if best is None or d > best[0]:", u"                if best is None or d < best[0]:", ("combo", "form")),
    (u"T4 終わりの日の線の文脈と要素を取り違える", u'{"C": line_flags(cx_keys, ends), "E": line_flags(el_keys, ends)}', u'{"C": line_flags(el_keys, ends), "E": line_flags(cx_keys, ends)}', ("combo", "form")),
    (u"T5 member の組の線の文脈と要素を取り違える", u'"C": line_flags(cx_keys, mems), "E": line_flags(el_keys, mems)}', u'"C": line_flags(el_keys, mems), "E": line_flags(cx_keys, mems)}', ("combo", "form")),
    (u"T6 終わりの日と member の組の真偽を入れ替える", u"                flags = [(b[0], e, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", u"                flags = [(b[0], m, e, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", ("combo", "form")),
    (u"T7 終わりの日の線を見ない", u"                flags = [(b[0], e, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", u"                flags = [(b[0], False, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", ("combo", "form")),
    (u"T8 member の組の線を見ない", u"                flags = [(b[0], e, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", u"                flags = [(b[0], e, False, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", ("combo", "form")),
    (u"T9 name の線の決めを見ない", u"                flags = [(b[0], e, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", u"                flags = [(False, e, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", ("combo", "form")),
    (u"T10 unitRef の線の決めを見ない", u"                flags = [(b[0], e, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", u"                flags = [(b[0], e, m, False, b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", ("form",)),
    (u"T11 decimals の線の決めを見ない", u"                flags = [(b[0], e, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", u"                flags = [(b[0], e, m, b[2], False, b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", ("form",)),
    (u"T12 scale の線の決めを見ない", u"                flags = [(b[0], e, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]", u"                flags = [(b[0], e, m, b[2], b[3], False) for b, e, m in zip(base, ef[es], mf[ms])]", ("form",)),
    (u"T13 線の決めを最頻でなく最後の値にする", u"    mode = dict((k, X.mode_first(vs)) for k, vs in on_line.items())", u"    mode = dict((k, vs[-1]) for k, vs in on_line.items())", ("combo",)),
    (u"T14 線の決めを最初の値にする(最頻を見ない)", u"    mode = dict((k, X.mode_first(vs)) for k, vs in on_line.items())", u"    mode = dict((k, vs[0]) for k, vs in on_line.items())", ("combo",)),
    (u"T15 向き B を試さない", u"    for orient in ORIENTS:\n        base = X.mismatches(items, orient)", u"    for orient in ORIENTS[:1]:\n        base = X.mismatches(items, orient)", ("combo", "form")),
    (u"T16 向きの線の取り違え(向き B も行が要素)", u"        keys = [X.line_keys(f, orient) for f in items]", u"        keys = [X.line_keys(f, \"A\") for f in items]", ("combo", "form")),
    (u"T17 8 通りを選んだ表の数を数えない", u'        acc["k_" + combo] += 1', u"        pass", ("form", "chunk")),
    (u"T18 文脈の線・文脈の線を選ばなかった表の判定を C・E だけにする", u'        if (es, ms) != ("C", "C"):', u'        if ms != "C":', ("form",)),
    (u"T19 決まる fact を数えない", u'        acc["decided"] += d', u"        pass", ("form", "chunk")),
    (u"T20 表ごとの欄を 2 にする", u"CELL_PER_TABLE = 3 ", u"CELL_PER_TABLE = 2 ", ("seal", "form")),
    (u"T21 要素の線の欄を 3 にする", u"CELL_PER_ELEMENT_LINE = 4 ", u"CELL_PER_ELEMENT_LINE = 3 ", ("seal", "form")),
    (u"T22 終わりの日の線の欄を 2 にする", u"CELL_PER_END_LINE = 1", u"CELL_PER_END_LINE = 2", ("seal", "form")),
    (u"T23 member の組の線の欄を 2 にする", u"CELL_PER_MEMBER_LINE = 1", u"CELL_PER_MEMBER_LINE = 2", ("seal", "form")),
    (u"T24 終わりの日を決める側の線の数を常に文脈の線にする", u'        acc["c_end"] += (cx if es == "C" else el) * CELL_PER_END_LINE', u'        acc["c_end"] += cx * CELL_PER_END_LINE', ("form",)),
    (u"T25 member の組を決める側の線の数を常に要素の線にする", u'        acc["c_member"] += (cx if ms == "C" else el) * CELL_PER_MEMBER_LINE', u'        acc["c_member"] += el * CELL_PER_MEMBER_LINE', ("form",)),
    (u"T26 要素の線の数を文脈の線の数にする", u'        acc["c_elem"] += el * CELL_PER_ELEMENT_LINE', u'        acc["c_elem"] += cx * CELL_PER_ELEMENT_LINE', ("form",)),
    (u"T27 全部決まらない fact に 7 を掛けない", u'    acc["c_undecided"] = (acc["inside"] - acc["full"]) * CELLS_PER_FACT', u'    acc["c_undecided"] = (acc["inside"] - acc["full"])', ("form",)),
    (u"T28 表の外の fact に 7 を掛けない", u'    acc["c_outside"] = outside * CELLS_PER_FACT', u'    acc["c_outside"] = outside', ("form",)),
    (u"T29 空の fact の項を数えない", u'    acc["c_nil"] = nil', u'    acc["c_nil"] = 0', ("form",)),
    (u"T30 書式の類の数を数えない", u'    acc["c_formats"] = formats_in_doc', u'    acc["c_formats"] = 0', ("form", "chunk")),
    (u"T31 全部決まるが符号・書式を見ない", u"            if not any(fl) and sf[i]:", u"            if not any(fl):", ("form",)),
    (u"T32 全部決まるが決まる fact を見ない", u"            if not any(fl) and sf[i]:", u"            if sf[i]:", ("form",)),
    (u"T33 符号の規則から sign を外す", u'        has = f["attrs"].get("sign") == "-"\n        out.append(neg == has and', u'        has = neg\n        out.append(neg == has and', ("form",)),
    (u"T34 書式の規則を外す", u'f["attrs"].get("format") == modes[X.format_class(f["text"])])', u'True)', ("form",)),
    (u"T35 空の fact を符号・書式に通さない", u"        if f[\"nil\"]:\n            out.append(True)\n            continue", u"        if f[\"nil\"]:\n            out.append(False)\n            continue", ("form",)),
    (u"T36 終わりの日の理由を数えない", u"            for key, hit in zip(S2_REASON_KEYS, fl[:6]):", u"            for key, hit in zip(S2_REASON_KEYS, (fl[0], False, fl[2], fl[3], fl[4], fl[5])):", ("form",)),
    (u"T37 どちらかが違えば 1 を、両方違えば 2 にする", u"            if fl[1] or fl[2]:\n                acc[\"r_endmember_any\"] += 1", u"            if fl[1]:\n                acc[\"r_endmember_any\"] += 1\n            if fl[2]:\n                acc[\"r_endmember_any\"] += 1", ("form",)),
    (u"T38 書式の最頻を表の外の fact も含めず表の中だけで取る", u"    live = [f for f in facts if not f[\"nil\"]]\n    modes = {}\n    for k in X.FORMAT_CLASSES:", u"    live = [f for f in facts if not f[\"nil\"] and f[\"table\"] is not None]\n    modes = {}\n    for k in X.FORMAT_CLASSES:", ("form",)),
    # ---- 文脈の数え
    (u"X1 期間の種類が 2 つ在る name を時点と期間でなく 2 種類以上で数える", u"if KIND_INSTANT in ks and KIND_DURATION in ks)", u"if len(ks) >= 2)", ("stats",)),
    (u"X2 期間の種類が 2 つ在る name の fact でなく name の数を書く", u'    st["mixed_facts"] = sum(1 for f in facts if f["attrs"].get("name") in mixed)', u'    st["mixed_facts"] = len(mixed)', ("stats",)),
    (u"X3 始まりの日が違う束を 1 種類以上にする", u"diff = set(p for p, starts in groups.items() if len(starts) >= 2)", u"diff = set(p for p, starts in groups.items() if len(starts) >= 1)", ("stats",)),
    (u"X4 始まりの日が違う束に時点も入れる", u"        if content[0] == KIND_DURATION:\n            groups.setdefault(pair_of(content), set()).add(content[1])", u"        groups.setdefault(pair_of(content), set()).add(content[1])", ("stats",)),
    (u"X5 始まりの日が違う束を終わりの日だけで束ねる", u"            groups.setdefault(pair_of(content), set()).add(content[1])", u"            groups.setdefault(content[2], set()).add(content[1])", ("stats",)),
    (u"X6 始まりの日が違う文脈を指す fact でなく文脈の数を書く", u'    st["startdiff_facts"] = sum(1 for c in contents if c[0] == KIND_DURATION and pair_of(c) in diff)', u'    st["startdiff_facts"] = len(diff)', ("stats",)),
    (u"X7 文脈の定義の数を fact の数にする", u'    st["ctx_defs"] = len(defs)', u'    st["ctx_defs"] = len(facts)', ("stats",)),
    (u"X8 member を持つ文脈を指す fact の数を定義の数にする", u'    st["member_facts"] = sum(1 for c in contents if members_of(c))', u'    st["member_facts"] = sum(1 for c in defs.values() if members_of(c))', ("stats",)),
    (u"X9 typedMember の fact の数を member の fact にしない(印を見ない)", u'    st["typed_facts"] = sum(1 for c in contents if c[4])', u'    st["typed_facts"] = 0', ("stats",)),
    (u"X10 期間の種類が 2 つ在る name を fact でなく定義で見る", u"    for f, c in zip(facts, contents):\n        kinds.setdefault(f[\"attrs\"].get(\"name\"), set()).add(c[0])", u"    for f, c in zip(facts, contents):\n        kinds.setdefault(f[\"attrs\"].get(\"name\"), set()).add(KIND_INSTANT)", ("stats",)),
    # ---- 断り・読み
    (u"D1 断りの理由を捨てる", u"        return a0, u\"\", None, exc.reason, secret_strings(facts, {})", u"        return a0, u\"\", None, u\"\", secret_strings(facts, {})", ("refuse",)),
    (u"D2 便 XA0 の断りを別の理由にする", u"        return None, exc.reason, None, exc.reason, set()", u"        return None, exc.reason, None, R_CTX_MISSING, set()", ("refuse", "record")),
    (u"D3 便 XA0 の数を断った書類にも持たせない", u"        return a0, u\"\", None, exc.reason, secrets", u"        return None, u\"\", None, exc.reason, secrets", ("refuse",)),
    (u"D4 secret に要素の名を入れない", u"        out.add(local_of(f[\"attrs\"].get(\"name\") or u\"\"))", u"        pass", ("refuse", "record")),
    (u"D5 secret に文脈の名を入れない", u"        if re.search(r\"[A-Za-z]\", c):\n            out.add(c)", u"        pass", ("refuse", "record")),
    (u"D6 secret に member の名を入れない", u"            out.add(local_of(dim))\n            out.add(local_of(mem))", u"            pass", ("refuse", "record")),
    (u"D7 secret に docID を入れない", u"    return (set(), set(e for e in names if len(e) >= 3), [d[0] for d in docs], ecodes)", u"    return (set(), set(e for e in names if len(e) >= 3), [], ecodes)", ("record",)),
    (u"D8 secret に EDINET コードを入れない", u"            ecodes.update(re.findall(r\"E\\d{5}\", x))", u"            pass", ("record",)),
    # ---- 段 0 の照らし
    (u"Z1 段 0 の照らしをしない(build_record)", u"    require_stage0(rows0, accs0, prior, dev_count, True)\n    secret", u"    secret", ("stage0",)),
    (u"Z2 段 0 の照らしをしない(dev_run)", u"    require_stage0(rows0, accs0, prior, count, False)\n", u"", ("stage0",)),
    (u"Z3 照らしが違いを見ても止めない", u"    if bad:\n        raise Stop(", u"    if False:\n        raise Stop(", ("stage0",)),
    (u"Z4 書類の行を照らさない", u"        if i >= len(pr) or dumps(r) != dumps(pr[i]):", u"        if False:", ("stage0",)),
    (u"Z5 開発の塊を照らさない", u"    if dumps(X.chunk_of(rows0[:dev_count], accs0[:dev_count])) != dumps(prior.get(u\"開発の 5 本\")):", u"    if False:", ("stage0",)),
    (u"Z6 本番の塊を照らさない", u"    if whole and dumps(X.chunk_of(rows0[dev_count:], accs0[dev_count:])) != dumps(prior.get(u\"本番だけの 62 本\")):", u"    if False:", ("stage0",)),
    (u"Z7 本番の入口で本番の塊を照らさない(whole を偽にする)", u"    require_stage0(rows0, accs0, prior, dev_count, True)", u"    require_stage0(rows0, accs0, prior, dev_count, False)", ("stage0",)),
    (u"Z8 開発の入口が本番の塊まで照らす", u"    require_stage0(rows0, accs0, prior, count, False)", u"    require_stage0(rows0, accs0, prior, count, True)", ("stage0", "devrun")),
    (u"Z9 照らす書類を断った書類だけにする(この便の断りで便 XA0 の数を捨てる)", u"        rows0.append(X.doc_row(n, a0, r0))\n        accs0.append(a0)\n        rows.append(doc_row(n, d, reason))\n        ds.append(d)\n        if progress", u"        rows0.append(X.doc_row(n, d and a0, r0))\n        accs0.append(d and a0)\n        rows.append(doc_row(n, d, reason))\n        ds.append(d)\n        if progress", ("stage0", "record")),
    (u"Z10 便 XA0 の記録が無くても止めない", u"    if not os.path.isfile(path):\n        raise Stop(u\"**便 XA0 の記録が無い。止める**\")", u"    if not os.path.isfile(path):\n        return None", ("stage0",)),
    # ---- 塊・判定
    (u"E1 全部決まる書類の境を 90% より大きいにする", u"X.docs_full(a2s)", u"sum(1 for a in a2s if a[\"fact\"] > 0 and 100 * a[\"full\"] > 90 * a[\"fact\"])", ("judged",)),
    (u"E2 XA1-1 の分子を段 2 にする", u'(u"XA1-1 段 1 の全部決まる fact / fact", rate(t1["full"], t1["fact"])),', u'(u"XA1-1 段 1 の全部決まる fact / fact", rate(t2["full"], t1["fact"])),', ("judged",)),
    (u"E3 XA1-2 の分子を段 1 にする", u'(u"XA1-2 段 2 の全部決まる fact / fact", rate(t2["full"], t2["fact"])),', u'(u"XA1-2 段 2 の全部決まる fact / fact", rate(t1["full"], t2["fact"])),', ("judged",)),
    (u"E4 XA1-3 を終わりの日の理由だけにする", u'(u"XA1-3 段 2 で終わりの日か member の組が線の決めと違う fact の数", od([(u"数", t2["r_endmember_any"])])),', u'(u"XA1-3 段 2 で終わりの日か member の組が線の決めと違う fact の数", od([(u"数", t2["r_end"])])),', ("judged",)),
    (u"E5 XA1-4 の最多を 1 つだけにする", u"[k for k, v in reasons.items() if v == top]", u"[k for k, v in reasons.items() if v == top][:1]", ("judged",)),
    (u"E6 XA1-6 の分母を fact の数にする", u'rate(cells2(t2), t2["fact"] * CELLS_PER_FACT)', u'rate(cells2(t2), t2["fact"])', ("judged", "chunk")),
    (u"E7 XA1-7 の分子を期間の種類が 2 つ在る name の数にする", u'rate(tx["mixed_facts"], t0["fact"])', u'rate(tx["mixed_names"], t0["fact"])', ("judged",)),
    (u"E8 XA1-8 の分母を表の数でなく向き A の表にする", u'rate(t2["tables_not_cc"], t2["tables"])', u'rate(t2["tables_not_cc"], t2["k_ACC"] + t2["k_ACE"] + t2["k_AEC"] + t2["k_AEE"])', ("judged",)),
    (u"E9 欠陥を疑う条件(段 2 が 100%)を外す", u"    if f and s2 == f:", u"    if f and s2 > f:", ("suspicion",)),
    (u"E10 欠陥を疑う条件(段 2 が段 1 より少ない)の境を変える", u"    if s2 < s1:", u"    if s2 <= s1:", ("suspicion",)),
    (u"E11 欠陥を疑う条件(段 1 が段 0 より少ない)の境を変える", u"    if s1 < s0:", u"    if s1 <= s0:", ("suspicion",)),
    (u"E12 欠陥を疑う条件(断った 6 本)の境を変える", u"    if ch[u\"断った書類の数\"] >= SUSPECT_DECLINED:", u"    if ch[u\"断った書類の数\"] > SUSPECT_DECLINED:", ("suspicion",)),
    (u"E13 書類の行が段 2 でなく段 1 の全部決まる fact を書く", u"(u\"段 1 の全部決まる fact の数\", d[\"a1\"][\"full\"]), (u\"段 2 の全部決まる fact の数\", d[\"a2\"][\"full\"])", u"(u\"段 1 の全部決まる fact の数\", d[\"a1\"][\"full\"]), (u\"段 2 の全部決まる fact の数\", d[\"a1\"][\"full\"])", ("chunk", "record")),
    (u"E14 断った書類の理由を塊に数えない", u"            reasons[r[u\"断った理由\"]] = reasons.get(r[u\"断った理由\"], 0) + 1", u"            pass", ("chunk", "record")),
    (u"E15 断った書類も合計に足す", u"        if d is not None:\n            X.add_into(t0, d[\"a0\"])", u"        if True:\n            X.add_into(t0, d[\"a0\"])", ("chunk", "record")),
    (u"E16 段 2 の書く欄の比の分母を 6 にする", u"CELLS_PER_FACT = X.CELLS_PER_FACT", u"CELLS_PER_FACT = 6", ("seal", "chunk")),
    # ---- 記録
    (u"F1 塊の分け目を 1 つずらす", u"    prod_rows, prod_ds = rows[dev_count:], ds[dev_count:]", u"    prod_rows, prod_ds = rows[dev_count + 1:], ds[dev_count + 1:]", ("record",)),
    (u"F2 判定に要る数を 5 本の塊から作る", u"judged(prod_ds)", u"judged(dev_ds)", ("record",)),
    (u"F3 verify が塊の数を書類ごとの数と照らさない", u"            if ch[k] != v:\n                raise Stop(u\"**塊の数が書類ごとの数と合わない: %s。止める**\" % k)", u"            pass", ("record",)),
    (u"F4 verify が全部決まる fact を書類ごとの数と照らさない", u"            if ch[label][u\"全部決まる fact の数\"] != sum(r[rk] for r in kept):", u"            if False:", ("record",)),
    (u"F5 verify が書類 90% の数を見ない", u"            if ch[label][u\"全部決まる fact が %d%% 以上の書類の数\" % DOC_FULL_PCT] != sum(", u"            if False and ch[label][u\"全部決まる fact が %d%% 以上の書類の数\" % DOC_FULL_PCT] != sum(", ("record",)),
    (u"F6 verify が書く欄の比を見ない", u"            if blk[u\"fact の数 × 7\"] != CELLS_PER_FACT * ch[u\"fact の数\"] or blk[u\"書く欄の比\"][u\"数\"] != blk[u\"書く欄の数\"] or blk[u\"書く欄の比\"][u\"分母\"] != blk[u\"fact の数 × 7\"]:\n", u"            if False:\n", ("record",)),
    (u"F7 verify が 8 通りの表の数を見ない", u"        if sum(s2[u\"8 通りのそれぞれを選んだ表の数\"].values()) != s2[u\"fact の在る表の数\"] or s2[u\"文脈の線・文脈の線を選ばなかった表の数\"] != s2[u\"fact の在る表の数\"] - s2[u\"8 通りのそれぞれを選んだ表の数\"][u\"ACC\"] - s2[u\"8 通りのそれぞれを選んだ表の数\"][u\"BCC\"]:\n", u"        if False:\n", ("record",)),
    (u"F8 verify が段 2 の書く欄の項を見ない", u"        if list(s2[u\"8 通りのそれぞれを選んだ表の数\"]) != list(COMBOS) or sum(s2[u\"書く欄の数(項ごと)\"].values()) != s2[u\"書く欄の数\"]:", u"        if False:", ("record",)),
    (u"F9 verify が書類の形を見ない", u"        if r.get(u\"番号\") != i or list(r) != ROW_KEYS:", u"        if False:", ("record",)),
    (u"F10 verify が 67 本を見ない", u"    if not isinstance(rows, list) or len(rows) != want or rec[u\"材料\"][u\"書類の本数\"] != want:", u"    if not isinstance(rows, list):", ("record",)),
    (u"F11 check が置き場から数え直さない", u"    if dumps(now) != dumps(rec):", u"    if False:", ("record",)),
    (u"F12 write_record が既に在る記録を上書きできる", u"    if os.path.exists(path):\n        raise Stop(u\"**記録が既に在る: %s。止める**\" % os.path.basename(path))\n    text = record_text(rec, secret)", u"    text = record_text(rec, secret)", ("clean", "record")),
    (u"F13 run が進みを渡さない", u"rec, secret = build_record(docs, want, dev_count, prior_path, progress)", u"rec, secret = build_record(docs, want, dev_count, prior_path, None)", ("record",)),
    (u"F14 check_clean が何も止めない", u"    X.check_clean(rec, text, secret)\n", u"    pass\n", ("clean",)),
    (u"F15 check_clean が日付の形を見ない", u"    if DATE_FORM_RE.search(W.HEX_RE.sub(u\"\", text)):\n        raise Stop(u\"**記録に日付の形の字が在る。止める**\")", u"    pass", ("clean",)),
    (u"F16 日付の形を広げる(4 桁の数字)", u'DATE_FORM_RE = re.compile(r"(?<![0-9A-Za-z_])[0-9]{4}-[0-9]{2}-[0-9]{2}(?![0-9])")', u'DATE_FORM_RE = re.compile(r"(?<![0-9])[0-9]{4}(?![0-9])")', ("clean", "record")),
    (u"F17 開発の入口が 5 本より多く開く", u"    docs = dev_docs(docs_dir or DOCS_DIR, count)\n    rows0, accs0", u"    docs = dev_docs(docs_dir or DOCS_DIR, count + 2)\n    rows0, accs0", ("devrun",)),
    (u"F18 開発の入口が記録を書く", u"    ch = chunk_of(rows, ds)\n    say(u\"開発の 5 本の合計", u"    ch = chunk_of(rows, ds)\n    write_exclusive(os.path.join(docs_dir or DOCS_DIR, 'sheet_context_2026-11-22.json'), b'x')\n    say(u\"開発の 5 本の合計", ("devrun",)),
    (u"F19 開発の入口が欠陥を疑う行を出さない", u"    say(u\"先に自分の欠陥を疑う場合に当たったもの: %s\" % (u\"・\".join(suspicions(ch)) or u\"なし\"))", u"    pass", ("devrun",)),
    (u"F20 開発の入口が段 0 の照らしの行を出さない", u"    say(u\"段 0 は便 XA0 の記録(開発の 5 本)と全部の数で同じ\")", u"    pass", ("devrun",)),
    (u"F21 材料に便 XA0 の記録の sha256 を入れない", u"        (u\"便 XA0 の記録の sha256\", prior_sha), (u\"script の決めの字\", list(RULES))])", u"        (u\"便 XA0 の記録の sha256\", u\"\"), (u\"script の決めの字\", list(RULES))])", ("record",)),
    (u"F22 secret を作る名の集めを捨てる", u"        names |= strs\n", u"", ("record",)),
    # ---- 封の字・配線
    (u"G1 予測の境の数を変える", u'("XA1-1", (82, 92))', u'("XA1-1", (81, 92))', ("seal",)),
    (u"G2 予測の境の数を変える(XA1-3)", u'("XA1-3", (None, 3500))', u'("XA1-3", (None, 3600))', ("seal",)),
    (u"G3 上限を含まない予測の名を変える", u'BOUNDS_UPPER_EXCLUSIVE = ("XA1-1", "XA1-6")', u'BOUNDS_UPPER_EXCLUSIVE = ("XA1-1",)', ("seal",)),
    (u"G4 封の commit の字を変える", u'SEAL_COMMIT = "d46f92aa"', u'SEAL_COMMIT = "d46f92ab"', ("seal",)),
    (u"G5 限界の字を落とす", u'    u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]', u'    u"「XBRL を作れる」は、この便からは言えない。"]', ("seal",)),
    (u"G6 記録の path を変える", u'RECORD_REL = "fixtures/xbrl/cd8/sheet_context_2026-11-22.json"', u'RECORD_REL = "fixtures/xbrl/cd8/sheet_context_2026-11-23.json"', ("seal",)),
    (u"G7 便 XA0 の記録の path を変える", u'PRIOR_RECORD_REL = "fixtures/xbrl/cd8/sheet_wall_2026-11-22.json"', u'PRIOR_RECORD_REL = "fixtures/xbrl/cd8/sheet_wall_2026-11-23.json"', ("seal",)),
    (u"G8 書類 90% を変える", u"DOC_FULL_PCT = 90", u"DOC_FULL_PCT = 80", ("seal", "chunk")),
    (u"G9 開発の本数を変える", u"DEV_COUNT = 5", u"DEV_COUNT = 6", ("seal",)),
    (u"G10 書類の本数を変える(W の字を自分で持つ)", u"DOCS_WANT = W.DOCS_WANT", u"DOCS_WANT = 66", ("seal",)),
    (u"G11 欠陥を疑う条件の数を変える", u"SUSPECT_DECLINED = 6", u"SUSPECT_DECLINED = 7", ("seal", "suspicion")),
    (u"G12 向きの種類を足す", u'ORIENTS = ("A", "B")', u'ORIENTS = ("A", "B", "C")', ("seal",)),
    (u"G13 段の名を変える", u'STAGE_LABELS = (u"段 0", u"段 1", u"段 2")', u'STAGE_LABELS = (u"段 0", u"段 1", u"段 3")', ("seal",)),
    (u"W1 別の門の規準の字を関数の名にする", u"def attr_value(rx, attr_text):", u"def mutate(x):\n    return x\n\n\ndef attr_value(rx, attr_text):", ("wiring",)),
    (u"W2 別の門の規準の字を説明文に書く", u"# 文脈の定義(封 §1)\n", u"# 文脈の定義(封 §1)(注入)\n", ("wiring",)),
    (u"W3 便 XA0 の script を他の便と重なる名で読む", u'PRIOR_NAME = "_xa1_sheet_wall_2026_11_22"', u'PRIOR_NAME = "_xb0_tag_narrow"', ("wiring",)),
    (u"W4 前の便の関数を写す", u"def attr_value(rx, attr_text):", u"def mode_first(values):\n    return values\n\n\ndef attr_value(rx, attr_text):", ("wiring",)),
    (u"W5 zipfile を import する", u"import time\n", u"import time\nimport zipfile\n", ("wiring",)),
    (u"W6 subprocess を import する", u"import time\n", u"import time\nimport subprocess\n", ("wiring",)),
    (u"W7 engine を import する", u"import time\n", u"import time\nfrom adapters.xbrl import instance\n", ("wiring",)),
    (u"W8 Stop を便 XG0 から別に読む", u"W = X.W ", u'W = _load_sibling("_xa1_other_wall", "xbrl_tag_wall_2026-11-21.py")  # ', ("wiring",)),
    (u"W9 前の便の doc_texts を写す", u"def attr_value(rx, attr_text):", u"def doc_texts(zip_path):\n    return []\n\n\ndef attr_value(rx, attr_text):", ("wiring",)),
    (u"W10 便 XA0 の mismatches を呼ばない", u"        base = X.mismatches(items, orient)", u"        base = mismatches(items, orient)", ("wiring",)),
)
#: 黙ることが分かっている変異(理由つき)。予測は「黙る」ではなく、実行して黙った事実と理由を実行の後に書く(実行前は空)
SILENT_BY_DESIGN = {}


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"ctxread": ctxread_problems, u"form": form_problems, u"combo": combo_problems, u"stats": stats_problems, u"refuse": refuse_problems,
             u"suspicion": suspicion_problems, u"judged": judged_problems, u"chunk": chunk_problems, u"record": record_problems, u"stage0": stage0_problems_check, u"clean": clean_problems,
             u"devrun": devrun_problems, u"wall": wall_equal_problems}
    if name in table:
        return table[name](mod)
    if name == u"wiring":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"ctxread", u"form", u"combo", u"stats", u"refuse", u"suspicion", u"judged", u"chunk", u"record", u"stage0", u"clean", u"devrun", u"wall", u"wiring")


def run_mutants(table=MUTANTS, only=None):
    base = read(SCRIPT_REL)
    out_ = []
    for name, old, new, checks in table:
        if only is not None and name not in only:
            continue
        assert base.count(old) == 1, (name, base.count(old))
        src = base.replace(old, new)
        try:
            mod = load_source(src)
        except BaseException as exc:                # noqa: BLE001
            out_.append((name, [(c, True) for c in checks], u"読めない: %s" % type(exc).__name__))
            continue
        res = [(c, bool(guard(check_by_name, c, mod, src))) for c in checks]
        out_.append((name, res, u""))
    return out_


# ======================================================================== 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        for old, new in ((u"| XA1-2(主) | 段 2 の全部決まる fact は、fact の 90% 以上。", u"| XA1-2(主) | 段 2 の全部決まる fact は、fact の 91% 以上。"),
                         (u"同じなら、この順で先のもの: 向き A が先・終わりの日は文脈の線が先・member の組は文脈の線が先", u"同じなら、この順で先のもの: 向き A が先・終わりの日は要素の線が先・member の組は文脈の線が先"),
                         (u"× 4 + 終わりの日を決める側の fact の在る線の数 × 1", u"× 3 + 終わりの日を決める側の fact の在る線の数 × 1"), (u"表の外の fact の数 × 7", u"表の外の fact の数 × 8"),
                         (u"3(向き・終わりの日を決める線・member の組を決める線)", u"2(向き・終わりの日を決める線・member の組を決める線)"),
                         (u"| XA1-5 | 段 2 で、全部決まる fact が 90% 以上の書類は 31 本以上。", u"| XA1-5 | 段 2 で、全部決まる fact が 90% 以上の書類は 32 本以上。"),
                         (u"| XA1-1 | 段 1 の全部決まる fact は、fact の 82% 以上 92% 未満。", u"| XA1-1 | 段 1 の全部決まる fact は、fact の 82% 以上 93% 未満。")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"sheet_context", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        pr = load_order_helpers()
        r = pr.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        others = ["measure/s.py", "tests/g.py"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], pr.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertNotEqual([], pr.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("tests/new.py")
        self.assertNotEqual([], pr.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["tests/new.py"]))

    def test_d_3_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)

    def test_d_4_the_record_when_tracked_is_committed_after_the_script_and_the_gate(self):
        if not record_tracked():
            self.skipTest(u"記録は本番の走りの後に書かれ、commit される。commit された後で順を見る")
        self.assertEqual([], order_of(others=list(ORDER_FILES) + [RECORD_REL]))


class ReadTest(unittest.TestCase):
    def test_b_1_the_context_reading_is_decided_by_the_seal(self):
        self.assertEqual([], ctxread_problems())

    def test_b_2_refusals_and_the_secret_strings(self):
        self.assertEqual([], refuse_problems())


class CountTest(unittest.TestCase):
    def test_c_1_the_nine_forms_by_hand(self):
        self.assertEqual([], form_problems())

    def test_c_2_the_eight_combinations_and_the_tie_order(self):
        self.assertEqual([], combo_problems())

    def test_c_3_kinds_of_period_and_start_dates(self):
        self.assertEqual([], stats_problems())

    def test_c_4_suspicion_conditions(self):
        self.assertEqual([], suspicion_problems())

    def test_c_5_judging_numbers(self):
        self.assertEqual([], judged_problems())

    def test_c_6_chunks_from_a_fake_place(self):
        self.assertEqual([], chunk_problems())

    def test_c_7_the_s2_keys_are_the_hand_counted_keys(self):
        self.assertEqual(list(MS.S2_KEYS), list(numbers(MS, doc_b())["a2"]))
        self.assertEqual(list(MS.XKEYS), list(numbers(MS, doc_b())["x"]))


class Stage0Test(unittest.TestCase):
    def test_s_1_stage_zero_must_equal_the_prior_record_or_the_run_stops(self):
        self.assertEqual([], stage0_problems_check())

    def test_s_2_the_stage_zero_functions_are_the_prior_scripts(self):
        self.assertEqual([], wall_equal_problems())


class RecordTest(unittest.TestCase):
    def test_e_1_the_record_path_from_a_fake_place(self):
        self.assertEqual([], record_problems())

    def test_e_2_forbidden_things_stop_the_record(self):
        self.assertEqual([], clean_problems())

    def test_e_3_the_dev_entry_opens_only_the_first_five(self):
        self.assertEqual([], devrun_problems())

    def test_e_4_the_real_record_when_present_is_clean_and_consistent(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く")
        text = read(RECORD_REL)
        MS.verify_record(json.loads(text, object_pairs_hook=od), text)


class WiringTest(unittest.TestCase):
    def test_f_1_imports_and_the_earlier_functions_are_called_not_copied(self):
        self.assertEqual([], import_problems())

    def test_f_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for extra in (u"\nimport socket\n", u"\nimport zipfile\n", u"\nimport csv\n", u"\nimport subprocess\n", u"\nfrom adapters.xbrl import instance\n", u"\nX2 = os.system('a')\n",
                      u"\ndef select_docs(a, b):\n    return None\n", u"\ndef mismatches(a, b):\n    return None\n", u"\ndef run_doc(a):\n    return None\n", u"\ndef doc_texts(a):\n    return None\n"):
            self.assertNotEqual([], import_problems(base + extra), extra)
        self.assertNotEqual([], import_problems(base.replace(u"X.count_facts(", u"count_facts(")))
        self.assertNotEqual([], import_problems(base.replace(u"X.mismatches(", u"mismatches(")))
        self.assertNotEqual([], import_problems(base.replace(u"W.select_docs(", u"select_docs(")))

    def test_f_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_f_4_the_script_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_sheet_context_script_for_sysmodules_check")
        changed = [k for k in before if sys.modules.get(k) is not before[k]]
        self.assertEqual([], changed)
        self.assertEqual(mod.X.__name__, u"_xa1_sheet_wall_2026_11_22")
        self.assertIs(mod.W, mod.X.W)
        self.assertIs(mod.Stop, mod.X.B.V.Stop)
        del mod

    def test_f_5_the_default_place_is_outside_the_repo_and_the_gate_never_opens_it(self):
        top = os.path.realpath(REPO)
        self.assertFalse(os.path.realpath(MS.DOCS_DIR).startswith(top + os.sep))
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record|dev_docs|dev_run)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"docs|rec_path|\bd\b|prior_path", m.group(2)), m.group(0))

    def test_f_6_the_gate_calls_subprocess_only_for_git(self):
        src = read(GATE_REL)
        calls = re.findall(r"subprocess\.(\w+)", src)
        self.assertEqual(set(calls), {"run", "PIPE"})
        for m in re.finditer(r"subprocess\.run\(([^)]*)\)", src):
            self.assertTrue(m.group(1).startswith(u'["git"'), m.group(1))


class MutantTest(unittest.TestCase):
    def test_g_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL))
        modules_before = dict(sys.modules)
        results = run_mutants()
        self.assertEqual(before, (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL)))
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red and n not in SILENT_BY_DESIGN]
        self.assertEqual([], silent)
        self.assertEqual(set(SILENT_BY_DESIGN), set(n for n, res, _w in results if any(not red for _c, red in res)))
        self.assertEqual(len(MUTANTS), len(results))
        self.assertGreaterEqual(len(MUTANTS), 100)
        self.assertEqual(len(set(m[0] for m in MUTANTS)), len(MUTANTS))

    def test_g_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)

    def test_g_3_the_mutant_module_is_the_one_the_checks_look_at(self):
        u"""変異を入れた module の関数だけが検査の対象(実物の module を見て黙る型を防ぐ)。1 つの変異で、変異した module では赤・実物の module では緑。"""
        base = read(SCRIPT_REL)
        old, new = u"    return (content[2], content[3])", u"    return (u\"\", content[3])"
        mod = load_source(base.replace(old, new))
        self.assertNotEqual([], check_by_name(u"form", mod, base))
        self.assertEqual([], check_by_name(u"form", MS, base))
        self.assertIsNot(mod.pair_of, MS.pair_of)


if __name__ == "__main__":
    unittest.main()
