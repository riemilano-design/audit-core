# -*- coding: utf-8 -*-
u"""便 XC7: 規則で置けなかった表の数の升を、AI の席(subagent)に前の年の表を見せて札を付けさせる。

画面(今年の答えを読まない): 今年の表(行・列・升の字。規則で置いた升は付けた札も見せる)と、行の字が最も多く重なる前の年の表(升ごとの札)。
席は、印の付いた升ごとに札(要素・文脈・単位・桁・倍率・符号)か「付けない」を答える。機械は札の形を確かめ(文脈と単位が前の年の定義に在る・
要素の前置きが標準か今年の提出者の xsd に在る)、通った札だけ置く。土台は便 XC6(便 XC5 の F1〜F7 と G1・G2)。
今年の答えは採点でだけ読む。会社の素材の画面と席の答えは scratchpad に置く(repo に入れない)。
"""
import bisect
import collections
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc7_xc6", os.path.join(os.path.dirname(HERE), "xc6", "xc6.py"))
C6 = importlib.util.module_from_spec(spec)
sys.modules["_xc7_xc6"] = C6
spec.loader.exec_module(C6)
C5, C4, C3, C2, C1, C0, B, V = C6.C5, C6.C4, C6.C3, C6.C2, C6.C1, C6.C0, C6.B, C6.V
HP = C0.HP
od = collections.OrderedDict
TAG_RE = re.compile(r"<[^>]*>")
WS_RE = re.compile(r"\s+")
ATTRS = ("name", "contextRef", "unitRef", "decimals", "scale", "sign")
CHUNK = 60000                        # 画面 1 枚の字の数の目安(表の切れ目で分ける)
DIGIT_RE = re.compile(r"[0-9]")
STD_PREFIX_RE = re.compile(r"^(jp[a-z]+_cor|jpdei_cor|jpigp_cor)$")


def vis(s, n=40):
    t = WS_RE.sub(u" ", unicodedata.normalize("NFKC", TAG_RE.sub(u" ", s))).strip()
    return t if len(t) <= n else t[:n - 1] + u"…"


def tables_of(plain):
    u"""素の本文 → {表の番号: {(行, 列): (中身の始まり, 終わり)}}(便 XH0 の cells_of)。"""
    out = collections.defaultdict(dict)
    for t, r, c, cs, ce in HP.cells_of(plain):
        out[t][(r, c)] = (cs, ce)
    return out


def grid_md(cells, plain, label_of):
    u"""表の升 → 字の表(markdown)。``label_of(cs, ce)`` は升に添える字か None。"""
    rows = sorted(set(r for r, _c in cells))
    cols = sorted(set(c for _r, c in cells))
    lines = [u"| 行 | " + u" | ".join(u"列%d" % c for c in cols) + u" |", u"|---|" + u"---|" * len(cols)]
    for r in rows:
        tds = []
        for c in cols:
            if (r, c) not in cells:
                tds.append(u"")
                continue
            cs, ce = cells[(r, c)]
            t = vis(plain[cs:ce]).replace(u"|", u"/")
            lab = label_of(cs, ce)
            tds.append(t + (u" 〔%s〕" % lab if lab else u""))
        lines.append(u"| %d | " % r + u" | ".join(tds) + u" |")
    return u"\n".join(lines)


def tag_text(a):
    return u"・".join(u"%s=%s" % (k, a[k]) for k in ATTRS if a.get(k))


def row_labels(cells, plain):
    return set(vis(plain[cells[k][0]:cells[k][1]], 30) for k in cells if k[1] == min(c for _r, c in cells))


def heading(plain, cells, n=60):
    u"""表の前の見える字の終わり(表の見出し。注記の題など)。"""
    st = min(cs for cs, _ce in cells.values())
    i = plain.lower().rfind(u"<table", 0, st)
    t = vis(plain[max(0, i - 1500):i], 100000) if i > 0 else u""
    return t[-n:]


def match_score(mine_lab, mine_head, q):
    import difflib
    h1, h2 = DIGIT_RE.sub(u"", mine_head)[-30:], DIGIT_RE.sub(u"", q[6])[-30:]        # 年の数字の違いで組を変えない
    return (len(q[5] & mine_lab) + 5 * difflib.SequenceMatcher(None, h1, h2).ratio(), q[0])


def build_screen(cur, prv, entries):
    u"""1 組 → (画面の字, 印の表 {升の番号: (file の名, start, end, 空の fact か)}, 置いた数の fact の札 {(file の名, start, end): 属性})。"""
    C6.OWN[0] = C5.xsd_info(entries)[1]
    C3.xsd_of_cur[0] = C3.filer_xsd(entries)
    prior = C2.build_prior(prv, C3.RULES)
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None)
    res = C0.shift_resources(prior_H)
    ptabs = []
    for name, plain, F, _H in prv:
        tabs = tables_of(plain)
        nf = [(e["start"], e["end"], e["attrs"]) for e in F if e["kind"] == "nonFraction"]
        starts = [x[0] for x in nf]
        for t, cells in tabs.items():
            tagmap = {}
            for (r, c), (cs, ce) in cells.items():
                i = bisect.bisect_left(starts, cs)
                if i < len(nf) and nf[i][0] < ce:
                    tagmap[(cs, ce)] = nf[i][2]
            if tagmap:
                ptabs.append((C4.code_of(name), t, plain, cells, tagmap, row_labels(cells, plain), heading(plain, cells)))
    parts, marks, placed = [], od(), {}
    USE = collections.Counter()
    n_mark = 0
    for fi, (name, plain, _F, _H) in enumerate(cur):
        put, _stop, _skip, _m = C6.place3_g(plain, prior, res, C3.RULES)
        pmap = dict(((s, e), a) for s, e, a in put)
        for (s, e), a in pmap.items():
            placed[(name, s, e)] = a
        for t, cells in sorted(tables_of(plain).items()):
            mine = row_labels(cells, plain)
            head = heading(plain, cells)
            best = None
            if ptabs:
                sc = [(match_score(mine, head, q)[0], q[0] == C4.code_of(name)) for q in ptabs]
                top = max(sc)
                group = [q for q, x in zip(ptabs, sc) if x == top]                # 同じ重なりの表が幾つも在れば、何番目どうしで組む
                gk = tuple((q[0], q[1]) for q in group)
                USE[gk] += 1
                best = group[min(USE[gk], len(group)) - 1]
            if best is not None and not (best[5] & mine):
                best = None
            c0 = min(c for _r, c in cells)
            placed_cols = set(c for (r, c), (cs, ce) in cells.items() if any(cs <= s and e <= ce for (s, e) in pmap))
            prior_cols = set(c for (r, c), (cs, ce) in best[3].items() if (cs, ce) in best[4]) if best else set()
            placed_rows = [r for (r, c), (cs, ce) in cells.items() if any(cs <= s and e <= ce for (s, e) in pmap)]
            first_row = min(placed_rows) if placed_rows else None
            targets = {}
            for (r, c), (cs, ce) in cells.items():
                if u"<table" in plain[cs:ce].lower() or c == c0:
                    continue
                if c not in placed_cols and c not in prior_cols:              # 札の在る列だけ
                    continue
                if first_row is not None and r < first_row:                    # 札の在る最初の行より上(頭の行)は印を付けない
                    continue
                lab0 = cells.get((r, c0))
                if not lab0 or not vis(plain[lab0[0]:lab0[1]]):                # 行の字(最初の列)の無い行は印を付けない
                    continue
                for s, e, _sf in HP.predict_cell(plain[cs:ce], False):
                    s, e = cs + s, cs + e
                    if (s, e) not in pmap:
                        targets[(cs, ce)] = (s, e)
            if not targets:
                continue
            labels = {}
            for (cs, ce), (s, e) in sorted(targets.items()):
                n_mark += 1
                mid = u"M%d" % n_mark
                marks[mid] = (name, s, e, s == e)
                labels[(cs, ce)] = mid
            def lab(cs, ce):
                if (cs, ce) in labels:
                    return u"★" + labels[(cs, ce)]
                for (s, e), a in pmap.items():
                    if cs <= s and e <= ce:
                        return tag_text(a)
                return None
            blk = u"## 今年の表(file %d・表 %d)\n\n表の前の字: %s\n\n%s\n" % (fi, t, head, grid_md(cells, plain, lab))
            used = set(a.get("contextRef") for (s2, e2), a in pmap.items() if any(cs <= s2 and e2 <= ce for (cs, ce) in cells.values()))
            if best:
                _code, _t, pplain, pcells, ptag, _lab, phead = best
                blk += u"\n### 前の年の、行の字と表の前の字が最も重なる表(札つき)\n\n表の前の字: %s\n\n%s\n" % (phead, grid_md(pcells, pplain, lambda cs, ce: tag_text(ptag[(cs, ce)]) if (cs, ce) in ptag else None))
                used |= set(a.get("contextRef") for a in ptag.values())
            else:
                blk += u"\n### 前の年に行の字の重なる表は無い\n"
            parts.append((blk, [labels[k] for k in sorted(labels)], used))
    units = sorted(k for k, r in res.items() if r["type"] == "unit")
    chunks, cur_blk, cur_used, cur_len = [], [], set(), 0
    for blk, ids, used in parts:
        if cur_blk and cur_len + len(blk) > CHUNK:
            chunks.append((cur_blk, cur_used))
            cur_blk, cur_used, cur_len = [], set(), 0
        cur_blk.append((blk, ids))
        cur_used |= used
        cur_len += len(blk)
    if cur_blk:
        chunks.append((cur_blk, cur_used))
    screens = []
    for blks, used in chunks:
        ctx = sorted(k for k in used if k in res) + [u"(ほかに、前の年の文脈を 1 年ずらした id は全部使える。一覧は使った物だけ)"]
        head = (u"# 札を付ける画面\n\nこの画面の表で使われている文脈の id: " + u"・".join(ctx) +
                u"\n\n使える単位の id: " + u"・".join(units) + u"\n\n★M番号 の升に札を付ける。\n\n")
        screens.append((head + u"\n".join(b for b, _i in blks), [i for _b, ids in blks for i in ids]))
    return screens, marks, placed


def check_tag(a, res, own):
    u"""席の札の形の確かめ。通れば None、通らなければ理由。"""
    name = a.get("name") or u""
    pre, _c, local = name.partition(":")
    if not local:
        return u"要素の名の形"
    if not STD_PREFIX_RE.match(pre) and local not in own:
        return u"要素が今年の定義に無い"
    if a.get("contextRef") not in res or res[a["contextRef"]]["type"] != "context":
        return u"文脈が無い"
    if a.get("unitRef") and (a["unitRef"] not in res or res[a["unitRef"]]["type"] != "unit"):
        return u"単位が無い"
    return None


def norm_tag(a):
    return tuple((k, str(a.get(k) or u"")) for k in ATTRS)


def score_answers(cur, marks, answers, res, own):
    u"""席の答えを採点する。今年の答えはここでだけ読む。"""
    truth = {}
    for name, _plain, F, _H in cur:
        for e in F:
            if e["kind"] == "nonFraction":
                truth[(name, e["start"], e["end"])] = e["attrs"]
    c = collections.Counter()
    for mid, (name, s, e, _nil) in marks.items():
        t = truth.get((name, s, e))
        c["印"] += 1
        c["答えの在る印"] += t is not None
        a = answers.get(mid)
        if not a:
            c["付けない"] += 1
            c["付けない・答えが在る"] += t is not None
            continue
        why = check_tag(a, res, own)
        if why:
            c["形で落とした"] += 1
            c["形で落とした・" + why] += 1
            continue
        c["置いた"] += 1
        if t is None:
            c["置いた・答えが無い"] += 1
        elif norm_tag(a) == norm_tag(t):
            c["置いた・答えと同じ"] += 1
        else:
            c["置いた・答えと違う"] += 1
            for k in ATTRS:
                if str(a.get(k) or u"") != str(t.get(k) or u""):
                    c["違う属性・" + k] += 1
    return c
