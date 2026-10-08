# -*- coding: utf-8 -*-
"""Scan a document's text for numeric literals and the unit token that
follows them.

This is deliberately independent of ``adapters/xbrl/extract.py``: the
injector must not inherit the extractor's view of what counts as a number,
or an injected error would be invisible to it by construction.
"""

import re
import unicodedata

# A numeric literal: optional sign, digits with optional thousands commas,
# optional decimal part. Full-width digits are normalised before scanning.
NUM_RE = re.compile(r"(?<![0-9.,])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![0-9])")

# Unit families. A unit may only ever be swapped for another member of its
# own family (型 2 単位のずれ). Order inside a family is significant only in
# that the first element is treated as the family's canonical name.
UNIT_FAMILIES = {
    "count_move": ["手"],
    "count_game": ["局"],
    "count_position": ["局面"],
    "count_times": ["回"],
    "count_item": ["件"],
    "money": ["円", "千円", "百万円", "億円"],
    "ratio": ["%", "％", "ポイント"],  # ％ is an alias of %, see UNIT_ALIASES
    "time": ["秒", "分", "時間"],
    "point": ["点"],
}

# Notational variants of the SAME unit. Swapping between these is not an
# error, and counting it as one would make the core judge it GROUNDED and so
# push the measured detection rate down for free (measured 2026-10-08: a
# "％ -> %" injection was produced and would have counted as a miss).
UNIT_ALIASES = {"％": "%", "%": "%"}


def canonical_unit(unit):
    return UNIT_ALIASES.get(unit, unit)


def same_unit(a, b):
    """True when two unit tokens mean the same thing, however written."""
    return canonical_unit(a) == canonical_unit(b)


# Cross-family swaps that are still "単位のずれ" in the sense the human
# decision means: counting the wrong kind of thing (手 / 局 / 局面 / 回 / 件).
COUNT_FAMILY = ["手", "局", "局面", "回", "件"]

# Tokens that look like units but are calendar / ordinal markers. A number
# followed by one of these is not a measurable quantity, so it is never an
# injection site. Mirrors the intent of extract.py's EXCLUDE_AFTER without
# importing it.
NON_UNIT_AFTER = ["年", "月", "日", "期", "頁", "ページ", "四半期", "号", "条", "項", "回目", "つ目", "位", "番"]

_ALL_UNITS = sorted(
    {u for fam in UNIT_FAMILIES.values() for u in fam},
    key=len,
    reverse=True,
)


def normalize_digits(text):
    """Fold full-width digits/punctuation to ASCII, preserving length.

    Length preservation matters: spans recorded against the normalised text
    must address the same characters in the original.
    """
    out = []
    for ch in text:
        if "０" <= ch <= "９":
            out.append(chr(ord(ch) - ord("０") + ord("0")))
        elif ch == "．":
            out.append(".")
        elif ch == "，":
            out.append(",")
        else:
            out.append(ch)
    assert len(out) == len(text)
    return "".join(out)


def unit_family(unit):
    for fam, members in UNIT_FAMILIES.items():
        if unit in members:
            return fam
    return None


# This codebase writes quantities with a space: "107 局面", "25 局", "15.0 %".
# The separator is part of neither the number nor the unit, so it is skipped
# when looking for the unit and preserved when rewriting.
SEP_RE = re.compile(r"[ \u3000]*")


def _unit_after(text, pos):
    """Return (unit, end) for a unit token at/after ``pos``, else (None, pos).

    Any run of spaces between the digits and the unit is skipped; ``end`` is
    the index just past the unit token.
    """
    gap = SEP_RE.match(text, pos).end()
    rest = text[gap:]
    for bad in NON_UNIT_AFTER:
        if rest.startswith(bad):
            return None, pos
    for u in _ALL_UNITS:
        if rest.startswith(u):
            return u, gap + len(u)
    return None, pos


def unit_start_of(token):
    """Index at which ``token``'s unit begins, skipping the separator.

    Derived from ``unit_end`` so that a unit swap replaces the unit token
    only and leaves the separating space in place.
    """
    if token.unit is None:
        return None
    return token.unit_end - len(token.unit)


def parse_value(digits, frac):
    s = digits.replace(",", "")
    if frac:
        return float(s + frac)
    return float(s)


class NumberToken(object):
    """One numeric literal found in the text.

    ``start``/``end`` address the digits only (not the unit). ``unit_end``
    addresses the end of the unit token when one is present.
    """

    __slots__ = ("start", "end", "text", "value", "unit", "unit_end", "sentence_index", "has_comma", "has_frac")

    def __init__(self, start, end, text, value, unit, unit_end, sentence_index, has_comma, has_frac):
        self.start = start
        self.end = end
        self.text = text
        self.value = value
        self.unit = unit
        self.unit_end = unit_end
        self.sentence_index = sentence_index
        self.has_comma = has_comma
        self.has_frac = has_frac

    def as_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "value": self.value,
            "unit": self.unit,
            "unit_end": self.unit_end,
            "sentence_index": self.sentence_index,
        }

    def __repr__(self):
        return "NumberToken(%d:%d %r v=%r unit=%r)" % (self.start, self.end, self.text, self.value, self.unit)


# A number is a *quantity* only if it carries data. Section numbers, months,
# days, list indices and the bounds of a range all match reference values by
# coincidence, and treating them as data produced records that named a
# reference the sentence was not about (measured 2026-10-08: "4【経営者による
# 財政状態…】" was resolved to a share count, "2025年7月1日" to a remuneration
# count, "0〜1 秒" to a game count).
DATE_CONTEXT_RE = re.compile(r"(?:\d{4}\s*年|令和\s*\d+|平成\s*\d+)[^。\n]{0,12}$")
RANGE_AFTER_RE = re.compile(r"^\s*[〜~–—]")
RANGE_BEFORE_RE = re.compile(r"[〜~–—]\s*$")
HEADING_RE = re.compile(r"^\s*$")


# Japanese numeral multipliers. A digit group followed by one of these is a
# *component* of a compound amount ("394億1千9百万円" is one number written as
# 394 / 1 / 9), not a standalone quantity. Reading such an amount is exactly
# what the extractor's AMOUNT_JP_RE does, and this package may not reuse it,
# so these components are left alone instead of guessed at.
NUMERAL_MULT_RE = re.compile(r"^\s*(兆|億|千|百万|百|万|十)")
COMPOUND_LEFT_RE = re.compile(r"\d\s*(?:兆|億|万|千)\s*$")

# Digits welded to an identifier ("g02-sente.kif", "P5F"): part of a name.
IDENT_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-"
IDENT_AFTER_RE = re.compile(r"^[A-Za-z_-]")

# The first cell of a markdown table row is usually a row number. The
# exception is the observation table, where the first cell IS the value and
# the next cell holds nothing but its unit ("| 33 | 手 | ... |"). Rejecting
# that case too would be safe but would throw away good sites, so the unit
# in the following cell is used as the signal.
FIRST_CELL_RE = re.compile(r"^\s*\|\s*$")
UNIT_CELL_RE = re.compile(r"^\s*\|\s*([^\s|]{1,3})\s*\|")

# A parenthesised index: "(1）", "1(1）".
PAREN_INDEX_RE = re.compile(r"^\s*[)）]")
PAREN_LEFT_RE = re.compile(r"[((]\s*$")

# A section cross-reference: 「第5　経理の状況」/「1(1）連結財務諸表等」.
SECTION_LEFT_RE = re.compile(r"第\s*$")

# A per-unit denominator: "1株当たり当期純利益", "1ドル＝148円22銭". The number
# names the basis of a rate, not an amount that was measured.
PER_UNIT_RE = re.compile(r"^\s*(?:株|ドル|人|件|個|口|名|口座)\s*(?:当たり|あたり|＝|=)")


def is_quantity(text, token):
    """True when ``token`` looks like a measured amount rather than a label.

    False for, in order: a calendar or ordinal word after the digits; either
    bound of a range; a number inside a date; a heading or list number; a
    component of a compound Japanese amount; digits welded to an identifier;
    the first cell of a table row; and a section cross-reference.

    Every one of these was produced as an injection by an earlier version of
    this tool, each with a reference the sentence was not about.
    """
    after = text[token.end:token.end + 4]
    for bad in NON_UNIT_AFTER:
        if after.startswith(bad):
            return False
    if RANGE_AFTER_RE.match(after) or RANGE_BEFORE_RE.search(text[max(0, token.start - 3):token.start]):
        return False

    line_start = text.rfind("\n", 0, token.start) + 1
    before = text[line_start:token.start]
    if DATE_CONTEXT_RE.search(before):
        return False
    if HEADING_RE.match(before) and re.match(r"^\s*[【.．、)）]", after):
        return False

    # Component of a compound amount: a multiplier follows, AND more digits
    # follow the multiplier ("394億1千9百万円": 394 is followed by 億 then
    # another digit, so it is a component). When the multiplier is itself
    # the tail of a money unit (千円/百万円/億円 -- the only members of
    # UNIT_FAMILIES["money"] that begin with a multiplier character), the
    # token is a complete standalone quantity, not a component: "105,873千円"
    # and "10億円" must not be excluded here (measured 2026-10-08: they were,
    # 100% of the time, because 千/億 also happen to be multiplier markers).
    # A multiplier embedded deeper in a compound ("1千9百万円") is still
    # caught by the left-context check below.
    m = NUMERAL_MULT_RE.match(after)
    if m:
        tail = after[m.end():]
        if not tail.startswith("円"):
            return False
    if COMPOUND_LEFT_RE.search(text[max(0, token.start - 14):token.start]):
        return False

    # Welded to an identifier on either side.
    if token.start > 0 and text[token.start - 1] in IDENT_CHARS:
        return False
    if IDENT_AFTER_RE.match(after):
        return False

    if FIRST_CELL_RE.match(before):
        m = UNIT_CELL_RE.match(text[token.end:token.end + 12])
        if not (m and unit_family(m.group(1))):
            return False
    if SECTION_LEFT_RE.search(before):
        return False
    if PER_UNIT_RE.match(text[token.end:token.end + 10]):
        return False
    # A parenthesised index, and a number that opens one ("1(1）").
    if PAREN_INDEX_RE.match(after) and PAREN_LEFT_RE.search(before):
        return False
    if re.match(r"^\s*[((]", after):
        return False
    return True


SENT_END = "。\n"


def sentence_spans(text):
    """Split into sentences on 。 and newlines, returning (start, end) spans
    that tile the whole text."""
    spans = []
    start = 0
    for i, ch in enumerate(text):
        if ch in SENT_END:
            if i + 1 > start:
                spans.append((start, i + 1))
            start = i + 1
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def scan(text):
    """Return the list of :class:`NumberToken` in ``text``.

    ``text`` must already be digit-normalised by :func:`normalize_digits`.
    """
    spans = sentence_spans(text)
    tokens = []
    for m in NUM_RE.finditer(text):
        digits, frac = m.group(1), m.group(2)
        end = m.end()
        unit, unit_end = _unit_after(text, end)
        si = next((i for i, (a, b) in enumerate(spans) if a <= m.start() < b), -1)
        tokens.append(
            NumberToken(
                start=m.start(),
                end=end,
                text=m.group(0),
                value=parse_value(digits, frac),
                unit=unit,
                unit_end=unit_end,
                sentence_index=si,
                has_comma="," in digits,
                has_frac=frac is not None,
            )
        )
    return tokens


def render_value(value, like):
    """Render ``value`` in the surface form of the token ``like``.

    Keeping the surface form (thousands commas, one decimal place) matters:
    an injected error must differ from the original in its *value*, not in a
    typographic tell that would let the decomposer spot it for free.
    """
    if like.has_frac:
        places = len(like.text.split(".")[1])
        s = "%.*f" % (places, value)
    else:
        s = "%d" % (int(round(value)),)
    if like.has_comma:
        neg = s.startswith("-")
        body = s[1:] if neg else s
        intpart, _, rest = body.partition(".")
        chunks = []
        while len(intpart) > 3:
            chunks.insert(0, intpart[-3:])
            intpart = intpart[:-3]
        chunks.insert(0, intpart)
        body = ",".join(chunks) + (("." + rest) if rest else "")
        s = ("-" if neg else "") + body
    return s
