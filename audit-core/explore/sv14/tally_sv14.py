# -*- coding: utf-8 -*-
"""便 SV14 の照合と集計(封 explore/sv14/SEAL.md §1・§2)。

使い方: python3 -I tally_sv14.py <explore の folder> <scratchpad の根> <SV13 の根の写し> <SV10 の根の写し> <record.json の path>
SV12 の SetCompany(S1〜S6・日付の列・文の行の形 A・S10′)に、S11(円の項目を倍率 1000 以上の出どころから答えたら止める)を足した
S11Company。流れは tally_sv10.main を根と会社の番号を替えて走らせる(写しの中だけを書く)。記録は数だけ。
"""
import json
import os
import sys

EXPLORE, SCRATCH, FLOW13, FLOW10, OUT = sys.argv[1:6]
sys.path.insert(0, os.path.join(EXPLORE, "sv12"))
sys.argv = ["", EXPLORE, SCRATCH, FLOW13, os.devnull]
import tally_sv12 as V  # noqa: E402
T, tally, tally_sv10 = V.T, V.tally, V.tally_sv10
import tally_sv2  # noqa: E402  (tally_sv10 が path に足した sv2)

# SV0 の集計が理由ごとに数える欄に、S10・S11 を足す(sv0/tally.py は変えない)
tally.REASONS = tally.REASONS + [r for r in ("S10", "S11") if r not in tally.REASONS]
MODE = None  # None・"A"・"B"
HEADCOUNT = "期末の従業員数_当期末"


class S11Company(V.SetCompany):
    def has_detail(self):
        if not hasattr(self, "_detail"):
            self._detail = any(t.get("扱い") == "貯める" and self.date_col(name) is not None
                               for name, t in self.tags.items())
        return self._detail

    def s11(self, item, sources):
        if MODE is None or item == HEADCOUNT:
            return None
        if not any(not s.get("文") and s.get("倍率", 1) >= 1000 for s in sources):
            return None
        if MODE == "B" and not self.has_detail():
            return None
        return "S11"

    def check(self, item, value, sources, value_only=False):
        w = V.SetCompany.check(self, item, value, sources, value_only)
        if w is not None or value_only:
            return w
        return self.s11(item, sources)


def flow(root, nums, mode):
    global MODE
    MODE = mode
    T.TEXT_MODE = "A"
    tally.COMPANIES = nums
    tally_sv10.NUMS = nums
    tally_sv10.ROOT = root
    keep = tally_sv10.TextCompany
    tally_sv10.TextCompany = S11Company
    tally_sv10.OUT = os.path.join(root, "work_tally", "flow_sv14_%s.json" % (mode or "なし"))
    try:
        tally_sv10.main()
    finally:
        tally_sv10.TextCompany = keep
        MODE = None
    f = tally_sv10.load(tally_sv10.OUT)
    return {k: f[k] for k in ("正しい行", "違う行", "正しい行(決めの行を除く)", "そのうち S1〜S9 で止めた",
                              "違う行(決めの行を除く)", "そのうち S1〜S9 を全部通った(資料に残る誤り)",
                              "決めの行で値の在る行", "決めの行を S1〜S9 で止めた")}


def check_only(root, nums):
    global MODE
    g = {"S1〜S6・S10′ を通った正しい行": 0, "そのうち形 A が止めた": 0, "そのうち形 B が止めた": 0,
         "S1〜S6・S10′ を通った違う行": 0, "違う行のうち形 A が止めた": 0, "違う行のうち形 B が止めた": 0}
    T.TEXT_MODE = "A"
    for n in nums:
        co = S11Company(root, n)
        for item in tally.ITEMS:
            a = co.answers.get(item) or {}
            v, src = a.get("値"), a.get("出どころ") or []
            if v is None:
                continue
            MODE = None
            if V.judge(co, V.SetCompany, item, v, src) is not None:
                continue
            ok = v == co.gold[item]
            g["S1〜S6・S10′ を通った正しい行" if ok else "S1〜S6・S10′ を通った違う行"] += 1
            for m in ("A", "B"):
                MODE = m
                if co.s11(item, src) is not None:
                    g[("そのうち形 %s が止めた" if ok else "違う行のうち形 %s が止めた") % m] += 1
            MODE = None
    return g


def main():
    rec = {"流れ": {}, "照合だけ": {}}
    for name, root, nums in (("SV13 の流れ(社 18〜20)", FLOW13, ["18", "19", "20"]),
                             ("SV10 の流れ(社 15〜17)", FLOW10, ["15", "16", "17"])):
        rec["流れ"][name] = {("S11 なし" if m is None else "S11 形 " + m): flow(root, nums, m) for m in (None, "A", "B")}
    tally.COMPANIES = ["12", "13", "14"]
    for name, root in (("SV5 の元の file を見た席の答え(社 12〜14)", os.path.join(SCRATCH, "sv5", "r0")),
                       ("SV5 の貯めた行だけの席の答え(社 12〜14)", os.path.join(SCRATCH, "sv5", "r1", "conv"))):
        rec["照合だけ"][name] = check_only(root, ["12", "13", "14"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
