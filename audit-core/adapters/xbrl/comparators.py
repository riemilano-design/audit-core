# -*- coding: utf-8 -*-
"""The six comparators C-1d §3.1 fixes, registered under ``register_all``
(see :mod:`registry_setup`).

Each comparator reads only the already-resolved ``evidence`` (a tuple of
Core ``Resolved`` objects, in the order the Recipe's ``xbrl:`` pointers
were listed), ``claim.value`` and ``contract.params``. This module does
**not** import :mod:`vocabulary`, :mod:`instance` or :mod:`extract`: the
one piece of XBRL-adjacent logic it needs (the round/truncate/abs ladder
that decides whether a fact matches a target within one unit's rounding)
is kept local as ``_match_value`` -- a value-for-value copy of
``vocabulary.match_value`` / the original ``xbrl_probe.py: match_value``
(C-1d task §A: "同じ梯子を comparators に写すか...写すなら系譜の試験に値比較を
1 本足す" -- copied; see ``test_lineage.py:
test_match_value_also_matches_comparators_copy``).

The three "原本の癖" identified by C-1d prediction §3.1: (a) and (b) were
**fixed** by C-1f (2026-10-06, per ``CORE_CONNECTION_C1F_PREDICTION``);
(c) is left as-is (reproduced without correction). (a) ``equals_within
(pure*100)`` and ``ratio*100`` now compare the recomputed number to the
**signed** ``claim.value`` (previously compared to ``abs(claim.value)``,
which let a negative claim such as "△5.8%" match a positive 5.8 fact);
(b) ``builtin:sign(cur-prior)==direction`` now treats a difference of
exactly 0 as neither an increase nor a decrease (``actual = 0``, which
matches neither ``direction=1`` nor ``direction=-1``) -- previously
``actual = -1`` when ``diff == 0`` (counted as a "decrease"), same as
the original's ``1 if diff > 0 else -1``; (c) a zero ``prior`` is never
passed to ``ratio*100`` / ``pct_change(cur,prior)`` by this Adapter (the
raw-claim builder short-circuits to ``unverifiable_reason="prior is 0"``
before a Contract is ever built for that Claim), so those two comparators
do not guard against a zero denominator themselves.
"""

import audit_core as core


def _match_value(fact_value, target, unit):
    """Copy of ``vocabulary.match_value`` / ``xbrl_probe.py: match_value``.

    round    : |fact - target| <= unit/2
    truncate : 0 <= fact - target < unit
    abs+...  : same two checks with both sides' sign dropped
    Returns one of "round" / "truncate" / "abs+round" / "abs+truncate",
    or ``None`` if neither check passes in either sign mode.
    """

    for sign_mode, fv in (("", fact_value), ("abs", abs(fact_value))):
        t = abs(target) if sign_mode else target
        if abs(fv - t) <= unit / 2:
            return (sign_mode + "+round").strip("+")
        if 0 <= fv - t < unit:
            return (sign_mode + "+truncate").strip("+")
    return None


def equals_within(evidence, claim, contract):
    """C-1d §3.1 row 1. Two branches, chosen by which param is present:

    - ``abs_tolerance`` set (direct_value claims in units 名/人; not
      exercised by the 224-claim material -- 0 such claims bind a
      pointer): match = |fact - claim.value| <= abs_tolerance.
    - otherwise (money claims): match = ``_match_value(fact,
      claim.value * unit_scale, claim_scale)`` is not None.

    ``recomputed`` is always the fact's raw (unrounded) value.
    """

    params = contract.params or {}
    fact = evidence[0]
    abs_tolerance = params.get("abs_tolerance")
    if abs_tolerance is not None:
        match = abs(fact.value - claim.value) <= abs_tolerance
        detail = {"abs_tolerance": abs_tolerance}
        return core.Comparison(match=match, recomputed=fact.value, depth="value_match", detail=detail)
    unit_scale = params["unit_scale"]
    claim_scale = params["claim_scale"]
    target = claim.value * unit_scale
    how = _match_value(fact.value, target, claim_scale)
    detail = {"normalization": how}
    return core.Comparison(match=how is not None, recomputed=fact.value, depth="value_match", detail=detail)


def equals_within_pure100(evidence, claim, contract):
    """C-1d §3.1 row 2 (``equals_within(pure*100)``).

    fv = evidence[0].value (an XBRL "pure" fact, e.g. 0.058 for 5.8%).
    fvp = fv*100 if |fv| <= pure_threshold else fv (原本の癖 a-adjacent: a
    "pure" fact that is already > pure_threshold -- e.g. already
    expressed as a percentage number -- is left as-is rather than
    multiplied again; this part is unchanged by C-1f).
    match = |fvp - claim.value| <= tolerance (**fixed by C-1f**: compared
    to the signed ``claim.value``, not ``abs(claim.value)``).
    recomputed = round(fvp, 2).
    """

    params = contract.params or {}
    tolerance = params["tolerance"]
    pure_threshold = params["pure_threshold"]
    fv = evidence[0].value
    fvp = fv * 100 if abs(fv) <= pure_threshold else fv
    recomputed = round(fvp, 2)
    match = abs(fvp - claim.value) <= tolerance
    detail = {"tolerance": tolerance, "pure_threshold": pure_threshold}
    return core.Comparison(match=match, recomputed=recomputed, depth="value_match", detail=detail)


def ratio100(evidence, claim, contract):
    """C-1d §3.1 row 3. evidence = (cur, prior).

    ratio = cur.value / prior.value * 100. match = |ratio - claim.value|
    <= tolerance (**fixed by C-1f**: compared to the signed
    ``claim.value``, not ``abs(claim.value)``). recomputed = round(ratio,
    2). This Adapter never builds a Recipe with this comparator when
    prior.value == 0 (see module docstring, 癖 c); division by zero is
    not guarded here.
    """

    params = contract.params or {}
    tolerance = params["tolerance"]
    cur, prior = evidence[0], evidence[1]
    ratio = cur.value / prior.value * 100
    recomputed = round(ratio, 2)
    match = abs(ratio - claim.value) <= tolerance
    detail = {"tolerance": tolerance}
    return core.Comparison(match=match, recomputed=recomputed, depth="value_match", detail=detail)


def pct_change(evidence, claim, contract):
    """C-1d §3.1 row 4 (``pct_change(cur,prior)``). evidence = (cur, prior).

    pct = (cur.value - prior.value) / |prior.value| * 100. match =
    |pct - claim.value| <= tolerance (claim.value is signed here, unlike
    ratio100 / pure100 -- per C-1d prediction §3.1 table). recomputed =
    round(pct, 2). Division by zero: see ``ratio100``'s docstring.
    """

    params = contract.params or {}
    tolerance = params["tolerance"]
    cur, prior = evidence[0], evidence[1]
    pct = (cur.value - prior.value) / abs(prior.value) * 100
    recomputed = round(pct, 2)
    match = abs(pct - claim.value) <= tolerance
    detail = {"tolerance": tolerance}
    return core.Comparison(match=match, recomputed=recomputed, depth="value_match", detail=detail)


def diff_ab_equals_within(evidence, claim, contract):
    """C-1d §3.1 row 5 (``diff(a-b) equals_within``). evidence = (a, b).

    diff = a.value - b.value (raw, unrounded -- this is ``recomputed``).
    match = ``_match_value(diff, claim.value * unit_scale, claim_scale)``
    is not None.
    """

    params = contract.params or {}
    unit_scale = params["unit_scale"]
    claim_scale = params["claim_scale"]
    a, b = evidence[0], evidence[1]
    diff = a.value - b.value
    target = claim.value * unit_scale
    how = _match_value(diff, target, claim_scale)
    detail = {"normalization": how}
    return core.Comparison(match=how is not None, recomputed=diff, depth="value_match", detail=detail)


def builtin_sign_direction(evidence, claim, contract):
    """C-1d §3.1 row 6 (``builtin:sign(cur-prior)==direction``).

    evidence = (cur, prior). diff = cur.value - prior.value. actual = 0
    if diff == 0 else (1 if diff > 0 else -1) (**fixed by C-1f**: a
    difference of exactly 0 is now neither an increase nor a decrease,
    so it matches neither ``direction``; previously ``actual = -1`` when
    ``diff == 0``, counting a zero difference as a "decrease", per the
    original's ``1 if diff > 0 else -1``). match = actual == direction
    (params["direction"], an Adapter-resolved +1/-1; the Core never
    reads the direction word itself; ``actual == 0`` matches neither
    ``direction == 1`` nor ``direction == -1``).
    """

    params = contract.params or {}
    direction = params["direction"]
    cur, prior = evidence[0], evidence[1]
    diff = cur.value - prior.value
    actual = 0 if diff == 0 else (1 if diff > 0 else -1)
    detail = {"direction": direction, "actual": actual}
    return core.Comparison(match=(actual == direction), recomputed=diff, depth="value_match", detail=detail)
