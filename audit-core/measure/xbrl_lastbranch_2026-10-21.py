# -*- coding: utf-8 -*-
u"""最後の枝の名指しは証拠があるときだけ「違う」と言う P25 の段 1 の測定 ― 封 ``docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md`` §2(L-1〜L-9。L-9 は段 2 なので判定しない)。

    cd audit-core
    python3 measure/xbrl_lastbranch_2026-10-21.py --stage all --readings <読みの file> --run-tests   # 記録 fixtures/xbrl/lastbranch_2026-10-21.json を書く
    python3 measure/xbrl_lastbranch_2026-10-21.py --stage l1 --out <file> --docs S100YYK8              # 軽い走らせ直し(--out 必須)
    python3 measure/xbrl_lastbranch_2026-10-21.py --stage dossier --out <file>                         # 人が読むための材料(L-3 の未読の行・L-2 の残る行)

**0 USD・通信なし・鍵の値は読まない。** 書類は ``~/.cache/audit-core/edinet/*.zip`` の手元の cache だけ(無い書類は取りに行かない)。
engine(``core/``・``adapters/``)は**測る側から 1 行も変えない**(P25 は別に実装済み)。穴 B の道具・儀式・段 2 の材料は P24 の測定
(``measure/xbrl_vocab_2026-10-21.py``)と同じく ``measure/xbrl_period_bind_2026-10-20.py`` 経由で import して使う(書き直さない)。
比べる 2 つは **P24(対照。いまの既定ではない。語彙と枠の旗つき)と P25(P24 + 旗 1 つ)** で、どちらも明示して呼ぶ(既定が動いても同じ数が出る)。

  L-1  経営分析の文を持つ 67 書類の無改変を P24 と P25 で ``verify_document`` し、claim ごとに ``(state, pointers, reason, recomputed, form)`` を比べる。
       VALUE_MISMATCH の合計と、動いた行の向き・理由(全部 VALUE_MISMATCH → POINTER_NOT_FOUND ``no_same_value`` のはず)。GROUNDED・UNVERIFIABLE の数。
  L-2  最後の枝に入って証拠があり VALUE_MISMATCH に残る行の数と、その全部の人の読み(「文が本当に違う」の数)。
  L-3  段 1 で動いた行のうち、試作で読んでいない行(= 動いた行 - 試作で読んだ集合の (doc, id))の全部の人の読み。読みは ``--readings`` で渡す(門では縛れない)。
  L-4  穴 B の 485 件を P25 で通す数と、P24 の止め(VALUE_MISMATCH)のうち POINTER_NOT_FOUND(要確認)に移る数。対照: P24 の再計算が P24 の記録(``vocab_2026-10-21.json`` の W-4)に全行一致。
  L-5  儀式(同梱の 1 書類 S100Z4Q1)を P25 で: 通した数、注入の止め(VALUE_MISMATCH)のうち要確認に移る数(素の書類の動きは含めない)。対照: P24 の再計算が P24 の記録の W-5 に全行一致。
  L-6  段 2 の材料(24 行 × 8 書類 = 192 行)の Core 自身: 注入の GROUNDED と、注入の止めのうち要確認に移る数。対照: P24 の再計算が P24 の記録の補助 S2 に全行一致。
  L-7  P24 → P25 に動いた全行の文の数を 1 回に 1 件だけ変える注入(末尾の桁 ±3・10 倍)で P25 が GROUNDED にする数。
  L-8  engine の差分の行数(``git diff HEAD --numstat``)と、既存試験で赤になった試験の種類。
  L-9  段 2。この実行では判定しない。段 2 の人間に見せる数(3 つの率・「違う」が「要確認」に移る注入の数)は記録に置く。
"""
from __future__ import print_function

import argparse
import collections
import concurrent.futures
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import platform
import re
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


PB = _mod("measure/xbrl_period_bind_2026-10-20.py", "period_bind_for_lastbranch")
PP = PB.PP
RIT = PB.RIT
FP = PB.FP
OLD, NEW = "P24", "P25"
# period_bind の道具は module の OLD / NEW を呼ぶ時に読む。ここで P24(対照)/ P25 に差し替える(この script の中だけ)。
PB.OLD, PB.NEW = OLD, NEW

from adapters.xbrl import edinet as ED          # noqa: E402
from adapters.xbrl import instance as I         # noqa: E402
from adapters.xbrl import recipes as R          # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"
OUT_REL = "fixtures/xbrl/lastbranch_2026-10-21.json"
VOCAB_REL = "fixtures/xbrl/vocab_2026-10-21.json"            # 対照の P24 の記録
ROUNDING_REL = "fixtures/xbrl/rounding_2026-10-21.json"
S2_MATERIAL_REL = PB.S2_MATERIAL_REL
S2_REC_REL = PB.S2_REC_REL
PERIOD_BIND_REL = "fixtures/xbrl/period_bind_2026-10-20.json"
KEY_NAMES = PB.KEY_NAMES
pct, frac, sha_file, jload, git = PB.pct, PB.frac, PB.sha_file, PB.jload, PB.git
claim_key, view = PB.claim_key, PB.view
NSV = "no_same_value"

#: 判定の語(読み)。
READ_OK = u"正しい文"          # VALUE_MISMATCH が偽だった(名指した当期の fact が文の参照先でない、または参照先と文が帯で合う)
READ_WRONG = u"文が本当に違う"  # 名指した fact が文の参照先で、値が帯の外(VALUE_MISMATCH が正しかった = 弱めた代価)
READ_UNSURE = u"分からない"
READ_WORDS = (READ_OK, READ_WRONG, READ_UNSURE)


def kv(d):
    return dict(sorted(d.items()))


def _pairs(block):
    out = []
    for line in block.strip().splitlines():
        p = line.split()
        out.extend((p[0], x) for x in p[1:])
    return out


#: 試作で読んだ集合(封 L-3): 試作 v1 の記録 ``scratchpad/lastbranch/proto.json`` の読み 228 行 + 試作 v3 の 13 行(v1 で VALUE_MISMATCH に残った最後の枝
#: 17 行のうち、v3 でも残る 4 行を除く 13 行)の (docID, id)。司令塔の席の手元の下調べ(repo の外、正本でない)から (doc, id) を写した。
PROTO_READ_228 = """
S100YUHC N008 N013 N045 N063
S100YWGX N013 N034 N067 N083
S100YXF5 N016 N033 N046 N071
S100YXGH N004 N020 N049 N053
S100YXLE N011 N026 N053 N068
S100YXMA N018 N025 N030 N032
S100YYDI N020 N029 N088 N092
S100YYIA N035 N047 N071 N086
S100YYK8 N003 N017 N033 N049
S100YYN7 N001 N024 N069 N081
S100YYOS N017 N023 N030 N047
S100YYQX N001 N045 N060 N070
S100YYRG N004 N008 N012 N026
S100YYRV N041 N062 N090 N100
S100YYS4 N047 N049
S100YYT4 N027 N032 N043 N047
S100YYT8 N023 N042 N072 N092
S100YYUD N002 N004 N006 N008
S100YYVN N004 N021 N032 N041
S100YZ31 N002 N024 N047
S100YZ4E N007 N026 N027 N040
S100YZ7E N024 N033 N049 N061
S100YZCT N021 N047 N077 N099
S100YZEV N001 N048
S100Z0OS N011 N022 N047 N064
S100Z1WR N019 N040 N047 N057
S100Z35K N041 N050 N061 N081
S100Z37J N014 N016 N048 N063
S100Z38F N015 N019 N057 N067
S100Z39P N054 N055 N056
S100Z3BW N045 N049 N058
S100Z3CI N003 N027 N077 N084
S100Z3CO N016 N034 N035 N041
S100Z3DU N014 N015 N037 N050
S100Z3FB N015 N016 N024 N025
S100Z3H2 N048 N056 N067 N076
S100Z3HP N033
S100Z3IZ N010 N013 N019 N057
S100Z3JY N019 N027 N054 N097
S100Z3L6 N029 N034 N036
S100Z3LJ N029 N032 N058
S100Z3PS N058
S100Z3V1 N022 N027 N042
S100Z40G N049 N070 N074
S100Z40H N017 N033 N049 N075
S100Z42X N019 N020 N027 N033
S100Z433 N005
S100Z448 N024
S100Z461 N007 N009 N011
S100Z46V N005 N008 N034 N038
S100Z48T N009 N017 N043 N063
S100Z492 N008 N009 N011 N028
S100Z4B6 N011 N048 N062 N087
S100Z4DE N009 N013 N017 N059
S100Z4GF N011 N016 N032 N040
S100Z4J8 N057 N061
S100Z4LC N007 N011 N032 N061
S100Z4N9 N007 N038 N048 N102
S100Z4PA N037 N084
S100Z4R8 N016 N024 N032 N041
S100Z55N N005 N012 N018 N044
S100Z5CH N006 N020 N034 N055
S100Z5DN N034 N054 N077 N078
S100Z6XO N003 N025 N064 N075
"""
PROTO_READ_13 = """
S100YYIA N011 N015
S100YZ4E N012 N015
S100Z40G N019 N021 N023 N025
S100Z433 N024 N028 N032
S100Z448 N009 N013
"""
PROTO_SOURCES = {u"proto.json の sha256": "47e89390750a702c4782896521167835dd854065fed27b2fe6f4967584f91db8",
                 u"read/moved_reading.json(228 行の (doc, id) の元)の sha256": "34e80e6eed0b1869116c33521e43e0021d5a2a33d817a05675dae37a32888278",
                 u"out/plain.json(試作 v1 の最後の枝の VALUE_MISMATCH 17 行の元)の sha256": "1039dd189df7d29c778f343446bb9ba5387e9d9cb90490ab92dce442d53c4e0a",
                 u"out_v3/plain.json(試作 v3)の sha256": "60b793ffaae65fef72e12a89867c1d3bf365e6c577d9612d422952d5dd4be3c6",
                 u"置き場": u"司令塔の席の scratchpad/lastbranch/(repo の外)。この script は (doc, id) の一覧を字で持つ"}
PROTO_READ = sorted(set(_pairs(PROTO_READ_228)) | set(_pairs(PROTO_READ_13)))

#: 実装席が P25 を engine に入れた直後に ``tests/adapters/xbrl`` と ``tests/measure`` を走らせて赤だった既存試験(直す前の状態。2026-10-21)と、封 L-8 の種類・直し。
#: 種類は封の字「登録の一覧・旗の形・sha の留め・diff の門」のどれか。**「数 / state の門」「人間の決定の字の門」は 0**(無ければ L-8 は外れ)。
_ADP = "tests/adapters/xbrl/"
_MEA = "tests/measure/"
_SHA = u"ENGINE_LATER の遷移を P25 の段 1 の値に(測った時点の値は注記に残す)"
EXISTING_RED_BEFORE_FIX = [
    {u"試験": _ADP + "test_mutations.py::MutationTwoWayTest::test_all_mutations_match_their_prediction", u"種類": u"登録の一覧",
     u"直し": u"変異の部分木に写された test_vocabulary の登録の一覧に P25 が無く、変異が予測と逆に赤になった。test_vocabulary の一覧 2 本を直して解消(この試験自体は直していない)"},
    {u"試験": _ADP + "test_p17.py::PctToleranceTest::test_p18_is_p17_plus_the_tolerance_flag", u"種類": u"旗の形",
     u"直し": u"率の旗 pct_tolerance_from_decimals を持つ profile の一覧に P25 を足した(P25 は P24 から作る)"},
    {u"試験": _ADP + "test_p20.py::ProfileShapeTest::test_every_other_profile_keeps_the_flag_off", u"種類": u"旗の形",
     u"直し": u"除外の一覧に P25 を足した(nonconsolidated_fallback を引き継ぐ)"},
    {u"試験": _ADP + "test_recipes_p21.py::FlagShapeTest::test_only_p21_has_the_flag_on", u"種類": u"旗の形",
     u"直し": u"last_branch_cues を持つ profile の一覧を P21〜P24 から P21〜P25 に"},
    {u"試験": _ADP + "test_recipes_p22.py::FlagShapeTest::test_only_p22_has_the_flag_on", u"種類": u"旗の形",
     u"直し": u"period_bind を持つ profile の一覧を P22〜P24 から P22〜P25 に"},
    {u"試験": _ADP + "test_recipes_p22.py::WithoutCueTest::test_every_profile_before_p22_keeps_grounding_the_prior_fact", u"種類": u"旗の形",
     u"直し": u"除外を P22〜P24 から P22〜P25 に"},
    {u"試験": _ADP + "test_recipes_p23.py::FlagShapeTest::test_only_p23_has_the_new_flag_on", u"種類": u"旗の形",
     u"直し": u"truncate_abs_band を持つ profile の一覧を P23・P24 から P23〜P25 に"},
    {u"試験": _ADP + "test_recipes_p23.py::P22UnchangedTest::test_every_profile_but_p23_keeps_the_signed_band_under_truncate", u"種類": u"旗の形",
     u"直し": u"除外を P19・P23・P24 から P19・P23〜P25 に"},
    {u"試験": _ADP + "test_recipes_p24.py::FlagShapeTest::test_the_flags_are_false_by_default_and_for_every_other_profile", u"種類": u"旗の形",
     u"直し": u"P24 の旗 2 つが真の profile の一覧を P24 から P24・P25 に(P25 は P24 から作る)"},
    {u"試験": _ADP + "test_registry_setup.py::RegisterAllTest::test_register_all_registration_counts_from_registry", u"種類": u"登録の一覧",
     u"直し": u"POINTER_NOT_FOUND の理由の数を 8 から 9、登録の総数を 31 から 32 に(no_same_value を足したため)"},
    {u"試験": _ADP + "test_vocabulary.py::ProfileListPinsAreSelfCheckedTest::test_every_registry_pin_matches_the_registry", u"種類": u"登録の一覧",
     u"直し": u"この試験自体は直していない: 下の 2 本の一覧に P25 を足すと緑になる(登録表と字の一覧の食い違いを見つける守りが効いた)"},
    {u"試験": _ADP + "test_vocabulary.py::P7ProfileTest::test_p7_in_profiles_registry", u"種類": u"登録の一覧", u"直し": u"PROFILES の一覧に P25 を足した"},
    {u"試験": _ADP + "test_vocabulary.py::P12P13P14ProfileTest::test_profiles_registry_lists_every_profile", u"種類": u"登録の一覧", u"直し": u"PROFILES の一覧に P25 を足した"},
    {u"試験": _MEA + "test_xbrl_a_core_vs_grep_seal.py::FrozenTest::test_9_tools_have_not_moved", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の vocabulary.py の遷移を P25 の段 1 の値に(測った時点の値は注記に残す)"},
    {u"試験": _MEA + "test_xbrl_axis3_decision.py::Axis3Test::test_9_the_engine_was_not_touched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の vocabulary.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_branch_a.py::PredictionTest::test_14_engine_files_are_untouched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_cd_seal.py::FrozenToolsTest::test_12_engine_and_tools_have_not_moved", u"種類": u"sha の留め", u"直し": u"FROZEN_LATER の vocabulary.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_p20_result.py::DisciplineTest::test_11_engine_is_untouched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_period_bind_result.py::RecordTest::test_16_frozen_bundle_last_generation_is_the_working_tree_and_declares_step_2", u"種類": u"sha の留め",
     u"直し": u"fixtures/frozen_bundle_sha.py の FROZEN_BUNDLE_GENERATIONS に世代を 1 つ足した(門は P24 のとき直した『最新から後の封の宣言を飛ばして読む』形のまま)"},
    {u"試験": _MEA + "test_xbrl_period_bind_result.py::RecordTest::test_8_engine_is_the_one_measured_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_period_bind_seal.py::EngineAtSealTest::test_12_engine_sha_is_the_one_at_the_seal_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_pnf_diag.py::DisciplineTest::test_7_engine_files_are_untouched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_role_swap_result.py::DisciplineTest::test_11_engine_untouched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_rounding_result.py::RecordTest::test_6_engine_is_the_one_measured_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の vocabulary.py・recipes.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_rounding_result.py::MutationTest::test_baseline_is_green", u"種類": u"sha の留め", u"直し": u"上と同じ(基準線が engine_ok を呼ぶ)"},
    {u"試験": _MEA + "test_xbrl_rounding_result.py::MutationTest::test_m16_a_wrong_engine_sha_is_red", u"種類": u"sha の留め", u"直し": u"上と同じ(この変異は ENGINE_LATER を空にして確かめる形のままで、遷移の値が変わっただけ)"},
    {u"試験": _MEA + "test_xbrl_rounding_seal.py::EngineAtSealTest::test_11_engine_sha_is_the_one_at_the_seal_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の vocabulary.py・recipes.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_vocab_result.py::RecordTest::test_6_engine_is_the_one_measured_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER(空だった)に 3 file の遷移を P25 の段 1 の値で宣言"},
    {u"試験": _MEA + "test_xbrl_vocab_result.py::MutationTest::test_baseline_is_green", u"種類": u"sha の留め", u"直し": u"上と同じ(基準線が engine_ok を呼ぶ)"},
    {u"試験": _MEA + "test_xbrl_vocab_result.py::MutationTest::test_m16_a_wrong_engine_sha_is_red", u"種類": u"sha の留め",
     u"直し": u"変異『測った時点の sha を壊すと赤』が、宣言された遷移の受け入れで赤にならなくなったので、この変異の中だけ ENGINE_LATER を空にして確かめる(変異の意図は不変。rounding_result と同じ直し)"},
    {u"試験": _MEA + "test_xbrl_vocab_seal.py::EngineAtSealTest::test_13_engine_sha_is_the_one_at_the_seal_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の 3 file の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_lastbranch_seal.py::EngineAtSealTest::test_13_engine_sha_is_the_one_at_the_seal_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER(空)に 3 file の遷移を宣言(docstring のとおり)"},
    {u"試験": _MEA + "test_xbrl_point_prior_result.py::RecordTest::test_3_judgments_recomputed_equal_the_script_and_the_record", u"種類": u"diff の門", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py・registry_setup.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_point_prior_result.py::DocTest::test_6_the_document_equals_what_the_record_says", u"種類": u"diff の門", u"直し": u"上と同じ"},
    {u"試験": _MEA + "test_xbrl_point_prior_result.py::DocTest::test_7_seal_and_engine_are_untouched_since_the_seal_commit", u"種類": u"diff の門", u"直し": u"上と同じ"},
    {u"試験": _MEA + "test_xbrl_point_prior_result.py::MutationTest::test_m0_the_genuine_samples_pass", u"種類": u"diff の門", u"直し": u"上と同じ"},
    {u"試験": _MEA + "test_xbrl_ritual_result.py::PredictionTest::test_8_judgments_recomputed_equal_the_document_table", u"種類": u"diff の門", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py・registry_setup.py の遷移を P25 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_period_bind_seal.py::EngineAtSealTest::test_13_default_is_p22_from_step_2_and_p22_is_registered_with_the_flag", u"種類": u"旗の形", u"直し": u"period_bind を持つ profile の一覧を P22〜P24 から P22〜P25 に"},
    {u"試験": _MEA + "test_xbrl_rounding_seal.py::EngineAtSealTest::test_12_flags_exist_default_is_p22_and_p23_is_p22_plus_the_two_flags", u"種類": u"旗の形",
     u"直し": u"truncate_abs_band・pct_tolerance_from_decimals を持つ profile の一覧に P25 を足した"},
    {u"試験": _MEA + "test_xbrl_vocab_seal.py::EngineAtSealTest::test_14_new_flags_p24_and_other_frame_exist_now_default_is_p22", u"種類": u"旗の形", u"直し": u"旗 vocab_2026_10_21・frame_rebind が真の profile の一覧を P24 から P24・P25 に"},
    {u"試験": _MEA + "test_xbrl_vocab_seal.py::EngineAtSealTest::test_15_p23_flags_are_unchanged", u"種類": u"旗の形", u"直し": u"最後の assert『truncate_abs_band が真なのは P23・P24 だけ』は P25 = P24 + 旗 1 つが引き継ぐので成り立たない。P23〜P25 に直した(封の門の食い違い。封の字は不変)"},
    {u"試験": _MEA + "test_xbrl_lastbranch_seal.py::EngineAtSealTest::test_14_new_flag_p25_and_no_same_value_do_not_exist_yet", u"種類": u"旗の形",
     u"直し": u"docstring のとおり『まだ無い』を『在る(旗は Profile に在って既定は偽・真なのは P25 だけ・no_same_value は registry_setup.py に在る・core/ に無い)』に直した"},
]
#: 新しい試験 file(tests/adapters/xbrl/test_recipes_p25.py・tests/measure/test_xbrl_lastbranch_result.py)を足したために赤くなった覆いの門。engine とは無関係。
#: 封 §4 の順の最後の『覆い』(measure/suite_coverage_2026-10-16.py --write と 1 冊の A-06〜A-09)で直す。実際に赤だった名前は覆いの直しの前に実測して置き換える。
COVERAGE_RED_BEFORE_FIX = [
    {u"試験": _MEA + "test_facts_for_buyers.py::AssetNumbersTest::test_22_record_is_the_live_disk_count", u"直し": u"覆いの記録を測り直して 1 冊の A-06〜A-09 を直す"},
    {u"試験": _MEA + "test_suite_coverage.py::CountTest::test_1_recount_the_files_on_disk", u"直し": u"覆いの記録を測り直す(--write)"},
    {u"試験": _MEA + "test_suite_coverage.py::RecordIsStableAndReadOnlyTest::test_37_the_default_run_does_not_write_the_record", u"直し": u"覆いの記録を測り直す(--write)"},
]


def existing_red_before_fix():
    return list(EXISTING_RED_BEFORE_FIX)


# ====================================================================================================
# 道具: raw claim を拾う(engine の file は変えない。module の属性を実行中だけ差し替える)
class _RawTap(object):
    def __enter__(self):
        self.orig = (R._build_raw_num_claims, R._build_raw_text_claims, R._member_material)
        self.cur = {}
        tap = self

        def num(*a, **kw):
            out = tap.orig[0](*a, **kw)
            tap.cur["num"] = out
            return out

        def text(*a, **kw):
            out = tap.orig[1](*a, **kw)
            tap.cur["text"] = out
            return out

        def mm(zb, inst, text_, sentences, profile):
            out = tap.orig[2](zb, inst, text_, sentences, profile)
            tap.cur["sentences"] = sentences
            return out
        R._build_raw_num_claims, R._build_raw_text_claims, R._member_material = num, text, mm
        return self

    def __exit__(self, *a):
        R._build_raw_num_claims, R._build_raw_text_claims, R._member_material = self.orig
        if (R._build_raw_num_claims, R._build_raw_text_claims, R._member_material) != self.orig:
            raise SystemExit(u"**R の関数を戻せていない。止める**")


def verify_raw(tap, zb, prof, text=None):
    tap.cur.clear()
    out = VD.verify_document(zb, prof, text)
    if out["profile"] != prof:
        raise SystemExit(u"**profile が違う: %s != %s。止める**" % (out["profile"], prof))
    raw = {}
    for c in tap.cur.get("num", []) + tap.cur.get("text", []):
        raw[c["id"]] = c
    return out, raw, list(tap.cur.get("sentences", []))


# ====================================================================================================
# 人が読むための材料(dossier)。engine の関数は呼ばず、書類の fact から数え直す。
def _num_span(sent, pos):
    for x in FP.E.iter_numbers(sent):
        if x[0] == pos:
            return x[0], x[1]
    return pos, pos


def dossier(inst, raw, sent, value, unit):
    u"""名指した fact・文の値との差(主張の桁の単位)・同じ要素の当期 - 前期との差・別の要素の同じ値。**読むための材料で、判定ではない。**"""
    facts = inst["facts"]
    jpy = [f for f in facts if f["unit"] and f["unit"].upper().startswith("JPY")]
    ns = raw.get("no_same_value")
    named = ns["named"] if ns else raw.get("pointer")
    named_value = ns["value"] if ns else raw.get("recomputed")
    if not isinstance(named, str) or not named.startswith("xbrl:"):
        return {u"名指した fact": named, u"型": u"名指しなし"}
    nname, nctx = named[5:].split("@")
    scale = raw.get("claim_scale") or V.UNIT_SCALE.get(unit)
    unit_scale = raw.get("unit_scale") or (1.0 if unit == u"円" else V.UNIT_SCALE.get(unit, 1.0))
    value = value * unit_scale            # claim の value は書かれた単位の数(千円なら 千円 の数)。円に直す
    rounding = raw.get("rounding")
    mt = R._mag_trunc(V.PROFILES[NEW], rounding)
    d = {u"名指した fact": named, u"名指した値": named_value, u"文の値": value, u"主張の桁": scale}
    d[u"差(主張の桁)"] = None if (named_value is None or not scale) else round((abs(named_value) - abs(value)) / scale, 3)
    by = {(f["name"], f["context"]): f for f in jpy}
    mate = None
    if nctx.startswith("CurrentYear"):
        mate = by.get((nname, nctx.replace("CurrentYear", "Prior1Year", 1)))
    d[u"同じ要素の前期の値"] = None if mate is None else mate["value"]
    if mate is not None and scale:
        cp = named_value - mate["value"]
        d[u"当期 - 前期"] = cp
        d[u"|当期 - 前期| と文の値の差(主張の桁)"] = round((abs(cp) - abs(value)) / scale, 3)
    else:
        d[u"当期 - 前期"] = None
        d[u"|当期 - 前期| と文の値の差(主張の桁)"] = None
    others = sorted({f["name"].split(":")[-1] + "@" + f["context"] for f in jpy
                     if f["name"] != nname and scale and V.match_value(f["value"], value, scale, rounding, mt)})
    d[u"別の要素に同じ値"] = others[:6]
    d[u"別の要素に同じ値の数"] = len(others)
    sm = [f["context"] for f in jpy if f["name"] == nname and f["context"] != nctx and scale and V.match_value(f["value"], value, scale, rounding, mt)]
    d[u"同じ要素の別の context に同じ値"] = sm[:4]
    a = raw.get("pos")
    if sent and a is not None:
        a, b = _num_span(sent, a)
        d[u"増減の語"] = bool(R._MONEY_UNIT_RE_AFTER.search(sent[b:b + 4])) or bool(R._MONEY_DIFF_PHRASE_RE.search(sent[max(0, a - 25):a]))
    gap = d[u"|当期 - 前期| と文の値の差(主張の桁)"]
    if gap is not None and abs(gap) <= 2:
        d[u"型"] = u"A 同じ要素の当期 - 前期と 2 単位以内"
    elif others:
        d[u"型"] = u"B 別の要素に同じ値"
    elif mate is None:
        d[u"型"] = u"C 名指す要素に前期なし"
    else:
        d[u"型"] = u"D 同じ値なし"
    return d


# ====================================================================================================
# L-1 / L-2 / L-3(無改変 67 書類)
def plain_doc(doc_id, zb):
    u"""1 書類の無改変を P24・P25 で。(書類別の集計, 動いた行, 最後の枝に入った行, 証拠つきで残った行)を返す。"""
    inst = I.load_instance(zb)
    with _RawTap() as tap:
        a, ra, sa = verify_raw(tap, zb, OLD)
        b, rb, sb = verify_raw(tap, zb, NEW)
    if [c["id"] for c in a["claims"]] != [c["id"] for c in b["claims"]]:
        raise SystemExit(u"**claim の id の並びが P24 と P25 で違う: %s。止める**" % doc_id)
    if [(c["value"], c["span"], c["unit"]) for c in a["claims"]] != [(c["value"], c["span"], c["unit"]) for c in b["claims"]]:
        raise SystemExit(u"**claim の値・span・単位が P24 と P25 で違う: %s。止める**" % doc_id)
    moved, reached, kept = [], [], []
    for x, y in zip(a["claims"], b["claims"]):
        r = rb.get(y["id"], {})
        si = r.get("sentence")
        sent = sb[si] if (si is not None and si < len(sb)) else u""
        if "last_branch_evidence" in r:      # 最後の枝に入った(P25 の旗が真のとき、証拠の判定まで来た)行
            reached.append({u"doc": doc_id, u"id": y["id"], u"state P24": x["state"], u"state P25": y["state"], u"証拠": r.get("last_branch_evidence")})
            if y["state"] == "VALUE_MISMATCH" and r.get("last_branch_evidence"):
                kept.append({u"doc": doc_id, u"id": y["id"], u"subject": y["subject"], u"unit": y["unit"], u"value": y["value"], u"span": y["span"],
                             u"証拠": r["last_branch_evidence"], u"pointers": y["pointers"], u"recomputed": y["recomputed"], u"文": sent[:400],
                             u"dossier": dossier(inst, dict(r, pointer=(y["pointers"] or [None])[0], recomputed=y["recomputed"]), sent, y["value"], y["unit"])})
        if claim_key(x) == claim_key(y) and x["subject"] == y["subject"]:
            continue
        direction = (u"非G→G" if (x["state"] != "GROUNDED" and y["state"] == "GROUNDED") else
                     u"G→非G" if (x["state"] == "GROUNDED" and y["state"] != "GROUNDED") else
                     u"G→G" if x["state"] == "GROUNDED" else u"非G→非G")
        moved.append({u"doc": doc_id, u"id": x["id"], u"kind": y["kind"], u"subject": y["subject"], u"unit": y["unit"], u"value": y["value"],
                      u"word": y["word"], u"span": y["span"], u"向き": direction, u"P24": view(x), u"P25": view(y),
                      u"raw reason P25": r.get("reason"), u"no_same_value": r.get("no_same_value"), u"last_branch_evidence": r.get("last_branch_evidence"),
                      u"sentence": r.get("sentence"), u"pos": r.get("pos"), u"文": sent[:400],
                      u"dossier": dossier(inst, r, sent, y["value"], y["unit"])})
    per = {u"doc": doc_id, u"claims": len(a["claims"]), u"動いた": len(moved), u"最後の枝に入った": len(reached),
           u"states P24": a["document"]["states"], u"states P25": b["document"]["states"]}
    return per, moved, reached, kept


def plain_summary(rec):
    u"""L-1 の集計。**書類別と行から数える純関数**(門が記録に独立に当て直す)。"""
    mv = rec[u"動いた行"]
    docs = rec[u"書類"]
    st = lambda k, s: sum(d[k].get(s, 0) for d in docs)
    isnsv = lambda r: r[u"P24"][u"state"] == "VALUE_MISMATCH" and r[u"P25"][u"state"] == "POINTER_NOT_FOUND" and r[u"P25"][u"reason"] == NSV
    return {u"書類数": len(docs), u"総 claim": sum(d[u"claims"] for d in docs), u"動いた(全 state)": len(mv),
            u"向き(全部)": kv(collections.Counter(u"%s %s(%s) → %s(%s)" % (r[u"向き"], r[u"P24"][u"state"], r[u"P24"][u"reason"], r[u"P25"][u"state"], r[u"P25"][u"reason"]) for r in mv)),
            u"VALUE_MISMATCH → POINTER_NOT_FOUND(no_same_value)": sum(1 for r in mv if isnsv(r)),
            u"それ以外の向き": sum(1 for r in mv if not isnsv(r)),
            u"GROUNDED の合計 P24": st(u"states P24", "GROUNDED"), u"GROUNDED の合計 P25": st(u"states P25", "GROUNDED"),
            u"VALUE_MISMATCH の合計 P24": st(u"states P24", "VALUE_MISMATCH"), u"VALUE_MISMATCH の合計 P25": st(u"states P25", "VALUE_MISMATCH"),
            u"UNVERIFIABLE の合計 P24": st(u"states P24", "UNVERIFIABLE"), u"UNVERIFIABLE の合計 P25": st(u"states P25", "UNVERIFIABLE"),
            u"POINTER_NOT_FOUND の合計 P24": st(u"states P24", "POINTER_NOT_FOUND"), u"POINTER_NOT_FOUND の合計 P25": st(u"states P25", "POINTER_NOT_FOUND"),
            u"最後の枝に入った行(P25)": sum(d[u"最後の枝に入った"] for d in docs)}


# ====================================================================================================
# L-4(穴 B)
def hole_b_doc(doc_id, zb, text0):
    sites, _diag, _b, _o, sentences, _base = PP.find_sites(zb, text0)
    for s in sites:
        s[u"書類"] = doc_id
    rows_old = PB.inject_with_profile(doc_id, zb, text0, sites, sentences, OLD)
    rows_new = PB.inject_with_profile(doc_id, zb, text0, sites, sentences, NEW)
    made = [s for s in sites if s[u"作れた"]]
    if len(rows_old) != len(made) or len(rows_new) != len(made):
        raise SystemExit(u"**注入の行の数が作れた site の数と違う(%s): %d / %d / %d。止める**" % (doc_id, len(rows_old), len(rows_new), len(made)))
    by_old = dict((r[u"id"], r) for r in rows_old)
    out = []
    for r in rows_new:
        o = by_old[r[u"id"]]
        out.append({u"書類": doc_id, u"id": r[u"id"], u"要素": r[u"要素"], u"単位": r[u"単位"], u"元の字": r[u"元の字"], u"後の字": r[u"後の字"],
                    u"当期の fact": r[u"当期の fact"], u"前期の fact": r[u"前期の fact"], u"文脈 60 字": r[u"文脈 60 字"],
                    u"P24": {u"結果": o[u"結果"], u"state": o[u"結果の細目"], u"reason": o.get(u"後の reason"), u"pointers": o.get(u"後の pointers")},
                    u"P25": {u"結果": r[u"結果"], u"state": r[u"結果の細目"], u"reason": r.get(u"後の reason"), u"pointers": r.get(u"後の pointers")}})
    return out, len(sites), len(made)


def hole_b_summary(rows):
    u"""L-4 の集計(行から数える純関数)。"""
    n = len(rows)
    passed_kinds = (PP.K_MOVED, PP.K_SAME, PP.K_OTHER, PP.K_ODD)
    new = collections.Counter(r[u"P25"][u"結果"] for r in rows)
    old = collections.Counter(r[u"P24"][u"結果"] for r in rows)
    stop2conf = [r for r in rows if r[u"P24"][u"結果"] == PP.K_STOP and r[u"P25"][u"state"] == "POINTER_NOT_FOUND"]
    differ_any = [r for r in rows if r[u"P24"] != r[u"P25"]]
    return {u"注入": n,
            u"P25 の結果": kv(new), u"P24(対照)の結果": kv(old),
            u"P25 で通した(GROUNDED のまま)": frac(sum(new[k] for k in passed_kinds), n),
            u"P24(対照)で通した": frac(sum(old[k] for k in passed_kinds), n),
            u"P24 の止め": frac(old[PP.K_STOP], n),
            u"P25 で止めた(VALUE_MISMATCH)": frac(new[PP.K_STOP], n),
            u"止め(P24 の VALUE_MISMATCH)のうち要確認(POINTER_NOT_FOUND)に移る": frac(len(stop2conf), old[PP.K_STOP]),
            u"要確認に移る行": [{u"書類": r[u"書類"], u"id": r[u"id"], u"元の字": r[u"元の字"], u"後の字": r[u"後の字"], u"文脈 60 字": r[u"文脈 60 字"]} for r in stop2conf],
            u"P24 と P25 で(結果, state, reason, pointers)のどれかが違う行": len(differ_any)}


def hole_b_vs_vocab(rows):
    u"""対照の再現: P24 の記録(vocab_2026-10-21.json の W-4)の 485 行の P24 の欄と、(書類, id) ごとに 結果・state・reason・pointers が一致するか。"""
    rec = jload(VOCAB_REL)[u"W4"][u"行"]
    want = dict(((r[u"書類"], r[u"id"]), r) for r in rec)
    diff = []
    for r in rows:
        w = want.get((r[u"書類"], r[u"id"]))
        o = r[u"P24"]
        if w is None:
            diff.append({u"書類": r[u"書類"], u"id": r[u"id"]})
            continue
        wp = w[u"P24"]
        if (wp[u"結果"], wp[u"state"], wp[u"reason"], wp[u"pointers"]) != (o[u"結果"], o[u"state"], o[u"reason"], o[u"pointers"]):
            diff.append({u"書類": r[u"書類"], u"id": r[u"id"]})
    return {u"記録の行": len(want), u"今回の行": len(rows), u"記録に無い行": sum(1 for r in rows if (r[u"書類"], r[u"id"]) not in want),
            u"違った行": len(diff), u"違った行の id": diff[:20]}


# ====================================================================================================
# L-5(儀式)
def ritual(label_shas):
    zp = os.path.join(ROOT, RIT.ZIP_REL)
    with io.open(zp, "rb") as fh:
        zb = fh.read()
    if hashlib.sha256(zb).hexdigest() != RIT.ZIP_SHA256:
        raise SystemExit(u"**儀式の入力の sha256 が封の字と違う。止める**")
    old = RIT.build(zb, OLD, label_shas)
    new = RIT.build(zb, NEW, label_shas)
    rec = jload(VOCAB_REL)[u"W5"]
    key = lambda x: (x[u"id"], x[u"型"])
    by_rec = dict((key(x), x[u"P24"]) for x in rec[u"行"])
    by_old = dict((key(x), x[u"結果"]) for x in old[u"注入の一覧"])
    by_new = dict((key(x), x[u"結果"]) for x in new[u"注入の一覧"])
    rows = []
    for k in sorted(set(by_old) | set(by_new)):
        rows.append({u"id": k[0], u"型": k[1], u"P24": by_old.get(k), u"P25": by_new.get(k)})
    return {u"行": rows,
            u"通した P25 の一覧": [{u"id": x[u"id"], u"型": x[u"型"], u"元の字": x[u"元の字"], u"後の字": x[u"後の字"], u"単位": x[u"単位"],
                               u"分類": x[u"分類"], u"値の差": x[u"値の差"], u"1 最小単位": x[u"1 最小単位"], u"文脈": x[u"文脈"]} for x in new[u"通した の一覧"]],
            u"通した P25": new[u"通した"], u"止めた P25": new[u"止めた"], u"その他 P25": new[u"止めた でも 通した でもない結果"],
            u"通した P24(対照)": old[u"通した"], u"止めた P24(対照)": old[u"止めた"],
            u"通した の分け方 P25": new[u"通した の分け方"], u"型別 P25": new[u"型別"], u"型別 P24(対照)": old[u"型別"],
            u"対照: P24 の再計算が P24 の記録の W-5 と違った行": sum(1 for k in set(by_rec) | set(by_old) if by_rec.get(k) != by_old.get(k)),
            u"記録の行数": len(by_rec), u"P24 の行数": len(by_old), u"P25 の行数": len(by_new),
            u"素の書類 P25": new[u"素の書類"], u"素の書類 P24": old[u"素の書類"],
            u"注入の対象 P25": new[u"注入"][u"注入の対象(GROUNDED の site)"], u"注入の対象 P24": old[u"注入"][u"注入の対象(GROUNDED の site)"],
            u"所要秒": {u"P24": old[u"所要秒"][u"全体"], u"P25": new[u"所要秒"][u"全体"]}}


def ritual_summary(rec):
    u"""L-5 の集計(行から数える純関数)。共通の行(両方に在る)で、注入の止め(VALUE_MISMATCH)が要確認(POINTER_NOT_FOUND)に移った数。"""
    both = [r for r in rec[u"行"] if r[u"P24"] is not None and r[u"P25"] is not None]
    stop2conf = [r for r in both if r[u"P24"] == "detected:VALUE_MISMATCH" and r[u"P25"] == "detected:POINTER_NOT_FOUND"]
    passed = [r for r in rec[u"行"] if r[u"P25"] == "PASSED"]
    return {u"P25 の行": sum(1 for r in rec[u"行"] if r[u"P25"] is not None), u"P24 の行": sum(1 for r in rec[u"行"] if r[u"P24"] is not None),
            u"共通の行": len(both), u"P25 だけに在る行": sum(1 for r in rec[u"行"] if r[u"P24"] is None),
            u"P24 だけに在る行": sum(1 for r in rec[u"行"] if r[u"P25"] is None),
            u"P25 の PASSED": len(passed), u"注入の止めが要確認に移った(共通の行)": len(stop2conf),
            u"移った行の型": kv(collections.Counter(r[u"型"] for r in stop2conf)),
            u"移った行の id": [u"%s %s" % (r[u"id"], r[u"型"]) for r in stop2conf],
            u"共通の行で結果が違う行": sum(1 for r in both if r[u"P24"] != r[u"P25"]),
            u"遷移(共通の行)": kv(collections.Counter(u"%s → %s" % (r[u"P24"], r[u"P25"]) for r in both if r[u"P24"] != r[u"P25"]))}


# ====================================================================================================
# L-7(動いた全行への注入)
DIG = u"0123456789０１２３４５６７８９"


def mutate_last_digit(tok):
    for i in range(len(tok) - 1, -1, -1):
        if tok[i] in DIG:
            idx = DIG.index(tok[i])
            d, wide = idx % 10, idx >= 10
            nd = d + 3 if d + 3 <= 9 else d - 3
            return tok[:i] + DIG[nd + (10 if wide else 0)] + tok[i + 1:]
    return None


def mutate_x10(tok):
    m = re.search(u"[0-9０-９][0-9０-９,，]*", tok)
    if not m:
        return None
    g = m.group(0)
    norm = g.translate({ord(DIG[10 + i]): DIG[i] for i in range(10)}).replace(u"，", u",")
    v = int(norm.replace(u",", u"")) * 10
    new = u"{:,}".format(v) if u"," in norm else str(v)
    return tok[:m.start()] + new + tok[m.end():]


def injections_doc(doc_id, zb, text0, rows):
    u"""``rows``(この書類の P24 → P25 に動いた行)の文の数を 1 つだけ変えて、P24・P25 で再検証する(1 回に 1 件)。末尾の桁 ±3(+3 で 9 を越えるなら −3)・最上位の数の群を 10 倍。"""
    out = []
    with _RawTap() as tap:
        _o, _raw, sents0 = verify_raw(tap, zb, NEW)
        for r in rows:
            si, a = r[u"sentence"], r[u"pos"]
            sent = sents0[si]
            nums = [x for x in FP.E.iter_numbers(sent) if x[0] == a]
            if r[u"kind"] != "num" or not nums:
                out.append({u"doc": doc_id, u"id": r[u"id"], u"変え方": None, u"結果": u"数が見つからない"})
                continue
            a0, b0 = nums[0][0], nums[0][1]
            tok = sent[a0:b0]
            for how, fn in ((u"末尾の桁 ±3", mutate_last_digit), (u"10 倍", mutate_x10)):
                nt = fn(tok)
                if nt is None or nt == tok:
                    continue
                ns = sent[:a0] + nt + sent[b0:]
                nv = [x for x in FP.E.iter_numbers(ns) if x[0] == a0]
                nv = nv[0][2] if nv else None
                row = {u"doc": doc_id, u"id": r[u"id"], u"変え方": how, u"元の字": tok, u"後の字": nt, u"後の値(期待)": nv, u"文": ns[:300]}
                for prof in (OLD, NEW):
                    pos = text0.find(sent)
                    if pos < 0:
                        row[prof] = {u"結果": u"文が見つからない"}
                        continue
                    text = text0[:pos] + ns + text0[pos + len(sent):]
                    o2, raw, _s = verify_raw(tap, zb, prof, text)
                    hit = [c for c in raw.values() if c.get("sentence") == si and c.get("pos") == a]
                    if not hit:
                        row[prof] = {u"結果": u"主張が見つからない"}
                        continue
                    rc = hit[0]
                    got = {c["id"]: c for c in o2["claims"]}[rc["id"]]
                    if nv is None or got["value"] is None or abs(abs(got["value"]) - abs(nv)) > 1e-6 * max(1.0, abs(nv)):
                        row[prof] = {u"結果": u"値がずれた", u"value": got["value"]}
                        continue
                    row[prof] = {u"state": got["state"], u"reason": rc.get("reason"), u"pointers": got["pointers"], u"recomputed": got["recomputed"]}
                out.append(row)
    return out


def injection_summary(rows, n_target):
    u"""L-7 の集計(行から数える純関数)。"""
    done = [x for x in rows if x.get(u"変え方")]

    def st(x, prof):
        return x[prof].get(u"state") or x[prof].get(u"結果")
    valid = [x for x in done if x[OLD].get(u"state") is not None and x[NEW].get(u"state") is not None]
    tally = lambda prof, xs: kv(collections.Counter(u"%s:%s" % (x[u"変え方"], st(x, prof)) for x in xs))
    cnt = lambda prof, s, xs: sum(1 for x in xs if st(x, prof) == s)
    return {u"対象の行(P24 → P25 に動いた行)": n_target, u"注入の数": len(done), u"作れなかった": len(rows) - len(done), u"有効な注入": len(valid),
            u"有効でない注入(主張が見つからない・値がずれた)": len(done) - len(valid),
            u"P25 で GROUNDED(全部の注入)": cnt(NEW, "GROUNDED", done), u"P25 で GROUNDED(有効な注入)": cnt(NEW, "GROUNDED", valid),
            u"P24(対照)で GROUNDED(全部の注入)": cnt(OLD, "GROUNDED", done), u"P24(対照)で GROUNDED(有効な注入)": cnt(OLD, "GROUNDED", valid),
            u"有効な注入の P25": kv(collections.Counter(st(x, NEW) for x in valid)), u"有効な注入の P24": kv(collections.Counter(st(x, OLD) for x in valid)),
            u"集計 P25(有効)": tally(NEW, valid), u"集計 P24(有効)": tally(OLD, valid),
            u"P24 で VALUE_MISMATCH(違う)が P25 で POINTER_NOT_FOUND(要確認)に移った有効な注入": sum(1 for x in valid if st(x, OLD) == "VALUE_MISMATCH" and st(x, NEW) == "POINTER_NOT_FOUND"),
            u"P25 で GROUNDED の行": [{k: x[k] for k in (u"doc", u"id", u"変え方", u"元の字", u"後の字", u"文")} for x in done if st(x, NEW) == "GROUNDED"]}


# ====================================================================================================
# L-6(段 2 の材料)
def s2(work):
    rows = PB.e4(work)
    out = []
    for r in rows:
        out.append({u"doc": r[u"doc"], u"id": r[u"id"], u"注入か": r[u"注入か"], u"注入の型": r[u"注入の型"],
                    u"Core 自身 P24": r[u"Core 自身 P21(今回)"],       # PB.OLD = P24 なので PB の「P21(今回)」の欄は P24
                    u"Core 自身 P25": r[u"Core 自身 P22"]})
    return out


def s2_summary(rows):
    moved = [r for r in rows if r[u"Core 自身 P24"] != r[u"Core 自身 P25"]]
    inj = [r for r in rows if r[u"注入か"]]
    stop2conf = [r for r in inj if r[u"Core 自身 P24"][u"state"] == "VALUE_MISMATCH" and r[u"Core 自身 P25"][u"state"] == "POINTER_NOT_FOUND"]
    return {u"行": len(rows), u"注入": len(inj), u"無改変": len(rows) - len(inj),
            u"Core 自身が P24 → P25 で動いた行": len(moved),
            u"動いた行の id": [u"%s %s" % (r[u"doc"], r[u"id"]) for r in moved],
            u"動いた行の遷移": kv(collections.Counter(u"%s(%s) → %s" % (r[u"Core 自身 P24"][u"state"], u"注入" if r[u"注入か"] else u"無改変", r[u"Core 自身 P25"][u"state"]) for r in moved)),
            u"全注入で Core 自身 P24 が GROUNDED": frac(sum(1 for r in inj if r[u"Core 自身 P24"][u"state"] == "GROUNDED"), len(inj)),
            u"全注入で Core 自身 P25 が GROUNDED": frac(sum(1 for r in inj if r[u"Core 自身 P25"][u"state"] == "GROUNDED"), len(inj)),
            u"注入の P24 の止め(VALUE_MISMATCH)": sum(1 for r in inj if r[u"Core 自身 P24"][u"state"] == "VALUE_MISMATCH"),
            u"注入の止めのうち要確認(POINTER_NOT_FOUND)に移る": len(stop2conf),
            u"要確認に移る注入の型": kv(collections.Counter(str(r[u"注入の型"]) for r in stop2conf)),
            u"要確認に移る行の id": [u"%s %s" % (r[u"doc"], r[u"id"]) for r in stop2conf],
            u"無改変で P24 の VALUE_MISMATCH": sum(1 for r in rows if not r[u"注入か"] and r[u"Core 自身 P24"][u"state"] == "VALUE_MISMATCH"),
            u"無改変で P25 の VALUE_MISMATCH": sum(1 for r in rows if not r[u"注入か"] and r[u"Core 自身 P25"][u"state"] == "VALUE_MISMATCH")}


def s2_vs_vocab(rows):
    u"""対照の再現: P24 の記録の補助 S2(192 行)の P24 の欄と、(doc, id) ごとに一致するか。"""
    rec = jload(VOCAB_REL)[u"S2"][u"行"]
    want = dict(((r[u"doc"], r[u"id"]), r[u"Core 自身 P24"]) for r in rec)
    diff = [r for r in rows if want.get((r[u"doc"], r[u"id"])) != r[u"Core 自身 P24"]]
    return {u"記録の行": len(want), u"今回の行": len(rows), u"違った行": len(diff)}


# ====================================================================================================
# 補助: provenance(動いた行の Recipe が登録簿の理由と名指しの provenance を持つか)
def provenance_doc(doc_id, zb):
    n = collections.Counter()
    for rc in R.build_recipes(zb, V.PROFILES[NEW]):
        if rc.not_found_reason == NSV:
            n[u"no_same_value の Recipe"] += 1
            if rc.claim.provenance.get(NSV, {}).get("named"):
                n[u"provenance に名指しあり"] += 1
            if list(rc.pointers):
                n[u"pointer あり(0 のはず)"] += 1
        elif (rc.not_found_reason or "").startswith(NSV):
            n[u"理由の名が違う(0 のはず)"] += 1
        if rc.unverifiable_reason == NSV:
            n[u"UNVERIFIABLE に入った(0 のはず)"] += 1
    return dict(n)


# ====================================================================================================
def numstat():
    out = {}
    for f in ("adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py"):
        rc, o = git("diff", "--numstat", "HEAD", "--", f)
        p = o.split()
        out[f] = {u"挿入": int(p[0]), u"削除": int(p[1])} if len(p) >= 2 and p[0].isdigit() else {u"挿入": 0, u"削除": 0}
    rc, o = git("diff", "--numstat", "HEAD", "--", "core")
    rc2, st = git("status", "--porcelain", "--", "core")
    out[u"core/"] = {u"差の行数": sum(int(l.split("\t")[0]) + int(l.split("\t")[1]) for l in o.splitlines() if l.split("\t")[0].isdigit()),
                     u"status": st.strip()}
    return out


def env_block(label_shas):
    bundle, n_files = RIT.engine_bundle_sha256()
    return {u"封": SEAL, u"HEAD": RIT.git_head(), u"python": platform.python_version(),
            u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順。変更後)": bundle,
            u"engine の file 数": n_files,
            u"vocabulary.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/vocabulary.py"))[:16],
            u"comparators.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/comparators.py"))[:16],
            u"recipes.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/recipes.py"))[:16],
            u"registry_setup.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/registry_setup.py"))[:16],
            u"DEFAULT_PROFILE": V.DEFAULT_PROFILE, u"比べた profile": [OLD, NEW],
            u"鍵の名前の有無(値は読まない)": dict((k, (k in os.environ)) for k in KEY_NAMES),
            u"名前が ANTHROPIC/OPENAI/GOOGLE/GEMINI で始まる環境変数の数(値は読まない)": sum(1 for k in os.environ if k.split("_")[0] in ("ANTHROPIC", "OPENAI", "GOOGLE", "GEMINI")),
            u"ラベル 2 file の sha256(起動時に照合)": label_shas,
            u"cache": u"~/.cache/audit-core/edinet/*.zip(手元の file だけ。取りに行かない)",
            u"通信": u"この script は urllib・socket・http を import しない。adapters は urllib を import するが接続は起きない",
            u"並列": u"multiprocessing(fork)の子プロセスで、書類ごと・段ごとに走らせる(結果は書類・id の順に並べ直す)",
            u"費用": u"0 USD"}


def inputs_block(doc_ids_67, doc_ids_out, readings_path, mutations_path=None):
    d = {}
    for rel in (VOCAB_REL, ROUNDING_REL, PERIOD_BIND_REL, S2_MATERIAL_REL, S2_REC_REL):
        d[rel] = sha_file(os.path.join(ROOT, rel))
    d[u"seat answers(hybrid_s2_answers)"] = dict((fn, sha_file(os.path.join(PB.HS2.ANS_DIR, fn))) for fn in sorted(os.listdir(PB.HS2.ANS_DIR)) if fn.endswith("_answer.json"))
    d[u"儀式の同梱書類"] = sha_file(os.path.join(ROOT, RIT.ZIP_REL))
    d[u"書類 67(経営分析の文を持つ)の sha256"] = dict((x, sha_file(ED.cache_path(x))) for x in doc_ids_67 if os.path.exists(ED.cache_path(x)))
    d[u"書類 214(67 の外)の sha256 を束ねた値(path 順の 'docID\\tsha256' の行)"] = hashlib.sha256(
        u"\n".join(u"%s\t%s" % (x, sha_file(ED.cache_path(x))) for x in sorted(doc_ids_out)).encode("utf-8")).hexdigest()
    d[u"人の読みの入力 file の sha256(``--readings``。内容は記録の行に写した)"] = sha_file(readings_path) if readings_path else None
    d[u"engine の変異の表の入力 file の sha256(``--mutations``。手で走らせた表の写し)"] = sha_file(mutations_path) if mutations_path else None
    d[u"試作で読んだ集合の出どころ"] = PROTO_SOURCES
    return d


# ====================================================================================================
# 人の読み(L-2・L-3)
def attach_readings(rec, readings):
    u"""``readings`` = {"rows": {"doc:id": {"読み": 語, "根拠": 文}}, "残る": {"doc:id": {...}}} を、L-3 の未読の行と L-2 の残る行に写す。
    **行と読みは 1 対 1**(足りない・余る・語が違うは止める)。読みの中身は門で縛れない(数と行の対応だけ縛る)。"""
    unread = rec[u"L3"][u"未読の行"]
    kept = rec[u"L2"][u"残る行"]
    want_u = set(u"%s:%s" % (r[u"doc"], r[u"id"]) for r in unread)
    want_k = set(u"%s:%s" % (r[u"doc"], r[u"id"]) for r in kept)
    got_u, got_k = set(readings.get("rows", {})), set(readings.get(u"残る", {}))
    if got_u != want_u or got_k != want_k:
        raise SystemExit(u"**読みと行が 1 対 1 でない: 未読の行 %d に読み %d(足りない %d・余り %d)/ 残る行 %d に読み %d(足りない %d・余り %d)。止める**" % (
            len(want_u), len(got_u), len(want_u - got_u), len(got_u - want_u), len(want_k), len(got_k), len(want_k - got_k), len(got_k - want_k)))
    for part, rows in (("rows", unread), (u"残る", kept)):
        for r in rows:
            x = readings[part][u"%s:%s" % (r[u"doc"], r[u"id"])]
            if x[u"読み"] not in READ_WORDS or not x.get(u"根拠"):
                raise SystemExit(u"**読みの語か根拠が無い: %s %s**" % (r[u"doc"], r[u"id"]))
            r[u"読み"], r[u"根拠"] = x[u"読み"], x[u"根拠"]


def reading_summary(rows):
    u"""読みの集計(行から数える純関数)。読みが付いていない行は ``None`` として数える。"""
    c = collections.Counter(r.get(u"読み") for r in rows)
    n = len(rows)
    return {u"行": n, READ_OK: c.get(READ_OK, 0), READ_WRONG: c.get(READ_WRONG, 0), READ_UNSURE: c.get(READ_UNSURE, 0), u"未読": c.get(None, 0),
            u"文が本当に違う の率": frac(c.get(READ_WRONG, 0), n)}


def l3_block(moved_rows):
    proto = set(PROTO_READ)
    moved_keys = set((r[u"doc"], r[u"id"]) for r in moved_rows)
    unread = [r for r in moved_rows if (r[u"doc"], r[u"id"]) not in proto]
    read_before = [r for r in moved_rows if (r[u"doc"], r[u"id"]) in proto]
    return {u"試作で読んだ集合": {u"(doc, id) の数": len(proto), u"うち段 1 で動いた行": len(read_before),
                           u"うち動かなかった(P25 でも VALUE_MISMATCH に残る等)": len(proto) - len(moved_keys & proto),
                           u"一覧": [u"%s %s" % x for x in sorted(proto)]},
            u"動いた行": len(moved_rows),
            u"未読の行": [{k: r[k] for k in (u"doc", u"id", u"subject", u"unit", u"value", u"word", u"文", u"no_same_value", u"dossier")} for r in unread]}


# ====================================================================================================
def judge(rec):
    u"""封 §2 の L-1〜L-9 の機械的な判定。幅・外れ方は封の字のまま。"""
    J = {}
    if u"L1" in rec:
        s = rec[u"L1"][u"集計"]
        v25, v24 = s[u"VALUE_MISMATCH の合計 P25"], s[u"VALUE_MISMATCH の合計 P24"]
        n = s[u"VALUE_MISMATCH → POINTER_NOT_FOUND(no_same_value)"]
        parts = {u"VALUE_MISMATCH 620〜632": 620 <= v25 <= 632, u"動く行は全部 VM → PNF no_same_value": s[u"それ以外の向き"] == 0,
                 u"動いた行 570〜584": 570 <= n <= 584,
                 u"GROUNDED の数が P24 と同じ": s[u"GROUNDED の合計 P25"] == s[u"GROUNDED の合計 P24"],
                 u"UNVERIFIABLE の数が P24 と同じ": s[u"UNVERIFIABLE の合計 P25"] == s[u"UNVERIFIABLE の合計 P24"]}
        J[u"L-1"] = {u"実測": u"67 書類(実数 %d)・claim %s: VALUE_MISMATCH P24 %s → P25 %s、動いた %d 行(VM → PNF no_same_value %d・それ以外の向き %d)、GROUNDED %s → %s・UNVERIFIABLE %s → %s" % (
            s[u"書類数"], format(s[u"総 claim"], ","), format(v24, ","), format(v25, ","), s[u"動いた(全 state)"], n, s[u"それ以外の向き"],
            format(s[u"GROUNDED の合計 P24"], ","), format(s[u"GROUNDED の合計 P25"], ","), format(s[u"UNVERIFIABLE の合計 P24"], ","), format(s[u"UNVERIFIABLE の合計 P25"], ",")),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"L2" in rec:
        kept = rec[u"L2"][u"残る行"]
        rs = reading_summary(kept)
        parts = {u"残る行 4〜8": 4 <= len(kept) <= 8}
        if rs[u"未読"] == 0:
            parts[u"文が本当に違う 0〜1"] = 0 <= rs[READ_WRONG] <= 1
            word = u"当たり" if all(parts.values()) else u"外れ"
        else:
            word = u"読み待ち"
        J[u"L-2"] = {u"実測": u"最後の枝に入って証拠があり VALUE_MISMATCH に残る行 %d(証拠 %s)。読み: 正しい文 %d・文が本当に違う %d・分からない %d・未読 %d" % (
            len(kept), json.dumps(kv(collections.Counter(r[u"証拠"].split(":")[0] for r in kept)), ensure_ascii=False),
            rs[READ_OK], rs[READ_WRONG], rs[READ_UNSURE], rs[u"未読"]), u"部分の判定": parts, u"判定": word}
    if u"L3" in rec:
        un = rec[u"L3"][u"未読の行"]
        rs = reading_summary(un)
        if rs[u"未読"] == 0 and rs[u"行"] > 0:
            ok = rs[READ_WRONG] * 100.0 <= 2.0 * rs[u"行"]
            word = u"当たり" if ok else u"外れ"
            parts = {u"文が本当に違う ≤ 読んだ行の 2%": ok}
        else:
            word, parts = u"読み待ち", {}
        J[u"L-3"] = {u"実測": u"試作で読んでいない行(動いた %d - 試作で読んだ集合のうち動いた %d)%d 行の読み: 正しい文 %d・文が本当に違う %d・分からない %d・未読 %d(違う %d / %d = %s%%)" % (
            rec[u"L3"][u"動いた行"], rec[u"L3"][u"試作で読んだ集合"][u"うち段 1 で動いた行"], rs[u"行"], rs[READ_OK], rs[READ_WRONG], rs[READ_UNSURE], rs[u"未読"],
            rs[READ_WRONG], rs[u"行"], rs[u"文が本当に違う の率"][u"率"]), u"部分の判定": parts, u"判定": word}
    if u"L4" in rec:
        s = rec[u"L4"][u"集計"]
        p = s[u"P25 で通した(GROUNDED のまま)"]
        c = s[u"止め(P24 の VALUE_MISMATCH)のうち要確認(POINTER_NOT_FOUND)に移る"]
        parts = {u"穴 B を P25 で通した 0": p[u"件"] == 0, u"止め → 要確認 0〜4": 0 <= c[u"件"] <= 4}
        J[u"L-4"] = {u"実測": u"通した %d / %d・P24 の止め %d のうち要確認に移る %d(対照 P24 の通した %d)" % (
            p[u"件"], p[u"分母"], c[u"分母"], c[u"件"], s[u"P24(対照)で通した"][u"件"]), u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"L5" in rec:
        e = rec[u"L5"]
        s = e[u"集計"]
        p = e[u"通した P25"]
        parts = {u"通した 2〜3": 2 <= p[u"件"] <= 3, u"注入の止め → 要確認 26〜34": 26 <= s[u"注入の止めが要確認に移った(共通の行)"] <= 34}
        J[u"L-5"] = {u"実測": u"通した %d / %d(%s)・注入の止め(P24 の VALUE_MISMATCH)が要確認に移った %d(型 %s)。対照 P24 の通した %d / %d" % (
            p[u"件"], p[u"分母"], u"・".join(x[u"id"] for x in e[u"通した P25 の一覧"]), s[u"注入の止めが要確認に移った(共通の行)"],
            json.dumps(s[u"移った行の型"], ensure_ascii=False), e[u"通した P24(対照)"][u"件"], e[u"通した P24(対照)"][u"分母"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"L6" in rec:
        s = rec[u"L6"][u"集計"]
        g = s[u"全注入で Core 自身 P25 が GROUNDED"]
        c = s[u"注入の止めのうち要確認(POINTER_NOT_FOUND)に移る"]
        parts = {u"注入の GROUNDED 0 / 64": g[u"件"] == 0 and g[u"分母"] == 64, u"注入の止め → 要確認 0〜2": 0 <= c <= 2}
        J[u"L-6"] = {u"実測": u"注入の GROUNDED %d / %d・P24 の止め %d のうち要確認に移る %d(型 %s)・Core 自身が動いた行 %d" % (
            g[u"件"], g[u"分母"], s[u"注入の P24 の止め(VALUE_MISMATCH)"], c, json.dumps(s[u"要確認に移る注入の型"], ensure_ascii=False), s[u"Core 自身が P24 → P25 で動いた行"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"L7" in rec:
        s = rec[u"L7"][u"集計"]
        parts = {u"P25 が GROUNDED にする 0 回": s[u"P25 で GROUNDED(全部の注入)"] == 0}
        J[u"L-7"] = {u"実測": u"対象 %d 行・注入 %d 回(有効 %d)で P25 が GROUNDED %d・VALUE_MISMATCH %d・POINTER_NOT_FOUND %d(対照 P24 は GROUNDED %d)。P24 の VALUE_MISMATCH が P25 で要確認に移った有効な注入 %d" % (
            s[u"対象の行(P24 → P25 に動いた行)"], s[u"注入の数"], s[u"有効な注入"], s[u"P25 で GROUNDED(全部の注入)"],
            s[u"有効な注入の P25"].get("VALUE_MISMATCH", 0), s[u"有効な注入の P25"].get("POINTER_NOT_FOUND", 0), s[u"P24(対照)で GROUNDED(全部の注入)"],
            s[u"P24 で VALUE_MISMATCH(違う)が P25 で POINTER_NOT_FOUND(要確認)に移った有効な注入"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"L8" in rec:
        e = rec[u"L8"]
        r = e[u"engine の差分"]
        v, c, rc, rs = (r["adapters/xbrl/vocabulary.py"], r["adapters/xbrl/comparators.py"], r["adapters/xbrl/recipes.py"], r["adapters/xbrl/registry_setup.py"])
        kinds = collections.Counter(x[u"種類"] for x in e[u"既存試験の赤(直す前)"])
        allowed = (u"登録の一覧", u"旗の形", u"sha の留め", u"diff の門")
        parts = {u"recipes.py 挿入 + 削除 60〜90": 60 <= rc[u"挿入"] + rc[u"削除"] <= 90, u"recipes.py 削除 0": rc[u"削除"] == 0,
                 u"vocabulary.py ≤ 10 行": v[u"挿入"] + v[u"削除"] <= 10, u"registry_setup.py ≤ 5 行": rs[u"挿入"] + rs[u"削除"] <= 5,
                 u"comparators.py 0 行": c[u"挿入"] == 0 and c[u"削除"] == 0, u"core/ 0 行": r[u"core/"][u"差の行数"] == 0,
                 u"既存試験の赤は種類の中だけ(数 / state の門・人間の決定の字の門は 0)": all(k in allowed for k in kinds)}
        J[u"L-8"] = {u"実測": u"vocabulary.py 挿入 %d・削除 %d、recipes.py 挿入 %d・削除 %d、registry_setup.py 挿入 %d・削除 %d、comparators.py %d/%d、core/ %d 行。既存試験の赤(直す前)%d 本、種類 %s" % (
            v[u"挿入"], v[u"削除"], rc[u"挿入"], rc[u"削除"], rs[u"挿入"], rs[u"削除"], c[u"挿入"], c[u"削除"], r[u"core/"][u"差の行数"],
            len(e[u"既存試験の赤(直す前)"]), json.dumps(kv(kinds), ensure_ascii=False)),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    J[u"L-9"] = {u"実測": u"段 2(既定 P22 → P25 を P23・P24 とまとめて 1 回)は人間に 3 つの率と「違う」が「要確認」に移る注入の数を見せてから。この実行では何も変えていない(DEFAULT_PROFILE = %s)" % V.DEFAULT_PROFILE,
               u"判定": u"判定しない(段 2)"}
    return J


# ====================================================================================================
G = {}      # fork した子プロセスが読む(run() が pool を作る前に埋める)


def _t_plain(doc_id):
    zb, _text = G["texts"][doc_id]
    return doc_id, plain_doc(doc_id, zb)


def _t_hole_b(doc_id):
    zb, text = G["texts"][doc_id]
    return doc_id, hole_b_doc(doc_id, zb, text)


def _t_inj(args):
    doc_id, rows = args
    zb, text0 = G["texts"][doc_id]
    return doc_id, injections_doc(doc_id, zb, text0, rows)


def _t_prov(doc_id):
    zb, _t = G["texts"][doc_id]
    return doc_id, provenance_doc(doc_id, zb)


def _t_ritual(_):
    return "ritual", ritual(G["label_shas"])


def _t_s2(_):
    work = tempfile.mkdtemp(prefix="lastbranch_s2_", dir=os.environ.get("TMPDIR"))
    try:
        return "s2", s2(work)
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)


def run(stage, only_docs=None, readings=None, readings_path=None, mutations=None, mutations_path=None, run_tests=False, jobs=4):
    t_all = time.time()
    label_shas, why = RIT.check_labels()
    if why:
        print(RIT.label_guidance(why), file=sys.stderr)
        raise SystemExit(2)
    zips = PP.list_zips()
    texts_of, ids67, ids_out = {}, [], []
    for doc_id, path in zips:
        if only_docs and doc_id not in only_docs:
            continue
        with io.open(path, "rb") as fh:
            zb = fh.read()
        cat, _why, text = PP.classify_doc(zb)
        if cat == PP.CAT_TEXT:
            texts_of[doc_id] = (zb, text)
            ids67.append(doc_id)
        else:
            ids_out.append(doc_id)
    ids67.sort()
    G["texts"], G["label_shas"] = texts_of, label_shas
    rec = {u"step": u"**最後の枝の名指しは証拠があるときだけ「違う」と言う P25 の段 1 の測定。0 USD・通信なし・engine は測る側から 1 行も変えない**",
           u"環境": env_block(label_shas), u"書類の数": {u"経営分析の文を持つ": len(ids67), u"67 の外": len(ids_out)}}
    secs = {}
    want = lambda *names: stage in names or stage == "all"
    ctx = multiprocessing.get_context("fork")
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, jobs), mp_context=ctx) as ex:
        moved_all = []
        if want("l1"):
            t = time.time()
            res = dict(ex.map(_t_plain, ids67))
            per, moved, reached, kept = [], [], [], []
            for d in ids67:
                p, m, rc_, k = res[d]
                per.append(p)
                moved.extend(m)
                reached.extend(rc_)
                kept.extend(k)
            moved_all = moved
            rec[u"L1"] = {u"書類": per, u"動いた行": [{k: v for k, v in r.items() if k != u"dossier"} for r in moved]}
            rec[u"L1"][u"集計"] = plain_summary(rec[u"L1"])
            rec[u"L2"] = {u"最後の枝に入った行": len(reached), u"最後の枝に入った行の証拠": kv(collections.Counter(str(r[u"証拠"]).split(":")[0] for r in reached)),
                          u"残る行": kept}
            rec[u"L3"] = l3_block(moved)
            if readings:
                attach_readings(rec, readings)
            secs[u"L1 L2 L3"] = round(time.time() - t, 1)
        futs = {}
        if want("l4"):
            futs["l4"] = [ex.submit(_t_hole_b, d) for d in ids67]
        if want("l5"):
            futs["l5"] = ex.submit(_t_ritual, None)
        if want("l6"):
            futs["l6"] = ex.submit(_t_s2, None)
        if want("prov"):
            futs["prov"] = [ex.submit(_t_prov, d) for d in ids67]
        if want("l7"):
            if not moved_all:
                raise SystemExit(u"--stage l7 は単独では走らせない(動いた行が要る)。--stage all で")
            by_doc = collections.defaultdict(list)
            for r in moved_all:
                by_doc[r[u"doc"]].append(r)
            futs["l7"] = [ex.submit(_t_inj, (d, by_doc[d])) for d in sorted(by_doc)]
        if "l4" in futs:
            t = time.time()
            res = dict(f.result() for f in futs["l4"])
            rows, per = [], []
            for d in ids67:
                r, ns, nm = res[d]
                rows.extend(r)
                per.append({u"書類": d, u"site": ns, u"作れた": nm})
            rec[u"L4"] = {u"書類別": per, u"行": rows, u"集計": hole_b_summary(rows),
                          u"対照: P24 の再計算と P24 の記録": (hole_b_vs_vocab(rows) if not only_docs else None)}
            secs[u"L4"] = round(time.time() - t, 1)
        if "l5" in futs:
            t = time.time()
            e = futs["l5"].result()[1]
            rec[u"L5"] = dict(e, **{u"集計": ritual_summary(e)})
            secs[u"L5"] = round(time.time() - t, 1)
        if "l6" in futs:
            t = time.time()
            rows = futs["l6"].result()[1]
            rec[u"L6"] = {u"行": rows, u"集計": s2_summary(rows), u"対照: P24 の再計算と P24 の記録": s2_vs_vocab(rows)}
            secs[u"L6"] = round(time.time() - t, 1)
        if "prov" in futs:
            t = time.time()
            res = dict(f.result() for f in futs["prov"])
            tot = collections.Counter()
            for d in ids67:
                tot.update(res[d])
            rec[u"provenance"] = kv(dict(tot))
            secs[u"provenance"] = round(time.time() - t, 1)
        if "l7" in futs:
            t = time.time()
            res = dict(f.result() for f in futs["l7"])
            rows = []
            for d in sorted(res):
                rows.extend(res[d])
            rec[u"L7"] = {u"行": rows, u"集計": injection_summary(rows, len(moved_all))}
            secs[u"L7"] = round(time.time() - t, 1)
    if want("l8"):
        t = time.time()
        e8 = {u"engine の差分": numstat(), u"既存試験の赤(直す前)": existing_red_before_fix(),
              u"覆いの門で赤になった試験(新しい試験 file を足したため。engine と無関係)": list(COVERAGE_RED_BEFORE_FIX)}
        if run_tests:
            e8[u"既存試験"] = [PB.run_pytest("tests/adapters/xbrl")]
        rec[u"L8"] = e8
        secs[u"L8"] = round(time.time() - t, 1)
    secs[u"全体"] = round(time.time() - t_all, 1)
    rec[u"所要秒"] = secs
    rec[u"入力の sha256"] = inputs_block(ids67, ids_out, readings_path, mutations_path)
    if mutations:
        rec[u"変異(engine。手で走らせた)"] = mutations
    rec[u"予測の判定"] = judge(rec)
    rec[u"limits"] = [
        u"手元の cache の 67 書類(経営分析の文を持つ)。規則はこの 67 書類を読んで作った(試作 3 回)。無作為ではない。67 書類での違う 0 は新しい標本での違う 0 を意味しない。",
        u"新しい標本は手元に無い: 手元の cache の 67 の外 214 書類は全部 jpsps(特定有価証券)で、67 と同じ抽出は経営分析の文を取れず claim は 0(P24 の W-7 で確かめた)。",
        u"L-1・L-2・L-4〜L-7 は試作の再現で、外れるなら実装が試作と違う。本当に外れうるのは L-3(試作で読んでいない行)。",
        u"読み(L-2・L-3)は実装席の人(エージェント)の読みで、門では縛れない(数と行の対応だけ縛る)。『分からない』は『分からない』のまま数えた。",
        u"L-7 の注入は『末尾の桁 ±3・10 倍』の 2 型で、1 回に 1 件。向きの語の反転・ほかの誤りの作り方では未測定。",
        u"L-5 の儀式は同梱 1 書類(S100Z4Q1)。注入は型 V1・V2 だけ。",
        u"『違う』を『要確認』に弱める代価がある(封 §3): 増減の数・前期の数で、注入前に結んだ fact と名指す fact が別物の誤りは、どの証拠にも当たらず要確認になる。誤りを通す数は変わらない。",
        u"増減の数で、表示桁の fact の当期 - 前期と 1 単位違う正しい文は要確認になる(丸めた値の差の帯の問題。この封では直さない)。",
        u"顧客の出力(verify_document)には provenance の欄が無い。名指した当期の値を見せるのは日本語の報告形の封で決める。"]
    return rec


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=u"P25 の段 1 の測定(0 USD・通信なし)")
    ap.add_argument("--stage", choices=["l1", "l4", "l5", "l6", "l7", "prov", "l8", "dossier", "all"], default="all")
    ap.add_argument("--out", default=None, help=u"記録の出力先。--stage all の既定は " + OUT_REL)
    ap.add_argument("--docs", default=None, help=u"docID をコンマ区切りで絞る(軽い走らせ直し用)")
    ap.add_argument("--readings", default=None, help=u"人の読みの JSON(L-2・L-3 の行に写す。--stage all と l1 で使う)")
    ap.add_argument("--mutations", default=None, help=u"engine の変異(手で走らせた)の表の JSON({注記, 表}。記録に写す)")
    ap.add_argument("--jobs", type=int, default=4, help=u"並列の子プロセスの数")
    ap.add_argument("--run-tests", action="store_true", help=u"L-8 で tests/adapters/xbrl の pytest も走らせて記録する(約 30 分)")
    a = ap.parse_args(argv)
    out = a.out
    if out is None:
        if a.stage != "all" or a.docs:
            raise SystemExit(u"--stage all 以外か --docs のときは --out を渡す(正本の記録を上書きしない)")
        out = os.path.join(ROOT, OUT_REL)
    readings = None
    if a.readings:
        with io.open(a.readings, encoding="utf-8") as fh:
            readings = json.load(fh)
    mutations = None
    if a.mutations:
        with io.open(a.mutations, encoding="utf-8") as fh:
            mutations = json.load(fh)
    stage = "l1" if a.stage == "dossier" else a.stage
    rec = run(stage, set(a.docs.split(",")) if a.docs else None, readings=readings, readings_path=a.readings, mutations=mutations, mutations_path=a.mutations,
              run_tests=a.run_tests, jobs=a.jobs)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print(u"=== 最後の枝 P25 の段 1(%s → %s・手元の cache・鍵なし・0 USD)===" % (OLD, NEW))
    for k, v in sorted(rec[u"予測の判定"].items()):
        print(u"%s: %s → %s" % (k, v[u"実測"], v[u"判定"]))
    print(u"所要 %s 秒 / 記録: %s" % (json.dumps(rec[u"所要秒"], ensure_ascii=False), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
