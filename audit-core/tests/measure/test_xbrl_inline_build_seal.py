# -*- coding: utf-8 -*-
u"""封 docs/XBRL_INLINE_BUILD_SEAL_2026-11-21.md(XB0 ― 受理済みの有報の inline XBRL を、タグを剥がした本文と fact の表から自前の部品で組み直すと、公開の道具が読む fact と検査の鳴り方は元と同じになるか)の封の門。

**この門は置き場も道具も読まない**(書類の置き場 ``~/.cache/audit-core/edinet/``・道具の venv は 1 度も開かない。道具が無い機械でも緑)。通信しない。subprocess も呼ばない(道具の呼び出しは作り物の runner に差し替える)。
作り物の ``.htm``(入れ子・自己閉じ・xsi:nil・footnote・header・複数の文脈と単位・軸つきの文脈)で、剥がす・組む・比べる・混ぜ物・数え方・記録の検査を本物の関数のまま通す。

**この門が縛るもの**

1. 封の字: 封の commit(9c528c49)・封の file が commit した blob と同じ・版・sha256・掛け方・規則の年・67 本・開発の 5 本・600 秒・混ぜ物の種類・予測の境・限界の字が script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 剥がす(素の本文・表 F・表 H を手で決めた値と照らす)・組む(手で書いた字と一致・属性の並び/空白/引用符が違う元から同じ字が出る・表から組み直した表が同じ)・知らない形は断る・混ぜ物の当て先と変え方。
4. 組む部品は素の本文・表 F・表 H だけを引数に取り、元の字・包み・zip を読まない(関数の形と本体の名前を縛る)。
5. 比べ方(fact が同じ・鳴り方が同じ)・数え方(§2)・書類 1 本の通し(元の包みと組み直した包みを同じ掛け方で 1 回ずつ・.xbrl を除く・ほかの file は元のまま・混ぜ物 3 つ)を作り物の runner で通す。
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
    mod = types.ModuleType("xbrl_inline_build_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_INLINE_BUILD_SEAL_2026-11-21.md"
SEAL_COMMIT_SHORT = "9c528c49"
SCRIPT_REL = "measure/xbrl_inline_build_2026-11-21.py"
GATE_REL = "tests/measure/test_xbrl_inline_build_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/inline_build_2026-11-21.json"
MS = load_module(SCRIPT_REL, "xbrl_inline_build_script_for_seal_gate")
ORDER_FILES = (SCRIPT_REL, GATE_REL)
od = collections.OrderedDict
VALIDATE_NAME = "_xb0_edinet_validate_2026_11_21"


def load_helpers():
    u"""順の門(``order_problems``)の部品。木の中で通るときだけ読む。"""
    p = os.path.join(ROOT, "tests", "measure", "test_xbrl_p28_result.py")
    if not os.path.exists(p):
        return None
    return load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_inline_build_seal")


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
        self.d = tempfile.mkdtemp(prefix="xb0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


# ======================================================================== 作り物の .htm(手で書いた字)
HEAD = u'<html xmlns="x" xmlns:ix="y">\n<body>\n'
HDR = u"""<ix:header>
<ix:hidden>
<ix:nonNumeric name="jpdei_cor:EDINETCodeDEI" contextRef="FilingDateInstant">E99999</ix:nonNumeric>
<ix:nonNumeric name="jpdei_cor:FundCodeDEI" contextRef="FilingDateInstant" xsi:nil="true" />
<ix:nonFraction name="jpdei_cor:NumberOfSubmissionDEI" contextRef="FilingDateInstant" unitRef="pure" decimals="0" scale="0">1</ix:nonFraction>
</ix:hidden>
<ix:references>
<link:schemaRef xlink:type="simple" xlink:href="fake.xsd" />
</ix:references>
<ix:resources>
<link:roleRef roleURI="http://x/role/a" xlink:type="simple" xlink:href="http://x/a.xsd#rol_a" />
<xbrli:context id="C1">
<xbrli:entity>
<xbrli:identifier scheme="http://disclosure.edinet-fsa.go.jp">E99999-000</xbrli:identifier>
</xbrli:entity>
<xbrli:period>
<xbrli:startDate>2025-04-01</xbrli:startDate>
<xbrli:endDate>2026-03-31</xbrli:endDate>
</xbrli:period>
</xbrli:context>
<xbrli:context id="C2">
<xbrli:entity>
<xbrli:identifier scheme="http://disclosure.edinet-fsa.go.jp">E99999-000</xbrli:identifier>
</xbrli:entity>
<xbrli:period>
<xbrli:instant>2026-03-31</xbrli:instant>
</xbrli:period>
<xbrli:scenario>
<xbrldi:explicitMember dimension="jppfs_cor:ComponentsOfEquityAxis">jppfs_cor:ShareholdersEquityMember</xbrldi:explicitMember>
<xbrldi:explicitMember dimension="jppfs_cor:ConsolidatedOrNonConsolidatedAxis">jppfs_cor:NonConsolidatedMember</xbrldi:explicitMember>
</xbrli:scenario>
</xbrli:context>
<xbrli:unit id="JPY">
<xbrli:measure>iso4217:JPY</xbrli:measure>
</xbrli:unit>
<xbrli:unit id="JPYPerShares">
<xbrli:divide>
<xbrli:unitNumerator>
<xbrli:measure>iso4217:JPY</xbrli:measure>
</xbrli:unitNumerator>
<xbrli:unitDenominator>
<xbrli:measure>xbrli:shares</xbrli:measure>
</xbrli:unitDenominator>
</xbrli:divide>
</xbrli:unit>
</ix:resources>
</ix:header>"""
#: 組む部品が書く字そのもの(手で書いた)。ix:header を持つ file
HTM_A = (HEAD
         + u'<p>売上 <ix:nonFraction name="jppfs_cor:Sales" contextRef="C1" unitRef="JPY" decimals="-6" scale="6" format="ixt:numdotdecimal" sign="-">1,234</ix:nonFraction> と'
           u' <ix:nonNumeric name="jpcrp_cor:Title" contextRef="C1" escape="true">題<ix:nonNumeric name="jpcrp_cor:Inner" contextRef="C1">内</ix:nonNumeric>名</ix:nonNumeric></p>\n'
           u'<p><ix:nonFraction name="jppfs_cor:Nil" contextRef="C2" unitRef="JPY" xsi:nil="true" /></p>\n'
           u'<p><ix:nonNumeric name="jpcrp_cor:Empty" contextRef="C1"></ix:nonNumeric><ix:footnote footnoteID="f1" footnoteLinkRole="r" arcrole="a" footnoteRole="fr" xml:lang="ja">注<b>太</b></ix:footnote>'
           u'<ix:nonFraction name="jppfs_cor:Cost" contextRef="C2" unitRef="JPY" decimals="0" scale="0" format="ixt:numdotdecimal">0</ix:nonFraction></p>\n'
         + u'<div style="display:none">\n' + HDR + u'\n</div>\n</body>\n</html>\n')
#: ix:header を持たない file(属性の並び・引用符・空白が組む部品の決めと違う)
HTM_B = (u'<html xmlns="x" xmlns:ix="y">\n<body>\n'
         u"<p><ix:nonFraction  unitRef = 'JPY' contextRef='C1' name=\"jppfs_cor:Assets\" decimals='0' format='ixt:numdotdecimal' scale='0' >5</ix:nonFraction>\n"
         u'<ix:nonNumeric contextRef="C2" name="jpcrp_cor:Text" escape="false"/></p>\n</body>\n</html>\n')
HTM_B_CANON = (u'<html xmlns="x" xmlns:ix="y">\n<body>\n'
               u'<p><ix:nonFraction name="jppfs_cor:Assets" contextRef="C1" unitRef="JPY" decimals="0" scale="0" format="ixt:numdotdecimal">5</ix:nonFraction>\n'
               u'<ix:nonNumeric name="jpcrp_cor:Text" contextRef="C2" escape="false" /></p>\n</body>\n</html>\n')
PLAIN_A = (HEAD + u"<p>売上 1,234 と 題内名</p>\n<p></p>\n<p>注<b>太</b>0</p>\n" + u'<div style="display:none">\n' + u"\n</div>\n</body>\n</html>\n")
PLAIN_B = u'<html xmlns="x" xmlns:ix="y">\n<body>\n<p>5\n</p>\n</body>\n</html>\n'


def idx(s, sub):
    return s.index(sub)


#: 手で決めた表 F(HTM_A)。(kind, self, 始まる字・終わる字の素の本文の中の探し方, 親の番号, 属性)
HAND_F_A = [
    (u"nonFraction", False, (u"1,234", 0, 5), -1, {"name": "jppfs_cor:Sales", "contextRef": "C1", "unitRef": "JPY", "decimals": "-6", "scale": "6", "format": "ixt:numdotdecimal", "sign": "-"}),
    (u"nonNumeric", False, (u"題内名", 0, 3), -1, {"name": "jpcrp_cor:Title", "contextRef": "C1", "escape": "true"}),
    (u"nonNumeric", False, (u"内", 0, 1), 1, {"name": "jpcrp_cor:Inner", "contextRef": "C1"}),
    (u"nonFraction", True, (u"<p></p>", 3, 3), -1, {"name": "jppfs_cor:Nil", "contextRef": "C2", "unitRef": "JPY", "xsi:nil": "true"}),
    (u"nonNumeric", False, (u"<p>注<b>太</b>0</p>", 3, 3), -1, {"name": "jpcrp_cor:Empty", "contextRef": "C1"}),
    (u"footnote", False, (u"注<b>太</b>", 0, 9), -1, {"footnoteID": "f1", "footnoteLinkRole": "r", "arcrole": "a", "footnoteRole": "fr", "xml:lang": "ja"}),
    (u"nonFraction", False, (u"0</p>\n</p>", 0, 0), -1, {"name": "jppfs_cor:Cost", "contextRef": "C2", "unitRef": "JPY", "decimals": "0", "scale": "0", "format": "ixt:numdotdecimal"}),
]


def hand_f_a():
    u"""手で決めた (kind, self, start, end, parent, attrs)。位置は PLAIN_A の字から手で探す。"""
    p = PLAIN_A
    a = idx(p, u"1,234")
    t = idx(p, u"題内名")
    nil = idx(p, u"<p></p>") + 3
    emp = idx(p, u"<p>注") + 3
    fn = idx(p, u"注<b>太</b>")
    cost = idx(p, u"</b>0</p>") + 4
    return [
        (u"nonFraction", False, a, a + 5, -1, HAND_F_A[0][4]),
        (u"nonNumeric", False, t, t + 3, -1, HAND_F_A[1][4]),
        (u"nonNumeric", False, t + 1, t + 2, 1, HAND_F_A[2][4]),
        (u"nonFraction", True, nil, nil, -1, HAND_F_A[3][4]),
        (u"nonNumeric", False, emp, emp, -1, HAND_F_A[4][4]),
        (u"footnote", False, fn, fn + 9, -1, HAND_F_A[5][4]),
        (u"nonFraction", False, cost, cost + 1, -1, HAND_F_A[6][4])]


def hand_h_pos_a():
    return PLAIN_A.index(u'<div style="display:none">\n') + len(u'<div style="display:none">\n')


def f_tuple(e):
    return (e["kind"], e["self"], e["start"], e["end"], e["parent"], dict(e["attrs"]))


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XB0-1", (56, None)), ("XB0-2", (None, 4)), ("XB0-3", (56, None)), ("XB0-4", (50, None)), ("XB0-5", (None, 10)), ("XB0-6", (15, None)), ("XB0-7", (None, 5))])
SEAL_BOUND_TEXT = od([("XB0-1", u"56 本以上"), ("XB0-2", u"4 本以下"), ("XB0-3", u"56 本以上"), ("XB0-4", u"50% 以上"), ("XB0-5", u"10 本以下"), ("XB0-6", u"15 個"), ("XB0-7", u"5 個以下")])
SEAL_SHA_P = u"fd9b0d08bf283452fe4ebd6ec9de2f273010de0420b70e61c993a6c033814635"


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
    if ms.FACT_COLS != u"Name contextRef unitRef Dec Value EntityScheme EntityIdentifier Period Dimensions" or (u"--factListCols '%s'" % ms.FACT_COLS) not in seal or u"--facts <CSV の場所>" not in seal:
        out_.append(u"--facts・--factListCols が封と違う")
    if ms.TIMEOUT_SEC != 600 or u"1 回の時間の上限は 600 秒" not in seal:
        out_.append(u"時間の上限が封と違う")
    if ms.DOCS_WANT != 67 or u"便 XG0 と同じ 67 本" not in seal or u"書類は 67 本(違えば script は止まる)" not in seal:
        out_.append(u"67 が封と違う")
    if ms.DEV_COUNT != 5 or u"並びの頭の 5 本" not in seal:
        out_.append(u"開発の 5 本が封と違う")
    if ms.STRIP_SUFFIX != u".xbrl" or u"名が `.xbrl` で終わる file を除いた写し" not in seal:
        out_.append(u".xbrl を除く決めが封と違う")
    if tuple(ms.IX_KINDS) != (u"nonFraction", u"nonNumeric", u"footnote") or u"`ix:nonFraction`・`ix:nonNumeric`・`ix:footnote` の開きタグと閉じタグ" not in seal:
        out_.append(u"剥がす 3 種類が封と違う")
    if tuple(ms.MIX_KINDS) != (u"抜く", u"文脈を替える", u"符号を返す") or u"**抜く**" not in seal or u"**文脈を替える**" not in seal or u"**符号を返す**" not in seal or u"開発の 5 本 × 3 種類 = 15 個" not in seal:
        out_.append(u"混ぜ物の種類が封と違う")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out_.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [x for x in seal.splitlines() if x.startswith(u"| %s" % k)]
        if len(row_) != 1 or t not in row_[0]:
            out_.append(u"封の予測の行の字が違う: %s" % k)
    for rel in (SCRIPT_REL, RECORD_REL, u"tests/measure/test_xbrl_inline_build_seal.py"):
        if rel not in seal:
            out_.append(u"封に path が無い: %s" % rel)
    if u"docID・会社の名・EDINET コード・file の名・fact の値・要素の名・指摘の行の本文は書かない" not in seal:
        out_.append(u"封の記録の禁止の字が違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    want_phrases = (u"タグを決める力は測っていない", u"提出者別タクソノミ・マニフェスト・画像・AuditDoc は元のまま", u"原稿(Word など)ではない", u"道具 P。司令塔が 1 行を直したもの", u"無作為ではない。有報だけ", u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」")
    if any(p not in sec7 for p in want_phrases) or any(k not in u"".join(ms.LIMITS) for k in (u"タグを決める力は測っていない", u"元のまま", u"原稿(Word など)ではない", u"1 行を直したもの", u"無作為ではない。有報だけ", u"「EDINET の検査に通る」")):
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
    plain, F, H = ms.strip_text(HTM_A)
    if plain != PLAIN_A:
        out_.append(u"素の本文が手で決めた字と違う: %r" % plain[:80])
    if [f_tuple(e) for e in F] != hand_f_a():
        out_.append(u"表 F が手で決めた値と違う: %s" % [f_tuple(e) for e in F][:3])
    if H is None or H["pos"] != hand_h_pos_a() or H["before"] != len(HAND_F_A) or H["sections"] != [u"ix:hidden", u"ix:references", u"ix:resources"]:
        out_.append(u"表 H の位置・並びが違う")
    else:
        hid = H["hidden"]
        if [(h["kind"], h["self"], h["text"], h["attrs"].get("name")) for h in hid] != [
                (u"nonNumeric", False, u"E99999", u"jpdei_cor:EDINETCodeDEI"), (u"nonNumeric", True, u"", u"jpdei_cor:FundCodeDEI"), (u"nonFraction", False, u"1", u"jpdei_cor:NumberOfSubmissionDEI")]:
            out_.append(u"隠しの fact が違う")
        if hid[1]["attrs"].get("xsi:nil") != u"true" or hid[2]["attrs"].get("unitRef") != u"pure":
            out_.append(u"隠しの fact の属性が違う")
        if [(r["tag"], r["attrs"]["xlink:href"]) for r in H["references"]] != [(u"link:schemaRef", u"fake.xsd")]:
            out_.append(u"参照が違う")
        res = H["resources"]
        if [r["type"] for r in res] != [u"ref", u"context", u"context", u"unit", u"unit"]:
            out_.append(u"resources の並びが違う: %s" % [r["type"] for r in res])
        else:
            c1, c2, u1, u2 = res[1], res[2], res[3], res[4]
            if (c1["id"], c1["scheme"], c1["ident"], c1["period"], c1["members"], c1["has_scenario"]) != (u"C1", u"http://disclosure.edinet-fsa.go.jp", u"E99999-000", [(u"xbrli:startDate", u"2025-04-01"), (u"xbrli:endDate", u"2026-03-31")], [], False):
                out_.append(u"文脈 C1(期間)が違う")
            if (c2["id"], c2["period"], c2["members"], c2["has_scenario"]) != (u"C2", [(u"xbrli:instant", u"2026-03-31")], [(u"jppfs_cor:ComponentsOfEquityAxis", u"jppfs_cor:ShareholdersEquityMember"), (u"jppfs_cor:ConsolidatedOrNonConsolidatedAxis", u"jppfs_cor:NonConsolidatedMember")], True):
                out_.append(u"文脈 C2(時点・軸 2 つ)が違う")
            if (u1["id"], u1["measures"], u1["divide"]) != (u"JPY", [u"iso4217:JPY"], None) or (u2["id"], u2["measures"], u2["divide"]) != (u"JPYPerShares", [], {"num": [u"iso4217:JPY"], "den": [u"xbrli:shares"]}):
                out_.append(u"単位が違う(割り算の上下)")
            if res[0]["tag"] != u"link:roleRef" or res[0]["attrs"]["roleURI"] != u"http://x/role/a":
                out_.append(u"roleRef が違う")
        if u"ix:header" in json.dumps(H, ensure_ascii=False) and u"<ix:header" in json.dumps(H, ensure_ascii=False):
            out_.append(u"表 H に ix:header の元の字が在る")
    # 頭の部を持たない file
    p2, F2, H2 = ms.strip_text(HTM_B)
    if p2 != PLAIN_B or H2 is not None or [(e["kind"], e["self"], e["parent"], e["attrs"]) for e in F2] != [
            (u"nonFraction", False, -1, {"contextRef": "C1", "decimals": "0", "format": "ixt:numdotdecimal", "name": "jppfs_cor:Assets", "scale": "0", "unitRef": "JPY"}), (u"nonNumeric", True, -1, {"contextRef": "C2", "escape": "false", "name": "jpcrp_cor:Text"})]:
        out_.append(u"頭の部を持たない file の剥がしが手で決めた値と違う")
    # 表の属性は並びの順を持たない(辞書の並びが名の昇順)
    if any(list(e["attrs"]) != sorted(e["attrs"]) for e in F + F2):
        out_.append(u"表 F の属性が名の昇順でない(元の並びの順を持っている)")
    # 属性の値は元の字のまま(実体参照を直さない)
    ent_text = u'<p><ix:nonNumeric name="n" contextRef="C&amp;1">a&lt;b</ix:nonNumeric></p>'
    pe, Fe, _He = ms.strip_text(ent_text)
    if Fe[0]["attrs"]["contextRef"] != u"C&amp;1" or pe != u"<p>a&lt;b</p>" or ms.build_text(pe, Fe, None) != ent_text:
        out_.append(u"属性の値の実体参照を直している(元の字のままでない)")
    # 剥がしただけで元の字の他の部分は 1 字も変わらない: 素の本文にタグの字が残らない
    if re.search(r"</?ix:", plain) or re.search(r"</?ix:", p2):
        out_.append(u"素の本文に ix のタグが残っている")
    # 位置の根拠: 閉じタグの手前に注の中の <b> が素の本文に残る
    if u"<b>太</b>" not in plain:
        out_.append(u"タグの中身の字を変えた")
    return out_


# ======================================================================== 3. 組む
def hand_tables_a():
    u"""元の字を介さず、手で書いた表(組む部品が元の字を読んでいないことを見るため、表は strip の出力を使わない)。"""
    F = [od([("kind", k), ("self", s), ("start", st), ("end", en), ("parent", par), ("attrs", dict(at))]) for k, s, st, en, par, at in hand_f_a()]
    H = od([
        ("sections", [u"ix:hidden", u"ix:references", u"ix:resources"]), ("pos", hand_h_pos_a()), ("before", len(F)),
        ("hidden", [od([("kind", u"nonNumeric"), ("self", False), ("attrs", {"name": "jpdei_cor:EDINETCodeDEI", "contextRef": "FilingDateInstant"}), ("text", u"E99999")]),
                    od([("kind", u"nonNumeric"), ("self", True), ("attrs", {"name": "jpdei_cor:FundCodeDEI", "contextRef": "FilingDateInstant", "xsi:nil": "true"}), ("text", u"")]),
                    od([("kind", u"nonFraction"), ("self", False), ("attrs", {"name": "jpdei_cor:NumberOfSubmissionDEI", "contextRef": "FilingDateInstant", "unitRef": "pure", "decimals": "0", "scale": "0"}), ("text", u"1")])]),
        ("references", [od([("tag", u"link:schemaRef"), ("self", True), ("attrs", {"xlink:type": "simple", "xlink:href": "fake.xsd"})])]),
        ("resources", [
            od([("type", u"ref"), ("tag", u"link:roleRef"), ("self", True), ("attrs", {"roleURI": "http://x/role/a", "xlink:type": "simple", "xlink:href": "http://x/a.xsd#rol_a"})]),
            od([("type", u"context"), ("id", u"C1"), ("scheme", u"http://disclosure.edinet-fsa.go.jp"), ("ident", u"E99999-000"), ("period", [(u"xbrli:startDate", u"2025-04-01"), (u"xbrli:endDate", u"2026-03-31")]), ("members", []), ("has_scenario", False)]),
            od([("type", u"context"), ("id", u"C2"), ("scheme", u"http://disclosure.edinet-fsa.go.jp"), ("ident", u"E99999-000"), ("period", [(u"xbrli:instant", u"2026-03-31")]),
                ("members", [(u"jppfs_cor:ComponentsOfEquityAxis", u"jppfs_cor:ShareholdersEquityMember"), (u"jppfs_cor:ConsolidatedOrNonConsolidatedAxis", u"jppfs_cor:NonConsolidatedMember")]), ("has_scenario", True)]),
            od([("type", u"unit"), ("id", u"JPY"), ("measures", [u"iso4217:JPY"]), ("divide", None)]),
            od([("type", u"unit"), ("id", u"JPYPerShares"), ("measures", []), ("divide", od([("num", [u"iso4217:JPY"]), ("den", [u"xbrli:shares"])]))])])])
    return PLAIN_A, F, H


def build_problems(ms=None):
    ms = ms or MS
    out_ = []
    plain, F, H = hand_tables_a()
    got = ms.build_text(plain, F, H)
    if got != HTM_A:
        i = next((k for k in range(min(len(got), len(HTM_A))) if got[k] != HTM_A[k]), min(len(got), len(HTM_A)))
        out_.append(u"手で書いた表から組んだ字が手で書いた字と違う(最初の違い: %r / %r)" % (got[max(0, i - 30):i + 50], HTM_A[max(0, i - 30):i + 50]))
    # 往復: 組んだ字を剥がし直すと同じ表(位置・親・属性・頭の部の構造)
    p1, F1, H1 = ms.strip_text(HTM_A)
    if ms.build_text(p1, F1, H1) != HTM_A:
        out_.append(u"剥がして組むと元の字に戻らない(組む部品の決めの形の file)")
    p2, F2, H2 = ms.strip_text(got)
    if (p2, [f_tuple(e) for e in F2], json.dumps(H2, sort_keys=True)) != (p1, [f_tuple(e) for e in F1], json.dumps(H1, sort_keys=True)):
        out_.append(u"組んだ字を剥がし直した表が違う")
    # 元の字の並び・空白・引用符の違いは持たない: 組む部品の決めの字が出る
    pb, Fb, Hb = ms.strip_text(HTM_B)
    if ms.build_text(pb, Fb, Hb) != HTM_B_CANON:
        out_.append(u"属性の並び・空白・引用符が違う元から、組む部品の決めの字が出ない: %r" % ms.build_text(pb, Fb, Hb)[:200])
    # 値に " が在れば ' で囲む・両方在れば断る
    for attrs, want in (({"name": 'a"b'}, u"<ix:nonNumeric name='a\"b'>"), ({"name": "a'b"}, u'<ix:nonNumeric name="a\'b">')):
        if ms.open_tag("ix:nonNumeric", attrs, ms.ATTR_ORDER["nonNumeric"], False) != want:
            out_.append(u"引用符の決めが違う: %s" % attrs)
    if not declines(ms, ms.open_tag, "ix:nonNumeric", {"name": "a'\"b"}, ms.ATTR_ORDER["nonNumeric"], False):
        out_.append(u"値に引用符が両方在るのに断らない")
    # 頭の部の位置: 同じ位置に頭の部と表 F の行が在るときの順(before)
    plain3 = u"AB"
    F3 = [od([("kind", u"nonNumeric"), ("self", False), ("start", 1), ("end", 1), ("parent", -1), ("attrs", {"name": "n1"})]),
          od([("kind", u"nonNumeric"), ("self", False), ("start", 1), ("end", 1), ("parent", -1), ("attrs", {"name": "n2"})])]
    H3 = od([("sections", []), ("pos", 1), ("before", 1), ("hidden", []), ("references", []), ("resources", []), ])
    t3 = ms.build_text(plain3, F3, H3)
    if t3 != u'A<ix:nonNumeric name="n1"></ix:nonNumeric><ix:header>\n</ix:header><ix:nonNumeric name="n2"></ix:nonNumeric>B':
        out_.append(u"頭の部の位置(before)の扱いが違う: %r" % t3)
    # 同じ位置の入れ子: 自己閉じの子と親が同じ位置で終わる
    F4 = [od([("kind", u"nonNumeric"), ("self", False), ("start", 1), ("end", 2), ("parent", -1), ("attrs", {"name": "p"})]),
          od([("kind", u"nonNumeric"), ("self", True), ("start", 2), ("end", 2), ("parent", 0), ("attrs", {"name": "c"})]),
          od([("kind", u"nonNumeric"), ("self", True), ("start", 2), ("end", 2), ("parent", -1), ("attrs", {"name": "d"})])]
    t4 = ms.build_text(u"XYZ", F4, None)
    if t4 != u'X<ix:nonNumeric name="p">Y<ix:nonNumeric name="c" /></ix:nonNumeric><ix:nonNumeric name="d" />Z':
        out_.append(u"同じ位置の子と兄弟の順が違う: %r" % t4)
    return out_


def decline_problems(ms=None):
    ms = ms or MS
    out_ = []
    base = HTM_A
    cases = [
        (u"知らない ix の要素", base.replace(u"<p>売上", u"<ix:continuation id='x'/><p>売上")),
        (u"知らない属性", base.replace(u'contextRef="C1" unitRef="JPY" decimals="-6"', u'contextRef="C1" unitRef="JPY" order="9" decimals="-6"')),
        (u"footnote の知らない属性", base.replace(u'xml:lang="ja"', u'xml:lang="ja" zzz="1"')),
        (u"属性の名が重なる", base.replace(u'contextRef="C1" unitRef="JPY" decimals="-6"', u'contextRef="C1" contextRef="C2" unitRef="JPY" decimals="-6"')),
        (u"閉じタグが合わない", base.replace(u"</ix:nonNumeric>名", u"</ix:nonFraction>名")),
        (u"閉じていない", base.replace(u"</ix:footnote>", u"")),
        (u"2 つ目の頭の部", base.replace(u"</body>", HDR + u"</body>")),
        (u"自己閉じの頭の部", base.replace(HDR, u"<ix:header />")),
        (u"入れ子の頭の部", base.replace(u"<ix:hidden>", u"<ix:hidden><ix:header>")),
        (u"頭の部の知らない子", base.replace(u"<ix:references>", u"<ix:tuple></ix:tuple><ix:references>")),
        (u"頭の部の子に属性", base.replace(u"<ix:hidden>", u'<ix:hidden id="x">')),
        (u"知らない文脈の子", base.replace(u"</xbrli:entity>\n<xbrli:period>\n<xbrli:instant>", u"</xbrli:entity>\n<xbrli:segment></xbrli:segment>\n<xbrli:period>\n<xbrli:instant>")),
        (u"知らないメンバー", base.replace(u"<xbrldi:explicitMember dimension=\"jppfs_cor:ComponentsOfEquityAxis\">jppfs_cor:ShareholdersEquityMember</xbrldi:explicitMember>", u"<xbrldi:typedMember dimension=\"a\">x</xbrldi:typedMember>")),
        (u"頭の部の中の知らない字(コメント)", base.replace(u"<ix:hidden>", u"<ix:hidden><!-- x -->")),
        (u"隠しの fact が入れ子", base.replace(u">E99999</ix:nonNumeric>", u"><ix:nonNumeric name='q'>E99999</ix:nonNumeric></ix:nonNumeric>")),
        (u"頭の部の閉じタグが合わない", base.replace(u"</ix:hidden>", u"</ix:references>")),
        (u"ix のタグの字が知らない形(属性の引用が欠ける)", base.replace(u'name="jppfs_cor:Sales"', u"name=jppfs_cor:Sales")),
        (u"ix のタグの字が知らない形(自己閉じで引用が欠ける。閉じタグは対に無い)", base.replace(u'<ix:nonNumeric name="jpcrp_cor:Empty" contextRef="C1"></ix:nonNumeric>', u"<ix:nonNumeric name=jpcrp_cor:Empty />")),
        (u"最後の閉じタグが無い(頭の部の前ではない)", HTM_B.replace(u"</ix:nonFraction>", u"")),
        (u"頭の部の葉の字に知らない形(コメント)", base.replace(u"<xbrli:measure>iso4217:JPY</xbrli:measure>", u"<xbrli:measure>iso4217:JPY<!-- c --></xbrli:measure>", 1)),
    ]
    for what, text in cases:
        if text == base:
            out_.append(u"断る例の字が元と同じ(作り損ね): %s" % what)
            continue
        if not declines(ms, ms.strip_text, text):
            out_.append(u"剥がす部品が断らない: %s" % what)
    # 組む部品が知らない形に当たったとき断る
    plain, F, H = hand_tables_a()
    bad_kind = copy.deepcopy(F)
    bad_kind[0]["kind"] = u"continuation"
    if not declines(ms, ms.build_text, plain, bad_kind, H):
        out_.append(u"組む部品が知らない ix の要素で断らない")
    bad_attr = copy.deepcopy(F)
    bad_attr[0]["attrs"]["zzz"] = u"1"
    if not declines(ms, ms.build_text, plain, bad_attr, H):
        out_.append(u"組む部品が知らない属性で断らない")
    bad_h = copy.deepcopy(H)
    bad_h["sections"].append(u"ix:tuple")
    if not declines(ms, ms.build_text, plain, F, bad_h):
        out_.append(u"組む部品が頭の部の知らない子で断らない")
    bad_h2 = copy.deepcopy(H)
    bad_h2["resources"].append(od([("type", u"typed")]))
    if not declines(ms, ms.build_text, plain, F, bad_h2):
        out_.append(u"組む部品が resources の知らない子で断らない")
    bad_pos = copy.deepcopy(F)
    bad_pos[0]["start"] = bad_pos[0]["end"] + 3
    if not declines(ms, ms.build_text, plain, bad_pos, H):
        out_.append(u"位置が合わないのに断らない")
    bad_parent = copy.deepcopy(F)
    bad_parent[1]["parent"] = 1
    if not declines(ms, ms.build_text, plain, bad_parent, H):
        out_.append(u"親の番号が合わないのに断らない")
    # 書類ごとの例外も断ったに数える(process_doc の中の分は書類の通しの検査)
    return out_


# ======================================================================== 4. 混ぜ物
def files_of(*texts):
    out = []
    for i, t in enumerate(texts):
        p, F, H = MS.strip_text(t)
        out.append(("f%d" % i, p, F, H))
    return out


def mix_problems(ms=None):
    ms = ms or MS
    out_ = []
    files = []
    for nm, t in ((u"f1", HTM_B), (u"f0", HTM_A)):                     # 並びは名の昇順(f0 が先)に直して渡す: 当て先の決めは呼ぶ側の並びの順
        p, F, H = ms.strip_text(t)
        files.append((nm, p, F, H))
    files.sort(key=lambda x: x[0])
    # 抜く: 先頭の file(f0 = HTM_A)の最初の xsi:nil の無い nonFraction = Sales(表 F の 0 番)
    tgt = ms.mix_target(files, u"抜く")
    if tgt != (0, 0):
        out_.append(u"抜くの当て先が違う: %s" % (tgt,))
    r = ms.mix_tables(files, u"抜く")
    if r is None or r[0] != 0 or len(r[1]) != len(files[0][2]) - 1 or r[1][0]["attrs"]["name"] != "jpcrp_cor:Title":
        out_.append(u"抜くの結果が違う")
    elif [e["parent"] for e in r[1]] != [-1, 0, -1, -1, -1, -1] or r[2]["before"] != files[0][3]["before"] - 1:
        out_.append(u"抜いた後の親の番号・頭の部の位置の直しが違う: %s %s" % ([e["parent"] for e in r[1]], r[2]["before"]))
    else:
        built = ms.build_text(files[0][1], r[1], r[2])
        if u'name="jppfs_cor:Sales"' in built or u"1,234" not in built or built.count(u"<ix:nonFraction") != 3:
            out_.append(u"抜いた字が違う(Sales だけ消えて中身の字は残る): %d" % built.count(u"<ix:nonFraction"))
    # xsi:nil だけが先頭に在るときは次を当てる
    tgt = ms.mix_target(files[:1], u"抜く")
    if tgt != (0, 0):
        out_.append(u"xsi:nil の無い最初の行でない")
    nil_first = [(u"x", PLAIN_A, [e for e in files[0][2] if "xsi:nil" in e["attrs"]] + [e for e in files[0][2] if e["kind"] == "nonFraction" and "xsi:nil" not in e["attrs"]], None)]
    if ms.mix_target(nil_first, u"抜く") != (0, 1):
        out_.append(u"抜くが xsi:nil の行を飛ばさない")
    # 文脈を替える: Sales(C1)の contextRef を、pool の中で C1 と違う最初の値(Cost の C2)にする
    r = ms.mix_tables(files, u"文脈を替える")
    if r is None or r[1][0]["attrs"]["contextRef"] != u"C2" or r[1][0]["attrs"]["name"] != "jppfs_cor:Sales" or any(a["attrs"] != b["attrs"] for a, b in zip(r[1][1:], files[0][2][1:])):
        out_.append(u"文脈を替えるの結果が違う")
    if files[0][2][0]["attrs"]["contextRef"] != u"C1":
        out_.append(u"文脈を替えるが元の表を書き換えた")
    only_c1 = [(u"x", u"AB", [od([("kind", u"nonFraction"), ("self", False), ("start", 0), ("end", 1), ("parent", -1), ("attrs", {"name": "a", "contextRef": "C1"})]),
                              od([("kind", u"nonFraction"), ("self", False), ("start", 1), ("end", 2), ("parent", -1), ("attrs", {"name": "b", "contextRef": "C1"})])], None)]
    if ms.mix_tables(only_c1, u"文脈を替える") is not None:
        out_.append(u"別の contextRef が無いのに作った")
    # 符号を返す: sign が在れば除く
    r = ms.mix_tables(files, u"符号を返す")
    if r is None or "sign" in r[1][0]["attrs"] or r[1][0]["attrs"]["name"] != "jppfs_cor:Sales" or "sign" not in files[0][2][0]["attrs"]:
        out_.append(u"符号を返す(sign を除く)が違う")
    # sign が無ければ足す
    nosign = [(u"x", u"AB", [od([("kind", u"nonFraction"), ("self", False), ("start", 0), ("end", 1), ("parent", -1), ("attrs", {"name": "a", "contextRef": "C1"})])], None)]
    r = ms.mix_tables(nosign, u"符号を返す")
    if r is None or r[1][0]["attrs"].get("sign") != u"-" or "sign" in nosign[0][2][0]["attrs"]:
        out_.append(u"符号を返す(sign を足す)が違う")
    # 中身が 0 だけなら順で次の fact に当てる(全角の 0 も)
    zero = [(u"x", u"0０x7", [od([("kind", u"nonFraction"), ("self", False), ("start", 0), ("end", 1), ("parent", -1), ("attrs", {"name": "a", "contextRef": "C1"})]),
                              od([("kind", u"nonFraction"), ("self", False), ("start", 1), ("end", 2), ("parent", -1), ("attrs", {"name": "b", "contextRef": "C1"})]),
                              od([("kind", u"nonFraction"), ("self", False), ("start", 3), ("end", 4), ("parent", -1), ("attrs", {"name": "c", "contextRef": "C1"})])], None)]
    r = ms.mix_tables(zero, u"符号を返す")
    if r is None or "sign" not in r[1][2]["attrs"] or "sign" in r[1][0]["attrs"] or "sign" in r[1][1]["attrs"]:
        out_.append(u"中身が 0 だけの fact を飛ばして次に当てない")
    if not ms.is_zero_content(u" 0 ") or not ms.is_zero_content(u"００") or ms.is_zero_content(u"0.5") or ms.is_zero_content(u"  ") or ms.is_zero_content(u"10"):
        out_.append(u"中身が 0 だけの判定が違う")
    # 子の在る行を抜くときは断る(作れない)
    nested = [(u"x", u"AB", [od([("kind", u"nonFraction"), ("self", False), ("start", 0), ("end", 2), ("parent", -1), ("attrs", {"name": "a", "contextRef": "C1"})]),
                             od([("kind", u"nonNumeric"), ("self", False), ("start", 0), ("end", 1), ("parent", 0), ("attrs", {"name": "b", "contextRef": "C1"})])], None)]
    if not declines(ms, ms.mix_tables, nested, u"抜く"):
        out_.append(u"子の在る行を抜くのに断らない")
    # 当て先が無い file 群
    if ms.mix_tables([(u"x", u"A", [], None)], u"抜く") is not None:
        out_.append(u"fact が無いのに混ぜ物を作った")
    return out_


# ======================================================================== 5. 比べる・数える
def compare_problems(ms=None):
    ms = ms or MS
    out_ = []
    csv.field_size_limit(131072)                  # csv の上限は process で共有。直す前の値に戻してから、読む部品が直すかを見る
    with Temp() as d:
        p = os.path.join(d, "a.csv")
        with io.open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(u'Name,contextRef,Value\r\nb,C1,"x,y"\r\na,C2,"長い\r\n行"\r\n')
        rows = ms.read_rows(p)
        if rows != [(u"a", u"C2", u"長い\r\n行"), (u"b", u"C1", u"x,y")]:
            out_.append(u"CSV の読み(見出しを除く・並べ替え・引用つきの欄)が違う: %s" % rows)
        if ms.read_rows(os.path.join(d, "none.csv")) != []:
            out_.append(u"CSV が無いとき [] でない")
        with io.open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(u"Name,Value\r\n" + u"a," + u"z" * 200000 + u"\r\n")
        if len(ms.read_rows(p)[0][1]) != 200000:
            out_.append(u"長い欄を読めない(csv の欄の大きさの上限)")
    if not ms.facts_same([(u"a",)], [(u"a",)]) or ms.facts_same([], []) or ms.facts_same([(u"a",)], []) or ms.facts_same([], [(u"a",)]) or ms.facts_same([(u"a",)], [(u"b",)]) or ms.facts_same([(u"a",), (u"b",)], [(u"a",)]):
        out_.append(u"fact が同じの判定が違う(行が 0 なら同じとしない)")
    a = od([(u"類", u"走った"), (u"符号ごとの行", {u"EDINET.EC5611W": 2})])
    same = od([(u"類", u"走った"), (u"符号ごとの行", od([(u"EDINET.EC5611W", 2)]))])
    cases = [(same, True), (od([(u"類", u"止まった"), (u"符号ごとの行", {u"EDINET.EC5611W": 2})]), False), (od([(u"類", u"走った"), (u"符号ごとの行", {u"EDINET.EC5611W": 3})]), False),
             (od([(u"類", u"走った"), (u"符号ごとの行", {})]), False), (od([(u"類", u"走った"), (u"符号ごとの行", {u"EDINET.EC5611W": 2, u"EDINET.EC0121E": 1})]), False),
             (od([(u"類", u"走った"), (u"符号ごとの行", {u"EDINET.EC0121E": 2})]), False)]
    for b, want in cases:
        if ms.sounds_same(a, b) != want:
            out_.append(u"鳴り方が同じの判定が違う: %s" % dict(b))
    return out_


# ---- 作り物の道具(runner)
ACT = u"Activation of plug-in Validate EDINET successful"
FMT = u"Identified filing format"
FREEZE = u"foo==1.0\narelle-release==2.47.5\n"
PYVER = u"Python 3.11.17\n"
MV_P = b"model value P content"
FACT_TAG_RE = re.compile(r"<ix:(nonFraction|nonNumeric)\b([^>]*?)(/?)>(.*?)(?=</ix:\1>|\Z)", re.S)


def fake_facts(htm_texts):
    u"""作り物の道具が読む fact: 全部の ``.htm`` の ``nonFraction``/``nonNumeric`` の (name, contextRef, sign, 中身)。属性の並びによらず読む。"""
    rows = []
    for t in htm_texts:
        for m in re.finditer(r"<ix:(nonFraction|nonNumeric)\b((?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>", t):
            attrs = dict((a.group(1), a.group(2) if a.group(2) is not None else a.group(3)) for a in re.finditer(r"""([\w:]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""", m.group(2)))
            content = u""
            if not m.group(3):
                tail = t[m.end():]
                content = re.sub(r"<[^>]*>", u"", tail.split(u"</ix:%s>" % m.group(1), 1)[0])
            rows.append((attrs.get("name", u""), attrs.get("contextRef", u""), attrs.get("sign", u""), content))
    return rows


class FakeRunner(object):
    u"""道具の呼び出しの作り物。呼ばれた順・zip の中身・csv の場所を覚える。fact は zip の ``.htm`` から読み、``sign`` が ``-`` の fact の数だけ ``EC5611W`` の行を出す。"""

    def __init__(self, mv_path, freeze=FREEZE, pyver=PYVER, crash_on=None, out_extra=None):
        self.mv_path, self.freeze, self.pyver = mv_path, freeze, pyver
        self.calls = []
        self.crash_on = crash_on
        self.out_extra = out_extra or {}

    def __call__(self, cmd, timeout):
        cmd = list(cmd)
        if os.path.basename(cmd[0]) == "arelleCmdLine":
            zp = cmd[cmd.index("-f") + 1]
            csv_path = cmd[cmd.index("--facts") + 1]
            with zipfile.ZipFile(zp) as z:
                names = z.namelist()
                htms = [z.read(n).decode("utf-8") for n in names if n.endswith(".htm")]
                blobs = dict((n, z.read(n)) for n in names)
            self.calls.append(dict(cmd=cmd, timeout=timeout, names=names, blobs=blobs, zip=zp, csv=csv_path, existed=os.path.exists(zp)))
            if self.crash_on is not None and len(self.calls) == self.crash_on:
                raise RuntimeError("boom")
            rows = fake_facts(htms)
            with io.open(csv_path, "w", encoding="utf-8", newline="") as fh:
                fh.write(u"Name,contextRef,Sign,Value\r\n")
                for r in rows:
                    fh.write(u",".join(r) + u"\r\n")
            lines = [u"[info] " + ACT, u"[info] " + FMT + u": EDINET"] + [u"[EDINET.EC5611W] 本文の字 %d" % i for i in range(sum(1 for r in rows if r[2] == u"-"))]
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


HTM_NAME_A = "XBRL/PublicDoc/0101010_honbun_E99991-000_ixbrl.htm"
HTM_NAME_B = "XBRL/PublicDoc/0102010_honbun_E99991-000_ixbrl.htm"
XSD_NAME = "XBRL/PublicDoc/jpcrp030000-asr-001_E99991-000_2026-03-31_01_2026-06-30.xsd"


def make_doc_zip(path, no=1, with_continuation=False, order_reversed=False):
    u"""作り物の書類。PublicDoc に ``.htm`` 2 つ(A は頭の部を持つ・組む決めの字、B は持たない・決めと違う字)・.xsd・.xbrl(API が足した file)・AuditDoc。"""
    a = HTM_A.replace(u"E99999", u"E9999%d" % no)
    b = HTM_B
    if with_continuation:
        b = b.replace(u"<p>", u"<p><ix:continuation id='c1'/>")
    names = [(HTM_NAME_A.replace("E99991", "E9999%d" % no), a), (HTM_NAME_B.replace("E99991", "E9999%d" % no), b)]
    if order_reversed:
        names.reverse()
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(XSD_NAME.replace("E99991", "E9999%d" % no), b"<schema/>")
        for n, t in names:
            z.writestr(n, t.encode("utf-8"))
        z.writestr("XBRL/PublicDoc/manifest_PublicDoc.xml", b"<manifest/>")
        z.writestr("XBRL/PublicDoc/api_added_E9999%d-000.xbrl" % no, b"<xbrl/>")
        z.writestr("XBRL/AuditDoc/audit.xml", b"<a/>")


def make_docs(d, count=3, declined=(), reversed_=()):
    for i in range(count):
        make_doc_zip(os.path.join(d, "S2FAKE0%d.zip" % (i + 1)), i + 1, with_continuation=(i + 1) in declined, order_reversed=(i + 1) in reversed_)
    other = os.path.join(d, "S2OTHER1.zip")
    with zipfile.ZipFile(other, "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


STEMS = ["S2FAKE01", "S2FAKE02", "S2FAKE03"]
ORDER_SHA = hashlib.sha256(u"\n".join(STEMS).encode("utf-8")).hexdigest()
HAND_FACT_ROWS_A = 9                     # HTM_A の nonFraction・nonNumeric の開きタグ: 本文 6(Sales・Title・Inner・Nil・Empty・Cost) + 頭の部 3 = 9
HAND_FACT_ROWS_B = 2
HAND_ROWS_ALL = HAND_FACT_ROWS_A + HAND_FACT_ROWS_B


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
        before = read_bytes_sha(os.path.join(docs, "S2FAKE01.zip"))
        r = FakeRunner(mv)
        rec, elems = ms.process_doc(tool, os.path.join(docs, "S2FAKE01.zip"), tmp, r, mixtures=True)
        # 呼び出し: 元・組み直し・混ぜ物 3 つ = 5 回。同じ掛け方(zip と csv の場所だけが違う)・上限 600
        if len(r.calls) != 5:
            out_.append(u"道具の呼び出しが 5 回でない: %d" % len(r.calls))
        else:
            norm = [[x for x in c["cmd"][1:] if x not in (c["zip"], c["csv"])] for c in r.calls]
            if any(n != norm[0] for n in norm) or any(c["timeout"] != 600 for c in r.calls) or any(not c["existed"] for c in r.calls):
                out_.append(u"掛け方が 5 回で同じでない・時間の上限・zip が無い")
            c0 = r.calls[0]["cmd"]
            if c0[1:9] != [u"--plugins", u"validate/EDINET|inlineXbrlDocumentSet", u"--disclosureSystem", u"EDINET-2026", u"-f", r.calls[0]["zip"], u"--validate", u"--facts"] or c0[-2:] != [u"--factListCols", ms.FACT_COLS] or c0[0] != os.path.join(tool, "bin", "arelleCmdLine"):
                out_.append(u"掛け方の引数の並びが封と違う: %s" % c0)
            if len(set(c["zip"] for c in r.calls)) != 5 or len(set(c["csv"] for c in r.calls)) != 5 or len(set(os.path.dirname(c["zip"]) for c in r.calls)) != 1:
                out_.append(u"zip か csv の場所を使い回している")
            for c in r.calls:
                if any(n.endswith(".xbrl") for n in c["names"]) or u"XBRL/AuditDoc/audit.xml" not in c["names"] or c["blobs"]["XBRL/AuditDoc/audit.xml"] != b"<a/>" or c["blobs"][XSD_NAME.replace("E99991", "E99991")] != b"<schema/>" or c["blobs"]["XBRL/PublicDoc/manifest_PublicDoc.xml"] != b"<manifest/>":
                    out_.append(u"掛けた包みの中身が違う(.xbrl が残る・ほかの file が変わった)")
                    break
            # 元の包みは元の .htm の字・組み直した包みは組んだ字(A は同じ・B は決めの字)
            o, n = r.calls[0]["blobs"], r.calls[1]["blobs"]
            if o[HTM_NAME_A].decode("utf-8") != HTM_A.replace(u"E99999", u"E99991") or o[HTM_NAME_B].decode("utf-8") != HTM_B:
                out_.append(u"元の包みの .htm が元の字でない")
            if n[HTM_NAME_A] != o[HTM_NAME_A] or n[HTM_NAME_B].decode("utf-8") != HTM_B_CANON:
                out_.append(u"組み直した包みの .htm が組んだ字でない(比べる相手が同じ file になっている)")
            if len(set(hashlib.sha256(c["blobs"][HTM_NAME_B]).hexdigest() for c in r.calls[:2])) != 2:
                out_.append(u"元の包みと組み直した包みの B が同じ字(比べ方が効かない)")
        if rec[u"断った"] or rec[u"断った理由"] != u"":
            out_.append(u"断らない書類を断った: %s" % rec[u"断った理由"])
        if rec[u"元の fact の行の数"] != HAND_ROWS_ALL or rec[u"組み直しの fact の行の数"] != HAND_ROWS_ALL:
            out_.append(u"fact の行の数が違う(手で数えた値は %d): %s %s" % (HAND_ROWS_ALL, rec[u"元の fact の行の数"], rec[u"組み直しの fact の行の数"]))
        if not rec[u"fact が同じ"] or not rec[u"鳴り方が同じ"]:
            out_.append(u"組み直しで fact・鳴り方が同じにならない")
        if dict(rec[u"タグの数"]) != HAND_TAGS:
            out_.append(u"タグの数が手で数えた値と違う: %s" % dict(rec[u"タグの数"]))
        fl = rec[u"字の file"]
        if (fl[u"持つ"][u"数"], fl[u"持つ"][u"字が同じ"], fl[u"持たない"][u"数"], fl[u"持たない"][u"字が同じ"]) != (1, 1, 1, 0):
            out_.append(u"字の file の数が違う: %s" % json.dumps(fl))
        if rec[u"元の 1 回"][u"符号ごとの行"] != {u"EDINET.EC5611W": 1} or rec[u"元の 1 回"][u"類"] != u"走った":
            out_.append(u"元の 1 回の数が違う")
        # 混ぜ物 3 つ(手で決めた値): 抜く = Sales(sign="-")を除く → 行 1 つ減り・EC5611W 1 → 0。文脈 = C1 → C2 で行が変わる(鳴り方は同じ)。符号 = Sales の sign を除く → EC5611W 1 → 0
        got = [(m[u"種類"], m[u"作った"], m[u"fact が同じ"], m[u"鳴り方が同じ"]) for m in rec[u"混ぜ物"]]
        if got != [(u"抜く", True, False, False), (u"文脈を替える", True, False, True), (u"符号を返す", True, False, False)]:
            out_.append(u"混ぜ物 3 つの結果が手で決めた値と違う: %s" % got)
        mrows = [x for x in r.calls[2:]]
        sg = [fake_facts([z.decode("utf-8") for n, z in c["blobs"].items() if n.endswith(".htm")]) for c in mrows]
        if len(sg[0]) != HAND_ROWS_ALL - 1 or [x for x in sg[1] if x[0] == "jppfs_cor:Sales"][0][1] != "C2" or [x for x in sg[2] if x[0] == "jppfs_cor:Sales"][0][2] != "":
            out_.append(u"混ぜ物の包みの中身が手で決めた変え方と違う")
        if elems != {"Sales", "Title", "Inner", "Nil", "Empty", "Cost", "Assets", "Text", "EDINETCodeDEI", "FundCodeDEI", "NumberOfSubmissionDEI"}:
            out_.append(u"secret の要素の名の集まりが違う: %s" % sorted(elems))
        if read_bytes_sha(os.path.join(docs, "S2FAKE01.zip")) != before:
            out_.append(u"置き場の zip が変わった")
        if os.listdir(tmp):
            out_.append(u"使い捨ての場所が残っている")
        # 既定の runner は V.exec_cmd(作り物に差し替えて、呼ばれることを見る)
        fake_default = FakeRunner(mv)
        saved = ms.V.exec_cmd
        ms.V.exec_cmd = fake_default
        try:
            ms.process_doc(tool, os.path.join(docs, "S2FAKE01.zip"), tmp, None, mixtures=False)
            ms.check_tool(tool, None, want_sha=hashlib.sha256(MV_P).hexdigest())
        finally:
            ms.V.exec_cmd = saved
        if len(fake_default.calls) != 2:
            out_.append(u"既定の runner が V.exec_cmd でない(道具を自分で呼んでいる): %d" % len(fake_default.calls))
        # 混ぜ物を作らない呼び方
        r2 = FakeRunner(mv)
        rec2, _e = ms.process_doc(tool, os.path.join(docs, "S2FAKE01.zip"), tmp, r2, mixtures=False)
        if len(r2.calls) != 2 or rec2[u"混ぜ物"] != []:
            out_.append(u"混ぜ物を作らない呼び方で 2 回でない")
        # file の並びは名の昇順(zip の並びでない): B を先に書いた zip でも抜くの当て先は A の Sales
        make_doc_zip(os.path.join(docs, "S2REV.zip"), 1, order_reversed=True)
        r3 = FakeRunner(mv)
        rec3, _e = ms.process_doc(tool, os.path.join(docs, "S2REV.zip"), tmp, r3, mixtures=True)
        sg3 = fake_facts([z.decode("utf-8") for n, z in r3.calls[2]["blobs"].items() if n.endswith(".htm")])
        if len(sg3) != HAND_ROWS_ALL - 1 or [x for x in sg3 if x[0] == "jppfs_cor:Sales"]:
            out_.append(u"抜くの当て先が名の昇順の先頭の file でない(zip の並びの順になっている)")
        if os.listdir(tmp):
            out_.append(u"使い捨ての場所が残っている(2)")
        # 断る書類: 知らない形 → 断った・fact も鳴り方も同じとしない・字は同じでない・混ぜ物は作らない・理由は固定の字
        make_doc_zip(os.path.join(docs, "S2DEC.zip"), 1, with_continuation=True)
        r4 = FakeRunner(mv)
        rec4, _e = ms.process_doc(tool, os.path.join(docs, "S2DEC.zip"), tmp, r4, mixtures=True)
        if not rec4[u"断った"] or rec4[u"断った理由"] != u"知らない ix の要素" or rec4[u"組み直しの 1 回"] is not None or rec4[u"fact が同じ"] or rec4[u"鳴り方が同じ"]:
            out_.append(u"知らない形の書類を断らない: %s" % rec4[u"断った理由"])
        if len(r4.calls) != 1:
            out_.append(u"断った書類で組み直した包みを掛けた(か元を掛けていない)")
        if [m[u"作った"] for m in rec4[u"混ぜ物"]] != [False, False, False] or rec4[u"字の file"][u"持つ"][u"字が同じ"] != 0 or rec4[u"字の file"][u"持たない"][u"字が同じ"] != 0 or (rec4[u"字の file"][u"持つ"][u"数"], rec4[u"字の file"][u"持たない"][u"数"]) != (1, 1):
            out_.append(u"断った書類の file の数え方・混ぜ物が違う")
        if rec4[u"元の fact の行の数"] != HAND_ROWS_ALL:
            out_.append(u"断った書類でも元の fact の行の数を数える")
        if rec4[u"タグの数"][u"nonNumeric"] != HAND_TAGS[u"nonNumeric"]:
            out_.append(u"断った書類のタグの数が違う")
        # 書類 1 本の中の例外も断ったに数える
        orig = ms.build_text
        ms.build_text = lambda *a, **k: (_ for _ in ()).throw(ValueError("x"))
        try:
            rec5, _e = ms.process_doc(tool, os.path.join(docs, "S2FAKE01.zip"), tmp, FakeRunner(mv), mixtures=False)
        finally:
            ms.build_text = orig
        if not rec5[u"断った"] or rec5[u"断った理由"] != u"組む途中の例外":
            out_.append(u"組む途中の例外を断ったに数えない: %s" % rec5[u"断った理由"])
        # 道具が落ちても使い捨ての場所は残らない
        try:
            ms.process_doc(tool, os.path.join(docs, "S2FAKE01.zip"), tmp, FakeRunner(mv, crash_on=2), mixtures=False)
        except RuntimeError:
            pass
        if os.listdir(tmp):
            out_.append(u"途中で落ちたとき使い捨ての場所が残る")
    return out_


# 手で数えた HTM_A + HTM_B のタグの数(file 全体の開きタグの字): nonFraction = Sales・Nil・Cost・頭の部 1 つ + B の Assets = 5、
# nonNumeric = Title・Inner・Empty・頭の部 2 つ + B の Text = 6、footnote = 1
HAND_TAGS = {u"nonFraction": 5, u"nonNumeric": 6, u"footnote": 1}


def totals_problems(ms=None):
    ms = ms or MS
    out_ = []

    def ent(declined=False, fs=True, ss=True, rows=10, cls=u"走った", fh=(1, 1), fn=(2, 1), tags=(3, 2, 1), mixes=()):
        return od([(u"断った", declined), (u"断った理由", u"知らない属性" if declined else u""), (u"タグの数", od(zip(ms.IX_KINDS, tags))), (u"元の fact の行の数", rows),
                   (u"元の 1 回", od([(u"類", u"走った"), (u"符号ごとの行", {})])), (u"字の file", od([(u"持たない", od([(u"数", fn[0]), (u"字が同じ", fn[1])])), (u"持つ", od([(u"数", fh[0]), (u"字が同じ", fh[1])]))])),
                   (u"fact が同じ", fs), (u"鳴り方が同じ", ss), (u"組み直しの 1 回", None if declined else od([(u"類", cls), (u"符号ごとの行", {})])),
                   (u"混ぜ物", list(mixes))])

    def mx(made, fs, ss, kind=u"抜く"):
        return od([(u"種類", kind), (u"作った", made), (u"fact が同じ", fs), (u"鳴り方が同じ", ss)])
    dev = [ent(mixes=[mx(True, False, True), mx(True, False, False, u"文脈を替える"), mx(False, False, False, u"符号を返す")]) for _ in range(2)]
    prod = [ent(), ent(declined=True, fs=False, ss=False, rows=7, fh=(1, 0), fn=(3, 0), tags=(10, 20, 30)), ent(fs=False, ss=True, cls=u"止まった", fh=(0, 0), fn=(4, 2)), ent(ss=False, cls=u"走らなかった")]
    per = dev + prod
    t = ms.totals_of(per, 2)
    keys = list(t)
    if keys != [u"開発の 5 本", u"本番だけの 4 本", u"全部", u"混ぜ物"]:
        out_.append(u"集計の群の名・並びが違う: %s" % keys)
        return out_
    p = t[u"本番だけの 4 本"]
    got = (p[u"書類"], p[u"断った書類"], p[u"fact が同じ書類"], p[u"鳴り方が同じ書類"], sum(p[u"組み直した包みの 1 回の類ごと"].values()))
    if got != (4, 1, 2, 2, 3):          # 書類・断った・fact が同じ・鳴り方が同じ書類・類の合計(断った書類は類に数えない)
        out_.append(u"本番の群の数が手で数えた値と違う: %s" % (got,))
    if dict(p[u"組み直した包みの 1 回の類ごと"]) != {u"走った": 1, u"止まった": 1, u"走らなかった": 1} or dict(p[u"断った理由ごと"]) != {u"知らない属性": 1}:
        out_.append(u"類ごと・断った理由ごとの数が違う")
    if (p[u"file"][u"持つ"][u"数"], p[u"file"][u"持つ"][u"字が同じ"], p[u"file"][u"持たない"][u"数"], p[u"file"][u"持たない"][u"字が同じ"]) != (3, 2, 11, 4) or p[u"元の fact の行の数の合計"] != 37:
        out_.append(u"file の数・fact の行の数の合計が手で数えた値と違う: %s %s" % (json.dumps(p[u"file"]), p[u"元の fact の行の数の合計"]))
    if dict(p[u"ix のタグの数の合計"]) != {u"nonFraction": 19, u"nonNumeric": 26, u"footnote": 33}:
        out_.append(u"ix のタグの数の合計が違う: %s" % dict(p[u"ix のタグの数の合計"]))
    if p[u"元の fact の行が 0 の書類"] != 0 or ms.totals_of([ent(rows=0), ent(rows=5), ent(rows=0)], 1)[u"全部"][u"元の fact の行が 0 の書類"] != 2:
        out_.append(u"元の fact の行が 0 の書類の数が違う")
    dv = t[u"開発の 5 本"]
    if (dv[u"書類"], dv[u"fact が同じ書類"], dv[u"断った書類"]) != (2, 2, 0) or t[u"全部"][u"書類"] != 6 or t[u"全部"][u"断った書類"] != 1:
        out_.append(u"開発の群・全部の数が違う")
    m = t[u"混ぜ物"]
    if dict(m) != {u"混ぜ物の数": 6, u"作れた数": 4, u"fact が同じでない数": 6, u"鳴り方が同じでない数": 4}:
        out_.append(u"混ぜ物の合計が手で数えた値と違う: %s" % dict(m))
    j = ms.judged(t, 6)
    jv = list(j.values())
    if (jv[0][u"書類"], jv[0][u"分母"], jv[1][u"書類"], jv[2][u"書類"], jv[3][u"file"], jv[3][u"分母"], jv[4][u"file"], jv[4][u"分母"], jv[5][u"個"], jv[5][u"分母"], jv[6][u"個"]) != (2, 4, 1, 2, 4, 11, 2, 3, 6, 6, 4):
        out_.append(u"予測の判定に要る数が手で数えた値と違う: %s" % [dict(x) if isinstance(x, dict) else x for x in jv])
    return out_


# ======================================================================== 6. 道具の確かめ・記録
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
        if not stops(ms, ms.check_tool, tool, FakeRunner(mv, freeze=u"foo==1\n"), want_sha=wp):
            out_.append(u"arelle-release の行が無いのに止まらない")
        if not stops(ms, ms.check_tool, tool, r, want_sha=u"0" * 64):
            out_.append(u"ModelValue.py の sha256 が封と違うのに止まらない")
        if not stops(ms, ms.check_tool, tool, r):
            out_.append(u"封の sha256(既定)と違うのに止まらない")
        if not stops(ms, ms.check_tool, os.path.join(d, "none"), r, want_sha=wp):
            out_.append(u"道具の場所が無いのに止まらない")
    return out_


# ======================================================================== 8. 監査 REVISE で足した縛り
class TamperRunner(FakeRunner):
    u"""組み直した包み(2 回目の呼び出し)だけ、fact を 1 行落とす・指摘の行を 1 つ足す、を言う作り物の道具。"""

    def __init__(self, mv_path, drop=False, add_sound=False):
        FakeRunner.__init__(self, mv_path)
        self.drop, self.add_sound = drop, add_sound

    def __call__(self, cmd, timeout):
        res = FakeRunner.__call__(self, cmd, timeout)
        if os.path.basename(cmd[0]) == "arelleCmdLine" and len(self.calls) == 2:
            text, to = res
            if self.drop:
                path = self.calls[-1]["csv"]
                with io.open(path, encoding="utf-8", newline="") as fh:
                    rows = fh.read().split(u"\r\n")
                rows = [r for r in rows if r]
                with io.open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(u"\r\n".join(rows[:-1]) + u"\r\n")
            if self.add_sound:
                text = text + u"[EDINET.EC5611W] 足した指摘\n"
            return text, to
        return res


def docmain_problems(ms=None):
    u"""本線の比べ: 組み直した包みの fact・鳴り方が元と違うと、``process_doc`` の「fact が同じ」「鳴り方が同じ」が False になる(元と同じなら True)。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        zp = os.path.join(d, "S2FAKE01.zip")
        make_doc_zip(zp, 1)
        tool, mv = make_tool(d)
        tmp = os.path.join(d, "tmp")
        os.makedirs(tmp)
        for drop, add_sound, want in ((False, False, (True, True)), (True, False, (False, True)), (False, True, (True, False)), (True, True, (False, False))):
            rec, _e = ms.process_doc(tool, zp, tmp, TamperRunner(mv, drop, add_sound), mixtures=False)
            got = (rec[u"fact が同じ"], rec[u"鳴り方が同じ"])
            if got != want:
                out_.append(u"組み直しの fact を落とす=%s・指摘を足す=%s のとき (fact が同じ, 鳴り方が同じ) が %s(手で決めた値は %s)" % (drop, add_sound, got, want))
    return out_


HDR_ALT = (u"<ix:header>\n\n   <ix:hidden>\n"
           u'      <ix:nonNumeric contextRef="FilingDateInstant" name="jpdei_cor:EDINETCodeDEI">E99999</ix:nonNumeric><ix:nonNumeric xsi:nil="true" contextRef=\'FilingDateInstant\' name="jpdei_cor:FundCodeDEI"/>\n'
           u'\n      <ix:nonFraction scale="0" decimals="0" unitRef="pure" contextRef="FilingDateInstant" name="jpdei_cor:NumberOfSubmissionDEI">1</ix:nonFraction>\n   </ix:hidden>\n'
           u'   <ix:references><link:schemaRef xlink:href="fake.xsd" xlink:type="simple"/></ix:references>\n'
           u'   <ix:resources>\n      <link:roleRef xlink:href="http://x/a.xsd#rol_a" roleURI="http://x/role/a" xlink:type="simple"/>\n'
           u'      <xbrli:context id="C1">\n         <xbrli:entity><xbrli:identifier scheme="http://disclosure.edinet-fsa.go.jp">E99999-000</xbrli:identifier></xbrli:entity>\n'
           u'         <xbrli:period><xbrli:startDate>2025-04-01</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period>\n      </xbrli:context>\n\n'
           u'      <xbrli:context id="C2"><xbrli:period><xbrli:instant>2026-03-31</xbrli:instant></xbrli:period>\n'
           u'         <xbrli:entity><xbrli:identifier scheme="http://disclosure.edinet-fsa.go.jp">E99999-000</xbrli:identifier></xbrli:entity>\n'
           u'         <xbrli:scenario><xbrldi:explicitMember dimension="jppfs_cor:ComponentsOfEquityAxis">jppfs_cor:ShareholdersEquityMember</xbrldi:explicitMember>\n'
           u'            <xbrldi:explicitMember dimension="jppfs_cor:ConsolidatedOrNonConsolidatedAxis">jppfs_cor:NonConsolidatedMember</xbrldi:explicitMember></xbrli:scenario></xbrli:context>\n'
           u'      <xbrli:unit id="JPY"><xbrli:measure>iso4217:JPY</xbrli:measure></xbrli:unit>\n'
           u'      <xbrli:unit id="JPYPerShares">\n         <xbrli:divide><xbrli:unitNumerator><xbrli:measure>iso4217:JPY</xbrli:measure></xbrli:unitNumerator>\n'
           u'            <xbrli:unitDenominator><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unitDenominator></xbrli:divide>\n      </xbrli:unit>\n'
           u"   </ix:resources>\n</ix:header>")
HTM_ALT = HTM_A.replace(HDR, HDR_ALT)
H_KEYS = {"sections", "pos", "before", "hidden", "references", "resources"}
F_KEYS = {"kind", "self", "start", "end", "parent", "attrs"}


def hdrraw_problems(ms=None):
    u"""表 H は元の字を持たない: 頭の部の字の形(字下げ・1 行に詰める・空行・属性の並び・引用符・自己閉じの空白)が組む部品の決めと違っても、組んだ字は決めの字。表の鍵の集まりを縛る。"""
    ms = ms or MS
    out_ = []
    if HTM_ALT == HTM_A or HDR_ALT == HDR or HTM_ALT.count(u"<ix:header>") != 1:
        out_.append(u"作り物の字の作り損ね")
        return out_
    plain, F, H = ms.strip_text(HTM_ALT)
    if plain != PLAIN_A:
        out_.append(u"頭の部の形が違う元から素の本文が変わる")
    got = ms.build_text(plain, F, H)
    if got != HTM_A:
        i = next((k for k in range(min(len(got), len(HTM_A))) if got[k] != HTM_A[k]), min(len(got), len(HTM_A)))
        out_.append(u"頭の部の字の形が違う元から決めの字が出ない(最初の違い: %r)" % got[max(0, i - 20):i + 40])
    if set(H.keys()) != H_KEYS:
        out_.append(u"表 H の鍵が %s だけでない: %s" % (sorted(H_KEYS), sorted(H.keys())))
    if any(set(e.keys()) != F_KEYS for e in F):
        out_.append(u"表 F の行の鍵が %s だけでない" % sorted(F_KEYS))
    _p, _F, H0 = ms.strip_text(HTM_A)
    if json.dumps(H, sort_keys=True) != json.dumps(H0, sort_keys=True):
        out_.append(u"頭の部の字の形が違う元と決めの字の元で表 H が違う(字の形を表に持っている)")
    blob = json.dumps(H, ensure_ascii=False)
    if u"\n" in blob.replace(u"\\n", u"") or u"   " in blob:
        out_.append(u"表 H に頭の部の元の字の空白・改行が残っている")
    return out_


def ctx3_problems(ms=None):
    u"""文脈を替える: 文脈が 3 つ以上あるとき、順で最初の別の値を選ぶ。"""
    ms = ms or MS
    out_ = []

    def fact(name, ctx, st):
        return od([("kind", u"nonFraction"), ("self", False), ("start", st), ("end", st + 1), ("parent", -1), ("attrs", {"name": name, "contextRef": ctx})])
    files = [(u"f0", u"ABCDE", [fact("a", "C1", 0), fact("b", "C1", 1), fact("c", "C2", 2)], None), (u"f1", u"FG", [fact("d", "C3", 0), fact("e", "C2", 1)], None)]
    r = ms.mix_tables(files, u"文脈を替える")
    if r is None or r[0] != 0 or r[1][0]["attrs"]["contextRef"] != u"C2" or r[1][0]["attrs"]["name"] != "a":
        out_.append(u"文脈を替えるが順で最初の別の値(C2)を選ばない: %s" % (r[1][0]["attrs"] if r else None))
    files2 = [(u"f0", u"AB", [fact("a", "C1", 0), fact("b", "C3", 1)], None), (u"f1", u"CD", [fact("c", "C2", 0)], None)]
    r = ms.mix_tables(files2, u"文脈を替える")
    if r is None or r[1][0]["attrs"]["contextRef"] != u"C3":
        out_.append(u"別の値の順が file をまたいで先頭から数えていない")
    return out_


def devopen_problems(ms=None):
    u"""開発の入口は 5 本だけ: 7 本以上の zip で ``dev_docs`` は 5 本を選んだ所で止まり、6 本目を開かない(``zipfile.ZipFile`` を数える)。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        for i in range(1, 8):
            make_doc_zip(os.path.join(d, "S2FAKE0%d.zip" % i), i)
        opened = []
        real = ms.zipfile.ZipFile

        class Counting(real):
            def __init__(self, f, *a, **kw):
                opened.append(os.path.basename(str(f)))
                real.__init__(self, f, *a, **kw)
        ms.zipfile.ZipFile = Counting
        try:
            got = ms.dev_docs(d, 5)
        finally:
            ms.zipfile.ZipFile = real
        if [g[0] for g in got] != [u"S2FAKE0%d" % i for i in range(1, 6)]:
            out_.append(u"開発の 5 本が並びの頭の 5 本でない: %s" % [g[0] for g in got])
        if opened != [u"S2FAKE0%d.zip" % i for i in range(1, 6)]:
            out_.append(u"開いた zip が並びの頭の 5 本だけでない: %s" % opened)
        if ms.DEV_COUNT != 5 or ms.dev_docs.__defaults__ != (5,):
            out_.append(u"dev_docs の既定の本数が 5 でない")
    return out_


def dev_docs_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        make_docs(d, 3)
        got = ms.dev_docs(d, 2)
        if [g[0] for g in got] != STEMS[:2]:
            out_.append(u"開発の本数・並びが違う: %s" % [g[0] for g in got])
        if [g[0] for g in ms.dev_docs(d, 5)] != STEMS:
            out_.append(u"5 本に足りないとき全部を返さない")
        # 並びの頭の本数だけ開く: 3 本目以降の zip が壊れていても読まれない
        with open(os.path.join(d, "S2FAKE03.zip"), "wb") as fh:
            fh.write(b"not a zip")
        with open(os.path.join(d, "S2ZZZ.zip"), "wb") as fh:
            fh.write(b"not a zip")
        if [g[0] for g in ms.dev_docs(d, 2)] != STEMS[:2]:
            out_.append(u"開発の本数より後の zip を開いている(壊れた zip で落ちる)")
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
        # 1 本目は混ぜ物つきで 5 回・2 本目と 3 本目は 2 回ずつ
        if len(runner.calls) != 5 + 2 + 2:
            out_.append(u"道具の呼び出しの数が違う(開発の 1 本は混ぜ物つき 5 回、残りは 2 回ずつ): %d" % len(runner.calls))
        mat = rec[u"材料"]
        if (mat[u"書類の本数"], mat[u"書類の file 名の並びの sha256"], mat[u"開発の 5 本の番号"], mat[u"道具の版"], mat[u"道具 P の ModelValue.py の sha256"], mat[u"Python の版(道具 P)"], mat[u"規則の年"], mat[u"時間の上限(秒)"], mat[u"混ぜ物の種類"]) != (
                3, ORDER_SHA, [1], u"2.47.5", hashlib.sha256(MV_P).hexdigest(), u"Python 3.11.17", u"EDINET-2026", 600, list(ms.MIX_KINDS)):
            out_.append(u"材料の欄が手で数えた値と違う: %s" % dict(mat))
        if [dd[u"番号"] for dd in rec[u"書類"]] != [1, 2, 3] or [len(dd[u"混ぜ物"]) for dd in rec[u"書類"]] != [3, 0, 0]:
            out_.append(u"書類の番号・混ぜ物の置き場所が違う(混ぜ物は開発の本数だけ)")
        t = rec[u"集計"]
        if (t[u"開発の 5 本"][u"書類"], t[u"本番だけの 2 本"][u"書類"], t[u"全部"][u"fact が同じ書類"], t[u"混ぜ物"][u"混ぜ物の数"]) != (1, 2, 3, 3):
            out_.append(u"集計が手で数えた値と違う")
        text = ms.dumps(rec)
        for leak in STEMS + [u"E9999", u"S2OTHER1", u".xbrl", u".htm", u"audit", u"本文の字", u"Sales", u"Title", u"jppfs", u"1,234", u"題"]:
            if leak in text:
                out_.append(u"記録に材料の字が在る: %s" % leak)
        if set(secret[3]) != set([u"E9999%d" % i for i in (1, 2, 3)]) or list(secret[2]) != STEMS or not {"Sales", "Assets", "Cost"} <= set(secret[1]):
            out_.append(u"secret の docID・EDINET コード・要素の名が違う")
        if os.listdir(tmp):
            out_.append(u"使い捨ての場所が残っている")
        # 67 本でない置き場・道具の確かめの失敗では 1 回も掛けない
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
            (u"断ったのに fact が同じ", refresh_after(lambda r: (r[u"書類"][1].__setitem__(u"断った", True), r[u"書類"][1].__setitem__(u"組み直しの 1 回", None)))),
            (u"混ぜ物を本番の書類に置く", refresh_after(lambda r: r[u"書類"][1].__setitem__(u"混ぜ物", [od([(u"種類", u"抜く"), (u"作った", True), (u"fact が同じ", False), (u"鳴り方が同じ", True)])] * 3))),
            (u"混ぜ物の種類を変える", refresh_after(lambda r: r[u"書類"][0][u"混ぜ物"][0].__setitem__(u"種類", u"消す"))),
            (u"字が同じが数より多い", refresh_after(lambda r: r[u"書類"][0][u"字の file"][u"持つ"].__setitem__(u"字が同じ", 9))),
            (u"判定の数を変える", lambda r: [r[k] for k in r if k.startswith(u"予測の判定に要る数")][0].__setitem__(u"XB0-1 fact が同じ書類", 99))]
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
    secret = (set(), {u"NetSalesOfX"}, [u"zzdoc"], {u"E99991"}, {u"[EDINET.EC5611W] ある指摘の行の本文"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out_.append(u"きれいな記録で止まる")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"company", 1)])), (u"禁止の欄(label)", od([(u"label", 1)])),
        (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])),
        (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])),
        (u"file の名(xsd)", od([(u"x", u"jpcrp030000-asr-001.xsd")])), (u"file の名(htm)", od([(u"x", u"0101010_honbun.htm")])), (u"file の名(PublicDoc)", od([(u"x", u"XBRL/PublicDoc/x")])),
        (u"要素の名", od([(u"x", u"理由 NetSalesOfX")])),
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


# ======================================================================== 7. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "csv", "glob", "hashlib", "importlib", "io", "json", "os", "re", "shutil", "sys", "tempfile", "zipfile")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "adapters", "core", "audit_core", "subprocess")
CALLED = (("W", "select_docs"), ("W", "order_sha256"), ("W", "doc_xsd_names"), ("V", "count_one"), ("V", "command"), ("V", "exec_cmd"), ("V", "tool_info"), ("V", "check_clean"))
NOT_COPIED = ("select_docs", "order_sha256", "doc_xsd_names", "sha256_file", "codes_of", "run_class", "count_one", "command", "exec_cmd", "tool_info", "strip_copy", "is_envelope", "is_e_code")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
#: 組む部品の仲間(これらの関数の本体は、元の字・包み・zip・file を読む名前を使わない)
BUILD_FUNCS = ("build_text", "render_header", "open_tag", "attr_text")
BUILD_FORBIDDEN_NAMES = ("load_package", "zipfile", "open", "io", "os", "strip_text", "process_doc", "entries", "data", "text", "zip_path", "csv", "read_rows", "parse_header", "parse_tree", "package_with", "build_files")


def build_isolation_problems(src=None):
    u"""組む部品は素の本文・表 F・表 H だけを引数に取り、元の字・包み・zip を読まない。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    funcs = dict((n.name, n) for n in tree.body if isinstance(n, ast.FunctionDef))
    out_ = []
    b = funcs.get("build_text")
    if b is None or [a.arg for a in b.args.args] != ["plain", "F", "H"] or b.args.vararg or b.args.kwarg or b.args.kwonlyargs or b.args.defaults:
        out_.append(u"build_text の引数が (plain, F, H) だけでない")
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
        if any(v in ("os", "zipfile", "io", "csv") for v, _a in attrs):
            out_.append(u"組む部品 %s が os・zipfile・io を使っている" % nm)
    # process_doc は組む部品に表だけを渡す(元の字を渡さない)
    pd = funcs.get("process_doc")
    calls = [n for n in ast.walk(pd) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "build_text"] if pd else []
    for c in calls:
        if len(c.args) != 3 or c.keywords or any(not isinstance(a, ast.Name) or a.id not in ("plain", "F2", "H2", "F", "H", "_p") for a in c.args):
            out_.append(u"build_text の呼び出しが表と素の本文以外を渡している")
    rb = funcs.get("rebuilt_texts")
    rcalls = [n for n in ast.walk(rb) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "build_text"] if rb else []
    if len(rcalls) != 1 or [getattr(a, "id", None) for a in rcalls[0].args] != ["plain", "F", "H"]:
        out_.append(u"rebuilt_texts が build_text に (plain, F, H) だけを渡していない")
    # 置き場の zip を読む所は 1 か所(load_package)
    readers = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and any(isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "zipfile" and x.attr == "ZipFile" for x in ast.walk(n))]
    if sorted(readers) != ["dev_docs", "load_package", "write_package"]:
        out_.append(u"zipfile を開く関数が想定の 3 つ(置き場を読む load_package・並びの頭を選ぶ dev_docs・使い捨ての包みを書く write_package)でない: %s" % readers)
    lp = funcs.get("load_package")
    if not lp or not any(isinstance(x, ast.Constant) and x.value == "r" for x in ast.walk(lp)) and any(isinstance(x, ast.Constant) and x.value in ("w", "a", "x") for x in ast.walk(lp)):
        out_.append(u"load_package が置き場の zip を書き込みで開く")
    return out_


def import_problems(src=None):
    u"""script の import は標準ライブラリと importlib だけ(engine を読まない・subprocess を持たない)。前の便の script は V・W から呼び写さない。"""
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
    if VALIDATE_NAME not in consts:
        out_.append(u"前の便の script を読む名が一意の名(%s)でない" % VALIDATE_NAME)
    if not any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "W" for t in n.targets) and isinstance(n.value, ast.Attribute) and n.value.attr == "W" for n in tree.body):
        out_.append(u"便 XG0 の script を便 XV0 の script の W から受けていない(Stop の型が 2 つになる)")
    if any(n in consts for n in (u"_xv0_tag_wall_2026_11_21", u"_xg1_tag_wall_2026_11_21", u"_xb0_tag_wall_2026_11_21", u"_xb0_tag_narrow")):
        out_.append(u"他の便と重なる名で読んでいる")
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            if u".env" in n.value or u"dotenv" in n.value or u"API_KEY" in n.value:
                out_.append(u"鍵・.env の字が在る")
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
    # ---- 剥がす
    (u"V1 頭の部を除かない(中身を素の本文に残す)", u"                inner = text[hdr_open.end():m.start()]\n", u"                inner = text[hdr_open.end():m.start()]\n                plain.append(text[hdr_open.start():m.end()])\n                plen += m.end() - hdr_open.start()\n", ("strip", "build")),
    (u"V2 頭の部の位置を持たない(常に 0)", u'                H["pos"] = plen\n', u'                H["pos"] = 0\n', ("strip", "build")),
    (u"V3 頭の部の前に開いた行の数を持たない", u'                H["before"] = len(F)\n', u'                H["before"] = 0\n', ("strip", "build")),
    (u"V4 入れ子の親を持たない", u'("parent", stack[-1] if stack else -1)', u'("parent", -1)', ("strip", "build")),
    (u"V5 自己閉じを持たない", u'e = od([("kind", kind), ("self", selfc),', u'e = od([("kind", kind), ("self", False),', ("strip", "build")),
    (u"V6 閉じタグの位置を持たない", u'            F[stack[-1]]["end"] = plen\n', u"            pass\n", ("strip", "build")),
    (u"V7 属性の並びの順を持つ(昇順にしない)", u"    return dict(sorted(out.items()))\n\n\ndef count_ix_tags", u"    return out\n\n\ndef count_ix_tags", ("strip",)),
    (u"V8 知らない属性を断らない", u'        if k not in known:\n            raise Decline(u"知らない属性")\n', u"        pass\n", ("decline",)),
    (u"V9 知らない ix の要素を断らない", u'        if kind not in IX_KINDS:\n            raise Decline(u"知らない ix の要素")\n        if closing:', u"        if kind not in IX_KINDS:\n            continue\n        if closing:", ("decline", "doc")),
    (u"V10 ix のタグの数の照合を外す", u'    if len(IX_ANY_RE.findall(text)) != len(toks):\n        raise Decline(u"ix のタグの字が知らない形")\n', u"", ("decline",)),
    (u"V11 2 つ目の頭の部を断らない", u'            if H is not None or stack:\n                raise Decline(u"2 つ目の頭の部か入れ子の頭の部")\n', u"            if stack:\n                raise Decline(u\"入れ子の頭の部\")\n", ("decline",)),
    (u"V12 閉じタグの名の照合を外す", u'            if attr_s.strip() or selfc or not stack or F[stack[-1]]["kind"] != kind:', u"            if attr_s.strip() or selfc or not stack:", ("decline",)),
    (u"V13 閉じていないものを断らない", u'    if hdr_open is not None or stack:\n        raise Decline(u"閉じていない")\n', u"", ("decline",)),
    (u"V14 属性の値の実体参照を直す(&amp; → &)", u"        out[k] = m.group(2) if m.group(2) is not None else m.group(3)\n", u'        out[k] = (m.group(2) if m.group(2) is not None else m.group(3)).replace("&amp;", "&")\n', ("strip",)),
    (u"V15 footnote の属性の一覧から footnoteRole を落とす", u'"footnoteRole", "xml:lang", "id")}', u'"xml:lang", "id")}', ("strip", "build")),
    # ---- 頭の部を読む
    (u"V16 文脈の軸を読まない", u'            out["members"] = mem\n', u'            out["members"] = []\n', ("strip", "build")),
    (u"V17 割り算の単位の下を読まない", u'("den", parse_measures(d["children"][1], "xbrli:measure"))', u'("den", [])', ("strip", "build")),
    (u"V18 roleRef を読まない(捨てる)", u'                    H["resources"].append(od([("type", "ref"), ("tag", c["name"]), ("self", c["self"]), ("attrs", c["attrs"])]))\n', u"                    pass\n", ("strip", "build")),
    (u"V19 隠しの fact の中身の字を持たない", u'("attrs", c["attrs"]), ("text", c["text"])])', u'("attrs", c["attrs"]), ("text", u"")])', ("strip", "build")),
    (u"V20 頭の部の子の並びを持たない(固定の並びにする)", u'H["sections"].append(sec["name"])', u'H["sections"] = list(HEADER_SECTIONS)', ("strip", "build")),
    (u"V21 知らない文脈の子を断らない", u'        else:\n            raise Decline(u"文脈の子が知らない形")\n', u"        else:\n            pass\n", ("decline",)),
    (u"V22 頭の部の中の知らない字を断らない", u'        if "<" in piece:\n            raise Decline(u"頭の部に知らない形の字")\n', u"", ("decline",)),
    # ---- 組む
    (u"V23 属性の並びを決めの並びでなく昇順にする", u"        parts.append(u\" %s=\\\"%s\\\"\" % (k, v))" if False else u"    for k in order:\n        if k in attrs:\n            v = attrs[k]", u"    for k in sorted(order):\n        if k in attrs:\n            v = attrs[k]", ("build", "norm")),
    (u"V24 引用符を常に ' にする", u"""            if '"' not in v:
                parts.append(u' %s="%s"' % (k, v))""", u"""            if True:
                parts.append(u" %s='%s'" % (k, v))""", ("build",)),
    (u"V25 自己閉じの前の空白を落とす", u'return u"<%s%s%s>" % (tag, attr_text(attrs, order), u" /" if selfc else u"")', u'return u"<%s%s%s>" % (tag, attr_text(attrs, order), u"/" if selfc else u"")', ("build",)),
    (u"V26 頭の部の子を 1 行ずつでなく空白なしでつなぐ", u'    lines.append(u"</ix:header>")\n    return u"\\n".join(lines)', u'    lines.append(u"</ix:header>")\n    return u"".join(lines)', ("build",)),
    (u"V27 頭の部を出さない", u"        parts.append(render_header(header))\n", u"        parts.append(u\"\")\n", ("build",)),
    (u"V28 頭の部を表 F の行より先に必ず出す", u'            if not done and c >= header["before"]:', u"            if not done:", ("build",)),
    (u"V29 子の位置の検査を外す", u'            if e["start"] < cur or e["end"] > limit or e["end"] < e["start"]:\n                raise Decline(u"位置が合わない")\n', u"", ("decline",)),
    (u"V30 親の番号の検査を外す", u'        if not (-1 <= e["parent"] < i):\n            raise Decline(u"親の番号が合わない")\n', u"", ("decline",)),
    (u"V31 組む部品が知らない ix の要素を断らない", u'        if e["kind"] not in ATTR_ORDER:\n            raise Decline(u"知らない ix の要素")\n', u"", ("decline",)),
    (u"V32 組む部品が知らない属性を断らない", u"    if unknown:\n        raise Decline(u\"知らない属性\")\n", u"", ("decline",)),
    (u"V33 値に引用符が両方在るときそのまま書く", u'            else:\n                raise Decline(u"値に引用符が両方在る")\n', u'            else:\n                parts.append(u" %s=\'%s\'" % (k, v))\n', ("build",)),
    (u"V34 組む部品が元の字を引数に取る", u"def build_text(plain, F, H):", u"def build_text(plain, F, H, text=None):", ("isolation",)),
    (u"V35 組む部品が zip を読む", u'    kids = collections.defaultdict(list)\n    for i, e in enumerate(F):\n        if e["kind"] not in ATTR_ORDER:', u'    zipfile.ZipFile\n    kids = collections.defaultdict(list)\n    for i, e in enumerate(F):\n        if e["kind"] not in ATTR_ORDER:', ("isolation",)),
    (u"V36 rebuilt_texts が元の字を渡す", u"            out.append((name, build_text(plain, F, H)))", u"            out.append((name, build_text(plain, F, H)))\n            data = 0\n            build_text(data, F, H)", ("isolation",)),
    (u"V37 zip を開く関数を足す", u"def write_package(entries, path):", u"def sneak(path):\n    with zipfile.ZipFile(path) as z:\n        return z.namelist()\n\n\ndef write_package(entries, path):", ("isolation",)),
    # ---- 混ぜ物
    (u"V38 抜くが xsi:nil の行を飛ばさない", u'            if e["kind"] == "nonFraction" and "xsi:nil" not in e["attrs"]:', u'            if e["kind"] == "nonFraction":', ("mix",)),
    (u"V39 抜くの後に親の番号を直さない", u"        if e2[\"parent\"] > i:\n            e2[\"parent\"] -= 1\n", u"", ("mix",)),
    (u"V40 抜くの後に頭の部の位置を直さない", u'        if H2["before"] > i:\n            H2["before"] -= 1\n', u"", ("mix",)),
    (u"V41 文脈を替えるが同じ値に替える(別の値を探さない)", u"            if v is not None and v != cur:", u"            if v is not None:", ("mix", "doc")),
    (u"V42 符号を返すが sign を足すだけ", u'        if "sign" in a:\n            del a["sign"]\n        else:\n            a["sign"] = "-"\n', u'        a["sign"] = "-"\n', ("mix", "doc")),
    (u"V43 符号を返すが 0 だけの fact を飛ばさない", u"        if not is_zero_content(files[fi][1][e[\"start\"]:e[\"end\"]]):\n            return fi, i\n", u"        return fi, i\n", ("mix",)),
    (u"V44 0 だけの判定が全角の 0 を数えない", u'set(t) <= set(u"0０")', u'set(t) <= set(u"0")', ("mix",)),
    (u"V45 混ぜ物が元の表を書き換える(複製しない)", u"    return [od((k, (dict(v) if k == \"attrs\" else v)) for k, v in e.items()) for e in F], H\n", u"    return F, H\n", ("mix",)),
    (u"V46 混ぜ物の当て先が zip の並び(名の昇順にしない)", u"    out.sort(key=lambda t: t[0])\n    return out\n", u"    return out\n", ("doc",)),
    # ---- 比べる
    (u"V47 fact が同じが行 0 でも同じにする", u"    return bool(a) and bool(b) and a == b\n", u"    return a == b\n", ("compare",)),
    (u"V48 CSV の見出しの行を除かない", u"    return sorted(rows[1:])\n", u"    return sorted(rows)\n", ("compare",)),
    (u"V49 CSV を並べ替えない", u"    return sorted(rows[1:])\n", u"    return rows[1:]\n", ("compare",)),
    (u"V50 CSV の欄の大きさの上限を直さない", u"    csv.field_size_limit(2 ** 31 - 1)\n", u"", ("compare",)),
    (u"V51 鳴り方が同じが類を見ない", u'    return a[u"類"] == b[u"類"] and dict(a[u"符号ごとの行"]) == dict(b[u"符号ごとの行"])', u'    return dict(a[u"符号ごとの行"]) == dict(b[u"符号ごとの行"])', ("compare",)),
    (u"V52 鳴り方が同じが符号ごとの数を見ない", u'    return a[u"類"] == b[u"類"] and dict(a[u"符号ごとの行"]) == dict(b[u"符号ごとの行"])', u'    return a[u"類"] == b[u"類"] and set(a[u"符号ごとの行"]) == set(b[u"符号ごとの行"])', ("compare",)),
    (u"V53 組み直しの包みを元の包みで置き換える(比べる相手が同じ)", u"        write_package(package_with(entries, tdict), new_zip)\n", u"        write_package(entries, new_zip)\n", ("doc",)),
    (u"V54 .xbrl を除かない", u"            if not info.filename.endswith(STRIP_SUFFIX):", u"            if True:", ("doc",)),
    (u"V55 組んだ字でなく元の字を組み直した包みに入れる", u'            out.append((info, texts[info.filename].encode("utf-8")))', u"            out.append((info, data))", ("doc",)),
    (u"V56 道具を 1 回しか掛けない(組み直しを掛けず元の結果を使う)", u"        new, new_rows, _t = run_tool(tool, new_zip, d, \"new\", runner)\n", u"        new, new_rows = orig, orig_rows\n", ("doc",)),
    (u"V57 時間の上限を渡さない", u"    text, timed_out = runner(cmd, TIMEOUT_SEC)", u"    text, timed_out = runner(cmd, None)", ("doc",)),
    (u"V58 規則の年を 2025 にする", u'YEAR = "EDINET-2026"', u'YEAR = "EDINET-2025"', ("seal", "doc")),
    (u"V59 --facts を付けない", u'    cmd = V.command(tool, YEAR, zip_path) + ["--facts", csv_path, "--factListCols", FACT_COLS]', u"    cmd = V.command(tool, YEAR, zip_path)", ("doc",)),
    (u"V60 使い捨ての場所を消さない", u"        shutil.rmtree(d, ignore_errors=True)\n", u"        pass\n", ("doc",)),
    (u"V61 断ったとき元の包みを掛けない", u"        orig, orig_rows, _t = run_tool(tool, orig_zip, d, \"orig\", runner)\n        rec[u\"元の fact の行の数\"] = len(orig_rows)", u"        orig, orig_rows = od([(u\"類\", u\"走った\"), (u\"符号ごとの行\", {})]), []\n        rec[u\"元の fact の行の数\"] = len(orig_rows)", ("doc",)),
    (u"V62 組む途中の例外を断ったに数えず落とす", u'            raise Decline(u"組む途中の例外")', u"            raise", ("doc",)),
    (u"V63 断った書類の fact が同じを True にする", u'            rec[u"fact が同じ"] = False\n            rec[u"鳴り方が同じ"] = False\n            rec[u"混ぜ物"] = [] if not mixtures', u'            rec[u"fact が同じ"] = True\n            rec[u"鳴り方が同じ"] = False\n            rec[u"混ぜ物"] = [] if not mixtures', ("doc",)),
    # ---- 数え方
    (u"V64 字が同じ file を持つ・持たないで分けない", u'        k = u"持つ" if h else u"持たない"', u'        k = u"持たない"', ("doc",)),
    (u"V65 ix:header の有無を閉じタグで数える", u'    return "<ix:header" in text', u'    return "</ix:header" in text and False', ("doc",)),
    (u"V66 断った書類の file を「同じ」に数える", u'            rec[u"字の file"] = count_files(entries, set())', u'            rec[u"字の file"] = count_files(entries, set(i.filename for i, _d in entries))', ("doc",)),
    (u"V67 タグの数を file 全体でなく本文だけで数える", u'    return od((k, len(re.findall(r"<ix:%s\\b" % k, text))) for k in IX_KINDS)', u'    return od((k, len(re.findall(r"<ix:%s\\b" % k, text.split("<ix:header")[0]))) for k in IX_KINDS)', ("doc",)),
    (u"V68 群を 5 本で割らない(開発と本番を同じにする)", u"    dev, prod = per_doc[:dev_count], per_doc[dev_count:]", u"    dev, prod = per_doc[:dev_count], per_doc", ("totals", "run")),
    (u"V69 断った書類を類に数える(None の類で落ちる)", u'        else:\n            cls[e[u"組み直しの 1 回"][u"類"]] += 1', u'        if True:\n            cls[(e[u"組み直しの 1 回"] or e[u"元の 1 回"])[u"類"]] += 1', ("totals",)),
    (u"V100 元の fact の行が 0 の書類を数えない", u'        zero_rows += 1 if e[u"元の fact の行の数"] == 0 else 0\n', u"", ("totals",)),
    (u"V70 混ぜ物の fact の差を数えない", u'            fact_diff += 0 if m[u"fact が同じ"] else 1', u"            fact_diff += 0", ("totals",)),
    (u"V71 混ぜ物の鳴り方の差を fact の差で数える", u'            sound_diff += 0 if m[u"鳴り方が同じ"] else 1', u'            sound_diff += 0 if m[u"fact が同じ"] else 1', ("totals",)),
    (u"V72 XB0-4 の分母を持つ file の数にする", u'(u"XB0-4 ix:header を持たない file のうち字が同じもの", od([(u"file", nh[u"字が同じ"]), (u"分母", nh[u"数"])]))', u'(u"XB0-4 ix:header を持たない file のうち字が同じもの", od([(u"file", nh[u"字が同じ"]), (u"分母", wh[u"数"])]))', ("totals",)),
    (u"V73 XB0-1 を全部の群で読む", u'    prod = tot[[k for k in tot if k.startswith(u"本番だけの")][0]]', u'    prod = tot[u"全部"]', ("totals",)),
    # ---- 道具の確かめ・記録
    (u"V74 版の照合を外す", u'    if info[u"版"] != want_version:\n        raise Stop(u"**道具の版が %s でない。止める**" % want_version)\n', u"", ("tools",)),
    (u"V75 sha256 の照合を外す", u'    if info[u"ModelValue.py の sha256"] != want_sha:', u"    if False:", ("tools",)),
    (u"V76 実行 file の在るかの確かめを外す", u"    if not os.path.isfile(os.path.join(tool, V.EXE_REL)):", u"    if False:", ("tools",)),
    (u"V77 sha256 の封の字を 1 字替える", u'SHA_P = "fd9b0d08', u'SHA_P = "ed9b0d08', ("seal",)),
    (u"V78 時間の上限を 60 秒にする", u"TIMEOUT_SEC = 600", u"TIMEOUT_SEC = 60", ("seal", "doc")),
    (u"V79 開発の本数を 6 にする", u"DEV_COUNT = 5", u"DEV_COUNT = 6", ("seal",)),
    (u"V80 混ぜ物の種類の並びを替える", u'MIX_KINDS = (u"抜く", u"文脈を替える", u"符号を返す")', u'MIX_KINDS = (u"抜く", u"符号を返す", u"文脈を替える")', ("seal", "doc")),
    (u"V81 開発の 5 本より後も開く(dev_docs が本数で止まらない)", u"            if len(found) == count:\n                break\n", u"", ("devdocs",)),
    (u"V82 混ぜ物を本番の書類にも掛ける", u"mixtures=(n <= dev_count))", u"mixtures=True)", ("run",)),
    (u"V83 --check が合計を照らさない", u'    if dumps(tot) != dumps(rec[u"集計"]) or', u'    if False or', ("verify",)),
    (u"V84 --check が判定の数を照らさない", u'or dumps(judged(tot, len(docs))) != dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):', u":", ("verify",)),
    (u"V85 --check が書類の本数を問わない", u"len(docs) != want or rec[u\"材料\"][u\"書類の本数\"] != want:", u"False:", ("verify",)),
    (u"V86 --check が断った書類の形を見ない", u'        if d[u"断った"] != (d[u"組み直しの 1 回"] is None) or (d[u"断った"] and (d[u"fact が同じ"] or d[u"鳴り方が同じ"])) or (not d[u"断った"] and d[u"断った理由"]):', u"        if False:", ("verify",)),
    (u"V87 --check が混ぜ物の形を見ない", u'        if len(d[u"混ぜ物"]) != (len(MIX_KINDS) if i <= dev_count else 0) or [m[u"種類"] for m in d[u"混ぜ物"]] != (list(MIX_KINDS) if i <= dev_count else []):', u"        if False:", ("verify",)),
    (u"V88 --check が字の file の数を見ない", u'            if f[u"字が同じ"] > f[u"数"] or (d[u"断った"] and f[u"字が同じ"]):', u"            if False:", ("verify",)),
    (u"V89 file の名の形の検査を外す", u"    V.check_clean(rec, text, secret)", u"    pass", ("clean",)),
    (u"V91 書いた後の検査を外す", u"        check_clean(rec, back, secret)\n    except SystemExit:", u"        pass\n    except SystemExit:", ("clean",)),
    (u"V92 書く前の検査を外す", u"    text = record_text(rec, secret)\n    os.makedirs", u"    text = dumps(rec)\n    os.makedirs", ("clean",)),
    (u"V93 道具の確かめの前に掛ける", u"    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)\n    per_doc = []", u"    info = od([(u\"版\", u\"\"), (u\"ModelValue.py の sha256\", u\"\"), (u\"package の一覧の sha256\", u\"\"), (u\"Python の版\", u\"\")])\n    per_doc = []", ("run", "e2e")),
    (u"V94 書類の選びを自分で書く(W.select_docs を呼ばない)", u"    docs = W.select_docs(docs_dir or DOCS_DIR, want)", u"    docs = dev_docs(docs_dir or DOCS_DIR, want)", ("wiring", "run")),
    (u"V95 前の便の script を他と重なる名で読む", u'VALIDATE_NAME = "_xb0_edinet_validate_2026_11_21"', u'VALIDATE_NAME = "_xv0_edinet_validate_2026_11_21"', ("wiring",)),
    (u"V99 便 XG0 の script を自分で読み直す(Stop の型が 2 つになる)", u'W = V.W ', u'W = _load_sibling("_xb0_other_wall", "xbrl_tag_wall_2026-11-21.py")  # ', ("wiring",)),
    (u"V96 engine を読む", u"import zipfile\n\nHERE", u"import zipfile\nfrom adapters.xbrl import instance as I\n\nHERE", ("wiring",)),
    (u"V97 subprocess を import する", u"import tempfile\nimport zipfile\n\nHERE", u"import subprocess\nimport tempfile\nimport zipfile\n\nHERE", ("wiring",)),
    (u"V98 道具の呼び出しを自分で書く(V.exec_cmd を呼ばない)", u"    runner = runner or V.exec_cmd\n    csv_path", u"    runner = runner or (lambda c, t: (u\"\", False))\n    csv_path", ("doc",)),
)
# ---- 監査 REVISE の後に足した変異(予測 = 赤になるべき検査。表は実行より先に書いた)
MUTANTS = MUTANTS + (
    (u"V101 本線の「fact が同じ」が組み直しの行どうしを比べる", u'rec[u"fact が同じ"] = facts_same(orig_rows, new_rows)', u'rec[u"fact が同じ"] = facts_same(new_rows, new_rows)', ("docmain",)),
    (u"V102 本線の「鳴り方が同じ」が組み直しどうしを比べる", u'rec[u"鳴り方が同じ"] = sounds_same(orig, new)', u'rec[u"鳴り方が同じ"] = sounds_same(new, new)', ("docmain",)),
    (u"V103 表 H に頭の部の中身の元の字を持たせ、render_header がそのまま返す",
     (u'                H["pos"] = plen\n', u'def render_header(H):\n    u"""表 H → ``ix:header`` の字。"""\n'),
     (u'                H["pos"] = plen\n                H["rawinner"] = inner\n', u'def render_header(H):\n    u"""表 H → ``ix:header`` の字。"""\n    if "rawinner" in H:\n        return u"<ix:header>" + H["rawinner"] + u"</ix:header>"\n'), ("hdrraw",)),
    (u"V104 表 F の行に開きタグの元の字を持たせる", u'("attrs", parse_attrs(attr_s, ATTR_ORDER[kind]))])', u'("attrs", parse_attrs(attr_s, ATTR_ORDER[kind])), ("raw", m.group(0))])', ("hdrraw",)),
    (u"V105 文脈を替えるが最後の別の値を選ぶ", u"        for fj, j in num_pool(files):", u"        for fj, j in reversed(num_pool(files)):", ("ctx3",)),
    (u"V106 dev_docs が 5 本を選んだ後も開き続け、頭の 5 本だけを返す",
     (u"            if len(found) == count:\n                break\n", u"    return found\n"), (u"", u"    return found[:count]\n"), ("devopen",)),
    (u"V107 dev_docs が 6 本目まで開いて 6 本を返す", u"            if len(found) == count:\n                break\n", u"            if len(found) == count + 1:\n                break\n", ("devopen",)),
)
#: 黙ることが分かっている変異(理由つき)
SILENT_BY_DESIGN = ()


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"strip": strip_problems, u"build": build_problems, u"decline": decline_problems, u"mix": mix_problems, u"compare": compare_problems,
             u"doc": doc_problems, u"totals": totals_problems, u"tools": tools_problems, u"devdocs": dev_docs_problems, u"docmain": docmain_problems, u"hdrraw": hdrraw_problems, u"ctx3": ctx3_problems, u"devopen": devopen_problems, u"run": run_problems, u"verify": verify_problems, u"clean": clean_problems, u"e2e": e2e_problems}
    if name in table:
        return table[name](mod)
    if name == u"wiring":
        return import_problems(src)
    if name == u"isolation":
        return build_isolation_problems(src)
    if name == u"norm":
        return build_problems(mod)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"strip", u"build", u"decline", u"mix", u"compare", u"doc", u"totals", u"tools", u"devdocs", u"docmain", u"hdrraw", u"ctx3", u"devopen", u"run", u"verify", u"clean", u"e2e", u"wiring", u"isolation")


def run_mutants(table=MUTANTS):
    base = read(SCRIPT_REL)
    out_ = []
    for name, old, new, checks in table:
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
        for old, new in ((u"`arelle-release` の版 `2.47.5`", u"`arelle-release` の版 `2.47.6`"), (SEAL_SHA_P, SEAL_SHA_P[:-1] + u"1"), (u"開発の 5 本 × 3 種類 = 15 個", u"開発の 5 本 × 3 種類 = 16 個"),
                         (u"| XB0-1(主) | fact が同じ書類は 56 本以上", u"| XB0-1(主) | fact が同じ書類は 57 本以上"), (u"1 回の時間の上限は 600 秒", u"1 回の時間の上限は 60 秒"),
                         (u"**抜く**", u"**消す**"), (u"--disclosureSystem EDINET-2026", u"--disclosureSystem EDINET-2025"), (u"便 XG0 と同じ 67 本", u"便 XG0 と同じ 66 本")):
            self.assertEqual(1, seal.count(old), old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"inline_build", body)


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
    def test_b_1_strip_gives_the_plain_text_and_the_two_tables(self):
        self.assertEqual([], strip_problems())

    def test_b_2_build_writes_the_same_bytes_from_the_tables_alone(self):
        self.assertEqual([], build_problems())

    def test_b_3_unknown_forms_are_declined(self):
        self.assertEqual([], decline_problems())

    def test_b_4_the_three_mixtures(self):
        self.assertEqual([], mix_problems())

    def test_b_5_comparisons(self):
        self.assertEqual([], compare_problems())

    def test_b_6_totals_and_the_judged_numbers(self):
        self.assertEqual([], totals_problems())

    def test_b_7_the_hand_made_files_cover_every_form(self):
        u"""作り物の字が入れ子・自己閉じ・xsi:nil・footnote・header・複数の文脈と単位・軸つきの文脈を含む(門が薄い材料で緑にならないこと)。"""
        a = HTM_A
        self.assertIn(u"<ix:nonNumeric", a.split(u"<ix:nonNumeric name=\"jpcrp_cor:Title\"")[1].split(u"</ix:nonNumeric>名")[0])             # 入れ子
        self.assertIn(u'xsi:nil="true" />', a)
        self.assertIn(u"<ix:footnote", a)
        self.assertIn(u"<ix:header>", a)
        self.assertGreaterEqual(a.count(u"<xbrli:context "), 2)
        self.assertGreaterEqual(a.count(u"<xbrli:unit "), 2)
        self.assertIn(u"<xbrli:divide>", a)
        self.assertIn(u"<xbrli:scenario>", a)
        self.assertGreaterEqual(a.count(u"<xbrldi:explicitMember"), 2)
        self.assertIn(u"<ix:hidden>", a)
        self.assertIn(u"<ix:references>", a)
        self.assertIn(u"<link:roleRef", a)
        self.assertNotEqual(HTM_B, HTM_B_CANON)
        self.assertNotIn(u"<ix:header", HTM_B)
        self.assertEqual(len(hand_f_a()), 7)
        self.assertEqual(len(set(HAND_TAGS.values())) >= 3, True)
        self.assertEqual(sum(HAND_TAGS.values()), 12)
        self.assertEqual(len(set([HAND_ROWS_ALL, HAND_FACT_ROWS_A, HAND_FACT_ROWS_B])), 3)


class ReviseTest(unittest.TestCase):
    u"""監査 REVISE の指摘 4 つ(本線の比べ・表 H は元の字を持たない・文脈を替える・開発の入口は 5 本だけ)。"""

    def test_g_1_the_main_comparison_turns_false_when_the_rebuilt_package_differs(self):
        self.assertEqual([], docmain_problems())

    def test_g_2_table_h_and_f_hold_no_original_text(self):
        self.assertEqual([], hdrraw_problems())

    def test_g_3_the_context_swap_takes_the_first_other_value_with_three_or_more_contexts(self):
        self.assertEqual([], ctx3_problems())

    def test_g_4_the_dev_entry_opens_only_the_first_five_zips(self):
        self.assertEqual([], devopen_problems())


class RunTest(unittest.TestCase):
    def test_c_1_the_tool_check(self):
        self.assertEqual([], tools_problems())

    def test_c_2_one_document_goes_through_with_a_fake_tool(self):
        self.assertEqual([], doc_problems())

    def test_c_3_dev_docs_open_only_the_head_of_the_list(self):
        self.assertEqual([], dev_docs_problems())

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
        self.assertNotEqual([], import_problems(base + u"\nfrom adapters.xbrl import instance\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.system('a')\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef select_docs(a, b):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef codes_of(a):\n    return None\n"))
        self.assertNotEqual([], import_problems(base.replace(u"W.order_sha256(", u"order_sha256(")))
        self.assertNotEqual([], import_problems(base.replace(u"V.count_one(", u"count_one(")))

    def test_e_3_the_build_function_reads_nothing_but_the_three_tables(self):
        self.assertEqual([], build_isolation_problems())

    def test_e_4_the_isolation_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], build_isolation_problems(base.replace(u"def build_text(plain, F, H):", u"def build_text(plain, F, H, original=None):")))
        self.assertNotEqual([], build_isolation_problems(base.replace(u"def build_text(plain, F, H):", u"def build_text(text, F, H):")))
        self.assertNotEqual([], build_isolation_problems(base.replace(u"    kids = collections.defaultdict(list)\n", u"    kids = collections.defaultdict(list)\n    data = open(plain)\n", 1)))
        self.assertNotEqual([], build_isolation_problems(base + u"\ndef reader(p):\n    return zipfile.ZipFile(p)\n"))

    def test_e_5_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_6_the_script_leaves_sys_modules_as_it_found_them_except_its_own_earlier_script_names(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_inline_build_script_for_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        self.assertEqual(mod.V.__name__, VALIDATE_NAME)
        self.assertIs(mod.W, mod.V.W)
        self.assertIs(mod.Stop, mod.V.Stop)
        self.assertNotEqual(VALIDATE_NAME, "xbrl_edinet_validate_script_for_seal_gate")
        del mod

    def test_e_7_the_default_place_is_outside_the_repo_and_the_gate_never_opens_it(self):
        top = os.path.realpath(REPO)
        self.assertFalse(os.path.realpath(MS.DOCS_DIR).startswith(top + os.sep))
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record|dev_docs|dev_run)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"docs|rec_path|\*\*kw|rp|\bd\b", m.group(2)), m.group(0))

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
        self.assertGreaterEqual(len(MUTANTS), 25)

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
