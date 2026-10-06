# -*- coding: utf-8 -*-
"""``register_all`` (C-1d prediction §3.3): registers this Adapter's
schemes, comparators, normalizations and reasons on top of
``audit_core.Registry.default()``.

21 registrations: 2 schemes (``xbrl``, ``formula`` -- ``builtin`` is
already registered by ``Registry.default()`` and is *not* re-registered
here) + 6 comparators (:mod:`comparators`) + 4 normalizations (the
``_match_value`` ladder's four ``how`` strings) + 9 reasons (4
POINTER_NOT_FOUND + 5 UNVERIFIABLE, matching ``recipes.UNBOUND_REASON_STATE``
plus the count-free ``ambiguous(elements)`` -- see ``recipes.py``'s
normalization of ``ambiguous(N elements)``).
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
)

_NORMALIZATIONS = ("round", "truncate", "abs+round", "abs+truncate")

_POINTER_NOT_FOUND_REASONS = (
    "no_element",
    "no_element(unit not in XBRL)",
    "no_element(ratio without fact)",
    "no_prior_member_context",
)

_UNVERIFIABLE_REASONS = (
    "no_subject",
    "ambiguous(member)",
    "ambiguous(elements)",
    "state_word(no line)",
    "prior is 0",
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
