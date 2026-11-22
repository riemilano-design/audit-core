# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PRIOR_YEAR_DRAFT_SEAL_2026-11-22.md(XY0 ― 同じ会社の前の年の提出書類の「行の字 → 要素」を今年の行に当てる)の封の門。

**この門は置き場を読まない**(今年の側の置き場 ``~/.cache/audit-core/edinet/``・前の年の側の置き場・標準ラベルの置き場・標準タクソノミの zip は 1 度も開かない)。通信しない。
読むのは repo の中の封の file・便 XG0 の記録(行の番号の並びの形)・script だけ。作り物の zip(今年の側と前の年の側の組)・作り物のラベルの linkbase・作り物の標準タクソノミを使う。

**この門が縛るもの**

1. 封の字: 封の commit(ce70f71f)・封の file が commit した blob と同じ・組の数 63 と書類の本数 67・組の作り方の file 名の形・段(P・PK・C)と類(U・A・W1・W2・N)の名・
   集まり S の接頭辞・95% の境・予測の境の数・限界の 6 行が script の定数と同じ。
2. engine は封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 作り物の組で、組の作り方(当たる zip が無い → 除く・2 本以上 → 止まる・期末が合わない → 止まる・組の数が違えば止まる・file 名の形が読めない今年の書類は止まる)・
   行の切り方(name が 2 種類の行・行の字が無い行・数字だけの字の行は分母の外)・集まり S と集まり B・表 P と表 PK(K は見出しから・K が決まらない行は決まらない同士)・
   段 P・段 PK・段 C(PK の候補が在れば PK・空なら標準の表)・類 U・A・W1・W2・N・書類ごとの数・合計・95% の境(ちょうど 95.0% を含む)を、本物の関数のまま通す(手で数えた値と照らす)。
4. E(今年の行の要素)は、候補を作る関数(段 P・段 PK・段 C・標準の表の候補)に渡さない。前の年の側として今年の zip を読まない。
5. 記録の禁止の検査(docID・EDINET コード・会社の名・行の字・見出しの字・要素の名・業種のコードの値・日付の形)が作り物で止まる。S の行の合計の照合(便 XG0 の記録)が違えば止まる。
6. script の import は標準ライブラリと engine の 2 module(instance・verify_document)と importlib だけ。前の便の script は importlib で読み(一意の名)、関数は呼ぶ(写さない)。
7. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
黙る変異は ``SILENT_BY_DESIGN`` に理由とともに置き、「黙ること」自体を別の試験で縛る。
"""
import ast
import collections
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
    mod = types.ModuleType("xbrl_prior_year_draft_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_PRIOR_YEAR_DRAFT_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "ce70f71f"                # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_prior_year_draft_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_prior_year_draft_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/prior_year_draft_2026-11-22.json"
WALL_RECORD_REL = "fixtures/xbrl/cd8/tag_wall_2026-11-21.json"
MS = load_module(SCRIPT_REL, "xbrl_prior_year_draft_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_prior_year_draft_seal")      # 順序・履歴の部品。門としては走らせない
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
        self.d = tempfile.mkdtemp(prefix="xy0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


# ======================================================================== 作り物の標準タクソノミ(段 C の標準の表)
XSD_HEAD = u'<?xml version="1.0" encoding="UTF-8"?><xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xbrli="http://www.xbrl.org/2003/instance">'
MONETARY = u"xbrli:monetaryItemType"
FAKE_X = [u"Assets", u"OthPl", u"OthBs", u"Cash", u"CashEq", u"NewItem"]
FAKE_C = {("cai", "bs"): {u"Assets", u"OthBs", u"Cash", u"NewItem"}, ("cai", "pl"): {u"OthPl"}}            # cf の一覧は無い
FAKE_FOLDERS = ["cai"]


def xsd_bytes(names=None):
    parts = [XSD_HEAD]
    for nm in (FAKE_X if names is None else names):
        parts.append(u'<xsd:element name="%s" id="jppfs_cor_%s" type="%s" abstract="false" substitutionGroup="xbrli:item"/>' % (nm, nm, MONETARY))
    parts.append(u"</xsd:schema>")
    return u"".join(parts).encode("utf-8")


def def_text(names):
    parts = [u'<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink"><link:definitionLink>']
    for i, nm in enumerate(sorted(names)):
        parts.append(u'<link:loc xlink:type="locator" xlink:href="../../jppfs_cor_2025-11-01.xsd#jppfs_cor_%s" xlink:label="l%d"/>' % (nm, i))
    parts.append(u"</link:definitionLink></link:linkbase>")
    return u"".join(parts)


TOP = u"金融庁の日本語の名前/taxonomy/"


def make_tax_zip(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(TOP + u"jppfs/2025-11-01/jppfs_cor_2025-11-01.xsd", xsd_bytes())
        for (i, k), names in sorted(FAKE_C.items()):
            z.writestr(TOP + u"jppfs/2025-11-01/r/%s/jppfs_%s_cm_2025-11-01_def_%s.xml" % (i, i, k), def_text(names))


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


#: 表 L2(ラベルの字 → cand0)。段 C の標準の表の候補にだけ使う
FAKE_L2 = {u"資産": {u"Assets"}, u"その他": {u"OthPl", u"OthBs"}, u"現金": {u"Cash", u"CashEq"}, u"新科目": {u"NewItem"}}
FAKE_LABELS = linkbase([(u"jppfs_cor_%s" % e, R_STD, t, "ja") for t, es in sorted(FAKE_L2.items()) for e in sorted(es)])


def fake_tax(ms=None):
    ms = ms or MS
    return ms.N.make_tax(ms.N.build_x(xsd_bytes()), dict(FAKE_C), FAKE_FOLDERS)


def fake_l2(ms=None):
    ms = ms or MS
    return ms.W.label_tables(FAKE_LABELS)[0]


def patched_labels(ms, label_bytes=FAKE_LABELS):
    u"""``W.read_label_bytes`` を作り物のラベルへ差し替える。呼び出し側が元に戻す(戻り値が元の関数)。"""
    orig = ms.W.read_label_bytes
    ms.W.read_label_bytes = lambda d: (label_bytes, hashlib.sha256(label_bytes).hexdigest())
    return orig


# ======================================================================== 作り物の書類(今年の側と前の年の側)
NFTAG = u'<ix:nonFraction name="%s" contextRef="c1" unitRef="JPY" decimals="-6" scale="6">100</ix:nonFraction>'
DEI_C = u"jpdei_cor:IndustryCodeWhenConsolidatedFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI"
DEI_S = u"jpdei_cor:IndustryCodeWhenFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI"
STD = u"jppfs_cor:"
CRP = u"jpcrp_cor:"


def row(label, *names):
    u"""``<tr>``: 左端のセルが行の字・あとのセルが ix:nonFraction。"""
    return u"<tr><td>%s</td>%s</tr>" % (label, u"".join(u"<td>%s</td>" % (NFTAG % n) for n in names))


def head(h):
    return u"<p>【%s】</p>" % h


def dei(name, value):
    return u'<p><ix:nonNumeric name="%s" contextRef="c1"><span> %s </span></ix:nonNumeric></p>' % (name, value)


def table(rows):
    return u"<table>" + u"".join(rows) + u"</table>"


def file_of(groups):
    u"""[(見出しか None, [<tr> の字])] → 1 file の字。"""
    out = []
    for h, rows in groups:
        if h is not None:
            out.append(head(h))
        out.append(table(rows))
    return u"".join(out)


H_BS, H_PL, H_CF, H_NOTE = u"貸借対照表", u"損益計算書", u"キャッシュ・フロー計算書", u"注記事項"
#: 作り物の書類 D1 の今年の行(名前, 行の字, 要素 E, 見出し, 種類 K, 集まり S か) ― 段 P・段 PK・段 C の類は書類ごとの手の値(HAND_PAIRS)で
#: c1  bs 資産 Assets             P=A  PK=U  C=U         c8  - 資産 Assets          P=A  PK=W1 C=W1  (標準の表なら U。PK の候補が在るので PK)
#: c2  bs その他 OthBs            P=A  PK=U  C=U         c9  pl 負債 Liab           P=U  PK=N  C=N   (表 L2 に負債が無い)
#: c3  pl その他 OthPl            P=A  PK=U  C=U         c10 -  前期特有 Foo(B のみ) P=U  PK=U
#: c4  pl その他 OthBs            P=A  PK=W1 C=W1        c11 bs 資産 jpsub:Bar(Bのみ) P=W2 PK=W1
#: c5  bs 現金 Cash               P=A  PK=A  C=A         c12 -  新B Baz(B のみ)     P=N  PK=N
#: c6  bs 現金 Zzz                P=W2 PK=W2 C=W2        c13 cf 現金 Cash           P=A  PK=N  C=N   (cf の一覧が無い)
#: c7  bs 新科目 NewItem             P=N  PK=N  C=U(標準の表から)


def d1_cur():
    f0a = (dei(DEI_C, u"CAI") + dei(DEI_S, u"CAI")
           + file_of([(H_BS, [row(u"資産", STD + u"Assets", STD + u"Assets"),                                   # c1
                              row(u"その他", STD + u"OthBs"),                                                  # c2
                              row(u"現金", STD + u"Cash"),                                                    # c5
                              row(u"現金", STD + u"Zzz"),                                                     # c6
                              row(u"新科目", STD + u"NewItem"),                                              # c7
                              row(u"資産", STD + u"Cash", STD + u"Liab"),                                      # name が 2 種類(分母の外)
                              u"<tr><td></td><td>%s</td></tr>" % (NFTAG % (STD + u"Assets")),                 # 行の字が無い(分母の外)
                              u"<tr><td>12,345</td><td>%s</td></tr>" % (NFTAG % (STD + u"Assets")),           # 数字だけの字(分母の外)
                              u"<tr><td>資産</td><td>1</td></tr>"]),                                          # ix:nonFraction が無い
                      (H_PL, [row(u"その他", STD + u"OthPl"),                                                 # c3
                              row(u"その他", STD + u"OthBs"),                                                 # c4
                              row(u"負債", STD + u"Liab")]),                                                  # c9
                      (H_CF, [row(u"現金", STD + u"Cash")])]))                                                # c13
    f0b = file_of([(None, [row(u"資産", STD + u"Assets"),                                                      # c8
                           row(u"前期特有", CRP + u"Foo"),                                                      # c10
                           row(u"新B", CRP + u"Baz")]),                                                       # c12
                   (H_BS, [row(u"資産", u"jpsub:Bar")])])                                                     # c11
    return [("0b_ixbrl.htm", f0b), ("0a_ixbrl.htm", f0a)]                                                      # 並びは昇順でない


def d1_prior():
    f0a = file_of([(H_BS, [row(u"資産", STD + u"Assets"), row(u"その他", STD + u"OthBs"), row(u"現金", STD + u"Cash"), row(u"現金", STD + u"CashEq"),
                           row(u"負債", STD + u"Liab"),
                           row(u"資産", STD + u"Zzz1", STD + u"Zzz2")]),                                       # name が 2 種類(表に入れない)
                   (H_PL, [row(u"その他", STD + u"OthPl")])])
    f0b = file_of([(None, [row(u"前期特有", CRP + u"Foo")]), (H_NOTE, [row(u"資産", STD + u"AssetsNote")])])
    return [("0a_ixbrl.htm", f0a), ("0b_ixbrl.htm", f0b)]


HAND_P = {u"資産": {STD + u"Assets", STD + u"AssetsNote"}, u"その他": {STD + u"OthBs", STD + u"OthPl"}, u"現金": {STD + u"Cash", STD + u"CashEq"},
          u"負債": {STD + u"Liab"}, u"前期特有": {CRP + u"Foo"}}
HAND_PK = {("bs", u"資産"): {STD + u"Assets"}, ("bs", u"その他"): {STD + u"OthBs"}, ("pl", u"その他"): {STD + u"OthPl"}, ("bs", u"現金"): {STD + u"Cash", STD + u"CashEq"},
           ("bs", u"負債"): {STD + u"Liab"}, (None, u"前期特有"): {CRP + u"Foo"}, (None, u"資産"): {STD + u"AssetsNote"}}


def bs_doc(good, bad, no_dei=True):
    u"""見出し 貸借対照表 の下に、行の字 資産・E Assets の行 good 本と E Zed の行 bad 本。"""
    return [("0a_ixbrl.htm", file_of([(H_BS, [row(u"資産", STD + u"Assets")] * good + [row(u"資産", STD + u"Zed")] * bad)]))]


def d2_cur():
    return bs_doc(19, 1)                    # S 20 行・PK で U 19(95.0%)


def d4_cur():
    return bs_doc(18, 2)                    # S 20 行・PK で U 18(90.0%)


def prior_bs():
    return [("0a_ixbrl.htm", file_of([(H_BS, [row(u"資産", STD + u"Assets")])]))]


def d5_cur():
    return [("0a_ixbrl.htm", file_of([(None, [row(u"ABC", CRP + u"Foo2")])]))]                   # 半角の字


def d5_prior():
    return [("0a_ixbrl.htm", file_of([(None, [row(u"ＡＢＣ", CRP + u"Foo2")])]))]                  # 全角の字(NFKC で当たる)


def d3_cur():
    return [("0a_ixbrl.htm", file_of([(H_BS, [row(u"資産", STD + u"Assets")] * 7)]))]            # 組にならない書類(便 XG0 の記録の行は 7 とする)


# ---- 段 C の業種の配線・DEI の読み・落ちた行(K が決まらない S の行)を縛る作り物(count_pair を通る)
#: 業種 cai の bs の一覧は NewItem・業種 zzz の bs の一覧は AltItem。表 L2 の「新科目」は {NewItem, AltItem}。前の年の側は「資産」の行だけ(「新科目」は PK にも P にも無い)
FILL_X = [u"NewItem", u"AltItem"]
FILL_C = {("cai", "bs"): {u"NewItem"}, ("zzz", "bs"): {u"AltItem"}}
FILL_FOLDERS = ["cai", "zzz"]
FILL_L2 = {u"新科目": {u"NewItem", u"AltItem"}}


def fill_tax(ms=None):
    ms = ms or MS
    return ms.N.make_tax(ms.N.build_x(xsd_bytes(FILL_X)), dict(FILL_C), FILL_FOLDERS)


def fill_cur():
    u"""file 0a: 見出し「連結貸借対照表」の下と「貸借対照表」の下に同じ行(新科目・E NewItem)。file 0b: DEI だけ(連結 zzz・個別 cai。2 つ目の file)。file 0c: 見出しの無い同じ行。"""
    return [("0c_ixbrl.htm", file_of([(None, [row(u"新科目", STD + u"NewItem")])])),
            ("0b_ixbrl.htm", dei(DEI_C, u"zzz") + dei(DEI_S, u"cai")),
            ("0a_ixbrl.htm", file_of([(u"連結貸借対照表", [row(u"新科目", STD + u"NewItem")]), (H_BS, [row(u"新科目", STD + u"NewItem")])]))]


#: 手で数える。3 行とも S で P・PK の候補は空(N)。段 C: 連結の行は I=zzz → 一覧 {AltItem} なので E=NewItem は W1。個別の行は I=cai → {NewItem} で U。
#: 見出しの無い行は K が決まらず PK も空 → 標準の表の候補は段 2 のまま {NewItem, AltItem} で A。標準の表へ落ちた S の行は 3 行(K が決まらない行を含む)
HAND_FILL = (3, 3, ((0, 0, 0, 0, 3), (0, 0, 0, 0, 3), (1, 1, 1, 0, 0)), ((0, 0, 0, 0, 3), (0, 0, 0, 0, 3)), 3, (1, 1, 1, 0, 0))

# ---- XY0-7 の分母(S の行の数。B の行の数でない)を縛る作り物。3 組: (S 20 行・U 19 行・B 22 行)・(S 20・U 18・B 20)・(S 20・U 20・B 25)
U95_DOCS = (("S1PYU001", "E99101", 19, 1, 2), ("S1PYU002", "E99102", 18, 2, 0), ("S1PYU003", "E99103", 20, 0, 5))     # (stem, コード, E が合う S の行, E が違う S の行, S でない行)
#: 手で数える: S の U の率は 95.0%・90.0%・100.0%。B の行は 22・20・25。S の行で割れば 95 以上は 1 本目と 3 本目の 2 本。B の行で割ると 19/22=86.4%・20/25=80% で 0 本
U95_WANT = dict(docs_u95=2, docs_rows=3, s=(20, 20, 20), b=(22, 20, 25), pct=(95.0, 90.0, 100.0))


def u95_doc(good, bad, other):
    return [("0a_ixbrl.htm", file_of([(H_BS, [row(u"資産", STD + u"Assets")] * good + [row(u"資産", STD + u"Zed")] * bad + [row(u"前期特有", CRP + u"Foo")] * other)]))]


# 今年の側 5 本(番号 1〜5)。D3(番号 3)は前の年の側に zip が無い → 除く
CUR = [("S1PYD001", "E99001", d1_cur), ("S1PYD002", "E99002", d2_cur), ("S1PYD003", "E99003", d3_cur), ("S1PYD004", "F9904A", d4_cur), ("S1PYD005", "E99005", d5_cur)]
#: 前の年の側の stem は、今年の側の番号の順(1・2・4・5)が昇順の逆になるようにする(番号の順と昇順を見分けるため)
PRV = {"E99001": ("S1PRV005", d1_prior), "E99002": ("S1PRV004", prior_bs), "F9904A": ("S1PRV002", prior_bs), "E99005": ("S1PRV001", d5_prior)}
CUR_STEMS = [c[0] for c in CUR]
PRV_STEMS = ["S1PRV005", "S1PRV004", "S1PRV002", "S1PRV001"]
PAIR_NUMBERS = [1, 2, 4, 5]
CUR_END, PRV_END = "2026-03-31", "2025-03-31"


def fname(code, end, no=1, suffix=u".xsd"):
    return u"XBRL/PublicDoc/jpcrp030000-asr-%03d_%s-000_%s_01_%s%s" % (no, code, end, end[:4] + u"-06-30", suffix)


def make_doc_zip(path, code, end, texts, decoys=True):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(fname(code, end), b"<schema/>")
        for n, t in texts:
            z.writestr(fname(code, end, suffix=u"_" + n), t.encode("utf-8"))
        if decoys:          # PublicDoc の外の ixbrl・提出者のラベルと def・あとの順の file(別のコード。最初に当たるのは -001_)
            z.writestr(u"XBRL/AuditDoc/0000_audit_ixbrl.htm", file_of([(H_BS, [row(u"資産", STD + u"Decoy")] * 3)]).encode("utf-8"))
            z.writestr(fname(code, end, suffix=u"_lab.xml"), linkbase([(u"jppfs_cor_Foo", R_STD, u"未登録", "ja")]))
            z.writestr(fname(u"E99999", end, no=2, suffix=u"_lab.xml"), b"<x/>")


def make_dirs(d, cur_end=CUR_END, prv_end=PRV_END):
    docs, prior = os.path.join(d, "docs"), os.path.join(d, "prior")
    os.makedirs(docs)
    os.makedirs(prior)
    for stem, code, fn in CUR:
        make_doc_zip(os.path.join(docs, stem + ".zip"), code, cur_end, fn())
    other = os.path.join(docs, "S1OTHER1.zip")
    with zipfile.ZipFile(other, "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99998-000.xsd", b"<schema/>")
    for code, (stem, fn) in sorted(PRV.items()):
        make_doc_zip(os.path.join(prior, stem + ".zip"), code, prv_end, fn())
    make_doc_zip(os.path.join(prior, "S1PRV777.zip"), "E99777", prv_end, prior_bs())                  # 今年の側に相手が居ない会社
    with zipfile.ZipFile(os.path.join(prior, "S1PRVOTH.zip"), "w") as z:                                # 有報の様式でない
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99001-000.xsd", b"<schema/>")
    return docs, prior


FAKE_WALL = {u"書類": [od([(u"番号", 1), (u"計算書の行の数", 10)]), od([(u"番号", 2), (u"計算書の行の数", 20)]), od([(u"番号", 3), (u"計算書の行の数", 7)]),
                      od([(u"番号", 4), (u"計算書の行の数", 20)]), od([(u"番号", 5), (u"計算書の行の数", 0)])]}


# ---- 手で数えた値
#: (S の行, B の行, S の段 P・PK・C ((U, A, W1, W2, N) ずつ), B の段 P・PK, 標準の表へ落ちた行, その行の段 C の類, 段 PK・S の U の率)
HAND_PAIRS = [
    (10, 13, ((1, 7, 0, 1, 1), (3, 1, 2, 1, 3), (4, 1, 2, 1, 2)), ((2, 7, 0, 2, 2), (4, 1, 3, 1, 4)), 3, (1, 0, 0, 0, 2), 30.0),
    (20, 20, ((19, 0, 1, 0, 0), (19, 0, 1, 0, 0), (19, 0, 1, 0, 0)), ((19, 0, 1, 0, 0), (19, 0, 1, 0, 0)), 0, (0, 0, 0, 0, 0), 95.0),
    (20, 20, ((18, 0, 2, 0, 0), (18, 0, 2, 0, 0), (18, 0, 2, 0, 0)), ((18, 0, 2, 0, 0), (18, 0, 2, 0, 0)), 0, (0, 0, 0, 0, 0), 90.0),
    (0, 1, ((0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0)), ((1, 0, 0, 0, 0), (1, 0, 0, 0, 0)), 0, (0, 0, 0, 0, 0), None)]
HAND_TOTAL = dict(s=50, b=54, S=((38, 7, 3, 1, 1), (40, 1, 5, 1, 3), (41, 1, 5, 1, 2)), B=((40, 7, 3, 2, 2), (42, 1, 6, 1, 4)), fall=3, fallc=(1, 0, 0, 0, 2),
                  docs_rows=3, docs_u95=1,
                  rates=dict(xy1=76.0, xy2=80.0, xy3=10.0, xy3b=11.1, xy4=6.0, xy5u=82.0, xy5w=10.0, b=77.8, s=80.0, diff=-2.2))


def acc_hand(acc):
    cl = lambda d: tuple(d.values())                                                                      # noqa: E731
    return (acc["s"], acc["b"], tuple(cl(acc["S"][s]) for s in ("P", "PK", "C")), tuple(cl(acc["B"][s]) for s in ("P", "PK")), acc["fall"], cl(acc["fallc"]))


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XY0-1", (72, 88)), ("XY0-2", (84, 95)), ("XY0-3", (None, 1.5)), ("XY0-4", (3, 12)), ("XY0-5", ((86, 97), (None, 2.5))), ("XY0-6", (-5, None)), ("XY0-7", (10, 40))])
SEAL_BOUND_TEXT = {
    "XY0-1": u"段 P・集まり S の類 U は 72% 以上 88% 以下", "XY0-2": u"段 PK・集まり S の類 U は 84% 以上 95% 以下", "XY0-3": u"段 PK・集まり S の類 W1 は 1.5% 以下",
    "XY0-4": u"段 PK・集まり S の類 N は 3% 以上 12% 以下", "XY0-5": u"類 U は 86% 以上 97% 以下で、類 W1 は 2.5% 以下",
    "XY0-6": u"集まり B が集まり S より 5 ポイントを超えて低くはならない", "XY0-7": u"U の率が 95% 以上の書類は 10 本以上 40 本以下"}
FILE_RE_PATTERN = r"^jpcrp030000-asr-\d{3}_([^_\-]+)-\d{3}_(\d{4})-(\d{2})-(\d{2})"


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL:
        out.append(u"封の commit・path が門と違う")
    for rel in (SCRIPT_REL, RECORD_REL, GATE_REL):
        if rel not in seal:
            out.append(u"封に path が無い: %s" % rel)
    if ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL or ms.WALL_RECORD_REL != WALL_RECORD_REL:
        out.append(u"script の path が門と違う")
    want_prior = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-prior-2026-11-02")
    if ms.PRIOR_DIR != want_prior or ms.PRIOR_DIR == ms.DOCS_DIR or os.path.dirname(ms.PRIOR_DIR) != os.path.dirname(ms.DOCS_DIR) or u"`~/.cache/audit-core/edinet-prior-2026-11-02/`" not in seal:
        out.append(u"前の年の側の置き場が封の字(edinet-prior-2026-11-02。今年の側の edinet/ でない)と違う")
    if ms.PAIRS_WANT != 63 or u"組の数は 63(違えば script は止まる)" not in seal:
        out.append(u"組の数 63 が封と違う")
    if ms.DOCS_WANT != 67 or u"同じ 67 本" not in seal:
        out.append(u"今年の側の本数 67 が封と違う")
    if ms.FILE_RE.pattern != FILE_RE_PATTERN or u"`jpcrp030000-asr-` + 数字 3 つ + `_` + 提出者のコード + `-` + 数字 3 つ + `_` + 期末の日付(`YYYY-MM-DD`)の形" not in seal:
        out.append(u"組の作り方の file 名の形が封と違う")
    if u"file 名の昇順)から、提出者のコードと期末を読む" not in seal or u"提出者のコードが同じ zip がちょうど 1 本で、その期末が今年の期末と月日が同じ・年が 1 つ前" not in seal \
            or u"当たる zip が無い今年の書類は分母から除く" not in seal or u"2 本以上当たる・期末が合わない、が 1 つでも在れば script は止まる" not in seal:
        out.append(u"封の組の作り方の字が違う")
    if ms.STATEMENT_PREFIX != u"jppfs_cor" or u"E の接頭辞が `jppfs_cor` の行" not in seal or u"**集まり B**(1 行に要素が 1 種類の行の全部): 接頭辞を問わない" not in seal:
        out.append(u"集まり S・B の決めが封と違う")
    if tuple(ms.CLASSES) != (u"U", u"A", u"W1", u"W2", u"N") or tuple(ms.STAGES_S) != (u"P", u"PK", u"C") or tuple(ms.STAGES_B) != (u"P", u"PK"):
        out.append(u"段・類の名が封と違う")
    for w in (u"**段 P**", u"**段 PK**", u"**段 C**", u"**U**", u"**A**", u"**W1**", u"**W2**", u"**N**", u"表 P: T → その T を持つ行の E の集まり", u"表 PK: (K, T) → その (K, T) を持つ行の E の集まり"):
        if w not in seal:
            out.append(u"封に字が無い: %s" % w)
    if u"段 PK の候補が 1 つ以上なら段 PK の候補。空なら、便 XG1 の段 3 の候補(cand3。局所名に `jppfs_cor:` を付けた字で比べる)" not in seal or ms.STD_PREFIX_COLON != u"jppfs_cor:":
        out.append(u"段 C の決めが封と違う")
    if ms.U_DOC_THRESHOLD_PCT != 95 or u"U の率が 95% 以上の書類は 10 本以上 40 本以下" not in seal:
        out.append(u"XY0-7 の 95% が封と違う")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [ln for ln in seal.splitlines() if re.match(r"^\| %s[ (]" % re.escape(k), ln)]
        if len(row_) != 1 or t not in row_[0]:
            out.append(u"封の予測の行の字が違う: %s" % k)
    if u"docID・会社の名・EDINET コード・期末の日付・file の名・行の字・見出しの字・要素の名は書かない" not in seal or u"engine の指紋" not in seal or u"材料の並びの sha256" not in seal:
        out.append(u"封の記録の項目・禁止の字が違う")
    if u"63 本の S の行の合計が、便 XG0 の記録の同じ書類の番号の行の数の合計と違えば script は止まる" not in seal:
        out.append(u"封の S の行の合計の照合の字が違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    want_seal = (u"専用の道具が組んだ後の字", u"前の年の XBRL が在る会社にしか使えない", u"前に無かった行(N)".replace(u"前に", u"前の年に"), u"63 組は無作為ではない", u"期・連結か個別か", u"「XBRL を作れる」")
    want_script = (u"専用の道具が組んだ後の字", u"前の年の XBRL が在る会社にしか使えない", u"前の年に無かった行(N)", u"63 組は無作為ではない", u"期・連結か個別か", u"「XBRL を作れる」")
    if len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")]) != 6:
        out.append(u"封 §7 の限界の行が 6 行でない")
    if len(ms.LIMITS) != 6 or any(p not in sec7 for p in want_seal) or any(p not in u"".join(ms.LIMITS) for p in want_script):
        out.append(u"限界の 6 行が封 §7 と違う")
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


def wall_record_problems():
    u"""便 XG0 の記録(repo の中)の書類の並びは番号 1.. の順(S の行の合計の照合が頼る形)。"""
    with io.open(os.path.join(ROOT, WALL_RECORD_REL), encoding="utf-8") as fh:
        wall = json.load(fh, object_pairs_hook=od)
    docs = wall[u"書類"]
    if len(docs) != 67 or [d[u"番号"] for d in docs] != list(range(1, 68)):
        return [u"便 XG0 の記録の書類の番号が 1 から 67 の順でない"]
    return []


# ======================================================================== 2. 組の作り方
def pair_problems(ms=None):
    ms = ms or MS
    out = []
    # 形の読み取り
    nm = [u"XBRL/AuditDoc/jpcrp030000-asr-001_E11111-000_2020-03-31.xsd", fname("E00007", "2026-03-31", no=2, suffix=u"_b.htm"),
          fname("E00008", "2026-03-31", no=1, suffix=u"_a.htm"), u"XBRL/PublicDoc/readme.txt", u"XBRL/PublicDoc/"]
    if ms.code_and_end(nm) != ("E00008", (2026, "03", "31")):
        out.append(u"形の読み取りが違う(PublicDoc の中・file 名の昇順で最初に当たるもの): %s" % (ms.code_and_end(nm),))
    if ms.code_and_end([u"XBRL/PublicDoc/jpsps070000-xxx-001_E1-000_2026-03-31.xsd", u"XBRL/AuditDoc/jpcrp030000-asr-001_E11111-000_2020-03-31.xsd"]) is not None:
        out.append(u"形に当たらない zip が None でない")
    with Temp() as d:
        docs, prior = make_dirs(d)
        dd, pairs, excl = ms.make_pairs(docs, prior, 5, 4)
        got = [(p[0], p[1], p[3], p[5]) for p in pairs]
        want = [(1, "S1PYD001", "S1PRV005", "E99001"), (2, "S1PYD002", "S1PRV004", "E99002"), (4, "S1PYD004", "S1PRV002", "F9904A"), (5, "S1PYD005", "S1PRV001", "E99005")]
        if got != want or excl != 1 or [x[0] for x in dd] != CUR_STEMS:
            out.append(u"組が違う(番号・今年の側・前の年の側・コード・除いた数): %s %s" % (got, excl))
        for p in pairs:
            if os.path.basename(p[2]) != p[1] + ".zip" or os.path.basename(p[4]) != p[3] + ".zip" or p[2].startswith(prior) or p[4].startswith(docs):
                out.append(u"組の path が今年の側・前の年の側の置き場を取り違えている")
        # 除く: 前の年の側の相手を 1 つ減らすと、組の数 3・除く 2(組の数が違えば止まるので want を 3 にして通す)
        os.remove(os.path.join(prior, "S1PRV001.zip"))
        dd, pairs3, excl3 = ms.make_pairs(docs, prior, 5, 3)
        if [p[0] for p in pairs3] != [1, 2, 4] or excl3 != 2:
            out.append(u"当たる zip が無い書類を除いていない: %s %s" % ([p[0] for p in pairs3], excl3))
        if not stops(ms, ms.make_pairs, docs, prior, 5, 4):
            out.append(u"組の数が違うのに止まらない")
    with Temp() as d:                                   # 2 本以上
        docs, prior = make_dirs(d)
        make_doc_zip(os.path.join(prior, "S1PRV009.zip"), "E99002", PRV_END, prior_bs())
        if not stops(ms, ms.make_pairs, docs, prior, 5, 4):
            out.append(u"提出者のコードが同じ zip が 2 本在るのに止まらない")
    for label, cur_end, prv_end in (("1 年前でない(同じ年)", CUR_END, CUR_END), ("2 年前", CUR_END, "2024-03-31"), ("月日が違う", CUR_END, "2025-04-30"), ("日だけ違う", CUR_END, "2025-03-30")):
        with Temp() as d:
            docs, prior = make_dirs(d, cur_end, prv_end)
            if not stops(ms, ms.make_pairs, docs, prior, 5, 4):
                out.append(u"期末が合わないのに止まらない: %s" % label)
    with Temp() as d:                                   # 今年の側で形が読めない書類
        docs, prior = make_dirs(d)
        with zipfile.ZipFile(os.path.join(docs, "S1PYD003.zip"), "w") as z:
            z.writestr(u"XBRL/PublicDoc/jpcrp030000-asr-001.xsd", b"<schema/>")
        if not stops(ms, ms.make_pairs, docs, prior, 5, 4):
            out.append(u"今年の側で提出者のコードと期末が読めない書類が在るのに止まらない")
    with Temp() as d:                                   # 本数が違えば今年の側の選びが止まる
        docs, prior = make_dirs(d)
        if not stops(ms, ms.make_pairs, docs, prior, 6, 4):
            out.append(u"今年の側の本数が違うのに止まらない")
    return out


# ======================================================================== 3. 行・表・段・類
def row_problems(ms=None):
    ms = ms or MS
    out = []
    if ms.row_info(row(u"資産", STD + u"Assets", STD + u"Assets")) != (u"資産", STD + u"Assets") or ms.row_info(row(u"資産", CRP + u"Foo")) != (u"資産", CRP + u"Foo"):
        out.append(u"行が違う(E は name の字そのまま・接頭辞を問わない)")
    if ms.row_info(row(u"資産", STD + u"A", STD + u"B")) is not None or ms.row_info(u"<tr><td>資産</td><td>1</td></tr>") is not None:
        out.append(u"name が 2 種類・ix:nonFraction が無い行を拾っている")
    if ms.row_info(u"<tr><td></td><td>%s</td></tr>" % (NFTAG % (STD + u"A"))) is not None or ms.row_info(u"<tr><td>12,345</td><td>%s</td></tr>" % (NFTAG % (STD + u"A"))) is not None:
        out.append(u"行の字が無い行を拾っている")
    if ms.row_info(row(u"ＡＢ　Ｃ", STD + u"A")) != (u"ABC", STD + u"A"):
        out.append(u"行の字の NFKC・空白除きが無い: %s" % (ms.row_info(row(u"ＡＢ　Ｃ", STD + u"A")),))
    if not ms.is_s(STD + u"A") or ms.is_s(CRP + u"A") or ms.is_s(u"jpsub:A") or ms.is_s(u"jppfs_corX:A"):
        out.append(u"集まり S の判定が違う(接頭辞が jppfs_cor ちょうど)")
    rows = ms.file_row_list(d1_cur()[1][1])                    # 0a_ixbrl
    if [(r[0], r[1], r[2], r[3]) for r in rows[:5]] != [(u"資産", STD + u"Assets", H_BS, "bs"), (u"その他", STD + u"OthBs", H_BS, "bs"), (u"現金", STD + u"Cash", H_BS, "bs"),
                                                          (u"現金", STD + u"Zzz", H_BS, "bs"), (u"新科目", STD + u"NewItem", H_BS, "bs")] or len(rows) != 9:
        out.append(u"file の行の切り方が違う: %s" % len(rows))
    rows_b = ms.file_row_list(d1_cur()[0][1])                  # 0b_ixbrl(見出しが前の file から漏れない)
    if [(r[0], r[3]) for r in rows_b] != [(u"資産", None), (u"前期特有", None), (u"新B", None), (u"資産", "bs")]:
        out.append(u"見出しが file をまたいでいる(か K が違う)")
    return out


def tables_problems(ms=None):
    ms = ms or MS
    p, pk = ms.build_tables(d1_prior())
    out = []
    if p != HAND_P:
        out.append(u"表 P が手の値と違う: %s" % p)
    if pk != HAND_PK:
        out.append(u"表 PK が手の値と違う: %s" % pk)
    if ms.stage_p(p, u"資産") != HAND_P[u"資産"] or ms.stage_p(p, u"無い") != set():
        out.append(u"段 P が違う")
    if ms.stage_pk(pk, "bs", u"資産") != {STD + u"Assets"} or ms.stage_pk(pk, None, u"資産") != {STD + u"AssetsNote"} or ms.stage_pk(pk, "pl", u"資産") != set() or ms.stage_pk(pk, "cf", u"現金") != set():
        out.append(u"段 PK が違う(K が決まらない行は決まらない同士)")
    tax, l2 = fake_tax(ms), fake_l2(ms)
    if ms.std_cands(u"新科目", "bs", "cai", l2, tax) != {STD + u"NewItem"} or ms.std_cands(u"現金", "cf", "cai", l2, tax) != set() or ms.std_cands(u"負債", "pl", "cai", l2, tax) != set():
        out.append(u"標準の表の候補が違う(接頭辞つき・便 XG1 の段 3)")
    if ms.std_cands(u"現金", "bs", None, l2, tax) != {STD + u"Cash"} or ms.std_cands(u"現金", None, "cai", l2, tax) != {STD + u"Cash", STD + u"CashEq"}:
        out.append(u"標準の表の候補が違う(I か K が決まらないときは段 2 のまま)")
    if ms.stage_c({u"x"}, {u"y"}) != {u"x"} or ms.stage_c(set(), {u"y"}) != {u"y"} or ms.stage_c(set(), set()) != set():
        out.append(u"段 C が違う(PK の候補が在れば PK・空なら標準の表)")
    return out


def classify_problems(ms=None):
    ms = ms or MS
    f = ms.classify5
    cases = [(u"e", {u"e"}, "U"), (u"e", {u"e", u"f"}, "A"), (u"e", {u"e", u"f", u"g"}, "A"), (u"e", {u"f"}, "W1"), (u"e", {u"f", u"g"}, "W2"), (u"e", {u"f", u"g", u"h"}, "W2"), (u"e", set(), "N")]
    return [u"類が違う: %s %s -> %s" % (e, sorted(c), f(e, c)) for e, c, w in cases if f(e, c) != w]


# ======================================================================== 4. 書類ごと・合計
def count_hand_pair(ms, cur, prv, secret=None):
    return ms.count_pair(cur, prv, fake_l2(ms), fake_tax(ms), secret)


def doc_problems(ms=None):
    ms = ms or MS
    out = []
    cases = [(d1_cur, d1_prior), (d2_cur, prior_bs), (d4_cur, prior_bs), (d5_cur, d5_prior)]
    for k, (cf, pf) in enumerate(cases):
        got = acc_hand(count_hand_pair(ms, cf(), pf()))
        h = HAND_PAIRS[k]
        if got != (h[0], h[1], h[2], h[3], h[4], h[5]):
            out.append(u"組 %d の数が手で数えた値と違う: %s" % (k + 1, got))
    # 前の年の側として今年の側を読むと違う数になる(取り違えを見分ける)
    bad = acc_hand(count_hand_pair(ms, d1_cur(), d1_cur()))
    if bad == acc_hand(count_hand_pair(ms, d1_cur(), d1_prior())):
        out.append(u"作り物が前の年の側と今年の側を見分けない")
    return out


def totals_problems(ms=None):
    ms = ms or MS
    out = []
    accs = [count_hand_pair(ms, cf(), pf()) for cf, pf in [(d1_cur, d1_prior), (d2_cur, prior_bs), (d4_cur, prior_bs), (d5_cur, d5_prior)]]
    tot = ms.totals(accs)
    t = HAND_TOTAL
    cl = lambda d: tuple(d.values())                                                                      # noqa: E731
    if (tot["s"], tot["b"], tuple(cl(tot["S"][s]) for s in ("P", "PK", "C")), tuple(cl(tot["B"][s]) for s in ("P", "PK")), tot["fall"], cl(tot["fallc"])) != (t["s"], t["b"], t["S"], t["B"], t["fall"], t["fallc"]):
        out.append(u"合計が手で数えた値と違う")
    # 行の合計の照合(便 XG0 の記録)
    rows = {1: 10, 2: 20, 4: 20, 5: 0}
    if guard(ms.check_expected, rows, None) is not None:
        out.append(u"記録が無い(None)のとき照合を飛ばさない")
    if guard(ms.check_expected, rows, FAKE_WALL) is not None:
        out.append(u"合っている行の合計で止まる")
    if not stops(ms, ms.check_expected, {1: 10, 2: 20, 4: 21, 5: 0}, FAKE_WALL):
        out.append(u"行の合計が違うのに止まらない")
    if guard(ms.check_expected, {1: 10, 2: 20, 3: 7, 5: 0}, FAKE_WALL) is not None:
        out.append(u"番号 3 を組に入れた合計も、同じ番号どうしで照らして合う")
    if not stops(ms, ms.check_expected, {1: 10, 2: 20, 3: 7, 4: 20, 5: 0, 6: 0}, dict(FAKE_WALL, **{u"書類": FAKE_WALL[u"書類"][:5]})):
        out.append(u"便 XG0 の記録の長さを超えた番号で止まらない")
    if not stops(ms, ms.check_expected, {1: 10, 9: 0}, FAKE_WALL):
        out.append(u"便 XG0 の記録に無い番号で止まらない")
    return out


# ======================================================================== 5. 記録・止まる条件・配線
def clean_problems(ms=None):
    ms = ms or MS
    out = []
    secret = (set([u"資産"]), set([u"Assets"]), ["S1PYD001", "S1PRV005"], set(["E99001"]), set([u"貸借対照表"]), set([u"cai"]))
    for what, bad in ((u"docID の形", od([(u"x", u"S1PYD999")])), (u"EDINET コードの形", od([(u"x", u"E99991")])), (u"日付の形", od([(u"x", u"2026-03-31")])),
                      (u"禁止の欄", od([(u"docid", 1)])), (u"禁止の欄(名)", od([(u"name", 1)])), (u"今年の側の docID", od([(u"x", u"a S1PYD001 b")])),
                      (u"前の年の側の docID", od([(u"x", u"a S1PRV005 b")])), (u"コード", od([(u"x", u"a E99001 b")])), (u"要素の名", od([(u"x", u"a Assets b")])),
                      (u"行の字", od([(u"x", u"資産")])), (u"見出しの字", od([(u"x", u"貸借対照表")])), (u"業種の値", od([(u"x", u"a cai b")]))):
        if not stops(ms, ms.record_text, bad, secret):
            out.append(u"記録の検査が止めない: %s" % what)
    if stops(ms, ms.record_text, od([(u"a", 1), (u"seal", ms.SEAL_REL)]), secret):
        out.append(u"封の path の中の日付で止まる(封の path は書いてよい)")
    with Temp() as d:
        p = os.path.join(d, "r.json")
        good = od([(u"x", 1)])
        ms.write_record(p, good)
        if not stops(ms, ms.write_record, p, good):
            out.append(u"記録が既に在るのに書き直せる")
        q = os.path.join(d, "q.json")
        orig = ms.write_exclusive
        ms.write_exclusive = lambda path, data: orig(path, data + b" 2026-03-31")
        try:
            stopped = stops(ms, ms.write_record, q, good)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(q):
            out.append(u"書いた後の検査が止めない(か file を消さない)")
        v = os.path.join(d, "v.json")
        ms.write_exclusive = lambda path, data: orig(path, b"{}")
        try:
            stopped = stops(ms, ms.write_record, v, od([(u"x", u"2026-03-31")]))
        finally:
            ms.write_exclusive = orig
        if not stopped:
            out.append(u"書く前の検査が止めない(書いた後の検査だけで止まっている)")
    return out


def run_kw(d, docs, prior):
    return dict(docs=docs, prior=prior, taxonomy=os.path.join(d, "tax"), taxzip=os.path.join(d, "t.zip"), check_sha=False, want_docs=5, want_pairs=4)


def write_wall(path, wall=None):
    wall = wall or FAKE_WALL
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(wall, ensure_ascii=False))


def e2e_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    orig = patched_labels(ms)
    try:
        with Temp() as d:
            docs, prior = make_dirs(d)
            make_tax_zip(os.path.join(d, "t.zip"))
            wp = os.path.join(d, "wall.json")
            write_wall(wp)
            rec_path = os.path.join(d, "rec", "r.json")
            kw = run_kw(d, docs, prior)
            say = []
            # 下見: 記録を書かず数を出さない
            ms.dry_run(wall_path=wp, say=say.append, **kw)
            if say != [u"--dry-run: 4 組・止まらない(記録は書かない)"] or os.path.exists(os.path.join(d, "rec")) or os.path.exists(os.path.join(ROOT, RECORD_REL)):
                out.append(u"下見が記録を書いた・数を出した: %s" % say)
            bw = os.path.join(d, "wall_bad.json")
            write_wall(bw, dict(FAKE_WALL, **{u"書類": [FAKE_WALL[u"書類"][0], od([(u"番号", 2), (u"計算書の行の数", 21)])] + FAKE_WALL[u"書類"][2:]}))
            if not stops(ms, ms.dry_run, wall_path=bw, say=lambda *a: None, **kw):
                out.append(u"下見が S の行の合計の違いで止まらない")
            lines = []
            rec = ms.run(root=d, out=rec_path, wall_path=wp, say=lines.append, **kw)
            if not os.path.isfile(rec_path) or lines != [u"-> r.json(組 4)"]:
                out.append(u"本番が記録を書かない: %s" % lines)
            mat = rec[u"材料"]
            if (mat[u"今年の側の書類の本数"], mat[u"組の数"], mat[u"除いた今年の書類の数"]) != (5, 4, 1):
                out.append(u"材料の数が違う: %s" % dict(mat))
            if mat[u"今年の側の書類の file 名の並びの sha256"] != hashlib.sha256(u"\n".join(CUR_STEMS).encode("utf-8")).hexdigest():
                out.append(u"今年の側の並びの sha256 が違う")
            if mat[u"前の年の側の組の相手の file 名の並びの sha256"] != hashlib.sha256(u"\n".join(PRV_STEMS).encode("utf-8")).hexdigest():
                out.append(u"前の年の側の組の相手の並びの sha256 が違う(今年の側の番号の順)")
            fp = ms.VD.engine_fingerprint()
            fp_keys = ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files")
            if list(rec[u"engine の指紋"].keys()) != list(fp_keys) or any(not rec[u"engine の指紋"][k] for k in fp_keys) or any(rec[u"engine の指紋"][k] != fp[k] for k in fp_keys):
                out.append(u"記録の engine の指紋が engine の指紋でない(か空): %s" % dict(rec[u"engine の指紋"]))
            if rec[u"この script の sha256"] != sha_of(SCRIPT_REL):
                out.append(u"記録の script の sha256 が script の file の sha256 でない(か空)")
            seal_limits = [ln for ln in seal_text().split(u"## §7", 1)[-1].splitlines() if ln.startswith(u"- ")]
            if len(seal_limits) != 6 or len(rec[u"限界"]) != 6 or rec[u"限界"] != list(ms.LIMITS):
                out.append(u"記録の限界が封 §7 の行の数(6)と違う: %d" % len(rec[u"限界"]))
            with open(os.path.join(d, "t.zip"), "rb") as fh:
                zsha = hashlib.sha256(fh.read()).hexdigest()
            lsha = hashlib.sha256(FAKE_LABELS).hexdigest()
            if lsha == zsha or mat[u"標準ラベルの file の sha256"] != lsha or mat[u"標準タクソノミの zip の sha256"] != zsha:
                out.append(u"標準ラベルの sha256・標準タクソノミの zip の sha256 の欄が材料の file の sha256 でない(か取り違えている)")
            docs_rec = rec[u"書類"]
            if [r[u"番号"] for r in docs_rec] != PAIR_NUMBERS:
                out.append(u"書類の番号が違う(除いた書類の番号は飛ぶ): %s" % [r[u"番号"] for r in docs_rec])
            for k, r in enumerate(docs_rec):
                h = HAND_PAIRS[k]
                got = (r[u"集まり S の行の数"], r[u"集まり B の行の数"], tuple(tuple(r[u"集まり S の段ごとの類別"][s].values()) for s in ("P", "PK", "C")),
                       tuple(tuple(r[u"集まり B の段ごとの類別"][s].values()) for s in ("P", "PK")), r[u"段 C で標準の表へ落ちた S の行の数"], tuple(r[u"段 C で標準の表へ落ちた S の行の類別"].values()))
                if got != h[:6] or r[u"段 PK・集まり S の U の率(%)"] != h[6]:
                    out.append(u"記録の書類 %d が手で数えた値と違う: %s" % (k + 1, got))
            t = HAND_TOTAL
            agg = rec[u"集計"]
            if (agg[u"集まり S の行の数"], agg[u"集まり B の行の数"], tuple(tuple(agg[u"集まり S の段ごとの類別"][s].values()) for s in ("P", "PK", "C")),
                    tuple(tuple(agg[u"集まり B の段ごとの類別"][s].values()) for s in ("P", "PK")), agg[u"段 C で標準の表へ落ちた S の行の数"],
                    tuple(agg[u"段 C で標準の表へ落ちた S の行の類別"].values()), agg[u"集まり S の行が 1 行以上在る書類の数"]) \
                    != (t["s"], t["b"], t["S"], t["B"], t["fall"], t["fallc"], t["docs_rows"]):
                out.append(u"集計が手で数えた値と違う: %s" % dict(agg))
            pv = list([v for k, v in rec.items() if k.startswith(u"予測の判定に要る数")][0].values())
            rt = t["rates"]
            want_pct = [rt["xy1"], rt["xy2"], rt["xy3"], rt["xy3b"], rt["xy4"], rt["xy5u"], rt["xy5w"]]
            for j, w in enumerate(want_pct):
                if pv[j][u"%"] != w:
                    out.append(u"判定の数 %d の率が手で数えた値と違う: %s" % (j, dict(pv[j])))
            if (pv[0][u"行"], pv[0][u"分母"], pv[1][u"行"], pv[2][u"行"], pv[3][u"分母"], pv[4][u"行"], pv[5][u"行"], pv[6][u"行"]) != (38, 50, 40, 5, 45, 3, 41, 5):
                out.append(u"判定の数の行・分母が違う")
            x6 = pv[7]
            if (x6[u"集まり B の U の行"], x6[u"集まり B の行"], x6[u"集まり B の %"], x6[u"集まり S の U の行"], x6[u"集まり S の行"], x6[u"集まり S の %"],
                    x6[u"集まり B から集まり S を引いた差(ポイント)"]) != (42, 54, rt["b"], 40, 50, rt["s"], rt["diff"]):
                out.append(u"XY0-6 の数が違う: %s" % dict(x6))
            x7 = pv[8]
            if (x7[u"書類"], x7[u"分母"], x7[u"集まり S の行が 1 行以上在る書類"]) != (t["docs_u95"], 4, t["docs_rows"]):
                out.append(u"XY0-7 の数が違う(95.0% は含む・90.0% は含まない・行の無い書類は分母に入れない): %s" % dict(x7))
            text = io.open(rec_path, encoding="utf-8").read()
            for leak in CUR_STEMS + PRV_STEMS + [u"E99", u"F9904A", u"S1PYD", u"S1PRV", u"Assets", u"Cash", u"資産", u"現金", u"貸借対照表", u"注記事項", u"CAI", u"cai", u"2026-03", u"2025-03", u"jppfs", u"S1OTHER1"]:
                if leak in text:
                    out.append(u"記録に材料の字が在る: %s" % leak)
            if not stops(ms, ms.run, root=d, out=rec_path, wall_path=wp, say=lambda *a: None, **kw):
                out.append(u"記録が既に在るのに run が止まらない")
            ms.check(root=d, rec_path=rec_path, wall_path=wp, say=lambda *a: None, **kw)
            bad = text.replace(u'"集まり S の行の数": 10', u'"集まり S の行の数": 11', 1)
            bp = os.path.join(d, "bad.json")
            with io.open(bp, "w", encoding="utf-8") as fh:
                fh.write(bad)
            if bad == text or not stops(ms, ms.check, rec_path=bp, wall_path=wp, say=lambda *a: None, **kw):
                out.append(u"数を変えた記録で --check が止まらない")
            if not stops(ms, ms.check, rec_path=os.path.join(d, "none.json"), wall_path=wp, say=lambda *a: None, **kw):
                out.append(u"記録が無いのに --check が止まらない")
            # 前の年の側の書類を替えると --check が止まる
            make_doc_zip(os.path.join(prior, "S1PRV005.zip"), "E99001", PRV_END, d1_cur())
            if not stops(ms, ms.check, rec_path=rec_path, wall_path=wp, say=lambda *a: None, **kw):
                out.append(u"前の年の側の書類を変えても --check が止まらない")
            # 便 XG0 の記録が無ければ止まる
            if not stops(ms, ms.run, root=d, out=os.path.join(d, "rec", "r2.json"), wall_path=os.path.join(d, "nowall.json"), say=lambda *a: None, **kw):
                out.append(u"便 XG0 の記録が無いのに run が止まらない")
    finally:
        ms.W.read_label_bytes = orig
    return out


def fill_problems(ms=None):
    u"""段 C の業種(連結の見出し→連結の DEI・それ以外→個別の DEI・K が決まらない行は段 2 のまま)・DEI を 2 つ目の file から読む・K が決まらない S の行も落ちた行に数える。"""
    ms = ms or MS
    got = acc_hand(ms.count_pair(fill_cur(), prior_bs(), FILL_L2, fill_tax(ms)))
    if got != HAND_FILL:
        return [u"業種・DEI・落ちた行の作り物が手で数えた値と違う: %s" % (got,)]
    return []


def u95_problems(ms=None):
    u"""書類ごとの 95% の判定の分母は S の行の数(B の行の数でない)。build_record を通す。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    orig = patched_labels(ms)
    try:
        with Temp() as d:
            docs, prior = os.path.join(d, "docs"), os.path.join(d, "prior")
            os.makedirs(docs)
            os.makedirs(prior)
            for k, (stem, code, good, bad, other) in enumerate(U95_DOCS):
                make_doc_zip(os.path.join(docs, stem + ".zip"), code, CUR_END, u95_doc(good, bad, other))
                make_doc_zip(os.path.join(prior, "S1PRU00%d.zip" % (k + 1)), code, PRV_END, prior_bs())
            make_tax_zip(os.path.join(d, "t.zip"))
            rec, _secret = ms.build_record(docs, prior, os.path.join(d, "tax"), os.path.join(d, "t.zip"), 3, 3, False, None, False)
            w = U95_WANT
            rows = rec[u"書類"]
            if tuple(r[u"集まり S の行の数"] for r in rows) != w["s"] or tuple(r[u"集まり B の行の数"] for r in rows) != w["b"] or tuple(r[u"段 PK・集まり S の U の率(%)"] for r in rows) != w["pct"]:
                out.append(u"95% の作り物の行の数・率が手で数えた値と違う")
            x7 = [v for k, v in rec.items() if k.startswith(u"予測の判定に要る数")][0]
            x7 = [v for k, v in x7.items() if k.startswith(u"XY0-7")][0]
            if (x7[u"書類"], x7[u"分母"], x7[u"集まり S の行が 1 行以上在る書類"]) != (w["docs_u95"], 3, w["docs_rows"]):
                out.append(u"XY0-7 の書類の数が S の行の数で割った 95% の本数でない: %s" % dict(x7))
    finally:
        ms.W.read_label_bytes = orig
    return out


def secret_problems(ms=None):
    u"""本番の ``build_record`` が作る secret の配線と、``check()`` が secret を ``check_clean`` に渡していること。作り物の置き場だけ。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    orig = patched_labels(ms)
    try:
        with Temp() as d:
            docs, prior = make_dirs(d)
            make_tax_zip(os.path.join(d, "t.zip"))
            wp = os.path.join(d, "wall.json")
            write_wall(wp)
            kw = run_kw(d, docs, prior)
            rec, secret = ms.build_record(docs, prior, os.path.join(d, "tax"), os.path.join(d, "t.zip"), 5, 4, True, wp, False)
            labels, elems, ids, ecodes, heads, inds = secret
            if sorted(ids) != sorted(CUR_STEMS + PRV_STEMS):
                out.append(u"secret の docID が今年の側と前の年の側の stem でない: %s" % (list(ids),))
            if not set([u"E99001", u"E99002", u"F9904A", u"E99005"]) <= set(ecodes):
                out.append(u"secret の EDINET コードに組の提出者のコードが無い: %s" % (sorted(ecodes),))
            if not set([u"資産", u"その他", u"現金", u"新科目", u"前期特有", u"新B", u"負債", u"ABC"]) <= set(labels) or u"Assets" not in elems or u"AssetsNote" not in elems or u"Bar" not in elems or u"Foo2" not in elems:
                out.append(u"secret の行の字・要素の名が作り物の行と違う: %s" % sorted(elems))
            if heads != set([u"貸借対照表", u"損益計算書", u"キャッシュ・フロー計算書", u"注記事項"]):
                out.append(u"secret の見出しの字が違う: %s" % sorted(heads))
            if inds != set([u"cai"]):
                out.append(u"secret の業種の値が違う: %s" % sorted(inds))
            real_build = ms.build_record
            for ln, (what, leak) in enumerate(((u"前の年の側の docID", u"a S1PRV004 b"), (u"組のコード", u"a F9904A b"), (u"見出しの字(全部一致。5 字未満)", u"注記事項"), (u"見出しの字(部分一致)", u"a キャッシュ・フロー計算書 b"), (u"業種の値", u"a cai b"),
                                               (u"要素の名", u"a AssetsNote b"), (u"行の字", u"前期特有"))):
                leaky = od(rec)
                leaky[u"仕込み"] = leak
                lp = os.path.join(d, "leak_%d.json" % ln)
                with io.open(lp, "w", encoding="utf-8") as fh:
                    fh.write(ms.dumps(leaky))
                ms.build_record = lambda *a, **k: (leaky, secret)
                try:
                    stopped = stops(ms, ms.check, rec_path=lp, wall_path=wp, say=lambda *a: None, **kw)
                finally:
                    ms.build_record = real_build
                if not stopped:
                    out.append(u"check() が secret(%s)の仕込みで止まらない" % what)
    finally:
        ms.W.read_label_bytes = orig
    return out


# ======================================================================== 6. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "glob", "hashlib", "importlib", "io", "json", "os", "re", "sys", "zipfile", "adapters")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess")
ENGINE_CALLED = ("_row_label",)
WALL_CALLED = ("NF_RE", "select_docs", "label_tables", "read_label_bytes", "order_sha256", "Stop", "HEX_RE")
NARROW_CALLED = ("file_rows", "kind_of", "dei_values", "industry_of", "narrow", "load_tax", "doc_texts", "check_clean")
NOT_COPIED = ("select_docs", "label_tables", "read_label_bytes", "order_sha256", "norm_label", "file_rows", "kind_of", "dei_values", "industry_of", "narrow", "load_tax", "doc_texts", "classify")
CAND_FUNCS = ("stage_p", "stage_pk", "stage_c", "std_cands")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
NARROW_NAME = "_xy0_tag_narrow_2026_11_21"


def import_problems(src=None):
    u"""script の import は標準ライブラリと engine の 2 module と importlib だけ。前の便の関数は ``W.``・``N.`` から呼び写さない。E は候補を作る関数に渡さない。提出者の file を読まない。"""
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
    for fn in NARROW_CALLED:
        if ("N", fn) not in attrs:
            out.append(u"便 XG1 の %s を N から呼んでいない" % fn)
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in NOT_COPIED:
        if fn in funcs:
            out.append(u"前の便の %s を script が自分で定義している(写している)" % fn)
    for fn in CAND_FUNCS:
        f = funcs.get(fn)
        if f is None:
            out.append(u"候補を作る関数 %s が無い" % fn)
            continue
        argn = [a.arg for a in f.args.args]
        used = set(x.id for x in ast.walk(f) if isinstance(x, ast.Name))
        if "E" in argn or "E" in used or any(a in ("e", "elem", "element") for a in argn):
            out.append(u"候補を作る関数 %s に E が渡っている・使われている" % fn)
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            v = n.value
            if u".env" in v or u"dotenv" in v or u"API_KEY" in v:
                out.append(u"鍵・.env の字が在る")
            if any(s in v for s in (u"_lab.xml", u"_pre.xml", u"_cal.xml", u"_def.xml")):
                out.append(u"提出者の file の名の字が在る: %s" % v)
    if NARROW_NAME not in consts:
        out.append(u"前の便の script を読む名が一意の名(%s)でない" % NARROW_NAME)
    # 前の年の側は _ixbrl.htm だけ(N.doc_texts)・今年の側と同じ関数で読む
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and (n.func.value.id, n.func.attr) == ("N", "doc_texts")]
    if len(calls) != 2:
        out.append(u"書類の字を N.doc_texts で読む呼び出しが 2 つ(今年の側・前の年の側)でない: %d" % len(calls))
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
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**約束の側から作った。予測は「その検査が赤になる」。** この表は実行より先に書いた。
MUTANTS = (
    # ---- 類
    (u"M1 W1 を U に数える", u'return "W1" if len(cands) == 1 else "W2"', u'return "U" if len(cands) == 1 else "W2"', ("classify", "doc", "e2e")),
    (u"M2 W2 を W1 に数える", u'return "W1" if len(cands) == 1 else "W2"', u'return "W1" if len(cands) >= 1 else "W2"', ("classify", "doc", "e2e")),
    (u"M3 U の条件を候補 2 つ以下にする", u'return "U" if len(cands) == 1 else "A"', u'return "U" if len(cands) <= 2 else "A"', ("classify", "doc", "e2e")),
    (u"M4 候補が無い行を N に数えない", u'    if not cands:\n        return "N"', u'    if not cands:\n        return "W2"', ("classify", "doc", "e2e")),
    (u"M5 候補が 1 つの E を含むかを見ない", u"    if E not in cands:\n        return", u"    if E in cands and False:\n        return", ("classify", "doc", "e2e")),
    # ---- 組・前の年の側
    (u"M6 前の年の側として今年の zip を読む", u"        with zipfile.ZipFile(pp) as z:", u"        with zipfile.ZipFile(p) as z:", ("doc_e2e", "e2e", "secret")),
    (u"M7 表 PK の鍵から K を外す(書く側)", u"pk.setdefault((K, T), set()).add(E)", u"pk.setdefault((None, T), set()).add(E)", ("tables", "doc", "e2e")),
    (u"M8 表 PK の鍵から K を外す(引く側)", u"return set(tab_pk.get((K, T), ()))", u"return set(tab_pk.get((None, T), ()))", ("tables", "doc", "e2e")),
    (u"M9 段 C が PK の候補が在るのに標準の表を使う", u"    if cand_pk:\n        return set(cand_pk)\n    return set(cand_std)", u"    return set(cand_std)", ("tables", "doc", "e2e")),
    (u"M10 段 C が PK と標準の表の和集合になる", u"    if cand_pk:\n        return set(cand_pk)\n    return set(cand_std)", u"    return set(cand_pk) | set(cand_std)", ("tables", "doc", "e2e")),
    (u"M11 段 C が標準の表を使わない", u"    return set(cand_std)", u"    return set()", ("tables", "doc", "e2e")),
    (u"M12 集まり S の接頭辞の絞りを外す", u'return E.split(":")[0] == STATEMENT_PREFIX', u"return True", ("rows", "doc", "e2e")),
    (u"M13 集まり S を jp で始まる接頭辞にする", u'return E.split(":")[0] == STATEMENT_PREFIX', u'return E.split(":")[0].startswith("jp")', ("rows", "doc", "e2e")),
    (u"M14 前の年の表を S の行だけから作る", u"            p.setdefault(T, set()).add(E)\n            pk.setdefault((K, T), set()).add(E)",
     u"            if not is_s(E):\n                continue\n            p.setdefault(T, set()).add(E)\n            pk.setdefault((K, T), set()).add(E)", ("tables", "doc", "e2e")),
    (u"M15 前の年の表を今年の側の字から作る", u"tab_p, tab_pk = build_tables(prior_texts, secret)", u"tab_p, tab_pk = build_tables(cur_texts, secret)", ("doc", "e2e")),
    (u"M16 候補に今年の E を足す", u"c_pk = stage_pk(tab_pk, K, T)", u"c_pk = stage_pk(tab_pk, K, T) | set([E])", ("doc", "e2e")),
    (u"M17 name が 2 種類の行を拾う", u"    if not names or len(set(names)) != 1:\n        return None", u"    if not names:\n        return None", ("rows", "tables", "doc", "e2e")),
    (u"M18 行の字に NFKC・空白除きを掛けない", u"    t = norm_label(label)", u"    t = label", ("rows", "doc", "e2e")),
    (u"M19 集まり B を S だけ数える", u'            acc["b"] += 1', u'            acc["b"] += 1 if is_s(E) else 0', ("doc", "e2e")),
    (u"M20 落ちた行の条件を段 P の空にする", u"                if not c_pk:", u"                if not c_p:", ("doc", "e2e")),
    (u"M21 標準の表の候補に接頭辞を付けない", u"STD_PREFIX_COLON + x for x", u"x for x", ("tables", "doc", "e2e")),
    # ---- 組の作り方
    (u"M22 同じコードの zip が 2 本在っても止めない", u"        if len(cands) != 1:", u"        if len(cands) < 1:", ("pairs",)),
    (u"M23 期末が合わなくても止めない", u"        if (py, pm, pd) != (y - 1, m, d):", u"        if False:", ("pairs",)),
    (u"M24 期末を同じ年で照らす", u"        if (py, pm, pd) != (y - 1, m, d):", u"        if (py, pm, pd) != (y, m, d):", ("pairs", "e2e")),
    (u"M25 組の数が違っても止めない", u"    if len(pairs) != want_pairs:", u"    if False:", ("pairs",)),
    (u"M26 除いた数を数えない", u"return docs, pairs, len(docs) - len(pairs)", u"return docs, pairs, 0", ("pairs", "e2e")),
    (u"M27 file 名の最初でなく最後に当たるものを読む", u"    for b in base:", u"    for b in reversed(base):", ("pairs", "e2e")),
    (u"M28 前の年の側の相手がなくても分母に入れる(コードの取り違え: 提出者を鍵にしない)", u"        cands = idx.get(code, [])", u"        cands = [c for cs in idx.values() for c in cs][:1]", ("pairs", "e2e")),
    # ---- 合計・判定・照合
    (u"M29 95% の境を 90% にする", u"U_DOC_THRESHOLD_PCT = 95 ", u"U_DOC_THRESHOLD_PCT = 90 ", ("seal", "e2e")),
    (u"M30 95% の境でちょうど 95.0% を含めない", u"if 100 * u_pk >= U_DOC_THRESHOLD_PCT * r:", u"if 100 * u_pk > U_DOC_THRESHOLD_PCT * r:", ("e2e",)),
    (u"M31 S の行の合計の照合を外す", u"    if sum(rows_by_number.values()) != want:", u"    if False:", ("totals", "e2e")),
    (u"M32 S の行の合計を組にならなかった番号まで足す", u"    for n in rows_by_number:", u"    for n in range(1, len(docs) + 1):", ("totals", "e2e")),
    (u"M33 XY0-6 の差の向きを逆にする", u'pct1(bpk["U"] * rs - spk["U"] * rb, rb * rs)', u'pct1(spk["U"] * rb - bpk["U"] * rs, rb * rs)', ("e2e",)),
    (u"M34 XY0-3 の分母を U だけにする", u'rate_of(spk["W1"], spk["U"] + spk["W1"])', u'rate_of(spk["W1"], spk["U"])', ("e2e",)),
    (u"M35 前の年の側の並びの sha256 を今年の側の stem で作る", u'u"\\n".join(p[3] for p in pairs)', u'u"\\n".join(p[1] for p in pairs)', ("e2e",)),
    (u"M36 予測の境 XY0-2 の上限を替える", u'("XY0-2", (84, 95))', u'("XY0-2", (84, 96))', ("seal",)),
    (u"M37 組の数を 62 にする", u"PAIRS_WANT = 63", u"PAIRS_WANT = 62", ("seal",)),
    (u"M38 file 名の形の期末を落とす", u'(\\d{4})-(\\d{2})-(\\d{2})")', u'(\\d{4})-(\\d{2})")', ("seal",)),
    # ---- 記録の検査・書き方
    (u"M39 日付の形の検査を外す", u"    if DATE_RE.search(", u"    if False and DATE_RE.search(", ("clean",)),
    (u"M40 前の年の側の docID を secret に入れない", u"[d[0] for d in docs] + [p[3] for p in pairs]", u"[d[0] for d in docs]", ("secret",)),
    (u"M41 組の提出者のコードを secret に入れない", u"set(p[5] for p in pairs), set(), set())", u"set(), set(), set())", ("secret",)),
    (u"M42 記録を排他で書かない", u'    if os.path.exists(path):\n        raise Stop(u"**記録が既に在る', u'    if False:\n        raise Stop(u"**記録が既に在る', ("clean", "e2e")),
    (u"M43 下見が記録の検査を通さない", u"    record_text(rec, secret)\n    say(u\"--dry-run", u"    say(u\"--dry-run", ("dry",)),
    (u"M44 下見が数を出す", u'say(u"--dry-run: %d 組・止まらない(記録は書かない)" % rec[u"材料"][u"組の数"])', u'say(u"--dry-run: %d 組・止まらない(記録は書かない)" % rec[u"集計"][u"集まり S の行の数"])', ("e2e",)),
    (u"M45 --check が secret を検査に渡さない", u"    check_clean(rec, text, secret)\n    say(u\"--check", u"    check_clean(rec, text)\n    say(u\"--check", ("secret",)),
    (u"M46 前の便の script を一意でない名で読む", u'name = "_xy0_tag_narrow_2026_11_21"', u'name = "xbrl_tag_narrow"', ("import",)),
    # ---- 監査 REVISE の直し(2026-11-22)で足した変異
    (u"M47 書類ごとの 95% の分母を B の行の数にする", u"if 100 * u_pk >= U_DOC_THRESHOLD_PCT * r:", u'if 100 * u_pk >= U_DOC_THRESHOLD_PCT * acc["b"]:', ("u95",)),
    (u"M48 段 C の標準の表の候補に業種を渡さない", u"std_cands(T, K, ind, l2, tax))", u"std_cands(T, K, None, l2, tax))", ("fill",)),
    (u"M49 業種を常に None にする", u'ind = N.industry_of(head, dei, tax["folders"]) if K is not None else None', u"ind = None", ("fill",)),
    (u"M50 落ちた行の条件に K が決まっていることを足す", u"                if not c_pk:", u"                if not c_pk and K is not None:", ("fill",)),
    (u"M51 記録の engine の指紋を空にする", u'rec[u"engine の指紋"] = od((k, fp[k]) for k in', u'rec[u"engine の指紋"] = od((k, u"") for k in', ("e2e",)),
    (u"M52 記録の engine の指紋の欄を持たない", u'rec[u"engine の指紋"] = od((k, fp[k]) for k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files"))',
     u'rec[u"engine の指紋"] = od()', ("e2e",)),
    (u"M53 記録の script の sha256 を空にする", u'rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))', u'rec[u"この script の sha256"] = u""', ("e2e",)),
    (u"M54 記録の限界を 5 行にする", u'rec[u"限界"] = list(LIMITS)', u'rec[u"限界"] = list(LIMITS)[:5]', ("e2e",)),
    (u"M55 標準ラベルの sha256 の欄に zip の sha256 を入れる", u'(u"標準ラベルの file の sha256", label_sha)', u'(u"標準ラベルの file の sha256", zip_sha)', ("e2e",)),
    (u"M56 前の年の側の置き場を今年の側の置き場にする", u'"edinet-prior-2026-11-02")', u'"edinet")', ("seal",)),
    (u"M57 前の年の側の並びの sha256 を昇順にする", u'u"\\n".join(p[3] for p in pairs)', u'u"\\n".join(sorted(p[3] for p in pairs))', ("e2e",)),
    (u"M58 DEI を最初の file だけで読む", u"dei = N.dei_values(cur_texts)", u"dei = N.dei_values(cur_texts[:1])", ("fill",)),
)

#: 黙るのが設計どおりの変異(同値)。理由を書き、別の試験で「黙ること」を縛る
SILENT_BY_DESIGN = (
    (u"S1 count_pair が file を昇順に並べない",
     u"    cur_texts = sorted(cur_texts, key=lambda q: q[0])\n    tab_p, tab_pk", u"    tab_p, tab_pk",
     u"行は file ごとに独立に分類し(見出しは file の中だけ)、合計は足し算で順に依らない。DEI は ``dei_values`` が自分で file 名の昇順に並べて読む。よって並べ替えは結果を変えない(同値の変異)。"),
    (u"S2 種類 K が決まらない行でも業種を計算する",
     u"ind = N.industry_of(head, dei, tax[\"folders\"]) if K is not None else None", u"ind = N.industry_of(head, dei, tax[\"folders\"])",
     u"K が None の行は便 XG1 の段 3 が段 2 のまま(kind を見る)なので、I は使われない。K が None のとき I の値は結果に効かない(同値の変異)。"))


def check_by_name(name, mod, src):
    table_ = {u"seal": seal_problems, u"pairs": pair_problems, u"rows": row_problems, u"tables": tables_problems, u"classify": classify_problems, u"doc": doc_problems,
              u"totals": totals_problems, u"clean": clean_problems, u"e2e": e2e_problems, u"secret": secret_problems, u"dry": dry_problems, u"fill": fill_problems, u"u95": u95_problems}
    if name == u"doc_e2e":
        return doc_problems(mod) or e2e_problems(mod)
    if name in table_:
        return table_[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


def dry_problems(ms=None):
    u"""下見が、記録の検査(禁止の字)に当たる材料で止まる: 要素の名が記録に入る形の作り物では、書かずに止まる。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    orig = patched_labels(ms)
    real_build = ms.build_record
    try:
        with Temp() as d:
            docs, prior = make_dirs(d)
            make_tax_zip(os.path.join(d, "t.zip"))
            wp = os.path.join(d, "wall.json")
            write_wall(wp)
            kw = run_kw(d, docs, prior)
            rec, secret = real_build(docs, prior, os.path.join(d, "tax"), os.path.join(d, "t.zip"), 5, 4, True, wp, False)
            leaky = od(rec)
            leaky[u"仕込み"] = u"a S1PRV004 b"
            ms.build_record = lambda *a, **k: (leaky, secret)
            try:
                if not stops(ms, ms.dry_run, wall_path=wp, say=lambda *a: None, **kw):
                    out.append(u"下見が記録の検査を通さない(危ない記録でも止まらない)")
            finally:
                ms.build_record = real_build
    finally:
        ms.W.read_label_bytes = orig
    return out


ALL_CHECKS = (u"seal", u"pairs", u"rows", u"tables", u"classify", u"doc", u"totals", u"clean", u"e2e", u"secret", u"dry", u"fill", u"u95", u"import")


def run_mutants(table_=MUTANTS):
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in table_:
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
        for old, new in ((u"| XY0-2(主) | 段 PK・集まり S の類 U は 84% 以上 95% 以下", u"| XY0-2(主) | 段 PK・集まり S の類 U は 84% 以上 96% 以下"),
                         (u"U の率が 95% 以上の書類は 10 本以上 40 本以下", u"U の率が 90% 以上の書類は 10 本以上 40 本以下"), (u"組の数は 63(違えば script は止まる)", u"組の数は 62(違えば script は止まる)"),
                         (u"E の接頭辞が `jppfs_cor` の行", u"E の接頭辞が `jpcrp_cor` の行"), (u"年が 1 つ前", u"年が 2 つ前"),
                         (u"| XY0-3(主) | 段 PK・集まり S の類 W1 は 1.5% 以下", u"| XY0-3(主) | 段 PK・集まり S の類 W1 は 2.5% 以下"),
                         (u"空なら、便 XG1 の段 3 の候補", u"空なら、便 XG1 の段 2 の候補"), (u"期・連結か個別か", u"期・単位")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"prior_year_draft", body)
        self.assertNotIn(u"xbrl_prior_year", body)

    def test_a_6_the_wall_record_is_numbered_one_to_sixty_seven(self):
        self.assertEqual([], wall_record_problems())


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PureTest(unittest.TestCase):
    def test_b_1_pairs_are_made_excluded_or_stopped(self):
        self.assertEqual([], pair_problems())

    def test_b_2_rows_collections_tables_and_the_three_stages(self):
        self.assertEqual([], row_problems())
        self.assertEqual([], tables_problems())

    def test_b_3_classes(self):
        self.assertEqual([], classify_problems())

    def test_b_4_made_up_pairs_equal_the_hand_count_and_the_totals(self):
        self.assertEqual([], doc_problems())
        self.assertEqual([], totals_problems())

    def test_b_5_the_hand_counts_are_not_the_same_as_nearby_numbers(self):
        u"""手で決めた値が足し算と合い、段の U が互いに違い(段 P < 段 PK < 段 C)、95% の境の上(ちょうど)と下の書類が在る。"""
        t = HAND_TOTAL
        self.assertEqual(t["s"], sum(h[0] for h in HAND_PAIRS))
        self.assertEqual(t["b"], sum(h[1] for h in HAND_PAIRS))
        for k in range(3):
            self.assertEqual(t["s"], sum(t["S"][k]))
            self.assertEqual(t["S"][k], tuple(sum(h[2][k][i] for h in HAND_PAIRS) for i in range(5)))
        for k in range(2):
            self.assertEqual(t["b"], sum(t["B"][k]))
            self.assertEqual(t["B"][k], tuple(sum(h[3][k][i] for h in HAND_PAIRS) for i in range(5)))
        self.assertEqual(t["fall"], sum(h[4] for h in HAND_PAIRS))
        self.assertEqual(t["fall"], sum(t["fallc"]))
        self.assertEqual(t["fallc"], tuple(sum(h[5][i] for h in HAND_PAIRS) for i in range(5)))
        us = [t["S"][k][0] for k in range(3)]
        self.assertEqual(len(set(us)), 3)
        self.assertTrue(us[0] < us[1] < us[2])
        self.assertNotEqual(t["S"][1][2], t["S"][1][3])                                      # W1 と W2 が違う数
        self.assertGreater(t["B"][1][0], t["S"][1][0])                                       # B の U と S の U が違う
        rates = [h[6] for h in HAND_PAIRS if h[6] is not None]
        self.assertTrue(any(r == 95.0 for r in rates) and any(r < 95 for r in rates) and any(95 > r >= 90 for r in rates))
        self.assertTrue(any(h[6] is None for h in HAND_PAIRS))
        self.assertEqual(t["docs_u95"], sum(1 for r in rates if r >= 95))
        self.assertEqual(sorted(len(v) for v in FAKE_L2.values()), [1, 1, 2, 2])                      # cand0 の大きさ 1 と 2 の両方
        self.assertEqual(len(HAND_PAIRS), 4)

    def test_b_7_industry_wiring_dei_from_a_later_file_and_the_fallen_rows_with_no_kind(self):
        self.assertEqual([], fill_problems())
        # 作り物が見分ける: 業種を使わない段 2 のままの数は、手の値と違う
        ms = MS
        no_ind = acc_hand(ms.count_pair(fill_cur(), prior_bs(), FILL_L2, ms.N.make_tax(ms.N.build_x(xsd_bytes(FILL_X)), {}, FILL_FOLDERS)))
        self.assertNotEqual(no_ind, HAND_FILL)
        self.assertEqual((1, 1, 1), HAND_FILL[2][2][:3])                                              # 連結・個別・K なしで U・A・W1 が 1 行ずつ(3 行が互いに違う類)

    def test_b_6_the_fake_zips_have_the_decoys_the_checks_say(self):
        with Temp() as d:
            docs, prior = make_dirs(d)
            with zipfile.ZipFile(os.path.join(docs, "S1PYD001.zip")) as z:
                names = z.namelist()
            self.assertTrue(any(n.startswith(u"XBRL/AuditDoc/") for n in names) and any(u"-002_E99999" in n for n in names) and any(n.endswith(u"_lab.xml") for n in names))
            self.assertTrue(os.path.exists(os.path.join(prior, "S1PRV777.zip")) and os.path.exists(os.path.join(prior, "S1PRVOTH.zip")))


class RecordTest(unittest.TestCase):
    def test_c_1_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_c_2_cache_to_record_to_check_without_reading_the_real_cache(self):
        self.assertEqual([], e2e_problems())

    def test_c_3_the_production_secret_is_built_and_check_passes_it_to_the_clean_check(self):
        self.assertEqual([], secret_problems())

    def test_c_4_the_dry_run_goes_through_the_record_check(self):
        self.assertEqual([], dry_problems())

    def test_c_6_the_per_document_95_percent_denominator_is_the_s_rows(self):
        self.assertEqual([], u95_problems())
        w = U95_WANT
        self.assertEqual(2, sum(1 for s, b in zip(w["s"], w["b"]) if b != s))                                          # b ≠ s の書類が 2 本(S で数えると 95 以上・B で数えると 95 未満)
        self.assertEqual(w["docs_u95"], sum(1 for p in w["pct"] if p >= 95))
        self.assertEqual(0, sum(1 for (g, bad, o) in [(x[2], x[3], x[4]) for x in U95_DOCS] if 100 * g >= 95 * (g + bad + o)))                  # B の行で割ると 0 本

    def test_c_5_the_real_record_when_present_is_clean(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く")
        text = read(RECORD_REL)
        rec = json.loads(text, object_pairs_hook=od)
        MS.check_clean(rec, text)


class WiringTest(unittest.TestCase):
    def test_e_1_imports_engine_calls_and_e_is_not_given_to_the_candidates(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport urllib.request\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.environ.get('A')\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef classify(T, E, table):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = '_lab.xml'\n"))
        self.assertNotEqual([], import_problems(base.replace(u"def stage_pk(tab_pk, K, T):", u"def stage_pk(tab_pk, K, T, E):")))
        self.assertNotEqual([], import_problems(base.replace(u"I._row_label(rowtext)", u"None")))
        self.assertNotEqual([], import_problems(base.replace(u"from adapters.xbrl import instance as I", u"from adapters.xbrl import instance as I\nfrom adapters.xbrl import recipes as R")))
        self.assertNotEqual([], import_problems(base.replace(u"prv = N.doc_texts(z)", u"prv = []")))

    def test_e_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_4_the_script_leaves_sys_modules_as_it_found_them_except_its_own_narrow_name(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_prior_year_draft_script_for_sysmodules_check")
        self.assertEqual([], [k for k, v in before.items() if sys.modules.get(k) is not v])
        self.assertIn(mod.N.__name__, sys.modules)
        self.assertEqual(mod.N.__name__, NARROW_NAME)
        self.assertIs(mod.W, mod.N.W)
        del mod

    def test_e_5_the_default_places_are_outside_the_repo_and_the_gate_never_opens_them(self):
        top = os.path.realpath(REPO)
        for p in (MS.DOCS_DIR, MS.PRIOR_DIR, MS.TAXONOMY_DIR, MS.TAXZIP_PATH):
            self.assertFalse(os.path.realpath(p).startswith(top + os.sep), p)
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|make_pairs|prior_index|run|check|dry_run|build_record|load_tax)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"\bd\b|docs|\*\*kw|\bp\b|prior|tz|rec_path|real_build", m.group(2)) or m.group(1) in ("build_record", "run", "check", "dry_run"), m.group(0))
        for m in re.finditer(r"ms\.(run|check|dry_run)\(([^)]*)\)", src):
            self.assertIn(u"**kw", m.group(2), m.group(0))


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
        self.assertGreaterEqual(len(MUTANTS), 40)

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)

    def test_f_3_the_silent_mutants_are_silent_for_the_stated_reason(self):
        u"""同値の変異は、作り物の全部の検査でも、元と同じ。"""
        base = read(SCRIPT_REL)
        for name, old, new, _why in SILENT_BY_DESIGN:
            self.assertEqual(1, base.count(old), name)
            mod = load_source(base.replace(old, new))
            for c in (u"pairs", u"rows", u"tables", u"classify", u"doc", u"totals", u"clean", u"e2e", u"secret", u"dry", u"fill", u"u95"):
                self.assertEqual([], check_by_name(c, mod, None), (name, c))
            for cf, pf in [(d1_cur, d1_prior), (d2_cur, prior_bs), (d5_cur, d5_prior)]:
                self.assertEqual(acc_hand(count_hand_pair(MS, cf(), pf())), acc_hand(count_hand_pair(mod, cf(), pf())), name)


if __name__ == "__main__":
    unittest.main()
