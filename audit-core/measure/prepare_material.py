# -*- coding: utf-8 -*-
"""Prepare one document for injection: its text, and the reference numbers
that the underlying data contains.

Two deliberate constraints:

* **Nothing here imports ``audit_core`` or ``adapters``.** Reading the XBRL
  ZIP is reimplemented with the standard library. If this script shared the
  extractor's code, an injected error that the extractor cannot see would be
  invisible to the injector too, and the measurement would be circular
  (human decision 2026-10-08 第 2 便 §穴 2 (3)).
* **The output is called a reference number list, never a gold set.** The
  underlying data says what the facts are, not what a sentence claims. It is
  used to choose *which* value to inject, and never to score anything
  (same decision, consequence (b)).

Usage::

    python3 prepare_material.py shogi --booklet <md> --packet <json> --out <dir>
    python3 prepare_material.py xbrl --zip <zip> --doc <docID> --out <dir>
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import numbers as N  # noqa: E402

# Packet aggregates carry English unit names; the booklet writes Japanese.
SHOGI_UNIT_JA = {"moves": "手", "games": "局", "positions": "局面"}

# The shogi booklet and its observation packet are customer data (the
# booklet IS the customer's diagnosis report; the packet backs every number
# in it). Neither is committed to this repository -- only its sha256 is
# (``material/shogi/SOURCE.sha256``). The default read location mirrors
# ``inject.py``'s ``DEFAULT_RECORD_DIR``: outside the working tree, under
# the home directory. A session working in this repo therefore cannot read
# the customer's data unless it has already been placed there by hand.
# 2026-10-08 司令塔の判断: 人間は packet だけを名指ししたが、booklet も同じ
# 理由(顧客のデータ)が当たるため、同じ扱いに広げた。
EXTERNAL_MATERIAL_DIR = os.path.join(os.path.expanduser("~"), ".audit-core-measure", "material")
DEFAULT_SHOGI_BOOKLET = os.path.join(EXTERNAL_MATERIAL_DIR, "shogi", "c5_round5_booklet.md")
DEFAULT_SHOGI_PACKET = os.path.join(EXTERNAL_MATERIAL_DIR, "shogi", "c5_observation_packet.json")


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _write(out_dir, doc_id, text, refs, provenance):
    os.makedirs(out_dir, exist_ok=True)
    tpath = os.path.join(out_dir, "%s.original.txt" % doc_id)
    with io.open(tpath, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    rpath = os.path.join(out_dir, "%s.reference_numbers.json" % doc_id)
    payload = {
        "note": (
            "参照用の数の一覧。正解集合ではない。元データが教えるのは「何が事実か」で、"
            "「その文が何を主張しているか」ではない(2026-10-08 第 2 便 穴 2)。"
            "採点には使わない。混入する値を選ぶためだけに使う。"
        ),
        "document_id": doc_id,
        "provenance": provenance,
        "refs": refs,
    }
    with io.open(rpath, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("text  -> %s (%d chars)" % (tpath, len(text)))
    print("refs  -> %s (%d refs)" % (rpath, len(refs)))
    return tpath, rpath


def prepare_shogi(args):
    raw = io.open(args.booklet, encoding="utf-8").read()
    text = N.normalize_digits(raw)
    packet = json.load(io.open(args.packet, encoding="utf-8"))

    refs = []
    for a in packet.get("aggregates", []):
        unit = SHOGI_UNIT_JA.get(a.get("unit"), a.get("unit"))
        base = {"source_key": a["id"], "label": a.get("name"), "unit": unit}
        if "value" in a:
            refs.append(dict(base, key="%s.value" % a["id"], value=float(a["value"]), role="value"))
        if "numerator" in a:
            refs.append(dict(base, key="%s.numerator" % a["id"], value=float(a["numerator"]), role="numerator"))
        if "denominator" in a:
            refs.append(dict(base, key="%s.denominator" % a["id"], value=float(a["denominator"]), role="denominator"))

    # Per-game plies are facts the booklet can legitimately cite.
    for g in packet.get("facts", {}).get("games", []):
        refs.append({
            "key": "games.%s.totalPlyCount" % g["gameId"],
            "source_key": g["gameId"],
            "label": "%s の総手数" % g["gameId"],
            "unit": "手",
            "value": float(g["totalPlyCount"]),
            "role": "value",
        })

    prov = {
        "kind": "shogi_booklet",
        "booklet": os.path.basename(args.booklet),
        "booklet_sha256": sha256_file(args.booklet),
        "packet": os.path.basename(args.packet),
        "packet_sha256": sha256_file(args.packet),
        "packet_id": packet.get("packetId"),
    }
    return _write(args.out, args.doc or "shogi-c5", text, refs, prov)


class _Stripper(HTMLParser):
    """Minimal HTML-to-text. Independent of adapters/xbrl/instance.py."""

    def __init__(self):
        HTMLParser.__init__(self)
        self.buf = []

    def handle_data(self, d):
        self.buf.append(d)

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "div", "tr", "table"):
            self.buf.append("\n")

    def text(self):
        return re.sub(r"\n{3,}", "\n\n", "".join(self.buf))


def strip_html(s):
    p = _Stripper()
    p.feed(s)
    return p.text()


# 直し 2026-10-08(封 第 2 部): "1 株当たりの金額" と "総額" は同じ族で
# あってはならない。両方とも unitRef が "JPY" で始まるため、元の
# ``.upper().startswith("JPY")`` 判定は "JPYPerShares" も "円" に丸めて
# いた(実測: 3 書類に 41/40/41 件)。これにより、スケールを掛けた総額の
# トークンが、別の事実である 1 株当たり指標に偶然一致しうる経路が生まれる。
# ``JPYPerShares`` を先に見分け、総額の "円" とは異なる単位名にする。
# 他の unitRef 変種は実測していない(今回の 3 書類には "JPY" と
# "JPYPerShares" の 2 つしか無い)。
PER_SHARE_UNIT_LABEL = "円/株"


def _money_unit_label(unit):
    u = (unit or "").upper()
    if u == "JPYPERSHARES":
        return PER_SHARE_UNIT_LABEL
    if u.startswith("JPY"):
        return "円"
    return unit or None


# The opening tag's attribute string is captured once (group 2), and
# ``contextRef=`` / ``unitRef=`` are each located inside it with a separate
# ``re.search``. Matching both attributes with one pattern and a greedy
# ``[^>]*`` run between them does not work: EDINET tags interleave an
# unrelated attribute between the two (``contextRef="..." decimals="-3"
# unitRef="JPY">``), and because the ``unitRef`` group was optional, the
# preceding greedy ``[^>]*`` consumed the whole remainder of the tag --
# ``unitRef`` included -- before the engine ever needed the optional group
# to try, so it always matched empty (measured 2026-10-08: 3/3 documents,
# every one of 824/922/994 refs had ``unit=None``).
XBRLI_TAG_RE = re.compile(
    r"<(?:[\w-]+:)?(\w+)\b([^>]*)>"
    r"\s*(-?[\d,]+(?:\.\d+)?)\s*</",
)
_CONTEXTREF_ATTR_RE = re.compile(r"\bcontextRef=\"([^\"]+)\"")
_UNITREF_ATTR_RE = re.compile(r"\bunitRef=\"([^\"]+)\"")


def prepare_xbrl(args):
    """Read the cached EDINET ZIP with the standard library only.

    The MD&A text block is located the same way the Adapter locates it (a
    ``ManagementAnalysis...TextBlock`` element), but by independent code.
    """
    with zipfile.ZipFile(args.zip) as z:
        names = z.namelist()
        inst = [n for n in names if n.endswith(".xbrl") and "PublicDoc" in n]
        if not inst:
            inst = [n for n in names if n.endswith(".xbrl")]
        if not inst:
            raise SystemExit("no .xbrl instance inside %s" % args.zip)
        raw = z.read(inst[0]).decode("utf-8", "replace")

    tb = {}
    for m in re.finditer(r"<(?:[\w-]+:)?(\w*TextBlock)\b[^>]*>(.*?)</(?:[\w-]+:)?\1>", raw, re.S):
        tb.setdefault(m.group(1), m.group(2))
    name = next((n for n in tb if "ManagementAnalysis" in n), None)
    if name is None:
        name = next((n for n in tb if "AnalysisOfFinancialPosition" in n or "OverviewOfBusinessResults" in n), None)
    if name is None:
        raise SystemExit("no MD&A text block in %s; blocks: %s" % (args.zip, sorted(tb)[:10]))

    import html as _html
    body = _html.unescape(tb[name])
    text = N.normalize_digits(strip_html(body))
    text = re.sub(r"[ \t　]+\n", "\n", text).strip() + "\n"

    refs = []
    seen = set()
    for m in XBRLI_TAG_RE.finditer(raw):
        elem, attrs, val = m.group(1), m.group(2), m.group(3)
        if elem.endswith("TextBlock"):
            continue
        cm = _CONTEXTREF_ATTR_RE.search(attrs)
        if cm is None:
            continue
        ctx = cm.group(1)
        um = _UNITREF_ATTR_RE.search(attrs)
        unit = um.group(1) if um else None
        try:
            v = float(val.replace(",", ""))
        except ValueError:
            continue
        key = "%s@%s" % (elem, ctx)
        if key in seen:
            continue
        seen.add(key)
        refs.append({
            "key": key,
            "source_key": elem,
            "label": elem,
            "unit": _money_unit_label(unit),
            "value": v,
            "role": "value",
            "context": ctx,
        })

    prov = {
        "kind": "xbrl_mdna",
        "zip": os.path.basename(args.zip),
        "zip_sha256": sha256_file(args.zip),
        "instance": inst[0],
        "text_block": name,
    }
    return _write(args.out, args.doc, text, refs, prov)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("shogi")
    s.add_argument("--booklet", default=DEFAULT_SHOGI_BOOKLET,
                    help="default: %s (customer data, outside the repo; a missing file raises "
                         "FileNotFoundError rather than being skipped)" % DEFAULT_SHOGI_BOOKLET)
    s.add_argument("--packet", default=DEFAULT_SHOGI_PACKET,
                    help="default: %s (same treatment as --booklet)" % DEFAULT_SHOGI_PACKET)
    s.add_argument("--doc", default=None)
    s.add_argument("--out", required=True)
    s.set_defaults(fn=prepare_shogi)

    x = sub.add_parser("xbrl")
    x.add_argument("--zip", required=True)
    x.add_argument("--doc", required=True)
    x.add_argument("--out", required=True)
    x.set_defaults(fn=prepare_xbrl)

    args = ap.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
