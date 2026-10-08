# -*- coding: utf-8 -*-
"""``fixtures/xbrl/tamper_insert.py``・``run_detection_t3.py``(型 3)の
単体試験。合成の小さな ZIP だけを使う。封
``audit-core/docs/DETECTION_T1_T3_PLAN_2026-10-08.md`` 第 3 部が要求する
最低限の点(挿入位置は句点の直後・タグの内側に入らない・実在する主語は
使わない・「主張にならなかった」は検出に数えない・不変条件が破れたら記録
される・同定は値だけで行わない)をカバーする。
"""

import io
import os
import sys
import unittest
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_FIXTURES_XBRL = os.path.join(_AUDIT_CORE, "fixtures", "xbrl")
if _FIXTURES_XBRL not in sys.path:
    sys.path.insert(0, _FIXTURES_XBRL)

import tamper_insert as TI  # noqa: E402
import run_detection_t3 as D3  # noqa: E402


_MDNA_LOCAL = "ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock"


def make_zip(mdna_text, extra_files=None, local_name=_MDNA_LOCAL):
    """最小の合成 ZIP。``tests/fixtures/xbrl/test_tamper_unit.py: make_zip``
    と同じ形(重複して持つ -- 同ファイルの docstring と同じ理由)。"""

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" '
        'xmlns:jpcrp_cor="http://example.com/jpcrp_cor">\n'
        '<jpcrp_cor:%s contextRef="Ctx0">%s</jpcrp_cor:%s>\n'
        '</xbrli:xbrl>\n'
        % (local_name, mdna_text, local_name)
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("XBRL/PublicDoc/test-001_2026-01-01.xbrl", xml.encode("utf-8"))
        for name, data in (extra_files or {}).items():
            z.writestr(name, data)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 9. 挿入位置は句点の直後に限る。タグの内側に入らない
# ---------------------------------------------------------------------------

class InsertionPointTest(unittest.TestCase):
    def test_points_are_immediately_after_a_period_outside_any_tag(self):
        inner = "本文です。中の文です。末尾です。"
        points = TI.find_insertion_points(inner)
        # 先頭・末尾を除く(lib.sites.t3_sites と同じ方針)ので、句点 3 つ
        # なら候補は中央の 1 つだけ。
        self.assertEqual(len(points), 1)
        pos = points[0]
        self.assertEqual(inner[pos - 1], "。")

    def test_period_inside_a_tag_markup_is_not_a_candidate(self):
        # タグの markup そのものの内側(属性値)に句点がある合成 ―
        # 「タグの内側」は要素の内容(<span>。</span> の「。」)ではなく、
        # "<" と ">" の間(属性値など)を指す。中の文に挟まれた、その
        # 属性値の句点は候補になってはいけない。
        inner = '先頭の文。<a title="x。y">中の文。末尾の文。'
        points = TI.find_insertion_points(inner)
        attr_period_pos = inner.index("x。y") + len("x")  # 「。」の直後の位置
        self.assertNotIn(attr_period_pos, points)
        for pos in points:
            self.assertEqual(inner[pos - 1], "。")

    def test_period_in_element_content_between_tags_is_a_candidate(self):
        # <span>。</span> の「。」は要素の内容(タグの markup の外)なので、
        # 除外されない ― 「タグの内側」を「要素の内側」と取り違えていない
        # ことの回帰。
        inner = "先頭の文。<span>中の文。</span>別の文。末尾の文。"
        points = TI.find_insertion_points(inner)
        span_period_pos = inner.index("中の文。") + len("中の文。")
        self.assertIn(span_period_pos, points)

    def test_first_and_last_boundary_are_excluded(self):
        inner = "。中の文。末尾。"
        points = TI.find_insertion_points(inner)
        self.assertNotIn(1, points)  # 先頭の「。」の直後
        self.assertNotIn(len(inner), points)  # 末尾の「。」の直後

    def test_too_few_periods_yields_no_points(self):
        self.assertEqual(TI.find_insertion_points("句点が 1 つ。"), [])
        self.assertEqual(TI.find_insertion_points("句点が無い"), [])


# ---------------------------------------------------------------------------
# 10. 実在する主語は使わない
# ---------------------------------------------------------------------------

class SubjectAbsenceTest(unittest.TestCase):
    def test_subject_present_in_text_is_withheld(self):
        text = "最初の文です。当期の海外関連会社売上高は好調でした。最後の文です。"
        refs = [{"label": "何か", "value": 1.0}]
        templates = TI.usable_templates(text, refs, "xbrl")
        subjects = [s for s, _t in templates]
        self.assertNotIn("海外関連会社売上高", subjects)
        self.assertEqual(len(subjects), 5)  # 6 主語のうち 1 つだけ落ちる

    def test_subject_present_in_reference_label_is_withheld(self):
        text = "最初の文です。本文には出てこない中身です。最後の文です。"
        refs = [{"label": "研究開発受託収益", "value": 1.0}]
        templates = TI.usable_templates(text, refs, "xbrl")
        subjects = [s for s, _t in templates]
        self.assertNotIn("研究開発受託収益", subjects)
        self.assertEqual(len(subjects), 5)

    def test_subject_absent_from_both_is_offered(self):
        # t3_sites のアンカー(先頭・末尾を除く句点区切り)が最低 1 つ要る
        # ので、3 文以上にする(1 文だけでは候補が無く [] に落ちる)。
        text = "最初の文です。本文には出てこない中身です。最後の文です。"
        refs = [{"label": "何か別のもの", "value": 1.0}]
        templates = TI.usable_templates(text, refs, "xbrl")
        subjects = [s for s, _t in templates]
        self.assertEqual(len(subjects), 6)

    def test_degenerate_all_six_subjects_present_yields_no_templates(self):
        # 退化値: 6 主語が全部本文に実在する -> 使える主語 0(build_sentence
        # を呼べば None が返るはずの入口)。
        all_six = [subj for subj, _tpl in TI.S.ABSENT_TEMPLATES["xbrl"]]
        text = "最初の文です。" + "、".join(all_six) + "が全部出てくる文です。最後の文です。"
        refs = []
        templates = TI.usable_templates(text, refs, "xbrl")
        self.assertEqual(templates, [])

    def test_degenerate_no_eligible_site_in_run_detection_t1_pool(self):
        # 退化値: gate_c を通る現場が 0 件でも build_layer_summary が落ちない
        # (すべての層が n=0 の率を返す ― T2._rate_block の n==0 分岐)。
        import run_detection_t1 as D1
        shortfall = {k: 6 for k in D1.LAYERS + [D1.LAYER_APRIME]}
        excluded = {D1.LAYER_APRIME: {"cannot_build": 0, "collides_with_reference": 0}}
        empty_rows = {layer: [] for layer in D1.LAYERS + [D1.LAYER_APRIME]}
        summary = D1.build_layer_summary(empty_rows, shortfall, excluded)
        for layer in D1.LAYERS:
            self.assertEqual(summary["layer_rates"][layer]["drawn"], 0)
            self.assertIsNone(summary["layer_rates"][layer]["rates"]["conditional_on_traceable_before_mixing"]["rate"])
        self.assertEqual(summary["aprime_box"]["drawn"], 0)


# ---------------------------------------------------------------------------
# 11. 「主張にならなかった」は検出に数えられない(= 止めなかった側)
# ---------------------------------------------------------------------------

class NotClaimedIsNotDetectedTest(unittest.TestCase):
    def test_zero_candidates_means_not_claimed_not_detected(self):
        became_claim, identified, preexisting, ids = D3.identify_inserted_claim(
            new_num_sites=[], baseline_digits_set=set(), value_text="128", unit="百万円"
        )
        self.assertFalse(became_claim)
        self.assertIsNone(identified)
        self.assertFalse(preexisting)
        self.assertEqual(ids, set())
        # became_claim is False の行は、run_detection_t3.py の集計で
        # not_claimed_total に入り、became_claim_total には入らない
        # (main() の集計ロジックと同じ条件分岐をここでも確かめる)。
        rows = [{"became_claim": became_claim}]
        self.assertEqual(sum(1 for r in rows if r["became_claim"] is False), 1)
        self.assertEqual(sum(1 for r in rows if r["became_claim"] is True), 0)


# ---------------------------------------------------------------------------
# 12. 他の主張の状態が変わったら不変条件が破れたと記録される(合成で破る)
# ---------------------------------------------------------------------------

class InvariantViolationTest(unittest.TestCase):
    def test_unrelated_claim_state_change_is_caught(self):
        baseline_rows = [
            {"id": "N001", "unit": "円", "state": "GROUNDED", "recomputed": 1.0, "reason": None},
            {"id": "N002", "unit": "円", "state": "GROUNDED", "recomputed": 2.0, "reason": None},
        ]
        # 挿入で N003 が新しく増えたふりをして、かつ N002 が壊れている
        # (合成: VALUE_MISMATCH に変わった)。
        new_rows = [
            {"id": "N001", "unit": "円", "state": "GROUNDED", "recomputed": 1.0, "reason": None},
            {"id": "N002", "unit": "円", "state": "VALUE_MISMATCH", "recomputed": 2.0, "reason": "broken"},
            {"id": "N003", "unit": "百万円", "state": "POINTER_NOT_FOUND", "recomputed": None, "reason": "x"},
        ]
        ok, mismatch = D3.check_other_claims_unchanged(baseline_rows, new_rows, inserted_ids={"N003"})
        self.assertFalse(ok)
        self.assertIsNotNone(mismatch)
        self.assertEqual(mismatch["index"], 1)

    def test_truly_unrelated_insertion_passes(self):
        baseline_rows = [
            {"id": "N001", "unit": "円", "state": "GROUNDED", "recomputed": 1.0, "reason": None},
            {"id": "N002", "unit": "円", "state": "GROUNDED", "recomputed": 2.0, "reason": None},
        ]
        new_rows = [
            {"id": "N001", "unit": "円", "state": "GROUNDED", "recomputed": 1.0, "reason": None},
            {"id": "N002", "unit": "円", "state": "GROUNDED", "recomputed": 2.0, "reason": None},
            {"id": "N003", "unit": "百万円", "state": "POINTER_NOT_FOUND", "recomputed": None, "reason": "x"},
        ]
        ok, mismatch = D3.check_other_claims_unchanged(baseline_rows, new_rows, inserted_ids={"N003"})
        self.assertTrue(ok)
        self.assertIsNone(mismatch)


# ---------------------------------------------------------------------------
# 13. 挿入した文の同定は値だけで行われていない
# ---------------------------------------------------------------------------

class IdentificationNotByValueAloneTest(unittest.TestCase):
    def test_preexisting_identical_digits_is_marked_unidentified_not_claimed(self):
        # 挿入した値(128百万円)が、基準線にも既に「128百万円」という
        # digits で在る合成入力(値が偶然同じ既存の主張)。
        baseline_digits_set = {("128百万円", "百万円"), ("999百万円", "百万円")}
        new_num_sites = [
            {"id": "N010", "digits": "128百万円", "unit": "円"},
            {"id": "N050", "digits": "128百万円", "unit": "円"},  # 挿入した方(同じ digits)
        ]
        became_claim, identified, preexisting, ids = D3.identify_inserted_claim(
            new_num_sites, baseline_digits_set, "128", "百万円"
        )
        self.assertIsNone(became_claim)  # 同定できない(検出にも未検出にも数えない)
        self.assertFalse(identified)
        self.assertTrue(preexisting)
        self.assertEqual(ids, set())

    def test_value_absent_from_baseline_is_identified_as_inserted(self):
        baseline_digits_set = {("999百万円", "百万円")}
        new_num_sites = [{"id": "N050", "digits": "128百万円", "unit": "円"}]
        became_claim, identified, preexisting, ids = D3.identify_inserted_claim(
            new_num_sites, baseline_digits_set, "128", "百万円"
        )
        self.assertTrue(became_claim)
        self.assertTrue(identified)
        self.assertFalse(preexisting)
        self.assertEqual(ids, {"N050"})

    def test_two_claims_matching_the_inserted_value_are_both_counted(self):
        # F-5(挿入した文が 2 つ以上の主張になる)の形。値だけで同定する際、
        # 候補が複数でも(基準線に無ければ)両方「挿入した側」として数える。
        baseline_digits_set = set()
        new_num_sites = [
            {"id": "N050", "digits": "128百万円", "unit": "円"},
            {"id": "N051", "digits": "128百万円", "unit": "円"},
        ]
        became_claim, identified, preexisting, ids = D3.identify_inserted_claim(
            new_num_sites, baseline_digits_set, "128", "百万円"
        )
        self.assertTrue(became_claim)
        self.assertEqual(ids, {"N050", "N051"})


# ---------------------------------------------------------------------------
# 追加: 文の実際の組み立て・挿入(build_sentence / insert_sentence)
# ---------------------------------------------------------------------------

class BuildAndInsertTest(unittest.TestCase):
    def test_build_sentence_uses_a_different_subject_each_call(self):
        import random
        refs = []
        templates = TI.S.ABSENT_TEMPLATES["xbrl"]
        rng = random.Random("seed")
        used_subjects, used_values = set(), set()
        subjects = []
        for _ in range(6):
            built = TI.build_sentence(templates, refs, rng, used_subjects, used_values)
            self.assertIsNotNone(built)
            subjects.append(built["detail"]["fabricated_subject"])
        self.assertEqual(len(set(subjects)), 6)
        # 7 回目は主語が尽きて None になる。
        self.assertIsNone(TI.build_sentence(templates, refs, rng, used_subjects, used_values))

    def test_insert_sentence_only_touches_the_mdna_entry(self):
        extra = {"meta/other.bin": b"\x00\x01binary"}
        zb = make_zip("先頭の文。中の文。末尾の文。", extra_files=extra)
        entry, raw, start, end, _local = TI.locate_mdna_raw(zb)
        inner = raw[start:end]
        points = TI.find_insertion_points(inner)
        self.assertEqual(len(points), 1)
        new_zb = TI.insert_sentence(zb, points[0], "挿入した文。")
        z1 = zipfile.ZipFile(io.BytesIO(zb))
        z2 = zipfile.ZipFile(io.BytesIO(new_zb))
        self.assertEqual(z1.namelist(), z2.namelist())
        self.assertEqual(z1.read("meta/other.bin"), z2.read("meta/other.bin"))
        _e2, raw2, s2, e2, _l2 = TI.locate_mdna_raw(new_zb)
        self.assertIn("挿入した文。", raw2[s2:e2])


if __name__ == "__main__":
    unittest.main()
