# -*- coding: utf-8 -*-
u"""便 XC2: 便 XC1(R1+R2)の置き方に 2 つの規則を足し、止めた fact を減らす。

R3 同じ字の行: 同じ表の中に同じ行の字が 2 回以上出る時、行の鍵の字に「何回目か」を足す(今年の側も前の年の側も同じ)。
R4 空だった升: 前の年のその升が空の fact だけ(桁・書式が無い)で今年は数が在る時、前の年の同じ表の同じ列 (h, th, td) の
   空でない fact の (decimals, scale, format) が 1 つに決まれば、それを使う。
今年の答えは置く部品に渡さない(便 XC0・XC1 と同じ)。便 XC1 の file は読み込んで関数を呼ぶだけ。
"""
import bisect
import collections
import contextlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc2_xc1", os.path.join(os.path.dirname(HERE), "xc1", "xc1.py"))
C1 = importlib.util.module_from_spec(spec)
sys.modules["_xc2_xc1"] = C1
spec.loader.exec_module(C1)
C0 = C1.C0
B = C1.B
od = collections.OrderedDict
BASE_RULES = ("R1", "R2")
_row_keys0 = C0.row_keys


def row_keys_occ(plain):
    u"""便 XC0 の ``row_keys`` に、同じ表の中の同じ字の何回目かを足す(2 回目から ``字#1``・``字#2``…。1 回目は字のまま)。"""
    out, seen = [], collections.Counter()
    for h, th, T, ser in _row_keys0(plain):
        if T:
            n = seen[(ser, T)]
            seen[(ser, T)] += 1
            if n:
                T = u"%s#%d" % (T, n)
        out.append((h, th, T, ser))
    return out


@contextlib.contextmanager
def keys_with(rule_on):
    u"""R3 の間だけ、便 XC0 の行の鍵の作り方を替える(同じ process の中だけ。file は変えない)。"""
    C0.row_keys = row_keys_occ if rule_on else _row_keys0
    try:
        yield
    finally:
        C0.row_keys = _row_keys0


def col_digits(prior_files):
    u"""前の年 → (h, th, td) → {(decimals, scale, format)}(空でない fact だけ)。"""
    out = {}
    for _name, plain, F, _H in prior_files:
        cells = C0.plain_cells(plain)
        keys = C0.row_keys(plain)
        cst = [c[1] for c in cells]
        for e in F:
            if e["kind"] != "nonFraction" or e["attrs"].get("xsi:nil") == "true":
                continue
            j = bisect.bisect_right(cst, e["start"]) - 1
            while j >= 0 and not (cells[j][1] <= e["start"] and e["end"] <= cells[j][2]):
                j -= 1
            if j < 0:
                continue
            k, _cs, _ce, td = cells[j]
            h, th, _T, _ser = keys[k]
            a = e["attrs"]
            out.setdefault((h, th, td), set()).add((a.get("decimals"), a.get("scale"), a.get("format")))
    return out


def fill_nil_only(tab, cold):
    u"""R4: 候補が全部空の fact の鍵に、同じ列の (decimals, scale, format) が 1 つなら、その桁を持つ空でない候補を足す。足した数を返す。"""
    added = 0
    for key, cands in tab.items():
        if cands and all(c[6] for c in cands):
            h, th, _T, td = key
            d = cold.get((h, th, td), set())
            if len(d) == 1:
                dec, scale, fmt = next(iter(d))
                for c in list(cands):
                    cands.add(c[:3] + (dec, scale, fmt, False))
                added += 1
    return added


def build_prior(prv, rules):
    with keys_with("R3" in rules):
        tab, sig = C0.prior_table(prv)
        col, sigc = C1.prior_cols(prv)
        valid = C1.prior_valid(prv, tab, col)
        cold = col_digits(prv)
    if "R4" in rules:
        fill_nil_only(tab, cold)
    return tab, sig, col, sigc, valid


def place3(plain, prior, res, rules):
    tab, sig, col, sigc, valid = prior
    with keys_with("R3" in rules):
        return C1.place2(plain, tab, sig, col, sigc, res, BASE_RULES, valid)


# ======================================================================================================
# 採点(便 XC0・XC1 と同じ数え方。今年の答えはここでだけ読む)
def score_pair(cur_zip, prior_zip, rules):
    cur = B.build_files(B.load_package(cur_zip))
    prv = B.build_files(B.load_package(prior_zip))
    prior = build_prior(prv, rules)
    base = build_prior(prv, ()) if rules else prior
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None)
    cur_H = next((H for _n, _p, _F, H in cur if H is not None), None)
    res = C0.shift_resources(prior_H) if prior_H else {}
    acc = od([("答えの数の fact", 0), ("一致", 0), ("黙って違う", 0), ("止めた", 0), ("置かない", 0), ("余計に置いた", 0), ("置いた", 0),
              ("違う欄", collections.Counter()), ("止めた理由", collections.Counter()),
              ("規則で替えて一致", 0), ("規則で替えて黙って違う", 0), ("規則で替えて余計", 0),
              ("使った文脈", 0), ("使った文脈の定義が元と同じ", 0)])
    used = set()
    for _name, plain, F, _H in cur:
        put, stop, _skip, _moved = place3(plain, prior, res, rules)
        bp, _bs, _bk, _bm = place3(plain, base, res, ())
        base_put = dict(((s, e), a) for s, e, a in bp)
        acc["置いた"] += len(put)
        P = dict(((s, e), a) for s, e, a in put)
        S = dict(((s, e), w) for s, e, w in stop)
        hit = set()
        for e in F:
            if e["kind"] != "nonFraction":
                continue
            acc["答えの数の fact"] += 1
            key = (e["start"], e["end"])
            if key in P:
                hit.add(key)
                d = C0.compare(e["attrs"], P[key])
                changed = base_put.get(key) != P[key]
                if d:
                    acc["黙って違う"] += 1
                    acc["違う欄"]["+".join(d)] += 1
                    acc["規則で替えて黙って違う"] += int(changed)
                else:
                    acc["一致"] += 1
                    acc["規則で替えて一致"] += int(changed)
            elif key in S:
                acc["止めた"] += 1
                acc["止めた理由"][S[key]] += 1
            else:
                acc["置かない"] += 1
        for k, a in P.items():
            if k not in hit:
                acc["余計に置いた"] += 1
                acc["規則で替えて余計"] += int(base_put.get(k) != a)
        used.update(a["contextRef"] for a in P.values())
    if cur_H:
        ans = dict((r["id"], r) for r in cur_H["resources"] if r["type"] == "context")
        for c in used:
            acc["使った文脈"] += 1
            if c in res and c in ans and C0.same_resource(res[c], ans[c]):
                acc["使った文脈の定義が元と同じ"] += 1
    for k in ("違う欄", "止めた理由"):
        acc[k] = od(sorted(acc[k].items()))
    return acc


if __name__ == "__main__":
    which, rules = sys.argv[1], tuple(r for r in sys.argv[2].split(",") if r and r != "none")
    dev, held = C1.split()
    out = []
    for n, p, pp in (dev if which == "dev" else held):
        out.append(od([("番号", n)] + list(score_pair(p, pp, rules).items())))
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    tot = collections.Counter()
    for r in out:
        for k in ("答えの数の fact", "一致", "黙って違う", "止めた", "置かない", "余計に置いた", "置いた", "規則で替えて一致", "規則で替えて黙って違う", "規則で替えて余計"):
            tot[k] += r[k]
    print(which, rules, dict(tot))
