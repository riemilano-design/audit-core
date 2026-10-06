# -*- coding: utf-8 -*-
"""Shared support for the ``tests/golden`` instruments (C-1d §3.4/§3.5):
build the registry + resolver for one document/profile, run
``audit_core.verify_all``, and load/validate the C-0 expectation JSON the
same way ``tests/adapters/xbrl/test_claim_layer.py`` does.

Not a ``test_*`` module, so ``unittest discover`` does not try to run it.
"""

import hashlib
import json
import os

import audit_core as core

from adapters.xbrl import instance as I
from adapters.xbrl import recipes as R
from adapters.xbrl import registry_setup as RS
from adapters.xbrl import resolve as RV

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", ".."))
_FIXTURES_XBRL = os.path.join(_AUDIT_CORE, "fixtures", "xbrl")

_EXPECTATION_SHA256 = {
    "core_expectation_1B.json": "f8a45ecce18a3d98181061a6943449c75a0fbb850e09ec0b71808a45a70fd820",
    "core_expectation_5F.json": "a19f3419e1a6e1a0cc87df92ae7717c48049b2fcca89d7e8d7ae0161b994adc4",
}

# C-1d §3.3: the registered reason that replaces the script's dynamic
# ``ambiguous(N elements)`` string. Used to map the expectation's
# ``script_reason`` to the name Core's Result.reason will actually carry.
_REGISTERED_REASONS = frozenset((
    "no_element",
    "no_element(unit not in XBRL)",
    "no_element(ratio without fact)",
    "no_prior_member_context",
    "no_subject",
    "ambiguous(member)",
    "ambiguous(elements)",
    "state_word(no line)",
    "prior is 0",
))


def load_expectation(name):
    """Load and sha256-verify a C-0 expectation JSON (never edited here)."""

    path = os.path.join(_FIXTURES_XBRL, name)
    with open(path, "rb") as handle:
        data = handle.read()
    actual_sha = hashlib.sha256(data).hexdigest()
    expected_sha = _EXPECTATION_SHA256[name]
    if actual_sha != expected_sha:
        raise AssertionError(
            "expectation file %s changed (sha256 expected %s, got %s); "
            "the expectation must not be edited" % (name, expected_sha, actual_sha)
        )
    return json.loads(data.decode("utf-8"))


def expected_reason(script_reason):
    """Map the expectation's ``script_reason`` to the Core ``Result.reason``
    this Adapter's register_all + verify() is expected to produce.

    - ``None`` (GROUNDED/VALUE_MISMATCH with no script note) -> ``None``.
    - ``ambiguous(N elements)`` -> ``ambiguous(elements)`` (C-1d §3.3
      normalization; N moves to ``Claim.provenance["ambiguous_count"]``).
    - one of the 9 registered reason names -> itself (the short-circuit
      reason Core's verify() returns unchanged).
    - anything else (e.g. ``"value differs(segment/other period?)"``,
      ``"value_only(no subject)"``, ``"diff phrase but value matched a
      fact"`` -- descriptive notes the script leaves on a *bound*
      GROUNDED/VALUE_MISMATCH claim) -> ``None``: these are not registered
      reasons, and Core's ``verify()`` only ever sets ``Result.reason`` on
      a short-circuit or pointer-resolution-failure path, never alongside
      a comparator's GROUNDED/VALUE_MISMATCH outcome.
    """

    if script_reason is None:
        return None
    if script_reason.startswith("ambiguous(") and script_reason.endswith(" elements)"):
        return "ambiguous(elements)"
    if script_reason in _REGISTERED_REASONS:
        return script_reason
    return None


def run_verification(doc, profile, zip_loader):
    """Build Recipes for ``doc``/``profile``, verify them with this
    Adapter's resolver + registry, and return
    ``(recipe_list, results_by_id, pointer_metas)``.

    ``pointer_metas`` is ``{pointer_str: meta}`` for every ``xbrl:``
    pointer this run's resolver actually resolved (``meta`` is the dict
    :func:`resolve.make_resolver` attaches: decimals/duplicates/
    distinct_values) -- scoped to *this one document's run* (C-1d §3.2:
    the 99-pointer count in the prediction is 60 (1B) + 39 (5F), the sum
    of two *separate* per-document counts, not a cross-document union;
    merging the two runs' dicts together would silently drop the
    information needed to tell which document a given ambiguity, if any,
    came from).
    """

    zb = zip_loader()
    inst = I.load_instance(zb)
    resolver = RV.make_resolver(inst["facts"])
    registry = RS.register_all(core.Registry.default())
    recipe_list = R.build_recipes(zb, profile)
    results = core.verify_all(recipe_list, resolver, registry)
    results_by_id = {r.claim_id: r for r in results}
    pointer_metas = {}
    for result in results:
        for entry in result.provenance.get("resolved_pointers", ()):
            pointer_metas[entry["pointer"]] = entry["meta"]
    return recipe_list, results_by_id, pointer_metas
