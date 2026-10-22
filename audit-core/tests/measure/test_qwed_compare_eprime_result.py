# -*- coding: utf-8 -*-
u"""QWED 比較 E′(追記 2)の実測(docs/QWED_COMPARE_EPRIME_RESULT_2026-10-20.md)の門。

**本文の数は `fixtures/xbrl/cd8/qwed_compare_eprime_2026-10-20.json` を正本に突き合わせる。**
QWED は import しない(この門は 3.9 で走る。記録 JSON しか読まない)。
Audit Core 側の写しは段 B の記録(`qwed_compare_2026-10-19.json`)と、その出どころ(`period_unit_hold_2026-10-19.json`)から
数え直して記録と突き合わせる(写しが動いたら赤)。
**外れ 1 欄(Q-21)が外れとして残ること、E′a 18 / 18・E′b 0 / 18・T5 0 / 50・36 / 50 が行から数え直せることを固定する。**

変異 3 通りは in-memory で当てる: `check_record(rec)` / `check_doc(text, rec)` に書き換えた dict・字を渡す
(記録の E′b T5 の 1.0 の数 ±1 → 赤、Audit Core 側の写し 0 → 1 → 赤、文書の数の改ざん → 赤)。
"""
import collections
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "QWED_COMPARE_EPRIME_RESULT_2026-10-20.md")
REC = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "qwed_compare_eprime_2026-10-20.json")
REC_B = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "qwed_compare_2026-10-19.json")
REC_PU = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "period_unit_hold_2026-10-19.json")
VARIANTS = ["eprime-a", "eprime-b"]
#: 追記 2 の予測(字で留める。**外れは外れとして残す**)
MISSES = ["Q-21"]
HITS = ["Q-18", "Q-19", "Q-20", "Q-22", "Q-23", "Q-24"]
FIELDS = ("status", "deterministic_verdict", "deterministic_confidence", "semantic_similarity",
          "keyword_overlap", "entity_match", "negation_conflict", "citations", "constraint_id")
#: 追記 2 の「実物から描いた 1 行」(S100YXMA R004)。記録でこの字になっている
REAL = {u"context の行": "Fact OrdinaryIncome in CurrentYearDuration equals 12497000000.",
        "eprime-a": "Fact OrdinaryIncome in CurrentYearDuration equals 12497000000.",
        "eprime-b": "Fact OrdinaryIncome in CurrentYearDuration equals 12497."}
#: 段 B の描き方の一覧(封 §1-1 の字)。E′ の字数はこれより小さい(`.0` が落ちる)
SEAL_E_LIST = {"S100YWGX": (1122, 110764), "S100YXF5": (947, 91439), "S100YXMA": (1223, 116712),
               "S100YYRG": (777, 70358), "S100YYRV": (943, 88326), "S100YZ7E": (502, 52041),
               "S100YZCT": (1097, 105881), "S100YZEV": (397, 41062)}
SEAL_CHUNKS = {"S100YWGX": 2, "S100YXMA": 2, "S100YZCT": 2}


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load(p):
    return json.load(io.open(p, encoding="utf-8"))


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


def classify(f):
    """封 §0 の 3 分類(記録の `分類` を行から数え直すための写し)。"""
    em, v = f["entity_match"], f["deterministic_verdict"]
    if v == "REFUTED" or f["status"] == "BLOCKED" or (em is not None and em < 1.0):
        return u"違うと言う"
    if em == 1.0 and v == "SUPPORTED":
        return u"通す"
    return u"判定なし"


def _eq(a, b, msg=""):
    if a != b:
        raise AssertionError(u"%s: %r != %r" % (msg, a, b))


def _true(x, msg=""):
    if not x:
        raise AssertionError(msg)


def _n(rows, pred):
    return sum(1 for r in rows if pred(r))


def _em1(rows):
    return _n(rows, lambda r: r["entity_match"] == 1.0)


# ---------------------------------------------------------------- 記録の中身(変異はここに当てる)
def check_record(rec, rec_b=None, pu=None):
    rec_b = rec_b if rec_b is not None else load(REC_B)
    pu = pu if pu is not None else load(REC_PU)["rows"]
    _eq(rec[u"走らせた"], VARIANTS, u"走らせた")
    _eq(rec[u"追記 2 の commit"], "db8816f", u"追記 2 の commit")
    rows = rec["rows"]
    _eq(sorted(rows), sorted(VARIANTS), u"rows の鍵")
    pu_by = {(r["doc"], r["id"]): r for r in pu}
    for v in VARIANTS:
        rs = rows[v]
        _eq(len(rs), 192, u"%s の行" % v)
        for r in rs:
            for k in FIELDS:
                _true(k in r, u"%s の読む欄が無い: %s" % (v, k))
            _eq(r[u"分類"], classify(r), u"%s %s %s の分類" % (v, r["doc"], r["id"]))
            _eq(r[u"換算"], v == "eprime-a", u"%s の換算の旗" % v)
            want = pu_by[(r["doc"], r["id"])]
            _eq((r[u"注入か"], r[u"合成の後"], r[u"最終判定(後)"]),
                (want[u"注入か"], want[u"**合成の後**"], want[u"**最終判定(後)**"]), u"%s %s %s の Audit Core の欄" % (v, r["doc"], r["id"]))
            # 行の結果は entity_match 最大の chunk(同点は前)
            per = r[u"chunk ごと"]
            vals = [(x["entity_match"] if x["entity_match"] is not None else -1.0) for x in per]
            _eq(r[u"採った chunk"], vals.index(max(vals)), u"%s %s %s の chunk の採り方" % (v, r["doc"], r["id"]))
            _eq({k: r[k] for k in FIELDS}, {k: per[r[u"採った chunk"]][k] for k in FIELDS}, u"%s の行の結果が chunk の結果でない" % v)
            # claim の値の字: 整数なら '.' が無い。E′b は行の値そのまま、E′a は換算
            _true(re.fullmatch(r"-?\d+(\.\d*[1-9])?", r[u"claim の値の字"]), u"%s の値の字: %r" % (v, r[u"claim の値の字"]))
            _true(r["claim"].endswith("equals %s." % r[u"claim の値の字"]), u"%s の claim が値の字で終わらない" % v)
        _eq(_n(rs, lambda r: r[u"注入か"]), 64, u"%s の注入" % v)
        _eq(collections.Counter(r[u"注入の型"] for r in rs if r[u"注入か"]),
            {"T5_COINCIDENT": 50, "T3_ABSENT": 12, "T1_VALUE": 2}, u"%s の注入の型" % v)
        _eq(_n(rs, lambda r: r[u"合成の後"] == "GROUNDED"), 18, u"%s の GROUNDED" % v)
    # E′a と E′b は claim の値の字だけが違う(context・参照先の解決・chunk は同じ)
    for ra, rb in zip(rows["eprime-a"], rows["eprime-b"]):
        _eq((ra["doc"], ra["id"], ra[u"参照先の解決"], ra[u"席の参照先"]), (rb["doc"], rb["id"], rb[u"参照先の解決"], rb[u"席の参照先"]),
            u"E′a と E′b の行の並び")
        _eq(len(ra[u"chunk ごと"]), len(rb[u"chunk ごと"]), u"E′a と E′b の chunk の数")
        _eq(ra["claim"].replace("equals %s." % ra[u"claim の値の字"], ""), rb["claim"].replace("equals %s." % rb[u"claim の値の字"], ""),
            u"E′a と E′b の claim が値の字以外で違う")
    # 分母: 一覧と chunk
    lists = rec[u"分母"][u"E′ の一覧"]
    for v in VARIANTS:
        _eq(sorted(lists[v]), sorted(SEAL_E_LIST), u"%s の一覧の書類" % v)
        for d, x in lists[v].items():
            _eq((x[u"fact(全部が数)"], x[u"段 B の描き方(str(float))の字数"]), SEAL_E_LIST[d], u"%s %s の段 B の描き方" % (v, d))
            _true(x[u"字数"] < SEAL_E_LIST[d][1], u"%s %s の E′ の字数が段 B より小さくない" % (v, d))
            _eq(x[u"chunk の数"], SEAL_CHUNKS.get(d, 1), u"%s %s の chunk の数" % (v, d))
            _true(all(c <= 95000 for c in x[u"chunk"]), u"chunk が 95,000 字を超える")
        _eq(rec[u"分母"][u"chunk の数"][v], sum(x[u"chunk の数"] for x in lists[v].values()), u"%s の chunk の合計" % v)
        _eq(rec[u"分母"][u"chunk の数"][v], 11, u"%s の chunk は 11" % v)
    _true(rec[u"分母"][u"段 B の描き方(str(float))の一覧は封 §1-1 と 8 / 8 一致"], u"段 B の描き方の 8 / 8")
    # 実物の 1 行
    real = rec[u"実物の 1 行(追記 2)"]
    for v in VARIANTS:
        _eq(real[v][u"context の行"], REAL[u"context の行"], u"%s の context の行" % v)
        _eq(real[v]["claim"], REAL[v], u"%s の claim" % v)
        _true(real[v][u"context の行が追記 2 の字"] and real[v][u"claim が追記 2 の字"], u"%s の実物の 1 行の旗" % v)
        row = [r for r in rows[v] if r["doc"] == "S100YXMA" and r["id"] == "R004"][0]
        _eq(row["claim"], REAL[v], u"%s の行の claim" % v)
        _eq(row["entity_match"], real[v]["entity_match"], u"%s の実物の 1 行の entity_match" % v)
    _eq(real["eprime-a"]["entity_match"], 1.0, u"E′a の実物の 1 行は 1.0")
    _true(real["eprime-b"]["entity_match"] < 1.0, u"E′b の実物の 1 行は < 1.0")
    # 件数は行から数え直す
    cnt = rec[u"**件数**"]
    for v in VARIANTS:
        rs = rows[v]
        c = cnt[v]
        _eq(c[u"分類"], dict(collections.Counter(r[u"分類"] for r in rs)), u"%s 分類" % v)
        _eq(c[u"注入の分類"], dict(collections.Counter(r[u"分類"] for r in rs if r[u"注入か"])), u"%s 注入の分類" % v)
        _eq(c[u"無改変の分類"], dict(collections.Counter(r[u"分類"] for r in rs if not r[u"注入か"])), u"%s 無改変の分類" % v)
        _eq(c["status"], dict(collections.Counter(r["status"] for r in rs)), u"%s status" % v)
        _eq(c["verdict"], dict(collections.Counter(r["deterministic_verdict"] for r in rs)), u"%s verdict" % v)
        _eq(c[u"entity_match 1.0"], _em1(rs), u"%s 1.0" % v)
        _eq(c[u"注入で entity_match 1.0"], _em1([r for r in rs if r[u"注入か"]]), u"%s 注入で 1.0" % v)
        _eq(c[u"無改変で entity_match 1.0"], _em1([r for r in rs if not r[u"注入か"]]), u"%s 無改変で 1.0" % v)
        _eq(c[u"GROUNDED で entity_match 1.0"], _em1([r for r in rs if r[u"合成の後"] == "GROUNDED"]), u"%s GROUNDED で 1.0" % v)
        _eq(c[u"型ごとの entity_match 1.0"],
            {k: _em1([r for r in rs if r[u"注入の型"] == k]) for k in ("T5_COINCIDENT", "T3_ABSENT", "T1_VALUE")}, u"%s 型ごとの 1.0" % v)
        _eq(c[u"通す(注入)"], _n(rs, lambda r: r[u"注入か"] and r[u"分類"] == u"通す"), u"%s 通す(注入)" % v)
        _eq(c[u"通す(全体)"], _n(rs, lambda r: r[u"分類"] == u"通す"), u"%s 通す(全体)" % v)
        _eq(c[u"参照先の解決"], {"None": 107, u"解けた": 85}, u"%s 参照先の解決" % v)
    # 主比較の数(字で留める。動いたら赤)
    _eq(cnt["eprime-a"][u"GROUNDED で entity_match 1.0"], 18, u"E′a GROUNDED 18 / 18")
    _eq(cnt["eprime-b"][u"GROUNDED で entity_match 1.0"], 0, u"E′b GROUNDED 0 / 18")
    _eq(cnt["eprime-a"][u"型ごとの entity_match 1.0"]["T5_COINCIDENT"], 0, u"E′a T5 0 / 50")
    _eq(cnt["eprime-b"][u"型ごとの entity_match 1.0"]["T5_COINCIDENT"], 36, u"E′b T5 36 / 50")
    _eq(cnt["eprime-a"][u"通す(注入)"], 0, u"E′a 通す(注入)")
    _eq(cnt["eprime-b"][u"通す(注入)"], 14, u"E′b 通す(注入)")
    # Audit Core 側の写し: 段 B の記録と同じで、出どころから数え直しても同じ
    ac = rec[u"**Audit Core 側の写し(段 B の記録から。再実行しない)**"]
    acb = rec_b[u"**Audit Core 側の写し(再実行しない)**"]
    _eq({k: v for k, v in ac.items() if k != u"写した記録"}, acb, u"写し: 段 B の記録と違う")
    _eq(ac[u"写した記録"], "fixtures/xbrl/cd8/qwed_compare_2026-10-19.json", u"写した記録の名")
    inj = [r for r in pu if r[u"注入か"]]
    _eq(ac["XBRL"][u"**注入で GROUNDED**"], _n(inj, lambda r: r[u"**合成の後**"] == "GROUNDED"), u"写し: 注入で GROUNDED")
    _eq(ac["XBRL"][u"**注入で検査通過(誤りを通す)**"], _n(inj, lambda r: r[u"**最終判定(後)**"] == u"検査通過"), u"写し: 注入で検査通過")
    _eq(ac["XBRL"][u"**注入で GROUNDED**"], 0, u"注入で GROUNDED は 0")
    _eq(ac["XBRL"][u"**注入で検査通過(誤りを通す)**"], 0, u"注入で検査通過は 0")
    _eq((ac["XBRL"][u"行"], ac["XBRL"][u"注入"], ac["XBRL"][u"無改変"]), (192, 64, 128), u"写し: 分母")
    # 0 USD・入口・所要
    z = rec[u"0 USD"]
    _eq((z[u"在った件数"], z["provider"]), (0, None), u"0 USD")
    _eq(len(z[u"見た環境変数"]), 4, u"鍵の環境変数は 4 つ")
    _eq(rec[u"入口"][u"配布名 qwed の版(importlib.metadata)"], "7.3.0", u"qwed の版")
    _eq(rec[u"入口"][u"qwed_new.__version__"], "7.3.0", u"qwed_new の版")
    _true(rec[u"入口"]["sys.version"].startswith("3.11.17"), u"Python 3.11.17 でない")
    _eq(rec[u"入口"][u"fact_verifier.py の sha256"], rec_b[u"入口"][u"fact_verifier.py の sha256"], u"fact_verifier.py が段 B と違う")
    _true(re.fullmatch(r"[0-9a-f]{64}", rec[u"入口"][u"fact_verifier.py の sha256"]), u"fact_verifier.py の sha256")
    _true(rec[u"所要秒"][u"E′ + 対照"] < 300, u"300 秒以上")
    # 対照 C-2(E′a)
    c2 = rec[u"対照"]["C-2"]
    _true(c2[u"**期待どおり**"], u"C-2")
    _eq(c2[u"元の行の結果"]["entity_match"], 1.0, u"C-2: 元は 1.0")
    _true(c2[u"結果"]["entity_match"] < 1.0, u"C-2: +1 で < 1.0")
    _eq(c2[u"元の claim"], REAL["eprime-a"], u"C-2 の元の claim")
    _eq(c2[u"+1 の claim"], "Fact OrdinaryIncome in CurrentYearDuration equals 12497000001.", u"C-2 の +1 の claim")
    # 外れの原因の読み(行から数え直す)
    cz = rec[u"**外れの原因の読み**"]
    for v in VARIANTS:
        rs = rows[v]
        one = [r for r in rs if r[u"注入か"] and r["entity_match"] == 1.0]
        pas = [r for r in one if r[u"分類"] == u"通す"]
        _eq(cz[v][u"注入で 1.0 の行"], len(one), u"%s 注入で 1.0 の行" % v)
        _eq(cz[v][u"注入で 1.0 の verdict"], dict(collections.Counter(r["deterministic_verdict"] for r in one)), u"%s 注入で 1.0 の verdict" % v)
        _eq(cz[v][u"通す(注入)"], len(pas), u"%s 通す(注入)" % v)
        _eq(cz[v][u"通す(注入)で claim に否定語の部分一致が在る"], _n(pas, lambda r: r[u"読み"][u"claim の否定語(部分一致)"]), u"%s 通す 否定語あり" % v)
        _eq(cz[v][u"通す(注入)で claim に否定語の部分一致が無い"], _n(pas, lambda r: not r[u"読み"][u"claim の否定語(部分一致)"]), u"%s 通す 否定語なし" % v)
        _eq(len(cz[v][u"通す(注入)の明細"]), len(pas), u"%s 通す の明細" % v)
        _eq(cz[v][u"REFUTED の行"], cnt[v]["verdict"].get("REFUTED", 0), u"%s REFUTED" % v)
        _eq(cz[v][u"値の字が一覧に在るのに entity_match < 1.0"], 0, u"%s 在るのに < 1.0" % v)
        _eq(cz[v][u"entity_match 1.0 なのに値の字が一覧に無い"], 0, u"%s 1.0 なのに無い" % v)
        _eq(cz[v][u"値の字が一覧の数の字に在る(そのまま)"], _n(rs, lambda r: r[u"読み"][u"値の字が一覧の数の字に在る(そのまま)"]), u"%s 在る" % v)
        _eq(cz[v][u"値の字が一覧の数の字に在る(そのまま)"], cnt[v][u"entity_match 1.0"], u"%s 在る = 1.0" % v)
        _eq(cz[v][u"GROUNDED 18 行の verdict"], dict(collections.Counter(r["deterministic_verdict"] for r in rs if r[u"合成の後"] == "GROUNDED")),
            u"%s GROUNDED の verdict" % v)
    # 予測との照合
    p = rec[u"**予測との照合**"]
    q = p[u"欄ごと"]
    _eq([x[u"記号"] for x in q], ["Q-%d" % i for i in range(18, 25)], u"Q-18〜Q-24")
    _eq([x[u"記号"] for x in q if x[u"当たり"] is False], MISSES, u"外れの記号")
    _eq([x[u"記号"] for x in q if x[u"当たり"] is True], HITS, u"当たりの記号")
    _eq((p[u"当たり"], p[u"外れ"], p[u"未測"]),
        (_n(q, lambda x: x[u"当たり"] is True), _n(q, lambda x: x[u"当たり"] is False), _n(q, lambda x: x[u"当たり"] is None)),
        u"当たり / 外れ / 未測 の集計")
    _eq(p[u"外れの記号"], [x[u"記号"] for x in q if x[u"当たり"] is False], u"外れの記号の一覧")
    by = {x[u"記号"]: x for x in q}
    ea, eb = rows["eprime-a"], rows["eprime-b"]
    _eq(by["Q-18"][u"実測"][u"1.0"], _em1([r for r in ea if r[u"合成の後"] == "GROUNDED"]), u"Q-18 と行")
    _eq(by["Q-18"][u"当たり"], by["Q-18"][u"実測"][u"1.0"] == 18, u"Q-18 の判定")
    _eq(by["Q-19"][u"実測"][u"1.0"], _em1([r for r in ea if r[u"注入か"]]), u"Q-19 と行")
    _eq(by["Q-19"][u"当たり"], 0 <= by["Q-19"][u"実測"][u"1.0"] <= 3, u"Q-19 の判定")
    _eq(by["Q-20"][u"実測"][u"1.0"], _em1([r for r in eb if r[u"注入の型"] == "T5_COINCIDENT"]), u"Q-20 と行")
    _eq(by["Q-20"][u"実測"][u"1.0"], cnt["eprime-b"][u"型ごとの entity_match 1.0"]["T5_COINCIDENT"], u"Q-20 と件数")
    _eq(by["Q-20"][u"当たり"], 34 <= by["Q-20"][u"実測"][u"1.0"] <= 38, u"Q-20 の判定")
    _eq(by["Q-21"][u"実測"][u"通す(注入)"], _n(eb, lambda r: r[u"注入か"] and r[u"分類"] == u"通す"), u"Q-21 と行")
    _eq(by["Q-21"][u"実測"][u"注入で 1.0"], _em1([r for r in eb if r[u"注入か"]]), u"Q-21 の 1.0 と行")
    _eq(by["Q-21"][u"当たり"], 0 <= by["Q-21"][u"実測"][u"通す(注入)"] <= 5 and by["Q-21"][u"実測"][u"注入で 1.0"] >= 34, u"Q-21 の判定")
    _eq(by["Q-22"][u"実測"], {u"E′a": _n(ea, lambda r: r["status"] == "BLOCKED"), u"E′b": _n(eb, lambda r: r["status"] == "BLOCKED")}, u"Q-22 と行")
    _eq(by["Q-22"][u"当たり"], all(55 <= by["Q-22"][u"実測"][k] <= 70 for k in (u"E′a", u"E′b")), u"Q-22 の判定")
    _eq(by["Q-23"][u"実測"][u"+1"], c2[u"結果"]["entity_match"], u"Q-23 と対照")
    _eq(by["Q-23"][u"当たり"], c2[u"**期待どおり**"], u"Q-23 の判定")
    _eq(by["Q-24"][u"実測"][u"1.0"], _em1([r for r in eb if r[u"合成の後"] == "GROUNDED"]), u"Q-24 と行")
    _eq(by["Q-24"][u"当たり"], 0 <= by["Q-24"][u"実測"][u"1.0"] <= 2, u"Q-24 の判定")
    # 木
    tree = rec[u"木"]
    _eq(tree[u"core/・adapters/ の差分の行数"], 0, u"engine の差分")
    _eq(tree[u"core/・adapters/ の status"], [], u"engine の status")
    return True


# ---------------------------------------------------------------- 文書(数を記録に縛る)
def check_doc(t, rec):
    p = rec[u"**予測との照合**"]
    cnt = rec[u"**件数**"]
    cz = rec[u"**外れの原因の読み**"]
    ac = rec[u"**Audit Core 側の写し(段 B の記録から。再実行しない)**"]
    ca, cb = cnt["eprime-a"], cnt["eprime-b"]
    ta, tb = ca[u"型ごとの entity_match 1.0"], cb[u"型ごとの entity_match 1.0"]
    head = t.splitlines()[0]
    _true(u"予測 当たり %d / 外れ %d**" % (p[u"当たり"], p[u"外れ"]) in head, u"見出しの当たり / 外れ: " + head)
    _true(u"E′a %d / %d" % (ca[u"GROUNDED で entity_match 1.0"], 18) in head and u"E′b %d / 18" % cb[u"GROUNDED で entity_match 1.0"] in head,
          u"見出しの GROUNDED")
    _true(u"E′a %d / 50・E′b %d / 50" % (ta["T5_COINCIDENT"], tb["T5_COINCIDENT"]) in head, u"見出しの T5")
    _true(u"QWED が通した注入は %d / 64" % cb[u"通す(注入)"] in head, u"見出しの 通す")
    _true(u"commit `%s`" % rec[u"追記 2 の commit"] in t, u"追記 2 の commit")
    _true(u"**封は直さない。**" in t, u"封は直さない")
    _true(u"**W1・S は走らせていない**" in t, u"W1・S")
    b1 = sec(t, "## §1", "## §2")
    real = rec[u"実物の 1 行(追記 2)"]
    _true(u"`%s`" % real["eprime-a"][u"context の行"] in b1, u"§1 実物の context の行")
    _true(u"| E′a | Audit Core が GROUNDED にした 18 行の `entity_match` 1.0 | **%d / 18** |" % ca[u"GROUNDED で entity_match 1.0"] in b1, u"§1 E′a GROUNDED")
    _true(u"| E′a | 注入 64 行の `entity_match` 1.0 | %d / 64(T5 %d / 50・T3 %d / 12・T1 %d / 2)|"
          % (ca[u"注入で entity_match 1.0"], ta["T5_COINCIDENT"], ta["T3_ABSENT"], ta["T1_VALUE"]) in b1, u"§1 E′a 注入")
    _true(u"| E′a | QWED が通す(注入)| **%d / 64**(全体 %d / 192。" % (ca[u"通す(注入)"], ca[u"通す(全体)"]) in b1, u"§1 E′a 通す")
    _true(u"| E′b | T5 50 行の `entity_match` 1.0 | **%d / 50** |" % tb["T5_COINCIDENT"] in b1, u"§1 E′b T5")
    _true(u"| E′b | 注入 64 行の `entity_match` 1.0 | %d / 64 |" % cb[u"注入で entity_match 1.0"] in b1, u"§1 E′b 注入")
    _true(u"| E′b | QWED が通す(注入)| **%d / 64**(全体 %d / 192)|" % (cb[u"通す(注入)"], cb[u"通す(全体)"]) in b1, u"§1 E′b 通す")
    _true(u"| E′b | QWED が違うと言う(注入)| %d / 64(判定なし %d)|"
          % (cb[u"注入の分類"].get(u"違うと言う", 0), cb[u"注入の分類"].get(u"判定なし", 0)) in b1, u"§1 E′b 違うと言う")
    _true(u"| E′b | GROUNDED 18 行の `entity_match` 1.0 | **%d / 18** |" % cb[u"GROUNDED で entity_match 1.0"] in b1, u"§1 E′b GROUNDED")
    _true(u"| E′a・E′b | `status` BLOCKED(= REFUTED)| %d / 192・%d / 192" % (ca["status"].get("BLOCKED", 0), cb["status"].get("BLOCKED", 0)) in b1,
          u"§1 BLOCKED")
    _true(u"| Audit Core | 注入で検査通過(誤りを通す)| **%d / 64**(engine の GROUNDED %d / 64。"
          % (ac["XBRL"][u"**注入で検査通過(誤りを通す)**"], ac["XBRL"][u"**注入で GROUNDED**"]) in b1, u"§1 Audit Core")
    _true(u"E′a %d 行・E′b %d 行。在るのに < 1.0 は %d・1.0 なのに無い %d"
          % (ca[u"entity_match 1.0"], cb[u"entity_match 1.0"], cz["eprime-a"][u"値の字が一覧に在るのに entity_match < 1.0"],
             cz["eprime-b"][u"entity_match 1.0 なのに値の字が一覧に無い"]) in b1, u"§1 在る ⇔ 1.0")
    _true(u"E′b の SUPPORTED %d 行のうち `entity_match` 1.0 は %d・< 1.0 は %d"
          % (cb["verdict"].get("SUPPORTED", 0), cb[u"通す(全体)"], cb["verdict"].get("SUPPORTED", 0) - cb[u"通す(全体)"]) in b1, u"§1 E′b SUPPORTED")
    _true(u"E′a の SUPPORTED %d 行のうち 1.0 は %d・< 1.0 は %d"
          % (ca["verdict"].get("SUPPORTED", 0), ca[u"通す(全体)"], ca["verdict"].get("SUPPORTED", 0) - ca[u"通す(全体)"]) in b1, u"§1 E′a SUPPORTED")
    vd = cz["eprime-b"][u"注入で 1.0 の verdict"]
    _true(u"SUPPORTED %d・NEUTRAL %d・REFUTED %d" % (vd.get("SUPPORTED", 0), vd.get("NEUTRAL", 0), vd.get("REFUTED", 0)) in b1, u"§1 注入で 1.0 の verdict")
    lists = rec[u"分母"][u"E′ の一覧"]["eprime-a"]
    for d, x in lists.items():
        _true(u"| %s | %s | %s | %s | %d |" % (d, format(x[u"fact(全部が数)"], ","), format(x[u"字数"], ","),
                                             format(x[u"段 B の描き方(str(float))の字数"], ","), x[u"chunk の数"]) in b1, u"§1-1 の一覧: " + d)
    c2 = rec[u"対照"]["C-2"]
    _true(u"**%s → %s**" % (c2[u"元の行の結果"]["entity_match"], c2[u"結果"]["entity_match"]) in b1, u"§1-2 C-2")
    b2 = sec(t, "## §2", "## §3")
    by = {x[u"記号"]: x for x in p[u"欄ごと"]}
    _true(u"Q-20 は %d(予測 34〜38)、Q-24 は %d(予測 0〜2)" % (by["Q-20"][u"実測"][u"1.0"], by["Q-24"][u"実測"][u"1.0"]) in b2, u"§2 1 文目の数")
    _true((u"― 当たり。**" in b2) == bool(by["Q-20"][u"当たり"] and by["Q-24"][u"当たり"]), u"§2 1 文目の判定")
    _true(u"通すは %d / 64" % by["Q-21"][u"実測"][u"通す(注入)"] in b2, u"§2 2 文目の数")
    _true((u"― 外れ。**" in b2) == (not by["Q-21"][u"当たり"]), u"§2 2 文目の判定")
    b3 = sec(t, "## §3", "## §4")
    _true(u"**当たり %d / 外れ %d。**" % (p[u"当たり"], p[u"外れ"]) in b3, u"§3 の当たり / 外れ")
    _eq(len(re.findall(r"\| \*\*当たり\*\* \|", b3)), p[u"当たり"], u"§3 当たりの行数")
    _eq(len(re.findall(r"\| \*\*外れ\*\* \|", b3)), p[u"外れ"], u"§3 外れの行数")
    for sym in p[u"外れの記号"]:
        _true(re.search(r"\| \*\*%s\*\* \|.*\| \*\*外れ\*\* \|" % re.escape(sym), b3), u"§3 の外れの行: " + sym)
        _true(re.search(r"(?m)^- \*\*%s 外れ\*\*: " % re.escape(sym), b3), u"§3 の外れの原因: " + sym)
    for sym in (x[u"記号"] for x in p[u"欄ごと"] if x[u"当たり"] is True):
        _true(re.search(r"\| %s \|.*\| \*\*当たり\*\* \|" % re.escape(sym), b3), u"§3 の当たりの行: " + sym)
    _true(u"| Q-18 | E′a: GROUNDED 18 行の 1.0 は 18 / 18 | %d / 18 |" % by["Q-18"][u"実測"][u"1.0"] in b3, u"§3 Q-18")
    _true(u"| Q-20 | E′b: T5 50 行の 1.0 は 34〜38 | %d |" % by["Q-20"][u"実測"][u"1.0"] in b3, u"§3 Q-20")
    _true(u"通す **%d** / 64・1.0 は %d / 64 |" % (by["Q-21"][u"実測"][u"通す(注入)"], by["Q-21"][u"実測"][u"注入で 1.0"]) in b3, u"§3 Q-21")
    _true(u"| %d・%d |" % (by["Q-22"][u"実測"][u"E′a"], by["Q-22"][u"実測"][u"E′b"]) in b3, u"§3 Q-22")
    _true(u"| Q-24 | E′b: GROUNDED 18 行の 1.0 は 0〜2 | %d |" % by["Q-24"][u"実測"][u"1.0"] in b3, u"§3 Q-24")
    czb = cz["eprime-b"]
    _true(u"通す %d(予測 0〜5)" % czb[u"通す(注入)"] in b3, u"§3 Q-21 の 通す")
    _true(u"通す %d のうち **%d は claim に `no` の部分列が在る行**" % (czb[u"通す(注入)"], czb[u"通す(注入)で claim に否定語の部分一致が在る"]) in b3,
          u"§3 Q-21 否定語あり")
    _true(u"残る **%d は claim に否定語の無い行**" % czb[u"通す(注入)で claim に否定語の部分一致が無い"] in b3, u"§3 Q-21 否定語なし")
    rest = czb[u"注入で 1.0 の行"] - czb[u"通す(注入)"]
    _true(u"残る %d 行(NEUTRAL %d・REFUTED %d" % (rest, vd.get("NEUTRAL", 0), vd.get("REFUTED", 0)) in b3, u"§3 Q-21 残る行")
    for x in czb[u"通す(注入)の明細"]:
        _true(x["id"] in b3 or x["doc"] in b3, u"§3 に通す行の書類が無い: %s %s" % (x["doc"], x["id"]))
    secs = rec[u"所要秒"]
    _true(u"**E′ + 対照 %s 秒**" % secs[u"E′ + 対照"] in b3, u"§3 所要秒")
    _true(u"E′a %s 秒、E′b %s 秒" % (secs["eprime-a"], secs["eprime-b"]) in b3, u"§3 所要秒の内訳")
    _true(u"395 / 395 行で一致" in b3, u"§3 段 B の挙動が変わっていないこと")
    b4 = sec(t, "## §4")
    _true(u"**同じ 8 書類である。**" in b4, u"§4 限界")
    _true(u"**W1・S は走らせていない。**" in b4, u"§4 W1・S")
    _true(u"E′a %d・E′b %d" % (ca[u"無改変の分類"].get(u"通す", 0), cb[u"無改変の分類"].get(u"通す", 0)) in b4, u"§4 無改変で通す")
    return True


class RecordTest(unittest.TestCase):
    def test_1_record_is_consistent_with_its_rows_and_its_sources(self):
        self.assertTrue(check_record(load(REC)))

    def test_2_misses_stay_misses(self):
        p = load(REC)[u"**予測との照合**"]
        self.assertEqual([x[u"記号"] for x in p[u"欄ごと"] if x[u"当たり"] is False], MISSES)

    def test_3_stage_b_record_is_untouched_by_eprime(self):
        u"""段 B の記録は E′ で書き換えない(段 B の主比較の数がそのまま)。"""
        b = load(REC_B)
        self.assertEqual(b[u"**件数**"]["E"][u"entity_match 1.0"], 0)
        self.assertEqual(b[u"**予測との照合**"][u"外れ"], 10)
        self.assertNotIn(u"走らせた", b)


class DocTest(unittest.TestCase):
    def test_4_doc_numbers_are_bound_to_the_record(self):
        self.assertTrue(check_doc(text(DOC), load(REC)))

    def test_5_the_gate_itself_does_not_import_qwed(self):
        src = text(os.path.abspath(__file__))
        self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+qwed")


if __name__ == "__main__":
    unittest.main()
