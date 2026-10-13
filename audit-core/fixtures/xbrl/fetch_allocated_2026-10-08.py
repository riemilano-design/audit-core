# -*- coding: utf-8 -*-
"""割り当てた書類のうち、**役が「B 確認用」のものだけ**を取る。
Core のコードではない。

## なぜ専用の道具を作るか

`measure/fetch_material.py` は**封じた種で引く**道具で、docID を指して取る口が無い。
ここで要るのは「**すでに封じて記録した 2 件**を、それだけ取る」ことである。

**この道具は `allocation_2026-10-08.json` を読み、`role` が `B-verify` の行しか取らない。**
取り置き(`B-reserved`)とショーケース(`showcase`)の docID を渡しても**断る** ―
人間の指示「取り置き 2 件は資料用の最終の数字まで使わない」「ショーケースの 8 件は
ショーケースの実行まで誰も中身を見ない」を、**手で守るのではなく道具で守る。**

## 鍵

`EDINET_API_KEY` から読む。**値は読まない・印字しない・ファイルに書かない。**

## 残すもの

docID・社名・バイト数・ZIP の sha256・**中身の印**(`zip_content_digest.py`)。
ZIP の sha256 は EDINET が要求ごとに ZIP を作り直すので**再現しない** ―
封に使えるのは中身の印だけである(2026-10-08 に実測して分かった)。

**中身は読まない。** 中身の印は ZIP の目録(名前・CRC・展開後の大きさ)だけから作る。
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
import os as _os_gate
import sys as _sys_gate
_sys_gate.path.insert(0, _os_gate.path.dirname(_os_gate.path.abspath(__file__)))
from sealed_material import refuse_if_sealed  # noqa: E402  **取る直前に呼ぶ**

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from zip_content_digest import content_digest  # noqa: E402

API = "https://api.edinet-fsa.go.jp/api/v2/"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

# 取ってよい役。**字で書く。** ここを増やすのは人間の判断が要る。
FETCHABLE_ROLES = ("B-verify",)


def _key():
    k = os.environ.get("EDINET_API_KEY")
    if not k:
        raise SystemExit("EDINET_API_KEY is not set (this script never prints the key's value)")
    return k


def allowed_rows(allocation_path):
    """割り当ての記録から、取ってよい行だけを返す。"""

    rec = json.load(open(allocation_path, encoding="utf-8"))
    return [r for r in rec["assigned"] if r["role"] in FETCHABLE_ROLES]


def fetch_zip(doc_id):
    refuse_if_sealed(doc_id=doc_id, where="fetch_allocated.fetch_zip")   # **取る直前**
    q = {"type": 1, "Subscription-Key": _key()}
    url = API + "documents/%s?" % urllib.parse.quote(doc_id) + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=300) as r:
        body = r.read()
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, "%s.zip" % doc_id)
    with open(path, "wb") as fh:
        fh.write(body)
    return path, body


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--allocation", default=os.path.join(HERE, "allocation_2026-10-08.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "fetched_b_verify_2026-10-08.json"))
    a = ap.parse_args(argv)

    rows = allowed_rows(a.allocation)
    print("取ってよい役 %s の行: %d 件" % (",".join(FETCHABLE_ROLES), len(rows)))
    out = []
    for r in rows:
        path = os.path.join(CACHE_DIR, "%s.zip" % r["docID"])
        if os.path.exists(path):
            body = open(path, "rb").read()
            how = "すでに手元に在った"
        else:
            path, body = fetch_zip(r["docID"])
            how = "取った"
        rec = {
            "docID": r["docID"], "filerName": r["filerName"], "periodEnd": r["periodEnd"],
            "role": r["role"], "draw_order": r["draw_order"], "bytes": len(body),
            # 再現しない。記録としてだけ残す。
            "zip_sha256": hashlib.sha256(body).hexdigest(),
            # 再現する。封に使えるのはこちら。
            # ``content_digest`` は **(印, 目録の数) の対**を返す。
            # 記録の形は変えない(``allocation``・結果文書が [印, 数] の並びで
            # 引いている)。印字だけ対として扱う。
            "content_digest": list(content_digest(body)),
        }
        out.append(rec)
        digest, members = rec["content_digest"]
        print("  %-10s %-28s %8d bytes  zip=%s…  中身の印=%s…(目録 %d 本)  (%s)" % (
            rec["docID"], (rec["filerName"] or "")[:28], rec["bytes"],
            rec["zip_sha256"][:16], digest[:16], members, how))

    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump({"tool": "fetch_allocated_2026-10-08", "roles": list(FETCHABLE_ROLES),
                   "fetched": out}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("written: %s" % a.out)
    print("**中身は読んでいない**(中身の印は ZIP の目録だけから作っている)。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
