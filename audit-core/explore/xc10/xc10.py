# -*- coding: utf-8 -*-
u"""便 XC10: 席の数の札(便 XC7・XC8)と席の節(便 XC9)を合わせて包みに入れ、道具 P に読ませる。

R1 節の範囲の確かめ: 席の節の範囲の見える字(数字と空白を除く)の始めの 40 字と、前の年の同じ節の始めの 40 字の似かたが 0.5 未満で、
   かつ終わりの 40 字どうしの似かたが 0.3 未満なら置かない(作りの 3 組で、答えと違う 2 を落とし、答えと同じを落とさなかった境)。
包みは便 XC8 の組み方(数の札は T1 と G1・G2 つき)に、便 XC5 の文の fact の置き方へ席の節を足した物。三つの包みを比べる:
base(席なし = 便 XC6)・num(数の札だけ = 便 XC8)・all(数の札と節)。席は回し直さない。
"""
import collections
import difflib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc10_xc9", os.path.join(os.path.dirname(HERE), "xc9", "xc9.py"))
X9 = importlib.util.module_from_spec(spec)
sys.modules["_xc10_xc9"] = X9
spec.loader.exec_module(X9)
X8, X7, C6, C5, C4, C3, C2, C1, C0, B, V = X9.X8, X9.X7, X9.C6, X9.C5, X9.C4, X9.C3, X9.C2, X9.C1, X9.C0, X9.B, X9.X7.V
od = collections.OrderedDict
SEATTX = {}
STAT = collections.Counter()
_pt6 = C5.place_texts6


def nv(html):
    t = X7.WS_RE.sub(u"", unicodedata.normalize("NFKC", X7.TAG_RE.sub(u" ", html)))
    t = re.sub(r"&#?\w+;", u"", t)
    return re.sub(r"[0-9]", u"", t)


def r1_ok(prev, cur):
    a = difflib.SequenceMatcher(None, prev[:40], cur[:40]).ratio()
    b = difflib.SequenceMatcher(None, prev[-40:], cur[-40:]).ratio()
    return not (a < 0.5 and b < 0.3)


def seat_texts(cur, prv, entries, tx_answers, use_r1=True):
    u"""席の節の答え → SEATTX(素の本文ごと)と数え。"""
    sc, tmap, bmap, pt = X9.build_screens(cur, prv, entries)
    added, c = X9.place_answers(cur, tmap, bmap, pt, tx_answers)
    ptb = {}
    for nm, plain, F, _H in prv:
        for f in F:
            if f["kind"] == "nonNumeric" and X9.is_tb(f["attrs"]):
                ptb[(C4.code_of(nm), f["attrs"].get("name"), f["attrs"].get("contextRef"))] = nv(plain[f["start"]:f["end"]])
    SEATTX.clear()
    for nm, plain, _F, _H in cur:
        for s, e, a in added.get(nm, []):
            if use_r1 and not r1_ok(ptb.get((C4.code_of(nm), a.get("name"), a.get("contextRef")), u""), nv(plain[s:e])):
                c[u"R1 で落とした節"] += 1
                continue
            SEATTX.setdefault(plain, []).append((s, e, dict(a)))
            c[u"包みに渡す節"] += 1
    return c


def place_texts6_w(plain, sigs, rels, labels):
    put, miss = _pt6(plain, sigs, rels, labels)
    got = set((a.get("name"), a.get("contextRef")) for _s, _e, a in put)
    for s, e, a in SEATTX.get(plain, []):
        if (a.get("name"), a.get("contextRef")) not in got:
            put.append((s, e, a))
            STAT[u"文の置き方に足した節"] += 1
    return put, miss


def score10(cur_zip, prior_zip, workdir):
    u"""便 XC5 の score_pair と同じ組み方で包みを組み、道具 P の数の fact と数でない fact を元と比べる。"""
    entries = B.load_package(cur_zip)
    cur = B.build_files(entries)
    prv = B.build_files(B.load_package(prior_zip))
    C3.xsd_of_cur[0] = C3.filer_xsd(entries)
    texts, stat, placed_text = C5.built_texts5(cur, prv, entries, C5.FIXES)
    acc = od(sorted(stat.items()))
    ours, orig = os.path.join(workdir, "ours.zip"), os.path.join(workdir, "orig.zip")
    B.write_package(B.package_with(entries, texts), ours)
    B.write_package(entries, orig)
    c_o, rows_o, _t = B.run_tool(C3.TOOL, orig, workdir, "orig")
    c_m, rows_m, _t2 = B.run_tool(C3.TOOL, ours, workdir, "ours")
    num_o, non_o = C3.facts_of(rows_o)
    num_m, non_m = C3.facts_of(rows_m)
    acc[u"道具が読んだ: 元の数の fact"] = sum(num_o.values())
    acc[u"道具が読んだ: 組んだ数の fact"] = sum(num_m.values())
    acc[u"数の fact: 元と同じ行"] = sum((num_o & num_m).values())
    acc[u"道具が読んだ: 元の数でない fact"] = sum(non_o.values())
    acc[u"道具が読んだ: 組んだ数でない fact"] = sum(non_m.values())
    acc[u"数でない fact: 元と同じ行"] = sum((non_o & non_m).values())
    vi = C3.COLS.index("Value")
    wsn = lambda cnt: collections.Counter(dict((tuple(re.sub(r"\s+", u"", str(x)) if i == vi else x for i, x in enumerate(r)), 0) for r in cnt)) + collections.Counter(
        [tuple(re.sub(r"\s+", u"", str(x)) if i == vi else x for i, x in enumerate(r)) for r in cnt.elements()])
    acc[u"数でない fact: 値の空白を除けば元と同じ行"] = sum((wsn(non_o) & wsn(non_m)).values())
    co, cm = c_o[u"符号ごとの行"], c_m[u"符号ごとの行"]
    acc[u"組んだ側だけで鳴った符号"] = od(sorted((k, v) for k, v in cm.items() if k not in co))
    acc[u"組んだ側だけで鳴った E の符号の数"] = sum(1 for k in acc[u"組んだ側だけで鳴った符号"] if V.is_e_code(k))
    acc[u"道具の類: 元・組んだ"] = [c_o[u"類"], c_m[u"類"]]
    return acc


def run_pair(n, p, pp, num_ans, tx_ans, names, mode, workdir):
    entries = B.load_package(p)
    cur = B.build_files(entries)
    prv = B.build_files(B.load_package(pp))
    C6.OWN[0] = C5.xsd_info(entries)[1]
    C3.xsd_of_cur[0] = C3.filer_xsd(entries)
    ct = seat_texts(cur, prv, entries, tx_ans) if mode == "all" else collections.Counter()
    if mode != "all":
        SEATTX.clear()
    C2.place3 = lambda plain, prior, res, rules: C6.place3_g(plain, prior, res, rules)
    cn, _marks = X8.seat_tags(cur, prv, entries, num_ans, names)
    if mode == "base":
        X8.SEATS.clear()
    STAT.clear()
    C6._place3 = X8.place_with_seats
    C5.place_texts6 = place_texts6_w
    try:
        acc = score10(p, pp, workdir)
    finally:
        C6._place3 = X8._orig
        C2.place3 = X8._orig
        C5.place_texts6 = _pt6
    for k, v in sorted(list(cn.items()) + list(ct.items())):
        acc[k] = v
    acc[u"文の置き方に足した節"] = STAT[u"文の置き方に足した節"]
    return acc


if __name__ == "__main__":
    which, base7, base9, mode, outp = sys.argv[1:6]
    dev, held = C1.split()
    nums = {"dev": [1, 2, 3], "held": [25, 26, 27, 28]}[which]
    head = {"dev": "d", "held": "h"}[which]
    names = X8.std_names()
    rows = []
    for n, p, pp in [x for x in dev + held if x[0] in nums]:
        wd = tempfile.mkdtemp(prefix="xc10_")
        try:
            a = run_pair(n, p, pp, X8.load_answers(base7, head, n), X8.load_answers(base9, head, n), names, mode, wd)
        finally:
            shutil.rmtree(wd, ignore_errors=True)
        rows.append(od([(u"番号", n)] + list(a.items())))
        print(n, json.dumps(od((k, v) for k, v in a.items() if not isinstance(v, (dict, list))), ensure_ascii=False), flush=True)
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
