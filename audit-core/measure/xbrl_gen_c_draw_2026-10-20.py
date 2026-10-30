# -*- coding: utf-8 -*-
u"""汎化 C(封 docs/XBRL_GENERALITY_SEAL_2026-10-20.md §1)の draw。

cd8 の規則(fixtures/xbrl/cd8/draw_2026-10-17.json の ``rule``)を **位置 59 から**続ける:
封じた並び(seed 6a24d72、母集団 256)の order[59:] を順に見て、docs/ と fixtures/
(母集団の名簿 3 file を除く)に docID が 1 度も出ていない先頭 8 件を引く。
**取得はしない。通信しない。0 USD。**キャッシュに在れば止める(未使用でなくなる)。

    python3 measure/xbrl_gen_c_draw_2026-10-20.py [--write]
"""
import argparse
import glob
import io
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POOL = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "pool2_clean_2026-10-14.json")
OUT = os.path.join(ROOT, "fixtures", "xbrl", "gen_c", "draw_2026-10-20.json")
SEAL = "docs/XBRL_GENERALITY_SEAL_2026-10-20.md"
SEED_HEX = "6a24d72"
START = 59
WANT = 8
ROSTER = ("fixtures/xbrl/holdout_p17/pool2_clean_2026-10-14.json",
          "fixtures/xbrl/holdout_p17/pool2_meta_2026-10-14.json",
          "fixtures/xbrl/candidates_2026-09.json")
CACHE = os.path.expanduser("~/.cache/audit-core/edinet")


def order_of():
    with io.open(POOL, encoding="utf-8") as fh:
        ids = sorted(json.load(fh)["pool_clean"])
    order = list(ids)
    random.Random(int(SEED_HEX, 16)).shuffle(order)
    return order


def named_in_repo(doc):
    args = ["git", "grep", "-l", doc, "--", "docs", "fixtures"] + [":(exclude)%s" % r for r in ROSTER]
    out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return [f for f in out.stdout.split() if f]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    order = order_of()
    cached = set(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(CACHE, "*.zip")))
    taken, pos, skipped = [], [], []
    for i in range(START, len(order)):
        doc = order[i]
        files = named_in_repo(doc)
        if files:
            skipped.append({u"位置": i, "docID": doc, u"名前が出た file": files[0]})
            continue
        taken.append(doc)
        pos.append(i)
        if len(taken) == WANT:
            break
    found = [d for d in taken if d in cached]
    rec = {"seal": SEAL,
           "rule": u"cd8 の規則(fixtures/xbrl/cd8/draw_2026-10-17.json)を位置 %d から続ける: "
                   u"order[%d:] を順に見て、名簿以外で名前が出ていない先頭 %d 件" % (START, START, WANT),
           "seed_hex": SEED_HEX, "pool": len(order), u"開始の位置": START,
           u"引いた 8 件": taken, u"位置": pos, u"飛ばした件": skipped,
           u"**キャッシュに在るか**": {u"在った": found,
                                   "note": u"1 件も無い = 一度も取っていない" if not found else u"**在る = 未使用でない。止める**"},
           u"取得": u"**していない**(EDINET_API_KEY は人間が渡す。段 B)"}
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    if found:
        raise SystemExit(u"**キャッシュに在る: %s。未使用でなくなるので止める**" % found)
    if a.write:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
