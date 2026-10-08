# -*- coding: utf-8 -*-
"""型 3(原文に無い数): insert a sentence about a subject the document's data
does not contain, immediately after a ``。`` inside the MD&A text block's
raw (undecoded) HTML -- never inside a tag.

Built for the 封 ``audit-core/docs/DETECTION_T1_T3_PLAN_2026-10-08.md`` 第 3
部(型 3). Sibling of ``tamper_unit.py``/``tamper_value.py``, reusing the
same ZIP/MD&A machinery:

- :func:`tamper_unit.locate_mdna_raw` / :func:`tamper_unit._replace_zip_entry`
  -- find and rewrite the MD&A text block's raw bytes (imported, not
  re-derived).
- :func:`measure.inject.build_t3` -- the sentence/subject/value construction
  itself (imported, not re-derived): a template from
  ``measure/lib/sites.py: ABSENT_TEMPLATES["xbrl"]``, with a subject and a
  value neither of which appears in the reference numbers.
- :func:`measure.lib.sites.t3_sites` -- used only for its already-screened
  ``templates`` list (a subject dropped there if it turns up in the text or
  in a reference label is never offered to :func:`build_sentence`). Its own
  anchor list (plain-text sentence spans) is **not** used: this module finds
  its own anchors in the *raw HTML*, because a plain-text sentence boundary
  and a raw-HTML ``。`` do not share offsets (same reason
  ``tamper_unit.py``'s module docstring gives for not building a
  plaintext-span -> HTML-position map).

What is new here:

1. :func:`find_insertion_points` -- every ``。`` inside the MD&A raw HTML
   that is not inside a tag, excluding the first and last (mirrors
   ``lib.sites.t3_sites``'s own "not a heading, not the very end" rule,
   applied to raw-HTML anchors instead of plain-text sentence spans).
2. :func:`build_sentence` -- a thin wrapper around ``inject.build_t3`` that
   does not need a real ``t3_sites`` site dict (only ``templates``).
3. :func:`insert_sentence` -- splice the sentence into the raw HTML at one
   insertion point.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if os.path.join(ROOT, "measure") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "measure"))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from lib import sites as S  # noqa: E402
import inject as INJ  # noqa: E402

from tamper_unit import (  # noqa: E402,F401
    TamperError, NoInstance, NoMdnaTextblock, locate_mdna_raw, _replace_zip_entry,
)


class NoUsableSubject(TamperError):
    """Every subject in ``ABSENT_TEMPLATES["xbrl"]`` turns up in this
    document's text or reference labels (封 §3-2: ``ABSENT_TEMPLATES`` has
    exactly 6 subjects; dropping one is not guessed around)."""


class NoInsertionPoint(TamperError):
    """No usable ``。``-boundary (not inside a tag, not the first/last)
    was found inside the MD&A raw HTML."""


def usable_templates(text, refs, kind="xbrl"):
    """The subset of ``lib.sites.ABSENT_TEMPLATES[kind]`` that
    :func:`lib.sites.t3_sites` would offer for this document (subject absent
    from both ``text`` and every reference's label). Reuses ``t3_sites``
    itself rather than re-deriving the filter; falls back to an empty list
    only when ``t3_sites`` finds no raw-HTML-independent anchor at all (a
    single-sentence document), in which case the caller cannot proceed
    either way."""

    sites = S.t3_sites(text, refs, kind)
    if not sites:
        return []
    return sites[0]["templates"]


def find_insertion_points(inner):
    """Every character offset inside ``inner`` (the MD&A text block's raw,
    undecoded bytes) that sits immediately after a ``。`` which is not
    itself inside an HTML tag (tracked by a simple ``<``/``>`` state
    machine -- the same discipline the rest of this module's siblings use:
    read the raw bytes, do not assume entities are decoded).

    Excludes the first and last such offset (mirrors ``lib.sites.t3_sites``:
    "not a heading, not the very end"). Returns a sorted list of offsets;
    may be empty."""

    points = []
    in_tag = False
    for i, ch in enumerate(inner):
        if ch == "<":
            in_tag = True
        elif ch == ">":
            in_tag = False
        elif ch == "。" and not in_tag:
            points.append(i + 1)
    if len(points) <= 2:
        return []
    return points[1:-1]


def build_sentence(templates, refs, rng, used_subjects, used_values):
    """Thin wrapper around ``measure.inject.build_t3``: that function reads
    only ``site["templates"]`` from its ``site`` argument (see its own
    docstring), so a minimal dict carrying just that key stands in for a
    real ``lib.sites.t3_sites`` site (whose other keys -- ``"at"`` -- name a
    plain-text position this module does not use). Returns ``build_t3``'s
    dict (``"replacement"``/``"detail"``/...) or ``None`` when every
    template's subject has already been used (``build_t3``'s own
    exhaustion signal)."""

    # build_t3 also reads ``site["at"]`` to fill the span it returns
    # (``"span": [site["at"], site["at"]]``); this module never uses that
    # span (its own insertion position comes from
    # :func:`find_insertion_points`, a raw-HTML offset, not a plain-text
    # one), so the value is a placeholder.
    site = {"templates": templates, "at": 0}
    return INJ.build_t3(site, refs, rng, used_subjects, used_values)


def insert_sentence(zb, position_in_inner, sentence_text):
    """Return new ZIP bytes with ``sentence_text`` spliced into the MD&A
    text block's raw bytes at ``position_in_inner`` (an offset returned by
    :func:`find_insertion_points`, i.e. immediately after a ``。`` outside
    any tag). Every other byte of every other ZIP entry is unchanged."""

    entry, raw, start, end, _local = locate_mdna_raw(zb)
    inner = raw[start:end]
    new_inner = inner[:position_in_inner] + sentence_text + inner[position_in_inner:]
    new_raw = raw[:start] + new_inner + raw[end:]
    return _replace_zip_entry(zb, entry, new_raw.encode("utf-8"))
