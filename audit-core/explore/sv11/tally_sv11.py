# -*- coding: utf-8 -*-
"""便 SV11 の照合と集計(封 explore/sv11/SEAL.md §2・§3)。

使い方: python3 -I tally_sv11.py <explore の folder> <scratchpad の根> <SV10 の根の写し> <record.json の path>
SV10 の照合(TextCompany)に、S10(足し漏れ・足し過ぎ)と文の行の S1 の細かい形(A・B)を足した SumCompany。
変異は機械が作る。流れの数え直しは tally_sv10.main を SumCompany に差し替えて走らせる(写しの中だけを書く)。記録は数だけ。
"""
import json
import os
import re
import sys

EXPLORE, SCRATCH, FLOW, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, os.path.join(EXPLORE, "sv10"))
sys.argv = ["", EXPLORE, FLOW, os.devnull]
import tally_sv10  # noqa: E402
tally = tally_sv10.tally
Text = tally_sv10.TextCompany

TEXT_MODE = "旧"  # 旧・A・B
SUM_CHECK = True
UNIT_TOKEN = re.compile(r"(\d[\d,]*(?:\.\d+)?)[ 　]*(百万|千|万|億)?[ 　]*(円|人|名)")
WORD_SCALE = {None: 1, "千": 1000, "万": 10000, "百万": 1000000, "億": 100000000}


def unit_values(line, unit):
    """行の字の中で、札の単位に合う字が後ろに付いた数の、本当の大きさの並び。"""
    out = []
    for num, word, suffix in UNIT_TOKEN.findall(line):
        word = word or None
        x = float(num.replace(",", ""))
        if unit == "人" and suffix in ("人", "名") and word is None:
            out.append(x)
        elif unit == "円" and suffix == "円":
            out.append(x * WORD_SCALE[word])
    return out


class SumCompany(Text):
    def text_line(self, src):
        lines = tally_sv10.read_lines(os.path.join(self.dir, "期1", os.path.basename(src["file"])))
        r = src.get("行")
        if lines is None or not isinstance(r, int) or r < 1 or r > len(lines):
            return None
        return lines[r - 1]

    def cell(self, src):
        if not src.get("文") or TEXT_MODE == "旧":
            return Text.cell(self, src)
        line, v = self.text_line(src), src.get("値")
        if src.get("列") != 0 or line is None or not isinstance(v, int):
            return None
        vals = unit_values(line, (src.get("札") or {}).get("単位"))
        if not any(round(x) == v and x == round(x) for x in vals):
            return None
        if TEXT_MODE == "B" and len(set(vals)) >= 2:
            return None
        return v

    def monthly_rows(self, name):
        """月次 12 項目の答えが、この表から 2 行以上で引いた出どころの全部。"""
        out = []
        for item in tally.MONTHLY:
            src = (self.answers.get(item) or {}).get("出どころ") or []
            if len(src) >= 2:
                out.extend(s for s in src if isinstance(s, dict) and os.path.basename(str(s.get("file"))) == name)
        return out

    def sum_check(self, item, sources):
        names = {os.path.basename(s["file"]) for s in sources}
        if len(names) != 1:
            return "S10"
        name = names.pop()
        cells = [(s["行"], s["列"]) for s in sources]
        if len(set(cells)) != len(cells):
            return "S10"
        col = self.date_col(name)
        if col is None:
            return None
        t = self.table(name)
        every = self.monthly_rows(name)
        rows = sorted({s["行"] for s in every})
        amount = {s["列"] - 1 for s in every}
        width = max(len(r) for r in t)
        key = {}
        for c in range(width):
            if c == col or c in amount:
                continue
            vals = {(t[r - 1][c].strip() if c < len(t[r - 1]) else "") for r in rows}
            if len(vals) == 1 and "" not in vals:
                key[c] = vals.pop()
        if not key:
            return "S10"
        first, last = tally.month_range(self.start, int(item[-2:]))
        cited = {s["行"] for s in sources}
        for i, row in enumerate(t[1:], start=2):
            day = tally_sv10.tally_sv9.parse_date(row[col]) if col < len(row) else None
            if day is None or not (first <= day <= last):
                continue
            if all(c < len(row) and row[c].strip() == v for c, v in key.items()) and i not in cited:
                return "S10"
        return None

    def check(self, item, value, sources, value_only=False):
        w = Text.check(self, item, value, sources, value_only)
        if w is not None or value_only or not SUM_CHECK:
            return w
        if item.startswith("月次の売上高_当期_") and len(sources) >= 2:
            return self.sum_check(item, sources)
        return None


def old_check(co, item, value, sources):
    global SUM_CHECK
    SUM_CHECK = False
    try:
        return co.check(item, value, sources)
    finally:
        SUM_CHECK = True


def new_check(co, item, value, sources):
    keep = co.answers.get(item)
    co.answers[item] = {"項目": item, "値": value, "出どころ": sources}
    try:
        return co.check(item, value, sources)
    finally:
        co.answers[item] = keep


def amount(co, s):
    return co.cell(s) * s.get("倍率", 1) * s.get("符号", 1)


def sum_mutants(root, num):
    g = {"正しい月次の答え(出どころ 2 行以上・S1〜S6 を通る)": 0, "そのうち S10 が止めた": 0,
         "足し漏れの変異": 0, "足し漏れを旧い照合が通した": 0, "足し漏れを新しい照合が通した": 0,
         "足し過ぎの変異": 0, "足し過ぎを旧い照合が通した": 0, "足し過ぎを新しい照合が通した": 0}
    co = SumCompany(root, num)
    for item in tally.MONTHLY:
        a = co.answers.get(item) or {}
        v, src = a.get("値"), a.get("出どころ") or []
        if v is None or v != co.gold[item] or len(src) < 2 or old_check(co, item, v, src) is not None:
            continue
        g["正しい月次の答え(出どころ 2 行以上・S1〜S6 を通る)"] += 1
        g["そのうち S10 が止めた"] += co.check(item, v, src) is not None
        for i in range(len(src)):
            rest = src[:i] + src[i + 1:]
            v2 = sum(amount(co, s) for s in rest)
            g["足し漏れの変異"] += 1
            g["足し漏れを旧い照合が通した"] += old_check(co, item, v2, rest) is None
            g["足し漏れを新しい照合が通した"] += new_check(co, item, v2, rest) is None
        name = os.path.basename(src[0]["file"])
        col, t = co.date_col(name), co.table(name)
        if col is None:
            continue
        first, last = tally.month_range(co.start, int(item[-2:]))
        cited = {s["行"] for s in src}
        for r in range(2, len(t) + 1):
            row = t[r - 1]
            day = tally_sv10.tally_sv9.parse_date(row[col]) if col < len(row) else None
            extra = dict(src[0], 行=r)
            if day is None or not (first <= day <= last) or r in cited or co.cell(extra) in (None, 0):
                continue
            more = src + [extra]
            v2 = sum(amount(co, s) for s in more)
            g["足し過ぎの変異"] += 1
            g["足し過ぎを旧い照合が通した"] += old_check(co, item, v2, more) is None
            g["足し過ぎを新しい照合が通した"] += new_check(co, item, v2, more) is None
            break
    return g


def text_mutants():
    global TEXT_MODE
    modes = ["旧", "A", "B"]
    g = {"文の行": 0, "正しい値の升を止めた": {m: 0 for m in modes},
         "差し替え(同じ単位の字が付いた数)": 0, "同じ単位の差し替えを通した": {m: 0 for m in modes},
         "差し替え(それ以外)": 0, "それ以外の差し替えを通した": {m: 0 for m in modes}}
    conv = os.path.join(FLOW, "r1", "conv")
    for num in tally_sv10.NUMS:
        co = SumCompany(conv, num)
        mp = tally_sv10.load(os.path.join(FLOW, "r1", "map%s.json" % num))
        for src in mp.values():
            if not src.get("文"):
                continue
            g["文の行"] += 1
            line = co.text_line(src) or ""
            same = {int(x) for x in unit_values(line, (src.get("札") or {}).get("単位")) if x == int(x)}
            others = set()
            for m in tally_sv10.NUM.findall(line):
                x = float(m.replace(",", ""))
                if x == int(x) and int(x) != src.get("値"):
                    others.add(int(x))
            for mode in modes:
                TEXT_MODE = mode
                g["正しい値の升を止めた"][mode] += co.cell(src) is None
            for x in sorted(others):
                kind = "同じ単位の" if x in same else "それ以外の"
                g["差し替え(同じ単位の字が付いた数)" if x in same else "差し替え(それ以外)"] += 1
                for mode in modes:
                    TEXT_MODE = mode
                    g[kind + "差し替えを通した"][mode] += co.cell(dict(src, 値=x)) is not None
    TEXT_MODE = "旧"
    return g


def flow(mode, with_sum):
    global TEXT_MODE, SUM_CHECK
    TEXT_MODE, SUM_CHECK = mode, with_sum
    keep = tally_sv10.TextCompany
    tally_sv10.TextCompany = SumCompany
    tally_sv10.OUT = os.path.join(FLOW, "flow_%s_%d.json" % (mode, with_sum))
    try:
        tally_sv10.main()
    finally:
        tally_sv10.TextCompany = keep
        TEXT_MODE, SUM_CHECK = "旧", True
    return tally_sv10.load(tally_sv10.OUT)


def main():
    rec = {"足し漏れ・足し過ぎ": {}, "文の行": None, "流れの数え直し": {}}
    groups = [("SV5 の元の file を見た席の答え(社 13)", os.path.join(SCRATCH, "sv5", "r0"), "13"),
              ("SV7 の貯めた行だけの席の答え(社 15)", os.path.join(SCRATCH, "sv7", "r1", "conv"), "15"),
              ("SV10 の埋める席の答え(社 15)", os.path.join(FLOW, "r1", "conv"), "15")]
    for name, root, num in groups:
        rec["足し漏れ・足し過ぎ"][name] = sum_mutants(root, num)
    rec["文の行"] = text_mutants()
    keys = ["正しい行", "違う行", "正しい行(決めの行を除く)", "そのうち S1〜S9 で止めた",
            "そのうち S1〜S9 を全部通った(資料に残る誤り)", "文の中の項目を正しく出して S1〜S9 を通った"]
    for label, mode, with_sum in (("SV10 の照合のまま", "旧", False), ("S10 + 形 A", "A", True), ("S10 + 形 B", "B", True)):
        f = flow(mode, with_sum)
        rec["流れの数え直し"][label] = {k: f[k] for k in keys}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
