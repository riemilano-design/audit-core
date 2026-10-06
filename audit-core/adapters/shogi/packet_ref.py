# -*- coding: utf-8 -*-
"""Value-for-value transcription of ``scripts/playtest/lib/packetRef.ts``'s
grammar (not imported -- read-only reference; see the package docstring).

``AGGREGATE_REF_RE`` / ``FACTS_REF_RE`` are copied **character for
character** from the TypeScript regex literals (checked by the lineage
test ``tests/adapters/shogi/test_packet_ref.py``, which reads
``packetRef.ts`` as text and compares the extracted literal source to
``.pattern`` here). ``path_problems`` is a transcription of
``packetRefPathProblems``; ``aggregate_id_of`` is a transcription of
``hypothesis.ts``'s private (non-exported) ``aggregateIdOf`` -- that
function cannot be imported or run from Python/Node directly (it is not
exported), so this transcription is checked only by designed test cases
traced by hand against the TypeScript source (not a lineage test; see
the module docstring note in ``test_packet_ref.py``).
"""

import re

AGGREGATE_PARTS = ("numerator", "denominator", "value")

AGGREGATE_REF_RE = re.compile(
    r"^aggregates\.[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*\.(?:numerator|denominator|value)$"
)
FACTS_REF_RE = re.compile(
    r"^facts\.(?:(?:games|moves|engine|time|branches|collapse)|recognition\.(?:rows|definitions))"
    r"\[\d+\](?:\.[A-Za-z0-9_]+(?:\[\d+\])?)+$"
)


def path_problems(path):
    """Transcription of ``packetRefPathProblems``. Returns a list of 0 or 1
    problem strings (empty = grammar OK). Does not check existence."""

    if not isinstance(path, str) or len(path) == 0:
        return ["packetRef.path が文字列でない・空"]
    if AGGREGATE_REF_RE.match(path) or FACTS_REF_RE.match(path):
        return []
    return [
        "packetRef.path「%s」が文法(aggregates.<id>.numerator|denominator|value / "
        "facts.<列>[添字].欄名)に合わない" % (path,)
    ]


def aggregate_id_of(path):
    """Transcription of ``hypothesis.ts``'s private ``aggregateIdOf``:
    ``aggregates.<id>.numerator|denominator|value`` -> ``<id>``, or
    ``None`` if ``path`` does not start with ``aggregates.`` or has no
    id component (e.g. ``aggregates.value``)."""

    if not isinstance(path, str) or not path.startswith("aggregates."):
        return None
    parts = path[len("aggregates."):].split(".")
    last = parts[-1] if parts else None
    if last is None or last not in AGGREGATE_PARTS:
        return None
    id_ = ".".join(parts[:-1])
    return id_ if id_ != "" else None
