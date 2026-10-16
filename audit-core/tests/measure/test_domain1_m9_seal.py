# -*- coding: utf-8 -*-
"""段 9 の封(docs/DOMAIN1_M9_SEAL_2026-10-16.md)を固定する。

**封は材料・問いの直し・生成・採点より先に commit する。**
守るのは 10 つ。
  1. §2-2 の索引の事実が**実測と一致する**(封に書いた数が思い込みでないこと)
  2. §2-3 の「段 6・7・8 で③は 0 件」が**実測と一致する**
  3. `MIN_INDEPENDENT = 3` が engine に**字で**在ること(結果を見て動かさない数)
  4. §3-4 の問いの直しの字が在り、**旧の無条件の指示の字が消えていること**
  5. §4 の 3 本の sha が**実測と一致する**
  6. §6 の線が段 8 からどう変わったか(G-7 を外した・G-1′ を足した)が書いてあること
  7. §7 の 3 つの場合と「**(ウ) を 0 にする規則を足さない**」
  8. §8 の「**A-1 = 0 なら未測定**」= 発火しなかったことを安全の証拠にしない
  9. §9 の限界、特に「**別名の推測が誤りになる行が 1 件も無い**」
 10. §10 の予測が 12 本・件数で書かれていること
"""
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M9_SEAL_2026-10-16.md")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


_CACHE = {}


def index():
    """索引と別名表を 1 度だけ作る(実物を読む)。"""
    if "al" in _CACHE:
        return _CACHE["al"], _CACHE["raw"], _CACHE["ms"]
    E = _mod("m5_for_m9seal", "sheet_m5_engine_2026-10-15.py")
    M2 = E.M2
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    sk = M2.parse_soukatu(books[M2.SOUKATU])
    ks = M2.parse_kessan(books[M2.KESSAN])
    ms = M2.parse_meisai(books[M2.MEISAI])
    raw = E.fix_total_level(E.build_index(sk, ks, ms))
    _CACHE.update({"al": E.alias_table(raw), "raw": raw, "ms": ms, "E": E,
                   "sk": sk})
    return _CACHE["al"], raw, ms


class IndexFactTest(unittest.TestCase):
    """§2-2 の数を**実測と突き合わせる**。"""

    def test_1_alias_counts(self):
        al, raw, _ = index()
        E = _CACHE["E"]
        norm = E.M2.norm
        self.assertEqual(len(al["canonical"]), 20, "正本の会計名")
        others = len({e["scope"] for e in raw if e["scope"] not in al["canonical"]})
        self.assertEqual(others, 19, "明細側の別名")
        self.assertEqual(len(al["table"]), 1, "通った別名")
        self.assertEqual(list(al["table"]), ["東京都一般会計"])
        self.assertEqual(al["table"]["東京都一般会計"]["canonical"], "一般会計")
        self.assertEqual(
            al["table"]["東京都一般会計"]["evidence"]["独立した裏づけ"], 18)
        self.assertEqual(len(al["unconfirmed"]), 18, "未確認の別名")

    def test_2_every_unconfirmed_is_short_of_backing(self):
        """**18/18 が「裏づけ不足」。食い違い 0・接尾一致の曖昧さ 0。**"""
        al, _, _ = index()
        kinds = collections.Counter()
        inds = collections.Counter()
        for u in al["unconfirmed"]:
            why = u["why"]
            if "接尾一致" in why:
                kinds["接尾一致"] += 1
            elif "食い違い" in why:
                kinds["食い違い"] += 1
            else:
                kinds["裏づけ不足"] += 1
                inds[u["independent"]] += 1
            self.assertEqual(u.get("mismatch", 0), 0, u["name"])
        self.assertEqual(kinds["裏づけ不足"], 18)
        self.assertEqual(kinds["食い違い"], 0)
        self.assertEqual(kinds["接尾一致"], 0)
        self.assertEqual(dict(inds), {1: 17, 2: 1}, "独立した裏づけの本数の内訳")

    def test_3_no_canonical_name_is_a_suffix_of_another(self):
        """**封 §9 の限界の根拠。**0 組でなければこの実験の限界の書き方が変わる。"""
        al, _, _ = index()
        norm = _CACHE["E"].M2.norm
        pairs = [(a, b) for a in al["canonical"] for b in al["canonical"]
                 if a != b and norm(a).endswith(norm(b))]
        self.assertEqual(pairs, [], "接尾になっている組が在る")

    def test_4_min_independent_is_pinned_literally(self):
        """人が決めた数は**字で**留める(記憶 `pin-human-decided-numbers-literally.md`)。"""
        t = text(os.path.join(MEASURE, "sheet_m5_engine_2026-10-15.py"))
        self.assertIn("MIN_INDEPENDENT = 3", t)
        al, _, _ = index()
        self.assertEqual(al["min_independent"], 3)

    def test_5_moku_backing_counts(self):
        """§3-3 の 365 行 / 未確認ぶん 56 行。"""
        al, _, ms = index()
        B = _mod("bk_for_m9seal", "sheet_parent_backing_2026-10-16.py")
        norm = _CACHE["E"].M2.norm
        mp, why = B.moku_parents(ms)
        self.assertEqual(len(mp), 365)
        self.assertEqual(why, {})
        unconf = {norm(u["name"]) for u in al["unconfirmed"]}
        self.assertEqual(sum(1 for k in mp if k[0] in unconf), 56)

    def test_6_g4_opportunity_is_zero_valued_only(self):
        """§5-1: 「科目名・列・値まで同じで親が 2 通り以上」は**全部 値 0**。"""
        al, raw, _ = index()
        E = _CACHE["E"]
        norm = E.M2.norm
        ents = E.canonicalize(raw, al)
        out = {}
        for lv in ("款", "項", "目"):
            g = collections.defaultdict(set)
            for e in ents:
                if e["level"] != lv:
                    continue
                g[(norm(e["scope"]), norm(e["name"]), norm(e["column"]),
                   e["value"])].add(norm(e["parent"]) or "")
            d = {k: v for k, v in g.items() if len(v) > 1}
            out[lv] = (len(d), sum(1 for k in d if k[3] != 0))
        self.assertEqual(out["目"], (25, 0))
        self.assertEqual(out["項"], (7, 0))
        self.assertEqual(out["款"], (0, 0))


class PreviousStagesTest(unittest.TestCase):
    def test_7_alias_hold_never_fired(self):
        """§2-3: 段 6・段 7・段 8 で `unconfirmed_scope` は 0 件。"""
        seen = {}
        for tag, f, keys in (
                ("m6", "m6_binds_2026-10-15.json", ("binds",)),
                ("m7", "m7_binds_2026-10-15.json", ("binds",)),
                ("m8", "m8_binds_2026-10-16.json", ("binds_old", "binds_new"))):
            d = load(os.path.join(FX, f))
            n = 0
            for k in keys:
                for b in d.get(k) or []:
                    if b.get("unconfirmed_scope"):
                        n += 1
            seen[tag] = n
        self.assertEqual(seen, {"m6": 0, "m7": 0, "m8": 0})

    def test_8_m6_holds_were_a_different_reason(self):
        """段 6 の保留 4 件は「6 欄が一意でない(2 通り)」= A-2 であり③ではない。"""
        d = load(os.path.join(FX, "m6_binds_2026-10-15.json"))
        c = collections.Counter(b.get("hold_reason") for b in d["binds"]
                                if b.get("hold_reason"))
        self.assertEqual(c["6 欄が一意でない(2 通り。値で選ばない)"], 4)
        for r in c:
            self.assertNotIn("未確認の別名", r)


class ShaTest(unittest.TestCase):
    def test_9_engine_shas_match_the_seal(self):
        t = text(SEAL)
        for f, pre in (("sheet_m5_engine_2026-10-15.py", "6eb5723ef518e1b4"),
                       ("sheet_m7_engine_2026-10-15.py", "4574c3ea013d05a1"),
                       ("sheet_parent_backing_2026-10-16.py", "8e387958c69398e8")):
            h = hashlib.sha256(
                io.open(os.path.join(MEASURE, f), "rb").read()).hexdigest()
            self.assertTrue(h.startswith(pre), "%s の sha が封と違う: %s" % (f, h[:16]))
            self.assertIn(pre, t, "封に %s の sha が無い" % f)


class SealTextTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_10_engine_not_changed_is_declared(self):
        self.assertIn(u"**先に明言する。③の規則は段 6 の時点で既に実装されている。**",
                      self.t)
        self.assertIn(u"engine は変えない", self.t)

    def test_11_question_fix_is_written_with_the_defect(self):
        self.assertIn(u"**R-会計-1**(新)", self.t)
        self.assertIn(u"**R-会計-2**(新)", self.t)
        self.assertIn(u"指している行の「会計」欄に書かれている字をそのまま", self.t)
        # **旧の無条件の指示が残っていないこと**
        self.assertNotIn(u"と書かれていても、**`東京都` を外した表 1 の名前**で答えて",
                         self.t.split(u"いまの問いの R-会計-2 はこう書いてある。")[-1]
                         .split(u"直し。`SPEC`")[0]
                         .split(u"> 表 3(明細)")[0])
        self.assertIn(u"`東京都` を付けたり外したりしないでください", self.t)
        self.assertIn(u"**問いは席に「engine が拒んでいる別名の推測」をさせていた。**",
                      self.t)
        self.assertIn(u"**発火しなかった欠陥は消えた欠陥ではない**", self.t)
        self.assertIn(u"cb61f9ecdd9fcee0", self.t)

    def test_12_lines_and_what_changed_from_m8(self):
        for s in (u"**A-1**", u"**A-3**", u"**X-2**", u"**G-1′**",
                  u"**G-7 を線から外す。**", u"**G-8 = 0 は線に残す**",
                  u"≥ 50%", u"= 0 件", u"≥ 20 件", u"≥ 1 件"):
            self.assertIn(s, self.t, s)
        self.assertIn(u"**生の G-1 も必ず書く**", self.t)
        self.assertIn(u"**止めた主張(A-1 + A-2)が採点対象の半分を超えたら、"
                      u"G-1′ を成果として書かない。**", self.t)

    def test_13_a2_is_not_counted_as_success(self):
        self.assertIn(u"**A-2 を③の成功に数えない。**", self.t)

    def test_14_g4_is_separate(self):
        self.assertIn(u"**③の合否に入れない**", self.t)
        self.assertIn(u"**分母 0 なら `未測定`**", self.t)
        self.assertIn(u"**分母が 0 または 2 件以下なら「4 段続けて未確認」と書く。"
                      u"合格扱いにしない。**", self.t)
        self.assertIn(u"hold-denominator-may-be-seat-disagreement", self.t)

    def test_15_what_the_engine_does_when_grader_cannot_confirm(self):
        """人間が義務づけた予測対象。"""
        self.assertIn(u"**評価者が根拠を確認できないケースで engine が何をするか**",
                      self.t)
        for s in (u"(ア)", u"(イ)", u"(ウ)"):
            self.assertIn(s, self.t, s)
        self.assertIn(u"**(ウ) を 0 にするために engine に"
                      u"「抜粋の外に結ばない」規則を足すことはしない。**",
                      self.t.replace(u"\n", u""))

    def test_16_no_fire_means_unmeasured(self):
        self.assertIn(u"**発火しなかったことを安全の証拠にしない**", self.t)
        self.assertIn(u"**「未測定」**", self.t)
        self.assertIn(u"③の安全性は**確認できていない**", self.t)

    def test_17_limits(self):
        self.assertIn(u"**別名の推測が誤りになる行が 1 件も無い。**", self.t)
        self.assertIn(u"「止めたおかげで誤接続を防いだこと」は**この材料では"
                      u"原理的に示せない。**", self.t)
        self.assertIn(u"**2 本は段 8 の項の 3 本より弱い。"
                      u"この差を「同じ強さの根拠」として扱わない。**", self.t)
        self.assertIn(u"**②(階層の手がかりの引き継ぎ)には手を付けない。**", self.t)
        self.assertIn(u"**項(親 1 成分)で接続が増えるか**は段 9 でも測らない",
                      self.t)

    def test_18_predictions_are_twelve_and_counted(self):
        ids = re.findall(r"^\| T-(\d+) \|", self.t, re.M)
        self.assertEqual([int(x) for x in ids], list(range(1, 13)))
        block = self.t.split(u"## §10")[1]
        self.assertIn(u"**測ったあとに編集しない。追記は日付つきで足すだけ。"
                      u"外れは外れとして残す。**", block)
        self.assertIn(u"**0 件になる可能性が最も高い**と先に書く", block)

    def test_19_opportunity_rules(self):
        self.assertIn(u"**この数を見て表を増やしたり減らしたりしない。"
                      u"標本を選び直さない。生成文を誘導しない。**", self.t)
        self.assertIn(u"**単位が違うので、O と C を互いに比べない**", self.t)
        ids = re.findall(r"^\| O-(\d) \|", self.t, re.M)
        self.assertEqual([int(x) for x in ids], list(range(1, 8)))

    def test_20_symmetry_audit_is_a_precondition(self):
        self.assertIn(u"8819f61", self.t)
        self.assertIn(u"**`X-1 11 / X-2 8`**", self.t)
        for s in ("S-1", "S-2", "S-3", "S-4", "S-5"):
            self.assertIn(s, self.t, s)

    def test_21_frozen_previous_stages(self):
        self.assertIn(u"**どちらも再採点しない**", self.t)
        self.assertIn(u"**段 8 の 76.0% を段 9 の G-1 と比べない。**", self.t)
        self.assertIn(u"51.3%", self.t)
        self.assertIn(u"**6 件**", self.t)

    def test_22_material_rules_are_mechanical(self):
        self.assertIn(u"**内容で選ばない。全部機械の規則**", self.t)
        self.assertIn(u"**どの表も、段 4〜段 8 で主張された値(0 を除く)を持つ行は"
                      u"入れない。**", self.t)
        self.assertIn(u"**2 本がそろわない行は表 3 に入れない。"
                      u"款名・項名を空欄にして載せることもしない。\n推測で補完しない。**",
                      self.t)
        self.assertIn(u"**この差が抜粋の上に見えることが、③の発火機会である。**",
                      self.t)

    def test_23_order_of_steps(self):
        block = self.t.split(u"## §11")[1]
        for i, s in enumerate((u"この封を commit する", u"問いの直し",
                               u"材料を機械の規則だけで作る", u"機会 O-1〜O-7",
                               u"**1 回だけ**生成", u"旧・新 2 本の engine",
                               u"問いを `SPEC` と機械照合", u"**盲検 2 席**",
                               u"採点する", u"sha を測り直す")):
            self.assertIn(s, block, s)
        self.assertLess(block.index(u"この封を commit する"),
                        block.index(u"材料を機械の規則だけで作る"))
        self.assertLess(block.index(u"材料を機械の規則だけで作る"),
                        block.index(u"**1 回だけ**生成"))
        self.assertLess(block.index(u"**1 回だけ**生成"),
                        block.index(u"**盲検 2 席**"))


class LinesTableTest(unittest.TestCase):
    """**§6-1 の線の表をそのまま固定する。**

    「≥ 1 件」が文書のどこかに在る、では緩められる(変異 L1・L2 が黙った)。
    **記号と線の対応を 1 組ずつ**固定する。
    """

    WANT = [(u"**A-1**", u"**≥ 1 件**"),
            (u"**A-3**", u"**= 0 件**"),
            (u"**E2**", u"**= 0 件**"),
            (u"**X-2**", u"**= 0 件**"),
            (u"**G-5**", u"**≥ 20 件**"),
            (u"**G-1′**", u"**≥ 50%**")]

    def test_28_main_lines(self):
        block = text(SEAL).split(u"### §6-1")[1].split(u"### §6-2")[0]
        rows = []
        for line in block.split(u"\n"):
            cells = [c.strip() for c in line.strip().strip(u"|").split(u"|")]
            if len(cells) == 3 and cells[0].startswith(u"**") and u"---" not in line:
                rows.append((cells[0], cells[2]))
        self.assertEqual(rows, self.WANT, u"§6-1 の線が動いた")
        self.assertIn(u"**この 6 本すべてを満たして初めて合格**", block)
        self.assertIn(u"**E2 が 1 件でも出たら失敗。**", block)

    def test_29_g4_line_is_separate_and_unmeasured_at_zero(self):
        block = text(SEAL).split(u"### §6-3")[1].split(u"### §6-4")[0]
        self.assertIn(u"| G-4 | ラベルが保留の主張を GROUNDED 以外にできた割合 "
                      u"| ≥ 80%(**分母 0 なら `未測定`**) |", block)

    def test_30_g7_removed_from_lines_g8_kept(self):
        block = text(SEAL).split(u"### §6-4")[1].split(u"## §7")[0]
        self.assertIn(u"**G-7 を線から外す。**", block)
        self.assertIn(u"**G-8 = 0 は線に残す**", block)
        self.assertIn(u"G-7 が負(旧より減る)ならそれも書く。", block)
        # G-7 は §6-1 の線の表に在ってはいけない
        lines61 = text(SEAL).split(u"### §6-1")[1].split(u"### §6-2")[0]
        self.assertNotIn(u"G-7", lines61)


class SealNumbersMatchMeasurementTest(unittest.TestCase):
    """**封 §2-2 の数を、実測から字を組み立てて照合する。**

    封が思い込みの数を書けないようにする(記憶 `count-lines-not-guesses.md`)。
    """

    def test_25_section_2_2_numbers(self):
        al, raw, _ = index()
        norm = _CACHE["E"].M2.norm
        block = text(SEAL).split(u"### §2-2")[1].split(u"### §2-3")[0]
        others = len({e["scope"] for e in raw
                      if e["scope"] not in al["canonical"]})
        inds = collections.Counter(u["independent"] for u in al["unconfirmed"])
        pairs = [(a, b) for a in al["canonical"] for b in al["canonical"]
                 if a != b and norm(a).endswith(norm(b))]
        want = [
            u"| %d 件(`合計` を含む) |" % len(al["canonical"]),
            u"| %d 件 |" % others,
            u"| **%d 件**(`東京都一般会計 → 一般会計`、独立した裏づけ %d 本) |"
            % (len(al["table"]),
               al["table"]["東京都一般会計"]["evidence"]["独立した裏づけ"]),
            u"| **%d 件** |" % len(al["unconfirmed"]),
            u"| **%d/%d が「裏づけ不足」**(独立した裏づけ 1 本が %d 件・2 本が %d 件) |"
            % (len(al["unconfirmed"]), len(al["unconfirmed"]), inds[1], inds[2]),
            u"| **%d 組** |" % len(pairs),
        ]
        for s in want:
            self.assertIn(s, block, u"封 §2-2 が実測と違う: %s" % s)
        self.assertEqual(block.count(u"| **0 件**(18/18 で候補は 1 件に定まる) |"), 1)

    def test_26_section_3_3_numbers(self):
        al, _, ms = index()
        B = _mod("bk_for_m9seal2", "sheet_parent_backing_2026-10-16.py")
        norm = _CACHE["E"].M2.norm
        mp, _ = B.moku_parents(ms)
        unconf = {norm(u["name"]) for u in al["unconfirmed"]}
        n_un = sum(1 for k in mp if k[0] in unconf)
        block = text(SEAL).split(u"### §3-3")[1].split(u"### §3-4")[0]
        self.assertIn(u"**%d 行**" % len(mp), block)
        self.assertIn(u"**%d 行**(%d 会計)"
                      % (n_un, len({k[0] for k in mp if k[0] in unconf})), block)

    def test_27_section_5_1_numbers(self):
        al, raw, _ = index()
        E = _CACHE["E"]
        norm = E.M2.norm
        ents = E.canonicalize(raw, al)
        got = {}
        for lv in (u"項", u"目"):
            g = collections.defaultdict(set)
            for e in ents:
                if e["level"] != lv:
                    continue
                g[(norm(e["scope"]), norm(e["name"]), norm(e["column"]),
                   e["value"])].add(norm(e["parent"]) or "")
            d = {k: v for k, v in g.items() if len(v) > 1}
            got[lv] = (len(d), sum(1 for k in d if k[3] != 0))
        block = text(SEAL).split(u"### §5-1")[1]
        self.assertIn(u"目 %d 組・項 %d 組" % (got[u"目"][0], got[u"項"][0]), block)
        self.assertIn(u"**うち値が 0 でないものは %d 組**"
                      % (got[u"目"][1] + got[u"項"][1]), block)


class SealIsFirstTest(unittest.TestCase):
    def test_24_no_material_or_report_yet(self):
        """**封より先に材料や報告文が在ってはいけない。**"""
        for f in ("m9_material_2026-10-16.json", "m9_report_2026-10-16.json",
                  "m9_binds_2026-10-16.json", "m9_score_2026-10-16.json",
                  "m9_answers_seat1_2026-10-16.json"):
            self.assertFalse(os.path.exists(os.path.join(FX, f)),
                             "封より先に %s が在る" % f)


if __name__ == "__main__":
    unittest.main()
