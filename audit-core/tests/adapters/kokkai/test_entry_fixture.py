# -*- coding: utf-8 -*-
"""入口を実物の材料(fixtures/kokkai)に当てた出力が、記録した出力と同じこと。
engine の指紋(git commit・adapter の .py の束)は commit ごとに変わるので比べない。"""

import io
import json
import os
import unittest

from adapters.kokkai import verify_meeting as VM

_HERE = os.path.dirname(os.path.abspath(__file__))
_FIX = os.path.join(_HERE, "..", "..", "..", "fixtures", "kokkai")
MEETING = "meeting_122105261X01220260330.json"
# 1 回目の engine の記録(2026-10-14、単位の語彙を広げる前)。再実行の比較には使わない。
ROUND1_RECORD = {
    "out_seat_2026-10-14.json": {"GROUNDED": 34, "VALUE_MISMATCH": 5},
    "out_injected_2026-10-14.json": {"GROUNDED": 17, "VALUE_MISMATCH": 22},
}
# 2 回目の engine(U1・U2)で 1 回目の材料を回した出力。再実行はこれと比べる。
CASES = (
    ("summary_122105261X01220260330_seat.json", "out_seat_round1material_engine2_2026-10-14.json"),
    ("summary_122105261X01220260330_injected.json", "out_injected_round1material_engine2_2026-10-14.json"),
)
EXPECTED_STATES = {
    "out_seat_round1material_engine2_2026-10-14.json": {"GROUNDED": 39},
    "out_injected_round1material_engine2_2026-10-14.json": {"GROUNDED": 19, "VALUE_MISMATCH": 20},
}


def _load(name):
    with io.open(os.path.join(_FIX, name), encoding="utf-8") as fh:
        return json.load(fh)


class EntryFixtureTest(unittest.TestCase):
    def test_rerun_matches_recorded_output_except_engine_fingerprint(self):
        meeting = _load(MEETING)
        for summ, rec in CASES:
            out = VM.verify_meeting(meeting, _load(summ))
            recorded = _load(rec)
            for key in ("tool", "input", "document", "claims", "checks"):
                self.assertEqual(json.loads(json.dumps(out[key])), recorded[key], "%s/%s" % (rec, key))

    def test_recorded_state_counts_are_pinned(self):
        for _, rec in CASES:
            self.assertEqual(_load(rec)["document"]["states"], EXPECTED_STATES[rec], rec)
        for rec, states in ROUND1_RECORD.items():
            self.assertEqual(_load(rec)["document"]["states"], states, rec)

    def test_injected_rows_are_all_non_grounded(self):
        rows = _load("inject_record_2026-10-14.json")["rows"]
        out = {c["id"]: c for c in _load("out_injected_round1material_engine2_2026-10-14.json")["claims"]}
        self.assertEqual(len(rows), 20)
        self.assertEqual([r["id"] for r in rows if out[r["id"]]["state"] == "GROUNDED"], [])

    def test_untouched_claims_keep_their_state(self):
        rows = {r["id"] for r in _load("inject_record_2026-10-14.json")["rows"]}
        base = {c["id"]: c["state"] for c in _load("out_seat_round1material_engine2_2026-10-14.json")["claims"]}
        inj = {c["id"]: c["state"] for c in _load("out_injected_round1material_engine2_2026-10-14.json")["claims"]}
        self.assertEqual({k: (base[k], inj[k]) for k in base if k not in rows and base[k] != inj[k]}, {})
