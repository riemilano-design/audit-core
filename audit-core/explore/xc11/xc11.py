# -*- coding: utf-8 -*-
u"""便 XC11: 規則で置けなかった表の中の文の fact(役員ごと・大株主の行ごとなど、軸のメンバーの付いた文脈)を、AI の席に置かせる。

画面(今年の答えを読まない): 今年の表(規則で置いた文の fact は札を見せ、置いていない字の在る升に `★M番号`)と、行の字と表の前の字で組んだ前の年の表
(軸のメンバーの付いた文の fact の札 = 要素・文脈を升ごとに見せる)。席は印ごとに要素と文脈か null を答える。
機械: 文脈は 1 年ずらした前の年の定義に在る物だけ・要素はタクソノミ(便 XC8 の T1)か今年の提出者の xsd に在る物だけ。升の中の置き場は、
前の年の同じ要素・文脈(無ければ同じ要素)の fact が升の中で持っていたタグの並び(前と後)を今年の升に当てて決める(無ければ升の中の字の範囲)。
置いた fact と交わる物は置かない。属性は前の年の同じ要素の fact の属性(文脈だけ席の答え)。会社と人の名の入る画面と答えは scratchpad に置く。
"""
import collections
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc11_xc9", os.path.join(os.path.dirname(HERE), "xc9", "xc9.py"))
X9 = importlib.util.module_from_spec(spec)
sys.modules["_xc11_xc9"] = X9
spec.loader.exec_module(X9)
X8, X7, C6, C5, C4, C3, C2, C1, C0, B = X9.X8, X9.X7, X9.C6, X9.C5, X9.C4, X9.C3, X9.C2, X9.C1, X9.C0, X9.B
od = collections.OrderedDict
TAGN = re.compile(r"<(/?)(\w+)[^>]*>")
LT = re.compile(r"^(\s|<[^>]*>)*")
TT = re.compile(r"(\s|<[^>]*>)*$")
MEM_RE = X9.MEM_RE
CHUNK = 60000
FIX = {"S1"}                         # S1 升の中の fact の外の字を前の年に合わせて除く
NUM_RE = re.compile(r"[0-9,.\s△▲\-−―－%()（）円株千百万]*")


def toks_of(plain, a, b):
    u"""範囲の中のタグと字の並び → [(印, start, end)]。字は 'T'(空白だけの字は除く)。"""
    out, pos = [], a
    for mm in TAGN.finditer(plain, a, b):
        if plain[pos:mm.start()].strip():
            out.append(("T", pos, mm.start()))
        out.append((mm.group(1) + mm.group(2).lower(), mm.start(), mm.end()))
        pos = mm.end()
    if plain[pos:b].strip():
        out.append(("T", pos, b))
    return out


def shape(x):
    return tuple(t for t, _s, _e in toks_of(x, 0, len(x)))


def cell_of(cells, s, e):
    h = [x for x in cells if x[0] <= s and e <= x[1]]
    return min(h, key=lambda x: x[1] - x[0]) if h else None


def recon(plain, cs, ce, pre, post):
    u"""升の中の並びの前から pre、後ろから post を除いた所(字の塊も並びの 1 つ)。合わなければ None。"""
    tk = toks_of(plain, cs, ce)
    if len(tk) < len(pre) + len(post) or tuple(t for t, _a, _b in tk[:len(pre)]) != pre:
        return None
    if post and tuple(t for t, _a, _b in tk[len(tk) - len(post):]) != post:
        return None
    s = tk[len(pre) - 1][2] if pre else cs
    e = tk[len(tk) - len(post)][1] if post else ce
    return (s, e) if s < e else None


def recon_old(plain, cs, ce, pre, post):
    u"""升 (cs, ce) の中で、前からタグの並び pre・後ろから post を除いた所を置き場にする。合わなければ None。"""
    toks = list(TAGN.finditer(plain, cs, ce))
    pos, seq, i = cs, [], 0
    while tuple(seq) != pre:
        if i >= len(toks) or plain[pos:toks[i].start()].strip():
            return None
        seq.append(toks[i].group(1) + toks[i].group(2).lower())
        pos = toks[i].end()
        i += 1
    s = pos
    pos, seq, j = ce, [], len(toks) - 1
    while tuple(reversed(seq)) != post:
        if j < 0 or plain[toks[j].end():pos].strip():
            return None
        seq.append(toks[j].group(1) + toks[j].group(2).lower())
        pos = toks[j].start()
        j -= 1
    return (s, pos) if s < pos else None


def vtext(html):
    return X7.WS_RE.sub(u"", X7.TAG_RE.sub(u"", html)).replace(u"&#160;", u"")


def strip_text(plain, s, e, pre, post):
    u"""S1: 前の年の fact の升の中で fact の外に在った見える字(例 生年月日の後の字)を、今年の置き場の端からも除く。"""
    if post:
        seg = plain[s:e]
        k = seg.rfind(post)
        if k > 0 and not X7.WS_RE.sub(u"", X7.TAG_RE.sub(u"", seg[k + len(post):])):
            e = s + k
            while e > s and plain[e - 1].isspace():
                e -= 1
    if pre:
        seg = plain[s:e]
        k = seg.find(pre)
        if k >= 0 and not X7.WS_RE.sub(u"", X7.TAG_RE.sub(u"", seg[:k])):
            s = s + k + len(pre)
            while s < e and plain[s].isspace():
                s += 1
    return (s, e) if s < e else None


def innermost(plain, cs, ce):
    a = cs + LT.match(plain[cs:ce]).end()
    b = ce - len(TT.search(plain[cs:ce]).group(0))
    return (a, b) if a < b else None


def prior_tables(prv):
    u"""前の年の表のうち、軸のメンバーの付いた文の fact の在る物 → [(file の型, 表, 素の本文, 升, {升: 属性}, 行の字, 見出し)] と、
    前の年の fact の形 {(要素, 文脈): (前のタグの並び, 後のタグの並び, 属性)}・{要素: 属性}。"""
    out, shp, by_name = [], {}, {}
    for name, plain, F, _H in prv:
        tabs = X7.tables_of(plain)
        allc = [x for cl in tabs.values() for x in cl.values()]
        nn = [f for f in F if f["kind"] == "nonNumeric" and MEM_RE.search(f["attrs"].get("contextRef") or u"")]
        for f in nn:
            c = cell_of(allc, f["start"], f["end"])
            if c:
                shp[(f["attrs"].get("name"), f["attrs"].get("contextRef"))] = (shape(plain[c[0]:f["start"]]), shape(plain[f["end"]:c[1]]), dict(f["attrs"]),
                                                                              vtext(plain[c[0]:f["start"]]), vtext(plain[f["end"]:c[1]]))
                by_name.setdefault(f["attrs"].get("name"), dict(f["attrs"]))
        for t, cells in tabs.items():
            tag = {}
            for (r, cc), (cs, ce) in cells.items():
                for f in nn:
                    if cs <= f["start"] and f["end"] <= ce:
                        tag[(cs, ce)] = f["attrs"]
                        break
            if tag:
                out.append((C4.code_of(name), t, plain, cells, tag, X7.row_labels(cells, plain), X7.heading(plain, cells)))
    return out, shp, by_name


def build_screens(cur, prv, entries):
    u"""1 組 → (画面 [(字, [M])], 印 {M: (file の名, cs, ce)}, 前の年の形, 置いた fact {file の名: [(s, e)]}, 文脈の表)。"""
    pt = X9.placed_texts(cur, prv, entries)
    ptabs, shp, by_name = prior_tables(prv)
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None)
    res = C0.shift_resources(prior_H)
    prior = C2.build_prior(prv, C3.RULES)
    parts, marks, n_mark = [], od(), 0
    USE = collections.Counter()
    occupied = {}
    for fi, (name, plain, _F, _H) in enumerate(cur):
        put, _st, _sk, _mv = C6.place3_g(plain, prior, res, C3.RULES)
        occ = [(s, e) for s, e, _a in put] + [(s, e) for s, e, _a in pt.get(name, [])]
        occupied[name] = occ
        for t, cells in sorted(X7.tables_of(plain).items()):
            mine = X7.row_labels(cells, plain)
            head = X7.heading(plain, cells)
            if not ptabs:
                continue
            sc = [(X7.match_score(mine, head, q)[0], q[0] == C4.code_of(name)) for q in ptabs]
            top = max(sc)
            if top[0] < 2:                                   # 行の字が 2 つ以上重なるか、見出しがよく似る表だけ
                continue
            group = [q for q, x in zip(ptabs, sc) if x == top]
            gk = tuple((q[0], q[1]) for q in group)
            USE[gk] += 1
            best = group[min(USE[gk], len(group)) - 1]
            labels = {}
            tag_cols = set(cc for (r, cc), (pcs, pce) in best[3].items() if (pcs, pce) in best[4])
            for (r, cc), (cs, ce) in sorted(cells.items()):
                if u"<table" in plain[cs:ce].lower() or not X7.vis(plain[cs:ce]):
                    continue
                if cc not in tag_cols or NUM_RE.fullmatch(X7.vis(plain[cs:ce], 200)):      # 札の在る列だけ・数だけの升は除く
                    continue
                if any(cs <= s and e <= ce for s, e in occ) or any(s <= cs and ce <= e and (e - s) < 4 * (ce - cs) for s, e in occ):
                    continue
                n_mark += 1
                mid = u"M%d" % n_mark
                marks[mid] = (name, cs, ce)
                labels[(cs, ce)] = mid
            if not labels:
                continue
            lab = lambda cs, ce: (u"★" + labels[(cs, ce)]) if (cs, ce) in labels else None
            _code, _t, pplain, pcells, ptag, _l, phead = best
            ptxt = lambda cs, ce: (u"要素=%s・文脈=%s" % (ptag[(cs, ce)].get("name"), ptag[(cs, ce)].get("contextRef"))) if (cs, ce) in ptag else None
            blk = (u"## 今年の表(file %d・表 %d)\n\n表の前の字: %s\n\n%s\n\n### 前の年の、行の字と表の前の字が最も重なる表(札つき)\n\n表の前の字: %s\n\n%s\n"
                   % (fi, t, head, X7.grid_md(cells, plain, lab), phead, X7.grid_md(pcells, pplain, ptxt)))
            parts.append((blk, [labels[k] for k in sorted(labels)]))
    screens, cur_b, cur_ids, cur_len = [], [], [], 0
    hd = u"# 表の文の札を付ける画面\n\n★M番号 の升に、要素と文脈の札を付ける。\n\n"
    for blk, ids in parts:
        if cur_b and cur_len + len(blk) > CHUNK:
            screens.append((hd + u"\n".join(cur_b), cur_ids))
            cur_b, cur_ids, cur_len = [], [], 0
        cur_b.append(blk)
        cur_ids += ids
        cur_len += len(blk)
    if cur_b:
        screens.append((hd + u"\n".join(cur_b), cur_ids))
    return screens, marks, (shp, by_name), occupied, res


def place_answers(cur, entries, marks, forms, occupied, res, answers, names):
    shp, by_name = forms
    own = C5.xsd_info(entries)[1]
    plain_of = dict((nm, pl) for nm, pl, _F, _H in cur)
    out = collections.defaultdict(list)
    c = collections.Counter()
    for mid, (name, cs, ce) in marks.items():
        a = answers.get(mid)
        if not a:
            c[u"付けない"] += 1
            continue
        nm, ctx = a.get("name") or u"", a.get("contextRef") or u""
        pre, _c, local = nm.partition(":")
        if ctx not in res or res[ctx]["type"] != "context":
            c[u"形で落とした・文脈が無い"] += 1
            continue
        if X7.STD_PREFIX_RE.match(pre):
            if local not in names.get(pre, ()):
                c[u"形で落とした・要素がタクソノミに無い"] += 1
                continue
        elif local not in own:
            c[u"形で落とした・要素が今年の定義に無い"] += 1
            continue
        plain = plain_of[name]
        form = shp.get((nm, ctx))
        base = dict(form[2]) if form else dict(by_name.get(nm) or {"name": nm})
        base["contextRef"] = ctx
        span = recon(plain, cs, ce, form[0], form[1]) if form else None
        if span is None:
            span = innermost(plain, cs, ce)
        if span is not None and form and "S1" in FIX:
            span = strip_text(plain, span[0], span[1], form[3], form[4]) or span
        if span is None:
            c[u"形で落とした・置き場が無い"] += 1
            continue
        s, e = span
        if any(s < e2 and s2 < e and not ((s <= s2 and e2 <= e) or (s2 <= s and e <= e2)) for s2, e2 in occupied[name] + [(x, y) for x, y, _ in out[name]]):
            c[u"形で落とした・置いた fact と交わる"] += 1
            continue
        if any((s2, e2) == (s, e) for s2, e2, _a in out[name]):
            c[u"形で落とした・同じ置き場"] += 1
            continue
        out[name].append((s, e, base))
        c[u"置いた"] += 1
    return out, c


def score(cur, added, occupied_rules_texts):
    u"""置いた fact を今年の答えと比べる(置き場は前後の空白を除いて比べる・属性は TEXT_ATTRS)。採点だけ。"""
    c = collections.Counter()
    for name, plain, F, _H in cur:
        truth = {}
        for f in F:
            if f["kind"] == "nonNumeric" and MEM_RE.search(f["attrs"].get("contextRef") or u""):
                truth.setdefault(X9.trim(plain, f["start"], f["end"]), []).append(dict((k, f["attrs"][k]) for k in C4.TEXT_ATTRS if k in f["attrs"]))
        have = set(X9.trim(plain, s, e) for s, e, _a in occupied_rules_texts.get(name, []))
        c[u"答えの軸のメンバーの付いた文の fact"] += sum(len(v) for v in truth.values())
        c[u"規則で置いた(置き場が答えと同じ)"] += sum(len(truth[k]) for k in have if k in truth)
        for s, e, a in added.get(name, []):
            k = X9.trim(plain, s, e)
            want = dict((x, a[x]) for x in C4.TEXT_ATTRS if x in a)
            if k in truth and want in truth[k]:
                c[u"席・答えと同じ"] += 1
            elif k in truth:
                c[u"席・置き場は同じで属性が違う"] += 1
            else:
                c[u"席・置き場が違う"] += 1
    return c
