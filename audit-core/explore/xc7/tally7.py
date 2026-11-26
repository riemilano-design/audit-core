# -*- coding: utf-8 -*-
u"""便 XC7 の数え: 組ごとの席の答え(scratchpad)を採点し、数だけを record.json に書く。
使い方: tally7.py 答えの置き場 組の番号,…(作り) 組の番号,…(判定)。答えの file は <置き場>/<頭><組>_<画面>.json(作りは d・判定は h)。"""
import collections, importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("s7", os.path.join(HERE, "score7.py")); S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
od = collections.OrderedDict
KEYS = (u"答えの数の fact", u"規則で置いた中の答えの fact", u"印", u"答えの在る印", u"置いた", u"置いた・答えと同じ", u"置いた・答えと違う",
        u"置いた・答えが無い", u"形で落とした", u"付けない", u"付けない・答えが在る")


def group(base, head, pairs):
    rows = []
    for n in pairs:
        c = S.run(n, os.path.join(base, "%s%d" % (head, n)), verbose=False)
        rows.append(od([(u"番号", n)] + [(k, c.get(k, 0)) for k in KEYS]))
    t = od((k, sum(r[k] for r in rows)) for k in KEYS)
    wrong = t[u"置いた・答えと違う"] + t[u"置いた・答えが無い"]
    t[u"席の札の誤り(違う+答えが無い)"] = wrong
    t[u"席の札の誤りの割合"] = round(wrong / t[u"置いた"], 4) if t[u"置いた"] else 0.0
    t[u"印の中の答えを席が同じに置いた割合"] = round(t[u"置いた・答えと同じ"] / t[u"答えの在る印"], 4) if t[u"答えの在る印"] else 0.0
    t[u"規則だけの数の fact の覆い"] = round(t[u"規則で置いた中の答えの fact"] / t[u"答えの数の fact"], 4)
    t[u"規則と席の数の fact の覆い"] = round((t[u"規則で置いた中の答えの fact"] + t[u"置いた・答えと同じ"]) / t[u"答えの数の fact"], 4)
    t[u"形で落とした割合"] = round(t[u"形で落とした"] / (t[u"置いた"] + t[u"形で落とした"]), 4) if (t[u"置いた"] + t[u"形で落とした"]) else 0.0
    t[u"席の札の誤りが 5 を超えた組"] = sum(1 for r in rows if r[u"置いた・答えと違う"] + r[u"置いた・答えが無い"] > 5)
    return t, rows


def main():
    base, dv, hd = sys.argv[1], [int(x) for x in sys.argv[2].split(",")], [int(x) for x in sys.argv[3].split(",")]
    td, rd = group(base, "d", dv)
    th, rh = group(base, "h", hd)
    j = od()

    def judge(k, pred, got, ok):
        j[k] = od([(u"予測", pred), (u"出た", got), (u"判定", u"当たり" if ok else u"外れ")])
    judge("XC7-1", u"席の札の誤り(違う+答えが無い)は席の置いた札の 2% 以下", th[u"席の札の誤りの割合"], th[u"席の札の誤りの割合"] <= 0.02)
    judge("XC7-2", u"答えの在る印のうち席が答えと同じに置いた割合は 50% 以上 90% 以下", th[u"印の中の答えを席が同じに置いた割合"], 0.5 <= th[u"印の中の答えを席が同じに置いた割合"] <= 0.9)
    d = round(th[u"規則と席の数の fact の覆い"] - th[u"規則だけの数の fact の覆い"], 4)
    judge("XC7-3", u"数の fact の覆いは席で 5 ポイント以上ふえる", d, d >= 0.05)
    judge("XC7-4", u"形で落とした札は 2% 以下", th[u"形で落とした割合"], th[u"形で落とした割合"] <= 0.02)
    judge("XC7-5", u"席の札の誤りが 5 を超えた組は 0", th[u"席の札の誤りが 5 を超えた組"], th[u"席の札の誤りが 5 を超えた組"] == 0)
    rec = od([(u"便", u"XC7(規則で置けなかった表の数の升に AI の席が札を付ける)"), (u"集計 作りの組", td), (u"集計 判定の組", th),
              (u"予測の判定", j), (u"組ごと(番号と数だけ)", od([("dev", rd), ("held", rh)]))])
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(od([("dev", td), ("held", th), ("judge", j)]), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
