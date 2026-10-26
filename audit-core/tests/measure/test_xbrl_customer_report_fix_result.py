# -*- coding: utf-8 -*-
u"""顧客向けの報告形の直し(単位・桁・符号・英字・但し書き・指紋・表題・抜粋)の結果 ― 封 docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md §2(R2-1〜R2-7)の結果を縛る門。

記録: ``fixtures/xbrl/customer_report_fix_2026-10-21.json``(``measure/xbrl_customer_report_fix_2026-10-21.py --customer-out …`` の出力)。
文書: ``docs/XBRL_CUSTOMER_REPORT_FIX_RESULT_2026-10-21.md``。型は段 1 の結果の門 tests/measure/test_xbrl_customer_report_result.py に倣う。

この門がやること(どれも、壊した標本で赤くなることを ``MutationTest`` が毎回確かめる):
  1. 入力(書類 67 本の sha256 の digest・point_prior の記録・段 1 の記録・封・名簿の 3 file・客 A の出力)を字で留める。cache が在る機械では実物も記録と一致させる。
  2. 記録の行(書類別 67 × 2 profile)から、節の件数・和・単位・ラベル・hex・同じ byte を **script の関数を使わずに** 数え直し、記録の集計と一致させる。
     R2-1 は**段 1 の記録の書類別の節の件数と全書類で一致**すること(判定を変えていない)と、**行ごとの節の割り当て**の違いが 0 で割り当ての sha256 が前と後で同じことを見る。
  3. 予測 R2-1〜R2-7 の判定を、封の字から読んだ幅と記録の行から**門が自分で**求め、記録の判定と文書の表と一致させる。
  4. 文書の表・数のある文を記録から作った字と完全一致させる。それ以外の散文に算用数字が在れば ``residual_numbers`` が見つけて赤にする(コード片・識別子・日付・節の番号は除く)。散文は漢数字で書く。
  5. 測った module の sha256 と engine の指紋(adapters 16 file)が、いまの木と一致すること。触らない 6 file の sha256 が封の commit 時点のままであること。
  6. cache とラベルが在る機械では、軽い走らせ直し(2 書類 × 2 profile)を script で走らせて記録の該当行と一致。全部の走らせ直し(約 二分)は ``AUDIT_CORE_CUSTOMER_REPORT_FIX=1`` のときだけ。

**本文と provenance の扱い**(封 §1-7 の後、末尾の指紋の行が本文から消えた): 記録に置くのは**本文全体の sha256**(段 1 のように末尾の 1 行を除かない。本文に HEAD も engine の指紋も入らないので、
commit で HEAD が動いても本文は変わらない)と、``.provenance.json`` については「同じ入力から同じバイト列」「body_sha256 が本文と一致」の真偽だけ。
provenance の中身(engine の git_commit = HEAD を含む)のバイト列そのものは記録に置かない(commit のたびに変わる欄を含むため)。
縛っていないもの: 報告の日本語の字の良し悪し(客に伝わるか)、客 A の出力そのもの(repo の外。sha256 だけ)、抜粋の行の意味、
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
REC = os.path.join(ROOT, "fixtures", "xbrl", "customer_report_fix_2026-10-21.json")
OLD_REC = os.path.join(ROOT, "fixtures", "xbrl", "customer_report_2026-10-21.json")
DOC = os.path.join(ROOT, "docs", "XBRL_CUSTOMER_REPORT_FIX_RESULT_2026-10-21.md")
SEAL_REL = "docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SCRIPT = os.path.join(ROOT, "measure", "xbrl_customer_report_fix_2026-10-21.py")
MODULE_REL = "adapters/xbrl/report_customer.py"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
STD_LABELS = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy", "2025-11-01")
RUN_HEAVY = os.environ.get("AUDIT_CORE_CUSTOMER_REPORT_FIX") == "1"
LIGHT_DOCS = ("S100YYK8", "S100YZ7E")
BOTH = ("P22", "P25")
SECTIONS = (u"違う", u"要確認", u"対象外", u"判断しない", u"一致")
TWO = (u"違う", u"一致")

#: **字で留める**(記録の値の写し。定数から作らない)。
DOCS67_DIGEST = "118ec1015494db404b74dbd65b72bddfd2356459749d6f10dc910e5a1348429f"       # 書類 67 本の docID\tsha256 を sorted で \n 結合した sha256(段 1 の門と同じ集合)
PP_SHA = "e1db3f515bd83182235bf5751052e0bd440e8f6ff2a555419b014863b8e42862"              # fixtures/xbrl/point_prior_2026-10-20.json
OLD_REC_SHA = "268a7a3a4f63efc2af8a06039edbcb1bc5723638eeb45d0b280acafc8f453017"         # 段 1 の記録 fixtures/xbrl/customer_report_2026-10-21.json(c13a746)
CUSTOMER_OUT_SHA = "60e5fbdf2efffd0e81b4f4bf61aa857f8afa1a60e57c5036b27e68e8cac471b6"    # 客 A の P22 の出力 my_text.json(repo の外。段 1 の記録の C1 と同じ)
ROSTER_SHAS = {"jpcrp_2025-11-01_lab.xml": "df9c23764ec9a63cb65b5ef62e79a2907c590523797421442ea2a60e334cd684",
               "jpigp_2025-11-01_lab.xml": "d45c95cc634202973557f5ed935d747ba25e751b7386c5269fe3e7bdb2c82d09",
               "jppfs_2025-11-01_lab.xml": "bf56ea1585afe426b398a9053ec4de4dbeafc211a53675b5d6d19453e4e04bf4"}
#: 封の commit 時点(14cdd21 の木)から動かない file(sha256 の先頭 16 桁)。封の門 test_xbrl_customer_report_fix_seal.py の UNTOUCHED と同じ値。宣言の遷移を持たない。
UNTOUCHED = {"adapters/xbrl/report.py": "0d2854e659a5d8e0", "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
             "adapters/xbrl/vocabulary.py": "27e71e9861fc5aad", "adapters/xbrl/recipes.py": "bff243f13429b553",
             "adapters/xbrl/registry_setup.py": "f42ffe23aaa7673b", "adapters/xbrl/comparators.py": "d8706338325e725b"}
#: 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md が engine の 3 file(vocabulary・recipes・registry_setup)と report_customer.py(理由の表に 3 行)を書き換えた。
#: 上の UNTOUCHED・下の MODULE_SHA16・ENGINE_FP は「測った時点」の値で消さない(記録の C5・R2-7 が測った値)。いまの値は下の *_LATER で、その封が履歴に在るときだけ受け入れる。
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
# 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
UNTOUCHED_LATER = {"adapters/xbrl/vocabulary.py": ("e28733067b1f17f5", SEAL_DEFAULT_P26), "adapters/xbrl/recipes.py": ("181b370420ab751b", SEAL_P26),
                   "adapters/xbrl/registry_setup.py": ("7f2cbded9c830211", SEAL_P26)}
MODULE_LATER = {"sha16": "141767d189b63733", "seal": SEAL_P26}
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 束ねた指紋 498993e29055472a…(P26 の段 1)は残す(測った時点の次の値)、段 2 で 5aba774925968356…。受け入れるのは、封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md が履歴に在り、値が段 2 の後の値のときだけ。
ENGINE_FP_LATER = {"adapter_xbrl_py_sha256": ("5aba7749259683563c37e62353717f64b4e4828931998a7c42518aca107f3504", SEAL_DEFAULT_P26)}
#: 測った時点の module(report_customer.py)の sha256 の先頭 16 桁と engine の束ねた指紋。module が動けば測り直す。
MODULE_SHA16 = "715468699973cc4a"
ENGINE_FP = {"adapter_xbrl_py_sha256": "11840a097f04dcb4c01f057ce78d39c3aedabf139e65dbc5620e28c109f64693", "adapter_xbrl_py_files": 16,
             "core_py_sha256": "34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8", "core_py_files": 4}
#: 段 1 の engine の束ねた指紋(c13a746)。R2-7 の「module の分だけ動いた」の比べ先。
ENGINE_ADAPTER_SHA_STAGE1 = "c556de1cb26e975a172d54a4e39f4971bb5c11a5fd8a02a8404b9a719eb27acb"
ALLOWED_RESIDUAL = []


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
# 封の字から幅を読む(門が自分で)
def seal_bounds(seal):
    row = lambda tag: next(l for l in seal.splitlines() if l.startswith(u"| **%s**" % tag))
    r2 = re.search(r"読み取れない \*\*(\d+)〜(\d+) / ([\d,]+)\*\*", row("R2-2"))
    r3 = re.search(r"\*\*(\d+)〜(\d+)\*\*", row("R2-3").split(u"|")[2])
    r1 = row("R2-1")
    secs = {}
    for p in BOTH:
        m = re.search(p + r": ([\d,]+) / ([\d,]+) / ([\d,]+) / ([\d,]+) / ([\d,]+)", r1)
        secs[p] = dict(zip(SECTIONS, [int(x.replace(",", "")) for x in m.groups()]))
    return {"unread": (int(r2.group(1)), int(r2.group(2))), "unread_den": int(r2.group(3).replace(",", "")),
            "unres": (int(r3.group(1)), int(r3.group(2))), "sections": secs}


# ----------------------------------------------------------------------------------------------------------------
# 独立の数え直し(script の関数を使わない)
def sumd(rows, key, ks=SECTIONS):
    return dict((k, sum(r[key][k] for r in rows)) for k in ks)


def check_record(rec):
    docs = rec[u"入力の sha256"][u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"]
    assert len(docs) == 67 == rec[u"書類の数"][u"経営分析の文を持つ"]
    old = jload(OLD_REC)
    for p in BOTH:
        rows = rec[u"書類別"][p]
        agg = rec[u"集計"][p]
        assert sorted(r[u"doc"] for r in rows) == sorted(docs), p
        assert len(rows) == 67 and agg[u"書類数"] == 67
        old_by = dict((r[u"doc"], r) for r in old[u"書類別"][p])
        for r in rows:
            assert sum(r[u"節"].values()) == r[u"claims"], (p, r[u"doc"])
            # R2-1: 節の件数は段 1 の記録の同じ書類と同じ(判定を変えていない)。c13a746 の module で数え直した値とも同じ
            assert r[u"節"] == old_by[r[u"doc"]][u"節"], (p, r[u"doc"])
            assert r[u"節"] == r[u"節(c13a746 の module)"], (p, r[u"doc"])
            assert r[u"claims"] == old_by[r[u"doc"]][u"claims"], (p, r[u"doc"])
            assert r[u"行の節の割り当ての違い(前 → 後)"] == 0 and r[u"割り当ての sha256(後)"] == r[u"割り当ての sha256(前)"], (p, r[u"doc"])
            assert r[u"節の件数が報告の見出しと同じ"] is True and r[u"報告の中の id の並びが section_of と同じ"] is True, (p, r[u"doc"])
            # R2-2: 金額の claim は「読めた」と「読み取れない」に分かれる。食い違いは読めた行の部分集合
            for k in SECTIONS:
                assert r[u"金額の claim"][k] == r[u"金額の claim で文の字が読めた"][k] + r[u"読み取れない(金額の claim で span に同じ金額の字が無い)"][k], (p, r[u"doc"], k)
                assert r[u"金額の claim"][k] <= r[u"節"][k]
                assert 0 <= r[u"単位の食い違い 後"][k] <= r[u"金額の claim で文の字が読めた"][k]
                assert 0 <= r[u"単位の食い違い 前(文の字の単位 ≠ 表に出した単位)"][k] <= r[u"金額の claim で文の字が読めた"][k]
            # R2-2(独立): 金額の行の部分集合・(i)(ii) の和は食い違い以上
            for k in SECTIONS:
                assert 0 <= r[u"独立: 単位の食い違い 後"][k] <= r[u"独立: 金額の行(『文の値』の列が金額の単位で終わる)"][k], (p, r[u"doc"], k)
                assert r[u"独立: 単位の食い違い 後"][k] >= max(r[u"独立: 後のうち文の値が抜粋に無い"][k], r[u"独立: 後のうち出典の値の単位が違う"][k])
                assert r[u"独立: 単位の食い違い 後"][k] <= r[u"独立: 後のうち文の値が抜粋に無い"][k] + r[u"独立: 後のうち出典の値の単位が違う"][k]
            assert 0 <= r[u"一致の主表示が文と違って見える行 後"] <= r[u"一致の主表示を比べた行"]
            assert 0 <= r[u"一致の主表示が文と違って見える行 前"] <= r[u"一致の主表示を比べた行(四捨五入だけ・前)"]
            assert r[u"一致の主表示を比べた行"] == r[u"一致の主表示を比べた行(四捨五入だけ・前)"], (p, r[u"doc"])
            # R2-3
            for k in TWO:
                assert 0 <= r[u"ラベルが引けず名前のまま出た行 後(違う・一致)"][k] <= r[u"節"][k]
                assert 0 <= r[u"ラベルが引けず名前のまま出た行 前(違う・一致)"][k] <= r[u"節"][k]
            # R2-4
            assert r[u"同じ byte(本文 既定)"] is True and r[u"同じ byte(本文 --full)"] is True and r[u"同じ byte(provenance)"] is True, (p, r[u"doc"])
            assert r[u"provenance の body_sha256 が本文と一致"] is True, (p, r[u"doc"])
            assert re.match(r"^[0-9a-f]{64}$", r[u"本文の sha256(既定)"]) and re.match(r"^[0-9a-f]{64}$", r[u"本文の sha256(--full)"])
            assert r[u"profile"] == p, (p, r[u"doc"])
            assert r[u"表題"].startswith(u"# ") and r[u"表題"].endswith(u"の数の点検"), (p, r[u"doc"], r[u"表題"])
            assert [m[u"status"] for m in r[u"ラベルの file(後)"] if not m[u"file"].startswith(u"zip:")] == [u"used"] * 3, (p, r[u"doc"])
        # 集計を行から数え直す
        assert agg[u"claims"] == sum(r[u"claims"] for r in rows) == 7799, p
        assert agg[u"節"] == sumd(rows, u"節"), p
        assert agg[u"節の和"] == sum(agg[u"節"].values()) == agg[u"claims"], p
        assert agg[u"節"] == dict((k, old[u"集計"][p][u"節"][k]) for k in SECTIONS), p
        for key in (u"金額の claim", u"金額の claim で文の字が読めた", u"読み取れない(金額の claim で span に同じ金額の字が無い)",
                    u"単位の食い違い 前(文の字の単位 ≠ 表に出した単位)", u"単位の食い違い 後"):
            d = sumd(rows, key)
            d[u"計"] = sum(d.values())
            assert agg[key] == d, (p, key)
        for key in (u"独立: 金額の行(『文の値』の列が金額の単位で終わる)", u"独立: 単位の食い違い 前(c13a746 の本文)", u"独立: 単位の食い違い 後",
                    u"独立: 後のうち文の値が抜粋に無い", u"独立: 後のうち出典の値の単位が違う"):
            d = sumd(rows, key)
            d[u"計"] = sum(d.values())
            assert agg[key] == d, (p, key)
        for key in (u"一致の主表示を比べた行", u"一致の主表示を比べた行(四捨五入だけ・前)", u"一致の主表示が文と違って見える行 前", u"一致の主表示が文と違って見える行 後"):
            assert agg[key] == sum(r[key] for r in rows), (p, key)
        assert agg[u"一致の主表示が文と違って見える行 後"] <= agg[u"一致の主表示が文と違って見える行 前"]
        for key in (u"ラベルが引けず名前のまま出た行 前(違う・一致)", u"ラベルが引けず名前のまま出た行 後(違う・一致)",
                    u"英字の正規表現に当たる行 前(違う・一致)", u"英字の正規表現に当たる行 後(違う・一致)"):
            d = sumd(rows, key, TWO)
            d[u"計"] = sum(d.values())
            assert agg[key] == d, (p, key)
        for key in (u"本文の 64 桁の hex 前(c13a746・既定)", u"本文の 64 桁の hex 後(既定)", u"本文の 64 桁の hex 後(--full)", u"本文の『engine の指紋』の行 後"):
            assert agg[key] == sum(r[key] for r in rows), (p, key)
        assert agg[u"同じ byte の書類数(本文 既定)"] == sum(1 for r in rows if r[u"同じ byte(本文 既定)"]) == 67
        assert agg[u"同じ byte の書類数(本文 --full)"] == sum(1 for r in rows if r[u"同じ byte(本文 --full)"]) == 67
        assert agg[u"同じ byte の書類数(provenance)"] == sum(1 for r in rows if r[u"同じ byte(provenance)"]) == 67
        assert agg[u"provenance の body_sha256 が本文と一致した書類数"] == 67
        assert agg[u"行の節の割り当ての違い(前 → 後)"] == sum(r[u"行の節の割り当ての違い(前 → 後)"] for r in rows)
        assert agg[u"割り当ての sha256(後)"] == hashlib.sha256(u"\n".join(r[u"割り当ての sha256(後)"] for r in rows).encode("utf-8")).hexdigest()
        assert agg[u"割り当ての sha256(前)"] == hashlib.sha256(u"\n".join(r[u"割り当ての sha256(前)"] for r in rows).encode("utf-8")).hexdigest()
        w = collections_counter(rows, u"語の主張(出典の値あり。違う・一致)の単位の出どころ")
        assert agg[u"語の主張(出典の値あり。違う・一致)の単位の出どころ"] == w, p
        assert agg[u"表題が DEI 形の書類数"] == 67
    # 2 つの profile は同じ claim の集合(無改変の同じ書類・同じ claim 数)
    assert [r[u"claims"] for r in rec[u"書類別"]["P22"]] == [r[u"claims"] for r in rec[u"書類別"]["P25"]]
    # R2-5
    r5 = rec[u"R2-5"]
    n = r5[u"書類数"]
    assert n == 67
    for k in (u"名簿の外の file(zz_extra_lab.xml・jppfs_2025-11-01_lab.xml.orig)を置いても本文が同じ書類数", u"jpigp が sha256 違いの dir と jpigp が無い dir で本文が同じ書類数"):
        assert 0 <= r5[k] <= n
    assert 0 <= r5[u"jpigp が在ると本文が変わる書類数(歯)"] <= n
    # R2-6
    k = rec[u"R2-6"]
    assert k[u"入力"][u"claims"] == 39 and sum(k[u"節"].values()) == 39
    assert [r[u"id"] for r in k[u"行"]] == ["N001", "N007", "N010", "N015", "T009"]
    assert k[u"先頭の節に在る数"] == sum(1 for r in k[u"行"] if r[u"先頭の節に在る"] and r[u"節"] == u"違う")
    assert k[u"文の値の字が文の中にそのまま在る数"] == sum(1 for r in k[u"行"] if r[u"文の値の字が文(span)の中にそのまま在る(率は空白を除いて)"])
    assert k[u"単位が同じ数"] == sum(1 for r in k[u"行"] if r[u"出典の値の単位が文と同じ(語の主張は文の中でいちばん近い金額の単位)"])
    assert all(r[u"表の『文の値』の欄と一致"] for r in k[u"行"])
    assert k[u"同じ byte"] is True
    # 抜粋は P25 の 1 書類で、「違う」「要確認」が 3 行ずつ
    ex = rec[u"抜粋"]
    assert ex[u"profile"] == "P25" and ex[u"doc"] in docs
    assert len(ex[u"違う(先頭 3 行)"][u"行"]) == 3 and len(ex[u"要確認(先頭 3 行)"][u"行"]) == 3
    row = [r for r in rec[u"書類別"]["P25"] if r[u"doc"] == ex[u"doc"]][0]
    assert row[u"本文の sha256(既定)"] == ex[u"本文の sha256"] and row[u"表題"] == ex[u"表題"]
    assert row[u"節"][u"違う"] >= 3 and row[u"節"][u"要確認"] >= 3
    assert ex[u"末尾の 2 行"][0] == u"" and ex[u"末尾の 2 行"][1].startswith(u"<sub>") and ex[u"末尾の 2 行"][1].endswith(u"に置いた。</sub>")


def collections_counter(rows, key):
    t = {}
    for r in rows:
        for k, v in r[key].items():
            t[k] = t.get(k, 0) + v
    return dict(sorted(t.items()))


def check_inputs(rec):
    z = rec[u"入力の sha256"]
    docs = z[u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"]
    lines = sorted(u"%s\t%s" % (d, s) for d, s in docs.items())
    assert hashlib.sha256(u"\n".join(lines).encode("utf-8")).hexdigest() == DOCS67_DIGEST, u"書類 67 本の digest が違う"
    assert z["fixtures/xbrl/point_prior_2026-10-20.json"] == PP_SHA
    assert z["fixtures/xbrl/customer_report_2026-10-21.json"] == OLD_REC_SHA == sha_path(OLD_REC), u"段 1 の記録が動いている"
    assert z["seal"] == sha_path(SEAL), u"封が測った時点から動いている"
    assert rec[u"R2-6"][u"入力"][u"sha256"] == CUSTOMER_OUT_SHA
    assert rec[u"環境"][u"名簿の file の sha256(起動時に照合)"] == ROSTER_SHAS
    assert rec[u"環境"][u"比べた profile"] == [u"P22(既定。profile を渡さない)", u"P25(明示)"]


def judgments(rec, seal):
    """R2-1〜R2-7 を、記録の行と封の字から門が自分で求める。"""
    B = seal_bounds(seal)
    old = jload(OLD_REC)
    out = {}
    ok = True
    for p in BOTH:
        a = rec[u"集計"][p]
        ok = ok and a[u"節"] == B["sections"][p] == dict((k, old[u"集計"][p][u"節"][k]) for k in SECTIONS)
        ok = ok and a[u"行の節の割り当ての違い(前 → 後)"] == 0 and a[u"割り当ての sha256(後)"] == a[u"割り当ての sha256(前)"]
        ok = ok and all(a[u"節"][k] == a[u"節(c13a746 の module)"][k] for k in SECTIONS)
    out["R2-1"] = u"当たり" if ok else u"外れ"
    b = rec[u"集計"]["P25"]
    lo, hi = B["unread"]
    unread = b[u"読み取れない(金額の claim で span に同じ金額の字が無い)"][u"計"]
    out["R2-2"] = u"当たり" if (b[u"単位の食い違い 後"][u"計"] == 0 and b[u"独立: 単位の食い違い 後"][u"計"] == 0 and lo <= unread <= hi) else u"外れ"
    lo, hi = B["unres"]
    out["R2-3"] = u"当たり" if lo <= b[u"ラベルが引けず名前のまま出た行 後(違う・一致)"][u"計"] <= hi else u"外れ"
    ok = True
    for p in BOTH:
        a = rec[u"集計"][p]
        ok = ok and a[u"本文の 64 桁の hex 後(既定)"] == 0 and a[u"本文の 64 桁の hex 後(--full)"] == 0 and a[u"本文の『engine の指紋』の行 後"] == 0
        ok = ok and a[u"同じ byte の書類数(本文 既定)"] == a[u"同じ byte の書類数(本文 --full)"] == a[u"同じ byte の書類数(provenance)"] == a[u"書類数"]
    out["R2-4"] = u"当たり" if ok else u"外れ"
    r5 = rec[u"R2-5"]
    n = r5[u"書類数"]
    ok = (r5[u"名簿の外の file(zz_extra_lab.xml・jppfs_2025-11-01_lab.xml.orig)を置いても本文が同じ書類数"] == n
          and r5[u"jpigp が sha256 違いの dir と jpigp が無い dir で本文が同じ書類数"] == n
          and r5[u"sha256 違いの dir の jpigp の状態"] == [[u"jpigp_2025-11-01_lab.xml", u"sha256_mismatch"]]
          and r5[u"jpigp が無い dir の jpigp の状態"] == [[u"jpigp_2025-11-01_lab.xml", u"missing"]]
          and r5[u"jpigp が在ると本文が変わる書類数(歯)"] >= 1)
    out["R2-5"] = u"当たり" if ok else u"外れ"
    k = rec[u"R2-6"]
    out["R2-6"] = u"当たり" if (k[u"先頭の節に在る数"] == 5 and k[u"文の値の字が文の中にそのまま在る数"] == 5 and k[u"単位が同じ数"] == 5 and k[u"同じ byte"]) else u"外れ"
    c7 = rec[u"R2-7"]
    zero = all(v == u"0 行" for v in c7[u"HEAD からの差分(git diff --numstat)"].values()) and c7[u"core/ の HEAD からの差分"] == u"0 行"
    same = all(c7[u"sha16"][rel] == want for rel, want in UNTOUCHED.items())
    moved = c7[u"engine の指紋"][u"adapter_xbrl_py_sha256"] != ENGINE_ADAPTER_SHA_STAGE1
    out["R2-7"] = u"当たり" if (zero and same and moved and c7[u"engine の指紋"][u"adapter_xbrl_py_files"] == 16 and c7[u"engine の指紋"][u"core_py_sha256"] == ENGINE_FP["core_py_sha256"]) else u"外れ"
    return out


def check_judgments(rec, seal):
    got = judgments(rec, seal)
    for tag, v in got.items():
        assert rec[u"予測の判定"][tag][u"判定"] == v, (tag, v, rec[u"予測の判定"][tag][u"判定"])
    assert sorted(rec[u"予測の判定"]) == sorted(got) == ["R2-%d" % i for i in range(1, 8)]


def declared(seal_rel):
    return bool(subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", seal_rel], cwd=ROOT, capture_output=True, text=True).stdout.split())


def check_untouched_and_module(rec):
    c7 = rec[u"R2-7"]
    for rel, want in sorted(UNTOUCHED.items()):
        got = sha16(rel)
        if got != want and rel in UNTOUCHED_LATER:
            later, seal_rel = UNTOUCHED_LATER[rel]
            assert declared(seal_rel), u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel)
            assert got == later, u"**%s が、宣言された遷移の値とも違う**" % rel
        else:
            assert got == want, u"**%s が動いている(この封は触らない)**" % rel
        assert c7[u"sha256"][rel][:16] == want
    assert c7[u"report_customer.py の sha256"][:16] == MODULE_SHA16
    now = sha_path(os.path.join(ROOT, MODULE_REL))
    if now != c7[u"report_customer.py の sha256"]:
        assert declared(MODULE_LATER["seal"]), u"**module が測った時点から動いているのに、遷移を宣言した封が履歴に無い**"
        assert now[:16] == MODULE_LATER["sha16"], u"**module が、宣言された遷移の値とも違う**"
    from adapters.xbrl import verify_document as VD
    fp = VD.engine_fingerprint()
    for k, v in ENGINE_FP.items():
        if fp[k] != v and k in ENGINE_FP_LATER:
            later, seal_rel = ENGINE_FP_LATER[k]
            assert declared(seal_rel), u"**engine の指紋 %s が動いているのに、遷移を宣言した封が履歴に無い**" % k
            assert fp[k] == later, u"**engine の指紋 %s が、宣言された遷移の値とも違う**" % k
        else:
            assert fp[k] == v, u"**engine の指紋 %s が測った時点から動いている(測り直す)**" % k
    assert c7[u"engine の指紋"] == ENGINE_FP
    assert c7[u"core/ の HEAD からの差分"] == u"0 行"


# ----------------------------------------------------------------------------------------------------------------
# 文書(記録から作った字と完全一致)
def render_blocks(rec):
    B = {}
    pred = {"R2-1": u"節の件数は段 1 の記録と全く同じ・行の節の割り当ても全行同じ",
            "R2-2": u"P25 明示で単位の食い違い 0(前 1,480)・読み取れない 0〜20 / 4,083",
            "R2-3": u"ラベルが引けず要素名・区分名の字のまま出た行(違う・一致)0〜5(前 329)",
            "R2-4": u"本文の 64 桁の hex 0(前 201)・同じ入力から同じバイト列(本文・json)67 / 67 × 2 profile",
            "R2-5": u"ラベルの名簿の外の file を置いても本文のバイト列が変わらない",
            "R2-6": u"客 A の 5 件は先頭の「違う」に 5 / 5・文の値の字が文と同じ",
            "R2-7": u"report.py ほか 6 file は 0 行・engine の指紋は report_customer.py の分だけ動く"}
    L = [u"| # | 封の予測 | 実測 | 判定 |", u"|---|---|---|---|"]
    for tag in ("R2-%d" % i for i in range(1, 8)):
        j = rec[u"予測の判定"][tag]
        L.append(u"| **%s** | %s | %s | %s |" % (tag, cell(pred[tag]), cell(j[u"実測"]), j[u"判定"]))
    B[u"予測"] = u"\n".join(L)
    a, b = rec[u"集計"]["P22"], rec[u"集計"]["P25"]
    # 節の件数
    L = [u"| 節 | P22(既定)前 → 後 | P25(明示)前 → 後 |", u"|---|---|---|"]
    for k in SECTIONS:
        L.append(u"| %s | %s → %s | %s → %s |" % (k, comma(a[u"節(c13a746 の module)"][k]), comma(a[u"節"][k]), comma(b[u"節(c13a746 の module)"][k]), comma(b[u"節"][k])))
    L.append(u"| 和 | %s | %s |" % (comma(a[u"節の和"]), comma(b[u"節の和"])))
    L.append(u"| 行の節の割り当ての違い | %s | %s |" % (comma(a[u"行の節の割り当ての違い(前 → 後)"]), comma(b[u"行の節の割り当ての違い(前 → 後)"])))
    L.append(u"| 割り当ての sha256(前 = 後) | `%s` | `%s` |" % (a[u"割り当ての sha256(後)"][:16], b[u"割り当ての sha256(後)"][:16]))
    B[u"節"] = u"\n".join(L)
    # 単位
    L = [u"| P25 明示 | 違う | 要確認 | 判断しない | 一致 | 計 |", u"|---|---|---|---|---|---|"]
    for key, label in ((u"金額の claim", u"金額の claim"), (u"金額の claim で文の字が読めた", u"文の字の金額が読めた"),
                       (u"読み取れない(金額の claim で span に同じ金額の字が無い)", u"読み取れない"),
                       (u"単位の食い違い 前(文の字の単位 ≠ 表に出した単位)", u"単位の食い違い 前"), (u"単位の食い違い 後", u"単位の食い違い 後")):
        d = b[key]
        L.append(u"| %s | %s | %s | %s | %s | %s |" % (label, comma(d[u"違う"]), comma(d[u"要確認"]), comma(d[u"判断しない"]), comma(d[u"一致"]), comma(d[u"計"])))
    for key, label in ((u"独立: 金額の行(『文の値』の列が金額の単位で終わる)", u"独立に数えた金額の行"), (u"独立: 単位の食い違い 前(c13a746 の本文)", u"独立に数えた食い違い 前"),
                       (u"独立: 単位の食い違い 後", u"独立に数えた食い違い 後")):
        d = b[key]
        L.append(u"| %s | %s | %s | %s | %s | %s |" % (label, comma(d[u"違う"]), comma(d[u"要確認"]), comma(d[u"判断しない"]), comma(d[u"一致"]), comma(d[u"計"])))
    B[u"単位"] = u"\n".join(L)
    L = [u"| 語の主張(出典の値あり。違う・一致) | P22(既定) | P25(明示) |", u"|---|---|---|"]
    for k, label in ((u"word_span", u"単位を文の中のいちばん近い金額の字から取った"), (u"word_doc", u"単位を書類で最も多い単位に落とした(文から読み取っていない)")):
        L.append(u"| %s | %s | %s |" % (label, comma(a[u"語の主張(出典の値あり。違う・一致)の単位の出どころ"].get(k, 0)), comma(b[u"語の主張(出典の値あり。違う・一致)の単位の出どころ"].get(k, 0))))
    L.append(u"| 　うち円以外の単位に直った(前は円で出ていた) | %s | %s |" % (comma(sum(a[u"語の主張で円以外の単位に直った行"].values())), comma(sum(b[u"語の主張で円以外の単位に直った行"].values()))))
    B[u"語"] = u"\n".join(L)
    L = [u"| 「一致」の節の主表示(P25 明示) | 行 |", u"|---|---|",
         u"| 文の値と比べた行 | %s |" % comma(b[u"一致の主表示を比べた行"]),
         u"| 主表示が文の値と違って見える行 前(四捨五入だけ) | %s |" % comma(b[u"一致の主表示が文と違って見える行 前"]),
         u"| 主表示が文の値と違って見える行 後(文の値と同じになる丸め方を選ぶ) | %s |" % comma(b[u"一致の主表示が文と違って見える行 後"])]
    B[u"主表示"] = u"\n".join(L)
    # ラベル
    L = [u"| 違う・一致の行 | P22(既定)前 → 後 | P25(明示)前 → 後 |", u"|---|---|---|"]
    for label, key in ((u"ラベルが引けず名前のまま出た行(直接数えた)", u"ラベルが引けず名前のまま出た行 %s(違う・一致)"),
                       (u"英字の正規表現に当たる行(試作の数え方)", u"英字の正規表現に当たる行 %s(違う・一致)")):
        L.append(u"| %s | %s → %s | %s → %s |" % (label, comma(a[key % u"前"][u"計"]), comma(a[key % u"後"][u"計"]), comma(b[key % u"前"][u"計"]), comma(b[key % u"後"][u"計"])))
    L.append(u"| 　うち後の内訳 違う / 一致(英字の正規表現) | %s / %s | %s / %s |" % (
        comma(a[u"英字の正規表現に当たる行 後(違う・一致)"][u"違う"]), comma(a[u"英字の正規表現に当たる行 後(違う・一致)"][u"一致"]),
        comma(b[u"英字の正規表現に当たる行 後(違う・一致)"][u"違う"]), comma(b[u"英字の正規表現に当たる行 後(違う・一致)"][u"一致"])))
    B[u"ラベル"] = u"\n".join(L)
    # hex と byte
    L = [u"| 検査 | P22(既定) | P25(明示) |", u"|---|---|---|"]
    L.append(u"| 本文の 64 桁の hex 前(c13a746・既定) | %s | %s |" % (comma(a[u"本文の 64 桁の hex 前(c13a746・既定)"]), comma(b[u"本文の 64 桁の hex 前(c13a746・既定)"])))
    L.append(u"| 本文の 64 桁の hex 後(既定) | %s | %s |" % (comma(a[u"本文の 64 桁の hex 後(既定)"]), comma(b[u"本文の 64 桁の hex 後(既定)"])))
    L.append(u"| 本文の 64 桁の hex 後(--full) | %s | %s |" % (comma(a[u"本文の 64 桁の hex 後(--full)"]), comma(b[u"本文の 64 桁の hex 後(--full)"])))
    L.append(u"| 本文の『engine の指紋』の行 後 | %s | %s |" % (comma(a[u"本文の『engine の指紋』の行 後"]), comma(b[u"本文の『engine の指紋』の行 後"])))
    L.append(u"| 同じ byte の書類数 本文(既定) | %s | %s |" % (comma(a[u"同じ byte の書類数(本文 既定)"]), comma(b[u"同じ byte の書類数(本文 既定)"])))
    L.append(u"| 同じ byte の書類数 本文(--full) | %s | %s |" % (comma(a[u"同じ byte の書類数(本文 --full)"]), comma(b[u"同じ byte の書類数(本文 --full)"])))
    L.append(u"| 同じ byte の書類数 provenance | %s | %s |" % (comma(a[u"同じ byte の書類数(provenance)"]), comma(b[u"同じ byte の書類数(provenance)"])))
    L.append(u"| provenance の body_sha256 が本文と一致した書類数 | %s | %s |" % (comma(a[u"provenance の body_sha256 が本文と一致した書類数"]), comma(b[u"provenance の body_sha256 が本文と一致した書類数"])))
    L.append(u"| 表題が DEI 形の書類数 | %s | %s |" % (comma(a[u"表題が DEI 形の書類数"]), comma(b[u"表題が DEI 形の書類数"])))
    B[u"hex"] = u"\n".join(L)
    # 名簿
    r5 = rec[u"R2-5"]
    L = [u"| 名簿の検査(P25 明示の %d 書類) | 書類数 |" % r5[u"書類数"], u"|---|---|"]
    L.append(u"| 名簿の外の file を置いても本文が同じ | %s |" % comma(r5[u"名簿の外の file(zz_extra_lab.xml・jppfs_2025-11-01_lab.xml.orig)を置いても本文が同じ書類数"]))
    L.append(u"| sha256 違いの jpigp と jpigp 無しで本文が同じ | %s |" % comma(r5[u"jpigp が sha256 違いの dir と jpigp が無い dir で本文が同じ書類数"]))
    L.append(u"| jpigp が在ると本文が変わる(検査の歯) | %s |" % comma(r5[u"jpigp が在ると本文が変わる書類数(歯)"]))
    L.append(u"| sha256 違いの jpigp の状態 | %s |" % cell(u"・".join(x[1] for x in r5[u"sha256 違いの dir の jpigp の状態"])))
    L.append(u"| jpigp が無い dir の状態 | %s |" % cell(u"・".join(x[1] for x in r5[u"jpigp が無い dir の jpigp の状態"])))
    B[u"名簿"] = u"\n".join(L)
    # 客 A
    k = rec[u"R2-6"]
    L = [u"| 答え合わせ | id | 節 | 文の値 | 出典の値 |", u"|---|---|---|---|---|"]
    for r in k[u"行"]:
        L.append(u"| %s | %s | %s | %s | %s |" % (r[u"答え合わせ"], r[u"id"], r[u"節"], cell(r[u"文の値"]), cell(r[u"出典の値"])))
    L.append(u"| 節の件数(39 claim) | | 違う %d / 要確認 %d / 対象外 %d / 判断しない %d / 一致 %d | | |" % tuple(k[u"節"][s] for s in SECTIONS))
    B[u"客 A"] = u"\n".join(L)
    # 抜粋
    ex = rec[u"抜粋"]
    L = [u"```", ex[u"表題"], u"", u"## 1. 違う(先頭 3 行) ― %s・P25" % ex[u"doc"], u"", ex[u"違う(先頭 3 行)"][u"見出し行"], u"|---|---|---|---|---|"] + ex[u"違う(先頭 3 行)"][u"行"]
    L += [u"", u"## 2. 要確認(先頭 3 行) ― %s・P25" % ex[u"doc"], u"", ex[u"要確認(先頭 3 行)"][u"見出し行"], u"|---|---|---|---|"] + ex[u"要確認(先頭 3 行)"][u"行"]
    L += [u"", u"(末尾)", u"", ex[u"末尾の 2 行"][1], u"```"]
    B[u"抜粋"] = u"\n".join(L)
    # 指紋
    c7 = rec[u"R2-7"]
    L = [u"| file | sha256 | 封の commit からの差分 |", u"|---|---|---|"]
    for rel in sorted(c7[u"sha256"]):
        L.append(u"| `%s` | `%s` | %s |" % (rel, c7[u"sha256"][rel][:16], c7[u"HEAD からの差分(git diff --numstat)"][rel]))
    L.append(u"| `%s`(直した) | `%s` | 行数 %d |" % (MODULE_REL, c7[u"report_customer.py の sha256"][:16], c7[u"report_customer.py の行数"]))
    fp = c7[u"engine の指紋"]
    L.append(u"| engine の束ねた指紋 adapter_xbrl_py_sha256 | `%s`(%d file) | 段 1 は `%s` |" % (fp[u"adapter_xbrl_py_sha256"][:16], fp[u"adapter_xbrl_py_files"], ENGINE_ADAPTER_SHA_STAGE1[:16]))
    L.append(u"| `core/` | | %s |" % c7[u"core/ の HEAD からの差分"])
    B[u"指紋"] = u"\n".join(L)
    return B


def prose_facts(rec):
    return {
        u"書類": u"書類は %d 本(経営分析の文を持つ)。" % rec[u"書類の数"][u"経営分析の文を持つ"],
        u"和": u"claim の合計は %s、節の和は %s(P22)・%s(P25)。" % (comma(rec[u"集計"]["P22"][u"claims"]), comma(rec[u"集計"]["P22"][u"節の和"]), comma(rec[u"集計"]["P25"][u"節の和"])),
        u"客 A の claim": u"客 A の出力は %d claim(P22)。" % rec[u"R2-6"][u"入力"][u"claims"],
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
    for lit in (u"は一字も触らない", u"門で縛れない", u"封と実物の食い違い", u"一回限りの手の実測", u"本文全体の sha256", u"迷った点", u"書類の種類", u"名簿に無い file"):
        assert lit in doc, lit
    res = residual_numbers(doc, rec)
    assert res == ALLOWED_RESIDUAL, u"文書の散文に、記録に縛られない数が在る: %s" % res


def have_cache(docs):
    return all(os.path.exists(os.path.join(CACHE, d + ".zip")) for d in docs)


def labels_ok():
    return all(os.path.exists(os.path.join(STD_LABELS, fn)) for fn in ROSTER_SHAS)


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
        # 封の幅をこの門が自分で読んだ値(封が動けば赤)
        B = seal_bounds(self.seal)
        self.assertEqual((B["unread"], B["unread_den"], B["unres"]), ((0, 20), 4083, (0, 5)))

    def test_4_document_tables_equal_the_record(self):
        check_doc(self.rec, self.doc)

    def test_5_module_and_untouched_files_are_the_ones_measured(self):
        check_untouched_and_module(self.rec)
        self.assertEqual(self.rec[u"R2-7"][u"adapters/xbrl の .py の数"], 16)

    def test_6_seal_numbers_equal_the_prediction_table_and_section_0(self):
        # 封 §0 の数(試作の数え方)が、この測定の前の値と一致している(封の数の再現)
        b = self.rec[u"集計"]["P25"]
        # 封 §0 の試作の数 1,480(83/459/24/914)は「805千円」を漢数字形(単位 円)と読む誤読を含んでいた。直した読み取りで測り直すと 21 行(3/7/0/11)増えて 1,501。
        self.assertEqual(b[u"単位の食い違い 前(文の字の単位 ≠ 表に出した単位)"], {u"違う": 86, u"要確認": 466, u"対象外": 0, u"判断しない": 24, u"一致": 925, u"計": 1501})
        self.assertEqual(b[u"独立: 単位の食い違い 前(c13a746 の本文)"][u"計"], 1496)
        self.assertEqual(b[u"ラベルが引けず名前のまま出た行 前(違う・一致)"], {u"違う": 54, u"一致": 275, u"計": 329})
        self.assertEqual(b[u"本文の 64 桁の hex 前(c13a746・既定)"], 201)
        self.assertEqual(b[u"金額の claim で文の字が読めた"][u"計"], 4083)
        self.assertEqual(b[u"語の主張(出典の値あり。違う・一致)の単位の出どころ"].get(u"word_doc"), 444)
        self.assertEqual(sum(b[u"語の主張で円以外の単位に直った行"].values()), 1469)        # 封 §0 (a) は 1,466 行。千円の誤読(語の主張 3 行)を直したので 1,469
        # 直接数えた『名前のまま出た行』は 0、試作の正規表現では会社のラベル自体の英字の 7 行
        self.assertEqual(b[u"ラベルが引けず名前のまま出た行 後(違う・一致)"][u"計"], 0)
        self.assertEqual(b[u"英字の正規表現に当たる行 後(違う・一致)"][u"計"], 7)

    def test_7_cache_inputs_match_the_record(self):
        docs = self.rec[u"入力の sha256"][u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"]
        if not have_cache(sorted(docs)):
            self.skipTest(u"cache が無い")
        for d, s in sorted(docs.items()):
            self.assertEqual(sha_path(os.path.join(CACHE, d + ".zip")), s, d)

    def test_8_the_seal_precedes_this_result(self):
        self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", SEAL_REL).stdout.split(), u"封が履歴に無い")
        self.assertEqual(git("diff", "--numstat", "HEAD", "--", SEAL_REL).stdout.strip(), u"", u"封が封の commit から変わっている")

    def test_9_the_body_has_no_fingerprint_line_and_the_record_holds_the_whole_body_sha256(self):
        from adapters.xbrl import report_customer as RC
        out = jload(os.path.join(ROOT, "fixtures", "xbrl", "entry_output_S100Z4N9_original_2026-10-13.json"))
        md = RC.render_markdown(out, None, False)
        self.assertNotIn(u"engine の指紋", md)
        self.assertEqual(re.findall(r"\b[0-9a-f]{64}\b", md), [])
        # HEAD を変えても engine の指紋を変えても本文は変わらない(段 1 の『末尾の 1 行を除く』細工は要らない)
        out2 = copy.deepcopy(out)
        out2["engine"]["git_commit"] = "0" * 40
        out2["engine"]["adapter_xbrl_py_sha256"] = "1" * 64
        self.assertEqual(RC.render_markdown(out2, None, False), md)
        # provenance は変わる(指紋はそちらに在る)
        self.assertNotEqual(RC.render_provenance(out2, md, [], None, None), RC.render_provenance(out, md, [], None, None))


def run_script(args):
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=ROOT, capture_output=True, text=True)


def drop_time(rows):
    return [dict((k, v) for k, v in r.items() if k != u"verify 秒") for r in rows]


class RerunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)

    def _need(self, docs):
        if not have_cache(docs):
            self.skipTest(u"cache が無い")
        if not labels_ok():
            self.skipTest(u"標準タクソノミのラベルの 3 file が無い(fixtures/xbrl/TAXONOMY_LABELS_README.md)")

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

    @unittest.skipUnless(RUN_HEAVY, u"AUDIT_CORE_CUSTOMER_REPORT_FIX=1 のときだけ走る(全部の走らせ直し。約 二分)。客 A の出力は AUDIT_CORE_CUSTOMER_OUT で渡す")
    def test_heavy_everything_matches_the_record(self):
        if not (have_cache(sorted(self.rec[u"入力の sha256"][u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"])) and labels_ok()):
            self.fail(u"AUDIT_CORE_CUSTOMER_REPORT_FIX=1 なのに cache かラベルが揃っていない")
        cust = os.environ.get("AUDIT_CORE_CUSTOMER_OUT")
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "all.json")
            p = run_script(["--stage", "all", "--out", out] + (["--customer-out", cust] if cust else []))
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            got = jload(out)
        for prof in BOTH:
            self.assertEqual(drop_time(got[u"書類別"][prof]), drop_time(self.rec[u"書類別"][prof]), prof)
            self.assertEqual(got[u"集計"][prof], self.rec[u"集計"][prof], prof)
        self.assertEqual(got[u"抜粋"], self.rec[u"抜粋"])
        self.assertEqual(got[u"R2-5"], self.rec[u"R2-5"])
        self.assertEqual(got[u"R2-7"], self.rec[u"R2-7"])
        if cust:
            self.assertEqual(got[u"R2-6"], self.rec[u"R2-6"])
        for tag in ["R2-%d" % i for i in range(1, 8) if i != 6 or cust]:
            self.assertEqual(got[u"予測の判定"][tag][u"判定"], self.rec[u"予測の判定"][tag][u"判定"], tag)


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

    def _miss(self, r, tag):
        self.assertEqual(judgments(r, self.seal)[tag], u"外れ", tag)

    def test_baseline_is_green(self):
        check_record(self.rec)
        check_inputs(self.rec)
        check_judgments(self.rec, self.seal)
        check_doc(self.rec, self.doc)
        check_untouched_and_module(self.rec)
        self.assertEqual(set(judgments(self.rec, self.seal).values()), {u"当たり"})

    def test_m1_a_section_count_that_does_not_sum_to_the_claims_is_red(self):
        r = self._mut()
        r[u"書類別"]["P22"][3][u"節"][u"一致"] += 1
        self._red(check_record, r)

    def test_m2_a_document_whose_sections_differ_from_the_stage_1_record_is_red(self):
        r = self._mut()
        row = r[u"書類別"]["P25"][5]
        row[u"節"][u"違う"] += 1
        row[u"節"][u"一致"] -= 1
        row[u"節(c13a746 の module)"] = dict(row[u"節"])       # 前と後が揃っていても、段 1 の記録とは違う
        self._red(check_record, r)

    def test_m3_a_row_assignment_difference_is_red_and_a_miss_for_r2_1(self):
        r = self._mut()
        r[u"書類別"]["P25"][7][u"行の節の割り当ての違い(前 → 後)"] = 1
        self._red(check_record, r)
        r = self._mut()
        r[u"集計"]["P25"][u"行の節の割り当ての違い(前 → 後)"] = 1
        self._miss(r, "R2-1")
        r = self._mut()
        r[u"集計"]["P25"][u"割り当ての sha256(後)"] = "0" * 64
        self._miss(r, "R2-1")

    def test_m4_the_aggregate_must_equal_the_rows(self):
        r = self._mut()
        r[u"集計"]["P25"][u"単位の食い違い 後"][u"計"] += 1
        self._red(check_record, r)
        r = self._mut()
        r[u"集計"]["P22"][u"本文の 64 桁の hex 後(既定)"] += 1
        self._red(check_record, r)

    def test_m5_a_nondeterministic_document_is_red(self):
        r = self._mut()
        r[u"書類別"]["P22"][0][u"同じ byte(provenance)"] = False
        self._red(check_record, r)

    def test_m6_hex_in_the_body_or_a_fingerprint_line_is_a_miss_for_r2_4(self):
        r = self._mut()
        r[u"集計"]["P25"][u"本文の 64 桁の hex 後(既定)"] = 1
        self._miss(r, "R2-4")
        r = self._mut()
        r[u"集計"]["P22"][u"本文の『engine の指紋』の行 後"] = 1
        self._miss(r, "R2-4")

    def test_m7_unit_mismatch_or_too_many_unreadable_is_a_miss_for_r2_2(self):
        r = self._mut()
        r[u"集計"]["P25"][u"単位の食い違い 後"][u"計"] = 1
        self._miss(r, "R2-2")
        r = self._mut()
        r[u"集計"]["P25"][u"読み取れない(金額の claim で span に同じ金額の字が無い)"][u"計"] = 21
        self._miss(r, "R2-2")

    def test_m7b_the_independent_count_must_be_zero_for_r2_2(self):
        r = self._mut()
        r[u"集計"]["P25"][u"独立: 単位の食い違い 後"][u"計"] = 1
        self._miss(r, "R2-2")
        r = self._mut()
        r[u"書類別"]["P25"][4][u"独立: 単位の食い違い 後"][u"一致"] += 1
        self._red(check_record, r)

    def test_m7c_the_match_display_after_cannot_exceed_before(self):
        r = self._mut()
        r[u"集計"]["P25"][u"一致の主表示が文と違って見える行 後"] = r[u"集計"]["P25"][u"一致の主表示が文と違って見える行 前"] + 1
        self._red(check_record, r)

    def test_m8_names_left_in_roman_letters_over_the_bound_is_a_miss_for_r2_3(self):
        r = self._mut()
        r[u"集計"]["P25"][u"ラベルが引けず名前のまま出た行 後(違う・一致)"][u"計"] = 6
        self._miss(r, "R2-3")

    def test_m9_the_roster_checks_must_hold_for_r2_5(self):
        r = self._mut()
        r[u"R2-5"][u"名簿の外の file(zz_extra_lab.xml・jppfs_2025-11-01_lab.xml.orig)を置いても本文が同じ書類数"] -= 1
        self._miss(r, "R2-5")
        r = self._mut()
        r[u"R2-5"][u"jpigp が在ると本文が変わる書類数(歯)"] = 0           # 検査に歯が無い(jpigp が本文に効いていない)なら当たりと言わない
        self._miss(r, "R2-5")
        r = self._mut()
        r[u"R2-5"][u"sha256 違いの dir の jpigp の状態"] = [[u"jpigp_2025-11-01_lab.xml", u"used"]]
        self._miss(r, "R2-5")

    def test_m10_the_customer_a_answers_must_hold_for_r2_6(self):
        r = self._mut()
        r[u"R2-6"][u"単位が同じ数"] = 4
        self._miss(r, "R2-6")
        r = self._mut()
        r[u"R2-6"][u"行"][2][u"先頭の節に在る"] = False
        self._red(check_record, r)

    def test_m11_a_nonzero_diff_or_a_moved_untouched_file_is_a_miss_for_r2_7(self):
        r = self._mut()
        r[u"R2-7"][u"HEAD からの差分(git diff --numstat)"][u"adapters/xbrl/report.py"] = u"3\t1\tadapters/xbrl/report.py"
        self._miss(r, "R2-7")
        r = self._mut()
        r[u"R2-7"][u"sha16"][u"adapters/xbrl/recipes.py"] = "0" * 16
        self._miss(r, "R2-7")
        r = self._mut()
        r[u"R2-7"][u"engine の指紋"][u"adapter_xbrl_py_sha256"] = ENGINE_ADAPTER_SHA_STAGE1       # module の分だけ動いていない = 段 1 のまま
        self._miss(r, "R2-7")

    def test_m12_a_moved_module_or_engine_is_red(self):
        r = self._mut()
        r[u"R2-7"][u"report_customer.py の sha256"] = "0" * 64
        self._red(check_untouched_and_module, r)
        r = self._mut()
        r[u"R2-7"][u"engine の指紋"][u"adapter_xbrl_py_sha256"] = "0" * 64
        self._red(check_untouched_and_module, r)

    def test_m13_a_spoiled_input_digest_is_red(self):
        r = self._mut()
        d = r[u"入力の sha256"][u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"]
        k = sorted(d)[0]
        d[k] = "0" * 64
        self._red(check_inputs, r)
        r = self._mut()
        r[u"入力の sha256"]["fixtures/xbrl/customer_report_2026-10-21.json"] = "0" * 64
        self._red(check_inputs, r)
        r = self._mut()
        r[u"環境"][u"名簿の file の sha256(起動時に照合)"].pop("jpigp_2025-11-01_lab.xml")
        self._red(check_inputs, r)

    def test_m14_a_number_in_a_document_table_is_red(self):
        bad = self.doc.replace(u"| 和 | 7,799 | 7,799 |", u"| 和 | 7,798 | 7,799 |", 1)
        self.assertNotEqual(bad, self.doc)
        self._red(check_doc, self.rec, bad)

    def test_m15_a_number_in_a_prose_sentence_is_red(self):
        bad = self.doc.replace(u"## 一 結論\n", u"## 一 結論\n\n判定を変えた行は 12 件ある。\n", 1)
        self.assertNotEqual(bad, self.doc)
        self._red(check_doc, self.rec, bad)

    def test_m16_the_judgment_cannot_be_changed_in_the_record_alone(self):
        r = self._mut()
        r[u"予測の判定"]["R2-3"][u"判定"] = u"外れ"
        self._red(check_judgments, r, self.seal)

    def test_m17_a_changed_bound_in_the_seal_text_changes_the_judgment(self):
        bad = self.seal.replace(u"読み取れない **0〜20 / 4,083**", u"読み取れない **0〜0 / 4,083**", 1)
        self.assertNotEqual(bad, self.seal)
        r = self._mut()
        r[u"集計"]["P25"][u"読み取れない(金額の claim で span に同じ金額の字が無い)"][u"計"] = 3
        self.assertEqual(judgments(r, self.seal)["R2-2"], u"当たり")
        self.assertEqual(judgments(r, bad)["R2-2"], u"外れ")

    def test_m18_the_body_sha256_must_look_like_one(self):
        r = self._mut()
        r[u"書類別"]["P25"][2][u"本文の sha256(既定)"] = u"abc"
        self._red(check_record, r)

    def test_m19_an_excerpt_with_fewer_rows_or_a_fingerprint_tail_is_red(self):
        r = self._mut()
        r[u"抜粋"][u"違う(先頭 3 行)"][u"行"] = r[u"抜粋"][u"違う(先頭 3 行)"][u"行"][:2]
        self._red(check_record, r)
        r = self._mut()
        r[u"抜粋"][u"末尾の 2 行"][1] = u"<sub>engine の指紋: x</sub>"
        self._red(check_record, r)


if __name__ == "__main__":
    unittest.main()
