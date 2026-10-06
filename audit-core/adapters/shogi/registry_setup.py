# -*- coding: utf-8 -*-
"""``register_all`` (C-2 plan §4.1 P-2): registers this Adapter's
scheme, comparator and reasons on top of ``audit_core.Registry.default()``.

**8 registrations**: 1 scheme (``packet``) + 1 comparator
(``canonical_json_equals``) + 5 ``POINTER_NOT_FOUND`` reasons
(:mod:`resolve`'s 5 failure kinds) + 1 ``UNVERIFIABLE`` reason
(:mod:`recipes.NO_PACKET_REF_REASON`). 0 normalizations. ``builtin``
and ``equals`` are ``Registry.default()``'s own and are not
re-registered here.
"""

import audit_core as core

from . import comparators as C
from . import resolve as RV
from .recipes import NO_PACKET_REF_REASON

_POINTER_NOT_FOUND_REASONS = (
    RV.GRAMMAR,
    RV.NO_ROW,
    RV.NO_FIELD,
    RV.INDEX_OUT_OF_RANGE,
    RV.MISSING_KEY,
)


def register_all(registry):
    """Register everything this Adapter needs on ``registry`` (normally
    ``audit_core.Registry.default()``) and return it."""

    registry.register_scheme("packet", kind="evidence", trust="tool")
    registry.register_comparator("canonical_json_equals", C.canonical_json_equals)

    for name in _POINTER_NOT_FOUND_REASONS:
        registry.register_reason(name, core.State.POINTER_NOT_FOUND)

    registry.register_reason(NO_PACKET_REF_REASON, core.State.UNVERIFIABLE)

    return registry
