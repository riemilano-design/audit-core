# -*- coding: utf-8 -*-
"""新領域① の材料を**一度だけ**取得する(封 docs/DOMAIN1_FETCH_SEAL_2026-10-15.md)。

取得先は東京都オープンデータカタログの公開 xlsx 3 件(CC BY)。鍵は要らない。
**生ファイルは repo に置かない**(`~/.cache/audit-core/sheet/`)。
記録 `fixtures/sheet/opened_2026-10-15.json` が既に在れば**拒否する**。
失敗したファイルは**別のファイルで埋めない**(失敗として記録する)。

印字するのは名前・バイト数・sha256 だけ。  usage: python3 measure/sheet_fetch_2026-10-15.py
"""
import datetime
import hashlib
import io
import json
import os
import subprocess
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "sheet", "opened_2026-10-15.json")
CACHE = os.path.expanduser("~/.cache/audit-core/sheet")
BASE = "https://www.opendata.metro.tokyo.lg.jp/kaikeikanri/"
DATASET = ("令和６年度東京都各会計歳入歳出決算書及び東京都各会計歳入歳出決算附属書類等"
           "(東京都会計管理局、CC BY 4.0)")
FILES = [("決算書 総括", "op20251218_06kessan_01_soukatu.xlsx", 14016),
         ("決算書 歳出", "op20251218_06kessan_03_saisyutu.xlsx", 90015),
         ("事項別明細 歳出", "op20251218_06kessan_05_jikoubetu_saisyutu.xlsx", 2126397)]


def cache_path(name):
    return os.path.join(CACHE, name)


def main():
    if os.path.exists(OUT):
        raise SystemExit("記録が既に在る: %s(取得は一度だけ)" % OUT)
    os.makedirs(CACHE, exist_ok=True)
    head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                   cwd=ROOT).decode().strip()
    log, sha = [], {}
    for label, name, want in FILES:
        url = BASE + name
        p = cache_path(name)
        if os.path.exists(p):
            log.append({"name": name, "result": "already_present"})
        else:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "audit-core/domain1"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read()
                    mod = r.headers.get("Last-Modified")
                with io.open(p, "wb") as fh:
                    fh.write(body)
                log.append({"name": name, "result": "fetched", "last_modified": mod})
            except Exception as e:                      # 失敗は失敗として記録する
                log.append({"name": name, "result": "failed", "error": type(e).__name__})
                continue
        b = io.open(p, "rb").read()
        sha[name] = {"label": label, "sha256": hashlib.sha256(b).hexdigest(),
                     "bytes": len(b), "expected_bytes": want, "url": url}
        print("%-44s %9d B  %s" % (name, len(b), sha[name]["sha256"][:16]))
    rec = {"seal": "docs/DOMAIN1_FETCH_SEAL_2026-10-15.md",
           "dataset": DATASET,
           "license": "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/deed.ja)",
           "source": "東京都オープンデータカタログサイト / 東京都会計管理局",
           "opened_at": datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
           "engine_commit": head, "cache_dir": "~/.cache/audit-core/sheet",
           "fetch_log": log, "files": sha, "present": len(sha)}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("present %d / %d ->" % (len(sha), len(FILES)), OUT)


if __name__ == "__main__":
    main()
