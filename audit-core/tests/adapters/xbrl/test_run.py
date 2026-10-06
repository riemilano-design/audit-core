# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest

from . import _material as M
from adapters.xbrl import run as RUN


class BuildClaimLayerTest(unittest.TestCase):
    def test_p1_claim_layer_shape_and_count(self):
        out = RUN.build_claim_layer(M.DOC_1["docID"], "P1", expected_sha256=M.DOC_1["sha256"])
        self.assertEqual(out["document"], M.DOC_1["docID"])
        self.assertEqual(out["profile"], "P1")
        self.assertEqual(len(out["claims"]), 91)
        for c in out["claims"]:
            self.assertEqual(set(c.keys()), {"id", "kind", "form", "subject", "value", "unit", "word", "modifiers", "evidence", "contract"})
            self.assertNotIn("result", c)
            self.assertIn(c["kind"], ("num", "text"))
            self.assertEqual(c["kind"], "num" if c["id"].startswith("N") else "text")

    def test_wrong_sha_raises(self):
        with self.assertRaises(ValueError):
            RUN.build_claim_layer(M.DOC_1["docID"], "P1", expected_sha256="0" * 64)

    def test_cli_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "out.json")
            rc = RUN.main(["--doc", M.DOC_5["docID"], "--profile", "P5F", "--zip-sha256", M.DOC_5["sha256"], "--out", out_path])
            self.assertEqual(rc, 0)
            with open(out_path, encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(len(data["claims"]), 133)


if __name__ == "__main__":
    unittest.main()
