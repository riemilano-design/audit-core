# -*- coding: utf-8 -*-
u"""便 XC1: 便 XC0 の置き方に 2 つの規則を足し、黙って違う fact(主に contextRef)を減らす。

R1 番号の行: 前の年の同じ列(h, th, td)の fact の文脈に番号つきのメンバー(No#…Member・Row#Member)が在れば、
   今年の表の中で番号の行を上から数え直し、その番号のメンバーにする(行の字が人や会社の名で年ごとに順位が替わる表)。
R2 本文の期: 表の直前の字に「至 年月日」が在れば、それを表の期の終わりと読む。置く fact の文脈(1 年ずらした定義)の期の終わりの年が
   それと違えば、文脈の期の部品(CurrentYear・Prior#Year)を年の差だけずらす。ずらした id の定義が無ければ止める。
今年の答えは置く部品に渡さない(便 XC0 と同じ)。
"""
import bisect
import collections
import datetime
import importlib.util
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_xc1_xc0", os.path.join(os.path.dirname(HERE), "xc0", "xc0.py"))
C0 = importlib.util.module_from_spec(spec)
sys.modules["_xc1_xc0"] = C0
spec.loader.exec_module(C0)

od = collections.OrderedDict
I, Z, G, B, X = C0.I, C0.Z, C0.G, C0.B, C0.X
TAG_RE = C0.TAG_RE
SEEN_MAX_NO = 3
DEV_JUDGED = 20                      # 判定の 60 組のうち番号の小さい 20 組も作りに使う。残りの 40 組で判定
NUM_MEMBER_RE = re.compile(r"^(No|Row)([0-9]+)([A-Za-z]*Member)$")
PERIOD_RE = re.compile(r"^(CurrentYear|Prior([0-9]+)Year)(Duration|Instant)$")
ERA = {u"令和": 2018, u"平成": 1988}
DATE_RE = re.compile(u"(令和|平成)?\\s*([0-9]+|元)\\s*年\\s*([0-9]+)\\s*月\\s*([0-9]+)\\s*日")
TO_RE = re.compile(u"至")
LOOK_BACK = 400                      # 表の前の字を見る長さ(タグを除く前の字の数)


# ======================================================================================================
# R1 番号の行
def shape_of(ctx):
    return G.shape_of(ctx)


def prior_cols(prior_files):
    u"""前の年 → 表 COL: (h, th, td) → {(name, 形, unitRef, decimals, scale, format, nil)}・その頭の印 SIGC。"""
    col, sigc = {}, {}
    for _name, plain, F, _H in prior_files:
        cells = C0.plain_cells(plain)
        keys = C0.row_keys(plain)
        pred = C0.predicted(plain, cells)
        marks = C0.head_marks(plain, cells, pred, keys)
        cst = [c[1] for c in cells]
        for e in F:
            if e["kind"] != "nonFraction":
                continue
            j = bisect.bisect_right(cst, e["start"]) - 1
            while j >= 0 and not (cells[j][1] <= e["start"] and e["end"] <= cells[j][2]):
                j -= 1
            if j < 0:
                continue
            k, _cs, _ce, td = cells[j]
            h, th, T, ser = keys[k]
            a = e["attrs"]
            sh = shape_of(a.get("contextRef"))
            if sh is None:
                continue
            nil = a.get("xsi:nil") == "true"
            col.setdefault((h, th, td), set()).add((a.get("name"), sh, a.get("unitRef"), None if nil else a.get("decimals"),
                                                    None if nil else a.get("scale"), None if nil else a.get("format"), nil))
            sigc.setdefault((h, th, td), set()).add(marks.get(ser, u""))
    return col, sigc


# ======================================================================================================
# R2 本文の期
def to_date(m):
    era, y, mo, d = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
    y = 1 if y == u"元" else int(y)
    if era:
        y += ERA[era]
    try:
        return datetime.date(y, mo, d)
    except ValueError:
        return None


def table_end_dates(plain):
    u"""素の本文 → {表の通し番号: 表の直前の字の最後の「至 年月日」の日付}。表の直前の字は、前の表の終わり(か LOOK_BACK 字)から表の始まりまで。"""
    starts = [m.start() for m in Z.TABLE_RE.finditer(plain)]
    ends = [m.end() for m in re.finditer(r"</table\s*>", plain, re.I)]
    out = {}
    for ser, s in enumerate(starts, 1):
        prev_end = max([e for e in ends if e <= s] or [0])
        seg = unicodedata.normalize("NFKC", TAG_RE.sub(u"", plain[prev_end:s]))[-LOOK_BACK:]
        last = None
        for t in TO_RE.finditer(seg):
            m = DATE_RE.search(seg, t.end(), t.end() + 30)
            if m:
                last = to_date(m)
        if last:
            out[ser] = last
    return out


def period_of(ctx):
    head = ctx.split("_")[0]
    m = PERIOD_RE.match(head)
    if not m:
        return None
    return (0 if m.group(1) == "CurrentYear" else int(m.group(2))), m.group(3)


def with_period(ctx, n, kind):
    parts = ctx.split("_")
    parts[0] = ("CurrentYear" if n == 0 else "Prior%dYear" % n) + kind
    return "_".join(parts)


def end_year(defn):
    for k, v in defn["period"]:
        if k in ("xbrli:endDate", "xbrli:instant") and v:
            return int(v[:4])
    return None


def numbering(cells, keys, pred, tab, col, valid=None):
    u"""(番号の列を使う cell の集まり, 行の番号 → 表の中の番号)。``valid`` が在れば、その (h, th, td) の列だけ。"""
    use_cell, row_no, k_of = {}, {}, {}
    for i in sorted(pred):
        k, _cs, _ce, td = cells[i]
        h, th, T, _ser = keys[k]
        if not T or (valid is not None and (h, th, td) not in valid):    # 行の字が空の行(合計の行など)は数えない
            continue
        cands = tab.get((h, th, T, td), set()) if T else set()
        if (h, th, td) in col and (not cands or any(shape_of(c[1]) for c in cands)):
            use_cell[i] = True
    for k in sorted(set(cells[i][0] for i in use_cell)):
        ser = keys[k][3]
        row_no[ser] = row_no.get(ser, 0) + 1
        k_of[k] = row_no[ser]
    return use_cell, k_of


def prior_valid(prior_files, tab, col):
    u"""前の年の書類の中で、行を上から数えた番号が前の年自身のメンバーの番号と全部合う列 (h, th, td) の集まり(答えは読まない)。"""
    ok, bad = set(), set()
    for _name, plain, F, _H in prior_files:
        cells = C0.plain_cells(plain)
        keys = C0.row_keys(plain)
        pred = C0.predicted(plain, cells)
        use_cell, k_of = numbering(cells, keys, pred, tab, col)
        cst = [c[1] for c in cells]
        for e in F:
            if e["kind"] != "nonFraction":
                continue
            j = bisect.bisect_right(cst, e["start"]) - 1
            while j >= 0 and not (cells[j][1] <= e["start"] and e["end"] <= cells[j][2]):
                j -= 1
            if j < 0 or j not in use_cell:
                continue
            k, _cs, _ce, td = cells[j]
            h, th, _T, _ser = keys[k]
            sh = shape_of(e["attrs"].get("contextRef"))
            good = sh is not None and G.with_number(sh, k_of[k]) == e["attrs"].get("contextRef")
            (ok if good else bad).add((h, th, td))
    return frozenset(ok - bad)


# ======================================================================================================
# 置く
def place2(plain, tab, sig, col, sigc, res, rules=("R1", "R2"), valid=frozenset()):
    u"""便 XC0 の ``place`` に R1・R2 を足したもの。返り値も同じ形 + 規則ごとに替えた数。"""
    cells = C0.plain_cells(plain)
    keys = C0.row_keys(plain)
    pred = C0.predicted(plain, cells)
    marks = C0.head_marks(plain, cells, pred, keys)
    tends = table_end_dates(plain) if "R2" in rules else {}
    # R1: 番号の行を表ごとに上から数える(番号の列を使う cell を持つ行)。前の年で確かめた列だけ
    use_cell, k_of = ({}, {}) if "R1" not in rules else numbering(cells, keys, pred, tab, col, valid)
    # R2 は 1 年だけの表に当てる: 表の中で前の年の候補の Duration の期が 1 種類だけ
    dur_of = collections.defaultdict(set)
    dur_ctx = {}
    if "R2" in rules:
        for i in pred:
            k, _cs, _ce, td = cells[i]
            h, th, T, ser = keys[k]
            for c in (tab.get((h, th, T, td), set()) if T else set()):
                pe = period_of(c[1]) if c[1] else None
                if pe and pe[1] == "Duration":
                    dur_of[ser].add(pe[0])
                    if c[1] in res:
                        dur_ctx.setdefault(ser, c[1])
    put, stop, skip = [], [], 0
    moved = collections.Counter()
    for i, spans in sorted(pred.items()):
        k, cs, _ce, td = cells[i]
        h, th, T, ser = keys[k]
        for s, e in spans:
            nil = s == e
            if i in use_cell:
                cands = set((c[0], G.with_number(c[1], k_of[k])) + c[2:] for c in col[(h, th, td)])
                ok = marks.get(ser, u"") in sigc.get((h, th, td), ())
                tag = "R1"
            else:
                cands = tab.get((h, th, T, td), set()) if T else set()
                ok = marks.get(ser, u"") in sig.get((h, th, T, td), ())
                tag = None
            if not cands:
                skip += 1
                continue
            if not ok:
                stop.append((s, e, u"表の頭の字が前の年と違う"))
                continue
            b3 = set(c[:3] for c in cands)
            if len(b3) != 1:
                stop.append((s, e, u"前の年の候補が 2 つ以上"))
                continue
            name, ctx, unit = next(iter(b3))
            # R2: 表の直前の「至」の年と文脈の期の終わりの年を照らす
            if ser in tends and ser in dur_ctx and len(dur_of.get(ser, ())) == 1:
                pe = period_of(ctx)
                ey = end_year(res[dur_ctx[ser]])        # 年の差は表の Duration の文脈で決め、表の全部の文脈に当てる
                if pe is not None and ey is not None and ey != tends[ser].year:
                    n2 = pe[0] - (tends[ser].year - ey)
                    new = with_period(ctx, n2, pe[1]) if n2 >= 0 else None
                    if new is None or new not in res:
                        stop.append((s, e, u"本文の期と文脈の期が合わない"))
                        continue
                    ctx = new
                    moved["R2"] += 1
            if tag:
                moved[tag] += 1
            a = od([("name", name), ("contextRef", ctx), ("unitRef", unit)])
            if nil:
                a["xsi:nil"] = "true"
            else:
                rest = set(c[3:6] for c in cands if not c[6])
                if len(rest) != 1:
                    stop.append((s, e, u"前の年の桁・書式が 1 つに決まらない"))
                    continue
                a["decimals"], a["scale"], a["format"] = next(iter(rest))
                if X.reads_negative(TAG_RE.sub(u"", plain[cs:s])):
                    a["sign"] = "-"
            put.append((s, e, a))
    return put, stop, skip, moved


# ======================================================================================================
# 採点(便 XC0 と同じ数え方。今年の答えはここでだけ読む)
def score_pair(cur_zip, prior_zip, rules):
    cur = B.build_files(B.load_package(cur_zip))
    prv = B.build_files(B.load_package(prior_zip))
    tab, sig = C0.prior_table(prv)
    col, sigc = prior_cols(prv)
    valid = prior_valid(prv, tab, col)
    prior_H = next((H for _n, _p, _F, H in prv if H is not None), None)
    cur_H = next((H for _n, _p, _F, H in cur if H is not None), None)
    res = C0.shift_resources(prior_H) if prior_H else {}
    acc = od([("答えの数の fact", 0), ("一致", 0), ("黙って違う", 0), ("止めた", 0), ("置かない", 0), ("余計に置いた", 0), ("置いた", 0),
              ("違う欄", collections.Counter()), ("止めた理由", collections.Counter()), ("規則で替えた", collections.Counter()),
              ("規則で替えて一致", collections.Counter()), ("規則で替えて黙って違う", collections.Counter()), ("規則で替えて余計", collections.Counter()),
              ("使った文脈", 0), ("使った文脈の定義が元と同じ", 0)])
    used = set()
    for _name, plain, F, _H in cur:
        put, stop, skip, moved = place2(plain, tab, sig, col, sigc, res, rules, valid)
        acc["規則で替えた"].update(moved)
        # 規則ごとの行き先は、規則を外した置き方と比べて決める
        base_put = {}
        if rules:
            bp, _bs, _bk, _m = place2(plain, tab, sig, col, sigc, res, (), valid)
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
                changed = rules and base_put.get(key) != P[key]
                if d:
                    acc["黙って違う"] += 1
                    acc["違う欄"]["+".join(d)] += 1
                    if changed:
                        acc["規則で替えて黙って違う"]["置き方が替わった"] += 1
                else:
                    acc["一致"] += 1
                    if changed:
                        acc["規則で替えて一致"]["置き方が替わった"] += 1
            elif key in S:
                acc["止めた"] += 1
                acc["止めた理由"][S[key]] += 1
            else:
                acc["置かない"] += 1
        for k, a in P.items():
            if k not in hit and rules and base_put.get(k) != a:
                acc["規則で替えて余計"]["置き方が替わった"] += 1
        acc["余計に置いた"] += sum(1 for k in P if k not in hit)
        used.update(a["contextRef"] for a in P.values())
    if cur_H:
        ans = dict((r["id"], r) for r in cur_H["resources"] if r["type"] == "context")
        for c in used:
            acc["使った文脈"] += 1
            if c in res and c in ans and C0.same_resource(res[c], ans[c]):
                acc["使った文脈の定義が元と同じ"] += 1
    for k in ("違う欄", "止めた理由", "規則で替えた", "規則で替えて一致", "規則で替えて黙って違う", "規則で替えて余計"):
        acc[k] = od(sorted(acc[k].items()))
    return acc


def split():
    ps = C0.pairs()
    judged = [x for x in ps if x[0] > SEEN_MAX_NO]
    dev = [x for x in ps if x[0] <= SEEN_MAX_NO] + judged[:DEV_JUDGED]
    held = judged[DEV_JUDGED:]
    return dev, held


if __name__ == "__main__":
    which, rules = sys.argv[1], tuple(r for r in sys.argv[2].split(",") if r and r != "none")
    dev, held = split()
    out = []
    for n, p, pp in (dev if which == "dev" else held):
        a = score_pair(p, pp, rules)
        out.append(od([("番号", n)] + list(a.items())))
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    tot = collections.Counter()
    for r in out:
        for k in ("答えの数の fact", "一致", "黙って違う", "止めた", "置かない", "余計に置いた", "置いた"):
            tot[k] += r[k]
    print(which, rules, dict(tot))
