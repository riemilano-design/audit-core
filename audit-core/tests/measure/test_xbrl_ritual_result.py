# -*- coding: utf-8 -*-
u"""10 分の再現の儀式(封 docs/XBRL_RITUAL_SEAL_2026-10-20.md)の結果を縛る門。

記録: ``fixtures/xbrl/ritual_2026-10-20.json``(``measure/ritual_2026-10-20.py --out <dir>`` の ``ritual.json`` と同じ中身)。
**2026-10-20(期を縛る P22 の段 2)で既定が P21 -> P22 になったので、この記録は P22(既定)で採り直した**(通した 15 / 240)。
P21 のときの記録(通した 17 / 241。文書の本文 §0〜§5 が縛る数)は ``fixtures/xbrl/ritual_2026-10-20_p21.json``
(git の履歴 3320c8c の記録と同じバイト列。sha256 を字で留める)。本文の P21 の数は P21 の記録(``rec21``)に、README・追記・走らせ直しは
P22 の記録(``rec``)に縛る。
文書: ``docs/XBRL_RITUAL_RESULT_2026-10-20.md``。README の節: ``README.md``・``README.en.md``。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ。変異は ``MutationTest`` が毎回走らせる):
  1. 入力の zip の sha256・bytes を**字で留める**(定数から作らない)。
  2. 記録の行 241 本から 通した・止めた・分け方・型別を**数え直し**、記録の集計と一致させる。分け方は script の関数でなく、
     表記の字(元の字・後の字)から独立に求める。
  3. **同梱 zip から儀式を subprocess で走らせ直して**記録と一致(所要秒と実行環境を除く)。``HOME`` を空の dir にし、ラベルは
     ``EDINET_TAXONOMY_DIR`` で名指し、接続を潰して走らせる(``AUDIT_CORE_RITUAL=1`` のときだけ。重い ― 封 R-7 の外れ方どおり分けた)。
     ラベルが無い機械では案内を出して rc=2 で止まること(既定で走る軽い門)。
  4. 予測 R-1〜R-8 の判定を記録・封・git から門が自分で求め、文書の判定の表と一致させる。
  5. README の節を記録から作った字と**完全に一致**させる(日本語・英語)。
  6. 文書の通した 17 の表・分数を、記録から作った字と一致させる。
縛っていないもの: 文書の本文の文章、通した 17 の『読み』の正しさ(人の読み)、tests/measure 全体の所要(文書に実測を書くだけ)。
"""
import ast
import copy
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REC = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20.json")
REC21 = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20_p21.json")
DOC = os.path.join(ROOT, "docs", "XBRL_RITUAL_RESULT_2026-10-20.md")
SEAL_REL = "docs/XBRL_RITUAL_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SCRIPT = os.path.join(ROOT, "measure", "ritual_2026-10-20.py")
FALSE_PASS_REL = "measure/false_pass_2026-10-14.py"

# 2026-10-20 追記(宣言された遷移): 封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md(期を縛る P22 の段 1。engine を変える。人間の承認 2026-10-20)で
# adapters/xbrl/recipes.py と vocabulary.py だけが動いた。この門が測った時点(封の commit)の engine は 0 行だった(記録の事実、消さない)。
# 「封の commit から 0 行」を満たしたと数えるのは、(a) 動いた file がこの 2 つだけ、(b) その封が履歴に在る、(c) sha16 が宣言どおり、のときだけ。
SEAL_PERIOD_BIND = "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md"
# 2026-10-21 追記(丸めの帯 P23 の段 1): 封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 truncate_abs_band・P23・PROFILES の登録を、
# recipes.py に _mag_trunc を足した。recipes.py の 65a37869f053a60e・vocabulary.py の 25a3c0992e10daaa は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P23 の段 1 の後の値のときだけ。
SEAL_ROUNDING = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"
SEAL_VOCAB = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"    # 2026-10-21 追記: 語彙の登録と枠の取り直し P24 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"    # 2026-10-21 追記: 最後の枝 P25 の段 1(下の ENGINE_LATER の遷移)
SEAL_CUSTOMER_REPORT = "docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md"    # 2026-10-21 追記: 顧客向けの日本語の報告形(新しい module adapters/xbrl/report_customer.py。下の ENGINE_LATER の新規 file)
# 2026-10-21(語彙の登録と枠の取り直し P24 の段 1): 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に旗 vocab_2026_10_21・frame_rebind の塊(+224 行・既存の行は 1 つも書き換えない)を足した(DEFAULT_PROFILE は P22 のまま)。
# d5308700eae78c10(P23 の段 1)は残す(測った時点の値)、P24 の段 1 で 3461c3f8b7af6675。受け入れるのは、その封が履歴に在り、値が P24 の段 1 の後の値のときだけ。
# 2026-10-21(最後の枝 P25 の段 1): 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に最後の枝の証拠の判定の塊(+72 行・-0 行。既存の行は 1 つも書き換えない)、vocabulary.py に旗 last_branch_names_only_if_evidence・P25・PROFILES の登録(+7 行・-0 行)、registry_setup.py に理由 no_same_value(+2 行)を足した(DEFAULT_PROFILE は P22 のまま)。
# recipes.py の 3461c3f8b7af6675・vocabulary.py の 83498c04a7b70396・registry_setup.py の 9a0b08954cf22639(P24 の段 1)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P25 の段 1 の後の値のときだけ。
ENGINE_LATER = {"adapters/xbrl/recipes.py": ("bff243f13429b553", SEAL_LASTBRANCH),
                # 2026-10-20 追記(段 2): vocabulary.py の sha は 段 1 3320c8c で 1fdb48e7e3ba58ce(残す。測った時点の値)、段 2(DEFAULT_PROFILE を
                # P21 -> P22 にし、決定の注記を足した。vocabulary.py だけ・recipes.py は 0 行。同じ封 SEAL_PERIOD_BIND の段 2)で 25a3c0992e10daaa。
                # 2026-10-21(語彙の登録と枠の取り直し P24 の段 1): 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 2 つ・資金の句の表・P24・PROFILES の登録を足した(DEFAULT_PROFILE は P22 のまま)。
                # f7b8d925eb6787ec(P23 の段 1)は残す(測った時点の値)、P24 の段 1 で 83498c04a7b70396。受け入れるのは、その封が履歴に在り、値が P24 の段 1 の後の値のときだけ。
                "adapters/xbrl/vocabulary.py": ("27e71e9861fc5aad", SEAL_LASTBRANCH),
                # 2026-10-21(P24 の段 1): registry_setup.py に理由 other_frame を足した(+2 行)。この file はこの門が測った時点では動いていない(封の commit から 0 行だった)。
                "adapters/xbrl/registry_setup.py": ("f42ffe23aaa7673b", SEAL_LASTBRANCH),
                # 2026-10-21(顧客向けの日本語の報告形): 封 docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md(engine 側に module を足す。人間の事前承認 2026-10-21)で、新しい file adapters/xbrl/report_customer.py を足した
                # (既存の file は 1 字も触らない。report.py・verify_document.py・vocabulary.py・recipes.py・registry_setup.py は 0 行)。新規 file なので「測った時点の値」は無い。受け入れるのは、その封が履歴に在り、sha16 が下の値のときだけ。
                "adapters/xbrl/report_customer.py": ("d82481697762d167", SEAL_CUSTOMER_REPORT)}


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

ZIP_REL = "fixtures/xbrl/ai_prose_instance_2026-10-09.zip"
ZIP = os.path.join(ROOT, ZIP_REL)
README_JA = os.path.join(ROOT, "README.md")
README_EN = os.path.join(ROOT, "README.en.md")

#: **字で留める**(定数から作らない)。
ZIP_SHA256 = "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799"
ZIP_BYTES = 580260
#: 記録を採ったときの engine(core/・adapters/ の 36 file。__pycache__ を除く)の束ねた sha256。記録の事実として縛る
#: (いまの作業木との生の比較は置かない ― docstring 1 行の直しで赤くしない)。
ENGINE_BUNDLE = "5b5f030071188864092d0fba8f655ee1f413c08ebbb1769190511bd8720ccbee"        # P21 の記録(文書の本文)を採ったとき
#: P22(既定)で採り直した記録(2026-10-20 段 2)を採ったときの engine の束ねた sha256。
ENGINE_BUNDLE22 = "a0c92547a59802172340fa73c1aa97eac4763b1adaac62e8ab57aa5ad6b24e34"
#: P21 のときの記録の写し(git の履歴 3320c8c の ritual_2026-10-20.json と同じバイト列)の sha256。字で留める。
REC21_SHA256 = "dad4c56e7aeeadd1c1d07fe6dc3f844f62be2d127a5e7f9cac10df761ecac6d8"
#: 封 §0-1 の先に測った数(字で留める。R-2・R-5 の中心)
LABEL_SHAS = {"jppfs_2025-11-01_lab.xml": "bf56ea1585afe426b398a9053ec4de4dbeafc211a53675b5d6d19453e4e04bf4",
              "jpcrp_2025-11-01_lab.xml": "df9c23764ec9a63cb65b5ef62e79a2907c590523797421442ea2a60e334cd684"}
RUN_HEAVY = os.environ.get("AUDIT_CORE_RITUAL") == "1"
HEAVY_SKIP_REASON = (u"AUDIT_CORE_RITUAL=1 のときだけ走る(儀式を subprocess で 1 回走らせ直す。20 秒超。"
                     u"封 R-7 の外れ方どおり既定から分けた)")
#: 他の席の機械の実測(再現できない。字で留める)。R-7 の判定に使う: tests/measure 全体の所要秒。
R7_TOTAL_SECONDS = {u"司令塔の機械": (134.2, 140.9), u"監査席の機械": (164.0, 168.0)}
FACT = {"claims": 412, "states": {"GROUNDED": 330, "POINTER_NOT_FOUND": 16, "UNVERIFIABLE": 41, "VALUE_MISMATCH": 25},
        "sites": 304, "mismatch": 8, "targets": 241, "detected": 224, "passed": 17, "in_band": 16, "degenerate": 1}      # P21(封 §0-1・文書の本文)
#: P22(既定)で採り直した記録(2026-10-20 段 2)の先に測った数。素の書類で GROUNDED 1 行が VALUE_MISMATCH になり、注入の対象は 241 -> 240。
FACT22 = {"claims": 412, "states": {"GROUNDED": 329, "POINTER_NOT_FOUND": 16, "UNVERIFIABLE": 41, "VALUE_MISMATCH": 26},
          "sites": 304, "mismatch": 8, "targets": 240, "detected": 225, "passed": 15, "in_band": 14, "degenerate": 1}

K_PASSED, K_DETECTED, K_CLASS = u"通した", u"止めた", u"通した の分け方"
K_MOVED = u"通した のうち参照先が動いた(注入の前後で GROUNDED の参照先が違う)"
K_ENV = u"実行環境"
K_SEC = u"所要秒"
C_DEG = u"退化値(字は変わるが値が変わらない)"
C_IN = u"丸めの帯の中(±1 最小単位)"
C_OUT = u"帯の外(±1 最小単位より大きい)"
FRAC_RE = re.compile(r"(\d[\d,]*) / (\d[\d,]*) = (\d+\.\d)%")


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def F(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b)


# ----------------------------------------------------------------------------------------------------------------
# 字から独立に求める部品(script の classify を使わない)
def _digits(raw):
    m = re.search(r"\d[\d,]*(?:\.\d+)?", raw)
    return m.group(0)


def indep_class(row):
    u"""元の字・後の字・値から、分け方を求める。script と別の書き方(字の桁の差で見る)。"""
    a, b = _digits(row[u"元の字"]), _digits(row[u"後の字"])
    v0, v1 = row[u"元の値"], row[u"後の値"]
    if abs(v1 - v0) <= 1e-9 * max(1.0, abs(v0)):
        return C_DEG
    dec = len(a.split(".", 1)[1]) if "." in a else 0
    n0, n1 = float(a.replace(",", "")), float(b.replace(",", ""))
    if n0 == 0:
        return C_OUT
    unit_scale = abs(v0) / n0           # 表記の 1 に当たる値
    step = unit_scale * 10 ** (-dec)
    return C_IN if abs(v1 - v0) <= step * (1 + 1e-9) else C_OUT


# ----------------------------------------------------------------------------------------------------------------
# 記録の検査(純関数。変異の標本に同じ関数を当てる)
def check_input_bytes(zb):
    assert sha_bytes(zb) == ZIP_SHA256, u"zip の sha256 が字で留めた値と違う"
    assert len(zb) == ZIP_BYTES, u"zip の bytes が違う"


def check_record22(rec):
    u"""P22(既定)で採り直した記録(2026-10-20 段 2)の検査。"""
    return check_record(rec, FACT22, "P22", ENGINE_BUNDLE22)


def check_p21_copy(raw):
    assert sha_bytes(raw) == REC21_SHA256, u"P21 の記録の写しが履歴のバイト列と違う"


def check_record(rec, fact=None, profile="P21", bundle=None):
    u"""記録の内部整合。行から数え直した値と記録の集計、字で留めた先に測った数(P21 は封 §0-1、P22 は段 2 で採り直した記録)。"""
    FACT = fact or globals()["FACT"]
    bundle = bundle or ENGINE_BUNDLE
    rows = rec[u"注入の一覧"]
    assert len(rows) == FACT["targets"], u"注入の行の数"
    passed = [r for r in rows if r[u"結果"] == "PASSED"]
    det = [r for r in rows if r[u"結果"] == "detected:VALUE_MISMATCH"]
    assert len(passed) + len(det) == len(rows), u"通した でも 止めた でもない結果が在る"
    assert rec[u"止めた でも 通した でもない結果"] == {}, u"通した でも 止めた でもない結果の欄"
    for key, m in ((K_PASSED, passed), (K_DETECTED, det)):
        c = rec[key]
        assert c[u"件"] == len(m) and c[u"分母"] == len(rows), key
        assert c[u"字"] == F(len(m), len(rows)) and c[u"率"] == round(100.0 * len(m) / len(rows), 1), key
    assert (len(passed), len(det), len(rows)) == (FACT["passed"], FACT["detected"], FACT["targets"]), u"先に測った数との差"
    # 通した の一覧は 通した の行そのもの(順序つき)
    assert rec[u"通した の一覧"] == passed, u"通した の一覧が行と違う"
    # 分け方(字から独立に求める)
    cls = {C_DEG: [], C_IN: [], C_OUT: []}
    for r in passed:
        c = indep_class(r)
        assert r[u"分類"] == c, (r[u"id"], r[u"分類"], c)
        cls[c].append(r)
    for c, m in cls.items():
        d = rec[K_CLASS][c]
        assert d[u"件"] == len(m), c
        assert d[u"うち率(単位が %)"] == sum(1 for r in m if r[u"単位"] == u"%"), c
        assert d[u"うち金額ほか(単位が % でない)"] == sum(1 for r in m if r[u"単位"] != u"%"), c
    assert (len(cls[C_IN]), len(cls[C_DEG])) == (FACT["in_band"], FACT["degenerate"]), u"先に測った数との差(分け方)"
    assert rec[K_MOVED] == sum(1 for r in passed if r[u"参照先(注入前)"] != r[u"参照先(注入後)"]), u"参照先が動いた数"
    for r in passed:
        assert r[u"参照先が動いた"] == (r[u"参照先(注入前)"] != r[u"参照先(注入後)"]), r[u"id"]
    # 型別
    for key, how in ((u"V1(最小の桁の 1 字を変える)", "V1"), (u"V2(値を ±1 最小単位)", "V2")):
        m = [r for r in rows if r[u"型"] == how]
        t = rec[u"型別"][key]
        assert t == {u"対象": len(m), u"通した": sum(1 for r in m if r[u"結果"] == "PASSED"),
                     u"止めた": sum(1 for r in m if r[u"結果"] == "detected:VALUE_MISMATCH")}, key
    assert {r[u"型"] for r in rows} == {"V1", "V2"}
    # 行ごとの字: 後の字は元の字から 1 桁(V2)または桁の足し(V1)で作られている
    for r in rows:
        a, b = _digits(r[u"元の字"]), _digits(r[u"後の字"])
        if r[u"型"] == "V2":
            assert a[:-1] == b[:-1] and a[-1] != b[-1], r[u"id"]
            assert abs(int(a[-1]) - int(b[-1])) == 1, r[u"id"]
        else:
            assert a != b, r[u"id"]
        assert r[u"id"] and r[u"元の字"] in r[u"文脈"], r[u"id"]
    # 先に測った数(封 §0-1)
    assert rec[u"素の書類"][u"claim"] == FACT["claims"], u"claim の数"
    assert rec[u"素の書類"][u"state の分布"] == FACT["states"], u"素の書類の state の分布"
    assert sum(FACT["states"].values()) == FACT["claims"]
    inj = rec[u"注入"]
    assert (inj[u"数の site"], inj[u"土台の不一致"], inj[u"注入の対象(GROUNDED の site)"]) == (FACT["sites"], FACT["mismatch"], FACT["targets"])
    assert inj[u"土台(経営分析の文のまま)の state の分布"] == FACT["states"]
    ib = rec[u"入力"]
    assert (ib[u"sha256"], ib[u"bytes"], ib[u"path"], ib[u"profile"]) == (ZIP_SHA256, ZIP_BYTES, ZIP_REL, profile), u"入力の留め"
    assert rec[K_ENV][u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)"] == bundle
    assert rec[K_ENV][u"engine の file 数"] == 36
    assert rec[K_ENV][u"ラベル 2 file の sha256(起動時に照合)"] == LABEL_SHAS, u"ラベル 2 file の sha256"
    assert rec[K_ENV][u"通信"].endswith(u"通信は初回のラベル取得だけ"), u"通信の欄"
    moved = [r for r in passed if r[u"参照先が動いた"]]
    assert all(r[u"分類"] == C_IN for r in moved), u"参照先が動いた行が帯の中でない"


# ----------------------------------------------------------------------------------------------------------------
# README の節(記録から作った字)
def first_degenerate(rec):
    r = [x for x in rec[u"通した の一覧"] if x[u"分類"] == C_DEG][0]
    return u"`%s → %s`" % (r[u"元の字"], r[u"後の字"])


def first_degenerate_en(rec):
    r = [x for x in rec[u"通した の一覧"] if x[u"分類"] == C_DEG][0]
    return u"`%s` becoming `%s` before the unit word" % (_digits(r[u"元の字"]), _digits(r[u"後の字"]))


def moved_ids(rec):
    return [x[u"id"] for x in rec[u"通した の一覧"] if x[u"参照先が動いた"]]


def p21_record():
    u"""P21 のときの記録(README の P21 の 1 行と『P21 で参照先が前期へ移った行』の id の出どころ)。"""
    return json.loads(jtext(REC21))


def render_ja(rec):
    p, d = rec[K_PASSED], rec[K_DETECTED]
    c = rec[K_CLASS]
    ib = rec[u"入力"]
    mv = moved_ids(rec)
    return u"\n".join([
        u"## 10 分の再現(API 鍵なし・0 USD。初回のラベル取得を除き通信なし)",
        u"",
        u"clone した直後に、`audit-core/` の中で、誤りを入れたとき何を通し何を止めるかを自分の手で見る入口(記録 `fixtures/xbrl/ritual_2026-10-20.json`、結果 `docs/XBRL_RITUAL_RESULT_2026-10-20.md`)。",
        u"",
        u"**手順 0(初回に 1 回だけ)**: EDINET から標準タクソノミのラベル 2 file を取る(curl 2 本 + sha256 照合、約 8 MB)。"
        u"手順と sha256 は `fixtures/xbrl/TAXONOMY_LABELS_README.md`。置き場は `~/.cache/audit-core/edinet-taxonomy/2025-11-01/` で、"
        u"環境変数 `EDINET_TAXONOMY_DIR` で変えられる。ラベルには金融庁の著作権表示があるので repo には入れていない。"
        u"無いまま走らせると、案内を出して止まる(rc=2)。",
        u"",
        u"**手順 1**:",
        u"",
        u"```",
        u"python3 measure/ritual_2026-10-20.py --out <出力先>",
        u"```",
        u"",
        u"- **通した %s**: 経営分析の文の数を 1 つずつわざと変え(最小の桁の 1 字 / ±1 最小単位)、書類が GROUNDED のまま通した数。" % p[u"字"],
        u"- 止めた %s(VALUE_MISMATCH)。" % d[u"字"],
        u"- 通した %d の中身: 丸めの帯の中(±1 最小単位)%d(率 %d・金額ほか %d)・退化値(%s。字は変わるが値が変わらない)%d・帯の外 %d。これが欠陥でないかは読む人が決める。" % (
            p[u"件"], c[C_IN][u"件"], c[C_IN][u"うち率(単位が %)"], c[C_IN][u"うち金額ほか(単位が % でない)"],
            first_degenerate(rec), c[C_DEG][u"件"], c[C_OUT][u"件"]),
        u"- 既定は P22(期を縛る。2026-10-20)。前期の値を当期の数として書くと止まる: P21 で注入後の値が前期の fact に合い、参照先が当期から前期へ移ったまま GROUNDED で通した %s は、P22 では止める(VALUE_MISMATCH)。通した行のうち参照先が前期へ移った行は %d。" % (
            u"・".join(moved_ids(p21_record())), len(mv)),
        u"- P21 のとき(2026-10-20、`cb4b497` まで)は 通した %d / %d、止めた %d / %d(記録 `fixtures/xbrl/ritual_2026-10-20_p21.json`)。" % (
            p21_record()[K_PASSED][u"件"], p21_record()[K_PASSED][u"分母"], p21_record()[K_DETECTED][u"件"], p21_record()[K_DETECTED][u"分母"]),
        u"- 所要 %s 秒(記録を採った機械の値)。" % rec[K_SEC][u"全体"],
        u"- 入力 `%s`(sha256 `%s`、%s bytes)は EDINET の公開の開示書類(書類 ID %s、提出者コード E36539 ＤＮホールディングス株式会社、提出日 2026-09-30)。"
        u"**経営分析の節は 2026-10-09 の AI 文の実験で AI の文に差し替えてあり、原文ではない。**" % (
            ib[u"path"], ib[u"sha256"], u"{:,}".format(ib[u"bytes"]), ib[u"書類ID"]),
        u"- 鍵は使わない。読むのは同梱の書類と `~/.cache` のラベル 2 file だけ。自分の書類で回すには、EDINET の鍵と書類の取得が要る。",
        u""])


def render_en(rec):
    p, d = rec[K_PASSED], rec[K_DETECTED]
    c = rec[K_CLASS]
    ib = rec[u"入力"]
    mv = moved_ids(rec)
    return u"\n".join([
        u"## 10-minute reproduction (no API key, 0 USD; no network except the one-time label download)",
        u"",
        u"Right after cloning, one command run inside `audit-core/` lets you see by hand what the engine passes and what it stops when errors are injected (record `fixtures/xbrl/ritual_2026-10-20.json`, result `docs/XBRL_RITUAL_RESULT_2026-10-20.md`).",
        u"",
        u"**Step 0 (once)**: download the two standard-taxonomy label files from EDINET (two curl commands plus a sha256 check, about 8 MB). "
        u"The steps and sha256 values are in `fixtures/xbrl/TAXONOMY_LABELS_README.md`. They live in `~/.cache/audit-core/edinet-taxonomy/2025-11-01/` "
        u"(override with the `EDINET_TAXONOMY_DIR` environment variable) and are not in this repository because they carry the Financial Services Agency's copyright notice. "
        u"Without them the entry point prints instructions and stops (exit code 2).",
        u"",
        u"**Step 1**:",
        u"",
        u"```",
        u"python3 measure/ritual_2026-10-20.py --out <output dir>",
        u"```",
        u"",
        u"- **Passed %s**: each number in the management-discussion text is deliberately changed, one per sentence (the last digit changed / +-1 in the last printed unit), and the count is how many the engine still reports as GROUNDED." % p[u"字"],
        u"- Stopped %s (VALUE_MISMATCH)." % d[u"字"],
        u"- What the %d passed are: inside the rounding band (+-1 last unit) %d (rates %d, amounts and others %d); degenerate (%s: the text changes but the value does not) %d; outside the band %d. Whether these are defects is for the reader to decide." % (
            p[u"件"], c[C_IN][u"件"], c[C_IN][u"うち率(単位が %)"], c[C_IN][u"うち金額ほか(単位が % でない)"],
            first_degenerate_en(rec), c[C_DEG][u"件"], c[C_OUT][u"件"]),
        u"- The default is P22 (the period is pinned; 2026-10-20). Writing a prior-period value as a current-period number now stops: %s, whose injected value matched the prior-period fact under P21 so the reference moved from the current period to the prior period and was still reported as GROUNDED, are stopped (VALUE_MISMATCH) under P22. Passed rows whose reference moved to the prior period: %d." % (
            u", ".join(moved_ids(p21_record())), len(mv)),
        u"- Under P21 (2026-10-20, up to `cb4b497`) it was passed %d / %d, stopped %d / %d (record `fixtures/xbrl/ritual_2026-10-20_p21.json`)." % (
            p21_record()[K_PASSED][u"件"], p21_record()[K_PASSED][u"分母"], p21_record()[K_DETECTED][u"件"], p21_record()[K_DETECTED][u"分母"]),
        u"- Run time %s seconds (the machine that took the record)." % rec[K_SEC][u"全体"],
        u"- The input `%s` (sha256 `%s`, %s bytes) is a public EDINET disclosure document (document ID %s, filer code E36539, DN Holdings Co., Ltd., filed 2026-09-30). "
        u"**Its management-discussion section was replaced with AI-written text in the 2026-10-09 experiment, so it is not the original text.**" % (
            ib[u"path"], ib[u"sha256"], u"{:,}".format(ib[u"bytes"]), ib[u"書類ID"]),
        u"- No key is used. It reads the bundled filing and the two label files under `~/.cache`, nothing else. To run it on your own filings you need an EDINET key and the filings downloaded.",
        u""])


ADDENDUM_HEAD = u"## 6. 追記(2026-10-20、期を縛る P22 の段 2 ― 既定が P22 になった)"
STEP1_DOC_COMMIT = "3320c8c"


def addendum_facts(rec21, rec22):
    u"""追記(§6)の数のある文。二本の記録から作る(散文に手で数を書かない)。"""
    p21, p22 = rec21[K_PASSED], rec22[K_PASSED]
    d21, d22 = rec21[K_DETECTED], rec22[K_DETECTED]
    c = rec22[K_CLASS]
    ids21 = set((x[u"id"], x[u"型"]) for x in rec21[u"注入の一覧"])
    ids22 = set((x[u"id"], x[u"型"]) for x in rec22[u"注入の一覧"])
    dropped = sorted(ids21 - ids22)
    appeared = sorted(ids22 - ids21)
    mv21, mv22 = moved_ids(rec21), moved_ids(rec22)
    st21, st22 = rec21[u"素の書類"][u"state の分布"], rec22[u"素の書類"][u"state の分布"]
    return {
        "a_head": u"- **通した %s・止めた %s**(P22 = 既定。P21 のときは 通した %s・止めた %s)。" % (p22[u"字"], d22[u"字"], p21[u"字"], d21[u"字"]),
        "a_split": u"- 通した %d の中身: 丸めの帯の中 %d(率 %d・金額ほか %d)・退化値 %d・帯の外 %d(P21 のときは 帯の中 %d(率 %d・金額ほか %d))。" % (
            p22[u"件"], c[C_IN][u"件"], c[C_IN][u"うち率(単位が %)"], c[C_IN][u"うち金額ほか(単位が % でない)"], c[C_DEG][u"件"], c[C_OUT][u"件"],
            rec21[K_CLASS][C_IN][u"件"], rec21[K_CLASS][C_IN][u"うち率(単位が %)"], rec21[K_CLASS][C_IN][u"うち金額ほか(単位が % でない)"]),
        "a_moved": u"- 参照先が前期へ移って通した行は %d(P21 では %s の %d 行)。前期の値を当期の数として書いた注入は P22 で止まる(VALUE_MISMATCH)。" % (
            rec22[K_MOVED], u"・".join(mv21), len(mv21)),
        "a_targets": u"- 注入の対象は %d → %d(素の書類で GROUNDED だった 1 行が VALUE_MISMATCH になり、その site が対象から外れた。外れた行: %s、増えた行: %s)。" % (
            rec21[u"注入"][u"注入の対象(GROUNDED の site)"], rec22[u"注入"][u"注入の対象(GROUNDED の site)"],
            u"・".join(u"%s %s" % k for k in dropped) or u"なし", u"・".join(u"%s %s" % k for k in appeared) or u"なし"),
        "a_plain": u"- 素の書類(claim %d)の state: GROUNDED %d → %d・VALUE_MISMATCH %d → %d(POINTER_NOT_FOUND %d → %d・UNVERIFIABLE %d → %d は不動)。" % (
            rec22[u"素の書類"][u"claim"], st21["GROUNDED"], st22["GROUNDED"], st21["VALUE_MISMATCH"], st22["VALUE_MISMATCH"],
            st21["POINTER_NOT_FOUND"], st22["POINTER_NOT_FOUND"], st21["UNVERIFIABLE"], st22["UNVERIFIABLE"]),
        "a_secs": u"- 所要 %s 秒(P22 の記録を採った機械。P21 のときは %s 秒)。" % (rec22[K_SEC][u"全体"], rec21[K_SEC][u"全体"]),
        "a_sha": u"- 二本の記録: P21 のとき `fixtures/xbrl/ritual_2026-10-20_p21.json`(sha256 `%s`)、P22(既定)`fixtures/xbrl/ritual_2026-10-20.json`。" % REC21_SHA256,
    }


def check_addendum(rec21, rec22, doc):
    assert doc.count(ADDENDUM_HEAD) == 1 and doc.index(ADDENDUM_HEAD) > doc.index(u"## 5. 再現"), u"追記が末尾に 1 つ在る"
    add = doc[doc.index(ADDENDUM_HEAD):]
    for k, v in addendum_facts(rec21, rec22).items():
        assert v in add, u"追記に数のある文『%s』(二本の記録から作った字)が無い" % k
    for lit in (u"本文(§0〜§5)の数は P21 のときの記録", u"1 字も直さない", u"買い手が clone して走らせるのは今の既定", u"README",
                u"予測 R-1〜R-8 は封の字のまま、判定は P21 のときの記録に対するもの", u"verify_document.py", u"`AUDIT_CORE_RITUAL=1`"):
        assert lit in add, lit
    stripped = add
    for v in addendum_facts(rec21, rec22).values():
        stripped = stripped.replace(v, u"")
    stripped = re.sub(r"`[^`]*`", u"", stripped)
    stripped = re.sub(r"[A-Za-z_][A-Za-z_0-9\-]*\d[A-Za-z_0-9\-]*", u"", stripped)       # P21・P22・R-1・N125・sha 等
    stripped = re.sub(r"(?m)^## [\d\.]+", u"", stripped)
    stripped = re.sub(r"§[\d\-〜]+", u"", stripped)
    stripped = re.sub(r"\d{4}-\d{2}-\d{2}", u"", stripped)
    stripped = re.sub(r"段 \d", u"", stripped)                          # 工程の名前(段 1・段 2)
    stripped = re.sub(r"1 字|1 対 1|1 行|1 点", u"", stripped)           # 言い回しの『1』(数の主張ではない。2 以上の数は残る)
    stripped = stripped.replace(u"0 USD", u"")
    res = re.findall(r"\d[\d,\.]*", stripped)
    assert res == [], u"追記の散文に、二本の記録に縛られない数が在る: %s" % res


def section(text, head):
    u"""``head`` で始まる見出しの節(次の ``## `` の前まで)。"""
    i = text.index(head)
    j = text.find(u"\n## ", i + 1)
    return text[i:j + 1] if j >= 0 else text[i:]


def check_readme(rec, ja, en):
    assert section(ja, u"## 10 分の再現").rstrip() == render_ja(rec).rstrip(), u"README.md の節が記録と違う"
    assert section(en, u"## 10-minute reproduction").rstrip() == render_en(rec).rstrip(), u"README.en.md の節が記録と違う"
    for t, s in ((ja, u"**通した %s**" % rec[K_PASSED][u"字"]), (en, u"**Passed %s**" % rec[K_PASSED][u"字"])):
        sec = section(t, u"## 10 分の再現" if t is ja else u"## 10-minute reproduction")
        bullets = [l for l in sec.splitlines() if l.startswith(u"- ")]
        assert s in bullets[0], u"通した が先頭の項目でない"


def mutate_char(s, needle, new):
    assert s.count(needle) >= 1, needle
    return s.replace(needle, new, 1)


# ----------------------------------------------------------------------------------------------------------------
WRAP = u"""
import runpy, socket, sys
import http.client, ssl, urllib.request   # 先に import(ssl が socket.socket を継ぐため)。adapters が urllib を import してもよい
def _no(*a, **k):
    raise AssertionError("儀式が通信しようとした")
socket.socket.connect = _no
socket.socket.connect_ex = _no
socket.create_connection = _no
socket.getaddrinfo = _no
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def real_labels_dir():
    u"""この機械の実在のラベル dir(門を走らせる側の HOME で決める)。"""
    return os.environ.get("EDINET_TAXONOMY_DIR") or os.path.join(
        os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy", "2025-11-01")


def labels_present(d):
    return all(os.path.exists(os.path.join(d, fn)) for fn in LABEL_SHAS)


LABELS_MISSING_FAIL = (u"AUDIT_CORE_RITUAL=1 を指定したがラベル 2 file が無い。手順 0 を先に"
                       u"(fixtures/xbrl/TAXONOMY_LABELS_README.md。EDINET_TAXONOMY_DIR で置き場を指せる)")


def run_ritual(labels_dir, extra_env=None):
    u"""儀式を **subprocess** で走らせる。``HOME`` は空の dir、ラベルは ``EDINET_TAXONOMY_DIR`` で名指し、cwd は repo の外、接続は潰す。"""
    out = tempfile.mkdtemp(prefix="ritual_rerun_")
    home = tempfile.mkdtemp(prefix="ritual_home_")
    cwd = tempfile.mkdtemp(prefix="ritual_cwd_")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home, "EDINET_TAXONOMY_DIR": labels_dir,
           "PYTHONIOENCODING": "utf-8", "LANG": "C.UTF-8"}
    env.update(extra_env or {})
    t0 = time.time()
    r = subprocess.run([sys.executable, "-B", "-c", WRAP, SCRIPT, "--out", out], cwd=cwd, env=env,
                       capture_output=True, text=True, encoding="utf-8")
    res = {"rc": r.returncode, "stdout": r.stdout, "stderr": r.stderr, "secs": time.time() - t0, "json": None, "md": None}
    jp = os.path.join(out, "ritual.json")
    if os.path.exists(jp):
        res["json"] = json.loads(jtext(jp))
        res["md"] = jtext(os.path.join(out, "ritual.md"))
    return res


CURL_RE = re.compile(r"curl -sS -O (http://\S+)")


def script_curl_urls(src):
    u"""script の案内の文字列(ast の定数)にある curl の URL を、出てくる順に。"""
    out = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out += CURL_RE.findall(n.value)
    return out


def check_curl_urls(src, labels_readme):
    u"""案内の URL 2 本が TAXONOMY_LABELS_README の『取り方』の URL と完全一致(順も)。"""
    want = CURL_RE.findall(labels_readme)
    assert len(want) == 2, want
    got = script_curl_urls(src)
    assert got == want, (got, want)


def check_rerun(res, rec):
    u"""走らせ直しの結果が記録と一致(所要秒と実行環境を除く)。壊れた結果に同じ関数を当てて赤を見る。"""
    assert res["rc"] == 0, (res["rc"], res["stderr"][-300:])
    assert res["json"] is not None, u"ritual.json が出ていない"
    assert strip_volatile(res["json"]) == strip_volatile(rec), u"走らせ直しが記録と違う"
    assert res["json"][K_ENV][u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)"] == ENGINE_BUNDLE22, \
        u"いまの engine が記録を採ったときの engine と違う(動いたなら記録を採り直す人間の判断)"
    # 2026-10-20(段 2): 記録は P22(既定)で採り直した。通した 15 / 240 = 6.2%・止めた 225 / 240 = 93.8%(P21 のときは 17 / 241)
    assert u"**通した %s**" % rec[K_PASSED][u"字"] in res["md"]
    scr = res["stdout"].strip().splitlines()
    assert len(scr) <= 10, u"画面が 10 行を超えた"
    assert scr[1].startswith(u"通した %s" % rec[K_PASSED][u"字"]) and scr[2].startswith(u"止めた %s" % rec[K_DETECTED][u"字"]), u"画面の先頭"


def strip_volatile(rec):
    r = copy.deepcopy(rec)
    r.pop(K_SEC)
    r.pop(K_ENV)
    return r


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads(jtext(REC))
        cls.rec21 = json.loads(jtext(REC21))
        cls.doc = jtext(DOC)
        cls.seal = jtext(SEAL)
        cls.ja = jtext(README_JA)
        cls.en = jtext(README_EN)


class InputTest(Base):
    def test_1_zip_is_tracked_and_pinned_literally(self):
        with io.open(ZIP, "rb") as fh:
            check_input_bytes(fh.read())
        self.assertEqual(subprocess.run(["git", "ls-files", "--error-unmatch", ZIP_REL], cwd=ROOT, capture_output=True).returncode, 0)
        m = re.search(r"sha256 `([0-9a-f]{64})`、([\d,]+) bytes", self.seal)
        self.assertEqual(m.group(1), ZIP_SHA256)
        self.assertEqual(int(m.group(2).replace(",", "")), ZIP_BYTES)

    def test_2_record_is_consistent_with_its_rows_and_the_seal_facts(self):
        check_record(self.rec21)                                                       # P21 のときの記録(封 §0-1・文書の本文)
        check_record(self.rec, FACT22, "P22", ENGINE_BUNDLE22)                         # P22(既定)で採り直した記録(2026-10-20 段 2)
        # 字で留めた先に測った数は封 §0-1 の字と同じ
        b = self.seal[self.seal.index("## §0-1"):self.seal.index("## §1")]
        self.assertIn(u"claim %d、GROUNDED %d・POINTER_NOT_FOUND %d・UNVERIFIABLE %d・VALUE_MISMATCH %d" % (
            FACT["claims"], FACT["states"]["GROUNDED"], FACT["states"]["POINTER_NOT_FOUND"], FACT["states"]["UNVERIFIABLE"],
            FACT["states"]["VALUE_MISMATCH"]), b)
        self.assertIn(u"site %d、土台の不一致 %d、注入の対象(GROUNDED の site)%d、**止めた %d・通した %d**" % (
            FACT["sites"], FACT["mismatch"], FACT["targets"], FACT["detected"], FACT["passed"]), b)

    def test_3b_the_p21_record_is_the_one_in_history(self):
        u"""P21 のときの記録の写しは、git の履歴(3320c8c)の ritual_2026-10-20.json と同じバイト列(sha256 を字で留める)。"""
        check_p21_copy(io.open(REC21, "rb").read())
        r = subprocess.run(["git", "show", "3320c8c:./fixtures/xbrl/ritual_2026-10-20.json"], cwd=ROOT, capture_output=True)
        if r.returncode == 0:
            self.assertEqual(sha_bytes(r.stdout), REC21_SHA256)
        self.assertNotEqual(sha_bytes(io.open(REC, "rb").read()), REC21_SHA256, u"P22 の記録が P21 の写しと同じ(採り直していない)")
        self.assertEqual(self.rec21[u"入力"][u"profile"], "P21")
        self.assertEqual(self.rec[u"入力"][u"profile"], "P22")

    def test_3_passed_come_first_in_the_record_and_the_screen(self):
        for rec in (self.rec21, self.rec):
            keys = list(rec.keys())
            self.assertEqual(keys[1], K_PASSED)
            self.assertEqual(keys[2], K_DETECTED)
        # 画面の先頭(通した が先)は重い走らせ直しの門(RerunTest.test_4)が見る。ここは script の字で先頭の順を見る。
        src = jtext(SCRIPT)
        self.assertLess(src.index(u'print(u"通した %s" % p[u"字"])'), src.index(u'print(u"止めた %s" % d[u"字"])'))


class RerunTest(Base):
    def test_5_script_never_names_the_network_or_the_cache(self):
        tree = ast.parse(jtext(SCRIPT))
        imported = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imported |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                imported.add((n.module or "").split(".")[0])
        self.assertFalse(imported & {"urllib", "socket", "http", "requests", "ssl", "anthropic", "openai", "httpx", "ftplib", "smtplib"}, imported)
        doc_node = tree.body[0]
        consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n is not doc_node.value]
        self.assertFalse([c for c in consts if ".cache" in c or "expanduser" in c], u"script が ~/.cache を名指している")
        self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "expanduser"])
        # 引数は --out だけ
        adds = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument"]
        self.assertEqual([a.args[0].value for a in adds], ["--out"])


@unittest.skipUnless(RUN_HEAVY, HEAVY_SKIP_REASON)
class RerunHeavyTest(Base):
    u"""``AUDIT_CORE_RITUAL=1`` のときだけ走る。ラベルが無い機械では skip でなく **fail**(指定したのに見ないで緑にしない)。"""
    _res = None

    def setUp(self):
        if not labels_present(real_labels_dir()):
            self.fail(LABELS_MISSING_FAIL)

    @classmethod
    def res(cls):
        if RerunHeavyTest._res is None:
            RerunHeavyTest._res = run_ritual(real_labels_dir())
        return RerunHeavyTest._res

    def test_4_rerun_from_the_bundled_zip_equals_the_record(self):
        # HOME は空の dir・接続は潰す・cwd は repo の外。ラベルだけ EDINET_TAXONOMY_DIR で名指す
        check_rerun(self.res(), self.rec)
        self.assertEqual(self.res()["json"][K_ENV][u"鍵の名前の有無(値は読まない)"].keys(), self.rec[K_ENV][u"鍵の名前の有無(値は読まない)"].keys())

    def test_6_rerun_time_is_inside_the_sealed_bound(self):
        # 封 R-7: 走らせ直して一致は 30 秒以内
        self.assertEqual(self.res()["rc"], 0)
        self.assertLessEqual(self.res()["secs"], 30.0)

    def test_6b_without_the_labels_the_rerun_gate_is_red(self):
        # ラベルを空の dir に向けた走らせ直しに、本物と同じ check_rerun を当てて赤を見る(ラベルが本当に要る)
        empty = tempfile.mkdtemp(prefix="ritual_nolabel_")
        with self.assertRaises(AssertionError):
            check_rerun(run_ritual(empty), self.rec)


class LabelTest(Base):
    u"""ラベル 2 file が無い・違う機械で、儀式は案内を出して rc=2 で止まる(既定で走る軽い門。通信しない)。"""

    def test_13_without_the_labels_the_ritual_stops_with_instructions(self):
        empty = tempfile.mkdtemp(prefix="ritual_nolabel_")
        res = run_ritual(empty)
        self.assertEqual(res["rc"], 2)
        self.assertNotIn("Traceback", res["stderr"])
        self.assertNotIn("FileNotFoundError", res["stderr"])
        lines = res["stderr"].strip().splitlines()
        self.assertLessEqual(len(lines), 10)
        self.assertEqual(sum(1 for l in lines if "curl -sS -O" in l), 2)
        for w in (u"TAXONOMY_LABELS_README.md", u"EDINET_TAXONOMY_DIR", u"taxonomy_labels_sha256.txt", empty):
            self.assertIn(w, res["stderr"], w)
        self.assertEqual(res["stdout"], "")
        self.assertIsNone(res["json"], u"ラベル無しなのに記録が出た")
        # 走らせ直しの検査関数はこの結果に赤くなる(ラベル無しで本当に赤い)
        with self.assertRaises(AssertionError):
            check_rerun(res, self.rec)

    def test_14_labels_with_a_wrong_sha256_also_stop_with_instructions(self):
        bad = tempfile.mkdtemp(prefix="ritual_badlabel_")
        for fn in LABEL_SHAS:
            with io.open(os.path.join(bad, fn), "wb") as fh:
                fh.write(b"not the real label file")
        res = run_ritual(bad)
        self.assertEqual(res["rc"], 2)
        self.assertIn(u"sha256 が違う", res["stderr"])
        self.assertNotIn("Traceback", res["stderr"])
        self.assertLessEqual(len(res["stderr"].strip().splitlines()), 10)

    def test_16_guidance_urls_equal_the_labels_readme(self):
        readme = jtext(os.path.join(ROOT, "fixtures", "xbrl", "TAXONOMY_LABELS_README.md"))
        check_curl_urls(jtext(SCRIPT), readme)
        # 取得先は label ファイル名と版が engine の字と合う
        for u, fn in zip(script_curl_urls(jtext(SCRIPT)), LABEL_SHAS):
            self.assertTrue(u.endswith("/" + fn), u)

    def test_17_only_one_of_the_two_label_files_also_stops_with_instructions(self):
        d = real_labels_dir()
        if not labels_present(d):
            self.skipTest(u"実在のラベルが無い機械(片方だけの dir は実在の jppfs を写して作る)。" + LABELS_MISSING_FAIL)
        for keep, lack in (("jppfs_2025-11-01_lab.xml", "jpcrp_2025-11-01_lab.xml"), ("jpcrp_2025-11-01_lab.xml", "jppfs_2025-11-01_lab.xml")):
            half = tempfile.mkdtemp(prefix="ritual_half_")
            shutil.copyfile(os.path.join(d, keep), os.path.join(half, keep))
            res = run_ritual(half)
            self.assertEqual(res["rc"], 2, (keep, res["stderr"][-300:]))
            self.assertIn(lack, res["stderr"])
            self.assertNotIn("Traceback", res["stderr"])
            self.assertLessEqual(len(res["stderr"].strip().splitlines()), 10)

    def test_15_pinned_label_shas_equal_the_repo_list(self):
        listed = {}
        for l in jtext(os.path.join(ROOT, "fixtures", "xbrl", "taxonomy_labels_sha256.txt")).splitlines():
            if l.strip() and not l.startswith("#"):
                h, fn = l.split(None, 1)
                listed[fn.strip()] = h
        self.assertEqual(listed, LABEL_SHAS)


class ReadmeTest(Base):
    def test_7_readme_sections_equal_what_the_record_says(self):
        check_readme(self.rec, self.ja, self.en)
        self.assertEqual(self.ja.count(u"## 10 分の再現"), 1)
        self.assertEqual(self.en.count(u"## 10-minute reproduction"), 1)
        self.assertIn(u"S100Z4Q1", section(self.ja, u"## 10 分の再現"))
        self.assertIn(u"差し替えてあり、原文ではない", section(self.ja, u"## 10 分の再現"))
        self.assertIn(u"not the original text", section(self.en, u"## 10-minute reproduction"))
        for t in (section(self.ja, u"## 10 分の再現"), section(self.en, u"## 10-minute reproduction")):
            for a, b, p in FRAC_RE.findall(t):
                self.assertEqual("%.1f" % (100.0 * int(a) / int(b)), p)
            self.assertEqual(len(FRAC_RE.findall(t)), 2)


class PredictionTest(Base):
    def seal_row(self, h):
        for l in self.seal.splitlines():
            if l.startswith(u"| **%s** |" % h):
                return [c.strip() for c in l.strip().strip(u"|").split(u"|")]
        raise AssertionError(h)

    def git(self, *a):
        return subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)

    def judge(self):
        rec = self.rec21        # 予測 R-1〜R-8 は封の字 = P21 の記録に対する判定(文書の本文・表)。P22 の数は追記が縛る
        c = rec[K_CLASS]
        out = {}
        bound = int(re.search(r"\*\*(\d+) 秒以内\*\*", self.seal_row("R-1")[1]).group(1))
        out["R-1"] = rec[K_SEC][u"全体"] <= bound
        out["R-2"] = ((rec[u"注入"][u"注入の対象(GROUNDED の site)"], rec[K_DETECTED][u"件"], rec[K_PASSED][u"件"]) ==
                      tuple(int(x) for x in re.findall(r"\*\*(\d+)\*\*", self.seal_row("R-2")[1])))
        out["R-3"] = sum(1 for r in rec[u"注入の一覧"] if r.get(u"後の値") is not None and r[u"結果"] == "PASSED"
                         and abs(r[u"後の値"] - r[u"元の値"]) <= 1e-9 * max(1.0, abs(r[u"元の値"]))) == 1
        out["R-4"] = c[C_IN][u"件"] == 16 and c[C_OUT][u"件"] == 0
        out["R-5"] = (rec[u"素の書類"][u"state の分布"] == FACT["states"] and rec[u"素の書類"][u"claim"] == FACT["claims"]
                      and rec[u"入力"][u"profile"] == "P21")
        try:
            check_readme(self.rec, self.ja, self.en)          # README は P22(既定)の記録と 1 対 1
            out["R-6"] = True
        except AssertionError:
            out["R-6"] = False
        # R-7: 全体の上限は封の字(150)。他の席の機械の実測は字で留めた値(再現できない)。1 つでも超えたら外れ。
        total_bound = int(re.findall(r"\*\*(\d+) 秒以内\*\*", self.seal_row("R-7")[1])[-1])
        out["R-7"] = all(hi <= total_bound for (_lo, hi) in R7_TOTAL_SECONDS.values())
        base = self.git("log", "--diff-filter=A", "--format=%H", "--", SEAL_REL).stdout.split()[-1]
        d1 = self.git("diff", base, "--numstat", "--", "core", "adapters", FALSE_PASS_REL).stdout
        d2 = self.git("status", "--porcelain", "--", "core", "adapters", FALSE_PASS_REL).stdout
        out["R-8"] = (d1 == "" and d2 == "") or only_declared_changes(d1, d2)
        return out

    def test_8_judgments_recomputed_equal_the_document_table(self):
        j = self.judge()
        self.assertEqual(sorted(j), ["R-%d" % i for i in range(1, 9)])
        for h, ok in j.items():
            row = [l for l in self.doc.splitlines() if l.startswith(u"| **%s** |" % h)]
            self.assertEqual(len(row), 1, h)
            cells = [x.strip() for x in row[0].strip().strip(u"|").split(u"|")]
            self.assertEqual(len(cells), 4, h)
            self.assertEqual(cells[1], self.seal_row(h)[1], u"%s の予測欄が封の字と違う" % h)
            want = u"**当たり**" if ok else u"**外れ**"
            if h == "R-1":
                # 条件つき当たり: ラベル 2 file が在る機械で 60 秒以内。clone 直後(ラベル無し)の機械では走らない
                self.assertTrue(cells[3].startswith(want) and u"条件つき" in cells[3] and u"ラベル" in cells[3], cells[3])
            elif h == "R-7":
                self.assertTrue(cells[3].startswith(want) and u"機械依存" in cells[3], cells[3])
            else:
                self.assertEqual(cells[3], want, h)

    def test_9_prediction_table_numbers_come_from_the_record(self):
        rec = self.rec21
        r1 = [l for l in self.doc.splitlines() if l.startswith(u"| **R-1** |")][0]
        self.assertIn(u"%s 秒" % rec[K_SEC][u"全体"], r1)
        r2 = [l for l in self.doc.splitlines() if l.startswith(u"| **R-2** |")][0]
        for s in (u"241", u"224", u"17"):
            self.assertIn(s, r2)
        r6 = [l for l in self.doc.splitlines() if l.startswith(u"| **R-6** |")][0]
        self.assertIn(rec[K_PASSED][u"字"], r6)
        self.assertIn(rec[K_DETECTED][u"字"], r6)


class DocTest(Base):
    def test_10_passed_table_equals_lines_built_from_the_record(self):
        lines = self.doc.splitlines()
        for x in self.rec21[u"通した の一覧"]:
            moved = u"(動いた)" if x[u"参照先が動いた"] else u""
            want = u"| %s | %s | `%s` | `%s` | %s → %s | %s | `%s` → `%s`%s | %s |" % (
                x[u"id"], x[u"型"], x[u"元の字"], x[u"後の字"], x[u"元の値"], x[u"後の値"], x[u"単位"],
                x[u"参照先(注入前)"], x[u"参照先(注入後)"], moved, x[u"分類"])
            self.assertIn(want, lines, x[u"id"])
        n_table = sum(1 for l in lines if re.match(r"\| N\d{3} \| V[12] \|", l))
        self.assertEqual(n_table, FACT["passed"])

    def test_11_every_fraction_is_arithmetic_and_in_the_allowed_set(self):
        allowed = set()
        for rec in (self.rec21, self.rec):        # 本文は P21 の記録、追記(2026-10-20 段 2)は P22 の記録
            rows = rec[u"注入の一覧"]
            allowed |= {(rec[K_PASSED][u"件"], len(rows)), (rec[K_DETECTED][u"件"], len(rows))}
            for how in ("V1", "V2"):
                m = [r for r in rows if r[u"型"] == how]
                allowed.add((sum(1 for r in m if r[u"結果"] == "PASSED"), len(m)))
                allowed.add((sum(1 for r in m if r[u"結果"] == "detected:VALUE_MISMATCH"), len(m)))
        found = FRAC_RE.findall(self.doc)
        self.assertGreater(len(found), 4)
        for a, b, p in found:
            a_, b_ = int(a.replace(",", "")), int(b.replace(",", ""))
            self.assertEqual("%.1f" % (100.0 * a_ / b_), p, (a, b, p))
            self.assertIn((a_, b_), allowed, (a, b, p))
        self.assertIn(u"通した 17 / 241 = 7.1%", self.doc)
        self.assertIn(u"止めた 224 / 241 = 92.9%", self.doc)

    def test_18_addendum_numbers_equal_what_the_two_records_say(self):
        check_addendum(self.rec21, self.rec, self.doc)

    def test_19_the_body_is_not_rewritten_since_step_1(self):
        u"""本文(§0〜§5)は段 1 の commit(3320c8c)のまま。許すのは末尾の日付つきの追記だけ(字を足すだけで、1 字も消さない)。"""
        r = subprocess.run(["git", "show", STEP1_DOC_COMMIT + ":./docs/XBRL_RITUAL_RESULT_2026-10-20.md"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            self.skipTest(u"git の履歴に %s が無い" % STEP1_DOC_COMMIT)
        self.assertTrue(self.doc.startswith(r.stdout), u"本文が段 1 の commit から変わった")
        tail = self.doc[len(r.stdout):]
        self.assertTrue(tail.lstrip(u"\n").startswith(ADDENDUM_HEAD), tail[:60])

    def test_12_limits_reproduction_and_wording_exist(self):
        for s in (u"## 0. 結論", u"## 1. 予測 R-1〜R-8", u"## 2. 通した 17 の一覧と読み", u"## 3. 限界", u"## 4. 変異", u"## 5. 再現",
                  u"python3 measure/ritual_2026-10-20.py --out", u"python3 -m pytest -q tests/measure/test_xbrl_ritual_result.py",
                  u"**API 鍵なし・0 USD・初回のラベル取得を除き通信なし・engine(`core/`・`adapters/`)0 行。**",
                  u"## 0-1. 依存の見落とし(2026-10-20)", u"標準タクソノミのラベル 2 file", u"TAXONOMY_LABELS_README.md", u"EDINET_TAXONOMY_DIR",
                  u"AUDIT_CORE_RITUAL=1", u"R-2・R-4・R-5 の幅は封 §0-1 の先に測った数の写しで、当たって当然の再現",
                  u"**当たり**(条件つき: ラベル 2 file が在る機械", u"監査席の機械", u"**外れ**(機械依存。外れ方どおり分けた)",
                  u"同梱書類で回すにもラベル 2 file が要る(初回 1 回の通信)。自分の書類には鍵が要る",
                  u"「走らせ直し」が縛るのは出力の一致まで",
                  u"2026-10-20 の訂正",
                  u"原文ではない", u"**縛っていないもの**", ADDENDUM_HEAD):
            self.assertIn(s, self.doc, s)
        self.assertIn(u"束ねた sha256 `%s`" % ENGINE_BUNDLE, self.doc)
        self.assertIn(u"sha256 `%s`" % ZIP_SHA256, self.doc)


# ----------------------------------------------------------------------------------------------------------------
class MutationTest(Base):
    u"""門が壊れた標本で赤くなること(毎回走らせる)。壊した後の標本に、本物と同じ検査関数を当てる。"""

    def red(self, fn, *a):
        with self.assertRaises(AssertionError):
            fn(*a)

    def test_m0_the_genuine_samples_pass(self):
        check_record(self.rec21)
        check_record22(self.rec)
        check_p21_copy(io.open(REC21, "rb").read())
        check_readme(self.rec, self.ja, self.en)
        with io.open(ZIP, "rb") as fh:
            check_input_bytes(fh.read())

    def test_m1_one_character_of_the_record_is_red(self):
        for needle, new in ((u"\"後の字\": \"67.6%\"", u"\"後の字\": \"67.7%\""),            # 後の字 1 字
                            (u"\"元の字\": \"61.7%\"", u"\"元の字\": \"61.6%\""),             # 元の字 1 字(文脈と食い違う)
                            (u"\"sha256\": \"" + ZIP_SHA256[:8], u"\"sha256\": \"" + "f" + ZIP_SHA256[1:8])):
            bad = json.loads(mutate_char(jtext(REC), needle, new))
            self.red(check_record22, bad)

    def test_m1b_one_character_of_the_record_is_red_against_the_readme(self):
        bad = json.loads(mutate_char(jtext(REC), u"\"字\": \"225 / 240 = 93.8%\"", u"\"字\": \"225 / 240 = 93.7%\""))
        self.red(check_readme, bad, self.ja, self.en)

    def test_m2_one_character_of_each_readme_is_red(self):
        self.red(check_readme, self.rec, mutate_char(self.ja, u"225 / 240", u"226 / 240"), self.en)
        self.red(check_readme, self.rec, self.ja, mutate_char(self.en, u"225 / 240", u"226 / 240"))
        self.red(check_readme, self.rec, mutate_char(self.ja, u"93.8%", u"93.7%"), self.en)
        self.red(check_readme, self.rec, self.ja, mutate_char(self.en, u"6.2%", u"6.3%"))
        # P21 の 1 行(README にだけ在る P21 のときの数)も 1 字で赤
        self.red(check_readme, self.rec, mutate_char(self.ja, u"通した 17 / 241", u"通した 18 / 241"), self.en)
        self.red(check_readme, self.rec, self.ja, mutate_char(self.en, u"passed 17 / 241", u"passed 18 / 241"))

    def test_m3_passed_15_to_14_is_red(self):
        bad = copy.deepcopy(self.rec)
        bad[K_PASSED][u"件"] = 14
        self.red(check_record22, bad)
        bad = copy.deepcopy(self.rec)
        bad[K_PASSED][u"字"] = u"14 / 240 = 5.8%"
        self.red(check_record22, bad)
        # 行を 1 本 止めた に書き換えても赤(集計との食い違い)
        bad = copy.deepcopy(self.rec)
        bad[u"注入の一覧"][[i for i, r in enumerate(bad[u"注入の一覧"]) if r[u"結果"] == "PASSED"][0]][u"結果"] = "detected:VALUE_MISMATCH"
        self.red(check_record22, bad)

    def test_m7_removing_step_0_or_the_N125_note_from_the_readme_is_red(self):
        def cut(text, start_marker):
            i = text.index(start_marker)
            j = text.index(u"\n", i)
            return text[:i] + text[j + 1:]

        self.red(check_readme, self.rec, cut(self.ja, u"**手順 0(初回に 1 回だけ)**"), self.en)
        self.red(check_readme, self.rec, self.ja, cut(self.en, u"**Step 0 (once)**"))
        self.red(check_readme, self.rec, cut(self.ja, u"- 既定は P22"), self.en)
        self.red(check_readme, self.rec, self.ja, cut(self.en, u"- The default is P22"))
        self.red(check_readme, self.rec, cut(self.ja, u"- P21 のとき"), self.en)
        self.red(check_readme, self.rec, self.ja, cut(self.en, u"- Under P21"))
        # P21 で参照先が動いた id(数ではなく id で縛る。P22 の記録では動いた行は 0)
        self.assertEqual(moved_ids(self.rec21), [u"N125", u"N199"])
        self.assertEqual(moved_ids(self.rec), [])
        self.red(check_readme, self.rec, mutate_char(self.ja, u"N125・N199", u"N125・N198"), self.en)
        # 鍵と ~/.cache の字も記録とは別に縛られている(節の全文一致)
        self.red(check_readme, self.rec, mutate_char(self.ja, u"ラベル 2 file だけ", u"ラベル 2 file と鍵だけ"), self.en)

    def test_m11_a_number_in_the_addendum_is_red(self):
        facts = addendum_facts(self.rec21, self.rec)
        check_addendum(self.rec21, self.rec, self.doc)
        for k, v in facts.items():
            self.assertIn(v, self.doc, k)
            m = re.search(r"\d+", v)
            mutated = self.doc.replace(v, v[:m.start()] + str(int(m.group(0)) + 7) + v[m.end():], 1)
            self.assertNotEqual(mutated, self.doc)
            self.red(check_addendum, self.rec21, self.rec, mutated)
        # 新しい数の手書き・追記の削除・二重の追記も赤
        self.red(check_addendum, self.rec21, self.rec, self.doc + u"\n- 影響は 12345 行。\n")
        self.red(check_addendum, self.rec21, self.rec, self.doc.replace(ADDENDUM_HEAD, u"## 6. 追記", 1))
        self.red(check_addendum, self.rec21, self.rec, self.doc + u"\n" + ADDENDUM_HEAD + u"\n")

    def test_m9_a_changed_url_in_the_guidance_is_red(self):
        readme = jtext(os.path.join(ROOT, "fixtures", "xbrl", "TAXONOMY_LABELS_README.md"))
        src = jtext(SCRIPT)
        check_curl_urls(src, readme)
        url = script_curl_urls(src)[0]
        self.red(check_curl_urls, src.replace(url, url.replace("jppfs", "jppfz", 1), 1), readme)
        self.red(check_curl_urls, src.replace(url, url[:-1], 1), readme)
        self.red(check_curl_urls, src, readme.replace("2025-11-01/label", "2025-11-02/label", 1))

    def test_m8_a_wrong_communication_or_label_pin_in_the_record_is_red(self):
        bad = copy.deepcopy(self.rec)
        bad[K_ENV][u"通信"] = u"しない"
        self.red(check_record22, bad)
        bad = copy.deepcopy(self.rec)
        bad[K_ENV][u"ラベル 2 file の sha256(起動時に照合)"][u"jppfs_2025-11-01_lab.xml"] = u"0" * 64
        self.red(check_record22, bad)

    def test_m10_the_p21_copy_and_the_p21_record_are_bound(self):
        raw = bytearray(io.open(REC21, "rb").read())
        raw[2000] ^= 1
        self.red(check_p21_copy, bytes(raw))
        self.red(check_p21_copy, io.open(REC21, "rb").read()[:-1])
        self.red(check_p21_copy, io.open(REC, "rb").read())          # P22 の記録を P21 の写しとして置いても赤
        bad = json.loads(mutate_char(jtext(REC21), u"\"後の字\": \"67.6%\"", u"\"後の字\": \"67.7%\""))
        self.red(check_record, bad)
        bad = copy.deepcopy(self.rec21)
        bad[K_PASSED][u"件"] = 16
        self.red(check_record, bad)
        # P22 の記録を P21 の FACT で検査すると赤(取り違えを通さない)
        self.red(check_record, self.rec)
        self.red(check_record22, self.rec21)

    def test_m4_a_changed_zip_is_red(self):
        with io.open(ZIP, "rb") as fh:
            zb = bytearray(fh.read())
        zb[1000] ^= 1
        self.red(check_input_bytes, bytes(zb))
        with io.open(ZIP, "rb") as fh:
            self.red(check_input_bytes, fh.read()[:-1])
        bad = copy.deepcopy(self.rec)
        bad[u"入力"][u"sha256"] = "f" + ZIP_SHA256[1:]   # 先頭は '0' なので '0' への置換は恒等(退化値)になる
        self.red(check_record22, bad)

    def test_m5_a_wrong_classification_is_red(self):
        # 帯の外を帯の中に書き換える・退化値を帯の中に書き換える変異(分け方の独立な求め直し)
        bad = copy.deepcopy(self.rec)
        row = [r for r in bad[u"通した の一覧"] if r[u"分類"] == C_DEG][0]
        row[u"分類"] = C_IN
        for r in bad[u"注入の一覧"]:
            if r[u"id"] == row[u"id"]:
                r[u"分類"] = C_IN
        self.red(check_record22, bad)
        # 値を 1 つ ±1 より大きく動かした行(帯の外)が在れば、分け方が帯の外にならなければ赤
        bad = copy.deepcopy(self.rec)
        row = [r for r in bad[u"通した の一覧"] if r[u"分類"] == C_IN][0]
        row[u"後の値"] = row[u"元の値"] * 10
        self.assertEqual(indep_class(row), C_OUT)
        for r in bad[u"注入の一覧"]:
            if r[u"id"] == row[u"id"]:
                r[u"後の値"] = row[u"後の値"]
        self.red(check_record22, bad)

    def test_m6_the_independent_class_function_catches_each_kind(self):
        fake = lambda a, b, v0, v1: {u"元の字": a, u"後の字": b, u"元の値": v0, u"後の値": v1}
        self.assertEqual(indep_class(fake(u"67.5%", u"67.6%", 67.5, 67.6)), C_IN)
        self.assertEqual(indep_class(fake(u"67.5%", u"68.5%", 67.5, 68.5)), C_OUT)
        self.assertEqual(indep_class(fake(u"0百万円", u"00百万円", 0.0, 0.0)), C_DEG)
        self.assertEqual(indep_class(fake(u"△780百万円", u"△781百万円", -780e6, -781e6)), C_IN)
        self.assertEqual(indep_class(fake(u"19百万円", u"190百万円", 19e6, 190e6)), C_OUT)


if __name__ == "__main__":
    unittest.main()
