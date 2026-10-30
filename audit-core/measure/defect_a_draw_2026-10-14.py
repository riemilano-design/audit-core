# -*- coding: utf-8 -*-
"""欠陥 A の修正用標本を引く(docs/DEFECT_A_EVAL_SEAL_2026-10-14.md §2)。**通信しない。**

封じた並び(``docs/HOLDOUT_SPLIT_SEAL_2026-10-14.md``、seed ``6a24d72``)の
``order[26:34]`` をそのまま採る。**無作為性は無い**(並びは既に封じられており、
使用済み 26 件 = 使用済み 6 + 直し用 8 + 最終評価用 8 + Q2 で試した 4 の続き)。

走らせる前に**3 つの既定群が split と一致すること**と、**使用済み 26 件と重ならないこと**を
確かめる。出力が既に在れば上書きを拒む(引き直しで標本を選び直す道を塞ぐ)。
"""
import io
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

POOL = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "pool2_clean_2026-10-14.json")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
OUT = os.path.join(ROOT, "fixtures", "xbrl", "defect_a", "draw_2026-10-14.json")
SEED_HEX = "6a24d72"
USED_N = 26
NEED = 8


def order_and_check():
    """並びを作り直し、封じた 3 群が再現することを確かめて返す。"""
    pool = json.load(io.open(POOL, encoding="utf-8"))["pool_clean"]
    order = sorted(pool)
    random.Random(int(SEED_HEX, 16)).shuffle(order)
    split = json.load(io.open(SPLIT, encoding="utf-8"))
    groups = (("used", 0, 6), ("development", 6, 14), ("final_eval_sealed", 14, 22))
    for name, a, b in groups:
        if split[name] != order[a:b]:
            raise AssertionError("封じた群 %s が再現しない" % name)
    if split["pool"] != len(pool) or split["reserve_n"] != len(order) - 22:
        raise AssertionError("封じた件数が合わない")
    return order


def draw():
    order = order_and_check()
    docs = order[USED_N:USED_N + NEED]
    if len(set(docs)) != NEED or set(docs) & set(order[:USED_N]):
        raise AssertionError("標本が重なっている")
    return docs


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る。上書きしない: %s" % OUT)
    docs = draw()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rec = {"seal": "docs/DEFECT_A_EVAL_SEAL_2026-10-14.md",
           "rule": "封じた並びの order[26:34] をそのまま。無作為性なし",
           "seed_hex": SEED_HEX, "used_n": USED_N, "need": NEED, "docs": docs}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    for i, d in enumerate(docs, 1):
        print("%d) %s" % (i, d))
    print("->", OUT)


if __name__ == "__main__":
    main()
