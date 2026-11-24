# -*- coding: utf-8 -*-
u"""便 UM4 の結果の門(最小)。

結果の文書 docs/UNIVERSAL_FILL_VERIFY_RESULT_2026-11-24.md の §1 の表(予測の判定と数)と §2 の表(記録の鍵と数)が、
記録 fixtures/universal/um4/record.json と字で同じかだけを見る。頭の散文と §3 は縛らない(文書に【門なし】と書いた)。
通信しない・鍵を使わない・席の folder・素材・正解を読まない。
"""
import io
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = os.path.join(ROOT, "docs", "UNIVERSAL_FILL_VERIFY_RESULT_2026-11-24.md")
RECORD = os.path.join(ROOT, "fixtures", "universal", "um4", "record.json")
VERDICT = {True: u"当たり", False: u"外れ", None: u"判定しない"}


def section(text, head):
    m = re.search(r"^## " + re.escape(head) + r".*?$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else u""


def table_rows(block):
    rows = []
    for line in block.splitlines():
        if not line.startswith(u"| ") or line.startswith(u"| ---"):
            continue
        cells = [c.strip() for c in line.strip().strip(u"|").split(u"|")]
        rows.append(cells)
    return rows[1:]  # 頭の行を除く


def load():
    with io.open(DOC, encoding="utf-8") as fh:
        doc = fh.read()
    with io.open(RECORD, encoding="utf-8") as fh:
        rec = json.load(fh)
    return doc, rec


class ResultGate(unittest.TestCase):
    def test_1_predictions_match_record(self):
        doc, rec = load()
        rows = table_rows(section(doc, u"§1"))
        pred = rec[u"予測"]
        self.assertEqual([r[0] for r in rows], list(pred.keys()))
        for name, verdict, nums in rows:
            p = pred[name]
            self.assertEqual(verdict, VERDICT[p[u"当たり"]], name)
            want = u" / ".join(u"%s %s" % (k, v) for k, v in p.items() if k != u"当たり")
            self.assertEqual(nums, want, name)

    def test_2_numbers_match_record(self):
        doc, rec = load()
        rows = table_rows(section(doc, u"§2"))
        self.assertGreaterEqual(len(rows), 50)
        nums = rec[u"数"]
        for key, val in rows:
            if key in (u"会社の数", u"外した社の数"):
                got = rec[key]
            else:
                self.assertIn(key, nums)
                got = nums[key]
            self.assertEqual(val, str(got), key)

    def test_3_verdict_tally_in_head(self):
        doc, rec = load()
        vs = [p[u"当たり"] for p in rec[u"予測"].values()]
        line = u"当たり %d・外れ %d・判定しない %d" % (vs.count(True), vs.count(False), vs.count(None))
        self.assertIn(line, doc.split(u"## §1")[0])


if __name__ == "__main__":
    unittest.main()
