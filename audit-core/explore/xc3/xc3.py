# -*- coding: utf-8 -*-
u"""便 XC3: 今年の答えを見ずに組んだ包みを、公開の検査の道具(道具 P)に読ませ、元の包みと同じ fact が読めるかを見る。

組む物(今年の答えを読まない):
- 数の fact: 便 XC2 の置き方(R1〜R4)。
- 頭の部: 前の年の頭の部から作る。文脈の期は R5(今年の前の期は前の年の 1 つ新しい期の期をそのまま使い、無ければ 1 年ずらす)。隠しの fact(DEI など)は前の年の物を写し、値が日付(YYYY-MM-DD)なら 1 年ずらす。
持ち込み(今年の包みのまま。作らない): 提出者別タクソノミの file・schemaRef の file の名・文の fact(ix:nonNumeric)・脚注・画像・素の本文。
今年の答えは採点(道具が元の包みから読む fact)でだけ読む。
"""
import collections
import copy
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc3_xc2", os.path.join(os.path.dirname(HERE), "xc2", "xc2.py"))
C2 = importlib.util.module_from_spec(spec)
sys.modules["_xc3_xc2"] = C2
spec.loader.exec_module(C2)
C1, C0, B = C2.C1, C2.C0, C2.B
V = B.V
od = collections.OrderedDict
RULES = ("R3", "R4")
TOOL = os.path.expanduser("~/.cache/audit-core/tools/arelle-p-2.47.5")
DATE_ONLY_RE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")
BODY_RE = re.compile(r"<body\b[^>]*>", re.I)
WRAP_OPEN, WRAP_CLOSE = u'<div style="display:none">', u"</div>"
COLS = B.FACT_COLS.split()


class Stop(Exception):
    pass


def shift_text(t):
    m = DATE_ONLY_RE.match(t or u"")
    if not m:
        return t
    return C0.shift_date(u"%s-%s-%s" % m.groups())


def contexts_r5(prior_H):
    u"""R5 期の付け替え: 今年の Prior#Year の文脈は、前の年の 1 つ新しい期(Prior(#-1)Year か CurrentYear)の文脈の期をそのまま使う。
    同じ id の残りの部品の文脈が前の年に無ければ、1 年ずらす(便 XC0)。"""
    sh = C0.shift_resources(prior_H)
    byid = dict((r["id"], r) for r in prior_H["resources"] if r["type"] == "context")
    for i, r in list(sh.items()):
        if r["type"] != "context":
            continue
        pe = C1.period_of(i)
        if pe and pe[0] >= 1:
            src = C1.with_period(i, pe[0] - 1, pe[1])
            if src in byid:
                r["period"] = [list(x) for x in byid[src]["period"]]
    return sh


def header_from_prior(prior_H, xsd_name):
    u"""前の年の表 H → 今年の表 H(``pos``・``before`` は呼ぶ側が足す)。"""
    H = od([("sections", list(prior_H["sections"])), ("hidden", []), ("references", []), ("resources", [])])
    for h in prior_H["hidden"]:
        h2 = copy.deepcopy(h)
        h2["text"] = shift_text(h["text"])
        H["hidden"].append(h2)
    for r in prior_H["references"]:
        r2 = copy.deepcopy(r)
        if r2["tag"] == "link:schemaRef":
            r2["attrs"]["xlink:href"] = xsd_name
        H["references"].append(r2)
    res = contexts_r5(prior_H)
    for r in prior_H["resources"]:
        if r["type"] == "ref":
            H["resources"].append(copy.deepcopy(r))
        else:
            r2 = copy.deepcopy(r)
            if r["type"] == "context":
                r2["period"] = [tuple(x) for x in res[r["id"]]["period"]]
            H["resources"].append(r2)
    return H


def built_texts(cur, prv):
    u"""今年の [(名, plain, F, H)](plain だけを使う)と前の年 → ({名: 組んだ字}, 置いた数の fact の数)。"""
    prior = C2.build_prior(prv, RULES)
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None)
    if prior_H is None:
        raise Stop(u"前の年に頭の部が無い")
    res = C0.shift_resources(prior_H)
    texts, nput = {}, 0
    for idx, (name, plain, _F, _H) in enumerate(cur):
        put, _stop, _skip, _m = C2.place3(plain, prior, res, RULES)
        nput += len(put)
        F2 = [od([("kind", "nonFraction"), ("self", False), ("start", s), ("end", e), ("parent", -1),
                  ("attrs", od((k, v) for k, v in a.items() if v is not None))]) for s, e, a in sorted(put, key=lambda q: (q[0], q[1]))]
        H2 = None
        if idx == 0:
            m = BODY_RE.search(plain)
            if not m:
                raise Stop(u"最初の file に body が無い")
            b = m.end()
            plain = plain[:b] + WRAP_OPEN + WRAP_CLOSE + plain[b:]
            sh = len(WRAP_OPEN) + len(WRAP_CLOSE)
            for f in F2:
                if f["start"] >= b:
                    f["start"] += sh
                    f["end"] += sh
            H2 = header_from_prior(prior_H, xsd_of_cur[0])
            H2["pos"] = b + len(WRAP_OPEN)
            H2["before"] = sum(1 for f in F2 if f["start"] < b)
        texts[name] = B.build_text(plain, F2, H2)
    return texts, nput


xsd_of_cur = [None]


def filer_xsd(entries):
    names = [i.filename for i, _d in entries if i.filename.startswith(B.PUBLICDOC) and i.filename.endswith(".xsd")]
    if len(names) != 1:
        raise Stop(u"今年の包みの提出者の xsd が 1 つでない")
    return names[0].split("/")[-1]


def facts_of(rows):
    u"""道具の fact の行 → (数の fact の Counter, 数でない fact の Counter)。数の fact は unitRef の在る行。"""
    iu = COLS.index("unitRef")
    num, non = collections.Counter(), collections.Counter()
    for r in rows:
        if len(r) <= iu:                      # 欄の足りない行(道具の出力の形)は数でない側に入れる
            non[r] += 1
            continue
        (num if r[iu] else non)[r] += 1
    return num, non


def score_pair(cur_zip, prior_zip, workdir):
    entries = B.load_package(cur_zip)
    cur = B.build_files(entries)
    prv = B.build_files(B.load_package(prior_zip))
    xsd_of_cur[0] = filer_xsd(entries)
    texts, nput = built_texts(cur, prv)
    ours = os.path.join(workdir, "ours.zip")
    orig = os.path.join(workdir, "orig.zip")
    B.write_package(B.package_with(entries, texts), ours)
    B.write_package(entries, orig)
    c_o, rows_o, _t = B.run_tool(TOOL, orig, workdir, "orig")
    c_m, rows_m, _t2 = B.run_tool(TOOL, ours, workdir, "ours")
    num_o, non_o = facts_of(rows_o)
    num_m, non_m = facts_of(rows_m)
    acc = od()
    acc["置いた数の fact"] = nput
    acc["道具が読んだ: 元の数の fact"] = sum(num_o.values())
    acc["道具が読んだ: 組んだ数の fact"] = sum(num_m.values())
    acc["数の fact: 元と同じ行"] = sum((num_o & num_m).values())
    acc["数の fact: 組んだ側だけの行"] = sum((num_m - num_o).values())
    acc["数の fact: 元の側だけの行"] = sum((num_o - num_m).values())
    acc["道具が読んだ: 元の数でない fact"] = sum(non_o.values())
    acc["道具が読んだ: 組んだ数でない fact"] = sum(non_m.values())
    acc["数でない fact: 元と同じ行"] = sum((non_o & non_m).values())
    drop = lambda c: collections.Counter(dict((r[:-1], n) for r, n in c.items()))
    acc["数でない fact: 最後の欄(提出日の期)を除けば元と同じ行"] = sum((drop(non_o) & drop(non_m)).values())
    co, cm = c_o[u"符号ごとの行"], c_m[u"符号ごとの行"]
    acc["組んだ側だけで鳴った符号"] = od(sorted((k, v) for k, v in cm.items() if k not in co))
    acc["元の側だけで鳴った符号"] = od(sorted((k, v) for k, v in co.items() if k not in cm))
    acc["組んだ側だけで鳴った E の符号の数"] = sum(1 for k in acc["組んだ側だけで鳴った符号"] if V.is_e_code(k))
    acc["道具の類: 元・組んだ"] = [c_o[u"類"], c_m[u"類"]]
    acc["道具の数え: 元"] = c_o
    acc["道具の数え: 組んだ"] = c_m
    return acc


if __name__ == "__main__":
    which = sys.argv[1]
    dev, held = C1.split()
    group = {"train": [x for x in dev if x[0] <= C1.SEEN_MAX_NO], "dev": dev, "held": held}[which]
    out = []
    for n, p, pp in group:
        wd = tempfile.mkdtemp(prefix="xc3_")
        try:
            a = score_pair(p, pp, wd)
        finally:
            shutil.rmtree(wd, ignore_errors=True)
        out.append(od([("番号", n)] + list(a.items())))
        print(n, json.dumps(od((k, v) for k, v in a.items() if not k.startswith("道具の数え")), ensure_ascii=False), flush=True)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
