# -*- coding: utf-8 -*-
u"""便 XC5 の数え: out/dev.json・out/held.json → record.json。組の番号と数・道具の符号だけ。
誤りの符号: EDINET の E の符号(EDINET.EC…E)と、EDINET. で始まらない符号の全部(xbrldie:・xmlSchema:・ix…・exception:・arelle: など)。
EDINET の W の符号は誤りに数えない。"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
od = collections.OrderedDict


def is_edinet_e(c):
    return c.startswith("EDINET.EC") and c.endswith("E")


def is_err(c):
    return is_edinet_e(c) or not c.startswith("EDINET.")


def pct(n, d):
    return round(100.0 * n / d, 2) if d else None


def total(rows):
    t = collections.Counter()
    for r in rows:
        t.update(dict((k, v) for k, v in r.items() if isinstance(v, int) and k != u"番号"))
    t = od(sorted(t.items()))
    c = collections.Counter()
    for r in rows:
        c.update(r[u"組んだ側だけで鳴った符号"].keys())
    t[u"組んだ側だけで鳴った符号(その符号の鳴った組の数)"] = od(sorted(c.items(), key=lambda q: (-q[1], q[0])))
    t[u"組んだ側だけで EDINET の E の符号が鳴らなかった組"] = sum(1 for r in rows if not any(is_edinet_e(k) for k in r[u"組んだ側だけで鳴った符号"]))
    t[u"組んだ側だけで誤りの符号が 1 つも鳴らなかった組"] = sum(1 for r in rows if not any(is_err(k) for k in r[u"組んだ側だけで鳴った符号"]))
    t[u"組んだ包みを道具が最後まで読んだ組"] = sum(1 for r in rows if r[u"道具の類: 元・組んだ"][1] == u"走った")
    t[u"組の数"] = len(rows)
    return t


def main():
    dev = json.load(open(os.path.join(HERE, "out", "dev.json"), encoding="utf-8"))
    held = json.load(open(os.path.join(HERE, "out", "held.json"), encoding="utf-8"))
    h = total(held)
    codes = h[u"組んだ側だけで鳴った符号(その符号の鳴った組の数)"]
    j = od()

    def judge(key, pred, got, ok):
        j[key] = od([("予測", pred), ("出た", got), ("判定", u"当たり" if ok else u"外れ")])
    e0 = h[u"組んだ側だけで EDINET の E の符号が鳴らなかった組"]
    judge("XC5-1", u"組んだ側だけで EDINET の E の符号が鳴らなかった組は 40 のうち 30 以上(作りでは 21 / 23。便 XC4 は 0 / 40)", e0, e0 >= 30)
    a0 = h[u"組んだ側だけで誤りの符号が 1 つも鳴らなかった組"]
    judge("XC5-2", u"組んだ側だけで誤りの符号が 1 つも鳴らなかった組は 40 のうち 20 以上 36 以下(作りでは 16 / 23)", a0, 20 <= a0 <= 36)
    judge("XC5-3", u"組んだ側だけで xbrl.3.5.2.4.5:roleRefMismatch が鳴った組は 1 以下(便 XC4 は 35)", codes.get("xbrl.3.5.2.4.5:roleRefMismatch", 0), codes.get("xbrl.3.5.2.4.5:roleRefMismatch", 0) <= 1)
    judge("XC5-4", u"組んだ側だけで xmlSchema:syntax が鳴った組は 1 以下(便 XC4 は 15)", codes.get("xmlSchema:syntax", 0), codes.get("xmlSchema:syntax", 0) <= 1)
    judge("XC5-5", u"組んだ側だけで EDINET.EC1001E が鳴った組は 6 以下(便 XC4 は 35)", codes.get("EDINET.EC1001E", 0), codes.get("EDINET.EC1001E", 0) <= 6)
    judge("XC5-6", u"道具が読んだ数の fact で元と同じ行は 32000 以上(便 XC4 は 32124)", h[u"数の fact: 元と同じ行"], h[u"数の fact: 元と同じ行"] >= 32000)
    w = pct(h[u"位置: 置いた文の fact"] - h[u"位置: 一致"], h[u"位置: 置いた文の fact"])
    r = pct(h[u"位置: 一致"], h[u"位置: 答えの文の fact"])
    judge("XC5-7", u"置いた文の fact のうち答えと違うは 10% 以下・答えの文の fact の一致は 25% 以上 40% 以下(作りでは 6.9%・32.1%)", "%s%%・%s%%" % (w, r), w <= 10 and 25 <= r <= 40)
    st = h[u"組の数"] - h[u"組んだ包みを道具が最後まで読んだ組"]
    judge("XC5-8", u"組んだ包みで道具が途中で止まった組は 4 以下(作りでは 1 / 23。便 XC4 は 6 / 40)", st, st <= 4)
    rec = od([(u"便", u"XC5(道具の文から読んだ原因を直す: F1 字の形・F2 roleRef の版・F3 使う文脈だけ・F5 無い要素・F6 表紙の項目・F7 提出日)"),
              (u"集計 作りの 23 組", total(dev)), (u"集計 判定の 40 組", h), (u"予測の判定", j),
              (u"組ごと(番号と数だけ)", od([("dev", dev), ("held", held)]))])
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(j, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
