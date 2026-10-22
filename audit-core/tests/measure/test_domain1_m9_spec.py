# -*- coding: utf-8 -*-
"""段 9 の問いの直し(measure/sheet_label_spec_m9_2026-10-16.py)を固定する。

封 docs/DOMAIN1_M9_SEAL_2026-10-16.md §3-4。守るのは 8 つ。
  1. **凍結した spec の byte が動いていない**(段 6〜段 8 が再現できること)
  2. 差し替えたのは**会計の 2 本の規則と会計の欄の説明だけ**
  3. 旧の無条件の指示(`東京都` を外す)が**新しい問いに残っていない**
  4. **旧の問いは段 9 の検査器で落ちる**(直しが効いている証拠)
  5. `check_question` が**生成した問いを通す**・1 字欠けたら落ちる
  6. 新しい規則が `normalize_answer` と**同じ向き**になったこと
     ― 裏づけの無い別名は**畳まれない**ので、字のまま書くのが正しい
  7. 規則に**当たる例と当たらない例**が在ること
  8. 問いの sha と字数
"""
import copy
import hashlib
import importlib.util
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FROZEN = os.path.join(MEASURE, "sheet_label_spec_2026-10-15.py")
SRC = os.path.join(MEASURE, "sheet_label_spec_m9_2026-10-16.py")

# 凍結した file の sha(動かしてはいけない)
FROZEN_SHA = "5c5755572dbca1b6f0fe168d9ff8053fbe429c749190fdd6c44bdcd9ed43cb16"
# 段 9 の問い
M9_SHA16 = "615f5a0e213cac0c"
M9_CHARS = 1512
# 段 8 の問い(封に書いた値)
M8_SHA16 = "cb61f9ecdd9fcee0"
M8_CHARS = 1437


def mod():
    sp = importlib.util.spec_from_file_location("m9spec_t", SRC)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


class FrozenTest(unittest.TestCase):
    def test_1_frozen_spec_is_untouched(self):
        """**段 6〜段 8 の採点器が読む file を動かしていない。**"""
        h = hashlib.sha256(io.open(FROZEN, "rb").read()).hexdigest()
        self.assertEqual(h, FROZEN_SHA, "凍結した label spec が動いた")

    def test_2_frozen_question_unchanged(self):
        m = mod()
        q = m.L.question_text()
        self.assertEqual(hashlib.sha256(q.encode("utf-8")).hexdigest()[:16],
                         M8_SHA16)
        self.assertEqual(len(q), M8_CHARS)
        self.assertEqual(m.L.SPEC["version"], "2026-10-15/m6")


class ReplacementTest(unittest.TestCase):
    def setUp(self):
        self.m = mod()

    def test_3_only_the_account_rules_and_says_changed(self):
        m = self.m
        self.assertEqual(sorted(m.RULES_REPLACED), ["R-会計-1", "R-会計-2"])
        self.assertEqual(sorted(m.SAYS_REPLACED), ["会計"])
        for rid, body in m.L.SPEC["rules"].items():
            if rid in m.RULES_REPLACED:
                self.assertNotEqual(m.SPEC["rules"][rid], body, rid)
            else:
                self.assertEqual(m.SPEC["rules"][rid], body, rid)
        frozen = {f["key"]: f for f in m.L.SPEC["fields"]}
        for f in m.SPEC["fields"]:
            g = frozen[f["key"]]
            self.assertEqual(tuple(f["blank_at"]), tuple(g["blank_at"]), f["key"])
            self.assertEqual(tuple(f["rules"]), tuple(g["rules"]), f["key"])
            if f["key"] in m.SAYS_REPLACED:
                self.assertNotEqual(f["says"], g["says"])
            else:
                self.assertEqual(f["says"], g["says"], f["key"])
        self.assertEqual(m.SPEC["verdicts"], m.L.SPEC["verdicts"])
        self.assertEqual(m.SPEC["examples"], m.L.SPEC["examples"])
        self.assertEqual(m.SPEC["version"], "2026-10-16/m9")

    def test_4_old_unconditional_instruction_is_gone(self):
        q = self.m.question_text()
        self.assertNotIn(u"`東京都` を外した表 1 の名前", q)
        self.assertNotIn(u"と書かれていても", q)
        self.assertIn(u"指している行の「会計」欄に書かれている字をそのまま", q)
        self.assertIn(u"`東京都` を付けたり外したりしないでください", q)

    def test_5_rule_has_a_hit_and_a_miss_example(self):
        """規則は 1 通りに読める字で書く(記憶 `seal-rule-wording-must-be-executable`)。"""
        r = self.m.SPEC["rules"]["R-会計-2"]
        self.assertIn(u"`東京都と場会計` なら `東京都と場会計` と書く", r)
        self.assertIn(u"`一般会計` と書かれていれば `一般会計` と書く", r)
        self.assertIn(u"`と場会計` に直してはいけない", r)

    def test_6_check_question_accepts_the_new_and_rejects_the_old(self):
        m = self.m
        self.assertTrue(m.check_question(m.question_text()))
        with self.assertRaises(AssertionError):
            m.check_question(m.L.question_text())

    def test_7_check_question_is_not_vacuous(self):
        """1 字欠けたら落ちること(**この検査器が材料を止める唯一の門**)。"""
        m = self.m
        q = m.question_text()
        for drop in (m.SPEC["rules"]["R-会計-1"], m.SPEC["rules"]["R-会計-2"],
                     m.field_line([f for f in m.SPEC["fields"]
                                   if f["key"] == u"会計"][0])):
            with self.assertRaises(AssertionError):
                m.check_question(q.replace(drop, u""))

    def test_8_sha_and_length(self):
        q = self.m.question_text()
        self.assertEqual(hashlib.sha256(q.encode("utf-8")).hexdigest()[:16],
                         M9_SHA16)
        self.assertEqual(len(q), M9_CHARS)


class VerifyHasTeethTest(unittest.TestCase):
    """**壊した spec を食わせて赤になるか。**

    `verify` は正常な入力では発火しない守りなので、故障を作って当てないと測れない
    (記憶 `guard-that-only-fires-on-failure.md`)。
    """

    def setUp(self):
        self.m = mod()

    def broken(self, mutate):
        spec = copy.deepcopy(self.m.SPEC)
        mutate(spec)
        with self.assertRaises(AssertionError):
            self.m.verify(spec)

    def test_12_real_spec_passes(self):
        self.assertTrue(self.m.verify(copy.deepcopy(self.m.SPEC)))

    def test_13_changing_an_untouched_rule_is_red(self):
        self.broken(lambda s: s["rules"].__setitem__(u"R-値-1", u"好きに書いて"))

    def test_14_reverting_a_replaced_rule_is_red(self):
        m = self.m
        self.broken(lambda s: s["rules"].__setitem__(
            u"R-会計-2", m.L.SPEC["rules"][u"R-会計-2"]))

    def test_15_changing_blank_at_is_red(self):
        def f(s):
            for x in s["fields"]:
                if x["key"] == u"親":
                    x["blank_at"] = ()
        self.broken(f)

    def test_16_changing_an_untouched_says_is_red(self):
        def f(s):
            for x in s["fields"]:
                if x["key"] == u"列":
                    x["says"] = u"適当に"
        self.broken(f)

    def test_17_changing_the_rule_mapping_is_red(self):
        def f(s):
            for x in s["fields"]:
                if x["key"] == u"会計":
                    x["rules"] = (u"R-会計-1",)
        self.broken(f)

    def test_18_changing_verdicts_or_examples_is_red(self):
        self.broken(lambda s: s["verdicts"].__setitem__(u"判定不能", u"適当に"))
        self.broken(lambda s: s["examples"].pop())

    def test_19_dropping_or_adding_a_rule_is_red(self):
        self.broken(lambda s: s["rules"].pop(u"R-列-2"))
        self.broken(lambda s: s["rules"].__setitem__(u"R-新-1", u"足した"))

    def test_20_not_bumping_the_version_is_red(self):
        m = self.m
        self.broken(lambda s: s.__setitem__("version", m.L.SPEC["version"]))

    def test_22_replacement_identical_to_frozen_is_red(self):
        """**「直したつもりで旧と同じ字」を落とす守り**(変異 P4 が黙った穴)。

        凍結した側の字を新しい字に差し替えた spec を食わせると、
        「差し替え」が実質何も変えていないことになるので落ちねばならない。
        """
        m = self.m
        frozen = copy.deepcopy(m.L.SPEC)
        for rid, body in m.RULES_REPLACED.items():
            frozen["rules"][rid] = body
        with self.assertRaises(AssertionError) as cm:
            m.verify(copy.deepcopy(m.SPEC), frozen=frozen)
        self.assertIn(u"旧と同じ字", str(cm.exception))

    def test_21_fields_order_or_keys_changed_is_red(self):
        self.broken(lambda s: s["fields"].reverse())


class SameDirectionAsNormalizerTest(unittest.TestCase):
    """**封 §3-4 の欠陥がもう起きないことを数で確かめる。**

    裏づけの無い別名は `normalize_answer` で畳まれない。だから
    「字のまま書く」が engine の答えと一致し、「`東京都` を外す」は一致しない。
    """

    def setUp(self):
        self.m = mod()
        E = self._engine()
        M2 = E.M2
        books = {}
        for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
            books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
        raw = E.fix_total_level(E.build_index(
            M2.parse_soukatu(books[M2.SOUKATU]),
            M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI])))
        self.alias = E.alias_table(raw)

    def _engine(self):
        sp = importlib.util.spec_from_file_location(
            "m5_for_m9spec", os.path.join(MEASURE, "sheet_m5_engine_2026-10-15.py"))
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        return m

    def _ans(self, scope):
        return self.m.normalize_answer(
            {u"会計": scope, u"階層": u"項", u"親": u"x", u"科目名": u"y",
             u"列": u"支出済額", u"値": u"1"}, self.alias["table"])[u"会計"]

    def test_9_confirmed_alias_folds_either_way(self):
        self.assertEqual(self._ans(u"東京都一般会計"), u"一般会計")
        self.assertEqual(self._ans(u"一般会計"), u"一般会計")

    def test_10_unconfirmed_alias_does_not_fold(self):
        """ここが段 9 の要。**畳まれないので「字のまま」が正しい。**"""
        self.assertEqual(self._ans(u"東京都と場会計"), u"東京都と場会計")
        self.assertNotEqual(self._ans(u"と場会計"), self._ans(u"東京都と場会計"))
        self.assertIn(u"東京都と場会計",
                      {u["name"] for u in self.alias["unconfirmed"]})

    def test_11_engine_label_uses_the_same_normalizer(self):
        """engine の答えも同じ `_norm_field` を通る(両側に同じ正規化)。"""
        m = self.m
        bind = {"state": "GROUNDED",
                "evidence": {"scope": u"東京都と場会計", "level": u"目",
                             "parent": u"款 > 項", "name": u"管理費",
                             "column": u"支出済額", "value": 1}}
        lab = m.engine_label(bind, self.alias["table"])
        self.assertEqual(lab[u"会計"], u"東京都と場会計")
        self.assertEqual(lab[u"会計"], self._ans(u"東京都と場会計"))


if __name__ == "__main__":
    unittest.main()
