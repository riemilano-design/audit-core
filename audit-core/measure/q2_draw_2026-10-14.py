# -*- coding: utf-8 -*-
"""Q2 の対象書類を引く(docs/Q2_NONCONSOLIDATED_SEAL_2026-10-14.md §2)。**一度だけ走らせる。**

予備 order[22:] の順に 1 件ずつ取得し、`consolidated_element_count` **だけ**を見る。
  > 0(連結あり) -> 中を読まずに次へ送る(使用済みに移す)
  == 0(連結なし) -> Q2 の対象に採る。経営分析の節が在ることだけ確かめる
2 件採れたら止める。**取得を試みた件数の上限は 30**。

鍵は環境変数 EDINET_API_KEY を adapters.xbrl.edinet が読む。この script は値を参照も印字もしない。
印字・記録するのは docID・zip sha256・連結の要素数・採否だけ。**本文・主張・状態は読まない。**
"""
import hashlib
import io
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from adapters.xbrl import edinet, instance as I  # noqa: E402

POOL = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "pool2_clean_2026-10-14.json")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
OUT = os.path.join(ROOT, "fixtures", "xbrl", "q2_nonconsolidated")
DATE = "2026-10-14"
SEED_HEX = "6a24d72"
RESERVE_FROM = 22
NEED = 2
CAP = 30


def reserve():
    """封 88f8e16 §9-2 の算法で並びを作り直し、3 群が split と一致することを確かめてから予備を返す。"""
    pool = json.load(io.open(POOL, encoding="utf-8"))["pool_clean"]
    order = sorted(pool)
    random.Random(int(SEED_HEX, 16)).shuffle(order)
    d = json.load(io.open(SPLIT, encoding="utf-8"))
    assert order[0:6] == d["used"], "使用済み 6 件が再現しない"
    assert order[6:14] == d["development"], "直し用 8 件が再現しない"
    assert order[14:22] == d["final_eval_sealed"], "最終評価用 8 件が再現しない"
    return order[RESERVE_FROM:]


def main():
    q = reserve()
    rows, taken, tried = [], [], 0
    for doc in q:
        if len(taken) >= NEED or tried >= CAP:
            break
        tried += 1
        rec = {"n": tried, "docID": doc}
        try:
            path = edinet.cache_path(doc)
            if not os.path.exists(path):
                edinet.fetch(doc)
            zb = open(path, "rb").read()
            rec["zip_sha256"] = hashlib.sha256(zb).hexdigest()
        except Exception as e:  # noqa: BLE001
            rec.update(verdict="外す(取得できない)", error=type(e).__name__)
            rows.append(rec)
            print("%2d %s  %s" % (tried, doc, rec["verdict"]))
            continue
        inst = I.load_instance(zb)
        n = I.consolidated_element_count(inst["facts"])
        rec["consolidated_element_count"] = n
        if n > 0:
            rec["verdict"] = "送る(連結あり。中を読まない)"
        else:
            try:
                I.select_mdna(inst["textblocks"])
                rec["verdict"] = "採る(連結なし)"
                taken.append(doc)
            except Exception as e:  # noqa: BLE001
                rec.update(verdict="外す(経営分析の節が無い)", error=type(e).__name__)
        rows.append(rec)
        print("%2d %s  連結要素 %3d  %s" % (tried, doc, n, rec["verdict"]))

    out = {"seal": "docs/Q2_NONCONSOLIDATED_SEAL_2026-10-14.md",
           "rule": "order[22:] の順に 1 件ずつ。連結ありは中を読まずに送る。連結なしを 2 件採るまで。上限 30 件",
           "tried": tried, "cap": CAP, "taken": taken, "need": NEED,
           "complete": len(taken) >= NEED, "draws": rows}
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "draw_%s.json" % DATE)
    if os.path.exists(p):
        raise SystemExit("既に在る。上書きしない: %s" % p)
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print()
    print("試みた %d 件 / 上限 %d。採れた %d 件: %s" % (tried, CAP, len(taken), taken))
    print("2 件に届いた:", out["complete"])
    print("->", p)


if __name__ == "__main__":
    main()
