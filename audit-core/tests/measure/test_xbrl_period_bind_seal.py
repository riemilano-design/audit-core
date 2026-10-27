# -*- coding: utf-8 -*-
u"""期間を縛る直し(P22)の封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md を固定する。
人間の承認の引用・予測 E-1〜E-8 と外れ方・§0 の数(字・記録の値・cache が在る機械では AUDIT_CORE_PERIOD_BIND=1 で実走)・
§1 の人間の決定 4 つと「1 つも壊さない」「旗は P22 だけ」「既定は P21 のまま」・過去の門の engine の留めの一覧・
§4 の file 一覧と順序・封が実装より先であること(順序)・**封の commit 時点の engine の sha**を縛る。

**この門の engine の留め(test_9・test_10)は、段 1 の commit で「宣言された遷移」に更新する前提である。**
この封は engine(adapters/xbrl/recipes.py・vocabulary.py)を変える封なので、段 1 で sha が動く。そのとき
`ENGINE_LATER` に (段 1 の後の sha16, この封の path) を足し、`test_10` の「P22 は PROFILES に無い」を
「P22 は PROFILES に在り、DEFAULT_PROFILE は P21 のまま」に直す(他の pin 6 本・axis3 の LATER_ENGINE_COMMITS・
cd_seal の FROZEN_LATER・frozen_bundle の世代も同じ段 1 の commit で宣言する ― 封 §1 の一覧)。
段 2(既定 P21 → P22)でもう一度、`DEFAULT_PROFILE` の assert を直す。"""
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

SEAL_REL = "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
POINT_PRIOR_JSON = os.path.join(ROOT, "fixtures", "xbrl", "point_prior_2026-10-20.json")
# 封が見ているのは P21 のときの儀式の記録(N125・N199 が前期へ移って通した)。2026-10-20 の期を縛る P22 の段 2 で ritual_2026-10-20.json は
# P22(既定)で採り直したので、同じバイト列の写し ritual_2026-10-20_p21.json に当てる(sha256 dad4c56e…。結果の門が字で留める)。
RITUAL_JSON = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20_p21.json")
S2_JSON = os.path.join(ROOT, "fixtures", "xbrl", "gen_c", "hybrid_s2_2026-10-20.json")
NAMING_JSON = os.path.join(ROOT, "fixtures", "xbrl", "naming_fix", "p21_2026-10-20.json")
CACHE_GLOB = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet", "*.zip")

# §4 の file 一覧(この順で書かれている。段 1 の新規 file)
FILES = ("tests/adapters/xbrl/test_recipes_p22.py",
         "measure/xbrl_period_bind_2026-10-20.py",
         "fixtures/xbrl/period_bind_2026-10-20.json",
         "docs/XBRL_PERIOD_BIND_RESULT_2026-10-20.md",
         "tests/measure/test_xbrl_period_bind_result.py")
# 封より後でなければ git 履歴に現れてはならない新規 file(§4 の 5 本そのもの)
AFTER = FILES

# 封の commit 時点の engine(sha256 の先頭 16 桁)。**ここは宣言された遷移の前の値**で、消さない。
ENGINE_AT_SEAL = {"adapters/xbrl/recipes.py": "2f692bca1eac3cd3",
                  "adapters/xbrl/vocabulary.py": "1205b30b496090ef"}
# 宣言された遷移(段 1 の commit で足す): {path: (後の sha16, 遷移を宣言した封の path)}。封の commit 時点では空だった。
# 2026-10-20 追記(上の ENGINE_AT_SEAL は封の commit 時点の値で消さない): 段 1 の実装で recipes.py は +4 行(最初の枝の塊)、
# vocabulary.py は +4 行・-1 行(旗・P22・PROFILES の登録)。DEFAULT_PROFILE は P21 のまま。
# 2026-10-20 追記(段 2): vocabulary.py の sha は 段 1 3320c8c で 1fdb48e7e3ba58ce(残す。段 1 の結果の記録が測った時点の値)、
# 段 2(DEFAULT_PROFILE を P21 -> P22 にし、決定の注記を足した。vocabulary.py だけ・recipes.py は 0 行)で 25a3c0992e10daaa。
# 2026-10-21 追記(丸めの帯 P23 の段 1): 封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 truncate_abs_band・P23・PROFILES の登録を足し
# (DEFAULT_PROFILE は P22 のまま)、recipes.py に _mag_trunc を足した。recipes.py の 65a37869f053a60e・vocabulary.py の 25a3c0992e10daaa は残す(測った時点の値)。
# 受け入れるのは、その封が履歴に在り、値が P23 の段 1 の後の値のときだけ(遷移を宣言した封の path は SEAL_ROUNDING)。
SEAL_ROUNDING = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"
SEAL_VOCAB = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"    # 2026-10-21 追記: 語彙の登録と枠の取り直し P24 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"    # 2026-10-21 追記: 最後の枝 P25 の段 1(下の ENGINE_LATER の遷移)
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"    # 2026-10-22 追記: P26 の段 1(下の ENGINE_LATER の遷移)
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
# 2026-10-21(語彙の登録と枠の取り直し P24 の段 1): 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に旗 vocab_2026_10_21・frame_rebind の塊(+224 行・既存の行は 1 つも書き換えない)を足した(DEFAULT_PROFILE は P22 のまま)。
# d5308700eae78c10(P23 の段 1)は残す(測った時点の値)、P24 の段 1 で 3461c3f8b7af6675。受け入れるのは、その封が履歴に在り、値が P24 の段 1 の後の値のときだけ。
# 2026-10-21(最後の枝 P25 の段 1): 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に最後の枝の証拠の判定の塊(+72 行・-0 行。既存の行は 1 つも書き換えない)、vocabulary.py に旗 last_branch_names_only_if_evidence・P25・PROFILES の登録(+7 行・-0 行)を足した(DEFAULT_PROFILE は P22 のまま)。
# recipes.py の 3461c3f8b7af6675・vocabulary.py の 83498c04a7b70396(P24 の段 1)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P25 の段 1 の後の値のときだけ。
# 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
ENGINE_LATER = {"adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27),
                # 2026-10-21(語彙の登録と枠の取り直し P24 の段 1): 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 2 つ・資金の句の表・P24・PROFILES の登録を足した(DEFAULT_PROFILE は P22 のまま)。
                # f7b8d925eb6787ec(P23 の段 1)は残す(測った時点の値)、P24 の段 1 で 83498c04a7b70396。受け入れるのは、その封が履歴に在り、値が P24 の段 1 の後の値のときだけ。
                # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 5 つ・P26・PROFILES の登録(+17 行・-0 行) を足した。
                # 27e71e9861fc5aad(P25 の段 1)は残す(測った時点の値)、P26 の段 1 で 83025e9c0525d08b。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
                # 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
                # 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
                "adapters/xbrl/vocabulary.py": ("85896a67913ce1e7", SEAL_P27)}

# §1「過去の門の engine の留め」の一覧(封の字)と、実物の在りか
PIN_FILES_ENGINE_LATER = ("tests/measure/test_xbrl_branch_a.py", "tests/measure/test_xbrl_role_swap_result.py",
                          "tests/measure/test_xbrl_axis3_decision.py", "tests/measure/test_xbrl_p20_result.py",
                          "tests/measure/test_xbrl_a_core_vs_grep_seal.py", "tests/measure/test_xbrl_pnf_diag.py")
OTHER_PINS = {"tests/measure/test_xbrl_axis3_decision.py": "LATER_ENGINE_COMMITS",
              "tests/measure/test_xbrl_cd_seal.py": "FROZEN_LATER",
              "tests/measure/test_xbrl_a_core_vs_grep_seal.py": "ENGINE_LATER",
              "fixtures/frozen_bundle_sha.py": "FROZEN_BUNDLE_GENERATIONS"}


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


def s0_numbers(b):
    """§0 の数を、書かれた字のまま取り出す(書き方が変わったら落ちる)。"""
    m1 = re.search(r"(\d+) 書類で、当期の数を同じ要素の前期の値に置き換えた注入 (\d+) 件のうち.*?\*\*GROUNDED のまま通した (\d+) / (\d+) = ([\d.]+)%\*\*\(金額 (\d+) / (\d+) = ([\d.]+)%\)", b)
    m2 = re.search(r"段 2 の Core 自身 T6 (\d+) / (\d+)", b)
    m3 = re.search(r"通した (\d+) 件の文に「前期」「前年」等の語が在るのは (\d+)\(「前期比」等の比較形を除くと (\d+)\)", b)
    m4 = re.search(r"GROUNDED の claim で pointer が 1 本のもの ([\d,]+) のうち、\*\*Prior1Year に結び、文に前期の手がかりが無いもの (\d+)\*\*\(手がかりありは (\d+)、当期 ([\d,]+)\)", b)
    m5 = re.search(r"全 GROUNDED ([\d,]+) の ([\d.]+)%", b)
    m6 = re.search(r"経営分析の文を持つ (\d+) 書類", b)
    assert m1 and m2 and m3 and m4 and m5 and m6, u"§0 の数の書き方が変わった"
    return {"docs": int(m1.group(1)), "inj": int(m1.group(2)), "passed": int(m1.group(3)), "inj2": int(m1.group(4)),
            "rate": float(m1.group(5)), "money_passed": int(m1.group(6)), "money_total": int(m1.group(7)),
            "money_rate": float(m1.group(8)),
            "t6_grounded": int(m2.group(1)), "t6_total": int(m2.group(2)),
            "s459": int(m3.group(1)), "s336": int(m3.group(2)), "s186": int(m3.group(3)),
            "single": num(m4.group(1)), "cost": int(m4.group(2)), "cue": int(m4.group(3)), "cur": num(m4.group(4)),
            "grounded_all": num(m5.group(1)), "cost_rate": float(m5.group(2)),
            "with_text": int(m6.group(1))}


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)

    def test_1_human_approval_is_quoted_and_the_seal_says_it_changes_the_engine(self):
        head = self.t[:self.t.index("\n## §0 ")]
        self.assertIn(u"**この封は engine(`adapters/xbrl/recipes.py`・`vocabulary.py`)を変える。人間の承認(2026-10-20)", head)
        self.assertIn(u"人間「君に任せる」", head)
        self.assertIn(u"段 2(既定 P21 → P22)は段 1 の結果を見せてから別に諮る。", head)
        self.assertIn(u"数を見てから封・予測を直さない。外れは外れとして残す。**", head)

    def test_2_eight_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §2", "## §3")
        ids, lines = predictions(b, "E")
        self.assertEqual(ids, [str(i) for i in range(1, 9)])
        self.assertEqual(len(lines), 8)
        for line in lines:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[1], u"予測が空: " + line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        by = dict((i, l) for i, l in zip(ids, lines))
        # 行ごとに、予測の幅と外れ方の両方を字で縛る(幅を直すと赤くなる)
        for i, ss in (("1", (u"穴 B の 485 件を P22 で再検証", u"**0〜10 / 485**(458 から)", u"**420〜485**", u"通した 11 以上")),
                      ("2", (u"**22〜30**(§0 の 26 とその周辺)", u"新しく GROUNDED になる行 0", u"**1 行も動かない**",
                             u"幅の外 / 新 GROUNDED 1 以上 / 190・1,726 が動く")),
                      ("3", (u"40 書類 4,665 本", u"`fixtures/xbrl/naming_fix/p21_2026-10-20.json`", u"**≤ 40**",
                             u"41 以上 / 向きが逆")),
                      ("4", (u"**0〜1 / 10** GROUNDED(6 から)", u"**1 つも変わらない**(別の経路)", u"T6 2 以上 / α 型が動く")),
                      ("5", (u"通した **15**(N125・N199 が VALUE_MISMATCH に)", u"止めた **226**", u"15・226 でない / 他が動く")),
                      ("6", (u"**過半は「減少額が前期の残高と一致」型**", u"直しの代価は「正しい文を保留に落とす」", u"過半が別の型")),
                      ("7", (u"`recipes.py` **≤ 15 行**", u"`vocabulary.py` **≤ 6 行**", u"`core/` 0 行", u"**全部緑のまま**", u"超える / 赤")),
                      ("8", (u"E-1〜E-7 が当たったときだけ、人間の承認の後", u"`DEFAULT_PROFILE` の字の決定の注記を日付つきで", u"赤が残る"))):
            for s in ss:
                self.assertIn(s, by[i], u"E-%s: %s" % (i, s))
        self.assertIn(u"**本当に測っているのは E-1・E-2・E-6 である**", b)

    def test_3_section_0_numbers_are_pinned_as_written(self):
        b = s0(self.t)
        n = s0_numbers(b)
        self.assertEqual((n["docs"], n["with_text"]), (67, 67))
        self.assertEqual((n["inj"], n["inj2"], n["passed"]), (485, 485, 458))
        self.assertEqual(n["rate"], round(100.0 * 458 / 485, 1))
        self.assertEqual(n["rate"], 94.4)
        self.assertEqual((n["money_passed"], n["money_total"], n["money_rate"]), (458, 460, 99.6))
        self.assertEqual(n["money_rate"], round(100.0 * 458 / 460, 1))
        self.assertEqual((n["t6_grounded"], n["t6_total"]), (6, 10))
        self.assertEqual((n["s459"], n["s336"], n["s186"]), (459, 336, 186))
        self.assertLess(n["s186"], n["s336"])
        self.assertLessEqual(n["s336"], n["s459"])
        # 代価の見積もり 26 / 手がかりあり 190 / 当期 1,726 は足して pointer が 1 本の GROUNDED 1,942 になる
        self.assertEqual((n["cost"], n["cue"], n["cur"], n["single"]), (26, 190, 1726, 1942))
        self.assertEqual(n["cost"] + n["cue"] + n["cur"], n["single"])
        self.assertEqual((n["grounded_all"], n["cost_rate"]), (4267, 0.6))
        self.assertEqual(round(100.0 * 26 / 4267, 1), 0.6)
        for s in (u"N125・N199 も同じ形", u"`recipes._direct_value_claim` の最初の枝", u"`hits`", u"(C2)",
                  u"**engine 自身の `_prior_cue`(数の直前 12 字)は 459 件すべてで偽**", u"`_prior_cue_clause`(同じ節の「前期は」等)",
                  u"E-1 の外れ方は「`_prior_cue_clause` が真になる文で前期の fact が候補に残る数」",
                  u"「短期借入金が 2 億円減少」(前期残高 2 億 → 当期 0)", u"= 直しの代価", u"司令塔の手元"):
            self.assertIn(s, b, s)

    def test_4_section_0_numbers_match_the_point_prior_record(self):
        rec = jload(POINT_PRIOR_JSON)
        b = rec["B"]["集計"]
        n = s0_numbers(s0(self.t))
        self.assertEqual(b["書類の数(分母)"], n["docs"])
        self.assertEqual(b["作れた注入"]["合計"], n["inj"])
        self.assertEqual((b["前期へ移って通した"]["件"], b["前期へ移って通した"]["分母"], b["前期へ移って通した"]["率"]),
                         (n["passed"], n["inj"], n["rate"]))
        # 金額 = 円・千円・百万円(率の % と 名 を除く)。通した 458 / 全部 460 を単位別の結果から数え直す
        units = b["単位別の結果"]
        money = [u for u in units if u in (u"円", u"千円", u"百万円")]
        self.assertEqual(sorted(money), sorted([u"円", u"千円", u"百万円"]))
        total = sum(sum(units[u].values()) for u in money)
        moved = sum(v for u in money for k, v in units[u].items() if k.startswith(u"通した(参照先が前期へ移った)"))
        self.assertEqual((moved, total), (n["money_passed"], n["money_total"]))
        self.assertEqual(round(100.0 * moved / total, 1), n["money_rate"])
        # 通した(GROUNDED のまま)459 = 前期へ移った 458 + 当期のまま 1
        self.assertEqual(b["通した(GROUNDED のまま)合計"]["件"], n["s459"])
        self.assertEqual(n["s459"], n["passed"] + b["通した のうち参照先が Prior1Year でない"]["件"])
        self.assertEqual(rec["書類の数"]["文あり"], n["with_text"])

    def test_5_ritual_and_stage2_records_hold_what_section_0_says(self):
        n = s0_numbers(s0(self.t))
        rec = jload(RITUAL_JSON)
        rows = dict((x["id"], x) for x in rec["通した の一覧"])
        for i in ("N125", "N199"):
            x = rows[i]
            self.assertEqual(x["結果"], "PASSED", i)
            self.assertIn("@CurrentYear", x["参照先(注入前)"], i)
            self.assertIn("@Prior1Year", x["参照先(注入後)"], i)
            self.assertTrue(x["参照先が動いた"], i)
        self.assertEqual(sorted(x["id"] for x in rec["通した の一覧"] if x["参照先が動いた"]), ["N125", "N199"])
        t6 = jload(S2_JSON)["集計"]["型別"]["T6_PRIOR"]["Core 自身が GROUNDED"]
        self.assertEqual((t6["分子"], t6["分母"]), (n["t6_grounded"], n["t6_total"]))
        # E-5 の 15 / 226 は儀式の 241 件(通した 17 から N125・N199 を除く)
        self.assertEqual(len(rec["通した の一覧"]), 17)
        self.assertEqual(17 - 2, 15)
        self.assertEqual(241 - 15, 226)

    def test_6_naming_fix_set_is_40_docs_4665_claims(self):
        rec = jload(NAMING_JSON)["無改変の 40 書類"]
        self.assertEqual(len(rec["id の一覧"]), 40)
        self.assertEqual(rec["集計"]["claims"], 4665)

    def test_7_section_1_decisions_flag_and_default_are_written(self):
        b = sec(self.t, "## §1", "## §2")
        for s in (u"`Profile` に `period_bind: bool = False` を足し", u"`P22 = replace(P21, name=\"P22\", period_bind=True)`",
                  u"**段 1 では既定にしない**(`DEFAULT_PROFILE = \"P21\"` のまま)",
                  u"`if hits and not (is_diff and subj)` の前に", u"`_prior_cue(s, a, b)` でない(かつ `_prior_cue_clause` でもない)",
                  u"`hits` から `Prior1Year…` の fact を外す", u"**値の一致なし**として後続の枝",
                  u"core/ 0 行"):
            self.assertIn(s, b, s)
        # 触る枝の中の人間の決定 4 つ(列挙。この後ろに置き、1 つも壊さない)
        line = [l for l in b.splitlines() if l.startswith(u"- **触る枝の中の人間の決定")][0]
        for s in (u"この後ろに置き、1 つも壊さない", u"2026-10-08 案ア(主語が取れない数は束縛しない `no_subject`)",
                  u"2026-10-08 §1b の止め", u"C2 `period_cue`(前期の手がかりがあれば Prior1Year を先に = そのまま効く)",
                  u"P21 の最後の枝(5eb80a2)", u"P16/P20/P21 を明示した試験の数は 1 つも変えない(旗は P22 だけ)"):
            self.assertIn(s, line, s)
        self.assertEqual(len(re.findall(u"2026-10-08 案ア|2026-10-08 §1b の止め|C2 `period_cue`|P21 の最後の枝", line)), 4)

    def test_8_the_four_decisions_exist_in_the_engine_as_the_seal_says(self):
        """封が名指した人間の決定が、いまの engine の字に在る(封が実物と食い違っていない)。
        段 1 の後も 1 つも壊さない約束なので、この assert は段 1 の後も残す。"""
        r = text(os.path.join(ROOT, "adapters", "xbrl", "recipes.py"))
        v = text(os.path.join(ROOT, "adapters", "xbrl", "vocabulary.py"))
        i = r.index("def _direct_value_claim(")
        body = r[i:r.index("\ndef ", i + 1)]
        # 案ア: 主語が取れない数は束縛せず reason=no_subject
        self.assertIn(u"案ア", body)
        self.assertIn('claim["reason"] = "no_subject"', body)
        # §1b の止め
        self.assertIn('claim["reason"] = "no_element(no prior2 for prior-year diff)"', body)
        self.assertIn("profile.prior2_required", body)
        # C2 period_cue(並べ替え)
        self.assertIn("profile.period_cue and _prior_cue(s, a, b)", body)
        self.assertIn('hits = sorted(hits, key=lambda fh: 0 if fh[0]["context"].startswith("Prior1Year") else 1)', body)
        # 最初の枝の入口
        self.assertIn("if hits and not (is_diff and subj):", body)
        self.assertLess(body.index("hits = sorted("), body.index("if hits and not (is_diff and subj):"))
        # P21 の最後の枝(last_branch_cues)と §1b の止めの順(止めが先)
        self.assertIn('getattr(profile, "last_branch_cues", False)', body)
        self.assertLess(body.index("no_element(no prior2 for prior-year diff)"), body.index('getattr(profile, "last_branch_cues", False)'))
        # 補助: _prior_cue / _prior_cue_clause が在る
        self.assertIn("def _prior_cue(s, a, b=None):", r)
        self.assertIn("def _prior_cue_clause(s, pos):", r)
        self.assertIn("last_branch_cues: bool = False", v)

    def test_9_engine_pins_list_is_written_and_exists(self):
        b = sec(self.t, "## §1", "## §2")
        line = [l for l in b.splitlines() if l.startswith(u"- **過去の門の engine の留めを先に列挙")][0]
        for s in (u"段 1 の commit で遷移を宣言", u"axis3 `LATER_ENGINE_COMMITS`",
                  u"`ENGINE_LATER` の pin 6 本(vocabulary.py・recipes.py の sha16)", u"`fixtures/frozen_bundle_sha.py` の世代",
                  u"`test_xbrl_cd_seal.py` FROZEN_LATER", u"`test_xbrl_a_core_vs_grep_seal.py` ENGINE_LATER",
                  u"`test_xbrl_hybrid_trust_seal.py`(順序のみ)"):
            self.assertIn(s, line, s)
        # 実物: ENGINE_LATER を定義している試験は、封の言う 6 本を含む(7 本目が増えても赤にしない ― 6 本を落とすと赤)
        defining = set()
        for p in glob.glob(os.path.join(ROOT, "tests", "measure", "*.py")):
            if re.search(r"(?m)^ENGINE_LATER = \{", text(p)):
                defining.add("tests/measure/" + os.path.basename(p))
        self.assertTrue(set(PIN_FILES_ENGINE_LATER) <= defining, sorted(set(PIN_FILES_ENGINE_LATER) - defining))
        self.assertEqual(len(PIN_FILES_ENGINE_LATER), 6)
        for rel, name in sorted(OTHER_PINS.items()):
            self.assertTrue(re.search(r"(?m)^%s\b" % name, text(os.path.join(ROOT, rel))), rel + " の " + name)
        # 順序のみの試験は engine の sha を留めていない(封の「順序のみ」)
        hy = text(os.path.join(ROOT, "tests", "measure", "test_xbrl_hybrid_trust_seal.py"))
        self.assertNotRegex(hy, r"adapters/xbrl/(recipes|vocabulary)\.py")
        # 6 本のうち、いま recipes.py か vocabulary.py の sha16 を字で持つもの
        for rel in PIN_FILES_ENGINE_LATER:
            t = text(os.path.join(ROOT, rel))
            self.assertTrue(re.search(r"adapters/xbrl/(recipes|vocabulary)\.py\"?:", t), rel)

    def test_10_limits_are_written(self):
        b = sec(self.t, "## §3", "## §4")
        for s in (u"代価 26 行は 67 書類の数。別の書類では増えうる。",
                  u"`_prior_cue`(直前 12 字)と `_prior_cue_clause`(同じ節)の字の規則。「前期比」は当期扱い。",
                  u"手がかりの字の一覧を広げる直しはこの封に含めない。", u"金額だけが問題", u"穴 A(ポイント)はこの封で直さない"):
            self.assertIn(s, b, s)

    def test_11_closed_file_list(self):
        b = sec(self.t, "## §4")
        first = b[:b.index(u"\n順序:")]
        pos = []
        for rel in FILES:
            tok = "`%s`" % rel
            self.assertEqual(first.count(tok), 1, rel)
            pos.append(first.index(tok))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        self.assertEqual(len(FILES), 5)
        engine = [first.index("`adapters/xbrl/vocabulary.py`(P22)"), first.index("`adapters/xbrl/recipes.py`(最初の枝)")]
        self.assertLess(max(engine), pos[0])      # engine 2 file が試験より先
        self.assertIn(u"→ pin の遷移の宣言 → 覆い。", first)
        self.assertIn(u"`vocabulary.py` の `DEFAULT_PROFILE = \"P22\"` + 既定の字の試験 + pin", first)
        order = b[b.index(u"\n順序:"):]
        self.assertIn(u"人間の承認(済み、2026-10-20「君に任せる」)→ この封 + 封の門を commit → 段 1 実装(別席)→ 凍結 → 独立監査 → commit → 結果を人間に見せる → 段 2 の承認 → 段 2 → 監査 → commit。", order)


class EngineAtSealTest(unittest.TestCase):
    """封の commit 時点の engine を字で留め、段 1 の後は「宣言された遷移」の値だけを受け入れる(docstring)。"""

    def test_12_engine_sha_is_the_one_at_the_seal_or_a_declared_transition(self):
        for rel, want in sorted(ENGINE_AT_SEAL.items()):
            got = sha16(rel)
            if got != want and rel in ENGINE_LATER:
                later, seal_rel = ENGINE_LATER[rel]
                added = git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split()
                self.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている(段 1 の commit で ENGINE_LATER に遷移を宣言する)**" % rel)

    def test_13_default_is_p22_from_step_2_and_p22_is_registered_with_the_flag(self):
        from adapters.xbrl import vocabulary as V
        # 2026-10-20(段 2): 既定を P21 -> P22 にした(人間の承認 2026-10-20「任せる」)。段 1 3320c8c までは P21 のままだった。
        # 2026-10-23(P26 の段 2。封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)で P22 -> P26。P22 は P26 の土台で PROFILES に在り旗 period_bind が真のまま(下)。
        self.assertEqual(V.DEFAULT_PROFILE, "P26")
        self.assertIn("P21", V.PROFILES)      # 古い既定は消えていない(明示で呼べる)
        # 封の commit 時点は「P22 は PROFILES に無い」だった(測った当時の事実)。段 1 の commit で「P22 は PROFILES に在り、
        # 旗 period_bind が真」に直した。旗は P22 だけ。
        self.assertIn("P22", V.PROFILES)
        self.assertTrue(V.PROFILES["P22"].period_bind)
        # 2026-10-21: P23 = P22 + 率の旗 + truncate_abs_band は period_bind を引き継ぐ(封 XBRL_ROUNDING_SEAL_2026-10-21)
        # 2026-10-21: P24 = P23 + 旗 2 つも period_bind を引き継ぐ(封 XBRL_VOCAB_SEAL_2026-10-21)
        # 2026-10-21: P25 = P24 + 旗 1 つも period_bind を引き継ぐ(封 XBRL_LASTBRANCH_SEAL_2026-10-21)
        # 2026-10-22: P26 = P25 + 旗 5 つ(封 XBRL_P26_SEAL_2026-10-21)も引き継ぐ
        # 2026-10-27: P27 = P26 + 旗 4 つ・P27E = P27 + 旗 1 つ(封 XBRL_P27_SEAL_2026-10-27)も引き継ぐ
        self.assertEqual(["P22", "P23", "P24", "P25", "P26", "P27", "P27E"], sorted(n for n, p in V.PROFILES.items() if p.period_bind))


class LiveReproductionTest(unittest.TestCase):
    """cache(~/.cache/audit-core/edinet/*.zip)と AUDIT_CORE_PERIOD_BIND=1 のとき、§0 の代価 26・手がかりあり 190・当期 1,726・
    pointer 1 本の GROUNDED 1,942・全 GROUNDED 4,267 を、67 書類に P21 の verify_document を掛けて数え直す(約 40 秒)。
    §0 の数は P21 で測った数なので、2026-10-20(段 2)に既定が P22 になった後は P21 を**明示**する(字で留める)。
    **既定では走らせない**(重いので。走らせない間も SealTest が封の字と記録を縛る)。"""

    CUE = re.compile(u"前期|前年|前連結会計年度|前事業年度|\\(同|（同|前期末|前年度")

    def test_g1_cost_26_is_reproduced(self):
        if os.environ.get("AUDIT_CORE_PERIOD_BIND") != "1":
            self.skipTest(u"AUDIT_CORE_PERIOD_BIND=1 のときだけ走る(約 40 秒)")
        zips = sorted(glob.glob(CACHE_GLOB))
        if not zips:
            self.fail(u"AUDIT_CORE_PERIOD_BIND=1 なのに cache(~/.cache/audit-core/edinet/*.zip)が無い")
        spec = importlib.util.spec_from_file_location("fp_pb_gate", os.path.join(ROOT, "measure", "false_pass_2026-10-14.py"))
        fp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fp)
        from adapters.xbrl.verify_document import verify_document
        n = s0_numbers(s0(text(SEAL)))
        docs = grounded = single = prior_no_cue = prior_cue = cur = 0
        for z in zips:
            with open(z, "rb") as fh:
                zb = fh.read()
            try:
                fp.mdna_text(zb)
            except KeyError:
                continue
            docs += 1
            for c in verify_document(zb, "P21", None)["claims"]:      # §0 の数は P21 で測った。2026-10-20(段 2)で既定は P22 になったので P21 を明示
                if c["state"] != "GROUNDED":
                    continue
                grounded += 1
                if len(c["pointers"]) != 1:
                    continue
                single += 1
                if c["pointers"][0].split("@")[-1].startswith("Prior1Year"):
                    if self.CUE.search(c["span"] or ""):
                        prior_cue += 1
                    else:
                        prior_no_cue += 1
                else:
                    cur += 1
        self.assertEqual(docs, n["with_text"])
        self.assertEqual((grounded, single), (n["grounded_all"], n["single"]))
        self.assertEqual((prior_no_cue, prior_cue, cur), (n["cost"], n["cue"], n["cur"]))


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
