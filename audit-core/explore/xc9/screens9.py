# -*- coding: utf-8 -*-
u"""便 XC9: 組の画面を作って scratchpad に書く(組の番号・書く所の頭)。"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("x9", os.path.join(HERE, "xc9.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
if __name__ == "__main__":
    dev, held = m.C1.split()
    for n in [int(v) for v in sys.argv[1].split(",")]:
        _n, p, pp = [x for x in dev + held if x[0] == n][0]
        entries = m.B.load_package(p); cur = m.B.build_files(entries); prv = m.B.build_files(m.B.load_package(pp))
        sc, tmap, bmap, pt = m.build_screens(cur, prv, entries)
        for k, (s, _t) in enumerate(sc):
            with open(os.path.join(sys.argv[2], "s%d_%d.md" % (n, k)), "w", encoding="utf-8") as f:
                f.write(s)
        print(n, len(sc), [len(s) for s, _ in sc], len(tmap))
