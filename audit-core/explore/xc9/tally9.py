# -*- coding: utf-8 -*-
u"""便 XC9 の数え: 席の答え(scratchpad の <頭><組>_0.json)を置いて採点し、数だけを record.json に書く。
使い方: tally9.py 答えの置き場 作りの組,… 判定の組,…(作りは d・判定は h)。天井(oracle9)も並べて数える。"""
import collections, importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("o9", os.path.join(HERE, "oracle9.py")); O = importlib.util.module_from_spec(spec); spec.loader.exec_module(O)
m = O.m
od = collections.OrderedDict
KEYS = (u"T", u"置いた", u"付けない", u"形で落とした・塊の番号", u"形で落とした・塊の順", u"形で落とした・タグの対", u"形で落とした・置いた文の fact と交わる",
        u"答えの TextBlock", u"規則で置いた TextBlock(置き場が答えと同じ)", u"席・答えと同じ", u"席・置き場は同じで属性が違う", u"席・置き場が違う", u"天井・答えと同じ")


def run(base, head, nums):
    dev, held = m.C1.split()
    rows = []
    for n, p, pp in [x for x in dev + held if x[0] in nums]:
        entries = m.B.load_package(p); cur = m.B.build_files(entries); prv = m.B.build_files(m.B.load_package(pp))
        sc, tmap, bmap, pt = m.build_screens(cur, prv, entries)
        ans = m.load_answers(base, head, n)
        added, c = m.place_answers(cur, tmap, bmap, pt, ans)
        c.update(m.score(cur, added, pt)); c[u"T"] = len(tmap)
        oadd, _oc = m.place_answers(cur, tmap, bmap, pt, O.oracle(cur, tmap, bmap))
        c[u"天井・答えと同じ"] = m.score(cur, oadd, pt)[u"席・答えと同じ"]
        rows.append(od([(u"番号", n)] + [(k, c.get(k, 0)) for k in KEYS]))
    t = od((k, sum(r[k] for r in rows)) for k in KEYS)
    wrong = t[u"席・置き場は同じで属性が違う"] + t[u"席・置き場が違う"]
    t[u"席の誤り"] = wrong
    t[u"席の誤りの割合"] = round(wrong / t[u"置いた"], 4) if t[u"置いた"] else 0.0
    t[u"天井のうち席が同じに置いた割合"] = round(t[u"席・答えと同じ"] / t[u"天井・答えと同じ"], 4) if t[u"天井・答えと同じ"] else 0.0
    t[u"TextBlock の覆い: 規則だけ"] = round(t[u"規則で置いた TextBlock(置き場が答えと同じ)"] / t[u"答えの TextBlock"], 4)
    t[u"TextBlock の覆い: 規則と席"] = round((t[u"規則で置いた TextBlock(置き場が答えと同じ)"] + t[u"席・答えと同じ"]) / t[u"答えの TextBlock"], 4)
    return t, rows


def main():
    base, dv, hd = sys.argv[1], [int(x) for x in sys.argv[2].split(",")], [int(x) for x in sys.argv[3].split(",")]
    td, rd = run(base, "d", dv)
    th, rh = run(base, "h", hd)
    j = od()

    def judge(k, pred, got, ok):
        j[k] = od([(u"予測", pred), (u"出た", got), (u"判定", u"当たり" if ok else u"外れ")])
    judge("XC9-1", u"席の誤り(置き場が違う + 属性が違う)は席の置いた節の 10% 以下", th[u"席の誤りの割合"], th[u"席の誤りの割合"] <= 0.10)
    judge("XC9-2", u"天井のうち席が答えと同じに置いた割合は 80% 以上", th[u"天井のうち席が同じに置いた割合"], th[u"天井のうち席が同じに置いた割合"] >= 0.8)
    d = round(th[u"TextBlock の覆い: 規則と席"] - th[u"TextBlock の覆い: 規則だけ"], 4)
    judge("XC9-3", u"TextBlock の覆いは席で 15 ポイント以上ふえる", d, d >= 0.15)
    f = th[u"形で落とした・塊の番号"] + th[u"形で落とした・塊の順"] + th[u"形で落とした・タグの対"] + th[u"形で落とした・置いた文の fact と交わる"]
    judge("XC9-4", u"機械の確かめで落とした答えは 40 以下", f, f <= 40)
    rec = od([(u"便", u"XC9(規則で置けなかった TextBlock を AI の席が塊の範囲で置く)"), (u"集計 作りの組", td), (u"集計 判定の組", th),
              (u"予測の判定", j), (u"組ごと(番号と数だけ)", od([("dev", rd), ("held", rh)]))])
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as fo:
        json.dump(rec, fo, ensure_ascii=False, indent=1)
    print(json.dumps(od([("dev", td), ("held", th), ("judge", j)]), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
