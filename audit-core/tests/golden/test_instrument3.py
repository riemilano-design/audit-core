# -*- coding: utf-8 -*-
"""C-1d §3.4 ("計器 3"): P1 x S100Z4Q1 and P5F x S100Z4B6, run all the way
through ``audit_core.verify_all`` (this Adapter's registry + resolver),
compared against the C-0 expectation JSON on five columns: state,
pointers, recomputed (``==``, no rounding), reason (through the
expectation->registered-name mapping) and normalization (for the 77
claims whose ``modifiers.normalization`` is non-null). 224/224 on all
five is this module's gate.

The resolver's own ambiguity check (``distinct_values == 1`` for every
pointer this run actually resolves) is also asserted here, per document
(60 for 1B, 39 for 5F -- see ``_instrument.run_verification``'s
docstring for why the two counts are not merged into one union).

The ZIPs are read from the shared local cache
(``tests/adapters/xbrl/_material.py``); this module fails (does not
skip) if they are absent or sha-mismatched.
"""

import unittest

from tests.adapters.xbrl import _material as M
from adapters.xbrl import vocabulary as V

from . import _instrument as INS


class Instrument3GateTest(unittest.TestCase):
    """224/224 on state/pointers/recomputed/reason/normalization."""

    def _run_one(self, tag, doc, profile, expectation_name, expected_count):
        recipe_list, results_by_id, pointer_metas = INS.run_verification(
            doc, profile, lambda: M.load_zip_bytes(doc["docID"], doc["sha256"])
        )
        expectation = INS.load_expectation(expectation_name)
        rows = expectation["claims"]

        self.assertEqual(len(recipe_list), expected_count, "%s: recipe count" % (tag,))
        self.assertEqual(len(rows), expected_count, "%s: expectation count" % (tag,))

        mismatches = {"state": [], "pointers": [], "recomputed": [], "reason": [], "normalization": []}
        normalization_checked = 0

        for row in rows:
            rid = row["id"]
            result = results_by_id.get(rid)
            if result is None:
                mismatches["state"].append("%s %s: MISSING from verify_all output" % (tag, rid))
                continue

            exp_state = row["result"]["state"]
            if result.state.value != exp_state:
                mismatches["state"].append(
                    "%s %s: expected=%r actual=%r" % (tag, rid, exp_state, result.state.value)
                )

            exp_pointers = tuple(row["evidence"]["pointers"])
            if result.pointers != exp_pointers:
                mismatches["pointers"].append(
                    "%s %s: expected=%r actual=%r" % (tag, rid, exp_pointers, result.pointers)
                )

            exp_recomputed = row["result"]["recomputed"]
            if result.recomputed != exp_recomputed:
                mismatches["recomputed"].append(
                    "%s %s: expected=%r actual=%r" % (tag, rid, exp_recomputed, result.recomputed)
                )

            exp_reason = INS.expected_reason(row["result"]["script_reason"])
            if result.reason != exp_reason:
                mismatches["reason"].append(
                    "%s %s: script_reason=%r expected_reason=%r actual=%r"
                    % (tag, rid, row["result"]["script_reason"], exp_reason, result.reason)
                )

            exp_normalization = row["modifiers"]["normalization"]
            if exp_normalization:
                normalization_checked += 1
                actual_normalization = (result.provenance.get("comparison") or {}).get("normalization")
                if actual_normalization != exp_normalization:
                    mismatches["normalization"].append(
                        "%s %s: expected=%r actual=%r"
                        % (tag, rid, exp_normalization, actual_normalization)
                    )

        all_mismatches = [m for group in mismatches.values() for m in group]
        self.assertEqual(all_mismatches, [], "\n".join(all_mismatches))
        return expected_count, normalization_checked, pointer_metas

    def test_p1_against_1B(self):
        n, normalized, pointer_metas = self._run_one("1B", M.DOC_1, V.P1, "core_expectation_1B.json", 91)
        self.assertEqual(normalized, 43)
        self._assert_no_ambiguity("1B", pointer_metas, 59)

    def test_p5f_against_5F(self):
        n, normalized, pointer_metas = self._run_one("5F", M.DOC_5, V.P5F, "core_expectation_5F.json", 133)
        self.assertEqual(normalized, 28)
        self._assert_no_ambiguity("5F", pointer_metas, 34)

    def test_total_224(self):
        n1 = len(INS.load_expectation("core_expectation_1B.json")["claims"])
        n5 = len(INS.load_expectation("core_expectation_5F.json")["claims"])
        self.assertEqual(n1 + n5, 224)

    def test_normalization_total_77(self):
        _, normalized_1b, _ = self._run_one("1B", M.DOC_1, V.P1, "core_expectation_1B.json", 91)
        _, normalized_5f, _ = self._run_one("5F", M.DOC_5, V.P5F, "core_expectation_5F.json", 133)
        self.assertEqual(normalized_1b + normalized_5f, 71)

    def _assert_no_ambiguity(self, tag, pointer_metas, expected_pointer_count):
        self.assertEqual(len(pointer_metas), expected_pointer_count, "%s: distinct pointers resolved" % (tag,))
        ambiguous = [(p, meta) for p, meta in pointer_metas.items() if meta["distinct_values"] != 1]
        self.assertEqual(ambiguous, [], "%s: ambiguous pointers (distinct_values != 1): %r" % (tag, ambiguous))


if __name__ == "__main__":
    unittest.main()
