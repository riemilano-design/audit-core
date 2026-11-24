# -*- coding: utf-8 -*-
"""便 TR0 の集計(封 §6)。記録は数だけ。

使い方: python3 -I tally_tr0.py <TR0 の根> <record.json の path>
check/・check_mut/・mut/・state/・read/{n}/読み.json を読む。正解(XBRL)は読まない(材料の値を正とする。封 §8)。
「補足」の欄は、結果を見てから足した数(封 §6 に無い)。
"""
import json
import os
import re
import sys

ROOT, OUT = sys.argv[1], sys.argv[2]
NUMS = [str(i) for i in range(31, 42)]
SCALE = {"円": 1, "千円": 1000, "百万円": 1000000, "億円": 100000000}
OK = ("照合を通った", "人が画面で決めた")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def digits(s):
    return re.sub(r"\D", "", str(s or ""))


def same_as_material(r, st):
    """封 §6 の言い過ぎの判定: 拾った読みのまま、資料の数が材料の値と資料の桁で同じか(この script で別に計算)。"""
    keys = (r.get("info") or {}).get("keys") or []
    vals = [st.get(k, {}).get("値") for k in keys]
    if not keys or any(v is None for v in vals):
        return False
    u = r["単位"]
    if u in ("人", "名"):
        return abs(r["値"]) == vals[0]
    if u not in SCALE and r["種類"] != "ratio_change":
        return False
    if r["種類"] == "single_value":
        return round(vals[0] / SCALE[u]) == round(r["値"])
    if r["種類"] == "difference":
        d = round((vals[0] - vals[1]) / SCALE[u])
        return d == round(r["値"] * (r.get("符号") or 1)) or (r.get("符号") is None and abs(d) == round(abs(r["値"])))
    if r["種類"] == "ratio_change" and vals[1]:
        p = round((vals[0] - vals[1]) / abs(vals[1]) * 100, 1)
        return p == round(r["値"] * (r.get("符号") or 1), 1) or (r.get("符号") is None and abs(p) == round(abs(r["値"]), 1))
    return False


def any_material_reading(r, st):
    """補足: 資料の数が、その項目の材料の値(当期・前期)か増減額のどれかと、資料の桁で同じか。"""
    if r.get("項目") is None or r["単位"] not in SCALE:
        return False
    vals = [s["値"] for s in st.values() if s.get("項目") == r["項目"] and s.get("値") is not None]
    cands = set(round(v / SCALE[r["単位"]]) for v in vals)
    for a in vals:
        for b in vals:
            cands.add(round(abs(a - b) / SCALE[r["単位"]]))
    return round(abs(r["値"])) in cands


def main():
    g = {"資料": len(NUMS), "拾った数": 0, "項目に結べて照合した数": 0,
         "区分": {"確認済み": 0, "要確認": 0, "人の判断が必要": 0, "点検していない": 0},
         "要確認のうち資料の数が材料の値と同じ(言い過ぎ)": 0,
         "入れた誤り": 0, "入れた誤りのうち要確認": 0, "入れた誤りの種類": {},
         "読む席": 0, "読みが無い・形が読めない席": 0, "読む席が直すべきに挙げた数": 0,
         "入れた誤りのうち直すべきに挙げた": 0, "確認済みの数を直すべきに挙げた": 0,
         "確認済みの行で照合の一致か項目の状態を欠く": 0,
         "補足": {"要確認のうち、材料の値か増減額のどれかと資料の桁で同じ(拾い方の読み違い)": 0,
                 "誤りを入れていない要確認を直すべきに挙げた": 0}}
    for n in NUMS:
        st = load(os.path.join(ROOT, "state", n + ".json"))["状態"]
        recs = load(os.path.join(ROOT, "check", n + ".json"))
        g["拾った数"] += len(recs)
        for r in recs:
            g["区分"][r["区分"]] += 1
            if r["区分"] != "点検していない":
                g["項目に結べて照合した数"] += 1
            if r["区分"] == "要確認":
                g["要確認のうち資料の数が材料の値と同じ(言い過ぎ)"] += same_as_material(r, st)
                g["補足"]["要確認のうち、材料の値か増減額のどれかと資料の桁で同じ(拾い方の読み違い)"] += any_material_reading(r, st)
        muts = load(os.path.join(ROOT, "mut", n + ".json"))
        mrecs = load(os.path.join(ROOT, "check_mut", n + ".json"))
        at = {(r["行"], r["始め"]): r for r in mrecs}
        for m in muts:
            g["入れた誤り"] += 1
            g["入れた誤りの種類"][m["種類"]] = g["入れた誤りの種類"].get(m["種類"], 0) + 1
            r = at.get((m["行"], m["始め"]))
            g["入れた誤りのうち要確認"] += r is not None and r["区分"] == "要確認"
        for recs_ in (recs, mrecs):
            for r in recs_:
                if r["区分"] != "確認済み":
                    continue
                info = r.get("info") or {}
                keys = info.get("keys") or []
                sts = [st.get(k, {}).get("状態") for k in keys]
                matched = (abs(r["値"]) == info.get("元")) if r["単位"] in ("人", "名") else info.get("engine") == "GROUNDED"
                if not matched or not keys or any(s not in OK for s in sts):
                    g["確認済みの行で照合の一致か項目の状態を欠く"] += 1
        p = os.path.join(ROOT, "read", n, "読み.json")
        g["読む席"] += 1
        try:
            fix = load(p).get("直すべき数") or []
        except (OSError, ValueError, AttributeError):
            g["読みが無い・形が読めない席"] += 1
            continue
        fd = [digits(x.get("資料の数")) for x in fix if isinstance(x, dict)]
        g["読む席が直すべきに挙げた数"] += len(fd)
        injected = {digits(m["入れた字"]) for m in muts}
        g["入れた誤りのうち直すべきに挙げた"] += sum(1 for m in muts if digits(m["入れた字"]) in fd)
        okd = {digits(r["字"]) for r in mrecs if r["区分"] == "確認済み"}
        flag = {digits(r["字"]) for r in mrecs if r["区分"] == "要確認"} - injected
        g["確認済みの数を直すべきに挙げた"] += sum(1 for d in fd if d in okd and d not in injected and d not in flag)
        g["補足"]["誤りを入れていない要確認を直すべきに挙げた"] += sum(1 for d in fd if d in flag)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
