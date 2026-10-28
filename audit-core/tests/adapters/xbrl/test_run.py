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


class DefaultProfileTest(unittest.TestCase):
    """既定 profile。人間の決定 2026-10-13 で P16、2026-10-14 で P20、2026-10-20(段 2)で P21、
    **同日の期を縛る P22 の段 2 で P22**、2026-10-23 の P26 の段 2 で **P26**、2026-10-28 の P27 の段 2 で **P27**。字で留める。"""

    def test_default_profile_is_p27_literally(self):
        from adapters.xbrl import vocabulary as V
        self.assertEqual(V.DEFAULT_PROFILE, "P27")
        self.assertIn("P22", V.PROFILES)      # 古い既定は消えていない(明示で呼べる)
        self.assertIn("P20", V.PROFILES)      # 古い既定は消えていない(明示で呼べる)
        self.assertIn("P21", V.PROFILES)
        self.assertIn(V.DEFAULT_PROFILE, V.PROFILES)

    def test_cli_without_profile_uses_the_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "out.json")
            rc = RUN.main(["--doc", M.DOC_5["docID"], "--zip-sha256", M.DOC_5["sha256"], "--out", out_path])
            self.assertEqual(rc, 0)
            with open(out_path, encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data["profile"], "P27")      # 2026-10-28 の P27 の段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)から P27(それまでは P26)
            explicit = RUN.build_claim_layer(M.DOC_5["docID"], "P27", expected_sha256=M.DOC_5["sha256"])
            self.assertEqual(data["claims"], explicit["claims"])

    def test_explicit_profile_still_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "out.json")
            RUN.main(["--doc", M.DOC_5["docID"], "--profile", "P5F", "--zip-sha256", M.DOC_5["sha256"], "--out", out_path])
            with open(out_path, encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["profile"], "P5F")


if __name__ == "__main__":
    unittest.main()
