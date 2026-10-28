# -*- coding: utf-8 -*-
u"""語彙の登録と枠の取り直し P24 の段 1 の結果 ― 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md §2(W-1〜W-9)の結果を縛る門。

記録: ``fixtures/xbrl/vocab_2026-10-21.json``(``measure/xbrl_vocab_2026-10-21.py --stage all --run-tests`` の出力)。
文書: ``docs/XBRL_VOCAB_RESULT_2026-10-21.md``。

この門がやること(どれも、壊した標本で赤くなることを ``MutationTest`` が毎回確かめる):
  1. 入力(書類 67 本・67 の外 214 本の sha256・他の記録の sha256)を**字で留めた digest / sha256** に縛る。cache が在る機械では実物の sha256 も記録と一致させる。
  2. 記録の行(W-1〜W-3 の動いた行と書類別・W-4 の注入 485・W-5 の儀式・W-6 の注入・W-7 の 214 書類・補助の 192 行)から、集計・向き・型別を
     **script の関数を使わずに** 数え直し、記録の集計と一致させる。対照(P23 の再計算が、丸めの記録 ``rounding_2026-10-21.json`` の同じ行と一致すること
     = 旗が偽の側は 1 行も変わらない)も、門が自分で記録同士を突き合わせる。
  3. 予測 W-1〜W-9 の判定を、封の字から読んだ幅と記録の行から**門が自分で**求め、記録の判定と文書の表と一致させる。
  4. 文書の表(予測・W-1〜W-8 の数)を記録から作った字と完全一致させる。散文の数のある文は ``prose_facts`` が記録から作り、文書がその字を含むことを縛る。
     それ以外の散文に算用数字が在れば ``residual_numbers`` が見つけて赤にする(コード片・識別子・日付・節の番号は除く)。散文は漢数字で書く。
  5. engine の sha(測った時点の vocabulary.py・comparators.py・recipes.py・registry_setup.py)を字で留め、いまの engine が同じか宣言された遷移であること。
     ``core/`` が封の commit から 0 行であること。``DEFAULT_PROFILE`` が P22 のままであること(段 1)。封が封の commit から 1 字も変わっていないこと。
  6. cache とラベルが在る機械では、軽い走らせ直し(W-1〜W-3 を 2 書類、W-4 を 1 書類、W-7 を 67 の外の 3 書類)を script で走らせて記録の該当行と一致。
     全部の走らせ直し(約 三十分)は ``AUDIT_CORE_VOCAB=1`` のときだけ。
縛っていないもの: 新 GROUNDED・VALUE_MISMATCH → UNVERIFIABLE の行の「正しさ」(人の読み。試作 v3.1 の読みで、結果文書に書く)、
  限界の文の主張の中身、変異(engine)の手の実測そのもの(表は記録の写しを縛るだけ)、tests/measure 全体の所要、
  漢数字で書いた数(``residual_numbers`` は算用数字だけを探す。散文の数は記録から作った字で縛る約束)。
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
REC = os.path.join(ROOT, "fixtures", "xbrl", "vocab_2026-10-21.json")
DOC = os.path.join(ROOT, "docs", "XBRL_VOCAB_RESULT_2026-10-21.md")
SEAL_REL = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SEAL_COMMIT = "08987d0"
SCRIPT = os.path.join(ROOT, "measure", "xbrl_vocab_2026-10-21.py")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
RUN_HEAVY = os.environ.get("AUDIT_CORE_VOCAB") == "1"
ROUNDING = os.path.join(ROOT, "fixtures", "xbrl", "rounding_2026-10-21.json")
VOCAB = os.path.join(ROOT, "adapters", "xbrl", "vocabulary.py")
LIGHT_W1_DOCS = ("S100YUHC", "S100YYK8")       # 動いた行: 枠の取り直し・資金の句・CF 合計の符号が在る書類
LIGHT_W4_DOCS = ("S100YXLE",)
LIGHT_W7_DOCS = ("S100YRHD", "S100YRHF", "S100YTYH")
RATE_UNITS = (u"％", u"%", u"ポイント")
FRAME_REASONS = ("other_frame", "ambiguous(member)")

#: **字で留める**(記録の値の写し。定数から作らない)。
DOCS67_DIGEST = "118ec1015494db404b74dbd65b72bddfd2356459749d6f10dc910e5a1348429f"       # 書類 67 本の docID\tsha256 を sorted で \n 結合した sha256(丸めの門と同じ集合)
DOCS214_DIGEST = "1b36b8f77e878429976f46b2fcf377bbe76ecb42343fcfd4a22a826e015b23af"      # 67 の外 214 本の同じ形の sha256(記録の入力の欄の値。測った時点)
INPUT_SHAS = {
    "fixtures/xbrl/rounding_2026-10-21.json": "c39641935e08350acf4b6032fff14cb35f317f8e551411591933d84e0b468d94",
    "fixtures/xbrl/period_bind_2026-10-20.json": "dfcf8d94dadf51ef0d525b74edf72dff8a009dce7352c453c8bf6e5db2db9b60",
    "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json": "c3068024ff8c2812fabbf54e36f50b1cedeccb7955e9455603d1a17018418149",
    "fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json": "3b13d26f81906ae47696c95c2c0e21322579bcdabcde3a133b5a96970e7c52f6",
}
RITUAL_ZIP_SHA = "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799"
#: 測った時点の engine(sha256 の先頭 16 桁)。comparators.py は 0 行(封 §1 は comparators.py に触らない)。
ENGINE_AT_MEASURE = {"adapters/xbrl/vocabulary.py": "83498c04a7b70396", "adapters/xbrl/comparators.py": "d8706338325e725b",
                     "adapters/xbrl/recipes.py": "3461c3f8b7af6675", "adapters/xbrl/registry_setup.py": "9a0b08954cf22639"}
#: 段 2(既定の切り替え)などで動いたときの宣言された遷移: {path: (後の sha16, 遷移を宣言した封の path)}。段 1 の commit 時点では空だった。
#: 2026-10-21 追記(pin の遷移): 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(最後の枝 P25 の段 1。engine を変える。人間の事前承認 2026-10-21)で
#: vocabulary.py に旗 last_branch_names_only_if_evidence・P25・PROFILES の登録(+7 行)、recipes.py に最後の枝の証拠の判定の塊(+72 行・既存の行は 1 つも書き換えない)、
#: registry_setup.py に理由 no_same_value(+2 行)を足した(DEFAULT_PROFILE は P22 のまま)。上の ENGINE_AT_MEASURE は残す(測った時点の値)。
#: 受け入れるのは、その封が履歴に在り、値が P25 の段 1 の後の値のときだけ。
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"    # 2026-10-22 追記: P26 の段 1(下の ENGINE_LATER の遷移)
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
SEAL_DEFAULT_P27 = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"    # 2026-10-28 追記: 既定を P26 -> P27 に切り替える 段 2(下の遷移。vocabulary.py の DEFAULT_PROFILE の 1 行と注記 +5 行・-1 行、verify_document.py の docstring の 1 行 +1 行・-1 行だけ)
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
STOPPED_UNV = "detected:UNVERIFIABLE"


# ----------------------------------------------------------------------------------------------------------------
# 独立の数え直し(script の関数を使わない)
def recount_w123(sec):
    mv = sec[u"動いた行"]
    docs = sec[u"書類"]
    S = lambda r, side: r[side][u"state"]
    new_g = [r for r in mv if S(r, u"P23") != "GROUNDED" and S(r, u"P24") == "GROUNDED"]
    lost = [r for r in mv if S(r, u"P23") == "GROUNDED" and S(r, u"P24") != "GROUNDED"]
    g2g = [r for r in mv if S(r, u"P23") == "GROUNDED" and S(r, u"P24") == "GROUNDED"]
    vm2unv = [r for r in mv if S(r, u"P23") == "VALUE_MISMATCH" and S(r, u"P24") == "UNVERIFIABLE"]
    frame = [r for r in vm2unv if r[u"P24"][u"reason"] in FRAME_REASONS]
    w6 = [r for r in mv if S(r, u"P24") in ("GROUNDED", "UNVERIFIABLE") and not (S(r, u"P23") == "UNVERIFIABLE" and S(r, u"P24") == "UNVERIFIABLE")]
    st = lambda side, s: sum(d[side].get(s, 0) for d in docs)
    return {u"動いた": len(mv), u"動いた(書類別の合計)": sum(d[u"動いた"] for d in docs), u"新 GROUNDED": len(new_g), u"離れた": len(lost), u"G→G": len(g2g),
            u"VM→UNV": len(vm2unv), u"枠 VM→UNV": len(frame), u"other_frame": sum(1 for r in frame if r[u"P24"][u"reason"] == "other_frame"),
            u"ambiguous(member)": sum(1 for r in frame if r[u"P24"][u"reason"] == "ambiguous(member)"),
            u"枠の GROUNDED": sum(1 for r in new_g if r[u"型"] == u"枠の取り直し"),
            u"新 GROUNDED の型": dict((k, sum(1 for r in new_g if r[u"型"] == k)) for k in sorted({r[u"型"] for r in new_g})),
            u"新しい VM": sum(1 for r in mv if S(r, u"P23") != "VALUE_MISMATCH" and S(r, u"P24") == "VALUE_MISMATCH"),
            u"W-6 の対象": len(w6), u"書類数": len(docs), u"claims": sum(d[u"claims"] for d in docs),
            u"GROUNDED P23": st(u"states P23", "GROUNDED"), u"GROUNDED P24": st(u"states P24", "GROUNDED"),
            u"VM P23": st(u"states P23", "VALUE_MISMATCH"), u"VM P24": st(u"states P24", "VALUE_MISMATCH"),
            u"UNV P23": st(u"states P23", "UNVERIFIABLE"), u"UNV P24": st(u"states P24", "UNVERIFIABLE"),
            u"PNF P23": st(u"states P23", "POINTER_NOT_FOUND"), u"PNF P24": st(u"states P24", "POINTER_NOT_FOUND")}


def recount_w4(rows):
    n = len(rows)
    passed = lambda s: s.startswith(u"通した")
    return {u"注入": n, u"P24 通した": sum(1 for r in rows if passed(r[u"P24"][u"結果"])), u"P23 通した": sum(1 for r in rows if passed(r[u"P23"][u"結果"])),
            u"P24 止めた": sum(1 for r in rows if r[u"P24"][u"結果"] == u"止めた"), u"P24 その他": sum(1 for r in rows if r[u"P24"][u"結果"] == u"その他"),
            u"違う行(結果, state)": sum(1 for r in rows if (r[u"P23"][u"結果"], r[u"P23"][u"state"]) != (r[u"P24"][u"結果"], r[u"P24"][u"state"])),
            u"違う行(全部)": sum(1 for r in rows if r[u"P23"] != r[u"P24"])}


def recount_w5(rows):
    both = [r for r in rows if r[u"P23"] is not None and r[u"P24"] is not None]
    return {u"P24 の行": sum(1 for r in rows if r[u"P24"] is not None), u"P23 の行": sum(1 for r in rows if r[u"P23"] is not None),
            u"共通": len(both), u"P24 の通した id": [r[u"id"] for r in rows if r[u"P24"] == PASSED],
            u"P23 の通した id": [r[u"id"] for r in rows if r[u"P23"] == PASSED],
            u"P24 の止めた": sum(1 for r in rows if r[u"P24"] == STOPPED), u"P24 のその他": sum(1 for r in rows if r[u"P24"] not in (None, PASSED, STOPPED)),
            u"VM→UNV": sum(1 for r in both if r[u"P23"] == STOPPED and r[u"P24"] == STOPPED_UNV),
            u"結果が違う共通の行": sum(1 for r in both if r[u"P23"] != r[u"P24"])}


def recount_w6(rows):
    done = [x for x in rows if x.get(u"変え方")]
    st = lambda x, p: x[p].get(u"state") or x[p].get(u"結果")
    return {u"行": len(rows), u"注入": len(done), u"作れなかった": len(rows) - len(done),
            u"P24 G": sum(1 for x in done if st(x, u"P24") == "GROUNDED"), u"P24 UNV": sum(1 for x in done if st(x, u"P24") == "UNVERIFIABLE"),
            u"P24 VM": sum(1 for x in done if st(x, u"P24") == "VALUE_MISMATCH"), u"P23 G": sum(1 for x in done if st(x, u"P23") == "GROUNDED"),
            u"P23 UNV": sum(1 for x in done if st(x, u"P23") == "UNVERIFIABLE"),
            u"P24 その他": sum(1 for x in done if st(x, u"P24") not in ("GROUNDED", "UNVERIFIABLE", "VALUE_MISMATCH")),
            u"対象の行": len({(x[u"doc"], x[u"id"]) for x in rows})}


def recount_w7(rows):
    withc = [r for r in rows if r[u"claims P23"] >= 1]
    moved = [m for r in rows for m in r[u"動いた行"]]
    return {u"書類": len(rows), u"claim≥1": len(withc), u"claim≥1(P24)": sum(1 for r in rows if r[u"claims P24"] >= 1),
            u"claims P23": sum(r[u"claims P23"] for r in rows), u"claims P24": sum(r[u"claims P24"] for r in rows), u"動いた行": len(moved),
            u"新 G": sum(1 for m in moved if m[u"P23"][u"state"] != "GROUNDED" and m[u"P24"][u"state"] == "GROUNDED"),
            u"VM→UNV": sum(1 for m in moved if m[u"P23"][u"state"] == "VALUE_MISMATCH" and m[u"P24"][u"state"] == "UNVERIFIABLE"),
            u"区分": dict((k, sum(1 for r in rows if r[u"区分"] == k)) for k in sorted({r[u"区分"] for r in rows})),
            u"種別": dict((k, sum(1 for r in rows if str(r[u"種別"]) == k)) for k in sorted({str(r[u"種別"]) for r in rows}))}


def recount_s2(rows):
    return {u"行": len(rows), u"注入": sum(1 for r in rows if r[u"注入か"]),
            u"動いた": sorted((r[u"doc"], r[u"id"]) for r in rows if r[u"Core 自身 P23"] != r[u"Core 自身 P24"]),
            u"P23 G(注入)": sum(1 for r in rows if r[u"注入か"] and r[u"Core 自身 P23"][u"state"] == "GROUNDED"),
            u"P24 G(注入)": sum(1 for r in rows if r[u"注入か"] and r[u"Core 自身 P24"][u"state"] == "GROUNDED")}


def reading_category(t):
    return re.split(r"[(（:：]", t)[0].strip()


def check_readings(rec):
    """試作 v3.1 の人の読み(司令塔の席の読み。実装席の読みではない)が、今回の動いた行と (doc, id)・向き・型・state・reason・pointers まで同じ行に付いている。
    読みの正しさ自体は縛れない(人の読み)。縛るのは『読みが今回の行のものであること』と『新 GROUNDED の読みが全部「正」であること』だけ。"""
    rows = rec[u"試作の読み"][u"行"]
    mine = dict(((r[u"doc"], r[u"id"]), r) for r in rec[u"W1W2W3"][u"動いた行"])
    assert sorted((r[u"doc"], r[u"id"]) for r in rows) == sorted(mine), u"試作の読みの行が今回の動いた行と違う"
    for r in rows:
        m = mine[(r[u"doc"], r[u"id"])]
        assert (r[u"向き"], r[u"型"]) == (m[u"向き"], m[u"型"]), (r[u"doc"], r[u"id"])
        assert (r[u"試験 state(前)"], r[u"試験 reason(前)"], r[u"試験 pointers(前)"], r[u"試験 state(後)"], r[u"試験 reason(後)"], r[u"試験 pointers(後)"]) == (
            m[u"P23"][u"state"], m[u"P23"][u"reason"], m[u"P23"][u"pointers"], m[u"P24"][u"state"], m[u"P24"][u"reason"], m[u"P24"][u"pointers"]), (r[u"doc"], r[u"id"])
        assert r[u"読み"].strip(), (r[u"doc"], r[u"id"])
        c = reading_category(r[u"読み"])
        if m[u"P23"][u"state"] != "GROUNDED" and m[u"P24"][u"state"] == "GROUNDED":
            assert c == u"正", (r[u"doc"], r[u"id"], r[u"読み"])           # 新 GROUNDED の読みは全部「正」(偽を 1 件でも書いたら赤)
        if m[u"P23"][u"state"] == "VALUE_MISMATCH" and m[u"P24"][u"state"] == "UNVERIFIABLE":
            assert c in (u"正しい文", u"文が違う", u"分からない"), (r[u"doc"], r[u"id"], r[u"読み"])
    assert len(rec[u"試作の読み"][u"試作の記録"][u"sha256"]) == 64


def recount_readings(rec):
    rows = rec[u"試作の読み"][u"行"]
    mine = dict(((r[u"doc"], r[u"id"]), r) for r in rec[u"W1W2W3"][u"動いた行"])
    t = {}
    for r in rows:
        k = (r[u"向き"], r[u"型"], reading_category(r[u"読み"]))
        t[k] = t.get(k, 0) + 1
    new_g = [r for r in rows if mine[(r[u"doc"], r[u"id"])][u"向き"] == u"非G→G"]
    frame = [r for r in rows if mine[(r[u"doc"], r[u"id"])][u"P23"][u"state"] == "VALUE_MISMATCH" and mine[(r[u"doc"], r[u"id"])][u"P24"][u"state"] == "UNVERIFIABLE"]
    cnt = lambda rs, c: sum(1 for r in rs if reading_category(r[u"読み"]) == c)
    return {u"表": t, u"行": len(rows), u"新 GROUNDED": len(new_g), u"新 GROUNDED の正": cnt(new_g, u"正"), u"枠": len(frame),
            u"枠 正しい文": cnt(frame, u"正しい文"), u"枠 文が違う": cnt(frame, u"文が違う"), u"枠 分からない": cnt(frame, u"分からない")}


def check_record(rec):
    """記録の集計を、行から数え直した値と突き合わせる。壊した記録で赤くなる。"""
    check_readings(rec)
    rd = jload(ROUNDING)
    # W-1〜W-3
    sec = rec[u"W1W2W3"]
    c = recount_w123(sec)
    s = sec[u"集計"]
    assert c[u"動いた"] == c[u"動いた(書類別の合計)"] == s[u"動いた(全 state)"], u"動いた"
    assert s[u"GROUNDED でない → GROUNDED(新 GROUNDED)"] == c[u"新 GROUNDED"] and s[u"GROUNDED → GROUNDED でない"] == c[u"離れた"]
    assert s[u"GROUNDED → GROUNDED(参照先が動いた)"] == c[u"G→G"] and s[u"VALUE_MISMATCH → UNVERIFIABLE(全部)"] == c[u"VM→UNV"]
    assert s[u"VALUE_MISMATCH → UNVERIFIABLE(other_frame・ambiguous(member))"] == c[u"枠 VM→UNV"]
    assert s[u"うち other_frame"] == c[u"other_frame"] and s[u"うち ambiguous(member)"] == c[u"ambiguous(member)"]
    assert s[u"枠の取り直しが作る GROUNDED"] == c[u"枠の GROUNDED"] and s[u"新 GROUNDED の型"] == c[u"新 GROUNDED の型"]
    assert s[u"新しい VALUE_MISMATCH(P23 が VALUE_MISMATCH でない)"] == c[u"新しい VM"]
    assert s[u"W-6 の対象(GROUNDED か UNVERIFIABLE へ動いた行。UNVERIFIABLE のまま動いた行は含めない)"] == c[u"W-6 の対象"]
    assert s[u"書類数"] == c[u"書類数"] == 67 and sec[u"キャッシュに無い書類"] == [] and sec[u"総 claim"] == c[u"claims"] == s[u"総 claim"]
    for k, v in (u"GROUNDED", c[u"GROUNDED P23"]), (u"VALUE_MISMATCH", c[u"VM P23"]), (u"UNVERIFIABLE", c[u"UNV P23"]), (u"POINTER_NOT_FOUND", c[u"PNF P23"]):
        assert s[u"%s の合計 P23" % k] == v, k
    for k, v in (u"GROUNDED", c[u"GROUNDED P24"]), (u"VALUE_MISMATCH", c[u"VM P24"]), (u"UNVERIFIABLE", c[u"UNV P24"]), (u"POINTER_NOT_FOUND", c[u"PNF P24"]):
        assert s[u"%s の合計 P24" % k] == v, k
    for x in sec[u"動いた行"]:
        d = (x[u"P23"][u"state"] == "GROUNDED", x[u"P24"][u"state"] == "GROUNDED")
        want = {(False, True): u"非G→G", (True, False): u"G→非G", (True, True): u"G→G", (False, False): u"非G→非G"}[d]
        assert x[u"向き"] == want, (x[u"doc"], x[u"id"])
        if x[u"型"] == u"枠の取り直し":     # 枠の取り直しは GROUNDED を作らず、pointer を付けない
            assert x[u"P24"][u"state"] != "GROUNDED" and x[u"P24"][u"pointers"] == [], (x[u"doc"], x[u"id"])
    # 対照: P23 の書類別の state が丸めの記録(書類別の P23)と一致 = 旗が偽の側は動いていない
    rdd = dict((d[u"doc"], d) for d in rd[u"R2"][u"書類"])
    for d in sec[u"書類"]:
        assert rdd[d[u"doc"]][u"states P23"] == d[u"states P23"], d[u"doc"]
        assert rdd[d[u"doc"]][u"claims"] == d[u"claims"], d[u"doc"]
    # W-4
    w4 = rec[u"W4"]
    c4 = recount_w4(w4[u"行"])
    s4 = w4[u"集計"]
    assert c4[u"注入"] == 485 == s4[u"注入"] == sum(p[u"作れた"] for p in w4[u"書類別"]), u"W-4 注入"
    assert s4[u"P24 で通した(GROUNDED のまま)"][u"件"] == c4[u"P24 通した"] and s4[u"P23(対照)で通した"][u"件"] == c4[u"P23 通した"]
    assert s4[u"P24 で止めた(VALUE_MISMATCH)"][u"件"] == c4[u"P24 止めた"] and s4[u"P24 でその他"][u"件"] == c4[u"P24 その他"]
    assert s4[u"P23 と P24 で(結果, state)が違う行"] == c4[u"違う行(結果, state)"] and s4[u"P23 と P24 で(結果, state, reason, pointers)のどれかが違う行"] == c4[u"違う行(全部)"]
    want = dict(((r[u"書類"], r[u"id"]), r[u"P23"]) for r in rd[u"R3"][u"行"])
    assert len(want) == 485
    for r in w4[u"行"]:
        w = want[(r[u"書類"], r[u"id"])]
        assert (w[u"結果"], w[u"state"], w[u"reason"], w[u"pointers"]) == (r[u"P23"][u"結果"], r[u"P23"][u"state"], r[u"P23"][u"reason"], r[u"P23"][u"pointers"]), (r[u"書類"], r[u"id"])
    assert w4[u"対照: P23 の再計算と丸めの記録"][u"違った行"] == 0
    # W-5
    w5 = rec[u"W5"]
    c5 = recount_w5(w5[u"行"])
    s5 = w5[u"集計"]
    assert w5[u"通した P24"][u"件"] == len(c5[u"P24 の通した id"]) and w5[u"通した P24"][u"分母"] == c5[u"P24 の行"] == w5[u"P24 の行数"]
    assert w5[u"止めた P24"][u"件"] == c5[u"P24 の止めた"] and sum(w5[u"その他 P24"].values()) == c5[u"P24 のその他"]
    assert [x[u"id"] for x in w5[u"通した P24 の一覧"]] == c5[u"P24 の通した id"]
    assert w5[u"通した P23(対照)"][u"件"] == len(c5[u"P23 の通した id"]) and w5[u"P23 の行数"] == c5[u"P23 の行"] == 240
    assert s5[u"VALUE_MISMATCH → UNVERIFIABLE に移った(共通の行)"] == c5[u"VM→UNV"] and s5[u"共通の行"] == c5[u"共通"]
    assert s5[u"共通の行で結果が違う行"] == c5[u"結果が違う共通の行"]
    wantr = dict(((x[u"id"], x[u"型"]), x[u"P23"]) for x in rd[u"R1"][u"行"])
    gotr = dict(((r[u"id"], r[u"型"]), r[u"P23"]) for r in w5[u"行"] if r[u"P23"] is not None)
    assert wantr == gotr, u"P23 の欄が丸めの記録の儀式と違う(旗が偽の側が動いている)"
    assert w5[u"対照: P23 の再計算が丸めの記録の R1 と違った行"] == 0
    # W-6
    w6 = rec[u"W6"]
    c6 = recount_w6(w6[u"行"])
    s6 = w6[u"集計"]
    assert s6[u"注入の数"] == c6[u"注入"] and s6[u"作れなかった"] == c6[u"作れなかった"] and s6[u"対象の行(GROUNDED か UNVERIFIABLE へ動いた行)"] == c[u"W-6 の対象"] == c6[u"対象の行"]
    assert (s6[u"P24 で GROUNDED"], s6[u"P24 で UNVERIFIABLE"], s6[u"P24 で VALUE_MISMATCH"], s6[u"P24 でその他"]) == (c6[u"P24 G"], c6[u"P24 UNV"], c6[u"P24 VM"], c6[u"P24 その他"])
    assert (s6[u"P23(対照)で GROUNDED"], s6[u"P23(対照)で UNVERIFIABLE"]) == (c6[u"P23 G"], c6[u"P23 UNV"])
    assert len(s6[u"P24 で GROUNDED の行"]) == c6[u"P24 G"] and len(s6[u"P24 で UNVERIFIABLE の行"]) == c6[u"P24 UNV"]
    # W-7
    w7 = rec[u"W7"]
    c7 = recount_w7(w7[u"書類"])
    s7 = w7[u"集計"]
    assert s7[u"67 の外の書類"] == c7[u"書類"] == 214 == rec[u"書類の数"][u"67 の外"]
    assert (s7[u"claim が 1 以上の書類(P23)"], s7[u"claim が 1 以上の書類(P24)"]) == (c7[u"claim≥1"], c7[u"claim≥1(P24)"])
    assert (s7[u"claim の合計(P23)"], s7[u"claim の合計(P24)"], s7[u"動いた行"], s7[u"新 GROUNDED"], s7[u"VALUE_MISMATCH → UNVERIFIABLE"]) == (
        c7[u"claims P23"], c7[u"claims P24"], c7[u"動いた行"], c7[u"新 G"], c7[u"VM→UNV"])
    assert s7[u"区分"] == c7[u"区分"] and s7[u"種別"] == c7[u"種別"]
    assert s7[u"測れるか(claim が 1 以上の書類が 10 以上)"] == (c7[u"claim≥1"] >= 10)
    # 補助 S2
    s2 = rec[u"S2"]
    cs = recount_s2(s2[u"行"])
    assert cs[u"行"] == 192 == s2[u"集計"][u"行"] and cs[u"注入"] == 64 == s2[u"集計"][u"注入"]
    assert s2[u"集計"][u"Core 自身が P23 → P24 で動いた行"] == len(cs[u"動いた"])
    rd5 = dict(((r[u"doc"], r[u"id"]), r[u"Core 自身 P23"]) for r in rd[u"R5"][u"行"])
    for r in s2[u"行"]:
        assert rd5[(r[u"doc"], r[u"id"])] == r[u"Core 自身 P23"], (r[u"doc"], r[u"id"])        # 対照
    # provenance(other_frame の Recipe 数 = 動いた行の other_frame、全部に context)
    pv = rec[u"provenance"]
    assert pv[u"other_frame の Recipe"] == c[u"other_frame"] == pv[u"provenance に context あり"], u"provenance"
    assert u"pointer あり(0 のはず)" not in pv and u"理由の名に context が混ざった(0 のはず)" not in pv
    # 環境
    env = rec[u"環境"]
    assert env[u"比べた profile"] == ["P23", "P24"] and env[u"費用"] == u"0 USD" and env[u"DEFAULT_PROFILE"] == "P22"
    for k, rel in ((u"vocabulary.py の sha16", "adapters/xbrl/vocabulary.py"), (u"comparators.py の sha16", "adapters/xbrl/comparators.py"),
                   (u"recipes.py の sha16", "adapters/xbrl/recipes.py"), (u"registry_setup.py の sha16", "adapters/xbrl/registry_setup.py")):
        assert env[k] == ENGINE_AT_MEASURE[rel], k


def check_inputs(rec):
    inp = rec[u"入力の sha256"]
    d67 = inp[u"書類 67(経営分析の文を持つ)の sha256"]
    assert len(d67) == 67
    assert digest([u"%s\t%s" % (k, d67[k]) for k in sorted(d67)]) == DOCS67_DIGEST, u"書類 67 の digest が留めた値と違う"
    assert sorted(d[u"doc"] for d in rec[u"W1W2W3"][u"書類"]) == sorted(d67), u"W-1 の書類が入力の 67 と違う"
    assert inp[u"書類 214(67 の外)の sha256 を束ねた値(path 順の 'docID\\tsha256' の行)"] == DOCS214_DIGEST
    assert len(rec[u"W7"][u"書類"]) == 214 and set(d67).isdisjoint({r[u"doc"] for r in rec[u"W7"][u"書類"]})
    assert digest([u"%s\t%s" % (r[u"doc"], r[u"sha256"]) for r in sorted(rec[u"W7"][u"書類"], key=lambda r: r[u"doc"])]) == DOCS214_DIGEST, u"W-7 の書類の digest"
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
    c = dict((t, seal_cells(seal, t)[1]) for t in ("W-1", "W-2", "W-3", "W-4", "W-5", "W-6", "W-7", "W-8", "W-9"))
    n = lambda s: int(s.replace(",", ""))
    m1 = re.search(r"新しく GROUNDED になる行 \*\*(\d+)〜(\d+)\*\*.*枠の取り直しが作る GROUNDED \*\*(\d+)\*\*", c["W-1"])
    m2 = re.search(r"GROUNDED → 非 GROUNDED \*\*(\d+)〜(\d+)\*\*。G → G\(参照先が動いた\)\*\*(\d+)〜(\d+)\*\*", c["W-2"])
    m3 = re.search(r"VALUE_MISMATCH は \*\*([\d,]+)〜([\d,]+)\*\*.*other_frame・ambiguous\(member\)\)\*\*(\d+)〜(\d+)\*\*", c["W-3"])
    m4 = re.search(r"通す \*\*(\d+)\*\*", c["W-4"])
    m5 = re.search(r"通した \*\*(\d+)〜(\d+)\*\*、止めのうち VM → UNVERIFIABLE に移る \*\*(\d+)〜(\d+)\*\*", c["W-5"])
    m6 = re.search(r"P24 が GROUNDED にする \*\*(\d+)\*\* 回、止まらず UNVERIFIABLE \*\*(\d+)〜(\d+)\*\* 回", c["W-6"])
    m7 = re.search(r"新 GROUNDED の (\d+)% 以下.*が \*\*(\d+)% 以下\*\*.*書類が (\d+) 未満", c["W-7"])
    m8 = re.search(r"`recipes.py` \*\*\+(\d+)〜\+(\d+) / −(\d+)\*\*、`vocabulary.py` \*\*≤ (\d+) 行\*\*、`registry_setup.py` \*\*≤ (\d+) 行\*\*", c["W-8"])
    assert m1 and m2 and m3 and m4 and m5 and m6 and m7 and m8, u"封の予測の書き方が変わった"
    return {"w1": (int(m1.group(1)), int(m1.group(2))), "w1_frame": int(m1.group(3)), "w2_lost": (int(m2.group(1)), int(m2.group(2))),
            "w2_g2g": (int(m2.group(3)), int(m2.group(4))), "w3_vm": (n(m3.group(1)), n(m3.group(2))), "w3_frame": (int(m3.group(3)), int(m3.group(4))),
            "w4": int(m4.group(1)), "w5_pass": (int(m5.group(1)), int(m5.group(2))), "w5_vmunv": (int(m5.group(3)), int(m5.group(4))),
            "w6_g": int(m6.group(1)), "w6_unv": (int(m6.group(2)), int(m6.group(3))),
            "w7_false_pct": int(m7.group(1)), "w7_wrong_pct": int(m7.group(2)), "w7_min": int(m7.group(3)),
            "w8_rec": (int(m8.group(1)), int(m8.group(2))), "w8_rec_del": int(m8.group(3)), "w8_voc": int(m8.group(4)), "w8_reg": int(m8.group(5))}


ALLOWED_RED_KINDS = (u"登録の一覧", u"旗の形", u"sha の留め", u"diff の門")


def judgments(rec, seal):
    b = bounds(seal)
    J = {}
    c = recount_w123(rec[u"W1W2W3"])
    J["W-1"] = u"当たり" if (b["w1"][0] <= c[u"新 GROUNDED"] <= b["w1"][1] and c[u"枠の GROUNDED"] == b["w1_frame"]) else u"外れ"
    J["W-2"] = u"当たり" if (b["w2_lost"][0] <= c[u"離れた"] <= b["w2_lost"][1] and b["w2_g2g"][0] <= c[u"G→G"] <= b["w2_g2g"][1]) else u"外れ"
    J["W-3"] = u"当たり" if (b["w3_vm"][0] <= c[u"VM P24"] <= b["w3_vm"][1] and b["w3_frame"][0] <= c[u"枠 VM→UNV"] <= b["w3_frame"][1]) else u"外れ"
    c4 = recount_w4(rec[u"W4"][u"行"])
    J["W-4"] = u"当たり" if (c4[u"P24 通した"] == b["w4"] and c4[u"違う行(結果, state)"] == 0) else u"外れ"
    c5 = recount_w5(rec[u"W5"][u"行"])
    J["W-5"] = u"当たり" if (b["w5_pass"][0] <= len(c5[u"P24 の通した id"]) <= b["w5_pass"][1] and b["w5_vmunv"][0] <= c5[u"VM→UNV"] <= b["w5_vmunv"][1]) else u"外れ"
    c6 = recount_w6(rec[u"W6"][u"行"])
    J["W-6"] = u"当たり" if (c6[u"P24 G"] == b["w6_g"] and b["w6_unv"][0] <= c6[u"P24 UNV"] <= b["w6_unv"][1]) else u"外れ"
    c7 = recount_w7(rec[u"W7"][u"書類"])
    if c7[u"claim≥1"] < b["w7_min"]:
        J["W-7"] = u"測れない"
    else:
        reads = [m[u"読み"] for r in rec[u"W7"][u"書類"] for m in r[u"動いた行"]]
        J["W-7"] = u"読み待ち(人が全部読んで記録の行に書く)" if any(x is None for x in reads) else u"読みの数え直しは門で"
    e8 = rec[u"W8"]
    d = e8[u"engine の差分"]
    rc, v, rs, cm = (d["adapters/xbrl/recipes.py"], d["adapters/xbrl/vocabulary.py"], d["adapters/xbrl/registry_setup.py"], d["adapters/xbrl/comparators.py"])
    kinds = set(x[u"種類"] for x in e8[u"既存試験の赤(直す前)"])
    tests_ok = bool(e8.get(u"既存試験")) and all(t[u"rc"] == 0 for t in e8[u"既存試験"])
    ok8 = (b["w8_rec"][0] <= rc[u"挿入"] <= b["w8_rec"][1] and rc[u"削除"] == b["w8_rec_del"] and v[u"挿入"] <= b["w8_voc"] and rs[u"挿入"] <= b["w8_reg"]
           and cm[u"挿入"] == 0 and cm[u"削除"] == 0 and d[u"core/"][u"差の行数"] == 0 and kinds <= set(ALLOWED_RED_KINDS) and tests_ok)
    J["W-8"] = u"当たり" if ok8 else u"外れ"
    J["W-9"] = u"判定しない(段 2)"
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
    sec = rec[u"W1W2W3"]
    c = recount_w123(sec)
    L = [u"| 項目 | 件数 |", u"|---|---:|",
         u"| 書類 | %d |" % c[u"書類数"], u"| claim の総数 | %s |" % comma(c[u"claims"]), u"| 動いた行(全 state) | %d |" % c[u"動いた"],
         u"| 新 GROUNDED(GROUNDED でない → GROUNDED) | %d |" % c[u"新 GROUNDED"],
         u"| うち 型別 | %s |" % cell(u"・".join(u"%s %d" % (k, v) for k, v in sorted(c[u"新 GROUNDED の型"].items()))),
         u"| 枠の取り直しが作る GROUNDED | %d |" % c[u"枠の GROUNDED"],
         u"| GROUNDED → GROUNDED でない | %d |" % c[u"離れた"], u"| GROUNDED → GROUNDED(参照先だけ動いた) | %d |" % c[u"G→G"],
         u"| VALUE_MISMATCH → UNVERIFIABLE | %d |" % c[u"VM→UNV"],
         u"| うち other_frame | %d |" % c[u"other_frame"], u"| うち ambiguous(member) | %d |" % c[u"ambiguous(member)"],
         u"| 新しい VALUE_MISMATCH(P23 が VALUE_MISMATCH でない) | %d |" % c[u"新しい VM"],
         u"| W-6 の対象(GROUNDED か UNVERIFIABLE へ動いた行) | %d |" % c[u"W-6 の対象"]]
    B["W-1〜W-3 の数"] = u"\n".join(L)
    L = [u"| 無改変 67 書類 | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |", u"|---|---:|---:|---:|---:|",
         u"| P23(対照) | %s | %s | %s | %s |" % (comma(c[u"GROUNDED P23"]), comma(c[u"VM P23"]), comma(c[u"UNV P23"]), comma(c[u"PNF P23"])),
         u"| **P24** | **%s** | **%s** | **%s** | **%s** |" % (comma(c[u"GROUNDED P24"]), comma(c[u"VM P24"]), comma(c[u"UNV P24"]), comma(c[u"PNF P24"]))]
    B["W-3 の表"] = u"\n".join(L)
    L = [u"| 向き(P23 の state → P24 の state) | 行 |", u"|---|---:|"]
    for k, v in sorted(sec[u"集計"][u"向き(全部)"].items()):
        L.append(u"| %s | %d |" % (cell(k), v))
    B["遷移表"] = u"\n".join(L)
    L = [u"| 新 GROUNDED の前の state | 行 |", u"|---|---:|"]
    for k, v in sorted(sec[u"集計"][u"新 GROUNDED の前の state"].items()):
        L.append(u"| %s | %d |" % (cell(k), v))
    B["新 GROUNDED の前の表"] = u"\n".join(L)
    L = [u"| 型 | 行 |", u"|---|---:|"]
    types = {}
    for r in sec[u"動いた行"]:
        key = (r[u"型"], r[u"向き"])
        types[key] = types.get(key, 0) + 1
    for (t, d), v in sorted(types.items()):
        L.append(u"| %s・%s | %d |" % (cell(t), cell(d), v))
    B["動いた行の型別"] = u"\n".join(L)
    rr = recount_readings(rec)
    L = [u"| 向き・型 | 試作の読みの分類 | 行 |", u"|---|---|---:|"]
    for (d, t, c), v in sorted(rr[u"表"].items()):
        L.append(u"| %s・%s | %s | %d |" % (cell(d), cell(t), cell(c), v))
    B["試作の読みの表"] = u"\n".join(L)
    c4 = recount_w4(rec[u"W4"][u"行"])
    L = [u"| 穴 B の注入 485 件 | 通した | 止めた | その他 |", u"|---|---:|---:|---:|",
         u"| P23(対照) | %d | %d | %d |" % (c4[u"P23 通した"], 485 - c4[u"P23 通した"] - sum(1 for r in rec[u"W4"][u"行"] if r[u"P23"][u"結果"] == u"その他"),
                                       sum(1 for r in rec[u"W4"][u"行"] if r[u"P23"][u"結果"] == u"その他")),
         u"| **P24** | **%d** | **%d** | **%d** |" % (c4[u"P24 通した"], c4[u"P24 止めた"], c4[u"P24 その他"]),
         u"| P23 と P24 で(結果, state)が違う行 | | | %d |" % c4[u"違う行(結果, state)"]]
    B["W-4 の表"] = u"\n".join(L)
    w5 = rec[u"W5"]
    c5 = recount_w5(w5[u"行"])
    L = [u"| 儀式 | 注入の行 | 通した | 止めた | その他 |", u"|---|---:|---:|---:|---:|",
         u"| P23(対照) | %d | %d | %d | %d |" % (c5[u"P23 の行"], len(c5[u"P23 の通した id"]), sum(1 for r in w5[u"行"] if r[u"P23"] == STOPPED),
                                              sum(1 for r in w5[u"行"] if r[u"P23"] not in (None, PASSED, STOPPED))),
         u"| **P24** | **%d** | **%d** | **%d** | **%d** |" % (c5[u"P24 の行"], len(c5[u"P24 の通した id"]), c5[u"P24 の止めた"], c5[u"P24 のその他"]),
         u"| 素の書類 GROUNDED(P23 → P24) | %d → %d | | | |" % (w5[u"素の書類 P23"][u"state の分布"].get("GROUNDED", 0), w5[u"素の書類 P24"][u"state の分布"].get("GROUNDED", 0))]
    B["W-5 の表"] = u"\n".join(L)
    L = [u"| id | 分類 | 値の差 | 1 最小単位 | 文脈 |", u"|---|---|---|---|---|"]
    for x in w5[u"通した P24 の一覧"]:
        L.append(u"| %s | %s | %s | %s | %s |" % (x[u"id"], cell(x[u"分類"]), x[u"値の差"], x[u"1 最小単位"], cell(x[u"文脈"])))
    B["W-5 の通した"] = u"\n".join(L)
    s6 = rec[u"W6"][u"集計"]
    L = [u"| 変え方・結果 | P24 | P23(対照) |", u"|---|---:|---:|"]
    for k in sorted(set(s6[u"集計 P24"]) | set(s6[u"集計 P23"])):
        L.append(u"| %s | %d | %d |" % (cell(k), s6[u"集計 P24"].get(k, 0), s6[u"集計 P23"].get(k, 0)))
    B["W-6 の表"] = u"\n".join(L)
    L = [u"| doc | id | 変え方 | 元の字 → 後の字 | reason |", u"|---|---|---|---|---|"]
    for x in s6[u"P24 で UNVERIFIABLE の行"]:
        L.append(u"| %s | %s | %s | %s → %s | %s |" % (x[u"doc"], x[u"id"], cell(x[u"変え方"]), cell(x[u"元の字"]), cell(x[u"後の字"]), cell(x[u"reason"])))
    B["W-6 の UNVERIFIABLE"] = u"\n".join(L)
    s7 = rec[u"W7"][u"集計"]
    L = [u"| 67 の外の書類(手元の cache) | 件数 |", u"|---|---:|", u"| 書類 | %d |" % s7[u"67 の外の書類"],
         u"| 区分 | %s |" % cell(u"・".join(u"%s %d" % (k, v) for k, v in sorted(s7[u"区分"].items()))),
         u"| 種別 | %s |" % cell(u"・".join(u"%s %d" % (k, v) for k, v in sorted(s7[u"種別"].items()))),
         u"| claim が 1 以上の書類(P23) | %d |" % s7[u"claim が 1 以上の書類(P23)"], u"| claim が 1 以上の書類(P24) | %d |" % s7[u"claim が 1 以上の書類(P24)"],
         u"| claim の合計(P23 / P24) | %d / %d |" % (s7[u"claim の合計(P23)"], s7[u"claim の合計(P24)"]),
         u"| 動いた行 | %d |" % s7[u"動いた行"]]
    B["W-7 の表"] = u"\n".join(L)
    s2 = recount_s2(rec[u"S2"][u"行"])
    L = [u"| 段 2 の材料 192 行の Core 自身 | 件数 |", u"|---|---:|", u"| 行 | %d |" % s2[u"行"], u"| 注入 | %d |" % s2[u"注入"],
         u"| P23 → P24 で動いた行 | %d |" % len(s2[u"動いた"]), u"| 注入で Core 自身 P23 が GROUNDED | %d |" % s2[u"P23 G(注入)"],
         u"| 注入で Core 自身 P24 が GROUNDED | %d |" % s2[u"P24 G(注入)"]]
    B["補助 S2 の表"] = u"\n".join(L)
    pv = rec[u"provenance"]
    L = [u"| 理由 other_frame の Recipe | 件数 |", u"|---|---:|"] + [u"| %s | %d |" % (cell(k), v) for k, v in sorted(pv.items())]
    B["provenance の表"] = u"\n".join(L)
    e8 = rec[u"W8"]
    d = e8[u"engine の差分"]
    L = [u"| file | 挿入 | 削除 |", u"|---|---:|---:|"]
    for f in ("adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py"):
        L.append(u"| `%s` | %d | %d |" % (f, d[f][u"挿入"], d[f][u"削除"]))
    L.append(u"| `core/` | %d | |" % d[u"core/"][u"差の行数"])
    B["W-8 の表"] = u"\n".join(L)
    L = [u"| 試験 | 種類 | 直し |", u"|---|---|---|"] + [u"| %s | %s | %s |" % (cell(x[u"試験"]), cell(x[u"種類"]), cell(x[u"直し"])) for x in e8[u"既存試験の赤(直す前)"]]
    B["W-8 の赤の表"] = u"\n".join(L)
    return B


def prose_facts(rec):
    P = {}
    pr = rec[u"予測の判定"]
    hit = sum(1 for v in pr.values() if v[u"判定"] == u"当たり")
    miss = sum(1 for v in pr.values() if v[u"判定"] == u"外れ")
    unm = sum(1 for v in pr.values() if v[u"判定"] == u"測れない")
    P["pred"] = u"**予測 機械判定 当たり %d / 外れ %d / 測れない %d**(W-1〜W-8。W-9 は段 2 なので判定しない)。" % (hit, miss, unm)
    d = rec[u"W8"][u"engine の差分"]
    v, c, r, g = d["adapters/xbrl/vocabulary.py"], d["adapters/xbrl/comparators.py"], d["adapters/xbrl/recipes.py"], d["adapters/xbrl/registry_setup.py"]
    P["head"] = (u"engine の直し: `adapters/xbrl/vocabulary.py` 挿入 %d・削除 %d、`adapters/xbrl/recipes.py` 挿入 %d・削除 %d、`adapters/xbrl/registry_setup.py` 挿入 %d・削除 %d、"
                 u"`adapters/xbrl/comparators.py` 挿入 %d・削除 %d、`core/` %d 行。") % (
        v[u"挿入"], v[u"削除"], r[u"挿入"], r[u"削除"], g[u"挿入"], g[u"削除"], c[u"挿入"], c[u"削除"], d[u"core/"][u"差の行数"])
    cc = recount_w123(rec[u"W1W2W3"])
    P["w1"] = u"67 書類(claim %s)の無改変で、P23 から P24 に動いた行は %d。新 GROUNDED %d(%s)。枠の取り直しが作る GROUNDED %d。GROUNDED から離れた行 %d、GROUNDED のまま参照先が動いた行 %d。" % (
        comma(cc[u"claims"]), cc[u"動いた"], cc[u"新 GROUNDED"], u"・".join(u"%s %d" % (k, v_) for k, v_ in sorted(cc[u"新 GROUNDED の型"].items())),
        cc[u"枠の GROUNDED"], cc[u"離れた"], cc[u"G→G"])
    P["w3"] = u"VALUE_MISMATCH は P23 が %s、P24 が %s(差 %d)。VALUE_MISMATCH から UNVERIFIABLE に移った行は %d(other_frame %d・ambiguous(member) %d)。GROUNDED は %s から %s。" % (
        comma(cc[u"VM P23"]), comma(cc[u"VM P24"]), cc[u"VM P24"] - cc[u"VM P23"], cc[u"枠 VM→UNV"], cc[u"other_frame"], cc[u"ambiguous(member)"],
        comma(cc[u"GROUNDED P23"]), comma(cc[u"GROUNDED P24"]))
    rr = recount_readings(rec)
    P["readings"] = (u"試作 v3.1 の人の読み(司令塔の席の読み。実装席の読みではない)を同じ行に写した: 動いた行 %d の全部が試作の行と(doc, id)・state・reason・pointers まで一致。"
                     u"新 GROUNDED %d 行のうち読みが正 %d。枠の VALUE_MISMATCH から UNVERIFIABLE に移った %d 行は、正しい文 %d・文が違う %d・分からない %d。") % (
        rr[u"行"], rr[u"新 GROUNDED"], rr[u"新 GROUNDED の正"], rr[u"枠"], rr[u"枠 正しい文"], rr[u"枠 文が違う"], rr[u"枠 分からない"])
    c4 = recount_w4(rec[u"W4"][u"行"])
    P["w4"] = u"穴 B の注入 %d 件を P24 で再検証すると、通した %s・止めた %s・その他 %s(P23 は通した %s)。P23 と P24 で(結果, state)が違った行は %d。" % (
        c4[u"注入"], F(c4[u"P24 通した"], c4[u"注入"]), F(c4[u"P24 止めた"], c4[u"注入"]), F(c4[u"P24 その他"], c4[u"注入"]), F(c4[u"P23 通した"], c4[u"注入"]), c4[u"違う行(結果, state)"])
    w5 = rec[u"W5"]
    c5 = recount_w5(w5[u"行"])
    P["w5"] = u"儀式を P24 で回すと、通した %s・止めた %s(P23 は通した %s)。通した id: %s。止めのうち VALUE_MISMATCH から UNVERIFIABLE に移った行は %d。" % (
        F(len(c5[u"P24 の通した id"]), c5[u"P24 の行"]), F(c5[u"P24 の止めた"], c5[u"P24 の行"]), F(len(c5[u"P23 の通した id"]), c5[u"P23 の行"]),
        u"・".join(c5[u"P24 の通した id"]), c5[u"VM→UNV"])
    c6 = recount_w6(rec[u"W6"][u"行"])
    P["w6"] = u"動いた %d 行に注入 %d 回(作れなかった %d)。P24 が GROUNDED にした %d 回・UNVERIFIABLE %d 回・VALUE_MISMATCH %d 回・その他 %d 回。対照の P23 は同じ注入で GROUNDED %d 回。" % (
        c6[u"対象の行"], c6[u"注入"], c6[u"作れなかった"], c6[u"P24 G"], c6[u"P24 UNV"], c6[u"P24 VM"], c6[u"P24 その他"], c6[u"P23 G"])
    c7 = recount_w7(rec[u"W7"][u"書類"])
    P["w7"] = u"手元の cache の 67 の外 %d 書類に 67 と同じ抽出をかけて、claim が 1 以上の書類は %d(claim の合計 %d)。" % (c7[u"書類"], c7[u"claim≥1"], c7[u"claims P23"])
    s2 = recount_s2(rec[u"S2"][u"行"])
    P["s2"] = u"補助: 段 2 の材料 %d 行(注入 %d)の Core 自身は、P23 から P24 で動いた行が %d。" % (s2[u"行"], s2[u"注入"], len(s2[u"動いた"]))
    e8 = rec[u"W8"]
    P["w8"] = u"既存試験の赤(直す前): %d 本。直した後の既存試験: %s。" % (len(e8[u"既存試験の赤(直す前)"]), u"・".join(u"%s → %s" % (t[u"コマンド"], t[u"最後の行"]) for t in e8.get(u"既存試験", [])))
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
    pieces = list(render_blocks(rec).values()) + list(prose_facts(rec).values()) + [mutation_table(rec), rec[u"変異(engine。手で走らせた)"][u"注記"], rec[u"試作の読み"][u"注記"]]
    for v in sorted(pieces, key=len, reverse=True):
        t = t.replace(v, u"")
    t = re.sub(r"```.*?```", u"", t, flags=re.S)
    t = re.sub(r"`[^`]*`", u"", t)
    t = re.sub(r"[A-Za-z_][A-Za-z_0-9\-]*\d[A-Za-z_0-9\-]*", u"", t)      # S100YMFV・N076・W-1・P24・sha16 など
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
    assert rec[u"試作の読み"][u"注記"] in doc
    assert u"判定しない(段 2)" in doc
    for lit in (u"測れない", u"comparators.py は零行", u"試作 ", u"P25"):
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
        c = recount_w123(r[u"W1W2W3"])
        self.assertEqual((c[u"動いた"], c[u"新 GROUNDED"], c[u"枠の GROUNDED"], c[u"離れた"], c[u"G→G"]), (369, 148, 0, 0, 4))
        self.assertEqual((c[u"VM P23"], c[u"VM P24"], c[u"枠 VM→UNV"], c[u"other_frame"], c[u"ambiguous(member)"], c[u"W-6 の対象"]), (1418, 1203, 209, 198, 11, 361))
        c4 = recount_w4(r[u"W4"][u"行"])
        self.assertEqual((c4[u"P24 通した"], c4[u"P23 通した"], c4[u"違う行(結果, state)"]), (0, 0, 0))
        c5 = recount_w5(r[u"W5"][u"行"])
        self.assertEqual((len(c5[u"P24 の通した id"]), c5[u"P24 の行"], c5[u"P23 の行"], c5[u"VM→UNV"]), (2, 247, 240, 0))
        c6 = recount_w6(r[u"W6"][u"行"])
        self.assertEqual((c6[u"P24 G"], c6[u"P23 G"], c6[u"注入"]), (0, 2, 695))
        c7 = recount_w7(r[u"W7"][u"書類"])
        self.assertEqual((c7[u"書類"], c7[u"claim≥1"], c7[u"claims P23"]), (214, 0, 0))
        self.assertEqual(recount_s2(r[u"S2"][u"行"])[u"動いた"], [])
        self.assertEqual(r[u"予測の判定"]["W-7"][u"判定"], u"測れない")
        self.assertEqual(r[u"予測の判定"]["W-9"][u"判定"], u"判定しない(段 2)")

    def test_6_engine_is_the_one_measured_or_a_declared_transition(self):
        engine_ok()
        self.assertTrue(self.rec[u"環境"][u"HEAD"].startswith(SEAL_COMMIT))

    def test_7_numstat_in_the_record_is_the_engine_diff_from_the_seal_commit(self):
        """engine が測った時点の sha のままのときだけ: 封の commit からの差分の行数が記録と一致(動いたら宣言された遷移の後なので比べない)。"""
        for rel, want in ENGINE_AT_MEASURE.items():
            if sha16(rel) != want:
                self.skipTest(u"engine が宣言された遷移の後")
        d = self.rec[u"W8"][u"engine の差分"]
        for f in ("adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py"):
            o = git("diff", "--numstat", SEAL_COMMIT, "--", f).stdout.split()
            ins, dele = (int(o[0]), int(o[1])) if len(o) >= 2 else (0, 0)
            self.assertEqual((ins, dele), (d[f][u"挿入"], d[f][u"削除"]), f)

    def test_8_core_is_untouched_and_default_is_p22_in_step_1(self):
        out = git("diff", "--numstat", SEAL_COMMIT, "--", "core")
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout.strip(), u"", u"core/ が封の commit から動いている")
        src = jtext(VOCAB)
        self.assertEqual(re.findall(r'(?m)^DEFAULT_PROFILE = "(P\d+)"$', src), ["P27"], u"段 1 の commit 時点は既定が P22 だった。2026-10-23 の P26 の段 2(封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)で P26、2026-10-28 の P27 の段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で P27")
        from adapters.xbrl import vocabulary as V
        self.assertEqual(V.DEFAULT_PROFILE, "P27")      # 2026-10-28: P26 の段 2 の後は P26 だった。P27 の段 2 で P27
        self.assertTrue(V.PROFILES["P24"].vocab_2026_10_21 and V.PROFILES["P24"].frame_rebind)
        self.assertFalse(V.PROFILES["P23"].vocab_2026_10_21 or V.PROFILES["P23"].frame_rebind)

    def test_9_w9_is_not_judged_and_the_seal_was_not_edited(self):
        self.assertEqual(self.rec[u"予測の判定"]["W-9"][u"判定"], u"判定しない(段 2)")
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
        out = [r for r in self.rec[u"W7"][u"書類"]]
        if not have_cache([r[u"doc"] for r in out]):
            self.skipTest(u"67 の外の書類の cache が無い")
        for r in out:
            self.assertEqual(sha_path(os.path.join(CACHE, r[u"doc"] + ".zip")), r[u"sha256"], r[u"doc"])
        for rel in INPUT_SHAS:
            self.assertEqual(sha_path(os.path.join(ROOT, rel)), inp[rel], rel)
        self.assertEqual(sha_path(os.path.join(ROOT, "fixtures/xbrl/ai_prose_instance_2026-10-09.zip")), inp[u"儀式の同梱書類"])

    def test_11_existing_red_list_is_the_closed_kinds_and_every_fix_is_named(self):
        """直す前に赤だった既存試験の一覧: 種類は封の字の中だけ(数 / state の門・人間の決定の字の門は 0)。どの行にも直しが書いてある。"""
        red = self.rec[u"W8"][u"既存試験の赤(直す前)"]
        self.assertTrue(red)
        for x in red:
            self.assertIn(x[u"種類"], ALLOWED_RED_KINDS, x)
            self.assertTrue(x[u"直し"].strip(), x)
        self.assertEqual(len({x[u"試験"] for x in red}), len(red), u"同じ試験が 2 回載っている")


def run_script(args):
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=ROOT, capture_output=True, text=True)


def _script():
    import importlib.util
    spec = importlib.util.spec_from_file_location("vocab_script_for_gate", SCRIPT)
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

    def test_light_w1_matches_the_record(self):
        self._need(LIGHT_W1_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "w1.json")
            p = run_script(["--stage", "w1", "--docs", ",".join(LIGHT_W1_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)[u"W1W2W3"]
        want = [x for x in self.rec[u"W1W2W3"][u"動いた行"] if x[u"doc"] in LIGHT_W1_DOCS]
        self.assertTrue(want)
        self.assertEqual(got[u"動いた行"], want)
        self.assertEqual(got[u"書類"], [d for d in self.rec[u"W1W2W3"][u"書類"] if d[u"doc"] in LIGHT_W1_DOCS])

    def test_light_w4_matches_the_record(self):
        self._need(LIGHT_W4_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "w4.json")
            p = run_script(["--stage", "w4", "--docs", ",".join(LIGHT_W4_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)[u"W4"][u"行"]
        want = [r for r in self.rec[u"W4"][u"行"] if r[u"書類"] in LIGHT_W4_DOCS]
        self.assertTrue(want)
        self.assertEqual(got, want)

    def test_light_w7_matches_the_record(self):
        self._need(LIGHT_W7_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "w7.json")
            p = run_script(["--stage", "w7", "--docs", ",".join(LIGHT_W7_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)[u"W7"][u"書類"]
        want = [r for r in self.rec[u"W7"][u"書類"] if r[u"doc"] in LIGHT_W7_DOCS]
        self.assertEqual(len(want), len(LIGHT_W7_DOCS))
        self.assertEqual(got, want)

    @unittest.skipUnless(RUN_HEAVY, u"AUDIT_CORE_VOCAB=1 のときだけ走る(全部の走らせ直し。約 三十分)")
    def test_heavy_everything_matches_the_record(self):
        if not (have_cache(sorted(self.rec[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"])) and labels_ok()):
            self.fail(u"AUDIT_CORE_VOCAB=1 なのに cache かラベルが揃っていない")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "all.json")
            p = run_script(["--stage", "all", "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)
        for sec in (u"W1W2W3", u"W4", u"W6", u"W7", u"S2", u"provenance"):
            self.assertEqual(got[sec], self.rec[sec], sec)
        a = dict((k, v) for k, v in got[u"W5"].items() if k != u"所要秒")
        b = dict((k, v) for k, v in self.rec[u"W5"].items() if k != u"所要秒")
        self.assertEqual(a, b, u"W5")
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

    def test_m1_drop_one_moved_row(self):
        r = self._mut()
        r[u"W1W2W3"][u"動いた行"].pop()
        self._red(check_record, r)

    def test_m2_a_frame_rebind_row_that_becomes_grounded_is_seen(self):
        """枠の取り直しの行が GROUNDED になったことにすると、型の約束(GROUNDED を作らない・pointer なし)・集計・判定のどれかで赤。"""
        r = self._mut()
        for x in r[u"W1W2W3"][u"動いた行"]:
            if x[u"型"] == u"枠の取り直し":
                x[u"P24"][u"state"] = "GROUNDED"
                x[u"向き"] = u"非G→G"
                break
        self._red(check_record, r)
        self.assertEqual(recount_w123(r[u"W1W2W3"])[u"枠の GROUNDED"], 1)

    def test_m2b_a_false_reading_of_a_new_grounded_row_is_red(self):
        """新 GROUNDED の行の読みを『偽』にすると赤。読みが別の行のものになっても(state が違えば)赤。"""
        r = self._mut()
        for x in r[u"試作の読み"][u"行"]:
            if x[u"向き"] == u"非G→G":
                x[u"読み"] = u"偽: 別の fact に結んだ"
                break
        self._red(check_record, r)
        r = self._mut()
        r[u"試作の読み"][u"行"][0][u"試験 state(後)"] = "VALUE_MISMATCH" if r[u"試作の読み"][u"行"][0][u"試験 state(後)"] != "VALUE_MISMATCH" else "GROUNDED"
        self._red(check_record, r)
        r = self._mut()
        r[u"試作の読み"][u"行"].pop()
        self._red(check_record, r)

    def test_m3_change_the_value_mismatch_count_of_one_document(self):
        r = self._mut()
        for d in r[u"W1W2W3"][u"書類"]:
            if d[u"states P24"].get("VALUE_MISMATCH"):
                d[u"states P24"]["VALUE_MISMATCH"] += 7
                break
        self._red(check_record, r)

    def test_m4_change_a_judgment_word(self):
        r = self._mut()
        r[u"予測の判定"]["W-1"][u"判定"] = u"外れ"
        self._red(check_judgments, r, self.seal)

    def test_m5_a_lost_grounded_row_makes_w2_a_miss(self):
        r = self._mut()
        for x in r[u"W1W2W3"][u"動いた行"]:
            if x[u"向き"] == u"G→G":
                x[u"P24"][u"state"] = "VALUE_MISMATCH"
                x[u"向き"] = u"G→非G"
        s = r[u"W1W2W3"][u"集計"]
        s[u"GROUNDED → GROUNDED でない"] = s[u"GROUNDED → GROUNDED(参照先が動いた)"]
        s[u"GROUNDED → GROUNDED(参照先が動いた)"] = 0
        self.assertEqual(judgments(r, self.seal)["W-2"], u"外れ")

    def test_m6_a_p24_pass_in_the_hole_b_is_seen(self):
        r = self._mut()
        x = r[u"W4"][u"行"][0]
        x[u"P24"] = dict(x[u"P24"], **{u"結果": u"通した(参照先が前期へ移った)"})
        self._red(check_record, r)

    def test_m7_a_changed_hole_b_row_in_the_p23_column_is_seen(self):
        """旗が偽の側(P23 の欄)を 1 行動かすと、丸めの記録との突き合わせで赤。"""
        r = self._mut()
        r[u"W4"][u"行"][7][u"P23"] = dict(r[u"W4"][u"行"][7][u"P23"], **{u"state": u"GROUNDED"})
        self._red(check_record, r)
        r = self._mut()
        r[u"W5"][u"行"][5][u"P23"] = PASSED if r[u"W5"][u"行"][5][u"P23"] != PASSED else STOPPED
        self._red(check_record, r)

    def test_m8_a_p24_pass_in_the_ritual_moves_the_judgment(self):
        r = self._mut()
        rows = r[u"W5"][u"行"]
        n = 0
        for x in rows:
            if x[u"P24"] == STOPPED and n < 3:
                x[u"P24"] = PASSED
                n += 1
        self.assertEqual(judgments(r, self.seal)["W-5"], u"外れ")

    def test_m9_a_grounded_injection_in_w6_is_a_miss(self):
        r = self._mut()
        for x in r[u"W6"][u"行"]:
            if x.get(u"変え方"):
                x[u"P24"] = {u"state": "GROUNDED", u"reason": None, u"pointers": [], u"recomputed": None}
                break
        self.assertEqual(judgments(r, self.seal)["W-6"], u"外れ")
        self._red(check_record, r)

    def test_m10_a_measurable_new_sample_is_not_called_unmeasurable(self):
        """67 の外に claim が 1 以上の書類を 10 本作ると、判定は『測れない』でなくなる(読み待ち)。"""
        r = self._mut()
        for x in r[u"W7"][u"書類"][:10]:
            x[u"claims P23"] = 3
            x[u"claims P24"] = 3
        self.assertNotEqual(judgments(r, self.seal)["W-7"], u"測れない")
        self._red(check_record, r)         # 集計の数え直しとも合わなくなる

    def test_m11_a_number_in_a_document_table_is_red(self):
        for blk in ("W-1〜W-3 の数", "W-3 の表", "W-4 の表", "W-5 の表"):
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
        r = self._mut()
        r[u"W7"][u"書類"][5][u"sha256"] = u"0" * 64
        self._red(check_inputs, r)

    def test_m15_mutation_record_must_have_five_rows(self):
        r = self._mut()
        r[u"変異(engine。手で走らせた)"][u"表"] = r[u"変異(engine。手で走らせた)"][u"表"][:4]
        self._red(check_mutation_record, r)

    def test_m16_a_wrong_engine_sha_is_red(self):
        global ENGINE_AT_MEASURE, ENGINE_LATER
        old, old_later = dict(ENGINE_AT_MEASURE), dict(ENGINE_LATER)
        try:
            # 2026-10-21(pin の遷移): 宣言された遷移が在ると「測った時点と違う sha」は受け入れられてしまうので、この変異では遷移の宣言を外して(空にして)確かめる
            ENGINE_LATER = {}
            ENGINE_AT_MEASURE = dict(old, **{"adapters/xbrl/recipes.py": "0" * 16})
            self._red(engine_ok)
            ENGINE_AT_MEASURE = dict(old, **{"adapters/xbrl/registry_setup.py": "0" * 16})
            self._red(engine_ok)
        finally:
            ENGINE_AT_MEASURE, ENGINE_LATER = old, old_later
        engine_ok()

    def test_m17_an_existing_red_of_a_forbidden_kind_makes_w8_a_miss(self):
        r = self._mut()
        r[u"W8"][u"既存試験の赤(直す前)"].append({u"試験": u"tests/measure/x.py::T::t", u"種類": u"数 / state の門", u"直し": u"x"})
        self.assertEqual(judgments(r, self.seal)["W-8"], u"外れ")

    def test_m18_flags_made_identity_turn_w1_red(self):
        """旗を恒等(偽)にすると、W-1〜W-3 の再計算が記録の動いた行と食い違う(新 GROUNDED が消える)。
        engine の file は書き換えない(in-process で P24 の旗を偽にして、出るとき必ず戻す)。"""
        if not (have_cache(LIGHT_W1_DOCS) and labels_ok()):
            self.skipTest(u"cache かラベルが無い")
        import dataclasses
        m = _script()
        from adapters.xbrl import vocabulary as V
        want = [x for x in self.rec[u"W1W2W3"][u"動いた行"] if x[u"doc"] in LIGHT_W1_DOCS]
        self.assertTrue(want)
        texts = {}
        for d in LIGHT_W1_DOCS:
            with io.open(os.path.join(CACHE, d + ".zip"), "rb") as fh:
                texts[d] = (fh.read(), None)
        old = V.PROFILES["P24"]
        V.PROFILES["P24"] = dataclasses.replace(old, vocab_2026_10_21=False, frame_rebind=False)
        try:
            with m._RawTap() as tap:
                got = m.plain(tap, list(LIGHT_W1_DOCS), texts)
        finally:
            V.PROFILES["P24"] = old
        self.assertIs(V.PROFILES["P24"], old)
        self.assertEqual(got[u"動いた行"], [])


if __name__ == "__main__":
    unittest.main()
