# -*- coding: utf-8 -*-
u"""便 XC9 の天井: 今年の答えから「正しい塊の範囲」を作り、席が完全に答えた時に置ける数を数える(開発の確かめだけ。席には見せない)。"""
import bisect, collections, importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("x9", os.path.join(HERE, "xc9.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def oracle(cur, tmap, bmap):
    ans = {}
    truth = {}
    for name, plain, F, _H in cur:
        for f in F:
            if f["kind"] == "nonNumeric" and m.is_tb(f["attrs"]):
                truth.setdefault((name, f["attrs"].get("name"), f["attrs"].get("contextRef")), m.trim(plain, f["start"], f["end"]))
    plain_of = dict((nm, pl) for nm, pl, _F, _H in cur)
    for tid, (name, a, _eb) in tmap.items():
        t = truth.get((name, a.get("name"), a.get("contextRef")))
        if not t:
            continue
        bl = bmap[name]
        st = [s for s, _e in bl]
        i = bisect.bisect_left(st, t[0])
        js = [k for k, (s, e) in enumerate(bl) if e <= t[1]]
        if i < len(bl) and js and m.trim(plain_of[name], bl[i][0], bl[js[-1]][1]) == t:
            ans[tid] = ["B%d" % i, "B%d" % js[-1]]
    return ans


if __name__ == "__main__":
    dev, held = m.C1.split()
    tot = collections.Counter()
    for n, p, pp in [x for x in dev + held if x[0] in [int(v) for v in sys.argv[1].split(",")]]:
        entries = m.B.load_package(p); cur = m.B.build_files(entries); prv = m.B.build_files(m.B.load_package(pp))
        sc, tmap, bmap, pt = m.build_screens(cur, prv, entries)
        ans = oracle(cur, tmap, bmap)
        added, c = m.place_answers(cur, tmap, bmap, pt, ans)
        c.update(m.score(cur, added, pt)); c[u"T"] += len(tmap)
        print(n, dict(c)); tot.update(c)
    print("計", dict(tot))
