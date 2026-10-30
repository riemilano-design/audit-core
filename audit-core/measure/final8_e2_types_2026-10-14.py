# -*- coding: utf-8 -*-
"""最終評価用 8 書類の E2(誤った根拠で通した行)を型で数える。

**独立監査(2026-10-14)の指摘で後から commit した。** 結果文書 §1-2 の内訳
(D 19 / E 7 / A 6 / B 4 / F 2、合計 38)は、当初**使い捨ての inline script** で出したため
repo に残っておらず、監査は件数に合う規則を試行錯誤で逆算するしかなかった。
**文書の数は commit された code から再現できなければならない**ので、当時の分類をそのまま写す。

分類は合否には使わない(R-S1/2/3 は L・G・E1'・E2・E3 の総数だけで決まる)。参考情報である。

判定の順(**この順に最初に当たった型を採る**):
  A 同値類 v0 では一致   canon した要素名の集合が同じ かつ context の集合が同じ
  B member が違う        要素名の集合が同じ かつ context の member の集合が違う
  C 期間が違う           要素名の集合が同じ かつ context の集合が違う
  D 要素が違う           context の集合が同じ かつ要素名の集合が違う
  E 結んだ fact の数が違う
  F その他               要素も context も違う
"""
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import grounds_eval as GE  # noqa: E402

BASE = os.environ.get("FINAL8_BASE") or os.path.join(ROOT, "fixtures", "xbrl", "final8")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
PROFILE = "P16"

KINDS = ("A 同値類 v0 では一致(要素名の別名)",
         "B 要素は同じ・member が違う(対象の取り違え)",
         "C 要素は同じ・期間が違う",
         "D 期間は同じ・要素が違う",
         "E 結んだ fact の数が違う(形の取り違え)",
         "F その他(要素も期間も違う)")


def members(contexts, cid):
    c = contexts.get(cid) or {}
    return frozenset(m.split(":")[-1] for m in (c.get("members") or []))


def classify(row, contexts):
    """E2 の 1 行を 1 つの型に割り当てる(上の順で最初に当たったもの)。"""
    ea = {e for e, _ in row["arm"]}
    el = {e for e, _ in row["label"]}
    ca = {c for _, c in row["arm"]}
    cl = {c for _, c in row["label"]}
    ma = {members(contexts, c) for _, c in row["arm"]}
    ml = {members(contexts, c) for _, c in row["label"]}
    if {GE.canon(e) for e in ea} == {GE.canon(e) for e in el} and ca == cl:
        return KINDS[0]
    if ea == el and ma != ml:
        return KINDS[1]
    if ea == el and ca != cl:
        return KINDS[2]
    if ea != el and ca == cl:
        return KINDS[3]
    if len(row["arm"]) != len(row["label"]):
        return KINDS[4]
    return KINDS[5]


def main():
    docs = json.load(io.open(SPLIT, encoding="utf-8"))["final_eval_sealed"]
    labels = GE.load_labels(os.path.join(BASE, "labels_final8_2026-10-14.json"))
    dump = {}
    for d in docs:
        dump.update(json.load(io.open(os.path.join(BASE, "commander_only", "dump_%s_%s.json" % (PROFILE, d)),
                                      encoding="utf-8")))
    ctx = {d: json.load(io.open(os.path.join(BASE, "seat", "contexts_%s.json" % d), encoding="utf-8")) for d in docs}

    counts = collections.Counter()
    per_doc = collections.Counter()
    rows_out = []
    for r in GE.score(dump, labels):
        if r["state"] != "GROUNDED" or r["strict"]:
            continue
        d = r["id"].split(":", 1)[0]
        k = classify(r, ctx[d])
        counts[k] += 1
        per_doc[(d, k[0])] += 1
        rows_out.append({"id": r["id"], "kind": k[0], "arm": r["arm"], "label": r["label"],
                         "direction": r["direction"]})
    total = sum(counts.values())
    print("E2 合計 %d 件" % total)
    for k in KINDS:
        print("  %-42s %2d" % (k, counts[k]))
    print()
    print("書類別:")
    for (d, k), n in sorted(per_doc.items()):
        print("  %s %s %d" % (d, k, n))
    out = {"profile": PROFILE, "total": total,
           "counts": {k: counts[k] for k in KINDS},
           "per_doc": {"%s|%s" % kk: vv for kk, vv in sorted(per_doc.items())},
           "rows": rows_out}
    p = os.path.join(BASE, "e2_types_2026-10-14.json")
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\n->", p)


if __name__ == "__main__":
    main()
