# -*- coding: utf-8 -*-
"""C-2 系譜の試験(§2 対応表の Evidence Pointer 行): ``packet_ref.py`` の 2 つの
正規表現が ``scripts/playtest/lib/packetRef.ts`` の字面と一致することを、
TypeScript 側を**ファイルとして読んで**(import しない)確かめる。

``aggregate_id_of`` は ``hypothesis.ts`` の private(非 export)な
``aggregateIdOf`` の transcription。export されていないので TS を直接呼ぶ系譜試験
は書けない ― 代わりに、TS ソースを手でトレースして導いた既知の入出力(一部は
``exitSelect.ts`` の ``aggregateIdOfRef``(同じ "middle segment" の切り出しをする、
別の公開関数)の既存試験 ``exitSelect.test.ts`` のケースと共有)で固定する。
"""

import os
import re
import unittest

from adapters.shogi import packet_ref as PR

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_REPO_ROOT = os.path.abspath(os.path.join(_AUDIT_CORE, ".."))
_PACKET_REF_TS = os.path.join(_REPO_ROOT, "scripts", "playtest", "lib", "packetRef.ts")


def _extract_js_regex_literal(ts_source, const_name):
    pattern = re.compile(r"export const %s = /(.*)/;" % re.escape(const_name))
    m = pattern.search(ts_source)
    if m is None:
        raise AssertionError("%r not found in %s" % (const_name, _PACKET_REF_TS))
    return m.group(1)


class RegexLineageTest(unittest.TestCase):
    """packetRef.ts の正規表現リテラルの字面と、Python 側の .pattern を比べる。"""

    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(_PACKET_REF_TS):
            raise FileNotFoundError("packetRef.ts が無い: %s" % (_PACKET_REF_TS,))
        with open(_PACKET_REF_TS, "r", encoding="utf-8") as handle:
            cls.ts_source = handle.read()

    def test_aggregate_ref_re_matches_ts_literal(self):
        ts_literal = _extract_js_regex_literal(self.ts_source, "AGGREGATE_REF_RE")
        self.assertEqual(ts_literal, PR.AGGREGATE_REF_RE.pattern)

    def test_facts_ref_re_matches_ts_literal(self):
        ts_literal = _extract_js_regex_literal(self.ts_source, "FACTS_REF_RE")
        self.assertEqual(ts_literal, PR.FACTS_REF_RE.pattern)


class PathProblemsTest(unittest.TestCase):
    def test_non_string_or_empty(self):
        self.assertEqual(PR.path_problems(None), ["packetRef.path が文字列でない・空"])
        self.assertEqual(PR.path_problems(123), ["packetRef.path が文字列でない・空"])
        self.assertEqual(PR.path_problems(""), ["packetRef.path が文字列でない・空"])

    def test_aggregate_form_ok(self):
        self.assertEqual(PR.path_problems("aggregates.groups.core.games.value"), [])
        self.assertEqual(PR.path_problems("aggregates.a.numerator"), [])
        self.assertEqual(PR.path_problems("aggregates.a.denominator"), [])

    def test_facts_form_ok(self):
        self.assertEqual(PR.path_problems("facts.moves[0].usi"), [])
        self.assertEqual(PR.path_problems("facts.recognition.rows[3].selfSignature"), [])
        self.assertEqual(PR.path_problems("facts.branches[12].topGapCp"), [])

    def test_aggregates_single_form_rejected(self):
        # 司令塔の決定 2026-09-30: aggregates.<id> 単独は受けない。
        problems = PR.path_problems("aggregates.groups.core.games")
        self.assertEqual(len(problems), 1)
        self.assertIn("文法", problems[0])

    def test_facts_without_index_rejected(self):
        problems = PR.path_problems("facts.time.bySpent[3]")
        self.assertEqual(len(problems), 1)

    def test_unknown_facts_column_rejected(self):
        problems = PR.path_problems("facts.unknownColumn[0].x")
        self.assertEqual(len(problems), 1)

    def test_facts_missing_bracket_entirely_rejected(self):
        # 列の直後に添字が無い書き方は文法で落ちる(packetRef.ts のコメント
        # 「列の直後に添字」)。S-R2(FACTS_REF_RE の添字を任意にする変異)の的。
        problems = PR.path_problems("facts.moves.usi")
        self.assertEqual(len(problems), 1)


class AggregateIdOfTest(unittest.TestCase):
    def test_known_cases(self):
        # exitSelect.test.ts のケース(同じ切り出し)と共有。
        self.assertEqual(PR.aggregate_id_of("aggregates.groups.core.games.value"), "groups.core.games")
        self.assertEqual(PR.aggregate_id_of("aggregates.side_match.attack.numerator"), "side_match.attack")
        self.assertEqual(PR.aggregate_id_of("aggregates.a.denominator"), "a")

    def test_no_id_component_is_none(self):
        self.assertIsNone(PR.aggregate_id_of("aggregates.value"))

    def test_not_aggregates_path_is_none(self):
        self.assertIsNone(PR.aggregate_id_of("facts.moves[0].usi"))

    def test_last_segment_not_a_part_is_none(self):
        self.assertIsNone(PR.aggregate_id_of("aggregates.groups.core.games"))


if __name__ == "__main__":
    unittest.main()
