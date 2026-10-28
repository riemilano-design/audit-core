# -*- coding: utf-8 -*-
"""棚卸し(docs/XBRL_VERIFY_INVENTORY_2026-10-17.md)の門。

**探りの結果はコードから測り直す**(記録の写しを信じない)。
**対照が GROUNDED であること**を要求する(対照が壊れた探りは何も示さない)。
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
DOC = os.path.join(ROOT, "docs", "XBRL_VERIFY_INVENTORY_2026-10-17.md")
REC = os.path.join(FX, "verify_inventory_2026-10-17.json")
ENGINE_SHA = {"core/py/audit_core/verify.py": "d29b21dccec8af24",
              "adapters/xbrl/comparators.py": "d8706338325e725b",
              "adapters/xbrl/resolve.py": "a41043763c1d4073",
              "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad"}
# 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1・§4 (a′) が宣言した遷移。verify_document.py の docstring の 1 行(+1 行・-1 行。実行の字は変えない)。
# 上の ENGINE_SHA の 67e7639de3f5f2ad(測った時点の値)は残す。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ(他の file は遷移を持たない: 動いたら赤のまま)。
SEAL_DEFAULT_P27 = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"
VD_DOCSTRING_DECLARED = {"adapters/xbrl/verify_document.py": ("c3791080ab5aef2f", SEAL_DEFAULT_P27)}


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec():
    return json.load(io.open(REC, encoding="utf-8"))


class ProbeTest(unittest.TestCase):
    """**記録ではなく、いまのコードで探りをやり直す。**"""

    def setUp(self):
        self.t = text(DOC)
        self.r = rec()
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "inv", os.path.join(ROOT, "measure",
                                "xbrl_verify_inventory_2026-10-17.py"))
        self.M = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(self.M)

    def test_1_the_control_passes_or_nothing_is_shown(self):
        p1 = self.M.part1()
        self.assertTrue(p1[0][u"探り"].startswith(u"0"))
        self.assertEqual(p1[0][u"**結果**"], "GROUNDED",
                         u"**対照が通らない探りは何も示さない**")

    def test_2_existence_and_value_are_the_two_that_stop(self):
        p1 = {c[u"探り"]: c for c in self.M.part1()}
        stop = [k for k, c in p1.items()
                if not k.startswith(u"0") and c[u"**止めたか**"]]
        self.assertEqual(sorted(stop), [u"1 実在しない参照先", u"2 値が違う"])
        self.assertIn(u"**止めたのは 2 件、通したのは 4 件である。**", self.t)

    def test_3_unit_period_dimension_duplicate_are_not_checked(self):
        """**単位・期間・次元・重複は通る**(いまのコードで測り直す)。"""
        p1 = self.M.part1()
        for c in p1:
            if c[u"探り"][0] in "3456":
                self.assertEqual(c[u"**結果**"], "GROUNDED", c[u"探り"])
                self.assertIn(c[u"探り"], self.t, c[u"探り"])

    def test_4_the_comparator_does_not_read_the_facts_unit(self):
        """**文ではなく振る舞いで確かめる** ― 単位だけ違う fact が通る。"""
        base = {"name": "jppfs_cor:CurrentAssets",
                "context": "CurrentYearInstant", "value": 771000.0,
                "unit": "USD", "decimals": "-3"}
        got = self.M.probe([base],
                           "jppfs_cor:CurrentAssets@CurrentYearInstant",
                           771000.0)
        self.assertEqual(got[u"state"], "GROUNDED")

    def test_5_no_linkbase_is_read(self):
        import subprocess
        out = subprocess.run(
            ["git", "grep", "-l", "-E",
             "calculationLink|presentationLink|definitionLink", "--",
             "adapters", "core"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "",
                         u"**リンクベースを読む場所が在る: %s**" % out.stdout)
        self.assertIn(u"**リンクベース(`calculation`/`presentation`/\n"
                      u"`definition`)を読む場所はコードに無い。**", self.t)


class LiveTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_6_only_half_of_the_named_rows_can_be_verified(self):
        t = self.r[u"**第 2 部 実物での発火**"][u"数"]
        named, ok = t[u"席が名指した行"], t[u"検証できた行"]
        self.assertEqual(named, 85)
        self.assertLess(ok, named)
        self.assertEqual(ok, t[u"state GROUNDED"] + t[u"state VALUE_MISMATCH"])
        self.assertIn(u"**席が名指した %d 行のうち、今の Core で検証できたのは "
                      u"%d 行だけである。**" % (named, ok), self.t)

    def test_7_the_three_reasons_are_counted_and_printed(self):
        t = self.r[u"**第 2 部 実物での発火**"][u"数"]
        for k, label in ((u"**contract が無い(検証できない)**", u"contract が無い"),
                         (u"**Core に主張が無い(検証できない)**", u"Core に主張が無い"),
                         (u"**contract が参照先 2 本を要る"
                          u"(1 本渡しでは検証できない)**",
                          u"contract が参照先 2 本を要る")):
            self.assertIn(u"| **%s** | %d |" % (label, t[k]), self.t, label)
        self.assertEqual(t[u"席が名指した行"] + t[u"席が名指さなかった行"], 192)

    def test_8_no_row_holds_a_gold_comparison(self):
        """**棚卸しは正解と照合していない。**行の欄に「正解」が無いことで示す。"""
        rows = self.r[u"**第 2 部 実物での発火**"]["rows"]
        self.assertTrue(rows)
        for x in rows:
            for k in x:
                self.assertNotIn(u"正解", k, (x.get(u"id"), k))
        for c in self.r[u"**第 1 部 人工の探り**"]:
            for k in c:
                self.assertNotIn(u"正解", k, (c.get(u"探り"), k))
        self.assertIn(u"**正解とは照合していない**", self.t)


class DisciplineTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_9_engine_untouched(self):
        for rel, want in ENGINE_SHA.items():
            if want is None:
                continue
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()[:16]
            if got != want and rel in VD_DOCSTRING_DECLARED:
                later, seal_rel = VD_DOCSTRING_DECLARED[rel]
                added = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", seal_rel],
                                       cwd=ROOT, capture_output=True, text=True).stdout.split()
                self.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている**" % rel)
        self.assertIn(u"**engine は 1 行も変えていない。0 USD・席は呼んでいない。"
                      u"正解とは照合していない。**", self.t)

    def test_10_my_probe_defect_is_recorded(self):
        b = self.t[self.t.index(u"### §2-2"):]
        self.assertIn(u"**先に対照を入れていなかった**", self.t)
        self.assertIn(u"接頭辞(`jppfs_cor:`)が無く、1 件も解けていなかった", b)
        self.assertIn(u"**対照が GROUNDED でなければ script が止まる。**", b)

    def test_11_it_does_not_decide_the_next_step(self):
        b = self.t[self.t.index(u"## §6"):]
        self.assertIn(u"次に人間が決めること", b)
        self.assertIn(u"**4 つの評価軸は人間が定めたものを使う**", b)
        self.assertIn(u"**足せば「値が合うだけで通す」ことは無くなるが、"
                      u"新しい拒否が増える**", b)


if __name__ == "__main__":
    unittest.main()
