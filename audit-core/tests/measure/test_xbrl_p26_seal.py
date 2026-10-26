# -*- coding: utf-8 -*-
u"""「違う」に出る正しい文の主因を減らす(engine の直し P26 = P25 + 旗 5 つ)の封の門
docs/XBRL_P26_SEAL_2026-10-21.md を固定する。型は P25 の封の門 tests/measure/test_xbrl_lastbranch_seal.py と
報告形の直しの封の門 tests/measure/test_xbrl_customer_report_fix_seal.py に倣う。
人間の方針の引用・段 1 では既定にしない字・予測 Q-1〜Q-8 と外れ方と幅の算術・§0 の数(P25 の 4 state と穴 B・儀式・段 2 の分母は記録
`fixtures/xbrl/lastbranch_2026-10-21.json` と突き合わせ、試作の数は字のまま留めて内訳の和を縛る)・§1 の旗 5 つ・理由 3 つ・報告形の 3 行・
「GROUNDED にはしない」の字・触る枝の中の人間の決定(9 つ。engine の字に在ること)・§3 の限界・§4 の file 一覧と順序・
**封が実装より先であること(P26 が PROFILES に無い・理由 3 つが登録簿に無い・report_customer.py に 3 行が無い・新しい file が無い)**・
**封の commit 時点の adapters/xbrl 16 file(P26 が触る 5 + 触らない 11)の sha16・engine の束ねた指紋・frozen_bundle**・過去の門が engine を留めている所の一覧を縛る。

**この門の「封の commit 時点の値」(test_12 から test_14)は、段 1 の commit で「宣言された遷移」に更新する前提である。**
段 1 は engine 4 file(extract・vocabulary・recipes・registry_setup)と report_customer.py(理由の表の 3 行)を書き換える(comparators.py は触らない)ので、sha16・`adapter_xbrl_py_sha256`・frozen_bundle の束ねた sha がその場で動く。
この門は封の commit 時点の値を字で留めるので段 1 で赤くなる ― それが狙い。そのとき `ENGINE_TRANSITIONS` / `LATER_FINGERPRINT` / `LATER_FROZEN` に
(後の値, この封の path) を足して宣言する(P25 の封の門の ENGINE_LATER と同じ型)。宣言を足したら test_15 の「まだ無い」は skip に切り替わる
(報告形の直しの封の門 test_10 と同じ型)。

**試作の数(proto_v2.json・report2/proto.json)は repo に無い。** scratchpad の報告(追跡外、正本でない)から封に写した数で、この門は字と内訳の和だけを縛る。
記録に無い数を「測った」とは言わない。記録 `lastbranch_2026-10-21.json` と突き合わせられるのは、P25 の 4 state(7,799 claim・VALUE_MISMATCH 626 = P24 の 1,203 − 577)・
穴 B の分母 485 と通した 0・儀式の分母 247 と通した 2・段 2 の注入 64 と Core 自身が GROUNDED にした 0 だけ。

**封の下書きを写すときに実装席が見つけて報告した点は、司令塔が commit 前に封で直した(2026-10-22。直す前の写しは scratchpad/p26/seal_before_cmdfix.md)**:
旗 5 つの名前と型(`concept_gate: tuple`・`last_branch_digit_needs_size`・`rounded_diff_hold`・`cause_item_direction`・`numbers_2026_10_21`)・G1 の「その全部」と範囲・
G2 の手順・G3 を 1 本の旗 `rounded_diff_hold` に畳んだこと(`comparators.py` は触らず、正規化の登録はしない = engine 4 file + 報告形 1 file)・G4 の範囲と形と除外と順序・
G5 の関数名・人間の決定への「この後ろ」と `iter_numbers` 不変・Q-5(新しい GROUNDED 0)・Q-6(comparators 0)・§0 の「司令塔の直し」(赤 60 → 65、342 = 171 × 2、作れなかった 46)・
§4 の pin の遷移の一覧。この門は直した封の字に合わせてある。**pin の一覧は test_16 が実物から数え(PIN_DEF の grep と PIN_OTHER_TESTS)、封 §4 の一覧と突き合わせる。**
**新しい門で engine の留めを定義するときは変数名を `ENGINE_LATER` にしない**(P25 の封の門 test_10 が行頭の `ENGINE_LATER = {` を数えるので、この門は `ENGINE_TRANSITIONS`)。
"""
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
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_P26_SEAL_2026-10-21.md"
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL = os.path.join(ROOT, SEAL_REL)
LASTBRANCH_JSON = os.path.join(ROOT, "fixtures", "xbrl", "lastbranch_2026-10-21.json")
FRESH_SEAL_REL = "docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md"
REPORT_FIX_SEAL_REL = "docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md"
REPORT_FIX_COMMIT = "129ee9d"

# §4 の file 一覧(この順で書かれている)。engine 5 file(report_customer.py は理由の表の 3 行。comparators.py は触らないので入れない)→ 試験 → 測定 → 記録 → 結果 → 結果の門
ENGINE_FILES = ("adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py",
                "adapters/xbrl/registry_setup.py", "adapters/xbrl/report_customer.py")
P26_UNIT_TEST = "tests/adapters/xbrl/test_recipes_p26.py"
FILES = ("measure/xbrl_p26_2026-10-21.py",
         "fixtures/xbrl/p26_2026-10-21.json",
         "docs/XBRL_P26_RESULT_2026-10-21.md",
         "tests/measure/test_xbrl_p26_result.py")
# 封より後でなければ履歴に現れてはならない新規 file(§4 の 5 本)
AFTER = (P26_UNIT_TEST,) + FILES

# 封の commit 時点の adapters/xbrl 16 file の sha256 の先頭 16 桁(5d3074f の木)。**宣言された遷移の前の値**で、消さない。
# 段 1 が書き換えるのは §4 の ENGINE_FILES の 5 本だけ。残りの 11 本(comparators.py を含む)は P26 が触らない(動いたら赤のまま、遷移を持たない)。
ENGINE_AT_SEAL = {"adapters/xbrl/extract.py": "68a78f99f4d4c216",
                  "adapters/xbrl/vocabulary.py": "27e71e9861fc5aad",
                  "adapters/xbrl/recipes.py": "bff243f13429b553",
                  "adapters/xbrl/registry_setup.py": "f42ffe23aaa7673b",
                  "adapters/xbrl/report_customer.py": "715468699973cc4a"}
UNTOUCHED = {"adapters/xbrl/__init__.py": "65474b49e6b84626",
             "adapters/xbrl/comparators.py": "d8706338325e725b",         # 試作は +4 行だったが、G3 を旗 1 本に畳んだので封は触らない
             "adapters/xbrl/edinet.py": "e87d48d3597a4c4d",
             "adapters/xbrl/holds.py": "bed43d9e5c03565a",
             "adapters/xbrl/instance.py": "f2d9e040f19adebf",
             "adapters/xbrl/prose.py": "908ce389f16fac0b",
             "adapters/xbrl/report.py": "0d2854e659a5d8e0",              # 人間の決定 2026-10-13「判定に手を加えない・golden」
             "adapters/xbrl/resolve.py": "a41043763c1d4073",
             "adapters/xbrl/run.py": "e2192229bf2e4eff",
             "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
             "adapters/xbrl/verify_external.py": "0ae333392551912c"}
# 宣言された遷移(段 1 の commit で足す): {path: (後の sha16, 遷移を宣言した封の path)}。封の commit 時点では空。ENGINE_AT_SEAL は消さない。
# (変数名を ENGINE_LATER にしない: P25 の封の門 test_10 が tests/measure の「行頭の ENGINE_LATER = {」を数えて一覧と突き合わせるので、名前が同じだと既存の門が赤になる。段 1 の結果の門も同じ)
# 2026-10-22(段 1 の実装の便): 封が宣言した遷移。engine の 5 file が書き換わった(extract.py +42/-0・vocabulary.py +17/-0・recipes.py +251/-1・registry_setup.py +6/-0・
# report_customer.py +7/-2。comparators.py・report.py・verify_document.py・core/ は 0 行)。ENGINE_AT_SEAL(封の commit 時点の値)は消さない。
# 受け入れるのは、この封が履歴に在り、値が段 1 の後の値のときだけ。
ENGINE_TRANSITIONS = {"adapters/xbrl/extract.py": ("9982599fc31cbab3", SEAL_REL),
                      # 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ)。
                      # 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
                      "adapters/xbrl/vocabulary.py": ("e28733067b1f17f5", SEAL_DEFAULT_P26),
                      "adapters/xbrl/recipes.py": ("181b370420ab751b", SEAL_REL),
                      "adapters/xbrl/registry_setup.py": ("7f2cbded9c830211", SEAL_REL),
                      "adapters/xbrl/report_customer.py": ("141767d189b63733", SEAL_REL)}

# 封の commit 時点の engine の束ねた指紋(verify_document.engine_fingerprint())と frozen_bundle。**宣言された遷移の前の値**で、消さない。
FINGERPRINT_AT_SEAL = {"adapter_xbrl_py_sha256": "11840a097f04dcb4c01f057ce78d39c3aedabf139e65dbc5620e28c109f64693",
                       "adapter_xbrl_py_files": 16,
                       "core_py_sha256": "34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8",
                       "core_py_files": 4}
FROZEN_BUNDLE_AT_SEAL = "5c4da2e2ff3f30b7dcb6ebcbc84a5c68b074e8dc495f2d260551d7e10a4ce66c"   # frozen_bundle_sha.FROZEN_BUNDLE_GENERATIONS の最新(報告形の直しの段 1)
FROZEN_COUNT_AT_SEAL = 37
# 宣言された遷移(段 1 の commit で足す): {欄: (後の値, 遷移を宣言した封の path)}。封の commit 時点では空。
# adapter_xbrl_py_files は 16 のまま(file の数は動かない。段 1 が足すのは tests / measure / fixtures / docs で、adapters/ には 1 file も足さない)。
# 段 1 の実装の便: 束ねた指紋が 11840a09…(封の commit 時点)から 498993e2… に動き(file の数 16 は動かない)、frozen_bundle の世代がもう 1 つ増えた(a97ecf7c…。本数は 37 のまま)。
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 束ねた指紋が 498993e2…(P26 の段 1。残す)から 5aba7749… に動いた(file の数 16 は動かない)。受け入れるのは、封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md が履歴に在り、値が段 2 の後の値のときだけ。
LATER_FINGERPRINT = {"adapter_xbrl_py_sha256": ("5aba7749259683563c37e62353717f64b4e4828931998a7c42518aca107f3504", SEAL_DEFAULT_P26)}
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): frozen_bundle の世代がもう 1 つ増えた(26b52706…。本数は 37 のまま)。a97ecf7c…(P26 の段 1 の世代)は消さない。
LATER_FROZEN = {"bundle": ("26b5270646f2d8d8fcb7ca829f5f36066f9e2e9a1c3d1f0e4cdde1822e5d6fb6", SEAL_DEFAULT_P26)}

# §1「触る枝の中の人間の決定」の 9 つ(封の字の順)と、決定の commit が履歴に在ること
DECISIONS = (u"案ア(no_subject)", u"§1b の止め", u"C2 `period_cue`", u"C-1g §1-3 `_build_point_diff_claim`", u"P21 の最後の枝",
             u"P22 `period_bind`", u"P23 `_mag_trunc`", u"P24 の旗 2 つ", u"P25 の旗(証拠 (ii) は G2 の旗の下で条件を足す形、P25 の字は変えない)")
DECISION_COMMITS = ("5eb80a2", "3320c8c", "7d530cc", "8fc113f", "c7ad668", "92ae5e9", "9577eab")

# 過去の門が engine(adapters/xbrl の sha・指紋・profile の一覧・理由の数)を留めている所。**封の下書きには無かったので、実物から数えて門に持たせた**
# (報告の (3))。tests/measure に在る、engine の sha を宣言の遷移つきで留める門(正規表現 PIN_DEF で定義の行を探す)。
PIN_DEF = re.compile(r"(?m)^(ENGINE_LATER|ENGINE_AT_SEAL|UNTOUCHED|FROZEN_LATER|LATER_ENGINE_COMMITS|LATER_FINGERPRINT|FINGERPRINT_LATER|FINGERPRINT_AT_SEAL|"
                     r"LATER_TARGET|LATER_FROZEN|FROZEN_BUNDLE_AT_SEAL|TARGET_AT_SEAL)\b")
PIN_GATES_MEASURE = (
    # ENGINE_LATER 系(P24 までの封の一覧)
    "tests/measure/test_xbrl_branch_a.py", "tests/measure/test_xbrl_role_swap_result.py", "tests/measure/test_xbrl_axis3_decision.py",
    "tests/measure/test_xbrl_p20_result.py", "tests/measure/test_xbrl_a_core_vs_grep_seal.py", "tests/measure/test_xbrl_pnf_diag.py",
    # 結果 / 封の門 8 本
    "tests/measure/test_xbrl_point_prior_result.py", "tests/measure/test_xbrl_ritual_result.py",
    "tests/measure/test_xbrl_period_bind_seal.py", "tests/measure/test_xbrl_period_bind_result.py",
    "tests/measure/test_xbrl_rounding_seal.py", "tests/measure/test_xbrl_rounding_result.py",
    "tests/measure/test_xbrl_vocab_seal.py", "tests/measure/test_xbrl_vocab_result.py",
    # P25 の封・結果(P25 の封の一覧は「この門と P25 の結果の門を除く」と書いたので、いまは数える)
    "tests/measure/test_xbrl_lastbranch_seal.py", "tests/measure/test_xbrl_lastbranch_result.py",
    # cd_seal の FROZEN_LATER
    "tests/measure/test_xbrl_cd_seal.py",
    # 報告形の封・結果 4 本(UNTOUCHED で P26 が触る engine 5 file の sha を宣言の遷移なしで留める。P25 の封の一覧には無かった)
    "tests/measure/test_xbrl_customer_report_seal.py", "tests/measure/test_xbrl_customer_report_result.py",
    "tests/measure/test_xbrl_customer_report_fix_seal.py", "tests/measure/test_xbrl_customer_report_fix_result.py")
PIN_FILES_OTHER = ("fixtures/frozen_bundle_sha.py",)
# 封 §4 の pin の一覧の字(名前 → 実物の file)。一覧の 21 本 = PIN_GATES_MEASURE
SEAL_PIN_NAMES = (
    ("branch_a", "tests/measure/test_xbrl_branch_a.py"), ("role_swap", "tests/measure/test_xbrl_role_swap_result.py"),
    ("axis3", "tests/measure/test_xbrl_axis3_decision.py"), ("p20_result", "tests/measure/test_xbrl_p20_result.py"),
    ("a_core_vs_grep", "tests/measure/test_xbrl_a_core_vs_grep_seal.py"), ("pnf_diag", "tests/measure/test_xbrl_pnf_diag.py"),
    ("point_prior_result", "tests/measure/test_xbrl_point_prior_result.py"), ("ritual_result", "tests/measure/test_xbrl_ritual_result.py"),
    ("period_bind", "tests/measure/test_xbrl_period_bind_seal.py|tests/measure/test_xbrl_period_bind_result.py"),
    ("rounding", "tests/measure/test_xbrl_rounding_seal.py|tests/measure/test_xbrl_rounding_result.py"),
    ("vocab", "tests/measure/test_xbrl_vocab_seal.py|tests/measure/test_xbrl_vocab_result.py"),
    ("lastbranch", "tests/measure/test_xbrl_lastbranch_seal.py|tests/measure/test_xbrl_lastbranch_result.py"),
    ("cd_seal", "tests/measure/test_xbrl_cd_seal.py"),
    ("報告形の封と結果・報告形の直しの封と結果の 4 本", "tests/measure/test_xbrl_customer_report_seal.py|tests/measure/test_xbrl_customer_report_result.py|"
     "tests/measure/test_xbrl_customer_report_fix_seal.py|tests/measure/test_xbrl_customer_report_fix_result.py"))
# 封 §1 の旗 5 つ(名前, 型)と P26 の replace の字
FLAGS = (("concept_gate", "tuple = ()"), ("last_branch_digit_needs_size", "bool = False"), ("rounded_diff_hold", "bool = False"),
         ("cause_item_direction", "bool = False"), ("numbers_2026_10_21", "bool = False"))
P26_REPLACE = (u'`P26 = dataclasses.replace(P25, name="P26", concept_gate=("unit_family", "loose_prefix"), last_branch_digit_needs_size=True, '
               u'rounded_diff_hold=True, cause_item_direction=True, numbers_2026_10_21=True)`')
REASONS = ("other_concept", "direction_on_cause_item", "rounded_diff_within_double_band")
# 試作の差分(engine 5 file)を 5d3074f に当てて tests/measure と tests/adapters/xbrl を走らせたとき赤になった、PIN_DEF に当たらない file(2026-10-22 の実測 65 赤)
PIN_OTHER_TESTS = ("tests/measure/test_xbrl_verify_inventory.py",                  # DisciplineTest.test_9_engine_untouched
                   "tests/adapters/xbrl/test_mutations.py", "tests/adapters/xbrl/test_p17.py", "tests/adapters/xbrl/test_p20.py",
                   "tests/adapters/xbrl/test_recipes_p21.py", "tests/adapters/xbrl/test_recipes_p22.py", "tests/adapters/xbrl/test_recipes_p23.py",
                   "tests/adapters/xbrl/test_recipes_p24.py", "tests/adapters/xbrl/test_recipes_p25.py", "tests/adapters/xbrl/test_registry_setup.py",
                   "tests/adapters/xbrl/test_report_customer.py", "tests/adapters/xbrl/test_vocabulary.py")


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


def rng(line, tag_re):
    m = re.search(tag_re, line)
    assert m, tag_re
    return num(m.group(1)), num(m.group(2))


def s0_numbers(b):
    """§0 の数を、書かれた字のまま取り出す(書き方が変わったら落ちる)。"""
    m_p25 = one(r"無改変 67 書類 ([\d,]+) claim を P25 で: GROUNDED ([\d,]+)・POINTER_NOT_FOUND ([\d,]+)・UNVERIFIABLE ([\d,]+)・VALUE_MISMATCH ([\d,]+)\(([\d.]+)%\)", b, "P25 の 4 state")
    m_dg = one(r"別概念 (\d+)\(1 株当たり (\d+)・部分一致の別要素 (\d+)・語彙の行の別概念 (\d+)・値 0 の fact (\d+)\)、"
               r"同じ概念 (\d+)\(丸めた値の差 (\d+)・向きの語 (\d+)・区分の取り違えの疑い (\d+)・残高の差 (\d+) ほか\)", b, "診断")
    m_g3 = one(r"P25 で一致の差の主張 (\d+) 行に文を 1 単位小さくする注入を当てると、P25 が止めた (\d+) 行のうち (\d+) 行\(([\d.]+)%\)を一致にした", b, "G3 の代価")
    m_v = one(r"違う (\d+) → (\d+)\(([\d.]+)%\)、GROUNDED ([\d,]+) → ([\d,]+)\(一致から外れた (\d+) は全部偶然の一致\)、新しい GROUNDED (\d+)", b, "P26 の VM")
    m_mv = one(r"動いた (\d+) 行\(違う → UNVERIFIABLE rounded_diff_within_double_band (\d+)・違う → PNF other_concept (\d+)・"
               r"違う → UNVERIFIABLE direction_on_cause_item (\d+)・一致 → UNVERIFIABLE direction_on_cause_item (\d+)・"
               r"違う → PNF no_same_value (\d+)・PNF → UNVERIFIABLE direction_on_cause_item (\d+)・読みだけ (\d+)\)", b, "動いた行")
    m_rd = one(r"「違う」から外れた (\d+) 行を全部読み、正しい文 (\d+)・分からない (\d+)・違う (\d+)", b, "読み")
    m_in = one(r"穴 B 通した (\d+) / (\d+)、儀式 通した (\d+) / (\d+)\(数の読み取りで円銭の注入 (\d+) か所が表から消える。手で当てて通した (\d+)\)、"
               r"段 2 の注入 GROUNDED (\d+) / (\d+)、動いた行への注入 (\d+) 回\(有効 (\d+)\)で GROUNDED (\d+)", b, "穴 B・儀式・段 2・注入")
    m_cost = one(r"文を 1 単位小さくした注入の止め (\d+) が「違う」→「要確認」\(通すのは (\d+)\)、止め → 要確認 穴 B (\d+)・儀式 (\d+)・段 2 (\d+)", b, "代価")
    m_red = one(r"既存試験の赤 (\d+)\(engine の sha・指紋 (\d+)・profile の一覧 (\d+)・登録簿と理由の表 (\d+)・変異の予測 (\d+)、数 / state の門 (\d+)、人間の決定の字の門 (\d+)\)", b, "既存試験の赤")
    m_df = one(r"engine recipes \+(\d+)/−(\d+)・extract \+(\d+)・vocabulary \+(\d+)・registry_setup \+(\d+)・comparators \+(\d+)、既存の行の書き換え (\d+)", b, "engine の行数")
    return {"claims": num(m_p25.group(1)), "g": num(m_p25.group(2)), "pnf": num(m_p25.group(3)), "unv": num(m_p25.group(4)),
            "vm": num(m_p25.group(5)), "vm_pct": m_p25.group(6),
            "diag_other": int(m_dg.group(1)), "diag_per_share": int(m_dg.group(2)), "diag_loose": int(m_dg.group(3)),
            "diag_vocab": int(m_dg.group(4)), "diag_zero": int(m_dg.group(5)), "diag_same": int(m_dg.group(6)),
            "same_round": int(m_dg.group(7)), "same_dir": int(m_dg.group(8)), "same_section": int(m_dg.group(9)), "same_balance": int(m_dg.group(10)),
            "g3_den": int(m_g3.group(1)), "g3_stopped": int(m_g3.group(2)), "g3_passed": int(m_g3.group(3)), "g3_pct": m_g3.group(4),
            "vm_before": int(m_v.group(1)), "vm_after": int(m_v.group(2)), "vm_after_pct": m_v.group(3),
            "g_before": num(m_v.group(4)), "g_after": num(m_v.group(5)), "g_out": int(m_v.group(6)), "g_new": int(m_v.group(7)),
            "moved": int(m_mv.group(1)), "mv_round": int(m_mv.group(2)), "mv_concept": int(m_mv.group(3)), "mv_dir": int(m_mv.group(4)),
            "mv_g_dir": int(m_mv.group(5)), "mv_nsv": int(m_mv.group(6)), "mv_pnf_dir": int(m_mv.group(7)), "mv_read_only": int(m_mv.group(8)),
            "read": int(m_rd.group(1)), "read_right": int(m_rd.group(2)), "read_unknown": int(m_rd.group(3)), "read_wrong": int(m_rd.group(4)),
            "hole_pass": int(m_in.group(1)), "hole_den": int(m_in.group(2)), "rit_pass": int(m_in.group(3)), "rit_den": int(m_in.group(4)),
            "rit_gone": int(m_in.group(5)), "rit_hand": int(m_in.group(6)), "s2_g": int(m_in.group(7)), "s2_den": int(m_in.group(8)),
            "inj": int(m_in.group(9)), "inj_valid": int(m_in.group(10)), "inj_g": int(m_in.group(11)),
            "cost_stop": int(m_cost.group(1)), "cost_pass": int(m_cost.group(2)), "cost_hole": int(m_cost.group(3)),
            "cost_rit": int(m_cost.group(4)), "cost_s2": int(m_cost.group(5)),
            "red": int(m_red.group(1)), "red_sha": int(m_red.group(2)), "red_list": int(m_red.group(3)), "red_reg": int(m_red.group(4)),
            "red_mut": int(m_red.group(5)), "red_state": int(m_red.group(6)), "red_decision": int(m_red.group(7)),
            "rec_ins": int(m_df.group(1)), "rec_del": int(m_df.group(2)), "ext": int(m_df.group(3)), "voc": int(m_df.group(4)),
            "reg": int(m_df.group(5)), "cmp": int(m_df.group(6)), "rewrite": int(m_df.group(7)), "docs": 67}


class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)

    def test_1_human_policy_is_quoted_and_stage_1_is_not_the_default(self):
        head = self.t[:self.t.index("\n## §0 ")]
        self.assertTrue(head.startswith(u"# 封: 「違う」に出る正しい文の主因を減らす(engine の直し P26 = P25 + 旗 5 つ)― 2026-10-21"))
        for s in (u"**人間(2026-10-21 朝)「報告形の問題はきちんと解決して」「あとは全て任せる」。",
                  u"報告形の直し(`docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md`)を監査が顧客の目で読み、",
                  u"その根は engine にある。",
                  u"作法は変えない(封 → 実装 → 凍結 → 独立監査 GO → commit)。",
                  u"数を見てから封・予測を直さない。外れは外れとして残す。",
                  u"段 1 では既定にしない(DEFAULT_PROFILE = \"P22\" のまま)。",
                  u"既定は封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md` §3 の基準で決める",
                  u"この封の段 1 が新しい標本の取得より前に commit されれば P26 が最初の候補)。**"):
            self.assertIn(s, head, s)
        # 引用している封が在り、その §3 が P26 を候補の先頭に置いている(字の食い違いを避ける)
        fresh = text(os.path.join(ROOT, FRESH_SEAL_REL))
        self.assertIn(u"候補は P26 → P25 → P24 の順", fresh)
        self.assertTrue(os.path.exists(os.path.join(ROOT, REPORT_FIX_SEAL_REL)))

    def test_2_eight_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §2", "## §3")
        ids, lines = predictions(b, "Q")
        self.assertEqual(ids, [str(i) for i in range(1, 9)])
        self.assertEqual(len(lines), 8)
        for line in lines:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[1], u"予測が空: " + line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        # 行ごとに、予測の幅と外れ方の両方を字で縛る(幅を直すと赤くなる)
        for i, ss in (("1", (u"67 書類の無改変で VALUE_MISMATCH **425〜441**、新しい GROUNDED **0**、GROUNDED → 非 GROUNDED **8〜14**",
                             u"幅の外 / 新 GROUNDED 1 以上")),
                      ("2", (u"「違う」から外れた行を全部読み、「文が本当に違う」**0〜2**", u"3 以上")),
                      ("3", (u"穴 B 通した **0 / 485**、儀式 通した **2〜3**、段 2 の注入 GROUNDED **0 / 64**", u"幅の外")),
                      ("4", (u"動いた行への注入(1 回 1 件、末尾の桁 ±3・10 倍)で P26 の GROUNDED **0**", u"1 以上")),
                      ("5", (u"P25 で一致の差の主張への末尾の桁 ±1 の注入で、P25 が止めて P26 が GROUNDED にした行(新しい GROUNDED)**0**",
                             u"(G3 が誤りを通さない。P25 も P26 も GROUNDED にする行は数えない ― 試作では 9 行)", u"1 以上")),
                      ("6", (u"engine の差分 recipes **+240〜+300 / −0〜−2**、extract **≤ 60**、vocabulary **≤ 45**、registry_setup **≤ 15**、comparators **0**、core/ 0。",
                             u"既存試験の赤は sha・指紋・profile の一覧・登録簿と理由の表・変異の予測の連鎖だけ(数 / state の門 0、人間の決定の字の門 0)",
                             u"超える / 種類の外の赤")),
                      ("7", (u"報告形で P26 明示の 67 書類の「違う」の節 = P26 の VALUE_MISMATCH、3 つの理由は全部「要確認」の節、登録簿の理由の網羅 16 → 19", u"違う")),
                      ("8", (u"段 2(既定)は封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md` §3 の基準で", u"―"))):
            line = lines[int(i) - 1]
            for s in ss:
                self.assertIn(s, line, "Q-%s: %s" % (i, s))
        self.assertIn(u"**Q-1・Q-3〜Q-5 は試作の再現。本当に外れうるのは Q-2(実装席が読み直す)と、新しい標本での判定(Q-8)。**", b)
        # 算術: 試作の値は幅の中(幅は試作の周りに置いた。幅の算術を字で縛る)
        n = s0_numbers(s0(self.t))
        lo, hi = rng(lines[0], r"VALUE_MISMATCH \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["vm_after"] <= hi, (lo, n["vm_after"], hi))
        self.assertEqual((n["vm_after"] - lo, hi - n["vm_after"]), (8, 8))    # 試作 433 の ±8
        lo, hi = rng(lines[0], r"GROUNDED → 非 GROUNDED \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["mv_g_dir"] <= hi, (lo, n["mv_g_dir"], hi))
        self.assertEqual(n["g_new"], 0)
        lo, hi = rng(lines[1], r"「文が本当に違う」\*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["read_wrong"] <= hi)
        self.assertEqual(n["read_wrong"], 0)
        lo, hi = rng(lines[2], r"儀式 通した \*\*(\d+)〜(\d+)\*\*")
        self.assertTrue(lo <= n["rit_pass"] <= hi)
        self.assertEqual((n["hole_pass"], n["hole_den"]), (0, 485))
        self.assertEqual((n["s2_g"], n["s2_den"]), (0, 64))
        self.assertEqual(n["inj_g"], 0)
        lo, hi = rng(lines[5], r"recipes \*\*\+(\d+)〜\+(\d+) / −0〜−2\*\*")
        self.assertTrue(lo <= n["rec_ins"] <= hi, (lo, n["rec_ins"], hi))
        self.assertTrue(0 <= n["rec_del"] <= 2)
        for key, name in (("ext", "extract"), ("voc", "vocabulary"), ("reg", "registry_setup")):
            cap = int(re.search(r"%s \*\*≤ (\d+)\*\*" % name, lines[5]).group(1))
            self.assertLessEqual(n[key], cap, name)
        # comparators は 0(試作は +4 だったが、G3 を旗 1 本に畳んだので触らない。§0 の試作の +4 は試作の数として残る)
        self.assertIn(u"comparators **0**", lines[5])
        self.assertNotIn(u"comparators **≤", lines[5])
        # Q-5: 新しい GROUNDED を数える(P25 も P26 も GROUNDED にする試作の 9 行 = +1 の 7 と −1 の 2 は数えない)
        self.assertIn(u"新しい GROUNDED)**0**", lines[4])
        self.assertEqual(7 + 2, int(re.search(r"試作では (\d+) 行", lines[4]).group(1)))
        # Q-7: 登録簿の理由の網羅 16 → 19 = 理由 3 つを足す
        a, b2 = [int(x) for x in re.search(r"登録簿の理由の網羅 (\d+) → (\d+)", lines[6]).groups()]
        self.assertEqual((a, b2, b2 - a), (16, 19, 3))

    def test_3_section_0_numbers_are_pinned_as_written(self):
        b = s0(self.t)
        n = s0_numbers(b)
        # P25 の 4 state(7,799 claim)と率
        self.assertEqual((n["claims"], n["g"], n["pnf"], n["unv"], n["vm"]), (7799, 4382, 1394, 1397, 626))
        self.assertEqual(n["g"] + n["pnf"] + n["unv"] + n["vm"], n["claims"])
        self.assertEqual(n["vm_pct"], "%.1f" % (100.0 * n["vm"] / n["claims"]))
        # 診断: 別概念 32 = 1 + 25 + 2 + 4、同じ概念 594 = 626 − 32、下位の型の和は 594 以下("ほか")
        self.assertEqual((n["diag_per_share"], n["diag_loose"], n["diag_vocab"], n["diag_zero"]), (1, 25, 2, 4))
        self.assertEqual(n["diag_per_share"] + n["diag_loose"] + n["diag_vocab"] + n["diag_zero"], n["diag_other"])
        self.assertEqual(n["diag_other"], 32)
        self.assertEqual(n["diag_other"] + n["diag_same"], n["vm"])
        self.assertEqual(n["diag_same"], 594)
        self.assertEqual((n["same_round"], n["same_dir"], n["same_section"], n["same_balance"]), (161, 162, 139, 64))
        self.assertLessEqual(n["same_round"] + n["same_dir"] + n["same_section"] + n["same_balance"], n["diag_same"])
        # 丸めた差を GROUNDED にする版(G3)は採らない: 608 行、P25 が止めた 301 行のうち 156 行(51.8%)を一致にした
        self.assertEqual((n["g3_den"], n["g3_stopped"], n["g3_passed"], n["g3_pct"]), (608, 301, 156, "51.8"))
        self.assertEqual(n["g3_pct"], "%.1f" % (100.0 * n["g3_passed"] / n["g3_stopped"]))
        self.assertLessEqual(n["g3_stopped"], n["g3_den"])
        self.assertIn(u"**丸めた差を GROUNDED にする版(試作 P26 の G3)は採らない**", b)
        # 試作 P26b v2: 違う 626 → 433(5.6%)、GROUNDED 4,382 → 4,371(外れた 11)、新しい GROUNDED 0
        self.assertEqual((n["vm_before"], n["vm_after"], n["vm_after_pct"]), (626, 433, "5.6"))
        self.assertEqual(n["vm_before"], n["vm"])
        self.assertEqual(n["vm_after_pct"], "%.1f" % (100.0 * n["vm_after"] / n["claims"]))
        self.assertEqual((n["g_before"], n["g_after"], n["g_out"], n["g_new"]), (4382, 4371, 11, 0))
        self.assertEqual(n["g_before"], n["g"])
        self.assertEqual(n["g_before"] - n["g_out"] + n["g_new"], n["g_after"])
        # 動いた 217 行の内訳(和)。「違う」から外れた 193 = 158 + 23 + 11 + 1。一致 → UNVERIFIABLE 11 = 一致から外れた 11
        self.assertEqual((n["moved"], n["mv_round"], n["mv_concept"], n["mv_dir"], n["mv_g_dir"], n["mv_nsv"], n["mv_pnf_dir"], n["mv_read_only"]),
                         (217, 158, 23, 11, 11, 1, 2, 11))
        self.assertEqual(n["mv_round"] + n["mv_concept"] + n["mv_dir"] + n["mv_g_dir"] + n["mv_nsv"] + n["mv_pnf_dir"] + n["mv_read_only"], n["moved"])
        out_of_vm = n["mv_round"] + n["mv_concept"] + n["mv_dir"] + n["mv_nsv"]
        self.assertEqual(out_of_vm, 193)
        self.assertEqual(n["vm_before"] - out_of_vm, n["vm_after"])
        self.assertEqual(n["mv_g_dir"], n["g_out"])
        # 4 state の閉じ方(封に書かれた遷移から導く。UNVERIFIABLE と POINTER_NOT_FOUND の合計も 7,799 に閉じる)
        unv_after = n["unv"] + n["mv_round"] + n["mv_dir"] + n["mv_g_dir"] + n["mv_pnf_dir"]
        pnf_after = n["pnf"] + n["mv_concept"] + n["mv_nsv"] - n["mv_pnf_dir"]
        self.assertEqual((unv_after, pnf_after), (1579, 1416))
        self.assertEqual(n["g_after"] + n["vm_after"] + unv_after + pnf_after, n["claims"])
        # 読み: 外れた 193 行を全部読み、正しい 186・分からない 7・違う 0
        self.assertEqual((n["read"], n["read_right"], n["read_unknown"], n["read_wrong"]), (193, 186, 7, 0))
        self.assertEqual(n["read_right"] + n["read_unknown"] + n["read_wrong"], n["read"])
        self.assertEqual(n["read"], out_of_vm)
        # 穴 B・儀式・段 2・注入。儀式の分母 247 → 243 は円銭の注入 4 か所(G5 の下で表から消える)
        self.assertEqual((n["hole_pass"], n["hole_den"], n["rit_pass"], n["rit_den"], n["rit_gone"], n["rit_hand"]), (0, 485, 2, 243, 4, 0))
        self.assertEqual(247 - n["rit_gone"], n["rit_den"])
        self.assertEqual((n["s2_g"], n["s2_den"], n["inj"], n["inj_valid"], n["inj_g"]), (0, 64, 342, 318, 0))
        self.assertLessEqual(n["inj_valid"], n["inj"])
        # 代価: 止め 165 = 単独 156 + 重複 9(G3 の通した 156 と同じ行)。通すのは 0
        self.assertEqual((n["cost_stop"], n["cost_pass"], n["cost_hole"], n["cost_rit"], n["cost_s2"]), (165, 0, 1, 1, 1))
        self.assertEqual(n["cost_stop"], n["g3_passed"] + 9)
        # 既存試験の赤 60 = 31 + 19 + 9 + 1(数 / state の門 0、人間の決定の字の門 0)
        self.assertEqual((n["red"], n["red_sha"], n["red_list"], n["red_reg"], n["red_mut"], n["red_state"], n["red_decision"]), (60, 31, 19, 9, 1, 0, 0))
        self.assertEqual(n["red_sha"] + n["red_list"] + n["red_reg"] + n["red_mut"], n["red"])
        # engine の行数(試作): recipes +267/−1・extract +42・vocabulary +35・registry_setup +12・comparators +4、既存の行の書き換え 1
        self.assertEqual((n["rec_ins"], n["rec_del"], n["ext"], n["voc"], n["reg"], n["cmp"], n["rewrite"]), (267, 1, 42, 35, 12, 4, 1))
        self.assertEqual(n["rec_del"], n["rewrite"])
        self.assertEqual(n["rec_ins"] + n["rec_del"] + n["ext"] + n["voc"] + n["reg"] + n["cmp"], 361)   # 試作の差分 +360/−1
        # 司令塔の直し(2026-10-22): 赤 60 は 9dfb608 の時点、5d3074f で 65(増えた 5 = 報告形の直しの封の門 3 + 結果の門 2)、342 = 171 × 2、動いた 217 のうち 46 行は作れなかった
        fix = [l for l in b.splitlines() if l.startswith(u"- **司令塔の直し(commit 前、2026-10-22。封の門の席の指摘)**")]
        self.assertEqual(len(fix), 1)
        m = re.search(r"実測は (\d+)\(増えた (\d+) は報告形の直しの封の門 (\d+)・結果の門 (\d+)", fix[0])
        self.assertTrue(m, u"司令塔の直しの行の書き方が変わった: 赤")
        total, added, f_seal, f_result = [int(x) for x in m.groups()]
        self.assertEqual((total, added, f_seal, f_result), (65, 5, 3, 2))
        self.assertEqual(n["red"] + added, total)
        self.assertEqual(f_seal + f_result, added)
        m = re.search(r"注入を作れた (\d+) 行 × 2 型\(動いた (\d+) のうち (\d+) 行は作れなかった\)", fix[0])
        self.assertTrue(m, u"司令塔の直しの行の書き方が変わった: 342")
        made, moved, notmade = [int(x) for x in m.groups()]
        self.assertEqual((made, moved, notmade), (171, 217, 46))
        self.assertEqual(made * 2, n["inj"])
        self.assertEqual(made + notmade, n["moved"])
        self.assertEqual(moved, n["moved"])
        for t in (u"種類は sha・指紋・frozen_bundle で Q-6 の種類の中、数 / state の門と人間の決定の字の門は 0 のまま",
                  u"G3 を 1 本の旗 `rounded_diff_hold` に畳んだ(試作は GROUNDED にする旗と UNVERIFIABLE に落とす旗を 2 本とも真にしていた。"
                  u"落とす版だけなので `comparators.py` と正規化の登録は要らない)",
                  u"Q-5 の数える行を新しい GROUNDED と明記"):
            self.assertIn(t, fix[0], t)
        # 試作の位置づけの字(正本でない・同じ 67 書類・新しい標本で外れうる)
        for s in (u"(scratchpad の clone で試作 2 回。正本でない。`scratchpad/p26/proto_v2.json`・`scratchpad/report2/proto.json`)",
                  u"**試作は同じ 67 書類で測った。** 新しい標本(封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md`)で外れうる。",
                  u"P25 の証拠 (ii) の穴(名指す値が 2 単位より小さいと必ず真: 400 円 対 1 百万円)。",
                  u"数の読み取りの崩れ(「2兆3,471億円」→ 3,471 億円、「6万5千円」→ 5 千円、「148円22銭」→ 148 円)。",
                  u"「違う」から外れた 193 行を全部読み"):
            self.assertIn(s, b, s)

    def test_4_section_0_p25_numbers_match_the_records(self):
        """§0 の「P25 で」の数と、穴 B・儀式・段 2 の分母は、P25 段 1 の記録 fixtures/xbrl/lastbranch_2026-10-21.json と同じ。
        試作 P26b の数(433・4,371・217・193・342 など)は記録に無いので突き合わせない(docstring)。"""
        n = s0_numbers(s0(self.t))
        r = jload(LASTBRANCH_JSON)
        agg = r["L1"]["集計"]
        self.assertEqual(agg["総 claim"], n["claims"])
        self.assertEqual(agg["書類数"], n["docs"])
        self.assertEqual(agg["GROUNDED の合計 P25"], n["g"])
        self.assertEqual(agg["VALUE_MISMATCH の合計 P25"], n["vm"])
        self.assertEqual(agg["UNVERIFIABLE の合計 P25"], n["unv"])
        self.assertEqual(agg["POINTER_NOT_FOUND の合計 P25"], n["pnf"])
        # 書類別の state を足しても同じ(合計の欄の取り違えを避ける): P25 の VM は P24 の 1,203 − 577 = 626
        self.assertEqual(agg["VALUE_MISMATCH の合計 P24"] - agg["動いた(全 state)"], n["vm"])
        self.assertEqual(r["書類の数"]["経営分析の文を持つ"], n["docs"])
        self.assertEqual(len(r["L1"]["書類"]), n["docs"])
        # 穴 B: 485、P25 で通した 0
        w4 = r["L4"]["集計"]
        self.assertEqual((w4["P25 で通した(GROUNDED のまま)"]["件"], w4["P25 で通した(GROUNDED のまま)"]["分母"]), (n["hole_pass"], n["hole_den"]))
        self.assertEqual(len(r["L4"]["行"]), n["hole_den"])
        # 儀式: P25 の分母 247。P26 の 243 = 247 − 円銭の注入 4 か所。P25 で通した 2(N069・N096)
        l5 = r["L5"]
        self.assertEqual(l5["通した P25"]["件"], n["rit_pass"])
        self.assertEqual(l5["通した P25"]["分母"], n["rit_den"] + n["rit_gone"])
        self.assertEqual(len(l5["行"]), 247)
        self.assertEqual(sorted(x["id"] for x in l5["通した P25 の一覧"]), ["N069", "N096"])
        # 段 2 の材料: 注入 64、Core 自身 P25 が GROUNDED にした 0
        l6 = r["L6"]["集計"]
        self.assertEqual((l6["全注入で Core 自身 P25 が GROUNDED"]["件"], l6["全注入で Core 自身 P25 が GROUNDED"]["分母"]), (n["s2_g"], n["s2_den"]))
        self.assertEqual(l6["注入"], n["s2_den"])

    def test_5_section_1_flags_reasons_and_report_lines(self):
        b = sec(self.t, "## §1", "## §2")
        self.assertTrue(b.startswith(u"\n## §1 直しの中身(engine 4 file + 報告形 1 file、core/ 0 行。人間の決定の行は byte 一致、既存の行の書き換えは G5 の 1 行だけ)"))
        lines = b.splitlines()

        def bullet(prefix):
            """top-level の箇条書き 1 つ(次の top-level の箇条書きまで。入れ子を含む)"""
            idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
            self.assertEqual(len(idx), 1, prefix)
            j = idx[0] + 1
            while j < len(lines) and not lines[j].startswith(u"- "):
                j += 1
            return u"\n".join(lines[idx[0]:j])

        # --- vocabulary.py: 旗 5 つの名前と型、P26 の replace の字
        v = bullet(u"- `vocabulary.py`:")
        self.assertIn(u"`Profile` に旗 5 つ ― ", v)
        pos = []
        for name, typ in FLAGS:
            tok = u"`%s: %s`" % (name, typ)
            self.assertEqual(v.count(tok), 1, tok)
            pos.append(v.index(tok))
        self.assertEqual(pos, sorted(pos))
        self.assertIn(u"。**" + P26_REPLACE + u"、`PROFILES[\"P26\"] = P26`。試作の P26b を P26 と呼ぶ。", v)
        kws = re.findall(r"(\w+)=", re.search(r"`P26 = dataclasses\.replace\(([^`]*)\)`", v).group(1))
        self.assertEqual(kws, ["name"] + [n for n, _ in FLAGS])       # replace に旗 5 つが全部、この順で
        self.assertNotIn("rounded_diff_band", re.search(r"`P26 = dataclasses\.replace\(([^`]*)\)`", v).group(1))
        self.assertIn(u"丸めた差を GROUNDED にする版と旗 1 つずつの profile は engine に登録しない**(旗ごとの効きは measure の中で `dataclasses.replace` して測る)。", v)
        # --- G1
        g1 = bullet(u"- **G1 概念の門**")
        for t in (u"- **G1 概念の門**(`concept_gate`): 全部の claim を作った後に 1 度だけ。",
                  u"束縛が無い claim と、GROUNDED の claim(ただし `builtin:sign(cur-prior)` を名指し再計算の差がちょうど 0 のものは GROUNDED と数えない)には触らない。",
                  u"xbrl の pointer が無ければ触らない。",
                  u"当たれば POINTER_NOT_FOUND `other_concept`(名指した xbrl の fact と当たった規則は provenance)。",
                  u"  - `unit_family`: claim の単位が「百万円・千円・億円・兆円・円」のどれかか単位なしのとき、xbrl の pointer の fact のうち単位が `JPY` で始まるものについて、",
                  u"「単位が `JPY` そのものでない」と「主語の字に『株当たり』がある」が食い違えば当たる(総額の主語に 1 株当たりの fact、またはその逆)。",
                  u"  - `loose_prefix`: 主語の出どころ(`subject_from`)が `flow_item`・`ratio_table` でないとき、",
                  u"先頭の xbrl の pointer の要素名(名前空間を除く)が、どの要素 e とも完全一致しない",
                  u"(e・e + `SummaryOfBusinessResults`・e の `Income` を `IncomeLoss` にして + `SummaryOfBusinessResults` のどれとも同じでない)とき、",
                  u"要素名に大文字小文字を無視して含まれる e が 1 つ以上あり、**その全部**で前に付いた字が「」・`Cash`・`NetCashProvidedByUsedIn`・`CashFlowsFromUsedIn` のどれでもなければ当たる。",
                  u"  - 当てる順は `unit_family` → `loose_prefix`。"):
            self.assertIn(t, g1, t)
        self.assertEqual(g1.count(u"**その全部**"), 1)       # 「その全部」(all)。「どれか」(any)にしない
        # --- G2
        g2 = bullet(u"- **G2**")
        for t in (u"(`last_branch_digit_needs_size`、P25 の旗と一緒に真のときだけ)",
                  u"P25 の証拠 (ii)(差 ≤ 2 単位)が当たっても、名指す値の絶対値が 2 × 主張の桁 より小さいときは (ii) を証拠にせず、"
                  u"(iii)(10^n の帯、P25 と同じ n の順・同じ帯)だけを見直す。",
                  u"それでも証拠が無ければ P25 と同じ POINTER_NOT_FOUND `no_same_value`。(i)・(iii) の字は P25 のまま。"):
            self.assertIn(t, g2, t)
        # --- G3: 旗は 1 本、GROUNDED にはしない、comparators.py は触らない、正規化の登録はしない
        g3 = bullet(u"- **G3 丸めた差**")
        for t in (u"(`rounded_diff_hold`)",
                  u"書類の丸め方を決めた 2 周目(rounding が決まった後)で、増減の文が当期の残高(context が `CurrentYearInstant` で始まる)を選び、"
                  u"その前期の対の fact が在り、2 つの fact の 10^−decimals がどちらも主張の桁と同じ(decimals が無い・INF なら当てない)で、"
                  u"0 ≤ |a − b| − |文の数| < 2 × 桁 のとき、",
                  u"既存の F3b の照合より前で、結ばずに UNVERIFIABLE `rounded_diff_within_double_band`(名指した対と差は provenance)。",
                  u"**GROUNDED にはしない。**",
                  u"旗は 1 本で、丸めた差を一致にする照合(試作の `rounded_diff_band`・`comparators.py` の 2 倍の帯・正規化 `rounded_diff` の登録)は作らない。"):
            self.assertIn(t, g3, t)
        self.assertNotIn(u"`rounded_diff_band`", u"".join(n for n, _ in FLAGS))
        # --- G4
        g4 = bullet(u"- **G4 要因の項目にかかる語**")
        for t in (u"(`cause_item_direction`): 全部の claim を作った後に、向きの語(増加・減少など、claim の `word`)と主語の字が在る文字の主張に当てる。",
                  u"既に UNVERIFIABLE の主張には触らない。GROUNDED の行にも当てる。",
                  u"主語と語の間の字(gap)は、語より前で**最後に**現れた主語の字の後ろから語の前まで。",
                  u"  - 形 A: 語の直前が「等の」「などの」で、gap に `V.UNIT_SCALE` の単位(百万円・千円・億円・兆円・円)の数が在る。",
                  u"  - 形 C: 語の直前が「の」、直後が「等によ」「などによ」で、gap が「の」だけでない。",
                  u"  - 除外(先に見る): gap が「や」「・」「、」で始まり、その後ろが「などの」「等の」「の」(長い順に 1 つ)で終わり、間が空でなく、"
                  u"間に数字(半角・全角)・「は」「が」「を」「に」「で」・句点・括弧(半角・全角)のどれも無い(主語が列挙の 1 つ)。",
                  u"  - 当たれば結ばず UNVERIFIABLE `direction_on_cause_item`(形と、名指していた fact・その結果は provenance)。",
                  u"  - G4 は G1 より先に当てる。"):
            self.assertIn(t, g4, t)
        # --- G5
        g5 = bullet(u"- **G5 数の読み取り**")
        for t in (u"(`numbers_2026_10_21`、`extract.py` に新しい関数 `iter_numbers_2026_10_21`)",
                  u"「N兆M,MMM億円」「N万M千(L百)円」「N円MM銭」を 1 つの数(円)に読む。精度は書かれた最小の位。重なる既存の読みは捨てる。",
                  u"旗が偽なら `iter_numbers` のまま(数の読み取りを呼ぶ for 文 1 行を、旗で選ぶ関数に書き換える。これが既存の行の書き換え 1)。",
                  u"`iter_numbers` 自身の字は変えない。"):
            self.assertIn(t, g5, t)
        # --- 登録簿・比較器・正規化
        reg = bullet(u"- 登録簿(`registry_setup.py`)")
        self.assertIn(u"に理由 3 つ(`other_concept` は POINTER_NOT_FOUND の理由、`direction_on_cause_item`・`rounded_diff_within_double_band` は UNVERIFIABLE の理由)。"
                      u"正規化の登録は足さない。`comparators.py` は触らない。", reg)
        # 理由 3 つの state(封の字): PNF 1・UNVERIFIABLE 2
        self.assertEqual(REASONS, ("other_concept", "direction_on_cause_item", "rounded_diff_within_double_band"))
        # --- 報告形の 3 行
        rp = bullet(u"- **報告形(`report_customer.py`)の理由の表に 3 行**")
        for t in (u"(「要確認」の節): ",
                  u"`other_concept`「道具が当てた出典の数が、文の項目と別のもの(1 株当たりの数や、名前の一部だけが同じ別の項目)だった。文の項目の数を確かめる」、",
                  u"`direction_on_cause_item`「増加・減少の語が文の主語でなく、要因に挙げた項目にかかる。主語が増えたか減ったかは道具は判断していない」、",
                  u"`rounded_diff_within_double_band`「出典の前期と当期の差と 1 単位だけずれる。丸めた数どうしの差で出るずれか、1 単位の書き誤りかを道具は見分けられない。元の数で確かめる」。",
                  u"判定と他の節の割り当ては変えない。"):
            self.assertIn(t, rp, t)
        # --- 触る枝の中の人間の決定の「この後ろ」の字(test_6 が 9 つの順序を縛る)
        dc = bullet(u"- **触る枝の中の人間の決定")
        for t in (u"**G1・G4 は全部の claim を作った後に当てる(この後ろ)。",
                  u"その前の規則 ― A1(2026-10-08 符号と金額)・S4 と extract の skip(主語の規則の直し、人間の判断 1)・C-1g §1-2 の CF の符号の規約・"
                  u"§6 の括弧内の前期の向きの語 ― の字は変えず、G1・G4 が動かした行は記録に全部出す。",
                  u"G5 は `iter_numbers` の字を変えず(写し元との照合 `test_lineage` は緑のまま)、新しい関数を旗で選ぶ。**"):
            self.assertIn(t, dc, t)
        # 箇条書き(top-level)は 9 つ: vocabulary・G1〜G5・登録簿・報告形・触る枝の中の人間の決定
        self.assertEqual(len([l for l in lines if l.startswith(u"- ")]), 9)
        # GROUNDED と書いてあるのは「作らない・触らない・数えない」の文脈だけ(G1・G3 は GROUNDED を作らない)
        for m in re.finditer(r"GROUNDED", b):
            ctx = b[m.start():m.end() + 14]
            self.assertTrue(any(ctx.startswith(k) for k in (u"GROUNDED にする版", u"GROUNDED の claim", u"GROUNDED と数えない",
                                                           u"GROUNDED の行にも", u"GROUNDED にはしない")), ctx)

    def test_6_the_nine_decisions_in_the_touched_branch_are_listed_in_order(self):
        b = sec(self.t, "## §1", "## §2")
        line = [l for l in b.splitlines() if l.startswith(u"- **触る枝の中の人間の決定")][0]
        self.assertTrue(line.startswith(u"- **触る枝の中の人間の決定(字も振る舞いも壊さない)**: "))
        for s in DECISIONS:
            self.assertIn(s, line, s)
        positions = [line.index(s) for s in DECISIONS]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(DECISIONS), 9)
        self.assertIn(u"P16〜P25 を明示した試験の数は 1 つも変えない。", line)

    def test_7_the_decisions_exist_in_the_engine_now(self):
        """封が名指した人間の決定が、いまの engine の字に在る(封が実物と食い違っていない)。段 1 の後も 1 つも壊さない約束なので、この assert は段 1 の後も残す。
        案ア・§1b・C2・P21 の最後の枝・P22 の period_bind・P23 の _mag_trunc・P24 の旗・P25 の旗と、最後の枝の中の順(P25 の封の門 test_8 と同じ字)。"""
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
        self.assertIn('getattr(profile, "period_bind", False) and subj and not _prior_cue(s, a, b) and not _prior_cue_clause(s, a)', body)
        self.assertIn("\ndef _prior_cue_clause(s, pos):\n", r)
        self.assertIn("\ndef _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num, tol=PCT_TOLERANCE_DEFAULT):\n", r)
        j = r.index("def _build_point_diff_claim(")
        pbody = r[j:r.index("\ndef ", j + 1)]
        self.assertIn("    window = s[max(0, a - 25):a]\n    if not _POINT_PRIOR_PHRASE_RE.search(window):\n", pbody)
        self.assertIn('        if profile.point_diff and unit == "ポイント" and subj:\n            _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num, tol)\n', r)
        k = r.index("def _mag_trunc(profile, rounding):")
        mbody = r[k:r.index("\ndef ", k + 1)]
        self.assertIn('getattr(profile, "truncate_on_magnitude", False)', mbody)
        self.assertIn('getattr(profile, "truncate_abs_band", False) and rounding == "truncate"', mbody)
        self.assertIn('P24 = dataclasses.replace(P23, name="P24", vocab_2026_10_21=True, frame_rebind=True)', v)
        self.assertIn('getattr(profile, "frame_rebind", False)', body)
        # P25 の旗: P25 = P24 + 旗 1 つ。証拠 (ii) の定数と関数が在る(G2 は (ii) に条件を足すだけで、P25 の字は変えない)
        self.assertIn("last_branch_names_only_if_evidence: bool = False", v)
        self.assertIn('P25 = dataclasses.replace(P24, name="P25", last_branch_names_only_if_evidence=True)', v)
        self.assertIn("\nLAST_BRANCH_DIGIT_K = 2", r)
        self.assertIn("\ndef _last_branch_unname(", r)
        self.assertIn('getattr(profile, "last_branch_names_only_if_evidence", False) and _last_branch_unname(', body)
        # 決定の commit が履歴に在る(浅い clone では skip せず、在るかだけ見る)
        for c in DECISION_COMMITS:
            self.assertEqual(git("cat-file", "-e", c + "^{commit}").returncode, 0, u"封が名指す commit %s が無い" % c)

    def test_8_limits_are_written(self):
        b = sec(self.t, "## §3", "## §4")
        for s in (u"- G3 の代価: 差の主張の 1 単位の書き誤りは「違う」でなく「要確認」に出る(試作で注入の止め 165)。",
                  u"- G4 の代価: 一致の行から偶然の一致 11 を外すが、同じ形の正しい結びも外しうる(試作で列挙の 1 行を除外の規則で戻した)。",
                  u"- G1 の前置きの許す字 4 つと G4 の形は 67 書類の字で決めた。新しい標本で外れうる。",
                  u"- 数の読み取り(G5)は「人」など円以外の単位を読まない。儀式の道具は既存の読みで注入の site を作るので、円銭の 4 か所は G5 の下で表から消える(手で当てた結果を記録に)。",
                  u"- 「違う」に残る正しい文の主因(区分の取り違えの疑い 139・向きの語の残り)はこの封では直らない。"):
            self.assertIn(s, b, s)
        self.assertEqual(len(re.findall(r"(?m)^- ", b)), 5)
        # 限界の数が §0 と同じ(止め 165・一致から外れた 11・円銭 4 か所・区分の取り違え 139・許す字 4 つ)
        n = s0_numbers(s0(self.t))
        self.assertEqual((n["cost_stop"], n["g_out"], n["rit_gone"], n["same_section"]), (165, 11, 4, 139))

    def test_9_closed_file_list_and_order(self):
        b = sec(self.t, "## §4")
        first = b[:b.index(u"\n順序:")]
        self.assertTrue(first.startswith(u"\n## §4 触る file と順序"))
        pos = []
        tok = u"`adapters/xbrl/extract.py`"
        self.assertEqual(first.count(tok), 1)
        pos.append(first.index(tok))
        for rel in ENGINE_FILES[1:]:
            tok = "`%s`" % os.path.basename(rel)
            self.assertEqual(first.count(tok), 1, rel)
            pos.append(first.index(tok))
        self.assertIn(u"`report_customer.py`(理由の表の 3 行)", first)
        # comparators.py は触らない: 段 1 の file 一覧に無い(sha16 は「触らない」側 = UNTOUCHED)
        self.assertNotIn("comparators", first)
        self.assertIn("adapters/xbrl/comparators.py", UNTOUCHED)
        self.assertNotIn("adapters/xbrl/comparators.py", ENGINE_AT_SEAL)
        reg = first.index(u"→ 登録の一覧の試験に P26 →")
        for rel in (P26_UNIT_TEST,) + FILES:
            tok = "`%s`" % rel
            self.assertEqual(first.count(tok), 1, rel)
            pos.append(first.index(tok))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        self.assertEqual(len(ENGINE_FILES) + 1 + len(FILES), 10)
        self.assertTrue(pos[4] < reg < pos[5])      # 登録の一覧の試験に P26 は engine の後・test_recipes_p26.py の前
        self.assertIn(u"→ pin の遷移 → 覆い。", first)
        self.assertTrue(first.index(u"`tests/measure/test_xbrl_p26_result.py`") < first.index(u"→ pin の遷移"))
        order = b[b.index(u"\n順序:"):]
        self.assertIn(u"順序: 人間の方針(2026-10-21 朝)→ 報告形の直しの commit → **この封 + 封の門を commit** → 段 1 実装(別席)→ 凍結 → 独立監査 → commit → "
                      u"axis3 の宣言 → 新しい標本の取得(鍵)→ 判定。", order)
        # §4 が名指す file のうち既存のものは在る(登録の一覧の試験は tests/adapters/xbrl/test_vocabulary.py など)
        for rel in ENGINE_FILES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)


class EngineAtSealTest(unittest.TestCase):
    """封の commit 時点の engine を字で留め、段 1 の後は「宣言された遷移」の値だけを受け入れる(docstring)。"""

    def test_10_adapters_xbrl_file_set_is_the_16(self):
        py = sorted(f for f in os.listdir(os.path.join(ROOT, "adapters", "xbrl")) if f.endswith(".py"))
        self.assertEqual(["adapters/xbrl/" + f for f in py], sorted(list(UNTOUCHED) + list(ENGINE_AT_SEAL)), u"adapters/xbrl の file の集合が変わった")
        self.assertEqual((len(UNTOUCHED), len(ENGINE_AT_SEAL)), (11, 5))
        self.assertEqual(sorted(ENGINE_AT_SEAL), sorted(ENGINE_FILES))

    def test_11_untouched_files_keep_their_sha(self):
        """P26 が触らない adapters/xbrl 11 file(`comparators.py`・`report.py`・`verify_document.py`・`resolve.py` ほか)。宣言の遷移を持たない: 動いたら赤のまま。"""
        for rel, want in sorted(UNTOUCHED.items()):
            self.assertEqual(sha16(rel), want, u"**%s が動いている(この封は触らない)**" % rel)
        for rel in ("report", "verify_document"):
            self.assertIn("adapters/xbrl/%s.py" % rel, UNTOUCHED)

    def test_12_engine_sha_is_the_one_at_the_seal_or_a_declared_transition(self):
        for rel, want in sorted(ENGINE_AT_SEAL.items()):
            got = sha16(rel)
            if got != want and rel in ENGINE_TRANSITIONS:
                later, seal_rel = ENGINE_TRANSITIONS[rel]
                added = git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split()
                self.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている(段 1 の commit で ENGINE_TRANSITIONS に遷移を宣言する)**" % rel)

    def test_13_engine_fingerprint_is_the_one_at_the_seal_or_a_declared_transition(self):
        from adapters.xbrl import verify_document as VD
        fp = VD.engine_fingerprint()
        for k, want in sorted(FINGERPRINT_AT_SEAL.items()):
            got = fp[k]
            if got != want and k in LATER_FINGERPRINT:
                later, seal_rel = LATER_FINGERPRINT[k]
                self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(),
                                u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (k, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % k)
                continue
            self.assertEqual(got, want, u"**%s が動いている(段 1 の commit で LATER_FINGERPRINT に遷移を宣言する)**" % k)
        # 指紋が動くのは engine の file が動いたときだけ(別の file が動いていたら test_11 が赤)
        if fp["adapter_xbrl_py_sha256"] != FINGERPRINT_AT_SEAL["adapter_xbrl_py_sha256"]:
            self.assertTrue(any(sha16(rel) != want for rel, want in ENGINE_AT_SEAL.items()))
        self.assertEqual(fp["core_py_sha256"], FINGERPRINT_AT_SEAL["core_py_sha256"])

    def test_14_frozen_bundle_is_the_one_at_the_seal_or_a_declared_transition(self):
        src = text(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"))
        count = int(re.search(r"(?m)^FROZEN_COUNT = (\d+)", src).group(1))
        gens = re.findall(r'\("([0-9a-f]{64})",\n', src)
        self.assertEqual(count, FROZEN_COUNT_AT_SEAL)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py")], cwd=REPO, capture_output=True, text=True)
        out = r.stdout
        m = re.search(r"対象 (\d+) 本 @ ", out)
        self.assertIsNotNone(m, out)
        self.assertEqual(int(m.group(1)), FROZEN_COUNT_AT_SEAL)
        self.assertIn(FROZEN_BUNDLE_AT_SEAL, gens, u"封の commit 時点の世代は消さない")
        if "bundle" in LATER_FROZEN:
            later, seal_rel = LATER_FROZEN["bundle"]
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), u"遷移を宣言した封が履歴に無い")
            self.assertEqual(r.returncode, 0, out)
            self.assertIn(later, out)
            self.assertEqual(gens[-1], later)
        else:
            self.assertEqual(r.returncode, 0, u"**frozen_bundle が動いている(段 1 の commit で LATER_FROZEN に遷移を宣言する)**\n" + out)
            self.assertIn(FROZEN_BUNDLE_AT_SEAL, out)
            self.assertEqual(gens[-1], FROZEN_BUNDLE_AT_SEAL)

    def test_15_p26_flags_reasons_and_report_lines_do_not_exist_yet(self):
        """封が実装より先であること(実装前の状態)。P26 は PROFILES に無く、封が名指す旗は Profile に無く、理由 3 つは登録簿に無く、
        report_customer.py の理由の表に 3 行が無く、新しい file が作業木にも履歴にも無い。DEFAULT_PROFILE は P22。
        段 1 の commit で ENGINE_TRANSITIONS を宣言したら skip に切り替わる(順序は test_17)。"""
        if ENGINE_TRANSITIONS:
            self.skipTest(u"段 1 の後(ENGINE_TRANSITIONS が宣言されている)。順序は test_17")
        from adapters.xbrl import vocabulary as V
        from adapters.xbrl import registry_setup as RS
        self.assertNotIn("P26", V.PROFILES)
        self.assertEqual(V.DEFAULT_PROFILE, "P22")
        fields = set(f.name for f in dataclasses.fields(V.Profile))
        for flag, _typ in FLAGS:
            self.assertNotIn(flag, fields, u"封より先に旗が入っている: " + flag)
        reasons = REASONS
        for r in reasons:
            self.assertNotIn(r, RS._POINTER_NOT_FOUND_REASONS, r)
            self.assertNotIn(r, RS._UNVERIFIABLE_REASONS, r)
        self.assertEqual((len(RS._POINTER_NOT_FOUND_REASONS), len(RS._UNVERIFIABLE_REASONS)), (9, 7))   # 16(Q-7 の 16 → 19 の左)
        rc = text(os.path.join(ROOT, "adapters", "xbrl", "report_customer.py"))
        for r in reasons:
            self.assertNotIn(r, rc, u"封より先に report_customer.py に入っている: " + r)
        for rel in ENGINE_FILES[:4] + ("adapters/xbrl/comparators.py",):
            t = text(os.path.join(ROOT, rel))
            for lit in reasons + tuple(n for n, _ in FLAGS) + ("P26", "iter_numbers_2026_10_21", "rounded_diff"):
                self.assertNotIn(lit, t, u"封より先に %s に %s が入っている" % (rel, lit))
        for p in glob.glob(os.path.join(ROOT, "core", "**", "*.py"), recursive=True):
            t = text(p)
            for lit in reasons + tuple(n for n, _ in FLAGS):
                self.assertNotIn(lit, t, u"core/ の %s に %s が在る(core/ は 0 行)" % (os.path.relpath(p, ROOT), lit))
        for rel in AFTER:
            self.assertFalse(os.path.exists(os.path.join(ROOT, rel)), u"封より先に在る: " + rel)
            self.assertEqual(git("log", "--format=%H", "--", rel).stdout.strip(), "", u"封より先に履歴に現れた: " + rel)

    def test_16_every_engine_pin_gate_of_the_past_is_listed(self):
        """過去の門が engine の sha・指紋・frozen_bundle の世代を留めている所を、実物から数えて一覧(PIN_GATES_MEASURE)と突き合わせる。
        封 §4 の「pin の遷移」の一覧(司令塔が書いた)と突き合わせる。
        新しい留める門が増えたら赤(段 1 の便で直す対象が増える)。段 1 の便ではこの一覧の各 file に P26 の遷移を宣言する。"""
        defining = set()
        for p in glob.glob(os.path.join(ROOT, "tests", "measure", "*.py")):
            if p.endswith("test_xbrl_p26_seal.py") or p.endswith("test_xbrl_p26_result.py"):
                continue
            if PIN_DEF.search(text(p)):
                defining.add("tests/measure/" + os.path.basename(p))
        listed = set(PIN_GATES_MEASURE)
        self.assertEqual(len(PIN_GATES_MEASURE), len(listed))
        self.assertEqual(len(listed), 21)
        self.assertEqual(defining, listed, u"engine を留める門の一覧が違う: 足りない %s / 余り %s" % (sorted(listed - defining), sorted(defining - listed)))
        for rel in PIN_FILES_OTHER:
            self.assertTrue(re.search(r"(?m)^FROZEN_BUNDLE_GENERATIONS\b", text(os.path.join(ROOT, rel))), rel)
        # 登録の一覧・理由の数・profile の一覧・変異の予測を留める試験は、試作の差分を当てて赤になった file の名で持つ(PIN_OTHER_TESTS。実在するだけを見る)
        self.assertEqual(len(PIN_OTHER_TESTS), 12)
        for rel in PIN_OTHER_TESTS:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)
        # --- 封 §4 の pin の一覧が、いま数えた実物(defining = PIN_DEF の grep、PIN_OTHER_TESTS)と一致する
        b = sec(text(SEAL), "## §4")
        pin = b[b.index(u"pin の遷移(段 1 の同じ便で"):b.index(u"\n順序:")]
        self.assertIn(u"封の門 `tests/measure/test_xbrl_p26_seal.py` の test_16 が実物から数えて持つ", pin)
        from_seal = set()
        for name, files in SEAL_PIN_NAMES:
            self.assertIn(name, pin, name)
            from_seal.update(files.split("|"))
        self.assertEqual(from_seal, defining, u"封 §4 の一覧と実物が違う: 封にだけ %s / 実物にだけ %s" % (sorted(from_seal - defining), sorted(defining - from_seal)))
        for t in (u"- ENGINE_LATER 系 6 本: ", u"- 結果 / 封の門 8 本: ", u"- P25 の封と結果 2 本: ", u"- cd_seal の FROZEN_LATER。",
                  u"- **報告形の封と結果・報告形の直しの封と結果の 4 本**: ", u"`UNTOUCHED` で engine の file の sha を遷移の仕組みなしに留めている。"):
            self.assertIn(t, pin, t)
        self.assertEqual(6 + 8 + 2 + 1 + 4, len(defining))
        # 数えた file 数が封の本数と同じ(ENGINE_LATER 系 6・結果 / 封の門 8・P25 2・cd_seal 1・報告形 4)
        by_count = {u"ENGINE_LATER 系 6 本": 6, u"結果 / 封の門 8 本": 8, u"P25 の封と結果 2 本": 2, u"報告形の封と結果・報告形の直しの封と結果の 4 本": 4}
        sizes = dict((n, len(f.split("|"))) for n, f in SEAL_PIN_NAMES)
        self.assertEqual(sum(sizes[n] for n in ("branch_a", "role_swap", "axis3", "p20_result", "a_core_vs_grep", "pnf_diag")), by_count[u"ENGINE_LATER 系 6 本"])
        self.assertEqual(sum(sizes[n] for n in ("point_prior_result", "ritual_result", "period_bind", "rounding", "vocab")), by_count[u"結果 / 封の門 8 本"])
        self.assertEqual(sizes["lastbranch"], by_count[u"P25 の封と結果 2 本"])
        self.assertEqual(sizes[u"報告形の封と結果・報告形の直しの封と結果の 4 本"], by_count[u"報告形の封と結果・報告形の直しの封と結果の 4 本"])
        # PIN_DEF に当たらない留め
        for t in (u"`test_xbrl_verify_inventory.py` の test_9_engine_untouched", u"`fixtures/frozen_bundle_sha.py` の `FROZEN_BUNDLE_GENERATIONS` に新しい世代",
                  u"axis3 の `LATER_ENGINE_COMMITS` に段 1 の commit"):
            self.assertIn(t, pin, t)
        adapters = sorted(os.path.basename(x)[:-3] for x in PIN_OTHER_TESTS if x.startswith("tests/adapters/xbrl/"))
        self.assertEqual(len(adapters), 11)
        listed_names = [u"test_mutations", u"test_p17", u"test_p20", u"test_registry_setup", u"test_report_customer", u"test_vocabulary"]
        for nm in listed_names:
            self.assertIn(nm, pin, nm)
            self.assertIn(nm, adapters, nm)
        self.assertIn(u"test_recipes_p21〜p25", pin)
        self.assertEqual(sorted(listed_names + ["test_recipes_p%d" % i for i in range(21, 26)]), adapters)
        self.assertIn(u"- tests/adapters/xbrl の登録の一覧・profile の一覧・理由の表の試験(", pin)
        self.assertIn(u"新しい門で engine の留めを定義するときは `ENGINE_LATER` の名を使わない", pin)
        # 理由の数を字で留める門(Q-7 の 16)は報告形の封と登録簿の試験の 2 か所
        # 段 1 の実装の便(2026-10-22)で理由が 3 つ増えたので、留める数は (10, 9)・19。封の commit 時点の (9, 7)・16 は封の Q-7 の字「16 → 19」が持つ
        self.assertIn("len(RS._POINTER_NOT_FOUND_REASONS), 10)", text(os.path.join(ROOT, "tests/adapters/xbrl/test_registry_setup.py")))
        self.assertIn(u"(10, 9)", text(os.path.join(ROOT, "tests/measure/test_xbrl_customer_report_seal.py")))


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        shas = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split() if s]
        return shas[-1] if shas else None

    def test_17_the_seal_follows_the_report_fix_and_precedes_every_later_file(self):
        # 封は報告形の直しの commit(129ee9d)より後に commit される(この封は報告形の直しを監査が読んで書いた)
        self.assertEqual(git("cat-file", "-e", REPORT_FIX_COMMIT + "^{commit}").returncode, 0)
        self.assertEqual(git("merge-base", "--is-ancestor", REPORT_FIX_COMMIT, "HEAD").returncode, 0, u"報告形の直し 129ee9d が HEAD の祖先に無い")
        tracked = git("ls-files", "--error-unmatch", SEAL_REL).returncode == 0
        if not tracked:
            # 封が履歴に無い間に、後の file が履歴に現れていたら赤(順序の逆転)。何も無いことは pass と言わず skip で残す。
            for rel in AFTER:
                self.assertIsNone(self._added(rel), u"封より先に履歴に現れた: " + rel)
            for rel in ENGINE_FILES:
                self.assertEqual(git("log", "--format=%H", REPORT_FIX_COMMIT + "..HEAD", "--", rel).stdout.strip(), "", u"封より先に engine を直した: " + rel)
            self.skipTest(u"封がまだ commit されていない(後の file が履歴に無いことだけ確かめた)")
        seal = self._added(SEAL_REL)
        self.assertNotEqual(seal, REPORT_FIX_COMMIT)
        self.assertEqual(git("merge-base", "--is-ancestor", REPORT_FIX_COMMIT, seal).returncode, 0, u"封が報告形の直し 129ee9d より前にある")
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(git("merge-base", "--is-ancestor", seal, other).returncode == 0, rel)
        for rel in ENGINE_FILES:
            for c in git("log", "--format=%H", REPORT_FIX_COMMIT + "..HEAD", "--", rel).stdout.split():
                if c == seal:
                    continue
                self.assertTrue(git("merge-base", "--is-ancestor", seal, c).returncode == 0, u"封より先に engine を直した: %s @ %s" % (rel, c))


if __name__ == "__main__":
    unittest.main()
