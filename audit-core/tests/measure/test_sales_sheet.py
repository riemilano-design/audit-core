# -*- coding: utf-8 -*-
u"""門: 外向けの 1 枚 docs/SALES_SHEET_2026-11-02.md の数を、台帳 docs/FACTS_FOR_BUYERS_2026-10-20.md の同じ行に縛る。

縛る物:
- 〔台帳 X-nn〕の印が付いた行の数(数・比・割合)は全部、台帳のその行の「数」の欄の字に在る。比(a / b = c%)は字のまま在る。
- 印の無い行に 2 桁以上の数を書かない(【門なし】を付けた行は除く。日付・ID・profile の字は数と見ない)。
- 台帳の禁止語・言い切りの語・docID を書かない。印が指す台帳の行が実在する。
- 変異で赤くなる。
限界(監査 2026-11-02 の指摘): 照合は「印の行の数の欄に在る数の集合」で見るので、同じ行の欄に在る別の数への差し替え
(例: 254 → 255)は通る。比(a / b = c%)は字の全体で見るので、この限界は比に及ばない。
"""
from __future__ import print_function

import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHEET = os.path.join(ROOT, "docs", "SALES_SHEET_2026-11-02.md")
LEDGER = os.path.join(ROOT, "docs", "FACTS_FOR_BUYERS_2026-10-20.md")

TAG_RE = re.compile(u"〔台帳 ([A-Z]+-\\d+)〕")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
NOT_GATED = u"【門なし】"
FORBIDDEN = (u"精度", u"LLM より正確", u"世界で 1 社", u"金額", u"契約", u"税", u"USD",
             u"accurate", u"guarantee", u"正確", u"保証", u"世界初", u"出所として正しい証拠が得られた")
RATIO_RE = re.compile(r"(?<![\d.,])\d[\d,]*(?:\.\d+)? / \d[\d,]*(?:\.\d+)? = \d+(?:\.\d+)?%")
NUM_RE = re.compile(r"(?<![\d.,])\d[\d,]*(?:\.\d+)?%?(?![\d.,]\d)")        # 数の境界つき(前後に数字・小数点・桁区切りが続かない)
KNOWN_TYPES = re.compile(r"\bT[1-8](?:_[A-Z]+)?\b")                        # 台帳に在る型の名(T1〜T8、T8_REL など)だけ数と見ない


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def ledger_rows(ledger):
    u"""台帳の表の行: ID → 数の欄(3 つ目の欄)。"""
    out = {}
    for l in ledger.splitlines():
        m = re.match(r"^\| ([A-Z]+-\d+) \|", l)
        if m:
            cells = [c.strip() for c in l.strip().strip(u"|").split(u"|")]
            if len(cells) >= 3:
                out[m.group(1)] = cells[2]
    return out


def strip_non_numbers(s):
    s = re.sub(r"^#+\s*\d+\.\s", u"# ", s)              # 見出しの番号「## 1. 」だけ落とす(見出しの中の数は見る)
    s = re.sub(r"`[^`]*`", u" ", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
    s = TAG_RE.sub(u" ", s)
    s = re.sub(r"\b[A-Z]+-\d+\b", u" ", s)            # L-01・D-22 などの台帳の ID
    s = re.sub(r"\bP\d+[A-Z]?\b", u" ", s)              # profile の名(P16・P27E)
    s = KNOWN_TYPES.sub(u" ", s)
    return s


def tokens(s):
    u"""字から数と比を、境界つきで抜く(桁区切りは外す)。"""
    nums = set(n.replace(u",", u"") for n in NUM_RE.findall(s))
    ratios = set(r.replace(u",", u"") for r in RATIO_RE.findall(s))
    return nums, ratios


def sheet_problems(sheet, rows):
    p = []
    for ln in sheet.splitlines():
        if not ln.strip():
            continue
        tags = TAG_RE.findall(ln)
        body = strip_non_numbers(ln)
        nums, ratios = tokens(body)
        if not tags:
            for n in sorted(nums):
                if len(re.sub(r"\D", u"", n)) >= 2 and NOT_GATED not in ln:
                    p.append(u"印の無い行に数 %s … %s" % (n, ln[:40]))
            continue
        cell_nums, cell_ratios = set(), set()
        for t in tags:
            if t not in rows:
                p.append(u"台帳に %s が無い" % t)
            else:
                a, b = tokens(strip_non_numbers(rows[t]))      # 台帳の欄も同じ規則で(P22・T8_REL の数字を数と見ない)
                cell_nums |= a
                cell_ratios |= b
        for r in sorted(ratios):
            if r not in cell_ratios:
                p.append(u"比 %s が台帳の行に無い … %s" % (r, ln[:40]))
        for n in sorted(nums):
            if n not in cell_nums:
                p.append(u"数 %s が台帳の行に無い … %s" % (n, ln[:40]))
    for w in FORBIDDEN:
        if w in sheet:
            p.append(u"禁止語 %s" % w)
    if DOCID_RE.search(sheet):
        p.append(u"docID")
    return p


class SheetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheet = text(SHEET)
        cls.rows = ledger_rows(text(LEDGER))

    def test_a_1_numbers_bound_to_the_ledger(self):
        self.assertEqual(sheet_problems(self.sheet, self.rows), [])

    def test_a_2_tags_exist_and_cover_the_sections(self):
        tags = set(TAG_RE.findall(self.sheet))
        self.assertTrue(tags)
        for t in tags:
            self.assertIn(t, self.rows, t)
        for t in (u"L-01", u"D-01", u"D-21", u"D-22", u"L-23", u"A-06"):
            self.assertIn(t, tags)

    def test_a_3_mentions_losing_first_and_the_gate(self):
        lines = [l for l in self.sheet.splitlines() if l.startswith(u"## ")]
        self.assertIn(u"負け", lines[0])
        self.assertIn(u"tests/measure/test_sales_sheet.py", self.sheet)
        self.assertIn(u"docs/FACTS_FOR_BUYERS_2026-10-20.md", self.sheet)


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheet = text(SHEET)
        cls.rows = ledger_rows(text(LEDGER))

    def test_m_1_changed_number_is_caught(self):
        bad = self.sheet.replace(u"12 / 24 = 50.0%", u"13 / 24 = 54.2%", 1)
        self.assertNotEqual(bad, self.sheet)
        self.assertNotEqual(sheet_problems(bad, self.rows), [])

    def test_m_2_changed_plain_count_is_caught(self):
        m = re.search(u"いまの木の試験 file は (\\d+)", self.sheet)
        bad = self.sheet.replace(m.group(0), u"いまの木の試験 file は %d" % (int(m.group(1)) + 1), 1)
        self.assertNotEqual(bad, self.sheet)
        self.assertNotEqual(sheet_problems(bad, self.rows), [])

    def test_m_3_wrong_tag_is_caught(self):
        bad = self.sheet.replace(u"〔台帳 L-23〕", u"〔台帳 L-24〕", 1)
        self.assertNotEqual(bad, self.sheet)
        self.assertNotEqual(sheet_problems(bad, self.rows), [])
        bad = self.sheet.replace(u"〔台帳 L-23〕", u"〔台帳 L-99〕", 1)
        self.assertNotEqual(sheet_problems(bad, self.rows), [])

    def test_m_4_untagged_number_is_caught(self):
        self.assertNotEqual(sheet_problems(self.sheet + u"\n- 記録に無い 42 件。\n", self.rows), [])
        self.assertEqual(sheet_problems(self.sheet + u"\n- 相手の数 42 件【門なし】。\n", self.rows), [])

    def test_m_5_forbidden_word_and_docid_are_caught(self):
        self.assertNotEqual(sheet_problems(self.sheet + u"\n- 他社より" + u"正確" + u"。\n", self.rows), [])
        self.assertNotEqual(sheet_problems(self.sheet + u"\n- " + u"S100" + u"ABCD" + u"\n", self.rows), [])

    def test_m_7_truncated_or_partial_numbers_are_caught(self):
        u"""監査で見つかった穴: 部分文字列の一致で、桁を欠いた数・1 桁の数・比の片側・見出しの数・型の名に化けた数が通っていた。"""
        for old, new in ((u"一致は 254", u"一致は 25"), (u"一致は 254", u"一致は 3"), (u"claim の数 523", u"claim の数 52"),
                         (u"止めた真の文は 53", u"止めた真の文は 5"), (u"結果文書 108", u"結果文書 10"),
                         (u"期間 18 / 18 = 100.0%", u"期間 8 / 18 = 100.0%"), (u"(T1)30", u"(T50)30"), (u"一致は 254", u"一致は 999. ")):
            bad = self.sheet.replace(old, new, 1)
            self.assertNotEqual(bad, self.sheet, old)
            self.assertNotEqual(sheet_problems(bad, self.rows), [], u"%s → %s が通った" % (old, new))
        bad = self.sheet.replace(u"## 2. ", u"## 2. 999 ", 1)
        self.assertNotEqual(bad, self.sheet)
        self.assertNotEqual(sheet_problems(bad, self.rows), [], u"見出しの数が通った")

    def test_m_8_tokens_are_boundary_aware(self):
        nums, ratios = tokens(u"一致 254; 率 24 / 523 = 4.6%; 1,300 件; 100.0%")
        self.assertEqual(nums, {u"254", u"24", u"523", u"4.6%", u"1300", u"100.0%"})
        self.assertEqual(ratios, {u"24 / 523 = 4.6%"})
        self.assertNotIn(u"25", nums)
        self.assertNotIn(u"4", nums)

    def test_m_6_ledger_row_change_is_caught(self):
        rows = dict(self.rows)
        rows[u"D-01"] = rows[u"D-01"].replace(u"18 / 18 = 100.0%", u"17 / 18 = 94.4%")
        self.assertNotEqual(rows[u"D-01"], self.rows[u"D-01"])
        self.assertNotEqual(sheet_problems(self.sheet, rows), [])


if __name__ == "__main__":
    unittest.main()
