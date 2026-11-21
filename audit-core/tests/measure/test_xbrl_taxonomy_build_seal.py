# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TAXONOMY_BUILD_SEAL_2026-11-22.md(XT0 ― 受理済みの有報の提出者別タクソノミ(``.xsd`` と linkbase 5 つ)を、中身を読んだ表から自前の部品で組み直すと、公開の道具が読むタクソノミ・fact・検査の鳴り方は元と同じになるか)の封の門。

**この門は置き場も道具も読まない**(書類の置き場 ``~/.cache/audit-core/edinet/``・道具の venv は 1 度も開かない。道具が無い機械でも緑)。通信しない。subprocess も git のほかは呼ばない(道具の呼び出しは作り物の runner に差し替える)。
作り物の ``.xsd`` と 5 つの linkbase(``xsd:`` 接頭辞あり・なし(既定の名前空間)・BOM・prohibited・priority・preferredLabel・loc の xlink:role・roleRef・arcroleRef・重み -1・複数の拡張 link・同じ要素への複数の loc・同じ字の xlink:label を持つ複数の端)で、剥がす・組む・比べる・混ぜ物・数え方・記録の検査を本物の関数のまま通す。

**この門が縛るもの**

1. 封の字: 封の commit(dae701b0)・封の file が commit した blob と同じ・版・sha256・掛け方 A・B・規則の年・67 本・開発の 5 本・600 秒・混ぜ物 6 種類・予測の境の数・限界の字が script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 剥がす(表 S・表 K を手で決めた値と照らす。表が元の字・xlink:label の字・接頭辞・属性の並び・空白・引用符・注釈・XML 宣言を持たない)・組む(手で書いた字と一致・字の形が違う元から同じ字が出る・表から組み直した表が同じ)・知らない形は断る・混ぜ物の当て先と変え方。
4. 組む部品は表 S・表 K だけを引数に取り、元の字・包み・zip を読まない(関数の形と本体の名前を縛る)。
5. 比べ方(書き出し 7 つ・タクソノミが同じ・fact が同じ・鳴り方が同じ・全部同じ・字が同じ)・数え方(§2)・書類 1 本の通し(元の包みと組み直した包みを同じ掛け方 A・B で 1 回ずつ・.xbrl を除く・ほかの file は元のまま・混ぜ物 6 つ)を作り物の runner で通す。
6. 記録の検査と禁止のもの。script の import は標準ライブラリと importlib だけ。前の便の script は importlib で一意の名で読み、関数を呼ぶ(写さない)。
7. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。表は実行より先に書いた(予測 = 赤になるべき検査の名前)。
"""
import ast
import collections
import copy
import csv
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
import xml.etree.ElementTree as ET
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
    mod = types.ModuleType("xbrl_taxonomy_build_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_TAXONOMY_BUILD_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "dae701b0"
SCRIPT_REL = "measure/xbrl_taxonomy_build_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_taxonomy_build_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/taxonomy_build_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_taxonomy_build_script_for_seal_gate")
ORDER_FILES = (SCRIPT_REL, GATE_REL)
od = collections.OrderedDict
BUILD_NAME = "_xt0_inline_build_2026_11_21"


def load_helpers():
    u"""順の門(``order_problems``)の部品。木の中で通るときだけ読む。"""
    p = os.path.join(ROOT, "tests", "measure", "test_xbrl_p28_result.py")
    if not os.path.exists(p):
        return None
    return load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_taxonomy_build_seal")


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
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


def read_bytes_sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def read_text(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def stops(ms, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


def declines(ms, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ms.Decline:
        return True
    return False


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xt0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def norm(o):
    u"""比べるための正規化: 順序つき辞書→辞書・tuple→list(中身の並びは保つ)。"""
    if isinstance(o, dict):
        return dict((k, norm(v)) for k, v in o.items())
    if isinstance(o, (list, tuple)):
        return [norm(v) for v in o]
    return o


# ======================================================================== 作り物の ``.xsd`` と linkbase(手で書いた字)
TARGET = u"http://disclosure.edinet-fsa.go.jp/jpcrp030000/asr/001/E99991-000/2026-03-31/01/2026-06-30"
NS_IOD = u"http://disclosure.edinet-fsa.go.jp/taxonomy/common/2013-08-31/iod"
NS_XBRLI = u"http://www.xbrl.org/2003/instance"
NS_NUM = u"http://www.xbrl.org/dtr/type/numeric"
NS_JPCRP = u"http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor"
NS_JPPFS = u"http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor"
JPPFS_XSD = u"http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor_2025-11-01.xsd"
JPCRP_XSD = u"http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor_2025-11-01.xsd"
ROLE_PRE_REF = u"http://www.xbrl.org/2003/role/presentationLinkbaseRef"
ARCROLE_LB = u"http://www.w3.org/1999/xlink/properties/linkbase"
PC = u"http://www.xbrl.org/2003/arcrole/parent-child"
SUM = u"http://www.xbrl.org/2003/arcrole/summation-item"
CL = u"http://www.xbrl.org/2003/arcrole/concept-label"
DM = u"http://xbrl.org/int/dim/arcrole/domain-member"
ALL = u"http://xbrl.org/int/dim/arcrole/all"
GS = u"http://www.xbrl.org/2003/arcrole/general-special"
ROLE_A, ROLE_B, ROLE_D = u"http://x/role/a", u"http://x/role/b", u"http://x/role/d"

XSD_ALT = u"""<?xml version="1.0" encoding="utf-8"?>
<!-- Generated by a tool -->
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:nonnum="http://www.xbrl.org/dtr/type/non-numeric" xmlns:num="http://www.xbrl.org/dtr/type/numeric" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:iod="http://disclosure.edinet-fsa.go.jp/taxonomy/common/2013-08-31/iod" xmlns:jpcrp030000-asr_E99991-000="http://disclosure.edinet-fsa.go.jp/jpcrp030000/asr/001/E99991-000/2026-03-31/01/2026-06-30" targetNamespace="http://disclosure.edinet-fsa.go.jp/jpcrp030000/asr/001/E99991-000/2026-03-31/01/2026-06-30" elementFormDefault="qualified" attributeFormDefault="unqualified">
  <xsd:import namespace="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor" schemaLocation="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor_2025-11-01.xsd"/>
  <xsd:import schemaLocation="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor_2025-11-01.xsd" namespace="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor"/>
  <xsd:annotation><xsd:appinfo>
    <link:linkbaseRef xlink:arcrole='http://www.w3.org/1999/xlink/properties/linkbase' xlink:role="http://www.xbrl.org/2003/role/presentationLinkbaseRef" xlink:href="x_pre.xml" xlink:type="simple"/>
    <link:linkbaseRef xlink:type="simple" xlink:href="http://example.org/ext_gla.xml" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase"/>
  </xsd:appinfo></xsd:annotation>
  <xsd:element id="jpcrp030000-asr_E99991-000_Alpha" xbrli:periodType="duration" abstract="false" name="Alpha" nillable="true" substitutionGroup="xbrli:item" type="xbrli:monetaryItemType" xbrli:balance="debit"/>
  <xsd:element id="jpcrp030000-asr_E99991-000_BetaHeading" xbrli:periodType="instant" abstract="true" name="BetaHeading" nillable="true" substitutionGroup="iod:identifierItem" type="xbrli:stringItemType" />
  <xsd:element name="Gamma" id="jpcrp030000-asr_E99991-000_Gamma" abstract="false" xbrli:periodType="instant" type="num:percentItemType" substitutionGroup="xbrli:item"></xsd:element>
</xsd:schema>
"""
#: 既定の名前空間が XSD・接頭辞なし・BOM・宣言に encoding なし(``WizLabo`` の形)
XSD_NOPFX = u"﻿" + u"""<?xml version="1.0"?>
<schema xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:q9="http://www.xbrl.org/dtr/type/numeric" xmlns:zz="http://disclosure.edinet-fsa.go.jp/taxonomy/common/2013-08-31/iod" elementFormDefault="qualified" targetNamespace="http://disclosure.edinet-fsa.go.jp/jpcrp030000/asr/001/E99991-000/2026-03-31/01/2026-06-30" attributeFormDefault="unqualified" xmlns="http://www.w3.org/2001/XMLSchema">
<import schemaLocation="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor_2025-11-01.xsd" namespace="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor" />
<import schemaLocation="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor_2025-11-01.xsd" namespace="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor" />
<annotation>
<appinfo>
<link:linkbaseRef xlink:type="simple" xlink:href="x_pre.xml" xlink:role="http://www.xbrl.org/2003/role/presentationLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" />
<link:linkbaseRef xlink:type="simple" xlink:href="http://example.org/ext_gla.xml" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" />
</appinfo>
</annotation>
<element id="jpcrp030000-asr_E99991-000_Alpha" xbrli:balance="debit" xbrli:periodType="duration" abstract="false" name="Alpha" nillable="true" substitutionGroup="xbrli:item" type="xbrli:monetaryItemType" />
<element id="jpcrp030000-asr_E99991-000_BetaHeading" xbrli:periodType="instant" abstract="true" name="BetaHeading" nillable="true" substitutionGroup="zz:identifierItem" type="xbrli:stringItemType" />
<element id="jpcrp030000-asr_E99991-000_Gamma" xbrli:periodType="instant" abstract="false" name="Gamma" substitutionGroup="xbrli:item" type="q9:percentItemType" />
</schema>
"""
XSD_CANON = u"""<?xml version="1.0" encoding="utf-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:jpcrp030000-asr_E99991-000="http://disclosure.edinet-fsa.go.jp/jpcrp030000/asr/001/E99991-000/2026-03-31/01/2026-06-30" xmlns:iod="http://disclosure.edinet-fsa.go.jp/taxonomy/common/2013-08-31/iod" xmlns:num="http://www.xbrl.org/dtr/type/numeric" attributeFormDefault="unqualified" elementFormDefault="qualified" targetNamespace="http://disclosure.edinet-fsa.go.jp/jpcrp030000/asr/001/E99991-000/2026-03-31/01/2026-06-30">
  <xsd:import schemaLocation="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor_2025-11-01.xsd" namespace="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor" />
  <xsd:import schemaLocation="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor_2025-11-01.xsd" namespace="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/jppfs_cor" />
  <xsd:annotation>
    <xsd:appinfo>
      <link:linkbaseRef xlink:type="simple" xlink:href="x_pre.xml" xlink:role="http://www.xbrl.org/2003/role/presentationLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" />
      <link:linkbaseRef xlink:type="simple" xlink:href="http://example.org/ext_gla.xml" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" />
    </xsd:appinfo>
  </xsd:annotation>
  <xsd:element id="jpcrp030000-asr_E99991-000_Alpha" xbrli:balance="debit" xbrli:periodType="duration" abstract="false" name="Alpha" nillable="true" substitutionGroup="xbrli:item" type="xbrli:monetaryItemType" />
  <xsd:element id="jpcrp030000-asr_E99991-000_BetaHeading" xbrli:periodType="instant" abstract="true" name="BetaHeading" nillable="true" substitutionGroup="iod:identifierItem" type="xbrli:stringItemType" />
  <xsd:element id="jpcrp030000-asr_E99991-000_Gamma" xbrli:periodType="instant" abstract="false" name="Gamma" substitutionGroup="xbrli:item" type="num:percentItemType" />
</xsd:schema>
"""
#: 手で決めた表 S(``XSD_ALT``・``XSD_NOPFX`` のどちらからも同じ表が出る)
HAND_S = od([
    ("target", TARGET), ("defaults", od([("attributeFormDefault", "unqualified"), ("elementFormDefault", "qualified")])),
    ("imports", [(NS_JPCRP, JPCRP_XSD), (NS_JPPFS, JPPFS_XSD)]),
    ("refs", [od([("href", "x_pre.xml"), ("role", ROLE_PRE_REF), ("arcrole", ARCROLE_LB)]), od([("href", "http://example.org/ext_gla.xml"), ("role", None), ("arcrole", ARCROLE_LB)])]),
    ("elements", [
        {"id": "jpcrp030000-asr_E99991-000_Alpha", "{%s}periodType" % NS_XBRLI: "duration", "abstract": "false", "name": "Alpha", "nillable": "true", "substitutionGroup": (NS_XBRLI, "item"), "type": (NS_XBRLI, "monetaryItemType"), "{%s}balance" % NS_XBRLI: "debit"},
        {"id": "jpcrp030000-asr_E99991-000_BetaHeading", "{%s}periodType" % NS_XBRLI: "instant", "abstract": "true", "name": "BetaHeading", "nillable": "true", "substitutionGroup": (NS_IOD, "identifierItem"), "type": (NS_XBRLI, "stringItemType")},
        {"id": "jpcrp030000-asr_E99991-000_Gamma", "{%s}periodType" % NS_XBRLI: "instant", "abstract": "false", "name": "Gamma", "substitutionGroup": (NS_XBRLI, "item"), "type": (NS_NUM, "percentItemType")}])])


def mk_loc(href, role=None):
    return od([("kind", "loc"), ("href", href), ("role", role)])


def mk_res(text, lang="ja", role="http://www.xbrl.org/2003/role/label", id_=None):
    return od([("kind", "label"), ("lang", lang), ("role", role), ("id", id_), ("text", text)])


def mk_arc(f, t, arcrole, before, **attrs):
    return od([("from", f), ("to", t), ("before", before), ("arcrole", arcrole), ("attrs", od(sorted(attrs.items(), key=lambda kv: ARC_ORDER.index(kv[0]))))])


def mk_link(tag, role, ends, arcs):
    return od([("tag", tag), ("role", role), ("ends", ends), ("arcs", arcs)])


def mk_ref(tag, uri, href):
    return od([("tag", tag), ("uri", uri), ("href", href)])


NS_DT = u"http://xbrl.org/2005/xbrldt"
ARC_ORDER = ["order", "weight", "use", "priority", "preferredLabel", "{%s}contextElement" % NS_DT, "{%s}closed" % NS_DT, "{%s}usable" % NS_DT]
CE, CLOSED, USABLE = "{%s}contextElement" % NS_DT, "{%s}closed" % NS_DT, "{%s}usable" % NS_DT
TOTAL = u"http://www.xbrl.org/2003/role/totalLabel"
LINKROLE = u"http://www.xbrl.org/2003/role/link"
LABELROLE = u"http://www.xbrl.org/2003/role/label"
TXT1 = u" 売上 & <高>"

# ---- 表示(pre)
PRE_ALT = u"""<?xml version='1.0'?>
<!-- generated -->
<link:linkbase xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<link:roleRef xlink:href="http://x/rt.xsd#rol_a" roleURI='http://x/role/a' xlink:type='simple'/>
<link:presentationLink xlink:role="http://x/role/a" xlink:type="extended">
<!-- tree -->
<link:loc xlink:label="Alpha" xlink:href="t.xsd#a_Alpha" xlink:type="locator"/>
<link:loc xlink:type="locator" xlink:label="Beta_2" xlink:href="t.xsd#a_Beta"/>
<link:presentationArc order="1" preferredLabel="http://www.xbrl.org/2003/role/totalLabel" xlink:from="Alpha" xlink:to="Beta_2" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:type="arc"/>
<link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="Alpha_3"/>
<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="Beta_2" xlink:to="Alpha_3" order="2"/>
</link:presentationLink>
<link:presentationLink xlink:type="extended" xlink:role="http://x/role/b">
  <link:loc xlink:type="locator" xlink:href="t.xsd#a_P" xlink:label="P"/>
  <link:loc xlink:type="locator" xlink:href="t.xsd#a_Q" xlink:label="Q"/>
  <link:loc xlink:type="locator" xlink:href="t.xsd#a_Q2" xlink:label="Q"/>
  <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="P" xlink:to="Q" order="1"/>
</link:presentationLink>
</link:linkbase>
"""
PRE_CANON = u"""<?xml version="1.0" encoding="utf-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
  <link:roleRef roleURI="http://x/role/a" xlink:type="simple" xlink:href="http://x/rt.xsd#rol_a" />
  <link:presentationLink xlink:type="extended" xlink:role="http://x/role/a">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="L1" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Beta" xlink:label="L2" />
    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="L1" xlink:to="L2" order="1" preferredLabel="http://www.xbrl.org/2003/role/totalLabel" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="L3" />
    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="L2" xlink:to="L3" order="2" />
  </link:presentationLink>
  <link:presentationLink xlink:type="extended" xlink:role="http://x/role/b">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_P" xlink:label="L1" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Q" xlink:label="L2" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Q2" xlink:label="L3" />
    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="L1" xlink:to="L2" order="1" />
    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="L1" xlink:to="L3" order="1" />
  </link:presentationLink>
</link:linkbase>
"""
HAND_PRE = od([
    ("refs", [mk_ref("roleRef", ROLE_A, "http://x/rt.xsd#rol_a")]),
    ("links", [
        mk_link("presentationLink", ROLE_A, [mk_loc("t.xsd#a_Alpha"), mk_loc("t.xsd#a_Beta"), mk_loc("t.xsd#a_Alpha")],
                [mk_arc(0, 1, PC, 2, order="1", preferredLabel=TOTAL), mk_arc(1, 2, PC, 3, order="2")]),
        mk_link("presentationLink", ROLE_B, [mk_loc("t.xsd#a_P"), mk_loc("t.xsd#a_Q"), mk_loc("t.xsd#a_Q2")],
                [mk_arc(0, 1, PC, 3, order="1"), mk_arc(0, 2, PC, 3, order="1")])])])

# ---- 計算(cal)
CAL_ALT = u"""<?xml version="1.0" encoding="utf-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
  <link:roleRef xlink:type="simple" roleURI="http://x/role/a" xlink:href="http://x/rt.xsd#rol_a" />
  <link:calculationLink xlink:type="extended" xlink:role="http://x/role/a">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="A" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Beta" xlink:label="B" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Gamma" xlink:label="G" />
    <link:calculationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/summation-item" xlink:from="A" xlink:to="B" order="1" weight="1" />
    <link:calculationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/summation-item" xlink:from="A" xlink:to="G" order="2" weight="-1" />
  </link:calculationLink>
  <link:calculationLink xlink:type="extended" xlink:role="http://x/role/b">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="A" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Beta" xlink:label="B" />
    <link:calculationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/summation-item" xlink:from="A" xlink:to="B" order="1" weight="1" />
  </link:calculationLink>
</link:linkbase>
"""
CAL_CANON = u"""<?xml version="1.0" encoding="utf-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
  <link:roleRef roleURI="http://x/role/a" xlink:type="simple" xlink:href="http://x/rt.xsd#rol_a" />
  <link:calculationLink xlink:type="extended" xlink:role="http://x/role/a">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="L1" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Beta" xlink:label="L2" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Gamma" xlink:label="L3" />
    <link:calculationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/summation-item" xlink:from="L1" xlink:to="L2" order="1" weight="1" />
    <link:calculationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/summation-item" xlink:from="L1" xlink:to="L3" order="2" weight="-1" />
  </link:calculationLink>
  <link:calculationLink xlink:type="extended" xlink:role="http://x/role/b">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="L1" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Beta" xlink:label="L2" />
    <link:calculationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/summation-item" xlink:from="L1" xlink:to="L2" order="1" weight="1" />
  </link:calculationLink>
</link:linkbase>
"""
HAND_CAL = od([
    ("refs", [mk_ref("roleRef", ROLE_A, "http://x/rt.xsd#rol_a")]),
    ("links", [
        mk_link("calculationLink", ROLE_A, [mk_loc("t.xsd#a_Alpha"), mk_loc("t.xsd#a_Beta"), mk_loc("t.xsd#a_Gamma")], [mk_arc(0, 1, SUM, 3, order="1", weight="1"), mk_arc(0, 2, SUM, 3, order="2", weight="-1")]),
        mk_link("calculationLink", ROLE_B, [mk_loc("t.xsd#a_Alpha"), mk_loc("t.xsd#a_Beta")], [mk_arc(0, 1, SUM, 2, order="1", weight="1")])])])

# ---- 定義(def): arcroleRef・xbrldt の属性(接頭辞は ``dt``)・複数の arc
DEF_ALT = u"""<?xml version="1.0" encoding="utf-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dt="http://xbrl.org/2005/xbrldt">
  <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/domain-member" xlink:type="simple" xlink:href="http://x/dim.xsd#domain-member" />
  <link:definitionLink xlink:type="extended" xlink:role="http://x/role/d">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="A" />
    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="A" xlink:to="B" order="1" dt:usable="false" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Beta" xlink:label="B" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Gamma" xlink:label="G" />
    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/all" xlink:from="A" xlink:to="G" order="1" dt:contextElement="segment" dt:closed="true" />
    <link:definitionArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/general-special" xlink:from="B" xlink:to="G" order="1" />
    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="A" xlink:to="G" order="2" />
  </link:definitionLink>
</link:linkbase>
"""
DEF_CANON = u"""<?xml version="1.0" encoding="utf-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xbrldt="http://xbrl.org/2005/xbrldt">
  <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/domain-member" xlink:type="simple" xlink:href="http://x/dim.xsd#domain-member" />
  <link:definitionLink xlink:type="extended" xlink:role="http://x/role/d">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="L1" />
    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="L1" xlink:to="L2" order="1" xbrldt:usable="false" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Beta" xlink:label="L2" />
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Gamma" xlink:label="L3" />
    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/all" xlink:from="L1" xlink:to="L3" order="1" xbrldt:contextElement="segment" xbrldt:closed="true" />
    <link:definitionArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/general-special" xlink:from="L2" xlink:to="L3" order="1" />
    <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="L1" xlink:to="L3" order="2" />
  </link:definitionLink>
</link:linkbase>
"""
HAND_DEF = od([
    ("refs", [mk_ref("arcroleRef", DM, "http://x/dim.xsd#domain-member")]),
    ("links", [mk_link("definitionLink", ROLE_D, [mk_loc("t.xsd#a_Alpha"), mk_loc("t.xsd#a_Beta"), mk_loc("t.xsd#a_Gamma")],
                       [mk_arc(0, 1, DM, 1, order="1", **{USABLE: "false"}), mk_arc(0, 2, ALL, 3, order="1", **{CE: "segment", CLOSED: "true"}), mk_arc(1, 2, GS, 3, order="1"), mk_arc(0, 2, DM, 3, order="2")])])])

# ---- ラベル(lab・lab-en): loc の xlink:role・label の id・prohibited・priority・実体参照・先頭の空白
LAB_ALT = u"""<?xml version="1.0" encoding="utf-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
  <link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="Alpha" xlink:role="http://x/role/locrole" />
    <link:label xlink:type="resource" xlink:label="Alpha_lab" xml:lang="ja" xlink:role="http://www.xbrl.org/2003/role/label" id="lab_1"> 売上 &amp; &lt;高&gt;</link:label>
    <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="Alpha" xlink:to="Alpha_lab" order="1" />
    <link:label xlink:type="resource" xlink:label="Alpha_verbose" xml:lang="ja" xlink:role="http://www.xbrl.org/2003/role/verboseLabel">冗長</link:label>
    <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="Alpha" xlink:to="Alpha_verbose" use="prohibited" priority="1" order="2" />
  </link:labelLink>
</link:linkbase>
"""
LAB_CANON = u"""<?xml version="1.0" encoding="utf-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
  <link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:role="http://x/role/locrole" xlink:label="L1" />
    <link:label xlink:type="resource" xlink:label="L2" xml:lang="ja" xlink:role="http://www.xbrl.org/2003/role/label" id="lab_1"> 売上 &amp; &lt;高&gt;</link:label>
    <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="L1" xlink:to="L2" order="1" />
    <link:label xlink:type="resource" xlink:label="L3" xml:lang="ja" xlink:role="http://www.xbrl.org/2003/role/verboseLabel">冗長</link:label>
    <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="L1" xlink:to="L3" order="2" use="prohibited" priority="1" />
  </link:labelLink>
</link:linkbase>
"""
HAND_LAB = od([
    ("refs", []),
    ("links", [mk_link("labelLink", LINKROLE, [mk_loc("t.xsd#a_Alpha", role=u"http://x/role/locrole"), mk_res(TXT1, "ja", LABELROLE, "lab_1"), mk_res(u"冗長", "ja", u"http://www.xbrl.org/2003/role/verboseLabel")],
                       [mk_arc(0, 1, CL, 2, order="1"), mk_arc(0, 2, CL, 3, order="2", use="prohibited", priority="1")])])])
LABEN_ALT = u"""<?xml version="1.0" encoding="utf-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
<link:labelLink xlink:role="http://www.xbrl.org/2003/role/link" xlink:type="extended">
<link:loc xlink:href="t.xsd#a_Alpha" xlink:type="locator" xlink:label="Alpha"/>
<link:label xlink:label="Alpha_lab" xlink:type="resource" xml:lang="en" xlink:role="http://www.xbrl.org/2003/role/label">Sales</link:label>
<link:labelArc xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="Alpha" xlink:to="Alpha_lab" xlink:type="arc"/>
</link:labelLink>
</link:linkbase>
"""
LABEN_CANON = u"""<?xml version="1.0" encoding="utf-8"?>
<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
  <link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">
    <link:loc xlink:type="locator" xlink:href="t.xsd#a_Alpha" xlink:label="L1" />
    <link:label xlink:type="resource" xlink:label="L2" xml:lang="en" xlink:role="http://www.xbrl.org/2003/role/label">Sales</link:label>
    <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="L1" xlink:to="L2" />
  </link:labelLink>
</link:linkbase>
"""
HAND_LABEN = od([("refs", []), ("links", [mk_link("labelLink", LINKROLE, [mk_loc("t.xsd#a_Alpha"), mk_res(u"Sales", "en", LABELROLE)], [mk_arc(0, 1, CL, 2)])])])

ALT_TEXTS = od([("xsd", XSD_ALT), ("cal", CAL_ALT), ("def", DEF_ALT), ("lab", LAB_ALT), ("lab-en", LABEN_ALT), ("pre", PRE_ALT)])
CANON_TEXTS = od([("xsd", XSD_CANON), ("cal", CAL_CANON), ("def", DEF_CANON), ("lab", LAB_CANON), ("lab-en", LABEN_CANON), ("pre", PRE_CANON)])
HAND_TABLES = od([("xsd", HAND_S), ("cal", HAND_CAL), ("def", HAND_DEF), ("lab", HAND_LAB), ("lab-en", HAND_LABEN), ("pre", HAND_PRE)])
KINDS = ("xsd", "cal", "def", "lab", "lab-en", "pre")


def b(s):
    return s.encode("utf-8")


def alt_bytes():
    return od((k, b(v)) for k, v in ALT_TEXTS.items())


def fresh_hand():
    return copy.deepcopy(HAND_TABLES)


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XT0-1", (54, None)), ("XT0-2", (None, 5)), ("XT0-3", (54, None)), ("XT0-4", (None, 93)), ("XT0-5", (28, None)), ("XT0-6", (u"作れた数", None)), ("XT0-7", (5, 15))])
SEAL_BOUND_TEXT = od([("XT0-1", u"全部同じ書類は 54 本以上"), ("XT0-2", u"断った書類は 5 本以下"), ("XT0-3", u"鳴り方が同じ書類は 54 本以上"), ("XT0-4", u"372 のうち 93 以下"),
                      ("XT0-5", u"作れたのは 28 個以上"), ("XT0-6", u"作れた混ぜ物の全部で、違いを見つける"), ("XT0-7", u"5 個以上 15 個以下")])
SEAL_SHA_P = u"fd9b0d08bf283452fe4ebd6ec9de2f273010de0420b70e61c993a6c033814635"
SEAL_MIX = (u"M1 表示の arc を抜く", u"M2 計算の向きを返す", u"M3 日本語のラベルを変える", u"M4 英語のラベルを変える", u"M5 期の型を返す", u"M6 定義の arc を抜く")


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out_ = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out_.append(u"script の封の commit・path・記録の path が門と違う")
    if ms.TOOL_VERSION != u"2.47.5" or u"`arelle-release` の版 `2.47.5`" not in seal:
        out_.append(u"版の字が封と違う")
    if ms.SHA_P != SEAL_SHA_P or (u"`%s`" % SEAL_SHA_P) not in seal:
        out_.append(u"ModelValue.py の sha256 が封と違う")
    if ms.PLUGINS != u"validate/EDINET|inlineXbrlDocumentSet" or u"--plugins 'validate/EDINET|inlineXbrlDocumentSet'" not in seal:
        out_.append(u"掛け方の plugins が封と違う")
    if ms.YEAR != u"EDINET-2026" or u"--disclosureSystem EDINET-2026" not in seal:
        out_.append(u"規則の年が封と違う")
    if ms.FACT_COLS != u"Name contextRef unitRef Dec Value EntityScheme EntityIdentifier Period Dimensions" or (u"--factListCols '%s'" % ms.FACT_COLS) not in seal:
        out_.append(u"--factListCols が封と違う")
    if ms.CONCEPT_LABEL_ARCROLE != u"http://www.xbrl.org/2003/arcrole/concept-label" or u"--viewArcrole http://www.xbrl.org/2003/arcrole/concept-label" not in seal:
        out_.append(u"掛け方 A の viewArcrole が封と違う")
    if ms.GENERAL_SPECIAL_ARCROLE != u"http://www.xbrl.org/2003/arcrole/general-special" or u"--viewArcrole http://www.xbrl.org/2003/arcrole/general-special" not in seal:
        out_.append(u"掛け方 B の viewArcrole が封と違う")
    if u"--relationshipCols Name" not in seal or u"**掛け方 A**" not in seal or u"**掛け方 B**" not in seal:
        out_.append(u"掛け方 A・B の字が封と違う")
    if ms.TIMEOUT_SEC != 600 or u"1 回の時間の上限は 600 秒" not in seal:
        out_.append(u"時間の上限が封と違う")
    if ms.DOCS_WANT != 67 or u"便 XG0 と同じ 67 本" not in seal or u"書類は 67 本(違えば script は止まる)" not in seal:
        out_.append(u"67 が封と違う")
    if ms.DEV_COUNT != 5 or u"並びの頭の 5 本" not in seal:
        out_.append(u"開発の 5 本が封と違う")
    if tuple(ms.OUTPUT_KEYS) != (u"概念", u"役割型", u"表示", u"計算", u"次元", u"ラベルの関係", u"一般特殊") or u"**書き出し 7 つ**" not in seal:
        out_.append(u"書き出し 7 つが封と違う")
    if tuple(ms.NEED_ROWS) != (u"概念", u"役割型", u"表示", u"ラベルの関係") or u"concepts・roleTypes・pre・ラベルの関係は、どちらかの行が 1 以下なら同じとしない" not in seal or u"cal・dim・general-special" not in seal:
        out_.append(u"行が 1 以下なら同じとしない書き出しが封と違う")
    if tuple(ms.FILE_KINDS) != ("xsd", "cal", "def", "lab", "lab-en", "pre") or dict(ms.FILE_SUFFIX) != {"xsd": ".xsd", "cal": "_cal.xml", "def": "_def.xml", "lab": "_lab.xml", "lab-en": "_lab-en.xml", "pre": "_pre.xml"} or u"字が同じ**: 組んだ file の bytes が元の file の bytes と同じ(6 種類を分けて数える)" not in seal:
        out_.append(u"file の 6 種類が封と違う")
    if tuple(ms.MIX_KINDS) != (u"表示の arc を抜く", u"計算の向きを返す", u"日本語のラベルを変える", u"英語のラベルを変える", u"期の型を返す", u"定義の arc を抜く") or tuple(ms.MIX_IDS) != ("M1", "M2", "M3", "M4", "M5", "M6"):
        out_.append(u"混ぜ物の種類が script で封と違う")
    for m in SEAL_MIX:
        if (u"**%s**" % m) not in seal:
            out_.append(u"封に混ぜ物の字が無い: %s" % m)
    if u"開発の 5 本 × 6 種類 = 30 個" not in seal:
        out_.append(u"混ぜ物の数が封と違う")
    if ms.DOMAIN_MEMBER_ARCROLE != u"http://xbrl.org/int/dim/arcrole/domain-member" or u"arcrole が `domain-member`" not in seal:
        out_.append(u"M6 の arcrole が封と違う")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out_.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [x for x in seal.splitlines() if x.startswith(u"| %s" % k)]
        if len(row_) != 1 or t not in row_[0]:
            out_.append(u"封の予測の行の字が違う: %s" % k)
    if u"372" not in seal or u"62 × 6" not in seal:
        out_.append(u"file の分母が封と違う")
    for rel in (SCRIPT_REL, RECORD_REL, u"tests/measure/test_xbrl_taxonomy_build_seal.py"):
        if rel not in seal:
            out_.append(u"封に path が無い: %s" % rel)
    if u"docID・会社の名・EDINET コード・file の名・fact の値・要素の名・ラベルの字・role の URI・指摘の行の本文は書かない" not in seal:
        out_.append(u"封の記録の禁止の字が違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    want_phrases = (u"タクソノミの中身を決める力は測っていない", u"マニフェスト・画像・AuditDoc は元のまま", u"道具 P。司令塔が 1 行を直したもの", u"道具が読み捨てる属性", u"EDINET の本物の検査とは照らしていない", u"無作為ではない。有報だけ", u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」")
    got_phrases = (u"タクソノミの中身", u"元のまま", u"1 行を直したもの", u"道具が読み捨てる属性", u"EDINET の本物の検査とは照らしていない", u"無作為ではない。有報だけ", u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」")
    if any(p not in sec7 for p in want_phrases) or any(k not in u"".join(ms.LIMITS) for k in got_phrases):
        out_.append(u"限界の字が封 §7 と違う")
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
    pr = load_helpers()
    others = list(ORDER_FILES) if others is None else others
    return list(pr.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % x for x in rc.stdout.splitlines() if x.strip()]


# ======================================================================== 2. 剥がす
def strip_problems(ms=None):
    ms = ms or MS
    out_ = []
    for what, data in ((u"xsd: 接頭辞つき", b(XSD_ALT)), (u"xsd: 既定の名前空間・BOM・encoding なし・別の接頭辞", b(XSD_NOPFX)), (u"xsd: 組む部品の字", b(XSD_CANON))):
        S = ms.strip_xsd(data)
        if norm(S) != norm(HAND_S):
            out_.append(u"表 S が手で決めた値と違う(%s): %s" % (what, json.dumps(norm(S), ensure_ascii=False)[:200]))
        if list(S) != ["target", "defaults", "imports", "refs", "elements"]:
            out_.append(u"表 S の鍵が違う: %s" % list(S))
    for k in KINDS[1:]:
        for what, text in ((u"元の字", ALT_TEXTS[k]), (u"組む部品の字", CANON_TEXTS[k])):
            K = ms.strip_linkbase(b(text))
            if norm(K) != norm(HAND_TABLES[k]):
                out_.append(u"表 K(%s)が手で決めた値と違う(%s): %s" % (k, what, json.dumps(norm(K), ensure_ascii=False)[:300]))
            if list(K) != ["refs", "links"]:
                out_.append(u"表 K の鍵が違う: %s" % list(K))
    tabs = ms.strip_tables(alt_bytes())
    if list(tabs) != list(KINDS) or norm(tabs) != norm(HAND_TABLES):
        out_.append(u"strip_tables の返り値が手で決めた表の並びと違う")
    # 表は元の字・xlink:label の字・接頭辞・属性の並び・空白・引用符・注釈・XML 宣言を持たない
    blob = json.dumps(norm(tabs), ensure_ascii=False)
    for leak in (u"Beta_2", u"Alpha_3", u"Alpha_lab", u"Alpha_verbose", u"xlink:label", u"xlink:from", u"xlink:type", u"<!--", u"Generated by", u"<?xml", u"xmlns", u"encoding", u"xsd:", u"link:", u"xbrli:", u"xbrldt:", u"nonnum", u"WizLabo", u"tree", u"﻿"):
        if leak in blob:
            out_.append(u"表に持たないはずの字が在る: %s" % leak)
    # 表の鍵は属性の並びの順を持たない(要素の宣言の鍵の並びが入力の字の並びと違っても表は同じ)
    e0 = tabs["xsd"]["elements"][0]
    e2 = tabs["xsd"]["elements"][2]
    if norm(e0) == norm(e2) or dict(e0) == dict(e2):
        out_.append(u"作り物の要素が区別できない")
    # 同じ字の xlink:label を持つ端は端の組ごとの arc に開く(from の端 × to の端の順)
    pre = tabs["pre"]["links"][1]
    if [(a["from"], a["to"]) for a in pre["arcs"]] != [(0, 1), (0, 2)]:
        out_.append(u"同じ字の xlink:label の端を端の組ごとの arc に開いていない: %s" % [(a["from"], a["to"]) for a in pre["arcs"]])
    both = (u'<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">'
            u'<link:presentationLink xlink:type="extended" xlink:role="r">'
            u'<link:loc xlink:type="locator" xlink:href="a#1" xlink:label="P"/><link:loc xlink:type="locator" xlink:href="a#2" xlink:label="P"/>'
            u'<link:loc xlink:type="locator" xlink:href="a#3" xlink:label="Q"/><link:loc xlink:type="locator" xlink:href="a#4" xlink:label="Q"/>'
            u'<link:presentationArc xlink:type="arc" xlink:arcrole="x" xlink:from="P" xlink:to="Q" order="5"/></link:presentationLink></link:linkbase>')
    K2 = ms.strip_linkbase(b(both))
    if [(a["from"], a["to"]) for a in K2["links"][0]["arcs"]] != [(0, 2), (0, 3), (1, 2), (1, 3)]:
        out_.append(u"from の端 2 つ × to の端 2 つの開き方の順が違う: %s" % [(a["from"], a["to"]) for a in K2["links"][0]["arcs"]])
    # 端と arc の入り混じりは arc ごとの before(その arc より前に在った端の数)で持つ(Arelle は link の中の端と arc の位置で読み込みの順が変わる)
    if [a["before"] for L in tabs["pre"]["links"] for a in L["arcs"]] != [2, 3, 3, 3] or [a["before"] for L in tabs["def"]["links"] for a in L["arcs"]] != [1, 3, 3, 3] or [a["before"] for L in tabs["lab"]["links"] for a in L["arcs"]] != [2, 3]:
        out_.append(u"arc の前に在った端の数(before)が手で数えた値と違う: %s" % [a["before"] for L in tabs["pre"]["links"] for a in L["arcs"]])
    endsfirst = (u'<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink"><link:presentationLink xlink:type="extended" xlink:role="r">'
                 u'<link:presentationArc xlink:type="arc" xlink:arcrole="x" xlink:from="P" xlink:to="Q" order="5"/>'
                 u'<link:loc xlink:type="locator" xlink:href="a#1" xlink:label="P"/><link:loc xlink:type="locator" xlink:href="a#3" xlink:label="Q"/>'
                 u'<link:presentationArc xlink:type="arc" xlink:arcrole="y" xlink:from="P" xlink:to="Q" order="6"/></link:presentationLink></link:linkbase>')
    if [(a["before"], a["arcrole"]) for a in ms.strip_linkbase(b(endsfirst))["links"][0]["arcs"]] != [(0, u"x"), (2, u"y")]:
        out_.append(u"端より前の arc の before が 0 でない・arc ごとの before を持たない")
    # 属性の値は元の字のまま・label の中身の字は空白も実体参照の解きも ElementTree のとおり
    if ms.strip_linkbase(b(LAB_ALT))["links"][0]["ends"][1]["text"] != TXT1:
        out_.append(u"label の中身の字が違う(先頭の空白・実体参照)")
    return out_


# ======================================================================== 3. 組む
def build_problems(ms=None):
    ms = ms or MS
    out_ = []
    got = ms.build_xsd(copy.deepcopy(HAND_S))
    if got != XSD_CANON:
        i = next((k for k in range(min(len(got), len(XSD_CANON))) if got[k] != XSD_CANON[k]), min(len(got), len(XSD_CANON)))
        out_.append(u"手で書いた表 S から組んだ字が手で書いた字と違う(最初の違い: %r / %r)" % (got[max(0, i - 40):i + 60], XSD_CANON[max(0, i - 40):i + 60]))
    for k in KINDS[1:]:
        got = ms.build_linkbase(copy.deepcopy(HAND_TABLES[k]))
        if got != CANON_TEXTS[k]:
            i = next((n for n in range(min(len(got), len(CANON_TEXTS[k]))) if got[n] != CANON_TEXTS[k][n]), min(len(got), len(CANON_TEXTS[k])))
            out_.append(u"手で書いた表 K(%s)から組んだ字が手で書いた字と違う(最初の違い: %r / %r)" % (k, got[max(0, i - 40):i + 60], CANON_TEXTS[k][max(0, i - 40):i + 60]))
    # 字の形が違う元(属性の順・引用符・空白・コメント・接頭辞・BOM)から、組む部品の決めの字が出る
    built = ms.build_tables(ms.strip_tables(alt_bytes()))
    if list(built) != list(KINDS) or any(built[k] != b(CANON_TEXTS[k]) for k in KINDS):
        out_.append(u"字の形が違う元から組んだ字が決めの字でない: %s" % [k for k in KINDS if built.get(k) != b(CANON_TEXTS[k])])
    nopfx = ms.build_xsd(ms.strip_xsd(b(XSD_NOPFX)))
    if nopfx != XSD_CANON:
        out_.append(u"既定の名前空間の元から組んだ字が決めの字でない(接頭辞は名前空間から決める)")
    # 組んだ字を剥がし直した表が同じ
    again = ms.strip_tables(built)
    if norm(again) != norm(HAND_TABLES):
        out_.append(u"組んだ字を剥がし直した表が元の表と違う")
    if not isinstance(built["xsd"], bytes) or built["xsd"].startswith(b"\xef\xbb\xbf") or not built["xsd"].startswith(b'<?xml version="1.0" encoding="utf-8"?>\n'):
        out_.append(u"組んだ字が utf-8 の bytes・BOM なし・XML 宣言で始まる形でない")
    # 接頭辞の決め
    if ms.assign_prefixes([ms.NS_XSD, ms.NS_XBRLI, TARGET, NS_IOD, NS_NUM, NS_JPCRP]) != od([(ms.NS_XSD, "xsd"), (ms.NS_XBRLI, "xbrli"), (TARGET, "jpcrp030000-asr_E99991-000"), (NS_IOD, "iod"), (NS_NUM, "num"), (NS_JPCRP, "jpcrp_cor")]):
        out_.append(u"接頭辞の決めが違う(固定の表・提出者の名前空間・最後の path の字): %s" % dict(ms.assign_prefixes([ms.NS_XSD, ms.NS_XBRLI, TARGET, NS_IOD, NS_NUM, NS_JPCRP])))
    if ms.prefix_for(u"http://www.xbrl.org/dtr/type/non-numeric") != "nonnum" or ms.prefix_for(u"http://x.example/ns/2022-03-31") != "ns" or ms.prefix_for(u"http://x.example/ns/jppfs_cor") != "jppfs_cor":
        out_.append(u"接頭辞の候補が違う(non-numeric・NCName でない字・最後の path)")
    two = ms.assign_prefixes([u"http://a/b/foo", u"http://c/d/foo", u"http://e/f/foo", u"http://g/link"])
    if list(two.values()) != ["foo", "foo_2", "foo_3", "link_2"]:
        out_.append(u"重なった接頭辞を _2・_3 にしない・固定の接頭辞を使う: %s" % list(two.values()))
    if ms.assign_prefixes([u"http://x/y/ns1", NS_JPCRP, u"http://x/y/ns1"]) != od([(u"http://x/y/ns1", "ns1"), (NS_JPCRP, "jpcrp_cor")]):
        out_.append(u"同じ名前空間が 2 回出ても接頭辞は 1 つでない")
    # 実体参照・引用符
    K = od([("refs", [mk_ref("roleRef", u'http://x/a"b&c', u"h<ref>")]), ("links", [mk_link("labelLink", None, [mk_res(u"a&b <c> \r d\x0b"[:-1], lang=None, role=None)], [])])])
    t = ms.build_linkbase(K)
    if u'roleURI="http://x/a&quot;b&amp;c"' not in t or u'xlink:href="h&lt;ref>"' not in t or u">a&amp;b &lt;c&gt; &#13; d</link:label>" not in t:
        out_.append(u"実体参照の決めが違う: %s" % t)
    if u"xlink:role" in t.split(u"<link:labelLink")[1].split(u"<link:label ")[0] or u"xml:lang" in t or u"xlink:role" in t.split(u"<link:label ")[1]:
        out_.append(u"None の属性を書いている")
    if u"xmlns:xbrldt" in t:
        out_.append(u"xbrldt を使わないのに宣言している")
    return out_


def decline_problems(ms=None):
    ms = ms or MS
    out_ = []
    pre = PRE_ALT
    cases = [
        (u"DOCTYPE", pre.replace(u"<link:linkbase", u'<!DOCTYPE x [<!ENTITY e "v">]><link:linkbase', 1)),
        (u"XML として読めない", pre.replace(u"</link:linkbase>", u"")),
        (u"根が linkbase でない", pre.replace(u"link:linkbase", u"link:other")),
        (u"知らない拡張 link", pre.replace(u"presentationLink", u"footnoteLink")),
        (u"知らない arc", pre.replace(u"presentationArc", u"footnoteArc", 1)),
        (u"知らない属性(arc)", pre.replace(u'order="2"/>', u'order="2" title="x"/>')),
        (u"知らない属性(loc)", pre.replace(u'xlink:label="P"/>', u'xlink:label="P" xlink:title="t"/>')),
        (u"知らない属性(link)", pre.replace(u'xlink:role="http://x/role/b">', u'xlink:role="http://x/role/b" id="i">')),
        (u"知らない属性(roleRef)", pre.replace(u"xlink:type='simple'/>", u"xlink:type='simple' id='q'/>")),
        (u"端の無い xlink:label を指す arc", pre.replace(u'xlink:from="Alpha" xlink:to="Beta_2"', u'xlink:from="Alpha" xlink:to="Nowhere"')),
        (u"arc の type が arc でない", pre.replace(u'xlink:type="arc"/>', u'xlink:type="resource"/>', 1)),
        (u"loc の type が locator でない", pre.replace(u'xlink:type="locator"/>', u'xlink:type="resource"/>', 1)),
        (u"拡張 link の type が extended でない", pre.replace(u'xlink:role="http://x/role/a" xlink:type="extended"', u'xlink:role="http://x/role/a" xlink:type="simple"')),
        (u"label が labelLink の外", pre.replace(u'<link:loc xlink:type="locator" xlink:href="t.xsd#a_P" xlink:label="P"/>', u'<link:label xlink:type="resource" xlink:label="P">t</link:label>')),
        (u"字の在る loc", pre.replace(u'xlink:label="P"/>', u'xlink:label="P">字</link:loc>', 1).replace(u'<link:loc xlink:type="locator" xlink:href="t.xsd#a_P"', u'<link:loc xlink:type="locator" xlink:href="t.xsd#a_P"')),
        (u"link の中の字", pre.replace(u"<!-- tree -->", u"字が在る")),
        (u"linkbase の直下の字", pre.replace(u"<link:roleRef", u"字<link:roleRef", 1)),
        (u"根の属性", pre.replace(u'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">', u'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="z">')),
        (u"知らない子(linkbase の直下)", pre.replace(u"<link:roleRef", u"<link:documentation>d</link:documentation><link:roleRef", 1)),
        (u"知らない文字の符号化", pre.replace(u"<?xml version='1.0'?>", u"<?xml version='1.0' encoding='ISO-8859-1'?>")),
    ]
    for what, text in cases:
        if text == pre:
            out_.append(u"断る例の字が元と同じ(作り損ね): %s" % what)
            continue
        if not declines(ms, ms.strip_linkbase, b(text)):
            out_.append(u"剥がす部品(linkbase)が断らない: %s" % what)
    if not declines(ms, ms.strip_linkbase, b"\xff\xfe<\x00l\x00"):
        out_.append(u"UTF-16 の BOM を断らない")
    u16 = PRE_CANON.replace(u'encoding="utf-8"', u'encoding="utf-16"').encode("utf-16")
    if not declines(ms, ms.strip_linkbase, u16) or not declines(ms, ms.strip_xsd, XSD_CANON.replace(u'encoding="utf-8"', u'encoding="utf-16"').encode("utf-16")):
        out_.append(u"読める UTF-16 の文書(BOM・encoding=utf-16)を断らない")
    bom_iso = u"\ufeff" + PRE_ALT.replace(u"<?xml version='1.0'?>", u"<?xml version='1.0' encoding='ISO-8859-1'?>")
    if not declines(ms, ms.strip_linkbase, b(bom_iso)):
        out_.append(u"BOM つきで encoding が utf-8 でない文書を断らない")
    if declines(ms, ms.strip_linkbase, b(u"\ufeff" + PRE_ALT)):
        out_.append(u"BOM つきの utf-8 の文書を断った")
    lab = LAB_ALT
    for what, text in ((u"label の子", lab.replace(u"冗長</link:label>", u"冗長<b>x</b></link:label>")), (u"label の知らない属性", lab.replace(u'id="lab_1"', u'id="lab_1" z="1"')),
                       (u"label の type", lab.replace(u'xlink:type="resource"', u'xlink:type="locator"', 1)), (u"label の後ろの字", lab.replace(u"</link:label>\n    <link:labelArc", u"</link:label>字\n    <link:labelArc", 1))):
        if text == lab or not declines(ms, ms.strip_linkbase, b(text)):
            out_.append(u"label の断りが効かない: %s" % what)
    xs = XSD_ALT
    xcases = [
        (u"根が schema でない", xs.replace(u"xsd:schema", u"xsd:other")),
        (u"targetNamespace が無い", xs.replace(u'targetNamespace="http://disclosure.edinet-fsa.go.jp/jpcrp030000/asr/001/E99991-000/2026-03-31/01/2026-06-30" ', u"")),
        (u"根の知らない属性", xs.replace(u'elementFormDefault="qualified"', u'elementFormDefault="qualified" id="s"')),
        (u"知らない子(roleType)", xs.replace(u"</xsd:schema>", u'<xsd:complexType name="c"/></xsd:schema>')),
        (u"要素の知らない属性", xs.replace(u'name="Gamma"', u'name="Gamma" form="qualified"')),
        (u"要素に子", xs.replace(u'substitutionGroup="xbrli:item"></xsd:element>', u'substitutionGroup="xbrli:item"><xsd:annotation/></xsd:element>')),
        (u"要素に name が無い", xs.replace(u'name="Gamma" ', u"")),
        (u"import に namespace が無い", xs.replace(u'namespace="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor" ', u"")),
        (u"import の知らない属性", xs.replace(u'<xsd:import ', u'<xsd:import id="i" ')),
        (u"annotation が 2 つ", xs.replace(u"</xsd:annotation>", u"</xsd:annotation><xsd:annotation><xsd:appinfo/></xsd:annotation>")),
        (u"appinfo の知らない子", xs.replace(u"</xsd:appinfo>", u"<xsd:x/></xsd:appinfo>")),
        (u"linkbaseRef の type が simple でない", xs.replace(u'xlink:type="simple" xlink:href="http://example.org/ext_gla.xml"', u'xlink:type="locator" xlink:href="http://example.org/ext_gla.xml"')),
        (u"linkbaseRef の知らない属性", xs.replace(u'xlink:href="x_pre.xml"', u'xlink:href="x_pre.xml" xlink:title="t"')),
        (u"解けない接頭辞", xs.replace(u'type="num:percentItemType"', u'type="nope:percentItemType"')),
        (u"QName の : が 2 つ", xs.replace(u'type="num:percentItemType"', u'type="num:a:b"')),
        (u"要素の宣言の外の字", xs.replace(u"<xsd:element name=", u"字<xsd:element name=")),
    ]
    for what, text in xcases:
        if text == xs:
            out_.append(u"断る例の字が元と同じ(作り損ね): %s" % what)
            continue
        if not declines(ms, ms.strip_xsd, b(text)):
            out_.append(u"剥がす部品(xsd)が断らない: %s" % what)
    # file の種類が 1 つずつでない
    ent = [(types.SimpleNamespace(filename="XBRL/PublicDoc/a" + ms.FILE_SUFFIX[k]), b"x") for k in KINDS]
    if list(ms.find_files(ent)) != list(KINDS):
        out_.append(u"find_files が 6 種類を拾わない")
    for what, e2 in ((u"lab-en が無い", ent[:4] + ent[5:]), (u"xsd が 2 つ", ent + [(types.SimpleNamespace(filename="XBRL/PublicDoc/b.xsd"), b"x")]), (u"_pre が 2 つ", ent + [(types.SimpleNamespace(filename="XBRL/PublicDoc/c_pre.xml"), b"x")])):
        if not declines(ms, ms.find_files, e2):
            out_.append(u"file の種類が 1 つずつでないのに断らない: %s" % what)
    deeper = ent + [(types.SimpleNamespace(filename="XBRL/PublicDoc/sub/z_pre.xml"), b"x"), (types.SimpleNamespace(filename="XBRL/AuditDoc/y.xsd"), b"x"), (types.SimpleNamespace(filename="XBRL/PublicDoc/manifest_PublicDoc.xml"), b"x")]
    if declines(ms, ms.find_files, deeper):
        out_.append(u"PublicDoc の直下でない file・AuditDoc・マニフェストを数えて断った")
    # strip_tables の中の例外も断る
    bad = alt_bytes()
    bad["cal"] = None
    if not declines(ms, ms.strip_tables, bad):
        out_.append(u"剥がす途中の例外を断らない")
    # 組む部品が知らない形に当たったとき断る
    S = copy.deepcopy(HAND_S)
    S["elements"][0]["zzz"] = "1"
    if not declines(ms, ms.build_xsd, S):
        out_.append(u"組む部品(xsd)が知らない属性を断らない")
    for what, mut in ((u"知らない拡張 link", lambda K: K["links"][0].__setitem__("tag", "footnoteLink")), (u"arc の端の番号", lambda K: K["links"][0]["arcs"][0].__setitem__("to", 99)),
                      (u"arc の知らない属性", lambda K: K["links"][0]["arcs"][0]["attrs"].__setitem__("zzz", "1")), (u"知らない ref", lambda K: K["refs"][0].__setitem__("tag", "foo")),
                      (u"知らない端", lambda K: K["links"][0]["ends"][0].__setitem__("kind", "zzz")), (u"labelLink でない所の label", lambda K: K["links"][0]["ends"].append(mk_res(u"t")))):
        K = copy.deepcopy(HAND_PRE)
        mut(K)
        if not declines(ms, ms.build_linkbase, K):
            out_.append(u"組む部品(linkbase)が断らない: %s" % what)
    for what, mut in ((u"arc の位置(before)が端の数より大きい", lambda K: K["links"][0]["arcs"][0].__setitem__("before", 99)), (u"arc の位置(before)が戻る", lambda K: K["links"][0]["arcs"][1].__setitem__("before", 0)),
                      (u"arc の位置(before)が負", lambda K: K["links"][0]["arcs"][0].__setitem__("before", -1))):
        K = copy.deepcopy(HAND_PRE)
        mut(K)
        if not declines(ms, ms.build_linkbase, K):
            out_.append(u"組む部品(linkbase)が断らない: %s" % what)
    tb = fresh_hand()
    tb["pre"]["links"][0]["arcs"][0]["to"] = 99
    if not declines(ms, ms.build_tables, tb):
        out_.append(u"build_tables が知らない形で断らない")
    tb = fresh_hand()
    tb["cal"] = None
    if not declines(ms, ms.build_tables, tb):
        out_.append(u"組む途中の例外を断らない")
    return out_


# ======================================================================== 4. 混ぜ物
def mix_problems(ms=None):
    ms = ms or MS
    out_ = []
    base = fresh_hand()
    snap = json.dumps(norm(base), ensure_ascii=False, sort_keys=True)
    got = [ms.mix_tables(base, i) for i in range(6)]
    if json.dumps(norm(base), ensure_ascii=False, sort_keys=True) != snap:
        out_.append(u"混ぜ物が元の表を書き換えた")
    if any(g is None for g in got):
        out_.append(u"作れるはずの混ぜ物が作れない: %s" % [i for i, g in enumerate(got) if g is None])
        return out_
    if [g[0] for g in got] != ["pre", "cal", "lab", "lab-en", "xsd", "def"]:
        out_.append(u"混ぜ物の当て先の表の種類が違う: %s" % [g[0] for g in got])
    # M1: 表示の表の最初の link の最初の arc を除く
    T = got[0][1]
    if [len(L["arcs"]) for L in T["links"]] != [1, 2] or norm(T["links"][0]["arcs"][0]) != norm(HAND_PRE["links"][0]["arcs"][1]) or len(T["links"][0]["ends"]) != 3:
        out_.append(u"M1(表示の arc を抜く)の結果が違う")
    # M2: 計算の最初の arc の weight 1 → -1
    T = got[1][1]
    if [a["attrs"]["weight"] for L in T["links"] for a in L["arcs"]] != ["-1", "-1", "1"]:
        out_.append(u"M2(計算の向きを返す)の結果が違う: %s" % [a["attrs"]["weight"] for L in T["links"] for a in L["arcs"]])
    # M3・M4: 最初の label の字の後ろに X
    if got[2][1]["links"][0]["ends"][1]["text"] != TXT1 + u"X" or got[2][1]["links"][0]["ends"][2]["text"] != u"冗長":
        out_.append(u"M3(日本語のラベルを変える)の結果が違う")
    if got[3][1]["links"][0]["ends"][1]["text"] != u"SalesX":
        out_.append(u"M4(英語のラベルを変える)の結果が違う")
    # M5: 最初の abstract=false(Alpha)の periodType duration → instant
    T = got[4][1]
    if [e.get("{%s}periodType" % NS_XBRLI) for e in T["elements"]] != ["instant", "instant", "instant"]:
        out_.append(u"M5(期の型を返す)の結果が違う: %s" % [e.get("{%s}periodType" % NS_XBRLI) for e in T["elements"]])
    # M6: 定義の最初の domain-member の arc を除く(順で最初は番号 0 の arc。2 つ目の domain-member は残る)
    T = got[5][1]
    if [a["arcrole"] for a in T["links"][0]["arcs"]] != [ALL, GS, DM] or T["links"][0]["arcs"][2]["attrs"] != {"order": "2"}:
        out_.append(u"M6(定義の arc を抜く)の結果が違う: %s" % [a["arcrole"] for a in T["links"][0]["arcs"]])
    # M5 は期の型が instant なら duration に返す
    t2 = fresh_hand()
    t2["xsd"]["elements"][0]["{%s}periodType" % NS_XBRLI] = "instant"
    t2["xsd"]["elements"][1]["abstract"] = "false"
    r = ms.mix_tables(t2, 4)
    if r is None or r[1]["elements"][0]["{%s}periodType" % NS_XBRLI] != "duration":
        out_.append(u"M5 が instant を duration に返さない")
    # M5 は最初の abstract=false だけを見る(abstract=true の見出しを飛ばす)
    t3 = fresh_hand()
    t3["xsd"]["elements"].insert(0, {"name": "H", "abstract": "true", "{%s}periodType" % NS_XBRLI: "duration"})
    r = ms.mix_tables(t3, 4)
    if r is None or r[1]["elements"][0]["{%s}periodType" % NS_XBRLI] != "duration" or r[1]["elements"][1]["{%s}periodType" % NS_XBRLI] != "instant":
        out_.append(u"M5 が abstract が true の要素を飛ばして最初の false の要素に当てていない")
    # M1・M2・M6: link の並びと arc の並びの順で最初の arc(最初の link が arc を持たなければ次の link)
    t4 = fresh_hand()
    t4["pre"]["links"][0]["arcs"] = []
    r = ms.mix_tables(t4, 0)
    if r is None or [len(L["arcs"]) for L in r[1]["links"]] != [0, 1]:
        out_.append(u"M1 が arc の無い link を飛ばして次の link の最初の arc に当てていない")
    # 作れなかった
    t5 = fresh_hand()
    for k in ("pre", "cal", "def"):
        for L in t5[k]["links"]:
            L["arcs"] = []
    for k in ("lab", "lab-en"):
        for L in t5[k]["links"]:
            L["ends"] = [e for e in L["ends"] if e["kind"] == "loc"]
            L["arcs"] = []
    for e in t5["xsd"]["elements"]:
        e["abstract"] = "true"
    if [ms.mix_tables(t5, i) for i in range(6)] != [None] * 6:
        out_.append(u"当て先が無いのに混ぜ物を作った")
    t6 = fresh_hand()
    t6["cal"]["links"][0]["arcs"][0]["attrs"]["weight"] = "0.5"
    if ms.mix_tables(t6, 1) is not None:
        out_.append(u"M2: 最初の arc の weight が 1 でも -1 でもないのに作った")
    t6["cal"]["links"][0]["arcs"][0]["attrs"]["weight"] = "-1"
    r = ms.mix_tables(t6, 1)
    if r is None or r[1]["links"][0]["arcs"][0]["attrs"]["weight"] != "1":
        out_.append(u"M2 が -1 を 1 に返さない")
    t7 = fresh_hand()
    del t7["xsd"]["elements"][0]["{%s}periodType" % NS_XBRLI]
    if ms.mix_tables(t7, 4) is not None:
        out_.append(u"M5: periodType が無いのに作った")
    t8 = fresh_hand()
    for a in t8["def"]["links"][0]["arcs"]:
        if a["arcrole"] == DM:
            a["arcrole"] = ALL
    if ms.mix_tables(t8, 5) is not None:
        out_.append(u"M6: domain-member の arc が無いのに作った")
    # 組んで差が出る: 混ぜ物の表から組んだ字は元の字と違い、変えた kind の字だけが違う
    built0 = ms.build_tables(fresh_hand())
    for i, (kind, T) in enumerate(got):
        f2 = ms.build_xsd(T) if kind == "xsd" else ms.build_linkbase(T)
        if f2.encode("utf-8") == built0[kind]:
            out_.append(u"混ぜ物 %d の字が元と同じ(作った表が組む字に効いていない)" % (i + 1))
    return out_


# ======================================================================== 5. 比べる
def compare_problems(ms=None):
    ms = ms or MS
    out_ = []
    csv.field_size_limit(131072)                  # csv の上限は process で共有。直す前の値に戻してから、読む部品が直すかを見る
    with Temp() as d:
        p = os.path.join(d, "a.csv")
        with io.open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(u'﻿Name,Value\r\nb,"x,y"\r\na,"長い\r\n行"\r\n')
        rows = ms.read_table_rows(p)
        if rows != [(u"﻿Name", u"Value"), (u"b", u"x,y"), (u"a", u"長い\r\n行")]:
            out_.append(u"CSV の読み(見出しの行を含む・file の順のまま・引用つきの欄)が違う: %s" % rows)
        if ms.read_table_rows(os.path.join(d, "none.csv")) != []:
            out_.append(u"CSV が無いとき [] でない")
        with io.open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(u"Name,Value\r\n" + u"a," + u"z" * 200000 + u"\r\n")
        if len(ms.read_table_rows(p)[1][1]) != 200000:
            out_.append(u"長い欄を読めない(csv の欄の大きさの上限)")
    H, R1, R2 = [(u"h",)], [(u"a",)], [(u"b",)]
    for key in ms.NEED_ROWS:
        if ms.output_same(key, H + R1, H + R1) is not True or ms.output_same(key, H + R1, H + R2) or ms.output_same(key, H, H) or ms.output_same(key, [], []) or ms.output_same(key, H, H + R1) \
                or ms.output_same(key, H + R1, H) or ms.output_same(key, H + R1 + R2, H + R2 + R1):
            out_.append(u"書き出し(%s)の比べが違う(行が 1 以下は同じとしない・並びが違えば違う)" % key)
    if ms.canon_rows([]) != [] or ms.canon_rows([(u"h",)]) != [(u"h",)]:
        out_.append(u"canon_rows が空・見出しだけで違う")
    if ms.canon_rows([(u"h", u"z"), (u"b", u"2"), (u"b", u"1"), (u"a", u"9"), (u"b", u"0")]) != [(u"h", u"z"), (u"b", u"1"), (u"b", u"2"), (u"a", u"9"), (u"b", u"0")]:
        out_.append(u"canon_rows が同じ先頭の欄が続く行の中だけを並べ替えていない(ラベルの並びは保つ・離れた同じ先頭の欄は混ぜない)")
    ordered = [(u"h", u"z"), (u"b", u"2"), (u"b", u"1"), (u"a", u"9")]
    if not ms.output_same(u"概念", ordered, [(u"h", u"z"), (u"b", u"1"), (u"b", u"2"), (u"a", u"9")]) or ms.output_same(u"概念", ordered, [(u"h", u"z"), (u"a", u"9"), (u"b", u"1"), (u"b", u"2")]) \
            or ms.output_same(u"概念", ordered, [(u"h", u"z"), (u"b", u"2"), (u"b", u"1"), (u"a", u"8")]) or ms.output_same(u"概念", ordered, ordered[:3]):
        out_.append(u"概念は同じ先頭の欄の行の中の並びだけを問わない(ラベルの並び・行の中身・行の数は問う)")
    for key in (u"役割型", u"表示", u"計算", u"次元", u"ラベルの関係", u"一般特殊"):
        if ms.output_same(key, ordered, [(u"h", u"z"), (u"b", u"1"), (u"b", u"2"), (u"a", u"9")]):
            out_.append(u"概念のほかの書き出しは並びを問う: %s" % key)
    if list(ms.UNORDERED_OUTPUTS) != [u"概念"] or list(ms.SEED_PREFIX) != ["/usr/bin/env", "PYTHONHASHSEED=0"]:
        out_.append(u"並びを問わない書き出し・種の固定が決めと違う")
    for key in (u"計算", u"次元", u"一般特殊"):
        if ms.output_same(key, H, H) is not True or ms.output_same(key, [], []) is not True or ms.output_same(key, [], H) or ms.output_same(key, H + R1, H + R2) or ms.output_same(key, H + R1 + R2, H + R2 + R1):
            out_.append(u"書き出し(%s)の比べが違う(中身が無い書類は両方が同じ字なら同じ)" % key)
    a = od((k, H + R1) for k in ms.OUTPUT_KEYS)
    s = ms.outputs_same(a, copy.deepcopy(a))
    if list(s) != list(ms.OUTPUT_KEYS) or not all(s.values()):
        out_.append(u"outputs_same が 7 つ全部同じを返さない")
    for k in ms.OUTPUT_KEYS:
        c = copy.deepcopy(a)
        c[k] = H + R2
        s = ms.outputs_same(a, c)
        if [x for x in ms.OUTPUT_KEYS if not s[x]] != [k]:
            out_.append(u"書き出し 1 つだけ違うとき、その 1 つだけが違うと言わない: %s" % k)
    # 道具の呼び方(封 §1 の字のとおり)
    paths = ms.csv_paths("/w", "t")
    if list(paths) != ["facts"] + list(ms.OUTPUT_KEYS) or len(set(paths.values())) != 8:
        out_.append(u"CSV の場所が 8 つの別々の場所でない")
    ca = ms.command_a("/T", "/z.zip", paths)
    want_a = ["/T/bin/arelleCmdLine", "--plugins", "validate/EDINET|inlineXbrlDocumentSet", "--disclosureSystem", "EDINET-2026", "-f", "/z.zip", "--validate", "--facts", paths["facts"], "--factListCols",
              "Name contextRef unitRef Dec Value EntityScheme EntityIdentifier Period Dimensions", "--concepts", paths[u"概念"], "--pre", paths[u"表示"], "--cal", paths[u"計算"], "--dim", paths[u"次元"],
              "--roleTypes", paths[u"役割型"], "--viewArcrole", "http://www.xbrl.org/2003/arcrole/concept-label", "--viewFile", paths[u"ラベルの関係"], "--relationshipCols", "Name"]
    if ca != want_a:
        out_.append(u"掛け方 A の引数が封と違う: %s" % ca)
    cb = ms.command_b("/T", "/z.zip", paths)
    want_b = ["/T/bin/arelleCmdLine", "--plugins", "validate/EDINET|inlineXbrlDocumentSet", "--disclosureSystem", "EDINET-2026", "-f", "/z.zip", "--viewArcrole", "http://www.xbrl.org/2003/arcrole/general-special",
              "--viewFile", paths[u"一般特殊"], "--relationshipCols", "Name"]
    if cb != want_b:
        out_.append(u"掛け方 B の引数が封と違う(--validate を付けない): %s" % cb)
    return out_


# ---- 作り物の道具(runner)。道具が読む「タクソノミ」は、zip の中の file の意味から作る(label の字・arc の並び・属性・weight・期の型・要素の宣言)。字の形(属性の順・空白・接頭辞)には依らない
ACT = u"Activation of plug-in Validate EDINET successful"
FMT = u"Identified filing format"
FREEZE = u"foo==1.0\narelle-release==2.47.5\n"
PYVER = u"Python 3.11.17\n"
MV_P = b"model value P content"
LN = "{http://www.xbrl.org/2003/linkbase}"
XL = "{http://www.w3.org/1999/xlink}"
XMLLANG = "{http://www.w3.org/XML/1998/namespace}lang"
XS = "{http://www.w3.org/2001/XMLSchema}"
XB = "{http://www.xbrl.org/2003/instance}"


def fake_link_rows(data):
    u"""linkbase の bytes → 関係の行([(link の role, from の端, to の端, 属性の組)])。arc の並びのまま。"""
    root = ET.fromstring(data)
    rows = []
    for link in root:
        if not link.tag.endswith("Link"):
            continue
        desc = {}
        for c in link:
            if c.tag == LN + "loc":
                desc.setdefault(c.get(XL + "label"), []).append(("loc", c.get(XL + "href"), c.get(XL + "role")))
            elif c.tag == LN + "label":
                desc.setdefault(c.get(XL + "label"), []).append(("res", c.text or "", c.get(XMLLANG), c.get(XL + "role"), c.get("id")))
        for c in link:
            if c.tag.endswith("Arc"):
                extra = tuple(sorted((k, v) for k, v in c.attrib.items() if k not in (XL + "type", XL + "from", XL + "to")))
                for f in desc[c.get(XL + "from")]:
                    for t in desc[c.get(XL + "to")]:
                        rows.append((link.get(XL + "role"), f, t, extra))
    return rows


def fake_concept_rows(data):
    root = ET.fromstring(data.lstrip(b"\xef\xbb\xbf"))
    rows = []
    for e in root.iter(XS + "element"):
        rows.append((e.get("name"), e.get("type"), e.get("substitutionGroup"), e.get(XB + "periodType"), e.get("abstract"), e.get(XB + "balance"), e.get("nillable")))
    return sorted(rows)


def fake_role_rows(blobs):
    roles = set()
    for n, data in blobs.items():
        if n.endswith("_pre.xml") or n.endswith("_cal.xml") or n.endswith("_def.xml"):
            for link in ET.fromstring(data):
                if link.tag.endswith("Link"):
                    roles.add(link.get(XL + "role"))
    return sorted(roles)


def blob_of(blobs, suffix):
    return [data for n, data in blobs.items() if n.startswith("XBRL/PublicDoc/") and n.endswith(suffix)][0]


def fake_view(blobs):
    u"""包みの file(名 → bytes)→ ({書き出しの名: 行}, fact の行, 出力の字の指摘の数)。"""
    out = {}
    out[u"概念"] = [(u"Name", u"Type", u"Sub", u"Period", u"Abstract", u"Balance", u"Nillable")] + fake_concept_rows(blob_of(blobs, ".xsd"))
    out[u"役割型"] = [(u"Role",)] + [(r,) for r in fake_role_rows(blobs)]
    out[u"表示"] = [(u"pre",)] + [(repr(r),) for r in fake_link_rows(blob_of(blobs, "_pre.xml"))]
    out[u"計算"] = [(u"cal",)] + [(repr(r),) for r in fake_link_rows(blob_of(blobs, "_cal.xml"))]
    drows = fake_link_rows(blob_of(blobs, "_def.xml"))
    out[u"次元"] = [(u"dim",)] + [(repr(r),) for r in drows]
    out[u"ラベルの関係"] = [(u"lab",)] + [(repr(r),) for r in fake_link_rows(blob_of(blobs, "_lab.xml")) + fake_link_rows(blob_of(blobs, "_lab-en.xml"))]
    out[u"一般特殊"] = [(u"gs",)] + [(repr(r),) for r in drows if ("arcrole", GS) in r[3] or any(k == XL + "arcrole" and v == GS for k, v in r[3])]
    htm = [data.decode("utf-8") for n, data in blobs.items() if n.endswith(".htm")]
    facts = [(u"Name",)] + [(m,) for t in htm for m in re.findall(r'name="([^"]+)"', t)]
    neg = sum(1 for r in fake_link_rows(blob_of(blobs, "_cal.xml")) if ("weight", "-1") in r[3])
    return out, facts, neg


SEED = ["/usr/bin/env", "PYTHONHASHSEED=0"]


def is_tool_call(cmd):
    return any(os.path.basename(c) == "arelleCmdLine" for c in list(cmd)[:3])


def strip_seed(cmd):
    cmd = list(cmd)
    return cmd[2:] if cmd[:2] == SEED else cmd


class FakeRunner(object):
    u"""道具の呼び出しの作り物。呼ばれた順・zip の中身・csv の場所を覚える。タクソノミは zip の中の file の意味から読み、weight が -1 の arc の数だけ ``EC5611W`` の行を出す(掛け方 A だけ)。"""

    def __init__(self, mv_path, freeze=FREEZE, pyver=PYVER, crash_on=None):
        self.mv_path, self.freeze, self.pyver = mv_path, freeze, pyver
        self.calls = []
        self.crash_on = crash_on

    def write_csv(self, path, rows):
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(u"﻿")
            w = csv.writer(fh)
            for r in rows:
                w.writerow(r)

    def __call__(self, cmd, timeout):
        raw = list(cmd)
        cmd = strip_seed(raw)
        if os.path.basename(cmd[0]) == "arelleCmdLine":
            zp = cmd[cmd.index("-f") + 1]
            with zipfile.ZipFile(zp) as z:
                blobs = dict((n, z.read(n)) for n in z.namelist())
            self.calls.append(dict(cmd=cmd, raw=raw, timeout=timeout, names=list(blobs), blobs=blobs, zip=zp, existed=os.path.exists(zp)))
            if self.crash_on is not None and len(self.calls) == self.crash_on:
                raise RuntimeError("boom")
            view, facts, neg = fake_view(blobs)
            validate = "--validate" in cmd
            if "--facts" in cmd:
                self.write_csv(cmd[cmd.index("--facts") + 1], facts)
            for flag, key in (("--concepts", u"概念"), ("--roleTypes", u"役割型"), ("--pre", u"表示"), ("--cal", u"計算"), ("--dim", u"次元")):
                if flag in cmd:
                    self.write_csv(cmd[cmd.index(flag) + 1], view[key])
            if "--viewArcrole" in cmd:
                key = u"ラベルの関係" if cmd[cmd.index("--viewArcrole") + 1] == CL else u"一般特殊"
                self.write_csv(cmd[cmd.index("--viewFile") + 1], view[key])
            lines = [u"[info] " + ACT, u"[info] " + FMT + u": EDINET"]
            if validate:
                lines += [u"[EDINET.EC5611W] 本文の字 %d" % i for i in range(neg)]
            return u"\n".join(lines) + u"\n", False
        if cmd[1:] == ["-m", "pip", "freeze"]:
            return self.freeze, False
        if cmd[1] == "-c":
            return self.mv_path + u"\n", False
        if cmd[1:] == ["--version"]:
            return self.pyver, False
        raise AssertionError(cmd)


def make_tool(d):
    t = os.path.join(d, "tool_p")
    os.makedirs(os.path.join(t, "bin"))
    with open(os.path.join(t, "bin", "arelleCmdLine"), "w") as fh:
        fh.write("#!/bin/sh\n")
    mv = os.path.join(t, "ModelValue.py")
    with open(mv, "wb") as fh:
        fh.write(MV_P)
    return t, mv


STEM = "XBRL/PublicDoc/jpcrp030000-asr-001_E99991-000_2026-03-31_01_2026-06-30"
HTM_NAME = "XBRL/PublicDoc/0101010_honbun_E99991-000_ixbrl.htm"
HTM_TEXT = u'<html><body><ix:nonFraction name="jppfs_cor:Assets" contextRef="C1">5</ix:nonFraction><ix:nonNumeric name="jpcrp_cor:Title" contextRef="C1">題</ix:nonNumeric></body></html>'
SAME_KIND = "lab-en"                        # 作り物の書類で、元の字が組む部品の決めの字と同じ file(字が同じになるのはこの 1 種類だけ)


def doc_texts(no):
    texts = od((k, ALT_TEXTS[k]) for k in KINDS)
    texts[SAME_KIND] = CANON_TEXTS[SAME_KIND]
    return od((k, v.replace("E99991", "E9999%d" % no)) for k, v in texts.items())


def make_doc_zip(path, no=1, declined=False, shuffle=False):
    u"""作り物の書類。PublicDoc に ``.xsd`` と linkbase 5 つ・``.htm``・マニフェスト・``.xbrl``(API が足した file)・AuditDoc。"""
    texts = doc_texts(no)
    if declined:
        texts["cal"] = texts["cal"].replace(u'weight="1"', u'weight="1" zzz="1"', 1)
    items = [(STEM.replace("E99991", "E9999%d" % no) + FILE_SUFFIX_OF[k], texts[k].encode("utf-8")) for k in KINDS]
    if shuffle:
        items.reverse()
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("XBRL/PublicDoc/manifest_PublicDoc.xml", b"<manifest/>")
        for n, data in items:
            z.writestr(n, data)
        z.writestr(HTM_NAME.replace("E99991", "E9999%d" % no), HTM_TEXT.encode("utf-8"))
        z.writestr("XBRL/PublicDoc/api_added_E9999%d-000.xbrl" % no, b"<xbrl/>")
        z.writestr("XBRL/AuditDoc/audit.xml", b"<a/>")


FILE_SUFFIX_OF = {"xsd": ".xsd", "cal": "_cal.xml", "def": "_def.xml", "lab": "_lab.xml", "lab-en": "_lab-en.xml", "pre": "_pre.xml"}


def make_docs(d, count=3, declined=()):
    for i in range(count):
        make_doc_zip(os.path.join(d, "S2FAKE0%d.zip" % (i + 1)), i + 1, declined=(i + 1) in declined)
    other = os.path.join(d, "S2OTHER1.zip")
    with zipfile.ZipFile(other, "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


STEMS = ["S2FAKE01", "S2FAKE02", "S2FAKE03"]
ORDER_SHA = hashlib.sha256(u"\n".join(STEMS).encode("utf-8")).hexdigest()
#: 作り物の書類の手で数えた値(``fake_view`` の行の数。見出しの行を含む): 概念 3 + 1・役割型(a・b・d)3 + 1・表示 4 + 1・計算 3 + 1・次元 4 + 1・ラベル(lab 2 + lab-en 1)3 + 1・一般特殊 1 + 1
HAND_ROWS = od([(u"概念", 4), (u"役割型", 4), (u"表示", 5), (u"計算", 4), (u"次元", 5), (u"ラベルの関係", 4), (u"一般特殊", 2)])
HAND_FACT_ROWS = 2
HAND_COUNTS = {u"要素の宣言": 3, "cal": (2, 5, 3, 0), "def": (1, 3, 4, 0), "lab": (1, 3, 2, 2), "lab-en": (1, 2, 1, 1), "pre": (2, 6, 4, 0)}


def hand_counts_ok(tc):
    if tc[u"要素の宣言"] != HAND_COUNTS[u"要素の宣言"]:
        return False
    for k in KINDS[1:]:
        if tuple(tc[k][f] for f in (u"link", u"端", u"arc", u"ラベルの数")) != HAND_COUNTS[k]:
            return False
    return True


def doc_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        docs = os.path.join(d, "docs")
        os.makedirs(docs)
        make_doc_zip(os.path.join(docs, "S2FAKE01.zip"), 1)
        tool, mv = make_tool(d)
        tmp = os.path.join(d, "tmp")
        os.makedirs(tmp)
        zp = os.path.join(docs, "S2FAKE01.zip")
        before = read_bytes_sha(zp)
        r = FakeRunner(mv)
        rec = ms.process_doc(tool, zp, tmp, r, mixtures=True)
        # 呼び出し: 元 A・B・組み直し A・B・混ぜ物 6 つ × (A・B) = 16 回。同じ掛け方(zip と csv の場所だけが違う)・上限 600
        if len(r.calls) != 16:
            out_.append(u"道具の呼び出しが 16 回でない: %d" % len(r.calls))
        else:
            for i in range(0, 16, 2):
                ca, cb = r.calls[i], r.calls[i + 1]
                if u"--validate" not in ca["cmd"] or u"--validate" in cb["cmd"] or u"--viewArcrole" not in cb["cmd"] or ca["zip"] != cb["zip"]:
                    out_.append(u"呼び出しの対(A・B)が違う: %d" % i)
                    break
            if any(c["timeout"] != 600 for c in r.calls) or any(not c["existed"] for c in r.calls):
                out_.append(u"時間の上限・zip が無い")
            if any(c["raw"][:2] != SEED or c["raw"][2:] != c["cmd"] for c in r.calls):
                out_.append(u"道具の呼び出しの前に /usr/bin/env PYTHONHASHSEED=0 を付けていない")
            if r.calls[0]["cmd"] != ms.command_a(tool, r.calls[0]["zip"], ms.csv_paths(os.path.dirname(r.calls[0]["zip"]), "orig")) or r.calls[1]["cmd"] != ms.command_b(tool, r.calls[1]["zip"], ms.csv_paths(os.path.dirname(r.calls[1]["zip"]), "orig")):
                out_.append(u"元の包みに掛けた引数が掛け方 A・B の関数の返り値と違う")
            if len(set(c["zip"] for c in r.calls[::2])) != 8 or len(set(os.path.dirname(c["zip"]) for c in r.calls)) != 1:
                out_.append(u"包みの場所を使い回している(か使い捨ての場所が 1 つでない)")
            if [os.path.basename(c["zip"]) for c in r.calls[:4]] != ["orig.zip", "orig.zip", "new.zip", "new.zip"]:
                out_.append(u"元の包み・組み直した包みの順・名が違う")
            for c in r.calls:
                if any(n.endswith(".xbrl") for n in c["names"]) or c["blobs"]["XBRL/AuditDoc/audit.xml"] != b"<a/>" or c["blobs"]["XBRL/PublicDoc/manifest_PublicDoc.xml"] != b"<manifest/>" or c["blobs"][HTM_NAME] != HTM_TEXT.encode("utf-8"):
                    out_.append(u"掛けた包みの中身が違う(.xbrl が残る・タクソノミ以外の file が変わった)")
                    break
            o, n = r.calls[0]["blobs"], r.calls[2]["blobs"]
            texts = doc_texts(1)
            for k in KINDS:
                nm = STEM + FILE_SUFFIX_OF[k]
                if o[nm].decode("utf-8") != texts[k]:
                    out_.append(u"元の包みの %s が元の字でない" % k)
                if n[nm] != b(CANON_TEXTS[k].replace("E99991", "E99991")) and k != "xsd":
                    out_.append(u"組み直した包みの %s が組んだ字でない(比べる相手が同じ file になっている)" % k)
            if n[STEM + ".xsd"].decode("utf-8") != XSD_CANON or n[STEM + "_lab-en.xml"] != o[STEM + "_lab-en.xml"]:
                out_.append(u"組み直した包みの xsd が組んだ字でない・元の字が決めの字の file が変わった")
            if len(set(hashlib.sha256(n[STEM + FILE_SUFFIX_OF[k]]).hexdigest() == hashlib.sha256(o[STEM + FILE_SUFFIX_OF[k]]).hexdigest() for k in KINDS)) != 2:
                out_.append(u"元の包みと組み直した包みの file が全部同じか全部違う(比べ方が効かない)")
        if rec[u"断った"] or rec[u"断った理由"] != u"":
            out_.append(u"断らない書類を断った: %s" % rec[u"断った理由"])
        if dict(rec[u"元の書き出しの行の数"]) != dict(HAND_ROWS) or dict(rec[u"組み直しの書き出しの行の数"]) != dict(HAND_ROWS):
            out_.append(u"書き出しの行の数が手で数えた値と違う: %s %s" % (dict(rec[u"元の書き出しの行の数"]), dict(rec[u"組み直しの書き出しの行の数"])))
        if rec[u"元の fact の行の数"] != HAND_FACT_ROWS or rec[u"組み直しの fact の行の数"] != HAND_FACT_ROWS:
            out_.append(u"fact の行の数が違う(手で数えた値は %d)" % HAND_FACT_ROWS)
        if not all(rec[u"書き出しが同じ"].values()) or list(rec[u"書き出しが同じ"]) != list(ms.OUTPUT_KEYS) or not rec[u"タクソノミが同じ"] or not rec[u"fact が同じ"] or not rec[u"鳴り方が同じ"] or not rec[u"全部同じ"]:
            out_.append(u"組み直しで書き出し・fact・鳴り方が同じにならない: %s" % json.dumps(rec[u"書き出しが同じ"], ensure_ascii=False))
        if dict(rec[u"字が同じ"]) != {"xsd": False, "cal": False, "def": False, "lab": False, "lab-en": True, "pre": False} or list(rec[u"字が同じ"]) != list(KINDS):
            out_.append(u"字が同じ file が手で決めた値と違う: %s" % json.dumps(rec[u"字が同じ"]))
        if rec[u"元の 1 回"][u"符号ごとの行"] != {u"EDINET.EC5611W": 1} or rec[u"元の 1 回"][u"類"] != u"走った" or rec[u"組み直しの 1 回"] != rec[u"元の 1 回"]:
            out_.append(u"元の 1 回の数が違う")
        if not hand_counts_ok(rec[u"表の数"]):
            out_.append(u"表の数が手で数えた値と違う: %s" % json.dumps(rec[u"表の数"], ensure_ascii=False))
        # 混ぜ物 6 つ(手で決めた値)
        got = [(m[u"種類"], m[u"作った"], m[u"違いを見つけた"], m[u"鳴り方が違う"]) for m in rec[u"混ぜ物"]]
        want = [(k, True, True, i == 1) for i, k in enumerate((u"表示の arc を抜く", u"計算の向きを返す", u"日本語のラベルを変える", u"英語のラベルを変える", u"期の型を返す", u"定義の arc を抜く"))]
        if got != want:
            out_.append(u"混ぜ物 6 つの結果が手で決めた値と違う: %s" % got)
        mix = [c for c in r.calls[4:]]
        mn = STEM
        wants = [(mn + "_pre.xml", None), (mn + "_cal.xml", None), (mn + "_lab.xml", None), (mn + "_lab-en.xml", None), (mn + ".xsd", None), (mn + "_def.xml", None)]
        for i, (nm, _x) in enumerate(wants):
            blobs = mix[2 * i]["blobs"]
            diff = [k for k in blobs if k in r.calls[2]["blobs"] and blobs[k] != r.calls[2]["blobs"][k]]
            if diff != [nm]:
                out_.append(u"混ぜ物 %d の包みが組み直した包みと違うのは変えた kind の file だけであるはず: %s" % (i + 1, diff))
        if read_bytes_sha(zp) != before:
            out_.append(u"置き場の zip が変わった")
        if os.listdir(tmp):
            out_.append(u"使い捨ての場所が残っている")
        # 既定の runner は V.exec_cmd(作り物に差し替えて、呼ばれることを見る)
        fake_default = FakeRunner(mv)
        saved = ms.V.exec_cmd
        ms.V.exec_cmd = fake_default
        try:
            ms.process_doc(tool, zp, tmp, None, mixtures=False)
            ms.check_tool(tool, None, want_sha=hashlib.sha256(MV_P).hexdigest())
        finally:
            ms.V.exec_cmd = saved
        if len(fake_default.calls) != 4:
            out_.append(u"既定の runner が V.exec_cmd でない(道具を自分で呼んでいる): %d" % len(fake_default.calls))
        # 混ぜ物を作らない呼び方
        r2 = FakeRunner(mv)
        rec2 = ms.process_doc(tool, zp, tmp, r2, mixtures=False)
        if len(r2.calls) != 4 or rec2[u"混ぜ物"] != []:
            out_.append(u"混ぜ物を作らない呼び方で 4 回でない")
        # zip の並びによらない(逆順の zip でも同じ)
        make_doc_zip(os.path.join(docs, "S2REV.zip"), 1, shuffle=True)
        rec3 = ms.process_doc(tool, os.path.join(docs, "S2REV.zip"), tmp, FakeRunner(mv), mixtures=False)
        if not rec3[u"全部同じ"] or dict(rec3[u"字が同じ"]) != dict(rec[u"字が同じ"]):
            out_.append(u"zip の並びが違うと結果が変わる")
        # 断る書類: 知らない形 → 断った・同じとしない・字は同じでない・混ぜ物は作らない・理由は固定の字・元の包みは掛ける(2 回)
        make_doc_zip(os.path.join(docs, "S2DEC.zip"), 1, declined=True)
        r4 = FakeRunner(mv)
        rec4 = ms.process_doc(tool, os.path.join(docs, "S2DEC.zip"), tmp, r4, mixtures=True)
        if not rec4[u"断った"] or rec4[u"断った理由"] != u"知らない属性" or rec4[u"組み直しの 1 回"] is not None or rec4[u"fact が同じ"] or rec4[u"鳴り方が同じ"] or rec4[u"全部同じ"] or rec4[u"タクソノミが同じ"]:
            out_.append(u"知らない形の書類を断らない: %s" % rec4[u"断った理由"])
        if len(r4.calls) != 2:
            out_.append(u"断った書類で組み直した包みを掛けた(か元を掛けていない)")
        if [m[u"作った"] for m in rec4[u"混ぜ物"]] != [False] * 6 or any(m[u"違いを見つけた"] or m[u"鳴り方が違う"] for m in rec4[u"混ぜ物"]) or any(rec4[u"字が同じ"].values()) or any(rec4[u"書き出しが同じ"].values()):
            out_.append(u"断った書類の字が同じ・書き出し・混ぜ物の数え方が違う")
        if rec4[u"元の書き出しの行の数"][u"概念"] != 4 or rec4[u"元の fact の行の数"] != HAND_FACT_ROWS:
            out_.append(u"断った書類でも元の書き出しの行・fact の行の数を数える")
        if rec4[u"組み直しの書き出しの行の数"] is not None or hand_counts_ok(rec4[u"表の数"]) or rec4[u"表の数"][u"要素の宣言"] != 0:
            out_.append(u"断った書類の表の数・組み直しの行の数が違う")
        # 書類 1 本の中の例外も断ったに数える
        orig = ms.build_tables
        ms.build_tables = lambda *a, **k: (_ for _ in ()).throw(ValueError("x"))
        try:
            rec5 = ms.process_doc(tool, zp, tmp, FakeRunner(mv), mixtures=False)
        finally:
            ms.build_tables = orig
        if not rec5[u"断った"] or rec5[u"断った理由"] != u"例外":
            out_.append(u"組む途中の例外を断ったに数えない: %s" % rec5[u"断った理由"])
        # 道具が落ちても使い捨ての場所は残らない
        try:
            ms.process_doc(tool, zp, tmp, FakeRunner(mv, crash_on=3), mixtures=False)
        except RuntimeError:
            pass
        if os.listdir(tmp):
            out_.append(u"途中で落ちたとき使い捨ての場所が残る")
    return out_


class TamperRunner(FakeRunner):
    u"""組み直した包み(``new.zip``)だけ、書き出しを 1 行落とす・指摘の行を 1 つ足す・fact を 1 行落とす、を言う作り物の道具。"""

    def __init__(self, mv_path, cut=None, add_sound=False, drop_fact=False):
        FakeRunner.__init__(self, mv_path)
        self.cut, self.add_sound, self.drop_fact = cut, add_sound, drop_fact

    def __call__(self, cmd, timeout):
        res = FakeRunner.__call__(self, cmd, timeout)
        cmd = strip_seed(cmd)
        if is_tool_call(cmd) and os.path.basename(self.calls[-1]["zip"]) == "new.zip":
            text, to = res
            flags = {u"概念": "--concepts", u"役割型": "--roleTypes", u"表示": "--pre", u"計算": "--cal", u"次元": "--dim"}
            targets = []
            if self.cut in flags and flags[self.cut] in cmd:
                targets.append(cmd[cmd.index(flags[self.cut]) + 1])
            if self.cut == u"ラベルの関係" and "--viewArcrole" in cmd and cmd[cmd.index("--viewArcrole") + 1] == CL:
                targets.append(cmd[cmd.index("--viewFile") + 1])
            if self.cut == u"一般特殊" and "--viewArcrole" in cmd and cmd[cmd.index("--viewArcrole") + 1] == GS:
                targets.append(cmd[cmd.index("--viewFile") + 1])
            if self.drop_fact and "--facts" in cmd:
                targets.append(cmd[cmd.index("--facts") + 1])
            for path in targets:
                with io.open(path, encoding="utf-8", newline="") as fh:
                    rows = list(csv.reader(fh))
                with io.open(path, "w", encoding="utf-8", newline="") as fh:
                    w = csv.writer(fh)
                    for r_ in rows[:-1]:
                        w.writerow(r_)
            if self.add_sound and "--validate" in cmd:
                text = text + u"[EDINET.EC5611W] 足した指摘\n"
            return text, to
        return res


def docmain_problems(ms=None):
    u"""本線の比べ: 組み直した包みの書き出し・fact・鳴り方が元と違うと、``process_doc`` の対応する欄が False になる(元と同じなら True)。書き出し 7 つのどれが違うかも言い当てる。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        zp = os.path.join(d, "S2FAKE01.zip")
        make_doc_zip(zp, 1)
        tool, mv = make_tool(d)
        tmp = os.path.join(d, "tmp")
        os.makedirs(tmp)
        for key in ms.OUTPUT_KEYS:
            rec = ms.process_doc(tool, zp, tmp, TamperRunner(mv, cut=key), mixtures=False)
            same = dict(rec[u"書き出しが同じ"])
            if [k for k in ms.OUTPUT_KEYS if not same[k]] != [key] or rec[u"タクソノミが同じ"] or rec[u"全部同じ"] or not rec[u"fact が同じ"] or not rec[u"鳴り方が同じ"]:
                out_.append(u"書き出し(%s)を 1 行落としたとき、それだけが違うと言わない: %s" % (key, json.dumps(same, ensure_ascii=False)))
        rec = ms.process_doc(tool, zp, tmp, TamperRunner(mv, drop_fact=True), mixtures=False)
        if rec[u"fact が同じ"] or rec[u"全部同じ"] or not rec[u"タクソノミが同じ"] or not rec[u"鳴り方が同じ"]:
            out_.append(u"fact を 1 行落としたのに fact が同じ・全部同じのまま(か、ほかが変わった)")
        rec = ms.process_doc(tool, zp, tmp, TamperRunner(mv, add_sound=True), mixtures=False)
        if rec[u"鳴り方が同じ"] or not rec[u"全部同じ"] or not rec[u"タクソノミが同じ"] or not rec[u"fact が同じ"]:
            out_.append(u"指摘の行を足したのに鳴り方が同じのまま(か、全部同じが鳴り方で決まっている)")
        rec = ms.process_doc(tool, zp, tmp, TamperRunner(mv, cut=u"表示", drop_fact=True, add_sound=True), mixtures=False)
        if rec[u"タクソノミが同じ"] or rec[u"fact が同じ"] or rec[u"鳴り方が同じ"] or rec[u"全部同じ"]:
            out_.append(u"3 つ全部を変えたのにどれかが同じ")
    return out_


def mixtamper_problems(ms=None):
    u"""混ぜ物の「違いを見つけた」「鳴り方が違う」は、混ぜ物の包みの書き出し・fact・鳴り方を元と比べて決まる(混ぜ物の包みの掛け方 A・B の両方を見る)。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        zp = os.path.join(d, "S2FAKE01.zip")
        make_doc_zip(zp, 1)
        tool, mv = make_tool(d)
        tmp = os.path.join(d, "tmp")
        os.makedirs(tmp)

        class SameMix(FakeRunner):
            u"""混ぜ物の包み(``mix0.zip``)でも、元の包みと同じ答えを返す作り物(混ぜ物が効かない道具)。"""

            def __call__(self, cmd, timeout):
                cmd = list(cmd)
                if is_tool_call(cmd):
                    zp_ = cmd[cmd.index("-f") + 1]
                    if os.path.basename(zp_).startswith("mix"):
                        zo = os.path.join(os.path.dirname(zp_), "orig.zip")
                        cmd[cmd.index("-f") + 1] = zo
                return FakeRunner.__call__(self, cmd, timeout)
        rec = ms.process_doc(tool, zp, tmp, SameMix(mv), mixtures=True)
        if any(m[u"違いを見つけた"] or m[u"鳴り方が違う"] for m in rec[u"混ぜ物"]) or not all(m[u"作った"] for m in rec[u"混ぜ物"]):
            out_.append(u"混ぜ物の包みが元と同じ答えなのに違いを見つけたと言う: %s" % [(m[u"種類"], m[u"違いを見つけた"], m[u"鳴り方が違う"]) for m in rec[u"混ぜ物"]])

        class MixBOnly(FakeRunner):
            u"""混ぜ物の包みの掛け方 B(一般特殊)だけ元と違う答えを返す。掛け方 A の答えは元と同じ。"""

            def __call__(self, cmd, timeout):
                cmd = list(cmd)
                if is_tool_call(cmd):
                    zp_ = cmd[cmd.index("-f") + 1]
                    is_mix = os.path.basename(zp_).startswith("mix")
                    if is_mix:
                        cmd[cmd.index("-f") + 1] = os.path.join(os.path.dirname(zp_), "orig.zip")
                    res = FakeRunner.__call__(self, cmd, timeout)
                    if is_mix and "--viewArcrole" in cmd and cmd[cmd.index("--viewArcrole") + 1] == GS:
                        path = cmd[cmd.index("--viewFile") + 1]
                        with io.open(path, "a", encoding="utf-8", newline="") as fh:
                            fh.write(u"extra\r\n")
                    return res
                return FakeRunner.__call__(self, cmd, timeout)
        rec = ms.process_doc(tool, zp, tmp, MixBOnly(mv), mixtures=True)
        if not all(m[u"違いを見つけた"] for m in rec[u"混ぜ物"]) or any(m[u"鳴り方が違う"] for m in rec[u"混ぜ物"]):
            out_.append(u"混ぜ物の包みの掛け方 B だけが違うとき、違いを見つけた(鳴り方は同じ)と言わない: %s" % [(m[u"違いを見つけた"], m[u"鳴り方が違う"]) for m in rec[u"混ぜ物"]])

        class MixFacts(FakeRunner):
            u"""混ぜ物の包みの fact だけ元と違う答え(1 行少ない)を返す。タクソノミ・鳴り方は元と同じ。"""

            def __call__(self, cmd, timeout):
                cmd = list(cmd)
                if is_tool_call(cmd):
                    zp_ = cmd[cmd.index("-f") + 1]
                    is_mix = os.path.basename(zp_).startswith("mix")
                    if is_mix:
                        cmd[cmd.index("-f") + 1] = os.path.join(os.path.dirname(zp_), "orig.zip")
                    res = FakeRunner.__call__(self, cmd, timeout)
                    if is_mix and "--facts" in cmd:
                        path = cmd[cmd.index("--facts") + 1]
                        with io.open(path, encoding="utf-8", newline="") as fh:
                            rows = list(csv.reader(fh))
                        with io.open(path, "w", encoding="utf-8", newline="") as fh:
                            w = csv.writer(fh)
                            for r_ in rows[:-1]:
                                w.writerow(r_)
                    return res
                return FakeRunner.__call__(self, cmd, timeout)
        rec = ms.process_doc(tool, zp, tmp, MixFacts(mv), mixtures=True)
        if not all(m[u"違いを見つけた"] for m in rec[u"混ぜ物"]) or any(m[u"鳴り方が違う"] for m in rec[u"混ぜ物"]):
            out_.append(u"混ぜ物の包みの fact だけが違うとき、違いを見つけた(鳴り方は同じ)と言わない: %s" % [(m[u"違いを見つけた"], m[u"鳴り方が違う"]) for m in rec[u"混ぜ物"]])
    return out_


# ======================================================================== 数え方・道具の確かめ・記録
def ent(declined=False, same=None, facts=True, sound=True, cls=u"走った", fcount=(3, 3, 3, 3, 3, 3), mixes=(), rows=None, tabs=None, reason=u"知らない属性", file_same=None):
    same = same if same is not None else [True] * 7
    keys = MS.OUTPUT_KEYS
    ss = od((k, (False if declined else same[i])) for i, k in enumerate(keys))
    tax = all(ss.values())
    fs = od((k, (False if declined else (file_same[i] if file_same else i < sum(fcount) % 7))) for i, k in enumerate(MS.FILE_KINDS))
    rows = rows or [4] * 7
    t = od([(u"要素の宣言", 0 if declined else 10)] + [(k, od([(u"link", 0 if declined else 2), (u"端", 0 if declined else 5), (u"arc", 0 if declined else 3), (u"ラベルの数", 0 if declined else 1)])) for k in MS.FILE_KINDS[1:]])
    return od([(u"断った", declined), (u"断った理由", reason if declined else u""), (u"表の数", tabs or t), (u"元の書き出しの行の数", od((k, rows[i]) for i, k in enumerate(keys))), (u"元の fact の行の数", 5),
               (u"元の 1 回", od([(u"類", u"走った"), (u"符号ごとの行", {})])), (u"字が同じ", fs), (u"書き出しが同じ", ss), (u"タクソノミが同じ", tax), (u"fact が同じ", False if declined else facts),
               (u"鳴り方が同じ", False if declined else sound), (u"全部同じ", (not declined) and tax and facts), (u"混ぜ物", list(mixes)),
               (u"組み直しの 1 回", None if declined else od([(u"類", cls), (u"符号ごとの行", {})]))])


def mx(made, found, sound, kind=u"表示の arc を抜く"):
    return od([(u"種類", kind), (u"作った", made), (u"違いを見つけた", found), (u"鳴り方が違う", sound)])


def totals_problems(ms=None):
    ms = ms or MS
    out_ = []
    mixes_a = [mx(True, True, False), mx(True, True, True, u"計算の向きを返す"), mx(False, True, True, u"日本語のラベルを変える"), mx(True, False, False, u"英語のラベルを変える"), mx(False, False, False, u"期の型を返す"), mx(True, True, True, u"定義の arc を抜く")]
    mixes_b = [mx(True, True, False), mx(False, False, False, u"計算の向きを返す"), mx(True, True, False, u"日本語のラベルを変える"), mx(True, True, True, u"英語のラベルを変える"), mx(True, True, False, u"期の型を返す"), mx(True, True, False, u"定義の arc を抜く")]
    dev = [ent(mixes=mixes_a, same=[True] * 7, rows=[0, 1, 2, 3, 4, 5, 6]), ent(mixes=mixes_b, same=[True, True, True, True, True, True, False], facts=False)]
    prod = [ent(), ent(declined=True, rows=[1] * 7), ent(same=[True, False, True, True, True, True, True], sound=False, cls=u"止まった"), ent(facts=False, cls=u"走らなかった"), ent(file_same=[True, True, False, False, False, False])]
    per = dev + prod
    t = ms.totals_of(per, 2)
    keys = list(t)
    if keys != [u"開発の 5 本", u"本番だけの 5 本", u"全部", u"混ぜ物", u"混ぜ物の種類ごと"]:
        out_.append(u"集計の群の名・並びが違う: %s" % keys)
        return out_
    p = t[u"本番だけの 5 本"]
    # 本番: 書類 5・断った 1・全部同じ = (ent() = 1)・(ent(file_same..) = 1)・(declined なし) → 全部同じ 2・タクソノミが同じ 3(declined・書き出し 1 つ違うを除く)・fact が同じ 3・鳴り方が同じ 3
    got = (p[u"書類"], p[u"断った書類"], p[u"全部同じ書類"], p[u"タクソノミが同じ書類"], p[u"fact が同じ書類"], p[u"鳴り方が同じ書類"], sum(p[u"組み直した包みの 1 回の類ごと"].values()))
    if got != (5, 1, 2, 3, 3, 3, 4):
        out_.append(u"本番の群の数が手で数えた値と違う: %s" % (got,))
    if dict(p[u"組み直した包みの 1 回の類ごと"]) != {u"走った": 2, u"止まった": 1, u"走らなかった": 1} or dict(p[u"断った理由ごと"]) != {u"知らない属性": 1}:
        out_.append(u"類ごと・断った理由ごとの数が違う")
    if dict(p[u"書き出しごとに同じ書類"]) != {u"概念": 4, u"役割型": 3, u"表示": 4, u"計算": 4, u"次元": 4, u"ラベルの関係": 4, u"一般特殊": 4}:
        out_.append(u"書き出しごとに同じ書類の数が違う: %s" % dict(p[u"書き出しごとに同じ書類"]))
    fl = p[u"字が同じ file"]
    # ent() の既定: file_same[i] = i < sum(fcount) % 7 = i < 18 % 7 = 4 → 4 つ。declined は 0。file_same 指定は 2 つ。本番 5 本: 4 + 0 + 4 + 4 + 2 = 14
    if fl[u"合計"] != 14 or fl[u"分母"] != 30 or dict(fl[u"種類ごと"]) != {"xsd": 4, "cal": 4, "def": 3, "lab": 3, "lab-en": 0, "pre": 0}:
        out_.append(u"字が同じ file の数が手で数えた値と違う: %s" % json.dumps(fl))
    if p[u"元の書き出しの行の数の合計"][u"概念"] != 4 + 1 + 4 + 4 + 4 or p[u"元の概念の行が 1 以下の書類"] != 1 or t[u"開発の 5 本"][u"元の概念の行が 1 以下の書類"] != 1:
        out_.append(u"元の書き出しの行の数の合計・概念の行が 1 以下の書類の数が違う")
    tb = p[u"表の数の合計"]
    if tb[u"要素の宣言"] != 40 or tb["pre"][u"arc"] != 12 or tb["lab"][u"ラベルの数"] != 4 or tb["cal"][u"link"] != 8:
        out_.append(u"表の数の合計が違う: %s" % json.dumps(tb, ensure_ascii=False))
    dv = t[u"開発の 5 本"]
    if (dv[u"書類"], dv[u"全部同じ書類"], dv[u"断った書類"], dv[u"fact が同じ書類"]) != (2, 1, 0, 1) or t[u"全部"][u"書類"] != 7 or t[u"全部"][u"断った書類"] != 1:
        out_.append(u"開発の群・全部の数が違う: %s" % ((dv[u"書類"], dv[u"全部同じ書類"], dv[u"断った書類"], dv[u"fact が同じ書類"]),))
    m = t[u"混ぜ物"]
    # 12 枠・作れた 8(a: 4・b: 5 → 9 ではなく a: 1,1,0,1,0,1 = 4・b: 1,0,1,1,1,1 = 5 で 9)・違いを見つけた(a: 3・b: 5 = 8)・鳴り方が違う(a: 2・b: 1 = 3)
    if dict(m) != {u"混ぜ物の数": 12, u"作れた数": 9, u"違いを見つけた数": 8, u"鳴り方が違う数": 3}:
        out_.append(u"混ぜ物の合計が手で数えた値と違う(作れなかった混ぜ物を数えない): %s" % dict(m))
    mk = t[u"混ぜ物の種類ごと"]
    if list(mk) != list(ms.MIX_KINDS) or dict(mk[u"表示の arc を抜く"]) != {u"作れた": 2, u"違いを見つけた": 2, u"鳴り方が違う": 0} or dict(mk[u"計算の向きを返す"]) != {u"作れた": 1, u"違いを見つけた": 1, u"鳴り方が違う": 1} or dict(mk[u"日本語のラベルを変える"]) != {u"作れた": 1, u"違いを見つけた": 1, u"鳴り方が違う": 0}:
        out_.append(u"混ぜ物の種類ごとの数が違う: %s" % json.dumps(mk, ensure_ascii=False))
    j = ms.judged(t, 7)
    jv = list(j.values())
    if (jv[0][u"書類"], jv[0][u"分母"], jv[1][u"書類"], jv[2][u"書類"], jv[3][u"file"], jv[3][u"分母"], jv[4][u"個"], jv[4][u"分母"], jv[5][u"個"], jv[5][u"分母"], jv[6][u"個"], jv[6][u"分母"]) != (2, 5, 1, 3, 14, 30, 9, 12, 8, 9, 3, 9):
        out_.append(u"予測の判定に要る数が手で数えた値と違う: %s" % [dict(x) if isinstance(x, dict) else x for x in jv])
    if [k[:5] for k in j] != [u"XT0-1", u"XT0-2", u"XT0-3", u"XT0-4", u"XT0-5", u"XT0-6", u"XT0-7"]:
        out_.append(u"判定の鍵の並びが違う")
    return out_


def tools_problems(ms=None):
    ms = ms or MS
    out_ = []
    wp = hashlib.sha256(MV_P).hexdigest()
    with Temp() as d:
        tool, mv = make_tool(d)
        r = FakeRunner(mv)
        seen = []
        info = ms.check_tool(tool, r, lambda path: (seen.append(path), read_bytes_sha(path))[1], want_sha=wp)
        if len(seen) != 1 or not seen[0].endswith("/ModelValue.py"):
            out_.append(u"sha256 を読む file が ModelValue.py でない: %s" % seen)
        if (info[u"版"], info[u"ModelValue.py の sha256"], info[u"Python の版"]) != (u"2.47.5", wp, u"Python 3.11.17") or info[u"package の一覧の sha256"] != hashlib.sha256(FREEZE.encode("utf-8")).hexdigest():
            out_.append(u"道具の情報が違う: %s" % dict(info))
        if stops(ms, ms.check_tool, tool, r, want_sha=wp, want_version=u"2.47.5") or not stops(ms, ms.check_tool, tool, r, want_sha=wp, want_version=u"2.47.6"):
            out_.append(u"版が違うとき止まらない(か合うとき止まる)")
        if not stops(ms, ms.check_tool, tool, FakeRunner(mv, freeze=u"arelle-release==2.40.0\n"), want_sha=wp):
            out_.append(u"道具の版が 2.47.5 でないのに止まらない")
        if not stops(ms, ms.check_tool, tool, r, want_sha=u"0" * 64):
            out_.append(u"ModelValue.py の sha256 が封と違うのに止まらない")
        if not stops(ms, ms.check_tool, tool, r):
            out_.append(u"封の sha256(既定)と違うのに止まらない")
        if not stops(ms, ms.check_tool, os.path.join(d, "none"), r, want_sha=wp):
            out_.append(u"道具の場所が無いのに止まらない")
    return out_


def dev_docs_problems(ms=None):
    u"""開発の入口は 5 本だけ: 7 本以上の zip で ``dev_docs`` は 5 本を選んだ所で止まり、6 本目を開かない(``zipfile.ZipFile`` を数える)。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        for i in range(1, 8):
            make_doc_zip(os.path.join(d, "S2FAKE0%d.zip" % i), i)
        opened = []
        bz = sys.modules[ms.BUILD_NAME].zipfile
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
        if [g[0] for g in got] != [u"S2FAKE0%d" % i for i in range(1, 6)] or [g[0] for g in got_default] != [u"S2FAKE0%d" % i for i in range(1, 6)]:
            out_.append(u"開発の 5 本が並びの頭の 5 本でない: %s" % [g[0] for g in got])
        if opened != [u"S2FAKE0%d.zip" % i for i in range(1, 6)] * 2:
            out_.append(u"開いた zip が並びの頭の 5 本だけでない: %s" % opened)
        if ms.DEV_COUNT != 5 or ms.dev_docs.__defaults__ != (5,):
            out_.append(u"dev_docs の既定の本数が 5 でない")
    return out_


def record_args(d, ms, runner=None, count=3, **kw):
    docs = os.path.join(d, "docs")
    os.makedirs(docs)
    make_docs(docs, count)
    tool, mv = make_tool(os.path.join(d, "tool"))
    tmp = os.path.join(d, "tmp")
    os.makedirs(tmp)
    runner = runner or FakeRunner(mv)
    args = dict(want=count, runner=runner, tmp_root=tmp, want_sha=hashlib.sha256(MV_P).hexdigest(), dev_count=1)
    args.update(kw)
    return tool, docs, runner, tmp, args


def run_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms)
        rec, secret = ms.build_record(tool, docs, **args)
        # 1 本目は混ぜ物つきで 16 回・2 本目と 3 本目は 4 回ずつ
        if len(runner.calls) != 16 + 4 + 4:
            out_.append(u"道具の呼び出しの数が違う(開発の 1 本は混ぜ物つき 16 回、残りは 4 回ずつ): %d" % len(runner.calls))
        mat = rec[u"材料"]
        if (mat[u"書類の本数"], mat[u"書類の file 名の並びの sha256"], mat[u"開発の 5 本の番号"], mat[u"道具の版"], mat[u"道具 P の ModelValue.py の sha256"], mat[u"Python の版(道具 P)"], mat[u"規則の年"], mat[u"時間の上限(秒)"], mat[u"混ぜ物の種類"]) != (
                3, ORDER_SHA, [1], u"2.47.5", hashlib.sha256(MV_P).hexdigest(), u"Python 3.11.17", u"EDINET-2026", 600, list(ms.MIX_KINDS)):
            out_.append(u"材料の欄が手で数えた値と違う: %s" % dict(mat))
        if [dd[u"番号"] for dd in rec[u"書類"]] != [1, 2, 3] or [len(dd[u"混ぜ物"]) for dd in rec[u"書類"]] != [6, 0, 0]:
            out_.append(u"書類の番号・混ぜ物の置き場所が違う(混ぜ物は開発の本数だけ)")
        t = rec[u"集計"]
        if (t[u"開発の 5 本"][u"書類"], t[u"本番だけの 2 本"][u"書類"], t[u"全部"][u"全部同じ書類"], t[u"混ぜ物"][u"混ぜ物の数"], t[u"混ぜ物"][u"作れた数"]) != (1, 2, 3, 6, 6):
            out_.append(u"集計が手で数えた値と違う")
        text = ms.dumps(rec)
        for leak in STEMS + [u"E9999", u"S2OTHER1", u".xbrl", u".htm", u".xsd", u"audit", u"Alpha", u"Beta", u"Gamma", u"jppfs", u"http", u"冗長", u"売上", u"Sales", u"x_pre", u"role/a"]:
            if leak in text:
                out_.append(u"記録に材料の字が在る: %s" % leak)
        if set(secret[3]) != set([u"E9999%d" % i for i in (1, 2, 3)]) or list(secret[2]) != STEMS or not {"Alpha", "Gamma", "BetaHeading"} <= set(secret[1]) or u"冗長" in secret[0] or TXT1 not in secret[0] or u"Sales" not in secret[0]:
            out_.append(u"secret の docID・EDINET コード・要素の名・ラベルの字が違う(ラベルの字は 5 字以上だけ): %s" % sorted(secret[0]))
        if os.listdir(tmp):
            out_.append(u"使い捨ての場所が残っている")
        r2 = FakeRunner(runner.mv_path)
        a2 = dict(args)
        a2["want"] = 67
        a2["runner"] = r2
        if not stops(ms, ms.build_record, tool, docs, **a2) or r2.calls:
            out_.append(u"書類が 67 本でないのに止まらない(か掛けた)")
        r3 = FakeRunner(runner.mv_path)
        a3 = dict(args, runner=r3, want_sha=u"0" * 64)
        if not stops(ms, ms.build_record, tool, docs, **a3) or r3.calls:
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
            (u"書類ごとの fact が同じを変える(合計と合わない)", lambda r: r[u"書類"][0].__setitem__(u"fact が同じ", False)),
            (u"書類ごとの鳴り方を変える", lambda r: r[u"書類"][1].__setitem__(u"鳴り方が同じ", False)),
            (u"書類を 1 本消す", lambda r: r[u"書類"].pop()),
            (u"書類の番号を変える", lambda r: r[u"書類"][0].__setitem__(u"番号", 7)),
            (u"材料の書類の本数だけを変える", lambda r: r[u"材料"].__setitem__(u"書類の本数", 5)),
            (u"欄を消す", lambda r: r[u"書類"][0].pop(u"元の 1 回")),
            (u"類の字が違う", lambda r: r[u"書類"][0][u"元の 1 回"].__setitem__(u"類", u"壊れた")),
            (u"断ったのに組み直しの 1 回が在る", refresh_after(lambda r: r[u"書類"][1].__setitem__(u"断った", True))),
            (u"断っていないのに理由が在る", refresh_after(lambda r: r[u"書類"][1].__setitem__(u"断った理由", u"知らない属性"))),
            (u"断ったのに全部同じ", refresh_after(lambda r: (r[u"書類"][1].__setitem__(u"断った", True), r[u"書類"][1].__setitem__(u"組み直しの 1 回", None)))),
            (u"混ぜ物を本番の書類に置く", refresh_after(lambda r: r[u"書類"][1].__setitem__(u"混ぜ物", [od([(u"種類", k), (u"作った", True), (u"違いを見つけた", True), (u"鳴り方が違う", True)]) for k in ms.MIX_KINDS]))),
            (u"混ぜ物の種類を変える", refresh_after(lambda r: r[u"書類"][0][u"混ぜ物"][0].__setitem__(u"種類", u"消す"))),
            (u"作れなかった混ぜ物に違いを見つけたが付く", refresh_after(lambda r: r[u"書類"][0][u"混ぜ物"][0].update({u"作った": False, u"違いを見つけた": True}))),
            (u"字が同じの種類の並びを変える", refresh_after(lambda r: r[u"書類"][0].__setitem__(u"字が同じ", od(reversed(list(r[u"書類"][0][u"字が同じ"].items())))))),
            (u"書き出しが同じの欄の 1 つが違うのにタクソノミが同じのまま", refresh_after(lambda r: r[u"書類"][0][u"書き出しが同じ"].__setitem__(u"表示", False))),
            (u"全部同じが fact が同じと合わない", refresh_after(lambda r: r[u"書類"][0].__setitem__(u"fact が同じ", False))),
            (u"判定の数を変える", lambda r: [r[k] for k in r if k.startswith(u"予測の判定に要る数")][0].__setitem__(u"XT0-1 全部同じ書類", 99))]
        for what, fn in tampers:
            r2 = json.loads(base, object_pairs_hook=od)
            fn(r2)
            if ms.dumps(r2) == base or not stops(ms, ms.verify_record, r2, None, 3, 1):
                out_.append(u"記録を変えても検査が止まらない: %s" % what)
    return out_


def clean_problems(ms=None):
    ms = ms or MS
    out_ = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"断った理由", u"知らない属性"), (u"材料の sha256", u"a" * 64)])])])
    secret = ({u"長めのラベルの字"}, {u"NetSalesOfX"}, [u"zzdoc"], {u"E99991"}, {u"[EDINET.EC5611W] ある指摘の行の本文"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out_.append(u"きれいな記録で止まる")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"company", 1)])), (u"禁止の欄(label)", od([(u"label", 1)])), (u"禁止の欄(element)", od([(u"element", 1)])),
        (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])),
        (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])),
        (u"file の名(xsd)", od([(u"x", u"jpcrp030000-asr-001.xsd")])), (u"file の名(xml)", od([(u"x", u"a_pre.xml")])), (u"file の名(PublicDoc)", od([(u"x", u"XBRL/PublicDoc/x")])),
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
        w = os.path.join(d, "w.json")
        ms.write_exclusive = lambda path, data: orig(path, b"{}")
        try:
            stopped = stops(ms, ms.write_record, w, bad)
        finally:
            ms.write_exclusive = orig
        if not stopped:
            out_.append(u"書く前の検査が止めない(書いた後の検査だけで止まっている)")
    return out_


def e2e_problems(ms=None):
    u"""``run`` → 記録 → ``--check`` を作り物の置き場と道具で通す(置き場も道具も開かない)。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms)
        rp = os.path.join(d, "rec", "r.json")
        kw = dict(docs=docs, out=rp, runner=runner, tmp_root=tmp, say=lambda *a: None, want_sha=args["want_sha"], dev_count=1)
        if not stops(ms, ms.run, tool, want=67, **kw) or os.path.exists(rp):
            out_.append(u"書類が 67 本でないのに run が止まらない(か記録を書いた)")
        rec = ms.run(tool, want=3, **kw)
        if not os.path.exists(rp) or ms.dumps(rec) != read_text(rp):
            out_.append(u"記録が書かれていない・字が違う")
        if not stops(ms, ms.run, tool, want=3, **kw):
            out_.append(u"記録が既に在るのに run が止まらない")
        ms.check(rec_path=rp, want=3, say=lambda *a: None, dev_count=1)
        rp2 = os.path.join(d, "rec", "r2.json")
        kw2 = dict(kw, out=rp2, runner=FakeRunner(runner.mv_path), want_sha=u"0" * 64)
        if not stops(ms, ms.run, tool, want=3, **kw2) or os.path.exists(rp2):
            out_.append(u"道具の sha256 が違うのに記録を書いた")
    return out_


def devrun_problems(ms=None):
    u"""開発の入口(``dev_run``): 置き場の並びの頭の本数だけを掛け、記録は書かない。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms, count=7)
        lines = []
        saved = ms.check_tool
        ms.check_tool = lambda t, r=None, *a, **k: saved(t, r, sha_reader=ms.sha256_file, want_sha=hashlib.sha256(MV_P).hexdigest())
        try:
            per = ms.dev_run(tool, docs_dir=docs, runner=runner, tmp_root=tmp, say=lines.append)
        finally:
            ms.check_tool = saved
        if len(per) != 5 or len(runner.calls) != 5 * 16 + 0 or os.path.exists(os.path.join(d, "rec")):
            out_.append(u"開発の入口が 5 本だけ(混ぜ物つき 16 回ずつ)掛けていない: %d 本・%d 回" % (len(per), len(runner.calls)))
        if len(lines) != 6 or not lines[0].startswith(u"doc 1(") or u"全部同じ=True" not in lines[0] or not lines[-1].startswith(u"開発の 5 本の合計"):
            out_.append(u"開発の入口の出力の形が違う: %s" % lines[:1])
    return out_


# ======================================================================== 7. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "copy", "csv", "importlib", "io", "json", "os", "re", "shutil", "sys", "tempfile", "time", "xml")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "adapters", "core", "audit_core", "subprocess", "zipfile")
#: 前の便の script の関数を呼ぶ(写さない): (module の名, 関数の名)
CALLED = (("W", "select_docs"), ("W", "order_sha256"), ("V", "count_one"), ("V", "exec_cmd"), ("V", "check_clean"), ("V", "CLASSES"), ("V", "EXE_REL"),
          ("B", "load_package"), ("B", "write_package"), ("B", "read_rows"), ("B", "facts_same"), ("B", "sounds_same"), ("B", "check_tool"), ("B", "dev_docs"))
NOT_COPIED = ("select_docs", "order_sha256", "doc_xsd_names", "sha256_file", "codes_of", "run_class", "count_one", "command", "exec_cmd", "tool_info", "strip_copy", "is_envelope", "is_e_code",
              "load_package", "write_package", "read_rows", "facts_same", "sounds_same", "is_public_htm", "run_tool")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
#: 別の門の規準の字(関数の名・呼び出しに使わない)
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
#: 組む部品の仲間(これらの関数の本体は、元の字・包み・zip・file を読む名前を使わない)
BUILD_FUNCS = ("build_xsd", "build_linkbase", "build_tables", "esc_text", "esc_attr", "prefix_for", "assign_prefixes", "qname_text", "open_attrs")
BUILD_FORBIDDEN_NAMES = ("load_package", "zipfile", "open", "io", "os", "ET", "strip_xsd", "strip_linkbase", "strip_tables", "parse_xml", "find_files", "process_doc", "entries", "data", "files",
                         "zip_path", "csv", "read_table_rows", "package_with", "text_of", "check_blank", "resolve_qname", "B", "V", "W", "orig_by")
BUILD_ONLY_CALLERS = ("build_xsd", "build_linkbase", "build_tables")


def build_isolation_problems(src=None):
    u"""組む部品は表 S・表 K だけを引数に取り、元の字・包み・zip を読まない。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    funcs = dict((n.name, n) for n in tree.body if isinstance(n, ast.FunctionDef))
    out_ = []
    for nm, args in (("build_xsd", ["S"]), ("build_linkbase", ["K"]), ("build_tables", ["tables"])):
        f = funcs.get(nm)
        if f is None or [a.arg for a in f.args.args] != args or f.args.vararg or f.args.kwarg or f.args.kwonlyargs or f.args.defaults:
            out_.append(u"%s の引数が (%s) だけでない" % (nm, ", ".join(args)))
    for nm in BUILD_FUNCS:
        f = funcs.get(nm)
        if f is None:
            out_.append(u"組む部品の関数が無い: %s" % nm)
            continue
        names = set(n.id for n in ast.walk(f) if isinstance(n, ast.Name))
        bad = sorted(names & set(BUILD_FORBIDDEN_NAMES))
        if bad:
            out_.append(u"組む部品 %s が元の字・包み・file を読む名前を使っている: %s" % (nm, bad))
        attrs = [(n.value.id, n.attr) for n in ast.walk(f) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
        if any(v in ("os", "zipfile", "io", "csv", "ET", "B", "V", "W") for v, _a in attrs):
            out_.append(u"組む部品 %s が os・zipfile・io・ElementTree・前の便の script を使っている" % nm)
    # 組む部品の呼び出しは表だけを渡す(元の字・file を渡さない)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in BUILD_ONLY_CALLERS]
    for c in calls:
        a0 = c.args[0] if len(c.args) == 1 else None
        sub_ok = isinstance(a0, ast.Subscript) and isinstance(a0.value, ast.Name) and a0.value.id == "tables"
        if len(c.args) != 1 or c.keywords or not ((isinstance(a0, ast.Name) and a0.id in ("S", "K", "T", "tables")) or sub_ok):
            out_.append(u"%s の呼び出しが表以外を渡している" % c.func.id)
    callers = set()
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            for c in ast.walk(n):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in BUILD_ONLY_CALLERS:
                    callers.add((n.name, c.func.id))
    if not {("process_doc", "build_tables"), ("process_doc", "build_xsd"), ("process_doc", "build_linkbase")} <= callers:
        out_.append(u"process_doc が組む部品を呼んでいない: %s" % sorted(callers))
    # process_doc の中で build_tables に渡す名は、剥がした表(tables)の名
    pd = funcs.get("process_doc")
    for c in [n for n in ast.walk(pd) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "build_tables"] if pd else []:
        if [getattr(a, "id", None) for a in c.args] != ["tables"]:
            out_.append(u"process_doc が build_tables に tables 以外を渡している")
    # zip を開く所は script の中に無い(前の便の load_package・dev_docs が読む)
    if any(isinstance(n, ast.Name) and n.id == "zipfile" for n in ast.walk(tree)):
        out_.append(u"script が zipfile を使っている(置き場の zip は前の便の関数が読む)")
    # ElementTree を使う所は parse_xml だけ(組む部品・比べる部品は使わない)
    users = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and any(isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "ET" for x in ast.walk(n))]
    if sorted(users) != ["parse_xml"]:
        out_.append(u"ElementTree を使う関数が parse_xml だけでない: %s" % users)
    return out_


def import_problems(src=None):
    u"""script の import は標準ライブラリと importlib だけ(engine を読まない・subprocess を持たない)。前の便の script は B・V・W から呼び写さない。"""
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
            out_.append(u"前の便の %s を %s から呼んでいない" % (fn, mod))
    funcs = set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in NOT_COPIED:
        if fn in funcs:
            out_.append(u"前の便の %s を script が自分で定義している(写している)" % fn)
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    if BUILD_NAME not in consts:
        out_.append(u"便 XB0 の script を読む名が一意の名(%s)でない" % BUILD_NAME)
    if not any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "V" for t in n.targets) and isinstance(n.value, ast.Attribute) and n.value.attr == "V" for n in tree.body):
        out_.append(u"便 XV0 の script を便 XB0 の script の V から受けていない")
    if not any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "W" for t in n.targets) and isinstance(n.value, ast.Attribute) and n.value.attr == "W" for n in tree.body):
        out_.append(u"便 XG0 の script を便 XB0 の script の W から受けていない(Stop の型が 2 つになる)")
    if any(n in consts for n in (u"_xv0_tag_wall_2026_11_21", u"_xg1_tag_wall_2026_11_21", u"_xb0_tag_wall_2026_11_21", u"_xb0_tag_narrow", u"_xb0_edinet_validate_2026_11_21", u"_xb0_inline_build_2026_11_21")):
        out_.append(u"他の便と重なる名で読んでいる")
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            if u".env" in n.value or u"dotenv" in n.value or u"API_KEY" in n.value:
                out_.append(u"鍵・.env の字が在る")
    # 別の門の規準の字を使わない(関数の名・呼び出し・説明文のどこにも)
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
    # ---- 剥がす(表 S)
    (u"T1 根の既定の属性を持たない", u'S = od([("target", root["attrs"]["targetNamespace"]), ("defaults", od((k, root["attrs"][k]) for k in ("attributeFormDefault", "elementFormDefault") if k in root["attrs"])),',
     u'S = od([("target", root["attrs"]["targetNamespace"]), ("defaults", od()),', ("strip", "build")),
    (u"T2 import の並びを逆に持つ", u'S["imports"].append((c["attrs"]["namespace"], c["attrs"]["schemaLocation"]))', u'S["imports"].insert(0, (c["attrs"]["namespace"], c["attrs"]["schemaLocation"]))', ("strip", "build")),
    (u"T3 linkbaseRef の arcrole を持たない", u'("arcrole", r["attrs"].get(XLINK_KEYS["arcrole"]))', u'("arcrole", None)', ("strip", "doc")),
    (u"T4 QName の値を名前空間に解かない", u'e[k] = resolve_qname(v, c["scope"]) if k in XSD_QNAME_ATTRS else v', u"e[k] = v", ("strip", "build")),
    (u"T5 annotation が 2 つ以上でも断らない", u'if annotations > 1 or c["attrs"] or len(c["children"]) != 1', u'if c["attrs"] or len(c["children"]) != 1', ("decline",)),
    (u"T6 要素の知らない属性を断らない", u"            only_attrs(c, XSD_ELEMENT_ATTRS)\n", u"            pass\n", ("decline",)),
    (u"T7 根の知らない属性を断らない", u"    only_attrs(root, XSD_ROOT_ATTRS)\n", u"    pass\n", ("decline",)),
    (u"T8 解けない接頭辞を断らない", u'        if uri is None:\n            raise Decline(u"解けない接頭辞")\n', u"        if uri is None:\n            uri = u\"\"\n", ("decline",)),
    (u"T9 QName の : が 2 つを断らない", u'    if v.count(":") > 1 or not v:\n        raise Decline(u"QName の形が知らない形")\n', u'    if not v:\n        raise Decline(u"QName の形が知らない形")\n', ("decline",)),
    (u"T10 import の namespace が無いのを断らない", u'if "namespace" not in c["attrs"] or "schemaLocation" not in c["attrs"] or c["children"]:', u'if "schemaLocation" not in c["attrs"] or c["children"]:', ("decline",)),
    # ---- 剥がす(表 K)
    (u"T11 loc の知らない属性を断らない", u'            only_attrs(c, (XLINK_KEYS["type"], XLINK_KEYS["href"], XLINK_KEYS["role"], XLINK_KEYS["label"]))\n', u"            pass\n", ("decline",)),
    (u"T12 端の無い xlink:label を指す arc を断らない", u'        if not froms or not tos:\n            raise Decline(u"端の無い xlink:label を指す arc")\n', u"", ("decline",)),
    (u"T13 端の組の開き方の順を逆にする", u"        for f in froms:\n            for t in tos:\n", u"        for t in tos:\n            for f in froms:\n", ("strip",)),
    (u"T14 arc の位置(before)を持たない", u'("from", f), ("to", t), ("before", before),', u'("from", f), ("to", t), ("before", 0),', ("strip", "build", "doc")),
    (u"T15 label の中身の字の前後の空白を落とす", u'("id", c["attrs"].get("id")), ("text", text_of(c))])', u'("id", c["attrs"].get("id")), ("text", text_of(c).strip())])', ("strip", "build")),
    (u"T16 loc の role を持たない", u'("kind", "loc"), ("href", c["attrs"][XLINK_KEYS["href"]]), ("role", c["attrs"].get(XLINK_KEYS["role"]))', u'("kind", "loc"), ("href", c["attrs"][XLINK_KEYS["href"]]), ("role", None)', ("strip", "build")),
    (u"T17 label の id を持たない", u'("id", c["attrs"].get("id"))', u'("id", None)', ("strip", "build")),
    (u"T18 label の言語を持たない", u'("kind", "label"), ("lang", c["attrs"].get(XML_LANG))', u'("kind", "label"), ("lang", None)', ("strip", "build")),
    (u"T19 arc のそのほかの属性を持たない", u'extra = od((k, a[k]) for k in ARC_ATTR_ORDER if k in a)', u"extra = od()", ("strip", "build", "doc")),
    (u"T20 拡張 link の role を持たない", u'return od([("tag", local), ("role", node["attrs"].get(XLINK_KEYS["role"])), ("ends", ends), ("arcs", arcs)])', u'return od([("tag", local), ("role", None), ("ends", ends), ("arcs", arcs)])', ("strip", "build")),
    (u"T21 roleRef の URI を持たない", u'("uri", c["attrs"][REF_TAGS[local]])', u'("uri", u"")', ("strip", "build")),
    (u"T22 file が 1 つずつでないのを断らない", u"    if any(len(v) != 1 for v in found.values()):", u"    if False:", ("decline",)),
    (u"T23 PublicDoc の直下だけを見ない", u'if not n.startswith(PUBLICDOC) or "/" in n[len(PUBLICDOC):]:', u"if not n.startswith(PUBLICDOC):", ("decline",)),
    (u"T24 剥がす途中の例外を断らない", u'            raise Decline(u"剥がす途中の例外")', u"            out[k] = None", ("decline",)),
    (u"T25 DOCTYPE を断らない", u'    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:\n        raise Decline(u"DOCTYPE か実体宣言")\n', u"", ("decline",)),
    (u"T26 XML 宣言の encoding を見ない", u'    if m and m.group(1).lower() != b"utf-8":\n        raise Decline(u"知らない文字の符号化")\n', u"", ("decline",)),
    (u"T27 UTF-16 の BOM を断らない", u'    if data[:2] in (b"\\xff\\xfe", b"\\xfe\\xff") or data[:4] in (b"\\xff\\xfe\\x00\\x00", b"\\x00\\x00\\xfe\\xff"):\n        raise Decline(u"知らない文字の符号化")\n', u"", ("decline",)),
    (u"T28 子の後ろの字を見ない", u'        if (c["elem"].tail or u"").strip():', u"        if False:", ("decline",)),
    (u"T29 中身の字を見ない", u"    if text_of(node).strip():", u"    if False:", ("decline",)),
    (u"T31 arc の type を見ない", u'            if c["attrs"].get(XLINK_KEYS["type"]) != "arc" or not all(', u'            if not all(', ("decline",)),
    (u"T32 BOM を読めない(BOM を除かない)", u'    body = data[3:] if data[:3] == b"\\xef\\xbb\\xbf" else data\n', u"    body = data\n", ("decline",)),
    # ---- 組む
    (u"B1 提出者の接頭辞の字の決め(- を _ にする)", u'return u"%s-%s_%s" % (m.group(1), m.group(2), m.group(3))', u'return u"%s_%s_%s" % (m.group(1), m.group(2), m.group(3))', ("build", "doc")),
    (u"B2 最後の path の字を接頭辞にしない", u'    if NCNAME_RE.match(last) and not last.lower().startswith("xml"):', u"    if False:", ("build",)),
    (u"B3 重なった接頭辞を直さない", u"        while p in used:", u"        while False:", ("build",)),
    (u"B4 固定の接頭辞を取っておかない", u"    used = set(FIXED_PREFIX.values())", u"    used = set()", ("build",)),
    (u"B5 属性の値の引用符を実体参照にしない", u""".replace('"', "&quot;")""", u"", ("build",)),
    (u"B6 本文の > を実体参照にしない", u'''    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\\r", "&#13;")''', u'''    return s.replace("&", "&amp;").replace("<", "&lt;").replace("\\r", "&#13;")''', ("build",)),
    (u"B7 本文の復帰を実体参照にしない", u'''.replace(">", "&gt;").replace("\\r", "&#13;")''', u'''.replace(">", "&gt;")''', ("build",)),
    (u"B8 xbrldt を使わなくても宣言する", u"    uses_dt = any(k.startswith(", u"    uses_dt = True or any(k.startswith(", ("build",)),
    (u"B9 端の xlink:label の番号をずらす", u'+ [(u"xlink:label", u"L%d" % i)]', u'+ [(u"xlink:label", u"L%d" % (i + 1))]', ("build",)),
    (u"B10 arc の属性を昇順に書く", u"            for k in ARC_ATTR_ORDER:\n                if k in a[\"attrs\"]:", u"            for k in sorted(ARC_ATTR_ORDER):\n                if k in a[\"attrs\"]:", ("build",)),
    (u"B11 端を全部先に書く", u'            lines.extend(end_lines[done:a["before"]])\n', u"", ("build", "doc")),
    (u"B12 arc の位置の検査を外す", u'            if not (done <= a["before"] <= len(L["ends"])):\n                raise Decline(u"arc の位置が合わない")\n', u"", ("decline",)),
    (u"B13 arc の端の番号の検査を外す", u'            if not (0 <= a["from"] < len(L["ends"]) and 0 <= a["to"] < len(L["ends"])):\n                raise Decline(u"arc の端の番号が合わない")\n', u"", ("decline",)),
    (u"B14 組む部品が arc の知らない属性を断らない", u'            if set(a["attrs"]) - set(ARC_ATTR_ORDER):\n                raise Decline(u"知らない属性")\n', u"", ("decline",)),
    (u"B15 組む部品が知らない拡張 link を断らない", u'        if L["tag"] not in LINK_TAGS:\n            raise Decline(u"知らない拡張 link")\n', u"", ("decline",)),
    (u"B16 組む部品が知らない ref を断らない", u'        if r["tag"] not in REF_TAGS:\n            raise Decline(u"知らない ref")\n', u"", ("decline",)),
    (u"B17 組む部品(xsd)が知らない属性を断らない", u'    if unknown:\n        raise Decline(u"知らない属性")\n', u"", ("decline",)),
    (u"B18 要素の宣言の属性の並びを替える", u'XSD_ELEMENT_ATTRS = ("id", XSD_KEY_BALANCE, XSD_KEY_PERIOD, "abstract", "name",', u'XSD_ELEMENT_ATTRS = ("name", XSD_KEY_BALANCE, XSD_KEY_PERIOD, "abstract", "id",', ("build",)),
    (u"B19 組んだ字に BOM を付ける", u'            out[k] = (build_xsd(tables[k]) if k == "xsd" else build_linkbase(tables[k])).encode("utf-8")', u'            out[k] = (build_xsd(tables[k]) if k == "xsd" else build_linkbase(tables[k])).encode("utf-8-sig")', ("build",)),
    (u"B20 xsd の XML 宣言の版を変える", u"""lines = [u'<?xml version="1.0" encoding="utf-8"?>', u"<xsd:schema%s>" % open_attrs(root_attrs)]""", u"""lines = [u'<?xml version="1.1" encoding="utf-8"?>', u"<xsd:schema%s>" % open_attrs(root_attrs)]""", ("build",)),
    (u"B21 組む途中の例外を断らない", u'            raise Decline(u"組む途中の例外")', u"            raise", ("decline",)),
    (u"B22 import を組まない", u'    for ns, loc in S["imports"]:\n', u'    for ns, loc in []:\n', ("build",)),
    (u"B23 linkbaseRef の role を落とす", u'            if r["role"] is not None:\n                pairs.append((u"xlink:role", r["role"]))\n', u"", ("build",)),
    (u"B24 要素の QName の接頭辞を付けない", u"    return u\"%s:%s\" % (prefixes[ns], local) if ns else local", u"    return local", ("build",)),
    (u"B25 目的の名前空間の宣言を落とす", u'    root_attrs = decls + [(k, v) for k, v in S["defaults"].items()] + [(u"targetNamespace", S["target"])]', u'    root_attrs = [d for d in decls if d[1] != S["target"]] + [(k, v) for k, v in S["defaults"].items()] + [(u"targetNamespace", S["target"])]', ("build",)),
    (u"B26 label の言語を組まない", u'                if e["lang"] is not None:\n                    pairs.append((u"xml:lang", e["lang"]))\n', u"", ("build",)),
    (u"B27 label の id を組まない", u'                if e["id"] is not None:\n                    pairs.append((u"id", e["id"]))\n', u"", ("build",)),
    (u"B28 loc の role を組まない", u'+ ([(u"xlink:role", e["role"])] if e["role"] is not None else []) + [(u"xlink:label", u"L%d" % i)]', u'+ [(u"xlink:label", u"L%d" % i)]', ("build",)),
    (u"B29 拡張 link の role を組まない", u'open_attrs([(u"xlink:type", u"extended")] + ([(u"xlink:role", L["role"])] if L["role"] is not None else []))', u'open_attrs([(u"xlink:type", u"extended")])', ("build",)),
    # ---- 混ぜ物
    (u"X1 M1 の当て先を計算の表にする", u'        kind, at = "pre", first_arc(tables["pre"])', u'        kind, at = "cal", first_arc(tables["pre"])', ("mix",)),
    (u"X2 M2 が常に -1 にする", u'        a["attrs"]["weight"] = "-1" if w == "1" else "1"', u'        a["attrs"]["weight"] = "-1"', ("mix",)),
    (u"X3 M2 が 1 でも -1 でもない weight でも作る", u'        if w not in ("1", "-1"):\n            return None\n', u"", ("mix",)),
    (u"X4 M3 が字の後ろに Y を足す", u'        T["links"][li]["ends"][ei]["text"] += u"X"', u'        T["links"][li]["ends"][ei]["text"] += u"Y"', ("mix",)),
    (u"X5 M5 が常に instant にする", u'        e[XSD_KEY_PERIOD] = "instant" if p == "duration" else "duration"', u'        e[XSD_KEY_PERIOD] = "instant"', ("mix",)),
    (u"X6 M5 が abstract の値を問わず最初の要素に当てる", u'        at = next((i for i, e in enumerate(tables["xsd"]["elements"]) if e.get("abstract") == "false"), None)', u'        at = 0', ("mix",)),
    (u"X7 M6 が arc を除かず最初の arc を足す", u'    if idx in (0, 5):\n        li, ai = at\n        del T["links"][li]["arcs"][ai]\n', u'    if idx in (0, 5):\n        li, ai = at\n        T["links"][li]["arcs"].insert(0, T["links"][li]["arcs"][ai])\n', ("mix",)),
    (u"X8 first_arc が arc の無い link を飛ばさない", u'        if L["arcs"]:\n            return li, 0\n', u"        return li, 0\n", ("mix",)),
    (u"X9 first_label が loc を返す", u'            if e["kind"] == "label":\n                return li, ei\n', u'            if e["kind"] == "loc":\n                return li, ei\n', ("mix",)),
    (u"X10 混ぜ物が元の表を書き換える", u"    T = copy.deepcopy(tables[kind])", u"    T = tables[kind]", ("mix",)),
    (u"X11 M1 が最初でない arc を除く", u'        li, ai = at\n        del T["links"][li]["arcs"][ai]\n    elif idx == 1:', u'        li, ai = at\n        del T["links"][li]["arcs"][-1]\n    elif idx == 1:', ("mix",)),
    (u"X12 M4 の当て先を日本語のラベルにする", u'        kind, at = "lab-en", first_label(tables["lab-en"])', u'        kind, at = "lab", first_label(tables["lab"])', ("mix",)),
    (u"X13 M6 の arcrole を all にする", u'DOMAIN_MEMBER_ARCROLE = "http://xbrl.org/int/dim/arcrole/domain-member"', u'DOMAIN_MEMBER_ARCROLE = "http://xbrl.org/int/dim/arcrole/all"', ("seal", "mix")),
    (u"X14 違いを見つけたが fact を見ない", u'item[u"違いを見つけた"] = not (tax and B.facts_same(orig_facts, mfacts))', u'item[u"違いを見つけた"] = not tax', ("mixtamper",)),
    (u"X15 違いを見つけたが書き出しを見ない", u'item[u"違いを見つけた"] = not (tax and B.facts_same(orig_facts, mfacts))', u'item[u"違いを見つけた"] = not B.facts_same(orig_facts, mfacts)', ("doc", "mixtamper")),
    (u"X16 混ぜ物の鳴り方が元どうしを比べる", u'item[u"鳴り方が違う"] = not B.sounds_same(orig, mone)', u'item[u"鳴り方が違う"] = not B.sounds_same(orig, orig)', ("doc",)),
    (u"X17 混ぜ物の書き出しを掛け方 A の 1 つだけで見る", u"tax = all(outputs_same(orig_outs, mouts).values())", u"tax = outputs_same(orig_outs, mouts)[OUTPUT_KEYS[0]]", ("doc", "mixtamper")),
    (u"X18 混ぜ物の包みに混ぜ物でない表から組んだ字を入れる", u"                files2[kind] = (build_xsd(T) if kind == \"xsd\" else build_linkbase(T)).encode(\"utf-8\")", u"                files2[kind] = new_files[kind]", ("doc",)),
    (u"X19 混ぜ物を本番の書類にも掛ける", u"mixtures=(n <= dev_count))", u"mixtures=True)", ("run",)),
    # ---- 比べる
    (u"C1 行が 1 以下でも同じにする", u"    if key in NEED_ROWS and (len(a) <= 1 or len(b) <= 1):\n        return False\n", u"", ("compare",)),
    (u"C2 行が 1 以下を問う書き出しに計算を足す", u'NEED_ROWS = (u"概念", u"役割型", u"表示", u"ラベルの関係")', u'NEED_ROWS = (u"概念", u"役割型", u"表示", u"計算", u"ラベルの関係")', ("seal", "compare")),
    (u"C3 概念の同じ先頭の欄の行を並べ替えない", u"        out.extend(sorted(rows[i:j]))", u"        out.extend(rows[i:j])", ("compare",)),
    (u"C4 概念の行を全部並べ替える", u"        while j < len(rows) and rows[j][:1] == rows[i][:1]:", u"        while j < len(rows):", ("compare",)),
    (u"C5 並びを問わない書き出しに表示を足す", u'UNORDERED_OUTPUTS = (u"概念",)', u'UNORDERED_OUTPUTS = (u"概念", u"表示")', ("compare",)),
    (u"C6 CSV の見出しの行を除く", u"        return [tuple(r) for r in csv.reader(fh)]", u"        return [tuple(r) for r in csv.reader(fh)][1:]", ("compare",)),
    (u"C7 CSV の欄の大きさの上限を直さない", u"    csv.field_size_limit(2 ** 31 - 1)\n", u"", ("compare",)),
    (u"C8 CSV の場所を使い回す", u'(k, os.path.join(workdir, u"%s_%d.csv" % (tag, i)))', u'(k, os.path.join(workdir, u"%s.csv" % tag))', ("compare", "doc")),
    (u"C9 掛け方 A から --validate を外す", u'"-f", zip_path, "--validate", "--facts"', u'"-f", zip_path, "--facts"', ("compare", "doc")),
    (u"C10 掛け方 B に --validate を付ける", u'"-f", zip_path, "--viewArcrole", GENERAL_SPECIAL_ARCROLE', u'"-f", zip_path, "--validate", "--viewArcrole", GENERAL_SPECIAL_ARCROLE', ("compare", "doc")),
    (u"C11 道具の呼び出しに種の固定を付けない(A)", u"    text_a, to_a = runner(SEED_PREFIX + command_a(", u"    text_a, to_a = runner(command_a(", ("doc",)),
    (u"C12 道具の呼び出しに種の固定を付けない(B)", u"    runner(SEED_PREFIX + command_b(", u"    runner(command_b(", ("doc",)),
    (u"C13 種の固定の字を替える", u'SEED_PREFIX = ["/usr/bin/env", "PYTHONHASHSEED=0"]', u'SEED_PREFIX = ["/usr/bin/env", "PYTHONHASHSEED=1"]', ("compare", "doc")),
    (u"C14 掛け方 A の factListCols を替える", u'FACT_COLS = "Name contextRef unitRef Dec Value EntityScheme EntityIdentifier Period Dimensions"', u'FACT_COLS = "Name contextRef unitRef Dec Value"', ("seal", "compare")),
    (u"C15 掛け方 B を掛けない", u"    runner(SEED_PREFIX + command_b(tool, zip_path, paths), TIMEOUT_SEC)\n", u"", ("doc",)),
    (u"C16 書き出し 7 つの並びを替える", u'OUTPUT_KEYS = (u"概念", u"役割型", u"表示", u"計算", u"次元", u"ラベルの関係", u"一般特殊")', u'OUTPUT_KEYS = (u"概念", u"役割型", u"計算", u"表示", u"次元", u"ラベルの関係", u"一般特殊")', ("seal",)),
    # ---- 書類 1 本
    (u"D1 元の包みと組み直した包みを同じ名にする", u'        new_zip = os.path.join(d, "new.zip")', u'        new_zip = os.path.join(d, "orig.zip")', ("doc",)),
    (u"D2 組み直した包みに元の file を入れる", u"    by_name = dict((names[k], new_files[k]) for k in new_files)", u"    by_name = {}", ("doc",)),
    (u"D3 字が同じを全部 True にする", u'rec[u"字が同じ"] = od((k, new_files[k] == orig_by[names[k]]) for k in FILE_KINDS)', u'rec[u"字が同じ"] = od((k, True) for k in FILE_KINDS)', ("doc",)),
    (u"D4 fact が同じが組み直しどうしを比べる", u'rec[u"fact が同じ"] = B.facts_same(orig_facts, new_facts)', u'rec[u"fact が同じ"] = B.facts_same(new_facts, new_facts)', ("docmain",)),
    (u"D5 鳴り方が同じが組み直しどうしを比べる", u'rec[u"鳴り方が同じ"] = B.sounds_same(orig, new)', u'rec[u"鳴り方が同じ"] = B.sounds_same(new, new)', ("docmain",)),
    (u"D6 全部同じが or になる", u'rec[u"全部同じ"] = rec[u"タクソノミが同じ"] and rec[u"fact が同じ"]', u'rec[u"全部同じ"] = rec[u"タクソノミが同じ"] or rec[u"fact が同じ"]', ("docmain",)),
    (u"D7 タクソノミが同じが any になる", u'rec[u"タクソノミが同じ"] = all(same.values())', u'rec[u"タクソノミが同じ"] = any(same.values())', ("docmain",)),
    (u"D8 書き出しの比べが組み直しどうしを見る", u"    return od((k, output_same(k, a[k], b[k])) for k in OUTPUT_KEYS)", u"    return od((k, output_same(k, b[k], b[k])) for k in OUTPUT_KEYS)", ("docmain", "compare")),
    (u"D9 断った書類の同じを True にする", u'rec[u"タクソノミが同じ"] = rec[u"fact が同じ"] = rec[u"鳴り方が同じ"] = rec[u"全部同じ"] = False', u'rec[u"タクソノミが同じ"] = rec[u"fact が同じ"] = rec[u"鳴り方が同じ"] = rec[u"全部同じ"] = True', ("doc",)),
    (u"D10 例外の理由を替える", u'rec[u"断った"], rec[u"断った理由"] = True, u"例外"', u'rec[u"断った"], rec[u"断った理由"] = True, u"知らない形"', ("doc",)),
    (u"D11 使い捨ての場所を消さない", u"    finally:\n        shutil.rmtree(d, ignore_errors=True)\n\n\ndef compare_into", u"    finally:\n        pass\n\n\ndef compare_into", ("doc",)),
    (u"D12 ラベルの数を端の数にする", u'(u"ラベルの数", sum(1 for L in K["links"] for e in L["ends"] if e["kind"] == "label") if K else 0)', u'(u"ラベルの数", sum(1 for L in K["links"] for e in L["ends"]) if K else 0)', ("doc",)),
    (u"D13 時間の上限を 60 秒にする", u"TIMEOUT_SEC = 600", u"TIMEOUT_SEC = 60", ("seal", "doc")),
    (u"D14 規則の年を 2025 にする", u'YEAR = "EDINET-2026"', u'YEAR = "EDINET-2025"', ("seal", "compare")),
    (u"D15 開発の本数を 6 にする", u"DEV_COUNT = 5", u"DEV_COUNT = 6", ("seal", "devdocs")),
    (u"D16 混ぜ物の種類の並びを替える", u'MIX_KINDS = (u"表示の arc を抜く", u"計算の向きを返す",', u'MIX_KINDS = (u"計算の向きを返す", u"表示の arc を抜く",', ("seal", "doc")),
    (u"D17 予測の境を 1 つ替える", u'("XT0-1", (54, None))', u'("XT0-1", (55, None))', ("seal",)),
    (u"D18 sha256 の封の字を 1 字替える", u'SHA_P = "fd9b0d08', u'SHA_P = "ed9b0d08', ("seal",)),
    (u"D19 封の commit を替える", u'SEAL_COMMIT = "dae701b0"', u'SEAL_COMMIT = "dae701b1"', ("seal",)),
    (u"D20 限界の字を 1 つ消す", u'    u"EDINET の本物の検査とは照らしていない。",\n', u"", ("seal",)),
    (u"D21 書類の元の包みに掛けない(元の結果を空にする)", u'        orig, orig_outs, orig_facts = run_package(tool, orig_zip, d, "orig", runner)', u'        orig, orig_outs, orig_facts = od([(u"類", u"走った"), (u"符号ごとの行", {})]), od((k, []) for k in OUTPUT_KEYS), []', ("doc",)),
    # ---- 数え方
    (u"N1 群を 5 本で割らない", u"    dev, prod = per_doc[:dev_count], per_doc[dev_count:]", u"    dev, prod = per_doc[:dev_count], per_doc", ("totals", "run")),
    (u"N2 全部同じ書類をタクソノミで数える", u'same_all += 1 if e[u"全部同じ"] else 0', u'same_all += 1 if e[u"タクソノミが同じ"] else 0', ("totals",)),
    (u"N3 断った書類を数えない", u"            declined += 1\n", u"            declined += 0\n", ("totals",)),
    (u"N4 字が同じ file を全部数える", u'same_file[k] += 1 if e[u"字が同じ"][k] else 0', u"same_file[k] += 1", ("totals",)),
    (u"N5 混ぜ物の違いを全部数える", u'found += 1 if m[u"違いを見つけた"] else 0', u"found += 1", ("totals",)),
    (u"N6 鳴り方が違うを違いを見つけたで数える", u'sound += 1 if m[u"鳴り方が違う"] else 0', u'sound += 1 if m[u"違いを見つけた"] else 0', ("totals",)),
    (u"N7 XT0-4 の分母を 372 にする", u'(u"分母", fl[u"分母"])', u'(u"分母", 372)', ("totals",)),
    (u"N8 XT0-6 の分母を混ぜ物の数にする", u'(u"個", mx[u"違いを見つけた数"]), (u"分母", mx[u"作れた数"])', u'(u"個", mx[u"違いを見つけた数"]), (u"分母", mx[u"混ぜ物の数"])', ("totals",)),
    (u"N9 判定を本番だけでなく全部で読む", u'    prod = tot[[k for k in tot if k.startswith(u"本番だけの")][0]]', u'    prod = tot[u"全部"]', ("totals",)),
    (u"N10 概念の行が 1 以下の書類を < 1 で数える", u'low_concepts += 1 if e[u"元の書き出しの行の数"][OUTPUT_KEYS[0]] <= 1 else 0', u'low_concepts += 1 if e[u"元の書き出しの行の数"][OUTPUT_KEYS[0]] < 1 else 0', ("totals",)),
    (u"N11 種類ごとの違いを見つけたが作れたを見ない", u'(u"違いを見つけた", sum(1 for m in items if m[u"作った"] and m[u"違いを見つけた"]))', u'(u"違いを見つけた", sum(1 for m in items if m[u"違いを見つけた"]))', ("totals",)),
    (u"N12 書き出しごとの同じを全部数える", u'same_out[k] += 1 if e[u"書き出しが同じ"][k] else 0', u"same_out[k] += 1", ("totals",)),
    (u"N13 表の数の合計に要素の宣言を足さない", u'tabs[u"要素の宣言"] += e[u"表の数"][u"要素の宣言"]', u'tabs[u"要素の宣言"] += 0', ("totals",)),
    (u"N14 作れた数を数えない", u"                made += 1\n", u"                made += 0\n", ("totals",)),
    # ---- 道具の確かめ・記録
    (u"O1 版の既定を替える", u"want_version=TOOL_VERSION, want_sha=SHA_P):\n    u\"\"\"実行 file が在り", u"want_version=u\"2.40.0\", want_sha=SHA_P):\n    u\"\"\"実行 file が在り", ("tools", "doc")),
    (u"O2 dev_docs が 1 本多く開く", u"    return B.dev_docs(docs_dir, count)", u"    return B.dev_docs(docs_dir, count + 1)", ("devdocs",)),
    (u"O3 dev_docs の既定を 6 にする", u"def dev_docs(docs_dir, count=DEV_COUNT):", u"def dev_docs(docs_dir, count=6):", ("devdocs",)),
    (u"O4 書類の選びを自分で書く", u"    docs = W.select_docs(docs_dir or DOCS_DIR, want)\n    info = check_tool(", u"    docs = dev_docs(docs_dir or DOCS_DIR, want)\n    info = check_tool(", ("wiring", "run")),
    (u"O5 道具の確かめの前に掛ける", u"    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)\n    per_doc = []", u"    info = od([(u\"版\", u\"\"), (u\"ModelValue.py の sha256\", u\"\"), (u\"package の一覧の sha256\", u\"\"), (u\"Python の版\", u\"\")])\n    per_doc = []", ("run", "e2e")),
    (u"O6 ラベルの字を 1 字から secret に入れる", u'if e["kind"] == "label" and len(e["text"]) >= 5:', u'if e["kind"] == "label" and len(e["text"]) >= 1:', ("run",)),
    (u"O7 要素の名を secret に入れない", u'            elems.add(e["name"])\n', u"            pass\n", ("run",)),
    (u"O8 --check が合計を照らさない", u'    if dumps(tot) != dumps(rec[u"集計"]) or', u'    if False or', ("verify",)),
    (u"O9 --check が判定の数を照らさない", u'or dumps(judged(tot, len(docs))) != dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):', u":", ("verify",)),
    (u"O10 --check が書類の本数を問わない", u"len(docs) != want or rec[u\"材料\"][u\"書類の本数\"] != want:", u"False:", ("verify",)),
    (u"O11 --check が断った書類の形を見ない", u'        if d[u"断った"] != (d[u"組み直しの 1 回"] is None) or (d[u"断った"] and (d[u"全部同じ"] or d[u"タクソノミが同じ"] or d[u"fact が同じ"] or d[u"鳴り方が同じ"] or any(d[u"字が同じ"].values()))) or (not d[u"断った"] and d[u"断った理由"]):', u"        if False:", ("verify",)),
    (u"O12 --check が導き方を見ない", u'        if d[u"全部同じ"] != (d[u"タクソノミが同じ"] and d[u"fact が同じ"]) or d[u"タクソノミが同じ"] != all(d[u"書き出しが同じ"].values()):', u"        if False:", ("verify",)),
    (u"O13 --check が欄の並びを見ない", u'        if list(d[u"字が同じ"]) != list(FILE_KINDS) or list(d[u"書き出しが同じ"]) != list(OUTPUT_KEYS) or list(d[u"元の書き出しの行の数"]) != list(OUTPUT_KEYS):', u"        if False:", ("verify",)),
    (u"O14 --check が混ぜ物の形を見ない", u'        if len(d[u"混ぜ物"]) != (len(MIX_KINDS) if i <= dev_count else 0) or [m[u"種類"] for m in d[u"混ぜ物"]] != (list(MIX_KINDS) if i <= dev_count else []):', u"        if False:", ("verify",)),
    (u"O15 --check が作れなかった混ぜ物の形を見ない", u'            if not m[u"作った"] and (m[u"違いを見つけた"] or m[u"鳴り方が違う"]):', u"            if False:", ("verify",)),
    (u"O16 URI の形を止めない", u'    if "http://" in text or "https://" in text:', u"    if False:", ("clean",)),
    (u"O17 前の便の記録の検査を呼ばない", u"    V.check_clean(rec, text, secret)", u"    pass", ("clean", "wiring")),
    (u"O18 書いた後の検査を外す", u"        check_clean(rec, back, secret)\n    except SystemExit:", u"        pass\n    except SystemExit:", ("clean",)),
    (u"O19 書く前の検査を外す", u"    text = record_text(rec, secret)\n    os.makedirs", u"    text = dumps(rec)\n    os.makedirs", ("clean",)),
    (u"O20 既に在る記録を書き直せる", u"    if os.path.exists(path):\n        raise Stop(u\"**記録が既に在る: %s。止める**\" % os.path.basename(path))\n", u"", ("clean", "e2e")),
    (u"O21 開発の入口が 7 本掛ける", u"    docs = dev_docs(docs_dir or DOCS_DIR, DEV_COUNT)\n    check_tool(tool_p, runner)", u"    docs = dev_docs(docs_dir or DOCS_DIR, 7)\n    check_tool(tool_p, runner)", ("devrun",)),
    (u"O22 開発の入口が混ぜ物を作らない", u"        r = process_doc(tool_p, p, tmp_root, runner, mixtures=True)\n        per.append", u"        r = process_doc(tool_p, p, tmp_root, runner, mixtures=False)\n        per.append", ("devrun",)),
    (u"O23 run が記録を書かない", u"    write_record(out, rec, secret)\n    say(", u"    say(", ("e2e",)),
    (u"O24 道具の確かめの前の道具の場所の存在を見ない版を呼ぶ", u"    return B.check_tool(tool, runner, sha_reader, want_version, want_sha)", u"    return {u\"版\": want_version, u\"ModelValue.py の sha256\": want_sha, u\"package の一覧の sha256\": u\"\", u\"Python の版\": u\"\"}", ("tools", "wiring")),
    # ---- 配線
    (u"W1 subprocess を import する", u"import shutil\nimport sys", u"import shutil\nimport subprocess\nimport sys", ("wiring",)),
    (u"W2 zipfile を import する", u"import tempfile\nimport time", u"import tempfile\nimport time\nimport zipfile", ("wiring",)),
    (u"W3 engine を読む", u"import xml.etree.ElementTree as ET\n\nHERE", u"import xml.etree.ElementTree as ET\nfrom adapters.xbrl import instance as I\n\nHERE", ("wiring",)),
    (u"W4 前の便の script を重なる名で読む", u'BUILD_NAME = "_xt0_inline_build_2026_11_21"', u'BUILD_NAME = "_xb0_inline_build_2026_11_21"', ("wiring",)),
    (u"W5 便 XV0 の script を自分で読み直す", u"V = B.V ", u'V = _load_sibling("_xt0_other_validate", "xbrl_edinet_validate_2026-11-21.py")  # ', ("wiring",)),
    (u"W6 load_package を写す", u"def package_with(entries, names, new_files):", u"def load_package(zip_path):\n    return []\n\n\ndef package_with(entries, names, new_files):", ("wiring",)),
    (u"W7 build_xsd が元の字を引数に取る", u"def build_xsd(S):", u"def build_xsd(S, text=None):", ("isolation",)),
    (u"W8 build_linkbase が file を開く", u'    uses_dt = any(k.startswith("{%s}" % NS_XBRLDT)', u'    open\n    uses_dt = any(k.startswith("{%s}" % NS_XBRLDT)', ("isolation",)),
    (u"W9 build_xsd が ElementTree を使う", u'    unknown = set(k for e in S["elements"] for k in e) - set(XSD_ELEMENT_ATTRS)', u'    ET\n    unknown = set(k for e in S["elements"] for k in e) - set(XSD_ELEMENT_ATTRS)', ("isolation",)),
    (u"W10 process_doc が組む部品に元の字を渡す", u"            new_files = build_tables(tables)", u"            new_files = build_tables(found)", ("isolation",)),
    (u"W11 ElementTree を使う関数を足す", u"def text_of(node):", u"def sneak(x):\n    return ET.fromstring(x)\n\n\ndef text_of(node):", ("isolation",)),
    (u"W12 別の門の規準の字を関数の名にする", u"def text_of(node):", u"def mutate(x):\n    return x\n\n\ndef text_of(node):", ("wiring",)),
    (u"W13 別の門の規準の字を説明文に書く", u"# ---- 名前空間\n", u"# ---- 名前空間(注入)\n", ("wiring",)),
    (u"W14 組む部品が前の便の script を使う", u'    prefixes = assign_prefixes([NS_XSD, NS_LINK, NS_XLINK, NS_XBRLI] + uris)', u'    prefixes = assign_prefixes([NS_XSD, NS_LINK, NS_XLINK, NS_XBRLI] + uris)\n    B.load_package', ("isolation",)),
    (u"W15 便 XG0 の script の Stop を使わない", u"W = B.W ", u'W = _load_sibling("_xt0_other_wall", "xbrl_tag_wall_2026-11-21.py")  # ', ("wiring",)),
)
#: 黙ることが分かっている変異(理由つき)
SILENT_BY_DESIGN = ()


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"strip": strip_problems, u"build": build_problems, u"decline": decline_problems, u"mix": mix_problems, u"compare": compare_problems,
             u"doc": doc_problems, u"docmain": docmain_problems, u"mixtamper": mixtamper_problems, u"totals": totals_problems, u"tools": tools_problems, u"devdocs": dev_docs_problems,
             u"run": run_problems, u"verify": verify_problems, u"clean": clean_problems, u"e2e": e2e_problems, u"devrun": devrun_problems}
    if name in table:
        return table[name](mod)
    if name == u"wiring":
        return import_problems(src)
    if name == u"isolation":
        return build_isolation_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"strip", u"build", u"decline", u"mix", u"compare", u"doc", u"docmain", u"mixtamper", u"totals", u"tools", u"devdocs", u"run", u"verify", u"clean", u"e2e", u"devrun", u"wiring", u"isolation")


def run_mutants(table=MUTANTS, only=None):
    base = read(SCRIPT_REL)
    out_ = []
    for name, old, new, checks in table:
        if only is not None and name not in only:
            continue
        pairs = list(zip(old, new)) if isinstance(old, tuple) else [(old, new)]
        src = base
        for o, n in pairs:
            assert base.count(o) == 1, (name, base.count(o))
            src = src.replace(o, n)
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
        for old, new in ((u"`arelle-release` の版 `2.47.5`", u"`arelle-release` の版 `2.47.6`"), (SEAL_SHA_P, SEAL_SHA_P[:-1] + u"1"), (u"開発の 5 本 × 6 種類 = 30 個", u"開発の 5 本 × 6 種類 = 31 個"),
                         (u"| XT0-1(主) | 全部同じ書類は 54 本以上", u"| XT0-1(主) | 全部同じ書類は 55 本以上"), (u"1 回の時間の上限は 600 秒", u"1 回の時間の上限は 60 秒"),
                         (u"**M1 表示の arc を抜く**", u"**M1 表示の arc を消す**"), (u"--disclosureSystem EDINET-2026", u"--disclosureSystem EDINET-2025"), (u"便 XG0 と同じ 67 本", u"便 XG0 と同じ 66 本"),
                         (u"--viewArcrole http://www.xbrl.org/2003/arcrole/general-special", u"--viewArcrole http://www.xbrl.org/2003/arcrole/general-specia1")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"taxonomy_build", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        pr = load_helpers()
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


class PureTest(unittest.TestCase):
    def test_b_1_strip_gives_the_two_kinds_of_tables_and_holds_no_original_text(self):
        self.assertEqual([], strip_problems())

    def test_b_2_build_writes_the_same_bytes_from_the_tables_alone(self):
        self.assertEqual([], build_problems())

    def test_b_3_unknown_forms_are_declined(self):
        self.assertEqual([], decline_problems())

    def test_b_4_the_six_mixtures(self):
        self.assertEqual([], mix_problems())

    def test_b_5_comparisons_and_the_two_ways_of_running_the_tool(self):
        self.assertEqual([], compare_problems())

    def test_b_6_totals_and_the_judged_numbers(self):
        self.assertEqual([], totals_problems())

    def test_b_7_the_hand_made_files_cover_every_form(self):
        u"""作り物の字が ``xsd:`` あり・なし・BOM・prohibited・priority・preferredLabel・loc の xlink:role・roleRef・arcroleRef・重み -1・複数の拡張 link・同じ要素への複数の loc・同じ字の xlink:label・端と arc の入り混じりを含む。"""
        self.assertIn(u"<xsd:schema", XSD_ALT)
        self.assertNotIn(u"<xsd:schema", XSD_NOPFX)
        self.assertTrue(XSD_NOPFX.startswith(u"\ufeff"))
        self.assertNotIn(u"encoding", XSD_NOPFX.split(u"?>")[0])
        self.assertIn(u'use="prohibited"', LAB_ALT)
        self.assertIn(u"priority=", LAB_ALT)
        self.assertIn(u"preferredLabel=", PRE_ALT)
        self.assertIn(u'xlink:role="http://x/role/locrole"', LAB_ALT)
        self.assertIn(u"<link:roleRef", PRE_ALT)
        self.assertIn(u"<link:arcroleRef", DEF_ALT)
        self.assertIn(u'weight="-1"', CAL_ALT)
        self.assertGreaterEqual(PRE_ALT.count(u"<link:presentationLink"), 2)
        self.assertGreaterEqual(CAL_ALT.count(u"<link:calculationLink"), 2)
        self.assertGreaterEqual(PRE_ALT.count(u'xlink:href="t.xsd#a_Alpha"'), 2)
        self.assertGreaterEqual(PRE_ALT.count(u'xlink:label="Q"'), 2)
        self.assertIn(u"dt:usable", DEF_ALT)
        self.assertIn(u"<!--", XSD_ALT)
        self.assertIn(u"<!--", PRE_ALT)
        self.assertNotEqual(ALT_TEXTS, CANON_TEXTS)
        for k in KINDS:
            self.assertNotEqual(ALT_TEXTS[k], CANON_TEXTS[k], k)
        # 端と arc の入り混じり(arc が後ろの端より前に在る)
        self.assertLess(DEF_ALT.index(u"<link:definitionArc"), DEF_ALT.index(u'xlink:label="B"'))
        self.assertLess(LAB_ALT.index(u"<link:labelArc"), LAB_ALT.index(u'xlink:label="Alpha_verbose"'))
        self.assertEqual(len(set(HAND_ROWS.values())) >= 3, True)
        self.assertEqual(len(KINDS), 6)
        self.assertEqual(len(MS.MIX_KINDS), 6)


class ReviseTest(unittest.TestCase):
    u"""本線の比べ・混ぜ物の比べ・開発の入口・並びの問い方を、作り物の道具の答えを 1 つずつ変えて縛る。"""

    def test_g_1_the_main_comparison_turns_false_when_the_rebuilt_package_differs(self):
        self.assertEqual([], docmain_problems())

    def test_g_2_the_mixture_verdicts_come_from_comparing_with_the_original(self):
        self.assertEqual([], mixtamper_problems())

    def test_g_3_the_dev_entry_runs_only_the_first_five_documents(self):
        self.assertEqual([], devrun_problems())

    def test_g_4_the_dev_docs_open_only_the_head_of_the_list(self):
        self.assertEqual([], dev_docs_problems())


class RunTest(unittest.TestCase):
    def test_c_1_the_tool_check(self):
        self.assertEqual([], tools_problems())

    def test_c_2_one_document_goes_through_with_a_fake_tool(self):
        self.assertEqual([], doc_problems())

    def test_c_4_build_record_with_fake_documents_and_a_fake_tool(self):
        self.assertEqual([], run_problems())

    def test_c_5_run_record_check_with_fake_tools_and_a_fake_cache(self):
        self.assertEqual([], e2e_problems())

    def test_c_6_the_record_check_catches_tampering(self):
        self.assertEqual([], verify_problems())

    def test_c_7_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_c_8_the_real_record_when_present_is_clean_and_consistent(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く")
        text = read(RECORD_REL)
        MS.verify_record(json.loads(text, object_pairs_hook=od), text)


class WiringTest(unittest.TestCase):
    def test_e_1_imports_and_the_earlier_functions_are_called_not_copied(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport subprocess\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport zipfile\n"))
        self.assertNotEqual([], import_problems(base + u"\nfrom adapters.xbrl import instance\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.system('a')\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef select_docs(a, b):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef load_package(a):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef run_doc(a):\n    return None\n"))
        self.assertNotEqual([], import_problems(base.replace(u"W.order_sha256(", u"order_sha256(")))
        self.assertNotEqual([], import_problems(base.replace(u"B.load_package(", u"load_package(")))

    def test_e_3_the_build_functions_read_nothing_but_the_tables(self):
        self.assertEqual([], build_isolation_problems())

    def test_e_4_the_isolation_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], build_isolation_problems(base.replace(u"def build_xsd(S):", u"def build_xsd(S, original=None):")))
        self.assertNotEqual([], build_isolation_problems(base.replace(u"def build_linkbase(K):", u"def build_linkbase(text):")))
        self.assertNotEqual([], build_isolation_problems(base.replace(u"    lines = [u'<?xml", u"    data = open(K)\n    lines = [u'<?xml", 1)))
        self.assertNotEqual([], build_isolation_problems(base + u"\ndef reader(p):\n    return ET.parse(p)\n"))

    def test_e_5_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_6_the_script_leaves_sys_modules_as_it_found_them_except_its_own_earlier_script_names(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_taxonomy_build_script_for_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        self.assertEqual(mod.B.__name__, BUILD_NAME)
        self.assertIs(mod.V, mod.B.V)
        self.assertIs(mod.W, mod.B.W)
        self.assertIs(mod.Stop, mod.V.Stop)
        del mod

    def test_e_7_the_default_place_is_outside_the_repo_and_the_gate_never_opens_it(self):
        top = os.path.realpath(REPO)
        self.assertFalse(os.path.realpath(MS.DOCS_DIR).startswith(top + os.sep))
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record|dev_docs|dev_run)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"docs|rec_path|\*\*kw|rp|\bd\b|\btool\b", m.group(2)), m.group(0))

    def test_e_8_the_gate_does_not_import_subprocess_except_for_git(self):
        src = read(GATE_REL)
        calls = re.findall(r"subprocess\.(\w+)", src)
        self.assertEqual(set(calls), {"run", "PIPE"})
        for m in re.finditer(r"subprocess\.run\(\[([^\]]*)\]", src):
            self.assertTrue(m.group(1).startswith(u'"git"'), m.group(0))


class MutantTest(unittest.TestCase):
    def test_f_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL))
        modules_before = dict(sys.modules)
        results = run_mutants()
        self.assertEqual(before, (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL)))
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
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
