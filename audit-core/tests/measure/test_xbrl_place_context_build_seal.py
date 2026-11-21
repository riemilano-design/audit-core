# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PLACE_CONTEXT_BUILD_SEAL_2026-11-22.md(XH0 ― 数の置き場を表の cell の字から決め、文脈と単位の定義を紙から作って包みを組むと、道具が読む fact は元と同じになるか)の封の門。

**この門は置き場を読まない**(書類の置き場 ``~/.cache/audit-core/edinet/`` は 1 度も開かない)。通信しない。道具(Arelle)は呼ばない(偽の ``runner`` を渡す)。subprocess を呼ぶのは git だけ
(紙 2 を作る・置き場を作る・文脈と単位を作る・属性を作る・組む命令の別の process は、同じ引数で呼ぶ同じ process の中の ``proc`` に替えて通す。別の process の呼び方そのものは引数の形を字で縛る)。
作り物の書類(手で書いた htm と最小のタクソノミの zip)で、規則を 1 つずつ本物の関数のまま通す。

**この門が縛るもの**

1. 封の字: 封の commit(97eff9a2)・封の file が commit した blob と同じ・封の決め(紙の欄の式・混ぜ物の字・予測の境・限界の字・置き場と文脈の規則の字)が script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 置き場の規則を 1 つずつ(作り物の書類): 数の並びが 1 つ・2 つ・0・``※`` の直後・文字参照の中の数字・横棒だけ・span の前に置く(重なる)・cell の中の表・例外の cell・1 つずつ書く fact の在る cell・
   空の fact の 2 つの形(最頻・並んだら自己閉じ)。文脈の規則: ``id`` の作り方・member の字の 2 つの形・連結個別の軸が先・``id`` の分け方が 2 通り・期の名が決まらない・単位・混ぜ物の 2 つ。
4. 紙 2 の値を 1 つ変えると出力が変わる。紙の欄の数は紙の file を読み戻して数えた値。
5. **置き場を作る命令・文脈と単位を作る命令に渡す folder に元の行が無い**(数の fact の行・文脈と単位の行)。2 つの命令は元の包み・元の ``.htm``・元の fact を読む関数を呼ばない(字で縛る)。
6. 書類 1 本の通し・断りの段と理由・塊・判定に要る数・欠陥を疑う条件・記録の形と合計と禁止のもの(記録がまだ無い間は作り物の記録で見る。在るときは本物の記録も見る)。
7. 封 → script → 記録の commit の順(script・門のどちらかが未 commit なら赤)。
8. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

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
    mod = types.ModuleType("xbrl_place_context_build_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_PLACE_CONTEXT_BUILD_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "97eff9a2"
SCRIPT_REL = "measure/xbrl_place_context_build_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_place_context_build_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/place_context_build_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_place_context_build_script_for_seal_gate")
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
    u"""``Refuse``(紙・置き場・文脈の断り)が上がれば断った理由の字・上がらなければ None。"""
    try:
        fn(*a, **kw)
    except (ms.Refuse, ms.P.Refuse) as exc:
        return exc.reason
    return None


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xh0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def load_order_helpers():
    p = os.path.join(ROOT, "tests", "measure", "test_xbrl_p28_result.py")
    if not os.path.exists(p):
        return None
    return load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_place_context_build_seal")


def want_eq(out_, label, got, want):
    if got != want:
        out_.append(u"%s: 得 %r 正 %r" % (label, got, want))


# ======================================================================== 作り物の書類(手で書いた字)
AXIS = u"jppfs_cor:SegAxis"
CNC = u"jppfs_cor:ConsolidatedOrNonConsolidatedAxis"
XSD = b'<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" targetNamespace="http://example.com/x"/>'
LB = b'<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase"/>'
IA, IB, IM = u"CurrentYearInstant", u"Prior1YearInstant", u"CurrentYearInstant_Mem1"
MEM1 = [(AXIS, u"jppfs_cor:Mem1")]
JPY_UNIT = u'<xbrli:unit id="JPY"><xbrli:measure>iso4217:JPY</xbrli:measure></xbrli:unit>'
USD_UNIT = u'<xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>'


def fx(name=u"jppfs_cor:E0", ctx=IA, unit=u"JPY", dec=u"0", text=u"1,000", nil=False, pair=False, fmt=u"ixt:numdotdecimal"):
    a = u'name="%s" contextRef="%s"' % (name, ctx)
    if unit is not None:
        a += u' unitRef="%s"' % unit
    if nil:
        if pair:
            return u'<ix:nonFraction %s xsi:nil="true"></ix:nonFraction>' % a
        return u'<ix:nonFraction %s xsi:nil="true" />' % a
    if dec is not None:
        a += u' decimals="%s"' % dec
    if fmt is not None:
        a += u' format="%s"' % fmt
    return u"<ix:nonFraction %s>%s</ix:nonFraction>" % (a, text)


def tbl(rows):
    return u"<table>" + u"".join(u"<tr>" + u"".join(u"<td>%s</td>" % c for c in r) + u"</tr>" for r in rows) + u"</table>"


def cdef(cid, end=u"2025-03-31", start=None, mem=(), forever=False, ident=u"E0", scheme=u"http://x"):
    per = u"<xbrli:forever/>" if forever else u"<xbrli:instant>%s</xbrli:instant>" % end if start is None else u"<xbrli:startDate>%s</xbrli:startDate><xbrli:endDate>%s</xbrli:endDate>" % (start, end)
    scen = u"<xbrli:scenario>%s</xbrli:scenario>" % u"".join(u'<xbrldi:explicitMember dimension="%s">%s</xbrldi:explicitMember>' % (d, m) for d, m in mem) if mem else u""
    return (u'<xbrli:context id="%s"><xbrli:entity><xbrli:identifier scheme="%s">%s</xbrli:identifier></xbrli:entity><xbrli:period>%s</xbrli:period>%s</xbrli:context>' % (cid, scheme, ident, per, scen))


ROLE_REF = u'<link:roleRef roleURI="http://x/role" xlink:type="simple" xlink:href="http://x/r.xsd#r" />'
PS_UNIT = (u'<xbrli:unit id="JPYPerShares"><xbrli:divide><xbrli:unitNumerator><xbrli:measure>iso4217:JPY</xbrli:measure></xbrli:unitNumerator>'
           u'<xbrli:unitDenominator><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unitDenominator></xbrli:divide></xbrli:unit>')


def header(defs, units=(JPY_UNIT,), hidden=u"", refs=(ROLE_REF,)):
    hid = u"<ix:hidden>%s</ix:hidden>" % hidden if hidden else u""
    return u"<ix:header>%s<ix:resources>%s%s%s</ix:resources></ix:header>" % (hid, u"".join(refs), u"".join(defs), u"".join(units))


def cpage(body, defs, units=(JPY_UNIT,), hidden=u"", refs=(ROLE_REF,)):
    return u"<html><body>%s\n%s\n</body></html>\n" % (header(defs, units, hidden, refs), body)


def sent(name, body, ctx=IA):
    return u'<ix:nonNumeric name="jppfs_cor:%s" contextRef="%s">%s</ix:nonNumeric>' % (name, ctx, body)


DEFS3 = [cdef(IA), cdef(IB, end=u"2024-03-31"), cdef(IM, mem=MEM1)]


def doc_r1():
    u"""2 行 × 3 列。行ごとに要素・列ごとに文脈(IA 時点 2025・IB 時点 2024・IM 時点 2025 と member)。全部規則で当たる。"""
    rows = [[fx(name=u"jppfs_cor:E%d" % r, ctx=c, dec=u"-3" if r == 0 else u"0") for c in (IA, IB, IM)] for r in range(2)]
    return cpage(tbl(rows), DEFS3)


def case_rows():
    u"""置き場の規則の 1 つずつ。各行 = [試す cell(列 0), 列 1 の fact]。(行の名前, 中身)の並び。"""
    cases = [
        (u"A 数の並びが 1 つ", fx(name=u"jppfs_cor:E0", text=u"1,000")),
        (u"B 数の並びが 2 つ(fact 無し)", u"1,000 2,000"),
        (u"C 数の並びが 2 つ(fact 在り)", fx(name=u"jppfs_cor:E2", text=u"1,000") + u" 2,000"),
        (u"D ※の直後(fact 無し)", u"※1,000"),
        (u"E ※の直後(fact 在り)", u"※" + fx(name=u"jppfs_cor:E4", text=u"1,000")),
        (u"F 文字参照の直後の数(fact 在り)", u"&#160;" + fx(name=u"jppfs_cor:E5", text=u"1,000")),
        (u"G 文字参照の中の数字(fact 無し)", u"&#1000;"),
        (u"H 横棒だけ(fact 無し)", u"－"),
        (u"I 横棒だけ(空の fact 在り)", fx(name=u"jppfs_cor:E8", nil=True) + u"－"),
        (u"J span の前(空の fact 在り)", fx(name=u"jppfs_cor:E9", nil=True) + u"<span>－</span>"),
        (u"K span の重なる前(空の fact 在り)", fx(name=u"jppfs_cor:E10", nil=True) + u"<span><span>－</span></span>"),
        (u"L cell の中の表(fact 無し)", u"<table><tr><td>1,000</td></tr></table>"),
        (u"M 数も横棒も無い", u"abc"),
        (u"N 空の cell", u""),
        (u"O 1 つずつ書く fact の在る cell", u""),
    ]
    return cases


def doc_cells():
    u"""16 行 × 2 列。列 0 に試す cell・列 1 に fact(行 14 と 15 の列 1 だけ 1 つずつ書く fact: name が行の決めと違う。行 15 は cell に数の並びが 2 つ)。"""
    rows = []
    for r, (_label, content) in enumerate(case_rows()):
        if r == 14:
            rows.append([u"", fx(name=u"jppfs_cor:Odd", ctx=IB, text=u"1,000")])
        else:
            rows.append([content, fx(name=u"jppfs_cor:E%d" % r, ctx=IB)])
    # 行 14 の列 0 にも 1 つ fact を置いて、行の name の決めを E14 にする
    rows[14][0] = fx(name=u"jppfs_cor:E14", ctx=IA)
    # 行 15: 列 1 は 1 つずつ書く fact(name が行の決めと違う)で、cell に数の並びが 2 つ(規則では当たらない)
    rows.append([fx(name=u"jppfs_cor:E15", ctx=IA), fx(name=u"jppfs_cor:Odd", ctx=IB, text=u"1,000") + u" 2,000"])
    return cpage(tbl(rows), [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_pair():
    u"""1 行 2 列。空の fact は開きと閉じの組(最頻 = 組)。"""
    return cpage(tbl([[fx(nil=True, pair=True) + u"－", fx(ctx=IB)]]), [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_tie():
    u"""2 行 2 列。空の fact は自己閉じ 1 つ・組 1 つ(並んだら自己閉じ)。組の方が例外の cell になる。"""
    return cpage(tbl([[fx(name=u"jppfs_cor:E0", nil=True) + u"－", fx(name=u"jppfs_cor:E0", ctx=IB)], [fx(name=u"jppfs_cor:E1", nil=True, pair=True) + u"－", fx(name=u"jppfs_cor:E1", ctx=IB)]]),
                 [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_ids():
    u"""id の作り方: 連結・個別の軸が先(軸の字の順では後)・member の字の 2 つの形(_cor で終わる接頭辞・そうでない接頭辞)。"""
    mem_cnc = [(u"jppfs_cor:AAxis", u"jppfs_cor:MemA"), (CNC, u"jppfs_cor:NonConsolidatedMember")]
    mem_other = [(u"jpcrp_cor:BAxis", u"jpcrp030000-asr_E0-000:KMember")]
    defs = [cdef(IA), cdef(IA + u"_NonConsolidatedMember_MemA", mem=mem_cnc), cdef(IA + u"_jpcrp030000-asr_E0-000KMember", mem=mem_other)]
    row = [fx(ctx=c) for c in (IA, IA + u"_NonConsolidatedMember_MemA", IA + u"_jpcrp030000-asr_E0-000KMember")]
    return cpage(tbl([row]), defs)


def doc_ambiguous():
    u"""id の分け方が 2 通り: A_B = 期の名 A_B(member 無し)・期の名 A + member の字 B。"""
    defs = [cdef(u"A_B"), cdef(u"A", end=u"2024-03-31"), cdef(u"Z_B", end=u"2023-03-31", mem=[(AXIS, u"p_cor:B")])]
    return cpage(tbl([[fx(ctx=c) for c in (u"A_B", u"A", u"Z_B")]]), defs)


def doc_period_twice():
    u"""同じ (期間の種類, 終わりの日) の期の名が 2 つ(member の組が違うので 1 つずつ書く fact にならない)。"""
    defs = [cdef(IM, mem=MEM1), cdef(u"Alt"), cdef(IB, end=u"2024-03-31")]
    return cpage(tbl([[fx(ctx=c) for c in (IM, u"Alt", IB)]]), defs)


def doc_units():
    u"""単位が 3 つ(JPY・USD・割り算の単位)。"""
    return cpage(tbl([[fx(ctx=IA), fx(ctx=IB, unit=u"USD")]]), [cdef(IA), cdef(IB, end=u"2024-03-31")], units=(JPY_UNIT, USD_UNIT, PS_UNIT))


def doc_duration():
    u"""期間の文脈(期の名 Duration・開始日と終了日)。"""
    return cpage(tbl([[fx(ctx=u"CurrentYearDuration"), fx(ctx=u"Prior1YearDuration")]]), [cdef(u"CurrentYearDuration", start=u"2024-04-01"), cdef(u"Prior1YearDuration", start=u"2023-04-01", end=u"2024-03-31")])


def doc_single_period():
    u"""期の名ごとに fact が 1 つずつ(混ぜ物(期)を作れない)。"""
    return cpage(tbl([[fx(name=u"jppfs_cor:E0", ctx=IA)], [fx(name=u"jppfs_cor:E1", ctx=IB)]]), [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_outside():
    u"""表の外の fact(1 つずつ書く fact・数の並びは 1 つ)。"""
    return cpage(tbl([[fx(ctx=IA), fx(ctx=IB)]]) + u"<p>" + fx(name=u"jppfs_cor:Ex", ctx=IA) + u"</p>", [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_sentence():
    u"""文の fact(nonNumeric)が数の fact を囲む。数の fact の parent は文の fact の行。"""
    inner = u"<ix:nonNumeric name=\"jppfs_cor:Txt\" contextRef=\"%s\">本文 %s</ix:nonNumeric>" % (IA, tbl([[fx(ctx=IA), fx(ctx=IB)]]))
    return cpage(inner, [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_acc():
    u"""ACC の表(終わりの日・member の組を列で決める)。3 行 × 3 列。行 2 と列 2 には fact が無く、数の字だけ在る(決めが無い cell)。"""
    rows = [[fx(name=u"jppfs_cor:E0", ctx=IA), fx(name=u"jppfs_cor:E0", ctx=IB), u"5,000"], [fx(name=u"jppfs_cor:E1", ctx=IA), fx(name=u"jppfs_cor:E1", ctx=IB), u"5,000"], [u"5,000", u"5,000", u"5,000"]]
    return cpage(tbl(rows), [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_ace():
    u"""ACE の表(終わりの日は列・member の組は行で決める)。列 2 には fact が無い。"""
    ibm = u"Prior1YearInstant_Mem1"
    rows = [[fx(name=u"jppfs_cor:E0", ctx=IA), fx(name=u"jppfs_cor:E0", ctx=IB), u"5,000"], [fx(name=u"jppfs_cor:E1", ctx=IM), fx(name=u"jppfs_cor:E1", ctx=ibm), u"5,000"]]
    return cpage(tbl(rows), [cdef(IA), cdef(IB, end=u"2024-03-31"), cdef(IM, mem=MEM1), cdef(ibm, end=u"2024-03-31", mem=MEM1)])


def doc_aec():
    u"""AEC の表(終わりの日は行・member の組は列で決める)。列 2 には fact が無い。"""
    ibm = u"Prior1YearInstant_Mem1"
    rows = [[fx(name=u"jppfs_cor:E0", ctx=IA), fx(name=u"jppfs_cor:E0", ctx=IM), u"5,000"], [fx(name=u"jppfs_cor:E1", ctx=IB), fx(name=u"jppfs_cor:E1", ctx=ibm), u"5,000"]]
    return cpage(tbl(rows), [cdef(IA), cdef(IB, end=u"2024-03-31"), cdef(IM, mem=MEM1), cdef(ibm, end=u"2024-03-31", mem=MEM1)])


def doc_b():
    u"""向き B の表(要素は列・文脈は行)。3 行 × 3 列。列 2 には fact が無い。"""
    rows = [[fx(name=u"jppfs_cor:E0", ctx=c), fx(name=u"jppfs_cor:E1", ctx=c), u"5,000"] for c in (IA, IB, IM)]
    return cpage(tbl(rows), [cdef(IA), cdef(IB, end=u"2024-03-31"), cdef(IM, mem=MEM1)])


def doc_nested():
    u"""文の fact が入れ子・閉じた文の fact の後ろの表・数の fact が文の fact の頭に在る(start が同じ)。"""
    tie = sent(u"T3", fx(name=u"jppfs_cor:Ex", ctx=IA) + u" 円")
    body = (sent(u"T0", u"前文") + tbl([[fx(name=u"jppfs_cor:E0", ctx=IA), fx(name=u"jppfs_cor:E0", ctx=IB)]])
            + sent(u"T1", sent(u"T2", u"内 " + tbl([[fx(name=u"jppfs_cor:E1", ctx=IA), fx(name=u"jppfs_cor:E1", ctx=IB)]]))) + tie)
    return cpage(body, [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_late_header():
    u"""頭の部(ix:header)が本文の後ろに在る。持ち込みの before は 1(文の fact)・組んだ後の before は 3。"""
    defs = [cdef(IA), cdef(IB, end=u"2024-03-31")]
    return u"<html><body>%s%s%s</body></html>\n" % (sent(u"T0", u"前文"), tbl([[fx(ctx=IA), fx(ctx=IB)]]), header(defs))


def doc_special_refs():
    u"""使う fact が 1 つだけの文脈: 文の fact(ウ)・表の外の fact(イ)・見えない fact(ウ)。"""
    hidden = u'<ix:nonNumeric name="jpcrp_cor:Hid" contextRef="FilingDateInstant">x</ix:nonNumeric>'
    body = tbl([[fx(ctx=IA), fx(ctx=IB)]]) + sent(u"T9", u"注記", ctx=u"Prior3YearInstant") + u"<p>" + fx(name=u"jppfs_cor:Ex", ctx=u"Prior4YearInstant") + u"</p>"
    defs = [cdef(IA), cdef(IB, end=u"2024-03-31"), cdef(u"Prior3YearInstant", end=u"2022-03-31"), cdef(u"Prior4YearInstant", end=u"2021-03-31"), cdef(u"FilingDateInstant", end=u"2026-06-30")]
    return cpage(body, defs, hidden=hidden)


def doc_orphans():
    u"""使われない定義が 3 つ: 期の名に分けられる 1 つ・member の字で終わらない id(Weird_X)・id が member の字そのもの(_Mem1)。"""
    body = tbl([[fx(name=u"jppfs_cor:E%d" % r, ctx=c) for c in (IA, IB)] for r in range(2)])
    defs = [cdef(IA), cdef(IB, end=u"2024-03-31"), cdef(u"Prior2YearInstant", end=u"2023-03-31"), cdef(u"Weird_X", end=u"2022-03-31", mem=MEM1), cdef(u"_Mem1", end=u"2021-03-31", mem=MEM1)]
    return cpage(body, defs)


def doc_second_header():
    u"""頭の部が在る 1 つ目の .htm(文脈の定義を持つ)。"""
    return cpage(tbl([[fx(ctx=IA), fx(ctx=IB)]]), [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_second_header_file():
    u"""2 つ目の .htm にも頭の部が在る(resources は空)。文脈は 1 つ目の頭の部に入る。"""
    return u"<html><body>%s\n%s\n</body></html>\n" % (header([], units=(), refs=()), tbl([[fx(name=u"jppfs_cor:Z0", ctx=IA), fx(name=u"jppfs_cor:Z0", ctx=IB)]]))


def doc_member_orders():
    u"""member の並び: 4 つ(連結・個別の軸が最後に書かれ、id では先)・2 つ(書いた順が id の順の逆)。"""
    mem4 = [(u"jppfs_cor:AAxis", u"jppfs_cor:MemA"), (u"jppfs_cor:BAxis", u"jppfs_cor:MemB"), (u"jppfs_cor:CAxis", u"jppfs_cor:MemC"), (CNC, u"jppfs_cor:NonConsolidatedMember")]
    mem2 = [(u"jppfs_cor:YAxis", u"jppfs_cor:MemY"), (u"jppfs_cor:XAxis", u"jppfs_cor:MemX")]
    id4, id2 = IA + u"_NonConsolidatedMember_MemA_MemB_MemC", IB + u"_MemX_MemY"
    defs = [cdef(IA), cdef(id4, mem=mem4), cdef(IB, end=u"2024-03-31"), cdef(id2, end=u"2024-03-31", mem=mem2)]
    return cpage(tbl([[fx(ctx=c) for c in (IA, id4, IB, id2)]]), defs)


def doc_two_axes():
    u"""同じ member が 2 つの軸の下に在る(member の表は 1 つの軸しか持てない)。"""
    return cpage(tbl([[fx(ctx=IM), fx(ctx=u"Prior1YearInstant_Mem1")]]), [cdef(IM, mem=MEM1), cdef(u"Prior1YearInstant_Mem1", end=u"2024-03-31", mem=[(u"jppfs_cor:OtherAxis", u"jppfs_cor:Mem1")])])


def doc_epoch():
    u"""期の日付が混ぜ物の日付と同じ(日付を替えても変わらない)。"""
    return cpage(tbl([[fx(ctx=IA), fx(ctx=IA)]]), [cdef(IA, end=u"1900-01-01")])


def doc_hand_nil():
    u"""空の fact: 表の中の自己閉じが 1 つ(最頻)・表の外の 1 つずつ書く fact の空が組で 2 つ(最頻に入れない)。"""
    body = tbl([[fx(name=u"jppfs_cor:E0", nil=True) + u"－", fx(name=u"jppfs_cor:E0", ctx=IB)]]) + u"<p>" + fx(name=u"jppfs_cor:Ex", nil=True, pair=True) + fx(name=u"jppfs_cor:Ey", nil=True, pair=True) + u"</p>"
    return cpage(body, [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_noname():
    u"""要素の線の name の決めが「無い」(行 0 の fact に name が無い)。その行の数の字だけの cell には fact を付けない。"""
    nameless = u'<ix:nonFraction contextRef="%s" unitRef="JPY" decimals="0" format="ixt:numdotdecimal">1,000</ix:nonFraction>' % IA
    rows = [[nameless, u"5,000"], [fx(name=u"jppfs_cor:E1", ctx=IA), fx(name=u"jppfs_cor:E1", ctx=IB)]]
    return cpage(tbl(rows), [cdef(IA), cdef(IB, end=u"2024-03-31")])


def doc_missing():
    return cpage(tbl([[fx(ctx=IA), fx(ctx=u"Kz9")]]), [cdef(IA)])


def doc_broken():
    return u"<html><body><table><tr><td>%s</td></table></body></html>" % fx(ctx=IA)


def write_pack(path, html, tag=u"1", extra=()):
    u"""作り物の包み 1 つ(PublicDoc に xsd・linkbase 5 つ・htm 1 つ・マニフェスト・画像)。"""
    base = u"XBRL/PublicDoc/jpcrp030000-asr-001_E9999%s-000_2026-03-31_01_2026-06-30" % tag
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(base + u".xsd", XSD)
        for s in (u"_cal", u"_def", u"_lab", u"_lab-en", u"_pre"):
            z.writestr(base + s + u".xml", LB)
        z.writestr(u"XBRL/PublicDoc/0100000_a_E9999%s-000_ixbrl.htm" % tag, html.encode("utf-8"))
        for n, h in extra:
            z.writestr(u"XBRL/PublicDoc/%s" % n, h.encode("utf-8"))
        z.writestr(u"XBRL/PublicDoc/manifest_PublicDoc.xml", b"<manifest/>")
        z.writestr(u"XBRL/PublicDoc/logo.png", b"PNG")


def make_docs(d, htmls):
    u"""作り物の置き場。書類ごとに包み 1 つ。ほかに有報でない zip を 1 つ。"""
    for i, h in enumerate(htmls, 1):
        write_pack(os.path.join(d, "S2FAKE%02d.zip" % i), h, u"%d" % i)
    with zipfile.ZipFile(os.path.join(d, "S2OTHER1.zip"), "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


def alter_first_attr(ms, out):
    u"""出す folder の最初の nonFraction の name を別の字にする(比べ方 1 が違いを数えることを見る)。"""
    idx = ms.P.jload(ms.P.read_bytes(os.path.join(out, ms.P.INDEX_FILE)))
    p = os.path.join(out, idx["htm"][0]["tables"])
    tab = ms.P.jload(ms.P.read_bytes(p))
    for e in tab["F"]:
        if e["kind"] == "nonFraction":
            e["attrs"]["name"] = u"jppfs_cor:Altered"
            break
    ms.P.write_bytes(p, ms.P.jdump(tab))


def alter_first_context(ms, out, mode=True):
    u"""出す folder の最初の文脈の定義の scheme(``mode`` が ``unit`` なら最初の単位の測度)を別の字にする(比べ方 2 が違いを数えることを見る)。"""
    idx = ms.P.jload(ms.P.read_bytes(os.path.join(out, ms.P.INDEX_FILE)))
    for item in idx["htm"]:
        p = os.path.join(out, item["tables"])
        tab = ms.P.jload(ms.P.read_bytes(p))
        if tab["H"] is not None:
            for r in tab["H"]["resources"]:
                if mode == "unit" and r.get("type") == "unit":
                    r["measures"] = [u"iso4217:XXX"]
                    ms.P.write_bytes(p, ms.P.jdump(tab))
                    return
                if mode is True and r.get("type") == "context":
                    r["scheme"] = u"http://altered"
                    ms.P.write_bytes(p, ms.P.jdump(tab))
                    return


def alter_place_folder(ms, out, mode):
    u"""置いた folder の表 F を替える(比べ方 1 が違いを数えることを見る)。number = 最初の数の fact の parent・carried = 最初の持ち込みの行の end・attrs = 最初の数の fact に attrs を足す。"""
    idx = ms.P.jload(ms.P.read_bytes(os.path.join(out, ms.P.INDEX_FILE)))
    p = os.path.join(out, idx["htm"][0]["tables"])
    tab = ms.P.jload(ms.P.read_bytes(p))
    for e in tab["F"]:
        if mode == "carried" and e["kind"] != "nonFraction":
            e["end"] += 1
            break
        if mode == "number" and e["kind"] == "nonFraction":
            e["parent"] = 99
            break
        if mode == "attrs" and e["kind"] == "nonFraction":
            e["attrs"] = {"name": u"jppfs_cor:Planted"}
            break
    ms.P.write_bytes(p, ms.P.jdump(tab))


def inproc(ms, log=None, fail=None, alter_attrs=False, alter_ctx=False, alter_place=None, drop_build_file=False, second_build_differs=False):
    u"""別の process の呼び出し(``[python, -I, script, 命令, folder, folder]``)を、同じ process の中の同じ入口に替える。``fail`` = {命令の名: 偽の返り値}。"""
    builds = []
    fail = fail or {}

    def proc(cmd, cwd, timeout):
        assert cmd[1] == "-I" and len(cmd) == 6, cmd
        name = cmd[3]
        if log is not None:
            log.append(name)
        if name in fail:
            return fail[name]
        buf = io.StringIO()
        old = sys.stderr
        sys.stderr = buf
        try:
            if name == "place":
                rc = ms.place_main(cmd[4:])
                if rc == 0 and alter_place:
                    alter_place_folder(ms, cmd[5], alter_place)
            elif name == "context":
                rc = ms.context_main(cmd[4:])
                if rc == 0 and alter_ctx:
                    alter_first_context(ms, cmd[5], alter_ctx)
            elif name == "attrs":
                rc = ms.S.attrs_main(cmd[4:])
                if rc == 0 and alter_attrs:
                    alter_first_attr(ms, cmd[5])
            else:
                rc = ms.P.build_main(cmd[4:])
                builds.append(cmd[5])
                if rc == 0 and drop_build_file:
                    os.remove(os.path.join(cmd[5], sorted(os.listdir(cmd[5]))[0]))
                if rc == 0 and second_build_differs and len(builds) == 2:
                    with open(os.path.join(cmd[5], sorted(os.listdir(cmd[5]))[0]), "ab") as fh:
                        fh.write(b" ")
        finally:
            sys.stderr = old
        return rc, buf.getvalue(), False
    return proc


def make_runner(mode=u"same", seen=None):
    u"""偽の道具。包みの sha256 を ``seen`` に足し、道具が書く CSV(fact と書き出し 7 つ)を ``mode`` どおりに書く: same・tax_differs・facts_differs。"""
    flags = ("--facts", "--concepts", "--pre", "--cal", "--dim", "--roleTypes", "--viewFile")

    def runner(cmd, timeout):
        z = cmd[cmd.index("-f") + 1]
        with open(z, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        if seen is not None:
            seen.append(sha)
        for fl in flags:
            if fl in cmd:
                body = u"Name\nx%s\n" % (sha if mode == "facts_differs" else u"") if fl == "--facts" else u"h\nrow%s\n" % (sha if mode == "tax_differs" else u"")
                with io.open(cmd[cmd.index(fl) + 1], "w", encoding="utf-8") as fh:
                    fh.write(body)
        return u"", False
    return runner


FAKE_TOOL_INFO = od([(u"版", u"2.47.5"), (u"ModelValue.py の sha256", u"a" * 64), (u"package の一覧の sha256", u"b" * 64), (u"Python の版", u"3.11")])
fake_runner = make_runner()


def run_one(ms, html, d, tag=u"1", mode=u"same", seen=None, extra=(), **proc_kw):
    u"""作り物の書類 1 本を ``measure_one`` に通す(道具は偽の runner)。(rec, 呼んだ命令の並び)。"""
    z = os.path.join(d, "p%s.zip" % tag)
    write_pack(z, html, tag, extra)
    log = []
    tmp = os.path.join(d, "tmp")
    rec = ms.measure_one(u"tool", z, tmp if os.path.isdir(tmp) else None, make_runner(mode, seen), inproc(ms, log, **proc_kw))
    return rec, log


def pipeline(ms, html, d, tag=u"1", extra=()):
    u"""紙 2 を作る → 置き場を作る → 文脈と単位を作る → 属性を作る(同じ process の入口)。dict(p2, st, files, placed, ctx, new, folder, ...)。断りは例外のまま上げる。"""
    z = os.path.join(d, "q%s.zip" % tag)
    write_pack(z, html, tag, extra)
    folder = os.path.join(d, "paper%s" % tag)
    sheet, info, files, p2, st = ms.make_paper_folder(ms.B.load_package(z), z, folder)
    placed = os.path.join(d, "placed%s" % tag)
    ms.write_place_folder(folder, placed)
    ctx = os.path.join(d, "ctx%s" % tag)
    ms.write_context_folder(placed, ctx)
    out = os.path.join(d, "attrs%s" % tag)
    ms.S.write_attrs_folder(ctx, out)
    pf = ms.P.load_htm_tables(placed, ms.P.jload(ms.P.read_bytes(os.path.join(placed, ms.P.INDEX_FILE))))
    cf = ms.P.load_htm_tables(ctx, ms.P.jload(ms.P.read_bytes(os.path.join(ctx, ms.P.INDEX_FILE))))
    nf = ms.P.load_htm_tables(out, ms.P.jload(ms.P.read_bytes(os.path.join(out, ms.P.INDEX_FILE))))
    diff, by = ms.S.compare_attrs(files, nf)
    return dict(sheet=sheet, info=info, files=files, p2=p2, st=st, folder=folder, placed=pf, placed_dir=placed, ctx=cf, ctx_dir=ctx, new=nf, diff=diff, by=dict(by),
                same_numbers=ms.number_rows(files) == ms.number_rows(pf), same_rows=ms.all_rows(files) == ms.all_rows(pf), defs=ms.compare_definitions(files, cf))


def nf_attrs(files):
    return [dict(e["attrs"]) for _n, _p, F, _h in files for e in F if e["kind"] == "nonFraction"]


def resources_of(files):
    return [r for _n, _p, _F, H in files if H is not None for r in H["resources"]]


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XH0-1", (97, None)), ("XH0-2", (None, 3)), ("XH0-3", (55, None)), ("XH0-4", (None, 5)), ("XH0-5", (55, None)), ("XH0-6", (55, None)), ("XH0-7", (None, 5)),
                    ("XH0-8", (u"作れた数", None)), ("XH0-9", (40, 44)), ("XH0-10", (None, 0))])
SEAL_BOUND_TEXT = od([("XH0-1", u"置き場の規則が当てたものは 97% 以上"), ("XH0-2", u"3% 以下"), ("XH0-3", u"文脈が同じ書類は 55 本以上"), ("XH0-4", u"断った書類は 5 本以下"),
                      ("XH0-5", u"元と同じ書類は 55 本以上"), ("XH0-6", u"鳴り方が同じ書類は 55 本以上"), ("XH0-7", u"1 つ以上在る書類は 5 本以下"), ("XH0-8", u"作れた書類の全部で効く"),
                      ("XH0-9", u"40% 以上 44% 未満"), ("XH0-10", u"0 本")])
SEAL_RULE_PHRASES = (
    u"並びのすぐ前(タグは飛ばす。空白と文字参照は飛ばさない)の字が `※` なら、数の並びに数えない。",
    u"cell の中に表が在れば、fact を付けない。",
    u"数の並びがちょうど 1 つなら、その並びに中身の在る fact を付ける",
    u"全部が便 XA0 の横棒の字(`DASH_CHARS`)なら、空の fact を付ける。置く所は最初の横棒の字の前。ただし、そのすぐ前が `span` の開きタグなら、その開きタグの前(重なっていれば繰り返す)。",
    u"接頭辞が `_cor` で終わるなら local name、そうでなければ接頭辞 + local name。連結・個別の軸(local name が `ConsolidatedOrNonConsolidatedAxis`)の member が先",
    u"分け方がちょうど 1 通りでなければ、その書類は「断った」",
    u"期の表で(期間の種類、終わりの日)がその組の期の名(ちょうど 1 つでなければ、その書類は「断った」)",
    u"1 つずつ書く fact の在る cell と例外の cell は紙 2 のとおりにし、規則を当てない",
    u"書類の、1 つずつ書く fact でない空の fact の最頻。並んだら自己閉じ",
    u"1900-01-01",
    u"紙 2 の欄 = 空の fact の形 1 + 1 つずつ書く fact × 2(始まりと終わり)+ 例外の cell × 1 + 例外の cell の中の fact × 2 + 識別子 1 + scheme 1 + 期の表の期の名ごとに(1 + 日付の数)+ member の表の member × 2 + 単位の表の単位 × 2",
    u"**紙の欄の比** = 紙の欄の数 ÷(fact の数 × 7)",
    u"`fixtures/xbrl/cd8/place_context_build_2026-11-22.json`")
SEAL_LIMIT_PHRASES = (u"答えから作っている", u"持ち込み", u"「XBRL を作れる」「専用の道具が要らない」", u"置き場は、字の番号(`start`・`end`)で比べている", u"member の並びと定義の並びは見ていない",
                      u"混ぜ物は 1 本につき 2 つだけ")
LIMIT_PHRASES = (u"紙も紙 2 も答え(元の書類)から作っている", u"持ち込み(", u"「XBRL を作れる」「専用の道具が要らない」", u"置き場は字の番号(start・end)で比べている", u"member の並びと定義の並びは見ていない",
                 u"混ぜ物は 1 本につき 2 つだけ")


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out_ = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out_.append(u"script の封の commit・path・記録の path が門と違う")
    if RECORD_REL not in seal:
        out_.append(u"封に記録の path が無い")
    if (ms.CELLS_NIL_FORM, ms.CELLS_PER_HAND_PLACE, ms.CELLS_PER_EXC_CELL, ms.CELLS_PER_EXC_FACT, ms.CELLS_IDENT, ms.CELLS_SCHEME, ms.CELLS_PER_MEMBER, ms.CELLS_PER_UNIT) != (1, 2, 1, 2, 1, 1, 2, 2):
        out_.append(u"紙 2 の欄の式の数が封と違う")
    if ms.MIX_DATE != "1900-01-01" or ms.CNC_AXIS != "ConsolidatedOrNonConsolidatedAxis" or ms.COR_SUFFIX != "_cor":
        out_.append(u"混ぜ物の日付・連結個別の軸の字・_cor の字が封と違う")
    if ms.DOCS_WANT != 67 or ms.DEV_COUNT != 5 or ms.SUSPECT_DECLINED != 10:
        out_.append(u"67 本・開発の 5 本・欠陥を疑う条件の数が封と違う")
    if tuple(ms.STAGES) != (u"紙を作る", u"置き場を作る", u"文脈と単位を作る", u"属性を作る", u"組む"):
        out_.append(u"断りの段が封と違う")
    if ms.TOOL_VERSION != ms.S.TOOL_VERSION or ms.SHA_P != ms.S.SHA_P or ms.YEAR != ms.S.YEAR or ms.TIMEOUT_SEC != ms.S.TIMEOUT_SEC or ms.NIL_ATTR != "xsi:nil":
        out_.append(u"道具の版・sha256・規則の年・時間の上限が便 XS0 と違う")
    for p in SEAL_RULE_PHRASES:
        if p not in seal:
            out_.append(u"封に字が無い: %s" % p[:30])
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS) or tuple(ms.BOUNDS_UPPER_EXCLUSIVE) != ("XH0-9",):
        out_.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [x for x in seal.splitlines() if x.startswith(u"| %s(" % k) or x.startswith(u"| %s " % k)]
        if len(row_) != 1 or t not in row_[0]:
            out_.append(u"封の予測の行の字が違う: %s" % k)
    for p in SEAL_LIMIT_PHRASES:
        if p not in seal:
            out_.append(u"封に限界の字が無い: %s" % p)
    for p in LIMIT_PHRASES:
        if p not in u"".join(ms.LIMITS):
            out_.append(u"限界の字が script に無い: %s" % p)
    if u"docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・member の名・日付・表の字・紙の中身" not in seal:
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


# ======================================================================== 2. 規則を 1 つずつ(作り物の書類)
def raw_pred(ms, raw, nil_self=True):
    return ms.predict_cell(raw, nil_self)


def rules_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    # ---- 置き場の規則(cell の中身の字 → 答え。位置は中身の中の番号)
    want_eq(out_, u"数の並び 1 つ", raw_pred(ms, u"a 1,000 b"), [(2, 7, False)])
    want_eq(out_, u"数の並び 1 つ(全角)", raw_pred(ms, u"１，２３４"), [(0, 5, False)])
    want_eq(out_, u"数の並び 2 つ", raw_pred(ms, u"1,000 2,000"), [])
    want_eq(out_, u"数の並び 0", raw_pred(ms, u"abc"), [])
    want_eq(out_, u"数の並び 3 つ", raw_pred(ms, u"1 2 3"), [])
    want_eq(out_, u"数字を含まない並び(, と . だけ)", raw_pred(ms, u"..,"), [])
    want_eq(out_, u"※の直後", raw_pred(ms, u"※1,000"), [])
    want_eq(out_, u"※の直後(タグを飛ばす)", raw_pred(ms, u"※<span>1,000</span>"), [])
    want_eq(out_, u"※の後に空白が在れば数", raw_pred(ms, u"※ 1,000"), [(2, 7, False)])
    want_eq(out_, u"※の後に文字参照が在れば数", raw_pred(ms, u"※&#160;1,000"), [(7, 12, False)])
    want_eq(out_, u"文字参照の中の数字は数でない", raw_pred(ms, u"&#1000;"), [])
    want_eq(out_, u"文字参照の中の数字は数でない(後ろの数は在る)", raw_pred(ms, u"&#1000;5"), [(7, 8, False)])
    want_eq(out_, u"タグの中の数字は数でない", raw_pred(ms, u'<td width="100">7</td>'), [(16, 17, False)])
    want_eq(out_, u"横棒だけ", raw_pred(ms, u"－"), [(0, 0, True)])
    want_eq(out_, u"横棒だけ(組の形)", raw_pred(ms, u"－", nil_self=False), [(0, 0, False)])
    want_eq(out_, u"横棒の前の空白", raw_pred(ms, u"  －"), [(2, 2, True)])
    want_eq(out_, u"横棒が 2 つ", raw_pred(ms, u"－－"), [(0, 0, True)])
    want_eq(out_, u"span の前", raw_pred(ms, u"<span>－</span>"), [(0, 0, True)])
    want_eq(out_, u"span の前(属性つき)", raw_pred(ms, u'<span class="x">－</span>'), [(0, 0, True)])
    want_eq(out_, u"span の前の空白は戻る先に含まれる", raw_pred(ms, u" <span>－</span>"), [(1, 1, True)])
    want_eq(out_, u"span の重なる前", raw_pred(ms, u"<span><span>－</span></span>"), [(0, 0, True)])
    want_eq(out_, u"span でないタグの前では戻らない", raw_pred(ms, u"<b>－</b>"), [(3, 3, True)])
    want_eq(out_, u"span の開きタグと横棒の間に字が在れば戻らない", raw_pred(ms, u"<span> －</span>"), [(7, 7, True)])
    want_eq(out_, u"span の外のタグも戻らない", raw_pred(ms, u"<b><span>－</span></b>"), [(3, 3, True)])
    want_eq(out_, u"文字参照だけは横棒でない", raw_pred(ms, u"&#8211;"), [])
    want_eq(out_, u"横棒と字は空の fact でない", raw_pred(ms, u"－a"), [])
    want_eq(out_, u"横棒と数なら数", raw_pred(ms, u"－5"), [(1, 2, False)])
    want_eq(out_, u"cell の中の表", raw_pred(ms, u"<table><tr><td>1,000</td></tr></table>"), [])
    want_eq(out_, u"cell の中の表(大文字)", raw_pred(ms, u"<TABLE><tr><td>1</td></tr></TABLE>"), [])
    want_eq(out_, u"空の cell", raw_pred(ms, u""), [])
    # ---- cell の数え方
    want_eq(out_, u"cell の数え方", ms.cells_of(u"<table><tr><td>a</td><td colspan=\"2\">b</td><td>c</td></tr></table>"), [(0, 0, 0, 15, 16), (0, 0, 1, 37, 38), (0, 0, 3, 47, 48)])
    # ---- 行の並び・parent・before
    carried = [od([("kind", "nonNumeric"), ("self", False), ("start", 0), ("end", 20), ("parent", -1), ("attrs", {})]),
               od([("kind", "nonNumeric"), ("self", False), ("start", 5), ("end", 10), ("parent", 0), ("attrs", {})]),
               od([("kind", "nonNumeric"), ("self", False), ("start", 30), ("end", 40), ("parent", -1), ("attrs", {})])]
    rows, order = ms.merge_rows(carried, [(2, 3, False), (6, 7, False), (12, 13, False), (35, 35, True), (50, 51, False)])
    want_eq(out_, u"行の並び", [(r["kind"], r["start"]) for r in rows], [("nonNumeric", 0), ("nonFraction", 2), ("nonNumeric", 5), ("nonFraction", 6), ("nonFraction", 12), ("nonNumeric", 30), ("nonFraction", 35), ("nonFraction", 50)])
    want_eq(out_, u"parent(囲む最も内側の持ち込みの行・無ければ -1)", [r["parent"] for r in rows], [-1, 0, 0, 2, 0, -1, 5, -1])
    want_eq(out_, u"持ち込みの行の parent の付け直し", [rows[i]["parent"] for i in (2, 5)], [0, -1])
    rows2, _o = ms.merge_rows(carried, [(5, 6, False)])
    want_eq(out_, u"同じ start では囲む行が先", [(r["kind"], r["start"], r["parent"]) for r in rows2][:4], [("nonNumeric", 0, -1), ("nonNumeric", 5, 0), ("nonFraction", 5, 1), ("nonNumeric", 30, -1)])
    rows5, _o = ms.merge_rows([od([("kind", "nonNumeric"), ("self", False), ("start", 0), ("end", 20), ("parent", -1), ("attrs", {})])], [(15, 20, False)])
    want_eq(out_, u"囲む行の end と数の fact の end が同じなら囲む", [r["parent"] for r in rows5], [-1, 0])
    c3 = [od([("kind", "nonNumeric"), ("self", False), ("start", 0), ("end", 5), ("parent", -1), ("attrs", {})]), od([("kind", "nonNumeric"), ("self", False), ("start", 10), ("end", 30), ("parent", -1), ("attrs", {})]),
          od([("kind", "nonNumeric"), ("self", False), ("start", 12), ("end", 20), ("parent", 1), ("attrs", {})])]
    rows6, _o = ms.merge_rows(c3, [(6, 7, False)])
    want_eq(out_, u"持ち込みの行の parent は数の fact が前に入った分だけ付け直す", [(r["kind"], r["parent"]) for r in rows6], [("nonNumeric", -1), ("nonFraction", -1), ("nonNumeric", -1), ("nonNumeric", 2)])
    rows3, _o = ms.merge_rows([od([("kind", "nonNumeric"), ("self", False), ("start", 5), ("end", 6), ("parent", -1), ("attrs", {})])], [(5, 8, False)])
    want_eq(out_, u"同じ start で囲まない行は数が先", [(r["kind"], r["start"], r["parent"]) for r in rows3], [("nonFraction", 5, -1), ("nonNumeric", 5, -1)])
    rows4, _o = ms.merge_rows([od([("kind", "nonNumeric"), ("self", True), ("start", 5), ("end", 5), ("parent", -1), ("attrs", {})])], [(5, 5, True)])
    want_eq(out_, u"自己閉じの行は囲まない", [(r["kind"], r["parent"]) for r in rows4], [("nonFraction", -1), ("nonNumeric", -1)])
    want_eq(out_, u"before(持ち込みの行の中の数 + start が位置より前の数の fact)", ms.header_before({"before": 2, "pos": 6}, order, [(2, 3, False), (6, 7, False), (12, 13, False), (35, 35, True), (50, 51, False)]), 3)
    # ---- 文脈の規則
    want_eq(out_, u"member の字(_cor で終わる接頭辞)", ms.token_of(u"jppfs_cor:Mem1"), u"Mem1")
    want_eq(out_, u"member の字(そうでない接頭辞)", ms.token_of(u"jpcrp030000-asr_E0-000:KMember"), u"jpcrp030000-asr_E0-000KMember")
    want_eq(out_, u"member の字(: が無い)", ms.token_of(u"Plain"), u"Plain")
    want_eq(out_, u"連結個別の軸", (ms.is_cnc(CNC), ms.is_cnc(AXIS)), (True, False))
    pm = {("I", "2025-03-31"): [u"P"]}
    want_eq(out_, u"id の作り方(連結個別が先)", ms.id_of_triple(("I", "2025-03-31", ((u"jppfs_cor:AAxis", u"jppfs_cor:MemA"), (CNC, u"jppfs_cor:NonConsolidatedMember"))), pm), u"P_NonConsolidatedMember_MemA")
    want_eq(out_, u"id の作り方(member 無し)", ms.id_of_triple(("I", "2025-03-31", ()), pm), u"P")
    want_eq(out_, u"期の名が 2 つ", refuses(ms, ms.id_of_triple, ("I", "2025-03-31", ()), {("I", "2025-03-31"): [u"P", u"Q"]}), ms.R_PERIOD)
    want_eq(out_, u"期の名が無い", refuses(ms, ms.id_of_triple, ("I", "2025-03-31", ()), {}), ms.R_PERIOD)
    by_tok = {u"B": [u"x_cor:B"], u"B_C": [u"y_cor:B_C"]}
    want_eq(out_, u"id の分け方(1 通り)", ms.split_id(u"A_B", [u"A"], by_tok), [(u"A", [u"x_cor:B"])])
    want_eq(out_, u"id の分け方(2 つの member)", ms.split_id(u"A_B_B", [u"A"], by_tok), [(u"A", [u"x_cor:B", u"x_cor:B"])])
    want_eq(out_, u"id の分け方(2 通り)", len(ms.split_id(u"A_B_C", [u"A", u"A_B"], {u"C": [u"z_cor:C"], u"B_C": [u"y_cor:B_C"]})), 2)
    want_eq(out_, u"id の分け方(期の名が頭に合わない)", ms.split_id(u"Z_B", [u"A"], by_tok), [])
    want_eq(out_, u"id の分け方(期の名が頭でなく中に在る)", ms.split_id(u"A_B", [u"Z", u"B"], {u"B": [u"m"]}), [])
    want_eq(out_, u"id の分け方(同じ token の member が 2 つなら 2 通り)", len(ms.split_id(u"A_B", [u"A"], {u"B": [u"x_cor:B", u"y_cor:B"]})), 2)
    want_eq(out_, u"期の表の引き", ms.period_map([[u"P", [[u"xbrli:instant", u" 2025-03-31 "]]], [u"Q", [[u"xbrli:startDate", u"2024-04-01"], [u"xbrli:endDate", u"2025-03-31"]]]]),
            {("I", u"2025-03-31"): [u"P"], ("D", u"2025-03-31"): [u"Q"]})
    want_eq(out_, u"日付を替える(時点)", ms.period_change([[u"xbrli:instant", u"2025-03-31"]]), [[u"xbrli:instant", u"1900-01-01"]])
    want_eq(out_, u"日付を替える(期間は終わりの日)", ms.period_change([[u"xbrli:startDate", u"2024-04-01"], [u"xbrli:endDate", u"2025-03-31"]]), [[u"xbrli:startDate", u"2024-04-01"], [u"xbrli:endDate", u"1900-01-01"]])
    want_eq(out_, u"日付を替える(forever は替えない)", ms.period_change([[u"xbrli:forever", u""]]), None)
    with Temp() as d:
        # --- R1 全部規則で当たる
        r = pipeline(ms, doc_r1(), d, u"1")
        p2 = r["p2"]
        want_eq(out_, u"R1 紙 2", (p2["nil_form"], p2["hand"], p2["exceptions"], p2["scheme"], p2["ident"], p2["members"], p2["units"]),
                (u"self", [], [], u"http://x", u"E0", [[u"jppfs_cor:Mem1", AXIS]], [od([("id", u"JPY"), ("measures", [u"iso4217:JPY"]), ("divide", None)])]))
        want_eq(out_, u"R1 期の表", p2["periods"], [[IA, [[u"xbrli:instant", u"2025-03-31"]]], [IB, [[u"xbrli:instant", u"2024-03-31"]]]])
        want_eq(out_, u"R1 数", dict(r["st"]), od([(u"決めの在る cell", 6), (u"1 つずつ書く fact の在る cell", 0), (u"例外 付ける", 0), (u"例外 違う", 0), (u"1 つずつ書く fact の在る cell の中の fact", 0),
                                                 (u"1 つずつ書く fact でない fact", 6), (u"規則が当てた fact", 6), (u"決めの在る cell の外の fact", 0)]))
        want_eq(out_, u"R1 置き場が同じ", (r["same_numbers"], r["same_rows"]), (True, True))
        want_eq(out_, u"R1 文脈", dict((k, v) for k, v in r["defs"].items()), od([(u"元", 3), (u"作った", 3), (u"中身が違う", 0), (u"元にだけ", 0), (u"作った側にだけ", 0), (u"文脈が同じ", True), (u"単位が同じ", True), (u"並びまで同じ", False)]))
        want_eq(out_, u"R1 attrs", (r["diff"], [a["contextRef"] for a in nf_attrs(r["new"])]), (0, [IA, IB, IM] * 2))
        want_eq(out_, u"R1 出す定義の並び(期の表の並び・同じ期の名の中は id の字の順)", [x["id"] for x in resources_of(r["ctx"]) if x.get("type") == "context"], [IA, IM, IB])
        want_eq(out_, u"R1 持ち込みの参照の行が先・単位が最後", [x.get("type") for x in resources_of(r["ctx"])], ["ref", "context", "context", "context", "unit"])
        cells = ms.paper2_cells(p2)
        want_eq(out_, u"R1 紙 2 の欄", (sum(cells.values()), list(cells.values())), (1 + 0 + 0 + 0 + 2 + 4 + 2 + 2, [1, 0, 0, 0, 2, 4, 2, 2]))
        # --- 置き場の規則 1 つずつ(15 行)
        r = pipeline(ms, doc_cells(), d, u"2")
        want_eq(out_, u"規則 1 つずつ 数", dict(r["st"]), od([(u"決めの在る cell", 32), (u"1 つずつ書く fact の在る cell", 2), (u"例外 付ける", 1), (u"例外 違う", 2), (u"1 つずつ書く fact の在る cell の中の fact", 0),
                                                         (u"1 つずつ書く fact でない fact", 23), (u"規則が当てた fact", 21), (u"決めの在る cell の外の fact", 0)]))
        want_eq(out_, u"規則 1 つずつ 例外の cell の行(行 2・4 は fact を持ち、行 7 は無い)", sorted((x[2], len(x[4])) for x in r["p2"]["exceptions"]), [(2, 1), (4, 1), (7, 0)])
        want_eq(out_, u"規則 1 つずつ 1 つずつ書く fact は 2 つ(行 14 と行 15 の列 1)", (len(r["p2"]["hand"]), r["info"]["hand"].count(True)), (2, 2))
        want_eq(out_, u"規則 1 つずつ 空の fact の形", r["p2"]["nil_form"], u"self")
        want_eq(out_, u"規則 1 つずつ 置き場が同じ・attrs が同じ", (r["same_numbers"], r["same_rows"], r["diff"]), (True, True, 0))
        want_eq(out_, u"規則 1 つずつ 文脈が同じ", r["defs"][u"文脈が同じ"], True)
        want_eq(out_, u"規則 1 つずつ 紙 2 の欄(例外の cell 3・例外の cell の中の fact × 2)", (ms.paper2_cells(r["p2"])[u"例外の cell"], ms.paper2_cells(r["p2"])[u"例外の cell の中の fact の始まりと終わり"],
                                                                                  ms.paper2_cells(r["p2"])[u"1 つずつ書く fact の始まりと終わり"]), (3, 4, 4))
        # --- 空の fact の 2 つの形
        r = pipeline(ms, doc_pair(), d, u"3")
        want_eq(out_, u"空の fact(組)", (r["p2"]["nil_form"], r["p2"]["exceptions"], r["same_rows"], r["placed"][0][2][0]["self"] if False else [e["self"] for e in r["placed"][0][2] if e["kind"] == "nonFraction"]), (u"pair", [], True, [False, False]))
        r = pipeline(ms, doc_tie(), d, u"4")
        want_eq(out_, u"空の fact(同数なら自己閉じ・組は例外の cell)", (r["p2"]["nil_form"], [(x[4][0][2]) for x in r["p2"]["exceptions"]], r["same_rows"], r["st"][u"例外 違う"]), (u"self", [False], True, 1))
        # --- id の作り方・member の字の 2 つの形・連結個別の軸が先
        r = pipeline(ms, doc_ids(), d, u"5")
        want_eq(out_, u"id の作り方 文脈が同じ", (r["defs"][u"文脈が同じ"], r["defs"][u"並びまで同じ"], r["diff"], [a["contextRef"] for a in nf_attrs(r["new"])]),
                (True, False, 0, [IA, IA + u"_NonConsolidatedMember_MemA", IA + u"_jpcrp030000-asr_E0-000KMember"]))
        want_eq(out_, u"id の作り方 member の表(2 つの形)", sorted(m for m, _a in r["p2"]["members"]), sorted([u"jppfs_cor:MemA", u"jppfs_cor:NonConsolidatedMember", u"jpcrp030000-asr_E0-000:KMember"]))
        made = [x for x in resources_of(r["ctx"]) if x.get("id") == IA + u"_NonConsolidatedMember_MemA"][0]
        want_eq(out_, u"id の作り方 出した member の並び(連結個別が先)", [d_ for d_, _m in made["members"]], [CNC, u"jppfs_cor:AAxis"])
        # --- id の分け方が 2 通り・期の名が決まらない
        z = os.path.join(d, "amb.zip")
        write_pack(z, doc_ambiguous(), u"6")
        folder = os.path.join(d, "amb")
        ms.make_paper_folder(ms.B.load_package(z), z, folder)
        ms.write_place_folder(folder, os.path.join(d, "amb_placed"))
        want_eq(out_, u"id の分け方が 2 通り", refuses(ms, ms.write_context_folder, os.path.join(d, "amb_placed"), os.path.join(d, "amb_ctx")), ms.R_SPLIT)
        write_pack(z, doc_period_twice(), u"7")
        folder = os.path.join(d, "twice")
        ms.make_paper_folder(ms.B.load_package(z), z, folder)
        ms.write_place_folder(folder, os.path.join(d, "twice_placed"))
        want_eq(out_, u"期の名が決まらない", refuses(ms, ms.write_context_folder, os.path.join(d, "twice_placed"), os.path.join(d, "twice_ctx")), ms.R_PERIOD)
        # --- 単位・期間の文脈・表の外の fact(1 つずつ書く)・文の fact
        r = pipeline(ms, doc_units(), d, u"8")
        want_eq(out_, u"単位が 3 つ(割り算の単位を含む)", (r["defs"][u"単位が同じ"], [u["id"] for u in r["p2"]["units"]], [x["id"] for x in resources_of(r["ctx"]) if x.get("type") == "unit"], r["diff"]),
                (True, [u"JPY", u"USD", u"JPYPerShares"], [u"JPY", u"USD", u"JPYPerShares"], 0))
        want_eq(out_, u"割り算の単位の中身", [u["divide"] for u in r["p2"]["units"]], [None, None, od([("num", [u"iso4217:JPY"]), ("den", [u"xbrli:shares"])])])
        r = pipeline(ms, doc_duration(), d, u"9")
        want_eq(out_, u"期間の文脈", (r["defs"][u"文脈が同じ"], r["diff"], [p[0] for p in r["p2"]["periods"]], ms.paper2_cells(r["p2"])[u"期の表"]), (True, 0, [u"CurrentYearDuration", u"Prior1YearDuration"], 2 * (1 + 2)))
        r = pipeline(ms, doc_outside(), d, u"10")
        want_eq(out_, u"表の外の fact は 1 つずつ書く fact", (len(r["p2"]["hand"]), r["st"][u"1 つずつ書く fact でない fact"], r["same_rows"], r["diff"]), (1, 2, True, 0))
        r = pipeline(ms, doc_sentence(), d, u"11")
        want_eq(out_, u"文の fact の parent", ([(e["kind"], e["parent"]) for e in r["placed"][0][2]], r["same_rows"], r["diff"]), ([("nonNumeric", -1), ("nonFraction", 0), ("nonFraction", 0)], True, 0))
        # --- 決めの無い cell(線の決めが 1 つ欠ける表。向きと 2 つの線の元を替えた 4 つ)
        for label, html, combo, ndec in ((u"ACC", doc_acc(), ("A", "C", "C"), 4), (u"ACE", doc_ace(), ("A", "C", "E"), 4), (u"AEC", doc_aec(), ("A", "E", "C"), 4), (u"B", doc_b(), ("B", "C", "C"), 6)):
            r = pipeline(ms, html, d, u"u" + label)
            t_ = r["sheet"]["tables"][0]
            want_eq(out_, u"決めの無い cell %s 表の選び" % label, (t_["orient"], t_["end_src"], t_["member_src"]), combo)
            want_eq(out_, u"決めの無い cell %s" % label, (r["st"][u"決めの在る cell"], r["st"][u"例外 付ける"], r["st"][u"例外 違う"], r["p2"]["exceptions"], r["same_rows"], r["diff"]), (ndec, 0, 0, [], True, 0))
        # --- 空の fact の形の最頻に 1 つずつ書く fact の空を数えない
        r = pipeline(ms, doc_hand_nil(), d, u"h1")
        want_eq(out_, u"空の fact の形の最頻 1 つずつ書く fact の空は数えない", (r["p2"]["nil_form"], len(r["p2"]["hand"]), r["p2"]["exceptions"], r["same_rows"], r["diff"]), (u"self", 2, [], True, 0))
        # --- name の決めが「無い」線の cell
        r = pipeline(ms, doc_noname(), d, u"h2")
        want_eq(out_, u"name の決めが無い線の cell", (r["st"][u"決めの在る cell"], r["st"][u"例外 付ける"], r["st"][u"例外 違う"], len(r["p2"]["hand"]), r["same_rows"], r["diff"]), (2, 0, 0, 1, True, 0))
        # --- 文の fact の入れ子・頭が同じ・閉じた文の fact の後ろ
        r = pipeline(ms, doc_nested(), d, u"n1")
        rows_ = r["placed"][0][2]
        want_eq(out_, u"入れ子 置き場が同じ", (r["same_numbers"], r["same_rows"], r["diff"]), (True, True, 0))
        want_eq(out_, u"入れ子 数の fact の parent は 3 通り(外・内側の文・頭が同じ文)", (len(set(e["parent"] for e in rows_ if e["kind"] == "nonFraction")), [e["parent"] for e in rows_ if e["kind"] == "nonFraction"].count(-1)), (3, 2))
        # --- 頭の部が後ろに在る(before)
        r = pipeline(ms, doc_late_header(), d, u"n2")
        want_eq(out_, u"頭の部が後ろ", (r["same_rows"], r["placed"][0][3]["before"], r["files"][0][3]["before"], r["diff"], r["defs"][u"文脈が同じ"]), (True, 3, 3, 0, True))
        # --- 使う fact が 1 つだけの文脈(イ・ウ)
        r = pipeline(ms, doc_special_refs(), d, u"n3")
        tags = ms.context_tables(r["placed_dir"])[2]["ids"]
        want_eq(out_, u"使う fact が 1 つだけの文脈 id の出どころ", dict((k, sorted(v)) for k, v in tags.items()),
                {IA: [u"ア"], IB: [u"ア"], u"Prior3YearInstant": [u"ウ"], u"Prior4YearInstant": [u"イ"], u"FilingDateInstant": [u"ウ"]})
        want_eq(out_, u"使う fact が 1 つだけの文脈 文脈が同じ", (r["defs"][u"文脈が同じ"], r["defs"][u"元にだけ"], r["diff"], r["same_rows"]), (True, 0, 0, True))
        # --- 使われない定義・分けられない定義
        r = pipeline(ms, doc_orphans(), d, u"n4")
        want_eq(out_, u"使われない定義 期の表(分けられない id は載せない)", ([n for n, _p in r["p2"]["periods"]], r["p2"]["members"]), ([IA, IB, u"Prior2YearInstant"], []))
        want_eq(out_, u"使われない定義 元にだけ在る id(使われない 3 つ)", (r["defs"][u"元にだけ"], r["defs"][u"作った側にだけ"], r["defs"][u"文脈が同じ"], r["defs"][u"作った"], r["diff"]), (3, 0, False, 2, 0))
        # --- 頭の部が 2 つの .htm に在る(文脈は 1 つ目に入る)
        r = pipeline(ms, doc_second_header(), d, u"n5", extra=[(u"0200000_b_E99999-000_ixbrl.htm", doc_second_header_file())])
        want_eq(out_, u"頭の部が 2 つ", ([len([x for x in (H_["resources"] if H_ else []) if x.get("type") == "context"]) for _n, _p, _F, H_ in r["ctx"]], r["same_rows"], r["diff"]), ([2, 0], True, 0))
        # --- member の並び(4 つ・書いた順の逆)・同じ member の 2 つの軸
        r = pipeline(ms, doc_member_orders(), d, u"n6")
        want_eq(out_, u"member の並び", (r["defs"][u"文脈が同じ"], r["defs"][u"並びまで同じ"], r["diff"], len(r["p2"]["periods"]), len(r["p2"]["members"])), (True, False, 0, 2, 6))
        z = os.path.join(d, "ax.zip")
        write_pack(z, doc_two_axes(), u"n7")
        _s, _i, _f, p2x, _st = ms.make_paper_folder(ms.B.load_package(z), z, os.path.join(d, "axf"))
        want_eq(out_, u"同じ member の軸は最初の定義のもの", p2x["members"], [[u"jppfs_cor:Mem1", AXIS]])
        # --- 混ぜ物の 2 つ
        want_eq(out_, u"混ぜ物(期)の当て先は最初の期の名", ms.period_target(ms.context_tables(pipeline(ms, doc_r1(), d, u"12a")["placed_dir"])[2]), (IA, [[u"xbrli:instant", u"1900-01-01"]]))
        want_eq(out_, u"混ぜ物(期) 日付が混ぜ物の日付と同じ", ms.mix_period_effect(pipeline(ms, doc_epoch(), d, u"12b")["placed_dir"]), (True, False))
        want_eq(out_, u"混ぜ物(期) r1", ms.mix_period_effect(pipeline(ms, doc_r1(), d, u"12")["placed_dir"]), (True, True))
        want_eq(out_, u"混ぜ物(期) 期間の文脈", ms.mix_period_effect(pipeline(ms, doc_duration(), d, u"13")["placed_dir"]), (False, False))
        want_eq(out_, u"混ぜ物(期) 期の名ごとに fact が 1 つ", ms.mix_period_effect(pipeline(ms, doc_single_period(), d, u"14")["placed_dir"]), (False, False))
        scratch = os.path.join(d, "mx1")
        os.makedirs(scratch)
        want_eq(out_, u"混ぜ物(置き場) 空の fact が在る", ms.mix_place_effect(pipeline(ms, doc_cells(), d, u"15")["folder"], scratch), (True, True))
        scratch = os.path.join(d, "mx2")
        os.makedirs(scratch)
        want_eq(out_, u"混ぜ物(置き場) 空の fact が無い", ms.mix_place_effect(pipeline(ms, doc_r1(), d, u"16")["folder"], scratch), (False, False))
        # --- 混ぜ物の判定そのもの(替える関数を差し替えて、判定が違いを見つける)
        placed = pipeline(ms, doc_r1(), d, u"17")["placed_dir"]
        saved = ms.period_change
        try:
            ms.period_change = lambda per: [list(x) for x in per] if per[0][0] == u"xbrli:instant" else None
            want_eq(out_, u"混ぜ物(期) 日付を替えない", ms.mix_period_effect(placed), (True, False))
        finally:
            ms.period_change = saved
        # --- 混ぜ物(期)・混ぜ物(置き場)の判定そのもの(出力を壊す版に差し替えて、判定が違いを見つける)
        orig_ct = ms.context_tables

        def spoil_other_period(folder_, overlay=None):
            ix_, files_, info_ = orig_ct(folder_, overlay)
            if overlay:
                for r_ in files_[info_["hi"]][3]["resources"]:
                    if r_.get("type") == "context" and info_["names"].get(r_["id"]) != list(overlay)[0]:
                        r_["period"] = [[u"xbrli:instant", u"1999-01-01"]]
                        break
            return ix_, files_, info_

        def spoil_other_file(folder_, overlay=None):
            ix_, files_, info_ = orig_ct(folder_, overlay)
            if overlay:
                files_[1][2].append(od([("kind", "nonNumeric"), ("self", True), ("start", 0), ("end", 0), ("parent", -1), ("attrs", {})]))
            return ix_, files_, info_
        two = pipeline(ms, doc_second_header(), d, u"41", extra=[(u"0200000_b_E99999-000_ixbrl.htm", doc_second_header_file())])["placed_dir"]
        try:
            ms.context_tables = spoil_other_period
            want_eq(out_, u"混ぜ物(期) ほかの定義も変わる出力", ms.mix_period_effect(placed), (True, False))
            ms.context_tables = spoil_other_file
            want_eq(out_, u"混ぜ物(期) ほかの file も変わる出力", ms.mix_period_effect(two), (True, False))
        finally:
            ms.context_tables = orig_ct
        orig_pt = ms.place_tables
        cellsf = pipeline(ms, doc_cells(), d, u"42")["folder"]

        def spoil_place(mode_):
            state = {"n": 0}

            def w(folder_):
                ix_, sh_, p2_, files_, em_ = orig_pt(folder_)
                state["n"] += 1
                if state["n"] == 2:
                    mode_(files_, em_)
                return ix_, sh_, p2_, files_, em_
            return w

        def bump_flipped(files_, em_):
            for e in files_[0][2]:
                if e["kind"] == "nonFraction" and (e["start"], e["end"]) in em_[0]:
                    e["parent"] += 5
                    break

        def bump_other(files_, em_):
            for e in files_[0][2]:
                if e["kind"] == "nonFraction" and (e["start"], e["end"]) not in em_[0]:
                    e["parent"] += 7
                    break

        def bump_header(files_, em_):
            files_[0][3]["before"] += 1
        for label_, mode_ in ((u"反転した行の ほかの欄が変わる", bump_flipped), (u"ほかの行が変わる", bump_other), (u"頭の部が変わる", bump_header)):
            scratch = os.path.join(d, "mxs_%s" % abs(hash(label_)))
            os.makedirs(scratch)
            try:
                ms.place_tables = spoil_place(mode_)
                want_eq(out_, u"混ぜ物(置き場) %s出力" % label_, ms.mix_place_effect(cellsf, scratch), (True, False))
            finally:
                ms.place_tables = orig_pt
        # --- 断り(紙を作る命令)
        z = os.path.join(d, "m.zip")
        write_pack(z, doc_missing(), u"14")
        want_eq(out_, u"定義の無い contextRef", refuses(ms, ms.make_paper_folder, ms.B.load_package(z), z, os.path.join(d, "mf")), ms.A1.R_CTX_MISSING)
        write_pack(z, doc_broken(), u"15")
        want_eq(out_, u"表が読めない", refuses(ms, ms.make_paper_folder, ms.B.load_package(z), z, os.path.join(d, "mg")), ms.X.R_TABLE)
    return out_


# ======================================================================== 3. 紙 2 の値・渡す folder に無いもの
def outputs_with(ms, folder, d, edit, tag):
    u"""紙の folder の写しの紙 2 を ``edit`` で替えて、置き場を作り、文脈と単位を作る。(置いた表の bytes の並び, 出した表の bytes の並び) か 断りの理由。"""
    copy_ = os.path.join(d, "edit%s" % tag)
    shutil.copytree(folder, copy_)
    p = os.path.join(copy_, ms.PAPER2_FILE)
    p2 = json.loads(read_text(p), object_pairs_hook=od)
    edit(p2)
    ms.P.write_bytes(p, ms.P.jdump(p2))
    try:
        ms.write_place_folder(copy_, os.path.join(d, "eplaced%s" % tag))
        ms.write_context_folder(os.path.join(d, "eplaced%s" % tag), os.path.join(d, "ectx%s" % tag))
    except (ms.Refuse, ms.P.Refuse) as exc:
        return exc.reason
    return tables_bytes(ms, os.path.join(d, "eplaced%s" % tag)), tables_bytes(ms, os.path.join(d, "ectx%s" % tag))


def tables_bytes(ms, folder):
    idx = ms.P.jload(ms.P.read_bytes(os.path.join(folder, ms.P.INDEX_FILE)))
    return [ms.P.read_bytes(os.path.join(folder, it["tables"])) for it in idx["htm"]]


def paper_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        r = pipeline(ms, doc_cells(), d, u"1")
        folder = r["folder"]
        base = (tables_bytes(ms, r["placed_dir"]), tables_bytes(ms, r["ctx_dir"]))
        want_eq(out_, u"何も替えない(同じ出力)", outputs_with(ms, folder, d, lambda p: None, "0"), base)

        def changed(edit, tag):
            got = outputs_with(ms, folder, d, edit, tag)
            if isinstance(got, str):
                return got
            return (got[0] != base[0], got[1] != base[1])
        # 紙 2 の値を 1 つ変えると、その値が効く出力だけが変わる(置き場 = 置いた folder・文脈と単位 = 出した folder は置き場も含む)
        want_eq(out_, u"紙 2 空の fact の形", changed(lambda p: p.__setitem__("nil_form", u"pair"), "a"), (True, True))
        want_eq(out_, u"紙 2 1 つずつ書く fact の終わり", changed(lambda p: p["hand"][0].__setitem__(2, p["hand"][0][2] + 1), "b"), (True, True))
        want_eq(out_, u"紙 2 例外の cell の fact の終わり", changed(lambda p: [x for x in p["exceptions"] if x[4]][0][4][0].__setitem__(1, [x for x in p["exceptions"] if x[4]][0][4][0][1] + 1), "c"), (True, True))
        want_eq(out_, u"紙 2 例外の cell の fact を消す", changed(lambda p: [x for x in p["exceptions"] if x[4]][0].__setitem__(4, []), "d"), (True, True))
        want_eq(out_, u"紙 2 例外の cell を消す(規則が当たる)", changed(lambda p: p["exceptions"].pop(), "e"), (True, True))
        want_eq(out_, u"紙 2 scheme", changed(lambda p: p.__setitem__("scheme", u"http://other"), "f"), (False, True))
        want_eq(out_, u"紙 2 識別子", changed(lambda p: p.__setitem__("ident", u"E1"), "g"), (False, True))
        want_eq(out_, u"紙 2 期の表の終わりの日(引けなくなって断る)", changed(lambda p: p["periods"][0][1].__setitem__(0, [u"xbrli:instant", u"2020-01-01"]), "h"), ms.R_PERIOD)
        want_eq(out_, u"紙 2 単位の表", changed(lambda p: p["units"][0].__setitem__("measures", [u"iso4217:USD"]), "i"), (False, True))
        want_eq(out_, u"紙 2 単位の表を消す", changed(lambda p: p.__setitem__("units", []), "j"), (False, True))
        # 断る(期の表を空にする・member の表の token を重ねる・期の表の日付を重ねる)
        want_eq(out_, u"紙 2 期の表を空にする", changed(lambda p: p.__setitem__("periods", []), "k"), ms.R_PERIOD)
        r2 = pipeline(ms, doc_r1(), d, u"2")
        folder2 = r2["folder"]
        base2 = (tables_bytes(ms, r2["placed_dir"]), tables_bytes(ms, r2["ctx_dir"]))

        def changed2(edit, tag):
            got = outputs_with(ms, folder2, d, edit, tag)
            return got if isinstance(got, str) else (got[0] != base2[0], got[1] != base2[1])
        want_eq(out_, u"紙 2 member の軸", changed2(lambda p: p["members"][0].__setitem__(1, u"jppfs_cor:OtherAxis"), "m"), (False, True))
        want_eq(out_, u"紙 2 member の表を空にする(id を分けられない)", changed2(lambda p: p.__setitem__("members", []), "n"), ms.R_SPLIT)
        want_eq(out_, u"紙 2 期の表の日付を同じにする(期の名が 2 つ)", changed2(lambda p: p["periods"][1][1].__setitem__(0, [u"xbrli:instant", u"2025-03-31"]), "o"), ms.R_PERIOD)
        want_eq(out_, u"紙 2 のどの欄も欠けたら断る", changed2(lambda p: p.pop("units"), "p"), ms.R_P2)
        r3 = pipeline(ms, doc_duration(), d, u"3")
        base3 = (tables_bytes(ms, r3["placed_dir"]), tables_bytes(ms, r3["ctx_dir"]))
        got3 = outputs_with(ms, r3["folder"], d, lambda p: p["periods"][0][1].__setitem__(0, [u"xbrli:startDate", u"2020-01-01"]), "q")
        want_eq(out_, u"紙 2 期の表の始まりの日", (got3[0] != base3[0], got3[1] != base3[1]) if not isinstance(got3, str) else got3, (False, True))
        # 渡す folder に元の行が無い
        want_eq(out_, u"置き場を作る命令の folder の元の行", ms.leak_place_problems(folder), 0)
        want_eq(out_, u"文脈と単位を作る命令の folder の元の行", ms.leak_context_problems(r["placed_dir"]), 0)
        want_eq(out_, u"紙の folder の元の attrs(便 XS0 の検査)", ms.S.leak_problems(folder), 0)
        # 元の行を置けば数える(門が数える)
        leaky = os.path.join(d, "leaky")
        shutil.copytree(folder, leaky)
        idx = ms.P.jload(ms.P.read_bytes(os.path.join(leaky, ms.P.INDEX_FILE)))
        tp = os.path.join(leaky, idx["htm"][0]["tables"])
        tab = ms.P.jload(ms.P.read_bytes(tp))
        tab["F"].append(od([("kind", "nonFraction"), ("self", False), ("start", 0), ("end", 1), ("parent", -1), ("attrs", {"name": "x"})]))
        tab["H"]["resources"].append(od([("type", "context"), ("id", u"X"), ("scheme", u"s"), ("ident", u"i"), ("period", []), ("members", []), ("has_scenario", False)]))
        ms.P.write_bytes(tp, ms.P.jdump(tab))
        want_eq(out_, u"置き場を作る命令の folder に数の fact の行と文脈を置けば数える", ms.leak_place_problems(leaky), 2)
        want_eq(out_, u"文脈と単位を作る命令の folder に attrs と文脈を置けば数える", ms.leak_context_problems(leaky), 2)
        leaky2 = os.path.join(d, "leaky2")
        shutil.copytree(r["placed_dir"], leaky2)
        idx2 = ms.P.jload(ms.P.read_bytes(os.path.join(leaky2, ms.P.INDEX_FILE)))
        tp2 = os.path.join(leaky2, idx2["htm"][0]["tables"])
        tab2 = ms.P.jload(ms.P.read_bytes(tp2))
        [e for e in tab2["F"] if e["kind"] == "nonFraction"][0]["attrs"] = {"name": "x"}
        ms.P.write_bytes(tp2, ms.P.jdump(tab2))
        want_eq(out_, u"置いた folder の数の fact に attrs が在れば数える", ms.leak_context_problems(leaky2), 1)
        # 紙の folder の中身: 数の fact の行が無い・表 H に文脈と単位が無い・持ち込みの行は元のまま・紙 2 に 1 つずつ書く fact でない fact の行が無い(例外の cell を除く)
        for (_n, _p, F, H), tab_ in zip(r["files"], tables_of(ms, folder)):
            keep = [e for e in F if e["kind"] != "nonFraction"]
            want_eq(out_, u"紙の folder の持ち込みの行(kind・start・end)", [(e["kind"], e["start"], e["end"]) for e in tab_["F"]], [(e["kind"], e["start"], e["end"]) for e in keep])
            want_eq(out_, u"紙の folder の表 H(文脈と単位が無く参照は在る)", sorted(set(x.get("type") for x in (tab_["H"]["resources"] if tab_["H"] else []))), [] if not (H and any(x.get("type") == "ref" for x in H["resources"])) else ["ref"])
        p2 = r["p2"]
        exc_facts = sum(len(x[4]) for x in p2["exceptions"])
        want_eq(out_, u"紙 2 の置き場の数 = 1 つずつ書く fact + 例外の cell の中の fact", len(p2["hand"]) + exc_facts, 2 + 2)
        want_eq(out_, u"紙 2 の hand は 1 つずつ書く fact だけ", len(p2["hand"]), r["info"]["hand"].count(True))
        # 紙の欄の数は紙 2 の file を読み戻した値
        back = ms.P.jload(ms.P.read_bytes(os.path.join(folder, ms.PAPER2_FILE)))
        want_eq(out_, u"紙 2 の欄の数(読み戻し)", sum(ms.paper2_cells(back).values()), 1 + 4 + 3 + 4 + 2 + 2 * (1 + 1) + 2 * 0 + 2 * 1)
        # 持ち込みの表 F の parent は持ち込みの行の中の番号
        rs = pipeline(ms, doc_sentence(), d, u"4s")
        want_eq(out_, u"持ち込みの表 F(文の fact だけ)", [(e["kind"], e["parent"]) for e in tables_of(ms, rs["folder"])[0]["F"]], [("nonNumeric", -1)])
        want_eq(out_, u"持ち込みの before(持ち込みの行の中の数)", tables_of(ms, rs["folder"])[0]["H"]["before"], 0)
        rl = pipeline(ms, doc_late_header(), d, u"5l")
        want_eq(out_, u"頭の部が後ろの書類の持ち込みの before(文の fact 1 つ)", tables_of(ms, rl["folder"])[0]["H"]["before"], 1)
        # 表 H が無い folder では文脈と単位を作る命令が断る
        nohdr = os.path.join(d, "nohdr")
        shutil.copytree(r["placed_dir"], nohdr)
        idxn = ms.P.jload(ms.P.read_bytes(os.path.join(nohdr, ms.P.INDEX_FILE)))
        tpn = os.path.join(nohdr, idxn["htm"][0]["tables"])
        tabn = ms.P.jload(ms.P.read_bytes(tpn))
        tabn["H"] = None
        ms.P.write_bytes(tpn, ms.P.jdump(tabn))
        want_eq(out_, u"表 H が無い", refuses(ms, ms.write_context_folder, nohdr, os.path.join(d, "nohdr_out")), ms.R_NOHDR)
    return out_


def tables_of(ms, folder):
    idx = ms.P.jload(ms.P.read_bytes(os.path.join(folder, ms.P.INDEX_FILE)))
    return [ms.P.jload(ms.P.read_bytes(os.path.join(folder, it["tables"]))) for it in idx["htm"]]


# ======================================================================== 4. 答えを読まない(字で縛る)
BLIND_FUNCS = ("read_paper_folder", "place_tables", "write_place_folder", "context_tables", "write_context_folder", "step_main", "place_main", "context_main", "place_command", "context_command",
               "step_command", "context_resources", "needed_ids", "file_placements", "merge_rows", "header_before", "cells_of", "masked", "number_runs", "dash_only", "nil_position", "predict_cell",
               "decided_cell", "encloses", "token_of", "is_cnc", "id_of_triple", "split_id", "period_map", "copy_folder", "tables_bytes")
BLIND_DENY_ATTRS = ("doc_texts", "facts_of_files", "facts_of_text", "load_package", "peel_tables", "context_defs", "resolve_facts", "strip_text", "build_files", "contexts_of_text", "build_sheet",
                    "make_sheet_folder", "make_paper_folder", "make_paper2", "peel_folder", "sheet_cells", "compare_attrs")
BLIND_DENY_NAMES = ("make_paper_folder", "make_paper2", "carried_tables", "measure_one", "mix_period_effect", "mix_place_effect", "compare_definitions", "number_rows", "all_rows", "definition_map",
                    "unit_map", "split_definition", "paper2_cells", "same_bytes", "leak_place_problems", "leak_context_problems", "paper_main", "member_pairs", "entries", "zip_path")
BLIND_DENY_ARGS = ("entries", "zip_path", "zip", "orig", "original", "facts", "files_orig")


def blind_problems(src=None):
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out_ = []
    funcs = dict((n.name, n) for n in tree.body if isinstance(n, ast.FunctionDef))
    for name in BLIND_FUNCS:
        fn = funcs.get(name)
        if fn is None:
            out_.append(u"答えを読まない側の関数が無い: %s" % name)
            continue
        args = [a.arg for a in fn.args.args + fn.args.kwonlyargs]
        if any(a in BLIND_DENY_ARGS for a in args):
            out_.append(u"%s が元の包み・元の fact を受け取れる形(引数 %s)" % (name, args))
        for n in ast.walk(fn):
            if isinstance(n, ast.Attribute) and n.attr in BLIND_DENY_ATTRS:
                out_.append(u"%s が答えを読む関数 %s を呼んでいる" % (name, n.attr))
            if isinstance(n, ast.Name) and n.id in BLIND_DENY_NAMES:
                out_.append(u"%s が答えを読む側の関数 %s を呼んでいる" % (name, n.id))
    for name in ("place_command", "context_command", "exec_step"):
        if name not in funcs:
            out_.append(u"%s が無い" % name)
    for name, word in (("place_command", "place"), ("context_command", "context")):
        cmd = funcs.get(name)
        if cmd is not None:
            args = [a.arg for a in cmd.args.args]
            body = ast.get_source_segment(src, cmd)
            if args != ["folder", "out"] or "step_command(" not in body or ('"%s"' % word) not in body:
                out_.append(u"%s の呼び方が python3 -I ... %s <folder> <folder> でない" % (name, word))
    sc = funcs.get("step_command")
    if sc is not None:
        body = ast.dump(sc.body[-1])
        if [a.arg for a in sc.args.args] != ["name", "folder", "out"] or "Constant(value='-I')" not in body or "SCRIPT_PATH" not in body:
            out_.append(u"step_command の呼び方が python3 -I <script> <命令> <folder> <folder> でない")
    sm = funcs.get("step_main")
    if sm is not None and "len(args) != 2" not in ast.get_source_segment(src, sm):
        out_.append(u"置き場を作る・文脈と単位を作る命令が引数の数(2)を見ない")
    main = funcs.get("main")
    if main is not None:
        seg = ast.get_source_segment(src, main)
        if 'argv[0] == "place"' not in seg or 'argv[0] == "context"' not in seg:
            out_.append(u"main が place・context を別の入口に渡していない")
    return out_


def blind_behaviour_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    err = io.StringIO()
    old = sys.stderr
    sys.stderr = err
    try:
        rcs = tuple((ms.place_main(a), ms.context_main(a)) for a in ([], ["a"], ["a", "b", "c"], ["/nonexistent/x", "/nonexistent/y"]))
    finally:
        sys.stderr = old
    want_eq(out_, u"place・context の終わりの値", rcs, ((ms.EXIT_USAGE, ms.EXIT_USAGE), (ms.EXIT_USAGE, ms.EXIT_USAGE), (ms.EXIT_USAGE, ms.EXIT_USAGE), (ms.EXIT_DECLINE, ms.EXIT_DECLINE)))
    want_eq(out_, u"place の命令の並び", ms.place_command(u"F", u"O")[1:], [u"-I", ms.SCRIPT_PATH, u"place", u"F", u"O"])
    want_eq(out_, u"context の命令の並び", ms.context_command(u"F", u"O")[1:], [u"-I", ms.SCRIPT_PATH, u"context", u"F", u"O"])
    with Temp() as d:
        # 2 つの命令は元の包みを使わない: 包みを消した folder でも作れる
        r = pipeline(ms, doc_r1(), d, u"1")
        os.remove(os.path.join(d, "q1.zip"))
        ms.write_place_folder(r["folder"], os.path.join(d, "o1"))
        ms.write_context_folder(os.path.join(d, "o1"), os.path.join(d, "o2"))
        # 出す folder の file の集まりは入れた folder と同じ
        want_eq(out_, u"置いた folder の file", sorted(os.listdir(os.path.join(d, "o1"))), sorted(os.listdir(r["folder"])))
        want_eq(out_, u"出した folder の file", sorted(os.listdir(os.path.join(d, "o2"))), sorted(os.listdir(r["folder"])))
        # 呼び出し(proc)の失敗の読み
        want_eq(out_, u"exec_step の断り", ms.exec_step("place", u"置き場を作る", r["folder"], os.path.join(d, "o3"), d, lambda c, w, t: (2, u"DECLINE: 理由\n", False))[:2], (False, u"理由"))
        want_eq(out_, u"exec_step の終わりの値", ms.exec_step("context", u"文脈と単位を作る", r["folder"], os.path.join(d, "o4"), d, lambda c, w, t: (1, u"", False))[:2], (False, u"文脈と単位を作る命令が 0 でない終わりの値で終わった"))
        want_eq(out_, u"exec_step の時間", ms.exec_step("place", u"置き場を作る", r["folder"], os.path.join(d, "o5"), d, lambda c, w, t: (None, u"", True))[:2], (False, u"置き場を作る命令が時間の上限を超えた"))
        # 命令に渡した引数は folder 2 つだけ
        seen = []
        ms.exec_step("place", u"置き場を作る", r["folder"], os.path.join(d, "o6"), d, lambda c, w, t: seen.append(list(c)) or (0, u"", False))
        want_eq(out_, u"exec_step の引数", (seen[0][1], seen[0][3:]), (u"-I", [u"place", r["folder"], os.path.join(d, "o6")]))
    return out_


# ======================================================================== 5. 書類 1 本の通し・塊・記録
def measure_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        os.makedirs(os.path.join(d, "tmp"))
        rec, log = run_one(ms, doc_r1(), d, u"1")
        want_eq(out_, u"通し 呼んだ命令", log, [u"place", u"context", u"attrs", u"build", u"build"])
        want_eq(out_, u"通し 断り", (rec[u"断った"], rec[u"断った段"], rec[u"断った理由"]), (False, u"", u""))
        want_eq(out_, u"通し 数", (rec[u"fact の数"], rec[u"1 つずつ書く fact の数"], rec[u"決めの在る cell の数"], rec[u"規則が当てた fact の数"], rec[u"1 つずつ書く fact でない fact の数"]), (6, 0, 6, 6, 6))
        want_eq(out_, u"通し 置き場", (rec[u"置き場を作れた"], rec[u"置き場が同じ"], rec[u"表 F の行が全部同じ"]), (True, True, True))
        want_eq(out_, u"通し 文脈", (rec[u"文脈と単位を作れた"], rec[u"元の文脈の定義の数"], rec[u"作った定義の数"], rec[u"中身が違う id の数"], rec[u"元にだけ在る id の数"], rec[u"作った側にだけ在る id の数"],
                                 rec[u"文脈が同じ"], rec[u"単位が同じ"], rec[u"定義の並びまで同じ"]), (True, 3, 3, 0, 0, 0, True, True, False))
        want_eq(out_, u"通し 数え物", (rec[u"期の名の数"], rec[u"member の数"], rec[u"単位の数"], rec[u"(ア)だけが指す id の数"]), (2, 1, 1, 3))
        want_eq(out_, u"通し 比べ方 1 の属性", (rec[u"属性を作れた"], rec[u"表 F が同じ"], rec[u"attrs が違う fact の数"]), (True, True, 0))
        want_eq(out_, u"通し 組む", (rec[u"組めた"], rec[u"2 回組んで同じ"]), (True, True))
        want_eq(out_, u"通し 混ぜ物", (dict(rec[u"混ぜ物(期)"]), dict(rec[u"混ぜ物(置き場)"])), ({u"作れた": True, u"効いた": True}, {u"作れた": False, u"効いた": False}))
        want_eq(out_, u"通し 道具の読みが同じ", (rec[u"fact が同じ"], rec[u"タクソノミが同じ"], rec[u"鳴り方が同じ"], rec[u"全部同じ"]), (True, True, True, True))
        want_eq(out_, u"通し 秒の欄", (rec[u"置き場を作る命令の秒"] is not None, rec[u"文脈と単位を作る命令の秒"] is not None, rec[u"属性を作る命令の秒"] is not None, rec[u"組む命令の秒"] is not None,
                                  rec[u"組み直しの 1 回"] is not None), (True,) * 5)
        want_eq(out_, u"通し 紙の欄", (rec[u"紙の欄の数"], list(rec[u"紙の欄の数(項ごと)"]) == list(ms.CELL_KEYS)), (20 + 11, True))
        want_eq(out_, u"通し 包みが元と byte で同じ", rec[u"包みが元と byte で同じ"], False)
        # 空の fact の在る書類(混ぜ物(置き場)が作れる)・1 つずつ書く fact・例外の cell
        rec, _log = run_one(ms, doc_cells(), d, u"2")
        want_eq(out_, u"通し 規則 1 つずつ", (rec[u"決めの在る cell の数"], rec[u"1 つずつ書く fact の在る cell の数"], rec[u"例外の cell の数(元は fact が無いのに規則が付ける)"],
                                        rec[u"例外の cell の数(元は fact が在るのに規則が違う)"], rec[u"規則が当てた fact の数"], rec[u"1 つずつ書く fact でない fact の数"], rec[u"置き場が同じ"],
                                        rec[u"表 F が同じ"], dict(rec[u"混ぜ物(置き場)"])), (32, 2, 1, 2, 21, 23, True, True, {u"作れた": True, u"効いた": True}))
        want_eq(out_, u"通し (ア)だけが指す id(1 つずつ書く fact と共有する id は数えない)", rec[u"(ア)だけが指す id の数"], 1)
        # 書類ごとの通し(id の作り方・単位・入れ子・頭の部)
        rec, _log = run_one(ms, doc_ids(), d, u"2a")
        want_eq(out_, u"通し id の作り方", (rec[u"文脈が同じ"], rec[u"定義の並びまで同じ"], rec[u"表 F が同じ"], rec[u"fact が同じ"]), (True, False, True, True))
        rec, _log = run_one(ms, doc_units(), d, u"2b")
        want_eq(out_, u"通し 単位", (rec[u"単位が同じ"], rec[u"単位の数"], rec[u"組めた"]), (True, 3, True))
        rec, _log = run_one(ms, doc_nested(), d, u"2c")
        want_eq(out_, u"通し 入れ子", (rec[u"置き場が同じ"], rec[u"表 F の行が全部同じ"], rec[u"表 F が同じ"], rec[u"組めた"]), (True, True, True, True))
        rec, _log = run_one(ms, doc_late_header(), d, u"2d")
        want_eq(out_, u"通し 頭の部が後ろ", (rec[u"置き場が同じ"], rec[u"表 F の行が全部同じ"], rec[u"文脈が同じ"], rec[u"fact が同じ"]), (True, True, True, True))
        rec, _log = run_one(ms, doc_special_refs(), d, u"2e")
        want_eq(out_, u"通し 使う fact が 1 つだけの文脈", (rec[u"文脈が同じ"], rec[u"元にだけ在る id の数"], rec[u"表 F が同じ"]), (True, 0, True))
        rec, _log = run_one(ms, doc_orphans(), d, u"2f")
        want_eq(out_, u"通し 使われない定義", (rec[u"文脈が同じ"], rec[u"元にだけ在る id の数"], rec[u"元の文脈の定義の数"], rec[u"作った定義の数"]), (False, 3, 5, 2))
        # 置いた folder が元と違えば、比べ方 1 が数える(数の fact の行・持ち込みの行)
        rec, _log = run_one(ms, doc_r1(), d, u"2g", alter_place="number")
        want_eq(out_, u"比べ方 1(置き場)が数える 数の fact の行", (rec[u"置き場が同じ"], rec[u"表 F の行が全部同じ"]), (False, False))
        rec, _log = run_one(ms, doc_sentence(), d, u"2h", alter_place="carried")
        want_eq(out_, u"比べ方 1(置き場)が数える 持ち込みの行", (rec[u"置き場が同じ"], rec[u"表 F の行が全部同じ"]), (True, False))
        rec, _log = run_one(ms, doc_r1(), d, u"2i", alter_ctx="unit")
        want_eq(out_, u"比べ方 2 が数える 単位", (rec[u"単位が同じ"], rec[u"文脈が同じ"], rec[u"中身が違う id の数"]), (False, True, 0))
        if not stops(ms, run_one, ms, doc_r1(), d, u"2j", alter_place="attrs"):
            out_.append(u"置いた folder の数の fact に attrs が在るのに止まらない")
        # 道具の読みが違う書類(偽の道具が書き出しだけ・fact だけ違う CSV を書く)
        rec, _log = run_one(ms, doc_r1(), d, u"3", mode=u"tax_differs")
        want_eq(out_, u"通し 書き出しだけ違う", (rec[u"fact が同じ"], rec[u"タクソノミが同じ"], rec[u"全部同じ"]), (True, False, False))
        rec, _log = run_one(ms, doc_r1(), d, u"4", mode=u"facts_differs")
        want_eq(out_, u"通し fact だけ違う", (rec[u"fact が同じ"], rec[u"タクソノミが同じ"], rec[u"全部同じ"]), (False, True, False))
        seen = []
        rec, _log = run_one(ms, doc_r1(), d, u"5", seen=seen)
        want_eq(out_, u"通し 道具に掛けた包み", (len(seen), seen[0] == seen[1], seen[2] == seen[3], seen[0] != seen[2]) if len(seen) == 4 else len(seen), (4, True, True, True))
        # 断り: 紙を作る・置き場を作る・文脈と単位を作る・属性を作る・組む
        rec, log = run_one(ms, doc_missing(), d, u"6")
        want_eq(out_, u"断り 紙を作る", (rec[u"断った"], rec[u"断った段"], rec[u"断った理由"], rec[u"fact の数"], log), (True, u"紙を作る", ms.A1.R_CTX_MISSING, None, []))
        rec, log = run_one(ms, doc_broken(), d, u"7")
        want_eq(out_, u"断り 表が読めない", (rec[u"断った段"], rec[u"断った理由"]), (u"紙を作る", ms.X.R_TABLE))
        rec, log = run_one(ms, doc_r1(), d, u"8", fail={"place": (2, u"DECLINE: 置き場の理由\n", False)})
        want_eq(out_, u"断り 置き場を作る", (rec[u"断った段"], rec[u"断った理由"], rec[u"置き場を作れた"], rec[u"組めた"], log, rec[u"fact の数"], rec[u"紙の欄の数"]), (u"置き場を作る", u"置き場の理由", False, False, [u"place"], 6, 31))
        rec, log = run_one(ms, doc_r1(), d, u"9", fail={"context": (2, u"DECLINE: 文脈の理由\n", False)})
        want_eq(out_, u"断り 文脈と単位を作る", (rec[u"断った段"], rec[u"断った理由"], rec[u"置き場を作れた"], rec[u"置き場が同じ"], rec[u"文脈と単位を作れた"], log), (u"文脈と単位を作る", u"文脈の理由", True, True, False, [u"place", u"context"]))
        rec, log = run_one(ms, doc_ambiguous(), d, u"10")
        want_eq(out_, u"断り id の分け方(本物の命令)", (rec[u"断った段"], rec[u"断った理由"], log), (u"文脈と単位を作る", ms.R_SPLIT, [u"place", u"context"]))
        rec, log = run_one(ms, doc_period_twice(), d, u"11")
        want_eq(out_, u"断り 期の名が決まらない(本物の命令)", (rec[u"断った段"], rec[u"断った理由"]), (u"文脈と単位を作る", ms.R_PERIOD))
        rec, log = run_one(ms, doc_r1(), d, u"12", fail={"attrs": (2, u"DECLINE: 属性の理由\n", False)})
        want_eq(out_, u"断り 属性を作る", (rec[u"断った段"], rec[u"断った理由"], rec[u"文脈が同じ"], rec[u"属性を作れた"], rec[u"組めた"], log), (u"属性を作る", u"属性の理由", True, False, False, [u"place", u"context", u"attrs"]))
        rec, log = run_one(ms, doc_r1(), d, u"13", fail={"build": (1, u"", False)})
        want_eq(out_, u"断り 組む", (rec[u"断った段"], rec[u"断った理由"], rec[u"属性を作れた"], rec[u"表 F が同じ"], rec[u"組めた"]), (u"組む", u"組む命令が 0 でない終わりの値で終わった", True, True, False))
        rec, log = run_one(ms, doc_r1(), d, u"14", drop_build_file=True)
        want_eq(out_, u"断り 出す folder の file が足りない", (rec[u"断った段"], rec[u"断った理由"], rec[u"組めた"]), (u"組む", ms.R_BUILD_OUT, False))
        rec, log = run_one(ms, doc_r1(), d, u"15", second_build_differs=True)
        want_eq(out_, u"2 回目の包みが違う", (rec[u"組めた"], rec[u"2 回組んで同じ"], rec[u"断った"]), (True, False, False))
        # 2 つの命令が元と違う物を出せば、比べ方が数える
        rec, log = run_one(ms, doc_r1(), d, u"16", alter_ctx=True)
        want_eq(out_, u"比べ方 2 が違いを数える", (rec[u"文脈が同じ"], rec[u"中身が違う id の数"], rec[u"組めた"]), (False, 1, True))
        rec, log = run_one(ms, doc_r1(), d, u"17", alter_attrs=True)
        want_eq(out_, u"比べ方 1 の属性が違いを数える", (rec[u"表 F が同じ"], rec[u"attrs が違う fact の数"], dict((k, v) for k, v in rec[u"attrs が違う属性ごとの fact の数(重ねて数える)"].items() if v), rec[u"組めた"]),
                (False, 1, {u"属性 name": 1}, True))
        # 紙の folder・置いた folder に元の行が在れば止まる
        saved = ms.carried_tables
        try:
            def keep_numbers(files, p2_unused=None):
                out = saved(files)
                return [(n, p, F + [od([("kind", "nonFraction"), ("self", False), ("start", 0), ("end", 0), ("parent", -1), ("attrs", {})])], H) for n, p, F, H in out]
            ms.carried_tables = keep_numbers
            if not stops(ms, run_one, ms, doc_r1(), d, u"18"):
                out_.append(u"置き場を作る命令に渡す folder に数の fact の行が在るのに止まらない")
        finally:
            ms.carried_tables = saved
        saved = ms.write_place_folder
        # 置き場の比べ方の関数そのもの
        rows_a = [(u"n", u"p", [od([("kind", "nonFraction"), ("self", False), ("start", 1), ("end", 2), ("parent", -1), ("attrs", {})])], None)]
        rows_b = [(u"n", u"p", [od([("kind", "nonFraction"), ("self", True), ("start", 1), ("end", 2), ("parent", -1), ("attrs", {})])], None)]
        rows_c = [(u"n", u"p", [od([("kind", "nonFraction"), ("self", False), ("start", 1), ("end", 2), ("parent", 0), ("attrs", {})])], None)]
        rows_d = [(u"n", u"p", [od([("kind", "nonFraction"), ("self", False), ("start", 1), ("end", 3), ("parent", -1), ("attrs", {})])], None)]
        want_eq(out_, u"置き場の比べ方", (ms.number_rows(rows_a) == ms.number_rows(rows_a), ms.number_rows(rows_a) == ms.number_rows(rows_b), ms.number_rows(rows_a) == ms.number_rows(rows_c), ms.number_rows(rows_a) == ms.number_rows(rows_d)),
                (True, False, False, False))
        rows_e = [(u"n", u"p", [od([("kind", "nonNumeric"), ("self", False), ("start", 1), ("end", 2), ("parent", -1), ("attrs", {})])], None)]
        rows_h1 = [(u"n", u"p", [], od([("before", 1), ("pos", 5)]))]
        rows_h2 = [(u"n", u"p", [], od([("before", 2), ("pos", 5)]))]
        rows_h3 = [(u"n", u"p", [], od([("before", 1), ("pos", 6)]))]
        want_eq(out_, u"置き場の比べ方(全部の行)", (ms.all_rows(rows_a) == ms.all_rows(rows_a), ms.all_rows(rows_a) == ms.all_rows(rows_b), ms.all_rows(rows_a) == ms.all_rows(rows_e),
                                              ms.all_rows(rows_h1) == ms.all_rows(rows_h1), ms.all_rows(rows_h1) == ms.all_rows(rows_h2), ms.all_rows(rows_h1) == ms.all_rows(rows_h3)), (True, False, False, True, False, False))
        # 定義の比べ方の関数そのもの
        def ctxfile(*rs):
            return [(u"n", u"p", [], od([("resources", list(rs))]))]
        c1 = od([("type", "context"), ("id", u"A"), ("scheme", u"s"), ("ident", u"i"), ("period", [[u"xbrli:instant", u"2025-03-31"]]), ("members", [[AXIS, u"m1"], [u"x", u"m2"]]), ("has_scenario", True)])
        c1b = od([("type", "context"), ("id", u"A"), ("scheme", u"s"), ("ident", u"i"), ("period", [[u"xbrli:instant", u"2025-03-31"]]), ("members", [[u"x", u"m2"], [AXIS, u"m1"]]), ("has_scenario", True)])
        c1c = od([("type", "context"), ("id", u"A"), ("scheme", u"s2"), ("ident", u"i"), ("period", [[u"xbrli:instant", u"2025-03-31"]]), ("members", [[AXIS, u"m1"], [u"x", u"m2"]]), ("has_scenario", True)])
        c1d = od([("type", "context"), ("id", u"A"), ("scheme", u"s"), ("ident", u"i"), ("period", [[u"xbrli:instant", u"2025-03-31"]]), ("members", [[AXIS, u"m1"]]), ("has_scenario", True)])
        c1e = od([("type", "context"), ("id", u"A"), ("scheme", u"s"), ("ident", u"i"), ("period", [[u"xbrli:instant", u"2025-03-31"]]), ("members", [[AXIS, u"m1"], [u"x", u"m2"]]), ("has_scenario", False)])
        c1f = od([("type", "context"), ("id", u"A"), ("scheme", u"s"), ("ident", u"i2"), ("period", [[u"xbrli:instant", u"2025-03-31"]]), ("members", [[AXIS, u"m1"], [u"x", u"m2"]]), ("has_scenario", True)])
        c1g = od([("type", "context"), ("id", u"A"), ("scheme", u"s"), ("ident", u"i"), ("period", [[u"xbrli:instant", u"2024-03-31"]]), ("members", [[AXIS, u"m1"], [u"x", u"m2"]]), ("has_scenario", True)])
        c2 = od([("type", "context"), ("id", u"B"), ("scheme", u"s"), ("ident", u"i"), ("period", [[u"xbrli:instant", u"2025-03-31"]]), ("members", []), ("has_scenario", False)])
        cmp_ = lambda a, b: dict(ms.compare_definitions(a, b))
        want_eq(out_, u"定義の比べ方 同じ", (cmp_(ctxfile(c1), ctxfile(c1))[u"文脈が同じ"], cmp_(ctxfile(c1), ctxfile(c1))[u"並びまで同じ"]), (True, True))
        want_eq(out_, u"定義の比べ方 member の並びは見ない(並びまで同じは偽)", (cmp_(ctxfile(c1), ctxfile(c1b))[u"文脈が同じ"], cmp_(ctxfile(c1), ctxfile(c1b))[u"並びまで同じ"]), (True, False))
        c1h = od([("type", "context"), ("id", u"A"), ("scheme", u"s"), ("ident", u"i"), ("period", [[u"xbrli:instant", u"2025-03-31"]]), ("members", [[u"other", u"m1"], [u"x", u"m2"]]), ("has_scenario", True)])
        for what, other in ((u"scheme", c1c), (u"member の数", c1d), (u"has_scenario", c1e), (u"識別子", c1f), (u"期", c1g), (u"軸", c1h)):
            r_ = cmp_(ctxfile(c1), ctxfile(other))
            want_eq(out_, u"定義の比べ方 %s が違う" % what, (r_[u"文脈が同じ"], r_[u"中身が違う"]), (False, 1))
        r_ = cmp_(ctxfile(c1, c2), ctxfile(c1))
        want_eq(out_, u"定義の比べ方 元にだけ在る id", (r_[u"文脈が同じ"], r_[u"元にだけ"], r_[u"作った側にだけ"], r_[u"元"], r_[u"作った"]), (False, 1, 0, 2, 1))
        r_ = cmp_(ctxfile(c1), ctxfile(c1, c2))
        want_eq(out_, u"定義の比べ方 作った側にだけ在る id", (r_[u"文脈が同じ"], r_[u"元にだけ"], r_[u"作った側にだけ"]), (False, 0, 1))
        r_ = cmp_(ctxfile(c1, c2), ctxfile(c2, c1))
        want_eq(out_, u"定義の比べ方 定義の並び", (r_[u"文脈が同じ"], r_[u"並びまで同じ"]), (True, False))

        def unitfile(*rs):
            return [(u"n", u"p", [], od([("resources", list(rs))]))]
        u1 = od([("type", "unit"), ("id", u"JPY"), ("measures", [u"iso4217:JPY"]), ("divide", None)])
        u2 = od([("type", "unit"), ("id", u"JPY"), ("measures", [u"iso4217:USD"]), ("divide", None)])
        u3 = od([("type", "unit"), ("id", u"PS"), ("measures", []), ("divide", od([("num", [u"iso4217:JPY"]), ("den", [u"xbrli:shares"])]))])
        u4 = od([("type", "unit"), ("id", u"PS"), ("measures", []), ("divide", od([("num", [u"iso4217:JPY"]), ("den", [u"xbrli:pure"])]))])
        want_eq(out_, u"単位の比べ方", (cmp_(unitfile(u1), unitfile(u1))[u"単位が同じ"], cmp_(unitfile(u1), unitfile(u2))[u"単位が同じ"], cmp_(unitfile(u3), unitfile(u4))[u"単位が同じ"], cmp_(unitfile(u1), unitfile(u1, u3))[u"単位が同じ"]),
                (True, False, False, False))
        want_eq(out_, u"byte の比べ方", (ms.same_bytes([(types.SimpleNamespace(filename=ms.P.PUBLICDOC + u"a.htm"), b"x")], {u"a.htm": b"x"}),
                                      ms.same_bytes([(types.SimpleNamespace(filename=ms.P.PUBLICDOC + u"a.htm"), b"x")], {u"a.htm": b"y"}),
                                      ms.same_bytes([(types.SimpleNamespace(filename=ms.P.PUBLICDOC + u"a.htm"), b"x")], {u"b.htm": b"x"})), (True, False, False))
    return out_


def chunk_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        os.makedirs(os.path.join(d, "tmp"))
        plan = [(doc_r1(), {}), (doc_missing(), {}), (doc_cells(), {}), (doc_ambiguous(), {}), (doc_r1(), dict(second_build_differs=True)),
                (doc_r1(), dict(fail={"place": (2, u"DECLINE: 置き場の理由\n", False)})), (doc_r1(), dict(alter_ctx=True)), (doc_r1(), dict(alter_attrs=True)), (doc_orphans(), {})]
        recs = [run_one(ms, h, d, u"%d" % (i + 1), **kw)[0] for i, (h, kw) in enumerate(plan)]
        per = [od([(u"番号", i)] + list(r.items())) for i, r in enumerate(recs, 1)]
        tot = ms.group_totals(per)
        made = [r for r in recs if r[u"fact の数"] is not None]
        want_eq(out_, u"塊 書類・断り", (tot[u"書類の数"], tot[u"断った書類の数"], dict(tot[u"断った段ごとの数"]), dict(tot[u"断った理由ごとの数"])),
                (9, 3, {u"紙を作る": 1, u"置き場を作る": 1, u"文脈と単位を作る": 1, u"属性を作る": 0, u"組む": 0}, {u"紙を作る: " + ms.A1.R_CTX_MISSING: 1, u"置き場を作る: 置き場の理由": 1, u"文脈と単位を作る: " + ms.R_SPLIT: 1}))
        want_eq(out_, u"塊 fact", (tot[u"紙を作れた書類の数"], tot[u"fact の数(紙を作れた書類)"], tot[u"1 つずつ書く fact の数"], tot[u"1 つずつ書く fact でない fact の数"]),
                (8, sum(r[u"fact の数"] for r in made), 2, sum(r[u"fact の数"] for r in made) - 2))
        want_eq(out_, u"塊 fact(手で数える)", tot[u"fact の数(紙を作れた書類)"], 6 + 25 + 3 + 6 + 6 + 6 + 6 + 4)
        want_eq(out_, u"塊 置き場", (tot[u"決めの在る cell の数"], tot[u"1 つずつ書く fact の在る cell の数"], tot[u"例外の cell の数"], tot[u"例外の cell の数(元は fact が無いのに規則が付ける)"],
                                 tot[u"例外の cell の数(元は fact が在るのに規則が違う)"], tot[u"規則が当てた fact の数"], tot[u"例外の cell が在る書類の数"]), (6 + 32 + 3 + 6 + 6 + 6 + 6 + 4, 2, 3, 1, 2, 6 + 21 + 3 + 6 + 6 + 6 + 6 + 4, 1))
        want_eq(out_, u"塊 置き場が同じ", (tot[u"置き場を作れた書類の数"], tot[u"置き場が同じ書類の数"], tot[u"表 F の行が全部同じ書類の数"], tot[u"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数"]), (7, 7, 7, 0))
        want_eq(out_, u"塊 文脈", (tot[u"文脈と単位を作れた書類の数"], tot[u"文脈が同じ書類の数"], tot[u"単位が同じ書類の数"], tot[u"定義の並びまで同じ書類の数"], tot[u"中身が違う id の数"]), (6, 4, 6, 1, 1))
        want_eq(out_, u"塊 元にだけ・作った側にだけ", (tot[u"元にだけ在る id の数"], tot[u"元にだけ在る id が 1 つ以上在る書類の数"], tot[u"作った側にだけ在る id の数"]), (3, 1, 0))
        want_eq(out_, u"塊 数え物", (tot[u"期の名の数"], tot[u"member の数"], tot[u"単位の数"], tot[u"(ア)だけが指す id の数"]), (2 * 5 + 3, 4, 6, 3 + 1 + 3 + 3 + 3 + 2))
        want_eq(out_, u"塊 属性", (tot[u"属性を作れた書類の数"], tot[u"表 F が同じ書類の数"], tot[u"attrs が違う fact の数"], tot[u"fact の数(属性を作れた書類)"]), (6, 5, 1, 6 + 25 + 6 + 6 + 6 + 4))
        want_eq(out_, u"塊 違う属性", dict((k, v) for k, v in tot[u"attrs が違う属性ごとの fact の数(重ねて数える)"].items() if v), {u"属性 name": 1})
        want_eq(out_, u"塊 組む", (tot[u"組めた書類の数"], tot[u"2 回組んで同じ書類の数"], tot[u"fact が同じ書類の数"], tot[u"鳴り方が同じ書類の数"], tot[u"タクソノミが同じ書類の数"], tot[u"全部同じ書類の数"], tot[u"包みが元と byte で同じ書類の数"]),
                (6, 5, 6, 6, 6, 6, 0))
        want_eq(out_, u"塊 混ぜ物", (tot[u"混ぜ物(期)を作れた書類の数"], tot[u"混ぜ物(期)が効いた書類の数"], tot[u"混ぜ物(置き場)を作れた書類の数"], tot[u"混ぜ物(置き場)が効いた書類の数"]), (6, 6, 1, 1))
        want_eq(out_, u"塊 紙の欄の比", (tot[u"紙の欄の比"][u"数"], tot[u"紙の欄の比"][u"分母"], tot[u"紙の欄の数"], tot[u"fact の数 × 7"]),
                (tot[u"紙の欄の数"], 7 * tot[u"fact の数(紙を作れた書類)"], sum(r[u"紙の欄の数"] for r in made), 7 * tot[u"fact の数(紙を作れた書類)"]))
        want_eq(out_, u"塊 紙の欄の項", sum(tot[u"紙の欄の数(項ごと)"].values()), tot[u"紙の欄の数"])
        want_eq(out_, u"塊 秒", [k for k in tot if k.endswith(u"秒の合計")], [u"置き場を作る命令の秒の合計", u"文脈と単位を作る命令の秒の合計", u"属性を作る命令の秒の合計", u"組む命令の秒の合計"])
        # 判定に要る数は本番の塊(2 本の後ろ)だけから
        rec = ms.assemble(per, u"c" * 64, FAKE_TOOL_INFO, 2)
        jk = [k for k in rec if k.startswith(u"予測の判定に要る数")]
        if len(jk) != 1:
            out_.append(u"判定に要る数の欄が 1 つでない")
        else:
            j = rec[jk[0]]
            prod = per[2:]
            pmade = [r for r in prod if r[u"fact の数"] is not None]
            pick = lambda tag: j[[k for k in j if k.startswith(tag + u" ")][0]]
            nh = sum(r[u"1 つずつ書く fact でない fact の数"] for r in pmade)
            hit = sum(r[u"規則が当てた fact の数"] for r in pmade)
            want_eq(out_, u"判定 XH0-1(1 つずつ書く fact を含む本番の塊)", (pick(u"XH0-1")[u"数"], pick(u"XH0-1")[u"分母"], nh == sum(r[u"fact の数"] for r in pmade) - 2), (hit, nh, True))
            cells_ = sum(r[u"決めの在る cell の数"] for r in pmade)
            hands_ = sum(r[u"1 つずつ書く fact の在る cell の数"] for r in pmade)
            exc_ = sum(r[u"例外の cell の数(元は fact が無いのに規則が付ける)"] + r[u"例外の cell の数(元は fact が在るのに規則が違う)"] for r in pmade)
            want_eq(out_, u"判定 XH0-2", (pick(u"XH0-2")[u"数"], pick(u"XH0-2")[u"分母"], hands_), (exc_, cells_ - hands_, 2))
            want_eq(out_, u"判定 XH0-3", dict(pick(u"XH0-3")), {u"書類": sum(1 for r in prod if r[u"文脈が同じ"]), u"分母": 7})
            want_eq(out_, u"判定 XH0-4", dict(pick(u"XH0-4")), {u"書類": sum(1 for r in prod if r[u"断った段"] == u"文脈と単位を作る"), u"分母": 7})
            want_eq(out_, u"判定 XH0-5", dict(pick(u"XH0-5")), {u"書類": sum(1 for r in prod if r[u"fact が同じ"]), u"分母": 7})
            want_eq(out_, u"判定 XH0-6", dict(pick(u"XH0-6")), {u"書類": sum(1 for r in prod if r[u"鳴り方が同じ"]), u"分母": 7})
            want_eq(out_, u"判定 XH0-7(書類の数と id の数が違う)", (dict(pick(u"XH0-7")), sum(r[u"元にだけ在る id の数"] or 0 for r in prod)), ({u"書類": 1, u"分母": 7}, 3))
            m8 = pick(u"XH0-8")
            want_eq(out_, u"判定 XH0-8", (dict(m8[u"期"]), dict(m8[u"置き場"])), ({u"書類": sum(1 for r in prod if r[u"混ぜ物(期)"][u"効いた"]), u"分母": sum(1 for r in prod if r[u"混ぜ物(期)"][u"作れた"])},
                                                                            {u"書類": sum(1 for r in prod if r[u"混ぜ物(置き場)"][u"効いた"]), u"分母": sum(1 for r in prod if r[u"混ぜ物(置き場)"][u"作れた"])}))
            m9 = pick(u"XH0-9")
            want_eq(out_, u"判定 XH0-9", (m9[u"分母"], m9[u"数"]), (7 * sum(r[u"fact の数"] for r in pmade), sum(r[u"紙の欄の数"] for r in pmade)))
            want_eq(out_, u"判定 XH0-10", dict(pick(u"XH0-10")), {u"書類": 0, u"分母": 7})
        # 欠陥を疑う条件
        ch = copy.deepcopy(tot)
        ch[u"断った書類の数"] = 0
        ch[u"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数"] = 0
        ch[u"置き場が同じ書類の数"] = ch[u"置き場を作れた書類の数"]
        ch[u"混ぜ物(期)を作れた書類の数"] = ch[u"文脈と単位を作れた書類の数"]
        ch[u"混ぜ物(置き場)を作れた書類の数"] = ch[u"置き場を作れた書類の数"]
        ch[u"文脈が同じ書類の数"] = ch[u"fact が同じ書類の数"]
        want_eq(out_, u"疑い 何も当たらない", ms.suspicions(ch), [])
        ch2 = copy.deepcopy(ch)
        ch2[u"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数"] = 1
        want_eq(out_, u"疑い 決めの在る cell の外に fact が 1 つ", len(ms.suspicions(ch2)), 1)
        ch2 = copy.deepcopy(ch)
        ch2[u"置き場が同じ書類の数"] = ch2[u"置き場を作れた書類の数"] - 1
        want_eq(out_, u"疑い 置き場が同じでない書類が 1 本", len(ms.suspicions(ch2)), 1)
        ch2 = copy.deepcopy(ch)
        ch2[u"例外の cell の数"] = 0
        want_eq(out_, u"疑い 例外の cell が全部 0(62 本の側だけ)", (len(ms.suspicions(ch2)), len(ms.suspicions(ch2, whole=False))), (1, 0))
        ch2 = copy.deepcopy(ch)
        ch2[u"文脈が同じ書類の数"] = ch2[u"fact が同じ書類の数"] + 1
        want_eq(out_, u"疑い 文脈が同じなのに fact が違う書類", len(ms.suspicions(ch2)), 1)
        ch2 = copy.deepcopy(ch)
        ch2[u"断った書類の数"] = 10
        want_eq(out_, u"疑い 断った書類 10 本", len(ms.suspicions(ch2)), 1)
        ch2[u"断った書類の数"] = 9
        want_eq(out_, u"疑い 断った書類 9 本は疑わない", len(ms.suspicions(ch2)), 0)
        ch2 = copy.deepcopy(ch)
        ch2[u"混ぜ物(期)を作れた書類の数"] -= 1
        want_eq(out_, u"疑い 混ぜ物(期)を作れなかった書類が 1 本", len(ms.suspicions(ch2)), 1)
        ch2 = copy.deepcopy(ch)
        ch2[u"混ぜ物(置き場)を作れた書類の数"] -= 1
        want_eq(out_, u"疑い 混ぜ物(置き場)を作れなかった書類が 1 本", len(ms.suspicions(ch2)), 1)
    return out_


def record_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        docs = os.path.join(d, "docs")
        os.makedirs(docs)
        make_docs(docs, [doc_r1(), doc_missing(), doc_ambiguous(), doc_cells()])
        os.makedirs(os.path.join(d, "tmp"))
        calls = []
        ms.check_tool = lambda *a, **k: calls.append(1) or FAKE_TOOL_INFO
        proc = inproc(ms)
        rec, secret = ms.build_record(u"tool", docs, 4, fake_runner, None, os.path.join(d, "tmp"), dev_count=1, proc=proc)
        want_eq(out_, u"build_record は道具を確かめる", len(calls), 1)
        keys = list(rec)
        if keys[:5] != [u"seal", u"封の commit", u"step", u"この script の sha256", u"材料"] or keys[5:7] != [u"書類", u"集計"] or keys[-1] != u"限界":
            out_.append(u"記録の欄の並びが違う: %s" % keys)
        want_eq(out_, u"書類の数", len(rec[u"書類"]), 4)
        want_eq(out_, u"断った段", [r[u"断った段"] for r in rec[u"書類"]], [u"", u"紙を作る", u"文脈と単位を作る", u""])
        want_eq(out_, u"script の sha256", rec[u"この script の sha256"], sha_of(SCRIPT_REL))
        want_eq(out_, u"材料", (rec[u"材料"][u"書類の本数"], rec[u"材料"][u"開発の 5 本の番号"], rec[u"材料"][u"script の決めの字"]), (4, [1], list(ms.RULES)))
        want_eq(out_, u"道具の欄", (rec[u"材料"][u"道具の版"], rec[u"材料"][u"規則の年"], rec[u"材料"][u"時間の上限(秒)"]), (u"2.47.5", ms.YEAR, ms.TIMEOUT_SEC))
        text = ms.dumps(rec)
        for t in (u"1,000", u"jppfs_cor", u"CurrentYear", u"Prior1Year", u"Mem1", u".htm", u"E9999", u"S2FAKE", u"2025-03-31", u"2024-03-31", u"SegAxis", u"ixt:", u"http://x", u"iso4217", u"JPY"):
            if t in text:
                out_.append(u"記録に禁止の字が在る: %s" % t)
        if not {u"SegAxis", u"Mem1", u"CurrentYearInstant", u"Prior1YearInstant"} <= set(secret[1]) or u"S2FAKE01" not in secret[2] or u"E99991" not in secret[3]:
            out_.append(u"secret に要素の名・文脈の名・member の名・docID・EDINET コードが入っていない")
        ms.verify_record(rec, text, 4, 1)
        mutate_cases = (
            (u"書類の数(塊)", lambda r: r[u"集計"][u"開発の 5 本"].__setitem__(u"書類の数", 2)),
            (u"書類の fact の数", lambda r: r[u"書類"][0].__setitem__(u"fact の数", 22)),
            (u"塊の fact の数", lambda r: r[u"集計"][u"開発の 5 本"].__setitem__(u"fact の数(紙を作れた書類)", 22)),
            (u"紙の欄の項", lambda r: r[u"書類"][0][u"紙の欄の数(項ごと)"].__setitem__(u"表ごとの 3", 9)),
            (u"紙の欄の合計", lambda r: r[u"書類"][0].__setitem__(u"紙の欄の数", 21)),
            (u"1 つずつ書く fact × 7", lambda r: r[u"書類"][3][u"紙の欄の数(項ごと)"].__setitem__(u"1 つずつ書く fact × 7", 8)),
            (u"1 つずつ書く fact の始まりと終わり", lambda r: r[u"書類"][3][u"紙の欄の数(項ごと)"].__setitem__(u"1 つずつ書く fact の始まりと終わり", 3)),
            (u"1 つずつ書く fact の数", lambda r: r[u"書類"][0].__setitem__(u"1 つずつ書く fact の数", 99)),
            (u"1 つずつ書く fact でない fact の数", lambda r: r[u"書類"][0].__setitem__(u"1 つずつ書く fact でない fact の数", 5)),
            (u"規則が当てた fact の数", lambda r: r[u"書類"][0].__setitem__(u"規則が当てた fact の数", 99)),
            (u"全部同じ", lambda r: r[u"書類"][0].__setitem__(u"全部同じ", False)),
            (u"表 F が同じ", lambda r: r[u"書類"][0].__setitem__(u"表 F が同じ", False)),
            (u"文脈が同じ(元にだけ在る id が在るのに同じ)", lambda r: r[u"書類"][0].__setitem__(u"元にだけ在る id の数", 1)),
            (u"文脈が同じ(文脈を作れていないのに同じ)", lambda r: r[u"書類"][2].__setitem__(u"文脈が同じ", True)),
            (u"置き場が同じ(置き場を作れていないのに同じ)", lambda r: r[u"書類"][1].__setitem__(u"置き場が同じ", True)),
            (u"番号", lambda r: r[u"書類"][2].__setitem__(u"番号", 9)),
            (u"断った理由", lambda r: r[u"書類"][1].__setitem__(u"断った理由", u"")),
            (u"断った段", lambda r: r[u"書類"][1].__setitem__(u"断った段", u"道具")),
            (u"断った書類の組めた", lambda r: r[u"書類"][1].__setitem__(u"組めた", True)),
            (u"混ぜ物(期)の形", lambda r: r[u"書類"][1][u"混ぜ物(期)"].__setitem__(u"効いた", True)),
            (u"混ぜ物(置き場)の形", lambda r: r[u"書類"][1][u"混ぜ物(置き場)"].__setitem__(u"効いた", True)),
            (u"属性の欄", lambda r: r[u"書類"][0][u"attrs が違う属性ごとの fact の数(重ねて数える)"].pop(u"属性 name")),
            (u"集計の合計", lambda r: r[u"集計"][u"全部"].__setitem__(u"表 F が同じ書類の数", 1)),
            (u"判定に要る数", lambda r: r[[k for k in r if k.startswith(u"予測の判定に要る数")][0]][[k for k in r[[k for k in r if k.startswith(u"予測の判定に要る数")][0]] if k.startswith(u"XH0-3 ")][0]].__setitem__(u"書類", 0)))
        bad = []
        for what, fn in mutate_cases:
            r2 = copy.deepcopy(rec)
            fn(r2)
            if not stops(ms, ms.verify_record, r2, None, 4, 1):
                bad.append(what)
        if bad:
            out_.append(u"verify_record が止めない: %s" % bad)
        if not stops(ms, ms.verify_record, rec, text, 67, 1):
            out_.append(u"書類が 67 本でないのに verify_record が止めない")
        rp = os.path.join(d, "rec", "r.json")
        if not stops(ms, ms.run, u"tool", docs=docs, out=rp, want=67, say=lambda *a: None, runner=fake_runner, proc=proc) or os.path.exists(rp):
            out_.append(u"67 本でないのに run が止まらない(か記録を書いた)")
        lines = []
        rec2 = ms.run(u"tool", docs=docs, out=rp, want=4, say=lambda *a: None, runner=fake_runner, tmp_root=os.path.join(d, "tmp"), dev_count=1, proc=proc, progress=lines.append)
        if not os.path.exists(rp) or ms.dumps(rec2)[:0] != u"" or len(lines) != 4:
            out_.append(u"記録が書かれていない・進みを出さない")
        want_eq(out_, u"書いた記録の検査", read_text(rp).count(u"\n") > 10, True)
        ms.check(rec_path=rp, say=lambda *a: None, want=4, dev_count=1)
        if not stops(ms, ms.run, u"tool", docs=docs, out=rp, want=4, say=lambda *a: None, runner=fake_runner, dev_count=1, proc=proc):
            out_.append(u"記録が既に在るのに run が止まらない")
        rp3 = os.path.join(d, "rec", "r3.json")
        with io.open(rp3, "w", encoding="utf-8") as fh:
            fh.write(read_text(rp).replace(u'"属性を作れた": true', u'"属性を作れた": false', 1))
        if not stops(ms, ms.check, rec_path=rp3, say=lambda *a: None, want=4, dev_count=1):
            out_.append(u"記録を書き換えたのに check が止まらない")
        if not stops(ms, ms.check, rec_path=os.path.join(d, "none.json"), say=lambda *a: None, want=4):
            out_.append(u"記録が無いのに check が止まらない")
        # 開発の入口は 5 本だけ(記録は書かない)
        docs2 = os.path.join(d, "docs2")
        os.makedirs(docs2)
        make_docs(docs2, [doc_r1()] * 7)
        out_lines = []
        before_calls = len(calls)
        per = ms.dev_run(u"tool", docs_dir=docs2, runner=fake_runner, tmp_root=os.path.join(d, "tmp"), say=out_lines.append, proc=proc)
        want_eq(out_, u"開発の入口は 5 本だけ", (len(per), sum(1 for x in out_lines if x.startswith(u"doc "))), (5, 5))
        want_eq(out_, u"dev_run は道具を確かめる", len(calls) - before_calls, 1)
        if not any(u"先に自分の欠陥を疑う場合に当たったもの" in x for x in out_lines):
            out_.append(u"欠陥を疑う場合の行を出さない")
        want_eq(out_, u"dev_docs の本数", len(ms.dev_docs(docs2, 2)), 2)
    return out_


def clean_problems(ms=None):
    ms = ms or MS
    out_ = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"断った理由", u"固定の理由"), (u"fact の数", 5)])]), (u"hash", u"a" * 64)])
    secret = (set(), {u"NetSalesOfX", u"CurrentYearInstant", u"MemberY"}, [u"zzdoc"], {u"E99991"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out_.append(u"きれいな記録で止まる")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"company", 1)])), (u"禁止の欄(element)", od([(u"element", 1)])), (u"禁止の欄(name)", od([(u"name", 1)])),
        (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])), (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])),
        (u"要素の名", od([(u"x", u"理由 NetSalesOfX")])), (u"文脈の名", od([(u"x", u"CurrentYearInstant")])), (u"member の名", od([(u"x", u"MemberY を含む")])),
        (u"日付の形", od([(u"x", u"終わりは 2025-03-31")])), (u"file の名(htm)", od([(u"x", u"0101010_honbun.htm")])), (u"file の名(xsd)", od([(u"x", u"jpcrp030000-asr-001.xsd")]))]
    for what, rec in cases:
        if not stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out_.append(u"%s が止まらない" % what)
        if not stops(ms, ms.record_text, rec, secret):
            out_.append(u"%s が record_text で止まらない" % what)
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


# ======================================================================== 6. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "io", "itertools", "json", "os", "re", "shutil", "sys", "tempfile", "time")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "adapters", "core", "audit_core", "zipfile", "csv", "xml", "subprocess")
#: 前の便の script の関数を呼ぶ(写さない): (module の名, 関数の名)
CALLED = (("S", "make_sheet_folder"), ("S", "decided_attrs"), ("S", "values_attrs"), ("S", "table_lookup"), ("S", "read_context"), ("S", "exec_attrs"), ("S", "compare_attrs"), ("S", "sheet_cells"),
          ("S", "leak_problems"), ("S", "fact_ids"), ("S", "check_tool"), ("S", "check_clean"), ("S", "doc_secret_strings"),
          ("X", "table_tokens"), ("X", "step_token"), ("X", "place_positions"), ("X", "line_keys"), ("X", "strip_tags"),
          ("W", "select_docs"), ("W", "order_sha256"), ("P", "jload"), ("P", "jdump"), ("P", "read_bytes"), ("P", "write_bytes"), ("P", "load_htm_tables"), ("P", "safe_local"), ("P", "exec_build"),
          ("P", "read_tree"), ("P", "expected_names"), ("P", "rebuilt_pack"), ("P", "decline_reason"), ("P", "run_process"), ("T", "run_package"), ("T", "compare_into"),
          ("B", "load_package"), ("B", "write_package"), ("B", "dev_docs"))
NOT_COPIED = ("select_docs", "order_sha256", "strip_text", "load_package", "is_public_htm", "mismatches", "count_facts", "mode_first", "lines_of", "line_keys", "doc_texts", "facts_of_files",
              "reads_negative", "format_class", "strip_tags", "place_positions", "pct1", "sha256_file", "sha256_bytes", "facts_of_text", "table_tokens", "context_defs", "contexts_of_text",
              "resolve_facts", "choose_combo", "sign_format_flags", "peel_tables", "write_folder", "load_htm_tables", "exec_build", "read_tree", "expected_names", "rebuilt_pack", "run_package",
              "compare_into", "run_process", "decline_reason", "jdump", "jload", "build_text", "build_main", "render_folder", "decided_attrs", "values_attrs", "table_lookup", "read_context",
              "exec_attrs", "compare_attrs", "sheet_cells", "leak_problems", "fact_ids", "make_sheet_folder", "attrs_tables", "context_index", "blank_row", "build_sheet", "write_attrs_folder",
              "attrs_main", "attrs_command", "step_token", "read_bytes", "write_bytes", "safe_local")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
#: 別の門の規準の字(関数の名・呼び出し・説明文のどこにも使わない)
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
OTHER_NAMES = (u"_xb0_inline_build_2026_11_21", u"_xt0_inline_build_2026_11_21", u"_xp0_taxonomy_build_2026_11_22", u"_xt0_taxonomy_build_2026_11_22", u"_xv0_tag_wall_2026_11_21", u"_xg1_tag_wall_2026_11_21",
               u"_xb0_tag_wall_2026_11_21", u"_xb0_tag_narrow", u"_xb0_edinet_validate_2026_11_21", u"_xa0_inline_build_2026_11_22", u"_xa1_sheet_wall_2026_11_22", u"_xs0_sheet_context_2026_11_22", u"_xs0_pack_build_2026_11_22")


def attr_names(tree):
    return [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]


def import_problems(src=None):
    u"""script の import は標準ライブラリだけ(engine・zipfile・csv・subprocess を読まない)。前の便の script は S(便 XS0)・X・P・T・B・W・A1 から呼び、写さない。"""
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
    if u"_xh0_sheet_build_2026_11_22" not in consts:
        out_.append(u"前の便の script を読む名が一意の名でない")
    if any(n in consts for n in OTHER_NAMES):
        out_.append(u"他の便と重なる名で読んでいる")
    for var, want in (("S", ("_load_sibling", None)), ("A1", ("S", "A1")), ("X", ("S", "X")), ("P", ("S", "P")), ("B", ("S", "B")), ("T", ("S", "T")), ("W", ("S", "W"))):
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
            if u".env" in n.value or u"dotenv" in n.value or u"API_KEY" in n.value or u"/private/tmp" in n.value or u"scratchpad" in n.value:
                out_.append(u"鍵・.env・scratchpad の path の字が在る")
    if u"/private/tmp" in src or u"scratchpad" in src:
        out_.append(u"scratchpad の path の字が script の中に在る")
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


def called_same_problems(ms=None):
    u"""この便の script が呼ぶ前の便の関数は、前の便の script の関数そのもの(写していない)。"""
    ms = ms or MS
    out_ = []
    for mod, fn in CALLED:
        if not callable(getattr(getattr(ms, mod, None), fn, None)):
            out_.append(u"前の便の %s.%s が無い" % (mod, fn))
    if ms.Stop is not ms.X.Stop or ms.Stop is not ms.P.Stop or ms.Stop is not ms.S.Stop or ms.Refuse is not ms.X.Refuse or ms.W is not ms.X.W or ms.W is not ms.P.W or ms.W is not ms.S.W:
        out_.append(u"Stop・Refuse・W が前の便と同じ object でない")
    return out_


# ======================================================================== 変異
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**予測は「その検査が赤になる」。** この表は実行より先に書いた。
#: 検査の名前: seal・rules・paper・blind・behaviour・measure・chunk・record・clean・wiring・called
MUTANTS = (
    # ---- 置き場の規則(約束の側から: 規則の 1 つずつ)
    (u"R1 ※の直後を数に数える", u"        if j >= 0 and m[j] == STAR:\n            continue\n", u"", ("rules",)),
    (u"R2 ※の直前の判定でタグを飛ばさない", u"        while j >= 0 and m[j] == TAG_MASK:\n            j -= 1\n", u"", ("rules",)),
    (u"R3 ※の直前の判定で文字参照も飛ばす", u"        while j >= 0 and m[j] == TAG_MASK:", u"        while j >= 0 and m[j] in (TAG_MASK, REF_MASK):", ("rules",)),
    (u"R4 文字参照を別の字に置き換えない(中の数字を数の字に読む)", u"MASK_RE = re.compile(r\"<[^>]*>|&[#A-Za-z0-9]+;\")", u"MASK_RE = re.compile(r\"<[^>]*>\")", ("rules",)),
    (u"R5 タグの中の数字を数の字に読む", u"    for mm in MASK_RE.finditer(raw):\n        c = TAG_MASK", u"    for mm in MASK_RE.finditer(raw[:0]):\n        c = TAG_MASK", ("rules",)),
    (u"R6 数字を含まない並びを数の並びに数える", u"        if not any(c in DIGITS for c in raw[s:e]):\n            continue\n", u"", ("rules",)),
    (u"R7 数の並びが 2 つ以上でも最初の 1 つに付ける", u"    if len(runs) == 1:\n        return [(runs[0][0], runs[0][1], False)]", u"    if len(runs) >= 1:\n        return [(runs[0][0], runs[0][1], False)]", ("rules", "measure", "chunk")),
    (u"R8 数の並びが 0 でも 1 つの並びを探す(最後の並びを使う)", u"    if len(runs) == 1:\n        return [(runs[0][0], runs[0][1], False)]", u"    if len(runs) >= 1 and len(runs) != 2:\n        return [(runs[0][0], runs[0][1], False)]", ("rules",)),
    (u"R9 cell の中の表を見ない", u"    if u\"<table\" in raw.lower():\n        return []\n", u"", ("rules", "measure", "chunk")),
    (u"R10 cell の中の表を大文字小文字で見分ける", u"    if u\"<table\" in raw.lower():", u"    if u\"<table\" in raw:", ("rules",)),
    (u"R11 横棒だけの cell の判定で文字参照を横棒にする", u"    vis = u\"\".join(u\" \" if c == REF_MASK else c for c in m if c != TAG_MASK).strip()", u"    vis = u\"\".join(u\"－\" if c == REF_MASK else c for c in m if c != TAG_MASK).strip()", ("rules",)),
    (u"R12 横棒だけの判定で字が 1 つでも横棒なら付ける", u"    return vis != u\"\" and all(ch in X.DASH_CHARS for ch in vis)", u"    return vis != u\"\" and any(ch in X.DASH_CHARS for ch in vis)", ("rules",)),
    (u"R13 横棒だけの判定で空の字も横棒だけに数える", u"    return vis != u\"\" and all(ch in X.DASH_CHARS for ch in vis)", u"    return all(ch in X.DASH_CHARS for ch in vis)", ("rules", "measure", "chunk")),
    (u"R14 空の fact を最初の横棒でなく最後の横棒の前に置く", u"    k = [i for i, ch in enumerate(m) if ch in X.DASH_CHARS][0]", u"    k = [i for i, ch in enumerate(m) if ch in X.DASH_CHARS][-1]", ("rules",)),
    (u"R15 空の fact を横棒の後ろに置く", u"    k = [i for i, ch in enumerate(m) if ch in X.DASH_CHARS][0]\n    while True:", u"    k = [i for i, ch in enumerate(m) if ch in X.DASH_CHARS][0] + 1\n    while True:", ("rules", "measure", "chunk")),
    (u"R16 span の前に戻らない", u"        q = SPAN_OPEN_END_RE.search(raw[:k])\n        if not q:\n            return k\n        k = q.start()", u"        return k", ("rules", "measure", "chunk")),
    (u"R17 span の前に戻るのを 1 回だけにする", u"        q = SPAN_OPEN_END_RE.search(raw[:k])\n        if not q:\n            return k\n        k = q.start()", u"        q = SPAN_OPEN_END_RE.search(raw[:k])\n        return q.start() if q else k", ("rules",)),
    (u"R18 span の開きタグに限らずどのタグの前にも戻る", u"SPAN_OPEN_END_RE = re.compile(r\"<span\\b[^>]*>\\Z\", re.I)", u"SPAN_OPEN_END_RE = re.compile(r\"<[a-z]+\\b[^>]*>\\Z\", re.I)", ("rules",)),
    (u"R19 空の fact の形を引数でなく自己閉じに固定する", u"        return [(k, k, bool(nil_self))]", u"        return [(k, k, True)]", ("rules", "measure", "chunk")),
    (u"R20 空の fact の形の最頻で並んだら組にする", u"    nil_self = empties_self >= empties_pair", u"    nil_self = empties_self > empties_pair", ("rules",)),
    (u"R21 空の fact の形の最頻に 1 つずつ書く fact の空も数える", u"            if e[\"kind\"] == \"nonFraction\" and (fi, i) not in hand_set and e[\"end\"] == e[\"start\"]:", u"            if e[\"kind\"] == \"nonFraction\" and e[\"end\"] == e[\"start\"]:", ("rules",)),
    (u"R22 空の fact の形の最頻を数えず先頭の空の fact で決める", u"    nil_self = empties_self >= empties_pair", u"    nil_self = True", ("rules",)),
    (u"R23 決めの在る cell の判定で終わりの日の決めを見ない", u"    return el is not None and el[0] is not None and endv is not None and memv is not None", u"    return el is not None and el[0] is not None and memv is not None", ("rules",)),
    (u"R24 決めの在る cell の判定で member の組の決めを見ない", u"    return el is not None and el[0] is not None and endv is not None and memv is not None", u"    return el is not None and el[0] is not None and endv is not None", ("rules",)),
    (u"R25 決めの在る cell の判定で name の決めを見ない", u"    return el is not None and el[0] is not None and endv is not None and memv is not None", u"    return el is not None and endv is not None and memv is not None", ("rules",)),
    (u"R26 決めの在る cell の判定で向きを見ない(いつも A)", u"    e, c = X.line_keys({\"row\": r, \"col\": col}, ts[\"orient\"])", u"    e, c = X.line_keys({\"row\": r, \"col\": col}, \"A\")", ("rules",)),
    (u"R27 1 つずつ書く fact の在る cell にも規則を当てる", u"        if key in hand_cells:\n            continue\n", u"", ("rules", "measure", "chunk")),
    (u"R28 例外の cell を無視して規則を当てる", u"        if key in exc:\n            out.extend(exc[key])\n            continue\n", u"", ("rules", "measure", "chunk")),
    (u"R29 例外の cell の fact の置き場を足さない(規則も当てない)", u"            out.extend(exc[key])\n", u"            pass\n", ("rules", "measure", "chunk")),
    (u"R30 1 つずつ書く fact の置き場を足さない", u"    out = list(hand)\n    hs =", u"    out = []\n    hs =", ("rules", "measure", "chunk")),
    (u"R31 1 つずつ書く fact の在る cell を hand の始まりでなく終わりで引く", u"    hs = sorted(set(s for s, _e, _x in hand))", u"    hs = sorted(set(e for _s, e, _x in hand))", ("rules",)),
    (u"R32 決めの無い cell にも規則を当てる", u"        if not decided_cell(tabs.get((fi, t)), r, col):\n            continue\n", u"", ("rules", "measure", "chunk")),
    (u"R33 置き場を start の昇順に並べない", u"    out.sort(key=lambda p: (p[0], p[1]))", u"    out.sort(key=lambda p: (p[1], p[0]), reverse=True)", ("rules", "measure", "chunk")),
    (u"R34 規則が置いた空の fact を数えない", u"            if s == e:\n                rule_empty.add((oe + s, oe + e))", u"            if False:\n                rule_empty.add((oe + s, oe + e))", ("rules", "measure", "chunk")),
    # ---- 行の並び・parent・before
    (u"P1 同じ start で数の fact を先に置く", u"                take_c = last is not None", u"                take_c = False", ("rules", "measure")),
    (u"P2 同じ start で持ち込みの行を先に置く", u"                take_c = last is not None", u"                take_c = True", ("rules",)),
    (u"P3 自己閉じの行も囲む行にする", u"    return (not row[\"self\"]) and row[\"start\"] <= s and e <= row[\"end\"]", u"    return row[\"start\"] <= s and e <= row[\"end\"]", ("rules",)),
    (u"P4 囲む行を start が数の fact の start と同じ行に限る", u"    return (not row[\"self\"]) and row[\"start\"] <= s and e <= row[\"end\"]", u"    return (not row[\"self\"]) and row[\"start\"] == s and e <= row[\"end\"]", ("rules",)),
    (u"P5 囲む行を end が数の fact の end 以上でなく end より大きい行に限る", u"    return (not row[\"self\"]) and row[\"start\"] <= s and e <= row[\"end\"]", u"    return (not row[\"self\"]) and row[\"start\"] <= s and e < row[\"end\"]", ("rules",)),
    (u"P6 parent を囲む最も内側でなく最も外側の行にする", u"            while stack and not encloses(carried[stack[-1]], s, e):\n                stack.pop()\n            pending.append(stack[-1] if stack else -1)", u"            while stack and not encloses(carried[stack[-1]], s, e):\n                stack.pop()\n            pending.append(stack[0] if stack else -1)", ("rules", "measure")),
    (u"P7 parent を持ち込みの行に付けず -1 にする", u"            pending.append(stack[-1] if stack else -1)", u"            pending.append(-1)", ("rules", "measure")),
    (u"P8 閉じた行を積みから外さない", u"            while stack and not encloses(carried[stack[-1]], s, e):\n                stack.pop()\n", u"", ("rules", "measure")),
    (u"P9 持ち込みの行の parent を付け直さない", u"            row[\"parent\"] = new_index[carried[i][\"parent\"]] if carried[i][\"parent\"] >= 0 else -1", u"            row[\"parent\"] = carried[i][\"parent\"]", ("rules", "measure")),
    (u"P10 before を持ち込みの行の数のままにする", u"    return sum(1 for k, i in order if (k == u\"c\" and i < cb) or (k == u\"n\" and numbers[i][0] < pos))", u"    return cb", ("rules",)),
    (u"P11 before に数の fact を数えない", u"    return sum(1 for k, i in order if (k == u\"c\" and i < cb) or (k == u\"n\" and numbers[i][0] < pos))", u"    return sum(1 for k, i in order if k == u\"c\" and i < cb)", ("rules",)),
    (u"P12 before の数の fact を start が位置以下で数える", u"(k == u\"n\" and numbers[i][0] < pos))", u"(k == u\"n\" and numbers[i][0] <= pos))", ("rules",)),
    (u"P13 持ち込みの表 H の before を直さない", u"            H2[\"before\"] = sum(1 for i in range(H[\"before\"]) if F[i][\"kind\"] != \"nonFraction\")", u"            H2[\"before\"] = H[\"before\"]", ("paper",)),
    (u"P14 持ち込みの表 F に数の fact の行を残す", u"            if e[\"kind\"] == \"nonFraction\":\n                continue\n            cmap[i] = len(rows)", u"            cmap[i] = len(rows)", ("paper", "measure")),
    (u"P15 持ち込みの表 H に文脈を残す", u"            H2[\"resources\"] = [r for r in H[\"resources\"] if r.get(\"type\") == \"ref\"]", u"            H2[\"resources\"] = list(H[\"resources\"])", ("paper", "measure")),
    (u"P16 持ち込みの表 H から参照も除く", u"            H2[\"resources\"] = [r for r in H[\"resources\"] if r.get(\"type\") == \"ref\"]", u"            H2[\"resources\"] = []", ("paper",)),
    # ---- 紙 2 を作る(例外の cell の決め方)
    (u"E1 例外の cell を作らない", u"            if pred == tr:\n                st[u\"規則が当てた fact\"] += len(tr)\n            else:", u"            if True:\n                st[u\"規則が当てた fact\"] += len(tr)\n            if False:", ("rules", "measure", "chunk")),
    (u"E2 例外の cell を 1 つずつ書く fact の在る cell も含めて全部の cell に書く", u"            if pred == tr:", u"            if False:", ("rules", "paper", "measure", "chunk")),
    (u"E3 例外の cell の fact を書かない", u"                exc_rows.append([fi, t, r, col, [list(x) for x in tr]])\n        for key, tr in truth.items():", u"                exc_rows.append([fi, t, r, col, []])\n        for key, tr in truth.items():", ("rules", "paper", "measure", "chunk")),
    (u"E4 例外の cell の比べに自己閉じの印を入れない", u"            pred = sorted((oe + s, oe + e, sf) for s, e, sf in predict_cell(plain[oe:cs], nil_self))", u"            pred = sorted((oe + s, oe + e, False) for s, e, sf in predict_cell(plain[oe:cs], nil_self))", ("rules",)),
    (u"E5 元の 1 つずつ書く fact を hand に書かない", u"                hand_rows.append([fi, e[\"start\"], e[\"end\"], bool(e[\"self\"])])\n", u"                pass\n", ("rules", "measure", "chunk")),
    (u"E6 hand の印を全部の fact に付ける", u"            if (fi, i) in hand_set:\n                hand_rows.append", u"            if True:\n                hand_rows.append", ("rules", "paper", "measure", "chunk")),
    (u"E7 決めの在る cell を数えない", u"            if ts:\n                st[u\"決めの在る cell\"] += 1", u"            if False:\n                st[u\"決めの在る cell\"] += 1", ("rules", "measure", "chunk")),
    (u"E8 規則が当てた fact を cell の数で数える", u"                st[u\"規則が当てた fact\"] += len(tr)", u"                st[u\"規則が当てた fact\"] += 1", ("rules", "measure", "chunk")),
    (u"E9 例外を付ける・違うに分けず全部違うにする", u"                st[u\"例外 付ける\" if not tr else u\"例外 違う\"] += 1", u"                st[u\"例外 違う\"] += 1", ("rules", "measure", "chunk")),
    (u"E10 決めの在る cell の外の fact を数えない", u"                    st[u\"決めの在る cell の外の fact\"] += len(tr)\n                    exc_rows.append([fi, t, r, col, [list(x) for x in tr]])\n                continue", u"                    exc_rows.append([fi, t, r, col, [list(x) for x in tr]])\n                continue", ("rules",)),
    # ---- 紙 2 を作る(文脈・単位・表)
    (u"T1 期の表を作らない", u"        periods.setdefault(nm, [list(x) for x in r[\"period\"]])", u"        pass", ("rules", "paper", "measure", "chunk")),
    (u"T2 member の表を作らない", u"            members.setdefault(m, d)", u"            pass", ("rules", "paper", "measure", "chunk")),
    (u"T3 member の軸を最後の定義で決める", u"            members.setdefault(m, d)", u"            members[m] = d", ("rules",)),
    (u"T4 単位の表を作らない", u"                units.append(od([(\"id\", r[\"id\"]), (\"measures\", list(r[\"measures\"])), (\"divide\", r[\"divide\"])]))", u"                pass", ("rules", "paper", "measure", "chunk")),
    (u"T5 scheme を書かない", u"(\"scheme\", defs[0][\"scheme\"] if defs else None)", u"(\"scheme\", None)", ("rules",)),
    (u"T6 識別子を書かない", u"(\"ident\", defs[0][\"ident\"] if defs else None)", u"(\"ident\", None)", ("rules",)),
    (u"T7 id を分けられない定義も期の表に載せる(最初の _ まで)", u"    return None\n\n\ndef make_paper2", u"    return row[\"id\"].split(u\"_\")[0]\n\n\ndef make_paper2", ("rules",)),
    (u"T8 id の分けに連結個別の軸を先にした並びを試さない", u"    orders = [list(members), [x for x in members if is_cnc(x[0])] + [x for x in members if not is_cnc(x[0])]]", u"    orders = [list(members)]", ("rules",)),
    (u"T9 id の分けに並べ替えを試さない", u"    if 1 < len(members) <= 3:", u"    if False:", ("rules",)),
    (u"T10 期の名の判定で id が member の字だけでもよい", u"        if row[\"id\"].endswith(suffix) and len(row[\"id\"]) > len(suffix):", u"        if row[\"id\"].endswith(suffix):", ("rules",)),
    (u"T11 紙 2 の欄に期の表の日付を数えない", u"    out[u\"期の表\"] = sum(1 + sum(1 for _tag, val in per if val != u\"\") for _n, per in p2[\"periods\"])", u"    out[u\"期の表\"] = sum(1 for _n, per in p2[\"periods\"])", ("rules", "paper")),
    (u"T12 紙 2 の欄で 1 つずつ書く fact を 1 で数える", u"    out[u\"1 つずつ書く fact の始まりと終わり\"] = CELLS_PER_HAND_PLACE * len(p2[\"hand\"])", u"    out[u\"1 つずつ書く fact の始まりと終わり\"] = len(p2[\"hand\"])", ("rules", "paper")),
    (u"T13 紙 2 の欄で例外の cell の中の fact を数えない", u"    out[u\"例外の cell の中の fact の始まりと終わり\"] = CELLS_PER_EXC_FACT * sum(len(x[4]) for x in p2[\"exceptions\"])", u"    out[u\"例外の cell の中の fact の始まりと終わり\"] = 0", ("rules", "paper")),
    (u"T14 紙 2 の欄で member を 1 で数える", u"    out[u\"member の表\"] = CELLS_PER_MEMBER * len(p2[\"members\"])", u"    out[u\"member の表\"] = len(p2[\"members\"])", ("rules",)),
    (u"T15 紙 2 の欄の式の数(例外の fact)を変える", u"CELLS_PER_EXC_FACT = 2 ", u"CELLS_PER_EXC_FACT = 3 ", ("seal", "rules", "paper")),
    (u"T16 紙 2 の欄の式の数(member)を変える", u"CELLS_PER_MEMBER = 2 ", u"CELLS_PER_MEMBER = 1 ", ("seal", "rules")),
    (u"T17 紙 2 の欄の式の数(単位)を変える", u"CELLS_PER_UNIT = 2 ", u"CELLS_PER_UNIT = 3 ", ("seal", "rules", "paper")),
    # ---- 文脈と単位を作る(答えを読まない側)
    (u"C1 member の字をいつも local name にする", u"    return local if prefix.endswith(COR_SUFFIX) else prefix + local", u"    return local", ("rules", "measure")),
    (u"C2 member の字をいつも接頭辞つきにする", u"    return local if prefix.endswith(COR_SUFFIX) else prefix + local", u"    return prefix + local", ("rules", "measure")),
    (u"C3 member の字の _cor 判定を前方一致にする", u"    return local if prefix.endswith(COR_SUFFIX) else prefix + local", u"    return local if prefix.startswith(COR_SUFFIX) else prefix + local", ("rules", "measure")),
    (u"C4 連結個別の軸を先にしない", u"    first = [x for x in mem if is_cnc(x[0])]\n    rest = [x for x in mem if not is_cnc(x[0])]", u"    first = []\n    rest = list(mem)", ("rules", "measure")),
    (u"C5 連結個別の軸を最後にする", u"    return names[0] + u\"\".join(u\"_\" + token_of(m) for _d, m in first + rest)", u"    return names[0] + u\"\".join(u\"_\" + token_of(m) for _d, m in rest + first)", ("rules", "measure")),
    (u"C6 連結個別の軸の判定を全字一致にする", u"    return dim.split(u\":\")[-1] == CNC_AXIS", u"    return dim == CNC_AXIS", ("rules",)),
    (u"C7 連結個別の軸の判定に接頭辞を含める", u"    return dim.split(u\":\")[-1] == CNC_AXIS", u"    return dim.split(u\":\")[0] == CNC_AXIS", ("rules", "measure")),
    (u"C8 期の名が 2 つでも先の名を使う", u"    if len(names) != 1:\n        raise Refuse(R_PERIOD)\n    first", u"    if len(names) < 1:\n        raise Refuse(R_PERIOD)\n    first", ("rules",)),
    (u"C9 期の名が無くても断らない", u"    if len(names) != 1:\n        raise Refuse(R_PERIOD)\n    first", u"    names = names or [u\"\"]\n    if len(names) != 1:\n        raise Refuse(R_PERIOD)\n    first", ("rules", "paper")),
    (u"C10 id の分け方が 2 通りでも先の分けを使う", u"        if len(sp) != 1:\n            raise Refuse(R_SPLIT)\n        parsed[cid] = sp[0]", u"        if len(sp) < 1:\n            raise Refuse(R_SPLIT)\n        parsed[cid] = sp[0]", ("rules",)),
    (u"C11 id の分け方が 0 通りでも断らない", u"        if len(sp) != 1:\n            raise Refuse(R_SPLIT)\n        parsed[cid] = sp[0]", u"        if len(sp) != 1:\n            sp = [(names[0], [])]\n        parsed[cid] = sp[0]", ("rules", "paper", "measure")),
    (u"C12 id の分けで 2 通り目を探さない(1 つ見つけたら止める)", u"        if len(out) >= 2:\n            return\n", u"        if len(out) >= 1:\n            return\n", ("rules",)),
    (u"C13 id の分けで期の名を頭で合わせない", u"        if nm and cid.startswith(nm):", u"        if nm and nm in cid:", ("rules",)),
    (u"C14 id の分けで同じ token の member を 1 つしか見ない", u"                for mem in by_token[tok]:", u"                for mem in by_token[tok][:1]:", ("rules",)),
    (u"C15 id の分けで _ を見ない", u"            if tok and rest.startswith(u\"_\" + tok):", u"            if tok and rest.startswith(tok):", ("rules",)),
    (u"C16 id の分けで token が残りの字の頭に合えばよい(尻を見ない)", u"        if rest == u\"\":\n            out.append((name, list(acc)))\n            return", u"        if rest == u\"\" or acc:\n            out.append((name, list(acc)))\n            return", ("rules",)),
    (u"C17 期の表の引きに終わりの日の空白を落とさない", u"        _i, (kind, end, _m) = S.read_context({\"id\": name, \"period\": per, \"members\": []})", u"        kind, end = (S.A1.KIND_INSTANT, per[0][1]) if per[0][0] == \"xbrli:instant\" else S.read_context({\"id\": name, \"period\": per, \"members\": []})[1][:2]", ("rules",)),
    (u"C18 要る id の集まりに (ア) を入れない", u"                add(cid, u\"ア\")", u"                pass", ("rules", "measure", "chunk")),
    (u"C19 要る id の集まりに (イ) を入れない", u"                add(cid, u\"イ\")", u"                pass", ("rules", "measure")),
    (u"C20 要る id の集まりに (ウ) の持ち込みの文の fact を入れない", u"            if e[\"kind\"] != \"nonFraction\":\n                add(e[\"attrs\"].get(\"contextRef\"), u\"ウ\")", u"            pass", ("rules", "measure")),
    (u"C21 要る id の集まりに (ウ) の見えない fact を入れない", u"            for h in H[\"hidden\"]:\n                add(h[\"attrs\"].get(\"contextRef\"), u\"ウ\")", u"            pass", ("rules", "measure")),
    (u"C22 使われない定義も全部出す", u"    ids, per_fact = needed_ids(files, sheet, pm)", u"    ids, per_fact = needed_ids(files, sheet, pm)\n    for nm_ in [n for n, _p in periods]:\n        ids.setdefault(nm_, set()).add(u\"ア\")", ("rules", "measure", "chunk")),
    (u"C23 出す文脈の並びを期の表の並びでなく id の字の順にする", u"    for nm in names:\n        for cid in sorted(c for c, (n, _m) in parsed.items() if n == nm):", u"    for nm in [None]:\n        for cid in sorted(c for c, (n, _m) in parsed.items()):", ("rules", "chunk")),
    (u"C24 同じ期の名の中の並びを id の字の順にしない", u"        for cid in sorted(c for c, (n, _m) in parsed.items() if n == nm):", u"        for cid in reversed(sorted(c for c, (n, _m) in parsed.items() if n == nm)):", ("rules",)),
    (u"C25 has_scenario を常に偽にする", u"(\"has_scenario\", len(mems) >= 1)", u"(\"has_scenario\", False)", ("rules", "measure")),
    (u"C26 has_scenario を常に真にする", u"(\"has_scenario\", len(mems) >= 1)", u"(\"has_scenario\", True)", ("rules", "measure")),
    (u"C27 member の軸を取り違える(軸の表を引かず軸を空にする)", u"(\"members\", [[axis_of[m], m] for m in mems])", u"(\"members\", [[u\"\", m] for m in mems])", ("rules", "measure")),
    (u"C28 member の並びを id の並びでなく逆にする", u"(\"members\", [[axis_of[m], m] for m in mems])", u"(\"members\", [[axis_of[m], m] for m in reversed(mems)])", ("rules",)),
    (u"C29 scheme を紙 2 でなく固定の字にする", u"(\"scheme\", p2[\"scheme\"])", u"(\"scheme\", u\"http://x\")", ("paper",)),
    (u"C30 識別子を紙 2 でなく固定の字にする", u"(\"ident\", p2[\"ident\"])", u"(\"ident\", u\"E0\")", ("paper",)),
    (u"C31 出す定義の期を紙 2 の期の表でなく最初の期にする", u"            per = (overlay or {}).get(nm, per_of[nm])", u"            per = (overlay or {}).get(nm, periods[0][1])", ("rules", "paper", "measure")),
    (u"C32 混ぜ物の overlay を無視する", u"            per = (overlay or {}).get(nm, per_of[nm])", u"            per = per_of[nm]", ("rules", "measure", "chunk")),
    (u"C33 単位を出さない", u"    unit_rows = [od([(\"type\", \"unit\"), (\"id\", u[\"id\"]), (\"measures\", list(u[\"measures\"])), (\"divide\", u[\"divide\"])]) for u in p2[\"units\"]]", u"    unit_rows = []", ("rules", "paper", "measure", "chunk")),
    (u"C34 単位の割り算を落とす", u"(\"measures\", list(u[\"measures\"])), (\"divide\", u[\"divide\"])]) for u in p2[\"units\"]]", u"(\"measures\", list(u[\"measures\"])), (\"divide\", None)]) for u in p2[\"units\"]]", ("measure",)),
    (u"C35 参照の行を出さない", u"    rows = [r for r in files[hi[0]][3][\"resources\"] if r.get(\"type\") == \"ref\"]", u"    rows = []", ("rules",)),
    (u"C36 文脈を最初の表 H でなく最後の表 H に入れる", u"    resources, info = context_resources(files, sheet, p2, overlay)\n    out = []\n    for fi, (name, plain, F, H) in enumerate(files):\n        if fi == info[\"hi\"]:", u"    resources, info = context_resources(files, sheet, p2, overlay)\n    out = []\n    for fi, (name, plain, F, H) in enumerate(files):\n        if H is not None and fi == max(i for i, f in enumerate(files) if f[3] is not None):", ("rules",)),
    (u"C37 表 H が無い書類で断らない", u"    if not hi:\n        raise Refuse(R_NOHDR)", u"    if not hi:\n        hi = [0]", ("paper",)),
    (u"C38 (ア) の id を引く前に 1 つずつ書く fact も (ア) にする", u"                cid = S.values_attrs(row).get(\"contextRef\")\n                add(cid, u\"イ\")", u"                cid = S.values_attrs(row).get(\"contextRef\")\n                add(cid, u\"ア\")", ("rules",)),
    (u"C39 数の fact ごとの id の並びを取らない", u"            per_fact.append(cid)", u"            pass", ("rules", "measure", "chunk")),
    # ---- 答えを読まない 2 つの命令
    (u"B1 置き場を作る命令が元の包みを読める(zip_path を受ける)", u"def place_tables(folder):", u"def place_tables(folder, zip_path=None):", ("blind",)),
    (u"B2 文脈と単位を作る命令が元の包みを読める(entries を受ける)", u"def context_tables(folder, overlay=None):", u"def context_tables(folder, overlay=None, entries=None):", ("blind",)),
    (u"B3 置き場を作る命令が元の fact を読む関数を呼ぶ", u"    index, sheet, p2, files = read_paper_folder(folder)\n    tabs = S.table_lookup(sheet)\n    nil_self", u"    index, sheet, p2, files = read_paper_folder(folder)\n    X.doc_texts(folder)\n    tabs = S.table_lookup(sheet)\n    nil_self", ("blind",)),
    (u"B4 文脈と単位を作る命令が紙 2 を作る関数を呼ぶ", u"    index, sheet, p2, files = read_paper_folder(folder)\n    resources, info", u"    index, sheet, p2, files = read_paper_folder(folder)\n    make_paper2(files, [], [], sheet)\n    resources, info", ("blind",)),
    (u"B5 紙 2 の読みが数の fact の元の行を読む(measure_one を呼ぶ)", u"def read_paper_folder(folder):\n    u\"\"\"紙の folder(または置いた folder)→ (目次, 紙, 紙 2, [(名, 素の本文, 表 F, 表 H)])。読めなければ ``Refuse``。\"\"\"\n    try:", u"def read_paper_folder(folder):\n    u\"\"\"紙の folder(または置いた folder)→ (目次, 紙, 紙 2, [(名, 素の本文, 表 F, 表 H)])。読めなければ ``Refuse``。\"\"\"\n    measure_one\n    try:", ("blind",)),
    (u"B6 step_main が引数の数を見ない", u"    if len(args) != 2:\n        print(usage, file=sys.stderr)", u"    if len(args) < 1:\n        print(usage, file=sys.stderr)", ("behaviour", "blind")),
    (u"B7 place の命令を -I なしで呼ぶ", u"    return [sys.executable, \"-I\", SCRIPT_PATH, name, folder, out]", u"    return [sys.executable, SCRIPT_PATH, name, folder, out]", ("behaviour", "blind")),
    (u"B8 context の命令の名を替える", u"def context_command(folder, out):\n    return step_command(\"context\", folder, out)", u"def context_command(folder, out):\n    return step_command(\"contexts\", folder, out)", ("behaviour", "blind")),
    (u"B9 命令の断りを 1 にする", u"    except (Refuse, P.Refuse) as exc:\n        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)\n        return EXIT_DECLINE\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef place_main", u"    except (Refuse, P.Refuse) as exc:\n        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)\n        return EXIT_ERROR\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef place_main", ("behaviour",)),
    (u"B10 main が place を別の入口に渡さない", u"    if argv and argv[0] == \"place\":\n        sys.exit(place_main(argv[1:]))\n", u"", ("blind",)),
    (u"B11 出す folder に紙 2 を写さない(file を絞る)", u"    for fn in sorted(os.listdir(folder)):\n        path = os.path.join(folder, fn)\n        if os.path.isfile(path):", u"    for fn in sorted(os.listdir(folder)):\n        path = os.path.join(folder, fn)\n        if os.path.isfile(path) and fn != PAPER2_FILE:", ("behaviour", "measure", "chunk")),
    (u"B12 置いた folder の表を替えず写す(置き場を書かない)", u"    index, _sheet, _p2, files, _e = place_tables(folder)\n    copy_folder(folder, out, tables_bytes(index, files))", u"    index, _sheet, _p2, files, _e = place_tables(folder)\n    copy_folder(folder, out, {})", ("rules", "measure", "chunk")),
    (u"B13 出した folder の表を替えず写す(文脈を書かない)", u"    index, files, _info = context_tables(folder)\n    copy_folder(folder, out, tables_bytes(index, files))", u"    index, files, _info = context_tables(folder)\n    copy_folder(folder, out, {})", ("measure", "chunk", "paper")),
    # ---- 比べ方・混ぜ物
    (u"M1 置き場の比べ方が parent を見ない", u"    return [[(e[\"start\"], e[\"end\"], bool(e[\"self\"]), e[\"parent\"]) for e in F if e[\"kind\"] == \"nonFraction\"] for _n, _p, F, _h in files]", u"    return [[(e[\"start\"], e[\"end\"], bool(e[\"self\"])) for e in F if e[\"kind\"] == \"nonFraction\"] for _n, _p, F, _h in files]", ("measure",)),
    (u"M2 置き場の比べ方が自己閉じを見ない", u"    return [[(e[\"start\"], e[\"end\"], bool(e[\"self\"]), e[\"parent\"]) for e in F if e[\"kind\"] == \"nonFraction\"] for _n, _p, F, _h in files]", u"    return [[(e[\"start\"], e[\"end\"], e[\"parent\"]) for e in F if e[\"kind\"] == \"nonFraction\"] for _n, _p, F, _h in files]", ("measure",)),
    (u"M3 置き場の比べ方が end を見ない", u"    return [[(e[\"start\"], e[\"end\"], bool(e[\"self\"]), e[\"parent\"]) for e in F if e[\"kind\"] == \"nonFraction\"] for _n, _p, F, _h in files]", u"    return [[(e[\"start\"], bool(e[\"self\"]), e[\"parent\"]) for e in F if e[\"kind\"] == \"nonFraction\"] for _n, _p, F, _h in files]", ("measure",)),
    (u"M4 全部の行の比べ方が kind を見ない", u"[([(e[\"kind\"], bool(e[\"self\"]), e[\"start\"], e[\"end\"], e[\"parent\"]) for e in F],", u"[([(bool(e[\"self\"]), e[\"start\"], e[\"end\"], e[\"parent\"]) for e in F],", ("measure",)),
    (u"M20 全部の行の比べ方が頭の部の位置を見ない", u"None if H is None else (H[\"before\"], H[\"pos\"])", u"None", ("measure",)),
    (u"M5 定義の比べ方が scheme を見ない", u"            defs[r[\"id\"]] = (r[\"scheme\"], r[\"ident\"],", u"            defs[r[\"id\"]] = (r[\"ident\"],", ("measure",)),
    (u"M6 定義の比べ方が識別子を見ない", u"            defs[r[\"id\"]] = (r[\"scheme\"], r[\"ident\"],", u"            defs[r[\"id\"]] = (r[\"scheme\"],", ("measure",)),
    (u"M7 定義の比べ方が has_scenario を見ない", u"frozenset((d or u\"\", m) for d, m in r[\"members\"]), bool(r[\"has_scenario\"]))", u"frozenset((d or u\"\", m) for d, m in r[\"members\"]))", ("measure",)),
    (u"M8 定義の比べ方が軸を見ない(member だけ)", u"frozenset((d or u\"\", m) for d, m in r[\"members\"]), bool(r[\"has_scenario\"]))", u"frozenset(m for d, m in r[\"members\"]), bool(r[\"has_scenario\"]))", ("measure",)),
    (u"M9 定義の比べ方が期を見ない", u"tuple(tuple(x) for x in r[\"period\"]), frozenset", u"(), frozenset", ("measure",)),
    (u"M10 定義の比べ方が member の並びを見る(文脈が同じに使う)", u"            defs[r[\"id\"]] = (r[\"scheme\"], r[\"ident\"], tuple(tuple(x) for x in r[\"period\"]), frozenset((d or u\"\", m) for d, m in r[\"members\"]), bool(r[\"has_scenario\"]))", u"            defs[r[\"id\"]] = (r[\"scheme\"], r[\"ident\"], tuple(tuple(x) for x in r[\"period\"]), tuple((d or u\"\", m) for d, m in r[\"members\"]), bool(r[\"has_scenario\"]))", ("measure",)),
    (u"M11 定義の比べ方で元にだけ在る id を見ない", u"(u\"文脈が同じ\", differ == 0 and only_a == 0 and only_b == 0)", u"(u\"文脈が同じ\", differ == 0 and only_b == 0)", ("measure",)),
    (u"M12 定義の比べ方で作った側にだけ在る id を見ない", u"(u\"文脈が同じ\", differ == 0 and only_a == 0 and only_b == 0)", u"(u\"文脈が同じ\", differ == 0 and only_a == 0)", ("measure",)),
    (u"M13 定義の比べ方で中身の違いを見ない", u"(u\"文脈が同じ\", differ == 0 and only_a == 0 and only_b == 0)", u"(u\"文脈が同じ\", only_a == 0 and only_b == 0)", ("measure",)),
    (u"M14 単位の比べ方が割り算を見ない", u"                out[r[\"id\"]] = (tuple(r[\"measures\"]), None if dv is None else (tuple(dv[\"num\"]), tuple(dv[\"den\"])))", u"                out[r[\"id\"]] = (tuple(r[\"measures\"]), None)", ("measure",)),
    (u"M15 単位の比べ方が測度を見ない", u"                out[r[\"id\"]] = (tuple(r[\"measures\"]), None if dv is None else (tuple(dv[\"num\"]), tuple(dv[\"den\"])))", u"                out[r[\"id\"]] = ((), None if dv is None else (tuple(dv[\"num\"]), tuple(dv[\"den\"])))", ("measure",)),
    (u"M16 定義の並びまで同じが並びを見ない", u"(u\"並びまで同じ\", a_order == b_order and all(a_mem[i] == b_mem[i] for i in a_order) and a == b)", u"(u\"並びまで同じ\", a == b)", ("measure",)),
    (u"M17 定義の並びまで同じが member の並びを見ない", u"(u\"並びまで同じ\", a_order == b_order and all(a_mem[i] == b_mem[i] for i in a_order) and a == b)", u"(u\"並びまで同じ\", a_order == b_order and a == b)", ("measure",)),
    (u"M18 byte の比べ方が名の有無を見ない", u"    return all((P.PUBLICDOC + rel) in orig and orig[P.PUBLICDOC + rel] == data for rel, data in tree.items())", u"    return all(orig.get(P.PUBLICDOC + rel, data) == data for rel, data in tree.items())", ("measure",)),
    (u"M19 byte の比べ方が中身を見ない", u"    return all((P.PUBLICDOC + rel) in orig and orig[P.PUBLICDOC + rel] == data for rel, data in tree.items())", u"    return all((P.PUBLICDOC + rel) in orig for rel, data in tree.items())", ("measure",)),
    (u"X1 混ぜ物(期)が日付を替えない", u"        return [[per[0][0], MIX_DATE]]", u"        return [[per[0][0], per[0][1]]]", ("rules", "measure", "chunk")),
    (u"X2 混ぜ物(期)の当て先が 1 つの fact だけの期の名でもよい", u"        if counts[name] >= 2 and period_change(per) is not None:", u"        if counts[name] >= 1 and period_change(per) is not None:", ("rules",)),
    (u"X3 混ぜ物(期)の当て先を最後の期の名にする", u"    for name, per in info[\"periods\"]:\n        if counts[name] >= 2", u"    for name, per in reversed(info[\"periods\"]):\n        if counts[name] >= 2", ("rules",)),
    (u"X4 混ぜ物(期)がほかの定義の変化を見ない", u"        elif ra != rb:\n            return True, False\n    for fi", u"        elif False:\n            return True, False\n    for fi", ("rules",)),
    (u"X5 混ぜ物(期)で当て先の定義が変わったかを確かめない", u"            if rb != want or ra[\"period\"] == rb[\"period\"]:", u"            if rb != want:", ("rules",)),
    (u"X6 混ぜ物(期)の効いたを常に真にする", u"    return True, changed >= 1\n\n\ndef mix_place_effect", u"    return True, True\n\n\ndef mix_place_effect", ("rules",)),
    (u"X7 混ぜ物(期)を作れなかった書類も作れたに数える", u"    if target is None:\n        return False, False\n    try:\n        _ix2, mixed, _i2 = context_tables(folder, {target[0]: target[1]})", u"    if target is None:\n        return True, False\n    try:\n        _ix2, mixed, _i2 = context_tables(folder, {target[0]: target[1]})", ("rules",)),
    (u"X8 混ぜ物(期)が表 H の無い file の変化を見ない", u"        if fi != info[\"hi\"] and (F != F2 or H != H2):\n            return True, False", u"        if False:\n            return True, False", ("rules",)),
    (u"X9 混ぜ物(置き場)が形を逆にしない", u"    flipped[\"nil_form\"] = u\"pair\" if p2[\"nil_form\"] == u\"self\" else u\"self\"", u"    flipped[\"nil_form\"] = p2[\"nil_form\"]", ("rules", "measure", "chunk")),
    (u"X10 混ぜ物(置き場)で変わる行が自己閉じの印だけかを確かめない", u"                if e2 != want:\n                    return True, False\n                flips += 1", u"                flips += 1", ("rules",)),
    (u"X11 混ぜ物(置き場)がほかの行の変化を見ない", u"            elif e != e2:\n                return True, False\n    return True, flips", u"            elif False:\n                return True, False\n    return True, flips", ("rules",)),
    (u"X12 混ぜ物(置き場)で表 H の変化を見ない", u"        if len(F) != len(F2) or H != H2:\n            return True, False", u"        if len(F) != len(F2):\n            return True, False", ("rules",)),
    (u"X13 混ぜ物(置き場)を作れなかった書類も作れたに数える", u"    if sum(len(x) for x in empties) == 0:\n        return False, False", u"    if sum(len(x) for x in empties) == 0:\n        return True, False", ("rules",)),
    (u"X14 混ぜ物(置き場)の効いたを常に真にする", u"    return True, flips == sum(len(x) for x in empties)", u"    return True, True", ("rules",)),
    (u"X15 混ぜ物の日付の字を変える", u"MIX_DATE = \"1900-01-01\"", u"MIX_DATE = \"1900-01-02\"", ("seal",)),
    # ---- 通し・断り・数え方
    (u"N1 断りの段を取り違える(置き場を作る → 文脈と単位を作る)", u"            return declined_rec(rec, STAGES[1], reason)", u"            return declined_rec(rec, STAGES[2], reason)", ("measure", "chunk")),
    (u"N2 断りの段を取り違える(文脈と単位を作る → 属性を作る)", u"            return declined_rec(rec, STAGES[2], reason)", u"            return declined_rec(rec, STAGES[3], reason)", ("measure", "chunk")),
    (u"N3 命令の断りの理由を捨てる", u"        reason = P.decline_reason(err)\n        return False, (reason if reason is not None else label + u\"命令が 0 でない終わりの値で終わった\"), secs", u"        return False, label + u\"命令が 0 でない終わりの値で終わった\", secs", ("behaviour", "measure")),
    (u"N4 命令の時間の上限を見ない", u"    if timed_out:\n        return False, label + u\"命令が時間の上限を超えた\", secs", u"    if False:\n        return False, label + u\"命令が時間の上限を超えた\", secs", ("behaviour",)),
    (u"N5 置き場が同じを全部の行でなく数の fact の行だけで決める(比べを逆にする)", u"        rec[u\"置き場が同じ\"] = number_rows(files) == number_rows(pfiles)", u"        rec[u\"置き場が同じ\"] = True", ("measure",)),
    (u"N6 表 F の行が全部同じを常に真にする", u"        rec[u\"表 F の行が全部同じ\"] = all_rows(files) == all_rows(pfiles)", u"        rec[u\"表 F の行が全部同じ\"] = True", ("measure",)),
    (u"N7 文脈が同じを常に真にする", u"        rec[u\"文脈が同じ\"] = bool(cmp2[u\"文脈が同じ\"])", u"        rec[u\"文脈が同じ\"] = True", ("measure", "chunk")),
    (u"N8 単位が同じを常に真にする", u"        rec[u\"単位が同じ\"] = bool(cmp2[u\"単位が同じ\"])", u"        rec[u\"単位が同じ\"] = True", ("measure",)),
    (u"N9 (ア)だけが指す id を (ア) が指す id で数える", u"        rec[u\"(ア)だけが指す id の数\"] = sum(1 for tags in cinfo[\"ids\"].values() if tags == set([u\"ア\"]))", u"        rec[u\"(ア)だけが指す id の数\"] = sum(1 for tags in cinfo[\"ids\"].values() if u\"ア\" in tags)", ("measure", "chunk")),
    (u"N10 期の名の数を数えない", u"        rec[u\"期の名の数\"] = len(back2[\"periods\"])", u"        rec[u\"期の名の数\"] = 0", ("measure", "chunk")),
    (u"N11 2 回組んで同じを見ない(いつも真)", u"        rec[u\"2 回組んで同じ\"] = bool(ok2 and P.read_tree(bout2) == tree)", u"        rec[u\"2 回組んで同じ\"] = True", ("measure", "chunk")),
    (u"N12 組み直しの包みでなく元の包みを道具に掛ける", u"        B.write_package(P.rebuilt_pack(entries, tree), new_zip)", u"        B.write_package(entries, new_zip)", ("measure",)),
    (u"N13 属性を作る命令に文脈を作った folder でなく置いた folder を渡す", u"        ok, reason, secs = S.exec_attrs(ctxf, out1, cwd, proc)", u"        ok, reason, secs = S.exec_attrs(placed, out1, cwd, proc)", ("measure", "chunk")),
    (u"N14 文脈と単位を作る命令に紙の folder を渡す(置き場を作る前の folder)", u"        ok, reason, secs = exec_step(\"context\", u\"文脈と単位を作る\", placed, ctxf, cwd, proc)", u"        ok, reason, secs = exec_step(\"context\", u\"文脈と単位を作る\", folder, ctxf, cwd, proc)", ("measure", "chunk")),
    (u"N15 組む命令に属性を作った folder でなく文脈を作った folder を渡す", u"        ok, reason, secs = P.exec_build(out1, bout1, cwd, proc)", u"        ok, reason, secs = P.exec_build(ctxf, bout1, cwd, proc)", ("measure", "chunk")),
    (u"N16 組む命令の出力の file の名を見ない", u"        if set(tree) != P.expected_names(out_index):", u"        if False:", ("measure",)),
    (u"N17 紙の folder に元の行が在っても止めない", u"        if S.leak_problems(folder) or leak_place_problems(folder):", u"        if False:", ("measure",)),
    (u"N18 置いた folder に元の行が在っても止めない", u"        if leak_context_problems(placed):", u"        if False:", ("measure",)),
    (u"N19 全部同じを fact が同じだけで決める", u"        for k in (u\"タクソノミが同じ\", u\"fact が同じ\", u\"鳴り方が同じ\", u\"全部同じ\"):\n            rec[k] = bool(cmp[k])", u"        for k in (u\"タクソノミが同じ\", u\"fact が同じ\", u\"鳴り方が同じ\"):\n            rec[k] = bool(cmp[k])\n        rec[u\"全部同じ\"] = rec[u\"fact が同じ\"]", ("measure",)),
    (u"N20 表 F が同じを違う fact の数に依らず真にする", u"        rec[u\"表 F が同じ\"] = diff == 0", u"        rec[u\"表 F が同じ\"] = True", ("measure", "chunk")),
    (u"N21 紙の欄に紙 2 の欄を足さない", u"        cells.update(paper2_cells(back2))", u"        pass", ("measure", "chunk")),
    (u"N22 紙の欄の数を 0 にする", u"        rec[u\"紙の欄の数\"] = sum(cells.values())", u"        rec[u\"紙の欄の数\"] = 0", ("measure", "chunk")),
    (u"N23 道具の確かめを掛けない(build_record)", u"    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)\n    per_doc = []", u"    info = od([(u\"版\", u\"x\"), (u\"ModelValue.py の sha256\", u\"x\"), (u\"package の一覧の sha256\", u\"x\"), (u\"Python の版\", u\"x\")])\n    per_doc = []", ("record",)),
    (u"N24 包みが元と byte で同じを常に偽にする", u"        rec[u\"包みが元と byte で同じ\"] = same_bytes(entries, tree)", u"        rec[u\"包みが元と byte で同じ\"] = False", ("chunk",)),
    # ---- 数え方(塊・判定)
    (u"G1 判定 XH0-1 の分母を 1 つずつ書く fact を含む fact の数にする", u"rate(prod[u\"規則が当てた fact の数\"], prod[u\"1 つずつ書く fact でない fact の数\"])", u"rate(prod[u\"規則が当てた fact の数\"], prod[u\"fact の数(紙を作れた書類)\"])", ("chunk",)),
    (u"G2 判定 XH0-2 の分母から 1 つずつ書く fact の在る cell を除かない", u"prod[u\"決めの在る cell の数\"] - prod[u\"1 つずつ書く fact の在る cell の数\"]", u"prod[u\"決めの在る cell の数\"]", ("chunk",)),
    (u"G3 判定 XH0-4 を属性を作る段の断りで数える", u"prod[u\"断った段ごとの数\"][STAGES[2]]", u"prod[u\"断った段ごとの数\"][STAGES[3]]", ("chunk",)),
    (u"G4 判定に要る数を 5 本も入れた全部の塊から作る", u"    prod = tot[[k for k in tot if k.startswith(u\"本番だけの\")][0]]", u"    prod = tot[u\"全部\"]", ("chunk",)),
    (u"G5 断った書類を紙を作れた書類に数える", u"    made = [e for e in entries if e[u\"fact の数\"] is not None]", u"    made = [e for e in entries]", ("chunk",)),
    (u"G6 判定 XH0-7 を元にだけ在る id の数で数える", u"od([(u\"書類\", prod[u\"元にだけ在る id が 1 つ以上在る書類の数\"]), (u\"分母\", n)])", u"od([(u\"書類\", prod[u\"元にだけ在る id の数\"]), (u\"分母\", n)])", ("chunk",)),
    (u"G7 判定 XH0-8 の期の分母を書類の数にする", u"(u\"分母\", prod[u\"混ぜ物(期)を作れた書類の数\"])", u"(u\"分母\", n)", ("chunk",)),
    (u"G8 判定 XH0-8 の置き場の分母を書類の数にする", u"(u\"分母\", prod[u\"混ぜ物(置き場)を作れた書類の数\"])", u"(u\"分母\", n)", ("chunk",)),
    (u"G9 疑いの断った書類の数を 11 にする", u"SUSPECT_DECLINED = 10", u"SUSPECT_DECLINED = 11", ("seal", "chunk")),
    (u"G10 疑いの例外の cell が全部 0 を見ない", u"    if whole and ch[u\"紙を作れた書類の数\"] and ch[u\"例外の cell の数\"] == 0:", u"    if False:", ("chunk",)),
    (u"G11 疑いの置き場が同じでない書類を見ない", u"    if ch[u\"置き場を作れた書類の数\"] and ch[u\"置き場が同じ書類の数\"] < ch[u\"置き場を作れた書類の数\"]:", u"    if False:", ("chunk",)),
    (u"G12 疑いの決めの在る cell の外を見ない", u"    if ch[u\"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数\"] > 0:", u"    if False:", ("chunk",)),
    (u"G13 疑いの文脈が同じなのに fact が違う書類を見ない", u"    if ch[u\"文脈と単位を作れた書類の数\"] and ch[u\"文脈が同じ書類の数\"] > ch[u\"fact が同じ書類の数\"]:", u"    if False:", ("chunk",)),
    (u"G14 疑いの混ぜ物を作れなかった書類を見ない", u"    if ch[u\"混ぜ物(期)を作れた書類の数\"] < ch[u\"文脈と単位を作れた書類の数\"] or ch[u\"混ぜ物(置き場)を作れた書類の数\"] < ch[u\"置き場を作れた書類の数\"]:", u"    if False:", ("chunk",)),
    (u"G15 予測の境(XH0-1)を変える", u"(\"XH0-1\", (97, None))", u"(\"XH0-1\", (96, None))", ("seal",)),
    (u"G16 予測の境(XH0-2)を変える", u"(\"XH0-2\", (None, 3))", u"(\"XH0-2\", (None, 4))", ("seal",)),
    (u"G17 予測の境(XH0-3)を変える", u"(\"XH0-3\", (55, None))", u"(\"XH0-3\", (54, None))", ("seal",)),
    (u"G18 予測の境(XH0-9 の上限)を変える", u"(\"XH0-9\", (40, 44))", u"(\"XH0-9\", (40, 45))", ("seal",)),
    (u"G19 予測の境(XH0-10)を変える", u"(\"XH0-10\", (None, 0))", u"(\"XH0-10\", (None, 1))", ("seal",)),
    (u"G20 封の commit を変える", u"SEAL_COMMIT = \"97eff9a2\"", u"SEAL_COMMIT = \"97eff9a3\"", ("seal",)),
    (u"G21 記録の path を変える", u"RECORD_REL = \"fixtures/xbrl/cd8/place_context_build_2026-11-22.json\"", u"RECORD_REL = \"fixtures/xbrl/cd8/place_context_build_2026-11-23.json\"", ("seal",)),
    (u"G22 断りの段を変える", u"STAGES = (u\"紙を作る\", u\"置き場を作る\", u\"文脈と単位を作る\", u\"属性を作る\", u\"組む\")", u"STAGES = (u\"紙を作る\", u\"置き場を作る\", u\"文脈と単位を作る\", u\"属性を作る\", u\"道具\")", ("seal",)),
    (u"G23 開発の本数を変える", u"DEV_COUNT = 5\n\n# ---- 封 §1", u"DEV_COUNT = 6\n\n# ---- 封 §1", ("seal",)),
    (u"G24 限界の字を消す", u"    u\"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。\"]", u"    u\"この便の限界。\"]", ("seal",)),
    (u"G25 連結個別の軸の字を変える", u"CNC_AXIS = \"ConsolidatedOrNonConsolidatedAxis\"", u"CNC_AXIS = \"ConsolidatedOrNonConsolidatedAxes\"", ("seal", "rules")),
    (u"G26 _cor の字を変える", u"COR_SUFFIX = \"_cor\"", u"COR_SUFFIX = \"_core\"", ("seal", "rules")),
    (u"G27 記録に紙の中身の字(要素の名)を書く", u"        (u\"書類の本数\", len(per_doc)), (u\"書類の file 名の並びの sha256\", order_sha),", u"        (u\"書類の本数\", len(per_doc)), (u\"書類の file 名の並びの sha256\", order_sha), (u\"例\", u\"jppfs_cor:E0\"),", ("record",)),
    (u"G28 記録の日付の検査を外す(便 XS0 の検査を呼ばない)", u"    S.check_clean(rec, text, secret)", u"    X.check_clean(rec, text, secret)", ("clean",)),
    (u"G29 secret の要素の名を渡さない", u"    secret = (set(), set(e for e in names if len(e) >= 3), [d[0] for d in docs], ecodes)\n    return assemble(per_doc,", u"    secret = (set(), set(), [d[0] for d in docs], ecodes)\n    return assemble(per_doc,", ("record",)),
    (u"G30 記録の検査で書類の形を見ない", u"        if d.get(u\"番号\") != i or list(d) != DOC_KEYS:\n            raise Stop(u\"**記録の書類の形が違う。止める**\")\n", u"", ("record",)),
    # ---- 配線
    (u"W1 別の門の規準の字を関数の名にする", u"def masked(raw):", u"def mutate(x):\n    return x\n\n\ndef masked(raw):", ("wiring",)),
    (u"W2 別の門の規準の字を説明文に書く", u"# 置き場の規則(封 §1。", u"# 置き場の規則(注入)(封 §1。", ("wiring",)),
    (u"W3 便 XS0 の script を他の便と重なる名で読む", u"SHEET_NAME = \"_xh0_sheet_build_2026_11_22\"", u"SHEET_NAME = \"_xs0_sheet_context_2026_11_22\"", ("wiring",)),
    (u"W4 前の便の関数を写す", u"def masked(raw):", u"def table_lookup(sheet):\n    return {}\n\n\ndef masked(raw):", ("wiring",)),
    (u"W5 zipfile を import する", u"import time\n\nHERE", u"import time\nimport zipfile\n\nHERE", ("wiring",)),
    (u"W6 subprocess を import する", u"import time\n\nHERE", u"import time\nimport subprocess\n\nHERE", ("wiring",)),
    (u"W7 engine を import する", u"import time\n\nHERE", u"import time\nfrom adapters.xbrl import instance\n\nHERE", ("wiring",)),
    (u"W8 Stop を別に読む", u"W = S.W ", u"W = _load_sibling(\"_xh0_other_wall\", \"xbrl_tag_wall_2026-11-21.py\")  # ", ("wiring", "called")),
    (u"W9 前の便の place_positions を写す", u"def masked(raw):", u"def place_positions(text, positions):\n    return []\n\n\ndef masked(raw):", ("wiring",)),
    (u"W10 前の便の decided_attrs を呼ばない", u"                S.decided_attrs(f, t, sheet, probe, row)\n                cid = id_of_triple", u"                probe.asked.append((u\"I\", u\"\", ()))\n                cid = id_of_triple", ("wiring", "rules")),
    (u"W11 scratchpad の path を書く", u"R_P2 = u\"紙 2 が読めない形\"", u"R_P2 = u\"紙 2 が読めない形\"\nSCRATCH = \"/private/tmp/x/scratchpad\"", ("wiring",)),
    (u"W12 itertools でなく random を import する", u"import itertools\n", u"import random\n", ("wiring",)),
)
#: 黙ることが分かっている変異(理由つき)。予測は「黙る」ではなく、実行して黙った事実と理由を実行の後に書く(実行前は空)
SILENT_BY_DESIGN = {
    u"R31 1 つずつ書く fact の在る cell を hand の始まりでなく終わりで引く": u"同値の変異: 1 つずつ書く fact の始まりと終わりは同じ cell の中に在る(便 XA0 の cell の引きは「開きタグが ``p`` より前」なので、終わりが cell の閉じタグの始まりに当たっても同じ cell)。この便の書類では始まりと終わりで cell が変わる fact が無い",
    u"E10 決めの在る cell の外の fact を数えない": u"同値の変異: 1 つずつ書く fact でない fact は便 XS0 の紙の決めが全部在る fact なので、その fact の cell には必ず決めが在る。決めの在る cell の外の数は構造上 0 のままで、数えない変異は 0 を 0 のまま返す。この数は封 §4 の欠陥を疑う条件の「数が 1 つでも在れば」のためだけに在る",
    u"X6 混ぜ物(期)の効いたを常に真にする": u"同値の変異: 当て先の期の名を指す fact が 2 つ以上在る(当て先の選び方)ので、その期の名の定義は必ず 1 つ以上在り、変わった定義の数 changed は 1 以上になる。それ以外の早い抜け(長さ・定義・ほかの file の違い)は先に偽を返すので、末尾の「changed >= 1」は冗長",
    u"X14 混ぜ物(置き場)の効いたを常に真にする": u"同値の変異: 先に返さずに全部の行を通った場合、規則が置いた空の fact の行は 1 つずつ全部が反転として数えられ、flips は集まりの大きさに等しい。末尾の「flips == 全部の数」は冗長",
    u"N24 包みが元と byte で同じを常に偽にする": u"作り物の書類では組んだ包みが元の包みと byte で同じになる書類を作れていない(組む側の属性の並び・頭の部の行の並びが元の字と同じになる書類は手で書いていない)。比べ方を縛るのは byte の比べ方の部品の試験(同じ・中身が違う・名が違う)",
}


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"rules": rules_problems, u"paper": paper_problems, u"behaviour": blind_behaviour_problems, u"measure": measure_problems, u"chunk": chunk_problems,
             u"record": record_problems, u"clean": clean_problems, u"called": called_same_problems}
    if name in table:
        return table[name](mod)
    if name == u"blind":
        return blind_problems(src)
    if name == u"wiring":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"rules", u"paper", u"blind", u"behaviour", u"measure", u"chunk", u"record", u"clean", u"called", u"wiring")


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
        for old, new in ((u"置き場の規則が当てたものは 97% 以上", u"置き場の規則が当てたものは 96% 以上"), (u"紙の欄の比は 40% 以上 44% 未満", u"紙の欄の比は 40% 以上 45% 未満"),
                         (u"文脈が同じ書類は 55 本以上", u"文脈が同じ書類は 56 本以上"), (u"例外の cell × 1 + 例外の cell の中の fact × 2", u"例外の cell × 1 + 例外の cell の中の fact × 3"),
                         (u"ただし、そのすぐ前が `span` の開きタグなら", u"ただし、そのすぐ前が `div` の開きタグなら"), (u"接頭辞が `_cor` で終わるなら local name", u"接頭辞が `_core` で終わるなら local name"),
                         (u"`1900-01-01`", u"`1900-01-02`"), (u"**紙の欄の比** = 紙の欄の数 ÷(fact の数 × 7)", u"**紙の欄の比** = 紙の欄の数 ÷(fact の数 × 8)")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"place_context_build", body)


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


class RuleTest(unittest.TestCase):
    def test_b_1_the_rules_one_by_one_on_made_up_documents(self):
        self.assertEqual([], rules_problems())

    def test_b_2_a_changed_paper_2_value_changes_the_output_and_the_folders_have_no_answer(self):
        self.assertEqual([], paper_problems())


class BlindTest(unittest.TestCase):
    def test_h_1_the_two_commands_have_no_door_to_the_answer(self):
        self.assertEqual([], blind_problems())

    def test_h_2_the_two_commands_take_two_folders_only(self):
        self.assertEqual([], blind_behaviour_problems())

    def test_h_3_the_blind_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for old, new in ((u"def place_tables(folder):", u"def place_tables(folder, entries=None):"),
                         (u"    index, sheet, p2, files = read_paper_folder(folder)\n    resources, info", u"    index, sheet, p2, files = read_paper_folder(folder)\n    X.doc_texts(folder)\n    resources, info"),
                         (u"    index, sheet, p2, files = read_paper_folder(folder)\n    resources, info", u"    index, sheet, p2, files = read_paper_folder(folder)\n    make_paper_folder(folder, folder, folder)\n    resources, info")):
            self.assertEqual(1, base.count(old), old)
            self.assertNotEqual([], blind_problems(base.replace(old, new)), new)


class CountTest(unittest.TestCase):
    def test_c_1_one_document_end_to_end(self):
        self.assertEqual([], measure_problems())

    def test_c_2_chunks_judging_numbers_and_suspicions(self):
        self.assertEqual([], chunk_problems())


class RecordTest(unittest.TestCase):
    def test_e_1_the_record_path_from_a_fake_place(self):
        self.assertEqual([], record_problems())

    def test_e_2_forbidden_things_stop_the_record(self):
        self.assertEqual([], clean_problems())

    def test_e_3_the_real_record_when_present_is_clean_and_consistent(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く(作り物の記録の検査は test_e_1)")
        text = read(RECORD_REL)
        MS.verify_record(json.loads(text, object_pairs_hook=od), text)


class WiringTest(unittest.TestCase):
    def test_f_1_imports_and_the_earlier_functions_are_called_not_copied(self):
        self.assertEqual([], import_problems())

    def test_f_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for extra in (u"\nimport socket\n", u"\nimport zipfile\n", u"\nimport csv\n", u"\nimport subprocess\n", u"\nfrom adapters.xbrl import instance\n", u"\nX2 = os.system('a')\n",
                      u"\ndef select_docs(a, b):\n    return None\n", u"\ndef place_positions(a, b):\n    return None\n", u"\ndef run_doc(a):\n    return None\n", u"\ndef doc_texts(a):\n    return None\n",
                      u"\nSCRATCH = '/private/tmp/x'\n"):
            self.assertNotEqual([], import_problems(base + extra), extra)
        self.assertNotEqual([], import_problems(base.replace(u"S.make_sheet_folder(", u"make_sheet_folder(")))
        self.assertNotEqual([], import_problems(base.replace(u"P.exec_build(", u"exec_build(")))
        self.assertNotEqual([], import_problems(base.replace(u"W.select_docs(", u"select_docs(")))

    def test_f_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_f_4_the_script_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_place_context_build_script_for_sysmodules_check")
        changed = [k for k in before if sys.modules.get(k) is not before[k]]
        self.assertEqual([], changed)
        self.assertEqual(mod.S.__name__, u"_xh0_sheet_build_2026_11_22")
        self.assertIs(mod.W, mod.S.W)
        self.assertIs(mod.Stop, mod.S.Stop)
        self.assertEqual([], called_same_problems())
        del mod

    def test_f_5_the_default_place_is_outside_the_repo_and_the_gate_never_opens_it(self):
        top = os.path.realpath(REPO)
        self.assertFalse(os.path.realpath(MS.DOCS_DIR).startswith(top + os.sep))
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record|dev_docs|dev_run)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"docs|rec_path|\bd\b|docs2", m.group(2)), m.group(0))

    def test_f_6_the_gate_calls_subprocess_only_for_git(self):
        src = read(GATE_REL)
        calls = re.findall(r"subprocess\.(\w+)", src)
        self.assertEqual(set(calls), {"run", "PIPE"})
        for m in re.finditer(r"subprocess\.run\(([^)]*)\)", src):
            self.assertTrue(m.group(1).startswith(u'["git"'), m.group(1))

    def test_f_7_the_script_has_no_scratchpad_path_and_calls_no_paid_api(self):
        src = read(SCRIPT_REL)
        for w in (u"scratchpad", u"/private/tmp", u"anthropic", u"openai", u"API_KEY", u"urllib", u"requests"):
            self.assertNotIn(w, src, w)


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
        old, new = u"    if len(runs) == 1:\n        return [(runs[0][0], runs[0][1], False)]", u"    if len(runs) >= 1:\n        return [(runs[0][0], runs[0][1], False)]"
        mod = load_source(base.replace(old, new))
        self.assertNotEqual([], guard(check_by_name, u"rules", mod, base))
        self.assertEqual([], check_by_name(u"rules", MS, base))
        self.assertIsNot(mod.predict_cell, MS.predict_cell)


if __name__ == "__main__":
    unittest.main()
