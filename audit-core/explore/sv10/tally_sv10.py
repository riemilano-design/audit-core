# -*- coding: utf-8 -*-
"""便 SV10 の照合と集計(封 explore/sv10/SEAL.md §2)。

使い方: python3 -I tally_sv10.py <explore の folder> <SV10 の根> <record.json の path>
SV10 の根の下: r0(SV7 の r0 の写し。答え.json は空)・r1(build_sv10.py の出力と、埋める席の out{n}/答え.json)・
r2〜r4(SV7 の写し)・ask/out{n}/聞く.json(SV8 の写し)。
照合は SV9 の DatedCompany に、文の行の扱いを足した TextCompany。流れの数え方は SV7 の tally_sv7.py と同じ。記録は数だけ。
"""
import json
import os
import re
import sys

EXPLORE, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
NUMS = ["15", "16", "17"]
for d in ("sv0", "sv1", "sv2", "sv4", "sv9"):
    sys.path.insert(0, os.path.join(EXPLORE, d))
sys.argv = ["", EXPLORE, ROOT, os.devnull]
import tally  # noqa: E402
tally.COMPANIES = NUMS
import tally_sv9  # noqa: E402
sys.argv = ["", os.path.join(EXPLORE, "sv0")]
import tally_sv1  # noqa: E402
sys.argv = ["", EXPLORE]
import tally_sv2  # noqa: E402
import tally_sv4  # noqa: E402

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
SCALES = (1, 1000, 10000, 1000000, 100000000)


def read_lines(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp932"):
        try:
            return raw.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return None


class TextCompany(tally_sv9.DatedCompany):
    """文の行(map に 文: true)を出どころにした答えを扱う。"""

    def cell(self, src):
        if not src.get("文"):
            return tally_sv9.DatedCompany.cell(self, src)
        if src.get("列") != 0:
            return None
        lines = read_lines(os.path.join(self.dir, "期1", os.path.basename(src["file"])))
        r = src.get("行")
        v = src.get("値")
        if lines is None or not isinstance(r, int) or r < 1 or r > len(lines) or not isinstance(v, int):
            return None
        for m in NUM.findall(lines[r - 1]):
            x = float(m.replace(",", ""))
            if any(round(x * s) == v for s in SCALES):
                return v
        return None

    def label(self, src):
        if src.get("文"):
            return dict(src.get("札") or {})
        return tally_sv9.DatedCompany.label(self, src)

    def check(self, item, value, sources, value_only=False):
        if not any(isinstance(s, dict) and s.get("文") for s in sources):
            return tally_sv9.DatedCompany.check(self, item, value, sources, value_only)
        # SV0 の check と同じ順。文の行に限って S7 を当てない。
        total = 0
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
            if s.get("文"):
                continue
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
            elif u not in tally.UNIT_SCALE or tally.UNIT_SCALE[u] != s.get("倍率", 1):
                return "S4"
        for lab in labs:
            if lab.get("性質") != "実績":
                return "S5"
        if not multi and labs[0].get("範囲") != "全社":
            return "S6"
        return None


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def ask_set(num):
    out = set()
    for r in load(os.path.join(ROOT, "ask", "out" + num, "聞く.json")).get("項目") or []:
        if r.get("聞く") is True:
            if r.get("項目") == "月次の売上高_当期":
                out.update(tally.MONTHLY)
            else:
                out.add(r.get("項目"))
    return out


def main():
    tally.Company = TextCompany
    r0, r1, r2, r3, r4 = (os.path.join(ROOT, x) for x in ("r0", "r1", "r2", "r3", "r4"))
    work = os.path.join(ROOT, "work_tally")
    os.makedirs(work, exist_ok=True)
    sys.argv = ["", "", r0, r1, os.path.join(work, "store.json")]
    tally_sv1.main()
    conv = os.path.join(r1, "conv")
    sys.argv = ["", "", conv, r2, r3, r4, os.path.join(work, "s8.json")]
    tally_sv4.main()
    g = {"文の行(足した数)": 0, "正しい行": 0, "違う行": 0, "無いと答えた": 0, "正解が在るのに無いと答えた": 0,
         "決めの行で値の在る行": 0, "決めの行を S1〜S9 で止めた": 0,
         "正しい行(決めの行を除く)": 0, "そのうち S1〜S9 で止めた": 0,
         "違う行(決めの行を除く)": 0, "そのうち S1〜S9 を全部通った(資料に残る誤り)": 0,
         "文の中の項目": 0, "文の中の項目を正しく出した": 0, "文の中の項目を正しく出して S1〜S9 を通った": 0}
    for num in NUMS:
        g["文の行(足した数)"] += sum(1 for v in load(os.path.join(r1, "map%s.json" % num)).values() if v.get("文"))
        co = TextCompany(conv, num)
        marks = load(os.path.join(r4, "merged", "out" + num, "紛れ.json"))["印"]
        ask = ask_set(num)
        decide = {x["項目"] for x in co.trap.get("決め", [])}
        texts = set(load(os.path.join(co.dir, "正解", "文の中.json")))
        for item in tally.ITEMS:
            a = co.answers.get(item) or {}
            v, src = a.get("値"), a.get("出どころ") or []
            gold = co.gold[item]
            if item in texts:
                g["文の中の項目"] += 1
            if v is None:
                g["無いと答えた"] += 1
                g["正解が在るのに無いと答えた"] += gold is not None
                continue
            g["正しい行" if v == gold else "違う行"] += 1
            w = tally_sv2.judge(co, marks, item, v, src)
            if w is None and item in ask:
                w = "S9"
            if item in texts and v == gold:
                g["文の中の項目を正しく出した"] += 1
                g["文の中の項目を正しく出して S1〜S9 を通った"] += w is None
            if item in decide:
                g["決めの行で値の在る行"] += 1
                g["決めの行を S1〜S9 で止めた"] += w is not None
            elif v == gold:
                g["正しい行(決めの行を除く)"] += 1
                g["そのうち S1〜S9 で止めた"] += w is not None
            else:
                g["違う行(決めの行を除く)"] += 1
                g["そのうち S1〜S9 を全部通った(資料に残る誤り)"] += w is None
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
