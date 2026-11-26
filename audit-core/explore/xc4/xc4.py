# -*- coding: utf-8 -*-
u"""便 XC4: 今年の答えを見ずに、文の fact(ix:nonNumeric)を前の年から置き、便 XC3 の包みに足して道具 P に読ませる。

文の fact の置き方(今年の答えを読まない):
- file は名の頭の番号(例 0101010)で前の年と今年を対にする。
- 前の年の文の fact ごとに、始まりのすぐ後の生の字 K 字(タグも含む)を「始まりの印」、終わりのすぐ後の生の字 K 字を「終わりの印」にする。
- 今年の素の本文で、始まりの印がちょうど 1 か所に在ればそこを始まりにする(2 か所以上なら、始まりの前の K 字も合う所が 1 つならそこ)。
  終わりは、始まりより後で最初に終わりの印が在る所。終わりの印が空(file の終わり)なら、終わりの前の K 字が始まりより後で最後に在る所の後。
  印は 120 字(作りの組で短い印を試し、置き場違いが増えたのでやめた)。軸のメンバーの在る文脈の文の fact は置かない。
- 決まらなければ置かない。属性(name・contextRef・escape・format・空の fact)は前の年の物を写す。
- 入れ子は位置で決め直す(親は位置で包む文の fact)。部分だけ重なる fact は置かない。数の fact(便 XC2 の置き方)も包む文の fact を親にする。
今年の答えは採点でだけ読む。
"""
import collections
import importlib.util
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc4_xc3", os.path.join(os.path.dirname(HERE), "xc3", "xc3.py"))
C3 = importlib.util.module_from_spec(spec)
sys.modules["_xc4_xc3"] = C3
spec.loader.exec_module(C3)
C2, C1, C0, B, V = C3.C2, C3.C1, C3.C0, C3.B, C3.V
od = collections.OrderedDict
K = 120
USE_REL = True
TEXT_ATTRS = ("name", "contextRef", "escape", "format", "xsi:nil")


def code_of(name):
    return name.split("/")[-1].split("_")[0]


def finds(s, sub):
    out, i = [], s.find(sub)
    while i >= 0 and sub:
        out.append(i)
        i = s.find(sub, i + 1)
    return out


def text_sigs_rel(prior_files):
    u"""text_sigs と同じ並びに、終わりの結び先を足す: 前の年で終わりが別の文の fact の始まりと同じならその番号(("s", 番号))、
    親の文の fact の終わりと同じなら(("p", 番号))、どちらでもなければ None。番号は同じ file の中の text_sigs の並びの番号。"""
    out = collections.defaultdict(list)
    for name, plain, F, _H in prior_files:
        tf = [(i, e) for i, e in enumerate(F) if e["kind"] == "nonNumeric" and not e["self"]]
        idx = dict((i, n) for n, (i, _e) in enumerate(tf))
        starts = {}
        for n, (_i, e) in enumerate(tf):
            starts.setdefault(e["start"], n)
        for n, (i, e) in enumerate(tf):
            rel = None
            j = starts.get(e["end"])
            if j is not None and j != n and e["end"] > e["start"]:
                rel = ("s", j)
            elif e["parent"] in idx and F[e["parent"]]["end"] == e["end"]:
                rel = ("p", idx[e["parent"]])
            out[code_of(name)].append(rel)
    return out


def text_sigs(prior_files):
    u"""前の年 → {file の頭の番号: [(始まりの印, 始まりの前の K 字, 終わりの印, 終わりの前の K 字, 属性)]}(文の fact だけ・始まりの順)。"""
    out = collections.defaultdict(list)
    for name, plain, F, _H in prior_files:
        for e in F:
            if e["kind"] != "nonNumeric" or e["self"]:
                continue
            s, t = e["start"], e["end"]
            attrs = od((k, e["attrs"][k]) for k in TEXT_ATTRS if k in e["attrs"])
            out[code_of(name)].append((plain[s:s + K], plain[max(0, s - K):s], plain[t:t + K], plain[max(0, t - K):t], attrs))
    return out


STEPS = (120,)                       # 作りの組で、短い印は置き場違いを増やした(封 §3)


def find_start(plain, a, before):
    u"""始まりの印を長い順に短くして探し、1 か所に決まった所(2 か所以上なら前の字も合う所が 1 つ)。決まらなければ -1。"""
    for k in STEPS:
        cand = finds(plain, a[:k])
        if len(cand) > 1:
            cand = [c for c in cand if plain[max(0, c - k):c] == before[-k:]]
        if len(cand) == 1:
            return cand[0]
    return -1


def find_end(plain, s, endm, endb):
    u"""終わり: 始まりより後で最初に終わりの印が在る所(長い順に短くして探す)。印が空なら、終わりの前の字が最後に在る所の後。"""
    if not endm:
        q = plain.rfind(endb)
        return q + len(endb) if q >= s else -1
    for k in STEPS:
        t = plain.find(endm[:k], s + 1)
        if t >= 0:
            return t
    return -1


def place_texts(plain, sigs, rels=None):
    u"""今年の素の本文と、その file の前の年の印 → (置いた文の fact [(start, end, 属性)], 置かなかった数)。
    ``rels`` が在れば、終わりは結び先(次の文の fact の始まり・親の終わり)を先に使う。"""
    starts = [find_start(plain, a, before) for a, before, _m, _b, _at in sigs]
    ends = [None] * len(sigs)

    def end_of(n, depth=0):
        if ends[n] is not None:
            return ends[n]
        s = starts[n]
        t = -1
        rel = rels[n] if rels else None
        if s >= 0 and rel and depth < 50:
            if rel[0] == "s" and starts[rel[1]] > s:
                t = starts[rel[1]]
            elif rel[0] == "p" and starts[rel[1]] >= 0 and starts[rel[1]] <= s:
                t = end_of(rel[1], depth + 1)
        if s >= 0 and t < s:
            t = find_end(plain, s, sigs[n][2], sigs[n][3])
        ends[n] = t
        return t
    put, miss = [], 0
    for n, (_a, _b, _m, _eb, attrs) in enumerate(sigs):
        s = starts[n]
        t = end_of(n) if s >= 0 else -1
        if s < 0 or t < s:
            miss += 1
            continue
        if "_" in attrs.get("contextRef", ""):           # 軸のメンバーの在る文脈(役員の行など)は置かない(封 §3)
            miss += 1
            continue
        put.append((s, t, attrs))
    return put, miss


def nest(nums, texts):
    u"""数の fact [(s, e, 属性)] と文の fact [(s, e, 属性)] → 表 F(親を位置で決める)。(表 F, 捨てた文の fact の数)。
    並べ方は始まりの昇順・終わりの降順・同じ所では文の fact が先。開いている文の fact が終わる前に終わらない物(部分だけ重なる物)は捨てる。
    同じ位置・同じ名と文脈の文の fact の 2 つ目も捨てる。"""
    items = [(s, e, "nonNumeric", a) for s, e, a in texts] + [(s, e, "nonFraction", a) for s, e, a in nums]
    items.sort(key=lambda q: (q[0], -q[1], 0 if q[2] == "nonNumeric" else 1))
    F, stack, dropped, seen = [], [], 0, set()
    for s, e, kind, a in items:
        if kind == "nonNumeric":
            key = (s, e, a.get("name"), a.get("contextRef"))
            if key in seen:
                dropped += 1
                continue
        while stack and F[stack[-1]]["end"] <= s:
            stack.pop()
        if stack and F[stack[-1]]["end"] < e:
            dropped += int(kind == "nonNumeric")
            if kind == "nonFraction":
                raise ValueError(u"数の fact が文の fact と部分だけ重なる")
            continue
        F.append(od([("kind", kind), ("self", False), ("start", s), ("end", e), ("parent", stack[-1] if stack else -1),
                     ("attrs", od((k, v) for k, v in a.items() if v is not None))]))
        if kind == "nonNumeric":
            seen.add(key)
            if s < e:
                stack.append(len(F) - 1)
    return F, dropped


def built_texts(cur, prv, with_text=True):
    prior = C2.build_prior(prv, C3.RULES)
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None)
    res = C0.shift_resources(prior_H)
    sigs = text_sigs(prv) if with_text else {}
    rels = text_sigs_rel(prv) if with_text else {}
    texts, stat = {}, collections.Counter()
    placed_text = {}
    for idx, (name, plain, _F, _H) in enumerate(cur):
        nums, _stop, _skip, _m = C2.place3(plain, prior, res, C3.RULES)
        tx, miss = place_texts(plain, sigs.get(code_of(name), []), rels.get(code_of(name)) if USE_REL else None)
        stat["文の fact: 前の年の数"] += len(sigs.get(code_of(name), []))
        stat["文の fact: 置かなかった"] += miss
        F2, dropped = nest(nums, tx)
        stat["文の fact: 重なりで捨てた"] += dropped
        stat["文の fact: 置いた"] += sum(1 for f in F2 if f["kind"] == "nonNumeric")
        stat["数の fact: 置いた"] += sum(1 for f in F2 if f["kind"] == "nonFraction")
        placed_text[name] = [(f["start"], f["end"], dict(f["attrs"])) for f in F2 if f["kind"] == "nonNumeric"]
        H2 = None
        if idx == 0:
            m = C3.BODY_RE.search(plain)
            b = m.end()
            plain = plain[:b] + C3.WRAP_OPEN + C3.WRAP_CLOSE + plain[b:]
            sh = len(C3.WRAP_OPEN) + len(C3.WRAP_CLOSE)
            for f in F2:
                if f["start"] >= b:
                    f["start"] += sh
                    f["end"] += sh
            H2 = C3.header_from_prior(prior_H, C3.xsd_of_cur[0])
            H2["pos"] = b + len(C3.WRAP_OPEN)
            H2["before"] = sum(1 for f in F2 if f["start"] < b)
        texts[name] = B.build_text(plain, F2, H2)
    return texts, stat, placed_text


def score_text_positions(cur, placed_text):
    u"""文の fact の置き場と属性を、今年の答えの表 F と比べる(採点だけ)。"""
    acc = collections.Counter()
    for name, _plain, F, _H in cur:
        P = {}
        for s, e, a in placed_text.get(name, []):
            P.setdefault((s, e), []).append(a)
        hit = collections.Counter()
        for f in F:
            if f["kind"] != "nonNumeric":
                continue
            acc["答えの文の fact"] += 1
            want = dict((k, f["attrs"][k]) for k in TEXT_ATTRS if k in f["attrs"])
            got = P.get((f["start"], f["end"]), [])
            if want in got:
                acc["一致"] += 1
                hit[(f["start"], f["end"], json.dumps(want, sort_keys=True))] += 1
            elif got:
                acc["同じ置き場で属性が違う"] += 1
            else:
                acc["同じ置き場に置いていない"] += 1
        n_put = sum(len(v) for v in P.values())
        acc["置いた文の fact"] += n_put
    return acc


def score_pair(cur_zip, prior_zip, workdir, run_tool=True):
    entries = B.load_package(cur_zip)
    cur = B.build_files(entries)
    prv = B.build_files(B.load_package(prior_zip))
    C3.xsd_of_cur[0] = C3.filer_xsd(entries)
    texts, stat, placed_text = built_texts(cur, prv)
    acc = od(sorted(stat.items()))
    acc.update(("位置: " + k, v) for k, v in sorted(score_text_positions(cur, placed_text).items()))
    if not run_tool:
        return acc
    ours = os.path.join(workdir, "ours.zip")
    orig = os.path.join(workdir, "orig.zip")
    B.write_package(B.package_with(entries, texts), ours)
    B.write_package(entries, orig)
    c_o, rows_o, _t = B.run_tool(C3.TOOL, orig, workdir, "orig")
    c_m, rows_m, _t2 = B.run_tool(C3.TOOL, ours, workdir, "ours")
    num_o, non_o = C3.facts_of(rows_o)
    num_m, non_m = C3.facts_of(rows_m)
    drop = lambda c: collections.Counter(dict((r[:-1], n) for r, n in c.items()))
    acc["道具が読んだ: 元の数の fact"] = sum(num_o.values())
    acc["道具が読んだ: 組んだ数の fact"] = sum(num_m.values())
    acc["数の fact: 元と同じ行"] = sum((num_o & num_m).values())
    acc["道具が読んだ: 元の数でない fact"] = sum(non_o.values())
    acc["道具が読んだ: 組んだ数でない fact"] = sum(non_m.values())
    acc["数でない fact: 元と同じ行"] = sum((non_o & non_m).values())
    acc["数でない fact: 最後の欄を除けば元と同じ行"] = sum((drop(non_o) & drop(non_m)).values())
    co, cm = c_o[u"符号ごとの行"], c_m[u"符号ごとの行"]
    acc["組んだ側だけで鳴った符号"] = od(sorted((k, v) for k, v in cm.items() if k not in co))
    acc["組んだ側だけで鳴った E の符号の数"] = sum(1 for k in acc["組んだ側だけで鳴った符号"] if V.is_e_code(k))
    acc["道具の類: 元・組んだ"] = [c_o[u"類"], c_m[u"類"]]
    return acc


if __name__ == "__main__":
    which, tool = sys.argv[1], sys.argv[2] == "tool"
    dev, held = C1.split()
    group = {"train": [x for x in dev if x[0] <= C1.SEEN_MAX_NO], "dev": dev, "held": held}[which]
    out = []
    for n, p, pp in group:
        wd = tempfile.mkdtemp(prefix="xc4_")
        try:
            a = score_pair(p, pp, wd, tool)
        finally:
            shutil.rmtree(wd, ignore_errors=True)
        out.append(od([("番号", n)] + list(a.items())))
        print(n, json.dumps(od((k, v) for k, v in a.items() if not isinstance(v, (dict, list))), ensure_ascii=False), flush=True)
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
