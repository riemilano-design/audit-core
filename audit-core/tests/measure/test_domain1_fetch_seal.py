"""新領域① の取得の封を門にする(取得の前に commit される試験)。

守るのは 3 つ: 封が名指したファイルだけを取ること / 生ファイルを repo に置かないこと /
取得が一度だけであること。
"""
import importlib.util
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_FETCH_SEAL_2026-10-15.md")
SCRIPT = os.path.join(ROOT, "measure", "sheet_fetch_2026-10-15.py")

spec = importlib.util.spec_from_file_location("sheet_fetch", SCRIPT)
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


class SealTest(unittest.TestCase):
    def setUp(self):
        with io.open(SEAL, encoding="utf-8") as fh:
            self.doc = fh.read()
        self.rows = [[c.strip().replace("*", "").replace("`", "") for c in l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]

    def test_the_script_fetches_exactly_the_three_sealed_files(self):
        self.assertEqual(len(F.FILES), 3)
        for _, name, want in F.FILES:
            hit = [r for r in self.rows if any(name in c for c in r)]
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (name, len(hit)))
            self.assertTrue(any("{:,}".format(want) in c for c in hit[0]),
                            "%s のバイト数が封と違う: %s" % (name, hit[0]))

    def test_the_script_names_no_other_file(self):
        names = {name for _, name, _ in F.FILES}
        for bad in ("02_sainyuu", "04_jikoubetu_sainyuu", "06_jissitusyuusi"):
            self.assertFalse(any(bad in n for n in names), bad)
            self.assertIn(bad.split("_")[0], self.doc)   # 取得しないものとして封に書いてある

    def test_the_raw_files_live_outside_the_repo(self):
        self.assertTrue(F.CACHE.startswith(os.path.expanduser("~/.cache/")), F.CACHE)
        self.assertNotIn(ROOT, F.CACHE)

    def test_the_record_path_is_inside_the_repo(self):
        self.assertTrue(F.OUT.startswith(os.path.join(ROOT, "fixtures", "sheet")), F.OUT)

    def test_the_license_and_attribution_are_recorded(self):
        self.assertIn("CC BY", F.DATASET)
        self.assertIn("東京都会計管理局", self.doc)
        self.assertIn("creativecommons.org/licenses/by/4.0", self.doc)

    def test_the_seal_forbids_substituting_another_file(self):
        self.assertIn("別のファイルで埋めない", self.doc)

    def test_the_seal_says_the_record_is_committed_before_measuring(self):
        self.assertIn("記録を commit してから M-1 を始める", self.doc)

    def test_m1_has_no_pass_line(self):
        self.assertIn("M-1 の合格線は作らない", self.doc)

    def test_the_fetch_refuses_when_the_record_exists(self):
        import unittest.mock as mock
        with mock.patch.object(os.path, "exists", lambda p: p == F.OUT):
            with self.assertRaises(SystemExit):
                F.main()


if __name__ == "__main__":
    unittest.main()
