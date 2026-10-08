# -*- coding: utf-8 -*-
"""C-1c §4 前段照合: P1 x S100Z4Q1 の Recipe 列を core_expectation_1B.json と、
P5F x S100Z4B6 の Recipe 列を core_expectation_5F.json と、7 欄
(id・form・subject・value・unit・modifiers・evidence.pointers)で比べる。
224/224 が C-1d へ進む門。期待値は 1 byte も変えない(sha256 で確認)。
"""

import hashlib
import json
import os
import unittest

from . import _material as M
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

_HERE = os.path.dirname(os.path.abspath(__file__))
_FIXTURES_XBRL = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "fixtures", "xbrl"))

_EXPECTATION_SHA256 = {
    "core_expectation_1B.json": "31818f183290febe4caaad50eca503bd9379122cb261afa8cacaf1ecf0ae1325",
    "core_expectation_5F.json": "13e7dac1ddb8c935305767e7202b90eb6c677fab98e187267d90b7da91c3a752",
}

_COMPARED_FIELDS = ("id", "form", "subject", "value", "unit", "population", "time_range", "normalization", "pointers")


def _load_expectation(name):
    path = os.path.join(_FIXTURES_XBRL, name)
    with open(path, "rb") as handle:
        data = handle.read()
    actual_sha = hashlib.sha256(data).hexdigest()
    expected_sha = _EXPECTATION_SHA256[name]
    if actual_sha != expected_sha:
        raise AssertionError(
            "expectation file %s changed (sha256 expected %s, got %s); "
            "the expectation must not be edited" % (name, expected_sha, actual_sha)
        )
    return json.loads(data.decode("utf-8"))


def _norm_time_range(tr):
    if not tr:
        return ()
    return tuple("/".join(pair) for pair in tr)


def _expected_fields(row):
    return {
        "id": row["id"],
        "form": row["form"],
        "subject": row["subject"],
        "value": row["value"],
        "unit": row["unit"],
        "population": row["modifiers"]["population"],
        "time_range": _norm_time_range(row["modifiers"]["time_range"]),
        "normalization": row["modifiers"]["normalization"],
        "pointers": tuple(row["evidence"]["pointers"]),
    }


def _actual_fields(recipe):
    claim = recipe.claim
    return {
        "id": claim.id,
        "form": claim.form.value,
        "subject": claim.subject,
        "value": claim.value,
        "unit": claim.unit,
        "population": claim.modifiers.population,
        "time_range": tuple(claim.modifiers.time_range),
        "normalization": claim.modifiers.normalization,
        "pointers": tuple(str(p) for p in recipe.pointers),
    }


class ClaimLayerGateTest(unittest.TestCase):
    """224/224 の門。差があれば Claim ごと・欄ごとにメッセージへ全部出す。"""

    def _run_one(self, tag, doc, profile, expectation_name):
        zb = M.load_zip_bytes(doc["docID"], doc["sha256"])
        recipe_list = R.build_recipes(zb, profile)
        actual_by_id = {r.claim.id: r for r in recipe_list}
        expectation = _load_expectation(expectation_name)
        rows = expectation["claims"]

        self.assertEqual(expectation["document"], doc["docID"])
        self.assertEqual(len(recipe_list), len(rows), "%s: claim count differs" % (tag,))

        mismatches = []
        for row in rows:
            rid = row["id"]
            if rid not in actual_by_id:
                mismatches.append("%s %s: MISSING from Adapter output" % (tag, rid))
                continue
            expected = _expected_fields(row)
            actual = _actual_fields(actual_by_id[rid])
            for field in _COMPARED_FIELDS:
                if expected[field] != actual[field]:
                    mismatches.append(
                        "%s %s.%s: expected=%r actual=%r" % (tag, rid, field, expected[field], actual[field])
                    )
        extra_ids = sorted(set(actual_by_id) - {row["id"] for row in rows})
        for rid in extra_ids:
            mismatches.append("%s %s: EXTRA in Adapter output (not in expectation)" % (tag, rid))

        self.assertEqual(mismatches, [], "\n".join(mismatches))
        return len(rows)

    def test_p1_against_1B(self):
        n = self._run_one("1B", M.DOC_1, V.P1, "core_expectation_1B.json")
        self.assertEqual(n, 91)

    def test_p5f_against_5F(self):
        n = self._run_one("5F", M.DOC_5, V.P5F, "core_expectation_5F.json")
        self.assertEqual(n, 133)

    def test_total_224(self):
        count_1b = len(_load_expectation("core_expectation_1B.json")["claims"])
        count_5f = len(_load_expectation("core_expectation_5F.json")["claims"])
        self.assertEqual(count_1b + count_5f, 224)


if __name__ == "__main__":
    unittest.main()
