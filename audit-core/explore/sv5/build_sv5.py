# -*- coding: utf-8 -*-
"""便 SV5: SV1 の build_store.py を会社 12・13・14 に当てる(封 explore/sv5/SEAL.md §1)。

使い方: python3 -I build_sv5.py <explore の folder> <SV5 の根> <会社の番号…>
<SV5 の根>/r0(素材と札)から <SV5 の根>/r1 に store{n}/貯め.csv と map{n}.json を作る。
"""
import os
import sys

EXPLORE, ROOT, NUMS = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.path.insert(0, os.path.join(EXPLORE, "sv0"))
sys.path.insert(0, os.path.join(EXPLORE, "sv1"))
import tally  # noqa: E402
import build_store  # noqa: E402

tally.COMPANIES = NUMS
sys.argv = ["", os.path.join(EXPLORE, "sv0"), os.path.join(ROOT, "r0"), os.path.join(ROOT, "r1")]
build_store.main()
