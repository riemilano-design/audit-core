# -*- coding: utf-8 -*-
"""Python re-implementation of ``scripts/playtest/lib/observationPacket.ts``'s
``canonicalJson`` (not imported -- read-only reference; see the package
docstring), to the degree C-2 needs: key order, number formatting
(integers, decimals, ``-0``, exponential notation), string escaping
(no ``ensure_ascii``), ``null``/``true``/``false``.

``canonicalJson`` itself is:

    export function canonicalJson(value: unknown): string {
      if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
      if (value !== null && typeof value === "object") {
        const entries = Object.keys(value as Record<string, unknown>)
          .sort()
          .map((key) => `${JSON.stringify(key)}:${canonicalJson((value as Record<string, unknown>)[key])}`);
        return `{${entries.join(",")}}`;
      }
      return JSON.stringify(value) ?? "null";
    }

For objects/arrays/strings/null/booleans this is a direct transcription.
The one nontrivial part is **numbers**: ``JSON.stringify`` on a JS
number formats it via the ECMA-262 ``Number::toString`` algorithm (the
shortest decimal digit string that round-trips to the same IEEE-754
double, laid out as a plain integer / fixed decimal / exponential form
depending on the decimal-point position ``n`` relative to the digit
count ``k``), which **does not match** Python's ``repr(float)`` or
``json.dumps`` formatting verbatim (e.g. Python keeps ``100.0`` as
``"100.0"``; JS's ``100`` -- there is no float/int distinction in JS --
stringifies to ``"100"``). ``_format_number`` below re-implements the
ECMA-262 layout rules directly: it gets the canonical (shortest,
trailing-zero-stripped) significant-digit string ``digit_str`` and
decimal-point position ``n`` from ``repr()`` (for a Python ``float``,
``repr()`` already produces the shortest round-trip digit string, by
the same "round-trips to this IEEE-754 double" property JS's algorithm
uses -- only the *layout* differs, not the digits) or directly from the
``Decimal`` of a plain ``int`` (exact, no float round-trip needed),
then lays them out per ECMA-262 9.8.1 step 6's four cases (plain
integer / embedded point / leading-zero decimal / exponential).

This was checked empirically against the real ``canonicalJson`` (not
guessed): ``npx tsx`` was used to call the actual TypeScript function on
a battery of 37 values (0, -0, 1, -1, 1.5, -1.5, 100, 1_000_000,
-1_000_000, 0.001 through 1e-7 (crossing the exponential threshold),
1e20/1e21/1e22 (crossing the other exponential threshold),
123456789012345680000, 5.8, -5.8, a long-decimal float
(53.333333333333336), 300, -300, 0.5, 12.34, 9999999999999998,
2**53, plain/Japanese/quote/backslash/control-char/newline strings,
and nested arrays/objects with out-of-order keys) and this module's
output matched all 37, value for value (recorded in the implementer's
report for this STEP; the probe scripts are not checked in -- scratch
material under the session's scratchpad, not project material).

**Known, undefensed gap** (shogi observation values never approach
this range, so it is left unhandled rather than guessed at): for a
plain Python ``int`` whose magnitude exceeds 2**53, this module formats
the *exact* integer, whereas a JS number is always an IEEE-754 double
and would first round such an integer to the nearest representable
double before ``Number::toString`` ever sees it. ``NaN``/``Infinity``
(never produced by ``json.load`` on valid JSON, so not exercised by
real packet/envelope material either) are mapped to ``"null"``,
matching ``JSON.stringify(NaN)`` / ``JSON.stringify(Infinity)``.
"""

import json
import math
from decimal import Decimal


def _canonical_digits(ax):
    """``ax``: a positive ``int`` or ``float``. Returns ``(digit_str, n)``
    where ``digit_str`` has no trailing zero and represents the value as
    ``int(digit_str) * 10 ** (n - len(digit_str))`` (ECMA-262's ``s`` and
    ``n``, with ``k = len(digit_str)``)."""

    if isinstance(ax, int):
        d = Decimal(ax)
    else:
        d = Decimal(repr(ax))
    _sign, digits, exp = d.as_tuple()
    digits = list(digits)
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()
        exp += 1
    k = len(digits)
    n = exp + k
    digit_str = "".join(str(dd) for dd in digits)
    return digit_str, n


def _format_number(x):
    """ECMA-262 ``Number::toString`` layout (9.8.1 step 6), given the
    canonical digit string/point position from ``_canonical_digits``."""

    if x == 0:
        return "0"
    neg = x < 0
    ax = -x if neg else x
    digit_str, n = _canonical_digits(ax)
    k = len(digit_str)
    if k <= n <= 21:
        s = digit_str + "0" * (n - k)
    elif 0 < n <= 21:
        s = digit_str[:n] + "." + digit_str[n:]
    elif -6 < n <= 0:
        s = "0." + "0" * (-n) + digit_str
    else:
        mantissa = digit_str if k == 1 else digit_str[0] + "." + digit_str[1:]
        exp_val = n - 1
        s = mantissa + "e" + ("+" if exp_val >= 0 else "-") + str(abs(exp_val))
    return ("-" + s) if neg else s


def canonical_json(value):
    """Transcription of ``canonicalJson``. Keys sorted; arrays keep their
    own order (array order is part of the fact, per the TS docstring)."""

    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return "null"
    if isinstance(value, (int, float)):
        return _format_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(canonical_json(v) for v in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value.keys())
        parts = [json.dumps(k, ensure_ascii=False) + ":" + canonical_json(value[k]) for k in keys]
        return "{" + ",".join(parts) + "}"
    raise TypeError("canonical_json: unsupported type %r" % (type(value),))
