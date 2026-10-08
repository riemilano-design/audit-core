# -*- coding: utf-8 -*-
"""Swap exactly one unit word inside a document's MD&A text block, leaving
every digit and every other byte of the ZIP untouched.

Built for the 封 ``audit-core/docs/DETECTION_T2_PLAN_2026-10-08.md`` 第 1 部
(段 3/段 4, 型 2 のみの検出率). Not Core, not an Adapter change: this reads
``adapters.xbrl.instance.select_mdna`` (to pick the *same* text block the
real pipeline uses) but never imports ``audit_core`` and never writes to
``~/.cache/audit-core/edinet/``.

Why the search happens on *raw*, undecoded bytes
--------------------------------------------------
``adapters.xbrl.instance.load_instance`` returns the MD&A text block already
XML-entity-decoded (and, for the iXBRL branch, taken verbatim from the raw
``.htm``). Neither form carries byte offsets back into the ZIP. Rather than
build a plaintext-span -> HTML-position map (fragile: the two differ exactly
where an entity or a tag sits), this module relocates the chosen text block
directly inside the *raw* entry bytes, independently of
``adapters.xbrl.instance`` (the same discipline ``measure/prepare_material.py``
already uses, for the same reason: a locator shared with the thing being
measured could hide a site the real pipeline also misses).

The uniqueness check that decides whether a site is usable therefore runs
against the untouched raw bytes, entities and tags included -- exactly the
text the plan calls "HTML": a number+unit pair that is split by a tag, or
whose ``&amp;`` has not been unescaped, will not match and the site is
reported unusable rather than forced.

Only the ``.xbrl`` instance branch is implemented. The 3 documents this
fixture measures all carry one (confirmed: ``measure/prepare_material.py``
already requires it and has produced material for all 3). An iXBRL-only
filing raises :class:`NoInstance` rather than being silently mishandled.
"""

import io
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from adapters.xbrl import instance as I  # noqa: E402

# Mirrors measure/prepare_material.py's XBRLI_TAG_RE-adjacent technique: a
# text block is found by its *local* element name, with a backreference to
# the same local name's closing tag, so the (unknown ahead of time) namespace
# prefix never has to be resolved. Not imported from prepare_material.py
# (that script may not be imported by anything that touches adapters/ --
# see its own module docstring) and not imported from instance.py (it has no
# raw-offset-returning entry point at all). Written independently here.
_TEXTBLOCK_RE = re.compile(r"<(?:[\w\-]+:)?(\w*TextBlock)\b([^>]*)>(.*?)</(?:[\w\-]+:)?\1>", re.S)

_SEP_RE_SRC = r"[ 　]*"

# REVISE 2026-10-08(独立監査、1 回目): find_unit_site の正規表現に数字側の
# 左の境界が無く、短い数字が長い数字の末尾に多重一致していた(「149百万円」
# が「1,149百万円」に当たる等)。adapters/xbrl/extract.py の NUM_RE が持つ
# ``(?<![\d.,])`` 相当を、全角の数字・カンマ・ピリオドも含めて足す。
_NUM_LEFT_BOUNDARY_SRC = r"(?<![0-9.,０-９，．])"

# 全角 -> 半角の逆写像。measure/lib/numbers.py:normalize_digits は全角の数字・
# カンマ・ピリオドを半角へ畳むので、t2_sites の token.text は既に半角だが、
# raw HTML はまだ全角のままの場合がある(実測 2026-10-08: S100Z4Q1 の
# 「３億円」)。unit 側の _unit_text_variants(run_detection_t2.py)と対にな
# る、数字側の両形探索。
_HALF_TO_FULLWIDTH = {
    "0": "０", "1": "１", "2": "２", "3": "３", "4": "４",
    "5": "５", "6": "６", "7": "７", "8": "８", "9": "９",
    ",": "，", ".": "．",
}


def _number_text_variants(number_text):
    """``number_text``(半角に畳まれた形)と、その全角書き起こしの両方を返す
    (差が無ければ 1 件だけ)。"""

    fullwidth = "".join(_HALF_TO_FULLWIDTH.get(ch, ch) for ch in number_text)
    return sorted({number_text, fullwidth})


class TamperError(RuntimeError):
    """Base class for the reasons a document/site cannot be tampered."""


class NoInstance(TamperError):
    """No ``.xbrl`` instance entry was found inside the ZIP."""


class NoMdnaTextblock(TamperError):
    """``adapters.xbrl.instance.select_mdna`` named a text block that this
    module's independent raw-byte locator could not find in the instance
    entry (the two disagree on what is inside the ZIP)."""


class AmbiguousSite(TamperError):
    """The requested number+unit text did not occur exactly once inside the
    MD&A text block's raw bytes. Carries the match count so callers can
    distinguish "0 (hidden behind a tag/entity)" from "2+ (genuinely
    repeated in the document)"."""

    def __init__(self, message, match_count):
        super().__init__(message)
        self.match_count = match_count


def _xbrl_instance_entry(names):
    inst = [n for n in names if n.endswith(".xbrl") and "PublicDoc" in n]
    if not inst:
        inst = [n for n in names if n.endswith(".xbrl")]
    if not inst:
        raise NoInstance("no .xbrl instance entry inside the ZIP (names: %r)" % (names[:20],))
    return inst[0]


def mdna_name(zb):
    """The text block name ``adapters.xbrl.instance.select_mdna`` picks for
    this ZIP (``None`` if the document carries no MD&A block at all)."""

    z = zipfile.ZipFile(io.BytesIO(zb))
    inst = I.load_instance(zb)
    return I.select_mdna(inst["textblocks"])


def locate_mdna_raw(zb):
    """Find the MD&A text block inside the raw ``.xbrl`` instance bytes.

    Returns ``(entry_name, raw_text, inner_start, inner_end, local_name)``
    where ``raw_text[inner_start:inner_end]`` is the text block's content
    exactly as it sits in the ZIP (undecoded: entities and nested escaped
    tags, if any, are left as literal substrings).

    Raises :class:`NoInstance` if there is no ``.xbrl`` entry, or
    :class:`NoMdnaTextblock` if ``select_mdna``'s choice cannot be found by
    this module's independent, local-name-based regex.
    """

    z = zipfile.ZipFile(io.BytesIO(zb))
    names = z.namelist()
    entry = _xbrl_instance_entry(names)
    raw = z.read(entry).decode("utf-8")

    name = mdna_name(zb)
    if name is None:
        raise NoMdnaTextblock("adapters.xbrl.instance.select_mdna found no MD&A text block")
    local = name.split(":")[-1]

    first_by_local = {}
    for m in _TEXTBLOCK_RE.finditer(raw):
        if m.group(1) not in first_by_local:
            first_by_local[m.group(1)] = m
    m = first_by_local.get(local)
    if m is None:
        raise NoMdnaTextblock(
            "select_mdna chose %r but no <...%s...>...</...> was found in %s "
            "(local text block names seen: %r)" % (name, local, entry, sorted(first_by_local)[:20])
        )
    return entry, raw, m.start(3), m.end(3), local


def find_unit_site(inner, number_text, unit):
    """Locate the single occurrence of ``number_text`` immediately (modulo a
    run of spaces) followed by ``unit`` inside ``inner`` (raw, undecoded
    bytes of the MD&A text block).

    ``number_text`` is matched with a left boundary (no digit/comma/period,
    half- or full-width, immediately before it) so a short number cannot
    match as the tail of a longer one (「149百万円」 inside 「1,149百万円」),
    and both the half-width form (what ``measure/lib/numbers.py`` already
    folded ``number_text`` to) and its full-width rendering are tried (the
    raw HTML may still hold the original full-width digits). There is no
    right-side boundary requirement beyond "the unit follows": a longer
    number never falsely matches a shorter prefix, because the characters
    right after ``number_text`` would then not be ``unit`` and the whole
    pattern fails to match at that position.

    Returns ``(unit_start, unit_end)`` -- the span of the unit word alone,
    so a caller can replace exactly that substring and leave the digits and
    everything else untouched.

    Raises :class:`AmbiguousSite` when the pairing occurs 0 or 2+ times
    (counting across both width forms together -- it is the same number
    however it is written).
    """

    alt = "|".join(re.escape(v) for v in _number_text_variants(number_text))
    pat = re.compile(_NUM_LEFT_BOUNDARY_SRC + r"(?:" + alt + r")" + _SEP_RE_SRC + re.escape(unit))
    matches = list(pat.finditer(inner))
    if len(matches) != 1:
        raise AmbiguousSite(
            "expected exactly 1 occurrence of %r + unit %r inside the MD&A text block, found %d"
            % (number_text, unit, len(matches)),
            len(matches),
        )
    m = matches[0]
    unit_end = m.end()
    unit_start = unit_end - len(unit)
    return unit_start, unit_end


def _replace_zip_entry(zb, entry_name, new_data):
    """Return new ZIP bytes with ``entry_name``'s content replaced by
    ``new_data``. Every other entry's *content* (``ZipFile.read`` output) is
    carried over unchanged; this is the invariant the tests check, not
    byte-identical local-file-header placement (the ZIP container itself is
    rebuilt, since Python's ``zipfile`` has no in-place-edit API)."""

    src = zipfile.ZipFile(io.BytesIO(zb))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = new_data if info.filename == entry_name else src.read(info.filename)
            new_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new_info.compress_type = info.compress_type
            new_info.external_attr = info.external_attr
            new_info.create_system = info.create_system
            dst.writestr(new_info, data)
    return buf.getvalue()


def tamper_unit_word(zb, number_text, old_unit, new_unit):
    """Return new ZIP bytes where, inside the MD&A text block only, the one
    occurrence of ``number_text`` + ``old_unit`` has its unit word replaced
    by ``new_unit``. The digits (``number_text``) are copied through
    unchanged. Every other byte of every other ZIP entry is unchanged.

    Raises :class:`NoInstance` / :class:`NoMdnaTextblock` / :class:`AmbiguousSite`
    (the last carrying ``match_count``) instead of guessing.
    """

    entry, raw, start, end, _local = locate_mdna_raw(zb)
    inner = raw[start:end]
    unit_start, unit_end = find_unit_site(inner, number_text, old_unit)
    new_inner = inner[:unit_start] + new_unit + inner[unit_end:]
    new_raw = raw[:start] + new_inner + raw[end:]
    return _replace_zip_entry(zb, entry, new_raw.encode("utf-8"))
