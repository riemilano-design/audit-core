# -*- coding: utf-8 -*-
"""The six comparators C-1d §3.1 fixes (plus two more added by Core 接続
C-1g §1-2/§1-3 for profile P6 only: ``builtin_flow_sign_direction`` /
``diff_ab_pure100``, and one more added by Core 接続 C-1h §1-1 for
profile P7 only: ``builtin_sign_abs_diff_direction``), all registered
under ``register_all`` (see :mod:`registry_setup`).

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


def _match_value(fact_value, target, unit, mode=None):
    """Copy of ``vocabulary.match_value`` / ``xbrl_probe.py: match_value``.

    round    : |fact - target| <= unit/2
    truncate : 0 <= fact - target < unit
    abs+...  : same two checks with both sides' sign dropped
    Returns one of "round" / "truncate" / "abs+round" / "abs+truncate",
    or ``None`` if neither check passes in either sign mode.

    ``mode`` (XBRL 直し §2、人間の決定 2026-10-08) は省略可能。``None`` の
    ときは写し元と同じ梯子(P1/P5F/P6/P7 はこちら)。``"round"`` /
    ``"truncate"`` のときは**その 1 つだけ**を試す。値は
    ``Contract.params["rounding"]`` で渡ってくる ― 書類単位で 1 つに決めた
    丸め方を、組むときと検証するときの両方で同じものにするため。
    ``vocabulary.match_value`` と同じ引数・同じ戻り値であることは
    ``test_lineage`` が ``mode`` ごとに照合する。
    """

    for sign_mode, fv in (("", fact_value), ("abs", abs(fact_value))):
        t = abs(target) if sign_mode else target
        if mode in (None, "round") and abs(fv - t) <= unit / 2:
            return (sign_mode + "+round").strip("+")
        if mode in (None, "truncate") and 0 <= fv - t < unit:
            return (sign_mode + "+truncate").strip("+")
    return None


def equals_within(evidence, claim, contract):
    """C-1d §3.1 row 1. Three branches, chosen by which params are present:

    - ``abs_tolerance`` set (direct_value claims in units 名/人; not
      exercised by the 224-claim material -- 0 such claims bind a
      pointer): match = |fact - claim.value| <= abs_tolerance.
    - ``flow_convention``/``claim_direction`` both set (Core 接続 C-1g
      §1-2, profile P6 only; P1/P5F never set these params, so this
      branch is unreached for them): the magnitude is matched on the
      *unsigned* round/truncate ladder (dropping the "abs+" prefix,
      since both operands are already made non-negative here), and the
      sign is checked separately: match = (ladder match) and
      (sign(fact) * flow_convention == claim_direction). A fact value
      of exactly 0 has sign 0, which matches no non-zero direction.
    - otherwise (money claims, the original behaviour): match =
      ``_match_value(fact, claim.value * unit_scale, claim_scale)`` is
      not None.

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
    flow_convention = params.get("flow_convention")
    claim_direction = params.get("claim_direction")
    if flow_convention is not None and claim_direction is not None:
        target_abs = abs(claim.value) * unit_scale
        how = _match_value(abs(fact.value), target_abs, claim_scale, params.get("rounding"))
        fact_sign = 0 if fact.value == 0 else (1 if fact.value > 0 else -1)
        sign_ok = (fact_sign * flow_convention) == claim_direction
        detail = {"normalization": how, "flow_convention": flow_convention, "claim_direction": claim_direction, "fact_sign": fact_sign}
        return core.Comparison(match=(how is not None and sign_ok), recomputed=fact.value, depth="value_match", detail=detail)
    target = claim.value * unit_scale
    how = _match_value(fact.value, target, claim_scale, params.get("rounding"))
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
    how = _match_value(diff, target, claim_scale, params.get("rounding"))
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


def builtin_flow_sign_direction(evidence, claim, contract):
    """Core 接続 C-1g §1-2 (``builtin:flow_sign(cur)==direction``, profile
    P6 only). evidence = (cur,) -- the current-year fact alone (no prior
    year; the CF flow item's own value already represents the period's
    movement, per ``vocabulary.flow_convention``'s docstring).

    actual = 0 if cur.value == 0 else (1 if cur.value * flow_convention
    > 0 else -1). match = actual == direction (params["direction"], an
    Adapter-resolved +1/-1). recomputed = cur.value (raw).
    """

    params = contract.params or {}
    direction = params["direction"]
    flow_convention = params["flow_convention"]
    cur = evidence[0]
    actual = 0 if cur.value == 0 else (1 if cur.value * flow_convention > 0 else -1)
    detail = {"direction": direction, "flow_convention": flow_convention, "actual": actual}
    return core.Comparison(match=(actual == direction), recomputed=cur.value, depth="value_match", detail=detail)


def builtin_sign_abs_diff_direction(evidence, claim, contract):
    """Core 接続 C-1h §1-1 (``builtin:sign(|cur|-|prior|)==direction``,
    profile P7 only). evidence = (cur, prior) -- CF の「支出」系項目
    (負で記録される。``vocabulary.expenditure_convention``)の当期・前期の
    JPY fact。文の「増加/減少」は大きさ(絶対値)の増減を指す。

    actual = 0 if |cur.value| == |prior.value| else (1 if |cur.value| >
    |prior.value| else -1)(差 0 はどちらの方向にも一致しない。C-1f の
    ``builtin_sign_direction`` の癖 b と同じ扱い)。match = actual ==
    direction。recomputed = |cur.value| - |prior.value|(符号つき、大きさ
    の差)。
    """

    params = contract.params or {}
    direction = params["direction"]
    cur, prior = evidence[0], evidence[1]
    acur, aprior = abs(cur.value), abs(prior.value)
    magnitude_diff = acur - aprior
    # C-1h §1-1 (deliberately phrased/named differently from
    # builtin_sign_direction's own ``actual = 0 if diff == 0 else (...)``
    # / ``return core.Comparison(match=(actual == direction), recomputed=
    # diff, ...)`` lines, so this new function's text does not collide
    # with mutations F-R3/D-R4's unique-match targets in this file; see
    # tests/adapters/xbrl/mutations.json).
    actual = (1 if magnitude_diff > 0 else -1) if magnitude_diff != 0 else 0
    detail = {"direction": direction, "actual": actual}
    return core.Comparison(match=(direction == actual), recomputed=magnitude_diff, depth="value_match", detail=detail)


def builtin_sign_direction_with_amount(evidence, claim, contract):
    """A1(主語の規則の直し、人間の追加指示、2026-10-08)。
    ``builtin:sign(cur-prior)==direction&amount``。

    evidence = (cur, prior)。向きの判定は ``builtin_sign_direction`` と同じ
    (差がちょうど 0 ならどちらの方向にも一致しない)。**そのうえで**、
    Adapter が向きの語と同じ節から読んだ金額 (``claim.value``) を
    ``|cur - prior|`` と照合する: ``_match_value(|diff|, |claim.value| *
    unit_scale, claim_scale, rounding)``。

    match = (向きが一致) **かつ** (金額が一致)。``recomputed`` は
    ``builtin_sign_direction`` と同じ生の差。**この比較器は向きだけの
    比較器より厳しい側にしか動かない** ― 向きが合っていても金額が合わなければ
    一致しない。
    """

    params = contract.params or {}
    direction = params["direction"]
    cur, prior = evidence[0], evidence[1]
    difference = cur.value - prior.value
    sign_now = 0 if difference == 0 else (1 if difference > 0 else -1)
    target_amount = abs(claim.value) * params["unit_scale"]
    ladder = _match_value(abs(difference), target_amount, params["claim_scale"], params.get("rounding"))
    detail = {"direction": direction, "actual": sign_now, "normalization": ladder}
    agree = (sign_now == direction) and (ladder is not None)
    return core.Comparison(match=agree, recomputed=difference, depth="value_match", detail=detail)


def diff_ab_pure100(evidence, claim, contract):
    """Core 接続 C-1g §1-3 (``diff(a-b)(pure*100)``, profile P6 only, the
    ``XP-3rd-1`` point-difference form). evidence = (a, b) -- the current
    and prior year "pure" (ratio) facts.

    recomputed = round((a.value - b.value) * 100, 2) (raw difference of
    the two ratios, rescaled to percentage points). match = |recomputed -
    claim.value| <= tolerance (params["tolerance"]; claim.value is
    signed -- the Adapter attaches the direction word's sign when it
    builds the point-difference Claim, see ``recipes.py``).
    """

    params = contract.params or {}
    tolerance = params["tolerance"]
    a, b = evidence[0], evidence[1]
    recomputed = round((a.value - b.value) * 100, 2)
    match = abs(recomputed - claim.value) <= tolerance
    detail = {"tolerance": tolerance}
    return core.Comparison(match=match, recomputed=recomputed, depth="value_match", detail=detail)
