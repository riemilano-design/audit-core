# -*- coding: utf-8 -*-
"""便 TR7: 部分の読み(封 §2)。止めた時も、変わった所の影響しない項目だけは先に読む。AI を使わない。

待たせる規則(1 つでも当たる項目は読まない):
  P1 行の中身の変化(行の追加・削除・字の変更)が在るシートの項目は全部待つ。足した行や字の変わった行は、どの項目に
     入るかを人が決めるまで分からない(単独の行で読む項目も、合計の行で読む項目も)。
  P2 単位の変更・頭の行の字の変更・シートの名の変更・シートが無い・列の見出しが見つからないシートの項目は全部待つ。
  P3 列の字の変更・列の削除: その列を使う項目は待つ。
  P4 行の順の変更: そのシートに同じ字の行が 2 つ以上在れば(何番目が変わりうる。並びの差は、動いた行として重なりの
     行でなく間の行を挙げることがある)、そのシートの項目は全部待つ。
  列の追加・列の順の変更・使わないシートの増減だけなら待たせない。
読む: 待たない項目は、確定の台帳の成分のまま今回の file の升から読む(TR2 の layout で行の位置を引き直す)。
"""
import ledger_tr2 as L


def waiting(decided, changes, book):
    """待つ項目@期 の集まり。"""
    sheet_of = {}
    for it in decided["項目"]:
        key = "%s@%s" % (it["項目"], it["期"])
        for c in it.get("成分") or []:
            sheet_of.setdefault(key, set()).add(c["シート"])
    wait_sheets, wait_items = set(), set()
    for ch in changes:
        k, s = ch["種類"], ch["シート"]
        if k in ("行の追加", "行の削除", "行の字の変更", "単位の変更", "頭の行の字の変更", "シートの名の変更", "シートが無い",
                 "列の見出しが見つからない"):
            wait_sheets.add(s)
        elif k in ("列の字の変更", "列の削除"):
            for it in decided["項目"]:
                if any(c["シート"] == s and c["列"] == ch["前"] for c in it.get("成分") or []):
                    wait_items.add("%s@%s" % (it["項目"], it["期"]))
        elif k == "行の順の変更":
            cfg = decided["シート"].get(s)
            lay = L.layout(book[s], cfg) if (cfg and s in book) else None
            labs = [lab for _, lab, _ in lay[2]] if lay else []
            if lay is None or len(labs) != len(set(labs)):
                wait_sheets.add(s)
    for key, ss in sheet_of.items():
        if ss & wait_sheets:
            wait_items.add(key)
    return wait_items


def read_some(decided, book, keys):
    """keys の項目だけを台帳の成分のまま読む。読めない項目は除く。"""
    out = {}
    for it in decided["項目"]:
        key = "%s@%s" % (it["項目"], it["期"])
        if key not in keys:
            continue
        total, ok = 0, True
        for c in it.get("成分") or []:
            s = c["シート"]
            cfg = decided["シート"].get(s)
            lay = L.layout(book[s], cfg) if (cfg and s in book) else None
            if lay is None:
                ok = False
                break
            head = [L.text(x) for x in book[s][lay[0]]]
            r = next((i for i, lab, k in lay[2] if (s, lab, k) == (c["シート"], c["行"], int(c.get("何番目") or 1))), None)
            if r is None or c["列"] not in head:
                ok = False
                break
            j = head.index(c["列"])
            x = book[s][r][j] if j < len(book[s][r]) else None
            if not isinstance(x, (int, float)) or isinstance(x, bool):
                ok = False
                break
            total += int(round(x * L.UNIT.get(cfg.get("単位"), 1))) * int(c.get("符号") or 1)
        if ok:
            out[key] = total
    return out
