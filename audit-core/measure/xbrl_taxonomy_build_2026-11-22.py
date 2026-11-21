# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TAXONOMY_BUILD_SEAL_2026-11-22.md(XT0 ― 受理済みの有報の提出者別タクソノミ(``.xsd`` と linkbase 5 つ)を、中身を読んだ表から自前の部品で組み直すと、公開の道具が読むタクソノミ・fact・検査の鳴り方は元と同じになるか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。** engine(``core/``・``adapters/``)は読まない・変えない。書類の選び方・符号の読み方・1 回の類・fact の比べ方・写しの関数は前の便の script の関数を importlib で呼ぶ(写さない)。

    python3 measure/xbrl_taxonomy_build_2026-11-22.py --tool-p <venv の場所>           # 道具を確かめて 67 本(+ 開発の 5 本の混ぜ物 30 個)を掛け、記録を書く(本番は 1 回)
    python3 measure/xbrl_taxonomy_build_2026-11-22.py --check                         # 記録の形・合計・禁止のものを検査する。道具は呼ばない・掛け直さない
    python3 measure/xbrl_taxonomy_build_2026-11-22.py --dev --tool-p <venv の場所>     # 開発の 5 本だけ(置き場の並びの頭の 5 本の zip だけ開く)。記録は書かない

組む部品(``build_xsd``・``build_linkbase``)は **表 S・表 K だけ** を引数に取る。元の file の字も元の包みも読まない(file の名は表の外から渡す)。置き場の zip は前の便の ``load_package`` が読む(この script は zip を開かない)。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く。開発の 5 本で試して直した所は「5 本で決めた」と書く):
- 表 S(``.xsd``): ``target``・``defaults``(根の ``attributeFormDefault``・``elementFormDefault`` のうち在るもの)・``imports``([(namespace, schemaLocation)])・``refs``(``link:linkbaseRef`` の並び。``href``・``role``・``arcrole``。
  封 §1 は「在りか・role が在ればその値」だが、67 本の実物の linkbaseRef は全部 ``xlink:arcrole`` を持つので、``arcrole`` も在ればその値として持つ・``xlink:type`` は ``simple`` だけ)・``elements``(宣言の並び。属性の名 → 値の辞書。名前空間つきの属性は ``{名前空間}局所名``・QName の値(``type``・``substitutionGroup``)は ``(名前空間, 局所名)`` に解く)。
  知らない形(断る): ``xsd:import`` の ``namespace`` か ``schemaLocation`` が無い・``annotation`` が 2 つ以上・``appinfo`` に ``linkbaseRef`` 以外・``roleType`` などの知らない子・要素の宣言に子・知らない属性・解けない接頭辞。
- 表 K(linkbase 1 つ): ``refs``(``roleRef``・``arcroleRef`` の並び。``tag``・``uri``・``href``)・``links``(拡張 link の並び。``tag``・``role``・``ends``・``arcs``)。
  ``ends`` の 1 つは ``kind`` が ``loc``(``href``・``role``)か ``label``(``lang``・``role``・``id``・``text``)。``arcs`` の 1 つは ``from``・``to``(``ends`` の中の番号)・``arcrole``・``attrs``(そのほかの属性の名 → 値)。
  ``xlink:label`` の字は持たない。1 つの arc が同じ字の ``xlink:label`` を持つ複数の端を結ぶ書き方は、端の組ごとの arc に開く(from の端 × to の端の順)。
  端と arc の入り混じりは arc ごとの ``before``(その arc より前に在った端の数。開いた arc は元の arc と同じ値)で持つ。封 §1 の列挙に無いが、持たないと組み直した包みの書き出し(ラベルの関係)が元と違った
  (開発の 5 本のうち 1 本で、端を全部先に並べただけで、道具がラベルの関係を並べる順が変わった。link の中で loc と arc の位置が変わると、道具が href を読んで文書を読み込む順が変わるためと読んだが、道具の中までは見ていない)。組むときは arc の順に、その ``before`` までの端を先に書く。
  知らない形(断る): 知らない拡張 link・知らない arc・知らない属性・端の無い ``xlink:label`` を指す arc・字の在る loc や arc・``label`` 以外の子を持つ ``label``。arc の属性は ``order``・``weight``・``use``・``priority``・``preferredLabel``・``xbrldt:contextElement``・``xbrldt:closed``・``xbrldt:usable`` だけ。
- 道具の書き出しの並びが呼び出しごとに変わる所(開発の 5 本で、同じ元の包みを 2 回掛けて見た): 役割型の ``Used On`` の欄の並びは python の字の hash の種で変わるので、道具の呼び出しの前に ``/usr/bin/env PYTHONHASHSEED=0`` を付けて種を固定する(``SEED_PREFIX``)。
  概念は同じラベルの行の並びが道具の中の set の順(object の id の順)で毎回変わり、種では直らない。封 §1 の「file の順のまま」のままだと、同じ包みを 2 回掛けても概念が「同じ」にならない。
  そこで概念だけ、見出しの行・ラベルの並び(同じ先頭の欄が続く行の塊の並び)はそのまま比べ、同じ先頭の欄が続く行の塊の中だけ並びを問わない(``canon_rows``)。**これは封の字を緩める決めなので、報告で人間の確認を求める。** ほかの 6 つは file の順のまま。
- 読む前の断り: DOCTYPE か実体宣言が在る・XML 宣言の encoding が utf-8 でない・UTF-16/32 の BOM・XML として読めない。
- 組み方の決め(開発の 5 本で決めた。本番の前にここへ留める): XML 宣言は ``<?xml version="1.0" encoding="utf-8"?>``・字下げは 2 字・改行は ``\\n``・自己閉じは `` />``・引用符は ``"``(値の ``&``・``<``・``"``・改行・タブは実体参照)。
  linkbase の接頭辞は ``link``・``xlink``・(使うときだけ)``xbrldt``。``xlink:label`` は link の中の端に順に ``L1``・``L2``・… を付ける。属性の並びは ``ATTR_ORDER_*`` の並び。
  ``.xsd`` の接頭辞は名前空間から決める: 固定の表(``xsd``・``link``・``xlink``・``xbrli``・``xbrldt``・DTR の ``num``・``nonnum``)・提出者の名前空間(``.../jp...NNNNNN/xxx/NNN/ENNNNN-NNN/...``)は ``jp...NNNNNN-xxx_ENNNNN-NNN``・
  それ以外は名前空間の最後の path の字(NCName に当たるとき)・当たらなければ ``ns``・同じ字が重なったら ``_2``・``_3``。理由: 道具の書き出し(concepts・ラベルの関係)の ``Name``・``Type`` の欄に接頭辞の字が出るため、表が接頭辞を持たないなら名前空間から決めるしかない。
- 書き出し 7 つの名は ``OUTPUT_KEYS``(概念・役割型・表示・計算・次元・ラベル・一般特殊)。CSV は csv として読み、見出しの行を含めた行の並びを file の順のまま比べる。「行が 1 以下」は見出しの行を含めて数える。
  封 §4 末尾の「元の包みの concepts の行が 1 以下の書類が在ったら同じ。」は読み方が 1 通りに決まらないので、比べ方の規則(行が 1 以下なら同じとしない)のとおりに実装し、そういう書類の数を別に数えて書く。
- 道具は書類 1 本につき、元の包み・組み直した包みに掛け方 A・B の 2 回ずつ、混ぜ物の包みにも A・B の 2 回ずつ掛ける(合わせて 4 + 12 = 16 回)。掛け方 B は ``--validate`` を付けない(封 §1 の字のとおり)。
- 混ぜ物 M1〜M6 の当て先は「表の並びの順で最初」(封の字)。M2 は最初の arc の ``weight`` が ``1`` か ``-1`` でないときは作れなかった・M5 は最初の ``abstract`` が ``false`` の要素が ``periodType`` を持たないか ``duration``・``instant`` でないときは作れなかった。
  当て先の表の kind が無い・当て先が無いときは作れなかった。混ぜ物の「違いを見つけた」は 全部同じ でないこと(= タクソノミが同じでない か fact が同じでない)・「鳴り方が違う」は鳴り方が同じでないこと。数えるのは作れた混ぜ物だけ。
- 比べる相手: 元の包みと組み直した包みの zip は別の file 名(``orig.zip``・``new.zip``)。道具の書き出しに zip の場所が出ないことは開発の 5 本で見た。
- 1 回の時間の上限は 600 秒。規則の年は ``EDINET-2026`` だけ。字が同じ: 組んだ file の bytes が元の file の bytes と同じ(6 種類を分けて数える。断った書類の file は「同じでない」に数える)。
"""
from __future__ import print_function

import argparse
import collections
import copy
import csv
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

BUILD_NAME = "_xt0_inline_build_2026_11_21"


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


B = _load_sibling(BUILD_NAME, "xbrl_inline_build_2026-11-21.py")
V = B.V                                            # 便 XV0 の script(便 XB0 の script が一意の名で読んだもの)
W = B.W                                            # 便 XG0 の script(Stop の型を 1 つにするため同じ object を使う)

SEAL_REL = "docs/XBRL_TAXONOMY_BUILD_SEAL_2026-11-22.md"
SEAL_COMMIT = "dae701b0"
SCRIPT_REL = "measure/xbrl_taxonomy_build_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/taxonomy_build_2026-11-22.json"
DOCS_DIR = W.DOCS_DIR
DOCS_WANT = W.DOCS_WANT

# ---- 封 §1 の決めごと(字で留める。封の門が封の字と照らす)
TOOL_VERSION = "2.47.5"
SHA_P = "fd9b0d08bf283452fe4ebd6ec9de2f273010de0420b70e61c993a6c033814635"
PLUGINS = "validate/EDINET|inlineXbrlDocumentSet"
YEAR = "EDINET-2026"
FACT_COLS = "Name contextRef unitRef Dec Value EntityScheme EntityIdentifier Period Dimensions"
TIMEOUT_SEC = 600
DEV_COUNT = 5
PUBLICDOC = "XBRL/PublicDoc/"
CONCEPT_LABEL_ARCROLE = "http://www.xbrl.org/2003/arcrole/concept-label"
GENERAL_SPECIAL_ARCROLE = "http://www.xbrl.org/2003/arcrole/general-special"
DOMAIN_MEMBER_ARCROLE = "http://xbrl.org/int/dim/arcrole/domain-member"
#: 書き出し 7 つ(掛け方 A の 6 つと、掛け方 B の 1 つ)
OUTPUT_KEYS = (u"概念", u"役割型", u"表示", u"計算", u"次元", u"ラベルの関係", u"一般特殊")
#: 行が 1 以下なら同じとしない書き出し(中身が無い書類が在りうる 3 つ ― 計算・次元・一般特殊 ― は両方が同じ字なら同じ)
NEED_ROWS = (u"概念", u"役割型", u"表示", u"ラベルの関係")
#: 道具の中で並びが決まらない書き出し(概念: 同じラベルの行の並びが、道具の中の set(object の id の順)で呼び出しごとに変わる。開発の 5 本で、同じ包みを 2 回掛けても並びが違うことを見た)
UNORDERED_OUTPUTS = (u"概念",)
#: 道具の呼び出しの前に付ける。書き出しの並びが python の字の hash の種で変わる(役割型の ``Used On`` の欄の並び。開発の 5 本で、種を固定すると同じ包みの 2 回が同じになることを見た)
SEED_PREFIX = ["/usr/bin/env", "PYTHONHASHSEED=0"]
FILE_KINDS = ("xsd", "cal", "def", "lab", "lab-en", "pre")
FILE_SUFFIX = collections.OrderedDict([("xsd", ".xsd"), ("cal", "_cal.xml"), ("def", "_def.xml"), ("lab", "_lab.xml"), ("lab-en", "_lab-en.xml"), ("pre", "_pre.xml")])
MIX_KINDS = (u"表示の arc を抜く", u"計算の向きを返す", u"日本語のラベルを変える", u"英語のラベルを変える", u"期の型を返す", u"定義の arc を抜く")
MIX_IDS = ("M1", "M2", "M3", "M4", "M5", "M6")
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) か None。XT0-6 は「作れた数に等しい」(下限が作れた数)
BOUNDS = collections.OrderedDict([
    ("XT0-1", (54, None)), ("XT0-2", (None, 5)), ("XT0-3", (54, None)), ("XT0-4", (None, 93)), ("XT0-5", (28, None)), ("XT0-6", (u"作れた数", None)), ("XT0-7", (5, 15))])
LIMITS = [
    u"表は元のタクソノミの file から作っている。タクソノミの中身(どの要素を作るか・木・ラベル・計算の向き)を決める力は測っていない。",
    u"本文の inline XBRL(便 XB0 で測った)・マニフェスト・画像・監査報告書の包みは元のまま。",
    u"比べたのは公開の道具 1 つ(道具 P。司令塔が 1 行を直したもの)の書き出しで、道具が書き出さない性質(例: order の値そのもの・道具が読み捨てる属性)の違いは見えない。",
    u"EDINET の本物の検査とは照らしていない。",
    u"組み方は開発の 5 本で決めた。67 本は無作為ではない。有報だけ。",
    u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]

Stop = W.Stop
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps

# ---- 名前空間
NS_XSD = "http://www.w3.org/2001/XMLSchema"
NS_LINK = "http://www.xbrl.org/2003/linkbase"
NS_XLINK = "http://www.w3.org/1999/xlink"
NS_XBRLI = "http://www.xbrl.org/2003/instance"
NS_XBRLDT = "http://xbrl.org/2005/xbrldt"
NS_XML = "http://www.w3.org/XML/1998/namespace"
DTR_NUM = "http://www.xbrl.org/dtr/type/numeric"
DTR_NONNUM = "http://www.xbrl.org/dtr/type/non-numeric"
FIXED_PREFIX = collections.OrderedDict([(NS_XSD, "xsd"), (NS_LINK, "link"), (NS_XLINK, "xlink"), (NS_XBRLI, "xbrli"), (NS_XBRLDT, "xbrldt"), (DTR_NUM, "num"), (DTR_NONNUM, "nonnum")])
FILING_NS_RE = re.compile(r"^http://disclosure\.edinet-fsa\.go\.jp/(jp[a-z]+[0-9]+)/([a-z]+)/[0-9]+/(E[0-9]{5}-[0-9]{3})/")
NCNAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
XML_DECL_RE = re.compile(br"^<\?xml[^>]*?encoding\s*=\s*[\"']([^\"']+)[\"']")

# ---- 表の形(既知のもの)
XSD_ROOT_ATTRS = ("targetNamespace", "attributeFormDefault", "elementFormDefault")
XSD_KEY_PERIOD = "{%s}periodType" % NS_XBRLI
XSD_KEY_BALANCE = "{%s}balance" % NS_XBRLI
XSD_ELEMENT_ATTRS = ("id", XSD_KEY_BALANCE, XSD_KEY_PERIOD, "abstract", "name", "nillable", "substitutionGroup", "type")      # 組むときの並びでもある
XSD_QNAME_ATTRS = ("type", "substitutionGroup")
LINK_TAGS = collections.OrderedDict([("calculationLink", "calculationArc"), ("definitionLink", "definitionArc"), ("labelLink", "labelArc"), ("presentationLink", "presentationArc")])
REF_TAGS = collections.OrderedDict([("roleRef", "roleURI"), ("arcroleRef", "arcroleURI")])
ARC_ATTR_ORDER = ("order", "weight", "use", "priority", "preferredLabel", "{%s}contextElement" % NS_XBRLDT, "{%s}closed" % NS_XBRLDT, "{%s}usable" % NS_XBRLDT)
XLINK_KEYS = dict((k, "{%s}%s" % (NS_XLINK, k)) for k in ("type", "href", "role", "arcrole", "label", "from", "to"))
XML_LANG = "{%s}lang" % NS_XML


class Decline(Exception):
    u"""知らない形に当たった(断る)。``reason`` は固定の字(材料の字を入れない)。"""

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason


# ======================================================================================================
# XML を読む(標準ライブラリの ElementTree。名前空間の接頭辞は読んだ後に持たない)
def split_clark(tag):
    if tag.startswith("{"):
        ns, local = tag[1:].split("}", 1)
        return ns, local
    return None, tag


def parse_xml(data):
    u"""bytes → 根の node。node = dict(tag=(ns, local), attrs={鍵: 値}, scope={接頭辞: 名前空間}, children=[node], elem)。知らない形は ``Decline``。"""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff") or data[:4] in (b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff"):
        raise Decline(u"知らない文字の符号化")
    body = data[3:] if data[:3] == b"\xef\xbb\xbf" else data
    m = XML_DECL_RE.match(body)
    if m and m.group(1).lower() != b"utf-8":
        raise Decline(u"知らない文字の符号化")
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise Decline(u"DOCTYPE か実体宣言")
    stack = []
    root = None
    pending = []
    try:
        for ev, obj in ET.iterparse(io.BytesIO(data), events=("start-ns", "start", "end")):
            if ev == "start-ns":
                pending.append(obj)
            elif ev == "start":
                if pending:
                    scope = dict(stack[-1]["scope"]) if stack else {}
                    for p, u in pending:
                        scope[p or ""] = u
                    pending = []
                else:
                    scope = stack[-1]["scope"] if stack else {}
                node = {"tag": split_clark(obj.tag), "attrs": dict(obj.attrib), "scope": scope, "elem": obj, "children": []}
                if stack:
                    stack[-1]["children"].append(node)
                else:
                    root = node
                stack.append(node)
            else:
                stack.pop()
    except ET.ParseError:
        raise Decline(u"XML として読めない")
    if root is None:
        raise Decline(u"XML として読めない")
    return root


def text_of(node):
    return node["elem"].text or u""


def check_blank(node):
    u"""node の中身の字と子の後ろの字が空白だけであること。"""
    if text_of(node).strip():
        raise Decline(u"字の在る所が知らない形")
    for c in node["children"]:
        if (c["elem"].tail or u"").strip():
            raise Decline(u"字の在る所が知らない形")


def resolve_qname(value, scope):
    u"""QName の値 → (名前空間, 局所名)。名前空間が無いときは ``""``。解けない接頭辞は断る。"""
    v = value.strip()
    if v.count(":") > 1 or not v:
        raise Decline(u"QName の形が知らない形")
    if ":" in v:
        p, local = v.split(":", 1)
        uri = scope.get(p)
        if uri is None:
            raise Decline(u"解けない接頭辞")
        return uri, local
    return scope.get("", ""), v


def only_attrs(node, allowed):
    if set(node["attrs"]) - set(allowed):
        raise Decline(u"知らない属性")


# ======================================================================================================
# 剥がす(表 S・表 K)
def strip_xsd(data):
    u"""``.xsd`` の bytes → 表 S。"""
    root = parse_xml(data)
    if root["tag"] != (NS_XSD, "schema"):
        raise Decline(u"根が schema でない")
    only_attrs(root, XSD_ROOT_ATTRS)
    if "targetNamespace" not in root["attrs"]:
        raise Decline(u"targetNamespace が無い")
    check_blank(root)
    S = od([("target", root["attrs"]["targetNamespace"]), ("defaults", od((k, root["attrs"][k]) for k in ("attributeFormDefault", "elementFormDefault") if k in root["attrs"])),
            ("imports", []), ("refs", []), ("elements", [])])
    annotations = 0
    for c in root["children"]:
        if c["tag"][0] != NS_XSD:
            raise Decline(u"知らない子")
        kind = c["tag"][1]
        if kind == "import":
            only_attrs(c, ("namespace", "schemaLocation"))
            if "namespace" not in c["attrs"] or "schemaLocation" not in c["attrs"] or c["children"]:
                raise Decline(u"import の形が知らない形")
            check_blank(c)
            S["imports"].append((c["attrs"]["namespace"], c["attrs"]["schemaLocation"]))
        elif kind == "annotation":
            annotations += 1
            check_blank(c)
            if annotations > 1 or c["attrs"] or len(c["children"]) != 1 or c["children"][0]["tag"] != (NS_XSD, "appinfo") or c["children"][0]["attrs"]:
                raise Decline(u"annotation の形が知らない形")
            app = c["children"][0]
            check_blank(app)
            for r in app["children"]:
                if r["tag"] != (NS_LINK, "linkbaseRef") or r["children"]:
                    raise Decline(u"appinfo の子が知らない形")
                only_attrs(r, (XLINK_KEYS["type"], XLINK_KEYS["href"], XLINK_KEYS["role"], XLINK_KEYS["arcrole"]))
                if r["attrs"].get(XLINK_KEYS["type"]) != "simple" or XLINK_KEYS["href"] not in r["attrs"]:
                    raise Decline(u"linkbaseRef の形が知らない形")
                check_blank(r)
                S["refs"].append(od([("href", r["attrs"][XLINK_KEYS["href"]]), ("role", r["attrs"].get(XLINK_KEYS["role"])), ("arcrole", r["attrs"].get(XLINK_KEYS["arcrole"]))]))
        elif kind == "element":
            only_attrs(c, XSD_ELEMENT_ATTRS)
            if c["children"] or "name" not in c["attrs"]:
                raise Decline(u"要素の宣言の形が知らない形")
            check_blank(c)
            e = {}
            for k, v in c["attrs"].items():
                e[k] = resolve_qname(v, c["scope"]) if k in XSD_QNAME_ATTRS else v
            S["elements"].append(e)
        else:
            raise Decline(u"知らない子")
    return S


def strip_linkbase(data):
    u"""linkbase の bytes → 表 K。"""
    root = parse_xml(data)
    if root["tag"] != (NS_LINK, "linkbase") or root["attrs"]:
        raise Decline(u"根が linkbase でない")
    check_blank(root)
    K = od([("refs", []), ("links", [])])
    for c in root["children"]:
        ns, local = c["tag"]
        if ns != NS_LINK:
            raise Decline(u"知らない子")
        if local in REF_TAGS:
            only_attrs(c, (REF_TAGS[local], XLINK_KEYS["type"], XLINK_KEYS["href"]))
            if set(c["attrs"]) != set((REF_TAGS[local], XLINK_KEYS["type"], XLINK_KEYS["href"])) or c["attrs"][XLINK_KEYS["type"]] != "simple" or c["children"]:
                raise Decline(u"ref の形が知らない形")
            check_blank(c)
            K["refs"].append(od([("tag", local), ("uri", c["attrs"][REF_TAGS[local]]), ("href", c["attrs"][XLINK_KEYS["href"]])]))
        elif local in LINK_TAGS:
            K["links"].append(strip_link(c, local))
        else:
            raise Decline(u"知らない拡張 link")
    return K


def strip_link(node, local):
    only_attrs(node, (XLINK_KEYS["type"], XLINK_KEYS["role"]))
    if node["attrs"].get(XLINK_KEYS["type"]) != "extended":
        raise Decline(u"拡張 link の形が知らない形")
    check_blank(node)
    ends = []
    by_label = collections.defaultdict(list)
    raw_arcs = []
    arc_tag = LINK_TAGS[local]
    for c in node["children"]:
        ns, tag = c["tag"]
        if ns != NS_LINK:
            raise Decline(u"知らない子")
        if tag == "loc":
            only_attrs(c, (XLINK_KEYS["type"], XLINK_KEYS["href"], XLINK_KEYS["role"], XLINK_KEYS["label"]))
            if c["attrs"].get(XLINK_KEYS["type"]) != "locator" or XLINK_KEYS["href"] not in c["attrs"] or XLINK_KEYS["label"] not in c["attrs"] or c["children"]:
                raise Decline(u"loc の形が知らない形")
            check_blank(c)
            by_label[c["attrs"][XLINK_KEYS["label"]]].append(len(ends))
            ends.append(od([("kind", "loc"), ("href", c["attrs"][XLINK_KEYS["href"]]), ("role", c["attrs"].get(XLINK_KEYS["role"]))]))
        elif tag == "label" and local == "labelLink":
            only_attrs(c, (XLINK_KEYS["type"], XLINK_KEYS["label"], XLINK_KEYS["role"], XML_LANG, "id"))
            if c["attrs"].get(XLINK_KEYS["type"]) != "resource" or XLINK_KEYS["label"] not in c["attrs"] or c["children"]:
                raise Decline(u"label の形が知らない形")
            by_label[c["attrs"][XLINK_KEYS["label"]]].append(len(ends))
            ends.append(od([("kind", "label"), ("lang", c["attrs"].get(XML_LANG)), ("role", c["attrs"].get(XLINK_KEYS["role"])), ("id", c["attrs"].get("id")), ("text", text_of(c))]))
        elif tag == arc_tag:
            only_attrs(c, (XLINK_KEYS["type"], XLINK_KEYS["arcrole"], XLINK_KEYS["from"], XLINK_KEYS["to"]) + ARC_ATTR_ORDER)
            if c["attrs"].get(XLINK_KEYS["type"]) != "arc" or not all(XLINK_KEYS[k] in c["attrs"] for k in ("arcrole", "from", "to")) or c["children"]:
                raise Decline(u"arc の形が知らない形")
            check_blank(c)
            raw_arcs.append((c, len(ends)))
        else:
            raise Decline(u"知らない子")
    arcs = []
    for c, before in raw_arcs:
        a = c["attrs"]
        froms, tos = by_label.get(a[XLINK_KEYS["from"]], []), by_label.get(a[XLINK_KEYS["to"]], [])
        if not froms or not tos:
            raise Decline(u"端の無い xlink:label を指す arc")
        extra = od((k, a[k]) for k in ARC_ATTR_ORDER if k in a)
        for f in froms:
            for t in tos:
                arcs.append(od([("from", f), ("to", t), ("before", before), ("arcrole", a[XLINK_KEYS["arcrole"]]), ("attrs", od(extra))]))
    return od([("tag", local), ("role", node["attrs"].get(XLINK_KEYS["role"])), ("ends", ends), ("arcs", arcs)])


def find_files(entries):
    u"""包みの PublicDoc 直下から ``.xsd`` と linkbase 5 つを 1 つずつ。(kind → (file の名, bytes))。1 つずつでなければ断る。"""
    found = dict((k, []) for k in FILE_KINDS)
    for info, data in entries:
        n = info.filename
        if not n.startswith(PUBLICDOC) or "/" in n[len(PUBLICDOC):]:
            continue
        for k in FILE_KINDS:
            if n.endswith(FILE_SUFFIX[k]):
                found[k].append((n, data))
    if any(len(v) != 1 for v in found.values()):
        raise Decline(u"タクソノミの file が 1 つずつでない")
    return od((k, found[k][0]) for k in FILE_KINDS)


def strip_tables(files):
    u"""``files`` = (kind → bytes)。(kind → 表)。知らない形・例外は ``Decline``。"""
    out = od()
    for k in FILE_KINDS:
        try:
            out[k] = strip_xsd(files[k]) if k == "xsd" else strip_linkbase(files[k])
        except Decline:
            raise
        except Exception:                                      # noqa: BLE001  知らない形は断る
            raise Decline(u"剥がす途中の例外")
    return out


# ======================================================================================================
# 組む(表 S・表 K だけを受ける。元の file も元の包みも読まない)
def esc_text(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\r", "&#13;")


def esc_attr(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;").replace("\n", "&#10;").replace("\r", "&#13;").replace("\t", "&#9;")


def prefix_for(uri):
    u"""名前空間 → 接頭辞の候補(固定の表・提出者の名前空間・最後の path の字・``ns``)。"""
    if uri in FIXED_PREFIX:
        return FIXED_PREFIX[uri]
    m = FILING_NS_RE.match(uri)
    if m:
        return u"%s-%s_%s" % (m.group(1), m.group(2), m.group(3))
    last = uri.rstrip("/").rsplit("/", 1)[-1]
    if NCNAME_RE.match(last) and not last.lower().startswith("xml"):
        return last
    return u"ns"


def assign_prefixes(uris):
    u"""名前空間の並び → {名前空間: 接頭辞}。同じ字が重なったら ``_2``・``_3``。固定の表の接頭辞は固定の名前空間だけが使う。"""
    used = set(FIXED_PREFIX.values())
    out = od()
    for u in uris:
        if u in out:
            continue
        if u in FIXED_PREFIX:
            out[u] = FIXED_PREFIX[u]
            continue
        base = prefix_for(u)
        p, n = base, 1
        while p in used:
            n += 1
            p = u"%s_%d" % (base, n)
        used.add(p)
        out[u] = p
    return out


def qname_text(q, prefixes):
    ns, local = q
    return u"%s:%s" % (prefixes[ns], local) if ns else local


def open_attrs(pairs):
    return u"".join(u' %s="%s"' % (k, esc_attr(v)) for k, v in pairs)


def build_xsd(S):
    u"""表 S だけから ``.xsd`` の字を返す。"""
    uris = [S["target"]]
    for e in S["elements"]:
        for k in XSD_QNAME_ATTRS:
            if k in e and e[k][0]:
                uris.append(e[k][0])
    prefixes = assign_prefixes([NS_XSD, NS_LINK, NS_XLINK, NS_XBRLI] + uris)
    unknown = set(k for e in S["elements"] for k in e) - set(XSD_ELEMENT_ATTRS)
    if unknown:
        raise Decline(u"知らない属性")
    decls = [(u"xmlns:%s" % p, u) for u, p in prefixes.items()]
    root_attrs = decls + [(k, v) for k, v in S["defaults"].items()] + [(u"targetNamespace", S["target"])]
    lines = [u'<?xml version="1.0" encoding="utf-8"?>', u"<xsd:schema%s>" % open_attrs(root_attrs)]
    for ns, loc in S["imports"]:
        lines.append(u"  <xsd:import%s />" % open_attrs([(u"schemaLocation", loc), (u"namespace", ns)]))
    if S["refs"]:
        lines.append(u"  <xsd:annotation>")
        lines.append(u"    <xsd:appinfo>")
        for r in S["refs"]:
            pairs = [(u"xlink:type", u"simple"), (u"xlink:href", r["href"])]
            if r["role"] is not None:
                pairs.append((u"xlink:role", r["role"]))
            if r["arcrole"] is not None:
                pairs.append((u"xlink:arcrole", r["arcrole"]))
            lines.append(u"      <link:linkbaseRef%s />" % open_attrs(pairs))
        lines.append(u"    </xsd:appinfo>")
        lines.append(u"  </xsd:annotation>")
    for e in S["elements"]:
        pairs = []
        for k in XSD_ELEMENT_ATTRS:
            if k not in e:
                continue
            name = u"xbrli:" + split_clark(k)[1] if k.startswith("{") else k
            pairs.append((name, qname_text(e[k], prefixes) if k in XSD_QNAME_ATTRS else e[k]))
        lines.append(u"  <xsd:element%s />" % open_attrs(pairs))
    lines.append(u"</xsd:schema>")
    return u"\n".join(lines) + u"\n"


def build_linkbase(K):
    u"""表 K だけから linkbase の字を返す。"""
    uses_dt = any(k.startswith("{%s}" % NS_XBRLDT) for L in K["links"] for a in L["arcs"] for k in a["attrs"])
    decls = [(u"xmlns:link", NS_LINK), (u"xmlns:xlink", NS_XLINK)] + ([(u"xmlns:xbrldt", NS_XBRLDT)] if uses_dt else [])
    lines = [u'<?xml version="1.0" encoding="utf-8"?>', u"<link:linkbase%s>" % open_attrs(decls)]
    for r in K["refs"]:
        if r["tag"] not in REF_TAGS:
            raise Decline(u"知らない ref")
        lines.append(u"  <link:%s%s />" % (r["tag"], open_attrs([(REF_TAGS[r["tag"]], r["uri"]), (u"xlink:type", u"simple"), (u"xlink:href", r["href"])])))
    for L in K["links"]:
        if L["tag"] not in LINK_TAGS:
            raise Decline(u"知らない拡張 link")
        lines.append(u"  <link:%s%s>" % (L["tag"], open_attrs([(u"xlink:type", u"extended")] + ([(u"xlink:role", L["role"])] if L["role"] is not None else []))))
        end_lines = []
        for i, e in enumerate(L["ends"], 1):
            if e["kind"] == "loc":
                pairs = [(u"xlink:type", u"locator"), (u"xlink:href", e["href"])] + ([(u"xlink:role", e["role"])] if e["role"] is not None else []) + [(u"xlink:label", u"L%d" % i)]
                end_lines.append(u"    <link:loc%s />" % open_attrs(pairs))
            elif e["kind"] == "label" and L["tag"] == "labelLink":
                pairs = [(u"xlink:type", u"resource"), (u"xlink:label", u"L%d" % i)]
                if e["lang"] is not None:
                    pairs.append((u"xml:lang", e["lang"]))
                if e["role"] is not None:
                    pairs.append((u"xlink:role", e["role"]))
                if e["id"] is not None:
                    pairs.append((u"id", e["id"]))
                end_lines.append(u"    <link:label%s>%s</link:label>" % (open_attrs(pairs), esc_text(e["text"])))
            else:
                raise Decline(u"知らない端")
        done = 0
        for a in L["arcs"]:
            if not (0 <= a["from"] < len(L["ends"]) and 0 <= a["to"] < len(L["ends"])):
                raise Decline(u"arc の端の番号が合わない")
            if set(a["attrs"]) - set(ARC_ATTR_ORDER):
                raise Decline(u"知らない属性")
            if not (done <= a["before"] <= len(L["ends"])):
                raise Decline(u"arc の位置が合わない")
            lines.extend(end_lines[done:a["before"]])
            done = a["before"]
            pairs = [(u"xlink:type", u"arc"), (u"xlink:arcrole", a["arcrole"]), (u"xlink:from", u"L%d" % (a["from"] + 1)), (u"xlink:to", u"L%d" % (a["to"] + 1))]
            for k in ARC_ATTR_ORDER:
                if k in a["attrs"]:
                    pairs.append((u"xbrldt:" + split_clark(k)[1] if k.startswith("{") else k, a["attrs"][k]))
            lines.append(u"    <link:%s%s />" % (LINK_TAGS[L["tag"]], open_attrs(pairs)))
        lines.extend(end_lines[done:])
        lines.append(u"  </link:%s>" % L["tag"])
    lines.append(u"</link:linkbase>")
    return u"\n".join(lines) + u"\n"


def build_tables(tables):
    u"""(kind → 表)から (kind → bytes)。表だけを受ける。知らない形・例外は ``Decline``。"""
    out = od()
    for k in FILE_KINDS:
        try:
            out[k] = (build_xsd(tables[k]) if k == "xsd" else build_linkbase(tables[k])).encode("utf-8")
        except Decline:
            raise
        except Exception:                                      # noqa: BLE001
            raise Decline(u"組む途中の例外")
    return out


# ======================================================================================================
# 混ぜ物(表を 1 か所だけ変える)
def first_arc(K):
    u"""link の並びと arc の並びの順で最初の arc の (link の番号, arc の番号)。無ければ ``None``。"""
    for li, L in enumerate(K["links"]):
        if L["arcs"]:
            return li, 0
    return None


def first_label(K):
    for li, L in enumerate(K["links"]):
        for ei, e in enumerate(L["ends"]):
            if e["kind"] == "label":
                return li, ei
    return None


def first_arc_where(K, test):
    for li, L in enumerate(K["links"]):
        for ai, a in enumerate(L["arcs"]):
            if test(a):
                return li, ai
    return None


def mix_tables(tables, idx):
    u"""混ぜ物 ``idx``(0〜5)。(変えた kind, 変えた表)か ``None``(作れなかった)。元の表は書き換えない。"""
    if idx == 0:
        kind, at = "pre", first_arc(tables["pre"])
    elif idx == 1:
        kind, at = "cal", first_arc(tables["cal"])
    elif idx == 2:
        kind, at = "lab", first_label(tables["lab"])
    elif idx == 3:
        kind, at = "lab-en", first_label(tables["lab-en"])
    elif idx == 4:
        kind = "xsd"
        at = next((i for i, e in enumerate(tables["xsd"]["elements"]) if e.get("abstract") == "false"), None)
    else:
        kind, at = "def", first_arc_where(tables["def"], lambda a: a["arcrole"] == DOMAIN_MEMBER_ARCROLE)
    if at is None:
        return None
    T = copy.deepcopy(tables[kind])
    if idx in (0, 5):
        li, ai = at
        del T["links"][li]["arcs"][ai]
    elif idx == 1:
        li, ai = at
        a = T["links"][li]["arcs"][ai]
        w = a["attrs"].get("weight")
        if w not in ("1", "-1"):
            return None
        a["attrs"]["weight"] = "-1" if w == "1" else "1"
    elif idx in (2, 3):
        li, ei = at
        T["links"][li]["ends"][ei]["text"] += u"X"
    else:
        e = T["elements"][at]
        p = e.get(XSD_KEY_PERIOD)
        if p not in ("duration", "instant"):
            return None
        e[XSD_KEY_PERIOD] = "instant" if p == "duration" else "duration"
    return kind, T


# ======================================================================================================
# 比べる
def read_table_rows(path):
    u"""CSV を csv として読む。見出しの行を含めた行(字の組)を file の順のまま。file が無ければ ``[]``。"""
    if not os.path.isfile(path):
        return []
    csv.field_size_limit(2 ** 31 - 1)
    with io.open(path, encoding="utf-8", newline="") as fh:
        return [tuple(r) for r in csv.reader(fh)]


def canon_rows(rows):
    u"""並びが道具の中で決まらない書き出しの比べ用の形: 見出しの行・同じ先頭の欄(ラベル)の行の並び(ラベルの順)はそのまま、同じ先頭の欄が続く行の中だけ並べ替える。"""
    if not rows:
        return []
    out = [rows[0]]
    i = 1
    while i < len(rows):
        j = i
        while j < len(rows) and rows[j][:1] == rows[i][:1]:
            j += 1
        out.extend(sorted(rows[i:j]))
        i = j
    return out


def output_same(key, a, b):
    u"""書き出し 1 つが同じか。``NEED_ROWS`` の書き出しは、どちらかの行が 1 以下なら同じとしない。``UNORDERED_OUTPUTS`` は同じ先頭の欄の行の中の並びを問わない。"""
    if key in NEED_ROWS and (len(a) <= 1 or len(b) <= 1):
        return False
    if key in UNORDERED_OUTPUTS:
        return canon_rows(a) == canon_rows(b)
    return a == b


def outputs_same(a, b):
    return od((k, output_same(k, a[k], b[k])) for k in OUTPUT_KEYS)


def csv_paths(workdir, tag):
    return od([("facts", os.path.join(workdir, tag + "_facts.csv"))] + [(k, os.path.join(workdir, u"%s_%d.csv" % (tag, i))) for i, k in enumerate(OUTPUT_KEYS)])


def command_a(tool, zip_path, paths):
    u"""掛け方 A(封 §1 の字のとおり)。"""
    exe = os.path.join(tool, V.EXE_REL)
    return [exe, "--plugins", PLUGINS, "--disclosureSystem", YEAR, "-f", zip_path, "--validate", "--facts", paths["facts"], "--factListCols", FACT_COLS,
            "--concepts", paths[OUTPUT_KEYS[0]], "--pre", paths[OUTPUT_KEYS[2]], "--cal", paths[OUTPUT_KEYS[3]], "--dim", paths[OUTPUT_KEYS[4]], "--roleTypes", paths[OUTPUT_KEYS[1]],
            "--viewArcrole", CONCEPT_LABEL_ARCROLE, "--viewFile", paths[OUTPUT_KEYS[5]], "--relationshipCols", "Name"]


def command_b(tool, zip_path, paths):
    u"""掛け方 B(封 §1 の字のとおり。``--validate`` は付けない)。"""
    exe = os.path.join(tool, V.EXE_REL)
    return [exe, "--plugins", PLUGINS, "--disclosureSystem", YEAR, "-f", zip_path, "--viewArcrole", GENERAL_SPECIAL_ARCROLE, "--viewFile", paths[OUTPUT_KEYS[6]], "--relationshipCols", "Name"]


def run_package(tool, zip_path, workdir, tag, runner=None):
    u"""包み 1 つに掛け方 A・B を 1 回ずつ。(A の 1 回分の数, 書き出し 7 つの行, fact の行の並び)。"""
    runner = runner or V.exec_cmd
    paths = csv_paths(workdir, tag)
    text_a, to_a = runner(SEED_PREFIX + command_a(tool, zip_path, paths), TIMEOUT_SEC)
    runner(SEED_PREFIX + command_b(tool, zip_path, paths), TIMEOUT_SEC)
    one = V.count_one(text_a, to_a)
    outs = od((k, read_table_rows(paths[k])) for k in OUTPUT_KEYS)
    return one, outs, B.read_rows(paths["facts"])


def package_with(entries, names, new_files):
    u"""元の包みの PublicDoc の ``.xsd`` と linkbase 5 つを ``new_files``(kind → bytes)で置き換えた包み。ほかの file は元のまま。"""
    by_name = dict((names[k], new_files[k]) for k in new_files)
    out = []
    for info, data in entries:
        out.append((info, by_name[info.filename] if info.filename in by_name else data))
    return out


def table_counts(tables):
    u"""表の数(§2-3): 表 S の要素の宣言の数・表 K の kind ごとの link・端・arc・ラベル。"""
    out = od([(u"要素の宣言", len(tables["xsd"]["elements"]) if tables else 0)])
    for k in FILE_KINDS[1:]:
        K = tables[k] if tables else None
        out[k] = od([(u"link", len(K["links"]) if K else 0), (u"端", sum(len(L["ends"]) for L in K["links"]) if K else 0),
                     (u"arc", sum(len(L["arcs"]) for L in K["links"]) if K else 0), (u"ラベルの数", sum(1 for L in K["links"] for e in L["ends"] if e["kind"] == "label") if K else 0)])
    return out


def empty_mixes(mixtures):
    return [od([(u"種類", k), (u"作った", False), (u"違いを見つけた", False), (u"鳴り方が違う", False)]) for k in MIX_KINDS] if mixtures else []


def process_doc(tool, zip_path, tmp_root=None, runner=None, mixtures=False):
    u"""書類 1 本。書類ごとの数。元の包みと組み直した包みを同じ掛け方で 1 回ずつ(掛け方 A・B)。"""
    entries = B.load_package(zip_path)
    rec = od([(u"断った", False), (u"断った理由", u"")])
    d = tempfile.mkdtemp(prefix="xt0_", dir=tmp_root)
    try:
        orig_zip = os.path.join(d, "orig.zip")
        B.write_package(entries, orig_zip)
        orig, orig_outs, orig_facts = run_package(tool, orig_zip, d, "orig", runner)
        rec[u"元の書き出しの行の数"] = od((k, len(orig_outs[k])) for k in OUTPUT_KEYS)
        rec[u"元の fact の行の数"] = len(orig_facts)
        rec[u"元の 1 回"] = orig
        tables = names = new_files = None
        try:
            found = find_files(entries)
            names = od((k, found[k][0]) for k in FILE_KINDS)
            tables = strip_tables(od((k, found[k][1]) for k in FILE_KINDS))
            new_files = build_tables(tables)
        except Decline as exc:
            rec[u"断った"], rec[u"断った理由"] = True, exc.reason
        except Exception:                                      # noqa: BLE001
            rec[u"断った"], rec[u"断った理由"] = True, u"例外"
        if rec[u"断った"]:
            rec[u"表の数"] = table_counts(None)
            rec[u"字が同じ"] = od((k, False) for k in FILE_KINDS)
            rec[u"組み直しの書き出しの行の数"] = None
            rec[u"組み直しの fact の行の数"] = None
            rec[u"組み直しの 1 回"] = None
            rec[u"書き出しが同じ"] = od((k, False) for k in OUTPUT_KEYS)
            rec[u"タクソノミが同じ"] = rec[u"fact が同じ"] = rec[u"鳴り方が同じ"] = rec[u"全部同じ"] = False
            rec[u"混ぜ物"] = empty_mixes(mixtures)
            return rec
        rec[u"表の数"] = table_counts(tables)
        orig_by = dict((info.filename, data) for info, data in entries)
        rec[u"字が同じ"] = od((k, new_files[k] == orig_by[names[k]]) for k in FILE_KINDS)
        new_zip = os.path.join(d, "new.zip")
        B.write_package(package_with(entries, names, new_files), new_zip)
        new, new_outs, new_facts = run_package(tool, new_zip, d, "new", runner)
        rec[u"組み直しの書き出しの行の数"] = od((k, len(new_outs[k])) for k in OUTPUT_KEYS)
        rec[u"組み直しの fact の行の数"] = len(new_facts)
        rec[u"組み直しの 1 回"] = new
        compare_into(rec, orig_outs, orig_facts, orig, new_outs, new_facts, new)
        mixes = empty_mixes(mixtures)
        for i, item in enumerate(mixes):
            m = None
            try:
                m = mix_tables(tables, i)
            except Exception:                                  # noqa: BLE001
                m = None
            if m is None:
                continue
            kind, T = m
            try:
                files2 = od(new_files)
                files2[kind] = (build_xsd(T) if kind == "xsd" else build_linkbase(T)).encode("utf-8")
            except Exception:                                  # noqa: BLE001
                continue
            mz = os.path.join(d, "mix%d.zip" % i)
            B.write_package(package_with(entries, names, files2), mz)
            mone, mouts, mfacts = run_package(tool, mz, d, "mix%d" % i, runner)
            item[u"作った"] = True
            tax = all(outputs_same(orig_outs, mouts).values())
            item[u"違いを見つけた"] = not (tax and B.facts_same(orig_facts, mfacts))
            item[u"鳴り方が違う"] = not B.sounds_same(orig, mone)
        rec[u"混ぜ物"] = mixes
        return rec
    finally:
        shutil.rmtree(d, ignore_errors=True)


def compare_into(rec, orig_outs, orig_facts, orig, new_outs, new_facts, new):
    same = outputs_same(orig_outs, new_outs)
    rec[u"書き出しが同じ"] = same
    rec[u"タクソノミが同じ"] = all(same.values())
    rec[u"fact が同じ"] = B.facts_same(orig_facts, new_facts)
    rec[u"鳴り方が同じ"] = B.sounds_same(orig, new)
    rec[u"全部同じ"] = rec[u"タクソノミが同じ"] and rec[u"fact が同じ"]


# ======================================================================================================
# 数える(封 §2)
def group_totals(entries):
    u"""書類ごとの数の並び → §2 の 1〜3。"""
    cls = od((c, 0) for c in V.CLASSES)
    declined = same_all = same_tax = same_facts = same_sound = low_concepts = 0
    reasons = collections.Counter()
    same_out = od((k, 0) for k in OUTPUT_KEYS)
    same_file = od((k, 0) for k in FILE_KINDS)
    rows = od((k, 0) for k in OUTPUT_KEYS)
    tabs = od([(u"要素の宣言", 0)] + [(k, od([(u"link", 0), (u"端", 0), (u"arc", 0), (u"ラベルの数", 0)])) for k in FILE_KINDS[1:]])
    for e in entries:
        if e[u"断った"]:
            declined += 1
            reasons[e[u"断った理由"]] += 1
        else:
            cls[e[u"組み直しの 1 回"][u"類"]] += 1
        same_all += 1 if e[u"全部同じ"] else 0
        same_tax += 1 if e[u"タクソノミが同じ"] else 0
        same_facts += 1 if e[u"fact が同じ"] else 0
        same_sound += 1 if e[u"鳴り方が同じ"] else 0
        low_concepts += 1 if e[u"元の書き出しの行の数"][OUTPUT_KEYS[0]] <= 1 else 0
        for k in OUTPUT_KEYS:
            same_out[k] += 1 if e[u"書き出しが同じ"][k] else 0
            rows[k] += e[u"元の書き出しの行の数"][k]
        for k in FILE_KINDS:
            same_file[k] += 1 if e[u"字が同じ"][k] else 0
        tabs[u"要素の宣言"] += e[u"表の数"][u"要素の宣言"]
        for k in FILE_KINDS[1:]:
            for f in (u"link", u"端", u"arc", u"ラベルの数"):
                tabs[k][f] += e[u"表の数"][k][f]
    return od([
        (u"書類", len(entries)), (u"断った書類", declined), (u"断った理由ごと", od(sorted(reasons.items()))), (u"全部同じ書類", same_all), (u"タクソノミが同じ書類", same_tax),
        (u"fact が同じ書類", same_facts), (u"鳴り方が同じ書類", same_sound), (u"書き出しごとに同じ書類", same_out), (u"組み直した包みの 1 回の類ごと", cls),
        (u"字が同じ file", od([(u"種類ごと", same_file), (u"合計", sum(same_file.values())), (u"分母", len(entries) * len(FILE_KINDS))])),
        (u"表の数の合計", tabs), (u"元の書き出しの行の数の合計", rows), (u"元の概念の行が 1 以下の書類", low_concepts)])


def mix_totals(per_doc):
    made = found = sound = 0
    for e in per_doc:
        for m in e[u"混ぜ物"]:
            if m[u"作った"]:
                made += 1
                found += 1 if m[u"違いを見つけた"] else 0
                sound += 1 if m[u"鳴り方が違う"] else 0
    return od([(u"混ぜ物の数", sum(len(e[u"混ぜ物"]) for e in per_doc)), (u"作れた数", made), (u"違いを見つけた数", found), (u"鳴り方が違う数", sound)])


def mix_kinds_totals(per_doc):
    u"""混ぜ物の種類ごとの (作れた・違いを見つけた・鳴り方が違う)。"""
    out = od()
    for i, k in enumerate(MIX_KINDS):
        items = [e[u"混ぜ物"][i] for e in per_doc if len(e[u"混ぜ物"]) > i]
        out[k] = od([(u"作れた", sum(1 for m in items if m[u"作った"])), (u"違いを見つけた", sum(1 for m in items if m[u"作った"] and m[u"違いを見つけた"])),
                     (u"鳴り方が違う", sum(1 for m in items if m[u"作った"] and m[u"鳴り方が違う"]))])
    return out


def totals_of(per_doc, dev_count=DEV_COUNT):
    dev, prod = per_doc[:dev_count], per_doc[dev_count:]
    return od([(u"開発の 5 本", group_totals(dev)), (u"本番だけの %d 本" % (len(per_doc) - dev_count), group_totals(prod)), (u"全部", group_totals(per_doc)),
               (u"混ぜ物", mix_totals(dev)), (u"混ぜ物の種類ごと", mix_kinds_totals(dev))])


def judged(tot, n=DOCS_WANT):
    u"""封 §4 の判定に要る数(当たり・外れは書かない)。"""
    prod = tot[[k for k in tot if k.startswith(u"本番だけの")][0]]
    fl = prod[u"字が同じ file"]
    mx = tot[u"混ぜ物"]
    return od([
        (u"XT0-1 全部同じ書類", od([(u"書類", prod[u"全部同じ書類"]), (u"分母", prod[u"書類"])])),
        (u"XT0-2 断った書類", od([(u"書類", prod[u"断った書類"]), (u"分母", prod[u"書類"])])),
        (u"XT0-3 鳴り方が同じ書類", od([(u"書類", prod[u"鳴り方が同じ書類"]), (u"分母", prod[u"書類"])])),
        (u"XT0-4 字が同じ file", od([(u"file", fl[u"合計"]), (u"分母", fl[u"分母"])])),
        (u"XT0-5 作れた混ぜ物", od([(u"個", mx[u"作れた数"]), (u"分母", mx[u"混ぜ物の数"])])),
        (u"XT0-6 作れた混ぜ物のうち違いを見つけたもの", od([(u"個", mx[u"違いを見つけた数"]), (u"分母", mx[u"作れた数"])])),
        (u"XT0-7 作れた混ぜ物のうち鳴り方が元と違うもの", od([(u"個", mx[u"鳴り方が違う数"]), (u"分母", mx[u"作れた数"])]))])


# ======================================================================================================
# 道具の確かめ・記録
def check_tool(tool, runner=None, sha_reader=sha256_file, want_version=TOOL_VERSION, want_sha=SHA_P):
    u"""実行 file が在り、版・ModelValue.py の sha256 が封の字と同じであること。違えば止まる。道具の情報を返す。"""
    return B.check_tool(tool, runner, sha_reader, want_version, want_sha)


def dev_docs(docs_dir, count=DEV_COUNT):
    u"""置き場の並びの頭から ``count`` 本だけを選ぶ(便 XB0 の関数。残りの zip は開かない)。[(stem, path, xsd の名の並び)]。"""
    return B.dev_docs(docs_dir, count)


def secret_of(entries_list):
    u"""記録に書かないものの集まり(要素の名・ラベルの字)。書類の包みから読むだけ。"""
    elems, labels = set(), set()
    for entries in entries_list:
        try:
            tables = strip_tables(od((k, v[1]) for k, v in find_files(entries).items()))
        except Exception:                                      # noqa: BLE001
            continue
        for e in tables["xsd"]["elements"]:
            elems.add(e["name"])
        for k in ("lab", "lab-en"):
            for L in tables[k]["links"]:
                for e in L["ends"]:
                    if e["kind"] == "label" and len(e["text"]) >= 5:
                        labels.add(e["text"])
    return elems, labels


def build_record(tool_p, docs_dir=None, want=DOCS_WANT, runner=None, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_sha=SHA_P, dev_count=DEV_COUNT):
    u"""道具を確かめてから、書類を 1 本ずつ掛ける。(記録, secret)。書かない。"""
    docs = W.select_docs(docs_dir or DOCS_DIR, want)
    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)
    per_doc = []
    elems, labels = set(), set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        r = process_doc(tool_p, p, tmp_root, runner, mixtures=(n <= dev_count))
        per_doc.append(od([(u"番号", n)] + list(r.items())))
        el, lb = secret_of([B.load_package(p)])
        elems |= el
        labels |= lb
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    secret = (labels, elems, [d[0] for d in docs], ecodes, set())
    return assemble(per_doc, W.order_sha256([d[0] for d in docs]), info, dev_count), secret


def assemble(per_doc, order_sha, info, dev_count=DEV_COUNT):
    tot = totals_of(per_doc, dev_count)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XT0(受理済みの有報の提出者別タクソノミ(xsd の file と linkbase 5 つ)を、中身を読んだ表から自前の部品で組み直すと、公開の道具が読むタクソノミ・fact・検査の鳴り方は元と同じになるか)(0 USD・engine は読まない)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"書類の本数", len(per_doc)), (u"書類の file 名の並びの sha256", order_sha), (u"開発の 5 本の番号", list(range(1, dev_count + 1))),
        (u"道具の版", info[u"版"]), (u"道具 P の ModelValue.py の sha256", info[u"ModelValue.py の sha256"]), (u"道具 P の package の一覧の sha256", info[u"package の一覧の sha256"]),
        (u"Python の版(道具 P)", info[u"Python の版"]), (u"規則の年", YEAR), (u"混ぜ物の種類", list(MIX_KINDS)), (u"時間の上限(秒)", TIMEOUT_SEC)])
    rec[u"書類"] = per_doc
    rec[u"集計"] = tot
    rec[u"予測の判定に要る数(XT0-1〜XT0-7。当たり・外れは結果の文書で)"] = judged(tot, len(per_doc))
    rec[u"限界"] = list(LIMITS)
    return rec


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(docID・EDINET コード・file の名・要素の名・ラベルの字・role の URI・指摘の行の本文)が無いか。在れば止める。"""
    V.check_clean(rec, text, secret)                   # 欄・字の形・docID・EDINET コード・要素の名・ラベルの字・file の名の形・指摘の行の本文
    if "http://" in text or "https://" in text:
        raise Stop(u"**記録に URI の形の字が在る。止める**")


def verify_record(rec, text=None, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する(道具は呼ばない・掛け直さない)。違えば止まる。"""
    docs = rec.get(u"書類")
    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"書類の本数"] != want:
        raise Stop(u"**記録の書類が 67 本でない。止める**")
    for i, d in enumerate(docs, 1):
        if d.get(u"番号") != i:
            raise Stop(u"**記録の書類の番号が違う。止める**")
        for k in (u"断った", u"断った理由", u"表の数", u"元の書き出しの行の数", u"元の fact の行の数", u"元の 1 回", u"字が同じ", u"書き出しが同じ", u"タクソノミが同じ", u"fact が同じ", u"鳴り方が同じ", u"全部同じ", u"混ぜ物", u"組み直しの 1 回"):
            if k not in d:
                raise Stop(u"**記録の書類の形が違う。止める**")
        if d[u"断った"] != (d[u"組み直しの 1 回"] is None) or (d[u"断った"] and (d[u"全部同じ"] or d[u"タクソノミが同じ"] or d[u"fact が同じ"] or d[u"鳴り方が同じ"] or any(d[u"字が同じ"].values()))) or (not d[u"断った"] and d[u"断った理由"]):
            raise Stop(u"**断った書類の形が違う。止める**")
        if d[u"全部同じ"] != (d[u"タクソノミが同じ"] and d[u"fact が同じ"]) or d[u"タクソノミが同じ"] != all(d[u"書き出しが同じ"].values()):
            raise Stop(u"**全部同じ・タクソノミが同じの導き方が違う。止める**")
        if list(d[u"字が同じ"]) != list(FILE_KINDS) or list(d[u"書き出しが同じ"]) != list(OUTPUT_KEYS) or list(d[u"元の書き出しの行の数"]) != list(OUTPUT_KEYS):
            raise Stop(u"**字が同じ・書き出しの欄が違う。止める**")
        if d[u"元の 1 回"][u"類"] not in V.CLASSES or (d[u"組み直しの 1 回"] is not None and d[u"組み直しの 1 回"][u"類"] not in V.CLASSES):
            raise Stop(u"**1 回の類が違う。止める**")
        if len(d[u"混ぜ物"]) != (len(MIX_KINDS) if i <= dev_count else 0) or [m[u"種類"] for m in d[u"混ぜ物"]] != (list(MIX_KINDS) if i <= dev_count else []):
            raise Stop(u"**混ぜ物の形が違う。止める**")
        for m in d[u"混ぜ物"]:
            if not m[u"作った"] and (m[u"違いを見つけた"] or m[u"鳴り方が違う"]):
                raise Stop(u"**作れなかった混ぜ物の形が違う。止める**")
    tot = totals_of(docs, dev_count)
    if dumps(tot) != dumps(rec[u"集計"]) or dumps(judged(tot, len(docs))) != dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):
        raise Stop(u"**記録の合計が書類ごとの数と合わない。止める**")
    check_clean(rec, text if text is not None else dumps(rec))


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に検査する。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_exclusive(path, text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_clean(rec, back, secret)
    except SystemExit:
        os.remove(path)
        raise


def run(tool_p, root=ROOT, docs=None, out=None, want=DOCS_WANT, runner=None, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_sha=SHA_P, say=print, dev_count=DEV_COUNT):
    rec, secret = build_record(tool_p, docs, want, runner, sha_reader, tmp_root, want_version, want_sha, dev_count)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(書類 %d)" % (os.path.basename(out), rec[u"材料"][u"書類の本数"]))
    return rec


def check(root=ROOT, rec_path=None, say=print, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する。置き場も道具も読まない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    verify_record(rec, text, want, dev_count)
    say(u"--check: 記録の形・合計・禁止のものの検査は通った(書類 %d)" % len(rec[u"書類"]))
    return rec


def dev_run(tool_p, docs_dir=None, runner=None, tmp_root=None, say=print):
    u"""開発の 5 本だけ(記録は書かない)。(書類ごとの数の並び)。"""
    docs = dev_docs(docs_dir or DOCS_DIR, DEV_COUNT)
    check_tool(tool_p, runner)
    per = []
    t_all = time.time()
    for n, (_s, p, _x) in enumerate(docs, 1):
        t0 = time.time()
        r = process_doc(tool_p, p, tmp_root, runner, mixtures=True)
        per.append(od([(u"番号", n)] + list(r.items())))
        say(u"doc %d(%.0f 秒): 断った=%s(%s) 全部同じ=%s タクソノミ=%s fact=%s 鳴り方=%s 書き出し=%s 字が同じ=%s 混ぜ物=%s" % (
            n, time.time() - t0, r[u"断った"], r[u"断った理由"], r[u"全部同じ"], r[u"タクソノミが同じ"], r[u"fact が同じ"], r[u"鳴り方が同じ"],
            json.dumps(r[u"書き出しが同じ"], ensure_ascii=False), json.dumps(r[u"字が同じ"], ensure_ascii=False), [(m[u"種類"], m[u"作った"], m[u"違いを見つけた"], m[u"鳴り方が違う"]) for m in r[u"混ぜ物"]]))
    say(u"開発の 5 本の合計: %.0f 秒" % (time.time() - t_all))
    return per


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="記録の形・合計・禁止のものを検査する。道具は呼ばない")
    ap.add_argument("--dev", action="store_true", help="開発の 5 本だけ掛ける。記録は書かない")
    ap.add_argument("--tool-p", default=None, help="道具 P(1 行の直し)の venv の場所")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="書類の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root)
        return
    if not a.tool_p:
        raise Stop(u"**--tool-p が要る。止める**")
    if a.dev:
        dev_run(a.tool_p, docs_dir=a.docs)
        return
    run(a.tool_p, root=a.root, docs=a.docs)


if __name__ == "__main__":
    main()
