# -*- coding: utf-8 -*-
"""便 TR8: 台帳の読みに足す 2 つの止め(封 §2)。TR2 の ledger_tr2 を変えずに上に足す。AI を使わない。

- S5 同じ見出しの列: 使う列の見出しが、使う表の列の見出しの行に 2 つ以上在れば止める(どちらの列か決まらない)。
- S6 検算: 台帳を作る時の file で「合計の行 = すぐ上に続く行の和」が成り立つ所を覚え、読む時に同じ式が
  成り立たなければ止める。行の見出しの並びが同じでも、値の入れ替わった file(同じ字の 2 行の入れ替わりなど)を止める。
  覚え方: 表の値の列ごとに、上から行を見て、値の無い行(区分の見出し)か覚えた合計の行の次から、その行のすぐ上までの
  続いた 2 行以上(長い方から試す)の和と等しい値の行を合計の行とする。許す差は、和の行の数を n として (n + 1) // 2(表の単位)。
"""
import ledger_tr2 as L


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _value_cols(g, h, lc, rws):
    head = [L.text(x) for x in g[h]]
    out = []
    for j, name in enumerate(head):
        if j == lc or not name:
            continue
        nums = sum(1 for i, _, _ in rws if j < len(g[i]) and _num(g[i][j]))
        if nums * 2 >= len(rws):
            out.append((j, name))
    return out


def learn(decided, book):
    rels = []
    for s, cfg in decided["シート"].items():
        if not cfg.get("使う") or s not in book:
            continue
        lay = L.layout(book[s], cfg)
        if lay is None:
            continue
        h, lc, rws = lay
        g = book[s]
        for j, name in _value_cols(g, h, lc, rws):
            start = 0
            for n, (i, lab, k) in enumerate(rws):
                x = g[i][j] if j < len(g[i]) else None
                if not _num(x):
                    start = n + 1
                    continue
                for a in range(start, n - 1):  # 一番長い続きから試す
                    block = rws[a:n]
                    vals = [g[b][j] if j < len(g[b]) else None for b, _, _ in block]
                    if all(_num(v) for v in vals) and sum(vals) == x:
                        rels.append({"シート": s, "列": name, "合計": [lab, k], "成分": [[l2, k2] for _, l2, k2 in block]})
                        start = n + 1
                        break
    return rels


def check(decided, rels, book):
    """成り立たない式の一覧。行か列が見つからない式は見ない(様式の変化は指紋が止める)。"""
    bad = []
    for r in rels:
        s = r["シート"]
        cfg = decided["シート"].get(s)
        if not cfg or s not in book:
            continue
        lay = L.layout(book[s], cfg)
        if lay is None:
            continue
        h, lc, rws = lay
        head = [L.text(x) for x in book[s][h]]
        if head.count(r["列"]) != 1:
            continue
        j = head.index(r["列"])
        pos = {(lab, k): i for i, lab, k in rws}
        keys = [tuple(r["合計"])] + [tuple(c) for c in r["成分"]]
        if any(k not in pos for k in keys):
            continue
        vals = [book[s][pos[k]][j] if j < len(book[s][pos[k]]) else None for k in keys]
        if not all(_num(v) for v in vals):
            bad.append({"規則": "S6", "シート": s, "種類": "検算", "前": "%s = 上の %d 行の和" % (r["合計"][0], len(r["成分"])), "今": "値が無い"})
            continue
        tol = (len(r["成分"]) + 1) // 2
        if abs(sum(vals[1:]) - vals[0]) > tol:
            bad.append({"規則": "S6", "シート": s, "種類": "検算", "前": "%s = 上の %d 行の和" % (r["合計"][0], len(r["成分"])),
                        "今": "和 %s・合計の行 %s(列「%s」)" % (sum(vals[1:]), vals[0], r["列"])})
    return bad


def dup_cols(decided, book):
    bad = []
    for it in decided["項目"]:
        for c in it.get("成分") or []:
            s = c["シート"]
            cfg = decided["シート"].get(s)
            if not cfg or s not in book:
                continue
            lay = L.layout(book[s], cfg)
            if lay is None:
                continue
            head = [L.text(x) for x in book[s][lay[0]]]
            if head.count(c["列"]) > 1:
                d = {"規則": "S5", "シート": s, "種類": "同じ見出しの列", "前": c["列"], "今": "%d 本" % head.count(c["列"])}
                if d not in bad:
                    bad.append(d)
    return bad


def make(decided, book):
    """TR2 の台帳 + 検算の式。"""
    led = L.make_ledger(decided, book)
    led["検算"] = learn(decided, book)
    return led


def read(decided, led, book):
    """TR2 の read に S5・S6 を足す。"""
    r = L.read(led, book)
    if r[0] == "止める":
        return r
    extra = dup_cols(decided, book) + check(decided, led.get("検算") or [], book)
    if extra:
        return "止める", extra
    return r
