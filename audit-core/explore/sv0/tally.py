# -*- coding: utf-8 -*-
"""便 SV0 の照合と集計(封 explore/sv0/SEAL.md §2・§3)。

使い方: python3 -I tally.py <素材と席の出力の根> <record.json の path>
根の下に co9・co10・co11(素材)と out9・out10・out11(札.json・答え.json)が在る。
記録は数だけ(会社の名・file の名・値・日付・項目の名は書かない)。
"""
import csv
import datetime
import io
import json
import os
import re
import sys

COMPANIES = ["9", "10", "11"]
REASONS = ["S1", "S7", "S2", "S3", "S4", "S5", "S6"]
UNIT_SCALE = {"円": 1, "千円": 1000, "百万円": 1000000}
SINGLE = ["売上高_当期", "売上高_前期", "売上総利益_当期", "営業利益_当期", "営業利益_前期",
          "経常利益_当期", "当期純利益_当期", "減価償却費_当期", "現金及び預金_当期末",
          "流動資産合計_当期末", "資産合計_当期末", "短期借入金_当期末", "長期借入金_当期末",
          "負債合計_当期末", "純資産合計_当期末", "純資産合計_前期末",
          "借入の残高の合計_当期末", "期末の従業員数_当期末", "人件費_当期"]
MONTHLY = ["月次の売上高_当期_%02d" % i for i in range(1, 13)]
ITEMS = SINGLE + MONTHLY


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_table(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp932"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return None
    return list(csv.reader(io.StringIO(text)))


def cell_number(text):
    """升の字を数に読む。読めなければ None。"""
    s = text.strip().replace(",", "").replace(" ", "").replace("　", "").replace("円", "")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    if s[:1] in ("△", "▲", "-"):
        neg, s = not neg, s[1:]
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return None
    v = float(s)
    if v != int(v):
        return None
    return -int(v) if neg else int(v)


def d(s):
    return datetime.date.fromisoformat(s)


def month_range(start, n):
    """当期の n 番目(1 から)の月の初日と末日。"""
    y, m = start.year, start.month + (n - 1)
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    first = datetime.date(y, m, 1)
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return first, datetime.date(ny, nm, 1) - datetime.timedelta(days=1)


class Company:
    def __init__(self, root, num):
        self.dir = os.path.join(root, "co" + num)
        self.out = os.path.join(root, "out" + num)
        gold = load_json(os.path.join(self.dir, "正解", "正解.json"))["期1"]
        self.gold = {}
        for k in SINGLE:
            self.gold[k] = gold[k]
        monthly = gold["月次の売上高_当期"]
        for i, k in enumerate(MONTHLY):
            self.gold[k] = monthly[i] if monthly is not None else None
        self.trap = load_json(os.path.join(self.dir, "正解", "罠.json"))
        per = load_json(os.path.join(self.dir, "正解", "期.json"))
        self.start, self.end = d(per["当期の始まり"]), d(per["当期の終わり"])
        self.unused = load_json(os.path.join(self.dir, "正解", "使わない.json"))
        if isinstance(self.unused, dict):
            self.unused = [x for v in self.unused.values() for x in (v if isinstance(v, list) else [v])]
        self.unused = [os.path.basename(x) for x in self.unused]
        tags = load_json(os.path.join(self.out, "札.json"))["file"]
        self.tags = {os.path.basename(t["名"]): t for t in tags}
        self.answers = {r["項目"]: r for r in load_json(os.path.join(self.out, "答え.json"))["行"]}
        self.tables = {}

    def table(self, name):
        name = os.path.basename(name)
        if name not in self.tables:
            path = os.path.join(self.dir, "期1", name)
            self.tables[name] = read_table(path) if os.path.isfile(path) else None
        return self.tables[name]

    def cell(self, src):
        t = self.table(src["file"])
        r, c = src.get("行"), src.get("列")
        if t is None or not isinstance(r, int) or not isinstance(c, int):
            return None
        if r < 1 or c < 1 or r > len(t) or c > len(t[r - 1]):
            return None
        return cell_number(t[r - 1][c - 1])

    def label(self, src):
        tag = self.tags.get(os.path.basename(src["file"]))
        lab = dict(tag.get("既定") or {})
        for axis, key in (("列", "列"), ("行", "行")):
            for ex in tag.get("例外") or []:
                if ex.get("軸") == axis and src[key] in (ex.get("番号") or []):
                    for f in ("期", "単位", "性質", "範囲"):
                        if f in ex:
                            lab[f] = ex[f]
        return lab

    def period_ok(self, item, p, multi):
        before = self.start - datetime.timedelta(days=1)
        kind = p.get("種類")
        try:
            if kind == "期間":
                a, b = d(p["始まり"]), d(p["終わり"])
            elif kind == "時点":
                t = d(p["日"])
            else:
                return False
        except (KeyError, ValueError, TypeError):
            return False
        if item.startswith("月次の売上高_当期_"):
            first, last = month_range(self.start, int(item[-2:]))
            return kind == "期間" and a == first and b == last
        if item.endswith("_当期末"):
            return (kind == "時点" and t == self.end) or (kind == "期間" and b == self.end)
        if item.endswith("_前期末"):
            return (kind == "時点" and t in (before, self.start)) or (kind == "期間" and b == before)
        if item.endswith("_前期"):
            return kind == "期間" and b == before
        if item.endswith("_当期"):
            if kind != "期間":
                return False
            if a == self.start and b == self.end:
                return True
            return multi and a >= self.start and b <= self.end
        return False

    def check(self, item, value, sources, value_only=False):
        """通すなら None、止めるなら理由。"""
        total = 0
        if not sources:
            return "S1"
        for s in sources:
            n = self.cell(s) if isinstance(s, dict) and "file" in s else None
            if n is None:
                return "S1"
            total += n * s.get("倍率", 1) * s.get("符号", 1)
        if total != value:
            return "S1"
        if value_only:
            return None
        for s in sources:
            tag = self.tags.get(os.path.basename(s["file"]))
            if tag is None or tag.get("扱い") != "貯める":
                return "S7"
        labs = [self.label(s) for s in sources]
        multi = len(sources) >= 2
        for lab in labs:
            if lab.get("期") is None:
                return "S2"
        for lab in labs:
            if not self.period_ok(item, lab["期"], multi):
                return "S3"
        for s, lab in zip(sources, labs):
            u = lab.get("単位")
            if item == "期末の従業員数_当期末":
                if u != "人":
                    return "S4"
            elif u not in UNIT_SCALE or UNIT_SCALE[u] != s.get("倍率", 1):
                return "S4"
        for lab in labs:
            if lab.get("性質") != "実績":
                return "S5"
        if not multi and labs[0].get("範囲") != "全社":
            return "S6"
        return None


def main():
    root, out_path = sys.argv[1], sys.argv[2]
    rec = {
        "会社の数": 0, "行": 0, "無いと答えた": 0, "無いと答えて正解も無い": 0,
        "正しい行": 0, "正しい行を通した": 0, "正しい行を止めた": 0,
        "正しい行を止めた理由": {r: 0 for r in REASONS},
        "違う行": 0, "違う行を通した": 0,
        "値だけ見る照合": {"正しい行を通した": 0, "違う行を通した": 0, "M-罠を通した": 0, "M-ずらしを通した": 0, "決めの行を通した": 0},
        "決めの行": 0, "決めの行を通した": 0,
        "M-罠": 0, "M-罠を通した": 0, "M-罠を止めた理由": {r: 0 for r in REASONS},
        "M-ずらし": 0, "M-ずらしを通した": 0, "M-ずらしを止めた理由": {r: 0 for r in REASONS},
        "使わない file": 0, "使わない file が原本のままへ": 0,
        "正しい行の出どころの file": 0, "そのうち原本のままへ": 0, "そのうち札に無い": 0,
        "file の数": 0, "貯めるの数": 0, "人に聞く問い": 0, "貯めるで既定の期が無い": 0,
    }
    for num in COMPANIES:
        co = Company(root, num)
        rec["会社の数"] += 1
        decide = {x["項目"] for x in co.trap.get("決め", [])}
        used_files = set()
        for item in ITEMS:
            rec["行"] += 1
            ans = co.answers.get(item) or {"値": None, "出どころ": []}
            value, sources = ans.get("値"), ans.get("出どころ") or []
            gold = co.gold[item]
            if item in decide:
                rec["決めの行"] += 1
                if value is not None:
                    if co.check(item, value, sources) is None:
                        rec["決めの行を通した"] += 1
                    if co.check(item, value, sources, True) is None:
                        rec["値だけ見る照合"]["決めの行を通した"] += 1
            if value is None:
                rec["無いと答えた"] += 1
                if gold is None:
                    rec["無いと答えて正解も無い"] += 1
                continue
            why = co.check(item, value, sources)
            only = co.check(item, value, sources, True)
            if gold is not None and value == gold:
                rec["正しい行"] += 1
                if why is None:
                    rec["正しい行を通した"] += 1
                else:
                    rec["正しい行を止めた"] += 1
                    rec["正しい行を止めた理由"][why] += 1
                if only is None:
                    rec["値だけ見る照合"]["正しい行を通した"] += 1
                if only is None:
                    used_files.update(os.path.basename(s["file"]) for s in sources)
                # M-ずらし
                if len(sources) == 1 and only is None:
                    s = sources[0]
                    for dc in (1, -1):
                        s2 = dict(s, 列=s["列"] + dc)
                        n = co.cell(s2)
                        if n is not None and n != co.cell(s):
                            v2 = n * s2.get("倍率", 1) * s2.get("符号", 1)
                            rec["M-ずらし"] += 1
                            w2 = co.check(item, v2, [s2])
                            if w2 is None:
                                rec["M-ずらしを通した"] += 1
                            else:
                                rec["M-ずらしを止めた理由"][w2] += 1
                            if co.check(item, v2, [s2], True) is None:
                                rec["値だけ見る照合"]["M-ずらしを通した"] += 1
                            break
            else:
                rec["違う行"] += 1
                if why is None:
                    rec["違う行を通した"] += 1
                if only is None:
                    rec["値だけ見る照合"]["違う行を通した"] += 1
        for t in co.trap.get("罠", []):
            rec["M-罠"] += 1
            src = [{"file": t["file"], "行": t["行"], "列": t["列"], "倍率": 1, "符号": 1}]
            w = co.check(t["項目"], t["罠の値"], src)
            if w is None:
                rec["M-罠を通した"] += 1
            else:
                rec["M-罠を止めた理由"][w] += 1
            if co.check(t["項目"], t["罠の値"], src, True) is None:
                rec["値だけ見る照合"]["M-罠を通した"] += 1
        for name in co.unused:
            rec["使わない file"] += 1
            tag = co.tags.get(name)
            if tag is not None and tag.get("扱い") == "原本のまま":
                rec["使わない file が原本のままへ"] += 1
        for name in used_files:
            rec["正しい行の出どころの file"] += 1
            tag = co.tags.get(name)
            if tag is None:
                rec["そのうち札に無い"] += 1
            elif tag.get("扱い") != "貯める":
                rec["そのうち原本のままへ"] += 1
        for tag in co.tags.values():
            rec["file の数"] += 1
            if tag.get("扱い") == "貯める":
                rec["貯めるの数"] += 1
                rec["人に聞く問い"] += len(tag.get("人に聞く") or [])
                if (tag.get("既定") or {}).get("期") is None:
                    rec["貯めるで既定の期が無い"] += 1
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
