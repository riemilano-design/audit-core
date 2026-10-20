# -*- coding: utf-8 -*-
u"""丸めの帯を直す(P23 = P22 + 率の旗(既存)+ 切り捨ての帯の旗(新 `truncate_abs_band`))の封
docs/XBRL_ROUNDING_SEAL_2026-10-21.md を固定する。
人間の承認の引用・予測 R-1〜R-7 と外れ方・§0 の数(字・記録の値・算術。cache が在る機械では AUDIT_CORE_ROUNDING=1 で実走)・
§1 の旗の形と「`truncate_on_magnitude` を積まない」・触る枝の中の人間の決定・過去の門の engine の留めの一覧・
§4 の file 一覧と順序・封が実装より先であること(順序)・**封の commit 時点の engine の sha**を縛る。

**この門の engine の留め(test_11・test_12)は、段 1 の commit で「宣言された遷移」に更新する前提である。**
この封は engine(adapters/xbrl/vocabulary.py・comparators.py・recipes.py)を変える封なので、段 1 で sha が動く。そのとき
`ENGINE_LATER` に (段 1 の後の sha16, この封の path) を足し、`test_12` の「`truncate_abs_band` は Profile に無い・P23 は PROFILES に無い」を
「`truncate_abs_band` は Profile に在り P23 だけが真・P23 は PROFILES に在り、DEFAULT_PROFILE は P22 のまま」に直す
(他の pin 6 本・axis3 の LATER_ENGINE_COMMITS・cd_seal の FROZEN_LATER・frozen_bundle の世代も同じ段 1 の commit で宣言する ― 封 §1 の一覧)。
段 2(既定 P22 → P23)でもう一度、`DEFAULT_PROFILE` の assert を直す。

**実走(AUDIT_CORE_ROUNDING=1)が数えるのは「率の旗だけを in-process の replace で P22 に積んだ profile」**(= 封 §0 の
「率の旗だけ」の数。新しい旗はまだ無いので、旗 2 つの P23 そのものは数えられない)。engine の file は書き換えない。"""
import contextlib
import dataclasses
import glob
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
RITUAL_P21_JSON = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20_p21.json")
RITUAL_P22_JSON = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20.json")
PERIOD_BIND_JSON = os.path.join(ROOT, "fixtures", "xbrl", "period_bind_2026-10-20.json")
POINT_PRIOR_JSON = os.path.join(ROOT, "fixtures", "xbrl", "point_prior_2026-10-20.json")
RITUAL_ZIP = os.path.join(ROOT, "fixtures", "xbrl", "ai_prose_instance_2026-10-09.zip")
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

# §4 の file 一覧(この順で書かれている)
ENGINE_FILES = ("adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py")
FILES = ("tests/adapters/xbrl/test_recipes_p23.py",
         "measure/xbrl_rounding_2026-10-21.py",
         "fixtures/xbrl/rounding_2026-10-21.json",
         "docs/XBRL_ROUNDING_RESULT_2026-10-21.md",
         "tests/measure/test_xbrl_rounding_result.py")
# 封より後でなければ git 履歴に現れてはならない新規 file(§4 の 5 本そのもの)
AFTER = FILES

# 封の commit 時点の engine(sha256 の先頭 16 桁)。**ここは宣言された遷移の前の値**で、消さない。
ENGINE_AT_SEAL = {"adapters/xbrl/vocabulary.py": "25a3c0992e10daaa",
                  "adapters/xbrl/comparators.py": "d8706338325e725b",
                  "adapters/xbrl/recipes.py": "65a37869f053a60e"}
# 宣言された遷移(段 1 の commit で足す): {path: (後の sha16, 遷移を宣言した封の path)}。封の commit 時点では空。
ENGINE_LATER = {}

# §1「過去の門の engine の留め」の一覧(封の字)と、実物の在りか
PIN_FILES_ENGINE_LATER = ("tests/measure/test_xbrl_branch_a.py", "tests/measure/test_xbrl_role_swap_result.py",
                          "tests/measure/test_xbrl_axis3_decision.py", "tests/measure/test_xbrl_p20_result.py",
                          "tests/measure/test_xbrl_a_core_vs_grep_seal.py", "tests/measure/test_xbrl_pnf_diag.py")
OTHER_PINS = {"tests/measure/test_xbrl_axis3_decision.py": "LATER_ENGINE_COMMITS",
              "tests/measure/test_xbrl_cd_seal.py": "FROZEN_LATER",
              "fixtures/frozen_bundle_sha.py": "FROZEN_BUNDLE_GENERATIONS"}

RITUAL_PASSED_P21 = ["N033", "N069", "N011", "N096", "N017", "N031", "N037", "N045", "N113", "N125", "N199",
                     "N131", "N177", "N237", "N251", "N225", "N277"]


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i + 1) if end else len(t)
    return t[i:j]


def predictions(block, tag):
    ids = re.findall(r"(?m)^\| \*\*%s-(\d+)\*\* \|" % tag, block)
    lines = re.findall(r"(?m)^\| \*\*%s-\d+\*\* \|.*$" % tag, block)
    return ids, lines


def s0(t):
    return sec(t, "## §0 ", "## §1")


def num(s):
    return int(s.replace(",", ""))


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def s0_numbers(b):
    """§0 の数を、書かれた字のまま取り出す(書き方が変わったら落ちる)。"""
    m1 = re.search(r"通した 17: 率 (\d+) は.*?金額 (\d+) のうち", b)
    m2 = re.search(r"字の方針は (\d+) 書類\(切り捨て (\d+)・四捨五入 (\d+)\)しか取れず.*?金額 (\d+) 行\(([\d.]+)%\)が落ちる", b)
    m3 = re.search(r"67 書類 ([\d,]+) 行・儀式 (\d+) 行で 0", b)
    m4 = re.search(r"旗 2 つ = 儀式 通した (\d+) / (\d+)\(N069・N096\)、67 書類の代価 (\d+)\(金額 (\d+)・％ (\d+)・ポイント (\d+)\)", b)
    m5 = re.search(r"率の旗だけ = 儀式 (\d+) / (\d+)\(N069・N096・N237・N277\)、代価 (\d+)\(％ (\d+)・ポイント (\d+)\)、VALUE_MISMATCH ([\d,]+) → ([\d,]+)", b)
    m6 = re.search(r"3 書類\(S100YZ7E・S100Z38F・S100Z48T\)で切り捨て → 四捨五入に反転して金額 (\d+) 行が落ちる", b)
    m7 = re.search(r"儀式 17 のうち止まる (\d+)\(残り (\d+) = N096 退化値・N125・N199\)、素の (\d+) claim の代価 (\d+)", b)
    m8 = re.search(r"67 書類\(素の GROUNDED ([\d,]+)\)の代価 (\d+)\(％ (\d+)・ポイント (\d+)、(\d+) 書類、([\d.]+)%\)、金額 (\d+)", b)
    m9 = re.search(r"V5 は (\d+) 行落ちて悪化", b)
    assert m1 and m2 and m3 and m4 and m5 and m6 and m7 and m8 and m9, u"§0 の数の書き方が変わった"
    return {"ritual_rate": int(m1.group(1)), "ritual_money": int(m1.group(2)),
            "policy_docs": int(m2.group(1)), "policy_trunc": int(m2.group(2)), "policy_round": int(m2.group(3)),
            "round_cost": int(m2.group(4)), "round_cost_rate": float(m2.group(5)),
            "dec_rows": num(m3.group(1)), "dec_ritual": int(m3.group(2)),
            "both_pass": int(m4.group(1)), "both_den": int(m4.group(2)), "both_cost": int(m4.group(3)),
            "both_money": int(m4.group(4)), "both_pct": int(m4.group(5)), "both_pt": int(m4.group(6)),
            "pct_pass": int(m5.group(1)), "pct_den": int(m5.group(2)), "pct_cost": int(m5.group(3)),
            "pct_pct": int(m5.group(4)), "pct_pt": int(m5.group(5)), "vm_before": num(m5.group(6)), "vm_after": num(m5.group(7)),
            "flip_money": int(m6.group(1)),
            "v3_stopped": int(m7.group(1)), "v3_left": int(m7.group(2)), "v3_claims": int(m7.group(3)), "v3_plain_cost": int(m7.group(4)),
            "grounded_p21": num(m8.group(1)), "v3_cost": int(m8.group(2)), "v3_pct": int(m8.group(3)), "v3_pt": int(m8.group(4)),
            "v3_docs": int(m8.group(5)), "v3_rate": float(m8.group(6)), "v3_money": int(m8.group(7)),
            "v5_cost": int(m9.group(1))}


class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)

    def test_1_human_approval_is_quoted_and_the_seal_says_it_changes_the_engine(self):
        head = self.t[:self.t.index("\n## §0 ")]
        self.assertIn(u"**この封は engine(`adapters/xbrl/vocabulary.py`)を変える。人間の承認(2026-10-21 深夜)", head)
        self.assertIn(u"人間「engine に触るので承認が要る → 先に承認しておくので好きに進めて これをもって承認とする」", head)
        self.assertIn(u"作法は変えない(封 → 実装 → 凍結 → 独立監査 GO → commit)。", head)
        self.assertIn(u"数を見てから封・予測を直さない。外れは外れとして残す。**", head)

    def test_2_seven_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §2", "## §3")
        ids, lines = predictions(b, "R")
        self.assertEqual(ids, [str(i) for i in range(1, 8)])
        self.assertEqual(len(lines), 7)
        for line in lines:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[1], u"予測が空: " + line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        by = dict((i, l) for i, l in zip(ids, lines))
        # 行ごとに、予測の幅と外れ方の両方を字で縛る(幅を直すと赤くなる)
        for i, ss in (("1", (u"儀式 240 件を P23 で", u"通した **2〜3 / 240**", u"止めた **237〜238**",
                             u"N237・N277(負の金額の符号つき切り捨て)は止まる", u"通した 4 以上 / N237・N277 が通る")),
                      ("2", (u"**6〜12**", u"うち金額 **0**", u"全部 率(％・ポイント)", u"新 GROUNDED **0**",
                             u"書類ごとの丸め方の判定(R/T)は 67 書類で **1 つも変わらない**",
                             u"幅の外 / 金額 1 以上 / 新 GROUNDED 1 以上 / 判定が変わる書類 1 以上")),
                      ("3", (u"穴 B の 485 件", u"通す **0〜2 / 485**", u"P22 の 1 から", u"3 以上")),
                      ("4", (u"無改変の VALUE_MISMATCH 1,410(P22)", u"**1,416〜1,422**", u"幅の外")),
                      ("5", (u"192 行", u"Core 自身は **1 行も動かない**", u"1 行以上")),
                      ("6", (u"`vocabulary.py` **≤ 20 行**", u"`comparators.py` **≤ 10 行**", u"`recipes.py` **≤ 10 行**",
                             u"`core/` 0 行", u"旗が偽なら 1 行も変わらない(P22 明示の数は不変)",
                             u"登録の一覧の試験 4 か所に P23 を足す以外の既存試験は全部緑", u"超える / 赤 / P22 が動く")),
                      ("7", (u"既定の切り替えは P24・P25 とまとめて人間に諮る", u"通した 2〜3 / 240 が先頭に", u"赤が残る"))):
            for s in ss:
                self.assertIn(s, by[i], u"R-%s: %s" % (i, s))
        self.assertIn(u"**本当に測っているのは R-1・R-2 である**", b)

    def test_3_prediction_arithmetic_is_consistent(self):
        """幅どうしの算術(R-1 の止めた = 240 - 通した、R-4 = 1,410 + R-2)。片方だけ直すと赤くなる。"""
        b = sec(self.t, "## §2", "## §3")
        _, lines = predictions(b, "R")
        r1 = re.search(r"通した \*\*(\d+)〜(\d+) / 240\*\*.*止めた \*\*(\d+)〜(\d+)\*\*", lines[0])
        r2 = re.search(r"\*\*(\d+)〜(\d+)\*\*", lines[1])
        r4 = re.search(r"\*\*([\d,]+)〜([\d,]+)\*\*", lines[3])
        self.assertTrue(r1 and r2 and r4)
        p_lo, p_hi, s_lo, s_hi = [int(x) for x in r1.groups()]
        self.assertEqual((s_lo, s_hi), (240 - p_hi, 240 - p_lo))
        lo, hi = int(r2.group(1)), int(r2.group(2))
        self.assertEqual((num(r4.group(1)), num(r4.group(2))), (1410 + lo, 1410 + hi))

    def test_4_section_0_numbers_are_pinned_as_written(self):
        b = s0(self.t)
        n = s0_numbers(b)
        self.assertEqual((n["ritual_rate"], n["ritual_money"]), (12, 4))
        self.assertEqual(n["ritual_rate"] + n["ritual_money"], 16)      # 帯の中 16 + 退化値 1 = 17(記録で突き合わせる)
        self.assertEqual((n["policy_docs"], n["policy_trunc"], n["policy_round"]), (5, 4, 1))
        self.assertEqual(n["policy_trunc"] + n["policy_round"], n["policy_docs"])
        self.assertEqual((n["round_cost"], n["round_cost_rate"]), (339, 7.9))
        self.assertEqual(round(100.0 * 339 / 4267, 1), 7.9)
        self.assertEqual((n["dec_rows"], n["dec_ritual"]), (2512, 221))
        # 旗 2 つ(本物)= 2 / 240、67 書類の代価 63 = 金額 55 + ％ 7 + ポイント 1。金額 55 は丸め方の判定が反転した 3 書類
        self.assertEqual((n["both_pass"], n["both_den"]), (2, 240))
        self.assertEqual((n["both_cost"], n["both_money"], n["both_pct"], n["both_pt"]), (63, 55, 7, 1))
        self.assertEqual(n["both_money"] + n["both_pct"] + n["both_pt"], n["both_cost"])
        self.assertEqual(n["flip_money"], n["both_money"])
        # 率の旗だけ = 4 / 240、代価 8 = ％ 7 + ポイント 1、VALUE_MISMATCH 1,410 -> 1,418
        self.assertEqual((n["pct_pass"], n["pct_den"]), (4, 240))
        self.assertEqual((n["pct_cost"], n["pct_pct"], n["pct_pt"]), (8, 7, 1))
        self.assertEqual(n["pct_pct"] + n["pct_pt"], n["pct_cost"])
        self.assertEqual((n["vm_before"], n["vm_after"]), (1410, 1418))
        self.assertEqual(n["vm_before"] + n["pct_cost"], n["vm_after"])
        # 下調べの V3(帯だけ。率 ±0.05)
        self.assertEqual((n["v3_stopped"], n["v3_left"], n["v3_claims"], n["v3_plain_cost"]), (14, 3, 412, 0))
        self.assertEqual(17 - n["v3_left"], n["v3_stopped"])
        self.assertEqual((n["grounded_p21"], n["v3_cost"], n["v3_pct"], n["v3_pt"], n["v3_docs"], n["v3_rate"], n["v3_money"]),
                         (4267, 14, 13, 1, 9, 0.3, 0))
        self.assertEqual(n["v3_pct"] + n["v3_pt"], n["v3_cost"])
        self.assertEqual(round(100.0 * 14 / 4267, 1), 0.3)
        self.assertEqual(n["v5_cost"], 85)
        for s in (u"`tol_of` は呼び出し元なし", u"P20〜P22 に積まれていない",
                  u"N125・N199 は前期へ移った(P22 で止まる)", u"N096 は 0 → 00 の退化値",
                  u"字の方針は使わない", u"`decide_rounding` の判定の軸も変え",
                  u"1 桁で ±0.06(0.5·10^-d + 0.01、recipes.py 182〜191 行)で ±0.05 ではない",
                  u"**司令塔の判断: 率の旗は既存のまま積み、切り捨ては「照合の帯だけ絶対値で片側」の新しい旗にする(判定は P22 のまま)= 下調べの V3 の形。**",
                  u"司令塔の席の手元の数。正本でない"):
            self.assertIn(s, b, s)

    def test_5_section_0_numbers_match_the_records(self):
        n = s0_numbers(s0(self.t))
        p21 = jload(RITUAL_P21_JSON)
        p22 = jload(RITUAL_P22_JSON)
        # 儀式 P21: 17 件 = 帯の中 16(率 12・金額 4)+ 退化値 1
        self.assertEqual(p21["通した"]["件"], 17)
        self.assertEqual([x["id"] for x in p21["通した の一覧"]], RITUAL_PASSED_P21)
        band = p21["通した の分け方"]["丸めの帯の中(±1 最小単位)"]
        self.assertEqual((band["件"], band["うち率(単位が %)"], band["うち金額ほか(単位が % でない)"]), (16, n["ritual_rate"], n["ritual_money"]))
        deg = p21["通した の分け方"]["退化値(字は変わるが値が変わらない)"]
        self.assertEqual(deg["件"], 1)
        rows = dict((x["id"], x) for x in p21["通した の一覧"])
        self.assertEqual(rows["N096"]["分類"], u"退化値(字は変わるが値が変わらない)")
        self.assertEqual((rows["N096"]["元の字"], rows["N096"]["後の字"]), (u"0百万円", u"00百万円"))
        # 負の金額: 符号つきの切り捨てが通した
        self.assertEqual((rows["N237"]["元の字"], rows["N237"]["後の字"]), (u"△22百万円", u"△23百万円"))
        self.assertEqual((rows["N277"]["元の字"], rows["N277"]["後の字"]), (u"△780百万円", u"△781百万円"))
        self.assertEqual([i for i in RITUAL_PASSED_P21 if rows[i]["単位"] == u"%"].__len__(), n["ritual_rate"])
        # N125・N199 は前期へ移って通した(P22 で止まる)
        self.assertEqual(sorted(i for i in rows if rows[i]["参照先が動いた"]), ["N125", "N199"])
        # 儀式 P22: 15 / 240 = P21 の 17 から N125・N199 を除いたもの
        self.assertEqual((p22["通した"]["件"], p22["通した"]["分母"]), (15, 240))
        self.assertEqual([x["id"] for x in p22["通した の一覧"]], [i for i in RITUAL_PASSED_P21 if i not in ("N125", "N199")])
        self.assertEqual(n["pct_den"], p22["通した"]["分母"])
        # 67 書類の P21 の GROUNDED 4,267(期間を縛る結果の記録)
        pb = jload(PERIOD_BIND_JSON)
        self.assertEqual((pb["E2"]["集計"]["P21 の GROUNDED"], pb["E2"]["集計"]["claims"]), (n["grounded_p21"], 7799))
        self.assertEqual(jload(POINT_PRIOR_JSON)["書類の数"]["文あり"], 67)

    def test_6_section_1_flag_shape_and_what_is_not_stacked(self):
        b = sec(self.t, "## §1", "## §2")
        for s in (u"`Profile` に `truncate_abs_band: bool = False`", u"**照合の帯だけ**", u"0 ≤ |fact| − |文| < 桁",
                  u"`decide_rounding` の判定の軸は変えない", u"`truncate_on_magnitude` とは別の旗",
                  u"`P23 = replace(P22, name=\"P23\", pct_tolerance_from_decimals=True, truncate_abs_band=True)`",
                  u"**段 1 では既定にしない**(`DEFAULT_PROFILE = \"P22\"` のまま)",
                  u"`vocabulary.match_value` とその写し `comparators._match_value` の切り捨ての枝だけ",
                  u"率の帯は既存の旗のまま(1 桁なら ±0.06)", u"率を金額の方針に連動させない",
                  u"P18/P19 の旗の意味(そのまま)"):
            self.assertIn(s, b, s)
        # P19 の旗は P23 に積まない(積むと 3 書類で金額 55 行が落ちる)
        p23 = re.search(r"`P23 = replace\([^`]*\)`", b).group(0)
        self.assertNotIn("truncate_on_magnitude", p23)
        self.assertIn("pct_tolerance_from_decimals=True", p23)
        # 触る枝の中の人間の決定(列挙。1 つも壊さない)
        line = [l for l in b.splitlines() if l.startswith(u"- **触る枝の中の人間の決定")][0]
        for s in (u"1 つも壊さない", u"2026-10-08 案ア", u"§1b の止め", u"C2 `period_cue`", u"P21 の最後の枝(5eb80a2)",
                  u"P22 の `period_bind`(3320c8c、`subj and`)", u"P18/P19 の旗の意味(そのまま)",
                  u"P16/P20/P21/P22 を明示した試験の数は 1 つも変えない"):
            self.assertIn(s, line, s)
        s3 = sec(self.t, "## §3", "## §4")
        self.assertIn(u"P19 の `truncate_on_magnitude`(判定の軸も変える旗)は積まない。積むと 3 書類で金額 55 行が落ちる(§0)。", s3)

    def test_7_the_decisions_in_the_touched_branch_exist_in_the_engine(self):
        """封が名指した人間の決定が、いまの engine の字に在る(封が実物と食い違っていない)。
        段 1 の後も 1 つも壊さない約束なので、この assert は段 1 の後も残す。"""
        r = text(os.path.join(ROOT, "adapters", "xbrl", "recipes.py"))
        v = text(os.path.join(ROOT, "adapters", "xbrl", "vocabulary.py"))
        i = r.index("def _direct_value_claim(")
        body = r[i:r.index("\ndef ", i + 1)]
        self.assertIn(u"案ア", body)
        self.assertIn('claim["reason"] = "no_subject"', body)
        self.assertIn('claim["reason"] = "no_element(no prior2 for prior-year diff)"', body)
        self.assertIn("profile.prior2_required", body)
        self.assertIn("profile.period_cue and _prior_cue(s, a, b)", body)
        self.assertIn('getattr(profile, "last_branch_cues", False)', body)
        # P22 の period_bind は `subj and` つき(3320c8c)
        self.assertIn('getattr(profile, "period_bind", False) and subj and not _prior_cue(s, a, b) and not _prior_cue_clause(s, a)', body)
        self.assertIn("last_branch_cues: bool = False", v)
        self.assertIn("period_bind: bool = False", v)

    def test_8_engine_pins_list_is_written_and_exists(self):
        b = sec(self.t, "## §1", "## §2")
        line = [l for l in b.splitlines() if l.startswith(u"- **過去の門の engine の留め**")][0]
        for s in (u"ENGINE_LATER(branch_a・role_swap・axis3・p20_result・a_core_vs_grep・pnf_diag)", u"cd_seal FROZEN_LATER",
                  u"point_prior・ritual・period_bind(seal/result)", u"frozen_bundle の世代",
                  u"axis3 LATER_ENGINE_COMMITS(次の便)"):
            self.assertIn(s, line, s)
        defining = set()
        for p in glob.glob(os.path.join(ROOT, "tests", "measure", "*.py")):
            if re.search(r"(?m)^ENGINE_LATER = \{", text(p)):
                defining.add("tests/measure/" + os.path.basename(p))
        self.assertTrue(set(PIN_FILES_ENGINE_LATER) <= defining, sorted(set(PIN_FILES_ENGINE_LATER) - defining))
        self.assertEqual(len(PIN_FILES_ENGINE_LATER), 6)
        for rel, name in sorted(OTHER_PINS.items()):
            self.assertTrue(re.search(r"(?m)^%s\b" % name, text(os.path.join(ROOT, rel))), rel + " の " + name)
        # point_prior・ritual・period_bind の seal/result の門は実在する
        for rel in ("tests/measure/test_xbrl_point_prior_seal.py", "tests/measure/test_xbrl_point_prior_result.py",
                    "tests/measure/test_xbrl_ritual_seal.py", "tests/measure/test_xbrl_ritual_result.py",
                    "tests/measure/test_xbrl_period_bind_seal.py", "tests/measure/test_xbrl_period_bind_result.py"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_9_limits_are_written(self):
        b = sec(self.t, "## §3", "## §4")
        for s in (u"率の帯(1 桁で ±0.06)は、提出者が表示の桁の金額から率を出した型(下調べで 7 行)を落とす。",
                  u"差が 0.05〜0.06 の注入は通る(儀式の N069)。",
                  u"退化値(0 → 00)は注入道具の欠陥で、帯では止まらない。",
                  u"字の端数処理の方針は使わない(取れる書類が 5 / 67)。",
                  u"前々期の値への置き換えは P23 でも通る(P22 の限界のまま)。"):
            self.assertIn(s, b, s)

    def test_10_closed_file_list(self):
        b = sec(self.t, "## §4")
        first = b[:b.index(u"\n順序:")]
        pos = []
        for rel in ENGINE_FILES + FILES:
            tok = "`%s`" % rel
            self.assertEqual(first.count(tok), 1, rel)
            pos.append(first.index(tok))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        self.assertEqual(len(ENGINE_FILES + FILES), 8)
        self.assertLess(pos[2], pos[3])         # engine 3 file が試験より先
        self.assertIn(u"→ 登録の一覧の試験 4 か所に P23 →", first)
        self.assertIn(u"→ pin の遷移 → 覆い。", first)
        self.assertIn(u"段 2(P24・P25 と合わせて結果を人間に見せてから): 既定の切り替え + 既定の字の試験 + 儀式の走らせ直し + README + pin。", first)
        order = b[b.index(u"\n順序:"):]
        self.assertIn(u"人間の事前承認(2026-10-21)→ この封 + 封の門を commit → 段 1 実装(別席)→ 凍結 → 独立監査 → commit → 結果を人間に見せる(朝)→ 段 2(まとめて)→ 監査 → commit。", order)


class EngineAtSealTest(unittest.TestCase):
    """封の commit 時点の engine を字で留め、段 1 の後は「宣言された遷移」の値だけを受け入れる(docstring)。"""

    def test_11_engine_sha_is_the_one_at_the_seal_or_a_declared_transition(self):
        self.assertEqual(sorted(ENGINE_AT_SEAL), sorted(ENGINE_FILES))
        for rel, want in sorted(ENGINE_AT_SEAL.items()):
            got = sha16(rel)
            if got != want and rel in ENGINE_LATER:
                later, seal_rel = ENGINE_LATER[rel]
                added = git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split()
                self.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている(段 1 の commit で ENGINE_LATER に遷移を宣言する)**" % rel)

    def test_12_flags_exist_default_is_p22_and_the_new_flag_and_p23_do_not_exist_yet(self):
        from adapters.xbrl import vocabulary as V
        fields = dict((f.name, f) for f in dataclasses.fields(V.Profile))
        # 既存の旗 2 つ(封 §1)
        self.assertIn("pct_tolerance_from_decimals", fields)
        self.assertIn("truncate_on_magnitude", fields)
        self.assertEqual(sorted(n for n, p in V.PROFILES.items() if p.pct_tolerance_from_decimals), ["P18", "P19"])
        self.assertEqual(sorted(n for n, p in V.PROFILES.items() if p.truncate_on_magnitude), ["P19"])
        for n in ("P20", "P21", "P22"):       # P20〜P22 には積まれていない(封 §0)
            self.assertFalse(V.PROFILES[n].pct_tolerance_from_decimals, n)
            self.assertFalse(V.PROFILES[n].truncate_on_magnitude, n)
        # 既定は P22 のまま。新しい旗 `truncate_abs_band` はまだ Profile に無い。P23 は PROFILES に無い(封の commit 時点の事実)。
        # 段 1 の commit で「在る・P23 だけが真・P23 は在り既定は P22 のまま」に直す(docstring)。
        self.assertEqual(V.DEFAULT_PROFILE, "P22")
        self.assertNotIn("truncate_abs_band", fields)
        self.assertNotIn("P23", V.PROFILES)

    def test_13_pct_band_is_half_the_written_digit_plus_001(self):
        """封 §0「率の旗の帯は 1 桁で ±0.06」は recipes.pct_tolerance の実物の値である(下調べの V3 の ±0.05 ではない)。"""
        from adapters.xbrl import recipes as R, vocabulary as V
        s = u"自己資本比率は3.8%となり"
        a = s.index(u"3.8")
        b = a + 3
        self.assertAlmostEqual(R.pct_tolerance(V.PROFILES["P18"], s, a, b), 0.06, places=9)
        self.assertAlmostEqual(R.pct_tolerance(V.PROFILES["P22"], s, a, b), 0.15, places=9)
        self.assertEqual(R.PCT_TOLERANCE_DEFAULT, 0.15)
        s0_ = u"増加率は12%となり"
        a0 = s0_.index(u"12")
        self.assertAlmostEqual(R.pct_tolerance(V.PROFILES["P18"], s0_, a0, a0 + 2), 0.51, places=9)


@contextlib.contextmanager
def registered(name, **flags):
    """in-process で profile を登録する(engine の file は書き換えない)。出るとき必ず消す。"""
    from adapters.xbrl import vocabulary as V
    V.PROFILES[name] = dataclasses.replace(V.PROFILES["P22"], name=name, **flags)
    try:
        yield name
    finally:
        V.PROFILES.pop(name, None)


class LiveReproductionTest(unittest.TestCase):
    """cache(~/.cache/audit-core/edinet/*.zip)と AUDIT_CORE_ROUNDING=1 のとき、封 §0 の「率の旗だけ」の数を実走で数え直す。
    **率の旗だけを in-process の replace で P22 に積んだ profile** で、儀式 240 件の通した 4(N069・N096・N237・N277)、
    67 書類の無改変で GROUNDED を離れる 8(％ 7・ポイント 1・金額 0)・新 GROUNDED 0・VALUE_MISMATCH 1,410 → 1,418・
    書類ごとの丸め方の判定(R/T)の不変、と、P19 の `truncate_on_magnitude` を積むと 3 書類で判定が切り捨て → 四捨五入に反転することを確かめる。
    **既定では走らせない**(重いので。走らせない間も SealTest が封の字と記録を縛る)。engine の file は書き換えない。"""

    FLIP_DOCS = ("S100YZ7E", "S100Z38F", "S100Z48T")

    @staticmethod
    def _need():
        if os.environ.get("AUDIT_CORE_ROUNDING") != "1":
            raise unittest.SkipTest(u"AUDIT_CORE_ROUNDING=1 のときだけ走る(約 2 分)")

    @staticmethod
    def _fp():
        spec = importlib.util.spec_from_file_location("fp_rounding_gate", os.path.join(ROOT, "measure", "false_pass_2026-10-14.py"))
        fp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fp)
        return fp

    @staticmethod
    def _doc_ids():
        pp = jload(POINT_PRIOR_JSON)
        return sorted(x["docID"] for x in pp["書類"] if x["区分"] == u"文あり")

    def test_g1_ritual_pct_flag_only_passes_four_of_240(self):
        self._need()
        fp = self._fp()
        with io.open(RITUAL_ZIP, "rb") as fh:
            zb = fh.read()
        text0 = fp.mdna_text(zb)
        with registered("P23_GATE_PCT", pct_tolerance_from_decimals=True) as pn:
            r = fp.run_doc("ai_prose", pn, zb, text0)
        passed = sorted(x["id"] for x in r["rows"] if x["outcome"] == "PASSED")
        self.assertEqual(r["targets"], 240)
        self.assertEqual(passed, ["N069", "N096", "N237", "N277"])
        self.assertEqual(r["counts"].get("PASSED"), 4)
        self.assertEqual(r["counts"].get("detected:VALUE_MISMATCH"), 236)
        # 対照: P22(既定)は記録どおり 15
        p22 = jload(RITUAL_P22_JSON)
        self.assertEqual(len(p22["通した の一覧"]), 15)
        self.assertTrue(set(passed) <= set(x["id"] for x in p22["通した の一覧"]))

    def test_g2_docs_pct_flag_only_costs_eight_all_rates_and_keeps_the_rounding_decision(self):
        self._need()
        ids = self._doc_ids()
        if not os.path.isdir(CACHE_DIR) or not all(os.path.exists(os.path.join(CACHE_DIR, d + ".zip")) for d in ids):
            self.fail(u"AUDIT_CORE_ROUNDING=1 なのに cache(~/.cache/audit-core/edinet/*.zip)が揃っていない")
        from adapters.xbrl import recipes as R, vocabulary as V
        from adapters.xbrl.verify_document import verify_document
        self.assertEqual(len(ids), 67)
        vm = {"P22": 0, "gate": 0}
        lost, gained, changed_mode = [], [], []
        with registered("P23_GATE_PCT", pct_tolerance_from_decimals=True) as pn:
            for d in ids:
                with io.open(os.path.join(CACHE_DIR, d + ".zip"), "rb") as fh:
                    zb = fh.read()
                a = verify_document(zb, "P22", None)
                b = verify_document(zb, pn, None)
                A = dict((c["id"], c) for c in a["claims"])
                B = dict((c["id"], c) for c in b["claims"])
                self.assertEqual(sorted(A), sorted(B), d)
                vm["P22"] += a["document"]["states"].get("VALUE_MISMATCH", 0)
                vm["gate"] += b["document"]["states"].get("VALUE_MISMATCH", 0)
                for i, c in A.items():
                    if c["state"] == "GROUNDED" and B[i]["state"] != "GROUNDED":
                        lost.append((d, i, c["unit"], B[i]["state"]))
                    if c["state"] != "GROUNDED" and B[i]["state"] == "GROUNDED":
                        gained.append((d, i))
                ia, ib = {}, {}
                R.build_recipes(zb, V.PROFILES["P22"], info=ia)
                R.build_recipes(zb, V.PROFILES[pn], info=ib)
                if (ia.get("rounding"), ia.get("rounding_round_only"), ia.get("rounding_truncate_only")) != \
                        (ib.get("rounding"), ib.get("rounding_round_only"), ib.get("rounding_truncate_only")):
                    changed_mode.append(d)
        n = s0_numbers(s0(text(SEAL)))
        self.assertEqual(len(lost), n["pct_cost"])
        units = sorted(u for _, _, u, _ in lost)
        self.assertEqual(units, sorted([u"%"] * n["pct_pct"] + [u"ポイント"] * n["pct_pt"]))
        self.assertEqual([s for _, _, _, s in lost], ["VALUE_MISMATCH"] * n["pct_cost"])
        self.assertEqual(gained, [])
        self.assertEqual((vm["P22"], vm["gate"]), (n["vm_before"], n["vm_after"]))
        self.assertEqual(changed_mode, [])

    def test_g3_the_magnitude_flag_flips_the_rounding_decision_in_three_docs(self):
        self._need()
        from adapters.xbrl import recipes as R, vocabulary as V
        with registered("P23_GATE_MAG", truncate_on_magnitude=True) as pn:
            for d in self.FLIP_DOCS:
                with io.open(os.path.join(CACHE_DIR, d + ".zip"), "rb") as fh:
                    zb = fh.read()
                ia, ib = {}, {}
                R.build_recipes(zb, V.PROFILES["P22"], info=ia)
                R.build_recipes(zb, V.PROFILES[pn], info=ib)
                self.assertEqual(ia.get("rounding"), "truncate", d)
                self.assertEqual(ib.get("rounding"), "round", d)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        shas = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split() if s]
        return shas[-1] if shas else None

    def test_14_the_seal_precedes_every_later_file(self):
        tracked = git("ls-files", "--error-unmatch", SEAL_REL).returncode == 0
        if not tracked:
            # 封が履歴に無い間に、後の file が履歴に現れていたら赤(順序の逆転)。何も無いことは pass と言わず skip で残す。
            for rel in AFTER:
                self.assertIsNone(self._added(rel), u"封より先に履歴に現れた: " + rel)
            self.skipTest(u"封がまだ commit されていない")
        seal = self._added(SEAL_REL)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(git("merge-base", "--is-ancestor", seal, other).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
