# -*- coding: utf-8 -*-
"""便 TR4 の集計(封 §4)。記録は数だけ。

使い方: python3 -I tally_tr4.py <TR0 の根> <TR4 の根> <record.json の path>
check/・mut/・tag/・regress.json を読み、言い過ぎは judge_tr4(読みにも札にも依らない判定)で数える。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_tr4 as J  # noqa: E402

TR0, TR4, OUT = sys.argv[1:4]
NUMS = [str(i) for i in range(31, 42)]
UNITN = {"％": "%", "名": "人"}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    g = {"資料": len(NUMS), "札": 0, "資料に見つからない札": 0, "機械が拾った数": 0, "札の付かない数": 0,
         "区分(札)": {"確認済み": 0, "要修正・精査": 0, "軽量確認": 0, "人の判断が必要": 0, "点検していない": 0},
         "要修正・精査の訳": {}, "点検していない(札)の訳": {}, "言い過ぎ": 0,
         "原文の抜粋を欠く(確認済み・点検していない)": 0,
         "誤り": {k: {"入れた": 0, "止めた": 0} for k in "abcde"}, "誤り b・d の内訳": {}, "誤り a の止めの訳": {},
         "回帰": load(os.path.join(TR4, "regress.json"))}
    for k in ("b", "d"):
        g["誤り b・d の内訳"][k] = {"食い違いで止めた": 0, "ほかの訳で止めた": 0, "確認済みのまま(抜粋に出た)": 0, "確認済みのまま(抜粋なし)": 0}
    for n in NUMS:
        mat = {(m["項目"], m["期"]): m["値"] for m in load(os.path.join(TR0, "mat", n + ".json"))["項目"]}
        rows = load(os.path.join(TR4, "check", n + ".json"))
        g["札"] += len(load(os.path.join(TR4, "tag", n + ".json")).get("札") or [])
        for r in rows:
            tagged = r.get("札") is not None
            if "行" in r:
                g["機械が拾った数"] += 1
            if not tagged:
                g["札の付かない数"] += 1
            else:
                g["区分(札)"][r["区分"]] += 1
                if r["訳"] == "札の数が資料に見つからない":
                    g["資料に見つからない札"] += 1
                if r["区分"] == "要修正・精査":
                    g["要修正・精査の訳"][r["訳"]] = g["要修正・精査の訳"].get(r["訳"], 0) + 1
                    if "字" in r:
                        u = UNITN.get(r["札"].get("単位"), r["札"].get("単位"))
                        g["言い過ぎ"] += J.is_correct(r["字"], r["値"], u, mat)
                if r["区分"] == "点検していない":
                    g["点検していない(札)の訳"][r["訳"]] = g["点検していない(札)の訳"].get(r["訳"], 0) + 1
            if r["区分"] in ("確認済み", "点検していない") and "行" in r and not r.get("抜粋"):
                g["原文の抜粋を欠く(確認済み・点検していない)"] += 1
        m = load(os.path.join(TR4, "mut", n + ".json"))
        for k, v in m.items():
            g["誤り"][k]["入れた"] += 1
            g["誤り"][k]["止めた"] += bool(v["止めた"])
            if k == "a" and v["止めた"]:
                g["誤り a の止めの訳"][v["訳"]] = g["誤り a の止めの訳"].get(v["訳"], 0) + 1
            if k in ("b", "d"):
                d = g["誤り b・d の内訳"][k]
                if v["止めた"]:
                    d["食い違いで止めた" if v.get("食い違いで止めた") else "ほかの訳で止めた"] += 1
                else:
                    d["確認済みのまま(抜粋に出た)" if v.get("抜粋") else "確認済みのまま(抜粋なし)"] += 1
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
