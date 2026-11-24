# -*- coding: utf-8 -*-
"""便 SV13 の照合と集計(封 explore/sv13/SEAL.md §2)。

使い方: python3 -I tally_sv13.py <explore の folder> <SV13 の根> <record.json の path>
SV13 の根の形は SV10 と同じ(r0・r1・r2〜r4・ask)。照合は SV12 の SetCompany(形 A・S10′)に S8・S9。
流れは tally_sv10.main を会社 18・19・20 に替えて走らせ、変異は tally_sv12.mutants と tally_sv11.text_mutants を当てる。記録は数だけ。
"""
import json
import os
import sys

EXPLORE, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
NUMS = ["18", "19", "20"]
sys.path.insert(0, os.path.join(EXPLORE, "sv12"))
sys.argv = ["", EXPLORE, os.path.dirname(ROOT), ROOT, os.devnull]
import tally_sv12 as V  # noqa: E402
T, tally, tally_sv10 = V.T, V.tally, V.tally_sv10
tally.COMPANIES = NUMS
tally_sv10.NUMS = NUMS


def main():
    T.TEXT_MODE = "A"
    keep = tally_sv10.TextCompany
    tally_sv10.TextCompany = V.SetCompany
    tally_sv10.OUT = os.path.join(ROOT, "work_tally", "flow.json")
    try:
        tally_sv10.main()
    finally:
        tally_sv10.TextCompany = keep
    flow = tally_sv10.load(tally_sv10.OUT)
    flow["聞く項目"] = sum(len({("月次" if a in tally.MONTHLY else a) for a in tally_sv10.ask_set(n)}) for n in NUMS)
    conv = os.path.join(ROOT, "r1", "conv")
    rec = {"流れ(S10′ + 形 A + S8 + S9)": flow, "足し漏れの変異(社ごと)": {}, "文の行": None}
    for i, n in enumerate(NUMS):
        rec["足し漏れの変異(社ごと)"]["社 %d" % (i + 1)] = V.mutants(conv, n)
    text = T.text_mutants()
    rec["文の行"] = {"文の行": text["文の行"],
                    "正しい値の升を形 A が止めた": text["正しい値の升を止めた"]["A"],
                    "差し替え(同じ単位の字が付いた数)": text["差し替え(同じ単位の字が付いた数)"],
                    "同じ単位の差し替えを形 A が通した": text["同じ単位の差し替えを通した"]["A"],
                    "差し替え(それ以外)": text["差し替え(それ以外)"],
                    "それ以外の差し替えを形 A が通した": text["それ以外の差し替えを通した"]["A"]}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
