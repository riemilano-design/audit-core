# -*- coding: utf-8 -*-
"""**2 つの規則セットの「誤りを通す率」が比較可能かを機械で確かめ、揃えた分母で比べる。**

人間の指摘(2026-10-14)「P16 と P18 の**分母・誤りの種類・評価条件が比較可能である
ことが前提**です」に答えるための道具。比較の前に 3 つを機械で確かめる::

    (1) 分母   ― どちらの規則セットで「一致」と言った行を変えたか。集合として一致するか、
                  一方が他方の部分集合か。部分集合なら**共通の行だけ**で比べ、増えた行は
                  別に数える(増えた行で通した件数を隠さない)。**どちらの部分集合でもない
                  (交差するだけ)なら比べない** ― 両側に相手に無い行が在ると、どちらの率も
                  自分の母集団の一部しか見ていない。共通の行が 0 件でも比べない。
    (2) 誤りの種類 ― 同じ行に同じ変え方(V1 = 10 倍 / V2 = 末尾の桁 +1)が当たっているか。
                  当たっていなければ件数は比べられない(2026-10-14 に実測した 1 つ目の欠陥)。
    (3) 評価条件 ― 同じ書類・同じ土台の文章・**1 回の検証で 1 件だけ変える**(batch=1)か。
                  まとめて変えると書類の丸めの判定が動いて互いを汚す(3 つ目の欠陥)。

どれかが崩れていたら、**率を並べずに崩れている所を印字する**。

**形の検査は 1 か所にまとめる(``check_shape``)。** 2026-10-15 に独立監査が退化値で
**7 件**の欠陥を出した ― 行の集合が崩れた入力・``kind`` の欄が無い入力・共通 0 件での
0 除算・``doc`` の欄が無い入力・``outcome`` の欄が無い入力・空の報告が「すべて通った」と
言う・同じ ``id`` が 2 行在って**黙って嘘の率**を出す。最初の 3 件を 1 か所ずつ塞いだら
4 件目〜7 件目が別の経路で出た。**1 か所ずつ塞ぐのをやめ、報告の形を先に 1 回で検査する。**
欄の欠落・重複・空は全部ここで落ち、以降の計算は形が整っていることを前提にできる。

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

# 報告の 1 件(run)と 1 行に在るべき欄。**字で固定する。**
RUN_FIELDS = ("doc", "profile", "kind", "batch", "rows")
ROW_FIELDS = ("id", "new", "outcome")


def load(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def check_shape(report):
    """**報告の形を 1 か所で確かめる。** 問題の一覧を返す(空なら形は整っている)。

    ここで落とすもの: 報告が list でない / 報告が空 / run が辞書でない / run の欄の欠落 /
    **同じ ``(書類, 規則セット, 変え方)`` の run が 2 回** / ``rows`` が list でない /
    行が辞書でない / 行の欄の欠落 / **同じ run の中に同じ ``id`` が 2 回**。

    最後のものは、辞書に入れると後勝ちで黙って 1 件に潰れ、**件数がずれた分母で
    率が出る**(2026-10-15 の監査が実測。「黙って嘘の率を出す」型)。
    """

    problems = []
    if not isinstance(report, list):
        return ["報告が list でない(%s)" % type(report).__name__]
    if not report:
        return ["報告が空(比べる対象が無い)"]
    seen_runs = set()
    for i, run in enumerate(report):
        if not isinstance(run, dict):
            problems.append("run[%d] が辞書でない(%s)" % (i, type(run).__name__))
            continue
        for field in RUN_FIELDS:
            if field not in run:
                problems.append("run[%d]: 欄 %s が無い" % (i, field))
        # **run そのものの重複を落とす。** ``index`` は辞書に詰めるので後勝ちで黙って
        # 上書きし、**上書きされた側の結果が消えてずれた率が出る**(2026-10-15 の監査が
        # 実測した 8 件目: 真の run が 0/4 なのに、後から来た run で 1/4 = 25% になった)。
        # 行の ``id`` の重複と対になる、run の層の重複の検査。測定の出力を手で連結すると
        # 現実に起きる(この project は実際に 4 回測り直して別の file に書いている)。
        key = (run.get("doc"), run.get("profile"), run.get("kind"))
        if key in seen_runs:
            problems.append("run[%d]: (書類, 規則セット, 変え方) = %r が 2 回在る(分母がずれる)"
                            % (i, key))
        seen_runs.add(key)
        rows = run.get("rows")
        if not isinstance(rows, list):
            if "rows" in run:
                problems.append("run[%d]: rows が list でない(%s)" % (i, type(rows).__name__))
            continue
        seen = set()
        for j, row in enumerate(rows):
            if not isinstance(row, dict):
                problems.append("run[%d] の行[%d] が辞書でない" % (i, j))
                continue
            for field in ROW_FIELDS:
                if field not in row:
                    problems.append("run[%d] の行[%d]: 欄 %s が無い" % (i, j, field))
            cid = row.get("id")
            if cid in seen:
                problems.append("run[%d]: id %r が 2 回在る(分母がずれる)" % (i, cid))
            seen.add(cid)
    return problems


def index(report):
    """``(書類, 規則セット, 変え方)`` で引ける形にする。

    欠けた欄で例外を投げない(``check_shape`` が先に落とすが、落ちる道具は
    「比較できない」と言えない)。
    """

    out = {}
    for r in report:
        out[(r.get("doc"), r.get("profile"), r.get("kind"))] = r
    return out


def docs_of(report):
    """報告に在る書類の一覧。欠けた欄で例外を投げない。"""

    return sorted(set(r.get("doc") for r in report if isinstance(r, dict)))


def rows_of(by, doc, profile, kind):
    return {x.get("id"): x for x in by[(doc, profile, kind)].get("rows", [])}


def check_comparable(by, docs, a, b):
    """``(ok, 問題の一覧, 内訳)``。問題が 1 件でもあれば率を並べない。

    **形の検査(``check_shape``)を先に通した報告を前提にする。**
    """

    problems, detail = [], {}
    if a == b:
        problems.append("同じ規則セットを比べようとしている(%s と %s)" % (a, b))
    if not docs:
        problems.append("書類が 0 件(比べる対象が無い)")
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
            for cid in sorted(common, key=lambda v: (v is None, v)):
                if cid not in ra or cid not in rb:
                    problems.append("%s %s %s: %s にこの行が無い"
                                    % (doc, cid, kind, a if cid not in ra else b))
                    continue
                if ra[cid].get("new") != rb[cid].get("new"):
                    problems.append("%s %s: 変えた字が違う(%r != %r)"
                                    % (doc, cid, ra[cid].get("new"), rb[cid].get("new")))
        # (1) の続き: **どちらの部分集合でもない場合を落とす。**
        if not (ia <= ib or ib <= ia):
            problems.append("%s: 行の集合がどちらの部分集合でもない(%s だけ %d 行 / %s だけ %d 行)"
                            % (doc, a, len(ia - ib), b, len(ib - ia)))
        # **共通の行が 0 件なら率を出す分母が無い。**
        if not common:
            problems.append("%s: 共通の行が 0 件(比べる分母が無い)" % doc)
        detail[doc] = {"rows_a": len(ia), "rows_b": len(ib), "common": len(common),
                       "a_subset_of_b": ia <= ib, "b_subset_of_a": ib <= ia}
    return (not problems), problems, detail


def analyze(report, a="P16", b="P18"):
    """**形 → 構造の順に 1 本で検査する入口。** ``(ok, 問題, 内訳, 書類, 索引)``。"""

    shape = check_shape(report)
    if shape:
        return False, shape, {}, [], {}
    docs = docs_of(report)
    by = index(report)
    ok, problems, detail = check_comparable(by, docs, a, b)
    return ok, problems, detail, docs, by


def pct(n, d):
    """``n/d`` の百分率。``d`` が 0 なら ``None``(**0 除算で落ちない**)。"""

    if not d:
        return None
    return 100.0 * n / d


def fmt_rate(n, d):
    r = pct(n, d)
    return "%d/%d = ―" % (n, d) if r is None else "%d/%d = %.1f%%" % (n, d, r)


def tally(by, docs, a, b, detail):
    acc = {"common_n": 0, "a_all_n": 0, "b_all_n": 0,
           "a_common": 0, "b_common": 0, "a_all": 0, "b_all": 0, "b_extra_n": 0, "b_extra": 0}
    for doc in docs:
        ia = set(rows_of(by, doc, a, "V1"))
        ib = set(rows_of(by, doc, b, "V1"))
        common = ia & ib
        extra = ib - ia
        acc["common_n"] += len(common) * len(KINDS)
        acc["a_all_n"] += len(ia) * len(KINDS)
        acc["b_all_n"] += len(ib) * len(KINDS)
        acc["b_extra_n"] += len(extra) * len(KINDS)
        for kind in KINDS:
            for cid, x in rows_of(by, doc, a, kind).items():
                if x.get("outcome") == "PASSED":
                    acc["a_all"] += 1
                    if cid in common:
                        acc["a_common"] += 1
            for cid, x in rows_of(by, doc, b, kind).items():
                if x.get("outcome") == "PASSED":
                    acc["b_all"] += 1
                    if cid in common:
                        acc["b_common"] += 1
                    if cid in extra:
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
    ok, problems, detail, docs, by = analyze(rep, a, b)
    print("入力: %s" % path)
    print("書類: %s" % ", ".join(str(d) for d in docs))
    if not ok:
        print("**比較できない。** 率は並べない。崩れている所:")
        for p in problems:
            print("  -", p)
        return 1
    acc = tally(by, docs, a, b, detail)
    print("比較可能の確認: 報告の形・分母の集合・変えた字・batch=1 すべて通った")
    for doc in docs:
        d = detail[doc]
        print("  %s: %s %d 行 / %s %d 行 / 共通 %d 行 (%s ⊆ %s: %s)"
              % (doc, a, d["rows_a"], b, d["rows_b"], d["common"], a, b, d["a_subset_of_b"]))
    print()
    print("**分母を揃えた比較**(共通の行 × %d 通りの変え方 = %d 回):"
          % (len(KINDS), acc["common_n"]))
    print("  %s %s" % (a, fmt_rate(acc["a_common"], acc["common_n"])))
    print("  %s %s" % (b, fmt_rate(acc["b_common"], acc["common_n"])))
    print("参考(それぞれの全部の行): %s %d/%d / %s %d/%d"
          % (a, acc["a_all"], acc["a_all_n"], b, acc["b_all"], acc["b_all_n"]))
    print("**%s で新たに「一致」と言うようになった行**(%d 回)での通過: %d 件"
          % (b, acc["b_extra_n"], acc["b_extra"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
