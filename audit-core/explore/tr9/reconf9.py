# -*- coding: utf-8 -*-
"""便 TR9: 確定し直しの 2 つの直し(封 §2)。TR6・TR8 の file を変えずに上に足す。AI を使わない。

- diff9: TR8 の diff8 に、行の変化で「確定した台帳で使わない行だったか」を足す。
- 決め: 同じ見出しの列の追加に {"列の何番目": k}(その見出しの列は k 本目を読む)か {"保留": true}(決めない。止めたまま)。
- screen9: 使わない行だった時はそう書く。同じ見出しの列の追加では、列の見出しの行より上の行(表の頭)も列に揃えて出す。
"""
import copy
import html

import ledger_tr2 as L
import reconf8 as R8
import reconf_tr6 as R


def diff9(decided, ledger, book):
    changes = R8.diff8(decided, ledger, book)
    used = {(c["シート"], c["行"]) for it in decided["項目"] for c in it.get("成分") or []}
    unused = {(u.get("シート"), u.get("行")) for u in decided.get("使わない行") or []}
    for ch in changes:
        if ch["種類"] in ("行の字の変更", "行の順の変更", "行の削除"):
            ch["使わない行だった"] = (ch["シート"], ch["前"]) in unused and (ch["シート"], ch["前"]) not in used
    return changes


def apply(decided, changes, decisions):
    """同じ見出しの列の追加の決めを当て、ほかは TR6 の apply。保留・決めの漏れは「当てられなかった所」に入る。"""
    byn = {ch["番号"]: ch for ch in changes}
    rest, mine = {}, {}
    for num, dec in decisions.items():
        (mine if (byn.get(num) or {}).get("種類") == "同じ見出しの列の追加" else rest)[num] = dec
    d, bad = R.apply(decided, [ch for ch in changes if ch["種類"] != "同じ見出しの列の追加"], rest)
    d = copy.deepcopy(d)
    for ch in changes:
        if ch["種類"] != "同じ見出しの列の追加":
            continue
        dec = mine.get(ch["番号"])
        k = dec.get("列の何番目") if isinstance(dec, dict) else None
        if isinstance(k, int) and not isinstance(k, bool) and k >= 1:
            for it in d["項目"]:
                for c in it.get("成分") or []:
                    if c["シート"] == ch["シート"] and c["列"] == ch["今"]:
                        c["列の何番目"] = k
        elif isinstance(dec, dict) and dec.get("保留"):
            bad.append((ch["番号"], "保留"))
        else:
            bad.append((ch["番号"], "決めが無いか形が合わない"))
    return d, bad


def note9(ch, base=R8.note):
    if ch.get("使わない行だった"):
        return "この行は、確定した台帳で使わない行でした(どの項目にも使っていません)"
    if ch["種類"] == "同じ見出しの列の追加":
        return ("同じ見出しの列が 2 本になりました。どちらを読むか機械は決めません。読む列が分かれば「列の何番目」(左から何本目か)を、"
                "分からなければ「保留」を選んでください")
    return base(ch)


def table9(decided, book, sheet, rename, label=None, k=2, with_head=False, base=R8._table):
    t = base(decided, book, sheet, rename, label, k)
    if not with_head or not t:
        return t
    s1 = rename.get(sheet, sheet)
    h = L.layout(book[s1], decided["シート"][sheet])[0]
    top = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % html.escape(L.text(x)) for x in row) for row in book[s1][:h] if row)
    return t.replace("<table class=ctx>", "<table class=ctx>" + top, 1)


def screen9(n, sk, changes, decided, book, plan_read, early):
    """TR8 の screen8 を、note と表だけ差し替えて使う。"""
    old_note, old_table = R8.note, R8._table
    dupe = {ch["シート"] for ch in changes if ch["種類"] == "同じ見出しの列の追加"}
    R8.note = note9
    R8._table = lambda d, b, s, rn, label=None, k=2: table9(d, b, s, rn, label, k, with_head=(s in dupe and label is None))
    try:
        out = R8.screen8(n, sk, changes, decided, book, plan_read, early)
    finally:
        R8.note, R8._table = old_note, old_table
    return out
