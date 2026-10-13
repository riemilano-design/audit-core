# -*- coding: utf-8 -*-
"""漢数字・算用数字の読み取り(会議録の本文用)。

会議録の数は 2 通りの書き方が混ざる:

- 位取り(十百千万億兆)で書く: 「三百億円」「一・一兆円」「二十四日」
- 桁を並べて書く: 「一九九一年」「一五％」「二〇二二年」

規則: 「・」は小数点。十百千万億兆が 1 字も無ければ桁の並び、在れば位取り。
小数のあとに万億兆が付く形(「一・一兆」)は、小数を作ってから掛ける。
"""

import re

_DIGITS = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
           "六": 6, "七": 7, "八": 8, "九": 9}
for _i in range(10):
    _DIGITS[str(_i)] = _i
    _DIGITS[chr(0xFF10 + _i)] = _i  # 全角 ０〜９
_SMALL = {"十": 10, "百": 100, "千": 1000}
_BIG = {"万": 10 ** 4, "億": 10 ** 8, "兆": 10 ** 12}

_DIGIT_CLASS = "〇零一二三四五六七八九0-9０-９"
_NUM_RE = re.compile(
    r"(?P<int>[" + _DIGIT_CLASS + r"十百千万億兆]+)"
    r"(?:・(?P<frac>[" + _DIGIT_CLASS + r"]+)(?P<big>[万億兆])?)?"
)

# 単位(この後ろに付く語)。表記の揺れは UNIT_ALIASES で 1 つに寄せる。
UNITS = ("円", "人", "件", "％", "%", "パーセント", "年", "割", "倍", "か所", "カ所", "箇所",
         "か月", "カ月", "ヶ月", "日", "回", "社", "世帯", "トン", "キロ", "名", "か国", "カ国", "本", "案", "ポイント")
UNIT_ALIASES = {"%": "％", "パーセント": "％", "カ所": "か所", "箇所": "か所", "カ月": "か月", "ヶ月": "か月", "カ国": "か国"}
_UNIT_RE = "|".join(sorted((re.escape(u) for u in UNITS), key=len, reverse=True))
_TOKEN_RE = re.compile(_NUM_RE.pattern + r"(?P<unit>" + _UNIT_RE + r")?")


def normalize_unit(unit):
    if unit is None:
        return None
    unit = str(unit).strip()
    if unit == "":
        return None
    return UNIT_ALIASES.get(unit, unit)


def _positional(s):
    v = 0
    for ch in s:
        if ch not in _DIGITS:
            return None
        v = v * 10 + _DIGITS[ch]
    return v


def _place_value(s):
    total = 0
    section = 0
    digit = 0
    seen_digit = False
    for ch in s:
        if ch in _DIGITS:
            digit = digit * 10 + _DIGITS[ch]
            seen_digit = True
        elif ch in _SMALL:
            section += (digit if seen_digit else 1) * _SMALL[ch]
            digit = 0
            seen_digit = False
        elif ch in _BIG:
            section += digit
            if section == 0:
                section = 1
            total += section * _BIG[ch]
            section = 0
            digit = 0
            seen_digit = False
        else:
            return None
    return total + section + digit


def parse_number(text):
    """「三百億」「一・一兆」「一九九一」「15」→ 値(float)。読めなければ ``None``。"""

    if text is None:
        return None
    m = _NUM_RE.fullmatch(str(text).strip())
    if m is None:
        return None
    return _value_of(m)


def _value_of(m):
    int_part = m.group("int")
    frac = m.group("frac")
    big = m.group("big")
    if frac is not None:
        ip = _positional(int_part) if not any(c in int_part for c in "十百千万億兆") else _place_value(int_part)
        fp = _positional(frac)
        if ip is None or fp is None:
            return None
        v = ip + fp / float(10 ** len(frac))
        if big:
            v *= _BIG[big]
        return float(v)
    if any(c in int_part for c in "十百千万億兆"):
        v = _place_value(int_part)
    else:
        v = _positional(int_part)
    return None if v is None else float(v)


def number_tokens(text):
    """本文中の数を全部拾う。``[(value, unit, raw), ...]``。unit は正規化済み(無ければ None)。"""

    out = []
    for m in _TOKEN_RE.finditer(text):
        v = _value_of(m)
        if v is None:
            continue
        raw = m.group(0)
        out.append((v, normalize_unit(m.group("unit")), raw))
    return out
