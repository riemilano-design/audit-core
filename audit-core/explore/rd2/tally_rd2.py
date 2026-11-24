# -*- coding: utf-8 -*-
"""便 RD2 の照合と集計(封 explore/rd2/SEAL.md §2)。RD0 の tally_rd0.py を、会社の番号 31〜41 に替えて走らせる。

使い方: python3 -I tally_rd2.py <explore の folder> <RD2 の根> <record.json の path>
"""
import os
import sys

EXPLORE, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(EXPLORE, "rd0"))
import tally_rd0 as R  # noqa: E402  (sys.argv をそのまま読む)

NUMS = [str(i) for i in range(31, 42)]
R.NUMS = NUMS
R.tally.COMPANIES = NUMS
R.tally_sv10.NUMS = NUMS

if __name__ == "__main__":
    R.main()
