# -*- coding: utf-8 -*-
"""C′ 対 D′ の封(docs/XBRL_CD_SEAL_2026-10-17.md)を固定する。

守るのは 9 つ(封 §11)。
**8 件の docID は封の表から読まず、規則を独立に実装して突き合わせる**
(表に書いた私が選んでいないことの証拠)。
"""
import hashlib
import io
import os
import random
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_CD_SEAL_2026-10-17.md"
SEAL = os.path.join(ROOT, SEAL_REL)
HP = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
DOC_RE = re.compile(r"S100[A-Z0-9]{4}")
SEED_HEX = "6a24d72"
NEED = 8

# 母集団を列挙しているだけの file(封 §1-2)
ROSTER = {
    "fixtures/xbrl/holdout_p17/pool2_clean_2026-10-14.json",
    "fixtures/xbrl/holdout_p17/fetched_not_read_2026-10-14.json",
    "fixtures/xbrl/holdout_p17/pool_meta_2026-10-14.json",
    "fixtures/xbrl/holdout_p17/pool2_meta_2026-10-14.json",
}
# この便で作る file(封 §1-2)
THIS_RUN = {
    SEAL_REL,
    "fixtures/xbrl/cd8/draw_2026-10-17.json",
    "docs/XBRL_CD_RESULT_2026-10-17.md",
    "docs/XBRL_CD_DRYRUN_2026-10-17.md",
    "tests/measure/test_xbrl_cd_seal.py",
    "tests/measure/test_xbrl_cd.py",
    "measure/xbrl_cd_draw_2026-10-17.py",
    # 下見(封 §1-2 の「およびこの便で作る file」)
    "measure/xbrl_cd_dryrun_2026-10-17.py",
    "fixtures/xbrl/cd8/dryrun_2026-10-17.json",
    "tests/measure/test_xbrl_cd_dryrun.py",
}

# 封 G-9。**engine と道具が動いたら赤くなる**
FROZEN = {
    "measure/inject.py": "92d34774c4cc76bb",
    "measure/prepare_material.py": "b1a0010df9bc725d",
    "measure/grounds_eval.py": "bff2778d45f29051",
    "adapters/xbrl/extract.py": "68a78f99f4d4c216",
    "adapters/xbrl/instance.py": "2805441b7812033e",
    "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
    "adapters/xbrl/vocabulary.py": "bcf559308bda0cc6",
    "measure/SEED.json": "f74146592f68b88d",
}

# 2026-10-19 追記(封 G-9 の値は消さない)。**宣言された遷移**: 封 `docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md`
# (commit `ae528a4`、独立監査 GO)により `instance.py` に枠の軸 `axes` が足された(既存の鍵は不変)。
# 上の値は 10-17 の便でのものとして正しい。いまの値はこの表で、**その封が履歴に在るときだけ**受け入れる
# (`fixtures/frozen_bundle_sha.py` の世代と同じ型: 「ずれ」と「宣言された遷移」を言い分ける)。
FROZEN_LATER = {
    "adapters/xbrl/instance.py": ("f2d9e040f19adebf", "docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md"),
    # 2026-10-20: 封 `docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md`(名指しの直し P21)で vocabulary.py に旗 last_branch_cues と P21 が足された。
    # 2026-10-20(段 2): 既定を P20 -> P21 にした(vocabulary.py の DEFAULT_PROFILE と決定の注記。同じ封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md の段 2)。
    # vocabulary.py の sha は 段 1 5eb80a2 のとき 6c6db4c75e571a6c(残す。段 1 の結果の記録が測った時点の値)、段 2 で 1205b30b496090ef。
    # 受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    # 2026-10-20(期を縛る P22 の段 1): 同じ封で vocabulary.py に旗 period_bind と P22 を足した(DEFAULT_PROFILE は P21 のまま)。
    # sha は 段 1 5eb80a2 で 6c6db4c75e571a6c・名指しの直し 段 2 で 1205b30b496090ef(どちらも残す。測った時点の値)、P22 の段 1 で 1fdb48e7e3ba58ce。
    "adapters/xbrl/vocabulary.py": ("1fdb48e7e3ba58ce", "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md"),
    # 2026-10-20(席と Core の一致の信頼 段 2): measure/inject.py に型 T6_PRIOR・T7_ROUND と select の quota・fallback を足した
    # (既存の型 T1/T2/T3/T5・MACHINE_TYPES・TYPE_POLICY・types を明示しない呼び出しの結果は不変。封 §4。司令塔の承認 2026-10-20)。
    # 封 G-9 の 92d34774c4cc76bb は消さない(10-17 の便の値)。受け入れるのは、その封が履歴に在り、値が足した後の値のときだけ。
    "measure/inject.py": ("211e37d028f46cf7", "docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md"),
}


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


def sealed_order():
    """封 431f436 の算法で並びを作り直し、**3 群の再現を確かめてから**返す。"""
    import json
    pool = json.load(io.open(os.path.join(HP, "pool2_clean_2026-10-14.json"),
                             encoding="utf-8"))["pool_clean"]
    order = sorted(pool)
    random.Random(int(SEED_HEX, 16)).shuffle(order)
    sp = json.load(io.open(os.path.join(HP, "split_2026-10-14.json"),
                           encoding="utf-8"))
    assert order[0:6] == sp["used"], "使用済み 6 件が再現しない"
    assert order[6:14] == sp["development"], "開発 8 件が再現しない"
    assert order[14:22] == sp["final_eval_sealed"], "最終評価 8 件が再現しない"
    assert sp["reserve_n"] == len(order) - 22, "予備の件数が合わない"
    return order


def seal_commit():
    """封を足した commit。**「この便で作る file」をここで切る。**"""
    out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--",
                          SEAL_REL], cwd=ROOT, capture_output=True, text=True)
    shas = [s for s in out.stdout.split() if s]
    return shas[-1] if shas else None


def mentioned_outside_roster():
    """名簿を除いて、**封の commit の時点で**名前が出ていた docID -> その file。

    **封より後に足した file を数えない。**封 §1-2 の「およびこの便で作る file」を
    **commit の順で**書いた形である(字の一覧で書くと、後から file を足すたびに
    この門が壊れる ― 2026-10-17 に 2 回壊した)。
    """
    sha = seal_commit()
    assert sha, "封がまだ commit されていない"
    names = subprocess.run(["git", "ls-tree", "-r", "--name-only", sha],
                           cwd=ROOT, capture_output=True, text=True).stdout.split()
    out = {}
    for f in names:
        if f in ROSTER or f in THIS_RUN:
            continue
        if f.endswith((".xlsx", ".zip", ".png", ".pdf")):
            continue
        # **`:./path` は cwd から解く。**`sha:path` は repo の根から解くので、
        # 下位ディレクトリで走らせると 1 件も読めずに「言及 0 件」になる
        # (2026-10-17 に実際そうなり、引く 8 件が別の 8 件に変わった)
        blob = subprocess.run(["git", "show", "%s:./%s" % (sha, f)], cwd=ROOT,
                              capture_output=True)
        if blob.returncode != 0:
            continue
        try:
            body = blob.stdout.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for d in set(DOC_RE.findall(body)):
            out.setdefault(d, f)
    return out


class DrawTest(unittest.TestCase):
    def test_1_the_eight_docs_are_reproduced_by_the_rule(self):
        """封 G-2。**表の 8 件は、規則の独立な実装と一致する。**"""
        order = sealed_order()
        seen = mentioned_outside_roster()
        drawn = [d for d in order[22:] if d not in seen][:NEED]
        self.assertEqual(len(drawn), NEED, "規則で 8 件そろわない")
        b = sec(text(SEAL), "### §1-2", "## §2")
        listed = re.findall(r"(?m)^\| \d \| `(S100[A-Z0-9]{4})` \|", b)
        self.assertEqual(listed, drawn, "**封の表が規則の結果と違う(選んでいる)**")

    def test_2_the_reserve_head_is_recorded_as_consumed(self):
        """封 §1-1。**`order[22:30]` が使えないことを実測で言う。**"""
        order = sealed_order()
        seen = mentioned_outside_roster()
        consumed = [d for d in order[22:30] if d in seen]
        self.assertEqual(len(consumed), 8, "8 件すべてが言及されているはず")
        b = sec(text(SEAL), "### §1-1", "### §1-2")
        self.assertIn("**`order[22:30]` は使えない(測って分かった)**", b)
        self.assertIn("`order[26:34]` を使った", b)

    def test_3_the_eight_docs_have_never_been_fetched(self):
        """封 G-3。取得の記録が commit されるまで、キャッシュに在ったら赤。"""
        rec = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "fetched_2026-10-17.json")
        if os.path.exists(rec):
            self.skipTest("取得の記録が在る(開封後)")
        b = sec(text(SEAL), "### §1-2", "## §2")
        listed = re.findall(r"(?m)^\| \d \| `(S100[A-Z0-9]{4})` \|", b)
        self.assertEqual(len(listed), NEED)
        if not os.path.isdir(CACHE):
            return
        names = "\n".join(os.listdir(CACHE))
        for d in listed:
            self.assertNotIn(d, names, "**%s が既にキャッシュに在る**" % d)


class ArmsAndScoringTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_4_five_arms_sharing_one_generation(self):
        b = sec(self.t, "## §4 腕", "### §4-1")
        ids = re.findall(r"(?m)^\| \*\*(A|B|C′|D′|D″)\*\*", b)
        self.assertEqual(ids, ["A", "B", "C′", "D′", "D″"], "腕は 5 つ")
        self.assertIn("**A・C′・D′・D″ は 1 回の生成を共有する。入力の差はゼロである。**", b)
        self.assertIn("**席は 1 席。**", b)
        self.assertIn("複数の LLM の一致を証拠に数えない", b)

    def test_5_dprime_is_defined_in_five_rows_and_composition_in_four(self):
        b = sec(self.t, "### §4-1", "### §4-2")
        rows = [l for l in b.splitlines()
                if l.startswith("| ") and not l.startswith("|---")
                and "| 字 |" not in l]
        self.assertEqual(len(rows), 5, "D′ の定義は 5 項目")
        self.assertIn("**しない**(element の名前・context の期間・連結/個別・member "
                      "を見ない)", b)
        self.assertIn("**単位の倍率換算をしない**", b)
        d2 = sec(self.t, "### §4-2", "### §4-3")
        self.assertIn("**Core の丸め規約(`profile.doc_rounding`)は使わない**", d2)
        c = sec(self.t, "### §4-3", "## §5")
        nums = re.findall(r"(?m)^(\d)\. ", c)
        self.assertEqual(nums, ["1", "2", "3", "4"], "合成の規則は 4 条")
        self.assertIn("**席が「誤りが在る」と言ったら、その申告はそのまま残る。**", c)

    def test_6_five_independent_counts(self):
        b = sec(self.t, "## §5 採点", "### §5-1")
        ids = re.findall(r"(?m)^\| \*\*(検出|見落とし|保留|偽警報|種類)\*\*", b)
        self.assertEqual(ids, ["検出", "見落とし", "保留", "偽警報", "種類"])
        self.assertIn("**排他**", b)

    def test_7_two_pointer_rates_with_different_denominators(self):
        """人間の条件。**特定率と誤認定率を 1 つにまとめない。**"""
        b = sec(self.t, "### §5-1", "### §5-2")
        ids = re.findall(r"(?m)^\| \*\*(P-特定率|P-誤認定率)\*\*", b)
        self.assertEqual(ids, ["P-特定率", "P-誤認定率"])
        self.assertIn("**T5 の件数**", b)
        self.assertIn("**参照先を出した件数**", b)
        self.assertIn("**この 2 つを 1 つの率にまとめない。**", b)
        for k in ("**T5**:", "**T3**:", "**T1**:"):
            self.assertIn(k, b, k)

    def test_8_gold_is_element_and_context_not_value(self):
        b = sec(self.t, "### §5-2", "### §5-3")
        self.assertIn("**`(element の局所名, context)` の集合として厳密一致。**", b)
        self.assertIn("**値の一致は正解にしない。**", b)
        self.assertIn("`unit` は別の欄として一致を要求する", b)
        s = sec(self.t, "### §5-3", "## §6")
        ids = re.findall(r"(?m)^\| \*\*(n = 1|n = 2〜5|n ≥ 6)\*\*", s)
        self.assertEqual(ids, ["n = 1", "n = 2〜5", "n ≥ 6"], "層は 3 つ")

    def test_9_symmetry_four_rules(self):
        b = sec(self.t, "## §6 対称性", "## §7")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, ["1", "2", "3", "4"])
        self.assertIn("**結果を見てから、どちらの側にも例外規則・正規化・閾値を"
                      "足さない。**", b)


class PredictAndStopTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_10_ten_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §7 予測", "## §8")
        rows = re.findall(r"(?m)^\| \*\*X-(\d+)\*\* \| (.+?) \| (.+?) \|$", b)
        self.assertEqual([r[0] for r in rows], [str(i) for i in range(1, 11)])
        for num, pred, how in rows:
            self.assertTrue(pred.strip(), num)
            self.assertTrue(len(how.strip()) >= 4, "X-%s の外れ方が薄い" % num)
        self.assertIn("**X-2 が外れたら、「Core が参照先で勝る」という見立ては、"
                      "この標本では支持されない。**", b)

    def test_11_six_stops_and_seven_limits_and_the_four_stages(self):
        b = sec(self.t, "## §8 止める条件", "## §9")
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 7)], "止める条件は 6 本")
        self.assertIn("**規模を自分で勝手に削らない**", b)
        st = sec(self.t, "## §9 工程", "## §10")
        self.assertEqual(re.findall(r"(?m)^\| \*\*(\d)\*\*", st), ["1", "2", "3", "4"])
        self.assertIn("**費用の実測見積もりを報告して止まる**", st)
        li = sec(self.t, "## §10 示せないこと", "## §11")
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", li),
                         [str(i) for i in range(1, 8)], "限界は 7 本")
        g = sec(self.t, "## §11 門")
        self.assertEqual(re.findall(r"(?m)^\| \*\*(G-\d)\*\*", g),
                         ["G-%d" % i for i in range(1, 10)], "G-1〜G-9")


class FrozenToolsTest(unittest.TestCase):
    def test_12_engine_and_tools_have_not_moved(self):
        """封 G-9。**この便で engine・採点器・注入の規則を直したら赤くなる。**"""
        for rel, want in FROZEN.items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()[:16]
            if got != want and rel in FROZEN_LATER:
                # 2026-10-19 追記: 宣言された遷移(上の FROZEN_LATER)。封が履歴に在り、値がその封の値のときだけ通す
                later, seal_rel = FROZEN_LATER[rel]
                added = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", seal_rel],
                                       cwd=ROOT, capture_output=True, text=True).stdout.split()
                self.assertTrue(added, "**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, "**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, "**%s が動いている**" % rel)


class CommitOrderTest(unittest.TestCase):
    AFTER = ("measure/xbrl_cd_draw_2026-10-17.py",
             "fixtures/xbrl/cd8/draw_2026-10-17.json",
             "docs/XBRL_CD_DRYRUN_2026-10-17.md",
             "docs/XBRL_CD_RESULT_2026-10-17.md")

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

    def test_13_seal_precedes_everything(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        self.assertTrue(tracked, "pathspec の誤り")
        seal = self._added(SEAL_REL)
        self.assertIsNotNone(seal, "封がまだ commit されていない")
        for rel in self.AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, "同じ commit に在る: %s" % rel)
            self.assertTrue(self._ancestor(seal, other), rel)
            self.assertFalse(self._ancestor(other, seal))


if __name__ == "__main__":
    unittest.main()
