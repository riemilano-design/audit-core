# -*- coding: utf-8 -*-
u"""丸めの帯を片側にする P23 の段 1 の結果 ― 封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md §2(R-1〜R-7)の結果を縛る門。

記録: ``fixtures/xbrl/rounding_2026-10-21.json``(``measure/xbrl_rounding_2026-10-21.py --stage all --run-tests`` の出力)。
文書: ``docs/XBRL_ROUNDING_RESULT_2026-10-21.md``。

この門がやること(どれも、壊した標本で赤くなることを ``MutationTest`` が毎回確かめる):
  1. 入力(書類 67 本の sha256・他の記録の sha256)を**字で留めた digest / sha256** に縛る。cache が在る機械では実物の sha256 も記録と一致させる。
  2. 記録の行(R-1 の儀式 240・R-2 の動いた行と書類別・R-3 の注入 485・R-5 の 192 行)から、集計・向き・単位別を **script の関数を使わずに** 数え直し、記録の集計と一致させる。
     対照(P22 の再計算が、儀式の記録・期を縛る P22 の記録の同じ行と一致すること = 旗が偽の側は 1 行も変わらない)も、門が自分で記録同士を突き合わせる。
  3. 予測 R-1〜R-7 の判定を、封の字から読んだ幅と記録の行から**門が自分で**求め、記録の判定と文書の表と一致させる。
  4. 文書の表(予測・R-1・R-2・R-3・R-5・R-6)を記録から作った字と完全一致させる。散文の数のある文は ``prose_facts`` が記録から作り、文書がその字を含むことを縛る。
     それ以外の散文に算用数字が在れば ``residual_numbers`` が見つけて赤にする(コード片・識別子・日付・節の番号は除く)。散文は漢数字で書く。
  5. engine の sha(測った時点の vocabulary.py・comparators.py・recipes.py)を字で留め、いまの engine が同じか宣言された遷移であること。
     ``core/`` が封の commit から 0 行であること。``DEFAULT_PROFILE`` が P22 のままであること(段 1)。封が封の commit から 1 字も変わっていないこと。
  6. cache とラベルが在る機械では、軽い走らせ直し(R-2 を 2 書類、R-3 を 1 書類)を script で走らせて記録の該当行と一致。
     全部の走らせ直し(約 7 分)は ``AUDIT_CORE_ROUNDING=1`` のときだけ。
縛っていないもの: 動いた行の「正しさ」(人の読み。結果文書に書く)、限界の文の主張の中身、変異(engine)の手の実測そのもの(表は記録の写しを縛るだけ)、
  tests/measure 全体の所要、漢数字で書いた数(``residual_numbers`` は算用数字だけを探す。散文の数は記録から作った字で縛る約束)。
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
REC = os.path.join(ROOT, "fixtures", "xbrl", "rounding_2026-10-21.json")
DOC = os.path.join(ROOT, "docs", "XBRL_ROUNDING_RESULT_2026-10-21.md")
SEAL_REL = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SEAL_COMMIT = "5008985"
SCRIPT = os.path.join(ROOT, "measure", "xbrl_rounding_2026-10-21.py")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
RUN_HEAVY = os.environ.get("AUDIT_CORE_ROUNDING") == "1"
# 2026-10-23(P26 の段 2。封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)で ritual_2026-10-20.json は P26(既定)で採り直したので、P22 のときの記録は同じバイト列(sha256 c89824f7…)の写し ritual_2026-10-20_p22.json を読む
RITUAL_P22 = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20_p22.json")
PERIOD_BIND = os.path.join(ROOT, "fixtures", "xbrl", "period_bind_2026-10-20.json")
VOCAB = os.path.join(ROOT, "adapters", "xbrl", "vocabulary.py")
LIGHT_R2_DOCS = ("S100YMFV", "S100YUHC")      # 動いた行 3 件(％ 2・ポイント 1)
LIGHT_R3_DOCS = ("S100YXLE",)                 # P22 で通した 1 件(率 89.4 → 89.5)が在る書類
RATE_UNITS = (u"％", u"%", u"ポイント")

#: **字で留める**(記録の値の写し。定数から作らない)。
DOCS67_DIGEST = "118ec1015494db404b74dbd65b72bddfd2356459749d6f10dc910e5a1348429f"       # 書類 67 本の docID\tsha256 を sorted で \n 結合した sha256(期を縛る P22 の門と同じ集合)
INPUT_SHAS = {
    "fixtures/xbrl/ritual_2026-10-20.json": "c89824f71e8002421fd27eb98044884ef94b2adb047c9fab0235a489d69f0249",
    "fixtures/xbrl/period_bind_2026-10-20.json": "dfcf8d94dadf51ef0d525b74edf72dff8a009dce7352c453c8bf6e5db2db9b60",
    "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json": "c3068024ff8c2812fabbf54e36f50b1cedeccb7955e9455603d1a17018418149",
    "fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json": "3b13d26f81906ae47696c95c2c0e21322579bcdabcde3a133b5a96970e7c52f6",
}
RITUAL_ZIP_SHA = "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799"
#: 測った時点の engine(sha256 の先頭 16 桁)。comparators.py は 0 行(封 §1 は「写しの帯」を変更として数えたが、実物は P19 で入っており変更が要らなかった)。
ENGINE_AT_MEASURE = {"adapters/xbrl/vocabulary.py": "f7b8d925eb6787ec", "adapters/xbrl/comparators.py": "d8706338325e725b",
                     "adapters/xbrl/recipes.py": "d5308700eae78c10"}
#: 段 2(既定の切り替え)などで動いたときの宣言された遷移: {path: (後の sha16, 遷移を宣言した封の path)}。段 1 の commit 時点では空だった。
#: 2026-10-21 追記(pin の遷移): 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(語彙の登録と枠の取り直し P24 の段 1。engine を変える。人間の事前承認 2026-10-21)で
#: vocabulary.py に旗 2 つ・資金の句の表・P24・PROFILES の登録、recipes.py に旗 vocab_2026_10_21・frame_rebind の塊を足した(DEFAULT_PROFILE は P22 のまま)。
#: 上の ENGINE_AT_MEASURE は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P24 の段 1 の後の値のときだけ。
SEAL_VOCAB = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"    # 2026-10-21 追記: 最後の枝 P25 の段 1(下の ENGINE_LATER の遷移)
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"    # 2026-10-22 追記: P26 の段 1(下の ENGINE_LATER の遷移)
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
# 2026-10-21(最後の枝 P25 の段 1): 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 last_branch_names_only_if_evidence・P25・PROFILES の登録(+7 行・-0 行)、recipes.py に最後の枝の証拠の判定の塊(+72 行・-0 行。既存の行は 1 つも書き換えない)を足した(DEFAULT_PROFILE は P22 のまま)。
# vocabulary.py の 83498c04a7b70396・recipes.py の 3461c3f8b7af6675(P24 の段 1)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P25 の段 1 の後の値のときだけ。
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
# 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
# 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
ENGINE_LATER = {"adapters/xbrl/vocabulary.py": ("85896a67913ce1e7", SEAL_P27),
                # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に G1〜G5 の塊(+251 行・-1 行。既存の行の書き換えは数の読み取りの for 文 1 行だけ) を足した。
                # bff243f13429b553(P25 の段 1)は残す(測った時点の値)、P26 の段 1 で 181b370420ab751b。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
                "adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27)}


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


def comma(n):
    return format(n, ",")


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


PASSED = "PASSED"
STOPPED = "detected:VALUE_MISMATCH"


# ----------------------------------------------------------------------------------------------------------------
# 独立の数え直し(script の関数を使わない)
def recount_r1(rows):
    n = len(rows)
    c = {u"行": n}
    for side in ("P22", "P23"):
        c[side] = {u"通した": sum(1 for r in rows if r[side] == PASSED), u"止めた": sum(1 for r in rows if r[side] == STOPPED),
                   u"その他": sum(1 for r in rows if r[side] not in (PASSED, STOPPED))}
    c[u"P23 の通した id"] = [r[u"id"] for r in rows if r[u"P23"] == PASSED]
    c[u"P22 で通して P23 で止めた id"] = [r[u"id"] for r in rows if r[u"P22"] == PASSED and r[u"P23"] == STOPPED]
    c[u"P22 で止めて P23 で通した id"] = [r[u"id"] for r in rows if r[u"P22"] == STOPPED and r[u"P23"] == PASSED]
    c[u"P22 で通した 率"] = sum(1 for r in rows if r[u"P22"] == PASSED and r[u"単位"] in RATE_UNITS)
    c[u"P22 で通した 金額ほか"] = sum(1 for r in rows if r[u"P22"] == PASSED and r[u"単位"] not in RATE_UNITS)
    c[u"P22 で通して P23 で止めた 率"] = sum(1 for r in rows if r[u"P22"] == PASSED and r[u"P23"] == STOPPED and r[u"単位"] in RATE_UNITS)
    c[u"P22 で通して P23 で止めた 金額ほか"] = sum(1 for r in rows if r[u"P22"] == PASSED and r[u"P23"] == STOPPED and r[u"単位"] not in RATE_UNITS)
    return c


def moved_unit_class(r):
    return u"率" if r[u"unit"] in RATE_UNITS else u"金額ほか"


def recount_r2(sec):
    mv = sec[u"動いた行"]
    docs = sec[u"書類"]
    leave = [r for r in mv if r[u"P22"][u"state"] == "GROUNDED" and r[u"P23"][u"state"] != "GROUNDED"]
    new_g = [r for r in mv if r[u"P22"][u"state"] != "GROUNDED" and r[u"P23"][u"state"] == "GROUNDED"]
    same = [r for r in mv if r[u"P22"][u"state"] == "GROUNDED" and r[u"P23"][u"state"] == "GROUNDED"]
    units = {}
    for r in leave:
        units[r[u"unit"]] = units.get(r[u"unit"], 0) + 1
    return {u"動いた": len(mv), u"離れた": len(leave), u"新 GROUNDED": len(new_g), u"参照先だけ動いた": len(same),
            u"離れた 率": sum(1 for r in leave if r[u"unit"] in RATE_UNITS), u"離れた 金額ほか": sum(1 for r in leave if r[u"unit"] not in RATE_UNITS),
            u"離れた 単位別": units, u"離れた 書類数": len({r[u"doc"] for r in leave}), u"書類数": len(docs),
            u"判定が変わった書類": sorted(d[u"doc"] for d in docs if d[u"丸めの判定 P22"] != d[u"丸めの判定 P23"]),
            u"丸め方 P22": sorted((str(d[u"丸めの判定 P22"][u"丸め方"])) for d in docs).count("truncate"),
            u"GROUNDED P22": sum(d[u"states P22"].get("GROUNDED", 0) for d in docs), u"GROUNDED P23": sum(d[u"states P23"].get("GROUNDED", 0) for d in docs),
            u"VM P22": sum(d[u"states P22"].get("VALUE_MISMATCH", 0) for d in docs), u"VM P23": sum(d[u"states P23"].get("VALUE_MISMATCH", 0) for d in docs),
            u"claims": sum(d[u"claims"] for d in docs), u"動いた(書類別の合計)": sum(d[u"動いた"] for d in docs)}


def recount_r3(rows):
    n = len(rows)
    passed = lambda s: s.startswith(u"通した")
    return {u"注入": n, u"P23 通した": sum(1 for r in rows if passed(r[u"P23"][u"結果"])), u"P22 通した": sum(1 for r in rows if passed(r[u"P22"][u"結果"])),
            u"P23 止めた": sum(1 for r in rows if r[u"P23"][u"結果"] == u"止めた"), u"P22 止めた": sum(1 for r in rows if r[u"P22"][u"結果"] == u"止めた"),
            u"P23 その他": sum(1 for r in rows if r[u"P23"][u"結果"] == u"その他"), u"P22 その他": sum(1 for r in rows if r[u"P22"][u"結果"] == u"その他"),
            u"P22 通して P23 止めた": [(r[u"書類"], r[u"id"]) for r in rows if passed(r[u"P22"][u"結果"]) and r[u"P23"][u"結果"] == u"止めた"],
            u"P22 通さず P23 通した": [(r[u"書類"], r[u"id"]) for r in rows if not passed(r[u"P22"][u"結果"]) and passed(r[u"P23"][u"結果"])]}


def recount_r5(rows):
    inj = [r for r in rows if r[u"注入か"]]
    return {u"行": len(rows), u"注入": len(inj),
            u"動いた": sorted((r[u"doc"], r[u"id"]) for r in rows if r[u"Core 自身 P22(今回)"] != r[u"Core 自身 P23"]),
            u"対照の違い": sum(1 for r in rows if r[u"Core 自身 P22(今回)"] != r[u"Core 自身 P22(期を縛る P22 の記録)"]),
            u"P22 GROUNDED(注入)": sum(1 for r in inj if r[u"Core 自身 P22(今回)"][u"state"] == "GROUNDED"),
            u"P23 GROUNDED(注入)": sum(1 for r in inj if r[u"Core 自身 P23"][u"state"] == "GROUNDED"),
            u"T6": sum(1 for r in inj if r[u"注入の型"] == "T6_PRIOR"),
            u"T6 P23 GROUNDED": sum(1 for r in inj if r[u"注入の型"] == "T6_PRIOR" and r[u"Core 自身 P23"][u"state"] == "GROUNDED")}


def check_record(rec):
    """記録の集計を、行から数え直した値と突き合わせる。壊した記録で赤くなる。"""
    # R-1
    r1 = rec[u"R1"]
    c = recount_r1(r1[u"行"])
    assert c[u"行"] == 240 == r1[u"P23 の行数"] == r1[u"P22 の行数"] == r1[u"記録の行数"], c[u"行"]
    assert r1[u"通した P23"][u"件"] == c[u"P23"][u"通した"] and r1[u"通した P23"][u"分母"] == c[u"行"], u"R-1 通した"
    assert r1[u"止めた P23"][u"件"] == c[u"P23"][u"止めた"], u"R-1 止めた"
    assert sum(r1[u"その他 P23"].values()) == c[u"P23"][u"その他"], u"R-1 その他"
    assert r1[u"通した P22(対照)"][u"件"] == c[u"P22"][u"通した"] and r1[u"止めた P22(対照)"][u"件"] == c[u"P22"][u"止めた"], u"R-1 対照"
    assert [x[u"id"] for x in r1[u"通した P23 の一覧"]] == c[u"P23 の通した id"], u"R-1 通した一覧"
    assert r1[u"N237・N277 の P23 の結果"] == dict((i, [r[u"P23"] for r in r1[u"行"] if r[u"id"] == i]) for i in ("N237", "N277")), u"R-1 N237・N277"
    assert r1[u"対照: P22 の再計算が儀式の記録と違った行"] == 0
    # 対照: P22 の欄を、儀式の記録(P22 で採り直した)の 240 行と門が自分で突き合わせる
    rit = jload(RITUAL_P22)
    want = dict(((x[u"id"], x[u"型"]), x[u"結果"]) for x in rit[u"注入の一覧"])
    got = dict(((r[u"id"], r[u"型"]), r[u"P22"]) for r in r1[u"行"])
    assert want == got, u"P22 の欄が儀式の記録と違う(旗が偽の側が動いている)"
    # R-2
    r2 = rec[u"R2"]
    c2 = recount_r2(r2)
    s = r2[u"集計"]
    assert s[u"動いた(全 state)"] == c2[u"動いた"] == c2[u"動いた(書類別の合計)"], u"R-2 動いた"
    assert s[u"GROUNDED → GROUNDED でない"] == c2[u"離れた"] and s[u"GROUNDED でない → GROUNDED(新 GROUNDED)"] == c2[u"新 GROUNDED"]
    assert s[u"GROUNDED → GROUNDED(参照先だけ動いた)"] == c2[u"参照先だけ動いた"]
    assert s[u"GROUNDED を離れた行のうち 率(％・%・ポイント)"] == c2[u"離れた 率"] and s[u"GROUNDED を離れた行のうち 金額ほか(率でない)"] == c2[u"離れた 金額ほか"]
    assert s[u"GROUNDED を離れた行の単位別"] == c2[u"離れた 単位別"] and s[u"GROUNDED を離れた行の書類数"] == c2[u"離れた 書類数"]
    assert s[u"書類数"] == c2[u"書類数"] == 67 and r2[u"キャッシュに無い書類"] == []
    assert s[u"丸めの判定が変わった書類(丸め方・R・T のどれか)"] == c2[u"判定が変わった書類"]
    assert s[u"GROUNDED の合計 P22"] == c2[u"GROUNDED P22"] and s[u"GROUNDED の合計 P23"] == c2[u"GROUNDED P23"]
    assert s[u"VALUE_MISMATCH の合計 P22"] == c2[u"VM P22"] and s[u"VALUE_MISMATCH の合計 P23"] == c2[u"VM P23"]
    assert r2[u"総 claim"] == c2[u"claims"]
    # 動いた行の向きは全部 GROUNDED → 非 GROUNDED(新 GROUNDED・参照先だけ動いた行は 0)
    for x in r2[u"動いた行"]:
        assert x[u"向き"] == u"%s → %s" % (x[u"P22"][u"state"], x[u"P23"][u"state"]), x[u"id"]
    # 対照: P22 の GROUNDED / VALUE_MISMATCH は期を縛る P22 の記録(書類別の P22)と書類ごとに一致 = 旗が偽の側は動いていない
    pb = jload(PERIOD_BIND)
    pbd = dict((d[u"doc"], d) for d in pb[u"E2"][u"書類"])
    for d in r2[u"書類"]:
        assert pbd[d[u"doc"]][u"GROUNDED(P22)"] == d[u"states P22"].get("GROUNDED", 0), d[u"doc"]
        assert pbd[d[u"doc"]][u"claims"] == d[u"claims"], d[u"doc"]
    # R-2b
    b = rec[u"R2b"]
    assert b[u"動いた行の数"] == len(b[u"動いた行"]), u"R-2b 動いた"
    assert b[u"旗が効きうる行のある書類数"] <= b[u"切り捨てと判定された書類"] == c2[u"丸め方 P22"], u"R-2b 切り捨ての書類"
    # R-3
    r3 = rec[u"R3"]
    c3 = recount_r3(r3[u"行"])
    s3 = r3[u"集計"]
    assert c3[u"注入"] == 485 == s3[u"注入"] == sum(p[u"作れた"] for p in r3[u"書類別"]), u"R-3 注入"
    assert s3[u"P23 で通した(GROUNDED のまま)"][u"件"] == c3[u"P23 通した"] and s3[u"P22(対照)で通した"][u"件"] == c3[u"P22 通した"]
    assert s3[u"P23 で止めた(VALUE_MISMATCH)"][u"件"] == c3[u"P23 止めた"] and s3[u"P23 でその他"][u"件"] == c3[u"P23 その他"]
    assert s3[u"P22 で通して P23 で止めた行"] == len(c3[u"P22 通して P23 止めた"]) and s3[u"P22 で通さず P23 で通した行"] == len(c3[u"P22 通さず P23 通した"])
    assert [(x[u"書類"], x[u"id"]) for x in s3[u"P23 で通した行"]] == [(r[u"書類"], r[u"id"]) for r in r3[u"行"] if r[u"P23"][u"結果"].startswith(u"通した")]
    # 対照: P22 の欄が期を縛る P22 の記録の E1 の P22 の欄と 485 行全部一致
    pbw = dict(((r[u"書類"], r[u"id"]), r[u"P22"]) for r in pb[u"E1"][u"行"])
    assert len(pbw) == 485
    for r in r3[u"行"]:
        w = pbw[(r[u"書類"], r[u"id"])]
        assert (w[u"結果"], w[u"state"], w[u"reason"], w[u"pointers"]) == (r[u"P22"][u"結果"], r[u"P22"][u"state"], r[u"P22"][u"reason"], r[u"P22"][u"pointers"]), (r[u"書類"], r[u"id"])
    assert r3[u"対照: P22 の再計算と期を縛る P22 の記録"][u"違った行"] == 0
    # R-5
    r5 = rec[u"R5"]
    c5 = recount_r5(r5[u"行"])
    s5 = r5[u"集計"]
    assert c5[u"行"] == 192 == s5[u"行"] and c5[u"注入"] == 64 == s5[u"注入"]
    assert s5[u"Core 自身が P22 → P23 で動いた行"] == len(c5[u"動いた"]) and s5[u"対照: P22 の再計算が期を縛る P22 の記録と違った行"] == c5[u"対照の違い"]
    assert s5[u"全注入で Core 自身 P23 が GROUNDED"][u"件"] == c5[u"P23 GROUNDED(注入)"] and s5[u"全注入で Core 自身 P22 が GROUNDED"][u"件"] == c5[u"P22 GROUNDED(注入)"]
    assert s5[u"T6_PRIOR の注入で Core 自身 P23 が GROUNDED"][u"件"] == c5[u"T6 P23 GROUNDED"] and s5[u"T6_PRIOR の注入で Core 自身 P23 が GROUNDED"][u"分母"] == c5[u"T6"]
    pbr = dict(((r[u"doc"], r[u"id"]), r[u"Core 自身 P22"]) for r in pb[u"E4"][u"行"])
    for r in r5[u"行"]:
        assert pbr[(r[u"doc"], r[u"id"])] == r[u"Core 自身 P22(今回)"], (r[u"doc"], r[u"id"])
    # 環境
    env = rec[u"環境"]
    assert env[u"比べた profile"] == ["P22", "P23"] and env[u"費用"] == u"0 USD" and env[u"DEFAULT_PROFILE"] == "P22"
    assert env[u"vocabulary.py の sha16"] == ENGINE_AT_MEASURE["adapters/xbrl/vocabulary.py"]
    assert env[u"comparators.py の sha16"] == ENGINE_AT_MEASURE["adapters/xbrl/comparators.py"]
    assert env[u"recipes.py の sha16"] == ENGINE_AT_MEASURE["adapters/xbrl/recipes.py"]


def check_inputs(rec):
    inp = rec[u"入力の sha256"]
    d67 = inp[u"書類 67(経営分析の文を持つ)の sha256"]
    assert len(d67) == 67
    assert digest([u"%s\t%s" % (k, d67[k]) for k in sorted(d67)]) == DOCS67_DIGEST, u"書類 67 の digest が留めた値と違う"
    assert sorted(d[u"doc"] for d in rec[u"R2"][u"書類"]) == sorted(d67), u"R-2 の書類が入力の 67 と違う"
    for rel, want in INPUT_SHAS.items():
        assert inp[rel] == want, rel
    assert inp[u"儀式の同梱書類"] == RITUAL_ZIP_SHA


# ----------------------------------------------------------------------------------------------------------------
# 予測の判定(封の字から幅を読み、記録の行から門が自分で求める)
def seal_cells(seal, tag):
    for l in seal.splitlines():
        if l.startswith(u"| **%s** |" % tag):
            return [c.strip() for c in l.strip().strip(u"|").split(u"|")]
    raise AssertionError(tag)


def bounds(seal):
    c = dict((t, seal_cells(seal, t)[1]) for t in ("R-1", "R-2", "R-3", "R-4", "R-5", "R-6", "R-7"))
    m1 = re.search(r"通した \*\*(\d+)〜(\d+) / 240\*\*.*止めた \*\*(\d+)〜(\d+)\*\*", c["R-1"])
    m2 = re.search(r"GROUNDED を離れる行 \*\*(\d+)〜(\d+)\*\*、うち金額 \*\*(\d+)\*\*", c["R-2"])
    m3 = re.search(r"通す \*\*(\d+)〜(\d+) / 485\*\*", c["R-3"])
    m4 = re.search(r"\*\*([\d,]+)〜([\d,]+)\*\*", c["R-4"])
    m6 = re.search(r"`vocabulary.py` \*\*≤ (\d+) 行\*\*、`comparators.py` \*\*≤ (\d+) 行\*\*、`recipes.py` \*\*≤ (\d+) 行\*\*", c["R-6"])
    assert m1 and m2 and m3 and m4 and m6 and u"**1 行も動かない**" in c["R-5"], u"封の予測の書き方が変わった"
    n = lambda s: int(s.replace(",", ""))
    return {"r1_pass": (int(m1.group(1)), int(m1.group(2))), "r1_stop": (int(m1.group(3)), int(m1.group(4))),
            "r2": (int(m2.group(1)), int(m2.group(2))), "r2_money": int(m2.group(3)), "r3": (int(m3.group(1)), int(m3.group(2))),
            "r4": (n(m4.group(1)), n(m4.group(2))), "r6": (int(m6.group(1)), int(m6.group(2)), int(m6.group(3)))}


def judgments(rec, seal):
    b = bounds(seal)
    J = {}
    c1 = recount_r1(rec[u"R1"][u"行"])
    ok1 = (b["r1_pass"][0] <= c1[u"P23"][u"通した"] <= b["r1_pass"][1] and b["r1_stop"][0] <= c1[u"P23"][u"止めた"] <= b["r1_stop"][1]
           and "N237" not in c1[u"P23 の通した id"] and "N277" not in c1[u"P23 の通した id"])
    J["R-1"] = u"当たり" if ok1 else u"外れ"
    c2 = recount_r2(rec[u"R2"])
    ok2 = (b["r2"][0] <= c2[u"離れた"] <= b["r2"][1] and c2[u"離れた 金額ほか"] == b["r2_money"] and c2[u"離れた 率"] == c2[u"離れた"]
           and c2[u"新 GROUNDED"] == 0 and not c2[u"判定が変わった書類"])
    J["R-2"] = u"当たり" if ok2 else u"外れ"
    c3 = recount_r3(rec[u"R3"][u"行"])
    J["R-3"] = u"当たり" if b["r3"][0] <= c3[u"P23 通した"] <= b["r3"][1] else u"外れ"
    J["R-4"] = u"当たり" if b["r4"][0] <= c2[u"VM P23"] <= b["r4"][1] else u"外れ"
    c5 = recount_r5(rec[u"R5"][u"行"])
    J["R-5"] = u"当たり" if not c5[u"動いた"] else u"外れ"
    e6 = rec[u"R6"]
    d = e6[u"engine の差分"]
    tests_ok = bool(e6.get(u"既存試験")) and all(t[u"rc"] == 0 for t in e6[u"既存試験"]) and not e6.get(u"封の 4 か所のほかに直した既存試験")
    ok6 = (d["adapters/xbrl/vocabulary.py"][u"挿入"] <= b["r6"][0] and d["adapters/xbrl/comparators.py"][u"挿入"] <= b["r6"][1]
           and d["adapters/xbrl/recipes.py"][u"挿入"] <= b["r6"][2] and d[u"core/"][u"差の行数"] == 0 and tests_ok)
    J["R-6"] = u"当たり" if ok6 else u"外れ"
    J["R-7"] = u"判定しない(段 2)"
    return J


def check_judgments(rec, seal):
    want = judgments(rec, seal)
    got = dict((k, v[u"判定"]) for k, v in rec[u"予測の判定"].items())
    assert sorted(got) == sorted(want), (sorted(got), sorted(want))
    for k in want:
        assert got[k] == want[k], (k, got[k], want[k])


# ----------------------------------------------------------------------------------------------------------------
# 文書に載せる表(記録から作る。文書はこの字を含まなければならない)
def render_blocks(rec, seal=None):
    seal = seal if seal is not None else jtext(SEAL)
    B = {}
    pr = rec[u"予測の判定"]
    L = [u"| # | 封の予測 | 実測 | 判定 |", u"|---|---|---|---|"]
    for k in sorted(pr, key=lambda s: int(s.split("-")[1])):
        L.append(u"| **%s** | %s | %s | **%s** |" % (k, cell(seal_cells(seal, k)[1]), cell(pr[k][u"実測"]), pr[k][u"判定"]))
    B["予測の表"] = u"\n".join(L)
    r1 = rec[u"R1"]
    c1 = recount_r1(r1[u"行"])
    L = [u"| 儀式 240 件 | 通した | 止めた | その他 |", u"|---|---:|---:|---:|"]
    L.append(u"| P22(対照。いまの既定) | %d | %d | %d |" % (c1[u"P22"][u"通した"], c1[u"P22"][u"止めた"], c1[u"P22"][u"その他"]))
    L.append(u"| **P23** | **%d** | **%d** | **%d** |" % (c1[u"P23"][u"通した"], c1[u"P23"][u"止めた"], c1[u"P23"][u"その他"]))
    B["R-1 の数"] = u"\n".join(L)
    L = [u"| id | 型 | 元の字 → 後の字 | 単位 | P22 | P23 |", u"|---|---|---|---|---|---|"]
    for r in r1[u"行"]:
        if r[u"P22"] == PASSED or r[u"P23"] == PASSED:
            L.append(u"| %s | %s | %s → %s | %s | %s | **%s** |" % (r[u"id"], r[u"型"], cell(r[u"元の字"]), cell(r[u"後の字"]), cell(r[u"単位"]), r[u"P22"], r[u"P23"]))
    B["R-1 の表"] = u"\n".join(L)
    L = [u"| id | 分類 | 値の差 | 1 最小単位 | 文脈 |", u"|---|---|---|---|---|"]
    for x in r1[u"通した P23 の一覧"]:
        L.append(u"| %s | %s | %s | %s | %s |" % (x[u"id"], cell(x[u"分類"]), x[u"値の差"], x[u"1 最小単位"], cell(x[u"文脈"])))
    B["R-1 の通した"] = u"\n".join(L)
    r2 = rec[u"R2"]
    L = [u"| doc | id | 単位 | 文の値 | P22 の生の値(recomputed) | 差(絶対値) | 向き | 文の抜粋 |", u"|---|---|---|---|---|---|---|---|"]
    for x in r2[u"動いた行"]:
        L.append(u"| %s | %s | %s | %s | %s | %.2f | %s | %s |" % (x[u"doc"], x[u"id"], cell(x[u"unit"]), x[u"value"], x[u"P22"][u"recomputed"],
                                                             abs(x[u"value"] - x[u"P22"][u"recomputed"]), x[u"向き"], cell((x[u"span"] or u"")[:48])))
    B["R-2 の動いた行"] = u"\n".join(L)
    c2 = recount_r2(r2)
    L = [u"| 項目 | 件数 |", u"|---|---:|",
         u"| 動いた行(全 state) | %d |" % c2[u"動いた"], u"| GROUNDED を離れた | %d |" % c2[u"離れた"],
         u"| うち 率(％・ポイント) | %d |" % c2[u"離れた 率"], u"| うち 金額ほか | %d |" % c2[u"離れた 金額ほか"],
         u"| 単位別 | %s |" % cell(u"・".join(u"%s %d" % (k, v) for k, v in sorted(c2[u"離れた 単位別"].items()))),
         u"| 新 GROUNDED | %d |" % c2[u"新 GROUNDED"], u"| GROUNDED のまま参照先だけ動いた | %d |" % c2[u"参照先だけ動いた"],
         u"| 離れた行のある書類 | %d |" % c2[u"離れた 書類数"], u"| 丸めの判定(R・T・丸め方)が変わった書類 | %d |" % len(c2[u"判定が変わった書類"]),
         u"| 書類 | %d |" % c2[u"書類数"], u"| claim の総数 | %s |" % comma(c2[u"claims"])]
    B["R-2 の数"] = u"\n".join(L)
    L = [u"| 無改変 67 書類 | GROUNDED | VALUE_MISMATCH |", u"|---|---:|---:|",
         u"| P22 | %s | %s |" % (comma(c2[u"GROUNDED P22"]), comma(c2[u"VM P22"])),
         u"| **P23** | **%s** | **%s** |" % (comma(c2[u"GROUNDED P23"]), comma(c2[u"VM P23"]))]
    B["R-4 の表"] = u"\n".join(L)
    b = rec[u"R2b"]
    L = [u"| 旗 truncate_abs_band だけを P22 に積む(R-2b) | 件数 |", u"|---|---:|",
         u"| 動いた行 | %d |" % b[u"動いた行の数"], u"| 切り捨てと判定された書類 | %d |" % b[u"切り捨てと判定された書類"],
         u"| 旗が効きうる行のある書類 | %d |" % b[u"旗が効きうる行のある書類数"]]
    for k, v in sorted(b[u"旗が効きうる行(P22 の生の claim から数えた)"].items()):
        L.append(u"| %s | %d |" % (cell(k), v))
    B["R-2b の表"] = u"\n".join(L)
    r3 = rec[u"R3"]
    c3 = recount_r3(r3[u"行"])
    L = [u"| 穴 B の注入 485 件 | 通した | 止めた | その他 |", u"|---|---:|---:|---:|",
         u"| P22(対照) | %d | %d | %d |" % (c3[u"P22 通した"], c3[u"P22 止めた"], c3[u"P22 その他"]),
         u"| **P23** | **%d** | **%d** | **%d** |" % (c3[u"P23 通した"], c3[u"P23 止めた"], c3[u"P23 その他"])]
    B["R-3 の表"] = u"\n".join(L)
    L = [u"| 書類 | id | 元の字 → 後の字 | 当期の fact | 前期の fact | P22 | P23 |", u"|---|---|---|---|---|---|---|"]
    for r in r3[u"行"]:
        if r[u"P22"][u"結果"].startswith(u"通した") or r[u"P23"][u"結果"].startswith(u"通した"):
            L.append(u"| %s | %s | %s → %s | %s | %s | %s | %s |" % (r[u"書類"], r[u"id"], cell(r[u"元の字"]), cell(r[u"後の字"]), r[u"当期の fact"], r[u"前期の fact"],
                                                           cell(r[u"P22"][u"結果"]), cell(r[u"P23"][u"結果"])))
    B["R-3 の通した"] = u"\n".join(L)
    c5 = recount_r5(rec[u"R5"][u"行"])
    L = [u"| 段 2 の材料 192 行の Core 自身 | 件数 |", u"|---|---:|", u"| 行 | %d |" % c5[u"行"], u"| 注入 | %d |" % c5[u"注入"],
         u"| P22 → P23 で動いた行 | %d |" % len(c5[u"動いた"]), u"| 注入で Core 自身 P22 が GROUNDED | %d |" % c5[u"P22 GROUNDED(注入)"],
         u"| 注入で Core 自身 P23 が GROUNDED | %d |" % c5[u"P23 GROUNDED(注入)"],
         u"| 対照: P22 の再計算が期を縛る P22 の記録と違った行 | %d |" % c5[u"対照の違い"]]
    B["R-5 の表"] = u"\n".join(L)
    e6 = rec[u"R6"]
    d = e6[u"engine の差分"]
    L = [u"| file | 挿入 | 削除 |", u"|---|---:|---:|"]
    for f in ("adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py"):
        L.append(u"| `%s` | %d | %d |" % (f, d[f][u"挿入"], d[f][u"削除"]))
    L.append(u"| `core/` | %d | |" % d[u"core/"][u"差の行数"])
    B["R-6 の表"] = u"\n".join(L)
    L = [u"| 4 か所のほかに直した既存試験 |", u"|---|"] + [u"| %s |" % cell(x) for x in e6[u"封の 4 か所のほかに直した既存試験"]]
    B["R-6 の直した試験"] = u"\n".join(L)
    return B


def pct1(a, b):
    return u"%.1f%%" % (100.0 * a / b)


def prose_facts(rec):
    P = {}
    pr = rec[u"予測の判定"]
    hit = sum(1 for v in pr.values() if v[u"判定"] == u"当たり")
    miss = sum(1 for v in pr.values() if v[u"判定"] == u"外れ")
    P["pred"] = u"**予測 機械判定 当たり %d / 外れ %d**(R-1〜R-6。R-7 は段 2 なので判定しない)。" % (hit, miss)
    d = rec[u"R6"][u"engine の差分"]
    v, c, r = d["adapters/xbrl/vocabulary.py"], d["adapters/xbrl/comparators.py"], d["adapters/xbrl/recipes.py"]
    P["head"] = u"engine の直し: `adapters/xbrl/vocabulary.py` 挿入 %d・削除 %d、`adapters/xbrl/comparators.py` 挿入 %d・削除 %d、`adapters/xbrl/recipes.py` 挿入 %d・削除 %d、`core/` %d 行。" % (
        v[u"挿入"], v[u"削除"], c[u"挿入"], c[u"削除"], r[u"挿入"], r[u"削除"], d[u"core/"][u"差の行数"])
    c1 = recount_r1(rec[u"R1"][u"行"])
    P["r1"] = u"儀式 240 件を P23 で回すと、通した %s・止めた %s(P22 は通した %s)。P22 で通した %d 件のうち P23 で止まったのは %d(率 %d・金額ほか %d)。N237・N277 は止まった。" % (
        F(c1[u"P23"][u"通した"], c1[u"行"]), F(c1[u"P23"][u"止めた"], c1[u"行"]), F(c1[u"P22"][u"通した"], c1[u"行"]), c1[u"P22"][u"通した"],
        len(c1[u"P22 で通して P23 で止めた id"]), c1[u"P22 で通して P23 で止めた 率"], c1[u"P22 で通して P23 で止めた 金額ほか"])
    P["r1ids"] = u"P23 でも通した id: %s。" % u"・".join(c1[u"P23 の通した id"])
    c2 = recount_r2(rec[u"R2"])
    P["r2"] = u"67 書類(claim %s)の無改変で、P22 から P23 に動いた行は %d。全部 GROUNDED → VALUE_MISMATCH で、率 %d(%s)・金額ほか %d。新 GROUNDED %d。書類 %d に散る。" % (
        comma(c2[u"claims"]), c2[u"動いた"], c2[u"離れた 率"], u"・".join(u"%s %d" % (k, v_) for k, v_ in sorted(c2[u"離れた 単位別"].items())),
        c2[u"離れた 金額ほか"], c2[u"新 GROUNDED"], c2[u"離れた 書類数"])
    P["r2rt"] = u"書類ごとの丸め方の判定(R・T・丸め方)が P22 と P23 で変わった書類は %d(書類 %d のうち切り捨て %d)。" % (
        len(c2[u"判定が変わった書類"]), c2[u"書類数"], c2[u"丸め方 P22"])
    b = rec[u"R2b"]
    opp = b[u"旗が効きうる行(P22 の生の claim から数えた)"]
    P["r2b"] = u"旗 `truncate_abs_band` だけを P22 に積むと、67 書類で動く行は %d。旗が効きうる行(切り捨てと判定された %d 書類で負の fact に GROUNDED した金額の claim)は %d(%d 書類)。" % (
        b[u"動いた行の数"], b[u"切り捨てと判定された書類"], sum(v_ for k, v_ in opp.items() if k.startswith(u"負の fact")), b[u"旗が効きうる行のある書類数"])
    c3 = recount_r3(rec[u"R3"][u"行"])
    P["r3"] = u"穴 B の注入 %d 件を P23 で再検証すると、通した %s・止めた %s・その他 %s(P22 は通した %s)。" % (
        c3[u"注入"], F(c3[u"P23 通した"], c3[u"注入"]), F(c3[u"P23 止めた"], c3[u"注入"]), F(c3[u"P23 その他"], c3[u"注入"]), F(c3[u"P22 通した"], c3[u"注入"]))
    P["r4"] = u"無改変の VALUE_MISMATCH は P22 が %s、P23 が %s(差 %d)。GROUNDED は %s から %s。" % (
        comma(c2[u"VM P22"]), comma(c2[u"VM P23"]), c2[u"VM P23"] - c2[u"VM P22"], comma(c2[u"GROUNDED P22"]), comma(c2[u"GROUNDED P23"]))
    c5 = recount_r5(rec[u"R5"][u"行"])
    P["r5"] = u"段 2 の材料 %d 行(注入 %d)の Core 自身は、P22 から P23 で動いた行が %d。対照の P22 の再計算は期を縛る P22 の記録と全行一致(違った行 %d)。" % (
        c5[u"行"], c5[u"注入"], len(c5[u"動いた"]), c5[u"対照の違い"])
    e6 = rec[u"R6"]
    P["r6"] = u"既存試験: %s。封の 4 か所のほかに直した既存試験は %d 本。" % (
        u"・".join(u"%s → %s" % (t[u"コマンド"], t[u"最後の行"]) for t in e6.get(u"既存試験", [])), len(e6[u"封の 4 か所のほかに直した既存試験"]))
    P["secs"] = u"記録の所要秒: %s。" % json.dumps(rec[u"所要秒"], ensure_ascii=False, sort_keys=True)
    return P


def mutation_table(rec):
    m = rec[u"変異(engine。手で走らせた)"]
    L = [u"| # | 変異 | 予測 | 実測 |", u"|---|---|---|---|"]
    for x in m[u"表"]:
        L.append(u"| %s | %s | %s | %s |" % (x[u"#"], cell(x[u"変異"]), cell(x[u"予測"]), cell(x[u"実測"])))
    return u"\n".join(L)


def check_mutation_record(rec):
    m = rec[u"変異(engine。手で走らせた)"]
    assert len(m[u"表"]) >= 5, u"engine の変異が 5 通り未満"
    assert u"手で走らせた" in m[u"注記"]
    for x in m[u"表"]:
        assert set(x) >= {u"#", u"変異", u"予測", u"実測"}, x


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
    t = re.sub(r"[A-Za-z_][A-Za-z_0-9\-]*\d[A-Za-z_0-9\-]*", u"", t)      # S100YMFV・N076・R-1・P22・sha16 など
    t = re.sub(r"(?m)^#+ [\d\-]+\.?", u"", t)                # 見出しの節番号
    t = re.sub(r"段 \d", u"", t)                                 # 工程の名前(段 1・段 2)
    t = t.replace(u"0 USD", u"")
    t = re.sub(r"§[\d\-]+", u"", t)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    return re.findall(r"\d[\d,\.]*", t)


def check_doc(rec, doc):
    B = render_blocks(rec)
    for k, v in B.items():
        assert v in doc, u"文書に『%s』の表(記録から作った字)が無い" % k
    for k, v in prose_facts(rec).items():
        assert v in doc, u"文書に数のある文『%s』(記録から作った字)が無い" % k
    assert mutation_table(rec) in doc, u"文書に変異の表(記録の写し)が無い"
    assert rec[u"変異(engine。手で走らせた)"][u"注記"] in doc
    assert u"判定しない(段 2)" in doc
    for lit in (u"comparators.py は零行", u"封 §1 の「写しの帯」", u"_mag_trunc(profile, rounding)", u"P24・P25"):
        assert lit in doc, lit
    res = residual_numbers(doc, rec)
    assert res == ALLOWED_RESIDUAL, u"文書の散文に、記録に縛られない数が在る: %s" % res


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


def engine_ok():
    """いまの engine が、測った時点の sha か、宣言された遷移の値であること。"""
    for rel, want in sorted(ENGINE_AT_MEASURE.items()):
        got = sha16(rel)
        if got != want and rel in ENGINE_LATER:
            later, seal_rel = ENGINE_LATER[rel]
            assert git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), seal_rel
            assert got == later, (rel, got, later)
            continue
        assert got == want, u"**%s が測った時点から動いている(宣言された遷移が要る)**: %s != %s" % (rel, got, want)


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

    def test_4_document_tables_equal_the_record(self):
        check_doc(self.rec, self.doc)
        check_mutation_record(self.rec)

    def test_5_facts_as_measured(self):
        r = self.rec
        c1 = recount_r1(r[u"R1"][u"行"])
        self.assertEqual((c1[u"P23"][u"通した"], c1[u"P23"][u"止めた"], c1[u"P22"][u"通した"]), (2, 238, 15))
        self.assertEqual(c1[u"P23 の通した id"], ["N069", "N096"])
        self.assertEqual(len(c1[u"P22 で通して P23 で止めた id"]), 13)
        self.assertIn("N237", c1[u"P22 で通して P23 で止めた id"])
        self.assertIn("N277", c1[u"P22 で通して P23 で止めた id"])
        c2 = recount_r2(r[u"R2"])
        self.assertEqual((c2[u"動いた"], c2[u"離れた"], c2[u"離れた 率"], c2[u"離れた 金額ほか"], c2[u"新 GROUNDED"]), (8, 8, 8, 0, 0))
        self.assertEqual((c2[u"VM P22"], c2[u"VM P23"]), (1410, 1418))
        c3 = recount_r3(r[u"R3"][u"行"])
        self.assertEqual((c3[u"P23 通した"], c3[u"P22 通した"]), (0, 1))
        c5 = recount_r5(r[u"R5"][u"行"])
        self.assertEqual(c5[u"動いた"], [])
        self.assertEqual(r[u"予測の判定"]["R-7"][u"判定"], u"判定しない(段 2)")

    def test_6_engine_is_the_one_measured_or_a_declared_transition(self):
        engine_ok()
        self.assertTrue(self.rec[u"環境"][u"HEAD"].startswith(SEAL_COMMIT))

    def test_7_numstat_in_the_record_is_the_engine_diff_from_the_seal_commit(self):
        """engine が測った時点の sha のままのときだけ: 封の commit からの差分の行数が記録と一致(動いたら宣言された遷移の後なので比べない)。"""
        for rel, want in ENGINE_AT_MEASURE.items():
            if sha16(rel) != want:
                self.skipTest(u"engine が宣言された遷移の後")
        d = self.rec[u"R6"][u"engine の差分"]
        for f in ("adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py"):
            o = git("diff", "--numstat", SEAL_COMMIT, "--", f).stdout.split()
            ins, dele = (int(o[0]), int(o[1])) if len(o) >= 2 else (0, 0)
            self.assertEqual((ins, dele), (d[f][u"挿入"], d[f][u"削除"]), f)

    def test_8_core_is_untouched_and_default_is_p22_in_step_1(self):
        out = git("diff", "--numstat", SEAL_COMMIT, "--", "core")
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout.strip(), u"", u"core/ が封の commit から動いている")
        src = jtext(VOCAB)
        self.assertEqual(re.findall(r'(?m)^DEFAULT_PROFILE = "(P\d+)"$', src), ["P26"], u"段 1 の commit 時点は既定が P22 だった。2026-10-23 の P26 の段 2(封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)で P26")
        from adapters.xbrl import vocabulary as V
        self.assertEqual(V.DEFAULT_PROFILE, "P26")
        self.assertTrue(V.PROFILES["P23"].truncate_abs_band)
        self.assertFalse(V.PROFILES["P22"].truncate_abs_band)

    def test_9_r7_is_not_judged_and_the_seal_was_not_edited(self):
        self.assertEqual(self.rec[u"予測の判定"]["R-7"][u"判定"], u"判定しない(段 2)")
        orig = git("show", "%s:./%s" % (SEAL_COMMIT, SEAL_REL))
        self.assertEqual(orig.returncode, 0)
        self.assertEqual(jtext(SEAL), orig.stdout, u"封が封の commit から変わった(数を見てから封を直さない)")

    def test_10_cache_inputs_match_the_record(self):
        inp = self.rec[u"入力の sha256"]
        names = sorted(inp[u"書類 67(経営分析の文を持つ)の sha256"])
        if not have_cache(names):
            self.skipTest(u"cache(~/.cache/audit-core/edinet/*.zip)が無い")
        for d in names:
            self.assertEqual(sha_path(os.path.join(CACHE, d + ".zip")), inp[u"書類 67(経営分析の文を持つ)の sha256"][d], d)
        for rel in INPUT_SHAS:
            real = "fixtures/xbrl/ritual_2026-10-20_p22.json" if rel == "fixtures/xbrl/ritual_2026-10-20.json" else rel      # 2026-10-23(P26 の段 2。封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)
            self.assertEqual(sha_path(os.path.join(ROOT, real)), inp[rel], rel)
        self.assertEqual(sha_path(os.path.join(ROOT, "fixtures/xbrl/ai_prose_instance_2026-10-09.zip")), inp[u"儀式の同梱書類"])


def run_script(args):
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=ROOT, capture_output=True, text=True)


def _script():
    import importlib.util
    spec = importlib.util.spec_from_file_location("rounding_script_for_gate", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class RerunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)

    def _need(self, docs):
        if not have_cache(docs):
            self.skipTest(u"cache が無い")
        if not labels_ok():
            self.skipTest(u"標準タクソノミのラベルが無い(fixtures/xbrl/TAXONOMY_LABELS_README.md)")

    def test_light_r2_matches_the_record(self):
        self._need(LIGHT_R2_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "r2.json")
            p = run_script(["--stage", "r2", "--docs", ",".join(LIGHT_R2_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)[u"R2"]
        want = [x for x in self.rec[u"R2"][u"動いた行"] if x[u"doc"] in LIGHT_R2_DOCS]
        self.assertTrue(want)
        self.assertEqual(got[u"動いた行"], want)
        self.assertEqual(got[u"書類"], [d for d in self.rec[u"R2"][u"書類"] if d[u"doc"] in LIGHT_R2_DOCS])

    def test_light_r3_matches_the_record(self):
        self._need(LIGHT_R3_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "r3.json")
            p = run_script(["--stage", "r3", "--docs", ",".join(LIGHT_R3_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)[u"R3"][u"行"]
        want = [r for r in self.rec[u"R3"][u"行"] if r[u"書類"] in LIGHT_R3_DOCS]
        self.assertTrue(want)
        self.assertEqual(got, want)

    @unittest.skipUnless(RUN_HEAVY, u"AUDIT_CORE_ROUNDING=1 のときだけ走る(全部の走らせ直し。約 7 分)")
    def test_heavy_everything_matches_the_record(self):
        if not (have_cache(sorted(self.rec[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"])) and labels_ok()):
            self.fail(u"AUDIT_CORE_ROUNDING=1 なのに cache かラベルが揃っていない")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "all.json")
            p = run_script(["--stage", "all", "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)
        for sec in (u"R1", u"R2", u"R2b", u"R3", u"R5"):
            a, b = got[sec], self.rec[sec]
            if sec == u"R1":
                a = dict((k, v) for k, v in a.items() if k != u"所要秒")
                b = dict((k, v) for k, v in b.items() if k != u"所要秒")
            self.assertEqual(a, b, sec)
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

    def _mut(self):
        return copy.deepcopy(self.rec)

    def test_baseline_is_green(self):
        check_record(self.rec)
        check_inputs(self.rec)
        check_judgments(self.rec, self.seal)
        check_doc(self.rec, self.doc)
        check_mutation_record(self.rec)
        engine_ok()

    def test_m1_flip_one_r1_row_to_passed(self):
        """N237(負の金額の符号つき切り捨て)が P23 でも通ったことにすると、集計・通した一覧・判定のどれかで赤。"""
        r = self._mut()
        for x in r[u"R1"][u"行"]:
            if x[u"id"] == "N237":
                x[u"P23"] = PASSED
        self._red(check_record, r)

    def test_m2_drop_one_moved_row(self):
        r = self._mut()
        r[u"R2"][u"動いた行"].pop()
        self._red(check_record, r)

    def test_m3_change_the_value_mismatch_count_of_one_document(self):
        r = self._mut()
        for d in r[u"R2"][u"書類"]:
            if d[u"states P23"].get("VALUE_MISMATCH"):
                d[u"states P23"]["VALUE_MISMATCH"] += 7
                break
        self._red(check_record, r)

    def test_m4_change_a_judgment_word(self):
        r = self._mut()
        r[u"予測の判定"]["R-2"][u"判定"] = u"外れ"
        self._red(check_judgments, r, self.seal)

    def test_m5_a_money_row_among_the_moved_is_seen(self):
        """動いた行に金額の行が 1 件混ざったら R-2 は外れ(予測の外れ方『金額 1 以上』)。判定と記録の集計の両方が赤になる。"""
        r = self._mut()
        r[u"R2"][u"動いた行"][0][u"unit"] = u"百万円"
        self._red(check_record, r)
        r2 = self._mut()
        for x in r2[u"R2"][u"動いた行"]:
            x[u"unit"] = u"百万円"
        r2[u"R2"][u"集計"][u"GROUNDED を離れた行のうち 率(％・%・ポイント)"] = 0
        r2[u"R2"][u"集計"][u"GROUNDED を離れた行のうち 金額ほか(率でない)"] = len(r2[u"R2"][u"動いた行"])
        r2[u"R2"][u"集計"][u"GROUNDED を離れた行の単位別"] = {u"百万円": len(r2[u"R2"][u"動いた行"])}
        self.assertEqual(judgments(r2, self.seal)["R-2"], u"外れ")

    def test_m6_a_new_grounded_row_is_seen(self):
        r = self._mut()
        x = r[u"R2"][u"動いた行"][0]
        x[u"P22"][u"state"], x[u"P23"][u"state"] = "VALUE_MISMATCH", "GROUNDED"
        x[u"向き"] = u"VALUE_MISMATCH → GROUNDED"
        self._red(check_record, r)
        self.assertEqual(recount_r2(r[u"R2"])[u"新 GROUNDED"], 1)

    def test_m7_a_changed_rounding_decision_is_seen(self):
        r = self._mut()
        r[u"R2"][u"書類"][0][u"丸めの判定 P23"] = dict(r[u"R2"][u"書類"][0][u"丸めの判定 P23"], **{u"丸め方": u"truncate" if r[u"R2"][u"書類"][0][u"丸めの判定 P22"][u"丸め方"] != u"truncate" else u"round"})
        self._red(check_record, r)
        self.assertEqual(judgments(r, self.seal)["R-2"], u"外れ")

    def test_m8_a_p23_pass_in_the_hole_b_is_seen(self):
        r = self._mut()
        x = r[u"R3"][u"行"][0]
        x[u"P23"] = dict(x[u"P23"], **{u"結果": u"通した(参照先が前期へ移った)"})
        self._red(check_record, r)

    def test_m9_a_moved_core_row_is_seen(self):
        r = self._mut()
        r[u"R5"][u"行"][0][u"Core 自身 P23"] = {u"state": "GROUNDED", u"参照先": u"x"}
        self._red(check_record, r)

    def test_m10_p22_column_must_stay_the_record_of_the_default(self):
        """旗が偽の側(P22 の欄)を 1 行動かすと、儀式の記録・期を縛る P22 の記録との突き合わせで赤。"""
        r = self._mut()
        r[u"R1"][u"行"][5][u"P22"] = PASSED if r[u"R1"][u"行"][5][u"P22"] != PASSED else STOPPED
        self._red(check_record, r)
        r = self._mut()
        r[u"R3"][u"行"][7][u"P22"] = dict(r[u"R3"][u"行"][7][u"P22"], **{u"state": u"GROUNDED"})
        self._red(check_record, r)

    def test_m11_a_number_in_a_document_table_is_red(self):
        for blk in ("R-1 の数", "R-2 の数", "R-3 の表", "R-4 の表"):
            v = render_blocks(self.rec)[blk]
            i = re.search(r"\d", v).start()
            bad = self.doc.replace(v, v[:i] + u"9" + v[i + 1:], 1)
            self.assertNotEqual(bad, self.doc)
            self._red(check_doc, self.rec, bad)

    def test_m12_a_number_in_a_prose_sentence_is_red(self):
        for k, v in prose_facts(self.rec).items():
            m = re.search(r"\d", v)
            if not m:
                continue
            bad = self.doc.replace(v, v[:m.start()] + (u"9" if v[m.start()] != u"9" else u"8") + v[m.start() + 1:], 1)
            self.assertNotEqual(bad, self.doc, k)
            self._red(check_doc, self.rec, bad)

    def test_m13_a_new_unbound_number_in_prose_is_red(self):
        bad = self.doc + u"\n\nなお、書類のうち 99 件は別の扱いになった。\n"
        self._red(check_doc, self.rec, bad)

    def test_m14_a_spoiled_input_digest_is_red(self):
        r = self._mut()
        k = sorted(r[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"])[3]
        r[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"][k] = u"0" * 64
        self._red(check_inputs, r)

    def test_m15_mutation_record_must_have_five_rows(self):
        r = self._mut()
        r[u"変異(engine。手で走らせた)"][u"表"] = r[u"変異(engine。手で走らせた)"][u"表"][:4]
        self._red(check_mutation_record, r)

    def test_m16_a_wrong_engine_sha_is_red(self):
        global ENGINE_AT_MEASURE, ENGINE_LATER
        old, old_later = dict(ENGINE_AT_MEASURE), dict(ENGINE_LATER)
        try:
            ENGINE_AT_MEASURE = dict(old, **{"adapters/xbrl/recipes.py": "0" * 16})
            # 2026-10-21(pin の遷移): 宣言された遷移が在ると「測った時点と違う sha」は受け入れられてしまうので、この変異では遷移の宣言を外して(空にして)確かめる
            ENGINE_LATER = {}
            self._red(engine_ok)
        finally:
            ENGINE_AT_MEASURE, ENGINE_LATER = old, old_later
        engine_ok()

    def test_m17_flag_made_identity_turns_r1_red(self):
        """旗を恒等(偽)にすると、R-1 の再計算(儀式 240 件を P23 で)が記録と食い違い、N237・N277 が通る。
        engine の file は書き換えない(in-process で P23 の旗を偽にして、出るとき必ず戻す)。"""
        if not labels_ok():
            self.skipTest(u"標準タクソノミのラベルが無い")
        import dataclasses
        m = _script()
        from adapters.xbrl import vocabulary as V
        labels, why = m.RIT.check_labels()
        self.assertFalse(why)
        with io.open(os.path.join(ROOT, m.RIT.ZIP_REL), "rb") as fh:
            zb = fh.read()
        want = dict(((x[u"id"], x[u"型"]), x[u"P23"]) for x in self.rec[u"R1"][u"行"])
        base = m.RIT.build(zb, "P23", labels)
        got = dict(((x[u"id"], x[u"型"]), x[u"結果"]) for x in base[u"注入の一覧"])
        self.assertEqual(got, want, u"旗が真のままの再計算は記録と一致")
        old = V.PROFILES["P23"]
        V.PROFILES["P23"] = dataclasses.replace(old, truncate_abs_band=False)
        try:
            bad = m.RIT.build(zb, "P23", labels)
        finally:
            V.PROFILES["P23"] = old
        self.assertIs(V.PROFILES["P23"], old)
        got2 = dict(((x[u"id"], x[u"型"]), x[u"結果"]) for x in bad[u"注入の一覧"])
        self.assertNotEqual(got2, want)
        self.assertEqual(sorted(k[0] for k in got2 if got2[k] == PASSED and want[k] != PASSED), ["N237", "N277"])


if __name__ == "__main__":
    unittest.main()
