# -*- coding: utf-8 -*-
u"""最後の枝の名指しは証拠があるときだけ「違う」と言う P25 の段 1 の結果 ― 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md §2(L-1〜L-9)の結果を縛る門。

記録: ``fixtures/xbrl/lastbranch_2026-10-21.json``(``measure/xbrl_lastbranch_2026-10-21.py --stage all --readings … --mutations … --run-tests`` の出力)。
文書: ``docs/XBRL_LASTBRANCH_RESULT_2026-10-21.md``。

この門がやること(どれも、壊した標本で赤くなることを ``MutationTest`` が毎回確かめる):
  1. 入力(書類 67 本・67 の外 214 本の sha256・他の記録の sha256)を**字で留めた digest / sha256** に縛る。cache が在る機械では実物の sha256 も記録と一致させる。
  2. 記録の行(L-1 の動いた行と書類別・L-2 の残る行・L-3 の未読の行・L-4 の注入 485・L-5 の儀式・L-6 の 192 行・L-7 の注入・provenance)から、集計・向きを
     **script の関数を使わずに** 数え直し、記録の集計と一致させる。対照(P24 の再計算が、P24 の記録 ``vocab_2026-10-21.json`` の同じ行と一致すること
     = 旗が偽の側は 1 行も変わらない)も、門が自分で記録同士を突き合わせる。
  3. **読みと行の 1 対 1**: L-3 の未読の行 = 動いた行 − 試作で読んだ集合((doc, id) 241 を digest で留めた)、L-2 の残る行。どの行にも読みの語(正しい文 /
     文が本当に違う / 分からない)と根拠が付いていること。**読みの中身の正しさは門で縛れない**(人(エージェント)の読み。縛るのは行と読みの対応と、数と、判定の算術だけ)。
  4. 予測 L-1〜L-9 の判定を、封の字から読んだ幅と記録の行から**門が自分で**求め、記録の判定と文書の表と一致させる。
  5. 文書の表・数のある文を記録から作った字と完全一致させる。それ以外の散文に算用数字が在れば ``residual_numbers`` が見つけて赤にする(コード片・識別子・日付・節の番号は除く)。散文は漢数字で書く。
  6. engine の sha(測った時点の vocabulary.py・comparators.py・recipes.py・registry_setup.py)を字で留め、いまの engine が同じか宣言された遷移であること。
     ``core/`` が封の commit から 0 行であること。``DEFAULT_PROFILE`` が P22 のままであること(段 1)。封が封の commit から 1 字も変わっていないこと。
  7. cache とラベルが在る機械では、軽い走らせ直し(L-1〜L-3 を 2 書類、L-4 を 1 書類、L-6 の 192 行)を script で走らせて記録の該当行と一致。
     全部の走らせ直し(約 十五分)は ``AUDIT_CORE_LASTBRANCH=1`` のときだけ。
縛っていないもの: 読みの中身の正しさ(上の 3.)、限界の文の主張の中身、変異(engine)の手の実測そのもの(表は記録の写しを縛るだけ)、
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
REC = os.path.join(ROOT, "fixtures", "xbrl", "lastbranch_2026-10-21.json")
DOC = os.path.join(ROOT, "docs", "XBRL_LASTBRANCH_RESULT_2026-10-21.md")
SEAL_REL = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SEAL_COMMIT = "80ca08d"
SCRIPT = os.path.join(ROOT, "measure", "xbrl_lastbranch_2026-10-21.py")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
RUN_HEAVY = os.environ.get("AUDIT_CORE_LASTBRANCH") == "1"
VOCAB_REC = os.path.join(ROOT, "fixtures", "xbrl", "vocab_2026-10-21.json")
VOCAB = os.path.join(ROOT, "adapters", "xbrl", "vocabulary.py")
LIGHT_L1_DOCS = ("S100YYK8", "S100YZ7E")       # 動いた行・残る行・「文が本当に違う」の行(S100YZ7E N071)が在る書類
LIGHT_L4_DOCS = ("S100YYQX",)                   # 穴 B の注入のうち要確認に移る行(N008)が在る書類
READ_OK, READ_WRONG, READ_UNSURE = u"正しい文", u"文が本当に違う", u"分からない"
READ_WORDS = (READ_OK, READ_WRONG, READ_UNSURE)
NSV = "no_same_value"

#: **字で留める**(記録の値の写し。定数から作らない)。
DOCS67_DIGEST = "118ec1015494db404b74dbd65b72bddfd2356459749d6f10dc910e5a1348429f"       # 書類 67 本の docID\tsha256 を sorted で \n 結合した sha256(P24 の門と同じ集合)
DOCS214_DIGEST = "1b36b8f77e878429976f46b2fcf377bbe76ecb42343fcfd4a22a826e015b23af"      # 67 の外 214 本の同じ形の sha256
PROTO_DIGEST = "1dd7d00f5b5c3cabd5c3084ca2852d4acc4fdbc5e0e11957c41673c6b18e82d2"       # 試作で読んだ集合 241 の 'doc id' の行(sorted)を \n で結んだ sha256
PROTO_N, PROTO_MOVED = 241, 240                                                          # 228 + 13。段 1 で動いた行に当たるのは 240
INPUT_SHAS = {
    "fixtures/xbrl/vocab_2026-10-21.json": "84480c3703cc7beabcb9461c6f9d234c7e7db65b092b9a140c71bb8bd8aba377",
    "fixtures/xbrl/rounding_2026-10-21.json": "c39641935e08350acf4b6032fff14cb35f317f8e551411591933d84e0b468d94",
    "fixtures/xbrl/period_bind_2026-10-20.json": "dfcf8d94dadf51ef0d525b74edf72dff8a009dce7352c453c8bf6e5db2db9b60",
    "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json": "c3068024ff8c2812fabbf54e36f50b1cedeccb7955e9455603d1a17018418149",
    "fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json": "3b13d26f81906ae47696c95c2c0e21322579bcdabcde3a133b5a96970e7c52f6",
}
RITUAL_ZIP_SHA = "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799"
#: 測った時点の engine(sha256 の先頭 16 桁)。comparators.py は 0 行(封 §1 は comparators.py に触らない)。
ENGINE_AT_MEASURE = {"adapters/xbrl/vocabulary.py": "27e71e9861fc5aad", "adapters/xbrl/comparators.py": "d8706338325e725b",
                     "adapters/xbrl/recipes.py": "bff243f13429b553", "adapters/xbrl/registry_setup.py": "f42ffe23aaa7673b"}
#: 段 2(既定の切り替え)などで動いたときの宣言された遷移: {path: (後の sha16, 遷移を宣言した封の path)}。段 1 の commit 時点では空。
#: 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py・recipes.py・registry_setup.py が動いた。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
# 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
# 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
ENGINE_LATER = {"adapters/xbrl/vocabulary.py": ("85896a67913ce1e7", SEAL_P27),
                "adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27),
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
TO_CHECK = "detected:POINTER_NOT_FOUND"


# ----------------------------------------------------------------------------------------------------------------
# 独立の数え直し(script の関数を使わない)
def recount_l1(sec):
    mv = sec[u"動いた行"]
    docs = sec[u"書類"]
    S = lambda r, side: r[side][u"state"]
    moved_ok = [r for r in mv if S(r, u"P24") == "VALUE_MISMATCH" and S(r, u"P25") == "POINTER_NOT_FOUND" and r[u"P25"][u"reason"] == NSV]
    st = lambda side, s: sum(d[side].get(s, 0) for d in docs)
    return {u"動いた": len(mv), u"動いた(書類別の合計)": sum(d[u"動いた"] for d in docs), u"VM→PNF nsv": len(moved_ok), u"それ以外の向き": len(mv) - len(moved_ok),
            u"書類数": len(docs), u"claims": sum(d[u"claims"] for d in docs), u"最後の枝に入った(書類別の合計)": sum(d[u"最後の枝に入った"] for d in docs),
            u"GROUNDED P24": st(u"states P24", "GROUNDED"), u"GROUNDED P25": st(u"states P25", "GROUNDED"),
            u"VM P24": st(u"states P24", "VALUE_MISMATCH"), u"VM P25": st(u"states P25", "VALUE_MISMATCH"),
            u"UNV P24": st(u"states P24", "UNVERIFIABLE"), u"UNV P25": st(u"states P25", "UNVERIFIABLE"),
            u"PNF P24": st(u"states P24", "POINTER_NOT_FOUND"), u"PNF P25": st(u"states P25", "POINTER_NOT_FOUND"),
            u"向き": dict((k, sum(1 for r in mv if u"%s(%s) → %s(%s)" % (r[u"P24"][u"state"], r[u"P24"][u"reason"], r[u"P25"][u"state"], r[u"P25"][u"reason"]) == k))
                        for k in sorted({u"%s(%s) → %s(%s)" % (r[u"P24"][u"state"], r[u"P24"][u"reason"], r[u"P25"][u"state"], r[u"P25"][u"reason"]) for r in mv})),
            u"P25 の pointer のある行": sum(1 for r in mv if r[u"P25"][u"pointers"]), u"P25 の recomputed のある行": sum(1 for r in mv if r[u"P25"][u"recomputed"] is not None)}


def reading_category(t):
    return re.split(r"[(（:：]", t)[0].strip()


def recount_reading(rows):
    return {u"行": len(rows), READ_OK: sum(1 for r in rows if r.get(u"読み") == READ_OK), READ_WRONG: sum(1 for r in rows if r.get(u"読み") == READ_WRONG),
            READ_UNSURE: sum(1 for r in rows if r.get(u"読み") == READ_UNSURE), u"未読": sum(1 for r in rows if r.get(u"読み") not in READ_WORDS)}


def recount_l2l3(rec):
    mv = rec[u"L1"][u"動いた行"]
    keys = set((r[u"doc"], r[u"id"]) for r in mv)
    proto = set(tuple(x.split(" ")) for x in rec[u"L3"][u"試作で読んだ集合"][u"一覧"])
    unread = rec[u"L3"][u"未読の行"]
    kept = rec[u"L2"][u"残る行"]
    ev = rec[u"L2"][u"最後の枝に入った行の証拠"]
    return {u"動いた": len(keys), u"試作": len(proto), u"試作∩動いた": len(proto & keys), u"動いた−試作": sorted(keys - proto), u"未読の行": sorted((r[u"doc"], r[u"id"]) for r in unread),
            u"証拠の合計": sum(ev.values()), u"証拠なし": ev.get("None", 0), u"証拠あり": sum(v for k, v in ev.items() if k != "None"),
            u"未読": recount_reading(unread), u"残る": recount_reading(kept), u"残る行": len(kept),
            u"未読の型": dict((k, sum(1 for r in unread if r[u"dossier"][u"型"] == k)) for k in sorted({r[u"dossier"][u"型"] for r in unread}))}


def recount_l4(rows):
    n = len(rows)
    passed = lambda s: s.startswith(u"通した")
    return {u"注入": n, u"P25 通した": sum(1 for r in rows if passed(r[u"P25"][u"結果"])), u"P24 通した": sum(1 for r in rows if passed(r[u"P24"][u"結果"])),
            u"P24 止めた": sum(1 for r in rows if r[u"P24"][u"state"] == "VALUE_MISMATCH"), u"P25 止めた": sum(1 for r in rows if r[u"P25"][u"state"] == "VALUE_MISMATCH"),
            u"要確認に移る": sum(1 for r in rows if r[u"P24"][u"state"] == "VALUE_MISMATCH" and r[u"P25"][u"state"] == "POINTER_NOT_FOUND"),
            u"違う行(全部)": sum(1 for r in rows if r[u"P24"] != r[u"P25"]),
            u"P24 その他": sum(1 for r in rows if r[u"P24"][u"結果"] == u"その他"), u"P25 その他": sum(1 for r in rows if r[u"P25"][u"結果"] == u"その他")}


def recount_l5(rows):
    both = [r for r in rows if r[u"P24"] is not None and r[u"P25"] is not None]
    return {u"P25 の行": sum(1 for r in rows if r[u"P25"] is not None), u"P24 の行": sum(1 for r in rows if r[u"P24"] is not None), u"共通": len(both),
            u"P25 の通した id": [r[u"id"] for r in rows if r[u"P25"] == PASSED], u"P24 の通した id": [r[u"id"] for r in rows if r[u"P24"] == PASSED],
            u"P25 の止めた": sum(1 for r in rows if r[u"P25"] == STOPPED), u"P24 の止めた": sum(1 for r in rows if r[u"P24"] == STOPPED),
            u"P25 の要確認": sum(1 for r in rows if r[u"P25"] == TO_CHECK),
            u"VM→要確認": sum(1 for r in both if r[u"P24"] == STOPPED and r[u"P25"] == TO_CHECK),
            u"結果が違う共通の行": sum(1 for r in both if r[u"P24"] != r[u"P25"]),
            u"VM→要確認の型": dict((k, sum(1 for r in both if r[u"P24"] == STOPPED and r[u"P25"] == TO_CHECK and r[u"型"] == k))
                           for k in sorted({r[u"型"] for r in both if r[u"P24"] == STOPPED and r[u"P25"] == TO_CHECK}))}


def recount_l6(rows):
    inj = [r for r in rows if r[u"注入か"]]
    return {u"行": len(rows), u"注入": len(inj), u"動いた": sorted(u"%s %s" % (r[u"doc"], r[u"id"]) for r in rows if r[u"Core 自身 P24"] != r[u"Core 自身 P25"]),
            u"P24 G(注入)": sum(1 for r in inj if r[u"Core 自身 P24"][u"state"] == "GROUNDED"), u"P25 G(注入)": sum(1 for r in inj if r[u"Core 自身 P25"][u"state"] == "GROUNDED"),
            u"P24 VM(注入)": sum(1 for r in inj if r[u"Core 自身 P24"][u"state"] == "VALUE_MISMATCH"),
            u"VM→要確認(注入)": sum(1 for r in inj if r[u"Core 自身 P24"][u"state"] == "VALUE_MISMATCH" and r[u"Core 自身 P25"][u"state"] == "POINTER_NOT_FOUND"),
            u"P24 VM(無改変)": sum(1 for r in rows if not r[u"注入か"] and r[u"Core 自身 P24"][u"state"] == "VALUE_MISMATCH"),
            u"P25 VM(無改変)": sum(1 for r in rows if not r[u"注入か"] and r[u"Core 自身 P25"][u"state"] == "VALUE_MISMATCH")}


def recount_l7(rows):
    done = [x for x in rows if x.get(u"変え方")]
    valid = [x for x in done if x[u"P24"].get(u"state") is not None and x[u"P25"].get(u"state") is not None]
    st = lambda x, p: x[p].get(u"state")
    return {u"行": len({(x[u"doc"], x[u"id"]) for x in rows}), u"注入": len(done), u"有効": len(valid), u"有効でない": len(done) - len(valid),
            u"P25 G(全部)": sum(1 for x in done if st(x, u"P25") == "GROUNDED"), u"P24 G(全部)": sum(1 for x in done if st(x, u"P24") == "GROUNDED"),
            u"P25 VM": sum(1 for x in valid if st(x, u"P25") == "VALUE_MISMATCH"), u"P25 PNF": sum(1 for x in valid if st(x, u"P25") == "POINTER_NOT_FOUND"),
            u"P25 UNV": sum(1 for x in valid if st(x, u"P25") == "UNVERIFIABLE"),
            u"VM→PNF": sum(1 for x in valid if st(x, u"P24") == "VALUE_MISMATCH" and st(x, u"P25") == "POINTER_NOT_FOUND"),
            u"残り": [x for x in valid if st(x, u"P25") != "POINTER_NOT_FOUND"]}


def check_readings(rec):
    """L-3 の未読の行 = 動いた行 − 試作で読んだ集合((doc, id))、L-2 の残る行。どの行にも読みの語と根拠が付いている。
    読みの中身の正しさは縛れない(人(エージェント)の読み)。縛るのは『読みが今回の行のものであること』だけ。"""
    p = rec[u"L3"][u"試作で読んだ集合"]
    assert digest(p[u"一覧"]) == PROTO_DIGEST, u"試作で読んだ集合の digest が留めた値と違う"
    c = recount_l2l3(rec)
    assert c[u"試作"] == PROTO_N == p[u"(doc, id) の数"] and c[u"試作∩動いた"] == PROTO_MOVED == p[u"うち段 1 で動いた行"], u"試作の集合"
    assert p[u"うち動かなかった(P25 でも VALUE_MISMATCH に残る等)"] == PROTO_N - PROTO_MOVED
    assert c[u"未読の行"] == c[u"動いた−試作"], u"未読の行が『動いた行 − 試作で読んだ集合』と違う"
    assert len(set(c[u"未読の行"])) == len(c[u"未読の行"]), u"未読の行に重複"
    assert rec[u"L3"][u"動いた行"] == c[u"動いた"]
    mine = dict(((r[u"doc"], r[u"id"]), r) for r in rec[u"L1"][u"動いた行"])
    for r in rec[u"L3"][u"未読の行"]:
        m = mine[(r[u"doc"], r[u"id"])]
        assert r[u"文"] == m[u"文"] and r[u"no_same_value"] == m[u"no_same_value"], (r[u"doc"], r[u"id"])
        assert r[u"読み"] in READ_WORDS and r[u"根拠"].strip(), (r[u"doc"], r[u"id"])
    for r in rec[u"L2"][u"残る行"]:
        assert r[u"読み"] in READ_WORDS and r[u"根拠"].strip(), (r[u"doc"], r[u"id"])
        assert r[u"証拠"] and (r[u"doc"], r[u"id"]) not in mine, (r[u"doc"], r[u"id"])        # 証拠が在って名指しに残った行は、動いた行ではない
    assert len({(r[u"doc"], r[u"id"]) for r in rec[u"L2"][u"残る行"]}) == len(rec[u"L2"][u"残る行"])


def check_record(rec):
    """記録の集計を、行から数え直した値と突き合わせる。壊した記録で赤くなる。"""
    vr = jload(VOCAB_REC)
    # L-1
    sec = rec[u"L1"]
    c = recount_l1(sec)
    s = sec[u"集計"]
    assert c[u"動いた"] == c[u"動いた(書類別の合計)"] == s[u"動いた(全 state)"], u"動いた"
    assert s[u"VALUE_MISMATCH → POINTER_NOT_FOUND(no_same_value)"] == c[u"VM→PNF nsv"] and s[u"それ以外の向き"] == c[u"それ以外の向き"]
    assert sum(s[u"向き(全部)"].values()) == c[u"動いた"], u"向きの合計"
    assert s[u"書類数"] == c[u"書類数"] == 67 and s[u"総 claim"] == c[u"claims"] and rec[u"書類の数"][u"経営分析の文を持つ"] == 67
    for k, v in ((u"GROUNDED", c[u"GROUNDED P24"]), (u"VALUE_MISMATCH", c[u"VM P24"]), (u"UNVERIFIABLE", c[u"UNV P24"]), (u"POINTER_NOT_FOUND", c[u"PNF P24"])):
        assert s[u"%s の合計 P24" % k] == v, k
    for k, v in ((u"GROUNDED", c[u"GROUNDED P25"]), (u"VALUE_MISMATCH", c[u"VM P25"]), (u"UNVERIFIABLE", c[u"UNV P25"]), (u"POINTER_NOT_FOUND", c[u"PNF P25"])):
        assert s[u"%s の合計 P25" % k] == v, k
    assert s[u"最後の枝に入った行(P25)"] == c[u"最後の枝に入った(書類別の合計)"] == rec[u"L2"][u"最後の枝に入った行"], u"最後の枝に入った行"
    assert c[u"P25 の pointer のある行"] == 0 and c[u"P25 の recomputed のある行"] == 0, u"no_same_value は pointer なし(名指しは provenance だけ)"
    for x in sec[u"動いた行"]:
        assert x[u"P25"][u"reason"] == NSV and x[u"raw reason P25"] == NSV and x[u"last_branch_evidence"] is None, (x[u"doc"], x[u"id"])
        assert x[u"no_same_value"][u"named"] and x[u"P24"][u"pointers"] == [x[u"no_same_value"][u"named"]], (x[u"doc"], x[u"id"])      # 名指しは P24 が結んだ fact と同じ
        assert x[u"P24"][u"recomputed"] == x[u"no_same_value"][u"value"], (x[u"doc"], x[u"id"])
    # 対照: P24 の書類別の state が P24 の記録(vocab)と一致 = 旗が偽の側は動いていない
    vd = dict((d[u"doc"], d) for d in vr[u"W1W2W3"][u"書類"])
    for d in sec[u"書類"]:
        assert vd[d[u"doc"]][u"states P24"] == d[u"states P24"], d[u"doc"]
        assert vd[d[u"doc"]][u"claims"] == d[u"claims"], d[u"doc"]
    # L-2・L-3
    check_readings(rec)
    c23 = recount_l2l3(rec)
    assert c23[u"証拠の合計"] == rec[u"L2"][u"最後の枝に入った行"] and c23[u"証拠なし"] == c[u"動いた"], u"証拠別の合計"
    assert c23[u"証拠あり"] == c23[u"残る行"], u"証拠があって名指しに残った行 = 残る行"
    # L-4
    w4 = rec[u"L4"]
    c4 = recount_l4(w4[u"行"])
    s4 = w4[u"集計"]
    assert c4[u"注入"] == 485 == s4[u"注入"] == sum(p[u"作れた"] for p in w4[u"書類別"]), u"L-4 注入"
    assert s4[u"P25 で通した(GROUNDED のまま)"][u"件"] == c4[u"P25 通した"] and s4[u"P24(対照)で通した"][u"件"] == c4[u"P24 通した"]
    assert s4[u"P24 の止め"][u"件"] == c4[u"P24 止めた"] and s4[u"P25 で止めた(VALUE_MISMATCH)"][u"件"] == c4[u"P25 止めた"]
    assert s4[u"止め(P24 の VALUE_MISMATCH)のうち要確認(POINTER_NOT_FOUND)に移る"][u"件"] == c4[u"要確認に移る"]
    assert s4[u"止め(P24 の VALUE_MISMATCH)のうち要確認(POINTER_NOT_FOUND)に移る"][u"分母"] == c4[u"P24 止めた"]
    assert s4[u"P24 と P25 で(結果, state, reason, pointers)のどれかが違う行"] == c4[u"違う行(全部)"] == len(s4[u"要確認に移る行"])
    want = dict(((r[u"書類"], r[u"id"]), r[u"P24"]) for r in vr[u"W4"][u"行"])
    assert len(want) == 485
    for r in w4[u"行"]:
        w = want[(r[u"書類"], r[u"id"])]
        assert (w[u"結果"], w[u"state"], w[u"reason"], w[u"pointers"]) == (r[u"P24"][u"結果"], r[u"P24"][u"state"], r[u"P24"][u"reason"], r[u"P24"][u"pointers"]), (r[u"書類"], r[u"id"])
    assert w4[u"対照: P24 の再計算と P24 の記録"][u"違った行"] == 0
    # L-5
    w5 = rec[u"L5"]
    c5 = recount_l5(w5[u"行"])
    s5 = w5[u"集計"]
    assert w5[u"通した P25"][u"件"] == len(c5[u"P25 の通した id"]) and w5[u"通した P25"][u"分母"] == c5[u"P25 の行"] == w5[u"P25 の行数"]
    assert w5[u"通した P24(対照)"][u"件"] == len(c5[u"P24 の通した id"]) and w5[u"通した P24(対照)"][u"分母"] == c5[u"P24 の行"] == w5[u"P24 の行数"]
    assert w5[u"止めた P25"][u"件"] == c5[u"P25 の止めた"] and w5[u"止めた P24(対照)"][u"件"] == c5[u"P24 の止めた"]
    assert sum(w5[u"その他 P25"].values()) == c5[u"P25 の要確認"] and set(w5[u"その他 P25"]) <= {TO_CHECK}, u"その他は要確認だけ"
    assert [x[u"id"] for x in w5[u"通した P25 の一覧"]] == c5[u"P25 の通した id"]
    assert s5[u"注入の止めが要確認に移った(共通の行)"] == c5[u"VM→要確認"] and s5[u"共通の行"] == c5[u"共通"] == 247 and s5[u"移った行の型"] == c5[u"VM→要確認の型"]
    assert s5[u"共通の行で結果が違う行"] == c5[u"結果が違う共通の行"] == c5[u"VM→要確認"], u"結果が変わった共通の行は全部 VM → 要確認"
    wantr = dict(((x[u"id"], x[u"型"]), x[u"P24"]) for x in vr[u"W5"][u"行"])
    gotr = dict(((r[u"id"], r[u"型"]), r[u"P24"]) for r in w5[u"行"] if r[u"P24"] is not None)
    assert wantr == gotr, u"P24 の欄が P24 の記録の儀式と違う(旗が偽の側が動いている)"
    assert w5[u"対照: P24 の再計算が P24 の記録の W-5 と違った行"] == 0
    # L-6
    w6 = rec[u"L6"]
    c6 = recount_l6(w6[u"行"])
    s6 = w6[u"集計"]
    assert c6[u"行"] == 192 == s6[u"行"] and c6[u"注入"] == 64 == s6[u"注入"]
    assert s6[u"Core 自身が P24 → P25 で動いた行"] == len(c6[u"動いた"]) and sorted(s6[u"動いた行の id"]) == c6[u"動いた"]
    assert s6[u"全注入で Core 自身 P25 が GROUNDED"][u"件"] == c6[u"P25 G(注入)"] and s6[u"全注入で Core 自身 P24 が GROUNDED"][u"件"] == c6[u"P24 G(注入)"]
    assert s6[u"注入の P24 の止め(VALUE_MISMATCH)"] == c6[u"P24 VM(注入)"] and s6[u"注入の止めのうち要確認(POINTER_NOT_FOUND)に移る"] == c6[u"VM→要確認(注入)"]
    assert s6[u"無改変で P24 の VALUE_MISMATCH"] == c6[u"P24 VM(無改変)"] and s6[u"無改変で P25 の VALUE_MISMATCH"] == c6[u"P25 VM(無改変)"]
    vs2 = dict(((r[u"doc"], r[u"id"]), r[u"Core 自身 P24"]) for r in vr[u"S2"][u"行"])
    for r in w6[u"行"]:
        assert vs2[(r[u"doc"], r[u"id"])] == r[u"Core 自身 P24"], (r[u"doc"], r[u"id"])        # 対照
    # L-7
    w7 = rec[u"L7"]
    c7 = recount_l7(w7[u"行"])
    s7 = w7[u"集計"]
    assert s7[u"対象の行(P24 → P25 に動いた行)"] == c7[u"行"] == c[u"動いた"], u"L-7 の対象の行"
    assert (s7[u"注入の数"], s7[u"有効な注入"], s7[u"有効でない注入(主張が見つからない・値がずれた)"]) == (c7[u"注入"], c7[u"有効"], c7[u"有効でない"])
    assert s7[u"作れなかった"] == 2 * c7[u"行"] - c7[u"注入"], u"作れなかった"
    assert (s7[u"P25 で GROUNDED(全部の注入)"], s7[u"P24(対照)で GROUNDED(全部の注入)"]) == (c7[u"P25 G(全部)"], c7[u"P24 G(全部)"])
    assert s7[u"有効な注入の P25"] == dict((k, v) for k, v in (("POINTER_NOT_FOUND", c7[u"P25 PNF"]), ("UNVERIFIABLE", c7[u"P25 UNV"]), ("VALUE_MISMATCH", c7[u"P25 VM"])) if v)
    assert s7[u"P24 で VALUE_MISMATCH(違う)が P25 で POINTER_NOT_FOUND(要確認)に移った有効な注入"] == c7[u"VM→PNF"]
    assert len(s7[u"P25 で GROUNDED の行"]) == c7[u"P25 G(全部)"]
    # provenance
    pv = rec[u"provenance"]
    assert pv[u"no_same_value の Recipe"] == c[u"動いた"] == pv[u"provenance に名指しあり"], u"provenance"
    assert all(k in (u"no_same_value の Recipe", u"provenance に名指しあり") for k in pv), u"provenance の (0 のはず)の欄が出ている"
    # 環境
    env = rec[u"環境"]
    assert env[u"比べた profile"] == ["P24", "P25"] and env[u"費用"] == u"0 USD" and env[u"DEFAULT_PROFILE"] == "P22"
    for k, rel in ((u"vocabulary.py の sha16", "adapters/xbrl/vocabulary.py"), (u"comparators.py の sha16", "adapters/xbrl/comparators.py"),
                   (u"recipes.py の sha16", "adapters/xbrl/recipes.py"), (u"registry_setup.py の sha16", "adapters/xbrl/registry_setup.py")):
        assert env[k] == ENGINE_AT_MEASURE[rel], k


def check_inputs(rec):
    inp = rec[u"入力の sha256"]
    d67 = inp[u"書類 67(経営分析の文を持つ)の sha256"]
    assert len(d67) == 67
    assert digest([u"%s\t%s" % (k, d67[k]) for k in sorted(d67)]) == DOCS67_DIGEST, u"書類 67 の digest が留めた値と違う"
    assert sorted(d[u"doc"] for d in rec[u"L1"][u"書類"]) == sorted(d67), u"L-1 の書類が入力の 67 と違う"
    assert inp[u"書類 214(67 の外)の sha256 を束ねた値(path 順の 'docID\\tsha256' の行)"] == DOCS214_DIGEST
    for rel, want in INPUT_SHAS.items():
        assert inp[rel] == want, rel
    assert inp[u"儀式の同梱書類"] == RITUAL_ZIP_SHA
    assert len(inp[u"人の読みの入力 file の sha256(``--readings``。内容は記録の行に写した)"]) == 64
    assert len(inp[u"engine の変異の表の入力 file の sha256(``--mutations``。手で走らせた表の写し)"]) == 64
    assert len(inp[u"seat answers(hybrid_s2_answers)"]) == 8


# ----------------------------------------------------------------------------------------------------------------
# 予測の判定(封の字から幅を読み、記録の行から門が自分で求める)
def seal_cells(seal, tag):
    for l in seal.splitlines():
        if l.startswith(u"| **%s** |" % tag):
            return [c.strip() for c in l.strip().strip(u"|").split(u"|")]
    raise AssertionError(tag)


def bounds(seal):
    c = dict((t, seal_cells(seal, t)[1]) for t in ("L-1", "L-2", "L-3", "L-4", "L-5", "L-6", "L-7", "L-8", "L-9"))
    n = lambda s: int(s.replace(",", ""))
    m1 = re.search(r"VALUE_MISMATCH \*\*(\d+)〜(\d+)\*\*.*で \*\*(\d+)〜(\d+)\*\*、GROUNDED と UNVERIFIABLE の数は P24 と同じ", c["L-1"])
    m2 = re.search(r"VM に残る行 \*\*(\d+)〜(\d+)\*\*、全部読んで「文が本当に違う」\*\*(\d+)〜(\d+)\*\*", c["L-2"])
    m3 = re.search(r"「文が本当に違う」が読んだ行の (\d+)% 以下", c["L-3"])
    m4 = re.search(r"通す \*\*(\d+)\*\*、止め.*→ 要確認 \*\*(\d+)〜(\d+)\*\*", c["L-4"])
    m5 = re.search(r"通した \*\*(\d+)〜(\d+)\*\*、注入の止め → 要確認 \*\*(\d+)〜(\d+)\*\*", c["L-5"])
    m6 = re.search(r"注入の GROUNDED \*\*(\d+) / (\d+)\*\*、注入の止め → 要確認 \*\*(\d+)〜(\d+)\*\*", c["L-6"])
    m7 = re.search(r"P25 が GROUNDED にする \*\*(\d+)\*\* 回", c["L-7"])
    m8 = re.search(r"`recipes.py` \*\*\+(\d+)〜\+(\d+) / −(\d+)\*\*、`vocabulary.py` \*\*≤ (\d+) 行\*\*、`registry_setup.py` \*\*≤ (\d+) 行\*\*", c["L-8"])
    assert m1 and m2 and m3 and m4 and m5 and m6 and m7 and m8, u"封の予測の書き方が変わった"
    return {"l1_vm": (n(m1.group(1)), n(m1.group(2))), "l1_moved": (n(m1.group(3)), n(m1.group(4))), "l2_kept": (int(m2.group(1)), int(m2.group(2))),
            "l2_wrong": (int(m2.group(3)), int(m2.group(4))), "l3_pct": int(m3.group(1)), "l4_pass": int(m4.group(1)), "l4_to_check": (int(m4.group(2)), int(m4.group(3))),
            "l5_pass": (int(m5.group(1)), int(m5.group(2))), "l5_to_check": (int(m5.group(3)), int(m5.group(4))),
            "l6_g": (int(m6.group(1)), int(m6.group(2))), "l6_to_check": (int(m6.group(3)), int(m6.group(4))), "l7_g": int(m7.group(1)),
            "l8_rec": (int(m8.group(1)), int(m8.group(2))), "l8_rec_del": int(m8.group(3)), "l8_voc": int(m8.group(4)), "l8_reg": int(m8.group(5))}


ALLOWED_RED_KINDS = (u"登録の一覧", u"旗の形", u"sha の留め", u"diff の門")


def judgments(rec, seal):
    b = bounds(seal)
    J = {}
    c = recount_l1(rec[u"L1"])
    J["L-1"] = u"当たり" if (b["l1_vm"][0] <= c[u"VM P25"] <= b["l1_vm"][1] and c[u"それ以外の向き"] == 0 and b["l1_moved"][0] <= c[u"VM→PNF nsv"] <= b["l1_moved"][1]
                            and c[u"GROUNDED P25"] == c[u"GROUNDED P24"] and c[u"UNV P25"] == c[u"UNV P24"]) else u"外れ"
    c23 = recount_l2l3(rec)
    r2 = c23[u"残る"]
    if r2[u"未読"]:
        J["L-2"] = u"読み待ち"
    else:
        J["L-2"] = u"当たり" if (b["l2_kept"][0] <= c23[u"残る行"] <= b["l2_kept"][1] and b["l2_wrong"][0] <= r2[READ_WRONG] <= b["l2_wrong"][1]) else u"外れ"
    r3 = c23[u"未読"]
    if r3[u"未読"] or not r3[u"行"]:
        J["L-3"] = u"読み待ち"
    else:
        J["L-3"] = u"当たり" if r3[READ_WRONG] * 100 <= b["l3_pct"] * r3[u"行"] else u"外れ"
    c4 = recount_l4(rec[u"L4"][u"行"])
    J["L-4"] = u"当たり" if (c4[u"P25 通した"] == b["l4_pass"] and b["l4_to_check"][0] <= c4[u"要確認に移る"] <= b["l4_to_check"][1]) else u"外れ"
    c5 = recount_l5(rec[u"L5"][u"行"])
    J["L-5"] = u"当たり" if (b["l5_pass"][0] <= len(c5[u"P25 の通した id"]) <= b["l5_pass"][1] and b["l5_to_check"][0] <= c5[u"VM→要確認"] <= b["l5_to_check"][1]) else u"外れ"
    c6 = recount_l6(rec[u"L6"][u"行"])
    J["L-6"] = u"当たり" if (c6[u"P25 G(注入)"] == b["l6_g"][0] and c6[u"注入"] == b["l6_g"][1] and b["l6_to_check"][0] <= c6[u"VM→要確認(注入)"] <= b["l6_to_check"][1]) else u"外れ"
    c7 = recount_l7(rec[u"L7"][u"行"])
    J["L-7"] = u"当たり" if c7[u"P25 G(全部)"] == b["l7_g"] else u"外れ"
    e8 = rec[u"L8"]
    d = e8[u"engine の差分"]
    rc, v, rs, cm = (d["adapters/xbrl/recipes.py"], d["adapters/xbrl/vocabulary.py"], d["adapters/xbrl/registry_setup.py"], d["adapters/xbrl/comparators.py"])
    kinds = set(x[u"種類"] for x in e8[u"既存試験の赤(直す前)"])
    tests_ok = bool(e8.get(u"既存試験")) and all(t[u"rc"] == 0 for t in e8[u"既存試験"])
    ok8 = (b["l8_rec"][0] <= rc[u"挿入"] + rc[u"削除"] <= b["l8_rec"][1] and rc[u"削除"] == b["l8_rec_del"] and v[u"挿入"] + v[u"削除"] <= b["l8_voc"]
           and rs[u"挿入"] + rs[u"削除"] <= b["l8_reg"] and cm[u"挿入"] == 0 and cm[u"削除"] == 0 and d[u"core/"][u"差の行数"] == 0 and kinds <= set(ALLOWED_RED_KINDS) and tests_ok)
    J["L-8"] = u"当たり" if ok8 else u"外れ"
    J["L-9"] = u"判定しない(段 2)"
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
    L = [u"| # | 封の予測 | 封の外れ方 | 実測 | 判定 |", u"|---|---|---|---|---|"]
    for k in sorted(pr, key=lambda s: int(s.split("-")[1])):
        sc = seal_cells(seal, k)
        L.append(u"| **%s** | %s | %s | %s | **%s** |" % (k, cell(sc[1]), cell(sc[2]), cell(pr[k][u"実測"]), pr[k][u"判定"]))
    B["予測の表"] = u"\n".join(L)
    sec = rec[u"L1"]
    c = recount_l1(sec)
    L = [u"| 項目 | 件数 |", u"|---|---:|",
         u"| 書類 | %d |" % c[u"書類数"], u"| claim の総数 | %s |" % comma(c[u"claims"]), u"| 動いた行(全 state) | %d |" % c[u"動いた"],
         u"| VALUE_MISMATCH → POINTER_NOT_FOUND(`no_same_value`) | %d |" % c[u"VM→PNF nsv"], u"| それ以外の向き | %d |" % c[u"それ以外の向き"],
         u"| 最後の枝に入った行(P25) | %d |" % c[u"最後の枝に入った(書類別の合計)"],
         u"| うち 名指しに残った行(証拠あり) | %d |" % recount_l2l3(rec)[u"証拠あり"],
         u"| P25 の動いた行で pointer の在る行 | %d |" % c[u"P25 の pointer のある行"]]
    B["L-1 の数"] = u"\n".join(L)
    L = [u"| 無改変 67 書類 | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |", u"|---|---:|---:|---:|---:|",
         u"| P24(対照) | %s | %s | %s | %s |" % (comma(c[u"GROUNDED P24"]), comma(c[u"VM P24"]), comma(c[u"UNV P24"]), comma(c[u"PNF P24"])),
         u"| **P25** | **%s** | **%s** | **%s** | **%s** |" % (comma(c[u"GROUNDED P25"]), comma(c[u"VM P25"]), comma(c[u"UNV P25"]), comma(c[u"PNF P25"]))]
    B["L-1 の state の表"] = u"\n".join(L)
    L = [u"| 向き(P24 の state(reason) → P25 の state(reason)) | 行 |", u"|---|---:|"]
    for k, v in sorted(c[u"向き"].items()):
        L.append(u"| %s | %d |" % (cell(k), v))
    B["遷移表"] = u"\n".join(L)
    ev = rec[u"L2"][u"最後の枝に入った行の証拠"]
    L = [u"| 最後の枝に入った行の証拠 | 行 |", u"|---|---:|"] + [u"| %s | %d |" % (cell(u"証拠なし(名指さず要確認へ)" if k == "None" else k), v) for k, v in sorted(ev.items())]
    B["証拠別の表"] = u"\n".join(L)
    L = [u"| doc | id | 証拠 | 名指した fact | 読み | 根拠 |", u"|---|---|---|---|---|---|"]
    for r in rec[u"L2"][u"残る行"]:
        L.append(u"| %s | %s | %s | %s | %s | %s |" % (r[u"doc"], r[u"id"], cell(r[u"証拠"]), cell(r[u"dossier"][u"名指した fact"]), r[u"読み"], cell(r[u"根拠"])))
    B["L-2 の表"] = u"\n".join(L)
    c23 = recount_l2l3(rec)
    L = [u"| 項目 | 件数 |", u"|---|---:|", u"| 段 1 で動いた行 | %d |" % c23[u"動いた"], u"| 試作で読んだ集合 (doc, id) | %d |" % c23[u"試作"],
         u"| うち 段 1 で動いた行 | %d |" % c23[u"試作∩動いた"], u"| 試作で読んでいない行(動いた行 − 試作で読んだ集合。全部読んだ) | %d |" % c23[u"未読"][u"行"]]
    B["L-3 の分母の表"] = u"\n".join(L)
    L = [u"| 行の型(読むための材料の分け方) | 読み | 行 |", u"|---|---|---:|"]
    t = {}
    for r in rec[u"L3"][u"未読の行"]:
        k = (r[u"dossier"][u"型"], r[u"読み"])
        t[k] = t.get(k, 0) + 1
    for (a, w), v in sorted(t.items()):
        L.append(u"| %s | %s | %d |" % (cell(a), w, v))
    B["L-3 の読みの表"] = u"\n".join(L)
    L = [u"| doc | id | 読み | 文 | 名指した fact | 名指した値 | 根拠 |", u"|---|---|---|---|---|---|---|"]
    for r in rec[u"L3"][u"未読の行"]:
        if r[u"読み"] != READ_OK:
            L.append(u"| %s | %s | %s | %s | %s | %s | %s |" % (r[u"doc"], r[u"id"], r[u"読み"], cell(r[u"文"]), cell(r[u"no_same_value"][u"named"]),
                                                              r[u"no_same_value"][u"value"], cell(r[u"根拠"])))
    B["L-3 の違う・分からない"] = u"\n".join(L)
    c4 = recount_l4(rec[u"L4"][u"行"])
    L = [u"| 穴 B の注入 485 件 | 通した | 止めた | その他 |", u"|---|---:|---:|---:|",
         u"| P24(対照) | %d | %d | %d |" % (c4[u"P24 通した"], c4[u"P24 止めた"], c4[u"P24 その他"]),
         u"| **P25** | **%d** | **%d** | **%d** |" % (c4[u"P25 通した"], c4[u"P25 止めた"], c4[u"P25 その他"]),
         u"| P24 の止めのうち要確認に移る | | | %d |" % c4[u"要確認に移る"]]
    B["L-4 の表"] = u"\n".join(L)
    L = [u"| 書類 | id | 元の字 | 後の字 | 文脈 |", u"|---|---|---|---|---|"]
    for x in rec[u"L4"][u"集計"][u"要確認に移る行"]:
        L.append(u"| %s | %s | %s | %s | %s |" % (x[u"書類"], x[u"id"], cell(x[u"元の字"]), cell(x[u"後の字"]), cell(x[u"文脈 60 字"])))
    B["L-4 の移った行"] = u"\n".join(L)
    w5 = rec[u"L5"]
    c5 = recount_l5(w5[u"行"])
    L = [u"| 儀式 | 注入の行 | 通した | 止めた | 要確認 |", u"|---|---:|---:|---:|---:|",
         u"| P24(対照) | %d | %d | %d | %d |" % (c5[u"P24 の行"], len(c5[u"P24 の通した id"]), c5[u"P24 の止めた"], sum(1 for r in w5[u"行"] if r[u"P24"] == TO_CHECK)),
         u"| **P25** | **%d** | **%d** | **%d** | **%d** |" % (c5[u"P25 の行"], len(c5[u"P25 の通した id"]), c5[u"P25 の止めた"], c5[u"P25 の要確認"]),
         u"| 素の書類 GROUNDED(P24 → P25) | %d → %d | | | |" % (w5[u"素の書類 P24"][u"state の分布"].get("GROUNDED", 0), w5[u"素の書類 P25"][u"state の分布"].get("GROUNDED", 0)),
         u"| 注入の止めが要確認に移った(型) | %d(%s) | | | |" % (c5[u"VM→要確認"], cell(u"・".join(u"%s %d" % (k, v) for k, v in sorted(c5[u"VM→要確認の型"].items()))))]
    B["L-5 の表"] = u"\n".join(L)
    L = [u"| id | 分類 | 値の差 | 1 最小単位 | 文脈 |", u"|---|---|---|---|---|"]
    for x in w5[u"通した P25 の一覧"]:
        L.append(u"| %s | %s | %s | %s | %s |" % (x[u"id"], cell(x[u"分類"]), x[u"値の差"], x[u"1 最小単位"], cell(x[u"文脈"])))
    B["L-5 の通した"] = u"\n".join(L)
    c6 = recount_l6(rec[u"L6"][u"行"])
    L = [u"| 段 2 の材料 192 行の Core 自身 | 件数 |", u"|---|---:|", u"| 行 | %d |" % c6[u"行"], u"| 注入 | %d |" % c6[u"注入"],
         u"| P24 → P25 で動いた行 | %d |" % len(c6[u"動いた"]), u"| 注入で Core 自身 P24 が GROUNDED | %d |" % c6[u"P24 G(注入)"],
         u"| 注入で Core 自身 P25 が GROUNDED | %d |" % c6[u"P25 G(注入)"], u"| 注入の P24 の止め(VALUE_MISMATCH) | %d |" % c6[u"P24 VM(注入)"],
         u"| うち 要確認に移る | %d |" % c6[u"VM→要確認(注入)"], u"| 無改変で VALUE_MISMATCH(P24 → P25) | %d → %d |" % (c6[u"P24 VM(無改変)"], c6[u"P25 VM(無改変)"])]
    B["L-6 の表"] = u"\n".join(L)
    s7 = rec[u"L7"][u"集計"]
    L = [u"| 変え方・結果(有効な注入) | P25 | P24(対照) |", u"|---|---:|---:|"]
    for k in sorted(set(s7[u"集計 P25(有効)"]) | set(s7[u"集計 P24(有効)"])):
        L.append(u"| %s | %d | %d |" % (cell(k), s7[u"集計 P25(有効)"].get(k, 0), s7[u"集計 P24(有効)"].get(k, 0)))
    B["L-7 の表"] = u"\n".join(L)
    c7 = recount_l7(rec[u"L7"][u"行"])
    L = [u"| doc | id | 変え方 | 元の字 → 後の字 | P25 の state | reason |", u"|---|---|---|---|---|---|"]
    for x in c7[u"残り"]:
        L.append(u"| %s | %s | %s | %s → %s | %s | %s |" % (x[u"doc"], x[u"id"], cell(x[u"変え方"]), cell(x[u"元の字"]), cell(x[u"後の字"]), x[u"P25"][u"state"], cell(x[u"P25"][u"reason"])))
    B["L-7 の残り"] = u"\n".join(L)
    pv = rec[u"provenance"]
    L = [u"| `no_same_value` の Recipe | 件数 |", u"|---|---:|"] + [u"| %s | %d |" % (cell(k), v) for k, v in sorted(pv.items())]
    B["provenance の表"] = u"\n".join(L)
    e8 = rec[u"L8"]
    d = e8[u"engine の差分"]
    L = [u"| file | 挿入 | 削除 |", u"|---|---:|---:|"]
    for f in ("adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py"):
        L.append(u"| `%s` | %d | %d |" % (f, d[f][u"挿入"], d[f][u"削除"]))
    L.append(u"| `core/` | %d | |" % d[u"core/"][u"差の行数"])
    B["L-8 の表"] = u"\n".join(L)
    L = [u"| 試験 | 種類 | 直し |", u"|---|---|---|"] + [u"| %s | %s | %s |" % (cell(x[u"試験"]), cell(x[u"種類"]), cell(x[u"直し"])) for x in e8[u"既存試験の赤(直す前)"]]
    B["L-8 の赤の表"] = u"\n".join(L)
    L = [u"| 試験 | 直し |", u"|---|---|"] + [u"| %s | %s |" % (cell(x[u"試験"]), cell(x[u"直し"])) for x in e8[u"覆いの門で赤になった試験(新しい試験 file を足したため。engine と無関係)"]]
    B["覆いの赤の表"] = u"\n".join(L)
    B["限界"] = u"\n".join(u"- %s" % cell(x) for x in rec[u"limits"])
    return B


def prose_facts(rec):
    P = {}
    pr = rec[u"予測の判定"]
    hit = sum(1 for v in pr.values() if v[u"判定"] == u"当たり")
    miss = sum(1 for v in pr.values() if v[u"判定"] == u"外れ")
    unm = sum(1 for v in pr.values() if v[u"判定"] == u"測れない")
    P["pred"] = u"**予測 機械判定 当たり %d / 外れ %d / 測れない %d**(L-1〜L-8。L-9 は段 2 なので判定しない)。" % (hit, miss, unm)
    d = rec[u"L8"][u"engine の差分"]
    v, c, r, g = d["adapters/xbrl/vocabulary.py"], d["adapters/xbrl/comparators.py"], d["adapters/xbrl/recipes.py"], d["adapters/xbrl/registry_setup.py"]
    P["head"] = (u"engine の直し: `adapters/xbrl/vocabulary.py` 挿入 %d・削除 %d、`adapters/xbrl/recipes.py` 挿入 %d・削除 %d、`adapters/xbrl/registry_setup.py` 挿入 %d・削除 %d、"
                 u"`adapters/xbrl/comparators.py` 挿入 %d・削除 %d、`core/` %d 行。") % (
        v[u"挿入"], v[u"削除"], r[u"挿入"], r[u"削除"], g[u"挿入"], g[u"削除"], c[u"挿入"], c[u"削除"], d[u"core/"][u"差の行数"])
    cc = recount_l1(rec[u"L1"])
    P["l1"] = u"67 書類(claim %s)の無改変で、P24 から P25 に動いた行は %d(全部 VALUE_MISMATCH から POINTER_NOT_FOUND の `no_same_value`。それ以外の向き %d)。VALUE_MISMATCH は P24 が %s、P25 が %s(差 %d)。GROUNDED は %s のまま、UNVERIFIABLE は %s のまま。" % (
        comma(cc[u"claims"]), cc[u"動いた"], cc[u"それ以外の向き"], comma(cc[u"VM P24"]), comma(cc[u"VM P25"]), cc[u"VM P25"] - cc[u"VM P24"],
        comma(cc[u"GROUNDED P25"]), comma(cc[u"UNV P25"]))
    c23 = recount_l2l3(rec)
    r2, r3 = c23[u"残る"], c23[u"未読"]
    P["l2"] = u"最後の枝に入った行 %d のうち、証拠があって名指しに残った行は %d。全部読んで、正しい文 %d・文が本当に違う %d・分からない %d(未読 %d)。" % (
        rec[u"L2"][u"最後の枝に入った行"], c23[u"残る行"], r2[READ_OK], r2[READ_WRONG], r2[READ_UNSURE], r2[u"未読"])
    P["l3"] = u"試作で読んでいない行(動いた行 %d から試作で読んだ集合のうち動いた %d を引いた %d 行)を全部読んで、正しい文 %d・文が本当に違う %d・分からない %d(未読 %d)。文が本当に違う %s。" % (
        c23[u"動いた"], c23[u"試作∩動いた"], r3[u"行"], r3[READ_OK], r3[READ_WRONG], r3[READ_UNSURE], r3[u"未読"], F(r3[READ_WRONG], r3[u"行"]))
    c4 = recount_l4(rec[u"L4"][u"行"])
    P["l4"] = u"穴 B の注入 %d 件を P25 で再検証すると、通した %s・止めた %s(P24 は通した %s・止めた %s)。P24 の止め %d のうち要確認に移った行は %d。" % (
        c4[u"注入"], F(c4[u"P25 通した"], c4[u"注入"]), F(c4[u"P25 止めた"], c4[u"注入"]), F(c4[u"P24 通した"], c4[u"注入"]), F(c4[u"P24 止めた"], c4[u"注入"]),
        c4[u"P24 止めた"], c4[u"要確認に移る"])
    w5 = rec[u"L5"]
    c5 = recount_l5(w5[u"行"])
    P["l5"] = u"儀式を P25 で回すと、通した %s・止めた %s・要確認 %s(P24 は通した %s・止めた %s)。通した id: %s。注入の止めが要確認に移った行は %d(素の書類の VALUE_MISMATCH の動きは含めない)。" % (
        F(len(c5[u"P25 の通した id"]), c5[u"P25 の行"]), F(c5[u"P25 の止めた"], c5[u"P25 の行"]), F(c5[u"P25 の要確認"], c5[u"P25 の行"]),
        F(len(c5[u"P24 の通した id"]), c5[u"P24 の行"]), F(c5[u"P24 の止めた"], c5[u"P24 の行"]), u"・".join(c5[u"P25 の通した id"]), c5[u"VM→要確認"])
    c6 = recount_l6(rec[u"L6"][u"行"])
    P["l6"] = u"段 2 の材料 %d 行(注入 %d)の Core 自身は、注入で P25 が GROUNDED にした %d・P24 の止め %d のうち要確認に移った %d。P24 から P25 で動いた行は %d。" % (
        c6[u"行"], c6[u"注入"], c6[u"P25 G(注入)"], c6[u"P24 VM(注入)"], c6[u"VM→要確認(注入)"], len(c6[u"動いた"]))
    c7 = recount_l7(rec[u"L7"][u"行"])
    P["l7"] = u"動いた %d 行に注入 %d 回(作れなかった %d・有効 %d・有効でない %d)。P25 が GROUNDED にした %d 回(P24 の対照も %d 回)。有効な注入のうち VALUE_MISMATCH が要確認に移ったのは %d、VALUE_MISMATCH のまま %d、UNVERIFIABLE %d。" % (
        c7[u"行"], c7[u"注入"], rec[u"L7"][u"集計"][u"作れなかった"], c7[u"有効"], c7[u"有効でない"], c7[u"P25 G(全部)"], c7[u"P24 G(全部)"], c7[u"VM→PNF"], c7[u"P25 VM"], c7[u"P25 UNV"])
    P["l9"] = (u"段 2 に人間へ見せる数(この実行では何も変えず、判定もしない): 無改変 %d 書類・claim %s のうち「違う」(VALUE_MISMATCH)は P24 %s → P25 %s、"
               u"結べない(POINTER_NOT_FOUND)は P24 %s → P25 %s。誤りを通す数は穴 B %s・儀式 %s・段 2 の材料の注入 %d / %d・動いた行への注入 %d / %d。"
               u"「違う」が「要確認」に移った注入の数は穴 B %d・儀式 %d・段 2 の材料 %d・動いた行への注入(有効)%d。") % (
        cc[u"書類数"], comma(cc[u"claims"]), F(cc[u"VM P24"], cc[u"claims"]), F(cc[u"VM P25"], cc[u"claims"]), F(cc[u"PNF P24"], cc[u"claims"]), F(cc[u"PNF P25"], cc[u"claims"]),
        F(c4[u"P25 通した"], c4[u"注入"]), F(len(c5[u"P25 の通した id"]), c5[u"P25 の行"]), c6[u"P25 G(注入)"], c6[u"注入"], c7[u"P25 G(全部)"], c7[u"注入"],
        c4[u"要確認に移る"], c5[u"VM→要確認"], c6[u"VM→要確認(注入)"], c7[u"VM→PNF"])
    e8 = rec[u"L8"]
    P["l8"] = u"既存試験の赤(直す前): %d 本。覆いの門の赤(新しい試験 file を足したため): %d 本。直した後の既存試験: %s。" % (
        len(e8[u"既存試験の赤(直す前)"]), len(e8[u"覆いの門で赤になった試験(新しい試験 file を足したため。engine と無関係)"]),
        u"・".join(u"%s → %s" % (t[u"コマンド"], t[u"最後の行"]) for t in e8.get(u"既存試験", [])))
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
    t = re.sub(r"[A-Za-z_][A-Za-z_0-9\-]*\d[A-Za-z_0-9\-]*", u"", t)      # S100YMFV・N076・L-1・P25・sha16 など
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
    for lit in (u"判定しない(段 2)", u"comparators.py は零行", u"門で縛れない", u"文が本当に違う", u"要確認", u"P24", u"P25"):
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
        c = recount_l1(r[u"L1"])
        self.assertEqual((c[u"動いた"], c[u"VM→PNF nsv"], c[u"それ以外の向き"]), (577, 577, 0))
        self.assertEqual((c[u"VM P24"], c[u"VM P25"], c[u"GROUNDED P24"], c[u"GROUNDED P25"], c[u"UNV P24"], c[u"UNV P25"]), (1203, 626, 4382, 4382, 1397, 1397))
        c23 = recount_l2l3(r)
        self.assertEqual((c23[u"残る行"], c23[u"未読"][u"行"]), (6, 337))
        self.assertEqual(c23[u"残る"][READ_WRONG], 0)
        self.assertEqual((c23[u"未読"][READ_OK], c23[u"未読"][READ_WRONG], c23[u"未読"][READ_UNSURE], c23[u"未読"][u"未読"]), (335, 1, 1, 0))
        self.assertEqual([(x[u"doc"], x[u"id"]) for x in r[u"L3"][u"未読の行"] if x[u"読み"] == READ_WRONG], [("S100YZ7E", "N071")])
        c4 = recount_l4(r[u"L4"][u"行"])
        self.assertEqual((c4[u"P25 通した"], c4[u"P24 通した"], c4[u"要確認に移る"]), (0, 0, 2))
        c5 = recount_l5(r[u"L5"][u"行"])
        self.assertEqual((len(c5[u"P25 の通した id"]), c5[u"P25 の行"], c5[u"P24 の行"], c5[u"VM→要確認"]), (2, 247, 247, 30))
        c6 = recount_l6(r[u"L6"][u"行"])
        self.assertEqual((c6[u"P25 G(注入)"], c6[u"P24 VM(注入)"], c6[u"VM→要確認(注入)"], len(c6[u"動いた"])), (0, 27, 1, 8))
        c7 = recount_l7(r[u"L7"][u"行"])
        self.assertEqual((c7[u"P25 G(全部)"], c7[u"P24 G(全部)"], c7[u"注入"], c7[u"有効"], c7[u"VM→PNF"]), (0, 0, 1154, 1118, 1108))
        self.assertEqual(r[u"予測の判定"]["L-9"][u"判定"], u"判定しない(段 2)")

    def test_6_engine_is_the_one_measured_or_a_declared_transition(self):
        engine_ok()
        self.assertTrue(self.rec[u"環境"][u"HEAD"].startswith(SEAL_COMMIT))

    def test_7_numstat_in_the_record_is_the_engine_diff_from_the_seal_commit(self):
        """engine が測った時点の sha のままのときだけ: 封の commit からの差分の行数が記録と一致(動いたら宣言された遷移の後なので比べない)。"""
        for rel, want in ENGINE_AT_MEASURE.items():
            if sha16(rel) != want:
                self.skipTest(u"engine が宣言された遷移の後")
        d = self.rec[u"L8"][u"engine の差分"]
        for f in ("adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py", "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py"):
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
        self.assertTrue(V.PROFILES["P25"].last_branch_names_only_if_evidence)
        self.assertFalse(V.PROFILES["P24"].last_branch_names_only_if_evidence)
        self.assertFalse(V.PROFILES["P22"].last_branch_names_only_if_evidence or V.PROFILES["P23"].last_branch_names_only_if_evidence)

    def test_9_l9_is_not_judged_and_the_seal_was_not_edited(self):
        self.assertEqual(self.rec[u"予測の判定"]["L-9"][u"判定"], u"判定しない(段 2)")
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
            self.assertEqual(sha_path(os.path.join(ROOT, rel)), inp[rel], rel)
        self.assertEqual(sha_path(os.path.join(ROOT, "fixtures/xbrl/ai_prose_instance_2026-10-09.zip")), inp[u"儀式の同梱書類"])

    def test_11_existing_red_list_is_the_closed_kinds_and_every_fix_is_named(self):
        """直す前に赤だった既存試験の一覧: 種類は封の字の中だけ(数 / state の門・人間の決定の字の門は 0)。どの行にも直しが書いてある。"""
        red = self.rec[u"L8"][u"既存試験の赤(直す前)"]
        self.assertTrue(red)
        for x in red:
            self.assertIn(x[u"種類"], ALLOWED_RED_KINDS, x)
            self.assertTrue(x[u"直し"].strip(), x)
        self.assertEqual(len({x[u"試験"] for x in red}), len(red), u"同じ試験が 2 回載っている")
        for x in self.rec[u"L8"][u"覆いの門で赤になった試験(新しい試験 file を足したため。engine と無関係)"]:
            self.assertTrue(x[u"直し"].strip(), x)

    def test_12_every_moved_row_is_one_to_one_with_its_named_fact(self):
        """動いた行 577 の全部が名指しの fact を provenance に持ち(名指しは P24 が結んでいた fact と同じ)、P25 は pointer を持たない。"""
        for x in self.rec[u"L1"][u"動いた行"]:
            self.assertEqual(x[u"P25"][u"pointers"], [])
            self.assertEqual(x[u"P24"][u"pointers"], [x[u"no_same_value"][u"named"]])


def run_script(args):
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=ROOT, capture_output=True, text=True)


def _script():
    import importlib.util
    spec = importlib.util.spec_from_file_location("lastbranch_script_for_gate", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def strip_readings(rows):
    return [dict((k, v) for k, v in r.items() if k not in (u"読み", u"根拠")) for r in rows]


class RerunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)

    def _need(self, docs):
        if not have_cache(docs):
            self.skipTest(u"cache が無い")
        if not labels_ok():
            self.skipTest(u"標準タクソノミのラベルが無い(fixtures/xbrl/TAXONOMY_LABELS_README.md)")

    def test_light_l1_matches_the_record(self):
        self._need(LIGHT_L1_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "l1.json")
            p = run_script(["--stage", "l1", "--docs", ",".join(LIGHT_L1_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)
        want = [x for x in self.rec[u"L1"][u"動いた行"] if x[u"doc"] in LIGHT_L1_DOCS]
        self.assertTrue(want)
        self.assertEqual(got[u"L1"][u"動いた行"], want)
        self.assertEqual(got[u"L1"][u"書類"], [d for d in self.rec[u"L1"][u"書類"] if d[u"doc"] in LIGHT_L1_DOCS])
        keep = [x for x in self.rec[u"L2"][u"残る行"] if x[u"doc"] in LIGHT_L1_DOCS]
        self.assertTrue(keep)
        self.assertEqual(got[u"L2"][u"残る行"], strip_readings(keep))
        unread = [x for x in self.rec[u"L3"][u"未読の行"] if x[u"doc"] in LIGHT_L1_DOCS]
        self.assertTrue(any(x[u"読み"] == READ_WRONG for x in unread))
        self.assertEqual(got[u"L3"][u"未読の行"], strip_readings(unread))

    def test_light_l4_matches_the_record(self):
        self._need(LIGHT_L4_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "l4.json")
            p = run_script(["--stage", "l4", "--docs", ",".join(LIGHT_L4_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)[u"L4"][u"行"]
        want = [r for r in self.rec[u"L4"][u"行"] if r[u"書類"] in LIGHT_L4_DOCS]
        self.assertTrue(want)
        self.assertEqual(got, want)

    def test_light_l6_matches_the_record(self):
        docs = sorted({r[u"doc"] for r in self.rec[u"L6"][u"行"]})
        self._need(docs)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "l6.json")
            p = run_script(["--stage", "l6", "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)[u"L6"]
        self.assertEqual(got[u"行"], self.rec[u"L6"][u"行"])
        self.assertEqual(got[u"集計"], self.rec[u"L6"][u"集計"])

    @unittest.skipUnless(RUN_HEAVY, u"AUDIT_CORE_LASTBRANCH=1 のときだけ走る(全部の走らせ直し。約 十五分。--run-tests は付けない)")
    def test_heavy_everything_matches_the_record(self):
        if not (have_cache(sorted(self.rec[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"])) and labels_ok()):
            self.fail(u"AUDIT_CORE_LASTBRANCH=1 なのに cache かラベルが揃っていない")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "all.json")
            p = run_script(["--stage", "all", "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)
        for sec in (u"L1", u"L4", u"L6", u"L7", u"provenance"):
            self.assertEqual(got[sec], self.rec[sec], sec)
        self.assertEqual(got[u"L2"][u"残る行"], strip_readings(self.rec[u"L2"][u"残る行"]))
        self.assertEqual(got[u"L3"][u"未読の行"], strip_readings(self.rec[u"L3"][u"未読の行"]))
        self.assertEqual(got[u"L3"][u"試作で読んだ集合"], self.rec[u"L3"][u"試作で読んだ集合"])
        a = dict((k, v) for k, v in got[u"L5"].items() if k != u"所要秒")
        b = dict((k, v) for k, v in self.rec[u"L5"].items() if k != u"所要秒")
        self.assertEqual(a, b, u"L5")
        for k in (u"書類 67(経営分析の文を持つ)の sha256", u"儀式の同梱書類", u"試作で読んだ集合の出どころ"):
            self.assertEqual(got[u"入力の sha256"][k], self.rec[u"入力の sha256"][k], k)


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
        r[u"L1"][u"動いた行"].pop()
        self._red(check_record, r)

    def test_m2_a_moved_row_that_becomes_grounded_is_seen(self):
        """動いた行が GROUNDED になったことにすると、向きの約束・集計・判定のどれかで赤。"""
        r = self._mut()
        r[u"L1"][u"動いた行"][0][u"P25"][u"state"] = "GROUNDED"
        self._red(check_record, r)
        self.assertEqual(recount_l1(r[u"L1"])[u"それ以外の向き"], 1)
        self.assertEqual(judgments(r, self.seal)["L-1"], u"外れ")

    def test_m3_change_the_value_mismatch_count_of_one_document(self):
        r = self._mut()
        for d in r[u"L1"][u"書類"]:
            if d[u"states P25"].get("VALUE_MISMATCH"):
                d[u"states P25"]["VALUE_MISMATCH"] += 7
                break
        self._red(check_record, r)

    def test_m3b_the_p24_side_must_equal_the_p24_record(self):
        """旗が偽の側(P24 の欄)を 1 つ動かすと、P24 の記録との突き合わせで赤。"""
        r = self._mut()
        r[u"L1"][u"書類"][3][u"states P24"]["GROUNDED"] = r[u"L1"][u"書類"][3][u"states P24"].get("GROUNDED", 0) + 1
        self._red(check_record, r)
        r = self._mut()
        r[u"L4"][u"行"][7][u"P24"] = dict(r[u"L4"][u"行"][7][u"P24"], **{u"state": u"GROUNDED"})
        self._red(check_record, r)
        r = self._mut()
        r[u"L5"][u"行"][5][u"P24"] = PASSED if r[u"L5"][u"行"][5][u"P24"] != PASSED else STOPPED
        self._red(check_record, r)
        r = self._mut()
        r[u"L6"][u"行"][9][u"Core 自身 P24"] = {u"state": u"GROUNDED", u"参照先": u"x"}
        self._red(check_record, r)

    def test_m4_change_a_judgment_word(self):
        r = self._mut()
        r[u"予測の判定"]["L-1"][u"判定"] = u"外れ"
        self._red(check_judgments, r, self.seal)

    def test_m5_a_pointer_on_a_no_same_value_row_is_red(self):
        """no_same_value は pointer なし。名指しを pointer に付けると赤(名指しは provenance だけ)。"""
        r = self._mut()
        x = r[u"L1"][u"動いた行"][0]
        x[u"P25"][u"pointers"] = [x[u"no_same_value"][u"named"]]
        self._red(check_record, r)

    def test_m6_a_p25_pass_in_the_hole_b_is_seen(self):
        r = self._mut()
        x = r[u"L4"][u"行"][0]
        x[u"P25"] = dict(x[u"P25"], **{u"結果": u"通した(参照先が前期へ移った)"})
        self._red(check_record, r)
        self.assertEqual(judgments(r, self.seal)["L-4"], u"外れ")

    def test_m7_a_p25_pass_in_the_ritual_moves_the_judgment(self):
        r = self._mut()
        n = 0
        for x in r[u"L5"][u"行"]:
            if x[u"P25"] == STOPPED and n < 2:
                x[u"P25"] = PASSED
                n += 1
        self.assertEqual(judgments(r, self.seal)["L-5"], u"外れ")
        self._red(check_record, r)

    def test_m8_the_ritual_to_check_count_moves_the_judgment(self):
        r = self._mut()
        n = 0
        for x in r[u"L5"][u"行"]:
            if x[u"P25"] == TO_CHECK and x[u"P24"] == STOPPED and n < 10:
                x[u"P25"] = STOPPED
                n += 1
        self.assertEqual(judgments(r, self.seal)["L-5"], u"外れ")

    def test_m9_a_grounded_injection_in_l7_is_a_miss(self):
        r = self._mut()
        for x in r[u"L7"][u"行"]:
            if x.get(u"変え方"):
                x[u"P25"] = {u"state": "GROUNDED", u"reason": None, u"pointers": [], u"recomputed": None}
                break
        self.assertEqual(judgments(r, self.seal)["L-7"], u"外れ")
        self._red(check_record, r)

    def test_m10_a_grounded_injection_in_l6_is_a_miss(self):
        r = self._mut()
        for x in r[u"L6"][u"行"]:
            if x[u"注入か"]:
                x[u"Core 自身 P25"] = {u"state": "GROUNDED", u"参照先": u"x"}
                break
        self.assertEqual(judgments(r, self.seal)["L-6"], u"外れ")
        self._red(check_record, r)

    def test_m11_a_reading_that_loses_its_row_is_red(self):
        """読みの行が足りない・余る・別の行のものになる・語が違う・根拠が空、のどれも赤。"""
        r = self._mut()
        r[u"L3"][u"未読の行"].pop()
        self._red(check_record, r)
        r = self._mut()
        r[u"L3"][u"未読の行"][0][u"id"] = u"N999"
        self._red(check_record, r)
        r = self._mut()
        r[u"L3"][u"未読の行"][0][u"読み"] = u"偽"
        self._red(check_record, r)
        r = self._mut()
        r[u"L3"][u"未読の行"][0][u"根拠"] = u" "
        self._red(check_record, r)
        r = self._mut()
        r[u"L2"][u"残る行"][0][u"読み"] = None
        self._red(check_record, r)
        r = self._mut()
        r[u"L2"][u"残る行"].pop()
        self._red(check_record, r)

    def test_m12_the_proto_set_must_be_the_pinned_one(self):
        r = self._mut()
        r[u"L3"][u"試作で読んだ集合"][u"一覧"].pop()
        self._red(check_record, r)
        r = self._mut()
        r[u"L3"][u"試作で読んだ集合"][u"一覧"][0] = u"S100YUHC N999"
        self._red(check_record, r)

    def test_m13_too_many_wrong_readings_make_l3_a_miss(self):
        r = self._mut()
        n = 0
        for x in r[u"L3"][u"未読の行"]:
            if x[u"読み"] == READ_OK and n < 6:
                x[u"読み"] = READ_WRONG
                n += 1
        self.assertEqual(judgments(r, self.seal)["L-3"], u"外れ")        # 7 / 337 = 2.1% > 2%
        r = self._mut()
        n = 0
        for x in r[u"L3"][u"未読の行"]:
            if x[u"読み"] == READ_OK and n < 5:
                x[u"読み"] = READ_WRONG
                n += 1
        self.assertEqual(judgments(r, self.seal)["L-3"], u"当たり")      # 6 / 337 = 1.8% <= 2%(境目)

    def test_m14_two_wrong_readings_in_the_kept_rows_make_l2_a_miss(self):
        r = self._mut()
        for x in r[u"L2"][u"残る行"][:2]:
            x[u"読み"] = READ_WRONG
        self.assertEqual(judgments(r, self.seal)["L-2"], u"外れ")
        r = self._mut()
        r[u"L2"][u"残る行"][0][u"読み"] = None
        self.assertEqual(judgments(r, self.seal)["L-2"], u"読み待ち")

    def test_m15_a_number_in_a_document_table_is_red(self):
        for blk in ("L-1 の数", "L-1 の state の表", "L-4 の表", "L-5 の表", "L-6 の表", "L-7 の表", "L-3 の読みの表"):
            v = render_blocks(self.rec)[blk]
            i = re.search(r"\d", v).start()
            bad = self.doc.replace(v, v[:i] + (u"9" if v[i] != u"9" else u"8") + v[i + 1:], 1)
            self.assertNotEqual(bad, self.doc)
            self._red(check_doc, self.rec, bad)

    def test_m16_a_number_in_a_prose_sentence_is_red(self):
        for k, v in prose_facts(self.rec).items():
            m = re.search(r"\d", v)
            if not m:
                continue
            bad = self.doc.replace(v, v[:m.start()] + (u"9" if v[m.start()] != u"9" else u"8") + v[m.start() + 1:], 1)
            self.assertNotEqual(bad, self.doc, k)
            self._red(check_doc, self.rec, bad)

    def test_m17_a_new_unbound_number_in_prose_is_red(self):
        bad = self.doc + u"\n\nなお、書類のうち 99 件は別の扱いになった。\n"
        self._red(check_doc, self.rec, bad)

    def test_m18_a_spoiled_input_digest_is_red(self):
        r = self._mut()
        k = sorted(r[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"])[3]
        r[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"][k] = u"0" * 64
        self._red(check_inputs, r)
        r = self._mut()
        r[u"入力の sha256"]["fixtures/xbrl/vocab_2026-10-21.json"] = u"0" * 64
        self._red(check_inputs, r)

    def test_m19_mutation_record_must_have_five_rows(self):
        r = self._mut()
        r[u"変異(engine。手で走らせた)"][u"表"] = r[u"変異(engine。手で走らせた)"][u"表"][:4]
        self._red(check_mutation_record, r)

    def test_m20_a_wrong_engine_sha_is_red(self):
        global ENGINE_AT_MEASURE, ENGINE_LATER
        old, old_later = dict(ENGINE_AT_MEASURE), dict(ENGINE_LATER)
        try:
            for rel in sorted(old):
                if rel == "adapters/xbrl/comparators.py":
                    continue
                # 2026-10-22: 遷移が宣言されている file は、宣言された後の sha を取り違えたときに赤(測った時点の sha は遷移で見ないので)
                if rel in old_later:
                    ENGINE_LATER = dict(old_later, **{rel: ("0" * 16, old_later[rel][1])})
                    self._red(engine_ok)
                ENGINE_LATER = {}
                ENGINE_AT_MEASURE = dict(old, **{rel: "0" * 16})
                self._red(engine_ok)
                ENGINE_AT_MEASURE = dict(old)
        finally:
            ENGINE_AT_MEASURE, ENGINE_LATER = old, old_later
        engine_ok()

    def test_m21_an_existing_red_of_a_forbidden_kind_makes_l8_a_miss(self):
        r = self._mut()
        r[u"L8"][u"既存試験の赤(直す前)"].append({u"試験": u"tests/measure/x.py::T::t", u"種類": u"数 / state の門", u"直し": u"x"})
        self.assertEqual(judgments(r, self.seal)["L-8"], u"外れ")

    def test_m22_a_deletion_in_recipes_or_a_failed_existing_run_makes_l8_a_miss(self):
        r = self._mut()
        r[u"L8"][u"engine の差分"]["adapters/xbrl/recipes.py"][u"削除"] = 1
        self.assertEqual(judgments(r, self.seal)["L-8"], u"外れ")
        r = self._mut()
        r[u"L8"][u"既存試験"][0][u"rc"] = 1
        self.assertEqual(judgments(r, self.seal)["L-8"], u"外れ")
        r = self._mut()
        r[u"L8"][u"engine の差分"]["core/"][u"差の行数"] = 1
        self.assertEqual(judgments(r, self.seal)["L-8"], u"外れ")

    def test_m23_the_flag_made_identity_turns_l1_red(self):
        """旗を恒等(偽)にすると、動いた行が消える(L-1 の再計算が記録と食い違う)。engine の file は書き換えない(in-process で P25 の旗を偽にして、出るとき必ず戻す)。"""
        if not (have_cache(LIGHT_L1_DOCS) and labels_ok()):
            self.skipTest(u"cache かラベルが無い")
        import dataclasses
        m = _script()
        from adapters.xbrl import vocabulary as V
        want = [x for x in self.rec[u"L1"][u"動いた行"] if x[u"doc"] in LIGHT_L1_DOCS]
        self.assertTrue(want)
        old = V.PROFILES["P25"]
        V.PROFILES["P25"] = dataclasses.replace(old, last_branch_names_only_if_evidence=False)
        try:
            moved = []
            for d in LIGHT_L1_DOCS:
                with io.open(os.path.join(CACHE, d + ".zip"), "rb") as fh:
                    zb = fh.read()
                moved.extend(m.plain_doc(d, zb)[1])
        finally:
            V.PROFILES["P25"] = old
        self.assertIs(V.PROFILES["P25"], old)
        self.assertEqual(moved, [])


if __name__ == "__main__":
    unittest.main()
