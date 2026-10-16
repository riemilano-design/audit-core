# -*- coding: utf-8 -*-
"""段 9 の材料と機会の数を固定する(封 docs/DOMAIN1_M9_SEAL_2026-10-16.md §3・§5)。

**生成より先に commit する。**守るのは 10 つ。
  1. 表の形と件数が封の規則どおり
  2. **表 3b の会計は別名の形**(`東京都○○会計`)・**表 3a は正本の形**
     ― この差が③の発火機会(封 §3-2)
  3. 表 2 の款名は **B-1〜B-3 の 3 本**がそろった項だけ。**未確認会計の項は落ちる**
  4. 表 3 の款名・項名は **B-4 + B-5 の 2 本だけ**。落ちた数を記録
  5. **段 4〜段 8 で主張された値(0 を除く)を 1 つも載せていない**
  6. **封に無い規則(過去の抜粋の行を除く)を script が足していない。**
     重複した数は記録して開示する
  7. 生成の指示文が**段 4 と 1 バイト同じ**
  8. 機会 O-1〜O-7 が数え直しと一致。**O-3 = O-1**(6 欄すべて読める)
  9. **O-4(抜粋の中)と O-4′(索引全体)が別物**であること
 10. **報告文より先**であること(まだ report が無い)
"""
import collections
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m9_material_2026-10-16.json")
OPP = os.path.join(FX, "m9_opportunity_2026-10-16.json")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M9_SEAL_2026-10-16.md")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


class TableShapeTest(unittest.TestCase):
    def setUp(self):
        self.mat = load(MAT)
        self.c = self.mat["counts"]
        O = _mod("opp9_t", "sheet_m9_opportunity_2026-10-16.py")
        self.O = O
        self.extract = O.extract_of(self.mat)

    def test_1_counts(self):
        c = self.c
        self.assertEqual(c["表1_行"], 20)
        self.assertFalse(c["表1_に値を載せたか"])
        self.assertEqual(c["表2_行"], 26)
        self.assertEqual(c["表2_一般会計の行"], 16)
        self.assertEqual(c["表2_未確認会計の正本の行"], 10)
        self.assertEqual(c["表2_款の行"], 10)
        self.assertEqual(c["表2_項の行"], 16)
        self.assertEqual(c["表3a_行"], 12)
        self.assertEqual(c["表3b_行"], 54)
        self.assertEqual(c["表3_行"], 66)
        self.assertLessEqual(self.mat["extract_chars"], 24000)

    def test_2_ippan_head_is_the_declared_limit(self):
        M = _mod("mat9_t", "sheet_m9_material_2026-10-16.py")
        self.assertEqual(M.IPPAN_HEAD, 16)
        self.assertEqual(M.MOKU_3A_HEAD, 12)
        self.assertEqual(self.c["表2_一般会計の行"], M.IPPAN_HEAD)
        self.assertEqual(self.c["表3a_行"], M.MOKU_3A_HEAD)

    def test_3_columns(self):
        self.assertEqual(self.mat["value_columns"],
                         {"表2": ["予算現額", "支出済額", "不用額"],
                          "表3": ["支出済額", "補正予算額"]})
        self.assertIn("会計\t階層\t款名\t科目名\t予算現額\t支出済額\t不用額",
                      self.extract)
        self.assertIn("会計\t款名\t項名\t目名\t支出済額\t補正予算額", self.extract)


class AliasFormTest(unittest.TestCase):
    """**封 §3-2 の要。**表 3b は別名の形・表 3a は正本の形で載る。"""

    def setUp(self):
        self.mat = load(MAT)

    def test_4_unconfirmed_accounts_are_written_as_aliases(self):
        names = self.mat["counts"]["表3b_の会計"]
        self.assertEqual(len(names), 17)
        for n in names:
            self.assertTrue(n.strip().startswith("東京都"), n)
        unconf = set(self.mat["alias"]["未確認の別名"])
        for n in names:
            self.assertIn(n, unconf, n)

    def test_5_confirmed_alias_is_canonicalised(self):
        for x in self.mat["chosen"]["表3a"]:
            self.assertEqual(x["会計"], "一般会計")
            self.assertFalse(x["別名の形か"])
        for x in self.mat["chosen"]["表3b"]:
            self.assertTrue(x["別名の形か"])
        self.assertEqual(self.mat["alias"]["通った"], ["東京都一般会計"])

    def test_6_the_difference_is_declared_as_the_firing_opportunity(self):
        self.assertIn("この差が③の発火機会である", self.mat["alias"]["注"])


class BackingTest(unittest.TestCase):
    def setUp(self):
        self.mat = load(MAT)

    def test_7_kou_needs_three_backings_and_unconfirmed_drop(self):
        b = self.mat["parent_backing"]
        self.assertIn("B-1", b["表2_款名"])
        self.assertIn("B-2", b["表2_款名"])
        self.assertIn("B-3", b["表2_款名"])
        dropped = b["落とした数"]["項"]
        self.assertEqual(dropped["未確認会計 の項"], 11,
                         "未確認会計の項は B-3 が別名を要するので落ちねばならない")
        self.assertEqual(dropped["一般会計 の項"], 2)
        # **款名を空欄にして載せた行が無いこと**(推測で補完しない)
        for x in self.mat["chosen"]["表2"]:
            if x["階層"] == "項":
                self.assertTrue(x["款名"], x)
            else:
                self.assertEqual(x["款名"], "", x)

    def test_8_moku_has_only_two_backings_and_says_so(self):
        b = self.mat["parent_backing"]
        self.assertIn("B-4", b["表3_款名項名"])
        self.assertIn("B-5", b["表3_款名項名"])
        self.assertNotIn("B-1", b["表3_款名項名"])
        self.assertNotIn("B-3", b["表3_款名項名"])
        self.assertIn("2 本だけ", b["表3_款名項名"])
        self.assertIn("**2 本を 3 本と同じ強さの根拠として扱わない。**", b["注"])
        for x in self.mat["chosen"]["表3a"] + self.mat["chosen"]["表3b"]:
            self.assertTrue(x["款名"], x)
            self.assertTrue(x["項名"], x)


class EquivalenceTest(unittest.TestCase):
    """**黙った変異を等価だと証明して留める**(段 8 の J2 と同じやり方)。

    変異「表 3 の款名・項名を親の欄から直に取る」は**この材料では等価**である。
    裏づけ B-4 は `e["parent"]` と**同じ明細の配置**を見ており、B-5 は 1 行も
    落としていない。だから**試験では区別できない。その事実を字と数で留める。**
    """

    def test_22_backing_equals_splitting_the_parent_field(self):
        M = _mod("mat9_eq", "sheet_m9_material_2026-10-16.py")
        E, M2, norm, BK = M.E, M.M2, M.norm, M.BK
        books = {}
        for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
            books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
        ms = M2.parse_meisai(books[M2.MEISAI])
        raw = E.fix_total_level(E.build_index(
            M2.parse_soukatu(books[M2.SOUKATU]),
            M2.parse_kessan(books[M2.KESSAN]), ms))
        al = E.alias_table(raw)
        ents = E.canonicalize(raw, al)
        moku_ok, why = BK.moku_parents(ms)
        self.assertEqual(why, {}, "B-5 が落とした行が在る(等価でなくなる)")
        written = collections.defaultdict(set)
        for e in raw:
            if e["file"] == "事項別明細":
                written[norm(e["scope"])].add(norm(e["scope"]))
        for w, rec in al["table"].items():
            written[norm(rec["canonical"])].add(norm(w))
        same = diff = nobk = 0
        seen = set()
        for e in ents:
            if e["level"] != "目" or e["file"] != "事項別明細":
                continue
            k = (norm(e["scope"]), norm(e["name"]), norm(e["parent"]),
                 norm(e["column"]))
            if k in seen:
                continue
            seen.add(k)
            bk = M._moku_parent(e, moku_ok, written)
            if bk is None:
                nobk += 1
                continue
            d = tuple((e["parent"] or " > ").split(" > ")[:2])
            if (norm(bk[0]), norm(bk[1])) == (norm(d[0]), norm(d[1])):
                same += 1
            else:
                diff += 1
        self.assertEqual((same, diff, nobk), (2555, 0, 0))

    def test_23_the_equivalence_is_disclosed_in_the_record(self):
        note = load(MAT)["parent_backing"]["**測って分かったこと**"]
        self.assertIn(u"1 行も落ちない", note)
        self.assertIn(u"実質 1 本しか働いていない。**", note)
        self.assertIn(u"**この差を隠さない。**", note)


class NoveltyTest(unittest.TestCase):
    def setUp(self):
        self.mat = load(MAT)
        self.M = _mod("mat9_t2", "sheet_m9_material_2026-10-16.py")
        O = _mod("opp9_t2", "sheet_m9_opportunity_2026-10-16.py")
        self.cells = O.cells_of(O.extract_of(self.mat))

    def test_9_no_previously_claimed_value_is_printed(self):
        """**段 4〜段 8 で主張された値(0 を除く)を 1 つも載せていない。**"""
        used = self.M.used_values()
        self.assertEqual(self.mat["excluded_values"], len(used))
        bad = [c for c in self.cells if c["value"] in used]
        self.assertEqual(bad, [], "既出の値が抜粋に載っている")
        self.assertNotIn(0, used, "0 は除外の対象から外してある")

    def test_10_the_row_rule_not_in_the_seal_is_not_applied(self):
        """**封に無い規則を script が足していない。**重複は数えて開示する。"""
        with io.open(SEAL, encoding="utf-8") as fh:
            seal = fh.read()
        self.assertNotIn("抜粋に現れた行", seal, "封にこの規則は無い")
        ov = self.mat["counts"]["過去の抜粋と重複した行"]
        self.assertEqual(ov, {"表2": 17, "表3a": 14})
        self.assertEqual(self.mat["counts"]["過去の抜粋に在った行の総数"], 191)
        self.assertIn("**重複した行の数を記録して開示する。**", self.M.__doc__)

    def test_11_generation_prompt_is_byte_identical_to_stage4(self):
        M4 = _mod("m4mat_t9", "sheet_m4_material_2026-10-15.py")
        self.assertEqual(self.M.PROMPT, M4.PROMPT)
        self.assertTrue(self.mat["prompt_identical_to_stage4"])

    def test_12_withheld_includes_the_opportunity_counts(self):
        self.assertIn("機会の数(O-1〜O-7)", self.mat["withheld"])
        for s in ("engine の判定", "合否ラベル", "封の内容"):
            self.assertIn(s, self.mat["withheld"])


class OpportunityTest(unittest.TestCase):
    def setUp(self):
        self.opp = load(OPP)
        self.mat = load(MAT)

    def test_13_counts(self):
        o = self.opp
        self.assertEqual(o["O-1 抜粋の値のセル"], 210)
        self.assertEqual(o["O-2 ③が発火し得るセル(会計が未確認の別名)"], 108)
        self.assertEqual(o["O-3 6 欄すべてが抜粋から読めるセル"], 210)
        self.assertEqual(o["O-4 抜粋の中で親が 2 通り以上に割れるセル"
                           "(席が決められない)"], 10)
        self.assertEqual(o["O-4 の科目名ごとの内訳"], {"管理費": 8, "委員会費": 2})
        self.assertEqual(o["O-4′ 索引全体で親が 2 通り以上に割れるセル"], 12)
        self.assertEqual(o["O-5 親の全成分が抜粋から読めるセル"], 180)
        self.assertEqual(o["O-6 列の手がかりが在るセル"], 210)
        self.assertEqual(o["O-6 列の手がかりが無いセル"], 0)
        self.assertEqual(o["O-7 旧では保留・新では接続になりうるセル"], 20)
        self.assertEqual(o["O-7 の表ごとの内訳"], {"表 3": 20})

    def test_14_all_six_fields_readable(self):
        """**O-3 = O-1。**抜粋に無い行に結ぶ余地を材料の側で消しておく。"""
        self.assertEqual(self.opp["O-3 6 欄すべてが抜粋から読めるセル"],
                         self.opp["O-1 抜粋の値のセル"])

    def test_15_o4_and_o4prime_are_different(self):
        """席は抜粋しか読まない。engine は材料の全部を読む。**足さない。**"""
        self.assertNotEqual(self.opp["O-4 抜粋の中で親が 2 通り以上に割れるセル"
                                     "(席が決められない)"],
                            self.opp["O-4′ 索引全体で親が 2 通り以上に割れるセル"])
        self.assertTrue(any("足したり比べたりしない" in x
                            for x in self.opp["limit"]))

    def test_16_o4_rows_are_all_zero_valued(self):
        rows = [c for c in self.opp["cells"] if c["ambiguous_in_extract"]]
        self.assertEqual(len(rows), 10)
        for r in rows:
            self.assertEqual(r["value"], 0, r)
            self.assertEqual(r["column"], "補正予算額", r)

    def test_17_o2_rows_are_all_in_table3(self):
        rows = [c for c in self.opp["cells"] if c["scope_unconfirmed"]]
        self.assertEqual(len(rows), 108)
        self.assertEqual({r["表"] for r in rows}, {"表 3"})

    def test_25_equivalent_mutations_are_disclosed(self):
        """**黙った変異を「穴」ではなく「等価」として字で残す。**"""
        note = self.opp["O-3 の注"]
        self.assertIn(u"この材料では等価", note)
        self.assertIn(u"壊した入力", note)
        self.assertIn(u"prediction-must-be-able-to-fail", note)

    def test_18_limits_are_declared(self):
        joined = " ".join(self.opp["limit"])
        self.assertIn("0 件だったときは「未測定」として", joined)
        self.assertIn("**G-4 の分母は再び 0 になり得る**", joined)
        self.assertIn("**G-7 は段 9 の線ではない**", joined)
        self.assertTrue(self.opp["not_a_pass_condition"])
        self.assertIn("標本を選び直さない", self.opp["will_not_reselect"])

    def test_21_readable_has_teeth(self):
        """**O-3 = O-1 なので数だけでは歯が無い。**壊した入力で False になること。"""
        O = _mod("opp9_t4", "sheet_m9_opportunity_2026-10-16.py")
        en = O.norm("一般会計 福祉費 子供費 児童費 支出済額")
        ok = {"scope": "一般会計", "level": "目", "parent": "福祉費 > 子供費",
              "name": "児童費", "column": "支出済額"}
        comps = ["福祉費", "子供費"]
        self.assertTrue(O.readable_of(ok, en, comps))
        # 会計が抜粋に無い
        self.assertFalse(O.readable_of(dict(ok, scope="と場会計"), en, comps))
        # 列が抜粋に無い
        self.assertFalse(O.readable_of(dict(ok, column="不用額"), en, comps))
        # 親の成分の片方が抜粋に無い
        self.assertFalse(O.readable_of(ok, en, ["福祉費", "無い費"]))
        # 項なのに親が空(段 7 の失敗の形)
        self.assertFalse(O.readable_of(
            {"scope": "一般会計", "level": "項", "parent": "", "name": "児童費",
             "column": "支出済額"}, en, []))
        self.assertIn("緩める変異が等価になり", O.readable_of.__doc__)

    def test_24_recorded_readable_comes_from_readable_of(self):
        """**O-3 = O-1 なので数では歯が無い**(変異 Q13 が黙った)。
        記録した 1 セルごとの旗が `readable_of` の計算と一致することを要求する。
        """
        O = _mod("opp9_t5", "sheet_m9_opportunity_2026-10-16.py")
        NEW = _mod("m7_for_t5", "sheet_m7_engine_2026-10-15.py")
        en = O.norm(O.extract_of(self.mat))
        n = 0
        for c in self.opp["cells"]:
            comps = NEW.parent_components(c["parent"])
            want = O.readable_of(c, en, comps)
            self.assertEqual(c["six_fields_readable"], want, c)
            n += 1 if want else 0
        self.assertEqual(n, self.opp["O-3 6 欄すべてが抜粋から読めるセル"])

    def test_19_recount_from_the_extract(self):
        """**記録ではなく、いま数え直して一致すること。**"""
        O = _mod("opp9_t3", "sheet_m9_opportunity_2026-10-16.py")
        cells = O.cells_of(O.extract_of(self.mat))
        self.assertEqual(len(cells), self.opp["O-1 抜粋の値のセル"])
        unconf = {O.norm(n) for n in self.mat["alias"]["未確認の別名"]}
        self.assertEqual(sum(1 for c in cells if O.norm(c["scope"]) in unconf),
                         self.opp["O-2 ③が発火し得るセル(会計が未確認の別名)"])
        g = collections.defaultdict(set)
        for c in cells:
            g[(O.norm(c["scope"]), O.norm(c["level"]), O.norm(c["name"]),
               O.norm(c["column"]), c["value"])].add(O.norm(c["parent"]) or "")
        dup = {k for k, v in g.items() if len(v) > 1}
        self.assertEqual(
            sum(1 for c in cells
                if (O.norm(c["scope"]), O.norm(c["level"]), O.norm(c["name"]),
                    O.norm(c["column"]), c["value"]) in dup),
            self.opp["O-4 抜粋の中で親が 2 通り以上に割れるセル(席が決められない)"])


class BeforeGenerationTest(unittest.TestCase):
    def test_20_no_report_yet(self):
        for f in ("m9_report_2026-10-16.json", "m9_binds_2026-10-16.json",
                  "m9_answers_seat1_2026-10-16.json",
                  "m9_score_2026-10-16.json"):
            self.assertFalse(os.path.exists(os.path.join(FX, f)),
                             "生成より先に %s が在る" % f)


if __name__ == "__main__":
    unittest.main()
