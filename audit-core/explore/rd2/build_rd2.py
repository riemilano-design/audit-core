# -*- coding: utf-8 -*-
"""便 RD2: RD0 の build_rd0.py を `#` 7〜17 の 11 社に当て、番号を 31〜41 にする(封 explore/rd2/SEAL.md §1)。

使い方: python3 -I build_rd2.py <audit-core の folder> <RD2 の根>
減価償却費の要素が無い社は、同じ枠の DepreciationAndOtherAmortizationOpeCF を正解にする(封 §1 で足した 1 つ)。
"""
import json
import os
import shutil
import sys

AC, ROOT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(AC, "explore", "rd0"))
sys.argv = ["", AC, os.path.join(ROOT, "_tmp")]
import build_rd0 as B  # noqa: E402

ROWS = [str(i) for i in range(7, 18)]
ALT = "DepreciationAndOtherAmortizationOpeCF"


def main():
    B.ROWS = ROWS
    B.main()
    d = json.load(open(os.path.join(AC, "fixtures/xbrl/tanshin/fetched_2026-11-09.json"), encoding="utf-8"))
    rows = {str(r["#"]): r for r in d["行"]}
    sha2path = {}
    import hashlib
    for sub in ("edinet", "edinet-fresh-2026-10-21", "edinet-prior-2026-11-02"):
        for f in os.listdir(os.path.join(B.CACHE, sub)):
            p = os.path.join(B.CACHE, sub, f)
            sha2path[hashlib.sha256(open(p, "rb").read()).hexdigest()] = p
    for i, key in enumerate(ROWS):
        src = os.path.join(ROOT, "_tmp", "co" + str(21 + i))
        num = str(31 + i)
        dst = os.path.join(ROOT, "co" + num)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.move(src, dst)
        gp = os.path.join(dst, "正解", "正解.json")
        gold = json.load(open(gp, encoding="utf-8"))
        if gold["期1"].get("減価償却費_当期") is None:
            inst = B.load_instance(open(sha2path[rows[key]["有報の ZIP の sha256"]], "rb").read())
            facts = inst["facts"]
            cons = B.value(facts, None, "NetSales", "CurrentYearDuration") is not None or B.value(facts, None, "Assets", "CurrentYearInstant") is not None
            v = B.value(facts, None, ALT, "CurrentYearDuration" + ("" if cons else B.NONCON))
            if v is not None:
                gold["期1"]["減価償却費_当期"] = v
                json.dump(gold, open(gp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                tp = os.path.join(dst, "正解", "罠.json")
                trap = json.load(open(tp, encoding="utf-8"))
                trap["無い"] = [x for x in trap["無い"] if x != "減価償却費_当期"]
                json.dump(trap, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(num, "減価償却費 を", ALT, "で埋めた")
    os.rmdir(os.path.join(ROOT, "_tmp"))


if __name__ == "__main__":
    main()
