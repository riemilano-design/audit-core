# -*- coding: utf-8 -*-
"""The Adapter's pointer resolver (C-1d prediction §3.2): turns one
``xbrl:<name>@<context>`` pointer into a Core ``Resolved``, by lookup in
a document's already-loaded ``facts`` list (the ``facts`` key of
:func:`adapters.xbrl.instance.load_instance`'s return value).

``make_resolver`` takes the facts list itself, not the document bytes or
the :mod:`instance` module, so this file does not import :mod:`instance`,
:mod:`extract` or :mod:`vocabulary` (callers -- :mod:`run` and the
``tests/golden`` instruments -- load the instance and pass its facts in).
This is new C-1d code, not a transcription of any probe script: the
originals never resolve a pointer string back to a fact; they keep the
chosen fact dict in hand from the moment they pick it.
"""

import audit_core as core


def make_resolver(facts):
    """Build a resolver closure over one document's ``facts`` list.

    Lookup key is ``(name, context)``, matching the ``xbrl:<name>@<context>``
    pointer shape built throughout :mod:`recipes`. Resolution is **by
    instance order**: the first fact (in ``facts``' own order) with a
    matching key is returned; a pointer with no matching fact resolves to
    ``None`` (the Core turns that into ``POINTER_NOT_FOUND``).

    ``Resolved.meta`` carries ``decimals`` (of the chosen fact),
    ``duplicates`` (how many facts share the exact same (name, context)
    key) and ``distinct_values`` (how many distinct values those
    duplicates have -- the C-1d gate asserts this is 1 for every pointer
    actually used by the 224-claim material).
    """

    by_key = {}
    for fact in facts:
        by_key.setdefault((fact["name"], fact["context"]), []).append(fact)

    def resolver(pointer):
        name, _, context = pointer.locator.partition("@")
        matches = by_key.get((name, context))
        if not matches:
            return None
        chosen = matches[0]
        decimals = chosen.get("decimals")
        precision = None
        if decimals is not None and decimals != "INF":
            try:
                precision = 10 ** (-int(decimals))
            except ValueError:
                precision = None
        distinct_values = len({m["value"] for m in matches})
        return core.Resolved(
            value=chosen["value"],
            unit=chosen["unit"],
            precision=precision,
            meta={
                "decimals": decimals,
                "duplicates": len(matches),
                "distinct_values": distinct_values,
            },
        )

    return resolver
