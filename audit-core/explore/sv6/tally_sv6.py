# -*- coding: utf-8 -*-
"""便 SV6 の照合と集計(封 explore/sv6/SEAL.md §2)。

使い方: python3 -I tally_sv6.py <explore の folder> <scratchpad の根> <record.json の path>
SV0 側(9・10・11): 答え・札・素材は <根>/sv1/conv、印(標準・種類を足したもの)は <根>/sv4/merged。
SV5 側(12・13・14): 答え・札・素材は <根>/sv5/r1/conv、印は <根>/sv5/r4/merged。
聞く印は <根>/sv6/out{n}/聞く.json。S1〜S8 は SV4 の形(tally_sv4.marked と tally_sv2.judge)、通った行にだけ S9。
記録は数だけ。
"""
import json
import os
import sys

EXPLORE, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = [sys.argv[0], EXPLORE]
sys.path.insert(0, os.path.join(EXPLORE, "sv0"))
sys.path.insert(0, os.path.join(EXPLORE, "sv2"))
sys.path.insert(0, os.path.join(EXPLORE, "sv4"))
import tally  # noqa: E402
import tally_sv2  # noqa: E402
import tally_sv4  # noqa: E402

tally_sv2.marked = tally_sv4.marked
GROUPS = {"SV0 側": (["9", "10", "11"], os.path.join(ROOT, "sv1", "conv"), os.path.join(ROOT, "sv4", "merged")),
          "SV5 側": (["12", "13", "14"], os.path.join(ROOT, "sv5", "r1", "conv"), os.path.join(ROOT, "sv5", "r4", "merged"))}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def ask_set(num):
    out = set()
    for r in load(os.path.join(ROOT, "sv6", "out" + num, "聞く.json")).get("項目") or []:
        if r.get("聞く") is True:
            name = r.get("項目")
            if name == "月次の売上高_当期":
                out.update(tally.MONTHLY)
            else:
                out.add(name)
    return out


def judge(co, marks, ask, item, value, sources):
    w = tally_sv2.judge(co, marks, item, value, sources)
    if w is not None:
        return w
    return "S9" if item in ask else None


def blank():
    return {"聞く項目": 0, "決めの行で値の在る行": 0, "決めの行を S1〜S8 で止めた": 0, "決めの行を S1〜S9 で止めた": 0,
            "正しい行(決めの行を除く)": 0, "そのうち S1〜S8 で止めた": 0, "そのうち S9 で止めた": 0,
            "違う行(決めの行を除く)": 0, "そのうち S1〜S8 を全部通った": 0, "そのうち S1〜S9 を全部通った": 0,
            "S1〜S8 で通った罠": 0, "そのうち S9 で止めた罠": 0}


def main():
    rec = {}
    for gname, (nums, conv, merged) in GROUPS.items():
        g = blank()
        for num in nums:
            co = tally.Company(conv, num)
            marks = load(os.path.join(merged, "out" + num, "紛れ.json"))["印"]
            ask = ask_set(num)
            g["聞く項目"] += len({("月次" if a in tally.MONTHLY else a) for a in ask})
            decide = {x["項目"] for x in co.trap.get("決め", [])}
            for item in tally.ITEMS:
                a = co.answers.get(item) or {}
                v, src = a.get("値"), a.get("出どころ") or []
                if v is None:
                    continue
                w8 = tally_sv2.judge(co, marks, item, v, src)
                w9 = judge(co, marks, ask, item, v, src)
                if item in decide:
                    g["決めの行で値の在る行"] += 1
                    g["決めの行を S1〜S8 で止めた"] += w8 is not None
                    g["決めの行を S1〜S9 で止めた"] += w9 is not None
                elif v == co.gold[item]:
                    g["正しい行(決めの行を除く)"] += 1
                    if w8 is not None:
                        g["そのうち S1〜S8 で止めた"] += 1
                    elif w9 == "S9":
                        g["そのうち S9 で止めた"] += 1
                else:
                    g["違う行(決めの行を除く)"] += 1
                    g["そのうち S1〜S8 を全部通った"] += w8 is None
                    g["そのうち S1〜S9 を全部通った"] += w9 is None
            for t in co.trap.get("罠", []):
                src = [{"file": t["file"], "行": t["行"], "列": t["列"], "倍率": 1, "符号": 1}]
                if tally_sv2.judge(co, marks, t["項目"], t["罠の値"], src) is None:
                    g["S1〜S8 で通った罠"] += 1
                    if t["項目"] in ask:
                        g["そのうち S9 で止めた罠"] += 1
        rec[gname] = g
    rec["合計"] = {k: rec["SV0 側"][k] + rec["SV5 側"][k] for k in blank()}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(rec["合計"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
