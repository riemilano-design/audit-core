# -*- coding: utf-8 -*-
"""CLI: read a cached EDINET ZIP, build Recipes for one profile, and write
the Claim layer (no ``result``; that is C-1d's job, once the registry and
comparators exist and ``audit_core.verify_all`` is wired in) as JSON in the
same key shape as the C-0 expectation files.

Usage::

    python3 -m adapters.xbrl.run --doc S100Z4B6 --profile P5F --out out.json
"""

import argparse
import json
import sys

import audit_core  # noqa: F401  (C-1d hook: this module is the intended entry
# point for audit_core.verify_all once the registry is built in C-1d; it does
# not call verify_all yet)

from . import edinet
from . import recipes
from . import vocabulary as V


def _serialize_recipe(recipe):
    claim = recipe.claim
    kind = "num" if claim.id.startswith("N") else "text"
    ptrs = recipe.pointers
    schemes = sorted({p.scheme for p in ptrs})
    contract = recipe.contract
    return {
        "id": claim.id,
        "kind": kind,
        "form": claim.form.value,
        "subject": claim.subject,
        "value": claim.value,
        "unit": claim.unit,
        "word": claim.provenance.get("word"),
        "modifiers": {
            "population": claim.modifiers.population,
            "time_range": list(claim.modifiers.time_range) or None,
            "normalization": claim.modifiers.normalization,
        },
        "evidence": {
            "schemes": schemes,
            "pointers": [str(p) for p in ptrs],
        },
        "contract": None if contract is None else {
            "comparator": contract.comparator,
            "tolerance": (contract.params or {}).get("tolerance"),
        },
    }


def build_claim_layer(doc_id, profile_name, expected_sha256=None):
    profile = V.PROFILES[profile_name]
    zb = edinet.read_cached(doc_id, expected_sha256=expected_sha256)
    recipe_list = recipes.build_recipes(zb, profile)
    return {
        "document": doc_id,
        "profile": profile_name,
        "claims": [_serialize_recipe(r) for r in recipe_list],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", required=True, help="EDINET docID (ZIP must already be cached locally)")
    parser.add_argument("--profile", required=True, choices=sorted(V.PROFILES.keys()))
    parser.add_argument("--zip-sha256", default=None, help="optional expected sha256 of the cached ZIP")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = build_claim_layer(args.doc, args.profile, expected_sha256=args.zip_sha256)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("written:", args.out, "claims:", len(out["claims"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
