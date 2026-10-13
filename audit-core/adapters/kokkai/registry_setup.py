# -*- coding: utf-8 -*-
"""この adapter の登録: scheme 1・照合器 3・理由 2(UNVERIFIABLE)。
POINTER_NOT_FOUND の理由は Core 自身の ``unresolved:<pointer>`` だけ(登録不要)。"""

import audit_core as core

from . import comparators as C

SCHEME = "kokkai"

_COMPARATORS = (
    ("speaker_equals", C.speaker_equals),
    ("quote_in_speech", C.quote_in_speech),
    ("number_in_speech", C.number_in_speech),
)

NO_POINTER_GIVEN = "no_pointer_given"
NO_SPEAKER_GIVEN = "no_speaker_given"
_UNVERIFIABLE_REASONS = (NO_POINTER_GIVEN, NO_SPEAKER_GIVEN)


def register_all(registry):
    registry.register_scheme(SCHEME, kind="evidence", trust="official_record")
    for name, fn in _COMPARATORS:
        registry.register_comparator(name, fn)
    for name in _UNVERIFIABLE_REASONS:
        registry.register_reason(name, core.State.UNVERIFIABLE)
    return registry
