# -*- coding: utf-8 -*-
"""Transcription of ``resolvePacketPath`` (``scripts/playtest/lib/
observationPacket.ts``, not imported -- read-only reference; see the
package docstring) plus this Adapter's pointer resolver
(``make_resolver``, the Core-facing half).

``resolve_packet_path`` keeps the TypeScript function's order of checks
(packet present -> grammar -> aggregates row/field -> facts
array/index/key walk) and its Japanese reason text (``reason_text``,
preserved verbatim for a human reading the output), but additionally
classifies every failure into one of **5 kinds** (C-2 plan §2's
``resolvePacketPath`` row), each registered as a Core
``POINTER_NOT_FOUND`` reason by :mod:`registry_setup`:

  - ``"grammar"``: the path failed ``packet_ref.path_problems`` (or,
    defensively, the unreachable-in-practice "path の形が読めない" case --
    grammar already guarantees ``_path_steps`` succeeds, since every
    character class the grammar regexes allow is also accepted by
    ``_STEP_RE``/``_INDEX_RE``; kept for parity with the TS source,
    which also has this branch).
  - ``"no_row"``: ``packet`` has no ``aggregates`` array, or no row with
    the given id.
  - ``"no_field"``: the row exists but lacks the requested field
    (numerator/denominator/value mismatch).
  - ``"index_out_of_range"``: a numeric path step indexes past the end
    of an array.
  - ``"missing_key"``: everything else TS folds into a plain "can't walk
    further" reason (packet absent, stepping into a non-array with a
    numeric index, stepping into a non-object/array value, or a missing
    object key) -- per the implementer instruction, "packet が無い"・
    「列でない」・「引けない」 all land here, alongside TS's 「が packet
    に無い」.
"""

import re

from . import packet_ref as PR

GRAMMAR = "grammar"
NO_ROW = "no_row"
NO_FIELD = "no_field"
INDEX_OUT_OF_RANGE = "index_out_of_range"
MISSING_KEY = "missing_key"

_STEP_RE = re.compile(r"^([A-Za-z0-9_]+)((?:\[\d+\])*)$")
_INDEX_RE = re.compile(r"\[(\d+)\]")


def _path_steps(path):
    """Transcription of ``pathSteps``. Returns a list of ``str``/``int``
    steps, or ``None`` if a path segment does not match the key[idx]...
    shape."""

    steps = []
    for part in path.split("."):
        if part == "":
            return None
        m = _STEP_RE.match(part)
        if m is None:
            return None
        steps.append(m.group(1))
        for idx_m in _INDEX_RE.finditer(m.group(2)):
            steps.append(int(idx_m.group(1)))
    return steps


def resolve_packet_path(packet, path):
    """Transcription of ``resolvePacketPath``. Returns
    ``(ok, value_or_kind, reason_text)``: on success,
    ``(True, value, None)``; on failure, ``(False, <one of the 5 kinds
    above>, <TS-style Japanese reason text>)``."""

    if packet is None or not isinstance(packet, dict):
        return (False, MISSING_KEY, "packet が無い")

    grammar = PR.path_problems(path)
    if grammar:
        return (False, GRAMMAR, grammar[0])

    steps = _path_steps(path)
    if steps is None:
        return (False, GRAMMAR, "path の形が読めない: %s" % (path,))
    head = steps[0]

    if head == "aggregates":
        last = steps[-1]
        id_ = ".".join(str(s) for s in steps[1:-1])
        rows = packet.get("aggregates")
        if not isinstance(rows, list):
            return (False, NO_ROW, "packet に aggregates が無い")
        row = None
        for candidate in rows:
            if isinstance(candidate, dict) and candidate.get("id") == id_:
                row = candidate
                break
        if row is None:
            return (False, NO_ROW, "集計に %s の行が無い" % (id_,))
        if last not in row:
            return (
                False,
                NO_FIELD,
                "集計の %s に %s が無い(分数の行と単独の数の行を取り違えていないか)" % (id_, last),
            )
        return (True, row[last], None)

    current = packet
    walked = []
    for step in steps:
        walked.append(str(step))
        if isinstance(step, int):
            if not isinstance(current, list):
                return (False, MISSING_KEY, "%s は列でない" % (".".join(walked),))
            if step >= len(current):
                return (
                    False,
                    INDEX_OUT_OF_RANGE,
                    "%s は列の外(長さ %d)" % (".".join(walked), len(current)),
                )
            current = current[step]
            continue
        if current is None or not isinstance(current, dict) or isinstance(current, list):
            return (False, MISSING_KEY, "%s を引けない" % (".".join(walked),))
        if step not in current:
            return (False, MISSING_KEY, "%s が packet に無い" % (".".join(walked),))
        current = current[step]
    return (True, current, None)


def make_resolver(packet):
    """Build a Core resolver closure over one ``packet`` dict. Lookup is
    ``resolve_packet_path(packet, pointer.locator)``; a failure resolves
    to ``None`` (the Core turns that into ``POINTER_NOT_FOUND`` -- but in
    this Adapter's recipes, an unresolvable pointer is always caught at
    build time via ``Recipe.not_found_reason`` instead, so the resolver
    only actually runs for pointers already known to resolve; see
    :mod:`recipes`)."""

    def resolver(pointer):
        import audit_core as core

        ok, value_or_kind, _reason = resolve_packet_path(packet, pointer.locator)
        if not ok:
            return None
        value = value_or_kind
        is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
        return core.Resolved(
            value=float(value) if is_number else None,
            unit=None,
            precision=None,
            meta={"raw": value},
        )

    return resolver
