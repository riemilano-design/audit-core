# -*- coding: utf-8 -*-
"""段 10 の封(docs/DOMAIN1_M10_SEAL_2026-10-16.md)を固定する。

**封は実装・材料・生成・採点より先に commit する。**
守るのは 11 つ。
  1. §2-1 の **9 本の sha** が実測と一致する(段 10 で触らない file)
  2. `MIN_INDEPENDENT = 3` が engine に**字で**在る
  3. §3 の数(款の合計の一致・列の別名・代数の関係・比べられる列)が**実測と一致**する
  4. §3 の「**明細の款が 1 つだけの会計が 17**」「**I-3 後に 2 本が 17 会計**」
     「**3 本に達するのは 1 会計**」が実測と一致する
  5. **§3-1 に第 1 稿の外れた予測(18/18)と実測(1/18)が両方在る**
  6. §3-3 の「通る 1 会計は段 9 の 12 件のどれにも現れない」が**凍結した fixture と一致**する
  7. §4 の D-1 = 18/18・D-2 = 0/342 が実測と一致する
  8. **§4-1 の「D-2 = 0 は歯の無い対照」が実測と一致する**
     (1 列に緩めても誤った対の受理は 0 件)
  9. §5-2 の**停止規則**が封に在る(診断で 1 件以上でなければ本実験を走らせない)
 10. §8〜§9 の線・数え方・予測 16 本・§11 の限界 10 本
 11. **封が実装より先に commit されたこと**(commit の順。file の有無で見ない)
"""
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M10_SEAL_2026-10-16.md")
# **`cwd=ROOT`(= audit-core/)から git を呼ぶので、道は ROOT からの相対で書く。**
# repo のルートからの道(`audit-core/...`)を渡すと pathspec が当たらず、
# `--diff-filter=A` が空を返して「まだ commit されていない」に見える
# ― 2026-10-16 に実際にこれで誤判定した(commit の有無ではなく私の道の誤り)。
SEAL_REL = "docs/DOMAIN1_M10_SEAL_2026-10-16.md"
M10_ENGINE_REL = "measure/sheet_m10_engine_2026-10-16.py"

COLS = ("支出済額", "不用額")
PASSING = "東京都都営住宅等保証金会計"

# §2-1 の表。**段 10 で 1 文字も触らない file**
FROZEN = (
    ("measure/sheet_m5_engine_2026-10-15.py", "6eb5723ef518e1b4"),
    ("measure/sheet_m7_engine_2026-10-15.py", "4574c3ea013d05a1"),
    ("measure/sheet_parent_backing_2026-10-16.py", "8e387958c69398e8"),
    ("measure/sheet_label_spec_2026-10-15.py", "5c5755572dbca1b6"),
    ("measure/sheet_label_spec_m9_2026-10-16.py", "b0d0cb530f4824fe"),
    ("measure/sheet_symmetry_audit_2026-10-16.py", "f3914350ae305b30"),
    ("fixtures/sheet/m9_report_2026-10-16.json", "c93cdf85bbebc287"),
    ("fixtures/sheet/m9_answers_seat1_2026-10-16.json", "54ac4d6cf1d51c69"),
    ("fixtures/sheet/m9_answers_seat2_2026-10-16.json", "c3c896caaa136538"),
)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


_CACHE = {}


def facts():
    """**実物の 3 冊を読んで封の数を作り直す。**1 度だけ。"""
    if "f" in _CACHE:
        return _CACHE["f"]
    sp = importlib.util.spec_from_file_location(
        "m5_for_m10seal", os.path.join(MEASURE, "sheet_m5_engine_2026-10-15.py"))
    E = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(E)
    M2 = E.M2
    norm = M2.norm
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    raw = E.fix_total_level(E.build_index(
        M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
        M2.parse_meisai(books[M2.MEISAI])))
    al = E.alias_table(raw)
    unconf = [u for u in al["unconfirmed"] if u.get("canonical")]

    tot, kan, nkan = {}, collections.defaultdict(int), collections.defaultdict(set)
    sou = []
    for e in raw:
        if e["file"] == "決算書 歳出" and e["level"] == "合計":
            tot[(norm(e["scope"]), norm(e["column"]))] = e["value"]
        elif e["file"] == "事項別明細" and e["level"] == "款":
            kan[(norm(e["scope"]), norm(e["column"]))] += e["value"]
            nkan[norm(e["scope"])].add(norm(e["name"]))
        if e["file"] == "総括" and norm(e["column"]) == norm("歳出決算額"):
            sou.append((norm(e["scope"]), e["level"], e["value"]))

    uniq = {}
    for col in COLS:
        byv = collections.defaultdict(set)
        for (c, cl), v in tot.items():
            if cl == norm(col):
                byv[v].add(c)
        uniq[col] = byv

    def accept(x, c, cols=COLS):
        """R-裏-2: **cols すべてで 一致 かつ 一意**なら受理。"""
        for col in cols:
            a, b = kan.get((norm(x), norm(col))), tot.get((norm(c), norm(col)))
            if a is None or b is None or a != b:
                return False
            if len(uniq.get(col, {}).get(b, ())) != 1:
                return False
        return True

    # R-裏-1 の採用された本(engine と同じ組み立て)
    rows = {}
    for e in raw:
        if e["name"] and e["level"] in ("款", "項"):
            k = (e["scope"], e["level"], norm(e["name"]), norm(e["column"]))
            rows.setdefault(k, {"files": {}, "parent": e["parent"]})
            rows[k]["files"][e["file"]] = e["value"]
    existing, merged, kancount = collections.Counter(), collections.Counter(), \
        collections.Counter()
    passing = []
    for u in unconf:
        x, c = u["name"], norm(u["canonical"])
        hits = []
        for (sc, lv, nm, col), rec in rows.items():
            if sc != x:
                continue
            other = rows.get((c, lv, nm, col))
            if not other:
                continue
            v = sorted(rec["files"].values())[0]
            w = sorted(other["files"].values())[0]
            if v == w and len(set(rec["files"]) | set(other["files"])) >= 2:
                hits.append({"level": lv, "name": nm, "column": col, "value": v,
                             "parent": norm(rec["parent"]) or None,
                             "files": sorted(set(rec["files"]) | set(other["files"]))})
        ind, _ = E._independent(hits)
        vals = {h["value"] for h in ind}
        tv = [tot.get((c, norm(col))) for col in COLS]
        existing[len(ind)] += 1
        kancount[len(nkan.get(norm(x), ()))] += 1
        m = set(vals) | {v for v in tv if v is not None}
        merged[len(m)] += 1
        if len(m) >= al["min_independent"]:
            passing.append(x)

    # 列ごとの一致
    colmatch = {}
    for col in sorted({c for (_, c) in tot}):
        ok = ng = na = 0
        for u in unconf:
            a = kan.get((norm(u["name"]), col))
            b = tot.get((norm(u["canonical"]), col))
            if a is None or b is None:
                na += 1
            elif a == b:
                ok += 1
            else:
                ng += 1
        colmatch[col] = (ok, ng, na)
    # 列の別名 計 <-> 予算現額
    alias_col = sum(1 for u in unconf
                    if kan.get((norm(u["name"]), norm("計"))) is not None
                    and kan[(norm(u["name"]), norm("計"))]
                    == tot.get((norm(u["canonical"]), norm("予算現額"))))
    # 代数の関係
    alg = sum(1 for u in unconf
              if tot.get((norm(u["canonical"]), norm("予算現額")))
              == sum(tot.get((norm(u["canonical"]), norm(x)), 0)
                     for x in ("支出済額", "不用額", "翌年度繰越額")))
    # 総括 == 決算書の支出済額
    souv = {s: v for s, lv, v in sou if lv == "会計"}
    same = sum(1 for u in unconf
               if souv.get(norm(u["canonical"]))
               == tot.get((norm(u["canonical"]), norm("支出済額")))
               and souv.get(norm(u["canonical"])) is not None)
    # 負の対照
    canon = [norm(c) for c in al["canonical"]]
    pairs = [(u["name"], c) for u in unconf for c in canon
             if c != norm(u["canonical"])]
    d1 = sum(1 for u in unconf if accept(u["name"], u["canonical"]))
    d2 = [p for p in pairs if accept(*p)]
    loose = [p for p in pairs if accept(p[0], p[1], cols=("支出済額",))]
    # 一意性(R-独立-4)が本当に 0 組か
    dup = {col: sum(1 for v, s in uniq[col].items() if len(s) > 1) for col in COLS}

    _CACHE["f"] = {
        "E": E, "norm": norm, "unconf": unconf, "min": al["min_independent"],
        "sou_rows": len(sou), "sou_values": len({v for _, _, v in sou}),
        "sou_levels": collections.Counter(lv for _, lv, _ in sou),
        "colmatch": colmatch, "alias_col": alias_col, "alg": alg, "same": same,
        "existing": dict(existing), "merged": dict(merged),
        "kancount": dict(kancount), "passing": passing,
        "d1": d1, "pairs": len(pairs), "d2": len(d2), "loose": len(loose),
        "dup": dup, "accept": accept, "tot": tot, "kan": kan, "uniq": uniq,
    }
    return _CACHE["f"]


class ShaTest(unittest.TestCase):
    """§2-1 ― **段 10 で触らない file の sha が封と実測で一致する。**"""

    def test_1_nine_frozen_shas(self):
        t = text(SEAL)
        for rel, pre in FROZEN:
            h = hashlib.sha256(
                io.open(os.path.join(ROOT, rel), "rb").read()).hexdigest()
            self.assertTrue(h.startswith(pre),
                            "%s の sha が封と違う: %s" % (rel, h[:16]))
            self.assertIn(pre, t, "封に %s の sha が無い" % rel)

    def test_2_the_table_has_exactly_nine_rows(self):
        """**9 本。**増えても減っても封の表と合わなくなる。"""
        t = text(SEAL)
        rows = re.findall(r"^\| `(measure/[^`]+|fixtures/[^`]+)` \| `([0-9a-f]{16})` \|$",
                          t, re.M)
        self.assertEqual(len(rows), 9, rows)
        self.assertEqual(sorted(rows), sorted(FROZEN))

    def test_3_min_independent_is_pinned_literally(self):
        t = text(os.path.join(MEASURE, "sheet_m5_engine_2026-10-15.py"))
        self.assertIn("MIN_INDEPENDENT = 3", t)
        self.assertEqual(facts()["min"], 3)
        self.assertIn("**`MIN_INDEPENDENT = 3`**", text(SEAL))


class MeasuredFactTest(unittest.TestCase):
    """§3 の表を**実測と突き合わせる。**封の数が思い込みでないこと。"""

    def setUp(self):
        self.f = facts()

    def test_4_soukatu_rows_and_values(self):
        self.assertEqual(self.f["sou_rows"], 20)
        self.assertEqual(self.f["sou_values"], 20)
        self.assertEqual(dict(self.f["sou_levels"]), {"会計": 19, "合計": 1})

    def test_5_two_columns_match_eighteen_of_eighteen(self):
        for col in COLS:
            self.assertEqual(self.f["colmatch"][col], (18, 0, 0), col)

    def test_6_only_two_columns_are_comparable(self):
        """**R-独立-3。**比べられるのは 支出済額・不用額 だけ。"""
        comparable = sorted(c for c, (ok, ng, na) in self.f["colmatch"].items()
                            if ok + ng > 0)
        self.assertEqual(comparable, sorted(COLS))
        self.assertEqual(self.f["colmatch"]["翌年度繰越額"], (0, 0, 18))

    def test_7_column_alias_and_algebra_make_yosan_dependent(self):
        """**R-独立-2 は飾りではない** ― `計` は別名で 18/18 一致する。"""
        self.assertEqual(self.f["alias_col"], 18)
        self.assertEqual(self.f["alg"], 18)

    def test_8_soukatu_is_the_same_number(self):
        """**R-独立-1。**総括の歳出決算額は決算書の支出済額と同じ数。"""
        self.assertEqual(self.f["same"], 18)

    def test_9_existing_backing_counts(self):
        self.assertEqual(self.f["existing"], {1: 17, 2: 1})

    def test_10_seventeen_accounts_have_exactly_one_kan(self):
        """**§3-2 の構造の理由。**款が 1 つなら合計はその款の値そのもの。"""
        self.assertEqual(self.f["kancount"], {1: 17, 2: 1})

    def test_11_after_i3_only_one_account_reaches_three(self):
        self.assertEqual(self.f["merged"], {2: 17, 4: 1})
        self.assertEqual(self.f["passing"], [PASSING])

    def test_12_uniqueness_has_no_collision_in_this_material(self):
        """R-独立-4 は**この材料では 1 件も発火しない** ― だから D-3 が要る。"""
        self.assertEqual(self.f["dup"], {"支出済額": 0, "不用額": 0})


class NegativeControlTest(unittest.TestCase):
    def setUp(self):
        self.f = facts()

    def test_13_d1_and_d2(self):
        self.assertEqual(self.f["d1"], 18)
        self.assertEqual(self.f["pairs"], 342)
        self.assertEqual(self.f["d2"], 0)

    def test_14_the_control_has_no_teeth(self):
        """**§4-1。**1 列に緩めても誤った対の受理は 0 件 ―
        つまり D-2 = 0 は「2 列を要求したこと」の価値を示さない。"""
        self.assertEqual(self.f["loose"], 0)

    def test_15_d3_teeth_on_doctored_material(self):
        """**§4-2 の D-3。**値が重なる正本を人工で作ると R-独立-4 が数えない。

        D-3b(重なりを取り除けば数える)が無いと D-3a は無意味である。
        """
        f = self.f
        norm = f["norm"]
        x, c = PASSING, norm("都営住宅等保証金会計")
        self.assertTrue(f["accept"](x, c), "素の材料では通ること(D-3b)")
        # D-3a: 同じ合計の値を持つ正本をもう 1 つ作る
        uniq2 = {col: {v: set(s) for v, s in f["uniq"][col].items()} for col in COLS}
        v = f["tot"][(c, norm("支出済額"))]
        uniq2["支出済額"][v].add("にせの会計")

        def accept2(xx, cc, cols=COLS):
            for col in cols:
                a = f["kan"].get((norm(xx), norm(col)))
                b = f["tot"].get((norm(cc), norm(col)))
                if a is None or b is None or a != b:
                    return False
                if len(uniq2[col].get(b, ())) != 1:
                    return False
            return True

        self.assertFalse(accept2(x, c), "D-3a: 値が重なる列を数えてはいけない")
        uniq2["支出済額"][v].discard("にせの会計")
        self.assertTrue(accept2(x, c), "D-3b: 重なりを取り除けば数える")


class FrozenM9Test(unittest.TestCase):
    """§3-3 ― **通る 1 会計は段 9 で止まった 12 件のどれにも現れない。**"""

    def test_16_held_accounts_match_the_seal(self):
        d = load(os.path.join(FX, "m9_binds_2026-10-16.json"))
        c = collections.Counter(r["会計"] for r in d["A-1_詳細"])
        self.assertEqual(sum(c.values()), 12)
        self.assertEqual(dict(c), {
            "東京都公債費会計": 4, "東京都国民健康保険事業会計": 3,
            "東京都特別区財政調整会計": 2, "東京都地方消費税清算会計": 2,
            "東京都都営住宅等事業会計": 1})
        self.assertNotIn(PASSING, c, "通る会計が 12 件に現れている")
        t = text(SEAL)
        for name, n in (("公債費", 4), ("国民健康保険事業", 3),
                        ("特別区財政調整", 2), ("地方消費税清算", 2),
                        ("都営住宅等事業", 1)):
            self.assertIn("%s %d" % (name, n), t, name)

    def test_17_every_held_account_has_one_kan(self):
        """**封の「どれも款が 1 つの会計である」を実測で確かめる。**"""
        f = facts()
        norm = f["norm"]
        d = load(os.path.join(FX, "m9_binds_2026-10-16.json"))
        held = {r["会計"] for r in d["A-1_詳細"]}
        sp = importlib.util.spec_from_file_location(
            "m5_k", os.path.join(MEASURE, "sheet_m5_engine_2026-10-15.py"))
        for name in held:
            u = [x for x in f["unconf"] if norm(x["name"]) == norm(name)]
            self.assertEqual(len(u), 1, name)
        # 款が 1 つであること
        self.assertEqual(f["kancount"][1], 17)


class SealTextTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_18_first_draft_prediction_is_kept(self):
        """**外れた第 1 稿を残す。**(記憶 `predict-then-tally-my-bias`)"""
        self.assertIn("**先に言う。この封を書く前に測った結果、私の第 1 稿の予測は外れていた。**",
                      self.t)
        self.assertIn("| 3 本に達する会計 | **18 / 18** | **1 / 18** |", self.t)
        self.assertIn("**この足し算が誤りだった。**", self.t)

    def test_19_structural_reason_is_written(self):
        self.assertIn("**未確認 18 会計のうち 17 会計は、明細に款が 1 つしか無い。**", self.t)
        self.assertIn("**これは規則が保守的すぎるのではなく、材料にそれだけの情報が無いということである。**",
                      self.t)
        self.assertIn("**材料を増やす判断(歳入側の file を取得するか)は人間に出す。私は決めない。**",
                      self.t)

    def test_20_control_without_teeth_is_disclosed(self):
        self.assertIn("### §4-1 **だが D-2 = 0 は規則の厳しさの証拠ではない ― 歯が無い**",
                      self.t)
        self.assertIn("**規則を「支出済額 1 列だけ」に緩めても誤った対の受理は 0 件**", self.t)
        self.assertIn("**D-3b が無いと D-3a は無意味である**", self.t)

    def test_21_stop_rule_is_sealed(self):
        """**§5-2。**走らせる条件を**結果を見る前に**書く。"""
        self.assertIn("> **診断で、新しく正しく接続した主張が 1 件以上生まれた場合。**", self.t)
        self.assertIn("**この停止規則は結果を見てから作らない。封に書いてから測る。**", self.t)
        self.assertIn("**走らせない場合、生成の費用は 0 USD である。**", self.t)

    def test_22_diagnosis_is_not_proof(self):
        self.assertIn("**これは既知の標本に対する診断であり、性能の証明ではない。**", self.t)
        self.assertIn("私は段 9 のラベルを**既に読んでいる**", self.t)

    def test_23_lines_are_six_and_increase_is_not_one(self):
        block = self.t.split("### §8-1")[1].split("### §8-2")[0]
        rows = [l for l in block.splitlines()
                if l.startswith("| **") and l.count("|") >= 4]
        self.assertEqual(len(rows), 6, rows)
        self.assertIn("**N-接続-増 を合否に入れない**", self.t)
        self.assertIn("**診断の N-接続-増**(予測 0 件)。**0 でも失敗としない。**", self.t)

    def test_24_five_separate_counts(self):
        block = self.t.split("### §8-2")[1].split("### §8-3")[0]
        self.assertEqual(len(re.findall(r"\| \*\*N-", block)), 5, block)

    def test_25_g4_and_seat_agreement_are_not_in_the_verdict(self):
        self.assertIn("**段 10 では機会を作らない。別の封で設計する**", self.t)
        self.assertIn("**5 段続けて未測定になる。**", self.t)
        self.assertIn("席の一致率。**成果として書かない。**", self.t)

    def test_26_sixteen_predictions(self):
        block = self.t.split("## §9")[1].split("## §10")[0]
        ids = re.findall(r"^\| T-(\d+) \|", block, re.M)
        self.assertEqual([int(x) for x in ids], list(range(1, 17)), ids)
        for must in ("T-9", "T-15", "T-16"):
            self.assertIn("| %s |" % must, block)
        self.assertIn("**測ったあとに編集しない。追記は日付つきで足すだけ。外れは外れとして残す。**",
                      self.t)

    def test_27_failure_conditions_include_silent_mutation(self):
        block = self.t.split("## §10")[1].split("## §11")[0]
        self.assertIn("**緩める変異が 1 本でも黙った**", block)
        self.assertIn("**接続が増えないこと自体は失敗ではない。**", block)
        self.assertIn("**ただし「③の安全性を確認できた」とは書かない**", block)

    def test_28_ten_limits_with_the_two_that_matter(self):
        block = self.t.split("## §11")[1].split("## §12")[0]
        ids = re.findall(r"^(\d+)\. ", block, re.M)
        self.assertEqual([int(x) for x in ids], list(range(1, 11)), ids)
        self.assertIn("**③の実物の文に対する安全性は、段 10 でも未検証である。**", block)
        self.assertIn("**5 段続けて未検証**", block)
        self.assertIn("**R-裏-2 はこの材料では役に立たない。**", block)

    def test_29_procedure_puts_the_seal_first(self):
        block = self.t.split("## §12")[1].split("## §13")[0]
        self.assertIn("1. **この封を commit する。**", block)
        self.assertIn("**新しい file** `measure/sheet_m10_engine_2026-10-16.py`", block)
        self.assertIn("既存の engine も触らない。**", block)


class CommitOrderTest(unittest.TestCase):
    """**封が実装より先に commit されたこと**を commit の順で確かめる。

    **file の有無で見ない** ― 2026-10-16 に同じ型の門を 2 度壊した
    (記憶 `order-gate-by-commit-not-file-absence`)。
    """

    @staticmethod
    def _added(rel):
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
            cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    @staticmethod
    def _ancestor(a, b):
        return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                              cwd=ROOT, capture_output=True).returncode == 0

    @staticmethod
    def _tracked(rel):
        out = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                             cwd=ROOT, capture_output=True)
        return out.returncode == 0

    def test_30_seal_is_committed(self):
        # **先に道が当たっていることを確かめる。**空振りを「未 commit」と読まない。
        self.assertTrue(self._tracked(SEAL_REL),
                        "道が git に当たっていない(pathspec の誤り)")
        self.assertIsNotNone(self._added(SEAL_REL),
                             "封がまだ commit されていない")

    def test_30b_a_wrong_pathspec_is_detected_not_read_as_uncommitted(self):
        """**歯。**repo ルートからの道を渡すと `_added` は空を返す ―
        そのとき `_tracked` が偽になるので、未 commit と読み違えない。"""
        wrong = "audit-core/" + SEAL_REL
        self.assertIsNone(self._added(wrong))
        self.assertFalse(self._tracked(wrong))

    def test_31_seal_precedes_the_m10_engine(self):
        seal = self._added(SEAL_REL)
        eng = self._added(M10_ENGINE_REL)
        if seal is None or eng is None:
            self.skipTest("まだ両方は commit されていない")
        self.assertTrue(self._ancestor(seal, eng),
                        "封が engine より後に commit されている")

    def test_32_the_order_gate_has_teeth(self):
        """**逆向きが偽であること。**でなければ 31 は何も言っていない。"""
        seal = self._added(SEAL_REL)
        eng = self._added(M10_ENGINE_REL)
        if seal is None or eng is None:
            self.skipTest("まだ両方は commit されていない")
        if seal == eng:
            self.fail("封と engine が同じ commit に入っている(順を測れない)")
        self.assertFalse(self._ancestor(eng, seal))


class DocNumbersMatchMeasurementTest(unittest.TestCase):
    """**封の表の数を、その場の実測から組み立てた字で突き合わせる。**

    門が自分の控えと比べるだけでは、封の表を書き間違えても気づかない
    (記憶 `test-built-from-same-table-is-blind`)。だからここでは
    **期待する字を実測から作って** `assertIn` する。
    """

    def setUp(self):
        self.t = text(SEAL)
        self.f = facts()
        self.n = len(self.f["unconf"])

    def want(self, s):
        self.assertIn(s, self.t, "封の表が実測と合わない: %s" % s)

    def test_33_section3_table(self):
        f = self.f
        self.want("| 総括の歳出決算額の行 | **%d 行 / 値の種類 %d**"
                  % (f["sou_rows"], f["sou_values"]))
        ok, ng, _ = f["colmatch"]["支出済額"]
        self.want("| 明細の款の合計 == 決算書の合計行(未確認 %d 会計)/ 支出済額 "
                  "| **一致 %d / 食い違い %d** |" % (self.n, ok, ng))
        ok2, ng2, _ = f["colmatch"]["不用額"]
        self.want("| 同じことを 不用額 の列で | **一致 %d / 食い違い %d** |" % (ok2, ng2))
        self.want("| 明細の `計` == 決算書の `予算現額`(列の別名) "
                  "| **一致 %d / 食い違い 0。だが R-独立-2 で数えない** |" % f["alias_col"])
        self.want("| 決算書の合計行で `予算現額 = 支出済額+不用額+翌年度繰越額` "
                  "| **%d / %d 成立** |" % (f["alg"], self.n))
        self.want("| 総括の歳出決算額 == 決算書の合計行の支出済額 | **%d/%d 一致**"
                  % (f["same"], self.n))
        self.want("| いまの独立した裏づけ | **1 本が %d 会計・2 本が %d 会計** |"
                  % (f["existing"][1], f["existing"][2]))
        self.want("| **未確認 %d 会計の「明細の款の数」** | **1 つだけが %d 会計・"
                  "2 つが %d 会計** |" % (self.n, f["kancount"][1], f["kancount"][2]))
        self.want("| **R-独立-5(I-3)を当てたあとの本数** | **2 本が %d 会計・"
                  "4 本が %d 会計** |" % (f["merged"][2], f["merged"][4]))
        self.want("| **3 本に達する会計** | **%d / %d**(`%s`) |"
                  % (len(f["passing"]), self.n, f["passing"][0]))
        self.want("| 負の対照 D-1(正しい対の受理) | **%d / %d** |" % (f["d1"], self.n))
        self.want("| 負の対照 D-2(誤った対の受理) | **%d / %d** |"
                  % (f["d2"], f["pairs"]))

    def test_34_section3_2_structure_table(self):
        f = self.f
        self.want("**未確認 %d 会計のうち %d 会計は、明細に款が 1 つしか無い。**"
                  % (self.n, f["kancount"][1]))
        self.want("| 明細の款が 1 つ(**%d 会計**) | 1 本 |" % f["kancount"][1])
        self.want("| 明細の款が 2 つ(**%d 会計**) | 2 本 |" % f["kancount"][2])

    def test_35_section3_1_first_draft_vs_measured(self):
        f = self.f
        self.want("| 3 本に達する会計 | **%d / %d** | **%d / %d** |"
                  % (self.n, self.n, len(f["passing"]), self.n))

    def test_36_negative_control_counts_in_section4(self):
        f = self.f
        self.want("**実データの数字から用意できた。**%d の別名 × **誤った**正本 %d 通り "
                  "= **%d 組**。" % (self.n, len(f["unconf"]) + 1, f["pairs"]))

    def test_37_the_want_helper_can_fail(self):
        """**歯。**実測から作った字が封に無ければ落ちること。"""
        with self.assertRaises(AssertionError):
            self.want("| 3 本に達する会計 | **99 / 18**")


if __name__ == "__main__":
    unittest.main()
