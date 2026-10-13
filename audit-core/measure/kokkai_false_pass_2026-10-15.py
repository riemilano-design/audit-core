# -*- coding: utf-8 -*-
"""議事録(国会会議録)の「誤りを通す率」を**小さな誤り**で測る。

人間の原則(2026-10-14)「誤りを通す率は 0 を目指さないと意味ない」。混入の道具
(``measure/kokkai_inject_2026-10-14.py``)の T4 は数を **10 倍**にする誤りで、
**書かれた最小の桁 1 つ分**という小さな誤りを測っていなかった。

やり方: 2 つの会議の claims のうち ``number`` を持ち、土台で GROUNDED のもの全部に
ついて、``number.value`` を**書かれた表記の最小の桁 1 つ分**だけ増やし、**1 件ずつ
別の検証**にかけて、数の検査がそれでも GROUNDED になる件数を数える。

「書かれた最小の桁」= 表記の中で**実際に数字が書かれている位のうち最小のもの**。
位取りの字(十百千)と大きい単位(万億兆)を解いて、桁の一覧を作り、その最小を採る::

    三百億円            → 百億 = 1e10
    八兆五千六百四十一億円 → 一億 = 1e8   (億の位の「一」まで書かれている)
    四十五隻            → 一   = 1       (「五」が一の位)
    一・一兆円          → 0.1 兆 = 1e11
    一五％ / 15％       → 1
    二七・七％          → 0.1

2026-10-15 の監査の REVISE で直した: 最初の実装(scratchpad の使い捨て script)は
十百千だけで書かれた数で**先頭の位**を採っており、49 件中 26 件で桁が粗すぎた
(「四十五隻」に +10)。監査が 26 件を正しい桁で測り直し、**結論(1/49)は変わらない**
ことを確認済み。ここで道具として置き直し、桁の決め方に試験を付ける。

通信しない。
"""

import copy
import io
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.kokkai import numerals as N  # noqa: E402
from adapters.kokkai import verify_meeting as VM  # noqa: E402

FIX = os.path.join(ROOT, "fixtures", "kokkai")
CASES = (
    ("meeting_122105261X01220260330.json", "summary_122105261X01220260330_seat.json"),
    ("meeting_122115261X00820260330.json", "summary_122115261X00820260330_seat.json"),
)

_DIGITS = "〇零一二三四五六七八九0-9０-９"
_SMALL = {"十": 10.0, "百": 100.0, "千": 1000.0}
_BIG = (("兆", 1e12), ("億", 1e8), ("万", 1e4))
_PREFIX_RE = re.compile(r"^(約|およそ|概ね|ほぼ)+")


def _is_digit(ch):
    return ch in "〇零一二三四五六七八九" or ch.isdigit()


def _places_small(s):
    """位取りの字(十百千)・数字・小数点だけの並び → 書かれている位の一覧。

    小数点はここで扱う(大きい単位の前に来る形 ― 「一・一兆」 ― があるため。
    上の層で末尾だけ見ていると、この形の小数桁を見落として桁が粗くなる)。"""

    m = re.match(r"^(.*?)[・.]([%s]+)$" % _DIGITS, s)
    frac_digits = 0
    if m:
        s, frac_digits = m.group(1), len(m.group(2))
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if _is_digit(ch):
            if i + 1 < len(s) and s[i + 1] in _SMALL:
                out.append(_SMALL[s[i + 1]])
                i += 2
            else:
                out.append(1.0)
                i += 1
        elif ch in _SMALL:
            out.append(_SMALL[ch])   # 「十」単独 = 1 の桁が無い 10
            i += 1
        else:
            i += 1
    for k in range(1, frac_digits + 1):
        out.append(1.0 / (10 ** k))
    return out


def _places(s):
    for ch, val in _BIG:
        if ch in s:
            left, right = s.split(ch, 1)
            return [p * val for p in _places_small(left)] + _places(right)
    return _places_small(s)


def min_written_step(text):
    """書かれた表記の最小の桁 1 つ分。読めなければ ``None``。"""

    if text is None:
        return None
    t = unicodedata.normalize("NFKC", str(text)).strip()
    t = _PREFIX_RE.sub("", t)
    for u in sorted(N.UNITS, key=len, reverse=True):
        if t.endswith(u):
            t = t[: -len(u)]
            break
    t = t.strip()
    ps = _places(t)
    if not ps:
        return None
    return min(ps)


def _load(name):
    with io.open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return json.load(fh)


def run():
    rows = []
    for mt, sm in CASES:
        meeting, summary = _load(mt), _load(sm)
        base = {c["id"]: c for c in VM.verify_meeting(meeting, summary)["claims"]}
        for c in summary["claims"]:
            n = c.get("number")
            if not isinstance(n, dict) or n.get("value") is None:
                continue
            if base[c["id"]]["state"] != "GROUNDED":
                rows.append({"doc": mt, "id": c["id"], "skipped": "base not grounded"})
                continue
            step = min_written_step(n.get("text"))
            if step is None:
                rows.append({"doc": mt, "id": c["id"], "skipped": "step unreadable", "text": n.get("text")})
                continue
            s2 = copy.deepcopy(summary)
            for cc in s2["claims"]:
                if cc["id"] == c["id"]:
                    cc["number"]["value"] = n["value"] + step
            out = {x["id"]: x for x in VM.verify_meeting(meeting, s2)["claims"]}
            rows.append({"doc": mt, "id": c["id"], "text": n.get("text"), "unit": n.get("unit"),
                         "value": n["value"], "step": step,
                         "after": out[c["id"]]["checks"].get("number")})
    measured = [r for r in rows if "after" in r]
    passed = [r for r in measured if r["after"] == "GROUNDED"]
    rec = {"purpose": "議事録の誤りを通す率(書かれた最小の桁 1 つ分の誤り)。1 件ずつ別の検証。",
           "n": len(measured), "passed": len(passed),
           "passed_rows": [{k: r[k] for k in ("doc", "id", "text", "unit", "value", "step")} for r in passed],
           "rows": rows}
    p = os.path.join(FIX, "false_pass_round12_2026-10-15.json")
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("測った %d 件、通した %d 件" % (len(measured), len(passed)))
    for r in passed:
        print("  通した", r["doc"][8:-5], r["id"], r["text"], "+", r["step"], r["unit"])
    print("->", p)


if __name__ == "__main__":
    run()
