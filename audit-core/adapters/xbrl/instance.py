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

import html
import io
import re
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


def load_instance(zbytes):
    """xbrl_probe.py: load_instance の写し(.xbrl があればそれ、無ければ iXBRL)。"""

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
            contexts[cid] = {
                "instant": inst.text if inst is not None else None,
                "start": st.text if st is not None else None,
                "end": en.text if en is not None else None,
                "members": members,
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
                }
    return {"source": src, "facts": facts, "contexts": contexts, "textblocks": textblocks, "names": names}


def plain_context(cid, contexts):
    c = contexts.get(cid) or {}
    return not c.get("members") and "NonConsolidated" not in cid


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
