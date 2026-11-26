# -*- coding: utf-8 -*-
u"""便 XC6: 便 XC5 の後に残る誤りの符号のうち、道具の文から原因の読めた 2 つを、今年の答えを見ずに直す。

G1 無いメンバー: 数の fact の文脈(1 年ずらした前の年の定義)の軸のメンバーのうち、提出者の独自のメンバー(前置きが `_cor` で終わらない物)が、
   今年の提出者の xsd(持ち込み)に定義の無い物なら、その数の fact は置かない(辞めた役員のメンバーなど。xbrldie: の符号の原因)。
G2 食い違う重なり: 同じ file の中で、同じ要素・文脈・単位の数の fact が 2 つ以上在り、升の見える字が違えば、その全部を置かない(EDINET.EC8024E の原因)。
土台は便 XC5(F1〜F7)。便 XC0〜XC5 の file は読み込んで関数を呼ぶだけ。今年の答えは採点でだけ読む。
"""
import collections
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc6_xc5", os.path.join(os.path.dirname(HERE), "xc5", "xc5.py"))
C5 = importlib.util.module_from_spec(spec)
sys.modules["_xc6_xc5"] = C5
spec.loader.exec_module(C5)
C4, C3, C2, C1, C0, B, V = C5.C4, C5.C3, C5.C2, C5.C1, C5.C0, C5.B, C5.V
od = collections.OrderedDict
FIXES5 = C5.FIXES
TAG_RE = re.compile(r"<[^>]*>")
STAT = collections.Counter()
OWN = [set()]
_place3 = C2.place3


def own_member_missing(ctx_def, own):
    for _dim, mem in ctx_def.get("members") or []:
        pre, _c, local = (mem or u"").partition(":")
        if pre and not pre.endswith("_cor") and local not in own:
            return True
    return False


def place3_g(plain, prior, res, rules, fixes=("G1", "G2")):
    u"""便 XC2 の ``place3`` を呼び、G1・G2 で置く数の fact を減らす(止めたに回す)。"""
    put, stop, skip, moved = _place3(plain, prior, res, rules)
    if "G1" in fixes:
        keep = []
        for s, e, a in put:
            d = res.get(a.get("contextRef"))
            if d is not None and own_member_missing(d, OWN[0]):
                stop.append((s, e, u"G1 無いメンバー"))
                STAT["G1 で置かなかった数の fact"] += 1
            else:
                keep.append((s, e, a))
        put = keep
    if "G2" in fixes:
        groups = collections.defaultdict(list)
        for s, e, a in put:
            groups[(a.get("name"), a.get("contextRef"), a.get("unitRef"))].append((s, e, a))
        keep = []
        for k, items in groups.items():
            vals = set(TAG_RE.sub(u"", plain[s:e]).strip() for s, e, _a in items)
            if len(items) > 1 and len(vals) > 1:
                for s, e, _a in items:
                    stop.append((s, e, u"G2 食い違う重なり"))
                STAT["G2 で置かなかった数の fact"] += len(items)
            else:
                keep.extend(items)
        put = sorted(keep, key=lambda q: (q[0], q[1]))
    return put, stop, skip, moved


def score_pair(cur_zip, prior_zip, workdir, fixes):
    entries = B.load_package(cur_zip)
    OWN[0] = C5.xsd_info(entries)[1]
    STAT.clear()
    C2.place3 = (lambda plain, prior, res, rules: place3_g(plain, prior, res, rules, fixes)) if fixes else _place3
    try:
        acc = C5.score_pair(cur_zip, prior_zip, workdir, FIXES5)
    finally:
        C2.place3 = _place3
    for k in ("G1 で置かなかった数の fact", "G2 で置かなかった数の fact"):
        acc[k] = STAT[k]
    return acc


if __name__ == "__main__":
    which, fixes = sys.argv[1], tuple(f for f in sys.argv[2].split(",") if f and f != "none")
    dev, held = C1.split()
    group = {"train": [x for x in dev if x[0] <= C1.SEEN_MAX_NO], "dev": dev, "held": held}[which]
    if len(sys.argv) > 4:
        only = set(int(x) for x in sys.argv[4].split(","))
        group = [x for x in group if x[0] in only]
    out = []
    for n, p, pp in group:
        wd = tempfile.mkdtemp(prefix="xc6_")
        try:
            a = score_pair(p, pp, wd, fixes)
        finally:
            shutil.rmtree(wd, ignore_errors=True)
        out.append(od([("番号", n)] + list(a.items())))
        print(n, json.dumps(od((k, v) for k, v in a.items() if not isinstance(v, (dict, list))), ensure_ascii=False), flush=True)
    if len(sys.argv) > 3 and sys.argv[3] != "-":
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
