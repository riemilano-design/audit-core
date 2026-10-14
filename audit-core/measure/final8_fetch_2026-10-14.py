# -*- coding: utf-8 -*-
"""最終評価用 8 書類の取得(docs/FINAL_EVAL_8_SEAL_2026-10-14.md §9 手順 3)。**一度だけ走らせる。**

- 取るのは split の final_eval_sealed の 8 件だけ。他の docID は取らない。
- 鍵は環境変数 EDINET_API_KEY を adapters.xbrl.edinet が読む。この script は値を参照も印字もしない。
- 既にキャッシュに在る件は取らず「already」と印字する(二度目の取得をしない)。
- 失敗した件は別の書類で埋めず、失敗として印字して続ける(封 §7・人間の条件)。
印字するのは docID・結果・zip sha256 だけ。
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from adapters.xbrl import edinet  # noqa: E402

SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")


def main():
    ids = json.load(open(SPLIT, encoding="utf-8"))["final_eval_sealed"]
    assert len(ids) == 8, ids
    ok = 0
    for doc in ids:
        p = edinet.cache_path(doc)
        if os.path.exists(p):
            print(doc, "already", hashlib.sha256(open(p, "rb").read()).hexdigest())
            ok += 1
            continue
        try:
            edinet.fetch(doc)
            print(doc, "fetched", hashlib.sha256(open(p, "rb").read()).hexdigest())
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(doc, "FAILED", type(e).__name__, str(e)[:80])
    print("present %d / 8" % ok)


if __name__ == "__main__":
    main()
