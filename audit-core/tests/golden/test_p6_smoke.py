# -*- coding: utf-8 -*-
"""Core 接続 C-1g §F: profile P6 の 3 書類の計測は司令塔が
``fixtures/xbrl/run_core_path.py`` で回す(この試験はそれの代わりではない)。
ここで確かめるのは最小限 -- P6 で 3 書類が例外なく完走し、Claim の総数が
91・133・140(P1 x 1B / P5F x 5F と同じ総数。P6 のフラグは束縛や state を
変えるだけで、抽出される Claim の個数そのものは変えない)であること。
``§3`` の ID 単位の予測をここへ書き写さない(それは照合であって試験では
ない)。
"""

import unittest

from tests.adapters.xbrl import _material as M
from adapters.xbrl import instance as I
from adapters.xbrl import recipes as R
from adapters.xbrl import registry_setup as RS
from adapters.xbrl import resolve as RV
from adapters.xbrl import vocabulary as V

import audit_core as core


class P6SmokeTest(unittest.TestCase):
    def _run(self, doc):
        zb = M.load_zip_bytes(doc["docID"], doc["sha256"])
        inst = I.load_instance(zb)
        recipe_list = R.build_recipes(zb, V.P6)
        resolver = RV.make_resolver(inst["facts"])
        registry = RS.register_all(core.Registry.default())
        results = core.verify_all(recipe_list, resolver, registry)
        self.assertEqual(len(results), len(recipe_list))
        return recipe_list

    def test_1b_p6_completes_with_91_claims(self):
        recipe_list = self._run(M.DOC_1)
        self.assertEqual(len(recipe_list), 91)

    def test_5f_p6_completes_with_133_claims(self):
        recipe_list = self._run(M.DOC_5)
        self.assertEqual(len(recipe_list), 133)

    def test_3rd_p6_completes_with_140_claims(self):
        recipe_list = self._run(M.DOC_3RD)
        self.assertEqual(len(recipe_list), 140)


if __name__ == "__main__":
    unittest.main()
