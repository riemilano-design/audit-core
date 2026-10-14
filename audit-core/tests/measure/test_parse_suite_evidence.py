# -*- coding: utf-8 -*-
"""`measure/parse_suite_evidence.py` の試験。

**崩し方を表で当てる**(1 か所ずつ塞いで 3 回失敗した 2026-10-15 の記録)。
```
GOOD = 完走した 1 本の形
```
"""

import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
# tests/measure/<file> -> tests/measure -> tests -> audit-core(3 段。2 段だと tests/ を
# audit-core と取り違えて「道具が無い」で落ちる ― 実際に 1 回落ちた)。
ROOT = os.path.dirname(os.path.dirname(HERE))
TOOL = os.path.join(ROOT, "measure", "parse_suite_evidence.py")


def _load():
    spec = importlib.util.spec_from_file_location("parse_suite_evidence", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P = _load()

GOOD = """=== HEAD(この run の間は 1 commit もしない) ===
abc1234 test(x): y
=== status(前) ===

=== 1) pytest(path 指定なし) ===
1141 passed in 1148.97s (0:19:08)

=== 2) unittest discover -s tests -t . ===
Ran 1036 tests in 1121.317s
OK

=== 3) 変異 89 本 ===
Ran 5 tests in 1069.202s
OK
predicted == actual: 88 本 / 外れ: 1 本 (X-R7b)

=== status(後) ===
=== HEAD(後) ===
abc1234 test(x): y
"""


class GoodLogTest(unittest.TestCase):
    def test_every_number_comes_out(self):
        self.assertEqual({"head": "abc1234", "pytest_passed": 1141, "discover_ran": 1036,
                          "mutation_test_methods": 5, "mutation_predicted": 88,
                          "mutation_misses": 1},
                         P.parse(GOOD))

    def test_the_discover_count_is_not_the_mutation_count(self):
        """``Ran N tests`` はログに 2 回出る。**節で分けていないと取り違える。**"""

        out = P.parse(GOOD)
        self.assertNotEqual(out["discover_ran"], out["mutation_test_methods"])
        self.assertEqual(1036, out["discover_ran"])
        self.assertEqual(5, out["mutation_test_methods"])


class BrokenLogTest(unittest.TestCase):
    """**崩れたログを緑として記録しない。**崩し方を表にする。"""

    def _broken(self):
        return {
            "空": "",
            "空白だけ": "   \n\n",
            "赤が在る": GOOD.replace("OK", "FAILED (failures=1)", 1),
            "pytest の節が無い": GOOD.replace("=== 1) pytest(path 指定なし) ===", "=== 1) なにか ==="),
            "discover の節が無い": GOOD.replace("=== 2) unittest discover -s tests -t . ===", "=== 2) なにか ==="),
            "変異の節が無い": GOOD.replace("=== 3) 変異 89 本 ===", "=== 3) なにか ==="),
            "HEAD の節が無い": GOOD.replace("=== HEAD(この run の間は 1 commit もしない) ===", "=== さいしょ ==="),
            "pytest の数が無い": GOOD.replace("1141 passed in 1148.97s (0:19:08)", "(途中で止めた)"),
            "pytest の数が 2 つ": GOOD.replace("1141 passed in 1148.97s (0:19:08)",
                                            "1141 passed in 1.0s\n999 passed in 2.0s"),
            "discover の Ran が無い": GOOD.replace("Ran 1036 tests in 1121.317s", "(途中)"),
            "discover の OK が無い": GOOD.replace("Ran 1036 tests in 1121.317s\nOK",
                                              "Ran 1036 tests in 1121.317s"),
            "変異の予測の行が無い": GOOD.replace("predicted == actual: 88 本 / 外れ: 1 本 (X-R7b)", ""),
            "変異の予測の行が 2 つ": GOOD.replace(
                "predicted == actual: 88 本 / 外れ: 1 本 (X-R7b)",
                "predicted == actual: 88 本 / 外れ: 1 本 (X-R7b)\npredicted == actual: 80 本 / 外れ: 9 本 (z)"),
            "HEAD の sha が無い": GOOD.replace("abc1234 test(x): y", "(取れなかった)", 1),
            "節の見出しが 1 つも無い": GOOD.replace("===", "---"),
        }

    def test_each_broken_log_is_refused(self):
        for name, text in self._broken().items():
            with self.subTest(name):
                with self.assertRaises(ValueError, msg=name):
                    P.parse(text)

    def test_the_table_covers_more_than_a_couple_of_shapes(self):
        """**表が縮んでいないこと**(0 件や 1 件なら「通った」ではなく「届いていない」)。"""

        self.assertGreaterEqual(len(self._broken()), 14)


class WrittenEvidenceTest(unittest.TestCase):
    """記録した json が、**この run の形で**取り出されたものであること。"""

    def test_the_committed_json_matches_what_the_parser_produces(self):
        path = os.path.join(ROOT, "fixtures", "xbrl", "p20", "suite_evidence_2026-10-14.json")
        with io.open(path, encoding="utf-8") as fh:
            saved = json.load(fh)
        self.assertEqual(sorted(P.parse(GOOD)), sorted(saved), "欄の形が変わっている")
        # **HEAD の値は字で固定しない。** 固定すると、文書を 1 行直すたびに
        # 「撮り直す → 試験の字を直す → また撮り直す」で終わらない(2026-10-14 に気づいた)。
        # 固定するのは**書き写しで間違えた数**だけにして、HEAD は形だけ見る。
        # どの commit を測ったかは json と結果文書の両方に在り、
        # `test_p20.SuiteEvidenceTest.test_the_frozen_head_is_the_one_the_document_names`
        # が 2 つの一致を見る。
        self.assertRegex(saved["head"], r"^[0-9a-f]{7,40}$")
        # 2026-10-14 の完走した 1 本の数(手で書き写していない)。
        self.assertEqual(1141, saved["pytest_passed"])
        self.assertEqual(1036, saved["discover_ran"])
        self.assertEqual(88, saved["mutation_predicted"])
        self.assertEqual(1, saved["mutation_misses"])


if __name__ == "__main__":
    unittest.main()
