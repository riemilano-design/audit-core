# -*- coding: utf-8 -*-
"""3 つの照合器。読むのは evidence(発言)・claim・contract.params だけ。"""

import re
import unicodedata

from . import numerals as N

_WS_RE = re.compile(r"[\s　]+")


def normalize_text(s):
    """NFKC にして、空白・改行・全角空白を全部除く。"""

    return _WS_RE.sub("", unicodedata.normalize("NFKC", s or ""))


def normalize_name(s):
    return _WS_RE.sub("", s or "")


def speaker_equals(evidence, claim, contract):
    import audit_core as core

    expected = normalize_name(contract.params["expected"])
    actual = normalize_name(evidence[0].meta.get("speaker"))
    return core.Comparison(match=(expected != "" and expected == actual), recomputed=None,
                           depth="value_match", detail={"expected": expected, "actual": actual})


def quote_in_speech(evidence, claim, contract):
    import audit_core as core

    quote = normalize_text(contract.params["quote"])
    speech = normalize_text(evidence[0].meta.get("speech"))
    found = quote != "" and quote in speech
    return core.Comparison(match=found, recomputed=None, depth="value_match",
                           detail={"quote_chars": len(quote), "found": found})


def number_in_speech(evidence, claim, contract):
    import audit_core as core

    tokens = N.number_tokens(evidence[0].meta.get("speech") or "")
    unit = N.normalize_unit(claim.unit)
    hit = None
    for value, tunit, raw in tokens:
        if claim.value is not None and _same_value(value, claim.value) and tunit == unit:
            hit = (value, tunit, raw)
            break
    return core.Comparison(match=(hit is not None), recomputed=(hit[0] if hit else None),
                           depth="value_match",
                           detail={"tokens": len(tokens), "unit": unit,
                                   "matched_raw": (hit[2] if hit else None)})


def _same_value(a, b):
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))
