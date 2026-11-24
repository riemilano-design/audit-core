# -*- coding: utf-8 -*-
"""便 TR5: TR4 の札の点検に R1・R2 を足して点検し、誤りを札の全部に入れて止める割合を測る(封 §3)。AI を使わない。

使い方: python3 -I check_tr5.py <audit-core> <TR0 の根> <TR1 の根> <TR3 の根> <TR4 の根> <TR5 の根>
新しい資料(<TR5>/doc・tag)と TR4 の資料(<TR4>/doc・tag)の両方を点検し、<TR5>/out/{新しい|TR4}/{n}.json に書く。
回帰を <TR5>/out/regress.json に書く。照合は TR4 の check_tr4.check_doc(基準 A・engine を読むだけ)。
"""
import copy
import json
import os
import sys

AC, TR0, TR1, TR3, TR4, TR5 = sys.argv[1:7]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], AC, TR0, TR1, TR3, TR5]
sys.path.insert(0, os.path.join(AC, "explore", "tr4"))
sys.path.insert(0, HERE)
import check_tr4 as K  # noqa: E402
import numbers_tr4 as N  # noqa: E402
import judge_tr4 as J  # noqa: E402
import rules_tr5 as T  # noqa: E402

C = K.C


def check5(md, tags, A):
    rows = K.check_doc(md, tags, A)
    recs = {(r["行"], r["始め"]): r for r in N.extract_all(md)}
    located = [(recs[(r["行"], r["始め"])], r["札"], r["札の番号"]) for r in rows if r.get("札") is not None and "行" in r]
    hit1 = T.r1(md, located)
    for r in rows:
        if r.get("札") is None or "行" not in r or r["区分"] not in ("確認済み", "軽量確認"):
            continue
        rec = recs[(r["行"], r["始め"])]
        if r["札の番号"] in hit1:
            r.update({"区分": "要修正・精査", "訳": "同じ文に、同じ項目・同じ期の金額の札が 2 枚在る(R1)", "規則": "R1"})
            continue
        stop, why = T.r2(rec, r["札"])
        if stop:
            r.update({"区分": "要修正・精査", "訳": why + "(R2)", "規則": "R2"})
    return rows


def mutate_all(md, tags, rows, A):
    out = {"b": [], "d": [], "a2": []}
    ok = [r for r in rows if r["区分"] == "確認済み"]

    def run(md2, t2, idx):
        r2 = next(x for x in check5(md2, t2, A) if x.get("札の番号") == idx)
        return {"止めた": r2["区分"] != "確認済み", "訳": r2["訳"], "規則": r2.get("規則")}

    for r in ok:
        t = r["札"]
        if t["種類"] == "金額" and t["期"] in ("当期", "当期末") and t.get("単位") in K.SCALE:
            pk = "%s@%s" % (t["項目"], C.CTX[C.periods(t["項目"])[1]])
            if pk in A["map"]:
                new = K.fmt(A["map"][pk]["値"], t["単位"], r["字"])
                if K.norm(new) != K.norm(r["字"]):
                    t2 = copy.deepcopy(tags)
                    t2[r["札の番号"]].update({"字": new, "期": C.periods(t["項目"])[1], "何番目": 1})
                    res = run(K.replace_at(md, r["行"], r["始め"], r["字"], new), t2, r["札の番号"])
                    res["場所"] = r["場所"]
                    out["b"].append(res)
        if t["種類"] == "金額" and r["場所"] == "文" and t.get("単位") in K.SCALE and t["期"] in C.CTX:
            ctx = C.CTX[t["期"]]
            other = next((it for it in K.ORDER if it != t["項目"] and "%s@%s" % (it, ctx) in A["map"]
                          and K.norm(K.fmt(A["map"]["%s@%s" % (it, ctx)]["値"], t["単位"], r["字"])) != K.norm(r["字"])), None)
            if other:
                v = A["map"]["%s@%s" % (other, ctx)]["値"]
                new = K.fmt(v, t["単位"], r["字"])
                t2 = copy.deepcopy(tags)
                t2[r["札の番号"]].update({"字": new, "項目": other, "向き": "−" if v < 0 else "+", "何番目": 1})
                out["d"].append(run(K.replace_at(md, r["行"], r["始め"], r["字"], new), t2, r["札の番号"]))
        new = K.bump2(r["字"])
        t2 = copy.deepcopy(tags)
        t2[r["札の番号"]]["字"] = new
        out["a2"].append(run(K.replace_at(md, r["行"], r["始め"], r["字"], new), t2, r["札の番号"]))
    return out


def overflags(md, rows, mat):
    n = 0
    for r in rows:
        if r["区分"] == "要修正・精査" and "字" in r:
            n += J.is_correct(r["字"], r["値"], T.unit_at(md, r["行"], r["始め"]), mat)
    return n


def regress():
    g = {"TR3 の要修正・精査": 0, "そのうち本文の単位で正しい数": 0, "TR0 の要確認": 0, "そのうち本文の単位で正しい数(TR0)": 0}
    for n in C.NUMS:
        mat = {(m["項目"], m["期"]): m["値"] for m in K.load(os.path.join(TR0, "mat", n + ".json"))["項目"]}
        for root, key, cond in ((TR3, "", lambda r: r["区分"] == "要確認" and not r["info"].get("held")),
                                (TR0, "(TR0)", lambda r: r["区分"] == "要確認")):
            with open(os.path.join(root, "doc", n + ".md"), encoding="utf-8") as f:
                md = f.read()
            for r in K.load(os.path.join(root, "check", n + ".json")):
                if cond(r):
                    g["TR3 の要修正・精査" if not key else "TR0 の要確認"] += 1
                    g["そのうち本文の単位で正しい数" + key] += J.is_correct(r["字"], r["値"], T.unit_at(md, r["行"], r["始め"]), mat)
    return g


def main():
    for name, root in (("新しい", TR5), ("TR4", TR4)):
        for n in C.NUMS:
            A = K.load(os.path.join(TR1, "A", n + ".json"))
            mat = {(m["項目"], m["期"]): m["値"] for m in K.load(os.path.join(TR0, "mat", n + ".json"))["項目"]}
            with open(os.path.join(root, "doc", n + ".md"), encoding="utf-8") as f:
                md = f.read()
            tags = K.load(os.path.join(root, "tag", n + ".json")).get("札") or []
            rows = check5(md, tags, A)
            res = {"区分": {k: sum(r["区分"] == k for r in rows) for k in ("確認済み", "要修正・精査", "軽量確認", "点検していない")},
                   "R1": sum(r.get("規則") == "R1" for r in rows), "R2": sum(r.get("規則") == "R2" for r in rows),
                   "言い過ぎ": overflags(md, rows, mat), "札": len(tags),
                   "止めた行": [{"訳": r["訳"], "抜粋": r.get("抜粋")} for r in rows if r.get("規則")],
                   "誤り": mutate_all(md, tags, rows, A)}
            K.dump(res, TR5, "out", name, n + ".json")
            m = res["誤り"]
            print(name, n, res["区分"], "R1", res["R1"], "R2", res["R2"], "言い過ぎ", res["言い過ぎ"], "| b",
                  sum(x["止めた"] for x in m["b"]), "/", len(m["b"]), "d", sum(x["止めた"] for x in m["d"]), "/", len(m["d"]),
                  "a2", sum(x["止めた"] for x in m["a2"]), "/", len(m["a2"]))
    g = regress()
    K.dump(g, TR5, "out", "regress.json")
    print(g)


if __name__ == "__main__":
    main()
