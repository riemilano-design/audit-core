# -*- coding: utf-8 -*-
"""``fixtures/xbrl/tamper_unit.py`` の単体試験。

合成の小さな ZIP だけを使う(本物の EDINET ZIP には触れない)。封
``audit-core/docs/DETECTION_T2_PLAN_2026-10-08.md`` 第 1 部で要求される
最低限の 3 点(一意でない現場は使えない現場になる・数字は 1 文字も変わら
ない・他のエントリはバイト単位で不変)に加えて、変異を自分で当てて見つけ
た穴(エンティティ越しの一意性・末尾一致・接頭辞違い)の回帰も入れる。
"""

import io
import os
import sys
import unicodedata
import unittest
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_FIXTURES_XBRL = os.path.join(_AUDIT_CORE, "fixtures", "xbrl")
if _FIXTURES_XBRL not in sys.path:
    sys.path.insert(0, _FIXTURES_XBRL)

import tamper_unit as T  # noqa: E402


_MDNA_LOCAL = "ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock"


def make_zip(mdna_text, extra_files=None, local_name=_MDNA_LOCAL, mdna_count=1):
    """1 つの .xbrl instance エントリ(MD&A textblock を ``mdna_count`` 回
    ― 2 回目以降は contextRef を変えて埋める、別文書の前期欄のような形)を
    持つ最小の ZIP を合成する。``extra_files``: {entry_name: bytes} を素の
    まま追加する(他のエントリの不変を確かめる試験のため)。"""

    blocks = []
    for i in range(mdna_count):
        blocks.append(
            '<jpcrp_cor:%s contextRef="Ctx%d">%s</jpcrp_cor:%s>' % (local_name, i, mdna_text, local_name)
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" '
        'xmlns:jpcrp_cor="http://example.com/jpcrp_cor">\n'
        + "\n".join(blocks) +
        '\n</xbrli:xbrl>\n'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("XBRL/PublicDoc/test-001_2026-01-01.xbrl", xml.encode("utf-8"))
        for name, data in (extra_files or {}).items():
            z.writestr(name, data)
    return buf.getvalue()


class LocateMdnaTest(unittest.TestCase):
    def test_finds_the_single_textblock(self):
        zb = make_zip("本文です。105,873千円となりました。")
        entry, raw, start, end, local = T.locate_mdna_raw(zb)
        self.assertEqual(local, _MDNA_LOCAL)
        self.assertEqual(raw[start:end], "本文です。105,873千円となりました。")

    def test_no_instance_entry_raises_no_instance(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("README.txt", b"not an xbrl zip")
        with self.assertRaises(T.NoInstance):
            T.locate_mdna_raw(buf.getvalue())

    def test_no_mdna_textblock_raises(self):
        # AnalysisOfFinancialPosition も OverviewOfBusinessResults も無い。
        zb = make_zip("本文", local_name="SomeUnrelatedTextBlock")
        with self.assertRaises(T.NoMdnaTextblock):
            T.locate_mdna_raw(zb)


class FindUnitSiteTest(unittest.TestCase):
    """試験 1: 一意でない現場は使えない現場になる。"""

    def test_unique_occurrence_is_found(self):
        zb = make_zip("本文です。105,873千円となりました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        start, end = T.find_unit_site(raw[s:e], "105,873", "千円")
        self.assertEqual(raw[s:e][start:end], "千円")

    def test_duplicate_number_and_unit_is_ambiguous(self):
        """同じ「数字+単位」が HTML(ここでは textblock の平文)に 2 回出る。"""
        zb = make_zip("105,873千円でした。後で改めて105,873千円という数字が出ます。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "105,873", "千円")
        self.assertEqual(ctx.exception.match_count, 2)

    def test_zero_occurrences_is_ambiguous_not_a_crash(self):
        zb = make_zip("105,873千円となりました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "999,999", "億円")
        self.assertEqual(ctx.exception.match_count, 0)

    def test_tag_between_digits_and_unit_is_not_forced(self):
        """HTML にはタグが数字と単位の間に入りうる。その場合は無理に合わせ
        ず、0 件(使えない現場)として扱う ― 平文の strip_html を通さない、
        raw のままの探索だから起きる。"""
        zb = make_zip("105,873&lt;span&gt;千円&lt;/span&gt;となりました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "105,873", "千円")
        self.assertEqual(ctx.exception.match_count, 0)

    def test_entity_between_digits_and_unit_is_not_forced(self):
        """``&amp;`` のような実体参照が割り込む場合も同様(無理に合わせない)。"""
        zb = make_zip("105,873&amp;千円となりました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "105,873", "千円")
        self.assertEqual(ctx.exception.match_count, 0)

    # --- REVISE 2026-10-08(独立監査、1 回目): 数字側の左の境界 -------------
    # 短い数字が長い数字の末尾の部分として誤って多重一致してはいけない
    # (「149百万円」が「1,149百万円」に当たる、等)。監査が実測で見つけた
    # 5 件の型をそのまま回帰試験にする。

    def test_short_number_does_not_match_inside_longer_comma_number(self):
        """「149百万円」が「1,149百万円」の中に一致しないこと。"""
        zb = make_zip("当期は減少し、1,149百万円となりました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "149", "百万円")
        self.assertEqual(ctx.exception.match_count, 0)

    def test_short_number_does_not_match_inside_longer_decimal_number(self):
        """「2.5％」が「52.5％」の中に一致しないこと。"""
        zb = make_zip("前期比52.5％増加しました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "2.5", "％")
        self.assertEqual(ctx.exception.match_count, 0)

    def test_short_number_does_not_match_inside_longer_comma_number_2(self):
        """「50,000千円」が「150,000千円」の中に一致しないこと。"""
        zb = make_zip("特別損失として150,000千円を計上しました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "50,000", "千円")
        self.assertEqual(ctx.exception.match_count, 0)

    def test_short_number_still_matches_when_it_really_is_the_whole_number(self):
        """境界を足しても、本当にその数字ちょうどの現場は見つかる(回帰で
        過剰に厳しくなっていないかの確認)。"""
        zb = make_zip("当期は149百万円となりました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        start, end = T.find_unit_site(raw[s:e], "149", "百万円")
        self.assertEqual(raw[s:e][start:end], "百万円")

    def test_fullwidth_number_is_found_from_halfwidth_query(self):
        """measure 側で半角に畳まれた後の token.text(半角)を渡しても、raw
        HTML がまだ全角の数字のままなら見つかる(実測 2026-10-08:
        S100Z4Q1 の「３億円」)。"""
        zb = make_zip("新株式発行によって約３億円の資金調達を実施しました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        start, end = T.find_unit_site(raw[s:e], "3", "億円")
        self.assertEqual(raw[s:e][start:end], "億円")
        # 数字そのものは全角のまま変わらない(全角のまま探して全角のまま置換)。
        new_zb = T.tamper_unit_word(zb, "3", "億円", "千円")
        _e, raw2, s2, e2, _l = T.locate_mdna_raw(new_zb)
        self.assertIn("３千円", raw2[s2:e2])
        self.assertNotIn("３億円", raw2[s2:e2])

    def test_fullwidth_duplicate_is_reported_as_ambiguous_not_missing(self):
        """全角で探しても現場が 2 回出る場合は、0 件(見つからない)ではなく
        2 件(重複)として報告されること ― 「0 件 = 見つからない」と
        「2 件以上 = 重複」を言い分ける。"""
        zb = make_zip("当期は約３億円、翌期も約３億円の調達を予定しています。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "3", "億円")
        self.assertEqual(ctx.exception.match_count, 2)


class TamperUnitWordTest(unittest.TestCase):
    """試験 2・3: 数字は 1 文字も変わらない / 他のエントリはバイト単位で不変。"""

    def _digits_only(self, s):
        return "".join(ch for ch in s if ch.isdigit() or ch == ",")

    def test_digits_unchanged(self):
        zb = make_zip("本文です。105,873千円となりました。")
        new_zb = T.tamper_unit_word(zb, "105,873", "千円", "億円")
        _e, raw0, s0, e0, _l = T.locate_mdna_raw(zb)
        _e, raw1, s1, e1, _l = T.locate_mdna_raw(new_zb)
        before_digits = self._digits_only(raw0[s0:e0])
        after_digits = self._digits_only(raw1[s1:e1])
        self.assertEqual(before_digits, after_digits)
        self.assertIn("105,873", raw1[s1:e1])
        self.assertNotIn("千円", raw1[s1:e1])
        self.assertIn("億円", raw1[s1:e1])

    def test_other_entries_byte_identical(self):
        extra = {
            "XBRL/PublicDoc/test-001_2026-01-01_lab.xml": b"<label>dummy label file</label>",
            "README.txt": ("readme" * 50).encode("utf-8"),
        }
        zb = make_zip("本文です。105,873千円となりました。", extra_files=extra)
        new_zb = T.tamper_unit_word(zb, "105,873", "千円", "億円")
        z0 = zipfile.ZipFile(io.BytesIO(zb))
        z1 = zipfile.ZipFile(io.BytesIO(new_zb))
        self.assertEqual(sorted(z0.namelist()), sorted(z1.namelist()))
        for name in z0.namelist():
            if name == "XBRL/PublicDoc/test-001_2026-01-01.xbrl":
                self.assertNotEqual(z0.read(name), z1.read(name), "the tampered entry must actually change")
                continue
            self.assertEqual(z0.read(name), z1.read(name), "entry %r must be byte-identical" % (name,))

    def test_only_the_instance_entry_differs(self):
        """他のエントリの集合全体が変わらないことも、名前の集合で確かめる
        (エントリが増えたり消えたりしていないか)。"""
        extra = {"a.txt": b"aaa", "b.txt": b"bbb"}
        zb = make_zip("105,873千円。", extra_files=extra)
        new_zb = T.tamper_unit_word(zb, "105,873", "千円", "億円")
        z0 = zipfile.ZipFile(io.BytesIO(zb))
        z1 = zipfile.ZipFile(io.BytesIO(new_zb))
        diffs = [n for n in z0.namelist() if z0.read(n) != z1.read(n)]
        self.assertEqual(diffs, ["XBRL/PublicDoc/test-001_2026-01-01.xbrl"])

    def test_ambiguous_site_leaves_zip_untouched_raises(self):
        zb = make_zip("105,873千円でした。後で改めて105,873千円という数字が出ます。")
        with self.assertRaises(T.AmbiguousSite):
            T.tamper_unit_word(zb, "105,873", "千円", "億円")


class AdversarialMutationProbesTest(unittest.TestCase):
    """自分で当てた変異のうち、黙らず赤くなることを確かめておく回帰群。
    (具体的な変異の当て方・結果は SubagentHandback の報告に書く。ここでは
    「その変異が実際に壊れていたら検出できる」という形の試験だけを残す。)
    """

    def test_unit_match_requires_exact_boundary_not_prefix(self):
        """ある unit がたまたま別の、長い unit の接頭辞になっていても、
        その長い方の出現を「一致」と数えてはいけない(「円」 vs 「千円」)。
        ここでは union body に「千円」だけがあり「円」単独は無い状況で、
        old_unit="円" を要求したら見つからない(0 件)ことを確かめる。"""

        zb = make_zip("本文です。105,873千円となりました。")
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "105,873", "円")
        self.assertEqual(ctx.exception.match_count, 0)

    def test_sibling_mdna_block_is_not_confused_with_first(self):
        """select_mdna が選ぶのは 1 つの名前だが、raw の正規表現は「最初の
        出現」を取る契約になっている。2 つ目のブロック(前期欄などを模す、
        contextRef だけ違う)の内容が 1 つ目に紛れ込んでいないことを確かめ
        る(``</...>`` の非貪欲マッチが効いているかの回帰)。"""

        zb = make_zip("当期は105,873千円でした。", mdna_count=1)
        zb2 = make_zip("当期は105,873千円でした。", mdna_count=2)
        # mdna_count=2 でも最初のブロックの内容は mdna_count=1 のときと同一。
        _e, raw1, s1, e1, _l = T.locate_mdna_raw(zb)
        _e, raw2, s2, e2, _l = T.locate_mdna_raw(zb2)
        self.assertEqual(raw1[s1:e1], raw2[s2:e2])

    def test_single_digit_number_is_handled(self):
        """退化値: 数字が 1 桁(「3億円」)でも一意に特定・置換できる。"""

        zb = make_zip("今後3億円を投資します。")
        new_zb = T.tamper_unit_word(zb, "3", "億円", "千円")
        _e, raw, s, e, _l = T.locate_mdna_raw(new_zb)
        self.assertEqual(raw[s:e], "今後3千円を投資します。")

    def test_nfkc_width_variant_not_silently_accepted_by_tamper(self):
        """tamper_unit 自体は unit の NFKC 正規化を一切しない(それは
        run_detection_t2.py の対応づけ側の責務)。半角 % の現場しかない
        ZIP に全角 ％ を要求したら、素直に 0 件になることを確かめる
        (変異: ここで NFKC を足すと real HTML の実体参照越しの判定が
        崩れるので、意図的に区別したままであることの回帰)。"""

        zb = make_zip("前期比106.0%増加しました。")
        self.assertNotEqual(unicodedata.normalize("NFKC", "％"), "％")  # NFKC の対象であることの前提確認
        _e, raw, s, e, _l = T.locate_mdna_raw(zb)
        with self.assertRaises(T.AmbiguousSite) as ctx:
            T.find_unit_site(raw[s:e], "106.0", "％")
        self.assertEqual(ctx.exception.match_count, 0)
        # 半角そのものなら見つかる。
        start, end = T.find_unit_site(raw[s:e], "106.0", "%")
        self.assertEqual(raw[s:e][start:end], "%")


if __name__ == "__main__":
    unittest.main()
