# -*- coding: utf-8 -*-
"""封 docs/XBRL_GENERALITY_SEAL_2026-10-20.md §6 の段 B ― **汎化 C の未使用 8 書類を取得する。費用 0 USD(EDINET は無料)。**

**鍵は環境変数 `EDINET_API_KEY` から取る。値は読まない・印字しない・記録しない。**
生 ZIP は `~/.cache/audit-core/edinet/` にしか置かない(repo に入れない)。

やること
  1. 引いた 8 件を `fixtures/xbrl/gen_c/draw_2026-10-20.json` から読む(**引き直さない**)
  2. **取得前にキャッシュに無いことを確かめる**(在ったら止める ― 未使用でなくなる)
  3. 取得して **バイト数と sha256** を記録する
  4. **記録に鍵らしい字が無いことを確かめてから書く**

    EDINET_API_KEY=... python3 measure/xbrl_gen_c_fetch_2026-10-20.py
"""
import datetime
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from adapters.xbrl import edinet as ED   # noqa: E402

FX = os.path.join(ROOT, "fixtures", "xbrl", "gen_c")
DRAW = os.path.join(FX, "draw_2026-10-20.json")
OUT = os.path.join(FX, "fetched_2026-10-20.json")
SEAL = "docs/XBRL_GENERALITY_SEAL_2026-10-20.md"
KEY_NAME = "EDINET_API_KEY"
KEYISH = re.compile(r"[A-Za-z0-9]{32,}")


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(取り直さない)" % OUT)
    if not os.environ.get(KEY_NAME):
        raise SystemExit("**%s が無い。封 §6 の段 B で止まる**" % KEY_NAME)
    docs = json.load(io.open(DRAW, encoding="utf-8"))["引いた 8 件"]
    if len(docs) != 8:
        raise SystemExit("**引いた件数が 8 でない。止める**")
    pre = [d for d in docs if os.path.exists(ED.cache_path(d))]
    if pre:
        raise SystemExit("**取得前にキャッシュに在る: %s。未使用でなくなるので止める**"
                         % pre)
    rows = []
    for d in docs:
        ED.fetch(d)
        path = ED.cache_path(d)
        with io.open(path, "rb") as fh:
            blob = fh.read()
        rows.append({"docID": d, "bytes": len(blob),
                     "sha256": hashlib.sha256(blob).hexdigest(),
                     "cache": "~/.cache/audit-core/edinet/%s" % os.path.basename(path)})
        print("  %s %10d bytes  %s" % (d, len(blob), rows[-1]["sha256"][:16]))
    rec = {"seal": SEAL, "step": "**汎化 C の封 §6 の段 B。取得。費用 0 USD(EDINET は無料)**",
           "鍵": {"環境変数の名前": KEY_NAME,
                 "値": "**読まない・印字しない・記録しない**"},
           "取得した書類": rows,
           "合計バイト": sum(r["bytes"] for r in rows),
           "取得した時刻(UTC)": datetime.datetime.utcnow().isoformat() + "Z",
           "置いた場所": "**`~/.cache/audit-core/edinet/` だけ。repo に生 ZIP は入れない**",
           "**1 度しか開かない**": ("封 `HOLDOUT_SPLIT_SEAL_2026-10-14` の守ること 4。"
                            "この 8 件は C0 のあと使用済みへ移る"),
           "limits": ["**取得しただけである。**本文も fact も 1 件も読んでいない",
                      "**席は 1 回も呼んでいない**"]}
    blob = json.dumps(rec, ensure_ascii=False)
    leaks = [s for s in KEYISH.findall(blob) if not re.fullmatch(r"[0-9a-f]{32,}", s)]
    if leaks:
        raise SystemExit("**鍵らしい字が記録に在る。書かずに止める**")
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== 汎化 C 段 B: 取得 8 件 / 合計 %d bytes ===" % rec["合計バイト"])
    print("->", OUT)


if __name__ == "__main__":
    main()
