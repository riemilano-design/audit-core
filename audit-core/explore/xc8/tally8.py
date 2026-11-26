# -*- coding: utf-8 -*-
u"""便 XC8 の数え: out/{dev,held}_base.json(席の札なし)と out/{dev,held}.json(席の札あり)→ record.json。符号の分けは便 XC5 と同じ。"""
import collections, importlib.util, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_t5", os.path.join(os.path.dirname(HERE), "xc5", "tally_xc5.py"))
T5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(T5)
od = collections.OrderedDict
EXTRA = (u"席の札を置いた", u"包みに渡した席の札", u"形で落とした・要素がタクソノミに無い", u"形で落とした・文脈が無い", u"形で落とした・単位が無い",
         u"形で落とした・要素が今年の定義に無い", u"形で落とした・要素の名の形", u"G1 で置かなかった数の fact", u"G2 で置かなかった数の fact")


def total(rows):
    t = T5.total(rows)
    for k in EXTRA:
        t[k] = sum(r.get(k, 0) for r in rows)
    t[u"道具が読んだ組んだ数の fact のうち元と違う行"] = t[u"道具が読んだ: 組んだ数の fact"] - t[u"数の fact: 元と同じ行"]
    return t


def load(name):
    with open(os.path.join(HERE, "out", name), encoding="utf-8") as f:
        return json.load(f)


def main():
    g = od()
    for w in ("dev", "held"):
        g[w] = od([(u"席の札なし", total(load(w + "_base.json"))), (u"席の札あり", total(load(w + ".json")))])
    b, s = g["held"][u"席の札なし"], g["held"][u"席の札あり"]
    j = od()

    def judge(k, pred, got, ok):
        j[k] = od([(u"予測", pred), (u"出た", got), (u"判定", u"当たり" if ok else u"外れ")])
    t1 = s[u"形で落とした・要素がタクソノミに無い"]
    judge("XC8-1", u"T1 で要素がタクソノミに無いと落とした席の札は 12 以上 20 以下", t1, 12 <= t1 <= 20)
    d = s[u"数の fact: 元と同じ行"] - b[u"数の fact: 元と同じ行"]
    judge("XC8-2", u"道具が読んだ数の fact の元と同じ行は、席の札で 430 以上ふえる", d, d >= 430)
    wb = b[u"道具が読んだ組んだ数の fact のうち元と違う行"]; ws = s[u"道具が読んだ組んだ数の fact のうち元と違う行"]
    judge("XC8-3", u"道具が読んだ組んだ数の fact のうち元と違う行は、席の札で 5 以下しかふえない", ws - wb, ws - wb <= 5)
    eb = b[u"組んだ側だけで誤りの符号が 1 つも鳴らなかった組"]; es = s[u"組んだ側だけで誤りの符号が 1 つも鳴らなかった組"]
    judge("XC8-4", u"誤りの符号が 1 つも鳴らなかった組は、席の札で減らない", [eb, es], es >= eb)
    rb = b[u"組んだ包みを道具が最後まで読んだ組"]; rs = s[u"組んだ包みを道具が最後まで読んだ組"]
    judge("XC8-5", u"道具が最後まで読んだ組は、席の札で減らない", [rb, rs], rs >= rb)
    rec = od([(u"便", u"XC8(席の札の名をタクソノミで引き、包みに入れて道具 P に読ませる)"), (u"集計", g), (u"予測の判定", j),
              (u"組ごと(番号と数だけ)", od((w + k, load(w + k + ".json")) for w in ("dev", "held") for k in ("_base", "")))])
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(j, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
