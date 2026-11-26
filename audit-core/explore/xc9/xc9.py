# -*- coding: utf-8 -*-
u"""便 XC9: 規則で置けなかった文の fact のうち TextBlock(節ごとの文)を、AI の席(subagent)に置かせる。

画面(今年の答えを読まない): file ごとに、(a) 前の年に在って今年の規則で置けなかった TextBlock の一覧(要素・文脈・前の年の始めと終わりの見える字・
直前の見出し)と、(b) 今年の素の本文の塊(p・h1〜h6・table・ul・ol で、表や段落の中に無い物)に番号を振った一覧(始めの見える字)。
席は TextBlock ごとに、始めの塊と終わりの塊の番号か null を答える。機械は塊の範囲を字の位置にし、便 XC5 の F1(タグの対)と、
置いた文の fact と交わらない(入れ子か離れている)ことを確かめて置く。属性は前の年の TextBlock の属性のまま(文脈は前の年と同じ id)。
対象は軸のメンバーの無い文脈の TextBlock だけ。土台は便 XC8(数の fact の席の札まで)。
"""
import bisect
import collections
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc9_xc8", os.path.join(os.path.dirname(HERE), "xc8", "xc8.py"))
X8 = importlib.util.module_from_spec(spec)
sys.modules["_xc9_xc8"] = X8
spec.loader.exec_module(X8)
X7, C6, C5, C4, C3, C2, C1, C0, B = X8.X7, X8.C6, X8.C5, X8.X7.C4, X8.X7.C3, X8.C2, X8.C1, X8.C0, X8.B
od = collections.OrderedDict
TAG = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9:]*)\b[^>]*?(/?)>')
CAND = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol"}
VOID = {"br", "img", "hr", "meta", "link", "input", "col", "area", "base", "wbr", "source"}
MEM_RE = re.compile(r"_(?!NonConsolidatedMember$)[A-Za-z0-9-]+Member")
CHUNK = 60000
FIX = {"A1"}                         # A1 端の空の塊の合わせ


def blocks(plain):
    u"""素の本文 → 塊 [(start, end, 種類)](表・段落・並びの中に無い候補の要素)。"""
    st, out = [], []
    b0 = max(0, plain.lower().find("<body"))
    for mm in TAG.finditer(plain, b0):
        close, tag, selfc = mm.group(1), mm.group(2).lower(), mm.group(3)
        if tag in VOID or selfc:
            continue
        if not close:
            st.append((tag, mm.start()))
            continue
        while st:
            t, s = st.pop()
            if t == tag:
                if tag in CAND and not any(x[0] in ("table", "p", "ul", "ol") for x in st):
                    out.append((s, mm.end(), tag))
                break
    return sorted(out)


def trim(plain, s, e):
    while s < e and plain[s].isspace():
        s += 1
    while e > s and plain[e - 1].isspace():
        e -= 1
    return s, e


def vis(s, n):
    return X7.vis(s, n)


BLANK_RE = re.compile(r"&#160;|&nbsp;|&#12288;|\s|\u3000|\xa0")


def blank(html):
    u"""塊が空(タグと空白と &#160; だけ)か。"""
    return not BLANK_RE.sub(u"", X7.TAG_RE.sub(u"", html))


def is_tb(a):
    return (a.get("name") or u"").endswith("TextBlock") and not MEM_RE.search(a.get("contextRef") or u"")


def prior_tbs(prv):
    u"""前の年 → {file の型: [(属性, 始めの字, 終わりの字, 直前の字)]}。"""
    out = collections.defaultdict(list)
    for name, plain, F, _H in prv:
        for f in F:
            if f["kind"] == "nonNumeric" and is_tb(f["attrs"]):
                body = plain[f["start"]:f["end"]]
                t = X7.WS_RE.sub(u" ", X7.unicodedata.normalize("NFKC", X7.TAG_RE.sub(u" ", body))).strip()
                pre = X7.WS_RE.sub(u" ", X7.unicodedata.normalize("NFKC", X7.TAG_RE.sub(u" ", plain[max(0, f["start"] - 1500):f["start"]]))).strip()
                inner = [(bs, be) for bs, be, _t in blocks(plain) if f["start"] <= bs and be <= f["end"]]
                eb = (blank(plain[inner[0][0]:inner[0][1]]), blank(plain[inner[-1][0]:inner[-1][1]])) if inner else (False, False)
                out[C4.code_of(name)].append((dict(f["attrs"]), t[:80], t[-80:], pre[-50:], eb))
    return out


def placed_texts(cur, prv, entries):
    u"""便 XC5 の組み方で置いた文の fact → {file の名: [(start, end, 属性)]}(便 XC6 の G1・G2 つき・席の数の札なし)。"""
    C6.OWN[0] = C5.xsd_info(entries)[1]
    C3.xsd_of_cur[0] = C3.filer_xsd(entries)
    X8.SEATS.clear()
    C2.place3 = lambda plain, prior, res, rules: C6.place3_g(plain, prior, res, rules)
    try:
        _texts, _stat, pt = C5.built_texts5(cur, prv, entries, C5.FIXES)
    finally:
        C2.place3 = X8._orig
    return pt


def build_screens(cur, prv, entries):
    u"""1 組 → (画面 [(字, [T 番号])], T の表 {T: (file の名, 属性)}, 塊の表 {file の名: [(s, e)]}, 置いた文の fact)。"""
    pt = placed_texts(cur, prv, entries)
    ptb = prior_tbs(prv)
    screens, tmap, bmap = [], od(), {}
    nt = 0
    for fi, (name, plain, _F, _H) in enumerate(cur):
        have = set((a.get("name"), a.get("contextRef")) for _s, _e, a in pt.get(name, []))
        todo = [x for x in ptb.get(C4.code_of(name), []) if (x[0].get("name"), x[0].get("contextRef")) not in have]
        if not todo:
            continue
        bl = blocks(plain)
        bmap[name] = [(s, e) for s, e, _t in bl]
        inside = [(s, e) for s, e, a in pt.get(name, []) if (a.get("name") or u"").endswith("TextBlock")]
        lines = []
        for k, (s, e, tag) in enumerate(bl):
            mark = u"〔既〕" if any(a <= s and e <= b for a, b in inside) else u""
            lines.append(u"B%d %s%s %s" % (k, u"[表] " if tag == "table" else (u"[" + tag + u"] " if tag[0] == "h" else u""), mark, vis(plain[s:e], 50)))
        ts = []
        for a, first, last, pre, eb in todo:
            nt += 1
            tid = u"T%d" % nt
            tmap[tid] = (name, a, eb)
            ts.append(u"- %s 要素=%s 文脈=%s\n  前の年の直前の字: %s\n  前の年の始め: %s\n  前の年の終わり: %s" % (tid, a.get("name"), a.get("contextRef"), pre, first, last))
        head = u"# 節を置く画面(file %d)\n\n## 置く節(前の年の TextBlock)\n\n%s\n\n## 今年の本文の塊\n\n" % (fi, u"\n".join(ts))
        body = u"\n".join(lines)
        if len(head) + len(body) <= CHUNK:
            screens.append((head + body, [t for t in tmap if tmap[t][0] == name]))
        else:
            # 長い file は塊を窓に分けず、そのまま 1 枚にする(席は file を読む)
            screens.append((head + body, [t for t in tmap if tmap[t][0] == name]))
    return screens, tmap, bmap, pt


def place_answers(cur, tmap, bmap, pt, answers):
    u"""席の答え → {file の名: [(start, end, 属性)]} と数え。"""
    plain_of = dict((nm, pl) for nm, pl, _F, _H in cur)
    out = collections.defaultdict(list)
    c = collections.Counter()
    for tid, (name, a, eb) in tmap.items():
        ans = answers.get(tid)
        if not ans:
            c[u"付けない"] += 1
            continue
        try:
            i, j = int(str(ans[0]).lstrip("B")), int(str(ans[1]).lstrip("B"))
            s, e = bmap[name][i][0], bmap[name][j][1]
        except (ValueError, IndexError, KeyError, TypeError):
            c[u"形で落とした・塊の番号"] += 1
            continue
        if j < i:
            c[u"形で落とした・塊の順"] += 1
            continue
        plain = plain_of[name]
        if "A1" in FIX:                                   # 端の空の塊を前の年の節の端に合わせる
            bl = bmap[name]
            isb = lambda k: blank(plain[bl[k][0]:bl[k][1]])
            if eb[1]:
                while j + 1 < len(bl) and not isb(j) and isb(j + 1):
                    j += 1
                    break
            else:
                while j > i and isb(j):
                    j -= 1
            if eb[0]:
                if i > 0 and not isb(i) and isb(i - 1):
                    i -= 1
            else:
                while i < j and isb(i):
                    i += 1
            s, e = bl[i][0], bl[j][1]
        if not C5.balanced(plain[s:e]):
            c[u"形で落とした・タグの対"] += 1
            continue
        clash = False
        for s2, e2, _a2 in pt.get(name, []) + out[name]:
            if s < e2 and s2 < e and not ((s <= s2 and e2 <= e) or (s2 <= s and e <= e2)):
                clash = True
                break
        if clash:
            c[u"形で落とした・置いた文の fact と交わる"] += 1
            continue
        out[name].append((s, e, a))
        c[u"置いた"] += 1
    return out, c


def score(cur, added, pt):
    u"""置いた TextBlock を今年の答えと比べる(始めと終わりは前後の空白を除いて比べる)。採点だけ。"""
    c = collections.Counter()
    for name, plain, F, _H in cur:
        truth = {}
        for f in F:
            if f["kind"] == "nonNumeric" and is_tb(f["attrs"]):
                truth.setdefault(trim(plain, f["start"], f["end"]), []).append(dict((k, f["attrs"][k]) for k in C4.TEXT_ATTRS if k in f["attrs"]))
        got_rules = set(trim(plain, s, e) for s, e, a in pt.get(name, []) if is_tb(a))
        c[u"答えの TextBlock"] += sum(len(v) for v in truth.values())
        c[u"規則で置いた TextBlock(置き場が答えと同じ)"] += sum(len(truth[k]) for k in got_rules if k in truth)
        for s, e, a in added.get(name, []):
            k = trim(plain, s, e)
            want = dict((x, a[x]) for x in C4.TEXT_ATTRS if x in a)
            if k in truth and want in truth[k]:
                c[u"席・答えと同じ"] += 1
            elif k in truth:
                c[u"席・置き場は同じで属性が違う"] += 1
            else:
                c[u"席・置き場が違う"] += 1
    return c


def load_answers(base, head, n):
    return X8.load_answers(base, head, n)
