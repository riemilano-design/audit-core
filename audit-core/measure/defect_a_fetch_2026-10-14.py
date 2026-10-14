# -*- coding: utf-8 -*-
"""欠陥 A の修正用標本の取得(docs/DEFECT_A_EVAL_SEAL_2026-10-14.md §2)。**一度だけ走らせる。**

- 取るのは `fixtures/xbrl/defect_a/draw_2026-10-14.json` の 8 件**だけ**。他の docID は取らない。
- 鍵は環境変数 **EDINET_API_KEY** を `adapters.xbrl.edinet` が読む。
  **この script は鍵の値を参照も印字もしない。**
- 既にキャッシュに在る件は取らず「already」と印字する(二度目の取得をしない)。
- 失敗した件は**別の書類で埋めない**。失敗として印字して続ける(封 §2)。
- 走り終わると開封の記録 `fixtures/xbrl/defect_a/opened_2026-10-14.json` を書く
  (docID・結果・zip sha256・時刻・engine の commit だけ。**本文も主張も状態も読まない**)。

印字するのは docID・結果・zip sha256 だけ。
"""
import datetime
import hashlib
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from adapters.xbrl import edinet  # noqa: E402

DRAW = os.path.join(ROOT, "fixtures", "xbrl", "defect_a", "draw_2026-10-14.json")
OPENED = os.path.join(ROOT, "fixtures", "xbrl", "defect_a", "opened_2026-10-14.json")


def main():
    if os.path.exists(OPENED):
        raise SystemExit("開封は既に記録されている。二度目を走らせない: %s" % OPENED)
    if not os.environ.get("EDINET_API_KEY"):
        raise SystemExit("環境変数 EDINET_API_KEY が無い。鍵を持つ端末で走らせること")
    ids = json.load(io.open(DRAW, encoding="utf-8"))["docs"]
    assert len(ids) == 8 and len(set(ids)) == 8, ids
    log, sha, ok = [], {}, 0
    for doc in ids:
        p = edinet.cache_path(doc)
        if os.path.exists(p):
            h = hashlib.sha256(io.open(p, "rb").read()).hexdigest()
            print(doc, "already", h)
            log.append({"docID": doc, "result": "already"})
            sha[doc] = h
            ok += 1
            continue
        try:
            edinet.fetch(doc)
            h = hashlib.sha256(io.open(p, "rb").read()).hexdigest()
            print(doc, "fetched", h)
            log.append({"docID": doc, "result": "fetched"})
            sha[doc] = h
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(doc, "FAILED", type(e).__name__, str(e)[:80])
            log.append({"docID": doc, "result": "FAILED", "error": type(e).__name__})
    print("present %d / 8" % ok)
    head = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    rec = {"seal": "docs/DEFECT_A_EVAL_SEAL_2026-10-14.md",
           "opened_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "engine_commit": head,
           "how": "measure/defect_a_fetch_2026-10-14.py を 1 回実行"
                  "(鍵は環境変数 EDINET_API_KEY の名前だけ。値は記録しない)",
           "docs": ids, "fetch_log": log, "zip_sha256": sha, "present": ok}
    with io.open(OPENED, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("->", OPENED)


if __name__ == "__main__":
    main()
