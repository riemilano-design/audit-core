# -*- coding: utf-8 -*-
u"""封 docs/XBRL_INLINE_BUILD_SEAL_2026-11-21.md(XB0 ― 受理済みの有報の inline XBRL を、タグを剥がした本文と fact の表から自前の部品で組み直すと、公開の道具が読む fact と検査の鳴り方は元と同じになるか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。** engine(``core/``・``adapters/``)は読まない・変えない。書類の選び方・符号の読み方・1 回の類は前の便の script の関数を importlib で呼ぶ(写さない)。

    python3 measure/xbrl_inline_build_2026-11-21.py --tool-p <venv の場所>           # 道具を確かめて 67 本(+ 開発の 5 本の混ぜ物 15 個)を掛け、記録を書く(本番は 1 回)
    python3 measure/xbrl_inline_build_2026-11-21.py --check                         # 記録の形・合計・禁止のものを検査する。道具は呼ばない・掛け直さない
    python3 measure/xbrl_inline_build_2026-11-21.py --dev --tool-p <venv の場所>     # 開発の 5 本だけ(置き場の並びの頭の 5 本の zip だけ開く)。記録は書かない

組む部品(``build_text``)は **素の本文・表 F・表 H だけ** を引数に取る。元の ``.htm`` の字も元の包みも読まない。置き場の zip を読む所は ``load_package`` の 1 か所。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 表 F の 1 行: ``kind``(``nonFraction``・``nonNumeric``・``footnote``)・``self``(中身の無い自己閉じの形か)・``start``/``end``(素の本文の中の位置)・``parent``(入れ子の親の番号、無ければ -1)・``attrs``(名 → 値の辞書。並びの順は持たない)。
  入れ子の親と自己閉じの形は元の字から読んだ「どこにタグが付くか」の答えの一部として渡す(位置だけでは同じ位置の入れ子の順が決まらないため)。属性の値は元の字のまま(実体参照を直さない)。
- 表 H: ``pos``(素の本文の中の位置)・``before``(頭の部より前に開いた表 F の行の数)・``sections``(頭の部の子の並び)・``hidden``・``references``・``resources``(``roleRef`` と ``arcroleRef`` を含む。封 §1 の列挙に無いが、実書類の頭の部の子として在るので既知の子に数える)。
  ``ix:header`` の元の字は持たない。
- 知らない形(断る): 知らない ``ix:`` の要素・知らない属性・自己閉じの ``ix:header``・2 つ目の ``ix:header``・入れ子の頭の部・頭の部の中の知らない子・知らない文字の符号化・タグの字が strict な形に当たらないもの。
  既知の属性: ``nonFraction`` と ``nonNumeric`` は封 §0 の 11 個、``footnote`` は ``footnoteID``・``footnoteLinkRole``・``arcrole``・``footnoteRole``・``xml:lang``・``id``(封 §0 は ``footnote`` の属性を見ていない。開発の 5 本で在った 5 つと inline XBRL の規格の ``id``)。
- 組み方の決め(開発の 5 本で決めた。本番の前にここへ留める): 属性は ``ATTR_ORDER`` の並び(開発の 5 本のうち 4 本の元の並びの多数に合わせた: ``name contextRef unitRef decimals scale format sign footnoteRefs id escape xsi:nil``。1 本は別の並びで、その本の字は同じにならない)・引用符は ``"``(値に ``"`` が在れば ``'``、両方在れば断る)・自己閉じは `` />``・頭の部は子を 1 行ずつ ``\\n`` で区切り字下げ無し・
  頭の部の子の並びは ``sections`` の並び・``resources`` の中は表 H の並び。
- 組む前の位置の順: 表 F の並びは開きタグの順。混ぜ物の「file の並び」は PublicDoc の ``.htm`` の名の昇順。
- 「中身の字が 0 だけ」: 前後の空白を落とした字が空でなく、``0`` と ``０`` だけでできているもの。
- 比べ方の ``fact が同じ``: CSV を csv として読み、最初の 1 行(見出し)を除いた行(全部の欄の字の組)を並べ替えた並びが同じで、行が 0 でない。
- 1 回の時間の上限は 600 秒。規則の年は ``EDINET-2026`` だけ。
- ``ix:header`` を持つか: ``<ix:header`` の字が在るか(断った書類の file でも同じ数え方)。タグの数: file 全体の ``<ix:nonFraction``・``<ix:nonNumeric``・``<ix:footnote`` の字の数(封 §0 と同じ数え方)。
"""
from __future__ import print_function

import argparse
import collections
import csv
import glob
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

VALIDATE_NAME = "_xb0_edinet_validate_2026_11_21"


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


V = _load_sibling(VALIDATE_NAME, "xbrl_edinet_validate_2026-11-21.py")
W = V.W                                            # 便 XG0 の script(便 XV0 の script が一意の名で読んだもの。Stop の型を 1 つにするため同じ object を使う)

SEAL_REL = "docs/XBRL_INLINE_BUILD_SEAL_2026-11-21.md"
SEAL_COMMIT = "9c528c49"
SCRIPT_REL = "measure/xbrl_inline_build_2026-11-21.py"
RECORD_REL = "fixtures/xbrl/cd8/inline_build_2026-11-21.json"
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
HTM_SUFFIX = ".htm"
STRIP_SUFFIX = ".xbrl"
IX_KINDS = ("nonFraction", "nonNumeric", "footnote")
MIX_KINDS = (u"抜く", u"文脈を替える", u"符号を返す")
BOUNDS = collections.OrderedDict([
    ("XB0-1", (56, None)), ("XB0-2", (None, 4)), ("XB0-3", (56, None)), ("XB0-4", (50, None)), ("XB0-5", (None, 10)), ("XB0-6", (15, None)), ("XB0-7", (None, 5))])
LIMITS = [
    u"剥がして組み直す往復で、渡す表は元の書類から作っている。タグを決める力は測っていない。",
    u"提出者別タクソノミ・マニフェスト・画像・監査報告書の包みは元のまま。専用の道具の仕事のうち、タクソノミを作る所は測っていない。",
    u"素の本文は元の書類の本文からタグを除いたもので、原稿(Word など)ではない。根の名前空間の宣言も元の字のまま。",
    u"読み戻しと検査は公開の道具 1 つ(道具 P。司令塔が 1 行を直したもの)。EDINET の本物の検査とは照らしていない。",
    u"組み方は開発の 5 本で決めた。67 本は無作為ではない。有報だけ。",
    u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]

Stop = W.Stop
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps

# ---- 属性(既知のものと、組むときの並び。並びの順は元の字から持たない)
NUM_ATTRS = ("name", "contextRef", "unitRef", "decimals", "scale", "format", "sign", "footnoteRefs", "id", "escape", "xsi:nil")
ATTR_ORDER = {"nonFraction": NUM_ATTRS, "nonNumeric": NUM_ATTRS, "footnote": ("footnoteID", "footnoteLinkRole", "arcrole", "footnoteRole", "xml:lang", "id")}
REF_ATTRS = {"link:schemaRef": ("xlink:type", "xlink:href"), "link:roleRef": ("roleURI", "xlink:type", "xlink:href"), "link:arcroleRef": ("arcroleURI", "xlink:type", "xlink:href")}
HEADER_SECTIONS = ("ix:hidden", "ix:references", "ix:resources")


class Decline(Exception):
    u"""知らない形に当たった(断る)。``reason`` は固定の字(材料の字を入れない)。"""

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason


# ======================================================================================================
# 置き場の zip を読む所(1 か所)
def load_package(zip_path):
    u"""元の包み: 名が ``.xbrl`` で終わる file を除いた [(ZipInfo, bytes)] を zip の並びで。置き場の zip は開くだけ。"""
    out = []
    with zipfile.ZipFile(zip_path) as zi:
        for info in zi.infolist():
            if not info.filename.endswith(STRIP_SUFFIX):
                out.append((info, zi.read(info.filename)))
    return out


def write_package(entries, path):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zo:
        for info, data in entries:
            zo.writestr(info, data)


def is_public_htm(name):
    return name.startswith(PUBLICDOC) and name.endswith(HTM_SUFFIX)


# ======================================================================================================
# 剥がす
IX_ANY_RE = re.compile(r"<(?:/)?ix:")
ATTR_PIECE = r"""\s+[^\s=<>/"']+\s*=\s*(?:"[^"]*"|'[^']*')"""
IX_TAG_RE = re.compile(r"<(/?)(ix:[A-Za-z]+)((?:" + ATTR_PIECE + r")*)\s*(/?)>")
ATTR_RE = re.compile(r"""\s+([^\s=<>/"']+)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
GEN_TAG_RE = re.compile(r"<(/?)([A-Za-z][\w.\-]*(?::[\w.\-]+)?)((?:" + ATTR_PIECE + r")*)\s*(/?)>")


def parse_attrs(s, known):
    out = {}
    for m in ATTR_RE.finditer(s):
        k = m.group(1)
        if k in out:
            raise Decline(u"属性の名が重なる")
        if k not in known:
            raise Decline(u"知らない属性")
        out[k] = m.group(2) if m.group(2) is not None else m.group(3)
    return dict(sorted(out.items()))


def count_ix_tags(text):
    u"""file 全体の 3 種類の開きタグの字の数(封 §0 と同じ数え方)。"""
    return od((k, len(re.findall(r"<ix:%s\b" % k, text))) for k in IX_KINDS)


def has_header(text):
    return "<ix:header" in text


def strip_text(text):
    u"""元の ``.htm`` の字 → (素の本文, 表 F, 表 H または None)。知らない形は ``Decline``。"""
    toks = list(IX_TAG_RE.finditer(text))
    if len(IX_ANY_RE.findall(text)) != len(toks):
        raise Decline(u"ix のタグの字が知らない形")
    plain = []
    plen = 0
    pos = 0
    stack = []
    F = []
    H = None
    hdr_open = None
    for m in toks:
        closing, name, attr_s, selfc = m.group(1) == "/", m.group(2), m.group(3), m.group(4) == "/"
        if hdr_open is not None:
            if name == "ix:header":
                if not closing or selfc:
                    raise Decline(u"入れ子の頭の部")
                inner = text[hdr_open.end():m.start()]
                H = parse_header(inner)
                H["pos"] = plen
                H["before"] = len(F)
                hdr_open = None
                pos = m.end()
            continue
        seg = text[pos:m.start()]
        plain.append(seg)
        plen += len(seg)
        pos = m.end()
        if name == "ix:header":
            if closing or selfc:
                raise Decline(u"頭の部の形が知らない形")
            if H is not None or stack:
                raise Decline(u"2 つ目の頭の部か入れ子の頭の部")
            if attr_s.strip():
                raise Decline(u"頭の部に属性")
            hdr_open = m
            continue
        kind = name[3:]
        if kind not in IX_KINDS:
            raise Decline(u"知らない ix の要素")
        if closing:
            if attr_s.strip() or selfc or not stack or F[stack[-1]]["kind"] != kind:
                raise Decline(u"閉じタグが合わない")
            F[stack[-1]]["end"] = plen
            stack.pop()
            continue
        e = od([("kind", kind), ("self", selfc), ("start", plen), ("end", plen), ("parent", stack[-1] if stack else -1), ("attrs", parse_attrs(attr_s, ATTR_ORDER[kind]))])
        F.append(e)
        if not selfc:
            stack.append(len(F) - 1)
    if hdr_open is not None or stack:
        raise Decline(u"閉じていない")
    plain.append(text[pos:])
    return u"".join(plain), F, H


# ---- 頭の部を読む
def parse_tree(s):
    u"""頭の部の中身の字 → 子の並び。1 つの node は dict(name, attrs, self, children, text)。タグ以外の ``<`` は断る。"""
    root = od([("name", None), ("attrs", {}), ("self", False), ("children", []), ("text", u"")])
    stack = [root]
    pos = 0
    texts = {id(root): []}
    for m in GEN_TAG_RE.finditer(s):
        piece = s[pos:m.start()]
        if "<" in piece:
            raise Decline(u"頭の部に知らない形の字")
        texts[id(stack[-1])].append(piece)
        pos = m.end()
        closing, name, attr_s, selfc = m.group(1) == "/", m.group(2), m.group(3), m.group(4) == "/"
        if closing:
            if attr_s.strip() or selfc or len(stack) < 2 or stack[-1]["name"] != name:
                raise Decline(u"頭の部の閉じタグが合わない")
            stack.pop()
            continue
        attrs = {}
        for a in ATTR_RE.finditer(attr_s):
            if a.group(1) in attrs:
                raise Decline(u"属性の名が重なる")
            attrs[a.group(1)] = a.group(2) if a.group(2) is not None else a.group(3)
        node = od([("name", name), ("attrs", dict(sorted(attrs.items()))), ("self", selfc), ("children", []), ("text", u"")])
        stack[-1]["children"].append(node)
        texts[id(node)] = []
        if not selfc:
            stack.append(node)
    tail = s[pos:]
    if "<" in tail or len(stack) != 1:
        raise Decline(u"頭の部に知らない形の字")
    texts[id(root)].append(tail)

    def fill(n):
        n["text"] = u"".join(texts[id(n)])
        for c in n["children"]:
            fill(c)
    fill(root)
    return root


def only_ws(n):
    return not n["text"].strip()


def leaf_text(n, allowed_attrs):
    u"""子を持たない node の中身の字(属性は既知のものだけ)。"""
    if n["children"] or set(n["attrs"]) - set(allowed_attrs):
        raise Decline(u"頭の部の葉の形が知らない形")
    return n["text"]


def parse_hidden(sec):
    out = []
    for c in sec["children"]:
        kind = c["name"][3:] if c["name"] in ("ix:nonNumeric", "ix:nonFraction") else None
        if kind is None or c["children"] or set(c["attrs"]) - set(ATTR_ORDER[kind]):
            raise Decline(u"隠しの fact の形が知らない形")
        out.append(od([("kind", kind), ("self", c["self"]), ("attrs", c["attrs"]), ("text", c["text"])]))
    return out


def parse_context(n):
    if set(n["attrs"]) != {"id"} or not only_ws(n):
        raise Decline(u"文脈の形が知らない形")
    out = od([("type", "context"), ("id", n["attrs"]["id"]), ("scheme", None), ("ident", None), ("period", None), ("members", None)])
    for c in n["children"]:
        if c["name"] == "xbrli:entity" and out["ident"] is None:
            if not only_ws(c) or len(c["children"]) != 1 or c["children"][0]["name"] != "xbrli:identifier":
                raise Decline(u"文脈の提出者の形が知らない形")
            idn = c["children"][0]
            if set(idn["attrs"]) != {"scheme"}:
                raise Decline(u"文脈の提出者の形が知らない形")
            out["scheme"], out["ident"] = idn["attrs"]["scheme"], leaf_text(idn, ("scheme",))
        elif c["name"] == "xbrli:period" and out["period"] is None:
            if c["attrs"] or not only_ws(c):
                raise Decline(u"期の形が知らない形")
            ch = [(x["name"], leaf_text(x, ())) for x in c["children"]]
            names = [k for k, _v in ch]
            if names == ["xbrli:instant"] or names == ["xbrli:forever"] and ch[0][1] == u"" or names == ["xbrli:startDate", "xbrli:endDate"]:
                out["period"] = ch
            else:
                raise Decline(u"期の形が知らない形")
        elif c["name"] == "xbrli:scenario" and out["members"] is None:
            if c["attrs"] or not only_ws(c):
                raise Decline(u"軸の形が知らない形")
            mem = []
            for x in c["children"]:
                if x["name"] != "xbrldi:explicitMember":
                    raise Decline(u"知らないメンバーの形")
                mem.append((x["attrs"].get("dimension"), leaf_text(x, ("dimension",))))
                if mem[-1][0] is None:
                    raise Decline(u"メンバーに軸が無い")
            out["members"] = mem
        else:
            raise Decline(u"文脈の子が知らない形")
    if out["ident"] is None or out["period"] is None:
        raise Decline(u"文脈に提出者か期が無い")
    out["has_scenario"] = out["members"] is not None
    out["members"] = out["members"] or []
    return out


def parse_measures(n, tag):
    if n["attrs"] or not only_ws(n):
        raise Decline(u"単位の形が知らない形")
    ms = []
    for c in n["children"]:
        if c["name"] != tag:
            raise Decline(u"単位の子が知らない形")
        ms.append(leaf_text(c, ()))
    return ms


def parse_unit(n):
    if set(n["attrs"]) != {"id"} or not only_ws(n) or not n["children"]:
        raise Decline(u"単位の形が知らない形")
    out = od([("type", "unit"), ("id", n["attrs"]["id"])])
    ch = n["children"]
    if all(c["name"] == "xbrli:measure" for c in ch):
        out["measures"] = [leaf_text(c, ()) for c in ch]
        out["divide"] = None
    elif len(ch) == 1 and ch[0]["name"] == "xbrli:divide":
        d = ch[0]
        if d["attrs"] or not only_ws(d) or [c["name"] for c in d["children"]] != ["xbrli:unitNumerator", "xbrli:unitDenominator"]:
            raise Decline(u"割り算の単位の形が知らない形")
        out["measures"] = []
        out["divide"] = od([("num", parse_measures(d["children"][0], "xbrli:measure")), ("den", parse_measures(d["children"][1], "xbrli:measure"))])
    else:
        raise Decline(u"単位の子が知らない形")
    return out


def parse_header(inner):
    u"""``ix:header`` の中身の字 → 表 H(``pos``・``before`` は呼ぶ側が足す)。元の字は持たない。"""
    root = parse_tree(inner)
    if not only_ws(root):
        raise Decline(u"頭の部に字")
    H = od([("sections", []), ("hidden", []), ("references", []), ("resources", [])])
    for sec in root["children"]:
        if sec["name"] not in HEADER_SECTIONS or sec["name"] in H["sections"] or sec["attrs"] or not only_ws(sec):
            raise Decline(u"頭の部の子が知らない形")
        H["sections"].append(sec["name"])
        if sec["name"] == "ix:hidden":
            if sec["self"]:
                raise Decline(u"自己閉じの隠しの部")
            H["hidden"] = parse_hidden(sec)
        elif sec["name"] == "ix:references":
            for c in sec["children"]:
                if c["name"] != "link:schemaRef" or c["children"] or set(c["attrs"]) - set(REF_ATTRS[c["name"]]) or not only_ws(c):
                    raise Decline(u"参照の形が知らない形")
                H["references"].append(od([("tag", c["name"]), ("self", c["self"]), ("attrs", c["attrs"])]))
        else:
            for c in sec["children"]:
                if c["name"] == "xbrli:context":
                    H["resources"].append(parse_context(c))
                elif c["name"] == "xbrli:unit":
                    H["resources"].append(parse_unit(c))
                elif c["name"] in ("link:roleRef", "link:arcroleRef"):
                    if c["children"] or set(c["attrs"]) - set(REF_ATTRS[c["name"]]) or not only_ws(c):
                        raise Decline(u"roleRef の形が知らない形")
                    H["resources"].append(od([("type", "ref"), ("tag", c["name"]), ("self", c["self"]), ("attrs", c["attrs"])]))
                else:
                    raise Decline(u"resources の子が知らない形")
    return H


# ======================================================================================================
# 組む(素の本文・表 F・表 H だけを受ける)
def attr_text(attrs, order):
    unknown = set(attrs) - set(order)
    if unknown:
        raise Decline(u"知らない属性")
    parts = []
    for k in order:
        if k in attrs:
            v = attrs[k]
            if '"' not in v:
                parts.append(u' %s="%s"' % (k, v))
            elif "'" not in v:
                parts.append(u" %s='%s'" % (k, v))
            else:
                raise Decline(u"値に引用符が両方在る")
    return u"".join(parts)


def open_tag(tag, attrs, order, selfc):
    return u"<%s%s%s>" % (tag, attr_text(attrs, order), u" /" if selfc else u"")


def render_header(H):
    u"""表 H → ``ix:header`` の字。"""
    lines = [u"<ix:header>"]
    for sec in H["sections"]:
        if sec == "ix:hidden":
            lines.append(u"<ix:hidden>")
            for h in H["hidden"]:
                order = ATTR_ORDER[h["kind"]]
                if h["self"]:
                    if h["text"]:
                        raise Decline(u"自己閉じに字")
                    lines.append(open_tag("ix:" + h["kind"], h["attrs"], order, True))
                else:
                    lines.append(open_tag("ix:" + h["kind"], h["attrs"], order, False) + h["text"] + u"</ix:%s>" % h["kind"])
            lines.append(u"</ix:hidden>")
        elif sec == "ix:references":
            lines.append(u"<ix:references>")
            for r in H["references"]:
                lines.append(open_tag(r["tag"], r["attrs"], REF_ATTRS[r["tag"]], r["self"]))
            lines.append(u"</ix:references>")
        elif sec == "ix:resources":
            lines.append(u"<ix:resources>")
            for r in H["resources"]:
                if r["type"] == "ref":
                    lines.append(open_tag(r["tag"], r["attrs"], REF_ATTRS[r["tag"]], r["self"]))
                elif r["type"] == "context":
                    lines.append(u'<xbrli:context id="%s">' % r["id"])
                    lines.append(u"<xbrli:entity>")
                    lines.append(u'<xbrli:identifier scheme="%s">%s</xbrli:identifier>' % (r["scheme"], r["ident"]))
                    lines.append(u"</xbrli:entity>")
                    lines.append(u"<xbrli:period>")
                    for k, v in r["period"]:
                        lines.append(u"<%s>%s</%s>" % (k, v, k) if v != u"" else u"<%s />" % k)
                    lines.append(u"</xbrli:period>")
                    if r["has_scenario"]:
                        lines.append(u"<xbrli:scenario>")
                        for dim, val in r["members"]:
                            lines.append(u'<xbrldi:explicitMember dimension="%s">%s</xbrldi:explicitMember>' % (dim, val))
                        lines.append(u"</xbrli:scenario>")
                    lines.append(u"</xbrli:context>")
                elif r["type"] == "unit":
                    lines.append(u'<xbrli:unit id="%s">' % r["id"])
                    if r["divide"] is None:
                        for m in r["measures"]:
                            lines.append(u"<xbrli:measure>%s</xbrli:measure>" % m)
                    else:
                        lines.append(u"<xbrli:divide>")
                        lines.append(u"<xbrli:unitNumerator>")
                        for m in r["divide"]["num"]:
                            lines.append(u"<xbrli:measure>%s</xbrli:measure>" % m)
                        lines.append(u"</xbrli:unitNumerator>")
                        lines.append(u"<xbrli:unitDenominator>")
                        for m in r["divide"]["den"]:
                            lines.append(u"<xbrli:measure>%s</xbrli:measure>" % m)
                        lines.append(u"</xbrli:unitDenominator>")
                        lines.append(u"</xbrli:divide>")
                    lines.append(u"</xbrli:unit>")
                else:
                    raise Decline(u"知らない resources の子")
            lines.append(u"</ix:resources>")
        else:
            raise Decline(u"知らない頭の部の子")
    lines.append(u"</ix:header>")
    return u"\n".join(lines)


def build_text(plain, F, H):
    u"""素の本文・表 F・表 H だけから ``.htm`` の字を返す。元の ``.htm`` も元の包みも読まない。知らない形は ``Decline``。"""
    kids = collections.defaultdict(list)
    for i, e in enumerate(F):
        if e["kind"] not in ATTR_ORDER:
            raise Decline(u"知らない ix の要素")
        if not (-1 <= e["parent"] < i):
            raise Decline(u"親の番号が合わない")
        kids[e["parent"]].append(i)
    parts = []

    def emit(i):
        e = F[i]
        order = ATTR_ORDER[e["kind"]]
        if e["self"]:
            if e["start"] != e["end"] or kids.get(i):
                raise Decline(u"自己閉じの形が合わない")
            parts.append(open_tag("ix:" + e["kind"], e["attrs"], order, True))
            return
        parts.append(open_tag("ix:" + e["kind"], e["attrs"], order, False))
        cur = walk(e["start"], e["end"], kids.get(i, []))
        parts.append(plain[cur:e["end"]])
        parts.append(u"</ix:%s>" % e["kind"])

    def walk(cur, limit, ids, header=None):
        u"""``ids`` の子を ``cur`` から順に出す。返り値は出した後の位置(``limit`` までの残りは呼ぶ側が出す)。"""
        done = header is None
        for c in ids:
            if not done and c >= header["before"]:
                cur = put_header(cur, header)
                done = True
            e = F[c]
            if e["start"] < cur or e["end"] > limit or e["end"] < e["start"]:
                raise Decline(u"位置が合わない")
            parts.append(plain[cur:e["start"]])
            emit(c)
            cur = e["end"]
        if not done:
            cur = put_header(cur, header)
        return cur

    def put_header(cur, header):
        if header["pos"] < cur or header["pos"] > len(plain):
            raise Decline(u"頭の部の位置が合わない")
        parts.append(plain[cur:header["pos"]])
        parts.append(render_header(header))
        return header["pos"]

    if H is not None and not (0 <= H["before"] <= len(F)):
        raise Decline(u"頭の部の位置の番号が合わない")
    cur = walk(0, len(plain), kids.get(-1, []), H)
    parts.append(plain[cur:])
    return u"".join(parts)


# ======================================================================================================
# 混ぜ物(表 F を 1 か所だけ変える)
def copy_tables(F, H):
    return [od((k, (dict(v) if k == "attrs" else v)) for k, v in e.items()) for e in F], H


def num_pool(files):
    u"""``files`` = [(名, plain, F, H)] の file の並び → ``xsi:nil`` の無い ``nonFraction`` の (file の番号, 表 F の番号) を順に。"""
    out = []
    for fi, (_n, _p, F, _h) in enumerate(files):
        for i, e in enumerate(F):
            if e["kind"] == "nonFraction" and "xsi:nil" not in e["attrs"]:
                out.append((fi, i))
    return out


def is_zero_content(s):
    t = s.strip()
    return bool(t) and set(t) <= set(u"0０")


def remove_entry(F, H, i):
    u"""表 F の i 行を除く(子が在れば断る)。残りの親の番号・頭の部の ``before`` を直す。"""
    if any(e["parent"] == i for e in F):
        raise Decline(u"子の在る行は除けない")
    out = []
    for j, e in enumerate(F):
        if j == i:
            continue
        e2 = od((k, (dict(v) if k == "attrs" else v)) for k, v in e.items())
        if e2["parent"] > i:
            e2["parent"] -= 1
        out.append(e2)
    H2 = None
    if H is not None:
        H2 = od(H.items())
        if H2["before"] > i:
            H2["before"] -= 1
    return out, H2


def mix_target(files, kind):
    u"""混ぜ物 1 つの当て先 (file の番号, 表 F の番号)。無ければ ``None``。"""
    pool = num_pool(files)
    if not pool:
        return None
    if kind != u"符号を返す":
        return pool[0]
    for fi, i in pool:
        e = files[fi][2][i]
        if not is_zero_content(files[fi][1][e["start"]:e["end"]]):
            return fi, i
    return None


def mix_tables(files, kind):
    u"""``(file の番号, 変えた F, H)`` か ``None``。files = [(名, plain, F, H)]。"""
    tgt = mix_target(files, kind)
    if tgt is None:
        return None
    fi, i = tgt
    _n, _p, F, H = files[fi]
    if kind == u"抜く":
        F2, H2 = remove_entry(F, H, i)
        return fi, F2, H2
    F2, H2 = copy_tables(F, H)
    a = F2[i]["attrs"]
    if kind == u"文脈を替える":
        cur = a.get("contextRef")
        other = None
        for fj, j in num_pool(files):
            v = files[fj][2][j]["attrs"].get("contextRef")
            if v is not None and v != cur:
                other = v
                break
        if other is None:
            return None
        a["contextRef"] = other
    else:
        if "sign" in a:
            del a["sign"]
        else:
            a["sign"] = "-"
    F2[i]["attrs"] = dict(sorted(a.items()))
    return fi, F2, H2


# ======================================================================================================
# 比べる
def read_rows(path):
    u"""CSV を csv として読む。最初の 1 行(見出し)を除いた行(字の組)を並べ替えた並び。file が無ければ ``[]``。"""
    if not os.path.isfile(path):
        return []
    csv.field_size_limit(2 ** 31 - 1)
    with io.open(path, encoding="utf-8", newline="") as fh:
        rows = [tuple(r) for r in csv.reader(fh)]
    return sorted(rows[1:])


def facts_same(a, b):
    return bool(a) and bool(b) and a == b


def sounds_same(a, b):
    u"""鳴り方: 1 回の類と符号ごとの指摘の行の数が全部同じ。"""
    return a[u"類"] == b[u"類"] and dict(a[u"符号ごとの行"]) == dict(b[u"符号ごとの行"])


def run_tool(tool, zip_path, workdir, tag, runner=None):
    u"""公開の道具を 1 回掛ける(``--facts`` つき)。(1 回分の数, 行の並び)。"""
    runner = runner or V.exec_cmd
    csv_path = os.path.join(workdir, tag + ".csv")
    cmd = V.command(tool, YEAR, zip_path) + ["--facts", csv_path, "--factListCols", FACT_COLS]
    text, timed_out = runner(cmd, TIMEOUT_SEC)
    return V.count_one(text, timed_out), read_rows(csv_path), text


def build_files(entries):
    u"""元の包みの PublicDoc の ``.htm`` を剥がして表にする。[(名, plain, F, H)] を名の昇順で(混ぜ物の「file の並び」)。知らない形は ``Decline``(例外も断る)。"""
    out = []
    for info, data in entries:
        if is_public_htm(info.filename):
            try:
                text = data.decode("utf-8")
                plain, F, H = strip_text(text)
            except Decline:
                raise
            except Exception:                                 # noqa: BLE001  知らない形は断る
                raise Decline(u"剥がす途中の例外")
            out.append((info.filename, plain, F, H))
    out.sort(key=lambda t: t[0])
    return out


def rebuilt_texts(files):
    u"""[(名, 組んだ字)]。例外は断る。"""
    out = []
    for name, plain, F, H in files:
        try:
            out.append((name, build_text(plain, F, H)))
        except Decline:
            raise
        except Exception:                                     # noqa: BLE001
            raise Decline(u"組む途中の例外")
    return out


def package_with(entries, texts):
    u"""元の包みの PublicDoc の ``.htm`` を ``texts``({名: 字})で置き換えた包み。ほかの file は元のまま。"""
    out = []
    for info, data in entries:
        if info.filename in texts:
            out.append((info, texts[info.filename].encode("utf-8")))
        else:
            out.append((info, data))
    return out


def count_files(entries, same_names):
    u"""``ix:header`` を持たない・持つ .htm の (数, 字が同じ数)。断った書類は ``same_names`` が空。"""
    res = od([(u"持たない", od([(u"数", 0), (u"字が同じ", 0)])), (u"持つ", od([(u"数", 0), (u"字が同じ", 0)]))])
    for info, data in entries:
        if not is_public_htm(info.filename):
            continue
        try:
            text = data.decode("utf-8")
            h = has_header(text)
        except UnicodeDecodeError:
            h = b"<ix:header" in data
        k = u"持つ" if h else u"持たない"
        res[k][u"数"] += 1
        if info.filename in same_names:
            res[k][u"字が同じ"] += 1
    return res


def process_doc(tool, zip_path, tmp_root=None, runner=None, mixtures=False):
    u"""書類 1 本。(書類ごとの数, secret に足す要素の名の集まり)。元の包みと組み直した包みを同じ掛け方で 1 回ずつ。"""
    entries = load_package(zip_path)
    tags = od((k, 0) for k in IX_KINDS)
    for info, data in entries:
        if is_public_htm(info.filename):
            for k, n in count_ix_tags(data.decode("utf-8", "replace")).items():
                tags[k] += n
    rec = od([(u"断った", False), (u"断った理由", u""), (u"タグの数", tags)])
    elems = set()
    d = tempfile.mkdtemp(prefix="xb0_", dir=tmp_root)
    try:
        orig_zip = os.path.join(d, "orig.zip")
        write_package(entries, orig_zip)
        orig, orig_rows, _t = run_tool(tool, orig_zip, d, "orig", runner)
        rec[u"元の fact の行の数"] = len(orig_rows)
        rec[u"元の 1 回"] = orig
        files = texts = None
        try:
            files = build_files(entries)
            texts = rebuilt_texts(files)
        except Decline as exc:
            rec[u"断った"], rec[u"断った理由"] = True, exc.reason
        except Exception:                                      # noqa: BLE001
            rec[u"断った"], rec[u"断った理由"] = True, u"例外"
        if rec[u"断った"]:
            rec[u"字の file"] = count_files(entries, set())
            rec[u"組み直しの fact の行の数"] = None
            rec[u"組み直しの 1 回"] = None
            rec[u"fact が同じ"] = False
            rec[u"鳴り方が同じ"] = False
            rec[u"混ぜ物"] = [] if not mixtures else [od([(u"種類", k), (u"作った", False), (u"fact が同じ", False), (u"鳴り方が同じ", False)]) for k in MIX_KINDS]
            return rec, elems
        for _n, _p, F, H in files:
            for e in F:
                if "name" in e["attrs"]:
                    elems.add(e["attrs"]["name"].split(":")[-1])
            for h in (H["hidden"] if H else []):
                if "name" in h["attrs"]:
                    elems.add(h["attrs"]["name"].split(":")[-1])
        tdict = dict(texts)
        orig_by = dict((info.filename, data) for info, data in entries)
        same_names = set(n for n, t in texts if t.encode("utf-8") == orig_by[n])
        rec[u"字の file"] = count_files(entries, same_names)
        new_zip = os.path.join(d, "new.zip")
        write_package(package_with(entries, tdict), new_zip)
        new, new_rows, _t = run_tool(tool, new_zip, d, "new", runner)
        rec[u"組み直しの fact の行の数"] = len(new_rows)
        rec[u"組み直しの 1 回"] = new
        rec[u"fact が同じ"] = facts_same(orig_rows, new_rows)
        rec[u"鳴り方が同じ"] = sounds_same(orig, new)
        mixes = []
        if mixtures:
            for kind in MIX_KINDS:
                m = None
                try:
                    m = mix_tables(files, kind)
                except Decline:
                    m = None
                item = od([(u"種類", kind), (u"作った", False), (u"fact が同じ", False), (u"鳴り方が同じ", False)])
                if m is not None:
                    fi, F2, H2 = m
                    nm, plain, _F, _H = files[fi]
                    try:
                        t2 = dict(tdict)
                        t2[nm] = build_text(plain, F2, H2)
                    except Exception:                          # noqa: BLE001
                        t2 = None
                    if t2 is not None:
                        mz = os.path.join(d, "mix%d.zip" % MIX_KINDS.index(kind))
                        write_package(package_with(entries, t2), mz)
                        mres, mrows, _t = run_tool(tool, mz, d, "mix%d" % MIX_KINDS.index(kind), runner)
                        item[u"作った"] = True
                        item[u"fact が同じ"] = facts_same(orig_rows, mrows)
                        item[u"鳴り方が同じ"] = sounds_same(orig, mres)
                mixes.append(item)
        rec[u"混ぜ物"] = mixes
        return rec, elems
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ======================================================================================================
# 数える(封 §2)
def group_totals(entries):
    u"""書類ごとの数の並び → §2 の 1〜3。"""
    cls = od((c, 0) for c in V.CLASSES)
    files = od([(u"持たない", od([(u"数", 0), (u"字が同じ", 0)])), (u"持つ", od([(u"数", 0), (u"字が同じ", 0)]))])
    tags = od((k, 0) for k in IX_KINDS)
    declined = same_facts = same_sound = facts_rows = zero_rows = 0
    reasons = collections.Counter()
    for e in entries:
        if e[u"断った"]:
            declined += 1
            reasons[e[u"断った理由"]] += 1
        else:
            cls[e[u"組み直しの 1 回"][u"類"]] += 1
        same_facts += 1 if e[u"fact が同じ"] else 0
        same_sound += 1 if e[u"鳴り方が同じ"] else 0
        facts_rows += e[u"元の fact の行の数"]
        zero_rows += 1 if e[u"元の fact の行の数"] == 0 else 0
        for k in (u"持たない", u"持つ"):
            for f in (u"数", u"字が同じ"):
                files[k][f] += e[u"字の file"][k][f]
        for k in IX_KINDS:
            tags[k] += e[u"タグの数"][k]
    return od([
        (u"書類", len(entries)), (u"断った書類", declined), (u"断った理由ごと", od(sorted(reasons.items()))), (u"fact が同じ書類", same_facts), (u"鳴り方が同じ書類", same_sound),
        (u"組み直した包みの 1 回の類ごと", cls), (u"file", files), (u"元の fact の行の数の合計", facts_rows), (u"元の fact の行が 0 の書類", zero_rows), (u"ix のタグの数の合計", tags)])


def mix_totals(per_doc):
    res = od()
    made = fact_diff = sound_diff = 0
    for e in per_doc:
        for m in e[u"混ぜ物"]:
            if m[u"作った"]:
                made += 1
            fact_diff += 0 if m[u"fact が同じ"] else 1
            sound_diff += 0 if m[u"鳴り方が同じ"] else 1
    res[u"混ぜ物の数"] = sum(len(e[u"混ぜ物"]) for e in per_doc)
    res[u"作れた数"] = made
    res[u"fact が同じでない数"] = fact_diff
    res[u"鳴り方が同じでない数"] = sound_diff
    return res


def totals_of(per_doc, dev_count=DEV_COUNT):
    dev, prod = per_doc[:dev_count], per_doc[dev_count:]
    return od([(u"開発の 5 本", group_totals(dev)), (u"本番だけの %d 本" % (len(per_doc) - dev_count), group_totals(prod)), (u"全部", group_totals(per_doc)), (u"混ぜ物", mix_totals(dev))])


def judged(tot, n=DOCS_WANT):
    u"""封 §4 の判定に要る数(当たり・外れは書かない)。"""
    prod = tot[[k for k in tot if k.startswith(u"本番だけの")][0]]
    nh = prod[u"file"][u"持たない"]
    wh = prod[u"file"][u"持つ"]
    mx = tot[u"混ぜ物"]
    return od([
        (u"XB0-1 fact が同じ書類", od([(u"書類", prod[u"fact が同じ書類"]), (u"分母", prod[u"書類"])])),
        (u"XB0-2 断った書類", od([(u"書類", prod[u"断った書類"]), (u"分母", prod[u"書類"])])),
        (u"XB0-3 鳴り方が同じ書類", od([(u"書類", prod[u"鳴り方が同じ書類"]), (u"分母", prod[u"書類"])])),
        (u"XB0-4 ix:header を持たない file のうち字が同じもの", od([(u"file", nh[u"字が同じ"]), (u"分母", nh[u"数"])])),
        (u"XB0-5 ix:header を持つ file のうち字が同じもの", od([(u"file", wh[u"字が同じ"]), (u"分母", wh[u"数"])])),
        (u"XB0-6 混ぜ物のうち fact が同じでないもの", od([(u"個", mx[u"fact が同じでない数"]), (u"分母", mx[u"混ぜ物の数"])])),
        (u"XB0-7 混ぜ物のうち鳴り方が元と違うもの", od([(u"個", mx[u"鳴り方が同じでない数"]), (u"分母", mx[u"混ぜ物の数"])]))])


# ======================================================================================================
# 道具の確かめ・記録
def check_tool(tool, runner=None, sha_reader=sha256_file, want_version=TOOL_VERSION, want_sha=SHA_P):
    u"""実行 file が在り、版・ModelValue.py の sha256 が封の字と同じであること。違えば止まる。道具の情報を返す。"""
    runner = runner or V.exec_cmd
    if not os.path.isfile(os.path.join(tool, V.EXE_REL)):
        raise Stop(u"**道具の実行 file が無い。止める**")
    info = V.tool_info(tool, runner, sha_reader)
    if info[u"版"] != want_version:
        raise Stop(u"**道具の版が %s でない。止める**" % want_version)
    if info[u"ModelValue.py の sha256"] != want_sha:
        raise Stop(u"**道具 P の ModelValue.py の sha256 が封と違う。止める**")
    return info


def dev_docs(docs_dir, count=DEV_COUNT):
    u"""置き場の並びの頭から ``count`` 本だけを選ぶ(``W.select_docs`` と同じ条件・同じ並び。残りの zip は開かない)。[(stem, path, xsd の名の並び)]。"""
    found = []
    for p in sorted(glob.glob(os.path.join(docs_dir, "*.zip")), key=lambda x: os.path.basename(x)[:-4]):
        with zipfile.ZipFile(p) as z:
            xs = [os.path.basename(n) for n in W.doc_xsd_names(z)]
        if any(x.startswith(W.XSD_PREFIX) for x in xs):
            found.append((os.path.basename(p)[:-4], p, xs))
            if len(found) == count:
                break
    return found


def build_record(tool_p, docs_dir=None, want=DOCS_WANT, runner=None, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_sha=SHA_P, dev_count=DEV_COUNT):
    u"""道具を確かめてから、書類を 1 本ずつ掛ける。(記録, secret)。書かない。"""
    docs = W.select_docs(docs_dir or DOCS_DIR, want)
    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)
    per_doc = []
    elems = set()
    lines = set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        r, el = process_doc(tool_p, p, tmp_root, runner, mixtures=(n <= dev_count))
        per_doc.append(od([(u"番号", n)] + list(r.items())))
        elems |= el
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    secret = (set(), elems, [d[0] for d in docs], ecodes, lines)
    return assemble(per_doc, W.order_sha256([d[0] for d in docs]), info, dev_count), secret


def assemble(per_doc, order_sha, info, dev_count=DEV_COUNT):
    tot = totals_of(per_doc, dev_count)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XB0(受理済みの有報の inline XBRL を、タグを剥がした本文と fact の表から自前の部品で組み直すと、公開の道具が読む fact と検査の鳴り方は元と同じになるか)(0 USD・engine は読まない)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"書類の本数", len(per_doc)), (u"書類の file 名の並びの sha256", order_sha), (u"開発の 5 本の番号", list(range(1, dev_count + 1))),
        (u"道具の版", info[u"版"]), (u"道具 P の ModelValue.py の sha256", info[u"ModelValue.py の sha256"]), (u"道具 P の package の一覧の sha256", info[u"package の一覧の sha256"]),
        (u"Python の版(道具 P)", info[u"Python の版"]), (u"規則の年", YEAR), (u"混ぜ物の種類", list(MIX_KINDS)), (u"時間の上限(秒)", TIMEOUT_SEC)])
    rec[u"書類"] = per_doc
    rec[u"集計"] = tot
    rec[u"予測の判定に要る数(XB0-1〜XB0-7。当たり・外れは結果の文書で)"] = judged(tot, len(per_doc))
    rec[u"限界"] = list(LIMITS)
    return rec


FILE_FORM_RE = V.FILE_FORM_RE
BODY_MIN = V.BODY_MIN


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(docID・EDINET コード・file の名・要素の名・指摘の行の本文)が無いか。在れば止める。"""
    V.check_clean(rec, text, secret)                   # 欄・字の形・docID・EDINET コード・要素の名(secret[1])・file の名の形・指摘の行の本文


def verify_record(rec, text=None, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する(道具は呼ばない・掛け直さない)。違えば止まる。"""
    docs = rec.get(u"書類")
    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"書類の本数"] != want:
        raise Stop(u"**記録の書類が 67 本でない。止める**")
    for i, d in enumerate(docs, 1):
        if d.get(u"番号") != i:
            raise Stop(u"**記録の書類の番号が違う。止める**")
        for k in (u"断った", u"断った理由", u"タグの数", u"元の fact の行の数", u"元の 1 回", u"字の file", u"fact が同じ", u"鳴り方が同じ", u"混ぜ物", u"組み直しの 1 回"):
            if k not in d:
                raise Stop(u"**記録の書類の形が違う。止める**")
        if d[u"断った"] != (d[u"組み直しの 1 回"] is None) or (d[u"断った"] and (d[u"fact が同じ"] or d[u"鳴り方が同じ"])) or (not d[u"断った"] and d[u"断った理由"]):
            raise Stop(u"**断った書類の形が違う。止める**")
        if d[u"元の 1 回"][u"類"] not in V.CLASSES or (d[u"組み直しの 1 回"] is not None and d[u"組み直しの 1 回"][u"類"] not in V.CLASSES):
            raise Stop(u"**1 回の類が違う。止める**")
        if len(d[u"混ぜ物"]) != (len(MIX_KINDS) if i <= dev_count else 0) or [m[u"種類"] for m in d[u"混ぜ物"]] != (list(MIX_KINDS) if i <= dev_count else []):
            raise Stop(u"**混ぜ物の形が違う。止める**")
        for k in (u"持たない", u"持つ"):
            f = d[u"字の file"][k]
            if f[u"字が同じ"] > f[u"数"] or (d[u"断った"] and f[u"字が同じ"]):
                raise Stop(u"**字の file の数が違う。止める**")
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
    for n, (_s, p, _x) in enumerate(docs, 1):
        r, _el = process_doc(tool_p, p, tmp_root, runner, mixtures=True)
        per.append(od([(u"番号", n)] + list(r.items())))
        say(u"doc %d: 断った=%s(%s) fact同じ=%s 鳴り方同じ=%s 元の行=%s 新の行=%s ファイル=%s 混ぜ物=%s" % (
            n, r[u"断った"], r[u"断った理由"], r[u"fact が同じ"], r[u"鳴り方が同じ"], r[u"元の fact の行の数"], r[u"組み直しの fact の行の数"],
            json.dumps(r[u"字の file"], ensure_ascii=False), [(m[u"種類"], m[u"作った"], m[u"fact が同じ"], m[u"鳴り方が同じ"]) for m in r[u"混ぜ物"]]))
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
