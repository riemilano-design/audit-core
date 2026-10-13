# -*- coding: utf-8 -*-
"""**2 つの規則セットの「誤りを通す率」が比較可能かを機械で確かめ、揃えた分母で比べる。**

人間の指摘(2026-10-14)「P16 と P18 の**分母・誤りの種類・評価条件が比較可能である
ことが前提**です」に答えるための道具。比較の前に 3 つを機械で確かめる::

    (1) 分母   ― どちらの規則セットで「一致」と言った行を変えたか。集合として一致するか、
                  一方が他方の部分集合か。部分集合なら**共通の行だけ**で比べ、増えた行は
                  別に数える(増えた行で通した件数を隠さない)。
    (2) 誤りの種類 ― 同じ行に同じ変え方(V1 = 10 倍 / V2 = 末尾の桁 +1)が当たっているか。
                  当たっていなければ件数は比べられない(2026-10-14 に実測した 1 つ目の欠陥)。
    (3) 評価条件 ― 同じ書類・同じ土台の文章・**1 回の検証で 1 件だけ変える**(batch=1)か。
                  まとめて変えると書類の丸めの判定が動いて互いを汚す(3 つ目の欠陥)。

どれかが崩れていたら、**率を並べずに崩れている所を印字する**。

使い方::  python3 -B measure/false_pass_compare_2026-10-15.py [--in <json>] [--a P16] [--b P18]
入力は ``measure/false_pass_2026-10-14.py --batch 1 --kinds V1,V2`` の出力。通信しない。
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_IN = os.path.join(ROOT, "fixtures", "xbrl", "p17", "false_pass_2026-10-14_batch1.json")
KINDS = ("V1", "V2")


def load(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def index(report):
    """``(書類, 規則セット, 変え方)`` で引ける形にする。

    **欠けた欄で例外を投げない。**古い出力(``--kinds`` を足す前の版)には ``kind`` が
    無い。例外を投げる道具は「比較できない」と言えず、何も印字せずに落ちる
    (2026-10-15 に実測。同じ型を上の層で直した直後に、ここで 2 か所目が出た)。
    欄が欠けている run は ``kind=None`` で入れ、検査が「run が無い」として落とす。
    """

    out = {}
    for r in report:
        out[(r.get("doc"), r.get("profile"), r.get("kind"))] = r
    return out


def rows_of(by, doc, profile, kind):
    return {x["id"]: x for x in by[(doc, profile, kind)]["rows"]}


def check_comparable(by, docs, a, b):
    """``(ok, 問題の一覧, 内訳)``。問題が 1 件でもあれば率を並べない。"""

    problems, detail = [], {}
    for doc in docs:
        for kind in KINDS:
            for pn in (a, b):
                if (doc, pn, kind) not in by:
                    problems.append("%s %s %s の run が無い" % (doc, pn, kind))
    if problems:
        return False, problems, detail

    for doc in docs:
        ia = set(rows_of(by, doc, a, "V1"))
        ib = set(rows_of(by, doc, b, "V1"))
        for kind in KINDS:
            # (1) 分母: V1 と V2 が同じ行に当たっているか(両方当てた版か)
            if set(rows_of(by, doc, a, kind)) != ia:
                problems.append("%s %s: V1 と %s で行が違う(両方当てた版でない)" % (doc, a, kind))
            if set(rows_of(by, doc, b, kind)) != ib:
                problems.append("%s %s: V1 と %s で行が違う(両方当てた版でない)" % (doc, b, kind))
            # (3) 評価条件: batch=1
            for pn in (a, b):
                if by[(doc, pn, kind)].get("batch") != 1:
                    problems.append("%s %s %s: batch が 1 でない(%r)"
                                    % (doc, pn, kind, by[(doc, pn, kind)].get("batch")))
        # (2) 誤りの種類: 共通の行で、同じ id に同じ字の変え方が当たっているか
        common = ia & ib
        for kind in KINDS:
            ra, rb = rows_of(by, doc, a, kind), rows_of(by, doc, b, kind)
            for cid in sorted(common):
                # 上の (1) で行の集合の崩れは既に記録済み。ここで落ちない
                # (崩れた入力で例外を投げる道具は、崩れを「比較できない」と言えない)。
                if cid not in ra or cid not in rb:
                    problems.append("%s %s %s: %s にこの行が無い"
                                    % (doc, cid, kind, a if cid not in ra else b))
                    continue
                if ra[cid].get("new") != rb[cid].get("new"):
                    problems.append("%s %s: 変えた字が違う(%r != %r)"
                                    % (doc, cid, ra[cid].get("new"), rb[cid].get("new")))
        detail[doc] = {"rows_a": len(ia), "rows_b": len(ib), "common": len(common),
                       "a_subset_of_b": ia <= ib, "b_subset_of_a": ib <= ia}
    return (not problems), problems, detail


def tally(by, docs, a, b, detail):
    acc = {"common_n": 0, "a_all_n": 0, "b_all_n": 0,
           "a_common": 0, "b_common": 0, "a_all": 0, "b_all": 0, "b_extra_n": 0, "b_extra": 0}
    for doc in docs:
        ia = set(rows_of(by, doc, a, "V1"))
        ib = set(rows_of(by, doc, b, "V1"))
        common = ia & ib
        acc["common_n"] += len(common) * len(KINDS)
        acc["a_all_n"] += len(ia) * len(KINDS)
        acc["b_all_n"] += len(ib) * len(KINDS)
        acc["b_extra_n"] += len(ib - ia) * len(KINDS)
        for kind in KINDS:
            for cid, x in rows_of(by, doc, a, kind).items():
                if x["outcome"] == "PASSED":
                    acc["a_all"] += 1
                    if cid in common:
                        acc["a_common"] += 1
            for cid, x in rows_of(by, doc, b, kind).items():
                if x["outcome"] == "PASSED":
                    acc["b_all"] += 1
                    if cid in common:
                        acc["b_common"] += 1
                    if cid in (ib - ia):
                        acc["b_extra"] += 1
    return acc


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    path, a, b = DEFAULT_IN, "P16", "P18"
    while argv:
        if argv[0] == "--in":
            path = argv[1]; argv = argv[2:]
        elif argv[0] == "--a":
            a = argv[1]; argv = argv[2:]
        elif argv[0] == "--b":
            b = argv[1]; argv = argv[2:]
        else:
            raise SystemExit("unknown arg %r" % argv[0])
    rep = load(path)
    by = index(rep)
    docs = sorted(set(r["doc"] for r in rep))
    ok, problems, detail = check_comparable(by, docs, a, b)
    print("入力: %s" % path)
    print("書類: %s" % ", ".join(docs))
    if not ok:
        print("**比較できない。** 率は並べない。崩れている所:")
        for p in problems:
            print("  -", p)
        return 1
    acc = tally(by, docs, a, b, detail)
    print("比較可能の確認: 分母の集合・変えた字・batch=1 すべて通った")
    for doc in docs:
        d = detail[doc]
        print("  %s: %s %d 行 / %s %d 行 / 共通 %d 行 (%s ⊆ %s: %s)"
              % (doc, a, d["rows_a"], b, d["rows_b"], d["common"], a, b, d["a_subset_of_b"]))
    print()
    print("**分母を揃えた比較**(共通の行 × %d 通りの変え方 = %d 回):"
          % (len(KINDS), acc["common_n"]))
    print("  %s %d/%d = %.1f%%" % (a, acc["a_common"], acc["common_n"],
                                   100.0 * acc["a_common"] / acc["common_n"]))
    print("  %s %d/%d = %.1f%%" % (b, acc["b_common"], acc["common_n"],
                                   100.0 * acc["b_common"] / acc["common_n"]))
    print("参考(それぞれの全部の行): %s %d/%d / %s %d/%d"
          % (a, acc["a_all"], acc["a_all_n"], b, acc["b_all"], acc["b_all_n"]))
    print("**%s で新たに「一致」と言うようになった行**(%d 回)での通過: %d 件"
          % (b, acc["b_extra_n"], acc["b_extra"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
