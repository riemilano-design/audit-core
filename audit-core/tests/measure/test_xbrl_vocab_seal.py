# -*- coding: utf-8 -*-
u"""語彙の登録と枠の取り直し(P24 = P23 + 旗 `vocab_2026_10_21` + 旗 `frame_rebind`)の封
docs/XBRL_VOCAB_SEAL_2026-10-21.md を固定する。
人間の承認の引用・予測 W-1〜W-9 と外れ方と幅の算術・§0 の数(字・記録 `rounding_2026-10-21.json` の P23 の値・手元の cache の書類の数)・
§1 の旗の形・触る枝の中の人間の決定(7 つ。engine の字に在ること)・過去の門の engine の留めの一覧・§3 の限界・
§4 の file 一覧と順序・封が実装より先であること(順序)・**封の commit 時点の engine 3 file の sha**を縛る。

**この門の engine の留め(test_12・test_13)は、段 1 の commit で「宣言された遷移」に更新する前提である**(P23 の封の門
tests/measure/test_xbrl_rounding_seal.py の test_11・test_12 と同じ型)。
この封は engine(adapters/xbrl/vocabulary.py・recipes.py・registry_setup.py)を変える封なので、段 1 で sha が動く。そのとき
`ENGINE_LATER` に (段 1 の後の sha16, この封の path) を 3 file 分足し、`test_13` の「旗 `vocab_2026_10_21`・`frame_rebind` は Profile に無い・
P24 は PROFILES に無い・理由 `other_frame` は engine に無い」を「旗は Profile に在り P24 だけが真・P24 は PROFILES に在り
DEFAULT_PROFILE は P22 のまま・`other_frame` は registry_setup.py に在る」に直す
(他の pin ― P23 までの封・結果の門の ENGINE_LATER 群(branch_a・role_swap・axis3・p20_result・a_core_vs_grep・pnf_diag・period_bind・rounding など)・
cd_seal の FROZEN_LATER・frozen_bundle の世代・axis3 の LATER_ENGINE_COMMITS ― も同じ便で宣言する。封 §1 の一覧)。
段 2(既定 P22 → P24)でもう一度、`DEFAULT_PROFILE` の assert を直す。

W-7(新しい標本)は cache の 67 の外 214 書類を使う測定で、この門は数えない(結果の門が持つ)。この門が cache について縛るのは
「67 と 281 と 214 が手元で数え直せること」だけで、cache が無い機械では skip(skip の理由を出す)。"""
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

SEAL_REL = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"    # 2026-10-21 追記: 最後の枝 P25 の段 1(下の ENGINE_LATER の遷移)
SEAL = os.path.join(ROOT, SEAL_REL)
ROUNDING_JSON = os.path.join(ROOT, "fixtures", "xbrl", "rounding_2026-10-21.json")
POINT_PRIOR_JSON = os.path.join(ROOT, "fixtures", "xbrl", "point_prior_2026-10-20.json")
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

# §4 の file 一覧(この順で書かれている)
ENGINE_FILES = ("adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py")
FILES = ("tests/adapters/xbrl/test_recipes_p24.py",
         "measure/xbrl_vocab_2026-10-21.py",
         "fixtures/xbrl/vocab_2026-10-21.json",
         "docs/XBRL_VOCAB_RESULT_2026-10-21.md",
         "tests/measure/test_xbrl_vocab_result.py")
# 封より後でなければ git 履歴に現れてはならない新規 file(§4 の 5 本そのもの)
AFTER = FILES

# 封の commit 時点の engine(sha256 の先頭 16 桁。P23 段 1 の 7d530cc の後の木)。**ここは宣言された遷移の前の値**で、消さない。
ENGINE_AT_SEAL = {"adapters/xbrl/vocabulary.py": "f7b8d925eb6787ec",
                  "adapters/xbrl/recipes.py": "d5308700eae78c10",
                  "adapters/xbrl/registry_setup.py": "b93e504f2fc7d642"}
# 宣言された遷移(段 1 の commit で足す): {path: (後の sha16, 遷移を宣言した封の path)}。封の commit 時点では空だった。
# 2026-10-21 追記(段 1 の実装): vocabulary.py は旗 2 つ・資金の句の表 CF_FUND_SUBJECTS_2026_10_21・P24・PROFILES の登録(+27 行・-1 行)、
# recipes.py は旗 vocab_2026_10_21・frame_rebind の塊(+224 行・-0 行。既存の行は 1 つも書き換えない)、registry_setup.py は理由 other_frame(+2 行)。
# comparators.py・core/ は 0 行。DEFAULT_PROFILE は P22 のまま。ENGINE_AT_SEAL は残す(封の commit 時点の値)。
# 2026-10-21(最後の枝 P25 の段 1): 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 last_branch_names_only_if_evidence・P25・PROFILES の登録(+7 行・-0 行)、recipes.py に最後の枝の証拠の判定の塊(+72 行・-0 行。既存の行は 1 つも書き換えない)、registry_setup.py に理由 no_same_value(+2 行)を足した(DEFAULT_PROFILE は P22 のまま)。
# vocabulary.py の 83498c04a7b70396・recipes.py の 3461c3f8b7af6675・registry_setup.py の 9a0b08954cf22639(P24 の段 1)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P25 の段 1 の後の値のときだけ。
ENGINE_LATER = {"adapters/xbrl/vocabulary.py": ("27e71e9861fc5aad", SEAL_LASTBRANCH),
                "adapters/xbrl/recipes.py": ("bff243f13429b553", SEAL_LASTBRANCH),
                "adapters/xbrl/registry_setup.py": ("f42ffe23aaa7673b", SEAL_LASTBRANCH)}

# §1「過去の門の engine の留め」の一覧(封の字)と、実物の在りか
PIN_FILES_ENGINE_LATER = ("tests/measure/test_xbrl_branch_a.py", "tests/measure/test_xbrl_role_swap_result.py",
                          "tests/measure/test_xbrl_axis3_decision.py", "tests/measure/test_xbrl_p20_result.py",
                          "tests/measure/test_xbrl_a_core_vs_grep_seal.py", "tests/measure/test_xbrl_pnf_diag.py")
OTHER_PINS = {"tests/measure/test_xbrl_axis3_decision.py": "LATER_ENGINE_COMMITS",
              "tests/measure/test_xbrl_cd_seal.py": "FROZEN_LATER",
              "fixtures/frozen_bundle_sha.py": "FROZEN_BUNDLE_GENERATIONS"}
PIN_GATES = ("tests/measure/test_xbrl_point_prior_result.py", "tests/measure/test_xbrl_ritual_result.py",
             "tests/measure/test_xbrl_period_bind_seal.py", "tests/measure/test_xbrl_period_bind_result.py",
             "tests/measure/test_xbrl_rounding_seal.py", "tests/measure/test_xbrl_rounding_result.py")

# 封が名指す人間の決定が commit に在る(封 §1)
DECISION_COMMITS = ("5eb80a2", "3320c8c", "7d530cc", "8fc113f")


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
    m_p23 = one(r"67 書類 ([\d,]+) claim を P23 で: GROUNDED ([\d,]+)、VALUE_MISMATCH ([\d,]+)、UNVERIFIABLE ([\d,]+)、POINTER_NOT_FOUND ([\d,]+)", b, "P23 の 4 state")
    m_v2 = one(r"新 GROUNDED (\d+) のうち偽 (\d+)・準偽 (\d+) を出した", b, "試作 v2")
    m_v3 = one(r"試作 v3 は偽 (\d+)\(.*?注入 (\d+) 回で GROUNDED (\d+)", b, "試作 v3")
    m_ng = one(r"新 GROUNDED (\d+)\(資金の主語の句 (\d+)・手がかり語とポイント (\d+)・CF 合計の符号 (\d+)\)を全部人が読み\*\*偽 (\d+)\*\*", b, "新 GROUNDED の内訳")
    m_gg = one(r"G → 非 G (\d+)、G → G (\d+)", b, "G → 非 G と G → G")
    m_vm = one(r"VALUE_MISMATCH ([\d,]+) → ([\d,]+)\(−(\d+) = 枠 −(\d+)・語彙 −(\d+)\)", b, "VM の増減")
    m_fr = one(r"枠の VM → UNVERIFIABLE (\d+)\(other_frame (\d+)・ambiguous\(member\) (\d+)\)を全部読み、正しい文 (\d+)・文が本当に違う (\d+)・分からない (\d+)", b, "枠の読み")
    m_nvm = one(r"新しい VALUE_MISMATCH (\d+)", b, "新しい VM")
    m_hb = one(r"穴 B 通した (\d+) / (\d+)", b, "穴 B")
    m_rt = one(r"儀式 通した (\d+) / (\d+)・止めた (\d+) / (\d+)\(素の書類の GROUNDED (\d+) → (\d+) で注入の対象が (\d+) → (\d+)\)", b, "儀式")
    m_in = one(r"動いた (\d+) 行への注入 (\d+) 回.*?P24 の GROUNDED (\d+)・UNVERIFIABLE (\d+)\(P23 は同じ (\d+) 回で GROUNDED (\d+)\)", b, "注入")
    m_rd = one(r"既存試験の赤 (\d+)\(登録の一覧 (\d+)・test_mutations (\d+)・sha の留め (\d+)・diff の門 (\d+)", b, "既存試験の赤")
    m_df = one(r"engine recipes \+(\d+)/−(\d+)・vocabulary \+(\d+)/−(\d+)・registry_setup \+(\d+)/−(\d+)", b, "engine の行数")
    m_ca = one(r"は 281 書類、うち 67 の外が 214", b, "cache")
    return {"claims": num(m_p23.group(1)), "g": num(m_p23.group(2)), "vm": num(m_p23.group(3)),
            "unv": num(m_p23.group(4)), "pnf": num(m_p23.group(5)),
            "v2_new_g": int(m_v2.group(1)), "v2_false": int(m_v2.group(2)), "v2_semi": int(m_v2.group(3)),
            "v3_false": int(m_v3.group(1)), "v3_inj": int(m_v3.group(2)), "v3_inj_g": int(m_v3.group(3)),
            "new_g": int(m_ng.group(1)), "new_g_fund": int(m_ng.group(2)), "new_g_cue": int(m_ng.group(3)),
            "new_g_cf": int(m_ng.group(4)), "new_g_false": int(m_ng.group(5)),
            "g_to_nong": int(m_gg.group(1)), "g_to_g": int(m_gg.group(2)),
            "vm_before": num(m_vm.group(1)), "vm_after": num(m_vm.group(2)), "vm_delta": int(m_vm.group(3)),
            "vm_frame": int(m_vm.group(4)), "vm_vocab": int(m_vm.group(5)),
            "frame": int(m_fr.group(1)), "other_frame": int(m_fr.group(2)), "ambig_member": int(m_fr.group(3)),
            "frame_right": int(m_fr.group(4)), "frame_wrong": int(m_fr.group(5)), "frame_unknown": int(m_fr.group(6)),
            "new_vm": int(m_nvm.group(1)),
            "hole_b_pass": int(m_hb.group(1)), "hole_b_den": int(m_hb.group(2)),
            "rit_pass": int(m_rt.group(1)), "rit_den": int(m_rt.group(2)), "rit_stop": int(m_rt.group(3)), "rit_den2": int(m_rt.group(4)),
            "rit_g_before": int(m_rt.group(5)), "rit_g_after": int(m_rt.group(6)),
            "rit_target_before": int(m_rt.group(7)), "rit_target_after": int(m_rt.group(8)),
            "moved": int(m_in.group(1)), "inj": int(m_in.group(2)), "inj_p24_g": int(m_in.group(3)), "inj_p24_unv": int(m_in.group(4)),
            "inj_p23_n": int(m_in.group(5)), "inj_p23_g": int(m_in.group(6)),
            "red": int(m_rd.group(1)), "red_list": int(m_rd.group(2)), "red_mut": int(m_rd.group(3)),
            "red_sha": int(m_rd.group(4)), "red_diff": int(m_rd.group(5)),
            "rec_ins": int(m_df.group(1)), "rec_del": int(m_df.group(2)), "voc_ins": int(m_df.group(3)),
            "voc_del": int(m_df.group(4)), "reg_ins": int(m_df.group(5)), "reg_del": int(m_df.group(6)),
            "cache_all": 281, "cache_outside": 214, "docs": 67}


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
        self.assertIn(u"**この封は engine(`adapters/xbrl/vocabulary.py`・`recipes.py`・`registry_setup.py`)を変える。人間の承認(2026-10-21 深夜)", head)
        self.assertIn(u"司令塔が朝に諮ると言った 3 点(語彙の封・丸めの帯・日本語の報告形)に対し、", head)
        self.assertIn(u"人間「engine に触るので承認が要る → 先に承認しておくので好きに進めて これをもって承認とする」", head)
        self.assertIn(u"作法は変えない(封 → 実装 → 凍結 → 独立監査 GO → commit)。", head)
        self.assertIn(u"数を見てから封・予測を直さない。外れは外れとして残す。P23 段 1(7d530cc、宣言 8fc113f)の後に置く。**", head)
        self.assertTrue(head.startswith(u"# 封: 語彙の登録で「結べない」を減らし、枠の取り直しで「違う」を「要確認」に弱める(engine の直し P24 = P23 + 旗 2 つ)― 2026-10-21"))

    def test_2_nine_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §2", "## §3")
        ids, lines = predictions(b, "W")
        self.assertEqual(ids, [str(i) for i in range(1, 10)])
        self.assertEqual(len(lines), 9)
        for line in lines:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[1], u"予測が空: " + line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        by = dict((i, l) for i, l in zip(ids, lines))
        # 行ごとに、予測の幅と外れ方の両方を字で縛る(幅を直すと赤くなる)
        for i, ss in (("1", (u"67 書類の無改変で新しく GROUNDED になる行 **140〜156**", u"向きは全部 非 GROUNDED → GROUNDED",
                             u"枠の取り直しが作る GROUNDED **0**", u"幅の外 / 枠の GROUNDED 1 以上")),
                      ("2", (u"GROUNDED → 非 GROUNDED **0〜1**", u"G → G(参照先が動いた)**0〜6**", u"2 以上 / 7 以上")),
                      ("3", (u"VALUE_MISMATCH は **1,195〜1,211**(P23 1,418)", u"VM → UNVERIFIABLE(other_frame・ambiguous(member))**200〜215**",
                             u"幅の外")),
                      ("4", (u"穴 B の 485 件を P24 で通す **0**", u"止めた行の state は P23 と全行同じ", u"1 以上 / 1 行でも違う")),
                      ("5", (u"儀式を P24 で: 通した **2〜3**", u"VM → UNVERIFIABLE に移る **0〜1**",
                             u"対象の数は予測しない", u"幅の外")),
                      ("6", (u"GROUNDED か UNVERIFIABLE へ動いた行(G → G を含む。試作で 361 = 148 + 4 + 209。非 G → 非 G の 8 は含めない)への注入", u"末尾の桁 ±3・10 倍・向きの語の反転", u"P24 が GROUNDED にする **0** 回",
                             u"止まらず UNVERIFIABLE **0〜3** 回", u"GROUNDED 1 回以上 / UNV 4 以上")),
                      ("7", (u"手元の cache の 67 の外 214 書類のうち、67 と同じ抽出で claim が 1 以上の書類", u"偽(間違った fact に結んだ)が新 GROUNDED の 3% 以下",
                             u"「文が本当に違う」が **10% 以下**", u"claim が 1 以上の書類が 10 未満なら「測れない」と記録する(当たりにも外れにもしない)",
                             u"偽が 3% 超 / 違うが 10% 超")),
                      ("8", (u"`recipes.py` **+200〜+250 / −0**", u"`vocabulary.py` **≤ 35 行**", u"`registry_setup.py` **≤ 5 行**",
                             u"`comparators.py`・`core/` 0 行", u"既存試験の赤は登録の一覧・旗の形・sha の留め・diff の門だけ",
                             u"(数 / state の門 0、人間の決定の字の門 0)", u"超える / `recipes.py` の削除 1 行以上 / 種類の外の赤")),
                      ("9", (u"段 2(既定 P22 → P24、P23 と P25 を含めてまとめて)は人間に 3 つの率(通す率・無改変で「違う」と言う率・結べない率)を見せてから",))):
            for s in ss:
                self.assertIn(s, by[i], u"W-%s: %s" % (i, s))
        self.assertIn(u"**W-1〜W-6 は試作の再現で、外れるなら実装が試作と違うことを示す。本当に外れうるのは W-7(新しい標本)である。**", b)
        self.assertIn(u"W-7 の分母と読みは結果文書に 1 行ずつ残す。", b)

    def test_3_prediction_arithmetic_is_consistent(self):
        """予測の幅が §0 の試作の数を含む(幅どうし・幅と試作の整合)。片方だけ直すと赤くなる。"""
        n = s0_numbers(s0(self.t))
        b = sec(self.t, "## §2", "## §3")
        _, lines = predictions(b, "W")
        # W-1: 新 GROUNDED 148 は幅の中。148 = 117 + 13 + 18
        lo, hi = rng(lines[0], r"新しく GROUNDED になる行 \*\*(\d+)〜(\d+)\*\*")
        self.assertLessEqual(lo, hi)
        self.assertTrue(lo <= n["new_g"] <= hi, (lo, n["new_g"], hi))
        self.assertEqual(n["new_g_fund"] + n["new_g_cue"] + n["new_g_cf"], n["new_g"])
        # W-2: G → 非 G は 0〜1(試作 0)、G → G は 0〜6(試作 4)
        lo, hi = rng(lines[1], r"GROUNDED → 非 GROUNDED \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["g_to_nong"] <= hi)
        lo2, hi2 = rng(lines[1], r"参照先が動いた\)\*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo2 <= n["g_to_g"] <= hi2)
        # W-3: VM の幅は 1,418 − 215 = 1,203 を含み、VM → UNV の幅は 209 を含む。1,418 − 1,203 = 215 = 209 + 6(§0)
        lo, hi = rng(lines[2], r"VALUE_MISMATCH は \*\*([\d,]+)〜([\d,]+)\*\*")
        self.assertLessEqual(lo, hi)
        self.assertEqual(n["vm_before"] - n["vm_delta"], n["vm_after"])
        self.assertTrue(lo <= n["vm_after"] <= hi, (lo, n["vm_after"], hi))
        # 幅の差が §0 の −215 を含む: P23 1,418 との差が [418 - hi, 1418 - lo] に 215 が入る
        self.assertTrue(n["vm_before"] - hi <= n["vm_delta"] <= n["vm_before"] - lo, (n["vm_before"] - hi, n["vm_delta"], n["vm_before"] - lo))
        self.assertEqual(n["vm_before"], 1418)
        lo, hi = rng(lines[2], r"\(other_frame・ambiguous\(member\)\)\*\*(\d+)〜(\d+)\*\*")
        self.assertLessEqual(lo, hi)
        self.assertTrue(lo <= n["frame"] <= hi, (lo, n["frame"], hi))
        self.assertEqual(n["vm_frame"] + n["vm_vocab"], n["vm_delta"])
        self.assertEqual(n["vm_frame"], n["frame"])
        # W-5: 儀式の通した 2〜3 は試作の 2 を含み、VM → UNV の移りは 0〜1
        lo, hi = rng(lines[4], r"通した \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["rit_pass"] <= hi)
        # W-6: 注入の UNV は 0〜3(試作 1)、GROUNDED は 0 回(試作 0)
        lo, hi = rng(lines[5], r"UNVERIFIABLE \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["inj_p24_unv"] <= hi)
        self.assertEqual(n["inj_p24_g"], 0)
        # W-8: engine の行数の試作は幅の中(recipes +224 は +200〜+250、vocabulary +27 は ≤ 35、registry_setup +2 は ≤ 5)
        lo, hi = rng(lines[7], r"`recipes.py` \*\*\+(\d+)〜\+(\d+) / −0\*\*")
        self.assertLessEqual(lo, hi)
        self.assertTrue(lo <= n["rec_ins"] <= hi)
        self.assertEqual(n["rec_del"], 0)
        self.assertLessEqual(n["voc_ins"], num(re.search(r"`vocabulary.py` \*\*≤ (\d+) 行\*\*", lines[7]).group(1)))
        self.assertLessEqual(n["reg_ins"], num(re.search(r"`registry_setup.py` \*\*≤ (\d+) 行\*\*", lines[7]).group(1)))

    def test_4_section_0_numbers_are_pinned_as_written(self):
        b = s0(self.t)
        n = s0_numbers(b)
        # P23 の 4 state(7,799 claim)
        self.assertEqual((n["claims"], n["g"], n["vm"], n["unv"], n["pnf"]), (7799, 4234, 1418, 1323, 824))
        self.assertEqual(n["g"] + n["vm"] + n["unv"] + n["pnf"], n["claims"])
        # 試作 v2 / v3(封に至る経緯。偽が出て設計を変えた)
        self.assertEqual((n["v2_new_g"], n["v2_false"], n["v2_semi"]), (345, 16, 11))
        self.assertEqual((n["v3_false"], n["v3_inj"], n["v3_inj_g"]), (5, 705, 1))
        # 試作 v3.1: 新 GROUNDED 148 = 117 + 13 + 18、偽 0、G → 非 G 0、G → G 4
        self.assertEqual((n["new_g"], n["new_g_fund"], n["new_g_cue"], n["new_g_cf"], n["new_g_false"]), (148, 117, 13, 18, 0))
        self.assertEqual((n["g_to_nong"], n["g_to_g"]), (0, 4))
        # VM 1,418 → 1,203 = −215 = 枠 −209 + 語彙 −6
        self.assertEqual((n["vm_before"], n["vm_after"], n["vm_delta"], n["vm_frame"], n["vm_vocab"]), (1418, 1203, 215, 209, 6))
        self.assertEqual(n["vm_frame"] + n["vm_vocab"], n["vm_delta"])
        # 枠の VM → UNV 209 = other_frame 198 + ambiguous(member) 11 = 正しい文 207 + 違う 1 + 分からない 1
        self.assertEqual((n["frame"], n["other_frame"], n["ambig_member"]), (209, 198, 11))
        self.assertEqual(n["other_frame"] + n["ambig_member"], n["frame"])
        self.assertEqual((n["frame_right"], n["frame_wrong"], n["frame_unknown"]), (207, 1, 1))
        self.assertEqual(n["frame_right"] + n["frame_wrong"] + n["frame_unknown"], n["frame"])
        self.assertEqual(n["new_vm"], 6)
        # 動いた(注入の対象)361 = 新 GROUNDED 148 + G → G 4 + 枠 209。注入 695 回、P24 は GROUNDED 0・UNV 1、P23 は GROUNDED 2
        self.assertEqual((n["moved"], n["inj"], n["inj_p24_g"], n["inj_p24_unv"], n["inj_p23_n"], n["inj_p23_g"]), (361, 695, 0, 1, 695, 2))
        self.assertEqual(n["new_g"] + n["g_to_g"] + n["frame"], n["moved"])
        self.assertEqual(n["inj_p23_n"], n["inj"])
        # 穴 B 0 / 485、儀式 2 / 247 と 245 / 247(素の書類の GROUNDED 329 → 340、注入の対象 240 → 247)
        self.assertEqual((n["hole_b_pass"], n["hole_b_den"]), (0, 485))
        self.assertEqual((n["rit_pass"], n["rit_den"], n["rit_stop"], n["rit_den2"]), (2, 247, 245, 247))
        self.assertEqual(n["rit_pass"] + n["rit_stop"], n["rit_den"])
        self.assertEqual((n["rit_g_before"], n["rit_g_after"], n["rit_target_before"], n["rit_target_after"]), (329, 340, 240, 247))
        # 既存試験の赤 33 = 13 + 1 + 14 + 5(数 / state の門 0、人間の決定の字の門 0)
        self.assertEqual((n["red"], n["red_list"], n["red_mut"], n["red_sha"], n["red_diff"]), (33, 13, 1, 14, 5))
        self.assertEqual(n["red_list"] + n["red_mut"] + n["red_sha"] + n["red_diff"], n["red"])
        self.assertIn(u"数 / state の門 0、人間の決定の字の門 0", b)
        # engine の行数(試作)
        self.assertEqual((n["rec_ins"], n["rec_del"], n["voc_ins"], n["voc_del"], n["reg_ins"], n["reg_del"]), (224, 0, 27, 1, 2, 0))
        for s in (u"**試作 v2(枠の取り直しで GROUNDED を作る形)は新 GROUNDED 345 のうち偽 16・準偽 11 を出した。**",
                  u"**値が合う枠がちょうど 1 つでも同定ではない** → 枠の取り直しは GROUNDED を作らない設計に変えた。",
                  u"(ホ) 資金の句の括弧「(前年同期は…の減少)」を前期 − 前々期の差の符号で照合する(12。P22 でも既存 6 句で同じ枝を 6 行が通る)",
                  u"CF 合計の文字の主張を、前期の手がかりが無いとき当期の値の符号で照合した枝",
                  u"**試作は全部同じ 67 書類で測った。** 規則は 67 書類を読んで作ったので、67 書類での偽 0 は新しい標本での偽 0 を意味しない",
                  u"司令塔の席の手元の報告 `scratchpad/vocab/proto_report.md`・`scratchpad/vocab3/proto3_report.md`)",
                  u"正本でない",
                  u"text と claim の有無は未測定"):
            self.assertIn(s, b, s)

    def test_5_section_0_p23_numbers_match_the_records(self):
        """§0 の「P23 で」の数は、P23 段 1 の記録 fixtures/xbrl/rounding_2026-10-21.json と同じ。"""
        n = s0_numbers(s0(self.t))
        r = jload(ROUNDING_JSON)
        agg = r["R2"]["集計"]
        self.assertEqual(r["R2"]["総 claim"], n["claims"])
        self.assertEqual(agg["書類数"], n["docs"])
        self.assertEqual(r["書類の数"]["経営分析の文を持つ"], n["docs"])
        self.assertEqual(agg["GROUNDED の合計 P23"], n["g"])
        self.assertEqual(agg["VALUE_MISMATCH の合計 P23"], n["vm"])
        # UNVERIFIABLE・POINTER_NOT_FOUND は書類別の states を足して数える(記録に合計の欄が無い)
        tot = {}
        for d in r["R2"]["書類"]:
            for k, v in d["states P23"].items():
                tot[k] = tot.get(k, 0) + v
        self.assertEqual(tot, {"GROUNDED": n["g"], "VALUE_MISMATCH": n["vm"], "UNVERIFIABLE": n["unv"], "POINTER_NOT_FOUND": n["pnf"]})
        self.assertEqual(sum(tot.values()), n["claims"])
        self.assertEqual(len(r["R2"]["書類"]), n["docs"])
        # 儀式 P23 の素の書類 GROUNDED 329(注入の対象 240)と穴 B 0 / 485 の P23 側(対照)
        self.assertEqual(r["R1"]["素の書類 P23"]["state の分布"]["GROUNDED"], n["rit_g_before"])
        self.assertEqual(r["R1"]["注入の対象 P23"], n["rit_target_before"])
        self.assertEqual((r["R3"]["集計"]["P23 で通した(GROUNDED のまま)"]["件"], r["R3"]["集計"]["P23 で通した(GROUNDED のまま)"]["分母"]),
                         (n["hole_b_pass"], n["hole_b_den"]))
        self.assertEqual((r["R1"]["通した P23"]["件"], r["R1"]["通した P23"]["分母"]), (2, 240))
        # P23 の記録の環境: 既定は P22 のまま・P23 の engine の sha16 は封の留めと同じ
        self.assertEqual(r["環境"]["DEFAULT_PROFILE"], "P22")
        self.assertEqual(r["環境"]["vocabulary.py の sha16"], ENGINE_AT_SEAL["adapters/xbrl/vocabulary.py"])
        self.assertEqual(r["環境"]["recipes.py の sha16"], ENGINE_AT_SEAL["adapters/xbrl/recipes.py"])

    def test_6_cache_counts_67_281_214(self):
        """§0「手元の cache は 281 書類、うち 67 の外が 214」を手元の cache を数えて確かめる。cache が無い機械では skip(理由を出す)。"""
        n = s0_numbers(s0(self.t))
        if not os.path.isdir(CACHE_DIR):
            self.skipTest(u"cache(%s)が無い機械では 281・214 を数えられない(封の字と記録は他の門が縛る)" % CACHE_DIR)
        zips = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(CACHE_DIR, "*.zip")))
        ids = sorted(x["docID"] for x in jload(POINT_PRIOR_JSON)["書類"] if x["区分"] == u"文あり")
        self.assertEqual(len(ids), n["docs"])
        self.assertTrue(set(ids) <= set(zips), u"67 書類が cache に揃っていない: " + str(sorted(set(ids) - set(zips))))
        self.assertEqual(len(zips), n["cache_all"])
        self.assertEqual(len(set(zips) - set(ids)), n["cache_outside"])
        self.assertEqual(n["cache_all"] - n["docs"], n["cache_outside"])

    def test_7_section_1_flag_shapes_and_rules(self):
        b = sec(self.t, "## §1", "## §2")
        for s in (u"`Profile` に `vocab_2026_10_21: bool = False`・`frame_rebind: bool = False`",
                  u"`P24 = dataclasses.replace(P23, name=\"P24\", vocab_2026_10_21=True, frame_rebind=True)`、`PROFILES` に登録",
                  u"**段 1 では既定にしない(DEFAULT_PROFILE = \"P22\" のまま)。** 旗が偽なら 1 行も変わらない。",
                  u"recipes.py の既存の行は 1 行も書き換えない",
                  # 旗 vocab_2026_10_21 の 4 規則
                  u"「前連結会計年度末残高」「前年は」「(前期␣」",
                  u"新しい関数が持ち、`def _prior_cue_clause(s, pos):` とその本体は字を変えない。",
                  u"**「前連結会計年度に」「前期同期」は足さない**",
                  u"period_bind の `if` 行の字は変えず、後ろに足す",
                  u"「(同」「前事業年度」「前事業年度末」",
                  u"**C-1g §1-3 の `_build_point_diff_claim` は字を変えず**(def 行・窓の `if` 行・呼び出しの行)",
                  u"既存の語で reason が `no_element(point without prior phrase)` になった数だけ、本体を写した新しい関数で組み直す",
                  u"資金の主語の句 19 通り(67 書類で件数 2 以上)",
                  u"**この 19 句の主語の数は当期と Prior1Year の fact にだけ値で結ぶ(Prior2Year 以前に結ばない)。** 既存 6 句は変えない。",
                  u"`NetCashProvidedByUsedIn(Operating|Investing|Investment|Financing)Activities`",
                  u"**前期の手がかり(既存の括弧の「前連結会計年度は」・節の手がかり・(1) の語)があるときだけ**",
                  u"Prior1Year の値そのものの符号で照合する(正 = 増加・獲得、負 = 減少・使用・支出)。前期・前々期の対には落とさない。",
                  u"**手がかりが無ければ P23 のまま。**",
                  # 旗 frame_rebind
                  u"主語の要素が取れ、取った枠で値が合わず、前期の手がかりが無い数。同じ要素の別の枠(素か member 1 つ、当期)で (i) 直接の値 (ii) 当期・前期の率 (iii) 当期 − 前期 が合うとき。",
                  u"VALUE_MISMATCH をやめて UNVERIFIABLE。合う枠が 1 つなら理由 `other_frame`(登録簿の固定の名前。`registry_setup.py` に登録。",
                  u"2 つ以上なら `ambiguous(member)`。**pointer を付けず、GROUNDED にしない。** 別の要素・前期の枠には広げない。"):
            self.assertIn(s, b, s)
        # P24 は P23 に 2 旗を足したもの。P23 の旗は変えない・既定は P22 のまま
        p24 = re.search(r"`P24 = dataclasses\.replace\([^`]*\)`", b).group(0)
        self.assertIn("P23", p24)
        self.assertIn("vocab_2026_10_21=True", p24)
        self.assertIn("frame_rebind=True", p24)
        self.assertNotIn("truncate_on_magnitude", p24)

    def test_8_the_seven_decisions_in_the_touched_branch_are_listed(self):
        b = sec(self.t, "## §1", "## §2")
        line = [l for l in b.splitlines() if l.startswith(u"- **触る枝の中の人間の決定")][0]
        names = (u"2026-10-08 案ア(no_subject)", u"§1b の止め", u"C2 `period_cue`", u"C-1g §1-3 `_build_point_diff_claim`",
                 u"P21 の最後の枝(5eb80a2)", u"P22 の `period_bind`(3320c8c、`subj and`)", u"P23 の `_mag_trunc`(7d530cc)")
        for s in names:
            self.assertIn(s, line, s)
        positions = [line.index(s) for s in names]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(names), 7)
        for s in (u"字も振る舞いも 1 つも壊さない", u"period_bind_seal test_8・rounding_seal test_7 ほか", u"**直さずに緑**",
                  u"P16/P20/P21/P22/P23 を明示した試験の数は 1 つも変えない"):
            self.assertIn(s, line, s)

    def test_9_the_decisions_exist_in_the_engine_now(self):
        """封が名指した人間の決定が、いまの engine の字に在る(封が実物と食い違っていない)。段 1 の後も 1 つも壊さない約束なので、この assert は段 1 の後も残す。"""
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
        # `_prior_cue_clause` は def 行がこの字(封 §1 (1))
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
        # 決定の commit が履歴に在る(浅い clone では skip せず、在るかだけ見る)
        for c in DECISION_COMMITS:
            self.assertEqual(git("cat-file", "-e", c + "^{commit}").returncode, 0, u"封が名指す commit %s が無い" % c)

    def test_10_engine_pins_list_is_written_and_exists(self):
        b = sec(self.t, "## §1", "## §2")
        line = [l for l in b.splitlines() if l.startswith(u"- **過去の門の engine の留め**")][0]
        for s in (u"ENGINE_LATER 6 本(branch_a・role_swap・axis3・p20_result・a_core_vs_grep・pnf_diag)", u"cd_seal FROZEN_LATER",
                  u"point_prior_result・ritual_result・period_bind(seal/result)・rounding(seal/result)", u"frozen_bundle の世代",
                  u"axis3 LATER_ENGINE_COMMITS(次の便)", u"registry_setup.py の sha を留める門があれば同じ型で宣言する"):
            self.assertIn(s, line, s)
        defining = set()
        for p in glob.glob(os.path.join(ROOT, "tests", "measure", "*.py")):
            if re.search(r"(?m)^ENGINE_LATER = \{", text(p)):
                defining.add("tests/measure/" + os.path.basename(p))
        self.assertTrue(set(PIN_FILES_ENGINE_LATER) <= defining, sorted(set(PIN_FILES_ENGINE_LATER) - defining))
        self.assertEqual(len(PIN_FILES_ENGINE_LATER), 6)
        for rel, name in sorted(OTHER_PINS.items()):
            self.assertTrue(re.search(r"(?m)^%s\b" % name, text(os.path.join(ROOT, rel))), rel + " の " + name)
        for rel in PIN_GATES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_11_limits_are_written(self):
        b = sec(self.t, "## §3", "## §4")
        for s in (u"枠の取り直しは、別の枠の率が帯の中で合うとき、注入した誤りを UNVERIFIABLE にする(試作で 695 回中 1 回、S100YWGX N020)。",
                  u"「違う」を「要確認」に弱める代価がある(67 書類で 209 行中 2)。",
                  u"「前期同期」(誤字)の文は VALUE_MISMATCH のまま。",
                  u"増減の数・支出の減少率を当期の値や符号つきの率と照合する型の正しい文は VALUE_MISMATCH(試作で新しい VM 6)。",
                  u"手がかりの無い CF 合計の文字の主張は P23 のまま(前期・前々期の対の符号で、偶然に合う行がある。試作で S100Z6XO の 3 行)。",
                  u"登録する語は 67 書類の字。別の提出者の言い回しは W-7 で一部だけ見る。",
                  u"段 2 の材料(192 行)にはこの規則の形の文が無い(試作で動いた行 0)= 段 2 の材料ではこの直しの安全を測れない。安全は W-6 と W-7 で見る。",
                  u"最後の枝の名指し(696)・率の再計算で対が無い・増減で対が無い・向きの語は、この封では直らない(P25 の封)。",
                  u"単位 145(店舗・社・台・株・倍・件)は fact が無いので登録しない。"):
            self.assertIn(s, b, s)
        # 限界の「209 行中 2」は §0 の枠の読み(違う 1 + 分からない 1 = 2 / 209)
        n = s0_numbers(s0(self.t))
        self.assertEqual(n["frame_wrong"] + n["frame_unknown"], 2)
        self.assertEqual(n["frame"], 209)

    def test_12_closed_file_list_and_order(self):
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
        self.assertIn(u"→ 登録の一覧の試験に P24 →", first)
        self.assertIn(u"(W-1〜W-8)", first)
        self.assertIn(u"→ pin の遷移 → 覆い。", first)
        self.assertIn(u"段 2(人間に見せてから): `DEFAULT_PROFILE` + 既定の字の試験 + 儀式の走らせ直し + README + pin。", first)
        order = b[b.index(u"\n順序:"):]
        self.assertIn(u"人間の事前承認(2026-10-21)→ P23 段 1 の commit(7d530cc・8fc113f)→ **この封 + 封の門を commit** → 段 1 実装(別席)→ 凍結 → "
                      u"独立監査 → commit → axis3 の宣言 → P25 の封 → 段 2 を人間に。", order)


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

    def test_14_new_flags_p24_and_other_frame_exist_now_default_is_p22(self):
        """封が実装より先であることは、段 1 の実装の commit で「在る」に直した(2026-10-21。封の commit 時点は 旗 `vocab_2026_10_21`・`frame_rebind`・
        profile `P24`・理由 `other_frame` が engine にまだ無かった = 測った当時の事実)。いまは: 旗は Profile に在って既定は偽、真なのは P24 だけ、
        P24 は PROFILES に在って P23 + 旗 2 つ、既定は P22 のまま、`other_frame` は registry_setup.py の登録に在り、`core/` には 1 字も無い。"""
        from adapters.xbrl import vocabulary as V
        fields = dict((f.name, f) for f in dataclasses.fields(V.Profile))
        self.assertIn("P23", V.PROFILES)
        self.assertEqual(V.PROFILES["P23"], dataclasses.replace(V.P22, name="P23", pct_tolerance_from_decimals=True, truncate_abs_band=True))
        self.assertEqual(V.DEFAULT_PROFILE, "P22")
        for flag in ("vocab_2026_10_21", "frame_rebind"):
            self.assertIn(flag, fields)
            self.assertIs(fields[flag].default, False)
            # 2026-10-21: P25 = P24 + 旗 1 つ(封 XBRL_LASTBRANCH_SEAL_2026-10-21)は P24 の旗 2 つを引き継ぐ
            self.assertEqual(sorted(n for n, p in V.PROFILES.items() if getattr(p, flag)), ["P24", "P25"], flag)
        self.assertIn("P24", V.PROFILES)
        self.assertEqual(V.PROFILES["P24"], dataclasses.replace(V.P23, name="P24", vocab_2026_10_21=True, frame_rebind=True))
        # 登録簿: other_frame は新しい名前で registry_setup.py にだけ在る(engine の 3 file の外と core/ には無い)
        from adapters.xbrl import registry_setup as RS
        self.assertIn("other_frame", RS._UNVERIFIABLE_REASONS)
        self.assertIn("ambiguous(member)", RS._UNVERIFIABLE_REASONS)
        for p in glob.glob(os.path.join(ROOT, "core", "**", "*.py"), recursive=True):
            t = text(p)
            for lit in ("other_frame", "frame_rebind", "vocab_2026_10_21"):
                self.assertNotIn(lit, t, u"core/ の %s に %s が在る(core/ は 0 行)" % (os.path.relpath(p, ROOT), lit))
        for rel in ENGINE_FILES:
            t = text(os.path.join(ROOT, rel))
            if rel.endswith("registry_setup.py"):
                self.assertIn("other_frame", t)
            else:
                self.assertIn("vocab_2026_10_21", t)

    def test_15_p23_flags_are_unchanged(self):
        """P24 は P23 に積むので、P23 の旗は封の commit 時点のまま(P23 = P22 + 率の帯 + 切り捨ての帯。P19 の旗は積まない)。"""
        from adapters.xbrl import vocabulary as V
        p23 = V.PROFILES["P23"]
        self.assertTrue(p23.pct_tolerance_from_decimals)
        self.assertTrue(p23.truncate_abs_band)
        self.assertFalse(p23.truncate_on_magnitude)
        # 2026-10-21: P24 = P23 + 旗 2 つ(段 1 の実装)は truncate_abs_band を引き継ぐ
        # 2026-10-21: P25 = P24 + 旗 1 つ(封 XBRL_LASTBRANCH_SEAL_2026-10-21)も引き継ぐ
        self.assertEqual(sorted(n for n, p in V.PROFILES.items() if p.truncate_abs_band), ["P23", "P24", "P25"])


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        shas = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split() if s]
        return shas[-1] if shas else None

    def test_16_the_seal_precedes_every_later_file(self):
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
