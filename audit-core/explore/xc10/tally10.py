# -*- coding: utf-8 -*-
u"""便 XC10 の数え: out/{dev,held}_{base,num,all}.json → record.json。符号の分けは便 XC5 と同じ。"""
import collections, importlib.util, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_t5", os.path.join(os.path.dirname(HERE), "xc5", "tally_xc5.py"))
T5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(T5)
od = collections.OrderedDict
EXTRA = (u"道具が読んだ: 元の数でない fact", u"道具が読んだ: 組んだ数でない fact", u"数でない fact: 元と同じ行", u"数でない fact: 値の空白を除けば元と同じ行",
         u"R1 で落とした節", u"包みに渡す節", u"文の置き方に足した節", u"席の札を置いた", u"形で落とした・要素がタクソノミに無い")


def total(rows):
    t = T5.total(rows)
    for k in EXTRA:
        t[k] = sum(r.get(k, 0) for r in rows)
    return t


def load(name):
    with open(os.path.join(HERE, "out", name), encoding="utf-8") as f:
        return json.load(f)


def main():
    g = od((w, od((md, total(load("%s_%s.json" % (w, md)))) for md in ("base", "num", "all"))) for w in ("dev", "held"))
    h = g["held"]
    j = od()

    def judge(k, pred, got, ok):
        j[k] = od([(u"予測", pred), (u"出た", got), (u"判定", u"当たり" if ok else u"外れ")])
    d1 = h["all"][u"数の fact: 元と同じ行"] - h["num"][u"数の fact: 元と同じ行"]
    judge("XC10-1", u"数の fact の元と同じ行は、節を足しても数の札だけの時から 5 以内しか動かない", d1, abs(d1) <= 5)
    d2 = h["all"][u"数でない fact: 値の空白を除けば元と同じ行"] - h["num"][u"数でない fact: 値の空白を除けば元と同じ行"]
    judge("XC10-2", u"数でない fact の、値の空白を除けば元と同じ行は、節を足して 80 以上ふえる", d2, d2 >= 80)
    e = [h[md][u"組んだ側だけで EDINET の E の符号が鳴らなかった組"] for md in ("base", "num", "all")]
    judge("XC10-3", u"E の符号が鳴らなかった組は、席なし → 数の札 → 節つきで減らない", e, e[2] >= e[0] and e[2] >= e[1])
    a = [h[md][u"組んだ側だけで誤りの符号が 1 つも鳴らなかった組"] for md in ("base", "num", "all")]
    judge("XC10-4", u"誤りの符号が 1 つも鳴らなかった組は、席なし → 数の札 → 節つきで減らない", a, a[2] >= a[0] and a[2] >= a[1])
    r1 = h["all"][u"R1 で落とした節"]
    judge("XC10-5", u"R1 で落とした節は 5 以下", r1, r1 <= 5)
    rec = od([(u"便", u"XC10(席の数の札と節を合わせて包みに入れ、道具 P に読ませる)"), (u"集計", g), (u"予測の判定", j),
              (u"組ごと(番号と数だけ)", od(("%s_%s" % (w, md), load("%s_%s.json" % (w, md))) for w in ("dev", "held") for md in ("base", "num", "all")))])
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(j, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
