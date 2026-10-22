# -*- coding: utf-8 -*-
u"""QWED 比較の実測(docs/QWED_COMPARE_RESULT_2026-10-19.md)の門。

**本文の数は `fixtures/xbrl/cd8/qwed_compare_2026-10-19.json` を正本に突き合わせる。**
QWED は import しない(この門は 3.9 で走る。記録 JSON しか読まない)。
Audit Core 側の写しは、その出どころ(`period_unit_hold_2026-10-19.json`・`errdet_core_2026-10-17.json`)から
数え直して記録と突き合わせる(写しが動いたら赤)。
**外れ 10 欄が外れとして残ること、「QWED が通す 注入 0 / 64」が行から数え直せることを固定する。**

変異 3 通り(封 §6)は in-memory で当てる: `check_record(rec)` / `check_doc(text, rec)` に書き換えた dict・字を渡す。
"""
import collections
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "QWED_COMPARE_RESULT_2026-10-19.md")
REC = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "qwed_compare_2026-10-19.json")
REC_PU = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "period_unit_hold_2026-10-19.json")
REC_ERRDET = os.path.join(ROOT, "fixtures", "sheet", "errdet_core_2026-10-17.json")
#: Q-1〜Q-16 の外れ(字で留める。**外れは外れとして残す**)。Q-17(木・pytest)は記録の pytest の欄から動的に決める
MISSES_16 = ["Q-2", "Q-3", "Q-4", "Q-5", "Q-7", "Q-8", "Q-9", "Q-10", "Q-11", "Q-12"]
HITS_16 = ["Q-1", "Q-6", "Q-13", "Q-14", "Q-15", "Q-16"]
FIELDS = ("status", "deterministic_verdict", "deterministic_confidence", "semantic_similarity",
          "keyword_overlap", "entity_match", "negation_conflict", "citations", "constraint_id")


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


# ---------------------------------------------------------------- 記録の中身(変異はここに当てる)
def check_record(rec):
    rows = rec["rows"]
    w1, e, s = rows["W1"], rows["E"], rows["S"]
    _eq((len(w1), len(e), len(s)), (192, 192, 11), u"行の数")
    for name, rs in (("W1", w1), ("E", e), ("S", s)):
        for r in rs:
            for k in FIELDS:
                _true(k in r, u"%s の読む欄が無い: %s" % (name, k))
            _eq(r[u"分類"], classify(r), u"%s %s の分類" % (name, r.get("id", r.get(u"文の番号"))))
    # 分母
    _eq(sum(1 for r in w1 if r[u"注入か"]), 64, u"W1 注入")
    _eq(sum(1 for r in e if r[u"注入か"]), 64, u"E 注入")
    _eq(collections.Counter(r[u"注入の型"] for r in e if r[u"注入か"]),
        {"T5_COINCIDENT": 50, "T3_ABSENT": 12, "T1_VALUE": 2}, u"注入の型")
    _eq(sum(len(r["ids"]) for r in s), 35, u"S の id")
    _eq(sum(1 for r in s if r[u"誤り"]), 8, u"S の誤りの文")
    _eq(sorted(r[u"誤り"]["id"] for r in s if r[u"誤り"]),
        ["R001", "R004", "R009", "R010", "R012", "R021", "R024", "R030"], u"S の誤りの id")
    _true(all(r[u"誤り"][u"置き換えた回数"] == 1 for r in s if r[u"誤り"]), u"置換が 1 回でない")
    _true(all(r[u"context の字数"] == 4194 for r in s), u"S の context が 4,194 字でない")
    el = rec[u"分母"][u"E の一覧"]
    _eq(sum(1 for v in el.values() if v[u"一致"]), 8, u"E の一覧の 8 / 8")
    _eq(sum(v[u"chunk の数"] for v in el.values()), 11, u"chunk の数")
    _true(all(c <= 95000 for v in el.values() for c in v[u"chunk"]), u"chunk が 95,000 字を超える")
    # 件数は行から数え直す
    cnt = rec[u"**件数**"]
    _eq(cnt["W1"][u"分類"], dict(collections.Counter(r[u"分類"] for r in w1)), u"W1 分類")
    _eq(cnt["W1"][u"注入の分類"], dict(collections.Counter(r[u"分類"] for r in w1 if r[u"注入か"])), u"W1 注入の分類")
    _eq(cnt["W1"]["status"], dict(collections.Counter(r["status"] for r in w1)), u"W1 status")
    _eq(cnt["W1"]["verdict"], dict(collections.Counter(r["deterministic_verdict"] for r in w1)), u"W1 verdict")
    _eq(cnt["W1"][u"entity_match 1.0"], sum(1 for r in w1 if r["entity_match"] == 1.0), u"W1 1.0")
    _eq(cnt["E"][u"分類"], dict(collections.Counter(r[u"分類"] for r in e)), u"E 分類")
    _eq(cnt["E"][u"注入の分類"], dict(collections.Counter(r[u"分類"] for r in e if r[u"注入か"])), u"E 注入の分類")
    _eq(cnt["E"][u"無改変の分類"], dict(collections.Counter(r[u"分類"] for r in e if not r[u"注入か"])), u"E 無改変の分類")
    _eq(cnt["E"]["verdict"], dict(collections.Counter(r["deterministic_verdict"] for r in e)), u"E verdict")
    _eq(cnt["E"]["status"], dict(collections.Counter(r["status"] for r in e)), u"E status")
    _eq(cnt["E"][u"entity_match 1.0"], sum(1 for r in e if r["entity_match"] == 1.0), u"E 1.0")
    _eq(cnt["S"][u"誤りの文の分類"], dict(collections.Counter(r[u"分類"] for r in s if r[u"誤り"])), u"S 誤りの分類")
    _eq(cnt["S"]["status"], dict(collections.Counter(r["status"] for r in s)), u"S status")
    _eq(cnt["S"]["verdict"], dict(collections.Counter(r["deterministic_verdict"] for r in s)), u"S verdict")
    # E: 行の結果は entity_match 最大の chunk(同点は前)
    for r in e:
        per = r[u"chunk ごと"]
        vals = [(x["entity_match"] if x["entity_match"] is not None else -1.0) for x in per]
        _eq(r[u"採った chunk"], vals.index(max(vals)), u"E %s %s の chunk の採り方" % (r["doc"], r["id"]))
        _eq({k: r[k] for k in FIELDS}, {k: per[r[u"採った chunk"]][k] for k in FIELDS}, u"E の行の結果が chunk の結果でない")
    # 主比較の数(Q-5・Q-9)
    _eq(cnt["E"][u"注入の分類"].get(u"通す", 0), 0, u"E で QWED が通す 注入")
    _eq(cnt["W1"][u"注入の分類"].get(u"通す", 0), 3, u"W1 で QWED が通す 注入")
    _eq(cnt["W1"][u"分類"].get(u"通す", 0), 5, u"W1 で QWED が通す 全体")
    # Audit Core 側の写しは出どころから数え直す
    ac = rec[u"**Audit Core 側の写し(再実行しない)**"]
    pu = load(REC_PU)["rows"]
    inj = [r for r in pu if r[u"注入か"]]
    _eq(ac["XBRL"][u"**注入で GROUNDED**"], sum(1 for r in inj if r[u"**合成の後**"] == "GROUNDED"), u"写し: 注入で GROUNDED")
    _eq(ac["XBRL"][u"**注入で検査通過(誤りを通す)**"], sum(1 for r in inj if r[u"**最終判定(後)**"] == u"検査通過"),
        u"写し: 注入で検査通過")
    _eq(ac["XBRL"][u"**注入で GROUNDED**"], 0, u"注入で GROUNDED は 0")
    _eq(ac["XBRL"][u"**注入で検査通過(誤りを通す)**"], 0, u"注入で検査通過は 0")
    _eq((ac["XBRL"][u"行"], ac["XBRL"][u"注入"], ac["XBRL"][u"無改変"]), (192, 64, 128), u"写し: 分母")
    ec = load(REC_ERRDET)[u"検出 / 保留 / 見落とし(誤り 8 件)"]
    _eq((ac[u"表計算"][u"検出"], ac[u"表計算"][u"保留"], ac[u"表計算"][u"見落とし"]),
        (ec[u"検出"][u"件数"], ec[u"保留"][u"件数"], ec[u"見落とし"][u"件数"]), u"写し: 表計算")
    _eq((ac[u"表計算"][u"検出"], ac[u"表計算"][u"保留"], ac[u"表計算"][u"見落とし"]), (4, 4, 0), u"表計算は 4 / 4 / 0")
    # 0 USD・入口・所要
    z = rec[u"0 USD"]
    _eq((z[u"在った件数"], z["provider"]), (0, None), u"0 USD")
    _eq(len(z[u"見た環境変数"]), 4, u"鍵の環境変数は 4 つ")
    _eq(rec[u"入口"][u"配布名 qwed の版(importlib.metadata)"], "7.3.0", u"qwed の版")
    _true(rec[u"入口"]["sys.version"].startswith("3.11.17"), u"Python 3.11.17 でない")
    _true(re.fullmatch(r"[0-9a-f]{64}", rec[u"入口"][u"fact_verifier.py の sha256"]), u"fact_verifier.py の sha256")
    _true(rec[u"所要秒"][u"3 本 + 対照"] < 300, u"300 秒以上")
    # 対照
    c = rec[u"対照"]
    _true(c["C-1"][u"**期待どおり**"], u"C-1")
    _true(not c["C-2"][u"**期待どおり**"], u"C-2 は外れとして残す")
    _eq(c["C-2"][u"結果"]["entity_match"], c["C-2"][u"元の行の結果"]["entity_match"], u"C-2: +1 で entity_match が動いていない")
    _true(c["C-3"][u"**期待どおり**"], u"C-3")
    _eq(c["C-3"][u"**その数から抜けた字**"], ["385", "483"], u"C-3 の字")
    # 予測との照合
    p = rec[u"**予測との照合**"]
    q = p[u"欄ごと"]
    _eq([x[u"記号"] for x in q], ["Q-%d" % i for i in range(1, 18)], u"Q-1〜Q-17")
    _eq([x[u"記号"] for x in q if x[u"当たり"] is False and x[u"記号"] != "Q-17"], MISSES_16, u"外れの記号(Q-1〜Q-16)")
    _eq([x[u"記号"] for x in q if x[u"当たり"] is True and x[u"記号"] != "Q-17"], HITS_16, u"当たりの記号(Q-1〜Q-16)")
    _eq((p[u"当たり"], p[u"外れ"], p[u"未測"]),
        (sum(1 for x in q if x[u"当たり"] is True), sum(1 for x in q if x[u"当たり"] is False),
         sum(1 for x in q if x[u"当たり"] is None)), u"当たり / 外れ / 未測 の集計")
    _eq(p[u"外れの記号"], [x[u"記号"] for x in q if x[u"当たり"] is False], u"外れの記号の一覧")
    by = {x[u"記号"]: x for x in q}
    _eq(by["Q-9"][u"実測"][u"QWED が通す(注入)"], cnt["E"][u"注入の分類"].get(u"通す", 0), u"Q-9 と件数")
    _eq(by["Q-5"][u"実測"][u"注入の分類"], cnt["W1"][u"注入の分類"], u"Q-5 と件数")
    _eq(by["Q-4"][u"実測"], {u"注入": sum(1 for r in w1 if r[u"注入か"] and r["entity_match"] == 1.0),
                            u"全体": cnt["W1"][u"entity_match 1.0"]}, u"Q-4 と行")
    _eq(by["Q-8"][u"実測"][u"T5 で 1.0"], sum(1 for r in e if r[u"注入の型"] == "T5_COINCIDENT" and r["entity_match"] == 1.0),
        u"Q-8 と行")
    _eq(by["Q-11"][u"実測"][u"1.0"], sum(1 for r in e if r[u"合成の後"] == "GROUNDED" and r["entity_match"] == 1.0), u"Q-11 と行")
    _eq(by["Q-14"][u"実測"][u"1.0"], sum(1 for r in s if r[u"誤り"] and r["entity_match"] == 1.0), u"Q-14 と行")
    tree = rec[u"木"]
    _eq(tree[u"core/・adapters/ の差分の行数"], 0, u"engine の差分")
    _eq(tree[u"core/・adapters/ の status"], [], u"engine の status")
    py = tree[u"pytest(tests/measure、3.9)"]
    _eq(by["Q-17"][u"実測"]["pytest"], py, u"Q-17 と木")
    if py is None:                                      # 門を書く前の 1 回だけ通る形(未測)。他の欄は全部照合する
        _eq(by["Q-17"][u"当たり"], None, u"pytest が未測なら Q-17 は未測")
    else:
        _eq(by["Q-17"][u"当たり"], py["failed"] == 0, u"Q-17 の当たりは pytest の赤 0 と同値")
        _eq(len(py[u"赤の試験"]), py["failed"], u"赤の試験の名前の数")
    # 外れの原因の読み(0 件の原因が字で在る)
    cz = rec[u"**外れの原因の読み**"]
    _eq(cz["E"][u"全体"][u"値の字が一覧の数の字に在る(そのまま)"], 0, u"E: 値の字そのまま")
    _eq(cz["E"][u"全体"][u"値の字 + '.0' が一覧の数の字に在る"],
        sum(1 for r in e if r[u"読み"][u"値の字 + '.0' が一覧の数の字に在る"]), u"E: .0 の数え直し")
    _eq(cz["E"][u"Audit Core が GROUNDED"][u"値の字 + '.0' が一覧の数の字に在る"], 18, u"E: GROUNDED 18 の .0")
    _eq(cz["E"][u"注入 T5"][u"換算した値が fact の値に在る(数として)"], 0, u"E: T5 の換算した値")
    _eq(sum(x[u"件数"] for x in cz["E"][u"T5 の機構(行の単位 × 借りた ref の単位)"]), 50, u"T5 の機構の合計")
    _eq(cz["E"][u"REFUTED の行"], cnt["E"]["verdict"].get("REFUTED", 0), u"REFUTED の数え直し")
    _eq(cz["W1"][u"entity_match < 1.0 の行"], cz["W1"][u"context に無い数の字が在る行の entity_match < 1.0"],
        u"W1: < 1.0 は全部 context に無い数の字(抜粋の境)")
    _eq(cz["W1"][u"claim に英字の語が在る行の verdict"].get("SUPPORTED", 0), cnt["W1"]["verdict"].get("SUPPORTED", 0),
        u"W1: SUPPORTED は全部 英字の語の行")
    return True


# ---------------------------------------------------------------- 文書(数を記録に縛る)
def check_doc(t, rec):
    p = rec[u"**予測との照合**"]
    cnt = rec[u"**件数**"]
    ac = rec[u"**Audit Core 側の写し(再実行しない)**"]
    cz = rec[u"**外れの原因の読み**"]
    head = t.splitlines()[0]
    _true(u"予測 当たり %d / 外れ %d**" % (p[u"当たり"], p[u"外れ"]) in head, u"見出しの当たり / 外れ: " + head)
    _true(u"commit `%s`" % rec["seal_commit"] in t, u"封の commit")
    b1 = sec(t, "## §1", "## §2")
    ew = cnt["E"][u"注入の分類"]
    w = cnt["W1"][u"注入の分類"]
    _true(u"| E | QWED が通す(注入)| **%d / 64** |" % ew.get(u"通す", 0) in b1, u"§1 E 通す")
    _true(u"| E | QWED が違うと言う(注入)| %d / 64 |" % ew.get(u"違うと言う", 0) in b1, u"§1 E 違うと言う")
    _true(u"| W1 | QWED が通す(注入)| **%d / 64**(全体 %d / 192)|" % (w.get(u"通す", 0), cnt["W1"][u"分類"].get(u"通す", 0)) in b1,
          u"§1 W1 通す")
    _true(u"| W1 | QWED が違うと言う(注入)| %d / 64(全体 %d / 192)|" % (w.get(u"違うと言う", 0), cnt["W1"][u"分類"].get(u"違うと言う", 0)) in b1,
          u"§1 W1 違うと言う")
    _true(u"| Audit Core | 注入で検査通過(誤りを通す)| **%d / 64**(engine の GROUNDED %d / 64)|"
          % (ac["XBRL"][u"**注入で検査通過(誤りを通す)**"], ac["XBRL"][u"**注入で GROUNDED**"]) in b1, u"§1 Audit Core")
    sc = cnt["S"][u"誤りの文の分類"]
    _true(u"| S | 誤り 8 文で QWED が違うと言う | %d / 8(entity_match 1.0 は %d / 8)|"
          % (sc.get(u"違うと言う", 0), sum(1 for r in rec["rows"]["S"] if r[u"誤り"] and r["entity_match"] == 1.0)) in b1, u"§1 S")
    _true(u"| Audit Core | 表計算の誤り 8 件 | 検出 %d・保留 %d・見落とし %d |"
          % (ac[u"表計算"][u"検出"], ac[u"表計算"][u"保留"], ac[u"表計算"][u"見落とし"]) in b1, u"§1 表計算")
    _true(u"entity_match 1.0 は **0 / 192**" in b1 if cnt["E"][u"entity_match 1.0"] == 0 else True, u"§1 E の 1.0")
    _true(u"**%d / 192** が REFUTED" % cnt["E"]["verdict"].get("REFUTED", 0) in b1, u"§1 REFUTED")
    b3 = sec(t, "## §3", "## §4")
    _true(u"**当たり %d / 外れ %d。**" % (p[u"当たり"], p[u"外れ"]) in b3, u"§3 の当たり / 外れ")
    _eq(len(re.findall(r"\| \*\*当たり\*\* \|", b3)), p[u"当たり"], u"§3 当たりの行数")
    _eq(len(re.findall(r"\| \*\*外れ\*\* \|", b3)), p[u"外れ"], u"§3 外れの行数")
    for sym in p[u"外れの記号"]:
        _true(re.search(r"\| \*\*%s\*\* \|.*\| \*\*外れ\*\* \|" % re.escape(sym), b3), u"§3 の外れの行: " + sym)
        _true(re.search(r"(?m)^- \*\*%s 外れ\*\*: " % re.escape(sym), b3), u"§3 の外れの原因: " + sym)
    for sym in (x[u"記号"] for x in p[u"欄ごと"] if x[u"当たり"] is True):
        _true(re.search(r"\| %s \|.*\| \*\*当たり\*\* \|" % re.escape(sym), b3), u"§3 の当たりの行: " + sym)
    _true(u"値の字そのまま 0 / 192・`.0` を付けると %d / 192" % cz["E"][u"全体"][u"値の字 + '.0' が一覧の数の字に在る"] in b3, u"§3 .0")
    _true(u"GROUNDED 18 行は `.0` で %d / 18" % cz["E"][u"Audit Core が GROUNDED"][u"値の字 + '.0' が一覧の数の字に在る"] in b3,
          u"§3 GROUNDED の .0")
    _true(u"REFUTED %d 行のうち claim に否定語の部分一致が無いのが %d" % (cz["E"][u"REFUTED の行"], cz["E"][u"REFUTED で claim に否定語の部分一致が無い"]) in b3,
          u"§3 REFUTED")
    _true(u"英字の語が在る行 %d" % cz["W1"][u"claim に英字の語が在る行"] in b3, u"§3 W1 英字")
    _true(u"context に無い数の字が在る行 %d" % cz["W1"][u"context に無い数の字が在る行"] in b3, u"§3 W1 境")
    t5 = {(x[u"行の単位"], x[u"借りた ref の単位"]): x[u"件数"] for x in cz["E"][u"T5 の機構(行の単位 × 借りた ref の単位)"]}
    _true(u"千円 × 円 %d・百万円 × 円 %d・百万円 × 単位なし %d" % (t5.get((u"千円", u"円"), 0), t5.get((u"百万円", u"円"), 0),
                                                        t5.get((u"百万円", "None"), 0)) in b3, u"§3 T5 の機構")
    secs = rec[u"所要秒"]
    _true(u"3 本 + 対照 %s 秒" % secs[u"3 本 + 対照"] in b3, u"§3 所要秒")
    py = rec[u"木"][u"pytest(tests/measure、3.9)"]
    if py is not None:                                  # 未測(門を書く前)なら、この 1 行だけ照合しない
        _true(u"赤 %d 本" % py["failed"] in b3, u"§3 pytest")
        for name in py[u"赤の試験"]:
            _true(name.split("::")[0].split("/")[-1] in b3, u"§3 に赤の試験の名前が無い: " + name)
    b4 = sec(t, "## §4")
    _true(u"**同じ 8 書類・同じ 35 件である。**" in b4, u"§4 限界")
    _true(u"**封は直さない。**" in t, u"封は直さない")
    for m in re.finditer(u"QWED は計算、こちらは出所", t):
        pass
    _true(u"Q-5 は外れ・Q-9 は外れ" in t, u"Q-5・Q-9 の数で書く")
    return True


class RecordTest(unittest.TestCase):
    def test_1_record_is_consistent_with_its_rows_and_its_sources(self):
        self.assertTrue(check_record(load(REC)))

    def test_2_misses_stay_misses(self):
        p = load(REC)[u"**予測との照合**"]
        self.assertEqual([x[u"記号"] for x in p[u"欄ごと"] if x[u"当たり"] is False and x[u"記号"] != "Q-17"], MISSES_16)


class DocTest(unittest.TestCase):
    def test_3_doc_numbers_are_bound_to_the_record(self):
        self.assertTrue(check_doc(text(DOC), load(REC)))

    def test_4_the_gate_itself_does_not_import_qwed(self):
        src = text(os.path.abspath(__file__))
        self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+qwed")


if __name__ == "__main__":
    unittest.main()
