# -*- coding: utf-8 -*-
"""便 SV12 の照合と集計(封 explore/sv12/SEAL.md §2・§3)。

使い方: python3 -I tally_sv12.py <explore の folder> <scratchpad の根> <SV10 の根の写し> <record.json の path>
SV11 の SumCompany(S10・文の行の形 A)の鍵を、くり返し出る字の集まり(S10′)に替えた SetCompany。記録は数だけ。
"""
import json
import os
import sys

EXPLORE, SCRATCH, FLOW, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, os.path.join(EXPLORE, "sv11"))
sys.argv = ["", EXPLORE, SCRATCH, FLOW, os.devnull]
import tally_sv11 as T  # noqa: E402
tally, tally_sv10 = T.tally, T.tally_sv10
parse_date = tally_sv10.tally_sv9.parse_date
MIN_MONTHS = 6
CREDIT = "貸方勘定科目"


class SetCompany(T.SumCompany):
    def month_of(self, row, col):
        day = parse_date(row[col]) if col < len(row) else None
        return None if day is None else (day.year, day.month)

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
            months = {}
            for r in rows:
                v = t[r - 1][c].strip() if c < len(t[r - 1]) else ""
                months.setdefault(v, set()).add(self.month_of(t[r - 1], col))
            if months and all(len(m) >= MIN_MONTHS for m in months.values()):
                key[c] = set(months)
        if not key:
            return "S10"
        first, last = tally.month_range(self.start, int(item[-2:]))
        cited = {s["行"] for s in sources}
        for i, row in enumerate(t[1:], start=2):
            day = parse_date(row[col]) if col < len(row) else None
            if day is None or not (first <= day <= last):
                continue
            if all((row[c].strip() if c < len(row) else "") in vs for c, vs in key.items()) and i not in cited:
                return "S10"
        return None


def judge(co, cls, item, value, sources):
    """S1〜S6(と文の行)を見て、通れば cls の sum_check を当てる(self の差し替えに頼らない)。"""
    w = T.Text.check(co, item, value, sources)
    if w is not None or cls is None:
        return w
    if item.startswith("月次の売上高_当期_") and len(sources) >= 2:
        return cls.sum_check(co, item, sources)
    return None


def check(co, cls, item, value, sources):
    """cls の照合で見る。S1〜S6 だけなら cls=None。"""
    keep = co.answers.get(item)
    co.answers[item] = {"項目": item, "値": value, "出どころ": sources}
    try:
        return judge(co, cls, item, value, sources)
    finally:
        co.answers[item] = keep


def amount(co, s):
    return co.cell(s) * s.get("倍率", 1) * s.get("符号", 1)


def mutants(root, num):
    kinds = ["1 行抜き", "1 行足し", "まるごと落とし"]
    g = {"正しい月次の答え": 0, "正しい答えを S10 が止めた": 0, "正しい答えを S10′ が止めた": 0}
    for k in kinds:
        g[k] = {"数": 0, "旧が通した": 0, "S10 が通した": 0, "S10′ が通した": 0}
    co = SetCompany(root, num)

    def count(kind, item, srcs):
        v2 = sum(amount(co, s) for s in srcs)
        g[kind]["数"] += 1
        g[kind]["旧が通した"] += check(co, None, item, v2, srcs) is None
        g[kind]["S10 が通した"] += check(co, T.SumCompany, item, v2, srcs) is None
        g[kind]["S10′ が通した"] += check(co, SetCompany, item, v2, srcs) is None

    for item in tally.MONTHLY:
        a = co.answers.get(item) or {}
        v, src = a.get("値"), a.get("出どころ") or []
        if v is None or v != co.gold[item] or len(src) < 2 or judge(co, None, item, v, src) is not None:
            continue
        g["正しい月次の答え"] += 1
        g["正しい答えを S10 が止めた"] += judge(co, T.SumCompany, item, v, src) is not None
        g["正しい答えを S10′ が止めた"] += judge(co, SetCompany, item, v, src) is not None
        for i in range(len(src)):
            count("1 行抜き", item, src[:i] + src[i + 1:])
        name = os.path.basename(src[0]["file"])
        col, t = co.date_col(name), co.table(name)
        first, last = tally.month_range(co.start, int(item[-2:]))
        cited = {s["行"] for s in src}
        for r in range(2, len(t) + 1):
            row = t[r - 1]
            day = parse_date(row[col]) if col < len(row) else None
            extra = dict(src[0], 行=r)
            if day is None or not (first <= day <= last) or r in cited or co.cell(extra) in (None, 0):
                continue
            count("1 行足し", item, src + [extra])
            break
        head = t[0]
        cc = next((c for c, h in enumerate(head) if CREDIT in h), None)
        if cc is None:
            continue
        groups = {}
        for s in src:
            groups.setdefault(t[s["行"] - 1][cc].strip(), []).append(s)
        if len(groups) >= 2:
            for k in groups:
                count("まるごと落とし", item, [s for s in src if t[s["行"] - 1][cc].strip() != k])
    return g


def main():
    rec = {"群": {}, "流れの数え直し(S10′ + 形 A)": None}
    groups = [("SV5 の元の file を見た席の答え(社 13)", os.path.join(SCRATCH, "sv5", "r0"), "13"),
              ("SV7 の貯めた行だけの席の答え(社 15)", os.path.join(SCRATCH, "sv7", "r1", "conv"), "15"),
              ("SV10 の埋める席の答え(社 15)", os.path.join(FLOW, "r1", "conv"), "15")]
    T.TEXT_MODE = "A"
    for name, root, num in groups:
        rec["群"][name] = mutants(root, num)
    keep = tally_sv10.TextCompany
    tally_sv10.TextCompany = SetCompany
    tally_sv10.OUT = os.path.join(FLOW, "flow_sv12.json")
    try:
        tally_sv10.main()
    finally:
        tally_sv10.TextCompany = keep
    f = tally_sv10.load(tally_sv10.OUT)
    rec["流れの数え直し(S10′ + 形 A)"] = {k: f[k] for k in (
        "正しい行", "違う行", "正しい行(決めの行を除く)", "そのうち S1〜S9 で止めた",
        "そのうち S1〜S9 を全部通った(資料に残る誤り)", "文の中の項目を正しく出して S1〜S9 を通った")}
    with open(OUT, "w", encoding="utf-8") as fo:
        json.dump(rec, fo, ensure_ascii=False, indent=1)
        fo.write("\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
