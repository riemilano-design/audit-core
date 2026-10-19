# -*- coding: utf-8 -*-
"""外部主張の入口(``adapters/xbrl/verify_external.py``)。実材料での再現と対照。

封 `docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md` の F-3〜F-6・F-8。
**材料の ZIP(``~/.cache/audit-core/edinet/``)と ``fixtures/xbrl/cd8`` の記録を読む。無ければ落ちる(skip にしない)。**

**PP(期間の対、2026-10-19 段 2)**: 封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md`
(commit `790a5c5` + 追記 1 `78a04f5`)。合成の入口試験(符号つき/符号なし/0 本/2 本/重複)と、
実材料の再現(段 1 の記録 ``period_pair_2026-10-19.json`` の 13 行 + 重複 4 行、
③ の記録の 175 行、対照 4 種)。
"""
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

import audit_core as core

from adapters.xbrl import edinet as ED
from adapters.xbrl import holds as H
from adapters.xbrl import instance as I
from adapters.xbrl import registry_setup as RS
from adapters.xbrl import verify_external as VE

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_CD8 = os.path.join(_ROOT, "fixtures", "xbrl", "cd8")
_REC = os.path.join(_CD8, "period_unit_hold_2026-10-19.json")
_PP_REC = os.path.join(_CD8, "period_pair_2026-10-19.json")
_DIAG = os.path.join(_CD8, "dim_diag_2026-10-17.json")
_DRAW = os.path.join(_CD8, "draw_2026-10-17.json")

#: PP-2(追記 1)で段 1(封 §1 の下見)の「兄弟 2 本」から「兄弟 1 本」に変わる 4 行
#: (instance 内の重複。値が全部同じ。``docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md`` 追記 1)。
PP_DUPLICATE_KEYS = (("S100YWGX", "R004"), ("S100YWGX", "R006"),
                     ("S100YWGX", "R008"), ("S100YZCT", "R005"))


def _load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(_ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


class ContractTest(unittest.TestCase):
    """contract v1 の表の写し(``measure/xbrl_verify_external_v1_2026-10-17.py`` と同じ)。"""

    def test_rules_are_the_three_of_v1(self):
        self.assertEqual(sorted(VE.RULES), ["difference", "ratio_change", "single_value"])

    def test_no_rule_cases(self):
        self.assertIsNone(VE.contract_for("single_value", u"百万円", 2)[0])
        self.assertIsNone(VE.contract_for("ratio_change", u"百万円", 2)[0])
        self.assertIsNone(VE.contract_for("single_value", u"円", 1)[0])
        self.assertIsNone(VE.contract_for("nope", u"百万円", 1)[0])

    def test_unknown_kind_is_unprovable_with_checks_listed(self):
        out = VE.verify_external({"kind": "nope", "value": 1, "unit": u"百万円", "pointers": ["a@b"]}, [], {})
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertFalse(out["held"])
        self.assertEqual(out["checks"], H.CHECKS)
        self.assertEqual(out["unchecked"], H.UNCHECKED)


class SyntheticEntryTest(unittest.TestCase):
    F = {"name": "jppfs_cor:NetSales", "context": "CurrentYearDuration", "unit": "JPY",
         "decimals": "-6", "value": 100000000.0}

    def _spec(self, **kw):
        s = {"kind": "single_value", "value": 100.0, "unit": u"百万円",
             "pointers": ["jppfs_cor:NetSales@CurrentYearDuration"]}
        s.update(kw)
        return s

    def test_grounded_when_alone(self):
        out = VE.verify_external(self._spec(), [self.F], {})
        self.assertEqual((out["state"], out["held"], out["hold_rules"]), ("GROUNDED", False, ()))

    def test_held_by_each_rule(self):
        d = dict(self.F, context="CurrentYearDuration_SegMember")
        out = VE.verify_external(self._spec(), [self.F, d],
                                 {"CurrentYearDuration": {"axes": []},
                                  "CurrentYearDuration_SegMember": {"axes": [["x:OperatingSegmentsAxis", "x:Seg"]]}})
        self.assertEqual((out["state"], out["hold_rules"], out["hold_axes"]),
                         ("UNPROVABLE", ("d",), ["x:OperatingSegmentsAxis"]))
        p = dict(self.F, context="Prior1YearDuration")
        out = VE.verify_external(self._spec(), [self.F, p], {})
        self.assertEqual((out["state"], out["hold_rules"]), ("UNPROVABLE", ("P",)))
        u = dict(self.F, context="CurrentYearDuration_UnitTest", unit="USD")
        out = VE.verify_external(self._spec(pointers=["jppfs_cor:NetSales@CurrentYearDuration_UnitTest"]),
                                 [self.F, u], {})
        self.assertEqual((out["state"], out["hold_rules"]), ("UNPROVABLE", ("U",)))

    def test_mismatch_and_not_found_are_not_held(self):
        out = VE.verify_external(self._spec(value=101.0), [self.F, dict(self.F, context="Prior1YearDuration")], {})
        self.assertEqual((out["state"], out["held"]), ("VALUE_MISMATCH", False))
        out = VE.verify_external(self._spec(pointers=["jppfs_cor:Nope@CurrentYearDuration"]), [self.F], {})
        self.assertEqual((out["state"], out["held"]), ("POINTER_NOT_FOUND", False))

    def test_verify_claims_rows_have_the_pinned_fields(self):
        inst = {"facts": [self.F], "contexts": {}, "source": "x"}
        rows = VE.verify_claims([self._spec(id="X1"), {"kind": "nope", "value": 1, "unit": None, "pointers": []}], inst)
        self.assertEqual([tuple(r.keys()) for r in rows], [VE.RESULT_FIELDS] * 2)
        self.assertEqual(rows[0]["id"], "X1")
        self.assertEqual(rows[1]["id"], "EXT2")


class PeriodPairSyntheticTest(unittest.TestCase):
    """PP(期間の対)。合成の入口試験(符号つき/符号なし/0 本/2 本/重複)。

    封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md` §0・追記 1(PP-2)。
    """

    F = {"name": "ns:NetSales", "context": "CurrentYearDuration", "unit": "pure", "value": 10.0}
    G = {"name": "ns:NetSales", "context": "Prior1YearDuration", "unit": "pure", "value": 8.0}

    def _spec(self, **kw):
        s = {"kind": "ratio_change", "value": 25.0, "unit": u"％",
             "pointers": ["ns:NetSales@CurrentYearDuration"]}
        s.update(kw)
        return s

    def test_signed_match_is_grounded_with_derived_pointer(self):
        out = VE.verify_external(self._spec(sign=1), [self.F, self.G], {})
        self.assertEqual(out["state"], "GROUNDED")
        self.assertEqual(out["recomputed"], 25.0)
        self.assertEqual(out["derived_pointers"], ["ns:NetSales@Prior1YearDuration"])
        self.assertTrue(out["direction_checked"])
        self.assertEqual(out["unchecked"], H.UNCHECKED)
        self.assertEqual(out["checks"], H.CHECKS)
        self.assertEqual(out["pointers"], ("ns:NetSales@CurrentYearDuration",), u"席の参照先は変えない")

    def test_sign_mismatch_is_value_mismatch(self):
        out = VE.verify_external(self._spec(sign=-1), [self.F, self.G], {})
        self.assertEqual(out["state"], "VALUE_MISMATCH")

    def test_unsigned_uses_the_absolute_value_and_flags_direction_unchecked(self):
        out = VE.verify_external(self._spec(), [self.F, self.G], {})  # sign を渡さない
        self.assertEqual(out["state"], "GROUNDED")
        self.assertFalse(out["direction_checked"])
        self.assertEqual(out["unchecked"], H.UNCHECKED + (u"方向",))
        self.assertEqual(out["checks"], H.CHECKS, u"CHECKS の定数は変えない")

    def test_zero_siblings_is_unprovable(self):
        out = VE.verify_external(self._spec(sign=1), [self.F], {})
        self.assertEqual((out["state"], out["held"], out["reason"]), ("UNPROVABLE", False, "prior_sibling:0"))
        self.assertEqual(out["derived_pointers"], [])
        self.assertEqual(out["unchecked"], H.UNCHECKED)

    def test_two_differing_siblings_is_unprovable_with_duplicate_marker(self):
        g2 = dict(self.G, value=9.0)
        out = VE.verify_external(self._spec(sign=1), [self.F, self.G, g2], {})
        self.assertEqual((out["state"], out["reason"]), ("UNPROVABLE", "prior_sibling:2;duplicate_values"))

    def test_duplicate_same_value_sibling_is_grounded(self):
        g2 = dict(self.G)
        out = VE.verify_external(self._spec(sign=1), [self.F, self.G, g2], {})
        self.assertEqual(out["state"], "GROUNDED")

    def test_pointer_not_at_a_current_year_frame_is_unprovable(self):
        f = dict(self.F, context="Prior1YearDuration")
        out = VE.verify_external(dict(self._spec(sign=1), pointers=["ns:NetSales@Prior1YearDuration"]), [f], {})
        self.assertEqual((out["state"], out["reason"]), ("UNPROVABLE", "not_current_year"))

    def test_unresolved_pointer_is_unprovable_no_fact(self):
        out = VE.verify_external(self._spec(sign=1, pointers=["ns:Nope@CurrentYearDuration"]),
                                 [self.F, self.G], {})
        self.assertEqual((out["state"], out["reason"]), ("UNPROVABLE", "no_fact"))

    def test_two_pointers_bypasses_pp_and_uses_the_v1_contract(self):
        out = VE.verify_external(self._spec(pointers=["ns:NetSales@CurrentYearDuration",
                                                       "ns:NetSales@Prior1YearDuration"]),
                                 [self.F, self.G], {})
        self.assertEqual(out["state"], "GROUNDED")
        self.assertEqual(out["derived_pointers"], [])

    def test_period_pair_false_restores_the_old_two_pointer_requirement(self):
        out = VE.verify_external(self._spec(sign=1), [self.F, self.G], {}, period_pair=False)
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertIn(u"参照先 2 本を要る", out["reason"])
        self.assertEqual(out["derived_pointers"], [])


class RealMaterialTest(unittest.TestCase):
    """封 F-3・F-4・F-5・F-6: 8 書類での軸の 1:1、192 行の再現、(d) の 6 行の軸、対照。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = _load(_REC)
        cls.docs = _load(_DRAW)[u"引いた 8 件"]
        cls.AT = _mod("measure/xbrl_attr_inject_2026-10-17.py", "attr_for_ve_test")
        cls.A1, cls.MB, cls.IJ, cls.PR = cls.AT.A1, cls.AT.MB, cls.AT.IJ, cls.AT.PR

    def test_f3_axes_are_one_to_one_with_members_in_all_eight_documents(self):
        total, with_members = 0, 0
        for d in self.docs:
            inst = I.load_instance(io.open(ED.cache_path(d), "rb").read())
            for cid, c in inst["contexts"].items():
                total += 1
                with_members += bool(c["members"])
                self.assertEqual(len(c["axes"]), len(c["members"]), (d, cid))
                self.assertEqual([m for _a, m in c["axes"]], c["members"], (d, cid))
                for a, _m in c["axes"]:
                    self.assertTrue(a, (d, cid))
        self.assertGreater(with_members, 0)

    def _material_rows(self):
        """``measure/xbrl_period_unit_hold_2026-10-19.py`` と同じ材料の組み立て(注入後の 8 書類)。"""
        seed, _m = self.IJ.verify_seed_sealed(self.MB.SEED_FILE)
        swap = _load(os.path.join(_CD8, "role_swap_2026-10-17.json"))
        b_by = {(x[u"doc"], x[u"id"]): x for x in swap["rows"]}
        for doc in self.docs:
            zb = io.open(ED.cache_path(doc), "rb").read()
            old, self.A1.TMP = self.A1.TMP, self.MB.TMP
            try:
                text, refs = self.A1.material(doc)
            finally:
                self.A1.TMP = old
            chosen, _c = self.MB.pick_injections(text, refs, seed, doc)
            tampered, pl = self.IJ.apply_edits(text, chosen)
            mrows, _n = self.MB.build_rows(tampered, chosen, pl)
            zb2, _e, _mm = self.PR.build_modified_zip(zb, tampered)
            inst = I.load_instance(zb2)
            yield doc, inst, mrows, b_by

    def test_f4_f5_f6_reproduce_the_record_on_192_rows_and_the_controls(self):
        # 2026-10-19(PP の段 2、封 docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md): この記録は PP の
        # 導入より前(③)に作ったものなので period_pair=False を渡して再現する。この試験の spec は
        # kind="single_value" を常に使う(unit="％" の行も含む)ので、PP の入口条件
        # (kind=="ratio_change") には元々当たらず、実際の挙動は period_pair の値によらない
        # ― それでも「③ の記録は PP なしの経路で検算した」ことを呼び出しの字で残す。
        rec_rows = {(x[u"doc"], x[u"id"]): x for x in self.rec["rows"]}
        diag = {(x[u"doc"], x[u"id"]): x for x in _load(_DIAG)["rows"]}
        registry = RS.register_all(core.Registry.default())
        n_same, n_rows = 0, 0
        ctrl = {"period": [0, 0], "unit": [0, 0], "dim": [0, 0]}
        axes_by_row = {}
        for doc, inst, mrows, b_by in self._material_rows():
            facts, contexts = inst["facts"], inst["contexts"]
            keys = {self.A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f for f in facts}
            for r in mrows:
                b = b_by[(doc, r["id"])]
                ptr, unit, val = b[u"席の参照先"], r[u"単位"], r[u"値"]
                want = rec_rows[(doc, r["id"])]
                n_rows += 1
                if ptr is None:
                    self.assertIsNone(want[u"**合成の後**"])
                    n_same += 1
                    continue
                f = keys.get(self.A1.norm_pointer(ptr))
                loc = ("%s@%s" % (f["name"], f["context"])) if f else ptr
                spec = {"kind": "single_value", "value": val, "unit": unit, "pointers": [loc]}
                out = VE.verify_external(spec, facts, contexts, registry, period_pair=False)
                self.assertEqual(out["state"], want[u"**合成の後**"], (doc, r["id"]))
                if want.get(u"理由") and want[u"**合成の後**"] == "UNPROVABLE" and out["held"]:
                    self.assertEqual(out["reason"], want[u"理由"], (doc, r["id"]))
                n_same += 1
                if (doc, r["id"]) in diag:
                    axes_by_row[(doc, r["id"])] = out["hold_axes"]
                # 対照(GROUNDED の 24 行): 注入 1 件ずつ
                if want[u"v1 の state"] == "GROUNDED":
                    for branch, key_, point_at_injected in ((u"期間(注入)", "period", False),
                                                             (u"単位", "unit", True),
                                                             (u"次元", "dim", False)):
                        fs, key, _bad = self.AT.inject(facts, f, branch)
                        if key is None:
                            continue
                        ctrl[key_][0] += 1
                        o2 = VE.verify_external(dict(spec, pointers=[key if point_at_injected else loc]),
                                                fs, contexts, registry, period_pair=False)
                        ctrl[key_][1] += (o2["state"] == "UNPROVABLE" and o2["held"])
        self.assertEqual(n_rows, 192)
        self.assertEqual(n_same, 192)
        # F-6: 期間 18/18・単位 24/24・次元 24/24
        self.assertEqual(ctrl, {"period": [18, 18], "unit": [24, 24], "dim": [24, 24]})
        # F-5: (d) の 6 行の軸の分類
        classes = {"ConsolidatedOrNonConsolidatedAxis": 0, "OperatingSegmentsAxis": 0, "ComponentsOfEquityAxis": 0}
        self.assertEqual(len(axes_by_row), 6)
        for k, axes in axes_by_row.items():
            self.assertEqual(len(axes), 1, (k, axes))
            classes[axes[0].split(":")[-1]] += 1
        self.assertEqual(classes, {"ConsolidatedOrNonConsolidatedAxis": 2, "OperatingSegmentsAxis": 2,
                                   "ComponentsOfEquityAxis": 2})

    def test_pp_reproduces_the_period_pair_record_the_175_rows_and_the_controls(self):
        """PP(期間の対、段 2)。封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md` §5 段 2。

        H-12: 192 行再現(17 行は PP、うち 13 行は段 1 の記録と一致)。
        H-16: 重複 4 行は PP-2 の後、兄弟 1 本で検算に進む。
        H-18: 残り 175 行は ③ の記録(``**合成の後**``)と一致。
        H-19: 対照 4 種は元の 13 行(兄弟 1 本の行)で 13/13。

        **H-17 の外れ(実測)**: PP(pct_change)の検算そのものは 4 行とも一致する
        (``GROUNDED`` 3・``VALUE_MISMATCH`` 0 相当)が、``S100YWGX`` ``R008`` は
        PP の後に当期の fact へ当てる既存の保留規則 (d)(同額の次元兄弟)が発火し、
        最終 state は ``UNPROVABLE``(``ambiguous_dimension:2``)になる。封 §3 の
        「(d)・P・U は PP の後に当期の fact に対して従来どおり」をそのまま実装した結果で、
        封 H-17 の予測(``GROUNDED`` 3〜4・``VALUE_MISMATCH`` 0〜1)はこの形(保留による
        ``UNPROVABLE``)を数えていない。封は書き換えない(実測のまま報告する)。
        """
        rec_rows = {(x[u"doc"], x[u"id"]): x for x in self.rec["rows"]}
        pp_rows = {(x[u"doc"], x[u"id"]): x for x in _load(_PP_REC)["rows"]}
        PPR = _mod("measure/xbrl_period_pair_rule_2026-10-19.py", "pp_rule_for_pp_product_test")
        registry = RS.register_all(core.Registry.default())
        n_rows = n_ref1 = n_175 = n_dup = 0
        dup_states = []
        ctrl_tally = {u"値": [], u"符号": [], u"前期を消す": [], u"前期を増やす": []}
        for doc, inst, mrows, b_by in self._material_rows():
            facts, contexts = inst["facts"], inst["contexts"]
            keys = {self.A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f for f in facts}
            for r in mrows:
                n_rows += 1
                key = (doc, r["id"])
                b = b_by[key]
                ptr, unit, val = b[u"席の参照先"], r[u"単位"], r[u"値"]
                is_pp_row = unit in (u"％", u"%") and ptr is not None
                if not is_pp_row:
                    # 175 行(参照先なし 20 + 金額 155): PP を当てない。③ の記録と一致(H-18)。
                    want = rec_rows[key]
                    if ptr is None:
                        self.assertIsNone(want[u"**合成の後**"], key)
                        n_175 += 1
                        continue
                    f = keys.get(self.A1.norm_pointer(ptr))
                    loc = ("%s@%s" % (f["name"], f["context"])) if f else ptr
                    spec = {"kind": "single_value", "value": val, "unit": unit, "pointers": [loc]}
                    out = VE.verify_external(spec, facts, contexts, registry)
                    self.assertEqual(out["state"], want[u"**合成の後**"], key)
                    n_175 += 1
                    continue
                # 17 行(ref1): PP。
                n_ref1 += 1
                f = keys.get(self.A1.norm_pointer(ptr))
                loc = ("%s@%s" % (f["name"], f["context"])) if f else ptr
                sign = PPR.sign_from_text(r[u"抜粋"], r[u"数の字面"])
                spec = {"kind": "ratio_change", "value": val, "unit": unit, "pointers": [loc], "sign": sign}
                out = VE.verify_external(spec, facts, contexts, registry)
                want_pp = pp_rows[key]
                if key in PP_DUPLICATE_KEYS:
                    n_dup += 1
                    # H-16: 段 1 の記録は prior_sibling:2(重複)。PP-2 により prior_siblings は
                    # 兄弟 1 本・duplicate_values=False(値が全部同じ)になる。
                    self.assertEqual((want_pp["state"], want_pp["reason"]), ("UNPROVABLE", "prior_sibling:2"), key)
                    siblings, duplicate_values = H.prior_siblings(facts, f)
                    self.assertEqual(len(siblings), 1, key)
                    self.assertFalse(duplicate_values, key)
                    self.assertEqual(len(out["derived_pointers"]), 1, key)
                    dup_states.append(out["state"])
                    if key == ("S100YWGX", "R008"):
                        # H-17 の外れ(実測、docstring 参照): (d) が発火して UNPROVABLE まで下がる。
                        self.assertEqual(out["state"], "UNPROVABLE", key)
                        self.assertTrue(out["held"], key)
                        self.assertIn("d", out["hold_rules"], key)
                        self.assertEqual(out["reason"], "ambiguous_dimension:2", key)
                    else:
                        self.assertEqual(out["state"], "GROUNDED", key)
                elif key == ("S100YYRV", "R014"):
                    # H-12 の外れ(実測。H-10 で既に記録済みの事実と同じ行): 段 1 は
                    # pct_change の検算だけで state を記録した(GROUNDED・recomputed -3.66)が、
                    # 段 2 は封 §0 の 5 どおり PP の後に当期の fact へ (d)・P・U を当てるので、
                    # この行は (d)(同額の次元兄弟、結果 H-10 が実測した行そのもの)が発火して
                    # UNPROVABLE まで下がる。recomputed は検算の値のまま変わらない。
                    self.assertEqual(out["state"], "UNPROVABLE", key)
                    self.assertTrue(out["held"], key)
                    self.assertEqual(out["hold_rules"], ("d",), key)
                    self.assertEqual(out["reason"], "ambiguous_dimension:1", key)
                    self.assertEqual(out["recomputed"], want_pp["recomputed"], key)
                    self.assertEqual(out["derived_pointers"], want_pp["derived_pointers"], key)
                else:
                    # H-12: 段 1(13 行のうち 12 行)の state・reason・recomputed・derived_pointers と一致。
                    self.assertEqual(out["state"], want_pp["state"], key)
                    self.assertEqual(out["reason"], want_pp["reason"], key)
                    self.assertEqual(out["recomputed"], want_pp["recomputed"], key)
                    self.assertEqual(out["derived_pointers"], want_pp["derived_pointers"], key)
                # 対照(13 行すべて。段 1 と同じ作り方。重複 4 行には当てない ― 封 §2 の 13 行のまま)。
                if want_pp.get(u"兄弟の本数") == 1:
                    sibs = H.prior_siblings(facts, f)
                    siblings, _dup = sibs
                    g = siblings[0]
                    ctrl_tally[u"値"].append(
                        VE.verify_external(dict(spec, value=val + 1.0), facts, contexts, registry)["state"])
                    flipped = (-sign) if sign is not None else None
                    ctrl_tally[u"符号"].append(
                        VE.verify_external(dict(spec, sign=flipped), facts, contexts, registry)["state"])
                    facts_rm = [x for x in facts if x is not g]
                    out_rm = VE.verify_external(spec, facts_rm, contexts, registry)
                    ctrl_tally[u"前期を消す"].append((out_rm["state"], out_rm["reason"]))
                    dup = dict(g, value=g["value"] + 1.0)
                    out_add = VE.verify_external(spec, facts + [dup], contexts, registry)
                    ctrl_tally[u"前期を増やす"].append((out_add["state"], out_add["reason"]))

        self.assertEqual(n_rows, 192)
        self.assertEqual(n_ref1, 17)
        self.assertEqual(n_175, 175)
        self.assertEqual(n_dup, 4)
        # H-17 の実測(docstring 参照): GROUNDED 3・UNPROVABLE(保留) 1・VALUE_MISMATCH 0。
        self.assertEqual(dup_states.count("GROUNDED"), 3)
        self.assertEqual(dup_states.count("UNPROVABLE"), 1)
        self.assertEqual(dup_states.count("VALUE_MISMATCH"), 0)
        self.assertEqual(len(ctrl_tally[u"値"]), 13)
        self.assertEqual(ctrl_tally[u"値"].count("VALUE_MISMATCH"), 13)
        self.assertEqual(ctrl_tally[u"符号"].count("VALUE_MISMATCH"), 13)
        self.assertEqual(ctrl_tally[u"前期を消す"].count(("UNPROVABLE", "prior_sibling:0")), 13)
        # H-19: 前期を増やす(値 +1 の複製)は PP-2 の後も 13/13 が UNPROVABLE(値が違うので 2 本のまま)。
        # PP-2(追記 1)により、理由の字は duplicate_values の印が付いた形になる(段 1 に無い印。
        # 「同じ context の重複で値が違う」という PP-2 自身の定義どおりの表示であり、外れではない)。
        self.assertEqual(ctrl_tally[u"前期を増やす"].count(("UNPROVABLE", "prior_sibling:2;duplicate_values")), 13)


class CliTest(unittest.TestCase):
    """F-8: CLI の出力は 2 回走らせて sha256 が同じ。"""

    def test_cli_is_byte_stable(self):
        doc = "S100YXMA"
        inst = I.load_instance(io.open(ED.cache_path(doc), "rb").read())
        f = [x for x in inst["facts"] if x["unit"] == "JPY" and x["context"] == "CurrentYearDuration"][0]
        claims = {"claims": [
            {"id": "C1", "kind": "single_value", "value": f["value"] / 1e6, "unit": u"百万円",
             "pointers": ["%s@%s" % (f["name"], f["context"])]},
            {"id": "C2", "kind": "single_value", "value": 1.0, "unit": u"百万円",
             "pointers": ["jppfs_cor:Nope@CurrentYearDuration"]},
            {"id": "C3", "kind": "ratio_change", "value": 1.0, "unit": u"％", "pointers": ["a@b"]},
        ]}
        tmp = tempfile.mkdtemp()
        cp = os.path.join(tmp, "claims.json")
        with io.open(cp, "w", encoding="utf-8") as fh:
            json.dump(claims, fh, ensure_ascii=False)
        shas = []
        for i in (1, 2):
            outp = os.path.join(tmp, "out%d.json" % i)
            r = subprocess.run([sys.executable, "-m", "adapters.xbrl.verify_external", "--doc", doc,
                                "--claims", cp, "--out", outp], cwd=_ROOT, capture_output=True, text=True,
                               env=dict(os.environ, PYTHONPATH=os.path.join(_ROOT, "core", "py") + os.pathsep + _ROOT))
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(outp, "rb") as fh:
                shas.append(hashlib.sha256(fh.read()).hexdigest())
        self.assertEqual(shas[0], shas[1])
        out = _load(outp)
        self.assertEqual(out["states"], {"GROUNDED": 1, "POINTER_NOT_FOUND": 1, "UNPROVABLE": 1})
        self.assertEqual([r["id"] for r in out["results"]], ["C1", "C2", "C3"])
        self.assertEqual(out["unchecked"], list(H.UNCHECKED))

    def test_cli_is_byte_stable_with_a_sign_bearing_pp_claim(self):
        """PP(期間の対)。``sign`` を含む claims.json で 2 回走らせ、byte が同じことを見る。"""
        doc = "S100YWGX"
        inst = I.load_instance(io.open(ED.cache_path(doc), "rb").read())
        f = [x for x in inst["facts"] if x["name"] == "jppfs_cor:NetSales"
            and x["context"] == "CurrentYearDuration"][0]
        claims = {"claims": [
            {"id": "P1", "kind": "ratio_change", "value": 9.2, "unit": u"％", "sign": 1,
             "pointers": ["%s@%s" % (f["name"], f["context"])]},
            {"id": "P2", "kind": "ratio_change", "value": 9.2, "unit": u"％",
             "pointers": ["%s@%s" % (f["name"], f["context"])]},
        ]}
        tmp = tempfile.mkdtemp()
        cp = os.path.join(tmp, "claims.json")
        with io.open(cp, "w", encoding="utf-8") as fh:
            json.dump(claims, fh, ensure_ascii=False)
        shas = []
        for i in (1, 2):
            outp = os.path.join(tmp, "out%d.json" % i)
            r = subprocess.run([sys.executable, "-m", "adapters.xbrl.verify_external", "--doc", doc,
                                "--claims", cp, "--out", outp], cwd=_ROOT, capture_output=True, text=True,
                               env=dict(os.environ, PYTHONPATH=os.path.join(_ROOT, "core", "py") + os.pathsep + _ROOT))
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(outp, "rb") as fh:
                shas.append(hashlib.sha256(fh.read()).hexdigest())
        self.assertEqual(shas[0], shas[1])
        out = _load(outp)
        self.assertEqual([row["id"] for row in out["results"]], ["P1", "P2"])
        p1, p2 = out["results"]
        self.assertEqual(p1["direction_checked"], True)
        self.assertEqual(p1["derived_pointers"], ["jppfs_cor:NetSales@Prior1YearDuration"])
        self.assertEqual(p1["unchecked"], list(H.UNCHECKED))
        self.assertEqual(p2["direction_checked"], False)
        self.assertEqual(p2["unchecked"], list(H.UNCHECKED) + [u"方向"])
        self.assertEqual(p1["state"], p2["state"])


if __name__ == "__main__":
    unittest.main()
