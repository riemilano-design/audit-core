# -*- coding: utf-8 -*-
"""便 RD0 の照合と集計(封 explore/rd0/SEAL.md §2)。

使い方: python3 -I tally_rd0.py <explore の folder> <RD0 の根> <record.json の path>
RD0 の根の形は SV13 と同じ(co{n}・r0・r1・r2〜r4・ask)。会社は 21〜26、数える項目は封 §1 の 16 項目だけ。
照合は SV12 の SetCompany(文の行の形 A。S10′ は月次を数えないので当たらない)に S8・S9。S11 は当てない。
流れの元(r1/conv・r4/merged)は tally_sv10.main で作り、数えるのはこの script の中で行う。記録は数だけ。
"""
import json
import os
import sys

EXPLORE, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
NUMS = ["21", "22", "23", "24", "25", "26"]
sys.path.insert(0, os.path.join(EXPLORE, "sv12"))
sys.argv = ["", EXPLORE, os.path.dirname(ROOT), ROOT, os.devnull]
import tally_sv12 as V  # noqa: E402
T, tally, tally_sv10 = V.T, V.tally, V.tally_sv10
import tally_sv2  # noqa: E402

SCOPE = ["売上高_当期", "売上高_前期", "営業利益_当期", "営業利益_前期", "経常利益_当期", "当期純利益_当期",
         "減価償却費_当期", "現金及び預金_当期末", "流動資産合計_当期末", "資産合計_当期末", "短期借入金_当期末",
         "長期借入金_当期末", "負債合計_当期末", "純資産合計_当期末", "純資産合計_前期末", "期末の従業員数_当期末"]
tally.SINGLE = SCOPE
tally.MONTHLY = []
tally.ITEMS = SCOPE
tally.COMPANIES = NUMS
tally_sv10.NUMS = NUMS
tally_sv10.ROOT = ROOT


def main():
    T.TEXT_MODE = "A"
    keep = tally_sv10.TextCompany
    tally_sv10.TextCompany = V.SetCompany
    tally_sv10.OUT = os.path.join(ROOT, "work_tally", "flow_sv10_form.json")
    try:
        tally_sv10.main()  # r1/conv と r4/merged を作る
    finally:
        tally_sv10.TextCompany = keep
    conv = os.path.join(ROOT, "r1", "conv")
    g = {"会社": 0, "行": 0, "正解の在る行": 0, "正しい行": 0, "違う行": 0,
         "正解が在るのに無いと答えた": 0, "正解が無いのに答えた": 0, "無いと答えて正解も無い": 0,
         "正しい行(決めの行を除く)": 0, "そのうち S1〜S9 で止めた": 0,
         "違う行(決めの行を除く)": 0, "そのうち S1〜S9 を全部通った(資料に残る誤り)": 0,
         "決めの行で値の在る行": 0, "決めの行を S1〜S9 で止めた": 0,
         "違う行のうち単体か前期の値に当たる": 0, "そのうち S1〜S9 で止めた ": 0,
         "正解が無いのに答えた行のうち S1〜S9 を全部通った": 0, "聞く項目": 0,
         "正しい行を止めた理由": {}}
    for n in NUMS:
        g["会社"] += 1
        co = V.SetCompany(conv, n)
        marks = tally_sv10.load(os.path.join(ROOT, "r4", "merged", "out" + n, "紛れ.json"))["印"]
        ask = tally_sv10.ask_set(n) & set(SCOPE)
        g["聞く項目"] += len(ask)
        decide = {x["項目"] for x in co.trap.get("決め", [])}
        other = tally_sv10.load(os.path.join(co.dir, "正解", "他の読み.json"))
        for item in SCOPE:
            g["行"] += 1
            a = co.answers.get(item) or {}
            v, src = a.get("値"), a.get("出どころ") or []
            gold = co.gold[item]
            g["正解の在る行"] += gold is not None
            if v is None:
                g["正解が在るのに無いと答えた" if gold is not None else "無いと答えて正解も無い"] += 1
                continue
            w = tally_sv2.judge(co, marks, item, v, src)
            if w is None and item in ask:
                w = "S9"
            if gold is None:
                g["正解が無いのに答えた"] += 1
                g["正解が無いのに答えた行のうち S1〜S9 を全部通った"] += w is None
                continue
            g["正しい行" if v == gold else "違う行"] += 1
            if item in decide:
                g["決めの行で値の在る行"] += 1
                g["決めの行を S1〜S9 で止めた"] += w is not None
            elif v == gold:
                g["正しい行(決めの行を除く)"] += 1
                if w is not None:
                    g["そのうち S1〜S9 で止めた"] += 1
                    g["正しい行を止めた理由"][w] = g["正しい行を止めた理由"].get(w, 0) + 1
            else:
                g["違う行(決めの行を除く)"] += 1
                g["そのうち S1〜S9 を全部通った(資料に残る誤り)"] += w is None
                if v in (other.get(item) or []):
                    g["違う行のうち単体か前期の値に当たる"] += 1
                    g["そのうち S1〜S9 で止めた "] += w is not None
    g["単体か前期の値に当たる違う行のうち S1〜S9 で止めた"] = g.pop("そのうち S1〜S9 で止めた ")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
