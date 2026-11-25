# -*- coding: utf-8 -*-
"""便 TR10 の単体試験(封の前提)。値は全部作り物。走らせ方: python3 -I test_tr10.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_tr10 as K  # noqa: E402

LEDGER = {"売上高@当期": 4629400000, "売上高@前期": 4000100000, "純資産合計@当期末": 4370000000, "純資産合計@前期末": 4100000000,
          "短期借入金@当期末": 120000000}
SRCS = {k: [{"シート": "BS", "行": k.split("@")[0], "何番目": 1, "列": "当期末", "升の値": v, "符号": 1}] for k, v in LEDGER.items()}
DOC = """# 業績(第 51 社)

当期の売上高は 4,629 百万円となり、前期の 4,000 百万円から 629 百万円(15.7%)増えました。
当期末の純資産合計は 4,370 百万円でした。
当期末の長期借入金は 300 百万円でした。
"""


def tag(line, text, item, per, kind="金額", unit="百万円", sign="+"):
    return {"行": line, "字": text, "何番目": 1, "項目": item, "期": per, "種類": kind, "向き": sign, "単位": unit}


TAGS = [tag(3, "4,629", "売上高", "当期"), tag(3, "4,000", "売上高", "前期"), tag(3, "629", "売上高", "当期", "増減額"),
        tag(3, "15.7", "売上高", "当期", "増減率", "%"), tag(4, "4,370", "純資産合計", "当期末"), tag(5, "300", "長期借入金", "当期末")]


def rows(md=DOC, tags=TAGS):
    return {r["札の番号"]: r for r in K.check_doc(md, tags, LEDGER, SRCS) if r["札の番号"] is not None}


class T(unittest.TestCase):
    def test_amounts_diff_rate_confirmed_with_source(self):
        r = rows()
        for i in range(5):
            self.assertEqual(r[i]["区分"], "確認済み", r[i]["訳"])
        self.assertEqual(r[0]["出どころ"][0]["シート"], "BS")
        self.assertEqual(len(r[2]["出どころ"]), 2)  # 増減額は当期と前期の升

    def test_missing_ledger_item_not_checked(self):
        self.assertEqual(rows()[5]["区分"], "点検していない")

    def test_wrong_value_stopped(self):
        md = DOC.replace("4,370", "4,372")
        t = [dict(x) for x in TAGS]
        t[4]["字"] = "4,372"
        self.assertEqual(rows(md, t)[4]["区分"], "要修正・精査")

    def test_untagged_number_listed(self):
        out = K.check_doc(DOC, TAGS[:4], LEDGER, SRCS)
        self.assertTrue(any(r["札"] is None and r["字"] == "4,370" and r["区分"] == "点検していない" for r in out))

    def test_period_hide_stopped(self):
        md = DOC.replace("当期の売上高は 4,629", "当期の売上高は 4,000")
        t = [dict(x) for x in TAGS]
        t[0].update({"字": "4,000", "期": "前期", "何番目": K.nth_at(md, 2, md.split("\n")[2].index("4,000"), "4,000")})
        self.assertEqual(t[0]["何番目"], 1)
        self.assertNotEqual(rows(md, t)[0]["区分"], "確認済み")

    def test_nth_at_second(self):
        md = DOC.replace("前期の 4,000", "前期の 4,629")
        line = md.split("\n")[2]
        self.assertEqual(K.nth_at(md, 2, line.rindex("4,629"), "4,629"), 2)

    def test_sign_mismatch_stopped(self):
        t = [dict(x) for x in TAGS]
        t[2]["向き"] = "−"
        self.assertEqual(rows(DOC, t)[2]["区分"], "要修正・精査")

    def test_r1_reason_has_no_code(self):
        md = DOC.replace("前期の 4,000", "前期の 4,629")
        t = [dict(x) for x in TAGS]
        t[1].update({"字": "4,629", "何番目": 2, "期": "当期"})
        r = rows(md, t)
        self.assertEqual(r[0]["規則"], "R1")
        self.assertNotIn("R1", K.report(51, K.check_doc(md, t, LEDGER, SRCS), "x"))

    def test_report_has_no_internal_codes(self):
        h = K.report(51, K.check_doc(DOC, TAGS, LEDGER, SRCS), "x")
        for w in ("S1", "S6", "GROUNDED", "UNPROVABLE", "R1"):
            self.assertNotIn(w, h)
        self.assertIn("升の値", h)


if __name__ == "__main__":
    unittest.main()
