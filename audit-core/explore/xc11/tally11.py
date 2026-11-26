# -*- coding: utf-8 -*-
u"""便 XC11 の数え: 席の答え(scratchpad の <頭><組>_<画面>.json)を置いて採点し、数だけを record.json に書く。
使い方: tally11.py 答えの置き場 作りの組,… 判定の組,…(作りは d・判定は h)。"""
import collections, importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("x11", os.path.join(HERE, "xc11.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
od = collections.OrderedDict
KEYS = (u"印", u"置いた", u"付けない", u"形で落とした・文脈が無い", u"形で落とした・要素がタクソノミに無い", u"形で落とした・要素が今年の定義に無い",
        u"形で落とした・置き場が無い", u"形で落とした・置いた fact と交わる", u"形で落とした・同じ置き場",
        u"答えの軸のメンバーの付いた文の fact", u"規則で置いた(置き場が答えと同じ)", u"席・答えと同じ", u"席・置き場は同じで属性が違う", u"席・置き場が違う")


def run(base, head, nums, names):
    dev, held = m.C1.split()
    rows = []
    for n, p, pp in [x for x in dev + held if x[0] in nums]:
        entries = m.B.load_package(p); cur = m.B.build_files(entries); prv = m.B.build_files(m.B.load_package(pp))
        sc, marks, forms, occ, res = m.build_screens(cur, prv, entries)
        ans = m.X8.load_answers(base, head, n)
        added, c = m.place_answers(cur, entries, marks, forms, occ, res, ans, names)
        c.update(m.score(cur, added, dict((k, [(s, e, None) for s, e in v]) for k, v in occ.items())))
        c[u"印"] = len(marks)
        rows.append(od([(u"番号", n)] + [(k, c.get(k, 0)) for k in KEYS]))
    t = od((k, sum(r[k] for r in rows)) for k in KEYS)
    wrong = t[u"席・置き場は同じで属性が違う"] + t[u"席・置き場が違う"]
    t[u"席の誤り"] = wrong
    t[u"席の誤りの割合"] = round(wrong / t[u"置いた"], 4) if t[u"置いた"] else 0.0
    t[u"覆い: 規則だけ"] = round(t[u"規則で置いた(置き場が答えと同じ)"] / t[u"答えの軸のメンバーの付いた文の fact"], 4) if t[u"答えの軸のメンバーの付いた文の fact"] else 0.0
    t[u"覆い: 規則と席"] = round((t[u"規則で置いた(置き場が答えと同じ)"] + t[u"席・答えと同じ"]) / t[u"答えの軸のメンバーの付いた文の fact"], 4) if t[u"答えの軸のメンバーの付いた文の fact"] else 0.0
    return t, rows


def main():
    base, dv, hd = sys.argv[1], [int(x) for x in sys.argv[2].split(",")], [int(x) for x in sys.argv[3].split(",")]
    names = m.X8.std_names()
    td, rd = run(base, "d", dv, names)
    th, rh = run(base, "h", hd, names)
    j = od()

    def judge(k, pred, got, ok):
        j[k] = od([(u"予測", pred), (u"出た", got), (u"判定", u"当たり" if ok else u"外れ")])
    judge("XC11-1", u"席の誤り(置き場が違う + 属性が違う)は席の置いた fact の 10% 以下", th[u"席の誤りの割合"], th[u"席の誤りの割合"] <= 0.10)
    d = round(th[u"覆い: 規則と席"] - th[u"覆い: 規則だけ"], 4)
    judge("XC11-2", u"軸のメンバーの付いた文の fact の覆いは席で 30 ポイント以上ふえる", d, d >= 0.30)
    rec = od([(u"便", u"XC11(表の中の軸のメンバーの付いた文の fact を AI の席が置く)"), (u"集計 作りの組", td), (u"集計 判定の組", th),
              (u"予測の判定", j), (u"組ごと(番号と数だけ)", od([("dev", rd), ("held", rh)]))])
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as fo:
        json.dump(rec, fo, ensure_ascii=False, indent=1)
    print(json.dumps(od([("dev", td), ("held", th), ("judge", j)]), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
