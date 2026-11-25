# -*- coding: utf-8 -*-
"""便 TR11 の補足(結果を見てから足した)。直した report11b で点検レポートを書き直し、引く升の数と印の数を社ごとに比べる。
足す側に印が付いた行(同じ升が別の項目で引かれる升)の数も数える。書くもの: <TR11>/report_fixed/{n}.html・<TR11>/out/extra.json
使い方: python3 -E extra_tr11.py <TR11 の根>
"""
import json
import os
import sys

ROOT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("tr2", "tr4", "tr5", "tr6", "tr7", "tr8", "tr9", "tr10"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
sys.path.insert(0, HERE)
import flow_tr11 as F  # noqa: E402

out = {}
for n in range(51, 57):
    with open(os.path.join(ROOT, "ledger", "%d.json" % n), encoding="utf-8") as f:
        lg = json.load(f)
    with open(os.path.join(ROOT, "doc", "%d.md" % n), encoding="utf-8") as f:
        md = f.read()
    with open(os.path.join(ROOT, "tag", "%d.json" % n), encoding="utf-8") as f:
        tags = json.load(f).get("札") or []
    rows = F.K.check_doc(md, tags, lg["値"], lg["出どころ"])
    neg = sum(1 for r in rows if r["区分"] == "確認済み" for s in r.get("出どころ") or [] if int(s.get("符号") or 1) == -1)
    old, new = F.report11(n, rows, "第 %d 社の資料" % n), F.report11b(n, rows, "第 %d 社の資料" % n)
    os.makedirs(os.path.join(ROOT, "report_fixed"), exist_ok=True)
    with open(os.path.join(ROOT, "report_fixed", "%d.html" % n), "w", encoding="utf-8") as f:
        f.write(new)
    out[n] = {"引く升": neg, "封の印": old.count("(引く)"), "直した印": new.count("(引く)")}
with open(os.path.join(ROOT, "out", "extra.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
