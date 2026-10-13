# -*- coding: utf-8 -*-
"""報告の装置: golden(byte 一致 + sha256 を字で固定)・判定を足さない・決定的。"""

import hashlib
import io
import json
import os
import re
import unittest

from adapters.kokkai import report_meeting as RM

_HERE = os.path.dirname(os.path.abspath(__file__))
_FIX = os.path.join(_HERE, "..", "..", "..", "fixtures", "kokkai")

CASES = (
    ("out_seat_2026-10-14.json", "report_seat_2026-10-14.md"),
    ("out_injected_2026-10-14.json", "report_injected_2026-10-14.md"),
    # 2 回目(参議院 予算委員会 第8号)
    ("out_seat_round2_2026-10-14.json", "report_seat_round2_2026-10-14.md"),
    ("out_injected_round2_2026-10-14.json", "report_injected_round2_2026-10-14.md"),
)
# **字で固定。** 報告の byte を変える変更はここも変える(= 人が見る)。
GOLDEN_SHA256 = {
    "report_seat_2026-10-14.md": "12a9897da08fb73c1be9f161739f62090d9ed1cecdcc29f8d3fbfc0c8c03100d",
    "report_injected_2026-10-14.md": "f3a61ce9adfd2ff7fb0e428f0108a9278870c42f3f82c6785faa9b9353845352",
    "report_seat_round2_2026-10-14.md": "81cc218df4a935a2b0470610eda3539d89501965d91d9f72f104ae3133692e68",
    "report_injected_round2_2026-10-14.md": "d8d28d11d3cd109b29b5c064164b884c63792ac91bf2960ec7c74c05ef9607df",
}


def _load(name):
    with io.open(os.path.join(_FIX, name), encoding="utf-8") as fh:
        return json.load(fh)


def _read_bytes(name):
    with open(os.path.join(_FIX, name), "rb") as fh:
        return fh.read()


class GoldenTest(unittest.TestCase):
    def test_render_equals_golden_bytes(self):
        for inp, gold in CASES:
            self.assertEqual(RM.render_markdown(_load(inp)).encode("utf-8"), _read_bytes(gold), gold)

    def test_golden_sha256_is_pinned(self):
        for _, gold in CASES:
            self.assertEqual(hashlib.sha256(_read_bytes(gold)).hexdigest(), GOLDEN_SHA256[gold], gold)

    def test_render_is_deterministic(self):
        out = _load(CASES[0][0])
        self.assertEqual(RM.render_markdown(out), RM.render_markdown(json.loads(json.dumps(out))))


class NoReclassificationTest(unittest.TestCase):
    def test_every_claim_appears_once_in_its_own_state_section(self):
        for inp, _ in CASES:
            out = _load(inp)
            md = RM.render_markdown(out)
            sections = re.split(r"^## ", md, flags=re.M)
            for c in out["claims"]:
                hits = [s for s in sections if re.search(r"^\| %s \| " % re.escape(c["id"]), s, flags=re.M)]
                self.assertEqual(len(hits), 1, c["id"])
                self.assertTrue(hits[0].startswith(RM.STATE_LABEL[c["state"]]), c["id"])

    def test_counts_in_table_equal_json(self):
        for inp, _ in CASES:
            out = _load(inp)
            md = RM.render_markdown(out)
            for st, n in out["document"]["states"].items():
                self.assertIn("| %s | %s |" % (RM.STATE_LABEL[st], n), md)

    def test_rule_is_verbatim(self):
        out = _load(CASES[0][0])
        self.assertIn("規則(字のまま): " + out["document"]["rule"], RM.render_markdown(out))

    def test_unknown_state_goes_to_other_section(self):
        out = _load(CASES[0][0])
        out = json.loads(json.dumps(out))
        out["claims"][0]["state"] = "SOMETHING_ELSE"
        md = RM.render_markdown(out)
        self.assertIn("## その他の状態 ― 1 件", md)
        self.assertIn("| K-001 | SOMETHING_ELSE |", md)

    def test_stopped_checks_are_all_listed(self):
        out = _load(CASES[1][0])
        md = RM.render_markdown(out)
        stopped = [r for r in out["checks"] if r["state"] != "GROUNDED"]
        self.assertIn("## 一致しなかった検査の中身 ― %d 件" % len(stopped), md)
        for r in stopped:
            self.assertIn("| %s | %s |" % (r["id"], r["state"]), md)


class FormattingTest(unittest.TestCase):
    def test_cell_escapes_pipes_and_newlines(self):
        self.assertEqual(RM.cell("a|b\r\nc"), "a\\|b c")
        self.assertEqual(RM.cell(None), "")

    def test_fmt_num(self):
        self.assertEqual(RM.fmt_num(30000000000.0), "30,000,000,000")
        self.assertEqual(RM.fmt_num(177.7), "177.7")
        self.assertEqual(RM.fmt_num(None), "")
