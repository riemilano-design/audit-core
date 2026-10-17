# -*- coding: utf-8 -*-
"""contract v1 の入口(measure/xbrl_verify_external_v1_2026-10-17.py)の試験。

封 `docs/XBRL_CONTRACT_V1_SEAL_2026-10-17.md` の §2 の表を**振る舞いで**固定する。
**人工の入力で 2 本の規則も試す**(実物の材料では発火しないので、ここで確かめる)。
"""
import os
import sys
import unittest

import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

import audit_core as core                                   # noqa: E402

_SP = importlib.util.spec_from_file_location(
    "verify_external_v1",
    os.path.join(ROOT, "measure", "xbrl_verify_external_v1_2026-10-17.py"))
VE = importlib.util.module_from_spec(_SP)
_SP.loader.exec_module(VE)

CUR = "jppfs_cor:NetSales@CurrentYearDuration"
PRI = "jppfs_cor:NetSales@Prior1YearDuration"


def facts(cur=120000000.0, prior=100000000.0):
    return [{"name": "jppfs_cor:NetSales", "context": "CurrentYearDuration",
             "value": cur, "unit": "JPY", "decimals": "-6"},
            {"name": "jppfs_cor:NetSales", "context": "Prior1YearDuration",
             "value": prior, "unit": "JPY", "decimals": "-6"}]


class SingleValueTest(unittest.TestCase):
    def test_1_money_single_value_passes_when_the_value_matches(self):
        out = VE.verify_external(
            {"kind": "single_value", "value": 120.0, "unit": u"百万円",
             "pointers": [CUR]}, facts())
        self.assertEqual(out["state"], "GROUNDED")
        self.assertEqual(out["rule"], u"単一の値(金額)")
        self.assertEqual(out["comparator"], "equals_within")

    def test_2_a_wrong_value_is_a_mismatch(self):
        out = VE.verify_external(
            {"kind": "single_value", "value": 999.0, "unit": u"百万円",
             "pointers": [CUR]}, facts())
        self.assertEqual(out["state"], "VALUE_MISMATCH")

    def test_3_an_absent_pointer_stops(self):
        out = VE.verify_external(
            {"kind": "single_value", "value": 120.0, "unit": u"百万円",
             "pointers": ["jppfs_cor:NoSuch@CurrentYearDuration"]}, facts())
        self.assertEqual(out["state"], "POINTER_NOT_FOUND")

    def test_4_the_unit_scale_comes_from_the_table(self):
        """**千円で渡したら千倍で照らす**(規則は UNIT_SCALE のまま)。"""
        out = VE.verify_external(
            {"kind": "single_value", "value": 120000.0, "unit": u"千円",
             "pointers": [CUR]}, facts())
        self.assertEqual(out["state"], "GROUNDED")
        bad = VE.verify_external(
            {"kind": "single_value", "value": 120000.0, "unit": u"百万円",
             "pointers": [CUR]}, facts())
        self.assertEqual(bad["state"], "VALUE_MISMATCH")


class NoRuleTest(unittest.TestCase):
    def test_5_percent_single_value_has_no_rule(self):
        out = VE.verify_external(
            {"kind": "single_value", "value": 20.0, "unit": u"％",
             "pointers": [CUR]}, facts())
        self.assertEqual(out["state"], VE.UNPROVABLE)
        self.assertIsNone(out["rule"])
        self.assertIn(u"金額の単位を要る", out["reason"])

    def test_6_an_unknown_kind_has_no_rule(self):
        out = VE.verify_external(
            {"kind": "something_else", "value": 1.0, "unit": u"千円",
             "pointers": [CUR]}, facts())
        self.assertEqual(out["state"], VE.UNPROVABLE)
        self.assertIn(u"未知の種類", out["reason"])

    def test_7_the_pointer_count_must_match_the_rule(self):
        out = VE.verify_external(
            {"kind": "difference", "value": 20.0, "unit": u"百万円",
             "pointers": [CUR]}, facts())
        self.assertEqual(out["state"], VE.UNPROVABLE)
        self.assertIn(u"参照先 2 本を要る", out["reason"])
        out2 = VE.verify_external(
            {"kind": "single_value", "value": 20.0, "unit": u"百万円",
             "pointers": [CUR, PRI]}, facts())
        self.assertEqual(out2["state"], VE.UNPROVABLE)
        self.assertIn(u"参照先 1 本を要る", out2["reason"])

    def test_8_no_rule_means_no_verification(self):
        """**規則が無い応答は照合の跡を持たない。**"""
        out = VE.verify_external(
            {"kind": "single_value", "value": 20.0, "unit": u"％",
             "pointers": [CUR]}, facts())
        self.assertIsNone(out["recomputed"])
        self.assertIsNone(out["comparator"])


class TwoPointerTest(unittest.TestCase):
    """**実物では発火しない規則を、人工の入力で確かめる**(封 §9 の 2)。"""

    def test_9_difference_uses_two_pointers(self):
        out = VE.verify_external(
            {"kind": "difference", "value": 20.0, "unit": u"百万円",
             "pointers": [CUR, PRI]}, facts())
        self.assertEqual(out["state"], "GROUNDED")
        self.assertEqual(out["comparator"], "diff(a-b) equals_within")
        bad = VE.verify_external(
            {"kind": "difference", "value": 999.0, "unit": u"百万円",
             "pointers": [CUR, PRI]}, facts())
        self.assertEqual(bad["state"], "VALUE_MISMATCH")

    def test_10_ratio_change_needs_a_ratio_unit(self):
        out = VE.verify_external(
            {"kind": "ratio_change", "value": 20.0, "unit": u"％",
             "pointers": [CUR, PRI]}, facts())
        self.assertEqual(out["state"], "GROUNDED")
        self.assertEqual(out["comparator"], "pct_change(cur,prior)")
        bad = VE.verify_external(
            {"kind": "ratio_change", "value": 20.0, "unit": u"百万円",
             "pointers": [CUR, PRI]}, facts())
        self.assertEqual(bad["state"], VE.UNPROVABLE)
        self.assertIn(u"率の単位を要る", bad["reason"])

    def test_11_ratio_change_detects_a_wrong_rate(self):
        out = VE.verify_external(
            {"kind": "ratio_change", "value": 50.0, "unit": u"％",
             "pointers": [CUR, PRI]}, facts())
        self.assertEqual(out["state"], "VALUE_MISMATCH")


class ContractTableTest(unittest.TestCase):
    def test_12_the_table_has_exactly_three_rules(self):
        self.assertEqual(sorted(VE.RULES),
                         ["difference", "ratio_change", "single_value"])
        self.assertEqual([VE.RULES[k][1] for k in
                          ("single_value", "difference", "ratio_change")],
                         [1, 2, 2])

    def test_13_contract_for_is_the_single_decision_point(self):
        c, why = VE.contract_for("single_value", u"千円", 1)
        self.assertIsNotNone(c)
        self.assertIsNone(why)
        self.assertEqual(c.params["unit_scale"], 1000.0)
        self.assertEqual(c.params["claim_scale"], 1000.0)
        c2, why2 = VE.contract_for("single_value", u"ドル", 1)
        self.assertIsNone(c2)
        self.assertIn(u"金額の単位を要る", why2)


class UncheckedTest(unittest.TestCase):
    def test_14_every_answer_carries_the_four_unchecked_attributes(self):
        for spec in ({"kind": "single_value", "value": 120.0, "unit": u"百万円",
                      "pointers": [CUR]},
                     {"kind": "single_value", "value": 1.0, "unit": u"％",
                      "pointers": [CUR]},
                     {"kind": "difference", "value": 20.0, "unit": u"百万円",
                      "pointers": [CUR, PRI]}):
            out = VE.verify_external(spec, facts())
            self.assertEqual(out["unchecked"], VE.UNCHECKED)
            self.assertEqual(len(out["unchecked"]), 4)

    def test_15_a_dimensioned_or_prior_period_pointer_still_passes(self):
        """**未検査属性は本当に見ていない**(棚卸し §2 と同じ振る舞い)。"""
        f = [{"name": "jppfs_cor:NetSales",
              "context": "Prior1YearDuration_NonConsolidatedMember",
              "value": 120000000.0, "unit": "USD", "decimals": "-6"}]
        out = VE.verify_external(
            {"kind": "single_value", "value": 120.0, "unit": u"百万円",
             "pointers":
                 ["jppfs_cor:NetSales@Prior1YearDuration_NonConsolidatedMember"]},
            f)
        self.assertEqual(out["state"], "GROUNDED")
        self.assertIn(u"単位", out["unchecked"])


if __name__ == "__main__":
    unittest.main()


class ToleranceTest(unittest.TestCase):
    def test_16_the_rate_tolerance_is_cores_own_constant(self):
        """**新しい数を作っていない**ことを、Core の定数と突き合わせて示す。"""
        from adapters.xbrl import recipes as R
        self.assertEqual(VE.DEFAULT_PCT_TOLERANCE, R.PCT_TOLERANCE_DEFAULT)
        c, _ = VE.contract_for("ratio_change", u"％", 2)
        self.assertEqual(c.params["tolerance"], R.PCT_TOLERANCE_DEFAULT)

    def test_17_the_caller_may_state_the_tolerance(self):
        out = VE.verify_external(
            {"kind": "ratio_change", "value": 20.0, "unit": u"％",
             "pointers": [CUR, PRI], "tolerance": 0.001}, facts())
        self.assertEqual(out["state"], "GROUNDED")
        tight = VE.verify_external(
            {"kind": "ratio_change", "value": 20.1, "unit": u"％",
             "pointers": [CUR, PRI], "tolerance": 0.001}, facts())
        self.assertEqual(tight["state"], "VALUE_MISMATCH")
        loose = VE.verify_external(
            {"kind": "ratio_change", "value": 20.1, "unit": u"％",
             "pointers": [CUR, PRI], "tolerance": 1.0}, facts())
        self.assertEqual(loose["state"], "GROUNDED")


class ExistingPathsTest(unittest.TestCase):
    """**既存の経路を変えていない**ことを import の向きで示す(封 §1)。"""

    def test_18_the_entry_point_is_not_imported_by_the_existing_engine(self):
        import io as _io
        import re
        for rel in ("adapters/xbrl/recipes.py", "adapters/xbrl/verify_document.py",
                    "adapters/xbrl/resolve.py", "adapters/xbrl/comparators.py",
                    "adapters/xbrl/instance.py", "adapters/xbrl/run.py"):
            with _io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                src = fh.read()
            self.assertIsNone(re.search(r"verify_external", src),
                              u"**%s が新しい入口を参照している**" % rel)


class YenExclusionTest(unittest.TestCase):
    """**`円` は v1 の対象外**(独立監査の指摘。2026-10-17)。"""

    def test_19_raw_yen_has_no_rule(self):
        out = VE.verify_external(
            {"kind": "single_value", "value": 120000000.0, "unit": u"円",
             "pointers": [CUR]}, facts())
        self.assertEqual(out["state"], VE.UNPROVABLE)
        self.assertIsNone(out["rule"])
        self.assertIsNone(out["recomputed"])
        self.assertIn(u"金額の単位を要る", out["reason"])

    def test_20_the_exclusion_is_declared_and_only_yen(self):
        self.assertEqual(VE.EXCLUDED_MONEY_UNITS, (u"円",))
        c, why = VE.contract_for("single_value", u"円", 1)
        self.assertIsNone(c, u"**円で contract を作ってはいけない**")
        self.assertIsNotNone(why)
        for unit, want in ((u"千円", 1000.0), (u"百万円", 1000000.0),
                           (u"億円", 100000000.0), (u"兆円", 1000000000000.0)):
            ok, _w = VE.contract_for("single_value", unit, 1)
            self.assertIsNotNone(ok, unit)
            self.assertEqual(ok.params["claim_scale"], want, unit)

    def test_21_the_reason_for_the_exclusion_is_recorded_in_the_source(self):
        """**なぜ外したか**が file に書いてあること(既存コードとの食い違い)。"""
        import io as _io
        with _io.open(os.path.join(ROOT, "measure",
                                   "xbrl_verify_external_v1_2026-10-17.py"),
                      encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(u"_direct_value_claim", src)
        self.assertIn(u"独立監査の指摘", src)
        self.assertIn(u"**封の字は直さず、ここで外す。**", src)

    def test_22_the_placement_deviation_is_recorded(self):
        import io as _io
        with _io.open(os.path.join(ROOT, "measure",
                                   "xbrl_verify_external_v1_2026-10-17.py"),
                      encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(u"test_only_recipes_and_run_import_core_among_adapter_files",
                      src)
        self.assertIn(u"**一覧を書き換えて通すことはしない**", src)
        self.assertIn(u"人間が決める", src)


class ReviseRecordTest(unittest.TestCase):
    """**REVISE の 2 点が結果文書に記録されていること**(2026-10-17)。"""

    def setUp(self):
        import io as _io
        with _io.open(os.path.join(ROOT, "docs",
                                   "XBRL_CONTRACT_V1_RESULT_2026-10-17.md"),
                      encoding="utf-8") as fh:
            self.t = fh.read()

    def test_23_the_yen_exclusion_is_recorded_with_its_reason(self):
        b = self.t[self.t.index(u"### §7-1"):self.t.index(u"### §7-2")]
        self.assertIn(u"`recipes._direct_value_claim`", b)
        self.assertIn(u"`EXCLUDED_MONEY_UNITS`", b)
        self.assertIn(u"封の字は直さず、ここに食い違いを記録する。**", b)
        self.assertIn(u"**`円` は 1 行も無い**", b)

    def test_24_the_boundary_violation_is_recorded(self):
        b = self.t[self.t.index(u"### §7-2"):self.t.index(u"### §7-3")]
        self.assertIn(u"test_only_recipes_and_run_import_core_among_adapter_files",
                      b)
        self.assertIn(u"**一覧を書き換えて通すことはしない**", b)
        self.assertIn(u"**逆向きの既存の規則", b)
        self.assertIn(u"人間が決める", b)

    def test_25_the_allowed_list_was_not_edited(self):
        """**境界の一覧を書き換えていない**ことを git で確かめる。"""
        import subprocess
        out = subprocess.run(
            ["git", "diff", "--", "tests/adapters/xbrl/test_boundary.py"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "",
                         u"**既存の境界試験に差分が在る**")

    def test_26_the_entry_point_is_not_in_the_adapters_directory(self):
        self.assertFalse(os.path.exists(os.path.join(
            ROOT, "adapters", "xbrl", "verify_external.py")))
        self.assertTrue(os.path.exists(os.path.join(
            ROOT, "measure", "xbrl_verify_external_v1_2026-10-17.py")))


class StalePathTest(unittest.TestCase):
    """**旧い道を残した理由が、コードと文書の両方に在ること**(再監査の軽微な指摘)。"""

    def setUp(self):
        import io as _io
        self.src = _io.open(os.path.join(ROOT, "measure",
                                         "xbrl_contract_v1_2026-10-17.py"),
                            encoding="utf-8").read()
        self.doc = _io.open(os.path.join(ROOT, "docs",
                                         "XBRL_CONTRACT_V1_RESULT_2026-10-17.md"),
                            encoding="utf-8").read()

    def test_27_the_docstring_points_at_the_new_path(self):
        head = self.src[:self.src.index('"""', 40)]
        self.assertIn(u"measure/xbrl_verify_external_v1_2026-10-17.py", head)
        self.assertNotIn(u"adapters/xbrl/verify_external.py", head)

    def test_28_the_frozen_note_is_kept_with_its_reason(self):
        import io as _io
        import json
        rec = json.load(_io.open(os.path.join(
            ROOT, "fixtures", "xbrl", "cd8", "contract_v1_2026-10-17.json"),
            encoding="utf-8"))
        note = [x.get(u"注") for x in rec[u"**予測との照合**"][u"欄ごと"]
                if x.get(u"注")]
        self.assertEqual(len(note), 1)
        # **記録に残った旧い道が、script の側にも同じ字で在る**
        # (`注` は 3 つの文字列の連結なので、記録の 1 本の字は source に
        #  そのままは現れない。**両方に在る旧い道の字**で突き合わせる)
        old = u"tests/adapters/xbrl/test_verify_external.py"
        self.assertIn(old, note[0])
        self.assertIn(old, self.src)
        self.assertIn(u"**字を直すと script が自分の記録を再現しなくなる**", self.src)
        self.assertIn(u"**字を直すと script が自分の凍結した記録を再現しなくなる。**",
                      self.doc)

    def test_29_the_reaudit_verdict_is_recorded(self):
        b = self.doc[self.doc.index(u"### §7-4"):]
        self.assertIn(u"**GO**", b)
        self.assertIn(u"c75be11225891c5d", b)
        self.assertIn(u"**境界試験が 12 本緑**", b)
