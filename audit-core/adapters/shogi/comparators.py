# -*- coding: utf-8 -*-
"""The one comparator C-2 plan §2 fixes: ``canonical_json_equals`` (H-9's
"``canonicalJson(value)`` が一致" check, re-expressed as a Core
comparator).

Reads only the already-resolved ``evidence`` (one ``Resolved``, whose
``meta["raw"]`` is the packet value :mod:`resolve`'s resolver found),
``claim`` (unused directly -- the expected value travels through
``contract.params["expected"]``, not ``claim.value``, because many
observed values are strings/objects that do not fit ``Claim.value``'s
``Optional[float]`` -- C-2 plan §4.1 P-5) and ``contract.params``.
"""

from . import canonical as J


def canonical_json_equals(evidence, claim, contract):
    import audit_core as core

    expected = contract.params["expected"]
    actual_raw = evidence[0].meta["raw"]
    expected_canonical = J.canonical_json(expected)
    actual_canonical = J.canonical_json(actual_raw)
    is_number = isinstance(actual_raw, (int, float)) and not isinstance(actual_raw, bool)
    recomputed = float(actual_raw) if is_number else None
    return core.Comparison(
        match=(expected_canonical == actual_canonical),
        recomputed=recomputed,
        depth="value_match",
        detail={"expected_canonical": expected_canonical, "actual_canonical": actual_canonical},
    )
