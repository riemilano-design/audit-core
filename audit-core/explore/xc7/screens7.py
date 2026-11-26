# -*- coding: utf-8 -*-
u"""便 XC7: 組の画面を作って scratchpad に書く(組の番号・書く所の頭)。会社の素材の画面は repo に入れない。"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("x", os.path.join(HERE, "xc7.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

if __name__ == "__main__":
    pair, prefix = int(sys.argv[1]), sys.argv[2]
    dev, held = m.C1.split()
    n, p, pp = [x for x in dev + held if x[0] == pair][0]
    entries = m.B.load_package(p); cur = m.B.build_files(entries); prv = m.B.build_files(m.B.load_package(pp))
    screens, marks, placed = m.build_screen(cur, prv, entries)
    for k, (s, _ids) in enumerate(screens):
        with open(prefix + "_%d.md" % k, "w", encoding="utf-8") as f:
            f.write(s)
    print(pair, len(screens), len(marks))
