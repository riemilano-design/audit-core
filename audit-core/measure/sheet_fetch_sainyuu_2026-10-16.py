# -*- coding: utf-8 -*-
"""歳入側の材料を**一度だけ**取得する(封 docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md)。

人間の判断 2026-10-16:
> 歳入側のファイルを取得する。ただし**取得した時点で本実験を続行するのではなく、
> 段 10 の停止規則を維持したまま、独立証拠として使えるかを先に測る。**
> 取得するのは**今回の目的に必要な歳入側の資料に限定**する。

取得先は段 9 まで使ったのと**同じデータセット**(東京都オープンデータカタログ・CC BY 4.0)。
**鍵は要らない。生ファイルは repo に置かない**(`~/.cache/audit-core/sheet/`)。
記録 `fixtures/sheet/opened_sainyuu_2026-10-16.json` が既に在れば**拒否する**。
**失敗したファイルは別のファイルで埋めない**(失敗として記録する)。
**実質収支 file は取得しない**(歳入と歳出から導出される数。封 §1)。

印字するのは名前・バイト数・sha256 だけ。
  usage: python3 measure/sheet_fetch_sainyuu_2026-10-16.py
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
SEAL = "docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md"
OUT = os.path.join(ROOT, "fixtures", "sheet", "opened_sainyuu_2026-10-16.json")
CACHE = os.path.expanduser("~/.cache/audit-core/sheet")
BASE = "https://www.opendata.metro.tokyo.lg.jp/kaikeikanri/"
DATASET = ("令和６年度東京都各会計歳入歳出決算書及び東京都各会計歳入歳出決算附属書類等"
           "(東京都会計管理局、CC BY 4.0)")
# 封 §1 の表。**HEAD で見たバイト数**を字で留める(違ったら記録に残る)
FILES = [("決算書 歳入", "op20251218_06kessan_02_sainyuu.xlsx", 96925),
         ("事項別明細 歳入", "op20251218_06kessan_04_jikoubetu_sainyuu.xlsx", 706250)]
# **取らないもの。**実質収支は歳入と歳出から導出されるので R-独立-2 で丸ごと落ちる
NOT_FETCHED = [("実質収支", "op20251218_06kessan_06_jissitusyuusi.xlsx",
                "歳入と歳出から導出される数。封 §1・R-独立-2")]

SAINYUU = FILES[0][1]
MEISAI_SAINYUU = FILES[1][1]


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
                req = urllib.request.Request(
                    url, headers={"User-Agent": "audit-core/domain1"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    body = r.read()
                    mod = r.headers.get("Last-Modified")
                with io.open(p, "wb") as fh:
                    fh.write(body)
                log.append({"name": name, "result": "fetched", "last_modified": mod})
            except Exception as e:              # **失敗は失敗として記録する**
                log.append({"name": name, "result": "failed", "error": type(e).__name__})
                continue
        b = io.open(p, "rb").read()
        sha[name] = {"label": label, "sha256": hashlib.sha256(b).hexdigest(),
                     "bytes": len(b), "expected_bytes": want, "url": url}
        print("%-48s %9d B  %s" % (name, len(b), sha[name]["sha256"][:16]))

    rec = {"seal": SEAL,
           "purpose": ("**独立した証拠になるかを測るための取得**。"
                       "取得しただけでは本実験を続行しない(封 §2)"),
           "dataset": DATASET,
           "license": "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/deed.ja)",
           "source": "東京都オープンデータカタログサイト / 東京都会計管理局",
           "opened_at": datetime.datetime.now().astimezone()
                        .replace(microsecond=0).isoformat(),
           "engine_commit": head, "cache_dir": "~/.cache/audit-core/sheet",
           "fetch_log": log, "files": sha, "present": len(sha),
           "not_fetched": [{"label": l, "name": n, "why": w}
                           for l, n, w in NOT_FETCHED],
           "scope_note": ("**他の年度・他の自治体は取らない**(人間の指示 2026-10-16)。"
                          "令和 5〜2 年度も同じ構成で公開されているが、"
                          "**今回の結果を見てから判断する**"),
           "not_a_continuation": ("**段 10 の停止規則は維持する。**"
                                  "診断で新しい正しい接続が 1 件も生まれなければ"
                                  "この経路は打ち切る。**規則も閾値も緩めない**")}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("->", OUT)
    bad = [x for x in log if x["result"] == "failed"]
    if bad:
        print("**失敗 %d 件(別の file で埋めない)**" % len(bad))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
