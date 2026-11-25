# -*- coding: utf-8 -*-
"""便 TR10 の補足(結果を見てから足した。封 §3 に無い)。0 の数を自分の欠陥として疑って確かめる。

1. 台帳の値が、TR2 の素材の正解(期 2)と全部同じか。
2. 確認済みの数が、札に依らない判定(judge_tr4.is_correct・本文の単位)でも正しい数か。
3. 資料の数字の字のうち、拾わなかったものの訳(見出しの番号・題の会社の番号のほかに在るか)。
4. 項目の隠し (d) の止まらなかった形: 数の近くに項目の字が在ったか。
使い方: python3 -I extra_tr10.py <TR2 の根> <TR10 の根>
"""
import json
import os
import re
import sys

TR2, ROOT = sys.argv[1:3]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_tr10 as K  # noqa: E402

N, J, T = K.N, K.J, K.T
out = {"台帳と正解が違う": 0, "台帳の値": 0, "確認済み": 0, "確認済みで判定が正しい数でない": 0, "拾わなかった字": 0,
       "拾わなかった字で見出しの番号か題の番号でない": 0, "d 止まらなかった": 0, "d そのうち数の近くに項目の字が無い": 0}
for n in range(51, 57):
    with open(os.path.join(ROOT, "ledger", "%d.json" % n), encoding="utf-8") as f:
        lg = json.load(f)
    with open(os.path.join(TR2, "co%d" % n, "正解", "値.json"), encoding="utf-8") as f:
        truth = json.load(f)["期2"]
    out["台帳の値"] += len(lg["値"])
    out["台帳と正解が違う"] += sum(lg["値"][k] != truth[k] for k in truth)
    with open(os.path.join(ROOT, "doc", "%d.md" % n), encoding="utf-8") as f:
        md = f.read()
    with open(os.path.join(ROOT, "tag", "%d.json" % n), encoding="utf-8") as f:
        tags = json.load(f)["札"]
    mat = {tuple(k.split("@")): v for k, v in lg["値"].items()}
    rows = K.check_doc(md, tags, lg["値"], lg["出どころ"])
    for r in rows:
        if r["区分"] == "確認済み":
            out["確認済み"] += 1
            out["確認済みで判定が正しい数でない"] += not J.is_correct(r["字"], r["値"], T.unit_at(md, r["行"], r["始め"]), mat)
    recs = N.extract_all(md)
    for i, line in enumerate(md.split("\n")):
        for m in re.finditer(r"\d[\d,]*(\.\d+)?", line):
            if any(r["行"] == i and r["始め"] <= m.start() < r["終わり"] for r in recs):
                continue
            out["拾わなかった字"] += 1
            head = line.startswith("#") and (re.match(r"#+\s*(\d+\.|\(\d+\)|第\s*\d+\s*社)", line[:m.end() + 3]) or "社" in line[m.end():m.end() + 3])
            out["拾わなかった字で見出しの番号か題の番号でない"] += not head
    recmap = {(r["行"], r["始め"]): r for r in recs}
    res = K.mutate_all(md, tags, rows, lg["値"], lg["出どころ"])
    ok = [r for r in rows if r["区分"] == "確認済み"]
    dl = [r for r in ok if r["札"]["種類"] == "金額" and r["場所"] == "文" and r["札"].get("単位") in K.SCALE
          and any(it != r["札"]["項目"] and "%s@%s" % (it, r["札"]["期"]) in lg["値"]
                  and K.norm(K.fmt(lg["値"]["%s@%s" % (it, r["札"]["期"])], r["札"]["単位"], r["字"])) != K.norm(r["字"]) for it in K.ORDER)]
    assert len(dl) == len(res["d"])
    for r, x in zip(dl, res["d"]):
        if not x["止めた"]:
            out["d 止まらなかった"] += 1
            out["d そのうち数の近くに項目の字が無い"] += N.item_word(recmap[(r["行"], r["始め"])])[0] is None
with open(os.path.join(ROOT, "out", "extra.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
