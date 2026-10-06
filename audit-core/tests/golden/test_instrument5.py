# -*- coding: utf-8 -*-
"""C-1d §3.5 ("計器 5"): for every Claim carrying a ``sign_token``
(P-8's own-number-only match, ``extract.own_sign_match`` /
``claim["sign_token"] = pm.group(0)`` in ``recipes.py``), the number
written inside that token text must equal ``abs(claim.value)``. 0
mismatches is the gate. 5F has 15 such Claims; 1B has 0 (recorded as "no
such material", not as a pass).
"""

import re
import unittest

from tests.adapters.xbrl import _material as M
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

_TOKEN_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _tokened_recipes(zb, profile):
    recipe_list = R.build_recipes(zb, profile)
    return [r for r in recipe_list if r.claim.provenance.get("sign_token")]


class Instrument5Test(unittest.TestCase):
    def test_5f_sign_token_number_matches_claim_value(self):
        zb = M.load_zip_bytes(M.DOC_5["docID"], M.DOC_5["sha256"])
        tokened = _tokened_recipes(zb, V.P5F)
        self.assertEqual(len(tokened), 15)

        mismatches = []
        for recipe in tokened:
            token = recipe.claim.provenance["sign_token"]
            match = _TOKEN_NUMBER_RE.search(token)
            self.assertIsNotNone(match, "sign_token %r has no number" % (token,))
            number_in_token = float(match.group(1))
            if abs(number_in_token - abs(recipe.claim.value)) > 1e-9:
                mismatches.append((recipe.claim.id, token, number_in_token, recipe.claim.value))
        self.assertEqual(mismatches, [])

    def test_1b_has_no_sign_token_claims(self):
        zb = M.load_zip_bytes(M.DOC_1["docID"], M.DOC_1["sha256"])
        tokened = _tokened_recipes(zb, V.P1)
        # 0 is "not present in this material", not "checked and passed".
        self.assertEqual(len(tokened), 0)


if __name__ == "__main__":
    unittest.main()
