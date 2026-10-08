# -*- coding: utf-8 -*-
"""``register_all`` (C-1d prediction §3.3; extended by C-1g §1-5 and
C-1h §3.4-c, 2026-10-06): registers this Adapter's schemes, comparators,
normalizations and reasons on top of ``audit_core.Registry.default()``.

29 registrations: 2 schemes (``xbrl``, ``formula`` -- ``builtin`` is
already registered by ``Registry.default()`` and is *not* re-registered
here) + 9 comparators (:mod:`comparators`; 6 from C-1d + 2 from C-1g's
profile P6 + 1 from C-1h's profile P7) + 4 normalizations (the
``_match_value`` ladder's four ``how`` strings; unchanged -- P6's
flow-sign branch of ``equals_within`` reuses the existing
"round"/"truncate" names, see ``comparators.py``) + 14 reasons (7
POINTER_NOT_FOUND + 6 UNVERIFIABLE; C-1d's 9, matching
``recipes.UNBOUND_REASON_STATE`` plus the count-free
``ambiguous(elements)``, plus C-1g's one new POINTER_NOT_FOUND reason
for the point-difference form, plus C-1h's two new POINTER_NOT_FOUND
reasons for the text-claim pair-not-found split and one new
UNVERIFIABLE reason for ``target_or_plan``). This function registers
everything unconditionally (it does not take a profile): P1/P5F/P6's
recipes simply never reference the P7-only comparator or the three
P7-only reasons, so their presence in the registry is inert for those
three profiles.
"""

import audit_core as core

from . import comparators as C

_COMPARATORS = (
    ("equals_within", C.equals_within),
    ("equals_within(pure*100)", C.equals_within_pure100),
    ("ratio*100", C.ratio100),
    ("pct_change(cur,prior)", C.pct_change),
    ("diff(a-b) equals_within", C.diff_ab_equals_within),
    ("builtin:sign(cur-prior)==direction", C.builtin_sign_direction),
    # Core 接続 C-1g §1-2/§1-3(profile P6 のみが参照する)。
    ("builtin:flow_sign(cur)==direction", C.builtin_flow_sign_direction),
    ("diff(a-b)(pure*100)", C.diff_ab_pure100),
    # Core 接続 C-1h §1-1(profile P7 のみが参照する)。
    ("builtin:sign(|cur|-|prior|)==direction", C.builtin_sign_abs_diff_direction),
)

_NORMALIZATIONS = ("round", "truncate", "abs+round", "abs+truncate")

_POINTER_NOT_FOUND_REASONS = (
    "no_element",
    "no_element(unit not in XBRL)",
    "no_element(ratio without fact)",
    "no_prior_member_context",
    # Core 接続 C-1g §1-3(profile P6 のみ)。
    "no_element(point without prior phrase)",
    # Core 接続 C-1h §1-3(profile P7 のみ)。
    "no_element(text needs money fact)",
    "no_element(no prior for text)",
    # XBRL 直し §1b(人間の決定、2026-10-08、profile P8 のみ)。前々期の値が
    # 無いときに代用せず止める理由。P1/P5F/P6/P7 はこの理由を作らないので、
    # 登録簿に在ること自体は彼らに対して無害(既存の理由は 1 つも消していない)。
    "no_element(no prior2 for prior-year diff)",
)

_UNVERIFIABLE_REASONS = (
    "no_subject",
    "ambiguous(member)",
    "ambiguous(elements)",
    "state_word(no line)",
    "prior is 0",
    # Core 接続 C-1h §1-2(profile P7 のみ)。
    "target_or_plan",
)


def register_all(registry):
    """Register everything this Adapter needs on ``registry`` (normally
    ``audit_core.Registry.default()``) and return it.
    """

    registry.register_scheme("xbrl", kind="evidence", trust="filing")
    registry.register_scheme("formula", kind="operator", trust="structural")

    for name, fn in _COMPARATORS:
        registry.register_comparator(name, fn)

    for name in _NORMALIZATIONS:
        registry.register_normalization(name)

    for name in _POINTER_NOT_FOUND_REASONS:
        registry.register_reason(name, core.State.POINTER_NOT_FOUND)

    for name in _UNVERIFIABLE_REASONS:
        registry.register_reason(name, core.State.UNVERIFIABLE)

    return registry
