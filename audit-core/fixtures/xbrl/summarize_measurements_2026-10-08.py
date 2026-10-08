# -*- coding: utf-8 -*-
"""測った書類**すべての合計**と**書類ごとの値**を並べて出す。Core のコードではない。

人間の指示(2026-10-08): 「今後、止まった率は 1 社ではなく、測った書類すべての合計と
書類ごとの値を並べて報告してください。」

`fixtures/xbrl/measure_xbrl_fix5_<docID>.json` を全部読み、構成ごとに

    合計(止まった / 主張 / 率) | 書類ごとの値

を印字する。**合計は「止まった件数の合計 ÷ 主張の合計」**であって、書類ごとの率の平均ではない
(書類の大きさが違うので平均は意味が違う。両方出して、どちらを読んでいるか迷わないようにする)。

**開発に使った書類**(`S100Z4Q1`・`S100Z4B6`・`S100YMFV`)と**未使用の書類**は
**別の行にまとめて**出す ― 混ぜると「直しを作るのに使った書類での値」が効果の値に見えてしまう。

    python3 fixtures/xbrl/summarize_measurements_2026-10-08.py [--dir fixtures/xbrl]

通信はしない。API は呼ばない(費用 0 円)。
"""

import argparse
import glob
import json
import os
import sys

# 接続部分(adapters/xbrl)の設計・語彙・境界を決めるのに使った書類。字で書く。
DEVELOPMENT_DOCS = ("S100Z4Q1", "S100Z4B6", "S100YMFV")

# 印字する構成の順と見出し。
CONFIG_LABELS = [
    ("base", "直す前(P7)"),
    ("fix1a_vocab", "1a 語彙"),
    ("fix1b_stop", "1b 代用せず止める"),
    ("fix1_both", "1 = 1a + 1b"),
    ("fix2_rounding", "2 書類単位の丸め"),
    ("fix3_target", "3 目標・見通し"),
    ("fix4_paren", "4 括弧内の句点"),
    ("fix5_qualitative", "5 定性的な語(広い版)"),
    ("fix5n_state_only", "5' 状態語だけ(狭い版)"),
    ("fix6_prior_paren", "6 括弧内の前期の方向語"),
    ("fix6_with_vocab", "6 + 1a"),
    ("all", "5 つとも(P8)"),
    ("all6", "6 つとも・広い版(P9)"),
    ("all6n", "6 つとも・狭い版(P10)★正本"),
    ("fix7_label_vocab", "7 ラベルの語彙だけ"),
    ("all7", "P10 + ラベルの語彙(P11)"),
]


def load(dirname):
    out = {}
    for path in sorted(glob.glob(os.path.join(dirname, "measure_xbrl_fix5_*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        out[d["doc"]] = d
    return out


def band(stopped, claims):
    """止まった率の 95% の幅(正規近似。1 書類の数がどれだけ粗いかを一緒に出す)。"""

    if claims == 0:
        return (0.0, 0.0)
    p = float(stopped) / claims
    se = (p * (1.0 - p) / claims) ** 0.5
    return (max(0.0, p - 1.96 * se) * 100.0, min(1.0, p + 1.96 * se) * 100.0)


def report(docs, group_name, doc_ids, base_denominator=None):
    if not doc_ids:
        return
    print("=" * 110)
    print("%s(%d 書類: %s)" % (group_name, len(doc_ids), " / ".join(doc_ids)))
    print("-" * 110)
    base_total = sum(docs[d]["configs"]["base"]["tally"]["claims"] for d in doc_ids)
    head = "%-26s %-22s" % ("構成", "合計 止まった/主張 = 率")
    head += " ".join("%-20s" % d for d in doc_ids)
    print(head)
    for key, label in CONFIG_LABELS:
        if not all(key in docs[d]["configs"] for d in doc_ids):
            continue
        st = sum(docs[d]["configs"][key]["tally"]["stopped"] for d in doc_ids)
        cl = sum(docs[d]["configs"][key]["tally"]["claims"] for d in doc_ids)
        lo, hi = band(st, cl)
        line = "%-26s %-22s" % (label, "%3d/%3d = %5.1f%%" % (st, cl, 100.0 * st / cl))
        for d in doc_ids:
            t = docs[d]["configs"][key]["tally"]
            line += "%-20s " % ("%2d/%3d = %5.1f%%" % (t["stopped"], t["claims"], 100.0 * t["stopped"] / t["claims"]))
        print(line)
        print("%-26s %-22s %s" % ("", "  幅 %4.1f〜%4.1f%%" % (lo, hi),
                                  "  元の分母 %d で数えると %5.1f%%" % (base_total, 100.0 * st / base_total)))
    print("-" * 110)
    print("合計の率 = 止まった件数の合計 ÷ 主張の合計(書類ごとの率の平均ではない)。")
    print("書類ごとの率は 1 標本であり、幅は上の行のとおり広い。書類の本数を増やさないと縮まらない。")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args(argv)
    docs = load(a.dir)
    if not docs:
        raise SystemExit("no measure_xbrl_fix5_*.json under %s" % a.dir)
    dev = [d for d in DEVELOPMENT_DOCS if d in docs]
    held = sorted(d for d in docs if d not in DEVELOPMENT_DOCS)
    report(docs, "開発に使った書類 ― 直しを作るのに使った値であって、効果の値ではない", dev)
    if held:
        report(docs, "未使用の書類(holdout)― 直しの効果の値", held)
    else:
        print("=" * 110)
        print("未使用の書類(holdout): **まだ無い**。EDINET の API キーが入るまで保留。")
        print("効果の値はここに入る。上の表は開発に使った書類での値である。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
