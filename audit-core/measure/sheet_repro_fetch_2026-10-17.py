# -*- coding: utf-8 -*-
"""別資料(令和５年度)を**一度だけ**取得する(封 docs/DOMAIN1_REPRO_SEAL_2026-10-17.md §1)。

同じ発行者・同じ構成の別年度。**CC BY 4.0・鍵は要らない。**
**生ファイルは repo に置かない**(`~/.cache/audit-core/sheet/`)。
記録が既に在れば**拒否する。失敗した file を別の file で埋めない。**
**実質収支は取らない**(歳入と歳出から導出される数)。

印字するのは名前・バイト数・sha256 だけ。
  usage: python3 measure/sheet_repro_fetch_2026-10-17.py
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
SEAL = "docs/DOMAIN1_REPRO_SEAL_2026-10-17.md"
OUT = os.path.join(ROOT, "fixtures", "sheet", "repro_opened_2026-10-17.json")
CACHE = os.path.expanduser("~/.cache/audit-core/sheet")
BASE = "https://www.opendata.metro.tokyo.lg.jp/kaikeikanri/"
DATASET = ("令和５年度東京都各会計歳入歳出決算書及び東京都各会計歳入歳出決算附属書類等"
           "(東京都会計管理局、CC BY 4.0、カタログ t000016d1700000015)")
# **封 §1 の表。HEAD で見たバイト数を字で留める**(違ったら記録に残る)
FILES = [("総括", "op20250114_05kessan_01_soukatu.xlsx", 17339),
         ("決算書 歳入", "op20250114_05kessan_02_sainyuu.xlsx", 100564),
         ("決算書 歳出", "op20250114_05kessan_03_saisyutu.xlsx", 94966),
         ("事項別明細 歳入", "op20250114_05kessan_04_jikoubetu_sainyuu.xlsx", 754510),
         ("事項別明細 歳出", "op20250114_05kessan_05_jikoubetu_saisyutu.xlsx",
          2047161)]
NOT_FETCHED = [("実質収支", "op20250114_05kessan_06_jissitusyuusi.xlsx",
                "歳入と歳出から導出される数。封 §1")]
SOUKATU = FILES[0][1]
SAINYUU = FILES[1][1]
KESSAN = FILES[2][1]
MEISAI_SAINYUU = FILES[3][1]
MEISAI = FILES[4][1]


def cache_path(name):
    return os.path.join(CACHE, name)


def main():
    if os.path.exists(OUT):
        raise SystemExit("記録が既に在る: %s(取得は一度だけ)" % OUT)
    os.makedirs(CACHE, exist_ok=True)
    head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                   cwd=ROOT).decode().strip()
    log = []
    for label, name, want in FILES:
        p = cache_path(name)
        if os.path.exists(p):
            log.append({"label": label, "name": name, "result": "already_present"})
        else:
            try:
                with urllib.request.urlopen(BASE + name, timeout=120) as r:
                    data = r.read()
                io.open(p, "wb").write(data)
                log.append({"label": label, "name": name, "result": "fetched"})
            except Exception as e:           # **失敗は失敗として記録する**
                log.append({"label": label, "name": name, "result": "failed",
                            "why": "%s: %s" % (type(e).__name__, e)})
                continue
        b = io.open(p, "rb").read()
        log[-1].update({"bytes": len(b),
                        "bytes_matches_seal": len(b) == want,
                        "expected_bytes": want,
                        "sha256": hashlib.sha256(b).hexdigest()})
    rec = {"seal": SEAL, "dataset": DATASET, "base": BASE,
           "fetched_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
           "repo_head": head, "cache": CACHE,
           "**生ファイルは repo に置かない**": True,
           "**取らなかったもの**": [{"label": l, "name": n, "why": w}
                           for l, n, w in NOT_FETCHED],
           "files": log,
           "全部そろった": all(x.get("result") in ("fetched", "already_present")
                        for x in log),
           "バイト数が封と一致": all(x.get("bytes_matches_seal") for x in log)}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for x in log:
        print("%-14s %-48s %-16s %s %s"
              % (x["label"], x["name"], x["result"], x.get("bytes"),
                 (x.get("sha256") or "")[:16]))
    print("全部そろった: %s / バイト数が封と一致: %s"
          % (rec["全部そろった"], rec["バイト数が封と一致"]))
    for x in NOT_FETCHED:
        print("取らなかった: %s(%s)" % (x[1], x[2]))
    print("->", OUT)


if __name__ == "__main__":
    main()
