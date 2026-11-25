# -*- coding: utf-8 -*-
"""便 TR11: XBRL でない経路を 1 本の流れで通す(封 §2)。TR2・TR6〜TR10 の file を変えずに読んで使う。AI を使わない。

流れ(1 社ずつ):
  1 確定の台帳(TR2 の確定 + 期 1。検算と列の何番目つき = ledger9)で今期の file を読む。
  2 止めたら、変わった所(diff9)と、変わった所に触れない数の先の読み(部分の読み)を出し、確定し直しの画面(screen11)を作る。
  3 確定し直しの席の決めを当て(reconf9.apply)、台帳を作り直して今期の file を読み直す。
  4 読んだ 15 の値を材料に、書く席が資料と札を書く(TR10 の紙)。
  5 札の数を台帳の値で点検し(TR10 の check_doc)、点検レポート(report11)を出す。
小さな足し 2 つ:
  - screen11: 同じ見出しの列の追加の補足に、その列の上の行の字(表の頭)を並べる(TR9 で 4 席が、手がかりが別の行に出て分かりにくいと書いた)。
  - report11: 確認済みの元の升で、引く升(符号 −1)に「(引く)」を付ける(TR10 §3)。
"""
import html
import re

import ledger_tr2 as L
import reconf8 as R8
import reconf9 as R9
import check_tr10 as K


def head_words(decided, book, sheet, name):
    """その見出しの列ごとに、列の見出しの行より上の行の字を返す [(何本目, 上の字)]。"""
    lay = L.layout(book[sheet], decided["シート"][sheet])
    if lay is None:
        return []
    h = lay[0]
    cols = [j for j, x in enumerate(book[sheet][h]) if L.text(x) == name]
    out = []
    for k, j in enumerate(cols, 1):
        words = [L.text(row[j]) for row in book[sheet][:h] if j < len(row) and row[j] not in (None, "")]
        out.append((k, " / ".join(words) or "(字なし)"))
    return out


def screen11(n, sk, changes, decided, book, plan_read, early):
    extra = {}
    for ch in changes:
        if ch["種類"] == "同じ見出しの列の追加":
            hw = head_words(decided, book, ch["シート"], ch["今"])
            extra[ch["番号"]] = "列の上の行の字: " + "・".join("%d 本目「%s」" % (k, w) for k, w in hw)
    base_note = R9.note9

    def note11(ch, base=base_note):
        s = base(ch)
        return s + ("。" + extra[ch["番号"]] if ch["番号"] in extra else "")

    old = R9.note9
    R9.note9 = note11
    try:
        return R9.screen9(n, sk, changes, decided, book, plan_read, early)
    finally:
        R9.note9 = old


def report11(n, rows, title):
    h = K.report(n, rows, title)
    marks = {"シート「%s」・行「%s」・列「%s」・升の値 %s" % (html.escape(s["シート"]), html.escape(s["行"]), html.escape(s["列"]), html.escape(str(s["升の値"])))
             for r in rows if r["区分"] == "確認済み" for s in r.get("出どころ") or [] if int(s.get("符号") or 1) == -1}
    for a in marks:
        h = re.sub(re.escape(a) + r"(?!(引く))", lambda m: m.group(0) + "(引く)", h)
    return h
