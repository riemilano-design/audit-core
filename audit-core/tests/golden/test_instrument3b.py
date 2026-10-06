# -*- coding: utf-8 -*-
"""C-1g §8 ("計器 3b"): P6 x S100Z4Q1 against core_expectation_1B_v2.json
(v1 + the 5 sealed IDs, built by fixtures/xbrl/make_expectation_1B_v2.py from
the commander's first run c1g_first_run_1B_P6.json) on the same five columns
as instrument 3: state, pointers, recomputed, reason, normalization.

P5F x S100Z4B6 stays on v1 (the P6 run changed 0 of its 133 rows), so the
P6 gate for the second document is ``P6 x 5F == v1`` -- also checked here.
The third document has no expectation yet (the sealed rule stopped: the
predicted and measured ID sets differed, see CORE_CONNECTION_C1G_RESULT §3.3).
"""

import unittest

from tests.adapters.xbrl import _material as M
from tests.golden import _instrument as INS
from adapters.xbrl import vocabulary as V


def _mismatches(tag, results_by_id, rows):
    out = []
    checked_normalization = 0
    for row in rows:
        rid = row["id"]
        result = results_by_id.get(rid)
        if result is None:
            out.append("%s %s: MISSING" % (tag, rid))
            continue
        if result.state.value != row["result"]["state"]:
            out.append("%s %s state: expected=%r actual=%r" % (tag, rid, row["result"]["state"], result.state.value))
        if result.pointers != tuple(row["evidence"]["pointers"]):
            out.append("%s %s pointers: expected=%r actual=%r" % (tag, rid, row["evidence"]["pointers"], result.pointers))
        if result.recomputed != row["result"]["recomputed"]:
            out.append("%s %s recomputed: expected=%r actual=%r" % (tag, rid, row["result"]["recomputed"], result.recomputed))
        exp_reason = INS.expected_reason(row["result"]["script_reason"])
        if result.reason != exp_reason:
            out.append("%s %s reason: expected=%r actual=%r" % (tag, rid, exp_reason, result.reason))
        exp_norm = row["modifiers"]["normalization"]
        if exp_norm:
            checked_normalization += 1
            actual_norm = (result.provenance.get("comparison") or {}).get("normalization")
            if actual_norm != exp_norm:
                out.append("%s %s normalization: expected=%r actual=%r" % (tag, rid, exp_norm, actual_norm))
    return out, checked_normalization


class Instrument3bTest(unittest.TestCase):
    def test_p6_against_1B_v2(self):
        recipe_list, results_by_id, _ = INS.run_verification(
            M.DOC_1, V.P6, lambda: M.load_zip_bytes(M.DOC_1["docID"], M.DOC_1["sha256"])
        )
        expectation = INS.load_expectation("core_expectation_1B_v2.json")
        rows = expectation["claims"]
        self.assertEqual(expectation["profile"], "P6")
        self.assertEqual(len(rows), 91)
        self.assertEqual(len(recipe_list), 91)
        mismatches, checked = _mismatches("1B/P6", results_by_id, rows)
        self.assertEqual(mismatches, [], "\n".join(mismatches))
        # v2 has 3 fewer abs+ labels than v1 (N030/N048/N050) but the same number of normalized rows.
        self.assertEqual(checked, 44)

    def test_v2_differs_from_v1_only_in_the_5_sealed_ids(self):
        v1 = {r["id"]: r for r in INS.load_expectation("core_expectation_1B.json")["claims"]}
        v2 = {r["id"]: r for r in INS.load_expectation("core_expectation_1B_v2.json")["claims"]}
        self.assertEqual(sorted(v1), sorted(v2))
        changed = sorted(i for i in v1 if v1[i] != v2[i])
        self.assertEqual(changed, ["N030", "N048", "N050", "T026", "T028"])
        for i in ("N030", "N048", "N050"):
            self.assertEqual(v1[i]["modifiers"]["normalization"].replace("abs+", ""), v2[i]["modifiers"]["normalization"])
        for i in ("T026", "T028"):
            self.assertEqual(v2[i]["evidence"]["pointers"][-1], "builtin:flow_sign(cur)==direction")
            self.assertEqual(len(v2[i]["evidence"]["pointers"]), 2)
        self.assertEqual(v2["T026"]["result"]["state"], "GROUNDED")
        self.assertEqual(v2["T028"]["result"]["state"], "GROUNDED")

    def test_p6_against_5F_v1_unchanged(self):
        recipe_list, results_by_id, _ = INS.run_verification(
            M.DOC_5, V.P6, lambda: M.load_zip_bytes(M.DOC_5["docID"], M.DOC_5["sha256"])
        )
        rows = INS.load_expectation("core_expectation_5F.json")["claims"]
        self.assertEqual(len(recipe_list), 133)
        mismatches, _ = _mismatches("5F/P6", results_by_id, rows)
        self.assertEqual(mismatches, [], "\n".join(mismatches))


if __name__ == "__main__":
    unittest.main()
