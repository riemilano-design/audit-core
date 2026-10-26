# -*- coding: utf-8 -*-
u"""「違う」に出る正しい文の主因を減らす P26 の段 1 の結果 ― 封 docs/XBRL_P26_SEAL_2026-10-21.md §2(Q-1〜Q-8)の結果を縛る門。

記録: ``fixtures/xbrl/p26_2026-10-21.json``(``measure/xbrl_p26_2026-10-21.py --stage all --readings … --mutations … --existing-red … --out …`` の出力)。
文書: ``docs/XBRL_P26_RESULT_2026-10-21.md``。

この門がやること(どれも、壊した標本で赤くなることを ``MutationTest`` が毎回確かめる):
  1. 入力(書類 67 本・67 の外 214 本の sha256・他の記録の sha256)を**字で留めた digest / sha256** に縛る。cache が在る機械では実物の sha256 も記録と一致させる。
  2. 記録の行(Q-1 の動いた行と書類別・Q-2 の読み・Q-3 の穴 B / 儀式 / 段 2・Q-4 と Q-5 の注入・Q-7 の書類別)から、集計・向きを
     **script の関数を使わずに** 数え直し、記録の集計と一致させる。旗が偽の側(P25)は、P25 の記録 ``lastbranch_2026-10-21.json`` の同じ数と突き合わせる。
  3. **読みと行の 1 対 1**: Q-2 の読みの行 = 動いた行のうち P25 が VALUE_MISMATCH で P26 がそうでない行、Q-2b = P25 が GROUNDED で P26 が GROUNDED でない行。
     どの行にも読みの語と根拠が付いていること。**読みの中身の正しさは門で縛れない**(エージェントの読み。縛るのは行と読みの対応と、数と、判定の算術だけ)。
  4. 予測 Q-1〜Q-8 の判定を、封の字から読んだ幅と記録の行から**門が自分で**求め、記録の判定と文書の表と一致させる。
  5. 文書の表・数のある文を記録から作った字と完全一致させる。それ以外の散文に算用数字が在れば ``residual_numbers`` が見つけて赤にする(コード片・識別子・日付・節の番号は除く)。散文は漢数字で書く。
  6. engine の sha(測った時点の extract.py・vocabulary.py・recipes.py・registry_setup.py・report_customer.py・comparators.py)を字で留め、いまの engine が同じか宣言された遷移であること
     (遷移の表の名前は ``ENGINE_TRANSITIONS``。P25 の封の門 test_10 が行頭の ``ENGINE_LATER = {`` を数えるので、この門はその名前を使わない)。
     ``core/``・``report.py``・``verify_document.py`` が封の commit から 0 行であること。``DEFAULT_PROFILE`` が P22 のままであること(段 1)。封が封の commit から 1 字も変わっていないこと。
  7. cache とラベルが在る機械では、軽い走らせ直し(Q-1 を 2 書類)を script で走らせて記録の該当行と一致。全部の走らせ直し(約 二十分)は ``AUDIT_CORE_P26=1`` のときだけ。
縛っていないもの: 読みの中身の正しさ(上の 3.)、限界の文の主張の中身、変異(engine)の手の実測そのもの(表は記録の写しを縛るだけ)、
  tests/measure 全体の所要、漢数字で書いた数(``residual_numbers`` は算用数字だけを探す。散文の数は記録から作った字で縛る約束)。
"""
import copy
import dataclasses
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
REC = os.path.join(ROOT, "fixtures", "xbrl", "p26_2026-10-21.json")
DOC = os.path.join(ROOT, "docs", "XBRL_P26_RESULT_2026-10-21.md")
SEAL_REL = "docs/XBRL_P26_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SEAL_COMMIT = "a8d8099"
SCRIPT = os.path.join(ROOT, "measure", "xbrl_p26_2026-10-21.py")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
RUN_HEAVY = os.environ.get("AUDIT_CORE_P26") == "1"
LASTBRANCH_REC = os.path.join(ROOT, "fixtures", "xbrl", "lastbranch_2026-10-21.json")
LIGHT_DOCS = ("S100Z5CH", "S100YZ7E")       # 動いた行(丸めた差の N051・N071、概念・語の行 N050)が在る書類
READ_OK, READ_WRONG, READ_UNSURE = u"正しい文", u"文が本当に違う", u"分からない"
READ_COINCIDENCE, READ_LOST = u"偶然の一致", u"正しい結びを失った"
READ_WORDS = (READ_OK, READ_WRONG, READ_UNSURE)
READ_WORDS_2B = (READ_COINCIDENCE, READ_LOST, READ_UNSURE)
REASON_CONCEPT, REASON_DIR, REASON_HOLD = "other_concept", "direction_on_cause_item", "rounded_diff_within_double_band"
THREE_REASONS = (REASON_CONCEPT, REASON_DIR, REASON_HOLD)

#: **字で留める**(記録の値の写し。定数から作らない)。
DOCS67_DIGEST = "118ec1015494db404b74dbd65b72bddfd2356459749d6f10dc910e5a1348429f"       # 書類 67 本の docID\tsha256 を sorted で \n 結合した sha256
DOCS214_DIGEST = "1b36b8f77e878429976f46b2fcf377bbe76ecb42343fcfd4a22a826e015b23af"      # 67 の外 214 本の同じ形の sha256
INPUT_SHAS = {
    "fixtures/xbrl/lastbranch_2026-10-21.json": "a49ef3a6d18748b95d5d4786e7276d91c9c7ad9d10b776bfb58500fd96044cfd",
    "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json": "c3068024ff8c2812fabbf54e36f50b1cedeccb7955e9455603d1a17018418149",
    "fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json": "3b13d26f81906ae47696c95c2c0e21322579bcdabcde3a133b5a96970e7c52f6",
}
RITUAL_ZIP_SHA = "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799"
#: 測った時点の engine(sha256 の先頭 16 桁)。comparators.py は 0 行(封 §1 は comparators.py に触らない)。
ENGINE_AT_MEASURE = {"adapters/xbrl/extract.py": "9982599fc31cbab3", "adapters/xbrl/vocabulary.py": "83025e9c0525d08b", "adapters/xbrl/recipes.py": "181b370420ab751b",
                     "adapters/xbrl/registry_setup.py": "7f2cbded9c830211", "adapters/xbrl/report_customer.py": "141767d189b63733",
                     "adapters/xbrl/comparators.py": "d8706338325e725b"}
#: 段 2(既定の切り替え)などで動いたときの宣言された遷移: {path: (後の sha16, 遷移を宣言した封の path)}。段 1 の commit 時点では空。
#: 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md が宣言した遷移。vocabulary.py は DEFAULT_PROFILE の 1 行と決定の注記(+4 行・-1 行)だけ動いた。
#: 83025e9c0525d08b(P26 の段 1。ENGINE_AT_MEASURE に残す = 測った時点の値)から段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"
ENGINE_TRANSITIONS = {"adapters/xbrl/vocabulary.py": ("e28733067b1f17f5", SEAL_DEFAULT_P26)}
#: 封の commit から 0 行でなければならない file(core/ は別に見る)。
UNTOUCHED = ("adapters/xbrl/report.py", "adapters/xbrl/verify_document.py", "adapters/xbrl/comparators.py")


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


def key(r):
    return (r[u"doc"], r[u"id"])


def way(r):
    u"""動いた行の向きの字(``STATE(reason) → STATE(reason)``)。script の字と同じ書き方で門が作る。"""
    return u"%s(%s) → %s(%s)" % (r[u"P25"][u"state"], r[u"P25"][u"reason"], r[u"P26"][u"state"], r[u"P26"][u"reason"])


PASSED = "PASSED"
STOPPED = "detected:VALUE_MISMATCH"
TO_CHECK = "detected:POINTER_NOT_FOUND"


# ----------------------------------------------------------------------------------------------------------------
# 独立の数え直し(script の関数を使わない)
def recount_q1(rec):
    q = rec[u"Q1"]
    mv, docs = q[u"動いた行"], q[u"書類"]
    S = lambda r, side: r[side][u"state"]
    st = lambda side, s: sum(d[u"states " + side].get(s, 0) for d in docs)
    return {u"書類数": len(docs), u"claims": sum(d[u"claims"] for d in docs), u"動いた": len(mv), u"動いた(書類別)": sum(d[u"動いた"] for d in docs),
            u"G25": st(u"P25", "GROUNDED"), u"VM25": st(u"P25", "VALUE_MISMATCH"), u"UNV25": st(u"P25", "UNVERIFIABLE"), u"PNF25": st(u"P25", "POINTER_NOT_FOUND"),
            u"G26": st(u"P26", "GROUNDED"), u"VM26": st(u"P26", "VALUE_MISMATCH"), u"UNV26": st(u"P26", "UNVERIFIABLE"), u"PNF26": st(u"P26", "POINTER_NOT_FOUND"),
            u"新しい GROUNDED": sum(1 for r in mv if S(r, u"P26") == "GROUNDED" and S(r, u"P25") != "GROUNDED"),
            u"GROUNDED から外れた": sum(1 for r in mv if S(r, u"P25") == "GROUNDED" and S(r, u"P26") != "GROUNDED"),
            u"違うから外れた": sum(1 for r in mv if S(r, u"P25") == "VALUE_MISMATCH" and S(r, u"P26") != "VALUE_MISMATCH"),
            u"読みだけ": sum(1 for r in mv if r[u"読みが変わった"] and (r[u"P25"][u"state"], r[u"P25"][u"reason"]) == (r[u"P26"][u"state"], r[u"P26"][u"reason"])),
            u"向き": dict((k, sum(1 for r in mv if way(r) == k)) for k in sorted({way(r) for r in mv})),
            u"三つの理由に動いた": sum(1 for r in mv if r[u"P26"][u"reason"] in THREE_REASONS and r[u"P25"][u"reason"] != r[u"P26"][u"reason"]),
            u"理由別": dict((k, sum(1 for r in mv if r[u"P26"][u"reason"] == k and r[u"P25"][u"reason"] != k)) for k in THREE_REASONS)}


def read_rows(rec):
    u"""Q-2 の行 = 動いた行のうち P25 が VM で P26 が VM でない、Q-2b = P25 が G で P26 が G でない。"""
    mv = rec[u"Q1"][u"動いた行"]
    q2 = [r for r in mv if r[u"P25"][u"state"] == "VALUE_MISMATCH" and r[u"P26"][u"state"] != "VALUE_MISMATCH"]
    q2b = [r for r in mv if r[u"P25"][u"state"] == "GROUNDED" and r[u"P26"][u"state"] != "GROUNDED"]
    return q2, q2b


def recount_readings(rows, words):
    c = {}
    for r in rows:
        c[r.get(u"読み")] = c.get(r.get(u"読み"), 0) + 1
    out = dict((w, c.get(w, 0)) for w in words)
    out[u"行"], out[u"未読"] = len(rows), c.get(None, 0)
    return out


def recount_q3(rec):
    q = rec[u"Q3"]
    hb = q[u"穴 B"][u"行"]
    rit = q[u"儀式"][u"行"]
    s2 = q[u"段 2"][u"行"]
    inj = [r for r in s2 if r[u"注入か"]]
    passed = lambda s: s.startswith(u"通した")
    both = [r for r in rit if r[u"P25"] is not None and r[u"P26"] is not None]
    return {u"穴 B": len(hb), u"穴 B P26 通した": sum(1 for r in hb if passed(r[u"P26"][u"結果"])), u"穴 B P25 通した": sum(1 for r in hb if passed(r[u"P25"][u"結果"])),
            u"穴 B P25 止めた": sum(1 for r in hb if r[u"P25"][u"state"] == "VALUE_MISMATCH"),
            u"穴 B 要確認に移る": sum(1 for r in hb if r[u"P25"][u"state"] == "VALUE_MISMATCH" and r[u"P26"][u"state"] in ("POINTER_NOT_FOUND", "UNVERIFIABLE")),
            u"儀式 P26 の行": sum(1 for r in rit if r[u"P26"] is not None), u"儀式 P25 の行": sum(1 for r in rit if r[u"P25"] is not None), u"儀式 共通": len(both),
            u"儀式 P26 通した id": [r[u"id"] for r in rit if r[u"P26"] == PASSED], u"儀式 P25 通した id": [r[u"id"] for r in rit if r[u"P25"] == PASSED],
            u"儀式 VM→要確認": sum(1 for r in both if r[u"P25"] == STOPPED and r[u"P26"] == TO_CHECK),
            u"儀式 共通で結果が違う": sum(1 for r in both if r[u"P25"] != r[u"P26"]),
            u"段 2 行": len(s2), u"段 2 注入": len(inj), u"段 2 注入 P26 G": sum(1 for r in inj if r[u"Core 自身 P26"][u"state"] == "GROUNDED"),
            u"段 2 注入 P25 G": sum(1 for r in inj if r[u"Core 自身 P25"][u"state"] == "GROUNDED"),
            u"段 2 動いた": sorted(u"%s %s" % (r[u"doc"], r[u"id"]) for r in s2 if r[u"Core 自身 P25"] != r[u"Core 自身 P26"]),
            u"段 2 注入の VM→要確認": sum(1 for r in inj if r[u"Core 自身 P25"][u"state"] == "VALUE_MISMATCH" and r[u"Core 自身 P26"][u"state"] in ("POINTER_NOT_FOUND", "UNVERIFIABLE"))}


def recount_q4(rows):
    done = [x for x in rows if x.get(u"変え方")]                       # 注入を作れなかった行は 変え方 が None で P25・P26 の欄が無い
    valid = [x for x in done if x[u"P25"].get(u"state") is not None and x[u"P26"].get(u"state") is not None]
    st = lambda x, p: x[p].get(u"state")
    return {u"行": len({(x[u"doc"], x[u"id"]) for x in rows}), u"注入": len(done), u"有効": len(valid), u"有効でない": len(done) - len(valid),
            u"P26 G(全部)": sum(1 for x in done if st(x, u"P26") == "GROUNDED"), u"P25 G(全部)": sum(1 for x in done if st(x, u"P25") == "GROUNDED"),
            u"有効 P26": dict((k, sum(1 for x in valid if st(x, u"P26") == k)) for k in sorted({st(x, u"P26") for x in valid})),
            u"VM→要確認": sum(1 for x in valid if st(x, u"P25") == "VALUE_MISMATCH" and st(x, u"P26") in ("POINTER_NOT_FOUND", "UNVERIFIABLE"))}


def recount_q5(rows):
    done = [x for x in rows if x.get(u"変え方")]
    valid = [x for x in done if x[u"P25"].get(u"state") is not None and x[u"P26"].get(u"state") is not None]
    st = lambda x, p: x[p].get(u"state")
    return {u"行": len({(x[u"doc"], x[u"id"]) for x in rows}), u"注入": len(done), u"有効": len(valid),
            u"新しい GROUNDED": sum(1 for x in valid if st(x, u"P25") != "GROUNDED" and st(x, u"P26") == "GROUNDED"),
            u"両方 GROUNDED": sum(1 for x in valid if st(x, u"P25") == "GROUNDED" and st(x, u"P26") == "GROUNDED"),
            u"P25 が止めた": sum(1 for x in valid if st(x, u"P25") == "VALUE_MISMATCH"),
            u"P25 が通さなかった": sum(1 for x in valid if st(x, u"P25") != "GROUNDED"),
            u"VM→要確認": sum(1 for x in valid if st(x, u"P25") == "VALUE_MISMATCH" and st(x, u"P26") in ("POINTER_NOT_FOUND", "UNVERIFIABLE"))}


def recount_q7(rec):
    q = rec[u"Q7"]
    docs = q[u"書類別"]
    return {u"書類": len(docs), u"違う(節)": sum(d[u"違う(節の件数)"] for d in docs), u"VM(state)": sum(d[u"VALUE_MISMATCH(state)"] for d in docs),
            u"書類ごとに一致": all(d[u"違う(節の件数)"] == d[u"VALUE_MISMATCH(state)"] for d in docs), u"claims": sum(d[u"claims"] for d in docs),
            u"節の合計が claim": all(d[u"違う(節の件数)"] + d[u"要確認(節の件数)"] + d[u"一致(節の件数)"] + d[u"対象外"] + d[u"判断しない"] == d[u"claims"] for d in docs)}


def check_readings(rec):
    q2, q2b = read_rows(rec)
    for part, rows, words, want in ((u"Q2", rec[u"Q2"][u"行"], READ_WORDS, q2), (u"Q2b", rec[u"Q2b"][u"行"], READ_WORDS_2B, q2b)):
        assert sorted(key(r) for r in rows) == sorted(key(r) for r in want), u"%s の行が『動いた行から求めた行』と 1 対 1 でない" % part
        assert len({key(r) for r in rows}) == len(rows), u"%s に重複" % part
        for r in rows:
            assert r[u"読み"] in words and r[u"根拠"].strip(), (part, key(r))
    mine = dict((key(r), r) for r in rec[u"Q1"][u"動いた行"])
    for r in rec[u"Q2"][u"行"] + rec[u"Q2b"][u"行"]:
        m = mine[key(r)]
        assert r[u"P25"] == m[u"P25"] and r[u"P26"] == m[u"P26"], key(r)


def check_record(rec):
    u"""記録の集計を、行から数え直した値と突き合わせる。壊した記録で赤くなる。"""
    lb = jload(LASTBRANCH_REC)
    c = recount_q1(rec)
    s = rec[u"Q1"][u"集計"]
    assert c[u"動いた"] == c[u"動いた(書類別)"] == s[u"動いた(全 state)"], u"動いた"
    assert c[u"書類数"] == s[u"書類数"] == 67 == rec[u"書類の数"][u"経営分析の文を持つ"] and c[u"claims"] == s[u"総 claim"], u"書類数・claim"
    for k, a, b in ((u"GROUNDED", u"G25", u"G26"), (u"VALUE_MISMATCH", u"VM25", u"VM26"), (u"UNVERIFIABLE", u"UNV25", u"UNV26"), (u"POINTER_NOT_FOUND", u"PNF25", u"PNF26")):
        assert s[u"%s の合計 P25" % k] == c[a] and s[u"%s の合計 P26" % k] == c[b], k
    assert s[u"新しい GROUNDED(P25 が GROUNDED でなく P26 が GROUNDED)"] == c[u"新しい GROUNDED"]
    assert s[u"GROUNDED から外れた行(P25 が GROUNDED で P26 が GROUNDED でない)"] == c[u"GROUNDED から外れた"]
    assert s[u"「違う」から外れた行(P25 が VALUE_MISMATCH で P26 が違う)"] == c[u"違うから外れた"]
    assert s[u"読みだけ変わった行(G5)"] == c[u"読みだけ"] == len(rec[u"Q1"][u"読みが変わった行"]) == s[u"読みが変わった行(全部)"], u"読みだけ変わった行"
    assert s[u"向き(全部)"] == c[u"向き"] and sum(c[u"向き"].values()) == c[u"動いた"], u"向き"
    # 対照: P25 の書類別の state が P25 の記録(lastbranch)と一致 = 旗が偽の側は動いていない
    ld = dict((d[u"doc"], d) for d in lb[u"L1"][u"書類"])
    for d in rec[u"Q1"][u"書類"]:
        assert ld[d[u"doc"]][u"states P25"] == d[u"states P25"] and ld[d[u"doc"]][u"claims"] == d[u"claims"], d[u"doc"]
    # provenance: 三つの理由の Recipe の数 = 動いた行の数、名指しは全部 provenance に
    pv = rec[u"provenance"]
    for r in THREE_REASONS:
        assert pv[u"%s の Recipe" % r] == c[u"理由別"][r], r                                  # 動いた行の数 = Recipe の数
    for r in THREE_REASONS:
        n = pv[u"%s の Recipe" % r]
        has = pv[u"provenance に名指しあり"] if r == REASON_CONCEPT else pv[u"%s の provenance あり" % r]
        assert has == n, (r, has, n)                                                          # 名指し(形・fact)は全部 provenance にある
    # 読み
    check_readings(rec)
    q2, q2b = read_rows(rec)
    assert len(q2) == c[u"違うから外れた"] and len(q2b) == c[u"GROUNDED から外れた"]
    # Q-3
    c3 = recount_q3(rec)
    hb = rec[u"Q3"][u"穴 B"][u"集計"]
    assert c3[u"穴 B"] == 485 == hb[u"注入"] == sum(p[u"作れた"] for p in rec[u"Q3"][u"穴 B"][u"書類別"]), u"穴 B の注入"
    assert hb[u"P26 で通した(GROUNDED のまま)"][u"件"] == c3[u"穴 B P26 通した"] and hb[u"P25(対照)で通した"][u"件"] == c3[u"穴 B P25 通した"]
    assert hb[u"P25 の止め"][u"件"] == c3[u"穴 B P25 止めた"] and hb[u"止め(P25 の VALUE_MISMATCH)のうち要確認(POINTER_NOT_FOUND か UNVERIFIABLE)に移る"][u"件"] == c3[u"穴 B 要確認に移る"]
    assert hb[u"止め(P25 の VALUE_MISMATCH)のうち要確認(POINTER_NOT_FOUND か UNVERIFIABLE)に移る"][u"分母"] == c3[u"穴 B P25 止めた"]
    assert len(hb[u"要確認に移る行"]) == c3[u"穴 B 要確認に移る"]
    lh = dict(((r[u"書類"], r[u"id"]), r[u"P25"]) for r in lb[u"L4"][u"行"])
    for r in rec[u"Q3"][u"穴 B"][u"行"]:
        w = lh[(r[u"書類"], r[u"id"])]
        assert (w[u"結果"], w[u"state"], w[u"reason"], w[u"pointers"]) == (r[u"P25"][u"結果"], r[u"P25"][u"state"], r[u"P25"][u"reason"], r[u"P25"][u"pointers"]), (r[u"書類"], r[u"id"])
    rt = rec[u"Q3"][u"儀式"]
    assert rt[u"通した P26"][u"件"] == len(c3[u"儀式 P26 通した id"]) and rt[u"通した P26"][u"分母"] == c3[u"儀式 P26 の行"] == rt[u"P26 の行数"]
    assert rt[u"通した P25(対照)"][u"件"] == len(c3[u"儀式 P25 通した id"]) and rt[u"通した P25(対照)"][u"分母"] == c3[u"儀式 P25 の行"] == rt[u"P25 の行数"]
    assert [x[u"id"] for x in rt[u"通した P26 の一覧"]] == c3[u"儀式 P26 通した id"]
    assert rt[u"集計"][u"注入の止めが要確認に移った(共通の行)"] == c3[u"儀式 VM→要確認"] and rt[u"集計"][u"共通の行"] == c3[u"儀式 共通"]
    assert rt[u"集計"][u"共通の行で結果が違う行"] == c3[u"儀式 共通で結果が違う"] == c3[u"儀式 VM→要確認"], u"結果が変わった共通の行は全部 VM → 要確認"
    assert rt[u"集計"][u"P25 だけに在る行"] == c3[u"儀式 P25 の行"] - c3[u"儀式 共通"] and rt[u"集計"][u"P26 だけに在る行"] == c3[u"儀式 P26 の行"] - c3[u"儀式 共通"] == 0
    hand = rt[u"手で当てた(P26 の表から消えた行)"]
    assert rt[u"集計"][u"手で当てた行"] == len(hand) == rt[u"集計"][u"P25 だけに在る行"], u"手で当てた行 = P26 の表から消えた行"
    assert rt[u"集計"][u"手で当てて通した"] == 0 and sum(rt[u"集計"][u"手で当てた結果"].values()) == len(hand), u"手で当てて通した行は 0"
    lr = dict(((x[u"id"], x[u"型"]), x[u"P25"]) for x in lb[u"L5"][u"行"] if x[u"P25"] is not None)
    gr = dict(((r[u"id"], r[u"型"]), r[u"P25"]) for r in rec[u"Q3"][u"儀式"][u"行"] if r[u"P25"] is not None)
    assert lr == gr, u"P25 の欄が P25 の記録の儀式と違う(旗が偽の側が動いている)"
    s2 = rec[u"Q3"][u"段 2"][u"集計"]
    assert c3[u"段 2 行"] == 192 == s2[u"行"] and c3[u"段 2 注入"] == 64 == s2[u"注入"]
    assert s2[u"Core 自身が P25 → P26 で動いた行"] == len(c3[u"段 2 動いた"]) and sorted(s2[u"動いた行の id"]) == c3[u"段 2 動いた"]
    assert s2[u"全注入で Core 自身 P26 が GROUNDED"][u"件"] == c3[u"段 2 注入 P26 G"] and s2[u"全注入で Core 自身 P25 が GROUNDED"][u"件"] == c3[u"段 2 注入 P25 G"]
    assert s2[u"注入の止めのうち要確認に移る"] == c3[u"段 2 注入の VM→要確認"]
    ls2 = dict(((r[u"doc"], r[u"id"]), r[u"Core 自身 P25"]) for r in lb[u"L6"][u"行"])
    for r in rec[u"Q3"][u"段 2"][u"行"]:
        assert ls2[(r[u"doc"], r[u"id"])] == r[u"Core 自身 P25"], (r[u"doc"], r[u"id"])        # 対照
    # Q-4・Q-5
    c4 = recount_q4(rec[u"Q4"][u"行"])
    s4 = rec[u"Q4"][u"集計"]
    assert s4[u"対象の行(P25 → P26 に動いた行)"] == c4[u"行"] == c[u"動いた"], u"Q-4 の対象の行"
    assert (s4[u"注入の数"], s4[u"有効な注入"], s4[u"有効でない注入(主張が見つからない・値がずれた)"]) == (c4[u"注入"], c4[u"有効"], c4[u"有効でない"])
    made = {(x[u"doc"], x[u"id"]) for x in rec[u"Q4"][u"行"] if x.get(u"変え方")}
    assert s4[u"作れなかった"] == c4[u"行"] - len(made) and 2 * len(made) == c4[u"注入"], u"作れなかった(作れた行は 2 型 = 注入 2 回、作れなかった行は 1 行)"
    assert (s4[u"P26 で GROUNDED(全部の注入)"], s4[u"P25(対照)で GROUNDED(全部の注入)"]) == (c4[u"P26 G(全部)"], c4[u"P25 G(全部)"])
    assert s4[u"有効な注入の P26"] == c4[u"有効 P26"]
    assert s4[u"P25 で VALUE_MISMATCH(違う)が P26 で要確認(POINTER_NOT_FOUND か UNVERIFIABLE)に移った有効な注入"] == c4[u"VM→要確認"]
    assert len(s4[u"P26 で GROUNDED の行"]) == c4[u"P26 G(全部)"]
    c5 = recount_q5(rec[u"Q5"][u"行"])
    s5 = rec[u"Q5"][u"集計"]
    assert (s5[u"対象の行(P25 で GROUNDED の差の主張)"], s5[u"注入"], s5[u"有効"]) == (c5[u"行"], c5[u"注入"], c5[u"有効"])
    assert s5[u"新しい GROUNDED(P25 が止めて P26 が GROUNDED にした)"] == c5[u"新しい GROUNDED"] and len(s5[u"新しい GROUNDED の行"]) == c5[u"新しい GROUNDED"]
    assert s5[u"P25 も P26 も GROUNDED にした注入(数えない)"] == c5[u"両方 GROUNDED"] and s5[u"P25 が止めた注入"] == c5[u"P25 が通さなかった"]      # script の『止めた』は P25 が GROUNDED にしなかった注入(VALUE_MISMATCH 以外も含む)
    assert s5[u"P25 の止め(VALUE_MISMATCH)が P26 で要確認に移った注入"] == c5[u"VM→要確認"]
    # Q-7
    c7 = recount_q7(rec)
    q7 = rec[u"Q7"]
    assert q7[u"違う(節)の合計"] == c7[u"違う(節)"] and q7[u"VALUE_MISMATCH(state)の合計"] == c7[u"VM(state)"] and c7[u"節の合計が claim"], u"Q-7 の合計"
    assert c7[u"VM(state)"] == c[u"VM26"], u"Q-7 の VALUE_MISMATCH は Q-1 の P26 の合計と同じ(同じ 67 書類を P26 明示で)"
    assert q7[u"登録簿の理由"][u"合計"] == q7[u"登録簿の理由"][u"POINTER_NOT_FOUND"] + q7[u"登録簿の理由"][u"UNVERIFIABLE"]
    assert sorted(q7[u"登録簿の理由"][u"3 つの理由が登録簿にある"]) == sorted(THREE_REASONS)
    # 環境
    env = rec[u"環境"]
    assert env[u"比べた profile"] == ["P25", "P26"] and env[u"費用"] == u"0 USD" and env[u"DEFAULT_PROFILE"] == "P22"
    for rel, want in ENGINE_AT_MEASURE.items():
        assert env[u"engine の sha16"][rel] == want, rel
    from adapters.xbrl import vocabulary as V
    flags = env[u"P26 の旗"]
    for f in ("last_branch_digit_needs_size", "rounded_diff_hold", "cause_item_direction", "numbers_2026_10_21"):
        assert flags[f] is True and getattr(V.P26, f) is True, f
    assert list(flags["concept_gate"]) == list(V.P26.concept_gate) == ["unit_family", "loose_prefix"]


def check_inputs(rec):
    inp = rec[u"入力の sha256"]
    d67 = inp[u"書類 67(経営分析の文を持つ)の sha256"]
    assert len(d67) == 67
    assert digest([u"%s\t%s" % (k, d67[k]) for k in sorted(d67)]) == DOCS67_DIGEST, u"書類 67 の digest が留めた値と違う"
    assert sorted(d[u"doc"] for d in rec[u"Q1"][u"書類"]) == sorted(d67), u"Q-1 の書類が入力の 67 と違う"
    assert inp[u"書類 214(67 の外)の sha256 を束ねた値(path 順の 'docID\\tsha256' の行)"] == DOCS214_DIGEST
    for rel, want in INPUT_SHAS.items():
        assert inp[rel] == want, rel
    assert inp[u"儀式の同梱書類"] == RITUAL_ZIP_SHA
    assert len(inp[u"人の読みの入力 file の sha256(``--readings``。内容は記録の行に写した)"]) == 64
    assert len(inp[u"engine の変異の表の入力 file の sha256(``--mutations``。手で走らせた表の写し)"]) == 64


# ----------------------------------------------------------------------------------------------------------------
# 予測の判定(封の字から幅を読み、記録の行から門が自分で求める)
def seal_cells(seal, tag):
    for l in seal.splitlines():
        if l.startswith(u"| **%s** |" % tag):
            return [c.strip() for c in l.strip().strip(u"|").split(u"|")]
    raise AssertionError(tag)


def bounds(seal):
    c = dict((t, seal_cells(seal, t)[1]) for t in ("Q-1", "Q-2", "Q-3", "Q-4", "Q-5", "Q-6", "Q-7"))
    m1 = re.search(r"VALUE_MISMATCH \*\*(\d+)〜(\d+)\*\*、新しい GROUNDED \*\*(\d+)\*\*、GROUNDED → 非 GROUNDED \*\*(\d+)〜(\d+)\*\*", c["Q-1"])
    m2 = re.search(r"「文が本当に違う」\*\*(\d+)〜(\d+)\*\*", c["Q-2"])
    m3 = re.search(r"穴 B 通した \*\*(\d+) / (\d+)\*\*、儀式 通した \*\*(\d+)〜(\d+)\*\*、段 2 の注入 GROUNDED \*\*(\d+) / (\d+)\*\*", c["Q-3"])
    m4 = re.search(r"P26 の GROUNDED \*\*(\d+)\*\*", c["Q-4"])
    m5 = re.search(r"新しい GROUNDED\)\*\*(\d+)\*\*", c["Q-5"])
    m6 = re.search(r"recipes \*\*\+(\d+)〜\+(\d+) / −(\d+)〜−(\d+)\*\*、extract \*\*≤ (\d+)\*\*、vocabulary \*\*≤ (\d+)\*\*、registry_setup \*\*≤ (\d+)\*\*、comparators \*\*(\d+)\*\*、core/ (\d+)", c["Q-6"])
    m7 = re.search(r"登録簿の理由の網羅 (\d+) → (\d+)", c["Q-7"])
    assert m1 and m2 and m3 and m4 and m5 and m6 and m7, u"封の予測の書き方が変わった"
    g = lambda m: tuple(int(x) for x in m.groups())
    return {"q1": g(m1), "q2": g(m2), "q3": g(m3), "q4": g(m4)[0], "q5": g(m5)[0], "q6": g(m6), "q7": g(m7)}


ALLOWED_RED_KINDS = (u"sha・指紋", u"profile の一覧", u"登録簿と理由の表", u"変異の予測")


def judgments(rec, seal):
    b = bounds(seal)
    J = {}
    c = recount_q1(rec)
    vlo, vhi, newg, glo, ghi = b["q1"]
    J["Q-1"] = u"当たり" if (vlo <= c[u"VM26"] <= vhi and c[u"新しい GROUNDED"] == newg and glo <= c[u"GROUNDED から外れた"] <= ghi) else u"外れ"
    q2, _q2b = read_rows(rec)
    r2 = recount_readings(rec[u"Q2"][u"行"], READ_WORDS)
    if r2[u"未読"]:
        J["Q-2"] = u"読み待ち"
    else:
        J["Q-2"] = u"当たり" if b["q2"][0] <= r2[READ_WRONG] <= b["q2"][1] else u"外れ"
    c3 = recount_q3(rec)
    h0, hn, rlo, rhi, s0, sn = b["q3"]
    J["Q-3"] = u"当たり" if (c3[u"穴 B P26 通した"] == h0 and c3[u"穴 B"] == hn and rlo <= len(c3[u"儀式 P26 通した id"]) <= rhi
                            and c3[u"段 2 注入 P26 G"] == s0 and c3[u"段 2 注入"] == sn) else u"外れ"
    J["Q-4"] = u"当たり" if recount_q4(rec[u"Q4"][u"行"])[u"P26 G(全部)"] == b["q4"] else u"外れ"
    J["Q-5"] = u"当たり" if recount_q5(rec[u"Q5"][u"行"])[u"新しい GROUNDED"] == b["q5"] else u"外れ"
    e6 = rec[u"Q6"]
    d = e6[u"engine の差分"]
    rc, ex, vc, rg, cp = (d["adapters/xbrl/recipes.py"], d["adapters/xbrl/extract.py"], d["adapters/xbrl/vocabulary.py"], d["adapters/xbrl/registry_setup.py"], d["adapters/xbrl/comparators.py"])
    kinds = set(x[u"種類"] for x in e6[u"既存試験の赤(直す前)"])
    ilo, ihi, dlo, dhi, emax, vmax, rmax, cmax, core_max = b["q6"]
    ok6 = (ilo <= rc[u"挿入"] <= ihi and dlo <= rc[u"削除"] <= dhi and ex[u"挿入"] + ex[u"削除"] <= emax and vc[u"挿入"] + vc[u"削除"] <= vmax
           and rg[u"挿入"] + rg[u"削除"] <= rmax and cp[u"挿入"] + cp[u"削除"] <= cmax and d[u"core/"][u"差の行数"] <= core_max and kinds <= set(ALLOWED_RED_KINDS)
           and bool(e6[u"既存試験の赤(直す前)"]))
    J["Q-6"] = u"当たり" if ok6 else u"外れ"
    c7 = recount_q7(rec)
    q7 = rec[u"Q7"]
    reg = q7[u"登録簿の理由"]
    ok7 = (c7[u"違う(節)"] == c[u"VM26"] and c7[u"書類ごとに一致"] and q7[u"3 つの理由の行"] > 0 and list(q7[u"3 つの理由の行が入った節"]) == [u"要確認"]
           and (reg[u"合計"], reg[u"表 REASON_JA にある"]) == (b["q7"][1], b["q7"][1]) and not reg[u"表に無い"])
    J["Q-7"] = u"当たり" if ok7 else u"外れ"
    J["Q-8"] = u"判定しない(段 2)"
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
    c = recount_q1(rec)
    L = [u"| 項目 | 件数 |", u"|---|---:|",
         u"| 書類 | %d |" % c[u"書類数"], u"| claim の総数 | %s |" % comma(c[u"claims"]), u"| 動いた行(全 state) | %d |" % c[u"動いた"],
         u"| 「違う」から外れた行(P25 が VALUE_MISMATCH、P26 が違う) | %d |" % c[u"違うから外れた"],
         u"| GROUNDED から外れた行(P25 が GROUNDED、P26 が違う) | %d |" % c[u"GROUNDED から外れた"],
         u"| 新しい GROUNDED(P25 が GROUNDED でなく P26 が GROUNDED) | %d |" % c[u"新しい GROUNDED"],
         u"| 読みだけ変わった行(G5。state・reason は同じ) | %d |" % c[u"読みだけ"]]
    B["Q-1 の数"] = u"\n".join(L)
    L = [u"| 無改変 67 書類 | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND |", u"|---|---:|---:|---:|---:|",
         u"| P25(対照) | %s | %s | %s | %s |" % (comma(c[u"G25"]), comma(c[u"VM25"]), comma(c[u"UNV25"]), comma(c[u"PNF25"])),
         u"| **P26** | **%s** | **%s** | **%s** | **%s** |" % (comma(c[u"G26"]), comma(c[u"VM26"]), comma(c[u"UNV26"]), comma(c[u"PNF26"]))]
    B["Q-1 の state の表"] = u"\n".join(L)
    L = [u"| 向き(P25 → P26) | 行 |", u"|---|---:|"]
    for k, v in sorted(c[u"向き"].items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(u"| %s | %d |" % (cell(k), v))
    B["Q-1 の向き"] = u"\n".join(L)
    fl = rec[u"旗ごと"]
    L = [u"| 旗 1 つだけを P25 に足した profile | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND | 動いた行 |", u"|---|---:|---:|---:|---:|---:|"]
    for g in sorted(fl[u"旗"]):
        x = fl[u"旗"][g]
        L.append(u"| %s | %s | %s | %s | %s | %d |" % (g, comma(x["GROUNDED"]), comma(x["VALUE_MISMATCH"]), comma(x["UNVERIFIABLE"]), comma(x["POINTER_NOT_FOUND"]), x[u"動いた行"]))
    B["旗ごとの表"] = u"\n".join(L)
    q2, q2b = read_rows(rec)
    r2 = recount_readings(rec[u"Q2"][u"行"], READ_WORDS)
    r2b = recount_readings(rec[u"Q2b"][u"行"], READ_WORDS_2B)
    L = [u"| 動いた先の理由 | 行 | 正しい文 | 文が本当に違う | 分からない | 未読 |", u"|---|---:|---:|---:|---:|---:|"]
    byr = {}
    for r in rec[u"Q2"][u"行"]:
        byr.setdefault(r[u"P26"][u"reason"], []).append(r)
    for k in sorted(byr, key=lambda s: (-len(byr[s]), s)):
        rr = recount_readings(byr[k], READ_WORDS)
        L.append(u"| %s | %d | %d | %d | %d | %d |" % (k, rr[u"行"], rr[READ_OK], rr[READ_WRONG], rr[READ_UNSURE], rr[u"未読"]))
    L.append(u"| **合計** | **%d** | **%d** | **%d** | **%d** | **%d** |" % (r2[u"行"], r2[READ_OK], r2[READ_WRONG], r2[READ_UNSURE], r2[u"未読"]))
    B["Q-2 の読み"] = u"\n".join(L)
    L = [u"| GROUNDED から外れた行 | 行 | 偶然の一致 | 正しい結びを失った | 分からない | 未読 |", u"|---|---:|---:|---:|---:|---:|",
         u"| 合計 | %d | %d | %d | %d | %d |" % (r2b[u"行"], r2b[READ_COINCIDENCE], r2b[READ_LOST], r2b[READ_UNSURE], r2b[u"未読"])]
    B["Q-2b の読み"] = u"\n".join(L)
    c3 = recount_q3(rec)
    L = [u"| 項目 | 実測 |", u"|---|---|",
         u"| 穴 B(前期の値への置き換え)の注入 P26 で通した | %s |" % F(c3[u"穴 B P26 通した"], c3[u"穴 B"]),
         u"| 穴 B P25(対照)で通した | %s |" % F(c3[u"穴 B P25 通した"], c3[u"穴 B"]),
         u"| 穴 B P25 の止めのうち要確認に移った | %s |" % F(c3[u"穴 B 要確認に移る"], c3[u"穴 B P25 止めた"]),
         u"| 儀式 P26 で通した | %s(%s) |" % (F(len(c3[u"儀式 P26 通した id"]), c3[u"儀式 P26 の行"]), u"・".join(c3[u"儀式 P26 通した id"])),
         u"| 儀式 P25(対照)で通した | %s(%s) |" % (F(len(c3[u"儀式 P25 通した id"]), c3[u"儀式 P25 の行"]), u"・".join(c3[u"儀式 P25 通した id"])),
         u"| 儀式の注入の止めが要確認に移った(共通の行) | %d |" % c3[u"儀式 VM→要確認"],
         u"| 儀式 手で当てた(P26 の表から消えた)行 | %d(通した %d) |" % (len(rec[u"Q3"][u"儀式"][u"手で当てた(P26 の表から消えた行)"]), rec[u"Q3"][u"儀式"][u"集計"][u"手で当てて通した"]),
         u"| 段 2 の注入で Core 自身 P26 が GROUNDED | %s |" % F(c3[u"段 2 注入 P26 G"], c3[u"段 2 注入"]),
         u"| 段 2 の注入の止めのうち要確認に移った | %d |" % c3[u"段 2 注入の VM→要確認"]]
    B["Q-3 の数"] = u"\n".join(L)
    c4, c5 = recount_q4(rec[u"Q4"][u"行"]), recount_q5(rec[u"Q5"][u"行"])
    L = [u"| 項目 | 実測 |", u"|---|---|",
         u"| Q-4 動いた行 | %d |" % c4[u"行"], u"| Q-4 注入(作れなかった %d) | %d |" % (rec[u"Q4"][u"集計"][u"作れなかった"], c4[u"注入"]),
         u"| Q-4 有効な注入 | %d |" % c4[u"有効"], u"| Q-4 P26 が GROUNDED にした(P25 の対照 %d) | %d |" % (c4[u"P25 G(全部)"], c4[u"P26 G(全部)"]),
         u"| Q-4 P25 の止めが P26 で要確認に移った有効な注入 | %d |" % c4[u"VM→要確認"],
         u"| Q-5 P25 で GROUNDED の差の主張 | %d |" % c5[u"行"], u"| Q-5 注入(有効 %d) | %d |" % (c5[u"有効"], c5[u"注入"]),
         u"| Q-5 新しい GROUNDED(P25 が止めて P26 が GROUNDED にした) | %d |" % c5[u"新しい GROUNDED"],
         u"| Q-5 P25 も P26 も GROUNDED にした(数えない) | %d |" % c5[u"両方 GROUNDED"],
         u"| Q-5 P25 の止めが P26 で要確認に移った | %d / %d |" % (c5[u"VM→要確認"], c5[u"P25 が止めた"])]
    B["Q-4・Q-5 の数"] = u"\n".join(L)
    d = rec[u"Q6"][u"engine の差分"]
    L = [u"| file | 挿入 | 削除 |", u"|---|---:|---:|"]
    for f in sorted(k for k in d if k != u"core/"):
        L.append(u"| `%s` | %d | %d |" % (f, d[f][u"挿入"], d[f][u"削除"]))
    L.append(u"| `core/`(差の行数) | %d | |" % d[u"core/"][u"差の行数"])
    B["Q-6 の差分"] = u"\n".join(L)
    red = rec[u"Q6"][u"既存試験の赤(直す前)"]
    kinds = {}
    for x in red:
        kinds[x[u"種類"]] = kinds.get(x[u"種類"], 0) + 1
    L = [u"| 既存試験の赤(直す前)の種類 | 本数 |", u"|---|---:|"]
    for k in sorted(kinds, key=lambda s: (-kinds[s], s)):
        L.append(u"| %s | %d |" % (k, kinds[k]))
    L.append(u"| **合計** | **%d** |" % len(red))
    B["Q-6 の赤の種類"] = u"\n".join(L)
    L = [u"| 試験 | 種類 | 直し |", u"|---|---|---|"]
    for x in red:
        L.append(u"| `%s` | %s | %s |" % (x[u"試験"], cell(x[u"種類"]), cell(x[u"直し"])))
    B["Q-6 の赤の一覧"] = u"\n".join(L)
    c7 = recount_q7(rec)
    q7 = rec[u"Q7"]
    reg = q7[u"登録簿の理由"]
    L = [u"| 項目 | 実測 |", u"|---|---|",
         u"| 報告形の「違う」の節の合計(P26 を明示した 67 書類) | %d |" % c7[u"違う(節)"], u"| P26 の VALUE_MISMATCH(state)の合計 | %d |" % c7[u"VM(state)"],
         u"| 三つの理由の行(入った節) | %d(%s) |" % (q7[u"3 つの理由の行"], u"・".join(u"%s %d" % (k, v) for k, v in q7[u"3 つの理由の行が入った節"].items())),
         u"| 登録簿の理由 | %d(POINTER_NOT_FOUND %d・UNVERIFIABLE %d) |" % (reg[u"合計"], reg[u"POINTER_NOT_FOUND"], reg[u"UNVERIFIABLE"]),
         u"| うち報告形の表 REASON_JA にある | %d |" % reg[u"表 REASON_JA にある"]]
    B["Q-7 の数"] = u"\n".join(L)
    return B


def prose_facts(rec):
    P = {}
    pr = rec[u"予測の判定"]
    hit = sum(1 for v in pr.values() if v[u"判定"] == u"当たり")
    miss = sum(1 for v in pr.values() if v[u"判定"] == u"外れ")
    unm = sum(1 for v in pr.values() if v[u"判定"] in (u"読み待ち", u"測れない"))
    P["pred"] = u"**予測 機械判定 当たり %d / 外れ %d / 読み待ち・測れない %d**(Q-1〜Q-7。Q-8 は段 2 なので判定しない)。" % (hit, miss, unm)
    d = rec[u"Q6"][u"engine の差分"]
    P["head"] = (u"engine の直し: " + u"、".join(u"`%s` 挿入 %d・削除 %d" % (f, d[f][u"挿入"], d[f][u"削除"]) for f in
                                                ("adapters/xbrl/recipes.py", "adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/registry_setup.py",
                                                 "adapters/xbrl/report_customer.py", "adapters/xbrl/comparators.py")) + u"、`core/` %d 行。" % d[u"core/"][u"差の行数"])
    c = recount_q1(rec)
    P["q1"] = u"67 書類(claim %s)の無改変で、P25 から P26 に動いた行は %d。VALUE_MISMATCH は P25 が %s、P26 が %s(差 %d)。GROUNDED は %s → %s、UNVERIFIABLE は %s → %s、POINTER_NOT_FOUND は %s → %s。新しい GROUNDED は %d。" % (
        comma(c[u"claims"]), c[u"動いた"], comma(c[u"VM25"]), comma(c[u"VM26"]), c[u"VM25"] - c[u"VM26"], comma(c[u"G25"]), comma(c[u"G26"]), comma(c[u"UNV25"]), comma(c[u"UNV26"]),
        comma(c[u"PNF25"]), comma(c[u"PNF26"]), c[u"新しい GROUNDED"])
    r2 = recount_readings(rec[u"Q2"][u"行"], READ_WORDS)
    r2b = recount_readings(rec[u"Q2b"][u"行"], READ_WORDS_2B)
    P["q2"] = u"「違う」から外れた %d 行を全部読んで、正しい文 %d・文が本当に違う %d・分からない %d(未読 %d)。GROUNDED から外れた %d 行は、偶然の一致 %d・正しい結びを失った %d・分からない %d(未読 %d)。" % (
        r2[u"行"], r2[READ_OK], r2[READ_WRONG], r2[READ_UNSURE], r2[u"未読"], r2b[u"行"], r2b[READ_COINCIDENCE], r2b[READ_LOST], r2b[READ_UNSURE], r2b[u"未読"])
    c3 = recount_q3(rec)
    P["q3"] = u"穴 B の注入 %d 件を P26 で再検証すると、通した %s(P25 は %s)。儀式を P26 で回すと、通した %s(%s)。段 2 の材料の注入 %d 件のうち Core 自身 P26 が GROUNDED にしたのは %d。" % (
        c3[u"穴 B"], F(c3[u"穴 B P26 通した"], c3[u"穴 B"]), F(c3[u"穴 B P25 通した"], c3[u"穴 B"]), F(len(c3[u"儀式 P26 通した id"]), c3[u"儀式 P26 の行"]),
        u"・".join(c3[u"儀式 P26 通した id"]), c3[u"段 2 注入"], c3[u"段 2 注入 P26 G"])
    c4, c5 = recount_q4(rec[u"Q4"][u"行"]), recount_q5(rec[u"Q5"][u"行"])
    P["q4"] = u"動いた %d 行に注入 %d 回(作れなかった %d・有効 %d・有効でない %d)。P26 が GROUNDED にした %d 回(P25 の対照も %d 回)。" % (
        c4[u"行"], c4[u"注入"], rec[u"Q4"][u"集計"][u"作れなかった"], c4[u"有効"], c4[u"有効でない"], c4[u"P26 G(全部)"], c4[u"P25 G(全部)"])
    P["q5"] = u"P25 で GROUNDED の差の主張 %d 行に末尾の桁 ±1 の注入 %d 回(有効 %d)。P25 が止めて P26 が GROUNDED にした行(新しい GROUNDED)は %d、P25 も P26 も GROUNDED にした注入は %d(数えない)、P25 の止めが P26 で要確認に移った注入は %d。" % (
        c5[u"行"], c5[u"注入"], c5[u"有効"], c5[u"新しい GROUNDED"], c5[u"両方 GROUNDED"], c5[u"VM→要確認"])
    e6 = rec[u"Q6"]
    after = u"・".join(u"%s → %s" % (t[u"コマンド"], t[u"最後の行"]) for t in e6.get(u"既存試験", []))
    P["q6"] = u"既存試験の赤(直す前): %d 本。%s" % (
        len(e6[u"既存試験の赤(直す前)"]), (u"直した後の既存試験: %s。" % after) if after else u"直した後の既存試験の全実行は記録に写していない(commit 前の全実行の結果は司令塔への報告に書く)。")
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
    t = re.sub(r"[A-Za-z_][A-Za-z_0-9\-]*\d[A-Za-z_0-9\-]*", u"", t)      # S100YMFV・N076・Q-1・P26・sha16 など
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
    for lit in (u"判定しない(段 2)", u"`comparators.py` は零行", u"門で縛れない", u"文が本当に違う", u"要確認", u"P25", u"P26"):
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
    u"""いまの engine が、測った時点の sha か、宣言された遷移の値であること。"""
    for rel, want in sorted(ENGINE_AT_MEASURE.items()):
        got = sha16(rel)
        if got != want and rel in ENGINE_TRANSITIONS:
            later, seal_rel = ENGINE_TRANSITIONS[rel]
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
        u"""この実行の事実を字で留める(行から数えた値。変えたら記録も文書も作り直す)。"""
        c = recount_q1(self.rec)
        self.assertEqual((c[u"動いた"], c[u"VM25"], c[u"VM26"], c[u"G25"], c[u"G26"], c[u"新しい GROUNDED"], c[u"GROUNDED から外れた"], c[u"違うから外れた"]),
                         (217, 626, 433, 4382, 4371, 0, 11, 193))
        self.assertEqual(c[u"理由別"], {REASON_HOLD: 158, REASON_CONCEPT: 23, REASON_DIR: 24})
        c3 = recount_q3(self.rec)
        self.assertEqual((c3[u"穴 B P26 通した"], len(c3[u"儀式 P26 通した id"]), c3[u"段 2 注入 P26 G"]), (0, 2, 0))
        self.assertEqual(c3[u"儀式 P26 通した id"], ["N069", "N096"])
        self.assertEqual((recount_q4(self.rec[u"Q4"][u"行"])[u"P26 G(全部)"], recount_q5(self.rec[u"Q5"][u"行"])[u"新しい GROUNDED"]), (0, 0))

    def test_6_engine_is_the_one_measured_or_a_declared_transition(self):
        engine_ok()
        self.assertTrue(self.rec[u"環境"][u"HEAD"].startswith(SEAL_COMMIT))

    def test_7_numstat_in_the_record_is_the_engine_diff_from_the_seal_commit(self):
        u"""engine が測った時点の sha のままのときだけ: 封の commit からの差分の行数が記録と一致(動いたら宣言された遷移の後なので比べない)。
        封の commit は a8d8099、engine の差は段 1 の commit が入るまでは作業木との差。段 1 の commit の後は封の commit からの差がそのまま残る。"""
        for rel, want in ENGINE_AT_MEASURE.items():
            if sha16(rel) != want:
                self.skipTest(u"engine が宣言された遷移の後")
        d = self.rec[u"Q6"][u"engine の差分"]
        for f in ("adapters/xbrl/recipes.py", "adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/registry_setup.py", "adapters/xbrl/report_customer.py",
                  "adapters/xbrl/comparators.py"):
            o = git("diff", "--numstat", SEAL_COMMIT, "--", f).stdout.split()
            self.assertEqual((int(o[0]), int(o[1])) if o else (0, 0), (d[f][u"挿入"], d[f][u"削除"]), f)

    def test_8_core_and_the_untouched_files_are_untouched_and_default_is_p22_in_step_1(self):
        self.assertEqual(git("diff", "--numstat", SEAL_COMMIT, "--", "core").stdout, "")
        self.assertEqual(git("status", "--porcelain", "--", "core").stdout, "")
        for rel in UNTOUCHED:
            self.assertEqual(git("diff", "--numstat", SEAL_COMMIT, "--", rel).stdout, "", rel)
            self.assertEqual(git("status", "--porcelain", "--", rel).stdout, "", rel)
        from adapters.xbrl import vocabulary as V
        # 段 1 の結果の commit では P22。段 2 の遷移(vocabulary.py が宣言された値)の後は P26(封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md)
        moved = sha16("adapters/xbrl/vocabulary.py") != ENGINE_AT_MEASURE["adapters/xbrl/vocabulary.py"]
        self.assertEqual(V.DEFAULT_PROFILE, "P26" if moved else "P22")
        self.assertIn("P26", V.PROFILES)

    def test_9_q8_is_not_judged_and_the_seal_was_not_edited(self):
        self.assertTrue(self.rec[u"予測の判定"]["Q-8"][u"判定"].startswith(u"判定しない"))
        self.assertEqual(git("diff", "--numstat", SEAL_COMMIT, "--", SEAL_REL).stdout, "")
        self.assertEqual(git("status", "--porcelain", "--", SEAL_REL).stdout, "")

    def test_10_cache_inputs_match_the_record(self):
        d67 = self.rec[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]
        if not have_cache(d67):
            self.skipTest(u"手元の cache に 67 書類が揃っていない")
        for d, want in d67.items():
            self.assertEqual(sha_path(os.path.join(CACHE, d + ".zip")), want, d)
        self.assertEqual(sha_path(LASTBRANCH_REC), INPUT_SHAS["fixtures/xbrl/lastbranch_2026-10-21.json"])

    def test_11_existing_red_list_is_the_closed_kinds_and_every_fix_is_named(self):
        red = self.rec[u"Q6"][u"既存試験の赤(直す前)"]
        self.assertTrue(red)
        for x in red:
            self.assertIn(x[u"種類"], ALLOWED_RED_KINDS, x[u"試験"])
            self.assertTrue(x[u"直し"].strip() and x[u"試験"].startswith(u"tests/"), x)
        self.assertEqual(len({x[u"試験"] for x in red}), len(red), u"同じ試験が 2 回")

    def test_12_every_moved_row_is_one_to_one_with_its_named_fact(self):
        u"""動いた 217 行のうち三つの理由に動いた行は、provenance に名指した fact か形を持つ(Recipe の数 = 動いた行の数。check_record が縛る)。
        ここでは動いた行が (doc, id) で一意なことと、向きの合計が行数なことを見る。"""
        mv = self.rec[u"Q1"][u"動いた行"]
        self.assertEqual(len({key(r) for r in mv}), len(mv))
        for r in mv:
            self.assertNotEqual((r[u"P25"], r[u"P26"]), (None, None))
            if r[u"P26"][u"reason"] in (REASON_CONCEPT, REASON_HOLD):
                self.assertEqual(r[u"P26"][u"pointers"], [], key(r))        # 名指さない(pointer なし)。名指しは provenance だけ


def run_script(args):
    env = dict(os.environ)
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=ROOT, capture_output=True, text=True, env=env)


def strip_readings(rows):
    return [dict((k, v) for k, v in r.items() if k not in (u"読み", u"根拠")) for r in rows]


@unittest.skipUnless(have_cache(LIGHT_DOCS) and labels_ok(), u"手元の cache とラベルが要る")
class RerunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)

    def test_light_q1_matches_the_record(self):
        import tempfile
        out = os.path.join(tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None), "q1.json")
        r = run_script(["--stage", "q1", "--docs", ",".join(LIGHT_DOCS), "--out", out])
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        got = jload(out)[u"Q1"]
        want = [x for x in self.rec[u"Q1"][u"動いた行"] if x[u"doc"] in LIGHT_DOCS]
        self.assertTrue(want)
        self.assertEqual(sorted(strip_readings(got[u"動いた行"]), key=lambda x: (x[u"doc"], x[u"id"])), sorted(strip_readings(want), key=lambda x: (x[u"doc"], x[u"id"])))
        wd = dict((d[u"doc"], d) for d in self.rec[u"Q1"][u"書類"] if d[u"doc"] in LIGHT_DOCS)
        for d in got[u"書類"]:
            self.assertEqual(d, wd[d[u"doc"]])

    @unittest.skipUnless(RUN_HEAVY, u"AUDIT_CORE_P26=1 のときだけ走る(全書類の走らせ直し。約 二十分)")
    def test_heavy_everything_matches_the_record(self):
        import tempfile
        out = os.path.join(tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None), "all.json")
        r = run_script(["--stage", "all", "--out", out, "--jobs", "4"])
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        got = jload(out)
        for k in (u"Q1", u"Q3", u"Q4", u"Q5", u"Q7"):
            a, b = copy.deepcopy(got[k]), copy.deepcopy(self.rec[k])
            for part in (a, b):
                for sec in part.values():
                    if isinstance(sec, dict):
                        sec.pop(u"所要秒", None)
            if k == u"Q1":
                for part in (a, b):
                    part[u"動いた行"] = strip_readings(part[u"動いた行"])
            self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True), k)


# ----------------------------------------------------------------------------------------------------------------
# 門自身の変異(壊した標本で赤くなること)
class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec0 = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def _mut(self):
        return copy.deepcopy(self.rec0)

    def _red(self, fn, *a):
        with self.assertRaises((AssertionError, KeyError, IndexError, TypeError, ValueError)):
            fn(*a)

    def test_baseline_is_green(self):
        check_record(self._mut())
        check_inputs(self._mut())
        check_judgments(self._mut(), self.seal)
        check_doc(self._mut(), self.doc)
        check_mutation_record(self._mut())
        engine_ok()

    def test_m1_drop_one_moved_row(self):
        r = self._mut()
        r[u"Q1"][u"動いた行"].pop()
        self._red(check_record, r)

    def test_m2_a_moved_row_that_becomes_grounded_is_seen(self):
        r = self._mut()
        x = [x for x in r[u"Q1"][u"動いた行"] if x[u"P25"][u"state"] == "VALUE_MISMATCH"][0]
        x[u"P26"][u"state"] = "GROUNDED"
        self._red(check_record, r)
        self.assertEqual(judgments(r, self.seal)["Q-1"], u"外れ")

    def test_m3_change_the_value_mismatch_count_of_one_document(self):
        r = self._mut()
        d = [d for d in r[u"Q1"][u"書類"] if d[u"states P26"].get("VALUE_MISMATCH")][0]
        d[u"states P26"]["VALUE_MISMATCH"] += 1
        self._red(check_record, r)

    def test_m3b_the_p25_side_must_equal_the_p25_record(self):
        """書類 2 本で GROUNDED を +1 と −1(合計は変わらない)にする。書類ごとの突き合わせ(P25 の記録 lastbranch の書類別)だけが見つける。"""
        r = self._mut()
        a, b = r[u"Q1"][u"書類"][0], r[u"Q1"][u"書類"][1]
        a[u"states P25"]["GROUNDED"] += 1
        b[u"states P25"]["GROUNDED"] -= 1
        self._red(check_record, r)

    def test_m4_change_a_judgment_word(self):
        r = self._mut()
        r[u"予測の判定"]["Q-1"][u"判定"] = u"外れ"
        self._red(check_judgments, r, self.seal)

    def test_m5_a_p26_pass_in_the_hole_b_is_seen(self):
        r = self._mut()
        x = r[u"Q3"][u"穴 B"][u"行"][0]
        x[u"P26"][u"結果"] = u"通した(参照先が前期へ移った)"
        self._red(check_record, r)
        self.assertEqual(judgments(r, self.seal)["Q-3"], u"外れ")

    def test_m6_a_p26_pass_in_the_ritual_moves_the_judgment(self):
        r = self._mut()
        for x in r[u"Q3"][u"儀式"][u"行"]:
            if x[u"P26"] == STOPPED:
                x[u"P26"] = PASSED
                break
        self.assertEqual(judgments(r, self.seal)["Q-3"], u"当たり" if 2 <= len(recount_q3(r)[u"儀式 P26 通した id"]) <= 3 else u"外れ")
        self._red(check_record, r)
        for x in r[u"Q3"][u"儀式"][u"行"]:
            if x[u"P26"] == STOPPED:
                x[u"P26"] = PASSED
        self.assertEqual(judgments(r, self.seal)["Q-3"], u"外れ")

    def test_m7_a_grounded_injection_in_the_stage_2_material_is_a_miss(self):
        r = self._mut()
        x = [x for x in r[u"Q3"][u"段 2"][u"行"] if x[u"注入か"]][0]
        x[u"Core 自身 P26"][u"state"] = "GROUNDED"
        self._red(check_record, r)
        self.assertEqual(judgments(r, self.seal)["Q-3"], u"外れ")

    def test_m8_a_grounded_injection_in_q4_is_a_miss(self):
        r = self._mut()
        x = [x for x in r[u"Q4"][u"行"] if x.get(u"変え方") and x[u"P26"].get(u"state")][0]
        x[u"P26"][u"state"] = "GROUNDED"
        self._red(check_record, r)
        self.assertEqual(judgments(r, self.seal)["Q-4"], u"外れ")

    def test_m9_a_new_grounded_injection_in_q5_is_a_miss(self):
        r = self._mut()
        x = [x for x in r[u"Q5"][u"行"] if x[u"P25"].get(u"state") == "VALUE_MISMATCH" and x[u"P26"].get(u"state")][0]
        x[u"P26"][u"state"] = "GROUNDED"
        self._red(check_record, r)
        self.assertEqual(judgments(r, self.seal)["Q-5"], u"外れ")

    def test_m10_a_reading_that_loses_its_row_is_red(self):
        r = self._mut()
        r[u"Q2"][u"行"].pop()
        self._red(check_record, r)
        r = self._mut()
        r[u"Q2"][u"行"][0][u"読み"] = u"どちらとも"
        self._red(check_record, r)
        r = self._mut()
        r[u"Q2"][u"行"][0][u"根拠"] = u" "
        self._red(check_record, r)
        r = self._mut()
        r[u"Q2b"][u"行"][0][u"読み"] = READ_OK            # Q-2b の語ではない
        self._red(check_record, r)

    def test_m11_too_many_wrong_readings_make_q2_a_miss(self):
        r = self._mut()
        for x in r[u"Q2"][u"行"][:3]:
            x[u"読み"] = READ_WRONG
        self.assertEqual(judgments(r, self.seal)["Q-2"], u"外れ")
        r = self._mut()
        for x in r[u"Q2"][u"行"][:2]:
            x[u"読み"] = READ_WRONG
        self.assertEqual(judgments(r, self.seal)["Q-2"], u"当たり")
        r[u"Q2"][u"行"][5].pop(u"読み")
        self.assertEqual(judgments(r, self.seal)["Q-2"], u"読み待ち")

    def test_m12_a_number_in_a_document_table_is_red(self):
        doc = self.doc
        B = render_blocks(self.rec0)
        line = [l for l in B["Q-1 の数"].splitlines() if l.startswith(u"| 動いた行")][0]
        self.assertIn(line, doc)
        self._red(check_doc, self.rec0, doc.replace(line, line.replace(u"217", u"216")))

    def test_m13_a_number_in_a_prose_sentence_is_red(self):
        P = prose_facts(self.rec0)
        self.assertIn(P["q1"], self.doc)
        self._red(check_doc, self.rec0, self.doc.replace(P["q1"], P["q1"].replace(u"217", u"218")))

    def test_m14_a_new_unbound_number_in_prose_is_red(self):
        self._red(check_doc, self.rec0, self.doc + u"\nなお本件は 99 件である。\n")

    def test_m15_a_spoiled_input_digest_is_red(self):
        r = self._mut()
        r[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]["S100YMFV"] = u"0" * 64
        self._red(check_inputs, r)
        r = self._mut()
        r[u"入力の sha256"]["fixtures/xbrl/lastbranch_2026-10-21.json"] = u"0" * 64
        self._red(check_inputs, r)

    def test_m16_mutation_record_must_have_five_rows(self):
        r = self._mut()
        r[u"変異(engine。手で走らせた)"][u"表"] = r[u"変異(engine。手で走らせた)"][u"表"][:4]
        self._red(check_mutation_record, r)

    def test_m17_a_wrong_engine_sha_is_red(self):
        global ENGINE_AT_MEASURE, ENGINE_TRANSITIONS
        old, old_t = dict(ENGINE_AT_MEASURE), dict(ENGINE_TRANSITIONS)
        try:
            for rel in sorted(old):
                if rel in old_t:
                    ENGINE_TRANSITIONS = dict(old_t, **{rel: ("0" * 16, old_t[rel][1])})
                    self._red(engine_ok)
                ENGINE_TRANSITIONS = {}
                ENGINE_AT_MEASURE = dict(old, **{rel: "0" * 16})
                self._red(engine_ok)
                ENGINE_AT_MEASURE = dict(old)
        finally:
            ENGINE_AT_MEASURE, ENGINE_TRANSITIONS = old, old_t
        engine_ok()

    def test_m18_an_existing_red_of_a_forbidden_kind_makes_q6_a_miss(self):
        r = self._mut()
        r[u"Q6"][u"既存試験の赤(直す前)"].append({u"試験": u"tests/measure/x.py::T::t", u"種類": u"数 / state の門", u"直し": u"x"})
        self.assertEqual(judgments(r, self.seal)["Q-6"], u"外れ")

    def test_m19_a_deletion_in_recipes_or_a_wide_diff_makes_q6_a_miss(self):
        r = self._mut()
        r[u"Q6"][u"engine の差分"]["adapters/xbrl/recipes.py"][u"削除"] = 3
        self.assertEqual(judgments(r, self.seal)["Q-6"], u"外れ")
        r = self._mut()
        r[u"Q6"][u"engine の差分"]["adapters/xbrl/comparators.py"][u"挿入"] = 1
        self.assertEqual(judgments(r, self.seal)["Q-6"], u"外れ")
        r = self._mut()
        r[u"Q6"][u"engine の差分"]["adapters/xbrl/extract.py"][u"挿入"] = 61
        self.assertEqual(judgments(r, self.seal)["Q-6"], u"外れ")
        r = self._mut()
        r[u"Q6"][u"engine の差分"][u"core/"][u"差の行数"] = 1
        self.assertEqual(judgments(r, self.seal)["Q-6"], u"外れ")
        r = self._mut()
        r[u"Q6"][u"既存試験の赤(直す前)"] = []
        self.assertEqual(judgments(r, self.seal)["Q-6"], u"外れ")

    def test_m20_a_three_reason_row_in_the_wrong_section_makes_q7_a_miss(self):
        r = self._mut()
        r[u"Q7"][u"3 つの理由の行が入った節"] = {u"要確認": r[u"Q7"][u"3 つの理由の行"] - 1, u"違う": 1}
        self.assertEqual(judgments(r, self.seal)["Q-7"], u"外れ")
        r = self._mut()
        r[u"Q7"][u"書類別"][0][u"違う(節の件数)"] += 1
        self.assertEqual(judgments(r, self.seal)["Q-7"], u"外れ")
        r = self._mut()
        r[u"Q7"][u"登録簿の理由"][u"表 REASON_JA にある"] -= 1
        self.assertEqual(judgments(r, self.seal)["Q-7"], u"外れ")

    def test_m21_the_flag_made_identity_turns_q1_red(self):
        r = self._mut()
        for x in r[u"Q1"][u"動いた行"]:
            x[u"P26"] = copy.deepcopy(x[u"P25"])
        self._red(check_record, r)

    def test_m22_the_p25_side_changed_in_the_ritual_or_the_hole_b_is_red(self):
        r = self._mut()
        x = [x for x in r[u"Q3"][u"儀式"][u"行"] if x[u"P25"] == STOPPED][0]
        x[u"P25"] = TO_CHECK
        self._red(check_record, r)
        r = self._mut()
        r[u"Q3"][u"穴 B"][u"行"][0][u"P25"][u"pointers"] = ["x"]
        self._red(check_record, r)

    def test_m23_hand_injected_rows_that_passed_are_red(self):
        r = self._mut()
        r[u"Q3"][u"儀式"][u"集計"][u"手で当てて通した"] = 1
        self._red(check_record, r)

    def test_m24_an_engine_flag_changed_in_the_environment_is_red(self):
        r = self._mut()
        r[u"環境"][u"P26 の旗"]["rounded_diff_hold"] = False
        self._red(check_record, r)

    def test_m25_a_changed_seal_bound_moves_the_judgment(self):
        seal = self.seal.replace(u"VALUE_MISMATCH **425〜441**", u"VALUE_MISMATCH **425〜432**")
        self.assertNotEqual(seal, self.seal)
        self.assertEqual(judgments(self.rec0, seal)["Q-1"], u"外れ")

    def test_m26_the_grounded_out_count_must_be_inside_the_sealed_range(self):
        """GROUNDED から外れた行の数(封の幅 8〜14)。行を動かして 7 と 15 にすると Q-1 は外れ、境界の 8 と 14 は当たり。"""
        def with_out(n):
            r = self._mut()
            rows = r[u"Q1"][u"動いた行"]
            outs = [x for x in rows if x[u"P25"][u"state"] == "GROUNDED" and x[u"P26"][u"state"] != "GROUNDED"]
            others = [x for x in rows if not (x[u"P25"][u"state"] == "GROUNDED" and x[u"P26"][u"state"] != "GROUNDED") and x[u"P25"][u"state"] != "GROUNDED"
                      and x[u"P26"][u"state"] != "GROUNDED"]
            k = len(outs)
            for x in outs[:max(0, k - n)]:
                x[u"P25"][u"state"] = "UNVERIFIABLE"               # 一致から外れた行ではなくす
            for x in others[:max(0, n - k)]:
                x[u"P25"][u"state"] = "GROUNDED"                   # 一致から外れた行を増やす
            return r
        self.assertEqual(recount_q1(with_out(8))[u"GROUNDED から外れた"], 8)
        self.assertEqual(judgments(with_out(8), self.seal)["Q-1"], u"当たり")
        self.assertEqual(judgments(with_out(14), self.seal)["Q-1"], u"当たり")
        self.assertEqual(judgments(with_out(7), self.seal)["Q-1"], u"外れ")
        self.assertEqual(judgments(with_out(15), self.seal)["Q-1"], u"外れ")

    def test_m27_a_ritual_row_whose_result_changed_to_something_else_is_red(self):
        """儀式で共通の行の結果が変わった行は全部『止め → 要確認』でなければならない。別の変わり方(止め → UNVERIFIABLE)を集計の写しと合わせても、この検査だけが見つける。"""
        r = self._mut()
        x = [x for x in r[u"Q3"][u"儀式"][u"行"] if x[u"P25"] == STOPPED and x[u"P26"] == STOPPED][0]
        x[u"P26"] = u"detected:UNVERIFIABLE"
        r[u"Q3"][u"儀式"][u"集計"][u"共通の行で結果が違う行"] += 1
        self._red(check_record, r)
        self.assertEqual(recount_q3(r)[u"儀式 共通で結果が違う"], recount_q3(r)[u"儀式 VM→要確認"] + 1)

    def test_m28_a_changed_mutation_table_row_in_the_document_is_red(self):
        row = [l for l in mutation_table(self.rec0).splitlines() if l.startswith(u"| M7 |")][0]
        self.assertIn(row, self.doc)
        self._red(check_doc, self.rec0, self.doc.replace(row, row.replace(u"M7", u"M70")))
        self._red(check_doc, self.rec0, self.doc.replace(row + u"\n", u""))

    def test_m29_the_recipe_count_must_equal_the_moved_rows_of_each_reason(self):
        """provenance の Recipe の数と『あり』を同じだけ増やす(二つの数の突き合わせは通る)。動いた行の数との突き合わせだけが見つける。"""
        r = self._mut()
        r[u"provenance"][u"%s の Recipe" % REASON_HOLD] += 1
        r[u"provenance"][u"%s の provenance あり" % REASON_HOLD] += 1
        self._red(check_record, r)
        r = self._mut()
        r[u"provenance"][u"%s の Recipe" % REASON_CONCEPT] -= 1
        r[u"provenance"][u"provenance に名指しあり"] -= 1
        self._red(check_record, r)
        r = self._mut()
        r[u"provenance"][u"%s の provenance あり" % REASON_DIR] -= 1                  # 名指しを持たない Recipe が 1 つ
        self._red(check_record, r)


if __name__ == "__main__":
    unittest.main()
