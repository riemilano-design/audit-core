# -*- coding: utf-8 -*-
"""**α(参照先検証)の天井を、commit 済みの記録だけから読む。0 USD・新しい計算をしない。**

人間の決定は α(「LLM が名指した参照先を Core が検査し、警告を足す」)だった。
**封を書く前に、その仕組みが届く上限を数える**(記憶 `opportunity-in-material-does-not-mean-it-fires`
― 封 v2 で「Core に出番が 0 行」を踏んだ直後なので、同じ型を 2 度踏まない)。

読むのは次の 3 つだけ。**どれも commit 済みで、書き換えない。**

  fixtures/xbrl/cd8/material_2026-10-17.json    行ごとの Core / D′ / D″ / 正解
  fixtures/xbrl/cd8/score_2026-10-17.json       席の答えの読み取り結果(腕 A)
  fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json  (ア)。**別の 8 書類**・同じ P16

**(ア) と本番は書類が違う。**profile はどちらも P16、関数も正規化も同じなので、
**変数は「書類」だけ**である(封 v2 §Δ 以降の読み替えではなく、記録の照合で確かめる)。

    python3 measure/xbrl_cd_ceiling_2026-10-17.py
"""
import collections
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
MAT = os.path.join(FX, "material_2026-10-17.json")
SCORE = os.path.join(FX, "score_2026-10-17.json")
PRIOR = os.path.join(FX, "a_core_vs_grep_2026-10-17.json")
OUT = os.path.join(FX, "ceiling_2026-10-17.json")
GOLD_KIND = u"参照先が在る"


def has_dimension(key):
    """正解の context に次元メンバーが付くか(`@...` の後ろに `member`)。"""
    return "member" in (key.split("@", 1)[1] if "@" in key else "")


def is_summary_element(key):
    """**主要な経営指標等の推移**の要素族か(`...summaryofbusinessresult*`)。"""
    return "summaryofbusinessresult" in key.split("@", 1)[0]


def t5_rows(mat, seat_by):
    """新しい 8 書類の T5 行を 1 か所で組み立てる(**判定を散らさない**)。"""
    out = []
    for p in mat[u"書類ごと"]:
        doc = p["docID"]
        for rid, pre in sorted(p[u"席の前に出せる分"].items()):
            g = pre[u"正解"]
            if not (g and g.get(u"種類") == GOLD_KIND):
                continue
            seat = seat_by[(doc, rid)][u"席"]
            out.append({u"doc": doc, u"id": rid, u"正解": g[u"正解"],
                        u"偶然一致する側": g[u"偶然一致する側"],
                        u"Core の参照先": pre["Core"][u"参照先"],
                        u"Core の言うこと": pre["Core"][u"言うこと"],
                        u"席の参照先": seat[u"参照先"],
                        u"Core に主張が対応したか":
                            pre["Core"][u"言うこと"] != u"対応が付かない"})
    return out


def ceiling(rows):
    """**α の天井**: 席が外した行で、Core が正解を持っているか。"""
    wrong = [r for r in rows
             if r[u"席の参照先"] is not None and r[u"席の参照先"] != r[u"正解"]]
    fixable = [r for r in wrong if r[u"Core の参照先"] == r[u"正解"]]
    same = [r for r in wrong if r[u"Core の参照先"] == r[u"席の参照先"]]
    silent = [r for r in wrong if r[u"Core の参照先"] is None]
    return {u"席が外した行": len(wrong),
            u"**Core が正解を持っていた**": len(fixable),
            u"Core が席と同じ参照先を出した": len(same),
            u"Core が参照先を出さなかった": len(silent),
            u"明細": [{u"doc": r[u"doc"], u"id": r[u"id"],
                     u"席": r[u"席の参照先"], u"Core": r[u"Core の参照先"],
                     u"正解": r[u"正解"], u"Core の言うこと": r[u"Core の言うこと"]}
                    for r in wrong]}


def rate(num, den):
    return {u"分子": num, u"分母": den,
            u"率": (round(100.0 * num / den, 1) if den else None)}


def strata(pairs):
    """(正解, 当たったか) の列から、次元つき・summary 要素で層別する。"""
    t = collections.Counter()
    for key, hit in pairs:
        for name in ((u"次元つき" if has_dimension(key) else u"次元なし"),
                     (u"summary 要素" if is_summary_element(key) else u"通常要素")):
            t[(name, u"n")] += 1
            t[(name, u"特定")] += bool(hit)
    return {k: rate(t[(k, u"特定")], t[(k, u"n")])
            for k in (u"次元なし", u"次元つき", u"通常要素", u"summary 要素")}


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    mat = json.load(io.open(MAT, encoding="utf-8"))
    sc = json.load(io.open(SCORE, encoding="utf-8"))
    pri = json.load(io.open(PRIOR, encoding="utf-8"))
    seat_by = {(r[u"doc"], r[u"id"]): r for r in sc[u"rows"]}
    rows = t5_rows(mat, seat_by)

    # **席が参照先を名指した行**(α が検査できる母集団)
    named = [r for r in sc[u"rows"] if r[u"席"][u"参照先"] is not None]
    pre_by = {}
    for p in mat[u"書類ごと"]:
        for rid, pre in p[u"席の前に出せる分"].items():
            pre_by[(p["docID"], rid)] = pre
    have_claim = [r for r in named
                  if pre_by[(r[u"doc"], r[u"id"])]["Core"][u"言うこと"]
                  != u"対応が付かない"]
    t5_named = [r for r in rows if r[u"席の参照先"] is not None]
    clean_named = [r for r in named
                   if pre_by[(r[u"doc"], r[u"id"])][u"正解"] is None]

    new_pairs = [(r[u"正解"], r[u"Core の参照先"] == r[u"正解"]) for r in rows]
    old_pairs = []
    for r in pri["rows"]:
        g = r.get(u"正解") or {}
        if g.get(u"種類") != GOLD_KIND or not r.get(u"対応が付いた"):
            continue
        old_pairs.append((g[u"正解"], r[u"腕"]["Core-P"][u"参照先"] == g[u"正解"]))

    per_doc = collections.Counter()
    for r in rows:
        per_doc[(r[u"doc"], u"n")] += 1
        per_doc[(r[u"doc"], u"特定")] += (r[u"Core の参照先"] == r[u"正解"])

    rec = {
        "step": u"**α の天井を commit 済みの記録から読む。0 USD・席を呼ばない**",
        u"読んだ記録": [os.path.relpath(p, ROOT) for p in (MAT, SCORE, PRIOR)],
        u"**変数は書類だけ**": {u"profile": {u"本番": mat["profile"],
                                    u"(ア)": pri["profile"]},
                        u"本番の 8 書類": [p["docID"] for p in mat[u"書類ごと"]],
                        u"(ア) の 8 書類": pri[u"書類"],
                        u"同じか": sorted(p["docID"] for p in mat[u"書類ごと"])
                        == sorted(pri[u"書類"])},
        u"α が検査できる母集団": {
            u"席が参照先を名指した行": len(named),
            u"うち Core に主張が対応した行": len(have_claim),
            u"うち正解が固定できる行(T5)": len(t5_named),
            u"無改変で名指した行": len(clean_named)},
        u"**α の天井(席が外した行で Core が正解を持っていたか)**": ceiling(rows),
        u"Core 自身の特定率": {
            u"本番(未使用 8 書類)": rate(sum(1 for r in rows
                                      if r[u"Core の参照先"] == r[u"正解"]),
                                  len(rows)),
            u"(ア)(別の 8 書類・同じ P16)":
                rate(sum(1 for _, h in old_pairs if h), len(old_pairs)),
            u"席(本番)": rate(sum(1 for r in rows
                               if r[u"席の参照先"] == r[u"正解"]), len(rows))},
        u"層別": {u"本番(未使用 8)": strata(new_pairs),
                u"(ア)(別の 8)": strata(old_pairs)},
        u"書類ごと(本番)": {d: rate(per_doc[(d, u"特定")], per_doc[(d, u"n")])
                      for d in sorted({r[u"doc"] for r in rows})},
        u"limits": [
            u"**これは新しい実験ではない。**commit 済みの 3 つの記録を読んだだけで、"
            u"engine も材料も席の答えも触っていない",
            u"**2 つの標本は書類が違う。**profile と関数と正規化は同じだが、"
            u"**書類差と注入箇所の差が混ざる**ので、差を「劣化」と読んではいけない",
            u"**書類ごとの散らばりが大きい**(下の表)。8 書類 1 標本の率を"
            u"「Core の性能」として単独で引用しない",
            u"**次元つきの層の 0 件は、原因を特定していない。**"
            u"Core がどの key を試したかはこの記録に無い(別便で測る)",
            u"**α の天井 0 件は「この標本で」である。**"
            u"別の標本で 0 になるとは言っていない",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    c = rec[u"**α の天井(席が外した行で Core が正解を持っていたか)**"]
    print(u"=== α の天井(commit 済みの記録だけ。0 USD)===")
    print(u"席が参照先を名指した行 %d / うち Core に主張が対応 %d / T5 %d"
          % (len(named), len(have_claim), len(t5_named)))
    print(u"**席が外した %d 行のうち、Core が正解を持っていたのは %d 行**"
          % (c[u"席が外した行"], c[u"**Core が正解を持っていた**"]))
    print(u"  (Core が参照先を出さなかった %d / 席と同じ参照先 %d)"
          % (c[u"Core が参照先を出さなかった"], c[u"Core が席と同じ参照先を出した"]))
    for k, v in rec[u"Core 自身の特定率"].items():
        print(u"  %-26s %s (%s/%s)" % (k, v[u"率"], v[u"分子"], v[u"分母"]))
    for s, st in rec[u"層別"].items():
        print(u"  層別 %-14s %s" % (s, json.dumps(
            {k: "%s%% (%s/%s)" % (v[u"率"], v[u"分子"], v[u"分母"])
             for k, v in st.items()}, ensure_ascii=False)))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
