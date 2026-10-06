# -*- coding: utf-8 -*-
"""Shogi Adapter (Core 接続 C-2, 2026-10-06, 封 `CORE_CONNECTION_C2_PLAN_2026-10-06.md`
§2). Knows about the Golden Master (c5) shogi material shape: the
Observation Packet (``docs/golden_master`` 相当)and the LLM seats'
hypothesis envelopes (``items[].observations[]`` / ``counterEvidence``).

Scope (C-2 §1): this Adapter reproduces only the **H-9** judgement
(packetRef の実在と値の一致) of the TypeScript verifier
(``scripts/playtest/lib/hypothesis.ts``), through a Python-side Claim /
Pointer / Contract / Result translation that ``audit_core.verify_all``
runs unmodified. It does not replace, call, or import anything under
``scripts/playtest/`` -- the TypeScript source there is read-only
reference material this package's modules independently reproduce the
*behaviour* of (and the lineage tests in
``tests/adapters/shogi/test_packet_ref.py`` /
``tests/adapters/shogi/test_canonical.py`` check that reproduction
against the TypeScript text/output, value for value).

This package itself does not import ``audit_core`` (mirrors
``adapters/__init__.py``'s existing ``sys.path`` wiring for
``core/py``); only :mod:`recipes` does.
"""
