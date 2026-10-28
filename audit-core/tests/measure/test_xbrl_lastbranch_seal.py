# -*- coding: utf-8 -*-
u"""最後の枝の名指しは証拠があるときだけ「違う」と言う(P25 = P24 + 旗 `last_branch_names_only_if_evidence`)の封の門
docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md を固定する。
人間の承認の引用・予測 L-1〜L-9 と外れ方と幅の算術・§0 の数(P24 の 4 state は記録 `vocab_2026-10-21.json` と突き合わせ、試作の数は
字のまま留めて内訳の和を縛る)・§1 の旗の形と規則・触る枝の中の人間の決定(8 つ。engine の字に在ること)・過去の門の engine の留めの一覧・
§3 の限界・§4 の file 一覧と順序・封が実装より先であること(順序)・**封の commit 時点の engine 3 file の sha**を縛る。

**この門の engine の留め(test_13・test_14)は、段 1 の commit で「宣言された遷移」に更新する前提である**(P24 の封の門
tests/measure/test_xbrl_vocab_seal.py の test_13・test_14 と同じ型)。
この封は engine(adapters/xbrl/vocabulary.py・recipes.py・registry_setup.py)を変える封なので、段 1 で sha が動く。そのとき
`ENGINE_LATER` に (段 1 の後の sha16, この封の path) を 3 file 分足し、`test_14` の「旗 `last_branch_names_only_if_evidence` は Profile に無い・
P25 は PROFILES に無い・理由 `no_same_value` は engine に無い」を「旗は Profile に在り P25 だけが真・P25 は PROFILES に在り DEFAULT_PROFILE は
P22 のまま・`no_same_value` は registry_setup.py に在る」に直す(他の pin ― P24 までの封・結果の門の ENGINE_LATER 群(test_10 の 14 本)・
cd_seal の FROZEN_LATER・frozen_bundle の世代・axis3 の LATER_ENGINE_COMMITS ― も同じ便で宣言する。封 §1 の一覧)。
段 2(既定 P22 → P25)でもう一度、`DEFAULT_PROFILE` の assert を直す。

**§0 の 583(P24 の VALUE_MISMATCH 1,203 のうち「最後の枝の名指し」)は、記録から数えられない。** 記録 `vocab_2026-10-21.json` は P23 → P24 で
動いた 369 行しか行を持たず(動かなかった VALUE_MISMATCH の行は無い)、動いた行の P23 の reason は VALUE_MISMATCH では全部 None
(最後の枝の名指しと他の枝を reason で分けられない)。583 を数えるには P24 の engine で 67 書類を走らせ直し、最後の枝に入った行を
engine の側で印づけるしかなく、それは engine を変えることになる(この門は engine 0 行)。だから 583 は**字だけ**留め、
動かせる関係(583 − 577 = 6 = 残る行、1,203 − 577 = 626、583 ≤ 1,203、(i)(ii)(iii) の 2 + 2 + 2 = 6)を縛る。
実物で 583 を数え直すのは段 1 の結果の門(L-1 の測定)の仕事。

試作 v1〜v3 の数(637・566・228・82・245・577・240・337・1,154 など)は scratchpad の報告(追跡外、正本でない)から封に写した数で、
この門は字と内訳の和だけを縛る。記録に無い数を「測った」とは言わない。"""
import dataclasses
import glob
import hashlib
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

SEAL_REL = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"    # 2026-10-22 追記: P26 の段 1(下の ENGINE_LATER の遷移)
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
SEAL_DEFAULT_P27 = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"    # 2026-10-28 追記: 既定を P26 -> P27 に切り替える 段 2(下の遷移。vocabulary.py の DEFAULT_PROFILE の 1 行と注記 +5 行・-1 行、verify_document.py の docstring の 1 行 +1 行・-1 行だけ)
SEAL = os.path.join(ROOT, SEAL_REL)
VOCAB_JSON = os.path.join(ROOT, "fixtures", "xbrl", "vocab_2026-10-21.json")

# §4 の file 一覧(この順で書かれている)
ENGINE_FILES = ("adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py")
P25_UNIT_TEST = "tests/adapters/xbrl/test_recipes_p25.py"
P24_UNIT_TEST = "tests/adapters/xbrl/test_recipes_p24.py"   # 既存。§4 では basename で書かれ、1 本足す
FILES = ("measure/xbrl_lastbranch_2026-10-21.py",
         "fixtures/xbrl/lastbranch_2026-10-21.json",
         "docs/XBRL_LASTBRANCH_RESULT_2026-10-21.md",
         "tests/measure/test_xbrl_lastbranch_result.py")
# 封より後でなければ git 履歴に現れてはならない新規 file(§4 の 5 本。test_recipes_p24.py は既存なので入れない)
AFTER = (P25_UNIT_TEST,) + FILES

# 封の commit 時点の engine(sha256 の先頭 16 桁。P24 段 1 の c7ad668 の後の木)。**ここは宣言された遷移の前の値**で、消さない。
ENGINE_AT_SEAL = {"adapters/xbrl/vocabulary.py": "83498c04a7b70396",
                  "adapters/xbrl/recipes.py": "3461c3f8b7af6675",
                  "adapters/xbrl/registry_setup.py": "9a0b08954cf22639"}
# 宣言された遷移(段 1 の commit で足す): {path: (後の sha16, 遷移を宣言した封の path)}。封の commit 時点では空。
# 2026-10-21 追記(段 1 の実装): vocabulary.py は旗 last_branch_names_only_if_evidence・P25・PROFILES の登録(+7 行・-0 行)、recipes.py は最後の枝の証拠の判定の塊
# (+72 行・-0 行。既存の行は 1 つも書き換えない)、registry_setup.py は理由 no_same_value(+2 行)。comparators.py・core/ は 0 行。DEFAULT_PROFILE は P22 のまま。
# ENGINE_AT_SEAL は残す(封の commit 時点の値)。
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
# 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
# 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
# 85896a67913ce1e7(P27 の段 2) は残す(測った時点の値。vocabulary.py の sha16)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 514ebb8104451c07。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
ENGINE_LATER = {"adapters/xbrl/vocabulary.py": ("514ebb8104451c07", SEAL_DEFAULT_P27),
                # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に G1〜G5 の塊(+251 行・-1 行。既存の行の書き換えは数の読み取りの for 文 1 行だけ) を足した。
                # bff243f13429b553(P25 の段 1)は残す(測った時点の値)、P26 の段 1 で 181b370420ab751b。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
                "adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27),
                # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で registry_setup.py に理由 3 つ(+6 行) を足した。
                # f42ffe23aaa7673b(P25 の段 1)は残す(測った時点の値)、P26 の段 1 で 7f2cbded9c830211。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
                "adapters/xbrl/registry_setup.py": ("d6f25750bcd73c0a", SEAL_P27)}

# §1「過去の門の engine の留め」の一覧(封の字)と、実物の在りか。
# ENGINE_LATER を持つ門 14 本 = ENGINE_LATER 系 6 本 + 結果 / 封の門 8 本(point_prior_result・ritual_result・period_bind seal/result・
# rounding seal/result・vocab seal/result)。registry_setup の sha を留める門はこの 14 本の中に在る。
PIN_FILES_ENGINE_LATER = ("tests/measure/test_xbrl_branch_a.py", "tests/measure/test_xbrl_role_swap_result.py",
                          "tests/measure/test_xbrl_axis3_decision.py", "tests/measure/test_xbrl_p20_result.py",
                          "tests/measure/test_xbrl_a_core_vs_grep_seal.py", "tests/measure/test_xbrl_pnf_diag.py")
PIN_GATES = ("tests/measure/test_xbrl_point_prior_result.py", "tests/measure/test_xbrl_ritual_result.py",
             "tests/measure/test_xbrl_period_bind_seal.py", "tests/measure/test_xbrl_period_bind_result.py",
             "tests/measure/test_xbrl_rounding_seal.py", "tests/measure/test_xbrl_rounding_result.py",
             "tests/measure/test_xbrl_vocab_seal.py", "tests/measure/test_xbrl_vocab_result.py")
OTHER_PINS = {"tests/measure/test_xbrl_axis3_decision.py": "LATER_ENGINE_COMMITS",
              "tests/measure/test_xbrl_cd_seal.py": "FROZEN_LATER",
              "fixtures/frozen_bundle_sha.py": "FROZEN_BUNDLE_GENERATIONS"}

# 封が名指す人間の決定・直前の commit が履歴に在る(封 §1・§4)
DECISION_COMMITS = ("5eb80a2", "3320c8c", "7d530cc", "8fc113f", "c7ad668", "92ae5e9")


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


def one(pattern, b, label):
    m = re.search(pattern, b)
    assert m, u"§0 の書き方が変わった: " + label
    return m


def s0_numbers(b):
    """§0 の数を、書かれた字のまま取り出す(書き方が変わったら落ちる)。"""
    m_p24 = one(r"67 書類 ([\d,]+) claim を P24 で: GROUNDED ([\d,]+)、VALUE_MISMATCH ([\d,]+)、UNVERIFIABLE ([\d,]+)、POINTER_NOT_FOUND ([\d,]+)", b, "P24 の 4 state")
    m_last = one(r"VALUE_MISMATCH ([\d,]+) のうち \*\*(\d+) は最後の枝の名指し\*\*", b, "最後の枝の名指し")
    m_v1 = one(r"k = 2 で VM ([\d,]+) → (\d+)。VM → PNF に動いた (\d+) 行から書類ごとに上限 4 行の決め打ちの抽出で (\d+) 行\((\d+) 書類\)を読み、"
               r"正しい文 (\d+)・文が本当に違う (\d+)・分からない (\d+)", b, "試作 v1 の読み")
    m_v1c = one(r"儀式の止め (\d+) / (\d+) が「違う」→「要確認」\(10 倍の注入 (\d+)・±1 単位 (\d+)\)、段 2 の注入 (\d+) / (\d+)", b, "試作 v1 の代価")
    m_v3 = one(r"VM ([\d,]+) → (\d+)\(動いた (\d+) 行は全部 VM → PNF `no_same_value`", b, "試作 v3 の VM")
    m_rest = one(r"最後の枝で VM に残る (\d+) 行\(\(i\) (\d+)・\(ii\) (\d+)・\(iii\) (\d+)\)は全部読み正しい文\(偶然の近さ (\d+) を含む\)", b, "残る行")
    m_read = one(r"読んだ (\d+) 行\(v1 の抽出 (\d+) \+ (\d+)\)は正しい文 (\d+)・分からない (\d+)・違う (\d+)、\*\*残り (\d+) 行は読んでいない\*\*", b, "読んだ行")
    m_hb = one(r"穴 B 通した (\d+) / (\d+)・止め → 要確認 (\d+)", b, "穴 B")
    m_rt = one(r"儀式 通した (\d+) / (\d+)\(N069・N096\)・止め → 要確認 (\d+)\(10 倍 (\d+)・±1 単位 (\d+)\)", b, "儀式")
    m_s2 = one(r"段 2 の材料 注入の GROUNDED (\d+) / (\d+)・止め → 要確認 (\d+) / (\d+)", b, "段 2 の材料")
    m_in = one(r"動いた行への注入 ([\d,]+) 回\(有効 ([\d,]+)\)で GROUNDED は P24 (\d+)・P25 (\d+)", b, "注入")
    m_n9 = one(r"n = ±9 の効き目は段 2 の注入 (\d+) 行だけ\(無改変 (\d+)\)", b, "n = ±9")
    m_rd = one(r"既存試験の赤 (\d+)\(登録の一覧 (\d+)・test_mutations (\d+)・sha (\d+)・diff の門 (\d+)、数 / state の門 (\d+)、人間の決定の字の門 (\d+)\)", b, "既存試験の赤")
    m_df = one(r"engine recipes \+(\d+)/−(\d+)・vocabulary \+(\d+)/−(\d+)・registry_setup \+(\d+)/−(\d+)", b, "engine の行数")
    m_ca = one(r"手元の cache の 67 の外 214 書類は全部 jpsps", b, "cache の外 214")
    return {"claims": num(m_p24.group(1)), "g": num(m_p24.group(2)), "vm": num(m_p24.group(3)),
            "unv": num(m_p24.group(4)), "pnf": num(m_p24.group(5)),
            "vm_last_den": num(m_last.group(1)), "last": int(m_last.group(2)),
            "v1_vm_before": num(m_v1.group(1)), "v1_vm_after": int(m_v1.group(2)), "v1_moved": int(m_v1.group(3)),
            "v1_read": int(m_v1.group(4)), "v1_read_docs": int(m_v1.group(5)),
            "v1_right": int(m_v1.group(6)), "v1_wrong": int(m_v1.group(7)), "v1_unknown": int(m_v1.group(8)),
            "v1_rit_stop": int(m_v1c.group(1)), "v1_rit_den": int(m_v1c.group(2)), "v1_rit_x10": int(m_v1c.group(3)),
            "v1_rit_pm1": int(m_v1c.group(4)), "v1_s2": int(m_v1c.group(5)), "v1_s2_den": int(m_v1c.group(6)),
            "v3_vm_before": num(m_v3.group(1)), "v3_vm_after": int(m_v3.group(2)), "moved": int(m_v3.group(3)),
            "rest": int(m_rest.group(1)), "rest_i": int(m_rest.group(2)), "rest_ii": int(m_rest.group(3)),
            "rest_iii": int(m_rest.group(4)), "rest_chance": int(m_rest.group(5)),
            "read": int(m_read.group(1)), "read_v1": int(m_read.group(2)), "read_extra": int(m_read.group(3)),
            "read_right": int(m_read.group(4)), "read_unknown": int(m_read.group(5)), "read_wrong": int(m_read.group(6)),
            "unread": int(m_read.group(7)),
            "hole_b_pass": int(m_hb.group(1)), "hole_b_den": int(m_hb.group(2)), "hole_b_unv": int(m_hb.group(3)),
            "rit_pass": int(m_rt.group(1)), "rit_den": int(m_rt.group(2)), "rit_unv": int(m_rt.group(3)),
            "rit_x10": int(m_rt.group(4)), "rit_pm1": int(m_rt.group(5)),
            "s2_g": int(m_s2.group(1)), "s2_g_den": int(m_s2.group(2)), "s2_unv": int(m_s2.group(3)), "s2_unv_den": int(m_s2.group(4)),
            "inj": num(m_in.group(1)), "inj_valid": num(m_in.group(2)), "inj_p24_g": int(m_in.group(3)), "inj_p25_g": int(m_in.group(4)),
            "n9_s2": int(m_n9.group(1)), "n9_plain": int(m_n9.group(2)),
            "red": int(m_rd.group(1)), "red_list": int(m_rd.group(2)), "red_mut": int(m_rd.group(3)),
            "red_sha": int(m_rd.group(4)), "red_diff": int(m_rd.group(5)),
            "red_state": int(m_rd.group(6)), "red_decision": int(m_rd.group(7)),
            "rec_ins": int(m_df.group(1)), "rec_del": int(m_df.group(2)), "voc_ins": int(m_df.group(3)),
            "voc_del": int(m_df.group(4)), "reg_ins": int(m_df.group(5)), "reg_del": int(m_df.group(6)),
            "cache_outside": 214, "docs": 67}


def rng(line, tag_re):
    m = re.search(tag_re, line)
    assert m, tag_re
    return num(m.group(1)), num(m.group(2))


class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)

    def test_1_human_approval_is_quoted_and_the_seal_says_it_changes_the_engine(self):
        head = self.t[:self.t.index("\n## §0 ")]
        self.assertIn(u"**この封は engine(`adapters/xbrl/vocabulary.py`・`recipes.py`・`registry_setup.py`)を変える。人間の承認(2026-10-21 深夜): ", head)
        self.assertIn(u"人間「engine に触るので承認が要る → 先に承認しておくので好きに進めて これをもって承認とする」、", head)
        self.assertIn(u"続けて「その先の展望まで全て進めといてね」", head)
        self.assertIn(u"(司令塔が示した展望: 丸めの帯 P23 → 語彙と枠 P24 → 最後の枝 P25 → 日本語の報告形 → 既定の切り替えは 1 回にまとめて人間に)。", head)
        self.assertIn(u"作法は変えない(封 → 実装 → 凍結 → 独立監査 GO → commit)。", head)
        self.assertIn(u"数を見てから封・予測を直さない。外れは外れとして残す。P24 段 1(c7ad668、宣言 92ae5e9)の後に置く。**", head)
        self.assertTrue(head.startswith(u"# 封: 最後の枝の名指しは証拠があるときだけ「違う」と言う(engine の直し P25 = P24 + 旗 1 つ)― 2026-10-21"))

    def test_2_nine_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §2", "## §3")
        ids, lines = predictions(b, "L")
        self.assertEqual(ids, [str(i) for i in range(1, 10)])
        self.assertEqual(len(lines), 9)
        for line in lines:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[1], u"予測が空: " + line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        by = dict((i, l) for i, l in zip(ids, lines))
        # 行ごとに、予測の幅と外れ方の両方を字で縛る(幅を直すと赤くなる)
        for i, ss in (("1", (u"67 書類の無改変で VALUE_MISMATCH **620〜632**(P24 1,203)", u"動く行は全部 VM → POINTER_NOT_FOUND `no_same_value` で **570〜584**",
                             u"GROUNDED と UNVERIFIABLE の数は P24 と同じ", u"幅の外 / 他の向きが 1 行以上")),
                      ("2", (u"最後の枝で VM に残る行 **4〜8**", u"全部読んで「文が本当に違う」**0〜1**", u"幅の外")),
                      ("3", (u"**試作で読んでいない VM → PNF の行を全部読み、", u"「文が本当に違う」が読んだ行の 2% 以下**",
                             u"2% 超")),
                      ("4", (u"穴 B の 485 件を P25 で通す **0**", u"止め(P24 で VALUE_MISMATCH の 483)のうち → 要確認 **0〜4**", u"通す 1 以上 / 5 以上")),
                      ("5", (u"儀式を P25 で: 通した **2〜3**", u"注入の止め → 要確認 **26〜34**(素の書類の VM の動きは含めない)", u"幅の外")),
                      ("6", (u"段 2 の材料: 注入の GROUNDED **0 / 64**", u"注入の止め → 要確認 **0〜2**", u"幅の外")),
                      ("7", (u"67 書類で P24 → P25 に動いた全行への注入(1 回に 1 件、末尾の桁 ±3・10 倍、試作と同じ作り方)で", u"P25 が GROUNDED にする **0** 回",
                             u"1 回以上")),
                      ("8", (u"engine の差分 `recipes.py` **+60〜+90 / −0**", u"`vocabulary.py` **≤ 10 行**", u"`registry_setup.py` **≤ 5 行**(行数は挿入 + 削除)",
                             u"`comparators.py`・`core/` 0 行", u"既存試験の赤は登録の一覧・旗の形・sha の留め・diff の門だけ",
                             u"(数 / state の門 0、人間の決定の字の門 0)", u"超える / `recipes.py` の削除 1 行以上 / 種類の外の赤")),
                      ("9", (u"段 2(既定 P22 → P25 をまとめて 1 回)は人間に 3 つの率(誤りを通す率・無改変で「違う」と言う率・結べない率)と、",
                             u"「違う」が「要確認」に移る注入の数を見せてから"))):
            for s in ss:
                self.assertIn(s, by[i], u"L-%s: %s" % (i, s))
        self.assertIn(u"**L-1・L-2・L-4〜L-7 は試作の再現で、外れるなら実装が試作と違うことを示す。本当に外れうるのは L-3(試作で読んでいない 337 行)である。**", b)
        self.assertIn(u"新しい標本は手元に無い(§0)。", b)

    def test_3_prediction_arithmetic_is_consistent(self):
        """予測の幅が §0 の試作の数を含む(幅どうし・幅と試作の整合)。片方だけ直すと赤くなる。"""
        n = s0_numbers(s0(self.t))
        b = sec(self.t, "## §2", "## §3")
        _, lines = predictions(b, "L")
        # L-1: VM の幅は試作の 626 を含み、動く行の幅は 577 を含む。P24 の 1,203 − 動く行 = VM
        lo, hi = rng(lines[0], r"VALUE_MISMATCH \*\*([\d,]+)〜([\d,]+)\*\*")
        self.assertLessEqual(lo, hi)
        self.assertTrue(lo <= n["v3_vm_after"] <= hi, (lo, n["v3_vm_after"], hi))
        lo2, hi2 = rng(lines[0], r"`no_same_value` で \*\*(\d+)〜(\d+)\*\*")
        self.assertLessEqual(lo2, hi2)
        self.assertTrue(lo2 <= n["moved"] <= hi2, (lo2, n["moved"], hi2))
        # 2 つの幅は同じ P24 の 1,203 を介して整合する: VM の幅は [1,203 − 動く行の幅の上、1,203 − 動く行の幅の下] の中(動く行の他に VM は動かない)
        self.assertEqual(num(re.search(r"\(P24 ([\d,]+)\)", lines[0]).group(1)), n["vm"])
        self.assertTrue(n["vm"] - hi2 <= lo and hi <= n["vm"] - lo2, (n["vm"] - hi2, lo, hi, n["vm"] - lo2))
        # L-2: 残る行 4〜8 は試作の 6 を含み、読んだ「違う」0〜1 は試作の 0 を含む
        lo, hi = rng(lines[1], r"VM に残る行 \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["rest"] <= hi, (lo, n["rest"], hi))
        lo, hi = rng(lines[1], r"「文が本当に違う」\*\*(\d+)〜(\d+)\*\*")
        self.assertEqual(n["read_wrong"], 0)
        self.assertTrue(lo <= 0 <= hi)
        # L-3: 2% は読んでいない行 337 に対して 6 行まで(7 行目で 2.08%)。337 行の分母は 577 − 240
        self.assertEqual(n["unread"] * 2 // 100, 6)
        self.assertGreater(7 * 100, n["unread"] * 2)
        self.assertEqual(n["moved"] - n["read"], n["unread"])
        # L-4: 穴 B の止め → 要確認 0〜4 は試作の 2 を含み、通す 0
        lo, hi = rng(lines[3], r"→ 要確認 \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["hole_b_unv"] <= hi)
        self.assertEqual(n["hole_b_pass"], 0)
        # L-5: 儀式の通した 2〜3 は試作の 2 を含み、止め → 要確認 26〜34 は試作の 30 を含む
        lo, hi = rng(lines[4], r"通した \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["rit_pass"] <= hi)
        lo, hi = rng(lines[4], r"止め → 要確認 \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["rit_unv"] <= hi, (lo, n["rit_unv"], hi))
        # L-6: 段 2 の材料の注入の GROUNDED 0 / 64、止め → 要確認 0〜2 は試作の 1 を含む
        self.assertIn("**%d / %d**" % (n["s2_g"], n["s2_g_den"]), lines[5])
        self.assertEqual(n["s2_g"], 0)
        lo, hi = rng(lines[5], r"止め → 要確認 \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["s2_unv"] <= hi)
        # L-7: P25 が GROUNDED にする 0 回は試作の 0 と同じ
        self.assertIn("**%d** 回" % n["inj_p25_g"], lines[6])
        self.assertEqual(n["inj_p25_g"], 0)
        # L-8: engine の行数の試作は幅の中(recipes +72 は +60〜+90、vocabulary +7 は ≤ 10、registry_setup +2 は ≤ 5)
        lo, hi = rng(lines[7], r"`recipes.py` \*\*\+(\d+)〜\+(\d+) / −0\*\*")
        self.assertLessEqual(lo, hi)
        self.assertTrue(lo <= n["rec_ins"] <= hi)
        self.assertEqual(n["rec_del"], 0)
        self.assertLessEqual(n["voc_ins"] + n["voc_del"], num(re.search(r"`vocabulary.py` \*\*≤ (\d+) 行\*\*", lines[7]).group(1)))
        self.assertLessEqual(n["reg_ins"] + n["reg_del"], num(re.search(r"`registry_setup.py` \*\*≤ (\d+) 行\*\*", lines[7]).group(1)))

    def test_4_section_0_numbers_are_pinned_as_written(self):
        b = s0(self.t)
        n = s0_numbers(b)
        # P24 の 4 state(7,799 claim)。記録との突き合わせは test_5
        self.assertEqual((n["claims"], n["g"], n["vm"], n["unv"], n["pnf"]), (7799, 4382, 1203, 1397, 817))
        self.assertEqual(n["g"] + n["vm"] + n["unv"] + n["pnf"], n["claims"])
        # 最後の枝の名指し 583 は VM 1,203 の一部。583 は記録から数えられない(docstring)ので字で留め、関係を縛る
        self.assertEqual((n["vm_last_den"], n["last"]), (1203, 583))
        self.assertEqual(n["vm_last_den"], n["vm"])
        self.assertLessEqual(n["last"], n["vm"])
        # 試作 v1: VM 1,203 → 637 = −566。読んだ 228 行(64 書類)は正しい 227 + 違う 0 + 分からない 1。代価 82 = 71 + 11
        self.assertEqual((n["v1_vm_before"], n["v1_vm_after"], n["v1_moved"]), (1203, 637, 566))
        self.assertEqual(n["v1_vm_before"] - n["v1_moved"], n["v1_vm_after"])
        self.assertEqual((n["v1_read"], n["v1_read_docs"]), (228, 64))
        self.assertEqual((n["v1_right"], n["v1_wrong"], n["v1_unknown"]), (227, 0, 1))
        self.assertEqual(n["v1_right"] + n["v1_wrong"] + n["v1_unknown"], n["v1_read"])
        self.assertEqual((n["v1_rit_stop"], n["v1_rit_den"], n["v1_rit_x10"], n["v1_rit_pm1"]), (82, 245, 71, 11))
        self.assertEqual(n["v1_rit_x10"] + n["v1_rit_pm1"], n["v1_rit_stop"])
        self.assertEqual((n["v1_s2"], n["v1_s2_den"]), (11, 27))
        # 試作 v3: VM 1,203 → 626 = −577。残る 6 = (i) 2 + (ii) 2 + (iii) 2(偶然の近さ 3 を含む)。583 − 577 = 6
        self.assertEqual((n["v3_vm_before"], n["v3_vm_after"], n["moved"]), (1203, 626, 577))
        self.assertEqual(n["v3_vm_before"] - n["moved"], n["v3_vm_after"])
        self.assertEqual((n["rest"], n["rest_i"], n["rest_ii"], n["rest_iii"], n["rest_chance"]), (6, 2, 2, 2, 3))
        self.assertEqual(n["rest_i"] + n["rest_ii"] + n["rest_iii"], n["rest"])
        self.assertEqual(n["last"] - n["moved"], n["rest"])
        self.assertLessEqual(n["rest_chance"], n["rest"])
        # 読んだ 240 = v1 の抽出 227 + 13。読み: 正しい 239・分からない 1・違う 0。残り 337 = 577 − 240
        self.assertEqual((n["read"], n["read_v1"], n["read_extra"]), (240, 227, 13))
        self.assertEqual(n["read_v1"] + n["read_extra"], n["read"])
        self.assertEqual((n["read_right"], n["read_unknown"], n["read_wrong"]), (239, 1, 0))
        self.assertEqual(n["read_right"] + n["read_unknown"] + n["read_wrong"], n["read"])
        self.assertEqual(n["unread"], 337)
        self.assertEqual(n["read"] + n["unread"], n["moved"])
        # 穴 B 0 / 485・止め → 要確認 2、儀式 2 / 247・止め → 要確認 30 = 10 倍 19 + ±1 単位 11
        self.assertEqual((n["hole_b_pass"], n["hole_b_den"], n["hole_b_unv"]), (0, 485, 2))
        self.assertEqual((n["rit_pass"], n["rit_den"], n["rit_unv"], n["rit_x10"], n["rit_pm1"]), (2, 247, 30, 19, 11))
        self.assertEqual(n["rit_x10"] + n["rit_pm1"], n["rit_unv"])
        self.assertEqual((n["s2_g"], n["s2_g_den"], n["s2_unv"], n["s2_unv_den"]), (0, 64, 1, 27))
        # 注入 1,154 回(有効 1,118)= 動いた 577 行 × 2 型(末尾の桁 ±3・10 倍。試作の報告 v3-6 (d))。GROUNDED は P24 0・P25 0
        self.assertEqual((n["inj"], n["inj_valid"], n["inj_p24_g"], n["inj_p25_g"]), (1154, 1118, 0, 0))
        self.assertEqual(n["moved"] * 2, n["inj"])
        self.assertLessEqual(n["inj_valid"], n["inj"])
        self.assertEqual((n["n9_s2"], n["n9_plain"]), (1, 0))
        # 既存試験の赤 33 = 13 + 1 + 14 + 5(数 / state の門 0、人間の決定の字の門 0)
        self.assertEqual((n["red"], n["red_list"], n["red_mut"], n["red_sha"], n["red_diff"], n["red_state"], n["red_decision"]),
                         (33, 13, 1, 14, 5, 0, 0))
        self.assertEqual(n["red_list"] + n["red_mut"] + n["red_sha"] + n["red_diff"], n["red"])
        # engine の行数(試作)
        self.assertEqual((n["rec_ins"], n["rec_del"], n["voc_ins"], n["voc_del"], n["reg_ins"], n["reg_del"]), (72, 0, 7, 0, 2, 0))
        # 試作の経緯の字(k の効き方・v2 の失敗・同じ 67 書類)
        for s in (u"k = 1 は k = 2 と同じ、k = 5 は残る「違う」6 行が全部偽。",
                  u"試作 v2: 桁・単位の取り違え(10^n)を証拠に足したが、名指す fact の表示より下の端数も 10 倍になり帯から出て、10 倍は 71 → 64 しか戻らなかった。",
                  u"GROUNDED と UNVERIFIABLE は 1 行も動かない",
                  u"**試作は全部同じ 67 書類で測った。**",
                  u"= 新しい標本は手元に無い。",
                  u"**残り 337 行は読んでいない**",
                  u"司令塔の席の手元の報告 `scratchpad/lastbranch/proto_report.md`",
                  u"正本でない"):
            self.assertIn(s, self.t, s)

    def test_5_section_0_p24_numbers_match_the_records(self):
        """§0 の「P24 で」の数は、P24 段 1 の記録 fixtures/xbrl/vocab_2026-10-21.json と同じ。
        583(最後の枝の名指し)と試作 v1〜v3 の数は記録に無いので、ここでは突き合わせない(docstring)。"""
        n = s0_numbers(s0(self.t))
        r = jload(VOCAB_JSON)
        agg = r["W1W2W3"]["集計"]
        self.assertEqual(r["W1W2W3"]["総 claim"], n["claims"])
        self.assertEqual(agg["書類数"], n["docs"])
        self.assertEqual(agg["GROUNDED の合計 P24"], n["g"])
        self.assertEqual(agg["VALUE_MISMATCH の合計 P24"], n["vm"])
        self.assertEqual(agg["UNVERIFIABLE の合計 P24"], n["unv"])
        self.assertEqual(agg["POINTER_NOT_FOUND の合計 P24"], n["pnf"])
        # 書類別の states P24 を足しても同じ(合計の欄の取り違えを避ける)
        tot = {}
        for d in r["W1W2W3"]["書類"]:
            for k, v in d["states P24"].items():
                tot[k] = tot.get(k, 0) + v
        self.assertEqual(tot, {"GROUNDED": n["g"], "VALUE_MISMATCH": n["vm"], "UNVERIFIABLE": n["unv"], "POINTER_NOT_FOUND": n["pnf"]})
        self.assertEqual(sum(tot.values()), n["claims"])
        self.assertEqual(len(r["W1W2W3"]["書類"]), n["docs"])
        # 儀式 P24: 通した 2 / 247(N069・N096)、止めた 245。穴 B: 通した 0 / 485(止めた VM 483 + その他 2)
        w5 = r["W5"]
        self.assertEqual((w5["通した P24"]["件"], w5["通した P24"]["分母"]), (n["rit_pass"], n["rit_den"]))
        self.assertEqual(sorted(x["id"] for x in w5["通した P24 の一覧"]), ["N069", "N096"])
        self.assertEqual((w5["止めた P24"]["件"], w5["止めた P24"]["分母"]), (n["v1_rit_den"], n["rit_den"]))
        w4 = r["W4"]["集計"]
        self.assertEqual((w4["P24 で通した(GROUNDED のまま)"]["件"], w4["P24 で通した(GROUNDED のまま)"]["分母"]), (n["hole_b_pass"], n["hole_b_den"]))
        self.assertEqual(w4["P24 で止めた(VALUE_MISMATCH)"]["件"] + w4["P24 でその他"]["件"], n["hole_b_den"])
        # 段 2 の材料: 注入 64、Core 自身 P24 が GROUNDED にした 0、注入で VALUE_MISMATCH に止まっている行 27
        s2 = r["S2"]["集計"]
        self.assertEqual((s2["全注入で Core 自身 P24 が GROUNDED"]["件"], s2["全注入で Core 自身 P24 が GROUNDED"]["分母"]), (n["s2_g"], n["s2_g_den"]))
        inj = [x for x in r["S2"]["行"] if x["注入か"]]
        self.assertEqual(len(inj), n["s2_g_den"])
        self.assertEqual(len([x for x in inj if x["Core 自身 P24"]["state"] == "VALUE_MISMATCH"]), n["s2_unv_den"])
        # 動いた 369 行(P23 → P24。全 state)と、その向きの内訳。最後の枝の名指しは「P24 の VM」に含まれ、
        # P24 の VM に入っている行は P25 の対象。GROUNDED と UNVERIFIABLE の数が P24 のままになることが L-1 の約束
        self.assertEqual(agg["動いた(全 state)"], 369)
        # W7: 手元の cache の 67 の外 214 書類は全部 jpsps で claim 0 = 新しい標本が手元に無い(封 §0 の字を記録で縛る)
        w7 = r["W7"]
        self.assertEqual(len(w7["書類"]), n["cache_outside"])
        self.assertEqual(w7["集計"]["67 の外の書類"], n["cache_outside"])
        self.assertEqual(w7["集計"]["claim の合計(P24)"], 0)
        self.assertEqual(w7["集計"]["種別"], {"jpsps…-asr-": n["cache_outside"]})
        self.assertFalse(w7["集計"]["測れるか(claim が 1 以上の書類が 10 以上)"])
        self.assertEqual(r["書類の数"]["経営分析の文を持つ"], n["docs"])
        self.assertEqual(r["書類の数"]["67 の外"], n["cache_outside"])

    def test_6_section_1_flag_shapes_and_rules(self):
        b = sec(self.t, "## §1", "## §2")
        for s in (u"`Profile` に `last_branch_names_only_if_evidence: bool = False`。",
                  u"`P25 = dataclasses.replace(P24, name=\"P25\", last_branch_names_only_if_evidence=True)`、`PROFILES[\"P25\"] = P25` を足す",
                  u"(`PROFILES = {...}` の行の字は変えない)。",
                  u"**段 1 では既定にしない(DEFAULT_PROFILE = \"P22\" のまま)。** 旗が偽なら 1 行も変わらない。",
                  u"core/・comparators.py 0 行、既存の行は 1 行も書き換えない",
                  # 最後の枝の位置(P21 の枝の後ろ)
                  u"§1b の止め・F2′・P24 frame_rebind・F1′・F3b のどれにも当たらず、主語の当期の先頭 fact = 「名指す fact」を名指して VALUE_MISMATCH にする直前",
                  u"照合の帯は `vocabulary.match_value` が当てるもの(主張の桁・書類の丸め方・P23 の `_mag_trunc`)。",
                  # (i)(ii)(iii)
                  u"(i) 名指す fact と**同じ要素名・同じ枠**(context から期の接頭辞を除いた字が同じ)で context が違う JPY の fact(単位の字が JPY で始まる)のどれかが、文の値と照合の帯で合う(期の取り違えの証拠)。",
                  u"別の枠・別の要素は証拠にしない。",
                  u"(ii) `min(|名指す値 − 文の値|, ||名指す値| − |文の値||) ≤ 2 × 主張の桁`(桁の打ち間違いの証拠。`LAST_BRANCH_DIGIT_K = 2`)。",
                  u"(iii) `n ∈ (1, −1, 2, −2, 3, −3, 6, −6, 9, −9)` のどれかで、名指す値が 文の値 × 10^−n と帯「書かれた数の精度 × 10^−n」で合う(桁・単位の取り違えの証拠)。",
                  u"書かれた数の精度 = 主張の桁 × 10^(round(|文の値| / 主張の桁) の末尾の 0 の数)、round は Python の `round`(偶数丸め)。n が負のとき帯は 精度 × 10^|n| に広がる(文の値を 10^|n| 倍して比べる側の精度)。符号は問わない。",
                  # 結果
                  u"どれかが真なら今までどおり名指して VALUE_MISMATCH。",
                  u"どれも偽なら pointer を付けず POINTER_NOT_FOUND、reason は登録簿の固定の名前 `no_same_value`(`registry_setup._POINTER_NOT_FOUND_REASONS` と `_state_of` の 2 か所に登録)。",
                  u"名指す fact の要素・context・値は `Claim.provenance[\"no_same_value\"]` に残す(名指しは消さない)。"):
            self.assertIn(s, b, s)
        # P25 は P24 に旗 1 つを足したもの。P24 の旗は変えない・既定は P22 のまま
        p25 = re.search(r"`P25 = dataclasses\.replace\([^`]*\)`", b).group(0)
        self.assertIn("P24", p25)
        self.assertIn("last_branch_names_only_if_evidence=True", p25)
        self.assertNotIn("P23", p25)
        # 定数: 2 と 10 個の n(字で留める。定数から土台を作らない)
        n_list = re.search(r"`n ∈ \(([^)]*)\)`", b).group(1)
        self.assertEqual([x.strip().replace(u"−", "-") for x in n_list.split(",")], ["1", "-1", "2", "-2", "3", "-3", "6", "-6", "9", "-9"])
        # P24 の監査の軽い指摘の手当て(同じ便)
        for s in (u"**P24 の監査の軽い指摘の手当て(同じ便)**",
                  u"率の枠の取り直し (ii) の旗が偽のとき効かないことを 1 件で直接見る unit 試験を `tests/adapters/xbrl/test_recipes_p24.py` に 1 本足す(engine は変えない)。"):
            self.assertIn(s, b, s)

    def test_7_the_eight_decisions_in_the_touched_branch_are_listed(self):
        b = sec(self.t, "## §1", "## §2")
        line = [l for l in b.splitlines() if l.startswith(u"- **触る枝の中の人間の決定")][0]
        names = (u"2026-10-08 案ア(no_subject)", u"§1b の止め", u"C2 `period_cue`", u"C-1g §1-3 `_build_point_diff_claim`",
                 u"P21 の最後の枝(5eb80a2。この封は最後の枝の**後ろ**に証拠の判定を足すだけで、P21 の枝の字は変えない)",
                 u"P22 `period_bind`(`subj and`)", u"P23 `_mag_trunc`", u"P24 の旗 2 つ(c7ad668)")
        for s in names:
            self.assertIn(s, line, s)
        positions = [line.index(s) for s in names]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(names), 8)
        for s in (u"字も振る舞いも 1 つも壊さない", u"これらの字を探す既存の門は直さずに緑。",
                  u"P16/P20/P21/P22/P23/P24 を明示した試験の数は 1 つも変えない"):
            self.assertIn(s, line, s)

    def test_8_the_decisions_exist_in_the_engine_now(self):
        """封が名指した人間の決定が、いまの engine の字に在る(封が実物と食い違っていない)。段 1 の後も 1 つも壊さない約束なので、この assert は段 1 の後も残す。
        P24 の封の門 test_9 の一覧(案ア・§1b・C2・C-1g・P21 の最後の枝・P22 の period_bind・P23 の _mag_trunc)に、P24 の新しい関数と旗を足し、
        最後の枝の中の順(F2′ → frame_rebind → F1′ → F3b → 名指し)を字で留める(封 §1 が「どれにも当たらず」と書いた順)。"""
        r = text(os.path.join(ROOT, "adapters", "xbrl", "recipes.py"))
        v = text(os.path.join(ROOT, "adapters", "xbrl", "vocabulary.py"))
        i = r.index("def _direct_value_claim(")
        body = r[i:r.index("\ndef ", i + 1)]
        # 案ア・§1b・C2・P21 の最後の枝・P22 の period_bind(subj and)
        self.assertIn(u"案ア", body)
        self.assertIn('claim["reason"] = "no_subject"', body)
        self.assertIn('claim["reason"] = "no_element(no prior2 for prior-year diff)"', body)
        self.assertIn("profile.prior2_required", body)
        self.assertIn("profile.period_cue and _prior_cue(s, a, b)", body)
        self.assertIn('getattr(profile, "last_branch_cues", False)', body)
        self.assertIn('getattr(profile, "period_bind", False) and subj and not _prior_cue(s, a, b) and not _prior_cue_clause(s, a)', body)
        self.assertIn("last_branch_cues: bool = False", v)
        self.assertIn("period_bind: bool = False", v)
        # `_prior_cue_clause` は def 行がこの字
        self.assertIn("\ndef _prior_cue_clause(s, pos):\n", r)
        # C-1g §1-3 `_build_point_diff_claim` の 3 行(def 行・窓の `if` 行・呼び出しの行)
        self.assertIn("\ndef _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num, tol=PCT_TOLERANCE_DEFAULT):\n", r)
        j = r.index("def _build_point_diff_claim(")
        pbody = r[j:r.index("\ndef ", j + 1)]
        self.assertIn("    window = s[max(0, a - 25):a]\n    if not _POINT_PRIOR_PHRASE_RE.search(window):\n", pbody)
        self.assertIn('claim["reason"] = "no_element(point without prior phrase)"', pbody)
        self.assertIn('_POINT_PRIOR_PHRASE_RE = re.compile(r"前期比|前連結会計年度|前年")', r)
        self.assertIn('        if profile.point_diff and unit == "ポイント" and subj:\n            _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num, tol)\n', r)
        self.assertEqual(r.count("_build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num, tol)"), 1)
        # P23 の `_mag_trunc`
        k = r.index("def _mag_trunc(profile, rounding):")
        mbody = r[k:r.index("\ndef ", k + 1)]
        self.assertIn('getattr(profile, "truncate_on_magnitude", False)', mbody)
        self.assertIn('getattr(profile, "truncate_abs_band", False) and rounding == "truncate"', mbody)
        # P24 の旗 2 つ(c7ad668)と新しい関数
        self.assertIn("vocab_2026_10_21: bool = False", v)
        self.assertIn("frame_rebind: bool = False", v)
        self.assertIn('P24 = dataclasses.replace(P23, name="P24", vocab_2026_10_21=True, frame_rebind=True)', v)
        for sig in ("\ndef _prior_cue_clause_2026_10_21(s, pos):\n",
                    "\ndef _build_point_diff_claim_2026_10_21(claim, s, a, b, elems, member, facts, contexts, num, tol=PCT_TOLERANCE_DEFAULT):\n",
                    "\ndef _cf_total_facts(", "\ndef _cf_total_prior_cue(", "\ndef _cf_total_text_claim(",
                    "\ndef _unbind_other_frame(", "\ndef _frame_rebind_money(", "\ndef _frame_rebind_pct("):
            self.assertIn(sig, r, sig)
        self.assertIn('getattr(profile, "frame_rebind", False)', body)
        # 最後の枝の中の順(封 §1「どれにも当たらず」): F2′ → P24 frame_rebind → F1′ → F3b → 主語の当期の先頭 fact を名指す VALUE_MISMATCH
        order = ["# F2′: 枠(セグメントの member)が取れていないセグメント利益は全社の fact を名指さない。",
                 "# P24 frame_rebind(試作 v3): 取った枠で値が合わず、同じ要素の別の枠(当期)で値か a-b が合うなら",
                 "# F1′: 「前期は…」「(同…」の数は前期の fact を名指す(増減の語が無いときだけ)。",
                 "# F3b: 増減の文が当期の残高を選んだときは、残高 1 本ではなく残高の対(当期 - 前期)。",
                 '                claim["pointer"] = "xbrl:%s@%s" % (cur[0]["name"], cur[0]["context"])\n'
                 '                claim["bound"] = True\n'
                 '                claim["result"] = "VALUE_MISMATCH"\n'
                 '                claim["recomputed"] = cur[0]["value"]\n'
                 '                claim["reason"] = "value differs(segment/other period?)"\n']
        pos = []
        for s in order:
            self.assertEqual(body.count(s), 1, s[:40])
            pos.append(body.index(s))
        self.assertEqual(pos, sorted(pos), u"最後の枝の中の順が封 §1 の字と違う")
        # 決定の commit が履歴に在る(浅い clone では skip せず、在るかだけ見る)
        for c in DECISION_COMMITS:
            self.assertEqual(git("cat-file", "-e", c + "^{commit}").returncode, 0, u"封が名指す commit %s が無い" % c)

    def test_9_p24_flags_and_p25_base_are_unchanged(self):
        """P25 は P24 に積むので、P24 の旗は封の commit 時点のまま(P24 = P23 + 旗 2 つ)。段 1 の後も残す。"""
        from adapters.xbrl import vocabulary as V
        self.assertEqual(V.PROFILES["P24"], dataclasses.replace(V.P23, name="P24", vocab_2026_10_21=True, frame_rebind=True))
        self.assertEqual(V.DEFAULT_PROFILE, "P27")      # 段 1 の commit 時点は P22。2026-10-23 の P26 の段 2(封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)で P26、2026-10-28 の P27 の段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で P27
        for flag in ("vocab_2026_10_21", "frame_rebind"):
            self.assertEqual(sorted(n for n, p in V.PROFILES.items() if getattr(p, flag)), ["P24", "P25", "P26", "P27", "P27E"], flag)   # 2026-10-22: P26 = P25 + 旗 5 つ(封 XBRL_P26_SEAL_2026-10-21)も引き継ぐ。(2026-10-27: P27 = P26 + 旗 4 つ・P27E = P27 + 旗 1 つ。封 XBRL_P27_SEAL_2026-10-27)も引き継ぐ

    def test_10_engine_pins_list_is_written_and_exists(self):
        b = sec(self.t, "## §1", "## §2")
        line = [l for l in b.splitlines() if l.startswith(u"- **過去の門の engine の留め**")][0]
        for s in (u"ENGINE_LATER 系(branch_a・role_swap・axis3・p20_result・a_core_vs_grep・pnf_diag)", u"cd_seal FROZEN_LATER",
                  u"point_prior_result・ritual_result・period_bind(seal/result)・rounding(seal/result)・vocab(seal/result)",
                  u"registry_setup の sha を留める門", u"frozen_bundle の世代", u"axis3 LATER_ENGINE_COMMITS(次の便)"):
            self.assertIn(s, line, s)
        defining = set()
        for p in glob.glob(os.path.join(ROOT, "tests", "measure", "*.py")):
            if re.search(r"(?m)^ENGINE_LATER = \{", text(p)):
                defining.add("tests/measure/" + os.path.basename(p))
        listed = set(PIN_FILES_ENGINE_LATER) | set(PIN_GATES)
        self.assertEqual(len(PIN_FILES_ENGINE_LATER) + len(PIN_GATES), 14)
        self.assertEqual(len(listed), 14)
        # この封の門と、これから足す P25 の結果の門(lastbranch)を除いて、ENGINE_LATER を持つ門は一覧と一致する
        others = set(x for x in defining if "lastbranch" not in x)
        self.assertEqual(others, listed, u"ENGINE_LATER を持つ門と封の一覧が違う: 足りない %s / 余り %s" % (sorted(listed - others), sorted(others - listed)))
        for rel, name in sorted(OTHER_PINS.items()):
            self.assertTrue(re.search(r"(?m)^%s\b" % name, text(os.path.join(ROOT, rel))), rel + " の " + name)
        for rel in PIN_FILES_ENGINE_LATER + PIN_GATES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_11_limits_are_written(self):
        b = sec(self.t, "## §3", "## §4")
        for s in (u"**「違う」を「要確認」に弱める代価がある**",
                  u"誤りを**通す**数は変わらない(GROUNDED にはしない)が、顧客の報告では「違う」でなく「要確認」に出る。",
                  u"(試作で儀式の ±1 単位 11・10 倍 19、段 2 の単位の取り違え 1)",
                  u"(iii) の帯は末尾の 0 が多い数で広がる(無改変の偶然の「違う」1: S100YYK8 N041)。(ii)・(iii) は偶然の近さでも立つ(残る 6 のうち 3)。",
                  u"増減の数で、表示桁の fact の当期 − 前期と 1 単位違う正しい文(試作で 29 行)は「要確認」になる",
                  u"この封では直さない",
                  u"顧客の出力(verify_document)には provenance の欄が無い。",
                  u"日本語の報告形の封で決める。",
                  u"試作も実装も同じ 67 書類。新しい標本での率は未測定(EDINET から取るのは人間の決定)。"):
            self.assertIn(s, b, s)
        # 限界の数が §0 と同じ(儀式 11 + 19 = 30、段 2 の 1、残る 6 のうち 3、偶然の「違う」1)
        n = s0_numbers(s0(self.t))
        self.assertEqual((n["rit_pm1"], n["rit_x10"], n["s2_unv"], n["rest"], n["rest_chance"]), (11, 19, 1, 6, 3))

    def test_12_closed_file_list_and_order(self):
        b = sec(self.t, "## §4")
        first = b[:b.index(u"\n順序:")]
        pos = []
        for rel in ENGINE_FILES + (P25_UNIT_TEST,):
            tok = "`%s`" % rel
            self.assertEqual(first.count(tok), 1, rel)
            pos.append(first.index(tok))
        # 既存の test_recipes_p24.py は basename で「1 本足す」と書かれている(§1 の path と同じ file)
        tok = u"(+ `test_recipes_p24.py` に 1 本)"
        self.assertEqual(first.count(tok), 1)
        pos.append(first.index(tok))
        for rel in FILES:
            tok = "`%s`" % rel
            self.assertEqual(first.count(tok), 1, rel)
            pos.append(first.index(tok))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        self.assertEqual(len(ENGINE_FILES) + 1 + 1 + len(FILES), 9)
        self.assertLess(pos[2], pos[3])         # engine 3 file が試験より先
        # 登録の一覧の試験に P25 は engine の後・test_recipes_p25.py の前
        reg = first.index(u"→ 登録の一覧の試験に P25 →")
        self.assertTrue(pos[2] < reg < pos[3])
        self.assertIn(u"(L-1〜L-8)", first)
        self.assertIn(u"→ pin の遷移 → 覆い。", first)
        self.assertIn(u"段 2(人間に見せてから): `DEFAULT_PROFILE` + 既定の字の試験 + 儀式の走らせ直し + README + pin。", first)
        self.assertTrue(first.startswith(u"\n## §4 触る file と順序"))
        order = b[b.index(u"\n順序:"):]
        self.assertIn(u"人間の事前承認(2026-10-21)→ P24 段 1 の commit(c7ad668・92ae5e9)→ **この封 + 封の門を commit** → 段 1 実装(別席)→ 凍結 → "
                      u"独立監査 → commit → axis3 の宣言 → 日本語の報告形の封 → 段 2 を人間に。", order)
        # 実在する file は在る(既存の test_recipes_p24.py)。新規の 5 本は封の commit 時点で履歴に無い(test_15)
        self.assertTrue(os.path.exists(os.path.join(ROOT, P24_UNIT_TEST)))


class EngineAtSealTest(unittest.TestCase):
    """封の commit 時点の engine を字で留め、段 1 の後は「宣言された遷移」の値だけを受け入れる(docstring)。"""

    def test_13_engine_sha_is_the_one_at_the_seal_or_a_declared_transition(self):
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

    def test_14_new_flag_p25_and_no_same_value_exist_now_default_is_p22(self):
        """封が実装より先であることは、段 1 の実装の commit で「在る」に直した(2026-10-21。封の commit 時点は 旗 `last_branch_names_only_if_evidence`・
        profile `P25`・理由 `no_same_value` が engine にまだ無かった = 測った当時の事実)。いまは: 旗は Profile に在って既定は偽、真なのは P25 だけ、
        P25 は PROFILES に在って P24 + 旗 1 つ、既定は P22 のまま、`no_same_value` は registry_setup.py の POINTER_NOT_FOUND の理由に在り、`core/` には 1 字も無い。"""
        from adapters.xbrl import vocabulary as V
        fields = dict((f.name, f) for f in dataclasses.fields(V.Profile))
        flag = "last_branch_names_only_if_evidence"
        self.assertIn(flag, fields)
        self.assertIs(fields[flag].default, False)
        self.assertEqual(sorted(n for n, p in V.PROFILES.items() if getattr(p, flag)), ["P25", "P26", "P27", "P27E"])   # 2026-10-22: P26 = P25 + 旗 5 つ(封 XBRL_P26_SEAL_2026-10-21)も引き継ぐ。(2026-10-27: P27 = P26 + 旗 4 つ・P27E = P27 + 旗 1 つ。封 XBRL_P27_SEAL_2026-10-27)も引き継ぐ
        self.assertEqual(V.PROFILES["P25"], dataclasses.replace(V.P24, name="P25", last_branch_names_only_if_evidence=True))
        self.assertEqual(V.DEFAULT_PROFILE, "P27")      # 段 1 の commit 時点は P22。2026-10-23 の P26 の段 2(封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)で P26、2026-10-28 の P27 の段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で P27
        from adapters.xbrl import registry_setup as RS
        self.assertIn("no_same_value", RS._POINTER_NOT_FOUND_REASONS)
        self.assertNotIn("no_same_value", RS._UNVERIFIABLE_REASONS)
        for rel in ENGINE_FILES:
            t = text(os.path.join(ROOT, rel))
            lits = ("no_same_value",) if rel.endswith("registry_setup.py") else ("last_branch_names_only_if_evidence", "P25") if rel.endswith("vocabulary.py") \
                else ("last_branch_names_only_if_evidence", "no_same_value", "LAST_BRANCH_DIGIT_K")
            for lit in lits:
                self.assertIn(lit, t, u"%s に %s が無い" % (rel, lit))
        for p in glob.glob(os.path.join(ROOT, "core", "**", "*.py"), recursive=True):
            t = text(p)
            for lit in ("last_branch_names_only_if_evidence", "no_same_value"):
                self.assertNotIn(lit, t, u"core/ の %s に %s が在る(core/ は 0 行)" % (os.path.relpath(p, ROOT), lit))
        # 新規 file は作業木に在る(段 1 の実装)。履歴の順序は test_15
        for rel in AFTER:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), u"段 1 の file が無い: " + rel)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        shas = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split() if s]
        return shas[-1] if shas else None

    def test_15_the_seal_precedes_every_later_file(self):
        tracked = git("ls-files", "--error-unmatch", SEAL_REL).returncode == 0
        if not tracked:
            # 封が履歴に無い間に、後の file が履歴に現れていたら赤(順序の逆転)。何も無いことは pass と言わず skip で残す。
            for rel in AFTER:
                self.assertIsNone(self._added(rel), u"封より先に履歴に現れた: " + rel)
            self.skipTest(u"封がまだ commit されていない(後の file が履歴に無いことだけ確かめた)")
        seal = self._added(SEAL_REL)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(git("merge-base", "--is-ancestor", seal, other).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
