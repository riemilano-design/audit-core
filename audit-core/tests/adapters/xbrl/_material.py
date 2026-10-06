# -*- coding: utf-8 -*-
"""Shared test support: load the two cached EDINET ZIPs (hard failure, not
skip, if absent or sha-mismatched) and load the probe originals via
``importlib`` for the lineage Golden tests.

Not a ``test_*`` module, so ``unittest discover`` does not try to run it.
"""

import hashlib
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_FIXTURES_XBRL = os.path.join(_AUDIT_CORE, "fixtures", "xbrl")
_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

DOC_1 = {
    "docID": "S100Z4Q1",
    "sha256": "0731a291f10af5dd207e05d54df8e2b5dc34e79a84de94af1c1a5d4e207228f6",
}
DOC_5 = {
    "docID": "S100Z4B6",
    "sha256": "d617b6e1807c8aa6d2b1269f6b25ff57a6a71dbf683020f1859d2d4a04c02d26",
}
# Core 接続 C-1g: 3 社目(S100YMFV、2026-09-28 提出)。profile P6 の 3 書類計測
# (tests/golden/test_p6_smoke.py)だけが使う。P1/P5F の既存の門はこの定数を
# 読まない。
DOC_3RD = {
    "docID": "S100YMFV",
    "sha256": "4a5982e7447d6e0614c6ad12e7c091d462ca61a0128c2ce2af957a8bdfe1d52c",
}


def load_zip_bytes(doc_id, expected_sha256):
    """Read a cached ZIP. Raises (does not skip) if absent or mismatched."""

    path = os.path.join(_CACHE_DIR, "%s.zip" % (doc_id,))
    if not os.path.exists(path):
        raise FileNotFoundError(
            "material ZIP for %s is not cached at %s; the C-1c test suite "
            "fails rather than skipping when material is absent" % (doc_id, path)
        )
    with open(path, "rb") as handle:
        data = handle.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha256:
        raise ValueError("sha256 mismatch for %s: expected %s, got %s" % (doc_id, expected_sha256, actual))
    return data


def load_zip_1():
    return load_zip_bytes(DOC_1["docID"], DOC_1["sha256"])


def load_zip_5():
    return load_zip_bytes(DOC_5["docID"], DOC_5["sha256"])


_PROBE_MODULES = {}


def _load_probe(name):
    if name in _PROBE_MODULES:
        return _PROBE_MODULES[name]
    os.environ.setdefault("PROBE_RUN", "B")
    path = os.path.join(_FIXTURES_XBRL, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Register in sys.modules *before* exec so that the probe scripts'
    # internal ``import xbrl_probe as P`` (etc.) statements resolve to this
    # same loaded module instead of re-reading the file under a second name.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _PROBE_MODULES[name] = module
    return module


def load_probe_originals():
    """Load the four probe originals (unmodified; read-only use) via
    ``importlib``, in dependency order, with ``PROBE_RUN=B`` (73-word
    vocabulary, matching profile ``P1``).

    Returns a namespace-like object with ``.probe``, ``.probe3``,
    ``.probe4``, ``.probe5`` attributes.
    """

    probe = _load_probe("xbrl_probe")
    probe3 = _load_probe("xbrl_probe3")
    probe4 = _load_probe("xbrl_probe4")
    probe5 = _load_probe("xbrl_probe5")

    class _NS(object):
        pass

    ns = _NS()
    ns.probe, ns.probe3, ns.probe4, ns.probe5 = probe, probe3, probe4, probe5
    return ns
