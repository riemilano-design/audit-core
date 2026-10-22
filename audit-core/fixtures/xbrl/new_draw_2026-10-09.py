# -*- coding: utf-8 -*-
"""封 docs/XBRL_NEW_DRAW_SEAL_2026-10-09.md の算法をそのまま実行する。

**通信しない。ZIP は取らない。** metadata だけを読み、引いた 4 件と割当を記録する。
種は本線が 2026-10-09 に Golden 更新をコミットした sha(私が作った値ではない)。
"""

import json
import os
import random
import sys

SEED = "749c12b"
RNG_LABEL = "new-draw-2026-10-09|truncate+A1"
HERE = os.path.dirname(os.path.abspath(__file__))

# 封 §1 の除く群。**字で書く。**
DEVELOPMENT_DOCS = ("S100Z4Q1", "S100Z4B6", "S100YMFV", "S100Z37J")   # ADAPTER_USED 3 件を含む
READ_INDEPENDENT = ("S100Z3BW", "S100Z4DE")                            # 読んだ(集計が公開済み)
SEALED_2026_10_08 = ("S100Z2S2", "S100Z359", "S100Z2RN", "S100Z3PT", "S100Z3T5",
                     "S100Z38M", "S100Z1T7", "S100Z3WK", "S100Z3CG", "S100Z2EI")
ROLELESS_FETCHED = ("S100Z1WR", "S100Z433", "S100Z39P", "S100Z4N9")
EXCLUDE = DEVELOPMENT_DOCS + READ_INDEPENDENT + SEALED_2026_10_08 + ROLELESS_FETCHED

# 封 §4 の割当。**引く順だけで決める。**
ASSIGNMENT = ("本線の truncate 封", "本線の truncate 封", "A1 封(① 差の許容幅)", "A1 封(① 差の許容幅)")


def main():
    cand = json.load(open(os.path.join(HERE, "candidates_2026-09.json"), encoding="utf-8"))
    rows = cand["rows"]
    present = [d for d in EXCLUDE if any(r["docID"] == d for r in rows)]
    pool = [r for r in rows if r["docID"] not in EXCLUDE]
    pool.sort(key=lambda r: (r["date"], r["docID"]))
    label = "%s|%s|%s|%s" % (SEED, RNG_LABEL, pool[0]["date"], pool[-1]["date"])
    picked = random.Random(label).sample(pool, 4)

    print("候補 %d 件 / 除く字の数 %d 件(うち候補に実在 %d 件)/ 母集団 %d 件"
          % (len(rows), len(EXCLUDE), len(present), len(pool)))
    print("python3 %s" % sys.version.split()[0])
    print("rng label(種を除く): <種>|%s|%s|%s" % (RNG_LABEL, pool[0]["date"], pool[-1]["date"]))
    print()
    print("引いた 4 件(引いた順。割当は封の表どおり):")
    out = []
    for i, (r, role) in enumerate(zip(picked, ASSIGNMENT), 1):
        print("  %d. %-10s %-30s %s  -> %s" % (i, r["docID"], r.get("filerName", "")[:30], r["date"], role))
        out.append({"order": i, "docID": r["docID"], "filerName": r.get("filerName"),
                    "date": r["date"], "seal": role})
    rec = {"tool": "new_draw_2026-10-09.py", "seed_source": "本線 749c12b(Golden 更新)",
           "rng_label_without_the_seed": "<種>|%s|%s|%s" % (RNG_LABEL, pool[0]["date"], pool[-1]["date"]),
           "python": sys.version.split()[0],
           "candidates_total": len(rows), "excluded_names": len(EXCLUDE),
           "excluded_present_in_candidates": len(present), "pool": len(pool),
           "picked": out, "zips_fetched": False}
    path = os.path.join(HERE, "new_draw_2026-10-09.json")
    json.dump(rec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print()
    print("記録 -> %s(**ZIP は取っていない**)" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
