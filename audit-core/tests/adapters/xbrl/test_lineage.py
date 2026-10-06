# -*- coding: utf-8 -*-
"""C-1c §5 系譜の試験: 原本(fixtures/xbrl/xbrl_probe*.py)は import せず写した。
この試験は原本を importlib で読み、Adapter の物と値で比べる。ZIP が無ければ
落ちる(skip にしない)。
"""

import unittest

from . import _material as M
from adapters.xbrl import comparators as C
from adapters.xbrl import extract as E
from adapters.xbrl import instance as I
from adapters.xbrl import vocabulary as V


def _pattern_and_flags(regex):
    return regex.pattern, regex.flags


# Shared by test_match_value (original vs. vocabulary.match_value) and
# test_match_value_also_matches_comparators_copy (vocabulary.match_value
# vs. comparators._match_value): the one set of (fact_value, target,
# unit) triples this lineage test already exercises, in ``main``'s own
# calling shape (fact, claim.value * unit_scale, claim_scale).
_MATCH_VALUE_CASES = [
    (100.0, 100.0, 1.0), (100.4, 100.0, 1.0), (100.6, 100.0, 1.0),
    (100.0, -100.0, 1.0), (-100.4, -100.0, 1.0),
    (1000000.0, 999999.6, 1.0), (999999.6, 1000000.0, 1.0),
    (0.0, 0.0, 1e6), (5.8, 5.8, 1.0), (3.0, 10.0, 1.0),
    (-52196000.0, 52196000.0, 1000.0), (-52196000.0, -52196000.0, 1000.0),
]


class ConstantLineageTest(unittest.TestCase):
    """§5-1: 正規表現・語の一覧・定数。"""

    @classmethod
    def setUpClass(cls):
        cls.ns = M.load_probe_originals()

    def test_regex_constants(self):
        probe, probe4 = self.ns.probe, self.ns.probe4
        pairs = [
            (probe.NUM_RE, E.NUM_RE),
            (probe.AMOUNT_JP_RE, E.AMOUNT_JP_RE),
            (probe.EXCLUDE_AFTER, E.EXCLUDE_AFTER),
            (probe.EXCLUDE_CONTEXT, E.EXCLUDE_CONTEXT),
            (probe.PCT_DIR_RE, E.PCT_DIR_RE),
            (probe.PCT_RATIO_RE, E.PCT_RATIO_RE),
            (probe4.CONN_RE, E.CONN_RE),
        ]
        for original, mine in pairs:
            self.assertEqual(_pattern_and_flags(original), _pattern_and_flags(mine))

    def test_subjects_73_matches_run_b(self):
        # P1 の語彙(1 本目 Run B の 73 語、順序込み)。
        self.assertEqual(self.ns.probe.SUBJECTS, list(V.SUBJECTS_73))
        self.assertEqual(len(V.SUBJECTS_73), 73)

    def test_subjects_74_matches_vocab4_plus_run_b(self):
        # P5F の語彙(4 本目の変更 A: 先頭に 1 行足した 74 語)。main() の
        # P.SUBJECTS.insert(0, VOCAB4) を実行せず、同じ操作を値で再現して比べる
        # (main 呼び出しは API/ZIP の材料に依存する副作用の多い経路のため)。
        probe4 = self.ns.probe4
        expected = [probe4.VOCAB4] + list(self.ns.probe.SUBJECTS)
        self.assertEqual(expected, list(V.SUBJECTS_74))
        self.assertEqual(len(V.SUBJECTS_74), 74)

    def test_direction_words(self):
        self.assertEqual(self.ns.probe.DIRECTION_WORDS, E.DIRECTION_WORDS)

    def test_state_words(self):
        self.assertEqual(self.ns.probe.STATE_WORDS, E.STATE_WORDS)

    def test_profit_subjects(self):
        self.assertEqual(self.ns.probe.PROFIT_SUBJECTS, V.PROFIT_SUBJECTS)

    def test_unit_scale(self):
        self.assertEqual(self.ns.probe.UNIT_SCALE, V.UNIT_SCALE)

    def test_mark_consol(self):
        self.assertEqual(self.ns.probe4.MARK_CONSOL, E.MARK_CONSOL)

    def test_carry_back(self):
        self.assertEqual(self.ns.probe3.CARRY_BACK, E.CARRY_BACK)

    def test_ambig(self):
        self.assertEqual(self.ns.probe3.AMBIG, E.AMBIG)


class FunctionGoldenTest(unittest.TestCase):
    """§5-2: 関数レベルの Golden(2 書類の MD&A の全文、1 社目 119 文・2 社目 136 文)。"""

    @classmethod
    def setUpClass(cls):
        cls.ns = M.load_probe_originals()
        cls.zb1 = M.load_zip_1()
        cls.zb5 = M.load_zip_5()
        cls.inst1 = I.load_instance(cls.zb1)
        cls.inst5 = I.load_instance(cls.zb5)
        cls.mdna1 = cls.ns.probe.strip_html(cls.inst1["textblocks"][I.select_mdna(cls.inst1["textblocks"])])
        cls.mdna5 = cls.ns.probe.strip_html(cls.inst5["textblocks"][I.select_mdna(cls.inst5["textblocks"])])
        cls.sent1 = E.split_sentences(cls.mdna1)
        cls.sent5 = E.split_sentences(cls.mdna5)

    def test_sentence_counts(self):
        self.assertEqual(len(self.sent1), 119)
        self.assertEqual(len(self.sent5), 136)

    def test_strip_html(self):
        for name, tb in list(self.inst1["textblocks"].items())[:20] + list(self.inst5["textblocks"].items())[:20]:
            self.assertEqual(self.ns.probe.strip_html(tb), I.strip_html(tb))
        for s in ("<p>a</p><br/>b<div>c</div>", "", "&amp;&lt;x&gt;", "<td>a</td><td>b</td>"):
            self.assertEqual(self.ns.probe.strip_html(s), I.strip_html(s))

    def test_load_instance(self):
        for zb in (self.zb1, self.zb5):
            orig = self.ns.probe.load_instance(zb)
            mine = I.load_instance(zb)
            self.assertEqual(len(orig["facts"]), len(mine["facts"]))
            self.assertEqual(sorted(orig["contexts"].keys()), sorted(mine["contexts"].keys()))
            self.assertEqual(sorted(orig["textblocks"].keys()), sorted(mine["textblocks"].keys()))
            self.assertEqual(orig["source"], mine["source"])

    def test_iter_numbers_over_all_sentences(self):
        for sentences in (self.sent1, self.sent5):
            for s in sentences:
                self.assertEqual(list(self.ns.probe.iter_numbers(s)), list(E.iter_numbers(s)))

    def test_subject_of_profile_p1(self):
        probe = self.ns.probe
        for sentences, inst in ((self.sent1, self.inst1), (self.sent5, self.inst5)):
            for si, s in enumerate(sentences):
                for (a, b, signed, unit, prec) in E.iter_numbers(s):
                    self.assertEqual(probe.subject_of(s, a), E.subject_of(s, a, V.SUBJECTS_73))

    def test_subject_of_profile_p5f(self):
        probe, probe4 = self.ns.probe, self.ns.probe4
        original_subjects = probe.SUBJECTS
        probe.SUBJECTS = [probe4.VOCAB4] + list(original_subjects)
        try:
            for sentences in (self.sent1, self.sent5):
                for si, s in enumerate(sentences):
                    for (a, b, signed, unit, prec) in E.iter_numbers(s):
                        self.assertEqual(probe.subject_of(s, a), E.subject_of(s, a, V.SUBJECTS_74))
        finally:
            probe.SUBJECTS = original_subjects

    def test_match_value(self):
        for fv, target, unit in _MATCH_VALUE_CASES:
            self.assertEqual(self.ns.probe.match_value(fv, target, unit), V.match_value(fv, target, unit))

    def test_match_value_also_matches_comparators_copy(self):
        # comparators.py's C-1d task §A decision: copy the ladder rather
        # than import vocabulary (so comparators.py reads only
        # evidence/claim.value/contract.params). This is the "系譜の試験
        # に値比較を1本足す" this decision called for: the original
        # (via importlib), vocabulary.match_value, and comparators's own
        # copy agree, value for value, on every case this lineage test
        # already uses for ``test_match_value``.
        for fv, target, unit in _MATCH_VALUE_CASES:
            original = self.ns.probe.match_value(fv, target, unit)
            vocabulary_copy = V.match_value(fv, target, unit)
            comparators_copy = C._match_value(fv, target, unit)
            self.assertEqual(original, vocabulary_copy)
            self.assertEqual(vocabulary_copy, comparators_copy)

    def test_tol_of(self):
        for fact in (
            {"decimals": "-6"}, {"decimals": "-3"}, {"decimals": "0"}, {"decimals": None},
            {"decimals": "INF"}, {},
        ):
            for scale in (1.0, 1e3, 1e6):
                self.assertEqual(self.ns.probe.tol_of(fact, scale), V.tol_of(fact, scale))

    def test_own_sign_match(self):
        probe5 = self.ns.probe5
        cases = [
            ("前年同期比 10.5% 増 のとおり", 10.5),
            ("前連結会計年度比 106.0%", 106.0),
            ("3.3%増加した一方、2.7%減少した", 3.3),
            ("3.3%増加した一方、2.7%減少した", 2.7),
            ("特に変化はない", 5.0),
        ]
        for window, num in cases:
            orig = probe5.own_sign_match(window, num)
            mine = E.own_sign_match(window, num)
            self.assertEqual(orig is None, mine is None)
            if orig is not None:
                self.assertEqual(orig.group(0), mine.group(0))

    def test_member_denominator(self):
        for inst in (self.inst1, self.inst5):
            self.assertEqual(self.ns.probe3.member_denominator(inst["contexts"]), I.member_denominator(inst["contexts"]))

    def test_labels_from_zip(self):
        import io
        import zipfile

        for zb, inst in ((self.zb1, self.inst1), (self.zb5, self.inst5)):
            z = zipfile.ZipFile(io.BytesIO(zb))
            self.assertEqual(
                self.ns.probe3.labels_from_zip(z, inst["names"]),
                I.labels_from_zip(z, inst["names"]),
            )

    def test_build_registry(self):
        import io
        import unicodedata
        import zipfile

        for zb, inst in ((self.zb1, self.inst1), (self.zb5, self.inst5)):
            z = zipfile.ZipFile(io.BytesIO(zb))
            members = self.ns.probe3.member_denominator(inst["contexts"])
            id2label = self.ns.probe3.labels_from_zip(z, inst["names"])
            mdna_name = I.select_mdna(inst["textblocks"])
            text = self.ns.probe.strip_html(inst["textblocks"][mdna_name]) if mdna_name else ""
            ntext = unicodedata.normalize("NFKC", text)
            orig_reg, orig_rows, orig_hand = self.ns.probe3.build_registry(members, id2label, ntext, "L")
            mine_reg, mine_rows, mine_hand = E.build_registry(members, id2label, ntext, "L")
            self.assertEqual(orig_reg, mine_reg)
            self.assertEqual(orig_rows, mine_rows)
            self.assertEqual(orig_hand, mine_hand)

    def test_paragraph_index(self):
        for sentences, (inst, zb) in ((self.sent1, (self.inst1, self.zb1)), (self.sent5, (self.inst5, self.zb5))):
            mdna_name = I.select_mdna(inst["textblocks"])
            text = self.ns.probe.strip_html(inst["textblocks"][mdna_name])
            self.assertEqual(self.ns.probe3.paragraph_index(text, sentences), E.paragraph_index(text, sentences))

    def test_resolve_members(self):
        import io
        import unicodedata
        import zipfile

        for zb, inst, sentences in ((self.zb5, self.inst5, self.sent5), (self.zb1, self.inst1, self.sent1)):
            z = zipfile.ZipFile(io.BytesIO(zb))
            members = self.ns.probe3.member_denominator(inst["contexts"])
            id2label = self.ns.probe3.labels_from_zip(z, inst["names"])
            mdna_name = I.select_mdna(inst["textblocks"])
            text = self.ns.probe.strip_html(inst["textblocks"][mdna_name])
            ntext = unicodedata.normalize("NFKC", text)
            reg, _rows, _hand = self.ns.probe3.build_registry(members, id2label, ntext, "L")
            paras = self.ns.probe3.paragraph_index(text, sentences)
            self.assertEqual(
                self.ns.probe3.resolve_members(sentences, paras, reg),
                E.resolve_members(sentences, paras, reg),
            )

    def test_claim_member_b(self):
        import io
        import unicodedata
        import zipfile

        zb, inst, sentences = self.zb5, self.inst5, self.sent5
        z = zipfile.ZipFile(io.BytesIO(zb))
        members = self.ns.probe3.member_denominator(inst["contexts"])
        id2label = self.ns.probe3.labels_from_zip(z, inst["names"])
        mdna_name = I.select_mdna(inst["textblocks"])
        text = self.ns.probe.strip_html(inst["textblocks"][mdna_name])
        ntext = unicodedata.normalize("NFKC", text)
        reg, _rows, _hand = self.ns.probe3.build_registry(members, id2label, ntext, "L")
        paras = self.ns.probe3.paragraph_index(text, sentences)
        sent_member = self.ns.probe3.resolve_members(sentences, paras, reg)
        for si, s in enumerate(sentences):
            for m in __import__("re").finditer("増加|減少|増収|増益|減収|減益", s):
                fallback = sent_member[si]
                self.assertEqual(
                    self.ns.probe4.claim_member_B(s, m.start(), reg, fallback),
                    E.claim_member_B(s, m.start(), reg, fallback),
                )


if __name__ == "__main__":
    unittest.main()
