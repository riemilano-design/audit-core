# -*- coding: utf-8 -*-
"""便 SV9 の照合と集計(封 explore/sv9/SEAL.md §2)。

使い方: python3 -I tally_sv9.py <explore の folder> <scratchpad の根> <record.json の path>
SV0 の照合(../sv0/tally.py)は変えず、Company を差し替えた DatedCompany で同じ集計(tally.main)を走らせ、
旧い照合と新しい照合の数を群ごとに並べる。記録は数だけ。
"""
import datetime
import json
import os
import re
import sys

EXPLORE, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(EXPLORE, "sv0"))
import tally  # noqa: E402

OLD = tally.Company
DATE = re.compile(r"^\s*(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})日?\s*$")
GROUPS = [
    ("A SV1 の答え(貯めた行だけ)", ["9", "10", "11"], os.path.join(ROOT, "sv1", "conv")),
    ("B SV5 の元の file を見た席の答え", ["12", "13", "14"], os.path.join(ROOT, "sv5", "r0")),
    ("C SV5 の貯めた行だけの席の答え", ["12", "13", "14"], os.path.join(ROOT, "sv5", "r1", "conv")),
    ("D SV7 の貯めた行だけの席の答え", ["15", "16", "17"], os.path.join(ROOT, "sv7", "r1", "conv")),
]


def parse_date(text):
    m = DATE.match(text or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


class DatedCompany(OLD):
    """日付の列が在る表では、升の期をその行の日 1 日の期間に細かくする(札の期間の中に在る時だけ)。"""

    def __init__(self, root, num):
        OLD.__init__(self, root, num)
        self.date_cols = {}

    def date_col(self, name):
        name = os.path.basename(name)
        if name not in self.date_cols:
            t = self.table(name)
            found = None
            if t is not None:
                width = max((len(r) for r in t), default=0)
                for c in range(width):
                    cells = [r[c] for r in t[1:] if c < len(r) and r[c].strip()]
                    if cells and sum(parse_date(x) is not None for x in cells) >= 0.8 * len(cells):
                        found = c
                        break
            self.date_cols[name] = found
        return self.date_cols[name]

    def label(self, src):
        lab = OLD.label(self, src)
        p = lab.get("期")
        if not isinstance(p, dict) or p.get("種類") != "期間":
            return lab
        col = self.date_col(src["file"])
        t = self.table(src["file"])
        r = src.get("行")
        if col is None or t is None or not isinstance(r, int) or r < 1 or r > len(t) or col >= len(t[r - 1]):
            return lab
        day = parse_date(t[r - 1][col])
        try:
            a, b = tally.d(p["始まり"]), tally.d(p["終わり"])
        except (KeyError, ValueError, TypeError):
            return lab
        if day is None or not (a <= day <= b):
            return lab
        lab = dict(lab)
        lab["期"] = {"種類": "期間", "始まり": day.isoformat(), "終わり": day.isoformat()}
        return lab

    def period_ok(self, item, p, multi):
        if multi and item.startswith("月次の売上高_当期_") and p.get("種類") == "期間":
            try:
                a, b = tally.d(p["始まり"]), tally.d(p["終わり"])
            except (KeyError, ValueError, TypeError):
                return False
            first, last = tally.month_range(self.start, int(item[-2:]))
            return first <= a and b <= last
        return OLD.period_ok(self, item, p, multi)


KEYS = ["正しい行", "正しい行を止めた", "違う行", "違う行を通した", "決めの行を通した",
        "M-罠を通した", "M-ずらし", "M-ずらしを通した"]


def run(nums, root, cls, path):
    tally.COMPANIES = nums
    tally.Company = cls
    sys.argv = ["", root, path]
    try:
        tally.main()
    finally:
        tally.Company = OLD
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    work = os.path.join(ROOT, "sv9")
    os.makedirs(work, exist_ok=True)
    rec = {}
    for i, (name, nums, root) in enumerate(GROUPS):
        old = run(nums, root, OLD, os.path.join(work, "old%d.json" % i))
        new = run(nums, root, DatedCompany, os.path.join(work, "new%d.json" % i))
        g = {}
        for k in KEYS:
            g[k] = {"旧": old[k], "新": new[k]}
        g["正しい行を S3 で止めた"] = {"旧": old["正しい行を止めた理由"]["S3"], "新": new["正しい行を止めた理由"]["S3"]}
        rec[name] = g
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
