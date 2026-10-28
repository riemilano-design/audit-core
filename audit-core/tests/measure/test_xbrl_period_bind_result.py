# -*- coding: utf-8 -*-
u"""期を縛る直し P22 の段 1 の結果 ― 封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md §2(E-1〜E-8)の結果を縛る門。

記録: ``fixtures/xbrl/period_bind_2026-10-20.json``(``measure/xbrl_period_bind_2026-10-20.py --stage all`` の出力)。
文書: ``docs/XBRL_PERIOD_BIND_RESULT_2026-10-20.md``。

この門がやること(どれも、壊した標本で赤くなることを ``MutationTest`` が毎回確かめる):
  1. 入力(書類 67 本と 40 本の sha256・他の記録 5 本の sha256)を**字で留めた digest** に縛る。cache が在る機械では実物の sha256 も記録と一致させる。
  2. 記録の行(E-1 の注入 485・E-2 の動いた 42 行・E-3 の動いた 26 行・E-4 の 192 行)から、集計・分布・群・向きを**独立に**数え直し、記録の集計と一致させる。
     script の関数は使わない(pointer の字・span の正規表現から求め直す)。
  3. 予測 E-1〜E-8 の判定を、封の字から読んだ幅と記録の行から**門が自分で**求め、記録の判定と文書の表と一致させる。
  4. 文書の表(予測・E-1 の単位別・E-2 の動いた行 42・E-3 の動いた行・E-4・E-5)を記録から作った字と完全一致させる。
     人の読み(E-2 の動いた行の型 ``READ``)は門が字で持ち、記録の行と過不足なく対応することを縛る(読みそのものは人の読み)。
  5. engine の sha(測った時点の recipes.py・vocabulary.py)を字で留め、いまの engine が同じか宣言された遷移であること。
     ``core/`` が封の commit から 0 行であること。``DEFAULT_PROFILE`` は段 1 では P21 のままだったが、**段 2(2026-10-20)で P22 になった**。
  6. cache とラベルが在る機械では、軽い走らせ直し(E-1 を 1 書類、E-2 を 2 書類)を script で走らせて記録の該当行と一致。
     全部の走らせ直し(約 10 分)は ``AUDIT_CORE_PERIOD_BIND=1`` のときだけ。
  7. **文書の散文の数**(2026-10-20 独立監査の指摘): 数のある文(結論・E-1〜E-7 の数・代価・部分の判定・所要秒)は ``prose_facts`` が記録から作り、
     文書がその字を含むことを縛る。変異の表は記録の写し(``変異(engine。手で走らせた)``)から作る。それ以外の散文に数字が在れば
     ``residual_numbers`` が見つけて赤にする(コード片・識別子・日付・節の番号は除く)。散文は漢数字で書く。
  8. **段 2(2026-10-20。既定 P21 -> P22)**: 記録の新欄 ``stage2_default_2026-10-20`` ― profile を省いた製品の経路が段 1 の P22 の数と 1 行ずつ一致する
     (E-1 の 485 行・E-2 の動いた 36 行・E-5 の 240 行で差 0)― を、段 1 の記録の行から独立に数え直した値と一致させる。
     文書 §14 の数は ``stage2_facts`` が記録から作った字で縛る。既定が P22 であること・決定の注記が日付つきで在り P21 の注記が消えていないこと・
     ``vocabulary.py`` の sha が宣言された遷移であること・封の末尾の追記が 1 点だけであることも縛る。変異は ``MutationTest`` が毎回走らせる。
     儀式の P21 の記録(対照)は ``fixtures/xbrl/ritual_2026-10-20_p21.json``(段 2 で ``ritual_2026-10-20.json`` を P22 で採り直したため)。
縛っていないもの: 型の読みの正しさ(人の読み)、A〜C の例などの引用文(コード片の中の数)、限界の文の主張(中身は人の読み)、
  変異の手の実測そのもの(表は記録の写しを縛るだけで、変異を走らせ直すのは ``mutate.py`` を手で)、tests/measure 全体の所要。
  漢数字で書いた数(``residual_numbers`` は算用数字だけを探す。散文の数は記録から作った字で縛る約束で、漢数字の数は縛らない ― 2026-10-20 の独立監査の軽い指摘)。
**2026-10-27 追記(重い走らせ直しの遷移。封 docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md §2-4)**: ``AUDIT_CORE_PERIOD_BIND=1`` の ``test_heavy_stage2_default_matches_the_record`` は、
P23 の段 1 以後の engine の commit で動いた ``recipes.py の sha16``・``vocabulary.py の sha16``・``engine の束ねた sha256`` が記録(段 2 の当時の値)と違って赤だった。
比べは ``heavy_rerun_check`` に移し、``HEAVY_RERUN_LATER`` に名指しした 3 欄だけを、封が履歴に在り値が宣言の値のときに限って記録の値に戻す。測った値の欄
(E1・E2・E5・対照・差 0 の行数・差のあった行の合計・DEFAULT_PROFILE)は byte 一致のまま。遷移の規則は ``MutationTest.test_mh_heavy_rerun_transitions`` が環境変数なしで毎回試す。
"""
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
REC = os.path.join(ROOT, "fixtures", "xbrl", "period_bind_2026-10-20.json")
DOC = os.path.join(ROOT, "docs", "XBRL_PERIOD_BIND_RESULT_2026-10-20.md")
SEAL_REL = "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SCRIPT = os.path.join(ROOT, "measure", "xbrl_period_bind_2026-10-20.py")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
RUN_HEAVY = os.environ.get("AUDIT_CORE_PERIOD_BIND") == "1"
VOCAB = os.path.join(ROOT, "adapters", "xbrl", "vocabulary.py")
RITUAL_P21 = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20_p21.json")       # P21 のときの儀式の記録(段 1 の対照)
RITUAL_P22 = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20_p22.json")       # 段 2 で P22(既定)で採り直した儀式の記録。2026-10-23 の P26 の段 2 で ritual_2026-10-20.json は P26 で採り直したので、同じバイト列(sha256 c89824f7…)の写し
STAGE2 = u"stage2_default_2026-10-20"
STAGE2_HEAD = u"## 14. 段 2(2026-10-20、既定 P21 → P22)"
#: 既定で測った記録を持つ measure。測った当時の P21 を字で留めた(段 2)。vocabulary.DEFAULT_PROFILE を読まない。
PINNED_P21_SCRIPTS = ("measure/xbrl_point_prior_2026-10-20.py", "measure/xbrl_hybrid_s2_2026-10-20.py", "measure/xbrl_hybrid_trust_2026-10-20.py")
HEAVY_SKIP_REASON = u"AUDIT_CORE_PERIOD_BIND=1 のときだけ走る(全部の走らせ直し。約 10 分)"
LIGHT_E1_DOCS = ("S100YMFV",)               # 注入 4 件(P21 では 4 件とも通し、P22 では 4 件とも止める)
LIGHT_E2_DOCS = ("S100Z4DE", "S100YUHC")    # 手がかりの字の規則に載らない前期の数 5 件・減少額が前期残高と一致 2 件

#: **字で留める**(記録の値の写し。定数から作らない)。
DOCS67_DIGEST = "118ec1015494db404b74dbd65b72bddfd2356459749d6f10dc910e5a1348429f"       # 書類 67 本の docID\tsha256 を sorted で \n 結合した sha256
DOCS40_DIGEST = "7226d84a9d4ab4e63f982a2638b561a36cccd7a327a3c587f3076b5425eb2ba3"       # 書類 40 本(名指しの直しの無改変の集合)も同じ作り
ENGINE_AT_MEASURE = {"adapters/xbrl/recipes.py": "65a37869f053a60e", "adapters/xbrl/vocabulary.py": "1fdb48e7e3ba58ce"}
#: 測った時点の engine を宣言された遷移として受け入れる: {path: (後の sha16, 遷移を宣言した封の path)}。
#: 2026-10-20(段 2): vocabulary.py の DEFAULT_PROFILE を P21 -> P22 にし、決定の注記を日付つきで足した(vocabulary.py だけ。recipes.py は 0 行)。
#: 段 1 の sha(1fdb48e7e3ba58ce)は ENGINE_AT_MEASURE に残す(段 1 の記録が測った時点の値)。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
#: 段 2(d0b544c)の後の engine(段 2 の記録 stage2_default_2026-10-20 が測った時点の値)。消さない。
ENGINE_AT_STAGE2 = {"adapters/xbrl/recipes.py": "65a37869f053a60e", "adapters/xbrl/vocabulary.py": "25a3c0992e10daaa"}
#: 2026-10-21 追記(pin の遷移): 封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md(丸めの帯 P23 の段 1。engine を変える。人間の事前承認 2026-10-21)で
#: vocabulary.py に旗 truncate_abs_band・P23・PROFILES の登録を足し、recipes.py に _mag_trunc を足した(DEFAULT_PROFILE は P22 のまま)。
#: 上の段 2 の値は ENGINE_AT_STAGE2 に残す。受け入れるのは、その封が履歴に在り、値が P23 の段 1 の後の値のときだけ。
SEAL_ROUNDING = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"
SEAL_VOCAB = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"    # 2026-10-21 追記: 語彙の登録と枠の取り直し P24 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"    # 2026-10-21 追記: 最後の枝 P25 の段 1(下の ENGINE_LATER の遷移)
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"    # 2026-10-22 追記: P26 の段 1(下の ENGINE_LATER の遷移)
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
SEAL_DEFAULT_P27 = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"    # 2026-10-28 追記: 既定を P26 -> P27 に切り替える 段 2(下の遷移。vocabulary.py の DEFAULT_PROFILE の 1 行と注記 +5 行・-1 行、verify_document.py の docstring の 1 行 +1 行・-1 行だけ)
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
                # 85896a67913ce1e7(P27 の段 2) は残す(測った時点の値。vocabulary.py の sha16)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 514ebb8104451c07。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
                "adapters/xbrl/vocabulary.py": ("514ebb8104451c07", SEAL_DEFAULT_P27)}
FACT = {
    "e1": (485, 1, 482, 2),                    # 注入・P22 で通した・止めた・その他
    "e1_p21": (459, 458),                      # P21(対照)で通した・うち前期へ移った(穴 B の記録と同じ 459・458)
    "e2": (36, 25, 11, 0),                     # 動いた(全 state)・GROUNDED を離れた・参照先だけ動いた・新 GROUNDED(P21 で GROUNDED でない行は動かない)
    "e2_groups": {u"Prior1Year・手がかりあり": 11, u"Prior1Year・手がかり無し": 25},    # 動いた GROUNDED の群(当期 1,726 は 0 行)
    "e2_base_groups": {u"Prior1Year・手がかりあり": 190, u"Prior1Year・手がかり無し": 26, u"pointer が 1 本でない": 2325, u"当期": 1726},
    "e2_types": {},                            # 下で READ の型の件数から作る(A 13・B 1・C 11・D 10・E 1・F 6)
    "e3": (23, 16, 7, 0, 4665),                # 動いた・離れた・参照先だけ動いた・新 GROUNDED・claims
    "e4": (0, 6, 6, 0, 0),                     # T6 の P22 GROUNDED・段 2 の記録の GROUNDED・Core 自身が動いた行・対照の違い・α 型の違い
    "e5": (15, 225, 240),                      # 通した・止めた・注入の対象(封の予測は 15・226・241)
}

CUE = re.compile(u"前期|前年|前連結会計年度|前事業年度|\\(同|（同|前期末|前年度")   # 封 §0 の代価 26 を数えた字(test_xbrl_period_bind_seal.py の CUE と同じ)
PTR = re.compile(r"^xbrl:([^@]+)@(.+)$")
K_MOVED = u"通した(参照先が前期へ移った)"
K_SAME = u"通した(参照先が当期の同じ参照先のまま)"
K_OTHER = u"通した(参照先が当期の別要素)"
K_ODD = u"通した(参照先がそのほか)"
K_STOP = u"止めた"
K_ELSE = u"その他"
PASSED_KINDS = (K_MOVED, K_SAME, K_OTHER, K_ODD)

#: 人の読み(E-2 の動いた 42 行を 1 件ずつ文脈を読んで付けた型。記録の行と過不足なく対応することを門が縛る)。
T_A = u"A 減少額が前期の残高と一致"
T_B = u"B 別の要素の前期の値との偶然一致"
T_C = u"C 前期の値を正しく言う文(手がかりの語が engine の字の規則の外)"
T_D = u"D 両期が同額で当期の fact に結び直った"
T_E = u"E 増減額の導出(当期 − 前期)に結び直った"
READ = {
    # GROUNDED を離れた 25 行(手がかり無し 14 = A 13 + B 1、手がかりあり 11 = C 11)。2026-10-20 の独立監査の後、P22 は主語なしを P21 と同一にしたので、P21 で GROUNDED でない行は動かない
    ("S100YUHC", "N076"): T_A, ("S100YUHC", "N104"): T_A,
    ("S100YYRV", "N071"): T_A, ("S100YYRV", "N072"): T_A, ("S100YYRV", "N076"): T_A,
    ("S100YZ4E", "N021"): T_A, ("S100Z39P", "N038"): T_A, ("S100Z3CO", "N043"): T_A, ("S100Z433", "N009"): T_A,
    ("S100Z4N9", "N056"): T_A, ("S100Z4PA", "N046"): T_A, ("S100Z4PA", "N050"): T_A, ("S100Z5DN", "N014"): T_A,
    ("S100Z4PA", "N084"): T_B,
    ("S100YYS4", "N008"): T_C, ("S100YYS4", "N057"): T_C,
    ("S100YYVN", "N010"): T_C, ("S100YYVN", "N029"): T_C, ("S100YYVN", "N057"): T_C,
    ("S100Z3JY", "N084"): T_C,
    ("S100Z4DE", "N030"): T_C, ("S100Z4DE", "N035"): T_C, ("S100Z4DE", "N040"): T_C, ("S100Z4DE", "N045"): T_C, ("S100Z4DE", "N050"): T_C,
    # GROUNDED のまま参照先だけ動いた 11 行(D 10 + E 1)
    ("S100YXGH", "N040"): T_D, ("S100YZ31", "N031"): T_D, ("S100YZ7E", "N028"): T_D, ("S100YZ7E", "N058"): T_D,
    ("S100Z3CI", "N038"): T_D, ("S100Z3HP", "N039"): T_D, ("S100Z3HP", "N044"): T_D, ("S100Z3LJ", "N056"): T_D,
    ("S100Z4PA", "N083"): T_D, ("S100Z5DN", "N081"): T_D,
    ("S100Z4J8", "N026"): T_E,
}
FACT["e2_types"] = {T_A: 13, T_B: 1, T_C: 11, T_D: 10, T_E: 1}


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def sha_path(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def digest(lines):
    return hashlib.sha256(u"\n".join(lines).encode("utf-8")).hexdigest()


def F(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


def cell(s):
    return (s if s is not None else u"").replace(u"|", u"｜").replace(u"\n", u" ")


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def tally(rows, f):
    d = {}
    for r in rows:
        k = f(r)
        d[k] = d.get(k, 0) + 1
    return dict(sorted(d.items()))


# ----------------------------------------------------------------------------------------------------------------
# 独立な数え直し
def e1_kind(side, row):
    u"""注入の後の state と pointers の字から 止めた/通した/その他 を求める(script の classify_after を使わない)。"""
    st = side[u"state"]
    if st in ("sentence_not_found", "missing", "id_shift"):
        return K_ELSE
    if st == "VALUE_MISMATCH":
        return K_STOP
    if st != "GROUNDED":
        return K_ELSE
    ms = [PTR.match(p) for p in side[u"pointers"] if p.startswith("xbrl:")]
    assert ms and all(ms), u"GROUNDED なのに xbrl の pointer が無い"
    ctxs = [m.group(2) for m in ms]
    if all(c.startswith("Prior1Year") for c in ctxs):
        return K_MOVED
    if all(m.group(1) == row[u"要素"] for m in ms):
        return K_SAME
    return K_OTHER


def recount_e1(rows):
    n = len(rows)
    out = {u"注入": n}
    for key, name in ((u"P22", u"P22"), (u"P21(対照)", u"P21")):
        kinds = [e1_kind(r[key], r) for r in rows]
        c = tally(kinds, lambda k: k)
        passed = sum(c.get(k, 0) for k in PASSED_KINDS)
        out[name] = {u"結果": c, u"通した": passed, u"止めた": c.get(K_STOP, 0), u"その他": c.get(K_ELSE, 0), u"Prior1Year へ移った": c.get(K_MOVED, 0)}
    units = {}
    for r in rows:
        u = units.setdefault(r[u"単位"], {u"注入": 0, u"P21 通した": 0, u"P22 通した": 0, u"P22 止めた": 0, u"P22 その他": 0})
        u[u"注入"] += 1
        k21, k22 = e1_kind(r[u"P21(対照)"], r), e1_kind(r[u"P22"], r)
        u[u"P21 通した"] += k21 in PASSED_KINDS
        u[u"P22 通した"] += k22 in PASSED_KINDS
        u[u"P22 止めた"] += k22 == K_STOP
        u[u"P22 その他"] += k22 == K_ELSE
    out[u"単位別"] = dict(sorted(units.items()))
    out[u"P22 の止めた行の state"] = tally([r for r in rows if e1_kind(r[u"P22"], r) == K_STOP], lambda r: r[u"P22"][u"state"])
    out[u"遷移"] = tally(rows, lambda r: u"%s → %s" % (e1_kind(r[u"P21(対照)"], r), e1_kind(r[u"P22"], r)))
    return out


def group_of(row_side, span):
    u"""P21 で GROUNDED の主張の群(封 §0 の代価 26 / 190 / 1,726 の数え方)。"""
    ptr = row_side[u"pointers"]
    if len(ptr) != 1:
        return u"pointer が 1 本でない"
    if ptr[0].split("@")[-1].startswith("Prior1Year"):
        return u"Prior1Year・手がかりあり" if CUE.search(span or u"") else u"Prior1Year・手がかり無し"
    return u"当期"


def recount_cmp(sec):
    mv = sec[u"動いた行"]
    for r in mv:
        assert r[u"P21"] != r[u"P22"], u"動いたのに P21 と P22 が同じ"
        assert r[u"向き"] == u"%s → %s" % (r[u"P21"][u"state"], r[u"P22"][u"state"]), r[u"id"]
        if r[u"P21"][u"state"] == "GROUNDED":
            assert r[u"P21 の群"] == group_of(r[u"P21"], r[u"span"]), (r[u"doc"], r[u"id"], r[u"P21 の群"])
        else:
            assert r[u"P21 の群"] is None
    leave = [r for r in mv if r[u"P21"][u"state"] == "GROUNDED" and r[u"P22"][u"state"] != "GROUNDED"]
    stay = [r for r in mv if r[u"P21"][u"state"] == "GROUNDED" and r[u"P22"][u"state"] == "GROUNDED"]
    new = [r for r in mv if r[u"P21"][u"state"] != "GROUNDED" and r[u"P22"][u"state"] == "GROUNDED"]
    return {u"動いた": len(mv), u"離れた": len(leave), u"参照先だけ動いた": len(stay), u"新 GROUNDED": len(new),
            u"動いた GROUNDED の群": tally([r for r in mv if r[u"P21"][u"state"] == "GROUNDED"], lambda r: r[u"P21 の群"]),
            u"離れた行の群": tally(leave, lambda r: r[u"P21 の群"]),
            u"向き": tally(mv, lambda r: r[u"向き"]),
            u"離れた行の向き": tally(leave, lambda r: r[u"向き"]),
            u"離れた行のうち 文に 減少・減": sum(1 for r in leave if re.search(u"減少|減", r[u"文脈"] or r[u"span"] or u"")),
            u"書類": len({r[u"doc"] for r in leave}),
            u"claims": sum(d[u"claims"] for d in sec[u"書類"]),
            u"書類の数": len(sec[u"書類"])}


def recount_e4(rows):
    t6 = [r for r in rows if r[u"注入の型"] == "T6_PRIOR"]
    al = [r for r in rows if r[u"α 型を当てた"]]
    return {u"行": len(rows), u"注入": sum(1 for r in rows if r[u"注入か"]), u"T6": len(t6),
            u"T6 P22 GROUNDED": sum(1 for r in t6 if r[u"Core 自身 P22"][u"state"] == "GROUNDED"),
            u"T6 記録 GROUNDED": sum(1 for r in t6 if r[u"Core 自身(段 2 の記録)"][u"state"] == "GROUNDED"),
            u"T6 P21 再計算 GROUNDED": sum(1 for r in t6 if r[u"Core 自身 P21(今回)"][u"state"] == "GROUNDED"),
            u"対照の違い": sum(1 for r in rows if r[u"Core 自身 P21(今回)"] != r[u"Core 自身(段 2 の記録)"]),
            u"動いた": sum(1 for r in rows if r[u"Core 自身 P21(今回)"] != r[u"Core 自身 P22"]),
            u"注入 P22 GROUNDED": sum(1 for r in rows if r[u"注入か"] and r[u"Core 自身 P22"][u"state"] == "GROUNDED"),
            u"α 型": len(al), u"α 型の違い": sum(1 for r in al if r[u"α 型(今回)"] != r[u"α 型(段 2 の記録)"]),
            u"α 型が記録の席の参照先なしと食い違う": sum(1 for r in rows if (r[u"α 型(段 2 の記録)"] is None) == r[u"α 型を当てた"])}


def check_record(rec):
    u"""記録の内側の整合(行 → 集計)。壊した記録で赤くなる。"""
    e1 = rec[u"E1"]
    c = recount_e1(e1[u"行"])
    s = e1[u"集計"]
    assert s[u"注入"] == c[u"注入"]
    assert s[u"P22 の結果"] == c[u"P22"][u"結果"] and s[u"P21(対照)の結果"] == c[u"P21"][u"結果"]
    assert s[u"P22 で通した(GROUNDED のまま)"] == {u"件": c[u"P22"][u"通した"], u"分母": c[u"注入"], u"率": round(100.0 * c[u"P22"][u"通した"] / c[u"注入"], 1)}
    assert s[u"P21(対照)で通した"] == {u"件": c[u"P21"][u"通した"], u"分母": c[u"注入"], u"率": round(100.0 * c[u"P21"][u"通した"] / c[u"注入"], 1)}
    assert s[u"P22 で止めた(VALUE_MISMATCH)"][u"件"] == c[u"P22"][u"止めた"]
    assert s[u"P22 でその他(通した でも 止めた でもない)"][u"件"] == c[u"P22"][u"その他"]
    assert {k: v for k, v in s[u"P21 → P22 の遷移"].items()} == c[u"遷移"]
    for u_, v in c[u"単位別"].items():
        assert s[u"単位別 P22"][u_].get(K_STOP, 0) == v[u"P22 止めた"], u_
        assert sum(n for k, n in s[u"単位別 P22"][u_].items() if k in PASSED_KINDS) == v[u"P22 通した"], u_
        assert sum(n for k, n in s[u"単位別 P21(対照)"][u_].items() if k in PASSED_KINDS) == v[u"P21 通した"], u_
    for sec_name in (u"E2", u"E3"):
        sec = rec[sec_name]
        r = recount_cmp(sec)
        a = sec[u"集計"]
        assert a[u"動いた(全 state)"] == r[u"動いた"], sec_name
        assert a[u"GROUNDED → GROUNDED でない"] == r[u"離れた"] and a[u"GROUNDED → GROUNDED(参照先だけ動いた)"] == r[u"参照先だけ動いた"], sec_name
        assert a[u"GROUNDED でない → GROUNDED(新 GROUNDED)"] == r[u"新 GROUNDED"], sec_name
        assert sec[u"動いた GROUNDED の群"] == r[u"動いた GROUNDED の群"], sec_name
        assert a[u"GROUNDED → 非 GROUNDED の群"] == r[u"離れた行の群"], sec_name
        assert a[u"向き(全部)"] == r[u"向き"], sec_name
        assert a[u"GROUNDED → の向き"] == r[u"離れた行の向き"], sec_name
        assert a[u"GROUNDED → 非 GROUNDED のうち 印: 文に 減少・減"] == r[u"離れた行のうち 文に 減少・減"], sec_name
        assert a[u"GROUNDED → 非 GROUNDED の書類数"] == r[u"書類"], sec_name
        assert a[u"claims"] == r[u"claims"], sec_name
        assert sec[u"集計"][u"P21 の GROUNDED"] == a[u"P21 の GROUNDED"]
        assert sum(sec[u"P21 の GROUNDED の群"].values()) == a[u"P21 の GROUNDED"], sec_name
        for d in sec[u"書類"]:
            assert d[u"動いた"] == sum(1 for x in sec[u"動いた行"] if x[u"doc"] == d[u"doc"]), d[u"doc"]
            assert d[u"GROUNDED(P22)"] - d[u"GROUNDED(P21)"] == -sum(
                1 for x in sec[u"動いた行"] if x[u"doc"] == d[u"doc"] and x[u"P21"][u"state"] == "GROUNDED" and x[u"P22"][u"state"] != "GROUNDED"), d[u"doc"]
    # E-3 の動いた行は E-2 の動いた行の部分集合(40 書類は 67 書類の中)
    e2k = dict(((x[u"doc"], x[u"id"]), x) for x in rec[u"E2"][u"動いた行"])
    for x in rec[u"E3"][u"動いた行"]:
        y = e2k.get((x[u"doc"], x[u"id"]))
        assert y is not None and y[u"P21"] == x[u"P21"] and y[u"P22"] == x[u"P22"], (x[u"doc"], x[u"id"])
    assert sorted(rec[u"E3"][u"40 のうち 67 と重なる書類"]) == sorted(d[u"doc"] for d in rec[u"E3"][u"書類"])
    e4 = recount_e4(rec[u"E4"][u"行"])
    s4 = rec[u"E4"][u"集計"]
    assert (s4[u"行"], s4[u"注入"], s4[u"T6_PRIOR の注入"]) == (e4[u"行"], e4[u"注入"], e4[u"T6"])
    assert s4[u"T6 で Core 自身 P22 が GROUNDED"] == {u"件": e4[u"T6 P22 GROUNDED"], u"分母": e4[u"T6"], u"率": round(100.0 * e4[u"T6 P22 GROUNDED"] / e4[u"T6"], 1)}
    assert s4[u"T6 で Core 自身 段 2 の記録が GROUNDED"][u"件"] == e4[u"T6 記録 GROUNDED"]
    assert s4[u"T6 で Core 自身 P21(今回の再計算)が GROUNDED"][u"件"] == e4[u"T6 P21 再計算 GROUNDED"]
    assert s4[u"対照: P21 の再計算が 段 2 の記録と違った行"] == e4[u"対照の違い"]
    assert s4[u"Core 自身が P21 → P22 で動いた行(型を問わず)"] == e4[u"動いた"]
    assert s4[u"全注入(64)で Core 自身 P22 が GROUNDED"][u"件"] == e4[u"注入 P22 GROUNDED"]
    assert (s4[u"α 型を当てた行"], s4[u"α 型が記録と違った行"]) == (e4[u"α 型"], e4[u"α 型の違い"])
    assert e4[u"α 型が記録の席の参照先なしと食い違う"] == 0, u"α 型を当てた行と 段 2 の記録の『参照先なし』が食い違う"
    st = rec[u"E4"][u"α 型の経路の構造"]
    assert st[u"引数に profile が在る"] is False and st[u"verify_external の module の字に _direct_value_claim が在る"] is False
    e5 = rec[u"E5"]
    assert e5[u"通した P22"][u"件"] == len(e5[u"P22 の通した 一覧(id と型)"])
    assert e5[u"通した P22"][u"分母"] == e5[u"止めた P22"][u"分母"] == e5[u"注入の対象"]
    assert e5[u"通した P22"][u"件"] + e5[u"止めた P22"][u"件"] <= e5[u"注入の対象"]
    assert e5[u"対照: P21 の再計算が儀式の記録と違った行"] == 0
    ps = rec[u"postscript_2026-10-20"]
    assert u"外れ" in ps[u"E-7 の判定"] and u"test_recipes_p21.py" in ps[u"4 か所目の直し"]
    assert rec[u"E7"][u"封の 3 か所のほかに直した既存試験"] and rec[u"予測の判定"]["E-7"][u"判定"] == u"外れ", u"四か所目が要ったので E-7 は外れ"
    check_mutation_record(rec)


# ----------------------------------------------------------------------------------------------------------------
# 入力・環境
def check_inputs(rec):
    e = rec[u"環境"]
    assert e[u"費用"] == u"0 USD" and e[u"DEFAULT_PROFILE"] == "P21" and e[u"比べた profile"] == ["P21", "P22"]
    assert e[u"recipes.py の sha16"] == ENGINE_AT_MEASURE["adapters/xbrl/recipes.py"]
    assert e[u"vocabulary.py の sha16"] == ENGINE_AT_MEASURE["adapters/xbrl/vocabulary.py"]
    assert set(e[u"鍵の名前の有無(値は読まない)"]) == {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "EDINET_API_KEY", "OPENAI_API_KEY"}
    inp = rec[u"入力の sha256"]
    d67 = inp[u"書類 67(経営分析の文を持つ)の sha256"]
    d40 = inp[u"書類 40(名指しの直しの無改変)の sha256"]
    assert len(d67) == 67 and len(d40) == 40
    assert digest(sorted(u"%s\t%s" % kv for kv in d67.items())) == DOCS67_DIGEST, u"書類 67 の digest"
    assert digest(sorted(u"%s\t%s" % kv for kv in d40.items())) == DOCS40_DIGEST, u"書類 40 の digest"
    assert sorted(d[u"書類"] for d in rec[u"E1"][u"書類別"]) == sorted(d67), u"E-1 の書類別が 67 書類と違う"
    assert sorted(d[u"doc"] for d in rec[u"E2"][u"書類"]) == sorted(d67)
    assert sorted(d[u"doc"] for d in rec[u"E3"][u"書類"]) == sorted(d40)
    assert rec[u"E3"][u"キャッシュに無い書類"] == [] and rec[u"E2"][u"キャッシュに無い書類"] == []
    for rel in ("fixtures/xbrl/point_prior_2026-10-20.json", "fixtures/xbrl/ritual_2026-10-20.json", "fixtures/xbrl/naming_fix/p21_2026-10-20.json",
                "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json", "fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json"):
        assert rel in inp, rel
    assert len(inp[u"seat answers(hybrid_s2_answers)"]) == 8


# ----------------------------------------------------------------------------------------------------------------
# 予測の判定(封の字から幅を読み、記録の行から門が求める)
def seal_cells(seal, tag):
    for l in seal.splitlines():
        if l.startswith(u"| **%s** |" % tag):
            return [c.strip() for c in l.strip().strip(u"|").split(u"|")]
    raise AssertionError(tag)


def bounds(seal):
    c = {t: seal_cells(seal, t)[1] for t in ("E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8")}
    m1 = re.search(r"通した\(GROUNDED のまま\) \*\*(\d+)〜(\d+) / 485\*\*.*止めた\(VALUE_MISMATCH\)\*\*(\d+)〜(\d+)\*\*", c["E-1"])
    m2 = re.search(r"\*\*(\d+)〜(\d+)\*\*\(§0 の 26", c["E-2"])
    m3 = re.search(r"\*\*≤ (\d+)\*\*", c["E-3"])
    m4 = re.search(r"\*\*(\d+)〜(\d+) / 10\*\* GROUNDED\((\d+) から\)", c["E-4"])
    m5 = re.search(r"通した \*\*(\d+)\*\*.*止めた \*\*(\d+)\*\*", c["E-5"])
    m7 = re.search(r"`recipes.py` \*\*≤ (\d+) 行\*\*.*`vocabulary.py` \*\*≤ (\d+) 行\*\*", c["E-7"])
    m5b = re.search(r"他の (\d+) 件は同じ結果", c["E-5"])
    assert m1 and m2 and m3 and m4 and m5 and m5b and m7, u"封の予測の書き方が変わった"
    return {"e1_pass": (int(m1.group(1)), int(m1.group(2))), "e1_stop": (int(m1.group(3)), int(m1.group(4))),
            "e2": (int(m2.group(1)), int(m2.group(2))), "e3": int(m3.group(1)), "e4": (int(m4.group(1)), int(m4.group(2))),
            "e5": (int(m5.group(1)), int(m5.group(2))), "e5_same": int(m5b.group(1)), "e7": (int(m7.group(1)), int(m7.group(2)))}


def judgments(rec, seal):
    b = bounds(seal)
    J = {}
    c1 = recount_e1(rec[u"E1"][u"行"])
    J["E-1"] = u"当たり" if (b["e1_pass"][0] <= c1[u"P22"][u"通した"] <= b["e1_pass"][1] and b["e1_stop"][0] <= c1[u"P22"][u"止めた"] <= b["e1_stop"][1]) else u"外れ"
    r2 = recount_cmp(rec[u"E2"])
    g = rec[u"E2"][u"P21 の GROUNDED の群"]
    ok2 = (b["e2"][0] <= r2[u"離れた"] <= b["e2"][1] and r2[u"新 GROUNDED"] == 0
           and r2[u"動いた GROUNDED の群"].get(u"Prior1Year・手がかりあり", 0) == 0 and r2[u"動いた GROUNDED の群"].get(u"当期", 0) == 0)
    J["E-2"] = u"当たり" if ok2 else u"外れ"
    r3 = recount_cmp(rec[u"E3"])
    n3 = sum(r3[u"動いた GROUNDED の群"].values())
    J["E-3"] = u"当たり" if (n3 <= b["e3"] and r3[u"新 GROUNDED"] == 0) else u"外れ"
    c4 = recount_e4(rec[u"E4"][u"行"])
    J["E-4"] = u"当たり" if (b["e4"][0] <= c4[u"T6 P22 GROUNDED"] <= b["e4"][1] and c4[u"α 型の違い"] == 0) else u"外れ"
    e5 = rec[u"E5"]
    moved5 = sorted(x[u"id"] for x in e5[u"P21 → P22 で結果が動いた行"])
    ok5 = (e5[u"通した P22"][u"件"] == b["e5"][0] and e5[u"止めた P22"][u"件"] == b["e5"][1] and moved5 == ["N125", "N199"]
           and e5[u"注入の対象"] == b["e5"][0] + b["e5"][1] and e5[u"他の行(両方に在る)で結果が同じ"] == b["e5_same"])
    J["E-5"] = u"当たり" if ok5 else u"外れ"
    J["E-6"] = u"判定は文書で(人の読み)"
    e7 = rec[u"E7"]
    d = e7[u"engine の差分"]
    n_r = d["adapters/xbrl/recipes.py"][u"挿入"] + d["adapters/xbrl/recipes.py"][u"削除"]
    n_v = d["adapters/xbrl/vocabulary.py"][u"挿入"] + d["adapters/xbrl/vocabulary.py"][u"削除"]
    tests_ok = bool(e7.get(u"既存試験")) and all(t[u"rc"] == 0 for t in e7[u"既存試験"]) and not e7.get(u"封の 3 か所のほかに直した既存試験")
    J["E-7"] = u"当たり" if (n_r <= b["e7"][0] and n_v <= b["e7"][1] and d[u"core/"][u"差の行数"] == 0 and tests_ok) else u"外れ"
    J["E-8"] = u"判定しない(段 2)"
    return J


def check_judgments(rec, seal):
    want = judgments(rec, seal)
    got = dict((k, v[u"判定"]) for k, v in rec[u"予測の判定"].items())
    assert sorted(got) == sorted(want), (sorted(got), sorted(want))
    for k in want:
        assert got[k] == want[k], (k, got[k], want[k])


# ----------------------------------------------------------------------------------------------------------------
# 文書に載せる表(記録から作る。文書はこの字を含まなければならない)
def moved_type(x):
    return READ.get((x[u"doc"], x[u"id"]))


def render_blocks(rec):
    B = {}
    pr = rec[u"予測の判定"]
    L = [u"| # | 実測 | 判定 |", u"|---|---|---|"]
    for k in sorted(pr, key=lambda s: int(s.split("-")[1])):
        L.append(u"| **%s** | %s | **%s** |" % (k, cell(pr[k][u"実測"]), pr[k][u"判定"]))
    B["予測の表"] = u"\n".join(L)
    c1 = recount_e1(rec[u"E1"][u"行"])
    L = [u"| 単位 | 注入 | P21 通した | P22 通した | P22 止めた | P22 その他 |", u"|---|---:|---:|---:|---:|---:|"]
    tot = [0] * 5
    for u_, v in c1[u"単位別"].items():
        row = [v[u"注入"], v[u"P21 通した"], v[u"P22 通した"], v[u"P22 止めた"], v[u"P22 その他"]]
        tot = [a + b for a, b in zip(tot, row)]
        L.append(u"| %s | %d | %d | %d | %d | %d |" % ((u_,) + tuple(row)))
    L.append(u"| **合計** | **%d** | **%d** | **%d** | **%d** | **%d** |" % tuple(tot))
    B["E-1 の単位別"] = u"\n".join(L)
    B["E-1 の率"] = u"P21(対照) 通した %s・P22 通した %s・P22 止めた %s・P22 その他 %s" % (
        F(c1[u"P21"][u"通した"], c1[u"注入"]), F(c1[u"P22"][u"通した"], c1[u"注入"]), F(c1[u"P22"][u"止めた"], c1[u"注入"]), F(c1[u"P22"][u"その他"], c1[u"注入"]))
    L = [u"| doc | id | P21 → P22 | P21 の群 | 型(人の読み) | 文の抜粋 |", u"|---|---|---|---|---|---|"]
    for x in rec[u"E2"][u"動いた行"]:
        L.append(u"| %s | %s | %s | %s | %s | %s |" % (x[u"doc"], x[u"id"], x[u"向き"], cell(x[u"P21 の群"] or u"(GROUNDED でない)"),
                                                  cell(moved_type(x)), cell((x[u"span"] or u"")[:36])))
    B["E-2 の動いた行"] = u"\n".join(L)
    r2 = recount_cmp(rec[u"E2"])
    B["E-2 の数"] = u"動いた %d(P21 で GROUNDED の行 %d = GROUNDED を離れた %d + GROUNDED のまま参照先だけ動いた %d、P21 で GROUNDED でない行 %d)、新 GROUNDED %d" % (
        r2[u"動いた"], r2[u"離れた"] + r2[u"参照先だけ動いた"], r2[u"離れた"], r2[u"参照先だけ動いた"], r2[u"動いた"] - r2[u"離れた"] - r2[u"参照先だけ動いた"], r2[u"新 GROUNDED"])
    g = rec[u"E2"][u"P21 の GROUNDED の群"]
    mg = r2[u"動いた GROUNDED の群"]
    L = [u"| 群(P21 で GROUNDED) | 件数 | 動いた | うち GROUNDED を離れた |", u"|---|---:|---:|---:|"]
    for k in (u"Prior1Year・手がかり無し", u"Prior1Year・手がかりあり", u"当期", u"pointer が 1 本でない"):
        L.append(u"| %s | %d | %d | %d |" % (k, g[k], mg.get(k, 0), r2[u"離れた行の群"].get(k, 0)))
    B["E-2 の群"] = u"\n".join(L)
    L = [u"| 型(人の読み) | 件数 |", u"|---|---:|"]
    tc = tally(rec[u"E2"][u"動いた行"], moved_type)
    for k in sorted(tc):
        L.append(u"| %s | %d |" % (k, tc[k]))
    B["E-2 の型"] = u"\n".join(L)
    ps = rec[u"postscript_2026-10-20"]
    B["追記 2026-10-20"] = u"\n".join([u"- 四か所目の直し: %s" % ps[u"4 か所目の直し"], u"- E-7 の判定: %s" % ps[u"E-7 の判定"]])
    B.update(stage2_blocks(rec))
    return B



# ----------------------------------------------------------------------------------------------------------------
# 文書の散文の数(記録から作る。文書はこの字を含まなければならない)。散文に数を手で書かない ― 数のある文はここに置く。
def pct1(a, b):
    return u"%.1f%%" % (100.0 * a / b)


def prose_facts(rec):
    P = {}
    pr = rec[u"予測の判定"]
    hit = sum(1 for v in pr.values() if v[u"判定"] == u"当たり")
    miss = sum(1 for v in pr.values() if v[u"判定"] == u"外れ")
    P["pred"] = u"**予測 機械判定 当たり %d / 外れ %d**(E-1〜E-5・E-7。E-6 は人の読み、E-8 は段 2 なので判定しない)。" % (hit, miss)
    d = rec[u"E7"][u"engine の差分"]
    rr, vv = d["adapters/xbrl/recipes.py"], d["adapters/xbrl/vocabulary.py"]
    P["head"] = u"engine の直し: `adapters/xbrl/recipes.py` 挿入 %d・削除 %d、`adapters/xbrl/vocabulary.py` 挿入 %d・削除 %d、`core/` %d 行。" % (
        rr[u"挿入"], rr[u"削除"], vv[u"挿入"], vv[u"削除"], d[u"core/"][u"差の行数"])
    # E-1
    c1 = recount_e1(rec[u"E1"][u"行"])
    vs = rec[u"E1"][u"対照: P21 の再計算と穴 B の記録"]
    P["e1"] = (u"- **E-1(%s)**: 穴 B の注入 %d 件を P22 で検証し直すと、通した(GROUNDED のまま)のは **%s**(P21 の再計算は %s)。止めた(VALUE_MISMATCH)は %s。"
               u"前期へ移って通した件数は P21 %d → P22 %d。P21 の再計算は穴 B の記録の %d 行と 1 行ずつ比べて、違った行 %d(道具の再現)。") % (
        pr["E-1"][u"判定"], c1[u"注入"], F(c1[u"P22"][u"通した"], c1[u"注入"]), F(c1[u"P21"][u"通した"], c1[u"注入"]),
        F(c1[u"P22"][u"止めた"], c1[u"注入"]), c1[u"P21"][u"Prior1Year へ移った"], c1[u"P22"][u"Prior1Year へ移った"], vs[u"記録の行"], vs[u"違った行"])
    still = [r for r in rec[u"E1"][u"行"] if e1_kind(r[u"P22"], r) in PASSED_KINDS]
    P["e1_still"] = u"- P22 で通した %d 件: %s。" % (len(still), u"・".join(u"%s %s(%s → %s、%s)" % (r[u"書類"], r[u"id"], r[u"元の字"], r[u"後の字"], r[u"単位"]) for r in still))
    P["e1_stop"] = u"- 止めた %d 件の state は %s。" % (c1[u"P22"][u"止めた"], u"・".join(u"%s %d" % kv for kv in sorted(c1[u"P22 の止めた行の state"].items())))
    P["e1_trans"] = u"- P21 → P22 の遷移: %s。" % u"、".join(u"%s %d" % kv for kv in sorted(c1[u"遷移"].items()))
    P["e1_other"] = u"- その他 %d 件の内訳: %s(穴 B の記録でも『その他』。注入の道具側の事情で P21 でも同じ)。" % (
        c1[u"P22"][u"その他"], u"・".join(u"%s %d" % kv for kv in sorted(rec[u"E1"][u"集計"][u"P22 のその他の内訳(state, reason)"].items())))
    P["e1_cue"] = u"- 通した行の注入後の文で `_prior_cue` か `_prior_cue_clause` が真のもの: %d(封 §0 の外れ方の数)。" % rec[u"E1"][u"集計"][u"P22 で通した行のうち 手がかり(_prior_cue か _prior_cue_clause)が注入後の文で真"]
    # E-2
    r2 = recount_cmp(rec[u"E2"])
    g = rec[u"E2"][u"P21 の GROUNDED の群"]
    mg = r2[u"動いた GROUNDED の群"]
    lv = r2[u"離れた行の群"]
    n_g = r2[u"離れた"] + r2[u"参照先だけ動いた"]
    P["e2"] = (u"- **E-2(%s)**: 経営分析の文を持つ %d 書類の無改変(%d claim)で、P21 で GROUNDED の %d 行のうち動いたのは %d 行"
               u"(GROUNDED を離れた %d・GROUNDED のまま参照先だけ動いた %d)、P21 で GROUNDED でない行で動いたのは %d、新 GROUNDED %d。") % (
        pr["E-2"][u"判定"], r2[u"書類の数"], r2[u"claims"], rec[u"E2"][u"集計"][u"P21 の GROUNDED"], n_g, r2[u"離れた"], r2[u"参照先だけ動いた"],
        r2[u"動いた"] - n_g, r2[u"新 GROUNDED"])
    P["e2_groups"] = (u"- 群別(P21 で GROUNDED): 手がかり無し %d 行のうち動いた %d(離れた %d)・手がかりあり %d 行のうち動いた %d(離れた %d)・"
                      u"当期 %d 行のうち動いた %d・pointer が 1 本でない %d 行のうち動いた %d。") % (
        g[u"Prior1Year・手がかり無し"], mg.get(u"Prior1Year・手がかり無し", 0), lv.get(u"Prior1Year・手がかり無し", 0),
        g[u"Prior1Year・手がかりあり"], mg.get(u"Prior1Year・手がかりあり", 0), lv.get(u"Prior1Year・手がかりあり", 0),
        g[u"当期"], mg.get(u"当期", 0), g[u"pointer が 1 本でない"], mg.get(u"pointer が 1 本でない", 0))
    P["e2_base"] = u"- 封 §0 の数 26 / 190 / 1,726 / 4,267 は P21 側の数え直しで再現した: 手がかり無し %d・手がかりあり %d・当期 %d・全 GROUNDED %d。" % (
        g[u"Prior1Year・手がかり無し"], g[u"Prior1Year・手がかりあり"], g[u"当期"], rec[u"E2"][u"集計"][u"P21 の GROUNDED"])
    tc = tally(rec[u"E2"][u"動いた行"], moved_type)
    nA, nB, nC, nD, nE = [tc.get(t, 0) for t in (T_A, T_B, T_C, T_D, T_E)]
    P["e2_types"] = u"- 動いた %d 行の型(人の読み): A %d・B %d・C %d・D %d・E %d。" % (r2[u"動いた"], nA, nB, nC, nD, nE)
    P["e2_dest"] = u"- GROUNDED を離れた %d 行の行き先: %s。" % (r2[u"離れた"], u"・".join(u"%s %d" % kv for kv in sorted(r2[u"離れた行の向き"].items())))
    # E-6 : 3 つの分母
    leave, moved_all = r2[u"離れた"], r2[u"動いた"]
    P["e6"] = (u"- **E-6(人の読み)**: A「減少額が前期の残高と一致」の率は分母の選び方で変わる。GROUNDED を離れた行 %d を分母にすると %d / %d = %s、"
               u"動いた GROUNDED の行 %d を分母にすると %d / %d = %s、動いた全 state の行 %d を分母にすると %d / %d = %s。"
               u"封の予測『過半』は『動いた無改変の行(E-2 の幅の GROUNDED を離れた行)』の読みでは %s、ほかの分母では %s。") % (
        leave, nA, leave, pct1(nA, leave), n_g, nA, n_g, pct1(nA, n_g), moved_all, nA, moved_all, pct1(nA, moved_all),
        u"届いた" if 2 * nA > leave else u"届かない", u"届く" if (2 * nA > n_g and 2 * nA > moved_all) else u"届かない")
    P["e6_mark"] = u"- 機械の印(span 前後に『減少』『減』): 離れた %d 行のうち %d、A の %d 行と一致 = %s。" % (
        leave, r2[u"離れた行のうち 文に 減少・減"], nA, u"はい" if r2[u"離れた行のうち 文に 減少・減"] == nA else u"いいえ")
    P["e6_types"] = u"GROUNDED を離れた %d 行の型: A %d・B %d・C %d。参照先だけ動いた %d 行の型: D %d・E %d。" % (leave, nA, nB, nC, r2[u"参照先だけ動いた"], nD, nE)
    # E-3
    r3 = recount_cmp(rec[u"E3"])
    n3 = r3[u"離れた"] + r3[u"参照先だけ動いた"]
    P["e3"] = (u"- **E-3(%s)**: 名指しの直しの無改変 %d 書類(%d claim、cache に無い書類 %d、67 書類の中に入る書類 %d)で、動いた行 %d"
               u"(P21 で GROUNDED の行 %d = 離れた %d + 参照先だけ動いた %d)、新 GROUNDED %d。") % (
        pr["E-3"][u"判定"], r3[u"書類の数"], r3[u"claims"], len(rec[u"E3"][u"キャッシュに無い書類"]), len(rec[u"E3"][u"40 のうち 67 と重なる書類"]),
        r3[u"動いた"], n3, r3[u"離れた"], r3[u"参照先だけ動いた"], r3[u"新 GROUNDED"])
    # E-4
    c4 = recount_e4(rec[u"E4"][u"行"])
    P["e4"] = (u"- **E-4(%s)**: 段 2 の材料(%d 行・注入 %d)で Core 自身の T6 は P22 で %s(段 2 の記録は %s、P21 の再計算は %s)。"
               u"全注入では P22 で GROUNDED %s。Core 自身が動いた行 %d(型を問わず)、対照の違い %d。α 型を当てた %d 行を再計算して記録との差 %d。") % (
        pr["E-4"][u"判定"], c4[u"行"], c4[u"注入"], F(c4[u"T6 P22 GROUNDED"], c4[u"T6"]), F(c4[u"T6 記録 GROUNDED"], c4[u"T6"]),
        F(c4[u"T6 P21 再計算 GROUNDED"], c4[u"T6"]), F(c4[u"注入 P22 GROUNDED"], c4[u"注入"]), c4[u"動いた"], c4[u"対照の違い"], c4[u"α 型"], c4[u"α 型の違い"])
    P["e4_t6"] = u"- T6 の Core 自身 P22 の state: %s。" % u"・".join(u"%s %d" % kv for kv in sorted(rec[u"E4"][u"集計"][u"T6 の Core 自身 P22 の state"].items()))
    # E-5
    e5 = rec[u"E5"]
    P["e5"] = (u"- **E-5(%s)**: 儀式(同梱の 1 書類)で 通した %s・止めた %s(P21 の再計算 通した %s・止めた %s、儀式の記録と違った行 %d)。"
               u"動いた行 %s。注入の対象から外れた行 %d・対象に増えた行 %d・両方に在る行で結果が同じ %d。") % (
        pr["E-5"][u"判定"], e5[u"通した P22"][u"字"], e5[u"止めた P22"][u"字"], e5[u"通した P21(対照)"][u"字"], e5[u"止めた P21(対照)"][u"字"],
        e5[u"対照: P21 の再計算が儀式の記録と違った行"], u"・".join(u"%s %s" % (x[u"id"], x[u"型"]) for x in e5[u"P21 → P22 で結果が動いた行"]),
        len(e5[u"P22 の注入の対象から外れた行(P21 の対象に在った)"]), len(e5[u"P22 の注入の対象に増えた行"]), e5[u"他の行(両方に在る)で結果が同じ"])
    sp = e5[u"素の書類 P22"][u"state の分布"]
    so = e5[u"素の書類 P21"][u"state の分布"]
    P["e5_plain"] = u"- 素の書類(注入なし)の claim %d の state: P21 %s、P22 %s。素の書類で動いた claim %d。" % (
        e5[u"素の書類 P22"][u"claim"], json.dumps(so, ensure_ascii=False, sort_keys=True), json.dumps(sp, ensure_ascii=False, sort_keys=True),
        len(e5[u"素の書類で P21 → P22 で動いた claim"]))
    # E-7
    e7 = rec[u"E7"]
    t = e7.get(u"既存試験", [])
    P["e7"] = u"- **E-7(%s)**: engine の差分は %s 既存試験(封の 3 か所を直した後): %s。封の 3 か所のほかに直した既存試験: %d 件。" % (
        pr["E-7"][u"判定"], P["head"][len(u"engine の直し: "):], u"・".join(u"`%s` → %s" % (x[u"コマンド"], x[u"最後の行"]) for x in t) or u"(無し)",
        len(e7.get(u"封の 3 か所のほかに直した既存試験", [])))
    # cost (section 9)
    P["cost1"] = u"- P21 で GROUNDED の %d 行のうち **GROUNDED を離れたのは %d 行 = %s**(A %d・B %d・C %d)。参照先だけ動いた %d 行は GROUNDED のまま。" % (
        rec[u"E2"][u"集計"][u"P21 の GROUNDED"], leave, pct1(leave, rec[u"E2"][u"集計"][u"P21 の GROUNDED"]), nA, nB, nC, r2[u"参照先だけ動いた"])
    P["cost2"] = u"- 当期の文として正しい数を落とす行は A + C = %d 行 = %s(A は保留へ、C は不一致へ)。B は怪しかった GROUNDED を止めた行。" % (
        nA + nC, pct1(nA + nC, rec[u"E2"][u"集計"][u"P21 の GROUNDED"]))
    P["cost3"] = u"- 封 §0 の見積もり(手がかり無し %d 行 = %s)に対し、実測で手がかり無しの群から GROUNDED を離れたのは %d 行。見積もりに無かった C は手がかりありの %d 行のうち %d 行(%s)。" % (
        g[u"Prior1Year・手がかり無し"], pct1(g[u"Prior1Year・手がかり無し"], rec[u"E2"][u"集計"][u"P21 の GROUNDED"]), lv.get(u"Prior1Year・手がかり無し", 0),
        g[u"Prior1Year・手がかりあり"], lv.get(u"Prior1Year・手がかりあり", 0), pct1(lv.get(u"Prior1Year・手がかりあり", 0), g[u"Prior1Year・手がかりあり"]))
    P["cost4"] = u"- 見返り: 穴 B の金額で前期へ移って通した件数 %d → %d。段 2 の Core 自身 T6 の GROUNDED %d → %d。儀式で参照先が前期へ移って通した N125・N199 は VALUE_MISMATCH。" % (
        c1[u"P21"][u"Prior1Year へ移った"], c1[u"P22"][u"Prior1Year へ移った"], c4[u"T6 記録 GROUNDED"], c4[u"T6 P22 GROUNDED"])
    for k, name in (("E-2", "p2"), ("E-3", "p3"), ("E-5", "p5")):
        P[name] = u"- %s の部分の判定: %s" % (k, u"・".join(u"%s: %s" % (a, u"はい" if b else u"いいえ") for a, b in pr[k][u"部分の判定"].items()))
    # mutation + pins
    P["engine_sha"] = u"- 測った時点の engine: `recipes.py` sha16 `%s`・`vocabulary.py` sha16 `%s`。" % (
        ENGINE_AT_MEASURE["adapters/xbrl/recipes.py"], ENGINE_AT_MEASURE["adapters/xbrl/vocabulary.py"])
    P["secs"] = u"記録の所要秒: %s。" % json.dumps(rec[u"所要秒"], ensure_ascii=False, sort_keys=True)
    P.update(stage2_facts(rec))      # 段 2(2026-10-20)の節の数
    return P


def mutation_table(rec):
    m = rec[u"変異(engine。手で走らせた)"]
    L = [u"| # | 変異 | 予測(赤の本数) | 実測(%d 本版) | 判定 | 実測(%d 本版・参考) |" % (m[u"試験の本数(予測と同じ版)"], m[u"試験の本数"]), u"|---|---|---|---|---|---|"]
    for x in m[u"行"]:
        L.append(u"| %s | %s | %s | %s | %s | %s |" % (x[u"#"], cell(x[u"変異"]), cell(x[u"予測"]), cell(x[u"実測"]), x[u"判定"], cell(x[u"実測(最終版・参考)"])))
    return u"\n".join(L)


def check_mutation_record(rec):
    m = rec[u"変異(engine。手で走らせた)"]
    assert [x[u"#"] for x in m[u"行"]] == [u"M-%d" % i for i in (1, 2, 3, 4, 5, 6, 8, 9, 7)]
    for x in m[u"行"]:
        lo, hi = [int(v) for v in re.findall(r"\d+", x[u"予測"])[:2]] if u"〜" in x[u"予測"] else (int(re.findall(r"\d+", x[u"予測"])[0]), 10 ** 6)
        n = int(re.findall(r"(\d+) 本", x[u"実測"])[0])
        want = u"当たり" if (lo <= n <= hi if u"以上" not in x[u"予測"] else n >= lo) else u"外れ"
        if u"ちょうど" in x[u"予測"]:
            want = u"当たり" if n == lo else u"外れ"
        assert x[u"判定"] == want, (x[u"#"], x[u"予測"], x[u"実測"], x[u"判定"])
    assert m[u"engine の sha16 は変異の前後で一致"] is True


#: 散文に残ってよい数字の並び(記録に縛られない構造上の字)。空にできるよう、散文は漢数字で書く。
ALLOWED_RESIDUAL = []


def residual_numbers(doc, rec):
    u"""文書から、記録から作った表・文と、コード片・識別子・日付・節の番号を除いた残りの数字の並び。散文に手で書いた数がここに出る。"""
    t = doc
    pieces = list(render_blocks(rec).values()) + list(prose_facts(rec).values()) + [mutation_table(rec), rec[u"変異(engine。手で走らせた)"][u"注記"]]
    for v in sorted(pieces, key=len, reverse=True):
        t = t.replace(v, u"")
    t = re.sub(r"```.*?```", u"", t, flags=re.S)
    t = re.sub(r"`[^`]*`", u"", t)
    t = re.sub(r"[A-Za-z_][A-Za-z_0-9\-]*\d[A-Za-z_0-9\-]*", u"", t)      # S100YMFV・N076・E-1・M-1・P22・Prior1Year・sha16 など
    t = re.sub(r"(?m)^#+ [\d\-]+\.?", u"", t)                # 見出しの節番号
    t = re.sub(r"段 \d", u"", t)                                 # 工程の名前(段 1・段 2)
    t = t.replace(u"0 USD", u"")
    t = re.sub(r"§[\d\-]+", u"", t)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    return re.findall(r"\d[\d,\.]*", t)


# ----------------------------------------------------------------------------------------------------------------
# 段 2(2026-10-20、既定 P21 -> P22)
def stage2_facts(rec):
    u"""段 2 の節(§14)の数のある文。記録の新欄 ``stage2_default_2026-10-20`` と二本の儀式の記録から作る(散文に手で数を書かない)。"""
    s2 = rec[STAGE2]
    e1, e2, e5, ctrl = s2[u"E1"], s2[u"E2"], s2[u"E5"], s2[u"対照: 既定を P21 に戻す変異(比較器が差を拾えるか)"]
    P = {}
    P["s2_e1"] = (u"- **E-1(profile 省略)**: 穴 B の注入 %d 件を、profile を省いた `verify_document`(= 既定)で検証し直すと、通した(GROUNDED のまま)は %s・"
                  u"止めた(VALUE_MISMATCH)は %s・その他は %s。段 1 の P22 の欄と 1 行ずつ比べて違った行 %d、記録に無い行 %d。") % (
        e1[u"今回の行"], F(e1[u"通した(GROUNDED のまま)"][u"件"], e1[u"通した(GROUNDED のまま)"][u"分母"]),
        F(e1[u"止めた(VALUE_MISMATCH)"][u"件"], e1[u"止めた(VALUE_MISMATCH)"][u"分母"]), F(e1[u"その他"][u"件"], e1[u"その他"][u"分母"]),
        e1[u"段 1 の P22 の欄と違った行"], e1[u"記録に無い行"])
    P["s2_e2"] = (u"- **E-2(profile 省略)**: 経営分析の文を持つ %d 書類(%d claim)の無改変を P21 と既定で比べると、動いた行は %d(GROUNDED を離れた %d・新 GROUNDED %d)。"
                  u"段 1 の記録の動いた行 %d と過不足なく同じで、P21・P22 の欄が違った行 %d、記録に無い動いた行 %d。") % (
        e2[u"書類"], e2[u"claims"], e2[u"既定と P21 で動いた行"], e2[u"GROUNDED を離れた"], e2[u"新 GROUNDED"],
        e2[u"記録(段 1)の動いた行"], e2[u"記録の動いた行のうち違った行(P21・P22 の欄)"], e2[u"記録に無い動いた行"])
    P["s2_e5"] = (u"- **E-5(儀式、既定)**: 通した %s・止めた %s。P21 の記録に段 1 の動いた行・外れた行を当てて作った期待 %d 行と 1 行ずつ比べて違った行 %d、"
                  u"採り直した儀式の記録と違う欄 %d。素の書類 %d claim のうち、既定と P22 明示で違った claim %d。素の書類の state(既定): %s。") % (
        e5[u"通した"][u"字"], e5[u"止めた"][u"字"], e5[u"期待(P21 の記録 + 段 1 の動いた行・外れた行)の行"], e5[u"期待と違った行"],
        len(e5[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"]), e5[u"素の書類の claim"], e5[u"素の書類: 既定と P22 明示で違った claim"],
        json.dumps(e5[u"素の書類の state の分布(既定)"], ensure_ascii=False, sort_keys=True))
    pr = rec[u"予測の判定"]
    hit = sum(1 for k, v in pr.items() if k != "E-8" and v[u"判定"] == u"当たり")
    miss = sum(1 for k, v in pr.items() if k != "E-8" and v[u"判定"] == u"外れ")
    P["s2_e8"] = (u"- **E-8 の判定**: E-8 の条件(E-1〜E-7 が当たる)は満たされていない(当たり %d / 外れ %d)。人間の承認(2026-10-20「任せる」)で段 2 に進んだ。"
                  u"全緑の部分だけ成立(tests/measure・tests/adapters/xbrl 緑。axis3 の LATER_ENGINE_COMMITS は commit の直後に赤 1 本 → 次の便で宣言、段 1 と同じ扱い)。"
                  u"記録の 予測の判定.E-8 は『判定しない(段 2)』のまま。") % (hit, miss)
    P["s2_total"] = u"- 差のあった行の合計 %d(差 0 の行: E-1 %d・E-2 %d・E-5 %d)。" % (
        s2[u"差のあった行の合計"], s2[u"差 0 の行数"][u"E-1"], s2[u"差 0 の行数"][u"E-2"], s2[u"差 0 の行数"][u"E-5"])
    P["s2_ctrl"] = (u"- 『差 0』が自分の欠陥でないことの対照: `vocabulary.DEFAULT_PROFILE` を実行中だけ P21 に戻して %s の注入 %d 件を同じ比較器に当てると、"
                    u"段 1 の P22 の欄と違った行は %d。") % (ctrl[u"書類"], ctrl[u"比べた行"], ctrl[u"段 1 の P22 の欄と違った行"])
    p21, p22 = jload(RITUAL_P21), jload(RITUAL_P22)
    P["s2_ritual"] = (u"- 儀式(同梱の 1 書類)の記録: P21 のとき 通した %s・止めた %s → P22(既定)で 通した %s・止めた %s。注入の対象 %d → %d。"
                      u"素の書類の GROUNDED %d → %d・VALUE_MISMATCH %d → %d。") % (
        p21[u"通した"][u"字"], p21[u"止めた"][u"字"], p22[u"通した"][u"字"], p22[u"止めた"][u"字"],
        p21[u"注入"][u"注入の対象(GROUNDED の site)"], p22[u"注入"][u"注入の対象(GROUNDED の site)"],
        p21[u"素の書類"][u"state の分布"]["GROUNDED"], p22[u"素の書類"][u"state の分布"]["GROUNDED"],
        p21[u"素の書類"][u"state の分布"]["VALUE_MISMATCH"], p22[u"素の書類"][u"state の分布"]["VALUE_MISMATCH"])
    tc = tally(rec[u"E2"][u"動いた行"], moved_type)
    P["s2_cost"] = (u"- 代価(製品の経路で再掲): P21 で GROUNDED の %d 行のうち GROUNDED を離れたのは %d 行(A %d・B %d・C %d)。"
                    u"C は正しい前期の文が不一致になる行(下の表)。参照先だけ動いた %d 行(D %d・E %d)は GROUNDED のまま。") % (
        rec[u"E2"][u"集計"][u"P21 の GROUNDED"], e2[u"GROUNDED を離れた"], tc.get(T_A, 0), tc.get(T_B, 0), tc.get(T_C, 0),
        recount_cmp(rec[u"E2"])[u"参照先だけ動いた"], tc.get(T_D, 0), tc.get(T_E, 0))
    if u"既存試験" in s2:
        t = s2[u"既存試験"][0]
        P["s2_tests"] = u"- 既存試験 `%s` → rc %d・%s。" % (t[u"コマンド"], t[u"rc"], t[u"最後の行"])
    return P


def stage2_blocks(rec):
    L = [u"| doc | id | P21 → P22 | 文の抜粋 |", u"|---|---|---|---|"]
    for x in rec[u"E2"][u"動いた行"]:
        if moved_type(x) == T_C:
            L.append(u"| %s | %s | %s | %s |" % (x[u"doc"], x[u"id"], x[u"向き"], cell((x[u"span"] or u"")[:36])))
    return {"段 2 の C 行": u"\n".join(L)}


def check_stage2(rec):
    u"""記録の新欄を、段 1 の記録の行から独立に数え直した値・二本の儀式の記録と突き合わせる。壊した記録で赤くなる。"""
    s2 = rec[STAGE2]
    assert s2[u"DEFAULT_PROFILE"] == "P22", u"段 2 の測定は既定が P22 の時点"
    assert s2[u"recipes.py の sha16"] == ENGINE_AT_STAGE2["adapters/xbrl/recipes.py"] == ENGINE_AT_MEASURE["adapters/xbrl/recipes.py"], u"recipes.py は段 2 でも 0 行"
    assert s2[u"vocabulary.py の sha16"] == ENGINE_AT_STAGE2["adapters/xbrl/vocabulary.py"], u"vocabulary.py は宣言された遷移の値(段 2 の後)"
    assert s2[u"費用"] == u"0 USD"
    # E-1: 段 1 の記録の P22 の欄の独立な数え直しと一致
    c1 = recount_e1(rec[u"E1"][u"行"])
    e1 = s2[u"E1"]
    assert e1[u"記録(段 1)の行"] == c1[u"注入"] == e1[u"今回の行"], u"E-1 の行の数"
    assert e1[u"段 1 の P22 の欄と違った行"] == 0 and e1[u"記録に無い行"] == 0 and e1[u"違った行の id"] == [], u"E-1 は差 0"
    n = c1[u"注入"]
    assert e1[u"通した(GROUNDED のまま)"] == {u"件": c1[u"P22"][u"通した"], u"分母": n, u"率": round(100.0 * c1[u"P22"][u"通した"] / n, 1)}
    assert e1[u"止めた(VALUE_MISMATCH)"] == {u"件": c1[u"P22"][u"止めた"], u"分母": n, u"率": round(100.0 * c1[u"P22"][u"止めた"] / n, 1)}
    assert e1[u"その他"] == {u"件": c1[u"P22"][u"その他"], u"分母": n, u"率": round(100.0 * c1[u"P22"][u"その他"] / n, 1)}
    assert e1[u"通した のうち参照先が Prior1Year"][u"件"] == c1[u"P22"][u"Prior1Year へ移った"]
    # E-2
    r2 = recount_cmp(rec[u"E2"])
    e2 = s2[u"E2"]
    assert e2[u"書類"] == r2[u"書類の数"] and e2[u"claims"] == r2[u"claims"], u"E-2 の書類・claim"
    assert e2[u"記録(段 1)の動いた行"] == r2[u"動いた"] == e2[u"既定と P21 で動いた行"], u"E-2 の動いた行"
    assert e2[u"GROUNDED を離れた"] == r2[u"離れた"] and e2[u"新 GROUNDED"] == r2[u"新 GROUNDED"] == 0
    assert e2[u"記録の動いた行のうち違った行(P21・P22 の欄)"] == 0 and e2[u"記録に無い動いた行"] == 0 and e2[u"違った行"] == [], u"E-2 は差 0"
    # E-5: 儀式の二本の記録と、段 1 の E-5
    e5, e5r = s2[u"E5"], rec[u"E5"]
    p22 = jload(RITUAL_P22)
    p21 = jload(RITUAL_P21)
    assert e5[u"通した"] == p22[u"通した"] and e5[u"止めた"] == p22[u"止めた"], u"E-5 は採り直した儀式の記録と同じ数"
    assert e5[u"通した"][u"件"] == e5r[u"通した P22"][u"件"] and e5[u"止めた"][u"件"] == e5r[u"止めた P22"][u"件"], u"E-5 は段 1 の E-5 の P22 の数と同じ"
    assert e5[u"今回の行"] == e5[u"期待(P21 の記録 + 段 1 の動いた行・外れた行)の行"] == e5r[u"注入の対象"] == len(p22[u"注入の一覧"]), u"E-5 の行の数"
    assert len(p21[u"注入の一覧"]) - len(e5r[u"P22 の注入の対象から外れた行(P21 の対象に在った)"]) + len(e5r[u"P22 の注入の対象に増えた行"]) == e5[u"今回の行"]
    assert e5[u"期待と違った行"] == 0 and e5[u"違った行の id"] == [], u"E-5 は差 0"
    assert e5[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"] == [], u"E-5 は採り直した記録と同じ中身"
    assert e5[u"素の書類: 既定と P22 明示で違った claim"] == 0 and e5[u"素の書類の claim"] == p22[u"素の書類"][u"claim"]
    assert e5[u"素の書類の state の分布(既定)"] == p22[u"素の書類"][u"state の分布"] == e5r[u"素の書類 P22"][u"state の分布"]
    # 合計・差 0 の行
    assert s2[u"差 0 の行数"] == {u"E-1": e1[u"今回の行"] - e1[u"段 1 の P22 の欄と違った行"], u"E-2": e2[u"記録(段 1)の動いた行"] - e2[u"記録の動いた行のうち違った行(P21・P22 の欄)"],
                              u"E-5": e5[u"今回の行"] - e5[u"期待と違った行"]}
    total = (e1[u"段 1 の P22 の欄と違った行"] + e1[u"記録に無い行"] + e2[u"記録の動いた行のうち違った行(P21・P22 の欄)"] + e2[u"記録に無い動いた行"]
             + e5[u"期待と違った行"] + e5[u"素の書類: 既定と P22 明示で違った claim"] + len(e5[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"]))
    assert s2[u"差のあった行の合計"] == total == 0, u"差のあった行の合計"
    # 対照: 比較器が差を拾える(『0 件』が自分の欠陥でない)
    c = s2[u"対照: 既定を P21 に戻す変異(比較器が差を拾えるか)"]
    want = [r for r in rec[u"E1"][u"行"] if r[u"書類"] == c[u"書類"]]
    differ = sum(1 for r in want if r[u"P21(対照)"] != r[u"P22"] and (r[u"P21(対照)"][u"state"], r[u"P21(対照)"][u"pointers"]) != (r[u"P22"][u"state"], r[u"P22"][u"pointers"]))
    assert c[u"比べた行"] == len(want) and c[u"段 1 の P22 の欄と違った行"] > 0, u"対照の変異で差が出ていない(比較器が差を拾えない)"
    assert c[u"段 1 の P22 の欄と違った行"] == differ, u"対照の違った行の数が、段 1 の記録の P21 の欄と P22 の欄の差と合わない"
    if u"既存試験" in s2:
        t = s2[u"既存試験"][0]
        assert t[u"rc"] == 0 and u" passed" in t[u"最後の行"] and u"failed" not in t[u"最後の行"] and u"error" not in t[u"最後の行"], u"既存試験が緑でない"


def check_default_note(src):
    u"""vocabulary.py の字: 日付つきの決定の注記・P21 以前の注記が消えていない。既定は P22(2026-10-20 の段 2)から、2026-10-23 の P26 の段 2(封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)で P26。"""
    i = src.index("\nDEFAULT_PROFILE = ")
    note = src[:i][src[:i].index(u"# **既定 profile(人間の決定 2026-10-13、第 2 段階)"):]
    for lit in (u"# 2026-10-14 の人間の決定で P16 -> P20。", u"# 2026-10-20 に P20 -> P21(段 2)。",
                u"# 2026-10-20 に P21 -> P22(期を縛る P22 の段 2)。人間の決定 2026-10-20「任せる」。",
                u"段 1 3320c8c の結果", u"客の席の回し直し", u"**P21 の字は消さず**", u"P21 の既定は 2026-10-20 a516288"):
        assert lit in note, lit
    assert note.index(u"# 2026-10-14 の人間の決定で P16 -> P20。") < note.index(u"# 2026-10-20 に P20 -> P21(段 2)。") < note.index(u"# 2026-10-20 に P21 -> P22(期を縛る P22 の段 2)。")
    assert u"# 2026-10-23 に P22 -> P26(P26 の段 2)。" in src and u"**P22 の字は消さず**" in src, u"P26 の段 2 の注記が無い"      # 2026-10-23 追記
    found = re.findall(r'(?m)^DEFAULT_PROFILE = "(P\d+)"$', src)
    assert found == ["P27"], found      # 2026-10-28: P26 の段 2 の後は P26 だった。P27 の段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で P27


FROZEN_SRC = os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py")


def check_frozen_generation(generations, current):
    u"""``fixtures/frozen_bundle_sha.py`` の世代: 一番新しい世代がいまの作業木の束ねた sha と一致し、段 2(期を縛る P22)の宣言として書かれている。
    (世代の追加は pin の遷移の宣言の一つ。これまでどの門も作業木と突き合わせていなかった = 世代を足し忘れても緑 ― 2026-10-20 の段 2 の変異 MUT-7 が黙って見つけた。)"""
    assert generations, u"世代が無い"
    sha, why = generations[-1]
    assert sha == current, u"いまの作業木の束ねた sha が最新の世代と違う(世代を足し忘れている): %s != %s" % (current, sha)
    # 2026-10-21 追記(pin の遷移): 後の封(丸めの帯 P23 の段 1、docs/XBRL_ROUNDING_SEAL_2026-10-21.md)が世代を 1 つ足した後は、段 2 の宣言は
    # 最新の世代の 1 つ前になる。最新の世代がその後の封の宣言であるときだけ 1 つ前を段 2 として読む(それ以外は従来どおり最新が段 2)。
    # 2026-10-21 追記(pin の遷移): 語彙の登録と枠の取り直し P24 の段 1(docs/XBRL_VOCAB_SEAL_2026-10-21.md)が世代をもう 1 つ足した後は、
    # 段 2 の宣言は最新の世代の 2 つ前になる(後の封の宣言を新しい順に 1 つずつ飛ばして読む)。
    i = len(generations) - 1
    # 2026-10-21 追記(pin の遷移): 最後の枝 P25 の段 1(docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md)が世代をもう 1 つ足した後は、段 2 の宣言は最新の世代の 3 つ前になる。
    # 2026-10-21 追記(pin の遷移): 顧客向けの日本語の報告形(docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md。新しい module report_customer.py を足して 36 → 37 本)が世代をもう 1 つ足した後は、
    # 段 2 の宣言は最新の世代の 4 つ前になる(P23〜P25 の封と同じ型)。
    # 2026-10-21 追記(pin の遷移): 顧客向けの報告形の直し(docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md。report_customer.py の中身だけを直し、37 本のまま世代をもう 1 つ足した)の後は、
    # 段 2 の宣言は最新の世代の 5 つ前になる。
    # 2026-10-22 追記(pin の遷移): P26 の段 1(docs/XBRL_P26_SEAL_2026-10-21.md。engine 5 file を変え 37 本のまま世代をもう 1 つ足した)の後は、段 2 の宣言は最新の世代の 6 つ前になる。
    # 2026-10-23 追記(pin の遷移): 既定を P22 -> P26 に切り替える 段 2(docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md。vocabulary.py だけ、37 本のまま世代をもう 1 つ足した)の後は、段 2 の宣言は最新の世代の 7 つ前になる。
    # 2026-10-27 追記(pin の遷移): P27 の段 2(docs/XBRL_P27_SEAL_2026-10-27.md。engine 5 file を変え 37 本のまま世代をもう 1 つ足した)の後は、段 2 の宣言は最新の世代の 8 つ前になる。
    # 2026-10-28 追記(pin の遷移): 既定を P26 -> P27 に切り替える 段 2(docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md。vocabulary.py と verify_document.py を変え 37 本のまま世代をもう 1 つ足した)の後は、段 2 の宣言は最新の世代の 9 つ前になる。
    for later in (u"XBRL_DEFAULT_P27_SEAL_2026-10-28", u"XBRL_P27_SEAL_2026-10-27", u"XBRL_DEFAULT_P26_SEAL_2026-10-23", u"XBRL_P26_SEAL_2026-10-21", u"XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21", u"XBRL_CUSTOMER_REPORT_SEAL_2026-10-21", u"XBRL_LASTBRANCH_SEAL_2026-10-21", u"XBRL_VOCAB_SEAL_2026-10-21", u"XBRL_ROUNDING_SEAL_2026-10-21"):
        if later in generations[i][1]:
            i -= 1
            assert i >= 0, u"後の封の宣言の前に段 2 の世代が無い"
    sha, why = generations[i]
    assert u"期を縛る P22 の段 2" in why and u"DEFAULT_PROFILE" in why and u"XBRL_PERIOD_BIND_SEAL_2026-10-20" in why, u"最新の世代の説明が段 2 の宣言でない"
    assert len(set(g[0] for g in generations)) == len(generations), u"世代の sha が重複している"


def check_pinned_scripts(read=None):
    u"""既定で測った記録を持つ measure は測った当時の P21 を字で留める(vocabulary.DEFAULT_PROFILE を読まない)。"""
    import ast
    read = read or (lambda rel: jtext(os.path.join(ROOT, rel)))
    for rel in PINNED_P21_SCRIPTS:
        tree = ast.parse(read(rel))
        consts = [n.value.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PROFILE_AT_MEASURE" for t in n.targets)
                  and isinstance(n.value, ast.Constant)]
        assert consts == ["P21"], (rel, consts)
        reads = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "DEFAULT_PROFILE"]
        assert not reads, (rel, [n.lineno for n in reads])

def check_doc(rec, doc):
    B = render_blocks(rec)
    for k, v in B.items():
        assert v in doc, u"文書に『%s』の表(記録から作った字)が無い" % k
    for k, v in prose_facts(rec).items():
        assert v in doc, u"文書に数のある文『%s』(記録から作った字)が無い" % k
    assert mutation_table(rec) in doc, u"文書に変異の表(記録の写し)が無い"
    assert rec[u"変異(engine。手で走らせた)"][u"注記"] in doc
    assert u"判定しない(段 2)" in doc
    assert doc.count(STAGE2_HEAD) == 1 and doc.index(STAGE2_HEAD) > doc.index(u"## 13. 追記(2026-10-20、司令塔の判断の後)"), u"段 2 の節が末尾に 1 つ在る"
    sec2 = doc[doc.index(STAGE2_HEAD):]
    for lit in (u"`DEFAULT_PROFILE = \"P22\"`", u"人間の承認は 2026-10-20「任せる」", u"E-8 の条件(E-1〜E-7 が当たる)は満たされていない", u"`test_xbrl_axis3_decision.py` の `LATER_ENGINE_COMMITS`",
                u"verify_document.py", u"ritual_2026-10-20_p21.json", u"P21 の字は消していない"):
        assert lit in sec2, lit
    res = residual_numbers(doc, rec)
    assert res == ALLOWED_RESIDUAL, u"文書の散文に、記録に縛られない数が在る: %s" % res


def check_read(rec):
    u"""人の読み ``READ`` が E-2 の動いた行と過不足なく対応する。"""
    keys = [(x[u"doc"], x[u"id"]) for x in rec[u"E2"][u"動いた行"]]
    assert sorted(keys) == sorted(READ), (sorted(set(keys) ^ set(READ)))
    for x in rec[u"E2"][u"動いた行"]:
        t = READ[(x[u"doc"], x[u"id"])]
        assert x[u"P21"][u"state"] == "GROUNDED", (x[u"doc"], x[u"id"], u"P21 で GROUNDED でない行が動いている(主語なしは P21 と同一のはず)")
        if x[u"P22"][u"state"] == "GROUNDED":
            assert t in (T_D, T_E), x[u"id"]
            assert (t == T_E) == (x[u"P22"][u"form"] == "derived_value"), x[u"id"]
        else:
            assert t in (T_A, T_B, T_C), x[u"id"]
            assert (t == T_C) == (x[u"P21 の群"] == u"Prior1Year・手がかりあり"), (x[u"doc"], x[u"id"])
            if t == T_A:
                assert re.search(u"減少|減", x[u"文脈"] or x[u"span"] or u""), (x[u"doc"], x[u"id"])


# ----------------------------------------------------------------------------------------------------------------
def labels_ok():
    try:
        from adapters.xbrl import instance as I
        for _ns, fn, _sha in I.TAXONOMY_LABEL_FILES:
            if not os.path.exists(os.path.join(I.taxonomy_dir(), fn)):
                return False
        return True
    except Exception:
        return False


def have_cache(docs):
    return all(os.path.exists(os.path.join(CACHE, d + ".zip")) for d in docs)


class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_1_record_is_consistent(self):
        check_record(self.rec)

    def test_2_inputs_are_pinned(self):
        check_inputs(self.rec)

    def test_3_judgments_are_recomputed_from_rows(self):
        check_judgments(self.rec, self.seal)

    def test_4_read_covers_the_moved_rows_exactly(self):
        check_read(self.rec)

    def test_5_document_tables_equal_the_record(self):
        check_doc(self.rec, self.doc)

    def test_6_facts_as_measured(self):
        r = self.rec
        c1 = recount_e1(r[u"E1"][u"行"])
        self.assertEqual((c1[u"注入"], c1[u"P22"][u"通した"], c1[u"P22"][u"止めた"], c1[u"P22"][u"その他"]), FACT["e1"])
        self.assertEqual((c1[u"P21"][u"通した"], c1[u"P21"][u"Prior1Year へ移った"]), FACT["e1_p21"])
        c2 = recount_cmp(r[u"E2"])
        self.assertEqual((c2[u"動いた"], c2[u"離れた"], c2[u"参照先だけ動いた"], c2[u"新 GROUNDED"]), FACT["e2"])
        self.assertEqual(c2[u"動いた GROUNDED の群"], FACT["e2_groups"])
        self.assertEqual(r[u"E2"][u"P21 の GROUNDED の群"], FACT["e2_base_groups"])
        self.assertEqual(tally(r[u"E2"][u"動いた行"], moved_type), FACT["e2_types"])
        c3 = recount_cmp(r[u"E3"])
        self.assertEqual((c3[u"動いた"], c3[u"離れた"], c3[u"参照先だけ動いた"], c3[u"新 GROUNDED"], c3[u"claims"]), FACT["e3"])
        c4 = recount_e4(r[u"E4"][u"行"])
        self.assertEqual((c4[u"T6 P22 GROUNDED"], c4[u"T6 記録 GROUNDED"], c4[u"動いた"], c4[u"対照の違い"], c4[u"α 型の違い"]), FACT["e4"])
        e5 = r[u"E5"]
        self.assertEqual((e5[u"通した P22"][u"件"], e5[u"止めた P22"][u"件"], e5[u"注入の対象"]), FACT["e5"])

    def test_7_seal_numbers_are_reproduced_by_the_baseline(self):
        u"""封 §0 の代価 26 / 手がかりあり 190 / 当期 1,726 / 全 GROUNDED 4,267 を、P21 の側の数え直しが再現している。"""
        g = self.rec[u"E2"][u"P21 の GROUNDED の群"]
        self.assertEqual((g[u"Prior1Year・手がかり無し"], g[u"Prior1Year・手がかりあり"], g[u"当期"]), (26, 190, 1726))
        self.assertEqual(26 + 190 + 1726, 1942)
        self.assertEqual(self.rec[u"E2"][u"集計"][u"P21 の GROUNDED"], 4267)
        self.assertEqual(self.rec[u"E1"][u"集計"][u"P21(対照)で通した"][u"件"], 459)

    def test_8_engine_is_the_one_measured_or_a_declared_transition(self):
        for rel, want in sorted(ENGINE_AT_MEASURE.items()):
            got = sha16(rel)
            if got != want and rel in ENGINE_LATER:
                later, seal_rel = ENGINE_LATER[rel]
                added = git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split()
                self.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が測った時点から動いている(段 2 の commit で ENGINE_LATER に遷移を宣言する)**" % rel)

    def test_9_core_is_untouched_and_default_is_p22_from_step_2(self):
        out = git("diff", "--numstat", "4953a4f", "--", "core")
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout.strip(), u"", u"core/ が封の commit から動いている")
        from adapters.xbrl import vocabulary as V
        # 段 1(3320c8c)では P21 のままだった。2026-10-20 の段 2(人間の決定「任せる」)で P22 になった。2026-10-23 の P26 の段 2(封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)で P26 になった。
        self.assertEqual(V.DEFAULT_PROFILE, "P27")      # 2026-10-28: P26 の段 2 の後は P26 だった。P27 の段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で P27
        self.assertTrue(V.PROFILES["P22"].period_bind)
        self.assertIn("P21", V.PROFILES)
        self.assertFalse(V.PROFILES["P21"].period_bind)

    def test_10_e8_is_not_judged_and_the_seal_was_not_edited(self):
        self.assertEqual(self.rec[u"予測の判定"]["E-8"][u"判定"], u"判定しない(段 2)")
        # 封は封の commit から 1 字も直していない(順序の門: 数を見てから封を直さない)
        # 本文(§0〜§4)と予測は封の commit のまま。許すのは末尾の日付つき追記だけ(字を足すだけで、1 字も消さない)。
        orig = git("show", "4953a4f:./" + SEAL_REL)
        self.assertEqual(orig.returncode, 0)
        now = jtext(SEAL)
        self.assertTrue(now.startswith(orig.stdout), u"封の本文が封の commit から変わった")
        tail = now[len(orig.stdout):]
        self.assertTrue(tail == u"" or tail.lstrip(u"\n").startswith(u"## 追記(2026-10-20、段 1 の実測の後。本文と予測は不変)"), tail[:80])
        # 段 2 の追記は 1 点だけ(末尾)。見出しが 2 つ(段 1・段 2)で、段 2 は段 1 の後
        heads = re.findall(r"(?m)^## 追記\(.*$", tail)
        self.assertEqual(heads, [u"## 追記(2026-10-20、段 1 の実測の後。本文と予測は不変)", u"## 追記(2026-10-20、段 2。本文と予測は不変)"])
        self.assertIn(u"`DEFAULT_PROFILE = \"P22\"`", tail)
        self.assertEqual(git("log", "--format=%H", "--", SEAL_REL).stdout.split()[:1] != [], True)

    def test_11_cache_inputs_match_the_record(self):
        inp = self.rec[u"入力の sha256"]
        names = sorted(inp[u"書類 67(経営分析の文を持つ)の sha256"])
        if not have_cache(names):
            self.skipTest(u"cache(~/.cache/audit-core/edinet/*.zip)が無い")
        for d in names:
            self.assertEqual(sha_path(os.path.join(CACHE, d + ".zip")), inp[u"書類 67(経営分析の文を持つ)の sha256"][d], d)
        for rel in ("fixtures/xbrl/point_prior_2026-10-20.json", "fixtures/xbrl/ritual_2026-10-20.json", "fixtures/xbrl/naming_fix/p21_2026-10-20.json",
                    "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json", "fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json"):
            # 段 1 の記録の『ritual_2026-10-20.json』の欄は P21 のときの儀式の記録の sha256。段 2 で ritual_2026-10-20.json は P22 で採り直したので、
            # 同じバイト列の写し ritual_2026-10-20_p21.json に当てる。
            real = rel if rel != "fixtures/xbrl/ritual_2026-10-20.json" else "fixtures/xbrl/ritual_2026-10-20_p21.json"
            self.assertEqual(sha_path(os.path.join(ROOT, real)), inp[rel], rel)
        self.assertEqual(inp["fixtures/xbrl/ritual_2026-10-20.json"], u"dad4c56e7aeeadd1c1d07fe6dc3f844f62be2d127a5e7f9cac10df761ecac6d8")


    def test_12_stage2_record_equals_what_the_stage1_rows_say(self):
        check_stage2(self.rec)

    def test_13_stage2_default_note_and_pins(self):
        check_default_note(jtext(VOCAB))
        check_pinned_scripts()

    def test_14_stage2_changed_only_the_default_in_the_engine(self):
        u"""段 2 の engine の差分は vocabulary.py の DEFAULT_PROFILE と注記だけ。recipes.py は段 1 の値のまま、core/ は 0 行(test_9)。
        2026-10-21 追記(pin の遷移): 後の封(丸めの帯 P23)が作業木の vocabulary.py・recipes.py を動かしたので、段 2 の commit(d0b544c)の
        **commit された file** と段 1 の commit(3320c8c)を比べる(作業木の engine の留めは test_8 の宣言された遷移)。"""
        def blob(rev, rel):
            r = subprocess.run(["git", "show", "%s:./%s" % (rev, rel)], cwd=ROOT, capture_output=True)
            return r.stdout if r.returncode == 0 else None
        a_voc, b_voc = blob("3320c8c", "adapters/xbrl/vocabulary.py"), blob("d0b544c", "adapters/xbrl/vocabulary.py")
        b_rec = blob("d0b544c", "adapters/xbrl/recipes.py")
        if a_voc is None or b_voc is None or b_rec is None:
            return
        self.assertEqual(hashlib.sha256(b_rec).hexdigest()[:16], ENGINE_AT_MEASURE["adapters/xbrl/recipes.py"])
        self.assertEqual(hashlib.sha256(b_voc).hexdigest()[:16], ENGINE_AT_STAGE2["adapters/xbrl/vocabulary.py"])
        old = a_voc.decode("utf-8").splitlines()
        new = b_voc.decode("utf-8").splitlines()
        self.assertEqual(new[:len(old) - 1], old[:-1], u"段 1 の vocabulary.py の行を 1 行も変えない(最後の DEFAULT_PROFILE の行だけ直す)")
        self.assertEqual(old[-1], u'DEFAULT_PROFILE = "P21"')
        self.assertEqual(new[-1], u'DEFAULT_PROFILE = "P22"')
        self.assertTrue(all(l.startswith(u"#") for l in new[len(old) - 1:-1]), u"足した行は注記(#)だけ")

    def test_16_frozen_bundle_last_generation_is_the_working_tree_and_declares_step_2(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("frozen_bundle_sha_for_period_bind", FROZEN_SRC)
        fz = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fz)
        cwd = os.getcwd()
        os.chdir(os.path.dirname(ROOT))          # frozen_bundle_sha.py は repo の根で git ls-files audit-core/... を数える
        try:
            current, _rows = fz.bundle()
        finally:
            os.chdir(cwd)
        check_frozen_generation(fz.FROZEN_BUNDLE_GENERATIONS, current)
        self.assertEqual(fz.FROZEN_BUNDLE_SHA, fz.FROZEN_BUNDLE_GENERATIONS[-1][0])

    def test_15_p21_ritual_copy_is_the_control_of_stage1(self):
        self.assertEqual(sha_path(RITUAL_P21), u"dad4c56e7aeeadd1c1d07fe6dc3f844f62be2d127a5e7f9cac10df761ecac6d8")
        self.assertEqual(sha_path(RITUAL_P21), self.rec[u"入力の sha256"]["fixtures/xbrl/ritual_2026-10-20.json"])
        self.assertEqual(jload(RITUAL_P21)[u"入力"][u"profile"], "P21")
        self.assertEqual(jload(RITUAL_P22)[u"入力"][u"profile"], "P22")


def run_script(args):
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=ROOT, capture_output=True, text=True)


#: 2026-10-27(重い走らせ直しの遷移。封 docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md §2-4): 重い試験(段 2)の出力が記録と違ってよい欄の全部。{path: (後の値, 遷移を宣言した封, 桁)}。
#: 桁は全部 None(値そのもので比べる)。recipes.py・vocabulary.py は ENGINE_LATER を参照する。束ねた sha256 は他の門の定数を import せず字で書く。ここに名前の無い欄は 1 字でも違えば赤。
HEAVY_RERUN_LATER = {
    (u"recipes.py の sha16",): (ENGINE_LATER["adapters/xbrl/recipes.py"][0], ENGINE_LATER["adapters/xbrl/recipes.py"][1], None),
    (u"vocabulary.py の sha16",): (ENGINE_LATER["adapters/xbrl/vocabulary.py"][0], ENGINE_LATER["adapters/xbrl/vocabulary.py"][1], None),
    (u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)",):
        # 2026-10-27(P27 の段 2): 4f417562…(既定を P22 -> P26 にした段 2 の後の値。残す)から、P27 の封が宣言した遷移の値(engine の 5 file に挿入だけを足した後。ritual の engine_bundle_sha256)。
        # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 9dd27fab…(P27 の段 2 の後の値。残す)から、封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md が宣言した遷移の値(vocabulary.py の DEFAULT_PROFILE の 1 行と注記・verify_document.py の docstring の 1 行の後)。
        ("49bcd3ac7c3bfdcdadf275a8829f14b21e45a4908c3e857872231412e2d3e41c", SEAL_DEFAULT_P27, None),
}


def heavy_rerun_check(got, rec, later):
    u"""段 2 の重い走らせ直しの出力 ``got`` を記録 ``rec``(= 記録の stage2_default)と比べる(封 §2-1)。``later`` に名指しした欄は、封が履歴に在り値が宣言の値のときだけ記録の値に戻す。
    最後に ``g == r``(名前の無い欄は 1 字でも違えば AssertionError)。``所要秒`` は走らせるたびに違うので比べない。"""
    keys = (u"E1", u"E2", u"対照: 既定を P21 に戻す変異(比較器が差を拾えるか)", u"差 0 の行数", u"差のあった行の合計", u"DEFAULT_PROFILE",
            u"recipes.py の sha16", u"vocabulary.py の sha16",
            u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)")

    def pick(o):
        d = dict((k, o[k]) for k in keys)
        d[u"E5"] = dict((k, v) for k, v in o[u"E5"].items() if k != u"所要秒")
        return copy.deepcopy(d)

    def walk(d, path):
        for k in path:
            assert isinstance(d, dict) and k in d, u"欄が無い: %r" % (path,)
            d = d[k]
        return d

    g, r = pick(got), pick(rec)
    for path, (after, seal_rel, digits) in sorted(later.items()):
        v, w = walk(g, path), walk(r, path)
        if digits:
            v, w = v[:digits], w[:digits]
        if v == w:
            continue
        assert git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % ("/".join(path), seal_rel)
        assert v == after, u"**%s が、宣言された遷移の値とも違う**" % "/".join(path)
        walk(g, path[:-1])[path[-1]] = walk(r, path)
    assert g == r, u"重い走らせ直しの出力が記録と違う(名前の無い欄)"


class RerunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)

    def _need(self, docs):
        if not have_cache(docs):
            self.skipTest(u"cache が無い")
        if not labels_ok():
            self.skipTest(u"標準タクソノミのラベルが無い(fixtures/xbrl/TAXONOMY_LABELS_README.md)")

    def test_light_e1_matches_the_record(self):
        self._need(LIGHT_E1_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "e1.json")
            p = run_script(["--stage", "e1", "--docs", ",".join(LIGHT_E1_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)[u"E1"][u"行"]
        want = [r for r in self.rec[u"E1"][u"行"] if r[u"書類"] in LIGHT_E1_DOCS]
        self.assertTrue(want)
        self.assertEqual(got, want)

    def test_light_e2_matches_the_record(self):
        self._need(LIGHT_E2_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "e2.json")
            p = run_script(["--stage", "e2", "--docs", ",".join(LIGHT_E2_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)[u"E2"]
        want = [x for x in self.rec[u"E2"][u"動いた行"] if x[u"doc"] in LIGHT_E2_DOCS]
        self.assertTrue(want)
        self.assertEqual(got[u"動いた行"], want)
        self.assertEqual(got[u"書類"], [d for d in self.rec[u"E2"][u"書類"] if d[u"doc"] in LIGHT_E2_DOCS])

    @staticmethod
    def _script():
        import importlib.util
        spec = importlib.util.spec_from_file_location("pb_script_for_stage2", SCRIPT)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    @staticmethod
    def _texts(m, docs):
        out = {}
        for d in docs:
            with open(os.path.join(CACHE, d + ".zip"), "rb") as fh:
                zb = fh.read()
            out[d] = (zb, m.PP.classify_doc(zb)[2])
        return out

    def test_light_stage2_default_e1_matches_the_stage1_p22_rows(self):
        u"""profile を省いた(= 既定 P22 の)再検証が、段 1 の記録の P22 の欄と 1 行ずつ一致(軽い書類 1 本)。"""
        self._need(LIGHT_E1_DOCS)
        m = self._script()
        got = m.stage2_e1(self._texts(m, LIGHT_E1_DOCS), self.rec)
        want = [r for r in self.rec[u"E1"][u"行"] if r[u"書類"] in LIGHT_E1_DOCS]
        self.assertTrue(want)
        self.assertEqual((got[u"今回の行"], got[u"段 1 の P22 の欄と違った行"], got[u"記録に無い行"]), (len(want), 0, 0))

    def test_light_stage2_default_e2_matches_the_stage1_moved_rows(self):
        self._need(LIGHT_E2_DOCS)
        m = self._script()
        got = m.stage2_e2(self._texts(m, LIGHT_E2_DOCS), self.rec)
        want = [x for x in self.rec[u"E2"][u"動いた行"] if x[u"doc"] in LIGHT_E2_DOCS]
        self.assertTrue(want)
        self.assertEqual((got[u"既定と P21 で動いた行"], got[u"記録の動いた行のうち違った行(P21・P22 の欄)"], got[u"記録に無い動いた行"]), (len(want), 0, 0))

    def test_light_stage2_the_comparator_sees_a_wrong_default(self):
        u"""対照(変異): 測定の profile を P21 に取り違えると、同じ比較器が違った行を拾う(『差 0』が自分の欠陥でない)。
        2026-10-23(既定を P22 -> P26 に切り替える 段 2): 測定は既定に頼らず測った当時の P22 を明示するので、『既定を実行中だけ P21 に戻す』でなく profile を P21 にして当てる。
        既定が P26 の今、既定を P21 に戻しても測定が動かないこと(既定に頼っていないこと)も見る。"""
        self._need(LIGHT_E1_DOCS + LIGHT_E2_DOCS)
        m = self._script()
        from adapters.xbrl import vocabulary as V
        self.assertEqual(m.STAGE2_PROFILE_AT_MEASURE, "P22")
        e1 = m.stage2_e1(self._texts(m, LIGHT_E1_DOCS), self.rec, profile="P21")
        e2 = m.stage2_e2(self._texts(m, LIGHT_E2_DOCS), self.rec, profile="P21")
        old = V.DEFAULT_PROFILE
        V.DEFAULT_PROFILE = "P21"
        try:
            e1_def = m.stage2_e1(self._texts(m, LIGHT_E1_DOCS), self.rec)
        finally:
            V.DEFAULT_PROFILE = old
        self.assertEqual(V.DEFAULT_PROFILE, "P27")      # 2026-10-28: P26 の段 2 の後は P26 だった。P27 の段 2 で P27
        self.assertEqual(e1_def[u"段 1 の P22 の欄と違った行"], 0)       # 既定を動かしても測定は動かない
        self.assertGreater(e1[u"段 1 の P22 の欄と違った行"], 0)
        self.assertGreater(e2[u"記録の動いた行のうち違った行(P21・P22 の欄)"], 0)

    def test_heavy_stage2_default_matches_the_record(self):
        if not RUN_HEAVY:
            self.skipTest(HEAVY_SKIP_REASON)
        self._need(sorted(self.rec[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]))
        m = self._script()
        label_shas, why = m.RIT.check_labels()
        self.assertFalse(why)
        got = m.stage2_default(label_shas)
        heavy_rerun_check(got, self.rec[STAGE2], HEAVY_RERUN_LATER)

    def test_heavy_everything_matches_the_record(self):
        if not RUN_HEAVY:
            self.skipTest(HEAVY_SKIP_REASON)
        self._need(sorted(self.rec[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]))
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "all.json")
            p = run_script(["--stage", "all", "--no-tests", "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)
        for k in (u"E1", u"E2", u"E3"):
            self.assertEqual(got[k], self.rec[k], k)
        strip = lambda d: dict((k, v) for k, v in d.items() if k != u"所要秒")      # 所要秒だけは走らせるたびに違う
        self.assertEqual(strip(got[u"E5"]), strip(self.rec[u"E5"]))
        self.assertEqual(got[u"E4"][u"行"], self.rec[u"E4"][u"行"])
        self.assertEqual(got[u"E4"][u"集計"], self.rec[u"E4"][u"集計"])
        self.assertEqual(got[u"入力の sha256"], self.rec[u"入力の sha256"])


class MutationTest(unittest.TestCase):
    u"""門自身が、壊した標本で赤くなる(毎回走る)。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def _red(self, f, *a):
        with self.assertRaises(AssertionError):
            f(*a)

    def test_baseline_is_green(self):
        check_stage2(self.rec)
        check_record(self.rec)
        check_judgments(self.rec, self.seal)
        check_doc(self.rec, self.doc)
        check_read(self.rec)
        check_inputs(self.rec)

    def test_m1_flip_one_p22_row_to_grounded_current(self):
        r = copy.deepcopy(self.rec)
        row = next(x for x in r[u"E1"][u"行"] if x[u"P22"][u"結果"] == K_STOP)
        row[u"P22"][u"state"] = "GROUNDED"
        row[u"P22"][u"pointers"] = ["xbrl:%s@%s" % (row[u"要素"], u"CurrentYearDuration")]
        self._red(check_record, r)

    def test_m2_drop_one_moved_row(self):
        r = copy.deepcopy(self.rec)
        r[u"E2"][u"動いた行"].pop(0)
        self._red(check_record, r)

    def test_m3_change_a_judgment_word(self):
        r = copy.deepcopy(self.rec)
        k = "E-1"
        r[u"予測の判定"][k][u"判定"] = u"外れ" if r[u"予測の判定"][k][u"判定"] == u"当たり" else u"当たり"
        self._red(check_judgments, r, self.seal)

    def test_m4_change_a_number_in_a_document_table(self):
        b = render_blocks(self.rec)["E-1 の単位別"]
        self.assertIn(b, self.doc)
        self.assertIn(u"**485**", b)
        mutated = self.doc.replace(b, b.replace(u"**485**", u"**486**"), 1)
        self.assertNotEqual(mutated, self.doc)
        self._red(check_doc, self.rec, mutated)

    def test_m4b_change_a_number_in_the_moved_rows_table(self):
        b = render_blocks(self.rec)["E-2 の動いた行"]
        self.assertIn(b, self.doc)
        mutated = self.doc.replace(b, b.replace(u"GROUNDED → VALUE_MISMATCH", u"GROUNDED → POINTER_NOT_FOUND", 1), 1)
        self.assertNotEqual(mutated, self.doc)
        self._red(check_doc, self.rec, mutated)

    def test_m10_postscript_is_bound(self):
        r = copy.deepcopy(self.rec)
        r[u"postscript_2026-10-20"][u"E-7 の判定"] = u"当たり"
        self._red(check_record, r)
        b = render_blocks(self.rec)["追記 2026-10-20"]
        self.assertIn(b, self.doc)
        self._red(check_doc, self.rec, self.doc.replace(b, b.replace(u"外れ", u"当たり"), 1))

    def test_m11_a_number_in_a_prose_sentence_is_red(self):
        P = prose_facts(self.rec)
        for k in ("e1", "e2", "e2_groups", "e6", "e3", "e4", "e5", "e7", "cost1", "cost2", "cost3", "cost4", "head", "pred"):
            v = P[k]
            self.assertIn(v, self.doc, k)
            m = re.search(r"\d+", v)
            self.assertTrue(m, k)
            mutated = self.doc.replace(v, v[:m.start()] + str(int(m.group(0)) + 7) + v[m.end():], 1)
            self.assertNotEqual(mutated, self.doc)
            self._red(check_doc, self.rec, mutated)

    def test_m12_a_new_unbound_number_in_prose_is_red(self):
        self._red(check_doc, self.rec, self.doc.replace(u"## 11. 限界\n", u"## 11. 限界\n\n- 影響は 12345 行。\n", 1))
        self.assertEqual(residual_numbers(self.doc, self.rec), [])

    def test_m13_mutation_table_record_is_bound(self):
        r = copy.deepcopy(self.rec)
        r[u"変異(engine。手で走らせた)"][u"行"][0][u"判定"] = u"外れ" if r[u"変異(engine。手で走らせた)"][u"行"][0][u"判定"] == u"当たり" else u"当たり"
        self._red(check_record, r)
        t = mutation_table(self.rec)
        self.assertIn(t, self.doc)
        self._red(check_doc, self.rec, self.doc.replace(t, t.replace(u"当たり", u"外れ", 1), 1))

    def test_m5_move_one_row_between_groups(self):
        r = copy.deepcopy(self.rec)
        x = next(x for x in r[u"E2"][u"動いた行"] if x[u"P21 の群"] == u"Prior1Year・手がかり無し")
        x[u"P21 の群"] = u"Prior1Year・手がかりあり"
        self._red(check_record, r)

    def test_m6_a_new_grounded_row_is_seen(self):
        r = copy.deepcopy(self.rec)
        x = next(x for x in r[u"E2"][u"動いた行"] if x[u"P21"][u"state"] == "GROUNDED" and x[u"P22"][u"state"] != "GROUNDED")
        x[u"P21"] = dict(x[u"P21"], state="UNVERIFIABLE")
        x[u"P21 の群"] = None
        x[u"P22"] = dict(x[u"P22"], state="GROUNDED")
        x[u"向き"] = u"UNVERIFIABLE → GROUNDED"
        self._red(check_record, r)     # 集計の『新 GROUNDED』が 0 のまま
        self.assertEqual(recount_cmp(r[u"E2"])[u"新 GROUNDED"], 1)

    def test_m7_unread_row_is_red(self):
        r = copy.deepcopy(self.rec)
        key = (r[u"E2"][u"動いた行"][0][u"doc"], r[u"E2"][u"動いた行"][0][u"id"])
        saved = READ.pop(key)
        try:
            self._red(check_read, r)
        finally:
            READ[key] = saved

    def test_m8_engine_flag_made_identity_turns_e1_red(self):
        u"""旗 period_bind を恒等(偽)にすると、E-1 の再計算(軽い走らせ直しと同じ道)が記録と食い違う。"""
        if not (have_cache(LIGHT_E1_DOCS) and labels_ok()):
            self.skipTest(u"cache かラベルが無い")
        import dataclasses
        import importlib.util
        from adapters.xbrl import vocabulary as V
        spec = importlib.util.spec_from_file_location("pb_script_for_mutation", SCRIPT)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        want = [x for x in self.rec[u"E1"][u"行"] if x[u"書類"] in LIGHT_E1_DOCS]
        old = V.PROFILES["P22"]
        V.PROFILES["P22"] = dataclasses.replace(old, period_bind=False)
        try:
            zb = open(os.path.join(CACHE, LIGHT_E1_DOCS[0] + ".zip"), "rb").read()
            text = m.PP.classify_doc(zb)[2]
            got, _ns, _nm = m.e1_doc(LIGHT_E1_DOCS[0], zb, text)
        finally:
            V.PROFILES["P22"] = old
        self.assertNotEqual(got, want)
        self.assertGreater(sum(1 for x in got if e1_kind(x[u"P22"], x) in PASSED_KINDS), sum(1 for x in want if e1_kind(x[u"P22"], x) in PASSED_KINDS))

    def test_mh_heavy_rerun_transitions(self):
        u"""2026-10-27(封 docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md §4-1): 重い走らせ直しの遷移の規則を、環境変数なしで毎回試す。V-0 は緑、V-1〜V-7 は赤。"""
        rec = self.rec[STAGE2]

        def got0():
            u"""記録から作った『engine の遷移の後の出力』の標本(封 §4-1)。HEAVY_RERUN_LATER の後の値を入れる。"""
            g = copy.deepcopy(rec)
            for path, (after, _seal, _digits) in HEAVY_RERUN_LATER.items():
                g[path[0]] = after
            return g

        with self.subTest(u"V-0 基準"):
            heavy_rerun_check(got0(), rec, HEAVY_RERUN_LATER)
            heavy_rerun_check(copy.deepcopy(rec), rec, HEAVY_RERUN_LATER)
        for path in sorted(HEAVY_RERUN_LATER):
            after = HEAVY_RERUN_LATER[path][0]
            with self.subTest(u"V-1 封の path が在らない file " + path[0][:20]):
                bad = dict((k, (a, u"docs/XBRL_NO_SUCH_SEAL_2026-10-27.md" if k == path else s_, d)) for k, (a, s_, d) in HEAVY_RERUN_LATER.items())
                self._red(heavy_rerun_check, got0(), rec, bad)
            with self.subTest(u"V-2 後の値を 1 字変える " + path[0][:20]):
                chg = after[:-1] + (u"0" if after[-1] != u"0" else u"1")
                bad = dict((k, (chg if k == path else a, s_, d)) for k, (a, s_, d) in HEAVY_RERUN_LATER.items())
                self._red(heavy_rerun_check, got0(), rec, bad)
        with self.subTest(u"V-3 測った値の欄を 1 つ変える"):
            g = got0()
            g[u"差のあった行の合計"] += 1
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)
        with self.subTest(u"V-4 byte 一致のままの留めを変える"):
            g = got0()
            g[u"DEFAULT_PROFILE"] = "P26"
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)
        with self.subTest(u"V-5 宣言の無い欄に後の値を入れる"):
            g = got0()
            g[u"E5"][u"通した"][u"件"] += 1
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)
        with self.subTest(u"V-6 束ねた sha256 が段 2 の値でも後の値でもない"):
            g = got0()
            g[u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)"] = "0" * 64
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)
        with self.subTest(u"V-7 recipes.py の sha16 が途中の値(宣言していない)"):
            g = got0()
            g[u"recipes.py の sha16"] = u"d5308700eae78c10"
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)

    def test_ms1_stage2_a_row_that_differs_is_red(self):
        for path, newv in (((u"E1", u"段 1 の P22 の欄と違った行"), 1), ((u"E2", u"記録の動いた行のうち違った行(P21・P22 の欄)"), 1),
                           ((u"E5", u"期待と違った行"), 1), ((u"E5", u"素の書類: 既定と P22 明示で違った claim"), 1),
                           ((u"E1", u"記録に無い行"), 1), ((u"E2", u"記録に無い動いた行"), 1)):
            r = copy.deepcopy(self.rec)
            r[STAGE2][path[0]][path[1]] = newv
            self._red(check_stage2, r)

    def test_ms2_stage2_a_changed_count_is_red(self):
        r = copy.deepcopy(self.rec)
        r[STAGE2][u"E1"][u"通した(GROUNDED のまま)"][u"件"] += 1
        self._red(check_stage2, r)
        r = copy.deepcopy(self.rec)
        r[STAGE2][u"E2"][u"GROUNDED を離れた"] -= 1
        self._red(check_stage2, r)
        r = copy.deepcopy(self.rec)
        r[STAGE2][u"差 0 の行数"][u"E-5"] -= 1
        self._red(check_stage2, r)
        r = copy.deepcopy(self.rec)
        r[STAGE2][u"差のあった行の合計"] = 1
        self._red(check_stage2, r)
        r = copy.deepcopy(self.rec)
        r[STAGE2][u"E5"][u"通した"] = dict(r[STAGE2][u"E5"][u"通した"], 件=16, 字=u"16 / 240 = 6.7%")
        self._red(check_stage2, r)

    def test_ms3_stage2_a_comparator_that_sees_nothing_is_red(self):
        r = copy.deepcopy(self.rec)
        r[STAGE2][u"対照: 既定を P21 に戻す変異(比較器が差を拾えるか)"][u"段 1 の P22 の欄と違った行"] = 0
        self._red(check_stage2, r)

    def test_ms4_stage2_default_or_engine_sha_wrong_is_red(self):
        r = copy.deepcopy(self.rec)
        r[STAGE2][u"DEFAULT_PROFILE"] = "P21"
        self._red(check_stage2, r)
        r = copy.deepcopy(self.rec)
        r[STAGE2][u"vocabulary.py の sha16"] = u"1fdb48e7e3ba58ce"
        self._red(check_stage2, r)
        r = copy.deepcopy(self.rec)
        r[STAGE2][u"recipes.py の sha16"] = u"0" * 16
        self._red(check_stage2, r)

    def test_ms5_stage2_a_number_in_a_stage2_sentence_is_red(self):
        P = stage2_facts(self.rec)
        keys = [k for k in P if k.startswith("s2_")]
        self.assertGreaterEqual(len(keys), 7)
        for k in keys:
            v = P[k]
            self.assertIn(v, self.doc, k)
            m = re.search(r"\d+", v)
            self.assertTrue(m, k)
            mutated = self.doc.replace(v, v[:m.start()] + str(int(m.group(0)) + 7) + v[m.end():], 1)
            self.assertNotEqual(mutated, self.doc)
            self._red(check_doc, self.rec, mutated)
        b = stage2_blocks(self.rec)["段 2 の C 行"]
        self.assertIn(b, self.doc)
        self._red(check_doc, self.rec, self.doc.replace(b, b.replace(u"GROUNDED → VALUE_MISMATCH", u"GROUNDED → POINTER_NOT_FOUND", 1), 1))
        # 段 2 の節が無い・二つある文書は赤
        self._red(check_doc, self.rec, self.doc.replace(STAGE2_HEAD, u"## 14. 段 2", 1))
        self._red(check_doc, self.rec, self.doc + u"\n" + STAGE2_HEAD + u"\n")

    def test_ms6_stage2_default_note_mutations_are_red(self):
        src = jtext(VOCAB)
        check_default_note(src)
        for a, b in ((u'DEFAULT_PROFILE = "P27"', u'DEFAULT_PROFILE = "P21"'),
                     (u"# 2026-10-20 に P21 -> P22(期を縛る P22 の段 2)。", u"# 2026-10-20 に P21 -> P22(期を縛る P22 の段 1)。"),
                     (u"**P21 の字は消さず**", u"P21 の字は消し"),
                     (u"# 2026-10-20 に P20 -> P21(段 2)。", u"# 2026-10-20 に P20 -> P21。")):
            self.assertEqual(src.count(a), 1, a)
            self._red(check_default_note, src.replace(a, b, 1))

    def test_ms8_stage2_frozen_generation_mutations_are_red(self):
        gens = [("a" * 64, u"古い世代"), ("b" * 64, u"2026-10-20 feature/audit-core-final-eval-8(期を縛る P22 の段 2): vocabulary.py の DEFAULT_PROFILE を P21 -> P22 にし、"
                                              u"封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md の段 2")]
        check_frozen_generation(gens, "b" * 64)
        self._red(check_frozen_generation, gens[:-1], "b" * 64)                            # 世代を足し忘れた
        self._red(check_frozen_generation, gens, "c" * 64)                                 # 作業木が世代と違う
        self._red(check_frozen_generation, gens[:-1] + [("b" * 64, u"期を縛る P22 の段 1")], "b" * 64)   # 説明が段 2 でない
        self._red(check_frozen_generation, gens + [("a" * 64, u"期を縛る P22 の段 2 DEFAULT_PROFILE XBRL_PERIOD_BIND_SEAL_2026-10-20")], "a" * 64)   # 重複
        later = gens + [("d" * 64, u"2026-10-21 丸めの帯 P23 の段 1 docs/XBRL_ROUNDING_SEAL_2026-10-21.md")]
        check_frozen_generation(later, "d" * 64)                                           # 後の封の世代が足された後も、段 2 の宣言は 1 つ前に在ればよい
        self._red(check_frozen_generation, later, "b" * 64)                                # 作業木が最新の世代と違う
        self._red(check_frozen_generation, gens[:-1] + [("d" * 64, u"2026-10-21 丸めの帯 P23 の段 1 docs/XBRL_ROUNDING_SEAL_2026-10-21.md")], "d" * 64)   # 1 つ前が段 2 でない

    def test_ms7_stage2_unpinned_script_is_red(self):
        u"""測った当時の P21 を字で留めた measure のどれかが、既定を読むように戻ったら赤。"""
        check_pinned_scripts()
        for rel in PINNED_P21_SCRIPTS:
            src = jtext(os.path.join(ROOT, rel))
            self.assertEqual(src.count(u'PROFILE_AT_MEASURE = "P21"'), 1, rel)
            for bad in (src.replace(u'PROFILE_AT_MEASURE = "P21"', u'PROFILE_AT_MEASURE = "P22"', 1),                 # 当時の P21 を P22 に
                        src + u"\n_DEFAULT_READ = V.DEFAULT_PROFILE\n",                                              # 既定を読み直す
                        src.replace(u'PROFILE_AT_MEASURE = "P21"', u"", 1)):                                          # 留めを消す
                self.assertNotEqual(bad, src)
                self._red(check_pinned_scripts, lambda r, rel=rel, bad=bad: bad if r == rel else jtext(os.path.join(ROOT, r)))

    def test_m9_a_spoiled_input_digest_is_red(self):
        r = copy.deepcopy(self.rec)
        k = sorted(r[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"])[0]
        r[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"][k] = u"0" * 64
        self._red(check_inputs, r)


if __name__ == "__main__":
    if "--emit" in sys.argv:
        rec = jload(REC)
        for k, v in render_blocks(rec).items():
            print(u"<<<%s>>>\n%s\n" % (k, v))
    else:
        unittest.main()
