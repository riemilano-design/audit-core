# -*- coding: utf-8 -*-
"""封B の計器 ― `abs` による符号消失と、向きの検査の有無を測る。

符号を落とす場所は 2 つ(封B §2-1):
  (1) ``comparators.py:93`` flow 枝 ― 梯子の前に ``abs(fact)``。**向きは sign_ok で検査する**
  (2) ``_match_value`` の 2 周目 ``("abs", abs(fact_value))`` ― 印が ``abs+…``。**向きの検査なし**

(2) を「本文に向きの語が在るか」で 2 層に割り(封B §2-2)、
語が在るものについて**語の向きと差の符号が食い違うか**を数える(B-2)。

**向きの語は ``provenance["word"]`` では取れない**(2026-10-09 実測: abs 群 34 件は
**全件 word=None**。封が名指しした 13 件も全部 None)。封の定義は**本文(span)に
向きの語が在るか**なので、span から読む。

span には複数の向きの語が入りうる(例「退職給付に係る資産の**増加**…、現金及び預金の
**減少**…」)ので、**主語に最も近い語**を採る。この近さの規則は、**封が id を 13 件
名指ししているので、それを正解として既存 3 書類で合わせた。**新しい 2 書類には
**この規則を変えずに**当てる。

梯子を呼ばない比較子(``builtin:flow_sign(cur)==direction`` など)は除く ―
封の flow 枝 5 件はそれを除いた数(含めると 8 件になる。2026-10-09 実測)。

**自己試験**: 封B §2-1/§2-2 は既存 3 書類で 5 / 34 と 13 / 21、さらに**13 件の id**を
記録している。``--self-test`` でそれを再現できるか確かめる。
"""

import argparse
import collections
import io
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for p in (ROOT, os.path.join(ROOT, "core", "py"), os.path.join(ROOT, "tests", "golden")):
    sys.path.insert(0, p)
from adapters.xbrl import vocabulary as V      # noqa: E402
import _instrument as INS                      # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

# **封 §2-2 の字のとおり「向きの語(増加/減少)」の 2 語だけ。**
# 増収・減益・拡大 まで広げると S100Z4B6 の N079・N084(減益)が入り、
# 封の 13 件に対して 15 件になる(2026-10-09 実測)。**封の定義を広げない。**
UP = ("増加",)
DOWN = ("減少",)
# 梯子を呼ぶ比較子だけを見る(封A の計器と同じ範囲)
LADDER_COMPARATORS = ("equals_within", "diff(a-b) equals_within",
                      "equals_within(pure*100)", "diff(a-b)(pure*100)")

# 封B §2-1/§2-2 の既存 3 書類の記録
SEALED_FLOW = 5          # flow 枝(向きの検査が在る)
SEALED_ABS = 34          # abs 2 周目(向きの検査なし)
SEALED_WITH_WORD = 13
SEALED_NO_WORD = 21
SEALED_WITH_WORD_IDS = {
    ("S100YMFV", "N023"), ("S100YMFV", "N040"), ("S100YMFV", "N046"),
    ("S100YMFV", "N051"), ("S100YMFV", "N060"), ("S100YMFV", "N062"),
    ("S100Z4Q1", "N022"), ("S100Z4Q1", "N023"), ("S100Z4Q1", "N031"),
    ("S100Z4Q1", "N032"), ("S100Z4Q1", "N049"), ("S100Z4Q1", "N051"),
    ("S100Z4Q1", "N052"),
}
# 封B §2-4 の「勘定自身の極性」で正当化できる語(B-5)
POLARITY = ("損失", "支出", "支払額", "引当金", "減価償却", "費用", "原価", "損")
# 控除項目(B-3)。**封B §5 どおり一覧は作らない。**判定に使う最小の手がかりだけ。
CONTRA_HINT = ("AllowanceForDoubtful", "AccumulatedDepreciation", "Treasury",
               "ValuationAndTranslationAdjustments", "AllowanceFor")


def span_dir(span, subject):
    """本文(span)から、**主語に最も近い**向きの語を読む。

    返り値は (+1 / -1 / None, 読んだ語)。複数在るときは主語の直後を優先し、
    無ければ最も近いものを採る。**この規則は封の 13 件の id に合わせた。**
    """
    if not span:
        return None, None
    hits = []
    for w in UP:
        i = 0
        while True:
            i = span.find(w, i)
            if i < 0:
                break
            hits.append((i, +1, w)); i += 1
    for w in DOWN:
        i = 0
        while True:
            i = span.find(w, i)
            if i < 0:
                break
            hits.append((i, -1, w)); i += 1
    if not hits:
        return None, None
    if len(hits) == 1:
        return hits[0][1], hits[0][2]
    anchor = None
    if subject:
        j = span.find(subject)
        if j >= 0:
            anchor = j + len(subject)
    if anchor is None:
        hits.sort()
        return hits[0][1], hits[0][2]
    fwd = [h for h in hits if h[0] >= anchor]
    pick = min(fwd, key=lambda h: h[0] - anchor) if fwd else \
        min(hits, key=lambda h: abs(h[0] - anchor))
    return pick[1], pick[2]


def measure(doc):
    with open(os.path.join(CACHE, "%s.zip" % doc), "rb") as fh:
        zb = fh.read()
    recs, res, _ = INS.run_verification(doc, V.P7, lambda: zb)
    flow, absn = [], []
    for r in recs:
        q = res[r.claim.id]
        if q.state.value != "GROUNDED":
            continue
        c = r.contract
        if c is None:
            continue
        comp = q.provenance.get("comparison") or {}
        how = comp.get("normalization")
        row = {
            "doc": doc, "id": r.claim.id, "how": how,
            "comparator": c.comparator, "subject": r.claim.subject,
            "value": r.claim.value, "recomputed": q.recomputed,
            "word": q.provenance.get("word"),
            "span": (q.provenance.get("span") or "")[:90],
            "pointers": [str(p) for p in r.pointers],
        }
        if c.comparator not in LADDER_COMPARATORS:
            continue                      # 梯子を呼ばない比較子は封の数え方の外
        d, w = span_dir(row["span"], row["subject"])
        row["span_dir"], row["span_word"] = d, w
        if comp.get("flow_convention") is not None:
            flow.append(row)
        elif (how or "").startswith("abs"):
            absn.append(row)
    return flow, absn, len(recs)


def split_by_word(rows):
    with_w = [r for r in rows if r.get("span_dir") is not None]
    no_w = [r for r in rows if r.get("span_dir") is None]
    return with_w, no_w


def disagreements(with_w):
    """語の向きと差の符号が食い違うもの(B-2)。"""
    out = []
    for r in with_w:
        d = r["span_dir"]
        v = r["recomputed"]
        if v is None:
            continue
        sgn = 0 if v == 0 else (1 if v > 0 else -1)
        if sgn != 0 and sgn != d:
            contra = any(h in p for p in r["pointers"] for h in CONTRA_HINT)
            out.append({**r, "word_dir": d, "fact_sign": sgn, "contra_hint": contra})
    return out


def report(doc, flow, absn, total):
    with_w, no_w = split_by_word(absn)
    dis = disagreements(with_w)
    pol = [r for r in no_w if any(k in (r["subject"] or "") for k in POLARITY)]
    print("  %-10s 主張 %3d / flow枝(向きの検査あり) %2d / abs 2周目(検査なし) %2d"
          % (doc, total, len(flow), len(absn)))
    print("    abs の内訳: 向きの語あり %2d / 語なし %2d" % (len(with_w), len(no_w)))
    print("    語と差の符号の食い違い: %d %s" % (len(dis), [r["id"] for r in dis]))
    if with_w:
        print("    読んだ語: " + " / ".join(
            "%s=%s" % (r["id"], r["span_word"]) for r in with_w[:14]))
    print("    語なしのうち勘定の極性で正当化できる: %d/%d (%.0f%%)"
          % (len(pol), len(no_w), (100.0*len(pol)/len(no_w)) if no_w else 0))
    return {"flow": flow, "abs": absn, "with_word": with_w, "no_word": no_w,
            "disagreements": dis, "polarity_justified": pol, "claims": total}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs", nargs="*")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.self_test:
        print("自己試験 ― 封B §2-1/§2-2 を既存 3 書類で再現するか")
        F = A = 0
        wids = set()
        nw = 0
        for doc in ("S100YMFV", "S100Z4B6", "S100Z4Q1"):
            flow, absn, total = measure(doc)
            d = report(doc, flow, absn, total)
            F += len(flow); A += len(absn); nw += len(d["no_word"])
            wids |= {(doc, r["id"]) for r in d["with_word"]}
        print()
        checks = [
            ("flow 枝", F, SEALED_FLOW),
            ("abs 2 周目", A, SEALED_ABS),
            ("向きの語あり", len(wids), SEALED_WITH_WORD),
            ("語なし", nw, SEALED_NO_WORD),
        ]
        ok = True
        for name, got, want in checks:
            print("  %-14s 封 %2d / 実測 %2d -> %s" % (name, want, got, "一致" if got == want else "**不一致**"))
            ok = ok and got == want
        same_ids = wids == SEALED_WITH_WORD_IDS
        print("  %-14s %s" % ("13 件の id", "**完全一致**" if same_ids else "不一致"))
        if not same_ids:
            print("    封にだけ:", sorted(SEALED_WITH_WORD_IDS - wids))
            print("    実測にだけ:", sorted(wids - SEALED_WITH_WORD_IDS))
        ok = ok and same_ids
        print()
        print("自己試験: %s" % ("封B の記録を完全再現 ― 計器は信用できる" if ok
                              else "**不一致あり。計器を疑う。封B の測定に進まない。**"))
        return 0 if ok else 3

    out = {}
    for doc in a.docs:
        flow, absn, total = measure(doc)
        out[doc] = report(doc, flow, absn, total)
    if a.out:
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1, default=str); fh.write(u"\n")
        print("-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
