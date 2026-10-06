# -*- coding: utf-8 -*-
"""EDINET document retrieval and local cache.

The cache location is ``~/.cache/audit-core/edinet/<docID>.zip``. Fetching
over the network is isolated to :func:`fetch` and is never called by the
C-1c test suite (no test imports or exercises this function; see
``tests/adapters/xbrl/test_boundary.py`` B-3 for the check that no API key
value appears anywhere in this package).
"""

import hashlib
import os
import urllib.parse
import urllib.request

API = "https://api.edinet-fsa.go.jp/api/v2/"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")


def cache_path(doc_id):
    return os.path.join(CACHE_DIR, "%s.zip" % (doc_id,))


def sha256_of(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def read_cached(doc_id, expected_sha256=None):
    """Read the cached ZIP for ``doc_id``. Raises if the ZIP is absent or
    (when ``expected_sha256`` is given) does not match.

    This never falls back to :func:`fetch`: an absent ZIP is a hard error
    (tests must fail, not skip, per the C-1c instructions).
    """

    path = cache_path(doc_id)
    if not os.path.exists(path):
        raise FileNotFoundError("no cached ZIP for %s at %s" % (doc_id, path))
    with open(path, "rb") as handle:
        data = handle.read()
    if expected_sha256 is not None:
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected_sha256:
            raise ValueError("ZIP sha256 mismatch for %s: expected %s, got %s" % (doc_id, expected_sha256, actual))
    return data


def _api_key():
    # The key's value never appears in this file; only the environment
    # variable's *name* is referenced here.
    return os.environ.get("EDINET_API_KEY")


def fetch(doc_id):
    """Fetch a document's ZIP from EDINET and write it to the local cache.

    Not called by the C-1c test suite. Requires ``EDINET_API_KEY`` to be set
    in the environment.
    """

    key = _api_key()
    if not key:
        raise RuntimeError("EDINET_API_KEY is not set")
    params = {"type": 1, "Subscription-Key": key}
    url = API + "documents/%s" % (doc_id,) + "?" + urllib.parse.urlencode(params)
    data = urllib.request.urlopen(url, timeout=120).read()
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = cache_path(doc_id)
    with open(path, "wb") as f:
        f.write(data)
    return path
