# -*- coding: utf-8 -*-
"""報告の装置(``adapters/xbrl/report.py``)の試験。

人間の決定(2026-10-13): 報告は入口の JSON を並べ替えるだけで判定を足さない。LLM なし。
留めるもの: (1) 実出力 2 件からの報告が golden とバイト一致、(2) 同じ入力から同じバイト列、
(3) 全 Claim が 1 回ずつ現れ、JSON の state の節にだけ現れる(再分類していない)、
(4) 件数の表が JSON の件数と一致、(5) 規則の字がそのまま載る、(6) 数の書式。
"""

import io
import json
import os
import re
import unittest

from adapters.xbrl import report as RP

_HERE = os.path.dirname(os.path.abspath(__file__))
_FIX = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "fixtures", "xbrl"))

CASES = (
    ("entry_output_S100Z4N9_original_2026-10-13.json", "report_golden_S100Z4N9_original_2026-10-13.md", 186),
    ("entry_output_S100Z4Q1_ai_prose_2026-10-13.json", "report_golden_S100Z4Q1_ai_prose_2026-10-13.md", 412),
)
# golden の sha256 を字で留める(記法を変えたら必ず赤くなる)
GOLDEN_SHA256 = {
    "report_golden_S100Z4N9_original_2026-10-13.md": "dfa347925c84de4be763c43cbd5d54db13a636b52a367fff3ec37bd91ad0c763",
    "report_golden_S100Z4Q1_ai_prose_2026-10-13.md": "ead08b97484551a36ffa53c7a28d51e477c89ce3aa2ef4ed3cf5f22103d2c11e",
}

_ROW = re.compile(r"^\| ([NT]\d{3}) \|", re.M)
_SECTION = re.compile(r"^## (.+?) ― (\d[\d,]*) 件$", re.M)


def _load(name):
    with io.open(os.path.join(_FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _read(name):
    with io.open(os.path.join(_FIX, name), "r", encoding="utf-8", newline="") as f:
        return f.read()


class GoldenTest(unittest.TestCase):
    def test_report_of_each_real_output_matches_golden_bytes(self):
        for js, md, n in CASES:
            out = _load(js)
            self.assertEqual(len(out["claims"]), n)
            self.assertEqual(RP.render_markdown(out), _read(md), md)

    def test_golden_sha256_is_pinned_literally(self):
        import hashlib
        for md, sha in GOLDEN_SHA256.items():
            self.assertEqual(hashlib.sha256(_read(md).encode("utf-8")).hexdigest(), sha, md)

    def test_same_input_twice_gives_same_bytes(self):
        out = _load(CASES[0][0])
        self.assertEqual(RP.render_markdown(out), RP.render_markdown(json.loads(json.dumps(out))))


class NoReclassificationTest(unittest.TestCase):
    def _sections(self, md):
        """節の見出し → その節の行の id の一覧。"""
        parts = re.split(r"^## ", md, flags=re.M)
        found = {}
        for part in parts[1:]:
            head = part.split("\n", 1)[0]
            m = re.match(r"(.+?) ― (\d[\d,]*) 件$", head)
            if not m:
                continue
            found[m.group(1)] = _ROW.findall(part)
        return found

    def test_every_claim_appears_exactly_once_in_its_own_state_section(self):
        for js, md, n in CASES:
            out = _load(js)
            sections = self._sections(RP.render_markdown(out))
            seen = []
            for label, ids in sections.items():
                st = [k for k, v in RP.STATE_LABEL.items() if v == label]
                self.assertEqual(len(st), 1, label)
                for cid in ids:
                    claim = next(c for c in out["claims"] if c["id"] == cid)
                    self.assertEqual(claim["state"], st[0], cid)
                seen.extend(ids)
            self.assertEqual(sorted(seen), sorted(c["id"] for c in out["claims"]))
            self.assertEqual(len(seen), n)

    def test_section_counts_equal_json_counts(self):
        for js, md, n in CASES:
            out = _load(js)
            md_text = RP.render_markdown(out)
            for st, label in RP.STATE_LABEL.items():
                m = re.search(r"^## %s ― (\d[\d,]*) 件$" % re.escape(label), md_text, re.M)
                self.assertIsNotNone(m, label)
                self.assertEqual(int(m.group(1).replace(",", "")), out["document"]["states"].get(st, 0), st)
                # 件数の表の行
                self.assertIn("| %s | %s |" % (label, RP.fmt_num(out["document"]["states"].get(st, 0))), md_text)

    def test_the_legend_explains_window_dash_and_reason(self):
        md = RP.render_markdown(_load(CASES[0][0]))
        self.assertIn("凡例:", md)
        for word in ("抜粋(窓)", "「―」", "理由"):
            self.assertIn(word, md)

    def test_the_rule_text_is_printed_verbatim(self):
        out = _load(CASES[0][0])
        self.assertIn(out["document"]["rule"], RP.render_markdown(out))

    def test_document_flag_is_printed_from_the_json_not_recomputed(self):
        out = _load(CASES[0][0])
        self.assertFalse(out["document"]["unverifiable"])
        self.assertIn("旗なし", RP.render_markdown(out))
        flipped = json.loads(json.dumps(out))
        flipped["document"]["unverifiable"] = True
        flipped["document"]["unverifiable_why"] = "試験"
        md = RP.render_markdown(flipped)
        self.assertIn("UNVERIFIABLE(書類として判定できない)", md)
        self.assertIn("理由: 試験", md)

    def test_unknown_state_goes_to_the_other_section_not_dropped(self):
        out = json.loads(json.dumps(_load(CASES[0][0])))
        out["claims"][0]["state"] = "SOMETHING_NEW"
        md = RP.render_markdown(out)
        self.assertIn("## その他の状態 ― 1 件", md)
        self.assertIn("| %s | SOMETHING_NEW |" % out["claims"][0]["id"], md)


class FormattingTest(unittest.TestCase):
    def test_fmt_num(self):
        self.assertEqual(RP.fmt_num(None), "")
        self.assertEqual(RP.fmt_num(11804911.0), "11,804,911")
        self.assertEqual(RP.fmt_num(-639811000.0), "-639,811,000")
        self.assertEqual(RP.fmt_num(8.4), "8.4")
        self.assertEqual(RP.fmt_num(-198.37), "-198.37")
        self.assertEqual(RP.fmt_num(0.5), "0.5")
        self.assertEqual(RP.fmt_num(1234), "1,234")

    def test_cell_escapes_pipes_and_newlines(self):
        self.assertEqual(RP.cell("a|b\nc"), "a\\|b c")
        self.assertEqual(RP.cell(None), "")

    def test_claim_value_uses_word_for_text_claims(self):
        self.assertEqual(RP.claim_value({"value": None, "unit": None, "word": "増収"}), "増収")
        self.assertEqual(RP.claim_value({"value": 8.4, "unit": "%", "word": None}), "8.4 %")
        self.assertEqual(RP.claim_value({"value": 10.0, "unit": None, "word": None}), "10")


class CliTest(unittest.TestCase):
    def test_cli_writes_the_same_bytes_as_the_golden(self):
        import subprocess, sys, tempfile
        js, md, n = CASES[0]
        with tempfile.TemporaryDirectory() as d:
            outp = os.path.join(d, "r.md")
            r = subprocess.run([sys.executable, "-m", "adapters.xbrl.report", "--in", os.path.join(_FIX, js), "--out", outp],
                               cwd=os.path.join(_FIX, "..", ".."), capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            with io.open(outp, "r", encoding="utf-8", newline="") as f:
                self.assertEqual(f.read(), _read(md))


if __name__ == "__main__":
    unittest.main()
