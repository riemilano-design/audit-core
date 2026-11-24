# -*- coding: utf-8 -*-
"""便 TR5 の補足(結果を見てから足した。封 §3 に無い)。表の期の隠しが 1 つも止まらなかった訳を確かめる。

check_tr5.mutate_all の (b) は、替えた札の「何番目」を 1 に固定する。表の行では、替えた数(前期の値)が
同じ行の前期の欄にも在るので、札は前期の欄の数を指し、替えた当期の欄の数には札が付かない。
ここでは (b) の表の形それぞれについて、
  1. 替えた後の資料で、替えた位置の数が「点検していない」に出るか(札の無い数として)
  2. 「何番目」を替えた位置に合わせて入れ直すと、期の食い違いで止まるか
を数える。(d) の止まらなかった形も、数の近くに項目の字が在ったかで分ける。
使い方: python3 -I extra_b_tr5.py <audit-core> <TR0> <TR1> <TR3> <TR4> <TR5>
"""
import copy
import json
import os
import sys

AC, TR0, TR1, TR3, TR4, TR5 = sys.argv[1:7]
sys.argv = [sys.argv[0]] + [AC, TR0, TR1, TR3, TR4, TR5]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_tr5 as T5  # noqa: E402

K, N, C = T5.K, T5.N, T5.C


def nth(md, line, start, text):
    s = md.split("\n")[line]
    return s[:start].count(text) + 1 if text else 1


def main():
    out = {}
    for name, root in (("新しい", TR5), ("TR4", TR4)):
        g = {"表の (b)": 0, "替えた数が点検していないに出た": 0, "何番目を合わせると止めた": 0,
             "(d) 止まらなかった": 0, "そのうち数の近くに項目の字が無い": 0}
        for n in C.NUMS:
            A = K.load(os.path.join(TR1, "A", n + ".json"))
            with open(os.path.join(root, "doc", n + ".md"), encoding="utf-8") as f:
                md = f.read()
            tags = K.load(os.path.join(root, "tag", n + ".json")).get("札") or []
            rows = T5.check5(md, tags, A)
            recs = {(r["行"], r["始め"]): r for r in N.extract_all(md)}
            for r in rows:
                if r["区分"] != "確認済み":
                    continue
                t = r["札"]
                if r["場所"] == "表" and t["種類"] == "金額" and t["期"] in ("当期", "当期末") and t.get("単位") in K.SCALE:
                    pk = "%s@%s" % (t["項目"], C.CTX[C.periods(t["項目"])[1]])
                    if pk in A["map"]:
                        new = K.fmt(A["map"][pk]["値"], t["単位"], r["字"])
                        if K.norm(new) != K.norm(r["字"]):
                            g["表の (b)"] += 1
                            md2 = K.replace_at(md, r["行"], r["始め"], r["字"], new)
                            t2 = copy.deepcopy(tags)
                            t2[r["札の番号"]].update({"字": new, "期": C.periods(t["項目"])[1], "何番目": 1})
                            rows2 = T5.check5(md2, t2, A)
                            g["替えた数が点検していないに出た"] += any(
                                x["区分"] == "点検していない" and x.get("札") is None and x.get("行") == r["行"]
                                and x.get("始め") == r["始め"] for x in rows2)
                            t3 = copy.deepcopy(t2)
                            t3[r["札の番号"]]["何番目"] = nth(md2, r["行"], r["始め"], new)
                            r3 = next(x for x in T5.check5(md2, t3, A) if x.get("札の番号") == r["札の番号"])
                            g["何番目を合わせると止めた"] += r3["区分"] != "確認済み"
            res = K.load(os.path.join(TR5, "out", name, n + ".json"))
            ok = [r for r in rows if r["区分"] == "確認済み"]
            dl = [r for r in ok if r["札"]["種類"] == "金額" and r["場所"] == "文" and r["札"].get("単位") in K.SCALE
                  and r["札"]["期"] in C.CTX]
            # mutate_all は (d) を作れた札だけを並べる。作れたかを同じ式で決め直して、止まらなかった札と対にする
            made = [r for r in dl if any(
                it != r["札"]["項目"] and "%s@%s" % (it, C.CTX[r["札"]["期"]]) in A["map"]
                and K.norm(K.fmt(A["map"]["%s@%s" % (it, C.CTX[r["札"]["期"]])]["値"], r["札"]["単位"], r["字"])) != K.norm(r["字"])
                for it in K.ORDER)]
            assert len(made) == len(res["誤り"]["d"]), (name, n)
            for r, x in zip(made, res["誤り"]["d"]):
                if not x["止めた"]:
                    g["(d) 止まらなかった"] += 1
                    g["そのうち数の近くに項目の字が無い"] += N.item_word(recs[(r["行"], r["始め"])])[0] is None
        out[name] = g
        print(name, g)
    K.dump(out, TR5, "out", "extra_b.json")


if __name__ == "__main__":
    main()
