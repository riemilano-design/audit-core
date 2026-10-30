# -*- coding: utf-8 -*-
"""① 実費の確定のうち**私の記録で確かめられる部分**(人間の指示 2026-10-17)。

> 過去の課金記録から、モデル名、入力トークン、出力トークン、実請求額を確認します。
> **集計トークンしか残っていないなら、正確な内訳は取得できなかったと記録し、
> 推定を実測扱いしないこと。**

**課金の記録そのものは私から見えない。**私が機械で確かめられるのは
「**repo の記録に入出力の内訳が在るか**」だけである。それを全部の記録で数える。
**0 USD。通信しない。**

    python3 measure/xbrl_cost_records_2026-10-17.py
"""
import collections
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "cost_records_2026-10-17.json")

# 入出力の内訳を名乗る欄の字(**在れば拾う。無ければ無いと書く**)
IN_WORDS = ("input_tokens", "入力トークン", "prompt_tokens", "入力")
OUT_WORDS = ("output_tokens", "出力トークン", "completion_tokens")
TOTAL_WORDS = ("使ったトークン", "total_tokens", "トークン(実測)", "tokens")
BILL_WORDS = ("実請求", "invoice", "billed", "請求額")


def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            for r in walk(v, "%s/%s" % (path, k)):
                yield r
            yield (path + "/" + k, k, v)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            for r in walk(v, "%s[%d]" % (path, i)):
                yield r


def has_word(key, words):
    return any(w in key for w in words)


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    files = []
    for base, _, names in os.walk(os.path.join(ROOT, "fixtures")):
        for n in names:
            if n.endswith(".json"):
                files.append(os.path.join(base, n))
    rows, counts = [], collections.Counter()
    for f in sorted(files):
        try:
            j = json.load(io.open(f, encoding="utf-8"))
        except ValueError:
            counts["読めなかった"] += 1
            continue
        ins, outs, totals, bills, models = [], [], [], [], []
        for path, key, val in walk(j):
            if isinstance(val, (dict, list)):
                continue
            if has_word(key, IN_WORDS) and isinstance(val, (int, float)):
                ins.append((path, val))
            if has_word(key, OUT_WORDS) and isinstance(val, (int, float)):
                outs.append((path, val))
            if has_word(key, TOTAL_WORDS) and isinstance(val, (int, float)):
                totals.append((path, val))
            if has_word(key, BILL_WORDS):
                bills.append((path, val))
            if key == "model" and isinstance(val, str):
                models.append(val)
        if not (ins or outs or totals or bills):
            continue
        rel = os.path.relpath(f, ROOT)
        rows.append({"file": rel, "model": sorted(set(models)),
                     "入力の欄": ins, "出力の欄": outs,
                     "合計の欄": [t[0] for t in totals],
                     "合計の値": [t[1] for t in totals],
                     "請求額の欄": bills})
        counts["トークンの記録が在る file"] += 1
        counts["入出力の内訳が在る file"] += 1 if (ins and outs) else 0
        counts["合計だけの file"] += 1 if (totals and not (ins and outs)) else 0
        counts["実請求額が在る file"] += 1 if bills else 0
    rec = {"step": "**① のうち私が機械で確かめられる部分。0 USD・通信なし**",
           "**課金の記録は私から見えない**": (
               "見えるのは repo の記録だけ。**モデル名・実請求額・入出力の単価は"
               "人間が課金の画面で確かめる必要が在る**"),
           "数えた file": len(files), "内訳": dict(counts),
           "**判定**": ("**入出力の内訳は 1 件も無い**"
                     if counts["入出力の内訳が在る file"] == 0
                     else "**内訳が在る file が %d 件**"
                          % counts["入出力の内訳が在る file"]),
           "**だから**": ("**前便の 2.94 USD は仮定のままである。**"
                       "**推定を実測として扱わない**(人間の指示)"),
           "記録ごと": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== ① 記録の中の入出力の内訳(0 USD)===")
    print("数えた json: %d / トークンの記録が在る: %d"
          % (len(files), counts["トークンの記録が在る file"]))
    print("**入出力の内訳が在る: %d / 合計だけ: %d / 実請求額が在る: %d**"
          % (counts["入出力の内訳が在る file"], counts["合計だけの file"],
             counts["実請求額が在る file"]))
    for r in rows:
        print("  %-62s model %s / 合計 %s / 入 %d 欄 / 出 %d 欄"
              % (r["file"][:62], ",".join(r["model"]) or "-",
                 r["合計の値"], len(r["入力の欄"]), len(r["出力の欄"])))
    print("**判定: %s**" % rec["**判定**"])
    print("->", OUT)


if __name__ == "__main__":
    main()
