"""欠陥 A の共通構造と例外(measure/defect_a_structure_2026-10-14.py)を固定する。

docs/DEFECT_A_FIX_DESIGN_2026-10-14.md の数が commit された code から再現できることを門にする。
``classify`` 段は commit 済みの fixture だけで回る(ZIP は要らない)。
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
import sys
sys.path.insert(0, ROOT)
from adapters.xbrl import vocabulary as V  # noqa: E402


def _load(name):
    p = os.path.join(ROOT, "measure", name)
    spec = importlib.util.spec_from_file_location(name.replace("-", "_")[:-3], p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


T = _load("defect_a_structure_2026-10-14.py")
BASE = os.path.join(ROOT, "fixtures", "xbrl", "final8")
RAW = os.path.join(BASE, "defect_a_rows_2026-10-14.json")
OUT = os.path.join(BASE, "defect_a_structure_2026-10-14.json")
DOC = os.path.join(ROOT, "docs", "DEFECT_A_FIX_DESIGN_2026-10-14.md")


class WrittenAmountTest(unittest.TestCase):
    """書かれた金額の表記から「最小の書かれた桁」を取る。"""

    def test_thousand_yen_notation(self):
        self.assertEqual(T.written_precision("資産合計は1,810,699千円となり", 1810699000.0), 10 ** 3)

    def test_oku_and_million_compound(self):
        """「2億59百万円」は単位が円でも百万円の桁で書かれている。"""
        self.assertEqual(T.written_precision("前期末に比べ2億59百万円増加し", 259000000.0), 10 ** 6)

    def test_million_yen_notation(self):
        self.assertEqual(T.written_precision("売掛金27百万円増加", 27000000.0), 10 ** 6)

    def test_trailing_zeros_do_not_widen_the_place(self):
        """「100百万円」の桁は百万円。末尾の 0 から作ると 1 億になってしまう。"""
        self.assertEqual(T.written_precision("純減額100百万円", 100000000.0), 10 ** 6)
        self.assertEqual(T.diagnostic_precision(100000000.0), 10 ** 8)

    def test_plain_yen(self):
        self.assertEqual(T.written_precision("135,504円の減少", 135504.0), 1)

    def test_an_amount_that_is_not_in_the_text(self):
        self.assertIsNone(T.written_precision("売上高9,648百万円", 777000000.0))


class ChangeCueTest(unittest.TestCase):
    def test_compare_phrase_before_and_direction_after(self):
        self.assertEqual(T.change_cue("前連結会計年度に比べ14,816千円の増加となりました", 14816000.0), "compare")

    def test_direction_right_after_the_number(self):
        self.assertEqual(T.change_cue("売掛金27百万円増加、のれん18百万円", 27000000.0), "after")

    def test_change_noun_before_the_number(self):
        self.assertEqual(T.change_cue("短期借入金の純減額100百万円、長期借入金の", 100000000.0), "noun")

    def test_a_bare_level_has_no_cue(self):
        self.assertEqual(T.change_cue("主な内訳は支払利息13,043千円、震災復興支援金6,000千円です。", 6000000.0), "none")

    def test_a_number_not_in_the_text_has_no_cue(self):
        self.assertEqual(T.change_cue("売上高9,648百万円", 1.0), "none")


class BandTest(unittest.TestCase):
    """``band_match`` は k=1 で ``V.match_value`` の写しでなければならない。"""

    CASES = ((14817000.0, 14816000.0, 1000.0), (14816000.0, 14816000.0, 1000.0),
             (15988000.0, 14816000.0, 1000.0), (-682020000.0, 682019000.0, 1000.0),
             (260000000.0, 259000000.0, 1000000.0), (110000000.0, 100000000.0, 1000000.0),
             (7010000.0, 6000000.0, 1000.0))

    def test_k_one_agrees_with_the_real_match_value(self):
        for diff, target, unit in self.CASES:
            mine = T.band_match(diff, target, unit, 1)
            theirs = V.match_value(diff, target, unit, None, True)
            self.assertEqual(bool(mine), bool(theirs), "%r vs %r for %s" % (mine, theirs, (diff, target, unit)))

    def test_the_off_by_one_unit_case_is_the_boundary(self):
        """差が 1 単位ちょうど大きいとき、今の帯は当たらず 2 倍なら当たる。"""
        self.assertIsNone(T.band_match(14817000.0, 14816000.0, 1000.0, 1))
        self.assertIsNotNone(T.band_match(14817000.0, 14816000.0, 1000.0, 2, truncate_only=True))

    def test_the_spec_band_does_not_widen_the_round_side(self):
        """ずれが負(engine の差が小さい)の行は、仕様の帯では当たらない。"""
        diff, target, unit = 107000.0, 1000000.0, 1000000.0   # ずれ -0.893 単位の形
        self.assertIsNotNone(T.band_match(diff, target, unit, 2))
        self.assertIsNone(T.band_match(diff, target, unit, 2, truncate_only=True))

    def test_a_ten_unit_gap_is_not_matched_even_at_twice(self):
        self.assertIsNone(T.band_match(110000000.0, 100000000.0, 1000000.0, 2, truncate_only=True))

    def test_a_thousand_unit_gap_is_not_matched_even_at_twice(self):
        self.assertIsNone(T.band_match(7010000.0, 6000000.0, 1000.0, 2, truncate_only=True))


class RecordedCountsTest(unittest.TestCase):
    def setUp(self):
        self.rec = json.load(io.open(OUT, encoding="utf-8"))
        self.raw = json.load(io.open(RAW, encoding="utf-8"))

    def test_the_universe(self):
        self.assertEqual(self.rec["money_mismatch_rows"], 110)
        self.assertEqual(len(self.raw["rows"]), 110)
        self.assertEqual(len(self.raw["money"]), 464)

    def test_diagnostic_and_spec_counts(self):
        self.assertEqual(self.rec["diagnostic_count"], 30)
        self.assertEqual(self.rec["spec_count"], 26)
        self.assertEqual(self.rec["spec_only"], [])

    def test_the_four_exceptions_and_why(self):
        self.assertEqual(self.rec["dropped_reasons"],
                         {"S5 書かれた桁で差に一致しない": 2, "S6 文が変化として述べていない": 2})

    def test_every_spec_row_is_exactly_one_written_unit_off(self):
        """これが崩れたら「切り捨てが 2 回積む」という説明が崩れる。"""
        self.assertEqual(self.rec["offset_units"], {"+1.000": 26})

    def test_the_cue_forms(self):
        self.assertEqual(self.rec["cue_counts"], {"compare": 14, "after": 12})

    def test_the_noun_cue_is_never_used_in_this_sample(self):
        """未検証の枝であることを留める(0 件を根拠にしないため)。"""
        self.assertNotIn("noun", self.rec["cue_counts"])

    def test_the_spec_band_moves_28_and_steals_none(self):
        b = self.rec["band_counts"]
        self.assertEqual(b["VALUE_MISMATCH | 仕様(切り捨てだけ 2 倍)で当たる"], 28)
        self.assertEqual(b["VALUE_MISMATCH | 両側 2 倍でだけ当たる"], 1)
        self.assertNotIn("GROUNDED | 仕様(切り捨てだけ 2 倍)で当たる", b)
        self.assertNotIn("GROUNDED | 両側 2 倍でだけ当たる", b)
        self.assertEqual(sum(b.values()), 464)

    def test_the_claim_scale_already_equals_the_written_place(self):
        self.assertEqual(self.rec["scale_agreement"], {"claim_scale == 書かれた桁": 459})

    def test_the_fixture_is_what_the_script_builds_now(self):
        import contextlib
        import tempfile
        keep = T.OUT
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
            tmp = fh.name
        try:
            T.OUT = tmp
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                out = T.stage_classify()
        finally:
            T.OUT = keep
            os.unlink(tmp)
        self.assertEqual(json.loads(json.dumps(out, ensure_ascii=False)), self.rec)

    def test_the_document_states_the_numbers(self):
        with io.open(DOC, encoding="utf-8") as fh:
            doc = fh.read()
        rows = [[c.strip().replace("*", "") for c in l.strip().strip("|").split("|")]
                for l in doc.splitlines() if l.strip().startswith("|")]
        cells = {c for r in rows for c in r}
        for n in ("110", "30", "26", "28", "0", "459"):
            self.assertIn(n, cells, "%s が表の欄に無い" % n)
        # ずれの分布は**表の行として**留める(説明文に同じ字が在るので doc 全体では測れない)
        for key, n in self.rec["offset_units"].items():
            hit = [r for r in rows if r and r[0] == "%s 単位" % key]
            self.assertEqual(len(hit), 1, "「%s 単位」の行が %d 本" % (key, len(hit)))
            self.assertEqual(hit[0][1], str(n), "%s: %s" % (key, hit[0]))


if __name__ == "__main__":
    unittest.main()
