# -*- coding: utf-8 -*-
"""XBRL instance reading: ZIP -> facts / contexts / textblocks, context
selection (plain / member), member resolution material (label linkbase,
member denominator), and MD&A text-block selection.

A transcription of ``fixtures/xbrl/xbrl_probe.py`` (``load_instance``,
``Stripper``, ``strip_html``, ``plain_context``) and
``fixtures/xbrl/xbrl_probe3.py`` (``ctx_ok``, ``facts_for``,
``member_denominator``, ``labels_from_zip``). Not imported from the
originals; compared against them value-for-value by
``tests/adapters/xbrl/test_lineage.py``.
"""

import hashlib
import html
import io
import os
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

XLINK = "{http://www.w3.org/1999/xlink}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"


class Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, d):
        self.parts.append(d)

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "br", "div", "tr", "li", "h1", "h2", "h3", "h4", "td"):
            self.parts.append("\n" if tag != "td" else " ")

    def text(self):
        return re.sub(r"[ \t　]+", " ", "".join(self.parts))


def strip_html(s):
    p = Stripper()
    p.feed(html.unescape(s))
    return p.text()


def _dimension_attr(attrs):
    """``explicitMember`` の属性文字列から ``dimension`` の値(無ければ None)。"""
    m = re.search(r'dimension="([^"]+)"', attrs or "")
    return m.group(1) if m else None


def load_instance(zbytes):
    """xbrl_probe.py: load_instance の写し(.xbrl があればそれ、無ければ iXBRL)。

    2026-10-19: 各枠に ``axes``(``[[軸, 枠の名], ...]``、``members`` と 1:1)を足した
    (封 docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md)。既存の鍵は変えていない。
    """

    z = zipfile.ZipFile(io.BytesIO(zbytes))
    names = z.namelist()
    xbrl = [n for n in names if n.startswith("XBRL/PublicDoc/") and n.endswith(".xbrl")]
    htm = [n for n in names if n.startswith("XBRL/PublicDoc/") and n.endswith(".htm")]
    facts, contexts, textblocks = [], {}, {}
    src = None
    if xbrl:
        src = xbrl[0]
        raw = z.read(src).decode("utf-8")
        ns = dict(re.findall(r'xmlns:([A-Za-z0-9_\-]+)="([^"]+)"', raw))
        uri2pre = {v: k for k, v in ns.items()}
        root = ET.fromstring(raw)
        XBRLI = "{http://www.xbrl.org/2003/instance}"
        for c in root.iter(XBRLI + "context"):
            cid = c.get("id")
            per = c.find(XBRLI + "period")
            inst = per.find(XBRLI + "instant")
            st = per.find(XBRLI + "startDate")
            en = per.find(XBRLI + "endDate")
            members = [m.text for m in c.iter() if m.tag.endswith("explicitMember")]
            # 軸の保持((e) の準備。封 docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md §1 の 1)。
            # ``members`` と同じ要素から ``dimension`` 属性を取るので、並びと本数は 1:1。
            axes = [[m.get("dimension"), m.text] for m in c.iter() if m.tag.endswith("explicitMember")]
            contexts[cid] = {
                "instant": inst.text if inst is not None else None,
                "start": st.text if st is not None else None,
                "end": en.text if en is not None else None,
                "members": members,
                "axes": axes,
            }
        for el in root:
            tag = el.tag
            if not tag.startswith("{"):
                continue
            uri, local = tag[1:].split("}")
            pre = uri2pre.get(uri)
            if pre in (None, "xbrli", "link", "xlink"):
                continue
            name = "%s:%s" % (pre, local)
            cref = el.get("contextRef")
            if cref is None:
                continue
            txt = (el.text or "")
            if local.endswith("TextBlock"):
                textblocks[name] = textblocks.get(name) or txt
                continue
            dec = el.get("decimals")
            unit = el.get("unitRef")
            v = txt.strip()
            if unit and re.fullmatch(r"-?\d+(\.\d+)?", v):
                facts.append({"name": name, "context": cref, "unit": unit, "decimals": dec, "value": float(v)})
    else:
        src = ",".join(htm[:3])
        for n in htm:
            raw = z.read(n).decode("utf-8", "ignore")
            for m in re.finditer(r'<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>', raw, re.S):
                a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
                v = re.sub(r"<[^>]+>", "", m.group(2)).replace(",", "").strip()
                if not re.fullmatch(r"-?\d+(\.\d+)?", v or ""):
                    continue
                val = float(v) * (10 ** int(a.get("scale", "0") or 0))
                if a.get("sign") == "-":
                    val = -val
                facts.append({"name": a.get("name"), "context": a.get("contextRef"), "unit": a.get("unitRef"), "decimals": a.get("decimals"), "value": val})
            for m in re.finditer(r'<ix:nonNumeric([^>]*name="([^"]*TextBlock)"[^>]*)>(.*?)</ix:nonNumeric>', raw, re.S):
                textblocks[m.group(2)] = textblocks.get(m.group(2)) or m.group(3)
            for m in re.finditer(r'<xbrli:context id="([^"]+)">(.*?)</xbrli:context>', raw, re.S):
                body = m.group(2)

                def g(t):
                    mm = re.search(r"<xbrli:%s>([^<]+)<" % (t,), body)
                    return mm.group(1) if mm else None

                contexts[m.group(1)] = {
                    "instant": g("instant"), "start": g("startDate"), "end": g("endDate"),
                    "members": re.findall(r"explicitMember[^>]*>([^<]+)<", body),
                    # 軸の保持(上の .xbrl の経路と同じ 1:1。``dimension`` 属性が無い要素は None)
                    "axes": [[_dimension_attr(attrs), text_]
                             for attrs, text_ in re.findall(r"explicitMember([^>]*)>([^<]+)<", body)],
                }
    return {"source": src, "facts": facts, "contexts": contexts, "textblocks": textblocks, "names": names}


# ---------------------------------------------------------------------------
# 連結・単体の落とし込み(P20。封 docs/CONSOLIDATION_P20_PLAN_2026-10-14.md)
#
# 人間の指示(2026-10-14):「単純に『連結が見つからなければ単体を使う』とすれば
# よいわけではない。**検出件数を増やすより、違う対象の数値を正しい根拠として
# 扱わないことが重要。**」
#
# 守りは 3 つ。
#   (1) **書類レベルで 1 度だけ決める。** 決定は ``DocumentContexts`` に 1 つだけ
#       持たせる(主張ごとに決めると同じ書類で連結と単体が混ざる)。
#   (2) **連結の枠に財務の要素が 1 種でも在れば落とさない。** 少数しか無い書類も
#       落とさない(判断できない場合は止まる = 保留)。
#   (3) **落とすのは member の付かない素の枠を探しているときだけ。** セグメントの
#       member を指定した引き(``ctx_ok`` の member あり)は 1 行も変えない。
#
# 財務の接頭辞は **日本基準と IFRS の両方**。``jppfs_cor`` だけで数えると
# **IFRS の会社が「連結を作っていない」に見える**(2026-10-14 に S100YYQX を実際に
# そう誤分類した。封 §1-1)。
# ---------------------------------------------------------------------------
FINANCIAL_PREFIXES = ("jppfs_cor:", "jpigp_cor:")
PLAIN_PERIOD_CONTEXTS = ("CurrentYearInstant", "CurrentYearDuration",
                         "Prior1YearInstant", "Prior1YearDuration")
NONCONSOLIDATED_MEMBER = "NonConsolidatedMember"


def consolidated_element_count(facts):
    """連結の枠に在る**財務の要素の種類数**。0 なら連結財務諸表が無い。

    封 §2 の式そのまま。``facts`` は :func:`load_instance` の ``facts``。
    """

    names = set()
    for fact in facts:
        name = fact.get("name") or ""
        if name.startswith(FINANCIAL_PREFIXES) and fact.get("context") in PLAIN_PERIOD_CONTEXTS:
            names.add(name)
    return len(names)


class DocumentContexts(dict):
    """context の辞書に**書類レベルの決定を 1 つだけ**持たせる入れ物。

    中身は元の辞書と同じ(``items()`` の形も変えない)。足すのは属性 1 つだけなので、
    ``contexts`` を回している既存の関数(``member_denominator`` など)は 1 行も変わらない。
    """

    nonconsolidated_ok = False


def with_nonconsolidated_fallback(contexts, facts, enabled):
    """**書類ごとに 1 度だけ呼ぶ。** 旗が真で、連結の枠に財務の要素が 1 種も
    無いときだけ、単体の枠を素の枠として扱う ``DocumentContexts`` を返す。
    それ以外は元の ``contexts`` をそのまま返す(振る舞いは 1 行も変わらない)。
    """

    if not enabled or consolidated_element_count(facts) != 0:
        return contexts
    wrapped = DocumentContexts(contexts)
    wrapped.nonconsolidated_ok = True
    return wrapped


def _nonconsolidated_only(cid, contexts):
    """``cid`` が「単体の member **だけ**を持つ素の期間」か。

    member の値は ``jppfs_cor:NonConsolidatedMember`` のように**接頭辞つき**で入って
    いる(裸の局所名で比べると 1 件も当たらず、「0 件だから効かない」と読み違える。
    2026-10-14 に実際にそう読み違えた)。接頭辞は会社によって変わりうるので、
    **コロンの後の局所名**で比べる。

    member が 2 つ以上ある枠(資本金・自己株式などの内訳)は**当たらない**。
    内訳を素の枠として扱うと、本文の合計の数が内訳の数に結びついてしまう。
    """

    c = contexts.get(cid) or {}
    locals_ = [m.split(":")[-1] for m in (c.get("members") or [])]
    return locals_ == [NONCONSOLIDATED_MEMBER]


def plain_context(cid, contexts):
    c = contexts.get(cid) or {}
    if not c.get("members") and "NonConsolidated" not in cid:
        return True
    # P20: 連結財務諸表が無い書類でだけ、**単体の member だけ**を持つ枠を素として扱う。
    return bool(getattr(contexts, "nonconsolidated_ok", False)) and _nonconsolidated_only(cid, contexts)


def ctx_ok(cid, contexts, member=None):
    """xbrl_probe3.py: ctx_ok の写し。member が None なら plain_context。member が
    決まっていれば、その member だけを持つ連結の context(置き換え。合わせない)。
    """

    if member is None:
        return plain_context(cid, contexts)
    c = contexts.get(cid) or {}
    return c.get("members") == [member] and "NonConsolidated" not in cid


def facts_for(elems, facts, contexts, member=None, want_ctx=None):
    """xbrl_probe3.py: facts_for の写し。要素の選び方(完全一致 -> 部分一致)は
    xbrl_probe.py のまま、context の選別だけが plain_context -> ctx_ok(member)。
    """

    exact, loose = [], []
    for f in facts:
        local = f["name"].split(":")[-1]
        if not ctx_ok(f["context"], contexts, member):
            continue
        if want_ctx and not f["context"].startswith(want_ctx):
            continue
        if any(local == e or local == e + "SummaryOfBusinessResults" or local == e.replace("Income", "IncomeLoss") + "SummaryOfBusinessResults" for e in elems):
            exact.append(f)
        elif any(e.lower() in local.lower() for e in elems):
            loose.append(f)
    return exact or loose


def member_denominator(contexts):
    """xbrl_probe3.py: member_denominator の写し。"""

    ms = set()
    for cid, c in contexts.items():
        if not (c.get("start") and c.get("end")):
            continue
        if "NonConsolidated" in cid:
            continue
        if not (cid.startswith("CurrentYear") or cid.startswith("Prior1Year")):
            continue
        for m in c.get("members") or []:
            ms.add(m)
    return sorted(ms)


_STANDARD_MEMBER_NAMESPACE_PREFIXES = ("jppfs_cor", "jpcrp_cor", "jpigp_cor", "jpdei_cor")


def segment_member_denominator(contexts):
    """Core 接続 C-1g §1-4(人間の承認、2026-10-06): 事業 member だけを数える
    分母。凍結の ``member_denominator`` と同じ対象 context(連結・当期または
    前期・期間/時点を問わず start/end を持つ)から、接頭辞が標準の名前空間
    (jppfs_cor・jpcrp_cor・jpigp_cor・jpdei_cor)でない member だけを集める。
    P6 だけがこちらを使う(``member_denominator`` 自体は系譜の試験のため
    変えない)。
    """

    ms = set()
    for cid, c in contexts.items():
        if not (c.get("start") and c.get("end")):
            continue
        if "NonConsolidated" in cid:
            continue
        if not (cid.startswith("CurrentYear") or cid.startswith("Prior1Year")):
            continue
        for m in c.get("members") or []:
            prefix = m.split(":", 1)[0] if ":" in m else None
            if prefix not in _STANDARD_MEMBER_NAMESPACE_PREFIXES:
                ms.add(m)
    return sorted(ms)


def labels_from_zip(z, names):
    """xbrl_probe3.py: labels_from_zip の写し。"""

    out = {}
    for n in names:
        if not (n.startswith("XBRL/PublicDoc/") and n.endswith("_lab.xml")):
            continue
        root = ET.fromstring(z.read(n))
        loc_id, lab_text, arcs = {}, {}, []
        for el in root.iter():
            tag = el.tag.split("}")[-1]
            if tag == "loc":
                href = el.get(XLINK + "href") or ""
                loc_id[el.get(XLINK + "label")] = href.split("#")[-1]
            elif tag == "label":
                role = el.get(XLINK + "role") or ""
                lang = el.get(XML_NS + "lang") or ""
                if role.endswith("/label") and lang.startswith("ja"):
                    lab_text[el.get(XLINK + "label")] = el.text or ""
            elif tag == "labelArc":
                arcs.append((el.get(XLINK + "from"), el.get(XLINK + "to")))
        for a, b in arcs:
            if a in loc_id and b in lab_text:
                import unicodedata

                out[loc_id[a]] = unicodedata.normalize("NFKC", lab_text[b].strip())
    return out


def select_mdna(textblocks):
    """xbrl_probe.py main(): MD&A textBlock の選び方の写し。"""

    name = next((n for n in textblocks if "ManagementAnalysis" in n and n.endswith("TextBlock")), None)
    if name is None:
        name = next((n for n in textblocks if "AnalysisOfFinancialPosition" in n or "OverviewOfBusinessResults" in n), None)
    return name


# ---------------------------------------------------------------------------
# XBRL 直し §7(人間の指示、2026-10-08): 書類自身のインライン XBRL から
# 「日本語の勘定科目名 → 要素の局所名」を取る。``profile.label_vocabulary`` が
# 真のときだけ使う。
#
# 財務諸表は ``*_ixbrl.htm``(インライン XBRL)で、表の 1 つの ``<tr>`` の中に
# 日本語の科目名(テキストの ``<td>``)とその行の数値に付いた要素名
# (``<ix:nonFraction name="jppfs_cor:Assets">``)が並んでいる。**順番の推測では
# なく同じ行に在ること**で対にする(行をまたいだ対応づけはしない)。
#
# 標準タクソノミ(jppfs/jpcrp)の日本語ラベルは書類の ZIP には入っていない
# (ZIP に在るのは会社拡張の ``_lab.xml`` だけ)。それを使うには
# ``disclosure.edinet-fsa.go.jp`` からの取得が要る ― この関数は取得しない。
# 経緯は docs/XBRL_LABEL_VOCAB_PLAN_2026-10-08.md §1-2。
# ---------------------------------------------------------------------------
_TR_RE = re.compile(r"<tr[\s>].*?</tr>", re.S | re.I)
_TD_SPLIT_RE = re.compile(r"</td>", re.I)
_IX_NAME_RE = re.compile(r'<ix:non(?:Fraction|Numeric)[^>]*\bname="([^"]+)"', re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_NUMERIC_ONLY_RE = re.compile(r"^[\d,.\-△▲%()−\s]+$")

# 除く名前(字で書く)。勘定科目を一意に指さない語と、表紙の項目。
LABEL_MIN_LEN = 3
LABEL_DENY = ("その他", "合計", "小計", "計", "区分", "千円", "百万円", "円",
              "前連結会計年度", "当連結会計年度", "前事業年度", "当事業年度")


def _row_label(row):
    """``<tr>`` の中の、勘定科目名として読めるテキスト。
    数字だけ・空のセルは捨て、**最初の読めるセル**を採る(科目名は行の左端に
    在るため)。1 文字のセルが先頭に来ることがあるので、2 文字未満なら次を見る。
    """

    for cell in _TD_SPLIT_RE.split(row):
        # 実体参照を先に戻す ― この書類の HTML は空のセルに ``&#160;`` を
        # **文字列のまま**置いており、戻さずにタグだけ外すと "&#160;" という
        # 6 文字が科目名として拾われる(最初の実装がこれで 1 社目の名前を
        # 226 → 105 に落としていた。2 社目・3 社目は本物の nbsp 文字なので
        # 落ちず、1 書類だけで測っていたら気づかない型の誤りだった)。
        text = html.unescape(_TAG_RE.sub("", cell))
        text = re.sub(r"\s+", "", text.replace("\u00a0", " "))
        if not text or _NUMERIC_ONLY_RE.match(text) or len(text) < 2:
            continue
        return text
    return None


# ---------------------------------------------------------------------------
# XBRL 直し §7a(人間の判断、2026-10-08): ラベルを**計算書の行から来たものだけ**に
# 限る。原因が分かっている悪化 2 件のうち 1 件(2 社目 T009 の主語が 売上高 →
# 美容室支援事業(セグメント名)に移った)を消すため。
#
# 4 つの規則を測って比べた結果(docs/XBRL_LABEL_VOCAB2_PLAN_2026-10-08.md §1.1):
#
#   - member の付かない行だけ   -> セグメント名は消えるが「連結子会社」は残る
#   - jppfs_cor の要素だけ      -> 「連結子会社」(監査報酬の表 = jpcrp_cor)は消える
#   - **両方**                  -> 2 つの型が別々の条件で落ち、残ってほしい語
#                                  (売上原価・利益剰余金・短期借入金)は残る
#
# セグメント名は member つきの context を持つ行に、会社名・役員名・株主名は
# jpcrp_cor の要素に付いている。だから **両方**を要求する。
# ---------------------------------------------------------------------------
_IX_TAG_RE = re.compile(r"<ix:non(?:Fraction|Numeric)[^>]*>", re.I)
_IX_ATTR_NAME_RE = re.compile(r'\bname="([^"]+)"')
_IX_ATTR_CTX_RE = re.compile(r'\bcontextRef="([^"]+)"')

# 財務諸表タクソノミの接頭辞(字で書く)。計算書の行の要素はこれで付いている。
STATEMENT_PREFIX = "jppfs_cor"


def _row_elements(row, statement_only, contexts):
    """その ``<tr>`` から採る要素名(接頭辞つき)の一覧。

    ``statement_only`` が偽なら、今までどおり行の中の ix の ``name`` を全部採る。
    真なら §7a の規則を当てる ― 行の ix の context に member が **1 つも**
    付いていないこと、かつ要素が ``jppfs_cor`` のものだけを採る。
    どちらも満たさない行は空の一覧を返し、呼び出し側が行ごと捨てる。
    """

    if not statement_only:
        return _IX_NAME_RE.findall(row)
    pairs = []
    for tag in _IX_TAG_RE.findall(row):
        name = _IX_ATTR_NAME_RE.search(tag)
        if not name:
            continue
        ctx = _IX_ATTR_CTX_RE.search(tag)
        pairs.append((name.group(1), ctx.group(1) if ctx else ""))
    for _name, cid in pairs:
        if (contexts.get(cid) or {}).get("members"):
            return []
    return [name for name, _cid in pairs if name.split(":")[0] == STATEMENT_PREFIX]


def inline_labels(z, names, statement_only=False, contexts=None):
    """``{日本語の勘定科目名: [要素の局所名, ...]}``。除く名前は適用済み。

    ``statement_only`` は §7a。真のときは ``contexts``
    (``load_instance`` の ``contexts``)が要る ― member が付いているかを見るため。
    """

    if statement_only and contexts is None:
        raise ValueError("inline_labels(statement_only=True) needs contexts")
    found = {}
    for n in names:
        if not n.endswith("_ixbrl.htm"):
            continue
        text = z.read(n).decode("utf-8", "replace")
        for row in _TR_RE.findall(text):
            elements = _row_elements(row, statement_only, contexts or {})
            if not elements:
                continue
            label = _row_label(row)
            if not label or len(label) < LABEL_MIN_LEN or label in LABEL_DENY:
                continue
            if "【" in label or "】" in label:
                continue
            bucket = found.setdefault(label, [])
            for e in elements:
                local = e.split(":")[-1]
                if local not in bucket:
                    bucket.append(local)
    return found


# ---------------------------------------------------------------------------
# XBRL 直し §8(人間の許可、2026-10-08): 標準タクソノミ(jppfs・jpcrp の
# 2025-11-01 版)の**日本語の標準ラベル**で勘定科目を引く。
#
# ラベルの本体は**このリポジトリの外**に在る(人間の指示: 「取得したファイルは
# リポジトリの外に置いて sha256 だけを残す」)。置き場と取り方は
# fixtures/xbrl/TAXONOMY_LABELS_README.md、照合用の sha256 は
# fixtures/xbrl/taxonomy_labels_sha256.txt。
#
# **読む前に毎回 sha256 を照合し、無ければ・違えば落ちる。** 黙って 0 件を返すと
# 「効かなかった」と読み違える(同じ型の誤りを前に 4 回踏んでいる)。
#
# 要素は ``fact_locals``(その書類に fact が在る要素)に限る ― タクソノミ全体は
# 6,495 要素で、全部を主語の一覧にすると誤った一致が増える。
# ---------------------------------------------------------------------------
TAXONOMY_VERSION = "2025-11-01"
TAXONOMY_DIR_DEFAULT = os.path.join(os.path.expanduser("~"), ".cache", "audit-core",
                                    "edinet-taxonomy", TAXONOMY_VERSION)

# (名前空間, ファイル名, sha256)。**字で書く。**
TAXONOMY_LABEL_FILES = (
    ("jppfs", "jppfs_2025-11-01_lab.xml",
     "bf56ea1585afe426b398a9053ec4de4dbeafc211a53675b5d6d19453e4e04bf4"),
    ("jpcrp", "jpcrp_2025-11-01_lab.xml",
     "df9c23764ec9a63cb65b5ef62e79a2907c590523797421442ea2a60e334cd684"),
)

# 採るのは**標準ラベル**の role だけ。``totalLabel`` は「流動資産合計」のように
# 合計行の言い回しで、本文の「流動資産は…」とは別物なので採らない。
STANDARD_LABEL_ROLE = "http://www.xbrl.org/2003/role/label"

_TAXONOMY_CACHE = {}


def taxonomy_dir():
    """ラベルの置き場。環境変数 ``EDINET_TAXONOMY_DIR`` で上書きできる。"""

    return os.environ.get("EDINET_TAXONOMY_DIR") or TAXONOMY_DIR_DEFAULT


def parse_label_linkbase(data, role=STANDARD_LABEL_ROLE):
    """ラベル linkbase から ``{loc の指す id: 日本語ラベル}``。

    ``loc`` -> ``labelArc`` -> ``label`` の 3 つを辿る(``label_XXX`` という
    名前から要素名を推測することはしない。``labels_from_zip`` と同じ流儀)。
    """

    root = ET.fromstring(data)
    loc_id, lab_text, arcs = {}, {}, []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "loc":
            href = el.get(XLINK + "href") or ""
            loc_id[el.get(XLINK + "label")] = href.split("#")[-1]
        elif tag == "label":
            if (el.get(XLINK + "role") or "") != role:
                continue
            if not (el.get(XML_NS + "lang") or "").startswith("ja"):
                continue
            lab_text[el.get(XLINK + "label")] = el.text or ""
        elif tag == "labelArc":
            arcs.append((el.get(XLINK + "from"), el.get(XLINK + "to")))
    out = {}
    for a, b in arcs:
        if a in loc_id and b in lab_text:
            out[loc_id[a]] = unicodedata.normalize("NFKC", lab_text[b].strip())
    return out


def _read_taxonomy_file(directory, filename, expected_sha256):
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            "no taxonomy label file at %s (see fixtures/xbrl/TAXONOMY_LABELS_README.md)" % (path,))
    data = open(path, "rb").read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha256:
        raise ValueError("taxonomy label sha256 mismatch for %s: expected %s, got %s"
                         % (filename, expected_sha256, actual))
    return data, actual


def taxonomy_label_map(namespaces=("jppfs",), directory=None):
    """``{要素の局所名: 日本語の標準ラベル}``。``namespaces`` が ``None`` なら全部。"""

    directory = directory or taxonomy_dir()
    out = {}
    for ns, filename, sha in TAXONOMY_LABEL_FILES:
        if namespaces is not None and ns not in namespaces:
            continue
        key = (os.path.join(directory, filename), sha)
        if key not in _TAXONOMY_CACHE:
            data, _actual = _read_taxonomy_file(directory, filename, sha)
            _TAXONOMY_CACHE[key] = parse_label_linkbase(data)
        for full, word in _TAXONOMY_CACHE[key].items():
            local = full.split("_cor_")[-1] if "_cor_" in full else full
            out[local] = word
    return out


def taxonomy_labels(fact_locals, namespaces=("jppfs",), directory=None):
    """``{日本語の標準ラベル: [要素の局所名, ...]}``。

    ``fact_locals`` に在る要素だけを採り、``inline_labels`` と同じ除く名前
    (長さ・``LABEL_DENY``・``【】``)を当てる。並びは要素名の順(決めておく)。
    """

    labels = taxonomy_label_map(namespaces, directory)
    found = {}
    for local in sorted(fact_locals):
        word = labels.get(local)
        if not word or len(word) < LABEL_MIN_LEN or word in LABEL_DENY:
            continue
        if "【" in word or "】" in word:
            continue
        found.setdefault(word, []).append(local)
    return found
