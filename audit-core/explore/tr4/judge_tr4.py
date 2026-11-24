# -*- coding: utf-8 -*-
"""便 TR4: 評価の判定 ― 資料の数が「正しい数」か(拾った読み・札に依らない)。

TR0-1 と TR3-1 で、言い過ぎを「拾った読み(項目・期・種類)のまま材料と比べる」判定で数え、読み違いそのものが
言い過ぎから漏れて 0 と出た(2 度)。この判定は、読みも札も受け取らない。資料の数(字)と単位と、その社の材料だけを見る。

正しい数 = 材料のどれかの項目の、値・増減額(当期 − 前期)・増減率のどれかと、資料の桁で同じ(四捨五入か切り捨て。
符号は見ない)。人数は人数の値と同じ。
"""
import math
import re

SCALE = {"円": 1, "千円": 1000, "百万円": 1000000, "億円": 100000000}
PAIRS = {"当期": "前期", "当期末": "前期末"}


def decimals_of(text):
    m = re.search(r"\.(\d+)", text or "")
    return len(m.group(1)) if m else 0


def _shown(x, k):
    """x を小数 k 桁で表した時にありうる数を、10 の k 乗倍した整数で(四捨五入・切り捨て)。"""
    f = 10 ** k
    y = abs(x) * f
    return {int(round(y)), int(math.floor(y + 1e-9))}


def matches(text, value, unit, mat):
    """資料の数が当たる材料の読みの一覧 [(項目, 期, 形)]。空なら正しい数でない。

    text: 資料の数の字(桁を決めるのに使う)。value: 数(符号つきでもよい。符号は見ない)。
    unit: 円・千円・百万円・億円・%・％・人・名 のどれか。mat: {(項目, 期): 値(円か人)}。
    """
    k = decimals_of(text)
    got = int(round(abs(value) * 10 ** k))
    out = []
    if unit in ("人", "名"):
        for (item, per), v in mat.items():
            if item == "期末の従業員数" and v == abs(value):
                out.append((item, per, "値"))
        return out
    if unit in SCALE:
        s = SCALE[unit]
        for (item, per), v in mat.items():
            if item == "期末の従業員数":
                continue
            if got in _shown(v / s, k):
                out.append((item, per, "値"))
            if per in PAIRS and (item, PAIRS[per]) in mat:
                d = v - mat[(item, PAIRS[per])]
                if got in _shown(d / s, k):
                    out.append((item, per, "増減額"))
        return out
    if unit in ("%", "％"):
        for (item, per), v in mat.items():
            if per in PAIRS and (item, PAIRS[per]) in mat and mat[(item, PAIRS[per])]:
                p = mat[(item, PAIRS[per])]
                if got in _shown((v - p) / abs(p) * 100, k):
                    out.append((item, per, "増減率"))
        return out
    return out


def is_correct(text, value, unit, mat):
    return bool(matches(text, value, unit, mat))
