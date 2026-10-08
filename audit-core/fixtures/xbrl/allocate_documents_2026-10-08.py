# -*- coding: utf-8 -*-
"""未使用の書類の割り当て ― **封じた種で引き、役割を引いた順で決める。**
Core のコードではない。

人間の指示(2026-10-08):

> 候補(9 月提出の有価証券報告書)から、開発に使った 4 件を除く。
> 封じた種で、**B の確認用に 4 件・ショーケース用に 8 件**を、重複なしで選ぶ。
> 割り当ては、**どちらの中身も見る前に** 1 つのファイルに記録してコミットする。
> B の 4 件のうち 2 件は直しの確認用、2 件は資料用の最終の数字まで使わない。
> ショーケースの 8 件は、ショーケースの実行まで誰も中身を見ない。

## 2 つのモード

``--list-out <path>``
    EDINET の提出一覧を取り、**metadata だけ**(docID・社名・期末・提出日)を JSON に書く。
    **鍵が要る**(``EDINET_API_KEY``。値は読まない・印字しない・ファイルに書かない)。
    ZIP は取らない。**書類の中身には触らない。**

``--allocate --candidates <path>``
    **通信しない。** 上の JSON を読み、開発に使った 4 件を除き、封じた種で 12 件を引いて
    役割を割り当て、1 つのファイルに書く。

## 役割の決め方(**引く前に決めてある。この順を後から変えない**)

``random.Random("<種>|document-allocation-2026-10-08|<from>|<to>").sample(rows, 12)``
の**引いた順**で、

====  ================================================
順    役割
====  ================================================
1-2   **B 確認用** ― 主語の規則の直しの確認に使う
3-4   **B 取り置き** ― 資料用の最終の数字まで使わない
5-12  **ショーケース用** ― ショーケースの実行まで誰も中身を見ない
====  ================================================

``sample`` は重複なしなので、3 つの群は**構成上**重ならない。

並べ替えは ``(提出日, docID)``。**種は git の blob から読む**ので、
ファイルを書き換えても commit しなければ効かない(blob の sha256 を記録に残す)。
"""

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

API = "https://api.edinet-fsa.go.jp/api/v2/"

# 有価証券報告書: ordinanceCode 010 / docTypeCode 120。字で書く
# (fetch_material.py と同じ値。四半期・訂正は別の形の書類なので入れない)。
ORDINANCE = "010"
DOCTYPE = "120"

# 接続部分(adapters/xbrl)の設計・語彙・境界・主語の規則の原因調査に使った書類。
# **字で書く。** S100Z37J は 2026-10-08 の人間の判断 2 で開発用に移った。
DEVELOPMENT_DOCS = ("S100Z4Q1", "S100Z4B6", "S100YMFV", "S100Z37J")

# 種の在り処(本線の blob)。ファイルの中身ではなく **commit されたもの**を読む。
SEED_REF = "feature/phase7-recognition-spec"
SEED_PATH = "audit-core/measure/SEED.json"

# 乱数の札。``fetch_material.py`` の ``edinet-pick`` とは別にする
# (同じ札だと前の引きと混ざり、どちらの封に従ったのか分からなくなる)。
RNG_LABEL = "document-allocation-2026-10-08"

# 役割。**引いた順**に当てる。件数は字で書く。
ROLES = (
    (2, "B-verify", "B 確認用(主語の規則の直しの確認)"),
    (2, "B-reserved", "B 取り置き(資料用の最終の数字まで使わない)"),
    (8, "showcase", "ショーケース用(実行まで誰も中身を見ない)"),
)
TOTAL = sum(n for n, _k, _j in ROLES)


def sealed_seed():
    """``SEED.json`` を **git の blob から**読む。返すのは (種, blob の sha256)。"""

    blob = subprocess.check_output(["git", "-C", REPO, "show", "%s:%s" % (SEED_REF, SEED_PATH)])
    return json.loads(blob)["seed"], hashlib.sha256(blob).hexdigest()


# --- モード 1: 一覧を取る(鍵が要る。ZIP は取らない) ---------------------------


def _key():
    import os as _os

    k = _os.environ.get("EDINET_API_KEY")
    if not k:
        raise SystemExit("EDINET_API_KEY is not set (this script never reads the key from a file "
                         "and never prints its value)")
    return k


def list_candidates(date_from, date_to):
    import datetime
    import urllib.error
    import urllib.parse
    import urllib.request

    rows = []
    d = datetime.date.fromisoformat(date_from)
    end = datetime.date.fromisoformat(date_to)
    while d <= end:
        day = d.isoformat()
        d += datetime.timedelta(days=1)
        q = {"date": day, "type": 2, "Subscription-Key": _key()}
        try:
            with urllib.request.urlopen(API + "documents.json?" + urllib.parse.urlencode(q), timeout=120) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            print("  %s: HTTP %s (skipped)" % (day, e.code), file=sys.stderr)
            continue
        for r in data.get("results") or []:
            if r.get("ordinanceCode") != ORDINANCE or r.get("docTypeCode") != DOCTYPE:
                continue
            if r.get("xbrlFlag") != "1":
                continue
            if not r.get("docID"):
                continue
            rows.append({"docID": r["docID"], "filerName": r.get("filerName"),
                         "periodEnd": r.get("periodEnd"), "date": day})
    rows.sort(key=lambda r: (r["date"], r["docID"]))
    return rows


# --- モード 2: 割り当てる(通信しない) ---------------------------------------


def allocate(rows):
    """``rows`` から開発用を除き、封じた種で ``TOTAL`` 件を引いて役割を当てる。"""

    seed, seed_sha = sealed_seed()
    pool = [r for r in rows if r["docID"] not in DEVELOPMENT_DOCS]
    pool.sort(key=lambda r: (r["date"], r["docID"]))
    if len(pool) < TOTAL:
        raise SystemExit("pool has %d rows, need %d" % (len(pool), TOTAL))
    label = "%s|%s|%s|%s" % (seed, RNG_LABEL, rows[0]["date"], rows[-1]["date"])
    picked = random.Random(label).sample(pool, TOTAL)
    out, i = [], 0
    for n, key, jp in ROLES:
        for _ in range(n):
            out.append(dict(picked[i], role=key, role_ja=jp, draw_order=i + 1))
            i += 1
    return {"seed_blob_sha256": seed_sha, "rng_label_without_the_seed":
            "<種>|%s|%s|%s" % (RNG_LABEL, rows[0]["date"], rows[-1]["date"]),
            "excluded_development_docs": list(DEVELOPMENT_DOCS),
            "candidates_total": len(rows), "pool_after_exclusion": len(pool),
            "assigned": out}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-out")
    ap.add_argument("--allocate", action="store_true")
    ap.add_argument("--candidates")
    ap.add_argument("--out")
    ap.add_argument("--from", dest="date_from", default="2026-09-01")
    ap.add_argument("--to", dest="date_to", default="2026-09-30")
    a = ap.parse_args(argv)

    if a.list_out:
        rows = list_candidates(a.date_from, a.date_to)
        with open(a.list_out, "w", encoding="utf-8") as fh:
            json.dump({"window": [a.date_from, a.date_to], "ordinance": ORDINANCE,
                       "docType": DOCTYPE, "count": len(rows), "rows": rows},
                      fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("候補 %d 件 -> %s(metadata だけ。ZIP は取っていない)" % (len(rows), a.list_out))
        return 0

    if not a.allocate:
        raise SystemExit("--list-out か --allocate のどちらかを指定する")
    if not a.candidates:
        raise SystemExit("--allocate には --candidates が要る")
    rows = json.load(open(a.candidates, encoding="utf-8"))["rows"]
    res = allocate(rows)
    print("候補 %d 件 / 開発用 %d 件を除いて %d 件 / 引いた %d 件"
          % (res["candidates_total"], len(DEVELOPMENT_DOCS), res["pool_after_exclusion"], TOTAL))
    print("種の blob sha256: %s" % res["seed_blob_sha256"])
    for r in res["assigned"]:
        print("  %2d  %-10s %-12s %-34s %s" % (r["draw_order"], r["docID"], r["role"],
                                               (r["filerName"] or "")[:34], r["periodEnd"] or ""))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("written: %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
