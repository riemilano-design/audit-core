# -*- coding: utf-8 -*-
"""The multiplier a Japanese money unit carries, and nothing else.

Deliberately independent of ``audit_core`` and ``adapters``: a table that
reused ``adapters/xbrl/vocabulary.py`` would make the measurement circular
(the thing being measured and the thing doing the measuring would be the
same code). This table is written from the Japanese numeral system itself,
not read out of that file.

Human decision 2026-10-08 (封, 第 2 部): "表は人が決めた数を字で留める形に
する(定数から計算して作らない。千円 = 1e3 のように1行ずつ書く)。壊したら
試験が赤くなること。" Each row below is therefore a literal integer, not a
multiplication of another row (``億円`` is not written as ``万円 * 10000``).
"""

# A money unit's scale: multiply a number written with this unit by this
# many yen to get the amount in plain 円. Units with no scale (単位あたりの
# 円 や 1 株当たりの円 など) are not listed here; :func:`scale_of` returns
# ``None`` for them, and callers must treat ``None`` as "do not multiply".
MONEY_SCALE = {
    "円": 1,
    "千円": 1000,
    "百万円": 1000000,
    "億円": 100000000,
    "兆円": 1000000000000,
}

# The accounting notation for a negative amount. Glues directly onto the
# digits with nothing in between ("△1,234千円"), so detecting it is a
# one-character lookbehind, not a parse.
NEGATIVE_MARK = "△"  # △


def scale_of(unit):
    """The multiplier for ``unit``, or ``None`` when ``unit`` carries no
    scale (including when ``unit`` is ``None``)."""
    if unit is None:
        return None
    return MONEY_SCALE.get(unit)


def scaled_value(value, unit):
    """``value`` expressed in plain 円 (or in whatever base ``unit``'s
    family uses), unsigned. Units absent from :data:`MONEY_SCALE` pass
    through unchanged -- this is what lets the same lookup be applied to a
    reference's value, which is never written in thousands or millions in
    this material (measured 2026-10-08: every reference unit in the three
    filings is ``円`` or ``円/株``, never ``千円``/``百万円``/``億円``)."""
    factor = scale_of(unit)
    if factor is None:
        return value
    return value * factor


def is_negative_mark(text, start):
    """True when ``text[start - 1]`` is the accounting negative mark, i.e.
    the digits beginning at ``start`` are glued to a preceding △."""
    return start > 0 and text[start - 1] == NEGATIVE_MARK


def signed_scaled_value(text, token):
    """:func:`scaled_value` for ``token``, sign-flipped when ``text`` marks
    it negative with a preceding △.

    This is a standalone utility for reading realistic document text (used
    by the table-driven test for this module); it is not called from
    :mod:`lib.sites`. No 円-denominated △-prefixed token exists in the
    three cached filings (measured 2026-10-08: the only △-prefixed figures
    found are percentage points, which carry no money scale), so wiring
    sign detection into the live matching path was not done -- see the
    STEP report for this scope decision.
    """
    v = scaled_value(token.value, token.unit)
    if is_negative_mark(text, token.start):
        v = -v
    return v
