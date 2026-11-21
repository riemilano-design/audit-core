# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TAG_NARROW_SEAL_2026-11-21.md(XG1 ― 便 XG0 で候補が 2 つ以上だった行を、数を持てる要素・計算書の種類・業種の科目の一覧で絞る)の封の門。

**この門は置き場を読まない**(書類の置き場 ``~/.cache/audit-core/edinet/``・標準ラベルの置き場・標準タクソノミの zip は 1 度も開かない)。通信しない。
読むのは repo の中の封の file・前の便の記録(段 0 の 4 つの数の照合先)・script だけ。作り物の zip・作り物のラベルの linkbase・作り物の要素の表・科目の一覧・見出し・DEI を使う。

**この門が縛るもの**

1. 封の字: 封の commit(1bda1997)・封の file が commit した blob と同じ・zip の url と sha256・要素の表と科目の一覧の file の名の型・見出しの 5 つの決め(上から先に当たったもの)・``cte`` → ``cai``・
   DEI の name 2 つ・16763・段 0 の 4 つの数(前の便の記録から読む)・予測の境の数・限界の 6 行が script の定数と同じ。
2. engine は封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 作り物の行と見出しと DEI で、段 1(abstract・domainItemType・stringItemType を除く)・段 2(どれかの業種の C(·, K)・K が決まらない行は段 1 のまま)・段 3(C(I, K)・I が決まらない・
   C(I, K) が無いときは段 2 のまま)・見出し(行より前の最後・同じ file の中だけ・上から先に当たった決め)・業種(見出しの 連結 で DEI の欄を選ぶ・昇順で最初に空でない値・小文字・cte → cai)・
   類 U・A・W・N・落とした行・段を進めて U が減る例を、本物の関数のまま通す(行ごとに手で決めた値と照らす)。
4. E(提出の要素)は 3 つの段の関数に渡さない(関数の引数に無い)。提出者の ``_lab.xml``・``_pre.xml``・``_def.xml``・``_cal.xml``・``.xsd`` を読まない。
5. 記録の禁止の検査(docID・EDINET コード・会社の名・行の字・見出しの字・要素の名・業種のコードの値)が作り物で止まる。zip の sha256・16763・段 0 の 4 つの数が違えば止まる。
6. script の import は標準ライブラリと engine の 2 module(instance・verify_document)と importlib だけ。前の便の script は importlib で読み(一意の名)、関数は呼ぶ(写さない)。
7. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
黙る変異は ``SILENT_BY_DESIGN`` に理由とともに置き、「黙ること」自体を別の試験で縛る。
"""
import ast
import collections
import hashlib
import importlib.util
import inspect
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
    mod = types.ModuleType("xbrl_tag_narrow_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_TAG_NARROW_SEAL_2026-11-21.md"
SEAL_COMMIT_SHORT = "1bda1997"                # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_tag_narrow_2026-11-21.py"
GATE_REL = "tests/measure/test_xbrl_tag_narrow_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/tag_narrow_2026-11-21.json"
PRIOR_RECORD_REL = "fixtures/xbrl/cd8/tag_wall_2026-11-21.json"
MS = load_module(SCRIPT_REL, "xbrl_tag_narrow_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_tag_narrow_seal")      # 順序・履歴の部品。門としては走らせない
ORDER_FILES = (SCRIPT_REL, GATE_REL)          # 記録の順序は記録が在るときの結果の門に置く
od = collections.OrderedDict


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.exists(os.path.join(ROOT, rel)) else None


def guard(fn, *a, **kw):
    u"""fn が例外(``SystemExit`` を含む)を投げたら、その例外の型の名前の字を返す。違いを見るための道具。"""
    try:
        return fn(*a, **kw)
    except BaseException as exc:                # noqa: BLE001
        return [u"例外: %s" % type(exc).__name__]


def stops(ms, fn, *a, **kw):
    u"""fn が ``ms.Stop`` を投げれば True。投げなければ False。別の例外は投げ直す。"""
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xg1_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


# ======================================================================== 作り物の標準タクソノミ(要素の表・科目の一覧・業種の folder)
XSD_HEAD = u'<?xml version="1.0" encoding="UTF-8"?><xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xbrli="http://www.xbrl.org/2003/instance">'
MONETARY = u"xbrli:monetaryItemType"
#: (名前, type, abstract の字(None なら属性を付けない))
FAKE_X = [
    (u"Assets", MONETARY, u"false"), (u"AssetsAbs", MONETARY, u"true"), (u"AssetsDom", u"nonnum:domainItemType", u"false"), (u"AssetsStr", u"xbrli:stringItemType", u"false"),
    (u"CashAbs", MONETARY, u"true"),
    (u"OthPl", MONETARY, u"false"), (u"OthBk1Pl", MONETARY, u"false"), (u"OthBs", MONETARY, u"false"), (u"OthNone", MONETARY, u"false"),
    (u"ChgSs", MONETARY, u"false"), (u"ChgSs2", MONETARY, u"false"), (u"ChgPl", MONETARY, u"false"),
    (u"CfItem", MONETARY, u"false"), (u"CfOther", MONETARY, u"false"),
    (u"ShareQty", u"xbrli:sharesItemType", None)]                                     # abstract の属性が無い(段 1 に残る)
#: 科目の一覧(file が在る (I, K) だけ)
FAKE_C = {
    # abstract の要素(AssetsAbs)も科目の一覧には載る
    ("cai", "bs"): {u"Assets", u"OthBs", u"AssetsAbs"}, ("cai", "pl"): {u"OthPl", u"ChgPl"}, ("cai", "ss"): {u"ChgSs"}, ("cai", "cf"): {u"CfItem"},
    ("bk1", "bs"): {u"OthBs"}, ("bk1", "pl"): {u"OthBk1Pl"}, ("bk1", "cf"): {u"CfOther"},               # bk1 に ss の一覧は無い
    ("cmd", "ss"): {u"ChgSs2"}}
FAKE_FOLDERS = ["bk1", "cai", "cmd", "emp"]                                                    # emp は folder だけ在って一覧が 1 つも無い
UNION = {"bs": {u"Assets", u"OthBs", u"AssetsAbs"}, "pl": {u"OthPl", u"ChgPl", u"OthBk1Pl"}, "ss": {u"ChgSs", u"ChgSs2"}, "cf": {u"CfItem", u"CfOther"}}


def xsd_bytes(entries=None):
    parts = [XSD_HEAD]
    for nm, ty, ab in (FAKE_X if entries is None else entries):
        parts.append(u'<xsd:element name="%s" id="jppfs_cor_%s" type="%s"%s substitutionGroup="xbrli:item"/>' % (nm, nm, ty, u"" if ab is None else u' abstract="%s"' % ab))
    parts.append(u"</xsd:schema>")
    return u"".join(parts).encode("utf-8")


def def_text(names, decoys=True):
    u"""def の linkbase の字。``#jppfs_cor_`` の href のほかに、役割の href と jpcrp の href(使わない)を混ぜる。"""
    parts = [u'<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink"><link:definitionLink>']
    if decoys:
        parts.append(u'<link:loc xlink:type="locator" xlink:href="../../jppfs_rt_2025-11-01.xsd#rol_cai_StatementOfIncome" xlink:label="r"/>')
        parts.append(u'<link:loc xlink:type="locator" xlink:href="../../../jpcrp/jpcrp_cor_2025-11-01.xsd#jpcrp_cor_DecoyCrp" xlink:label="d"/>')
    for i, nm in enumerate(sorted(names)):
        parts.append(u'<link:loc xlink:type="locator" xlink:href="../../jppfs_cor_2025-11-01.xsd#jppfs_cor_%s" xlink:label="l%d"/>' % (nm, i))
    parts.append(u"</link:definitionLink></link:linkbase>")
    return u"".join(parts)


TOP = u"金融庁の日本語の名前/taxonomy/"
DEC_TOP = u"金融庁の日本語の名前/taxonomy_old/"                   # /taxonomy/ を含まない
R = u"jppfs/2025-11-01/r/"


def make_tax_zip(path):
    u"""作り物の標準タクソノミの zip。頭の folder は日本語。使わない file(別の日付・cal・def の枝・``/taxonomy/`` の外の folder)も入れる。"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(TOP + u"jppfs/2025-11-01/jppfs_cor_2025-11-01.xsd", xsd_bytes())
        z.writestr(TOP + u"jppfs/2024-11-01/jppfs_cor_2024-11-01.xsd", xsd_bytes([(u"Old", MONETARY, u"false")]))
        for (i, k), names in sorted(FAKE_C.items()):
            z.writestr(TOP + R + u"%s/jppfs_%s_cm_2025-11-01_def_%s.xml" % (i, i, k), def_text(names))
        z.writestr(TOP + R + u"cai/jppfs_cai_cm_2025-11-01_def_bs-1-BS-03-PPE.xml", def_text([u"ShareQty"]))        # def の枝(使わない)
        z.writestr(TOP + R + u"cai/jppfs_cai_cm_2025-11-01_cal_bs.xml", def_text([u"ShareQty"]))                    # cal(使わない)
        z.writestr(TOP + R + u"emp/jppfs_emp_ac_2025-11-01_def_bs.xml", def_text([u"ShareQty"]))                    # cm でない(使わない)
        z.writestr(DEC_TOP + R + u"zzz/jppfs_zzz_cm_2025-11-01_def_bs.xml", def_text([u"ShareQty"]))                 # /taxonomy/ の外(使わない)
        z.writestr(u"readme.txt", b"x")


# ======================================================================== 作り物のラベルの linkbase(表 L2)
LB_HEAD = (u'<?xml version="1.0" encoding="UTF-8"?>\n<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" '
           u'xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xml="http://www.w3.org/XML/1998/namespace"><link:labelLink xlink:type="extended">')
R_STD = "http://www.xbrl.org/2003/role/label"


def linkbase(entries):
    parts = [LB_HEAD]
    for i, (full, role, text, lang) in enumerate(entries):
        parts.append(u'<link:loc xlink:type="locator" xlink:href="x.xsd#%s" xlink:label="loc_%d"/>' % (full, i))
        parts.append(u'<link:label xlink:type="resource" xlink:label="lab_%d" xlink:role="%s" xml:lang="%s">%s</link:label>' % (i, role, lang, text))
        parts.append(u'<link:labelArc xlink:type="arc" xlink:from="loc_%d" xlink:to="lab_%d"/>' % (i, i))
    parts.append(u"</link:labelLink></link:linkbase>")
    return u"".join(parts).encode("utf-8")


#: 表 L2(ラベルの字 → cand0)。要素の数 5・1・4・3・1・2 がどれも違う
FAKE_L2 = {
    u"資産": {u"Assets", u"AssetsAbs", u"AssetsDom", u"AssetsStr", u"AssetsNoX"},          # AssetsNoX は要素の表に無い
    u"現金": {u"CashAbs"},
    u"その他": {u"OthPl", u"OthBk1Pl", u"OthBs", u"OthNone"},
    u"当期変動額": {u"ChgSs", u"ChgSs2", u"ChgPl"},
    u"株式数": {u"ShareQty"},
    u"現金同等物": {u"CfItem", u"CfOther"}}
FAKE_LABELS = linkbase([(u"jppfs_cor_%s" % e, R_STD, t, "ja") for t, es in sorted(FAKE_L2.items()) for e in sorted(es)] + [(u"jppfs_cor_Assets", R_STD, u"Assets", "en")])


def fake_tax(ms=None):
    ms = ms or MS
    return ms.make_tax(ms.build_x(xsd_bytes()), dict(FAKE_C), FAKE_FOLDERS)


# ======================================================================== 作り物の書類(見出し・DEI・行)
NFTAG = u'<ix:nonFraction name="%s" contextRef="c1" unitRef="JPY" decimals="-6" scale="6">100</ix:nonFraction>'
DEI_C = u"jpdei_cor:IndustryCodeWhenConsolidatedFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI"
DEI_S = u"jpdei_cor:IndustryCodeWhenFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI"


def row(label, e):
    return u"<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (label, NFTAG % (u"jppfs_cor:" + e), NFTAG % (u"jppfs_cor:" + e))


def table(rows):
    return u"<table>" + u"".join(rows) + u"</table>"


def head(h):
    return u"<p>【%s】</p>" % h


def dei(name, value):
    u"""``value`` が None なら中身の空の ix:nonNumeric。"""
    inner = u"" if value is None else u"<span> %s </span>" % value
    return u'<p><ix:nonNumeric name="%s" contextRef="c1">%s</ix:nonNumeric></p>' % (name, inner)


def dei_nl(name, value):
    u"""値が改行で挟まれた形(実物の書類に多い): ``<ix:nonNumeric …>\n  CTE\n</ix:nonNumeric>``。"""
    return u'<p><ix:nonNumeric name="%s" contextRef="c1">\n  %s\n</ix:nonNumeric></p>' % (name, value)


def file_of(groups):
    u"""[(見出しか None, [(label, E)])] → 1 file の字。"""
    out = []
    for h, rows in groups:
        if h is not None:
            out.append(head(h))
        out.append(table([row(l, e) for l, e in rows]))
    return u"".join(out)


H_BS, H_PL, H_PLCI, H_NOTE = u"連結貸借対照表", u"損益計算書", u"連結損益計算書及び連結包括利益計算書", u"注記事項"
H_SS, H_SS1, H_CF, H_CF1, H_CPL = u"連結株主資本等変動計算書", u"株主資本等変動計算書", u"連結キャッシュ・フロー計算書", u"キャッシュ・フロー計算書", u"連結損益計算書"
#: 行ごとに手で決めた値(書類 A と B)。(名, doc, label, E, 見出し, 段 0〜3 の類 4 字, 落とした行(段 1・段 2・段 3), 種類 K, I が決まらない行か)
HAND_ROWS = [
    ("r1", "A", u"資産", u"Assets", H_BS, "AUUU", (0, 0, 0), "bs", 0),
    ("r2", "A", u"資産", u"AssetsAbs", H_BS, "AWWW", (1, 1, 1), "bs", 0),
    ("r3", "A", u"現金", u"CashAbs", H_BS, "UNNN", (1, 1, 1), "bs", 0),
    ("r4", "A", u"その他", u"OthPl", H_PL, "AAAW", (0, 0, 1), "pl", 0),
    ("r5", "A", u"その他", u"OthBk1Pl", H_PL, "AAAU", (0, 0, 0), "pl", 0),
    ("r6", "A", u"未登録", u"Foo", H_PL, "NNNN", (0, 0, 0), "pl", 0),
    ("r7", "A", u"その他", u"OthPl", None, "AAAA", (0, 0, 0), None, 0),
    ("r8", "A", u"その他", u"OthNone", H_PLCI, "AAWW", (0, 1, 1), "pl", 0),
    ("r9", "A", u"その他", u"OthPl", H_PLCI, "AAAU", (0, 0, 0), "pl", 0),
    ("r10", "A", u"その他", u"OthPl", H_NOTE, "AAAA", (0, 0, 0), None, 0),
    ("r11", "A", u"当期変動額", u"ChgSs", H_SS, "AAAU", (0, 0, 0), "ss", 0),
    ("r12", "A", u"当期変動額", u"ChgSs", H_SS1, "AAAA", (0, 0, 0), "ss", 0),
    ("r13", "A", u"現金同等物", u"CfItem", H_CF, "AAAU", (0, 0, 0), "cf", 0),
    ("r14", "A", u"現金同等物", u"CfItem", H_CF1, "AAAW", (0, 0, 1), "cf", 0),
    ("r15", "A", u"株式数", u"ShareQty", H_CF1, "UUNN", (0, 1, 1), "cf", 0),
    ("r16", "B", u"その他", u"OthPl", H_CPL, "AAAA", (0, 0, 0), "pl", 1),
    ("r17", "B", u"その他", u"OthPl", H_PL, "AAAA", (0, 0, 0), "pl", 1),
    ("r18", "B", u"その他", u"OthNone", H_PL, "AAWW", (0, 1, 1), "pl", 1)]
#: 書類 A の DEI は 3 つの file に分かれる(連結の欄: 0a は空・0b が CTE・0c が cmd。個別の欄: 0a が BK1・0c が cmd)。書類 B は連結 ZZZ・個別は空
DEI_A = (u"cte", u"bk1")
DEI_B = (u"zzz", u"")


def doc_a_texts():
    rows = dict((r[0], r) for r in HAND_ROWS)

    def le(n):
        return (rows[n][2], rows[n][3])
    f0a = dei(DEI_C, None) + dei(DEI_S, u"BK1") + file_of([(H_BS, [le("r1"), le("r2"), le("r3")]), (H_PL, [le("r4"), le("r5"), le("r6")])])
    f0b = file_of([(None, [le("r7")]), (H_PLCI, [le("r8"), le("r9")]), (H_NOTE, [le("r10")])]) + dei_nl(DEI_C, u"CTE")
    f0c = (file_of([(H_SS, [le("r11")]), (H_SS1, [le("r12")]), (H_CF, [le("r13")]), (H_CF1, [le("r14"), le("r15")])]) + dei(DEI_C, u"cmd") + dei(DEI_S, u"cmd"))
    return [("0c_ixbrl.htm", f0c), ("0a_ixbrl.htm", f0a), ("0b_ixbrl.htm", f0b)]                   # 並びは昇順でない


def doc_b_texts():
    return [("0a_ixbrl.htm", dei(DEI_C, u"ZZZ") + dei(DEI_S, None) + file_of([(H_CPL, [(u"その他", u"OthPl")]), (H_PL, [(u"その他", u"OthPl"), (u"その他", u"OthNone")])]))]


def doc_c_texts():
    return [("0a_ixbrl.htm", dei(DEI_C, u"CTE") + file_of([(H_BS, [(u"資産", u"Assets")] * 9 + [(u"現金", u"CashAbs")])]))]


def doc_d_texts():
    return [("0a_ixbrl.htm", dei(DEI_C, u"cte") + file_of([(u"連 結 貸借 対照表", [(u"資産", u"Assets")] * 8 + [(u"現金", u"CashAbs")])]))]


def doc_e_texts():
    return [("0a_ixbrl.htm", dei(DEI_C, u"CTE") + u"<p>表なし</p>")]


DOCS_TEXTS = [doc_a_texts, doc_b_texts, doc_c_texts, doc_d_texts, doc_e_texts]
STEMS = ["S1FAKE01", "S1FAKE02", "S1FAKE03", "S1FAKE04", "S1FAKE05"]
ORDER_SHA = hashlib.sha256(u"\n".join(STEMS).encode("utf-8")).hexdigest()
#: 手で数えた書類ごとの値: (行, 段 0〜3 の (U, A, W, N), 落とした行(段 1〜3), K ごと (bs, pl, ss, cf), K が決まらない行, I が決まらない行, 段 3 の U の率)
HAND_DOCS = [
    (15, ((2, 12, 0, 1), (2, 10, 1, 2), (1, 9, 2, 3), (5, 3, 4, 3)), (2, 4, 6), (3, 5, 2, 3), 2, 0, 33.3),
    (3, ((0, 3, 0, 0), (0, 3, 0, 0), (0, 2, 1, 0), (0, 2, 1, 0)), (0, 1, 1), (0, 3, 0, 0), 0, 3, 0.0),
    (10, ((1, 9, 0, 0), (9, 0, 0, 1), (9, 0, 0, 1), (9, 0, 0, 1)), (1, 1, 1), (10, 0, 0, 0), 0, 0, 90.0),
    (9, ((1, 8, 0, 0), (8, 0, 0, 1), (8, 0, 0, 1), (8, 0, 0, 1)), (1, 1, 1), (9, 0, 0, 0), 0, 0, 88.9),
    (0, ((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)), (0, 0, 0), (0, 0, 0, 0), 0, 0, None)]
HAND_TOTAL = dict(rows=37, stages=((4, 32, 0, 1), (19, 13, 1, 4), (18, 11, 3, 5), (22, 5, 5, 5)), dropped=(4, 7, 9), kinds=(22, 8, 2, 3), k_none=2, i_none=3, docs_rows=4, docs_u90=1,
                  rates=(51.4, 48.6, 59.5, 13.5, 24.3, 5.4))
HEADINGS_SEEN = set([u"連結貸借対照表", u"損益計算書", u"連結損益計算書及び連結包括利益計算書", u"注記事項", u"連結株主資本等変動計算書", u"株主資本等変動計算書",
                     u"連結キャッシュ・フロー計算書", u"キャッシュ・フロー計算書", u"連結損益計算書"])
INDUSTRY_SEEN = set([u"cte", u"bk1", u"zzz"])


def xsd_name(no):
    return "XBRL/PublicDoc/jpcrp030000-asr-001_E9999%d-000_2026-03-31_01_2026-06-30.xsd" % no


def make_zip(path, no, texts, decoys=True):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(xsd_name(no), b"<schema/>")
        for n, t in texts:
            z.writestr("XBRL/PublicDoc/" + n.replace("_ixbrl.htm", "_honbun_E9999%d-000_ixbrl.htm" % no), t.encode("utf-8"))
        if decoys:        # PublicDoc の外の ixbrl・提出者のラベルと def(使わない)
            z.writestr("XBRL/AuditDoc/0000_audit_ixbrl.htm", file_of([(H_BS, [(u"資産", u"Assets")] * 3)]).encode("utf-8"))
            z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E9999%d-000_lab.xml" % no, linkbase([(u"jppfs_cor_Foo", R_STD, u"未登録", "ja")]))
            z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E9999%d-000_def.xml" % no, def_text([u"Foo"]))


def make_docs_dir(d, count=5):
    for i in range(count):
        make_zip(os.path.join(d, STEMS[i] + ".zip"), i + 1, DOCS_TEXTS[i]())
    other = os.path.join(d, "S1OTHER1.zip")
    with zipfile.ZipFile(other, "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


def patched_labels(ms, label_bytes=FAKE_LABELS):
    u"""``W.read_label_bytes`` を作り物のラベルへ差し替える。呼び出し側が元に戻す(戻り値が元の関数)。"""
    orig = ms.W.read_label_bytes
    ms.W.read_label_bytes = lambda d: (label_bytes, hashlib.sha256(label_bytes).hexdigest())
    return orig


def acc_hand(acc):
    return (sum(acc["stages"]["段 0"].values()), tuple(tuple(acc["stages"][s].values()) for s in ("段 0", "段 1", "段 2", "段 3")), tuple(acc["dropped"].values()),
            tuple(acc["kinds"].values()), acc["k_none"], acc["i_none"])


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XG1-1", (61, 68)), ("XG1-2", (68, 84)), ("XG1-3", (80, 93)), ("XG1-4", (5, 15)), ("XG1-5", (None, 3)), ("XG1-6", (None, 10)), ("XG1-7", (None, 25))])
SEAL_BOUND_TEXT = od([("XG1-1", u"61% 以上 68% 以下"), ("XG1-2", u"68% 以上 84% 以下"), ("XG1-3", u"80% 以上 93% 以下"), ("XG1-4", u"5% 以上 15% 以下"), ("XG1-5", u"3% 以下"),
                      ("XG1-6", u"10% 以下"), ("XG1-7", u"25 本以下")])
SEAL_KIND_LINES = (u"`貸借対照表` を含む → `bs`", u"`キャッシュ・フロー計算書` を含む → `cf`", u"`株主資本等変動計算書` を含む → `ss`", u"`損益計算書` か `包括利益計算書` を含む → `pl`")
SEAL_URL = u"https://www.fsa.go.jp/search/20251111/1c_Taxonomy.zip"
SEAL_ZIP_SHA = u"8d57f84802b20a8dc6a517ad6d4768270c294aa6991621d66cb5adb562df5de2"


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL or ms.PRIOR_RECORD_REL != PRIOR_RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    if ms.TAXZIP_URL != SEAL_URL or SEAL_URL not in seal or ms.TAXZIP_SHA256 != SEAL_ZIP_SHA or (u"sha256 `%s`" % SEAL_ZIP_SHA) not in seal:
        out.append(u"標準タクソノミの zip の url・sha256 が封と違う")
    if ms.TAXZIP_PATH != os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy-full", "2025-11-01", "1c_Taxonomy.zip") \
            or u"`~/.cache/audit-core/edinet-taxonomy-full/2025-11-01/1c_Taxonomy.zip`" not in seal:
        out.append(u"標準タクソノミの zip の置き場が封と違う")
    if ms.ZIP_MARK != u"/taxonomy/" or u"名の `/taxonomy/` より後ろの字で呼ぶ" not in seal:
        out.append(u"zip の中の file の呼び方が封と違う")
    if ms.XSD_NAME != u"jppfs/2025-11-01/jppfs_cor_2025-11-01.xsd" or u"`jppfs/2025-11-01/jppfs_cor_2025-11-01.xsd` の `xsd:element` の `name`・`type`・`abstract`" not in seal:
        out.append(u"要素の表の file が封と違う")
    if ms.DEF_NAME != u"jppfs/2025-11-01/r/%s/jppfs_%s_cm_2025-11-01_def_%s.xml" or u"`jppfs/2025-11-01/r/{I}/jppfs_{I}_cm_2025-11-01_def_{K}.xml`" not in seal \
            or tuple(ms.KINDS) != (u"bs", u"pl", u"ss", u"cf") or u"K は `bs`・`pl`・`ss`・`cf`" not in seal:
        out.append(u"科目の一覧の file の名の型・K が封と違う")
    if ms.HREF_RE.pattern != u'xlink:href="[^"]*#jppfs_cor_([^"]*)"' or u"`#jppfs_cor_` に続く局所名の集まり" not in seal:
        out.append(u"科目の一覧の読み方が封と違う")
    if tuple(ms.EXCLUDED_TYPES) != (u"nonnum:domainItemType", u"xbrli:stringItemType") or u"`type` が `nonnum:domainItemType` でも `xbrli:stringItemType` でもない" not in seal \
            or u"`abstract` が `true` でなく" not in seal:
        out.append(u"段 1 の除く要素が封と違う")
    if ms.HEAD_RE.pattern != u"【([^】]{0,40})】" or u"`【([^】]{0,40})】` に当たる所を見出しとする" not in seal or u"同じ file の中で、行の位置より前に在る最後の見出し" not in seal:
        out.append(u"見出しの拾い方が封と違う")
    want_rules = ((u"貸借対照表", "bs"), (u"キャッシュ・フロー計算書", "cf"), (u"株主資本等変動計算書", "ss"), (u"損益計算書", "pl"), (u"包括利益計算書", "pl"))
    if tuple(ms.KIND_RULES) != want_rules:
        out.append(u"見出しの 5 つの決めの字・順が門と違う")
    for line in SEAL_KIND_LINES:
        if line not in seal:
            out.append(u"封に見出しの決めの行が無い: %s" % line)
    pos = [seal.find(line) for line in SEAL_KIND_LINES]
    if min(pos) < 0 or pos != sorted(pos) or u"上から先に当たったもの" not in seal:
        out.append(u"封の見出しの決めの順が違う")
    if ms.CONSOLIDATED_WORD != u"連結" or u"見出しの字に `連結` が在れば" not in seal:
        out.append(u"連結の字が封と違う")
    if ms.DEI_CONSOLIDATED != DEI_C or ms.DEI_SINGLE != DEI_S or (u"`%s`" % DEI_C) not in seal or (u"`%s`" % DEI_S) not in seal:
        out.append(u"DEI の name 2 つが封と違う")
    if tuple(ms.INDUSTRY_ALIAS) != ((u"cte", u"cai"),) or u"`cte` は `cai` に読み替える" not in seal:
        out.append(u"cte → cai が封と違う")
    if ms.IXBRL_SUFFIX != u"_ixbrl.htm" or ms.PUBLICDOC != u"XBRL/PublicDoc/" or u"PublicDoc の `_ixbrl.htm` を file 名の昇順に読んで最初に空でなかったもの" not in seal:
        out.append(u"DEI を読む file が封と違う")
    if ms.ROWS_WANT != 16763 or u"67 本の合計で 16763 行。違えば script は止まる" not in seal:
        out.append(u"計算書の行の数 16763 が封と違う")
    if list(ms.STAGE0_WANT.items()) != [("U", 9571), ("A", 6880), ("W", 65), ("N", 247)] or u"U 9571・A 6880・W 65・N 247" not in seal:
        out.append(u"段 0 の 4 つの数が封と違う")
    if tuple(ms.STAGES) != (u"段 0", u"段 1", u"段 2", u"段 3") or list(ms.CLASSES) != [u"U", u"A", u"W", u"N"] or ms.DOCS_WANT != 67 or u"67" not in seal:
        out.append(u"段・類・書類の本数が封と違う")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [ln for ln in seal.splitlines() if re.match(r"^\| %s[ (]" % re.escape(k), ln)]
        if len(row_) != 1 or t not in row_[0]:
            out.append(u"封の予測の行の字が違う: %s" % k)
    if ms.U_DOC_THRESHOLD_PCT != 90 or u"段 3 の U の率が 90% 以上の書類は 25 本以下" not in seal:
        out.append(u"XG1-7 の 90% が封と違う")
    for rel in (SCRIPT_REL, RECORD_REL, GATE_REL):
        if rel not in seal:
            out.append(u"封に path が無い: %s" % rel)
    if u"docID・会社の名・EDINET コード・行の字・見出しの字・要素の名・業種のコードの値は書かない" not in seal or u"engine の指紋" not in seal or u"材料の並びの sha256" not in seal:
        out.append(u"封の記録の項目・禁止の字が違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    want_phrases = (u"専用の道具が組んだ後の字", u"DEI から読む", u"業種の段は、ほぼ 1 つの業種でしか試されない", u"2025-11-01 版の 1 つだけ", u"期・連結か個別か", u"「XBRL を作れる」")
    if len(ms.LIMITS) != 6 or any(p not in sec7 for p in want_phrases) or any(p not in u"".join(ms.LIMITS) for p in want_phrases):
        out.append(u"限界の 6 行が封 §7 と違う")
    return out


def stage0_problems(ms=None):
    u"""段 0 の 4 つの数・16763 は、前の便の記録(repo の中)から読んだ数と同じ。"""
    ms = ms or MS
    with io.open(os.path.join(ROOT, PRIOR_RECORD_REL), encoding="utf-8") as fh:
        prior = json.load(fh, object_pairs_hook=od)
    agg = prior[u"集計"]
    out = []
    if agg[u"計算書の行の数"] != ms.ROWS_WANT or list(agg[u"類別(表 L2)"].values()) != list(ms.STAGE0_WANT.values()) or list(agg[u"類別(表 L2)"].keys()) != list(ms.STAGE0_WANT.keys()):
        out.append(u"script の 16763・段 0 の 4 つの数が前の便の記録と違う")
    return out


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
    u"""封 ⊏ script・この門(足した commit が封の後)。未 commit は赤。"""
    others = list(ORDER_FILES) if others is None else others
    return list(PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % ln for ln in rc.stdout.splitlines() if ln.strip()]


# ======================================================================== 2. 純関数
def tax_pure_problems(ms=None):
    u"""要素の表・段 1 の残す集まり・科目の一覧・和集合・段 1〜3 を、手で決めた値と照らす。"""
    ms = ms or MS
    out = []
    x = ms.build_x(xsd_bytes())
    if x.get(u"Assets") != (MONETARY, u"false") or x.get(u"ShareQty") != (u"xbrli:sharesItemType", u"") or x.get(u"AssetsDom") != (u"nonnum:domainItemType", u"false") or len(x) != len(FAKE_X):
        out.append(u"要素の表が違う: %s" % len(x))
    num = ms.numeric_elements(x)
    if num != set([u"Assets", u"OthPl", u"OthBk1Pl", u"OthBs", u"OthNone", u"ChgSs", u"ChgSs2", u"ChgPl", u"CfItem", u"CfOther", u"ShareQty"]):
        out.append(u"段 1 が残す要素の集まりが違う: %s" % sorted(num))
    if ms.build_c(def_text([u"Assets", u"OthBs"])) != set([u"Assets", u"OthBs"]) or ms.build_c(def_text([])) != set():
        out.append(u"科目の一覧の読み取りが違う(役割の href・jpcrp の href を混ぜない)")
    if ms.build_c(u'<x xlink:href="a.xsd#jppfs_cor_P"/><x xlink:href="b.xsd#jppfs_cor_P"/><x xlink:href="c.xsd#jppfs_cor_Q_R"/>') != set([u"P", u"Q_R"]):
        out.append(u"科目の一覧の局所名の読み取りが違う")
    un = ms.union_by_kind(dict(FAKE_C))
    if un != UNION:
        out.append(u"どれかの業種の C(·, K) の和集合が違う: %s" % un)
    tax = fake_tax(ms)
    if tax["folders"] != set(FAKE_FOLDERS) or tax["c"] != FAKE_C or tax["union"] != UNION:
        out.append(u"make_tax が違う")
    sig = lambda f: tuple(inspect.signature(f).parameters)                                   # noqa: E731
    if sig(ms.stage1) != ("cand0", "tax") or sig(ms.stage2) != ("cand1", "kind", "tax") or sig(ms.stage3) != ("cand1", "cand2", "kind", "ind", "tax") or sig(ms.narrow) != ("cand0", "kind", "ind", "tax"):
        out.append(u"段の関数の引数が封と違う(E は渡さない)")
    c0 = set(FAKE_L2[u"資産"])
    if ms.stage1(c0, tax) != {u"Assets"} or ms.stage1({u"CashAbs"}, tax) != set() or ms.stage1(set(), tax) != set() or ms.stage1({u"ShareQty"}, tax) != {u"ShareQty"}:
        out.append(u"段 1 が違う(abstract・domainItemType・stringItemType・要素の表に無い要素を除く)")
    oth = set(FAKE_L2[u"その他"])
    chg = set(FAKE_L2[u"当期変動額"])
    if ms.stage2(oth, "pl", tax) != {u"OthPl", u"OthBk1Pl"} or ms.stage2(oth, "bs", tax) != {u"OthBs"} or ms.stage2(oth, None, tax) != oth or ms.stage2(chg, "ss", tax) != {u"ChgSs", u"ChgSs2"}:
        out.append(u"段 2 が違う(どれかの業種の C(·, K)。K が決まらない行は段 1 のまま)")
    c2 = ms.stage2(oth, "pl", tax)
    if ms.stage3(oth, c2, "pl", "cai", tax) != {u"OthPl"} or ms.stage3(oth, c2, "pl", "bk1", tax) != {u"OthBk1Pl"}:
        out.append(u"段 3 が違う(C(I, K) で絞る)")
    if ms.stage3(oth, c2, "pl", None, tax) != c2 or ms.stage3(oth, c2, None, "cai", tax) != c2 or ms.stage3(oth, c2, None, None, tax) != c2:
        out.append(u"段 3 が違う(I か K が決まらない行は段 2 のまま)")
    c2s = ms.stage2(chg, "ss", tax)
    if ms.stage3(chg, c2s, "ss", "bk1", tax) != c2s or ms.stage3(chg, c2s, "ss", "emp", tax) != c2s or ms.stage3(chg, c2s, "ss", "cai", tax) != {u"ChgSs"} or ms.stage3(chg, c2s, "ss", "cmd", tax) != {u"ChgSs2"}:
        out.append(u"段 3 が違う(C(I, K) が無いときは段 2 のまま・在るときは C(I, K))")
    if ms.narrow(c0, "bs", "cai", tax) != ({u"Assets"}, {u"Assets"}, {u"Assets"}) or ms.stage2(c0, "bs", tax) != {u"Assets", u"AssetsAbs"}:
        out.append(u"段 2 は段 1 の残りに掛ける(abstract の要素は科目の一覧に載っていても段 1 で落ちている)")
    c1, c2n, c3 = ms.narrow(oth, "pl", "cai", tax)
    if (c1, c2n, c3) != (oth, {u"OthPl", u"OthBk1Pl"}, {u"OthPl"}):
        out.append(u"narrow が 3 つの段を順に通していない")
    if ms.narrow({u"Assets", u"AssetsAbs"}, "bs", "bk1", tax) != ({u"Assets"}, {u"Assets"}, set()):
        out.append(u"narrow: 段 3 で空になる行(C(bk1, bs) に Assets が無い)")
    return out


def classify_problems(ms=None):
    u"""類 U・A・W・N・落とした行・段を進めて U が減る例。"""
    ms = ms or MS
    out = []
    for T, E, cand, want in ((u"t", u"E1", {u"E1"}, "U"), (u"t", u"E1", {u"E1", u"E2"}, "A"), (u"t", u"E9", {u"E1"}, "W"), (u"t", u"E9", {u"E1", u"E2"}, "W"), (u"t", u"E1", set(), "N"), (u"t", u"", set(), "N")):
        if ms.classify_stage(T, E, cand) != want:
            out.append(u"classify_stage(%s, %s) が %s(手で決めた値は %s)" % (sorted(cand), E, ms.classify_stage(T, E, cand), want))
    for E, c0, c, want in ((u"E1", {u"E1", u"E2"}, {u"E2"}, True), (u"E1", {u"E1", u"E2"}, {u"E1"}, False), (u"E1", {u"E1"}, set(), True), (u"E9", {u"E1"}, {u"E1"}, False),
                           (u"E9", {u"E1"}, set(), False), (u"E9", set(), set(), False)):
        if ms.is_dropped(E, c0, c) is not want:
            out.append(u"is_dropped(%s, %s, %s) が %s でない" % (E, sorted(c0), sorted(c), want))
    # 段を進めて U が減る: 資産・Assets の行は段 2 まで U。現金・CashAbs の行は段 0 で U → 段 1 で N
    tax = fake_tax(ms)
    acc = ms.new_doc()
    ms.add_row(acc, u"現金", u"CashAbs", set(FAKE_L2[u"現金"]), "bs", "cai", tax)
    if tuple(acc["stages"][s]["U"] for s in ms.STAGES) != (1, 0, 0, 0) or tuple(acc["dropped"].values()) != (1, 1, 1):
        out.append(u"段を進めて U が減る例が違う: %s" % (acc_hand(acc),))
    return out


def heading_problems(ms=None):
    u"""見出しの拾い方(行より前の最後・同じ file の中だけ・タグを除いた位置・始まりが同じなら前に数えない・40 字まで)と、種類 K・業種 I・DEI の読み方。"""
    ms = ms or MS
    out = []
    g = lambda s: [h for _r, h in ms.file_rows(s)]                                      # noqa: E731
    tr = u"<tr><td>a</td></tr>"
    if g(u"<p>【貸借対照表】</p>" + tr + u"<p>【損益計算書】</p>" + tr + tr) != [u"貸借対照表", u"損益計算書", u"損益計算書"]:
        out.append(u"見出しが「行より前の最後」でない")
    if g(tr + u"<p>【損益計算書】</p>" + tr) != [None, u"損益計算書"]:
        out.append(u"見出しの前の行に見出しが付く(か最初の行が None でない)")
    if g(u"<p>【貸借対照表】</p>" + tr + u"<p>【注記事項】</p>" + tr) != [u"貸借対照表", u"注記事項"]:
        out.append(u"種類を決めない見出しが最後でも、その見出しを前の見出しに戻している")
    if g(u"<p>【連結<span>損益</span>計算書】</p><table>" + tr + u"</table>") != [u"連結損益計算書"]:
        out.append(u"見出しの中のタグを除いていない")
    # 行の頭より前のタグの長さ: 行の前に長い属性のタグが並び、見出しは行の後ろに在る(タグを除かない位置で比べると前に数えてしまう)
    long_tr = u'<tr class="%s" style="%s"><td>a</td></tr>' % (u"x" * 200, u"y" * 200)
    if g(long_tr + u"<p>【損益計算書】</p>") != [None]:
        out.append(u"位置がタグを除いた字の長さでない(行の後ろの見出しを前に数えた)")
    # 同じ位置は前に数えない: 見出しが行の中に在る(行の頭までの字の長さと同じ位置から始まる)
    two = g(u"<p>【損益計算書】</p><table><tr><td>【貸借対照表】</td><td>x</td></tr><tr><td>a</td></tr></table>")
    if two != [u"損益計算書", u"貸借対照表"]:
        out.append(u"見出しの始まりが行の位置と同じとき前に数えている: %s" % two)
    long_head = u"【" + u"あ" * 41 + u"】"
    if g(u"<p>【貸借対照表】</p><p>" + long_head + u"</p>" + tr) != [u"貸借対照表"] or g(u"<p>【" + u"あ" * 40 + u"】</p>" + tr) != [u"あ" * 40]:
        out.append(u"見出しの長さの上限(40 字)が違う")
    if g(u"<p>[貸借対照表]</p>" + tr) != [None] or g(u"<p>【】</p>" + tr) != [u""]:
        out.append(u"見出しの括弧の形が違う")
    # ix の行は engine の _TR_RE と同じ切り方
    if [r for r, _h in ms.file_rows(u"<TR >x</TR><tr>y</tr>")] != [u"<TR >x</TR>", u"<tr>y</tr>"]:
        out.append(u"行の切り方が engine の _TR_RE と違う")
    for h, want in ((u"連結貸借対照表", "bs"), (u"連結損益計算書及び連結包括利益計算書", "pl"), (u"連結包括利益計算書", "pl"), (u"連結キャッシュ・フロー計算書", "cf"), (u"ｷｬｯｼｭ･ﾌﾛｰ計算書", "cf"),
                    (u"連 結 株主資本等変動計算書", "ss"), (u"貸借対照表及び損益計算書", "bs"), (u"損益計算書及び株主資本等変動計算書", "ss"), (u"キャッシュ・フロー計算書及び貸借対照表", "bs"),
                    (u"損益計算書(注)", "pl"), (u"連結損益計算書\u3000", "pl"), (u"経営指標等", None), (u"注記事項", None), (u"", None), (None, None)):
        if ms.kind_of(h) != want:
            out.append(u"kind_of(%r) が %r(手で決めた値は %r)" % (h, ms.kind_of(h), want))
    fol = set(FAKE_FOLDERS)
    for h, d, want in ((u"連結貸借対照表", (u"cte", u"bk1"), "cai"), (u"貸借対照表", (u"cte", u"bk1"), "bk1"), (u"連 結 貸借対照表", (u"cte", u"bk1"), "cai"), (u"連結貸借対照表", (u"", u"bk1"), None),
                       (u"貸借対照表", (u"cmd", u""), None), (u"連結貸借対照表", (u"zzz", u"bk1"), None), (u"貸借対照表", (u"bk1", u"zzz"), None), (u"連結貸借対照表", (u"cai", u""), "cai"),
                       (u"貸借対照表", (u"", u"cte"), "cai"), (u"貸借対照表", (u"", u"emp"), "emp"), (None, (u"cte", u"bk1"), None)):
        if ms.industry_of(h, d, fol) != want:
            out.append(u"industry_of(%r, %r) が %r(手で決めた値は %r)" % (h, d, ms.industry_of(h, d, fol), want))
    n = u"jpdei_cor:Foo"
    cases = [
        (u'<ix:nonNumeric name="%s" contextRef="c"> <span>C</span>T<b>E</b> </ix:nonNumeric>' % n, u"cte"),
        (u'<ix:nonNumeric name="%s" contextRef="c"></ix:nonNumeric><ix:nonNumeric name="%s" contextRef="d"> BK1 </ix:nonNumeric>' % (n, n), u"bk1"),
        (u'<ix:nonNumeric name="%s" contextRef="c">A</ix:nonNumeric><ix:nonNumeric name="%s" contextRef="d">B</ix:nonNumeric>' % (n, n), u"a"),
        (u'<ix:nonNumeric name="%sX" contextRef="c">Z</ix:nonNumeric><ix:nonNumeric name="other" contextRef="c">Z</ix:nonNumeric>' % n, u""),
        (u'<ix:nonNumeric name="%s" contextRef="c">\u3000\u00a0 </ix:nonNumeric>' % n, u""),
        (u"", u""),
        (u'<ix:nonNumeric name="%s" contextRef="c">\n  CTE\n</ix:nonNumeric>' % n, u"cte"),
        (u'<ix:nonNumeric name="%s" contextRef="c">\r\n\t<span>\n BK1\n</span>\n</ix:nonNumeric>' % n, u"bk1"),
        (u'<ix:nonNumeric name="%s" contextRef="c">\n\n</ix:nonNumeric><ix:nonNumeric name="%s" contextRef="d">\nX\n</ix:nonNumeric>' % (n, n), u"x")]
    for text, want in cases:
        if ms.dei_value(text, n) != want:
            out.append(u"dei_value が %r(手で決めた値は %r): %s" % (ms.dei_value(text, n), want, text[:50]))
    t1 = dei(DEI_C, None) + dei(DEI_S, u"BK1")
    t2 = dei(DEI_C, u"CTE")
    t3 = dei(DEI_C, u"cmd") + dei(DEI_S, u"cmd")
    tn = dei_nl(DEI_C, u"CTE") + dei_nl(DEI_S, u"BK1")
    if ms.dei_values([("0b", tn), ("0a", dei(DEI_C, None))]) != (u"cte", u"bk1") or ms.industry_of(u"連結貸借対照表", ms.dei_values([("0a", tn)]), set(FAKE_FOLDERS)) != "cai" \
            or ms.industry_of(u"貸借対照表", ms.dei_values([("0a", tn)]), set(FAKE_FOLDERS)) != "bk1":
        out_.append(u"値が改行で挟まれた DEI を読めない(dei_values・industry_of)")
    if ms.dei_values([("0c", t3), ("0a", t1), ("0b", t2)]) != (u"cte", u"bk1") or ms.dei_values([("0b", t2), ("0c", t3)]) != (u"cte", u"cmd") or ms.dei_values([("0a", t1)]) != (u"", u"bk1") \
            or ms.dei_values([]) != (u"", u""):
        out.append(u"dei_values が「file 名の昇順で最初に空でない値」でない")
    return out


def check_expected_problems(ms=None):
    ms = ms or MS
    out = []
    ok = ms.new_doc()
    for c, n in zip(ms.CLASSES, ms.STAGE0_WANT.values()):
        ok["stages"]["段 0"][c] = n
    prior = od([(u"集計", od([(u"計算書の行の数", 16763), (u"類別(表 L2)", od(zip(ms.CLASSES, ms.STAGE0_WANT.values())))]))])
    if stops(ms, ms.check_expected, ok, 16763, ms.STAGE0_WANT, prior):
        out.append(u"合う数で止まる")
    bad_rows = ms.new_doc()
    bad_rows["stages"]["段 0"].update(U=9571, A=6880, W=65, N=246)
    if not stops(ms, ms.check_expected, bad_rows, 16763, ms.STAGE0_WANT, None):
        out.append(u"計算書の行の合計が 16763 でないのに止まらない")
    if not stops(ms, ms.check_expected, bad_rows, 16763, None, None):
        out.append(u"計算書の行の合計だけが違う呼びで止まらない(段 0 の止めに隠れている)")
    swapped = ms.new_doc()
    swapped["stages"]["段 0"].update(U=9570, A=6881, W=65, N=247)
    if not stops(ms, ms.check_expected, swapped, 16763, ms.STAGE0_WANT, None):
        out.append(u"段 0 の U・A が封の字と違う(合計は同じ)のに止まらない")
    other = od([(u"集計", od([(u"計算書の行の数", 16763), (u"類別(表 L2)", od(zip(ms.CLASSES, (9572, 6879, 65, 247))))]))])
    if not stops(ms, ms.check_expected, ok, 16763, ms.STAGE0_WANT, other):
        out.append(u"便 XG0 の記録の数と違うのに止まらない")
    if stops(ms, ms.check_expected, bad_rows, None, None, None):
        out.append(u"止めを外した呼びで止まる(作り物の置き場の呼び)")
    return out


# ======================================================================== 3. 行・書類 → 数える
def row_problems(ms=None):
    u"""手で決めた行ごとの値を、1 行ずつ 1 本の file(見出しは書類の file の頭)に入れて数え、照らす。"""
    ms = ms or MS
    out = []
    tax = fake_tax(ms)
    for name, doc, label, e, h, classes, dropped, kind, inone in HAND_ROWS:
        d = DEI_A if doc == "A" else DEI_B
        text = dei(DEI_C, d[0].upper() or None) + dei(DEI_S, d[1].upper() or None) + file_of([(h, [(label, e)])])
        acc = ms.count_doc([("0a_ixbrl.htm", text)], FAKE_L2, tax)
        got_classes = u"".join(c for s in ms.STAGES for c, n in acc["stages"][s].items() if n)
        want_k = tuple(1 if k == kind else 0 for k in ms.KINDS)
        if got_classes != classes or tuple(acc["dropped"].values()) != dropped or tuple(acc["kinds"].values()) != want_k or acc["k_none"] != (1 if kind is None else 0) or acc["i_none"] != inone:
            out.append(u"行 %s が手で決めた値と違う: %s %s" % (name, got_classes, acc_hand(acc)))
    return out


def doc_problems(ms=None):
    ms = ms or MS
    out = []
    tax = fake_tax(ms)
    for i, fn in enumerate(DOCS_TEXTS):
        secret = (set(), set(), [], set(), set(), set())
        acc = ms.count_doc(fn(), FAKE_L2, tax, secret)
        if acc_hand(acc) != HAND_DOCS[i][:6]:
            out.append(u"書類 %d の数が手で数えた値と違う: %s" % (i + 1, acc_hand(acc)))
        if i == 0 and (secret[4] != HEADINGS_SEEN - set([u"連結損益計算書"]) or secret[5] != set([u"cte", u"bk1"])):
            out.append(u"secret の見出し・業種の値が違う: %s %s" % (sorted(secret[4]), sorted(secret[5])))
    # PublicDoc の外・提出者のラベルと def を使わない(zip を通す。decoy 有りと無しで同じ)
    with Temp() as d:
        p1, p2 = os.path.join(d, "a.zip"), os.path.join(d, "b.zip")
        make_zip(p1, 1, doc_a_texts(), decoys=True)
        make_zip(p2, 1, doc_a_texts(), decoys=False)
        res = []
        for p in (p1, p2):
            with zipfile.ZipFile(p) as z:
                res.append(acc_hand(ms.count_doc(ms.doc_texts(z), FAKE_L2, tax)))
        if res[0] != res[1] or res[0] != HAND_DOCS[0][:6]:
            out.append(u"PublicDoc の外の ixbrl か提出者の file を読んでいる: %s" % (res,))
    return out


def totals_problems(ms=None):
    ms = ms or MS
    out = []
    tax = fake_tax(ms)
    accs = [ms.count_doc(fn(), FAKE_L2, tax) for fn in DOCS_TEXTS]
    t = ms.totals(accs)
    h = HAND_TOTAL
    if ms.doc_rows(t) != h["rows"] or tuple(tuple(t["stages"][s].values()) for s in ms.STAGES) != h["stages"] or tuple(t["dropped"].values()) != h["dropped"] \
            or tuple(t["kinds"].values()) != h["kinds"] or t["k_none"] != h["k_none"] or t["i_none"] != h["i_none"]:
        out.append(u"合計が手で数えた値と違う: %s" % (acc_hand(t),))
    return out


# ======================================================================== 4. 標準タクソノミの zip
def taxzip_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        p = os.path.join(d, "t.zip")
        make_tax_zip(p)
        tax, sha, mat = ms.load_tax(p, check_sha=False)
        if tax["c"] != FAKE_C or tax["folders"] != set(FAKE_FOLDERS) or tax["union"] != UNION or tax["numeric"] != ms.numeric_elements(ms.build_x(xsd_bytes())):
            out.append(u"zip から読んだ表が作り物の値と違う(別の日付・cal・def の枝・cm でない file・/taxonomy/ の外を使った)")
        if sha != hashlib.sha256(open(p, "rb").read()).hexdigest() or list(mat.values()) != [len(FAKE_X), 11, 4, 8]:
            out.append(u"材料の数が手で数えた値と違う: %s" % list(mat.values()))
        if not stops(ms, ms.load_tax, p):
            out.append(u"zip の sha256 が封と違うのに load_tax が止まらない")
        if not stops(ms, ms.read_taxzip, p):
            out.append(u"zip の sha256 が封と違うのに read_taxzip が止まらない")
        if not stops(ms, ms.read_taxzip, os.path.join(d, "none.zip")):
            out.append(u"zip が無いのに止まらない")
        q = os.path.join(d, "q.zip")
        with zipfile.ZipFile(q, "w") as z:
            z.writestr(TOP + u"jppfs/2025-11-01/r/cai/x.xml", b"<a/>")
        if not stops(ms, ms.load_tax, q, False):
            out.append(u"要素の表の xsd が zip に無いのに止まらない")
    for nm, want in ((u"金融庁/taxonomy/jppfs/a.xsd", u"jppfs/a.xsd"), (u"taxonomy/jppfs/a.xsd", None), (u"readme.txt", None), (u"x/taxonomy_old/jppfs/a.xsd", None)):
        if ms.rel_name(nm) != want:
            out.append(u"rel_name(%r) が %r(手で決めた値は %r)" % (nm, ms.rel_name(nm), want))
    return out


# ======================================================================== 5. 記録
def clean_problems(ms=None):
    ms = ms or MS
    out = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"材料の sha256", u"a" * 64)])]), (u"git", u"b" * 40)])
    secret = ({u"現金", u"投資有価証券(注)"}, {u"CashAndDeposits"}, [u"zzdoc"], {u"E99991"}, {u"連結貸借対照表", u"注記"}, {u"cte", u"zzz"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out.append(u"きれいな記録で止まる(sha256 の 16 進を含む)")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"x", [od([(u"company", 1)])])])), (u"禁止の欄(label)", od([(u"label", 1)])),
        (u"禁止の欄(行の字)", od([(u"行の字", 1)])), (u"禁止の欄(要素の名)", od([(u"要素の名", 1)])), (u"禁止の欄(会社の名)", od([(u"会社の名", 1)])),
        (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])),
        (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])),
        (u"材料の要素の名", od([(u"x", u"a CashAndDeposits b")])),
        (u"材料の行の字(短い字は全部一致)", od([(u"x", u"現金")])), (u"材料の行の字(長い字は部分一致)", od([(u"x", u"文 投資有価証券(注) 文")])),
        (u"見出しの字(全部一致)", od([(u"x", u"注記")])), (u"見出しの字(部分一致)", od([(u"x", u"表 連結貸借対照表 表")])),
        (u"業種のコードの値(cte)", od([(u"x", u"cte")])), (u"業種のコードの値(zzz を文の中に)", od([(u"x", u"a zzz b")]))]
    for what, rec in cases:
        if not stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out.append(u"%s が止まらない" % what)
        if not stops(ms, ms.record_text, rec, secret):
            out.append(u"%s が record_text で止まらない" % what)
    for what, rec in ((u"短い見出しの部分(注記は 5 字未満なので部分一致では止めない)", od([(u"x", u"注記事項")])), (u"業種の値の部分だけ(別の語の一部)", od([(u"x", u"xctey")])),
                      (u"短い字の部分(現金は 5 字未満)", od([(u"x", u"現金化")]))):
        if stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out.append(u"%s で止まる(止め過ぎ)" % what)
    with Temp() as d:
        p = os.path.join(d, "r.json")
        bad = od([(u"x", u"E12345")])
        if not stops(ms, ms.write_record, p, bad) or os.path.exists(p):
            out.append(u"禁止の字が在る記録を書いた(書く前の検査)")
        bad2 = od([(u"x", u"連結貸借対照表")])
        if not stops(ms, ms.write_record, p, bad2, secret) or os.path.exists(p):
            out.append(u"見出しの字が在る記録を書いた(書く前の検査)")
        good = od([(u"x", 1)])
        ms.write_record(p, good)
        if not stops(ms, ms.write_record, p, good):
            out.append(u"記録が既に在るのに書き直せる")
        q = os.path.join(d, "q.json")
        orig = ms.write_exclusive
        ms.write_exclusive = lambda path, data: orig(path, data + b" E12345")
        try:
            stopped = stops(ms, ms.write_record, q, good)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(q):
            out.append(u"書いた後の検査が止めない(か file を消さない)")
        # 書く前の検査: 書く字を検査と無関係なきれいな字に替えても、危ない記録なら書く前に止める(後の検査だけに頼らない)
        v = os.path.join(d, "v.json")
        ms.write_exclusive = lambda path, data: orig(path, b"{}")
        try:
            stopped = stops(ms, ms.write_record, v, bad)
        finally:
            ms.write_exclusive = orig
        if not stopped:
            out.append(u"書く前の検査が止めない(書いた後の検査だけで止まっている)")
        # 書いた後だけが見出しの字を見る: 書いた字へ見出しを混ぜる(書く前は通る)
        w = os.path.join(d, "w.json")
        ms.write_exclusive = lambda path, data: orig(path, data + u" 連結貸借対照表".encode("utf-8"))
        try:
            stopped = stops(ms, ms.write_record, w, good, secret)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(w):
            out.append(u"書いた後の検査が見出しの字を止めない(か file を消さない)")
    return out


def e2e_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    orig = patched_labels(ms)
    try:
        with Temp() as d:
            docs, rec_path, tz = os.path.join(d, "docs"), os.path.join(d, "rec", "r.json"), os.path.join(d, "t.zip")
            os.makedirs(docs)
            make_docs_dir(docs)
            make_tax_zip(tz)
            kw = dict(root=d, docs=docs, taxonomy=os.path.join(d, "tax"), taxzip=tz, check_sha=False, say=lambda *a: None)
            if not stops(ms, ms.run, out=rec_path, **kw) or os.path.exists(rec_path):
                out.append(u"書類が 67 本でないのに run が止まらない(か記録を書いた)")
            if not stops(ms, ms.run, out=rec_path, want=5, expect=True, **kw) or os.path.exists(rec_path):
                out.append(u"計算書の行の合計が 16763 でないのに run が止まらない(か記録を書いた)")
            rec = ms.run(out=rec_path, want=5, expect=False, **kw)
            now = ms.check(rec_path=rec_path, want=5, expect=False, **kw)
            if ms.dumps(rec) != ms.dumps(now):
                out.append(u"記録と --check の数え直しが違う")
            mat = rec[u"材料"]
            if (mat[u"書類の本数"], mat[u"書類の file 名の並びの sha256"], mat[u"表 L2 のラベルの字の数"], mat[u"標準タクソノミの zip の sha256"], mat[u"要素の表の要素の数"], mat[u"段 1 が残す要素の数"],
                    mat[u"業種の folder の数"], mat[u"科目の一覧の数"]) != (5, ORDER_SHA, len(FAKE_L2), hashlib.sha256(open(tz, "rb").read()).hexdigest(), len(FAKE_X), 11, 4, 8):
                out.append(u"材料の欄が手で数えた値と違う: %s" % dict(mat))
            if mat[u"標準ラベルの file の sha256"] != hashlib.sha256(FAKE_LABELS).hexdigest():
                out.append(u"ラベルの file の sha256 が読んだ bytes のものでない")
            for i, hd in enumerate(HAND_DOCS):
                r = rec[u"書類"][i]
                got = (r[u"番号"], r[u"計算書の行の数"], tuple(tuple(r[u"段ごとの類別"][s].values()) for s in ms.STAGES), tuple(r[u"段ごとの落とした行"].values()), tuple(r[u"種類 K ごとの行"].values()),
                       r[u"K が決まらない行"], r[u"K が決まり I が決まらない行"], r[u"段 3 の U の率(%)"])
                want = (i + 1, hd[0], hd[1], hd[2], hd[3], hd[4], hd[5], hd[6])
                if got != want:
                    out.append(u"書類 %d の記録が手で数えた値と違う: %s" % (i + 1, got))
            t = HAND_TOTAL
            agg = rec[u"集計"]
            if (agg[u"計算書の行の数"], tuple(tuple(agg[u"段ごとの類別"][s].values()) for s in ms.STAGES), tuple(agg[u"段ごとの落とした行"].values()), tuple(agg[u"種類 K ごとの行"].values()),
                    agg[u"K が決まらない行"], agg[u"K が決まり I が決まらない行"], agg[u"計算書の行が 1 行以上在る書類の数"]) != (t["rows"], t["stages"], t["dropped"], t["kinds"], t["k_none"], t["i_none"], t["docs_rows"]):
                out.append(u"集計が手で数えた値と違う: %s" % dict(agg))
            pv = list([v for k, v in rec.items() if k.startswith(u"予測の判定に要る数")][0].values())
            wr = t["rates"]
            nums = ((t["stages"][1][0], wr[0]), (t["stages"][2][0], wr[1]), (t["stages"][3][0], wr[2]), (t["stages"][3][1], wr[3]), (t["dropped"][2], wr[4]), (t["k_none"], wr[5]))
            for j, (n, rate) in enumerate(nums):
                if (pv[j][u"行"], pv[j][u"分母"], pv[j][u"%"]) != (n, t["rows"], rate):
                    out.append(u"XG1-%d の数が手で数えた値と違う: %s" % (j + 1, dict(pv[j])))
            if (pv[6][u"書類"], pv[6][u"分母"]) != (t["docs_u90"], t["docs_rows"]):
                out.append(u"XG1-7 の数が手で数えた値と違う(90.0% は含む・88.9% は含まない・行の無い書類は分母に入れない)")
            text = io.open(rec_path, encoding="utf-8").read()
            for leak in STEMS + [u"E9999", u"Assets", u"現金", u"資産", u"貸借対照表", u"注記事項", u"cte", u"bk1", u"zzz", u"S1OTHER1"]:
                if leak in text:
                    out.append(u"記録に材料の字が在る: %s" % leak)
            if not stops(ms, ms.run, out=rec_path, want=5, expect=False, **kw):
                out.append(u"記録が既に在るのに run が止まらない")
            bad = text.replace(u'"計算書の行の数": 15', u'"計算書の行の数": 16', 1)
            bp = os.path.join(d, "bad.json")
            with io.open(bp, "w", encoding="utf-8") as fh:
                fh.write(bad)
            if bad == text or not stops(ms, ms.check, rec_path=bp, want=5, expect=False, **kw):
                out.append(u"数を変えた記録で --check が止まらない")
            make_zip(os.path.join(docs, STEMS[1] + ".zip"), 2, doc_a_texts())                      # 置き場の書類を替える
            if not stops(ms, ms.check, rec_path=rec_path, want=5, expect=False, **kw):
                out.append(u"置き場の書類を変えても --check が止まらない")
            if not stops(ms, ms.check, rec_path=os.path.join(d, "none.json"), want=5, expect=False, **kw):
                out.append(u"記録が無いのに --check が止まらない")
    finally:
        ms.W.read_label_bytes = orig
    return out


def secret_problems(ms=None):
    u"""本番の ``build_record`` が作る secret(行の字・要素の名・docID・EDINET コード・見出しの字・業種の値)の配線と、``check()`` が secret を ``check_clean`` に渡していること。作り物の置き場だけ。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    orig = patched_labels(ms)
    try:
        with Temp() as d:
            docs, rec_path, tz = os.path.join(d, "docs"), os.path.join(d, "rec", "r.json"), os.path.join(d, "t.zip")
            os.makedirs(docs)
            make_docs_dir(docs)
            make_tax_zip(tz)
            kw = dict(root=d, docs=docs, taxonomy=os.path.join(d, "tax"), taxzip=tz, check_sha=False, want=5, expect=False)
            rec, secret = ms.build_record(docs, os.path.join(d, "tax"), tz, 5, False, None, False)
            labels, elems, ids, ecodes, heads, inds = secret
            if list(ids) != STEMS:
                out.append(u"secret の docID の並びが作り物の置き場の書類と違う: %s" % (list(ids),))
            if set(ecodes) != set([u"E9999%d" % i for i in range(1, 6)]):
                out.append(u"secret の EDINET コードが作り物の xsd の名の 5 つと違う: %s" % (sorted(ecodes),))
            if not set([u"資産", u"現金", u"その他", u"当期変動額", u"株式数", u"現金同等物", u"未登録"]) <= set(labels) or u"Foo" not in elems or u"AssetsAbs" not in elems:
                out.append(u"secret の行の字・要素の名が作り物の行と違う")
            if heads != HEADINGS_SEEN:
                out.append(u"secret の見出しの字が違う(行を決めた見出しの NFKC・空白除きの字): %s" % sorted(heads))
            if inds != INDUSTRY_SEEN:
                out.append(u"secret の業種の値が違う(各書類で読んだ値): %s" % sorted(inds))
            real_build = ms.build_record
            for ln, (what, leak) in enumerate(((u"見出しの字(全部一致。5 字未満)", u"注記事項"), (u"見出しの字(部分一致)", u"a 連結貸借対照表 b"), (u"業種のコードの値", u"a cte b"), (u"要素の名", u"a CashAbs b"), (u"行の字", u"その他"))):
                leaky = od(rec)
                leaky[u"仕込み"] = leak
                lp = os.path.join(d, "leak_%d.json" % ln)
                with io.open(lp, "w", encoding="utf-8") as fh:
                    fh.write(ms.dumps(leaky))
                ms.build_record = lambda *a, **k: (leaky, secret)
                try:
                    stopped = stops(ms, ms.check, rec_path=lp, **kw, say=lambda *a: None)
                finally:
                    ms.build_record = real_build
                if not stopped:
                    out.append(u"check() が secret(%s)の仕込みで止まらない" % what)
            ms.run(out=rec_path, say=lambda *a: None, **kw)
            ms.check(rec_path=rec_path, say=lambda *a: None, **kw)
    finally:
        ms.W.read_label_bytes = orig
    return out


# ======================================================================== 6. 配線
STDLIB_OK = ("__future__", "argparse", "bisect", "collections", "hashlib", "importlib", "io", "json", "os", "re", "sys", "xml", "zipfile", "adapters")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess")
ENGINE_CALLED = ("_TR_RE",)
WALL_CALLED = ("classify", "row_status", "select_docs", "label_tables", "read_label_bytes", "check_clean", "order_sha256", "Stop")
WALL_NOT_COPIED = ("classify", "row_status", "select_docs", "label_tables", "read_label_bytes", "order_sha256", "norm_label")
STAGE_FUNCS = ("stage1", "stage2", "stage3", "narrow")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
WALL_NAME = "_xg1_tag_wall_2026_11_21"


def import_problems(src=None):
    u"""script の import は標準ライブラリと engine の 2 module と importlib だけ。前の便の関数は ``W.`` から呼び写さない。E は段の関数に渡さない。提出者の file を読まない。"""
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
                out.append(u"許さない module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    eng = sorted(a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "adapters.xbrl" for a in n.names)
    if eng != ["instance", "verify_document"]:
        out.append(u"engine から読む module が instance・verify_document の 2 つだけでない: %s" % eng)
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
    if ("os", "environ") in attrs or ("os", "getenv") in attrs:
        out.append(u"環境変数を読んでいる")
    for fn in ENGINE_CALLED:
        if ("I", fn) not in attrs:
            out.append(u"engine の %s を I から呼んでいない" % fn)
    for fn in WALL_CALLED:
        if ("W", fn) not in attrs:
            out.append(u"便 XG0 の %s を W から呼んでいない" % fn)
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in WALL_NOT_COPIED:
        if fn in funcs:
            out.append(u"便 XG0 の %s を script が自分で定義している(写している)" % fn)
    for fn in STAGE_FUNCS:
        f = funcs.get(fn)
        if f is None:
            out.append(u"段の関数 %s が無い" % fn)
            continue
        argn = [a.arg for a in f.args.args]
        used = set(x.id for x in ast.walk(f) if isinstance(x, ast.Name))
        if "E" in argn or "E" in used or any(a in ("e", "elem", "element") for a in argn):
            out.append(u"段の関数 %s に E が渡っている・使われている" % fn)
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            v = n.value
            if u".env" in v or u"dotenv" in v or u"API_KEY" in v:
                out.append(u"鍵・.env の字が在る")
            if any(s in v for s in (u"_lab.xml", u"_pre.xml", u"_cal.xml", u"_def.xml")):
                out.append(u"提出者の file の名の字が在る: %s" % v)
    if WALL_NAME not in consts:
        out.append(u"前の便の script を読む名が一意の名(%s)でない" % WALL_NAME)
    return out


def reserved_problems(rel=GATE_REL, base=ROOT):
    out = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(line.startswith(p) for p in RESERVED_PREFIXES):
            out.append(u"%s:%d" % (rel, n))
    return out


# ======================================================================== 変異
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**予測は「その検査が赤になる」。** この表は実行より先に書いた。
MUTANTS = (
    # ---- 段 1(数を持てる要素)
    (u"M1 段 1 が abstract を除かない", u'    return set(nm for nm, (ty, ab) in x.items() if ab != "true" and ty not in EXCLUDED_TYPES)', u'    return set(nm for nm, (ty, ab) in x.items() if ty not in EXCLUDED_TYPES)', ("tax_pure", "row", "doc")),
    (u"M2 段 1 が domainItemType を除かない", u'EXCLUDED_TYPES = ("nonnum:domainItemType", "xbrli:stringItemType")', u'EXCLUDED_TYPES = ("xbrli:stringItemType",)', ("seal", "tax_pure", "row")),
    (u"M3 段 1 が stringItemType を除かない", u'EXCLUDED_TYPES = ("nonnum:domainItemType", "xbrli:stringItemType")', u'EXCLUDED_TYPES = ("nonnum:domainItemType",)', ("seal", "tax_pure", "row")),
    (u"M4 段 1 が絞らない(cand0 のまま)", u"    return set(cand0) & tax[\"numeric\"]", u"    return set(cand0)", ("tax_pure", "row", "doc")),
    (u"M5 abstract の属性が無い要素を落とす(false だけ残す)", u'if ab != "true" and ty', u'if ab == "false" and ty', ("tax_pure", "row", "doc")),
    (u"M6 要素の表の abstract の既定を true にする", u'out[nm] = (el.get("type") or u"", el.get("abstract") or u"")', u'out[nm] = (el.get("type") or u"", el.get("abstract") or u"true")', ("tax_pure", "taxzip", "doc")),
    # ---- 段 2
    (u"M7 段 2 が絞らない(段 1 のまま)", u'    return set(cand1) & tax["union"].get(kind, set())', u"    return set(cand1)", ("tax_pure", "row", "doc")),
    (u"M8 段 2 が K の決まらない行を空にする", u"    if kind is None:\n        return set(cand1)\n    return set(cand1) & tax[\"union\"]", u"    if kind is None:\n        return set()\n    return set(cand1) & tax[\"union\"]", ("tax_pure", "row", "doc")),
    (u"M9 段 2 が 1 つの業種(cai)の一覧だけで絞る", u'    return set(cand1) & tax["union"].get(kind, set())', u'    return set(cand1) & tax["c"].get(("cai", kind), set())', ("tax_pure", "row", "doc")),
    (u"M10 和集合を積集合にする", u"        out[k] |= s", u"        out[k] &= s", ("tax_pure", "row", "doc", "taxzip")),
    (u"M11 narrow が段 2 を cand0 から作る(段 1 を飛ばす)", u"    c2 = stage2(c1, kind, tax)", u"    c2 = stage2(cand0, kind, tax)", ("tax_pure", "row")),
    # ---- 段 3
    (u"M12 段 3 が C(I, K) の在るかを見ない", u'    if kind is not None and ind is not None and (ind, kind) in tax["c"]:', u"    if kind is not None and ind is not None:", ("tax_pure", "row", "doc")),
    (u"M13 段 3 のそれ以外が段 1 のまま(段 2 でない)", u"    return set(cand2)\n\n\ndef narrow", u"    return set(cand1)\n\n\ndef narrow", ("tax_pure", "row")),
    (u"M14 段 3 が I を見ない(K の和集合のまま)", u'    if kind is not None and ind is not None and (ind, kind) in tax["c"]:\n        return set(cand1) & tax["c"][(ind, kind)]', u'    if kind is not None and ind is not None and (ind, kind) in tax["c"]:\n        return set(cand2)', ("tax_pure", "row")),
    (u"M15 段 3 が K を見ない(I だけで決める)", u'    if kind is not None and ind is not None and (ind, kind) in tax["c"]:', u'    if ind is not None and (ind, "pl") in tax["c"]:', ("tax_pure", "row")),
    # ---- 類・落とした行
    (u"M16 落とした行が E の在るかを見ない", u"    return E in cand0 and E not in cand", u"    return E not in cand", ("classify", "row")),
    (u"M17 落とした行を数えない(段ごとに cand0 と比べる)", u"        if is_dropped(E, cand0, cd):", u"        if is_dropped(E, cd, cd):", ("row", "doc")),
    (u"M18 全部の段を cand0 で分類する", u"        acc[\"stages\"][s][classify_stage(T, E, cd)] += 1", u"        acc[\"stages\"][s][classify_stage(T, E, cand0)] += 1", ("row", "doc")),
    (u"M19 落とした行を段 1 から数えない", u"    for s, cd in zip(STAGES[1:], cands[1:]):\n        if is_dropped", u"    for s, cd in zip(STAGES[2:], cands[2:]):\n        if is_dropped", ("row", "doc")),
    (u"M20 K が決まらない行を数えない", u"    if kind is None:\n        acc[\"k_none\"] += 1\n    else:", u"    if kind is None:\n        pass\n    else:", ("row", "doc")),
    (u"M21 I が決まらない行を K が決まらない行にも数える", u"    if kind is None:\n        acc[\"k_none\"] += 1\n    else:", u"    if kind is None:\n        acc[\"k_none\"] += 1\n        acc[\"i_none\"] += 1\n    else:", ("row", "doc")),
    # ---- 見出し・種類
    (u"M22 見出しの決めの順を入れ替える(損益計算書を貸借対照表より先に)", u'KIND_RULES = ((u"貸借対照表", "bs"), (u"キャッシュ・フロー計算書", "cf"), (u"株主資本等変動計算書", "ss"), (u"損益計算書", "pl"), (u"包括利益計算書", "pl"))',
     u'KIND_RULES = ((u"損益計算書", "pl"), (u"包括利益計算書", "pl"), (u"貸借対照表", "bs"), (u"キャッシュ・フロー計算書", "cf"), (u"株主資本等変動計算書", "ss"))', ("seal", "heading")),
    (u"M23 包括利益計算書の決めを外す", u'(u"損益計算書", "pl"), (u"包括利益計算書", "pl"))', u'(u"損益計算書", "pl"))', ("seal", "heading")),
    (u"M24 見出しの字の NFKC・空白除きを外す", u"    t = norm_label(heading)\n    for word", u"    t = heading\n    for word", ("heading", "doc")),
    (u"M25 見出しの最後でなく最初を使う", u"        out.append((m.group(0), heads[j - 1][1] if j else None))", u"        out.append((m.group(0), heads[0][1] if j else None))", ("heading", "doc")),
    (u"M26 行の位置をタグを除かない長さで測る", u"        pos = p - removed", u"        pos = p", ("heading",)),
    (u"M27 見出しの始まりが行の位置と同じでも前に数える", u"        j = bisect.bisect_left(hpos, pos)", u"        j = bisect.bisect_right(hpos, pos)", ("heading",)),
    (u"M28 見出しの長さの上限を外す(400 字)", u'HEAD_RE = re.compile(u"【([^】]{0,40})】")', u'HEAD_RE = re.compile(u"【([^】]{0,400})】")', ("seal", "heading")),
    (u"M29 見出しを file をまたいで引き継ぐ(前の file の最後の見出しを次の file の先頭に付ける)", u"    for _n, text in texts:\n        for rowtext, head in file_rows(text):",
     u"    _carry = u\"\"\n    for _n, text in texts:\n        text = _carry + text\n        _carry = u\"<p>【%s】</p>\" % (re.findall(u\"【([^】]{0,40})】\", strip_tags(text)) or [u\"\"])[-1]\n        for rowtext, head in file_rows(text):", ("doc",)),
    # ---- 業種・DEI
    (u"M30 業種を常に連結の欄から決める", u"    v = dei[0] if CONSOLIDATED_WORD in norm_label(heading) else dei[1]", u"    v = dei[0]", ("heading", "row", "doc")),
    (u"M31 業種を常に個別の欄から決める", u"    v = dei[0] if CONSOLIDATED_WORD in norm_label(heading) else dei[1]", u"    v = dei[1]", ("heading", "row", "doc")),
    (u"M32 連結の字を空白を除く前の見出しで探す", u"CONSOLIDATED_WORD in norm_label(heading)", u"CONSOLIDATED_WORD in heading", ("heading", "doc")),
    (u"M33 cte を cai に読み替えない", u'INDUSTRY_ALIAS = (("cte", "cai"),)', u"INDUSTRY_ALIAS = ()", ("seal", "heading", "row")),
    (u"M34 folder が無い値も業種にする", u"    return v if v and v in folders else None", u"    return v if v else None", ("heading", "row")),
    (u"M35 DEI の値を小文字にしない", u'v = W.WS_RE.sub(u"", strip_tags(m.group(1))).lower()', u'v = W.WS_RE.sub(u"", strip_tags(m.group(1)))', ("heading", "row")),
    (u"M36 DEI の値のタグを除かない", u'v = W.WS_RE.sub(u"", strip_tags(m.group(1))).lower()', u'v = W.WS_RE.sub(u"", m.group(1)).lower()', ("heading",)),
    (u"M37 DEI の値の空白を除かない", u'v = W.WS_RE.sub(u"", strip_tags(m.group(1))).lower()', u'v = strip_tags(m.group(1)).lower()', ("heading", "row")),
    (u"M38 DEI を最後の空でない値にする", u"        for _n, t in sorted(texts, key=lambda p: p[0]):\n            v = dei_value(t, name)\n            if v:\n                break",
     u"        for _n, t in sorted(texts, key=lambda p: p[0]):\n            v = dei_value(t, name) or v", ("heading", "doc")),
    (u"M39 DEI を file 名の昇順に並べない", u"        for _n, t in sorted(texts, key=lambda p: p[0]):\n            v = dei_value(t, name)", u"        for _n, t in texts:\n            v = dei_value(t, name)", ("heading",)),
    (u"M40 DEI の空の値で止まる(最初の file の値をそのまま使う)", u"            v = dei_value(t, name)\n            if v:\n                break", u"            v = dei_value(t, name)\n            break", ("heading", "doc")),
    # ---- 書類・タクソノミ
    (u"M41b DEI の値の読みで改行をまたげない(re.S を外す)", u"(.*?)</ix:nonNumeric>' % re.escape(name), re.S | re.I)", u"(.*?)</ix:nonNumeric>' % re.escape(name), re.I)", ("heading", "doc")),
    (u"M42 PublicDoc の外の ixbrl も読む", u"if n.startswith(PUBLICDOC) and n.endswith(IXBRL_SUFFIX)]", u"if n.endswith(IXBRL_SUFFIX)]", ("doc", "e2e")),
    (u"M43 提出者のラベルを表に混ぜる", u"    texts = sorted(texts, key=lambda p: p[0])\n    dei = dei_values(texts)\n    acc = new_doc()\n",
     u"    texts = sorted(texts, key=lambda p: p[0])\n    dei = dei_values(texts)\n    acc = new_doc()\n    l2 = dict(l2)\n    l2.setdefault(u\"未登録\", set()).add(u\"Foo\")\n", ("row", "doc")),
    (u"M44 zip の sha256 の照合を外す", u"    if sha != TAXZIP_SHA256:", u"    if False:", ("taxzip",)),
    (u"M45 要素の表を /taxonomy/ の外の file からも探す", u"    if ZIP_MARK not in name:\n        return None\n    return name.split(ZIP_MARK, 1)[1]", u"    if ZIP_MARK not in name:\n        return name\n    return name.split(ZIP_MARK, 1)[1]", ("taxzip",)),
    (u"M46 科目の一覧を cal の file から読む", u'DEF_NAME = "jppfs/2025-11-01/r/%s/jppfs_%s_cm_2025-11-01_def_%s.xml"', u'DEF_NAME = "jppfs/2025-11-01/r/%s/jppfs_%s_cm_2025-11-01_cal_%s.xml"', ("seal", "taxzip", "e2e")),
    (u"M47 科目の一覧の href を # の後ろ全部にする", u"""HREF_RE = re.compile(r'xlink:href="[^"]*#jppfs_cor_([^"]*)"')""", u"""HREF_RE = re.compile(r'xlink:href="[^"]*#([^"]*)"')""", ("seal", "tax_pure", "taxzip")),
    (u"M48 科目の一覧の file の日付を問わない", u'DEF_NAME % (i, i, k)', u'DEF_NAME.replace("2025-11-01", "2024-11-01") % (i, i, k)', ("taxzip", "e2e")),
    # ---- 合計・止め・率
    (u"M49 16763 の止めを外す", u"    if rows_want is not None and rows != rows_want:", u"    if False:", ("check_expected",)),
    (u"M50 段 0 の止めを外す", u"    if stage0_want is not None and list(tot[\"stages\"][\"段 0\"].values()) != list(stage0_want.values()):", u"    if False:", ("check_expected",)),
    (u"M51 便 XG0 の記録との照合を外す", u"    if prior is not None:\n        agg = prior", u"    if False:\n        agg = prior", ("check_expected",)),
    (u"M52 U の率 90% 以上を「より大きい」にする", u'            if 100 * u3 >= U_DOC_THRESHOLD_PCT * r:', u'            if 100 * u3 > U_DOC_THRESHOLD_PCT * r:', ("e2e",)),
    (u"M53 計算書の行が 0 の書類も分母に入れる", u"        if r:\n            docs_with_rows += 1", u"        if True:\n            docs_with_rows += 1", ("e2e",)),
    (u"M54 合計が落とした行を足さない", u'    for s in STAGES[1:]:\n        tot["dropped"][s] += acc["dropped"][s]', u'    for s in STAGES[1:]:\n        pass', ("totals", "e2e")),
    (u"M55 合計が I が決まらない行を足さない", u'    tot["i_none"] += acc["i_none"]', u"    pass", ("totals", "e2e")),
    (u"M56 XG1-5 の分子を段 2 の落とした行にする", u'rate_of(tot["dropped"]["段 3"], rows_all)', u'rate_of(tot["dropped"]["段 2"], rows_all)', ("e2e",)),
    (u"M57 XG1-1 の分子を段 0 の U にする", u'rate_of(st["段 1"]["U"], rows_all)', u'rate_of(st["段 0"]["U"], rows_all)', ("e2e",)),
    # ---- 記録の検査・secret
    (u"M58 見出しの字の全部一致の検査を外す", u"        if strs & set(heads):", u"        if False:", ("clean", "secret")),
    (u"M59 見出しの字の部分一致の検査を外す", u"            if len(h) >= W.LABEL_SUBSTRING_MIN and h in scan:", u"            if False:", ("clean", "secret")),
    (u"M60 業種のコードの値の検査を外す", u"        if tokens & set(inds):", u"        if False:", ("clean", "secret")),
    (u"M61 便 XG0 の記録の検査(欄・形・材料)を呼ばない", u"    W.check_clean(rec, text, secret[:4] if secret else None)", u"    pass", ("clean",)),
    (u"M62 書いた後の検査を外す", u"        check_clean(rec, back, secret)\n    except SystemExit:", u"        pass\n    except SystemExit:", ("clean",)),
    (u"M63 書く前の検査を外す", u"    text = record_text(rec, secret)\n    os.makedirs", u"    text = dumps(rec)\n    os.makedirs", ("clean",)),
    (u"M64 secret に見出しの字を集めない", u"                    secret[4].add(norm_label(head))", u"                    pass", ("secret",)),
    (u"M65 secret に見出しの字を正規化せずに集める", u"                    secret[4].add(norm_label(head))", u"                    secret[4].add(head)", ("secret",)),
    (u"M66 secret に業種の値を集めない", u"        secret[5].update(v for v in dei if v)", u"        pass", ("secret",)),
    (u"M67 check() が secret を check_clean に渡さない", u"    check_clean(rec, text, secret)\n    say(", u"    check_clean(rec, text)\n    say(", ("secret",)),
    (u"M68 build_record の secret の EDINET コードを集めない", u'            secret[3].update(re.findall(r"E\\d{5}", x))', u"            pass", ("secret",)),
    # ---- 封の字
    (u"M69 予測の境の数を 1 つ替える(XG1-3 の上限)", u'("XG1-3", (80, 93))', u'("XG1-3", (80, 94))', ("seal",)),
    (u"M70 計算書の行の数を替える", u"ROWS_WANT = 16763", u"ROWS_WANT = 16764", ("seal", "stage0")),
    (u"M71 段 0 の数を 1 つ替える", u'STAGE0_WANT = collections.OrderedDict([("U", 9571), ("A", 6880), ("W", 65), ("N", 247)])', u'STAGE0_WANT = collections.OrderedDict([("U", 9571), ("A", 6880), ("W", 66), ("N", 247)])', ("seal", "stage0")),
    (u"M72 zip の sha256 を 1 字替える", u'TAXZIP_SHA256 = "8d57f848', u'TAXZIP_SHA256 = "9d57f848', ("seal",)),
    (u"M73 DEI の name(連結)を替える", u'DEI_CONSOLIDATED = "jpdei_cor:IndustryCodeWhenConsolidated', u'DEI_CONSOLIDATED = "jpdei_cor:IndustryCodeWhenConsolidate', ("seal", "heading")),
    (u"M74 封の commit を替える", u'SEAL_COMMIT = "1bda1997"', u'SEAL_COMMIT = "1bda1998"', ("seal",)),
    # ---- 配線(E を絞りへ渡す・前の便の関数を写す・importlib の名)
    (u"M75 段 1 の関数に E を渡す", u"def stage1(cand0, tax):", u"def stage1(cand0, tax, E=None):", ("tax_pure", "import")),
    (u"M76 段 3 の関数が E を使う", u"def stage3(cand1, cand2, kind, ind, tax):\n", u"def stage3(cand1, cand2, kind, ind, tax):\n    E = None\n", ("import",)),
    (u"M77 前の便の script を他と重なる名で読む", u'    name = "_xg1_tag_wall_2026_11_21"', u'    name = "xbrl_tag_wall_script"', ("import",)),
    (u"M78 前の便の classify を写す", u"def classify_stage(T, E, cand):", u"def classify(T, E, table):\n    return 'U'\n\n\ndef classify_stage(T, E, cand):", ("import",)),
)
#: 黙ることが分かっている変異(理由つき)。黙ること自体を ``SilentTest`` が縛る
SILENT_BY_DESIGN = (
    (u"S3 count_doc が file を昇順に並べない",
     u"    texts = sorted(texts, key=lambda p: p[0])\n    dei = dei_values(texts)", u"    dei = dei_values(texts)",
     u"行は file ごとに独立に数え(見出しは file の中だけ)、合計は足し算で順に依らない。DEI は ``dei_values`` が自分で file 名の昇順に並べて読む。よって count_doc の並べ替えは結果を変えない(同値の変異)。"),
    (u"S1 段 3 が cand1 でなく cand2 に C(I, K) を掛ける",
     u'        return set(cand1) & tax["c"][(ind, kind)]', u'        return set(cand2) & tax["c"][(ind, kind)]',
     u"C(I, K) は和集合 union[K] の部分集合で、cand2 = cand1 ∩ union[K]。よって cand1 ∩ C(I, K) = cand2 ∩ C(I, K)。どの入力でも同じ(同値の変異)。"),
    (u"S2 種類 K が決まらない行でも業種を計算する",
     u"            ind = industry_of(head, dei, tax[\"folders\"]) if kind is not None else None", u"            ind = industry_of(head, dei, tax[\"folders\"])",
     u"K が決まらない行は段 3 が段 2 のまま(K を見る)で、I が決まらない行の数も K が決まる行だけに数える。K が None のとき I は使われない(同値の変異)。"))


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"stage0": stage0_problems, u"tax_pure": tax_pure_problems, u"classify": classify_problems, u"heading": heading_problems, u"check_expected": check_expected_problems,
             u"row": row_problems, u"doc": doc_problems, u"totals": totals_problems, u"taxzip": taxzip_problems, u"clean": clean_problems, u"e2e": e2e_problems, u"secret": secret_problems}
    if name in table:
        return table[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"stage0", u"tax_pure", u"classify", u"heading", u"check_expected", u"row", u"doc", u"totals", u"taxzip", u"clean", u"e2e", u"secret", u"import")


def run_mutants(table=MUTANTS):
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in table:
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


# ======================================================================== 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        for old, new in ((u"| XG1-3(主) | 段 3 の類 U は 80% 以上 93% 以下", u"| XG1-3(主) | 段 3 の類 U は 80% 以上 94% 以下"),
                         (u"段 3 の U の率が 90% 以上の書類は 25 本以下", u"段 3 の U の率が 80% 以上の書類は 25 本以下"), (u"`cte` は `cai` に読み替える", u"`cte` は `cna` に読み替える"),
                         (u"(U 9571・A 6880・W 65・N 247)", u"(U 9571・A 6880・W 66・N 247)"), (u"合計で 16763 行", u"合計で 16764 行"),
                         (u"`貸借対照表` を含む → `bs`", u"`貸借対照表` を含む → `pl`"), (u"8d57f84802b20a8dc6a517ad6d4768270c294aa6991621d66cb5adb562df5de2", u"9d57f84802b20a8dc6a517ad6d4768270c294aa6991621d66cb5adb562df5de2"),
                         (u"`abstract` が `true` でなく", u"`abstract` が `false` でなく"), (u"`【([^】]{0,40})】` に当たる所を見出しとする", u"`【([^】]{0,60})】` に当たる所を見出しとする")):
            self.assertEqual(1, seal.count(old), old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"tag_narrow", body)
        self.assertNotIn(u"xbrl_tag_narrow", body)

    def test_a_6_stage0_numbers_and_rows_equal_the_previous_record(self):
        self.assertEqual([], stage0_problems())


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        others = ["measure/s.py", "tests/g.py"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("tests/new.py")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["tests/new.py"]))
        r2 = PR.Repo()
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["measure/s.py"]))

    def test_d_3_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PureTest(unittest.TestCase):
    def test_b_1_tax_tables_and_the_three_stages(self):
        self.assertEqual([], tax_pure_problems())

    def test_b_2_classes_dropped_rows_and_u_falling_with_a_stage(self):
        self.assertEqual([], classify_problems())

    def test_b_3_headings_kinds_industries_and_dei(self):
        self.assertEqual([], heading_problems())

    def test_b_4_the_expected_totals_stop_the_script(self):
        self.assertEqual([], check_expected_problems())

    def test_b_5_every_hand_row_goes_through_the_real_functions(self):
        self.assertEqual([], row_problems())

    def test_b_6_made_up_documents_equal_the_hand_count_and_the_totals(self):
        self.assertEqual([], doc_problems())
        self.assertEqual([], totals_problems())

    def test_b_7_the_hand_counts_are_not_the_same_as_nearby_numbers(self):
        u"""手で決めた値が足し算と合い、段の U が互いに違い(段を進めて減る)、90% の境の上と下の書類が在る。"""
        t = HAND_TOTAL
        self.assertEqual(t["rows"], sum(h[0] for h in HAND_DOCS))
        for k in range(4):
            self.assertEqual(t["rows"], sum(t["stages"][k]))
            self.assertEqual(t["stages"][k], tuple(sum(h[1][k][i] for h in HAND_DOCS) for i in range(4)))
        self.assertEqual(t["dropped"], tuple(sum(h[2][i] for h in HAND_DOCS) for i in range(3)))
        self.assertEqual(t["kinds"], tuple(sum(h[3][i] for h in HAND_DOCS) for i in range(4)))
        self.assertEqual(t["rows"], sum(t["kinds"]) + t["k_none"])
        self.assertEqual(t["k_none"], sum(h[4] for h in HAND_DOCS))
        self.assertEqual(t["i_none"], sum(h[5] for h in HAND_DOCS))
        us = [t["stages"][k][0] for k in range(4)]
        self.assertEqual(len(set(us)), 4)
        self.assertGreater(us[1], us[2])                      # 段 1 → 段 2 で U が減る
        self.assertEqual(len(set(t["rates"])), len(t["rates"]))
        rates = [h[6] for h in HAND_DOCS if h[6] is not None]
        self.assertTrue(any(r >= 90 for r in rates) and any(r < 90 for r in rates) and any(r == 90.0 for r in rates))
        self.assertTrue(any(h[6] is None for h in HAND_DOCS))
        self.assertEqual(len(set(len(v) for v in FAKE_L2.values())), 5)                      # cand0 の大きさが 5・1・4・3・1・2(近い数と同じにしない)
        self.assertEqual(len(HAND_ROWS), 18)
        self.assertTrue(set(u"".join(r[5] for r in HAND_ROWS)) >= set("AUWN"))

    def test_b_8_the_fake_taxonomy_zip_has_the_decoys_the_checks_say(self):
        with Temp() as d:
            p = os.path.join(d, "t.zip")
            make_tax_zip(p)
            with zipfile.ZipFile(p) as z:
                names = z.namelist()
            self.assertTrue(any(u"taxonomy_old" in n for n in names) and any(u"2024-11-01" in n for n in names) and any(u"_cal_" in n for n in names))


class RecordTest(unittest.TestCase):
    def test_c_1_the_taxonomy_zip_is_read_by_name_and_sha(self):
        self.assertEqual([], taxzip_problems())

    def test_c_2_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_c_3_cache_to_record_to_check_without_reading_the_real_cache(self):
        self.assertEqual([], e2e_problems())

    def test_c_4_the_production_secret_is_built_and_check_passes_it_to_the_clean_check(self):
        self.assertEqual([], secret_problems())

    def test_c_5_the_real_record_when_present_is_clean(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く")
        text = read(RECORD_REL)
        rec = json.loads(text, object_pairs_hook=od)
        MS.check_clean(rec, text)


class WiringTest(unittest.TestCase):
    def test_e_1_imports_engine_calls_and_e_is_not_given_to_the_stages(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport subprocess\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport urllib.request\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.environ.get('A')\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef classify(T, E, table):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = '_lab.xml'\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = 'a_def.xml'\n"))
        self.assertNotEqual([], import_problems(base.replace(u"def stage2(cand1, kind, tax):", u"def stage2(cand1, kind, tax, E):")))
        self.assertNotEqual([], import_problems(base.replace(u"I._TR_RE.finditer(text)", u"[]")))
        self.assertNotEqual([], import_problems(base.replace(u"from adapters.xbrl import instance as I", u"from adapters.xbrl import instance as I\nfrom adapters.xbrl import recipes as R")))

    def test_e_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_4_the_script_leaves_sys_modules_as_it_found_them_except_its_own_wall_name(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_tag_narrow_script_for_sysmodules_check")
        self.assertEqual([], [k for k, v in before.items() if sys.modules.get(k) is not v])
        self.assertIn(mod.W.__name__, sys.modules)
        self.assertEqual(mod.W.__name__, WALL_NAME)
        self.assertNotEqual(WALL_NAME, "xbrl_tag_wall_script_for_seal_gate")
        del mod

    def test_e_5_the_default_places_are_outside_the_repo_and_the_gate_never_opens_them(self):
        top = os.path.realpath(REPO)
        for p in (MS.DOCS_DIR, MS.TAXONOMY_DIR, MS.TAXZIP_PATH):
            self.assertFalse(os.path.realpath(p).startswith(top + os.sep), p)
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record|load_tax)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"\bd\b|docs|\*\*kw|\bp\b|\bq\b|tz|docs_dir", m.group(2)) or m.group(1) == "build_record", m.group(0))


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
        self.assertGreaterEqual(len(MUTANTS), 30)

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)

    def test_f_3_the_silent_mutants_are_silent_for_the_stated_reason(self):
        u"""同値の変異は、作り物の全部の検査でも、字を足した入力の段の結果でも、元と同じ。"""
        base = read(SCRIPT_REL)
        tax = fake_tax(MS)
        for name, old, new, _why in SILENT_BY_DESIGN:
            self.assertEqual(1, base.count(old), name)
            mod = load_source(base.replace(old, new))
            for c in (u"tax_pure", u"classify", u"heading", u"row", u"doc", u"totals", u"taxzip", u"clean", u"e2e", u"secret"):
                self.assertEqual([], check_by_name(c, mod, None), (name, c))
            tax2 = mod.make_tax(mod.build_x(xsd_bytes()), dict(FAKE_C), FAKE_FOLDERS)
            for oth in (set(FAKE_L2[u"その他"]), set(FAKE_L2[u"当期変動額"]), set(FAKE_L2[u"現金同等物"]), set(FAKE_L2[u"資産"])):
                for k in (None, "bs", "pl", "ss", "cf"):
                    for i in (None, "cai", "bk1", "cmd", "emp"):
                        self.assertEqual(MS.narrow(oth, k, i, tax), mod.narrow(oth, k, i, tax2), (name, k, i))


if __name__ == "__main__":
    unittest.main()
