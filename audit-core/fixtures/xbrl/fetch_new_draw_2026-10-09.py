# -*- coding: utf-8 -*-
"""抽選 341e079 のうち **A1 封に割り当てられた 2 件だけ**を取る。

**本線の truncate 封に割り当てられた 2 件は取らない** ―
取得は席ごとの承認が要る行為で、席の間で承認は渡せない
(本線の席が 2026-10-09 に明言。同意した)。この道具は
``seal`` が A1 封でない docID を**拒否する**。

鍵は環境変数 ``EDINET_API_KEY`` から読む。**値は印字も保存もしない。**
ZIP は ``~/.cache/audit-core/edinet/`` に置く(**リポジトリの外**)。
記録に残すのは docID・社名・バイト数・sha256・中身の印だけ。**中身は見ない。**
「取った」のか「すでに手元に在った」のかを**区別して印字し、記録にも残す**
(人間の指示、2026-10-09)。
"""

import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from adapters.xbrl import edinet as E                      # noqa: E402
from fixtures.xbrl.zip_content_digest import content_digest  # noqa: E402

FETCHABLE_SEAL = "A1 封(① 差の許容幅)"
API = "https://api.edinet-fsa.go.jp/api/v2/documents/%s?type=1&Subscription-Key=%s"


def main():
    key = os.environ.get("EDINET_API_KEY")
    if not key:
        print("環境変数 EDINET_API_KEY が無い。鍵の値はこの道具に書かない。")
        return 2
    rec = json.load(open(os.path.join(HERE, "new_draw_2026-10-09.json"), encoding="utf-8"))
    out = []
    for row in rec["picked"]:
        doc, seal = row["docID"], row["seal"]
        if seal != FETCHABLE_SEAL:
            print("  %-10s **取らない**(%s ― 席の間で承認は渡せない)" % (doc, seal))
            continue
        path = E.cache_path(doc)
        had = os.path.exists(path)
        if not had:
            with urllib.request.urlopen(API % (doc, key), timeout=120) as r:
                data = r.read()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "wb").write(data)
        import hashlib
        zb = open(path, "rb").read()
        digest, members = content_digest(zb)
        out.append({"docID": doc, "filerName": row.get("filerName"), "seal": seal,
                    "bytes": len(zb), "zip_sha256": hashlib.sha256(zb).hexdigest(),
                    "content_digest": [digest, members],
                    "how": "すでに手元に在った" if had else "取った"})
        print("  %-10s %-24s %8d bytes  zip=%s…  中身の印=%s…(目録 %d 本)  (%s)"
              % (doc, (row.get("filerName") or "")[:24], len(zb),
                 out[-1]["zip_sha256"][:12], digest[:12], members, out[-1]["how"]))
    p = os.path.join(HERE, "fetched_new_draw_2026-10-09.json")
    json.dump({"tool": "fetch_new_draw_2026-10-09.py", "fetched": out},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("記録 -> %s  **中身は読んでいない**(中身の印は ZIP の目録だけから作っている)" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
