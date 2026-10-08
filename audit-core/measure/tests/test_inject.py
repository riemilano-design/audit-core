# -*- coding: utf-8 -*-
"""Self-tests for the injection tool.

Shapes chosen on purpose (記憶: 恒等・不変・連続性):

* **identity** ― asking for zero injections must return the document byte
  for byte. A tool that "normalises" its input silently changes what is
  being measured.
* **round trip** ― the record alone must rebuild the original from the
  tampered text. If it cannot, the record does not describe the document and
  every later score is meaningless.
* **invariance** ― shuffling the reference list, or renaming reference keys,
  must not change which sites exist.
* **the guards are the point** ― T1's replacement must be absent from the
  reference numbers and T5's must be present. These two assertions are what
  separate "a value mismatch" from "the known worst hole", so each is tested
  directly rather than through the count of injections.
* **degenerate inputs** ― empty text, no references, one reference, no
  numbers, and count larger than the catalogue. A full sweep of mutations
  can still be green while a degenerate input crashes.
"""

import argparse
import hashlib
import inspect
import io
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
MEASURE = os.path.dirname(HERE)
sys.path.insert(0, MEASURE)

import inject  # noqa: E402
import prepare_material  # noqa: E402
from lib import numbers as N  # noqa: E402
from lib import sites as S  # noqa: E402
from lib import scales as SC  # noqa: E402

TEXT = (
    "今回の 25 局を調べました。\n"
    "分かれ道 107 局面のうち、実戦も攻めだった局面が 65 でした。\n"
    "長考の直後の 37 手のうち、崩れた手が 9 でした。\n"
    "優勢になった対局は 18 局で、そのうち負けたのは 6 局です。\n"
    "売上は 1,234 百万円、前期は 1,100 百万円でした。\n"
)

REFS = [
    {"key": "a.denominator", "label": "分かれ道", "unit": "局面", "value": 107.0, "role": "denominator"},
    {"key": "a.numerator", "label": "攻めで一致", "unit": "局面", "value": 65.0, "role": "numerator"},
    {"key": "b.denominator", "label": "長考直後", "unit": "手", "value": 37.0, "role": "denominator"},
    {"key": "b.numerator", "label": "崩れた手", "unit": "手", "value": 9.0, "role": "numerator"},
    {"key": "c.value", "label": "優勢になった対局", "unit": "局", "value": 18.0, "role": "value"},
    {"key": "d.value", "label": "そのうち負け", "unit": "局", "value": 6.0, "role": "value"},
]

SEED = "test-seed-0001"


def build(count, text=TEXT, refs=REFS, kind="shogi", seed=SEED, doc="t", types=None):
    chosen, counts, allowed, withheld = inject.select(text, refs, kind, seed, doc, count, types)
    tampered, placements = inject.apply_edits(text, chosen)
    return chosen, counts, tampered, placements


class TestScanner(unittest.TestCase):
    def test_unit_after_space(self):
        toks = {t.value: t.unit for t in N.scan("25 局と 107 局面と 9 手")}
        self.assertEqual(toks[25.0], "局")
        self.assertEqual(toks[107.0], "局面")
        self.assertEqual(toks[9.0], "手")

    def test_calendar_is_not_a_unit(self):
        for s in ["2026 年", "9 月", "28 日", "3 頁", "第 2 四半期", "1 つ目"]:
            for t in N.scan(N.normalize_digits(s)):
                self.assertIsNone(t.unit, "%r took a calendar word as a unit" % s)

    def test_normalize_preserves_length(self):
        s = "１２３．４５、１，０００"
        self.assertEqual(len(N.normalize_digits(s)), len(s))
        self.assertEqual(N.scan(N.normalize_digits(s))[0].value, 123.45)

    def test_thousands_and_decimals(self):
        vals = [t.value for t in N.scan("1,234 と 15.0 と 1,100")]
        self.assertEqual(vals, [1234.0, 15.0, 1100.0])

    def test_render_keeps_surface_form(self):
        tok = N.scan("1,234")[0]
        self.assertEqual(N.render_value(5678.0, tok), "5,678")
        frac = N.scan("15.0")[0]
        self.assertEqual(N.render_value(16.0, frac), "16.0")

    def test_sentence_spans_tile_the_text(self):
        spans = N.sentence_spans(TEXT)
        self.assertEqual("".join(TEXT[a:b] for a, b in spans), TEXT)


class TestIdentity(unittest.TestCase):
    def test_zero_injections_is_byte_identical(self):
        chosen, _, tampered, _ = build(0)
        self.assertEqual(chosen, [])
        self.assertEqual(tampered, TEXT)

    def test_round_trip_rebuilds_original(self):
        chosen, _, tampered, placements = build(8)
        self.assertNotEqual(tampered, TEXT)
        self.assertEqual(inject.revert(tampered, chosen, placements, TEXT), TEXT)

    def test_tampered_spans_locate_the_replacement(self):
        chosen, _, tampered, placements = build(8)
        for c in chosen:
            a, b = placements[c["id"]]
            self.assertEqual(tampered[a:b], c["replacement"], c["id"])


class TestInvariance(unittest.TestCase):
    def test_shuffling_references_does_not_change_the_catalogue(self):
        base = {s["token"].start for s in S.t1_sites(TEXT, REFS)}
        ident = {(t.start, r["key"]) for t, r in S.identified_sites(TEXT, REFS)}
        for i in range(5):
            shuffled = list(REFS)
            random.Random(i).shuffle(shuffled)
            self.assertEqual({s["token"].start for s in S.t1_sites(TEXT, shuffled)}, base)
            self.assertEqual({(t.start, r["key"]) for t, r in S.identified_sites(TEXT, shuffled)}, ident)

    def test_renaming_keys_does_not_change_which_sites_exist(self):
        renamed = [dict(r, key="z" + r["key"]) for r in REFS]
        self.assertEqual(
            [s["token"].start for s in S.t1_sites(TEXT, REFS)],
            [s["token"].start for s in S.t1_sites(TEXT, renamed)],
        )

    def test_same_seed_same_result_different_seed_differs(self):
        a = build(6)[2]
        self.assertEqual(a, build(6)[2])
        others = {build(6, seed="other-%d" % i)[2] for i in range(6)}
        self.assertTrue(any(o != a for o in others), "seed has no effect on the result")

    def test_document_id_separates_the_draws(self):
        a = {c["type"] + str(c["span"]) for c in build(6, doc="d1")[0]}
        b = {c["type"] + str(c["span"]) for c in build(6, doc="d2")[0]}
        self.assertNotEqual(a, b)


class TestGuards(unittest.TestCase):
    def test_no_two_injections_overlap(self):
        chosen, _, _, _ = build(12)
        spans = sorted(tuple(c["span"]) for c in chosen)
        for (a, b), (c, d) in zip(spans, spans[1:]):
            self.assertFalse(a < d and c < b and not (a == b or c == d), "overlap %s %s" % ((a, b), (c, d)))

    def test_t1_replacement_is_absent_from_the_reference_numbers(self):
        present = {round(r["value"], 6) for r in REFS}
        found = 0
        for c in build(12)[0]:
            if c["type"] != "T1_VALUE":
                continue
            found += 1
            d = c["detail"]
            self.assertNotIn(round(d["replacement_value"], 6), present, c["id"])
            self.assertNotEqual(d["replacement_value"], d["original_value"])
        self.assertGreater(found, 0, "no T1 injection was built, so its guard was never exercised")

    def test_t1_does_not_claim_a_reference(self):
        """型 1 must not name a true reference. Naming one is how the first
        version produced records asserting a fact the sentence was not
        about."""
        for c in build(12)[0]:
            if c["type"] != "T1_VALUE":
                continue
            self.assertNotIn("true_ref_key", c["detail"])
            self.assertIn("candidate_ref_count", c["detail"])

    def test_t5_replacement_is_present_but_belongs_to_another_fact(self):
        by_key = {r["key"]: r["value"] for r in REFS}
        found = 0
        for c in build(12)[0]:
            if c["type"] != "T5_COINCIDENT":
                continue
            found += 1
            d = c["detail"]
            self.assertIn(round(d["replacement_value"], 6), {round(v, 6) for v in by_key.values()})
            self.assertNotEqual(d["coincident_ref_key"], d["true_ref_key"])
            self.assertEqual(round(by_key[d["coincident_ref_key"]], 6), round(d["replacement_value"], 6))
            self.assertNotEqual(round(d["replacement_value"], 6), round(d["true_value"], 6))
            self.assertNotEqual(d["coincident_ref_label"], d["true_ref_label"])
            ratio = d["replacement_value"] / d["true_value"]
            self.assertTrue(1.0 / S.MAGNITUDE_RATIO <= ratio <= S.MAGNITUDE_RATIO,
                            "magnitude jump %s -> %s" % (d["true_value"], d["replacement_value"]))
        self.assertGreater(found, 0, "no T5 injection was built, so its guard was never exercised")

    def test_t2_keeps_the_digits_and_swaps_inside_the_family(self):
        found = 0
        for c in build(12)[0]:
            if c["type"] != "T2_UNIT":
                continue
            found += 1
            d = c["detail"]
            self.assertNotEqual(d["unit_before"], d["unit_after"])
            fam_before = N.unit_family(d["unit_before"])
            fam_after = N.unit_family(d["unit_after"])
            same_family = fam_before == fam_after
            both_counts = d["unit_before"] in N.COUNT_FAMILY and d["unit_after"] in N.COUNT_FAMILY
            self.assertTrue(same_family or both_counts, "%s -> %s" % (d["unit_before"], d["unit_after"]))
            self.assertEqual(c["replacement"], d["unit_after"])
        self.assertGreater(found, 0, "no T2 injection was built, so its guard was never exercised")

    def test_only_one_injection_per_number(self):
        """A value substitution and a unit shift on the same number do not
        overlap as spans, but the record could no longer say which type a
        detection belonged to. Measured: before this guard, 107 局面 became
        65 手 under one draw."""
        chosen, _, _, _ = build(12)
        seen = []
        for c in chosen:
            if c["type"] == "T3_ABSENT":
                continue
            # The digits of a T1/T5 start at span[0]; a T2's unit sits just
            # after the digits, so attribute each edit to its sentence number.
            seen.append((c["type"], tuple(c["span"])))
        starts = [s for _, s in seen]
        self.assertEqual(len(starts), len(set(starts)))

    def test_t2_keeps_the_digits_in_the_output(self):
        """Read the digits out of the tampered text at the recorded tampered
        span, not at the original span: earlier edits shift the offsets."""
        chosen, _, tampered, placements = build(12)
        found = 0
        for c in chosen:
            if c["type"] != "T2_UNIT":
                continue
            found += 1
            a, b = placements[c["id"]]
            self.assertEqual(tampered[a:b], c["detail"]["unit_after"])
            before = tampered[max(0, a - 16):a]
            self.assertIn(c["detail"]["digits_unchanged"], before)
        self.assertGreater(found, 0)

    def test_t3_subject_and_value_are_absent(self):
        present = {round(r["value"], 6) for r in REFS}
        labels = " ".join(str(r["label"]) for r in REFS)
        found = 0
        for c in build(12)[0]:
            if c["type"] != "T3_ABSENT":
                continue
            found += 1
            subj = c["detail"]["fabricated_subject"]
            self.assertNotIn(subj, TEXT)
            self.assertNotIn(subj, labels)
            self.assertNotIn(round(c["new_value"], 6), present)
            self.assertEqual(c["span"][0], c["span"][1], "T3 must be an insertion")
        self.assertGreater(found, 0, "no T3 injection was built, so its guard was never exercised")

    def test_all_four_machine_types_are_reachable(self):
        got = {c["type"] for c in build(12)[0]}
        self.assertEqual(got, set(inject.MACHINE_TYPES), "missing: %s" % (set(inject.MACHINE_TYPES) - got))


class TestQuantityScreen(unittest.TestCase):
    """The numbers that must never become a 型 1 / 型 5 site.

    All three are real: they were produced as injections by the first
    version, each with a ``true_ref_key`` the sentence was not about.
    """

    OFFENDERS = [
        ("4【経営者による財政状態、経営成績及びキャッシュ・フローの状況の分析】", "4", "見出しの番号"),
        ("（自　2025年7月1日", "7", "日付の月"),
        ("0〜1 秒で指した手", "0", "範囲の下限"),
        ("2.最近2連結会計年度の主な相手先別の販売実績", "2", "箇条書きの番号"),
        ("| 2 | g02-sente.kif | 先手 | 87 | 勝ち |", "2", "表の行番号"),
        ("| 2 | g02-sente.kif | 先手 | 87 | 勝ち |", "02", "ファイル名の中の数字"),
        ("受注高は394億1千9百万円となりました", "9", "和数字の合成の部品"),
        ("「第5　経理の状況」", "5", "章の参照"),
        ("1株当たり当期純利益は69.64円", "1", "単位あたりの分母"),
    ]

    # 直し 1(2026-10-08 監査)。この一つだけ unit が「回」(COUNT_FAMILY の
    # メンバー)として認識されるため、t1_sites/t5_sites に加えて t2_sites も
    # 同じ理由で screen しなければ落ちない。実例: S100Z4B6 の「第三者割当による
    # 新株式発行及び第2回新株予約権の発行」。is_quantity を呼んでいなかった
    # t2_sites がこれを拾い、実際に「第2局新株予約権の発行」として混入した。
    ORDINAL_WITH_UNIT_OFFENDER = (
        "第三者割当による新株式発行及び第2回新株予約権の発行", "2", "回を数える序数(第2回)",
    )

    def test_offenders_are_not_quantities(self):
        for text, digits, why in self.OFFENDERS:
            t = N.normalize_digits(text)
            tok = next(x for x in N.scan(t) if x.text == digits)
            self.assertFalse(N.is_quantity(t, tok), "%s (%s) was taken as a quantity" % (digits, why))

    def test_offenders_do_not_become_sites(self):
        refs = [{"key": "k%d" % i, "label": "何か", "unit": None, "value": float(v), "role": "value"}
                for i, v in enumerate([4, 7, 0, 2])]
        for text, digits, why in self.OFFENDERS:
            t = N.normalize_digits(text)
            starts = {s["token"].start for s in S.t1_sites(t, refs)}
            starts |= {s["token"].start for s in S.t5_sites(t, refs)}
            tok = next(x for x in N.scan(t) if x.text == digits)
            self.assertNotIn(tok.start, starts, "%s (%s)" % (digits, why))

    def test_the_ordinal_offender_is_not_a_quantity(self):
        text, digits, why = self.ORDINAL_WITH_UNIT_OFFENDER
        t = N.normalize_digits(text)
        tok = next(x for x in N.scan(t) if x.text == digits)
        self.assertEqual(tok.unit, "回", "%s (%s) did not even carry the unit that caused the bug" % (digits, why))
        self.assertFalse(N.is_quantity(t, tok), "%s (%s) was taken as a quantity" % (digits, why))

    def test_the_ordinal_offender_does_not_become_a_t2_site(self):
        """直し 1(2026-10-08 監査)の回帰試験。t1_sites/t5_sites だけでなく
        t2_sites も同じ is_quantity 除外を通さなければ、「第2回」の「2」が
        型 2(単位のずれ)のサイトになり、「回」が「局/手/局面/件」に
        入れ替えられて「第2局新株予約権の発行」のような、序数を数量の
        入れ替えにした誤りが実際に混入する(S100Z4B6 で実測)。"""
        text, digits, why = self.ORDINAL_WITH_UNIT_OFFENDER
        t = N.normalize_digits(text)
        tok = next(x for x in N.scan(t) if x.text == digits)
        starts = {s["token"].start for s in S.t2_sites(t, [])}
        self.assertNotIn(tok.start, starts, "%s (%s) became a T2_UNIT site" % (digits, why))

    def test_a_real_quantity_still_passes(self):
        t = N.normalize_digits("今回の 25 局を調べました。")
        tok = next(x for x in N.scan(t) if x.text == "25")
        self.assertTrue(N.is_quantity(t, tok))
        self.assertEqual(tok.unit, "局")

    def test_unidentifiable_numbers_are_reported_not_dropped(self):
        """A number that carries data but cannot be pinned down must appear
        in the unidentified list, so the count is visible."""
        refs = REFS + [{"key": "x.value", "label": "別の事実", "unit": "局面", "value": 107.0, "role": "value"}]
        u = S.unidentified_sites(TEXT, refs)
        self.assertGreater(len(u), 0)
        for row in u:
            self.assertIn("candidate_count", row)
            self.assertIn("line", row)


class TestGuardsAreLoadBearing(unittest.TestCase):
    """Each test here went green when its guard was deleted, until the
    fixture was built to exercise it. Mutation run 2026-10-08: 7 of 14
    mutations were silent; six of those were this kind of fixture gap.
    """

    def test_t1_skips_a_replacement_that_lands_on_a_reference(self):
        """M-01. The first candidate the search tries is value + 2, so a
        reference holding value + 2 must push it further."""
        text = "今回の 25 局を調べました。\n"
        refs = [
            {"key": "a", "label": "対象の局", "unit": "局", "value": 25.0, "role": "value"},
            {"key": "b", "label": "別の局", "unit": "局", "value": 27.0, "role": "value"},
        ]
        sites = S.t1_sites(text, refs)
        self.assertEqual(len(sites), 1)
        built = inject.build_t1(sites[0], refs, random.Random(0))
        self.assertIsNotNone(built)
        self.assertNotEqual(built["detail"]["replacement_value"], 27.0,
                            "took a value that a reference already holds")
        self.assertNotIn(round(built["detail"]["replacement_value"], 6),
                         {round(r["value"], 6) for r in refs})

    def test_t5_refuses_a_borrowed_fact_with_the_same_label(self):
        """M-04. Real case: the same XBRL element in two contexts, so the
        record would read 'true=AverageNumberOfTemporaryWorkers,
        borrowed=AverageNumberOfTemporaryWorkers'."""
        text = "平均の人数は 22 局ありました。\n"
        same = [
            {"key": "x@c1", "label": "同じラベル", "unit": "局", "value": 22.0, "role": "value"},
            {"key": "x@c2", "label": "同じラベル", "unit": "局", "value": 30.0, "role": "value"},
        ]
        self.assertEqual(len(S.identified_sites(text, same)), 1)
        self.assertEqual(S.t5_sites(text, same), [],
                         "borrowed a fact carrying the same label")
        differ = [same[0], dict(same[1], label="別のラベル")]
        self.assertEqual(len(S.t5_sites(text, differ)), 1)

    def test_t5_refuses_a_borrowed_fact_of_a_different_magnitude(self):
        """M-05. Real case: a subsidiary count of 3 borrowed a cash-flow
        amount of 25,568,000."""
        text = "対象は 22 局ありました。\n"
        far = [
            {"key": "a", "label": "対象", "unit": "局", "value": 22.0, "role": "value"},
            {"key": "b", "label": "遠い値", "unit": "局", "value": 5000.0, "role": "value"},
        ]
        self.assertEqual(S.t5_sites(text, far), [], "borrowed a value 227x away")
        near = [far[0], dict(far[1], value=60.0)]
        self.assertEqual(len(S.t5_sites(text, near)), 1)

    def test_identifier_and_row_number_are_not_sites(self):
        """M-08 / M-13 together, on the real line that produced them."""
        text = "| 2 | g02-sente.kif | 先手 | 87 | 勝ち |\n"
        refs = [{"key": "k%d" % v, "label": "何か", "unit": None, "value": float(v), "role": "value"}
                for v in (2, 87)]
        starts = {s["token"].start for s in S.t1_sites(text, refs)}
        for digits in ("2", "02"):
            tok = next(x for x in N.scan(text) if x.text == digits)
            self.assertNotIn(tok.start, starts, "%r became a site" % digits)

    def test_digits_at_the_end_of_an_identifier_are_not_a_site(self):
        """M-08 on its own. In "g02-sente.kif" the trailing hyphen also
        catches the digits, so the leading-character check was untested until
        a name that *ends* in digits was used."""
        text = "群 B にあたる対局は g02 です。\n"
        refs = [{"key": "k", "label": "何か", "unit": None, "value": 2.0, "role": "value"}]
        tok = next(x for x in N.scan(text) if x.text == "02")
        self.assertFalse(N.is_quantity(text, tok))
        self.assertNotIn(tok.start, {s["token"].start for s in S.t1_sites(text, refs)})


class TestEndToEnd(unittest.TestCase):
    """Exercise ``main()``.

    The round-trip check and the seed seal live in ``main()``, and no test
    reached them: mutation M-12 deleted the round-trip check and all 50
    tests stayed green. A guard that only production runs is not a guard.
    """

    def _repo(self, tmp):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        subprocess.run(["git", "init", "-q", tmp], check=True)
        seed = os.path.join(tmp, "SEED.json")
        with io.open(seed, "w", encoding="utf-8") as fh:
            fh.write('{"seed": "%s"}' % SEED)
        mat = os.path.join(tmp, "material")
        os.makedirs(mat)
        with io.open(os.path.join(mat, "d.original.txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(TEXT)
        with io.open(os.path.join(mat, "d.reference_numbers.json"), "w", encoding="utf-8") as fh:
            json.dump({"refs": REFS}, fh, ensure_ascii=False)
        subprocess.run(["git", "-C", tmp, "add", "SEED.json"], check=True)
        subprocess.run(["git", "-C", tmp, "commit", "-qm", "seal"], check=True, env=env)
        return seed, mat

    def test_a_full_run_writes_the_three_outputs_and_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed, mat = self._repo(tmp)
            out = os.path.join(tmp, "documents")
            rec = os.path.join(tmp, "records")
            rc = inject.main([
                "--doc", "d", "--kind", "shogi", "--material", mat,
                "--seed-file", seed, "--count", "6", "--out", out, "--record-dir", rec,
            ])
            self.assertEqual(rc, 0)
            tampered = io.open(os.path.join(out, "d.tampered.txt"), encoding="utf-8", newline="").read()
            self.assertNotEqual(tampered, TEXT)
            with io.open(os.path.join(rec, "d.record.json"), encoding="utf-8") as fh:
                record = json.load(fh)
            self.assertTrue(record["round_trip_verified"])
            self.assertEqual(record["injected_count"], 6)

            # The record must rebuild the original from the tampered text.
            rebuilt = tampered
            for inj in sorted(record["injections"], key=lambda i: -i["tampered_span"][0]):
                a, b = inj["tampered_span"]
                self.assertEqual(tampered[a:b], inj["replacement_text"])
                rebuilt = rebuilt[:a] + inj["original_text"] + rebuilt[b:]
            self.assertEqual(rebuilt, TEXT, "the record does not describe the document")

    def test_the_record_stays_outside_the_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed, mat = self._repo(tmp)
            out = os.path.join(tmp, "documents")
            rec = os.path.join(tmp, "records")
            inject.main(["--doc", "d", "--kind", "shogi", "--material", mat,
                         "--seed-file", seed, "--count", "6", "--out", out, "--record-dir", rec])
            handed_over = set(os.listdir(out))
            self.assertNotIn("d.record.json", handed_over)
            self.assertIn("d.record.sha256", handed_over)
            # The digest in the repo must match the record that was written.
            with io.open(os.path.join(rec, "d.record.json"), "rb") as fh:
                actual = hashlib.sha256(fh.read()).hexdigest()
            with io.open(os.path.join(out, "d.record.sha256"), encoding="utf-8") as fh:
                self.assertTrue(fh.read().startswith(actual))

    def test_a_failed_round_trip_aborts_and_writes_nothing(self):
        """M-12. The abort only fires when reverting disagrees with the
        original, which valid input never does -- so the guard was invisible
        to every test until the failure was forced."""
        with tempfile.TemporaryDirectory() as tmp:
            seed, mat = self._repo(tmp)
            out = os.path.join(tmp, "documents")
            original = inject.revert
            inject.revert = lambda *a, **k: "この文書は元に戻らなかった"
            try:
                with self.assertRaises(SystemExit) as cm:
                    inject.main(["--doc", "d", "--kind", "shogi", "--material", mat,
                                 "--seed-file", seed, "--count", "6", "--out", out,
                                 "--record-dir", os.path.join(tmp, "records")])
                self.assertIn("round-trip failed", str(cm.exception))
            finally:
                inject.revert = original
            self.assertFalse(os.path.exists(out), "wrote a document despite a failed round trip")
            self.assertFalse(os.path.exists(os.path.join(tmp, "records")))

    def test_a_run_with_an_unsealed_seed_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed, mat = self._repo(tmp)
            with io.open(seed, "w", encoding="utf-8") as fh:
                fh.write('{"seed": "changed-after-the-fact"}')
            out = os.path.join(tmp, "documents")
            with self.assertRaises(inject.SealError):
                inject.main(["--doc", "d", "--kind", "shogi", "--material", mat,
                             "--seed-file", seed, "--count", "6", "--out", out,
                             "--record-dir", os.path.join(tmp, "records")])
            self.assertFalse(os.path.exists(out))


class TestNotNotation(unittest.TestCase):
    """A notational swap is not an error.

    Measured 2026-10-08: the tool produced "％ -> %". The core would judge
    that GROUNDED, and because the denominator is every injected error, a
    free miss pushes the detection rate down.
    """

    def test_percent_notation_is_one_unit(self):
        self.assertTrue(N.same_unit("%", "％"))
        self.assertEqual(N.canonical_unit("％"), "%")

    def test_t2_never_swaps_between_notations(self):
        for text in ("前期比 12.5 ％ 増でした。\n", "前期比 12.5 % 増でした。\n"):
            for site in S.t2_sites(text, []):
                for sib in site["siblings"]:
                    self.assertFalse(N.same_unit(sib, site["token"].unit),
                                     "%s -> %s is only a notation change" % (site["token"].unit, sib))

    def test_t2_on_a_percent_still_has_a_real_sibling(self):
        sites = S.t2_sites("前期比 12.5 ％ 増でした。\n", [])
        self.assertEqual(len(sites), 1)
        self.assertEqual(sites[0]["siblings"], ["ポイント"])


class TestT3Distinct(unittest.TestCase):
    def test_subjects_and_values_are_distinct_within_a_document(self):
        chosen = [c for c in build(18)[0] if c["type"] == "T3_ABSENT"]
        self.assertGreater(len(chosen), 1)
        subs = [c["detail"]["fabricated_subject"] for c in chosen]
        vals = [c["new_value"] for c in chosen]
        self.assertEqual(len(subs), len(set(subs)), "a fabricated subject was reused")
        self.assertEqual(len(vals), len(set(vals)), "a fabricated value was reused")

    def test_inserted_sentence_has_no_space_before_wa(self):
        for c in build(18)[0]:
            if c["type"] == "T3_ABSENT":
                self.assertNotIn(" は", c["replacement"])


class TestDegenerate(unittest.TestCase):
    def test_empty_text(self):
        chosen, counts, tampered, _ = build(4, text="", refs=REFS)
        self.assertEqual(tampered, "")
        self.assertEqual(chosen, [])

    def test_no_references(self):
        chosen, _, tampered, placements = build(4, refs=[])
        # T1/T5 need a resolved reference; T2/T3 do not.
        self.assertTrue(all(c["type"] in ("T2_UNIT", "T3_ABSENT") for c in chosen))
        self.assertEqual(inject.revert(tampered, chosen, placements, TEXT), TEXT)

    def test_single_reference(self):
        chosen, _, tampered, placements = build(4, refs=REFS[:1])
        self.assertEqual(inject.revert(tampered, chosen, placements, TEXT), TEXT)
        # With one reference there is no "other fact", so T5 is impossible.
        self.assertNotIn("T5_COINCIDENT", {c["type"] for c in chosen})

    def test_text_without_numbers(self):
        t = "数のない文です。\nここにも数はありません。\n"
        chosen, _, tampered, _ = build(4, text=t)
        self.assertTrue(all(c["type"] == "T3_ABSENT" for c in chosen))
        self.assertEqual(len(tampered) >= len(t), True)

    def test_count_larger_than_catalogue_does_not_loop(self):
        chosen, counts, _, _ = build(10000)
        self.assertLess(len(chosen), 10000)
        self.assertGreater(len(chosen), 0)

    def test_negative_and_zero_count(self):
        self.assertEqual(build(0)[0], [])
        self.assertEqual(build(-5)[0], [])

    def test_duplicate_reference_values_block_identification_not_t1(self):
        """Two references share 107 under different keys.

        The token can no longer be *identified*, so no 型 5 may be built on
        it. It is still data-bearing, so 型 1 may: a value absent from every
        reference is wrong whichever of the two the sentence meant.
        """
        refs = REFS + [{"key": "x.value", "label": "別の事実", "unit": "局面", "value": 107.0, "role": "value"}]
        amb = next(t.start for t in N.scan(TEXT) if t.value == 107.0)
        self.assertIn(amb, {s["token"].start for s in S.t1_sites(TEXT, refs)})
        self.assertNotIn(amb, {t.start for t, _ in S.identified_sites(TEXT, refs)})
        self.assertNotIn(amb, {s["token"].start for s in S.t5_sites(TEXT, refs)})
        self.assertIn(amb, {u["span"][0] for u in S.unidentified_sites(TEXT, refs)})


class TestTypePolicy(unittest.TestCase):
    """The per-corpus policy is part of the contract, not a default to drift.

    XBRL withholds 型 1 and 型 5 because identifying what a prose number
    refers to needs the extractor's reading of mixed Japanese numerals and
    the 円 / 百万円 scale, which this package may not use.
    """

    def test_xbrl_withholds_t1_and_t5(self):
        self.assertEqual(inject.TYPE_POLICY["xbrl"], ["T2_UNIT", "T3_ABSENT"])
        chosen, _, _, _ = build(12, kind="xbrl")
        self.assertEqual({c["type"] for c in chosen} - {"T2_UNIT", "T3_ABSENT"}, set())

    def test_shogi_builds_all_four(self):
        self.assertEqual(sorted(inject.TYPE_POLICY["shogi"]), sorted(inject.MACHINE_TYPES))

    def test_withheld_types_are_counted_not_hidden(self):
        _, _, allowed, withheld = inject.select(TEXT, REFS, "xbrl", SEED, "t", 12, None)
        self.assertEqual(sorted(withheld), ["T1_VALUE", "T5_COINCIDENT"])
        self.assertTrue(all(isinstance(v, int) for v in withheld.values()))

    def test_the_observed_t5_examples_stay_attached_to_the_policy(self):
        """The filings get no 型 5 by machine, so the claim "this hole is
        real in a filing" rests on the three observed cases. If that file
        goes missing, the policy is left looking like a measured zero."""
        path = os.path.join(MEASURE, "material", "xbrl", "observed_t5.json")
        self.assertTrue(os.path.exists(path), "observed_t5.json is missing")
        with io.open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual([c["id"] for c in data["cases"]], ["T008", "T022", "T031"])
        self.assertEqual(data["found_by"], "人の盲検確認(機械の混入ではない)")
        for c in data["cases"]:
            self.assertTrue(c["why_type5"].strip())

    def test_explicit_types_override_the_policy(self):
        chosen, _, _, _ = build(6, kind="xbrl", types=["T1_VALUE"])
        self.assertEqual({c["type"] for c in chosen}, {"T1_VALUE"})


class TestIdentification(unittest.TestCase):
    def test_a_reference_without_a_unit_cannot_identify_a_united_token(self):
        """Measured: "149百万円" was identified as an employee count of 149
        because that reference carried no unit."""
        text = "資金は 149 百万円 減少しました。\n"
        refs = [{"key": "emp", "label": "従業員数", "unit": None, "value": 149.0, "role": "value"}]
        self.assertEqual(S.identified_sites(text, refs), [])
        self.assertEqual(S.t5_sites(text, refs), [])

    def test_a_reference_in_the_same_unit_family_does_identify(self):
        """直し 2026-10-08(封 第 2 部)でこのフィクスチャの ``value`` を
        149.0 から 149000000.0 に変えた。149.0 のままだと、この試験自体が
        ``_matches``/``_value_index`` に倍率を掛ける前の欠陥(「149百万円」
        が素の 149 円に結ばれる)をそのまま固定してしまう ― ちょうど同じ
        数字が「149百万円の資金減少が従業員数149人に一致」の実例
        (INJECTION_TOOL_AUDIT3_RESULT_2026-10-08.md §1)として記録されて
        いる、避けるべきコインシデンスそのものだった。この試験の本来の
        主旨(ref が同じ族の明示的な単位を持てば identify される)は、
        倍率を正しく掛けた値どうしの一致で確かめても変わらない。"""
        text = "資金は 149 百万円 減少しました。\n"
        refs = [{"key": "cash", "label": "現金及び現金同等物", "unit": "円", "value": 149000000.0, "role": "value"}]
        got = S.identified_sites(text, refs)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0][1]["key"], "cash")

    def test_compound_amount_components_are_not_sites(self):
        text = "受注高は 394億1千9百万円 となりました。\n"
        refs = [{"key": "k%d" % v, "label": "何か", "unit": "円", "value": float(v), "role": "value"}
                for v in (394, 1, 9)]
        self.assertEqual(S.t1_sites(text, refs), [])
        self.assertEqual(S.t5_sites(text, refs), [])


class TestMoneyUnitIsQuantity(unittest.TestCase):
    """直し 2(2026-10-08 監査)。実物の書類に出る単位の表(parametrized)。

    欠陥: ``is_quantity()`` が「百万円」だけを乗数の例外にしていたため、
    和数字合成の「部品」(394億1千9百万円 の 1千)と、**単独の貨金量**
    (105,873千円 / 10億円 / 380億円)を区別できず、単独の量まで誤除外して
    いた(実測: S100Z4B6 の本文で「千円」「億円」を単位とする数 61 件が
    100% 誤除外)。ここは **実物の書類に現れる形**で固定する。
    """

    # (原文, 数字の文字列, 期待する unit, 量として扱われるべきか)
    REAL_WORLD_UNITS = [
        ("105,873千円の資金を調達した。", "105,873", "千円", True),
        ("10億円の資金調達を実施した。", "10", "億円", True),
        ("380億円の売上高となった。", "380", "億円", True),
        ("235百万円の利益となった。", "235", "百万円", True),
        ("1,234円の単価であった。", "1,234", "円", True),
        ("前期比 102.9% の実績であった。", "102.9", "%", True),
        ("発行済株式総数は 1,000株 である。", "1,000", None, True),
        ("従業員数は 149人 である。", "149", None, True),
    ]

    def test_units_in_real_document_shapes_are_quantities(self):
        for text, digits, unit, expected in self.REAL_WORLD_UNITS:
            t = N.normalize_digits(text)
            tok = next(x for x in N.scan(t) if x.text == digits)
            self.assertEqual(tok.unit, unit, "%r -> unit=%r (expected %r)" % (text, tok.unit, unit))
            self.assertEqual(N.is_quantity(t, tok), expected, "%r (%r)" % (text, digits))

    def test_compound_components_in_the_same_table_shape_are_not_quantities(self):
        """「394億1千9百万円」の部品(394 / 1 / 9)は、どれも上の表の金額の
        単位(億円・千円・百万円)を直後に持つが、量そのものではない。"""
        text = "受注高は394億1千9百万円となりました。"
        t = N.normalize_digits(text)
        for digits in ("394", "1", "9"):
            tok = next(x for x in N.scan(t) if x.text == digits)
            self.assertFalse(N.is_quantity(t, tok), "%r (%r) was taken as a standalone quantity" % (text, digits))


class TestMoneyScaleTable(unittest.TestCase):
    """直し 2026-10-08(封 第 2 部, DETECTION_T2_PLAN_2026-10-08.md 第 2 部)。

    欠陥: ``lib/sites.py`` の ``_matches()`` / ``_value_index()`` が、千円・
    百万円・億円という接尾辞の倍率を一切掛けずに、原文の数字リテラルと
    XBRL の生の値(素の円)を直接比べていた。実測(INJECTION_TOOL_AUDIT3_
    RESULT_2026-10-08.md §2): ``S100Z4B6`` で「短期貸付による支出
    50,000千円」(5千万円)が「その他の流動負債 50,000 円」に結ばれ、正しく
    結べる 29 件を落として誤って結んだ 1 件だけを採っていた。

    この表は ``lib/scales.py`` の倍率そのものを、実際の書類にある表現で
    固定する。倍率表は ``adapters/xbrl/vocabulary.py`` を写さず・読まず
    独立に書いた(測定が循環しないように)。

    必須の 9 行(人間の指示そのまま、DETECTION_T2_PLAN_2026-10-08.md 第 2
    部)のうち 5 行は material/xbrl/*.original.txt に実在する文字列である
    (grep で確認済み、行は下の注記に書く)。残り 4 行は人間が指示した代表
    例で、この 3 書類には実在しない(実在しないことも grep で確認済み ―
    「1兆円」「△」+金額単位の組はいずれも 0 件)。追加の行は自分で探し、
    実在を grep で確認したものだけを足す。
    """

    # (原文の数値+単位の表記, 期待する倍率を掛けた後の値, 出どころ)
    REQUIRED_ROWS = [
        # 人間の指示の 9 行(そのまま)。
        ("105,873千円", 105873000.0, "実在: S100Z4B6.original.txt:27 (親会社株主に帰属する当期純損失)"),
        ("235百万円", 235000000.0, "実在: S100YMFV.original.txt:49,243 (親会社株主に帰属する当期純利益)"),
        ("10億円", 1000000000.0, "実在: S100Z4B6.original.txt:15,237 (新株式発行による資金調達、約10億円)"),
        ("69.64円", 69.64, "実在: S100YMFV.original.txt:243 (1株当たり当期純利益)。unit=\"円\" のまま"
                            "(scale_of は money table に無いので no-op、69.64 は不変)"),
        ("50,000千円", 50000000.0, "実在: S100Z4B6.original.txt:97 (短期貸付による支出)"),
        ("2,281百万円", 2281000000.0,
         "人間の指示による代表例。この 3 書類には実在しない(grep で 0 件を確認済み)"),
        ("1兆円", 1000000000000.0,
         "人間の指示による代表例。この 3 書類に「兆円」は 0 件(grep で確認済み)"),
        ("△1,234千円", -1234000.0,
         "人間の指示による代表例。△ は会計の負号(-1,234,000 になる)。"
         "この 3 書類の MD&A 本文に △ は 4 件あるが、すべて % の値で金額には付かない"
         "(grep で確認済み ― S100Z4B6 の △4.8/△8.6、S100YMFV の △5.0/△1.5)"),
        ("1,475百万円", 1475000000.0,
         "人間の指示による代表例。この 3 書類には実在しない(grep で 0 件を確認済み)"),
    ]

    # 自分で探し、grep で実在を確認した追加の行(必須 9 行の外)。
    ADDITIONAL_REAL_ROWS = [
        ("1,850,502千円", 1850502000.0, "実在: S100Z4B6.original.txt:27,221 (売上高)"),
        ("35億円", 3500000000.0, "実在: S100Z4B6.original.txt:15,237 (新株予約権の行使による資金調達見込み)"),
        ("3億円", 300000000.0, "実在: S100Z4Q1.original.txt:15,23 (業務未払金の減少)"),
        ("8,294百万円", 8294000000.0, "実在: S100YMFV.original.txt:49,227 (売上高)"),
    ]

    _DIGITS_RE = re.compile(r"[0-9,]+(?:\.[0-9]+)?")

    def test_scale_table_rows(self):
        for digits, expected, why in self.REQUIRED_ROWS + self.ADDITIONAL_REAL_ROWS:
            text = N.normalize_digits("%sの額である。" % digits)
            signed = digits.startswith("△")
            digits_literal = self._DIGITS_RE.search(digits).group(0)
            tok = next(x for x in N.scan(text) if x.text == digits_literal)
            got = SC.signed_scaled_value(text, tok) if signed else SC.scaled_value(tok.value, tok.unit)
            self.assertEqual(got, expected, "%r (%s) -> %r (expected %r)" % (digits, why, got, expected))

    def test_negative_mark_flips_the_sign_only_when_it_immediately_precedes_the_digits(self):
        text = N.normalize_digits("前期は1,234千円であり、今期は△1,234千円であった。")
        toks = [t for t in N.scan(text) if t.text == "1,234"]
        self.assertEqual(len(toks), 2)
        positive, negative = toks
        self.assertFalse(SC.is_negative_mark(text, positive.start))
        self.assertTrue(SC.is_negative_mark(text, negative.start))
        self.assertEqual(SC.signed_scaled_value(text, positive), 1234000.0)
        self.assertEqual(SC.signed_scaled_value(text, negative), -1234000.0)

    def test_units_without_a_scale_pass_through_unchanged(self):
        """``scale_of`` は money table に無い単位(円/株・pure・shares・局・
        秒 など)に対して ``None`` を返し、``scaled_value`` は値をそのまま
        通す ― 掛け算の対象ではないことの固定。"""
        self.assertIsNone(SC.scale_of("円/株"))
        self.assertIsNone(SC.scale_of(None))
        self.assertIsNone(SC.scale_of("局"))
        self.assertEqual(SC.scaled_value(69.64, "円/株"), 69.64)
        self.assertEqual(SC.scaled_value(107.0, None), 107.0)

    def test_the_table_is_pinned_literally_not_derived(self):
        """人が決めた数は字で留める(2026-10-08 の人間の指示)。各行は独立
        した整数であり、他の行の掛け算から作られていないことを確かめる
        ― 1 行を壊す変異が他の行に伝播しないことの土台。"""
        self.assertEqual(SC.MONEY_SCALE["円"], 1)
        self.assertEqual(SC.MONEY_SCALE["千円"], 1000)
        self.assertEqual(SC.MONEY_SCALE["百万円"], 1000000)
        self.assertEqual(SC.MONEY_SCALE["億円"], 100000000)
        self.assertEqual(SC.MONEY_SCALE["兆円"], 1000000000000)


class TestCandidateFunctionsShareTheQuantityScreen(unittest.TestCase):
    """直し 1 の根は「候補関数のうち 1 つだけが is_quantity() を呼んでいな
    かった」こと。この試験は、将来 lib/sites.py に数字ベースの候補関数
    (``t<N>_sites`` という名前)が増えたときに、**それが is_quantity で
    screen される側か、screen しない理由を持つ側か**を人が明示的に分類
    するまで赤くするための歯止め。

    動的に呼び出すアプローチ(関数を足せば自動で対象に入る)は、
    t3_sites が ``(text, refs, kind)`` という別の署名を持ち、既存の数字
    トークンを走査しない(挿入する側)ため、一律の呼び出しができない。
    そこで「字で持つ一覧 + 一覧に無い候補関数が増えたら赤くなる」側を
    選んだ: 新しい ``t<N>_sites`` が増えると ``test_registry_is_complete``
    が真っ先に落ち、それを QUANTITY_SCREENED か NOT_QUANTITY_SCREENED の
    どちらかに人が追加するまで通らない。
    """

    # is_quantity() を直接呼び、既存の数字トークンを screen する候補関数。
    # どれも同じ signature (text, refs) -> list[dict] を持つ。
    QUANTITY_SCREENED = ("t1_sites", "t2_sites", "t5_sites")

    # 数字ベースの候補関数だが、理由があって is_quantity を呼ばない側。
    # t3_sites は原文の数字を一切読まない(主語も値も原文に無いことを確か
    # めてから新しい文を挿入するだけ)ので、quantity screen の対象外。
    NOT_QUANTITY_SCREENED = {
        "t3_sites": "原文の数字を走査しない(挿入のみ)",
    }

    def test_registry_is_complete(self):
        """lib/sites.py の t<N>_sites という名前の関数は、この 2 つの集合
        のどちらかに必ず入っていなければならない。増えたら最初にこれが
        落ちる。"""
        found = sorted(
            name for name, _ in inspect.getmembers(S, inspect.isfunction)
            if re.match(r"^t\d+_sites$", name)
        )
        known = sorted(set(self.QUANTITY_SCREENED) | set(self.NOT_QUANTITY_SCREENED))
        self.assertEqual(
            found, known,
            "lib/sites.py に新しい t<N>_sites が増えた(または減った)。"
            " QUANTITY_SCREENED か NOT_QUANTITY_SCREENED に分類してから"
            " この試験を直すこと。found=%s known=%s" % (found, known),
        )

    def test_every_screened_function_rejects_the_ordinal_offender(self):
        """「第2回」のような序数が、型 1・型 2・型 5 のどの候補にもならない
        ことを、個々の試験でなく一覧を回して確かめる(1 本足し忘れれば
        ここで検出できる)。"""
        text = "第三者割当による新株式発行及び第2回新株予約権の発行を決議した。"
        t = N.normalize_digits(text)
        tok = next(x for x in N.scan(t) if x.text == "2")
        refs = [{"key": "k%d" % i, "label": "何か", "unit": None, "value": float(v), "role": "value"}
                for i, v in enumerate([2, 3, 4, 5])]
        for name in self.QUANTITY_SCREENED:
            fn = getattr(S, name)
            starts = {s["token"].start for s in fn(t, refs)}
            self.assertNotIn(tok.start, starts, "%s() let the ordinal 第2回 through" % name)

    def test_the_registry_itself_is_not_empty(self):
        """空の一覧でも全部のループが自明に通るので、空にならないことを
        別に確かめる。"""
        self.assertGreaterEqual(len(self.QUANTITY_SCREENED), 1)
        for name in self.QUANTITY_SCREENED:
            self.assertTrue(hasattr(S, name), "%s is not defined in lib.sites" % name)


class TestT5UnitCompatibilityGuard(unittest.TestCase):
    """直し 4(2026-10-08 監査)。``t5_sites`` の ``others`` フィルタ内の
    ``_unit_compatible`` 呼び出し専用の試験。

    監査が当てた変異 M-D(この呼び出しを削除)は、監査の実行時点では 60 本
    全部緑で黙った ― 実物 4 文書では identified_sites が先に詰まって
    t5_sites の反復対象が 0 だったため。この試験は、単位が全く異なる
    「別の事実」が、桁の大きさ(magnitude)だけ近ければ借用されないことを、
    その呼び出しが無くても成立しうる他の条件(ラベル違い・桁の比・値の
    非一致)から独立に当てる。"""

    def test_a_magnitude_matching_fact_with_an_incompatible_unit_is_refused(self):
        text = "対局は 22 局ありました。\n"
        refs = [
            {"key": "a", "label": "対象", "unit": "局", "value": 22.0, "role": "value"},
            # 値は近い(比 1.14 倍、MAGNITUDE_RATIO=10 の範囲内)・ラベルも
            # 違う・値も不一致 ― _unit_compatible 以外の条件は全部満たす。
            {"key": "b", "label": "別の値", "unit": "秒", "value": 25.0, "role": "value"},
        ]
        self.assertEqual(S.t5_sites(text, refs), [], "unit が違う事実を借用した(秒 <- 局)")

    def test_the_same_fixture_with_a_compatible_unit_does_produce_a_site(self):
        """上と同じ値・ラベルの組で、unit だけ局に変えると型 5 が成立する
        ことを確かめる(フィクスチャそのものが退化していないことの確認)。"""
        text = "対局は 22 局ありました。\n"
        refs = [
            {"key": "a", "label": "対象", "unit": "局", "value": 22.0, "role": "value"},
            {"key": "b", "label": "別の値", "unit": "局", "value": 25.0, "role": "value"},
        ]
        self.assertEqual(len(S.t5_sites(text, refs)), 1)


class TestSeal(unittest.TestCase):
    def test_untracked_seed_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            p = os.path.join(d, "SEED.json")
            with io.open(p, "w") as fh:
                fh.write('{"seed": "x"}')
            with self.assertRaises(inject.SealError) as cm:
                inject.verify_seed_sealed(p)
            self.assertIn("not tracked", str(cm.exception))

    def test_modified_seed_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            p = os.path.join(d, "SEED.json")
            with io.open(p, "w") as fh:
                fh.write('{"seed": "x"}')
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
            subprocess.run(["git", "-C", d, "add", "SEED.json"], check=True)
            subprocess.run(["git", "-C", d, "commit", "-qm", "seal"], check=True, env=env)
            self.assertEqual(inject.verify_seed_sealed(p)[0], "x")
            with io.open(p, "w") as fh:
                fh.write('{"seed": "y"}')
            with self.assertRaises(inject.SealError) as cm:
                inject.verify_seed_sealed(p)
            self.assertIn("differs from its committed content", str(cm.exception))

    def test_seed_without_the_key_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", d], check=True)
            p = os.path.join(d, "SEED.json")
            with io.open(p, "w") as fh:
                fh.write('{"not_seed": 1}')
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
            subprocess.run(["git", "-C", d, "add", "SEED.json"], check=True)
            subprocess.run(["git", "-C", d, "commit", "-qm", "seal"], check=True, env=env)
            with self.assertRaises(inject.SealError):
                inject.verify_seed_sealed(p)


class TestHumanList(unittest.TestCase):
    def test_phrase_spans_address_the_phrase(self):
        for kind, text in (("shogi", TEXT),):
            for h in S.human_sites(text, kind):
                a, b = h["phrase_span"]
                self.assertEqual(text[a:b], h["phrase"])

    def test_a_list_tuned_to_one_kind_does_not_carry_over(self):
        """The booklet's populations (攻め / 自玉側) are invisible to the XBRL
        list. The first version of this test asserted the XBRL list finds
        *nothing* here, which was false: the fixture says 前期."""
        shogi = {h["phrase"] for h in S.human_sites(TEXT, "shogi")}
        xbrl = {h["phrase"] for h in S.human_sites(TEXT, "xbrl")}
        self.assertIn("攻め", shogi)
        self.assertNotIn("攻め", xbrl)
        self.assertEqual(shogi & xbrl, set())


class TestExternalCustomerMaterial(unittest.TestCase):
    """2026-10-08 司令塔の判断: 将棋の冊子と packet は顧客のデータなので、
    混入の記録と同じ考え方でリポジトリの外(``~/.audit-core-measure/material/``)
    に置く。人間が名指ししたのは packet だけだが、冊子は顧客の診断報告の
    本文そのものなので同じ理由が当たるとして拡張した。"""

    def test_defaults_point_outside_the_repository(self):
        home = os.path.expanduser("~")
        for path in (prepare_material.DEFAULT_SHOGI_BOOKLET, prepare_material.DEFAULT_SHOGI_PACKET):
            self.assertTrue(path.startswith(home), path)
            self.assertNotIn(MEASURE, path, "%s still points inside the repo" % path)

    def test_missing_material_raises_rather_than_being_skipped(self):
        """材料が無ければ落ちる(skip にしない)。"""
        args = argparse.Namespace(
            booklet="/nonexistent-for-test/booklet.md",
            packet="/nonexistent-for-test/packet.json",
            doc="x",
        )
        with tempfile.TemporaryDirectory() as tmp:
            args.out = tmp
            with self.assertRaises((IOError, OSError)):
                prepare_material.prepare_shogi(args)

    def test_source_sha256_matches_the_committed_record(self):
        """材料そのものはリポジトリに無いので、この試験は sha256 の記録が
        壊れていないことだけを確かめる(実物との一致は確認方法が
        README/SOURCE.sha256 の先頭コメントに書いてある手順で、
        人が手で行う ― 実物がこの環境に無い CI では検査できない)。"""
        path = os.path.join(MEASURE, "material", "shogi", "SOURCE.sha256")
        with io.open(path, encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip() and not ln.startswith("#")]
        self.assertEqual(len(lines), 2)
        for ln in lines:
            sha, _, name = ln.partition("  ")
            self.assertEqual(len(sha), 64, ln)
            self.assertIn(name, ("c5_observation_packet.json", "c5_round5_booklet.md"))


def _make_xbrl_zip(path, instance_name, instance_body, extra_entries=None):
    """Build a minimal EDINET-shaped ZIP for :func:`prepare_material.prepare_xbrl`.

    ``instance_name`` must satisfy the same selection rule the production
    code uses (``n.endswith(".xbrl") and "PublicDoc" in n``).
    """
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(instance_name, instance_body)
        for name, body in (extra_entries or {}).items():
            z.writestr(name, body)


# A text block is required before prepare_xbrl ever looks at the numeric
# elements (it raises SystemExit first if none is found), so every fixture
# below carries one.
_MDNA_BLOCK = (
    '<jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock '
    'contextRef="CurrentYearDuration"><p>テスト本文</p>'
    '</jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock>'
)


def _instance(numeric_tags):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" '
        'xmlns:jpcrp_cor="http://disclosure.edinet-fsa.go.jp/jpcrp_cor">\n'
        + _MDNA_BLOCK + "\n" + "\n".join(numeric_tags) + "\n"
        "</xbrli:xbrl>\n"
    )


class TestXBRLUnitRefExtraction(unittest.TestCase):
    """直し 1(2026-10-08 監査の 3 回目の REVISE)。

    欠陥: ``contextRef`` と ``unitRef`` を 1 本の正規表現で、間を greedy な
    ``[^>]*`` で埋めて同時に取ろうとしていた。``unitRef`` 側の群が
    optional だったため、先行する greedy な ``[^>]*`` がタグの残り全部
    (``unitRef`` を含む)を食べてから、オプション群は「空のまま」で
    成立してしまい、**実在する unitRef が一度も捕捉されなかった**
    (実測: 3 文書 824/922/994 件、100% が ``unit=None``)。

    直し: 開始タグの属性文字列を 1 回だけ捕捉し(``XBRLI_TAG_RE`` の群 2)、
    ``contextRef=``・``unitRef=`` をその文字列の中でそれぞれ個別に
    ``re.search`` する。
    """

    def test_unit_ref_is_captured_when_an_attribute_sits_between(self):
        """監査が指摘した最小例そのもの ― contextRef と unitRef の間に
        decimals が挟まる実在のタグの形。"""
        tag = (
            '<jpcrp_cor:NetSalesSummaryOfBusinessResults contextRef="Prior4YearDuration" '
            'decimals="-3" unitRef="JPY">6379051000</jpcrp_cor:NetSalesSummaryOfBusinessResults>'
        )
        m = next(prepare_material.XBRLI_TAG_RE.finditer(tag))
        attrs = m.group(2)
        cm = prepare_material._CONTEXTREF_ATTR_RE.search(attrs)
        um = prepare_material._UNITREF_ATTR_RE.search(attrs)
        self.assertIsNotNone(cm, "contextRef was not captured")
        self.assertEqual(cm.group(1), "Prior4YearDuration")
        self.assertIsNotNone(um, "unitRef was not captured (this is the bug the audit found)")
        self.assertEqual(um.group(1), "JPY")

    def test_production_path_through_prepare_xbrl_populates_unit(self):
        """regex の単体確認だけでなく、``prepare_xbrl`` 自体を実行し、
        書き出された参照用の数の一覧に ``unit`` が入ることを確かめる。"""
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "sample.zip")
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/sample.xbrl",
                _instance([
                    '<jpcrp_cor:NetSalesSummaryOfBusinessResults contextRef="CurrentYearDuration" '
                    'decimals="-3" unitRef="JPY">6379051000</jpcrp_cor:NetSalesSummaryOfBusinessResults>'
                ]),
            )
            args = argparse.Namespace(zip=zpath, doc="sample", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "sample.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            matches = [r for r in refs if r["source_key"] == "NetSalesSummaryOfBusinessResults"]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["unit"], "円", "unitRef=JPY must become 円 (bug: stayed None)")

    def test_degenerate_no_unit_ref_attribute_at_all(self):
        tag = '<x:Y contextRef="C" decimals="0">1</x:Y>'
        m = next(prepare_material.XBRLI_TAG_RE.finditer(tag))
        self.assertIsNone(prepare_material._UNITREF_ATTR_RE.search(m.group(2)))

    def test_degenerate_empty_unit_ref_value(self):
        tag = '<x:Y contextRef="C" unitRef="">1</x:Y>'
        m = next(prepare_material.XBRLI_TAG_RE.finditer(tag))
        # unitRef="" has no characters inside the quotes, so the attribute
        # regex (which requires at least one) does not match -- treated the
        # same as "no unit", not as an empty-string unit.
        self.assertIsNone(prepare_material._UNITREF_ATTR_RE.search(m.group(2)))

    def test_degenerate_five_or_more_attributes_unit_ref_last(self):
        tag = (
            '<x:Y contextRef="C" decimals="-3" sign="-" scale="0" '
            'id="z1" unitRef="JPY">123</x:Y>'
        )
        m = next(prepare_material.XBRLI_TAG_RE.finditer(tag))
        um = prepare_material._UNITREF_ATTR_RE.search(m.group(2))
        self.assertIsNotNone(um)
        self.assertEqual(um.group(1), "JPY")

    def test_degenerate_unit_ref_before_context_ref(self):
        """属性の並び順が実物と逆でも両方取れる(順序に依存しない設計)。"""
        tag = '<x:Y unitRef="JPY" decimals="-3" contextRef="C">123</x:Y>'
        m = next(prepare_material.XBRLI_TAG_RE.finditer(tag))
        attrs = m.group(2)
        self.assertEqual(prepare_material._CONTEXTREF_ATTR_RE.search(attrs).group(1), "C")
        self.assertEqual(prepare_material._UNITREF_ATTR_RE.search(attrs).group(1), "JPY")

    def test_degenerate_tag_without_context_ref_is_not_a_fact(self):
        """contextRef を持たないタグは参照にならない(数値を持っていても
        スキップされる ― prepare_xbrl のループが ``continue`` する)。"""
        tag = '<x:Y unitRef="JPY" decimals="-3">123</x:Y>'
        m = next(prepare_material.XBRLI_TAG_RE.finditer(tag))
        self.assertIsNone(prepare_material._CONTEXTREF_ATTR_RE.search(m.group(2)))

    def test_degenerate_duplicate_context_ref_keeps_first_seen(self):
        """同じ要素・同じ contextRef が 2 回現れても、既存の重複排除
        (``seen`` set)がそのまま働く ― 直し 1 で変えていない挙動。"""
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "dup.zip")
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/dup.xbrl",
                _instance([
                    '<x:Y contextRef="C" unitRef="JPY">100</x:Y>',
                    '<x:Y contextRef="C" unitRef="JPY">200</x:Y>',
                ]),
            )
            args = argparse.Namespace(zip=zpath, doc="dup", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "dup.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            ys = [r for r in refs if r["source_key"] == "Y"]
            self.assertEqual(len(ys), 1, "duplicate contextRef must not produce two refs")
            self.assertEqual(ys[0]["value"], 100.0)

    def test_mutation_hunt_same_element_different_contexts_both_survive(self):
        """自分で当てた変異 M2(2026-10-08)の回帰試験。``key`` から
        ``ctx`` を落とす変異(``"%s@%s" % (elem, ctx)`` を ``elem`` だけに
        する)は、単体試験 84 本では**黙った**(実物の書類で毎年同じ要素名
        を違う ``contextRef`` で繰り返す形 ― 当期・前期 ― が既存の試験
        材料に無かったため)。実物に近い「同じ要素・違う文脈が複数ある」
        形を材料にして閉じる。"""
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "years.zip")
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/years.xbrl",
                _instance([
                    '<x:NetSales contextRef="CurrentYearDuration" unitRef="JPY">100</x:NetSales>',
                    '<x:NetSales contextRef="Prior1YearDuration" unitRef="JPY">90</x:NetSales>',
                    '<x:NetSales contextRef="Prior2YearDuration" unitRef="JPY">80</x:NetSales>',
                ]),
            )
            args = argparse.Namespace(zip=zpath, doc="years", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "years.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            sales = [r for r in refs if r["source_key"] == "NetSales"]
            self.assertEqual(len(sales), 3, "different contexts of the same element must not collapse")
            self.assertEqual(sorted(r["value"] for r in sales), [80.0, 90.0, 100.0])

    def test_mutation_hunt_tag_without_context_ref_never_becomes_a_ref(self):
        """自分で当てた変異 M3(2026-10-08)の回帰試験。``if cm is None:
        continue`` を外す変異(欠けた contextRef を ``None`` のまま通す)
        は、単体試験 84 本では**黙った**(どの既存試験も
        ``prepare_xbrl`` の出力を「contextRef の無いタグが 1 件も無い」
        という形で確かめていなかったため)。全件を舐めて確かめる。"""
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "nocref.zip")
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/nocref.xbrl",
                _instance([
                    '<x:Orphan unitRef="JPY" decimals="0">999</x:Orphan>',
                    '<x:WithContext contextRef="C" unitRef="JPY">1</x:WithContext>',
                ]),
            )
            args = argparse.Namespace(zip=zpath, doc="nocref", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "nocref.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            self.assertEqual([r["source_key"] for r in refs], ["WithContext"])
            self.assertNotIn("Orphan", [r["source_key"] for r in refs])

    def test_mutation_hunt_missing_unit_stays_none_not_empty_string(self):
        """自分で当てた変異 M6(2026-10-08)の回帰試験。``unit = um.group(1)
        if um else None`` を ``else ""`` にする変異は、単体試験 84 本では
        **黙った**(既存試験は ``is None`` ではなく ``assertIsNone`` を
        regex の群に対してしか当てていなかったため、``prepare_xbrl`` の
        出力 JSON まで降りて ``unit`` の値そのものの型を確かめていなかっ
        た)。``""`` と ``None`` は ``lib/sites.py`` の ``_unit_compatible``
        で扱いが違う(``None`` は両立・``""`` は非両立になりうる)ので、
        ここで型まで固定する。"""
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "nounit.zip")
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/nounit.xbrl",
                _instance(['<x:NoUnit contextRef="C" decimals="0">5</x:NoUnit>']),
            )
            args = argparse.Namespace(zip=zpath, doc="nounit", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "nounit.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            matches = [r for r in refs if r["source_key"] == "NoUnit"]
            self.assertEqual(len(matches), 1)
            self.assertIsNone(matches[0]["unit"], "missing unitRef must serialise as null, not an empty string")

    def test_mutation_hunt_jpy_unit_mapping_is_case_insensitive(self):
        """自分で当てた変異 M7(2026-10-08)の回帰試験。``(unit or
        "").upper().startswith("JPY")`` から ``.upper()`` を外す変異は、
        単体試験 84 本では**黙った**(既存試験の ``unitRef`` はすべて
        大文字 ``"JPY"`` で書かれていたため、小文字化した入力を試す試験
        が無かった)。実在する ``unitRef`` は大文字の ``JPY`` だが、
        表記違いを汲み取れることを明示的に固定する。"""
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "lowercase.zip")
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/lowercase.xbrl",
                _instance(['<x:Y contextRef="C" unitRef="jpy">5</x:Y>']),
            )
            args = argparse.Namespace(zip=zpath, doc="lowercase", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "lowercase.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            ys = [r for r in refs if r["source_key"] == "Y"]
            self.assertEqual(ys[0]["unit"], "円")


class TestPerShareUnitIsSeparateFromMoney(unittest.TestCase):
    """直し 2026-10-08(封 第 2 部, 司令塔の追加)。``prepare_material.py``
    の ``"円" if (unit or "").upper().startswith("JPY") else ...`` は、
    実在する ``unitRef="JPYPerShares"``(1 株当たりの金額)も「円」に丸めて
    いた(実測: 3 書類に 41/40/41 件)。これをやらないと、倍率を掛けた
    「総額」のトークンが、別の事実である「1 株当たり」の参照に ``money``
    族の一致で結びうる。``JPYPerShares`` は ``JPY`` とは異なる文字列
    (``円/株``)にし、``lib/numbers.py`` の ``UNIT_FAMILIES`` には登録しない
    ことで、``unit_family("円/株")`` が ``None`` になり、``money`` 族の
    どの金額とも家族が一致しないようにする。"""

    def test_jpy_per_shares_becomes_a_distinct_label_not_yen(self):
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "pershare.zip")
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/pershare.xbrl",
                _instance([
                    '<x:EPS contextRef="C" unitRef="JPYPerShares">69.64</x:EPS>',
                    '<x:NetSales contextRef="C" unitRef="JPY">6379051000</x:NetSales>',
                ]),
            )
            args = argparse.Namespace(zip=zpath, doc="pershare", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "pershare.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            eps = next(r for r in refs if r["source_key"] == "EPS")
            sales = next(r for r in refs if r["source_key"] == "NetSales")
            self.assertEqual(eps["unit"], prepare_material.PER_SHARE_UNIT_LABEL)
            self.assertNotEqual(eps["unit"], "円")
            self.assertEqual(sales["unit"], "円")

    def test_the_distinct_label_does_not_share_a_family_with_money(self):
        """``円/株`` は ``lib/numbers.py`` の ``money`` family に登録され
        ていないので、``unit_family`` は ``None`` を返し、どの金額の単位
        とも家族が一致しない。"""
        self.assertIsNone(N.unit_family(prepare_material.PER_SHARE_UNIT_LABEL))
        for money_unit in N.UNIT_FAMILIES["money"]:
            self.assertNotEqual(N.unit_family(money_unit), N.unit_family(prepare_material.PER_SHARE_UNIT_LABEL))

    def test_a_plain_yen_token_does_not_identify_against_a_per_share_reference(self):
        """「69.64円」(1 株当たりの表現が平文の「円」で書かれた文)は、真の
        参照の単位が ``円/株`` に分かれたことで、明示的な単位どうしの家族
        一致を要求する ``identified_sites`` からは外れる(S-6 の実測の
        固定 ― 69.64 の identify は消え、別の「400百万円」が新たに
        identify された。STEP 報告の表に詳細)。"""
        text = "1株当たり当期純利益は69.64円となりました。\n"
        refs = [{
            "key": "eps@C", "source_key": "EPS",
            "label": "EPS", "unit": prepare_material.PER_SHARE_UNIT_LABEL,
            "value": 69.64, "role": "value",
        }]
        self.assertEqual(S.identified_sites(text, refs), [])
        self.assertEqual(S.data_bearing_sites(text, refs), [])

    def test_scale_applies_before_the_family_check_so_identification_resolves_the_total(self):
        """倍率を掛けたうえで家族も一致するとき(総額どうし)は identify
        される ― 「50,000千円」が 50,000,000 円の参照に結ばれる実物の形。"""
        text = "短期貸付による支出50,000千円によるものであります。\n"
        refs = [{
            "key": "loan@C", "source_key": "ShortTermLoansReceivable",
            "label": "短期貸付金", "unit": "円", "value": 50000000.0, "role": "value",
        }]
        got = S.identified_sites(text, refs)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0][1]["key"], "loan@C")


class TestXBRLInlineVsPlainInstance(unittest.TestCase):
    """人間の追加指示 1(2026-10-08): ``decimals`` と ``scale`` は別物。
    ``decimals`` は精度の情報で値そのものに掛け算は要らない。インライン
    XBRL の ``ix:nonFraction scale="N"`` は 10**N を掛ける必要がある
    (``adapters/xbrl/instance.py`` の ``else`` 分岐が行っている ―
    参考として読んだだけで import も真似た実装もしていない)。

    ``prepare_material.prepare_xbrl`` は ``n.endswith(".xbrl") and
    "PublicDoc" in n`` で候補を選ぶため、**インラインの
    ``*_ixbrl.htm`` を読む経路は存在しない。** 実物の 3 書類(手元の
    ``~/.cache/audit-core/edinet/*.zip``)を確認した: いずれも
    ``XBRL/PublicDoc/*.xbrl``(通常の instance)を持ち、その中に
    ``scale=`` は **0 件**(S100YMFV/S100Z4B6/S100Z4Q1 とも)。
    したがって ``scale`` はこの階層では効かない経路であり、直すのでは
    なく「効かないこと」を試験で固定する。
    """

    def test_plain_instance_is_selected_over_inline_htm_when_both_exist(self):
        """実物の ZIP は ``*_ixbrl.htm`` と ``.xbrl`` の両方を含む。選択規則
        (``endswith(".xbrl") and "PublicDoc" in n``)が常に通常の instance
        を選ぶことを、両方を含む ZIP で確かめる。"""
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "both.zip")
            inline_htm = (
                '<html><body><ix:nonFraction contextRef="C" unitRef="JPY" scale="3" '
                'name="x:Y">6379051</ix:nonFraction></body></html>'
            )
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/both.xbrl",
                _instance(['<x:Y contextRef="C" unitRef="JPY">6379051000</x:Y>']),
                extra_entries={
                    "XBRL/PublicDoc/0101010_honbun_both_ixbrl.htm": inline_htm,
                },
            )
            with zipfile.ZipFile(zpath) as z:
                names = z.namelist()
                inst = [n for n in names if n.endswith(".xbrl") and "PublicDoc" in n]
            self.assertEqual(inst, ["XBRL/PublicDoc/both.xbrl"])
            args = argparse.Namespace(zip=zpath, doc="both", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "both.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            ys = [r for r in refs if r["source_key"] == "Y"]
            self.assertEqual(len(ys), 1)
            # The value read is the plain instance's raw value (6379051000),
            # never the inline fragment's smaller, scale=3 value (6379051).
            self.assertEqual(ys[0]["value"], 6379051000.0)

    def test_scale_attribute_is_not_consulted_in_this_extraction_path(self):
        """退化値: 本来この経路には現れない ``scale`` 属性が紛れ込んでも、
        掛け算は行われない(効かないことを固定する)。将来この階層が
        インラインの ``*_ixbrl.htm`` を読むようになったら、ここが赤く
        なって知らせる。"""
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "scale.zip")
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/scale.xbrl",
                _instance([
                    '<x:Y contextRef="C" unitRef="JPY" scale="3">6379051</x:Y>',
                ]),
            )
            args = argparse.Namespace(zip=zpath, doc="scale", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "scale.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            ys = [r for r in refs if r["source_key"] == "Y"]
            self.assertEqual(len(ys), 1)
            self.assertEqual(
                ys[0]["value"], 6379051.0,
                "scale was applied (10**3 multiplication) in a path that must not consult it",
            )

    def test_degenerate_negative_scale_is_also_not_consulted(self):
        with tempfile.TemporaryDirectory() as tmp:
            zpath = os.path.join(tmp, "negscale.zip")
            _make_xbrl_zip(
                zpath,
                "XBRL/PublicDoc/negscale.xbrl",
                _instance([
                    '<x:Y contextRef="C" unitRef="JPY" scale="-2">6379051</x:Y>',
                ]),
            )
            args = argparse.Namespace(zip=zpath, doc="negscale", out=tmp)
            prepare_material.prepare_xbrl(args)
            with io.open(os.path.join(tmp, "negscale.reference_numbers.json"), encoding="utf-8") as fh:
                refs = json.load(fh)["refs"]
            ys = [r for r in refs if r["source_key"] == "Y"]
            self.assertEqual(ys[0]["value"], 6379051.0)

    def test_real_cached_documents_carry_no_scale_attribute(self):
        """実物の 3 書類(手元のキャッシュ)を確認: いずれも通常の instance
        を持ち、``scale=`` は 0 件。キャッシュが無い環境では skip する
        (材料は顧客データと同じ理由でリポジトリに無いので、CI では
        測れないことをここに明記する ― ``test_source_sha256_matches_the_
        committed_record`` と同じ扱い)。"""
        cache = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
        docs = {
            "S100YMFV": "jpcrp030000-asr-001_E31344-000_2026-06-30_01_2026-09-28.xbrl",
            "S100Z4B6": "jpcrp030000-asr-001_E05055-000_2026-06-30_01_2026-09-29.xbrl",
            "S100Z4Q1": "jpcrp030000-asr-001_E36539-000_2026-06-30_01_2026-09-30.xbrl",
        }
        found_any = False
        for doc, inst_basename in docs.items():
            zpath = os.path.join(cache, "%s.zip" % doc)
            if not os.path.exists(zpath):
                continue
            found_any = True
            with zipfile.ZipFile(zpath) as z:
                inst = [n for n in z.namelist() if n.endswith(".xbrl") and "PublicDoc" in n]
                self.assertEqual(len(inst), 1, doc)
                raw = z.read(inst[0]).decode("utf-8", "replace")
            self.assertEqual(raw.count("scale="), 0, "%s unexpectedly carries scale=" % doc)
        if not found_any:
            self.skipTest("~/.cache/audit-core/edinet/*.zip not present in this environment")


if __name__ == "__main__":
    unittest.main(verbosity=2)
