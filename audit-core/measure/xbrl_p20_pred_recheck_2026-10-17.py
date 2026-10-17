# -*- coding: utf-8 -*-
"""**照合器の欠陥を記録して、字で書いた参照先そのもので数え直す。**

`measure/xbrl_p20_rerun_2026-10-17.py` の主張ごとの照合は、予測の欄が
**「正解」で始まるか**で「正解を予測した / 正解でないを予測した」を決めていた。
**`N007` の予測は参照先を字で書いていた**(`operatingincome@…_nonconsolidatedmember`)
ので、その字が正解と一致する行(`R011`)まで「正解ではないと予測した」に分類され、
**正しい予測が外れに数えられた**(記憶 `comparator-scores-wrong-answers-as-hits` の裏)。

**先の記録は書き換えない。**この script は 2 つ目の数え方を**別の記録**に足す。

  照合 1(先の記録): 予測の欄が「正解」で始まるか
  照合 2(ここ)  : **字で書いた参照先が在るならその字と比べる**。
                   無いときだけ「正解 / 正解ではない」で比べる

**どちらの数も残す。**結果を見てから照合器を緩めたのではないことを、
**両方を並べることで示す**(片方だけ残せば緩めたのと同じになる)。

    python3 measure/xbrl_p20_pred_recheck_2026-10-17.py
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
RUN = os.path.join(FX, "p20_rerun_2026-10-17.json")
PRED = os.path.join(FX, "branch_a_predictions_2026-10-17.json")
OUT = os.path.join(FX, "p20_pred_recheck_2026-10-17.json")


def literal_pointer(text):
    """予測の欄に**字で書かれた参照先**が在れば返す(`要素@context` の形)。"""
    cand = [w.strip(u"()「」 ") for w in text.replace(u"(", u" ").replace(
        u")", u" ").split()]
    for w in cand:
        if "@" in w and " " not in w:
            return w
    return None


def judge(pred_text, got, gold):
    """**判定を 1 か所に置く。**字が在れば字で、無ければ正解かどうかで。"""
    lit = literal_pointer(pred_text)
    if lit:
        return (u"字で書いた参照先", lit, got == lit)
    want_gold = pred_text.startswith(u"正解") and u"ではない" not in pred_text
    return (u"正解かどうか", (u"正解" if want_gold else u"正解ではない"),
            (got == gold) == want_gold)


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    run = json.load(io.open(RUN, encoding="utf-8"))
    pred = json.load(io.open(PRED, encoding="utf-8"))
    by = {(c["doc"], c[u"行"]): c
          for c in run[u"**予測との照合**"][u"主張ごと"]}
    rows = []
    for x in pred[u"主張ごとの予測(10 行 = 6 主張)"]:
        for rid in x[u"行"]:
            c = by[(x["doc"], rid)]
            kind, want, ok = judge(x[u"予測する参照先"],
                                   c[u"実測の参照先"], c[u"正解"])
            rows.append({u"doc": x["doc"], u"主張 id": x[u"主張 id"], u"行": rid,
                         u"予測の欄": x[u"予測する参照先"],
                         u"比べ方": kind, u"予測した値": want,
                         u"実測の参照先": c[u"実測の参照先"],
                         u"正解": c[u"正解"],
                         u"照合 1(先の記録)": c[u"当たり"],
                         u"**照合 2**": ok})
    h1 = sum(1 for r in rows if r[u"照合 1(先の記録)"])
    h2 = sum(1 for r in rows if r[u"**照合 2**"])
    diff = [r for r in rows if r[u"照合 1(先の記録)"] != r[u"**照合 2**"]]
    rec = {"seal": run["seal"],
           "step": u"**照合器の欠陥の記録。先の記録は書き換えない。0 USD**",
           u"**何が起きたか**": (
               u"照合 1 は予測の欄が「正解」で始まるかだけを見ていた。"
               u"**`N007` の予測は参照先を字で書いていたので、"
               u"その字が正解と一致する行まで「正解ではない」に分類された。**"
               u"予測が外れたのではなく、**私の照合器が外れに数えた**"),
           u"照合 1(先の記録・そのまま残す)": {u"当たり": h1, u"外れ": len(rows) - h1},
           u"**照合 2(字で書いた参照先で比べる)**": {u"当たり": h2,
                                        u"外れ": len(rows) - h2},
           u"**2 つの数え方で違った行**": diff,
           u"rows": rows,
           u"limits": [
               u"**照合器を結果の後で足した。**だから**両方の数を残す**。"
               u"片方だけ残せば「結果を見て緩めた」のと同じである",
               u"**予測の file は編集していない**(封 §3。sha256 を門で固定)",
               u"**実測の数(M-1〜M-6)は 1 つも変えていない。**変えたのは"
               u"「予測と実測が一致したか」の数え方だけである",
               u"**照合 2 でも、予測が当たったことは「Core が良くなった」ではない。**"
               u"同じ便で誤認定が 7 行増えている",
           ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== 照合器の欠陥(先の記録は書き換えない)===")
    print(u"照合 1(先の記録): 当たり %d / 外れ %d" % (h1, len(rows) - h1))
    print(u"**照合 2(字で比べる): 当たり %d / 外れ %d**" % (h2, len(rows) - h2))
    for r in diff:
        print(u"  違った行: %s %s %s / 比べ方 %s / 予測 %s / 実測 %s"
              % (r[u"doc"], r[u"行"], r[u"主張 id"], r[u"比べ方"],
                 r[u"予測した値"], r[u"実測の参照先"]))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
