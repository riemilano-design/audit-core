# -*- coding: utf-8 -*-
u"""語彙の登録と枠の取り直しの P24 の段 1 の測定 ― 封 ``docs/XBRL_VOCAB_SEAL_2026-10-21.md`` §2(W-1〜W-9。W-9 は段 2 なので判定しない)。

    cd audit-core
    python3 measure/xbrl_vocab_2026-10-21.py --stage all                    # 記録 fixtures/xbrl/vocab_2026-10-21.json を書く
    python3 measure/xbrl_vocab_2026-10-21.py --stage w4 --out <file> --docs S100YMFV   # 軽い走らせ直し(--out 必須)

**0 USD・通信なし・鍵の値は読まない。** 書類は ``~/.cache/audit-core/edinet/*.zip`` の手元の cache だけ(無い書類は取りに行かない)。
engine(``core/``・``adapters/``)は**測る側から 1 行も変えない**(P24 は別に実装済み)。丸めの P23 の測定
(``measure/xbrl_rounding_2026-10-21.py``)の道具の元になった期を縛る P22 の測定(``measure/xbrl_period_bind_2026-10-20.py``)の
穴 B の注入 ``inject_with_profile``・段 2 の材料 ``core_say_for``・儀式(``measure/ritual_2026-10-20.py`` の ``build``)は import して使う(書き直さない)。
比べる 2 つは **P23(対照。いまの既定ではない。丸めの帯の旗つき)と P24(P23 + 旗 2 つ)** で、どちらも明示して呼ぶ(既定が動いても同じ数が出る)。

  W-1  経営分析の文を持つ 67 書類の無改変を P23 と P24 で ``verify_document`` し、claim ごとに ``(state, pointers, reason, recomputed, form)`` を比べる。
       新 GROUNDED の数と向き、枠の取り直しが作る GROUNDED の数。
  W-2  GROUNDED → 非 GROUNDED の数、GROUNDED → GROUNDED(参照先が動いた)の数。
  W-3  VALUE_MISMATCH の合計(P23 / P24)と、VALUE_MISMATCH → UNVERIFIABLE(other_frame・ambiguous(member))の数。
  W-4  穴 B の 485 件(前期の値への置き換え)を P24 で。対照: P23 の再計算が丸めの記録(``rounding_2026-10-21.json`` の R3)の 485 行に全部一致。
  W-5  儀式(同梱の 1 書類 S100Z4Q1)を P24 で。対照: P23 の再計算が丸めの記録の R1 に全部一致。
  W-6  P23 → P24 に GROUNDED か UNVERIFIABLE へ動いた行(G → G を含む。非 G → 非 G は含めない)の文の数を 1 回に 1 件だけ変える注入
       (末尾の桁 ±3・10 倍・向きの語の反転)で P24 が GROUNDED にする数。
  W-7  新しい標本 = 手元の cache の 67 の外 214 書類。67 と同じ抽出(``verify_document`` の既定の経路)で claim が 1 以上の書類の数。10 未満なら測れない。
  W-8  engine の差分の行数(``git diff HEAD --numstat``)と、既存試験で赤になった試験の種類。
  W-9  段 2。この実行では判定しない。
  補助: 段 2 の材料(24 行 × 8 書類 = 192 行)の Core 自身の動き(封 §3: 動いた行 0 のはず)、理由 ``other_frame`` の provenance(合った枠の context)。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
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


PB = _mod("measure/xbrl_period_bind_2026-10-20.py", "period_bind_for_vocab")
PP = PB.PP
RIT = PB.RIT
FP = PB.FP
OLD, NEW = "P23", "P24"
# period_bind の道具は module の OLD / NEW を呼ぶ時に読む。ここで P23(対照)/ P24 に差し替える(この script の中だけ)。
PB.OLD, PB.NEW = OLD, NEW

from adapters.xbrl import edinet as ED          # noqa: E402
from adapters.xbrl import recipes as R          # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"
OUT_REL = "fixtures/xbrl/vocab_2026-10-21.json"
ROUNDING_REL = "fixtures/xbrl/rounding_2026-10-21.json"       # 対照の P23 の記録
S2_MATERIAL_REL = PB.S2_MATERIAL_REL
S2_REC_REL = PB.S2_REC_REL
PERIOD_BIND_REL = PB.PERIOD_BIND_REL if hasattr(PB, "PERIOD_BIND_REL") else "fixtures/xbrl/period_bind_2026-10-20.json"
KEY_NAMES = PB.KEY_NAMES
FRAME_REASONS = ("other_frame", "ambiguous(member)")
pct, frac, sha_file, jload, git = PB.pct, PB.frac, PB.sha_file, PB.jload, PB.git
claim_key, view = PB.claim_key, PB.view


def kv(d):
    return dict(sorted(d.items()))


#: 実装席が P24 を engine に入れた直後に ``tests/adapters/xbrl`` と ``tests/measure`` を走らせて赤だった既存試験(直す前の状態。
#: 2026-10-21。実装席の手元の走らせ: tests/adapters/xbrl 12 本赤・tests/measure 27 本赤)と、封 W-8 の種類・直し。
#: 種類は封の字「登録の一覧・旗の形・sha の留め・diff の門」のどれか。**「数 / state の門」「人間の決定の字の門」は 0**(無ければ W-8 は外れ)。
#: 直しは全部、一覧に P24 を足す・遷移を宣言する 1 行(既存の assert は緩めていない)。
_ADP = "tests/adapters/xbrl/"
_MEA = "tests/measure/"
EXISTING_RED_BEFORE_FIX = [
    {u"試験": _ADP + "test_mutations.py::MutationTwoWayTest::test_all_mutations_match_their_prediction", u"種類": u"登録の一覧",
     u"直し": u"変異の部分木に写された test_vocabulary の登録の一覧に P24 が無く、変異 9 本が予測と逆に赤になった。test_vocabulary の一覧 2 本を直して解消(この試験自体は直していない)"},
    {u"試験": _ADP + "test_p17.py::PctToleranceTest::test_p18_is_p17_plus_the_tolerance_flag", u"種類": u"旗の形",
     u"直し": u"率の旗 pct_tolerance_from_decimals を持つ profile の一覧に P24 を足した(P24 は P23 から作る)"},
    {u"試験": _ADP + "test_p20.py::ProfileShapeTest::test_every_other_profile_keeps_the_flag_off", u"種類": u"旗の形",
     u"直し": u"除外の一覧に P24 を足した(nonconsolidated_fallback を引き継ぐ)"},
    {u"試験": _ADP + "test_recipes_p21.py::FlagShapeTest::test_only_p21_has_the_flag_on", u"種類": u"旗の形",
     u"直し": u"last_branch_cues を持つ profile の一覧を P21・P22・P23 から P21・P22・P23・P24 に"},
    {u"試験": _ADP + "test_recipes_p22.py::FlagShapeTest::test_only_p22_has_the_flag_on", u"種類": u"旗の形",
     u"直し": u"period_bind を持つ profile の一覧を P22・P23 から P22・P23・P24 に"},
    {u"試験": _ADP + "test_recipes_p22.py::WithoutCueTest::test_every_profile_before_p22_keeps_grounding_the_prior_fact", u"種類": u"旗の形",
     u"直し": u"除外を P22・P23 から P22・P23・P24 に"},
    {u"試験": _ADP + "test_recipes_p23.py::FlagShapeTest::test_only_p23_has_the_new_flag_on", u"種類": u"旗の形",
     u"直し": u"truncate_abs_band を持つ profile の一覧を P23 から P23・P24 に"},
    {u"試験": _ADP + "test_recipes_p23.py::P22UnchangedTest::test_every_profile_but_p23_keeps_the_signed_band_under_truncate", u"種類": u"旗の形",
     u"直し": u"除外を P19・P23 から P19・P23・P24 に"},
    {u"試験": _ADP + "test_registry_setup.py::RegisterAllTest::test_register_all_registration_counts_from_registry", u"種類": u"登録の一覧",
     u"直し": u"UNVERIFIABLE の理由の数を 6 から 7、登録の総数を 30 から 31 に(other_frame を足したため)"},
    {u"試験": _ADP + "test_vocabulary.py::ProfileListPinsAreSelfCheckedTest::test_every_registry_pin_matches_the_registry", u"種類": u"登録の一覧",
     u"直し": u"この試験自体は直していない: 下の 2 本の一覧に P24 を足すと緑になる(登録表と字の一覧の食い違いを見つける守りが効いた)"},
    {u"試験": _ADP + "test_vocabulary.py::P7ProfileTest::test_p7_in_profiles_registry", u"種類": u"登録の一覧",
     u"直し": u"PROFILES の一覧に P24 を足した"},
    {u"試験": _ADP + "test_vocabulary.py::P12P13P14ProfileTest::test_profiles_registry_lists_every_profile", u"種類": u"登録の一覧",
     u"直し": u"PROFILES の一覧に P24 を足した"},
    {u"試験": _MEA + "test_xbrl_a_core_vs_grep_seal.py::FrozenTest::test_9_tools_have_not_moved", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の vocabulary.py の遷移を P24 の段 1 の値に(測った時点の値は注記に残す)"},
    {u"試験": _MEA + "test_xbrl_axis3_decision.py::Axis3Test::test_9_the_engine_was_not_touched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の vocabulary.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_branch_a.py::PredictionTest::test_14_engine_files_are_untouched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_cd_seal.py::FrozenToolsTest::test_12_engine_and_tools_have_not_moved", u"種類": u"sha の留め", u"直し": u"FROZEN_LATER の vocabulary.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_p20_result.py::DisciplineTest::test_11_engine_is_untouched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_period_bind_result.py::RecordTest::test_16_frozen_bundle_last_generation_is_the_working_tree_and_declares_step_2", u"種類": u"sha の留め",
     u"直し": u"fixtures/frozen_bundle_sha.py の FROZEN_BUNDLE_GENERATIONS に世代を 1 つ足し、門が段 2 の宣言を最新から後の封の宣言を飛ばして読むようにした"},
    {u"試験": _MEA + "test_xbrl_period_bind_result.py::RecordTest::test_8_engine_is_the_one_measured_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_period_bind_seal.py::EngineAtSealTest::test_12_engine_sha_is_the_one_at_the_seal_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_pnf_diag.py::DisciplineTest::test_7_engine_files_are_untouched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py・vocabulary.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_role_swap_result.py::DisciplineTest::test_11_engine_untouched", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER の recipes.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_rounding_result.py::RecordTest::test_6_engine_is_the_one_measured_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER(空だった)に recipes.py・vocabulary.py の遷移を P24 の段 1 の値で宣言"},
    {u"試験": _MEA + "test_xbrl_rounding_result.py::MutationTest::test_baseline_is_green", u"種類": u"sha の留め", u"直し": u"上と同じ(基準線が engine_ok を呼ぶ)"},
    {u"試験": _MEA + "test_xbrl_rounding_result.py::MutationTest::test_m16_a_wrong_engine_sha_is_red", u"種類": u"sha の留め",
     u"直し": u"変異『測った時点の sha を壊すと赤』が、宣言された遷移の受け入れで赤にならなくなったので、この変異の中だけ ENGINE_LATER を空にして確かめる(変異の意図は不変)"},
    {u"試験": _MEA + "test_xbrl_rounding_seal.py::EngineAtSealTest::test_11_engine_sha_is_the_one_at_the_seal_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER を P24 の段 1 の値に(P23 の段 1 の値は注記に残す)"},
    {u"試験": _MEA + "test_xbrl_vocab_seal.py::EngineAtSealTest::test_13_engine_sha_is_the_one_at_the_seal_or_a_declared_transition", u"種類": u"sha の留め", u"直し": u"ENGINE_LATER(空)に 3 file の遷移を宣言(docstring のとおり)"},
    {u"試験": _MEA + "test_xbrl_point_prior_result.py::RecordTest::test_3_judgments_recomputed_equal_the_script_and_the_record", u"種類": u"diff の門", u"直し": u"ENGINE_LATER に registry_setup.py を足し、recipes.py・vocabulary.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_point_prior_result.py::DocTest::test_6_the_document_equals_what_the_record_says", u"種類": u"diff の門", u"直し": u"上と同じ"},
    {u"試験": _MEA + "test_xbrl_point_prior_result.py::DocTest::test_7_seal_and_engine_are_untouched_since_the_seal_commit", u"種類": u"diff の門", u"直し": u"上と同じ"},
    {u"試験": _MEA + "test_xbrl_point_prior_result.py::MutationTest::test_m0_the_genuine_samples_pass", u"種類": u"diff の門", u"直し": u"上と同じ"},
    {u"試験": _MEA + "test_xbrl_ritual_result.py::PredictionTest::test_8_judgments_recomputed_equal_the_document_table", u"種類": u"diff の門", u"直し": u"ENGINE_LATER に registry_setup.py を足し、recipes.py・vocabulary.py の遷移を P24 の段 1 の値に"},
    {u"試験": _MEA + "test_xbrl_period_bind_seal.py::EngineAtSealTest::test_13_default_is_p22_from_step_2_and_p22_is_registered_with_the_flag", u"種類": u"旗の形", u"直し": u"period_bind を持つ profile の一覧を P22・P23 から P22・P23・P24 に"},
    {u"試験": _MEA + "test_xbrl_rounding_seal.py::EngineAtSealTest::test_12_flags_exist_default_is_p22_and_p23_is_p22_plus_the_two_flags", u"種類": u"旗の形",
     u"直し": u"truncate_abs_band・pct_tolerance_from_decimals を持つ profile の一覧に P24 を足した"},
    {u"試験": _MEA + "test_xbrl_vocab_seal.py::EngineAtSealTest::test_14_new_flags_p24_and_other_frame_do_not_exist_yet_default_is_p22", u"種類": u"旗の形",
     u"直し": u"docstring のとおり『まだ無い』を『在る(旗は Profile に在って既定は偽・真なのは P24 だけ・other_frame は registry_setup.py に在る・core/ に無い)』に直した"},
    {u"試験": _MEA + "test_xbrl_vocab_seal.py::EngineAtSealTest::test_15_p23_flags_are_unchanged", u"種類": u"旗の形",
     u"直し": u"最後の assert『truncate_abs_band が真なのは P23 だけ』は P24 = P23 + 旗 2 つが引き継ぐので成り立たない。P23・P24 に直した(封の門の食い違い。封の字は不変)"},
]
#: 新しい試験 file(tests/adapters/xbrl/test_recipes_p24.py・tests/measure/test_xbrl_vocab_result.py)を足したために赤くなった覆いの門。engine とは無関係。
#: 封 §4 の順の最後の『覆い』(measure/suite_coverage_2026-10-16.py --write と 1 冊の A-06〜A-09)で直す。
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


def frame_tag(pointers):
    xs = [p for p in pointers if p.startswith("xbrl:")]
    return sorted({R._frame_of(p[5:].split("@")[1]) or "<plain>" for p in xs})


# ====================================================================================================
# W-1 / W-2 / W-3
def plain(tap, doc_ids, texts_of):
    per_doc, moved = [], []
    missing = []
    for d in doc_ids:
        zb = texts_of[d][0]
        a, ra, sa = verify_raw(tap, zb, OLD)
        b, rb, sb = verify_raw(tap, zb, NEW)
        if [c["id"] for c in a["claims"]] != [c["id"] for c in b["claims"]]:
            raise SystemExit(u"**claim の id の並びが P23 と P24 で違う: %s。止める**" % d)
        if [(c["value"], c["span"], c["unit"]) for c in a["claims"]] != [(c["value"], c["span"], c["unit"]) for c in b["claims"]]:
            raise SystemExit(u"**claim の値・span・単位が P23 と P24 で違う: %s。止める**" % d)
        n_moved = 0
        for x, y in zip(a["claims"], b["claims"]):
            if claim_key(x) == claim_key(y) and x["subject"] == y["subject"]:
                continue
            n_moved += 1
            r = rb.get(y["id"], {})
            si = r.get("sentence")
            sent = sb[si] if (si is not None and si < len(sb)) else u""
            if x["state"] != "GROUNDED" and y["state"] == "GROUNDED":
                direction = u"非G→G"
            elif x["state"] == "GROUNDED" and y["state"] != "GROUNDED":
                direction = u"G→非G"
            elif x["state"] == "GROUNDED":
                direction = u"G→G"
            else:
                direction = u"非G→非G"
            if r.get("frame_rebind"):
                kind = u"枠の取り直し"
            elif r.get("cf_total_sign"):
                kind = u"語彙(CF 合計の符号)"
            elif x["subject"] != y["subject"]:
                kind = u"語彙(主語の句)"
            else:
                kind = u"語彙(手がかり語・ポイントの語)"
            moved.append({u"doc": d, u"id": x["id"], u"kind": y["kind"], u"subject P23": x["subject"], u"subject P24": y["subject"],
                          u"unit": y["unit"], u"value": y["value"], u"word": y["word"], u"span": y["span"],
                          u"向き": direction, u"型": kind,
                          u"P23": view(x), u"P24": view(y),
                          u"枠 P23": frame_tag(x["pointers"]), u"枠 P24": frame_tag(y["pointers"]),
                          u"raw reason P24": r.get("reason"), u"other_frame": r.get("other_frame"), u"frame_rebind": r.get("frame_rebind"),
                          u"cf_total_sign": r.get("cf_total_sign"), u"sentence": r.get("sentence"), u"pos": r.get("pos"), u"raw word": r.get("word"),
                          u"文": sent[:400]})
        per_doc.append({u"doc": d, u"claims": len(a["claims"]), u"動いた": n_moved,
                        u"states P23": a["document"]["states"], u"states P24": b["document"]["states"]})
    return {u"書類": per_doc, u"動いた行": moved, u"キャッシュに無い書類": missing, u"総 claim": sum(p[u"claims"] for p in per_doc)}


def plain_summary(rec):
    u"""W-1〜W-3 の集計。**書類別と動いた行から数える純関数**(門が記録に独立に当て直す)。"""
    mv = rec[u"動いた行"]
    docs = rec[u"書類"]
    n2g = [r for r in mv if r[u"P23"][u"state"] != "GROUNDED" and r[u"P24"][u"state"] == "GROUNDED"]
    g2n = [r for r in mv if r[u"P23"][u"state"] == "GROUNDED" and r[u"P24"][u"state"] != "GROUNDED"]
    g2g = [r for r in mv if r[u"P23"][u"state"] == "GROUNDED" and r[u"P24"][u"state"] == "GROUNDED"]
    vm2unv = [r for r in mv if r[u"P23"][u"state"] == "VALUE_MISMATCH" and r[u"P24"][u"state"] == "UNVERIFIABLE"]
    frame_vm2unv = [r for r in vm2unv if r[u"P24"][u"reason"] in FRAME_REASONS]
    vm = lambda k: sum(d[k].get("VALUE_MISMATCH", 0) for d in docs)
    gr = lambda k: sum(d[k].get("GROUNDED", 0) for d in docs)
    st = lambda k, s: sum(d[k].get(s, 0) for d in docs)
    to_g_or_unv = [r for r in mv if r[u"P24"][u"state"] in ("GROUNDED", "UNVERIFIABLE") and
                   not (r[u"P23"][u"state"] == "UNVERIFIABLE" and r[u"P24"][u"state"] == "UNVERIFIABLE")]
    return {u"書類数": len(docs), u"総 claim": rec[u"総 claim"], u"動いた(全 state)": len(mv),
            u"GROUNDED でない → GROUNDED(新 GROUNDED)": len(n2g),
            u"新 GROUNDED の型": kv(collections.Counter(r[u"型"] for r in n2g)),
            u"新 GROUNDED の前の state": kv(collections.Counter(u"%s(%s)" % (r[u"P23"][u"state"], r[u"P23"][u"reason"]) for r in n2g)),
            u"新 GROUNDED の書類数": len({r[u"doc"] for r in n2g}),
            u"枠の取り直しが作る GROUNDED": sum(1 for r in n2g if r[u"型"] == u"枠の取り直し"),
            u"GROUNDED → GROUNDED でない": len(g2n),
            u"GROUNDED → GROUNDED(参照先が動いた)": len(g2g),
            u"VALUE_MISMATCH → UNVERIFIABLE(全部)": len(vm2unv),
            u"VALUE_MISMATCH → UNVERIFIABLE(other_frame・ambiguous(member))": len(frame_vm2unv),
            u"うち other_frame": sum(1 for r in frame_vm2unv if r[u"P24"][u"reason"] == "other_frame"),
            u"うち ambiguous(member)": sum(1 for r in frame_vm2unv if r[u"P24"][u"reason"] == "ambiguous(member)"),
            u"新しい VALUE_MISMATCH(P23 が VALUE_MISMATCH でない)": sum(1 for r in mv if r[u"P23"][u"state"] != "VALUE_MISMATCH" and r[u"P24"][u"state"] == "VALUE_MISMATCH"),
            u"向き(全部)": kv(collections.Counter(u"%s %s → %s" % (r[u"向き"], r[u"P23"][u"state"], r[u"P24"][u"state"]) for r in mv)),
            u"GROUNDED の合計 P23": gr(u"states P23"), u"GROUNDED の合計 P24": gr(u"states P24"),
            u"VALUE_MISMATCH の合計 P23": vm(u"states P23"), u"VALUE_MISMATCH の合計 P24": vm(u"states P24"),
            u"UNVERIFIABLE の合計 P23": st(u"states P23", "UNVERIFIABLE"), u"UNVERIFIABLE の合計 P24": st(u"states P24", "UNVERIFIABLE"),
            u"POINTER_NOT_FOUND の合計 P23": st(u"states P23", "POINTER_NOT_FOUND"), u"POINTER_NOT_FOUND の合計 P24": st(u"states P24", "POINTER_NOT_FOUND"),
            u"W-6 の対象(GROUNDED か UNVERIFIABLE へ動いた行。UNVERIFIABLE のまま動いた行は含めない)": len(to_g_or_unv)}


# ====================================================================================================
# W-4
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
                    u"P23": {u"結果": o[u"結果"], u"state": o[u"結果の細目"], u"reason": o.get(u"後の reason"), u"pointers": o.get(u"後の pointers")},
                    u"P24": {u"結果": r[u"結果"], u"state": r[u"結果の細目"], u"reason": r.get(u"後の reason"), u"pointers": r.get(u"後の pointers")}})
    return out, len(sites), len(made)


def hole_b_summary(rows):
    u"""W-4 の集計(行から数える純関数)。"""
    n = len(rows)
    passed_kinds = (PP.K_MOVED, PP.K_SAME, PP.K_OTHER, PP.K_ODD)
    new = collections.Counter(r[u"P24"][u"結果"] for r in rows)
    old = collections.Counter(r[u"P23"][u"結果"] for r in rows)
    differ_state = [r for r in rows if (r[u"P23"][u"結果"], r[u"P23"][u"state"]) != (r[u"P24"][u"結果"], r[u"P24"][u"state"])]
    differ_any = [r for r in rows if r[u"P23"] != r[u"P24"]]
    return {u"注入": n,
            u"P24 の結果": kv(new), u"P23(対照)の結果": kv(old),
            u"P24 で通した(GROUNDED のまま)": frac(sum(new[k] for k in passed_kinds), n),
            u"P23(対照)で通した": frac(sum(old[k] for k in passed_kinds), n),
            u"P24 で止めた(VALUE_MISMATCH)": frac(new[PP.K_STOP], n),
            u"P24 でその他": frac(new[PP.K_ELSE], n),
            u"P23 と P24 で(結果, state)が違う行": len(differ_state),
            u"P23 と P24 で(結果, state, reason, pointers)のどれかが違う行": len(differ_any),
            u"違う行": [{u"書類": r[u"書類"], u"id": r[u"id"], u"P23": r[u"P23"], u"P24": r[u"P24"]} for r in differ_any]}


def hole_b_vs_rounding(rows):
    u"""対照の再現: 丸めの記録の R3(485 行)の P23 の欄と、(書類, id) ごとに 結果・state・reason・pointers が一致するか。"""
    rec = jload(ROUNDING_REL)[u"R3"][u"行"]
    want = dict(((r[u"書類"], r[u"id"]), r) for r in rec)
    diff = []
    for r in rows:
        w = want.get((r[u"書類"], r[u"id"]))
        o = r[u"P23"]
        if w is None:
            diff.append({u"書類": r[u"書類"], u"id": r[u"id"]})
            continue
        wp = w[u"P23"]
        if (wp[u"結果"], wp[u"state"], wp[u"reason"], wp[u"pointers"]) != (o[u"結果"], o[u"state"], o[u"reason"], o[u"pointers"]):
            diff.append({u"書類": r[u"書類"], u"id": r[u"id"]})
    return {u"記録の行": len(want), u"今回の行": len(rows), u"記録に無い行": sum(1 for r in rows if (r[u"書類"], r[u"id"]) not in want),
            u"違った行": len(diff), u"違った行の id": diff[:20]}


# ====================================================================================================
# W-5
def ritual(label_shas):
    zp = os.path.join(ROOT, RIT.ZIP_REL)
    with io.open(zp, "rb") as fh:
        zb = fh.read()
    if hashlib.sha256(zb).hexdigest() != RIT.ZIP_SHA256:
        raise SystemExit(u"**儀式の入力の sha256 が封の字と違う。止める**")
    old = RIT.build(zb, OLD, label_shas)
    new = RIT.build(zb, NEW, label_shas)
    rec = jload(ROUNDING_REL)[u"R1"]
    key = lambda x: (x[u"id"], x[u"型"])
    by_rec = dict((key(x), x[u"P23"]) for x in rec[u"行"])
    by_old = dict((key(x), x[u"結果"]) for x in old[u"注入の一覧"])
    by_new = dict((key(x), x[u"結果"]) for x in new[u"注入の一覧"])
    rows = []
    for k in sorted(set(by_old) | set(by_new)):
        rows.append({u"id": k[0], u"型": k[1], u"P23": by_old.get(k), u"P24": by_new.get(k)})
    return {u"行": rows,
            u"通した P24 の一覧": [{u"id": x[u"id"], u"型": x[u"型"], u"元の字": x[u"元の字"], u"後の字": x[u"後の字"], u"単位": x[u"単位"],
                               u"分類": x[u"分類"], u"値の差": x[u"値の差"], u"1 最小単位": x[u"1 最小単位"], u"文脈": x[u"文脈"]} for x in new[u"通した の一覧"]],
            u"通した P24": new[u"通した"], u"止めた P24": new[u"止めた"], u"その他 P24": new[u"止めた でも 通した でもない結果"],
            u"通した P23(対照)": old[u"通した"], u"止めた P23(対照)": old[u"止めた"],
            u"通した の分け方 P24": new[u"通した の分け方"], u"型別 P24": new[u"型別"], u"型別 P23(対照)": old[u"型別"],
            u"対照: P23 の再計算が丸めの記録の R1 と違った行": sum(1 for k in set(by_rec) | set(by_old) if by_rec.get(k) != by_old.get(k)),
            u"記録の行数": len(by_rec), u"P23 の行数": len(by_old), u"P24 の行数": len(by_new),
            u"素の書類 P24": new[u"素の書類"], u"素の書類 P23": old[u"素の書類"],
            u"注入の対象 P24": new[u"注入"][u"注入の対象(GROUNDED の site)"], u"注入の対象 P23": old[u"注入"][u"注入の対象(GROUNDED の site)"],
            u"所要秒": {u"P23": old[u"所要秒"][u"全体"], u"P24": new[u"所要秒"][u"全体"]}}


def ritual_summary(rec):
    u"""W-5 の集計(行から数える純関数)。共通の行(両方に在る)で VM → UNVERIFIABLE に移った数。"""
    both = [r for r in rec[u"行"] if r[u"P23"] is not None and r[u"P24"] is not None]
    vm2unv = [r for r in both if r[u"P23"] == "detected:VALUE_MISMATCH" and r[u"P24"] == "detected:UNVERIFIABLE"]
    passed = [r for r in rec[u"行"] if r[u"P24"] == "PASSED"]
    return {u"P24 の行": sum(1 for r in rec[u"行"] if r[u"P24"] is not None), u"P23 の行": sum(1 for r in rec[u"行"] if r[u"P23"] is not None),
            u"共通の行": len(both), u"P24 だけに在る行": sum(1 for r in rec[u"行"] if r[u"P23"] is None),
            u"P23 だけに在る行": sum(1 for r in rec[u"行"] if r[u"P24"] is None),
            u"P24 の PASSED": len(passed), u"VALUE_MISMATCH → UNVERIFIABLE に移った(共通の行)": len(vm2unv),
            u"移った行の id": [u"%s %s" % (r[u"id"], r[u"型"]) for r in vm2unv],
            u"共通の行で結果が違う行": sum(1 for r in both if r[u"P23"] != r[u"P24"]),
            u"遷移(共通の行)": kv(collections.Counter(u"%s → %s" % (r[u"P23"], r[u"P24"]) for r in both if r[u"P23"] != r[u"P24"]))}


# ====================================================================================================
# W-6
FLIP = {u"増加": u"減少", u"減少": u"増加", u"増収": u"減収", u"減収": u"増収", u"増益": u"減益", u"減益": u"増益",
        u"上回": u"下回", u"下回": u"上回", u"改善": u"悪化", u"悪化": u"改善", u"拡大": u"縮小", u"縮小": u"拡大",
        u"増え": u"減り", u"減り": u"増え", u"増大": u"縮小", u"伸び": u"減り", u"低下": u"上回"}
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


def injections(tap, moved_rows, texts_of, progress=None):
    u"""P23 → P24 に GROUNDED か UNVERIFIABLE へ動いた行(``moved_rows``)の文の数を 1 つだけ変えて、P23・P24 で再検証する(1 回に 1 件)。
    数の主張: 末尾の桁 ±3(+3 で 9 を越えるなら −3)・最上位の数の群を 10 倍。文字の主張: 向きの語を反対の語に。"""
    rows = []
    by_doc = collections.defaultdict(list)
    for r in moved_rows:
        by_doc[r[u"doc"]].append(r)
    for doc_id in sorted(by_doc):
        zb, text0 = texts_of[doc_id]
        _o, _raw, sents0 = verify_raw(tap, zb, NEW)
        for r in by_doc[doc_id]:
            si, a = r[u"sentence"], r[u"pos"]
            sent = sents0[si]
            variants = []
            if r[u"kind"] == "num":
                nums = [x for x in FP.E.iter_numbers(sent) if x[0] == a]
                if not nums:
                    rows.append({u"doc": doc_id, u"id": r[u"id"], u"変え方": None, u"結果": u"数が見つからない"})
                    continue
                a0, b0 = nums[0][0], nums[0][1]
                tok = sent[a0:b0]
                for how, fn in ((u"末尾の桁 ±3", mutate_last_digit), (u"10 倍", mutate_x10)):
                    nt = fn(tok)
                    if nt is None or nt == tok:
                        continue
                    ns = sent[:a0] + nt + sent[b0:]
                    nv = [x for x in FP.E.iter_numbers(ns) if x[0] == a0]
                    variants.append((how, tok, nt, ns, nv[0][2] if nv else None))
            else:
                w = r[u"raw word"]
                if w in FLIP and sent[a:a + len(w)] == w:
                    nt = FLIP[w]
                    variants.append((u"向きの語を反対に", w, nt, sent[:a] + nt + sent[a + len(w):], None))
                else:
                    rows.append({u"doc": doc_id, u"id": r[u"id"], u"変え方": None, u"結果": u"反対の語なし(%s)" % w})
                    continue
            for how, tok, nt, ns, nv in variants:
                row = {u"doc": doc_id, u"id": r[u"id"], u"kind": r[u"kind"], u"型": r[u"型"], u"P24 の無改変の state": r[u"P24"][u"state"],
                       u"P24 の無改変の reason": r[u"raw reason P24"] or r[u"P24"][u"reason"], u"変え方": how, u"元の字": tok, u"後の字": nt,
                       u"後の値(期待)": nv, u"文": ns[:300]}
                for prof in (OLD, NEW):
                    pos = text0.find(sent)
                    if pos < 0:
                        row[prof] = {u"結果": u"文が見つからない"}
                        continue
                    text = text0[:pos] + ns + text0[pos + len(sent):]
                    out, raw, _s = verify_raw(tap, zb, prof, text)
                    hit = [c for c in raw.values() if c.get("sentence") == si and c.get("pos") == a
                           and (r[u"kind"] != "text" or c.get("word") == nt)]
                    if not hit:
                        row[prof] = {u"結果": u"主張が見つからない"}
                        continue
                    rc = hit[0]
                    got = {c["id"]: c for c in out["claims"]}[rc["id"]]
                    if r[u"kind"] == "num" and (nv is None or got["value"] is None or abs(abs(got["value"]) - abs(nv)) > 1e-6 * max(1.0, abs(nv))):
                        row[prof] = {u"結果": u"値がずれた", u"value": got["value"]}
                        continue
                    row[prof] = {u"state": got["state"], u"reason": rc.get("reason"), u"pointers": got["pointers"], u"recomputed": got["recomputed"]}
                rows.append(row)
        if progress:
            progress(u"W-6 %s 対象 %d" % (doc_id, len(by_doc[doc_id])))
    return rows


def injection_summary(rows, n_target):
    u"""W-6 の集計(行から数える純関数)。"""
    done = [x for x in rows if x.get(u"変え方")]

    def st(x, prof):
        return x[prof].get(u"state") or x[prof].get(u"結果")
    tally = lambda prof: kv(collections.Counter(u"%s:%s" % (x[u"変え方"], st(x, prof)) for x in done))
    return {u"対象の行(GROUNDED か UNVERIFIABLE へ動いた行)": n_target, u"注入の数": len(done),
            u"作れなかった": len(rows) - len(done),
            u"P24 で GROUNDED": sum(1 for x in done if st(x, NEW) == "GROUNDED"),
            u"P24 で UNVERIFIABLE": sum(1 for x in done if st(x, NEW) == "UNVERIFIABLE"),
            u"P24 で VALUE_MISMATCH": sum(1 for x in done if st(x, NEW) == "VALUE_MISMATCH"),
            u"P24 でその他": sum(1 for x in done if st(x, NEW) not in ("GROUNDED", "UNVERIFIABLE", "VALUE_MISMATCH")),
            u"P23(対照)で GROUNDED": sum(1 for x in done if st(x, OLD) == "GROUNDED"),
            u"P23(対照)で UNVERIFIABLE": sum(1 for x in done if st(x, OLD) == "UNVERIFIABLE"),
            u"集計 P24": tally(NEW), u"集計 P23": tally(OLD),
            u"P24 で GROUNDED の行": [{k: x[k] for k in (u"doc", u"id", u"変え方", u"元の字", u"後の字", u"文")} for x in done if st(x, NEW) == "GROUNDED"],
            u"P24 で UNVERIFIABLE の行": [{u"doc": x[u"doc"], u"id": x[u"id"], u"変え方": x[u"変え方"], u"元の字": x[u"元の字"], u"後の字": x[u"後の字"],
                                      u"reason": x[NEW].get(u"reason"), u"文": x[u"文"]} for x in done if st(x, NEW) == "UNVERIFIABLE"]}


# ====================================================================================================
# W-7
def new_sample(tap, doc_ids_67):
    u"""手元の cache の 67 の外の書類。67 と同じ抽出(``verify_document`` の既定の経路。経営分析の文を取れなければ claim 0)を P23・P24 でかける。"""
    rows = []
    for doc_id, path in PP.list_zips():
        if doc_id in doc_ids_67:
            continue
        with io.open(path, "rb") as fh:
            zb = fh.read()
        cat, why, _text = PP.classify_doc(zb)
        a, ra, sa = verify_raw(tap, zb, OLD)
        b, rb, sb = verify_raw(tap, zb, NEW)
        moved = []
        for x, y in zip(a["claims"], b["claims"]):
            if claim_key(x) == claim_key(y) and x["subject"] == y["subject"]:
                continue
            r = rb.get(y["id"], {})
            si = r.get("sentence")
            moved.append({u"id": x["id"], u"subject P24": y["subject"], u"unit": y["unit"], u"value": y["value"], u"span": y["span"],
                          u"P23": view(x), u"P24": view(y), u"other_frame": r.get("other_frame"),
                          u"文": (sb[si][:400] if (si is not None and si < len(sb)) else u""),
                          u"読み": None})
        rows.append({u"doc": doc_id, u"区分": cat, u"理由": why, u"種別": PP.kind_of(zb), u"sha256": hashlib.sha256(zb).hexdigest(),
                     u"claims P23": len(a["claims"]), u"claims P24": len(b["claims"]), u"動いた行": moved})
    return rows


def new_sample_summary(rows):
    u"""W-7 の集計(行から数える純関数)。"""
    with_claims = [r for r in rows if r[u"claims P23"] >= 1]
    moved = [m for r in rows for m in r[u"動いた行"]]
    new_g = [m for m in moved if m[u"P23"][u"state"] != "GROUNDED" and m[u"P24"][u"state"] == "GROUNDED"]
    vm2unv = [m for m in moved if m[u"P23"][u"state"] == "VALUE_MISMATCH" and m[u"P24"][u"state"] == "UNVERIFIABLE"]
    return {u"67 の外の書類": len(rows), u"区分": kv(collections.Counter(r[u"区分"] for r in rows)),
            u"種別": kv(collections.Counter(str(r[u"種別"]) for r in rows)),
            u"claim が 1 以上の書類(P23)": len(with_claims), u"claim が 1 以上の書類(P24)": sum(1 for r in rows if r[u"claims P24"] >= 1),
            u"claim の合計(P23)": sum(r[u"claims P23"] for r in rows), u"claim の合計(P24)": sum(r[u"claims P24"] for r in rows),
            u"動いた行": len(moved), u"新 GROUNDED": len(new_g), u"VALUE_MISMATCH → UNVERIFIABLE": len(vm2unv),
            u"測れるか(claim が 1 以上の書類が 10 以上)": len(with_claims) >= 10}


# ====================================================================================================
# 補助: 段 2 の材料 / provenance
def s2(work):
    rows = PB.e4(work)
    out = []
    for r in rows:
        out.append({u"doc": r[u"doc"], u"id": r[u"id"], u"注入か": r[u"注入か"], u"注入の型": r[u"注入の型"],
                    u"Core 自身 P23": r[u"Core 自身 P21(今回)"],       # PB.OLD = P23 なので PB の「P21(今回)」の欄は P23
                    u"Core 自身 P24": r[u"Core 自身 P22"]})
    return out


def s2_summary(rows):
    moved = [r for r in rows if r[u"Core 自身 P23"] != r[u"Core 自身 P24"]]
    inj = [r for r in rows if r[u"注入か"]]
    return {u"行": len(rows), u"注入": len(inj), u"Core 自身が P23 → P24 で動いた行": len(moved),
            u"動いた行の id": [u"%s %s" % (r[u"doc"], r[u"id"]) for r in moved],
            u"全注入で Core 自身 P23 が GROUNDED": frac(sum(1 for r in inj if r[u"Core 自身 P23"][u"state"] == "GROUNDED"), len(inj)),
            u"全注入で Core 自身 P24 が GROUNDED": frac(sum(1 for r in inj if r[u"Core 自身 P24"][u"state"] == "GROUNDED"), len(inj))}


def provenance_check(doc_ids, texts_of):
    u"""理由 ``other_frame`` の Recipe が、合った枠の context を provenance に持つか(登録簿の理由の名は context を含まない ``other_frame``)。"""
    n = collections.Counter()
    for d in doc_ids:
        recs = R.build_recipes(texts_of[d][0], V.PROFILES[NEW])
        for rc in recs:
            if rc.unverifiable_reason == "other_frame":
                n[u"other_frame の Recipe"] += 1
                if rc.claim.provenance.get("other_frame"):
                    n[u"provenance に context あり"] += 1
                if rc.claim.pointers if hasattr(rc.claim, "pointers") else False:
                    n[u"pointer あり(0 のはず)"] += 1
            elif (rc.unverifiable_reason or "").startswith("other_frame"):
                n[u"理由の名に context が混ざった(0 のはず)"] += 1
    return kv(n)


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
            u"費用": u"0 USD"}


def judge(rec):
    u"""封 §2 の W-1〜W-9 の機械的な判定。幅・外れ方は封の字のまま。W-7 の読みの部分(偽 ≤ 3%・違う ≤ 10%)は新しい標本に書類が在るときだけ。"""
    J = {}
    if u"W1W2W3" in rec:
        s = rec[u"W1W2W3"][u"集計"]
        n_new = s[u"GROUNDED でない → GROUNDED(新 GROUNDED)"]
        parts = {u"新 GROUNDED 140〜156": 140 <= n_new <= 156, u"枠の取り直しが作る GROUNDED 0": s[u"枠の取り直しが作る GROUNDED"] == 0}
        J[u"W-1"] = {u"実測": u"67 書類(実数 %d)の無改変で新 GROUNDED %d(型 %s)・枠の取り直しが作る GROUNDED %d" % (
            s[u"書類数"], n_new, json.dumps(s[u"新 GROUNDED の型"], ensure_ascii=False), s[u"枠の取り直しが作る GROUNDED"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
        lost, g2g = s[u"GROUNDED → GROUNDED でない"], s[u"GROUNDED → GROUNDED(参照先が動いた)"]
        parts = {u"GROUNDED → 非 GROUNDED 0〜1": 0 <= lost <= 1, u"G → G 0〜6": 0 <= g2g <= 6}
        J[u"W-2"] = {u"実測": u"GROUNDED → 非 GROUNDED %d・GROUNDED → GROUNDED(参照先が動いた)%d" % (lost, g2g),
                   u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
        v24, v23 = s[u"VALUE_MISMATCH の合計 P24"], s[u"VALUE_MISMATCH の合計 P23"]
        nf = s[u"VALUE_MISMATCH → UNVERIFIABLE(other_frame・ambiguous(member))"]
        parts = {u"VALUE_MISMATCH 1,195〜1,211": 1195 <= v24 <= 1211, u"VM → UNVERIFIABLE(other_frame・ambiguous(member))200〜215": 200 <= nf <= 215}
        J[u"W-3"] = {u"実測": u"VALUE_MISMATCH P23 %s → P24 %s(差 %d)・VM → UNVERIFIABLE(other_frame %d・ambiguous(member) %d)計 %d" % (
            format(v23, ","), format(v24, ","), v24 - v23, s[u"うち other_frame"], s[u"うち ambiguous(member)"], nf),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"W4" in rec:
        s = rec[u"W4"][u"集計"]
        p = s[u"P24 で通した(GROUNDED のまま)"]
        parts = {u"穴 B を P24 で通した 0": p[u"件"] == 0, u"止めた行の state が P23 と全行同じ": s[u"P23 と P24 で(結果, state)が違う行"] == 0}
        J[u"W-4"] = {u"実測": u"通した %d / %d・止めた %d・その他 %d。対照 P23 の通した %d。(結果, state)が P23 と違う行 %d(reason・pointers まで含めて %d)" % (
            p[u"件"], p[u"分母"], s[u"P24 で止めた(VALUE_MISMATCH)"][u"件"], s[u"P24 でその他"][u"件"], s[u"P23(対照)で通した"][u"件"],
            s[u"P23 と P24 で(結果, state)が違う行"], s[u"P23 と P24 で(結果, state, reason, pointers)のどれかが違う行"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"W5" in rec:
        e = rec[u"W5"]
        s = e[u"集計"]
        p = e[u"通した P24"]
        parts = {u"通した 2〜3": 2 <= p[u"件"] <= 3,
                 u"止めのうち VM → UNVERIFIABLE に移る 0〜1": 0 <= s[u"VALUE_MISMATCH → UNVERIFIABLE に移った(共通の行)"] <= 1}
        J[u"W-5"] = {u"実測": u"通した %d / %d(%s)・止めた %d / %d・その他 %s。VM → UNVERIFIABLE に移った(共通の行 %d のうち)%d。対照 P23 の通した %d / %d" % (
            p[u"件"], p[u"分母"], u"・".join(x[u"id"] for x in e[u"通した P24 の一覧"]), e[u"止めた P24"][u"件"], e[u"止めた P24"][u"分母"],
            json.dumps(e[u"その他 P24"], ensure_ascii=False), s[u"共通の行"], s[u"VALUE_MISMATCH → UNVERIFIABLE に移った(共通の行)"],
            e[u"通した P23(対照)"][u"件"], e[u"通した P23(対照)"][u"分母"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"W6" in rec:
        s = rec[u"W6"][u"集計"]
        parts = {u"P24 が GROUNDED にする 0 回": s[u"P24 で GROUNDED"] == 0, u"止まらず UNVERIFIABLE 0〜3 回": 0 <= s[u"P24 で UNVERIFIABLE"] <= 3}
        J[u"W-6"] = {u"実測": u"対象 %d 行・注入 %d 回で P24 が GROUNDED %d・UNVERIFIABLE %d・VALUE_MISMATCH %d・その他 %d(対照 P23 は GROUNDED %d)" % (
            s[u"対象の行(GROUNDED か UNVERIFIABLE へ動いた行)"], s[u"注入の数"], s[u"P24 で GROUNDED"], s[u"P24 で UNVERIFIABLE"],
            s[u"P24 で VALUE_MISMATCH"], s[u"P24 でその他"], s[u"P23(対照)で GROUNDED"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"W7" in rec:
        s = rec[u"W7"][u"集計"]
        if not s[u"測れるか(claim が 1 以上の書類が 10 以上)"]:
            J[u"W-7"] = {u"実測": u"手元の cache の 67 の外 %d 書類(区分 %s・種別 %s)に 67 と同じ抽出をかけて claim が 1 以上の書類 %d(claim 合計 %d)。10 未満なので測れない" % (
                s[u"67 の外の書類"], json.dumps(s[u"区分"], ensure_ascii=False), json.dumps(s[u"種別"], ensure_ascii=False),
                s[u"claim が 1 以上の書類(P23)"], s[u"claim の合計(P23)"]), u"判定": u"測れない"}
        else:
            reads = [m[u"読み"] for r in rec[u"W7"][u"書類"] for m in r[u"動いた行"]]
            J[u"W-7"] = {u"実測": u"claim が 1 以上の書類 %d(読み %d 行のうち未読 %d)" % (
                s[u"claim が 1 以上の書類(P23)"], len(reads), sum(1 for x in reads if x is None)),
                u"判定": u"読み待ち(人が全部読んで記録の行に書く)" if any(x is None for x in reads) else u"読みの数え直しは門で"}
    if u"W8" in rec:
        e = rec[u"W8"]
        r = e[u"engine の差分"]
        v, c, rc, rs = (r["adapters/xbrl/vocabulary.py"], r["adapters/xbrl/comparators.py"], r["adapters/xbrl/recipes.py"], r["adapters/xbrl/registry_setup.py"])
        kinds = collections.Counter(x[u"種類"] for x in e[u"既存試験の赤(直す前)"])
        allowed = (u"登録の一覧", u"旗の形", u"sha の留め", u"diff の門")
        parts = {u"recipes.py 挿入 200〜250": 200 <= rc[u"挿入"] <= 250, u"recipes.py 削除 0": rc[u"削除"] == 0,
                 u"vocabulary.py ≤ 35 行": v[u"挿入"] <= 35, u"registry_setup.py ≤ 5 行": rs[u"挿入"] <= 5,
                 u"comparators.py 0 行": c[u"挿入"] == 0 and c[u"削除"] == 0, u"core/ 0 行": r[u"core/"][u"差の行数"] == 0,
                 u"既存試験の赤は種類の中だけ(数 / state の門・人間の決定の字の門は 0)": all(k in allowed for k in kinds)}
        J[u"W-8"] = {u"実測": u"vocabulary.py 挿入 %d・削除 %d、recipes.py 挿入 %d・削除 %d、registry_setup.py 挿入 %d・削除 %d、comparators.py %d/%d、core/ %d 行。既存試験の赤(直す前)%d 本、種類 %s" % (
            v[u"挿入"], v[u"削除"], rc[u"挿入"], rc[u"削除"], rs[u"挿入"], rs[u"削除"], c[u"挿入"], c[u"削除"], r[u"core/"][u"差の行数"],
            len(e[u"既存試験の赤(直す前)"]), json.dumps(kv(kinds), ensure_ascii=False)),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    J[u"W-9"] = {u"実測": u"段 2(既定 P22 → P24。P23 と P25 とまとめて)は人間に 3 つの率を見せてから。この実行では何も変えていない(DEFAULT_PROFILE = %s)" % V.DEFAULT_PROFILE,
               u"判定": u"判定しない(段 2)"}
    return J


def inputs_block(doc_ids_67, doc_ids_out):
    d = {}
    for rel in (ROUNDING_REL, PERIOD_BIND_REL, S2_MATERIAL_REL, S2_REC_REL):
        d[rel] = sha_file(os.path.join(ROOT, rel))
    d[u"seat answers(hybrid_s2_answers)"] = dict((fn, sha_file(os.path.join(PB.HS2.ANS_DIR, fn))) for fn in sorted(os.listdir(PB.HS2.ANS_DIR)) if fn.endswith("_answer.json"))
    d[u"儀式の同梱書類"] = sha_file(os.path.join(ROOT, RIT.ZIP_REL))
    d[u"書類 67(経営分析の文を持つ)の sha256"] = dict((x, sha_file(ED.cache_path(x))) for x in doc_ids_67 if os.path.exists(ED.cache_path(x)))
    d[u"書類 214(67 の外)の sha256 を束ねた値(path 順の 'docID\\tsha256' の行)"] = hashlib.sha256(
        u"\n".join(u"%s\t%s" % (x, sha_file(ED.cache_path(x))) for x in sorted(doc_ids_out)).encode("utf-8")).hexdigest()
    return d


def run(stage, only_docs=None, run_tests=False, progress=None):
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
    rec = {u"step": u"**語彙の登録と枠の取り直しの P24 の段 1 の測定。0 USD・通信なし・engine は測る側から 1 行も変えない**",
           u"環境": env_block(label_shas), u"書類の数": {u"経営分析の文を持つ": len(ids67), u"67 の外": len(ids_out)}}
    secs = {}
    plain_rows = None
    if stage in ("w1", "all"):
        t = time.time()
        with _RawTap() as tap:
            r = plain(tap, ids67, texts_of)
        rec[u"W1W2W3"] = dict(r, **{u"集計": plain_summary(r)})
        plain_rows = [m for m in r[u"動いた行"] if m[u"P24"][u"state"] in ("GROUNDED", "UNVERIFIABLE")
                      and not (m[u"P23"][u"state"] == "UNVERIFIABLE" and m[u"P24"][u"state"] == "UNVERIFIABLE")]
        secs[u"W1W2W3"] = round(time.time() - t, 1)
    if stage in ("w4", "all"):
        t = time.time()
        rows, per = [], []
        for d in ids67:
            zb, text = texts_of[d]
            r, ns, nm = hole_b_doc(d, zb, text)
            rows.extend(r)
            per.append({u"書類": d, u"site": ns, u"作れた": nm})
            if progress:
                progress(u"W-4 %s site %d 作れた %d" % (d, ns, nm))
        rec[u"W4"] = {u"書類別": per, u"行": rows, u"集計": hole_b_summary(rows),
                      u"対照: P23 の再計算と丸めの記録": (hole_b_vs_rounding(rows) if not only_docs else None)}
        secs[u"W4"] = round(time.time() - t, 1)
    if stage in ("w5", "all"):
        t = time.time()
        e = ritual(label_shas)
        rec[u"W5"] = dict(e, **{u"集計": ritual_summary(e)})
        secs[u"W5"] = round(time.time() - t, 1)
    if stage in ("w6", "all"):
        t = time.time()
        if plain_rows is None:
            with _RawTap() as tap:
                plain_rows = [m for m in plain(tap, ids67, texts_of)[u"動いた行"] if m[u"P24"][u"state"] in ("GROUNDED", "UNVERIFIABLE")
                              and not (m[u"P23"][u"state"] == "UNVERIFIABLE" and m[u"P24"][u"state"] == "UNVERIFIABLE")]
        with _RawTap() as tap:
            rows = injections(tap, plain_rows, texts_of, progress)
        rec[u"W6"] = {u"行": rows, u"集計": injection_summary(rows, len(plain_rows))}
        secs[u"W6"] = round(time.time() - t, 1)
    if stage in ("w7", "all"):
        t = time.time()
        only_out = set(ids_out)
        with _RawTap() as tap:
            rows = new_sample(tap, set(ids67)) if not only_docs else [r for r in new_sample(tap, set(ids67)) if r[u"doc"] in only_out]
        rec[u"W7"] = {u"書類": rows, u"集計": new_sample_summary(rows)}
        secs[u"W7"] = round(time.time() - t, 1)
    if stage in ("s2", "all"):
        t = time.time()
        work = tempfile.mkdtemp(prefix="vocab_s2_")
        try:
            rows = s2(work)
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)
        rec[u"S2"] = {u"行": rows, u"集計": s2_summary(rows)}
        secs[u"S2"] = round(time.time() - t, 1)
    if stage in ("prov", "all"):
        t = time.time()
        rec[u"provenance"] = provenance_check(ids67, texts_of)
        secs[u"provenance"] = round(time.time() - t, 1)
    if stage in ("w8", "all"):
        t = time.time()
        e8 = {u"engine の差分": numstat(), u"既存試験の赤(直す前)": existing_red_before_fix(),
              u"覆いの門で赤になった試験(新しい試験 file を足したため。engine と無関係)": list(COVERAGE_RED_BEFORE_FIX)}
        if run_tests:
            e8[u"既存試験"] = [PB.run_pytest("tests/adapters/xbrl")]
        rec[u"W8"] = e8
        secs[u"W8"] = round(time.time() - t, 1)
    secs[u"全体"] = round(time.time() - t_all, 1)
    rec[u"所要秒"] = secs
    rec[u"入力の sha256"] = inputs_block(ids67, ids_out)
    rec[u"予測の判定"] = judge(rec)
    rec[u"limits"] = [
        u"手元の cache の 67 書類(経営分析の文を持つ)。規則はこの 67 書類を読んで作った。無作為ではない。67 書類での偽 0 は新しい標本での偽 0 を意味しない。",
        u"W-7 の新しい標本は手元の cache の 67 の外 214 書類だけ(取りに行かない)。cache に在る 214 書類は全部 jpsps…-asr-(特定有価証券の有価証券報告書)で、67 と同じ抽出(select_mdna)は経営分析の文を取れず claim は 0。= 新しい標本では測れない。",
        u"W-1〜W-6 は封 §0 の試作の再現で、外れるなら実装が試作と違う。67 書類で読んだ規則を同じ 67 書類で測っている。",
        u"W-6 の注入は『末尾の桁 ±3・10 倍・向きの語の反転』の 3 型で、1 回に 1 件。ほかの誤りの作り方では未測定。",
        u"W-5 の儀式は同梱 1 書類(S100Z4Q1)。注入は型 V1・V2 だけ。注入の対象の数は素の書類の GROUNDED で決まり P23 と P24 で違う。",
        u"枠の取り直しは、別の枠の率が帯の中で合うとき、注入した誤りを UNVERIFIABLE にする(封 §3)。『違う』を『要確認』に弱める代価。",
        u"増減の数・支出の減少率を当期の値や符号つきの率と照合する型の正しい文は VALUE_MISMATCH のまま(封 §3)。",
        u"単位 145(店舗・社・台・株・倍・件)は登録していない。",
        u"段 2 の材料(192 行)にはこの規則の形の文が無い(封 §3)= そこでは安全を測れない。補助 S2 は『動いた行 0』の確認だけ。"]
    return rec


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=u"P24 の段 1 の測定(0 USD・通信なし)")
    ap.add_argument("--stage", choices=["w1", "w4", "w5", "w6", "w7", "s2", "prov", "w8", "all"], default="all")
    ap.add_argument("--out", default=None, help=u"記録の出力先。--stage all の既定は " + OUT_REL)
    ap.add_argument("--docs", default=None, help=u"docID をコンマ区切りで絞る(軽い走らせ直し用)")
    ap.add_argument("--run-tests", action="store_true", help=u"W-8 で tests/adapters/xbrl の pytest も走らせて記録する(約 25 分)")
    a = ap.parse_args(argv)
    out = a.out
    if out is None:
        if a.stage != "all" or a.docs:
            raise SystemExit(u"--stage all 以外か --docs のときは --out を渡す(正本の記録を上書きしない)")
        out = os.path.join(ROOT, OUT_REL)
    rec = run(a.stage, set(a.docs.split(",")) if a.docs else None, run_tests=a.run_tests,
              progress=lambda m: print(m, file=sys.stderr))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print(u"=== 語彙の登録と枠の取り直し P24 の段 1(%s → %s・手元の cache・鍵なし・0 USD)===" % (OLD, NEW))
    for k, v in sorted(rec[u"予測の判定"].items()):
        print(u"%s: %s → %s" % (k, v[u"実測"], v[u"判定"]))
    print(u"所要 %s 秒 / 記録: %s" % (json.dumps(rec[u"所要秒"], ensure_ascii=False), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
