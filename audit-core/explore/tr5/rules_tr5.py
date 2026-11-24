# -*- coding: utf-8 -*-
"""便 TR5: TR4 の 2 つの穴を塞ぐ規則(AI を使わない)。TR4 の numbers_tr4・judge_tr4 は変えずに上に足す。

- R1 同じ文の重なり: 同じ行・同じ文(「。」で区切る)の中に、同じ項目・同じ期の「金額」の札が 2 枚以上在れば、全部止める。
  (TR4 の期の隠しの 3 は、替えた数が同じ文の「前期の」の数と同額で、札も 2 枚とも前期になった形)
- R2 前期の証拠: 「金額」の札の期が前期・前期末なのに、その数の期の字(numbers_tr4.period_word。文の行は前の数から
  この数まで・表は列の見出し)が「前」でなければ止める。「当」なら TR4 の食い違いで既に止まる。字が無い時に止めるのが足し。
  (TR4 の期の隠しの止まらなかった 7 は、どれも数の前に期の字が無い形)
- 単位を本文から取る(評価の判定の入口): 資料の行と位置から、numbers_tr4.extract_all の単位を返す。拾った読みの単位を使わない。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tr4"))
import numbers_tr4 as N  # noqa: E402


def sentence_of(md, line, start):
    s = md.split("\n")[line]
    return s[:start].count("。")


def r2(rec, tag):
    """前期の証拠が無ければ (True, 訳)。"""
    if tag.get("種類") != "金額" or tag.get("期") not in ("前期", "前期末"):
        return False, None
    k, w = N.period_word(rec)
    if k is None:
        return True, "前期の数の札なのに、数の近くに前期の字が無い"
    return False, None  # 「前」は証拠が在る。「当」は TR4 の食い違いで止まる


def r1(md, tagged):
    """tagged: [(rec, tag, 行の id)]。同じ文・同じ項目・同じ期の金額の札が 2 枚以上の id の集まり。"""
    groups = {}
    for rec, tag, rid in tagged:
        if tag.get("種類") != "金額" or rec["場所"] != "文":
            continue
        key = (rec["行"], sentence_of(md, rec["行"], rec["始め"]), tag.get("項目"), tag.get("期"))
        groups.setdefault(key, []).append(rid)
    return {rid for ids in groups.values() if len(ids) >= 2 for rid in ids}


def unit_at(md, line, start):
    """資料の line 行の start の位置の数の、本文の単位(numbers_tr4 の拾い方)。拾えなければ None。"""
    for r in N.extract_all(md):
        if r["行"] == line and r["始め"] <= start < r["終わり"]:
            return r["単位"]
    for r in N.extract_all(md):
        if r["行"] == line and abs(r["始め"] - start) <= 1:
            return r["単位"]
    return None
