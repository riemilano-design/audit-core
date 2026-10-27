# -*- coding: utf-8 -*-
u"""顧客向けの日本語の報告形の結果 ― 封 docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md §2(C-1・C-2・C-2b・C-3・C-4・C-5)の結果を縛る門。

記録: ``fixtures/xbrl/customer_report_2026-10-21.json``(``measure/xbrl_customer_report_2026-10-21.py --customer-out … --answer-key …`` の出力)。
文書: ``docs/XBRL_CUSTOMER_REPORT_RESULT_2026-10-21.md``。型は P25 の結果の門 tests/measure/test_xbrl_lastbranch_result.py に倣う。

この門がやること(どれも、壊した標本で赤くなることを ``MutationTest`` が毎回確かめる):
  1. 入力(書類 67 本の sha256 の digest・point_prior の記録・封・客 A の出力と答え合わせの表の sha256)を字で留める。cache が在る機械では実物も記録と一致させる。
  2. 記録の行(書類別 67 × 2 profile)から、節の件数・和・state との対応(違う = VALUE_MISMATCH、一致 = GROUNDED、残り = POINTER_NOT_FOUND + UNVERIFIABLE)・
     reason の件数を **script の関数を使わずに** 数え直し、記録の集計と一致させる。
  3. 予測 C-1〜C-5 の判定を、封の字から読んだ幅と記録の行から**門が自分で**求め、記録の判定と文書の表と一致させる。
  4. C-3 は記録を信じず、いまの module と登録簿から**門が自分で**求める(16 の集合・1 つ消すと赤)。
  5. 文書の表・数のある文を記録から作った字と完全一致させる。それ以外の散文に算用数字が在れば ``residual_numbers`` が見つけて赤にする(コード片・識別子・日付・節の番号は除く)。散文は漢数字で書く。
  6. 測った module の sha256 と engine の指紋(adapters 16 file)が、いまの木と一致すること。``report.py``・``verify_document.py``・engine 3 file の sha が封の commit 時点のままであること。
  7. cache とラベルが在る機械では、軽い走らせ直し(2 書類 × 2 profile)を script で走らせて記録の該当行と一致。全部の走らせ直し(約 一分)は ``AUDIT_CORE_CUSTOMER_REPORT=1`` のときだけ。
**2026-10-21 追記(pin の遷移。顧客向けの報告形の直し、封 docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md)**: 段 2 は module の中身だけを直した
(判定と節の割り当ては変えない)ので、この門が測った当時の値(module の sha256・engine の指紋・末尾の指紋の行・末尾に指紋が在る本文)は、いまの木では再現しない。
測った当時の記録は 1 字も直さない。この門は (1) 記録の module の sha256 が**履歴の c13a746 の module と一致**することを毎回確かめ(記録を履歴に縛る)、
(2) いまの module / 指紋は「測った当時の値」か「宣言された遷移の値(段 2 の封が履歴に在るとき)」だけを受け入れ、(3) 記録の走らせ直し(軽い 2 書類・重い全部)と
末尾の指紋の行の試験は、**履歴の c13a746 の module と当時のラベル 2 file** で行う(いまの module では行わない。いまの module の同じ数は
``tests/measure/test_xbrl_customer_report_fix_result.py`` が記録 ``customer_report_fix_2026-10-21.json`` の R2-1 で、c13a746 の module と全行の節の割り当てを突き合わせて縛る)。

縛っていないもの: 報告の日本語の字の良し悪し(客に伝わるか)、客 A の出力そのもの(repo の外。sha256 だけ)、抜粋の行の意味、変異(module)の手の実測そのもの、
  漢数字で書いた数(``residual_numbers`` は算用数字だけを探す。散文の数は記録から作った字で縛る約束)。
**2026-10-27 追記(重い走らせ直しの遷移。封 docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md §2-2)**: ``AUDIT_CORE_CUSTOMER_REPORT=1`` の重い試験は、P26 の段 1・段 2 の後の engine で
``C3``(登録簿の理由 16 -> 19)と ``C5``(sha256 の 3 file・report_customer.py の sha256 と行数・engine の指紋)が記録と違って赤だった。重い試験の比べは ``heavy_rerun_check`` に移し、
``HEAVY_RERUN_LATER`` に名指しした欄だけを、封が履歴に在り値が宣言の値のときに限って記録の値に戻す。C3 は P26 の 3 つの理由が足されただけの形に限る。名前の無い欄は 1 字でも違えば赤。
遷移の規則は ``MutationTest.test_mh_heavy_rerun_transitions`` が環境変数なしで毎回試す。
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
REC = os.path.join(ROOT, "fixtures", "xbrl", "customer_report_2026-10-21.json")
DOC = os.path.join(ROOT, "docs", "XBRL_CUSTOMER_REPORT_RESULT_2026-10-21.md")
SEAL_REL = "docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SCRIPT = os.path.join(ROOT, "measure", "xbrl_customer_report_2026-10-21.py")
MODULE_REL = "adapters/xbrl/report_customer.py"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
RUN_HEAVY = os.environ.get("AUDIT_CORE_CUSTOMER_REPORT") == "1"
LIGHT_DOCS = ("S100YYK8", "S100YZ7E")
BOTH = ("P22", "P25")
SECTIONS = (u"違う", u"要確認", u"対象外", u"判断しない", u"一致")
KINDS = (u"当期", u"前期", u"計算", u"その他")

#: **字で留める**(記録の値の写し。定数から作らない)。
DOCS67_DIGEST = "118ec1015494db404b74dbd65b72bddfd2356459749d6f10dc910e5a1348429f"       # 書類 67 本の docID\tsha256 を sorted で \n 結合した sha256(P24・P25 の門と同じ集合)
PP_SHA = "e1db3f515bd83182235bf5751052e0bd440e8f6ff2a555419b014863b8e42862"              # fixtures/xbrl/point_prior_2026-10-20.json
CUSTOMER_OUT_SHA = "60e5fbdf2efffd0e81b4f4bf61aa857f8afa1a60e57c5036b27e68e8cac471b6"    # 客 A の P22 の出力 my_text.json(repo の外)
CUSTOMER_KEY_SHA = "71ae780c68199c5ee24d601a1622a6e99768ead51a97298d2bc4c7c38bb44412"    # 客 A の答え合わせの表 answer_key.md(repo の外)
LABEL_SHAS = {"jppfs_2025-11-01_lab.xml": "bf56ea1585afe426b398a9053ec4de4dbeafc211a53675b5d6d19453e4e04bf4",
              "jpcrp_2025-11-01_lab.xml": "df9c23764ec9a63cb65b5ef62e79a2907c590523797421442ea2a60e334cd684"}
#: 封の commit 時点から動かない file(sha256 の先頭 16 桁)。封の門 test_xbrl_customer_report_seal.py の UNTOUCHED と同じ。宣言の遷移を持たない。
UNTOUCHED = {"adapters/xbrl/report.py": "0d2854e659a5d8e0", "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
             "adapters/xbrl/vocabulary.py": "27e71e9861fc5aad", "adapters/xbrl/recipes.py": "bff243f13429b553",
             "adapters/xbrl/registry_setup.py": "f42ffe23aaa7673b"}
#: 測った時点の engine の束ねた指紋(module を足した後。adapters 16 file)。module が動けばここも動く = 測り直す。
ENGINE_FP_AT_MEASURE = {"adapter_xbrl_py_files": 16, "core_py_sha256": "34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8", "core_py_files": 4}
#: 2026-10-21 追記(段 2 の遷移): 測った当時の module(c13a746)と、段 2 の後の module・指紋。段 2 の封が履歴に在るときだけ受け入れる。
MODULE_COMMIT_AT_MEASURE = "c13a746"
ENGINE_ADAPTER_SHA_AT_MEASURE = "c556de1cb26e975a172d54a4e39f4971bb5c11a5fd8a02a8404b9a719eb27acb"   # 測った当時(記録の C5 と同じ字)
FIX_SEAL_REL = "docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md"
#: 報告形の直し 段 1 の後の値は 715468699973cc4a・11840a09…(残す。測った時点の次の値)。2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md が report_customer.py の理由の表に 3 行・
#: engine の 4 file(extract・vocabulary・recipes・registry_setup)を書き換えたので、いまの値は下の値(その封が履歴に在るときだけ受け入れる)。
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
# 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
MODULE_LATER = {"sha16": "6679138d350ec382", "seal": SEAL_P27}
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): engine の束ねた指紋は vocabulary.py の 1 行と注記で動く。498993e29055472a…(P26 の段 1)は残す(測った時点の次の値)、段 2 で 5aba774925968356…。受け入れるのは、封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md が履歴に在り、値が段 2 の後の値のときだけ。
ENGINE_ADAPTER_SHA_LATER = {"value": "0e51211a8aed2151409cb6bf443fb6eae2aed87e6b2b4bd6150c8286afee87de", "seal": SEAL_P27}
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
# 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
UNTOUCHED_LATER = {"adapters/xbrl/vocabulary.py": ("85896a67913ce1e7", SEAL_P27), "adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27),
                   "adapters/xbrl/registry_setup.py": ("d6f25750bcd73c0a", SEAL_P27)}
P26_REASONS = {"other_concept", "direction_on_cause_item", "rounded_diff_within_double_band"}
P27_REASONS = {"per_unit_counter"}       # 2026-10-27(P27 の段 2。封 docs/XBRL_P27_SEAL_2026-10-27.md §1-4・§2-3「登録簿の理由 19 → 20」。UNVERIFIABLE)
ALLOWED_RESIDUAL = []
YEN_KEY = u"文の字に百万円・千円・億円・兆円があるが claim の単位が円の行(span の字から数えた概数)"
#: 報告の末尾の指紋の行の prefix。報告の「本体」= この 1 行だけを除いた残り(git の欄は HEAD で、adapters の欄は engine の file で変わる)。
ENGINE_LINE_PREFIX = u"<sub>engine の指紋:"


def report_body(md):
    u"""門の側の独立の実装。除く行が**ちょうど 1 行**でなければ AssertionError。"""
    lines = md.split(u"\n")
    hit = [i for i, l in enumerate(lines) if l.startswith(ENGINE_LINE_PREFIX)]
    assert len(hit) == 1, u"報告の末尾の指紋の行が %d 行ある" % len(hit)
    return u"\n".join(lines[:hit[0]] + lines[hit[0] + 1:])


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


def sha_path(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha16(rel):
    return sha_path(os.path.join(ROOT, rel))[:16]


def comma(n):
    return format(n, ",")


def cell(s):
    return (s if s is not None else u"").replace(u"|", u"｜").replace(u"\n", u" ")


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


# ----------------------------------------------------------------------------------------------------------------
# 独立の数え直し(script の関数を使わない)
def recount(rows):
    sec = dict((k, sum(r[u"節"][k] for r in rows)) for k in SECTIONS)
    st = {}
    for r in rows:
        for k, v in r[u"state"].items():
            st[k] = st.get(k, 0) + v
    kinds = dict((k, sum(r[u"一致の内訳"][k] for r in rows)) for k in KINDS)
    rs = {}
    for sec_name in (u"要確認", u"対象外", u"判断しない"):
        d = {}
        for r in rows:
            for k, v in r[u"reason(%s)" % sec_name].items():
                d[k] = d.get(k, 0) + v
        rs[sec_name] = dict(sorted(d.items()))
    return {u"claims": sum(r[u"claims"] for r in rows), u"節": sec, u"節の和": sum(sec.values()), u"state": dict(sorted(st.items())), u"一致の内訳": kinds, u"reason": rs,
            u"その他の節": sum(r[u"その他の節"] for r in rows)}


def check_record(rec):
    docs = rec[u"入力の sha256"][u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"]
    assert len(docs) == 67 == rec[u"書類の数"][u"経営分析の文を持つ"]
    for p in BOTH:
        rows = rec[u"書類別"][p]
        agg = rec[u"集計"][p]
        assert sorted(r[u"doc"] for r in rows) == sorted(docs), p
        assert len(rows) == 67 and agg[u"書類数"] == 67
        for r in rows:
            assert sum(r[u"節"].values()) == r[u"claims"] == sum(r[u"state"].values()), (p, r[u"doc"])
            assert r[u"その他の節"] == 0, (p, r[u"doc"])
            # 判定を足さず変えない: 違う = VALUE_MISMATCH、一致 = GROUNDED、残りの 3 節 = POINTER_NOT_FOUND + UNVERIFIABLE
            s = r[u"state"]
            assert r[u"節"][u"違う"] == s.get("VALUE_MISMATCH", 0), (p, r[u"doc"])
            assert r[u"節"][u"一致"] == s.get("GROUNDED", 0), (p, r[u"doc"])
            assert r[u"節"][u"要確認"] + r[u"節"][u"対象外"] + r[u"節"][u"判断しない"] == s.get("POINTER_NOT_FOUND", 0) + s.get("UNVERIFIABLE", 0), (p, r[u"doc"])
            assert sum(r[u"一致の内訳"].values()) == r[u"節"][u"一致"], (p, r[u"doc"])
            for sec_name in (u"要確認", u"対象外", u"判断しない"):
                assert sum(r[u"reason(%s)" % sec_name].values()) == r[u"節"][sec_name], (p, r[u"doc"], sec_name)
            assert r[u"同じ byte(既定)"] is True and r[u"同じ byte(--full)"] is True, (p, r[u"doc"])
            assert r[u"単位の検査"][u"出典の値の単位が文と違う"] == 0, (p, r[u"doc"])
            assert r[u"字のまま残った pointer"] == 0, (p, r[u"doc"])
            assert re.match(r"^[0-9a-f]{64}$", r[u"報告の本体の sha256"]) and re.match(r"^[0-9a-f]{64}$", r[u"報告 --full の本体の sha256"])
            assert r[u"profile"] == p, (p, r[u"doc"])
        n = recount(rows)
        assert agg[u"claims"] == n[u"claims"] == 7799, p
        assert agg[u"節"] == n[u"節"], p
        assert agg[u"節の和"] == n[u"節の和"] == agg[u"claims"], p
        assert agg[u"state"] == n[u"state"], p
        assert agg[u"一致の内訳"] == n[u"一致の内訳"], p
        assert agg[u"その他の節"] == 0 and agg[u"字のまま残った pointer"] == 0
        for sec_name in (u"要確認", u"対象外", u"判断しない"):
            assert agg[u"reason(%s)" % sec_name] == n[u"reason"][sec_name], (p, sec_name)
        assert agg[u"同じ byte(全部)"] is True
        assert agg[u"単位の検査"][u"出典の値の単位が文と違う"] == 0
        assert agg[u"単位の検査"][u"文が金額の単位で出典の値がある「違う」"] == sum(r[u"単位の検査"][u"文が金額の単位で出典の値がある「違う」"] for r in rows)
        assert agg[u"ラベル無しの要素を持つ行(違う・一致)"] == sum(r[u"ラベル無しの要素を持つ行(違う・一致)"] for r in rows)
        assert sum(agg[u"ラベル無しの名前空間別の行数"].values()) >= agg[u"ラベル無しの要素を持つ行(違う・一致)"]
        for r in rows:
            for k in SECTIONS:
                assert 0 <= r[YEN_KEY][k] <= r[u"節"][k], (p, r[u"doc"], k)
        assert agg[YEN_KEY] == dict((k, sum(r[YEN_KEY][k] for r in rows)) for k in SECTIONS), p
    # 2 つの profile は同じ claim の集合(無改変の同じ書類・同じ claim 数)
    assert [r[u"claims"] for r in rec[u"書類別"]["P22"]] == [r[u"claims"] for r in rec[u"書類別"]["P25"]]
    # 抜粋は P25 の 1 書類で、「違う」「要確認」が 5 行ずつ
    ex = rec[u"抜粋"]
    assert ex[u"profile"] == "P25" and ex[u"doc"] in docs
    assert len(ex[u"違う(先頭 5 行)"][u"行"]) == 5 and len(ex[u"要確認(先頭 5 行)"][u"行"]) == 5
    row = [r for r in rec[u"書類別"]["P25"] if r[u"doc"] == ex[u"doc"]][0]
    assert row[u"報告の本体の sha256"] == ex[u"報告の本体の sha256"]
    assert row[u"節"][u"違う"] >= 5 and row[u"節"][u"要確認"] >= 5
    # 客 A
    k = rec[u"C1"]
    assert k[u"入力"][u"claims"] == 39 and k[u"入力"][u"profile"] == "P22" and sum(k[u"節"].values()) == 39
    assert [r[u"id"] for r in k[u"行"]] == ["N001", "N007", "N010", "N015", "T009"]
    assert k[u"先頭の節に在る数"] == sum(1 for r in k[u"行"] if r[u"先頭の節に在る"] and r[u"節"] == u"違う")
    assert k[u"単位が文と同じ数"] == sum(1 for r in k[u"行"] if r[u"出典の値の単位が文と同じ(語の主張は円)"])
    assert k[u"同じ byte"] is True


def check_inputs(rec):
    z = rec[u"入力の sha256"]
    docs = z[u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"]
    lines = sorted(u"%s\t%s" % (d, s) for d, s in docs.items())
    assert hashlib.sha256(u"\n".join(lines).encode("utf-8")).hexdigest() == DOCS67_DIGEST, u"書類 67 本の digest が違う"
    assert z["fixtures/xbrl/point_prior_2026-10-20.json"] == PP_SHA
    assert z["seal"] == sha_path(SEAL), u"封が測った時点から動いている"
    assert rec[u"C1"][u"入力"][u"sha256"] == CUSTOMER_OUT_SHA
    assert rec[u"C1"][u"答え合わせの表"][u"sha256"] == CUSTOMER_KEY_SHA
    assert rec[u"環境"][u"ラベル 2 file の sha256(起動時に照合)"] == LABEL_SHAS
    assert rec[u"環境"][u"DEFAULT_PROFILE"] == "P22"


def seal_bounds(seal):
    u"""封 §2 の表から幅を読む(門が自分で)。"""
    rows = dict((m.group(1), m.group(2)) for m in re.finditer(r"(?m)^\| \*\*(C-[0-9a-z]+)\*\* \| (.*?) \| .*? \|$", seal))
    out = {}
    for tag in ("C-2", "C-2b"):
        pred = rows[tag]
        out[tag] = {u"点": [int(x.replace(",", "")) for x in re.findall(r"\*\*([\d,]+)\*\*", pred)],
                    u"幅": [(int(a.replace(",", "")), int(b.replace(",", ""))) for a, b in re.findall(r"\*\*([\d,]+)〜([\d,]+)\*\*", pred)]}
    return out


def judgments(rec, seal):
    B = seal_bounds(seal)
    out = {}
    a, b = rec[u"集計"]["P22"][u"節"], rec[u"集計"]["P25"][u"節"]
    n, w = B["C-2"][u"点"], B["C-2"][u"幅"]
    ok = (a[u"違う"] == n[0] and w[0][0] <= a[u"要確認"] <= w[0][1] and w[1][0] <= a[u"対象外"] + a[u"判断しない"] <= w[1][1]
          and a[u"一致"] == 4242 and sum(a.values()) == 7799)
    out["C-2"] = u"当たり" if ok else u"外れ"
    n, w = B["C-2b"][u"点"], B["C-2b"][u"幅"]
    ok = (b[u"違う"] == n[0] and b[u"一致"] == n[1] and w[0][0] <= b[u"対象外"] + b[u"判断しない"] <= w[0][1] and w[1][0] <= b[u"要確認"] <= w[1][1] and sum(b.values()) == 7799)
    out["C-2b"] = u"当たり" if ok else u"外れ"
    k = rec[u"C1"]
    out["C-1"] = u"当たり" if (k[u"先頭の節に在る数"] == 5 and k[u"単位が文と同じ数"] == 5) else u"外れ"
    c3 = live_c3()
    out["C-3"] = u"当たり" if c3 else u"外れ"
    c4 = rec[u"C4"]
    out["C-4"] = u"当たり" if (all(rec[u"集計"][p][u"同じ byte(全部)"] for p in BOTH) and all(x[u"report.py の出力が golden とバイト一致"] and x[u"新しい報告が 2 回で同じ"] for x in c4)) else u"外れ"
    c5 = rec[u"C5"]
    zero = all(v == u"0 行" for v in c5[u"HEAD からの差分(git diff --numstat)"].values())
    out["C-5"] = u"当たり" if (zero and c5[u"engine の指紋"][u"adapter_xbrl_py_files"] == 16 and c5[u"core/ の HEAD からの差分"] == u"0 行") else u"外れ"
    return out


def check_judgments(rec, seal):
    got = judgments(rec, seal)
    for tag, v in got.items():
        assert rec[u"予測の判定"][tag][u"判定"] == v, (tag, v, rec[u"予測の判定"][tag][u"判定"])
    assert sorted(rec[u"予測の判定"]) == sorted(got)


def live_c3():
    u"""C-3 を記録でなく、いまの module と登録簿から求める。測った時点の 16 の集合(+ P26 の封が履歴に在るなら、P26 が足した 3 つ)が登録簿と一致し、
    1 つ消すと網羅が赤、実測の reason が表の外に出ない。"""
    from adapters.xbrl import recipes as R
    from adapters.xbrl import registry_setup as RS
    from adapters.xbrl import report_customer as RC
    reg = set(RS._POINTER_NOT_FOUND_REASONS) | set(RS._UNVERIFIABLE_REASONS)
    want = set(R.UNBOUND_REASON_STATE) | {"other_frame", "no_same_value"}
    if git("log", "--diff-filter=A", "--format=%H", "--", SEAL_P26).stdout.split():
        want |= P26_REASONS         # 登録簿の理由 16 → 19(封 docs/XBRL_P26_SEAL_2026-10-21.md §2 Q-7)
    if git("log", "--diff-filter=A", "--format=%H", "--", SEAL_P27).stdout.split():
        want |= P27_REASONS         # 登録簿の理由 19 → 20(封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3)
    if len(reg) != len(want) or reg != want:
        return False
    if set(RC.REASON_JA) != reg:
        return False
    for k in RC.REASON_JA:
        if reg - (set(RC.REASON_JA) - {k}) != {k}:
            return False
    return True


# ----------------------------------------------------------------------------------------------------------------
# 文書(記録から作った字と完全一致)
def pct(a, b):
    return u"%.1f%%" % (100.0 * a / b)


def render_blocks(rec):
    B = {}
    # 予測の表
    L = [u"| # | 封の予測 | 実測 | 判定 |", u"|---|---|---|---|"]
    pred = {"C-1": u"答え合わせの 5 件が先頭の節「違う」に 5 / 5・出典の値は文と同じ単位",
            "C-2": u"既定 P22: 違う 1,410 / 要確認 880〜950 / 対象外 + 判断しない 1,200〜1,260 / 一致 4,242 / 和 7,799",
            "C-2b": u"P25 明示: 違う 626 / 一致 4,382 / 対象外 + 判断しない 1,190〜1,250 / 要確認 1,540〜1,600 / 和 7,799",
            "C-3": u"理由の日本語表は登録簿の理由の全部(16)を網羅・1 つ消すと網羅の検査が赤",
            "C-4": u"同じ JSON から 2 回で同じバイト列・report.py の golden は不変",
            "C-5": u"report.py・verify_document.py は 0 行・engine の指紋は module の分だけ動く(15 → 16 file)"}
    for tag in ("C-1", "C-2", "C-2b", "C-3", "C-4", "C-5"):
        j = rec[u"予測の判定"][tag]
        L.append(u"| **%s** | %s | %s | %s |" % (tag, cell(pred[tag]), cell(j[u"実測"]), j[u"判定"]))
    B[u"予測"] = u"\n".join(L)
    # 節の件数の表
    L = [u"| 節 | P22(既定) | P25(明示) |", u"|---|---|---|"]
    a, b = rec[u"集計"]["P22"], rec[u"集計"]["P25"]
    for k in SECTIONS:
        L.append(u"| %s | %s | %s |" % (k, comma(a[u"節"][k]), comma(b[u"節"][k])))
    L.append(u"| 和 | %s | %s |" % (comma(a[u"節の和"]), comma(b[u"節の和"])))
    L.append(u"| claim の合計 | %s | %s |" % (comma(a[u"claims"]), comma(b[u"claims"])))
    L.append(u"| 対象外 + 判断しない | %s | %s |" % (comma(a[u"節"][u"対象外"] + a[u"節"][u"判断しない"]), comma(b[u"節"][u"対象外"] + b[u"節"][u"判断しない"])))
    L.append(u"| 一致の内訳 当期 / 前期 / 計算 / その他 | %s | %s |" % (u" / ".join(comma(a[u"一致の内訳"][k]) for k in KINDS), u" / ".join(comma(b[u"一致の内訳"][k]) for k in KINDS)))
    B[u"節"] = u"\n".join(L)
    # state の表
    L = [u"| engine の state(報告は足さず変えない) | P22(既定) | P25(明示) |", u"|---|---|---|"]
    for k in ("VALUE_MISMATCH", "GROUNDED", "POINTER_NOT_FOUND", "UNVERIFIABLE"):
        L.append(u"| %s | %s | %s |" % (k, comma(a[u"state"].get(k, 0)), comma(b[u"state"].get(k, 0))))
    B[u"state"] = u"\n".join(L)
    # reason の表
    L = [u"| 節 | reason | 日本語の 1 行 | P22(既定) | P25(明示) |", u"|---|---|---|---|---|"]
    from adapters.xbrl import report_customer as RC
    for sec_name in (u"要確認", u"対象外", u"判断しない"):
        keys = sorted(set(a[u"reason(%s)" % sec_name]) | set(b[u"reason(%s)" % sec_name]))
        for k in keys:
            L.append(u"| %s | `%s` | %s | %s | %s |" % (sec_name, k, cell(RC.REASON_JA.get(k, k)), comma(a[u"reason(%s)" % sec_name].get(k, 0)), comma(b[u"reason(%s)" % sec_name].get(k, 0))))
    B[u"reason"] = u"\n".join(L)
    # 客 A
    k = rec[u"C1"]
    L = [u"| 答え合わせ | id | 節 | 文の値 | 出典の値(文と同じ単位) |", u"|---|---|---|---|---|"]
    for r in k[u"行"]:
        L.append(u"| %s | %s | %s | %s | %s |" % (r[u"答え合わせ"], r[u"id"], r[u"節"], cell(r[u"文の値"]), cell(r[u"出典の値"])))
    L.append(u"| 節の件数(39 claim) | | 違う %d / 要確認 %d / 対象外 %d / 判断しない %d / 一致 %d | | |" % tuple(k[u"節"][s] for s in SECTIONS))
    B[u"客 A"] = u"\n".join(L)
    # 検査の数
    L = [u"| 検査 | P22(既定) | P25(明示) |", u"|---|---|---|"]
    L.append(u"| 文が金額の単位で出典の値がある「違う」 | %s | %s |" % (comma(a[u"単位の検査"][u"文が金額の単位で出典の値がある「違う」"]), comma(b[u"単位の検査"][u"文が金額の単位で出典の値がある「違う」"])))
    L.append(u"| そのうち出典の値の単位が文と違う | %s | %s |" % (comma(a[u"単位の検査"][u"出典の値の単位が文と違う"]), comma(b[u"単位の検査"][u"出典の値の単位が文と違う"])))
    L.append(u"| 日本語に直らず字のまま残った計算の pointer | %s | %s |" % (comma(a[u"字のまま残った pointer"]), comma(b[u"字のまま残った pointer"])))
    L.append(u"| 標準ラベルが無く要素名のまま残る要素を持つ行(違う・一致) | %s | %s |" % (comma(a[u"ラベル無しの要素を持つ行(違う・一致)"]), comma(b[u"ラベル無しの要素を持つ行(違う・一致)"])))
    for ns in sorted(set(a[u"ラベル無しの名前空間別の行数"]) | set(b[u"ラベル無しの名前空間別の行数"])):
        L.append(u"| 　うち `%s` | %s | %s |" % (ns, comma(a[u"ラベル無しの名前空間別の行数"].get(ns, 0)), comma(b[u"ラベル無しの名前空間別の行数"].get(ns, 0))))
    B[u"検査"] = u"\n".join(L)
    # 抜粋
    ex = rec[u"抜粋"]
    L = [u"```", u"## 1. 違う(先頭 5 行) ― %s・P25" % ex[u"doc"], u"", ex[u"違う(先頭 5 行)"][u"見出し行"], u"|---|---|---|---|---|"] + ex[u"違う(先頭 5 行)"][u"行"]
    L += [u"", u"## 2. 要確認(先頭 5 行) ― %s・P25" % ex[u"doc"], u"", ex[u"要確認(先頭 5 行)"][u"見出し行"], u"|---|---|---|---|"] + ex[u"要確認(先頭 5 行)"][u"行"] + [u"```"]
    B[u"抜粋"] = u"\n".join(L)
    # 指紋
    c5 = rec[u"C5"]
    L = [u"| file | sha256 | 封の commit からの差分 |", u"|---|---|---|"]
    for rel in sorted(c5[u"sha256"]):
        L.append(u"| `%s` | `%s` | %s |" % (rel, c5[u"sha256"][rel][:16], c5[u"HEAD からの差分(git diff --numstat)"][rel]))
    L.append(u"| `%s`(新規) | `%s` | 行数 %d |" % (MODULE_REL, c5[u"report_customer.py の sha256"][:16], c5[u"report_customer.py の行数"]))
    fp = c5[u"engine の指紋"]
    L.append(u"| engine の束ねた指紋 adapter_xbrl_py_sha256 | `%s`(%d file) | 封の commit 時点は 15 file |" % (fp[u"adapter_xbrl_py_sha256"][:16], fp[u"adapter_xbrl_py_files"]))
    L.append(u"| `core/` | | %s |" % c5[u"core/ の HEAD からの差分"])
    B[u"指紋"] = u"\n".join(L)
    return B


def prose_facts(rec):
    a, b = rec[u"集計"]["P22"], rec[u"集計"]["P25"]
    return {
        u"和": u"claim の合計は %s、節の和は %s(P22)・%s(P25)。" % (comma(a[u"claims"]), comma(a[u"節の和"]), comma(b[u"節の和"])),
        u"書類": u"書類は %d 本(経営分析の文を持つ)。" % rec[u"書類の数"][u"経営分析の文を持つ"],
        u"客 A": u"客 A の出力は %d claim(P22)。" % rec[u"C1"][u"入力"][u"claims"],
        u"単位の注記": u"概数(span の字から数えた): P25 で違う %d・要確認 %d・一致 %d・判断しない %d(P22 で違う %d・要確認 %d・一致 %d・判断しない %d)。" % (
            tuple(b[YEN_KEY][k] for k in (u"違う", u"要確認", u"一致", u"判断しない")) + tuple(a[YEN_KEY][k] for k in (u"違う", u"要確認", u"一致", u"判断しない"))),
        u"所要": u"測定の所要は %s 秒(verify %s 秒)。" % (rec[u"所要秒"][u"合計"], rec[u"所要秒"][u"verify 合計"]),
    }


def residual_numbers(doc, rec):
    t = doc
    pieces = list(render_blocks(rec).values()) + list(prose_facts(rec).values())
    for v in sorted(pieces, key=len, reverse=True):
        t = t.replace(v, u"")
    t = re.sub(r"```.*?```", u"", t, flags=re.S)
    t = re.sub(r"`[^`]*`", u"", t)
    t = re.sub(r"[A-Za-z_][A-Za-z_0-9\-]*\d[A-Za-z_0-9\-]*", u"", t)
    t = re.sub(r"(?m)^#+ [\d\-]+\.?", u"", t)
    t = re.sub(r"段 \d", u"", t)
    t = t.replace(u"0 USD", u"")
    t = re.sub(r"§[\d\-]+", u"", t)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    return re.findall(r"\d[\d,\.]*", t)


def check_doc(rec, doc):
    for k, v in render_blocks(rec).items():
        assert v in doc, u"文書に『%s』の表(記録から作った字)が無い" % k
    for k, v in prose_facts(rec).items():
        assert v in doc, u"文書に数のある文『%s』(記録から作った字)が無い" % k
    for lit in (u"は一字も触らない", u"門で縛れない", u"封と実物の食い違い", u"一回限りの手の実測", u"文の字の単位ではない", u"報告の本体", u"迷った点"):
        assert lit in doc, lit
    res = residual_numbers(doc, rec)
    assert res == ALLOWED_RESIDUAL, u"文書の散文に、記録に縛られない数が在る: %s" % res


def check_p25_equals_lastbranch(rec):
    lb = jload(os.path.join(ROOT, "fixtures", "xbrl", "lastbranch_2026-10-21.json"))[u"L1"][u"集計"]
    b = rec[u"集計"]["P25"]
    assert b[u"節"][u"違う"] == lb[u"VALUE_MISMATCH の合計 P25"]
    assert b[u"節"][u"一致"] == lb[u"GROUNDED の合計 P25"]
    assert b[u"state"].get("UNVERIFIABLE", 0) == lb[u"UNVERIFIABLE の合計 P25"]
    assert b[u"claims"] == lb[u"総 claim"]


def check_p22_numbers(rec):
    u"""封 §0 の下調べの数(試作の P22 の 67 書類)。実測が同じであること。"""
    a = rec[u"集計"]["P22"]
    assert (a[u"節"][u"違う"], a[u"節"][u"一致"], a[u"節"][u"要確認"], a[u"節"][u"対象外"], a[u"節"][u"判断しない"]) == (1410, 4242, 915, 151, 1081)
    assert (a[u"一致の内訳"][u"当期"], a[u"一致の内訳"][u"前期"], a[u"一致の内訳"][u"計算"]) == (1736, 180, 2326)


def git_show_measured_module():
    r = subprocess.run(["git", "show", "%s:audit-core/%s" % (MODULE_COMMIT_AT_MEASURE, MODULE_REL)], cwd=os.path.dirname(ROOT), capture_output=True)
    assert r.returncode == 0, u"履歴に測った当時の module(%s)が無い" % MODULE_COMMIT_AT_MEASURE
    return r.stdout


def check_untouched_and_module(rec):
    for rel, want in sorted(UNTOUCHED.items()):
        got = sha16(rel)
        if got != want and rel in UNTOUCHED_LATER:
            later, seal_rel = UNTOUCHED_LATER[rel]
            assert git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel)
            assert got == later, u"**%s が、宣言された遷移の値とも違う**" % rel
        else:
            assert got == want, u"**%s が動いている(この封は触らない)**" % rel
        assert rec[u"C5"][u"sha256"][rel][:16] == want
    # 記録の module の sha256 は、履歴の測った当時の module と一致する(記録を履歴に縛る)
    assert rec[u"C5"][u"report_customer.py の sha256"] == hashlib.sha256(git_show_measured_module()).hexdigest(), u"**記録の module の sha256 が履歴の %s と違う**" % MODULE_COMMIT_AT_MEASURE
    now = sha_path(os.path.join(ROOT, MODULE_REL))
    from adapters.xbrl import verify_document as VD
    fp = VD.engine_fingerprint()
    for k, v in ENGINE_FP_AT_MEASURE.items():
        assert fp[k] == v, k
    assert rec[u"C5"][u"engine の指紋"][u"adapter_xbrl_py_sha256"] == ENGINE_ADAPTER_SHA_AT_MEASURE, u"記録の engine の指紋が測った当時の字と違う"
    if now == rec[u"C5"][u"report_customer.py の sha256"]:
        assert fp["adapter_xbrl_py_sha256"] == rec[u"C5"][u"engine の指紋"][u"adapter_xbrl_py_sha256"], u"**engine の指紋が測った時点から動いている(測り直す)**"
        return
    # module が動いている: 宣言された遷移(段 2 の封が履歴に在り、値が宣言の値)だけを受け入れる
    assert git("log", "--diff-filter=A", "--format=%H", "--", MODULE_LATER["seal"]).stdout.split(), u"**module が動いているのに、遷移を宣言した封が履歴に無い**"
    assert now[:16] == MODULE_LATER["sha16"], u"**module が、宣言された遷移の値とも違う**"
    assert git("log", "--diff-filter=A", "--format=%H", "--", ENGINE_ADAPTER_SHA_LATER["seal"]).stdout.split(), u"**engine の指紋が動いているのに、遷移を宣言した封が履歴に無い**"
    assert fp["adapter_xbrl_py_sha256"] == ENGINE_ADAPTER_SHA_LATER["value"], u"**engine の指紋が、宣言された遷移の値とも違う**"


def have_cache(docs):
    return all(os.path.exists(os.path.join(CACHE, d + ".zip")) for d in docs)


def labels_ok():
    try:
        from adapters.xbrl import instance as I
        return all(os.path.exists(os.path.join(I.taxonomy_dir(), fn)) for _ns, fn, _sha in I.TAXONOMY_LABEL_FILES)
    except Exception:
        return False


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

    def test_3_judgments_are_recomputed_from_rows_and_the_seal(self):
        check_judgments(self.rec, self.seal)

    def test_4_document_tables_equal_the_record(self):
        check_doc(self.rec, self.doc)

    def test_5_module_and_untouched_files_are_the_ones_measured(self):
        check_untouched_and_module(self.rec)
        self.assertEqual(self.rec[u"C5"][u"core/ の HEAD からの差分"], u"0 行")
        self.assertEqual(self.rec[u"環境"][u"DEFAULT_PROFILE"], "P22")

    def test_6_c3_is_recomputed_from_the_module_and_the_registry_not_the_record(self):
        self.assertTrue(live_c3())

    def test_7_c1_values_are_in_the_customers_units(self):
        rows = dict((r[u"id"], r) for r in self.rec[u"C1"][u"行"])
        self.assertEqual(rows["N001"][u"出典の値"], u"40,480 百万円")
        self.assertEqual(rows["N007"][u"出典の値"], u"3,111 百万円")
        self.assertEqual(rows["N010"][u"出典の値"], u"36.22 %")
        self.assertEqual(rows["N015"][u"出典の値"], u"53,812,000 千円")
        self.assertTrue(rows["T009"][u"出典の値"].endswith(u" 円"))
        for r in rows.values():
            self.assertEqual(r[u"節"], u"違う")

    def test_8_p25_numbers_equal_the_lastbranch_record(self):
        check_p25_equals_lastbranch(self.rec)

    def test_9_p22_numbers_equal_the_seal_section_0(self):
        check_p22_numbers(self.rec)

    def test_10_cache_inputs_match_the_record(self):
        docs = self.rec[u"入力の sha256"][u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"]
        if not have_cache(sorted(docs)):
            self.skipTest(u"cache が無い")
        for d, s in sorted(docs.items()):
            self.assertEqual(sha_path(os.path.join(CACHE, d + ".zip")), s, d)

    def test_12_report_body_drops_exactly_the_engine_line_and_does_not_depend_on_head(self):
        u"""記録の『報告の本体の sha256』は末尾の指紋の行(1 行だけ)を除いた本体。git の欄(HEAD)を変えても本体は変わらず、本体の 1 字を変えると変わる。
        門の側の report_body と script の body_of が同じ結果を返す。"""
        import importlib.util
        RC = measured_module()      # 2026-10-21 追記(段 2 の遷移): 末尾の指紋の行を持つ形は、履歴の c13a746 の module が出す
        spec = importlib.util.spec_from_file_location("customer_report_script_for_gate", SCRIPT)
        S = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(S)
        out = jload(os.path.join(ROOT, "fixtures", "xbrl", "entry_output_S100Z4N9_original_2026-10-13.json"))
        for full in (False, True):
            md = RC.render_markdown(out, None, full)
            self.assertEqual(report_body(md), S.body_of(md))
            self.assertEqual(S.body_sha(md), hashlib.sha256(report_body(md).encode("utf-8")).hexdigest())
            out2 = copy.deepcopy(out)
            out2["engine"]["git_commit"] = "0" * 40
            out2["engine"]["adapter_xbrl_py_sha256"] = "1" * 64
            md2 = RC.render_markdown(out2, None, full)
            self.assertNotEqual(md, md2)
            self.assertEqual(report_body(md), report_body(md2))
            self.assertEqual(S.body_sha(md), S.body_sha(md2))
            self.assertEqual(sum(1 for l in md.split(u"\n") if l.startswith(ENGINE_LINE_PREFIX)), 1)
        # 本体の 1 字(判定の欄)を変えれば sha が変わる
        out3 = copy.deepcopy(out)
        out3["claims"][0]["state"] = "VALUE_MISMATCH" if out3["claims"][0]["state"] != "VALUE_MISMATCH" else "GROUNDED"
        self.assertNotEqual(S.body_sha(RC.render_markdown(out, None, False)), S.body_sha(RC.render_markdown(out3, None, False)))

    def test_11_the_seal_precedes_this_result(self):
        self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", SEAL_REL).stdout.split(), u"封が履歴に無い")
        self.assertEqual(git("diff", "--numstat", "HEAD", "--", SEAL_REL).stdout.strip(), u"", u"封が封の commit から変わっている")


def measured_module():
    u"""履歴の測った当時の module(c13a746)を、記録の sha256 と一致を確かめてから exec して返す(相対 import だけ絶対に直す)。"""
    import types
    raw = git_show_measured_module()
    assert hashlib.sha256(raw).hexdigest() == jload(REC)[u"C5"][u"report_customer.py の sha256"]
    src = raw.decode("utf-8").replace("from .report import cell, fmt_num", "from adapters.xbrl.report import cell, fmt_num")
    mod = types.ModuleType("report_customer_at_measure")
    exec(compile(src, "report_customer_at_measure", "exec"), mod.__dict__)
    return mod


#: script を「測った当時の module と当時のラベル 2 file」で走らせる包み(2026-10-21 追記。段 2 で module が動いた後も、記録の走らせ直しを履歴の module で保つ)。
RUN_AT_MEASURE = r"""
import hashlib, os, runpy, subprocess, sys, types
root, script, commit, want = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "core", "py"))
raw = subprocess.run(["git", "show", "%s:audit-core/adapters/xbrl/report_customer.py" % commit], cwd=os.path.dirname(root), capture_output=True).stdout
assert hashlib.sha256(raw).hexdigest() == want, "測った当時の module の sha256 が記録と違う"
import adapters.xbrl
mod = types.ModuleType("adapters.xbrl.report_customer")
mod.__package__ = "adapters.xbrl"
exec(compile(raw.decode("utf-8"), "report_customer_at_measure", "exec"), mod.__dict__)
def load_labels(directory):
    out = {}
    for fn in ("jpcrp_2025-11-01_lab.xml", "jppfs_2025-11-01_lab.xml"):
        with open(os.path.join(directory, fn), "rb") as fh:
            out.update(mod.parse_label_linkbase(fh.read()))
    return out
mod.load_labels = load_labels
sys.modules["adapters.xbrl.report_customer"] = mod
adapters.xbrl.report_customer = mod
sys.argv = [script] + sys.argv[5:]
runpy.run_path(script, run_name="__main__")
"""


def run_script(args):
    return subprocess.run([sys.executable, "-c", RUN_AT_MEASURE, ROOT, SCRIPT, MODULE_COMMIT_AT_MEASURE,
                           jload(REC)[u"C5"][u"report_customer.py の sha256"]] + args, cwd=ROOT, capture_output=True, text=True)


def drop_time(rows):
    return [dict((k, v) for k, v in r.items() if k != u"verify 秒") for r in rows]


#: 2026-10-27(重い走らせ直しの遷移。封 docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md §2-2): 重い試験の出力が記録と違ってよい欄の全部。{path: (後の値, 遷移を宣言した封, 桁)}。
#: 桁が 16 なら頭 16 字で、None なら値そのもので比べる。既存の定数が持つ値はその定数を参照する(同じ sha を 2 か所に字で書かない)。ここに名前の無い欄は 1 字でも違えば赤。
HEAVY_RERUN_LATER = {
    (u"C5", u"sha256", "adapters/xbrl/vocabulary.py"): (UNTOUCHED_LATER["adapters/xbrl/vocabulary.py"][0], UNTOUCHED_LATER["adapters/xbrl/vocabulary.py"][1], 16),
    (u"C5", u"sha256", "adapters/xbrl/recipes.py"): (UNTOUCHED_LATER["adapters/xbrl/recipes.py"][0], UNTOUCHED_LATER["adapters/xbrl/recipes.py"][1], 16),
    (u"C5", u"sha256", "adapters/xbrl/registry_setup.py"): (UNTOUCHED_LATER["adapters/xbrl/registry_setup.py"][0], UNTOUCHED_LATER["adapters/xbrl/registry_setup.py"][1], 16),
    (u"C5", u"report_customer.py の sha256"): (MODULE_LATER["sha16"], MODULE_LATER["seal"], 16),
    (u"C5", u"report_customer.py の行数"): (1027, SEAL_P27, None),      # 2026-10-27: P27 の封が理由の表に 1 行(+コメント 1 行)を足した(1025 は P26 の段 1 の後の値。残す)
    (u"C5", u"engine の指紋", u"adapter_xbrl_py_sha256"): (ENGINE_ADAPTER_SHA_LATER["value"], ENGINE_ADAPTER_SHA_LATER["seal"], None),
}


def heavy_rerun_check(got, rec, later):
    u"""重い走らせ直しの出力 ``got`` を記録 ``rec`` と比べる(封 §2-1)。``later`` に名指しした欄は、封が履歴に在り値が宣言の値のときだけ記録の値に戻す。
    C3 は P26 の 3 つの理由が登録簿に足されただけの形(封 §2-2 の (i)〜(vii))のときだけ戻す。最後に ``g == r``(名前の無い欄は 1 字でも違えば AssertionError)。"""
    def pick(o):
        return copy.deepcopy({u"書類別": dict((p, drop_time(o[u"書類別"][p])) for p in BOTH), u"集計": dict((p, o[u"集計"][p]) for p in BOTH),
                              u"抜粋": o[u"抜粋"], u"C3": o[u"C3"], u"C4": o[u"C4"], u"C5": o[u"C5"]})

    def walk(d, path):
        for k in path:
            assert isinstance(d, dict) and k in d, u"欄が無い: %r" % (path,)
            d = d[k]
        return d

    def declared(seal_rel):
        return bool(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split())

    g, r = pick(got), pick(rec)
    for path, (after, seal_rel, digits) in sorted(later.items()):
        v, w = walk(g, path), walk(r, path)
        if digits:
            v, w = v[:digits], w[:digits]
        if v == w:
            continue
        assert declared(seal_rel), u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % ("/".join(path), seal_rel)
        assert v == after, u"**%s が、宣言された遷移の値とも違う**" % "/".join(path)
        walk(g, path[:-1])[path[-1]] = walk(r, path)
    g3, r3 = g[u"C3"], r[u"C3"]
    if g3 != r3:
        reg, tbl, one = u"登録簿の理由", u"1 つ消したときの網羅の検査(消した key → 表に無い登録簿の理由)", u"登録簿 − 理由の表"
        added = set(P26_REASONS) | (set(P27_REASONS) if declared(SEAL_P27) else set())      # 2026-10-27: P27 の封が履歴に在るなら、P27 の 1 つ(UNVERIFIABLE)も足された形
        A = sorted(added)
        assert declared(SEAL_P26), u"**C3 が動いているのに、遷移を宣言した封が履歴に無い**"
        assert set(g3) == set(r3), u"C3 の key の集合が違う"
        assert set(g3[reg]) == set(r3[reg]), u"登録簿の理由の key の集合が違う"
        assert g3[reg][u"POINTER_NOT_FOUND"] == r3[reg][u"POINTER_NOT_FOUND"] + [u"other_concept"], u"(i)"
        assert g3[reg][u"UNVERIFIABLE"] == r3[reg][u"UNVERIFIABLE"] + [u"direction_on_cause_item", u"rounded_diff_within_double_band"] + ([u"per_unit_counter"] if declared(SEAL_P27) else []), u"(ii)"
        assert g3[reg][u"数"] == r3[reg][u"数"] + len(added), u"(iii)"
        assert g3[one] == A, u"(iv)"
        for k in (u"登録簿 − UNBOUND_REASON_STATE", u"実測に出なかった登録簿の理由"):
            assert g3[k] == sorted(set(r3[k]) | set(A)), u"(v) %s" % k
        assert set(g3[tbl]) == set(r3[tbl]), u"(vi) key の集合"
        for k in r3[tbl]:
            assert g3[tbl][k] == sorted(set(r3[tbl][k]) | set(A)), u"(vi) %s" % k
        for k in (u"UNBOUND_REASON_STATE の key の数", u"UNBOUND_REASON_STATE − 登録簿", u"理由の表の key の数", u"理由の表 − 登録簿",
                  u"実測に出た reason", u"実測に出た reason のうち表の外", u"profile 別の reason の件数"):
            assert g3[k] == r3[k], u"(vii) %s" % k
        g[u"C3"] = r3
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

    def test_light_two_documents_match_the_record(self):
        self._need(LIGHT_DOCS)
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "docs.json")
            p = run_script(["--stage", "docs", "--docs", ",".join(LIGHT_DOCS), "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)
        for prof in BOTH:
            want = [r for r in self.rec[u"書類別"][prof] if r[u"doc"] in LIGHT_DOCS]
            self.assertEqual(len(want), 2)
            self.assertEqual(drop_time(got[u"書類別"][prof]), drop_time(want), prof)

    @unittest.skipUnless(RUN_HEAVY, u"AUDIT_CORE_CUSTOMER_REPORT=1 のときだけ走る(全部の走らせ直し。約 一分)")
    def test_heavy_everything_matches_the_record(self):
        if not (have_cache(sorted(self.rec[u"入力の sha256"][u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"])) and labels_ok()):
            self.fail(u"AUDIT_CORE_CUSTOMER_REPORT=1 なのに cache かラベルが揃っていない")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "all.json")
            p = run_script(["--stage", "all", "--out", out])
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)
        heavy_rerun_check(got, self.rec, HEAVY_RERUN_LATER)


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
        check_untouched_and_module(self.rec)

    def test_m1_a_section_count_that_does_not_sum_to_the_claims_is_red(self):
        r = self._mut()
        r[u"書類別"]["P22"][3][u"節"][u"一致"] += 1
        self._red(check_record, r)

    def test_m2_a_value_mismatch_filed_under_another_section_is_red(self):
        r = self._mut()
        row = [x for x in r[u"書類別"]["P25"] if x[u"節"][u"違う"] > 0][0]
        row[u"節"][u"違う"] -= 1
        row[u"節"][u"要確認"] += 1                       # 和は合うが state との対応が崩れる(再分類)
        self._red(check_record, r)

    def test_m3_the_aggregate_must_equal_the_rows(self):
        r = self._mut()
        r[u"集計"]["P25"][u"節"][u"要確認"] += 1
        self._red(check_record, r)

    def test_m4_a_nondeterministic_document_is_red(self):
        r = self._mut()
        r[u"書類別"]["P25"][10][u"同じ byte(--full)"] = False
        self._red(check_record, r)

    def test_m5_a_unit_that_differs_from_the_claim_is_red(self):
        r = self._mut()
        r[u"書類別"]["P22"][5][u"単位の検査"][u"出典の値の単位が文と違う"] = 1
        self._red(check_record, r)

    def test_m6_a_changed_judgment_word_is_red(self):
        r = self._mut()
        r[u"予測の判定"]["C-2b"][u"判定"] = u"外れ"
        self._red(check_judgments, r, self.seal)

    def test_m7_a_section_outside_the_sealed_range_makes_the_judgment_a_miss(self):
        r = self._mut()
        r[u"集計"]["P25"][u"節"][u"要確認"] = 1700           # 幅 1,540〜1,600 の外
        self.assertEqual(judgments(r, self.seal)["C-2b"], u"外れ")
        r = self._mut()
        r[u"集計"]["P22"][u"節"][u"違う"] = 1411
        self.assertEqual(judgments(r, self.seal)["C-2"], u"外れ")

    def test_m8_c1_with_a_missing_first_section_is_a_miss(self):
        r = self._mut()
        r[u"C1"][u"先頭の節に在る数"] = 4
        self.assertEqual(judgments(r, self.seal)["C-1"], u"外れ")
        r = self._mut()
        r[u"C1"][u"単位が文と同じ数"] = 4
        self.assertEqual(judgments(r, self.seal)["C-1"], u"外れ")

    def test_m9_a_nonzero_diff_of_report_py_is_a_miss_for_c5(self):
        r = self._mut()
        r[u"C5"][u"HEAD からの差分(git diff --numstat)"]["adapters/xbrl/report.py"] = u"3\t1\tadapters/xbrl/report.py"
        self.assertEqual(judgments(r, self.seal)["C-5"], u"外れ")

    def test_m10_a_golden_that_moved_is_a_miss_for_c4(self):
        r = self._mut()
        r[u"C4"][0][u"report.py の出力が golden とバイト一致"] = False
        self.assertEqual(judgments(r, self.seal)["C-4"], u"外れ")

    def test_m11_a_number_in_a_document_table_is_red(self):
        d = self.doc.replace(u"| 一致 | 4,242 | 4,382 |", u"| 一致 | 4,243 | 4,382 |")
        self.assertNotEqual(d, self.doc)
        self._red(check_doc, self.rec, d)

    def test_m12_a_number_in_a_prose_sentence_is_red(self):
        d = self.doc.replace(u"は一字も触らない", u"report.py は 1 字も触らない(三十二 行は 32 行)", 1)
        self.assertNotEqual(d, self.doc)
        self._red(check_doc, self.rec, d)

    def test_m13_a_spoiled_input_digest_is_red(self):
        r = self._mut()
        k = u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"
        d0 = sorted(r[u"入力の sha256"][k])[0]
        r[u"入力の sha256"][k][d0] = "0" * 64
        self._red(check_inputs, r)

    def test_m14_a_moved_module_or_engine_is_red(self):
        r = self._mut()
        r[u"C5"][u"report_customer.py の sha256"] = "0" * 64
        self._red(check_untouched_and_module, r)
        r = self._mut()
        r[u"C5"][u"engine の指紋"][u"adapter_xbrl_py_sha256"] = "0" * 64
        self._red(check_untouched_and_module, r)

    def test_m15_c3_goes_red_when_the_table_loses_a_reason(self):
        from adapters.xbrl import report_customer as RC
        saved = dict(RC.REASON_JA)
        try:
            for k in sorted(saved):
                del RC.REASON_JA[k]
                self.assertFalse(live_c3(), k)
                RC.REASON_JA[k] = saved[k]
            RC.REASON_JA[u"zzz(extra)"] = u"x"
            self.assertFalse(live_c3())
        finally:
            RC.REASON_JA.clear()
            RC.REASON_JA.update(saved)
        self.assertTrue(live_c3())

    def test_m16_the_reasons_must_equal_the_rows(self):
        r = self._mut()
        r[u"集計"]["P25"][u"reason(要確認)"]["no_same_value"] += 1
        self._red(check_record, r)

    def test_m17_an_excerpt_with_fewer_rows_is_red(self):
        r = self._mut()
        r[u"抜粋"][u"違う(先頭 5 行)"][u"行"] = r[u"抜粋"][u"違う(先頭 5 行)"][u"行"][:4]
        self._red(check_record, r)

    def test_m19_the_body_needs_exactly_one_engine_line(self):
        md = u"a\n%s x\nb\n" % ENGINE_LINE_PREFIX
        self.assertEqual(report_body(md), u"a\nb\n")
        self._red(report_body, u"a\nb\n")                                   # 0 行
        self._red(report_body, md + u"%s y\n" % ENGINE_LINE_PREFIX)         # 2 行

    def test_m20_the_yen_unit_note_must_equal_the_rows(self):
        r = self._mut()
        r[u"集計"]["P25"][YEN_KEY][u"違う"] += 1
        self._red(check_record, r)
        r = self._mut()
        r[u"書類別"]["P22"][0][YEN_KEY][u"違う"] = r[u"書類別"]["P22"][0][u"節"][u"違う"] + 1     # 節の件数を越える
        self._red(check_record, r)

    def test_mh_heavy_rerun_transitions(self):
        u"""2026-10-27(封 docs/XBRL_HEAVY_RERUN_FIX_SEAL_2026-10-27.md §4-1): 重い走らせ直しの遷移の規則を、環境変数なしで毎回試す。V-0 は緑、V-1〜V-7 は赤。"""
        rec = self.rec
        reg, tbl = u"登録簿の理由", u"1 つ消したときの網羅の検査(消した key → 表に無い登録簿の理由)"

        def walk(d, path):
            for k in path:
                d = d[k]
            return d

        def got0():
            u"""記録から作った『engine の遷移の後の出力』の標本(封 §4-1)。HEAVY_RERUN_LATER の後の値と、C3 に P26 の 3 つの理由を入れる。"""
            g = copy.deepcopy(rec)
            for path, (after, _seal, digits) in HEAVY_RERUN_LATER.items():
                parent = walk(g, path[:-1])
                parent[path[-1]] = after + parent[path[-1]][digits:] if digits else after
            c3 = g[u"C3"]
            c3[reg][u"POINTER_NOT_FOUND"] = c3[reg][u"POINTER_NOT_FOUND"] + [u"other_concept"]
            c3[reg][u"UNVERIFIABLE"] = c3[reg][u"UNVERIFIABLE"] + [u"direction_on_cause_item", u"rounded_diff_within_double_band", u"per_unit_counter"]
            c3[reg][u"数"] += 4
            c3[u"登録簿 − 理由の表"] = sorted(P26_REASONS | P27_REASONS)
            for k in (u"登録簿 − UNBOUND_REASON_STATE", u"実測に出なかった登録簿の理由"):
                c3[k] = sorted(set(c3[k]) | P26_REASONS | P27_REASONS)
            for k in c3[tbl]:
                c3[tbl][k] = sorted(set(c3[tbl][k]) | P26_REASONS | P27_REASONS)
            return g

        with self.subTest(u"V-0 基準"):
            heavy_rerun_check(got0(), rec, HEAVY_RERUN_LATER)
            heavy_rerun_check(copy.deepcopy(rec), rec, HEAVY_RERUN_LATER)
        for path in sorted(HEAVY_RERUN_LATER):
            after = HEAVY_RERUN_LATER[path][0]
            with self.subTest(u"V-1 封の path が在らない file " + "/".join(path)):
                bad = dict((k, (a, u"docs/XBRL_NO_SUCH_SEAL_2026-10-27.md" if k == path else s_, d)) for k, (a, s_, d) in HEAVY_RERUN_LATER.items())
                self._red(heavy_rerun_check, got0(), rec, bad)
            with self.subTest(u"V-2 後の値を 1 字変える " + "/".join(path)):
                new = after + 1 if not isinstance(after, str) else after[:-1] + (u"0" if after[-1] != u"0" else u"1")
                bad = dict((k, (new if k == path else a, s_, d)) for k, (a, s_, d) in HEAVY_RERUN_LATER.items())
                self._red(heavy_rerun_check, got0(), rec, bad)
        with self.subTest(u"V-3 測った値の欄を 1 つ変える"):
            g = got0()
            g[u"集計"]["P22"][u"節"][u"違う"] += 1
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)
        with self.subTest(u"V-4 byte 一致のままの留めを変える"):
            g = got0()
            g[u"C5"][u"engine の指紋"][u"core_py_sha256"] = "0" * 64
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)
        with self.subTest(u"V-5 宣言の無い欄に後の値を入れる"):
            g = got0()
            g[u"C5"][u"sha256"]["adapters/xbrl/report.py"] = HEAVY_RERUN_LATER[(u"C5", u"sha256", "adapters/xbrl/vocabulary.py")][0] + rec[u"C5"][u"sha256"]["adapters/xbrl/report.py"][16:]
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)
        with self.subTest(u"V-6 P26_REASONS に無い理由を C3 に足す"):
            g = got0()
            g[u"C3"][reg][u"UNVERIFIABLE"] = g[u"C3"][reg][u"UNVERIFIABLE"] + [u"zz_reason"]
            g[u"C3"][reg][u"数"] += 1
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)
        with self.subTest(u"V-7 other_concept を別の群へ移す"):
            g = got0()
            g[u"C3"][reg][u"POINTER_NOT_FOUND"] = [x for x in g[u"C3"][reg][u"POINTER_NOT_FOUND"] if x != u"other_concept"]
            g[u"C3"][reg][u"UNVERIFIABLE"] = g[u"C3"][reg][u"UNVERIFIABLE"] + [u"other_concept"]
            self._red(heavy_rerun_check, g, rec, HEAVY_RERUN_LATER)

    def test_m18_the_p25_and_p22_numbers_must_equal_their_records(self):
        r = self._mut()
        r[u"集計"]["P25"][u"節"][u"違う"] += 1
        self._red(check_p25_equals_lastbranch, r)
        r = self._mut()
        r[u"集計"]["P22"][u"節"][u"要確認"] += 1
        self._red(check_p22_numbers, r)


if __name__ == "__main__":
    unittest.main()
