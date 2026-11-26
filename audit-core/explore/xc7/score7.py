# -*- coding: utf-8 -*-
u"""便 XC7 の席の答えを採点する(組の番号・答えの file の頭・画面の数)。要素の名だけを見せる(文脈は見せない)。"""
import importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("x", os.path.join(HERE, "xc7.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def run(pair, prefix, verbose=True):
    dev, held = m.C1.split()
    n, p, pp = [x for x in dev + held if x[0] == pair][0]
    entries = m.B.load_package(p); cur = m.B.build_files(entries); prv = m.B.build_files(m.B.load_package(pp))
    screens, marks, placed = m.build_screen(cur, prv, entries)
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None); res = m.C0.shift_resources(prior_H)
    ans = {}
    for k in range(len(screens)):
        ans.update(json.load(open(prefix + "_%d.json" % k)))
    c = m.score_answers(cur, marks, ans, res, m.C6.OWN[0])
    truth = {(nm, e["start"], e["end"]): e["attrs"] for nm, _p, F, _H in cur for e in F if e["kind"] == "nonFraction"}
    c["答えの数の fact"] = len(truth)
    c["規則で置いた中の答えの fact"] = len(set(truth) & set(placed))
    if verbose:
        for mid, (nm, s, e, _) in marks.items():
            a = ans.get(mid)
            if not a:
                continue
            t = truth.get((nm, s, e))
            if t is None:
                print(u"無", a.get("name"))
            elif m.norm_tag(t) != m.norm_tag(a):
                print(u"違", [k for k in m.ATTRS if str(a.get(k) or "") != str(t.get(k) or "")], a.get("name"), "->", t.get("name"))
    return c


if __name__ == "__main__":
    c = run(int(sys.argv[1]), sys.argv[2])
    for k, v in sorted(c.items()):
        print(k, v)
