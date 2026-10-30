# -*- coding: utf-8 -*-
u"""穴 2 つ(単位語「ポイント」/ 前期の値を通す)の広さ ― 封 docs/XBRL_POINT_PRIOR_SEAL_2026-10-20.md の結果を縛る門。

記録: ``fixtures/xbrl/point_prior_2026-10-20.json``(``measure/xbrl_point_prior_2026-10-20.py --stage all`` の出力)。
文書: ``docs/XBRL_POINT_PRIOR_RESULT_2026-10-20.md``。

この門がやること(どれも、壊した標本で赤くなることを ``MutationTest`` が毎回確かめる):
  1. 入力(書類 281 本の docID・sha256・bytes・区分)を**字で留めた digest** に縛る。cache が在る機械では実物の sha256 も記録と一致させる。
  2. 記録の行(A のポイント claim 29・B の注入 485 と作れない site 287)から、集計・分布・分け方を**独立に**数え直し、記録の集計と一致させる。
     B の分け方は script の関数でなく pointer の字から、前期の字は表記の単位語から求め直す。
  3. 予測 A-1〜A-4・B-1〜B-5 の判定を、封の字から読んだ幅と記録の行から**門が自分で**求め、script の ``judge`` と文書の表と一致させる。
  4. 文書の表(予測・A の分布・ポイント 29 行・GROUNDED 4 行・B の単位別・書類別 67 行・作れない理由・通した例 5 件)を記録から作った字と完全一致させる。
  5. cache が在る機械では 2 書類(S100YMFV・S100YYIA)を script で走らせ直して記録の該当行と一致(軽い)。全書類(約 3 分)は ``AUDIT_CORE_POINT_PRIOR=1`` のときだけ。
  6. engine(``core/``・``adapters/``)・``measure/false_pass_2026-10-14.py``・``measure/inject.py``・封が、封の commit から 0 行であること。
縛っていないもの: A-4 の『正しく結べたか』と B の『前期の値が通ったことを欠陥と読むか』(人の読み。GROUNDED 4 行の読みは文書に字で書き、本数だけ縛る)、
  tests/measure 全体の所要。
"""
import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import statistics
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REC = os.path.join(ROOT, "fixtures", "xbrl", "point_prior_2026-10-20.json")
DOC = os.path.join(ROOT, "docs", "XBRL_POINT_PRIOR_RESULT_2026-10-20.md")
SEAL_REL = "docs/XBRL_POINT_PRIOR_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SCRIPT = os.path.join(ROOT, "measure", "xbrl_point_prior_2026-10-20.py")
GUARDED = ("core", "adapters", "measure/false_pass_2026-10-14.py", "measure/inject.py")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
RUN_HEAVY = os.environ.get("AUDIT_CORE_POINT_PRIOR") == "1"
HEAVY_SKIP_REASON = u"AUDIT_CORE_POINT_PRIOR=1 のときだけ走る(全書類 281 本の走らせ直し。約 3 分)"
LIGHT_DOCS = ("S100YMFV", "S100YYIA")   # 前者はポイントの claim と率の注入が在る小さな書類、後者は作れた注入が 25 件を超える(束が 2 つ)書類

#: **字で留める**(記録の値の写し。定数から作らない)。
INPUT_DIGEST = "9d1ca4159d2e58bb479b47e2495005a6c904d047c846037b1bc0b5dda6135e44"   # 書類 281 本の docID\tsha256\tbytes\t区分 を sorted で \n 結合した sha256
TEXT_DOCS_DIGEST = "f240150645a9b05a8d9bf5a9fe0ab89633ae338e42b8cc4d891dc04ca401e3f5"   # 文あり 67 本の docID を sorted で \n 結合した sha256
ENGINE_BUNDLE = "5b5f030071188864092d0fba8f655ee1f413c08ebbb1769190511bd8720ccbee"
ENGINE_FILES = 36
FACT = {
    "docs": 281, "with_text": 67, "no_text": 214, "unreadable": 0,
    "point_claims": 29, "point_docs": 15, "prints": 29,
    "point_states": {"GROUNDED": 4, "POINTER_NOT_FOUND": 20, "UNVERIFIABLE": 4, "VALUE_MISMATCH": 1},
    "point_reasons": {"(なし)": 5, "no_element": 12, "no_element(point without prior phrase)": 8, "no_subject": 4},
    "pct_claims": 1116, "pct_states": {"GROUNDED": 483, "POINTER_NOT_FOUND": 155, "UNVERIFIABLE": 205, "VALUE_MISMATCH": 273},
    "pct15_states": {"GROUNDED": 117, "POINTER_NOT_FOUND": 76, "UNVERIFIABLE": 57, "VALUE_MISMATCH": 60},
    "grounded_formula": 4, "grounded_words": 3, "span_other_unit": 21,
    "sites": 772, "site_median": 10.0, "site_max": 36, "made": 485, "made_median": 6.0, "unmade": 287,
    "unmade_reasons": {u"元の字の形では前期の値を 1 字違わず書けない": 167, u"数字部分が単純な数でない(複合表記。例 13億51百万円)": 120},
    "stopped": 24, "moved": 458, "same_ref": 1, "other_el": 0, "odd": 0, "else": 2, "passed": 459,
    "docs_with_no_made": 16,
}
K_MOVED = u"通した(参照先が前期へ移った)"
K_SAME = u"通した(参照先が当期の同じ参照先のまま)"
K_OTHER = u"通した(参照先が当期の別要素)"
K_ODD = u"通した(参照先がそのほか)"
K_STOP = u"止めた"
K_ELSE = u"その他"
PASSED_KINDS = (K_MOVED, K_SAME, K_OTHER, K_ODD)
FRAC_RE = re.compile(r"(\d[\d,]*) / (\d[\d,]*) = (\d+\.\d)%")
#: 人の読み(GROUNDED のポイント 4 行 ― 文脈を読んで書いた。本数と対応する行は門が縛る)
READ_A4 = {
    ("S100YMFV", "N066"): u"正しく結べた(自己資本比率の当期と前期の差。文は 2.9・再計算は 3.0 で、丸めの帯の中)",
    ("S100YMFV", "N086"): u"正しく結べた(ROE の当期と前期の差 1.2)",
    ("S100YYDI", "N098"): u"正しく結べた(自己資本比率の当期と前期の差。「減少」は -1.5 と読まれた)",
    ("S100Z6XO", "N092"): u"正しく結べた(自己資本比率 40.3% → 45.8% の差 5.5)",
}
EXAMPLES = (("S100YMFV", "N048"), ("S100YWGX", "N030"), ("S100YXGH", "N003"), ("S100YMFV", "N083"), ("S100YXLE", "N081"))
#: 表記の単位語 -> 文の数の字 1 に当たる fact の値(独立な求め直し用。リテラルで書く)
SUFFIX_MULT = {u"千円": 1e3, u"百万円": 1e6, u"億円": 1e8, u"円": 1.0, u"%": 0.01, u"名": 1.0}


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def F(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


def cell(s):
    return (s if s is not None else u"").replace(u"|", u"｜").replace(u"\n", u" ")


def digest(lines):
    return hashlib.sha256(u"\n".join(lines).encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------------------------------------------------
# 入力の留め
def check_inputs(rec):
    docs = rec[u"書類"]
    assert len(docs) == FACT["docs"], u"書類の数"
    assert len({d[u"docID"] for d in docs}) == len(docs), u"docID が重複"
    lines = sorted(u"%s\t%s\t%d\t%s" % (d[u"docID"], d[u"sha256"], d[u"bytes"], d[u"区分"]) for d in docs)
    assert digest(lines) == INPUT_DIGEST, u"書類の一覧(docID・sha256・bytes・区分)が字で留めた digest と違う"
    t = sorted(d[u"docID"] for d in docs if d[u"区分"] == u"文あり")
    assert digest(t) == TEXT_DOCS_DIGEST, u"文ありの書類の一覧"
    n = rec[u"書類の数"]
    assert (n[u"全部"], n[u"文あり"], n[u"文なし"], n[u"読めない"]) == (FACT["docs"], FACT["with_text"], FACT["no_text"], FACT["unreadable"])
    for k in (u"文あり", u"文なし", u"読めない"):
        assert n[k] == sum(1 for d in docs if d[u"区分"] == k), k
    assert len(t) == FACT["with_text"]
    kinds = {}
    for d in docs:
        kinds[(d[u"区分"], d[u"提出書類の種別"])] = kinds.get((d[u"区分"], d[u"提出書類の種別"]), 0) + 1
    assert kinds == {(u"文あり", u"jpcrp…-asr-"): 67, (u"文なし", u"jpsps…-asr-"): 214}, u"封 §3 の file 名の事実"
    e = rec[u"環境"]
    assert e[u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)"] == ENGINE_BUNDLE
    assert e[u"engine の file 数"] == ENGINE_FILES
    assert e[u"engine と測定の道具の差(git diff HEAD)"][u"差の行数"] == 0
    assert e[u"engine と測定の道具の差(git diff HEAD)"][u"未追跡・変更の file"] == []
    assert e[u"費用"] == u"0 USD" and e[u"profile"] == "P21"
    assert set(e[u"鍵の名前の有無(値は読まない)"]) == {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "EDINET_API_KEY", "OPENAI_API_KEY"}


# ----------------------------------------------------------------------------------------------------------------
# 記録の行から独立に数え直す
def tally(rows, key):
    d = {}
    for r in rows:
        k = r[key] if r[key] is not None else u"(なし)"
        d[k] = d.get(k, 0) + 1
    return dict(sorted(d.items()))


PTR = re.compile(r"^xbrl:([^@]+)@(.+)$")


def indep_kind(row):
    u"""後の state と pointers の字から、止めた/通した の種類を求める(script の classify_after を使わない)。"""
    st = row[u"結果の細目"]
    if row[u"結果"] == K_ELSE and st in ("sentence_not_found", "missing", "id_shift"):
        return K_ELSE
    if st == "VALUE_MISMATCH":
        return K_STOP
    if st != "GROUNDED":
        return K_ELSE
    ms = [PTR.match(p) for p in row[u"後の pointers"] if p.startswith("xbrl:")]
    assert ms and all(ms), u"GROUNDED なのに xbrl の pointer が無い"
    ctxs = [m.group(2) for m in ms]
    els = [m.group(1) for m in ms]
    if all(c.startswith("Prior1Year") for c in ctxs):
        return K_MOVED
    if all(e == row[u"要素"] and c == row[u"当期の枠"] for e, c in zip(els, ctxs)):
        return K_SAME
    if any(e != row[u"要素"] and c.startswith("CurrentYear") for e, c in zip(els, ctxs)):
        return K_OTHER
    return K_ODD


def digits_of(raw):
    m = re.search(r"\d[\d,]*(?:\.\d+)?", raw)
    return m.group(0) if m else None


def suffix_of(raw):
    return raw[raw.rindex(digits_of(raw)) + len(digits_of(raw)):]


def check_a(rec):
    A = rec[u"A"]
    pts = A[u"行"]
    assert len(pts) == FACT["point_claims"], u"ポイントの claim の数"
    assert tally(pts, u"state") == FACT["point_states"], u"ポイントの state の分布"
    assert tally(pts, u"reason") == FACT["point_reasons"], u"ポイントの reason の分布"
    assert len({p[u"書類"] for p in pts}) == FACT["point_docs"]
    text_docs = {d[u"docID"] for d in rec[u"書類"] if d[u"区分"] == u"文あり"}
    assert {p[u"書類"] for p in pts} <= text_docs, u"文なしの書類にポイントの claim が在る"
    assert [d[u"書類"] for d in A[u"書類別"]] == sorted(text_docs), u"A の書類別が文ありの書類と違う"
    # 書類別 -> 行
    for d in A[u"書類別"]:
        mine = [p for p in pts if p[u"書類"] == d[u"書類"]]
        assert d[u"ポイントの claim"] == len(mine), d[u"書類"]
        assert d[u"ポイントの state"] == tally(mine, u"state"), d[u"書類"]
        assert sum(d[u"state の分布"].values()) == d[u"claim"], d[u"書類"]
        assert sum(d[u"％の claim の state"].values()) <= d[u"claim"], d[u"書類"]
    for p in pts:
        assert p[u"id"] and p[u"state"] in ("GROUNDED", "POINTER_NOT_FOUND", "UNVERIFIABLE", "VALUE_MISMATCH"), p[u"id"]
        if p[u"state"] == "GROUNDED":
            ms = [PTR.match(x) for x in p[u"pointers"] if x.startswith("xbrl:")]
            els = [m.group(1) for m in ms]
            fm = [x for x in p[u"pointers"] if not x.startswith("xbrl:")]
            mk = p[u"参照先の印"]
            assert mk[u"差の式(formula:a-b)を持つ"] == any(x.startswith("formula:a-b") for x in fm), p[u"id"]
            assert mk[u"要素名に Change/Increase/Decrease/Ratio の語が在る"] == any(
                w in e.split(":", 1)[-1] for e in els for w in ("Change", "Increase", "Decrease", "Ratio")), p[u"id"]
        else:
            assert p[u"pointers"] == [] or p[u"state"] == "VALUE_MISMATCH", p[u"id"]
            assert u"参照先の印" not in p
    S = A[u"集計"]
    assert S[u"ポイントの claim"] == len(pts) and S[u"ポイントの state"] == tally(pts, u"state")
    g = sum(1 for p in pts if p[u"state"] == "GROUNDED")
    assert S[u"ポイントの GROUNDED"] == {u"件": g, u"分母": len(pts), u"率": round(100.0 * g / len(pts), 1)}
    pu = sum(1 for p in pts if p[u"state"] in ("POINTER_NOT_FOUND", "UNVERIFIABLE"))
    assert S[u"ポイントの POINTER_NOT_FOUND + UNVERIFIABLE"] == {u"件": pu, u"分母": len(pts), u"率": round(100.0 * pu / len(pts), 1)}
    pct = {}
    pct15 = {}
    for d in A[u"書類別"]:
        for k, v in d[u"％の claim の state"].items():
            pct[k] = pct.get(k, 0) + v
            if d[u"ポイントの claim"] > 0:
                pct15[k] = pct15.get(k, 0) + v
    assert dict(sorted(pct.items())) == S[u"％の state"] == FACT["pct_states"], u"％の state"
    assert dict(sorted(pct15.items())) == S[u"％の state(ポイントの claim がある書類だけ)"] == FACT["pct15_states"]
    assert S[u"％の claim"] == sum(pct.values()) == FACT["pct_claims"]
    gc = pct.get("GROUNDED", 0)
    assert S[u"％の GROUNDED"] == {u"件": gc, u"分母": sum(pct.values()), u"率": round(100.0 * gc / sum(pct.values()), 1)}
    assert S[u"％ − ポイント の GROUNDED の差(pt)"] == round(S[u"％の GROUNDED"][u"率"] - S[u"ポイントの GROUNDED"][u"率"], 1)
    assert S[u"印字(数字+ポイント)の合計"] == sum(d[u"印字(数字+ポイント)"] for d in A[u"書類別"]) == FACT["prints"]
    gr = [p for p in pts if p[u"state"] == "GROUNDED"]
    assert S[u"GROUNDED のポイント行のうち 差の式 formula:a-b を持つ"] == sum(1 for p in gr if p[u"参照先の印"][u"差の式(formula:a-b)を持つ"]) == FACT["grounded_formula"]
    assert S[u"GROUNDED のポイント行のうち 要素名に Change/Increase/Decrease/Ratio の語"] == sum(
        1 for p in gr if p[u"参照先の印"][u"要素名に Change/Increase/Decrease/Ratio の語が在る"]) == FACT["grounded_words"]
    assert S[u"span に ポイント を含むが単位がポイントでない claim の合計"] == sum(
        d[u"span に ポイント を含むが単位がポイントでない claim"] for d in A[u"書類別"]) == FACT["span_other_unit"]
    assert sorted((p[u"書類"], p[u"id"]) for p in gr) == sorted(READ_A4), u"GROUNDED のポイント行と文書の読みの対応"


def check_b(rec):
    B = rec[u"B"]
    rows, unmade = B[u"行"], B[u"作れない site"]
    text_docs = sorted(d[u"docID"] for d in rec[u"書類"] if d[u"区分"] == u"文あり")
    assert [s[u"書類"] for s in B[u"書類別"]] == text_docs, u"B の書類別が文ありの書類と違う"
    for s in B[u"書類別"]:
        mine = [r for r in rows if r[u"書類"] == s[u"書類"]]
        um = [u for u in unmade if u[u"書類"] == s[u"書類"]]
        assert s[u"作れた"] == len(mine) and s[u"作れない"] == len(um) and s[u"site"] == len(mine) + len(um), s[u"書類"]
        assert s[u"結果"] == tally(mine, u"結果"), s[u"書類"]
        assert s[u"土台の state が経営分析の文のままと同じ"] is True, s[u"書類"]
    # 行ごと
    for r in rows:
        assert r[u"結果"] == indep_kind(r), (r[u"書類"], r[u"id"], r[u"結果"])
        assert r[u"前期の枠"] == "Prior1Year" + r[u"当期の枠"][len("CurrentYear"):] and r[u"当期の枠"].startswith("CurrentYear"), r[u"id"]
        assert r[u"当期の fact"] > 0 and r[u"前期の fact"] > 0 and abs(r[u"当期の fact"] - r[u"前期の fact"]) > 1e-9, r[u"id"]
        a, b = digits_of(r[u"元の字"]), digits_of(r[u"後の字"])
        assert a != b and suffix_of(r[u"元の字"]) == suffix_of(r[u"後の字"]), r[u"id"]
        assert r[u"元の字"] in r[u"文脈 60 字"], r[u"id"]
        mult = SUFFIX_MULT[suffix_of(r[u"元の字"])]
        assert abs(float(b.replace(",", "")) * mult - r[u"前期の fact"]) <= max(1e-9, 1e-9 * r[u"前期の fact"]), (r[u"id"], u"後の字が前期の値を 1 字違わず書いていない")
        assert (len(a.split(".")[1]) if "." in a else 0) == (len(b.split(".")[1]) if "." in b else 0), r[u"id"]
        assert ("," in a) == ("," in b) or len(b.replace(",", "").split(".")[0]) <= 3, r[u"id"]
        if r[u"結果"] == K_ELSE:
            assert r[u"結果の細目"] in ("sentence_not_found", "id_shift", "missing"), r[u"id"]
        else:
            assert r[u"後の pointers"], r[u"id"]
    ids = [(r[u"書類"], r[u"id"]) for r in rows] + [(u[u"書類"], u[u"id"]) for u in unmade]
    assert len(ids) == len(set(ids)), u"site の重複"
    # 作れない site
    for u in unmade:
        why = u[u"作れない理由"]
        a = digits_of(u[u"元の字"])
        if why.startswith(u"数字部分が単純な数でない"):
            pre = u[u"元の字"]
            i = 0
            while not pre[i].isdigit():
                i += 1
            j = len(pre)
            while not pre[j - 1].isdigit():
                j -= 1
            assert not re.fullmatch(r"\d[\d,]*(?:\.\d+)?", pre[i:j]), (u[u"id"], pre)
        else:
            assert why == u"元の字の形では前期の値を 1 字違わず書けない", why
            assert re.fullmatch(r"\d[\d,]*(?:\.\d+)?", a)
            mult = SUFFIX_MULT[suffix_of(u[u"元の字"])]
            places = len(a.split(".")[1]) if "." in a else 0
            cand = round(u[u"前期の fact"] / mult, places)
            assert abs(cand * mult - u[u"前期の fact"]) > max(1e-9, 1e-9 * u[u"前期の fact"]), (u[u"id"], u"書けるのに作れないと数えた")
        assert u[u"作れた"] is False and u[u"後の字"] is None
    S = B[u"集計"]
    per_site = [s[u"site"] for s in B[u"書類別"]]
    per_made = [s[u"作れた"] for s in B[u"書類別"]]
    assert S[u"書類の数(分母)"] == len(text_docs) == FACT["with_text"]
    assert S[u"site"] == {u"合計": sum(per_site), u"書類あたり中央値": float(statistics.median(per_site)), u"書類あたり最大": max(per_site),
                          u"site が 0 の書類": sum(1 for x in per_site if x == 0)}
    assert (sum(per_site), float(statistics.median(per_site)), max(per_site)) == (FACT["sites"], FACT["site_median"], FACT["site_max"])
    assert S[u"作れた注入"] == {u"合計": len(rows), u"書類あたり中央値": float(statistics.median(per_made))}
    assert (len(rows), float(statistics.median(per_made))) == (FACT["made"], FACT["made_median"])
    assert sum(1 for x in per_made if x == 0) == FACT["docs_with_no_made"]
    assert S[u"作れない site"] == {u"合計": len(unmade), u"理由": tally(unmade, u"作れない理由")}
    assert len(unmade) == FACT["unmade"] and tally(unmade, u"作れない理由") == FACT["unmade_reasons"]
    res = tally(rows, u"結果")
    assert S[u"結果"] == res
    assert (res.get(K_STOP, 0), res.get(K_MOVED, 0), res.get(K_SAME, 0), res.get(K_OTHER, 0), res.get(K_ODD, 0), res.get(K_ELSE, 0)) == (
        FACT["stopped"], FACT["moved"], FACT["same_ref"], FACT["other_el"], FACT["odd"], FACT["else"])
    passed = sum(res.get(k, 0) for k in PASSED_KINDS)
    assert passed == FACT["passed"] and sum(res.values()) == len(rows)
    assert S[u"通した(GROUNDED のまま)合計"] == {u"件": passed, u"分母": len(rows), u"率": round(100.0 * passed / len(rows), 1)}
    mv = res.get(K_MOVED, 0)
    assert S[u"前期へ移って通した"] == {u"件": mv, u"分母": len(rows), u"率": round(100.0 * mv / len(rows), 1)}
    assert S[u"通した のうち参照先が Prior1Year でない"] == {u"件": passed - mv, u"分母": passed, u"率": round(100.0 * (passed - mv) / passed, 1)}
    by_unit = {}
    for r in rows:
        by_unit.setdefault(r[u"単位"], {})
        by_unit[r[u"単位"]][r[u"結果"]] = by_unit[r[u"単位"]].get(r[u"結果"], 0) + 1
    assert S[u"単位別の結果"] == {k: dict(sorted(v.items())) for k, v in sorted(by_unit.items())}
    assert S[u"前期へ移って通したうち 要素が同じ"] == sum(
        1 for r in rows if r[u"結果"] == K_MOVED and all(PTR.match(p).group(1) == r[u"要素"] for p in r[u"後の pointers"] if p.startswith("xbrl:")))


def check_record(rec):
    check_inputs(rec)
    check_a(rec)
    check_b(rec)


# ----------------------------------------------------------------------------------------------------------------
# 予測の判定(封の字から幅を読み、記録の行から門が求める)
def seal_cells(seal, tag):
    for l in seal.splitlines():
        if l.startswith(u"| **%s** |" % tag):
            return [c.strip() for c in l.strip().strip(u"|").split(u"|")]
    raise AssertionError(tag)


def seal_bounds(seal):
    b = {}
    c = seal_cells(seal, "A-1")[1]
    m = re.search(r"\*\*(\d+)〜(\d+) 件\*\*", c)
    b["A1"] = (int(m.group(1)), int(m.group(2)))
    c = seal_cells(seal, "A-2")[1]
    ms = re.findall(r"\*\*(\d+)〜(\d+)%\*\*", c)
    assert len(ms) == 2
    b["A2g"], b["A2pu"] = [(int(x), int(y)) for x, y in ms]
    b["A3"] = int(re.search(r"\*\*ポイントより (\d+) pt 以上高い\*\*", seal_cells(seal, "A-3")[1]).group(1))
    c = seal_cells(seal, "B-1")[1]
    m = re.search(r"中央値 (\d+)〜(\d+)\*\*", c)
    b["B1med"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"合計 \*\*(\d+)〜([\d,]+)\*\*", c)
    b["B1tot"] = (int(m.group(1)), int(m.group(2).replace(",", "")))
    m = re.search(r"割合は (\d+)〜(\d+)%\*\*", seal_cells(seal, "B-2")[1])
    b["B2"] = (int(m.group(1)), int(m.group(2)))
    b["B3"] = int(re.search(r"0〜(\d+)%", seal_cells(seal, "B-3")[1]).group(1))
    b["B4"] = int(re.search(r"\*\*合計 (\d+) 分以内\*\*", seal_cells(seal, "B-4")[1]).group(1)) * 60
    return b


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)


# 2026-10-20 追記(宣言された遷移): 封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md(期を縛る P22 の段 1。engine を変える。人間の承認 2026-10-20)で
# adapters/xbrl/recipes.py と vocabulary.py だけが動いた。この門が測った時点(封の commit)の engine は 0 行だった(記録の事実、消さない)。
# 「封の commit から 0 行」を満たしたと数えるのは、(a) 動いた file がこの 2 つだけ、(b) その封が履歴に在る、(c) sha16 が宣言どおり、のときだけ。
SEAL_PERIOD_BIND = "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md"
# 2026-10-21 追記(丸めの帯 P23 の段 1): 封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 truncate_abs_band・P23・PROFILES の登録を、
# recipes.py に _mag_trunc を足した。recipes.py の 65a37869f053a60e・vocabulary.py の 25a3c0992e10daaa は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P23 の段 1 の後の値のときだけ。
SEAL_ROUNDING = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"
SEAL_VOCAB = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"    # 2026-10-21 追記: 語彙の登録と枠の取り直し P24 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"    # 2026-10-21 追記: 最後の枝 P25 の段 1(下の ENGINE_LATER の遷移)
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"    # 2026-10-22 追記: P26 の段 1(下の ENGINE_LATER の遷移)
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_CUSTOMER_REPORT = "docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md"    # 2026-10-21 追記: 顧客向けの日本語の報告形(新しい module adapters/xbrl/report_customer.py。下の ENGINE_LATER の新規 file)
SEAL_CUSTOMER_REPORT_FIX = "docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md"    # 2026-10-21 追記: 顧客向けの報告形の直し(report_customer.py の中身だけ。下の ENGINE_LATER)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
SEAL_DEFAULT_P27 = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"    # 2026-10-28 追記: 既定を P26 -> P27 に切り替える 段 2(下の遷移。vocabulary.py の DEFAULT_PROFILE の 1 行と注記 +5 行・-1 行、verify_document.py の docstring の 1 行 +1 行・-1 行だけ)
SEAL_CAND = "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"    # 2026-10-30 追記: 候補の欄を足す(下の遷移)
# 2026-10-21(語彙の登録と枠の取り直し P24 の段 1): 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に旗 vocab_2026_10_21・frame_rebind の塊(+224 行・既存の行は 1 つも書き換えない)を足した(DEFAULT_PROFILE は P22 のまま)。
# d5308700eae78c10(P23 の段 1)は残す(測った時点の値)、P24 の段 1 で 3461c3f8b7af6675。受け入れるのは、その封が履歴に在り、値が P24 の段 1 の後の値のときだけ。
# 2026-10-21(最後の枝 P25 の段 1): 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に最後の枝の証拠の判定の塊(+72 行・-0 行。既存の行は 1 つも書き換えない)、vocabulary.py に旗 last_branch_names_only_if_evidence・P25・PROFILES の登録(+7 行・-0 行)、registry_setup.py に理由 no_same_value(+2 行)を足した(DEFAULT_PROFILE は P22 のまま)。
# recipes.py の 3461c3f8b7af6675・vocabulary.py の 83498c04a7b70396・registry_setup.py の 9a0b08954cf22639(P24 の段 1)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P25 の段 1 の後の値のときだけ。
# 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
ENGINE_LATER = {"adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27),
                # 2026-10-20 追記(段 2): vocabulary.py の sha は 段 1 3320c8c で 1fdb48e7e3ba58ce(残す。測った時点の値)、段 2(DEFAULT_PROFILE を
                # P21 -> P22 にし、決定の注記を足した。vocabulary.py だけ・recipes.py は 0 行。同じ封 SEAL_PERIOD_BIND の段 2)で 25a3c0992e10daaa。
                # 2026-10-21(語彙の登録と枠の取り直し P24 の段 1): 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 2 つ・資金の句の表・P24・PROFILES の登録を足した(DEFAULT_PROFILE は P22 のまま)。
                # f7b8d925eb6787ec(P23 の段 1)は残す(測った時点の値)、P24 の段 1 で 83498c04a7b70396。受け入れるのは、その封が履歴に在り、値が P24 の段 1 の後の値のときだけ。
                # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 5 つ・P26・PROFILES の登録(+17 行・-0 行) を足した。
                # 27e71e9861fc5aad(P25 の段 1)は残す(測った時点の値)、P26 の段 1 で 83025e9c0525d08b。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
                # 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
                # 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
                # 85896a67913ce1e7(P27 の段 2) は残す(測った時点の値。vocabulary.py の sha16)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 514ebb8104451c07。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
                # 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
                "adapters/xbrl/vocabulary.py": ("7fbcfbf0e472f366", SEAL_CAND),
                # 2026-10-21(P24 の段 1): registry_setup.py に理由 other_frame を足した(+2 行)。この file はこの門が測った時点では動いていない(封の commit から 0 行だった)。
                # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で registry_setup.py に理由 3 つ(+6 行) を足した。
                # f42ffe23aaa7673b(P25 の段 1)は残す(測った時点の値)、P26 の段 1 で 7f2cbded9c830211。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
                "adapters/xbrl/registry_setup.py": ("d6f25750bcd73c0a", SEAL_P27),
                # 2026-10-21(顧客向けの日本語の報告形): 封 docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md(engine 側に module を足す。人間の事前承認 2026-10-21)で、新しい file adapters/xbrl/report_customer.py を足した
                # (既存の file は 1 字も触らない。report.py・verify_document.py・vocabulary.py・recipes.py・registry_setup.py は 0 行)。新規 file なので「測った時点の値」は無い。受け入れるのは、その封が履歴に在り、sha16 が下の値のときだけ。
                # d82481697762d167(段 1 の c13a746)は残す(測った時点の値)。2026-10-21 追記(顧客向けの報告形の直し。封 docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md が
                # module の中身だけを直す。判定と節の割り当ては変えない)で 715468699973cc4a。受け入れるのは、その封が履歴に在り、値が直した後の値のときだけ。
                # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で report_customer.py の理由の表に 3 行(+7 行・-2 行。判定と節の割り当ては変えない) を足した。
                # 715468699973cc4a(報告形の直し 段 1)は残す(測った時点の値)、P26 の段 1 で 141767d189b63733。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
                # 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
                "adapters/xbrl/report_customer.py": ("bdbaa00a419219fe", SEAL_CAND),
                # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で extract.py に数の読み取りの足し(+42 行・-0 行)を足した。この file はこの門が測った時点では動いていない(封の commit から 0 行だった)。
                "adapters/xbrl/extract.py": ("3cf55966f12919f0", SEAL_P27),
                # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1 が宣言した遷移。verify_document.py の docstring の 1 行(+1 行・-1 行。実行の字は変えない)。
                # 受け入れるのは、その封が履歴に在り、値が下の値のときだけ。
                # 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
                "adapters/xbrl/verify_document.py": ("6c76c8ade6c7b1c8", SEAL_CAND)}


def only_declared_changes(numstat_out, status_out):
    paths = [l.split("\t")[-1] for l in numstat_out.splitlines() if l.strip()] + [l[3:] for l in status_out.splitlines() if l.strip()]
    rels = sorted(set(p[len("audit-core/"):] if p.startswith("audit-core/") else p for p in paths))
    for rel in rels:
        if rel not in ENGINE_LATER:
            return False
        later, seal_rel = ENGINE_LATER[rel]
        added = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", seal_rel], cwd=ROOT, capture_output=True, text=True).stdout.split()
        with io.open(os.path.join(ROOT, rel), "rb") as fh:
            if not added or hashlib.sha256(fh.read()).hexdigest()[:16] != later:
                return False
    return True


def engine_untouched():
    u"""封が最初に入った commit から、engine・false_pass・inject が 0 行(差も未追跡も無い)。git が使えなければ None。"""
    r = git("log", "--diff-filter=A", "--format=%H", "--", SEAL_REL)
    shas = r.stdout.split()
    if r.returncode != 0 or not shas:
        return None
    base = shas[-1]
    d1 = git("diff", base, "--numstat", "--", *GUARDED)
    d2 = git("status", "--porcelain", "--", *GUARDED)
    return d1.returncode == 0 and (d1.stdout == "" and d2.stdout == "" or only_declared_changes(d1.stdout, d2.stdout))


def judge_indep(rec, seal):
    b = seal_bounds(seal)
    A, B = rec[u"A"], rec[u"B"]
    pts = A[u"行"]
    n = len(pts)
    g = sum(1 for p in pts if p[u"state"] == "GROUNDED")
    pu = sum(1 for p in pts if p[u"state"] in ("POINTER_NOT_FOUND", "UNVERIFIABLE"))
    pct = {}
    for d in A[u"書類別"]:
        for k, v in d[u"％の claim の state"].items():
            pct[k] = pct.get(k, 0) + v
    gp, pup = 100.0 * g / n, 100.0 * pu / n
    gc = 100.0 * pct["GROUNDED"] / sum(pct.values())
    out = {}
    out["A-1"] = b["A1"][0] <= n <= b["A1"][1]
    out["A-2"] = b["A2g"][0] <= round(gp, 1) <= b["A2g"][1] and b["A2pu"][0] <= round(pup, 1) <= b["A2pu"][1]
    out["A-3"] = round(gc, 1) - round(gp, 1) >= b["A3"] - 1e-9
    rows, unmade = B[u"行"], B[u"作れない site"]
    per_site = [s[u"site"] for s in B[u"書類別"]]
    tot = sum(per_site)
    out["B-1"] = b["B1med"][0] <= statistics.median(per_site) <= b["B1med"][1] and b["B1tot"][0] <= tot <= b["B1tot"][1]
    moved = sum(1 for r in rows if indep_kind(r) == K_MOVED)
    passed = sum(1 for r in rows if indep_kind(r) in PASSED_KINDS)
    out["B-2"] = b["B2"][0] <= round(100.0 * moved / len(rows), 1) <= b["B2"][1]
    out["B-3"] = round(100.0 * (passed - moved) / passed, 1) <= b["B3"]
    out["B-4"] = rec[u"所要秒"][u"全体"] <= b["B4"]
    out["B-5"] = engine_untouched()
    return out


LABEL = {True: u"当たり", False: u"外れ"}


def check_judgments(rec, seal):
    j = judge_indep(rec, seal)
    rj = rec[u"予測の判定"]
    assert sorted(rj) == ["A-1", "A-2", "A-3", "A-4", "B-1", "B-2", "B-3", "B-4", "B-5"], u"判定の欄"
    for k, ok in j.items():
        if k == "B-5":
            assert ok is not None
            assert rj[k][u"判定"].startswith(u"engine の部分は 当たり" if ok else u"外れ"), (k, rj[k])
        else:
            assert rj[k][u"判定"] == LABEL[ok], (k, rj[k][u"判定"], ok)
    assert rj["A-4"][u"判定"] == u"判定は文書で(人の読み)"
    return j


def import_script():
    sp = importlib.util.spec_from_file_location("point_prior_script_for_gate", SCRIPT)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# ----------------------------------------------------------------------------------------------------------------
# 文書の表(記録から作った字)
def a_dist_lines(rec):
    S = rec[u"A"][u"集計"]

    def line(label, n, st):
        return u"| %s | %d | %d | %d | %d | %d | %s |" % (
            label, n, st.get("GROUNDED", 0), st.get("POINTER_NOT_FOUND", 0), st.get("UNVERIFIABLE", 0), st.get("VALUE_MISMATCH", 0),
            F(st.get("GROUNDED", 0), n))
    return [line(u"単位ポイント(文を持つ 67 書類。claim が在る書類は 15)", S[u"ポイントの claim"], S[u"ポイントの state"]),
            line(u"単位 ％(同じ 67 書類)", S[u"％の claim"], S[u"％の state"]),
            line(u"単位 ％(ポイントの claim が在る 15 書類だけ)", sum(S[u"％の state(ポイントの claim がある書類だけ)"].values()),
                 S[u"％の state(ポイントの claim がある書類だけ)"])]


def a_reason_lines(rec):
    t = tally(rec[u"A"][u"行"], u"reason")
    return [u"| `%s` | %d |" % (k, v) for k, v in t.items()]


def a_points_lines(rec):
    return [u"| %s | %s | %s | %s | %s | %s |" % (
        p[u"書類"], p[u"id"], p[u"値"], p[u"state"], p[u"reason"] if p[u"reason"] else u"(なし)", cell(p[u"文脈 60 字"] or p[u"span"]))
        for p in rec[u"A"][u"行"]]


def a_grounded_lines(rec):
    out = []
    for p in rec[u"A"][u"行"]:
        if p[u"state"] != "GROUNDED":
            continue
        mk = p[u"参照先の印"]
        els = u" ・ ".join(u"`%s@%s`" % (e[u"要素"], e[u"枠"]) for e in mk[u"xbrl の参照先"])
        out.append(u"| %s | %s | %s | %s | %s %s | %s | %s | %s |" % (
            p[u"書類"], p[u"id"], p[u"値"], p[u"再計算"], els, u"+ `%s`" % u"`・`".join(mk[u"式の pointer"]) if mk[u"式の pointer"] else u"",
            u"在る" if mk[u"要素名に Change/Increase/Decrease/Ratio の語が在る"] else u"無い",
            u"在る" if mk[u"差の式(formula:a-b)を持つ"] else u"無い", READ_A4[(p[u"書類"], p[u"id"])]))
    return out


def b_unit_lines(rec):
    out = []
    for u, v in rec[u"B"][u"集計"][u"単位別の結果"].items():
        n = sum(v.values())
        out.append(u"| %s | %d | %d | %d | %d | %d | %d |" % (
            u, n, v.get(K_STOP, 0), v.get(K_MOVED, 0), v.get(K_SAME, 0), v.get(K_OTHER, 0) + v.get(K_ODD, 0), v.get(K_ELSE, 0)))
    return out


def b_doc_lines(rec):
    out = []
    for s in rec[u"B"][u"書類別"]:
        r = s[u"結果"]
        out.append(u"| %s | %d | %d | %d | %d | %d | %d | %d |" % (
            s[u"書類"], s[u"site"], s[u"作れた"], s[u"作れない"], r.get(K_STOP, 0), r.get(K_MOVED, 0),
            r.get(K_SAME, 0) + r.get(K_OTHER, 0) + r.get(K_ODD, 0), r.get(K_ELSE, 0)))
    return out


def b_unmade_lines(rec):
    return [u"| %s | %d |" % (k, v) for k, v in rec[u"B"][u"集計"][u"作れない site"][u"理由"].items()]


def b_example_lines(rec):
    rows = dict(((r[u"書類"], r[u"id"]), r) for r in rec[u"B"][u"行"])
    out = []
    for key in EXAMPLES:
        r = rows[key]
        out.append(u"| %s | %s | `%s` | `%s` | `xbrl:%s@%s` | %s | %s | %s |" % (
            r[u"書類"], r[u"id"], r[u"元の字"], r[u"後の字"], r[u"要素"], r[u"当期の枠"],
            u" ・ ".join(u"`%s`" % p for p in r[u"後の pointers"]), r[u"結果"], cell(r[u"文脈 60 字"])))
    return out


def block(lines):
    return u"\n".join(lines)


def pred_rows(doc):
    out = {}
    for l in doc.splitlines():
        m = re.match(r"\| \*\*([AB]-\d)\*\* \|", l)
        if m:
            out[m.group(1)] = [c.strip() for c in l.strip().strip(u"|").split(u"|")]
    return out


A4_LABEL = u"外れ"          # 人の読み(GROUNDED のポイント 4 行はいずれも正しく結べた = 過半が正しく結べた)
HEADINGS = (u"## 0. 結論", u"## 1. 予測 A-1〜A-4・B-1〜B-5", u"## 2. 穴 A", u"## 3. 穴 B", u"## 4. 限界", u"## 5. 変異", u"## 6. 再現")


def doc_section(doc, head):
    u"""``head`` で始まる ``## `` の節(次の ``\n## `` の前まで)。"""
    i = doc.index(head)
    j = doc.find(u"\n## ", i + 1)
    return doc[i:j] if j >= 0 else doc[i:]


def check_conclusion(rec, doc):
    u"""結論(§0)・A-3 の行・§3-1 の数を、記録から作った字で縛る(数を 1 字変えると、算術が合っていても赤)。
    あわせて、経路の違い(段 2 の α 型と文書経路)・B-2 の意味・後追いの 1 行・監査席の概算の注記が書かれていること。"""
    A, B = rec[u"A"][u"集計"], rec[u"B"][u"集計"]
    pts, pc = A[u"ポイントの GROUNDED"], A[u"％の GROUNDED"]
    c15 = A[u"％の state(ポイントの claim がある書類だけ)"]
    r15 = round(100.0 * c15["GROUNDED"] / sum(c15.values()), 1)
    res = B[u"結果"]
    n = B[u"作れた注入"][u"合計"]
    amount = sum(v for u, d in B[u"単位別の結果"].items() if u in (u"千円", u"百万円", u"円") for v in d.values())
    amount_moved = sum(d.get(K_MOVED, 0) for u, d in B[u"単位別の結果"].items() if u in (u"千円", u"百万円", u"円"))
    pct_all = sum(B[u"単位別の結果"][u"%"].values())
    pct_stop = B[u"単位別の結果"][u"%"].get(K_STOP, 0)
    pnf_u = A[u"ポイントの POINTER_NOT_FOUND + UNVERIFIABLE"]
    s0 = doc_section(doc, u"## 0. 結論")
    s1 = doc_section(doc, u"## 1. 予測")
    s3 = doc_section(doc, u"## 3. 穴 B")
    s4 = doc_section(doc, u"## 4. 限界")
    s5 = doc_section(doc, u"## 5. 変異")
    s6 = doc_section(doc, u"## 6. 再現")
    want0 = [
        u"単位ポイントの claim は %d 件(%d 書類)" % (A[u"ポイントの claim"], A[u"ポイントの claim がある書類"]),
        u"GROUNDED にしたのは %s だけ" % F(pts[u"件"], pts[u"分母"]),
        u"単位 ％ の claim は %s で、ポイントは **%.1f pt 低い**" % (F(pc[u"件"], pc[u"分母"]), A[u"％ − ポイント の GROUNDED の差(pt)"]),
        u"**%s を通した**" % F(res[K_MOVED], n),
        u"率(`%`)の注入 " + u"%d は止めた %d" % (pct_all, pct_stop),
        u"作れた注入は site %d の %d(%.1f%%)" % (B[u"site"][u"合計"], n, 100.0 * n / B[u"site"][u"合計"]),
        u"(1) 作れた注入の範囲で、金額の主張は前期の値でも GROUNDED のまま通る(%s)" % F(amount_moved, amount),
        u"(2) 率の主張は止める(%s)" % F(pct_stop, pct_all),
        u"(3) ポイントの行は reason が『要素が無い』『主語が無い』などの行で止まる(%s が POINTER_NOT_FOUND か UNVERIFIABLE)" % F(pnf_u[u"件"], pnf_u[u"分母"]),
    ]
    for w in want0:
        assert w in s0, (u"§0 の結論に無い/違う", w)
    assert u"ポイントの claim が在る 15 書類だけの％でも %s で、差は %.1f pt(20 pt 以上)" % (
        F(c15["GROUNDED"], sum(c15.values())), r15 - pts[u"率"]) in s1, u"A-3 の行の 15 書類の数"
    other = res.get(K_ELSE, 0)
    want3 = [
        u"site 合計 %d(書類あたり中央値 %.1f" % (B[u"site"][u"合計"], B[u"site"][u"書類あたり中央値"]),
        u"作れた注入 %d(書類あたり中央値 %.1f)" % (n, B[u"作れた注入"][u"書類あたり中央値"]),
        u"止めた %d・通した(参照先が前期へ移った)%d・通した(参照先が当期の同じ参照先のまま)%d・通した(参照先が当期の別要素)%d・その他 %d" % (
            res[K_STOP], res[K_MOVED], res.get(K_SAME, 0), res.get(K_OTHER, 0), other),
        u"**前期へ移って通した %s**" % F(res[K_MOVED], n),
        u"その他 %d を除くと %s" % (other, F(res[K_MOVED], n - other)),
    ]
    for w in want3:
        assert w in s3, (u"§3-1 に無い/違う", w)
    # 経路の違い(D-2)・B-2 の意味と原因(D-3)・後追い(D-4)・監査席の概算(D-6)
    for w in (u"α 型(席の参照先を `verify_external` に渡す経路)", u"文書経路 `verify_document` で Core 自身が抽出して付けた理由",
              u"段 2 の『単位語の規則が止める』の読みは文書経路には当てはまらない"):
        assert w in s0, (u"§0 に経路の違いが無い", w)
    for w in (u"期間を縛らない", u"別の封(人間の承認)", u"**コードを読んだ原因**で、測った原因ではない", u"`_direct_value_claim`",
              u"`_prior_cue` は並べ替えだけ", u"`want` を `CurrentYear` に固定"):
        assert w in s0, (u"§0 に B-2 の意味・原因が無い", w)
    assert u"`judge(記録) == 記録の判定` は 9 キー一致" in s6 and u"`--stage all` のときだけ" in s6, u"§6 の後追いの 1 行"
    assert len(rec[u"予測の判定"]) == 9
    for w in (u"**監査席の概算**(この封の測定ではなく", u"336", u"186", u"459", u"`_prior_cue` は 459 件すべてで偽"):
        assert w in s4, (u"§4 に監査席の概算の注記が無い", w)
    assert u"### 5-3." in s5


def check_doc(rec, doc, seal):
    j = check_judgments(rec, seal)
    for h in HEADINGS:
        assert doc.count(h) == 1, h
    rows = pred_rows(doc)
    assert sorted(rows) == sorted(rec[u"予測の判定"]), u"予測の表の行"
    for k, cells in rows.items():
        assert len(cells) == 4, k
        assert cells[1] == seal_cells(seal, k)[1], u"%s の予測欄が封の字と違う" % k
        want = A4_LABEL if k == "A-4" else LABEL[bool(j[k])]
        assert cells[3].startswith(u"**%s**" % want), (k, cells[3])
        if k != "A-4":
            assert rec[u"予測の判定"][k][u"実測"] in cells[2], (k, u"実測の欄が記録の字を含まない")
    n_hit = sum(1 for k in rows if rows[k][3].startswith(u"**当たり**"))
    n_miss = sum(1 for k in rows if rows[k][3].startswith(u"**外れ**"))
    assert (n_hit, n_miss) == (7, 2) and n_hit + n_miss == 9
    assert u"**予測 当たり %d / 外れ %d**" % (n_hit, n_miss) in doc
    for lines in (a_dist_lines(rec), a_reason_lines(rec), a_points_lines(rec), a_grounded_lines(rec), b_unit_lines(rec),
                  b_doc_lines(rec), b_unmade_lines(rec), b_example_lines(rec)):
        assert block(lines) in doc, lines[0]
    assert sum(1 for l in doc.splitlines() if re.match(r"\| S100\w{4} \| \d+ \| \d+ \| \d+ \| \d+ \| \d+ \| \d+ \| \d+ \|$", l)) == FACT["with_text"]
    # 率は a / b = x.x%
    found = FRAC_RE.findall(doc)
    assert len(found) >= 10
    for a, b, p in found:
        a_, b_ = int(a.replace(",", "")), int(b.replace(",", ""))
        assert "%.1f" % (100.0 * a_ / b_) == p, (a, b, p)
    S, B = rec[u"A"][u"集計"], rec[u"B"][u"集計"]
    for a_, b_ in ((S[u"ポイントの GROUNDED"][u"件"], S[u"ポイントの GROUNDED"][u"分母"]), (S[u"％の GROUNDED"][u"件"], S[u"％の GROUNDED"][u"分母"]),
                   (B[u"前期へ移って通した"][u"件"], B[u"前期へ移って通した"][u"分母"]),
                   (B[u"通した のうち参照先が Prior1Year でない"][u"件"], B[u"通した のうち参照先が Prior1Year でない"][u"分母"])):
        assert F(a_, b_) in doc, F(a_, b_)
    check_conclusion(rec, doc)
    for s in (u"**API 鍵なし・0 USD・通信なし・engine(`core/`・`adapters/`)0 行。**", u"python3 measure/xbrl_point_prior_2026-10-20.py --stage all",
              u"python3 -m pytest -q tests/measure/test_xbrl_point_prior_result.py", u"AUDIT_CORE_POINT_PRIOR=1",
              u"束ねた sha256 `%s`" % ENGINE_BUNDLE, u"HEAD `%s`" % rec[u"環境"][u"HEAD"],
              u"書類の一覧の digest `%s`" % INPUT_DIGEST, u"**縛っていないもの**", u"無作為ではない",
              u"jpsps…-asr-", u"jpcrp…-asr-", u"前期の値 ±1", u"--batch 1", u"人の読み"):
        assert s in doc, s
    return j


# ----------------------------------------------------------------------------------------------------------------
class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads(jtext(REC))
        cls.doc = jtext(DOC)
        cls.seal = jtext(SEAL)


class RecordTest(Base):
    def test_1_inputs_are_pinned_literally(self):
        check_inputs(self.rec)

    def test_2_record_rows_recount_to_the_aggregates_and_the_facts(self):
        check_record(self.rec)

    def test_3_judgments_recomputed_equal_the_script_and_the_record(self):
        j = check_judgments(self.rec, self.seal)
        self.assertEqual([k for k, v in sorted(j.items()) if v is False], ["B-2"])
        self.assertEqual(sorted(k for k, v in j.items() if v is True), ["A-1", "A-2", "A-3", "B-1", "B-3", "B-4", "B-5"])
        # script の judge(純関数)を記録に当てると記録の判定と同じ
        PP = import_script()
        self.assertEqual(PP.judge(self.rec), self.rec[u"予測の判定"])

    def test_4_a_four_is_a_human_reading_and_not_decided_by_the_machine(self):
        self.assertEqual(self.rec[u"予測の判定"]["A-4"][u"判定"], u"判定は文書で(人の読み)")
        self.assertEqual(len(READ_A4), 4)
        self.assertTrue(all(v.startswith(u"正しく結べた") for v in READ_A4.values()))

    def test_5_every_document_in_the_record_is_the_cache_file_when_the_cache_exists(self):
        if not os.path.isdir(CACHE):
            self.skipTest(u"cache(~/.cache/audit-core/edinet)が無い機械")
        got = {}
        for fn in os.listdir(CACHE):
            if fn.endswith(".zip"):
                with io.open(os.path.join(CACHE, fn), "rb") as fh:
                    b = fh.read()
                got[fn[:-4]] = (hashlib.sha256(b).hexdigest(), len(b))
        want = dict((d[u"docID"], (d[u"sha256"], d[u"bytes"])) for d in self.rec[u"書類"])
        self.assertEqual(got, want, u"cache の書類が記録の書類と違う(記録を採った cache と別の機械)")


class DocTest(Base):
    def test_6_the_document_equals_what_the_record_says(self):
        check_doc(self.rec, self.doc, self.seal)

    def test_7_seal_and_engine_are_untouched_since_the_seal_commit(self):
        r = git("log", "--diff-filter=A", "--format=%H", "--", SEAL_REL)
        shas = r.stdout.split()
        if r.returncode != 0 or not shas:
            self.skipTest(u"封がまだ git の履歴に無い / git が使えない")
        base = shas[-1]
        self.assertEqual(git("diff", base, "--numstat", "--", SEAL_REL).stdout, "", u"封が封の commit から変わった")
        self.assertEqual(git("status", "--porcelain", "--", SEAL_REL).stdout, "")
        self.assertTrue(engine_untouched(), u"engine・false_pass・inject が封の commit から動いた")

    def test_8_the_seal_still_says_the_pre_registered_predictions(self):
        # 封の本文は結果の後も同じ(予測の字を文書が写している ― 文書の予測欄は封の字と完全一致)
        for k in ("A-1", "A-2", "A-3", "A-4", "B-1", "B-2", "B-3", "B-4", "B-5"):
            self.assertIn(seal_cells(self.seal, k)[1], self.doc)
        self.assertIn(u"**数を見てから封・予測を直さない。外れは外れとして残す。**", self.seal)


class ScriptTest(Base):
    def test_9_script_never_names_the_network_and_reads_only_the_cache(self):
        tree = ast.parse(jtext(SCRIPT))
        imported = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imported |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                imported.add((n.module or "").split(".")[0])
        self.assertFalse(imported & {"urllib", "socket", "http", "requests", "ssl", "anthropic", "openai", "httpx", "ftplib", "smtplib"}, imported)
        src = jtext(SCRIPT)
        for k in ("ANTHROPIC_API_KEY", "EDINET_API_KEY", "OPENAI_API_KEY"):
            # 鍵は名前の一覧にだけ在る(os.environ[...] / getenv で値を読まない)
            self.assertNotIn("os.environ[\"%s\"]" % k, src)
            self.assertNotIn("getenv(\"%s\"" % k, src)
        self.assertNotIn("os.environ.get(", src)
        adds = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument"]
        self.assertEqual([a.args[0].value for a in adds], ["--stage", "--out", "--docs"])


class LightRerunTest(Base):
    u"""cache とラベルが在る機械では、2 書類(S100YMFV・S100YYIA)を script で走らせ直して記録の該当行と一致。"""

    def test_10_two_documents_rerun_equal_the_record(self):
        for doc_id in LIGHT_DOCS:
            if not os.path.exists(os.path.join(CACHE, doc_id + ".zip")):
                self.skipTest(u"cache に %s が無い機械" % doc_id)
        PP = import_script()
        _sh, why = PP._load_ritual().check_labels()
        if why:
            self.skipTest(u"標準タクソノミのラベルが無い機械(%s)" % why)
        rt = lambda x: json.loads(json.dumps(x, ensure_ascii=False))
        A, B = self.rec[u"A"], self.rec[u"B"]
        n_pts = n_rows = n_batches = 0
        for doc_id in LIGHT_DOCS:
            with io.open(os.path.join(CACHE, doc_id + ".zip"), "rb") as fh:
                zb = fh.read()
            want = [d for d in self.rec[u"書類"] if d[u"docID"] == doc_id][0]
            self.assertEqual(hashlib.sha256(zb).hexdigest(), want[u"sha256"])
            cat, _why, text = PP.classify_doc(zb)
            self.assertEqual(cat, want[u"区分"])
            d, pts = PP.doc_a(doc_id, zb, text)
            self.assertEqual(rt(d), [x for x in A[u"書類別"] if x[u"書類"] == doc_id][0])
            self.assertEqual(rt(pts), [x for x in A[u"行"] if x[u"書類"] == doc_id])
            s, rows, um = PP.doc_b(doc_id, zb, text)
            self.assertEqual(rt(s), [x for x in B[u"書類別"] if x[u"書類"] == doc_id][0])
            self.assertEqual(rt(rows), [x for x in B[u"行"] if x[u"書類"] == doc_id])
            self.assertEqual(rt(um), [x for x in B[u"作れない site"] if x[u"書類"] == doc_id])
            n_pts += len(pts)
            n_rows += len(rows)
            n_batches += (len(rows) + 24) // 25
        self.assertGreater(n_pts, 0)
        self.assertGreater(n_rows, 25)
        self.assertGreaterEqual(n_batches, 3)


@unittest.skipUnless(RUN_HEAVY, HEAVY_SKIP_REASON)
class HeavyRerunTest(Base):
    def test_11_full_rerun_equals_the_record(self):
        if not os.path.isdir(CACHE):
            self.fail(u"AUDIT_CORE_POINT_PRIOR=1 を指定したが cache が無い")
        PP = import_script()
        _sh, why = PP._load_ritual().check_labels()
        if why:
            self.fail(u"AUDIT_CORE_POINT_PRIOR=1 を指定したがラベル 2 file が無い: " + why)
        out = PP.run("all")
        rt = lambda x: json.loads(json.dumps(x, ensure_ascii=False))
        out = rt(out)
        for k in (u"書類", u"書類の数", u"A", u"B"):
            self.assertEqual(out[k], self.rec[k], k)
        a = dict(out[u"予測の判定"])
        b = dict(self.rec[u"予測の判定"])
        a.pop("B-4")
        b.pop("B-4")
        # 2026-10-20(期を縛る P22 の段 2): B-5 は『作業木の git diff HEAD の行数』をその場で数えた値で、測った時点(封の commit)は 0 だった。
        # engine を宣言された遷移(段 1・段 2。ENGINE_LATER)で変えた木では、commit 前は 0 でなく、commit 後に 0 に戻る ― 走らせ直しの度に
        # 木の状態で変わる値なので等号の外に置く(engine が封の commit から宣言された遷移だけであることは test_7 の engine_untouched() が sha16 で縛る)。
        a.pop("B-5")
        b.pop("B-5")
        self.assertEqual(a, b)
        self.assertLessEqual(out[u"所要秒"][u"全体"], 1800)


# ----------------------------------------------------------------------------------------------------------------
class MutationTest(Base):
    u"""門が壊れた標本で赤くなること(毎回走らせる)。壊した後の標本に本物と同じ検査関数を当てる。"""

    def red(self, fn, *a):
        with self.assertRaises(AssertionError):
            fn(*a)

    def test_m0_the_genuine_samples_pass(self):
        check_record(self.rec)
        check_doc(self.rec, self.doc, self.seal)

    def test_m1_changing_one_input_document_is_red(self):
        bad = copy.deepcopy(self.rec)
        bad[u"書類"][0][u"sha256"] = u"f" + bad[u"書類"][0][u"sha256"][1:] if bad[u"書類"][0][u"sha256"][0] != u"f" else u"0" + bad[u"書類"][0][u"sha256"][1:]
        self.red(check_record, bad)
        bad = copy.deepcopy(self.rec)
        bad[u"書類"][3][u"区分"] = u"文なし" if bad[u"書類"][3][u"区分"] == u"文あり" else u"文あり"
        self.red(check_record, bad)
        bad = copy.deepcopy(self.rec)
        del bad[u"書類"][5]
        self.red(check_record, bad)

    def test_m2_a_point_row_state_or_a_deleted_row_is_red(self):
        bad = copy.deepcopy(self.rec)
        row = [p for p in bad[u"A"][u"行"] if p[u"state"] == "POINTER_NOT_FOUND"][0]
        row[u"state"] = "GROUNDED"
        self.red(check_record, bad)
        bad = copy.deepcopy(self.rec)
        del bad[u"A"][u"行"][0]
        self.red(check_record, bad)
        bad = copy.deepcopy(self.rec)
        bad[u"A"][u"行"][1][u"値"] = 99.0   # 値は分布に効かないが、文書の 29 行の表とは食い違う
        self.red(check_doc, bad, self.doc, self.seal)

    def test_m3_a_b_row_flipped_from_passed_to_stopped_is_red(self):
        bad = copy.deepcopy(self.rec)
        row = [r for r in bad[u"B"][u"行"] if r[u"結果"] == K_MOVED][0]
        row[u"結果"] = K_STOP
        self.red(check_record, bad)
        # 行は直したが集計を直していない
        bad = copy.deepcopy(self.rec)
        row = [r for r in bad[u"B"][u"行"] if r[u"結果"] == K_MOVED][0]
        row[u"結果"] = K_STOP
        row[u"結果の細目"] = "VALUE_MISMATCH"
        self.red(check_record, bad)

    def test_m4_a_pointer_that_does_not_move_to_the_prior_year_is_red(self):
        bad = copy.deepcopy(self.rec)
        row = [r for r in bad[u"B"][u"行"] if r[u"結果"] == K_MOVED][0]
        row[u"後の pointers"] = [p.replace("Prior1Year", "CurrentYear") for p in row[u"後の pointers"]]
        self.red(check_record, bad)

    def test_m5_a_wrong_replacement_digit_is_red(self):
        bad = copy.deepcopy(self.rec)
        row = [r for r in bad[u"B"][u"行"] if r[u"結果"] == K_MOVED][0]
        d = digits_of(row[u"後の字"])
        nd = d[:-1] + str((int(d[-1]) + 1) % 10)
        row[u"後の字"] = row[u"後の字"].replace(d, nd)
        self.red(check_record, bad)

    def test_m6_a_site_moved_between_made_and_unmade_is_red(self):
        bad = copy.deepcopy(self.rec)
        row = bad[u"B"][u"行"].pop(0)
        self.red(check_record, bad)
        bad = copy.deepcopy(self.rec)
        bad[u"B"][u"作れない site"][0][u"作れない理由"] = u"数字部分が単純な数でない(複合表記。例 13億51百万円)" if bad[u"B"][u"作れない site"][0][u"作れない理由"].startswith(u"元の字") else u"元の字の形では前期の値を 1 字違わず書けない"
        self.red(check_record, bad)

    def test_m7_a_changed_judgment_is_red(self):
        for k, new in (("B-2", u"当たり"), ("A-3", u"外れ"), ("B-3", u"外れ")):
            bad = copy.deepcopy(self.rec)
            bad[u"予測の判定"][k][u"判定"] = new
            self.red(check_judgments, bad, self.seal)
        # 封の幅を変えた標本(封を 1 字変えると、判定の求め直しが記録の判定とずれる)
        bad_seal = self.seal.replace(u"**30〜70%**", u"**30〜95%**").replace(u"割合は 30〜70%**", u"割合は 30〜95%**")
        self.assertNotEqual(bad_seal, self.seal)
        self.red(check_judgments, self.rec, bad_seal)

    def test_m8_a_changed_number_or_table_line_in_the_document_is_red(self):
        for needle, new in ((u"458 / 485 = 94.4%", u"458 / 485 = 94.3%"), (u"4 / 29 = 13.8%", u"4 / 29 = 13.9%"),
                            (u"**予測 当たり 7 / 外れ 2**", u"**予測 当たり 8 / 外れ 1**")):
            self.assertIn(needle, self.doc)
            self.red(check_doc, self.rec, self.doc.replace(needle, new), self.seal)   # 同じ字は文書に複数在る。全部を変える
        # 書類別の表の 1 行
        line = b_doc_lines(self.rec)[7]
        self.assertIn(line, self.doc)
        self.red(check_doc, self.rec, self.doc.replace(line, line.replace(u"| ", u"| 9", 2)[:-1] + u" |", 1), self.seal)
        # 予測の欄(封の字)を直す
        cells = seal_cells(self.seal, "B-2")
        self.red(check_doc, self.rec, self.doc.replace(cells[1], cells[1].replace(u"30〜70%", u"30〜95%"), 1), self.seal)
        # 判定の欄
        self.red(check_doc, self.rec, self.doc.replace(u"| **B-2** |", u"| **B-2** |", 1).replace(u"**外れ**", u"**当たり**", 1), self.seal)

    def test_m11_a_changed_conclusion_number_is_red_even_when_the_arithmetic_holds(self):
        u"""結論の数を 1 字変える(算術が合う書き換えを含む)と赤。同じ字が複数箇所に在る数は全部ではなく 1 か所だけ変える。"""
        cases = ((u"**29.5 pt 低い**", u"**29.6 pt 低い**"), (u"差は 23.9 pt(20 pt 以上)", u"差は 24.9 pt(20 pt 以上)"),
                 (u"485(62.8%)", u"485(63.8%)"), (u"止めた 24・通した", u"止めた 25・通した"),
                 (u"(1) 作れた注入の範囲で、金額の主張は前期の値でも GROUNDED のまま通る(458 / 460 = 99.6%)",
                  u"(1) 作れた注入の範囲で、金額の主張は前期の値でも GROUNDED のまま通る(457 / 460 = 99.3%)"),
                 (u"(2) 率の主張は止める(23 / 24 = 95.8%)", u"(2) 率の主張は止める(22 / 24 = 91.7%)"),
                 (u"(24 / 29 = 82.8% が POINTER_NOT_FOUND", u"(23 / 29 = 79.3% が POINTER_NOT_FOUND"),
                 (u"その他 2 を除くと 458 / 483 = 94.8%", u"その他 2 を除くと 458 / 483 = 94.9%"),
                 (u"α 型(席の参照先を `verify_external` に渡す経路)", u"α 型(席の参照先を `verify_x` に渡す経路)"), (u"**コードを読んだ原因**で、測った原因ではない", u"**測った原因**"),
                 (u"`judge(記録) == 記録の判定` は 9 キー一致", u"`judge(記録) == 記録の判定`"),
                 (u"**監査席の概算**(この封の測定ではなく", u"**概算**(この封の測定ではなく"))
        for old, new in cases:
            self.assertEqual(self.doc.count(old), 1, old)
            self.red(check_doc, self.rec, self.doc.replace(old, new), self.seal)

    def test_m9_independent_kind_function_distinguishes_each_case(self):
        base = {u"結果": K_ELSE, u"要素": u"jppfs_cor:Assets", u"当期の枠": u"CurrentYearInstant"}
        cases = (("VALUE_MISMATCH", ["xbrl:jppfs_cor:Assets@CurrentYearInstant"], K_STOP),
                 ("GROUNDED", ["xbrl:jppfs_cor:Assets@Prior1YearInstant"], K_MOVED),
                 ("GROUNDED", ["xbrl:jppfs_cor:Assets@CurrentYearInstant"], K_SAME),
                 ("GROUNDED", ["xbrl:jppfs_cor:Liabilities@CurrentYearInstant"], K_OTHER),
                 ("GROUNDED", ["xbrl:jppfs_cor:Liabilities@Prior1YearInstant", "xbrl:jppfs_cor:Assets@CurrentYearInstant"], K_ODD),
                 ("POINTER_NOT_FOUND", [], K_ELSE))
        for st, ptr, want in cases:
            r = dict(base, **{u"結果の細目": st, u"後の pointers": ptr})
            if want == K_ODD:
                r[u"当期の枠"] = u"CurrentYearInstant"
                # 前期の別要素 + 当期の同じ要素 = どれにも当たらない形
                self.assertEqual(indep_kind(r), K_ODD)
            else:
                self.assertEqual(indep_kind(r), want, (st, ptr))
        self.assertEqual(indep_kind(dict(base, **{u"結果の細目": "id_shift"})), K_ELSE)

    def test_m10_the_pinned_digest_changes_with_any_one_line(self):
        lines = sorted(u"%s\t%s\t%d\t%s" % (d[u"docID"], d[u"sha256"], d[u"bytes"], d[u"区分"]) for d in self.rec[u"書類"])
        self.assertEqual(digest(lines), INPUT_DIGEST)
        for i in (0, 100, 280):
            m = list(lines)
            m[i] = m[i][:-1] + (u"x" if m[i][-1] != u"x" else u"y")
            self.assertNotEqual(digest(m), INPUT_DIGEST)
        self.assertNotEqual(digest(lines[:-1]), INPUT_DIGEST)


if __name__ == "__main__":
    unittest.main()
