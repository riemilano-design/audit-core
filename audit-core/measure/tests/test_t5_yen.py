# -*- coding: utf-8 -*-
"""規則 T5Y(封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §0-2・§1)の試験。

注入の仕掛けの T5(値が偶然一致して参照先が違う)を円族の数に作れるようにする切り替え
``lib.sites.t5_yen_2026_11_06``(既定 偽)の試験。偽のとき ``t5_sites``・``build_t5`` が今までと
同じこと、真のとき篩が円で比べられ・描きが倍率で割られ・読み直せない相手が落ち・
相手の単位の優先と乱数の使い方が現行のままであること。

置き場: ``test_inject.py`` は名前で仕掛けの file に数えられ、封の木に在る file の変更が宣言できないので、
H の試験(``test_yen_scan.py``)と同じく新しい file。切り替えを真にする試験は必ず偽に戻す。
"""

import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
MEASURE = os.path.dirname(HERE)
sys.path.insert(0, MEASURE)

import inject  # noqa: E402
from lib import numbers as N  # noqa: E402
from lib import sites as S  # noqa: E402


class _Both(object):
    """H の切り替え(複合 token を読む)と T5Y の切り替えを with の中だけ真にする。出るときは必ず偽に戻す。"""

    def __enter__(self):
        N.yen_scan_2026_11_05 = True
        S.t5_yen_2026_11_06 = True
        return self

    def __exit__(self, *exc):
        N.yen_scan_2026_11_05 = False
        S.t5_yen_2026_11_06 = False
        return False


class _HOnly(object):
    def __enter__(self):
        N.yen_scan_2026_11_05 = True
        return self

    def __exit__(self, *exc):
        N.yen_scan_2026_11_05 = False
        return False


class _CountingRng(object):
    """``randrange`` を数え、いつも 0 を返す(相手の選びを固定する)。"""

    def __init__(self):
        self.calls = []

    def randrange(self, n):
        self.calls.append(n)
        return 0


def ref(key, label, value, unit="円"):
    return {"key": key, "label": label, "unit": unit, "value": float(value), "role": "value"}


TEXT_FRAC = "売上高は12.3億円でした。\n"
TEXT_COMPOUND = "売上高は14億3,300万円でした。\n"
TRUE_REF_FRAC = ref("sales@c", "売上高", 1230000000)
TRUE_REF_COMPOUND = ref("sales@c", "売上高", 1433000000)


def refs_frac(*others):
    return [TRUE_REF_FRAC] + list(others)


class TestSwitchDefaultsAndContext(unittest.TestCase):
    def test_the_switch_is_false_by_default_and_the_context_restores_it(self):
        self.assertFalse(S.t5_yen_2026_11_06)
        with S.t5_yen_on():
            self.assertTrue(S.t5_yen_2026_11_06)
        self.assertFalse(S.t5_yen_2026_11_06)
        try:
            with S.t5_yen_on():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertFalse(S.t5_yen_2026_11_06)

    def test_the_context_restores_the_old_value_not_a_hard_false(self):
        S.t5_yen_2026_11_06 = True
        try:
            with S.t5_yen_on():
                self.assertTrue(S.t5_yen_2026_11_06)
            self.assertTrue(S.t5_yen_2026_11_06)
        finally:
            S.t5_yen_2026_11_06 = False


class TestOffIsUnchanged(unittest.TestCase):
    """偽のとき ``t5_sites``・``build_t5`` は今までと同じ(円族の数は site 0、単位 None の数は今までどおり site)。"""

    def test_a_yen_family_number_is_no_site_when_off(self):
        other = ref("o@c", "営業利益", 1433000000)
        self.assertEqual(1, len(S.identified_sites(TEXT_FRAC, refs_frac(other))))
        self.assertEqual([], S.t5_sites(TEXT_FRAC, refs_frac(other)))
        with _HOnly():
            self.assertEqual([], S.t5_sites(TEXT_FRAC, refs_frac(other)))
            self.assertEqual([], S.t5_sites(TEXT_COMPOUND, [TRUE_REF_COMPOUND, ref("o@c", "営業利益", 1986000000)]))

    def test_the_old_screen_compares_the_written_value_so_a_small_value_is_a_site_when_off(self):
        small = ref("o@c", "従業員", 50, unit=None)
        sites = S.t5_sites(TEXT_FRAC, refs_frac(small))
        self.assertEqual(1, len(sites))
        self.assertEqual(["o@c"], [o["key"] for o in sites[0]["others"]])

    def test_a_unitless_number_is_a_site_as_before_and_build_t5_is_as_before(self):
        text = "対局は 22 局ありました。\n"
        refs = [ref("a", "対象", 22, unit="局"), ref("b", "別の値", 25, unit="局")]
        sites = S.t5_sites(text, refs)
        self.assertEqual(1, len(sites))
        built = inject.build_t5(sites[0], refs, random.Random(0))
        self.assertEqual(25.0, built["new_value"])
        self.assertEqual("25", built["replacement"])
        self.assertEqual({"true_ref_key": "a", "true_ref_label": "対象", "true_value": 22.0, "replacement_value": 25.0,
                          "coincident_ref_key": "b", "coincident_ref_label": "別の値", "replacement_absent_from_reference_numbers": False},
                         built["detail"])

    def test_build_t5_off_draws_the_value_unscaled_even_for_a_yen_family_token(self):
        small = ref("o@c", "従業員", 50, unit=None)
        sites = S.t5_sites(TEXT_FRAC, refs_frac(small))
        built = inject.build_t5(sites[0], refs_frac(small), random.Random(0))
        self.assertEqual("50.0", built["replacement"])                 # 今までどおり 倍率で割らない(読み直せない描き)
        self.assertEqual(50.0, built["new_value"])

    def test_off_uses_the_rng_exactly_once(self):
        text = "対局は 22 局ありました。\n"
        refs = [ref("a", "対象", 22, unit="局"), ref("b", "別の値", 25, unit="局")]
        rng = _CountingRng()
        inject.build_t5(S.t5_sites(text, refs)[0], refs, rng)
        self.assertEqual([1], rng.calls)


class TestOnScreenAndDrawing(unittest.TestCase):
    def test_a_fraction_oku_yen_gets_the_partner_drawn_by_the_scale(self):
        other = ref("o@c", "営業利益", 1433000000)
        with _Both():
            sites = S.t5_sites(TEXT_FRAC, refs_frac(other))
            self.assertEqual(1, len(sites))
            self.assertEqual(["o@c"], [o["key"] for o in sites[0]["others"]])
            rng = _CountingRng()
            built = inject.build_t5(sites[0], refs_frac(other), rng)
            self.assertEqual([1], rng.calls)                              # 乱数の使い方は現行のまま(1 回)
        self.assertEqual("14.3", built["replacement"])
        self.assertEqual(14.3, built["new_value"])
        self.assertEqual(1433000000.0, built["detail"]["replacement_value"])
        self.assertEqual("o@c", built["detail"]["coincident_ref_key"])
        self.assertEqual("営業利益", built["detail"]["coincident_ref_label"])
        self.assertEqual("sales@c", built["detail"]["true_ref_key"])
        t = sites[0]["token"]
        self.assertEqual([t.start, t.end], built["span"])
        # 読み直した円の値は相手の値と書かれた桁の半分(5,000,000)以内で、元の 1,230,000,000 から離れる
        with _Both():
            back = [x for x in N.scan(built["replacement"] + t.unit)]
        self.assertEqual(1, len(back))
        got = back[0].value * 100000000
        self.assertLessEqual(abs(got - 1433000000), 5000000)
        self.assertGreater(abs(got - 1230000000), 5000000)

    def test_a_compound_token_gets_the_partner_in_the_compound_form(self):
        other = ref("o@c", "営業利益", 1986000000)
        with _Both():
            tok = [t for t in N.scan(TEXT_COMPOUND) if t.groups is not None][0]
            self.assertEqual(143300.0, tok.value)
            self.assertEqual("万円", tok.unit)
            sites = S.t5_sites(TEXT_COMPOUND, [TRUE_REF_COMPOUND, other])
            self.assertEqual(1, len(sites))
            built = inject.build_t5(sites[0], [TRUE_REF_COMPOUND, other], random.Random(0))
            reread = [t for t in N.scan(built["replacement"] + "万円")]
        self.assertEqual("19億8,600", built["replacement"])
        self.assertEqual(198600.0, built["new_value"])                    # 描いた字を読み直した値(token の単位 = 万円)
        self.assertEqual(1, len(reread))
        self.assertEqual(198600.0, reread[0].value)
        self.assertEqual(1986000000.0, built["detail"]["replacement_value"])

    def test_the_screen_compares_in_yen_a_small_raw_value_is_no_longer_a_partner(self):
        small = ref("o@c", "従業員", 50, unit=None)
        with _Both():
            self.assertEqual([], S.t5_sites(TEXT_FRAC, refs_frac(small)))

    def test_a_partner_outside_ten_times_in_yen_is_dropped(self):
        far = ref("o@c", "遠い値", 99000000000)                              # 12.3 億円の 80 倍
        with _Both():
            self.assertEqual([], S.t5_sites(TEXT_FRAC, refs_frac(far)))
        near = ref("o@c", "近い値", 9900000000)                              # 8 倍
        with _Both():
            self.assertEqual(1, len(S.t5_sites(TEXT_FRAC, refs_frac(near))))

    def test_a_partner_that_draws_the_same_text_is_dropped(self):
        same_text = ref("o@c", "営業利益", 1230000001)                        # 「12.3」と描かれて元の字と同じ
        good = ref("p@c", "経常利益", 1433000000)
        with _Both():
            self.assertEqual([], S.t5_sites(TEXT_FRAC, refs_frac(same_text)))
            sites = S.t5_sites(TEXT_FRAC, refs_frac(same_text, good))
            self.assertEqual(["p@c"], [o["key"] for o in sites[0]["others"]])       # 読み直せない相手だけが others から落ちる
        with _Both():
            self.assertEqual([], S.t5_sites(TEXT_COMPOUND, [TRUE_REF_COMPOUND, ref("o@c", "営業利益", 1433000004)]))

    def test_readable_means_close_to_the_partner_and_different_from_the_original(self):
        # 少数 1 桁の token の書かれた桁は 10,000,000(0.1 億)、その半分の 5,000,000 以内に読めれば読み直せる
        with _Both():
            t = [x for x in N.scan(TEXT_FRAC) if x.text == "12.3"][0]
            self.assertTrue(S.t5_readable(t, 1433000000))
            self.assertFalse(S.t5_readable(t, 1230000001))                   # 元の字と同じ
            self.assertEqual(("14.3", 1430000000.0), S.t5_readback(t, 1433000000))
        self.assertEqual(10000000.0, S.t5_precision(t))

    def test_the_screen_only_form_counts_more_sites_than_the_read_back_form(self):
        same_text = ref("o@c", "営業利益", 1230000001)
        with _Both():
            self.assertEqual(1, len(S.t5_sites_yen(TEXT_FRAC, refs_frac(same_text), False)))
            self.assertEqual(0, len(S.t5_sites_yen(TEXT_FRAC, refs_frac(same_text), True)))

    def test_precision_per_shape(self):
        with _Both():
            frac = [x for x in N.scan(TEXT_FRAC) if x.text == "12.3"][0]
            comp = [x for x in N.scan(TEXT_COMPOUND) if x.groups is not None][0]
            man = [x for x in N.scan("費用は568万円でした。\n") if x.unit == "万円"][0]
            plain = [x for x in N.scan("対局は 22 局ありました。\n") if x.unit == "局"][0]
        self.assertEqual(10000000.0, S.t5_precision(frac))                   # 0.1 × 億
        self.assertEqual(10000, S.t5_precision(comp))                        # 最後の位の万円
        self.assertEqual(10000, S.t5_precision(man))                         # 1 × 万円
        self.assertEqual(1, S.t5_precision(plain))                           # 1 × 倍率なし

    def test_the_pool_prefers_the_partner_unit_that_matches_the_true_reference(self):
        diff_unit = ref("d@c", "営業利益", 1433000000, unit="千円")
        same_unit = ref("s@c", "経常利益", 1500000000, unit="円")
        refs = refs_frac(diff_unit, same_unit)
        with _Both():
            sites = S.t5_sites(TEXT_FRAC, refs)
            self.assertEqual(["d@c", "s@c"], [o["key"] for o in sites[0]["others"]])
            built = inject.build_t5(sites[0], refs, _CountingRng())
        self.assertEqual("s@c", built["detail"]["coincident_ref_key"])        # 相手の単位の優先(rng が 0 を返しても同じ単位が先)
        self.assertEqual("15.0", built["replacement"])

    def test_on_does_not_change_a_unitless_site_screen_except_by_the_read_back(self):
        text = "対局は 22 局ありました。\n"
        refs = [ref("a", "対象", 22, unit="局"), ref("b", "別の値", 25, unit="局")]
        off = [(s["token"].start, [o["key"] for o in s["others"]]) for s in S.t5_sites(text, refs)]
        with _Both():
            on = [(s["token"].start, [o["key"] for o in s["others"]]) for s in S.t5_sites(text, refs)]
        self.assertEqual(off, on)


class _Faked(object):
    """``N.render_value``・``N.scan`` を with の中だけ差し替える(読み直しの 4 つの条件を 1 つずつ単独で当てるため。出るときは必ず戻す)。"""

    def __init__(self, render=None, scan=None):
        self.render, self.scan = render, scan

    def __enter__(self):
        self.old = (N.render_value, N.scan)
        if self.render is not None:
            N.render_value = self.render
        if self.scan is not None:
            N.scan = self.scan
        return self

    def __exit__(self, *exc):
        N.render_value, N.scan = self.old
        return False


class TestEachReadBackConditionAlone(unittest.TestCase):
    """読み直しの 4 つの条件(token が 1 つ・相手の値と桁の半分以内・元の字と違う・元の値から桁の半分より離れる)は、
    実際の描きでは互いに隠し合う(元の字と同じなら元の値に戻るなど)ので、描きと読みを差し替えて 1 つずつ単独で当てる。"""

    def _tok(self):
        with _HOnly():
            return [x for x in N.scan(TEXT_FRAC) if x.text == "12.3"][0]

    def test_the_real_pair_is_readable(self):
        t = self._tok()
        self.assertTrue(S.t5_readable(t, 1433000000))

    def test_not_one_token_alone_is_refused(self):
        t = self._tok()
        real_scan = N.scan
        two = lambda text: real_scan("14.3億円と14.3億円")
        with _Faked(scan=two):
            self.assertIsNone(S.t5_readback(t, 1433000000)[1])
            self.assertFalse(S.t5_readable(t, 1433000000))

    def test_far_from_the_partner_alone_is_refused(self):
        t = self._tok()
        with _Faked(render=lambda v, like: "14.0"):                          # 読み直し 1,400,000,000 は相手 1,433,000,000 から 33,000,000
            self.assertFalse(S.t5_readable(t, 1433000000))

    def test_the_same_text_as_the_original_alone_is_refused(self):
        t = self._tok()
        real_scan = N.scan
        fake = lambda text: [x for x in real_scan("14.3億円")]               # 描いた字は元の字と同じ「12.3」だが、読みは相手の値に近い
        with _Faked(render=lambda v, like: "12.3", scan=fake):
            self.assertFalse(S.t5_readable(t, 1433000000))

    def test_near_the_original_value_alone_is_refused(self):
        t = self._tok()
        with _Faked(render=lambda v, like: "12.30"):                         # 字は違うが、読み直しは元の値 1,230,000,000
            self.assertFalse(S.t5_readable(t, 1232000000))                   # 相手とは 2,000,000 しか離れず、元の値とも同じ
            self.assertEqual(1230000000.0, S.t5_readback(t, 1232000000)[1])


if __name__ == "__main__":
    unittest.main()
