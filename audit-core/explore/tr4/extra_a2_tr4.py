# -*- coding: utf-8 -*-
"""便 TR4 の補足(結果を見てから足した。封 §3 に無い): 誤り (a′) 本文の数の最後の桁を 2 変え、札の字も合わせる。
(a) は札を変えないので、全部「札の数が資料に見つからない」で止まり、照合で止まるかを見ていなかった。

使い方: python3 -I extra_a2_tr4.py <audit-core> <TR0 の根> <TR1 の根> <TR3 の根> <TR4 の根>
<TR4>/extra_a2.json に数だけを書く。
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_tr4 as K  # noqa: E402  (引数は check_tr4 と同じ順)

out = {"入れた": 0, "止めた": 0, "止めの訳": {}, "金額 1 つ": [0, 0], "増減額・増減率・人数": [0, 0]}
for n in K.C.NUMS:
    A = K.load(os.path.join(K.TR1, "A", n + ".json"))
    with open(os.path.join(K.OUT, "doc", n + ".md"), encoding="utf-8") as f:
        md = f.read()
    tags = K.load(os.path.join(K.OUT, "tag", n + ".json")).get("札") or []
    rows = K.check_doc(md, tags, A)
    for r in [x for x in rows if x["区分"] == "確認済み"]:
        new = K.bump2(r["字"])
        md2 = K.replace_at(md, r["行"], r["始め"], r["字"], new)
        t2 = copy.deepcopy(tags)
        t2[r["札の番号"]]["字"] = new
        r2 = next(x for x in K.check_doc(md2, t2, A) if x.get("札の番号") == r["札の番号"])
        stop = r2["区分"] != "確認済み"
        out["入れた"] += 1
        out["止めた"] += stop
        if stop:
            out["止めの訳"][r2["訳"]] = out["止めの訳"].get(r2["訳"], 0) + 1
        key = "金額 1 つ" if r["札"]["種類"] == "金額" else "増減額・増減率・人数"
        out[key][0] += 1
        out[key][1] += stop
K.dump(out, K.OUT, "extra_a2.json")
print(out)
