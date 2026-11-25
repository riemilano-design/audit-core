# -*- coding: utf-8 -*-
"""便 TR9: 台帳の読みの 2 つの直し(封 §2)。TR2 の ledger_tr2 と TR8 の ledger8 を変えずに上に足す。AI を使わない。

- 列の何番目: 成分に「列の何番目」(同じ見出しの列の何本目か)を書けるようにする。書いてあればその列を読む。
  使う列の見出しが 2 本以上在るのに何番目が無ければ止める(S5′)。何番目が見出しの本数を超えても止める。
- 検算の覚え方を固くする(S6′): 式は、表の全部の値の列で同時に成り立つ時だけ覚える(TR8 は列ごとに覚えた)。
  値の列が 1 本だけの表は、その列で覚える。照らす時は、見出しが 1 本だけの値の列で照らす。
"""
import ledger_tr2 as L
import ledger8 as G8

_num = G8._num


def col_index(head, name, nth=None):
    idx = [j for j, x in enumerate(head) if x == name]
    if not idx:
        return None
    if nth is None:
        return idx[0] if len(idx) == 1 else None
    return idx[nth - 1] if 1 <= nth <= len(idx) else None


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
        cols = G8._value_cols(g, h, lc, rws)
        if not cols:
            continue
        val = lambda i, j: g[i][j] if j < len(g[i]) else None  # noqa: E731
        start = 0
        for n, (i, lab, k) in enumerate(rws):
            if not all(_num(val(i, j)) for j, _ in cols):
                start = n + 1
                continue
            for a in range(start, n - 1):
                block = rws[a:n]
                if all(all(_num(val(b, j)) for b, _, _ in block) and sum(val(b, j) for b, _, _ in block) == val(i, j) for j, _ in cols):
                    rels.append({"シート": s, "列": [name for _, name in cols], "合計": [lab, k], "成分": [[l2, k2] for _, l2, k2 in block]})
                    start = n + 1
                    break
    return rels


def check(decided, rels, book):
    bad = []
    for r in rels:
        for name in r["列"]:
            bad += G8.check(decided, [dict(r, 列=name)], book)
    return bad


def ordinal_stops(decided, book):
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
            if col_index(head, c["列"], c.get("列の何番目")) is None:
                d = {"規則": "S5", "シート": s, "種類": "同じ見出しの列", "前": c["列"],
                     "今": "%d 本・何番目 %s" % (head.count(c["列"]), c.get("列の何番目") or "なし")}
                if d not in bad:
                    bad.append(d)
    return bad


def values(decided, book):
    vals = {}
    for it in decided["項目"]:
        key = "%s@%s" % (it["項目"], it["期"])
        total = 0
        for c in it.get("成分") or []:
            s = c["シート"]
            cfg = decided["シート"][s]
            lay = L.layout(book[s], cfg)
            head = [L.text(x) for x in book[s][lay[0]]]
            r = next(i for i, lab, k in lay[2] if (lab, k) == (c["行"], int(c.get("何番目") or 1)))
            j = col_index(head, c["列"], c.get("列の何番目"))
            x = book[s][r][j] if j < len(book[s][r]) else None
            if not _num(x):
                return None, [{"規則": "S4", "シート": s, "種類": "升が数でない", "前": "数", "今": L.text(x), "項目": key}]
            total += int(round(x * L.UNIT.get(cfg.get("単位"), 1))) * int(c.get("符号") or 1)
        vals[key] = total
    return vals, []


def make(decided, book):
    led = L.make_ledger(decided, book)
    led["検算"] = learn(decided, book)
    return led


def read(decided, led, book):
    """S1〜S3 は TR2 の read。値は列の何番目を見て読み直す。S5′・S6′ を足す。"""
    r = L.read(led, book)
    if r[0] == "止める" and any(d["規則"] != "S4" for d in r[1]):
        return r
    extra = ordinal_stops(decided, book) + check(decided, led.get("検算") or [], book)
    if extra:
        return "止める", extra
    vals, bad = values(decided, book)
    if bad:
        return "止める", bad
    return "読めた", vals, None
