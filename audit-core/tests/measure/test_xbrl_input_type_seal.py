# -*- coding: utf-8 -*-
u"""封 docs/XBRL_INPUT_TYPE_SEAL_2026-11-22.md(XM0 ― 機械の側が決めた入力の型(第 0 版)と対応表だけから、fact の属性と文脈・単位の定義を作ると、公開の道具が読む fact は元と意味として同じになるか)の封の門。

**この門は置き場も道具も読まない**(書類の置き場 ``~/.cache/audit-core/edinet/``・道具の venv は 1 度も開かない。道具が無い機械でも緑)。通信しない。道具の呼び出しは作り物の runner に差し替える。
subprocess を呼ぶのは git と、型から作る命令(``python3 -I <script> make <folder> <folder>``)・便 XP0 の組む命令を作り物の folder に掛ける所だけ。
作り物の書類(PublicDoc に htm 2 つ・xsd・linkbase 5 つ・マニフェスト・``.xbrl``・AuditDoc。htm の fact は型の外の理由 (a)〜(h) のそれぞれ・同じ鍵のまとめ・空の fact・``-0``・個別と次元・持ち込みの属性を持つ)で、
型を作る・別の process で型から作る・組む・比べる・混ぜ物・表示の字の検査・数え方・記録の検査を本物の関数のまま通す。作り物の道具・作り物の包みの部品は、便 XT0・便 XP0 の封の門の部品を importlib で読んで使う(写さない)。

**この門が縛るもの**

1. 封の字: 封の commit(34afe495)・封の file が commit した blob と同じ・便 XT0 の封と同じ道具・時間の上限・67 本・開発の 5 本・混ぜ物の種類・型の外の理由 8 つ・単位の 4 つの形・期の名・予測の境の数・限界の字が script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 規則を 1 つずつ(期の名の N 年前と月の末日・単位の形・member の字・文脈の id の並び・型の外の理由 (a)〜(h)・同じ鍵のまとめ・空の fact・``-0``・表示の字・対応表の番号・resources の並び・id の重なりの断り・
   比べ方 2 の正規化・混ぜ物・表示の字の検査)。**型から作る命令に渡す folder の持ち込みに入れないものが無い**・型の値を 1 つ変えると作った属性か定義が変わる(欄ごとに)。
4. 型から作る命令の中身(``render_manuscript``)は folder だけを引数に取り、元の包み・zip・型を作る側の関数を読まない。``process_doc`` は型から作る命令・組む命令を別の process(``exec_make``・``exec_build``)で呼ぶ。
5. 書類 1 本の通し・断り(型を作る・型から作る・組む・道具)・数え方(§2)・記録の検査と禁止のもの。
6. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。表は実行より先に書いた(予測 = 赤になるべき検査の名前)。
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
    mod = types.ModuleType("xbrl_input_type_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_INPUT_TYPE_SEAL_2026-11-22.md"
XT0_SEAL_REL = "docs/XBRL_TAXONOMY_BUILD_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "34afe495"
SCRIPT_REL = "measure/xbrl_input_type_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_input_type_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/input_type_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_input_type_script_for_seal_gate")
PG = load_module("tests/measure/test_xbrl_pack_build_seal.py", "xm0_gate_helpers_from_pack_gate")
X = PG.X
ORDER_FILES = (SCRIPT_REL, GATE_REL)
od = collections.OrderedDict
PACK_NAME = "_xm0_pack_build_2026_11_22"
SIBLINGS = ("xbrl_pack_build_2026-11-22.py", "xbrl_taxonomy_build_2026-11-22.py", "xbrl_inline_build_2026-11-21.py", "xbrl_edinet_validate_2026-11-21.py", "xbrl_tag_wall_2026-11-21.py")
read = X.read
read_text = X.read_text
read_bytes_sha = X.read_bytes_sha
Temp = X.Temp
stops = X.stops
guard = X.guard
sha_of = X.sha_of
sha_or_none = X.sha_or_none
KINDS = X.KINDS
read_file = PG.read_file
write_file = PG.write_file
tree_of = PG.tree_of
captured = PG.captured
jdump, jload = MS.jdump, MS.jload

# ======================================================================== 作り物の書類(手で書いた字)
FMT_OK = u"ixt:numdotdecimal"
ENT = (u"http://example.org/id", u"E99991-000")
CA, NM = u"jppfs_cor:ConsolidatedOrNonConsolidatedAxis", u"jppfs_cor:NonConsolidatedMember"
COMP, CAP, RET = u"jppfs_cor:ComponentsOfEquityAxis", u"jppfs_cor:CapitalStockMember", u"jppfs_cor:RetainedEarningsMember"
SEG, MEM_A = u"jpcrp030000-asr_E99991-000:SegAxis", u"jpcrp030000-asr_E99991-000:AMember"


def cx(cid, per, members=(), ent=ENT):
    lines = [u'<xbrli:context id="%s">' % cid, u"<xbrli:entity>", u'<xbrli:identifier scheme="%s">%s</xbrli:identifier>' % ent, u"</xbrli:entity>", u"<xbrli:period>"]
    if per[0] == "i":
        lines.append(u"<xbrli:instant>%s</xbrli:instant>" % per[1])
    else:
        lines += [u"<xbrli:startDate>%s</xbrli:startDate>" % per[1], u"<xbrli:endDate>%s</xbrli:endDate>" % per[2]]
    lines.append(u"</xbrli:period>")
    if members:
        lines.append(u"<xbrli:scenario>")
        lines += [u'<xbrldi:explicitMember dimension="%s">%s</xbrldi:explicitMember>' % m for m in members]
        lines.append(u"</xbrli:scenario>")
    lines.append(u"</xbrli:context>")
    return u"\n".join(lines)


def un(uid, num, den=None):
    if den is None:
        return u'<xbrli:unit id="%s">\n<xbrli:measure>%s</xbrli:measure>\n</xbrli:unit>' % (uid, num)
    return u'<xbrli:unit id="%s">\n<xbrli:divide>\n<xbrli:unitNumerator>\n<xbrli:measure>%s</xbrli:measure>\n</xbrli:unitNumerator>\n<xbrli:unitDenominator>\n<xbrli:measure>%s</xbrli:measure>\n</xbrli:unitDenominator>\n</xbrli:divide>\n</xbrli:unit>' % (uid, num, den)


def tag(kind, attrs, content=None):
    a = u"".join(u' %s="%s"' % kv for kv in attrs)
    if content is None:
        return u"<ix:%s%s />" % (kind, a)
    return u"<ix:%s%s>%s</ix:%s>" % (kind, a, content, kind)


def nf(name, cref, unit, dec, scale, content, fmt=FMT_OK, extra=()):
    attrs = [(u"name", name), (u"contextRef", cref)]
    for k, v in ((u"unitRef", unit), (u"decimals", dec), (u"scale", scale), (u"format", fmt)):
        if v is not None:
            attrs.append((k, v))
    return tag(u"nonFraction", attrs + list(extra), content)


def nilf(name, cref, unit, extra=()):
    return tag(u"nonFraction", [(u"name", name), (u"contextRef", cref), (u"unitRef", unit), (u"xsi:nil", u"true")] + list(extra), None)


def nn(name, cref, content, extra=()):
    return tag(u"nonNumeric", [(u"name", name), (u"contextRef", cref)] + list(extra), content)


CYI, CYD, FDI = u"CurrentYearInstant", u"CurrentYearDuration", u"FilingDateInstant"
CYI_NC = u"CurrentYearInstant_NonConsolidatedMember"
CYI_SEG = u"CurrentYearInstant_NonConsolidatedMember_jpcrp030000-asr_E99991-000AMember"
P1I_COMP = u"Prior1YearInstant_ComponentsMember"
P1I_CAP = u"Prior1YearInstant_CapitalStockMember"
JPY = u"JPY"
CTX_ALL = [
    cx(CYI, ("i", u"2026-03-31")), cx(CYD, ("d", u"2025-04-01", u"2026-03-31")), cx(FDI, ("i", u"2026-06-30")), cx(u"Prior1YearInstant", ("i", u"2025-03-31")),
    cx(u"Prior1YearDuration", ("d", u"2024-04-01", u"2025-03-31")), cx(u"Prior2YearInstant", ("i", u"2024-03-31")),
    cx(CYI_NC, ("i", u"2026-03-31"), [(CA, NM)]), cx(CYI_SEG, ("i", u"2026-03-31"), [(SEG, MEM_A), (CA, NM)]), cx(P1I_COMP, ("i", u"2025-03-31"), [(COMP, CAP)]),
    cx(u"OddInstant", ("i", u"2026-02-15")), cx(u"OtherEntity", ("i", u"2026-03-31"), ent=(u"http://example.org/id", u"E88888-000")),
    cx(u"BadMember", ("i", u"2026-03-31"), [(CA, u"jppfs_cor:ConsolidatedMember")]), cx(u"DupAxis", ("i", u"2026-03-31"), [(COMP, CAP), (COMP, RET)]), cx(u"Unused", ("i", u"2023-03-31"))]
UNIT_ALL = [un(u"JPY", u"iso4217:JPY"), un(u"shares", u"xbrli:shares"), un(u"pure", u"xbrli:pure"), un(u"JPYperShares", u"iso4217:JPY", u"xbrli:shares"), un(u"USDPerJPY", u"iso4217:USD", u"iso4217:JPY")]
HIDDEN = u"\n".join([nn(u"jpdei_cor:FilingText", FDI, u"提出"), nf(u"jpdei_cor:NumSub", FDI, u"pure", u"0", u"0", u"1", fmt=None)])
HEADER = u"<ix:header>\n<ix:hidden>\n%s\n</ix:hidden>\n<ix:references>\n<link:schemaRef xlink:type=\"simple\" xlink:href=\"x.xsd\" />\n</ix:references>\n<ix:resources>\n%s\n</ix:resources>\n</ix:header>" % (
    HIDDEN, u"\n".join(CTX_ALL + UNIT_ALL))
FACTS_A = [
    nf(u"jppfs_cor:Assets", CYI, JPY, u"-3", u"3", u"1,234"),                                            # A1
    nf(u"jppfs_cor:Assets", CYI, JPY, u"-3", u"3", u"1,234"),                                            # A2 同じ鍵・同じ値
    nf(u"jppfs_cor:Assets", CYI_NC, JPY, u"0", u"0", u"999"),                                            # A3 個別
    nf(u"jppfs_cor:Profit", CYD, JPY, u"0", u"0", u"1,500", extra=[(u"sign", u"-")]),                    # A4
    nf(u"jppfs_cor:Zero", CYD, JPY, u"0", u"0", u"0", extra=[(u"sign", u"-")]),                          # A5 -0
    nilf(u"jppfs_cor:Receivable", CYI, JPY),                                                             # A6 空
    nf(u"jppfs_cor:EPS", CYD, u"JPYperShares", u"2", u"0", u"12.34"),                                    # A7
    nf(u"jppfs_cor:Shares", CYI, u"shares", u"0", u"0", u"1,000"),                                       # A8
    nf(u"jppfs_cor:Ratio", CYI, u"pure", u"3", u"0", u"0.500"),                                          # A9
    nf(u"jppfs_cor:Equity", P1I_COMP, JPY, u"0", u"0", u"5"),                                            # A10 次元
    nf(u"jppfs_cor:Seg", CYI_SEG, JPY, u"0", u"0", u"7"),                                                # A11 個別 + 提出者別の次元
    nf(u"jppfs_cor:Assets", u"OddInstant", JPY, u"0", u"0", u"3"),                                       # A12 (a)
    nf(u"jppfs_cor:Assets", u"OtherEntity", JPY, u"0", u"0", u"3"),                                      # A13 (b)
    nf(u"jppfs_cor:Assets", u"BadMember", JPY, u"0", u"0", u"3"),                                        # A14 (c) 個別の軸に別の member
    nf(u"jppfs_cor:Assets", u"DupAxis", JPY, u"0", u"0", u"3"),                                          # A15 (c) 同じ軸が 2 回
    nf(u"jppfs_cor:X1", CYI, u"USDPerJPY", u"0", u"0", u"5"),                                            # A16 (d) 4 つの形のどれでもない
    nf(u"jppfs_cor:X2", CYI, None, u"0", u"0", u"5"),                                                    # A17 (d) unitRef が無い
    nf(u"jppfs_cor:E1", CYI, JPY, u"0", u"0", u"5", fmt=u"ixt:numcommadecimal"),                         # A18 (e) format
    nf(u"jppfs_cor:E2", CYI, JPY, None, u"0", u"5"),                                                     # A19 (e) decimals が無い
    nf(u"jppfs_cor:E3", CYI, JPY, u"abc", u"0", u"5"),                                                   # A20 (e) decimals が整数でない
    nf(u"jppfs_cor:E4", CYI, JPY, u"0", u"1e3", u"5"),                                                   # A21 (e) scale が整数でない
    nf(u"jppfs_cor:F1", CYI, JPY, u"0", u"0", u"1.5.2"),                                                 # A22 (f)
    nf(u"jppfs_cor:F2", CYI, JPY, u"0", u"0", u"5", extra=[(u"sign", u"+")]),                            # A23 (f) sign が - 以外
    nf(u"jppfs_cor:F3", CYI, JPY, u"0", u"0", u"△5"),                                                    # A24 (f)
    nf(u"jppfs_cor:Dup", CYI, JPY, u"0", u"0", u"10"),                                                   # A25 (g)
    nf(u"jppfs_cor:Dup", CYI, JPY, u"0", u"0", u"11"),                                                   # A26 (g) 値が違う
    nf(u"jppfs_cor:DupUnit", CYI, JPY, u"0", u"0", u"5"),                                                # A27 (g)
    nf(u"jppfs_cor:DupUnit", CYI, u"pure", u"0", u"0", u"5"),                                            # A28 (g) 単位が違う
    nf(u"jppfs_cor:DupPrec", CYI, JPY, u"0", u"0", u"5"),                                                # A29 (g)
    nf(u"jppfs_cor:DupPrec", CYI, JPY, u"1", u"0", u"5"),                                                # A30 (g) 精度が違う
    nilf(u"jppfs_cor:DupNil", CYI, JPY),                                                                 # A31 (g)
    nf(u"jppfs_cor:DupNil", CYI, JPY, u"0", u"0", u"5"),                                                 # A32 (g) 空と値
    nilf(u"jppfs_cor:H1", CYI, JPY, extra=[(u"decimals", u"0")]),                                        # A33 (h) 空なのに decimals
    tag(u"nonFraction", [(u"name", u"jppfs_cor:H2"), (u"contextRef", CYI), (u"unitRef", JPY), (u"xsi:nil", u"false")], None),   # A34 (h) xsi:nil が true でない
    nf(u"jppfs_cor:S1", u"OddInstant", None, u"0", u"0", u"5"),                                          # A35 (a)(d)
    nf(u"jppfs_cor:NoScale", CYI, JPY, u"0", None, u"42"),                                               # A36 scale が無い
    nf(u"jppfs_cor:Carry", CYI, JPY, u"0", u"0", u"9", extra=[(u"footnoteRefs", u"fn1"), (u"id", u"f9")]),   # A37 持ち込みの属性
    nn(u"jpcrp_cor:Text", CYD, u"本文", extra=[(u"escape", u"true")]),                                   # T1
    nn(u"jpcrp_cor:Text", CYD, u"続き", extra=[(u"id", u"t2")]),                                         # T2 同じ鍵
    tag(u"nonNumeric", [(u"name", u"jpcrp_cor:NilText"), (u"contextRef", CYD), (u"xsi:nil", u"true")], None),   # T3 空の文
    nn(u"jpcrp_cor:Text2", u"OtherEntity", u"別"),                                                       # T4 (b)
    nn(u"jpcrp_cor:Nest", CYD, nf(u"jppfs_cor:Inner", CYI, JPY, u"0", u"0", u"8")),                      # T5 入れ子(外が文・中が数)
    nn(u"jpcrp_cor:Text3", u"OddInstant", u"別"),                                                        # T6 (a)
    nf(u"jppfs_cor:Profit", CYD, JPY, u"0", u"0", u"1,500", extra=[(u"sign", u"-")]),                    # A4b 同じ鍵・同じ値(行 2 は 3 つの fact)
    nf(u"jppfs_cor:Profit", CYD, JPY, u"0", u"0", u"1,500", extra=[(u"sign", u"-")]),                    # A4c
    nf(u"jppfs_cor:DupScale", CYI, JPY, u"0", u"0", u"5,000"),                                           # A38 (g) 表示の位だけ違う(値は同じ 5000・精度も同じ)
    nf(u"jppfs_cor:DupScale", CYI, JPY, u"0", u"3", u"5"),                                               # A39 (g)
    tag(u"footnote", [(u"footnoteID", u"fn1"), (u"xml:lang", u"ja")], u"注記")]
HTM_A_TEXT = u"<html><body>\n<p>表紙</p>\n%s\n<p>%s</p>\n</body></html>\n" % (HEADER, u"</p><p>".join(FACTS_A))
HTM_B_TEXT = u"<html><body><p>%s%s%s%s</p></body></html>" % (nf(u"jppfs_cor:Assets", CYI, JPY, u"-3", u"3", u"1,234"), nf(u"jppfs_cor:BOnly", u"Prior1YearDuration", JPY, u"0", u"0", u"6"),
                                                              nf(u"jppfs_cor:Equity", u"Prior1YearInstant", JPY, u"0", u"0", u"6"), nf(u"jppfs_cor:Assets", u"Prior2YearInstant", JPY, u"0", u"0", u"2"))
#: 対象の fact の並び(file の名の昇順・file の中は表 F の順の後に隠しの fact)と、手で決めた判定(理由の集まり)。**script の出力から作っていない。**
FACT_PLAN = [
    ("F", u"jppfs_cor:Assets", ""), ("F", u"jppfs_cor:Assets", ""), ("F", u"jppfs_cor:Assets", ""), ("F", u"jppfs_cor:Profit", ""), ("F", u"jppfs_cor:Zero", ""), ("F", u"jppfs_cor:Receivable", ""),
    ("F", u"jppfs_cor:EPS", ""), ("F", u"jppfs_cor:Shares", ""), ("F", u"jppfs_cor:Ratio", ""), ("F", u"jppfs_cor:Equity", ""), ("F", u"jppfs_cor:Seg", ""),
    ("F", u"jppfs_cor:Assets", "a"), ("F", u"jppfs_cor:Assets", "b"), ("F", u"jppfs_cor:Assets", "c"), ("F", u"jppfs_cor:Assets", "c"), ("F", u"jppfs_cor:X1", "d"), ("F", u"jppfs_cor:X2", "d"),
    ("F", u"jppfs_cor:E1", "e"), ("F", u"jppfs_cor:E2", "e"), ("F", u"jppfs_cor:E3", "e"), ("F", u"jppfs_cor:E4", "e"), ("F", u"jppfs_cor:F1", "f"), ("F", u"jppfs_cor:F2", "f"), ("F", u"jppfs_cor:F3", "f"),
    ("F", u"jppfs_cor:Dup", "g"), ("F", u"jppfs_cor:Dup", "g"), ("F", u"jppfs_cor:DupUnit", "g"), ("F", u"jppfs_cor:DupUnit", "g"), ("F", u"jppfs_cor:DupPrec", "g"), ("F", u"jppfs_cor:DupPrec", "g"),
    ("F", u"jppfs_cor:DupNil", "g"), ("F", u"jppfs_cor:DupNil", "g"), ("F", u"jppfs_cor:H1", "h"), ("F", u"jppfs_cor:H2", "h"), ("F", u"jppfs_cor:S1", "ad"),
    ("F", u"jppfs_cor:NoScale", ""), ("F", u"jppfs_cor:Carry", ""), ("F", u"jpcrp_cor:Text", ""), ("F", u"jpcrp_cor:Text", ""), ("F", u"jpcrp_cor:NilText", ""), ("F", u"jpcrp_cor:Text2", "b"),
    ("F", u"jpcrp_cor:Nest", ""), ("F", u"jppfs_cor:Inner", ""), ("F", u"jpcrp_cor:Text3", "a"), ("F", u"jppfs_cor:Profit", ""), ("F", u"jppfs_cor:Profit", ""), ("F", u"jppfs_cor:DupScale", "g"), ("F", u"jppfs_cor:DupScale", "g"), ("H", u"jpdei_cor:FilingText", ""), ("H", u"jpdei_cor:NumSub", "e"),
    ("F", u"jppfs_cor:Assets", ""), ("F", u"jppfs_cor:BOnly", ""), ("F", u"jppfs_cor:Equity", ""), ("F", u"jppfs_cor:Assets", "")]
#: 型の行(番号の順)。(種類, 要素の名, 期の種類, 期, 対象, 次元, 値, 単位, 表示の位, 精度, まとめた fact の数)
ROW_PLAN = [
    (u"数", u"jppfs_cor:Assets", "instant", [u"2026-03-31"], u"既定", [], u"1234000", u"通貨:JPY", 3, -3, 3),
    (u"数", u"jppfs_cor:Assets", "instant", [u"2026-03-31"], u"個別", [], u"999", u"通貨:JPY", 0, 0, 1),
    (u"数", u"jppfs_cor:Profit", "duration", [u"2025-04-01", u"2026-03-31"], u"既定", [], u"-1500", u"通貨:JPY", 0, 0, 3),
    (u"数", u"jppfs_cor:Zero", "duration", [u"2025-04-01", u"2026-03-31"], u"既定", [], u"-0", u"通貨:JPY", 0, 0, 1),
    (u"数", u"jppfs_cor:Receivable", "instant", [u"2026-03-31"], u"既定", [], u"無い", u"通貨:JPY", None, None, 1),
    (u"数", u"jppfs_cor:EPS", "duration", [u"2025-04-01", u"2026-03-31"], u"既定", [], u"12.34", u"通貨:JPY÷株", 0, 2, 1),
    (u"数", u"jppfs_cor:Shares", "instant", [u"2026-03-31"], u"既定", [], u"1000", u"株", 0, 0, 1),
    (u"数", u"jppfs_cor:Ratio", "instant", [u"2026-03-31"], u"既定", [], u"0.5", u"純数", 0, 3, 1),
    (u"数", u"jppfs_cor:Equity", "instant", [u"2025-03-31"], u"既定", [(COMP, CAP)], u"5", u"通貨:JPY", 0, 0, 1),
    (u"数", u"jppfs_cor:Seg", "instant", [u"2026-03-31"], u"個別", [(SEG, MEM_A)], u"7", u"通貨:JPY", 0, 0, 1),
    (u"数", u"jppfs_cor:NoScale", "instant", [u"2026-03-31"], u"既定", [], u"42", u"通貨:JPY", 0, 0, 1),
    (u"数", u"jppfs_cor:Carry", "instant", [u"2026-03-31"], u"既定", [], u"9", u"通貨:JPY", 0, 0, 1),
    (u"文", u"jpcrp_cor:Text", "duration", [u"2025-04-01", u"2026-03-31"], u"既定", [], None, None, None, None, 2),
    (u"文", u"jpcrp_cor:NilText", "duration", [u"2025-04-01", u"2026-03-31"], u"既定", [], None, None, None, None, 1),
    (u"文", u"jpcrp_cor:Nest", "duration", [u"2025-04-01", u"2026-03-31"], u"既定", [], None, None, None, None, 1),
    (u"数", u"jppfs_cor:Inner", "instant", [u"2026-03-31"], u"既定", [], u"8", u"通貨:JPY", 0, 0, 1),
    (u"文", u"jpdei_cor:FilingText", "instant", [u"2026-06-30"], u"既定", [], None, None, None, None, 1),
    (u"数", u"jppfs_cor:BOnly", "duration", [u"2024-04-01", u"2025-03-31"], u"既定", [], u"6", u"通貨:JPY", 0, 0, 1),
    (u"数", u"jppfs_cor:Equity", "instant", [u"2025-03-31"], u"既定", [], u"6", u"通貨:JPY", 0, 0, 1),
    (u"数", u"jppfs_cor:Assets", "instant", [u"2024-03-31"], u"既定", [], u"2", u"通貨:JPY", 0, 0, 1)]
BUILT_CTX_IDS = [u"CurrentYearDuration", u"CurrentYearInstant", u"CurrentYearInstant_NonConsolidatedMember", u"CurrentYearInstant_NonConsolidatedMember_jpcrp030000-asr_E99991-000AMember",
                 u"FilingDateInstant", u"Prior1YearDuration", u"Prior1YearInstant", u"Prior1YearInstant_CapitalStockMember", u"Prior2YearInstant"]
OUT_CTX_IDS = [u"OddInstant", u"OtherEntity", u"BadMember", u"DupAxis"]
BUILT_UNIT_IDS = [u"JPY", u"JPYPerShares", u"pure", u"shares"]
HTM_A_NAME, HTM_B_NAME = PG.HTM_A_NAME, PG.HTM_B_NAME


def make_doc(path, no=1, a=None, b=None, **kw):
    PG.make_pack(path, no, htms=[(HTM_A_NAME, HTM_A_TEXT if a is None else a), (HTM_B_NAME, HTM_B_TEXT if b is None else b)], **kw)


def good_variant(a_text):
    u"""元の字のまま戻る版: 文脈・単位の id を作る規則の字に合わせ、scale の無い fact に scale を足す。"""
    return a_text.replace(P1I_COMP, P1I_CAP).replace(u"JPYperShares", u"JPYPerShares").replace(u'decimals="0" format="ixt:numdotdecimal">42<', u'decimals="0" scale="0" format="ixt:numdotdecimal">42<')


def entries_of(path, ms=None):
    return (ms or MS).B.load_package(path)


def peel_doc(d, ms=None, a=None, b=None, no=1):
    ms = ms or MS
    zp = os.path.join(d, "doc%d.zip" % no)
    make_doc(zp, no, a, b)
    ent = entries_of(zp, ms)
    files, names, tables = ms.P.peel_tables(ent)
    return zp, ent, files, names, tables


def derive_doc(d, ms=None, a=None, b=None):
    u"""作り物の書類 → (包み, entries, 表の並び, 型の folder, 解析)。"""
    ms = ms or MS
    zp, ent, files, names, tables = peel_doc(d, ms, a, b)
    tf = os.path.join(d, "type")
    an, files2 = ms.derive_folder(ent, tf)
    return zp, ent, files2, tf, an


def jread(folder, name):
    return jload(read_file(os.path.join(folder, name)))


def spawn(cmd, cwd):
    p = subprocess.run(list(cmd), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    return p.returncode, p.stderr.decode("utf-8", "replace")


class FactRunner(X.FakeRunner):
    u"""作り物の道具。便 XT0 の門の作り物に、fact の一覧の csv(見出し・contextRef・unitRef・値・提出者・期・次元)を、掛けた包みの htm の fact から作って足す。
    ``stop_at`` が在れば、その番号(1 から)の呼び出しを「時間の上限を超えた」にする。"""

    HEAD = [u"Name", u"contextRef", u"unitRef", u"Dec", u"Value", u"EntityScheme", u"EntityIdentifier", u"Start", u"End/Instant", u"Dimensions"]

    def __init__(self, mv_path, stop_at=None, stop_all=False, **kw):
        X.FakeRunner.__init__(self, mv_path, **kw)
        self.stop_at = stop_at
        self.stop_all = stop_all

    def facts_rows(self, blobs):
        B = MS.B
        parsed = []
        for n, data in sorted(blobs.items()):
            if B.is_public_htm(n):
                try:
                    parsed.append((n, B.strip_text(data.decode("utf-8"))))
                except B.Decline:
                    pass
        ctx = {}
        for _n, (_p, _F, H) in parsed:
            for r in (H["resources"] if H else []):
                if r["type"] == "context":
                    ctx[r["id"]] = r
        out = []
        for _n, (plain, F, H) in parsed:
            facts = [(e["attrs"], plain[e["start"]:e["end"]]) for e in F if e["kind"] in ("nonFraction", "nonNumeric")]
            facts += [(h["attrs"], h["text"]) for h in (H["hidden"] if H else [])]
            for a, text in facts:
                c = ctx.get(a["contextRef"]) or ctx_dict(inst(u""), cid=u"none")
                per = [v for _k, v in c["period"]]
                start, end = (u"", per[0]) if len(per) == 1 else (per[0], per[1])
                dims = []
                for ax, m in sorted(c["members"]):
                    dims += [ax, m]
                out.append([a["name"], a["contextRef"], a.get("unitRef", u""), a.get("decimals", u""), text, c["scheme"], c["ident"], start, end] + dims)
        return out

    def __call__(self, cmd, timeout):
        c = X.strip_seed(cmd)
        res = X.FakeRunner.__call__(self, cmd, timeout)
        if os.path.basename(c[0]) == "arelleCmdLine" and "--facts" in c:
            self.write_csv(c[c.index("--facts") + 1], [self.HEAD] + self.facts_rows(self.calls[-1]["blobs"]))
            if self.stop_all or (self.stop_at is not None and len(self.calls) == self.stop_at):
                return res[0], True
        return res


class Proc(object):
    u"""別の process の命令の作り物。呼ばれた引数・cwd・folder の中身を覚え、型から作る命令(``make_main``)か便 XP0 の組む命令(``build_main``)を同じ process の中で走らせる。"""

    def __init__(self, ms, fail=None, make_rc=None):
        self.ms = ms
        self.calls = []
        self.fail = fail                      # (動詞, 何回目, (rc, 標準のエラー))
        self.make_rc = make_rc

    def __call__(self, cmd, cwd, timeout):
        verb = cmd[3]
        folder, out = cmd[-2], cmd[-1]
        listing = sorted(os.listdir(cwd)) if os.path.isdir(cwd) else None
        self.calls.append(dict(cmd=list(cmd), cwd=cwd, timeout=timeout, listing=listing, verb=verb, folder=folder, out=out,
                               folder_files=sorted(os.listdir(folder)) if os.path.isdir(folder) else None))
        n = sum(1 for c in self.calls if c["verb"] == verb)
        if self.fail is not None and self.fail[0] == verb and n == self.fail[1]:
            return self.fail[2][0], self.fail[2][1], False
        fn = self.ms.make_main if cmd[2] == self.ms.SCRIPT_PATH else self.ms.P.build_main
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = fn(list(cmd[4:]))
        return rc, err.getvalue(), False


def doc_run(ms, d, proc=None, runner=None, no=1, a=None, b=None, keep=None, runner_cls=None, rkw=None):
    docs = os.path.join(d, "docs")
    os.makedirs(docs, exist_ok=True)
    zp = os.path.join(docs, "S2FAKE0%d.zip" % no)
    make_doc(zp, no, a, b)
    tool, mv = X.make_tool(d)
    tmp = os.path.join(d, "tmp")
    os.makedirs(tmp, exist_ok=True)
    r = runner or (runner_cls or FactRunner)(mv, **(rkw or {}))
    proc = proc or Proc(ms)
    rec = ms.process_doc(tool, zp, tmp, r, proc=proc, keep=keep)
    return rec, r, proc, zp, tmp


def plan_facts(an):
    return [(f["where"], f["attrs"]["name"], "".join(sorted(f["reasons"]))) for f in an["facts"]]


def row_tuple(r):
    return (r["kind"], r["name"], r["pkind"], list(r["period"]), r["target"], [tuple(x) for x in r["dims"]], r["value"], r["unit"], r["shift"], r["prec"], r["count"])


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XM0-1", (58, None, False)), ("XM0-2", (45, None, False)), ("XM0-3", (None, u"0.5%", True)), ("XM0-4", (None, None, False)), ("XM0-5", (50, None, False)),
                    ("XM0-6", (None, 10, True)), ("XM0-7", (45, None, False)), ("XM0-8", (u"作れた書類の数", None, False)), ("XM0-9", (u"94%", u"98%", False)), ("XM0-10", (u"99%", None, False))])
SEAL_BOUND_TEXT = od([("XM0-1", u"58 本以上"), ("XM0-2", u"45 本以上"), ("XM0-3", u"0.5% 以下"), ("XM0-4", u"(a)(期間が期の表に無い)"), ("XM0-5", u"50 本以上"), ("XM0-6", u"10 本以下"),
                      ("XM0-7", u"45 本以上"), ("XM0-8", u"作れた書類の全部"), ("XM0-9", u"94% 以上 98% 未満"), ("XM0-10", u"99% 以上")])
SEAL_REASON_TEXT = (u"(a) 期間が期の表に無い", u"(b) 文脈の entity が書類の決めと違う", u"(c) 4. の軸に上の member 以外の member が在る・同じ軸が 1 つの文脈に 2 回在る", u"(d) 単位が 4 つの形のどれでもない",
                    u"(e) 数の fact の `format` が `ixt:numdotdecimal` でない", u"(f) 表示の字が「数字と `,` と `.` だけ」でなく、値を作れない", u"(g) 同じ鍵の数の fact の間で、値・単位・表示の位・精度のどれかが違う",
                    u"(h) 空の fact が `name`・`contextRef`・`unitRef`・`xsi:nil` と持ち込みの属性のほかの属性を持つ")


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    x0 = read(XT0_SEAL_REL)
    out_ = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out_.append(u"script の封の commit・path・記録の path が門と違う")
    if (u"`%s`" % RECORD_REL) not in seal:
        out_.append(u"封に記録の path が無い")
    if ms.TOOL_VERSION != u"2.47.5" or u"`arelle-release` の版 `2.47.5`" not in x0:
        out_.append(u"版の字が便 XT0 の封と違う")
    if ms.SHA_P != X.SEAL_SHA_P or (u"`%s`" % X.SEAL_SHA_P) not in x0:
        out_.append(u"ModelValue.py の sha256 が便 XT0 の封と違う")
    if ms.YEAR != u"EDINET-2026" or u"--disclosureSystem EDINET-2026" not in x0:
        out_.append(u"規則の年が便 XT0 の封と違う")
    if ms.TIMEOUT_SEC != 600 or u"1 回の時間の上限は 600 秒" not in x0:
        out_.append(u"時間の上限が便 XT0 の封と違う")
    if ms.DOCS_WANT != 67 or u"便 XG0 と同じ 67 本" not in seal:
        out_.append(u"67 が封と違う")
    if ms.DEV_COUNT != 5 or u"開発の 5 本" not in seal:
        out_.append(u"開発の 5 本が封と違う")
    if ms.PUBLICDOC != u"XBRL/PublicDoc/":
        out_.append(u"PublicDoc の場所が違う")
    if tuple(ms.REASONS) != tuple(u"abcdefgh"):
        out_.append(u"型の外の理由が (a)〜(h) の 8 つでない")
    for t in SEAL_REASON_TEXT:
        if t not in seal:
            out_.append(u"封に型の外の理由の字が無い: %s" % t[:6])
    if (ms.KIND_NUM, ms.KIND_TEXT, ms.TARGET_IND, ms.TARGET_DEF, ms.VALUE_NONE, ms.UNIT_SHARES, ms.UNIT_PURE) != (u"数", u"文", u"個別", u"既定", u"無い", u"株", u"純数"):
        out_.append(u"種類・対象・値の字が封と違う")
    for t in (u"`数` か `文`", u"`個別` か `既定`", u"`無い`(空の fact)", u"`通貨:XXX`", u"`株`", u"`純数`", u"`通貨:XXX÷株`", u"負の印つきの 0 は `-0` と書く"):
        if t not in seal:
            out_.append(u"封に型の欄の字が無い: %s" % t)
    if ms.FORMAT_OK != u"ixt:numdotdecimal" or u"`format` = `ixt:numdotdecimal`" not in seal:
        out_.append(u"format の字が封と違う")
    if ms.AXIS_CONS != u"jppfs_cor:ConsolidatedOrNonConsolidatedAxis" or ms.MEMBER_IND != u"jppfs_cor:NonConsolidatedMember" or (u"`%s`" % ms.AXIS_CONS) not in seal or (u"`%s`" % ms.MEMBER_IND) not in seal:
        out_.append(u"個別の軸・member の字が封と違う")
    if (ms.ID_END, ms.ID_START, ms.ID_FILING) != (u"CurrentYearInstant", u"CurrentYearDuration", u"FilingDateInstant") or any((u"`%s`" % t) not in seal for t in (ms.ID_END, ms.ID_START, ms.ID_FILING)):
        out_.append(u"書類の決めの id の頭が封と違う")
    if (ms.PERIOD_CUR, ms.PERIOD_FILING) != (u"CurrentYear", u"FilingDate") or u"`Prior<N>Year`" not in seal or u"`CurrentYear`" not in seal or u"`FilingDate`" not in seal:
        out_.append(u"期の名が封と違う")
    if tuple(ms.NUM_TYPED) != (u"name", u"contextRef", u"unitRef", u"decimals", u"scale", u"sign", u"format", u"xsi:nil") or tuple(ms.TEXT_TYPED) != (u"name", u"contextRef"):
        out_.append(u"型が持つ属性が封と違う")
    for t in (u"数の fact の、`name`・`contextRef`・`unitRef`・`decimals`・`scale`・`sign`・`format`・`xsi:nil` 以外の属性の全部(持ち込みの属性)", u"文の fact の、`name` と `contextRef` 以外の属性の全部(持ち込みの属性)",
              u"型に入った fact の `name`・`contextRef`・`unitRef`・`decimals`・`scale`・`sign`・数の fact の `format`・`xsi:nil`、文脈の定義、単位の定義"):
        if t not in seal:
            out_.append(u"封に持ち込みの字が無い: %s" % t[:12])
    if dict((k, v) for k, v in ms.CODE_PREFIX.items()) != od([(u"科目", "K"), (u"軸", "A"), (u"member", "M")]) or u"(`K0001`・`A0001`・`M0001` の形)" not in seal:
        out_.append(u"対応表のコードの形が封と違う")
    if ms.MIX_KIND != u"対象を個別に変える" or u"最初の行(型の行の番号の昇順)の対象を `個別` に変えて作り直し" not in seal:
        out_.append(u"混ぜ物の字が封と違う")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out_.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [x for x in seal.splitlines() if re.match(r"^\| %s[^0-9]" % re.escape(k), x)]
        if len(row_) != 1 or t not in row_[0]:
            out_.append(u"封の予測の行の字が違う: %s" % k)
    if ms.make_command(u"F", u"O")[1:] != [u"-I", ms.SCRIPT_PATH, u"make", u"F", u"O"] or ms.make_command(u"F", u"O")[0] != sys.executable:
        out_.append(u"型から作る命令の引数の並びが封と違う")
    if u"別の process で `python3 -I` で走らせる" not in seal or u"元の包み・元の `.htm` を読まない" not in seal:
        out_.append(u"封の型から作る命令の字が違う")
    if u"**持たないもの**: docID・会社の名・EDINET コード・file の名・fact の値・会社の独自の要素の名・文脈の名・日付・本文の字・型と対応表の中身" not in seal:
        out_.append(u"封の記録の禁止の字が違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    want_phrases = (u"型・対応表・持ち込み・型の外は、どれも答え(受理済みの XBRL)から作った", u"型の外の fact は元から写すので、その fact が元と同じになるのは当たり前", u"開発の 5 本を見て決めた",
                    u"比べ方 2 は `contextRef` の字を見ず", u"混ぜ物は 1 本につき 1 つ・対象の欄だけ", u"文の中身と書式の属性は持ち込み")
    got_phrases = (u"どれも答え(受理済みの XBRL)から作った", u"型の外の fact は元から写すので", u"開発の 5 本を見て決めた", u"比べ方 2 は contextRef の字を見ず", u"混ぜ物は 1 本につき 1 つ・対象の欄だけ", u"文の中身と書式の属性は持ち込み")
    if any(p not in sec7 for p in want_phrases) or any(k not in u"".join(ms.LIMITS) for k in got_phrases):
        out_.append(u"限界の字が封 §7 と違う")
    if len(ms.LIMITS) != 6 or u"「XBRL を作れる」「専用の道具が要らない」「どんな資料も作れる」「誤りが無くなる」" not in u"".join(ms.LIMITS):
        out_.append(u"限界に言えないことの字が無い")
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
    pr = X.load_helpers()
    others = list(ORDER_FILES) if others is None else others
    return list(pr.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % x for x in rc.stdout.splitlines() if x.strip()]


# ======================================================================== 2. 規則(部品を 1 つずつ)
def D(d_str):
    import datetime
    return datetime.date(*[int(x) for x in d_str.split("-")])


DEC = od([("scheme", ENT[0]), ("ident", ENT[1]), ("start", u"2025-04-01"), ("end", u"2026-03-31"), ("filing", u"2026-06-30")])


def ctx_dict(per, members=(), ent=ENT, cid=u"X"):
    return od([("type", "context"), ("id", cid), ("scheme", ent[0]), ("ident", ent[1]), ("period", [list(p) for p in per]), ("members", [list(m) for m in members]), ("has_scenario", bool(members))])


def inst(d_str):
    return [("xbrli:instant", d_str)]


def dur(a, b):
    return [("xbrli:startDate", a), ("xbrli:endDate", b)]


def rules_problems(ms=None):
    ms = ms or MS
    out_ = []

    def eq(what, got, want):
        if got != want:
            out_.append(u"%s: %r (手で数えた値は %r)" % (what, got, want))
    # ---- 日(N 年前・月の末日)
    yb = lambda s, n: (lambda r: r.isoformat() if r else None)(ms.years_before(D(s), n))
    eq(u"1 年前", yb(u"2026-03-31", 1), u"2025-03-31")
    eq(u"うるう日の 1 年前は 2 月の末日", yb(u"2024-02-29", 1), u"2023-02-28")
    eq(u"うるう日の 4 年前", yb(u"2024-02-29", 4), u"2020-02-29")
    eq(u"2 月の末日の 1 年前は 2 月の末日", yb(u"2023-02-28", 1), u"2022-02-28")
    eq(u"2 月の末日でない 28 日の 1 年前は同じ日", yb(u"2024-02-28", 1), u"2023-02-28")
    eq(u"4 月の末日の 1 年前", yb(u"2026-04-30", 1), u"2025-04-30")
    eq(u"月の途中の 3 年前", yb(u"2026-06-15", 3), u"2023-06-15")
    eq(u"うるう年の 2 月の末日でない 28 日の 4 年前", yb(u"2024-02-28", 4), u"2020-02-28")
    eq(u"N が 0 は作れない", yb(u"2026-03-31", 0), None)
    eq(u"N が負は作れない", yb(u"2026-03-31", -1), None)
    eq(u"年が 0 になる N は作れない", yb(u"2026-03-31", 2026), None)
    eq(u"年が 1 になる N は作れる", yb(u"2026-03-31", 2025), u"0001-03-31")
    pn = lambda x, b: ms.prior_n(D(x), D(b))
    eq(u"prior_n 1 年", pn(u"2025-03-31", u"2026-03-31"), 1)
    eq(u"prior_n 3 年", pn(u"2023-03-31", u"2026-03-31"), 3)
    eq(u"prior_n 同じ日は無い", pn(u"2026-03-31", u"2026-03-31"), None)
    eq(u"prior_n 日が違う", pn(u"2025-03-30", u"2026-03-31"), None)
    eq(u"prior_n 未来は無い", pn(u"2027-03-31", u"2026-03-31"), None)
    eq(u"prior_n うるう日の末日", pn(u"2023-02-28", u"2024-02-29"), 1)
    eq(u"prior_n うるう日(2 年前の 2 月 28 日は末日でも元がうるう日でない)", pn(u"2022-02-28", u"2024-02-29"), 2)
    eq(u"parse_date 正しい", ms.parse_date(u"2026-03-31"), D(u"2026-03-31"))
    for bad in (u"2026-3-31", u"20260331", u"2026-02-30", u"2026-13-01", u"２０２６-03-31", u"2026-03-31 ", u"", None, 20260331):
        eq(u"parse_date %r は日でない" % (bad,), ms.parse_date(bad), None)
    # ---- 期の名
    pnm = lambda kind, ds, dec=None: ms.period_name(kind, ds, dec or DEC)
    eq(u"当期の終わりの時点", pnm("instant", [u"2026-03-31"]), u"CurrentYear")
    eq(u"提出日の時点", pnm("instant", [u"2026-06-30"]), u"FilingDate")
    eq(u"1 年前の時点", pnm("instant", [u"2025-03-31"]), u"Prior1Year")
    eq(u"2 年前の時点", pnm("instant", [u"2024-03-31"]), u"Prior2Year")
    eq(u"表に無い時点", pnm("instant", [u"2026-02-15"]), None)
    eq(u"当期の期間", pnm("duration", [u"2025-04-01", u"2026-03-31"]), u"CurrentYear")
    eq(u"1 年前の期間", pnm("duration", [u"2024-04-01", u"2025-03-31"]), u"Prior1Year")
    eq(u"2 年前の期間", pnm("duration", [u"2023-04-01", u"2024-03-31"]), u"Prior2Year")
    eq(u"始まりだけ当期の期間", pnm("duration", [u"2025-04-01", u"2025-03-31"]), None)
    eq(u"終わりだけ当期の期間", pnm("duration", [u"2024-04-01", u"2026-03-31"]), None)
    eq(u"始まりが N 年前でない期間", pnm("duration", [u"2024-04-02", u"2025-03-31"]), None)
    eq(u"始まりと終わりの N が違う期間", pnm("duration", [u"2023-04-01", u"2025-03-31"]), None)
    eq(u"終わりが当期の始まりの期間", pnm("duration", [u"2025-04-01", u"2025-04-01"]), None)
    eq(u"始まりと終わりが同じ日の書類の決めでも日が 1 つの期間は当てない", pnm("duration", [u"2026-03-31"], od(DEC, start=u"2026-03-31")), None)
    eq(u"時点の字が日でない", pnm("instant", [u"2026-3-31"]), None)
    eq(u"期間の字が日でない", pnm("duration", [u"2025-04-01", u"x"]), None)
    eq(u"時点の種類に日が 2 つ", pnm("instant", [u"2026-03-31", u"2026-03-31"]), None)
    eq(u"期間の種類に日が 1 つ", pnm("duration", [u"2026-03-31"]), None)
    eq(u"知らない種類", pnm("forever", []), None)
    same = od(DEC, filing=u"2026-03-31")
    eq(u"当期の終わりと提出日が同じ日なら当期を先に当てる", pnm("instant", [u"2026-03-31"], same), u"CurrentYear")
    leap = od([("scheme", ENT[0]), ("ident", ENT[1]), ("start", u"2023-03-01"), ("end", u"2024-02-29"), ("filing", u"2024-06-30")])
    eq(u"うるう日の末日: 時点の 1 年前", pnm("instant", [u"2023-02-28"], leap), u"Prior1Year")
    eq(u"うるう日の末日: 期間の 1 年前", pnm("duration", [u"2022-03-01", u"2023-02-28"], leap), u"Prior1Year")
    eq(u"うるう日の末日: 時点の 4 年前", pnm("instant", [u"2020-02-29"], leap), u"Prior4Year")
    eq(u"提出日が末日でも N 年前には当たらない", pnm("instant", [u"2025-06-30"], leap), None)
    eq(u"書類の決めの日が日でない", pnm("instant", [u"2026-03-31"], od(DEC, end=u"x")), None)
    eq(u"書類の決めの提出日が日でない", pnm("instant", [u"2026-03-31"], od(DEC, filing=u"x")), None)
    eq(u"書類の決めの始まりが日でない", pnm("instant", [u"2026-03-31"], od(DEC, start=u"x")), None)
    # ---- 単位
    uf = lambda **kw: ms.unit_form(dict(kw))
    eq(u"通貨", uf(measures=["iso4217:JPY"], divide=None), u"通貨:JPY")
    eq(u"通貨(JPY 以外)", uf(measures=["iso4217:USD"], divide=None), u"通貨:USD")
    eq(u"株", uf(measures=["xbrli:shares"], divide=None), u"株")
    eq(u"純数", uf(measures=["xbrli:pure"], divide=None), u"純数")
    eq(u"通貨÷株", uf(measures=[], divide={"num": ["iso4217:JPY"], "den": ["xbrli:shares"]}), u"通貨:JPY÷株")
    eq(u"measure が 2 つ", uf(measures=["iso4217:JPY", "xbrli:shares"], divide=None), None)
    eq(u"measure が無い", uf(measures=[], divide=None), None)
    eq(u"知らない measure", uf(measures=["foo:bar"], divide=None), None)
    eq(u"通貨の字が空", uf(measures=["iso4217:"], divide=None), None)
    eq(u"通貨の字に :", uf(measures=["iso4217:J:P"], divide=None), None)
    eq(u"通貨の字に空白", uf(measures=["iso4217:J P"], divide=None), None)
    eq(u"分母が株でない", uf(measures=[], divide={"num": ["iso4217:JPY"], "den": ["xbrli:pure"]}), None)
    eq(u"分子が通貨でない", uf(measures=[], divide={"num": ["xbrli:shares"], "den": ["xbrli:shares"]}), None)
    eq(u"分子が 2 つ", uf(measures=[], divide={"num": ["iso4217:JPY", "iso4217:USD"], "den": ["xbrli:shares"]}), None)
    eq(u"分母が 2 つ", uf(measures=[], divide={"num": ["iso4217:JPY"], "den": ["xbrli:shares", "xbrli:shares"]}), None)
    eq(u"割り算と measure の両方", uf(measures=["iso4217:JPY"], divide={"num": ["iso4217:JPY"], "den": ["xbrli:shares"]}), None)
    eq(u"分母が通貨", uf(measures=[], divide={"num": ["iso4217:USD"], "den": ["iso4217:JPY"]}), None)
    for form, uid, shape in ((u"通貨:JPY", u"JPY", (["iso4217:JPY"], None)), (u"通貨:USD", u"USD", (["iso4217:USD"], None)), (u"株", u"shares", (["xbrli:shares"], None)), (u"純数", u"pure", (["xbrli:pure"], None)),
                             (u"通貨:JPY÷株", u"JPYPerShares", ([], {"num": ["iso4217:JPY"], "den": ["xbrli:shares"]})), (u"通貨:EUR÷株", u"EURPerShares", ([], {"num": ["iso4217:EUR"], "den": ["xbrli:shares"]}))):
        got_id, got_def = ms.unit_from_form(form)
        eq(u"単位の id %s" % form, got_id, uid)
        eq(u"単位の定義 %s" % form, (got_def["type"], got_def["id"], got_def["measures"], None if got_def["divide"] is None else dict(got_def["divide"])), (u"unit", uid, shape[0], shape[1]))
        eq(u"単位の形 → 定義 → 形 %s" % form, ms.unit_form(got_def), form)
    for bad in (u"通貨:", u"通貨", u"株株", u"通貨:J:P", u"純", u"", None, 5, u"通貨:JPY÷", u"通貨:J PY"):
        if not stops_refuse(ms, ms.unit_from_form, bad):
            out_.append(u"知らない単位の形 %r を断らない" % (bad,))
    eq(u"単位の字(通貨)", ms.unit_text(dict(measures=["iso4217:JPY"], divide=None)), u"iso4217:JPY")
    eq(u"単位の字(割り算)", ms.unit_text(dict(measures=[], divide={"num": ["iso4217:JPY"], "den": ["xbrli:shares"]})), u"iso4217:JPY/xbrli:shares")
    eq(u"単位の字(measure 2 つ)", ms.unit_text(dict(measures=["a", "b"], divide=None)), u"a,b")
    eq(u"単位の中身は id を含まない", ms.canon_unit(dict(measures=["a"], divide=None, id=u"x")), ms.canon_unit(dict(measures=["a"], divide=None, id=u"y")))
    if ms.canon_unit(dict(measures=["a"], divide=None)) == ms.canon_unit(dict(measures=["b"], divide=None)) or ms.canon_unit(dict(measures=[], divide={"num": ["a"], "den": ["b"]})) == ms.canon_unit(dict(measures=[], divide={"num": ["b"], "den": ["a"]})):
        out_.append(u"単位の中身の比べが measure・分子と分母の違いを見ない")
    # ---- member の字・文脈の id・定義
    for m, want in ((u"jppfs_cor:NonConsolidatedMember", u"NonConsolidatedMember"), (u"jpcrp030000-asr_E99991-000:AMember", u"jpcrp030000-asr_E99991-000AMember"), (u"foo_cor_x:Bar", u"foo_cor_xBar"),
                    (u"xcor:Q", u"xcorQ"), (u"NoColon", u"NoColon"), (u"_cor:Z", u"Z"), (u"a:b:c", u"ab:c")):
        eq(u"member の字 %s" % m, ms.member_str(m), want)
    cid = lambda p, k, mem: ms.context_id(p, k, mem)
    eq(u"id 時点・次元なし", cid(u"CurrentYear", "instant", []), u"CurrentYearInstant")
    eq(u"id 期間・次元なし", cid(u"Prior1Year", "duration", []), u"Prior1YearDuration")
    eq(u"id 個別", cid(u"CurrentYear", "instant", [(CA, NM)]), u"CurrentYearInstant_NonConsolidatedMember")
    eq(u"id 個別が先(入力の並びに依らない)", cid(u"CurrentYear", "duration", [(COMP, CAP), (CA, NM)]), u"CurrentYearDuration_NonConsolidatedMember_CapitalStockMember")
    eq(u"id 次元は軸の名の昇順", cid(u"CurrentYear", "instant", [(COMP, CAP), (SEG, MEM_A)]), u"CurrentYearInstant_jpcrp030000-asr_E99991-000AMember_CapitalStockMember")
    eq(u"id 軸の名の昇順(入力の並びを逆にしても同じ)", cid(u"CurrentYear", "instant", [(SEG, MEM_A), (COMP, CAP)]), u"CurrentYearInstant_jpcrp030000-asr_E99991-000AMember_CapitalStockMember")
    eq(u"id 個別 + 次元 2 つ", cid(u"FilingDate", "instant", [(COMP, CAP), (CA, NM), (SEG, MEM_A)]), u"FilingDateInstant_NonConsolidatedMember_jpcrp030000-asr_E99991-000AMember_CapitalStockMember")
    cd = ms.context_def(u"I", DEC, "instant", [u"2026-03-31"], [(COMP, CAP), (CA, NM), (SEG, MEM_A)])
    eq(u"定義の member は軸の名の昇順(個別の軸も同じ並びの中)", cd["members"], [[SEG, MEM_A], [COMP, CAP], [CA, NM]] if SEG < COMP < CA else None)
    if not (SEG < COMP < CA):
        out_.append(u"手で決めた軸の並びの前提が違う")
    eq(u"定義の中身(時点)", (cd["type"], cd["id"], cd["scheme"], cd["ident"], cd["period"], cd["has_scenario"]), (u"context", u"I", ENT[0], ENT[1], [["xbrli:instant", u"2026-03-31"]], True))
    cd2 = ms.context_def(u"D", DEC, "duration", [u"2025-04-01", u"2026-03-31"], [])
    eq(u"定義の中身(期間・member なし)", (cd2["period"], cd2["members"], cd2["has_scenario"]), ([["xbrli:startDate", u"2025-04-01"], ["xbrli:endDate", u"2026-03-31"]], [], False))
    eq(u"文脈の中身は id を含まない", ms.canon_ctx(ctx_dict(inst(u"2026-03-31"), cid=u"a")), ms.canon_ctx(ctx_dict(inst(u"2026-03-31"), cid=u"b")))
    eq(u"文脈の中身は member の並びを含まない", ms.canon_ctx(ctx_dict(inst(u"2026-03-31"), [(COMP, CAP), (CA, NM)])), ms.canon_ctx(ctx_dict(inst(u"2026-03-31"), [(CA, NM), (COMP, CAP)])))
    for a_, b_ in ((ctx_dict(inst(u"2026-03-31")), ctx_dict(inst(u"2026-03-30"))), (ctx_dict(inst(u"2026-03-31")), ctx_dict(inst(u"2026-03-31"), [(CA, NM)])), (ctx_dict(inst(u"2026-03-31")), ctx_dict(inst(u"2026-03-31"), ent=(ENT[0], u"E1"))),
                   (ctx_dict(inst(u"2026-03-31")), ctx_dict(inst(u"2026-03-31"), ent=(u"x", ENT[1]))), (ctx_dict(dur(u"2025-04-01", u"2026-03-31")), ctx_dict(dur(u"2025-04-02", u"2026-03-31")))):
        if ms.canon_ctx(a_) == ms.canon_ctx(b_):
            out_.append(u"文脈の中身の比べが期・member・提出者の違いを見ない")
    # ---- 文脈の読み(理由 (a)(b)(c))
    ci = lambda c: (lambda r: (sorted(r[0]), r[1], r[2], r[3], r[4], r[5]))(ms.ctx_info(c, DEC))
    eq(u"文脈: 当期の時点", ci(ctx_dict(inst(u"2026-03-31"))), ([], "instant", [u"2026-03-31"], u"CurrentYear", u"既定", []))
    eq(u"文脈: 個別", ci(ctx_dict(inst(u"2026-03-31"), [(CA, NM)]))[4:], (u"個別", []))
    eq(u"文脈: 個別 + 次元(次元は軸の名の昇順)", ci(ctx_dict(inst(u"2026-03-31"), [(COMP, CAP), (SEG, MEM_A), (CA, NM)]))[4:], (u"個別", [(SEG, MEM_A), (COMP, CAP)]))
    eq(u"文脈: 期の表に無い (a)", ci(ctx_dict(inst(u"2026-02-15")))[0], ["a"])
    eq(u"文脈: forever (a)", ci(ctx_dict([("xbrli:forever", u"")]))[0], ["a"])
    eq(u"文脈: 期の字が日でない (a)", ci(ctx_dict(inst(u"x")))[0], ["a"])
    eq(u"文脈: 提出者の識別子が違う (b)", ci(ctx_dict(inst(u"2026-03-31"), ent=(ENT[0], u"E1")))[0], ["b"])
    eq(u"文脈: scheme が違う (b)", ci(ctx_dict(inst(u"2026-03-31"), ent=(u"x", ENT[1])))[0], ["b"])
    eq(u"文脈: 個別の軸に別の member (c)", ci(ctx_dict(inst(u"2026-03-31"), [(CA, u"jppfs_cor:ConsolidatedMember")]))[0], ["c"])
    eq(u"文脈: 同じ軸が 2 回 (c)", ci(ctx_dict(inst(u"2026-03-31"), [(COMP, CAP), (COMP, RET)]))[0], ["c"])
    eq(u"文脈: 同じ軸・同じ member が 2 回 (c)", ci(ctx_dict(inst(u"2026-03-31"), [(COMP, CAP), (COMP, CAP)]))[0], ["c"])
    eq(u"文脈: 個別の軸が 2 回 (c)", ci(ctx_dict(inst(u"2026-03-31"), [(CA, NM), (CA, NM)]))[0], ["c"])
    eq(u"文脈: (a)(b)(c) の全部", ci(ctx_dict(inst(u"2026-02-15"), [(CA, u"x:y")], ent=(u"x", u"y")))[0], ["a", "b", "c"])
    # ---- 数の fact の読み(理由 (d)〜(h))
    units = {u"JPY": dict(type="unit", id=u"JPY", measures=["iso4217:JPY"], divide=None), u"pure": dict(type="unit", id=u"pure", measures=["xbrli:pure"], divide=None),
             u"X": dict(type="unit", id=u"X", measures=["foo:bar"], divide=None)}
    base = {"name": u"n", "contextRef": u"c", "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK}

    def jn(content, **kw):
        a = dict(base)
        for k, v in kw.items():
            if v is None:
                a.pop(k, None)
            else:
                a[k.replace("_", ":") if k == "xsi_nil" else k] = v
        r = ms.judge_number(a, content, units)
        return (sorted(r[0]), r[2], r[3], r[4], r[5], r[6])
    eq(u"数: 正しい", jn(u"1,234", scale=u"3", decimals=u"-3"), ([], u"1234000", u"通貨:JPY", 3, -3, False))
    eq(u"数: 負", jn(u"1,500", sign=u"-"), ([], u"-1500", u"通貨:JPY", 0, 0, False))
    eq(u"数: 負の 0 は -0", jn(u"0", sign=u"-")[1], u"-0")
    eq(u"数: 正の 0 は 0", jn(u"0")[1], u"0")
    eq(u"数: scale が無いなら 0", jn(u"5", scale=None), ([], u"5", u"通貨:JPY", 0, 0, False))
    eq(u"数: 単位が定義に無い (d)", jn(u"5", unitRef=u"Z")[0], ["d"])
    eq(u"数: unitRef が無い (d)", jn(u"5", unitRef=None)[0], ["d"])
    eq(u"数: 単位が 4 つの形でない (d)", jn(u"5", unitRef=u"X")[0], ["d"])
    eq(u"数: 純数", jn(u"5", unitRef=u"pure")[2], u"純数")
    eq(u"数: format が違う (e)", jn(u"5", format=u"ixt:numcommadecimal")[0], ["e"])
    eq(u"数: format が無い (e)", jn(u"5", format=None)[0], ["e"])
    eq(u"数: decimals が無い (e)", jn(u"5", decimals=None)[0], ["e"])
    eq(u"数: decimals が整数でない (e)", jn(u"5", decimals=u"INF")[0], ["e"])
    eq(u"数: decimals が 3.0 (e)", jn(u"5", decimals=u"3.0")[0], ["e"])
    eq(u"数: scale が整数でない (e)", jn(u"5", scale=u"1e3")[0], ["e"])
    eq(u"数: scale が + 付き (e)", jn(u"5", scale=u"+3")[0], ["e"])
    eq(u"数: scale が 1000 (守りの境の内)", jn(u"5", scale=u"1000")[0], [])
    eq(u"数: scale が 1001 (守りの境の外 e)", jn(u"5", scale=u"1001")[0], ["e"])
    eq(u"数: decimals が -1000 (境の内)", jn(u"5", decimals=u"-1000")[0], [])
    eq(u"数: decimals が -1001 (境の外 e)", jn(u"5", decimals=u"-1001")[0], ["e"])
    eq(u"数: 字が 1.5.2 (f)", jn(u"1.5.2")[0], ["f"])
    eq(u"数: 字が △5 (f)", jn(u"△5")[0], ["f"])
    eq(u"数: 字が空 (f)", jn(u"")[0], ["f"])
    eq(u"数: 字が - (f)", jn(u"-")[0], ["f"])
    eq(u"数: 字が .5 (f)", jn(u".5")[0], ["f"])
    eq(u"数: 字が 5. (f)", jn(u"5.")[0], ["f"])
    eq(u"数: 字に空白 (f)", jn(u" 5")[0], ["f"])
    eq(u"数: 全角の数字 (f)", jn(u"５")[0], ["f"])
    eq(u"数: sign が + (f)", jn(u"5", sign=u"+")[0], ["f"])
    eq(u"数: sign が空 (f)", jn(u"5", sign=u"")[0], ["f"])
    eq(u"数: 桁の区切りだけ", jn(u",,5")[1], u"5")
    eq(u"数: 小数", jn(u"12.34", decimals=u"2")[1], u"12.34")
    eq(u"数: 末尾の 0 は落とす", jn(u"0.500", decimals=u"3")[1], u"0.5")
    eq(u"数: 負の scale", jn(u"1,234.5", scale=u"-1", decimals=u"2")[1], u"123.45")
    eq(u"数: 大きい値", jn(u"123456789012345678901234567890", scale=u"6")[1], u"123456789012345678901234567890000000")
    eq(u"数: (e) と (f) が重なる", jn(u"△5", format=None)[0], ["e", "f"])
    eq(u"数: (d)(e)(f) の全部", jn(u"△5", format=None, unitRef=None)[0], ["d", "e", "f"])
    eq(u"数: (e) の decimals の不正のとき値は作らず字の検査は続ける", jn(u"1.5.2", decimals=u"x")[0], ["e", "f"])
    eq(u"空: 正しい", jn(u"", format=None, decimals=None, scale=None, xsi_nil=u"true"), ([], u"無い", u"通貨:JPY", None, None, True))
    eq(u"空: format を持つのは (h)(e の外)", jn(u"", decimals=None, scale=None, xsi_nil=u"true")[0], ["h"])
    eq(u"空: decimals を持つ (h)", jn(u"", format=None, scale=None, xsi_nil=u"true")[0], ["h"])
    eq(u"空: scale を持つ (h)", jn(u"", format=None, decimals=None, xsi_nil=u"true")[0], ["h"])
    eq(u"空: sign を持つ (h)", jn(u"", format=None, decimals=None, scale=None, sign=u"-", xsi_nil=u"true")[0], ["h"])
    eq(u"空: xsi:nil が true でない (h)", jn(u"", format=None, decimals=None, scale=None, xsi_nil=u"false")[0], ["h"])
    eq(u"空: 単位が無い (d)", jn(u"", format=None, decimals=None, scale=None, unitRef=None, xsi_nil=u"true")[0], ["d"])
    eq(u"空: 本文の字は見ない", jn(u"△", format=None, decimals=None, scale=None, xsi_nil=u"true")[0], [])
    # ---- 値 → 表示の字
    for what, args, want in ((u"千", (u"1234000", 3, -3), u"1,234"), (u"-0", (u"-0", 0, 0), u"0"), (u"小数 3 桁", (u"0.5", 0, 3), u"0.500"), (u"小数 2 桁", (u"12.34", 0, 2), u"12.34"),
                             (u"負の scale", (u"123.45", -1, 2), u"1,234.5"), (u"百万", (u"1000000", 6, -6), u"1"), (u"精度が負で位が 0", (u"5", 0, -2), u"5"), (u"負は大きさだけ", (u"-1500", 0, 0), u"1,500"),
                             (u"桁区切り 3 回", (u"1234567890", 0, 0), u"1,234,567,890"), (u"位 > 精度の和が正", (u"1234", 0, 1), u"1,234.0"), (u"大きい", (u"123456789012345678901234567890", 0, 0), u"123,456,789,012,345,678,901,234,567,890")):
        eq(u"表示の字: %s" % what, ms.display_text(*args), want)
    return out_


def stops_refuse(ms, fn, *a):
    try:
        fn(*a)
    except ms.Refuse:
        return True
    return False


def int_problems(ms=None):
    ms = ms or MS
    out_ = []
    for s, want in ((u"0", 0), (u"-3", -3), (u"1000", 1000), (u"-1000", -1000), (u"1001", None), (u"-1001", None), (u"abc", None), (u"+3", None), (u" 3", None), (u"٣", None), (u"", None), (None, None), (u"-0", 0), (u"3.0", None), (u"--3", None), (3, None)):
        if ms.int_attr(s) != want:
            out_.append(u"int_attr(%r) = %r (手で決めた値は %r)" % (s, ms.int_attr(s), want))
    for content, shift, sign, want in ((u"1,234", 3, None, u"1234000"), (u"0", 0, u"-", u"-0"), (u"0.50", 0, None, u"0.5"), (u"12.34", 0, u"-", u"-12.34"), (u"12", -2, None, u"0.12"), (u"100", 2, None, u"10000"),
                                       (u"0.0", 5, None, u"0"), (u"1.5.2", 0, None, None), (u"", 0, None, None), (None, 0, None, None), (u"△5", 0, None, None), (u"5", 0, u"-", u"-5"), (u"5", 0, u"+", u"5"), (u"00012", 0, None, u"12"),
                                       (u"0.00", 3, u"-", u"-0")):
        got = ms.number_value(content, shift, sign)
        if got != want:
            out_.append(u"number_value(%r, %r, %r) = %r (手で決めた値は %r)" % (content, shift, sign, got, want))
    return out_


# ======================================================================== 3. 型を作る(解析・folder)
OUT_COUNTS = {"a": (2, 1), "b": (1, 1), "c": (2, 0), "d": (3, 0), "e": (5, 0), "f": (3, 0), "g": (10, 0), "h": (2, 0)}
K_TABLE = od([("K0001", u"jpcrp_cor:Nest"), ("K0002", u"jpcrp_cor:NilText"), ("K0003", u"jpcrp_cor:Text"), ("K0004", u"jpdei_cor:FilingText"), ("K0005", u"jppfs_cor:Assets"), ("K0006", u"jppfs_cor:BOnly"),
              ("K0007", u"jppfs_cor:Carry"), ("K0008", u"jppfs_cor:EPS"), ("K0009", u"jppfs_cor:Equity"), ("K0010", u"jppfs_cor:Inner"), ("K0011", u"jppfs_cor:NoScale"), ("K0012", u"jppfs_cor:Profit"),
              ("K0013", u"jppfs_cor:Ratio"), ("K0014", u"jppfs_cor:Receivable"), ("K0015", u"jppfs_cor:Seg"), ("K0016", u"jppfs_cor:Shares"), ("K0017", u"jppfs_cor:Zero")])
MAP_PLAN = od([(u"科目", K_TABLE), (u"軸", od([("A0001", SEG), ("A0002", COMP)])), (u"member", od([("M0001", MEM_A), ("M0002", CAP)]))])
CODE_OF = dict((v, k) for tab in MAP_PLAN.values() for k, v in tab.items())
FOLDER_FILES = [u"c0000.json", u"c0001.json", u"index.json", u"map.json", u"outside.json", u"t0000.txt", u"t0001.txt", u"taxonomy.json", u"type.json"]


def row_json_plan(row):
    kind, name, pkind, period, target, dims, value, unit, shift, prec, _cnt = row
    o = od([("kind", kind), ("code", CODE_OF[name]), ("period", period), ("pkind", pkind), ("target", target), ("dims", [[CODE_OF[a], CODE_OF[m]] for a, m in dims])])
    if kind == u"数":
        o["value"], o["unit"] = value, unit
        if value != u"無い":
            o["shift"], o["prec"] = shift, prec
    return o


def analyze_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        _zp, _ent, _files, tf, an = derive_doc(d, ms)
        got = plan_facts(an)
        for i, (g, w) in enumerate(zip(got, FACT_PLAN)):
            if g != w:
                out_.append(u"対象の fact %d の判定が手で決めた値と違う: %s ≠ %s" % (i, g, w))
        if len(got) != len(FACT_PLAN):
            out_.append(u"対象の fact の数が違う: %d" % len(got))
        rows = [row_tuple(r) for r in an["rows"]]
        if rows != ROW_PLAN:
            for i, (g, w) in enumerate(zip(rows, ROW_PLAN)):
                if g != w:
                    out_.append(u"型の行 %d が手で決めた値と違う: %s ≠ %s" % (i, g, w))
            if len(rows) != len(ROW_PLAN):
                out_.append(u"型の行の数が違う: %d" % len(rows))
        if dict(an["dec"]) != dict(DEC) or an["hosts"] != [0]:
            out_.append(u"書類の決め・resources の部を持つ file が違う: %s %s" % (dict(an["dec"]), an["hosts"]))
        if [f["row"] for f in an["facts"] if "row" in f][:3] != [0, 0, 1]:
            out_.append(u"fact → 型の行の番号が違う")
        if [f["out"] for f in an["outside"]] != list(range(29)):
            out_.append(u"型の外の番号が並びの順でない")
        if [f["row"] for f in an["facts"] if "row" in f][-1] != 19 or sum(1 for f in an["facts"] if "row" in f) != 25:
            out_.append(u"型に入った fact の数が違う")
        maps, inv = ms.code_maps(an["rows"])
        if dict((k, dict(v)) for k, v in maps.items()) != dict((k, dict(v)) for k, v in MAP_PLAN.items()):
            out_.append(u"対応表が手で決めた表と違う: %s" % dict(maps))
        if [ms.row_to_json(r, inv) for r in an["rows"]] != [row_json_plan(r) for r in ROW_PLAN]:
            out_.append(u"folder に書く型の行が手で決めた値と違う")
        for r in ROW_PLAN:
            j = row_json_plan(r)
            if (u"value" in j) != (r[0] == u"数") or (u"shift" in j) != (r[0] == u"数" and r[6] != u"無い"):
                out_.append(u"型の行の欄が種類・空と合わない")
        carried = [ms.carried_attrs(f) for f in an["facts"] if "row" in f]
        for i, c in enumerate(carried):
            name = [f for f in an["facts"] if "row" in f][i]["attrs"]["name"]
            want = {u"jppfs_cor:Carry": {"footnoteRefs": "fn1", "id": "f9"}}.get(name, {})
            if name == u"jpcrp_cor:Text":
                want = {"escape": "true"} if c.get("escape") else {"id": "t2"}
            if name == u"jpcrp_cor:NilText":
                want = {"xsi:nil": "true"}
            if c != want:
                out_.append(u"持ち込みの属性が違う: %s %s" % (name, c))
    # ---- 断り
    def refusal(a=None, b=None):
        with Temp() as d2:
            _zp, ent, files, names, tables = peel_doc(d2, ms, a, b)
            try:
                ms.analyze(files)
            except ms.Refuse as exc:
                return exc.reason
            return None
    cases = [
        (u"文脈の定義が無い fact", dict(a=HTM_A_TEXT.replace(u'contextRef="OddInstant"', u'contextRef="Nowhere"', 1)), u"文脈の定義が無い fact"),
        (u"当期の終わりの文脈が無い", dict(a=HTM_A_TEXT.replace(u"CurrentYearInstant", u"CurYI")), u"書類の決めが 1 通りに決まらない"),
        (u"当期の始まりの文脈が無い", dict(a=HTM_A_TEXT.replace(u"CurrentYearDuration", u"CurYD")), u"書類の決めが 1 通りに決まらない"),
        (u"提出日の文脈が無い", dict(a=HTM_A_TEXT.replace(u"FilingDateInstant", u"FilYI")), u"書類の決めが 1 通りに決まらない"),
        (u"当期の終わりの日が 2 つ", dict(a=HTM_A_TEXT.replace(u"<xbrli:instant>2026-03-31</xbrli:instant>\n</xbrli:period>\n<xbrli:scenario>\n<xbrldi:explicitMember dimension=\"%s\">%s</xbrldi:explicitMember>\n</xbrli:scenario>\n</xbrli:context>\n<xbrli:context id=\"%s\">" % (CA, NM, CYI_SEG),
                                                           u"<xbrli:instant>2026-03-30</xbrli:instant>\n</xbrli:period>\n<xbrli:scenario>\n<xbrldi:explicitMember dimension=\"%s\">%s</xbrldi:explicitMember>\n</xbrli:scenario>\n</xbrli:context>\n<xbrli:context id=\"%s\">" % (CA, NM, CYI_SEG), 1)),
         u"書類の決めが 1 通りに決まらない"),
        (u"当期の終わりの日が日でない", dict(a=HTM_A_TEXT.replace(u"<xbrli:instant>2026-03-31</xbrli:instant>", u"<xbrli:instant>2026-3-31</xbrli:instant>", 1)), u"書類の決めが 1 通りに決まらない"),
        (u"当期の終わりの文脈の提出者が 2 つ", dict(a=HTM_A_TEXT.replace(u'<xbrli:context id="%s">\n<xbrli:entity>\n<xbrli:identifier scheme="http://example.org/id">E99991-000' % CYI_NC, u'<xbrli:context id="%s">\n<xbrli:entity>\n<xbrli:identifier scheme="http://example.org/id">E99992-000' % CYI_NC, 1)),
         u"書類の決めの提出者が 1 通りに決まらない"),
        (u"CurrentYearInstant の頭の id の文脈が期間", dict(a=HTM_A_TEXT.replace(u"<xbrli:instant>2026-03-31</xbrli:instant>\n</xbrli:period>\n<xbrli:scenario>\n<xbrldi:explicitMember dimension=\"%s\">%s</xbrldi:explicitMember>\n<xbrldi:explicitMember dimension=\"%s\">%s</xbrldi:explicitMember>" % (SEG, MEM_A, CA, NM),
                                                                                  u"<xbrli:startDate>2026-03-31</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate>\n</xbrli:period>\n<xbrli:scenario>\n<xbrldi:explicitMember dimension=\"%s\">%s</xbrldi:explicitMember>\n<xbrldi:explicitMember dimension=\"%s\">%s</xbrldi:explicitMember>" % (SEG, MEM_A, CA, NM), 1)),
         u"書類の決めの文脈の期の形が違う"),
        (u"CurrentYearDuration の頭の id の文脈が時点", dict(a=HTM_A_TEXT.replace(u"<xbrli:startDate>2025-04-01</xbrli:startDate>\n<xbrli:endDate>2026-03-31</xbrli:endDate>", u"<xbrli:instant>2026-03-31</xbrli:instant>", 1)), u"書類の決めの文脈の期の形が違う"),
        (u"同じ id で中身が違う文脈", dict(a=HTM_A_TEXT.replace(u"</ix:resources>", cx(CYD, ("d", u"2020-04-01", u"2021-03-31")) + u"\n</ix:resources>")), u"文脈の id が重なる"),
        (u"同じ id で中身が違う単位", dict(a=HTM_A_TEXT.replace(u"</ix:resources>", un(u"JPY", u"iso4217:USD") + u"\n</ix:resources>")), u"単位の id が重なる"),
        (u"resources の部が 2 つの file に在る", dict(b=u"<html><body><ix:header>\n<ix:resources>\n</ix:resources>\n</ix:header></body></html>"), u"resources の部が 2 つ以上"),
        (u"fact に name が無い", dict(a=HTM_A_TEXT.replace(u'name="jppfs_cor:Zero" ', u"", 1)), u"fact に name が無い")]
    for what, kw, want in cases:
        got = refusal(**kw)
        if got != want:
            out_.append(u"断り(%s): %r (手で決めた理由は %r)" % (what, got, want))
    for what, a_ in ((u"提出日の文脈だけ提出者が違う", HTM_A_TEXT.replace(cx(FDI, ("i", u"2026-06-30")), cx(FDI, ("i", u"2026-06-30"), ent=(ENT[0], u"E88888-000")))),
                     (u"当期の期間の文脈だけ提出者が違う", HTM_A_TEXT.replace(cx(CYD, ("d", u"2025-04-01", u"2026-03-31")), cx(CYD, ("d", u"2025-04-01", u"2026-03-31"), ent=(ENT[0], u"E88888-000"))))):
        if a_ == HTM_A_TEXT:
            out_.append(u"作り物の置き換えが効いていない: %s" % what)
        got = refusal(a=a_)
        if got is not None:
            out_.append(u"%s のを断った(提出者は CurrentYearInstant の頭の文脈だけで決める): %s" % (what, got))
    ok_dup = refusal(a=HTM_A_TEXT.replace(u"</ix:resources>", cx(CYD, ("d", u"2025-04-01", u"2026-03-31")) + u"\n" + un(u"JPY", u"iso4217:JPY") + u"\n</ix:resources>"))
    if ok_dup is not None:
        out_.append(u"同じ id で同じ中身の文脈・単位を断った: %s" % ok_dup)
    return out_


def folder_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        zp, ent, files, tf, an = derive_doc(d, ms)
        if sorted(os.listdir(tf)) != FOLDER_FILES:
            out_.append(u"型の folder の file の集まりが違う: %s" % sorted(os.listdir(tf)))
        idx = jread(tf, "index.json")
        if [(h["name"], h["text"], h["carry"]) for h in idx["htm"]] != [(u"0100000_a_E99991-000_ixbrl.htm", u"t0000.txt", u"c0000.json"), (u"0200000_b_E99991-000_ixbrl.htm", u"t0001.txt", u"c0001.json")]:
            out_.append(u"目次の htm が違う")
        if idx["taxonomy"]["file"] != u"taxonomy.json" or list(idx["taxonomy"]["names"]) != list(KINDS) or any(not v.startswith(u"jpcrp030000-asr-001_E99991-000") for v in idx["taxonomy"]["names"].values()):
            out_.append(u"目次のタクソノミが違う(PublicDoc の直下からの相対の名でない)")
        for i in (0, 1):
            raw = read_file(os.path.join(tf, "t%04d.txt" % i))
            if raw != files[i][1].encode("utf-8") or b"<ix:" in raw or b"xbrli:" in raw:
                out_.append(u"素の本文が元の本文からタグを除いた字でない(%d)" % i)
        typ = jread(tf, "type.json")
        if dict(typ["decision"]) != dict(DEC) or typ["rows"] != [row_json_plan(r) for r in ROW_PLAN] or list(typ) != ["decision", "rows"]:
            out_.append(u"type.json の決め・型の行が手で決めた値と違う")
        tbytes = read_file(os.path.join(tf, "type.json")).decode("utf-8")
        for leak in (u"jppfs_cor", u"jpcrp", u"xbrli", u"contextRef", u"unitRef", u"CurrentYear", u"Prior1Year", u"http"):
            if leak in tbytes.replace(ENT[0], u"").replace(ENT[1], u""):
                out_.append(u"type.json に元の名・文脈の名・属性の名が在る: %s" % leak)
        mp = jread(tf, "map.json")
        if dict((k, dict(v)) for k, v in mp.items()) != dict((k, dict(v)) for k, v in MAP_PLAN.items()) or list(mp) != [u"科目", u"軸", u"member"]:
            out_.append(u"map.json が手で決めた表と違う")
        # 持ち込み
        carry_raw = u"".join(read_file(os.path.join(tf, n)).decode("utf-8") for n in ("c0000.json", "c0001.json"))
        for leak in (u'"contextRef"', u'"unitRef"', u'"decimals"', u'"scale"', u'"sign"', u'"format"', u"xbrli:", u"CurrentYear", u"FilingDate", u"Prior1Year", u'"context"', u'"unit"', u"iso4217", u"explicitMember", u"OtherEntity"):
            if leak in carry_raw:
                out_.append(u"持ち込みに入れないものが在る: %s" % leak)
        if ms.carry_forbidden(tf) != []:
            out_.append(u"きれいな folder で carry_forbidden が何かを言う: %s" % ms.carry_forbidden(tf))
        c0 = jread(tf, "c0000.json")
        F0 = c0["F"]
        if len(F0) != 49 or [e["kind"] for e in F0].count("footnote") != 1 or c0["H"]["pos"] != files[0][3]["pos"] or c0["H"]["before"] != 0:
            out_.append(u"持ち込みの表 F・表 H の欄が違う")
        by = [(e.get("row"), e.get("out"), e.get("carry")) for e in F0]
        want_rows = [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        if [b[0] for b in by[:11]] != want_rows or any(b[1] is not None for b in by[:11]):
            out_.append(u"持ち込みの fact の型の行の番号が違う")
        if [b[1] for b in by[11:35]] != list(range(0, 24)) or any(b[0] is not None for b in by[11:35]):
            out_.append(u"持ち込みの型の外の番号が違う")
        if by[35][0] != 10 or by[36] != (11, None, {"footnoteRefs": "fn1", "id": "f9"}) or by[37][2] != {"escape": "true"} or by[38][2] != {"id": "t2"} or by[38][0] != 12 or by[39][2] != {"xsi:nil": "true"} or by[39][0] != 13:
            out_.append(u"持ち込みの属性・型の行の番号が違う: %s" % by[35:40])
        foot = F0[-1]
        if foot["kind"] != "footnote" or foot["attrs"] != {u"footnoteID": u"fn1", u"xml:lang": u"ja"} or "row" in foot or "out" in foot:
            out_.append(u"脚注の行が属性ごと持ち込みでない")
        if [(h["kind"], h.get("row"), h.get("out"), h["text"]) for h in c0["H"]["hidden"]] != [(u"nonNumeric", 16, None, u"提出"), (u"nonFraction", None, 28, u"1")] or c0["H"]["sections"] != ["ix:hidden", "ix:references", "ix:resources"]:
            out_.append(u"隠しの fact の持ち込みが違う")
        if [r["tag"] for r in c0["H"]["references"]] != ["link:schemaRef"] or c0["H"]["resources"] != []:
            out_.append(u"持ち込みの参照・resources が違う(resources は ref の entry だけ。この書類は ref が無い)")
        c1 = jread(tf, "c0001.json")
        if c1["H"] is not None or [(e.get("row"), e.get("out")) for e in c1["F"]] != [(0, None), (17, None), (18, None), (19, None)]:
            out_.append(u"2 つ目の file の持ち込みが違う")
        # 型の外
        o = jread(tf, "outside.json")
        if list(o) != ["facts", "contexts", "units"] or len(o["facts"]) != 29:
            out_.append(u"outside.json の形・fact の数が違う")
        elif [(f["kind"], u"".join(f["reasons"])) for f in o["facts"]][:6] != [(u"nonFraction", u"a"), (u"nonFraction", u"b"), (u"nonFraction", u"c"), (u"nonFraction", u"c"), (u"nonFraction", u"d"), (u"nonFraction", u"d")]:
            out_.append(u"型の外の fact の理由が違う")
        elif o["facts"][0]["attrs"] != {u"contextRef": u"OddInstant", u"decimals": u"0", u"format": FMT_OK, u"name": u"jppfs_cor:Assets", u"scale": u"0", u"unitRef": u"JPY"} or [f["reasons"] for f in o["facts"] if f["reasons"] == ["a", "d"]] != [["a", "d"]]:
            out_.append(u"型の外の fact の属性が元のまま写されていない・理由が重ならない")
        if [c["id"] for c in o["contexts"]] != [u"CurrentYearInstant", u"FilingDateInstant", u"OddInstant", u"OtherEntity", u"BadMember", u"DupAxis"]:
            out_.append(u"型の外が指す文脈の並びが元の並びでない: %s" % [c["id"] for c in o["contexts"]])
        if [u["id"] for u in o["units"]] != [u"JPY", u"pure", u"USDPerJPY"]:
            out_.append(u"型の外が指す単位が元の並びでない: %s" % [u["id"] for u in o["units"]])
        # 2 回書くと同じ字・元の包みに触らない
        d2 = os.path.join(d, "type2")
        ent2 = entries_of(zp, ms)
        ms.derive_folder(ent2, d2)
        if tree_of(d2) != tree_of(tf):
            out_.append(u"型の folder を 2 回作ると違う字を書く")
        # carry_forbidden が仕込みを見つける
        def planted(fn):
            dd = os.path.join(d, "plant")
            if os.path.exists(dd):
                shutil.rmtree(dd)
            shutil.copytree(tf, dd)
            p = os.path.join(dd, "c0000.json")
            c = jload(read_file(p))
            fn(c)
            write_file(p, jdump(c))
            return ms.carry_forbidden(dd)
        plants = [
            (u"数の行の持ち込みに contextRef", lambda c: c["F"][0]["carry"].__setitem__("contextRef", "x")), (u"数の行の持ち込みに unitRef", lambda c: c["F"][0]["carry"].__setitem__("unitRef", "x")),
            (u"数の行の持ち込みに decimals", lambda c: c["F"][0]["carry"].__setitem__("decimals", "0")), (u"数の行の持ち込みに scale", lambda c: c["F"][0]["carry"].__setitem__("scale", "0")),
            (u"数の行の持ち込みに sign", lambda c: c["F"][0]["carry"].__setitem__("sign", "-")), (u"数の行の持ち込みに format", lambda c: c["F"][0]["carry"].__setitem__("format", "x")),
            (u"数の行の持ち込みに xsi:nil", lambda c: c["F"][0]["carry"].__setitem__("xsi:nil", "true")), (u"数の行の持ち込みに name", lambda c: c["F"][0]["carry"].__setitem__("name", "x")),
            (u"文の行の持ち込みに contextRef", lambda c: c["F"][37]["carry"].__setitem__("contextRef", "x")), (u"文の行の持ち込みに name", lambda c: c["F"][37]["carry"].__setitem__("name", "x")),
            (u"型に入った行に属性の全部", lambda c: c["F"][0].__setitem__("attrs", {"a": "b"})), (u"隠しの型に入った行の持ち込みに contextRef", lambda c: c["H"]["hidden"][0]["carry"].__setitem__("contextRef", "x")),
            (u"隠しの型に入った行に属性の全部", lambda c: c["H"]["hidden"][0].__setitem__("attrs", {"a": "b"})),
            (u"持ち込みの resources に文脈の定義", lambda c: c["H"]["resources"].append({"type": "context", "id": "x"})), (u"持ち込みの resources に単位の定義", lambda c: c["H"]["resources"].append({"type": "unit", "id": "x"}))]
        for what, fn in plants:
            if not planted(fn):
                out_.append(u"carry_forbidden が見つけない: %s" % what)
        if planted(lambda c: c["F"][39]["carry"].__setitem__("xsi:nil", "false")) != []:
            out_.append(u"文の行の持ち込みの xsi:nil を禁止にしている(文の fact は型が xsi:nil を持たない)")
        if planted(lambda c: c["F"][0].__setitem__("carry", dict(c["F"][0]["carry"], id="z"))) != []:
            out_.append(u"数の行の持ち込みの id を禁止にしている")
        if os.path.exists(os.path.join(tf, "orig.zip")):
            out_.append(u"元の包みが folder に在る")
    return out_


# ======================================================================== 4. 型から作る
def clone_folder(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def edit_json(folder, name, fn):
    p = os.path.join(folder, name)
    o = jload(read_file(p))
    fn(o)
    write_file(p, jdump(o))


def attr_changes(base, new):
    u"""2 つの表の並び([(名, 素の本文, F, H)])の対象の fact の属性の違い: [(file, 行, 違う属性の名の並び)]。F の行・隠しの fact。"""
    out_ = []
    for fi, ((_n, _p, F1, H1), (_n2, _p2, F2, H2)) in enumerate(zip(base, new)):
        for i, (e1, e2) in enumerate(zip(F1, F2)):
            ks = sorted(k for k in set(e1["attrs"]) | set(e2["attrs"]) if e1["attrs"].get(k) != e2["attrs"].get(k) or (k in e1["attrs"]) != (k in e2["attrs"]))
            if ks:
                out_.append((fi, i, ks))
        if H1 is not None:
            for j, (h1, h2) in enumerate(zip(H1["hidden"], H2["hidden"])):
                ks = sorted(k for k in set(h1["attrs"]) | set(h2["attrs"]) if h1["attrs"].get(k) != h2["attrs"].get(k) or (k in h1["attrs"]) != (k in h2["attrs"]))
                if ks:
                    out_.append((fi, u"H%d" % j, ks))
    return out_


def res_ids(H):
    return [(r["type"], r.get("id") or r.get("tag")) for r in H["resources"]]


def render_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        _zp, _ent, files, tf, an = derive_doc(d, ms)
        nf_, names, tables = ms.render_manuscript(tf)
        if [x[0] for x in nf_] != [ms.PUBLICDOC + u"0100000_a_E99991-000_ixbrl.htm", ms.PUBLICDOC + u"0200000_b_E99991-000_ixbrl.htm"]:
            out_.append(u"作った表の file の名が違う(PublicDoc つきの名)")
        if [x[1] for x in nf_] != [x[1] for x in files]:
            out_.append(u"素の本文が持ち込みのままでない")
        if any(not names[k].startswith(ms.PUBLICDOC) for k in names) or list(names) != list(KINDS) or tables != jread(tf, "taxonomy.json")["tables"]:
            out_.append(u"タクソノミの名・表が持ち込みのままでない")
        F = nf_[0][2]
        want = {
            0: {"name": u"jppfs_cor:Assets", "contextRef": CYI, "unitRef": u"JPY", "decimals": u"-3", "scale": u"3", "format": FMT_OK},
            2: {"name": u"jppfs_cor:Assets", "contextRef": CYI_NC, "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK},
            3: {"name": u"jppfs_cor:Profit", "contextRef": CYD, "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK, "sign": u"-"},
            4: {"name": u"jppfs_cor:Zero", "contextRef": CYD, "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK, "sign": u"-"},
            5: {"name": u"jppfs_cor:Receivable", "contextRef": CYI, "unitRef": u"JPY", "xsi:nil": u"true"},
            6: {"name": u"jppfs_cor:EPS", "contextRef": CYD, "unitRef": u"JPYPerShares", "decimals": u"2", "scale": u"0", "format": FMT_OK},
            7: {"name": u"jppfs_cor:Shares", "contextRef": CYI, "unitRef": u"shares", "decimals": u"0", "scale": u"0", "format": FMT_OK},
            8: {"name": u"jppfs_cor:Ratio", "contextRef": CYI, "unitRef": u"pure", "decimals": u"3", "scale": u"0", "format": FMT_OK},
            9: {"name": u"jppfs_cor:Equity", "contextRef": P1I_CAP, "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK},
            10: {"name": u"jppfs_cor:Seg", "contextRef": u"CurrentYearInstant_NonConsolidatedMember_jpcrp030000-asr_E99991-000AMember", "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK},
            35: {"name": u"jppfs_cor:NoScale", "contextRef": CYI, "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK},
            36: {"name": u"jppfs_cor:Carry", "contextRef": CYI, "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK, "footnoteRefs": u"fn1", "id": u"f9"},
            37: {"name": u"jpcrp_cor:Text", "contextRef": CYD, "escape": u"true"},
            38: {"name": u"jpcrp_cor:Text", "contextRef": CYD, "id": u"t2"},
            39: {"name": u"jpcrp_cor:NilText", "contextRef": CYD, "xsi:nil": u"true"},
            41: {"name": u"jpcrp_cor:Nest", "contextRef": CYD},
            42: {"name": u"jppfs_cor:Inner", "contextRef": CYI, "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK},
            44: {"name": u"jppfs_cor:Profit", "contextRef": CYD, "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK, "sign": u"-"},
            45: {"name": u"jppfs_cor:Profit", "contextRef": CYD, "unitRef": u"JPY", "decimals": u"0", "scale": u"0", "format": FMT_OK, "sign": u"-"}}
        for i, w in want.items():
            if F[i]["attrs"] != w:
                out_.append(u"作った fact %d の属性が手で決めた値と違う: %s" % (i, F[i]["attrs"]))
        for i in range(11, 35):
            if F[i]["attrs"] != files[0][2][i]["attrs"]:
                out_.append(u"型の外の fact %d の属性が元のままでない" % i)
        if F[40]["attrs"] != files[0][2][40]["attrs"] or F[43]["attrs"] != files[0][2][43]["attrs"] or F[46]["attrs"] != files[0][2][46]["attrs"] or F[47]["attrs"] != files[0][2][47]["attrs"] or F[48]["attrs"] != files[0][2][48]["attrs"]:
            out_.append(u"型の外の文の fact・脚注の属性が元のままでない")
        for i, e in enumerate(F):
            o = files[0][2][i]
            if (e["kind"], e["self"], e["start"], e["end"], e["parent"]) != (o["kind"], o["self"], o["start"], o["end"], o["parent"]):
                out_.append(u"持ち込みの表 F の欄が元のままでない: %d" % i)
                break
        H = nf_[0][3]
        if (H["pos"], H["before"], H["sections"], H["references"]) != (files[0][3]["pos"], files[0][3]["before"], files[0][3]["sections"], files[0][3]["references"]):
            out_.append(u"持ち込みの表 H の欄が元のままでない")
        hid = [(h["kind"], h["self"], h["text"], h["attrs"]) for h in H["hidden"]]
        if hid != [(u"nonNumeric", False, u"提出", {u"name": u"jpdei_cor:FilingText", u"contextRef": FDI}), (u"nonFraction", False, u"1", files[0][3]["hidden"][1]["attrs"])]:
            out_.append(u"隠しの fact が違う: %s" % hid)
        want_res = [("context", i) for i in BUILT_CTX_IDS] + [("context", i) for i in OUT_CTX_IDS] + [("unit", i) for i in BUILT_UNIT_IDS] + [("unit", u"USDPerJPY")]
        if res_ids(H) != [("ref", None)] * 0 + want_res:
            out_.append(u"resources の並びが違う: %s" % res_ids(H))
        if nf_[1][3] is not None:
            out_.append(u"頭の部の無い file に表 H ができた")
        cm = dict((r["id"], r) for r in H["resources"] if r["type"] == "context")
        seg = cm[u"CurrentYearInstant_NonConsolidatedMember_jpcrp030000-asr_E99991-000AMember"]
        if (seg["scheme"], seg["ident"], seg["period"], seg["members"], seg["has_scenario"]) != (ENT[0], ENT[1], [[u"xbrli:instant", u"2026-03-31"]], [[SEG, MEM_A], [CA, NM]], True):
            out_.append(u"個別 + 次元の文脈の定義が違う: %s" % dict(seg))
        cyd = cm[CYD]
        if (cyd["period"], cyd["members"], cyd["has_scenario"]) != ([[u"xbrli:startDate", u"2025-04-01"], [u"xbrli:endDate", u"2026-03-31"]], [], False):
            out_.append(u"期間の文脈の定義が違う")
        pi = cm[P1I_CAP]
        if (pi["period"], pi["members"]) != ([[u"xbrli:instant", u"2025-03-31"]], [[COMP, CAP]]):
            out_.append(u"1 年前の文脈の定義が違う")
        um = dict((r["id"], r) for r in H["resources"] if r["type"] == "unit")
        if (um[u"JPYPerShares"]["measures"], dict(um[u"JPYPerShares"]["divide"]), um[u"shares"]["measures"], um[u"pure"]["measures"], um[u"JPY"]["measures"]) != ([], {"num": [u"iso4217:JPY"], "den": [u"xbrli:shares"]}, [u"xbrli:shares"], [u"xbrli:pure"], [u"iso4217:JPY"]):
            out_.append(u"単位の定義が違う")
        if jdump(ms.context_view([x[3] for x in nf_])[0][u"OddInstant"]) != jdump(files[0][3]["resources"][9]) or jdump(um[u"USDPerJPY"]) != jdump(files[0][3]["resources"][-1]):
            out_.append(u"型の外の定義が元のまま写されていない")
        # 組んで戻る(便 XB0 の組む部品に渡す)
        back = ms.B.build_text(nf_[0][1], nf_[0][2], nf_[0][3])
        if u'contextRef="Prior1YearInstant_CapitalStockMember"' not in back or u'id="Prior1YearInstant_ComponentsMember"' in back or u"</ix:header>" not in back:
            out_.append(u"組んだ字に作った文脈・定義が入っていない")
        # ---- 型の値を 1 つ変えると、作った属性か定義がその欄の分だけ変わる(行 0 = 3 つの fact)
        base = nf_

        def changed(fn):
            dd = clone_folder(tf, os.path.join(d, "chg"))
            edit_json(dd, "type.json", lambda t: fn(t["rows"][0], t))
            try:
                got, _n, _t = ms.render_manuscript(dd)
            except ms.Refuse as exc:
                return [("refuse", exc.reason)]
            return attr_changes(base, got)
        three = lambda ks: [(0, 0, ks), (0, 1, ks), (1, 0, ks)]
        exp = [
            (u"値の符号(負にする)", lambda r, t: r.__setitem__("value", u"-1234000"), three(["sign"])),
            (u"値を空にする", lambda r, t: r.__setitem__("value", u"無い"), three(["decimals", "format", "scale", "xsi:nil"])),
            (u"値の数字だけを変える(属性は変わらない。数字は本文の字が持つ)", lambda r, t: r.__setitem__("value", u"1234001"), []),
            (u"単位", lambda r, t: r.__setitem__("unit", u"株"), three(["unitRef"])),
            (u"単位(割り算)", lambda r, t: r.__setitem__("unit", u"通貨:JPY÷株"), three(["unitRef"])),
            (u"表示の位", lambda r, t: r.__setitem__("shift", 4), three(["scale"])),
            (u"精度", lambda r, t: r.__setitem__("prec", -2), three(["decimals"])),
            (u"対象", lambda r, t: r.__setitem__("target", u"個別"), three(["contextRef"])),
            (u"次元", lambda r, t: r.__setitem__("dims", [["A0002", "M0002"]]), three(["contextRef"])),
            (u"期(1 年前)", lambda r, t: (r.__setitem__("period", [u"2025-03-31"])), three(["contextRef"])),
            (u"期の種類を期間に", lambda r, t: (r.__setitem__("pkind", "duration"), r.__setitem__("period", [u"2025-04-01", u"2026-03-31"])), three(["contextRef"])),
            (u"科目", lambda r, t: r.__setitem__("code", "K0006"), three(["name"]))]
        for what, fn, want_ in exp:
            got = changed(fn)
            if got != want_:
                out_.append(u"型の値を変えたときの作った属性の違いが手で決めた値と違う(%s): %s" % (what, got))
        dd = clone_folder(tf, os.path.join(d, "chg"))
        edit_json(dd, "type.json", lambda t: t["rows"][0].__setitem__("target", u"個別"))
        got, _n, _t = ms.render_manuscript(dd)
        if CYI_NC not in [r["id"] for r in got[0][3]["resources"] if r["type"] == "context"] or CYI in [r["id"] for r in got[0][3]["resources"] if r["type"] == "context"][:0]:
            out_.append(u"対象を変えても文脈の定義が変わらない")
        # 定義の数: 行を消すと、その行だけが使う文脈・単位の定義が消える
        dd = clone_folder(tf, os.path.join(d, "chg"))
        edit_json(dd, "type.json", lambda t: t.__setitem__("rows", [r for i, r in enumerate(t["rows"]) if i not in (7, 6, 5)]))
        edit_json(dd, "c0000.json", lambda c: [c["F"].__setitem__(i, c["F"][i]) for i in ()])
        # ---- 文脈の id の member の並びは軸の名の昇順(member の昇順でない)。個別でない次元が 2 つで、軸の昇順と member の昇順が食い違う 2 つの組(軸の名: A0001 = SegAxis・A0002 = ComponentsOfEquityAxis。member: M0001 = AMember・M0002 = CapitalStockMember)
        for what, dims, want_id, want_members in (
                (u"軸の昇順と member の字の昇順が食い違う", [["A0001", "M0002"], ["A0002", "M0001"]], u"CurrentYearInstant_CapitalStockMember_jpcrp030000-asr_E99991-000AMember", [[SEG, CAP], [COMP, MEM_A]]),
                (u"軸の昇順と member の名の昇順が食い違う", [["A0002", "M0002"], ["A0001", "M0001"]], u"CurrentYearInstant_jpcrp030000-asr_E99991-000AMember_CapitalStockMember", [[SEG, MEM_A], [COMP, CAP]])):
            dd = clone_folder(tf, os.path.join(d, "chg"))
            edit_json(dd, "type.json", lambda t, dims=dims: t["rows"][0].__setitem__("dims", dims))
            got, _n, _t = ms.render_manuscript(dd)
            cms = dict((r["id"], r) for r in got[0][3]["resources"] if r["type"] == "context")
            if got[0][2][0]["attrs"]["contextRef"] != want_id or want_id not in cms or cms[want_id]["members"] != want_members:
                out_.append(u"文脈の id の member の並び(%s): %s" % (what, got[0][2][0]["attrs"]["contextRef"]))
        # ---- 作る単位の定義は型の行に現れた単位だけ(株・純数を持たない・片方だけ持つ型)
        typ0, map0 = jread(tf, "type.json"), jread(tf, "map.json")

        def built_unit_ids(unit_by_row):
            dd3 = clone_folder(tf, os.path.join(d, "chg"))
            edit_json(dd3, "type.json", lambda t: [t["rows"][i].__setitem__("unit", u) for i, u in unit_by_row.items()])
            tp = jread(dd3, "type.json")
            return [x["id"] for x in ms.build_definitions(tp["decision"], tp["rows"], map0)[1]]
        if built_unit_ids({}) != [u"JPY", u"JPYPerShares", u"pure", u"shares"]:
            out_.append(u"型のままの作った単位が違う")
        for what, ch, want_u in ((u"株・純数・割り算を持たない", {5: u"通貨:JPY", 6: u"通貨:JPY", 7: u"通貨:JPY"}, [u"JPY"]),
                                 (u"株だけ持つ", {5: u"通貨:JPY", 7: u"通貨:JPY"}, [u"JPY", u"shares"]),
                                 (u"純数だけ持つ", {5: u"通貨:JPY", 6: u"通貨:JPY"}, [u"JPY", u"pure"]),
                                 (u"割り算だけ持つ", {6: u"通貨:JPY", 7: u"通貨:JPY"}, [u"JPY", u"JPYPerShares"])):
            got_u = built_unit_ids(ch)
            if got_u != want_u:
                out_.append(u"作った単位の定義(%s): %s (手で決めた値は %s)" % (what, got_u, want_u))
        # ---- 断り(型から作る命令の中身)
        def refused(fn, name="type.json", reason=None):
            dd2 = clone_folder(tf, os.path.join(d, "bad"))
            edit_json(dd2, name, fn)
            try:
                ms.render_manuscript(dd2)
            except ms.Refuse as exc:
                return exc.reason if reason is None else (exc.reason == reason)
            return None
        bad = [
            (u"型の対象が知らない値", lambda t: t["rows"][0].__setitem__("target", u"連結"), u"型の対象が知らない値", "type.json"),
            (u"型の期の種類が知らない値", lambda t: t["rows"][0].__setitem__("pkind", "forever"), u"型の期の種類が知らない値", "type.json"),
            (u"期の名が作れない", lambda t: t["rows"][0].__setitem__("period", [u"2026-02-15"]), u"期の名が作れない", "type.json"),
            (u"単位の形が知らない形", lambda t: t["rows"][0].__setitem__("unit", u"円"), u"単位の形が知らない形", "type.json"),
            (u"型の種類が知らない値", lambda t: t["rows"][0].__setitem__("kind", u"画"), u"型の種類が知らない値", "type.json"),
            (u"持ち込みに型の属性", lambda c: c["F"][0]["carry"].__setitem__("unitRef", "JPY"), u"持ち込みに型の属性が在る", "c0000.json"),
            (u"持ち込みに型の属性(文)", lambda c: c["F"][37]["carry"].__setitem__("name", "x"), u"持ち込みに型の属性が在る", "c0000.json"),
            (u"対応表に無いコード", lambda t: t["rows"][0].__setitem__("code", "K9999"), u"作る途中の例外", "type.json"),
            (u"作った定義を置く頭の部が無い", lambda c: c["H"]["sections"].remove("ix:resources"), u"作った定義を置く頭の部が無い", "c0000.json"),
            (u"目次の名が上の folder", lambda c: c["htm"][0].__setitem__("name", "../x.htm"), u"目次の名が知らない形", "index.json"),
            (u"目次の本文の名が上の folder", lambda c: c["htm"][0].__setitem__("text", "../t0000.txt"), u"目次の名が知らない形", "index.json"),
            (u"文脈の id が違う組で重なる", None, u"文脈の id が違う組で重なる", "type.json"),
            (u"型の外の定義が作った定義と同じ id で中身が違う", None, u"型の外の定義が作った定義と同じ id で中身が違う", "outside.json"),
            (u"型の外の単位が作った単位と同じ id で中身が違う", None, u"型の外の定義が作った定義と同じ id で中身が違う", "outside.json")]
        for what, fn, want_reason, name in bad:
            if what == u"文脈の id が違う組で重なる":
                dd2 = clone_folder(tf, os.path.join(d, "bad"))
                edit_json(dd2, "map.json", lambda m: (m[u"member"].__setitem__("M0001", u"x:yMember"), m[u"member"].__setitem__("M0002", u"xy:Member")))

                def collide(t):
                    t["rows"][8]["period"] = [u"2026-03-31"]
                    t["rows"][8]["target"] = u"個別"
                    t["rows"][8]["dims"] = [["A0002", "M0002"]]
                    t["rows"][9]["dims"] = [["A0002", "M0001"]]
                edit_json(dd2, "type.json", collide)
                try:
                    ms.render_manuscript(dd2)
                    got = None
                except ms.Refuse as exc:
                    got = exc.reason
            elif what == u"型の外の定義が作った定義と同じ id で中身が違う":
                got = refused(lambda o: o["contexts"][2].__setitem__("id", u"CurrentYearDuration"), "outside.json")
            elif what == u"型の外の単位が作った単位と同じ id で中身が違う":
                got = refused(lambda o: o["units"][2].__setitem__("id", u"shares"), "outside.json")
            else:
                got = refused(fn, name)
            if got != want_reason:
                out_.append(u"断り(%s): %r (手で決めた理由は %r)" % (what, got, want_reason))
        if refused(lambda o: o["contexts"][0].__setitem__("id", u"CurrentYearInstant"), "outside.json") is not None:
            out_.append(u"型の外の定義が作った定義と同じ id・同じ中身なのに断った")
    return out_


def derive_problems_cmd(ms=None):
    return []


# ======================================================================== 5. 比べる・混ぜ物・表示の字
def cmp_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        zp, ent, files, names, tables = peel_doc(d, ms)
        an, files = ms.derive_folder(ent, os.path.join(d, "type"))
        nf_, _n, _t = ms.render_manuscript(os.path.join(d, "type"))
        r = ms.compare_attrs(files, nf_)
        if (r[0], r[1], r[2], dict(r[3])) != (False, False, 1, {"scale": 1}):
            out_.append(u"比べ方 1(元の書類): %s (手で数えた値は 1 つの fact の scale。文脈の名は 1 つ違う)" % (r,))
        # 戻る版
        d2 = os.path.join(d, "good")
        os.makedirs(d2)
        _z, ent2, files2, _n2, _t2 = peel_doc(d2, ms, a=good_variant(HTM_A_TEXT))
        an2, files2 = ms.derive_folder(ent2, os.path.join(d2, "type"))
        nf2, _a, _b = ms.render_manuscript(os.path.join(d2, "type"))
        r2 = ms.compare_attrs(files2, nf2)
        if (r2[0], r2[1], r2[2], dict(r2[3])) != (True, True, 0, {}):
            out_.append(u"比べ方 1(戻る版): %s" % (r2,))
        d3 = os.path.join(d, "ren")
        os.makedirs(d3)
        _z, ent3, files3, _n3, _t3 = peel_doc(d3, ms, a=HTM_A_TEXT.replace(u'decimals="0" format="ixt:numdotdecimal">42<', u'decimals="0" scale="0" format="ixt:numdotdecimal">42<'))
        an3, files3 = ms.derive_folder(ent3, os.path.join(d3, "type"))
        nf3, _a, _b = ms.render_manuscript(os.path.join(d3, "type"))
        r3 = ms.compare_attrs(files3, nf3)
        if (r3[0], r3[1], r3[2]) != (True, False, 0):
            out_.append(u"比べ方 1(文脈の名だけ違う版): %s (属性は意味として同じ・文脈の名は違う)" % (r3,))
        # 作った側の表を 1 か所ずつ壊す
        def tamper(fn):
            new = [(n, p, [od((k, (dict(v) if k == "attrs" else v)) for k, v in e.items()) for e in F], H) for n, p, F, H in nf2]
            fn(new)
            return ms.compare_attrs(files2, new)
        t_cases = [
            (u"decimals", lambda n: n[0][2][0]["attrs"].__setitem__("decimals", "9"), (False, True, 1, {"decimals": 1})),
            (u"sign", lambda n: n[0][2][3]["attrs"].pop("sign"), (False, True, 1, {"sign": 1})),
            (u"format", lambda n: n[0][2][0]["attrs"].__setitem__("format", "x"), (False, True, 1, {"format": 1})),
            (u"name", lambda n: n[0][2][0]["attrs"].__setitem__("name", "x"), (False, True, 1, {"name": 1})),
            (u"持ち込みの属性", lambda n: n[0][2][36]["attrs"].__setitem__("id", "zz"), (False, True, 1, {"id": 1})),
            (u"属性が増える", lambda n: n[0][2][0]["attrs"].__setitem__("zzz", "1"), (False, True, 1, {"zzz": 1})),
            (u"属性が減る", lambda n: n[0][2][0]["attrs"].pop("scale"), (False, True, 1, {"scale": 1})),
            (u"contextRef を別の中身の定義へ", lambda n: n[0][2][0]["attrs"].__setitem__("contextRef", CYD), (False, False, 1, {"contextRef": 1})),
            (u"unitRef を別の中身の定義へ", lambda n: n[0][2][0]["attrs"].__setitem__("unitRef", u"pure"), (False, True, 1, {"unitRef": 1})),
            (u"unitRef が無くなる", lambda n: n[0][2][0]["attrs"].pop("unitRef"), (False, True, 1, {"unitRef": 1})),
            (u"fact の数が違う", lambda n: n[0][2].pop(0), (False, False, 54, {u"fact の数": 1})),
            (u"2 つの属性が 1 つの fact で違う", lambda n: (n[0][2][0]["attrs"].__setitem__("decimals", "9"), n[0][2][0]["attrs"].__setitem__("scale", "9")), (False, True, 1, {"decimals": 1, "scale": 1})),
            (u"2 つの fact が違う", lambda n: (n[0][2][0]["attrs"].__setitem__("decimals", "9"), n[0][2][3]["attrs"].__setitem__("decimals", "9")), (False, True, 2, {"decimals": 2}))]
        for what, fn, want in t_cases:
            got = tamper(fn)
            if (got[0], got[1], got[2], dict(got[3])) != want:
                out_.append(u"比べ方 1 の違い(%s): %s (手で決めた値は %s)" % (what, got, want))

        def rename_unit(n):
            H = n[0][3]
            for rr in H["resources"]:
                if rr["type"] == "unit" and rr["id"] == u"JPY":
                    rr["id"] = u"YEN"
            for e in n[0][2] + n[1][2]:
                if e["attrs"].get("unitRef") == u"JPY":
                    e["attrs"]["unitRef"] = u"YEN"
            for h in H["hidden"]:
                if h["attrs"].get("unitRef") == u"JPY":
                    h["attrs"]["unitRef"] = u"YEN"
        got = tamper(rename_unit)
        if (got[0], got[1], got[2]) != (True, True, 0):
            out_.append(u"単位の id だけ違うのに違いに数える: %s" % (got,))
        # ---- 道具の fact の一覧の正規化
        hdr = (u"﻿Name", u"contextRef", u"unitRef", u"Dec", u"Value", u"EntityScheme", u"EntityIdentifier", u"Start", u"End/Instant", u"Dimensions")
        rows = [(u"n1", u"c1", u"JPY", u"0", u"5", u"s", u"e", u"", u"2026-03-31"), (u"n0", u"c2", u"", u"", u"x", u"s", u"e", u"", u"2026-03-31", u"ax", u"mem"), (u"n1", u"c3", u"Z", u"0", u"5", u"s", u"e", u"", u"2026-03-31")]
        got = ms.normalize_rows(hdr, rows, {u"JPY": u"iso4217:JPY"})
        want = sorted([(u"n1", u"iso4217:JPY", u"0", u"5", u"s", u"e", u"", u"2026-03-31"), (u"n0", u"", u"", u"x", u"s", u"e", u"", u"2026-03-31", u"ax", u"mem"), (u"n1", u"Z", u"0", u"5", u"s", u"e", u"", u"2026-03-31")])
        if got != want:
            out_.append(u"比べ方 2 の正規化が手で決めた値と違う: %s" % got)
        if ms.normalize_rows(hdr, rows, {u"JPY": u"a"}) == ms.normalize_rows(hdr, rows, {u"JPY": u"b"}):
            out_.append(u"正規化が単位の measure の字を使っていない")
        if ms.normalize_rows(None, rows, {}) is not None or ms.normalize_rows((u"Name", u"unitRef"), rows, {}) is not None or ms.normalize_rows((u"Name", u"contextRef"), rows, {}) is not None:
            out_.append(u"見出しが読めないのに正規化した")
        if ms.normalize_rows(hdr, [], {}) != []:
            out_.append(u"行が無いときの正規化が空でない")
        rows2 = [rows[2], rows[0], rows[1]]
        if ms.normalize_rows(hdr, rows2, {u"JPY": u"iso4217:JPY"}) != want:
            out_.append(u"正規化が行の並びに依る")
        p = os.path.join(d, "f.csv")
        with io.open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(u"﻿" + u",".join(h.lstrip(u"﻿") for h in hdr) + u"\r\n" + u"n1,c1,JPY,0,\"5,5\",s,e,,2026-03-31\r\n")
        h2, r2_ = ms.read_fact_rows(p)
        if h2[0] != u"﻿Name" or r2_ != [(u"n1", u"c1", u"JPY", u"0", u"5,5", u"s", u"e", u"", u"2026-03-31")]:
            out_.append(u"fact の一覧の csv の読みが違う: %s %s" % (h2[0:1], r2_))
        if ms.read_fact_rows(os.path.join(d, "none.csv")) != (None, []):
            out_.append(u"csv が無いときの読みが (None, []) でない")
        open(os.path.join(d, "empty.csv"), "w").close()
        if ms.read_fact_rows(os.path.join(d, "empty.csv")) != (None, []):
            out_.append(u"空の csv の読みが (None, []) でない")
        um = ms.unit_map_of(nf_)
        if um != {u"JPY": u"iso4217:JPY", u"shares": u"xbrli:shares", u"pure": u"xbrli:pure", u"JPYPerShares": u"iso4217:JPY/xbrli:shares", u"USDPerJPY": u"iso4217:USD/iso4217:JPY"}:
            out_.append(u"単位の id → measure の字が違う: %s" % um)
    return out_


def mix_problems(ms=None):
    ms = ms or MS
    out_ = []
    R = lambda **kw: dict(dict(kind=u"数", code=u"K1", period=[u"2026-03-31"], pkind="instant", target=u"既定", dims=[], value=u"5"), **kw)
    cases = [
        (u"最初の行", [R(), R(code=u"K2")], 0), (u"2 つ目が最初の当て先(1 つ目が文)", [R(kind=u"文"), R(code=u"K2")], 1), (u"次元が在る行は当てない", [R(dims=[["A", "M"]]), R(code=u"K2")], 1),
        (u"値が無い行は当てない", [R(value=u"無い"), R(code=u"K2")], 1), (u"個別の行は当てない", [R(target=u"個別"), R(code=u"K2")], 1),
        (u"個別の双子が在る行は当てない", [R(), R(target=u"個別"), R(code=u"K2")], 2), (u"期が違う個別は双子でない", [R(), R(target=u"個別", period=[u"2025-03-31"])], 0),
        (u"科目が違う個別は双子でない", [R(), R(target=u"個別", code=u"K2")], 0), (u"期の種類が違う個別は双子でない", [R(), R(target=u"個別", pkind="duration")], 0),
        (u"次元が違う個別は双子でない", [R(), R(target=u"個別", dims=[["A", "M"]])], 0), (u"当て先が無い", [R(kind=u"文"), R(dims=[["A", "M"]]), R(value=u"無い"), R(target=u"個別")], None),
        (u"行が無い", [], None), (u"双子のために当て先が無い", [R(), R(target=u"個別")] and [R(), R(target=u"個別")][0:1] + [R(target=u"個別")], None),
        (u"期が同じ双子(個別・次元なし)", [R(), R(target=u"個別"), R(code=u"K3", period=[u"2025-03-31"])], 2)]
    for what, rows, want in cases:
        got = ms.mix_row_index(rows)
        if got != want:
            out_.append(u"混ぜ物の当て先(%s): %r (手で決めた値は %r)" % (what, got, want))
    with Temp() as d:
        zp, ent, files, tf, an = derive_doc(d, ms)
        if ms.mix_row_index(jread(tf, "type.json")["rows"]) != 2:
            out_.append(u"この書類の混ぜ物の当て先が 2(Profit)でない")
        mf = clone_folder(tf, os.path.join(d, "mix"))
        before = tree_of(mf)
        r = ms.mix_folder(mf)
        after = tree_of(mf)
        if r != (2, 3):
            out_.append(u"mix_folder の返り値が違う: %s (手で数えた値は (2, 3))" % (r,))
        if sorted(k for k in before if before[k] != after[k]) != [u"type.json"]:
            out_.append(u"混ぜ物が type.json だけを変えていない")
        tb, ta = jload(before[u"type.json"]), jload(after[u"type.json"])
        diffs = [(i, k) for i, (a, b) in enumerate(zip(tb["rows"], ta["rows"])) for k in a if a[k] != b[k]]
        if diffs != [(2, "target")] or ta["rows"][2]["target"] != u"個別" or tb["decision"] != ta["decision"]:
            out_.append(u"混ぜ物が 1 か所(行 2 の対象)だけを変えていない: %s" % diffs)
        # 当て先の fact の数: 行 0 を当て先にする(行 1 の双子を消す)
        mf2 = clone_folder(tf, os.path.join(d, "mix2"))
        edit_json(mf2, "type.json", lambda t: t["rows"][1].__setitem__("code", "K0006"))
        if ms.mix_folder(mf2) != (0, 3):
            out_.append(u"当て先の行を指す fact の数(2 つの file・3 つ)が違う: %s" % (ms.mix_folder(clone_folder(tf, os.path.join(d, "mix3"))),))
        mf4 = clone_folder(tf, os.path.join(d, "mix4"))
        edit_json(mf4, "type.json", lambda t: [t["rows"][i].__setitem__("target", u"個別") for i in range(len(t["rows"]))])
        b4 = tree_of(mf4)
        if ms.mix_folder(mf4) is not None or tree_of(mf4) != b4:
            out_.append(u"当て先が無いのに混ぜ物を作った(か folder を変えた)")
        # 隠しの fact も数える: 行 16(隠しの文)ではなく、隠しの数を当て先にする作り物
        mf5 = clone_folder(tf, os.path.join(d, "mix5"))
        edit_json(mf5, "type.json", lambda t: [t["rows"].__setitem__(i, dict(t["rows"][i], target=u"個別")) for i in range(len(t["rows"])) if i != 16])
        edit_json(mf5, "type.json", lambda t: t["rows"][16].update({"kind": u"数", "value": u"5", "unit": u"通貨:JPY", "shift": 0, "prec": 0}))
        if ms.mix_folder(mf5) != (16, 1):
            out_.append(u"隠しの fact を指す行の fact の数が違う")
        # 表示の字の検査
        if ms.display_check(tf) != (19, 19):
            out_.append(u"表示の字の検査(元の書類)が (19, 19) でない: %s" % (ms.display_check(tf),))
        for what, fn, want in ((u"値の数字(表示の桁に届く変え方)", lambda t: t["rows"][0].__setitem__("value", u"1235000"), (19, 16)), (u"値の数字(表示の桁に届かない変え方は見えない)", lambda t: t["rows"][0].__setitem__("value", u"1234001"), (19, 19)), (u"精度", lambda t: t["rows"][7].__setitem__("prec", 2), (19, 18)),
                               (u"表示の位", lambda t: t["rows"][0].__setitem__("shift", 2), (19, 16)), (u"負の印(大きさだけ見る)", lambda t: t["rows"][2].__setitem__("value", u"1500"), (19, 19)),
                               (u"空の行は掛けない", lambda t: t["rows"][4].update({"value": u"5", "shift": 0, "prec": 0}), (20, 19)), (u"文の行は掛けない", lambda t: t["rows"][12].__setitem__("value", u"5"), (19, 19))):
            dd = clone_folder(tf, os.path.join(d, "disp"))
            edit_json(dd, "type.json", fn)
            if ms.display_check(dd) != want:
                out_.append(u"表示の字の検査(%s): %s (手で数えた値は %s)" % (what, ms.display_check(dd), want))
        dd = clone_folder(tf, os.path.join(d, "disp"))
        p = os.path.join(dd, "t0000.txt")
        raw = read_file(p)
        write_file(p, raw.replace(u"1,234".encode("utf-8"), u"1,235".encode("utf-8"), 1))
        if ms.display_check(dd) != (19, 18):
            out_.append(u"本文の字を 1 つ変えても表示の字の検査が変わらない: %s" % (ms.display_check(dd),))
        if ms.display_check(mf5) != (20, 19):
            out_.append(u"隠しの数の fact が表示の字の検査に掛からない: %s" % (ms.display_check(mf5),))
    # ---- mix_effect(正規化した行の並び)
    base = [(u"a", u"1"), (u"b", u"2"), (u"c", u"3")]
    ex = (ms.AXIS_CONS, ms.MEMBER_IND)
    good = [(u"a", u"1"), (u"b", u"2") + ex, (u"c", u"3")]
    if not ms.mix_effect(base, good, 1):
        out_.append(u"混ぜ物の効きの判定が、次元の組が 1 つ増えた 1 行を効いたと言わない")
    if not ms.mix_effect(base + [(u"b", u"2")], [(u"a", u"1"), (u"b", u"2") + ex, (u"b", u"2"), (u"c", u"3")], 1):
        out_.append(u"同じ行が 2 つ在るとき 1 つだけ変わったのを効いたと言わない")
    if not ms.mix_effect([(u"a", u"1"), (u"a", u"1")], [(u"a", u"1") + ex, (u"a", u"1") + ex], 2):
        out_.append(u"同じ行 2 つが両方変わったのを効いたと言わない(count 2)")
    neg = [
        (u"変わった行が 0", base, base, 1), (u"count が 0", base, good, 0), (u"count が多い", base, good, 2), (u"count が少ない(2 行変わった)", base, [(u"a", u"1") + ex, (u"b", u"2") + ex, (u"c", u"3")], 1),
        (u"別の軸が増えた", base, [(u"a", u"1"), (u"b", u"2", u"x", u"y"), (u"c", u"3")], 1), (u"member だけ違う", base, [(u"a", u"1"), (u"b", u"2", ms.AXIS_CONS, u"y"), (u"c", u"3")], 1),
        (u"軸だけ違う", base, [(u"a", u"1"), (u"b", u"2", u"x", ms.MEMBER_IND), (u"c", u"3")], 1), (u"列が 1 つだけ増えた", base, [(u"a", u"1"), (u"b", u"2", ms.MEMBER_IND), (u"c", u"3")], 1),
        (u"行が増えた(増えた行は元の行に対応しない)", base, base + [(u"d", u"4") + ex], 1), (u"行が消えた", base, base[:2], 1), (u"ほかの行も変わった", base, [(u"a", u"9"), (u"b", u"2") + ex, (u"c", u"3")], 1),
        (u"増えた行の頭が元に無い", base, [(u"a", u"1"), (u"z", u"2") + ex, (u"c", u"3")], 1), (u"元が無い", None, good, 1), (u"作った側が無い", base, None, 1), (u"元が空", [], good, 1),
        (u"同じ行を 2 回増やした(元に 1 つ)", base, [(u"a", u"1") + ex, (u"a", u"1") + ex, (u"b", u"2"), (u"c", u"3")], 2)]
    for what, b_, m_, c_ in neg:
        if ms.mix_effect(b_, m_, c_):
            out_.append(u"混ぜ物の効きの判定が効いたと言う: %s" % what)
    return out_


# ======================================================================== 6. 書類 1 本
def pair(n, t):
    return {u"数": n, u"文": t}


EXPECT_REC = {
    u"断った": False, u"断った段": u"", u"断った理由": u"",
    u"対象の fact": {u"数": 47, u"文": 7, u"隠し": 2, u"脚注": 1}, u"型に入った fact": pair(20, 5),
    u"型の外の fact": {u"理由ごと": {u"a": pair(2, 1), u"b": pair(1, 1), u"c": pair(2, 0), u"d": pair(3, 0), u"e": pair(5, 0), u"f": pair(3, 0), u"g": pair(10, 0), u"h": pair(2, 0)}, u"合計": pair(27, 2)},
    u"型の行": {u"数": 16, u"文": 4, u"2 つ以上の fact をまとめた行": 3, u"値が -0 の行": 1}, u"対応表の行": {u"科目": 17, u"軸": 2, u"member": 2, u"_cor で終わらない名": 2},
    u"持ち込みの属性を持つ fact": {u"数": 1, u"文": 3, u"属性ごと": {u"escape": 1, u"footnoteRefs": 1, u"id": 2, u"xsi:nil": 1}},
    u"文脈の定義": {u"作った": 9, u"作らなかった": 1}, u"単位の定義": {u"作った": 4, u"作らなかった": 0},
    u"比べ方 1": {u"属性が意味として同じ": False, u"文脈の名も同じ": False, u"違った fact": 1, u"属性ごとの違った fact": {u"scale": 1}},
    u"比べ方 2": {u"組めた": True, u"fact が意味として同じ": True, u"字も含めて行が同じ": False, u"鳴り方が同じ": True, u"2 回が同じ": True},
    u"混ぜ物": {u"作れた": True, u"効いた": True}, u"表示の字の検査": {u"掛けた fact": 19, u"合った fact": 19}}


def plain_rec(rec):
    o = json.loads(json.dumps(rec))
    secs = o.pop(u"秒")
    return o, secs


def doc_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        keep = os.path.join(d, "keep")
        os.makedirs(keep)
        rec, r, proc, zp, tmp = doc_run(ms, d, keep=keep)
        before = read_bytes_sha(zp)
        got, secs = plain_rec(rec)
        if got != EXPECT_REC:
            diff = [k for k in EXPECT_REC if got.get(k) != EXPECT_REC[k]]
            out_.append(u"書類 1 本の数が手で数えた値と違う: %s" % [(k, got.get(k)) for k in diff])
        if list(rec) != list(ms.zero_rec()) or not isinstance(secs[u"型から作る命令"], float):
            out_.append(u"書類ごとの欄の並び・秒が違う")
        if len(r.calls) != 3 or [os.path.basename(c["zip"]) for c in r.calls] != ["orig.zip", "new.zip", "mix.zip"]:
            out_.append(u"道具の呼び出しが 3 回(元・組み直し・混ぜ物)でない: %s" % [os.path.basename(c["zip"]) for c in r.calls])
        else:
            for c in r.calls:
                cmd = c["cmd"]
                if u"--validate" not in cmd or u"--facts" not in cmd or cmd[cmd.index(u"--factListCols") + 1] != ms.T.FACT_COLS or u"http://www.xbrl.org/2003/arcrole/general-special" in cmd:
                    out_.append(u"道具の掛け方が掛け方 A の字でない(--validate・--facts・--factListCols・掛け方 B を掛けない)")
                    break
            if any(c["timeout"] != 600 for c in r.calls) or any(not c["existed"] for c in r.calls) or any(c["raw"][:2] != X.SEED or c["raw"][2:] != c["cmd"] for c in r.calls):
                out_.append(u"時間の上限・zip・PYTHONHASHSEED=0 の前置きが違う")
            for c in r.calls:
                bl = c["blobs"]
                if any(n.endswith(".xbrl") for n in c["names"]) or bl["XBRL/AuditDoc/audit.xml"] != b"<a/>" or bl["XBRL/PublicDoc/manifest_PublicDoc.xml"] != b"<manifest/>" or bl["XBRL/PublicDoc/logo.png"] != b"PNG-not-an-image":
                    out_.append(u"掛けた包みの中身が違う(.xbrl が残る・マニフェスト・画像・AuditDoc が変わった)")
                    break
            orig = ms.B.load_package(zp)
            if sorted(c for c in r.calls[0]["names"]) != sorted(i.filename for i, _d in orig):
                out_.append(u"元の包みに掛けた file の集まりが元の包み(.xbrl を除く)と違う")
            for nm, data in r.calls[0]["blobs"].items():
                if dict((i.filename, dd) for i, dd in orig)[nm] != data:
                    out_.append(u"元の包みの file が元の字でない: %s" % nm[-12:])
                    break
            # 組み直した包み = 組む命令の出す字(独立に組み直して照らす)
            zp2, ent2, files2, tf2, an2 = derive_doc(os.path.join(d, "w"), ms) if os.makedirs(os.path.join(d, "w")) is None else (None,) * 5
            nfiles, nnames, ntables = ms.render_manuscript(tf2)
            mf = os.path.join(d, "man")
            ms.P.write_folder(mf, nfiles, nnames, ntables)
            want_tree = ms.P.render_folder(mf)
            n_ = r.calls[1]["blobs"]
            for rel, data in want_tree.items():
                if n_[ms.PUBLICDOC + rel] != data:
                    out_.append(u"組み直した包みの file が型から作って組んだ字でない: %s" % rel[:10])
            m_ = r.calls[2]["blobs"]
            ha, hb = n_[ms.PUBLICDOC + u"0100000_a_E99991-000_ixbrl.htm"].decode("utf-8"), m_[ms.PUBLICDOC + u"0100000_a_E99991-000_ixbrl.htm"].decode("utf-8")
            if u"CurrentYearDuration_NonConsolidatedMember" in ha or hb.count(u"CurrentYearDuration_NonConsolidatedMember") != 4 or u'contextRef="Prior1YearInstant_CapitalStockMember"' not in ha:
                out_.append(u"組み直した包みの字に作った文脈が入っていない・混ぜ物の包みが混ぜ物の分だけ違わない")
            for k in (u"XBRL/PublicDoc/manifest_PublicDoc.xml", u"XBRL/PublicDoc/logo.png", u"XBRL/AuditDoc/audit.xml"):
                if n_[k] != r.calls[0]["blobs"][k]:
                    out_.append(u"組み直した包みのほかの file が元のままでない")
        verbs = [c["verb"] for c in proc.calls]
        if verbs != ["make", "make", "build", "build", "make", "build"]:
            out_.append(u"別の process の呼び出しの並びが違う: %s" % verbs)
        else:
            for c in proc.calls:
                want_script = ms.SCRIPT_PATH if c["verb"] == "make" else ms.P.SCRIPT_PATH
                if c["cmd"][:3] != [sys.executable, "-I", want_script] or len(c["cmd"]) != 6 or c["timeout"] != 600 or c["listing"] != []:
                    out_.append(u"別の process の呼び出しの形が違う(python -I・script・引数 2 つ・時間の上限・空の cwd): %s" % c["cmd"][:4])
                    break
            if proc.calls[0]["folder_files"] != FOLDER_FILES or proc.calls[2]["folder_files"] != sorted([u"index.json", u"t0000.json", u"t0000.txt", u"t0001.json", u"t0001.txt", u"taxonomy.json"]):
                out_.append(u"別の process に渡した folder の中身が違う(型の folder・原稿の folder)")
            if len(set(c["cwd"] for c in proc.calls)) != 1 or any(os.path.dirname(c["cwd"]) == os.path.dirname(c["folder"]) and c["cwd"] == c["folder"] for c in proc.calls):
                out_.append(u"cwd が書類の folder と同じ・呼びごとに違う")
        if read_bytes_sha(zp) != before:
            out_.append(u"置き場の zip を書き換えた")
        if os.listdir(tmp):
            out_.append(u"使い捨ての場所が残っている")
        if sorted(os.listdir(keep)) != [u"manuscript", u"type"] or tree_of(os.path.join(keep, "type")) != tree_of(tf2) or u"index.json" not in os.listdir(os.path.join(keep, "manuscript")):
            out_.append(u"--keep の folder(型・組んだ原稿)が残っていない")
        # 2 度走らせて同じ数(秒は除く)
        rec2, _r2, _p2, _z2, _t2 = doc_run(ms, os.path.join(d, "again")) if os.makedirs(os.path.join(d, "again")) is None else (None,) * 5
        if plain_rec(rec2)[0] != got:
            out_.append(u"同じ書類を 2 度掛けると数が違う")
        # 戻る版: 全部同じ
        rec3, _r3, _p3, _z3, _t3 = doc_run(ms, os.path.join(d, "good")) if False else (None,) * 5
    with Temp() as d:
        rec, r, proc, zp, tmp = doc_run(ms, d, a=HTM_A_TEXT.replace(P1I_COMP, P1I_CAP))
        c1 = plain_rec(rec)[0][u"比べ方 1"]
        if c1 != {u"属性が意味として同じ": False, u"文脈の名も同じ": True, u"違った fact": 1, u"属性ごとの違った fact": {u"scale": 1}}:
            out_.append(u"属性は違うが文脈の名は全部同じ版の比べ方 1 が違う: %s" % c1)
    with Temp() as d:
        rec, r, proc, zp, tmp = doc_run(ms, d, a=good_variant(HTM_A_TEXT))
        c1 = plain_rec(rec)[0][u"比べ方 1"]
        c2 = plain_rec(rec)[0][u"比べ方 2"]
        if c1 != {u"属性が意味として同じ": True, u"文脈の名も同じ": True, u"違った fact": 0, u"属性ごとの違った fact": {}} or c2 != {u"組めた": True, u"fact が意味として同じ": True, u"字も含めて行が同じ": True, u"鳴り方が同じ": True, u"2 回が同じ": True}:
            out_.append(u"戻る版の比べ方 1・2 が全部同じでない: %s %s" % (c1, c2))
        if plain_rec(rec)[0][u"文脈の定義"] != {u"作った": 9, u"作らなかった": 1}:
            out_.append(u"戻る版の定義の数が違う")
    with Temp() as d:
        # 元に在って型の外にも無い単位の定義(どの fact も使わない)が 1 つ → 作らなかった単位の定義は 1
        rec, r, proc, zp, tmp = doc_run(ms, d, a=HTM_A_TEXT.replace(u"</ix:resources>", un(u"UnusedEUR", u"iso4217:EUR") + u"\n</ix:resources>"))
        pr = plain_rec(rec)[0]
        if pr[u"断った"] or pr[u"単位の定義"] != {u"作った": 4, u"作らなかった": 1} or pr[u"文脈の定義"] != {u"作った": 9, u"作らなかった": 1}:
            out_.append(u"使われない単位の定義がある版の定義の数が違う: %s %s" % (pr[u"断った"], pr[u"単位の定義"]))
    return out_


MINI_A = u"<html><body>%s%s</body></html>" % (HEADER, nn(u"jpcrp_cor:Text", CYD, u"x"))
MINI_B = u"<html><body><p>x</p></body></html>"


class HookProc(Proc):
    u"""出す folder の書き込みの後に ``after(verb, 何回目, out)`` を呼ぶ作り物。"""

    def __init__(self, ms, after=None, **kw):
        Proc.__init__(self, ms, **kw)
        self.after = after

    def __call__(self, cmd, cwd, timeout):
        res = Proc.__call__(self, cmd, cwd, timeout)
        verb = cmd[3]
        if self.after is not None and res[0] == 0:
            self.after(verb, sum(1 for c in self.calls if c["verb"] == verb), cmd[-1])
        return res


class TimeoutProc(Proc):
    def __call__(self, cmd, cwd, timeout):
        Proc.__call__(self, cmd, cwd, timeout)
        return None, u"", True


EMPTY_PART = {u"断った": True}


def decline_doc_problems(ms=None):
    ms = ms or MS
    out_ = []
    zero = json.loads(json.dumps(ms.zero_rec()))
    zero.pop(u"秒")

    def run_case(proc=None, runner_cls=None, a=None, b=None, **rkw):
        with Temp() as d:
            rec, r, p, zp, tmp = doc_run(ms, d, proc=proc, runner_cls=runner_cls, rkw=rkw, a=a, b=b)
            return plain_rec(rec), r, p
    # ---- 型を作る
    cases = [(u"当期の終わりの文脈が無い", dict(a=HTM_A_TEXT.replace(u"CurrentYearInstant", u"CurYI")), u"書類の決めが 1 通りに決まらない"), (u"文脈の定義が無い fact", dict(a=HTM_A_TEXT.replace(u'contextRef="OddInstant"', u'contextRef="Nowhere"', 1)), u"文脈の定義が無い fact"),
             (u"知らない ix の要素(落とす側の断り)", dict(a=HTM_A_TEXT + u"<ix:zzz>"), u"知らない ix の要素"), (u"resources が 2 つ", dict(b=u"<html><body><ix:header>\n<ix:resources>\n</ix:resources>\n</ix:header></body></html>"), u"resources の部が 2 つ以上")]
    for what, kw, reason in cases:
        (got, _s), r, p = run_case(**kw)
        want = dict(zero, **{u"断った": True, u"断った段": u"型を作る", u"断った理由": reason})
        if got != want or len(r.calls) != 1 or p.calls:
            out_.append(u"断り(型を作る・%s)が違う: %s %d %d" % (what, [(k, got[k]) for k in got if got[k] != want[k]][:3], len(r.calls), len(p.calls)))
    # ---- 型から作る
    for what, proc, reason in ((u"断り", Proc(ms, fail=("make", 1, (2, u"x\nDECLINE: 固定の理由\n"))), u"固定の理由"), (u"例外", Proc(ms, fail=("make", 1, (1, u"ERROR\n"))), u"型から作る命令が 0 でない終わりの値で終わった"),
                               (u"使い方", Proc(ms, fail=("make", 1, (64, u"使い方: make\n"))), u"型から作る命令が 0 でない終わりの値で終わった"), (u"時間", TimeoutProc(ms), u"型から作る命令が時間の上限を超えた"),
                               (u"長い理由", Proc(ms, fail=("make", 1, (2, u"DECLINE: " + u"あ" * 100 + u"\n"))), u"あ" * 80)):
        (got, secs), r, p = run_case(proc=proc)
        want = dict(EXPECT_REC, **{u"断った": True, u"断った段": u"型から作る", u"断った理由": reason})
        for k in (u"比べ方 1", u"文脈の定義", u"単位の定義", u"比べ方 2", u"混ぜ物"):
            want[k] = zero[k]
        if got != want or len(r.calls) != 1 or len(p.calls) != 1 or secs[u"型から作る命令"] is None:
            out_.append(u"断り(型から作る・%s)が違う: %s tool=%d proc=%d" % (what, [(k, got[k]) for k in got if got[k] != want[k]][:3], len(r.calls), len(p.calls)))
    # ---- 組む
    (got, _s), r, p = run_case(proc=Proc(ms, fail=("build", 1, (2, u"DECLINE: 組めない\n"))))
    want = dict(EXPECT_REC, **{u"断った": True, u"断った段": u"組む", u"断った理由": u"組めない"})
    for k in (u"比べ方 2", u"混ぜ物"):
        want[k] = zero[k]
    if got != want or len(r.calls) != 1 or [c["verb"] for c in p.calls] != ["make", "make", "build"]:
        out_.append(u"断り(組む)が違う: %s" % [(k, got[k]) for k in got if got[k] != want[k]][:3])

    def drop_first(verb, n, out):
        if verb == "build" and n == 1:
            os.remove(os.path.join(out, sorted(os.listdir(out))[0]))
    (got, _s), r, p = run_case(proc=HookProc(ms, after=drop_first))
    if got[u"断った段"] != u"組む" or got[u"断った理由"] != u"出す folder の file の名が目次と合わない" or len(r.calls) != 1:
        out_.append(u"出す folder の file の名が目次と合わないのに断らない: %s %s" % (got[u"断った段"], got[u"断った理由"]))
    # ---- 道具
    (got, _s), r, p = run_case(runner_cls=FactRunner, stop_at=2)
    want = dict(EXPECT_REC, **{u"断った": True, u"断った段": u"道具", u"断った理由": u"道具が組み直した包みで止まった"})
    want[u"比べ方 2"] = dict(zero[u"比べ方 2"], **{u"2 回が同じ": True})
    want[u"混ぜ物"] = zero[u"混ぜ物"]
    if got != want or len(r.calls) != 2:
        out_.append(u"断り(道具)が違う: %s tool=%d" % ([(k, got[k]) for k in got if got[k] != want[k]][:3], len(r.calls)))
    (got, _s), r, p = run_case(runner_cls=FactRunner, stop_at=1)
    if got[u"断った"] or len(r.calls) != 3:
        out_.append(u"元だけが止まったのに断った: %s" % got[u"断った"])
    (got, _s), r, p = run_case(runner_cls=FactRunner, stop_all=True)
    if got[u"断った"] or len(r.calls) != 3:
        out_.append(u"元も止まったのに組み直しの止まりで断った(元が止まっていないときだけ断る): %s" % got[u"断った"])
    # ---- 2 回が同じ
    base_ok = dict(EXPECT_REC)
    for what, proc in ((u"2 回目の型から作る命令が断る", Proc(ms, fail=("make", 2, (2, u"DECLINE: x\n")))), (u"2 回目の組む命令が断る", Proc(ms, fail=("build", 2, (2, u"DECLINE: x\n"))))):
        (got, _s), r, p = run_case(proc=proc)
        want = dict(base_ok, **{u"比べ方 2": dict(base_ok[u"比べ方 2"], **{u"2 回が同じ": False})})
        if got != want:
            out_.append(u"%s: %s" % (what, [(k, got[k]) for k in got if got[k] != want[k]][:3]))

    def mangle_make2(verb, n, out):
        if verb == "make" and n == 2:
            write_file(os.path.join(out, "extra.txt"), b"x")

    def mangle_build2(verb, n, out):
        if verb == "build" and n == 2:
            p_ = os.path.join(out, sorted(os.listdir(out))[0])
            write_file(p_, read_file(p_) + b" ")
    for what, hook in ((u"2 回目の型から作る命令が違う字を書く", mangle_make2), (u"2 回目の組む命令が違う字を書く", mangle_build2)):
        (got, _s), r, p = run_case(proc=HookProc(ms, after=hook))
        if got[u"比べ方 2"][u"2 回が同じ"] or not got[u"比べ方 2"][u"組めた"] or got[u"断った"]:
            out_.append(u"%s のに 2 回が同じと言う" % what)
    # ---- 混ぜ物を作れない
    (got, _s), r, p = run_case(a=MINI_A, b=MINI_B)
    if got[u"混ぜ物"] != {u"作れた": False, u"効いた": False} or len(r.calls) != 2 or got[u"断った"] or got[u"比べ方 2"][u"組めた"] is not True:
        out_.append(u"混ぜ物の当て先が無い書類: %s tool=%d" % (got[u"混ぜ物"], len(r.calls)))
    if got[u"型の行"][u"数"] != 0 or got[u"型の行"][u"文"] != 2 or got[u"型の外の fact"][u"合計"] != pair(1, 0) or got[u"表示の字の検査"] != {u"掛けた fact": 0, u"合った fact": 0}:
        out_.append(u"最小の書類の数が違う: %s" % got[u"型の行"])
    for what, proc in ((u"混ぜ物の型から作る命令が断る", Proc(ms, fail=("make", 3, (2, u"DECLINE: x\n")))), (u"混ぜ物の組む命令が断る", Proc(ms, fail=("build", 3, (2, u"DECLINE: x\n"))))):
        (got, _s), r, p = run_case(proc=proc)
        if got[u"混ぜ物"] != {u"作れた": False, u"効いた": False} or len(r.calls) != 2 or got[u"断った"]:
            out_.append(u"%s のに混ぜ物を作れたと言う: %s" % (what, got[u"混ぜ物"]))

    def drop_mix(verb, n, out):
        if verb == "build" and n == 3:
            os.remove(os.path.join(out, sorted(os.listdir(out))[0]))
    (got, _s), r, p = run_case(proc=HookProc(ms, after=drop_mix))
    if got[u"混ぜ物"] != {u"作れた": False, u"効いた": False} or len(r.calls) != 2:
        out_.append(u"混ぜ物の出す folder の名が目次と合わないのに作れたと言う")
    # ---- 混ぜ物が効かない(道具の作り物が、混ぜ物の包みで元と同じ行を返す)
    class DeafRunner(FactRunner):
        def facts_rows(self, blobs):
            rows = FactRunner.facts_rows(self, blobs)
            if len(self.calls) == 3:
                return [x for x in rows if len(x) <= 9]
            return rows
    (got, _s), r, p = run_case(runner_cls=DeafRunner)
    if got[u"混ぜ物"] != {u"作れた": True, u"効いた": False}:
        out_.append(u"混ぜ物の包みで道具の行が次元の組を持たないのに効いたと言う: %s" % got[u"混ぜ物"])
    # ---- carry_forbidden が何かを言えば止まる
    saved = ms.carry_forbidden
    ms.carry_forbidden = lambda folder: [u"x"]
    try:
        with Temp() as d:
            if not stops(ms, doc_run, ms, d):
                out_.append(u"持ち込みに入れないものが在るのに止まらない")
    finally:
        ms.carry_forbidden = saved
    return out_


# ======================================================================== 7. 数える
def mk(i=0, declined=None, **ov):
    r = json.loads(json.dumps(MS.zero_rec()), object_pairs_hook=od)
    r[u"番号"] = i
    r.move_to_end(u"番号", last=False)
    if declined:
        r[u"断った"], r[u"断った段"], r[u"断った理由"] = True, declined[0], declined[1]
    for k, v in ov.items():
        r[k] = v
    return r


def totals_problems(ms=None):
    ms = ms or MS
    out_ = []
    e1 = mk(1, **{u"対象の fact": {u"数": 10, u"文": 4, u"隠し": 2, u"脚注": 1}, u"型に入った fact": pair(9, 4), u"型の外の fact": {u"理由ごと": dict((k, pair(0, 0)) for k in "abcdefgh"), u"合計": pair(1, 0)},
                  u"型の行": {u"数": 8, u"文": 3, u"2 つ以上の fact をまとめた行": 1, u"値が -0 の行": 1}, u"文脈の定義": {u"作った": 5, u"作らなかった": 0}, u"秒": {u"型から作る命令": 0.5},
                  u"比べ方 2": {u"組めた": True, u"fact が意味として同じ": True, u"字も含めて行が同じ": True, u"鳴り方が同じ": True, u"2 回が同じ": True}, u"混ぜ物": {u"作れた": True, u"効いた": True}, u"表示の字の検査": {u"掛けた fact": 7, u"合った fact": 7}})
    e1[u"型の外の fact"][u"理由ごと"][u"e"] = pair(1, 0)
    e2 = mk(2, **{u"対象の fact": {u"数": 20, u"文": 6, u"隠し": 2, u"脚注": 3}, u"型に入った fact": pair(18, 6), u"型の外の fact": {u"理由ごと": dict((k, pair(0, 0)) for k in "abcdefgh"), u"合計": pair(2, 0)},
                  u"型の行": {u"数": 17, u"文": 5, u"2 つ以上の fact をまとめた行": 2, u"値が -0 の行": 0}, u"文脈の定義": {u"作った": 9, u"作らなかった": 2}, u"秒": {u"型から作る命令": 1.25},
                  u"比べ方 2": {u"組めた": True, u"fact が意味として同じ": False, u"字も含めて行が同じ": False, u"鳴り方が同じ": True, u"2 回が同じ": True}, u"混ぜ物": {u"作れた": True, u"効いた": False}, u"表示の字の検査": {u"掛けた fact": 13, u"合った fact": 12},
                  u"比べ方 1": {u"属性が意味として同じ": True, u"文脈の名も同じ": True, u"違った fact": 0, u"属性ごとの違った fact": {}}})
    e2[u"型の外の fact"][u"理由ごと"][u"a"] = pair(1, 1)
    e2[u"型の外の fact"][u"理由ごと"][u"e"] = pair(1, 0)
    e3 = mk(3, declined=(u"型を作る", u"理由 X"))
    e4 = mk(4, declined=(u"組む", u"理由 Y"), **{u"秒": {u"型から作る命令": 2.0}})
    e5 = mk(5, declined=(u"組む", u"理由 Y"))
    e6 = mk(6, **{u"型の外の fact": {u"理由ごと": dict((k, pair(0, 0)) for k in "abcdefgh"), u"合計": pair(0, 0)}, u"文脈の定義": {u"作った": 1, u"作らなかった": 1}})
    t = ms.group_totals([e1, e2, e3, e4, e5, e6])
    z = t[u"数"]
    want_checks = [
        (u"書類", t[u"書類"], 6), (u"断った書類", t[u"断った書類"], 3), (u"断った段と理由", {k: dict(v) for k, v in t[u"断った段と理由ごと"].items()}, {u"型を作る": {u"理由 X": 1}, u"型から作る": {}, u"組む": {u"理由 Y": 2}, u"道具": {}}),
        (u"型の外が 0 の書類(断った書類は数えない)", t[u"型の外の fact が 0 の書類"], 1), (u"対象の数", z[u"対象の fact"][u"数"], 30), (u"対象の隠し", z[u"対象の fact"][u"隠し"], 4), (u"脚注", z[u"対象の fact"][u"脚注"], 4),
        (u"型の外の合計", dict(z[u"型の外の fact"][u"合計"]), {u"数": 3, u"文": 0}), (u"型の外 e", dict(z[u"型の外の fact"][u"理由ごと"][u"e"]), {u"数": 2, u"文": 0}), (u"型の外 a", dict(z[u"型の外の fact"][u"理由ごと"][u"a"]), {u"数": 1, u"文": 1}),
        (u"型の行 数", z[u"型の行"][u"数"], 25), (u"型の行 -0", z[u"型の行"][u"値が -0 の行"], 1), (u"まとめた行", z[u"型の行"][u"2 つ以上の fact をまとめた行"], 3),
        (u"作った文脈", z[u"文脈の定義"][u"作った"], 15), (u"作らなかった文脈", z[u"文脈の定義"][u"作らなかった"], 3), (u"作らなかった文脈が 1 つ以上の書類", t[u"作らなかった文脈の定義が 1 つ以上在る書類"], 2),
        (u"比べ方 2 fact", z[u"比べ方 2"][u"fact が意味として同じ"], 1), (u"比べ方 2 組めた", z[u"比べ方 2"][u"組めた"], 2), (u"混ぜ物", dict(z[u"混ぜ物"]), {u"作れた": 2, u"効いた": 1}),
        (u"表示の字", dict(z[u"表示の字の検査"]), {u"掛けた fact": 20, u"合った fact": 19}), (u"秒の合計(None は 0)", t[u"型から作る命令の秒の合計"], 3.8), (u"比べ方 1 の同じ", z[u"比べ方 1"][u"属性が意味として同じ"], 1)]
    for what, got, want in want_checks:
        if got != want:
            out_.append(u"集計(%s): %r (手で数えた値は %r)" % (what, got, want))
    # 開発の本数で分ける
    tt = ms.totals_of([e1, e2, e3, e4, e5, e6], 2)
    if [k for k in tt] != [u"開発の 5 本", u"本番だけの 4 本", u"全部"] or tt[u"開発の 5 本"][u"書類"] != 2 or tt[u"本番だけの 4 本"][u"書類"] != 4 or tt[u"全部"][u"書類"] != 6:
        out_.append(u"開発と本番の分け方が違う: %s" % [(k, v[u"書類"]) for k, v in tt.items()])
    if tt[u"開発の 5 本"][u"数"][u"型の行"][u"数"] != 25 or tt[u"本番だけの 4 本"][u"数"][u"型の行"][u"数"] != 0 or tt[u"本番だけの 4 本"][u"断った書類"] != 3:
        out_.append(u"開発の数が本番に混ざる・本番の数が開発に混ざる")
    t0 = ms.group_totals([])
    if t0[u"書類"] != 0 or t0[u"断った書類"] != 0 or t0[u"型の外の fact が 0 の書類"] != 0 or t0[u"型から作る命令の秒の合計"] != 0:
        out_.append(u"空の並びの集計が 0 でない")
    t1 = ms.group_totals([e6])
    if t1[u"型の外の fact が 0 の書類"] != 1 or t1[u"書類"] != 1 or t1[u"数"][u"文脈の定義"][u"作った"] != 1:
        out_.append(u"1 本の集計が違う")
    # sum_nested
    sn = ms.sum_nested([od([("a", 1), ("b", od([("c", True), ("s", u"x"), ("n", None)]))]), od([("a", 2), ("b", od([("c", False), ("d", 5)])), ("z", u"s")])])
    if json.loads(json.dumps(sn)) != {"a": 3, "b": {"c": 1, "d": 5}}:
        out_.append(u"sum_nested が手で決めた値と違う: %s" % sn)
    if ms.sum_nested([]) != od():
        out_.append(u"sum_nested([]) が空でない")
    # 判定に要る数
    full = [mk(i) for i in range(1, 6)]
    prod = [mk(6 + i, **{u"型の外の fact": {u"理由ごと": dict((k, pair(0, 0)) for k in "abcdefgh"), u"合計": pair(0, 0)}}) for i in range(4)]
    prod[0][u"対象の fact"] = {u"数": 100, u"文": 50, u"隠し": 2, u"脚注": 0}
    prod[0][u"型に入った fact"] = pair(96, 50)
    prod[0][u"型の外の fact"] = {u"理由ごと": dict((k, pair(0, 0)) for k in "abcdefgh"), u"合計": pair(4, 2)}
    prod[0][u"型の外の fact"][u"理由ごと"][u"a"] = pair(3, 2)
    prod[0][u"型の外の fact"][u"理由ごと"][u"e"] = pair(1, 0)
    prod[0][u"型の行"] = {u"数": 90, u"文": 40, u"2 つ以上の fact をまとめた行": 0, u"値が -0 の行": 0}
    prod[0][u"比べ方 2"] = {u"組めた": True, u"fact が意味として同じ": True, u"字も含めて行が同じ": True, u"鳴り方が同じ": True, u"2 回が同じ": True}
    prod[1][u"比べ方 2"] = {u"組めた": True, u"fact が意味として同じ": True, u"字も含めて行が同じ": False, u"鳴り方が同じ": False, u"2 回が同じ": True}
    prod[1][u"比べ方 1"] = {u"属性が意味として同じ": True, u"文脈の名も同じ": True, u"違った fact": 0, u"属性ごとの違った fact": {}}
    prod[2][u"混ぜ物"] = {u"作れた": True, u"効いた": True}
    prod[3][u"混ぜ物"] = {u"作れた": True, u"効いた": False}
    prod[2][u"文脈の定義"] = {u"作った": 1, u"作らなかった": 4}
    prod[3][u"表示の字の検査"] = {u"掛けた fact": 200, u"合った fact": 199}
    prod.append(mk(10, declined=(u"組む", u"理由 Y")))
    allrec = full + prod
    tot = ms.totals_of(allrec, 5)
    j = ms.judged(tot, 10)
    jj = dict((k.split(" ")[0], v) for k, v in j.items())
    want_j = {
        "XM0-1": {u"書類": 2, u"分母": 5}, "XM0-2": {u"書類": 3, u"分母": 5}, "XM0-3": {u"fact": 6, u"分母(対象の fact)": 150}, "XM0-4": dict((k, 0) for k in "abcdefgh"),
        "XM0-5": {u"書類": 1, u"分母": 5}, "XM0-6": {u"書類": 1, u"分母": 5}, "XM0-7": {u"書類": 1, u"分母": 5}, "XM0-8": {u"効いた": 1, u"作れた": 2}, "XM0-9": {u"行": 90, u"分母(型に入った数の fact)": 96},
        "XM0-10": {u"合った": 199, u"分母(掛けた fact)": 200}}
    want_j["XM0-4"].update({"a": 5, "e": 1})
    if [k.split(" ")[0] for k in j] != list(want_j):
        out_.append(u"判定に要る数の欄の並びが違う: %s" % list(j))
    for k, w in want_j.items():
        if json.loads(json.dumps(jj.get(k))) != w:
            out_.append(u"判定に要る数(%s): %s (手で数えた値は %s)" % (k, json.dumps(jj.get(k), ensure_ascii=False), w))
    return out_


def tools_problems(ms=None):
    ms = ms or MS
    out_ = []
    wp = hashlib.sha256(X.MV_P).hexdigest()
    with Temp() as d:
        tool, mv = X.make_tool(d)
        r = X.FakeRunner(mv)
        info = ms.check_tool(tool, r, read_bytes_sha, want_sha=wp)
        if (info[u"版"], info[u"ModelValue.py の sha256"]) != (u"2.47.5", wp):
            out_.append(u"道具の情報が違う: %s" % dict(info))
        if not stops(ms, ms.check_tool, tool, r, want_sha=wp, want_version=u"2.47.6") or not stops(ms, ms.check_tool, tool, r, want_sha=u"0" * 64) or not stops(ms, ms.check_tool, tool, r):
            out_.append(u"版・sha256 が封と違うのに止まらない")
        if not stops(ms, ms.check_tool, os.path.join(d, "none"), r, want_sha=wp):
            out_.append(u"道具の場所が無いのに止まらない")
    return out_


def make_docs_dir(d, count=3, variants=None):
    for i in range(count):
        a = (variants or {}).get(i + 1)
        make_doc(os.path.join(d, "S2FAKE0%d.zip" % (i + 1)), i + 1, a=a)
    with zipfile.ZipFile(os.path.join(d, "S2OTHER1.zip"), "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


def dev_docs_problems(ms=None):
    u"""開発の入口は 5 本だけ: 7 本以上の zip で ``dev_docs`` は 5 本を選んだ所で止まり、6 本目を開かない。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        make_docs_dir(d, 7)
        opened = []
        bz = ms.B.zipfile
        real = bz.ZipFile

        class Counting(real):
            def __init__(self, f, *a, **kw):
                opened.append(os.path.basename(str(f)))
                real.__init__(self, f, *a, **kw)
        bz.ZipFile = Counting
        try:
            got = ms.dev_docs(d, 5)
            got_default = ms.dev_docs(d)
        finally:
            bz.ZipFile = real
        want = [u"S2FAKE0%d" % i for i in range(1, 6)]
        if [g[0] for g in got] != want or [g[0] for g in got_default] != want:
            out_.append(u"開発の 5 本が並びの頭の 5 本でない: %s" % [g[0] for g in got])
        if opened != [u"S2FAKE0%d.zip" % i for i in range(1, 6)] * 2:
            out_.append(u"開いた zip が並びの頭の 5 本だけでない: %s" % opened)
        if ms.DEV_COUNT != 5 or ms.dev_docs.__defaults__ != (5,):
            out_.append(u"dev_docs の既定の本数が 5 でない")
    return out_


# ======================================================================== 8. 記録
STEMS = [u"S2FAKE01", u"S2FAKE02", u"S2FAKE03"]
ORDER_SHA = hashlib.sha256(u"\n".join(STEMS).encode("utf-8")).hexdigest()
DOC_VARIANTS = {2: good_variant(HTM_A_TEXT), 3: HTM_A_TEXT.replace(u"CurrentYearInstant", u"CurYI")}


def record_args(d, ms, runner=None, count=3, proc=None, **kw):
    docs = os.path.join(d, "docs")
    os.makedirs(docs)
    make_docs_dir(docs, count, DOC_VARIANTS)
    tool, mv = X.make_tool(os.path.join(d, "tool"))
    tmp = os.path.join(d, "tmp")
    os.makedirs(tmp)
    runner = runner or FactRunner(mv)
    proc = proc or Proc(ms)
    args = dict(want=count, runner=runner, tmp_root=tmp, want_sha=hashlib.sha256(X.MV_P).hexdigest(), dev_count=1, proc=proc)
    args.update(kw)
    return tool, docs, runner, tmp, args


def run_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        keep = os.path.join(d, "keep")
        tool, docs, runner, tmp, args = record_args(d, ms)
        progress = []
        rec, secret = ms.build_record(tool, docs, progress=progress.append, keep=keep if os.makedirs(keep) is None else None, **args)
        # 1 本目・2 本目は道具 3 回・別の process 6 回。3 本目は型を作る所で断るので道具 1 回(元の包み)・別の process 0 回
        if len(runner.calls) != 3 + 3 + 1 or len(args["proc"].calls) != 6 + 6 + 0:
            out_.append(u"道具の呼び出し・別の process の呼び出しの数が違う: %d・%d" % (len(runner.calls), len(args["proc"].calls)))
        if len(progress) != 3 or not progress[0].startswith(u"doc 1/3("):
            out_.append(u"書類ごとの進みを出さない: %s" % progress)
        mat = rec[u"材料"]
        if (mat[u"書類の本数"], mat[u"書類の file 名の並びの sha256"], mat[u"開発の 5 本の番号"], mat[u"道具の版"], mat[u"道具 P の ModelValue.py の sha256"], mat[u"規則の年"], mat[u"時間の上限(秒)"], mat[u"混ぜ物の種類"]) != (
                3, ORDER_SHA, [1], u"2.47.5", hashlib.sha256(X.MV_P).hexdigest(), u"EDINET-2026", 600, [ms.MIX_KIND]):
            out_.append(u"材料の欄が手で数えた値と違う: %s" % dict(mat))
        if [dd[u"番号"] for dd in rec[u"書類"]] != [1, 2, 3] or [dd[u"断った"] for dd in rec[u"書類"]] != [False, False, True] or rec[u"書類"][2][u"断った段"] != u"型を作る":
            out_.append(u"書類の番号・断った書類が違う")
        t = rec[u"集計"]
        if (t[u"開発の 5 本"][u"書類"], t[u"本番だけの 2 本"][u"書類"], t[u"全部"][u"書類"], t[u"本番だけの 2 本"][u"断った書類"], t[u"開発の 5 本"][u"断った書類"], t[u"全部"][u"数"][u"比べ方 2"][u"fact が意味として同じ"]) != (1, 2, 3, 1, 0, 2):
            out_.append(u"集計が手で数えた値と違う")
        if t[u"全部"][u"数"][u"対象の fact"][u"数"] != 47 * 2 or t[u"全部"][u"数"][u"型の外の fact"][u"合計"][u"数"] != 27 * 2:
            out_.append(u"全部の対象の fact の数が手で数えた値と違う(断った書類は数えない)")
        if rec[u"この script の sha256"] != sha_of(SCRIPT_REL) and ms is MS:
            out_.append(u"記録の script の sha256 が違う")
        text = ms.dumps(rec)
        for leak in STEMS + [u"E9999", u"S2OTHER1", u".xbrl", u".htm", u".xsd", u"audit", u"Alpha", u"Beta", u"Gamma", u"jppfs", u"jpcrp", u"jpdei", u"http", u"Assets", u"BOnly", u"Profit", u"OtherEntity", u"OddInstant",
                             u"PublicDoc", u"1,234", u"index.json", u"Prior1Year", u"注記", u"続き", u"2026-03-31", u"2025-04-01", u"SegAxis", u"Member", u"K0001", u"ixt:numcomma"]:
            if leak in text:
                out_.append(u"記録に材料の字が在る: %s" % leak)
        if set(secret[3]) != set([u"E9999%d" % i for i in (1, 2, 3)]) or list(secret[2]) != STEMS or not {"Alpha", "Gamma", "BetaHeading"} <= set(secret[1]) or X.TXT1 not in secret[0]:
            out_.append(u"secret の docID・EDINET コード・要素の名・ラベルの字が違う")
        if os.listdir(tmp):
            out_.append(u"使い捨ての場所が残っている")
        if sorted(os.listdir(keep)) != [u"doc01", u"doc02", u"doc03"] or sorted(os.listdir(os.path.join(keep, "doc01"))) != [u"manuscript", u"type"] or os.listdir(os.path.join(keep, "doc03")) != []:
            out_.append(u"--keep の書類ごとの folder が違う")
        r2 = FactRunner(runner.mv_path)
        a2 = dict(args, runner=r2, want=67, proc=Proc(ms))
        if not stops(ms, ms.build_record, tool, docs, **a2) or r2.calls or a2["proc"].calls:
            out_.append(u"書類が 67 本でないのに止まらない(か掛けた)")
        r3 = FactRunner(runner.mv_path)
        a3 = dict(args, runner=r3, want_sha=u"0" * 64, proc=Proc(ms))
        if not stops(ms, ms.build_record, tool, docs, **a3) or r3.calls or a3["proc"].calls:
            out_.append(u"道具の sha256 が封と違うのに止まらない(か掛けた)")
    return out_


def verify_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms)
        rec, secret = ms.build_record(tool, docs, **args)
        p = os.path.join(d, "r.json")
        ms.write_record(p, rec, secret)
        if stops(ms, ms.check, rec_path=p, want=3, say=lambda *a: None, dev_count=1):
            out_.append(u"きれいな記録で --check が止まる")
        if not stops(ms, ms.check, rec_path=p, say=lambda *a: None):
            out_.append(u"書類が 67 本でない記録で --check が止まらない")
        if not stops(ms, ms.check, rec_path=os.path.join(d, "none.json"), want=3, say=lambda *a: None):
            out_.append(u"記録が無いのに --check が止まらない")
        base = ms.dumps(rec)
        if read_text(p) != base:
            out_.append(u"書いた字が dumps と違う")

        def refresh_after(fn):
            def go(r):
                fn(r)
                r[u"集計"] = ms.totals_of(r[u"書類"], 1)
                r[[k for k in r if k.startswith(u"予測の判定に要る数")][0]] = ms.judged(r[u"集計"], len(r[u"書類"]))
            return go
        tampers = [
            (u"集計の数を変える", lambda r: r[u"集計"][u"全部"].__setitem__(u"断った書類", 9)),
            (u"書類ごとの比べ方 2 を変える(合計と合わない)", lambda r: r[u"書類"][0][u"比べ方 2"].__setitem__(u"fact が意味として同じ", False)),
            (u"書類ごとの型の行を変える(合計と合わない)", lambda r: r[u"書類"][1][u"型の行"].__setitem__(u"数", 99)),
            (u"書類を 1 本消す", lambda r: r[u"書類"].pop()),
            (u"書類の番号を変える", lambda r: r[u"書類"][0].__setitem__(u"番号", 7)),
            (u"材料の書類の本数だけを変える", lambda r: r[u"材料"].__setitem__(u"書類の本数", 5)),
            (u"欄を消す", lambda r: r[u"書類"][0].pop(u"混ぜ物")),
            (u"欄の並びを変える", lambda r: r[u"書類"][0].move_to_end(u"番号")),
            (u"材料の欄に EDINET コードの形の字を足す", lambda r: r[u"材料"].__setitem__(u"メモ", u"E12345")),
            (u"判定の数を変える", lambda r: [r[k] for k in r if k.startswith(u"予測の判定に要る数")][0].__setitem__(u"XM0-1 fact が意味として同じ書類", 99)),
            (u"断ったのに段が空", refresh_after(lambda r: r[u"書類"][2].__setitem__(u"断った段", u""))),
            (u"断ったのに理由が空", refresh_after(lambda r: r[u"書類"][2].__setitem__(u"断った理由", u""))),
            (u"断った段が知らない値", refresh_after(lambda r: r[u"書類"][2].__setitem__(u"断った段", u"どこか"))),
            (u"断っていないのに段が在る", refresh_after(lambda r: r[u"書類"][1].__setitem__(u"断った段", u"組む"))),
            (u"断っていないのに理由が在る", refresh_after(lambda r: r[u"書類"][1].__setitem__(u"断った理由", u"理由"))),
            (u"断ったのに比べ方 2 の fact が同じ", refresh_after(lambda r: r[u"書類"][2][u"比べ方 2"].__setitem__(u"fact が意味として同じ", True))),
            (u"断ったのに混ぜ物が効いた", refresh_after(lambda r: r[u"書類"][2][u"混ぜ物"].__setitem__(u"効いた", True))),
            (u"作れなかった混ぜ物が効いた", refresh_after(lambda r: (r[u"書類"][0][u"混ぜ物"].__setitem__(u"作れた", False)))),
            (u"表示の字の合った数が掛けた数より多い", refresh_after(lambda r: r[u"書類"][0][u"表示の字の検査"].__setitem__(u"合った fact", 99))),
            (u"型に入った + 型の外 が対象の数と合わない(数)", refresh_after(lambda r: r[u"書類"][0][u"型に入った fact"].__setitem__(u"数", 1))),
            (u"型に入った + 型の外 が対象の数と合わない(文)", refresh_after(lambda r: r[u"書類"][0][u"型の外の fact"][u"合計"].__setitem__(u"文", 9))),
            (u"理由ごとの数が合計より多い(数)", refresh_after(lambda r: r[u"書類"][0][u"型の外の fact"][u"理由ごと"][u"g"].__setitem__(u"数", 28))),
            (u"理由ごとの数が合計より多い(文)", refresh_after(lambda r: r[u"書類"][0][u"型の外の fact"][u"理由ごと"][u"a"].__setitem__(u"文", 3)))]
        for what, fn in tampers:
            r2 = json.loads(base, object_pairs_hook=od)
            fn(r2)
            if ms.dumps(r2) == base or not stops(ms, ms.verify_record, r2, None, 3, 1):
                out_.append(u"記録を変えても検査が止まらない: %s" % what)
    return out_


def clean_problems(ms=None):
    ms = ms or MS
    out_ = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"断った理由", u"固定の理由"), (u"材料の sha256", u"a" * 64)])])])
    secret = ({u"長めのラベルの字"}, {u"NetSalesOfX"}, [u"zzdoc"], {u"E99991"}, {u"[EDINET.EC5611W] ある指摘の行の本文"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out_.append(u"きれいな記録で止まる")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"company", 1)])), (u"禁止の欄(label)", od([(u"label", 1)])), (u"禁止の欄(element)", od([(u"element", 1)])),
        (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])),
        (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])),
        (u"file の名(htm)", od([(u"x", u"0101010_honbun.htm")])), (u"file の名(xsd)", od([(u"x", u"jpcrp030000-asr-001.xsd")])), (u"file の名(PublicDoc)", od([(u"x", u"XBRL/PublicDoc/x")])),
        (u"要素の名", od([(u"x", u"理由 NetSalesOfX")])), (u"ラベルの字", od([(u"x", u"文 長めのラベルの字 文")])),
        (u"role の URI", od([(u"x", u"http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_BalanceSheet")])), (u"role の URI(https)", od([(u"x", u"https://x/y")])),
        (u"指摘の行の本文", od([(u"x", u"文 [EDINET.EC5611W] ある指摘の行の本文 文")]))]
    for what, rec in cases:
        if not stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out_.append(u"%s が止まらない" % what)
        if not stops(ms, ms.record_text, rec, secret):
            out_.append(u"%s が record_text で止まらない" % what)
    with Temp() as d:
        p = os.path.join(d, "r.json")
        bad = od([(u"x", u"E12345")])
        if not stops(ms, ms.write_record, p, bad) or os.path.exists(p):
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


def e2e_problems(ms=None):
    u"""``run`` → 記録 → ``--check`` を作り物の置き場と道具で通す(置き場も道具も開かない)。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms)
        rp = os.path.join(d, "rec", "r.json")
        kw = dict(docs=docs, out=rp, runner=runner, tmp_root=tmp, say=lambda *a: None, want_sha=args["want_sha"], dev_count=1, proc=args["proc"])
        if not stops(ms, ms.run, tool, want=67, **kw) or os.path.exists(rp):
            out_.append(u"書類が 67 本でないのに run が止まらない(か記録を書いた)")
        lines = []
        rec = ms.run(tool, want=3, progress=lines.append, **kw)
        if not os.path.exists(rp) or ms.dumps(rec) != read_text(rp) or len(lines) != 3:
            out_.append(u"記録が書かれていない・字が違う・進みを出さない")
        if not stops(ms, ms.run, tool, want=3, **kw):
            out_.append(u"記録が既に在るのに run が止まらない")
        ms.check(rec_path=rp, want=3, say=lambda *a: None, dev_count=1)
        rp2 = os.path.join(d, "rec", "r2.json")
        kw2 = dict(kw, out=rp2, runner=FactRunner(runner.mv_path), want_sha=u"0" * 64, proc=Proc(ms))
        if not stops(ms, ms.run, tool, want=3, **kw2) or os.path.exists(rp2):
            out_.append(u"道具の sha256 が違うのに記録を書いた")
        rp3 = os.path.join(d, "rec", "r3.json")
        saved = ms.build_record
        leaky = od([(u"x", u"文 長めのラベルの字 文")])
        ms.build_record = lambda *a, **k: (leaky, ({u"長めのラベルの字"}, set(), [], set(), set()))
        try:
            stopped = stops(ms, ms.run, tool, out=rp3, say=lambda *a: None)
        finally:
            ms.build_record = saved
        if not stopped or os.path.exists(rp3):
            out_.append(u"run が秘密の字(secret)を build_record から受けて記録を検査していない")
    return out_


def devrun_problems(ms=None):
    u"""開発の入口(``dev_run``): 置き場の並びの頭の本数だけを掛け、記録は書かない。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        docs = os.path.join(d, "docs")
        os.makedirs(docs)
        make_docs_dir(docs, 7)
        tool, mv = X.make_tool(os.path.join(d, "tool"))
        tmp = os.path.join(d, "tmp")
        os.makedirs(tmp)
        runner, proc = FactRunner(mv), Proc(ms)
        lines = []
        saved = ms.check_tool
        ms.check_tool = lambda t, r=None, *a, **k: saved(t, r, sha_reader=ms.sha256_file, want_sha=hashlib.sha256(X.MV_P).hexdigest())
        try:
            per = ms.dev_run(tool, docs_dir=docs, runner=runner, tmp_root=tmp, say=lines.append, proc=proc)
        finally:
            ms.check_tool = saved
        if len(per) != 5 or len(runner.calls) != 5 * 3 or len(proc.calls) != 5 * 6 or os.path.exists(os.path.join(d, "rec")):
            out_.append(u"開発の入口が 5 本だけ掛けていない: %d 本・道具 %d 回・別の process %d 回" % (len(per), len(runner.calls), len(proc.calls)))
        if len(lines) != 6 or not lines[0].startswith(u"doc 1(") or u'"断った": false' not in lines[0] or u'"fact が意味として同じ": true' not in lines[0] or not lines[-1].startswith(u"開発の 5 本の合計"):
            out_.append(u"開発の入口の出力の形が違う: %s" % lines[:1])
    return out_


def stop_text(ms, fn, *a):
    u"""止まったときの字(止まらなければ空)。"""
    try:
        fn(*a)
    except ms.Stop as exc:
        return str(exc.args[0]) if exc.args else u""
    return u""


def main_problems(ms=None):
    u"""入口(``main``)の引数の読み: make・derive の終わりの値と、記録を読む・道具を要る・--keep が空でないときの止まり。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        zp, ent, files, tf, an = derive_doc(d, ms)
        o = os.path.join(d, "out")
        r, _e = captured(ms.main, ["make", tf, o])
        if r != ("exit", 0) or u"index.json" not in os.listdir(o):
            out_.append(u"main make が 0 で終わり folder を作らない: %s" % (r,))
        t2 = os.path.join(d, "type2")
        r, _e = captured(ms.main, ["derive", zp, t2])
        if r != ("exit", 0) or sorted(os.listdir(t2)) != FOLDER_FILES:
            out_.append(u"main derive が型の folder を作らない: %s" % (r,))
        for args in (["make"], ["make", tf], ["make", tf, os.path.join(d, "o9"), "x"], ["derive"], ["derive", zp], ["derive", zp, os.path.join(d, "o9"), "x"]):
            r, _e = captured(ms.main, args)
            if r != ("exit", 64) or os.path.exists(os.path.join(d, "o9")):
                out_.append(u"main %s の引数の数が違うのに 64 で終わらない: %s" % (args[0], r))
        r, e = captured(ms.main, ["derive", zp, os.path.join(d, "t3")] if False else ["derive", os.path.join(d, "none.zip"), os.path.join(d, "t4")])
        if r != ("exit", 1) or os.path.exists(os.path.join(d, "t4")):
            out_.append(u"main derive が zip を読めない例外で 1 で終わらない: %s" % (r,))
        zd = os.path.join(d, "decl.zip")
        make_doc(zd, 1, a=HTM_A_TEXT.replace(u"CurrentYearInstant", u"CurYI"))
        r, e = captured(ms.main, ["derive", zd, os.path.join(d, "t5")])
        if r != ("exit", 2) or u"DECLINE: 書類の決めが 1 通りに決まらない" not in e.splitlines() or os.path.exists(os.path.join(d, "t5")):
            out_.append(u"main derive が断りを 2 と理由の行で出さない: %s %r" % (r, e[-100:]))
        bad = clone_folder(tf, os.path.join(d, "badtype"))
        edit_json(bad, "type.json", lambda t: t["rows"][0].__setitem__("target", u"連結"))
        r, e = captured(ms.main, ["make", bad, os.path.join(d, "o6")])
        if r != ("exit", 2) or u"DECLINE: 型の対象が知らない値" not in e.splitlines() or os.path.exists(os.path.join(d, "o6")):
            out_.append(u"main make が断りを 2 と理由の行で出さない: %s %r" % (r, e[-100:]))
        os.makedirs(os.path.join(d, "o7"))
        r, e = captured(ms.main, ["make", tf, os.path.join(d, "o7")])
        if r != ("exit", 1) or u"DECLINE" in e:
            out_.append(u"main make が例外で 1 で終わらない: %s" % (r,))
        r, _e = captured(ms.main, ["--check", "--root", os.path.join(d, "noroot")]) if False else (None, None)
        if u"在る記録が無い" not in stop_text(ms, ms.main, ["--check", "--root", os.path.join(d, "noroot")]):
            out_.append(u"--check が記録の無い所で止まらない")
        if u"--tool-p が要る" not in stop_text(ms, ms.main, ["--dev"]) or u"--tool-p が要る" not in stop_text(ms, ms.main, ["--root", d]):
            out_.append(u"--tool-p が無いのに止まらない")
        kd = os.path.join(d, "keepdir")
        os.makedirs(kd)
        write_file(os.path.join(kd, "x"), b"x")
        if u"--keep の場所が空でない" not in stop_text(ms, ms.main, ["--dev", "--tool-p", os.path.join(d, "none"), "--keep", kd]):
            out_.append(u"--keep の場所が空でないのに止まらない")
        r, e = captured(ms.make_main, [tf])
        if r != 64:
            out_.append(u"make_main が引数 1 つで 64 を返さない")
        if ms.make_main([tf, os.path.join(d, "o10")]) != 0 or ms.derive_main([zp, os.path.join(d, "t10")]) != 0:
            out_.append(u"make_main・derive_main が成功で 0 を返さない")
    return out_


# ======================================================================== 9. 別の process
def want_names():
    return dict((k, u"jpcrp030000-asr-001_E99991-000_2026-03-31_01_2026-06-30" + X.FILE_SUFFIX_OF[k]) for k in KINDS)


class ScriptCopy(object):
    u"""``src`` を使い捨ての場所の measure/ に置き(前の便の script は symlink)、``python3 -I`` で走らせる入れ物。"""

    def __init__(self, d, src):
        mdir = os.path.join(d, "measure")
        os.makedirs(mdir)
        for fn in SIBLINGS:
            os.symlink(os.path.join(ROOT, "measure", fn), os.path.join(mdir, fn))
        for dn in ("core", "adapters"):                     # 便 XG0 の script が import だけする(呼ばない)。使い捨ての場所の根に置く
            os.symlink(os.path.join(ROOT, dn), os.path.join(d, dn))
        self.path = os.path.join(mdir, "xbrl_input_type_copy.py")
        with io.open(self.path, "w", encoding="utf-8") as fh:
            fh.write(src)

    def run(self, args, cwd):
        return spawn([sys.executable, "-I", self.path] + list(args), cwd)


def proc_problems(src=None):
    u"""本物の process(``python3 -I``)で型から作る命令・型を作る命令を走らせる。"""
    src = src if src is not None else read(SCRIPT_REL)
    out_ = []
    with Temp() as d:
        sc = ScriptCopy(d, src)
        cwd = os.path.join(d, "cwd")
        os.makedirs(cwd)
        write_file(os.path.join(cwd, "index.json"), b"{poison")
        w = os.path.join(d, "w")
        os.makedirs(w)
        zp, ent, files, tf, an = derive_doc(w)
        nfiles, nnames, ntables = MS.render_manuscript(tf)
        want_dir = os.path.join(d, "want")
        MS.P.write_folder(want_dir, nfiles, nnames, ntables)
        want = tree_of(want_dir)
        o1 = os.path.join(d, "o1")
        rc, err = sc.run(["make", tf, o1], cwd)
        if rc != 0 or not os.path.isdir(o1) or tree_of(o1) != want:
            out_.append(u"本物の process の型から作る命令の出す folder が同じ process の字と違う: rc=%s %s" % (rc, err[-200:]))
        o2 = os.path.join(d, "o2")
        rc, err = sc.run(["make", tf, o2], cwd)
        if rc != 0 or tree_of(o2) != tree_of(o1):
            out_.append(u"型から作る命令を 2 度走らせると違う字を書く")
        for args in (["make"], ["make", tf], ["make", tf, os.path.join(d, "o3"), "x"]):
            rc, err = sc.run(args, cwd)
            if rc != 64 or os.path.exists(os.path.join(d, "o3")):
                out_.append(u"本物の process: 引数が 2 つでないとき 64 で終わらない: %d 個 → %s" % (len(args) - 1, rc))
        bad = clone_folder(tf, os.path.join(d, "bad"))
        edit_json(bad, "type.json", lambda t: t["rows"][0].__setitem__("target", u"連結"))
        rc, err = sc.run(["make", bad, os.path.join(d, "o4")], cwd)
        if rc != 2 or u"DECLINE: 型の対象が知らない値" not in err.splitlines() or os.path.exists(os.path.join(d, "o4")):
            out_.append(u"本物の process: 知らない形で 2 と理由の行を出さない: rc=%s %r" % (rc, err[-200:]))
        os.makedirs(os.path.join(d, "o5"))
        rc, err = sc.run(["make", tf, os.path.join(d, "o5")], cwd)
        if rc != 1 or u"DECLINE: " in err:
            out_.append(u"本物の process: 例外で 1 を出さない: %s" % rc)
        # 型から作る命令は型の folder のほかを読まない: 元の包みも元の .htm も無い所で同じ字になる
        iso = os.path.join(d, "iso")
        os.makedirs(iso)
        shutil.copytree(tf, os.path.join(iso, "t"))
        rc, err = sc.run(["make", os.path.join(iso, "t"), os.path.join(iso, "o")], iso)
        if rc != 0 or tree_of(os.path.join(iso, "o")) != want:
            out_.append(u"型の folder だけを置いた所で型から作る命令が同じ字を出さない: rc=%s" % rc)
        # 型を作る命令
        t9 = os.path.join(d, "t9")
        rc, err = sc.run(["derive", zp, t9], cwd)
        if rc != 0 or tree_of(t9) != tree_of(tf):
            out_.append(u"本物の process の型を作る命令の出す folder が同じ process の字と違う: rc=%s %s" % (rc, err[-200:]))
        zd = os.path.join(d, "decl.zip")
        make_doc(zd, 1, a=HTM_A_TEXT.replace(u"CurrentYearInstant", u"CurYI"))
        rc, err = sc.run(["derive", zd, os.path.join(d, "t8")], cwd)
        if rc != 2 or u"DECLINE: 書類の決めが 1 通りに決まらない" not in err.splitlines() or os.path.exists(os.path.join(d, "t8")):
            out_.append(u"本物の process: 型を作る命令が断りを 2 と理由の行で出さない: rc=%s %r" % (rc, err[-200:]))
        for args in (["derive"], ["derive", zp], ["derive", zp, os.path.join(d, "t7"), "x"]):
            rc, err = sc.run(args, cwd)
            if rc != 64 or os.path.exists(os.path.join(d, "t7")):
                out_.append(u"本物の process: derive の引数が 2 つでないとき 64 で終わらない: %d 個 → %s" % (len(args) - 1, rc))
    return out_


# ======================================================================== 10. 配線
STDLIB_OK = ("__future__", "argparse", "calendar", "collections", "csv", "datetime", "decimal", "importlib", "io", "json", "os", "re", "shutil", "sys", "tempfile", "time")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "adapters", "core", "audit_core", "zipfile", "subprocess", "xml")
#: 前の便の script の関数・定数を使う(写さない): (module の名, 名前)
CALLED = (("W", "select_docs"), ("W", "order_sha256"), ("V", "CLS_STOPPED"), ("V", "exec_cmd"), ("V", "count_one"), ("B", "load_package"), ("B", "write_package"), ("B", "facts_same"), ("B", "sounds_same"), ("B", "dev_docs"),
          ("P", "peel_tables"), ("P", "write_folder"), ("P", "exec_build"), ("P", "read_tree"), ("P", "expected_names"), ("P", "rebuilt_pack"), ("P", "load_htm_tables"), ("P", "run_process"), ("P", "decline_reason"),
          ("P", "safe_local"), ("P", "safe_rel"), ("P", "rel_of"), ("T", "csv_paths"), ("T", "command_a"), ("T", "check_tool"), ("T", "check_clean"), ("T", "secret_of"), ("T", "SEED_PREFIX"))
NOT_COPIED = ("select_docs", "order_sha256", "strip_text", "build_text", "strip_tables", "build_tables", "build_files", "rebuilt_texts", "find_files", "load_package", "write_package", "package_with", "run_package",
              "compare_into", "outputs_same", "output_same", "command_a", "command_b", "count_one", "exec_cmd", "facts_same", "sounds_same", "read_rows", "read_table_rows", "mix_tables", "num_pool", "peel_tables", "peel_folder",
              "write_folder", "render_folder", "build_main", "exec_build", "read_tree", "rebuilt_pack", "expected_names", "load_htm_tables", "run_process", "decline_reason", "safe_local", "safe_rel", "rel_of", "csv_paths", "secret_of",
              "same_process_tree", "peel_main")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
#: 別の門の規準の字(関数の名・呼び出し・説明文のどこにも使わない)
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
OTHER_NAMES = (u"_xv0_tag_wall_2026_11_21", u"_xg1_tag_wall_2026_11_21", u"_xb0_tag_wall_2026_11_21", u"_xb0_tag_narrow", u"_xb0_edinet_validate_2026_11_21", u"_xb0_inline_build_2026_11_21", u"_xt0_inline_build_2026_11_21",
               u"_xt0_taxonomy_build_2026_11_22", u"_xp0_taxonomy_build_2026_11_22")


def func_map(tree):
    return dict((n.name, n) for n in tree.body if isinstance(n, ast.FunctionDef))


def names_in(node):
    return set(n.id for n in ast.walk(node) if isinstance(n, ast.Name))


def attr_calls(node):
    return [(n.func.value.id, n.func.attr) for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)]


def name_calls(node):
    return [n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]


def is_join_folder(a0):
    return isinstance(a0, ast.Call) and isinstance(a0.func, ast.Attribute) and a0.func.attr == "join" and bool(a0.args) and isinstance(a0.args[0], ast.Name) and a0.args[0].id == "folder"


def isolation_problems(src=None):
    u"""型から作る命令の中身(``render_manuscript``・``make_main``)は folder だけを引数に取り、元の包み・zip・型を作る側の関数を読まない。``process_doc`` は型から作る命令・組む命令を別の process で呼ぶ。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    funcs = func_map(tree)
    out_ = []
    for nm, args in (("render_manuscript", ["folder"]), ("make_main", ["args"]), ("make_command", ["folder", "out"]), ("derive_main", ["args"])):
        f = funcs.get(nm)
        if f is None or [a.arg for a in f.args.args] != args or f.args.vararg or f.args.kwarg or f.args.kwonlyargs or f.args.defaults:
            out_.append(u"%s の引数が (%s) だけでない" % (nm, ", ".join(args)))
    rm = funcs.get("render_manuscript")
    if rm is not None:
        bad = sorted(names_in(rm) & set(("entries", "zip_path", "zipfile", "load_package", "peel_tables", "derive_folder", "analyze", "write_type_folder", "process_doc", "orig_zip", "open", "SCRIPT_PATH", "exec_make", "exec_build",
                                         "run_process", "target_facts", "collect_resources", "decide_document", "judge_number", "ctx_info", "carried_attrs", "code_maps", "row_to_json", "an", "files_orig", "ET")))
        if bad:
            out_.append(u"render_manuscript が元の包み・zip・型を作る側の名前を使っている: %s" % bad)
        if any(m == "B" and a in ("load_package", "strip_text", "build_files") for m, a in attr_calls(rm)) or any(m == "T" and a in ("find_files", "strip_tables") for m, a in attr_calls(rm)) or any(m == "P" and a in ("peel_tables", "peel_folder") for m, a in attr_calls(rm)):
            out_.append(u"render_manuscript が剥がす側の関数を呼んでいる")
        reads = [n for n in ast.walk(rm) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "read_bytes"]
        for c in reads:
            if not (len(c.args) == 1 and is_join_folder(c.args[0])):
                out_.append(u"render_manuscript の read_bytes が folder の中の file を読んでいない")
        if len(reads) != 7:
            out_.append(u"render_manuscript が読む file が目次・型・対応表・型の外・本文・持ち込み・タクソノミの 7 か所でない: %d" % len(reads))
    mm = funcs.get("make_main")
    if mm is not None:
        allowed = set(("len", "print", "render_manuscript"))
        extra = sorted(set(name_calls(mm)) - allowed)
        if extra or ("P", "write_folder") not in attr_calls(mm) or "render_manuscript" not in name_calls(mm):
            out_.append(u"make_main が render_manuscript・P.write_folder のほかを呼んでいる(か呼んでいない): %s" % extra)
    dm = funcs.get("derive_main")
    if dm is not None and ("derive_folder" not in name_calls(dm) or ("B", "load_package") not in attr_calls(dm)):
        out_.append(u"derive_main が derive_folder・B.load_package を呼んでいない")
    mc = funcs.get("make_command")
    if mc is not None:
        rets = [n for n in ast.walk(mc) if isinstance(n, ast.Return)]
        lst = rets[0].value if len(rets) == 1 else None
        if (not isinstance(lst, ast.List) or len(lst.elts) != 6 or [getattr(e, "id", None) for e in lst.elts[4:]] != ["folder", "out"] or getattr(lst.elts[3], "value", None) != "make" or getattr(lst.elts[1], "value", None) != "-I"
                or getattr(lst.elts[2], "id", None) != "SCRIPT_PATH"):
            out_.append(u"make_command が [python, -I, script, make, folder, folder] の 6 つでない")
    pd = funcs.get("process_doc")
    if pd is not None:
        nc = name_calls(pd)
        if "render_manuscript" in names_in(pd) or "make_main" in names_in(pd):
            out_.append(u"process_doc が型から作る命令を同じ process で呼んでいる(別の process で呼ぶのは exec_make)")
        if nc.count("exec_make") != 3 or [a for m, a in attr_calls(pd) if m == "P" and a == "exec_build"] != ["exec_build"] * 3 or nc.count("derive_folder") != 1:
            out_.append(u"process_doc が exec_make・P.exec_build を 3 か所(1 回目・2 回目・混ぜ物)・derive_folder を 1 か所で呼んでいない: %d" % nc.count("exec_make"))
        for c in [n for n in ast.walk(pd) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "exec_make"]:
            if len(c.args) != 4 or [getattr(a, "id", None) for a in c.args[2:]] != ["cwd", "proc"]:
                out_.append(u"exec_make の呼び出しが (folder, out, cwd, proc) でない")
        for c in [n for n in ast.walk(pd) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "exec_build"]:
            if len(c.args) != 4 or [getattr(a, "id", None) for a in c.args[2:]] != ["cwd", "proc"]:
                out_.append(u"P.exec_build の呼び出しが (folder, out, cwd, proc) でない")
    em = funcs.get("exec_make")
    if em is not None and "make_command" not in name_calls(em):
        out_.append(u"exec_make が make_command を呼んでいない")
    callers = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            for c in name_calls(n):
                if c in ("render_manuscript", "derive_folder", "analyze", "write_type_folder"):
                    callers.setdefault(c, set()).add(n.name)
    if callers != {"render_manuscript": set(["make_main"]), "derive_folder": set(["process_doc", "derive_main"]), "analyze": set(["derive_folder"]), "write_type_folder": set(["derive_folder"])}:
        out_.append(u"型を作る側・型から作る側の関数の呼び出し元が決めた通りでない: %s" % dict((k, sorted(v)) for k, v in callers.items()))
    if any(isinstance(n, ast.Name) and n.id in ("zipfile", "ET", "subprocess") for n in ast.walk(tree)):
        out_.append(u"script が zipfile・ElementTree・subprocess を使っている(別の process は便 XP0 の run_process だけ)")
    return out_


def import_problems(src=None):
    u"""script の import は標準ライブラリだけ(engine を読まない・subprocess を使わない)。前の便の script は P・T・B・V・W から呼び、写さない。"""
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
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
    if any(a in (("os", "environ"), ("os", "getenv"), ("os", "system"), ("os", "popen")) for a in attrs):
        out_.append(u"環境変数・shell を読んで/呼んでいる")
    for mod, fn in CALLED:
        if (mod, fn) not in attrs:
            out_.append(u"前の便の %s を %s から使っていない" % (fn, mod))
    funcs = set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in NOT_COPIED:
        if fn in funcs:
            out_.append(u"前の便の %s を script が自分で定義している(写している)" % fn)
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    if PACK_NAME not in consts:
        out_.append(u"便 XP0 の script を読む名が一意の名(%s)でない" % PACK_NAME)
    for var in ("T", "B", "V", "W"):
        if not any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var for t in n.targets) and isinstance(n.value, ast.Attribute) and isinstance(n.value.value, ast.Name) and n.value.value.id == "P" and n.value.attr == var for n in tree.body):
            out_.append(u"%s を便 XP0 の script の %s から受けていない(Stop の型・module の実体が 2 つになる)" % (var, var))
    if not any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "P" for t in n.targets) and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", None) == "_load_sibling" for n in tree.body):
        out_.append(u"P を _load_sibling で読んでいない")
    if any(n in consts for n in OTHER_NAMES):
        out_.append(u"他の便と重なる名で読んでいる")
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
MUTANTS = (
    # ---- 日・期の名
    (u"D1 月の末日の規則を外す", u"    if d.day == calendar.monthrange(d.year, d.month)[1]:\n        return datetime.date(y, d.month, calendar.monthrange(y, d.month)[1])", u"    if False:\n        return datetime.date(y, d.month, calendar.monthrange(y, d.month)[1])", ("rules",)),
    (u"D2 N が 0 を作る", u"    if n < 1 or y < 1:", u"    if n < 0 or y < 1:", ("rules",)),
    (u"D3 年が 0 になる N を断らない", u"    if n < 1 or y < 1:", u"    if n < 1 or y < 0:", ("rules",)),
    (u"D4 prior_n の下限を 2 にする", u"    if n >= 1 and years_before(base, n) == x:", u"    if n >= 2 and years_before(base, n) == x:", ("rules",)),
    (u"D5 prior_n が日を見ない", u"    if n >= 1 and years_before(base, n) == x:\n        return n", u"    if n >= 1:\n        return n", ("rules",)),
    (u"D6 parse_date が fullmatch でなく match", u"    if not isinstance(s, str) or not DATE_RE.fullmatch(s):", u"    if not isinstance(s, str) or not DATE_RE.match(s):", ("rules",)),
    (u"D7 時点が当期の終わりでなく始まりと比べる", u"        if x == end:\n            return PERIOD_CUR", u"        if x == start:\n            return PERIOD_CUR", ("rules", "analyze")),
    (u"D8 提出日を当期の終わりより先に当てる", u"        if x == end:\n            return PERIOD_CUR\n        if x == filing:\n            return PERIOD_FILING", u"        if x == filing:\n            return PERIOD_FILING\n        if x == end:\n            return PERIOD_CUR", ("rules",)),
    (u"D9 期間を終わりだけで当てる", u"        if (s, e) == (start, end):\n            return PERIOD_CUR", u"        if e == end:\n            return PERIOD_CUR", ("rules",)),
    (u"D10 N 年前の期間の始まりを見ない", u"        if n and years_before(start, n) == s:", u"        if n:", ("rules",)),
    (u"D11 時点の日が 2 つあっても当てる", u'    if kind == "instant" and len(ds) == 1:', u'    if kind == "instant":', ("rules",)),
    (u"D12 期間の日が 1 つでも当てる", u'    if kind == "duration" and len(ds) == 2:\n        s, e = ds', u'    if kind == "duration":\n        s, e = ds[0], ds[-1]', ("rules",)),
    # ---- 単位
    (u"U1 株を純数と取り違える", u'        if ms[0] == "xbrli:shares":\n            return UNIT_SHARES', u'        if ms[0] == "xbrli:pure":\n            return UNIT_SHARES', ("rules", "analyze")),
    (u"U2 割り算の分母が株でなくても通す", u'    if ms or len(d["num"]) != 1 or len(d["den"]) != 1 or d["den"][0] != "xbrli:shares":', u'    if ms or len(d["num"]) != 1 or len(d["den"]) != 1:', ("rules",)),
    (u"U3 measure が 2 つでも通す", u"        if len(ms) != 1:\n            return None", u"        if len(ms) < 1:\n            return None", ("rules",)),
    (u"U4 通貨の字に : を許す", u"""x.startswith("iso4217:") and len(x) > len("iso4217:") and ":" not in x[len("iso4217:"):] and""", u"""x.startswith("iso4217:") and len(x) > len("iso4217:") and""", ("rules",)),
    (u"U5 通貨の字が空でも通す", u"""x.startswith("iso4217:") and len(x) > len("iso4217:") and ":" not in""", u"""x.startswith("iso4217:") and ":" not in""", ("rules",)),
    (u"U6 割り算の id の字を変える", u'uid = m.group(1) + "PerShares"', u'uid = m.group(1) + "Per"', ("rules", "render")),
    (u"U7 株の id を変える", u'        return "shares", od([("type", "unit"), ("id", "shares"),', u'        return "share", od([("type", "unit"), ("id", "share"),', ("rules", "render")),
    (u"U8 単位の字の区切りを変える", u'        return u",".join(d["num"]) + u"/" + u",".join(d["den"])', u'        return u",".join(d["num"]) + u"|" + u",".join(d["den"])', ("cmp",)),
    (u"U9 単位の中身が割り算を見ない", u'    return (tuple(u.get("measures") or ()), None if d is None else (tuple(d["num"]), tuple(d["den"])))', u'    return (tuple(u.get("measures") or ()), None)', ("rules",)),
    (u"U10 純数の id を変える", u'        return "pure", od([("type", "unit"), ("id", "pure"),', u'        return "puree", od([("type", "unit"), ("id", "puree"),', ("rules", "render")),
    # ---- member の字・文脈の id・定義
    (u"C1 _cor の判定を cor にする", u'    return local if prefix.endswith("_cor") else prefix + local', u'    return local if prefix.endswith("cor") else prefix + local', ("rules",)),
    (u"C2 id で個別を後ろにする", u'ind + [m for _a, m in rest])', u'[m for _a, m in rest] + ind)', ("rules", "render")),
    (u"C3 id の次元を並べ替えない", u"    rest = sorted((ax, m) for ax, m in members if ax != AXIS_CONS)", u"    rest = [(ax, m) for ax, m in members if ax != AXIS_CONS]", ("rules",)),
    (u"C4 id の Instant と Duration を取り違える", u'(u"Instant" if kind == "instant" else u"Duration")', u'(u"Duration" if kind == "instant" else u"Instant")', ("rules", "render")),
    (u"C5 定義の member を並べ替えない", u"    mem = sorted((ax, m) for ax, m in members)", u"    mem = [(ax, m) for ax, m in members]", ("rules",)),
    (u"C6 定義に scenario を常に付ける", u'("members", [list(x) for x in mem]), ("has_scenario", bool(mem))])', u'("members", [list(x) for x in mem]), ("has_scenario", True)])', ("rules", "render")),
    (u"C7 文脈の中身が member を見ない", u'tuple(sorted(tuple(m) for m in c["members"])))', u"())", ("rules",)),
    (u"C8 文脈の中身が期を見ない", u'tuple(tuple(p) for p in c["period"]), tuple(sorted', u'(), tuple(sorted', ("rules",)),
    (u"C9 文脈の中身が提出者を見ない", u'    return (c["scheme"], c["ident"], tuple(tuple(p)', u'    return (c["scheme"], tuple(tuple(p)', ("rules",)),
    # ---- 文脈の読み
    (u"X1 期の理由を (b) と書く", u'    if pname is None:\n        reasons.add("a")', u'    if pname is None:\n        reasons.add("b")', ("rules", "analyze")),
    (u"X2 提出者を識別子だけで比べる", u'    if (c["scheme"], c["ident"]) != (dec["scheme"], dec["ident"]):', u'    if c["ident"] != dec["ident"]:', ("rules",)),
    (u"X3 同じ軸が 2 回を見ない", u"    bad = len(set(axes)) != len(axes)", u"    bad = False", ("rules", "analyze")),
    (u"X4 個別の軸の別の member を見ない", u"            if m != MEMBER_IND:\n                bad = True\n            else:\n                target = TARGET_IND", u"            if False:\n                bad = True\n            else:\n                target = TARGET_IND", ("rules", "analyze")),
    (u"X5 次元を並べ替えない", u"    return reasons, kind, dates, pname, target, sorted(dims)", u"    return reasons, kind, dates, pname, target, dims", ("rules",)),
    (u"X6 forever の文脈を当てる", u'    names = [k for k, _v in per]\n    if names == ["xbrli:instant"]:', u'    names = [k for k, _v in per]\n    if names == ["xbrli:instant"] or names == ["xbrli:forever"]:', ("rules",)),
    # ---- 数の fact
    (u"N1 空の判定を反対にする", u'        if a.get("xsi:nil") != "true" or any(', u'        if a.get("xsi:nil") == "true" or any(', ("rules", "analyze")),
    (u"N2 空の fact の format を (h) に数えない", u'any(k in a for k in ("decimals", "scale", "sign", "format")):', u'any(k in a for k in ("decimals", "scale", "sign")):', ("rules",)),
    (u"N3 format を有る無いだけで見る", u'        if a.get("format") != FORMAT_OK:\n            reasons.add("e")', u'        if "format" not in a:\n            reasons.add("e")', ("rules", "analyze")),
    (u"N4 scale が無いときを 1 にする", u'shift = int_attr(a["scale"]) if "scale" in a else 0', u'shift = int_attr(a["scale"]) if "scale" in a else 1', ("rules", "analyze")),
    (u"N5 decimals か scale の片方の不正だけを (e) にする", u"        if prec is None or shift is None:\n            reasons.add(\"e\")", u"        if prec is None and shift is None:\n            reasons.add(\"e\")", ("rules", "analyze")),
    (u"N6 sign の + を通す", u'        if sign is not None and sign != "-":', u'        if sign is not None and sign not in ("-", "+"):', ("rules", "analyze")),
    (u"N7 (e) のとき字の検査をしない", u"        elif not DISPLAY_RE.fullmatch(content or \"\") or not NUMBER_RE.fullmatch((content or \"\").replace(\",\", \"\")):\n            reasons.add(\"f\")", u"        elif False:\n            reasons.add(\"f\")", ("rules",)),
    (u"N8 単位の理由を (e) と書く", u'    if form is None:\n        reasons.add("d")', u'    if form is None:\n        reasons.add("e")', ("rules", "analyze")),
    (u"N9 int_attr の境を 1000 未満にする", u"    return n if abs(n) <= MAX_EXP else None", u"    return n if abs(n) < MAX_EXP else None", ("int", "rules")),
    (u"N10 桁あふれの守りを 100000 にする", u"MAX_EXP = 1000", u"MAX_EXP = 100000", ("int", "rules")),
    (u"N11 桁区切りを取り除かない", u'    digits = content.replace(",", "")', u"    digits = content", ("int", "rules")),
    (u"N12 sign があれば - にする", u'    return (u"-" if sign == "-" else u"") + text', u'    return (u"-" if sign else u"") + text', ("int",)),
    (u"N13 値を normalize しない", u"    mag = CTX.normalize(CTX.scaleb(CTX.create_decimal(digits), shift))", u"    mag = CTX.scaleb(CTX.create_decimal(digits), shift)", ("int", "rules")),
    (u"N14 表示の位を足さない", u"    places = max(0, prec + shift)", u"    places = max(0, prec)", ("rules",)),
    (u"N15 表示の字に桁区切りを付けない", u'    return format(q, ",.%df" % places)', u'    return format(q, ".%df" % places)', ("rules", "mix")),
    (u"N16 表示の字で負の印を落とさない", u'    mag = CTX.create_decimal(value[1:] if value.startswith(u"-") else value)', u"    mag = CTX.create_decimal(value)", ("rules", "mix")),
    (u"N17 表示の位の向きを逆にする", u"    q = CTX.quantize(CTX.scaleb(mag, -shift), decimal.Decimal(1).scaleb(-places))", u"    q = CTX.quantize(CTX.scaleb(mag, shift), decimal.Decimal(1).scaleb(-places))", ("rules", "mix")),
    # ---- 解析
    (u"A1 resources の部が 2 つでも断らない", u"    if len(hosts) > 1:", u"    if len(hosts) > 2:", ("analyze",)),
    (u"A2 同じ id の違う文脈を断らない", u'                if r["id"] in ctxs and canon_ctx(ctxs[r["id"]]) != canon_ctx(r):', u'                if False:', ("analyze",)),
    (u"A3 同じ id の違う単位を断らない", u'                if r["id"] in units and canon_unit(units[r["id"]]) != canon_unit(r):', u'                if False:', ("analyze",)),
    (u"A4 当期の終わりの日が 2 つでも断らない", u"        if len(bag) != 1 or parse_date(next(iter(bag))) is None:", u"        if len(bag) < 1 or parse_date(next(iter(bag))) is None:", ("analyze",)),
    (u"A5 提出者が 2 つでも断らない", u"    if len(ents) != 1:", u"    if len(ents) < 1:", ("analyze",)),
    (u"A6 提出者を全部の頭の文脈から集める", u"                if pref == ID_END:\n                    ents.add((c[\"scheme\"], c[\"ident\"]))", u"                if True:\n                    ents.add((c[\"scheme\"], c[\"ident\"]))", ("analyze",)),
    (u"A7 隠しの fact を対象にしない", u"        if H is not None:\n            for j, h in enumerate(H[\"hidden\"]):\n                out.append(od([(\"fi\", fi), (\"where\", \"H\")", u"        if False:\n            for j, h in enumerate(H[\"hidden\"]):\n                out.append(od([(\"fi\", fi), (\"where\", \"H\")", ("analyze", "folder")),
    (u"A8 name が無い fact を断らない", u'        if "name" not in a:\n            raise Refuse(u"fact に name が無い")', u'        if False:\n            raise Refuse(u"fact に name が無い")', ("analyze",)),
    (u"A9 文脈の定義が無い fact を断らない", u'        if cref not in ctxs:\n            raise Refuse(u"文脈の定義が無い fact")', u'        if False:\n            raise Refuse(u"文脈の定義が無い fact")', ("analyze",)),
    (u"A10 鍵に対象を入れない", u'f["period"][0], f["target"], tuple(f["dims"]))', u'f["period"][0], tuple(f["dims"]))', ("analyze",)),
    (u"A11 鍵に次元を入れない", u'f["period"][0], f["target"], tuple(f["dims"]))', u'f["period"][0], f["target"])', ("analyze",)),
    (u"A12 鍵に期を入れない", u'tuple(f["period"][1]), f["period"][0], f["target"]', u'f["period"][0], f["target"]', ("analyze",)),
    (u"A13 鍵に名を入れない", u'(f["isnum"], f["attrs"]["name"], tuple(', u"(f[\"isnum\"], tuple(", ("analyze",)),
    (u"A14 食い違いの境を 2 にする", u"            if len(vals) > 1:", u"            if len(vals) > 2:", ("analyze",)),
    (u"A15 食い違いが精度を見ない", u'vals = set((x["value"], x["form"], x["shift"], x["prec"]) for x in fs)', u'vals = set((x["value"], x["form"], x["shift"]) for x in fs)', ("analyze",)),
    (u"A16 食い違いが単位を見ない", u'vals = set((x["value"], x["form"], x["shift"], x["prec"]) for x in fs)', u'vals = set((x["value"], x["shift"], x["prec"]) for x in fs)', ("analyze",)),
    (u"A17 食い違いが値を見ない", u'vals = set((x["value"], x["form"], x["shift"], x["prec"]) for x in fs)', u'vals = set((x["form"], x["shift"], x["prec"]) for x in fs)', ("analyze",)),
    (u"A18 食い違いが表示の位を見ない", u'vals = set((x["value"], x["form"], x["shift"], x["prec"]) for x in fs)', u'vals = set((x["value"], x["form"], x["prec"]) for x in fs)', ("analyze",)),
    (u"A19 まとめた fact の数を数えない", u'        rows[row_of[k]]["count"] += 1', u'        rows[row_of[k]]["count"] = 1', ("analyze",)),
    (u"A20 行の番号を並びの順にしない", u"            row_of[k] = len(rows)", u"            row_of[k] = 0", ("analyze",)),
    (u"A21 対応表の番号を逆の並びにする", u"        table = od((\"%s%04d\" % (pre, i), n) for i, n in enumerate(sorted(names[kind]), 1))", u"        table = od((\"%s%04d\" % (pre, i), n) for i, n in enumerate(sorted(names[kind], reverse=True), 1))", ("analyze",)),
    (u"A22 対応表のコードの桁を 3 にする", u'od(("%s%04d" % (pre, i), n)', u'od(("%s%03d" % (pre, i), n)', ("analyze",)),
    (u"A23 対応表の番号を 0 から振る", u"enumerate(sorted(names[kind]), 1))", u"enumerate(sorted(names[kind]), 0))", ("analyze",)),
    (u"A24 空の行にも表示の位と精度を書く", u'        if r["value"] != VALUE_NONE:\n            o["shift"], o["prec"] = r["shift"], r["prec"]', u'        if True:\n            o["shift"], o["prec"] = r["shift"], r["prec"]', ("analyze",)),
    (u"A25 文の fact の持ち込みから文の属性を外す", u"    typed = NUM_TYPED if f[\"isnum\"] else TEXT_TYPED", u"    typed = NUM_TYPED", ("analyze",)),
    (u"A26 対応表に個別の軸を入れる", u'        for ax, m in r["dims"]:\n            names[u"軸"].add(ax)', u'        for ax, m in r["dims"] + ([(AXIS_CONS, MEMBER_IND)] if r["target"] == TARGET_IND else []):\n            names[u"軸"].add(ax)', ("analyze",)),
    # ---- 型の folder
    (u"F1 持ち込みに元の属性を入れる", u'                o["row"], o["carry"] = f["row"], carried_attrs(f)\n            else:\n                o["out"] = f["out"]\n            cf.append(o)', u'                o["row"], o["carry"] = f["row"], dict(f["attrs"])\n            else:\n                o["out"] = f["out"]\n            cf.append(o)', ("folder", "render", "doc")),
    (u"F2 持ち込みの resources に文脈と単位も入れる", u'("resources", [r for r in H["resources"] if r["type"] == "ref"])])', u'("resources", list(H["resources"]))])', ("folder", "render", "doc")),
    (u"F3 型の外の文脈を書かない", u'("contexts", [c for i, c in an["ctxs"].items() if i in used_ctx]),', u'("contexts", []),', ("folder", "render")),
    (u"F4 型の外の文脈を使った順に書く", u'("contexts", [c for i, c in an["ctxs"].items() if i in used_ctx]),', u'("contexts", [an["ctxs"][i] for i in sorted(used_ctx)]),', ("folder",)),
    (u"F5 型の外の単位を書かない", u'("units", [u for i, u in an["units"].items() if i in used_unit])])))', u'("units", [])])))', ("folder", "render")),
    (u"F6 目次の htm の名に PublicDoc を付けたまま持つ", u'index["htm"].append(od([("name", P.rel_of(name)),', u'index["htm"].append(od([("name", name),', ("folder", "doc")),
    (u"F7 型の外の fact の属性を持ち込みへ回す", u'ofacts.append(od([("kind", f["kind"]), ("reasons", sorted(f["reasons"])), ("attrs", f["attrs"])]))', u'ofacts.append(od([("kind", f["kind"]), ("reasons", sorted(f["reasons"])), ("attrs", {})]))', ("folder", "render")),
    (u"F8 型の外の理由を書かない", u'("reasons", sorted(f["reasons"])), ("attrs", f["attrs"])]))', u'("reasons", []), ("attrs", f["attrs"])]))', ("folder",)),
    (u"F9 素の本文を書かない", u'        write_bytes(os.path.join(folder, P.TEXT_FMT % fi), plain.encode("utf-8"))', u'        write_bytes(os.path.join(folder, P.TEXT_FMT % fi), b"")', ("folder", "doc")),
    (u"F10 脚注の属性を持ち込まない", u'            if f is None:\n                o["attrs"] = e["attrs"]', u'            if f is None:\n                o["attrs"] = {}', ("folder", "render")),
    (u"F11 隠しの fact の持ち込みの番号を書かない", u'                if "row" in f:\n                    o["row"], o["carry"] = f["row"], carried_attrs(f)\n                else:\n                    o["out"] = f["out"]\n                hid.append(o)', u'                if "row" in f:\n                    o["row"], o["carry"] = 0, carried_attrs(f)\n                else:\n                    o["out"] = f["out"]\n                hid.append(o)', ("folder", "render")),
    # ---- 型から作る
    (u"R1 作った文脈を id の昇順に並べない", u"    ctxs = [defs[k][1] for k in sorted(defs)]", u"    ctxs = [defs[k][1] for k in defs]", ("render",)),
    (u"R2 id の重なりを断らない", u"        if cid in defs and defs[cid][0] != group:", u"        if False:", ("render",)),
    (u"R3 作った単位を id の昇順に並べない", u"    return ctxs, [units[k] for k in sorted(units)]", u"    return ctxs, [units[k] for k in units]", ("render",)),
    (u"R4 型の外の定義の中身の違いを断らない", u"            if not same:\n                raise Refuse(", u"            if False:\n                raise Refuse(", ("render",)),
    (u"R5 型の外の定義を同じ id でも足す", u"                raise Refuse(u\"型の外の定義が作った定義と同じ id で中身が違う\")\n            continue", u"                raise Refuse(u\"型の外の定義が作った定義と同じ id で中身が違う\")", ("render",)),
    (u"R6 decimals と scale を取り違える", u'a["decimals"], a["scale"], a["format"] = str(row["prec"]), str(row["shift"]), FORMAT_OK', u'a["decimals"], a["scale"], a["format"] = str(row["shift"]), str(row["prec"]), FORMAT_OK', ("render",)),
    (u"R7 負の印を付けない", u'            if row["value"].startswith(u"-"):\n                a["sign"] = "-"', u'            if False:\n                a["sign"] = "-"', ("render",)),
    (u"R8 空の fact の xsi:nil を false にする", u'            a["xsi:nil"] = "true"', u'            a["xsi:nil"] = "false"', ("render",)),
    (u"R9 持ち込みの型の属性を断らない", u"    if any(k in forbidden for k in carry):", u"    if False:", ("render",)),
    (u"R10 resources を単位が先にする", u"                    res = res + ctxs + units", u"                    res = res + units + ctxs", ("render",)),
    (u"R11 型の外の文脈を足さない", u'        ctxs = merge_outside(ctxs, outside["contexts"])', u"        ctxs = merge_outside(ctxs, [])", ("render",)),
    (u"R12 頭の部が無いのに断らない", u"        if (ctxs or units) and not host:", u"        if False:", ("render",)),
    (u"R13 持ち込みの親の番号を捨てる", u'("end", e["end"]), ("parent", e["parent"]), ("attrs", a)]))', u'("end", e["end"]), ("parent", -1), ("attrs", a)]))', ("render",)),
    (u"R14 隠しの fact の字を捨てる", u'hid.append(od([("kind", h["kind"]), ("self", h["self"]), ("attrs", a), ("text", h["text"])]))', u'hid.append(od([("kind", h["kind"]), ("self", h["self"]), ("attrs", a), ("text", u"")]))', ("render",)),
    (u"R15 文の fact の種類を断らない", u'    elif row["kind"] != KIND_TEXT:\n        raise Refuse(u"型の種類が知らない値")', u"    elif False:\n        raise Refuse(u\"型の種類が知らない値\")", ("render",)),
    (u"R16 型の対象の知らない値を断らない", u'        elif r["target"] != TARGET_DEF:\n            raise Refuse(u"型の対象が知らない値")', u'        elif False:\n            raise Refuse(u"型の対象が知らない値")', ("render", "main")),
    (u"R17 期の名が作れないのを断らない", u"        if pname is None:\n            raise Refuse(u\"期の名が作れない\")", u"        if False:\n            raise Refuse(u\"期の名が作れない\")", ("render",)),
    (u"R18 型から作る命令の断りを例外の終わりの値で返す", u"    except Refuse as exc:\n        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)\n        return EXIT_DECLINE\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef derive_main(args):", u"    except Refuse as exc:\n        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)\n        return EXIT_ERROR\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef derive_main(args):", ("main", "proc")),
    (u"R19 型から作る命令の引数の数を緩める", u'    if len(args) != 2:\n        print(u"使い方: make <型の folder> <原稿の folder>", file=sys.stderr)', u'    if len(args) < 2:\n        print(u"使い方: make <型の folder> <原稿の folder>", file=sys.stderr)', ("main", "proc")),
    (u"R20 型を作る命令の引数の数を緩める", u'    if len(args) != 2:\n        print(u"使い方: derive <zip> <型の folder>", file=sys.stderr)', u'    if len(args) < 2:\n        print(u"使い方: derive <zip> <型の folder>", file=sys.stderr)', ("main", "proc")),
    (u"R21 型から作る命令を -I なしで呼ぶ", u'    return [sys.executable, "-I", SCRIPT_PATH, "make", folder, out]', u'    return [sys.executable, SCRIPT_PATH, "make", folder, out]', ("seal", "isolation")),
    (u"R22 型から作る命令に元の包みを渡す", u'    return [sys.executable, "-I", SCRIPT_PATH, "make", folder, out]', u'    return [sys.executable, "-I", SCRIPT_PATH, "make", folder, out, "orig.zip"]', ("seal", "isolation")),
    (u"R23 断りの理由の行を読まない", u"        reason = P.decline_reason(err)\n        return False, (reason if reason is not None else u\"型から作る命令が 0 でない終わりの値で終わった\"), secs", u"        return False, u\"型から作る命令が 0 でない終わりの値で終わった\", secs", ("docdecl",)),
    (u"R24 時間の上限を見ない", u"    if timed_out:\n        return False, u\"型から作る命令が時間の上限を超えた\", secs", u"    if False:\n        return False, u\"型から作る命令が時間の上限を超えた\", secs", ("docdecl",)),
    (u"R25 0 でない終わりの値の一部を成功にする", u"    if rc != 0:\n        reason = P.decline_reason(err)", u"    if rc == 1:\n        reason = P.decline_reason(err)", ("docdecl",)),
    # ---- 比べる
    (u"K1 文脈を定義の中身でなく字で比べる", u"        if ca is None or cb is None or canon_ctx(ca) != canon_ctx(cb):", u'        if ca is None or cb is None or a.get("contextRef") != b.get("contextRef"):', ("cmp",)),
    (u"K2 単位を定義の中身でなく字で比べる", u"    return canon_unit(ua) == canon_unit(ub)", u"    return a_ref == b_ref", ("cmp",)),
    (u"K3 文脈の名の一致を数えない", u'        if a.get("contextRef") != b.get("contextRef"):\n            names_same = False', u"        if False:\n            names_same = False", ("cmp",)),
    (u"K4 contextRef と unitRef の字も属性として比べる", u'            if k not in ("contextRef", "unitRef") and ((k in a) != (k in b) or a.get(k) != b.get(k)):', u"            if ((k in a) != (k in b) or a.get(k) != b.get(k)):", ("cmp",)),
    (u"K5 違った fact が 1 つまでなら同じとする", u"    return diff_facts == 0, names_same, diff_facts, od(sorted(per.items()))", u"    return diff_facts <= 1, names_same, diff_facts, od(sorted(per.items()))", ("cmp",)),
    (u"K6 属性ごとの数を 1 つだけ数える", u"            per.update(bad)", u"            per.update(sorted(bad)[:1])", ("cmp",)),
    (u"K7 fact の数が違うのを見ない", u"    if len(oa) != len(na):\n        return False, False,", u"    if False:\n        return False, False,", ("cmp",)),
    (u"K8 正規化で contextRef の列を除かない", u"        out.append(tuple(x for i, x in enumerate(r) if i != ci))", u"        out.append(tuple(x for i, x in enumerate(r)))", ("cmp",)),
    (u"K9 正規化で単位を置き換えない", u"        r[ui] = unit_map.get(r[ui], r[ui]) if r[ui] else r[ui]", u"        pass", ("cmp",)),
    (u"K10 正規化の後で並べ替えない", u"    return sorted(out)\n\n\ndef unit_map_of(files):", u"    return out\n\n\ndef unit_map_of(files):", ("cmp",)),
    (u"K11 見出しを行に数える", u"    return rows[0], rows[1:]", u"    return rows[0], rows", ("cmp",)),
    (u"K12 見出しが読めなくても正規化する", u'    if u"contextRef" not in names or u"unitRef" not in names:\n        return None', u'    if False:\n        return None', ("cmp",)),
    (u"K13 比べ方 2 の単位の写しを元の側の表で作る", u"        nm = normalize_rows(nh, nrows, unit_map_of(new_files))", u"        nm = normalize_rows(nh, nrows, unit_map_of(files))", ("doc",)),
    # ---- 混ぜ物・表示の字
    (u"X7 混ぜ物が双子を見ない", u"            if (r[\"kind\"], r[\"code\"], tuple(r[\"period\"]), r[\"pkind\"], TARGET_IND, ()) not in keys:", u"            if True:", ("mix",)),
    (u"X8 混ぜ物が空の行も当てる", u'        if r["kind"] == KIND_NUM and r["target"] == TARGET_DEF and not r["dims"] and r["value"] != VALUE_NONE:', u'        if r["kind"] == KIND_NUM and r["target"] == TARGET_DEF and not r["dims"]:', ("mix",)),
    (u"X9 混ぜ物が次元の在る行も当てる", u'        if r["kind"] == KIND_NUM and r["target"] == TARGET_DEF and not r["dims"] and r["value"] != VALUE_NONE:', u'        if r["kind"] == KIND_NUM and r["target"] == TARGET_DEF and r["value"] != VALUE_NONE:', ("mix",)),
    (u"X10 混ぜ物が個別の行を当てる", u'        if r["kind"] == KIND_NUM and r["target"] == TARGET_DEF and not r["dims"] and r["value"] != VALUE_NONE:', u'        if r["kind"] == KIND_NUM and not r["dims"] and r["value"] != VALUE_NONE:', ("mix",)),
    (u"X11 混ぜ物が文の行も当てる", u'        if r["kind"] == KIND_NUM and r["target"] == TARGET_DEF and not r["dims"] and r["value"] != VALUE_NONE:', u'        if r["target"] == TARGET_DEF and not r["dims"] and r["value"] != VALUE_NONE:', ("mix",)),
    (u"X12 混ぜ物の双子の鍵が科目を見ない", u'    keys = set((r["kind"], r["code"], tuple(r["period"]), r["pkind"], r["target"], tuple(tuple(d) for d in r["dims"])) for r in rows)', u'    keys = set((r["kind"], 0, tuple(r["period"]), r["pkind"], r["target"], tuple(tuple(d) for d in r["dims"])) for r in rows)', ("mix",)),
    (u"X13 混ぜ物が対象を変えない", u'    typ["rows"][i]["target"] = TARGET_IND', u'    typ["rows"][i]["target"] = TARGET_DEF', ("mix", "doc")),
    (u"X14 混ぜ物が当て先の fact の数を表 F だけで数える", u'        n += sum(1 for e in carry["F"] if e.get("row") == i)\n        if carry["H"] is not None:\n            n += sum(1 for h in carry["H"]["hidden"] if h.get("row") == i)', u'        n += sum(1 for e in carry["F"] if e.get("row") == i)', ("mix",)),
    (u"X15 混ぜ物が当て先の fact の数を隠しだけで数える", u'        n += sum(1 for e in carry["F"] if e.get("row") == i)\n        if carry["H"] is not None:', u'        if carry["H"] is not None:', ("mix", "doc")),
    (u"X16 効きの判定が数を見ない", u"    if len(removed) != count or len(added) != count or count < 1:", u"    if len(removed) != len(added) or count < 1:", ("mix",)),
    (u"X17 効きの判定が増えた列を見ない", u"        if tuple(a[-2:]) != extra:", u"        if False:", ("mix",)),
    (u"X18 効きの判定が元の行との対応を見ない", u"        if rem[key] < 1:\n            return False", u"        if False:\n            return False", ("mix",)),
    (u"X19 表示の字の検査が合ったと数える", u'                    ok += 1 if display_text(r["value"], r["shift"], r["prec"]) == plain[e["start"]:e["end"]] else 0', u"                    ok += 1", ("mix",)),
    (u"X20 表示の字の検査が隠しの fact を見ない", u'        if carry["H"] is not None:\n            for h in carry["H"]["hidden"]:\n                if "row" in h:\n                    r = rows[h["row"]]', u'        if False:\n            for h in carry["H"]["hidden"]:\n                if "row" in h:\n                    r = rows[h["row"]]', ("mix",)),
    (u"X21 表示の字の検査が空の fact を掛ける", u'                if r["kind"] == KIND_NUM and r["value"] != VALUE_NONE:\n                    tried += 1\n                    ok += 1 if display_text(r["value"], r["shift"], r["prec"]) == plain', u'                if r["kind"] == KIND_NUM:\n                    tried += 1\n                    ok += 1 if display_text(r["value"], r["shift"], r["prec"]) == plain', ("mix",)),
    # ---- 書類 1 本
    (u"P1 型の数を数えない", u"        fill_type_stats(rec, an)\n        fill_footnotes(rec, files)", u"        fill_footnotes(rec, files)", ("doc",)),
    (u"P2 脚注を数えない", u"        fill_type_stats(rec, an)\n        fill_footnotes(rec, files)", u"        fill_type_stats(rec, an)", ("doc",)),
    (u"P3 持ち込みの検査を外す", u"        if carry_forbidden(tf):\n            raise Stop(", u"        if False:\n            raise Stop(", ("docdecl",)),
    (u"P4 型から作る命令を 2 回目に掛けない", u"        out2 = os.path.join(d, \"man2\")\n        ok2, _r2, _s2 = exec_make(tf, out2, cwd, proc)", u"        out2 = out1\n        ok2 = True", ("doc", "docdecl")),
    (u"P5 2 回が同じの判定で組んだ包みを見ない", u'rec[u"比べ方 2"][u"2 回が同じ"] = bool(tree_same and okb2 and P.read_tree(b2) == tree)', u'rec[u"比べ方 2"][u"2 回が同じ"] = bool(tree_same and okb2)', ("docdecl",)),
    (u"P6 2 回が同じの判定で原稿を見ない", u'rec[u"比べ方 2"][u"2 回が同じ"] = bool(tree_same and okb2 and P.read_tree(b2) == tree)', u'rec[u"比べ方 2"][u"2 回が同じ"] = bool(okb2 and P.read_tree(b2) == tree)', ("docdecl",)),
    (u"P7 組む命令の断りの段を型から作るにする", u"            return decline(rec, STAGES[2], reason)", u"            return decline(rec, STAGES[1], reason)", ("docdecl",)),
    (u"P8 道具の止まりを見ない", u"        if new[u\"類\"] == V.CLS_STOPPED and orig[u\"類\"] != V.CLS_STOPPED:", u"        if False:", ("docdecl",)),
    (u"P9 元も止まったときも断る", u"        if new[u\"類\"] == V.CLS_STOPPED and orig[u\"類\"] != V.CLS_STOPPED:", u"        if new[u\"類\"] == V.CLS_STOPPED:", ("docdecl",)),
    (u"P10 出す folder の名を目次と照らさない", u"        if set(tree) != P.expected_names(jload(read_bytes(os.path.join(out1, P.INDEX_FILE)))):", u"        if False:", ("docdecl",)),
    (u"P11 混ぜ物の当て先の fact の数を行の番号にする", u"                        rec[u\"混ぜ物\"][u\"効いた\"] = mix_effect(nm, mm, mixed[1])", u"                        rec[u\"混ぜ物\"][u\"効いた\"] = mix_effect(nm, mm, mixed[0])", ("doc",)),
    (u"P12 混ぜ物の出す folder の名を照らさない", u"                    if set(mtree) == P.expected_names(jload(read_bytes(os.path.join(mo, P.INDEX_FILE)))):", u"                    if True:", ("docdecl",)),
    (u"P13 --keep の folder を残さない", u"        if keep:\n            shutil.copytree(tf, os.path.join(keep, \"type\"))\n            shutil.copytree(out1, os.path.join(keep, \"manuscript\"))", u"        if False:\n            shutil.copytree(tf, os.path.join(keep, \"type\"))\n            shutil.copytree(out1, os.path.join(keep, \"manuscript\"))", ("doc", "run")),
    (u"P14 比べ方 1 を作った側の定義でなく元の側で数える", u'        rec[u"比べ方 1"] = od([(u"属性が意味として同じ", bool(a1)), (u"文脈の名も同じ", bool(names_same)),', u'        rec[u"比べ方 1"] = od([(u"属性が意味として同じ", True), (u"文脈の名も同じ", bool(names_same)),', ("doc",)),
    (u"P15 文脈の名も同じを属性の一致に縛る", u'(u"文脈の名も同じ", bool(names_same))', u'(u"文脈の名も同じ", bool(names_same and a1))', ("doc",)),
    (u"P16 作らなかった文脈を id で数える", u'    rec[u"文脈の定義"][u"作らなかった"] = len([c for c in oc.values() if canon_ctx(c) not in new_ctx])', u'    rec[u"文脈の定義"][u"作らなかった"] = len([i for i in oc if i not in nc])', ("doc",)),
    (u"P17 作らなかった単位を数えない", u'    rec[u"単位の定義"][u"作らなかった"] = len([u for u in ou.values() if canon_unit(u) not in new_unit])', u'    rec[u"単位の定義"][u"作らなかった"] = 0', ("totals", "doc", "decl_doc")) if False else (u"P17 作った文脈を型の外も含めて数える", u'    rec[u"文脈の定義"][u"作った"], rec[u"単位の定義"][u"作った"] = len(cids), len(uids)', u'    rec[u"文脈の定義"][u"作った"], rec[u"単位の定義"][u"作った"] = len(nc), len(uids)', ("doc",)),
    (u"P18 対応表の _cor で終わらない名を数えない", u'        rec[u"対応表の行"][u"_cor で終わらない名"] += sum(1 for n in maps[kind].values() if not (n.split(":", 1)[0] if ":" in n else "").endswith("_cor"))', u'        rec[u"対応表の行"][u"_cor で終わらない名"] += 0', ("doc",)),
    (u"P19 型に入った fact の持ち込みを文だけ数える", u'            if c:\n                rec[u"持ち込みの属性を持つ fact"][k] += 1', u'            if c and not f["isnum"]:\n                rec[u"持ち込みの属性を持つ fact"][k] += 1', ("doc",)),
    (u"P20 型の外の理由を重ねずに 1 つだけ数える", u"            for r in f[\"reasons\"]:\n                rec[u\"型の外の fact\"][u\"理由ごと\"][r][k] += 1", u"            for r in sorted(f[\"reasons\"])[:1]:\n                rec[u\"型の外の fact\"][u\"理由ごと\"][r][k] += 1", ("doc",)),
    (u"P21 2 つ以上まとめた行を 3 つ以上で数える", u'        rec[u"型の行"][u"2 つ以上の fact をまとめた行"] += 1 if r["count"] >= 2 else 0', u'        rec[u"型の行"][u"2 つ以上の fact をまとめた行"] += 1 if r["count"] >= 3 else 0', ("doc",)),
    (u"P22 -0 の行を数えない", u'        rec[u"型の行"][u"値が -0 の行"] += 1 if r["value"] == u"-0" else 0', u'        rec[u"型の行"][u"値が -0 の行"] += 0', ("doc",)),
    (u"P23 隠しの fact を数えない", u'        if f["where"] == "H":\n            rec[u"対象の fact"][u"隠し"] += 1', u'        if False:\n            rec[u"対象の fact"][u"隠し"] += 1', ("doc",)),
    # ---- 数え方・記録
    (u"T1 開発の本数の分け方を 1 つずらす", u"    dev, prod = per_doc[:dev_count], per_doc[dev_count:]", u"    dev, prod = per_doc[:dev_count + 1], per_doc[dev_count + 1:]", ("totals", "run")),
    (u"T2 型の外が 0 の書類に断った書類も数える", u"    zero_out = sum(1 for e in entries if not e[u\"断った\"] and", u"    zero_out = sum(1 for e in entries if", ("totals",)),
    (u"T3 秒の合計に None を 1 と数える", u'    out[u"型から作る命令の秒の合計"] = round(sum(e[u"秒"][u"型から作る命令"] or 0 for e in entries), 1)', u'    out[u"型から作る命令の秒の合計"] = round(sum(e[u"秒"][u"型から作る命令"] or 1 for e in entries), 1)', ("totals",)),
    (u"T4 XM0-3 の分母が数だけ", u'(u"分母(対象の fact)", tgt[KIND_NUM] + tgt[KIND_TEXT])', u'(u"分母(対象の fact)", tgt[KIND_NUM])', ("totals",)),
    (u"T5 XM0-9 の分子が文の行", u'(u"行", z[u"型の行"][KIND_NUM])', u'(u"行", z[u"型の行"][KIND_TEXT])', ("totals",)),
    (u"T6 XM0-8 の効いたが作れた", u'(u"効いた", mix[u"効いた"]), (u"作れた", mix[u"作れた"])', u'(u"効いた", mix[u"作れた"]), (u"作れた", mix[u"作れた"])', ("totals",)),
    (u"T7 XM0-1 の分母が断らなかった書類", u'(u"書類", z[u"比べ方 2"][u"fact が意味として同じ"]), (u"分母", prod[u"書類"])', u'(u"書類", z[u"比べ方 2"][u"fact が意味として同じ"]), (u"分母", prod[u"書類"] - prod[u"断った書類"])', ("totals",)),
    (u"T8 XM0-4 の理由を数だけ数える", u'z[u"型の外の fact"][u"理由ごと"][r][KIND_NUM] + z[u"型の外の fact"][u"理由ごと"][r][KIND_TEXT]) for r in REASONS)', u'z[u"型の外の fact"][u"理由ごと"][r][KIND_NUM]) for r in REASONS)', ("totals",)),
    (u"T9 断った理由の並びを段の順にしない", u"stage = od((s, od(sorted((r, n) for (st, r), n in reasons.items() if st == s))) for s in STAGES)", u"stage = od((s, od(sorted((r, n) for (st, r), n in reasons.items()))) for s in STAGES)", ("totals",)),
    (u"T10 sum_nested が bool を数えない", u"            elif any(isinstance(v, (bool, int)) for v in vals):\n                out[k] = sum(int(v) for v in vals if isinstance(v, (bool, int)))", u"            elif any(isinstance(v, int) and not isinstance(v, bool) for v in vals):\n                out[k] = sum(int(v) for v in vals if isinstance(v, int) and not isinstance(v, bool))", ("totals",)),
    (u"T11 verify が断った書類の形を見ない", u'        if d[u"断った"] != bool(d[u"断った段"]) or d[u"断った"] != bool(d[u"断った理由"]) or (d[u"断った"] and d[u"断った段"] not in STAGES):', u"        if False:", ("verify",)),
    (u"T12 verify が段の名を見ない", u'or (d[u"断った"] and d[u"断った段"] not in STAGES):', u":", ("verify",)) if False else (u"T12 verify が段の名を見ない", u' or (d[u"断った"] and d[u"断った段"] not in STAGES):', u":", ("verify",)),
    (u"T13 verify が型の外と型に入ったの合計を見ない", u"            if o[k] + t[k] != d[u\"対象の fact\"][k]:", u"            if False:", ("verify",)),
    (u"T14 verify が理由の数を見ない", u'            if max(d[u"型の外の fact"][u"理由ごと"][r][k] for r in REASONS) > o[k]:', u"            if False:", ("verify",)),
    (u"T15 verify が混ぜ物の形を見ない", u'        if d[u"混ぜ物"][u"効いた"] and not d[u"混ぜ物"][u"作れた"]:', u"        if False:", ("verify",)),
    (u"T16 verify が表示の字の数を見ない", u'        if d[u"表示の字の検査"][u"合った fact"] > d[u"表示の字の検査"][u"掛けた fact"]:', u"        if False:", ("verify",)),
    (u"T17 verify が断った書類の結果を見ない", u'        if d[u"断った"] and (d[u"比べ方 2"][u"fact が意味として同じ"] or d[u"混ぜ物"][u"効いた"]):', u"        if False:", ("verify",)),
    (u"T18 verify が欄の並びを見ない", u'        if d.get(u"番号") != i or list(d)[1:] != shape:', u'        if d.get(u"番号") != i:', ("verify",)),
    (u"T19 verify が合計を照らさない", u'    if dumps(tot) != dumps(rec[u"集計"]) or dumps(judged(tot, len(docs))) != dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):', u"    if False:", ("verify",)),
    (u"T20 check_clean が何も止めない", u"    T.check_clean(rec, text, secret)", u"    pass", ("clean", "verify")),
    (u"T21 記録が既に在っても書く", u"    if os.path.exists(path):\n        raise Stop(u\"**記録が既に在る: %s。止める**\" % os.path.basename(path))", u"    if False:\n        raise Stop(u\"**記録が既に在る: %s。止める**\" % os.path.basename(path))", ("clean", "e2e")),
    (u"T22 書いた後の検査をしない", u"    try:\n        check_clean(rec, back, secret)\n    except SystemExit:\n        os.remove(path)\n        raise", u"    pass", ("clean",)),
    (u"T23 run が secret を渡さない", u"    write_record(out, rec, secret)", u"    write_record(out, rec)", ("e2e",)),
    (u"T24 開発の番号を 0 から書く", u"(u\"開発の 5 本の番号\", list(range(1, dev_count + 1)))", u"(u\"開発の 5 本の番号\", list(range(0, dev_count)))", ("run",)),
    (u"T25 secret の並びを入れ替える", u"    secret = (labels, elems, [d[0] for d in docs], ecodes, set())", u"    secret = (elems, labels, [d[0] for d in docs], ecodes, set())", ("run",)),
    (u"T26 開発の入口が 6 本掛ける", u"    docs = dev_docs(docs_dir or DOCS_DIR, DEV_COUNT)\n    check_tool(tool_p, runner)", u"    docs = dev_docs(docs_dir or DOCS_DIR, DEV_COUNT + 1)\n    check_tool(tool_p, runner)", ("devrun",)),
    (u"T27 --keep の場所が空でなくても通す", u"        if os.listdir(a.keep):\n            raise Stop(", u"        if False:\n            raise Stop(", ("main",)),
    (u"T28 --check が記録の無い所で止まらない", u"    if not os.path.isfile(p):\n        raise Stop(u\"**在る記録が無い。止める**\")", u"    if False:\n        raise Stop(u\"**在る記録が無い。止める**\")", ("main",)),
    (u"T29 --tool-p が無くても進む", u"    if not a.tool_p:\n        raise Stop(u\"**--tool-p が要る。止める**\")", u"    if False:\n        raise Stop(u\"**--tool-p が要る。止める**\")", ("main",)),
    (u"T30 書類の本数を見ない", u"    docs = W.select_docs(docs_dir or DOCS_DIR, want)\n    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)", u"    docs = W.select_docs(docs_dir or DOCS_DIR, 3)\n    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)", ("run",)),
    # ---- 封の字・配線
    (u"S1 封の commit を変える", u'SEAL_COMMIT = "34afe495"', u'SEAL_COMMIT = "34afe496"', ("seal",)),
    (u"S2 型の外の理由から (h) を外す", u'REASONS = ("a", "b", "c", "d", "e", "f", "g", "h")', u'REASONS = ("a", "b", "c", "d", "e", "f", "g")', ("seal",)),
    (u"S3 予測の境を 1 つ変える", u'("XM0-1", (58, None, False))', u'("XM0-1", (57, None, False))', ("seal",)),
    (u"S4 format の字を変える", u'FORMAT_OK = "ixt:numdotdecimal"', u'FORMAT_OK = "ixt:numcommadecimal"', ("seal",)),
    (u"S5 書類の決めの id の頭を変える", u'ID_END, ID_START, ID_FILING = "CurrentYearInstant", "CurrentYearDuration", "FilingDateInstant"', u'ID_END, ID_START, ID_FILING = "CurrentYearInstants", "CurrentYearDuration", "FilingDateInstant"', ("seal",)),
    (u"S6 型が持つ属性から sign を外す", u'NUM_TYPED = ("name", "contextRef", "unitRef", "decimals", "scale", "sign", "format", "xsi:nil")', u'NUM_TYPED = ("name", "contextRef", "unitRef", "decimals", "scale", "format", "xsi:nil")', ("seal", "analyze")),
    (u"S7 対応表のコードの頭を変える", u'CODE_PREFIX = collections.OrderedDict([(u"科目", "K"), (u"軸", "A"), (u"member", "M")])', u'CODE_PREFIX = collections.OrderedDict([(u"科目", "K"), (u"軸", "B"), (u"member", "M")])', ("seal", "analyze")),
    (u"S8 混ぜ物の名前を変える", u'MIX_KIND = u"対象を個別に変える"', u'MIX_KIND = u"対象を連結に変える"', ("seal",)),
    (u"S9 限界の字を 1 つ消す", u'    u"持ち込み(素の本文・fact の置き場・どの置き場がどの数か・文の中身・脚注・提出者別タクソノミの表)はこの便では作っていない。",\n', u"", ("seal",)),
    (u"S10 株の字を変える", u'UNIT_SHARES, UNIT_PURE = u"株", u"純数"', u'UNIT_SHARES, UNIT_PURE = u"かぶ", u"純数"', ("seal", "rules")),
    (u"S11 時間の上限を変える", u"TIMEOUT_SEC = P.TIMEOUT_SEC", u"TIMEOUT_SEC = 300", ("seal", "doc")),
    (u"S12 個別の字を変える", u'TARGET_IND, TARGET_DEF = u"個別", u"既定"', u'TARGET_IND, TARGET_DEF = u"連結", u"既定"', ("seal",)),
    (u"W1 zipfile を import する", u"import time\n", u"import time\nimport zipfile\n", ("wiring",)),
    (u"W2 subprocess を import する", u"import time\n", u"import time\nimport subprocess\n", ("wiring",)),
    (u"W3 select_docs を自分で書く", u"def check_tool(tool, runner=None,", u"def select_docs(a, b):\n    return []\n\n\ndef check_tool(tool, runner=None,", ("wiring",)),
    (u"W4 render_manuscript が file を直に開く", u"def render_manuscript(folder):\n    u\"\"\"型の folder → (表の並び [(名, 素の本文, 表 F, 表 H)], 名, 表)。型の folder の中の file のほかを読まない。知らない形・例外は ``Refuse``。\"\"\"\n    try:\n", u"def render_manuscript(folder):\n    u\"\"\"型の folder → (表の並び [(名, 素の本文, 表 F, 表 H)], 名, 表)。型の folder の中の file のほかを読まない。知らない形・例外は ``Refuse``。\"\"\"\n    open(folder)\n    try:\n", ("isolation",)),
    (u"W5 render_manuscript が元の包みを引数に取る", u"def render_manuscript(folder):", u"def render_manuscript(folder, entries=None):", ("isolation",)),
    (u"W6 process_doc が型から作る命令を同じ process で呼ぶ", u"        out1 = os.path.join(d, \"man1\")\n        ok, reason, secs = exec_make(tf, out1, cwd, proc)", u"        out1 = os.path.join(d, \"man1\")\n        make_main([tf, out1])\n        ok, reason, secs = exec_make(tf, out1 + \"x\", cwd, proc)", ("isolation",)),
    (u"W7 run_doc という名の関数を足す", u"def check_tool(tool, runner=None,", u"def run_doc(a):\n    return a\n\n\ndef check_tool(tool, runner=None,", ("wiring",)),
    (u"W8 P の名を他の便と重ねる", u'PACK_NAME = "_xm0_pack_build_2026_11_22"', u'PACK_NAME = "_xp0_taxonomy_build_2026_11_22"', ("wiring",)),
    (u"W9 T を自分で読む", u"T = P.T                                            # 便 XT0 の script", u"T = _load_sibling('_xm0_own_t', 'xbrl_taxonomy_build_2026-11-22.py')  # 便 XT0 の script", ("wiring",)),
    (u"W10 render_manuscript が型を作る側の関数を呼ぶ", u"        dec, rows = typ[\"decision\"], typ[\"rows\"]\n", u"        dec, rows = typ[\"decision\"], typ[\"rows\"]\n        analyze([])\n", ("isolation",)),
    (u"W11 型を作る側が型から作る側の関数を呼ぶ", u"    files, names, tables = P.peel_tables(entries)\n    an = analyze(files)", u"    files, names, tables = P.peel_tables(entries)\n    render_manuscript(folder)\n    an = analyze(files)", ("isolation",)),
    (u"Q1 文脈の id の member の並びを member の昇順にする", u"    rest = sorted((ax, m) for ax, m in members if ax != AXIS_CONS)", u"    rest = sorted(((ax, m) for ax, m in members if ax != AXIS_CONS), key=lambda x: x[1])", ("render",)),
    (u"Q2 文脈の id の member の並びを member の字の昇順にする", u"    rest = sorted((ax, m) for ax, m in members if ax != AXIS_CONS)", u"    rest = sorted(((ax, m) for ax, m in members if ax != AXIS_CONS), key=lambda x: member_str(x[1]))", ("render",)),
    (u"Q3 型の行に現れない単位(株・純数)も作る", u"    units = od()\n    for r in rows:\n        if r[\"kind\"] == KIND_NUM:", u"    units = od()\n    for _f in (UNIT_SHARES, UNIT_PURE):\n        uid, u = unit_from_form(_f)\n        units.setdefault(uid, u)\n    for r in rows:\n        if r[\"kind\"] == KIND_NUM:", ("render",)),
    (u"Q4 型の行に現れない純数だけ作る", u"    units = od()\n    for r in rows:\n        if r[\"kind\"] == KIND_NUM:", u"    units = od()\n    for _f in (UNIT_PURE,):\n        uid, u = unit_from_form(_f)\n        units.setdefault(uid, u)\n    for r in rows:\n        if r[\"kind\"] == KIND_NUM:", ("render",)),
    (u"Q5 作らなかった単位の定義の数を常に 0 にする", u'    rec[u"単位の定義"][u"作らなかった"] = len([u for u in ou.values() if canon_unit(u) not in new_unit])', u'    rec[u"単位の定義"][u"作らなかった"] = 0', ("doc",)),
    (u"W12 make_main が書き出しを別の関数にする", u"        P.write_folder(args[1], files, names, tables)\n    except Refuse as exc:\n        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)\n        return EXIT_DECLINE\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef derive_main(args):", u"        open(args[1], 'w')\n    except Refuse as exc:\n        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)\n        return EXIT_DECLINE\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef derive_main(args):", ("isolation",)),
)
#: 黙ることが分かっている変異(理由つき)
SILENT_BY_DESIGN = {
    u"U5 通貨の字が空でも通す": u"通貨の字が空のとき cur() は空の字を返し、その空の字は呼ぶ側の ``if c`` で偽として扱われる(長さの検査と重なる 2 つの規則。どちらかだけ外しても形は断られる)",
    u"X6 forever の文脈を当てる": u"forever の文脈を時点として読んでも日の字が空で、日の字の検査が同じ文脈を理由 (a) にする(2 つの規則が重なる)",
    u"X10 混ぜ物が個別の行を当てる": u"個別の行は、自分自身が「対象を個別に変えた鍵」になるので、双子の検査が同じ行を外す(2 つの規則が重なる)"}


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"rules": rules_problems, u"int": int_problems, u"analyze": analyze_problems, u"folder": folder_problems, u"render": render_problems, u"cmp": cmp_problems, u"mix": mix_problems,
             u"doc": doc_problems, u"docdecl": decline_doc_problems, u"totals": totals_problems, u"tools": tools_problems, u"devdocs": dev_docs_problems, u"run": run_problems, u"verify": verify_problems,
             u"clean": clean_problems, u"e2e": e2e_problems, u"devrun": devrun_problems, u"main": main_problems}
    if name in table:
        return table[name](mod)
    if name == u"wiring":
        return import_problems(src)
    if name == u"isolation":
        return isolation_problems(src)
    if name == u"proc":
        return proc_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"rules", u"int", u"analyze", u"folder", u"render", u"cmp", u"mix", u"doc", u"docdecl", u"totals", u"tools", u"devdocs", u"run", u"verify", u"clean", u"e2e", u"devrun", u"main", u"wiring", u"isolation", u"proc")


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
        for old, new in ((u"| XM0-1(主) | 道具が読む fact が意味として同じ書類は 58 本以上。", u"| XM0-1(主) | 道具が読む fact が意味として同じ書類は 57 本以上。"), (u"| XM0-2 | 型の外の fact が 0 の書類は 45 本以上。", u"| XM0-2 | 型の外の fact が 0 の書類は 44 本以上。"),
                         (u"| XM0-3 | 型の外の fact は、対象の fact の 0.5% 以下。", u"| XM0-3 | 型の外の fact は、対象の fact の 0.6% 以下。"), (u"数の型の行の数は、型に入った数の fact の数の 94% 以上 98% 未満。", u"数の型の行の数は、型に入った数の fact の数の 93% 以上 98% 未満。"),
                         (u"`python3 -I` で走らせる", u"`python3` で走らせる"), (u"(便 XG0 と同じ 67 本)", u"(便 XG0 と同じ 66 本)"), (u"`通貨:XXX÷株`", u"`通貨:XXX/株`"),
                         (u"(c) 4. の軸に上の member 以外の member が在る", u"(c) 4. の軸に上の member 以外の member が無い"), (u"`format` = `ixt:numdotdecimal`", u"`format` = `ixt:numcommadecimal`"),
                         (u"負の印つきの 0 は `-0` と書く", u"負の印つきの 0 は `0` と書く"), (u"(`K0001`・`A0001`・`M0001` の形)", u"(`K0001`・`B0001`・`M0001` の形)")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"input_type", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        pr = X.load_helpers()
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


class RulesTest(unittest.TestCase):
    def test_b_1_dates_periods_units_members_contexts_and_numbers_one_rule_at_a_time(self):
        self.assertEqual([], rules_problems())

    def test_b_2_integers_and_values(self):
        self.assertEqual([], int_problems())

    def test_b_3_the_fake_document_is_judged_fact_by_fact_as_decided_by_hand(self):
        self.assertEqual([], analyze_problems())

    def test_b_4_the_type_folder_holds_no_original_attribute_context_or_unit(self):
        self.assertEqual([], folder_problems())

    def test_b_5_the_make_command_builds_from_the_folder_and_each_type_field_changes_its_own_attribute(self):
        self.assertEqual([], render_problems())

    def test_b_6_the_fake_document_covers_every_reason_and_form(self):
        u"""作り物の書類が、型の外の理由 8 つ・重なる理由・同じ鍵のまとめ・空・-0・個別・次元・持ち込みの属性・脚注・隠しの fact・2 つの file を全部持つ(手で数えた表との照合)。"""
        got = plan_facts(derive_doc_plan())
        reasons = set(r for _w, _n, r in got)
        self.assertTrue({"a", "b", "c", "d", "e", "f", "g", "h", "ad"} <= reasons)
        self.assertEqual(len([1 for w, _n, _r in got if w == "H"]), 2)
        self.assertIn(u"<ix:footnote", HTM_A_TEXT)
        self.assertIn(u'xsi:nil="true" />', HTM_A_TEXT)
        self.assertIn(u'sign="-"', HTM_A_TEXT)


def derive_doc_plan():
    with Temp() as d:
        return derive_doc(d)[4]


class CompareTest(unittest.TestCase):
    def test_c_1_attribute_comparison_context_name_comparison_and_the_tool_row_normalisation(self):
        self.assertEqual([], cmp_problems())

    def test_c_2_the_mixture_the_display_check_and_the_effect_rule(self):
        self.assertEqual([], mix_problems())

    def test_c_3_one_document_goes_through_with_a_fake_tool_and_a_fake_process(self):
        self.assertEqual([], doc_problems())

    def test_c_4_declines_failures_and_the_mixtures_that_could_not_be_made(self):
        self.assertEqual([], decline_doc_problems())

    def test_c_5_totals_and_the_judged_numbers(self):
        self.assertEqual([], totals_problems())

    def test_c_6_the_tool_check_and_the_dev_selection(self):
        self.assertEqual([], tools_problems())
        self.assertEqual([], dev_docs_problems())

    def test_c_7_build_record_with_fake_documents_and_a_fake_tool(self):
        self.assertEqual([], run_problems())

    def test_c_8_the_record_check_catches_tampering(self):
        self.assertEqual([], verify_problems())

    def test_c_9_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_c_10_run_record_check_with_fake_tools_and_a_fake_cache(self):
        self.assertEqual([], e2e_problems())

    def test_c_11_the_dev_entry_runs_only_the_first_five_documents(self):
        self.assertEqual([], devrun_problems())

    def test_c_12_the_entry_reads_its_arguments(self):
        self.assertEqual([], main_problems())

    def test_c_13_the_real_record_when_present_is_clean_and_consistent(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録はまだ無い(本番の後で書く)")
        text = read_text(p)
        MS.verify_record(json.loads(text, object_pairs_hook=od), text)


class ProcessTest(unittest.TestCase):
    def test_e_1_the_commands_in_a_real_process(self):
        self.assertEqual([], proc_problems())


class WiringTest(unittest.TestCase):
    def test_e_2_imports_and_the_earlier_functions_are_called_not_copied(self):
        self.assertEqual([], import_problems())

    def test_e_3_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for extra in (u"\nimport socket\n", u"\nimport zipfile\n", u"\nimport subprocess\n", u"\nfrom adapters.xbrl import instance\n", u"\nX = os.system('a')\n", u"\ndef select_docs(a, b):\n    return None\n",
                      u"\ndef load_package(a):\n    return None\n", u"\ndef run_doc(a):\n    return None\n", u"\ndef strip_tables(a):\n    return None\n", u"\ndef exec_build(a):\n    return None\n"):
            self.assertNotEqual([], import_problems(base + extra), extra)
        self.assertNotEqual([], import_problems(base.replace(u"W.order_sha256(", u"order_sha256(")))
        self.assertNotEqual([], import_problems(base.replace(u"B.load_package(", u"load_package(")))
        self.assertNotEqual([], import_problems(base.replace(u"P.peel_tables(", u"peel_tables(")))

    def test_e_4_the_build_side_reads_nothing_but_the_folder(self):
        self.assertEqual([], isolation_problems())

    def test_e_5_the_isolation_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for old, new in ((u"def render_manuscript(folder):", u"def render_manuscript(folder, original=None):"), (u"def make_main(args):", u"def make_main(args, more=None):"),
                         (u'        index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))\n        typ =', u'        data = open(folder)\n        index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))\n        typ ='),
                         (u"def render_manuscript(folder):\n", u"def render_manuscript(folder):\n    entries = B.load_package(folder)\n"), (u"ok, reason, secs = exec_make(tf, out1, cwd, proc)", u"ok, reason, secs = (make_main([tf, out1]) == 0, u'', 0.0)")):
            self.assertEqual(base.count(old), 1, old)
            self.assertNotEqual([], isolation_problems(base.replace(old, new)), old)
        self.assertNotEqual([], isolation_problems(base + u"\ndef reader(p):\n    return ET.parse(p)\n"))

    def test_e_6_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_7_the_script_leaves_sys_modules_as_it_found_them_except_its_own_earlier_script_names(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_input_type_script_for_sysmodules_check")
        changed = [k for k in before if sys.modules.get(k) is not before[k]]
        self.assertEqual([], changed)
        self.assertEqual(mod.P.__name__, PACK_NAME)
        self.assertIs(mod.T, mod.P.T)
        self.assertIs(mod.B, mod.P.B)
        self.assertIs(mod.V, mod.P.V)
        self.assertIs(mod.W, mod.P.W)
        self.assertIs(mod.Stop, mod.V.Stop)
        self.assertIs(mod.Refuse, mod.P.Refuse)
        del mod

    def test_e_8_the_default_place_is_outside_the_repo_and_the_gate_never_opens_it(self):
        top = os.path.realpath(REPO)
        self.assertFalse(os.path.realpath(MS.DOCS_DIR).startswith(top + os.sep))
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record|dev_docs|dev_run)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"docs|rec_path|\*\*kw|rp|\bd\b|\btool\b|\*\*args|\*\*a2|\*\*a3", m.group(2)), m.group(0))

    def test_e_9_the_gate_calls_subprocess_only_for_git_and_for_the_commands(self):
        src = read(GATE_REL)
        calls = re.findall(r"subprocess\.(\w+)", src)
        self.assertEqual(set(calls), {"run", "PIPE"})
        runs = [m.group(1) for m in re.finditer(r"subprocess\.run\(([^)]*)\)", src)]
        for r in runs:
            self.assertTrue(r.startswith(u'["git"') or r.startswith(u"list(cmd"), r)
        self.assertGreaterEqual(sum(1 for r in runs if r.startswith(u"list(cmd")), 1)

    def test_e_10_the_script_has_no_record_and_the_gate_does_not_write_it(self):
        src = read(GATE_REL)
        self.assertNotIn(u"write_record(os.path.join(" + u"ROOT", src)
        self.assertNotIn(u"open(os.path.join(" + u"ROOT, RECORD_REL), \"w", src)


class MutantTest(unittest.TestCase):
    def test_f_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
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

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
