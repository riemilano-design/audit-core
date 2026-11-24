# -*- coding: utf-8 -*-
"""便 SV13: SV10 の build_sv10.py を、会社 18・19・20 と SV13 の根に当てる(封 explore/sv13/SEAL.md §1)。

使い方: python3 -I build_sv13.py <explore の folder> <文の行を足す前の根> <SV13 の根> <会社の番号…>
前の根の r1/store{n}/貯め.csv と r1/map{n}.json に、<SV13 の根>/out{n}/文の数.json の数を足し、<SV13 の根>/r1 に書く。
"""
import os
import sys

EXPLORE, BASE, ROOT, NUMS = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
sys.path.insert(0, os.path.join(EXPLORE, "sv10"))
import build_sv10  # noqa: E402

build_sv10.NUMS = NUMS
sys.argv = ["", BASE, ROOT]
build_sv10.main()
