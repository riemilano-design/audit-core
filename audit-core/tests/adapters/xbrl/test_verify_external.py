# -*- coding: utf-8 -*-
"""外部主張の入口(``adapters/xbrl/verify_external.py``)。実材料での再現と対照。

封 `docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md` の F-3〜F-6・F-8。
**材料の ZIP(``~/.cache/audit-core/edinet/``)と ``fixtures/xbrl/cd8`` の記録を読む。無ければ落ちる(skip にしない)。**
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
_DIAG = os.path.join(_CD8, "dim_diag_2026-10-17.json")
_DRAW = os.path.join(_CD8, "draw_2026-10-17.json")


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
                out = VE.verify_external(spec, facts, contexts, registry)
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
                                                fs, contexts, registry)
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


if __name__ == "__main__":
    unittest.main()
