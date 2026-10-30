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
MEETING = "meeting_122105261X01220260330.json"    # 1 回目(衆議院 予算委員会 第12号)
MEETING2 = "meeting_122115261X00820260330.json"   # 2 回目(参議院 予算委員会 第8号)

# 1 回目の engine の記録(2026-10-14、単位の語彙を広げる前)。再実行の比較には使わない。
ROUND1_RECORD = {
    "out_seat_2026-10-14.json": {"GROUNDED": 34, "VALUE_MISMATCH": 5},
    "out_injected_2026-10-14.json": {"GROUNDED": 17, "VALUE_MISMATCH": 22},
}
# 2 回目の engine(U1・U2)の出力。再実行はこれと比べる。
CASES = (
    (MEETING, "summary_122105261X01220260330_seat.json", "out_seat_round1material_engine2_2026-10-14.json"),
    (MEETING, "summary_122105261X01220260330_injected.json", "out_injected_round1material_engine2_2026-10-14.json"),
    (MEETING2, "summary_122115261X00820260330_seat.json", "out_seat_round2_2026-10-14.json"),
    (MEETING2, "summary_122115261X00820260330_injected.json", "out_injected_round2_2026-10-14.json"),
)
EXPECTED_STATES = {
    "out_seat_round1material_engine2_2026-10-14.json": {"GROUNDED": 39},
    "out_injected_round1material_engine2_2026-10-14.json": {"GROUNDED": 19, "VALUE_MISMATCH": 20},
    "out_seat_round2_2026-10-14.json": {"GROUNDED": 40},
    "out_injected_round2_2026-10-14.json": {"GROUNDED": 20, "VALUE_MISMATCH": 20},
}


def _load(name):
    with io.open(os.path.join(_FIX, name), encoding="utf-8") as fh:
        return json.load(fh)


class EntryFixtureTest(unittest.TestCase):
    def test_rerun_matches_recorded_output_except_engine_fingerprint(self):
        meetings = {}
        for mt, summ, rec in CASES:
            meeting = meetings.setdefault(mt, _load(mt))
            out = VM.verify_meeting(meeting, _load(summ))
            recorded = _load(rec)
            for key in ("tool", "input", "document", "claims", "checks"):
                self.assertEqual(json.loads(json.dumps(out[key])), recorded[key], "%s/%s" % (rec, key))

    def test_recorded_state_counts_are_pinned(self):
        for _mt, _summ, rec in CASES:
            self.assertEqual(_load(rec)["document"]["states"], EXPECTED_STATES[rec], rec)
        for rec, states in ROUND1_RECORD.items():
            self.assertEqual(_load(rec)["document"]["states"], states, rec)


def _injection_checks(test, record, base_name, injected_name, pre_stopped_expected):
    rows = _load(record)["rows"]
    base = {c["id"]: c["state"] for c in _load(base_name)["claims"]}
    inj = {c["id"]: c["state"] for c in _load(injected_name)["claims"]}
    test.assertEqual(len(rows), 20)
    test.assertEqual([r["id"] for r in rows if inj[r["id"]] == "GROUNDED"], [])
    test.assertEqual(sorted(r["id"] for r in rows if base[r["id"]] != "GROUNDED"), pre_stopped_expected)
    touched = {r["id"] for r in rows}
    test.assertEqual({k for k in base if k not in touched and base[k] != inj[k]}, set())


class InjectionTest(unittest.TestCase):
    def test_round1_material_on_engine2(self):
        _injection_checks(self, "inject_record_2026-10-14.json",
                          "out_seat_round1material_engine2_2026-10-14.json",
                          "out_injected_round1material_engine2_2026-10-14.json", [])

    def test_round1_record_had_three_pre_stopped(self):
        rows = _load("inject_record_2026-10-14.json")["rows"]
        base = {c["id"]: c["state"] for c in _load("out_seat_2026-10-14.json")["claims"]}
        self.assertEqual(sorted(r["id"] for r in rows if base[r["id"]] != "GROUNDED"), ["K-024", "K-027", "K-028"])

    def test_round2(self):
        _injection_checks(self, "inject_record_round2_2026-10-14.json",
                          "out_seat_round2_2026-10-14.json", "out_injected_round2_2026-10-14.json", [])
