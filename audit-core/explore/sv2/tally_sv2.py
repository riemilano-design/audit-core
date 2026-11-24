# -*- coding: utf-8 -*-
"""便 SV2 の照合と集計(封 explore/sv2/SEAL.md §2)。

使い方: python3 -I tally_sv2.py <sv0 の tally.py の folder> <SV1 の conv の根> <SV2 の根> <record.json の path>
SV1 の conv の根は SV1 の答えを SV0 の形に直したもの(co{n}・out{n}/答え.json・札.json)。
SV2 の根の下に out{n}/紛れ.json。S1〜S7 は SV0 の照合をそのまま当て、通った行にだけ S8 を足す。
記録は数だけ。
"""
import json
import os
import sys

sys.path.insert(0, sys.argv[1])
import tally  # noqa: E402


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def marked(marks, src):
    name = os.path.basename(src["file"])
    for m in marks:
        if os.path.basename(str(m.get("file"))) != name:
            continue
        if src["行"] in (m.get("行") or []) and (not m.get("列") or src["列"] in m["列"]):
            return True
    return False


def judge(co, marks, item, value, sources):
    why = co.check(item, value, sources)
    if why is not None:
        return why
    if any(marked(marks, s) for s in sources):
        return "S8"
    return None


def main():
    conv, sv2, out_path = sys.argv[2], sys.argv[3], sys.argv[4]
    rec = {"会社の数": 0, "印の数": 0, "印の付いた升の数": 0,
           "正しい行": 0, "正しい行を S1〜S7 で止めた": 0, "正しい行を S8 で止めた": 0,
           "違う行": 0, "違う行を止めた": 0,
           "決めの行で値の在る行": 0, "決めの行を止めた": 0, "決めの行を S8 で止めた": 0,
           "M-罠": 0, "M-罠を止めた": 0, "M-罠を S8 で止めた": 0,
           "S1〜S7 で通った M-罠": 0, "そのうち S8 で止めた": 0}
    for num in tally.COMPANIES:
        co = tally.Company(conv, num)
        rec["会社の数"] += 1
        marks = load(os.path.join(sv2, "out" + num, "紛れ.json")).get("印") or []
        rec["印の数"] += len(marks)
        for m in marks:
            t = co.table(str(m.get("file")))
            for r in m.get("行") or []:
                if t is None or not isinstance(r, int) or r < 1 or r > len(t):
                    continue
                cols = m.get("列") or range(1, len(t[r - 1]) + 1)
                rec["印の付いた升の数"] += sum(1 for c in cols if isinstance(c, int) and 1 <= c <= len(t[r - 1])
                                            and tally.cell_number(t[r - 1][c - 1]) is not None)
        decide = {x["項目"] for x in co.trap.get("決め", [])}
        for item in tally.ITEMS:
            ans = co.answers.get(item) or {}
            value, sources = ans.get("値"), ans.get("出どころ") or []
            if value is None:
                continue
            w = judge(co, marks, item, value, sources)
            if item in decide:
                rec["決めの行で値の在る行"] += 1
                if w is not None:
                    rec["決めの行を止めた"] += 1
                if w == "S8":
                    rec["決めの行を S8 で止めた"] += 1
            gold = co.gold[item]
            if gold is not None and value == gold:
                rec["正しい行"] += 1
                if w == "S8":
                    rec["正しい行を S8 で止めた"] += 1
                elif w is not None:
                    rec["正しい行を S1〜S7 で止めた"] += 1
            else:
                rec["違う行"] += 1
                if w is not None:
                    rec["違う行を止めた"] += 1
        for t in co.trap.get("罠", []):
            rec["M-罠"] += 1
            src = [{"file": t["file"], "行": t["行"], "列": t["列"], "倍率": 1, "符号": 1}]
            base = co.check(t["項目"], t["罠の値"], src)
            w = judge(co, marks, t["項目"], t["罠の値"], src)
            if w is not None:
                rec["M-罠を止めた"] += 1
            if w == "S8":
                rec["M-罠を S8 で止めた"] += 1
            if base is None:
                rec["S1〜S7 で通った M-罠"] += 1
                if w == "S8":
                    rec["そのうち S8 で止めた"] += 1
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
